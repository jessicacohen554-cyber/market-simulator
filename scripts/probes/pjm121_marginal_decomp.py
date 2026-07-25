"""pjm-121: WHICH class sets the price in each C3a-2025 residual stratum?

The pjm-120 finding measured *where* PJM's C3a-2025 residual lives — a monotone
dispersion compression: the model runs ~$10/MWh too HIGH in the 1,922 cheapest
hours and ~$17-$635/MWh too LOW in every expensive stratum. It did not measure
*what* sets the price in those hours. This probe does.

For a solved PJM bundle, hours are stratified by the ACTUAL RT price (the same
bins the pjm-120 readout uses, so the two tables line up row-for-row) and each
stratum is decomposed on the model's own supply position:

  1. **Marginal class attribution** — the class whose offer (the LP's own
     ``mc_base``, so this is the price the LP actually solved on) sits at the
     zonal clearing price, weighted by how often it is the setter. This answers
     "what is marginal in the 1,655 hours where actual is $50-100 and the model
     prints $48".
  2. **Stack headroom above the clearing price** — MW of available-but-idle
     supply offered within $0/$10/$25/$50 of the model price, by class. A thick
     shelf just above the dual is what pins a stratum's price down.
  3. **Floored MW by mechanism** (D-2 attribution, ``min_gen_mechanism``) — what
     is holding generation ON in the cheap strata, which is the other half of
     the compression (over-pricing when slack).

No LP re-solve: the fleet + offer arrays are rebuilt through the bundle's own
config exactly as ``_g22_idle_supply_audit.py`` does. Pure diagnostic (rule 16).

Usage:
    python scripts/probes/pjm121_marginal_decomp.py results/probes/pjm121_base_2025 \
        --year 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
# REPO itself must be on the path so ``scripts.lib.clean_io`` resolves as a
# package — without it the data/clean readers silently fall back and the
# measured overlays (east interface cut, ramp capability) refuse to load.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from market_sim.config.interchange_config import IMPORT_ZONE  # noqa: E402
from market_sim.data.floor_mechanisms import MECH_NAMES  # noqa: E402

#: Stratum edges shared with ``pjm120_c3a_stratum_readout.py`` so the marginal
#: attribution can be read directly against that finding's residual table.
BINS = [-1e9, 0, 25, 50, 100, 200, 376, 1e9]
LABS = ["<0", "0-25", "25-50", "50-100", "100-200", "200-376", ">376"]

#: Offer-price windows above the clearing price used for the headroom shelf.
SHELVES = (10.0, 25.0, 50.0)


def _actual_rt(year: int, hours: int) -> np.ndarray:
    """Return hourly measured PJM RT LMP ($/MWh), mean across nodes."""
    df = pd.read_parquet(REPO / f"data/clean/lmp/PJM/RTM/lmp_{year}.parquet")
    df = df[df["interval_start_local"].dt.year == year]
    act = df.groupby("interval_start_local")["lmp_usd_per_mwh"].mean().sort_index()
    out = np.full(hours, np.nan)
    v = act.to_numpy(float)[:hours]
    out[: len(v)] = v
    return out


def decompose(bundle: Path, year: int, meta: dict) -> dict:
    """Return the per-stratum marginal / headroom / floor decomposition."""
    from derive_pjm_ordc_overlay import _run_year_kwargs
    from run_calibration import run_year

    hours = int(meta["hours"])
    state = run_year(
        year, meta["iso"], hours, meta["gas_prices"][str(year)], **_run_year_kwargs(meta)
    )
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T) the LP's own offers
    avail = fa.pmax[:, None] * fa.availability  # (n_gen, T)
    uids = np.asarray(fa.unit_ids, dtype=object)
    ext_zone = IMPORT_ZONE.get(meta["iso"], "")

    grp = (
        np.asarray(fa.plant_group, dtype=object)
        if fa.plant_group is not None
        else np.array([""] * len(uids), dtype=object)
    )

    sysf = pd.read_parquet(bundle / "system.parquet")
    sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == "P1")]
    internal = sysf[sysf["zone"] != ext_zone]
    g = internal.groupby("hour")
    dem = g["demand"].sum()
    lw = (
        internal.assign(pd_=internal["price"] * internal["demand"])
        .groupby("hour")["pd_"]
        .sum()
        / dem
    )
    price = lw.to_numpy(float)  # (T,) load-weighted model system price
    load = dem.to_numpy(float)

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    disp = disp[disp["pass"] == "P1"]
    unit_zone = (
        disp.drop_duplicates("unit_id")
        .set_index("unit_id")["zone"]
        .reindex(uids)
        .astype(object)
        .fillna("")
        .to_numpy()
    )
    is_ext = unit_zone == ext_zone
    dmat = (
        disp[disp["unit_id"].isin(set(map(str, uids)))]
        .pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )

    mg = fa.min_gen if fa.min_gen is not None else np.zeros_like(avail)
    mech = (
        fa.min_gen_mechanism
        if fa.min_gen_mechanism is not None
        else np.zeros_like(avail, dtype=np.int8)
    )

    act = _actual_rt(year, hours)
    ok = np.isfinite(act) & np.isfinite(price)
    bin_of = pd.cut(pd.Series(act), bins=BINS, labels=LABS)

    classes = sorted({str(c) for c in grp[~is_ext] if str(c)})
    therm = ~is_ext

    out: dict = {"year": year, "strata": []}
    for lab in LABS:
        sel = np.where(ok & (bin_of == lab).to_numpy())[0]
        if len(sel) == 0:
            continue
        w = load[sel] / load[sel].sum()

        # --- 1. marginal attribution: units strictly interior to their bounds
        # (0 < dispatch < available) are the LP's own price setters. Weight each
        # hour equally across its interior units, then load-weight the hours.
        marg: dict[str, float] = {c: 0.0 for c in classes}
        near: dict[str, float] = {c: 0.0 for c in classes}
        for j, h in enumerate(sel):
            d, a, m = dmat[:, h], avail[:, h], mc[:, h]
            interior = therm & (d > 1.0) & (d < a - 1.0)
            # Restrict to offers actually at the clearing price (+/- $1) — an
            # interior unit far from the dual is a floor/ceiling artifact.
            at = interior & (np.abs(m - price[h]) <= 1.0)
            pick = at if at.any() else interior
            if not pick.any():
                continue
            cs, cnt = np.unique(grp[pick].astype(str), return_counts=True)
            share = cnt / cnt.sum()
            for c, s in zip(cs, share):
                if c in marg:
                    marg[c] += float(w[j] * s)
            # capacity-weighted variant (which class carries the interior MW)
            for c in set(cs):
                mm = pick & (grp.astype(str) == c)
                if c in near:
                    near[c] += float(w[j] * d[mm].sum())

        # --- 2. headroom shelf above the dual, by class
        shelf: dict[str, dict[str, float]] = {}
        idle = np.clip(avail[:, sel] - dmat[:, sel], 0.0, None)
        for c in classes:
            mm = therm & (grp.astype(str) == c)
            if not mm.any():
                continue
            row = {}
            for s in SHELVES:
                band = (mc[np.ix_(mm, sel)] > price[sel][None, :] - 0.01) & (
                    mc[np.ix_(mm, sel)] <= price[sel][None, :] + s
                )
                row[f"idle_within_{int(s)}_gw"] = float(
                    (idle[mm] * band).sum(axis=0).mean() / 1e3
                )
            row["idle_gw"] = float(idle[mm].sum(axis=0).mean() / 1e3)
            row["disp_gw"] = float(dmat[np.ix_(mm, sel)].sum(axis=0).mean() / 1e3)
            shelf[c] = row

        # --- 3. floored MW by mechanism (D-2)
        floored = np.minimum(mg[:, sel], dmat[:, sel])
        binding = (mg[:, sel] > 1.0) & (dmat[:, sel] <= mg[:, sel] + 1.0)
        fl: dict[str, float] = {}
        for mid in np.unique(mech[:, sel]):
            if int(mid) == 0:
                continue
            mm = (mech[:, sel] == mid) & binding & therm[:, None]
            gw = float((floored * mm).sum(axis=0).mean() / 1e3)
            if gw > 0.005:
                fl[MECH_NAMES.get(int(mid), str(int(mid)))] = gw

        out["strata"].append(
            {
                "bin": lab,
                "hours": int(len(sel)),
                "model_lw": float((price[sel] * w).sum()),
                "actual_lw": float((act[sel] * w).sum()),
                "load_gw": float((load[sel] * w).sum() / 1e3),
                "marginal_share": {k: round(v, 4) for k, v in marg.items() if v > 1e-4},
                "interior_gw": {
                    k: round(v / 1e3, 3) for k, v in near.items() if v > 1.0
                },
                "shelf": shelf,
                "floored_gw": {k: round(v, 3) for k, v in sorted(fl.items())},
            }
        )
    return out


def _report(res: dict) -> None:
    """Print the decomposition tables."""
    print(f"\n########## {res['year']} marginal decomposition ##########")
    for s in res["strata"]:
        print(
            f"\n=== actual {s['bin']} | {s['hours']} h | load {s['load_gw']:.1f} GW "
            f"| model ${s['model_lw']:.1f} vs actual ${s['actual_lw']:.1f} ==="
        )
        ms = sorted(s["marginal_share"].items(), key=lambda kv: -kv[1])
        print(
            "  price-setting class share: "
            + ", ".join(f"{k} {v * 100:.0f}%" for k, v in ms[:6])
        )
        sh = sorted(
            s["shelf"].items(), key=lambda kv: -kv[1].get("idle_within_25_gw", 0.0)
        )
        print("  headroom shelf above the dual (GW idle offered within $X):")
        print(
            f"    {'class':<18}{'+$10':>8}{'+$25':>8}{'+$50':>8}{'idle':>8}{'disp':>8}"
        )
        for c, r in sh[:7]:
            print(
                f"    {c:<18}{r['idle_within_10_gw']:>8.2f}{r['idle_within_25_gw']:>8.2f}"
                f"{r['idle_within_50_gw']:>8.2f}{r['idle_gw']:>8.2f}{r['disp_gw']:>8.2f}"
            )
        if s["floored_gw"]:
            fl = sorted(s["floored_gw"].items(), key=lambda kv: -kv[1])
            print(
                "  binding floors (GW): "
                + ", ".join(f"{k} {v:.2f}" for k, v in fl[:6])
            )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    years = args.year or meta["years"]
    allres = []
    for y in years:
        if not (args.bundle / "dispatch" / f"{y}_P1.parquet").exists():
            print(f"{y}: no dispatch parquet — skipping")
            continue
        r = decompose(args.bundle, int(y), meta)
        _report(r)
        allres.append(r)
    p = args.bundle / "pjm121_marginal_decomp.json"
    p.write_text(json.dumps(allres, indent=1))
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
