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

    fastmob = types.ModuleType("fastmob")

    def compute_profiles(*args, **kwargs):
        if fail_profile:
            raise ValueError("compute_profiles requires at least 3 users")
        return pd.DataFrame(
            {
                "uid": ["u1", "u2", "u3"],
                "intermittency": [1.0, 2.0, 3.0],
                "degree_of_return": [0.1, 0.5, 0.9],
                "regularity": [0.1, 0.2, 0.3],
                "diversity": [0.4, 0.5, 0.6],
                "entropy": [0.7, 0.8, 0.9],
                "stationarity": [0.2, 0.4, 0.6],
                "profile": ["scouters", "regulars", "routiners"],
            }
        )

    fastmob.compute_profiles = compute_profiles
    fastmob.wasserstein_distance = lambda left, right: abs(
        float(pd.Series(list(left)).mean()) - float(pd.Series(list(right)).mean())
    )
    fastmob.jensen_shannon_divergence = lambda left, right: 0.456

    fastmob_vis = types.ModuleType("fastmob_vis")
    fastmob_vis_profiles = types.ModuleType("fastmob_vis.profiles")

    class FakeFigure:
        def __init__(self, chart_type):
            self.chart_type = chart_type

        def to_dict(self):
            return {"_meta": {"chartType": self.chart_type}, "series": []}

    fastmob_vis_profiles.plot_mobility_profiles = lambda *args, **kwargs: FakeFigure("mobility_profiles")
    fastmob_vis_profiles.plot_profile_metrics = lambda *args, **kwargs: FakeFigure("profile_metrics")

    monkeypatch.setitem(sys.modules, "fastmob", fastmob)
    monkeypatch.setitem(sys.modules, "fastmob_vis", fastmob_vis)
    monkeypatch.setitem(sys.modules, "fastmob_vis.profiles", fastmob_vis_profiles)
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


def test_profile_plotter_loader_falls_back_when_fastmob_vis_exports_are_missing(monkeypatch):
    from en_agentsociety.webapi.mobility import report

    fastmob_vis = types.ModuleType("fastmob_vis")
    monkeypatch.setitem(sys.modules, "fastmob_vis", fastmob_vis)
    monkeypatch.delitem(sys.modules, "fastmob_vis.profiles", raising=False)

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
