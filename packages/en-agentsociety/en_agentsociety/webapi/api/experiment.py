from collections import defaultdict
from datetime import datetime, timezone as _tz
import json
import logging
import uuid
import zipfile
import io
from typing import List, cast, Dict, Tuple

import yaml
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ApiResponseWrapper
from ..models.experiment import ApiExperiment, ApiTime, Experiment, ExperimentStatus
from ..models.metric import ApiMetric
from .const import DEMO_USER_ID

__all__ = ["router"]

router = APIRouter(tags=["experiments"])

logger = logging.getLogger(__name__)


def _row_to_api_experiment(row: Dict) -> ApiExperiment:
    """Convert an analytics-DB dict to ApiExperiment, making datetimes timezone-aware."""
    data = dict(row)
    for key in ("created_at", "updated_at"):
        val = data.get(key)
        if isinstance(val, datetime) and val.tzinfo is None:
            data[key] = val.replace(tzinfo=_tz.utc)
    return ApiExperiment.model_validate(data)


async def _find_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
    tenant_id: str,
) -> Dict:
    """Fetch experiment info from analytics DB; raise 404 if not found or wrong tenant."""
    analytics_db = request.app.state.analytics_db
    row = await analytics_db.query_experiment_info(str(exp_id))
    allowed = {tenant_id, "", "default"}
    if row is None or row.get("tenant_id", "") not in allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    return row


async def _find_started_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
    tenant_id: str,
) -> Dict:
    """Fetch experiment info and verify it has started (status != NOT_STARTED)."""
    row = await _find_experiment_by_id(request, exp_id, tenant_id)
    if ExperimentStatus(row["status"]) == ExperimentStatus.NOT_STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment not running"
        )
    return row


@router.get("/experiments")
async def list_experiments(
    request: Request,
) -> ApiResponseWrapper[List[ApiExperiment]]:
    """List all experiments from the analytics database (DuckDB + ClickHouse)."""
    tenant_id = await request.app.state.get_tenant_id(request)
    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_all_experiment_infos(tenant_id)
    experiments = [_row_to_api_experiment(row) for row in rows]
    return ApiResponseWrapper(data=experiments)


@router.get("/experiments/{exp_id}")
async def get_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[ApiExperiment]:
    """Get experiment by ID from the analytics database."""
    tenant_id = await request.app.state.get_tenant_id(request)
    row = await _find_experiment_by_id(request, exp_id, tenant_id)
    return ApiResponseWrapper(data=_row_to_api_experiment(row))


@router.get("/experiments/{exp_id}/timeline")
async def get_experiment_status_timeline_by_id(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[List[ApiTime]]:
    """Get experiment status timeline by ID (from DuckDB/ClickHouse)."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_started_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_timeline(str(exp_id))
    timeline = [ApiTime(day=int(row["day"]), t=float(row["t"])) for row in rows]
    return ApiResponseWrapper(data=timeline)


@router.delete("/experiments/{exp_id}", status_code=status.HTTP_200_OK)
async def delete_experiment_by_id(
    request: Request,
    exp_id: uuid.UUID,
):
    """Delete experiment by ID."""

    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )
    tenant_id = await request.app.state.get_tenant_id(request)
    if tenant_id == DEMO_USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo user is not allowed to delete experiments",
        )

    # Validate the experiment exists in the analytics DB before deleting files
    await _find_experiment_by_id(request, exp_id, tenant_id)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        try:
            async with db.begin():
                stmt = select(Experiment).where(
                    Experiment.tenant_id == tenant_id, Experiment.id == exp_id
                )
                result = await db.execute(stmt)
                row = result.first()
                if row:
                    experiment: Experiment = row[0]
                    await db.delete(experiment)

            import asyncio as _asyncio
            from pathlib import Path as _Path
            import os as _os

            env = request.app.state.env
            sqlite_path = _Path(env.home_dir) / "sqlite" / f"{exp_id}.db"
            if sqlite_path.exists():
                try:
                    await _asyncio.to_thread(_os.remove, sqlite_path)
                except Exception as e:
                    logging.warning(f"Could not delete per-experiment SQLite {sqlite_path}: {e}")

            duckdb_path = _Path(env.data_dir) / "duckdb" / f"{exp_id}.duckdb"
            if duckdb_path.exists():
                try:
                    await _asyncio.to_thread(_os.remove, duckdb_path)
                except Exception as e:
                    logging.warning(f"Could not delete DuckDB file {duckdb_path}: {e}")

            return ApiResponseWrapper(data={"message": "Experiment deleted successfully"})

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Error deleting experiment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete experiment: {str(e)}",
            )


async def get_experiment_metrics_by_id(
    request: Request,
    exp_id: uuid.UUID,
) -> Tuple[bool, Dict[str, List[ApiMetric]]]:
    """Get metrics for an experiment from DuckDB/ClickHouse."""
    analytics_db = request.app.state.analytics_db
    rows = await analytics_db.query_metrics(str(exp_id))

    if not rows:
        return False, {}

    metrics_by_key: Dict[str, List[ApiMetric]] = defaultdict(list)
    for row in rows:
        api_metric = ApiMetric(
            key=str(row["key"]),
            value=float(row["value"]),
            step=int(row["step"]),
        )
        metrics_by_key[str(row["key"])].append(api_metric)

    return True, metrics_by_key


def serialize_metrics(metrics_by_key: Dict[str, List[ApiMetric]]) -> Dict[str, List[dict]]:
    return {
        key: [m.model_dump() for m in metrics]
        for key, metrics in metrics_by_key.items()
    }


@router.get("/experiments/{exp_id}/metrics")
async def get_experiment_metrics(
    request: Request,
    exp_id: uuid.UUID,
) -> ApiResponseWrapper[Dict[str, List[ApiMetric]]]:
    """Get all metrics for an experiment, aggregated by metric key."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_experiment_by_id(request, exp_id, tenant_id)

    _, metrics_by_key = await get_experiment_metrics_by_id(request, exp_id)
    return ApiResponseWrapper(data=metrics_by_key)


@router.post("/experiments/{exp_id}/export")
async def export_experiment_data(
    request: Request,
    exp_id: uuid.UUID,
) -> StreamingResponse:
    """Export experiment data as a zip file containing YAML and CSV files."""
    tenant_id = await request.app.state.get_tenant_id(request)
    row = await _find_experiment_by_id(request, exp_id, tenant_id)

    analytics_db = request.app.state.analytics_db
    per_exp_sqlite = request.app.state.per_exp_sqlite
    exp_id_str = str(exp_id)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Export experiment info as YAML
        exp_dict = {k: str(v) if isinstance(v, (uuid.UUID,)) else v for k, v in row.items()}
        yaml_content = yaml.dump(exp_dict, allow_unicode=True)
        zip_file.writestr("experiment.yaml", yaml_content)

        # Export metrics from DuckDB/ClickHouse
        found, metrics_by_key = await get_experiment_metrics_by_id(request, exp_id)
        if found:
            serialized_metrics = serialize_metrics(metrics_by_key)
            zip_file.writestr("metrics.json", json.dumps(serialized_metrics, indent=2))

        # Export artifacts
        fs_client = request.app.state.env.fs_client
        artifacts_path = f"exps/{tenant_id}/{exp_id}/artifacts.json"
        artifacts_data = fs_client.download(artifacts_path)
        if artifacts_data:
            zip_file.writestr("artifacts.json", artifacts_data)

        # Export agent profiles from DuckDB as JSON
        profiles = await analytics_db.query_agent_profiles(exp_id_str)
        if profiles:
            zip_file.writestr("agent_profiles.json", json.dumps(profiles, indent=2, default=str))

        # Export dialogs from per-experiment SQLite
        dialog_rows = await per_exp_sqlite._run_async_all_dialogs(exp_id_str)
        if dialog_rows:
            import csv as _csv
            output = io.StringIO()
            writer = _csv.DictWriter(output, fieldnames=list(dialog_rows[0].keys()))
            writer.writeheader()
            writer.writerows(dialog_rows)
            zip_file.writestr("agent_dialog.csv", output.getvalue())

        # Export surveys from per-experiment SQLite
        survey_rows = await per_exp_sqlite._run_async_all_surveys(exp_id_str)
        if survey_rows:
            import csv as _csv
            output = io.StringIO()
            writer = _csv.DictWriter(output, fieldnames=list(survey_rows[0].keys()))
            writer.writeheader()
            writer.writerows(survey_rows)
            zip_file.writestr("agent_survey.csv", output.getvalue())

    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=experiment_{exp_id}_export.zip"
        },
    )


@router.post("/experiments/{exp_id}/artifacts")
async def export_experiment_artifacts(
    request: Request,
    exp_id: uuid.UUID,
) -> StreamingResponse:
    """Export experiment artifacts as a JSON file."""
    tenant_id = await request.app.state.get_tenant_id(request)
    await _find_experiment_by_id(request, exp_id, tenant_id)

    fs_client = request.app.state.env.fs_client
    artifacts_path = f"exps/{tenant_id}/{exp_id}/artifacts.json"
    artifacts_data = fs_client.download(artifacts_path)

    if not artifacts_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifacts not found"
        )

    return StreamingResponse(
        iter([artifacts_data]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=experiment_{exp_id}_artifacts.json"
        },
    )
