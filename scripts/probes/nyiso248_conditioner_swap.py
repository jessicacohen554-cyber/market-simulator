"""nyiso-248 phase 0 — gate G-4: the successor's gas coordinate is a MONTH selector.

ZERO LP (rule 32 ``[R-SHARD]`` (a)).

``derive_nyiso_offer_level_dispersion.state_windows`` bins its gas coordinate on
``gas_series_by_year()`` = the keeper's ``_gas_series``, which G-1/G-3 measured
to be a **12-value monthly step**. So ``gas_bin >= 2`` selects "an hour in one of
the year's ~1.2 dearest MONTHS", not "an hour on a dear DAY" — and the reported
``tight_winter_share`` of 98-100 % is then near-tautological rather than a
finding.

The market's own gas scarcity is a DAY phenomenon: the measured Transco Z6 NY
daily series carries a within-month p95/p50 of 1.34-2.69 (G-2), and the array
the LP actually prices gas on carries 90-120 % of that swing.

This gate asks the one question that decides whether nyiso-245/246/247's
conditional measurements survive the correction:

    How much of the TIGHT window moves when the gas coordinate is binned on the
    DAILY series instead of the monthly step?

Two daily candidates are reported, both drop-in replacements for the same
coordinate and neither introducing a parameter:

* ``hub_daily``  — ``iso_hub_daily_gas_prices(cfg, year)``, i.e. exactly what
  ``_hub_overlay_series`` would return if it honoured ``gas_hub_basis_daily``
  the way ``apply_hub_basis_overlay`` already does.
* ``fleet_daily`` — the capacity-weighted mean of the keeper's own per-unit
  ``fuel_prices`` gas rows: the delivered price the merit order actually sees.

Everything else is held at ``state_windows``' registered construction: the same
``NETLOAD_PCTS`` ladder, the same within-year percentile basis, the same net
load, the same ``tight = gas_bin >= 2 AND load_bin >= 2``.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso248_conditioner_swap.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT = REPO / "results" / "calibration" / "_nyiso248_conditioner_swap.json"
YEARS = (2022, 2023, 2024, 2025)
HOURS = 8760
NETLOAD_PCTS = (0.80, 0.90, 0.97)
GAS_CLASS_TOKENS = ("CC", "CT", "ST_GAS")


def _bins(x: np.ndarray) -> np.ndarray:
    """The registered within-year percentile ladder, unchanged."""
    return np.searchsorted(np.quantile(x, NETLOAD_PCTS), x, side="right")


def _fleet_daily(year: int) -> np.ndarray:
    """Capacity-weighted delivered gas across the keeper's own gas rows."""
    z = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    fp = np.asarray(z["fuel_prices"], dtype=float)
    groups = np.array([str(g) for g in z["plant_group"]])
    pmax = np.asarray(z["pmax"], dtype=float)
    sel = np.array(
        [any(t in g.upper() for t in GAS_CLASS_TOKENS) for g in groups], dtype=bool
    )
    w = pmax[sel]
    return (fp[sel, :] * w[:, None]).sum(axis=0) / w.sum()


def _hub_daily(year: int) -> np.ndarray | None:
    """What ``_hub_overlay_series`` would return if it honoured the daily gate."""
    from market_sim.data.fuel.hubs import iso_hub_daily_gas_prices

    from scripts.probes.nyiso242_tail_reachability import fleet_state

    st = fleet_state(year)
    cfg = st.get("config")
    d = iso_hub_daily_gas_prices(cfg, year)
    if d is None:
        return None
    d = np.asarray(d, dtype=float)
    # Months with no basis row stay NaN; fall back to the monthly series there,
    # exactly as apply_hub_basis_overlay's `covered` mask does.
    base = np.load(CACHE / f"gas_{year}.npy").astype(float)
    return np.where(np.isnan(d), base, d)


def run_year(year: int, hub: np.ndarray | None) -> dict:
    from scripts.data.derive_nyiso_offer_level_dispersion import net_load_by_year

    nl = net_load_by_year()[year]
    monthly = np.load(CACHE / f"gas_{year}.npy").astype(float)
    lb = _bins(nl)

    month = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h").month.to_numpy()
    cands: dict[str, np.ndarray] = {"monthly_step": monthly, "fleet_daily": _fleet_daily(year)}
    if hub is not None:
        cands["hub_daily"] = hub

    rec: dict = {}
    sets: dict[str, np.ndarray] = {}
    for name, g in cands.items():
        gb = _bins(g)
        tight = (gb >= 2) & (lb >= 2)
        ordinary = (gb == 0) & (lb == 0)
        sets[name] = tight
        mc = np.bincount(month[tight], minlength=13)[1:]
        rec[name] = {
            "gas_distinct": int(np.unique(np.round(g, 6)).size),
            "tight_hours": int(tight.sum()),
            "ordinary_hours": int(ordinary.sum()),
            "tight_winter_share": round(
                float(mc[[0, 1, 11]].sum() / max(1, tight.sum())), 4
            ),
            "tight_distinct_days": int(
                np.unique((np.nonzero(tight)[0] // 24)).size
            ),
            "tight_distinct_months": int(np.unique(month[tight]).size),
        }

    base = sets["monthly_step"]
    for name, s in sets.items():
        if name == "monthly_step":
            continue
        inter = int((base & s).sum())
        union = int((base | s).sum())
        rec[name]["jaccard_vs_monthly"] = round(inter / union, 4) if union else 0.0
        rec[name]["retained_share_of_monthly_tight"] = (
            round(inter / int(base.sum()), 4) if base.sum() else 0.0
        )
        rec[name]["new_hours_not_in_monthly_tight"] = int((s & ~base).sum())
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()

    result = {"gate": "G-4", "ladder": list(NETLOAD_PCTS), "years": {}}
    for y in args.year:
        hub = _hub_daily(y)
        r = run_year(y, hub)
        result["years"][str(y)] = r
        print(f"\n================ {y} ================")
        hdr = (
            f"  {'gas coordinate':<16} {'distinct':>9} {'tight h':>8} "
            f"{'days':>6} {'months':>7} {'winter%':>8} {'Jaccard':>8} {'kept':>7}"
        )
        print(hdr)
        for name, s in r.items():
            j = s.get("jaccard_vs_monthly", "")
            k = s.get("retained_share_of_monthly_tight", "")
            js = f"{j:>8.4f}" if j != "" else f"{'-':>8}"
            ks = f"{k:>7.3f}" if k != "" else f"{'-':>7}"
            print(
                f"  {name:<16} {s['gas_distinct']:>9} {s['tight_hours']:>8} "
                f"{s['tight_distinct_days']:>6} {s['tight_distinct_months']:>7} "
                f"{s['tight_winter_share']*100:>7.1f}% {js} {ks}"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
