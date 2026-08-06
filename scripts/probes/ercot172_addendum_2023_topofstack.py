"""ERCOT-172 ADDENDUM (NO LP): what sets price in the 2023 hours the model misses.

Owner-authorised in-session addendum to the ercot-172 record. The standing ERCOT
object is C3a-2023 (**−29.9 %** on the hub basis, −32.2 % on the scorer's zonal
basis) and `FINDING-ercot166` §1 already localised it — Aug+Sep carry 88 % of the
annual gap, tail recall 0.30. This addendum asks the one question no session had
put to the delivery-2023 SCED corpus: **in the hours the model misses, what was
actually offered above the model's ceiling, and by whom?**

Two measurements, both no-LP, both on committed inputs:

* **M1 — the miss, priced.** For every 2023 hour with actual RT > $200 that the
  keeper prices ≤ $200, the actual and model price distributions. This is the
  object stated as a price gap rather than an hour count.
* **M2 — the real top-of-stack at those hours.** From the NP3-965 delivery-2023
  corpus (the ercot-157 intake that ercot-168/169/171 mined for coal), the MW
  offered at or above $200 / $500 / $1,000 / $2,000 on the SCED-applied
  incremental energy curves of ONLINE resources, split by ERCOT Resource Type.
  Scoped to Aug+Sep, the months `FINDING-ercot166` §1 measured as 88 % of the
  gap; the scope is stated, not silent (rule: no silent caps).

**This addendum does NOT overturn `ercot_storage_rt_offer_surface` = `R`
(ercot-162).** That refutation is structural and stands: a battery's cap-priced
SCED offer is an *equilibrium* object, and transplanted as an LP marginal cost
into a model whose prices never reach the cap it merely withholds the fleet
(discharge collapsed ~74 % in every year). M2 corroborates the ladder ercot-162
already derived; what it adds is the **composition and depth** of the stack the
model has to clear through, which is a quantity/scarcity-depth statement — the
destination ercot-162 itself re-pointed to.

Usage:
    python scripts/probes/ercot172_addendum_2023_topofstack.py \
        [--bundle results/calibration/ercot168_yearcurves_B] \
        [--out results/calibration/ercot172_addendum_2023_topofstack.json]

Rule 22 `[R-HOLDOUT]`: 2023 only, a training year. No LP, no network.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "data" / "raw" / "ercot" / "SCED"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
YEAR = 2023
THRESH = (200, 500, 1000, 2000)
MW_COLS = [f"SCED1 Curve-MW{i}" for i in range(1, 11)]
PR_COLS = [f"SCED1 Curve-Price{i}" for i in range(1, 11)]
ONLINE = {"ON", "ONRUC", "ONTEST", "ONREG"}
# Delivery month = corpus filename month − 2 (the ercot-169 keying). Delivery
# Aug/Sep 2023 therefore live in the 2023-10 / 2023-11 shards.
AUGSEP_SHARDS = "2023-1[01].part*.parquet"


def system_price(bundle: Path) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted model system price and zonal demand sum for ``YEAR``."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{YEAR}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    pr = sysf.pivot_table(index="hour", columns="zone", values="price").to_numpy()
    dm = sysf.pivot_table(index="hour", columns="zone", values="demand").to_numpy()
    return (pr * dm).sum(1) / dm.sum(1), dm.sum(1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/ercot168_yearcurves_B")
    ap.add_argument(
        "--out",
        default="results/calibration/ercot172_addendum_2023_topofstack.json",
    )
    args = ap.parse_args()

    model, load = system_price(REPO / args.bundle)
    act = pd.read_parquet(ACTUAL)
    actual = act[act.year == YEAR]["rt"].to_numpy(float)
    n = min(len(model), len(actual))
    model, actual, load = model[:n], actual[:n], load[:n]
    clock = pd.DatetimeIndex(
        pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31 23:00", freq="h")[:n]
    )

    # ---- M1: the miss, priced -------------------------------------------
    hi = actual > 200
    miss = hi & (model <= 200)
    pos = np.clip(actual - model, 0, None)
    m1 = {
        "actual_above_200_hours": int(hi.sum()),
        "model_caught_hours": int((hi & (model > 200)).sum()),
        "tail_recall": float((hi & (model > 200)).sum() / hi.sum()),
        "missed_hours": int(miss.sum()),
        "actual_in_missed": {
            "p50": float(np.median(actual[miss])),
            "mean": float(actual[miss].mean()),
            "max": float(actual[miss].max()),
        },
        "model_in_missed": {
            "p50": float(np.median(model[miss])),
            "mean": float(model[miss].mean()),
            "max": float(model[miss].max()),
        },
        "missed_share_of_positive_underpricing": float(
            (actual - model)[miss].sum() / pos.sum()
        ),
        "c3a_hub_basis_pct": float(
            100
            * ((model * load).sum() / load.sum() - (actual * load).sum() / load.sum())
            / ((actual * load).sum() / load.sum())
        ),
        "note": (
            "the model's MAX price across every missed hour is the headline: it "
            "never crosses $200 in an hour where ERCOT did"
        ),
    }
    print(
        f"M1: {m1['missed_hours']} missed of {m1['actual_above_200_hours']} "
        f"(recall {m1['tail_recall']:.2f}); actual p50 ${m1['actual_in_missed']['p50']:.0f} "
        f"vs model p50 ${m1['model_in_missed']['p50']:.1f}, model MAX "
        f"${m1['model_in_missed']['max']:.1f}"
    )

    # ---- M2: the real top-of-stack at those hours ------------------------
    sel = clock[miss]
    sel = sel[sel.month.isin([8, 9])]
    want = set(sel.strftime("%Y-%m-%d %H"))
    files = sorted(glob.glob(str(CORPUS / AUGSEP_SHARDS)))
    if not files:
        raise SystemExit(f"no delivery-Aug/Sep 2023 shards under {CORPUS}")
    frames = []
    for f in files:
        t = pq.read_table(
            f,
            columns=[
                "SCED Time Stamp",
                "Resource Type",
                "Telemetered Resource Status",
                *MW_COLS,
                *PR_COLS,
            ],
        ).to_pandas()
        ts = pd.to_datetime(
            t["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
        )
        # Corpus stamps are CPT; Aug/Sep is CDT, so CST = CPT − 1 h.
        key = (ts - pd.Timedelta(hours=1)).dt.strftime("%Y-%m-%d %H")
        keep = key.isin(want)
        if keep.any():
            sub = t[keep].copy()
            sub["cst_hour"] = key[keep]
            sub["stamp"] = t.loc[keep, "SCED Time Stamp"]
            frames.append(sub)
    df = pd.concat(frames, ignore_index=True)
    n_all = len(df)
    df = df[
        df["Telemetered Resource Status"].astype(str).str.upper().isin(ONLINE)
    ].copy()

    mw = df[MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy()
    pr = df[PR_COLS].apply(pd.to_numeric, errors="coerce").to_numpy()
    # The SCED curve is cumulative MW against price; difference to segments.
    seg = np.clip(np.diff(np.nan_to_num(mw, nan=0.0), axis=1, prepend=0.0), 0, None)
    intervals = df.groupby("cst_hour")["stamp"].nunique()

    m2 = {
        "scope": "delivery Aug+Sep 2023 (FINDING-ercot166 §1: 88% of the annual gap)",
        "missed_hours_in_scope": int(len(sel)),
        "corpus_rows": int(n_all),
        "online_rows": int(len(df)),
        "by_threshold": {},
    }
    for thr in THRESH:
        per_row = (seg * ((pr >= thr) & np.isfinite(pr))).sum(axis=1)
        s = pd.DataFrame(
            {"h": df["cst_hour"].to_numpy(), "t": df["Resource Type"].astype(str), "mw": per_row}
        )
        hourly = s.groupby("h")["mw"].sum() / intervals.reindex(
            s.groupby("h")["mw"].sum().index
        )
        by_t = s.groupby(["h", "t"])["mw"].sum().unstack(fill_value=0.0)
        by_t = by_t.div(intervals.reindex(by_t.index), axis=0)
        tops = by_t.mean().sort_values(ascending=False)
        m2["by_threshold"][str(thr)] = {
            "total_mw_mean": float(hourly.mean()),
            "total_mw_p10": float(hourly.quantile(0.10)),
            "total_mw_p50": float(hourly.median()),
            "total_mw_p90": float(hourly.quantile(0.90)),
            "by_resource_type_mw": {k: float(v) for k, v in tops.items() if v >= 1.0},
            "storage_share": float(tops.get("PWRSTR", 0.0) / hourly.mean()),
        }
        print(
            f"M2 >=${thr}: {hourly.mean():7.0f} MW offered, PWRSTR "
            f"{tops.get('PWRSTR', 0.0):.0f} MW "
            f"({100 * tops.get('PWRSTR', 0.0) / hourly.mean():.0f}%)"
        )

    rec = {
        "session": "ercot-172",
        "artifact": "addendum",
        "phase": 0,
        "lp_solved": False,
        "year": YEAR,
        "bundle": args.bundle,
        "object": "C3a-2023 mean-LMP under-run",
        "M1_the_miss_priced": m1,
        "M2_real_top_of_stack": m2,
        "does_not_overturn": (
            "ercot_storage_rt_offer_surface stays R (ercot-162). That refutation is "
            "structural — a cap-priced battery offer is an equilibrium object and "
            "transplanted as an LP marginal cost it only withholds the fleet. This "
            "addendum corroborates the ladder's composition and depth; it is a "
            "quantity/scarcity-depth statement, which is where ercot-162 itself "
            "re-pointed the residual."
        ),
    }
    (REPO / args.out).write_text(json.dumps(rec, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
