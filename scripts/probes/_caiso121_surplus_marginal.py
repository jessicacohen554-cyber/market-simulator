"""caiso-121 — WHICH unit sets the model's lambda in the ACTUAL market's SURPLUS regime?

FINDING-caiso120 Inv 4 left the load-bearing question open: in the belly hours
where the real CAISO is long and hub-priced (measured RT <= $20, ~half of belly
hours), the keeper clears $7-14 ABOVE the raw min-hub while importing 2.1-3.4 GW.
WHICH rung sets that lambda? The named candidates were (a) a border-carbon-paying
import tranche (CARB adder ~$12-15 ~ the observed wedge), (b) domestic gas at a
floor/min-load block, (c) storage-charge opportunity cost, (d) hydro shadow value.

Method — the caiso-105 PIN-AWARE attribution, re-pointed at the REGIME split:

  * Interiority is measured against the LP's OWN bounds — ``min_gen`` from the
    bundle's ``floors/<year>_P1.npz`` (what the P1 LP actually saw, RA-bridge and
    commitment floors included) and caps from the ``run_year(fleet_only=True)``
    reconstruction (pmax x availability: outage windows and temp-derates
    included). NEVER a p99 interior proxy — that proxy is what produced the
    caiso-103 attribution artifact FINDING-caiso104 §2 had to retract.
  * A unit PINNED at its bounds (min_gen == cap) or sitting AT a bound cannot
    set lambda, by LP optimality. A unit STRICTLY interior has, at the optimum,
    offer == its own zone's lambda. So "which class is interior" IS "which class
    is marginal", read off the LP rather than inferred.
  * Conditioning is on the ACTUAL market's regime (measured RT, not the model's
    own residual): surplus = belly hour with RT <= $20, firm = RT > $20. This is
    the caiso-120 split, so the rows here compose directly with its Table 2.

Deliberately NOT conditioned on the model residual (the caiso-105 Q1 form): the
question is what the model does in the hours REALITY prices as surplus, which is
a fact about the actual market, not about where the model happens to miss.

Reported per year x regime:
  1. TRUE-BOUNDS interior share of hours by class + interior MW, with the at-cap
     and pinned shares alongside, so "not marginal" is as visible as "marginal".
  2. PER-IMPORT-TRANCHE interiority — names the specific rung, with its own
     hour-varying offer, rather than a class average over a 6-tranche ladder.
  3. The zonal ladder: every zone's lambda incl. the two WECC corridor nodes,
     plus whether CA lambda is EQUALIZED to a WECC node (import rung marginal,
     corridor slack) or strictly ABOVE every node (corridor bound).
  4. Renewable curtailment: is wind/solar strictly interior to its own cf x cap
     bound? A curtailing renewable prices the hour at its MC ~ 0, which is how
     reality reaches a negative belly; the model holding lambda above zero with
     renewables AT cap is the missing surplus-regime behaviour.
  5. min_gen MECHANISM attribution for the pinned units, so a "pinned" class is
     traceable to the mechanism that pinned it (the D-2 question).

NO LP is built or solved; NO mechanism is armed (derive-first, rule 1/19 — any
mechanism this selects is filed as a separate owner ask).

Usage:
    python scripts/probes/_caiso121_surplus_marginal.py <bundle_dir> \
        [--recipe-from <bundle>] [--years 2023 2024 2025]

Finding: results/calibration/FINDING-caiso121-surplus-marginal-attribution-2026-07-26.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso105_evening_q1_pin import fleet_state  # noqa: E402

ACT = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
HUB = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"
KEEPER = REPO / "results/calibration/caiso_netrev_margin"

CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
BELLY = (10, 11, 12, 13, 14, 15)  # caiso-120 lane convention
SURPLUS_THRESHOLD = 20.0  # $/MWh — the caiso-120 regime split point
# Intertie tie-break epsilon: flows carry an epsilon cost, so an "equalized"
# (import-marginal, corridor-slack) hour sits within a few epsilon of a hub.
EQ_TOL = 0.5  # $/MWh (the caiso-105 value)
T = 8760


def _actual_rt(year: int) -> np.ndarray:
    a = pd.read_parquet(ACT)
    return a[a.year == year].set_index("hour").rt.reindex(range(T)).to_numpy(float)


def _min_hub(year: int) -> np.ndarray:
    """(T,) min of the measured MALIN / PALOVRDE hub prices.

    The measured series carries gaps (2023: 2040 all-NaN hours), so every
    consumer of this array must reduce with a nan-aware statistic.
    """
    h = pd.read_parquet(HUB)
    h = h[h.year == year].pivot(index="hour", columns="hub", values="price")
    return h.min(axis=1).reindex(range(T)).to_numpy(float)


def _bounds_and_dispatch(bundle: Path, year: int, recipe: Path):
    """LP bounds + realized dispatch, aligned on the floors npz unit order."""
    npz = np.load(bundle / "floors" / f"{year}_P1.npz")
    ids = [str(u) for u in npz["unit_ids"]]
    min_gen = np.asarray(npz["min_gen"], dtype=float)  # (n, T)

    state = fleet_state(recipe, year)
    fa = state["fleet_arrays"]
    s_ids = [str(u) for u in fa.unit_ids]
    cap = fa.pmax[:, None] * fa.availability
    # mc_base is (n,) for a flat-cost fleet and (n, T) once any hour-varying
    # offer path is armed (hub-basis overlay, net-revenue margin, conditional
    # offer surface — all on in this keeper). Normalise to (n, T) so no hour's
    # offer is averaged away.
    mc0 = np.asarray(state["mc_base"], dtype=float)
    if mc0.ndim == 1:
        mc0 = np.repeat(mc0[:, None], T, axis=1)
    mech = np.asarray(getattr(fa, "min_gen_mechanism", []), dtype=object)
    if s_ids != ids:
        pos = {u: i for i, u in enumerate(s_ids)}
        sel = [pos[u] for u in ids]
        cap, mc0 = cap[sel], mc0[sel]
        if mech.size == len(s_ids):
            mech = mech[sel]

    d = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["unit_id", "klass", "zone", "hour", "mw"],
    )
    d = d[d.unit_id.isin(set(ids))]
    uidx = {u: i for i, u in enumerate(ids)}
    mw = np.zeros((len(ids), T))
    mw[d.unit_id.map(uidx).to_numpy(int), d.hour.to_numpy(int)] = d.mw.to_numpy(float)
    kl = dict(d[["unit_id", "klass"]].drop_duplicates().itertuples(index=False))
    zo = dict(d[["unit_id", "zone"]].drop_duplicates().itertuples(index=False))
    klass = np.array([kl.get(u, "?") for u in ids], dtype=object)
    zone = np.array([zo.get(u, "?") for u in ids], dtype=object)
    return mw, min_gen, cap, mc0, ids, klass, zone, mech, state


def _zone_lambda(bundle: Path, year: int) -> pd.DataFrame:
    """(T, n_zone) zonal lambda from the dispatch frame's own ``lmp`` column.

    ``system.parquet`` is written only after the LAST year of a run, so a probe
    that must read a mid-run bundle takes the price from the per-generator-hour
    frame instead: ``_dispatch_frame`` stamps each generator's own zone price
    (``prices[gen_zidx]``, the energy-balance dual) on every row, so a groupby
    on (hour, zone) recovers the zonal dual exactly.
    """
    d = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet", columns=["zone", "hour", "lmp"]
    )
    return d.groupby(["hour", "zone"]).lmp.first().unstack("zone").reindex(range(T))


def _ca_lambda(zl: pd.DataFrame, year: int) -> np.ndarray:
    """(T,) demand-weighted CA-zone model lambda.

    Demand is a model INPUT (identical across arms of an A/B), so the weights
    come from the committed keeper sidecar — available before a mid-run bundle
    has written its own ``system.parquet``.
    """
    cols = [z for z in CA_ZONES if z in zl.columns]
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    w = s[s.zone.isin(cols)].pivot_table(index="hour", columns="zone", values="demand")
    w = w.reindex(index=range(T), columns=cols).to_numpy(float)
    p = zl[cols].to_numpy(float)
    return (p * w).sum(axis=1) / w.sum(axis=1)


def _renewable_curtailment(bundle: Path, year: int, state: dict, idx: np.ndarray):
    """(share of hours curtailing, mean curtailed MW) for solar and wind.

    The LP bound is ``cf x capacity`` (rule 3: renewables are decision variables
    with MC 0 and that upper bound), so dispatch strictly below it IS
    curtailment — the channel by which a renewable becomes marginal and prices
    the hour at ~0.
    """
    d = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet", columns=["klass", "hour", "mw"]
    )
    out = {}
    for kind in ("solar", "wind"):
        cap = np.asarray(state.get(f"{kind}_cap"), dtype=float)
        cf = np.asarray(state.get(f"{kind}_cf"), dtype=float)
        if cap.size == 0 or cf.size == 0:
            continue
        bound = (cf * cap[:, None]).sum(axis=0) if cf.ndim == 2 else cf * float(cap)
        bound = np.asarray(bound, dtype=float).reshape(-1)[:T]
        got = (
            d[d.klass == kind]
            .groupby("hour")
            .mw.sum()
            .reindex(range(T), fill_value=0.0)
            .to_numpy(float)
        )
        curt = np.maximum(0.0, bound - got)
        tol = np.maximum(1.0, 1e-3 * np.maximum(bound, 1.0))
        out[kind] = (float((curt[idx] > tol[idx]).mean()), float(curt[idx].mean()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--recipe-from",
        default=None,
        help="bundle whose meta.json drives the fleet reconstruction (default: "
        "the target bundle; point at the keeper to read a replay arm that has "
        "not written its own meta yet)",
    )
    args = ap.parse_args()
    bundle = Path(args.bundle)
    recipe = Path(args.recipe_from) if args.recipe_from else bundle

    hod = np.arange(T) % 24
    belly = np.isin(hod, BELLY)

    for year in args.years:
        if not (bundle / "dispatch" / f"{year}_P1.parquet").exists():
            print(f"\n### {year}: no dispatch parquet yet — skipped")
            continue
        rt, hub = _actual_rt(year), _min_hub(year)
        zl = _zone_lambda(bundle, year)
        lam = _ca_lambda(zl, year)
        mw, min_gen, cap, mc0, ids, klass, zone, mech, state = _bounds_and_dispatch(
            bundle, year, recipe
        )

        tol = np.maximum(1.0, 1e-4 * cap)
        live = cap > tol
        interior = live & (mw > min_gen + tol) & (mw < cap - tol)
        at_cap = live & (mw >= cap - tol)
        pinned = live & (min_gen >= cap - tol)

        wecc_cols = [c for c in zl.columns if str(c).startswith("WECC")]
        ca_cols = [c for c in zl.columns if c in CA_ZONES]
        wl = zl[wecc_cols].to_numpy(float)
        cl = zl[ca_cols].to_numpy(float)
        diff = cl[:, :, None] - wl[:, None, :]
        eq_any = (np.abs(diff) <= EQ_TOL).any(axis=(1, 2))
        above_all = np.nanmin(diff, axis=(1, 2)) > EQ_TOL

        regimes = {
            "surplus RT<=20": belly & np.isfinite(rt) & (rt <= SURPLUS_THRESHOLD),
            "firm    RT >20": belly & np.isfinite(rt) & (rt > SURPLUS_THRESHOLD),
        }

        print(f"\n{'=' * 98}")
        print(f"{year}  —  belly hod 10-15, split by the ACTUAL market's regime")
        print("=" * 98)
        for label, mask in regimes.items():
            idx = np.flatnonzero(mask)
            n = idx.size
            if not n:
                continue
            print(
                f"\n--- {label}:  n={n}   actRT ${rt[idx].mean():6.2f}   model "
                f"${lam[idx].mean():6.2f}   min-hub ${np.nanmean(hub[idx]):6.2f}   "
                f"wedge ${np.nanmean(lam[idx] - hub[idx]):+6.2f}"
            )
            print(
                f"    corridor: CA lambda EQUALIZED to a WECC node in "
                f"{eq_any[idx].mean():.0%} of hours; strictly ABOVE every node in "
                f"{above_all[idx].mean():.0%}"
            )

            # -- 1. class-level true-bounds attribution ---------------------
            print(
                f"    {'class':14s} {'inter%':>7s} {'intMW':>7s} {'atcap%':>7s} "
                f"{'pin%':>6s} {'MW':>8s} {'offer@int':>10s}"
            )
            for k in sorted(set(klass)):
                rows = np.flatnonzero(klass == k)
                sel = interior[rows][:, idx]
                s_int = float(sel.any(axis=0).mean())
                tot = float(mw[rows][:, idx].sum(axis=0).mean())
                if s_int < 0.02 and tot < 50:
                    continue
                imw = (mw[rows] * interior[rows])[:, idx].sum(axis=0).mean()
                mcs = mc0[np.ix_(rows, idx)]
                mci = float(mcs[sel].mean()) if sel.any() else float("nan")
                print(
                    f"    {k:14s} {s_int * 100:6.1f}% {imw:7.0f} "
                    f"{float(at_cap[rows][:, idx].any(axis=0).mean()) * 100:6.1f}% "
                    f"{float(pinned[rows][:, idx].any(axis=0).mean()) * 100:5.1f}% "
                    f"{tot:8.0f} {mci:10.2f}"
                )

            # -- 2. per-import-tranche interiority (names the rung) ---------
            imp_rows = np.flatnonzero(klass == "import")
            if imp_rows.size:
                print("    import ladder — per tranche:")
                for r in imp_rows:
                    sel = interior[r][idx]
                    if not sel.any() and mw[r][idx].mean() < 1:
                        continue
                    off = mc0[r][idx][sel].mean() if sel.any() else float("nan")
                    print(
                        f"      {ids[r]:30s} interior {sel.mean() * 100:5.1f}%  "
                        f"MW {mw[r][idx].mean():6.0f}  atcap "
                        f"{at_cap[r][idx].mean() * 100:5.1f}%  offer@int ${off:7.2f}"
                    )

            # -- 3. zonal ladder incl. the WECC corridor nodes ---------------
            print(
                "    zonal lambda: "
                + "  ".join(
                    f"{z}=${zl[z].to_numpy(float)[idx].mean():.2f}"
                    for z in list(ca_cols) + list(wecc_cols)
                )
            )

            # -- 3b. corridor state per WECC node: is the cheap node stranded?
            # A node whose lambda runs deeply negative while its tranches sit
            # at cap has force-flowed supply and no outlet — the corridor into
            # CA is bound and the export sink is unused. That is a different
            # defect from "the import is priced too high".
            for wz in wecc_cols:
                v = zl[wz].to_numpy(float)[idx]
                node_mw = mw[np.flatnonzero(zone == wz)][:, idx].sum(axis=0)
                print(
                    f"      {wz:9s} lambda p10/p50/p90 "
                    f"${np.nanpercentile(v, 10):7.2f}/${np.nanpercentile(v, 50):6.2f}/"
                    f"${np.nanpercentile(v, 90):6.2f}  neg {np.mean(v < 0) * 100:4.1f}%"
                    f"  node dispatch {node_mw.mean():6.0f} MW"
                )

            # -- 4. renewable curtailment (the MC~0 marginal channel) -------
            curt = _renewable_curtailment(bundle, year, state, idx)
            if curt:
                print(
                    "    renewable curtailment: "
                    + "  ".join(
                        f"{k} {v[0] * 100:.1f}% of hours, {v[1]:.0f} MW"
                        for k, v in curt.items()
                    )
                )

            # -- 5. min_gen mechanism behind the pinned units ---------------
            if mech.size == len(ids):
                pin_any = pinned[:, idx].any(axis=1)
                labs = pd.Series(
                    [str(m) for m in mech[pin_any] if str(m) not in ("", "None", "nan")]
                )
                if len(labs):
                    top = ", ".join(
                        f"{a} {b}" for a, b in labs.value_counts().head(5).items()
                    )
                    print(f"    min_gen mechanisms on pinned units: {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
