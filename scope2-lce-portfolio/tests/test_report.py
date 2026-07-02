"""Tests for the PP-09 reporting deliverable (ADR 0014).

Covers the §3 payload contract (schema round-trip, version refusal, hourly
size discipline), the §2 renderer views (section anchors, §2.5/§2.6 gating),
the §6 seams (``write_outputs`` report emission + ``--no-report``), and the
``scripts/render_report.py`` byte-stable regeneration of the committed demo
run folder. Kept fast: one module-scoped 24-hour solve is reused everywhere;
the only 8760 solves are the two single-delta CLI runs.
"""

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from conftest import daytime_solar_cf, solar_plus_battery
from lce_portfolio.cli import compose_run_id
from lce_portfolio.cli import main as cli_main
from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.outputs import write_outputs, write_report
from lce_portfolio.report import (
    PAYLOAD_VERSION,
    SECTION_ANCHORS,
    build_report_payload,
    render_report,
    select_hourly_setpoint,
)
from lce_portfolio.sweep import SweepResult, run_sweep

_ROOT = Path(__file__).resolve().parents[1]  # scope2-lce-portfolio/


@pytest.fixture(scope="module")
def small_run():
    """One small 24-hour two-setpoint solve shared by the whole module."""
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, 24)
    load = np.full(24, 100.0)
    lmp = np.full(24, 40.0)
    lmp[16:20] = 90.0
    cfg = PortfolioConfig(
        hours=24,
        mode="premium_cap",
        premium_deltas=(5.0, 20.0),
        excess_sale_fraction=0.5,
    )
    return cfg, run_sweep(cfg, res, load, lmp, cf)


def _two_iso_payload(small_run):
    """Payload for a fake two-ISO batch (§2.6) reusing the one solve."""
    cfg, sweep = small_run
    sweep_b = SweepResult(iso="SAMPLE_B", mode=sweep.mode, results=sweep.results)
    return build_report_payload([sweep, sweep_b], [cfg, cfg])


# --------------------------------------------------------------------- §3


def test_payload_schema_round_trip_and_render_smoke(small_run) -> None:
    """build -> json -> render works; the HTML carries the §2 anchors and is
    byte-stable across the JSON round-trip (ADR 0014 §3/§6)."""
    cfg, sweep = small_run
    payload = build_report_payload([sweep], [cfg], run_id="t1")
    assert payload["payload_version"] == PAYLOAD_VERSION

    round_tripped = json.loads(json.dumps(payload))
    html_direct = render_report(payload)
    html_rt = render_report(round_tripped)
    assert html_direct == html_rt  # pure function of the payload

    for section in ("2.1", "2.2", "2.3", "2.4", "2.7"):
        assert SECTION_ANCHORS[section] in html_direct
    # §2.5 omitted (no emission rate in this sweep), §2.6 omitted (single ISO)
    assert SECTION_ANCHORS["2.5"] not in html_direct
    assert SECTION_ANCHORS["2.6"] not in html_direct
    # fully offline (§1): no external URL outside the html spec namespace
    assert "http" not in html_direct.replace("http://www.w3.org", "")


def test_render_refuses_unknown_payload_version(small_run) -> None:
    """payload_version=99 (and a missing version) raise ValueError (§3)."""
    cfg, sweep = small_run
    payload = build_report_payload([sweep], [cfg])
    with pytest.raises(ValueError, match="payload_version"):
        render_report({**payload, "payload_version": 99})
    with pytest.raises(ValueError, match="payload_version"):
        render_report({k: v for k, v in payload.items() if k != "payload_version"})


def test_mandatory_provenance_fields(small_run) -> None:
    """iso/mode/sensitivity/additionality_only are always present (§3/§4)."""
    cfg, sweep = small_run
    prov = build_report_payload([sweep], [cfg])["provenance"]
    assert prov["iso"] == "SAMPLE"
    assert prov["mode"] == "premium_cap"
    assert prov["sensitivity"] == "mid"
    assert prov["additionality_only"] is False


def test_hourly_discipline_selected_setpoint_only(small_run) -> None:
    """Default hourly block carries ONLY the selected setpoint, 3-sig-fig
    rounded (§3 size discipline)."""
    cfg, sweep = small_run
    payload = build_report_payload([sweep], [cfg])
    hourly = payload["hourly"]
    sel = select_hourly_setpoint(sweep)
    assert hourly["selected"]["SAMPLE"] == sel
    assert list(hourly["series"]["SAMPLE"]) == [f"{sel:g}"]

    series = hourly["series"]["SAMPLE"][f"{sel:g}"]
    values = list(series["grid_buy_mwh"])
    for soc in series["soc_mwh"].values():
        values.extend(soc)
    assert values, "hourly series must not be empty"
    for v in values:
        assert v == float(f"{v:.3g}"), f"{v} is not 3-sig-fig rounded"


def test_hourly_all_includes_every_setpoint(small_run) -> None:
    """--report-hourly all includes every swept setpoint (§3)."""
    cfg, sweep = small_run
    payload = build_report_payload([sweep], [cfg], report_hourly="all")
    assert sorted(payload["hourly"]["series"]["SAMPLE"]) == ["20", "5"]


def test_selected_setpoint_skips_non_optimal(small_run) -> None:
    """The default §2.7 setpoint is the highest-matching *optimal* one."""
    _, sweep = small_run
    broken = copy.deepcopy(sweep)
    best = max(broken.results, key=lambda r: r.matching_pct)
    best.status = "Infeasible"
    remaining = [r for r in broken.results if r.status.lower() == "optimal"]
    assert (
        select_hourly_setpoint(broken)
        == max(remaining, key=lambda r: r.matching_pct).setpoint
    )


# --------------------------------------------------------------------- §2


def test_non_optimal_setpoint_flagged_inline(small_run) -> None:
    """§2.1: a non-optimal solve is flagged in the provenance header."""
    cfg, sweep = small_run
    broken = copy.deepcopy(sweep)
    broken.results[0].status = "Infeasible"
    html = render_report(build_report_payload([broken], [cfg]))
    assert "solve-bad" in html and "Infeasible" in html


def test_residual_co2_section_gated_on_rate(small_run) -> None:
    """§2.5 appears only when some setpoint has a nonzero residual."""
    cfg, sweep = small_run
    payload = build_report_payload([sweep], [cfg])
    assert SECTION_ANCHORS["2.5"] not in render_report(payload)
    with_co2 = json.loads(json.dumps(payload))
    with_co2["frontier"][0]["residual_co2_tons"] = 123.0
    with_co2["frontier"][0]["grid_co2_tons"] = 123.0
    assert SECTION_ANCHORS["2.5"] in render_report(with_co2)


def test_multi_iso_batch_payload_grows_comparison_table(small_run) -> None:
    """§2.6: a >1-ISO batch payload renders the multi-ISO table (and a
    single-ISO run omits it — covered by the round-trip smoke test)."""
    payload = _two_iso_payload(small_run)
    assert payload["provenance"]["iso"] == "multi"
    assert payload["provenance"]["isos"] == ["SAMPLE", "SAMPLE_B"]
    html = render_report(payload)
    assert SECTION_ANCHORS["2.6"] in html
    assert "SAMPLE_B" in html


def test_split_tech_energy_in_build_mix_rows(small_run) -> None:
    """§2.3: build-mix rows carry build_energy_mwh (None for non-split)."""
    cfg, sweep = small_run
    rows = build_report_payload([sweep], [cfg])["build_mix"]
    assert {r["resource"] for r in rows} == {"solar", "battery"}
    assert all(r["build_energy_mwh"] is None for r in rows)  # no split tech here


# --------------------------------------------------------------------- §6 seams


def test_write_outputs_emits_report_by_default(small_run, tmp_path) -> None:
    """write_outputs(config=...) writes report.json + report.html (§6)."""
    cfg, sweep = small_run
    paths = write_outputs(sweep, tmp_path, config=cfg)
    assert paths["report_json"].exists() and paths["report_html"].exists()
    payload = json.loads(paths["report_json"].read_text())
    assert payload["payload_version"] == PAYLOAD_VERSION


def test_write_outputs_report_false_suppresses(small_run, tmp_path) -> None:
    """report=False (the CLI's --no-report) suppresses both files (§6)."""
    cfg, sweep = small_run
    paths = write_outputs(sweep, tmp_path, config=cfg, report=False)
    assert "report_json" not in paths
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "report.html").exists()


def test_write_report_batch(small_run, tmp_path) -> None:
    """write_report writes one report covering a whole batch (§2.6/§6)."""
    cfg, sweep = small_run
    sweep_b = SweepResult(iso="SAMPLE_B", mode=sweep.mode, results=sweep.results)
    paths = write_report([sweep, sweep_b], [cfg, cfg], tmp_path, run_id="batch1")
    html = paths["report_html"].read_text()
    assert SECTION_ANCHORS["2.6"] in html


def test_compose_run_id() -> None:
    """Run id composes <iso|multi>_<mode>_<YYYYMMDD-HHMMSS> (§5)."""
    from datetime import datetime

    now = datetime(2026, 7, 2, 12, 30, 45)
    assert compose_run_id(["SAMPLE"], "premium_cap", now) == (
        "SAMPLE_premium_cap_20260702-123045"
    )
    assert compose_run_id(["A", "B"], "matching_target", now) == (
        "multi_matching_target_20260702-123045"
    )


# ------------------------------------------------------------------ CLI seams


def _cli_fixtures(tmp_path):
    """Minimal single-ISO 8760 load + LMP files for one fast CLI solve."""
    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    load = 100.0 + 20.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = 25.0 + 10.0 * np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)
    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "load_mwh": load}).to_csv(
        load_path, index=False
    )
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "lmp": lmp}).to_csv(
        lmp_path, index=False
    )
    return load_path, lmp_path


def test_cli_results_flag_and_no_report(tmp_path, monkeypatch) -> None:
    """--results composes results/<run-id>/ and re-using the id overwrites the
    directory; --no-report suppresses report.json + report.html (§5/§6).

    Both CLI behaviors share one pair of solves against the same run id.
    """
    load_path, lmp_path = _cli_fixtures(tmp_path)
    # Solar-only + one delta keeps each 8760 solve at a few seconds (the same
    # trick as test_cli.py) so this double-solve test stays fast.
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "active_resources": ["solar_pv"],
                "premium_deltas": [5.0],
            }
        )
    )
    monkeypatch.chdir(tmp_path)  # RESULTS_ROOT is relative to the cwd
    argv = [
        "--load",
        str(load_path),
        "--lmp",
        str(lmp_path),
        "--config",
        str(config_path),
        "--results",
        "--run-id",
        "demo_run",
    ]

    assert cli_main(argv) == 0
    run_dir = tmp_path / "results" / "demo_run"
    assert (run_dir / "SAMPLE_frontier.parquet").exists()
    assert (run_dir / "SAMPLE_run_metadata.json").exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.html").exists()
    payload = json.loads((run_dir / "report.json").read_text())
    assert payload["provenance"]["run_id"] == "demo_run"

    # Re-using the run id overwrites the directory (§5): a stale file from the
    # first run must be gone, and --no-report must leave no report files.
    stale = run_dir / "stale.txt"
    stale.write_text("old")
    assert cli_main(argv + ["--no-report"]) == 0
    assert not stale.exists()
    assert (run_dir / "SAMPLE_frontier.parquet").exists()
    assert not (run_dir / "report.json").exists()
    assert not (run_dir / "report.html").exists()


# ------------------------------------------------- committed demo run folder


def _demo_run_dir() -> Path | None:
    """The committed worked-example run folder under results/ (ADR 0014 §5)."""
    results = _ROOT / "results"
    if not results.is_dir():
        return None
    for run_dir in sorted(results.iterdir()):
        if (run_dir / "report.json").exists():
            return run_dir
    return None


def test_render_report_script_regenerates_byte_stable_html(tmp_path) -> None:
    """scripts/render_report.py regenerates byte-identical HTML from the
    committed demo run folder without re-solving (§6)."""
    demo = _demo_run_dir()
    assert demo is not None, "committed demo run folder missing under results/"
    work = tmp_path / demo.name
    shutil.copytree(demo, work)
    committed = (work / "report.html").read_bytes()
    (work / "report.html").unlink()

    proc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "render_report.py"), str(work)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert (work / "report.html").read_bytes() == committed


def test_render_report_script_refuses_unknown_version(tmp_path) -> None:
    """The regeneration script surfaces the §3 version refusal cleanly."""
    demo = _demo_run_dir()
    assert demo is not None, "committed demo run folder missing under results/"
    work = tmp_path / "bad"
    work.mkdir()
    payload = json.loads((demo / "report.json").read_text())
    payload["payload_version"] = 99
    (work / "report.json").write_text(json.dumps(payload))

    proc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "render_report.py"), str(work)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "payload_version" in proc.stderr
    assert not (work / "report.html").exists()
