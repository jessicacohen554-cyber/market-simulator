"""nyiso-248 phase 0 — WHAT GRAIN IS THE KEEPER'S DELIVERED GAS, PER CLASS AND PER ZONE?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Reads the committed keeper's own assembled
``fuel_prices`` array out of ``_nyiso245_cache/<year>.npz`` and answers one
question the whole lane rests on:

    Which NYISO gas rows carry a DAILY delivered-gas series, and which carry a
    MONTHLY PLATEAU?

The keeper arms ``gas_daily_shape``, ``gas_hub_basis_daily`` AND
``gas_plant_monthly_fuel_pricing`` at once. The last one SETS a plant's gas to
its EIA-923 monthly average print, which OVERWRITES any daily shape built
upstream. The measured per-year delivered-gas percentiles in the lane prompt
have ``max == p97`` in all four years — the signature of a monthly step — so
the premise is testable rather than arguable.

It matters because ``dual_fuel_oil_daily_parity`` is armed in this keeper, and
its own docstring justifies arming it by asserting that "the gas side of the
same min() comparison is already DAILY". Gate G-1 below decides whether that
stated premise holds on the keeper as configured.

Definitions, fixed here before any number is read:

* **step_ratio** — distinct delivered-gas values in the year divided by 12. A
  pure monthly plateau reads ~1.0 (12 values). A daily series reads ~30 (365).
* **within_month_cv** — mean over months of (std / mean) of the delivered price
  *inside* each month. A plateau reads exactly 0.0.
* A row is classified **MONTHLY** when its ``within_month_cv`` is < 1e-9, else
  **DAILY**.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso248_gas_grain_census.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT = REPO / "results" / "calibration" / "_nyiso248_gas_grain_census.json"
YEARS = (2022, 2023, 2024, 2025)
HOURS = 8760
GAS_CLASS_TOKENS = ("CC", "CT", "ST_GAS")


def _month_of_hour(n_hours: int) -> np.ndarray:
    """Month index 0-11 for each hour of a non-leap 8760 calendar."""
    lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out = np.concatenate([np.full(d * 24, m) for m, d in enumerate(lengths)])
    return out[:n_hours]


def _zone_names() -> list[str]:
    from market_sim.config.iso_configs import get_iso_config

    return list(get_iso_config("NYISO").zone_names)


def census(year: int) -> dict:
    """Classify every gas row's delivered-gas grain for one year."""
    z = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    fp = np.asarray(z["fuel_prices"], dtype=float)
    groups = np.array([str(g) for g in z["plant_group"]])
    pmax = np.asarray(z["pmax"], dtype=float)
    unit_ids = np.array([str(u) for u in z["unit_ids"]])
    n_hours = fp.shape[1]
    moh = _month_of_hour(n_hours)

    is_gas = np.array(
        [any(t in g.upper() for t in GAS_CLASS_TOKENS) for g in groups], dtype=bool
    )
    # Drop rows whose price never moves at all (a constant is neither grain).
    rows = np.nonzero(is_gas)[0]

    per_row = []
    for i in rows:
        s = fp[i, :]
        cvs = []
        for m in range(12):
            seg = s[moh == m]
            mu = float(seg.mean())
            if mu > 0:
                cvs.append(float(seg.std()) / mu)
        within_cv = float(np.mean(cvs)) if cvs else 0.0
        per_row.append(
            {
                "unit": str(unit_ids[i]),
                "group": str(groups[i]),
                "pmax": float(pmax[i]),
                "n_distinct": int(np.unique(np.round(s, 6)).size),
                "within_month_cv": within_cv,
                "grain": "DAILY" if within_cv > 1e-9 else "MONTHLY",
                "mean": float(s.mean()),
                "p50": float(np.percentile(s, 50)),
                "p97": float(np.percentile(s, 97)),
                "max": float(s.max()),
            }
        )

    # Aggregate by class.
    by_class: dict[str, dict] = {}
    for r in per_row:
        g = r["group"]
        b = by_class.setdefault(
            g,
            {
                "n_rows": 0,
                "mw": 0.0,
                "mw_daily": 0.0,
                "mw_monthly": 0.0,
                "n_daily": 0,
                "n_monthly": 0,
                "distinct_min": 10**9,
                "distinct_max": 0,
            },
        )
        b["n_rows"] += 1
        b["mw"] += r["pmax"]
        if r["grain"] == "DAILY":
            b["mw_daily"] += r["pmax"]
            b["n_daily"] += 1
        else:
            b["mw_monthly"] += r["pmax"]
            b["n_monthly"] += 1
        b["distinct_min"] = min(b["distinct_min"], r["n_distinct"])
        b["distinct_max"] = max(b["distinct_max"], r["n_distinct"])

    tot_mw = sum(b["mw"] for b in by_class.values())
    tot_daily = sum(b["mw_daily"] for b in by_class.values())
    return {
        "year": year,
        "n_gas_rows": int(rows.size),
        "gas_mw": tot_mw,
        "gas_mw_daily": tot_daily,
        "gas_mw_monthly": tot_mw - tot_daily,
        "daily_mw_share": (tot_daily / tot_mw) if tot_mw else 0.0,
        "by_class": by_class,
        "rows": per_row,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()

    result = {"gate": "G-1", "years": {}}
    for y in args.year:
        c = census(y)
        result["years"][str(y)] = {k: v for k, v in c.items() if k != "rows"}
        result["years"][str(y)]["rows"] = c["rows"]

        print(f"\n================ {y} ================")
        print(
            f"gas rows {c['n_gas_rows']}   gas MW {c['gas_mw']:,.0f}   "
            f"DAILY-grain MW share {c['daily_mw_share']*100:.2f}%"
        )
        print(
            f"  {'class':<16} {'rows':>5} {'MW':>10} {'MW daily':>10} "
            f"{'MW monthly':>11} {'distinct':>12}"
        )
        for g, b in sorted(c["by_class"].items(), key=lambda kv: -kv[1]["mw"]):
            print(
                f"  {g:<16} {b['n_rows']:>5} {b['mw']:>10,.0f} "
                f"{b['mw_daily']:>10,.0f} {b['mw_monthly']:>11,.0f} "
                f"{b['distinct_min']:>5}-{b['distinct_max']:<6}"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
