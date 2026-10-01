#!/usr/bin/env python3
"""NYISO-NEXT-8 phase 0 (ZERO LP): the HQ accounting duplicate in the import ladder.

Measures, for every year the ladder carries (2018-2025):

1. that ``SCH - HQ_IMPORT_EXPORT`` duplicates ``SCH - HQ - NY`` (corr, share of
   hours equal within 0.5 MW, mean of each);
2. that the committed producer (duplicate INCLUDED) reproduces the committed
   ``IMPORT_TRANCHES_BY_YEAR["NYISO"]`` rungs exactly (so the re-derivation is the
   same frozen formula with one input corrected, not a re-fit);
3. the re-derived ladder with the duplicate EXCLUDED (the corrected producer), and the producer's own
   ``offline_score`` old vs new;
4. the always-on 900 MW ``HQ_hydro`` firm floor against the measured net import
   (share of hours below 900 MW, p1/p5, min) and against the HQ seam alone.

Writes ``results/phase0/nyiso/_nyisonext8_phase0.json``. Reads only committed
measured inputs; no solve, no bundle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_nyiso_import_tranches as dnit  # noqa: E402
from market_sim.data.nyiso_par_attribution import ACCOUNTING_DUPLICATE  # noqa: E402
from market_sim.model.interchange.spec import (  # noqa: E402
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
)

YEARS = tuple(range(2018, 2026))
HQ_ROW = "SCH - HQ - NY"
OUT = REPO / "results" / "phase0" / "nyiso" / "_nyisonext8_phase0.json"


def _pivot(year: int) -> pd.DataFrame:
    df = pd.read_csv(dnit.FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    df["t"] = pd.to_datetime(df["interval_start_local"])
    piv = df.pivot_table(
        index="t", columns="interface", values="flow_mw", aggfunc="mean"
    )
    piv["hoy"] = (piv.index.dayofyear - 1) * 24 + piv.index.hour
    return piv.groupby("hoy").mean().reindex(range(8760))


def _net(piv: pd.DataFrame, seams: dict[str, list[str]]) -> np.ndarray:
    return sum(
        piv[[c for c in cols if c in piv.columns]].sum(axis=1)
        for cols in seams.values()
    ).to_numpy(dtype=float)


def _seams_with_duplicate() -> dict[str, list[str]]:
    """The pre-NEXT-8 row set: the corrected seams plus the HQ accounting duplicate."""
    return {
        k: v + ([ACCOUNTING_DUPLICATE] if k == "HQ" else [])
        for k, v in dnit.EXTERNAL_SEAMS.items()
    }


def _floor(net: np.ndarray) -> dict[str, float]:
    x = net[~np.isnan(net)]
    return {
        "mean": float(x.mean()),
        "min": float(x.min()),
        "p1": float(np.percentile(x, 1)),
        "p5": float(np.percentile(x, 5)),
        "share_below_900": float((x < dnit.FIRM_BASE_MW).mean()),
        "share_below_0": float((x < 0).mean()),
    }


def main() -> None:
    old_seams = _seams_with_duplicate()
    new_seams = dnit.EXTERNAL_SEAMS
    out: dict = {"years": {}, "duplicate_row": ACCOUNTING_DUPLICATE}
    nets_old, nets_new, das = {}, {}, {}
    for y in YEARS:
        piv = _pivot(y)
        da = dnit.load_da_lmp(y)
        dup, hq = piv[ACCOUNTING_DUPLICATE].to_numpy(float), piv[HQ_ROW].to_numpy(float)
        m = ~np.isnan(dup) & ~np.isnan(hq)
        n_old, n_new = _net(piv, old_seams), _net(piv, new_seams)
        # the corrected producer's own loader must equal n_new (identity check)
        assert np.allclose(np.nan_to_num(dnit.load_net_import(y)), np.nan_to_num(n_new))
        old_r, new_r = dnit.derive(n_old, da), dnit.derive(n_new, da)
        committed = [tuple(r) for r in IMPORT_TRANCHES_BY_YEAR["NYISO"][y]]
        hq_seam = (
            piv[[c for c in new_seams["HQ"] if c in piv.columns]]
            .sum(axis=1)
            .to_numpy(float)
        )
        out["years"][y] = {
            "dup_corr": float(np.corrcoef(dup[m], hq[m])[0, 1]),
            "dup_equal_within_0p5_share": float((np.abs(dup[m] - hq[m]) <= 0.5).mean()),
            "dup_mean_mw": float(np.nanmean(dup)),
            "hq_ny_mean_mw": float(np.nanmean(hq)),
            "net_old_mean_mw": float(np.nanmean(n_old)),
            "net_new_mean_mw": float(np.nanmean(n_new)),
            "committed_reproduced_exactly": [tuple(r) for r in old_r] == committed,
            "ladder_old": old_r,
            "ladder_new": new_r,
            "offline_old": dnit.offline_score(n_old, da, old_r),
            # the correct scoring target is the TRUE net import in both cases
            "offline_old_vs_true": dnit.offline_score(n_new, da, old_r),
            "offline_new": dnit.offline_score(n_new, da, new_r),
            "floor_total_net_new": _floor(n_new),
            "hq_seam_new": _floor(hq_seam),
        }
        nets_old[y], nets_new[y], das[y] = n_old, n_new, da
    pool = (2023, 2024, 2025)
    po = np.concatenate([nets_old[y] for y in pool])
    pn = np.concatenate([nets_new[y] for y in pool])
    pd_ = np.concatenate([das[y] for y in pool])
    old_p, new_p = dnit.derive(po, pd_), dnit.derive(pn, pd_)
    out["pooled_2023_2025"] = {
        "committed_reproduced_exactly": [tuple(r) for r in old_p]
        == [tuple(r) for r in IMPORT_TRANCHES["NYISO"]],
        "ladder_old": old_p,
        "ladder_new": new_p,
        "offline_old_vs_true": dnit.offline_score(pn, pd_, old_p),
        "offline_new": dnit.offline_score(pn, pd_, new_p),
    }
    OUT.write_text(json.dumps(out, indent=1, default=float))
    for y, r in out["years"].items():
        print(
            y,
            f"corr {r['dup_corr']:.3f} eq {r['dup_equal_within_0p5_share']:.2f}",
            f"net {r['net_old_mean_mw']:.0f}->{r['net_new_mean_mw']:.0f}",
            "repro",
            r["committed_reproduced_exactly"],
            f"dur_rmse {r['offline_old_vs_true']['dur_rmse']:.0f}->{r['offline_new']['dur_rmse']:.0f}",
            f"twh {r['offline_old_vs_true']['sim_twh']:.2f}/{r['offline_new']['sim_twh']:.2f}/{r['offline_new']['act_twh']:.2f}",
            f"hcorr {r['offline_old_vs_true']['hourly_corr']:.2f}->{r['offline_new']['hourly_corr']:.2f}",
            f"<900 {r['floor_total_net_new']['share_below_900']:.3f} min {r['floor_total_net_new']['min']:.0f}",
            f"HQmean {r['hq_seam_new']['mean']:.0f}",
        )
        print("   old", [p for _, _, p in r["ladder_old"]], r["ladder_old"][-1][1])
        print("   new", [p for _, _, p in r["ladder_new"]], r["ladder_new"][-1][1])
    print("pooled repro", out["pooled_2023_2025"]["committed_reproduced_exactly"])
    print("   old", out["pooled_2023_2025"]["ladder_old"])
    print("   new", out["pooled_2023_2025"]["ladder_new"])


if __name__ == "__main__":
    main()
