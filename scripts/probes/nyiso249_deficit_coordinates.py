"""nyiso-249 — G-4: WHERE IS THE C3c DEFICIT, if it is not in the tight window?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Routing instrument, not a gate.

G-3 measured that only **7 of 153** missed hours across 2022-2025 fall inside
the P-27 book's registered TIGHT window (``gas_bin >= 2 AND load_bin >= 2`` on
nyiso-248's corrected daily coordinate), and that **95-100 %** of tight hours
carry no actual tail at all. So the window and the deficit are near-disjoint
hour sets, and the upper-tail offer-dispersion form -- whose magnitudes are
identified ONLY inside that window -- cannot be the C3c route.

This probe answers the question that leaves open, for the successor: **what
coordinate DOES select the missed hours?** It profiles them on the axes a
mechanism could plausibly key on, and reports each against the same axis
measured over all 8760 hours, so a concentration is visible as a ratio rather
than a raw count.

Axes: month; hour of day; net-load percentile (the book's own coordinate);
delivered-gas percentile (daily, the corrected coordinate); the model's own max
zonal price in that hour; and which zone carried the model's max.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_deficit_coordinates.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso249_deficit_coordinates.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    from scripts.data.derive_nyiso_offer_surface import YEARS, net_load_by_year
    from scripts.probes.nyiso242_tail_reachability import BUNDLE, missed_mask
    from scripts.probes.nyiso248_book_daily_regrain import daily_gas

    years = args.year or list(YEARS)
    nl = net_load_by_year()
    result: dict = {"gate": "G-4", "session": "nyiso-249", "years": {}}

    for y in years:
        missed, month = missed_mask(y)
        n = len(missed)
        gas = daily_gas(y)[:n]
        load = np.asarray(nl[y], float)[:n]
        hod = np.arange(n) % 24

        # Percentile RANK of each hour within its own year, both coordinates.
        gas_pct = np.searchsorted(np.sort(gas), gas) / n
        load_pct = np.searchsorted(np.sort(load), load) / n

        sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
        sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"] != "NYISO_external")]
        piv = sysf.pivot_table(index="hour", columns="zone", values="price").sort_index()
        piv = piv.iloc[:n]
        mmax = piv.max(axis=1).to_numpy()
        argz = piv.idxmax(axis=1).to_numpy()

        m = missed
        zc = pd.Series(argz[m]).value_counts().to_dict() if m.any() else {}
        result["years"][str(y)] = {
            "n_missed": int(m.sum()),
            "missed_month_counts": {
                str(k): int(v)
                for k, v in sorted(pd.Series(month[m]).value_counts().items())
            },
            "missed_hour_of_day_counts": {
                str(k): int(v)
                for k, v in sorted(pd.Series(hod[m]).value_counts().items())
            },
            "gas_pct": {
                "missed_p50": round(float(np.median(gas_pct[m])), 4),
                "missed_mean": round(float(gas_pct[m].mean()), 4),
                "missed_share_above_p90": round(float((gas_pct[m] >= 0.90).mean()), 4),
            },
            "load_pct": {
                "missed_p50": round(float(np.median(load_pct[m])), 4),
                "missed_mean": round(float(load_pct[m].mean()), 4),
                "missed_share_above_p90": round(float((load_pct[m] >= 0.90).mean()), 4),
            },
            "model_max_price_in_missed": {
                "p50": round(float(np.median(mmax[m])), 2),
                "p90": round(float(np.quantile(mmax[m], 0.90)), 2),
                "max": round(float(mmax[m].max()), 2),
            },
            "model_max_zone_counts": {str(k): int(v) for k, v in zc.items()},
        }
        r = result["years"][str(y)]
        print(
            f"\n{y}: missed={r['n_missed']}  "
            f"gas_pct p50={r['gas_pct']['missed_p50']:.2f} "
            f"(share>=p90 {r['gas_pct']['missed_share_above_p90']:.1%})  "
            f"load_pct p50={r['load_pct']['missed_p50']:.2f} "
            f"(share>=p90 {r['load_pct']['missed_share_above_p90']:.1%})"
        )
        print(f"   months {r['missed_month_counts']}")
        print(f"   model max price in those hours: {r['model_max_price_in_missed']}")
        print(f"   zone carrying model max: {r['model_max_zone_counts']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
