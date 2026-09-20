"""Surfaces the `ai_runs` audit trail that llm_client has written since Phase 2.

This router adds NO new logging — it only reads what is already recorded. Two
consequences worth stating plainly, because the UI states them too:

  - `latency_ms` is not a stored column. It is computed here as
    completed_at - started_at, which was the deliberate Phase 2 decision (both
    timestamps are written on every call, so the column would be redundant).
  - token counts and cost are NOT recorded anywhere. llm_client has never
    captured them, so they cannot be shown. Adding them would mean changing the
    write path, which is outside this router's job.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.core.db import get_db
from apps.api.models import AiRun

router = APIRouter(prefix="/observability", tags=["observability"])

NOT_LOGGED = ["prompt_tokens", "completion_tokens", "estimated_cost"]

# completed_at - started_at, in milliseconds. NULL-safe: a run that never
# completed (process killed mid-call) has no latency rather than a bogus 0.
_LATENCY_MS = (
    func.extract("epoch", AiRun.completed_at - AiRun.started_at) * 1000
)


def _latency(run: AiRun) -> float | None:
    if run.started_at is None or run.completed_at is None:
        return None
    return round((run.completed_at - run.started_at).total_seconds() * 1000, 1)


@router.get("/runs")
def list_runs(
    limit: int = Query(50, ge=1, le=500, description="Most recent runs to return"),
    agent_name: str | None = Query(None, description="Filter to one agent"),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    q = db.query(AiRun)
    if agent_name:
        q = q.filter(AiRun.agent_name == agent_name)
    if status:
        q = q.filter(AiRun.status == status)
    runs = q.order_by(AiRun.created_at.desc()).limit(limit).all()

    return {
        "count": len(runs),
        "not_logged": NOT_LOGGED,
        "runs": [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "status": r.status,
                "model": r.model,
                "prompt_version": r.prompt_version,
                "latency_ms": _latency(r),
                "run_type": r.run_type,
                "related_entity_type": r.related_entity_type,
                "error_message": r.error_message,
                "input_summary": (r.input_summary or "")[:160] or None,
                "created_at": r.created_at,
            }
            for r in runs
        ],
    }


@router.get("/summary")
def summary(
    hours: int = Query(24, ge=1, le=720, description="Rolling window in hours"),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    rows = (
        db.query(
            AiRun.agent_name,
            func.count(AiRun.id).label("calls"),
            func.count(AiRun.id).filter(AiRun.status == "failed").label("failed"),
            func.avg(_LATENCY_MS).label("avg_latency_ms"),
            func.max(_LATENCY_MS).label("max_latency_ms"),
        )
        .filter(AiRun.created_at >= since)
        .group_by(AiRun.agent_name)
        .order_by(func.count(AiRun.id).desc())
        .all()
    )

    by_agent = [
        {
            "agent_name": r.agent_name,
            "calls": r.calls,
            "failed": r.failed,
            "success_rate": round((r.calls - r.failed) / r.calls, 4) if r.calls else None,
            "avg_latency_ms": round(float(r.avg_latency_ms), 1) if r.avg_latency_ms else None,
            "max_latency_ms": round(float(r.max_latency_ms), 1) if r.max_latency_ms else None,
        }
        for r in rows
    ]

    total_calls = sum(a["calls"] for a in by_agent)
    total_failed = sum(a["failed"] for a in by_agent)

    models = [
        {"model": m, "calls": c}
        for m, c in db.query(AiRun.model, func.count(AiRun.id))
        .filter(AiRun.created_at >= since)
        .group_by(AiRun.model)
        .all()
    ]

    window = db.query(func.min(AiRun.created_at), func.max(AiRun.created_at)).first()

    return {
        "window_hours": hours,
        "total_calls": total_calls,
        "total_failed": total_failed,
        "success_rate": round((total_calls - total_failed) / total_calls, 4) if total_calls else None,
        "by_agent": by_agent,
        "by_model": models,
        "all_time_first_run": window[0] if window else None,
        "all_time_last_run": window[1] if window else None,
        "not_logged": NOT_LOGGED,
        "note": (
            "latency_ms is computed from completed_at - started_at, not stored. "
            "Token counts and cost have never been recorded by llm_client and "
            "therefore cannot be shown."
        ),
    }
