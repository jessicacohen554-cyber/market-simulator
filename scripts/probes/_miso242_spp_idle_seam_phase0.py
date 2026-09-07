"""miso-242 phase 0 — why is the model's SPP seam at EXACTLY ZERO flow in 42/41/48 % of hours?

Pre-registration:
``results/calibration/PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md``, pushed
together with this file and BEFORE either was run. Every decision rule applied here is
fixed in that document; nothing below selects anything.

The queue item is item 1 of the miso-241 handoff — the RECOMMENDED item and the first
thing miso-241 surfaced that nobody has explained. The PREREG's §0 F3/F4/F5 reduce it to
an arithmetic decomposition:

* the seam is at exactly zero iff its spread sits in the DEAD BAND
  ``[delta_1^export, delta_1^import]`` (F3, GATED by G-DB, not assumed);
* the Q-Q estimator sets those two thresholds to the quantiles matching
  ``P(flow > +250)`` and ``P(flow < -250)``, so ON ITS OWN SPREAD the dead band captures
  exactly ``P(|measured flow| <= 250 MW)`` (F5);
* therefore three shares decide the question — ``Z_target`` (measured), ``Z_derive`` (the
  committed table on the derive's spread) and ``Z_model`` (the same table on the model's
  bus-price spread).

Four legs:

* **Provenance gate (PREREG §1, six legs).** The committed ladder tuples and their
  monotonicity; miso-241 §3's zero-flow and env-zero shares; miso-241 §3's
  ceiling_active_share and mean bands in merit; miso-241's prefix identity on both legs of
  both variants of all four seams; miso-241 Q-0's REPAIRED harness; and the dead-band
  identity itself. If ANY leg fails the instrument is BROKEN and no Q is read.
* **Q-A (PREREG §2).** Does the COMMITTED, ROUNDED table reproduce its own estimator's
  target on the derive's own row set? Bar ``|Z_derive - Z_target| <= 0.020``.
* **Q-B (PREREG §3).** Does the MODEL's spread transmit the derive basis, or displace it?
  Bar ``|Z_model - Z_derive^K| <= 0.050`` on ONE common row set.
* **Q-D / Q-E (PREREG §4a/§4b).** The PJM contrast (gated on one thing only) and the
  sign/basis leg (E1 gated, E2 reported).

The model side is the REPAIRED four-seam reconstruction: ``build_recons``,
``identity_check`` and ``classify_leg`` are IMPORTED from
``_miso241_spp_quantity_side_charter_phase0`` rather than re-typed, so this session cannot
silently revert to miso-235's superseded export pricing — and G-B checks that it did not.

Basis discipline (PREREG §0b): the Indiana-hub RT series builds the finite-hour ``ok``
mask; every spread is on the Indiana-hub DA; the SPP anchor is the measured SPP NORTH hub
DA. They are never interchanged.

Rule 23 [R-FROZEN-DERIVE]: nothing here re-derives anything. The committed ladder is READ
and is not modified; the one call to ``derive_spp_neighbour_hourly`` below is a read-only
verification whose output is REPORTED and gated nowhere.

Usage: python3 scripts/probes/_miso242_spp_idle_seam_phase0.py
"""

from __future__ import annotations

import importlib
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
MISO241 = CAL / "_miso241_spp_quantity_side_charter_phase0.json"
OUT = CAL / "_miso242_spp_idle_seam_phase0.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
FOUR_SEAM = ("PJM", "SPP", "South", "Manitoba")
BUS_OF_SEAM = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}

# ---- PREREG §1 bars, fixed ex ante ----
TOL_SHARE = 0.002  # G-Z, G-L (ceiling leg)
TOL_MEAN_N = 0.01  # G-L (mean-bands leg)
TOL_ID_MW = 1e-6  # G-ID
TOL_CORR = 0.002  # G-B (corr leg)
TOL_LEVEL_MW = 0.5  # G-B (level leg)

# ---- PREREG §2/§3/§4a/§4b bars, fixed ex ante ----
QA_BAR = 0.020
QB_BAR = 0.050

# PREREG §1 reference values, restated HERE so every leg binds even if miso-241's JSON
# artifact is missing (the lane's "survive the artifact being absent" duty).
REF_ZERO_SHARE_SPP = (0.4175, 0.4066, 0.4810)
REF_ENV_I_ZERO_SPP = (0.0106, 0.0035, 0.0034)
REF_CEILING_SHARE_SPP = (0.2572, 0.2952, 0.2474)
REF_MEAN_N_IMPORT_SPP = (0.50, 0.49, 0.33)
REF_HARNESS_CORR_REPAIRED = (0.9917, 0.9935, 0.9935)
REF_HARNESS_LEVEL_REPAIRED = (8.9, 1.8, 5.8)

# PREREG §0 F2 — the committed frozen tables, quoted in the PREREG and pinned by G-T.
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
REF_LADDER_PJM_BAND1 = {
    2023: (-29.17, -93.98),
    2024: (-13.87, -35.03),
    2025: (-15.79, -60.49),
}

M1 = importlib.import_module("_miso241_spp_quantity_side_charter_phase0")
build_recons = M1.build_recons
identity_check = M1.identity_check
classify_leg = M1.classify_leg


def _json(path: Path):
    """Committed predecessor artifact, or ``None`` when absent (the gate still binds)."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def share_in_band(x: np.ndarray, lo: float, hi: float) -> float:
    """``P(lo <= x <= hi)`` — the DEAD-BAND share (PREREG §0 F3), closed on both edges."""
    return float(((x >= lo) & (x <= hi)).mean())


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation, NaN-safe on a degenerate series."""
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> int:  # noqa: PLR0912, PLR0915 - one linear probe, PREREG section order
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import (
        measured_miso_spp_hub_prices,
        measured_seam_import_envelope,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_MANITOBA_SEAM_SPEC,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    ladders = (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()
    hub_col = dm.SPP_ANCHOR_HUB
    spp_hub_da = dm.load_spp_hub_da()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    prior241 = _json(MISO241)

    # --- R_D, the DERIVE row set (PREREG §0c): dropna on (hub, MISO DA, seam flow) ---
    work_all = g_all.join(spp_hub_da, how="left")

    report = {
        "probe": (
            "miso-242 phase 0 — why is the model's SPP seam at EXACTLY ZERO in "
            "42/41/48 % of hours?"
        ),
        "prereg": (
            "results/calibration/PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "queue_item": "miso-241 handoff item 1 (RECOMMENDED)",
        "price_basis": (
            "ok mask = Indiana hub RT finite; every spread = Indiana hub DA; "
            "SPP anchor = measured SPP NORTH hub DA; p_bus = keeper MISO_external P1"
        ),
        "bars": {
            "tol_share": TOL_SHARE,
            "tol_mean_n": TOL_MEAN_N,
            "tol_identity_mw": TOL_ID_MW,
            "tol_corr": TOL_CORR,
            "tol_level_mw": TOL_LEVEL_MW,
            "qa_bar": QA_BAR,
            "qb_bar": QB_BAR,
        },
        "predecessor_artifacts": {"miso241": MISO241.name if prior241 else "ABSENT"},
        "years": {},
    }

    # ================= G-T (PREREG §1) — the committed tables and their monotonicity ===
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
            "spp_dead_band": [spp["export"][0], spp["import"][0]],
            "spp_dead_band_width": round(spp["import"][0] - spp["export"][0], 2),
            "pjm_dead_band": [pjm["export"][0], pjm["import"][0]],
            "pjm_dead_band_width": round(pjm["import"][0] - pjm["export"][0], 2),
        }
    gt["PASS"] = bool(
        gt["ladder_matches_prereg"] and gt["monotonicity_violations"] == 0
    )
    report["G_T"] = gt

    gate_fail: list[str] = []
    if not gt["PASS"]:
        gate_fail.append("G-T")

    for yi, year in enumerate(YEARS):
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)

        def dense(col: str) -> np.ndarray:
            return (
                gy[col]
                .reindex(range(HOURS))
                .interpolate(limit=3)
                .ffill()
                .bfill()
                .to_numpy(float)
            )

        border = dense("pjm_border")
        da = dense("da")
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)
        anchors = {"PJM": border, "SPP": spp_hub}

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        committed = (
            cls.groupby("hour")["mw"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0.0)
            .to_numpy(float)
        )[ok]

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]

        R: dict[str, dict] = {}
        widths: dict[str, float] = {}
        for seam in FOUR_SEAM:
            widths[seam] = float(specs[seam].interface_limit_mw) / SEAM_FLOW_TRANCHES
            R[seam] = build_recons(
                seam,
                year,
                bus_price[BUS_OF_SEAM[seam]],
                anchors,
                env_i,
                env_e,
                widths[seam],
                ks,
                ladders,
            )
        meas_net = {s: dense(s) for s in FOUR_SEAM}

        pv: dict[str, dict] = {}

        # --- G-Z: miso-241 §3's zero-flow share and env_i-zero share on SPP ---
        zero_share = float(
            ((R["SPP"]["n_i"][ok] == 0) & (R["SPP"]["n_e_repaired"][ok] == 0)).mean()
        )
        env_i_zero = float((R["SPP"]["env_i_eff"][ok] <= 1e-9).mean())
        ref_zero = REF_ZERO_SHARE_SPP[yi]
        ref_env0 = REF_ENV_I_ZERO_SPP[yi]
        if prior241:
            q1p = prior241["years"][str(year)]["Q1"]["SPP"]
            ref_zero = q1p.get("share_seam_exactly_zero_repaired", ref_zero)
            ref_env0 = q1p.get("env_i_zero_share", ref_env0)
        pv["G_Z"] = {
            "zero_share_recomputed": round(zero_share, 4),
            "zero_share_reference": ref_zero,
            "abs_delta_zero": round(abs(zero_share - float(ref_zero)), 4),
            "env_i_zero_recomputed": round(env_i_zero, 4),
            "env_i_zero_reference": ref_env0,
            "abs_delta_env_i_zero": round(abs(env_i_zero - float(ref_env0)), 4),
        }
        if (
            pv["G_Z"]["abs_delta_zero"] > TOL_SHARE
            or pv["G_Z"]["abs_delta_env_i_zero"] > TOL_SHARE
        ):
            gate_fail.append(f"G-Z {year}")

        # --- G-L: miso-241 §3's ceiling_active_share and mean import bands in merit ---
        leg_i = classify_leg(
            R["SPP"]["n_i"][ok], R["SPP"]["env_i_eff"][ok], widths["SPP"]
        )
        leg_e = classify_leg(
            R["SPP"]["n_e_repaired"][ok], R["SPP"]["env_e_eff"][ok], widths["SPP"]
        )
        ceil_share = float((leg_i["ceiling"] | leg_e["ceiling"]).mean())
        mean_n = float(leg_i["mean_n"])
        ref_ceil = REF_CEILING_SHARE_SPP[yi]
        ref_mn = REF_MEAN_N_IMPORT_SPP[yi]
        if prior241:
            q1p = prior241["years"][str(year)]["Q1"]["SPP"]
            ref_ceil = q1p.get("ceiling_active_share_repaired", ref_ceil)
            ref_mn = q1p.get("import", {}).get("mean_n", ref_mn)
        pv["G_L"] = {
            "ceiling_active_share_recomputed": round(ceil_share, 4),
            "ceiling_active_share_reference": ref_ceil,
            "abs_delta_ceiling": round(abs(ceil_share - float(ref_ceil)), 4),
            "mean_bands_in_merit_import_recomputed": round(mean_n, 4),
            "mean_bands_in_merit_import_reference": ref_mn,
            "abs_delta_mean_n": round(abs(mean_n - float(ref_mn)), 4),
        }
        if (
            pv["G_L"]["abs_delta_ceiling"] > TOL_SHARE
            or pv["G_L"]["abs_delta_mean_n"] > TOL_MEAN_N
        ):
            gate_fail.append(f"G-L {year}")

        # --- G-ID: the prefix identity, both legs of both variants, all four seams ---
        idmax = 0.0
        idviol = 0
        for seam in FOUR_SEAM:
            w = widths[seam]
            for f, n, e in (
                (R[seam]["imp"], R[seam]["n_i"], R[seam]["env_i_eff"]),
                (
                    R[seam]["exp_incumbent"],
                    R[seam]["n_e_incumbent"],
                    R[seam]["env_e_eff"],
                ),
                (
                    R[seam]["exp_repaired"],
                    R[seam]["n_e_repaired"],
                    R[seam]["env_e_eff"],
                ),
            ):
                d, v = identity_check(f[ok], n[ok], e[ok], w)
                idmax = max(idmax, d)
                idviol += v
        pv["G_ID"] = {
            "max_abs_mw": float(f"{idmax:.3e}"),
            "total_prefix_violations": idviol,
        }
        if idmax > TOL_ID_MW or idviol:
            gate_fail.append(f"G-ID {year}")

        # --- G-B: miso-241 Q-0's REPAIRED harness (this IS the repaired instrument) ---
        rec4_rep = sum(R[s]["net_repaired"][ok] for s in FOUR_SEAM)
        h_corr = float(np.corrcoef(rec4_rep, committed)[0, 1])
        h_lvl = abs(float(rec4_rep.mean() - committed.mean()))
        ref_c = REF_HARNESS_CORR_REPAIRED[yi]
        ref_l = REF_HARNESS_LEVEL_REPAIRED[yi]
        if prior241:
            hp = prior241["years"][str(year)]["Q0"]["harness"]["repaired"]
            ref_c = hp.get("corr_recon_vs_committed", ref_c)
            ref_l = hp.get("mean_abs_level_error_mw", ref_l)
        pv["G_B"] = {
            "corr_recomputed": round(h_corr, 4),
            "corr_reference": ref_c,
            "abs_delta_corr": round(abs(h_corr - float(ref_c)), 4),
            "level_recomputed": round(h_lvl, 1),
            "level_reference": ref_l,
            "abs_delta_level_mw": round(abs(h_lvl - float(ref_l)), 2),
        }
        if (
            pv["G_B"]["abs_delta_corr"] > TOL_CORR
            or pv["G_B"]["abs_delta_level_mw"] > TOL_LEVEL_MW
        ):
            gate_fail.append(f"G-B {year}")

        # --- G-DB: the DEAD-BAND identity (PREREG §0 F3), SPP and PJM, on R_K ---
        s_model = {
            "SPP": (bus_price[BUS_OF_SEAM["SPP"]] - spp_hub)[ok],
            "PJM": (bus_price[BUS_OF_SEAM["PJM"]] - border)[ok],
        }
        s_derive_K = {
            "SPP": (da - spp_hub)[ok],
            "PJM": (da - border)[ok],
        }
        band1 = {
            "SPP": (
                float(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "export"
                    ][0]
                ),
                float(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ][0]
                ),
            ),
            "PJM": (
                float(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["export"][0]
                ),
                float(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"][0]
                ),
            ),
        }
        db = {}
        db_bad = 0
        for seam in ("SPP", "PJM"):
            lo, hi = band1[seam]
            from_counts = (R[seam]["n_i"][ok] == 0) & (R[seam]["n_e_repaired"][ok] == 0)
            from_band = (s_model[seam] >= lo) & (s_model[seam] <= hi)
            bad = int((from_counts != from_band).sum())
            db_bad += bad
            db[seam] = {
                "disagreeing_hours": bad,
                "share_from_counts": round(float(from_counts.mean()), 4),
                "share_from_dead_band": round(float(from_band.mean()), 4),
            }
        pv["G_DB"] = {"seams": db, "total_disagreeing_hours": db_bad}
        if db_bad:
            gate_fail.append(f"G-DB {year}")

        # ================= Q-A (PREREG §2) — the Q-Q identity, on R_D ==================
        wy = work_all.loc[year] if year in work_all.index.get_level_values(0) else None
        qa = {}
        for seam, hub_series, mid1 in (
            ("SPP", hub_col, 0.5 * widths["SPP"]),
            ("PJM", "pjm_border", 0.5 * widths["PJM"]),
        ):
            sub = wy.dropna(subset=[hub_series, "da", seam])
            spread_d = (sub["da"] - sub[hub_series]).to_numpy(float)
            flow_d = sub[seam].to_numpy(float)
            lo, hi = band1[seam]
            z_derive = share_in_band(spread_d, lo, hi)
            z_target = (
                1.0 - float((flow_d > mid1).mean()) - float((flow_d < -mid1).mean())
            )
            qa[seam] = {
                "n_rows_R_D": int(len(sub)),
                "mid1_mw": mid1,
                "Z_target": round(z_target, 4),
                "Z_derive": round(z_derive, 4),
                "abs_delta": round(abs(z_derive - z_target), 4),
                "P_flow_gt_mid1": round(float((flow_d > mid1).mean()), 4),
                "P_flow_lt_neg_mid1": round(float((flow_d < -mid1).mean()), 4),
                "spread_derive_mean": round(float(spread_d.mean()), 2),
                "spread_derive_sigma": round(float(spread_d.std()), 2),
                "measured_flow_mean_mw": round(float(flow_d.mean()), 1),
                "measured_flow_sigma_mw": round(float(flow_d.std()), 1),
            }
        qa["VERDICT"] = (
            "IDENTITY HOLDS" if qa["SPP"]["abs_delta"] <= QA_BAR else "IDENTITY FAILS"
        )

        # ================= Q-B (PREREG §3) — displacement, on the common R_K ===========
        qb = {}
        for seam in ("SPP", "PJM"):
            lo, hi = band1[seam]
            z_model = share_in_band(s_model[seam], lo, hi)
            z_der_k = share_in_band(s_derive_K[seam], lo, hi)
            qb[seam] = {
                "n_rows_R_K": int(ok.sum()),
                "Z_model": round(z_model, 4),
                "Z_derive_K": round(z_der_k, 4),
                "abs_delta": round(abs(z_model - z_der_k), 4),
                "signed_delta": round(z_model - z_der_k, 4),
                "mean_s_model": round(float(s_model[seam].mean()), 2),
                "mean_s_derive": round(float(s_derive_K[seam].mean()), 2),
                "sigma_s_model": round(float(s_model[seam].std()), 2),
                "sigma_s_derive": round(float(s_derive_K[seam].std()), 2),
            }
        qb["VERDICT"] = (
            "TRANSMITTED" if qb["SPP"]["abs_delta"] <= QB_BAR else "DISPLACED"
        )

        # ================= Q-D (PREREG §4a) — the PJM contrast ========================
        qd = {
            "gated_question": "Z_target(PJM) < Z_target(SPP)?",
            "Z_target_PJM": qa["PJM"]["Z_target"],
            "Z_target_SPP": qa["SPP"]["Z_target"],
            "PJM_lt_SPP": bool(qa["PJM"]["Z_target"] < qa["SPP"]["Z_target"]),
            "reported_not_gated": {
                "dead_band_width_SPP": gt["detail"][str(year)]["spp_dead_band_width"],
                "dead_band_width_PJM": gt["detail"][str(year)]["pjm_dead_band_width"],
                "Z_model_PJM": qb["PJM"]["Z_model"],
                "Z_derive_K_PJM": qb["PJM"]["Z_derive_K"],
                "import_leg_zero_share_PJM": round(
                    float((R["PJM"]["n_i"][ok] == 0).mean()), 4
                ),
                "import_leg_zero_share_SPP": round(
                    float((R["SPP"]["n_i"][ok] == 0).mean()), 4
                ),
            },
        }

        # ================= Q-E (PREREG §4b) — the sign / basis leg ====================
        model_net_spp = R["SPP"]["net_repaired"][ok]
        e1 = corr(model_net_spp, s_model["SPP"])
        qe = {
            "E1_corr_model_net_vs_s_model": round(e1, 4),
            "E1_PASS": bool(e1 > 0),
            "reported_not_gated": {
                "corr_measured_net_vs_s_derive": round(
                    corr(meas_net["SPP"][ok], s_derive_K["SPP"]), 4
                ),
                "corr_p_bus_vs_miso_da": round(
                    corr(bus_price[BUS_OF_SEAM["SPP"]][ok], da[ok]), 4
                ),
                "mean_p_bus": round(float(bus_price[BUS_OF_SEAM["SPP"]][ok].mean()), 2),
                "mean_miso_da": round(float(da[ok].mean()), 2),
                "sigma_p_bus": round(float(bus_price[BUS_OF_SEAM["SPP"]][ok].std()), 2),
                "sigma_miso_da": round(float(da[ok].std()), 2),
                "mean_spp_hub": round(float(spp_hub[ok].mean()), 2),
            },
        }

        report["years"][str(year)] = {
            "provenance": pv,
            "QA": qa,
            "QB": qb,
            "QD": qd,
            "QE": qe,
        }

    # --- REPORTED, GATED NOWHERE (rule 23): a read-only re-run of the derive, whose
    # output is compared to the committed table. It changes nothing and selects nothing.
    rederive = {}
    for year in YEARS:
        try:
            lad, notes = dm.derive_spp_neighbour_hourly(g_all.loc[year])
            rederive[str(year)] = {
                "import": lad["import"],
                "export": lad["export"],
                "notes": notes,
                "band1_import_delta_vs_committed": round(
                    lad["import"][0] - REF_LADDER_SPP[year]["import"][0], 4
                ),
                "band1_export_delta_vs_committed": round(
                    lad["export"][0] - REF_LADDER_SPP[year]["export"][0], 4
                ),
            }
        except Exception as exc:  # noqa: BLE001 - reported, never gated
            rederive[str(year)] = {"status": f"NOT RUN: {type(exc).__name__}: {exc}"}
    report["read_only_derive_verification_reported_not_gated"] = rederive

    report["GATE"] = {
        "failed_legs": gate_fail,
        "PASS": not gate_fail,
    }
    if gate_fail:
        report["VERDICT"] = "INSTRUMENT BROKEN — no Q is read"
    else:
        qa_ok = all(
            report["years"][str(y)]["QA"]["VERDICT"] == "IDENTITY HOLDS" for y in YEARS
        )
        qb_ok = all(
            report["years"][str(y)]["QB"]["VERDICT"] == "TRANSMITTED" for y in YEARS
        )
        e1_ok = all(report["years"][str(y)]["QE"]["E1_PASS"] for y in YEARS)
        if not e1_ok:
            report["VERDICT"] = "SIGN DEFECT"
        elif not qa_ok:
            report["VERDICT"] = "TABLE-INTERNAL"
        elif qb_ok:
            report["VERDICT"] = "INHERITED"
        else:
            report["VERDICT"] = "DISPLACED"
        report["QD_gated"] = all(
            report["years"][str(y)]["QD"]["PJM_lt_SPP"] for y in YEARS
        )

    OUT.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(json.dumps(report, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
