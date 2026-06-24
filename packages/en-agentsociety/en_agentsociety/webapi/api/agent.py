from datetime import datetime, timezone
import json
import uuid
from typing import List, Optional, cast

from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ApiResponseWrapper
from ..models.agent import (
    AgentDialogType,
    ApiAgentDialog,
    ApiAgentProfile,
    ApiAgentStatus,
    ApiAgentSurvey,
    ApiGlobalPrompt,
    ApiBlockExecution,
    ApiTimelineStep,
    ApiLocationStep,
    ApiDailySchedule,
    ApiDailyScheduleBlock,
)
from ..models.experiment import Experiment, ExperimentStatus
from ..models.survey import Survey
from .experiment import _find_started_experiment_by_id
from .timezone import ensure_timezone_aware

__all__ = ["router"]

router = APIRouter(tags=["agent"])


@router.get("/experiments/{exp_id}/agents/{agent_id}/dialog")
async def get_agent_dialog_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentDialog]]:
    """Get dialog by experiment ID and agent ID"""

    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    per_exp_sqlite = request.app.state.per_exp_sqlite
    exp_id_str = str(exp_id)

    # Get completed dialogs from per-experiment SQLite
    raw_dialogs = await per_exp_sqlite.query_dialogs(exp_id_str, agent_id)
    dialogs: List[ApiAgentDialog] = []
    for row in raw_dialogs:
        dialogs.append(ApiAgentDialog(
            id=row.get("id", agent_id),
            day=row["day"],
            t=row["t"],
            type=AgentDialogType(row["type"]),
            speaker=row["speaker"],
            content=row["content"],
            created_at=ensure_timezone_aware(row["created_at"]),
        ))

    # Get pending (user-sent) dialogs from per-experiment SQLite
    raw_pending = await per_exp_sqlite.query_pending_dialogs(exp_id_str, agent_id)
    for row in raw_pending:
        dialogs.append(ApiAgentDialog(
            id=agent_id,
            day=row["day"],
            t=row["t"],
            type=AgentDialogType.User,
            speaker="user",
            content=row["content"],
            created_at=ensure_timezone_aware(row["created_at"]),
        ))

    dialogs.sort(key=lambda x: (x.day, x.t))
    return ApiResponseWrapper(data=dialogs)


@router.get("/experiments/{exp_id}/agents/-/profile")
async def list_agent_profile_by_exp_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[List[ApiAgentProfile]]:
    """List agent profiles by experiment ID (from ClickHouse/DuckDB)"""

    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_agent_profiles(str(exp_id))

    profiles: List[ApiAgentProfile] = []
    for row in rows:
        profile_val = row.get("profile", "{}")
        if isinstance(profile_val, str):
            try:
                profile_val = json.loads(profile_val)
            except Exception:
                pass
        profiles.append(ApiAgentProfile(
            id=row["agent_id"],
            name=row.get("name", ""),
            profile=profile_val,
        ))

    return ApiResponseWrapper(data=profiles)


@router.get("/experiments/{exp_id}/agents/{agent_id}/profile")
async def get_agent_profile_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[ApiAgentProfile]:
    """Get agent profile by experiment ID and agent ID (from ClickHouse/DuckDB)"""

    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_agent_profiles(str(exp_id), agent_id)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found"
        )

    row = rows[0]
    profile_val = row.get("profile", "{}")
    if isinstance(profile_val, str):
        try:
            profile_val = json.loads(profile_val)
        except Exception:
            pass

    return ApiResponseWrapper(data=ApiAgentProfile(
        id=row["agent_id"],
        name=row.get("name", ""),
        profile=profile_val,
    ))


@router.get("/experiments/{exp_id}/agents/-/status")
async def list_agent_status_by_day_and_t(
    request: Request,
    exp_id: uuid.UUID,
    day: Optional[int] = Query(None, description="the day for getting agent status"),
    t: Optional[float] = Query(None, description="the time for getting agent status"),
) -> ApiResponseWrapper[List[ApiAgentStatus]]:
    """List agent status by experiment ID, day and time (from ClickHouse/DuckDB)"""

    tenant_id = await request.app.state.get_tenant_id(request)
    exp_row = await _find_started_experiment_by_id(request, exp_id, tenant_id)
    if day is None:
        day = exp_row.get("cur_day", 0)
    if t is None:
        t = exp_row.get("cur_t", 0.0)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_agent_statuses(str(exp_id), day=day, t=t)

    statuses: List[ApiAgentStatus] = []
    for row in rows:
        status_val = row.get("status", "{}")
        if isinstance(status_val, str):
            try:
                status_val = json.loads(status_val)
            except Exception:
                pass
        statuses.append(ApiAgentStatus(
            id=row["agent_id"],
            day=int(row.get("day", day)),
            t=float(row.get("t", t)),
            lng=row.get("lng"),
            lat=row.get("lat"),
            parent_id=row.get("parent_id"),
            action=row.get("action", ""),
            status=status_val,
            created_at=ensure_timezone_aware(row.get("created_at", datetime.now(timezone.utc))),
        ))

    return ApiResponseWrapper(data=statuses)


@router.get("/experiments/{exp_id}/agents/{agent_id}/status")
async def get_agent_status_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentStatus]]:
    """Get agent status by experiment ID and agent ID (from ClickHouse/DuckDB)"""

    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_agent_statuses(str(exp_id), agent_id=agent_id)

    statuses: List[ApiAgentStatus] = []
    for row in rows:
        status_val = row.get("status", "{}")
        if isinstance(status_val, str):
            try:
                status_val = json.loads(status_val)
            except Exception:
                pass
        statuses.append(ApiAgentStatus(
            id=row["agent_id"],
            day=int(row.get("day", 0)),
            t=float(row.get("t", 0.0)),
            lng=row.get("lng"),
            lat=row.get("lat"),
            parent_id=row.get("parent_id"),
            action=row.get("action", ""),
            status=status_val,
            created_at=ensure_timezone_aware(row.get("created_at", datetime.now(timezone.utc))),
        ))

    return ApiResponseWrapper(data=statuses)


@router.get("/experiments/{exp_id}/agents/{agent_id}/survey")
async def get_agent_survey_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentSurvey]]:
    """Get survey by experiment ID and agent ID"""

    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    per_exp_sqlite = request.app.state.per_exp_sqlite
    exp_id_str = str(exp_id)

    raw_surveys = await per_exp_sqlite.query_surveys(exp_id_str, agent_id)
    surveys: List[ApiAgentSurvey] = []
    for row in raw_surveys:
        result_val = row.get("result")
        if isinstance(result_val, str):
            try:
                result_val = json.loads(result_val)
            except Exception:
                pass
        surveys.append(ApiAgentSurvey(
            id=row.get("id", agent_id),
            day=row["day"],
            t=row["t"],
            survey_id=row["survey_id"],
            result=result_val,
            created_at=ensure_timezone_aware(row["created_at"]),
        ))

    raw_pending = await per_exp_sqlite.query_pending_surveys(exp_id_str, agent_id)
    for row in raw_pending:
        surveys.append(ApiAgentSurvey(
            id=agent_id,
            day=row["day"],
            t=row["t"],
            survey_id=row["survey_id"],
            result=None,
            created_at=ensure_timezone_aware(row["created_at"]),
        ))

    surveys.sort(key=lambda x: (x.day, x.t))
    return ApiResponseWrapper(data=surveys)


@router.get("/experiments/{exp_id}/prompt")
async def get_global_prompt_by_day_t(
    request: Request,
    exp_id: uuid.UUID,
    day: Optional[int] = Query(None, description="the day for getting agent status"),
    t: Optional[float] = Query(None, description="the time for getting agent status"),
) -> ApiResponseWrapper[Optional[ApiGlobalPrompt]]:
    """Get global prompt by experiment ID, day and time"""

    tenant_id = await request.app.state.get_tenant_id(request)
    exp_row = await _find_started_experiment_by_id(request, exp_id, tenant_id)
    if day is None:
        day = exp_row.get("cur_day", 0)
    if t is None:
        t = exp_row.get("cur_t", 0.0)

    per_exp_sqlite = request.app.state.per_exp_sqlite
    row = await per_exp_sqlite.query_global_prompt(str(exp_id), day, t)

    if row is None:
        return ApiResponseWrapper(data=None)

    return ApiResponseWrapper(data=ApiGlobalPrompt(
        day=row["day"],
        t=row["t"],
        prompt=row["prompt"],
        created_at=ensure_timezone_aware(row["created_at"]),
    ))


class AgentChatMessage(BaseModel):
    content: str
    day: int
    t: float


@router.post("/experiments/{exp_id}/agents/{agent_id}/dialog")
async def post_agent_dialog(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
    message: AgentChatMessage = Body(...),
) -> ApiResponseWrapper[None]:
    """Send dialog to agent by experiment ID and agent ID"""

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(Experiment).where(
            Experiment.tenant_id == tenant_id, Experiment.id == exp_id
        )
        result = await db.execute(stmt)
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or you don't have permission to access it",
            )
        if ExperimentStatus(experiment.status) != ExperimentStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment not running"
            )

    # Write to per-experiment SQLite (the simulation reads from here)
    per_exp_sqlite = request.app.state.per_exp_sqlite
    ok = await per_exp_sqlite.write_pending_dialog(
        str(exp_id), agent_id, message.day, message.t, message.content
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store dialog; experiment SQLite file may not exist yet",
        )

    return ApiResponseWrapper(data=None)


class AgentSurveyMessage(BaseModel):
    survey_id: uuid.UUID
    day: int
    t: float


@router.post("/experiments/{exp_id}/agents/{agent_id}/survey")
async def post_agent_survey(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
    message: AgentSurveyMessage = Body(...),
) -> ApiResponseWrapper[None]:
    """Send survey to agent by experiment ID and agent ID"""

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(Experiment).where(
            Experiment.tenant_id == tenant_id, Experiment.id == exp_id
        )
        result = await db.execute(stmt)
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or you don't have permission to access it",
            )
        if ExperimentStatus(experiment.status) != ExperimentStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment not running"
            )

        # Verify survey exists
        stmt = select(Survey).where(
            Survey.tenant_id.in_([tenant_id, "", "default"]),
            Survey.id == message.survey_id,
        )
        result = await db.execute(stmt)
        survey = result.scalar_one_or_none()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )
        survey_data = survey.data

    # Write to per-experiment SQLite (the simulation reads from here)
    per_exp_sqlite = request.app.state.per_exp_sqlite
    ok = await per_exp_sqlite.write_pending_survey(
        str(exp_id), agent_id, message.day, message.t, message.survey_id, survey_data
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store survey; experiment SQLite file may not exist yet",
        )

    return ApiResponseWrapper(data=None)


@router.get("/experiments/{exp_id}/agents/{agent_id}/block-timeline")
async def get_agent_block_timeline(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
    day: int = Query(0, ge=0, description="simulation day index (0-based)"),
) -> ApiResponseWrapper[List[ApiTimelineStep]]:
    """Block execution timeline for one agent on the given day."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_block_timeline(str(exp_id), agent_id, day)
    steps: dict[int, list] = {}
    for row in rows:
        s = int(row["simulation_step"])
        steps.setdefault(s, []).append(ApiBlockExecution(
            block_name=row["block_name"],
            func_name=row.get("func_name") or "",
            prompt=row.get("prompt") or "",
            response=row.get("response") or "",
            detail_available=int(row.get("detail_available", 1)),
        ))
    result = [
        ApiTimelineStep(simulation_step=s, block_executions=execs)
        for s, execs in sorted(steps.items())
    ]
    return ApiResponseWrapper(data=result)


@router.get("/experiments/{exp_id}/agents/{agent_id}/daily-plan")
async def get_agent_daily_plan(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
    day: Optional[int] = Query(None, description="simulation day to fetch schedule for"),
) -> ApiResponseWrapper[Optional[ApiDailySchedule]]:
    """Return the LLM-generated daily schedule (CitySim) for a given agent and day."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    schedule = await analytics_db.query_daily_schedule(str(exp_id), agent_id, day)
    if not schedule:
        return ApiResponseWrapper(data=None)

    blocks = [
        ApiDailyScheduleBlock(
            start_time=b.get("start_time", ""),
            duration=int(b.get("duration", 0)),
            activity=b.get("activity", ""),
            description=b.get("description", ""),
        )
        for b in schedule.get("blocks", [])
    ]
    return ApiResponseWrapper(data=ApiDailySchedule(
        day=int(schedule.get("day", 0)),
        blocks=blocks,
        generated_at=schedule.get("generated_at", ""),
    ))


@router.get("/experiments/{exp_id}/agents/{agent_id}/location-timeline")
async def get_agent_location_timeline(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiLocationStep]]:
    """Location type change events for one agent, ordered by simulation_step."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_agent_location_timeline(str(exp_id), agent_id)
    return ApiResponseWrapper(data=[
        ApiLocationStep(
            simulation_step=int(r["simulation_step"]),
            location_type=str(r["location_type"]),
        )
        for r in rows
    ])
