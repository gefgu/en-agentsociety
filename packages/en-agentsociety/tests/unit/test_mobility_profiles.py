import sys
import types

import pandas as pd


def test_profile_label_normalization():
    from en_agentsociety.webapi.mobility import report

    assert report._normalise_profile_label("routiners") == "Routiner"
    assert report._normalise_profile_label("regulars") == "Regular"
    assert report._normalise_profile_label("scouters") == "Scouter"
    assert report._normalise_profile_label("Custom") == "Custom"


def _install_fake_profile_modules(monkeypatch, *, fail_profile=False):
    from en_agentsociety.webapi.mobility import report

    visits = pd.DataFrame(
        {
            "uid": ["u1", "u1", "u2", "u2", "u3", "u3"],
            "start_timestamp": pd.date_range("2024-01-01", periods=6, freq="h"),
            "end_timestamp": pd.date_range("2024-01-01 00:30", periods=6, freq="h"),
            "location_id": ["a", "b", "a", "a", "c", "d"],
        }
    )
    monkeypatch.setattr(report, "_profile_visits", lambda df: visits.copy())

    skmob2 = types.ModuleType("skmob2")

    def exploration_profiling(*args, **kwargs):
        if fail_profile:
            raise ValueError("exploration_profiling requires at least 3 users")
        return pd.DataFrame(
            {
                "uid": ["u1", "u2", "u3"],
                "intermittency": [1.0, 2.0, 3.0],
                "degree_of_return": [0.1, 0.5, 0.9],
                "mean_return": [0.5, 1.0, 1.5],
                "mean_exploration": [0.5, 1.0, 1.5],
                "profile": ["scouters", "regulars", "routiners"],
            }
        )

    skmob2.exploration_profiling = exploration_profiling
    skmob2.regularity = lambda *args, **kwargs: pd.DataFrame({"uid": ["u1", "u2", "u3"], "regularity": [0.1, 0.2, 0.3]})
    skmob2.diversity = lambda *args, **kwargs: pd.DataFrame({"uid": ["u1", "u2", "u3"], "diversity": [0.4, 0.5, 0.6]})
    skmob2.trajectory_entropy = lambda *args, **kwargs: pd.DataFrame({"uid": ["u1", "u2", "u3"], "entropy": [0.7, 0.8, 0.9]})
    skmob2.profile_metric_wasserstein_distance = lambda left, right, metric_col: abs(
        float(left[metric_col].mean()) - float(right[metric_col].mean())
    )
    skmob2.histogram_jensen_shannon_divergence = lambda left, right, bin_size=1.0: 0.123
    skmob2.jensen_shannon_divergence = lambda left, right: 0.456

    skmob_vis = types.ModuleType("skmob_vis")

    class FakeFigure:
        def __init__(self, chart_type):
            self.chart_type = chart_type

        def to_dict(self):
            return {"_meta": {"chartType": self.chart_type}, "series": []}

    skmob_vis.plot_mobility_profiles = lambda *args, **kwargs: FakeFigure("mobility_profiles")
    skmob_vis.plot_profile_metrics = lambda *args, **kwargs: FakeFigure("profile_metrics")

    monkeypatch.setitem(sys.modules, "skmob2", skmob2)
    monkeypatch.setitem(sys.modules, "skmob_vis", skmob_vis)
    return report


def test_profile_data_and_comparison_metrics(monkeypatch):
    report = _install_fake_profile_modules(monkeypatch)

    profiles = report._build_profile_data(pd.DataFrame({"uid": ["u1"]}))
    assert set(["agent_type", "regularity", "diversity", "stationarity", "entropy"]).issubset(profiles.columns)
    assert profiles["agent_type"].tolist() == ["Scouter", "Regular", "Routiner"]

    charts = {}
    warnings = []
    wasserstein = []
    jensen_shannon = []
    report._add_profile_comparison_section(
        pd.DataFrame({"uid": ["a"]}),
        pd.DataFrame({"uid": ["b"]}),
        "left",
        "right",
        charts,
        warnings,
        wasserstein,
        jensen_shannon,
    )

    assert warnings == []
    assert {"mobility_profiles", "profile_metrics"}.issubset(charts)
    assert {row["name"] for row in wasserstein} == {
        "Profile Degree Of Return",
        "Profile Intermittency",
        "Profile Regularity",
        "Profile Diversity",
        "Profile Stationarity",
        "Profile Entropy",
    }
    assert "Mobility profile mix" in {row["name"] for row in jensen_shannon}


def test_profile_plotter_loader_falls_back_when_skmob_vis_exports_are_missing(monkeypatch):
    from en_agentsociety.webapi.mobility import report

    skmob_vis = types.ModuleType("skmob_vis")
    monkeypatch.setitem(sys.modules, "skmob_vis", skmob_vis)
    monkeypatch.delitem(sys.modules, "skmob_vis.profiles", raising=False)

    plot_mobility_profiles, plot_profile_metrics = report._load_profile_plotters()

    assert plot_mobility_profiles is report._local_plot_mobility_profiles
    assert plot_profile_metrics is report._local_plot_profile_metrics


def test_profile_section_warns_without_failing(monkeypatch):
    report = _install_fake_profile_modules(monkeypatch, fail_profile=True)

    charts = {}
    warnings = []
    wasserstein = []
    jensen_shannon = []
    report._add_profile_comparison_section(
        pd.DataFrame({"uid": ["a"]}),
        pd.DataFrame({"uid": ["b"]}),
        "left",
        "right",
        charts,
        warnings,
        wasserstein,
        jensen_shannon,
    )

    assert charts == {}
    assert wasserstein == []
    assert jensen_shannon == []
    assert warnings and warnings[0].startswith("profile:")
