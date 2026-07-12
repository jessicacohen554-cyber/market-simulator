"""ERCOT-63 anatomy: coal-shuffle decomposition + bridge anchor evidence.

Supplements ``_ercot62_lowcurve_analyze.py`` (which scores the §6 table) with
the two adjudications this session must make on evidence:

1. **Coal reconciliation anatomy (charter step 4).** Where does the probe's
   coal delta vs the keeper reconstruction come from — energy AT the coal
   floors (impossible: floors bind) or ABOVE them (merit-order displacement
   by the marked-down / floored gas rows)? And which gas rows GAIN the
   energy (committed tranches vs econ rungs vs peak)? Reads the two bundles'
   ``dispatch/<year>_P1.parquet`` (row grain: klass + unit) + the coal
   floors from ``floors/<year>_P1.npz`` when present.

2. **Startup-aware drop-with-cause evidence (charter step 2).** The anchor
   run-length distribution of the bridged CC plants: if the runs the bridge
   anchors on are day-scale (>= several hours serving real load), the
   phantom-micro-run failure mode the CAISO startup-aware screen guards is
   empirically absent here, and the screen (which refuses every ERCOT
   anchor — the 62b silent no-op) is dropped with cause rather than
   re-thresholded. Approximated from the P1 dispatch run pattern adjacent
   to each floored segment (P0 is not persisted; P0/P1 share the LP and
   differ only in the startup-markup objective, so run/idle patterns agree
   at this grain).

Rule-16 diagnostic; no LP solve; never registered.

Usage::

    python scripts/probes/_ercot63_anatomy.py --a ercot63_keeper_2023 \
        --b ercot63_bridge_md_2023 [--year 2023]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_GAS_COMMITMENT_BRIDGE,
    MECH_NAMES,
)

COAL = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL")


def unit_hourly(bundle: Path, year: int) -> pd.DataFrame:
    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    return disp[disp["pass"] == "P1"] if "pass" in disp.columns else disp


def floors(bundle: Path, year: int):
    p = bundle / "floors" / f"{year}_P1.npz"
    if not p.exists():
        return None
    return np.load(p, allow_pickle=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", default="ercot63_keeper_2023")
    ap.add_argument("--b", default="ercot63_bridge_md_2023")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()
    root = REPO / "results" / "calibration"
    A, B = root / args.a, root / args.b

    da = unit_hourly(A, args.year)
    db = unit_hourly(B, args.year)
    print(f"== ERCOT-63 anatomy — {args.a} vs {args.b}, {args.year} ==")
    print("dispatch columns:", sorted(da.columns))

    # --- 1. coal delta anatomy -------------------------------------------
    unit_col = "unit" if "unit" in da.columns else "unit_id"
    for src, d in (("A", da), ("B", db)):
        coal = d[d["klass"].isin(COAL)]
        print(
            f"  {src} coal annual: "
            + ", ".join(
                f"{k} {v / 1e6:.2f} TWh"
                for k, v in coal.groupby("klass", observed=True)["mw"].sum().items()
            )
        )
    # per-unit coal delta: top losers
    ca = da[da["klass"].isin(COAL)].groupby(unit_col, observed=True)["mw"].sum()
    cb = db[db["klass"].isin(COAL)].groupby(unit_col, observed=True)["mw"].sum()
    delta = (cb - ca.reindex(cb.index).fillna(0.0)).sort_values()
    print("\n-- top coal per-unit deltas (GWh, B - A) --")
    print((delta / 1e3).head(10).to_string())

    # gas gains by tranche kind (unit_id suffix: committed / econc* / peak /
    # mustrun)
    def tranche_kind(uid: str) -> str:
        tail = uid.rsplit("_", 1)[-1]
        if tail.startswith("econc"):
            return "econ"
        return tail

    gas = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS")
    ga = da[da["klass"].isin(gas)].copy()
    gb = db[db["klass"].isin(gas)].copy()
    ga["kind"] = ga[unit_col].map(tranche_kind)
    gb["kind"] = gb[unit_col].map(tranche_kind)
    ta = ga.groupby(["klass", "kind"], observed=True)["mw"].sum()
    tb = gb.groupby(["klass", "kind"], observed=True)["mw"].sum()
    td = (tb - ta.reindex(tb.index).fillna(0.0)) / 1e6
    print("\n-- gas annual TWh delta by class x tranche kind (B - A) --")
    print(td[td.abs() > 0.005].to_string())

    # --- 2. bridge floor + anchor evidence (bundle B) ---------------------
    fz = floors(B, args.year)
    if fz is None:
        print("\n(no floors npz in B — skipping anchor evidence)")
        return
    print("\nfloors npz keys:", sorted(fz.keys()))
    mech = fz["mechanism"] if "mechanism" in fz else None
    mg = fz["min_gen"] if "min_gen" in fz else None
    if mech is None or mg is None:
        return
    is_bridge = mech == MECH_GAS_COMMITMENT_BRIDGE
    print(
        f"bridge unit-hours {int(is_bridge.sum())}, floor volume "
        f"{float(np.where(is_bridge, mg, 0.0).sum()) / 1e6:.2f} TWh "
        f"({MECH_NAMES[MECH_GAS_COMMITMENT_BRIDGE]})"
    )
    # floored-segment lengths (the bridged gaps) + adjacent P1 run lengths
    seg_lengths: list[int] = []
    anchor_runs: list[int] = []
    rows = np.flatnonzero(is_bridge.any(axis=1))
    units = fz["unit_ids"] if "unit_ids" in fz else None
    # rebuild per-row dispatch from the parquet for anchor runs
    dbu = db.set_index([unit_col, "hour"])["mw"]
    for g in rows:
        m = is_bridge[g]
        edges = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
        starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        seg_lengths += [int(e - s) for s, e in zip(starts, ends)]
        if units is None:
            continue
        uid = str(units[g])
        try:
            series = dbu.loc[uid].reindex(range(m.size)).fillna(0.0).to_numpy()
        except KeyError:
            continue
        on = series > 1e-3
        redges = np.diff(np.concatenate(([0], on.astype(np.int8), [0])))
        rs, re = np.flatnonzero(redges == 1), np.flatnonzero(redges == -1)
        for s, e in zip(starts, ends):
            for a, b in zip(rs, re):
                if b == s or a == e:  # run abuts the floored gap
                    anchor_runs.append(int(b - a))
    seg = np.array(seg_lengths)
    print(
        f"bridged gaps: n {seg.size}, len p10/p50/p90 "
        f"{np.percentile(seg, [10, 50, 90]).round(1).tolist() if seg.size else '—'}, "
        f">24h {int((seg > 24).sum()) if seg.size else 0}"
    )
    if anchor_runs:
        ar = np.array(anchor_runs)
        print(
            f"anchor runs (P1-adjacent): n {ar.size}, len p10/p50/p90 "
            f"{np.percentile(ar, [10, 50, 90]).round(1).tolist()}, "
            f"<4h share {float((ar < 4).mean()):.3f} "
            "(phantom-micro-run evidence for the startup-aware adjudication)"
        )


if __name__ == "__main__":
    main()
