"""Build a mobility-metrics comparison payload from two trajectory sources.

This re-implements (does NOT import) the orchestration of the sibling
``citybehavex`` HTML report, but returns a JSON-serialisable payload of skmob-vis
ECharts options + metrics so the React frontend renders the charts natively.

A "source" here is a normalised trajectory DataFrame with the columns:
``uid, datetime, lat, lng`` and, optionally, ``purpose, end_timestamp,
duration_minutes``. Use :func:`trajdf_from_visits_df` (for data extracted from a
simulation's ``step_agent_status``) or :func:`trajdf_from_upload` (for an
uploaded parquet/csv) to produce one.
"""

from __future__ import annotations

import io
import importlib
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Column auto-detection candidates (mirrors citybehavex's report loader).
_DATETIME_CANDIDATES = [
    "datetime", "start_timestamp", "timestamp", "check-in_time",
    "start_time", "_start_time", "checkin_time", "time", "date",
]
_LAT_CANDIDATES = ["lat", "latitude"]
_LNG_CANDIDATES = ["lng", "lon", "longitude", "long"]
_UID_CANDIDATES = ["uid", "user_id", "user", "agent_id", "userid"]
_DURATION_CANDIDATES = ["duration_minutes", "duration", "dwell_minutes", "duration_hours"]
_ACTIVITY_CANDIDATES = ["purpose", "activity", "act", "location_type", "category", "purpose_d"]
_END_TS_CANDIDATES = ["end_timestamp", "_end_time", "end_time"]

CPC_H3_RESOLUTIONS = (7, 8, 9)
STVD_RESOLUTIONS = [7, 9]
_H3_FALLBACK_RESOLUTION = 10
_PROFILE_LABELS = ("Routiner", "Regular", "Scouter")
_PROFILE_METRICS = (
    "degree_of_return",
    "intermittency",
    "regularity",
    "diversity",
    "stationarity",
    "entropy",
)
_PROFILE_BOXPLOT_METRICS = ("regularity", "diversity", "stationarity", "entropy")
_PROFILE_LABEL_MAP = {
    "routiner": "Routiner",
    "routiners": "Routiner",
    "regular": "Regular",
    "regulars": "Regular",
    "scouter": "Scouter",
    "scouters": "Scouter",
}
_PROFILE_COLORS = {
    "Routiner": "#2e7d32",
    "Regular": "#1565c0",
    "Scouter": "#c62828",
}
_DATASET_SYMBOLS = ("circle", "triangle", "diamond", "rect", "roundRect", "pin")


# ---------------------------------------------------------------------------
# Source normalisation
# ---------------------------------------------------------------------------

def _detect_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols_lower = {str(c).lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce an arbitrary trajectory/visit DataFrame to the standard schema."""
    datetime_col = _detect_column(df, _DATETIME_CANDIDATES)
    lat_col = _detect_column(df, _LAT_CANDIDATES)
    lng_col = _detect_column(df, _LNG_CANDIDATES)
    uid_col = _detect_column(df, _UID_CANDIDATES)
    missing = [
        name
        for name, col in [
            ("datetime", datetime_col), ("latitude", lat_col),
            ("longitude", lng_col), ("user id", uid_col),
        ]
        if col is None
    ]
    if missing:
        raise ValueError(
            "trajectory source is missing recognizable columns for: "
            + ", ".join(missing)
        )

    out = pd.DataFrame(
        {
            "uid": df[uid_col],
            "datetime": pd.to_datetime(df[datetime_col], errors="coerce"),
            "lat": pd.to_numeric(df[lat_col], errors="coerce"),
            "lng": pd.to_numeric(df[lng_col], errors="coerce"),
        }
    )
    activity_col = _detect_column(df, _ACTIVITY_CANDIDATES)
    if activity_col is not None:
        out["purpose"] = df[activity_col].astype(str).to_numpy()
    end_col = _detect_column(df, _END_TS_CANDIDATES)
    if end_col is not None:
        out["end_timestamp"] = pd.to_datetime(df[end_col], errors="coerce").to_numpy()
    duration_col = _detect_column(df, _DURATION_CANDIDATES)
    if duration_col is not None:
        out["duration_minutes"] = pd.to_numeric(df[duration_col], errors="coerce").to_numpy()

    out = out.dropna(subset=["uid", "datetime", "lat", "lng"])
    out = out[out["lat"].between(-90, 90) & out["lng"].between(-180, 180)]
    out = out.sort_values(["uid", "datetime"]).reset_index(drop=True)
    if out.empty:
        raise ValueError("trajectory source has no valid (uid, datetime, lat, lng) rows")
    return out


def trajdf_from_visits_df(visits_df: pd.DataFrame) -> pd.DataFrame:
    """Normalise the per-visit DataFrame produced by ``build_visits_from_frames``."""
    if visits_df is None or visits_df.empty:
        raise ValueError("no visits available for this experiment")
    return _normalise(visits_df)


def trajdf_from_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load + normalise an uploaded parquet/csv trajectory file."""
    name = (filename or "").lower()
    buffer = io.BytesIO(file_bytes)
    if name.endswith(".csv") or name.endswith(".txt"):
        df = pd.read_csv(buffer)
    else:
        # default to parquet for .parquet/.pq and unknown extensions
        df = pd.read_parquet(buffer)
    return _normalise(df)


def _traj(df: pd.DataFrame):
    import skmob2

    return skmob2.TrajDataFrame(
        df,
        datetime_col="datetime",
        lat_col="lat",
        lng_col="lng",
        uid_col="uid",
    )


# ---------------------------------------------------------------------------
# Metric helpers (ported from citybehavex/reports.py)
# ---------------------------------------------------------------------------

def _waiting_times_minutes(traj) -> list:
    from skmob2 import waiting_times

    secs = waiting_times(
        traj.df,
        merge=True,
        datetime_col=traj.datetime_col,
        lat_col=traj.lat_col,
        lng_col=traj.lng_col,
        uid_col=traj.uid_col,
    )
    return [s / 60 for s in secs]


def _trajectory_od_matrix(df: pd.DataFrame, *, resolution: int) -> pd.DataFrame:
    import h3

    points = df[["uid", "datetime", "lat", "lng"]].dropna().copy()
    points = points.sort_values(["uid", "datetime"], kind="mergesort")
    points["origin"] = [
        h3.latlng_to_cell(lat, lng, resolution)
        for lat, lng in zip(points["lat"], points["lng"])
    ]
    points["destination"] = points.groupby("uid")["origin"].shift(-1)
    trips = points.dropna(subset=["destination"])
    trips = trips[trips["origin"] != trips["destination"]]
    if trips.empty:
        return pd.DataFrame(dtype=float)
    return (
        trips.groupby(["origin", "destination"]).size().unstack(fill_value=0).astype(float)
    )


def _common_part_of_commuters(df_a: pd.DataFrame, df_b: pd.DataFrame) -> List[Tuple[int, float]]:
    from skmob2 import od_matrix_common_part_of_commuters

    values: List[Tuple[int, float]] = []
    for resolution in CPC_H3_RESOLUTIONS:
        od_a = _trajectory_od_matrix(df_a, resolution=resolution)
        od_b = _trajectory_od_matrix(df_b, resolution=resolution)
        values.append((resolution, float(od_matrix_common_part_of_commuters(od_a, od_b))))
    return values


def _visits_for_comparison(df: pd.DataFrame, *, location_resolution: int = _H3_FALLBACK_RESOLUTION) -> pd.DataFrame:
    """Build the visit table skmob2 activity/motif metrics expect."""
    import h3

    if "purpose" not in df.columns:
        raise ValueError("activity comparison requires a purpose column")
    visits = pd.DataFrame(
        {
            "uid": df["uid"].to_numpy(),
            "start_timestamp": pd.to_datetime(df["datetime"]).to_numpy(),
            "purpose": df["purpose"].to_numpy(),
        }
    )
    visits["location_id"] = [
        h3.latlng_to_cell(lat, lng, location_resolution)
        for lat, lng in zip(df["lat"], df["lng"])
    ]
    if "end_timestamp" in df.columns and df["end_timestamp"].notna().any():
        visits["end_timestamp"] = pd.to_datetime(df["end_timestamp"]).to_numpy()
    else:
        visits = visits.sort_values(["uid", "start_timestamp"]).reset_index(drop=True)
        visits["end_timestamp"] = visits.groupby("uid")["start_timestamp"].shift(-1)
        visits["end_timestamp"] = visits["end_timestamp"].fillna(
            visits["start_timestamp"].dt.normalize() + pd.Timedelta(days=1)
        )
    return visits.reset_index(drop=True)


def _motif_visits(visits: pd.DataFrame) -> pd.DataFrame:
    motif_visits = visits.copy()
    motif_visits["purpose"] = motif_visits["purpose"].where(
        motif_visits["purpose"].eq("HOME"), "VISIT"
    )
    return motif_visits


def _compute_stvd_layers(df_a: pd.DataFrame, df_b: pd.DataFrame, resolutions: List[int]) -> Dict[int, dict]:
    import h3

    a = df_a[["uid", "lat", "lng", "datetime"]].dropna().copy()
    b = df_b[["uid", "lat", "lng", "datetime"]].dropna().copy()
    a["_hour"] = pd.to_datetime(a["datetime"]).dt.hour
    b["_hour"] = pd.to_datetime(b["datetime"]).dt.hour

    layers: Dict[int, dict] = {}
    all_hours = list(range(24))
    for res in resolutions:
        a["_cell"] = [h3.latlng_to_cell(lat, lng, res) for lat, lng in zip(a["lat"], a["lng"])]
        b["_cell"] = [h3.latlng_to_cell(lat, lng, res) for lat, lng in zip(b["lat"], b["lng"])]
        a_hourly = a.groupby(["_cell", "_hour"]).size().unstack(fill_value=0).reindex(columns=all_hours, fill_value=0)
        b_hourly = b.groupby(["_cell", "_hour"]).size().unstack(fill_value=0).reindex(columns=all_hours, fill_value=0)

        features = []
        for cell in set(a_hourly.index) | set(b_hourly.index):
            a_row = a_hourly.loc[cell] if cell in a_hourly.index else pd.Series(0, index=all_hours)
            b_row = b_hourly.loc[cell] if cell in b_hourly.index else pd.Series(0, index=all_hours)
            a_vol = float(a_row.sum())
            b_vol = float(b_row.sum())
            a_peak = int(a_row.idxmax()) if a_vol > 0 else 0
            b_peak = int(b_row.idxmax()) if b_vol > 0 else 0
            volume_diff_pct = (a_vol - b_vol) / max(b_vol, 1.0) * 100.0
            raw_shift = abs(a_peak - b_peak)
            peak_shift_hours = min(float(min(raw_shift, 24 - raw_shift)), 12.0)
            boundary = h3.cell_to_boundary(cell)
            ring = [[lng, lat] for lat, lng in boundary]
            ring.append(ring[0])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                    "properties": {
                        "area": cell,
                        "volume_diff_pct": round(volume_diff_pct, 4),
                        "peak_shift_hours": round(peak_shift_hours, 4),
                    },
                }
            )
        layers[res] = {"type": "FeatureCollection", "features": features}
    return layers


def _motif_distribution_jsd(left: pd.DataFrame, right: pd.DataFrame) -> float:
    from skmob2 import jensen_shannon_divergence

    left_counts = dict(zip(left["motif_id"], left["count"]))
    right_counts = dict(zip(right["motif_id"], right["count"]))
    labels = sorted(set(left_counts) | set(right_counts), key=str)
    return float(
        jensen_shannon_divergence(
            [left_counts.get(label, 0) for label in labels],
            [right_counts.get(label, 0) for label in labels],
        )
    )


def _mobility_law_visits(df: pd.DataFrame) -> pd.DataFrame:
    import h3

    visits = pd.DataFrame(
        {
            "user_id": df["uid"].to_numpy(),
            "timestamp": pd.to_datetime(df["datetime"]).to_numpy(),
            "lat": df["lat"].to_numpy(),
            "lng": df["lng"].to_numpy(),
        }
    )
    visits["location_id"] = [
        h3.latlng_to_cell(lat, lng, _H3_FALLBACK_RESOLUTION)
        for lat, lng in zip(visits["lat"], visits["lng"])
    ]
    if "purpose" in df.columns:
        visits["purpose"] = df["purpose"].to_numpy()
    return visits.reset_index(drop=True)


def _daily_location_lognormal_dataset(visits: pd.DataFrame, label: str):
    daily = (
        visits.assign(date=pd.to_datetime(visits["timestamp"]).dt.normalize())
        .groupby(["user_id", "date"])["location_id"]
        .nunique()
    )
    values = daily.to_numpy(dtype=float)
    values = values[np.isfinite(values) & (values > 0)]
    if values.size < 2:
        raise ValueError("at least two daily location counts are required")
    log_values = np.log(values)
    mu = float(log_values.mean())
    sigma = float(log_values.std())
    if not np.isfinite(sigma) or sigma <= 1e-12:
        raise ValueError("daily location counts must have positive log variance")
    x_points, counts = np.unique(values, return_counts=True)
    y_points = counts / counts.sum()
    return x_points, y_points, mu, sigma, label


def _truncated_powerlaw_dataset(values, label: str):
    from skmob2 import fit_values_to_truncated_powerlaw

    filtered = np.asarray(list(values), dtype=float)
    filtered = filtered[np.isfinite(filtered) & (filtered > 0)]
    if filtered.size < 2 or np.unique(filtered).size < 2:
        raise ValueError("at least two distinct positive values are required")
    parameters, x_points, y_points = fit_values_to_truncated_powerlaw(filtered.tolist())
    return parameters, x_points, y_points, label


def _distance_frequency_dataset(visits: pd.DataFrame, label: str):
    from skmob2 import bin_visitation_law_data, compute_visitation_law_data, fit_visitation_law

    purpose_col = "purpose" if "purpose" in visits.columns else None
    law_data = compute_visitation_law_data(
        visits,
        user_id_col="user_id",
        location_id_col="location_id",
        timestamp_col="timestamp",
        purpose_col=purpose_col,
        lat_col="lat",
        lng_col="lng",
    )
    rf_points, rho_points, _ = bin_visitation_law_data(
        law_data, user_id_col="user_id", location_id_col="location_id"
    )
    eta, mu, _ = fit_visitation_law(rf_points, rho_points)
    if eta <= 0 or mu <= 0:
        raise ValueError("distance-frequency fit parameters must be positive")
    return rf_points, rho_points, eta, mu, label


# ---------------------------------------------------------------------------
# Mobility profile helpers
# ---------------------------------------------------------------------------

def _normalise_profile_label(value: Any) -> str:
    label = str(value)
    return _PROFILE_LABEL_MAP.get(label.strip().lower(), label)


def _profile_visits(df: pd.DataFrame, *, location_resolution: int = _H3_FALLBACK_RESOLUTION) -> pd.DataFrame:
    """Build a visit table suitable for skmob2 profile measures."""
    import h3

    visits = pd.DataFrame(
        {
            "uid": df["uid"].to_numpy(),
            "start_timestamp": pd.to_datetime(df["datetime"]).to_numpy(),
        }
    )
    visits["location_id"] = [
        h3.latlng_to_cell(lat, lng, location_resolution)
        for lat, lng in zip(df["lat"], df["lng"])
    ]
    if "end_timestamp" in df.columns and df["end_timestamp"].notna().any():
        visits["end_timestamp"] = pd.to_datetime(df["end_timestamp"], errors="coerce").to_numpy()
    else:
        visits = visits.sort_values(["uid", "start_timestamp"]).reset_index(drop=True)
        visits["end_timestamp"] = visits.groupby("uid")["start_timestamp"].shift(-1)

    visits["end_timestamp"] = pd.to_datetime(visits["end_timestamp"], errors="coerce")
    fallback_end = visits["start_timestamp"].dt.normalize() + pd.Timedelta(days=1)
    visits["end_timestamp"] = visits["end_timestamp"].fillna(fallback_end)
    visits.loc[visits["end_timestamp"] < visits["start_timestamp"], "end_timestamp"] = visits["start_timestamp"]
    return visits.sort_values(["uid", "start_timestamp"]).reset_index(drop=True)


def _stationarity(visits: pd.DataFrame) -> pd.DataFrame:
    """Compute per-user weekly-slot dominant-location occupancy share."""
    rows: List[dict] = []
    for row in visits[["uid", "location_id", "start_timestamp", "end_timestamp"]].itertuples(index=False):
        start = pd.Timestamp(row.start_timestamp)
        end = pd.Timestamp(row.end_timestamp)
        if pd.isna(start):
            continue
        if pd.isna(end) or end < start:
            end = start
        slot_start = start.floor("5min")
        slot_end = end.floor("5min")
        timestamps = pd.date_range(slot_start, slot_end, freq="5min")
        if len(timestamps) == 0:
            timestamps = pd.DatetimeIndex([slot_start])
        for timestamp in timestamps:
            rows.append(
                {
                    "uid": row.uid,
                    "weekly_slot": int(timestamp.dayofweek * 24 * 12 + timestamp.hour * 12 + timestamp.minute // 5),
                    "location_id": row.location_id,
                }
            )

    if not rows:
        return pd.DataFrame({"uid": visits["uid"].drop_duplicates().to_numpy(), "stationarity": 0.0})

    occupancy = pd.DataFrame(rows)
    counts = occupancy.groupby(["uid", "weekly_slot", "location_id"]).size().rename("count").reset_index()
    slot_totals = counts.groupby(["uid", "weekly_slot"])["count"].sum().rename("total").reset_index()
    dominant = counts.groupby(["uid", "weekly_slot"])["count"].max().rename("dominant").reset_index()
    shares = slot_totals.merge(dominant, on=["uid", "weekly_slot"])
    shares["slot_share"] = shares["dominant"] / shares["total"]
    result = shares.groupby("uid")["slot_share"].mean().rename("stationarity").reset_index()
    users = pd.DataFrame({"uid": visits["uid"].drop_duplicates().to_numpy()})
    return users.merge(result, on="uid", how="left").fillna({"stationarity": 0.0})


def _merge_user_metric(base: pd.DataFrame, metric_df: Any, metric_col: str) -> pd.DataFrame:
    metric_pd = pd.DataFrame(metric_df)
    if "uid" not in metric_pd.columns or metric_col not in metric_pd.columns:
        raise ValueError(f"{metric_col} measure did not return uid/{metric_col} columns")
    return base.merge(metric_pd[["uid", metric_col]], on="uid", how="left")


def _build_profile_data(df: pd.DataFrame) -> pd.DataFrame:
    import skmob2

    visits = _profile_visits(df)
    profile_df = pd.DataFrame(
        skmob2.exploration_profiling(
            visits,
            user_id_col="uid",
            location_id_col="location_id",
            datetime_col="start_timestamp",
        )
    )
    if "profile" not in profile_df.columns:
        raise ValueError("exploration_profiling did not return a profile column")
    profile_df["agent_type"] = profile_df["profile"].map(_normalise_profile_label)

    profile_df = _merge_user_metric(
        profile_df,
        skmob2.regularity(visits, user_id_col="uid", location_id_col="location_id", location_type_col=None),
        "regularity",
    )
    profile_df = _merge_user_metric(
        profile_df,
        skmob2.diversity(visits, user_id_col="uid", location_id_col="location_id", location_type_col=None),
        "diversity",
    )
    profile_df = _merge_user_metric(
        profile_df,
        skmob2.trajectory_entropy(
            visits,
            user_id_col="uid",
            location_id_col="location_id",
            location_type_col=None,
            timestamp_col="start_timestamp",
        ),
        "entropy",
    )
    profile_df = profile_df.merge(_stationarity(visits), on="uid", how="left")
    for metric in _PROFILE_METRICS:
        profile_df[metric] = pd.to_numeric(profile_df[metric], errors="coerce")
    profile_df["stationarity"] = profile_df["stationarity"].clip(lower=0.0, upper=1.0)
    return profile_df


class _LocalEChartsFigure:
    def __init__(self, option: dict):
        self._option = option

    def to_dict(self) -> dict:
        return self._option


def _load_profile_plotters():
    for module_name in ("skmob_vis", "skmob_vis.profiles"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        plot_mobility_profiles = getattr(module, "plot_mobility_profiles", None)
        plot_profile_metrics = getattr(module, "plot_profile_metrics", None)
        if callable(plot_mobility_profiles) and callable(plot_profile_metrics):
            return plot_mobility_profiles, plot_profile_metrics

    return _local_plot_mobility_profiles, _local_plot_profile_metrics


def _as_profile_datasets(profiles: Any) -> Dict[str, pd.DataFrame]:
    if isinstance(profiles, dict) and "degree_of_return" not in profiles:
        return {str(name): pd.DataFrame(data) for name, data in profiles.items()}
    return {"": pd.DataFrame(profiles)}


def _ordered_profile_labels(labels: Iterable[Any]) -> List[str]:
    seen = list(dict.fromkeys(str(label) for label in labels))
    ordered = [label for label in _PROFILE_LABELS if label in seen]
    ordered.extend(label for label in seen if label not in ordered)
    return ordered


def _base_profile_option(title: str, chart_type: str) -> dict:
    return {
        "_meta": {"chartType": chart_type},
        "backgroundColor": "#ffffff",
        "title": {
            "text": title,
            "left": 0,
            "top": 0,
            "textStyle": {
                "fontFamily": "serif",
                "fontWeight": 500,
                "fontSize": 28,
                "color": "#172033",
            },
        },
        "tooltip": {"trigger": "item"},
    }


def _local_plot_mobility_profiles(
    profiles: Any,
    *,
    profile_col: str = "agent_type",
    title: str = "Mobility profiles",
    **kwargs,
) -> _LocalEChartsFigure:
    datasets = _as_profile_datasets(profiles)
    multi = len(datasets) > 1 or next(iter(datasets)) != ""
    all_labels: List[str] = []
    for data in datasets.values():
        all_labels.extend(data[profile_col].astype(str).tolist())
    profile_order = _ordered_profile_labels(all_labels)

    series = []
    legend = []
    for dataset_index, (dataset_name, data) in enumerate(datasets.items()):
        symbol = _DATASET_SYMBOLS[dataset_index % len(_DATASET_SYMBOLS)]
        for profile in profile_order:
            subset = data[data[profile_col].astype(str) == profile]
            if subset.empty:
                continue
            series_name = f"{profile} · {dataset_name}" if multi else profile
            legend.append(series_name)
            series.append(
                {
                    "name": series_name,
                    "type": "scatter",
                    "symbol": symbol,
                    "symbolSize": 11,
                    "data": subset[["degree_of_return", "intermittency"]].astype(float).values.tolist(),
                    "itemStyle": {
                        "color": _PROFILE_COLORS.get(profile, "#6b7280"),
                        "opacity": 0.82,
                        "borderColor": "#ffffff",
                        "borderWidth": 0.6,
                    },
                    "emphasis": {"scale": 1.3},
                }
            )

    option = _base_profile_option(title, "mobility_profiles")
    option.update(
        {
            "grid": {"left": 78, "right": 28, "top": 96, "bottom": 70, "containLabel": False},
            "legend": {"data": legend, "top": 54, "left": 0, "right": 0},
            "xAxis": {
                "type": "value",
                "name": "DEGREE OF RETURN",
                "nameLocation": "middle",
                "nameGap": 42,
            },
            "yAxis": {
                "type": "value",
                "name": "INTERMITTENCY",
                "nameLocation": "middle",
                "nameGap": 64,
                "nameRotate": 90,
            },
            "series": series,
        }
    )
    return _LocalEChartsFigure(option)


def _box_stats(values: Iterable[Any]) -> Optional[List[float]]:
    array = _finite_values(values)
    if array.size == 0:
        return None
    return [
        float(np.min(array)),
        float(np.percentile(array, 25)),
        float(np.percentile(array, 50)),
        float(np.percentile(array, 75)),
        float(np.max(array)),
    ]


def _local_plot_profile_metrics(
    datasets: Dict[str, Any],
    *,
    metrics: Iterable[str] = _PROFILE_BOXPLOT_METRICS,
    profile_col: str = "agent_type",
    profile_order: Iterable[str] = ("Scouter", "Regular", "Routiner"),
    title: str = "Mobility profile metrics",
    **kwargs,
) -> _LocalEChartsFigure:
    dataset_frames = {str(name): pd.DataFrame(data) for name, data in datasets.items()}
    metric_names = [str(metric) for metric in metrics]
    profile_names = [str(profile) for profile in profile_order]
    ncols = 2 if len(metric_names) > 1 else 1
    nrows = int(np.ceil(len(metric_names) / ncols))
    cell_width = 40
    cell_height = 30 if nrows > 1 else 64
    grids = []
    titles = [
        {
            "text": title,
            "left": 0,
            "top": 0,
            "textStyle": {
                "fontFamily": "serif",
                "fontWeight": 500,
                "fontSize": 28,
                "color": "#172033",
            },
        }
    ]
    x_axes = []
    y_axes = []
    series = []
    dataset_colors = ["#1565c0", "#c62828", "#2e7d32", "#6b7280"]
    for index, metric in enumerate(metric_names):
        row, col = divmod(index, ncols)
        left = 7 + col * 50
        top = 16 + row * 43
        grids.append({"left": f"{left}%", "top": f"{top}%", "width": f"{cell_width}%", "height": f"{cell_height}%"})
        titles.append(
            {
                "text": metric.replace("_", " ").title(),
                "left": f"{left + cell_width / 2}%",
                "top": f"{max(top - 6, 0)}%",
                "textAlign": "center",
            }
        )
        x_axes.append({"gridIndex": index, "type": "category", "data": profile_names})
        y_axes.append({"gridIndex": index, "type": "value", "min": 0})
        for dataset_index, (dataset_name, data) in enumerate(dataset_frames.items()):
            boxes = []
            for profile in profile_names:
                subset = data[data[profile_col].astype(str) == profile]
                boxes.append(_box_stats(subset[metric]) if metric in subset.columns else None)
            series.append(
                {
                    "name": dataset_name,
                    "type": "boxplot",
                    "xAxisIndex": index,
                    "yAxisIndex": index,
                    "data": boxes,
                    "itemStyle": {
                        "color": "#ffffff",
                        "borderColor": dataset_colors[dataset_index % len(dataset_colors)],
                        "borderWidth": 1.6,
                    },
                    "boxWidth": [10, 40],
                }
            )

    option = _base_profile_option(title, "profile_metrics")
    option["title"] = titles
    option.update(
        {
            "grid": grids,
            "legend": {"data": list(dataset_frames), "top": 8, "right": 0},
            "xAxis": x_axes,
            "yAxis": y_axes,
            "series": series,
        }
    )
    return _LocalEChartsFigure(option)


def _add_single_profile_section(
    df: pd.DataFrame,
    label: str,
    charts: Dict[str, Any],
    warnings: List[str],
) -> None:
    try:
        plot_mobility_profiles, plot_profile_metrics = _load_profile_plotters()

        profiles = _build_profile_data(df)
        charts["mobility_profiles"] = _chart(
            plot_mobility_profiles(profiles, title="Degree of return vs intermittency"),
            "mobility_profiles",
        )
        charts["profile_metrics"] = _chart(
            plot_profile_metrics(
                {label: profiles},
                metrics=_PROFILE_BOXPLOT_METRICS,
                title="Mobility profile metrics",
            ),
            "profile_metrics",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"profile: {exc}")


def _finite_values(values: Iterable[Any]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float).ravel()
    return array[np.isfinite(array)]


def _profile_jsd(values_a: Iterable[Any], values_b: Iterable[Any]) -> float:
    from skmob2 import histogram_jensen_shannon_divergence

    a = _finite_values(values_a)
    b = _finite_values(values_b)
    if a.size == 0 or b.size == 0:
        return float("nan")
    value_range = float(max(a.max(), b.max()) - min(a.min(), b.min()))
    bin_size = value_range / 20.0 if value_range > 0 else 0.05
    return float(histogram_jensen_shannon_divergence(a, b, bin_size=max(bin_size, 1e-6)))


def _profile_mix_jsd(profiles_a: pd.DataFrame, profiles_b: pd.DataFrame) -> float:
    from skmob2 import jensen_shannon_divergence

    counts_a = profiles_a["agent_type"].value_counts()
    counts_b = profiles_b["agent_type"].value_counts()
    labels = list(_PROFILE_LABELS)
    return float(
        jensen_shannon_divergence(
            [counts_a.get(label, 0) for label in labels],
            [counts_b.get(label, 0) for label in labels],
        )
    )


def _add_profile_comparison_section(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str,
    label_b: str,
    charts: Dict[str, Any],
    warnings: List[str],
    wasserstein: List[dict],
    jensen_shannon: List[dict],
) -> None:
    try:
        from skmob2 import profile_metric_wasserstein_distance

        plot_mobility_profiles, plot_profile_metrics = _load_profile_plotters()

        profiles_a = _build_profile_data(df_a)
        profiles_b = _build_profile_data(df_b)

        for metric_col in _PROFILE_METRICS:
            name = metric_col.replace("_", " ").title()
            try:
                value = profile_metric_wasserstein_distance(profiles_a, profiles_b, metric_col)
                wasserstein.append({"name": f"Profile {name}", "value": round(float(value), 4), "unit": ""})
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"metric profile {metric_col} W1: {exc}")
            try:
                value = _profile_jsd(profiles_a[metric_col], profiles_b[metric_col])
                jensen_shannon.append({"name": f"Profile {name}", "value": round(float(value), 4)})
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"metric profile {metric_col} JSD: {exc}")

        try:
            jensen_shannon.append(
                {"name": "Mobility profile mix", "value": round(_profile_mix_jsd(profiles_a, profiles_b), 4)}
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"metric mobility profile mix: {exc}")

        profile_sets = {label_a: profiles_a, label_b: profiles_b}
        charts["mobility_profiles"] = _chart(
            plot_mobility_profiles(profile_sets, title="Degree of return vs intermittency"),
            "mobility_profiles",
        )
        charts["profile_metrics"] = _chart(
            plot_profile_metrics(
                profile_sets,
                metrics=_PROFILE_BOXPLOT_METRICS,
                title="Mobility profile metrics",
            ),
            "profile_metrics",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"profile: {exc}")


# ---------------------------------------------------------------------------
# Payload assembly
# ---------------------------------------------------------------------------

def build_single_payload(
    df: pd.DataFrame,
    label: str = "A",
) -> Dict[str, Any]:
    """Compute mobility charts for a single trajectory source (no comparison metrics)."""
    df = _normalise(df)
    traj = _traj(df)

    charts: Dict[str, Any] = {}
    warnings: List[str] = []

    def add_chart(key: str, chart_type: str, factory):
        try:
            result = factory()
            if result is None:
                return
            if isinstance(result, tuple):
                fig, extra = result
            else:
                fig, extra = result, {}
            if fig is not None:
                charts[key] = _chart(fig, chart_type, **extra)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"chart {key}: {exc}")

    from skmob_vis import (
        plot_distance_frequency_law,
        plot_lognormal_fits,
        plot_truncated_powerlaw_fits,
    )

    jumps = list(traj.jump_lengths(merge=True))
    rog = traj.radius_of_gyration()["radius_of_gyration"].to_numpy()
    law_visits = _mobility_law_visits(df)

    _POWERLAW_FORMULA = "p(x) = c (x + r0)^-beta exp(-x / kappa)"

    def powerlaw_single(values, **kwargs):
        dataset = _truncated_powerlaw_dataset(values, label)
        fig = plot_truncated_powerlaw_fits(dataset, **kwargs)
        params = [{"label": dataset[3], "values": dict(zip(("c", "r0", "beta", "kappa"), [round(float(x), 4) for x in dataset[0]]))}]
        return fig, {"formula": _POWERLAW_FORMULA, "parameters": params}

    add_chart("powerlaw_jump", "mobility_law", lambda: powerlaw_single(jumps, title="Travel-distance mobility law"))
    add_chart("powerlaw_rog", "mobility_law", lambda: powerlaw_single(rog, title="Radius-of-gyration mobility law", x_label="radius of gyration · km", y_label="P(r_g)"))

    def lognormal_single():
        dataset = _daily_location_lognormal_dataset(law_visits, label)
        fig = plot_lognormal_fits(dataset)
        params = [{"label": dataset[4], "values": {"mu": round(dataset[2], 4), "sigma": round(dataset[3], 4)}}]
        return fig, {
            "formula": "f(N) = exp(-(ln N - mu)^2 / (2 sigma^2)) / (N sigma sqrt(2 pi))",
            "parameters": params,
        }

    add_chart("lognormal", "mobility_law", lognormal_single)

    def dist_freq_single():
        dataset = _distance_frequency_dataset(law_visits, label)
        fig = plot_distance_frequency_law(dataset)
        params = [{"label": dataset[4], "values": {"eta": round(dataset[2], 4), "mu": round(dataset[3], 4)}}]
        return fig, {"formula": "rho(r, f) = mu (r f)^-eta", "parameters": params}

    add_chart("distance_frequency", "mobility_law", dist_freq_single)

    if "purpose" in df.columns:
        try:
            from skmob_vis import plot_visit_purpose_comparison

            visits_cmp = _visits_for_comparison(df)
            add_chart("purpose", "visit_purpose_comparison",
                      lambda: plot_visit_purpose_comparison({label: visits_cmp}))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"activity: {exc}")

    _add_single_profile_section(df, label, charts, warnings)

    return {
        "labels": [label],
        "metrics": {"wasserstein": [], "jensen_shannon": [], "cpc": []},
        "charts": charts,
        "warnings": warnings,
    }

def _chart(figure, chart_type: str, **extra) -> dict:
    payload = {"chartType": chart_type, "option": figure.to_dict()}
    payload.update(extra)
    return payload


def build_comparison_payload(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    """Compute metrics + skmob-vis chart options comparing two trajectory sources."""
    df_a = _normalise(df_a)
    df_b = _normalise(df_b)
    traj_a = _traj(df_a)
    traj_b = _traj(df_b)
    labels = (label_a, label_b)

    charts: Dict[str, Any] = {}
    warnings: List[str] = []
    wasserstein: List[dict] = []
    jensen_shannon: List[dict] = []
    cpc: List[dict] = []

    def metric(name: str, unit: str, fn):
        try:
            wasserstein.append({"name": name, "value": round(float(fn()), 4), "unit": unit})
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"metric {name}: {exc}")

    def add_chart(key: str, chart_type: str, factory):
        """factory returns either a figure or a (figure, extra_dict) tuple."""
        try:
            result = factory()
            if result is None:
                return
            if isinstance(result, tuple):
                fig, extra = result
            else:
                fig, extra = result, {}
            if fig is not None:
                charts[key] = _chart(fig, chart_type, **extra)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"chart {key}: {exc}")

    # --- distribution metrics + ECDF charts ---
    from skmob2 import visits_per_user_wasserstein_distance, wasserstein_distance
    from skmob_vis import (
        plot_dwell_time_ecdf,
        plot_jump_lengths_ecdf,
        plot_radius_of_gyration_ecdf,
        plot_visits_frequency_ecdf,
    )

    jumps_a = list(traj_a.jump_lengths(merge=True))
    jumps_b = list(traj_b.jump_lengths(merge=True))
    visits_a = traj_a.df[traj_a.uid_col].value_counts().to_list()
    visits_b = traj_b.df[traj_b.uid_col].value_counts().to_list()
    rog_a = traj_a.radius_of_gyration()["radius_of_gyration"].to_numpy()
    rog_b = traj_b.radius_of_gyration()["radius_of_gyration"].to_numpy()

    if "duration_minutes" in df_a.columns and df_a["duration_minutes"].notna().any():
        dwell_a = [d for d in df_a["duration_minutes"].dropna().tolist() if d >= 0]
    else:
        dwell_a = _waiting_times_minutes(traj_a)
    if "duration_minutes" in df_b.columns and df_b["duration_minutes"].notna().any():
        dwell_b = [d for d in df_b["duration_minutes"].dropna().tolist() if d >= 0]
    else:
        dwell_b = _waiting_times_minutes(traj_b)

    metric("Jump lengths", "km", lambda: wasserstein_distance(jumps_a, jumps_b))
    metric(
        "Visits per user", "visits",
        lambda: visits_per_user_wasserstein_distance(
            traj_a.df, traj_b.df,
            user_id_col1=traj_a.uid_col, user_id_col2=traj_b.uid_col,
        )[0],
    )
    metric("Radius of gyration", "km", lambda: wasserstein_distance(rog_a, rog_b))
    metric("Dwell time", "min", lambda: wasserstein_distance(dwell_a, dwell_b))

    add_chart("jump_ecdf", "ecdf", lambda: plot_jump_lengths_ecdf(jumps_a, jumps_b, labels=labels))
    add_chart("visits_ecdf", "ecdf", lambda: plot_visits_frequency_ecdf(visits_a, visits_b, labels=labels))
    add_chart("rog_ecdf", "ecdf", lambda: plot_radius_of_gyration_ecdf(rog_a, rog_b, labels=labels))
    add_chart("dwell_ecdf", "ecdf", lambda: plot_dwell_time_ecdf(dwell_a, dwell_b, labels=labels))

    # --- Common Part of Commuters ---
    try:
        for resolution, value in _common_part_of_commuters(df_a, df_b):
            cpc.append({"resolution": resolution, "value": round(value, 4)})
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"cpc: {exc}")

    # --- mobility laws ---
    from skmob_vis import (
        plot_distance_frequency_law,
        plot_lognormal_fits,
        plot_truncated_powerlaw_fits,
    )

    law_visits_a = _mobility_law_visits(df_a)
    law_visits_b = _mobility_law_visits(df_b)

    _POWERLAW_FORMULA = "p(x) = c (x + r0)^-beta exp(-x / kappa)"

    def powerlaw(values_a, values_b, **kwargs):
        a = _truncated_powerlaw_dataset(values_a, label_a)
        b = _truncated_powerlaw_dataset(values_b, label_b)
        fig = plot_truncated_powerlaw_fits(a, b, **kwargs)
        params = [
            {"label": a[3], "values": dict(zip(("c", "r0", "beta", "kappa"), [round(float(x), 4) for x in a[0]]))},
            {"label": b[3], "values": dict(zip(("c", "r0", "beta", "kappa"), [round(float(x), 4) for x in b[0]]))},
        ]
        return fig, {"formula": _POWERLAW_FORMULA, "parameters": params}

    add_chart(
        "powerlaw_jump", "mobility_law",
        lambda: powerlaw(jumps_a, jumps_b, title="Travel-distance mobility law"),
    )
    add_chart(
        "powerlaw_rog", "mobility_law",
        lambda: powerlaw(rog_a, rog_b, title="Radius-of-gyration mobility law", x_label="radius of gyration · km", y_label="P(r_g)"),
    )

    def lognormal():
        a = _daily_location_lognormal_dataset(law_visits_a, label_a)
        b = _daily_location_lognormal_dataset(law_visits_b, label_b)
        fig = plot_lognormal_fits(a, b)
        params = [
            {"label": a[4], "values": {"mu": round(a[2], 4), "sigma": round(a[3], 4)}},
            {"label": b[4], "values": {"mu": round(b[2], 4), "sigma": round(b[3], 4)}},
        ]
        return fig, {
            "formula": "f(N) = exp(-(ln N - mu)^2 / (2 sigma^2)) / (N sigma sqrt(2 pi))",
            "parameters": params,
        }

    add_chart("lognormal", "mobility_law", lognormal)

    def distance_frequency():
        a = _distance_frequency_dataset(law_visits_a, label_a)
        b = _distance_frequency_dataset(law_visits_b, label_b)
        fig = plot_distance_frequency_law(a, b)
        params = [
            {"label": a[4], "values": {"eta": round(a[2], 4), "mu": round(a[3], 4)}},
            {"label": b[4], "values": {"eta": round(b[2], 4), "mu": round(b[3], 4)}},
        ]
        return fig, {"formula": "rho(r, f) = mu (r f)^-eta", "parameters": params}

    add_chart("distance_frequency", "mobility_law", distance_frequency)

    # --- mobility profiles ---
    _add_profile_comparison_section(
        df_a, df_b, label_a, label_b, charts, warnings, wasserstein, jensen_shannon
    )

    # --- activity comparison (requires purpose on both sides) ---
    if "purpose" in df_a.columns and "purpose" in df_b.columns:
        try:
            visits_cmp_a = _visits_for_comparison(df_a)
            visits_cmp_b = _visits_for_comparison(df_b)
            _activity_section(
                visits_cmp_a, visits_cmp_b, labels, charts, warnings, jensen_shannon
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"activity: {exc}")

    # --- STVD map ---
    try:
        from skmob_vis import plot_stvd_comparison

        layers = _compute_stvd_layers(df_a, df_b, STVD_RESOLUTIONS)
        fig = plot_stvd_comparison(layers, title=f"{label_a} vs {label_b}")
        option = fig.to_dict()
        meta = option.get("_meta", {})
        leaflet = option.get("leaflet", {})
        charts["stvd"] = {
            "chartType": "stvd_comparison",
            "option": option,
            "layers": meta.get("layers"),
            "colors": meta.get("colors"),
            "center": leaflet.get("center"),
            "zoom": leaflet.get("zoom"),
        }
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"chart stvd: {exc}")

    return {
        "labels": [label_a, label_b],
        "metrics": {
            "wasserstein": wasserstein,
            "jensen_shannon": jensen_shannon,
            "cpc": cpc,
        },
        "charts": charts,
        "warnings": warnings,
    }


def _activity_section(visits_a, visits_b, labels, charts, warnings, jensen_shannon):
    from skmob2 import (
        activity_distribution_jensen_shannon_divergence,
        activity_transition_matrix,
        activity_transition_matrix_jensen_shannon_divergence,
        daily_activity_distribution,
        discover_daily_motifs_from_agents,
        time_bin_matrix_jensen_shannon_divergence,
    )
    from skmob_vis import (
        plot_activity_transition_difference,
        plot_daily_activity_difference,
        plot_motif_literature_comparison,
        plot_visit_purpose_comparison,
    )

    label_a, label_b = labels

    def jsd(name, fn):
        try:
            jensen_shannon.append({"name": name, "value": round(float(fn()), 4)})
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"metric {name}: {exc}")

    jsd(
        "Activity distribution",
        lambda: activity_distribution_jensen_shannon_divergence(visits_a, visits_b),
    )
    jsd(
        "Activity transitions",
        lambda: activity_transition_matrix_jensen_shannon_divergence(
            activity_transition_matrix(visits_a), activity_transition_matrix(visits_b)
        ),
    )

    def daily_jsd():
        a_daily, a_cats, _ = daily_activity_distribution(visits_a)
        b_daily, b_cats, _ = daily_activity_distribution(visits_b)
        return time_bin_matrix_jensen_shannon_divergence(a_daily, b_daily, a_cats, b_cats)

    jsd("Daily activity profile", daily_jsd)

    try:
        charts["purpose"] = _chart(
            plot_visit_purpose_comparison({label_a: visits_a, label_b: visits_b}),
            "visit_purpose_comparison",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"chart purpose: {exc}")
    try:
        charts["transition"] = _chart(
            plot_activity_transition_difference(visits_a, visits_b, labels=labels),
            "difference_heatmap",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"chart transition: {exc}")
    try:
        charts["daily_activity"] = _chart(
            plot_daily_activity_difference(visits_a, visits_b, labels=labels),
            "difference_heatmap",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"chart daily_activity: {exc}")

    # motifs
    try:
        _, dist_a = discover_daily_motifs_from_agents(
            _motif_visits(visits_a),
            user_id_col="uid", location_id_col="location_id",
            purpose_col="purpose", timestamp_col="start_timestamp",
            end_timestamp_col="end_timestamp",
        )
        _, dist_b = discover_daily_motifs_from_agents(
            _motif_visits(visits_b),
            user_id_col="uid", location_id_col="location_id",
            purpose_col="purpose", timestamp_col="start_timestamp",
            end_timestamp_col="end_timestamp",
        )
        jsd("Daily motifs", lambda: _motif_distribution_jsd(dist_a, dist_b))
        charts["motif"] = _chart(
            plot_motif_literature_comparison(
                reference_distribution=dist_a,
                comparison_distribution=dist_b,
                labels=labels,
            ),
            "motif",
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"chart motif: {exc}")
