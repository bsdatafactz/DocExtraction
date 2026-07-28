"""LLM extraction — DeepSeek first, Azure OpenAI (Foundry) on escalation only.

Both entry points share the same contract (document text in, validated
InvoiceExtraction out) and the same one-retry repair loop, so callers don't
need to know which model produced a result.
"""

import json
import logging
import time
from collections.abc import Callable

from openai import (
    APIConnectionError,
    APITimeoutError,
    AzureOpenAI,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.invoice import InvoiceExtraction

logger = logging.getLogger(__name__)

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

EXTRACTION_SYSTEM_PROMPT = """You are an invoice data extraction system. Extract \
fields from the invoice text into JSON matching the schema below exactly. \
Rules:
- If a field does not apply to this document (e.g. no PO number was ever \
issued), set field_status[field] = "not_applicable" and leave the value null.
- If a field is present on the document but you cannot read it confidently, \
set field_status[field] = "illegible".
- If a field is present and readable, set field_status[field] = "extracted" \
and include your own 0.0-1.0 confidence in self_reported_confidence[field].
- Never guess a value to fill a field — a wrong guess is worse than null.

Schema:
"""


class ExtractionError(Exception):
    pass


def _schema_json() -> str:
    return json.dumps(InvoiceExtraction.model_json_schema())


def _parse_and_validate(raw_text: str) -> InvoiceExtraction:
    data = json.loads(raw_text)
    return InvoiceExtraction.model_validate(data)


def _extract_with_repair(call: Callable[[str], str], document_text: str) -> InvoiceExtraction:
    prompt = f"Extract the invoice fields from this document text:\n\n{document_text}"
    raw = call(prompt)
    try:
        return _parse_and_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        repair_prompt = (
            f"{prompt}\n\nYour previous response failed schema validation with "
            f"this error: {exc}\nReturn corrected JSON only, no other text."
        )
        raw = call(repair_prompt)
        try:
            return _parse_and_validate(raw)
        except (json.JSONDecodeError, ValidationError) as exc2:
            raise ExtractionError(f"Extraction failed validation twice: {exc2}") from exc2


def extract_with_deepseek(document_text: str) -> InvoiceExtraction:
    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    def call(prompt: str) -> str:
        return _complete_with_retry(
            client,
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT + _schema_json()},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

    return _extract_with_repair(call, document_text)


def extract_with_azure_openai(document_text: str) -> InvoiceExtraction:
    """Escalation path for documents below the confidence threshold."""
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )

    def call(prompt: str) -> str:
        return _complete_with_retry(
            client,
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT + _schema_json()},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

    return _extract_with_repair(call, document_text)
