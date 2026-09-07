"""miso-239 phase 0 — WHICH PROPERTY of the merit ladder ``g`` carries the PJM seam's
spurious own-net-load response? Handoff queue item 1, on one exact zero-DOF decomposition.
Zero LP.

Pre-registration: ``results/calibration/PREREG-miso239-which-property-of-g-2026-09-07.md``
(pushed at ``c0e971ee``, before any adjudicating quantity). Every decision rule applied here
is fixed there; nothing below selects anything.

miso-238 attributed the model's spurious PJM own-net-load response to the reconstruction's
MERIT channel (1.005 / 0.892 / 0.938 of ``gamma_model``) and REFUTED the deliverability
envelope as its carrier. On PJM the export leg is identically zero, so exactly

    MERIT(t) = g(s(t)) - mean g,    g(x) = sum_k b_bar_k * 1[x > delta_k],   K = 8

a monotone, bounded, 8-step function of the model's own merit spread ``s = p_bus - p_border``.
miso-238 explicitly did NOT resolve WHICH PROPERTY of ``g`` does it. Four candidates were
named: (a) boundedness at the top, (b) K=8 step granularity, (c) delta_k placement, and
(d) the regressor is confounded — the response is right and ``ols_resid(., p1)`` removes the
WRONG spread (``p1 = da - p_border`` is the MEASURED Indiana-hub DA against the border, not
the model bus price the ladder actually clears on).

The split is exact and carries zero free parameters (PREREG §2). Three counterfactual
responses to the SAME realized spread series:

    g_step = g(s)                       the actual ladder
    g_lin  = alpha + beta*s             beta the OLS slope of g_step on s (a projection)
    g_cont = piecewise-linear interpolant through the ladder's own realized level-set knots
             (x_bar_n, g_n), n = 0..8, clamped at 0 and G_7 — continuous, monotone, and
             sharing g's EXACT bounds and thresholds, so it differs from g only in
             DISCRETENESS

    LINEAR = beta*(s - s_bar)                          -> candidate (d)
    CURVE  = (g_cont - mean) - LINEAR                   -> candidates (a) + (c)
    STEP   = (g_step - mean) - (g_cont - mean)          -> candidate (b)
    MERIT  = LINEAR + CURVE + STEP                      (exact; G-ID verifies it)

``gamma`` is the PARTIAL OLS slope on ``z_own_net_load`` in ``r ~ [1 | z_own_nl | z_own_VRE]``
(miso-237's estimator via miso-238 ADDENDUM §2), hence ``gamma(r) = sum_t w_t r_t`` for a
FIXED weight vector ``w``. That makes it linear in the series (so the channel split is exact)
AND exactly decomposable over any partition of the hours (so §3b's FLOOR / CAP / INTERIOR
band-count partition of ``gamma_CURVE`` separates (a) from (c)).

* **Provenance gate (PREREG §1), six legs.** G-P1 miso-235's sigma column to <= 0.5 MW;
  G-P2 miso-237's own-net-load coefficients to <= 0.5 MW/z; G-P3 miso-237 ADDENDUM §A's
  alignment column to <= 0.001; G-P4 miso-238's PUBLISHED column (its FINDING and JSON never
  reached main — PREREG §0a — so the references are the handoff's quoted values, restated in
  the PREREG before being recomputed); G-X0 the PJM export leg identically zero; G-ID this
  session's own decomposition identity to <= 1e-6 MW. Any leg failing declares the instrument
  BROKEN and nothing else is read.
* **Q-A (PREREG §3).** The verdict ladder on the shares, all three years, with absolute
  floors: REGRESSOR-CONFOUNDED (d) / LADDER-NONLINEARITY -> DISCRETENESS (b) or SHAPE ->
  BOUNDEDNESS (a) / PLACEMENT (c) / MIXED.
* **Q-C (PREREG §4).** The handoff's own second limb for (d): gamma re-run with the spread
  entered NON-PARAMETRICALLY (miso-237's P2 ventile block) instead of linearly.
* Robustness twin (PREREG §2c), REPORTED and never gating; census REPORTED and never gating.

NOTHING HERE LICENSES TOUCHING THE FROZEN delta_k LADDER OR THE MEASURED (month x hod)
ENVELOPE, WHATEVER THE ANSWER (PREREG §5.2, rules 23 / 14 / 1).

Usage: python3 scripts/probes/_miso239_merit_ladder_property_attribution_phase0.py
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
MISO235 = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
MISO237 = (
    REPO / "results/calibration/_miso237_price_representation_vs_state_phase0.json"
)
OUT = (
    REPO / "results/calibration/_miso239_merit_ladder_property_attribution_phase0.json"
)

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
GATED_SEAM = "PJM"

# PREREG §1 provenance bars, fixed ex ante.
TOL_SIGMA_MW = 0.5
TOL_COEF_MW = 0.5
TOL_ALIGN = 0.001
TOL_IDENTITY_MW = 1e-6
# PREREG §3 decision bars, fixed ex ante.
CHANNEL_BAR = 0.50
GAMMA_FLOOR_MW = 200.0
SUB_FLOOR_MW = 100.0
# PREREG §4 bars, fixed ex ante.
NP_SURVIVE_BAR = 0.50
NP_COLLAPSE_BAR = 0.25
VENTILES = 20

CHANNELS = ("LINEAR", "CURVE", "STEP")
REGIONS = ("FLOOR", "INTERIOR", "CAP")

# PREREG §1 G-P4 — miso-238's published PJM column, restated in the PREREG BEFORE being
# recomputed here, because its FINDING and phase-0 JSON never reached main (PREREG §0a).
MISO238_PUBLISHED = {
    "gamma_model_mw_per_z": (-866.18, -1043.37, -843.45),
    "share_merit": (1.005, 0.892, 0.938),
    "share_envelope_plus_interact": (-0.005, 0.108, 0.062),
    "a_merit_purged_mw": (-278.2, -226.7, -213.9),
    "a_model_purged_mw": (-327.0, -263.3, -242.0),
    "a_measured_purged_mw": (-256.0, -119.5, -205.4),
    "sat_share": (0.1740, 0.0068, 0.0000),
    "mean_bands_in_merit": (5.848, 4.585, 3.535),
    "corr_env_import_own_net_load": (0.3063, -0.0843, 0.3638),
}
MISO238_BARS = {
    "gamma_model_mw_per_z": 0.5,
    "share_merit": 0.005,
    "share_envelope_plus_interact": 0.005,
    "a_merit_purged_mw": 0.5,
    "a_model_purged_mw": 0.5,
    "a_measured_purged_mw": 0.5,
    "sat_share": 0.0005,
    "mean_bands_in_merit": 0.005,
    "corr_env_import_own_net_load": 0.0005,
}


def _load_miso238():
    """Import miso-238's probe module — its helpers ARE this session's code path.

    The handoff's binding instruction ("reuse
    ``scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py`` — it already carries
    the four-leg gate, the four-seam reconstruction, the exact MERIT/ENVELOPE/INTERACT split
    with its identity check, and the own-state block on one code path"). ``gamma`` there is
    the PARTIAL OLS estimator after that probe's own ADDENDUM §2 repair, applied this session
    (PREREG §0b) and verified by G-P2 rather than asserted.
    """
    return importlib.import_module("_miso238_pjm_seam_channel_attribution_phase0")


M8 = _load_miso238()
ols_resid = M8.ols_resid
_design = M8._design
gamma = M8.gamma
gamma_marginal = M8.gamma_marginal
_z = M8._z
hour_index = M8.hour_index
load_balance_miso = M8.load_balance_miso


def ventile_dummies(a: np.ndarray, bins: int = VENTILES) -> np.ndarray:
    """``bins``-quantile step function of ``a`` as ``bins - 1`` dummies (first dropped).

    miso-237's P2 non-parametric price representation, reproduced byte-for-byte
    (``_miso237_price_representation_vs_state_phase0.ventile_dummies``): exactly the class of
    response the model's band ladder can already express in the spread.
    """
    edges = np.quantile(a, np.linspace(0.0, 1.0, bins + 1)[1:-1])
    idx = np.searchsorted(edges, a, side="right")
    cols = [(idx == b).astype(float) for b in range(1, bins)]
    return np.column_stack(cols) if cols else np.zeros((len(a), 0))


def resid_on(x: np.ndarray, design: np.ndarray) -> np.ndarray:
    """Residual of ``x`` on an explicit design matrix (intercept already included)."""
    return x - design @ np.linalg.lstsq(design, x, rcond=None)[0]


def gamma_weights(s_own: np.ndarray, n: int) -> np.ndarray:
    """The FIXED weight vector ``w`` with ``gamma(r) = w . r`` (PREREG §0d(4)).

    ``gamma`` is ``e_1^T (X^T X)^-1 X^T r`` with ``X = [1 | s_own]``; row 1 of the
    pseudo-inverse IS that functional. Because it does not depend on ``r``, ``gamma``
    decomposes EXACTLY over any partition of the hours, which is what §3b's FLOOR / CAP /
    INTERIOR split of ``gamma_CURVE`` uses.
    """
    return np.linalg.pinv(_design(s_own, n))[1]


def interp_knots(x: np.ndarray, xk: np.ndarray, yk: np.ndarray) -> np.ndarray:
    """Piecewise-linear interpolation through ``(xk, yk)``, CLAMPED outside the knot range.

    ``np.interp`` clamps to the endpoint values by construction, which is exactly the
    PREREG §2a behaviour (``g_cont`` is flat at 0 below the first knot and at ``G_7`` above
    the last, sharing ``g``'s bounds).
    """
    return np.interp(x, xk, yk)


def _fmt3(vals) -> str:
    return "[" + ", ".join(f"{v:.3f}" for v in vals) + "]"


def main() -> int:  # noqa: PLR0915 - one linear probe, mirrors the PREREG section order
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
    prior235 = json.loads(MISO235.read_text())["years"]
    prior237 = json.loads(MISO237.read_text())["years"]

    bal = load_balance_miso()
    bal["hour"] = hour_index(bal["local"])
    bal["year"] = (pd.to_datetime(bal["local"]) - pd.Timedelta(hours=1)).dt.year
    bal = bal[(bal["hour"] >= 0) & (bal["hour"] < HOURS)]

    report: dict = {
        "probe": (
            "miso-239 phase 0 — LINEAR / CURVE / STEP attribution of the PJM merit ladder's "
            "own-net-load response: which property of g does it?"
        ),
        "prereg": (
            "results/calibration/PREREG-miso239-which-property-of-g-2026-09-07.md"
            " (pushed c0e971ee)"
        ),
        "predecessor_record_disclosure": (
            "miso-238's FINDING and its phase-0 JSON never reached main, and the committed "
            "miso-238 probe carried the un-repaired (marginal-covariance) estimator its own "
            "ADDENDUM §2 replaced. This session applied that declared repair and regenerated "
            "_miso238_pjm_seam_channel_attribution_phase0.json; G-P4 below reproduces "
            "miso-238's published column from scratch against the values the handoff quotes, "
            "restated in PREREG §1 BEFORE being recomputed."
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "price_basis": (
            "Indiana hub RT builds the ok mask and is the alignment price P; every regressor "
            "and every merit signal is Indiana hub DA. The ladder clears on the MODEL bus "
            "spread s = p_bus - p_border; the removed regressor is p1 = da - p_border. They "
            "are DIFFERENT SPREADS (PREREG §0d(3)) and that is what the LINEAR channel is."
        ),
        "estimator": (
            "gamma = PARTIAL OLS slope on z_own_net_load in r ~ [1 | z_own_nl | z_own_VRE] "
            "(miso-237's estimator via miso-238 ADDENDUM §2). gamma_marginal (the simple "
            "covariance) is REPORTED beside it and NEVER gated."
        ),
        "bars": {
            "tol_sigma_mw": TOL_SIGMA_MW,
            "tol_coef_mw_per_z": TOL_COEF_MW,
            "tol_alignment": TOL_ALIGN,
            "tol_identity_mw": TOL_IDENTITY_MW,
            "channel_bar": CHANNEL_BAR,
            "gamma_floor_mw_per_z": GAMMA_FLOOR_MW,
            "sub_verdict_floor_mw_per_z": SUB_FLOOR_MW,
            "np_survive_bar": NP_SURVIVE_BAR,
            "np_collapse_bar": NP_COLLAPSE_BAR,
            "miso238_gp4_bars": MISO238_BARS,
        },
        "gated_seam": GATED_SEAM,
        "tranches": SEAM_FLOW_TRANCHES,
    }

    provenance: dict[str, dict] = {}
    years_out: dict[str, dict] = {}
    export_zero: dict[str, dict] = {}

    for yi, year in enumerate(YEARS):
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        p_rt = act[ok]

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

        miso_nl = (miso_series("demand") - miso_series("wind") - miso_series("solar"))[
            ok
        ]
        miso_vre = (miso_series("wind") + miso_series("solar"))[ok]
        z_nl = _z(miso_nl)
        s_own = np.column_stack([z_nl, _z(miso_vre)])
        nT = int(ok.sum())
        w_gamma = gamma_weights(s_own, nT)

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        p1_of = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }

        # ---- G-X0 (all four seams, so "PJM is the only seam this object exists on" is
        # ---- MEASURED rather than asserted; only PJM is gated on it) ----
        ez: dict[str, float] = {}
        for seam in FOUR_SEAM:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb_s = bus_price[BUS_OF_SEAM[seam]]
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            me_s = (pb_s[None, :] < lade[:, None])[:, ok].astype(float)
            be_s = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )[:, ok]
            ez[seam] = float(np.abs((me_s * be_s).sum(0)).max())
        export_zero[str(year)] = {k: round(v, 6) for k, v in ez.items()}

        # ---- the provenance legs that need all four seams (G-P1 / G-P2 / G-P3) ----
        prov: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb_s = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                dk = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                merit_sig = pb_s - border
            elif seam == "SPP":
                dk = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ],
                    float,
                )
                merit_sig = pb_s - spp_hub
            else:
                dk = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                merit_sig = pb_s
            mi_s = (merit_sig[None, :] > dk[:, None])[:, ok].astype(float)
            bi_s = np.clip(
                np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width
            )[:, ok]
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            me_s = (pb_s[None, :] < lade[:, None])[:, ok].astype(float)
            be_s = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )[:, ok]
            model_net = (mi_s * bi_s).sum(0) - (me_s * be_s).sum(0)
            meas_net = dense(seam)[ok]
            p1s = p1_of[seam][ok]
            r_meas = ols_resid(meas_net, p1s)
            r_model = ols_resid(model_net, p1s)
            ref235 = prior235[str(year)]["decomposition"][seam]
            r237 = prior237[str(year)]["seams"][seam]["own_state_reported"]
            a237 = prior237[str(year)]["seams"][seam]["own_state_purge_addendum_A"]
            rm_p = M8.purge(r_model, s_own)
            rx_p = M8.purge(r_meas, s_own)
            align = {
                "alignment_model": M8.corr_abs(r_model, p_rt),
                "alignment_model_purged": M8.corr_abs(rm_p, p_rt),
                "alignment_measured": M8.corr_abs(r_meas, p_rt),
                "alignment_measured_purged": M8.corr_abs(rx_p, p_rt),
            }
            prov[seam] = {
                "max_abs_delta_sigma_mw": round(
                    max(
                        abs(float(meas_net.std()) - ref235["sigma_measured_mw"]),
                        abs(float(r_meas.std()) - ref235["sigma_resid_measured_mw"]),
                    ),
                    3,
                ),
                "max_abs_delta_coef_mw_per_z": round(
                    max(
                        abs(
                            gamma(r_model, s_own)
                            - float(r237["own_net_load_coef_resid_model"])
                        ),
                        abs(
                            gamma(r_meas, s_own)
                            - float(r237["own_net_load_coef_resid_measured"])
                        ),
                    ),
                    3,
                ),
                "max_abs_delta_alignment": round(
                    max(abs(align[k] - float(a237[k])) for k in align), 5
                ),
            }
        provenance[str(year)] = prov

        # ================= the GATED seam: PJM =================
        spec = specs["PJM"]
        width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
        pb = bus_price["MISO_external"]
        dk = np.asarray(
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"], float
        )
        s_spread = (pb - border)[ok]
        mi = (s_spread[None, :] > dk[:, None]).astype(float)
        bi = np.clip(np.asarray(env_i["PJM"], float)[None, :] - ks * width, 0.0, width)[
            :, ok
        ]
        p1s = p1_of["PJM"][ok]

        b_bar = bi.mean(axis=1)
        m_bar = mi.mean(axis=1)
        g_step = (mi * b_bar[:, None]).sum(0)
        merit = ((mi - m_bar[:, None]) * b_bar[:, None]).sum(0)
        n_bands = mi.sum(0).round().astype(int)
        cum_g = np.cumsum(b_bar)

        # The ladder is sorted, so the in-merit set is exactly {0..n-1}: verify, never assume.
        g_from_count = np.where(n_bands > 0, cum_g[np.maximum(n_bands - 1, 0)], 0.0)
        count_identity = float(np.abs(g_step - g_from_count).max())

        # ---- PREREG §2a: the three counterfactual responses ----
        sc = s_spread - s_spread.mean()
        beta = float((sc * (g_step - g_step.mean())).mean() / (sc * sc).mean())
        linear = beta * sc

        present = sorted({int(v) for v in n_bands})
        xk = np.array([s_spread[n_bands == n].mean() for n in present])
        yk = np.array([0.0 if n == 0 else float(cum_g[n - 1]) for n in present])
        knots_increasing = bool(np.all(np.diff(xk) > 0)) and bool(
            np.all(np.diff(yk) >= 0)
        )
        g_cont = interp_knots(s_spread, xk, yk)

        curve = (g_cont - g_cont.mean()) - linear
        step = (g_step - g_step.mean()) - (g_cont - g_cont.mean())
        identity_max_abs = float(np.abs(linear + curve + step - merit).max())

        # ---- PREREG §2c: the declared robustness twin ----
        xk2 = np.concatenate(
            [
                [min(float(s_spread.min()), float(dk[0]) - 1e-9)],
                dk,
                [max(float(s_spread.max()), float(dk[-1]) + 1e-9)],
            ]
        )
        yk2 = np.concatenate(
            [
                [0.0],
                np.concatenate([[0.0], cum_g[:-1]]) + b_bar / 2.0,
                [float(cum_g[-1])],
            ]
        )
        g_cont2 = interp_knots(s_spread, xk2, yk2)
        curve2 = (g_cont2 - g_cont2.mean()) - linear
        step2 = (g_step - g_step.mean()) - (g_cont2 - g_cont2.mean())

        series = {"LINEAR": linear, "CURVE": curve, "STEP": step}
        r_chan = {c: ols_resid(v, p1s) for c, v in series.items()}
        r_merit = ols_resid(merit, p1s)
        g_merit = gamma(r_merit, s_own)
        g_chan = {c: gamma(r_chan[c], s_own) for c in CHANNELS}
        share = {c: g_chan[c] / g_merit for c in CHANNELS}
        g_twin = {
            "CURVE": gamma(ols_resid(curve2, p1s), s_own),
            "STEP": gamma(ols_resid(step2, p1s), s_own),
        }

        # ---- PREREG §3b: the exact hour partition, gamma(r) = w . r ----
        masks = {
            "FLOOR": n_bands == 0,
            "INTERIOR": (n_bands >= 1) & (n_bands <= SEAM_FLOW_TRANCHES - 1),
            "CAP": n_bands == SEAM_FLOW_TRANCHES,
        }
        region_gamma = {
            c: {
                reg: float((w_gamma[msk] * r_chan[c][msk]).sum())
                for reg, msk in masks.items()
            }
            for c in CHANNELS
        }
        region_gamma["MERIT"] = {
            reg: float((w_gamma[msk] * r_merit[msk]).sum())
            for reg, msk in masks.items()
        }
        region_identity = max(
            abs(
                sum(region_gamma[c].values())
                - (g_chan[c] if c in CHANNELS else g_merit)
            )
            for c in (*CHANNELS, "MERIT")
        )

        # ---- PREREG §4: the non-parametric limb, and the two tautology checks ----
        one = np.ones((nT, 1))
        d_np_p1 = np.column_stack([one, ventile_dummies(p1s)])
        d_np_s = np.column_stack([one, ventile_dummies(s_spread)])
        d_count = np.column_stack(
            [one]
            + [
                (n_bands == n).astype(float)[:, None]
                for n in present[1:]  # first level dropped
            ]
        )
        g_np_p1 = gamma(resid_on(merit, d_np_p1), s_own)
        g_np_s = gamma(resid_on(merit, d_np_s), s_own)
        g_np_count = gamma(resid_on(merit, d_count), s_own)

        hist = {
            str(n): int((n_bands == n).sum()) for n in range(SEAM_FLOW_TRANCHES + 1)
        }

        years_out[str(year)] = {
            "n_ok_hours": nT,
            "gamma_merit_mw_per_z": round(g_merit, 2),
            "gamma_merit_marginal_mw_per_z": round(gamma_marginal(r_merit, z_nl), 2),
            "by_channel_mw_per_z": {c: round(g_chan[c], 2) for c in CHANNELS},
            "share_of_merit": {c: round(share[c], 4) for c in CHANNELS},
            "share_nonlinear": round(share["CURVE"] + share["STEP"], 4),
            "share_step_of_nonlinear": round(
                g_chan["STEP"] / (g_chan["CURVE"] + g_chan["STEP"]), 4
            ),
            "region_gamma_mw_per_z": {
                c: {r: round(v, 2) for r, v in region_gamma[c].items()}
                for c in (*CHANNELS, "MERIT")
            },
            "share_curve_clipped_regions": round(
                (region_gamma["CURVE"]["FLOOR"] + region_gamma["CURVE"]["CAP"])
                / g_chan["CURVE"],
                4,
            ),
            "share_curve_interior": round(
                region_gamma["CURVE"]["INTERIOR"] / g_chan["CURVE"], 4
            ),
            "non_parametric_limb": {
                "gamma_np_ventiles_p1_mw_per_z": round(g_np_p1, 2),
                "ratio_np_over_merit": round(abs(g_np_p1) / abs(g_merit), 4),
                "gamma_np_ventiles_model_spread_mw_per_z": round(g_np_s, 2),
                "gamma_np_band_count_dummies_mw_per_z": round(g_np_count, 6),
                "tautology_note": (
                    "band-count dummies span MERIT exactly (MERIT is measurable w.r.t. "
                    "n(t)), so the last value MUST be 0 — a framing check, not a verdict"
                ),
            },
            "twin_reported_not_gated": {
                "gamma_curve_mw_per_z": round(g_twin["CURVE"], 2),
                "gamma_step_mw_per_z": round(g_twin["STEP"], 2),
                "share_curve": round(g_twin["CURVE"] / g_merit, 4),
                "share_step": round(g_twin["STEP"] / g_merit, 4),
                "share_step_of_nonlinear": round(
                    g_twin["STEP"] / (g_twin["CURVE"] + g_twin["STEP"]), 4
                ),
            },
            "census_reported_not_gated": {
                "delta_k": [round(float(v), 2) for v in dk],
                "b_bar_mw": [round(float(v), 1) for v in b_bar],
                "cum_g_mw": [round(float(v), 1) for v in cum_g],
                "band_count_histogram": hist,
                "level_set_knots": [
                    {
                        "n": int(n),
                        "mean_spread": round(float(x), 3),
                        "g_mw": round(float(y), 1),
                    }
                    for n, x, y in zip(present, xk, yk, strict=True)
                ],
                "beta_mw_per_dollar": round(beta, 2),
                "sigma_g_step_mw": round(float(g_step.std()), 1),
                "sigma_g_cont_mw": round(float(g_cont.std()), 1),
                "sigma_g_lin_mw": round(float(linear.std()), 1),
                "corr_model_spread_vs_p1": round(
                    float(np.corrcoef(s_spread, p1s)[0, 1]), 4
                ),
                "corr_model_spread_vs_z_own_net_load": round(
                    float(np.corrcoef(s_spread, z_nl)[0, 1]), 4
                ),
                "corr_p1_vs_z_own_net_load": round(
                    float(np.corrcoef(p1s, z_nl)[0, 1]), 4
                ),
            },
            "identity_checks": {
                "channel_identity_max_abs_mw": float(f"{identity_max_abs:.3e}"),
                "band_count_identity_max_abs_mw": float(f"{count_identity:.3e}"),
                "region_partition_max_abs_mw_per_z": float(f"{region_identity:.3e}"),
                "knots_strictly_increasing": knots_increasing,
            },
            "gp4_miso238": {},
        }

        # ---- G-P4: miso-238's published PJM column, recomputed from scratch ----
        m8 = json.loads(
            (
                REPO
                / "results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json"
            ).read_text()
        )["years"][str(year)]["seams"]["PJM"]
        got = {
            "gamma_model_mw_per_z": m8["own_net_load_response"]["gamma_model_mw_per_z"],
            "share_merit": m8["own_net_load_response"]["share_of_model"]["MERIT"],
            "share_envelope_plus_interact": m8["own_net_load_response"][
                "share_envelope_plus_interact"
            ],
            "a_merit_purged_mw": m8["price_alignment"]["a_by_channel_purged_mw"][
                "MERIT"
            ],
            "a_model_purged_mw": m8["price_alignment"]["a_model_purged_mw"],
            "a_measured_purged_mw": m8["price_alignment"]["a_measured_purged_mw"],
            "sat_share": m8["saturation_census_reported_not_gated"]["sat_share"],
            "mean_bands_in_merit": m8["saturation_census_reported_not_gated"][
                "mean_bands_in_merit"
            ],
            "corr_env_import_own_net_load": m8["saturation_census_reported_not_gated"][
                "corr_env_import_own_net_load"
            ],
        }
        years_out[str(year)]["gp4_miso238"] = {
            k: {
                "handoff": MISO238_PUBLISHED[k][yi],
                "recomputed": got[k],
                "abs_delta": round(abs(got[k] - MISO238_PUBLISHED[k][yi]), 6),
                "bar": MISO238_BARS[k],
                "pass": abs(got[k] - MISO238_PUBLISHED[k][yi]) <= MISO238_BARS[k],
            }
            for k in MISO238_PUBLISHED
        }
        years_out[str(year)]["gp4_miso238"]["merit_export_leg_zero"] = (
            m8["own_net_load_response"]["by_leg"]["MERIT_export"] == 0.0
        )

    # ---------------- provenance verdicts ----------------
    worst = {
        "G_P1_max_abs_delta_sigma_mw": max(
            provenance[str(y)][s]["max_abs_delta_sigma_mw"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_P2_max_abs_delta_coef_mw_per_z": max(
            provenance[str(y)][s]["max_abs_delta_coef_mw_per_z"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_P3_max_abs_delta_alignment": max(
            provenance[str(y)][s]["max_abs_delta_alignment"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_P4_max_abs_delta_over_bar": max(
            years_out[str(y)]["gp4_miso238"][k]["abs_delta"] / MISO238_BARS[k]
            for y in YEARS
            for k in MISO238_PUBLISHED
        ),
        "G_X0_pjm_export_max_abs_mw": max(export_zero[str(y)]["PJM"] for y in YEARS),
        "G_ID_max_abs_mw": max(
            years_out[str(y)]["identity_checks"]["channel_identity_max_abs_mw"]
            for y in YEARS
        ),
    }
    gate = {
        "G_P1_sigmas_miso235": worst["G_P1_max_abs_delta_sigma_mw"] <= TOL_SIGMA_MW,
        "G_P2_own_net_load_coefs_miso237": (
            worst["G_P2_max_abs_delta_coef_mw_per_z"] <= TOL_COEF_MW
        ),
        "G_P3_alignment_column_miso237": worst["G_P3_max_abs_delta_alignment"]
        <= TOL_ALIGN,
        "G_P4_miso238_published_column": worst["G_P4_max_abs_delta_over_bar"] <= 1.0,
        "G_X0_pjm_export_leg_identically_zero": worst["G_X0_pjm_export_max_abs_mw"]
        == 0.0,
        "G_ID_decomposition_identity": worst["G_ID_max_abs_mw"] <= TOL_IDENTITY_MW,
    }
    gate["ALL_PASS"] = all(gate.values())
    report["provenance_gate"] = {
        "worst_case": worst,
        "legs": gate,
        "by_year": provenance,
        "export_leg_max_abs_mw_all_seams": export_zero,
        "export_leg_note": (
            "PREREG §3: MERIT = g(s) - mean g holds ONLY where the export leg is "
            "identically zero. Reported for all four seams so 'PJM is the only seam this "
            "object exists on' is measured, not asserted; only PJM is gated."
        ),
    }

    # ---------------- PREREG §3/§4 verdicts ----------------
    sh = {c: [years_out[str(y)]["share_of_merit"][c] for y in YEARS] for c in CHANNELS}
    g_abs = [abs(years_out[str(y)]["gamma_merit_mw_per_z"]) for y in YEARS]
    nonlin = [years_out[str(y)]["share_nonlinear"] for y in YEARS]
    step_of_nl = [years_out[str(y)]["share_step_of_nonlinear"] for y in YEARS]
    nl_abs = [
        abs(
            years_out[str(y)]["by_channel_mw_per_z"]["CURVE"]
            + years_out[str(y)]["by_channel_mw_per_z"]["STEP"]
        )
        for y in YEARS
    ]
    curve_abs = [abs(years_out[str(y)]["by_channel_mw_per_z"]["CURVE"]) for y in YEARS]
    clipped = [years_out[str(y)]["share_curve_clipped_regions"] for y in YEARS]
    interior = [years_out[str(y)]["share_curve_interior"] for y in YEARS]

    if not all(v >= GAMMA_FLOOR_MW for v in g_abs):
        verdict = "NOT MEANINGFUL (below the pre-registered absolute floor)"
        sub = "n/a"
    elif all(v >= CHANNEL_BAR for v in sh["LINEAR"]):
        verdict = "REGRESSOR-CONFOUNDED (property d)"
        sub = "n/a"
    elif all(v >= CHANNEL_BAR for v in nonlin):
        verdict = "LADDER-NONLINEARITY"
        if not all(v >= SUB_FLOOR_MW for v in nl_abs):
            sub = "NOT MEANINGFUL (below the pre-registered sub-verdict floor)"
        elif all(v >= CHANNEL_BAR for v in step_of_nl):
            sub = "DISCRETENESS (property b)"
        elif not all(v >= SUB_FLOOR_MW for v in curve_abs):
            sub = "SHAPE — sub-verdict NOT MEANINGFUL (gamma_CURVE below its floor)"
        elif all(v >= CHANNEL_BAR for v in clipped):
            sub = "SHAPE -> BOUNDEDNESS (property a)"
        elif all(v >= CHANNEL_BAR for v in interior):
            sub = "SHAPE -> PLACEMENT (property c)"
        else:
            sub = "SHAPE -> MIXED-SHAPE"
    else:
        verdict = "MIXED"
        sub = "n/a"

    np_ratio = [
        years_out[str(y)]["non_parametric_limb"]["ratio_np_over_merit"] for y in YEARS
    ]
    if not all(v >= GAMMA_FLOOR_MW for v in g_abs):
        np_verdict = "NOT MEANINGFUL (below the pre-registered absolute floor)"
    elif all(v >= NP_SURVIVE_BAR for v in np_ratio):
        np_verdict = "SURVIVES"
    elif all(v <= NP_COLLAPSE_BAR for v in np_ratio):
        np_verdict = "COLLAPSES"
    else:
        np_verdict = "MIXED"

    twin_step_nl = [
        years_out[str(y)]["twin_reported_not_gated"]["share_step_of_nonlinear"]
        for y in YEARS
    ]
    twin_agrees = all(
        (a >= CHANNEL_BAR) == (b >= CHANNEL_BAR)
        for a, b in zip(step_of_nl, twin_step_nl, strict=True)
    )

    report["verdicts"] = {
        "gated_seam": GATED_SEAM,
        "Q_A_property": verdict,
        "Q_A_sub_verdict": sub,
        "shares_linear": sh["LINEAR"],
        "shares_curve": sh["CURVE"],
        "shares_step": sh["STEP"],
        "shares_nonlinear": nonlin,
        "share_step_of_nonlinear": step_of_nl,
        "share_curve_clipped_regions": clipped,
        "share_curve_interior": interior,
        "gamma_merit_mw_per_z": [
            years_out[str(y)]["gamma_merit_mw_per_z"] for y in YEARS
        ],
        "Q_C_non_parametric_spread": np_verdict,
        "Q_C_ratio_np_over_merit": np_ratio,
        "twin_agrees_on_sub_verdict": twin_agrees,
        "twin_share_step_of_nonlinear": twin_step_nl,
        "sub_verdict_fragile": not twin_agrees,
    }
    report["years"] = years_out

    OUT.write_text(json.dumps(report, indent=1) + "\n")

    print(f"provenance gate: {gate}")
    print(f"worst case: {worst}")
    if not gate["ALL_PASS"]:
        print("INSTRUMENT BROKEN — PREREG §1 forbids reading anything below.")
        return 1
    print(
        f"\ngamma_MERIT (MW/z)      {_fmt3(report['verdicts']['gamma_merit_mw_per_z'])}"
    )
    print(f"share LINEAR  (d)       {_fmt3(sh['LINEAR'])}")
    print(f"share CURVE   (a)+(c)   {_fmt3(sh['CURVE'])}")
    print(f"share STEP    (b)       {_fmt3(sh['STEP'])}")
    print(f"share nonlinear         {_fmt3(nonlin)}")
    print(f"STEP / nonlinear        {_fmt3(step_of_nl)}   twin {_fmt3(twin_step_nl)}")
    print(f"CURVE clipped regions   {_fmt3(clipped)}")
    print(f"CURVE interior          {_fmt3(interior)}")
    print(f"Q-C |gamma_np|/|gamma|  {_fmt3(np_ratio)}")
    print(f"\nQ-A  {verdict}   ->   {sub}")
    print(f"Q-C  {np_verdict}")
    print(f"twin agrees on sub-verdict: {twin_agrees}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
