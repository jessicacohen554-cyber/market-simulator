"""Restate the nyiso-88 heat-rate bias on the basis the model actually uses.

``docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md`` §4 measured the NYISO
CT_PEAKER fleet's model heat rate against a CAMPD **gross**-basis loaded rate
and reported a 9.3–15.7 % overstatement worth +$6.48/+$6.70/+$7.34 per MWh.
That comparison mixes bases: CAMPD meters GROSS load, while eGRID's heat rate
(the model's), the LP's dispatched MW, and the benchmark's own "actual" (built
as ``gross × parasitic_factor`` in ``run_calibration_full._campd_hourly_frame``)
are all NET. The station-service fraction the comparison drops is 1 % for a bare
CT but 10.2 % at Bayonne Energy Center — the largest plant in the class and 41 %
of its energy.

This probe re-runs §4 on both bases so the size of that correction is on the
record, and adds the thing the aggregate hides: the per-plant errors do not
share a sign, so the input fix is a **merit-order reordering within the class**,
not a uniform discount. It also reports the capacity-weighted view alongside the
generation-weighted one, because those move in OPPOSITE directions here and only
the pair states the effect honestly.

Everything is read from committed artifacts. No LP is solved, no measured
outcome enters any model input — scoring-side characterisation only.

Usage::

    python scripts/probes/nyiso89_ct_heat_rate_basis.py --iso NYISO
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402

from scripts.probes.nyiso88_peaker_economics import (  # noqa: E402
    downstate_ct_gas_hourly,
)


def artifact(iso: str) -> pd.DataFrame:
    """Return the committed measured-CT heat-rate table for *iso*."""
    path = PROCESSED_DIR / f"campd_ct_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        raise SystemExit(
            f"{path} not built — run scripts/data/derive_campd_ct_heat_rates.py"
        )
    return pd.read_csv(path)


def delivered_gas(year: int) -> float:
    """Return the keeper's mean downstate-CT delivered gas ($/MMBtu) for *year*.

    The keeper prices downstate CTs on the curated per-zone daily index
    (``nyiso_downstate_ct_gas_daily``); the superseded statewide firm city-gate
    stand-in runs $1.5–2.3/MMBtu dearer and would inflate every $/MWh figure
    below (the correction recorded in the nyiso-88 finding §1).
    """
    by_zone = downstate_ct_gas_hourly(year) or {}
    if not by_zone:
        return float("nan")
    return float(np.mean([np.mean(v) for v in by_zone.values()]))


def main(argv: list[str] | None = None) -> int:
    """Print the basis restatement and the within-class reordering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="NYISO")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    table = artifact(args.iso)
    ok = table[table["flag"] == "ok"].copy()
    ok = ok[np.isfinite(ok["model_heat_rate_egrid"])]

    w_cap = ok["class_capacity_mw"].to_numpy(dtype=float)
    w_gen = ok["gross_mwh"].to_numpy(dtype=float)
    model = ok["model_heat_rate_egrid"].to_numpy(dtype=float)
    net = ok["heat_rate"].to_numpy(dtype=float)
    gross = ok["heat_rate_gross"].to_numpy(dtype=float)

    print(f"--- {args.iso} CT_PEAKER: heat-rate basis restatement ---")
    print(f"{'weighting':>12} {'model':>8} {'gross':>8} {'net':>8} {'model/net':>10}")
    rows = {}
    for label, w in (("capacity", w_cap), ("generation", w_gen)):
        m, g, n = (np.average(x, weights=w) for x in (model, gross, net))
        rows[label] = {"model": m, "gross": g, "net": n, "ratio": m / n}
        print(f"{label:>12} {m:>8.3f} {g:>8.3f} {n:>8.3f} {m / n:>10.3f}")

    print()
    print("$/MWh SRMC bias (model − measured_net) x the keeper's delivered gas:")
    gas_rows = {}
    for year in args.years:
        gas = delivered_gas(year)
        gas_rows[year] = {
            "delivered_gas": gas,
            "bias_capacity_wtd": (rows["capacity"]["model"] - rows["capacity"]["net"])
            * gas,
            "bias_generation_wtd": (
                rows["generation"]["model"] - rows["generation"]["net"]
            )
            * gas,
            "bias_gross_basis_generation_wtd": (
                rows["generation"]["model"] - rows["generation"]["gross"]
            )
            * gas,
        }
        r = gas_rows[year]
        print(
            f"  {year}  gas ${gas:>5.2f}/MMBtu   "
            f"cap-wtd {r['bias_capacity_wtd']:>+7.2f}   "
            f"gen-wtd {r['bias_generation_wtd']:>+7.2f}   "
            f"(gen-wtd on the GROSS basis nyiso-88 used: "
            f"{r['bias_gross_basis_generation_wtd']:>+6.2f})"
        )

    print()
    print("Within-class reordering — the aggregate hides this:")
    ok["delta"] = ok["heat_rate"] - ok["model_heat_rate_egrid"]
    cheaper = ok[ok["delta"] < 0]
    dearer = ok[ok["delta"] > 0]
    print(
        f"  {len(cheaper)} plants get CHEAPER ({cheaper['class_capacity_mw'].sum():.0f} MW), "
        f"{len(dearer)} get DEARER ({dearer['class_capacity_mw'].sum():.0f} MW)"
    )
    show = ok.sort_values("class_capacity_mw", ascending=False)
    print(
        f"  {'plant':<32} {'MW':>7} {'model':>7} {'net':>7} {'delta':>7} {'$/MWh@2025':>11}"
    )
    gas25 = gas_rows.get(max(args.years), {}).get("delivered_gas", float("nan"))
    for r in show.itertuples(index=False):
        print(
            f"  {str(r.plant_name)[:32]:<32} {r.class_capacity_mw:>7.1f} "
            f"{r.model_heat_rate_egrid:>7.2f} {r.heat_rate:>7.2f} "
            f"{r.heat_rate - r.model_heat_rate_egrid:>+7.2f} "
            f"{(r.model_heat_rate_egrid - r.heat_rate) * gas25:>+11.2f}"
        )

    if args.json_out:
        args.json_out.write_text(
            json.dumps({"weighted": rows, "by_year": gas_rows}, indent=2)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
