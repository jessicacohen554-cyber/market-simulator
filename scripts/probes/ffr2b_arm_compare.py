#!/usr/bin/env python
"""FFR-2B: extract the D-1/D-2 comparison rows from a set of probe bundles.

Reads each leg's evolution ledgers and emits, per leg and per solve year, the
quantities the owner's D-1/D-2 boxes are graded on:

* **economic-channel retirements by fuel** (the T-R10 no-inversion inputs and
  the retirement recall/false-retire feedstock);
* **I6** — ``economic MW / prior thermal MW``, the single-year econ-retirement
  fraction whose 20 % cap FH-1's §3.3 gate failed on (the §4 FH-4 cross-read);
* **BLK-10** — reserve-margin backstop fired MW, by fired row;
* **entry by tech and source**, so a damper's effect is separable into
  economic entry vs backstop;
* the ``pipeline_events`` decision/execution split where the pipeline rule ran.

Findings-only: reads committed bundles, computes nothing tunable, changes no
default (rules 1/11/24).

Usage::

    python scripts/probes/ffr2b_arm_compare.py \\
        --leg legacy=results/hindcast/miso-2021-2025-cmc-legacy-ffr2b \\
        --leg pipeline=results/hindcast/miso-2021-2025-cmc-pipeline-ffr2b \\
        --out results/hindcast/ffr2b-miso-compare.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from scripts.check_forecast_invariants import THERMAL_FUELS  # noqa: E402

# The I6 cap the checker grades against (check_forecast_invariants.T). Imported
# rather than restated so this probe can never quote a looser bound (rule 22's
# "bands never widened" discipline applied to a diagnostic).
from scripts.check_forecast_invariants import T as _INVARIANT_THRESHOLDS  # noqa: E402

I6_CAP = _INVARIANT_THRESHOLDS.econ_retire_frac_cap


def _bundle_dir(leg_dir: Path) -> Path:
    """Resolve the solved bundle under a harness out-dir.

    ``run_capacity_hindcast`` writes ``<out-dir>/<ISO>/<cache_key>/``; the
    full-horizon runner writes ``<out-dir>/<ISO>/<cache_key>/`` too (its cache
    root is redirected). Prefer the meta's recorded bundle when present.
    """
    meta = leg_dir / "meta.json"
    if meta.exists():
        recorded = json.loads(meta.read_text()).get("bundle")
        if recorded and Path(recorded).exists():
            return Path(recorded)
    summary = leg_dir / "full_horizon_summary.json"
    if summary.exists():
        recorded = json.loads(summary.read_text()).get("run_dir")
        if recorded and Path(recorded).exists():
            return Path(recorded)
    # Fall back to the single <ISO>/<key> directory holding evolution ledgers.
    for candidate in sorted(leg_dir.rglob("evolution_*.json")):
        return candidate.parent
    raise SystemExit(f"no solved bundle found under {leg_dir}")


def _thermal_mw(by_fuel: dict) -> float:
    return float(sum(v for f, v in by_fuel.items() if f in THERMAL_FUELS))


def _by(rows: list, key: str, mw_key: str = "mw") -> dict:
    out: dict[str, float] = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0.0) + float(r.get(mw_key, 0.0))
    return {k: round(v, 3) for k, v in sorted(out.items())}


def summarize_leg(name: str, leg_dir: Path) -> dict:
    """Per-year rows + cumulative totals for one probe leg."""
    bundle = _bundle_dir(leg_dir)
    ledgers = load_ledgers_for_run(bundle)
    years: list[dict] = []
    cum_econ_by_fuel: dict[str, float] = {}
    cum_backstop = 0.0
    for year in sorted(ledgers):
        led = ledgers[year]
        if led.get("bridge"):
            continue
        rets = led.get("retirements", [])
        econ = [r for r in rets if r.get("reason") == "economic"]
        econ_mw = float(sum(float(r.get("mw", 0.0)) for r in econ))
        prior_thermal = _thermal_mw(led.get("fleet_by_fuel_before", {}) or {})
        adds = led.get("thermal_additions", [])
        backstop = [a for a in adds if "backstop" in str(a.get("source", ""))]
        backstop_mw = float(sum(float(a.get("mw", 0.0)) for a in backstop))
        cum_backstop += backstop_mw
        for f, mw in _by(econ, "fuel").items():
            cum_econ_by_fuel[f] = round(cum_econ_by_fuel.get(f, 0.0) + mw, 3)
        i6 = (econ_mw / prior_thermal) if prior_thermal > 0 else None
        years.append(
            {
                "year": year,
                "prior_thermal_mw": round(prior_thermal, 1),
                "econ_retire_mw": round(econ_mw, 3),
                "i6_frac": round(i6, 5) if i6 is not None else None,
                "i6_verdict": (
                    None if i6 is None else ("FAIL" if i6 > I6_CAP else "PASS")
                ),
                "econ_by_fuel_mw": _by(econ, "fuel"),
                "retire_by_reason_mw": _by(rets, "reason"),
                "thermal_adds_by_fuel_mw": _by(adds, "fuel"),
                "thermal_adds_by_source_mw": _by(adds, "source"),
                "backstop_mw": round(backstop_mw, 3),
                "backstop_rows": [
                    {"source": a.get("source"), "mw": round(float(a.get("mw", 0.0)), 3)}
                    for a in backstop
                ],
                "renewable_adds_mw": _by(led.get("renewable_additions", []), "tech"),
                "storage_adds_mw": round(
                    float(
                        sum(
                            float(a.get("mw", 0.0))
                            for a in led.get("storage_additions", [])
                        )
                    ),
                    3,
                ),
                "pipeline_events": _by(led.get("pipeline_events", []), "event"),
                "reserve_margin": led.get("reserve_margin"),
            }
        )
    return {
        "leg": name,
        "bundle": str(bundle),
        "meta": (
            json.loads((leg_dir / "meta.json").read_text())
            if (leg_dir / "meta.json").exists()
            else None
        ),
        "years": years,
        "cumulative": {
            "econ_by_fuel_mw": cum_econ_by_fuel,
            "econ_total_mw": round(sum(cum_econ_by_fuel.values()), 3),
            "backstop_total_mw": round(cum_backstop, 3),
        },
        "i6_worst": max(
            (y["i6_frac"] for y in years if y["i6_frac"] is not None), default=None
        ),
        "i6_any_fail": any(y["i6_verdict"] == "FAIL" for y in years),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--leg",
        action="append",
        required=True,
        metavar="NAME=DIR",
        help="Probe leg as name=out-dir; repeat once per arm.",
    )
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    legs = []
    for spec in args.leg:
        name, _, path = spec.partition("=")
        if not path:
            raise SystemExit(f"--leg expects NAME=DIR, got {spec!r}")
        legs.append(summarize_leg(name, Path(path)))

    report = {"i6_cap": I6_CAP, "legs": legs}
    text = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
        print(f"[ffr2b] wrote {args.out}")

    for leg in legs:
        print(f"\n===== {leg['leg']} =====")
        print(f"  bundle {leg['bundle']}")
        print(
            f"  cumulative economic exits: {leg['cumulative']['econ_total_mw']:.1f} MW "
            f"{leg['cumulative']['econ_by_fuel_mw']}"
        )
        print(f"  backstop fired total: {leg['cumulative']['backstop_total_mw']:.1f} MW")
        print(f"  I6 worst: {leg['i6_worst']} (cap {I6_CAP}) "
              f"-> {'FAIL' if leg['i6_any_fail'] else 'PASS'}")
        for y in leg["years"]:
            print(
                f"    {y['year']}  prior_thermal={y['prior_thermal_mw']:>9.1f}  "
                f"econ={y['econ_retire_mw']:>9.1f}  I6={y['i6_frac']}  "
                f"{y['i6_verdict']}  econ_by_fuel={y['econ_by_fuel_mw']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
