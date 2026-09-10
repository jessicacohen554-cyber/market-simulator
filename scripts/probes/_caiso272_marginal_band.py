"""caiso-272 card 0(b): WHICH (class, band) sets the CAISO price — ZERO LP.

``FINDING-caiso270`` §4 measured a system-wide **+1 implied-marginal-heat-rate
bias** (model above market in 40 of 48 months, mean +1.01) and named no
carrier; ``PRECOMMIT-caiso271`` §0 narrowed it to the hours where the CC econ
stack reaches ``econc05`` (6,924 h, 81.8 % of 2022 load) without finishing the
identification. This probe finishes it, spends no LP, arms nothing, and adds no
``ScenarioConfig`` field.

WHAT IT READS
-------------
* ``hourly/system_<year>.parquet`` — the keeper's P1 zonal price. Per caiso-250
  §4.5 / caiso-270 §3.3 that price is ``lambda_LP + A(t)``, the CAISO scarcity
  adder ``A`` bounded by caiso-229 at $0.017/$0.006/$0.003 per MWh and ~0 in
  2022 on four independent instruments. CITED, never re-derived; it is one to
  three orders of magnitude below every distance reported here, which is why
  the match tolerance is fixed at 10x the largest such bound.
* ``hourly/class_band_hourly_<year>.parquet`` — P1 dispatch at (klass, band)
  grain, the only committed artifact below the class aggregate.
* ``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`` — the
  committed hourly actual RT and DA LMP.
* ``run_calibration.run_year(..., fleet_only=True)`` — the keeper's OWN
  assembled ``mc_base``, which the orchestrator documents as "the assembled P0
  objective ... so post-solve offer-stack diagnostics read the SAME offer
  prices the LP solved on".

THE ONE APPROXIMATION, STATED AT THE GATE
-----------------------------------------
``tranche_startup_amortization`` is OFF on this keeper, so the only P0->P1
wedge is ``commitment.compute_monthly_markup``'s ``startup / max(avg_run, 1)``.
Its denominator is a P0 dispatch this session may not spend an LP to get, so it
is BOUNDED exactly from the fleet instead — ``startup / measured_run <= markup
<= startup`` — and reported per band. It is zero for every econ and peak
tranche (only ``committed`` rows carry a startup cost), i.e. it cannot move the
identification of the econ ladder at all.

WHAT IT IS NOT
--------------
It selects no lever and is gated on no residual (rule 1 ``[R-STRUCT]``). It
identifies the price-setter and decomposes the published miss; the adjudication
lives in the session's FINDING, and the decision is the owner's.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso269_lateevening_2022"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = REPO / "results/calibration/_caiso272_marginal_band.json"
YEAR = 2022

#: Price-match tolerance, $/MWh. FIXED before the first number and never swept:
#: 10x the largest scarcity-adder bound the committed record carries for any
#: scored CAISO year, so the instrument cannot be sensitive to the one term the
#: persisted price adds to the raw dual. Three wider settings are reported
#: beside it precisely so the reader can see the answer does not move.
TOL = 0.25
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")


def band_of(unit_id: str) -> str:
    """The LP tranche suffix — the last underscore token of ``unit_id``.

    Verbatim the split ``run_calibration_full._write_class_band_hourly_sidecar``
    uses, so this probe's band key IS the committed sidecar's band key.
    """
    return str(unit_id).rsplit("_", 1)[-1]


def family(klass: str, band: str) -> str:
    """Collapse (klass, band) to the offer-stack family the census reports."""
    if klass in ("CC_REGULAR", "CC_CHP"):
        if band.startswith("econ"):
            return "CC econ"
        return "CC committed" if band == "committed" else "CC peak"
    if klass in ("CT_PEAKER", "CT_CHP"):
        if band.startswith("econ"):
            return "CT econ"
        return "CT committed" if band == "committed" else "CT peak"
    return klass


def build() -> dict:
    """Rebuild the keeper's 2022 offer surface and read its committed P1."""
    state, meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=(), required_sequences=()
    )
    from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER
    from market_sim.data.fuel import _caiso_hub_daily_gas_prices
    from market_sim.model.commitment import _startup_cost

    fa, fleet, cfg = state["fleet_arrays"], state["fleet"], state["config"]
    raw_klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel_name = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    binned = raw_klass != ""
    # The sidecar keys the non-binned families (hydro/nuclear/import/biomass/
    # oil/OTHER/solar/wind) by FUEL with an EMPTY band — their unit_id's last
    # token is a plant unit name, not a tranche suffix — so collapse them the
    # same way rather than inventing hundreds of one-row "bands".
    klass = np.where(binned, raw_klass, fuel_name)
    band = np.where(binned, [band_of(u) for u in fa.unit_ids], "")

    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    cbh = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{YEAR}.parquet")
    cbh = cbh[cbh["pass"] == "P1"]
    disp = cbh.pivot_table(
        index="hour", columns=["klass", "band"], values="mw", aggfunc="sum"
    ).fillna(0.0)

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR].sort_values("hour")

    return {
        "meta": meta,
        "mc": np.asarray(state["mc_base"], float),
        "fuel_row": np.asarray(state["fuel_prices"], float),
        "cap": np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float),
        "klass": klass,
        "band": band,
        "zone": np.array([str(getattr(g, "zone", "") or "") for g in fleet]),
        "name": np.array([str(getattr(g, "name", "") or "") for g in fleet]),
        "plant": np.array([str(getattr(g, "plant_code", "") or "") for g in fleet]),
        "startup": np.array(
            [_startup_cost(g, float(fa.heat_rate[i])) for i, g in enumerate(fleet)]
        ),
        "frun": np.array(
            [float(getattr(g, "fast_start_run_hours", 0.0) or 0.0) for g in fleet]
        ),
        "gas": np.asarray(
            _caiso_hub_daily_gas_prices(cfg, YEAR, spot_level=True, spot_coverage=True),
            float,
        )
        + CAISO_CITYGATE_TRANSPORT_ADDER,
        "zones": [str(z) for z in pr.columns],
        "price": pr.to_numpy(float).T,
        "demand": dm.to_numpy(float).T,
        "disp": disp,
        "rt": act["rt"].to_numpy(float),
        "da": act["da"].to_numpy(float),
    }


def census(S: dict, hs: np.ndarray, tol: float, pooled: bool) -> dict:
    """Price-match census over the CA zones for the hours ``hs``.

    A row is a candidate price-setter in a zone-hour when it is available and
    ``|mc - lambda| <= tol``; the hour's zonal demand is split evenly across the
    candidates. ``pooled`` matches against every CA-zone row rather than only
    the zone's own, because ``caiso_zonal_loss_surface`` makes a CA zone price
    off another zone's unit plus the loss/congestion wedge.
    """
    zone, mc, cap = S["zone"], S["mc"], S["cap"]
    P, D = S["price"], S["demand"]
    ca_rows = np.where(np.isin(zone, CA_ZONES))[0]
    w_fam, lam_fam, hr_fam = Counter(), Counter(), Counter()
    plants = Counter()
    w_matched = w_all = w_un = d_un = 0.0
    un_above = un_below = un_gap = 0.0
    for zz in CA_ZONES:
        i = S["zones"].index(zz)
        gi = ca_rows if pooled else np.where(zone == zz)[0]
        if gi.size == 0:
            continue
        w, lam = D[i][hs], P[i][hs]
        w_all += float(w.sum())
        live = cap[np.ix_(gi, hs)] > 1e-9
        sub = np.where(live, mc[np.ix_(gi, hs)], np.inf)
        fr = np.where(live, S["fuel_row"][np.ix_(gi, hs)], np.nan)
        d = np.abs(sub - lam[None, :])
        dmin = d.min(axis=0)
        hit = dmin <= tol
        hi = np.where(np.isfinite(sub), sub, -np.inf).max(axis=0)
        lo = np.where(np.isfinite(sub), sub, np.inf).min(axis=0)
        for j in np.where(hit)[0]:
            sel = np.where(d[:, j] <= tol)[0]
            ww = float(w[j]) / sel.size
            for a in sel:
                g = gi[a]
                key = family(str(klass_of(S, g)), str(S["band"][g]))
                w_fam[key] += ww
                lam_fam[key] += ww * float(lam[j])
                if fr[a, j] > 0:
                    hr_fam[key] += ww * float(sub[a, j] / fr[a, j])
                plants[(str(S["plant"][g]), str(S["name"][g])[:26], key)] += ww
            w_matched += float(w[j])
        u = ~hit
        w_un += float(w[u].sum())
        d_un += float((w[u] * dmin[u]).sum())
        un_above += float((w[u] * (lam[u] > hi[u] + tol)).sum())
        un_below += float((w[u] * (lam[u] < lo[u] - tol)).sum())
        un_gap += float(
            (w[u] * ((lam[u] <= hi[u] + tol) & (lam[u] >= lo[u] - tol))).sum()
        )
    return {
        "w_fam": w_fam,
        "lam_fam": lam_fam,
        "hr_fam": hr_fam,
        "plants": plants,
        "coverage": w_matched / w_all if w_all else None,
        "unmatched_w": w_un,
        "unmatched_dist": d_un / w_un if w_un else None,
        "unmatched_above": un_above / w_un if w_un else None,
        "unmatched_below": un_below / w_un if w_un else None,
        "unmatched_gap": un_gap / w_un if w_un else None,
        "w_all": w_all,
    }


def klass_of(S: dict, g: int) -> str:
    return S["klass"][g]


def main() -> None:
    S = build()
    P, D = S["price"], S["demand"]
    T = P.shape[1]
    disp = S["disp"]
    key = ("CC_REGULAR", "econc05")
    cc5 = disp[key].to_numpy(float) if key in disp.columns else np.zeros(T)
    hs = np.where(cc5 > 0.0)[0]
    w_h = D.sum(axis=0)
    lam_sys = (P * D).sum(axis=0) / D.sum(axis=0)
    lw = lambda v, w: float((v * w).sum() / w.sum())  # noqa: E731

    out: dict = {
        "session": "caiso-272",
        "year": YEAR,
        "bundle": str(BUNDLE.relative_to(REPO)),
        "keeper_git_sha": S["meta"].get("git_sha"),
        "tol_usd_mwh": TOL,
        "econc05_hours": int(hs.size),
        "econc05_load_share": round(float(w_h[hs].sum() / w_h.sum()), 4),
    }

    # ---- G-REPRO: the published numbers this instrument must return ----
    g_e, g_a = lw(S["gas"][hs], w_h[hs]), lw(S["gas"], w_h)
    repro = {
        "econc05_hours": int(hs.size),
        "econc05_load_share_pct": round(100 * w_h[hs].sum() / w_h.sum(), 2),
        "model_lw_price_2022": round(lw(lam_sys, w_h), 3),
        "rt_lw_price_2022": round(lw(S["rt"], w_h), 3),
        "da_lw_price_2022": round(lw(S["da"], w_h), 3),
        "gas_lw_2022": round(g_a, 4),
        "implied_hr_model_2022": round(lw(lam_sys, w_h) / g_a, 3),
        "implied_hr_rt_2022": round(lw(S["rt"], w_h) / g_a, 3),
        "implied_hr_da_2022": round(lw(S["da"], w_h) / g_a, 3),
        "implied_hr_model_econc05": round(lw(lam_sys[hs], w_h[hs]) / g_e, 3),
        "implied_hr_rt_econc05": round(lw(S["rt"][hs], w_h[hs]) / g_e, 3),
        "implied_hr_da_econc05": round(lw(S["da"][hs], w_h[hs]) / g_e, 3),
    }
    out["reproduction"] = repro
    print("=== G-REPRO (published values this instrument must return) ===")
    for k, v in repro.items():
        print(f"  {k:>30s} {v}")

    # ---- which market does the model's hourly price behave like ----
    def fit(x: np.ndarray) -> dict:
        return {
            "lw_mean": round(lw(x, w_h), 3),
            "lw_bias": round(lw(lam_sys, w_h) - lw(x, w_h), 3),
            "lw_mae": round(lw(np.abs(lam_sys - x), w_h), 3),
            "lw_rmse": round(float(np.sqrt(lw((lam_sys - x) ** 2, w_h))), 3),
            "pearson": round(float(np.corrcoef(lam_sys, x)[0, 1]), 4),
            "spearman": round(
                float(pd.Series(lam_sys).corr(pd.Series(x), method="spearman")), 4
            ),
        }

    out["hourly_fit"] = {"vs_RT_gated": fit(S["rt"]), "vs_DA_companion": fit(S["da"])}
    out["dart_lw_2022"] = round(lw(S["da"], w_h) - lw(S["rt"], w_h), 3)
    print("\n=== hourly fit, 2022 (n=8760, load-weighted) ===")
    for k, v in out["hourly_fit"].items():
        print(f"  {k:>18s} {v}")
    print(f"  DART (lw DA - lw RT) = ${out['dart_lw_2022']}")

    # ---- hour-of-day ----
    hod = np.arange(T) % 24
    rows = []
    for h in range(24):
        m = hod == h
        ww = w_h[m]
        f = lambda v: float((v[m] * ww).sum() / ww.sum())  # noqa: E731
        rows.append(
            {
                "hod": h,
                "model": round(f(lam_sys), 2),
                "rt": round(f(S["rt"]), 2),
                "da": round(f(S["da"]), 2),
                "m_minus_rt": round(f(lam_sys) - f(S["rt"]), 2),
                "m_minus_da": round(f(lam_sys) - f(S["da"]), 2),
                "dart": round(f(S["da"]) - f(S["rt"]), 2),
            }
        )
    out["hour_of_day"] = rows
    print("\n=== hour of day (load-weighted $/MWh) ===")
    print(
        f"{'hod':>3s} {'model':>8s} {'RT':>8s} {'DA':>8s} "
        f"{'m-RT':>7s} {'m-DA':>7s} {'DART':>7s}"
    )
    for r in rows:
        print(
            f"{r['hod']:>3d} {r['model']:>8.2f} {r['rt']:>8.2f} {r['da']:>8.2f} "
            f"{r['m_minus_rt']:>+7.2f} {r['m_minus_da']:>+7.2f} {r['dart']:>+7.2f}"
        )

    # ---- the census, at four settings, so the answer's robustness is visible
    out["marginal_census"] = {}
    for tol, pooled, tag in (
        (0.25, False, "own-zone tol$0.25"),
        (0.25, True, "CA-pooled tol$0.25"),
        (1.00, True, "CA-pooled tol$1.00"),
        (3.00, True, "CA-pooled tol$3.00"),
    ):
        c = census(S, hs, tol, pooled)
        tot = sum(c["w_fam"].values()) or 1.0
        fam_rows = []
        for k, v in sorted(c["w_fam"].items(), key=lambda x: -x[1]):
            fam_rows.append(
                {
                    "family": k,
                    "share_pct": round(100 * v / tot, 2),
                    "mean_lambda": round(c["lam_fam"][k] / v, 2),
                    "implied_hr": round(c["lam_fam"][k] / v / g_e, 3),
                    "offer_hr": round(c["hr_fam"][k] / v, 3)
                    if c["hr_fam"][k]
                    else None,
                }
            )
        cc = [k for k in c["w_fam"] if k.startswith("CC")]
        ccw = sum(c["w_fam"][k] for k in cc) or 1.0
        ccl = sum(c["lam_fam"][k] for k in cc) / ccw
        nc = [k for k in c["w_fam"] if not k.startswith("CC")]
        ncw = sum(c["w_fam"][k] for k in nc) or 1.0
        ncl = sum(c["lam_fam"][k] for k in nc) / ncw
        mix = sum(c["lam_fam"].values()) / tot
        blk = {
            "coverage_pct": round(100 * c["coverage"], 2),
            "families": fam_rows,
            "cc_share_pct": round(100 * ccw / tot, 2),
            "cc_mean_lambda": round(ccl, 2),
            "cc_implied_hr": round(ccl / g_e, 3),
            "noncc_share_pct": round(100 * ncw / tot, 2),
            "noncc_mean_lambda": round(ncl, 2),
            "noncc_implied_hr": round(ncl / g_e, 3),
            "mix_implied_hr": round(mix / g_e, 3),
            "hr_points_carried_by_noncc": round((mix - ccl) / g_e, 3),
            "unmatched_pct_of_weight": round(100 * c["unmatched_w"] / c["w_all"], 2),
            "unmatched_mean_dist": round(c["unmatched_dist"], 3),
            "unmatched_lambda_above_all_pct": round(100 * c["unmatched_above"], 2),
            "unmatched_lambda_below_all_pct": round(100 * c["unmatched_below"], 2),
            "unmatched_lambda_in_gap_pct": round(100 * c["unmatched_gap"], 2),
        }
        if tag == "CA-pooled tol$0.25":
            ptot = sum(c["plants"].values()) or 1.0
            blk["top_marginal_plants"] = [
                {
                    "plant": k[0],
                    "name": k[1],
                    "family": k[2],
                    "share_pct": round(100 * v / ptot, 2),
                }
                for k, v in c["plants"].most_common(10)
            ]
        out["marginal_census"][tag] = blk
        print(f"\n=== {tag}: coverage {blk['coverage_pct']}% of econc05 weight ===")
        print(
            f"{'marginal family':>16s} {'share%':>7s} {'mean lam':>9s} "
            f"{'impliedHR':>10s} {'offerHR':>8s}"
        )
        for r in fam_rows[:9]:
            print(
                f"{r['family']:>16s} {r['share_pct']:>7.2f} {r['mean_lambda']:>9.2f} "
                f"{r['implied_hr']:>10.3f} "
                f"{(r['offer_hr'] if r['offer_hr'] is not None else float('nan')):>8.3f}"
            )
        print(
            f"  CC-marginal {blk['cc_share_pct']}% at implied HR "
            f"{blk['cc_implied_hr']}; NON-CC {blk['noncc_share_pct']}% at "
            f"{blk['noncc_implied_hr']}; non-CC carries "
            f"+{blk['hr_points_carried_by_noncc']} HR points"
        )
        print(
            f"  UNMATCHED {blk['unmatched_pct_of_weight']}% of weight, mean dist "
            f"${blk['unmatched_mean_dist']}: above-all "
            f"{blk['unmatched_lambda_above_all_pct']}%, below-all "
            f"{blk['unmatched_lambda_below_all_pct']}%, IN A GAP "
            f"{blk['unmatched_lambda_in_gap_pct']}%"
        )

    # ---- the startup-markup bound, per family (the one approximation) ----
    mk = {}
    for f_ in sorted({family(str(k), str(b)) for k, b in zip(S["klass"], S["band"])}):
        gi = [
            i
            for i in range(S["klass"].size)
            if family(str(S["klass"][i]), str(S["band"][i])) == f_
        ]
        su = S["startup"][gi]
        fr = S["frun"][gi]
        lo = np.where(fr > 0, su / np.maximum(fr, 1.0), 0.0)
        mk[f_] = {
            "markup_lo": round(float(lo.mean()), 3),
            "markup_hi": round(float(su.mean()), 3),
        }
    out["startup_markup_bound_by_family"] = mk
    print("\n=== startup-markup bound $/MWh (the only P0->P1 wedge) ===")
    for k, v in mk.items():
        print(f"  {k:>16s} {v['markup_lo']:6.2f} - {v['markup_hi']:6.2f}")

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
