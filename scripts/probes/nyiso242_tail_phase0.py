"""nyiso-242 phase 0 — WHERE the missing 2022 RT scarcity hours are, and what the model does in them.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Reads only committed artifacts:

* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` — the hourly
  RT hub series ``derive_actual_tail.py`` counts the C3c benchmark from.
* the designated keeper's ``hourly/system_<yr>.parquet`` (per-zone LP dual,
  slack, dump, demand, reserve_price) and ``hourly/reserve_family_<yr>.parquet``
  (the ONLY artifact in which a locational reserve family's binding is
  observable — ``system.reserve_price`` is the cross-family SUM broadcast
  identically to every zone).

The question it answers, and nothing beyond it: of the actual RT hours above
the ISO's $300 C3c threshold, which does the model miss, WHEN do they sit, and
what is the LP doing in them — is a reserve family short, is load being shed,
or is the energy balance simply clearing on a cheap marginal unit?

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_tail_phase0.py [--years 2022 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
ACTUAL = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
#: C3c gate threshold for NYISO — mirrors calibration_verdict.TAIL_THRESHOLD
#: and derive_actual_tail.TAIL_THRESHOLD, which the rubric requires to agree.
THRESHOLD = 300.0


def load_actual(year: int) -> pd.Series:
    """Hourly actual RT hub price for ``year``, indexed by hour-of-year."""
    df = pd.read_parquet(ACTUAL)
    df = df[df["year"] == year]
    return df.set_index("hour")["rt"].sort_index()


def load_model(year: int) -> pd.DataFrame:
    """Per-hour model tail view: max zonal dual, and the zone that carries it.

    The C3c model count is the number of hours the LP's **max zonal dual**
    exceeds the threshold, so the max — not a load-weighted mean — is the
    quantity to compare.
    """
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    g = sysf.groupby("hour")
    idx = g["price"].idxmax()
    out = pd.DataFrame(
        {
            "max_dual": g["price"].max(),
            "max_zone": sysf.loc[idx, "zone"].to_numpy(),
            "lw_price": g.apply(
                lambda d: float((d["price"] * d["demand"]).sum() / d["demand"].sum()),
                include_groups=False,
            ),
            "slack_mwh": g["slack"].sum(),
            "dump_mwh": g["dump"].sum(),
            "demand_mw": g["demand"].sum(),
            "reserve_price": g["reserve_price"].max(),
        }
    )
    return out.sort_index()


def load_reserve(year: int) -> pd.DataFrame:
    """Per-hour reserve-family shortfall and the dual each family carries."""
    rf = pd.read_parquet(BUNDLE / "hourly" / f"reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"]
    short = rf[rf["shortfall_mw"] > 1e-6]
    per_hour = rf.groupby("hour").agg(
        n_short=("shortfall_mw", lambda s: int((s > 1e-6).sum())),
        short_mw=("shortfall_mw", "sum"),
        max_family_dual=("dual", "max"),
    )
    by_family = short.groupby("family").agg(
        hours=("hour", "nunique"),
        short_mw=("shortfall_mw", "sum"),
        max_dual=("dual", "max"),
    )
    return per_hour.sort_index(), by_family


def run_year(year: int) -> dict:
    actual = load_actual(year)
    model = load_model(year)
    resv, by_family = load_reserve(year)
    df = model.join(resv, how="left").join(actual.rename("actual_rt"), how="left")

    a_hot = df["actual_rt"] > THRESHOLD
    m_hot = df["max_dual"] > THRESHOLD
    missed = df[a_hot & ~m_hot]
    both = df[a_hot & m_hot]
    invented = df[~a_hot & m_hot]

    ts = pd.date_range(f"{year}-01-01", periods=len(df), freq="h")
    month = pd.Series(ts.month, index=df.index)
    hod = pd.Series(ts.hour, index=df.index)

    rec: dict = {
        "year": year,
        "threshold": THRESHOLD,
        "actual_tail_hours": int(a_hot.sum()),
        "model_tail_hours": int(m_hot.sum()),
        "hit": int(len(both)),
        "missed": int(len(missed)),
        "invented": int(len(invented)),
    }

    if len(missed):
        rec["missed_by_month"] = (
            month[missed.index].value_counts().sort_index().to_dict()
        )
        rec["missed_by_hour_of_day"] = (
            hod[missed.index].value_counts().sort_index().to_dict()
        )
        rec["missed_actual_price"] = {
            "min": float(missed["actual_rt"].min()),
            "median": float(missed["actual_rt"].median()),
            "max": float(missed["actual_rt"].max()),
            "mean": float(missed["actual_rt"].mean()),
        }
        rec["missed_model_price"] = {
            "max_dual_median": float(missed["max_dual"].median()),
            "max_dual_max": float(missed["max_dual"].max()),
            "lw_median": float(missed["lw_price"].median()),
        }
        rec["missed_max_zone"] = missed["max_zone"].value_counts().to_dict()
        rec["missed_model_state"] = {
            "hours_any_slack": int((missed["slack_mwh"] > 1e-6).sum()),
            "hours_any_dump": int((missed["dump_mwh"] > 1e-6).sum()),
            "hours_any_reserve_shortfall": int((missed["n_short"] > 0).sum()),
            "hours_reserve_price_gt0": int((missed["reserve_price"] > 1e-6).sum()),
            "reserve_price_median": float(missed["reserve_price"].median()),
            "reserve_price_max": float(missed["reserve_price"].max()),
        }
        # How far below the gate does the model sit in the hours it misses? A
        # near-miss distribution says "the tail is compressed"; a far-miss one
        # says "there is no scarcity mechanism firing here at all".
        rec["missed_model_dual_bands"] = {
            "<=50": int((missed["max_dual"] <= 50).sum()),
            "50-100": int(((missed["max_dual"] > 50) & (missed["max_dual"] <= 100)).sum()),
            "100-200": int(((missed["max_dual"] > 100) & (missed["max_dual"] <= 200)).sum()),
            "200-300": int(((missed["max_dual"] > 200) & (missed["max_dual"] <= 300)).sum()),
        }
        # The load the LP is serving in those hours, against the year's own
        # peak: are these genuinely the tight hours, or ordinary ones the
        # actual market priced high for a reason the model has no state for?
        peak = float(df["demand_mw"].max())
        rec["missed_load"] = {
            "year_peak_mw": peak,
            "median_load_pct_of_peak": float(
                100.0 * missed["demand_mw"].median() / peak
            ),
            "hours_above_90pct_peak": int((missed["demand_mw"] > 0.90 * peak).sum()),
            "hours_above_95pct_peak": int((missed["demand_mw"] > 0.95 * peak).sum()),
        }

    rec["reserve_family_year"] = {
        "hours_with_any_shortfall": int((resv["n_short"] > 0).sum()),
        "total_shortfall_mwh": float(resv["short_mw"].sum()),
        "by_family": {
            k: {
                "hours": int(v["hours"]),
                "short_mw": float(v["short_mw"]),
                "max_dual": float(v["max_dual"]),
            }
            for k, v in by_family.to_dict("index").items()
        },
    }
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_nyiso242_tail_phase0.json"),
    )
    args = ap.parse_args()

    out = {"bundle": str(BUNDLE.relative_to(REPO)), "years": {}}
    for y in args.years:
        rec = run_year(y)
        out["years"][str(y)] = rec
        print(
            f"{y}: actual {rec['actual_tail_hours']:4d} h > ${THRESHOLD:.0f} | "
            f"model {rec['model_tail_hours']:3d} | hit {rec['hit']:3d} | "
            f"missed {rec['missed']:4d} | invented {rec['invented']:3d}"
        )
        if rec["missed"]:
            print("   missed by month :", rec["missed_by_month"])
            print("   missed by hour  :", rec["missed_by_hour_of_day"])
            print("   model dual bands:", rec["missed_model_dual_bands"])
            print("   model state     :", rec["missed_model_state"])
            print("   load            :", rec["missed_load"])
            print("   max-dual zone   :", rec["missed_max_zone"])
        print("   reserve families:", rec["reserve_family_year"])

    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
