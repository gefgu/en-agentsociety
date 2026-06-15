"""Mobility-metrics comparison report (skmob-vis powered).

Computes the same metric/figure set as the sibling ``citybehavex`` report but
returns ECharts option JSON (via skmob-vis ``EChartsFigure.to_dict()``) so the
React frontend can render the charts natively.
"""

from .report import (
    build_comparison_payload,
    trajdf_from_visits_df,
    trajdf_from_upload,
)

__all__ = [
    "build_comparison_payload",
    "trajdf_from_visits_df",
    "trajdf_from_upload",
]
