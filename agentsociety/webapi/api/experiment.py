import logging
import uuid
from typing import List, cast

from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ApiResponseWrapper
from ..models.experiment import (
    ApiExperiment,
    ApiTime,
    Experiment,
    ExperimentStatus,
)

__all__ = ["router"]

router = APIRouter(tags=["experiments"])


@router.get("/experiments")
async def list_experiments(
    request: Request,
) -> ApiResponseWrapper[List[ApiExperiment]]:
    """List all experiments"""
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        tenant_id = request.app.state.get_tenant_id(request)
        stmt = select(Experiment).where(Experiment.tenant_id == tenant_id)
        results = await db.execute(stmt)
        db_experiments = [row[0] for row in results.all() if len(row) > 0]
        experiments = cast(List[ApiExperiment], db_experiments)
        return ApiResponseWrapper(data=experiments)


@router.get("/experiments/{exp_id}")
async def get_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[ApiExperiment]:
    """Get experiment by ID"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        tenant_id = request.app.state.get_tenant_id(request)
        stmt = select(Experiment).where(
            Experiment.tenant_id == tenant_id, Experiment.id == exp_id
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row or len(row) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        exp = row[0]
        return ApiResponseWrapper(data=exp)


@router.get("/experiments/{exp_id}/timeline")
async def get_experiment_status_timeline_by_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[List[ApiTime]]:
    """Get experiment status timeline by ID"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        tenant_id = request.app.state.get_tenant_id(request)
        stmt = select(Experiment).where(
            Experiment.tenant_id == tenant_id, Experiment.id == exp_id
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row or len(row) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        experiment: Experiment = row[0]
        # Check if the experiment has started
        if ExperimentStatus(experiment.status) == ExperimentStatus.NOT_STARTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Experiment has not started yet",
            )

        # Get timeline from agent status table
        table_name = experiment.agent_status_tablename

        # the table_name is safe to use in the query
        # it is generated from the experiment id
        query = text(
            f"""
            SELECT day, t 
            FROM {table_name} 
            GROUP BY day, t 
            ORDER BY day, t
        """
        )

        results = (await db.execute(query)).all()
        timeline = [ApiTime(day=int(row[0]), t=float(row[1])) for row in results]

        return ApiResponseWrapper(data=timeline)


@router.delete("/experiments/{exp_id}", status_code=status.HTTP_200_OK)
async def delete_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
):
    """Delete experiment by ID"""

    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        try:
            # Start transaction
            async with db.begin():
                tenant_id = request.app.state.get_tenant_id(request)
                stmt = select(Experiment).where(
                    Experiment.tenant_id == tenant_id, Experiment.id == exp_id
                )
                result = await db.execute(stmt)
                row = result.first()
                if not row or len(row) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
                    )
                experiment: Experiment = row[0]

                # Get all table names that need to be deleted
                table_names = [
                    experiment.agent_profile_tablename,
                    experiment.agent_status_tablename,
                    experiment.agent_dialog_tablename,
                    experiment.agent_survey_tablename
                ]

                # Delete related tables
                for table_name in table_names:
                    try:
                        query = text(f"DROP TABLE IF EXISTS {table_name}")
                        await db.execute(query)
                    except Exception as e:
                        logging.error(f"Error dropping table {table_name}: {str(e)}")
                        # Continue execution without interruption

                # Delete experiment record
                await db.delete(experiment)

            # Transaction will be committed automatically

            return ApiResponseWrapper(data={"message": "Experiment deleted successfully"})

        except Exception as e:
            logging.error(f"Error deleting experiment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete experiment: {str(e)}"
            )
