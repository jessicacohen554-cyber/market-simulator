"""SCN-WS4c — extract every number the FINDING cites from the solved arms.

Reads each arm's cached year results through the same seam the report uses
(``market_sim.results.cache`` + ``export._summarize_year``), and emits:

* the headline per-arm scalars (``emissions_mt``, ``unserved_mwh``,
  ``import_co2_mt_reported``, prices, ``clean_share``, ...);
* generation and CO2 by fuel, so the STOP gate's footprint check (S3) and the
  implied marginal rate (S2) are computable;
* the per-tranche import table (the leakage deliverable) from per-generator
  annual energy x ``import_tranche_ef``;
* the reserve-backstop build and its energy, matched on ``unit_id``.

Runs no LP. Every number is read from a committed-or-cached solve.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache
from market_sim.results.emissions import import_tranche_ef
from market_sim.results.export import _summarize_year

FOSSIL = {
    "gas_cc", "gas_ct", "gas_st", "gas_chp", "cc_chp", "coal", "oil",
    "gas_other", "other_fossil", "petroleum", "waste_coal",
}


def arm_key(root: Path, iso: str, case: str) -> str:
    """Return one arm's cache key, linking its bundle into the shared cache root.

    Each arm solves into its own ``--out-dir``, so its bundle sits at
    ``<out-dir>/<ISO>/<key>/`` while ``cache.CACHE_ROOT`` is the single
    ``results/`` root. The link makes the bundle readable through the same
    seam ``report_scenario_deltas.py`` uses, at a gitignored path
    (.gitignore section 7, ``results/<ISO>/``).
    """
    base = root / iso.lower() / case / iso.upper()
    keys = [p for p in base.iterdir() if p.is_dir() and (p / "config.yaml").exists()]
    if len(keys) != 1:
        raise SystemExit(f"{base}: expected 1 cache key, found {len(keys)}")
    link = Path(cache.CACHE_ROOT) / iso.upper() / keys[0].name
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        raise SystemExit(f"{link} exists and is not a symlink -- refusing")
    link.symlink_to(keys[0].resolve())
    return keys[0].name


def read_year(iso: str, key: str, year: int) -> dict:
    """Summarize one cached scenario-year plus the per-tranche/backstop grain."""
    result = cache.load_result(iso, key, year)
    context = cache.load_fleet_context(iso, key, year)
    config = ScenarioConfig.from_yaml(cache.get_config_path(iso, key, year))
    summary = _summarize_year(result, context, config)

    gen = np.asarray(result.dispatch, dtype=float).sum(axis=1)
    fuels = list(context.fuel_types)
    units = list(context.unit_ids)
    zones = list(context.zones)

    by_fuel_mwh: dict[str, float] = {}
    for g, f in enumerate(fuels):
        by_fuel_mwh[f] = by_fuel_mwh.get(f, 0.0) + float(gen[g])

    tranches = []
    for g, f in enumerate(fuels):
        if f != "import":
            continue
        ef = import_tranche_ef(units[g], zones[g])
        tranches.append(
            {
                "unit_id": units[g],
                "zone": zones[g],
                "ef_t_per_mwh": round(ef, 4),
                "twh": round(float(gen[g]) / 1e6, 4),
                "reported_mt": round(max(float(gen[g]), 0.0) * ef / 1e6, 4),
            }
        )

    fossil_mwh = sum(v for k, v in by_fuel_mwh.items() if k in FOSSIL)
    return {
        "year": year,
        "summary": {
            k: v
            for k, v in summary.items()
            if isinstance(v, (int, float, dict)) and not isinstance(v, bool)
        },
        "gen_by_fuel_twh": {k: round(v / 1e6, 4) for k, v in sorted(by_fuel_mwh.items())},
        "fossil_twh": round(fossil_mwh / 1e6, 4),
        "import_tranches": sorted(tranches, key=lambda t: -abs(t["twh"])),
    }


def main() -> None:
    """Emit the per-arm extraction as JSON for the FINDING tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--cases", nargs="+", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2026])
    ap.add_argument("--root", type=Path, default=Path("results/scn-ws4-probe"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    iso = args.iso.upper()
    out: dict = {"iso": iso, "arms": {}}
    for case in args.cases:
        key = arm_key(args.root, iso, case)
        out["arms"][case] = {
            "cache_key": key,
            "years": {str(y): read_year(iso, key, y) for y in args.years},
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
