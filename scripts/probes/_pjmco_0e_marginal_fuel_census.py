"""PJM close-out step 0e (zero LP): real-time marginal-fuel shares vs the keeper's ``unit_marginal`` layer.

Plan ``docs/backcast-closeout-plan-2026-10.md`` §3.6 step 0e / §4 row 12; research shard
``docs/records/governance/closeout-2026-10/SHARD-PJM-closeout-research-2026-10-02.md`` §6 row 1.

Pre-fixed reading (not changed here): PASS iff the model coal-set share is within 1.3x of
PJM's hourly-data share (ratio in [1/1.3, 1.3]); headline year 2020, every year 2019-2025
reported. PASS => the C3a 2020 low-end floor is a level error, not a merit-order error;
FAIL => merit-order.

Definitions (fixed before reading the model side)
-------------------------------------------------
PJM side (``data/raw/pjm-marginal-fuel/by-year/``, IMM Marginal Fuel Postings): each
5-minute interval gives weight 1/n to each of its n marginal units; the hourly fuel share
is the mean over the hour's intervals (the IMM data description's worked example). The
annual share is the mean of hourly shares over every hour of the year (time-weighted).
Coal set = ``Coal`` + ``Waste Coal`` (the model's coal set carries COAL_WC); ``Coal``
alone is also reported.

Model side (``results/calibration/pjmnext16_A_span/hourly/unit_marginal_<y>.parquet``,
P1, ``marginal == 1`` = interior column with |red_cost| <= 0.01, ``scripts/lib/
unit_marginal.py``): the LP has one interval per hour, so each hour gives weight 1/n to
each of its n flagged marginal units -- the same construction as PJM's. Primary:
internal units only (``fuel != 'import'``: the PJM 2019-2025 postings carry no
``Interface`` category); an hour with no flagged internal unit had its price set by a
column the layer cannot flag (wind/solar/storage/import/slack) -- the analogue of PJM's
wind/solar/interface weight -- and contributes coal weight 0; annual share = mean over
all 8760 hours.

Sensitivities: (b) both sides renormalised to the dispatchable universe the flag can see
(model: hours with >= 1 flagged internal unit; PJM: weight excluding Wind, Solar,
Battery, Demand Response, Price Responsive Demand, Missing Data, Min Gen/Dispatch Reset);
(c) model with imports in the denominator; (d) pooled count share (marginal unit-hours by
fuel / all marginal unit-hours) vs the IMM SOM "share of RT marginal units" (Coal/Steam,
``data/raw/som-competitive-conduct``), the like-for-like of the SOM's count-weighted
table. The PJM file cannot be re-aggregated to a count share (no per-interval n), so the
file-vs-SOM gap is an aggregation difference, reported not reconciled.

Hourly frequency: share of hours where coal carries any marginal weight (>0) and where it
carries >= 0.5 (the NEXT-18 "coal-set hour"), each side.

Run: ``python scripts/probes/_pjmco_0e_marginal_fuel_census.py``
Writes ``results/phase0/pjm/_pjmco_0e_marginal_fuel_census.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PJM_DIR = REPO / "data/raw/pjm-marginal-fuel/by-year"
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
OUT = REPO / "results/phase0/pjm/_pjmco_0e_marginal_fuel_census.json"
YEARS = list(range(2019, 2026))
HEADLINE = 2020
#: Pre-fixed PASS band (plan §3.6 step 0e).
RATIO_BAND = 1.3
#: Model hours per year (LP is 8760 always, rule 8).
T = 8760
PJM_COAL = ("Coal", "Waste Coal")
PJM_GAS = ("Natural Gas",)
#: PJM fuel labels with no flaggable model counterpart (sensitivity b).
PJM_NON_DISPATCHABLE = (
    "Wind",
    "Solar",
    "Battery",
    "Demand Response",
    "Price Responsive Demand",
    "Missing Data",
    "Min Gen/Dispatch Reset",
)
MODEL_GAS = ("gas_cc", "gas_ct", "gas_st")
#: Coal weight at or above which an hour is a "coal-set hour" (NEXT-18 definition).
COAL_SET_WEIGHT = 0.5


def pjm_year(y: int) -> dict:
    """Aggregate one year of the PJM postings into annual time-weighted shares."""
    d = pd.read_csv(PJM_DIR / f"pjm_marginal_fuel_{y}.csv")
    key = ["hour_beginning_ept", "mms_timezone"]
    w = d.pivot_table(
        index=key,
        columns="fuel_type",
        values="percent_marginal",
        aggfunc="sum",
        fill_value=0.0,
    )
    n_hours = len(w)
    col = lambda names: w[[c for c in names if c in w.columns]].sum(axis=1)  # noqa: E731
    coal = col(PJM_COAL)
    coal_only = col(("Coal",))
    gas = col(PJM_GAS)
    nondisp = col(PJM_NON_DISPATCHABLE)
    disp = 1.0 - nondisp
    ok = disp > 1e-9
    return {
        "hours": int(n_hours),
        "coal_share": float(coal.mean()),
        "coal_only_share": float(coal_only.mean()),
        "gas_share": float(gas.mean()),
        "nondispatchable_weight": float(nondisp.mean()),
        "coal_share_dispatchable_universe": float((coal[ok] / disp[ok]).mean()),
        "gas_share_dispatchable_universe": float((gas[ok] / disp[ok]).mean()),
        "freq_hours_coal_any": float((coal > 0).mean()),
        "freq_hours_coal_ge_half": float((coal >= COAL_SET_WEIGHT).mean()),
    }


def model_year(y: int) -> dict:
    """Aggregate one year of the keeper ``unit_marginal`` layer the same way."""
    d = pd.read_parquet(
        HOURLY / f"unit_marginal_{y}.parquet", columns=["fuel", "hour", "marginal"]
    )
    m = d[d["marginal"] == 1][["fuel", "hour"]].copy()
    m["fuel"] = m["fuel"].astype(str)
    m["is_coal"] = m["fuel"] == "coal"
    m["is_gas"] = m["fuel"].isin(MODEL_GAS)
    m["is_import"] = m["fuel"] == "import"

    def shares(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = np.bincount(frame["hour"], minlength=T).astype(float)
        c = np.bincount(frame["hour"], weights=frame["is_coal"], minlength=T)
        g = np.bincount(frame["hour"], weights=frame["is_gas"], minlength=T)
        with np.errstate(invalid="ignore", divide="ignore"):
            return n, np.where(n > 0, c / n, 0.0), np.where(n > 0, g / n, 0.0)

    internal = m[~m["is_import"]]
    n_i, coal_i, gas_i = shares(internal)
    n_a, coal_a, _ = shares(m)
    has = n_i > 0
    fuel_counts = m["fuel"].value_counts().to_dict()
    total = float(len(m))
    return {
        "hours": T,
        "marginal_unit_hours": int(total),
        "marginal_unit_hours_by_fuel": {k: int(v) for k, v in fuel_counts.items()},
        "hours_with_internal_flag": int(has.sum()),
        "hours_without_internal_flag": int((~has).sum()),
        "coal_share": float(coal_i.mean()),
        "gas_share": float(gas_i.mean()),
        "coal_share_dispatchable_universe": float(coal_i[has].mean()),
        "gas_share_dispatchable_universe": float(gas_i[has].mean()),
        "coal_share_incl_imports": float(coal_a.mean()),
        "coal_share_pooled_count_internal": float(
            internal["is_coal"].sum() / max(len(internal), 1)
        ),
        "coal_share_pooled_count_all": float(m["is_coal"].sum() / max(total, 1.0)),
        "freq_hours_coal_any": float((coal_i > 0).mean()),
        "freq_hours_coal_ge_half": float((coal_i >= COAL_SET_WEIGHT).mean()),
    }


def som_coal() -> dict[int, float]:
    """IMM SOM annual coal share of RT marginal units (Coal/Steam), by year."""
    s = pd.read_csv(SOM)
    s = s[
        (s["iso"] == "PJM")
        & (s["fleet_segment"] == "coal")
        & (s["metric"] == "rt_marginal_resource_share")
    ]
    return {int(r.year): float(r.value) for r in s.itertuples()}


def verdict(ratio: float) -> str:
    """PASS iff ratio in [1/RATIO_BAND, RATIO_BAND]."""
    return "PASS" if 1.0 / RATIO_BAND <= ratio <= RATIO_BAND else "FAIL"


def main() -> None:
    """Run the census and write the JSON record."""
    som = som_coal()
    rows = {}
    for y in YEARS:
        p, mo = pjm_year(y), model_year(y)
        ratio = mo["coal_share"] / p["coal_share"]
        rows[y] = {
            "pjm": p,
            "model": mo,
            "som_coal_rt_marginal_unit_share": som.get(y),
            "ratio_primary": ratio,
            "verdict_primary": verdict(ratio),
            "ratio_dispatchable_universe": mo["coal_share_dispatchable_universe"]
            / p["coal_share_dispatchable_universe"],
            "ratio_model_incl_imports": mo["coal_share_incl_imports"] / p["coal_share"],
            "ratio_pooled_count_vs_som": (
                mo["coal_share_pooled_count_internal"] / som[y] if y in som else None
            ),
            "ratio_gas": mo["gas_share"] / p["gas_share"],
            "ratio_freq_coal_any": mo["freq_hours_coal_any"] / p["freq_hours_coal_any"],
            "ratio_freq_coal_ge_half": mo["freq_hours_coal_ge_half"]
            / p["freq_hours_coal_ge_half"],
        }
        rows[y]["verdict_dispatchable_universe"] = verdict(
            rows[y]["ratio_dispatchable_universe"]
        )
    n_pass = sum(r["verdict_primary"] == "PASS" for r in rows.values())
    out = {
        "probe": "_pjmco_0e_marginal_fuel_census",
        "keeper": "pjmnext16_A_span",
        "reading": (
            f"PASS iff model/PJM coal-set share ratio in [1/{RATIO_BAND}, {RATIO_BAND}]; "
            f"headline {HEADLINE}; PASS => level error, FAIL => merit-order error"
        ),
        "headline_year": HEADLINE,
        "headline_verdict": rows[HEADLINE]["verdict_primary"],
        "years_pass_primary": n_pass,
        "years": {str(k): v for k, v in rows.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    hdr = "year pjm_coal pjm_coal_only som model ratio V | disp_pjm disp_model ratio V | pooled/som | gas pjm model | freq>0 pjm model | freq>=.5 pjm model | noflag_h"
    print(hdr)
    for y, r in rows.items():
        p, mo = r["pjm"], r["model"]
        print(
            f"{y} {p['coal_share']:.3f} {p['coal_only_share']:.3f} {r['som_coal_rt_marginal_unit_share']:.3f} "
            f"{mo['coal_share']:.3f} {r['ratio_primary']:.2f} {r['verdict_primary']} | "
            f"{p['coal_share_dispatchable_universe']:.3f} {mo['coal_share_dispatchable_universe']:.3f} "
            f"{r['ratio_dispatchable_universe']:.2f} {r['verdict_dispatchable_universe']} | "
            f"{mo['coal_share_pooled_count_internal']:.3f}/{r['ratio_pooled_count_vs_som']:.2f} | "
            f"{p['gas_share']:.3f} {mo['gas_share']:.3f} | "
            f"{p['freq_hours_coal_any']:.3f} {mo['freq_hours_coal_any']:.3f} | "
            f"{p['freq_hours_coal_ge_half']:.3f} {mo['freq_hours_coal_ge_half']:.3f} | "
            f"{mo['hours_without_internal_flag']}"
        )
    print(OUT)


if __name__ == "__main__":
    main()
