"""nyiso-195 PHASE 0 (NO LP) — the ``CC_REGULAR`` econ ramp at its own measured
marginal heat-rate basis: per-slice offer reconstruction, parking-slice
attribution and the CAMPD ramp-slope sign, on the keeper's COMMITTED artifacts.

The object handed forward by nyiso-194 §3 (top of the §5.5 queue): the LP parks
each combined cycle where its econ ramp meets the LMP, and NYISO's registered
physical basis (``phys_econ_low 0.784 -> phys_econ_high 0.925``,
``nyiso_campd_marginal_hr_summary.csv`` p50s) differs from the registered
offer ramp (``econ_low 0.95 -> econ_high 1.0``). Under the armed
``gas_offer_net_revenue_margin`` the difference is a FIXED $/MWh markup per
slice, ``(mult_k - phys_k) x base_HR x anchor`` — so the candidate single delta
(offer the econ block at its physical basis, markup 0) is a pure per-slice
price shift whose sign and size are computable before any solve.

This probe measures, with no LP and no parameter (rule 29 ``[R-SCREEN]`` step
0; rules 13 / 21):

1. **Slice offers** — every ``CC_REGULAR`` econ slice's keeper offer
   (``mc_base`` from an on-recipe ``run_year(fleet_only=True)`` rebuild of the
   keeper's 2024 fleet — the SAME assembled offer the LP solved on) and its
   arm offer (keeper minus the slice's fixed markup), the identity check that
   ``mc_base == phys x HR x fuel + markup x anchor + vom`` on every slice, and
   the keeper-zone LMP quantile at which each slice is marginal.
2. **Parking-slice attribution** — the keeper's per-plant hourly MW (decoded
   from the committed run payload, the same decode ``legitimacy_diagnostics``
   uses) against the plant's AVAILABLE committed / econ / peak capacity in
   each hour (the rebuild's ``availability``): in the 80-90 % loading hours,
   is the plant at the top of its available econ ramp (the wall), mid-ramp on
   a marginal slice, or in its peak band?
3. **The CAMPD ramp-slope sign per plant** — heat input vs gross load over
   50-95 % of each plant's own p99.5 (unit-level CAMPD summed per plant), a
   quadratic incremental-heat fit evaluated at the ramp's ends, to confirm
   whether the marginal heat rate RISES with load (the 0.784 -> 0.925 sign).
4. **The footprint census** across 2023-2025 from the committed
   ``class_band_hourly`` sidecars (econ-slice energy, mid-ramp plant-hours)
   — the rule-29 screen-year input, never a residual.

Control = the keeper's committed bundle (rule 29(b) form 4); nothing here is
gated on any residual. Writes ``results/calibration/_nyiso195_econ_basis_phase0.json``.

Usage::

    python scripts/probes/nyiso195_econ_basis_phase0.py [--bundle DIR] [--year 2024]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (
    ROOT,
    ROOT / "src",
    ROOT / "scripts",
    ROOT / "scripts/probes",
    ROOT / "scripts/data",
):
    sys.path.insert(0, str(p))
from market_sim.data.campd import load_campd_hourly  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

KEEPER_ID = "2026-09-05-nyiso-192-astoria-panel"
YEARS = (2023, 2024, 2025)
T = 8760
BINS = np.arange(0.0, 1.01, 0.1)
ARM = {"econ_low": 0.784, "econ_high": 0.925}  # NYISO's own registered phys_* p50s
EXCLUDE_SHAPE = {
    2500
}  # Ravenswood: CAMPD facility = whole steam station (nyiso-194 boundary misalignment)
RAMP_BAND = (0.50, 0.95)  # of the plant's own CAMPD p99.5 gross load
LO_PT, HI_PT = 0.55, 0.92  # where the fitted marginal HR is read (ramp ends)


def _tranche(unit_id: str) -> str:
    t = unit_id.rsplit("_", 1)[1]
    return "econ" if t.startswith("econc") else t


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _hist(mw: np.ndarray, cap: float) -> np.ndarray:
    on = mw[mw > 1.0]
    if on.size == 0:
        return np.zeros(len(BINS) - 1)
    h, _ = np.histogram(np.clip(on / cap, 0, 1 - 1e-9), bins=BINS)
    return h / on.size


def footprint_census(bundle: Path) -> dict:
    """Econ-ramp footprint per year from the committed class_band_hourly sidecars."""
    out = {}
    for yr in YEARS:
        f = bundle / "hourly" / f"class_band_hourly_{yr}.parquet"
        if not f.exists():
            continue
        t = pd.read_parquet(f)
        cc = t[(t.klass == "CC_REGULAR")]
        piv = cc.pivot_table(
            index="hour", columns="band", values="mw", aggfunc="sum"
        ).fillna(0.0)
        econ = [c for c in piv.columns if c.startswith("econ")]
        top, bot = piv[econ[-1]].to_numpy(), piv[econ[0]].to_numpy()
        out[str(yr)] = {
            "econ_twh": round(float(piv[econ].to_numpy().sum()) / 1e6, 3),
            "slice_twh": {c: round(float(piv[c].sum()) / 1e6, 3) for c in econ},
            "committed_twh": round(float(piv.get("committed", 0).sum()) / 1e6, 3),
            "peak_twh": round(float(piv.get("peak", 0).sum()) / 1e6, 3),
            "hours_some_plant_mid_ramp": int(((bot - top) > 1.0).sum()),
            "mid_ramp_mw_gap_twh": round(
                float(np.clip(bot - top, 0, None).sum()) / 1e6, 4
            ),
            "econ_top_slice_share_of_bottom": round(float(top.sum() / bot.sum()), 4)
            if bot.sum()
            else None,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="results/calibration/nyiso192_astoria_panel")
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()
    bundle = ROOT / a.bundle
    yr = a.year
    out = {
        "session": "nyiso-195",
        "status": "PHASE 0 — NO LP, MEASUREMENT ONLY",
        "bundle": a.bundle,
        "year": yr,
        "arm": ARM,
        "control": "keeper committed bundle (rule 29(b) form 4)",
    }

    # ---- 4. footprint census (all committed years) -------------------------------------------
    out["footprint_census"] = footprint_census(bundle)

    # ---- 1. on-recipe fleet rebuild (no LP): slice offers ---------------------------------------
    cache = ROOT / ".cache" / "nyiso195" / f"rebuild_{yr}.pkl"
    if cache.exists():
        st = pickle.load(open(cache, "rb"))
    else:
        state, meta = reconstruct_bundle_fleet(
            bundle, yr, required_flags=(), required_sequences=()
        )
        cfg, fa = state["config"], state["fleet_arrays"]
        st = {
            "rows": [],
            "mc": np.asarray(state["mc_base"]),
            "fuel": np.asarray(state["fuel_prices"]),
            "avail": np.asarray(fa.availability),
            "anchor": float(getattr(cfg, "gas_offer_margin_anchor")),
            "occ": dict(cfg.offer_curve_by_group["CC_REGULAR"]),
            "n": int(cfg.offer_curve_smoothing_n),
        }
        for i, g in enumerate(state["fleet"]):
            if str(getattr(g, "plant_group", "")) != "CC_REGULAR":
                continue
            st["rows"].append(
                {
                    "i": i,
                    "unit_id": g.unit_id,
                    "plant": int(g.plant_code),
                    "zone": str(g.zone),
                    "trk": _tranche(g.unit_id),
                    "pmax": float(g.pmax_mw),
                    "hr": float(g.heat_rate),
                    "vom": float(getattr(g, "vom", 0.0)),
                    "markup_hr": float(getattr(g, "offer_markup_hr", 0.0)),
                    "anchor": float(
                        getattr(g, "offer_margin_anchor", None)
                        or getattr(cfg, "gas_offer_margin_anchor")
                    ),
                }
            )
        cache.parent.mkdir(parents=True, exist_ok=True)
        pickle.dump(st, open(cache, "wb"))
    mc, fuel, avail, anchor, occ, n, rows = (
        st["mc"],
        st["fuel"],
        st["avail"],
        st["anchor"],
        st["occ"],
        st["n"],
        st["rows"],
    )
    out["registered_curve"] = {
        k: occ[k]
        for k in (
            "committed",
            "econ_low",
            "econ_high",
            "peak",
            "phys_committed",
            "phys_econ_low",
            "phys_econ_high",
            "phys_peak",
        )
    }
    out["anchor"] = anchor
    out["smoothing_n"] = n
    units = pd.DataFrame(rows)
    econ = units[units.trk == "econ"].copy()
    # slice index and registered position on the ramp (t = (k+0.5)/n)
    econ["k"] = econ.unit_id.str.extract(r"econc(\d+)$").astype(int)
    econ["t"] = (econ.k + 0.5) / n
    lo_m, hi_m = float(occ["econ_low"]), float(occ["econ_high"])
    plo, phi = float(occ["phys_econ_low"]), float(occ["phys_econ_high"])
    econ["mult"] = lo_m + (hi_m - lo_m) * econ.t
    econ["phys"] = plo + (phi - plo) * econ.t
    econ["markup_expected"] = econ.mult - econ.phys
    econ["arm_mult"] = ARM["econ_low"] + (ARM["econ_high"] - ARM["econ_low"]) * econ.t
    econ["base_hr"] = econ.hr / econ.mult
    idx = econ.i.to_numpy()
    fuel_mean = fuel[idx].mean(axis=1)
    mc_mean = mc[idx].mean(axis=1)
    # identity: mc = (hr - markup) x fuel + markup x anchor + vom  (+ carbon/NOx, expected ~0 for NY gas)
    ident = (
        (econ.hr.to_numpy() - econ.markup_hr.to_numpy())[:, None] * fuel[idx]
        + (econ.markup_hr * econ.anchor).to_numpy()[:, None]
        + econ.vom.to_numpy()[:, None]
    )
    resid = mc[idx] - ident
    econ["fuel_mean"] = fuel_mean
    econ["keeper_offer_mean"] = mc_mean
    econ["fixed_margin"] = (
        econ.markup_hr * econ.anchor
    )  # $/MWh, fuel-invariant (per-tranche anchor where the band carries one)
    out["tranche_anchors"] = sorted({round(float(x), 4) for x in econ.anchor})
    econ["arm_offer_mean"] = mc_mean - econ.fixed_margin
    out["identity_check"] = {
        "markup_hr_equals_(mult-phys)x_baseHR_max_abs_err": round(
            float(np.abs(econ.markup_hr - econ.markup_expected * econ.base_hr).max()), 6
        ),
        "mc_identity_residual_mean_abs": round(float(np.abs(resid).mean()), 4),
        "mc_identity_residual_max_abs": round(float(np.abs(resid).max()), 4),
        "note": "residual = carbon/NOx/EAC adders the identity omits; a constant per plant is expected, not a defect",
    }
    # per-slice class summary
    sl = econ.groupby("k").agg(
        cap_mw=("pmax", "sum"),
        mult=("mult", "first"),
        phys=("phys", "first"),
        arm_mult=("arm_mult", "first"),
        markup_hr_capw=(
            "markup_hr",
            lambda s: float(np.average(s, weights=econ.loc[s.index, "pmax"])),
        ),
        fixed_margin_capw=(
            "fixed_margin",
            lambda s: float(np.average(s, weights=econ.loc[s.index, "pmax"])),
        ),
        keeper_offer_capw=(
            "keeper_offer_mean",
            lambda s: float(np.average(s, weights=econ.loc[s.index, "pmax"])),
        ),
        arm_offer_capw=(
            "arm_offer_mean",
            lambda s: float(np.average(s, weights=econ.loc[s.index, "pmax"])),
        ),
    )
    out["slices_class"] = {
        int(k): {c: round(float(v), 4) for c, v in r.items()} for k, r in sl.iterrows()
    }
    out["ramp_spread_capw"] = {
        "keeper_top_minus_bottom_$MWh": round(
            float(sl.keeper_offer_capw.iloc[-1] - sl.keeper_offer_capw.iloc[0]), 3
        ),
        "arm_top_minus_bottom_$MWh": round(
            float(sl.arm_offer_capw.iloc[-1] - sl.arm_offer_capw.iloc[0]), 3
        ),
        "arm_minus_keeper_bottom_$MWh": round(
            float(sl.arm_offer_capw.iloc[0] - sl.keeper_offer_capw.iloc[0]), 3
        ),
        "arm_minus_keeper_top_$MWh": round(
            float(sl.arm_offer_capw.iloc[-1] - sl.keeper_offer_capw.iloc[-1]), 3
        ),
        "direction": "every econ slice CHEAPER under the arm by its fixed margin (markup -> 0); the bottom moves more than the top",
    }

    # ---- keeper zone LMP (committed hourly sidecar) -------------------------------------------
    sysp = pd.read_parquet(bundle / "hourly" / f"system_{yr}.parquet")
    lmp = sysp.pivot(index="hour", columns="zone", values="price").iloc[:T]

    # ---- 2. keeper per-plant hourly MW from the committed payload ------------------------------
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
    )["bench"]["plants"]
    plants_pl = run["years"][str(yr)]["plants"]
    camp = load_campd_hourly(["NY"], [yr], prefer_unit_level=True)
    plant_codes = sorted(set(units.plant))
    camp = camp[camp.plant_id.isin(plant_codes)]
    g = camp.groupby(["plant_id", "hour_of_year"]).agg(
        gross=("gross_mw", "sum"), heat=("heat_mmbtu", "sum")
    )

    per_plant = []
    cls = {
        "on_h": 0,
        "h_80_90": 0,
        "h_80_90_at_wall": 0,
        "h_80_90_mid_ramp": 0,
        "h_80_90_in_peak": 0,
        "h_80_90_below_committed": 0,
        "mw_on": 0.0,
        "mwh_80_90": 0.0,
        "mwh_80_90_at_wall": 0.0,
        "mwh_80_90_mid_ramp": 0.0,
        "newly_in_money_slice_hours": 0,
        "newly_in_money_bound_gwh": 0.0,
        "wall_in_80_90_plants": [],
    }
    tot_bins_keeper = np.zeros(len(BINS) - 1)
    tot_bins_campd = np.zeros(len(BINS) - 1)
    for pc in plant_codes:
        u = units[units.plant == pc]
        pm = float(u.pmax.sum())
        zone = u.zone.iloc[0]
        key = str(pc)
        if key not in plants_pl or not plants_pl[key].get("m"):
            continue
        raw = _dec(plants_pl[key]["m"])[:T]
        npl = float(bench.get(key, {}).get("npl", 0.0) or 0.0)
        m_ann = plants_pl[key].get("m_ann")
        if m_ann and raw.sum() > 0:
            m = raw * (
                float(m_ann) * 1e6 / raw.sum()
            )  # exact annual rescale (legitimacy_diagnostics._decode_cf_bytes)
            npl = npl or float(m.max())
        elif npl > 0:
            m = raw * npl / 100.0
        else:
            continue
        ci = u[u.trk == "committed"].i.to_numpy()
        ei = u[u.trk == "econ"].i.to_numpy()
        pi = u[u.trk == "peak"].i.to_numpy()
        C = (
            (avail[ci] * u.set_index("i").loc[ci].pmax.to_numpy()[:, None]).sum(axis=0)[
                :T
            ]
            if ci.size
            else np.zeros(T)
        )
        E = (
            (avail[ei] * u.set_index("i").loc[ei].pmax.to_numpy()[:, None]).sum(axis=0)[
                :T
            ]
            if ei.size
            else np.zeros(T)
        )
        tol = (
            0.01 * npl + 0.01 * pm
        )  # payload byte quantization (1 % of nameplate) + 1 % of pmax
        on = m > 1.0
        frac = m / pm
        in_80_90 = on & (frac >= 0.8) & (frac < 0.9)
        at_wall = in_80_90 & (np.abs(m - (C + E)) <= tol)
        in_peak = in_80_90 & (m > C + E + tol)
        below_c = in_80_90 & (m < C - tol)
        mid = in_80_90 & ~at_wall & ~in_peak & ~below_c
        # marginal slice in mid-ramp hours: which slice the loading sits on (available slice caps, equal)
        slice_cap = E / max(n, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            kk = np.floor(
                np.where(
                    mid & (slice_cap > 0),
                    (m - C) / np.where(slice_cap > 0, slice_cap, 1.0),
                    -1,
                )
            ).astype(int)
        mid_slice_hist = {int(k): int(((kk == k) & mid).sum()) for k in range(n)}
        # per-slice newly-in-the-money hours from the keeper zone LMP
        lz = lmp[zone].to_numpy() if zone in lmp.columns else None
        slices = econ[econ.plant == pc].sort_values("k")
        srows = []
        new_bound_mwh = 0.0
        for _, s in slices.iterrows():
            kmc = mc[s.i][:T]
            amc = kmc - s.fixed_margin
            if lz is not None:
                itm_k = int((lz >= kmc).sum())
                itm_a = int((lz >= amc).sum())
                newly = (lz >= amc) & (lz < kmc)
                q = (
                    {
                        p: round(float(np.percentile(lz[np.abs(lz - kmc) < 2.0], p)), 2)
                        for p in (10, 50, 90)
                    }
                    if (np.abs(lz - kmc) < 2.0).sum() > 20
                    else None
                )
                new_bound_mwh += float((s.pmax * avail[s.i][:T] * newly).sum())
            else:
                itm_k = itm_a = 0
                newly = np.zeros(T, bool)
                q = None
            srows.append(
                {
                    "k": int(s.k),
                    "cap_mw": round(s.pmax, 1),
                    "mult": round(s.mult, 4),
                    "phys": round(s.phys, 4),
                    "keeper_offer_mean": round(float(kmc.mean()), 2),
                    "fixed_margin": round(float(s.fixed_margin), 2),
                    "arm_offer_mean": round(float(amc.mean()), 2),
                    "lmp_ge_keeper_h": itm_k,
                    "lmp_ge_arm_h": itm_a,
                    "newly_in_money_h": int(newly.sum()),
                    "lmp_quantiles_when_marginal(+-2$)": q,
                }
            )
            cls["newly_in_money_slice_hours"] += int(newly.sum())
        cls["newly_in_money_bound_gwh"] += new_bound_mwh / 1e3
        wall_frac = float((C + E)[on].mean() / pm) if on.any() else None
        meas = None
        if pc in g.index.get_level_values(0):
            gg = g.loc[pc].reindex(range(T)).fillna(0.0)
            x = gg.gross.to_numpy()
            hh = gg.heat.to_numpy()
            p995 = float(np.percentile(x[x > 1], 99.5)) if (x > 1).any() else 0.0
            band = (x >= RAMP_BAND[0] * p995) & (x < RAMP_BAND[1] * p995) & (hh > 0)
            meas = {
                "p995_gross_mw": round(p995, 1),
                "ramp_band_hours": int(band.sum()),
                "hist": [round(float(v), 4) for v in _hist(x, pm)],
            }
            if band.sum() >= 100:
                xb, yb = x[band], hh[band]
                c2, c1, c0 = np.polyfit(xb, yb, 2)
                m_lo = c1 + 2 * c2 * LO_PT * p995
                m_hi = c1 + 2 * c2 * HI_PT * p995
                full = (x >= 0.90 * p995) & (hh > 0)
                avg_hr_full = (
                    float(hh[full].sum() / x[full].sum()) if full.sum() > 20 else None
                )
                avg_hr_band = float(yb.sum() / xb.sum())
                # piecewise OLS slopes (incremental HR) in three sub-bands
                pw = {}
                for lo, hi in ((0.50, 0.70), (0.70, 0.85), (0.85, 0.95)):
                    mm = (x >= lo * p995) & (x < hi * p995) & (hh > 0)
                    pw[f"{int(lo * 100)}-{int(hi * 100)}"] = (
                        round(float(np.polyfit(x[mm], hh[mm], 1)[0]), 3)
                        if mm.sum() >= 50
                        else None
                    )
                meas.update(
                    {
                        "quad_marginal_hr_at_55pct": round(float(m_lo), 3),
                        "quad_marginal_hr_at_92pct": round(float(m_hi), 3),
                        "marginal_hr_rises_with_load": bool(m_hi > m_lo),
                        "curvature_c2_sign": int(np.sign(c2)),
                        "avg_hr_full_load": round(avg_hr_full, 3)
                        if avg_hr_full
                        else None,
                        "avg_hr_ramp_band": round(avg_hr_band, 3),
                        "marg_over_avgfull_lo": round(float(m_lo / avg_hr_full), 3)
                        if avg_hr_full
                        else None,
                        "marg_over_avgfull_hi": round(float(m_hi / avg_hr_full), 3)
                        if avg_hr_full
                        else None,
                        "piecewise_incremental_hr": pw,
                    }
                )
            if pc not in EXCLUDE_SHAPE:
                tot_bins_campd += _hist(x, pm) * int((x > 1).sum()) * pm
        if pc not in EXCLUDE_SHAPE:
            tot_bins_keeper += _hist(m, pm) * int(on.sum()) * pm
        r = {
            "plant": int(pc),
            "zone": zone,
            "pmax": round(pm, 1),
            "committed_mw": round(float(u[u.trk == "committed"].pmax.sum()), 1),
            "econ_mw": round(float(u[u.trk == "econ"].pmax.sum()), 1),
            "peak_mw": round(float(u[u.trk == "peak"].pmax.sum()), 1),
            "wall_frac_static": round(1 - float(u[u.trk == "peak"].pmax.sum()) / pm, 3),
            "wall_frac_available_mean": round(wall_frac, 3) if wall_frac else None,
            "keeper": {
                "on_h": int(on.sum()),
                "hist": [round(float(v), 4) for v in _hist(m, pm)],
                "h_80_90": int(in_80_90.sum()),
                "h_80_90_at_available_wall": int(at_wall.sum()),
                "h_80_90_mid_ramp": int(mid.sum()),
                "h_80_90_in_peak": int(in_peak.sum()),
                "h_80_90_below_committed": int(below_c.sum()),
                "mid_ramp_marginal_slice_hist": mid_slice_hist,
                "h_gt90": int((frac > 0.9).sum()),
                "energy_gwh": round(float(m.sum()) / 1e3, 1),
            },
            "slices": srows,
            "newly_in_money_bound_gwh": round(new_bound_mwh / 1e3, 2),
            "measured": meas,
        }
        per_plant.append(r)
        cls["on_h"] += int(on.sum())
        cls["h_80_90"] += int(in_80_90.sum())
        cls["h_80_90_at_wall"] += int(at_wall.sum())
        cls["h_80_90_mid_ramp"] += int(mid.sum())
        cls["h_80_90_in_peak"] += int(in_peak.sum())
        cls["h_80_90_below_committed"] += int(below_c.sum())
        cls["mwh_80_90"] += float(m[in_80_90].sum())
        cls["mwh_80_90_at_wall"] += float(m[at_wall].sum())
        cls["mwh_80_90_mid_ramp"] += float(m[mid].sum())
        if r["wall_frac_static"] < 0.9 and r["wall_frac_static"] >= 0.7:
            cls["wall_in_80_90_plants"].append(int(pc))
    per_plant.sort(key=lambda r: -r["pmax"])
    kb = tot_bins_keeper / tot_bins_keeper.sum()
    cb = tot_bins_campd / tot_bins_campd.sum()
    cls = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cls.items()}
    cls["class_bins_keeper_payload_pct"] = [round(float(v) * 100, 1) for v in kb]
    cls["class_bins_campd_pct"] = [round(float(v) * 100, 1) for v in cb]
    cls["self_check_vs_nyiso194_parquet"] = {
        "share_80_90_payload": round(float(kb[8]) * 100, 2),
        "share_80_90_nyiso194": 32.96,
        "share_90_100_payload": round(float(kb[9]) * 100, 2),
        "share_90_100_nyiso194": 19.76,
    }
    out["class"] = cls
    out["plants"] = per_plant
    signs = [
        (r["plant"], r["measured"]["marginal_hr_rises_with_load"])
        for r in per_plant
        if r["measured"] and "marginal_hr_rises_with_load" in r["measured"]
    ]
    out["campd_ramp_sign"] = {
        "plants_with_fit": len(signs),
        "rising_marginal_hr": sum(1 for _, s in signs if s),
        "falling": sum(1 for _, s in signs if not s),
        "capw_marg_over_avgfull_lo": None,
        "capw_marg_over_avgfull_hi": None,
    }
    w = [
        (
            r["pmax"],
            r["measured"]["marg_over_avgfull_lo"],
            r["measured"]["marg_over_avgfull_hi"],
        )
        for r in per_plant
        if r["measured"]
        and r["measured"].get("marg_over_avgfull_lo")
        and r["plant"] not in EXCLUDE_SHAPE
    ]
    if w:
        W = np.array([x[0] for x in w])
        out["campd_ramp_sign"]["capw_marg_over_avgfull_lo"] = round(
            float(np.average([x[1] for x in w], weights=W)), 3
        )
        out["campd_ramp_sign"]["capw_marg_over_avgfull_hi"] = round(
            float(np.average([x[2] for x in w], weights=W)), 3
        )

    dst = ROOT / "results/calibration/_nyiso195_econ_basis_phase0.json"

    def _py(o):
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        raise TypeError(type(o))

    dst.write_text(json.dumps(out, indent=1, default=_py))
    # ---- print -----------------------------------------------------------------------------
    print(f"\n=== nyiso-195 phase 0, {yr} — keeper {KEEPER_ID} (no LP)")
    print(
        f"footprint census: { {y: {k: v for k, v in d.items() if k in ('econ_twh', 'hours_some_plant_mid_ramp', 'mid_ramp_mw_gap_twh', 'econ_top_slice_share_of_bottom')} for y, d in out['footprint_census'].items()} }"
    )
    print(f"identity: {out['identity_check']}")
    print(f"registered {out['registered_curve']}  anchor {anchor}  n {n}")
    print(
        f"{'k':>2} {'cap':>7} {'mult':>6} {'phys':>6} {'arm':>6} {'mkupHR':>7} {'fix$':>6} {'keep$':>7} {'arm$':>7}"
    )
    for k, r in out["slices_class"].items():
        print(
            f"{k:>2} {r['cap_mw']:7.1f} {r['mult']:6.4f} {r['phys']:6.4f} {r['arm_mult']:6.4f} {r['markup_hr_capw']:7.4f} {r['fixed_margin_capw']:6.2f} {r['keeper_offer_capw']:7.2f} {r['arm_offer_capw']:7.2f}"
        )
    print(f"ramp spread: {out['ramp_spread_capw']}")
    c = out["class"]
    print(
        f"class: on_h {c['on_h']}; 80-90 h {c['h_80_90']}: at available wall {c['h_80_90_at_wall']}, mid-ramp {c['h_80_90_mid_ramp']}, in peak {c['h_80_90_in_peak']}, below committed {c['h_80_90_below_committed']}"
    )
    print(
        f"       newly-in-money slice-hours {c['newly_in_money_slice_hours']}, energy upper bound {c['newly_in_money_bound_gwh']:.1f} GWh"
    )
    print(
        f"       bins keeper(payload) {c['class_bins_keeper_payload_pct']}\n       bins campd          {c['class_bins_campd_pct']}\n       self-check {c['self_check_vs_nyiso194_parquet']}"
    )
    print(f"CAMPD ramp sign: {out['campd_ramp_sign']}")
    print(
        f"{'plant':>6} {'pmax':>5} {'wall':>5} {'wallA':>5} | {'on':>5} {'80-90':>5} {'@wall':>5} {'mid':>5} {'peak':>4} | {'>90':>5} | {'new$h':>6} {'newGWh':>6} | {'mHR55':>6} {'mHR92':>6} {'rise':>5} {'lo/avg':>6} {'hi/avg':>6}"
    )
    for r in per_plant:
        k = r["keeper"]
        ms = r["measured"] or {}
        newh = sum(s["newly_in_money_h"] for s in r["slices"])
        f = lambda v, w=6, d=3: (
            f"{v:{w}.{d}f}"
            if isinstance(v, float)
            else f"{str(v) if v is not None else '-':>{w}}"
        )
        print(
            f"{r['plant']:>6} {r['pmax']:5.0f} {r['wall_frac_static']:5.3f} {f(r['wall_frac_available_mean'], 5)} | {k['on_h']:5d} {k['h_80_90']:5d} {k['h_80_90_at_available_wall']:5d} {k['h_80_90_mid_ramp']:5d} {k['h_80_90_in_peak']:4d} | {k['h_gt90']:5d} | {newh:6d} {r['newly_in_money_bound_gwh']:6.1f} | {f(ms.get('quad_marginal_hr_at_55pct'))} {f(ms.get('quad_marginal_hr_at_92pct'))} {f(ms.get('marginal_hr_rises_with_load'), 5)} {f(ms.get('marg_over_avgfull_lo'))} {f(ms.get('marg_over_avgfull_hi'))}"
        )
    print(f"\nwrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
