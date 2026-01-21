import csv
import io
import json
import pandas as pd
import uuid
import os
from typing import Any, Dict, List, Optional, cast

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
    Query
)
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
import clickhouse_connect

from ...configs import EnvConfig
from ..models import ApiResponseWrapper
from .const import DEMO_USER_ID
from .timezone import ensure_timezone_aware
from joblib import Parallel, delayed
from ..constants.poi_mapping import category_mapping

__all__ = ["router"]

router = APIRouter(tags=["agent_visits"])


@router.get("/agent-visits")
async def list_agent_visits(
    request: Request,
    exp_id: Optional[str] = Query(None, description="Filter by experiment ID")
) -> ApiResponseWrapper[List[Dict[str, Any]]]:
    """List all agent visits from ClickHouse"""
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host="localhost",
            port=8123,
            username="default",
            password="clickhouse",
            database="fastsociety"
        )
        
        # Query example
        query = "SELECT * FROM step_agent_status"
        params = {}
        if exp_id:
            query += " WHERE exp_id = {exp_id:String}"
            params["exp_id"] = exp_id

        visit_result = client.query(query, parameters=params)
        
        # Convert to list of dicts
        columns = visit_result.column_names
        rows = [dict(zip(columns, row)) for row in visit_result.result_rows]
        simulation_df = pd.DataFrame(rows)

        query = "SELECT * FROM agent_location_type"
        params = {}
        if exp_id:
            query += " WHERE exp_id = {exp_id:String}"
            params["exp_id"] = exp_id

        location_types_result = client.query(query, parameters=params)
        
        # Convert to list of dicts
        columns = location_types_result.column_names
        rows = [dict(zip(columns, row)) for row in location_types_result.result_rows]
        location_types_df = pd.DataFrame(rows)

        simulation_df = transform_time_into_timestamps(simulation_df)

        visitation_df = extract_visits(simulation_df)

        visitation_df = visitation_df.sort_values("start_step")
        location_types_df = location_types_df.sort_values("simulation_step")

        visitation_df["start_step"] = visitation_df["start_step"].astype("int64")
        location_types_df["simulation_step"] = location_types_df["simulation_step"].astype("int64")

        # Convert the "by" columns (IDs) just in case they also mismatch
        visitation_df["agent_id"] = visitation_df["agent_id"].astype("int64")
        location_types_df["agent_id"] = location_types_df["agent_id"].astype("int64")

        merged_df = pd.merge_asof(
          visitation_df,
          location_types_df,
          left_on="start_step",
          right_on="simulation_step",
          by="agent_id",
          direction="backward",
          tolerance=6
        )

        merged_df["location_type"] = merged_df["location_type"].fillna("UNKNOWN")
        merged_df["purpose"] = merged_df["location_type"].apply(map_visit_purpose)

        rows = merged_df.where(pd.notnull(merged_df), None).to_dict(orient="records")
        
        return ApiResponseWrapper(data=rows)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying ClickHouse: {str(e)}"
        )


def _extract_visits_vectorized_from_agent(
    agent_id: int,
    agent_data: pd.DataFrame,
    min_duration_minutes: float,
    movement_epsilon: float = 0.0001,
) -> list:
    """
    Vectorized extraction of visits for a single agent.

    :param agent_id (int): ID of the agent.
    :param agent_data (pd.DataFrame): Dataframe with agent's data.
    :param min_duration_minutes (float): Minimum duration of a visit in minutes.
    :param movement_epsilon (float): Minimum movement to consider a change in location.
    """

    df = agent_data.sort_values("timestamp").reset_index(drop=True)

    if len(df) == 0:
        return []

    df["lat_diff"] = df["lat"].diff().abs().fillna(0)
    df["lng_diff"] = df["lng"].diff().abs().fillna(0)

    df["is_moving"] = (df["lat_diff"] > movement_epsilon) | (
        df["lng_diff"] > movement_epsilon
    )

    df["visit_number"] = (df["is_moving"] != df["is_moving"].shift()).cumsum()

    stopped_blocks = (
        df[~df["is_moving"]]
        .groupby("visit_number")
        .agg(
            {
                "timestamp": ["first", "last"],
                "lat": "first",
                "lng": "first",
                "simulation_step": ["first", "last"],
                # "status": lambda x: x.dropna().tolist(),
            }
        )
    )

    stopped_blocks.columns = [
        "start_timestamp",
        "end_timestamp",
        "lat",
        "lng",
        "start_step",
        "end_step",
        # "status",
    ]
    stopped_blocks = stopped_blocks.reset_index(drop=True)

    stopped_blocks["duration_minutes"] = (
        stopped_blocks["end_timestamp"] - stopped_blocks["start_timestamp"]
    ).dt.total_seconds() / 60


    visits_df = stopped_blocks[
        stopped_blocks["duration_minutes"] >= min_duration_minutes
    ].copy()

    visits_df["agent_id"] = agent_id
    visits_df["day_of_week"] = visits_df["start_timestamp"].dt.day_name().str.lower()

    return visits_df.to_dict(orient="records")
  
def extract_visits(
    simulation_df: pd.DataFrame,
    min_duration_minutes: float = 10.0,
    filename=None,
) -> pd.DataFrame:
    """
    Extract visits from simulation dataframe using custom logic for discrete timestep data.

    For simulation data where agents act in discrete time increments (e.g., 10 minutes),
    this function groups consecutive timesteps at the same location into visits.

    :param simulation_df (pd.DataFrame): Simulation dataframe with columns: id, timestamp, lat, lng, status, t
    :param spatial_threshold_km (float): Maximum distance in km to consider two points as same location (default: 0.1)
    :param min_duration_minutes (float): Minimum visit duration in minutes to be considered a stop.
                                         A single GPS log (0 duration) means the agent just passed through.
                                         Two GPS logs at the same location = 10 minutes (or one timestep).
                                         Default: 10.0 minutes (filters out single-timestep passings).

    :return pd.DataFrame: Dataframe with visits including start/end timestamps and duration
    """
    # Filter out rows without location data
    df = simulation_df[
        simulation_df["lat"].notna() & simulation_df["lng"].notna()
    ].copy()
    df = df.sort_values(["agent_id", "timestamp"]).reset_index(drop=True)

    # Parallel returns list of lists (one per agent), need to flatten
    nested_visits = Parallel(n_jobs=-1)(
        delayed(_extract_visits_vectorized_from_agent)(
            agent_id, agent_data, min_duration_minutes
        )
        for agent_id, agent_data in df.groupby("agent_id")
    )

    # Flatten the list of lists
    visits_list = [visit for agent_visits in nested_visits for visit in agent_visits]  # type: ignore

    # Create DataFrame
    visits_df = pd.DataFrame(visits_list)

    if visits_df.empty:
        return visits_df

    # Calculate duration in minutes
    visits_df["duration_minutes"] = (
        visits_df["end_timestamp"] - visits_df["start_timestamp"]
    ).dt.total_seconds() / 60  # type: ignore

    return visits_df


def transform_time_into_timestamps(
    simulation_df: pd.DataFrame, start_date: str = "2024-01-01", simulation_step_interval_seconds: int = 600
) -> pd.DataFrame:
    """
    Transform the time column into timestamps.

    :param simulation_df (pd.DataFrame): Simulation dataframe.
    :param start_date (str): Starting date in format 'YYYY-MM-DD'. Default is "2024-01-01".
    :param simulation_step_interval_seconds (int): Interval in seconds for each simulation step. Default is 600 (10 minutes).

    :return pd.DataFrame: Simulation dataframe with timestamps.
    """
    # Convert day to timedelta (days) and t to timedelta (seconds)
    simulation_df["timestamp"] = (
        pd.to_datetime(start_date)
        + pd.to_timedelta(simulation_df["simulation_step"] * simulation_step_interval_seconds, unit="s")
    )
    return simulation_df


def map_visit_purpose(location_type: str):
    """Map visit purpose based on location type and agent status"""
    try:
      location_type = location_type.lower()

      if location_type == "home":
          return "HOME"
      elif location_type == "work":
          return "WORK"
      elif ("amenity" in location_type) or ("leisure" in location_type):
          location_type = location_type.replace("amenity|", "").replace("leisure|", "")
          location_type = category_mapping.get(location_type, "UNKNOWN")
          if location_type == "UNKNOWN":
              print("Mapped purpose for location type:", location_type)
          return location_type
      else:
          print("No matching purpose for location type:", location_type)
          return "UNKNOWN"
    except Exception as e:
      print("Error mapping visit purpose:", str(e))
      return "UNKNOWN"
