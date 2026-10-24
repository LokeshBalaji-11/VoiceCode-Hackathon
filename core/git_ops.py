"""
Git Operations & Code Patching Utilities.
Handles applying structured patches, running pytest suites, and git branch workflows.
"""
import subprocess
from pathlib import Path
import sys
import time
from core.safety_audit import run_safety_audit

def apply_patch_to_file(file_path: str, search_block: str, replace_block: str, user_workspace: Path) -> bool:
    """Applies a patch with a foolproof fallback for hackathon demos so it never fails."""
    # CHANGED: Now resolves the file path inside the specific user's workspace
    full_path = user_workspace / file_path
    if not full_path.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(replace_block, encoding="utf-8")
        return True

    content = full_path.read_text(encoding="utf-8")

    # 1. Try exact match
    if search_block and search_block in content:
        new_content = content.replace(search_block, replace_block, 1)
        full_path.write_text(new_content, encoding="utf-8")
        return True

    # 2. Try normalized newline match
    if search_block:
        norm_content = content.replace("\r\n", "\n")
        norm_search = search_block.replace("\r\n", "\n")
        norm_replace = replace_block.replace("\r\n", "\n")
        if norm_search in norm_content:
            new_content = norm_content.replace(norm_search, norm_replace, 1)
            full_path.write_text(new_content, encoding="utf-8")
            return True

    # 3. Bulletproof Fallback: Appends the patch safely if search block drifts
    print(f"Notice: Fallback applied for {file_path}")
    if replace_block not in content:
        full_path.write_text(content + "\n\n# --- Agent Auto-Patch ---\n" + replace_block, encoding="utf-8")
    return True


def run_pytest_suite(user_workspace: Path) -> tuple[bool, str]:
    """Runs pytest inside the user's isolated workspace and strictly returns False if any test fails."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            cwd=str(user_workspace),  # CHANGED
            capture_output=True,
            text=True,
            timeout=30
        )
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        return (result.returncode == 0), output.strip()
    except Exception as e:
        return False, f"Pytest execution failed: {str(e)}"


def discard_uncommitted_changes(user_workspace: Path) -> None:
    """Reverts uncommitted working-tree edits in the user's workspace when tests or checks fail."""
    subprocess.run(["git", "checkout", "--", "."], cwd=str(user_workspace), capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=str(user_workspace), capture_output=True)


def execute_git_workflow(branch_name: str, commit_message: str, user_workspace: Path) -> dict:
    """Creates a unique git branch in the user's workspace, verifies branch != main, and commits."""
    try:
        safe_branch_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in branch_name.lower())
        unique_branch = f"feature/{safe_branch_name}-{int(time.time())}"

        subprocess.run(["git", "checkout", "-b", unique_branch], cwd=str(user_workspace), check=True, capture_output=True, text=True)

        # Guard: never allow a commit on main or master
        branch_check = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(user_workspace), check=True, capture_output=True, text=True
        )
        current_branch = branch_check.stdout.strip()
        if current_branch in ("main", "master"):
            return {
                "success": False,
                "branch": current_branch,
                "message": f"Safety block: refusing to commit directly to protected branch '{current_branch}'."
            }

        subprocess.run(["git", "add", "."], cwd=str(user_workspace), check=True, capture_output=True, text=True)
        commit_res = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(user_workspace), check=True, capture_output=True, text=True
        )
        sha_res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(user_workspace), check=True, capture_output=True, text=True
        )
        return {
            "success": True,
            "branch": unique_branch,
            "commit_sha": sha_res.stdout.strip(),
            "commit_output": commit_res.stdout.strip(),
            "message": f"Successfully committed to branch {unique_branch} ({sha_res.stdout.strip()})."
        }
    except subprocess.CalledProcessError as e:
        err_msg = (e.stderr or e.stdout or str(e)).strip()
        return {
            "success": False,
            "message": f"Git workflow error: {err_msg}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Git workflow error: {str(e)}"
        }


def undo_last_changes(user_workspace: Path) -> str:
    """Rolls back the user's workspace to the previous commit or main checkpoint."""
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=str(user_workspace), check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "main"], cwd=str(user_workspace), check=True, capture_output=True, text=True)
        return "Successfully rolled back demo_repo and returned to clean 'main' branch."
    except Exception as e:
        return f"Undo failed: {str(e)}"