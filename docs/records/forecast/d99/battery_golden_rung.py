#!/usr/bin/env python3
"""T1.6 driver-battery rungs on the ``neiso-t3`` GOLDEN recipe, Q72 lever — metrics + assembly.

capx D99 measurement helper (``docs/handoffs/PRECOMMIT-capx-d99-2026-09-26.md``).
A copy of capx D94's ``docs/handoffs/d94/battery_golden_rung.py`` (kept as the
D94 record), re-pointed to the lever owner ruling Q72 put on the T1.6 ladder:
``entry_pipeline_aware_signal`` (``vre_short`` = False, ``vre_long`` = True).
Not standing tooling. Nothing under ``scripts/`` or ``src/`` is imported
except the battery instrument itself, whose own functions do every step.

``metrics``   Run IN THE SHARD after its solve, over its own ``--out-dir``:
              computes the rung's metrics with the instrument's OWN
              :func:`run_driver_battery._extract_metrics` (same cache reads, same
              rounding, same ACP ratio, and the Q72 2041–2050 window mean) and
              writes the rung row in the exact shape
              :func:`run_driver_battery.evaluate_rung` emits. It asserts both pins,
              ``entry_rate_limits`` = True (the golden's own, NOT perturbed) and the
              rung override off the solved ``run_config.json``, and REFUSES
              (exit 2) on any mismatch.

``reuse``     Run IN THE PARENT, zero LP: builds the ``vre_short`` row from
              the D96 ``base`` leg, which is the same config (PRECOMMIT §2: the
              resolved ``vre_short`` config keys to D96 ``base``'s literal
              ``dbef1ecac9596c90`` at this HEAD, and G-DRIFT is all-INERT). D96's
              cache parquets are off ``main``, so the cache-grain metrics are
              taken from capx D94's committed ``vre_short`` row — admissible
              because D96 ``base`` reproduces D94 ``vre_short`` on every
              trajectory cell (FINDING-capx-d96 E1) and all 25 evolution ledgers
              are byte-identical (asserted here). The one new metric, the Q72
              window mean, is computed from D96 ``base``'s committed ledgers'
              ``rps_dual`` (= ``round(result.rps_shadow_price, 6)`` for NEISO's
              scalar row, ``runner.py``), and its ledger-vs-cache grain equality is
              validated on ``vre_long``, whose parquets the shard pushes.

``assemble``  Run IN THE PARENT: feeds the two rung rows through the
              instrument's own :func:`run_driver_battery.run_ladder` via its
              ``evaluate_fn`` test seam, and writes the battery JSON + markdown
              exactly as ``main`` does.
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
#: The T1.6 rung registry, verbatim from ``run_driver_battery.build_ladders`` (Q72).
RUNG_FIELD = "entry_pipeline_aware_signal"
RUNG_OVERRIDE = {"vre_short": False, "vre_long": True}
#: The Q72 window metric T1.6b reads.
MEAN_METRIC = "rps_dual_over_acp_mean_2041_2050"


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
    want = {k: {RUNG_FIELD: v} for k, v in RUNG_OVERRIDE.items()}
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
    if sc.get(RUNG_FIELD) is not RUNG_OVERRIDE[rung]:
        bad[RUNG_FIELD] = (sc.get(RUNG_FIELD), RUNG_OVERRIDE[rung])
    if sc.get("entry_rate_limits") is not True:
        bad["entry_rate_limits"] = (sc.get("entry_rate_limits"), True)
    if sc.get("mode") != "forecast" or sc.get("iso") != ISO:
        bad["mode/iso"] = (sc.get("mode"), sc.get("iso"))
    if bad:
        print(
            f"REFUSED — config signature mismatch {{field: (solved, required)}}: {bad}"
        )
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
        overrides={RUNG_FIELD: RUNG_OVERRIDE[rung]},
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
    led_mean = _ledger_mean_ratio(ledgers)
    print(f"{MEAN_METRIC}={metrics.get(MEAN_METRIC)} ledger_grain={led_mean}")
    print(f"wrote {path}")
    return 0


def _ledger_mean_ratio(ledgers: dict) -> float | None:
    """The Q72 window mean at LEDGER grain (``rps_dual`` / the NEISO ACP)."""
    rdb = _load_battery()
    lo, hi = rdb.T16B_MEAN_WINDOW
    from market_sim.config.scenarios import ScenarioConfig

    acp = rdb._acp_ceiling(ScenarioConfig(iso=ISO, start_year=START, end_year=END))
    win = [ledgers[y].get("rps_dual") for y in range(lo, hi + 1) if y in ledgers]
    if not acp or len(win) != hi - lo + 1 or any(d is None for d in win):
        return None
    return round(sum(win) / len(win) / acp, 4)


def cmd_reuse(base_dir: Path, d94_dir: Path, out: Path) -> int:
    """Build the ``vre_short`` row from D96 ``base`` (same config), zero LP."""
    rdb = _load_battery()
    _t16_ladder(rdb)
    rc = json.loads((base_dir / "run_config.json").read_text())
    sc = rc["scenario_config"]
    want = dict(PINS, entry_rate_limits=True, mode="forecast", iso=ISO)
    want[RUNG_FIELD] = RUNG_OVERRIDE["vre_short"]
    bad = {k: (sc.get(k), v) for k, v in want.items() if sc.get(k) != v}
    if bad:
        print(f"REFUSED — D96 base config signature mismatch: {bad}")
        return 2
    d94_row_p = d94_dir / "_battery_metrics" / ISO / f"T1.6__{ISO}__vre_short.json"
    d94_row = json.loads(d94_row_p.read_text())
    key96 = _cache_dir(base_dir).name
    key94 = _cache_dir(d94_dir).name
    # Byte-identity of every evolution ledger + every trajectory cell.
    for y in range(START, END + 1):
        a = (base_dir / ISO / key96 / f"evolution_{y}.json").read_bytes()
        b = (d94_dir / ISO / key94 / f"evolution_{y}.json").read_bytes()
        if a != b:
            print(f"REFUSED — evolution_{y}.json differs between D96 base and D94")
            return 2
    ta = json.loads((base_dir / "full_horizon_summary.json").read_text())["trajectory"]
    tb = json.loads((d94_dir / "full_horizon_summary.json").read_text())["trajectory"]
    if ta != tb:
        print("REFUSED — trajectory differs between D96 base and D94 vre_short")
        return 2
    from market_sim.results.evolution_ledger import load_ledgers_for_run

    ledgers = load_ledgers_for_run(base_dir / ISO / key96)
    metrics = dict(d94_row["metrics"])
    mean = _ledger_mean_ratio(ledgers)
    if mean is None:
        print("REFUSED — no complete 2041–2050 rps_dual window in D96 base ledgers")
        return 2
    # Insert the new metric right after the final-year ratio (instrument order).
    ordered = {}
    for k, v in metrics.items():
        ordered[k] = v
        if k == "rps_dual_over_acp":
            ordered[MEAN_METRIC] = mean
    row = {
        "rung_id": "T1.6:NEISO:vre_short",
        "test_id": "T1.6",
        "iso": ISO,
        "rung_label": "vre_short",
        "overrides": {RUNG_FIELD: RUNG_OVERRIDE["vre_short"]},
        "status": "ok",
        "metrics": ordered,
        "cached": False,
        "reused_from": {
            "leg": str(base_dir),
            "cache_key": key96,
            "cache_grain_metrics_from": str(d94_row_p),
            "basis": "PRECOMMIT-capx-d99 §2: same config (key dbef1ecac9596c90 at "
            "the pinned HEAD), G-DRIFT all-INERT; 25/25 evolution ledgers and "
            "every trajectory cell byte-identical to D94 vre_short (asserted)",
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, indent=2))
    print(f"vre_short {MEAN_METRIC}={mean}; wrote {out}")
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
        # render_report hard-codes the legacy-bins bullet; the D99 rungs are
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
    """CLI entry point (``metrics`` in a shard; ``reuse`` / ``assemble`` in the parent)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("metrics")
    m.add_argument("--out-dir", type=Path, required=True)
    m.add_argument("--rung", choices=sorted(RUNG_OVERRIDE), required=True)
    u = sub.add_parser("reuse")
    u.add_argument("--base-dir", type=Path, required=True)
    u.add_argument("--d94-dir", type=Path, required=True)
    u.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("assemble")
    a.add_argument("--rows", type=Path, nargs="+", required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--elapsed-s", type=float, default=None)
    a.add_argument("--fleet-note", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "metrics":
        return cmd_metrics(args.out_dir, args.rung)
    if args.cmd == "reuse":
        return cmd_reuse(args.base_dir, args.d94_dir, args.out)
    return cmd_assemble(args.rows, args.out, args.elapsed_s, args.fleet_note)


if __name__ == "__main__":
    raise SystemExit(main())
