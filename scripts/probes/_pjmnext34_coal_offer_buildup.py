"""PJM-NEXT-34 (ZERO LP): COAL_BIT offer build-up census over the real-dark spells.

Readings fixed ex ante in
``docs/records/pjm/FINDING-pjm-next-34-coalbit-offer-buildup-census-2026-10-03.md`` §1.

Per year: one ``fleet_only`` rebuild of the keeper recipe (``w0_pjm_span``, fidelity-guarded,
``pjm_da_virtual_bids`` off as in NEXT-13). On the NEXT-33 dark-spell plant-hours, each keeper
COAL_BIT non-floor tranche's P1 offer ``K`` (``unit_marginal``) is split against the plant's
measured going cost ``G = HR_m·F + R``:

    K − G = HR_m·F·(b·π − 1) + m + s
          = B (band) + S (sigmoid) + m (mid-curve floor) + s (P1 seam)

``P_off`` is PJM's measured LONG_RUN offer at the row's within-plant share (the surface the
floor reads). Writes ``results/phase0/pjm/_pjmnext34_coal_offer_buildup.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext34_coal_offer_buildup.py [YEAR ...]``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO / "src"))
from _pjmnext28_sunk_noload import BUNDLE_REL, _parquet  # noqa: E402
from _pjmnext32_coal_commitment_census import (  # noqa: E402
    FLOOR,
    MIN_DOWN,
    T,
    _kind,
    _runs,
    coal_units,
    covered_masks,
)

from scripts.lib import bundle_fleet as BF  # noqa: E402

BUNDLE = REPO / BUNDLE_REL
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext34_coal_offer_buildup.json"
GROUP = "COAL_BIT"
YEARS = tuple(range(2019, 2026))
FAIL = (2019, 2020, 2021)
CTRL = (2023, 2024)
#: Ex-ante gate tolerances (FINDING §1 R0).
ID_TOL = 0.05
R_TOL = 0.01
COVER_MIN = 0.99
#: Ex-ante reading thresholds (FINDING §1 Q1/Q2/Q4).
BELOW_SHARE = 0.5
DISC_MARGIN = 2.0
FALSIFY_SHARE = 0.5
TERMS = ("B", "S", "m", "s")


def rebuild(year: int) -> dict:
    """Keeper ``fleet_only`` state for ``year`` (DA virtual rows off, fidelity guard on)."""
    BF.ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    BF.assert_reconstruction_fidelity(
        meta, state["config"], BF.DEFAULT_REQUIRED_FLAGS, BF.DEFAULT_REQUIRED_SEQUENCES
    )
    return state


def passthrough(state: dict, rows: list[int], year: int) -> dict[int, np.ndarray]:
    """``π`` per row, from ``campd_tranche_fuel_frac`` called as ``assembly.py`` calls it."""
    from market_sim.data.fleet import campd_tranche_fuel_frac
    from market_sim.data.fuel import coal_passthrough_by_supply

    cfg = state["config"]
    gens = state["fleet"]
    pt = coal_passthrough_by_supply(cfg, year, cfg.hours)
    assert not getattr(cfg, "coal_committed_takeorpay_regulated", False)
    assert getattr(cfg, "coal_sync_srmc_tranche", False)  # takeorpay=None (assembly)
    out = {}
    for g in rows:
        f = campd_tranche_fuel_frac(
            gens[g],
            pt,
            None,
            econ_srmc_bound=getattr(cfg, "coal_econ_srmc_bound", False),
            committed_takeorpay_bit=getattr(cfg, "coal_bit_committed_takeorpay", False),
            committed_takeorpay_all=getattr(cfg, "coal_committed_takeorpay_all", False),
            committed_takeorpay_regulated=False,
            regulated_plants=None,
            committed_takeorpay_sunk_fixed=getattr(
                cfg, "coal_committed_takeorpay_sunk_fixed", False
            ),
            committed_dispatchable_supplies=(
                frozenset({"prb", "subbituminous"})
                if getattr(cfg, "coal_prb_committed_dispatchable", False)
                else None
            ),
            committed_measured_basis=getattr(
                cfg, "committed_band_measured_basis", False
            ),
        )
        out[g] = np.broadcast_to(np.asarray(f, float), (T,)).copy()
    return out


def floor_and_target(state: dict, year: int, rows: list[int]):
    """Mid-curve floor markup ``m`` and PJM LONG_RUN offer ``P_off`` per row."""
    from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup
    from market_sim.data.fleet.offer_surfaces import (
        _pjm_midcurve_context,
        _pjm_midcurve_row_target,
    )

    cfg, fa, gens, mcb = (
        state["config"],
        state["fleet_arrays"],
        state["fleet"],
        state["mc_base"],
    )
    net = (
        state["demand"].sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )
    mk = build_pjm_offer_midcurve_conditional_markup(fa, gens, mcb, net, cfg, year)
    ctx = _pjm_midcurve_context(fa, gens, mcb, net, cfg, year, {"LONG_RUN"})
    want = set(rows)
    poff = {}
    for g, s_g, _sfx, seg in ctx.rows:
        if g in want and seg in ctx.tables:
            poff[g] = np.asarray(_pjm_midcurve_row_target(ctx, seg, s_g), float)
    m = {g: (mk[g] if mk is not None else np.zeros(T)) for g in rows}
    return m, poff


def keeper_offers(y: int) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Keeper P1 offer ``mc`` and ``cap_mw`` per COAL_BIT unit id."""
    um = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=["unit_id", "hour", "cap_mw", "mc"],
        filters=[("plant_group", "=", GROUP), ("pass", "=", "P1")],
    )
    K, C = {}, {}
    for uid, g in um.groupby("unit_id", observed=True):
        h = g["hour"].to_numpy()
        k, c = np.full(T, np.nan), np.zeros(T)
        k[h], c[h] = g["mc"], g["cap_mw"]
        K[str(uid)], C[str(uid)] = k, c
    return K, C


def dark_weights(y: int, plants: set[int]) -> dict[int, np.ndarray]:
    """NEXT-33 dark-spell plant-hour weights ``K*·peak_u/Σpeak`` (M+L, uncovered)."""
    from _pjmnext32_coal_commitment_census import keeper_plants

    kp = keeper_plants(y)
    d = coal_units(y, plants & set(kp))
    cov = covered_masks(y)
    out = {}
    for pc, g in d.groupby("facilityId"):
        P = kp.get(int(pc))
        if P is None:
            continue
        kstar = float(np.vstack([t[2] for t in P["tr"]]).sum(0).max())
        if kstar <= 0:
            continue
        units = {}
        for uid, gu in g.groupby("unitId"):
            gross, op = np.zeros(T), np.zeros(T)
            gross[gu["hoy"].to_numpy()] = gu["grossLoad"].fillna(0.0).to_numpy()
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            if gross.max() > 0:
                units[uid] = (gross.max(), op <= 0.0)
        if not units:
            continue
        ptot = sum(v[0] for v in units.values())
        w = np.zeros(T)
        for uid, (pk, dark) in units.items():
            ud = dark & ~cov.get((int(pc), uid), np.zeros(T, bool))
            for s, e in _runs(ud):
                if e - s >= MIN_DOWN:
                    w[s:e] += kstar * pk / ptot
        if w.any():
            out[int(pc)] = (w, P["zone"])
    return out


class Acc:
    """Weighted sums by key."""

    def __init__(self):
        self.s: dict[str, float] = {}

    def add(self, k: str, v: float) -> None:
        """Accumulate ``v`` under ``k``."""
        self.s[k] = self.s.get(k, 0.0) + float(v)

    def get(self, k: str) -> float:
        """Sum under ``k`` (0 when absent)."""
        return self.s.get(k, 0.0)


def run_year(y: int) -> dict:
    """Census one year (FINDING §1)."""
    from market_sim.data.fleet.campd_bins import measured_coal_heat_rates

    state = rebuild(y)
    gens, fa = state["fleet"], state["fleet_arrays"]
    fp = np.asarray(state["fuel_prices"], float)
    mcb = np.asarray(state["mc_base"], float)
    hr_t = np.asarray(fa.heat_rate, float)
    vom = np.asarray(fa.vom, float)
    hr_own = measured_coal_heat_rates("PJM", y)
    hr_pool = measured_coal_heat_rates("PJM", None)
    K, C = keeper_offers(y)

    rows_by_plant: dict[int, list[int]] = {}
    for i, g in enumerate(gens):
        if (
            g.plant_group == GROUP
            and _kind(pd.Series([g.unit_id])).iloc[0] not in FLOOR
        ):
            rows_by_plant.setdefault(int(g.plant_code), []).append(i)
    allrows = [i for r in rows_by_plant.values() for i in r]
    pi = passthrough(state, allrows, y)
    m_of, poff_of = floor_and_target(state, y, allrows)

    real = pd.read_parquet(ZONAL)
    real = real[real["year"] == y]
    pr = {
        str(z): g.set_index("hour")["da"].reindex(range(T)).to_numpy(float)
        for z, g in real.groupby("zone")
    }
    dw = dark_weights(y, set(rows_by_plant))

    A = Acc()
    for pc, (w, zone) in dw.items():
        rows = rows_by_plant.get(pc, [])
        uids = [gens[i].unit_id for i in rows]
        caps = np.vstack([C.get(u, np.zeros(T)) for u in uids]) if uids else None
        if caps is None or not caps.any():
            A.add("w_nocap", w.sum())
            continue
        ctot = caps.sum(0)
        hrm, src = hr_own.get(pc), "own"
        if hrm is None:
            hrm, src = hr_pool.get(pc), "pooled"
        ok_h = (w > 0) & (ctot > 0)
        Gp = np.zeros(T)  # plant cap-weighted G for Q5
        for j, i in enumerate(rows):
            u = uids[j]
            wt = np.where(ok_h, w * caps[j] / np.maximum(ctot, 1e-9), 0.0)
            if not wt.any():
                continue
            W = wt.sum()
            A.add("w", W)
            if u not in K:
                A.add("w_unmatched", W)
                continue
            if hrm is None:
                A.add("w_hr_absent", W)
                continue
            A.add(f"w_src_{src}", W)
            kind = _kind(pd.Series([u])).iloc[0]
            kind = "econ" if kind.startswith("econ") else kind
            F = fp[i]
            p = pi[i]
            Rr = mcb[i] - hr_t[i] * F * p
            b = hr_t[i] / hrm
            G = hrm * F + Rr
            m = m_of[i]
            k = K[u]
            s = k - mcb[i] - m
            B = hrm * F * (b - 1.0) * (p + 1.0) / 2.0
            S = hrm * F * (p - 1.0) * (b + 1.0) / 2.0
            ident = (np.abs(mcb[i] + m - k) <= ID_TOL) | (s >= -ID_TOL)
            A.add("w_ident_ok", (wt * ident).sum())
            A.add("w_R_ok", (wt * (Rr >= vom[i] - R_TOL)).sum())
            for key, v in (
                ("K", k),
                ("G", G),
                ("B", B),
                ("S", S),
                ("m", m),
                ("s", s),
                ("b", b * np.ones(T)),
                ("pi", p),
                ("F", F),
                ("hrm", hrm * np.ones(T)),
            ):
                A.add(key, (wt * v).sum())
                A.add(f"{kind}:{key}", (wt * v).sum())
            A.add(f"{kind}:w", W)
            A.add("below", (wt * (k < G)).sum())
            Gp += wt * G
            if kind in ("econ", "peak"):
                po = poff_of.get(i)
                A.add("fl:w", W)
                A.add("fl:bind", (wt * (m > ID_TOL)).sum())
                A.add("fl:K", (wt * k).sum())
                A.add("fl:G", (wt * G).sum())
                if po is not None:
                    A.add("fl:wP", W)
                    A.add("fl:P", (wt * po).sum())
                    A.add("fl:P_le_K", (wt * (po <= k)).sum())
                    A.add("fl:P_lt_G", (wt * (po < G)).sum())
        if zone in pr:
            wp = np.where(ok_h, w, 0.0)
            g_pl = Gp / np.maximum(wp, 1e-9)
            okp = (wp > 0) & np.isfinite(pr[zone]) & (Gp > 0)
            A.add("q5:w", wp[okp].sum())
            A.add("q5:real_lt_G", (wp * (pr[zone] < g_pl))[okp].sum())

    W = A.get("w") - A.get("w_unmatched") - A.get("w_hr_absent")
    res = {
        "dark_twh_weighted": A.get("w") / 1e6,
        "R0_cover": 1.0 - A.get("w_unmatched") / max(A.get("w"), 1e-9),
        "R0_ident": A.get("w_ident_ok") / max(W, 1e-9),
        "R0_R": A.get("w_R_ok") / max(W, 1e-9),
        "R0b_own": A.get("w_src_own") / max(W, 1e-9),
        "R0b_pooled": A.get("w_src_pooled") / max(W, 1e-9),
        "R0b_absent": A.get("w_hr_absent") / max(A.get("w"), 1e-9),
        "w_nocap_twh": A.get("w_nocap") / 1e6,
    }
    for key in ("K", "G", "B", "S", "m", "s", "b", "pi", "F", "hrm"):
        res[key] = A.get(key) / max(W, 1e-9)
    res["K_minus_G"] = res["K"] - res["G"]
    res["share_K_below_G"] = A.get("below") / max(W, 1e-9)
    res["by_kind"] = {}
    for kind in ("committed", "econ", "peak"):
        wk = A.get(f"{kind}:w")
        if wk > 0:
            res["by_kind"][kind] = {"w_share": wk / W} | {
                key: A.get(f"{kind}:{key}") / wk
                for key in ("K", "G", "B", "S", "m", "s", "b", "pi")
            }
    fw = A.get("fl:w")
    fwp = A.get("fl:wP")
    res["Q4"] = {
        "w_share": fw / max(W, 1e-9),
        "floor_binds": A.get("fl:bind") / max(fw, 1e-9),
        "K": A.get("fl:K") / max(fw, 1e-9),
        "G": A.get("fl:G") / max(fw, 1e-9),
        "P_off": A.get("fl:P") / max(fwp, 1e-9),
        "P_cover": fwp / max(fw, 1e-9),
        "share_P_le_K": A.get("fl:P_le_K") / max(fwp, 1e-9),
        "share_P_lt_G": A.get("fl:P_lt_G") / max(fwp, 1e-9),
    }
    res["Q5_share_real_below_G"] = A.get("q5:real_lt_G") / max(A.get("q5:w"), 1e-9)
    return res


def readings(res: dict) -> dict:
    """Apply the ex-ante readings (FINDING §1)."""
    yrs = [y for y in res if res[y]]

    def pooled(ys, key):
        ys = [str(y) for y in ys if str(y) in res]
        w = np.array([res[y]["dark_twh_weighted"] for y in ys])
        v = np.array([res[y][key] for y in ys])
        return float((w * v).sum() / w.sum()) if len(ys) else float("nan")

    q1 = {
        y: (res[y]["K_minus_G"] < 0 and res[y]["share_K_below_G"] >= BELOW_SHARE)
        for y in yrs
    }
    gap = {y: -res[y]["K_minus_G"] for y in yrs}
    have = all(str(y) in res for y in FAIL + CTRL)
    q2 = (
        min(gap[str(y)] for y in FAIL) >= max(gap[str(y)] for y in CTRL) + DISC_MARGIN
        if have
        else None
    )
    fail_gap = pooled(FAIL, "K_minus_G")
    ctrl_gap = pooled(CTRL, "K_minus_G")
    carrier = {t: -pooled(FAIL, t) / -fail_gap for t in TERMS} if fail_gap else {}
    diff = {t: -(pooled(FAIL, t) - pooled(CTRL, t)) for t in TERMS}
    q4 = {y: res[y]["Q4"]["share_P_le_K"] >= FALSIFY_SHARE for y in yrs}
    n_fals = sum(q4.get(str(y), False) for y in FAIL)
    n_below = sum(q1.get(str(y), False) for y in FAIL)
    top = max(carrier, key=lambda t: carrier[t]) if carrier else None
    return {
        "Q1_below": q1,
        "Q1_n_fail_below": n_below,
        "Q2_discriminating": q2,
        "Q2_gap_G_minus_K": gap,
        "Q3_carrier_share_pooled_fail": carrier,
        "Q3_carrier": top,
        "Q3_diff_fail_minus_ctrl_G_minus_K": {
            "total": -(fail_gap - ctrl_gap),
            **diff,
        },
        "Q4_falsified_years": q4,
        "Q4_falsified": n_fals >= 2,
        "chartered_preconditions": bool(n_below >= 2 and q2 and n_fals < 2),
    }


def main(years: list[int]) -> None:
    """Run the census and write the JSON (merging years already on disk)."""
    logging.disable(logging.CRITICAL)
    res = json.loads(OUT.read_text()).get("years", {}) if OUT.exists() else {}
    for y in years:
        r = run_year(y)
        res[str(y)] = r
        print(
            y,
            json.dumps({k: round(v, 3) for k, v in r.items() if isinstance(v, float)}),
            flush=True,
        )
        OUT.write_text(json.dumps({"years": res}, indent=1) + "\n")
        BF.clear_fleet_caches()
    out = {"years": res, "readings": readings(res), "keeper_bundle": BUNDLE_REL}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["readings"], indent=1))


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
