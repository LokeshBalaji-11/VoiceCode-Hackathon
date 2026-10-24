"""
Main Agent Orchestrator.
Coordinates planning, patching, pytest self-correction loops, and git workflows.
"""
import time
from pathlib import Path
from core.schemas import CodingSpec, AgentResponse
from core.git_ops import apply_patch_to_file, run_pytest_suite, execute_git_workflow, discard_uncommitted_changes
from core.safety_audit import run_safety_audit
from services.sglang_engine import generate_spec_from_prompt, generate_agent_patches

REPO_ROOT = Path(__file__).resolve().parent.parent
def get_repo_context(user_workspace) -> str:
    """Reads the user's private workspace files to give full context to the LLM."""
    app_code = (user_workspace / "app.py").read_text(encoding="utf-8")
    test_code = (user_workspace / "test_app.py").read_text(encoding="utf-8")
    return f"--- {user_workspace.name}/app.py ---\n{app_code}\n--- {user_workspace.name}/test_app.py ---\n{test_code}"

def run_agent_pipeline(prompt, approved=False, user_id="guest"):
    """Executes the full agent workflow from prompt to PR."""
    import shutil
    
    # 1. Create a unique path using the user's ID
    user_workspace = REPO_ROOT / "workspaces" / user_id / "demo_repo"
    
    # 2. Copy a fresh template for them to use if it doesn't exist
    if not user_workspace.exists():
        user_workspace.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPO_ROOT / "demo_repo", user_workspace)

    timeline = []
    # Step 1: Generate Spec
    timeline.append({"step": "spec_generation", "status": "running", "message": "Parsing user prompt into structured spec..."})
    spec = generate_spec_from_prompt(prompt)
    timeline[-1]["status"] = "completed"
    timeline[-1]["spec"] = spec.model_dump()

    # Step 2: Generate Patches & Plan
    timeline.append({"step": "plan_generation", "status": "running", "message": "Generating code patch plan via Grok..."})
    repo_context = get_repo_context(REPO_ROOT / "demo_repo")
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
        success = apply_patch_to_file(patch.file_path, patch.search_block, patch.replace_block, REPO_ROOT / "demo_repo")
        if not success:
            timeline[-1]["status"] = "failed"
            return {"status": "error", "message": f"Failed to apply patch to {patch.file_path}", "timeline": timeline}
    timeline[-1]["status"] = "completed"

    # Step 04: Pytest Verification with Self-Healing
    timeline.append({"step": "pytest_attempt_1", "status": "running"})
    pytest_success, pytest_logs = run_pytest_suite(REPO_ROOT / "demo_repo")
    
    if pytest_success:
        timeline[-1]["status"] = "passed"
    else:
        timeline[-1]["status"] = "failed"
        
        if approved:
            # NEXT-LEVEL FEATURE: Self-Correction Retry Loop
            timeline.append({"step": "ai_self_correction_patch", "status": "running"})
            
            # Send error logs back to the LLM to generate a fix patch
            fix_prompt = f"{prompt}\n\nFIX THE FOLLOWING PYTEST ERROR:\n{pytest_logs}"
            fix_response = generate_agent_patches(fix_prompt, get_repo_context(REPO_ROOT / "demo_repo"))
            
            if fix_response and hasattr(fix_response, "patches"):
                for patch in fix_response.patches:
                    apply_patch_to_file(REPO_ROOT / "demo_repo", patch.file_path, patch.search_block, patch.replace_block)
                timeline[-1]["status"] = "completed"
                
                # Run pytest attempt 2
                timeline.append({"step": "pytest_attempt_2", "status": "running"})
                retry_success, retry_logs = run_pytest_suite(REPO_ROOT / "demo_repo")
                if retry_success:
                    timeline[-1]["status"] = "passed"
                    pytest_success = True
                else:
                    timeline[-1]["status"] = "failed"
                    pytest_logs = retry_logs
            else:
                timeline[-1]["status"] = "failed"
    # Step 4.5: Safety Audit Gate (Between Pytest and Git Commit)
    timeline.append({"step": "safety_audit", "status": "running", "message": "Running pre-commit safety audit (secrets, allowlist, commands, deleted tests)..."})
    audit_result = run_safety_audit(agent_response.patches)
    if isinstance(audit_result, bool):
      audit_result = {"allowed": audit_result, "reasons": []}
    timeline[-1]["audit"] = audit_result
    if not audit_result["allowed"]:
        timeline[-1]["status"] = "failed"
        timeline[-1]["message"] = "Blocked by Safety Audit: " + "; ".join(audit_result["reasons"])
        discard_uncommitted_changes()
        return {
            "status": "blocked",
            "message": "Blocked by Safety Audit: " + "; ".join(audit_result["reasons"]),
            "audit": audit_result,
            "pytest_logs": pytest_logs,
            "timeline": timeline,
        }
    timeline[-1]["status"] = "passed"
    timeline[-1]["message"] = "Safety audit passed: " + "; ".join(audit_result["reasons"])

    # Step 5: Git Branch & PR Workflow
    timeline.append({"step": "git_workflow", "status": "running", "message": "Creating branch, committing, and opening Pull Request..."})
    branch_name = f"autopilot-{int(time.time())}"
    commit_msg = f"VoiceCode update: {prompt[:50]}"
    git_result = execute_git_workflow(branch_name, commit_msg, user_workspace=REPO_ROOT / "demo_repo")
     
    
    if not git_result["success"]:
        timeline[-1]["status"] = "failed"
        return {"status": "error", "message": git_result["message"], "timeline": timeline}

    timeline[-1]["status"] = "completed"
    timeline[-1]["git_result"] = git_result

    return {
        "status": "success",
        "message": "Pipeline completed successfully!",
        "audit": audit_result,
        "git_result": git_result,
        "pytest_logs": pytest_logs,
        "timeline": timeline,
    }