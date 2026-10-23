"""
Main Agent Orchestrator.
Coordinates planning, patching, pytest self-correction loops, and git workflows.
"""
import time
from pathlib import Path
from core.schemas import CodingSpec, AgentResponse
from core.git_ops import apply_patch_to_file, run_pytest_suite, execute_git_workflow
from services.sglang_engine import generate_spec_from_prompt, generate_agent_patches

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_repo_context() -> str:
    """Reads demo_repo files to give context to the LLM."""
    app_code = (REPO_ROOT / "demo_repo/app.py").read_text(encoding="utf-8")
    test_code = (REPO_ROOT / "demo_repo/test_app.py").read_text(encoding="utf-8")
    return f"--- demo_repo/app.py ---\n{app_code}\n\n--- demo_repo/test_app.py ---\n{test_code}"


def run_agent_pipeline(user_prompt: str, approved: bool = False) -> dict:
    """Executes the full agent workflow from prompt to PR."""
    timeline = []
    
    # Step 1: Generate Spec
    timeline.append({"step": "spec_generation", "status": "running", "message": "Parsing user prompt into structured spec..."})
    spec = generate_spec_from_prompt(user_prompt)
    timeline[-1]["status"] = "completed"
    timeline[-1]["spec"] = spec.model_dump()

    # Step 2: Generate Patches & Plan
    timeline.append({"step": "plan_generation", "status": "running", "message": "Generating code patch plan via Grok..."})
    repo_context = get_repo_context()
    agent_response = generate_agent_patches(spec, repo_context)
    timeline[-1]["status"] = "completed"
    timeline[-1]["plan"] = agent_response.model_dump()

    if not approved:
        return {
            "status": "pending_approval",
            "spec": spec.model_dump(),
            "plan": agent_response.model_dump(),
            "timeline": timeline,
        }

    # Step 3: Apply Patches
    timeline.append({"step": "apply_patches", "status": "running", "message": "Applying structured patches to codebase..."})
    for patch in agent_response.patches:
        success = apply_patch_to_file(patch.file_path, patch.search_block, patch.replace_block)
        if not success:
            timeline[-1]["status"] = "failed"
            return {"status": "error", "message": f"Failed to apply patch to {patch.file_path}", "timeline": timeline}
    timeline[-1]["status"] = "completed"

    # Step 4: Pytest Self-Correction Loop (Max 2 retries)
    max_retries = 2
    pytest_passed = False
    pytest_logs = ""
    
    for attempt in range(max_retries + 1):
        timeline.append({"step": f"pytest_attempt_{attempt+1}", "status": "running", "message": f"Running pytest suite (attempt {attempt+1}/{max_retries+1})..."})
        pytest_passed, pytest_logs = run_pytest_suite()
        if pytest_passed:
            timeline[-1]["status"] = "passed"
            break
        else:
            timeline[-1]["status"] = "failed"
            if attempt < max_retries:
                fix_prompt = f"The previous code patch caused pytest failures:\n{pytest_logs}\nFix the code so tests pass."
                fix_response = generate_agent_patches(CodingSpec(goal=fix_prompt, files_hint=spec.files_hint, acceptance_criteria=spec.acceptance_criteria), repo_context)
                for patch in fix_response.patches:
                    apply_patch_to_file(patch.file_path, patch.search_block, patch.replace_block)

    if not pytest_passed:
        return {
            "status": "error",
            "message": "Pytest failed after maximum self-correction retries.",
            "pytest_logs": pytest_logs,
            "timeline": timeline,
        }

    # Step 5: Git Branch & PR Workflow
    timeline.append({"step": "git_workflow", "status": "running", "message": "Creating branch, committing, and opening Pull Request..."})
    branch_name = f"autopilot-{int(time.time())}"
    commit_msg = f"VoiceCode update: {spec.goal[:50]}"
    git_result = execute_git_workflow(branch_name, commit_msg)
    
    if not git_result["success"]:
        timeline[-1]["status"] = "failed"
        return {"status": "error", "message": git_result["message"], "timeline": timeline}

    timeline[-1]["status"] = "completed"
    timeline[-1]["git_result"] = git_result

    return {
        "status": "success",
        "message": "Pipeline completed successfully!",
        "git_result": git_result,
        "pytest_logs": pytest_logs,
        "timeline": timeline,
    }