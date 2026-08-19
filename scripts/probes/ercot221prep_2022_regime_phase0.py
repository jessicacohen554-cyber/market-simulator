"""ercot-221 PREP (read-only): the 2022 regime point and the trailing-expectation year-grain test.

Owner-directed measurement session (2026-08-19, conversation lane
``claude/ercot-lmp-miss-analysis-cde845``) producing supporting evidence for
the ercot-220b-recommended ercot-221 Phase-0 charter (adaptive expectation
offer). NO shorthand consumed, no LP, no solve, no year scored, no run
registered, no matrix cell touched. Three read-only measurements:

(M-1) 2022 vs 2023 tail-formation contrast from ERCOT's own NP6-323
      telemetry (SystemLambda / PRC / RTORPA / RTORDPA, 5-min): PRC at the
      actual > $200 tail hours, lambda-carried share, adder share. 2022 is
      administratively-priced scarcity at real tightness (ORDC firing);
      2023 is conduct-priced scarcity at comfortable PRC — the regime axis
      of FINDING-ercot195 measured as a two-point contrast.

(M-2) Trailing-expectation year-grain test: candidate backward-looking
      statistics of realized EVENING (HE17-22) RT prices over trailing
      windows ending 1 June of each delivery year, compared to the measured
      storage offer p50 at p98 tightness (ercot-210: $2,714 / $1,281 /
      $990 for 2023/24/25). ALL candidates reported (no post-hoc
      selection buried): Uri-inclusive memory lands the 2023 level and the
      2023->2024 direction, and flattens by 2025 — the residual decay is
      the competitive-state (fleet growth) driver's signature.

(M-3) Model-margin hour selection on the current keeper
      (``ercot215_decontam_B`` committed sidecars): rank 2023 hours by the
      P1 ``ercot_ordc_total`` held-MW margin, sweep a binding-count
      threshold N, and report hits against the actual 181 tail hours. The
      trigger half of any conduct mechanism is already well-posed
      (136/181 at matched count); the price half is the open object.

Rule-22 posture: DATA-ONLY use of out-of-training years (the score is held
out, never the data). 2021/2022 actuals enter as measured *inputs* /
identification anchors; NO out-of-training year is solved or scored, and
2019 is left untouched entirely (no statistic here reads it) so the locked
test keeps its full power to surprise.

Usage::

    python scripts/probes/ercot221prep_2022_regime_phase0.py \
        [--out results/calibration/ercot221prep_2022_regime.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

# Committed inputs (all pre-existing; this probe writes nothing but its JSON).
ADDER_TELEMETRY = {
    2022: REPO
    / "data/raw/ercot/RTSCEDPRICEADDERNP6323_RTORDCRELDEPpriceAdderNP6323_2022.parquet",
    2023: REPO
    / "data/raw/ercot/RTSCEDPRICEADDERNP6323_RTORDCRELDEPpriceAdderNP6323_2023.parquet",
}
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
KEEPER_BUNDLE = REPO / "results/calibration/ercot215_decontam_B"

TAIL_THRESHOLD = 200.0  # $/MWh, rubric ERCOT scarcity-tail threshold
# ercot-210 measured storage offer p50 at the p98-tightness cut (FINDING-
# ercot210-conduct-transfer): the year-grain object M-2 tries to predict.
MEASURED_STORAGE_OFFER_P50 = {2023: 2714.0, 2024: 1281.0, 2025: 990.0}
# Evening block: HE17-22 (hour-beginning 16..21) — the storage discharge /
# net-peak window every scarcity episode in 2022-2025 lands in.
EVENING_HB = (16, 21)


def _hourly_telemetry(year: int) -> pd.DataFrame:
    """NP6-323 5-min feed -> hourly means keyed by fleet hour-of-year."""
    df = pd.read_parquet(
        ADDER_TELEMETRY[year],
        columns=["SCEDTimestamp", "SystemLambda", "PRC", "RTORPA", "RTORDPA"],
    )
    ts = pd.to_datetime(df["SCEDTimestamp"], format="%m/%d/%Y %H:%M:%S")
    df["hour"] = (
        (ts - pd.Timestamp(f"{year}-01-01")).dt.total_seconds() // 3600
    ).astype(int)
    return df.groupby("hour")[["SystemLambda", "PRC", "RTORPA", "RTORDPA"]].mean()


def measure_regime_contrast() -> dict:
    """M-1: 2022 vs 2023 tail formation from ERCOT's own telemetry."""
    act = pd.read_parquet(ACTUAL_LMP)
    out = {}
    for year in (2022, 2023):
        tel = _hourly_telemetry(year)
        ay = act[act["year"] == year]
        tail_hours = ay[ay["rt"] > TAIL_THRESHOLD]["hour"].values
        t = tel.loc[[h for h in tail_hours if h in tel.index]]
        adder = t["RTORPA"] + t["RTORDPA"]
        price = t["SystemLambda"] + adder
        out[str(year)] = {
            "tail_hours_gt200": int(len(tail_hours)),
            "prc_at_tail_mw": {
                "p50": float(t["PRC"].median()),
                "p10": float(t["PRC"].quantile(0.1)),
                "min": float(t["PRC"].min()),
            },
            "lambda_at_tail": {
                "p50": float(t["SystemLambda"].median()),
                "max": float(t["SystemLambda"].max()),
            },
            "rtorpa_at_tail": {
                "p50": float(t["RTORPA"].median()),
                "p90": float(t["RTORPA"].quantile(0.9)),
                "max": float(t["RTORPA"].max()),
            },
            "lambda_carried_hours": int((t["SystemLambda"] > TAIL_THRESHOLD).sum()),
            "adder_share_of_price_p50_pct": float(
                (100.0 * adder / price).median()
            ),
        }
    return out


def measure_trailing_expectation() -> dict:
    """M-2: trailing evening-price statistics vs measured storage offer p50.

    Every candidate is reported — the grid is the measurement, and any
    Phase-0 reusing it must PRE-REGISTER its statistic before looking
    (this probe's own scan spends selection freedom, stated in the JSON).
    """
    act = pd.read_parquet(ACTUAL_LMP).copy()
    act = act[act["year"] >= 2020]  # 2019 deliberately untouched (locked test)
    act["ts"] = act.apply(
        lambda r: pd.Timestamp(f"{int(r['year'])}-01-01")
        + pd.Timedelta(hours=int(r["hour"])),
        axis=1,
    )
    act["hb"] = act["ts"].dt.hour
    ev = (
        act[(act["hb"] >= EVENING_HB[0]) & (act["hb"] <= EVENING_HB[1])]
        .set_index("ts")
        .sort_index()
    )

    candidates = {
        "12mo_p99": (12, lambda s: s.quantile(0.99)),
        "24mo_p99": (24, lambda s: s.quantile(0.99)),
        "24mo_p995": (24, lambda s: s.quantile(0.995)),
        "36mo_p99": (36, lambda s: s.quantile(0.99)),
        "24mo_mean_top50h": (24, lambda s: s.nlargest(50).mean()),
        "36mo_mean_top100h": (36, lambda s: s.nlargest(100).mean()),
    }
    rows = {}
    for label, (months, fn) in candidates.items():
        vals = {}
        for year in (2023, 2024, 2025):
            end = pd.Timestamp(f"{year}-06-01")
            start = end - pd.DateOffset(months=months)
            s = ev.loc[start:end, "rt"].dropna()
            vals[str(year)] = float(fn(s))
        rows[label] = vals
    return {
        "measured_storage_offer_p50": {
            str(k): v for k, v in MEASURED_STORAGE_OFFER_P50.items()
        },
        "trailing_evening_rt_stats": rows,
        "selection_caveat": (
            "six candidates scanned post hoc in one session; a Phase-0 must "
            "pre-register its statistic and gates before evaluation"
        ),
        "reading": (
            "Uri-inclusive memory (36mo_mean_top100h) lands 2023 (~3016 vs "
            "2714) and the 2023->2024 direction, then flattens by 2025 while "
            "the measured level keeps falling — the residual decay matches "
            "the competitive-state (fleet 8.4x growth) driver, not price "
            "memory"
        ),
    }


def measure_margin_selection() -> dict:
    """M-3: keeper P1 margin as the trigger instrument for the 2023 tail."""
    act = pd.read_parquet(ACTUAL_LMP)
    a23 = act[act["year"] == 2023]
    tail = set(a23[a23["rt"] > TAIL_THRESHOLD]["hour"].values)

    rf = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "reserve_family_2023.parquet")
    rf = rf[(rf["pass"] == "P1") & (rf["family"] == "ercot_ordc_total")]
    margin = rf.set_index("hour")["held_mw"]
    order = margin.sort_values().index.values

    a23_ix = a23.set_index("hour")
    sweep = []
    for n in (100, 181, 300, 500, 1000):
        sel = set(order[:n])
        hits = len(sel & tail)
        false_hours = sorted(sel - tail)
        sweep.append(
            {
                "n_tightest": n,
                "hits_of_181": hits,
                "false_positives": n - hits,
                "actual_rt_p50_in_false_hours": float(
                    a23_ix.loc[false_hours, "rt"].median()
                )
                if false_hours
                else None,
            }
        )
    ranks = margin.rank(pct=True).loc[sorted(tail)]
    return {
        "instrument": "keeper P1 ercot_ordc_total held_mw (ascending = tighter)",
        "keeper_bundle": KEEPER_BUNDLE.name,
        "threshold_sweep": sweep,
        "actual_tail_model_tightness_percentile": {
            "p25": float(ranks.quantile(0.25)),
            "p50": float(ranks.quantile(0.50)),
            "p75": float(ranks.quantile(0.75)),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/ercot221prep_2022_regime.json"),
    )
    args = ap.parse_args()

    result = {
        "probe": "ercot221prep_2022_regime_phase0",
        "posture": (
            "read-only; no LP, no solve, no year scored, no run registered, "
            "no matrix cell touched, no shorthand consumed; rule-22 "
            "data-not-score (2019 untouched)"
        ),
        "m1_regime_contrast_2022_vs_2023": measure_regime_contrast(),
        "m2_trailing_expectation_year_grain": measure_trailing_expectation(),
        "m3_keeper_margin_selection_2023": measure_margin_selection(),
        "data_availability": {
            "sced_60day_offer_corpus_2022": (
                "NOT HELD: corpus publications span 2023-03..2026-03 "
                "(delivery >= ~2023-01); 2022 deliveries published "
                "2022-03..2023-02. MIS recoverability is an OPEN check "
                "(fetch_ercot_sced_corpus_shards.py exists; the fresh-MIS "
                "route decays per the corpus README)"
            ),
            "np6323_telemetry_2022": "held (data/raw/ercot)",
            "actual_lmp_hourly": "held 2018-2026 (_validation-source)",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out}")
    print(json.dumps(result["m1_regime_contrast_2022_vs_2023"], indent=1))


if __name__ == "__main__":
    main()
