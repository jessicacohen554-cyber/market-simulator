"""c3c-Q1 (read-only, no LP): is PJM's reserve dual REAL or the ercot-214 phantom?

Executes question Q1 of ``docs/CHARTER-c3c-scarcity-program-2026-08-31.md`` §5
against the PJM designated keeper's committed bytes and PJM's own published
reserve-market record. **Solves nothing, scores nothing, modifies nothing** —
no LP is built, no year is re-scored, no holdout year is touched (2023-2025
only). The ercot-163/170/208/214 no-LP precedent.

Inputs, all committed:

* ``results/calibration/pjm_debugb_inputclock_A/hourly/reserve_family_<y>.parquet``
  — the keeper's per-family P1 reserve balance-row dual, requirement, held MW
  and ORDC shortfall (the ONLY artifact in which a family's binding is
  observable, CLAUDE.md rule 15 ``[R-DASHBOARD]``).
* ``.../hourly/system_<y>.parquet`` — the P1 zonal energy dual (the C3c basis).
* ``data/raw/PJM-AS/reserve_market_results_<y>.parquet`` — PJM DataMiner2
  "Ancillary Services Market Results - Reserve Market Results" (RT), 5-minute,
  ``locale`` in {PJM_RTO, MAD} x ``service`` PR: the published clearing price
  (``mcp``), the published requirement (``as_req_mw``) and the published held
  quantity (``total_mw``). This is the public record of when PJM reality
  actually priced primary-reserve scarcity.
* ``data/raw/_validation-source/pjm_ordc_curve.csv`` — the published two-step
  ORDC penalty factors (Manual 11 sec 4.3.3: $850 to the requirement, $300 for
  the next 190 MW, $0 beyond).

Five measurements, in order:

1. **Clock + provenance identity.** The model's ``requirement_mw`` is asserted
   against the published ``as_req_mw`` plus the published outermost ORDC
   breakpoint offset (190 MW), hour by hour, on a leap-day-excised EPT
   hour-of-year index. An exact identity in every covered hour is what licenses
   every overlap below; anything less and the overlap is measuring a clock.
2. **Channel census.** Which LP channel forms the dual: the ORDC shortfall
   penalty steps (the ercot-214 failure mode) or reserve/energy opportunity
   cost. Reported as the shortfall column's support plus the dual's position
   against the published penalty factors.
3. **The overlap (the caiso-144 section-D construction).** The model's
   positive-dual hours against hours PJM reality priced primary reserve, at
   three published severity tiers - ``mcp > 0`` (reserve priced at all),
   ``max 5-min mcp >= $300`` (reality on an ORDC penalty step) and
   ``total_mw < as_req_mw`` (reality actually short) - with the year's base
   rate and a one-sided hypergeometric p-value for each.
4. **Magnitude and direction.** The model dual against the published MCP in the
   coincident hours. A phantom over-prices a channel reality does not have;
   the direction of the error is the discriminating fact.
5. **Is C3c even load-bearing on this channel?** The model's C3c tail hours
   (max zonal energy dual > $200, the rubric basis) intersected with the
   positive-dual hours, per year, plus the run payload's own ``ordc.hoursGt200``
   record of whether the scored tail is the energy-only dual or a settlement
   overlay.

Usage::

    python scripts/probes/c3c_q1_pjm_phantom_audit.py \
        [--out results/calibration/_c3c_q1_pjm_phantom_audit.json]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

BUNDLE = REPO / "results" / "calibration" / "pjm_debugb_inputclock_A"
KEEPER_ID = "2026-08-15-pjm-162-inputclock"
PAYLOAD = REPO / "frontend" / "data" / "backcast" / "runs" / f"{KEEPER_ID}.js"
PJM_AS = REPO / "data" / "raw" / "PJM-AS"
ORDC_CURVE = REPO / "data" / "raw" / "_validation-source" / "pjm_ordc_curve.csv"

YEARS = (2023, 2024, 2025)
# Model reserve family -> the published DataMiner2 ``locale`` it represents.
# ``pjm_primary`` is the RTO Reserve Zone, ``pjm_primary_mad`` the nested
# Mid-Atlantic/Dominion Reserve Subzone (Manual 11 sec 4.2; the model's MAD
# family is the INCREMENTAL nested row, while the published MAD ``mcp`` is the
# TOTAL subzone price, so the nested comparison also reports the model sum).
FAMILY_LOCALE = {"pjm_primary": "PJM_RTO", "pjm_primary_mad": "MAD"}
SERVICE = "PR"  # Primary Reserve — the product the model's family represents
TAIL_THRESHOLD = 200.0  # rubric section 5, PJM (calibration_verdict.TAIL_THRESHOLD)
DUAL_EPS = 1e-6


def _hour_of_year(ts: pd.Series, year: int) -> pd.Series:
    """Map EPT timestamps to the model's 8760 hour index (leap day excised).

    The LP is always 8760 hours (CLAUDE.md rule 8 ``[R-8760]``), so a leap
    year's Feb 29 has no model hour; every later timestamp shifts back one day.
    """
    doy = ts.dt.dayofyear.copy()
    if pd.Timestamp(f"{year}-12-31").dayofyear == 366:
        doy = doy - (ts.dt.month > 2).astype(int)
    return (doy - 1) * 24 + ts.dt.hour


def _published(year: int, locale: str) -> pd.DataFrame:
    """Hourly aggregation of the published RT reserve-market record."""
    df = pd.read_parquet(PJM_AS / f"reserve_market_results_{year}.parquet")
    df["_dt_ept"] = pd.to_datetime(df["_dt_ept"])
    df = df[~((df["_dt_ept"].dt.month == 2) & (df["_dt_ept"].dt.day == 29))].copy()
    d = df[(df["service"] == SERVICE) & (df["locale"] == locale)].copy()
    d["h"] = _hour_of_year(d["_dt_ept"], year)
    d["_short"] = d["total_mw"] < d["as_req_mw"] - 1e-6
    g = d.groupby("h").agg(
        mcp_mean=("mcp", "mean"),
        mcp_max=("mcp", "max"),
        as_req_mw=("as_req_mw", "mean"),
        total_mw=("total_mw", "mean"),
        short_intervals=("_short", "sum"),
        intervals=("mcp", "size"),
    )
    return g.reindex(range(8760))


def _ordc_offset() -> float:
    """The published outermost ORDC breakpoint offset (MW), from the cited CSV."""
    c = pd.read_csv(ORDC_CURVE, comment="#")
    sel = c[(c["service"] == "Primary") & (c["locale"] == "RTO")]
    return float(sel["breakpoint_offset_mw"].max())


def _ordc_penalties() -> list[float]:
    c = pd.read_csv(ORDC_CURVE, comment="#")
    sel = c[(c["service"] == "Primary") & (c["locale"] == "RTO")]
    return sorted(float(v) for v in sel["penalty_factor"].unique())


def _hypergeom_sf(k: int, N: int, K: int, n: int) -> float:
    """P(X >= k) for X ~ Hypergeometric(N population, K successes, n draws)."""
    if n == 0 or K == 0:
        return 1.0
    total = 0.0
    denom = math.comb(N, n)
    for i in range(k, min(K, n) + 1):
        total += math.comb(K, i) * math.comb(N - K, n - i)
    return total / denom


def _payload_ordc() -> dict:
    src = PAYLOAD.read_text()
    blob = src.split('"')[3]
    data = json.loads(gzip.decompress(base64.b64decode(blob)))
    return {y: data["years"][y].get("ordc") for y in data["years"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_c3c_q1_pjm_phantom_audit.json"),
    )
    args = ap.parse_args()

    offset = _ordc_offset()
    penalties = _ordc_penalties()
    out: dict = {
        "charter": "docs/CHARTER-c3c-scarcity-program-2026-08-31.md section 5 Q1",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(REPO)),
        "published_source": (
            "data/raw/PJM-AS/reserve_market_results_<year>.parquet "
            "(PJM DataMiner2, Ancillary Services Market Results - Reserve "
            "Market Results, RT, 5-minute; service=PR)"
        ),
        "ordc_curve": {
            "path": str(ORDC_CURVE.relative_to(REPO)),
            "outer_breakpoint_offset_mw": offset,
            "penalty_factors": penalties,
            "citation": "PJM Manual 11 sec 4.3.3 (FERC EL19-58/ER19-1486, in force 2022-10-01)",
        },
        "solve": "none — read-only over committed artifacts and published data",
        "years": {},
    }

    payload_ordc = _payload_ordc()

    for year in YEARS:
        rf = pd.read_parquet(BUNDLE / "hourly" / f"reserve_family_{year}.parquet")
        sysdf = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        max_zonal = sysdf.groupby("hour")["price"].max().reindex(range(8760))
        tail_hours = set(int(h) for h in max_zonal.index[max_zonal > TAIL_THRESHOLD])

        yrec: dict = {
            "model_tail_hours_gt200": len(tail_hours),
            "payload_ordc_hoursGt200": payload_ordc.get(str(year)),
            "c3c_scored_basis": (
                "settlement overlay"
                if (payload_ordc.get(str(year)) or {})
                .get("hoursGt200", {})
                .get("overlay")
                is not None
                else "energy-only LP dual (no overlay in payload)"
            ),
            "families": {},
        }

        for fam, locale in FAMILY_LOCALE.items():
            m = rf[rf["family"] == fam].set_index("hour").reindex(range(8760))
            pub = _published(year, locale)
            covered = pub["intervals"].notna() & m["dual"].notna()
            n_cov = int(covered.sum())

            # (1) clock + provenance identity
            diff = (m["requirement_mw"] - pub["as_req_mw"])[covered]
            exact = int((np.abs(diff - offset) < 1.0).sum())

            # (2) channel census
            shortfall_hours = int((m["shortfall_mw"].fillna(0).abs() > 1e-9).sum())
            dual = m["dual"].fillna(0.0)
            pos = set(int(h) for h in dual.index[dual > DUAL_EPS])

            # (3) overlap, three published severity tiers
            tiers = {
                "reality_reserve_priced_mcp_gt_0": set(
                    int(h) for h in pub.index[(pub["mcp_mean"] > 0.01).fillna(False)]
                ),
                "reality_ordc_step_5min_mcp_ge_300": set(
                    int(h) for h in pub.index[(pub["mcp_max"] >= 300.0).fillna(False)]
                ),
                "reality_short_total_lt_requirement": set(
                    int(h) for h in pub.index[(pub["short_intervals"] > 0).fillna(False)]
                ),
            }
            ov = {}
            for name, hrs in tiers.items():
                hits = len(pos & hrs)
                ov[name] = {
                    "reality_hours": len(hrs),
                    "base_rate": round(len(hrs) / n_cov, 6) if n_cov else None,
                    "overlap": hits,
                    "overlap_share_of_model": (
                        round(hits / len(pos), 4) if pos else None
                    ),
                    "lift_vs_base_rate": (
                        round((hits / len(pos)) / (len(hrs) / n_cov), 2)
                        if pos and hrs and n_cov
                        else None
                    ),
                    "hypergeom_p_ge": (
                        round(_hypergeom_sf(hits, n_cov, len(hrs), len(pos)), 12)
                        if pos and hrs and n_cov
                        else None
                    ),
                }

            # (4) magnitude and direction in the coincident hours
            coinc = sorted(pos & tiers["reality_reserve_priced_mcp_gt_0"])
            mag = None
            if coinc:
                md = dual.loc[coinc].to_numpy(dtype=float)
                pm = pub["mcp_mean"].loc[coinc].to_numpy(dtype=float)
                px = pub["mcp_max"].loc[coinc].to_numpy(dtype=float)
                mag = {
                    "n": len(coinc),
                    "model_dual_mean": round(float(md.mean()), 2),
                    "model_dual_max": round(float(md.max()), 2),
                    "published_mcp_hourly_mean": round(float(pm.mean()), 2),
                    "published_mcp_hourly_max": round(float(pm.max()), 2),
                    "published_mcp_5min_max": round(float(px.max()), 2),
                    "model_over_published_mean_ratio": (
                        round(float(md.mean() / pm.mean()), 3) if pm.mean() else None
                    ),
                    "hours_model_exceeds_published": int((md > pm).sum()),
                }

            yrec["families"][fam] = {
                "published_locale": locale,
                "covered_hours": n_cov,
                "requirement_identity": {
                    "claim": "model requirement_mw == published as_req_mw + published ORDC outer offset",
                    "offset_mw": offset,
                    "hours_matching_within_1mw": exact,
                    "hours_compared": int(diff.notna().sum()),
                    "median_diff_mw": round(float(np.nanmedian(diff)), 4),
                },
                "channel_census": {
                    "ordc_shortfall_hours": shortfall_hours,
                    "dual_max": round(float(dual.max()), 4),
                    "cheapest_ordc_penalty_step": min(penalties),
                    "dual_max_below_cheapest_penalty": bool(
                        float(dual.max()) < min(penalties)
                    ),
                    "channel": (
                        "ORDC shortfall penalty step"
                        if shortfall_hours
                        else "reserve/energy opportunity cost (no shortfall in any hour)"
                    ),
                },
                "model_positive_dual_hours": len(pos),
                "overlap": ov,
                "magnitude": mag,
                "c3c_load_bearing": {
                    "model_tail_hours": len(tail_hours),
                    "tail_hours_with_positive_dual": len(tail_hours & pos),
                    "share_of_tail": (
                        round(len(tail_hours & pos) / len(tail_hours), 4)
                        if tail_hours
                        else None
                    ),
                },
                "hour_table": [
                    {
                        "hour": int(h),
                        "model_dual": round(float(dual.loc[h]), 2),
                        "published_mcp_hourly_mean": (
                            None
                            if pd.isna(pub["mcp_mean"].loc[h])
                            else round(float(pub["mcp_mean"].loc[h]), 2)
                        ),
                        "published_mcp_5min_max": (
                            None
                            if pd.isna(pub["mcp_max"].loc[h])
                            else round(float(pub["mcp_max"].loc[h]), 2)
                        ),
                        "published_short_intervals": (
                            0
                            if pd.isna(pub["short_intervals"].loc[h])
                            else int(pub["short_intervals"].loc[h])
                        ),
                        "model_tail_hour": int(h) in tail_hours,
                    }
                    for h in sorted(pos)
                ],
            }

        out["years"][str(year)] = yrec

    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")

    for year in YEARS:
        y = out["years"][str(year)]
        print(f"\n=== {year} === model C3c tail {y['model_tail_hours_gt200']} h "
              f"({y['c3c_scored_basis']})")
        for fam, f in y["families"].items():
            o = f["overlap"]
            print(
                f"  {fam:16s} [{f['published_locale']}] pos-dual {f['model_positive_dual_hours']:3d} h | "
                f"identity {f['requirement_identity']['hours_matching_within_1mw']}/"
                f"{f['requirement_identity']['hours_compared']} | "
                f"shortfall h {f['channel_census']['ordc_shortfall_hours']} | "
                f"dual max ${f['channel_census']['dual_max']:.2f}"
            )
            for name, r in o.items():
                print(
                    f"      {name:38s} {r['overlap']:3d}/{f['model_positive_dual_hours']:<3d} "
                    f"base {r['base_rate']} lift {r['lift_vs_base_rate']} p {r['hypergeom_p_ge']}"
                )
            if f["magnitude"]:
                m = f["magnitude"]
                print(
                    f"      magnitude: model mean ${m['model_dual_mean']} max ${m['model_dual_max']} "
                    f"vs published hourly mean ${m['published_mcp_hourly_mean']} "
                    f"max ${m['published_mcp_hourly_max']} / 5-min ${m['published_mcp_5min_max']} "
                    f"(ratio {m['model_over_published_mean_ratio']}, model exceeds in "
                    f"{m['hours_model_exceeds_published']}/{m['n']} h)"
                )


if __name__ == "__main__":
    main()
