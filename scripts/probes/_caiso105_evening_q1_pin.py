"""CAISO-105 priority-2: PIN-AWARE Q1 evening margin re-decomposition.

FINDING-caiso104 §2 adjudicated the caiso-103 §3 attribution ("the firm
import blocks are price-setting in 96-100 % of Q1 hours with 1.7-2.5 GW
withheld") to be a PROXY ARTIFACT: the caiso-77 must-flow floor is LIVE in
the keeper, both firm blocks are PINNED (dispatch == min_gen == pmax x
availability in 1.0000 of positive-capability hours, all three years), and a
variable fixed at equal bounds never sets lambda. The owner's re-charter:
re-decompose the deepest-quartile (Q1) evening residual with interiority
measured against the LP's OWN bounds — ``min_gen`` from the bundle's
``floors/<year>_P1.npz`` (what the P1 LP actually saw, RA-bridge floors
included) and caps from the ``run_year(fleet_only=True)`` availability
reconstruction (pmax x availability, temp-derates and outage windows
included) — NEVER the unit-year p99 interior proxy that produced the
artifact. Question: what actually sets Q1 lambda one rung below CT entry?

Per year, aligned model clock (interval-beginning), evening hod 17-21,
Q1 = deepest resid-quartile of evening hours (resid = model CA
demand-weighted lambda - actual RT):

  1. TRUE-BOUNDS MARGINAL ATTRIBUTION — per Q1 hour, units STRICTLY interior
     to their LP bounds (min_gen + tol < mw < cap - tol; tol = max(1 MW,
     1e-4 x cap)); per-class share of Q1 hours with an interior unit and the
     interior MW, vs the all-evening share. Pinned units (floor == cap)
     cannot appear by construction.
  2. IMPORT-RUNG PRICE ELASTICITY — per Q1 hour, is a CA zone lambda
     EQUALIZED to a WECC node lambda (within the intertie tie-break
     epsilon), i.e. the import rung is marginal, vs SEPARATED (the corridor
     is bound and CA prices above the hubs)? From system.parquet zone
     prices — the LP's own duals, no flow-limit proxy.
  3. STORAGE MARGIN — fleet battery discharge strictly interior to the
     caiso-99 envelope cap (dis_frac_p95[hod] x EIA-860 monthly fleet MW,
     the LP's actual bound) in Q1 hours: is the battery the marginal rung?
  4. CT-RUNG DISTANCE — the LP's own CT entry: per Q1 hour the cheapest
     AVAILABLE CT_PEAKER offer (mc_base of units with cap > 0 that hour,
     P0 basis) minus the hour's lambda — the rung the margin sits below.
  5. FIRM-BLOCK NEGATIVE-LAMBDA FORCED FLOW (the floor->$0-bid candidate's
     evidence base) — per window, hours where a firm block's own zone
     lambda < 0 while the caiso-77 floor forces its full shaped MW, and the
     MWh forced through negative prices; the measured conduct
     (_caiso104_firm_negative_hub: curtailment in 5/6 corridor-years) says
     reality curtails those MWh. Also the CA-side lambda in those hours.

NO LP is built or solved; NO mechanism is armed (rule 19 — the floor->$0-bid
replacement, if the evidence supports it, is filed as a NEW owner ask; it
un-promotes part of caiso-77).

Usage: python scripts/probes/_caiso105_evening_q1_pin.py <bundle_dir>
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso102_evening_merit import (  # noqa: E402
    EVENING,
    actual_rt,
    model_hourly,
)
from _caiso103_evening_margin import envelope_dis_cap  # noqa: E402

YEARS = (2023, 2024, 2025)
FIRM_UNITS = ("WECC_PNW_PNW_hydro_base", "WECC_DSW_DSW_solar_PV")
# Intertie tie-break epsilon: flows carry an epsilon cost, so an equalized
# (import-marginal) hour has |lambda_CA - lambda_WECC| within a few epsilon.
EQ_TOL = 0.5  # $/MWh
WINDOWS = (
    ("overnight", (0, 1, 2, 3, 4, 5)),
    ("morning", (6, 7, 8, 9)),
    ("belly", (10, 11, 12, 13, 14)),
    ("pm-shldr", (15, 16)),
    ("evening", (17, 18, 19, 20, 21)),
    ("late", (22, 23)),
)

_META_RENAME = {
    "commitment": "commitment_enabled",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}


def fleet_state(bundle: Path, year: int) -> dict:
    """run_year(fleet_only=True) with the bundle's own meta flags.

    The `_caiso78_step0_ramp_mechanism._fleet_state` reconstruction: meta.json
    keys renamed onto the run_year signature, prb_overrides carried (the
    generic scenario-override channel every caiso structural flag rides on).
    """
    import inspect

    from run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {}
    for k, v in meta.items():
        k2 = _META_RENAME.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
    gas_prices = meta["gas_prices"]
    gas_price = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", 8760)),
        gas_price,
        {},
        fleet_only=True,
        **kwargs,
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    hod = np.arange(8760) % 24
    ev_mask = np.isin(hod, EVENING)

    for y in YEARS:
        m = model_hourly(bundle, y)
        rt = actual_rt(y)
        resid = m["lambda"] - rt
        ok = ev_mask & np.isfinite(resid) & (np.abs(rt) > 1e-9)
        q1_edge = np.nanquantile(resid[ok], 0.25)
        q1 = ok & (resid <= q1_edge)
        n_q1, n_ev = int(q1.sum()), int(ok.sum())

        # --- LP bounds: floors npz (lower) + fleet_only caps (upper) -------
        npz = np.load(bundle / "floors" / f"{y}_P1.npz")
        f_ids = [str(u) for u in npz["unit_ids"]]
        min_gen = np.asarray(npz["min_gen"], dtype=float)  # (n, 8760)
        state = fleet_state(bundle, y)
        fa = state["fleet_arrays"]
        s_ids = [str(u) for u in fa.unit_ids]
        cap = fa.pmax[:, None] * fa.availability  # (n, T)
        if s_ids != f_ids:
            # align the reconstruction onto the npz order by unit id
            pos = {u: i for i, u in enumerate(s_ids)}
            sel = [pos[u] for u in f_ids]
            cap = cap[sel]
            mc0 = np.asarray(state["mc_base"], dtype=float)[sel]
        else:
            mc0 = np.asarray(state["mc_base"], dtype=float)
        n_units = len(f_ids)

        d = pd.read_parquet(
            bundle / "dispatch" / f"{y}_P1.parquet",
            columns=["unit_id", "klass", "zone", "hour", "mw", "lmp"],
        )
        d = d[d["unit_id"].isin(set(f_ids))]
        uidx = {u: i for i, u in enumerate(f_ids)}
        mw = np.zeros((n_units, 8760))
        mw[
            d.unit_id.map(uidx).to_numpy(int),
            d.hour.to_numpy(int),
        ] = d.mw.to_numpy(float)
        klass_of = dict(
            d[["unit_id", "klass"]].drop_duplicates().itertuples(index=False)
        )
        zone_of = dict(d[["unit_id", "zone"]].drop_duplicates().itertuples(index=False))

        tol = np.maximum(1.0, 1e-4 * cap)
        interior = (mw > min_gen + tol) & (mw < cap - tol)

        print(f"\n===================== {y} =====================")
        print(
            f"Q1 = {n_q1}/{n_ev} evening hours, resid <= {q1_edge:+.1f}; "
            f"dw resid {np.average(resid[q1], weights=m['demand'][q1]):+.1f}; "
            f"mean model lam {m['lambda'][q1].mean():.1f} vs actual "
            f"{rt[q1].mean():.1f}"
        )

        # -- 1. true-bounds marginal attribution ----------------------------
        kl = np.array([klass_of.get(u, "?") for u in f_ids], dtype=object)
        q1_idx = np.flatnonzero(q1)
        ev_idx = np.flatnonzero(ok)
        print("1. TRUE-BOUNDS interior share of hours (Q1 | all-evening), Q1 MW:")
        for k in sorted(set(kl)):
            rows = np.flatnonzero(kl == k)
            if not rows.size:
                continue
            any_int = interior[rows].any(axis=0)
            s_q1 = float(any_int[q1_idx].mean())
            s_ev = float(any_int[ev_idx].mean())
            if max(s_q1, s_ev) < 0.02:
                continue
            imw = (mw[rows] * interior[rows])[:, q1_idx].sum(axis=0)
            print(
                f"    {str(k):16s}: {s_q1:5.2f} | {s_ev:5.2f}"
                f"  (interior {imw.mean():7.0f} MW in Q1)"
            )

        # -- 2. import-rung elasticity from the LP's own zone duals ---------
        s = pd.read_parquet(bundle / "system.parquet")
        s = s[(s["pass"] == "P1") & (s.year == y)]
        zlam = s.pivot_table(index="hour", columns="zone", values="price").reindex(
            range(8760)
        )
        wecc_cols = [c for c in zlam.columns if str(c).startswith("WECC")]
        ca_cols = [c for c in zlam.columns if not str(c).startswith("WECC")]
        wl = zlam[wecc_cols].to_numpy(float)
        cl = zlam[ca_cols].to_numpy(float)
        # equalized: any (CA, WECC) pair within EQ_TOL
        diff = cl[:, :, None] - wl[:, None, :]
        eq_any = (np.abs(diff) <= EQ_TOL).any(axis=(1, 2))
        above_all = np.nanmin(diff, axis=(1, 2)) > EQ_TOL
        print(
            f"2. import rung (LP duals): CA lam equalized to a WECC node in "
            f"{eq_any[q1].mean():.0%} of Q1 hours (all-evening "
            f"{eq_any[ok].mean():.0%}); CA strictly ABOVE every WECC node in "
            f"{above_all[q1].mean():.0%} of Q1 (all-evening "
            f"{above_all[ok].mean():.0%})"
        )

        # -- 3. storage margin vs the envelope bound ------------------------
        env_cap = envelope_dis_cap(y)
        st = pd.read_parquet(bundle / "storage.parquet")
        st = st[(st["pass"] == "P1") & (st.year == y) & (st.tech != "pumped_storage")]
        dis = (
            st.groupby("hour")
            .discharge_mw.sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy()
        )
        dis_int = (dis > 1.0) & (dis < env_cap - np.maximum(1.0, 1e-3 * env_cap))
        env_bind = dis >= env_cap - np.maximum(1.0, 1e-3 * env_cap)
        print(
            f"3. battery: envelope-BOUND in {env_bind[q1].mean():.0%} of Q1 "
            f"(all-evening {env_bind[ok].mean():.0%}); strictly interior "
            f"(discharge margin free) in {dis_int[q1].mean():.0%} of Q1 "
            f"(all-evening {dis_int[ok].mean():.0%}); Q1 mean dis "
            f"{dis[q1].mean() / 1e3:.2f} GW vs env {env_cap[q1].mean() / 1e3:.2f} GW"
        )

        # -- 4. CT-rung distance at the LP's own offers ---------------------
        ct_rows = np.flatnonzero(kl == "CT_PEAKER")
        if ct_rows.size:
            ct_avail = cap[ct_rows] > 1.0
            ct_mc = np.where(ct_avail, mc0[ct_rows], np.inf)
            entry = ct_mc.min(axis=0)  # cheapest available CT offer per hour
            gap = entry[q1_idx] - m["lambda"][q1_idx]
            fin = np.isfinite(gap)
            print(
                f"4. CT rung (P0 mc of cheapest AVAILABLE CT): Q1 lam sits "
                f"{np.nanmean(gap[fin]):+.1f} $/MWh below entry "
                f"(p25/p50/p75 {np.nanpercentile(gap[fin], 25):+.1f}/"
                f"{np.nanpercentile(gap[fin], 50):+.1f}/"
                f"{np.nanpercentile(gap[fin], 75):+.1f}); NOTE P1 adds "
                f"startup markup on top of P0 mc"
            )

        # -- 5. firm-block negative-lambda forced flow ----------------------
        print("5. firm-block forced flow through negative own-zone lambda:")
        ca_dw_lam = m["lambda"]
        for fu in FIRM_UNITS:
            if fu not in uidx:
                continue
            r = uidx[fu]
            zn = zone_of.get(fu, "")
            zl = (
                zlam[zn].to_numpy(float)
                if zn in zlam.columns
                else np.full(8760, np.nan)
            )
            forced = mw[r] > 1.0
            neg = forced & (zl < 0.0)
            mwh_neg = float(mw[r][neg].sum())
            print(
                f"    {fu} (zone {zn}): neg-lam forced hours {int(neg.sum())} "
                f"({mwh_neg / 1e3:.1f} GWh); pinned share "
                f"{np.isclose(mw[r], min_gen[r], rtol=1e-6, atol=1e-3)[forced].mean():.4f}"
            )
            if neg.any():
                by_w = []
                for wname, whods in WINDOWS:
                    wm = np.isin(hod, whods) & neg
                    if wm.any():
                        by_w.append(
                            f"{wname} {int(wm.sum())}h/{mw[r][wm].sum() / 1e3:.1f}GWh"
                            f"/CAlam {np.nanmean(ca_dw_lam[wm]):+.1f}"
                        )
                print("      by window: " + "; ".join(by_w))
    return 0


if __name__ == "__main__":
    sys.exit(main())
