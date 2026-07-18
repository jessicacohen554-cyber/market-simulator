#!/usr/bin/env python3
"""Empirical cross-class offer-curve tuning Jacobian from calibration bundles.

Pure parquet/JSON analysis of existing calibration bundles under
``results/calibration`` — no LP is re-solved. From consecutive run pairs whose
only difference is offer-curve band-multiplier moves ("pure-curve pairs"), it
collects observations Δ(band multiplier vector) → Δ(objective vector) per year
and fits a sparse ridge-regularized linear map

    Δobj[target] ≈ Σ S[target, (out_class, band)] · Δmult[(out_class, band)]

so tuning can solve one joint multi-class move instead of sequential
single-knob walks that whack-a-mole between interrelated classes
(CT_PEAKER committed ↔ ST_GAS, COAL_PRB ↔ COAL_LIGNITE, CC_REGULAR as the
big residual marginal class). Each year is fitted separately — the 2024 vs
2023/2025 asymmetry is gas-price-driven ($2.54 / $2.19 / $3.52 per MMBtu).

Objectives (the "blocks")
-------------------------
The fitted targets and the joint-move objective span three blocks, so a TWh
fix that wrecks the dispatch shape or the price level is visible BEFORE any
LP is solved:

- ``twh``   — annual class TWh (model, BTM-aware) per (year, class). The
  original objective; err = model − EIA-923.
- ``shape`` — hourly dispatch-shape residuals per year: NRMSE of the model's
  hourly non-CHP gas and coal series vs EIA-930 (the report's [5] table
  convention, flat-CHP subtracted from observed gas), plus the mean
  CAMPD CF-band earth-mover distance across the tuning-panel plants
  (``plant_cf_bands.parquet``). err = the metric itself (target 0).
- ``lmp``   — demand-weighted monthly |model − actual RT| price MAE ($/MWh)
  from ``system.parquet``'s hourly zone prices vs the committed
  ``data/raw/_validation-source/actual_lmp.json`` reference (the
  ``scripts/data/derive_actual_lmp.py`` product). err = the MAE (target 0).

The joint-move recipe minimizes a weighted sum of the three blocks
(``--w-twh`` / ``--w-shape`` / ``--w-lmp``), each block normalized by its
magnitude on the ``--baseline`` bundle (default ``e2_4_retune``, the run-79
keeper) so the units are comparable; defaults are balanced. Shape/LMP
sensitivity columns start data-poor (historical pairs moved knobs for TWh
reasons) and are reported with the existing n_obs/stderr confidence flags
rather than hidden; expect the LMP block to act mostly as a guardrail vetoing
price-degrading moves — LMP error is dominated by drivers outside the
offer-curve knobs (gas price path, scarcity pricing).

Trust region
------------
The run-82 recipe wrecked CT_PEAKER (+21/+14/+21%) by extrapolating a knob
far outside its sampled range (committed stacked to a cumulative −0.47 below
the calibrated default and crossed a merit-order step). The recipe now
zeroes any knob whose post-move resolved value (run_config.json's
``offer_curve_by_group``) would land at/beyond the edge of the value range
actually sampled by the pure pairs estimating that knob's column, printing a
"re-derive locally first" warning instead of an extrapolated move. The
per-step |Δmult| ≤ 0.15 cap (``--cap``) still applies on top.

Run pairs that include structural code or data changes (storage fix, plant
appends, BTM trims, fuel-cost re-grounding, demand alignment, heat-rate
re-bases, …) are excluded from the regression via a curated registry below;
unknown future runs are auto-classified from the bundle's
``model_changes_note`` plus a ``git diff`` between the recorded shas when both
are resolvable, so the tool keeps working as new backcasts accrue for any ISO.

Outputs
-------
- ``data/raw/_processed-legacy/offer_curve_jacobian.csv`` (long format: iso, year,
  metric, out_class, band, in_class, dTWh_per_unit_mult, n_obs, stderr,
  confidence). Schema v2: the ``metric`` column is new; filtering
  ``metric == "twh"`` reproduces the v1 content exactly. For ``shape`` rows
  the value column is d(NRMSE or EMD)/d(mult) and ``in_class`` names the
  series (``gas`` / ``coal`` / ``cf_emd``); for ``lmp`` rows it is
  d($/MWh MAE)/d(mult) with ``in_class == "system"``. The column name
  ``dTWh_per_unit_mult`` is kept for backward compatibility.
- printed matrix sorted by |sensitivity| with confidence flags
- merit-order adjacency validation: each class-band's $/MWh offer range
  (band mult × class base HR × monthly fuel price) vs the demand-weighted
  clearing-price distribution in ``system.parquet`` — overlapping ranges are
  the substitution pairs the regression should agree with
- a joint-move recipe: given the latest run's error blocks, solve
  min ‖W·(S·Δm + err)‖² (ridge-regularized, per-step band moves capped at
  ±0.15, trust-region-frozen knobs at 0) and print the recommended Δm with
  the predicted change PER BLOCK
- ``--validate-run RUN`` prints all three error blocks for the named run
- ``--backtest BASE TARGET`` predicts TARGET's per-block changes from BASE's
  config delta through the Jacobian and compares predicted vs actual — the
  regression test for the trust region is
  ``--backtest e2_4_retune run82_jacobian_joint`` flagging the CT_PEAKER
  committed move

Usage
-----
    python scripts/data/derive_offer_curve_jacobian.py                 # all ISOs found
    python scripts/data/derive_offer_curve_jacobian.py --iso ERCOT
    python scripts/data/derive_offer_curve_jacobian.py --include-pair Run-60-prbfix
    python scripts/data/derive_offer_curve_jacobian.py --validate-run Run-73
    python scripts/data/derive_offer_curve_jacobian.py --iso ERCOT \\
        --backtest e2_4_retune run82_jacobian_joint
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402

DEFAULT_ROOT = REPO / "results" / "calibration"
DEFAULT_OUT = REPO / "inputs" / "processed" / "offer_curve_jacobian.csv"
CACHE_PATH = REPO / "inputs" / "processed" / ".offer_curve_jacobian_cache.json"
FUEL_COSTS = REPO / "inputs" / "processed" / "eia923_monthly_fuel_costs.parquet"

# Offer-curve knobs per class as resolved in run_config.json
# scenario_config.offer_curve_by_group. The first four are heat-rate band
# multipliers (the ±0.15 recipe cap applies to these); econ_low_share is a
# fraction and pct_peaking a percent of nameplate — different units, fitted
# and reported but excluded from the joint-move solver.
BANDS = ("committed", "econ_low", "econ_high", "peak", "econ_low_share", "pct_peaking")
PRICE_BANDS = BANDS[:4]

# Objective blocks. "twh" is the original annual-energy objective; "shape"
# and "lmp" are the hourly-dispatch-shape and price-level objectives (see
# module docstring). Default recipe weights are balanced; each block is
# normalized by its baseline-bundle magnitude before weighting.
METRICS = ("twh", "shape", "lmp")

# Upper-case non-CHP gas classes for the EIA-930 gas shape comparison —
# matches run_calibration_full's [5] table (_NONCHP_GAS). Coal classes are
# any klass starting with "COAL".
GAS_NONCHP_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")

# Committed actual-LMP reference produced by scripts/data/derive_actual_lmp.py:
# {"ERCOT": {"2024": {"rt": ..., "rt_mon": [...12...], ...}, ...}, ...}.
ACTUAL_LMP_JSON = REPO / "inputs" / "calibration" / "actual_lmp.json"

# Fixed non-leap dispatch calendar (matches market_sim.data.campd and
# scripts/archive/analyze_lmp_residual.py).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(13))

# ---------------------------------------------------------------------------
# Pair classification registry. Keyed by the *later* run of a consecutive
# pair; a pair inherits the later run's status:
#   pure       — verified offer-curve-only move; regression input.
#   structural — code/data change (possibly alongside curve moves); excluded
#                from the regression, usable only as a qualitative sign check.
#   legacy     — early/exploratory bundles whose provenance was not verified;
#                excluded by default (force with --include-pair).
#   sidecar    — A/B experiment off a mainline run (e.g. a smoothing sweep);
#                removed from the pairing chain entirely so the mainline runs
#                on either side still pair with each other.
# Verification for the entries below: model_changes_note review plus
# `git diff <sha0> <sha1> -- src/ inputs/ data/` between the recorded shas
# (clean for every pure pair; note that several structural changes do NOT
# show in those diffs — storage parquet, ER plant append, BTM trim — so the
# note review is authoritative, not git).
# ---------------------------------------------------------------------------
REGISTRY: dict[str, tuple[str, str]] = {
    # --- ERCOT ---
    "Run46-tuning": ("legacy", "early tuning era, provenance unverified"),
    "run-47-tuning": ("legacy", "early tuning era, provenance unverified"),
    "run-48-tuning": ("legacy", "early tuning era, provenance unverified"),
    "Run-58-tuning": ("legacy", "OTHER-class breakout alongside tuning"),
    "Run-59-Claude-tuning": ("structural", "OTHER-class breakout alongside tuning"),
    "Run-60-prbfix": (
        "legacy",
        "note lists only multiplier moves and git is clean, but predates the "
        "verified candidate window — include explicitly once vetted",
    ),
    "Run-61": ("pure", "multiplier moves only (note + clean git)"),
    "Run-62": ("pure", "multiplier moves only (note + clean git)"),
    "Run-63": (
        "structural",
        "EIA-860 ER storage parquet; 2025 battery fleet 8.05->12.82 GW",
    ),
    "Run-64": (
        "structural",
        "ER plant append + storage 13.7 GW (CC_CHP shape move mixed in)",
    ),
    "Run-65": ("pure", "cross-class rebalance, multipliers only"),
    "Run-66": ("structural", "CHP BTM pull-out trim (supply-side data change)"),
    "Run-67": ("pure", "consolidation of Run-66, multipliers only"),
    "Run-68": ("structural", "measured EIA-923 PRB fuel costs replace flat assumption"),
    "Run-69": (
        "structural",
        "CC_CHP heat-rate re-base to eGRID PLHTRT (custom-bin-assignments.csv)",
    ),
    "Run-70": ("pure", "multiplier moves only on the new HR basis"),
    "Run-71": (
        "structural",
        "2025 demand-alignment fix (curves unchanged from Run-70)",
    ),
    "Run-72": ("pure", "multiplier moves only (note + clean git)"),
    "Run-73": (
        "structural",
        "CHP steam-floor fix + Petra Nova reclassification (curve moves mixed in — sign-check only)",
    ),
    "curve-n12-2024": (
        "sidecar",
        "A/B of offer_curve_smoothing_n off Run-72, single year",
    ),
    "Run-74": (
        "structural",
        "regenerated unit-outage extract (Rio Nogales / C.R. Wing derates) alongside the curve walk-back",
    ),
    # E2 storage family (dashboard runs 75-79). e2_2 precedes e2_1 by
    # timestamp, so the chain order is e2_2 -> e2_1 -> e2_3 -> e2_4.
    "e2_2_adder20": (
        "structural",
        "storage-persistence branch + battery adder 20 probe",
    ),
    "e2_1_storage_base": ("structural", "battery adder 20 -> 0 (scenario change)"),
    "e2_3_adder10": ("structural", "battery adder 0 -> 10 (scenario change)"),
    "e2_4_retune": (
        "pure",
        "coal/CT band re-tune on the adder-10 config (note + same adder as e2_3)",
    ),
    "run80a_code_baseline": (
        "structural",
        "run79 keeper config re-run on post-E3 main (code accumulation baseline; zero curve deltas)",
    ),
    # run80b..run80e are A/B probes off run80a (dashboard runs 80-81), all
    # reverted. Sidecar so run80a still pairs with run82. CAUTION: 80b/80c
    # repriced lignite via a constant outside scenario_config, and 80d/80e
    # PREDATE the --prb-* provenance fix — their run_config.json shows
    # DEFAULT sigmoid params while the true values are in
    # meta/model_changes_note. Never let auto-classification or sigmoid-param
    # reads trust those two run_configs.
    "run80b_lignite_105": (
        "sidecar",
        "lignite flat reprice $1.05 probe off run80a (rejected; reprice not in scenario_config)",
    ),
    "run80c_lignite_115": (
        "sidecar",
        "lignite flat reprice $1.15 probe off run80a (rejected)",
    ),
    "run80d_prb_floor_068": (
        "sidecar",
        "PRB floor 0.68 probe off run80a (rejected; run_config sigmoid params are stale defaults)",
    ),
    "run80e_prb_shaped": (
        "sidecar",
        "PRB sigmoid shape probe off run80a (rejected; run_config sigmoid params are stale defaults)",
    ),
    "run82_jacobian_joint": (
        "pure",
        "Jacobian recipe curve deltas only off run80a (rejected as a keeper but a valid sensitivity observation — incl. CT_PEAKER committed at 1.008)",
    ),
    "run84_coal_sigmoids": (
        "structural",
        "lignite passthrough sigmoid + PRB floor retune (coal sigmoid params, not curve moves)",
    ),
    "run91_cc_shave055": (
        "pure",
        "beta=0.55 dose of the run-90->run-91-full vector: CC_REGULAR econ_high/peak deltas only (note + clean git)",
    ),
    "run92_kiamichi": (
        "structural",
        "Kiamichi fleet fix: missing 1.4 GW CC added to registry + bins (run-91 tuning unchanged)",
    ),
    "run93_jacobian_probe": (
        "pure",
        "CC_REGULAR econ_high -0.40 -> -0.30 only, off run92 on the corrected fleet (the post-Kiamichi re-derivation probe)",
    ),
    # run94/run95 are probes whose chain pairs are structural either way
    # (Kiamichi bins CSV trim in 94, lignite sigmoid floor in 95); sidecar
    # them so run93 pairs with run95b, the corrected-fleet committed step.
    "run94_ct_kiamichi": (
        "sidecar",
        "CT econ_high -0.20 probe + Kiamichi bins trim v1 off the run-92 config (rejected: flips ST_GAS 2025); vector in the runs-93-96 calibration-log section",
    ),
    "run95_lignite_probe": (
        "sidecar",
        "lignite floor 0.69 endpoint + Kiamichi bins v2 probe off run94 (sigmoid param + bins, not curve knobs); vector in the runs-93-96 calibration-log section",
    ),
    "run95b_cc_committed_probe": (
        "pure",
        "vs chain-predecessor run93: CC_REGULAR committed -0.05 -> +0.05 and econ_high -0.30 -> -0.40 (curve moves only; the Kiamichi bins v1 trim between their shas is a measured within-CC ~0.15 TWh perturbation, run-94 note — accepted)",
    ),
    "run96_lignite_keeper": (
        "structural",
        "lignite sigmoid floor 0.75 -> 0.69 keeper (sigmoid param, not a curve knob; offer deltas = run92's)",
    ),
    "run97a_gas_plants": (
        "structural",
        "per-plant bins committed-share edits (Braunig/Sommers) + --btm-backfill-year reporting fix (inputs/data change, no curve knobs)",
    ),
    "run97b_coal_plants": (
        "structural",
        "Parish/Spruce committed-share probe (bins edit, REJECTED; mechanism corrected post-hoc: the P1 coal startup amortization prices the committed band above the econ ramp, so the share shift moved capacity into the startup-bearing band)",
    ),
    "run98a_warm_committed": (
        "structural",
        "--coal-warm-committed exemption probe (code flag, REJECTED: fixes the 2024 coal split but detonates 2023 - committed coal clears both years)",
    ),
    "run98b_warm_parish": (
        "structural",
        "warm exemption + Parish/Spruce committed shares (REJECTED: identical to 98a within noise - share lever redundant once the band clears)",
    ),
    # --- PJM ---
    "pjm_2023": ("legacy", "exploratory era"),
    "pjm_2024": ("legacy", "exploratory era"),
    "pjm_2023_8z_ix": ("legacy", "exploratory era"),
    "pjm_2024_v2": (
        "structural",
        "unit-only outages + grounded tranches + n=6 curve rebase",
    ),
    "pjm_2024_coalclass": ("structural", "EIA-923 coal supply class breakout"),
    "pjm_basis_tune2": ("legacy", "basis-scaling era, provenance unverified"),
    "pjm_n6_tuned": ("legacy", "mix-ratio LMP scaling era"),
    "pjm_tune5_2025": ("structural", "fuller unit-level CAMPD outages"),
    "pjm_2_hydro_ps": (
        "structural",
        "LP budget hydro + pumped storage + OTHER must-run injection",
    ),
    "pjm_3_tune": (
        "structural",
        "PS throughput adder (reserve reduced form) mixed with curve moves",
    ),
    "pjm_4_gasmonthly": ("structural", "measured EIA-923 ISO-monthly delivered gas"),
    "pjm_5_coalcommit": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_6_ccpeak": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_7_ct": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_8_outages": (
        "structural",
        "full-footprint CAMPD outage refresh (curves unchanged)",
    ),
    "pjm_9_chp_solar": ("structural", "CHP steam floors + sector BTM for PJM cogens"),
    # --- NEISO ---
    # P11/P12 era. The P12 keepers are per-year bundles (no year overlap, so
    # they never pair); the probe panel below is the first NEISO tuning data.
    "neiso_smoke_2024": ("structural", "P11 smoke, pre-P12 structural era"),
    "neiso_smoke_2024_priced_ix": (
        "sidecar",
        "--priced-interchange A/B diagnostic off the P11 smoke",
    ),
    "neiso_p12_base_2023": (
        "structural",
        "P12 sign-off keeper, 2023 (structural defaults, zero curve moves)",
    ),
    "neiso_p12_base_2024": (
        "structural",
        "P12 sign-off keeper, 2024 (structural defaults, zero curve moves)",
    ),
    "neiso_p12_hydrofix_2025": (
        "structural",
        "P12 sign-off keeper, 2025 (--hydro-backfill-year 2024)",
    ),
    # Probe panel (2026-06-12): single-knob ±0.05 runs chained off the
    # code-accumulation anchor (P12 keeper config re-run on current main;
    # reproduces neiso_p12_base_2024 to the float — zero NEISO code drift).
    # Each consecutive pair is a verified pure-curve observation.
    "neiso_probe_base_2024": (
        "structural",
        "P12 keeper config re-run on current main (code-accumulation anchor; zero curve deltas)",
    ),
    "neiso_probe_cc_regular_committed_plus": (
        "pure",
        "single knob: CC_REGULAR committed +0.05 off the probe anchor",
    ),
    "neiso_probe_cc_regular_committed_minus": (
        "pure",
        "single knob: CC_REGULAR committed -0.05 (pairs as -0.10 vs the plus probe)",
    ),
    "neiso_probe_cc_regular_econ_high_plus": (
        "pure",
        "single knob: CC_REGULAR econ_high +0.05",
    ),
    "neiso_probe_cc_regular_econ_high_minus": (
        "pure",
        "single knob: CC_REGULAR econ_high -0.05",
    ),
    "neiso_probe_ct_peaker_committed_plus": (
        "pure",
        "single knob: CT_PEAKER committed +0.05",
    ),
    "neiso_probe_ct_peaker_committed_minus": (
        "pure",
        "single knob: CT_PEAKER committed -0.05",
    ),
    "neiso_probe_st_gas_committed_minus": (
        "pure",
        "single knob: ST_GAS committed -0.05 (dual-fuel ST winter coverage)",
    ),
    "neiso_probe_st_gas_peak_minus": (
        "pure",
        "single knob: ST_GAS peak -0.05 (dual-fuel/oil-steam scarcity band)",
    ),
    "neiso_probe_cc_chp_committed_minus": (
        "pure",
        "single knob: CC_CHP committed -0.05 (grid-side CHP share)",
    ),
    "neiso_probe_ct_chp_committed_minus": (
        "pure",
        "single knob: CT_CHP committed -0.05 (grid-side CHP share)",
    ),
    # --- CAISO ---
    # 2026-06-13 probe panel: 11 single-knob ±0.05 band probes chained off a
    # zero-delta code baseline, all 2023-only at the same code state (results
    # bundles committed between runs, so shas advance but src/inputs/data git
    # diffs are clean — auto-classification agrees with every entry below).
    # CAVEAT: the panel ran with the P11 import-tranche mis-pricing OPEN
    # (the node over-imports +114% in 2023), so these sensitivities are
    # conditional on the import stack owning the $45-90 margin: CT_PEAKER and
    # ST_GAS knobs measure ~dead, and 30-50% of every CC_REGULAR band move
    # trades against the import node. Re-probe after the P9/P12 re-price.
    "caiso_probe_base": (
        "structural",
        "code-accumulation baseline off caiso_1_priced_ix (zero curve deltas, 2023 only)",
    ),
    "caiso_probe_cc_regular_committed_minus": (
        "pure",
        "single knob: CC_REGULAR committed -0.05",
    ),
    "caiso_probe_cc_regular_econ_low_minus": (
        "pure",
        "single knob: CC_REGULAR econ_low -0.05 (prior probe reverted)",
    ),
    "caiso_probe_cc_regular_econ_high_minus": (
        "pure",
        "single knob: CC_REGULAR econ_high -0.05",
    ),
    "caiso_probe_cc_regular_peak_minus": (
        "pure",
        "single knob: CC_REGULAR peak -0.05 (measured ~zero response)",
    ),
    "caiso_probe_ct_peaker_committed_minus": (
        "pure",
        "single knob: CT_PEAKER committed -0.05 (measured zero response — import-crowded)",
    ),
    "caiso_probe_ct_peaker_econ_low_minus": (
        "pure",
        "single knob: CT_PEAKER econ_low -0.05",
    ),
    "caiso_probe_st_gas_committed_plus": (
        "pure",
        "single knob: ST_GAS committed +0.05 (measured ~zero response)",
    ),
    "caiso_probe_st_gas_econ_low_plus": ("pure", "single knob: ST_GAS econ_low +0.05"),
    "caiso_probe_cc_chp_committed_minus": (
        "pure",
        "single knob: CC_CHP committed -0.05",
    ),
    "caiso_probe_ct_chp_committed_minus": (
        "pure",
        "single knob: CT_CHP committed -0.05",
    ),
    "caiso_probe_cc_regular_committed_plus": (
        "pure",
        "single knob: CC_REGULAR committed +0.05 (held-out back-test probe; exclude via --exclude-pair to reproduce the validation)",
    ),
    # --- NYISO ---
    # 2026-06-16 probe panel: 10 single-knob ±0.05 band probes chained off a
    # structurally-sound anchor (the P11 smoke's --priced-interchange config,
    # 2023 only). The anchor reproduces the nyiso_smoke_2023 priced diagnostic
    # to the float — 121.75 TWh total, -25.41 TWh net interchange, $40.34 avg —
    # so the import wedge (the P9 structural row) is SERVED before any curve is
    # probed. Gas classes only: NYISO has no coal fleet. Results bundles are
    # committed between runs, so shas advance but src/inputs/data git diffs
    # stay clean — auto-classification agrees with every entry below.
    "nyiso_probe_base_2023": (
        "structural",
        "smoke priced-interchange config re-run on current main (code-accumulation anchor; zero curve deltas, 2023 only)",
    ),
    "nyiso_probe_cc_regular_committed_plus": (
        "pure",
        "single knob: CC_REGULAR committed +0.05 off the probe anchor",
    ),
    "nyiso_probe_cc_regular_committed_minus": (
        "pure",
        "single knob: CC_REGULAR committed -0.05 (pairs as -0.10 vs the plus probe)",
    ),
    "nyiso_probe_cc_regular_econ_high_plus": (
        "pure",
        "single knob: CC_REGULAR econ_high +0.05",
    ),
    "nyiso_probe_cc_regular_econ_high_minus": (
        "pure",
        "single knob: CC_REGULAR econ_high -0.05",
    ),
    "nyiso_probe_ct_peaker_committed_plus": (
        "pure",
        "single knob: CT_PEAKER committed +0.05",
    ),
    "nyiso_probe_ct_peaker_committed_minus": (
        "pure",
        "single knob: CT_PEAKER committed -0.05",
    ),
    "nyiso_probe_st_gas_committed_minus": (
        "pure",
        "single knob: ST_GAS committed -0.05 (dual-fuel ST winter coverage)",
    ),
    "nyiso_probe_st_gas_peak_minus": (
        "pure",
        "single knob: ST_GAS peak -0.05 (dual-fuel/oil-steam scarcity band)",
    ),
    "nyiso_probe_cc_chp_committed_minus": (
        "pure",
        "single knob: CC_CHP committed -0.05 (grid-side CHP share)",
    ),
    "nyiso_probe_ct_chp_committed_minus": (
        "pure",
        "single knob: CT_CHP committed -0.05 (grid-side CHP share)",
    ),
}

# Bundles older than this per-ISO timestamp are "legacy" unless REGISTRY or
# --include-pair says otherwise: the model changed too much since (storage,
# BTM, fuel-cost, demand fixes) for their sensitivities to describe the
# current code. ERCOT's window opens at Run-58 (the verified candidate pairs
# start at Run-60 -> Run-61); PJM's at the pjm_2.. tuning sequence.
ERA_START = {"ERCOT": "2026-06-07", "PJM": "2026-06-09"}

# Words in a model_changes_note that suggest a structural (non-curve) change;
# used only for runs absent from REGISTRY. Matches are case-insensitive.
STRUCTURAL_NOTE_HINTS = (
    "fix",
    "append",
    "reclassif",
    "re-base",
    "rebase",
    "breakout",
    "measured",
    "parquet",
    "refresh",
    "overlay",
    "btm",
    "pull-out",
    "alignment",
    "storage fleet",
    "heat rate",
    "hr basis",
    "steam-floor",
    "outage",
)

# Representative base heat rates (MMBtu/MWh) per class for the merit-order
# adjacency check — midpoints of config.constants.HEAT_RATE_BINS vintages.
# Approximate by design: the check is qualitative (which bands share a price
# range), not quantitative.
CLASS_BASE_HR = {
    "CC_REGULAR": 7.0,
    "CC_CHP": 7.0,
    "CT_PEAKER": 10.5,
    "CT_CHP": 10.0,
    "ST_GAS": 10.4,
    "ST_CHP": 10.4,
    "COAL_LIGNITE": 10.4,
    "COAL_PRB": 10.4,
    "COAL_BIT": 10.0,
    "COAL_SUB": 10.2,
    "COAL_WC": 10.8,
    "COAL": 10.2,
}
ISO_STATES = {
    "ERCOT": {"TX"},
    "PJM": {
        "PA",
        "NJ",
        "MD",
        "DE",
        "OH",
        "WV",
        "VA",
        "KY",
        "IL",
        "IN",
        "MI",
        "NC",
        "TN",
        "DC",
    },
    "NEISO": {"CT", "MA", "ME", "NH", "RI", "VT"},
    "CAISO": {"CA"},
    "NYISO": {"NY"},
}


@dataclass
class Bundle:
    name: str
    path: Path
    iso: str
    timestamp: str
    years: list[int]
    curves: dict[str, dict[str, float]]
    note: str
    sha: str
    scenario: dict = field(default_factory=dict, repr=False)
    totals: pd.DataFrame | None = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Discovery + class totals
# ---------------------------------------------------------------------------


def discover_bundles(root: Path) -> list[Bundle]:
    """All bundles under root with resolved curves and dispatch parquet."""
    out = []
    for d in sorted(root.iterdir()):
        cfg_path = d / "run_config.json"
        if not d.is_dir() or not cfg_path.exists():
            continue
        try:
            cfg = json.loads(cfg_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        sc = cfg.get("scenario_config", {})
        curves = sc.get("offer_curve_by_group") or {}
        disp = sorted((d / "dispatch").glob("*_P1.parquet"))
        if not curves or not disp or bundle_input_path(d, "eia923") is None:
            continue
        meta = {}
        if (d / "meta.json").exists():
            try:
                meta = json.loads((d / "meta.json").read_text())
            except (json.JSONDecodeError, OSError):
                pass
        git = cfg.get("git") or {}
        out.append(
            Bundle(
                name=d.name,
                path=d,
                iso=meta.get("iso") or sc.get("iso") or "?",
                timestamp=meta.get("timestamp") or cfg.get("timestamp") or "",
                years=sorted(int(f.name.split("_")[0]) for f in disp),
                curves=curves,
                note=str(cfg.get("model_changes_note") or ""),
                sha=git.get("sha") or meta.get("git_sha") or "",
                scenario={k: v for k, v in sc.items() if k != "offer_curve_by_group"},
            )
        )
    return sorted(out, key=lambda b: b.timestamp)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def class_totals(b: Bundle, cache: dict) -> pd.DataFrame:
    """Per (year, klass): model TWh (grid + BTM add-back) and EIA-923 TWh.

    Mirrors scripts/archive/compare_runs_classes.py. Thermal response classes are the
    upper-case klass values in dispatch (excluding OTHER). Bundles without
    btm.parquet (older PJM format) get btm_twh=0 — pair deltas stay valid as
    long as BTM config didn't change inside the pair, which pure pairs satisfy.
    """
    if b.totals is not None:
        return b.totals
    stamp = {
        f.name: [f.stat().st_mtime, f.stat().st_size]
        for f in sorted((b.path / "dispatch").glob("*_P1.parquet"))
    }
    ent = cache.get(b.name)
    if ent and ent.get("stamp") == stamp:
        b.totals = pd.DataFrame(ent["rows"])
        return b.totals

    e923 = pd.read_parquet(bundle_input_path(b.path, "eia923"))
    btm_path = b.path / "btm.parquet"
    btm = pd.read_parquet(btm_path) if btm_path.exists() else None
    rows = []
    for f in sorted((b.path / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass", observed=True)["mw"].sum() / 1e6
        bt = {}
        if btm is not None:
            sl = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
            bt = dict(zip(sl["klass"], sl["btm_twh"]))
        bench = (
            e923[e923["year"] == year]
            .groupby("klass", observed=True)["annual_mwh"]
            .sum()
            / 1e6
        )
        klasses = sorted(
            k
            for k in grid.index
            if isinstance(k, str) and k == k.upper() and k != "OTHER"
        )
        for k in klasses:
            rows.append(
                {
                    "year": year,
                    "klass": k,
                    "model_twh": float(grid.get(k, 0.0)) + float(bt.get(k, 0.0)),
                    "eia_twh": float(bench.get(k, 0.0)),
                }
            )
    b.totals = pd.DataFrame(rows)
    ent = cache.setdefault(b.name, {})
    ent["stamp"], ent["rows"] = stamp, rows
    return b.totals


# ---------------------------------------------------------------------------
# Shape + LMP metrics (the non-TWh objective blocks)
# ---------------------------------------------------------------------------


def _nrmse(model: np.ndarray, obs: np.ndarray) -> float:
    denom = float(np.mean(obs))
    if denom <= 0:
        return float("nan")
    return float(np.sqrt(np.mean((model - obs) ** 2)) / denom)


def _hourly_class_sum(disp: pd.DataFrame, mask: pd.Series, T: int) -> np.ndarray:
    s = disp[mask].groupby("hour", observed=True)["mw"].sum()
    return s.reindex(range(T), fill_value=0.0).to_numpy(dtype=float)


def _shape_rows(
    b: Bundle, year: int, disp: pd.DataFrame, e930: pd.DataFrame | None
) -> list[dict]:
    """NRMSE of hourly non-CHP gas / coal vs EIA-930 ([5] table convention)."""
    if e930 is None:
        return []
    ey = e930[e930["year"] == year]
    if ey.empty:
        return []
    obs = {
        s: g.sort_values("hour")["mw"].to_numpy(dtype=float)
        for s, g in ey.groupby("series")
        if s in ("gas", "coal")
    }
    if "gas" not in obs or "coal" not in obs:
        return []
    T = min(int(disp["hour"].max()) + 1, obs["gas"].shape[0])
    klass = disp["klass"].astype(str)
    gas_m = _hourly_class_sum(disp, klass.isin(GAS_NONCHP_CLASSES), T)
    coal_m = _hourly_class_sum(disp, klass.str.startswith("COAL"), T)
    # Observed 930 gas includes CHP; the model compares non-CHP gas, so the
    # CHP grid energy comes off the observed series as a flat block (exactly
    # the report's [5] convention).
    chp_mwh = float(disp.loc[klass.str.endswith("_CHP"), "mw"].sum())
    rows = [
        {
            "year": year,
            "metric": "shape",
            "key": "gas",
            "value": _nrmse(gas_m, obs["gas"][:T] - chp_mwh / T),
        },
        {
            "year": year,
            "metric": "shape",
            "key": "coal",
            "value": _nrmse(coal_m, obs["coal"][:T]),
        },
    ]
    return [r for r in rows if np.isfinite(r["value"])]


def _cf_emd_rows(b: Bundle) -> list[dict]:
    """Mean CAMPD CF-band earth-mover distance across the panel plants.

    ``plant_cf_bands.parquet`` holds, per (year, plant), the model and CAMPD
    hour counts in 10%-of-capacity CF bands. EMD between the two normalized
    histograms = Σ|cumdiff| × band width — the report's [7b] cf_emd.
    """
    p = b.path / "plant_cf_bands.parquet"
    if not p.exists():
        return []
    bands = pd.read_parquet(p)
    if "pass" in bands.columns:
        bands = bands[bands["pass"] == "P1"]
    rows = []
    for year, gy in bands.groupby("year"):
        emds = []
        for _, gp in gy.groupby("plant_code"):
            gp = gp.sort_values("cf_lo")
            m, c = gp["model_hours"].to_numpy(float), gp["campd_hours"].to_numpy(float)
            if m.sum() <= 0 or c.sum() <= 0:
                continue
            width = float((gp["cf_hi"] - gp["cf_lo"]).mean())
            emds.append(np.abs(np.cumsum(m / m.sum() - c / c.sum())).sum() * width)
        if emds:
            rows.append(
                {
                    "year": int(year),
                    "metric": "shape",
                    "key": "cf_emd",
                    "value": float(np.mean(emds)),
                }
            )
    return rows


def _lmp_rows(b: Bundle) -> list[dict]:
    """Demand-weighted monthly |model − actual RT| MAE ($/MWh) per year.

    Model: hourly demand-weighted system price from ``system.parquet`` (P1),
    aggregated to demand-weighted monthly means on the fixed non-leap
    calendar. Actual: the ISO's ``rt_mon`` series in actual_lmp.json.
    """
    if not ACTUAL_LMP_JSON.exists() or not (b.path / "system.parquet").exists():
        return []
    actual_all = json.loads(ACTUAL_LMP_JSON.read_text()).get(b.iso) or {}
    sy = pd.read_parquet(
        b.path / "system.parquet", columns=["year", "pass", "hour", "price", "demand"]
    )
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    rows = []
    for year, g in sy.groupby("year"):
        act = (actual_all.get(str(int(year))) or {}).get("rt_mon")
        if not act:
            continue
        month = np.searchsorted(
            _MONTH_START_HOUR, g["hour"].to_numpy(), side="right"
        ).clip(1, 12)
        gm = (
            g.assign(month=month, pd_=g["price"] * g["demand"])
            .groupby("month")
            .agg(pd_=("pd_", "sum"), d=("demand", "sum"))
        )
        gm["model"] = np.where(gm["d"] > 0, gm["pd_"] / gm["d"], np.nan)
        num = den = 0.0
        for m, r in gm.iterrows():
            a = act[int(m) - 1] if int(m) <= len(act) else None
            if a is None or not np.isfinite(r["model"]):
                continue
            num += r["d"] * abs(r["model"] - a)
            den += r["d"]
        if den > 0:
            rows.append(
                {
                    "year": int(year),
                    "metric": "lmp",
                    "key": "system",
                    "value": num / den,
                }
            )
    return rows


def bundle_metrics(b: Bundle, cache: dict) -> pd.DataFrame:
    """Shape + LMP metric values per year (columns: year, metric, key, value).

    Pure parquet/JSON reads, cached on the source files' stamps. Bundles
    missing an input (old PJM format without plant_cf_bands, ISOs without an
    actual-LMP reference) simply contribute fewer rows; pair deltas are
    formed only over metrics both ends report.
    """
    files = sorted((b.path / "dispatch").glob("*_P1.parquet")) + [
        p
        for p in (
            b.path / "eia930.parquet",
            b.path / "system.parquet",
            b.path / "plant_cf_bands.parquet",
        )
        if p.exists()
    ]
    stamp = {f.name: [f.stat().st_mtime, f.stat().st_size] for f in files}
    ent = cache.get(b.name, {}).get("metrics")
    if ent and ent.get("stamp") == stamp:
        return pd.DataFrame(ent["rows"], columns=["year", "metric", "key", "value"])
    _e930p = bundle_input_path(b.path, "eia930")
    e930 = pd.read_parquet(_e930p) if _e930p is not None else None
    rows: list[dict] = []
    for f in sorted((b.path / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "hour", "mw"])
        rows += _shape_rows(b, int(disp["year"].iloc[0]), disp, e930)
    rows += _cf_emd_rows(b)
    rows += _lmp_rows(b)
    cache.setdefault(b.name, {})["metrics"] = {"stamp": stamp, "rows": rows}
    return pd.DataFrame(rows, columns=["year", "metric", "key", "value"])


def metric_values(b: Bundle, cache: dict) -> pd.Series:
    """All objective values, indexed by (year, metric, key).

    twh entries hold the model TWh per class (deltas across a pair are
    Δgeneration); shape/lmp entries hold the residual metric itself.
    """
    t = class_totals(b, cache)
    rows = {(int(r.year), "twh", r.klass): r.model_twh for r in t.itertuples()}
    for r in bundle_metrics(b, cache).itertuples():
        rows[(int(r.year), r.metric, r.key)] = r.value
    idx = pd.MultiIndex.from_tuples(rows.keys(), names=["year", "metric", "key"])
    return pd.Series(list(rows.values()), index=idx, dtype=float)


def error_blocks(b: Bundle, cache: dict) -> pd.DataFrame:
    """Error vector rows [year, metric, key, err] for the recipe target.

    twh: model − EIA-923 (TWh). shape/lmp: the residual metric (target 0).
    """
    t = class_totals(b, cache)
    rows = [
        {
            "year": int(r.year),
            "metric": "twh",
            "key": r.klass,
            "err": r.model_twh - r.eia_twh,
        }
        for r in t.itertuples()
    ]
    rows += [
        {"year": int(r.year), "metric": r.metric, "key": r.key, "err": r.value}
        for r in bundle_metrics(b, cache).itertuples()
    ]
    return pd.DataFrame(rows)


def block_scales(baseline: Bundle, cache: dict) -> dict[str, float]:
    """RMS error magnitude per block on the baseline bundle (normalizers)."""
    err = error_blocks(baseline, cache)
    out = {}
    for m in METRICS:
        v = err.loc[err["metric"] == m, "err"].to_numpy(float)
        v = v[np.isfinite(v)]
        out[m] = float(np.sqrt(np.mean(v**2))) if v.size else 1.0
        if out[m] <= 0:
            out[m] = 1.0
    return out


# ---------------------------------------------------------------------------
# Pair classification
# ---------------------------------------------------------------------------


def _git_pair_dirty(sha0: str, sha1: str) -> bool | None:
    """True if src/inputs/data differ between the shas; None if unresolvable."""
    if not sha0 or not sha1:
        return None
    if sha0 == sha1:
        return False
    try:
        r = subprocess.run(
            ["git", "diff", "--quiet", sha0, sha1, "--", "src/", "inputs/", "data/"],
            cwd=REPO,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode in (0, 1):
        return r.returncode == 1
    return None  # sha not in local history


_SC_DEFAULTS: dict | None = None


def _scenario_defaults() -> dict:
    """Current ScenarioConfig defaults, JSON-roundtripped like run_config.

    Used to ignore key-presence-only config diffs: a field added to
    ScenarioConfig between two runs shows up only in the newer bundle's
    recorded config, but if its value there equals the (inert) dataclass
    default the dispatch math was identical — e.g. run80a (predates the bit
    sigmoid fields) vs run82 (records coal_bit_* defaults, sigmoid off).
    Import failure degrades to {} — every presence diff then counts, which
    only ever downgrades a pair (safe direction).
    """
    global _SC_DEFAULTS
    if _SC_DEFAULTS is None:
        try:
            import dataclasses

            sys.path.insert(0, str(REPO / "src"))
            from market_sim.config.scenarios import ScenarioConfig

            _SC_DEFAULTS = json.loads(
                json.dumps(dataclasses.asdict(ScenarioConfig()), default=str)
            )
        except Exception:
            _SC_DEFAULTS = {}
    return _SC_DEFAULTS


def _config_diff(b0: Bundle, b1: Bundle) -> list[str]:
    """scenario_config keys (curves excluded) that differ inside the pair.

    Keys present on only one side are benign when the present value equals
    the current ScenarioConfig default (a field added/removed across code
    versions with an inert default); anything else differs for real.
    """
    missing = object()
    defaults = _scenario_defaults()
    out = []
    for k in set(b0.scenario) | set(b1.scenario):
        v0 = b0.scenario.get(k, missing)
        v1 = b1.scenario.get(k, missing)
        if v0 == v1:
            continue
        if v0 is missing or v1 is missing:
            present = v1 if v0 is missing else v0
            if k in defaults and present == defaults[k]:
                continue
        out.append(k)
    return sorted(out)


def classify_pair(b0: Bundle, b1: Bundle) -> tuple[str, str]:
    """(status, reason) for the consecutive pair b0->b1."""
    cfg_diff = _config_diff(b0, b1)
    if b1.name in REGISTRY:
        status, reason = REGISTRY[b1.name]
        if status == "pure" and cfg_diff:
            return (
                "structural",
                f"registry says pure but scenario_config differs "
                f"({', '.join(cfg_diff[:4])}) — downgraded",
            )
        return status, reason
    era = ERA_START.get(b1.iso)
    if era and b1.timestamp < era:
        return (
            "legacy",
            f"predates {b1.iso} analysis era ({era}) — model has since "
            "changed structurally",
        )
    # Unknown (future) run: scenario-config equality + git diff + note hints.
    if cfg_diff:
        return (
            "structural",
            f"auto: scenario_config differs ({', '.join(cfg_diff[:4])})",
        )
    dirty = _git_pair_dirty(b0.sha, b1.sha)
    hinted = [w for w in STRUCTURAL_NOTE_HINTS if w in b1.note.lower()]
    if dirty:
        return "structural", "auto: src/inputs/data differ between run shas"
    if hinted:
        return (
            "legacy",
            f"auto: note hints structural ({', '.join(hinted[:3])}) — "
            "add to REGISTRY after review",
        )
    if dirty is False:
        return (
            "pure",
            "auto: scenario_config identical, clean git diff, no structural note hints",
        )
    return ("legacy", "auto: shas unresolvable and note inconclusive — add to REGISTRY")


@dataclass
class PairObs:
    b0: Bundle
    b1: Bundle
    status: str
    reason: str
    dmult: dict[tuple[str, str], float] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"{self.b0.name} -> {self.b1.name}"


def curve_deltas(b0: Bundle, b1: Bundle, klasses: set[str]) -> dict:
    """{(class, band): Δmult} for classes actually present in dispatch."""
    out = {}
    for cls in sorted(set(b0.curves) & set(b1.curves) & klasses):
        for band in BANDS:
            v0, v1 = b0.curves[cls].get(band), b1.curves[cls].get(band)
            if v0 is None or v1 is None:
                continue
            d = round(float(v1) - float(v0), 6)
            if abs(d) > 1e-9:
                out[(cls, band)] = d
    return out


def build_pairs(
    bundles: list[Bundle], cache: dict, include: set[str], exclude: set[str]
) -> list[PairObs]:
    side = [b for b in bundles if REGISTRY.get(b.name, ("",))[0] == "sidecar"]
    for b in side:
        print(
            f"  [sidecar   ] {b.name}: {REGISTRY[b.name][1]} — "
            "skipped from the pairing chain"
        )
    bundles = [b for b in bundles if b not in side]
    pairs = []
    for b0, b1 in zip(bundles, bundles[1:]):
        if not set(b0.years) & set(b1.years):
            continue
        status, reason = classify_pair(b0, b1)
        if b1.name in include:
            status, reason = "pure", "forced via --include-pair"
        if b1.name in exclude:
            status, reason = "structural", "forced via --exclude-pair"
        p = PairObs(b0, b1, status, reason)
        if status in ("pure", "structural"):
            klasses = set(class_totals(b1, cache)["klass"])
            p.dmult = curve_deltas(b0, b1, klasses)
        pairs.append(p)
    return pairs


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def _ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> np.ndarray:
    """B (n_knobs × n_classes) minimizing ‖XB−Y‖² + λ‖B‖², λ trace-scaled."""
    lam = alpha * float(np.trace(X.T @ X)) / max(X.shape[1], 1)
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)


def fit_year(
    pairs: list[PairObs],
    knobs: list[tuple[str, str]],
    targets: list[tuple[str, str]],
    year: int,
    alpha: float,
    deltas: dict[str, pd.Series],
) -> pd.DataFrame:
    """Long-format S for one year, with jackknife stderr per cell.

    ``targets`` are (metric, key) pairs — ("twh", klass) plus shape/lmp
    entries. Each target column is fitted on the pairs where both bundle
    ends report the metric for this year, so a missing parquet in an old
    bundle shrinks that column's n_obs instead of poisoning the fit.
    """
    rows_x, rows_y = [], []
    for p in pairs:
        d = deltas[p.label]
        rows_x.append([p.dmult.get(k, 0.0) for k in knobs])
        rows_y.append([d.get((year, m, key), np.nan) for (m, key) in targets])
    if not rows_x:
        return pd.DataFrame()
    X, Y = np.array(rows_x), np.array(rows_y)

    rows = []
    for j, (metric, key) in enumerate(targets):
        ok = np.isfinite(Y[:, j])
        if not ok.any():
            continue
        Xj, yj = X[ok], Y[ok, j : j + 1]
        coefs = _ridge(Xj, yj, alpha)[:, 0]
        n = int(ok.sum())
        if n > 2:  # leave-one-pair-out jackknife
            Bs = np.stack(
                [
                    _ridge(np.delete(Xj, i, 0), np.delete(yj, i, 0), alpha)[:, 0]
                    for i in range(n)
                ]
            )
            se = np.sqrt((n - 1) / n * ((Bs - Bs.mean(0)) ** 2).sum(0))
        else:
            se = np.full(len(knobs), np.nan)
        n_obs = (np.abs(Xj) > 1e-9).sum(0)
        for i, (cls, band) in enumerate(knobs):
            coef, s = float(coefs[i]), float(se[i])
            if n_obs[i] >= 3 and np.isfinite(s) and abs(coef) > 2 * s:
                conf = "high"
            elif n_obs[i] >= 2 and (not np.isfinite(s) or abs(coef) > s):
                conf = "med"
            else:
                conf = "low"
            rows.append(
                {
                    "year": year,
                    "metric": metric,
                    "out_class": cls,
                    "band": band,
                    "in_class": key,
                    "dTWh_per_unit_mult": round(coef, 6),
                    "n_obs": int(n_obs[i]),
                    "stderr": round(s, 6) if np.isfinite(s) else None,
                    "confidence": conf,
                }
            )
    return pd.DataFrame(rows)


def fit_iso(pairs: list[PairObs], alpha: float, cache: dict) -> pd.DataFrame:
    pure = [p for p in pairs if p.status == "pure" and p.dmult]
    if not pure:
        return pd.DataFrame()
    knobs = sorted({k for p in pure for k in p.dmult})
    years = sorted({y for p in pure for y in set(p.b0.years) & set(p.b1.years)})
    deltas: dict[str, pd.Series] = {}
    targets: set[tuple[str, str]] = set()
    for p in pure:
        v0, v1 = metric_values(p.b0, cache), metric_values(p.b1, cache)
        common = v0.index.intersection(v1.index)
        deltas[p.label] = v1[common] - v0[common]
        targets |= {(m, k) for (_, m, k) in common}
    targets = sorted(targets)
    return pd.concat(
        [fit_year(pure, knobs, targets, y, alpha, deltas) for y in years],
        ignore_index=True,
    )


# ---------------------------------------------------------------------------
# Sanity anchors (ERCOT Run-72 -> Run-73; structural pair, sign check only)
# ---------------------------------------------------------------------------


def check_anchors(bundles: dict[str, Bundle], cache: dict) -> None:
    b0, b1 = bundles.get("Run-72"), bundles.get("Run-73")
    if not (b0 and b1):
        return
    t0 = class_totals(b0, cache).set_index(["year", "klass"])["model_twh"]
    t1 = class_totals(b1, cache).set_index(["year", "klass"])["model_twh"]
    d = (t1 - t0).round(2)
    print(
        "\n--- Sanity anchors: Run-72 -> Run-73 (structural pair — "
        "qualitative sign checks only) ---"
    )
    checks = [
        (
            "CT_PEAKER committed 1.30->1.10 lifts CT_PEAKER (expect ~+1.6/+2.1/+1.4)",
            [d.get((y, "CT_PEAKER"), 0) > 0 for y in (2023, 2024, 2025)],
        ),
        (
            "ST_GAS falls nearly 1:1 (expect ~-1.7/-2.4/-2.0)",
            [d.get((y, "ST_GAS"), 0) < 0 for y in (2023, 2024, 2025)],
        ),
        (
            "COAL_PRB committed/econ_low -0.10 lifts PRB (expect ~+0.7/+1.3 in 2023/24)",
            [d.get((y, "COAL_PRB"), 0) > 0 for y in (2023, 2024)],
        ),
        (
            "COAL_LIGNITE falls (expect ~-0.7/-0.9 in 2023/24)",
            [d.get((y, "COAL_LIGNITE"), 0) < 0 for y in (2023, 2024)],
        ),
    ]
    for label, oks in checks:
        print(f"  [{'PASS' if all(oks) else 'FAIL'}] {label}")
    for cls in ("CT_PEAKER", "ST_GAS", "COAL_PRB", "COAL_LIGNITE"):
        vals = [d.get((y, cls)) for y in (2023, 2024, 2025)]
        print(
            f"    {cls:<14} ΔTWh 23/24/25: "
            + " / ".join("n/a" if v is None else f"{v:+.2f}" for v in vals)
        )


# ---------------------------------------------------------------------------
# Merit-order adjacency validation
# ---------------------------------------------------------------------------


def monthly_fuel_prices(iso: str, year: int) -> dict[str, tuple[float, float]]:
    """{fuel_group: (min, max) quantity-weighted monthly $/MMBtu} for the ISO."""
    if not FUEL_COSTS.exists():
        return {}
    df = pd.read_parquet(FUEL_COSTS)
    df = df[df["year"] == year]
    states = ISO_STATES.get(iso)
    if states:
        df = df[df["state"].isin(states)]
    out = {}
    for fuel, g in df.groupby("fuel_group"):
        m = g.groupby("month").apply(
            lambda x: (
                np.average(x["price_per_mmbtu"], weights=x["quantity"])
                if x["quantity"].sum()
                else x["price_per_mmbtu"].mean()
            ),
            include_groups=False,
        )
        if len(m):
            out[fuel] = (float(m.min()), float(m.max()))
    return out


def band_offer_ranges(b: Bundle, year: int, klasses: list[str]) -> pd.DataFrame:
    """$/MWh offer range per class-band: mult × base HR × monthly fuel price."""
    fuel = monthly_fuel_prices(b.iso, year)
    rows = []
    for cls in klasses:
        curve, hr = b.curves.get(cls), CLASS_BASE_HR.get(cls)
        if not curve or not hr:
            continue
        grp = "Coal" if cls.startswith("COAL") else "Natural Gas"
        if grp not in fuel:
            continue
        pmin, pmax = fuel[grp]
        for band in PRICE_BANDS:
            mult = curve.get(band)
            if mult is None:
                continue
            rows.append(
                {
                    "class": cls,
                    "band": band,
                    "lo": round(mult * hr * pmin, 2),
                    "hi": round(mult * hr * pmax, 2),
                }
            )
    return pd.DataFrame(rows)


def price_mass(b: Bundle, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted hourly clearing prices + weights from system.parquet."""
    sysp = pd.read_parquet(
        b.path / "system.parquet", columns=["year", "pass", "price", "demand"]
    )
    sysp = sysp[(sysp["year"] == year) & (sysp["pass"] == "P1")]
    return sysp["price"].to_numpy(), sysp["demand"].to_numpy()


def adjacency_check(b: Bundle, S: pd.DataFrame, cache: dict) -> None:
    """Merit-order adjacency from one bundle vs the regression's couplings."""
    klasses = sorted(class_totals(b, cache)["klass"].unique())
    for year in b.years:
        ranges = band_offer_ranges(b, year, klasses)
        if ranges.empty:
            print(f"\n  {b.iso} {year}: no fuel-price data — adjacency check skipped")
            continue
        prices, w = price_mass(b, year)
        wtot = w.sum()
        ranges["price_mass_%"] = [
            round(100 * w[(prices >= lo) & (prices <= hi)].sum() / wtot, 1)
            for lo, hi in zip(ranges["lo"], ranges["hi"])
        ]
        q = np.quantile(prices, [0.05, 0.25, 0.5, 0.75, 0.95])
        print(
            f"\n  {b.iso} {year} clearing price P5/P25/P50/P75/P95: "
            + " / ".join(f"${v:.0f}" for v in q)
        )
        print(
            "  Class-band offer ranges ($/MWh, mult × base HR × monthly "
            "fuel price) and share of demand-weighted hours priced inside:"
        )
        print(ranges.to_string(index=False, col_space=8).replace("\n", "\n    "))

        # Substitution pairs: class-bands of different classes whose offer
        # ranges overlap where the price distribution actually has mass.
        adj: dict[tuple[str, str], float] = {}
        rec = ranges.to_dict("records")
        for i, a in enumerate(rec):
            for c in rec[i + 1 :]:
                if a["class"] == c["class"]:
                    continue
                lo, hi = max(a["lo"], c["lo"]), min(a["hi"], c["hi"])
                if lo >= hi:
                    continue
                mass = 100 * w[(prices >= lo) & (prices <= hi)].sum() / wtot
                key = tuple(sorted((a["class"], c["class"])))
                adj[key] = max(adj.get(key, 0.0), mass)
        top = sorted(adj.items(), key=lambda kv: -kv[1])[:10]
        print(
            "  Top merit-order adjacencies (max overlap mass, % of "
            "demand-weighted hours):"
        )
        for (a, c), mass in top:
            print(f"    {a:<14} <-> {c:<14} {mass:5.1f}%")

        if S.empty:
            continue
        cross = S[
            (S["year"] == year)
            & (S["metric"] == "twh")
            & (S["out_class"] != S["in_class"])
            & (S["confidence"] != "low")
        ]
        cross = cross.reindex(
            cross["dTWh_per_unit_mult"].abs().sort_values(ascending=False).index
        ).head(10)
        print("  Regression cross-couplings vs adjacency:")
        for _, r in cross.iterrows():
            key = tuple(sorted((r["out_class"], r["in_class"])))
            mass = adj.get(key, 0.0)
            verdict = "consistent" if mass > 1.0 else "REVIEW (no price overlap)"
            print(
                f"    {r['out_class']}.{r['band']} -> {r['in_class']}: "
                f"{r['dTWh_per_unit_mult']:+.2f} TWh/unit "
                f"[{r['confidence']}] — adjacency {mass:.1f}% -> {verdict}"
            )


# ---------------------------------------------------------------------------
# Trust region
# ---------------------------------------------------------------------------


def knob_sampled_ranges(
    pairs: list[PairObs],
    exclude: frozenset[str] = frozenset(),
) -> dict[tuple[str, str], tuple[float, float]]:
    """{(class, band): (lo, hi)} resolved-value range sampled by pure pairs.

    Only pairs where the knob actually moved contribute (both endpoints'
    resolved values). ``exclude`` drops pairs touching the named bundles —
    used by the back-test so the target run can't vouch for its own move.
    """
    rng: dict[tuple[str, str], tuple[float, float]] = {}
    for p in pairs:
        if p.status != "pure" or not p.dmult:
            continue
        if {p.b0.name, p.b1.name} & exclude:
            continue
        for cls, band in p.dmult:
            for bnd in (p.b0, p.b1):
                v = (bnd.curves.get(cls) or {}).get(band)
                if v is None:
                    continue
                lo, hi = rng.get((cls, band), (float(v), float(v)))
                rng[(cls, band)] = (min(lo, float(v)), max(hi, float(v)))
    return rng


def trust_region_violations(
    dm: pd.Series,
    resolved: dict[str, dict[str, float]],
    ranges: dict[tuple[str, str], tuple[float, float]],
    tol: float = 1e-9,
) -> dict[tuple[str, str], str]:
    """Knobs whose post-move resolved value exits the sampled range.

    A step that lands at/beyond the edge of the values the pure pairs
    actually sampled is an extrapolation — the run-82 failure mode — and is
    reported for zeroing rather than trusted.
    """
    out = {}
    for (cls, band), step in dm.items():
        if abs(step) <= tol:
            continue
        v = (resolved.get(cls) or {}).get(band)
        if v is None:
            continue
        lo, hi = ranges.get((cls, band), (float("nan"),) * 2)
        if not np.isfinite(lo):
            out[(cls, band)] = "knob never sampled by a pure pair"
            continue
        post = float(v) + float(step)
        if post < lo - tol or post > hi + tol:
            out[(cls, band)] = (
                f"post-move {post:.3f} exits sampled range "
                f"[{lo:.3f}, {hi:.3f}] (current {v:.3f})"
            )
    return out


# ---------------------------------------------------------------------------
# Joint-move recipe (multi-objective)
# ---------------------------------------------------------------------------


def _recipe_system(
    S: pd.DataFrame,
    err: pd.DataFrame,
    weights: dict[str, float],
    scales: dict[str, float],
    min_obs: int,
):
    """Assemble the weighted least-squares system across all blocks.

    Returns (knobs, rows, A, b, w) — A·Δm + b is the predicted error per
    row in native units; w is each row's weight (block weight / block
    scale), applied inside the solver only.
    """
    S = S[(S["band"].isin(PRICE_BANDS)) & (S["n_obs"] >= min_obs)]
    if S.empty:
        return None
    knobs = sorted({(r.out_class, r.band) for r in S.itertuples()})
    coef = S.set_index(["year", "metric", "in_class", "out_class", "band"])[
        "dTWh_per_unit_mult"
    ]
    sk = set(zip(S["year"], S["metric"], S["in_class"]))
    err = err[[(r.year, r.metric, r.key) in sk for r in err.itertuples()]]
    err = err[np.isfinite(err["err"])]
    if err.empty:
        return None
    rows = [(int(r.year), r.metric, r.key) for r in err.itertuples()]
    A = np.array(
        [[coef.get((y, m, k, c, bnd), 0.0) for (c, bnd) in knobs] for (y, m, k) in rows]
    )
    b = err["err"].to_numpy(float)
    w = np.array([weights.get(m, 1.0) / scales.get(m, 1.0) for (_, m, _) in rows])
    return knobs, rows, A, b, w


def _solve_box(
    A: np.ndarray,
    b: np.ndarray,
    w: np.ndarray,
    ridge: float,
    lo: np.ndarray,
    hi: np.ndarray,
) -> np.ndarray:
    """min ‖w·(A·x + b)‖² + λ‖x‖² s.t. lo ≤ x ≤ hi (projected gradient)."""
    Aw, bw = A * w[:, None], b * w
    lam = ridge * float(np.trace(Aw.T @ Aw)) / max(A.shape[1], 1)
    L = float(np.linalg.norm(Aw, 2) ** 2 + lam)
    if L <= 0:
        return np.zeros(A.shape[1])
    x = np.zeros(A.shape[1])
    for _ in range(5000):
        x = np.clip(x - (Aw.T @ (Aw @ x + bw) + lam * x) / L, lo, hi)
    return x


def _block_rms(rows: list[tuple], v: np.ndarray) -> dict[str, float]:
    out = {}
    for m in METRICS:
        sel = np.array([r[1] == m for r in rows])
        if sel.any():
            out[m] = float(np.sqrt(np.mean(v[sel] ** 2)))
    return out


def solve_joint_move(
    S: pd.DataFrame,
    err: pd.DataFrame,
    weights: dict[str, float],
    scales: dict[str, float],
    resolved: dict[str, dict[str, float]],
    ranges: dict[tuple[str, str], tuple[float, float]],
    ridge: float = 0.5,
    cap: float = 0.15,
    min_obs: int = 2,
) -> tuple[pd.Series, pd.DataFrame, dict[tuple[str, str], str]] | None:
    """Multi-objective joint move with per-step cap and trust region.

    Minimizes the block-weighted sum over twh + shape + lmp rows. Knobs whose
    recommended step would push the target's resolved multiplier outside the
    pure-pair sampled range are zeroed and re-solved (the trust region), so
    the recipe never recommends an extrapolated move.

    Returns (Δm, per-row prediction frame, {frozen knob: reason}).
    """
    sysm = _recipe_system(S, err, weights, scales, min_obs)
    if sysm is None:
        return None
    knobs, rows, A, b, w = sysm
    lo = np.full(len(knobs), -cap)
    hi = np.full(len(knobs), cap)
    x = _solve_box(A, b, w, ridge, lo, hi)
    dm = pd.Series(x, index=pd.MultiIndex.from_tuples(knobs))
    frozen = trust_region_violations(dm, resolved, ranges)
    if frozen:
        for i, k in enumerate(knobs):
            if k in frozen:
                lo[i] = hi[i] = 0.0
        x = _solve_box(A, b, w, ridge, lo, hi)
        dm = pd.Series(x, index=pd.MultiIndex.from_tuples(knobs))
        # The re-solve can route the same extrapolation through a different
        # knob; freeze cumulatively until clean (bounded by the knob count).
        for _ in range(len(knobs)):
            more = {
                k: r
                for k, r in trust_region_violations(dm, resolved, ranges).items()
                if k not in frozen
            }
            if not more:
                break
            frozen.update(more)
            for i, k in enumerate(knobs):
                if k in frozen:
                    lo[i] = hi[i] = 0.0
            x = _solve_box(A, b, w, ridge, lo, hi)
            dm = pd.Series(x, index=pd.MultiIndex.from_tuples(knobs))
    resid = A @ x + b
    pred = pd.DataFrame(
        {
            "year": [r[0] for r in rows],
            "metric": [r[1] for r in rows],
            "key": [r[2] for r in rows],
            "err_now": b,
            "err_pred": resid,
        }
    )
    return dm, pred, frozen


def print_error_blocks(b: Bundle, cache: dict) -> None:
    """All three error blocks for one run (--validate-run report)."""
    err = error_blocks(b, cache)
    print(f"\n  Error blocks — {b.name}:")
    twh = err[err["metric"] == "twh"].pivot(index="key", columns="year", values="err")
    print("  [twh] model − EIA-923 (TWh):")
    print("    " + twh.round(2).to_string().replace("\n", "\n    "))
    other = err[err["metric"] != "twh"]
    if other.empty:
        print(
            "  [shape]/[lmp] no metrics available (missing parquet or "
            "actual-LMP reference)"
        )
        return
    ov = other.pivot(index=["metric", "key"], columns="year", values="err")
    print(
        "  [shape] NRMSE vs EIA-930 / panel cf_emd; [lmp] demand-weighted "
        "monthly |model − actual RT| ($/MWh):"
    )
    print("    " + ov.round(3).to_string().replace("\n", "\n    "))


def print_recipe(
    iso: str,
    S: pd.DataFrame,
    target: Bundle,
    cache: dict,
    pairs: list[PairObs],
    baseline: Bundle,
    weights: dict[str, float],
    ridge: float,
    cap: float,
) -> None:
    scales = block_scales(baseline, cache)
    ranges = knob_sampled_ranges(pairs)
    res = solve_joint_move(
        S,
        error_blocks(target, cache),
        weights,
        scales,
        target.curves,
        ranges,
        ridge=ridge,
        cap=cap,
    )
    print(
        f"\n--- {iso} joint-move recipe (target: {target.name} errors; "
        f"blocks twh/shape/lmp weighted "
        f"{weights['twh']:g}/{weights['shape']:g}/{weights['lmp']:g}, "
        f"normalized to {baseline.name}; |Δmult| ≤ {cap}) ---"
    )
    if not (target.path / "btm.parquet").exists():
        print(
            "  NOTE: target bundle has no btm.parquet — errors are "
            "grid-only vs EIA-923 totals (BTM add-back missing), so "
            "CHP-class targets are biased low."
        )
    if res is None:
        print("  not enough well-observed knobs (n_obs >= 2) to solve")
        return
    dm, pred, frozen = res
    for (cls, band), reason in sorted(frozen.items()):
        print(
            f"  TRUST REGION: {cls}.{band} step zeroed — {reason}; "
            "re-derive locally first (run a small probe pair around the "
            "current value before trusting a move here)."
        )
    moves = dm[dm.abs() > 0.005].sort_values(key=lambda s: -s.abs())
    if moves.empty:
        print(
            "  no move recommended (errors already balanced, S too weak, "
            "or every useful knob trust-region-frozen)"
        )
    else:
        print("  Recommended Δmult per knob:")
        for (cls, band), v in moves.items():
            lo, hi = ranges.get((cls, band), (float("nan"),) * 2)
            cur = (target.curves.get(cls) or {}).get(band)
            print(
                f"    {cls:<14} {band:<10} {v:+.3f}   "
                f"(resolved {cur:.3f} -> {cur + v:.3f}; "
                f"sampled [{lo:.3f}, {hi:.3f}])"
            )
    print(
        "  Predicted change per block (RMS of err rows, native units — "
        "TWh / NRMSE-EMD / $-per-MWh):"
    )
    now = _block_rms(
        list(zip(pred["year"], pred["metric"], pred["key"])),
        pred["err_now"].to_numpy(float),
    )
    aft = _block_rms(
        list(zip(pred["year"], pred["metric"], pred["key"])),
        pred["err_pred"].to_numpy(float),
    )
    for m in METRICS:
        if m in now:
            arrow = (
                "improves"
                if aft[m] < now[m] - 1e-9
                else ("DEGRADES" if aft[m] > now[m] + 1e-9 else "unchanged")
            )
            print(f"    {m:<6} {now[m]:8.3f} -> {aft[m]:8.3f}  ({arrow})")
    tw = pred[pred["metric"] == "twh"]
    pv = tw.pivot(index="key", columns="year", values=["err_now", "err_pred"]).round(2)
    print("  Predicted class errors after the move (TWh, model − EIA-923):")
    print("    " + pv.to_string().replace("\n", "\n    "))


# ---------------------------------------------------------------------------
# Back-test: predict one historical move through the Jacobian
# ---------------------------------------------------------------------------


def backtest_pair(
    iso: str,
    S: pd.DataFrame,
    base: Bundle,
    target: Bundle,
    pairs: list[PairObs],
    cache: dict,
) -> None:
    """Predict target's per-block changes from base's config delta.

    The regression test for the trust region: with
    ``--backtest e2_4_retune run82_jacobian_joint`` the CT_PEAKER committed
    move must be flagged (its post-move value sat outside the range sampled
    by every pure pair available at the time — the target itself is excluded
    from the sampled-range computation here for exactly that reason).
    """
    klasses = {c for b in (base, target) for c in b.curves}
    dmult = curve_deltas(base, target, klasses)
    print(f"\n--- {iso} back-test: {base.name} -> {target.name} ---")
    if not dmult:
        print("  no offer-curve deltas between the two bundles")
        return
    print("  Config delta (Δmult per knob):")
    for (cls, band), d in sorted(dmult.items()):
        print(f"    {cls:<14} {band:<10} {d:+.3f}")

    ranges = knob_sampled_ranges(pairs, exclude=frozenset({target.name}))
    dm = pd.Series(dmult)
    flags = trust_region_violations(dm, base.curves, ranges)
    for (cls, band), reason in sorted(flags.items()):
        print(f"  TRUST REGION would flag {cls}.{band}: {reason}")
    if not flags:
        print(
            "  trust region: every knob's post-move value stays inside "
            "its sampled range"
        )

    Sp = S[S["band"].isin(BANDS)]
    coef = Sp.set_index(["year", "metric", "in_class", "out_class", "band"])[
        "dTWh_per_unit_mult"
    ]
    known = {(c, bnd) for (_, _, _, c, bnd) in coef.index}
    missing = sorted(set(dmult) - known)
    if missing:
        print(
            "  knobs absent from the Jacobian (no pure-pair coverage): "
            + ", ".join(f"{c}.{b}" for c, b in missing)
        )

    v0, v1 = metric_values(base, cache), metric_values(target, cache)
    common = v0.index.intersection(v1.index)
    actual = v1[common] - v0[common]
    rows = []
    for y, m, k in common:
        p = sum(coef.get((y, m, k, c, bnd), 0.0) * d for (c, bnd), d in dmult.items())
        rows.append(
            {
                "year": y,
                "metric": m,
                "key": k,
                "predicted": p,
                "actual": float(actual[(y, m, k)]),
            }
        )
    cmp_df = pd.DataFrame(rows)
    print("  Predicted vs actual change per block (RMS over rows):")
    keys = list(zip(cmp_df["year"], cmp_df["metric"], cmp_df["key"]))
    pr = _block_rms(keys, cmp_df["predicted"].to_numpy(float))
    ar = _block_rms(keys, cmp_df["actual"].to_numpy(float))
    er = _block_rms(keys, (cmp_df["predicted"] - cmp_df["actual"]).to_numpy(float))
    for m in METRICS:
        if m in ar:
            print(
                f"    {m:<6} predicted RMS {pr.get(m, 0):8.3f}   "
                f"actual RMS {ar[m]:8.3f}   prediction-error RMS "
                f"{er[m]:8.3f}"
            )
    big = cmp_df.reindex(
        cmp_df["actual"].abs().sort_values(ascending=False).index
    ).head(12)
    print("  Largest actual changes (predicted vs actual, native units):")
    for _, r in big.iterrows():
        print(
            f"    {int(r['year'])} {r['metric']:<6} {r['key']:<14} "
            f"pred {r['predicted']:+8.3f}   actual {r['actual']:+8.3f}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument(
        "--iso",
        action="append",
        help="restrict to ISO(s); default: every ISO discovered",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--ridge",
        type=float,
        default=0.05,
        help="regression ridge alpha (trace-scaled)",
    )
    ap.add_argument(
        "--recipe-ridge",
        type=float,
        default=0.5,
        help="joint-move solver ridge (heavier: small fits)",
    )
    ap.add_argument(
        "--cap",
        type=float,
        default=0.15,
        help="per-step band-move cap for the joint-move recipe",
    )
    ap.add_argument(
        "--validate-run",
        action="append",
        default=[],
        help="bundle name(s) for adjacency check + recipe target "
        "(default: latest bundle per ISO); prints all three "
        "error blocks (twh/shape/lmp) for the run",
    )
    ap.add_argument(
        "--w-twh",
        type=float,
        default=1.0,
        help="recipe weight for the annual class-TWh block",
    )
    ap.add_argument(
        "--w-shape",
        type=float,
        default=1.0,
        help="recipe weight for the hourly dispatch-shape block "
        "(EIA-930 NRMSE + panel cf_emd)",
    )
    ap.add_argument(
        "--w-lmp",
        type=float,
        default=1.0,
        help="recipe weight for the monthly LMP-MAE block "
        "(mostly a guardrail vetoing price-degrading moves)",
    )
    ap.add_argument(
        "--baseline",
        default="e2_4_retune",
        help="bundle whose per-block error magnitudes normalize "
        "the recipe blocks (default: the run-79 keeper "
        "e2_4_retune; falls back to the target run)",
    )
    ap.add_argument(
        "--backtest",
        nargs=2,
        metavar=("BASE", "TARGET"),
        default=None,
        help="predict TARGET's per-block changes from BASE's "
        "offer-curve delta through the Jacobian and compare "
        "with the actual bundle-to-bundle changes; the "
        "trust region is evaluated as of BASE (TARGET's own "
        "pairs excluded)",
    )
    ap.add_argument(
        "--include-pair",
        action="append",
        default=[],
        help="force-include the pair ending at this run name",
    )
    ap.add_argument(
        "--exclude-pair",
        action="append",
        default=[],
        help="force-exclude the pair ending at this run name",
    )
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--no-recipe", action="store_true")
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args(argv)

    pd.set_option("display.width", 220)
    bundles = discover_bundles(args.root)
    if args.iso:
        bundles = [b for b in bundles if b.iso in args.iso]
    if not bundles:
        print(f"no calibration bundles with offer_curve_by_group under {args.root}")
        return 1
    cache = {} if args.refresh_cache else _load_cache()
    by_name = {b.name: b for b in bundles}

    all_S = []
    for iso in sorted({b.iso for b in bundles}):
        seq = [b for b in bundles if b.iso == iso]
        print(
            f"\n{'=' * 78}\nISO {iso}: {len(seq)} bundles "
            f"({seq[0].name} … {seq[-1].name})"
        )
        pairs = build_pairs(seq, cache, set(args.include_pair), set(args.exclude_pair))
        print("\nConsecutive run pairs and classification:")
        for p in pairs:
            moved = (
                f"{len(p.dmult)} knob(s) moved"
                if p.dmult
                else "no curve deltas"
                if p.status != "legacy"
                else "-"
            )
            print(f"  [{p.status:<10}] {p.label:<44} {moved:<22} {p.reason}")

        pure = [p for p in pairs if p.status == "pure" and p.dmult]
        if not pure:
            print(
                f"\n  no verified pure-curve pairs for {iso} yet — the "
                "Jacobian will populate as tuning backcasts accrue. "
                "(Vet pairs above and add them to REGISTRY or use "
                "--include-pair.)"
            )
            continue
        for p in pure:  # materialize totals for both ends
            class_totals(p.b0, cache)

        S = fit_iso(pairs, args.ridge, cache)
        S.insert(0, "iso", iso)
        all_S.append(S)

        print(
            f"\n--- {iso} sensitivity matrix "
            f"({len(pure)} pure pairs; twh block, sorted by |dTWh/unit|; "
            "cells with n_obs<2 or |coef|<stderr are low-confidence) ---"
        )
        twh = S[S["metric"] == "twh"]
        show = twh[twh["dTWh_per_unit_mult"].abs() > 0.05]
        show = show.reindex(
            show["dTWh_per_unit_mult"].abs().sort_values(ascending=False).index
        )
        print(show.drop(columns=["iso", "metric"]).head(60).to_string(index=False))
        aux = S[S["metric"] != "twh"]
        if not aux.empty:
            print(
                f"\n--- {iso} shape/LMP sensitivities (d(metric)/d(mult); "
                "data-poor until pairs accrue — confidence flags matter "
                "more than magnitudes here) ---"
            )
            shaux = aux.reindex(
                aux["dTWh_per_unit_mult"].abs().sort_values(ascending=False).index
            )
            shaux = shaux[shaux["dTWh_per_unit_mult"].abs() > 1e-4]
            print(shaux.drop(columns="iso").head(40).to_string(index=False))

        if iso == "ERCOT":
            check_anchors(by_name, cache)

        targets = [
            by_name[n]
            for n in args.validate_run
            if n in by_name and by_name[n].iso == iso
        ] or [seq[-1]]
        for t in targets if args.validate_run else targets[:1]:
            print_error_blocks(t, cache)
        if not args.no_validate:
            print(
                f"\n--- {iso} merit-order adjacency validation "
                f"(bundle: {targets[0].name}) ---"
            )
            adjacency_check(targets[0], S, cache)
        if not args.no_recipe:
            baseline = by_name.get(args.baseline)
            if baseline is None or baseline.iso != iso:
                baseline = targets[0]
            print_recipe(
                iso,
                S,
                targets[0],
                cache,
                pairs,
                baseline,
                weights={"twh": args.w_twh, "shape": args.w_shape, "lmp": args.w_lmp},
                ridge=args.recipe_ridge,
                cap=args.cap,
            )
        if args.backtest:
            b0, b1 = (by_name.get(n) for n in args.backtest)
            if b0 and b1 and b0.iso == iso and b1.iso == iso:
                backtest_pair(iso, S, b0, b1, pairs, cache)
            elif iso in {getattr(b, "iso", None) for b in (b0, b1)}:
                print(
                    f"\n  --backtest: bundle(s) not found for {iso}: "
                    + ", ".join(n for n in args.backtest if n not in by_name)
                )

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache))
    if all_S:
        out = pd.concat(all_S, ignore_index=True)
        if args.out.exists():  # keep other ISOs' rows when run with --iso
            prev = pd.read_csv(args.out)
            out = pd.concat(
                [prev[~prev["iso"].isin(out["iso"])], out], ignore_index=True
            )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        sort_cols = [
            c
            for c in ("iso", "year", "metric", "out_class", "band", "in_class")
            if c in out.columns
        ]
        out.sort_values(sort_cols).to_csv(args.out, index=False)
        print(f"\nwrote {len(out)} cells -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
