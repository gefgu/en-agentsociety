"""Mobility-metrics comparison API.

Compares up to two trajectory sources — each a selected simulation (read from
ClickHouse or a DuckDB file) or an uploaded trajectory file — and returns
fastmob-vis ECharts option JSON + metrics for native rendering in the frontend.
"""

import os
import tempfile
from typing import Optional, Tuple

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from ..models import ApiResponseWrapper

__all__ = ["router"]

router = APIRouter(tags=["mobility"])


@router.get("/mobility/datasource")
async def get_datasource_status(request: Request) -> ApiResponseWrapper[dict]:
    """Report whether ClickHouse is reachable.

    When false, the UI should ask the user to upload an experiment's ``.duckdb``
    file for any simulation source.
    """
    from ..datasource import clickhouse_available

    return ApiResponseWrapper(data={"clickhouse": clickhouse_available()})


def _experiment_dataframe(
    request: Request,
    exp_id: str,
    duckdb_upload: Optional[bytes],
) -> pd.DataFrame:
    """Build a normalised trajectory DataFrame for a simulation source."""
    from ..api.visits import get_agent_visits
    from ..datasource import clickhouse_available, resolve_local_duckdb_path
    from ..mobility import trajdf_from_visits_df

    if clickhouse_available():
        from ..clickhouse import get_clickhouse_client

        visits = get_agent_visits(client=get_clickhouse_client(), exp_id=exp_id)
        return trajdf_from_visits_df(visits)

    # ClickHouse unavailable -> need a DuckDB file (uploaded or local).
    if duckdb_upload is not None:
        tmp = tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False)
        try:
            tmp.write(duckdb_upload)
            tmp.flush()
            tmp.close()
            visits = get_agent_visits(exp_id=exp_id, duckdb_path=tmp.name)
            return trajdf_from_visits_df(visits)
        finally:
            os.unlink(tmp.name)

    local = resolve_local_duckdb_path(request, exp_id)
    if local is not None:
        visits = get_agent_visits(exp_id=exp_id, duckdb_path=str(local))
        return trajdf_from_visits_df(visits)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "ClickHouse is unavailable and no DuckDB file was provided for "
            f"experiment {exp_id}. Upload the experiment's .duckdb file."
        ),
    )


def _load_source(
    request: Request,
    *,
    type_: Optional[str],
    exp_id: Optional[str],
    file: Optional[UploadFile],
    file_bytes: Optional[bytes],
    duckdb_bytes: Optional[bytes],
    label: Optional[str],
) -> Tuple[pd.DataFrame, str]:
    from ..mobility import trajdf_from_upload

    if type_ == "file":
        if file is None or file_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file source selected but no file was uploaded",
            )
        df = trajdf_from_upload(file_bytes, file.filename or "upload.parquet")
        return df, (label or file.filename or "uploaded file")

    if type_ == "experiment":
        if not exp_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="experiment source selected but no exp_id was provided",
            )
        df = _experiment_dataframe(request, exp_id, duckdb_bytes)
        return df, (label or exp_id)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"unknown source type: {type_!r} (expected 'experiment' or 'file')",
    )


def _source_provided(type_: Optional[str], exp_id: Optional[str], file: Optional[UploadFile]) -> bool:
    """Return True when the caller supplied enough params to identify a source."""
    if type_ == "experiment":
        return bool(exp_id)
    if type_ == "file":
        return file is not None
    return False


@router.post("/mobility/compare")
async def compare_sources(
    request: Request,
    a_type: Optional[str] = Form(None),
    a_exp_id: Optional[str] = Form(None),
    a_label: Optional[str] = Form(None),
    a_file: Optional[UploadFile] = File(None),
    a_duckdb: Optional[UploadFile] = File(None),
    b_type: Optional[str] = Form(None),
    b_exp_id: Optional[str] = Form(None),
    b_label: Optional[str] = Form(None),
    b_file: Optional[UploadFile] = File(None),
    b_duckdb: Optional[UploadFile] = File(None),
) -> ApiResponseWrapper[dict]:
    from ..mobility import build_comparison_payload, build_single_payload

    try:
        a_file_bytes = await a_file.read() if a_file is not None else None
        a_duckdb_bytes = await a_duckdb.read() if a_duckdb is not None else None

        if not _source_provided(a_type, a_exp_id, a_file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one source (A) must be provided.",
            )

        df_a, label_a = _load_source(
            request, type_=a_type, exp_id=a_exp_id, file=a_file,
            file_bytes=a_file_bytes, duckdb_bytes=a_duckdb_bytes, label=a_label,
        )

        if _source_provided(b_type, b_exp_id, b_file):
            b_file_bytes = await b_file.read() if b_file is not None else None
            b_duckdb_bytes = await b_duckdb.read() if b_duckdb is not None else None
            df_b, label_b = _load_source(
                request, type_=b_type, exp_id=b_exp_id, file=b_file,
                file_bytes=b_file_bytes, duckdb_bytes=b_duckdb_bytes, label=b_label,
            )
            if label_a == label_b:
                label_a, label_b = f"{label_a} (A)", f"{label_b} (B)"
            payload = build_comparison_payload(df_a, df_b, label_a, label_b)
        else:
            payload = build_single_payload(df_a, label_a)

        return ApiResponseWrapper(data=payload)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error building comparison report: {str(e)}",
        )
