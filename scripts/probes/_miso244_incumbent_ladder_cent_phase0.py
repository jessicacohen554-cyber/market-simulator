"""miso-244 phase 0 — DIAGNOSE the one-cent gap between ``MISO_SEAM_LADDER_BY_YEAR``
and its own derive at HEAD.  ZERO LP, read-only, repairs nothing.

Pre-registration:
``results/calibration/PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md``.
Every bar below is a LITERAL quoted from that document, and every predecessor
reference value is restated here as a literal so this probe adjudicates even if
the predecessor's artifact is missing (handoff process requirement).

THE OBJECT.  miso-243 measured, as a disclosed by-product of its own failed P-2
leg, that the committed incumbent ladder differs from ``derive()`` at HEAD by
exactly 0.01 on PJM 2023, South 2023 and South 2024 — magnitude exactly
``NO_WASH_EPS`` — and handed it forward UN-DIAGNOSED.  This probe diagnoses it.

THE VERDICT (PREREG §2.3, fixed before any number existed).  For each of the 192
committed entries let ``raw`` be the UNROUNDED value ``_derive_one`` computes at
HEAD and ``c`` the committed value.  An entry mismatches iff
``round(raw, 2) != c``; then ``t = |raw - c| - 0.005`` is how far the current
estimate sits PAST the half-cent boundary separating the two cents.

    V-ARTIFACT   iff t_max <= 1e-4  (a rounding TIE: both cents are correct
                                     roundings of the same estimate)
    V-NOT-A-TIE  iff t_max >  1e-4  (the committed value is not a rounding of
                                     the current estimate)

GATED: G-P2 / G-SPP / G-POOL / G-DOC / G-ROW / G-RAW (provenance + instrument
validity), I-1 (identity), and t_max -> VERDICT.
REPORTED, NEVER GATED: D-3 locations, D-4 clamp census, D-5 alternative-clamp
reconstruction, D-1' tie mechanism, D-1'' exact-cent recompute (a PREDICTION
that cannot move the verdict, PREREG §2.4), D-6 dtype, and the F6 liveness scope.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_miso244_incumbent_ladder_cent_phase0.json"
YEARS = (2023, 2024, 2025)
SEAMS = ("PJM", "SPP", "South", "Manitoba")
SIDES = ("import", "export")

# ---- BARS, quoted as literals from the PREREG -------------------------------
TIE_BAR = 1e-4  # §2.3: V-ARTIFACT iff t_max <= 1e-4
TOL_CORR = 0.002  # §2.1 G-DOC
IDENTITY_BAR = 0.002  # §2.2 I-1
ROUND_TOL = 0.005  # a half cent; the boundary the verdict turns on

# ---- PREDECESSOR REFERENCE VALUES, restated as literals ---------------------
# miso-243 P-2 (ADDENDUM-miso243-my-own-p2-leg-failed-... §0a):
REF_P2_PER_SEAM = {
    2023: {"PJM": 0.01, "SPP": 0.00, "South": 0.01, "Manitoba": 0.00},
    2024: {"PJM": 0.00, "SPP": 0.00, "South": 0.01, "Manitoba": 0.00},
    2025: {"PJM": 0.00, "SPP": 0.00, "South": 0.00, "Manitoba": 0.00},
}
# miso-243 G-DOC / the derive script's own docstring:
REF_DOC_CORR = {2023: 0.041, 2024: -0.020, 2025: 0.050}
# miso-243 P-1's own n_rows_R_D:
REF_N_RD = {2023: 8754, 2024: 8757, 2025: 8757}
REF_ROWS_PER_YEAR = 8760


def _load_derive_module():
    """Import the derive script as a module (reading its ESTIMATOR, not a label)."""
    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_miso244_derive", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _raw_one(da: np.ndarray, flow: np.ndarray, spec, eps: float) -> dict:
    """Replicate ``_derive_one`` and return the UNROUNDED bands + clamp trace.

    Byte-for-byte the estimator in ``scripts/data/derive_miso_seam_ladders.py``:
    the same midpoint-depth grid, the same Q-Q duration coupling, the same
    same-seam no-wash clamp taken off the UNROUNDED import list.  G-RAW asserts
    ``round(raw, 2) == derive()`` for all 192 entries, so a divergence here
    fails loudly instead of silently mis-stating the verdict.
    """
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
    mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
    exceed_i = [float((flow > m).mean()) for m in mids]
    depth_e = [float((flow < -m).mean()) for m in mids]
    imp = [float(np.quantile(da, 1.0 - e)) for e in exceed_i]
    exp = [float(np.quantile(da, d)) for d in depth_e]
    lim = min(imp) - eps
    clamped = [False] * len(exp)
    for k, s in enumerate(exp):
        if s > lim:
            clamped[k] = True
            exp[k] = lim
    return {
        "import": imp,
        "export": exp,
        "mids": [float(m) for m in mids],
        "exceed_import": exceed_i,
        "depth_export": depth_e,
        "clamped_export": clamped,
        "clamp_lim": float(lim),
    }


def _seam_samples(dm, g: pd.DataFrame) -> dict:
    """The per-seam (da, flow, spec) row sets ``derive()`` itself builds."""
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )

    out = {}
    g3 = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
    da3 = g3["da"].to_numpy(dtype=float)
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        out[spec.name] = (da3, g3[spec.name].to_numpy(dtype=float), spec)
    gm = g.dropna(subset=["da", MISO_MANITOBA_SEAM_SPEC.name])
    out[MISO_MANITOBA_SEAM_SPEC.name] = (
        gm["da"].to_numpy(dtype=float),
        gm[MISO_MANITOBA_SEAM_SPEC.name].to_numpy(dtype=float),
        MISO_MANITOBA_SEAM_SPEC,
    )
    return out


def _lad_max_delta(a: dict, b: dict) -> float:
    return max(
        float(np.max(np.abs(np.asarray(a[s], float) - np.asarray(b[s], float))))
        for s in SIDES
    )


def _quantile_interpolation(x: np.ndarray, q: float) -> dict:
    """D-1': the two source prices ``np.quantile`` interpolates and the weight.

    ``method="linear"`` places the quantile at ``h = q * (n - 1)``; a landing on
    a half-cent — the tie ``round(-, 2)`` cannot resolve — shows here as a
    ``frac`` that puts ``lo``/``hi`` exactly astride one.
    """
    xs = np.sort(np.asarray(x, dtype=float))
    n = xs.size
    h = q * (n - 1)
    lo = int(np.floor(h))
    hi = min(lo + 1, n - 1)
    frac = float(h - lo)
    val = float(xs[lo] + frac * (xs[hi] - xs[lo]))
    return {
        "n": int(n),
        "q": float(q),
        "lo_index": lo,
        "frac": round(frac, 9),
        "x_lo": float(xs[lo]),
        "x_hi": float(xs[hi]),
        "value": val,
        # 0.0 here means the value lands EXACTLY on a half-cent, i.e. on the
        # boundary `round(-, 2)` cannot resolve — the tie signature.
        "cent_fraction_distance_to_half": round(abs(((val * 100.0) % 1.0) - 0.5), 9),
    }


def main() -> None:
    from market_sim.config.interchange_config import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED,
    )

    dm = _load_derive_module()
    eps = float(dm.NO_WASH_EPS)
    g_all = dm.load_joined()

    report: dict = {
        "probe": (
            "miso-244 phase 0 — diagnose the one-cent gap between "
            "MISO_SEAM_LADDER_BY_YEAR and its own derive at HEAD"
        ),
        "prereg": (
            "results/calibration/"
            "PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md"
        ),
        "keeper": "2026-09-07-miso-243-spp-pairing",
        "zero_lp": True,
        "read_only": True,
        "repairs_nothing": True,
        "queue_item": "miso-243 handoff RECOMMENDED item (its own §7.1 named successor)",
        "price_basis": (
            "incumbent ladder anchor = measured Indiana-hub DA "
            "(actual_lmp_hourly_MISO.parquet 'da'); SPP anchor where it appears = "
            "measured SPP NORTH hub DA; row sets = the derive's own per-seam dropna"
        ),
        "bars": {
            "tie_bar_t_max": TIE_BAR,
            "tol_corr": TOL_CORR,
            "identity_bar": IDENTITY_BAR,
            "half_cent": ROUND_TOL,
            "NO_WASH_EPS": eps,
        },
        "gates": {},
        "reported": {},
    }
    fails: list[str] = []

    # ---- D-6 (reported): the price column's stored dtype ---------------------
    raw_lmp = pd.read_parquet(dm.ACTUAL_LMP_PARQUET)
    report["reported"]["D6_da_dtype"] = {
        "on_disk_dtype": str(raw_lmp["da"].dtype),
        "rows": int(len(raw_lmp)),
        "sample": [float(v) for v in raw_lmp["da"].head(4)],
        "share_exactly_2dp_in_float64": round(
            float(
                (
                    np.abs(
                        raw_lmp["da"].to_numpy(dtype=float) * 100.0
                        - np.round(raw_lmp["da"].to_numpy(dtype=float) * 100.0)
                    )
                    < 1e-9
                ).mean()
            ),
            6,
        ),
    }

    # ========================= per-year raw capture ==========================
    raws: dict[int, dict] = {}
    derived: dict[int, dict] = {}
    notes_by_year: dict[int, list[str]] = {}
    for year in YEARS:
        g = g_all.loc[[year]]
        out, notes = dm.derive(g)
        derived[year] = out
        notes_by_year[year] = list(notes)
        samples = _seam_samples(dm, g)
        raws[year] = {
            name: _raw_one(da, flow, spec, eps)
            for name, (da, flow, spec) in samples.items()
        }

    # ---- G-RAW: instrument validity (round(raw,2) == derive(), all 192) ------
    graw = {"detail": {}, "max_abs_delta": 0.0, "PASS": True}
    for year in YEARS:
        worst = 0.0
        for seam in SEAMS:
            for side in SIDES:
                r = np.round(np.asarray(raws[year][seam][side], float), 2)
                d = np.asarray(derived[year][seam][side], float)
                worst = max(worst, float(np.max(np.abs(r - d))))
        graw["detail"][str(year)] = {"max_abs_delta": round(worst, 9)}
        graw["max_abs_delta"] = max(graw["max_abs_delta"], worst)
        graw["PASS"] &= bool(worst < 1e-9)
    report["gates"]["G_RAW"] = graw
    if not graw["PASS"]:
        fails.append("G-RAW")

    # ---- G-P2: reproduce miso-243's per-seam max |committed - derive| --------
    gp2 = {"detail": {}, "PASS": True}
    for year in YEARS:
        per_seam = {}
        for seam in SEAMS:
            c = {s: list(MISO_SEAM_LADDER_BY_YEAR[year][seam][s]) for s in SIDES}
            per_seam[seam] = round(_lad_max_delta(derived[year][seam], c), 6)
        ok = all(abs(per_seam[s] - REF_P2_PER_SEAM[year][s]) < 5e-3 for s in SEAMS)
        gp2["detail"][str(year)] = {
            "measured": per_seam,
            "reference": REF_P2_PER_SEAM[year],
            "PASS": bool(ok),
        }
        gp2["PASS"] &= bool(ok)
    report["gates"]["G_P2"] = gp2
    if not gp2["PASS"]:
        fails.append("G-P2")

    # ---- G-SPP / G-POOL: the repaired SPP hourly ladders reproduce at 0.0 ----
    gspp = {"detail": {}, "max_abs_delta": 0.0, "PASS": True}
    for year in YEARS:
        d, _n = dm.derive_spp_neighbour_hourly(g_all.loc[[year]])
        c = {
            s: list(MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][s])
            for s in SIDES
        }
        w = _lad_max_delta(d, c)
        gspp["detail"][str(year)] = {"max_abs_delta": round(w, 9)}
        gspp["max_abs_delta"] = max(gspp["max_abs_delta"], w)
        gspp["PASS"] &= bool(w == 0.0)
    report["gates"]["G_SPP"] = gspp
    if not gspp["PASS"]:
        fails.append("G-SPP")

    d_pool, _n = dm.derive_spp_neighbour_hourly(g_all.loc[YEARS[0] : YEARS[-1]])
    c_pool = {
        s: list(MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED["SPP"][s]) for s in SIDES
    }
    w_pool = _lad_max_delta(d_pool, c_pool)
    report["gates"]["G_POOL"] = {
        "max_abs_delta": round(w_pool, 9),
        "PASS": bool(w_pool == 0.0),
    }
    if w_pool != 0.0:
        fails.append("G-POOL")

    # ---- G-DOC + G-ROW: the derive docstring's corr, and the row sets --------
    hub = dm.load_spp_hub_da()
    hub_col = str(hub.name)
    gdoc = {"detail": {}, "PASS": True}
    grow = {"detail": {}, "PASS": True}
    for year in YEARS:
        base = g_all.loc[[year]]
        joined = base.join(hub, how="left")
        work = joined.dropna(subset=[hub_col, "da", "SPP"])
        c = float(
            np.corrcoef(
                work["SPP"].to_numpy(float),
                work["da"].to_numpy(float) - work[hub_col].to_numpy(float),
            )[0, 1]
        )
        ok_doc = abs(c - REF_DOC_CORR[year]) <= TOL_CORR
        gdoc["detail"][str(year)] = {
            "corr_measured_flow_vs_derive_spread": round(c, 4),
            "reference": REF_DOC_CORR[year],
            "abs_delta": round(abs(c - REF_DOC_CORR[year]), 4),
            "PASS": bool(ok_doc),
        }
        gdoc["PASS"] &= bool(ok_doc)
        ok_row = (
            len(base) == REF_ROWS_PER_YEAR
            and len(joined) == len(base)
            and len(work) == REF_N_RD[year]
        )
        grow["detail"][str(year)] = {
            "rows_in_year": int(len(base)),
            "rows_after_hub_join": int(len(joined)),
            "n_rows_R_D": int(len(work)),
            "reference_n_rows_R_D": REF_N_RD[year],
            "PASS": bool(ok_row),
        }
        grow["PASS"] &= bool(ok_row)
    report["gates"]["G_DOC"] = gdoc
    report["gates"]["G_ROW"] = grow
    if not gdoc["PASS"]:
        fails.append("G-DOC")
    if not grow["PASS"]:
        fails.append("G-ROW")

    # ---- I-1: the Q-Q identity, tested on the COMMITTED table ---------------
    i1 = {"detail": {}, "worst_excess": 0.0, "PASS": True}
    for year in YEARS:
        g = g_all.loc[[year]]
        samples = _seam_samples(dm, g)
        yr = {}
        worst_year = 0.0
        for seam in SEAMS:
            da, flow, _spec = samples[seam]
            mids = raws[year][seam]["mids"]
            seam_worst = 0.0
            for side in SIDES:
                cvals = MISO_SEAM_LADDER_BY_YEAR[year][seam][side]
                for k, cv in enumerate(cvals):
                    if side == "import":
                        target = float((flow > mids[k]).mean())
                        lo = float((da > cv).mean())
                        hi = float((da >= cv).mean())
                    else:
                        target = float((flow < -mids[k]).mean())
                        lo = float((da < cv).mean())
                        hi = float((da <= cv).mean())
                    excess = max(
                        0.0, lo - IDENTITY_BAR - target, target - hi - IDENTITY_BAR
                    )
                    seam_worst = max(seam_worst, excess)
            yr[seam] = round(seam_worst, 6)
            worst_year = max(worst_year, seam_worst)
        i1["detail"][str(year)] = {
            "worst_excess_by_seam": yr,
            "worst_excess": round(worst_year, 6),
            "PASS": bool(worst_year == 0.0),
        }
        i1["worst_excess"] = max(i1["worst_excess"], worst_year)
        i1["PASS"] &= bool(worst_year == 0.0)
    report["gates"]["I_1_identity"] = i1
    if not i1["PASS"]:
        fails.append("I-1")

    # ================= THE VERDICT (PREREG §2.3) =============================
    mismatches = []
    for year in YEARS:
        for seam in SEAMS:
            for side in SIDES:
                cvals = MISO_SEAM_LADDER_BY_YEAR[year][seam][side]
                rvals = raws[year][seam][side]
                for k, (cv, rv) in enumerate(zip(cvals, rvals)):
                    if abs(round(rv, 2) - float(cv)) >= 5e-9:
                        e = float(rv) - float(cv)
                        mismatches.append(
                            {
                                "year": year,
                                "seam": seam,
                                "side": side,
                                "band": k + 1,
                                "committed": float(cv),
                                "raw_head": rv,
                                "rounded_head": round(rv, 2),
                                "e_raw_minus_committed": e,
                                "abs_e": abs(e),
                                "t_past_half_cent": abs(e) - ROUND_TOL,
                                "is_clamped_export": bool(
                                    side == "export"
                                    and raws[year][seam]["clamped_export"][k]
                                ),
                            }
                        )
    t_max = max((m["t_past_half_cent"] for m in mismatches), default=float("-inf"))
    verdict = "V-ARTIFACT" if t_max <= TIE_BAR else "V-NOT-A-TIE"
    report["gates"]["VERDICT"] = {
        "rule": (
            "V-ARTIFACT iff t_max <= 1e-4 (rounding TIE); V-NOT-A-TIE otherwise "
            "(PREREG §2.3, fixed before any number existed)"
        ),
        "n_entries_compared": 192,
        "n_mismatching": len(mismatches),
        "t_max": None if not mismatches else round(t_max, 12),
        "VERDICT": verdict,
    }

    # ---- D-3 (reported): exact locations ------------------------------------
    report["reported"]["D3_mismatch_locations"] = [
        {
            **m,
            "raw_head": round(m["raw_head"], 10),
            "e_raw_minus_committed": round(m["e_raw_minus_committed"], 12),
            "abs_e": round(m["abs_e"], 12),
            "t_past_half_cent": round(m["t_past_half_cent"], 12),
        }
        for m in mismatches
    ]

    # ---- D-4 (reported): the no-wash clamp census ---------------------------
    report["reported"]["D4_clamp_census"] = {
        str(y): {
            "derive_notes": notes_by_year[y],
            "clamped_export_bands": {
                s: [k + 1 for k, f in enumerate(raws[y][s]["clamped_export"]) if f]
                for s in SEAMS
            },
            "clamp_lim_by_seam": {s: round(raws[y][s]["clamp_lim"], 6) for s in SEAMS},
        }
        for y in YEARS
    }

    # ---- D-5 (reported): the alternative clamp, taken off ROUNDED imports ----
    d5 = []
    for m in mismatches:
        r = raws[m["year"]][m["seam"]]
        alt = round(min(round(p, 2) for p in r["import"]) - eps, 2)
        d5.append(
            {
                "year": m["year"],
                "seam": m["seam"],
                "side": m["side"],
                "band": m["band"],
                "committed": m["committed"],
                "alt_clamp_from_rounded_imports": alt,
                "alt_reproduces_committed": bool(abs(alt - m["committed"]) < 5e-9),
            }
        )
    report["reported"]["D5_alternative_clamp"] = d5

    # ---- D-1' (reported): the tie mechanism --------------------------------
    d1p = []
    for m in mismatches:
        r = raws[m["year"]][m["seam"]]
        samples = _seam_samples(dm, g_all.loc[[m["year"]]])
        da = samples[m["seam"]][0]
        k = m["band"] - 1
        q = (
            1.0 - r["exceed_import"][k]
            if m["side"] == "import"
            else r["depth_export"][k]
        )
        info = _quantile_interpolation(da, q)
        d1p.append(
            {
                "year": m["year"],
                "seam": m["seam"],
                "side": m["side"],
                "band": m["band"],
                **info,
            }
        )
    report["reported"]["D1p_tie_mechanism"] = d1p

    # ---- D-1'' (reported PREDICTION, cannot move the verdict) ---------------
    # The ONE alternative construction named in PREREG §2.4, before any result:
    # snap `da` to exact cents in float64 (what a published LMP actually is) and
    # ask whether the committed table then reproduces at exactly 0.00 on all 192.
    d1pp = {"detail": {}, "max_abs_delta": 0.0, "reproduces_all_192": True}
    for year in YEARS:
        g = g_all.loc[[year]].copy()
        g["da"] = np.round(g["da"].to_numpy(dtype=float), 2)
        samples = _seam_samples(dm, g)
        worst = 0.0
        for seam in SEAMS:
            da, flow, spec = samples[seam]
            snapped = _raw_one(da, flow, spec, eps)
            for side in SIDES:
                a = np.round(np.asarray(snapped[side], float), 2)
                b = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam][side], float)
                worst = max(worst, float(np.max(np.abs(a - b))))
        d1pp["detail"][str(year)] = {"max_abs_delta": round(worst, 9)}
        d1pp["max_abs_delta"] = max(d1pp["max_abs_delta"], worst)
        d1pp["reproduces_all_192"] &= bool(worst < 5e-9)
    report["reported"]["D1pp_exact_cent_recompute"] = d1pp

    # ---- F6 liveness scope (reported): which rows reach a solve -------------
    kcfg = json.loads(
        (REPO / "results/calibration/miso243_sppair_K/run_config.json").read_text()
    )["scenario_config"]
    report["reported"]["F6_liveness_scope"] = {
        "keeper_flags": {
            f: kcfg.get(f)
            for f in (
                "miso_seam_measured_ladder",
                "miso_seam_neighbour_anchored_ladder",
                "miso_seam_neighbour_hourly_ladder",
                "miso_seam_neighbour_hourly_spp",
            )
        },
        "incumbent_rows_priced_into_the_LP": ["South", "Manitoba"],
        "note": (
            "inject_miso_seam_ladder_prices overlays the PJM hourly then the SPP "
            "hourly ladder on top of the incumbent table (alternatives, never "
            "stacked), so PJM and SPP incumbent rows are DISPLACED on this keeper"
        ),
        "live_mismatches": [
            f"{m['year']} {m['seam']} {m['side']} band {m['band']}"
            for m in mismatches
            if m["seam"] in ("South", "Manitoba")
        ],
        "inert_mismatches": [
            f"{m['year']} {m['seam']} {m['side']} band {m['band']}"
            for m in mismatches
            if m["seam"] not in ("South", "Manitoba")
        ],
    }

    report["FAILED_LEGS"] = fails
    report["ALL_GATED_LEGS_PASS"] = not fails
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["gates"], indent=1))
    print(json.dumps(report["reported"]["D3_mismatch_locations"], indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
