"""ERCOT-61 A/B comparison: keeper reconstruction (A) vs no-ST_GAS-markdowns (B).

Compares two solved 2023 throwaway bundles on the binding-regime (top-30 %
net-load) class mix vs CAMPD, the ST_GAS floor decomposition, where the freed
energy went (conservation counterpart), the storage dispatch, and the
evening/morning price spread — the ERCOT-60 §7.3 chain (thermal excess →
flat spread → storage windows).

Usage::

    python scripts/probes/_ercot61_ab_compare.py \
        [--a ercot61_stgas_drag_2023] [--b ercot61b_stgas_nodeltas_2023]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_rtolcap_forward import _class_hourly, _net_load  # noqa: E402

ROOT = REPO / "results" / "calibration"
YEAR = 2023
HOURS = 8760


def class_hourly_model(bundle: str) -> pd.DataFrame:
    """(klass, hour) MW pivot for one bundle's P1 pass."""
    disp = pd.read_parquet(
        ROOT / bundle / "dispatch" / f"{YEAR}_P1.parquet",
        columns=["pass", "klass", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]
    kl = (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(HOURS), fill_value=0.0)
    )
    return kl


def st_floor_mw(bundle: str) -> tuple[np.ndarray, np.ndarray]:
    """(on_floor_mw, total_mw) hourly series for ST_GAS plant-group rows."""
    fl = np.load(ROOT / bundle / "floors" / f"{YEAR}_P1.npz")
    min_gen, mech = fl["min_gen"].astype(float), fl["mechanism"]
    unit_ids, pgroup = fl["unit_ids"], fl["plant_group"]
    st = np.where(pgroup == "ST_GAS")[0]
    disp = pd.read_parquet(
        ROOT / bundle / "dispatch" / f"{YEAR}_P1.parquet",
        columns=["pass", "unit_id", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]
    sub = disp[disp["unit_id"].isin(set(unit_ids[st].tolist()))]
    piv = sub.pivot_table(
        index="unit_id", columns="hour", values="mw", observed=True
    ).reindex(index=list(unit_ids[st]), columns=range(HOURS), fill_value=0.0)
    P = piv.to_numpy(float)
    mg, mk = min_gen[st], mech[st]
    on = (mk == 6) & (mg > 1.0) & (P <= mg * 1.02 + 1.0)
    return np.where(on, P, 0.0).sum(axis=0), P.sum(axis=0)


def lw_price(bundle: str) -> np.ndarray:
    """Hourly load-weighted system price."""
    s = pd.read_parquet(ROOT / bundle / "system.parquet")
    if "pass" in s.columns:
        s = s[s["pass"] == "P1"]
    s = s[s["year"] == YEAR]
    g = s.groupby("hour").apply(
        lambda x: np.average(x["price"], weights=np.maximum(x["demand"], 1e-9)),
        include_groups=False,
    )
    v = np.zeros(HOURS)
    v[g.index.to_numpy()] = g.to_numpy()
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", default="ercot61_stgas_drag_2023")
    ap.add_argument("--b", default="ercot61b_stgas_nodeltas_2023")
    args = ap.parse_args()

    nl = _net_load(YEAR)[:HOURS]
    bind = nl >= np.percentile(nl, 70.0)
    hod = np.arange(HOURS) % 24

    _, _, _, _, online_gross = _class_hourly(YEAR, chp_export_basis=True)

    ka, kb = class_hourly_model(args.a), class_hourly_model(args.b)
    print(f"== A={args.a}  B={args.b}  ({YEAR}) ==")
    print("\n-- binding-hour mean MW by class: A / B / CAMPD --")
    for cls in (
        "COAL",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "storage",
    ):

        def m(kl):
            rows = [
                c
                for c in kl.index
                if (c.startswith("COAL") if cls == "COAL" else c == cls)
            ]
            return (
                kl.loc[rows].sum(axis=0).to_numpy()[:HOURS] if rows else np.zeros(HOURS)
            )

        a, b = m(ka), m(kb)
        meas = online_gross.get(cls, np.zeros(HOURS))[:HOURS]
        note = "" if cls in online_gross else " (no CAMPD)"
        print(
            f"  {cls:<11} A {a[bind].mean():8,.0f}   B {b[bind].mean():8,.0f}"
            f"   Δ {b[bind].mean() - a[bind].mean():+7,.0f}   CAMPD {meas[bind].mean():8,.0f}{note}"
        )

    print("\n-- annual class TWh: A / B --")
    for cls in ("ST_GAS", "CC_REGULAR", "CT_PEAKER", "COAL_PRB", "COAL_LIGNITE"):
        a = float(ka.loc[cls].sum()) / 1e6 if cls in ka.index else 0.0
        b = float(kb.loc[cls].sum()) / 1e6 if cls in kb.index else 0.0
        print(f"  {cls:<13} A {a:6.2f}   B {b:6.2f}   Δ {b - a:+6.2f}")

    on_a, tot_a = st_floor_mw(args.a)
    on_b, tot_b = st_floor_mw(args.b)
    print("\n-- ST_GAS floor decomposition, binding-hour mean MW: A -> B --")
    print(f"  total    {tot_a[bind].mean():7,.0f} -> {tot_b[bind].mean():7,.0f}")
    print(f"  on-floor {on_a[bind].mean():7,.0f} -> {on_b[bind].mean():7,.0f}")
    print(f"  annual on-floor TWh {on_a.sum() / 1e6:.2f} -> {on_b.sum() / 1e6:.2f}")
    print(f"  annual class TWh    {tot_a.sum() / 1e6:.2f} -> {tot_b.sum() / 1e6:.2f}")
    fs_a = on_a.sum() / max(tot_a.sum(), 1e-9)
    fs_b = on_b.sum() / max(tot_b.sum(), 1e-9)
    print(f"  forced share        {fs_a:.3f} -> {fs_b:.3f}")

    pa, pb = lw_price(args.a), lw_price(args.b)
    ev = np.isin(hod, range(17, 21))
    mo = np.isin(hod, range(2, 6))
    print("\n-- price formation (load-weighted) --")
    print(f"  annual mean: A {pa.mean():6.2f}  B {pb.mean():6.2f}")
    print(f"  binding-hour mean: A {pa[bind].mean():6.2f}  B {pb[bind].mean():6.2f}")
    spread_a = pa[ev].mean() - pa[mo].mean()
    spread_b = pb[ev].mean() - pb[mo].mean()
    print(
        f"  evening(17-20) minus morning(2-5) spread: A {spread_a:6.2f}  B {spread_b:6.2f}"
    )


if __name__ == "__main__":
    main()
