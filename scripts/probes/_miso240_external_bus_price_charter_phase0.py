"""miso-240 phase 0 — CHARTER OR REFUSE queue item 1: the model's own external-bus price
``s = p(MISO_external) - p(PJM_border)``. Zero LP.

Pre-registration:
``results/calibration/PREREG-miso240-charter-or-refuse-the-external-bus-price-2026-09-07.md``
(pushed at ``5c503155``, before any adjudicating quantity), plus
``ADDENDUM-miso240-two-decision-rules-fixed-before-the-numbers-2026-09-07.md`` (pushed before
the numbers it governs). Every decision rule applied here is fixed in one of those two
documents; nothing below selects anything.

miso-239 left queue item 1 OPEN, its pre-registered property ladder MIXED, and the object
NAMED but explicitly NOT CHARTERED: the model's own merit spread ``s``. A charter owes, at
zero LP and before any field is named:

  (a) how ``MISO_external``'s price is FORMED in the LP, and whether its own-net-load
      response is a modelling artefact or a real seam property   -> Q-A (§3a)
  (b) what the MEASURED analogue of ``s`` is, NAMED, on a stated basis                 -> Q-C / Q-C2
  (c) rule 17 [R-FLOOR-WINDOW] in full                                                 -> the FINDING
  (d) rule 19 [R-ONE-MECH]: what already sets the PJM seam, REPLACE or RECONCILE       -> Q-D + the FINDING

and one extra leg this session adds because the handoff carries a reported-not-gated column
forward as evidence:

  Q-B (§3b) a declared PLACEBO testing whether miso-239's ``gamma_np(s)`` column is EVIDENCE
      at all, or an arithmetic consequence of ``MERIT = g(s)`` -- a code fact miso-239
      PREREG §0d(2) established BEFORE any data.

Q-A and Q-D read the keeper's OWN committed P1 zonal duals from
``hourly/system_<year>.parquet`` directly -- they are NOT reconstructions. Q-B rides
miso-239's committed reconstruction and is labelled as one.

NOTHING HERE LICENSES TOUCHING THE FROZEN delta_k LADDERS OR THE MEASURED (month x hod)
ENVELOPE, WHATEVER THE ANSWER (PREREG §5.2, rules 23 / 14 / 1).

Usage: python3 scripts/probes/_miso240_external_bus_price_charter_phase0.py
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
MISO238 = REPO / "results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json"
MISO239 = (
    REPO / "results/calibration/_miso239_merit_ladder_property_attribution_phase0.json"
)
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
OUT = REPO / "results/calibration/_miso240_external_bus_price_charter_phase0.json"
PREREPAIR = (
    REPO
    / "results/calibration/_miso240_external_bus_price_charter_phase0_PREREPAIR.json"
)

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
BUS = "MISO_external"
BUS_SOUTH = "MISO_external_South"
# PREREG §0c(1): the shared node's border links on the KEEPER's topology
# (miso_south_seam_split: true re-homes MISO-South onto MISO_external_South).
BORDER_ZONES = ("MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-West")
EAST_FACING = ("MISO-Illinois", "MISO-Indiana", "MISO-East")
WEST_FACING = "MISO-West"
# Seams hosted in the shared node (PREREG §0c(2)).
SHARED_SEAMS = ("PJM", "SPP", "Manitoba")

# ---- bars, every one fixed ex ante ----
# PREREG §1 provenance bars.
TOL_GAMMA = 0.5          # MW/z
TOL_SHARE = 0.005
TOL_ID1 = 1e-6           # MW
TOL_ID2 = 1e-9           # MW
# PREREG §2 tie tolerance + its declared sensitivity.
TAU = 0.01               # $/MWh
TAU_SENSITIVITY = (0.001, 0.01, 0.10)
# PREREG §3a bars.
QA_BAR = 0.50
# PREREG §3b bars + floor; ADDENDUM §A fixes BOTH denominators.
QB_ARTEFACT_BAR = 0.25
QB_NOT_ARTEFACT_BAR = 0.50
QB_FLOOR_MW = 100.0
# PREREG §3c bars (ADDENDUM §B: legs i+ii only).
QC_COVERAGE_BAR = 0.95
# ADDENDUM §B bars for Q-C2.
QC2_CONFIRM_BAR = 0.99
QC2_MISLABEL_BAR = 0.50
QC2_PRICE_TOL = 0.01     # $/MWh
QC2_CANDIDATE_HUBS = (
    "ARKANSAS.HUB",
    "ILLINOIS.HUB",
    "INDIANA.HUB",
    "LOUISIANA.HUB",
    "MICHIGAN.HUB",
    "MINN.HUB",
    "MS.HUB",
    "TEXAS.HUB",
)
# PREREG §3d bars.
QD_LIVE_BAR = 0.10
QD_INERT_BAR = 0.02

VENTILES = 20

# PREREG §1 reference values, restated HERE before they are recomputed. They are also read
# from the committed predecessor JSONs; both are checked (belt and braces).
REF_G_P1_GAMMA_MERIT = (-870.18, -930.93, -791.43)
REF_G_P2_SHARES = {
    "LINEAR": (0.6679, 0.2839, 0.7312),
    "CURVE": (0.3063, 0.6816, 0.2210),
    "STEP": (0.0259, 0.0345, 0.0479),
}
REF_G_P3_NP_P1 = (-677.62, -662.69, -590.15)
REF_G_P3_NP_S = (-15.70, 2.00, -4.41)
REF_G_P4_GAMMA_MODEL = (-866.18, -1043.37, -843.45)


def _load(mod: str):
    return importlib.import_module(mod)


M8 = _load("_miso238_pjm_seam_channel_attribution_phase0")
M9 = _load("_miso239_merit_ladder_property_attribution_phase0")

ols_resid = M8.ols_resid
gamma = M8.gamma
_z = M8._z
hour_index = M8.hour_index
load_balance_miso = M8.load_balance_miso
ventile_dummies = M9.ventile_dummies
resid_on = M9.resid_on
gamma_weights = M9.gamma_weights


def near(a: np.ndarray, b: np.ndarray, tol: float) -> np.ndarray:
    """Elementwise |a - b| <= tol, NaN-safe (NaN never ties)."""
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    return np.where(np.isfinite(d), d <= tol, False)


def main() -> int:  # noqa: PLR0912, PLR0915 - one linear probe, PREREG section order
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
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    prior238 = json.loads(MISO238.read_text())["years"]
    prior239 = json.loads(MISO239.read_text())["years"]

    zonal = pd.read_parquet(ZONAL_ACTUAL)

    bal = load_balance_miso()
    bal["hour"] = hour_index(bal["local"])
    bal["year"] = (pd.to_datetime(bal["local"]) - pd.Timedelta(hours=1)).dt.year
    bal = bal[(bal["hour"] >= 0) & (bal["hour"] < HOURS)]

    report: dict = {
        "probe": (
            "miso-240 phase 0 — charter or refuse queue item 1: the model's own external-bus "
            "price s = p(MISO_external) - p(PJM_border)"
        ),
        "prereg": (
            "results/calibration/PREREG-miso240-charter-or-refuse-the-external-bus-price-"
            "2026-09-07.md (pushed 5c503155)"
        ),
        "addendum": (
            "results/calibration/ADDENDUM-miso240-two-decision-rules-fixed-before-the-"
            "numbers-2026-09-07.md (pushed before the numbers it governs)"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "evidence_class": (
            "Q-A and Q-D read the keeper's OWN committed P1 zonal duals from "
            "hourly/system_<year>.parquet — NOT a reconstruction. Q-B rides miso-239's "
            "committed four-seam RECONSTRUCTION (harness corr +0.9845/+0.9745/+0.9839) and "
            "is labelled as one. Q-C/Q-C2 read committed measured parquets only."
        ),
        "price_basis": (
            "Indiana-hub RT builds the ok mask (byte-identically to miso-236/237/238/239). "
            "The lane's `da` (derive_miso_seam_ladders.load_joined, from "
            "actual_lmp_hourly_MISO.parquet) is the basis of p1 = da - p_border and of every "
            "merit signal; WHETHER that series is in fact the Indiana hub is Q-C2's own "
            "gated question (ADDENDUM §B) and is not assumed either way here."
        ),
        "bars": {
            "tol_gamma_mw_per_z": TOL_GAMMA,
            "tol_share": TOL_SHARE,
            "tol_identity_1_mw": TOL_ID1,
            "tol_identity_2_mw": TOL_ID2,
            "tau_usd_per_mwh": TAU,
            "tau_sensitivity": list(TAU_SENSITIVITY),
            "qa_bar": QA_BAR,
            "qb_artefact_bar": QB_ARTEFACT_BAR,
            "qb_not_artefact_bar": QB_NOT_ARTEFACT_BAR,
            "qb_floor_mw_per_z": QB_FLOOR_MW,
            "qc_coverage_bar": QC_COVERAGE_BAR,
            "qc2_confirm_bar": QC2_CONFIRM_BAR,
            "qc2_mislabel_bar": QC2_MISLABEL_BAR,
            "qc2_price_tol_usd": QC2_PRICE_TOL,
            "qd_live_bar": QD_LIVE_BAR,
            "qd_inert_bar": QD_INERT_BAR,
        },
        "gated_seam": "PJM",
        "tranches": SEAM_FLOW_TRANCHES,
    }

    prov: dict[str, dict] = {}
    years_out: dict[str, dict] = {}

    for yi, year in enumerate(YEARS):
        gy = g_all.loc[year]
        act_all = actual_zone_price(year)
        act = act_all[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        nT = int(ok.sum())

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

        my = bal[bal["year"] == year].drop_duplicates("hour")

        def miso_series(col: str) -> np.ndarray:
            s = pd.Series(my[col].to_numpy(), index=my["hour"].to_numpy())
            return s.reindex(range(HOURS)).to_numpy(float)

        miso_nl = (miso_series("demand") - miso_series("wind") - miso_series("solar"))[ok]
        miso_vre = (miso_series("wind") + miso_series("solar"))[ok]
        z_nl = _z(miso_nl)
        s_own = np.column_stack([z_nl, _z(miso_vre)])

        # ---- the keeper's OWN committed P1 zonal duals ----
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        zp = {
            z: sysf[sysf["zone"] == z].sort_values("hour")["price"].to_numpy(float)
            for z in sorted(sysf["zone"].unique())
        }
        p_ext = zp[BUS]
        s_spread = (p_ext - border)[ok]
        p1s = (da - border)[ok]

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]

        # ================= §1 PROVENANCE GATE =================
        width_pjm = float(specs["PJM"].interface_limit_mw) / SEAM_FLOW_TRANCHES
        dk_pjm = np.asarray(
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"], float
        )
        mi = (s_spread[None, :] > dk_pjm[:, None]).astype(float)
        bi = np.clip(
            np.asarray(env_i["PJM"], float)[None, :] - ks * width_pjm, 0.0, width_pjm
        )[:, ok]
        b_bar = bi.mean(axis=1)
        m_bar = mi.mean(axis=1)
        g_step = (mi * b_bar[:, None]).sum(0)
        merit = ((mi - m_bar[:, None]) * b_bar[:, None]).sum(0)
        n_bands = mi.sum(0).round().astype(int)
        cum_g = np.cumsum(b_bar)

        # G-X0: the PJM export leg identically zero (MERIT = g(s) - mean g needs it)
        lad_e = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["PJM"]["export"], float)
        me = (p_ext[None, :] < lad_e[:, None])[:, ok].astype(float)
        be = np.clip(
            np.asarray(env_e["PJM"], float)[None, :] - ks * width_pjm, 0.0, width_pjm
        )[:, ok]
        gx0 = float(np.abs((me * be).sum(0)).max())

        # G-ID1: the band-count identity
        g_from_count = np.where(n_bands > 0, cum_g[np.maximum(n_bands - 1, 0)], 0.0)
        id1 = float(np.abs(g_step - g_from_count).max())

        r_merit = ols_resid(merit, p1s)
        g_merit = gamma(r_merit, s_own)

        # miso-239's channel split, reproduced from scratch (G-P2)
        sc = s_spread - s_spread.mean()
        beta = float((sc * (g_step - g_step.mean())).mean() / (sc * sc).mean())
        linear = beta * sc
        present = sorted({int(v) for v in n_bands})
        xk = np.array([s_spread[n_bands == n].mean() for n in present])
        yk = np.array([0.0 if n == 0 else float(cum_g[n - 1]) for n in present])
        g_cont = np.interp(s_spread, xk, yk)
        curve = (g_cont - g_cont.mean()) - linear
        step = (g_step - g_step.mean()) - (g_cont - g_cont.mean())
        chan = {"LINEAR": linear, "CURVE": curve, "STEP": step}
        g_chan = {c: gamma(ols_resid(v, p1s), s_own) for c, v in chan.items()}
        share = {c: g_chan[c] / g_merit for c in chan}

        one = np.ones((nT, 1))
        d_np_p1 = np.column_stack([one, ventile_dummies(p1s, VENTILES)])
        d_np_s = np.column_stack([one, ventile_dummies(s_spread, VENTILES)])
        g_np_p1 = gamma(resid_on(merit, d_np_p1), s_own)
        g_np_s = gamma(resid_on(merit, d_np_s), s_own)

        # miso-238's gamma_model (G-P4), on the same reconstruction
        model_net = (mi * bi).sum(0) - (me * be).sum(0)
        g_model = gamma(ols_resid(model_net, p1s), s_own)

        ref239 = prior239[str(year)]
        ref238 = prior238[str(year)]["seams"]["PJM"]
        prov[str(year)] = {
            "G_P1_gamma_merit": {
                "recomputed": round(g_merit, 2),
                "handoff": REF_G_P1_GAMMA_MERIT[yi],
                "committed_json": ref239["gamma_merit_mw_per_z"],
                "max_abs_delta": round(
                    max(
                        abs(g_merit - REF_G_P1_GAMMA_MERIT[yi]),
                        abs(g_merit - float(ref239["gamma_merit_mw_per_z"])),
                    ),
                    3,
                ),
            },
            "G_P2_shares": {
                "recomputed": {c: round(share[c], 4) for c in chan},
                "max_abs_delta": round(
                    max(
                        max(
                            abs(share[c] - REF_G_P2_SHARES[c][yi]),
                            abs(share[c] - float(ref239["share_of_merit"][c])),
                        )
                        for c in chan
                    ),
                    5,
                ),
            },
            "G_P3_ventile_columns": {
                "gamma_np_p1_recomputed": round(g_np_p1, 2),
                "gamma_np_s_recomputed": round(g_np_s, 2),
                "max_abs_delta": round(
                    max(
                        abs(g_np_p1 - REF_G_P3_NP_P1[yi]),
                        abs(g_np_s - REF_G_P3_NP_S[yi]),
                        abs(
                            g_np_p1
                            - float(
                                ref239["non_parametric_limb"][
                                    "gamma_np_ventiles_p1_mw_per_z"
                                ]
                            )
                        ),
                        abs(
                            g_np_s
                            - float(
                                ref239["non_parametric_limb"][
                                    "gamma_np_ventiles_model_spread_mw_per_z"
                                ]
                            )
                        ),
                    ),
                    3,
                ),
            },
            "G_P4_gamma_model": {
                "recomputed": round(g_model, 2),
                "handoff": REF_G_P4_GAMMA_MODEL[yi],
                "committed_json": ref238["gamma_mw_per_z"]
                if "gamma_mw_per_z" in ref238
                else ref238.get("gamma_model_mw_per_z"),
                "max_abs_delta": round(abs(g_model - REF_G_P4_GAMMA_MODEL[yi]), 3),
            },
            "G_X0_pjm_export_max_abs_mw": round(gx0, 6),
            "G_ID1_band_count_identity_mw": float(f"{id1:.3e}"),
        }

        # ================= §3a Q-A — how is p_ext FORMED? =================
        def classify(tau: float) -> dict:
            zone_tie = np.zeros(nT, dtype=bool)
            which: dict[str, np.ndarray] = {}
            for z in BORDER_ZONES:
                t = near(p_ext[ok], zp[z][ok], tau)
                which[z] = t
                zone_tie |= t
            # BAND: any offer level injected into MISO_external by a hosted seam
            band_tie = np.zeros(nT, dtype=bool)
            for seam in SHARED_SEAMS:
                if seam == "PJM":
                    lvl_i = border[ok][None, :] + dk_pjm[:, None]
                elif seam == "SPP":
                    dks = np.asarray(
                        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                            "import"
                        ],
                        float,
                    )
                    lvl_i = spp_hub[ok][None, :] + dks[:, None]
                else:
                    dks = np.asarray(
                        MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float
                    )
                    lvl_i = np.repeat(dks[:, None], nT, axis=1)
                lvl_e = np.repeat(
                    np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)[
                        :, None
                    ],
                    nT,
                    axis=1,
                )
                for lvl in (lvl_i, lvl_e):
                    band_tie |= (np.abs(p_ext[ok][None, :] - lvl) <= tau).any(axis=0)
            band_only = band_tie & ~zone_tie
            neither = ~zone_tie & ~band_tie
            n_tied = np.zeros(nT, dtype=int)
            for z in BORDER_ZONES:
                n_tied += which[z].astype(int)
            zmat = np.column_stack([zp[z][ok] for z in BORDER_ZONES])
            return {
                "share_ZONE": round(float(zone_tie.mean()), 4),
                "share_BAND": round(float(band_only.mean()), 4),
                "share_NEITHER": round(float(neither.mean()), 4),
                "share_by_zone": {
                    z: round(float(which[z].mean()), 4) for z in BORDER_ZONES
                },
                "share_all_four_tied": round(float((n_tied == 4).mean()), 4),
                "mean_zones_tied": round(float(n_tied.mean()), 3),
                "share_pext_eq_min_of_border": round(
                    float(near(p_ext[ok], zmat.min(axis=1), tau).mean()), 4
                ),
                "share_pext_eq_max_of_border": round(
                    float(near(p_ext[ok], zmat.max(axis=1), tau).mean()), 4
                ),
                "share_pext_below_all_border": round(
                    float((p_ext[ok] < zmat.min(axis=1) - tau).mean()), 4
                ),
                "share_pext_above_all_border": round(
                    float((p_ext[ok] > zmat.max(axis=1) + tau).mean()), 4
                ),
            }

        qa = {f"tau_{t}": classify(t) for t in TAU_SENSITIVITY}
        qa_main = qa[f"tau_{TAU}"]

        # reported-only mirror on the South external node
        south_zone_tie = near(zp[BUS_SOUTH][ok], zp["MISO-South"][ok], TAU)
        qa_south = {
            "share_tie_MISO_South": round(float(south_zone_tie.mean()), 4),
            "note": "REPORTED, never gating — MISO_external_South has ONE border link.",
        }

        # ================= §3b Q-B — the declared PLACEBO =================
        # MERIT_p1: the SAME frozen ladder g (same b_bar, same delta_k) on the MEASURED spread.
        mi_p1 = (p1s[None, :] > dk_pjm[:, None]).astype(float)
        m_bar_p1 = mi_p1.mean(axis=1)
        merit_p1 = ((mi_p1 - m_bar_p1[:, None]) * b_bar[:, None]).sum(0)
        d_np_p1b = np.column_stack([one, ventile_dummies(p1s, VENTILES)])
        d_np_sb = np.column_stack([one, ventile_dummies(s_spread, VENTILES)])
        g_mirror = gamma(ols_resid(merit_p1, s_spread), s_own)
        g_raw = gamma(merit_p1, s_own)
        g_np_own_p1 = gamma(resid_on(merit_p1, d_np_p1b), s_own)
        g_np_cross_s = gamma(resid_on(merit_p1, d_np_sb), s_own)

        # G-ID2: the support identity — the residual is EXACTLY zero on ventile bins
        # containing no threshold. Computed for both the s-ladder and the p1-mirror.
        def support(x: np.ndarray, m: np.ndarray, dks: np.ndarray, design) -> dict:
            """Bin-impurity support census (SECOND ADDENDUM §2's declared repair).

            Impurity is EMPIRICAL and convention-free: a ventile bin is impure iff ``m`` is
            not constant on it to ``TOL_ID2``. The first version assigned bins to thresholds
            by interval arithmetic (``lo < d <= hi``) against ``searchsorted(side="right")``
            bins that are ``[lo, hi)``, which displaced by one position any threshold landing
            exactly on a ventile edge and failed G-ID2 at 869.6 MW in 2024. The falsifiable
            content is carried by the new gating leg ``G-ID2b``: a monotone K-step function of
            ``x`` can make at most ONE bin of ``x`` impure per crossed threshold, so
            ``n_impure <= n_crossed``. Zero free parameters.
            """
            edges = np.quantile(x, np.linspace(0.0, 1.0, VENTILES + 1)[1:-1])
            b_idx = np.searchsorted(edges, x, side="right")
            crossed = [d for d in dks if (x > d).any() and (~(x > d)).any()]
            impure = np.zeros(VENTILES, dtype=bool)
            for b in range(VENTILES):
                sel = b_idx == b
                if sel.any():
                    impure[b] = bool(m[sel].max() - m[sel].min() > TOL_ID2)
            r = resid_on(m, design)
            pure_hours = ~impure[b_idx]
            return {
                "n_impure_bins": int(impure.sum()),
                "n_crossed_thresholds": int(len(crossed)),
                "g_id2b_n_impure_le_n_crossed": bool(impure.sum() <= len(crossed)),
                "share_hours_impure": round(float((~pure_hours).mean()), 4),
                "max_abs_resid_on_pure_bins_mw": float(
                    f"{float(np.abs(r[pure_hours]).max() if pure_hours.any() else 0.0):.3e}"
                ),
            }

        sup_s = support(s_spread, merit, dk_pjm, d_np_s)
        sup_p1 = support(p1s, merit_p1, dk_pjm, d_np_p1b)
        id2 = max(
            sup_s["max_abs_resid_on_pure_bins_mw"],
            sup_p1["max_abs_resid_on_pure_bins_mw"],
        )

        # ================= §3c/§3c2 Q-C and Q-C2 =================
        zy = zonal[zonal["year"] == year]
        cov = {}
        for z in BORDER_ZONES:
            sub = zy[zy["zone"] == z]
            piv = sub.pivot_table(
                index="hour", columns="hub", values="da", aggfunc="first"
            ).reindex(range(HOURS))
            cov[z] = round(float(np.isfinite(piv.mean(axis=1).to_numpy()).mean()), 4)
        zones_present = sorted(set(zy["zone"].unique()))

        hub_da = zy.pivot_table(
            index="hour", columns="hub", values="da", aggfunc="first"
        ).reindex(range(HOURS))
        qc2_match = {}
        for h in QC2_CANDIDATE_HUBS:
            if h in hub_da.columns:
                qc2_match[h] = round(
                    float(near(hub_da[h].to_numpy(float)[ok], da[ok], QC2_PRICE_TOL).mean()),
                    4,
                )
        qc2_match["HUB8_MEAN"] = round(
            float(near(hub_da.mean(axis=1).to_numpy(float)[ok], da[ok], QC2_PRICE_TOL).mean()),
            4,
        )
        zone_da = {}
        for z in BORDER_ZONES:
            hubs = sorted(set(zy[zy["zone"] == z]["hub"].unique()))
            zone_da[z] = hub_da[[h for h in hubs if h in hub_da.columns]].mean(axis=1).to_numpy(float)

        # REPORTED-only correlations (never gating, never a target)
        def corr(a: np.ndarray, b: np.ndarray) -> float:
            m = np.isfinite(a) & np.isfinite(b)
            if m.sum() < 10:
                return float("nan")
            return round(float(np.corrcoef(a[m], b[m])[0, 1]), 4)

        s_meas_by_zone = {
            z: (zone_da[z] - border)[ok] for z in BORDER_ZONES
        }
        qc_reported = {
            z: {
                "corr_with_model_s": corr(s_meas_by_zone[z], s_spread),
                "corr_with_p1": corr(s_meas_by_zone[z], p1s),
            }
            for z in BORDER_ZONES
        }
        # zone-matched analogue: the zone p_ext ties this hour (first tie wins, stable order)
        zhat = np.full(nT, -1, dtype=int)
        for i, z in enumerate(BORDER_ZONES):
            t = near(p_ext[ok], zp[z][ok], TAU) & (zhat < 0)
            zhat[t] = i
        s_meas_matched = np.full(nT, np.nan)
        for i, z in enumerate(BORDER_ZONES):
            m = zhat == i
            s_meas_matched[m] = s_meas_by_zone[z][m]
        qc_reported["ZONE_MATCHED"] = {
            "share_hours_matched": round(float((zhat >= 0).mean()), 4),
            "corr_with_model_s": corr(s_meas_matched, s_spread),
            "corr_with_p1": corr(s_meas_matched, p1s),
        }

        # ================= §3d Q-D — the shared star node =================
        def star(tau: float) -> dict:
            east = np.column_stack([zp[z][ok] for z in EAST_FACING])
            west = zp[WEST_FACING][ok]
            pe = p_ext[ok]
            west_sets = near(pe, west, tau) & (pe < east.min(axis=1) - tau)
            east_tie = np.zeros(nT, dtype=bool)
            for z in EAST_FACING:
                east_tie |= near(pe, zp[z][ok], tau)
            east_sets = east_tie & (pe < west - tau)
            gap_w = float(np.abs(east.min(axis=1) - pe)[west_sets].mean()) if west_sets.any() else 0.0
            gap_e = float(np.abs(west - pe)[east_sets].mean()) if east_sets.any() else 0.0
            return {
                "share_west_sets": round(float(west_sets.mean()), 4),
                "share_east_sets": round(float(east_sets.mean()), 4),
                "share_total": round(float((west_sets | east_sets).mean()), 4),
                "mean_gap_usd_west_sets": round(gap_w, 3),
                "mean_gap_usd_east_sets": round(gap_e, 3),
                "n_hours_west_sets": int(west_sets.sum()),
                "n_hours_east_sets": int(east_sets.sum()),
            }

        qd = {f"tau_{t}": star(t) for t in TAU_SENSITIVITY}

        # ---- POST-HOC, LABELLED, AND IT MOVES NOTHING ----
        # Not named in the PREREG or either addendum. It reads no gated quantity: every
        # verdict is computed from share_ZONE / share_BAND, the Q-B ratios and floor, the
        # Q-C coverage, the Q-C2 match shares and the Q-D shares, none of which touches any
        # value below. Reported because a reader should be able to see WHERE the model's
        # price does and does not separate, which is the context Q-A's answer sits in.
        six = [z for z in ("MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-West",
                           "MISO-Plains", "MISO-South") if z in zp]
        mm6 = np.column_stack([zp[z][ok] for z in six])
        spread6 = mm6.max(axis=1) - mm6.min(axis=1)
        mm4 = np.column_stack([zp[z][ok] for z in BORDER_ZONES])
        spread4 = mm4.max(axis=1) - mm4.min(axis=1)
        meas4 = np.column_stack([zone_da[z][ok] for z in BORDER_ZONES])
        mfin = np.isfinite(meas4).all(axis=1)
        mspread4 = (meas4.max(axis=1) - meas4.min(axis=1))[mfin]
        post_hoc = {
            "label": "POST-HOC, NOT PRE-REGISTERED, reads no gated quantity, moves nothing",
            "zones_in_sidecar": six,
            "model_border4_max_minus_min": {
                "share_hours_gt_1c": round(float((spread4 > 0.01).mean()), 4),
                "mean_usd": round(float(spread4.mean()), 4),
                "p99_usd": round(float(np.percentile(spread4, 99)), 4),
                "max_usd": round(float(spread4.max()), 3),
            },
            "model_six_zone_max_minus_min": {
                "share_hours_gt_1c": round(float((spread6 > 0.01).mean()), 4),
                "mean_usd": round(float(spread6.mean()), 4),
                "p99_usd": round(float(np.percentile(spread6, 99)), 4),
                "max_usd": round(float(spread6.max()), 3),
            },
            "measured_border4_max_minus_min_da": {
                "share_hours_gt_1c": round(float((mspread4 > 0.01).mean()), 4),
                "mean_usd": round(float(mspread4.mean()), 4),
                "p99_usd": round(float(np.percentile(mspread4, 99)), 4),
                "max_usd": round(float(mspread4.max()), 3),
            },
            "note": (
                "CORROBORATES internal_congestion_split G (miso-79 NO-BUILD, miso-204) on a "
                "new instrument; rule 28(a) — NOT re-tested and NOT re-opened."
            ),
        }

        years_out[str(year)] = {
            "n_ok_hours": nT,
            "post_hoc_not_preregistered": post_hoc,
            "Q_A_formation": qa,
            "Q_A_south_node_reported": qa_south,
            "Q_B_placebo": {
                "gamma_merit_s_ladder_mw_per_z": round(g_merit, 2),
                "gamma_np_s_on_merit_s": round(g_np_s, 2),
                "ratio_np_s_over_merit": round(abs(g_np_s) / abs(g_merit), 4),
                "gamma_np_p1_on_merit_s": round(g_np_p1, 2),
                "ratio_np_p1_over_merit": round(abs(g_np_p1) / abs(g_merit), 4),
                "gamma_mirror_denominator_mw_per_z": round(g_mirror, 2),
                "gamma_raw_denominator_mw_per_z": round(g_raw, 2),
                "gamma_np_p1_on_merit_p1": round(g_np_own_p1, 2),
                "gamma_np_s_on_merit_p1": round(g_np_cross_s, 2),
                "ratio_vs_mirror": round(abs(g_np_own_p1) / abs(g_mirror), 4),
                "ratio_vs_raw": round(abs(g_np_own_p1) / abs(g_raw), 4),
                "ratio_cross_s_vs_mirror": round(abs(g_np_cross_s) / abs(g_mirror), 4),
                "support_s_ladder": sup_s,
                "support_p1_mirror": sup_p1,
                "reconstruction_note": (
                    "MERIT and MERIT_p1 ride miso-235's four-seam RECONSTRUCTION; labelled."
                ),
            },
            "Q_C_measured_analogue": {
                "zones_present": zones_present,
                "da_coverage_by_border_zone": cov,
                "reported_never_gating": qc_reported,
            },
            "Q_C2_basis_identity": {
                "match_share_by_candidate": qc2_match,
                "lane_da_source": "actual_lmp_hourly_MISO.parquet (via load_joined)",
            },
            "Q_D_star_node": qd,
            "identity_checks": {
                "G_ID1_band_count_mw": float(f"{id1:.3e}"),
                "G_ID2_pure_bin_support_mw": float(f"{id2:.3e}"),
            },
        }

    # ================= verdicts, on the pre-registered rules only =================
    ys = [years_out[str(y)] for y in YEARS]

    gate_legs = {
        "G_P1_gamma_merit_miso239": max(
            prov[str(y)]["G_P1_gamma_merit"]["max_abs_delta"] for y in YEARS
        )
        <= TOL_GAMMA,
        "G_P2_channel_shares_miso239": max(
            prov[str(y)]["G_P2_shares"]["max_abs_delta"] for y in YEARS
        )
        <= TOL_SHARE,
        "G_P3_ventile_columns_miso239": max(
            prov[str(y)]["G_P3_ventile_columns"]["max_abs_delta"] for y in YEARS
        )
        <= TOL_GAMMA,
        "G_P4_gamma_model_miso238": max(
            prov[str(y)]["G_P4_gamma_model"]["max_abs_delta"] for y in YEARS
        )
        <= TOL_GAMMA,
        "G_X0_pjm_export_identically_zero": all(
            prov[str(y)]["G_X0_pjm_export_max_abs_mw"] == 0.0 for y in YEARS
        ),
        "G_ID1_band_count_identity": max(
            y["identity_checks"]["G_ID1_band_count_mw"] for y in ys
        )
        <= TOL_ID1,
        "G_ID2_pure_bin_support": max(
            y["identity_checks"]["G_ID2_pure_bin_support_mw"] for y in ys
        )
        <= TOL_ID2,
        # SECOND ADDENDUM §2: n_impure <= n_crossed on BOTH ladders, all three years.
        "G_ID2b_n_impure_le_n_crossed": all(
            y["Q_B_placebo"][k]["g_id2b_n_impure_le_n_crossed"]
            for y in ys
            for k in ("support_s_ladder", "support_p1_mirror")
        ),
    }
    gate_legs["ALL_PASS"] = all(gate_legs.values())

    def qa_verdict(tag: str) -> str:
        zs = [y["Q_A_formation"][tag]["share_ZONE"] for y in ys]
        bs = [y["Q_A_formation"][tag]["share_BAND"] for y in ys]
        if all(v >= QA_BAR for v in zs):
            return "INTERNAL-PRICE FORMATION"
        if all(v >= QA_BAR for v in bs):
            return "SEAM-SELF-REFERENTIAL"
        return "MIXED"

    qa_by_tau = {t: qa_verdict(f"tau_{t}") for t in TAU_SENSITIVITY}
    qa_final = qa_by_tau[TAU]
    qa_fragile = len(set(qa_by_tau.values())) > 1

    mir = [abs(y["Q_B_placebo"]["gamma_mirror_denominator_mw_per_z"]) for y in ys]
    raw = [abs(y["Q_B_placebo"]["gamma_raw_denominator_mw_per_z"]) for y in ys]
    rv_m = [y["Q_B_placebo"]["ratio_vs_mirror"] for y in ys]
    rv_r = [y["Q_B_placebo"]["ratio_vs_raw"] for y in ys]
    rv_s = [y["Q_B_placebo"]["ratio_np_s_over_merit"] for y in ys]
    if not (all(v >= QB_FLOOR_MW for v in mir) and all(v >= QB_FLOOR_MW for v in raw)):
        qb = "NOT MEANINGFUL (below the pre-registered 100 MW/z floor on a denominator)"
    else:
        vm = (
            "SELF-CONDITIONING ARTEFACT"
            if all(v <= QB_ARTEFACT_BAR for v in rv_m)
            and all(v <= QB_ARTEFACT_BAR for v in rv_s)
            else "NOT AN ARTEFACT"
            if all(v >= QB_NOT_ARTEFACT_BAR for v in rv_m)
            else "MIXED"
        )
        vr = (
            "SELF-CONDITIONING ARTEFACT"
            if all(v <= QB_ARTEFACT_BAR for v in rv_r)
            and all(v <= QB_ARTEFACT_BAR for v in rv_s)
            else "NOT AN ARTEFACT"
            if all(v >= QB_NOT_ARTEFACT_BAR for v in rv_r)
            else "MIXED"
        )
        qb = vm if vm == vr else f"FRAGILE (mirror={vm}, raw={vr})"

    qc_ok = all(
        set(BORDER_ZONES).issubset(set(y["Q_C_measured_analogue"]["zones_present"]))
        and all(
            v >= QC_COVERAGE_BAR
            for v in y["Q_C_measured_analogue"]["da_coverage_by_border_zone"].values()
        )
        for y in ys
    )
    qc = "EXISTS" if qc_ok else "DOES NOT EXIST"

    ind = [y["Q_C2_basis_identity"]["match_share_by_candidate"].get("INDIANA.HUB", 0.0) for y in ys]
    if all(v >= QC2_CONFIRM_BAR for v in ind):
        qc2, qc2_named = "BASIS CONFIRMED", "INDIANA.HUB"
    elif any(v < QC2_MISLABEL_BAR for v in ind):
        cands = {}
        for c in (*QC2_CANDIDATE_HUBS, "HUB8_MEAN"):
            vals = [
                y["Q_C2_basis_identity"]["match_share_by_candidate"].get(c, 0.0)
                for y in ys
            ]
            if all(v >= QC2_CONFIRM_BAR for v in vals):
                cands[c] = min(vals)
        if cands:
            qc2_named = max(cands, key=lambda k: cands[k])
            qc2 = "BASIS MISLABELLED"
        else:
            qc2, qc2_named = "BASIS INDETERMINATE", None
    else:
        qc2, qc2_named = "BASIS INDETERMINATE", None

    def qd_verdict(tag: str) -> str:
        tot = [y["Q_D_star_node"][tag]["share_total"] for y in ys]
        if all(v >= QD_LIVE_BAR for v in tot):
            return "STAR-COUPLING LIVE"
        if all(v < QD_INERT_BAR for v in tot):
            return "STAR-COUPLING INERT"
        return "MIXED"

    qd_by_tau = {t: qd_verdict(f"tau_{t}") for t in TAU_SENSITIVITY}
    qd_final = qd_by_tau[TAU]
    qd_fragile = len(set(qd_by_tau.values())) > 1

    report["provenance_gate"] = {"legs": gate_legs, "per_year": prov}
    report["verdicts"] = {
        "Q_A_formation": qa_final,
        "Q_A_by_tau": qa_by_tau,
        "Q_A_fragile": qa_fragile,
        "Q_A_share_ZONE": [y["Q_A_formation"][f"tau_{TAU}"]["share_ZONE"] for y in ys],
        "Q_A_share_BAND": [y["Q_A_formation"][f"tau_{TAU}"]["share_BAND"] for y in ys],
        "Q_A_share_NEITHER": [
            y["Q_A_formation"][f"tau_{TAU}"]["share_NEITHER"] for y in ys
        ],
        "Q_B_placebo": qb,
        "Q_B_ratio_np_s_over_merit": rv_s,
        "Q_B_ratio_vs_mirror": rv_m,
        "Q_B_ratio_vs_raw": rv_r,
        "Q_C_measured_analogue": qc,
        "Q_C2_basis_identity": qc2,
        "Q_C2_named_series": qc2_named,
        "Q_C2_indiana_match_share": ind,
        "Q_D_star_node": qd_final,
        "Q_D_by_tau": qd_by_tau,
        "Q_D_fragile": qd_fragile,
        "Q_D_share_total": [y["Q_D_star_node"][f"tau_{TAU}"]["share_total"] for y in ys],
    }
    report["years"] = years_out
    report["non_claims"] = [
        "Zero LP. Nothing armed, screened, solved, registered or pruned.",
        "No cell verdict moves; rule 28(b) evidence-append form only, MISO's shard only.",
        "Every number here is declared UN-TARGETABLE by PREREG §5.3 before it was computed.",
        "The frozen delta_k ladders and the measured (month x hod) envelope are untouched and "
        "PREREG §5.2 forbids touching them whatever these verdicts read.",
        "Q-B changes no miso-239 number: that column was published REPORTED-NOT-GATED and "
        "chartered nothing.",
    ]

    # SECOND ADDENDUM §3: the declared no-move verification. The repair touched ONLY the
    # bin-impurity predicate, which feeds no verdict, so every other value in this report must
    # be identical to the pre-repair run's. The pre-repair artifact is committed beside this
    # one so the comparison is reproducible rather than asserted.
    if PREREPAIR.exists():
        def _strip(d: dict) -> dict:
            d = json.loads(json.dumps(d))
            for y in d["years"].values():
                for k in ("support_s_ladder", "support_p1_mirror"):
                    y["Q_B_placebo"].pop(k, None)
                y["identity_checks"].pop("G_ID2_pure_bin_support_mw", None)
                # the POST-HOC census was added after both runs and reads no gated
                # quantity; it exists in neither the pre-repair artifact nor any verdict.
                y.pop("post_hoc_not_preregistered", None)
            d["provenance_gate"]["legs"] = {
                k: v
                for k, v in d["provenance_gate"]["legs"].items()
                if "ID2" not in k and k != "ALL_PASS"
            }
            d.pop("s3_values_unchanged_after_repair", None)
            return d

        pre = json.loads(PREREPAIR.read_text())
        same = json.dumps(_strip(pre), sort_keys=True) == json.dumps(
            _strip(report), sort_keys=True
        )
        report["s3_values_unchanged_after_repair"] = {
            "verified": bool(same),
            "verdicts_identical": bool(
                json.dumps(pre["verdicts"], sort_keys=True)
                == json.dumps(report["verdicts"], sort_keys=True)
            ),
            "method": (
                "whole-report exact equality after removing ONLY the repaired predicate's own "
                "reported columns (support_s_ladder, support_p1_mirror, "
                "G_ID2_pure_bin_support_mw), the G-ID2 gate legs, and the POST-HOC census "
                "block, which was added after both runs and feeds no verdict"
            ),
            "prerepair_artifact": PREREPAIR.name,
        }

    OUT.write_text(json.dumps(report, indent=2) + "\n")

    print(f"provenance gate: {gate_legs}")
    print(f"Q-A formation      : {qa_final}  (by tau: {qa_by_tau})")
    print(f"   share ZONE/BAND/NEITHER: {report['verdicts']['Q_A_share_ZONE']} / "
          f"{report['verdicts']['Q_A_share_BAND']} / {report['verdicts']['Q_A_share_NEITHER']}")
    print(f"Q-B placebo        : {qb}")
    print(f"   ratio np(s)/MERIT     : {rv_s}")
    print(f"   ratio placebo/mirror  : {rv_m}   placebo/raw: {rv_r}")
    print(f"Q-C measured analog: {qc}")
    print(f"Q-C2 basis identity: {qc2}  named={qc2_named}  indiana match={ind}")
    print(f"Q-D star node      : {qd_final}  share_total={report['verdicts']['Q_D_share_total']}")
    print(f"wrote {OUT}")
    return 0 if gate_legs["ALL_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
