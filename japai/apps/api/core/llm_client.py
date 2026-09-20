import json
import re
import time
import uuid
from datetime import datetime, timezone

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from sqlalchemy.orm import Session

from apps.api.core.config import settings
from apps.api.models.ai_run import AiRun

_configured = False
_MAX_RATE_LIMIT_RETRIES = 5
_DEFAULT_RETRY_DELAY_SECONDS = 15
_RETRY_DELAY_PATTERN = re.compile(r"retry in (\d+(?:\.\d+)?)s")


class LLMError(Exception):
    """Base for model-layer failures that callers/endpoints should surface cleanly."""


class LLMUnavailableError(LLMError):
    """The model could not be reached or refused the request (quota, network, auth)."""


class LLMResponseError(LLMError):
    """The model responded, but not in the shape the caller requires."""


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        if not settings.GEMINI_API_KEY:
            raise LLMUnavailableError(
                "GEMINI_API_KEY is not set — add it to .env and restart the api container."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True


def _generate_with_rate_limit_retry(gen_model, prompt: str, **kwargs):
    """Free-tier Gemini quotas are a handful of requests/minute. Retry on
    429 ResourceExhausted using the delay Google's own error suggests,
    rather than surfacing a spurious failure under normal pipeline use."""
    for attempt in range(_MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return gen_model.generate_content(prompt, **kwargs)
        except ResourceExhausted as exc:
            if attempt == _MAX_RATE_LIMIT_RETRIES:
                raise
            match = _RETRY_DELAY_PATTERN.search(str(exc))
            delay = float(match.group(1)) + 1 if match else _DEFAULT_RETRY_DELAY_SECONDS
            print(f"[llm_client] Rate limited (attempt {attempt + 1}), retrying in {delay:.0f}s...")
            time.sleep(delay)


def generate(
    prompt: str,
    db: Session,
    *,
    system: str | None = None,
    model: str = settings.GEMINI_MODEL,
    agent_name: str = "unknown",
    prompt_version: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: uuid.UUID | None = None,
    **kwargs,
) -> str:
    """Thin wrapper around Gemini. Infra only — no agent logic lives here.
    Writes an ai_runs row on every call (success or failure) as the
    observability hook for downstream agents."""
    _ensure_configured()
    started_at = datetime.now(timezone.utc)
    gen_model = genai.GenerativeModel(model, system_instruction=system)

    try:
        response = _generate_with_rate_limit_retry(gen_model, prompt, **kwargs)
        output_text = response.text
    except Exception as exc:
        db.add(
            AiRun(
                agent_name=agent_name,
                run_type="generation",
                status="failed",
                model=model,
                prompt_version=prompt_version,
                input_summary=prompt[:500],
                error_message=str(exc),
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        # Surface as a typed error so endpoints return a clear 503 instead of a
        # raw provider traceback leaking through as an unhandled 500.
        raise LLMUnavailableError(
            f"Model call failed ({type(exc).__name__}): {str(exc)[:300]}"
        ) from exc

    db.add(
        AiRun(
            agent_name=agent_name,
            run_type="generation",
            status="succeeded",
            model=model,
            prompt_version=prompt_version,
            input_summary=prompt[:500],
            output_summary=output_text[:500],
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return output_text


def generate_json(
    prompt: str,
    db: Session,
    *,
    schema: dict,
    required_keys: tuple[str, ...] = (),
    **kwargs,
) -> dict | list:
    """generate() + strict parsing, so every structured call site fails the same way.

    Gemini's response_schema makes malformed output rare but not impossible, and a
    bare json.loads at the call site would surface as an unhandled 500.
    """
    from google.generativeai.types import GenerationConfig

    kwargs.setdefault(
        "generation_config",
        GenerationConfig(response_mime_type="application/json", response_schema=schema),
    )
    raw = generate(prompt, db, **kwargs)

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise LLMResponseError(
            f"Model returned unparseable JSON: {str(raw)[:200]}"
        ) from exc

    missing = [k for k in required_keys if k not in parsed] if isinstance(parsed, dict) else []
    if missing:
        raise LLMResponseError(f"Model response missing required field(s): {', '.join(missing)}")
    return parsed
