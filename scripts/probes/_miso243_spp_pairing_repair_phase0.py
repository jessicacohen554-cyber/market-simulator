#!/usr/bin/env python3
"""miso-243 phase 0 — REPAIR THE PER-YEAR SPP HOURLY LADDER'S CROSS-YEAR PAIRING.

ZERO LP. READ-ONLY: this probe changes no file, commits no table and applies no
repair. It runs the six provenance legs and the four phase-0 legs
pre-registered in
``results/calibration/PREREG-miso243-repair-the-spp-ladders-cross-year-pairing-2026-09-07.md``,
which was pushed together with this file and BEFORE either was run.

The legs, all with bars fixed in that document:

* **G-T**   the committed SPP + PJM hourly tuples equal PREREG §0 F4, and every
            ladder is monotone in its own clearing direction.
* **G-V1**  the MISPAIRED join returns 26,280 rows in three equal hub-year
            blocks with 0.0 deviation on ``da`` and the SPP flow.
* **G-V2**  the MISPAIRED frame reproduces the COMMITTED table, all 48 entries.
* **G-V3**  CONTROL — PJM's no-join derive reproduces its own committed table.
* **G-V5**  the POOLED forward ladder is correctly paired and reproduces.
* **G-DOC** the derive script's own docstring statistic
            ``corr(measured SPP seam flow, MISO DA - SPP hub DA)``
            = +0.041 / -0.020 / +0.050.
* **P-1**   THE FALSIFIABLE IDENTITY LEG: does the repaired ladder close the
            Q-Q identity ``|Z_derive - Z_target| <= 0.005`` in all three years?
* **P-2**   THE BYTE-IDENTITY LEG: the caller change moves nothing else.
* **P-3**   the mechanism's OWN MEASURED FOOTPRINT ``F(year)`` and the
            screen-year rule ``argmax F``.
* **P-4**   the PRE-SOLVE PREDICTION ``dq_hat`` on the MODEL basis (sets G-3's
            bar) and on the DERIVE basis (reported).

Dead-band and band-count membership are evaluated in the instrument's OWN TWO
OPERAND FORMS (miso-242 §0a): the import leg tests a SPREAD (a subtraction),
the export leg a LEVEL (an addition). An algebraic rearrangement is exact in
real arithmetic and NOT in IEEE at ties, and it cost miso-242 a failed gate on
43 exact-tie hours.

Usage:
    python3 scripts/probes/_miso243_spp_pairing_repair_phase0.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso233_sppseam_K"
CAL = REPO / "results/calibration"
OUT = CAL / "_miso243_spp_pairing_repair_phase0.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
BUS_OF_SEAM_SPP = "MISO_external"

# ---- PREREG bars, fixed ex ante ----
TOL_LADDER = 0.005  # G-V2 / G-V3 / G-V5 / P-2
TOL_CORR = 0.002  # G-DOC
P1_BAR = 0.005  # P-1, the identity leg — 4x tighter than miso-242's Q-A bar
MID_1 = 250.0  # interface_limit_mw / SEAM_FLOW_TRANCHES / 2 = 4000/8/2 (an identity)
STEP = 500.0  # interface_limit_mw / SEAM_FLOW_TRANCHES

# PREREG §0 F4 — the committed frozen SPP table, restated HERE so G-T binds even
# if the registry module is unreadable, and so this probe survives any
# predecessor artifact being absent.
REF_LADDER_SPP = {
    2023: {
        "import": (14.10, 32.64, 54.43, 85.36, 145.25, 185.08, 185.08, 185.08),
        "export": (-4.20, -24.96, -47.33, -92.59, -241.46, -521.38, -521.38, -521.38),
    },
    2024: {
        "import": (14.49, 35.59, 78.29, 212.51, 290.73, 290.73, 290.73, 290.73),
        "export": (-2.15, -19.39, -33.38, -42.97, -54.84, -64.17, -70.15, -83.23),
    },
    2025: {
        "import": (21.85, 46.55, 87.43, 169.08, 216.02, 252.76, 276.99, 345.40),
        "export": (1.04, -14.46, -29.20, -45.92, -125.99, -316.80, -515.34, -515.34),
    },
}
# PJM band 1 (import, export), the G-T comparator.
REF_LADDER_PJM_BAND1 = {
    2023: (-29.17, -93.98),
    2024: (-13.87, -35.03),
    2025: (-15.79, -60.49),
}
# miso-242 V-1's published block structure, restated for G-V1.
REF_V1_ROWS = 26280
REF_V1_BLOCKS = {"2023": 8760, "2024": 8760, "2025": 8760}
# The derive script's own docstring statistic, restated for G-DOC.
REF_DOC_CORR = (0.041, -0.020, 0.050)


def _load_derive():
    """Import ``scripts/data/derive_miso_seam_ladders.py`` as a module."""
    spec = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _band_counts(
    x: np.ndarray, anchor: np.ndarray, imp: np.ndarray, exp: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(n_import, n_export)`` in the instrument's OWN two operand forms.

    The import leg tests a SPREAD (``x - anchor > delta``); the export leg a
    LEVEL (``x < anchor + delta``). Never a rearrangement of either
    (miso-242 ADDENDUM "the dead-band predicate was a rearrangement").
    """
    spread = x - anchor
    n_i = np.zeros(x.shape[0], dtype=int)
    n_e = np.zeros(x.shape[0], dtype=int)
    for d in imp:
        n_i += (spread > d).astype(int)
    for d in exp:
        n_e += (x < anchor + d).astype(int)
    return n_i, n_e


def _in_dead_band(
    x: np.ndarray, anchor: np.ndarray, d_imp1: float, d_exp1: float
) -> np.ndarray:
    """Dead-band membership, in the instrument's own two operand forms."""
    return ((x - anchor) <= d_imp1) & (x >= anchor + d_exp1)


def _lad_delta(a: dict, b: dict) -> float:
    """Max abs deviation between two ``{"import": [...], "export": [...]}``."""
    out = 0.0
    for side in ("import", "export"):
        out = max(
            out,
            float(
                np.max(
                    np.abs(
                        np.asarray(a[side], dtype=float)
                        - np.asarray(b[side], dtype=float)
                    )
                )
            ),
        )
    return out


def main() -> None:
    """Run every pre-registered leg and write the phase-0 JSON."""
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED,
    )

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    dm = _load_derive()
    g_all = dm.load_joined()
    hub_col = dm.SPP_ANCHOR_HUB
    spp_hub_da = dm.load_spp_hub_da()

    report = {
        "probe": (
            "miso-243 phase 0 — repair the per-year SPP hourly ladder's "
            "cross-year pairing (CONSTRUCTION defect, rule 14 / rule 23)"
        ),
        "prereg": (
            "results/calibration/PREREG-miso243-repair-the-spp-ladders-"
            "cross-year-pairing-2026-09-07.md"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "read_only": True,
        "repairs_nothing_in_this_file": True,
        "queue_item": "miso-242 handoff RECOMMENDED item",
        "price_basis": (
            "ok mask = Indiana hub RT finite; every spread = Indiana hub DA; "
            "SPP anchor = measured SPP NORTH hub DA; p_bus = keeper "
            "MISO_external P1 price"
        ),
        "bars": {
            "tol_ladder": TOL_LADDER,
            "tol_corr": TOL_CORR,
            "p1_identity_bar": P1_BAR,
            "mid_1_mw": MID_1,
            "step_mw": STEP,
        },
        "gates": {},
        "years": {},
    }
    fails: list[str] = []

    # ============ G-T — the committed tables and their monotonicity ============
    gt = {"ladder_matches_prereg": True, "monotonicity_violations": 0, "detail": {}}
    for year in YEARS:
        spp = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]
        pjm = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]
        ok_i = tuple(spp["import"]) == REF_LADDER_SPP[year]["import"]
        ok_e = tuple(spp["export"]) == REF_LADDER_SPP[year]["export"]
        ok_p = (pjm["import"][0], pjm["export"][0]) == REF_LADDER_PJM_BAND1[year]
        viol = 0
        for lad in (spp, pjm):
            viol += int((np.diff(np.asarray(lad["import"], float)) < 0).sum())
            viol += int((np.diff(np.asarray(lad["export"], float)) > 0).sum())
        gt["ladder_matches_prereg"] &= bool(ok_i and ok_e and ok_p)
        gt["monotonicity_violations"] += viol
        gt["detail"][str(year)] = {
            "spp_import_matches": bool(ok_i),
            "spp_export_matches": bool(ok_e),
            "pjm_band1_matches": bool(ok_p),
            "monotonicity_violations": viol,
        }
    gt["PASS"] = bool(
        gt["ladder_matches_prereg"] and gt["monotonicity_violations"] == 0
    )
    report["gates"]["G_T"] = gt
    if not gt["PASS"]:
        fails.append("G-T")

    # ============ G-V1 / G-V2 / G-V3 / G-V5 — the pairing legs ================
    v1 = {"detail": {}, "PASS": True}
    v2 = {"detail": {}, "max_abs_delta": 0.0, "PASS": True}
    v3 = {"detail": {}, "max_abs_delta": 0.0, "PASS": True}

    mispaired: dict[int, dict] = {}
    repaired: dict[int, dict] = {}

    for year in YEARS:
        # --- the MISPAIRED frame: the defective call, df.loc[year] ---
        g_mis = g_all.loc[year]
        j_mis = g_mis.join(spp_hub_da, how="left")
        blocks = (
            j_mis.index.get_level_values("year").value_counts().sort_index().to_dict()
            if j_mis.index.nlevels > 1
            else {}
        )
        # the replication signature: da and flow identical across hub-year blocks
        dev_da = dev_fl = 0.0
        if j_mis.index.nlevels > 1:
            piv_da = j_mis.reset_index().pivot_table(
                index="hour", columns="year", values="da"
            )
            piv_fl = j_mis.reset_index().pivot_table(
                index="hour", columns="year", values="SPP"
            )
            dev_da = float(np.nanmax(np.abs(piv_da.sub(piv_da.iloc[:, 0], axis=0))))
            dev_fl = float(np.nanmax(np.abs(piv_fl.sub(piv_fl.iloc[:, 0], axis=0))))
        ok_v1 = (
            len(j_mis) == REF_V1_ROWS
            and {str(k): int(v) for k, v in blocks.items()} == REF_V1_BLOCKS
            and dev_da == 0.0
            and dev_fl == 0.0
        )
        v1["detail"][str(year)] = {
            "join_rows": int(len(j_mis)),
            "expected_rows": REF_V1_ROWS,
            "hub_year_blocks": {str(k): int(v) for k, v in blocks.items()},
            "max_abs_da_deviation_across_blocks": dev_da,
            "max_abs_flow_deviation_across_blocks": dev_fl,
            "PASS": bool(ok_v1),
        }
        v1["PASS"] &= bool(ok_v1)

        lad_mis, _ = dm.derive_spp_neighbour_hourly(g_mis)
        mispaired[year] = lad_mis
        committed = {
            k: list(v)
            for k, v in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year][
                "SPP"
            ].items()
        }
        d2 = _lad_delta(lad_mis, committed)
        v2["detail"][str(year)] = {
            "mispaired": lad_mis,
            "committed": committed,
            "max_abs_delta": round(d2, 6),
            "PASS": bool(d2 <= TOL_LADDER),
        }
        v2["max_abs_delta"] = max(v2["max_abs_delta"], d2)
        v2["PASS"] &= bool(d2 <= TOL_LADDER)

        # --- the REPAIRED frame: df.loc[[year]] keeps the (year, hour) MultiIndex ---
        g_rep = g_all.loc[[year]]
        j_rep = g_rep.join(spp_hub_da, how="left")
        lad_rep, notes_rep = dm.derive_spp_neighbour_hourly(g_rep)
        repaired[year] = lad_rep
        v1["detail"][str(year)]["repaired_join_rows"] = int(len(j_rep))
        v1["detail"][str(year)]["repaired_input_rows"] = int(len(g_rep))
        v1["detail"][str(year)]["repaired_row_count_preserved"] = bool(
            len(j_rep) == len(g_rep)
        )
        v1["detail"][str(year)]["repaired_notes"] = list(notes_rep)

        # --- G-V3 CONTROL: PJM's no-join derive, on the repaired frame ---
        lad_pjm, _ = dm.derive_pjm_neighbour_hourly(g_rep)
        committed_pjm = {
            k: list(v)
            for k, v in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"].items()
        }
        d3 = _lad_delta(lad_pjm, committed_pjm)
        v3["detail"][str(year)] = {
            "max_abs_delta": round(d3, 6),
            "PASS": bool(d3 <= TOL_LADDER),
        }
        v3["max_abs_delta"] = max(v3["max_abs_delta"], d3)
        v3["PASS"] &= bool(d3 <= TOL_LADDER)

    report["gates"]["G_V1"] = v1
    report["gates"]["G_V2"] = v2
    report["gates"]["G_V3_control_pjm"] = v3
    for name, leg in (("G-V1", v1), ("G-V2", v2), ("G-V3", v3)):
        if not leg["PASS"]:
            fails.append(name)

    # --- G-V5: the POOLED forward ladder, already correctly paired ---
    pooled_frame = g_all.loc[YEARS[0] : YEARS[-1]]
    lad_pool, _ = dm.derive_spp_neighbour_hourly(pooled_frame)
    committed_pool = {
        k: list(v)
        for k, v in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED["SPP"].items()
    }
    d5 = _lad_delta(lad_pool, committed_pool)
    j_pool = pooled_frame.join(spp_hub_da, how="left")
    report["gates"]["G_V5_pooled_forward"] = {
        "derived": lad_pool,
        "committed": committed_pool,
        "max_abs_delta": round(d5, 6),
        "join_rows": int(len(j_pool)),
        "input_rows": int(len(pooled_frame)),
        "row_count_preserved": bool(len(j_pool) == len(pooled_frame)),
        "PASS": bool(d5 <= TOL_LADDER),
    }
    if d5 > TOL_LADDER:
        fails.append("G-V5")

    # ================= P-2 — THE BYTE-IDENTITY LEG ============================
    p2 = {"detail": {}, "max_abs_delta": 0.0, "PASS": True}
    for year in YEARS:
        g_rep = g_all.loc[[year]]
        inc, _ = dm.derive(g_rep)
        worst = 0.0
        per_seam = {}
        for seam, lad in inc.items():
            ref = MISO_SEAM_LADDER_BY_YEAR[year].get(seam)
            if ref is None:
                per_seam[seam] = "ABSENT_FROM_REGISTRY"
                continue
            d = _lad_delta(lad, {k: list(v) for k, v in ref.items()})
            per_seam[seam] = round(d, 6)
            worst = max(worst, d)
        nb, _ = dm.derive_pjm_neighbour(g_rep)
        ref_nb = MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[year]["PJM"]
        d_nb = _lad_delta(nb, {k: list(v) for k, v in ref_nb.items()})
        worst = max(worst, d_nb)
        hb, _ = dm.derive_pjm_neighbour_hourly(g_rep)
        ref_hb = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]
        d_hb = _lad_delta(hb, {k: list(v) for k, v in ref_hb.items()})
        worst = max(worst, d_hb)
        p2["detail"][str(year)] = {
            "incumbent_per_seam_max_abs_delta": per_seam,
            "pjm_annual_neighbour_max_abs_delta": round(d_nb, 6),
            "pjm_hourly_neighbour_max_abs_delta": round(d_hb, 6),
            "worst": round(worst, 6),
            "PASS": bool(worst <= TOL_LADDER),
        }
        p2["max_abs_delta"] = max(p2["max_abs_delta"], worst)
        p2["PASS"] &= bool(worst <= TOL_LADDER)
    report["gates"]["P_2_byte_identity"] = p2
    if not p2["PASS"]:
        fails.append("P-2")

    # ============ per-year: G-DOC, P-1, P-3, P-4 ==============================
    from market_sim.data.eia_loader import measured_miso_spp_hub_prices

    doc = {"detail": {}, "PASS": True}
    p1 = {"detail": {}, "PASS": True}
    p3 = {"detail": {}}
    p4 = {"detail": {}}

    for yi, year in enumerate(YEARS):
        # ---- R_D, the DERIVE row set: dropna after a CORRECT join ----
        work = g_all.loc[[year]].join(spp_hub_da, how="left")
        work = work.dropna(subset=[hub_col, "da", "SPP"])
        da_d = work["da"].to_numpy(float)
        hub_d = work[hub_col].to_numpy(float)
        flow_d = work["SPP"].to_numpy(float)
        spread_d = da_d - hub_d

        # ---- G-DOC: the derive script's own docstring statistic ----
        c = float(np.corrcoef(flow_d, spread_d)[0, 1])
        ok_doc = abs(c - REF_DOC_CORR[yi]) <= TOL_CORR
        doc["detail"][str(year)] = {
            "corr_measured_flow_vs_derive_spread": round(c, 4),
            "reference": REF_DOC_CORR[yi],
            "abs_delta": round(abs(c - REF_DOC_CORR[yi]), 4),
            "PASS": bool(ok_doc),
        }
        doc["PASS"] &= bool(ok_doc)

        lad_c = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]
        imp_c = np.asarray(lad_c["import"], float)
        exp_c = np.asarray(lad_c["export"], float)
        imp_r = np.asarray(repaired[year]["import"], float)
        exp_r = np.asarray(repaired[year]["export"], float)

        # ---- P-1: THE FALSIFIABLE IDENTITY LEG ----
        z_target = float((np.abs(flow_d) <= MID_1).mean())
        z_com = float(_in_dead_band(da_d, hub_d, imp_c[0], exp_c[0]).mean())
        z_rep = float(_in_dead_band(da_d, hub_d, imp_r[0], exp_r[0]).mean())
        d_com = abs(z_com - z_target)
        d_rep = abs(z_rep - z_target)
        ok_p1 = d_rep <= P1_BAR
        p1["detail"][str(year)] = {
            "n_rows_R_D": int(len(work)),
            "Z_target": round(z_target, 4),
            "Z_derive_committed": round(z_com, 4),
            "Z_derive_repaired": round(z_rep, 4),
            "abs_delta_committed": round(d_com, 4),
            "abs_delta_repaired": round(d_rep, 4),
            "dead_band_committed": [
                round(float(exp_c[0]), 2),
                round(float(imp_c[0]), 2),
            ],
            "dead_band_repaired": [
                round(float(exp_r[0]), 2),
                round(float(imp_r[0]), 2),
            ],
            "PASS": bool(ok_p1),
        }
        p1["PASS"] &= bool(ok_p1)

        # ---- P-3: THE FOOTPRINT, on R_D, zero model input ----
        ni_c, ne_c = _band_counts(da_d, hub_d, imp_c, exp_c)
        ni_r, ne_r = _band_counts(da_d, hub_d, imp_r, exp_r)
        differs = (ni_c != ni_r) | (ne_c != ne_r)
        F = float(differs.mean())
        p3["detail"][str(year)] = {
            "F_share_of_R_D_rows_with_changed_band_counts": round(F, 6),
            "n_rows_R_D": int(len(work)),
            "n_rows_changed": int(differs.sum()),
            "mean_n_import_committed": round(float(ni_c.mean()), 4),
            "mean_n_import_repaired": round(float(ni_r.mean()), 4),
            "mean_n_export_committed": round(float(ne_c.mean()), 4),
            "mean_n_export_repaired": round(float(ne_r.mean()), 4),
        }

        # ---- P-4: THE PRE-SOLVE PREDICTION, on BOTH bases ----
        # derive basis (reported)
        dq_derive = STEP * (
            (float(ni_r.mean()) - float(ni_c.mean()))
            - (float(ne_r.mean()) - float(ne_c.mean()))
        )
        # model basis (SETS G-3's BAR): the keeper's committed MISO_external P1 price
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok_mask = np.isfinite(act)
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        p_bus = (
            sysf[sysf["zone"] == BUS_OF_SEAM_SPP]
            .sort_values("hour")["price"]
            .to_numpy(float)
        )
        hub_k = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)
        pb = p_bus[ok_mask]
        hk = hub_k[ok_mask]
        mi_c, me_c = _band_counts(pb, hk, imp_c, exp_c)
        mi_r, me_r = _band_counts(pb, hk, imp_r, exp_r)
        dq_model = STEP * (
            (float(mi_r.mean()) - float(mi_c.mean()))
            - (float(me_r.mean()) - float(me_c.mean()))
        )
        p4["detail"][str(year)] = {
            "dq_hat_model_basis_mw": round(dq_model, 2),
            "dq_hat_derive_basis_mw": round(dq_derive, 2),
            "n_rows_R_K": int(ok_mask.sum()),
            "model_mean_n_import_committed": round(float(mi_c.mean()), 4),
            "model_mean_n_import_repaired": round(float(mi_r.mean()), 4),
            "model_mean_n_export_committed": round(float(me_c.mean()), 4),
            "model_mean_n_export_repaired": round(float(me_r.mean()), 4),
            "model_band_count_change_share": round(
                float(((mi_c != mi_r) | (me_c != me_r)).mean()), 6
            ),
        }

    report["gates"]["G_DOC"] = doc
    report["gates"]["P_1_identity"] = p1
    report["P_3_footprint"] = p3
    report["P_4_presolve_prediction"] = p4
    if not doc["PASS"]:
        fails.append("G-DOC")
    if not p1["PASS"]:
        fails.append("P-1")

    # ---- the screen-year rule, applied to P-3 (argmax F, ties -> earliest) ----
    fvals = {
        y: p3["detail"][str(y)]["F_share_of_R_D_rows_with_changed_band_counts"]
        for y in YEARS
    }
    best = max(YEARS, key=lambda y: (fvals[y], -y))
    report["screen_year"] = {
        "rule": "argmax_year F(year); ties break to the EARLIEST year (PREREG §2.3)",
        "F_by_year": {str(y): fvals[y] for y in YEARS},
        "SCREEN_YEAR": int(best),
        "basis": (
            "measured MISO hub DA spread, measured SPP NORTH hub DA, and the two "
            "ladders. ZERO model output, zero scored criterion, zero residual."
        ),
    }

    report["repaired_ladder"] = {
        str(y): {k: list(v) for k, v in repaired[y].items()} for y in YEARS
    }
    report["committed_ladder"] = {
        str(y): {
            k: list(v)
            for k, v in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[y]["SPP"].items()
        }
        for y in YEARS
    }
    report["FAILED_LEGS"] = fails
    report["ALL_LEGS_PASS"] = not fails

    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "years"}, indent=1)[:1])
    print(f"wrote {OUT}")
    print("FAILED LEGS:", fails or "NONE")
    print(
        "SCREEN YEAR:",
        report["screen_year"]["SCREEN_YEAR"],
        report["screen_year"]["F_by_year"],
    )


if __name__ == "__main__":
    main()
