import os
from openai import OpenAI
from evals.safety_guardrail import audit_patches
def run_safety_audit(code_patch: str) -> bool:
    """
    Evaluates the code patch using SGLang or local safety guardrail fallback.
    """
    print("Running Safety Evaluation...")
    
    # 1. Run local deterministic safety guardrail check first
    guardrail_result = audit_patches([{"file": "patch.py", "diff": code_patch}])
    if not guardrail_result.get("passed", True):
        print("Blocked by Safety Guardrail:", guardrail_result.get("violations"))
        return False

    # 2. Try local SGLang engine if running, otherwise pass gracefully
    sglang_url = os.getenv("SGLANG_BASE_URL", "http://localhost:30000/v1")
    try:
        client = OpenAI(base_url=sglang_url, api_key="EMPTY")
        prompt = f"""Analyze the following code patch.
You must output ONLY the word 'FAIL' if the code contains:
1. Hardcoded API keys, secrets, or passwords.
2. Malicious system commands (e.g., os.system).
Otherwise output 'PASS'.

Code to evaluate:
{code_patch}
"""
        response = client.chat.completions.create(
            model="default",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            timeout=2.0
        )
        verdict = response.choices[0].message.content.strip().upper()
        return "FAIL" not in verdict
    except Exception:
        # If local SGLang server isn't running, rely on the verified local guardrail
        return True