"""
Safety Guardrail & Audit Module (Sponsor 4: Lexsi Labs / Rule-Based Scanner).
Audits every proposed diff before a Pull Request is allowed to open.
"""
import re


def audit_diff(file_path: str, search_block: str, replace_block: str) -> dict:
    """
    Audits a proposed code diff against 5 safety rules:
    1. Leaked secrets (API keys, tokens, private keys)
    2. Dangerous shell commands (rm -rf, os.system, subprocess with shell=True)
    3. Edits outside allowlist (only demo_repo/ files allowed)
    4. Deleted tests or assertion removal
    5. Prompt injection text patterns
    """
    combined_code = (search_block + "\n" + replace_block).lower()
    replace_upper = replace_block

    # Rule 1: Leaked API Keys / Secrets (Matches sk-ant-, ghp_, xai-, Bearer, api_key, etc.)
    secret_patterns = [
        r"sk-[a-zA-Z0-9-_]{20,}",
        r"ghp_[a-zA-Z0-9]{36}",
        r"xai-[a-zA-Z0-9-_]{20,}",
        r"secret_api_key\s*=\s*['\"].+['\"]",
        r"bearer\s+[a-zA-Z0-9-_.~+/-]+=*",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, replace_upper, re.IGNORECASE):
            return {
                "allowed": False,
                "reason": "Security Alert: Proposed diff contains a leaked API key or secret token.",
            }

    # Rule 2: Dangerous Shell Commands
    dangerous_commands = ["rm -rf", "os.system(", "subprocess.run(", "eval(", "exec("]
    for cmd in dangerous_commands:
        if cmd in combined_code:
            return {
                "allowed": False,
                "reason": f"Security Alert: Proposed diff contains dangerous execution command: {cmd}",
            }

    # Rule 3: Allowlist check (Only allow changes inside demo_repo/)
    if not file_path.startswith("demo_repo/"):
        return {
            "allowed": False,
            "reason": f"Security Alert: Modifications outside demo_repo allowlist are blocked: {file_path}",
        }

    # Rule 4: Deleted Tests Check
    if "test_" in search_block and ("# deleted tests" in replace_block.lower() or len(replace_block.strip()) < 10):
        return {
            "allowed": False,
            "reason": "Security Alert: Proposed diff deletes critical unit tests or assertions.",
        }

    # Rule 5: Prompt Injection / Malicious Override
    if "ignore previous instructions" in combined_code or "system prompt override" in combined_code:
        return {
            "allowed": False,
            "reason": "Security Alert: Prompt injection pattern detected in diff.",
        }

    return {
        "allowed": True,
        "reason": "Diff passed all safety guardrail audits successfully.",
    }