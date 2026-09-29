"""SPP-102 phase 0 (zero LP), part 2: can commitment PHYSICS (min-down, start cost) reach the gap?

For every missing-commitment CC plant-hour inside actual-RT <= $15 hours (CEMS online, keeper off; the
SPP-102 object), report:
  * the length of the keeper's own off-gap containing it (what a relaxed-UC min-down / start-cost
    constraint could hold across), bucketed <= 8 h (ASOM gas min-down, FINDING-spp-83 §2),
    <= L* (start-cost break-even), and longer;
  * the length of the CEMS online spell containing it;
  * the same-hour DA LMP (> $15 = the market's own day-ahead SCUC priced the hour above the bucket).
L* = S / ((mc - p) * pmin_frac) with S the keeper's own CC committed-tranche start cost (50 $/MW,
SPP-73 M4), pmin 0.209 (SPP-44), (mc - p) = the keeper's CC offer at the plant minus the MODEL price.
The CC offer cost per plant is approximated by the fleet median CC offer in `_spp89` (not re-derived):
we use the per-year break-even at the median spread, reported alongside, never gated.
Also: CEMS CC OFF-spell length distribution (the empirical min-down).
Writes docs/handoffs/spp102/trough_physics.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp102_cc_commitment_drivers import (  # noqa: E402
    LOW,
    MIN_LOAD,
    ON_CEMS,
    ON_MODEL,
    YEARS,
    dec,
    spells,
)
import gzip  # noqa: E402

S_CC = 50.0  # $/MW per start, keeper CC committed tranche (SPP-73 M4)
MIN_DOWN = 8  # h, SPP MMU ASOM gas min-down (FINDING-spp-83 §2)


def runs(mask: np.ndarray) -> np.ndarray:
    """Length of the True-run each hour belongs to (0 where False)."""
    return spells(mask)


def main() -> int:
    """Bucket the missing-commitment plant-hours by gap length, spell length and DA price."""
    pay = json.load(open(sys.argv[1]))
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    out = {}
    for y in YEARS:
        L = lmp[lmp.year == int(y)].set_index("hour").reindex(range(8760))
        rt, da = L["rt"].to_numpy(float), L["da"].to_numpy(float)
        low = rt <= LOW
        sysf = pd.read_parquet(
            REPO / f"results/calibration/spp100_arm_span/hourly/system_{y}.parquet"
        )
        sysf = sysf[sysf["pass"] == "P1"]
        mprice = (
            (
                sysf.groupby("hour").apply(
                    lambda g: np.average(g.price, weights=g.demand)
                )
            )
            .reindex(range(8760))
            .to_numpy()
        )
        b = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz")
        )["bench"]["plants"]
        mp = pay["years"][y]["plants"]
        acc = dict(
            gap_twh=0.0,
            in_gap_le8=0.0,
            in_gap_le24=0.0,
            in_gap_gt24=0.0,
            never_on=0.0,
            da_gt15=0.0,
            cems_spell_gt48=0.0,
        )
        off_spells, mprice_gap = [], []
        for k, v in b.items():
            if (
                v["group"] != "CC_REGULAR"
                or v.get("nodata") in (True, "True")
                or not v.get("campd")
            ):
                continue
            key = k if k in mp else f"{k}:CC_REGULAR"
            if key not in mp:
                continue
            c, m = dec(v["campd"]), dec(mp[key]["m"])
            npl = float(v["npl"])
            on, mon = c >= ON_CEMS, m >= ON_MODEL
            gap = on & ~mon & low
            e = MIN_LOAD * npl / 1e6
            glen = runs(~mon)
            # a model off-run bounded by model-on hours on both sides is a gap; otherwise never-on segment
            idx = np.flatnonzero(~mon)
            bounded = np.zeros(8760, bool)
            if len(idx):
                br = np.flatnonzero(np.diff(idx) > 1)
                for s_, e_ in zip(np.r_[idx[0], idx[br + 1]], np.r_[idx[br], idx[-1]]):
                    if s_ > 0 and e_ < 8759:
                        bounded[s_ : e_ + 1] = True
            acc["gap_twh"] += gap.sum() * e
            acc["in_gap_le8"] += (gap & bounded & (glen <= MIN_DOWN)).sum() * e
            acc["in_gap_le24"] += (gap & bounded & (glen <= 24)).sum() * e
            acc["in_gap_gt24"] += (gap & bounded & (glen > 24)).sum() * e
            acc["never_on"] += (gap & ~bounded).sum() * e
            acc["da_gt15"] += (gap & (da > LOW)).sum() * e
            acc["cems_spell_gt48"] += (gap & (spells(on) > 48)).sum() * e
            ii = np.flatnonzero(~on)
            if len(ii):
                br = np.flatnonzero(np.diff(ii) > 1)
                off_spells += [
                    e_ - s_ + 1
                    for s_, e_ in zip(np.r_[ii[0], ii[br + 1]], np.r_[ii[br], ii[-1]])
                ]
            mprice_gap.append(mprice[gap])
        acc = {k: round(float(v), 3) for k, v in acc.items()}
        os_arr = np.array(off_spells)
        acc["cems_off_spell_h_p10_p25_p50"] = (
            [float(np.percentile(os_arr, q)) for q in (10, 25, 50)]
            if len(os_arr)
            else None
        )
        acc["cems_off_spells_le8_share"] = (
            round(float((os_arr <= 8).mean()), 3) if len(os_arr) else None
        )
        mg = np.concatenate(mprice_gap) if mprice_gap else np.array([])
        acc["model_price_med_in_gap"] = (
            round(float(np.median(mg)), 2) if len(mg) else None
        )
        acc["actual_rt_med_low"] = round(float(np.median(rt[low])), 2)
        acc["actual_da_med_low"] = round(float(np.median(da[low])), 2)
        out[y] = acc
        print(y, acc)
    (REPO / "docs/handoffs/spp102/trough_physics.json").write_text(
        json.dumps(out, indent=1)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
