"""nyiso-144 — is NYISO's C3c scarcity tail a LOCATIONAL or a SYSTEM-WIDE event?

nyiso-143 measured that 100 % of the MODEL's C3c tail hours are Long_Island,
produced by the Zone-K import bound, and that arming the published N-1-1 limit
removes the bound and the tail together. It named "the downstate scarcity
mechanism" as the successor. This probe asks the prior question — **what is the
REAL tail made of?** — before any mechanism is built, because a Zone-K-scoped
mechanism can only reproduce a Zone-K-scoped tail.

Three measurements, no solve, no LP, and only 2023-2025 (holdout freeze ACTIVE):

A. **Tail anatomy.** Take the actual C3c tail hours (RT hourly hub average above
   the rubric threshold, ``frontend/data/backcast/tail/actual_tail.json``) from
   ``actual_lmp_hourly_NYISO.parquet``, and read NYISO's OWN posted RT ancillary
   prices in exactly those hours (``data/raw/NYISO-AS/NYISO_as_rt_<year>.csv``,
   all 11 posted zones, full 8,760 h coverage). Decompose each zone's reserve
   price into the NYCA-WIDE component (the minimum across zones — the part every
   zone shares) and Long Island's LOCATIONAL adder (LONGIL minus that base). If
   the tail were a Zone-K separation the adder would dominate; if it is a
   control-area reserve shortage the base does.

B. **Which model families bind.** The keeper's committed
   ``hourly/reserve_family_<year>.parquet`` — the ONLY artifact in which a
   locational family's binding is observable — reduced to hours with a non-zero
   dual, shortfall hours, and the maximum dual, per family per year.

C. **Whether the online gate could bind.** The gated class-2 row is
   ``R[c,z] <= rho * sum_g P[g]``, so the published NYCA spinning family is inert
   whenever ``rho >= rho* = requirement / min_t sum P_eligible``. Rebuild
   ``sum P`` for the eligible set from the keeper's committed
   ``hourly/class_hourly_<year>.parquet`` — with and without the hydro union the
   keeper's ``nyiso_hydro_reserve_eligible`` adds — and report ``rho*`` plus the
   binding-hour count at each candidate ``rho``. This is nyiso-110's own
   inertness arithmetic, re-run at values other than the 1.0 fallback.

Writes ``results/calibration/_nyiso144_tail_anatomy.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/nyiso143_n11tsl_arm"
YEARS = (2023, 2024, 2025)

# Published requirement of the NYCA 10-minute SPINNING family (MW) and the
# candidate rho values measurement C reports binding counts at: the hard-coded
# fallback, and the two measured downstate statistics with their min-load
# sensitivities (data/raw/_processed-legacy/campd_online_reserve_rho_NYISO.csv).
NYCA_SPIN_REQ_MW: float = 655.0
RHO_CANDIDATES: tuple[float, ...] = (0.2011, 0.3014, 1.0, 1.1247, 1.2462)

# Dispatch classes making up the quick-start (10-minute-capable) eligible set —
# model/reserves/spec.QUICK_START_FUEL_TYPES {gas_ct, oil} as they appear in the
# class_hourly sidecar's `klass` column, plus the hydro union the keeper arms.
QUICK_CLASSES: tuple[str, ...] = ("CT_PEAKER", "CT_CHP", "oil")
HYDRO_CLASS: str = "hydro"

# Posted NYISO AS price zones. LONGIL is Zone K; the base is the minimum across
# all of them, which is the component carrying no locational scarcity.
LI_ZONE: str = "LONGIL"
NYC_ZONE: str = "N.Y.C."


def tail_anatomy() -> dict:
    """Return the NYCA-vs-locational decomposition inside the actual tail hours."""
    hub = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
    )
    thresholds = json.loads(
        (REPO / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )["thresholds"]
    threshold = float(thresholds["NYISO"])
    out: dict[str, dict] = {}
    for year in YEARS:
        series = hub[hub.year == year].set_index("hour")["rt"].sort_index()
        tail = series[series > threshold].index.to_numpy()
        prices = pd.read_csv(REPO / f"data/raw/NYISO-AS/NYISO_as_rt_{year}.csv")
        prices["Time Stamp"] = pd.to_datetime(prices["Time Stamp"])
        wide = (
            prices.sort_values("Time Stamp")
            .pivot_table(index="Time Stamp", columns="Name", values="spin_10")
            .reset_index(drop=True)
        )
        base = wide.min(axis=1)
        li = (wide[LI_ZONE] - base).clip(lower=0)
        nyc = (wide[NYC_ZONE] - base).clip(lower=0)
        idx = np.array([h for h in tail if h < len(wide)], dtype=int)
        out[str(year)] = {
            "threshold_usd": threshold,
            "tail_hours": int(tail.size),
            "tail_hours_scored": int(idx.size),
            "hub_max_usd": round(float(series.max()), 2),
            "in_tail": {
                "nyca_base_mean": round(float(base.iloc[idx].mean()), 2),
                "nyca_base_median": round(float(base.iloc[idx].median()), 2),
                "nyca_base_max": round(float(base.iloc[idx].max()), 2),
                "nyca_base_share_gt_50": round(float((base.iloc[idx] > 50).mean()), 4),
                "li_adder_mean": round(float(li.iloc[idx].mean()), 2),
                "li_adder_median": round(float(li.iloc[idx].median()), 2),
                "li_adder_max": round(float(li.iloc[idx].max()), 2),
                "li_adder_share_gt_50": round(float((li.iloc[idx] > 50).mean()), 4),
                "nyc_adder_mean": round(float(nyc.iloc[idx].mean()), 2),
            },
            "all_hours": {
                "nyca_base_mean": round(float(base.mean()), 3),
                "li_adder_mean": round(float(li.mean()), 3),
            },
        }
    return out


def family_binding() -> dict:
    """Return each reserve family's P1 binding record on the committed keeper."""
    out: dict[str, dict] = {}
    for year in YEARS:
        path = BUNDLE / f"hourly/reserve_family_{year}.parquet"
        df = pd.read_parquet(path)
        df = df[df["pass"] == "P1"]
        rows: dict[str, dict] = {}
        for family, grp in df.groupby("family"):
            dual = grp["dual"].abs()
            rows[str(family)] = {
                "requirement_mw": round(float(grp["requirement_mw"].max()), 1),
                "hours_dual_nonzero": int((dual > 1e-6).sum()),
                "max_dual_usd": round(float(dual.max()), 4),
                "hours_shortfall": int((grp["shortfall_mw"] > 1e-6).sum()),
                "max_shortfall_mw": round(float(grp["shortfall_mw"].max()), 2),
            }
        out[str(year)] = rows
    return out


def spin_gate_liveness() -> dict:
    """Return ``rho*`` and binding-hour counts for the NYCA spinning family.

    ``rho*`` is the multiplier at or above which the gated row can never bind
    (nyiso-110's own inertness arithmetic). Reported for the keeper's actual
    eligible set (quick-start UNIONED with hydro, which
    ``nyiso_hydro_reserve_eligible`` arms) and for quick-start alone, because
    hydro supplies the overwhelming majority of the eligible output and carries
    NO entry in ``fleet.RAMP10_FRAC_*`` — a coverage gap, not a measured zero.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        df = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
        df = df[df["pass"] == "P1"]
        wide = df.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).fillna(0.0)
        quick = wide[[c for c in QUICK_CLASSES if c in wide.columns]].sum(axis=1)
        variants = {
            "quick_plus_hydro_keeper": quick + wide.get(HYDRO_CLASS, 0.0),
            "quick_only": quick,
        }
        out[str(year)] = {
            name: {
                "min_sum_p_mw": round(float(s.min()), 1),
                "median_sum_p_mw": round(float(s.median()), 1),
                "rho_star_for_inertness": (
                    round(float(NYCA_SPIN_REQ_MW / s.min()), 4) if s.min() > 0 else None
                ),
                "binding_hours_by_rho": {
                    str(r): int(((r * s) < NYCA_SPIN_REQ_MW).sum())
                    for r in RHO_CANDIDATES
                },
            }
            for name, s in variants.items()
        }
    return out


def main() -> int:
    """Run all three measurements and write the probe artifact."""
    result = {
        "session": "nyiso-144",
        "bundle": BUNDLE.name,
        "years": list(YEARS),
        "nyca_spin_requirement_mw": NYCA_SPIN_REQ_MW,
        "A_tail_anatomy": tail_anatomy(),
        "B_family_binding": family_binding(),
        "C_spin_gate_liveness": spin_gate_liveness(),
    }
    out = REPO / "results/calibration/_nyiso144_tail_anatomy.json"
    out.write_text(json.dumps(result, indent=1) + "\n")
    for year in YEARS:
        a = result["A_tail_anatomy"][str(year)]
        c = result["C_spin_gate_liveness"][str(year)]["quick_plus_hydro_keeper"]
        print(
            f"{year}: {a['tail_hours']:>3} tail h | NYCA base mean "
            f"${a['in_tail']['nyca_base_mean']:>8.2f} "
            f"({a['in_tail']['nyca_base_share_gt_50']:.0%} > $50) | LI adder mean "
            f"${a['in_tail']['li_adder_mean']:>7.2f} | nyca_10min_spin rho* "
            f"{c['rho_star_for_inertness']}"
        )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
