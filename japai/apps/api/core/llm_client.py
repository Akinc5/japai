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

import os
from dotenv import load_dotenv

_last_api_key = None
_MAX_RATE_LIMIT_RETRIES = 1
_DEFAULT_RETRY_DELAY_SECONDS = 3
_RETRY_DELAY_PATTERN = re.compile(r"retry in (\d+(?:\.\d+)?)s")


class LLMError(Exception):
    """Base for model-layer failures that callers/endpoints should surface cleanly."""


class LLMUnavailableError(LLMError):
    """The model could not be reached or refused the request (quota, network, auth)."""


class LLMResponseError(LLMError):
    """The model responded, but not in the shape the caller requires."""


def _ensure_configured() -> None:
    global _last_api_key
    load_dotenv(override=True)
    current_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not current_key:
        raise LLMUnavailableError(
            "GEMINI_API_KEY is not set — add it to .env and restart the api container."
        )
    if current_key != _last_api_key:
        genai.configure(api_key=current_key)
        _last_api_key = current_key



def _generate_with_rate_limit_retry(gen_model, prompt: str, **kwargs):
    """Attempt generation with rapid retry for transient rate limits,
    failing fast to allow model fallback if daily per-model limits are hit."""
    for attempt in range(_MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return gen_model.generate_content(prompt, **kwargs)
        except ResourceExhausted as exc:
            err_str = str(exc)
            # If daily project quota is exceeded, don't sleep — immediately let next model try
            if "GenerateRequestsPerDay" in err_str or attempt == _MAX_RATE_LIMIT_RETRIES:
                raise
            match = _RETRY_DELAY_PATTERN.search(err_str)
            delay = min(float(match.group(1)) if match else _DEFAULT_RETRY_DELAY_SECONDS, 5.0)
            print(f"[llm_client] Rate limited, quick pause {delay:.1f}s before retry...")
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

    candidate_models = [
        model,
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-3.6-flash",
    ]
    seen = set()
    candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

    last_exc = None
    output_text = None
    used_model = model

    for m in candidate_models:
        try:
            gen_model = genai.GenerativeModel(m, system_instruction=system)
            response = _generate_with_rate_limit_retry(gen_model, prompt, **kwargs)
            output_text = response.text
            used_model = m
            break
        except Exception as exc:
            last_exc = exc
            print(f"[llm_client] Model {m} failed: {str(exc)[:120]}, trying next model...")


    if output_text is None:
        db.add(
            AiRun(
                agent_name=agent_name,
                run_type="generation",
                status="failed",
                model=used_model,
                prompt_version=prompt_version,
                input_summary=prompt[:500],
                error_message=str(last_exc),
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        raise LLMUnavailableError(
            f"Model call failed ({type(last_exc).__name__}): {str(last_exc)[:300]}"
        ) from last_exc

    db.add(
        AiRun(
            agent_name=agent_name,
            run_type="generation",
            status="succeeded",
            model=used_model,
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
