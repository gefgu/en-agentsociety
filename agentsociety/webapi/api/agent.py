from typing import List, Optional, cast
import uuid

from fastapi import APIRouter, HTTPException, Request, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentsociety.webapi.models import ApiResponseWrapper

from ..models.agent import (
    ApiAgentDialog,
    ApiAgentProfile,
    ApiAgentStatus,
    ApiAgentSurvey,
    ApiGlobalPrompt,
    agent_dialog,
    agent_profile,
    agent_status,
    agent_survey,
    global_prompt,
)
from ..models.experiment import Experiment, ExperimentStatus

__all__ = ["router"]

router = APIRouter(tags=["agent"])


async def _find_started_experiment_by_id(
    request: Request, db: AsyncSession, exp_id: uuid.UUID
) -> Experiment:
    tenant_id = await request.app.state.get_tenant_id(request)
    stmt = select(Experiment).where(
        Experiment.tenant_id == tenant_id, Experiment.id == exp_id
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    exp: Experiment = row[0]
    if ExperimentStatus(exp.status) == ExperimentStatus.NOT_STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment not running"
        )
    return exp


@router.get("/experiments/{exp_id}/agents/{agent_id}/dialog")
async def get_agent_dialog_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentDialog]]:
    """Get dialog by experiment ID and agent ID"""

    # Check whether the experiment is started
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        # Generate table name dynamically
        table_name = experiment.agent_dialog_tablename
        table, columns = agent_dialog(table_name)
        stmt = (
            select(table).where(table.c.id == agent_id).order_by(table.c.day, table.c.t)
        )
        rows = (await db.execute(stmt)).all()
        dialogs: List[ApiAgentDialog] = []
        for row in rows:
            dialog = {columns[i]: row[i] for i in range(len(columns))}
            dialogs.append(ApiAgentDialog(**dialog))

        return ApiResponseWrapper(data=dialogs)


@router.get(
    "/experiments/{exp_id}/agents/-/profile",
)
async def list_agent_profile_by_exp_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[List[ApiAgentProfile]]:
    """List agent profile by experiment ID"""

    async with request.app.state.get_db() as db:
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        table_name = experiment.agent_profile_tablename
        table, columns = agent_profile(table_name)
        stmt = select(table)
        rows = (await db.execute(stmt)).all()
        profiles: List[ApiAgentProfile] = []
        for row in rows:
            profile = {columns[i]: row[i] for i in range(len(columns))}
            profiles.append(ApiAgentProfile(**profile))

        return ApiResponseWrapper(data=profiles)


@router.get(
    "/experiments/{exp_id}/agents/{agent_id}/profile",
)
async def get_agent_profile_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[ApiAgentProfile]:
    """Get agent profile by experiment ID and agent ID"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        table_name = experiment.agent_profile_tablename
        table, columns = agent_profile(table_name)
        stmt = select(table).where(table.c.id == agent_id).limit(1)
        row = (await db.execute(stmt)).first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found"
            )
        profile = ApiAgentProfile(**{columns[i]: row[i] for i in range(len(columns))})

        return ApiResponseWrapper(data=profile)


@router.get("/experiments/{exp_id}/agents/-/status")
async def list_agent_status_by_day_and_t(
    request: Request,
    exp_id: uuid.UUID,
    day: Optional[int] = Query(None, description="the day for getting agent status"),
    t: Optional[float] = Query(None, description="the time for getting agent status"),
) -> ApiResponseWrapper[List[ApiAgentStatus]]:
    """List agent status by experiment ID, day and time"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        if day is None:
            day = experiment.cur_day
        if t is None:
            t = experiment.cur_t

        table_name = experiment.agent_status_tablename
        table, columns = agent_status(table_name)
        stmt = select(table).where(table.c.day == day).where(table.c.t == t)
        rows = (await db.execute(stmt)).all()
        statuses: List[ApiAgentStatus] = []
        for row in rows:
            s = {columns[i]: row[i] for i in range(len(columns))}
            statuses.append(ApiAgentStatus(**s))

        return ApiResponseWrapper(data=statuses)


@router.get("/experiments/{exp_id}/agents/{agent_id}/status")
async def get_agent_status_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentStatus]]:
    """Get agent status by experiment ID and agent ID"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        table_name = experiment.agent_status_tablename
        table, columns = agent_status(table_name)
        stmt = (
            select(table).where(table.c.id == agent_id).order_by(table.c.day, table.c.t)
        )
        rows = (await db.execute(stmt)).all()
        statuses: List[ApiAgentStatus] = []
        for row in rows:
            s = {columns[i]: row[i] for i in range(len(columns))}
            statuses.append(ApiAgentStatus(**s))

        return ApiResponseWrapper(data=statuses)


@router.get("/experiments/{exp_id}/agents/{agent_id}/survey")
async def get_agent_survey_by_exp_id_and_agent_id(
    request: Request,
    exp_id: uuid.UUID,
    agent_id: int,
) -> ApiResponseWrapper[List[ApiAgentSurvey]]:
    """Get survey by experiment ID and agent ID"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        table_name = experiment.agent_survey_tablename
        table, columns = agent_survey(table_name)
        stmt = (
            select(table).where(table.c.id == agent_id).order_by(table.c.day, table.c.t)
        )
        rows = (await db.execute(stmt)).all()
        surveys: List[ApiAgentSurvey] = []
        for row in rows:
            survey = {columns[i]: row[i] for i in range(len(columns))}
            surveys.append(ApiAgentSurvey(**survey))

        return ApiResponseWrapper(data=surveys)


@router.get("/experiments/{exp_id}/prompt")
async def get_global_prompt_by_day_t(
    request: Request,
    exp_id: uuid.UUID,
    day: Optional[int] = Query(None, description="the day for getting agent status"),
    t: Optional[float] = Query(None, description="the time for getting agent status"),
) -> ApiResponseWrapper[Optional[ApiGlobalPrompt]]:
    """Get global prompt by experiment ID, day and time"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        experiment = await _find_started_experiment_by_id(request, db, exp_id)

        if day is None:
            day = experiment.cur_day
        if t is None:
            t = experiment.cur_t

        table_name = experiment.global_prompt_tablename
        table, columns = global_prompt(table_name)
        stmt = select(table).where(table.c.day == day).where(table.c.t == t)
        row = (await db.execute(stmt)).first()
        if row is None:
            return ApiResponseWrapper(data=None)
        prompt = ApiGlobalPrompt(**{columns[i]: row[i] for i in range(len(columns))})

        return ApiResponseWrapper(data=prompt)
