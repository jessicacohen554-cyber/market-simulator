"""miso-216 — THE GAS-OFFER MARGIN ANCHOR'S BASIS/CLASS GRAIN (phase 0, zero-solve).

Executes ``results/calibration/PREREG-miso216-anchor-basis-grain-2026-09-05.md``
(pushed BLIND at ``9fcd69cd``) on the miso-213 keeper's committed sidecars and the
HEAD fleet chain. **No LP is solved. Nothing is armed and nothing is minted** — no
``ScenarioConfig`` field, no registry entry, no matrix row.

The object (miso-215 §4, carried in as FACT): ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO
["MISO"] = 3.0492`` is the mean of the ISO-level ``_gas_series`` — annual Henry Hub
plus the flat ``GAS_BASIS_DIFFERENTIAL["MISO"] = 0.30`` — while the keeper prices
the fleet by the per-plant EIA-923 print, applied on the ``(n_gen, T)`` array AFTER
that series and invisible to the anchor's derive. Since ``apply_gas_offer_margin``'s
economic content is a fixed margin ``markup_hr x anchor``, the grain at which the
anchor is identified sizes the margin installed on five ALREADY-ARMED MISO gas
classes. **This is the BASIS/CLASS grain, NOT the ZONAL grain**
(``gas_offer_margin_zonal_anchor``, adjudicated ``I`` at miso-119/120), which is not
re-tested here.

  M-0   THE F-3 INSTRUMENT REPAIR, FIRST. Every distributional statistic is
        CAPACITY-HOUR WEIGHTED on BOTH legs — weighted mean AND weighted quantiles
        (an explicit weighted-quantile over a fine price histogram, not
        ``np.percentile``). miso-215's unweighted percentiles are re-read from its
        committed record and reported beside the repaired ones, so the size of that
        defect is visible rather than quietly corrected.
  A-1   THE CANDIDATE GRAINS, ENUMERATED AND PRICED: (a) the status-quo ISO
        ``_gas_series`` window mean 3.0492; (b) the gas fleet's capacity-hour MEAN
        resolved delivered price; (c) its capacity-hour MEDIAN; (d) per-CLASS means
        and medians; (e) an ENERGY-weighted variant (weights = the tranche's own
        static-screen dispatch). Each reported PER YEAR and over the 2023-2025
        WINDOW, because the registered anchor is one scalar over the window and the
        "grain" question must never be confounded with the "window mean" question.
  A-2   WHAT EACH GRAIN DOES TO THE ARMED CLASSES: the static reach of moving ONLY
        the anchor. Under the margin form the shift is exactly
        ``markup_hr x (A' - anchor)`` — a per-row CONSTANT — so the reach is
        evaluated on a dense anchor GRID once per year and every grain is read off
        it afterwards.
  A-3   THE IDENTITY THE MECHANISM CLAIMS, TESTED DIRECTLY: per class, per year, per
        grain, the capacity-hour mean of ``|F(t) - A'|`` and the cap-weighted
        ABSOLUTE OFFER DISTORTION ``E[|markup_hr x (A' - F(t))|]`` in $/MWh against
        the registered multiplier form. That number is the packet's primary axis.
  A-4   CROSS-ISO EXPOSURE, COUNTED NOT TESTED: from COMMITTED ARTIFACTS ONLY
        (``GAS_SERIES_FLAGS``, ``GAS_BASIS_DIFFERENTIAL``, each keeper's own
        ``run_config.json`` gas flags, the by-zone registry), is each ISO's anchor
        derived on an ISO-level series while its keeper prices the fleet on a
        different basis? **No other ISO's fleet is built and no other ISO's
        delivered price is measured** (rule 25 [R-ISO-SCOPE]).

INSTRUMENT LIMITS, DISCLOSED (PREREG §3): the keeper ships no ``unit_hourly/`` or
``dispatch/``, so plant-grain model merit is a PRICE-TAKING STATIC SCREEN on the
keeper's own committed P1 zone prices — miso-214 §1 measured it at 1.41-1.43x the
LP's own CT class energy, and it holds the PRICE FIXED, so cross-class backfill is
INVISIBLE to it. Every A-2 reach is a BOUND and the C1 exposure is an
un-instrumented risk, never a measurement. The EIA-923 print is a MONTHLY ALL-IN
delivered cost applied to an HOURLY decision — the average-vs-marginal convention
(miso-212 §8) is OWNER-COURT, ADJACENT TO BUT DISTINCT FROM this lane's question
(where a fixed margin is IDENTIFIED, not which cost basis an offer uses), and is
untouched.

Usage::

    PYTHONPATH=src .venv/bin/python scripts/probes/_miso216_anchor_basis_grain_phase0.py

Record: ``results/calibration/_miso216_anchor_basis_grain.json``.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso207_bound_the_shoulder as m207  # noqa: E402
import _miso208_find_the_supply as m208  # noqa: E402
import _miso211_rdt_binding_state as _m211  # noqa: E402  (re-points to miso-210 at import)

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso214_ct_peaker_conduct_phase0 import _band, _r, keeper_price  # noqa: E402
from market_sim.config.constants import (  # noqa: E402
    GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
    GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
)
from market_sim.config.fuel_trajectories import GAS_BASIS_DIFFERENTIAL  # noqa: E402

# T-1: re-point EVERY module global to the miso-213 keeper, AFTER the last import,
# because `_miso211` (pulled in transitively) re-points `_m134.BUNDLE` to ITS OWN
# keeper, `miso210_clock_B`, at module scope. miso-214 §9 ran a whole three-year
# launch on the CONTROL config for exactly this reason; the assert below is what
# makes the repeat impossible, and miso-215 carried it forward unchanged.
KEEPER = REPO / "results/calibration/miso213_layering_B"
_m134.BUNDLE = KEEPER
m207.KEEPER = KEEPER
m208.KEEPER = KEEPER
_m211.KEEPER = KEEPER
assert _m134.BUNDLE == KEEPER and m207.KEEPER == KEEPER and m208.KEEPER == KEEPER
assert _m134.keeper_config().miso_zonal_gas_basis_skip_923_priced, (
    "T-1 re-point failed: the probe would run on the control config"
)

OUT = REPO / "results/calibration/_miso216_anchor_basis_grain.json"
MISO215 = REPO / "results/calibration/_miso215_intermediate_phys.json"
# rule 22 [R-HOLDOUT]: MISO holds no marker, so 2023-2025 are the ONLY years this
# probe may touch. The env override exists for a single-year smoke test and is
# hard-gated to the training window.
YEARS = tuple(
    int(v) for v in os.environ.get("MISO216_YEARS", "2023,2024,2025").split(",")
)
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
EPS = 1e-9

#: The MISO model gas classes. A-1's "fleet" grain is capacity-weighted over these
#: and nothing else (coal, nuclear and non-thermal never enter the gas margin).
GAS_CLASSES = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")

#: Anchor grid for A-2 / A-3. The shift the margin form applies is exactly
#: ``markup_hr x (A' - anchor)`` — a per-row CONSTANT — so a dense grid evaluated
#: once per year lets every candidate grain be read off afterwards without
#: rebuilding the fleet. Range covers every statistic the fleet can produce.
GRID = np.round(np.arange(1.50, 9.0001, 0.02), 4)

#: Weighted-quantile histogram: 0-60 $/MMBtu at half-cent resolution, so a
#: weighted median is exact to +-0.0025 $/MMBtu.
HIST_LO, HIST_HI, HIST_W = 0.0, 60.0, 0.005
HIST_N = int(round((HIST_HI - HIST_LO) / HIST_W))
HIST_EDGES = HIST_LO + HIST_W * np.arange(HIST_N + 1)
HIST_MID = HIST_LO + HIST_W * (np.arange(HIST_N) + 0.5)

# Pre-registered protective faces (PREREG §4 A-2), stated before measurement.
C1_CC_2024 = 7.419      # % against the +/-8.00 band
C1_BAND = 8.00
C8_CT_2023 = 0.2044     # forced share against the 0.15 peaker budget
C8_BUDGET = 0.15
# Pre-registered kill bars (PREREG §6).
K1_FLEET_TOL = 0.35     # $/MMBtu: fleet mean AND median within this => grain (d) only
K2_DISTORTION_BAR = 2.0  # $/MWh: below this on every armed class-year => immaterial


def whist(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Capacity-hour weighted histogram of ``values`` on the shared price grid.

    ``values`` is ``(rows, T)`` delivered fuel and ``weights`` is ``(rows,)`` MW,
    broadcast over hours — so one unit of histogram mass is one MW-hour of
    CAPACITY, which is the weighting M-0 fixes miso-215's percentiles to use.
    """
    idx = np.clip(
        ((values - HIST_LO) / HIST_W).astype(np.int64), 0, HIST_N - 1
    )
    out = np.zeros(HIST_N)
    for r in range(idx.shape[0]):
        if weights[r] <= 0.0:
            continue
        np.add.at(out, idx[r], weights[r])
    return out


def wquantile(hist: np.ndarray, q: float) -> float:
    """Weighted quantile from a histogram — the M-0 replacement for the
    unweighted ``np.percentile`` miso-215 used on the same quantity."""
    tot = hist.sum()
    if tot <= 0:
        return float("nan")
    c = np.cumsum(hist)
    i = int(np.searchsorted(c, q * tot))
    return float(HIST_MID[min(i, HIST_N - 1)])


def wmean(hist: np.ndarray) -> float:
    tot = hist.sum()
    return float((hist * HIST_MID).sum() / tot) if tot > 0 else float("nan")


def main() -> None:  # noqa: PLR0912, PLR0915
    cfg = keeper_config()
    anchor = float(cfg.gas_offer_margin_anchor)
    assert anchor == GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"], "anchor drifted from the registry"

    rep: dict = {
        "charter": "miso-216 phase 0 — the gas-offer margin anchor's BASIS/CLASS grain; zero-solve, OWNER PACKET, nothing armed.",
        "prereg": "results/calibration/PREREG-miso216-anchor-basis-grain-2026-09-05.md @ 9fcd69cd",
        "keeper": "2026-09-05-miso-213-layering",
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "registered_anchor_usd_mmbtu": anchor,
        "instrument": {
            "model_plant_grain": "PRICE-TAKING STATIC SCREEN on the keeper's own committed P1 zone prices — the keeper ships no unit_hourly/ or dispatch/. miso-214 §1 measured it at 1.41-1.43x the LP's own CT class energy. A BOUND, not the LP.",
            "backfill_blind": "the screen holds the PRICE FIXED, so cross-class backfill is INVISIBLE; the C1 exposure is an un-instrumented risk, never a measurement.",
            "M0_weighting": "every mean AND quantile below is CAPACITY-HOUR weighted (one unit of histogram mass = one MW-hour of capacity), on a 0.005 $/MMBtu grid — the F-3 repair of miso-215, whose cohort means were capacity-hour weighted while its percentiles were not.",
            "A2_shift_algebra": "under the margin form the anchor move is exactly markup_hr x (A' - anchor), a per-row CONSTANT, so A-2 is evaluated on a dense anchor grid once per year and every grain read off it.",
            "monthly_923": "the EIA-923 print is a MONTHLY ALL-IN delivered cost applied to an HOURLY decision — the average-vs-marginal convention (miso-212 §8) is OWNER-COURT, ADJACENT TO BUT DISTINCT FROM this question, and untouched.",
            "metric_identity_disclosed": "A-3's L1 mean-absolute distortion is MINIMIZED AT THE WEIGHTED MEDIAN by construction, and its L2/RMS sibling at the weighted MEAN — so a single-metric packet would have built its own answer in. All three (L1, L2, signed bias) are reported at every grain, and the decisive comparator is each class-year's BEST ACHIEVABLE SCALAR (best_scalar below), against which the registered anchor is scored.",
            "nothing_armed": "no ScenarioConfig field, no registry entry, no matrix row, no solve.",
        },
        "protective_faces_preregistered": {
            "C1_CC_REGULAR_2024_pct": C1_CC_2024, "C1_band_pct": C1_BAND,
            "C8_CT_PEAKER_2023_forced_share": C8_CT_2023, "C8_peaker_budget": C8_BUDGET,
        },
        "kill_bars": {"K1_fleet_tol": K1_FLEET_TOL, "K2_distortion_bar": K2_DISTORTION_BAR},
        "years": {},
    }

    # ---- M-0: miso-215's own unweighted percentiles, re-read for comparison ----
    m215 = json.loads(MISO215.read_text())
    rep["M0_miso215_unweighted_reference"] = {
        "what": "miso-215's cap-weighted MEAN beside its UNWEIGHTED p25/p50/p75 for the same cohorts — the defect F-3 names. The repaired, capacity-hour-weighted values are in years.<y>.A1_class_stats below.",
        "rows": {
            yr: {
                ck: {
                    "cap_w_mean": (cv["intermediate"] or {}).get("cap_w_delivered_fuel_usd_mmbtu"),
                    "unweighted_p25_p50_p75": (cv["intermediate"] or {}).get("delivered_fuel_p25_p50_p75"),
                }
                for ck, cv in m215["years"][yr]["M1_M2_M3_cohorts"].items()
            }
            for yr in m215["years"]
        },
    }

    # ---- pooled window accumulators ---------------------------------------
    pool_cap: dict[str, np.ndarray] = {}      # class -> capacity-hour histogram
    pool_en: dict[str, np.ndarray] = {}       # class -> energy-weighted histogram
    pool_fleet_cap = np.zeros(HIST_N)
    pool_fleet_en = np.zeros(HIST_N)
    # grid curves accumulated over years: class -> (n_grid,) TWh and $/MWh-weight
    grid_reach: dict[str, dict[int, np.ndarray]] = {}
    grid_dist: dict[str, dict[int, np.ndarray]] = {}
    grid_rms: dict[str, dict[int, np.ndarray]] = {}
    grid_bias: dict[str, dict[int, np.ndarray]] = {}
    class_cap_marked: dict[str, float] = {}

    for year in YEARS:
        y: dict = {}
        raw_fleet, fleet, arrays, fp, mc, zones = build_year(cfg, year)
        gc.collect()
        # F-4's two-build technique, reused: the same resolution with the
        # dual-fuel oil-parity step disarmed, so the "delivered price" this
        # session anchors against is verified to be a GAS print.
        fp_gas = build_year(
            dataclasses.replace(cfg, dual_fuel_switching=False), year
        )[3]
        gc.collect()

        klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
        bands = np.array([_band(str(g.unit_id)) for g in fleet])
        pmax = np.asarray(arrays.pmax, float)
        avail = np.asarray(arrays.availability, float)
        zi = np.asarray(arrays.zone_idx)
        markup = np.array(
            [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet]
        )
        price = keeper_price(KEEPER, year, zones)
        gas = np.flatnonzero(np.isin(klass, GAS_CLASSES))
        zp = price[zi[gas], :]
        availcap = pmax[gas][:, None] * avail[gas]
        merit0 = mc[gas] <= zp
        mw0 = availcap * merit0

        y["N1_footing"] = {
            "n_gas_tranches": int(gas.size),
            "gas_capacity_mw": _r(float(pmax[gas].sum()), 1),
            "gas_capacity_marked_up_mw": _r(float(pmax[gas][markup[gas] > 0].sum()), 1),
            "n_tranches_marked_up": int((markup[gas] > 0).sum()),
            "screen_gas_twh": _r(float(mw0.sum()) / 1e6, 3),
            "oil_parity_binding_cap_hour_share": _r(
                float(((fp[gas] > fp_gas[gas] + 1e-6) * pmax[gas][:, None]).sum()
                      / max(pmax[gas].sum() * HOURS, EPS))
            ),
            "max_abs_fp_minus_fpgas_usd_mmbtu": _r(
                float(np.abs(fp[gas] - fp_gas[gas]).max()), 4
            ),
        }

        # ---- A-1 per-year statistics, capacity-hour AND energy weighted ----
        cls_stats: dict[str, dict] = {}
        fleet_cap_h = np.zeros(HIST_N)
        fleet_en_h = np.zeros(HIST_N)
        for cl in GAS_CLASSES:
            rows = np.flatnonzero(klass == cl)
            if rows.size == 0:
                continue
            h_cap = whist(fp[rows], pmax[rows])
            # energy weights: the tranche's own static-screen dispatch, per row
            sel = np.isin(gas, rows)
            en_row = mw0[sel].sum(axis=1)
            h_en = whist(fp[rows], en_row)
            fleet_cap_h += h_cap
            fleet_en_h += h_en
            pool_cap[cl] = pool_cap.get(cl, np.zeros(HIST_N)) + h_cap
            pool_en[cl] = pool_en.get(cl, np.zeros(HIST_N)) + h_en
            mk = markup[rows]
            capm = float(pmax[rows][mk > 0].sum())
            class_cap_marked[cl] = max(class_cap_marked.get(cl, 0.0), capm)
            # PREREG §3 FOOTING CHECK: miso-215 published the ECON-band
            # cap-weighted markup (CT_PEAKER remainder 3.9059 -> $11.91/MWh at
            # the anchor). This probe's class-level markup spans EVERY marked-up
            # band (econ + peak + committed), a different and larger quantity, so
            # the econ-only figure is emitted beside it for the check.
            econ_m = np.array([b.startswith("econ") for b in bands[rows]])
            e_live = econ_m & (mk > 0)
            cls_stats_econ = (
                float((mk[e_live] * pmax[rows][e_live]).sum()
                      / max(pmax[rows][e_live].sum(), EPS)) if e_live.any() else 0.0
            )
            cls_stats[cl] = {
                "capacity_mw": _r(float(pmax[rows].sum()), 1),
                "capacity_marked_up_mw": _r(capm, 1),
                "cap_w_markup_hr_over_marked": _r(
                    float((mk[mk > 0] * pmax[rows][mk > 0]).sum() / max(capm, EPS)), 4
                ) if capm > 0 else 0.0,
                "cap_w_mean_fuel": _r(wmean(h_cap), 4),
                "cap_w_p25_p50_p75": [_r(wquantile(h_cap, q), 4) for q in (.25, .50, .75)],
                "energy_w_mean_fuel": _r(wmean(h_en), 4),
                "energy_w_median_fuel": _r(wquantile(h_en, 0.50), 4),
                "screen_twh": _r(float(en_row.sum()) / 1e6, 3),
                "cap_w_markup_hr_ECON_ONLY": _r(cls_stats_econ, 4),
                "cap_w_offer_usd_mwh": _r(
                    float((mc[rows].mean(axis=1) * pmax[rows]).sum()
                          / max(pmax[rows].sum(), EPS)), 3
                ),
                # the dual-fuel counterfactual, BOTH directions (F-4's technique
                # reused): where the resolved price and the no-switch price
                # differ at all, and where the resolved one is HIGHER (an oil
                # step raising the offer, which is the only direction that could
                # inflate a delivered-price statistic).
                "dualfuel_diverge_cap_hour_share": _r(
                    float(((np.abs(fp[rows] - fp_gas[rows]) > 1e-6)
                           * pmax[rows][:, None]).sum()
                          / max(pmax[rows].sum() * HOURS, EPS))
                ),
                "dualfuel_resolved_above_noswitch_share": _r(
                    float(((fp[rows] > fp_gas[rows] + 1e-6) * pmax[rows][:, None]).sum()
                          / max(pmax[rows].sum() * HOURS, EPS))
                ),
            }
        pool_fleet_cap += fleet_cap_h
        pool_fleet_en += fleet_en_h
        y["A1_class_stats"] = cls_stats
        y["A1_fleet_stats"] = {
            "cap_w_mean_fuel": _r(wmean(fleet_cap_h), 4),
            "cap_w_p25_p50_p75": [_r(wquantile(fleet_cap_h, q), 4) for q in (.25, .50, .75)],
            "energy_w_mean_fuel": _r(wmean(fleet_en_h), 4),
            "energy_w_median_fuel": _r(wquantile(fleet_en_h, 0.50), 4),
        }

        # ---- A-2 / A-3 on the anchor GRID, per class -----------------------
        for cl in GAS_CLASSES:
            rows = np.flatnonzero(klass == cl)
            if rows.size == 0:
                continue
            sel = np.isin(gas, rows)
            mk = markup[rows]
            live = mk > 0.0
            base_twh = float(mw0[sel].sum()) / 1e6
            reach = np.zeros(GRID.size)
            dist = np.zeros(GRID.size)
            dist_rms = np.zeros(GRID.size)
            dist_bias = np.zeros(GRID.size)
            if live.any():
                sub = np.flatnonzero(sel)[live]
                mk_l = mk[live]
                cap_l = pmax[rows][live]
                mc_l = mc[gas][sub]
                zp_l = zp[sub]
                ac_l = availcap[sub]
                fp_l = fp[gas][sub]
                base_l = float((ac_l * (mc_l <= zp_l)).sum())
                for i, a in enumerate(GRID):
                    shift = mk_l * (a - anchor)
                    reach[i] = (
                        float((ac_l * ((mc_l + shift[:, None]) <= zp_l)).sum())
                        - base_l
                    ) / 1e6
                    # THREE metrics, because the choice among them IS the
                    # choice of grain (see the finding's §5): L1 mean-absolute
                    # distortion is minimized at the weighted MEDIAN by
                    # construction, L2 RMS at the weighted MEAN, and the SIGNED
                    # bias is zero at the weighted MEAN. Reporting only L1 would
                    # have built the median's advantage into the instrument.
                    dev = (a - fp_l) * mk_l[:, None]          # $/MWh, signed
                    dist[i] = float((np.abs(dev).mean(axis=1) * cap_l).sum()
                                    / max(cap_l.sum(), EPS))
                    dist_rms[i] = float(
                        (np.sqrt((dev ** 2).mean(axis=1)) * cap_l).sum()
                        / max(cap_l.sum(), EPS)
                    )
                    dist_bias[i] = float((dev.mean(axis=1) * cap_l).sum()
                                         / max(cap_l.sum(), EPS))
                del sub, mk_l, cap_l, mc_l, zp_l, ac_l, fp_l
            grid_reach.setdefault(cl, {})[year] = reach
            grid_dist.setdefault(cl, {})[year] = dist
            grid_rms.setdefault(cl, {})[year] = dist_rms
            grid_bias.setdefault(cl, {})[year] = dist_bias
            # THE DECISIVE COMPARATOR: the BEST scalar anchor available to this
            # class-year on each metric, and its argmin. If the status quo is
            # already near it, the grain question is immaterial however far the
            # anchor sits from any particular class statistic.
            if live.any():
                j1, j2 = int(np.argmin(dist)), int(np.argmin(dist_rms))
                cls_stats[cl].setdefault("best_scalar", {})
                cls_stats[cl]["best_scalar"] = {
                    "L1_min_distortion_usd_mwh": _r(float(dist[j1]), 3),
                    "L1_argmin_anchor": _r(float(GRID[j1]), 4),
                    "L1_at_registered_anchor": _r(
                        float(np.interp(anchor, GRID, dist)), 3),
                    "L1_excess_of_registered_over_best_pct": _r(
                        100.0 * (float(np.interp(anchor, GRID, dist)) - float(dist[j1]))
                        / max(float(dist[j1]), EPS), 2),
                    "L2_min_rms_usd_mwh": _r(float(dist_rms[j2]), 3),
                    "L2_argmin_anchor": _r(float(GRID[j2]), 4),
                    "L2_at_registered_anchor": _r(
                        float(np.interp(anchor, GRID, dist_rms)), 3),
                    "signed_bias_at_registered_anchor_usd_mwh": _r(
                        float(np.interp(anchor, GRID, dist_bias)), 3),
                }
            cls_stats[cl]["screen_twh_base"] = _r(base_twh, 4)

        rep["years"][str(year)] = y
        del raw_fleet, fleet, arrays, fp, fp_gas, mc, price, zp, availcap, mw0, merit0
        gc.collect()

    # ---- A-1: the candidate grains, per year and over the WINDOW -----------
    yrs = [str(v) for v in YEARS]

    def _win(h):
        return {"cap_w_mean": _r(wmean(h), 4),
                "cap_w_median": _r(wquantile(h, 0.50), 4)}

    grains: dict[str, dict] = {
        "a_status_quo_iso_series": {
            "what": "the registered anchor: the mean of the ISO-level _gas_series (annual Henry Hub + the flat GAS_BASIS_DIFFERENTIAL 0.30), 2023-2025.",
            "window_anchor": anchor,
            "per_year": {yr: anchor for yr in yrs},
            "weighting": "none — an ISO price series, not a fleet statistic",
        },
        "b_fleet_cap_hour_mean": {
            "what": "the gas fleet's own capacity-hour MEAN resolved delivered price.",
            "window_anchor": _r(wmean(pool_fleet_cap), 4),
            "per_year": {yr: rep["years"][yr]["A1_fleet_stats"]["cap_w_mean_fuel"] for yr in yrs},
            "weighting": "capacity-hour (MW x h)",
        },
        "c_fleet_cap_hour_median": {
            "what": "the gas fleet's own capacity-hour MEDIAN resolved delivered price.",
            "window_anchor": _r(wquantile(pool_fleet_cap, 0.50), 4),
            "per_year": {yr: rep["years"][yr]["A1_fleet_stats"]["cap_w_p25_p50_p75"][1] for yr in yrs},
            "weighting": "capacity-hour (MW x h)",
        },
        "e_fleet_energy_weighted_mean": {
            "what": "ENERGY-weighted mean (weights = each tranche's own static-screen dispatch MWh) rather than capacity-hour weighted.",
            "window_anchor": _r(wmean(pool_fleet_en), 4),
            "per_year": {yr: rep["years"][yr]["A1_fleet_stats"]["energy_w_mean_fuel"] for yr in yrs},
            "weighting": "screen-dispatch energy (MWh) — a BOUND, the screen runs 1.41-1.43x the LP",
        },
    }
    grains["d_per_class"] = {
        "what": "a per-CLASS registry — the natural sibling of the existing per-ZONE GAS_OFFER_MARGIN_ANCHOR_BY_ZONE. Window mean and median per class.",
        "weighting": "capacity-hour (MW x h), within the class",
        "window_anchor_by_class_mean": {
            cl: _r(wmean(pool_cap[cl]), 4) for cl in sorted(pool_cap)
        },
        "window_anchor_by_class_median": {
            cl: _r(wquantile(pool_cap[cl], 0.50), 4) for cl in sorted(pool_cap)
        },
        "window_anchor_by_class_energy_mean": {
            cl: _r(wmean(pool_en[cl]), 4) for cl in sorted(pool_en)
        },
    }
    rep["A1_grains"] = grains
    rep["A1_window_fleet"] = {"capacity_hour": _win(pool_fleet_cap),
                              "energy": _win(pool_fleet_en)}

    # ---- A-2 / A-3 read off the grid at each grain's anchor ----------------
    def _at(curve: np.ndarray, a: float) -> float:
        return float(np.interp(a, GRID, curve))

    grain_anchor_for: dict[str, dict[str, float]] = {
        "a_status_quo_iso_series": {cl: anchor for cl in pool_cap},
        "b_fleet_cap_hour_mean": {cl: float(wmean(pool_fleet_cap)) for cl in pool_cap},
        "c_fleet_cap_hour_median": {cl: float(wquantile(pool_fleet_cap, 0.50)) for cl in pool_cap},
        "d_per_class_mean": {cl: float(wmean(pool_cap[cl])) for cl in pool_cap},
        "d_per_class_median": {cl: float(wquantile(pool_cap[cl], 0.50)) for cl in pool_cap},
        "e_fleet_energy_weighted_mean": {cl: float(wmean(pool_fleet_en)) for cl in pool_cap},
    }
    rep["A2_A3_by_grain"] = {}
    for gname, amap in grain_anchor_for.items():
        rows_out: dict[str, dict] = {}
        for cl in sorted(pool_cap):
            if cl not in grid_reach or class_cap_marked.get(cl, 0.0) <= 0:
                continue
            a = amap[cl]
            rows_out[cl] = {
                "anchor_used": _r(a, 4),
                "anchor_minus_registered": _r(a - anchor, 4),
                "A3_distortion_usd_mwh_by_year": [
                    _r(_at(grid_dist[cl][v], a), 3) for v in YEARS
                ],
                "A3_rms_usd_mwh_by_year": [
                    _r(_at(grid_rms[cl][v], a), 3) for v in YEARS
                ],
                "A3_signed_bias_usd_mwh_by_year": [
                    _r(_at(grid_bias[cl][v], a), 3) for v in YEARS
                ],
                "A2_reach_twh_by_year": [
                    _r(_at(grid_reach[cl][v], a), 4) for v in YEARS
                ],
                "fixed_margin_usd_mwh": _r(
                    a * float(
                        np.mean([
                            rep["years"][yr]["A1_class_stats"][cl]["cap_w_markup_hr_over_marked"]
                            for yr in yrs
                            if cl in rep["years"][yr]["A1_class_stats"]
                        ])
                    ), 3
                ),
            }
        rep["A2_A3_by_grain"][gname] = rows_out

    # ---- A-4 cross-ISO exposure, COMMITTED ARTIFACTS ONLY ------------------
    sys.path.insert(0, str(REPO / "scripts" / "data"))
    from derive_gas_offer_margin_anchor import (  # noqa: E402
        GAS_SERIES_FLAGS,
        ZONAL_BASIS_ISOS,
    )

    KEEPERS = {
        "ERCOT": "results/calibration/ercot234_eastex_identity",
        "PJM": "results/calibration/pjm_debugb_inputclock_A",
        "CAISO": "results/calibration/caiso246_b1_spot_coverage",
        "MISO": "results/calibration/miso213_layering_B",
        "NYISO": "results/calibration/nyiso189_steam_identity",
        "NEISO": "results/calibration/neiso99_joint_B",
    }
    FUEL_FLAGS = ("gas_plant_monthly_fuel_pricing", "gas_monthly_actuals",
                  "gas_hub_basis_overlay", "gas_hub_basis_daily", "gas_daily_shape",
                  "gas_seasonality", "gas_offer_net_revenue_margin",
                  "gas_offer_margin_zonal_anchor")
    ZONAL_FLAG = {"ERCOT": "ercot_zonal_gas_basis", "PJM": "pjm_zonal_gas_basis",
                  "MISO": "miso_zonal_gas_basis", "NYISO": "nyiso_zonal_gas_basis",
                  "CAISO": "caiso_zonal_gas_basis", "NEISO": None}
    a4: dict[str, dict] = {}
    for iso, bundle in KEEPERS.items():
        raw = json.loads((REPO / bundle / "run_config.json").read_text())["scenario_config"]
        flags = {k: raw.get(k) for k in FUEL_FLAGS}
        zf = ZONAL_FLAG.get(iso)
        if zf:
            flags[zf] = raw.get(zf)
        derive = dict(GAS_SERIES_FLAGS.get(iso, {}))
        # A per-plant print in the KEEPER that the DERIVE recipe cannot carry is
        # the exposure: _gas_series is ISO-level by construction, so any keeper
        # flag that reprices units off that series after it is invisible to the
        # anchor.
        per_plant = bool(raw.get("gas_plant_monthly_fuel_pricing"))
        zonal_on = bool(zf and raw.get(zf))
        zonal_anchor_on = bool(raw.get("gas_offer_margin_zonal_anchor"))
        a4[iso] = {
            "keeper_bundle": bundle,
            "margin_armed": bool(raw.get("gas_offer_net_revenue_margin")),
            "registered_anchor": GAS_OFFER_MARGIN_ANCHOR_BY_ISO.get(iso),
            "gas_basis_differential": GAS_BASIS_DIFFERENTIAL.get(iso),
            "derive_recipe": derive,
            "keeper_gas_flags": flags,
            "per_plant_923_pricing": per_plant,
            "zonal_basis_armed": zonal_on,
            "in_ZONAL_BASIS_ISOS": iso in ZONAL_BASIS_ISOS,
            "zonal_anchor_armed": zonal_anchor_on,
            "has_by_zone_registry": iso in GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
            "basis_grain_exposed": bool(
                raw.get("gas_offer_net_revenue_margin") and per_plant
            ),
            "zone_grain_residual": bool(
                raw.get("gas_offer_net_revenue_margin") and zonal_on
                and not zonal_anchor_on
            ),
        }
    rep["A4_cross_iso_exposure"] = {
        "what": "COUNTED from committed artifacts only — GAS_SERIES_FLAGS, GAS_BASIS_DIFFERENTIAL, each keeper's own run_config.json gas flags, the by-zone registry. NO other ISO's fleet is built, NO other ISO's delivered price is measured, NO other ISO's matrix cell is filled (rule 25 [R-ISO-SCOPE]).",
        "criterion": "basis_grain_exposed = the margin is ARMED and the keeper prices the fleet per-plant (gas_plant_monthly_fuel_pricing), which _gas_series cannot carry — so the anchor and the fleet's delivered price are identified on different bases.",
        "isos": a4,
        "n_exposed": sum(1 for v in a4.values() if v["basis_grain_exposed"]),
    }

    # ---- the pre-registered kills ------------------------------------------
    fm, fmed = wmean(pool_fleet_cap), wquantile(pool_fleet_cap, 0.50)
    sq = rep["A2_A3_by_grain"]["a_status_quo_iso_series"]
    max_sq = max(
        (max(abs(v) for v in r["A3_distortion_usd_mwh_by_year"]) for r in sq.values()),
        default=0.0,
    )
    dom: dict[str, dict] = {}
    for metric in ("A3_distortion_usd_mwh_by_year", "A3_rms_usd_mwh_by_year"):
        base_d = {cl: sq[cl][metric] for cl in sq}
        for gname, rows_out in rep["A2_A3_by_grain"].items():
            if gname == "a_status_quo_iso_series":
                continue
            better = worse = 0
            for cl, r in rows_out.items():
                for i in range(len(YEARS)):
                    if r[metric][i] < base_d[cl][i] - 1e-9:
                        better += 1
                    elif r[metric][i] > base_d[cl][i] + 1e-9:
                        worse += 1
            key = "L1" if metric.startswith("A3_distortion") else "L2"
            dom.setdefault(gname, {})[key] = {
                "class_years_improved": better, "class_years_worsened": worse,
                "dominates_status_quo": bool(better > 0 and worse == 0),
            }
    rep["kills"] = {
        "K1_fleet_grain_fine": {
            "window_fleet_cap_w_mean": _r(fm, 4),
            "window_fleet_cap_w_median": _r(fmed, 4),
            "abs_mean_minus_anchor": _r(abs(fm - anchor), 4),
            "abs_median_minus_anchor": _r(abs(fmed - anchor), 4),
            "bar": K1_FLEET_TOL,
            "K1_FIRES": bool(abs(fm - anchor) <= K1_FLEET_TOL
                             and abs(fmed - anchor) <= K1_FLEET_TOL),
        },
        "K2_immaterial": {
            "max_status_quo_distortion_usd_mwh": _r(max_sq, 3),
            "bar": K2_DISTORTION_BAR,
            "K2_FIRES": bool(max_sq < K2_DISTORTION_BAR),
        },
        "K3_no_dominant_grain": {
            "by_grain": dom,
            "note": "L1 is minimized at the weighted MEDIAN and L2 at the weighted MEAN by construction; a grain that dominates on ONE metric only has not been shown to dominate.",
            "K3_FIRES": bool(not any(
                v["L1"]["dominates_status_quo"] and v["L2"]["dominates_status_quo"]
                for v in dom.values()
            )),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=2, sort_keys=False) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for k, v in rep["kills"].items():
        print(f"  {k}: FIRES={[x for x in v if x.endswith('FIRES')] and v[[x for x in v if x.endswith('FIRES')][0]]}")
    print(f"  A-4 exposed ISOs: {rep['A4_cross_iso_exposure']['n_exposed']} of 6")


if __name__ == "__main__":
    main()
