import pandas as pd
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
    Query,
)

from ..models import ApiResponseWrapper
from joblib import Parallel, delayed
from ..constants.poi_mapping import category_mapping
import numpy as np

__all__ = ["router", "get_agent_visits", "build_visits_from_frames"]

router = APIRouter(tags=["agent_visits"])


def resolve_visits(request: Request, exp_id: str) -> pd.DataFrame:
    """Load visits for an experiment from ClickHouse, falling back to local DuckDB.

    Probes ClickHouse first; if it is unavailable, reads the experiment's local
    ``.duckdb`` file. Raises 503 when neither backend can serve the data.
    """
    from ..datasource import (
        clickhouse_available,
        resolve_local_duckdb_path,
    )

    if clickhouse_available():
        from ..clickhouse import get_clickhouse_client

        return get_agent_visits(client=get_clickhouse_client(), exp_id=exp_id)

    duckdb_path = resolve_local_duckdb_path(request, exp_id)
    if duckdb_path is not None:
        return get_agent_visits(exp_id=exp_id, duckdb_path=str(duckdb_path))

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "No analytics backend available: ClickHouse is unreachable and no "
            f"local DuckDB file was found for experiment {exp_id}."
        ),
    )


@router.get("/agent-visits")
async def list_agent_visits(
    request: Request,
    exp_id: Optional[str] = Query(None, description="Filter by experiment ID"),
) -> ApiResponseWrapper[List[Dict[str, Any]]]:
    """List all agent visits from the analytics backend (ClickHouse or DuckDB)."""
    try:
        if exp_id is None:
            return ApiResponseWrapper(data=[])

        rows = resolve_visits(request, exp_id).to_dict(orient="records")

        return ApiResponseWrapper(data=rows)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying analytics backend: {str(e)}",
        )
    

@router.get("/visits/purpose-distributions")
async def get_visit_purpose_distributions(
    request: Request,
    exp_id: Optional[str] = Query(None, description="Filter by experiment ID"),
) -> ApiResponseWrapper[Dict[str, Any]]:
    """Visit-purpose distribution from the analytics backend (ClickHouse or DuckDB)."""

    try:
        if exp_id is None:
            return ApiResponseWrapper(data={})

        visits_df = resolve_visits(request, exp_id)
        if visits_df.empty:
            return ApiResponseWrapper(data={"distributions": [], "total_visits": 0})
        rows = extract_visit_purpose_distributions(visits_df).to_dict(orient="records")

        data = {
            "distributions": rows,
            "total_visits": len(visits_df),
        }

        return ApiResponseWrapper(data=data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying analytics backend: {str(e)}",
        )

@router.get("/visits/daily-activity")
async def get_daily_activity_distribution(
    request: Request,
    exp_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    step_minutes: int = Query(10, description="Time step resolution in minutes"),
) -> ApiResponseWrapper[Dict[str, Any]]:
    """
    Get the percentage of agents engaged in each purpose for every time step of the day.
    Replaces the frontend 'DATA PROCESSING' logic.
    """
    try:
        if exp_id is None:
            return ApiResponseWrapper(data={})

        # 1. Get raw visits with 'start_timestamp', 'end_timestamp', and 'purpose'
        visits_df = resolve_visits(request, exp_id)

        # 2. Process into time-series buckets
        result = extract_daily_activity_distribution(visits_df, step_minutes)

        return ApiResponseWrapper(data=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating daily activity: {str(e)}",
        )


def get_agent_visits(client=None, exp_id: str = "", duckdb_path=None) -> pd.DataFrame:
    """Load the per-visit DataFrame for an experiment from ClickHouse or DuckDB.

    Provide a ClickHouse ``client`` or a ``duckdb_path`` — the underlying tables
    share one schema, so the downstream processing is identical.
    """
    from ..datasource import load_experiment_frames

    simulation_df, location_types_df = load_experiment_frames(
        exp_id, client=client, duckdb_path=duckdb_path
    )
    return build_visits_from_frames(simulation_df, location_types_df)


def build_visits_from_frames(
    simulation_df: pd.DataFrame,
    location_types_df: pd.DataFrame,
) -> pd.DataFrame:
    """Turn raw ``step_agent_status`` + ``agent_location_type`` frames into visits.

    Extracted from :func:`get_agent_visits` so the same logic is reused regardless
    of whether the frames came from ClickHouse or a DuckDB file.
    """
    if simulation_df is None or simulation_df.empty:
        return pd.DataFrame()

    simulation_df = transform_time_into_timestamps(simulation_df)

    visitation_df = extract_visits(simulation_df)
    if visitation_df.empty:
        return visitation_df

    if location_types_df is None or location_types_df.empty:
        location_types_df = pd.DataFrame(
            columns=["exp_id", "simulation_step", "timestamp", "agent_id", "location_type"]
        )

    visitation_df = visitation_df.sort_values("start_step")
    location_types_df = location_types_df.sort_values("simulation_step")

    visitation_df["start_step"] = visitation_df["start_step"].astype("int64")
    visitation_df["end_step"] = visitation_df["end_step"].astype("Int64")  # Handle null
    location_types_df["simulation_step"] = location_types_df["simulation_step"].astype(
        "int64"
    )

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
        tolerance=6,
    )

    merged_df["location_type"] = merged_df["location_type"].fillna("UNKNOWN")
    merged_df["purpose"] = merged_df["location_type"].apply(map_visit_purpose)

    merged_df = merged_df.where(pd.notnull(merged_df), None)

    return merged_df


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


def extract_visit_purpose_distributions(
    visits_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Get visit purpose distributions from visits dataframe.

    :param visits_df (pd.DataFrame): Visits dataframe with 'purpose' column.

    :return pd.DataFrame: Dataframe with purpose distributions.
    """
    # 1. Get raw counts
    purpose_counts = visits_df["purpose"].value_counts().reset_index()
    
    # Rename columns explicitly to avoid confusion
    # value_counts().reset_index() returns columns: [original_name, 'count']
    purpose_counts.columns = ["purpose", "count"]

    # 2. Calculate proportion based on the 'count' column
    total = purpose_counts["count"].sum()
    purpose_counts["proportion"] = purpose_counts["count"] / total

    df = purpose_counts[["purpose", "proportion", "count"]] 

    # Reorder columns to match your desired output
    return df


def transform_time_into_timestamps(
    simulation_df: pd.DataFrame,
    start_date: str = "2024-01-01",
    simulation_step_interval_seconds: int = 600,
) -> pd.DataFrame:
    """
    Transform the time column into timestamps.

    :param simulation_df (pd.DataFrame): Simulation dataframe.
    :param start_date (str): Starting date in format 'YYYY-MM-DD'. Default is "2024-01-01".
    :param simulation_step_interval_seconds (int): Interval in seconds for each simulation step. Default is 600 (10 minutes).

    :return pd.DataFrame: Simulation dataframe with timestamps.
    """
    # Convert day to timedelta (days) and t to timedelta (seconds)
    simulation_df["timestamp"] = pd.to_datetime(start_date) + pd.to_timedelta(
        simulation_df["simulation_step"] * simulation_step_interval_seconds, unit="s"
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
            location_type = location_type.replace("amenity|", "").replace(
                "leisure|", ""
            )
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


def extract_daily_activity_distribution(
    visits_df: pd.DataFrame,
    step_minutes: int = 10
) -> Dict[str, Any]:
    """
    Calculate the percentage of agents engaged in each purpose at every time step of the day.
    
    Returns:
        {
            "time_labels": ["00:00", "00:10", ...],
            "series": {
                "HOME": [50.5, 50.2, ...],
                "WORK": [20.0, 25.5, ...],
                ...
            }
        }
    """
    if visits_df.empty:
        return {"time_labels": [], "series": {}}

    # --- 1. SETUP TIME STEPS ---
    total_minutes = 24 * 60
    total_steps = int(total_minutes / step_minutes)  # e.g., 144 steps for 10-min
    
    # Generate X-axis labels (e.g., "00:00", "00:10")
    time_labels = []
    for i in range(total_steps):
        total_m = i * step_minutes
        h = total_m // 60
        m = total_m % 60
        time_labels.append(f"{h:02d}:{m:02d}")

    # --- 2. PREPARE DATA ---
    # Handle missing purposes
    visits_df["purpose"] = visits_df["purpose"].fillna("UNKNOWN")
    
    # Get unique purposes and map them to array indices for speed
    unique_purposes = sorted(visits_df["purpose"].unique())
    purpose_to_idx = {p: i for i, p in enumerate(unique_purposes)}
    num_purposes = len(unique_purposes)

    # Initialize counters: [TimeSteps x NumPurposes]
    counts = np.zeros((total_steps, num_purposes), dtype=int)

    # --- 3. POPULATE BUCKETS ---
    # Convert timestamps to "minutes from midnight"
    # We use .dt accessor to get hour/minute efficiently
    starts_min = visits_df["start_timestamp"].dt.hour * 60 + visits_df["start_timestamp"].dt.minute
    ends_min = visits_df["end_timestamp"].dt.hour * 60 + visits_df["end_timestamp"].dt.minute
    
    # Calculate step indices
    start_indices = (starts_min // step_minutes).astype(int).values
    end_indices = (ends_min // step_minutes).astype(int).values
    purposes_indices = visits_df["purpose"].map(purpose_to_idx).values

    # Iterate and fill buckets (Vectorized iteration)
    for start_idx, end_idx, p_idx in zip(start_indices, end_indices, purposes_indices):
        if start_idx <= end_idx:
            # Standard case (e.g., 10:00 to 11:00)
            # Add 1 to end_idx because Python slicing is exclusive at the end
            counts[start_idx : end_idx + 1, p_idx] += 1
        else:
            # Day wrap-around case (e.g., 23:50 to 00:10)
            # 1. From start to end of day
            counts[start_idx : total_steps, p_idx] += 1
            # 2. From start of day to end time
            counts[0 : end_idx + 1, p_idx] += 1

    # --- 4. CALCULATE PROPORTIONS ---
    # Sum across purposes to get total active agents at each time step
    step_totals = counts.sum(axis=1, keepdims=True)
    
    # Avoid division by zero
    safe_totals = np.where(step_totals == 0, 1, step_totals)
    
    # Calculate percentage
    percentages = (counts / safe_totals) * 100
    
    # Round to 1 decimal place (matches .toFixed(1) in JS)
    percentages = np.round(percentages, 1)

    # --- 5. FORMAT OUTPUT ---
    series_data = {}
    for p_str, p_idx in purpose_to_idx.items():
        # Convert numpy array to standard python list for JSON serialization
        series_data[p_str] = percentages[:, p_idx].tolist()

    return {
        "time_labels": time_labels,
        "series": series_data
    }