"""LLM extraction — DeepSeek first, Azure OpenAI (Foundry) on escalation only.

Schema-agnostic: both entry points take the schema class and its prompt
intro (see app/schemas/registry.py) rather than hardcoding InvoiceExtraction,
so the same retry/repair machinery works for any implemented document type.
"""

import json
import logging
import time
from collections.abc import Callable
from typing import TypeVar

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Transient — worth retrying. Deliberately excludes AuthenticationError,
# BadRequestError, PermissionDeniedError: retrying a bad key or a malformed
# request just wastes the attempt budget on something that can't succeed.
_TRANSIENT_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)
_MAX_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 1.0


def _complete_with_retry(client, **kwargs) -> tuple[str, int, int]:
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            return content, prompt_tokens, completion_tokens
        except _TRANSIENT_ERRORS as exc:
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            delay = _BASE_DELAY_SECONDS * (2**attempt)
            logger.warning(
                "Transient LLM API error (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                delay,
                exc,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")  # loop always returns or raises


class ExtractionError(Exception):
    pass


def _parse_and_validate(raw_text: str, schema_cls: type[T]) -> T:
    data = json.loads(raw_text)
    return schema_cls.model_validate(data)


def _extract_with_repair(
    call: Callable[[str], tuple[str, int, int]], document_text: str, schema_cls: type[T]
) -> tuple[T, int, int]:
    prompt = f"Extract the fields from this document text:\n\n{document_text}"
    raw, prompt_tokens, completion_tokens = call(prompt)
    try:
        return _parse_and_validate(raw, schema_cls), prompt_tokens, completion_tokens
    except (json.JSONDecodeError, ValidationError) as exc:
        repair_prompt = (
            f"{prompt}\n\nYour previous response failed schema validation with "
            f"this error: {exc}\nReturn corrected JSON only, no other text."
        )
        raw, repair_prompt_tokens, repair_completion_tokens = call(repair_prompt)
        try:
            return (
                _parse_and_validate(raw, schema_cls),
                prompt_tokens + repair_prompt_tokens,
                completion_tokens + repair_completion_tokens,
            )
        except (json.JSONDecodeError, ValidationError) as exc2:
            raise ExtractionError(f"Extraction failed validation twice: {exc2}") from exc2


def _foundry_client() -> OpenAI:
    # Both the first-pass and escalation models are deployments on the same
    # Foundry resource's OpenAI-SDK-compatible v1 surface — one client
    # shape, differing only in the `model=` deployment name per call.
    return OpenAI(api_key=settings.foundry_api_key, base_url=settings.foundry_base_url)


def extract_with_deepseek(
    document_text: str, schema_cls: type[T], prompt_intro: str
) -> tuple[T, int, int]:
    client = _foundry_client()
    schema_json = json.dumps(schema_cls.model_json_schema())

    def call(prompt: str) -> tuple[str, int, int]:
        return _complete_with_retry(
            client,
            model=settings.deepseek_deployment,
            messages=[
                {"role": "system", "content": prompt_intro + schema_json},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

    return _extract_with_repair(call, document_text, schema_cls)


def extract_with_azure_openai(
    document_text: str, schema_cls: type[T], prompt_intro: str
) -> tuple[T, int, int]:
    """Escalation path for documents below the confidence threshold."""
    client = _foundry_client()
    schema_json = json.dumps(schema_cls.model_json_schema())

    def call(prompt: str) -> tuple[str, int, int]:
        return _complete_with_retry(
            client,
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": prompt_intro + schema_json},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

    return _extract_with_repair(call, document_text, schema_cls)
