#!/usr/bin/env python3
"""T1.6 driver-battery rungs on the ``neiso-t3`` GOLDEN recipe — metrics + assembly.

capx D94 measurement helper (``docs/handoffs/PRECOMMIT-capx-d94-2026-09-24.md``).
Not standing tooling: the measurement record for
``docs/handoffs/FINDING-capx-d94-2026-09-24.md``. Nothing under ``scripts/`` or
``src/`` is edited by the lane.

WHY IT EXISTS. ``scripts/run_driver_battery.py`` solves a rung as
``ScenarioConfig(iso, use_campd_bins=False, start, end, **overrides)`` — dataclass
defaults, legacy bins, and NEITHER of the two ``neiso-t3`` pins
(``ccs_retrofit_vom_adder=8.0``, ``ccs_retrofit_fixed_cost_co2_scaling=False``).
The D94 charter requires every rung to describe the model the verdict
describes, so each rung is SOLVED by the proven D92 command —
``scripts/run_full_horizon.py --golden-posture`` + both pins + the rung's own
``--entry-rate-limits`` / ``--no-entry-rate-limits`` — and this helper then does
the two zero-LP halves the battery instrument would otherwise have done:

``metrics``   Run IN THE SHARD after its solve, over its own ``--out-dir``:
              computes the rung's metrics with the instrument's OWN
              :func:`run_driver_battery._extract_metrics` (same cache reads, same
              rounding, same ACP ratio) and writes the rung row in the exact
              shape :func:`run_driver_battery.evaluate_rung` emits, at
              ``<out-dir>/_battery_metrics/NEISO/T1.6__NEISO__<rung>.json``.
              It also asserts the pins and the rung override off the solved
              ``run_config.json`` and REFUSES (exit 2) on any mismatch.

``assemble``  Run IN THE PARENT: feeds the two rung rows through the
              instrument's own :func:`run_driver_battery.run_ladder` via its
              ``evaluate_fn`` test seam (so the expectation ledger, rung order
              and ladder shape are the instrument's, not re-implemented), and
              writes the battery JSON + markdown exactly as ``main`` does.

``assemble`` is VALIDATED before any D94 LP (PRECOMMIT §4.3): pointed at the
committed ``bau-d46/fc6/_battery_metrics`` rows it re-emits the committed
``driver-battery-neiso-2026-09-03.json`` ``ladders`` block byte-identically.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(_REPO), str(_REPO / "src"), str(_REPO / "scripts")]

ISO = "NEISO"
START, END = 2026, 2050
#: The two pins ``neiso-t3``'s recipe carries (the two UNIDENTIFIED DOF entries).
PINS = {"ccs_retrofit_vom_adder": 8.0, "ccs_retrofit_fixed_cost_co2_scaling": False}
#: The T1.6 rung registry, verbatim from ``run_driver_battery.build_ladders``.
RUNG_OVERRIDE = {"vre_short": True, "vre_long": False}


def _load_battery():
    spec = importlib.util.spec_from_file_location(
        "run_driver_battery", _REPO / "scripts" / "run_driver_battery.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_driver_battery"] = mod
    spec.loader.exec_module(mod)
    return mod


def _t16_ladder(rdb):
    lads = [lad for lad in rdb.build_ladders() if lad.test_id == "T1.6"]
    if len(lads) != 1:
        raise SystemExit("expected exactly one T1.6 ladder in build_ladders()")
    lad = lads[0]
    got = {r.label: r.overrides for r in lad.rungs}
    want = {k: {"entry_rate_limits": v} for k, v in RUNG_OVERRIDE.items()}
    if got != want:
        raise SystemExit(f"T1.6 rung registry moved: {got} != {want}")
    return lad


def _cache_dir(out_dir: Path) -> Path:
    cands = sorted(p for p in (out_dir / ISO).iterdir() if p.is_dir())
    if len(cands) != 1:
        raise SystemExit(f"{out_dir}: expected one {ISO}/<key> dir, found {len(cands)}")
    return cands[0]


def cmd_metrics(out_dir: Path, rung: str) -> int:
    """Compute one rung's battery row from a solved golden-recipe out-dir."""
    rdb = _load_battery()
    _t16_ladder(rdb)
    rc = json.loads((out_dir / "run_config.json").read_text())
    sc = rc["scenario_config"]
    bad = {k: (sc.get(k), v) for k, v in PINS.items() if sc.get(k) != v}
    if sc.get("entry_rate_limits") is not RUNG_OVERRIDE[rung]:
        bad["entry_rate_limits"] = (sc.get("entry_rate_limits"), RUNG_OVERRIDE[rung])
    if sc.get("mode") != "forecast" or sc.get("iso") != ISO:
        bad["mode/iso"] = (sc.get("mode"), sc.get("iso"))
    if bad:
        print(f"REFUSED — config signature mismatch {{field: (solved, required)}}: {bad}")
        return 2
    key = rc["cache_key"]
    if _cache_dir(out_dir).name != key:
        print(f"REFUSED — cache dir {_cache_dir(out_dir).name} != run_config key {key}")
        return 2

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache
    from market_sim.results.evolution_ledger import load_ledgers_for_run
    from market_sim.results.export import _summarize_year

    cache.CACHE_ROOT = out_dir
    safe = f"T1.6__{ISO}__{rung}"
    spec = rdb.RungSpec(
        rung_id=f"T1.6:{ISO}:{rung}",
        test_id="T1.6",
        iso=ISO,
        rung_label=rung,
        overrides={"entry_rate_limits": RUNG_OVERRIDE[rung]},
        start_year=START,
        end_year=END,
        cache_root=str(out_dir),
        metrics_cache=str(out_dir / "_battery_metrics" / ISO / f"{safe}.json"),
    )
    # _extract_metrics reads ``config`` only for the ISO's ACP ceiling.
    config = ScenarioConfig(iso=ISO, start_year=START, end_year=END)
    ledgers = load_ledgers_for_run(out_dir / ISO / key)
    metrics = rdb._extract_metrics(spec, config, cache, key, ledgers, _summarize_year)
    row = {
        "rung_id": spec.rung_id,
        "test_id": spec.test_id,
        "iso": ISO,
        "rung_label": rung,
        "overrides": spec.overrides,
        "status": "ok",
        "metrics": metrics,
        "cached": False,
    }
    path = Path(spec.metrics_cache)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, indent=2))
    # Cross-check against the summary grain the parent will also hold.
    summ = json.loads((out_dir / "full_horizon_summary.json").read_text())
    co2_traj = round(sum(float(r["co2_mt"]) for r in summ["trajectory"]), 4)
    print(f"cache_key {key}")
    print(f"metrics {json.dumps(metrics, sort_keys=True)}")
    print(f"co2_mt_total={metrics['co2_mt_total']} trajectory_sum={co2_traj}")
    print(f"wrote {path}")
    return 0


def cmd_assemble(
    rows: list[Path], out: Path, elapsed_s: float | None, fleet_note: str | None = None
) -> int:
    """Assemble the battery JSON + markdown from rung rows via the instrument."""
    rdb = _load_battery()
    lad = _t16_ladder(rdb)
    by_label = {}
    for p in rows:
        r = json.loads(p.read_text())
        by_label[r["rung_label"]] = r

    def _evaluate(spec_dict: dict) -> dict:
        r = dict(by_label[spec_dict["rung_label"]])
        if r["overrides"] != spec_dict["overrides"]:
            raise SystemExit(f"rung override mismatch for {spec_dict['rung_label']}")
        return r

    result = rdb.run_ladder(
        lad, ISO, START, END, "unused", "unused", 1, evaluate_fn=_evaluate
    )
    run_date = out.stem.rsplit("-", 3)[-3:]
    run_date = "-".join(run_date) if len(run_date) == 3 else date.today().isoformat()
    payload = {
        "iso": ISO,
        "start_year": START,
        "end_year": END,
        "max_rungs": None,
        "elapsed_s": elapsed_s,
        "ladders": [result],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    md = rdb.render_report(ISO, START, END, [result], run_date)
    if fleet_note:
        # render_report hard-codes the legacy-bins bullet; the D94 rungs are
        # the golden recipe, so the bullet is replaced rather than left false.
        md = "\n".join(
            f"- **Fleet / recipe:** {fleet_note}"
            if "legacy equal-width bins" in line
            else line
            for line in md.split("\n")
        )
    out.with_suffix(".md").write_text(md)
    for e in result["expectations"]:
        print(f"{e['expr_id']}: {e['status']} — {e['detail']}")
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (``metrics`` in a shard, ``assemble`` in the parent)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("metrics")
    m.add_argument("--out-dir", type=Path, required=True)
    m.add_argument("--rung", choices=sorted(RUNG_OVERRIDE), required=True)
    a = sub.add_parser("assemble")
    a.add_argument("--rows", type=Path, nargs="+", required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--elapsed-s", type=float, default=None)
    a.add_argument("--fleet-note", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "metrics":
        return cmd_metrics(args.out_dir, args.rung)
    return cmd_assemble(args.rows, args.out, args.elapsed_s, args.fleet_note)


if __name__ == "__main__":
    raise SystemExit(main())
