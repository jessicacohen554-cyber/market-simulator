"""The per-ISO clean solve profile and its incremental manifest (cleanup-E).

Hermetic: nothing here runs a curate script or reads ``data/raw`` payloads.
Partition registries are monkeypatched, the clean tree is a tmp ``CLEAN_DIR``
and :func:`scripts.regenerate_clean.regenerate`'s subprocess is faked.

What is pinned:

* registry integrity — every entry is a known datatype with a curate script,
  a schema, and the CLI flags it forwards actually exist in that script;
* coverage — every clean-only datatype the solve path reads (the explicit
  list below, plus every ``data/clean`` datatype in
  ``input_completeness._PARTITION_REQUIREMENTS``) is in some ISO's profile;
* planning — ISO aliasing (NEISO -> ISONE), cross-ISO reads (NYISO reads
  NEISO's seam price), solve years never forwarded to the coal tables;
* the manifest — skip iff key unchanged + scope covered + output present,
  ``--force`` overrides, a changed key rebuilds.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from market_sim.data import input_completeness
from scripts import regenerate_clean as rc
from scripts.lib import clean_profiles as cp

#: Datatypes a solve-path loader reads from data/clean with no
#: MARKET_SIM_USE_CLEAN gate and no raw fallback (verified 2026-10-01 by
#: grepping read_clean/clean_exists consumers under src/market_sim). NOT here,
#: on purpose: nuclear-license-status and nyiso-renewable-curtailment (no
#: consumer outside their own module), nyiso-downstate-gas (raw fallback).
SOLVE_PATH_CLEAN_ONLY: frozenset[str] = frozenset(
    {
        "capacity-deliverability",
        "hydro-plant-modes",
        "coal-stocks",
        "coal-receipts",
        "transfer-interface-limits",
        "ramp-capability",
        "gtc-limits",
        "reserve-requirements",
        "storage-as-awards",
        "maxgen-events",
        "winter-fuel-inventory",
        "chp-btm-share",
        "nyiso-interface-flows",
        "seam-neighbour-price",
        "confirmed-retirements",
        "transmission-expansion",
        "capacity-market-avoidable-cost-rate",
    }
)


def _fake_partitions(source: cp.CleanSource) -> tuple[str, ...] | None:
    """Static stand-in for the curate registries (no imports of raw readers)."""
    table = {
        "capacity-deliverability": ("CAISO", "ISONE", "MISO", "NYISO", "PJM"),
        "hydro-plant-modes": ("CAISO", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SPP"),
        "transfer-interface-limits": ("PJM",),
        "ramp-capability": ("CAISO", "MISO", "PJM"),
        "reserve-requirements": ("NEISO",),
        "storage-as-awards": ("CAISO",),
        "maxgen-events": ("MISO",),
        "winter-fuel-inventory": ("ISONE",),
    }
    if isinstance(source.partitions, tuple):
        return source.partitions
    return table.get(source.datatype)


@pytest.fixture
def fake_registries(monkeypatch):
    """Replace runtime registry resolution with a static table."""
    monkeypatch.setattr(cp, "resolve_partitions", _fake_partitions)


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("source", cp.SOLVE_SOURCES, ids=lambda s: s.datatype)
def test_entry_maps_to_script_schema_and_flags(source):
    assert source.datatype in rc.DATATYPES
    assert source.script.is_file(), source.script
    assert (cp.SCHEMA_DIR / f"{source.datatype}.schema.yaml").is_file()
    assert source.lane in {"backcast", "forecast"}
    text = source.script.read_text()
    for flag in (source.iso_flag, source.years_flag):
        if flag:
            assert re.search(rf"[\"']{re.escape(flag)}[\"']", text), (
                f"{source.script.name} does not define {flag}"
            )


@pytest.mark.parametrize("source", cp.SOLVE_SOURCES, ids=lambda s: s.datatype)
def test_registry_resolver_names_a_real_attribute(source):
    if not isinstance(source.partitions, str) or source.partitions == "any":
        return
    module, attr = source.partitions.split(":")
    path = cp.REPO_ROOT / Path(*module.split("."))
    candidates = [path.with_suffix(".py"), path / "__init__.py"]
    found = next((c for c in candidates if c.is_file()), None)
    assert found is not None, module
    if found.name == "__init__.py":
        text = "".join(p.read_text() for p in found.parent.rglob("*.py"))
    else:
        text = found.read_text()
    assert re.search(rf"^(def {attr}\b|{attr}\s*[:=])", text, re.M) or (
        re.search(rf"\b{attr}\b", text)
    ), f"{module} has no {attr}"


def test_every_solve_path_clean_datatype_is_in_a_profile():
    profiled = {s.datatype for s in cp.SOLVE_SOURCES}
    required = set(SOLVE_PATH_CLEAN_ONLY)
    for req in input_completeness._PARTITION_REQUIREMENTS:
        if not req.location.startswith("data/clean"):
            continue  # e.g. the campd-unit-outages raw extract
        required.update(d.strip() for d in req.datatype.split("+"))
    assert required <= profiled, sorted(required - profiled)


def test_registry_has_no_duplicates():
    names = [s.datatype for s in cp.SOLVE_SOURCES]
    assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------
def _plan(isos, years=None, **kw):
    return {r.datatype: r for r in cp.plan_profile(isos, years, **kw)}


def test_every_profiled_datatype_reaches_some_iso(fake_registries):
    reached: set[str] = set()
    for iso in cp.MODEL_ISOS:
        reached |= set(_plan([iso], include_forecast=True))
    # gtc-limits is ERCOT-only; forecast-lane entries come from the --with-forecast leg.
    assert reached == {s.datatype for s in cp.SOLVE_SOURCES}


def test_neiso_uses_isone_partition_alias(fake_registries):
    plan = _plan(["NEISO"])
    assert plan["capacity-deliverability"].args == ("--isos", "ISONE")
    assert plan["winter-fuel-inventory"].args == ("--isos", "ISONE")
    assert plan["hydro-plant-modes"].args == ("--iso", "NEISO")
    assert "seam-neighbour-price" not in plan


def test_nyiso_reads_neiso_seam_partition(fake_registries):
    plan = _plan(["NYISO"], years=[2024, 2023])
    assert plan["seam-neighbour-price"].args == ("--isos", "NEISO")
    assert plan["nyiso-interface-flows"].args == ("--years", "2023", "2024")
    assert plan["nyiso-interface-flows"].years == (2023, 2024)


def test_solve_years_never_reach_the_coal_tables(fake_registries):
    plan = _plan(["MISO"], years=[2022])
    assert plan["coal-stocks"].args == ()
    assert plan["coal-receipts"].args == ()
    assert plan["coal-receipts"].years is None


def test_forecast_lane_is_opt_in(fake_registries):
    assert "confirmed-retirements" not in _plan(["PJM"])
    assert "confirmed-retirements" in _plan(["PJM"], include_forecast=True)


def test_iso_without_a_partition_is_dropped(fake_registries):
    plan = _plan(["SPP"])
    assert "ramp-capability" not in plan
    assert "gtc-limits" not in plan
    assert set(plan) == {
        "hydro-plant-modes",
        "coal-stocks",
        "coal-receipts",
        "chp-btm-share",
    }


def test_all_builds_everything_unsubset(fake_registries):
    plan = _plan(["all"])
    assert set(plan) == {s.datatype for s in cp.SOLVE_SOURCES if s.lane == "backcast"}
    assert all(r.args == () and r.isos is None for r in plan.values())


def test_multi_iso_unions_partitions(fake_registries):
    plan = _plan(["CAISO", "PJM"])
    assert plan["ramp-capability"].args == ("--isos", "CAISO", "PJM")


# ---------------------------------------------------------------------------
# Manifest key
# ---------------------------------------------------------------------------
def test_blob_sha_matches_git_hash_object(tmp_path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"hello\n")
    # `git hash-object` of "hello\n" — a fixed, well-known value.
    assert cp.blob_sha(f) == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_code_files_follow_scripts_lib_imports():
    files = cp.code_files(cp.SOURCES_BY_DATATYPE["maxgen-events"].script)
    rel = {p.relative_to(cp.REPO_ROOT).as_posix() for p in files}
    assert "scripts/data/curate_maxgen_events.py" in rel
    assert "scripts/lib/clean_io.py" in rel
    # scripts.lib.maxgen_events is a package: every module in it is keyed.
    assert "scripts/lib/maxgen_events/__init__.py" in rel


def test_manifest_key_is_order_independent_and_sensitive():
    a = {"code": {"x": "1", "y": "2"}, "schema": "s", "raw": {}}
    b = {"raw": {}, "schema": "s", "code": {"y": "2", "x": "1"}}
    assert cp.manifest_key(a) == cp.manifest_key(b)
    assert cp.manifest_key(a) != cp.manifest_key({**a, "schema": "t"})


def test_untracked_raw_input_falls_back_to_stat(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cp, "_git", lambda *a: None)
    (tmp_path / "raw").mkdir()
    f = tmp_path / "raw" / "a.csv"
    f.write_text("1")
    first = cp.raw_fingerprint("raw")
    assert first["head"] is None and "raw/a.csv" in first["stat"]
    f.write_text("12")
    assert cp.raw_fingerprint("raw") != first


# ---------------------------------------------------------------------------
# Manifest skip logic
# ---------------------------------------------------------------------------
def _run(isos=None, years=None, datatype="maxgen-events"):
    return cp.PlannedRun(datatype, (), isos, years)


def _make_output(clean: Path, datatype="maxgen-events"):
    out = clean / datatype / "MISO"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{datatype}.parquet").write_bytes(b"PAR1")


def test_skip_requires_manifest_key_and_output(tmp_clean_dir):
    run = _run(("MISO",))
    assert not cp.should_skip(run, "k")  # no manifest
    _make_output(tmp_clean_dir)
    cp.write_manifest(run, "k", {})
    assert cp.should_skip(run, "k")
    assert not cp.should_skip(run, "other-key")
    for p in (tmp_clean_dir / "maxgen-events").rglob("*.parquet"):
        p.unlink()
    assert not cp.should_skip(run, "k")  # output gone


def test_scope_coverage_and_widening(tmp_clean_dir):
    _make_output(tmp_clean_dir)
    cp.write_manifest(_run(("MISO",), (2023,)), "k", {})
    assert cp.should_skip(_run(("MISO",), (2023,)), "k")
    assert not cp.should_skip(_run(("PJM",), (2023,)), "k")
    assert not cp.should_skip(_run(("MISO",), None), "k")  # wants every year
    cp.write_manifest(_run(("PJM",), (2024,)), "k", {})  # same key -> widened
    assert cp.should_skip(_run(("MISO", "PJM"), (2023, 2024)), "k")
    cp.write_manifest(_run(None, None), "k2", {})  # new key -> replaced
    assert cp.should_skip(_run(("SPP",), (2019,)), "k2")
    assert not cp.should_skip(_run(("SPP",)), "k")


def test_no_manifest_when_script_wrote_no_dir(tmp_clean_dir):
    assert cp.write_manifest(_run(), "k", {}) is None
    assert not (tmp_clean_dir / "maxgen-events").exists()


def test_regenerate_skips_then_force_rebuilds(tmp_clean_dir, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        _make_output(tmp_clean_dir)
        return subprocess.CompletedProcess(cmd, 0)

    key_parts = {"v": 1}
    monkeypatch.setattr(rc.subprocess, "run", fake_run)
    monkeypatch.setattr(cp, "manifest_components", lambda d: dict(key_parts))
    run = _run(("MISO",))
    kw = {"incremental": True, "scopes": {"maxgen-events": run}}
    extra = {"maxgen-events": ("--isos", "MISO")}

    assert rc.regenerate(["maxgen-events"], extra, **kw) == 0
    assert len(calls) == 1 and calls[0][-2:] == ["--isos", "MISO"]
    assert (tmp_clean_dir / "maxgen-events" / cp.MANIFEST_NAME).is_file()
    assert rc.regenerate(["maxgen-events"], extra, **kw) == 0
    assert len(calls) == 1  # kept
    assert rc.regenerate(["maxgen-events"], extra, force=True, **kw) == 0
    assert len(calls) == 2  # --force
    key_parts["v"] = 2
    assert rc.regenerate(["maxgen-events"], extra, **kw) == 0
    assert len(calls) == 3  # key moved


def test_bare_regenerate_writes_no_manifest(tmp_clean_dir, monkeypatch):
    def fake_run(cmd, **kwargs):
        _make_output(tmp_clean_dir)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(rc.subprocess, "run", fake_run)
    assert rc.regenerate(["maxgen-events"]) == 0
    assert not (tmp_clean_dir / "maxgen-events" / cp.MANIFEST_NAME).exists()


def test_cli_dry_run_and_list(capsys, monkeypatch, fake_registries):
    assert rc.main(["--list"]) == 0
    assert "maxgen-events" in capsys.readouterr().out
    assert rc.main(["--solve-profile", "nyiso", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "seam-neighbour-price: curate_seam_neighbour_price.py --isos NEISO" in out
    with pytest.raises(SystemExit):
        rc.main(["--solve-profile", "XX"])
    with pytest.raises(SystemExit):
        rc.main(["--years", "2023"])
