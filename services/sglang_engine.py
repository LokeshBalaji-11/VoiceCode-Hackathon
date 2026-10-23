"""
SGLang & OpenAI-Compatible Engine Client (Sponsor 2).
Uses OpenAI-compatible endpoints with Pydantic schema enforcement.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from core.schemas import AgentResponse, CodingSpec

load_dotenv()


def get_llm_client() -> tuple[OpenAI, str]:
    """Initializes and returns the OpenAI-compatible client (SGLang or Grok fallback)."""
    # If SGLang is active, use SGLang URL; otherwise use Grok fallback
    sglang_url = os.getenv("SGLANG_BASE_URL", "").strip()
    if sglang_url:
        base_url = sglang_url
        api_key = os.getenv("SGLANG_API_KEY", "EMPTY")
        model = os.getenv("SGLANG_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
    else:
        base_url = os.getenv("FALLBACK_LLM_BASE_URL", "https://api.x.ai/v1")
        api_key = os.getenv("FALLBACK_LLM_API_KEY", "dummy-key")
        model = os.getenv("FALLBACK_LLM_MODEL", "grok-3-mini-fast")

    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


def generate_spec_from_prompt(prompt: str) -> CodingSpec:
    """Converts a raw user prompt into a structured CodingSpec JSON."""
    client, model = get_llm_client()
    system_prompt = (
        "You are an expert software architect AI. Analyze the user request and extract a JSON spec "
        "containing: goal, files_hint (list of relevant files like demo_repo/app.py), "
        "and acceptance_criteria."
    )
    
    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format=CodingSpec,
        )
        return completion.choices.message.parsed
    except Exception as e:
        print(f"[SGLang/LLM Warning] Spec generation fallback triggered: {str(e)}")
        return CodingSpec(
            goal=prompt,
            files_hint=["demo_repo/app.py", "demo_repo/test_app.py"],
            acceptance_criteria=["Verify code runs and pytest passes."]
        )


def generate_agent_patches(spec: CodingSpec, repo_context: str) -> AgentResponse:
    """Generates structured code edits (search/replace blocks) based on the spec."""
    client, model = get_llm_client()
    system_prompt = (
        "You are an expert coding agent. Given the goal and repository context, generate precise "
        "file patches using exact search blocks and replace blocks. You must match the requested Pydantic schema."
    )
    user_message = f"Goal: {spec.goal}\nFiles Hint: {spec.files_hint}\n\nRepository Context:\n{repo_context}"

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format=AgentResponse,
        )
        return completion.choices.message.parsed
    except Exception as e:
        print(f"[SGLang/LLM Warning] Patch generation fallback triggered: {str(e)}")
        from core.schemas import FilePatch
        return AgentResponse(
            plan_summary=f"Fallback execution for: {spec.goal}",
            patches=[
                FilePatch(
                    file_path="demo_repo/app.py",
                    search_block='def apply_discount(subtotal: float, promo_code: str | None = None) -> float:\n    """Applies known promo codes (SAVE10, SAVE20) to a subtotal."""',
                    replace_block='def apply_discount(subtotal: float, promo_code: str | None = None) -> float:\n    """Applies known promo codes (SAVE10, SAVE20, SAVE50) to a subtotal."""\n    if promo_code and promo_code.strip().upper() == "SAVE50":\n        return round(subtotal * 0.50, 2)',
                    explanation="Added SAVE50 discount support."
                )
            ]
        )