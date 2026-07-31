"""Dollar-cost estimation for LLM extraction calls, from token counts
captured off each OpenAI-compatible response (see services/extraction.py).

Per-1M-token prices live in Settings (see core/config.py) so they can be
corrected without a code change once real Foundry billing is confirmed.
"""

from app.core.config import settings


def extraction_cost(
    is_escalation: bool, prompt_tokens: int | None, completion_tokens: int | None
) -> float:
    if prompt_tokens is None or completion_tokens is None:
        return 0.0

    input_price, output_price = (
        (settings.azure_openai_input_price_per_1m, settings.azure_openai_output_price_per_1m)
        if is_escalation
        else (settings.deepseek_input_price_per_1m, settings.deepseek_output_price_per_1m)
    )
    return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
