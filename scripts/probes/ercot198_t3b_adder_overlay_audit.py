"""ercot-198 — T-3b: the published-adder overlay-completeness audit (read-only).

Executes the signed card-T companion T-3b
(`docs/DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md` §4 T-3b,
RESOLUTIONS signed 2026-08-14): does the committed RTORPA/RTORDPA overlay
capture the FULL published adder content of 2024/2025 RTSPP? No mechanism, no
ScenarioConfig field, no solve, no matrix row — measured-vs-measured only
(rule 13 `[R-MEASURED]`: actuals enter comparison/attribution, never any
model input; rule 22: no year is solved or scored).

Settlement identity audited: bench ``rt_lw_mon`` is settlement RTSPP =
time-weighted RTLMP + RTORPA + RTORDPA (the two adders of the pre-RTC+B
design — "The current ERCOT market design features two distinct price
adders, the ORDC and the RDPA", 2024 SOM p.43; RTOFFPA is published in the
same report but is NOT part of energy settlement, so it is reported here and
excluded from the content measure). The scored model monthly price ``pMon``
is the demand-weighted energy-only dual (card §2(d)); the keeper's committed
settlement-side content is the sidecar ``rtordpa_overlay`` (measured RTORDPA,
`ercot_rtordpa_overlay=True`) plus ``ordc_adder`` (the model's own endogenous
RTORPA analogue — the ORDC total-family reserve dual).

Published sources, all committed under data/raw (no new intake needed — the
card §4 T-3b cost line "not currently on disk" predates verification; the
series IS on disk in two independent forms):
- ``data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet`` — curated from
  ERCOT MIS NP6-905-CD "Historical Real-Time Price Adders by SCED Interval"
  (reportTypeId=13231, archive RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_<year>;
  https://www.ercot.com/mp/data-products — fetch provenance in
  ``scripts/data/fetch_ercot_ordc_reserves.py`` and the parquet metadata),
  hourly means on the model's non-leap CST 8760 clock;
- ``data/raw/ercot/RTSCEDPRICEADDERNP6323_RTORDCRELDEPpriceAdderNP6323_
  {year}.parquet`` — the recovered raw NP6-323-CD SCED-interval report
  (independent columns RTORPA/RTOFFPA/RTORDPA), used as a curation
  cross-check (NOTE: its 2024 file is missing June entirely; the curated
  NP6-905-CD series is the complete record);
- the ERCOT State of the Market reports (Potomac Economics), committed PDFs
  under ``data/raw/ERCOT/`` — annual all-hours adder averages used as the
  independent published cross-check (2024 SOM Fig.4/Fig.5; 2025 SOM
  Fig.5/Fig.6).

Settlement-closure guard: the published archive retains ORIGINAL (pre
price-correction) adder prints. An archive adder that never settled is not
RTSPP content; the guard flags hours where the archive adder total exceeds
the settled hub RTSPP (committed bench hourly) by > $50 — a settled adder is
additive to the hub LMP, so RTSPP cannot sit far below the adder alone
without a deeply negative hub-average LMP alongside a positive system
lambda. Exactly one hour trips it (2025 hour 4334, Jun-30 14:00 CST: archive
RTORPA $414.12/h from SCED prints near VOLL, RTOLCAP 14.9 GW, settled hub
RTSPP $54.96 vs lambda $41.61 — a price-corrected print). Headline
"settled published" content excludes it; the uncorrected series is also
reported.

Regime end: the ORDC/RTORPA/RTORDPA design retired at the RTC+B go-live
2025-12-05 (``scarcity.RTCB_GOLIVE_HOUR`` = 8112); the published series ends
there (trailing NaN, mapped to 0 adder content — the design's own zero).

Output: ``results/calibration/ercot198_t3b_adder_overlay_audit.json``.

Usage::

    python scripts/probes/ercot198_t3b_adder_overlay_audit.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CURATED = REPO / "data" / "raw" / "ercot" / "ercot_{year}_ordc_reserves_hourly.parquet"
RAW_NP6323 = (
    REPO
    / "data"
    / "raw"
    / "ercot"
    / "RTSCEDPRICEADDERNP6323_RTORDCRELDEPpriceAdderNP6323_{year}.parquet"
)
SIDECAR = REPO / "results" / "calibration" / "ercot192_arm_B" / "hourly"
ACTUAL_HOURLY = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
ERCOT196_JSON = REPO / "results" / "calibration" / "ercot196_shape_decomposition.json"
OUT = REPO / "results" / "calibration" / "ercot198_t3b_adder_overlay_audit.json"

YEARS = (2024, 2025)
HOURS = 8760
# Settlement-closure guard threshold ($/MWh): archive adder total above the
# settled hub RTSPP by more than this margin cannot have settled (see module
# docstring). Wide enough that no genuine congestion-basis hour trips it.
CORRECTION_MARGIN = 50.0

# Independent published cross-check: SOM all-hours annual averages ($/MWh).
# 2024 SOM Fig.4 (p.44): ORDC 2024 = 161 active h, $0.25 all-hours; Fig.5
# (p.45): RDPA 2024 = 837 active h, $0.24 all-hours. 2025 SOM Fig.5 (p.30):
# ORDC 2025 = 57 active h, $2.26 active, $0.02 all-hours ("contributed less
# than $0.02/MWh"); Fig.6 (p.31) + text: RDPA 2025 = $0.41 all-hours.
SOM_ALL_HOURS = {
    2024: {"ordc_rtorpa": 0.25, "rdpa_rtordpa": 0.24},
    2025: {"ordc_rtorpa": 0.02, "rdpa_rtordpa": 0.41},
}

# Non-leap month edges on the shared 8760-hour clock (the ercot-196 basis).
_MONTH_HOURS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_EDGES = [0]
for _d in _MONTH_HOURS:
    _EDGES.append(_EDGES[-1] + _d * 24)


def _dense(series: pd.Series) -> np.ndarray:
    return series.reindex(range(HOURS)).to_numpy(dtype=float)


def _monthly_w(values: np.ndarray, weights: np.ndarray) -> list[float]:
    out = []
    for m in range(12):
        lo, hi = _EDGES[m], _EDGES[m + 1]
        v, w = values[lo:hi], weights[lo:hi]
        ok = ~np.isnan(v) & (w > 0)
        out.append(round(float((v[ok] * w[ok]).sum() / w[ok].sum()), 4))
    return out


def _annual_w(values: np.ndarray, weights: np.ndarray) -> float:
    ok = ~np.isnan(values) & (weights > 0)
    return round(float((values[ok] * weights[ok]).sum() / weights[ok].sum()), 4)


def audit_year(year: int) -> dict:
    cur = pd.read_parquet(CURATED.with_name(CURATED.name.format(year=year))).set_index(
        "hour"
    )
    # Published adders on the model clock; NaN = post-go-live (design retired)
    # -> zero adder content, the design's own value, never fabricated.
    pub = {
        c: np.nan_to_num(_dense(cur[c]), nan=0.0)
        for c in ("rtorpa", "rtoffpa", "rtordpa")
    }
    covered = int((~cur["rtordpa"].isna()).sum())

    sysd = pd.read_parquet(SIDECAR / f"system_{year}.parquet")
    sysd = sysd[(sysd["year"] == year) & (sysd["pass"] == "P1")]
    demand = _dense(sysd.groupby("hour")["demand"].sum())
    committed = {
        c: np.nan_to_num(_dense(sysd.groupby("hour")[c].first()), nan=0.0)
        for c in ("rtordpa_overlay", "ordc_adder")
    }

    # Settlement-closure guard against price-corrected archive prints.
    act = pd.read_parquet(ACTUAL_HOURLY)
    rt = _dense(act[act["year"] == year].set_index("hour")["rt"])
    adder_total = pub["rtorpa"] + pub["rtordpa"]
    flagged = np.where(adder_total > rt + CORRECTION_MARGIN)[0]
    flag_rows = [
        {
            "hour": int(h),
            "rtorpa": round(float(pub["rtorpa"][h]), 2),
            "rtordpa": round(float(pub["rtordpa"][h]), 2),
            "settled_rt": round(float(rt[h]), 2),
            "system_lambda": round(float(cur["system_lambda"].get(h, np.nan)), 2),
        }
        for h in flagged
    ]
    settled = {k: v.copy() for k, v in pub.items()}
    for h in flagged:
        for k in settled:
            settled[k][h] = 0.0

    def block(rtorpa: np.ndarray, rtordpa: np.ndarray) -> dict:
        tot = rtorpa + rtordpa
        return {
            "rtorpa_mon": _monthly_w(rtorpa, demand),
            "rtordpa_mon": _monthly_w(rtordpa, demand),
            "total_mon": _monthly_w(tot, demand),
            "rtorpa_dw": _annual_w(rtorpa, demand),
            "rtordpa_dw": _annual_w(rtordpa, demand),
            "total_dw": _annual_w(tot, demand),
            # The card-§2(d) annual convention (mean of demand-weighted months).
            "total_mean_of_months": round(
                float(np.mean(_monthly_w(tot, demand))), 4
            ),
        }

    published = block(settled["rtorpa"], settled["rtordpa"])
    published_uncorrected = block(pub["rtorpa"], pub["rtordpa"])
    com = block(committed["ordc_adder"], committed["rtordpa_overlay"])
    com = {k.replace("rtorpa", "ordc_adder").replace("rtordpa", "rtordpa_overlay"): v
           for k, v in com.items()}

    gap_mon = [
        round(p - c, 4)
        for p, c in zip(published["total_mon"], com["total_mon"])
    ]
    # Component identity check: the overlay input IS the published RTORDPA.
    overlay_vs_pub_max = float(
        np.nanmax(np.abs(committed["rtordpa_overlay"] - pub["rtordpa"]))
    )

    # Curation cross-check vs the recovered raw NP6-323 SCED-interval report
    # (pooled-interval means overweight event hours vs the curated
    # hourly-mean basis; agreement is expected to ~0.2 $/MWh in scarcity
    # months, exact months missing from the raw file are named).
    rawp = RAW_NP6323.with_name(RAW_NP6323.name.format(year=year))
    raw = pd.read_parquet(rawp, columns=["SCEDTimestamp", "RTORPA", "RTORDPA"])
    ts = pd.to_datetime(raw["SCEDTimestamp"], format="%m/%d/%Y %H:%M:%S")
    g = raw.groupby(ts.dt.month)[["RTORPA", "RTORDPA"]].mean()
    raw_missing_months = sorted(set(range(1, 13)) - set(int(m) for m in g.index))
    cur_tw_mon = {
        c: [
            round(float(np.nanmean(_dense(cur[c])[_EDGES[m] : _EDGES[m + 1]])), 4)
            for m in range(12)
        ]
        for c in ("rtorpa", "rtordpa")
    }
    raw_tw_mon = {
        c.lower(): [
            round(float(g.loc[m, c]), 4) if m in g.index else None
            for m in range(1, 13)
        ]
        for c in ("RTORPA", "RTORDPA")
    }

    return {
        "coverage_hours": covered,
        "published_settled": published,
        "published_uncorrected_archive": published_uncorrected,
        "rtoffpa_dw_excluded_not_in_rtspp": _annual_w(settled["rtoffpa"], demand),
        "committed_overlay": com,
        "gap_total_mon": gap_mon,
        "gap_total_dw": round(published["total_dw"] - com["total_dw"], 4),
        "gap_rtorpa_vs_ordc_adder_dw": round(
            published["rtorpa_dw"] - com["ordc_adder_dw"], 4
        ),
        "gap_rtordpa_vs_overlay_dw": round(
            published["rtordpa_dw"] - com["rtordpa_overlay_dw"], 4
        ),
        "correction_flagged_hours": flag_rows,
        "overlay_input_vs_published_rtordpa_max_abs": round(overlay_vs_pub_max, 6),
        "cross_check_raw_np6323": {
            "missing_months": raw_missing_months,
            "curated_tw_mon": cur_tw_mon,
            "raw_tw_mon": raw_tw_mon,
        },
        "cross_check_som_all_hours": {
            "som": SOM_ALL_HOURS[year],
            "computed_tw_full_year": {
                "rtorpa": round(float(np.nanmean(settled["rtorpa"])), 4),
                "rtordpa": round(float(np.nanmean(settled["rtordpa"])), 4),
            },
        },
    }


def main() -> None:
    result: dict = {"probe": "ercot198_t3b_adder_overlay_audit", "years": {}}
    for year in YEARS:
        result["years"][str(year)] = audit_year(year)

    # Consistency with the card-§2(d) measurement (ercot-196 model_overlay_dw).
    e196 = json.loads(ERCOT196_JSON.read_text())
    for year in YEARS:
        ours = result["years"][str(year)]["committed_overlay"]["total_mon"]
        theirs = [t["model_overlay_dw"] for t in e196["years"][str(year)]["tail"]]
        result["years"][str(year)]["cross_check_ercot196_overlay_dw_max_abs"] = round(
            max(abs(a - b) for a, b in zip(ours, theirs)), 4
        )

    OUT.write_text(json.dumps(result, indent=2) + "\n")
    for year in YEARS:
        y = result["years"][str(year)]
        pubb, comb = y["published_settled"], y["committed_overlay"]
        print(
            f"{year}: published (settled) RTORPA+RTORDPA dw {pubb['total_dw']:.3f} "
            f"$/MWh (RTORPA {pubb['rtorpa_dw']:.3f} + RTORDPA {pubb['rtordpa_dw']:.3f}) "
            f"| committed overlay dw {comb['total_dw']:.3f} "
            f"(rtordpa_overlay {comb['rtordpa_overlay_dw']:.3f} + model ordc_adder "
            f"{comb['ordc_adder_dw']:.3f}) | gap {y['gap_total_dw']:+.3f}"
        )
        print("  mon   pubORPA pubORDPA pubTOT | comTOT    gap")
        for m in range(12):
            print(
                f"   {m + 1:02d}  {pubb['rtorpa_mon'][m]:8.3f} "
                f"{pubb['rtordpa_mon'][m]:8.3f} {pubb['total_mon'][m]:7.3f} | "
                f"{comb['total_mon'][m]:6.3f} {y['gap_total_mon'][m]:+7.3f}"
            )
        if y["correction_flagged_hours"]:
            print(f"  correction-flagged archive hours: {y['correction_flagged_hours']}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
