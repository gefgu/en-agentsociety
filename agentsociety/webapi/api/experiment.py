import csv
import io
import logging
import uuid
import zipfile
from typing import List, cast

import yaml
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ApiResponseWrapper
from ..models.agent import (
    agent_dialog,
    agent_profile,
    agent_status,
    agent_survey,
    global_prompt,
)
from ..models.experiment import ApiExperiment, ApiTime, Experiment, ExperimentStatus

__all__ = ["router"]

router = APIRouter(tags=["experiments"])


@router.get("/experiments")
async def list_experiments(
    request: Request,
) -> ApiResponseWrapper[List[ApiExperiment]]:
    """List all experiments"""
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        tenant_id = await request.app.state.get_tenant_id(request)
        stmt = (
            select(Experiment)
            .where(Experiment.tenant_id == tenant_id)
            .order_by(Experiment.created_at.desc())
        )
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
        tenant_id = await request.app.state.get_tenant_id(request)
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
        tenant_id = await request.app.state.get_tenant_id(request)
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
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        try:
            # Start transaction
            async with db.begin():
                stmt = select(Experiment).where(
                    Experiment.tenant_id == tenant_id, Experiment.id == exp_id
                )
                result = await db.execute(stmt)
                row = result.first()
                if not row or len(row) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Experiment not found",
                    )
                experiment: Experiment = row[0]

                # Get all table names that need to be deleted
                table_names = [
                    experiment.agent_profile_tablename,
                    experiment.agent_status_tablename,
                    experiment.agent_dialog_tablename,
                    experiment.agent_survey_tablename,
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

            return ApiResponseWrapper(
                data={"message": "Experiment deleted successfully"}
            )

        except Exception as e:
            logging.error(f"Error deleting experiment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete experiment: {str(e)}",
            )


@router.post("/experiments/{exp_id}/export")
async def export_experiment_data(
    request: Request,
    exp_id: uuid.UUID,
) -> StreamingResponse:
    """Export experiment data as a zip file containing YAML and CSV files"""

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        tenant_id = await request.app.state.get_tenant_id(request)

        # Get experiment info
        stmt = select(Experiment).where(
            Experiment.tenant_id == tenant_id, Experiment.id == exp_id
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        experiment: Experiment = row

        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Export experiment info as YAML
            exp_dict = experiment.to_dict()
            yaml_content = yaml.dump(exp_dict, allow_unicode=True)
            zip_file.writestr("experiment.yaml", yaml_content)

            # get all tables
            tables = {
                "agent_profile": agent_profile(experiment.agent_profile_tablename),
                "agent_status": agent_status(experiment.agent_status_tablename),
                "agent_survey": agent_survey(experiment.agent_survey_tablename),
                "agent_dialog": agent_dialog(experiment.agent_dialog_tablename),
                "global_prompt": global_prompt(experiment.global_prompt_tablename),
            }

            for table_name, (db_table, columns) in tables.items():
                query = select(db_table)
                results = await db.execute(query)
                rows = results.all()

                if rows:
                    # create csv file
                    output = io.StringIO()
                    writer = csv.writer(output)
                    # write header
                    writer.writerow([col for col in columns])
                    # write data
                    writer.writerows(rows)

                    zip_file.writestr(f"{table_name}.csv", output.getvalue())
                    output.close()

        # prepare response
        zip_buffer.seek(0)
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=experiment_{exp_id}_export.zip"
            },
        )
