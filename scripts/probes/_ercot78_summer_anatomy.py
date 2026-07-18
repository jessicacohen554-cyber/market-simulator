"""ERCOT-78 leg 0/1: the 2023 summer over-shoot decomposition (no solve).

PRE-REGISTRATION (written BEFORE any measurement was run — the ERCOT-74/75
diagnosis-first pattern; this docstring is the lane's pre-committed target and
guard set):

* Decomposition targets — the 2023 payload-lw monthly residuals on the
  standing keeper (`2026-07-16-ercot73-state-wall`, byte-faithful replay
  verified C3-parity to the decimal this session): **Jun +14.8 $/MWh on
  actual 74.5** and **Sep +17.9 on actual 109.7** (companions: Jan +9.8 on
  26.4, Apr +9.2 on 23.9 — reported, not this lane's charter). The
  over-shoot predates every 2026-07 mechanism (ERCOT-73 traced the state
  wall's own contribution at ~+$1/mo: Jun +13.9 -> +14.8, Sep +16.9 ->
  +17.9).
* The decomposition SET (pre-committed): every Jun/Sep-2023 hour with
  ``model_lw - rt > $25`` (a clear per-hour over-pricing, roughly one
  std of the actual summer hourly price). For each: the marginal-row
  attribution (which class + mechanism family sets the zonal-max dual, by
  matching interior rows at the settled price), the hour's net-load
  percentile bin (the wall's 7-bin edges AND the peak surface's 4-bin
  edges), the measured commitment-loading state w (CC/CT/ST), and the
  actual side (RT, DA, NP6-905 lambda/adders).
* GUARDS (what a named mechanism must NOT break, pre-committed): the Aug-2023
  caught set (119 caught of 181; Aug carries the real event weeks) and the
  2023 C3c count parity (179 vs 181) — any charter that would stand down
  summer formation must show its window excludes the caught Aug/Sep real
  event hours; the 60 invented 2023 hours (all system prints, Jun 20 /
  Sep 10 / Aug 12 — measured in ERCOT-76 leg 0) are the same phenomenon's
  tail and should fall with it, never be chased separately.
* Exit conditions (either closes the lane for frontier purposes): (a) a NAMED
  measured mechanism with its own forward-native driver and zero fitted
  scalars, chartered for its own numbered lane; or (b) an adjudication that
  the over-shoot is out-of-representation / input-driven, ledgered with the
  per-hour evidence. A tuned haircut, scoped damper, or residual-identified
  parameter is forbidden (rules 1/13/14/23/26).

Usage::

    uv run python scripts/probes/_ercot78_summer_anatomy.py \
        [--bundle _ercot76_keeper_replay] [--months 6 9] [--over 25]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

ROOT = REPO / "results" / "calibration"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
RESERVES = REPO / "data" / "raw" / "ercot" / "ercot_2023_ordc_reserves_hourly.parquet"
STATE = (
    REPO / "data" / "raw" / "_validation-source" / "ercot_commitment_loading_state.json"
)

HOURS = 8760
_CAL = pd.date_range("2023-01-01", periods=HOURS, freq="h")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="_ercot76_keeper_replay")
    ap.add_argument("--months", type=int, nargs="+", default=[6, 9])
    ap.add_argument("--over", type=float, default=25.0)
    args = ap.parse_args()
    b = ROOT / args.bundle

    sysq = pd.read_parquet(b / "system.parquet")
    sysq = sysq[(sysq["pass"] == "P1") & (sysq["year"] == 2023)].copy()
    px = sysq.pivot_table(index="hour", columns="zone", values="price")
    dem = sysq.pivot_table(index="hour", columns="zone", values="demand")
    lw = (px * dem).sum(axis=1) / dem.sum(axis=1)

    act = pd.read_parquet(ACTUAL)
    a = act[act["year"] == 2023].set_index("hour").reindex(range(HOURS))
    rt = a["rt"].to_numpy(float)
    da = a["da"].to_numpy(float)

    res = pd.read_parquet(RESERVES).set_index("hour").reindex(range(HOURS))

    import json

    state = json.loads(Path(STATE).read_text())
    w_cc = np.array(state["CC"]["years"]["2023"], float)
    w_ct = np.array(state["CT"]["years"]["2023"], float)
    w_st = np.array(state["ST"]["years"]["2023"], float) if "ST" in state else None

    from derive_ercot_dam_cleared_share import _netload_pct

    pct = _netload_pct(2023)

    mo = _CAL.month.to_numpy()
    hod = np.arange(HOURS) % 24
    over = (lw.to_numpy() - rt > args.over) & np.isin(mo, args.months)
    hrs = np.flatnonzero(over)
    mass = float((lw.to_numpy() - rt)[hrs].sum())
    print(
        f"decomposition set: {len(hrs)} h with model_lw - rt > ${args.over:.0f} "
        f"in months {args.months}; $-mass {mass:,.0f} $/MWh-h "
        f"(x demand-weighting drives the +14.8/+17.9 monthly residuals)"
    )
    print(f"by month: {pd.Series(mo[hrs]).value_counts().sort_index().to_dict()}")
    print(f"by hod: {pd.Series(hod[hrs]).value_counts().sort_index().to_dict()}")

    # netload-bin distribution (wall edges) and state
    edges7 = np.array([0.25, 0.50, 0.70, 0.80, 0.90, 0.97])
    bins7 = np.searchsorted(edges7, pct[hrs], side="right")
    print(f"wall bin dist: {pd.Series(bins7).value_counts().sort_index().to_dict()}")
    print(
        "w on set: CC mean %.2f  CT %.2f  ST %s"
        % (
            w_cc[hrs].mean(),
            w_ct[hrs].mean(),
            f"{w_st[hrs].mean():.2f}" if w_st is not None else "n/a",
        )
    )
    print(
        "actual on set: rt mean %.1f  da mean %.1f  rtorpa mean %.2f; "
        "model lw mean %.1f"
        % (
            rt[hrs].mean(),
            da[hrs].mean(),
            res["rtorpa"].to_numpy(float)[hrs].mean(),
            lw.to_numpy()[hrs].mean(),
        )
    )

    # Marginal-row attribution: interior rows (0 < mw < row's own hourly max
    # dispatch this month, a bounds proxy) in the zmax zone whose zonal price
    # they plausibly set; report by class x tranche family.
    disp = pd.read_parquet(
        b / "dispatch" / "2023_P1.parquet",
        columns=["unit_id", "klass", "zone", "hour", "mw"],
    )
    dsub = disp[disp["hour"].isin(hrs)].copy()
    mx = disp.groupby("unit_id", observed=True)["mw"].max()
    dsub["mxu"] = dsub["unit_id"].map(mx)
    dsub["frac"] = dsub["mw"] / dsub["mxu"].clip(lower=1e-9)
    interior = dsub[(dsub["mw"] > 1.0) & (dsub["frac"] > 0.02) & (dsub["frac"] < 0.98)]
    fam = interior["unit_id"].str.rpartition("_")[2].str.rstrip("0123456789")
    tab = (
        interior.assign(fam=fam)
        .groupby(["klass", "fam"], observed=True)["hour"]
        .nunique()
        .sort_values(ascending=False)
    )
    print("\ninterior (candidate-marginal) rows on the set — hours present:")
    print(tab.head(20).to_string())


if __name__ == "__main__":
    main()
