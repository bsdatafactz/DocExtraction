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
    AzureOpenAI,
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


def _complete_with_retry(client, **kwargs) -> str:
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
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
    call: Callable[[str], str], document_text: str, schema_cls: type[T]
) -> T:
    prompt = f"Extract the fields from this document text:\n\n{document_text}"
    raw = call(prompt)
    try:
        return _parse_and_validate(raw, schema_cls)
    except (json.JSONDecodeError, ValidationError) as exc:
        repair_prompt = (
            f"{prompt}\n\nYour previous response failed schema validation with "
            f"this error: {exc}\nReturn corrected JSON only, no other text."
        )
        raw = call(repair_prompt)
        try:
            return _parse_and_validate(raw, schema_cls)
        except (json.JSONDecodeError, ValidationError) as exc2:
            raise ExtractionError(f"Extraction failed validation twice: {exc2}") from exc2


def extract_with_deepseek(document_text: str, schema_cls: type[T], prompt_intro: str) -> T:
    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    schema_json = json.dumps(schema_cls.model_json_schema())

    def call(prompt: str) -> str:
        return _complete_with_retry(
            client,
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt_intro + schema_json},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

    return _extract_with_repair(call, document_text, schema_cls)


def extract_with_azure_openai(document_text: str, schema_cls: type[T], prompt_intro: str) -> T:
    """Escalation path for documents below the confidence threshold."""
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )
    schema_json = json.dumps(schema_cls.model_json_schema())

    def call(prompt: str) -> str:
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
