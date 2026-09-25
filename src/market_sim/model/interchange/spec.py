"""Interchange model configuration — unified spec for all ISOs.

Replaces the parallel CAISO per-hub corridor model and the generic
reference-price seam with a single ``InterchangeSpec`` per ISO, each
containing corridors, reference-price neighbors, firm imports, and
optional monthly reconciliation.  The spec drives a single
``build_interchange_fleet`` function that produces identical
``Generator`` objects regardless of which code path produced them before.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# Canonical constants (single definition: config/fuel_trajectories.py, re-exported
# by config/constants.py). The pre-3E module kept local duplicated copies "to
# break the circular import interchange_config → constants → interchange_config";
# that cycle is lazy-only on the constants side (constants.py imports
# REFERENCE_PRICE_DEFAULT_ISOS inside a function), so the canonical definitions
# are importable at module level and the duplicates are deleted, not zeroed
# (rule 25; single-definition test in tests/test_config_model_layering.py).
from market_sim.config.constants import (
    CARB_UNSPECIFIED_IMPORT_EF,
    GAS_BASIS_DIFFERENTIAL,
)
from market_sim.data.fleet_models import Generator

# ---------------------------------------------------------------------------
# Data constants — moved from constants.py (unchanged values)
# ---------------------------------------------------------------------------

# Per-ISO external zone hosting import/export pseudo-generators.
IMPORT_ZONE: dict[str, str] = {
    "CAISO": "WECC_import",
    "PJM": "PJM_external",
    "NYISO": "NYISO_external",
    "NEISO": "HQ_import",
    "MISO": "MISO_external",
}

# Per-ISO forced-outage derate on import tranches.
IMPORT_EFORD: dict[str, float] = {
    "CAISO": 0.02,
    "PJM": 0.0,
    "NYISO": 0.0,
    "NEISO": 0.0,
    "MISO": 0.0,
}

# Per-tranche CO2 emission factor (tCO2/MWh) for the CARB border-carbon
# adjustment on imports.
IMPORT_TRANCHE_EF: dict[str, dict[str, float]] = {
    "CAISO": {
        "PNW_hydro_base": 0.0,
        "PNW_midC": 0.0,
        "DSW_solar_PV": 0.0,
        "DSW_CCGT": 0.37,
        "DSW_CT": 0.55,
        "WECC_scarcity": CARB_UNSPECIFIED_IMPORT_EF,
        # Surplus-hour WEIM clean transfer (caiso-87): CARB EIM GHG
        # attribution assigns clean surplus resources to CAISO transfers, so
        # the tranche pays no border carbon (see the depth block below).
        "DSW_surplus_clean": 0.0,
        # Overnight WEIM clean transfer (caiso-93): same attribution — the
        # measured overnight CAISO−PaloVerde spread carries no wedge in
        # 93-99 % of ALL overnight hours (FINDING-caiso93 §3).
        "DSW_overnight_clean": 0.0,
        # Daytime trigger-OFF WEIM clean transfer (caiso-94): same attribution
        # extends to the daytime hours the caiso-87 surplus trigger does not
        # cover — the measured daytime trigger-OFF CAISO−PaloVerde spread
        # carries no wedge in every daytime cell (FINDING-caiso94 §2).
        "DSW_daytime_clean": 0.0,
        # LATE-EVENING WEIM clean transfer (caiso-269): the SAME attribution,
        # measured on the same instrument. caiso-253's G-WEDGE leg tested hod
        # 22-23 explicitly and PASSED everywhere (delivered median -5.2 to
        # -14.2 against a +4 gate; wedge-consistent share 0.0-4.7 % against a
        # 6 % gate), i.e. "there is NO carbon wedge at 22-23 and caiso-93's
        # question answers YES there too" — so EF 0 here is a MEASURED result
        # of that session, not a transfer of the neighbouring windows' verdict.
        "DSW_lateevening_clean": 0.0,
    },
}

# Per-tranche physical delivered-cost basis over the measured WECC
# neighbor-hub price, for CAISO priced imports.
CAISO_IMPORT_DELIVERY_BASIS: dict[str, tuple[float, float]] = {
    "PNW_hydro_base": (0.04, 2.0),
    "PNW_midC": (0.05, 5.0),
    "DSW_solar_PV": (0.03, 4.0),
    "DSW_CCGT": (0.03, 4.0),
    "DSW_CT": (0.03, 4.0),
    "WECC_scarcity": (0.03, 6.0),
    # Surplus-hour WEIM clean transfer (caiso-87): same Path-46/WOR physical
    # wheel as the other desert-SW rungs.
    "DSW_surplus_clean": (0.03, 4.0),
    # Overnight WEIM clean transfer (caiso-93): NO wheel. WEIM/EDAM transfers
    # use available transmission without an OATT point-to-point wheeling
    # charge (CAISO EIM design — transfers are financially settled dispatch,
    # not scheduled wheels), and the measured overnight record corroborates
    # it: actual CAISO clears at ≈ the RAW Palo Verde hub (the −$4.5…−5.1
    # median spread vs the delivered ×1.03+$4 parity ≈ exactly the wheel;
    # FINDING-caiso93 §3/§5). The scheduled-import rungs above keep theirs.
    "DSW_overnight_clean": (0.0, 0.0),
    # Daytime trigger-OFF WEIM clean transfer (caiso-94): NO wheel, same as
    # the overnight leg. The measured daytime trigger-OFF CAISO clears at ≈ the
    # RAW Palo Verde hub (autumn daytime raw-hub spread ≈ 0, FINDING-caiso94
    # §2-3); WEIM transfers pay no OATT point-to-point charge.
    "DSW_daytime_clean": (0.0, 0.0),
    # Late-evening WEIM clean transfer (caiso-269): NO wheel, the same WEIM
    # transfer basis as the overnight and daytime legs that bracket it. The
    # basis is MEASURED for these two hours rather than inherited: caiso-253's
    # raw-hub discriminator reads the DA CAISO-PaloVerde block median at
    # -3.21 / -0.36 / -0.03 (2023/2024/2025), i.e. CAISO clears at ~= the RAW
    # hub at hod 22-23 in 2024-2025 -- which is what a no-wheel basis predicts
    # and what a hub x 1.03 + $4 delivered basis does not. 2023 sits OUTSIDE
    # caiso-253's pre-registered [-2, +4] admissibility band and is refused
    # hour-by-hour by the arming gate below, not waived here.
    "DSW_lateevening_clean": (0.0, 0.0),
}

# ---------------------------------------------------------------------------
# CAISO south-corridor surplus-clean import depth (caiso-87,
# ``ScenarioConfig.caiso_dsw_surplus_clean``, default off; FINDING-caiso86b /
# FINDING-caiso82 §3 "measured clean DEPTH" lane).
#
# MECHANISM: in surplus-West hours the marginal import into CAISO is a
# WEIM/EDAM transfer attributed to CLEAN surplus resources (CARB EIM GHG
# attribution assigns clean resources to CAISO transfers; the West's surplus
# IS hydro/solar/wind), so the marginal transfer carries NO unspecified border
# carbon — the measured CAISO−hub spread in those hours shows parity with no
# +$13–19 wedge (FINDING-caiso82 §1). The model's static clean depth (firm
# blocks + PNW_midC) truncates at ~4.1–5.2 GW, after which every MW pays a
# fossil/unspecified CARB rung; this tranche carries the measured clean depth
# beyond the firm block in surplus hours. Fossil rungs are unchanged and
# price the flow BEYOND the clean depth (secondary dispatch).
#
# TRIGGER (mechanical, forward-reproducible; hour t is "surplus" iff):
#     PaloVerde_hub_LMP[t] < HR_DSW_CCGT × SoCal_citygate_gas[t] + remote VOM
# i.e. the hub's own price is below the remote gas-CCGT floor (no carbon —
# AZ/NV are uncarbonized), so gas is NOT the hub's marginal resource and the
# surplus is clean. HR_DSW_CCGT = IMPORT_TRANCHE_EF ratio (0.37/0.0531 ≈ 6.97,
# transmission._CAISO_IMPORT_COUPLE_HR); gas = the measured SoCal citygate
# weekly print (data/raw/gas-prices/pge_socal_citygate_weekly.csv — an LDC
# citygate proxy for the desert-SW border hubs, documented misalignment per
# rule 14: reconciled real data over a guess). Trigger evaluates ONLY on
# measured hub hours (the 2023 Jan–Feb OASIS gap's reference-formula fill is
# pricing continuity, not surplus evidence — filled hours stay non-surplus).
# In a forecast year the hub series and gas print regenerate from the
# reference-price seam / gas forwards, so the state responds to changed
# conditions (rule 13).
#
# DEPTH (measured, year-stable): p95 of the measured WECC_DSW corridor net
# import (EIA-930 CISO DIBAs, model clock) over trigger-ON hours:
#     2023: 5,312 MW · 2024: 4,792 MW · 2025: 5,472 MW
# Estimation-stage honesty gates (caiso-81/86 precedent, run 2026-07-16,
# scratch derivation in FINDING-caiso86b): CV 0.056 (≤0.20 PASS); LOYO
# (mean-of-other-two) worst 12.5% (≤25% PASS). Matches the caiso-82 §3 banked
# depth-in-surplus stability read (south p95 4.7/5.4/5.5 GW). The static
# entry is the pooled mean (forward story — WEIM clean-surplus transfer
# capability is persistent market structure); backcast years ride their own
# measured depth (the caiso-80/82 construction class: per-year measured data,
# no pooling, the derive gates are the cross-year transfer check).
# ---------------------------------------------------------------------------
CAISO_DSW_SURPLUS_CLEAN_NAME: str = "DSW_surplus_clean"
# 2022 ADDED 2026-09-07 (caiso-262, the rule-22 validation touchpoint). Rule 22
# as amended 2026-08-06 — "what is held out is the SCORE, never the DATA": a
# held-out year rides its OWN measured depth exactly as every other backcast
# year does, or the 2022 rung would silently run the pooled STATIC while
# 2023-2025 run measured values, i.e. a recipe the keeper was never scored on.
# Derivable only since caiso-261 landed the 2022 MALIN / PALOVRDE hub rows of
# wecc_intertie_lmp_hourly_CAISO.parquet from the OASIS GroupZip DAM archives
# (H-3); caiso-259 §2 listed S-3 as NOT derivable, and that is superseded by
# the H-3 landing, which is the source-data change rule 23 [R-FROZEN-DERIVE]
# requires a re-derivation to cite.
# PRODUCER, NEW AND VERIFIED: scripts/data/derive_caiso_dsw_surplus_depth.py.
# This depth was the one of the three with NO committed producer (the comment
# above still calls it a "scratch derivation in FINDING-caiso86b"); the new
# script transcribes the construction documented above and REPRODUCES the three
# committed values to the MW (5,311.600 / 4,791.900 / 5,472.500 against 5,312 /
# 4,792 / 5,472), the pooled static (5,192) and the published gates (CV 0.056,
# LOYO worst 12.5%) before it emits any new year. The 2023-2025 values and the
# static are UNCHANGED — the extra year is report-only and never enters the
# pooled mean or the gates, so the committed rows are not re-adjudicated.
CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR: dict[int, float] = {
    2022: 5813.0,
    2023: 5312.0,
    2024: 4792.0,
    2025: 5472.0,
}
CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC: float = 5192.0  # pooled 2023-2025 mean
# Remote-CCGT VOM for the trigger floor ($/MWh) — the same representative
# gas-CC VOM the soft-month floor decomposition used (FINDING-caiso82 §1).
CAISO_DSW_SURPLUS_REMOTE_VOM: float = 2.5

# ---------------------------------------------------------------------------
# CAISO south-corridor OVERNIGHT clean import depth (caiso-93,
# ``ScenarioConfig.caiso_dsw_overnight_clean``, default off;
# FINDING-caiso93-overnight-no-wedge-2026-07-17 — the FINDING-caiso92b §6
# import-side redirect, owner-authorized build 2026-07-17).
#
# MECHANISM: overnight (hod 0-5) the measured CAISO−PaloVerde spread carries
# NO unspecified-import carbon wedge in 93-99 % of ALL overnight hours
# (median DA spread −4.5…−5.1 $/MWh vs delivered parity, three years, both
# bases — FINDING-caiso93 §2-3): the marginal overnight import is a WEIM/EDAM
# transfer attributed to the West's overnight non-emitting surplus (NW
# hydro + wind — the PNW hub's negative overnight prints), so it pays no
# border carbon even while gas sets the HUB price. The model instead prices
# every incremental overnight DSW MW at hub + the +$12-15 wedge — parity with
# domestic CC — and serves the overnight residual with CC where reality
# imports (FINDING-caiso92b: CC over-run +1.4/+2.1/+2.6 TWh ≈ import
# under-run). The caiso-87 surplus tranche cannot cover this: its
# hub-below-gas-floor trigger fires in only 1.2-3.6 % of 2024/25 overnight
# hours (the no-wedge state overnight is UNCONDITIONAL, not
# hub-state-gated — FINDING-caiso93 §3).
#
# STATE (mechanical, forward-reproducible): hour t is overnight iff
# hod(t) ≤ CAISO_OVERNIGHT_CLEAN_HOD_MAX — the persistent WEIM overnight
# clean-transfer regime, an hod window fixed upstream by the phenomenon's
# charter (FINDING-caiso91c/92b, set before any spread was measured), not a
# fitted window. Armed only on measured-hub hours (the 2023 Jan-Feb OASIS
# gap's reference fill is pricing continuity, not clean-attribution
# evidence — gap hours stay 0 MW, preserving the closed winter lane).
#
# DEPTH (measured, year-stable): p95 of the measured WECC_DSW corridor net
# import (EIA-930 CISO DIBAs, model clock) over ALL overnight hours:
#     2023: 5,870 MW · 2024: 6,205 MW · 2025: 6,487 MW
# Estimation-stage honesty gates (caiso-81/86/87/88 precedent, run
# 2026-07-17 in scripts/data/derive_caiso_overnight_clean_depth.py): CV 0.041
# (≤0.20 PASS); LOYO (mean-of-other-two) worst 8.1 % (≤25 % PASS) — tighter
# than the caiso-87 midday depth's own gates (0.056 / 12.5 %). The static
# entry is the pooled mean (persistent WEIM market structure); backcast
# years ride their own measured depth (the caiso-80/82 construction class).
# Zero fitted scalars. Pricing: RAW measured Palo Verde hub, EF 0, no wheel
# (see CAISO_IMPORT_DELIVERY_BASIS above — WEIM transfers pay no OATT
# point-to-point charge, corroborated by the measured overnight spread).
# ---------------------------------------------------------------------------
CAISO_DSW_OVERNIGHT_CLEAN_NAME: str = "DSW_overnight_clean"
# 2022 ADDED 2026-09-07 (caiso-262) — same rule-22 rationale, same H-3 source
# unlock and the same report-only discipline as the surplus block above.
# Producer: derive_caiso_overnight_clean_depth.py --extra-years 2022, whose
# DEFAULT run reproduces 5,870 / 6,205 / 6,487, the gates (CV 0.041, LOYO worst
# 8.1%) and this block byte-for-byte. 2022's 6,309 MW sits INSIDE the
# 2023-2025 range, which is why nothing here is re-adjudicated.
CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR: dict[int, float] = {
    2022: 6309.0,
    2023: 5870.0,
    2024: 6205.0,
    2025: 6487.0,
}
CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC: float = 6187.0  # pooled 2023-2025 mean
# Overnight window upper hod (inclusive) — hod 0-5, the FINDING-caiso91c/92b
# overnight definition (fixed upstream of the spread measurement).
CAISO_OVERNIGHT_CLEAN_HOD_MAX: int = 5

# ---------------------------------------------------------------------------
# CAISO south-corridor DAYTIME trigger-OFF clean import depth (caiso-94,
# ``ScenarioConfig.caiso_dsw_daytime_clean``, default off;
# FINDING-caiso94-daytime-wedge-2026-07-17 — the C3a-2025 daytime lane, the
# caiso-93 promotion handoff's next charter; owner-authorized diagnostic build
# 2026-07-17, session-logged).
#
# MECHANISM: the measured no-wedge structure that admitted the caiso-93
# OVERNIGHT leg extends to the DAYTIME hours the caiso-87 surplus trigger does
# not cover. The daytime trigger-OFF CAISO−PaloVerde spread carries NO
# unspecified-import carbon wedge in every daytime cell (G1 no-wedge PASSES all
# cells; wedge-consistent share ≈ 0-6 % — FINDING-caiso94 §2), and the autumn
# daytime cells clear at raw-hub parity (raw-hub median +0.4…+3.0): the
# marginal daytime import is the same WEIM/EDAM clean-attributed transfer, so
# it pays no border carbon even while gas may set the HUB price. The model
# instead prices every incremental daytime DSW MW at hub + the +$12-15 wedge
# and over-prices the daytime (C3a-2025 +13.3 %, mass in autumn Sep-Dec + the
# belly). This tranche carries the measured daytime trigger-OFF clean depth.
#
# STATE (mechanical, forward-reproducible): hour t is armed iff
# CAISO_DAYTIME_CLEAN_HOD_MIN ≤ hod(t) ≤ CAISO_DAYTIME_CLEAN_HOD_MAX AND the
# raw measured Palo Verde hub is finite AND the caiso-87 surplus trigger is
# OFF (PaloVerde ≥ HR_CCGT × SoCal_citygate weekly + remote VOM). The
# trigger-OFF scoping is LOAD-BEARING: daytime caiso-87 is coverage-RICH
# (66-90 % trigger-ON in the belly), so this leg is scoped to the COMPLEMENT
# to stay DISJOINT from caiso-87 (unlike caiso-93 overnight, which was
# unconditional because caiso-87 is coverage-starved overnight —
# FINDING-caiso94 §1). Armed only on measured-hub hours (the 2023 Jan-Feb
# OASIS gap fill never arms). In a forecast year the hub series + gas print
# regenerate from the reference-price seam / gas forwards, so the state
# responds to changed conditions (rule 13).
#
# DEPTH (measured, year-stable): p95 of the measured WECC_DSW corridor net
# import (EIA-930 CISO DIBAs, model clock) over the daytime trigger-OFF window:
#     2023: 5,441 MW · 2024: 5,762 MW · 2025: 5,998 MW
# Estimation-stage honesty gates (caiso-81/86/87/88/93 precedent, run
# 2026-07-17 in scripts/data/derive_caiso_daytime_clean_depth.py): CV 0.040
# (≤0.20 PASS); LOYO (mean-of-other-two) worst 8.1 % (≤25 % PASS) — as tight
# as the caiso-93 overnight depth (0.041 / 8.1 %). The static entry is the
# pooled mean (persistent WEIM market structure); backcast years ride their
# own measured depth (the caiso-80/82 construction class). Zero fitted
# scalars. Pricing: RAW measured Palo Verde hub, EF 0, no wheel (WEIM transfer
# basis — see CAISO_IMPORT_DELIVERY_BASIS above). The injector nets the depth
# per hour against the shaped firm block + the caiso-87 surplus tranche + the
# caiso-93 overnight tranche, so no hour double-carries clean depth.
# ---------------------------------------------------------------------------
CAISO_DSW_DAYTIME_CLEAN_NAME: str = "DSW_daytime_clean"
# 2022 ADDED 2026-09-07 (caiso-262) — same rule-22 rationale, same H-3 source
# unlock and the same report-only discipline as the surplus block above.
# Producer: derive_caiso_daytime_clean_depth.py --extra-years 2022, whose
# DEFAULT run reproduces 5,441 / 5,762 / 5,998, the static (5,733) and the
# gates (CV 0.040, LOYO worst 8.1%) byte-for-byte.
# REPORTED AT FULL MAGNITUDE, NOT SMOOTHED: 2022's 6,774 MW sits ~13 % ABOVE
# the 2023-2025 range (5,441-5,998) — the only one of the three depths that
# does. The mechanism is visible in the window itself: 2022 is a high-gas year
# (the Dec-2022 West spike), the trigger floor is HR_CCGT x SoCal citygate, so
# a higher floor puts MORE hours on the trigger-OFF side (3,398 of 5,840
# measured daytime hours) and the p95 of that wider, deeper population rises.
# That is the construction responding to a changed condition exactly as rule 13
# [R-MEASURED] requires of an admissible input — NOT a fitted value, and not a
# reason to substitute the pooled static, which would replace a measured year
# with a mean of three other years.
CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR: dict[int, float] = {
    2022: 6774.0,
    2023: 5441.0,
    2024: 5762.0,
    2025: 5998.0,
}
CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC: float = 5733.0  # pooled 2023-2025 mean
# Daytime window hod bounds (inclusive) — hod 6-21, the FINDING-caiso94
# daytime band (morning ramp through evening peak; set before the depth was
# measured). Complements the caiso-93 overnight window (hod 0-5).
CAISO_DAYTIME_CLEAN_HOD_MIN: int = 6
CAISO_DAYTIME_CLEAN_HOD_MAX: int = 21

# ---------------------------------------------------------------------------
# EVENING-TRIMMED daytime window (caiso-97, ``ScenarioConfig.
# caiso_dsw_daytime_evening_trim``, default off) — the FINDING-caiso94 §7
# PRE-REGISTERED overshoot fix, armed by the owner's evening-watch TRIPPED
# ruling (2026-07-18, session-logged): drop the evening peak hod 18-21 from
# the daytime tranche window (6-21 → 6-17). Grounded in the measured per-cell
# admissibility table (FINDING-caiso94 §4A): evening 18-21 × non_autumn was
# an EXCLUDE cell (model UNDER-prices the peak — a clean-import lever there
# overshoots), and the caiso-96 A/B demonstrated the excess evening import
# volume (+1.9/+2.1/+2.2 TWh/yr vs EIA-930 hod 17-21) out-competes the
# now-online afternoon CC capacity. Never fitted to the residual — the trim
# window was pre-registered in the finding before any solve.
#
# DEPTH (measured, re-derived over the TRIMMED window so the depth prices the
# same population it caps — the derive script's CRITICAL window-match rule):
# p95 of measured WECC_DSW corridor net import over hod 6-17 trigger-OFF
# hours. Estimation-stage honesty gates (same FROZEN thresholds, run
# 2026-07-18 in scripts/data/derive_caiso_daytime_clean_depth.py --evening-trim):
# CV 0.060 (≤0.20 PASS); LOYO (mean-of-other-two) worst 13.5 % (≤25 % PASS —
# 2024 3.3 %, 2025 8.5 %). Static entry = pooled mean. Zero fitted scalars.
# ---------------------------------------------------------------------------
CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX: int = 17
CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR: dict[int, float] = {
    2023: 4994.0,
    2024: 5563.0,
    2025: 5770.0,
}
CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_STATIC: float = 5442.0  # pooled 2023-2025 mean

# ---------------------------------------------------------------------------
# CAISO south-corridor LATE-EVENING clean import depth (caiso-269,
# ``ScenarioConfig.caiso_dsw_lateevening_clean``, default off).
#
# THE OBJECT IS A WINDOW GAP, NOT A NEW MECHANISM. The three DSW clean-depth
# constructions do not tile the clock: caiso-93 runs hod 0-5, caiso-94 runs
# hod 6-21, and caiso-87's surplus trigger is coverage-STARVED at hod 22-23
# (measured ON in 0.3/0.8 % of 2024 and 1.6/1.9 % of 2025 hod 22/23 --
# caiso-253's G-WINDOW leg). Hours 22 and 23 therefore carry NO unconditional
# clean coverage, and the model's clean import capability falls off a cliff
# between two adjacent hours: measured on the 2026-09-09-caiso-fuelvintage-
# 860-gas keeper's own committed sidecars, armed clean capability runs
# 3,420 MW at hod 21 and 33 MW at hod 22 in 2025 (2,673 -> 123 MW in 2023;
# 3,117 -> 9 MW in 2024) -- a ~100x discontinuity across one hour boundary
# that no measured series supports, since the measured WECC_DSW corridor net
# import RISES across it (p50 4,642 -> 4,911 -> 4,875 MW at hod 21/22/23,
# 2025). The model's import deficit against EIA-930 at hod 22/23 is
# -1,063/-1,032 (2023), -1,290/-1,512 (2024) and -1,454/-1,787 MW (2025).
#
# WINDOW: hod 22-23, and the window is not this session's choice. caiso-253
# measured the trigger-coverage question and CLOSED it -- "22-23 are
# OVERNIGHT-construction hours and no future session need re-measure it" --
# so the window is the complement caiso-93/94/87 leave, fixed by the tiling
# and by that prior finding, never by a residual (rule 17
# ``[R-FLOOR-WINDOW]``: driver = the WEIM/EDAM clean transfer capability the
# caiso-87/93/94 family already carries; window = the hours the family's own
# coverage census leaves uncovered; forward story = the depth and the gate
# below are pooled climatologies that regenerate from any year's measured
# record exactly as the sibling legs do).
#
# ADMISSIBILITY GATE -- THIS IS caiso-253's OWN REFUSAL, ADOPTED AS THE GATE.
# caiso-253 REFUSED extending raw-hub pricing to hod 22-23 because its
# pre-registered raw-hub discriminator FAILED in 2023 (DA block median
# -3.98/-2.56 at hod 22/23 against a [-2, +4] band) while PASSING in 2024
# (-0.73/+0.11) and 2025 (-0.19/+0.06). That refusal is honoured literally:
# this tranche arms an hour ONLY where the measured (month x hod) median DA
# CAISO-PaloVerde spread lies inside caiso-253's band. Nothing about the band
# is this session's -- the statistic, the basis (DA), the window and the
# [-2, +4] bounds are all caiso-253's, pre-registered there before any solve
# and re-used here unchanged, so no threshold is selectable by a result.
# Measured admissible (month x hod) buckets: 2022 12/24, 2023 4/20 (the
# 2023 Jan-Feb OASIS hub gap leaves 10 covered months), 2024 18/24,
# 2025 19/24 -- i.e. the gate keeps 2023 dark, which is the point.
# The measured reason 2023 fails is itself published and forward-regenerating
# (caiso-253): the desert-SW hub peaks LATER than CAISO because Arizona keeps
# no DST, and the effect has closed monotonically (-3.21 -> -0.36 -> -0.03).
#
# DEPTH (measured, year-stable): p95 of the measured WECC_DSW corridor net
# import (EIA-930 CISO DIBAs, model clock) over hod 22-23 -- the same series,
# the same p95 statistic and the same window-match rule as the caiso-87/93/94
# depths. Estimation-stage honesty gates (the FROZEN caiso-81/86/87/88
# thresholds, run 2026-09-10 in
# scripts/data/derive_caiso_lateevening_clean_depth.py): CV 0.037
# (<= 0.20 PASS); LOYO (mean-of-other-two) worst 6.8 % (<= 25 % PASS) --
# tighter than the caiso-93 overnight depth (0.041 / 8.1 %). The static entry
# is the pooled 2023-2025 mean; backcast years ride their own measured depth
# (the caiso-80/82 construction class). Zero fitted scalars, zero new
# thresholds. Pricing: RAW measured Palo Verde hub, EF 0, no wheel (see
# CAISO_IMPORT_DELIVERY_BASIS above). The injector nets the depth per hour
# against the shaped firm block + the caiso-87 surplus tranche + the caiso-93
# overnight tranche + the caiso-94 daytime tranche, so no hour double-carries
# clean depth (rule 19 ``[R-ONE-MECH]``).
# ---------------------------------------------------------------------------
CAISO_DSW_LATEEVENING_CLEAN_NAME: str = "DSW_lateevening_clean"
CAISO_DSW_LATEEVENING_CLEAN_DEPTH_BY_YEAR: dict[int, float] = {
    2022: 6726.0,
    2023: 6120.0,
    2024: 6429.0,
    2025: 6697.0,
}
CAISO_DSW_LATEEVENING_CLEAN_DEPTH_STATIC: float = 6415.0  # pooled 2023-2025 mean
# Window hod bounds (inclusive) -- the complement caiso-93 (0-5) and caiso-94
# (6-21) leave, closed by caiso-253's G-WINDOW finding.
CAISO_LATEEVENING_CLEAN_HOD_MIN: int = 22
CAISO_LATEEVENING_CLEAN_HOD_MAX: int = 23
# caiso-253's pre-registered raw-hub admissibility band, re-used UNCHANGED as
# this tranche's per-(month x hod) arming gate (lo, hi) in $/MWh on the
# measured DA CAISO - raw PaloVerde spread. Not a free parameter: it is a
# prior session's frozen refusal criterion, and widening it would re-open the
# very cell caiso-253 closed.
CAISO_LATEEVENING_SPREAD_BAND: tuple[float, float] = (-2.0, 4.0)

# IMPORT_TRANCHES / EXPORT_TRANCHES entries: (name, capacity MW, $/MWh).
#
# CAISO firm-block volumes (LEVER B, 2026-07-04, FINDING-caiso-evening-merit):
# the two firm/contracted tranches (PNW_hydro_base, DSW_solar_PV — see
# transmission.CAISO_FIRM_IMPORT_TRANCHES) proxy CAISO's resource-adequacy
# import contracts: capacity-backed, must-offer supply that is self-scheduled
# or bid at/below $0/MWh during the availability assessment hours (CPUC
# D.20-06-028), i.e. price-taking firm blocks at the CAISO BAA boundary.
# Their volumes are grounded on two published primary sources:
#   1. TOTAL = DMM Annual Report on Market Issues & Performance, average
#      system RA capacity table, "Imports" row (excl. "Imports-MSS", which are
#      internal metered subsystems, not boundary imports):
#        2023: 2,323 MW (2023 report, Jul 2024, RA chapter capacity table)
#        2024: 3,371 MW (2024 report, Aug 2025, Table 15.6)
#        2025: carries the latest LIKE-FOR-LIKE measured year (2024,
#              3,371 MW). ADJUDICATED caiso-252 (2026-09-05): the DMM 2025
#              annual report HAS published (2026-06-26, caiso.com/documents/
#              2025-annual-report-on-market-issues-and-performance.pdf,
#              sha256 7c89fdc4…15ea9) and its Table 16.7 "Imports" row reads
#              1,710 MW — but that table is NOT the same measurement: DMM
#              changed the analysis-hour methodology for 2025 (60 availability
#              assessment hours, many in SPRING, "notably lower than in
#              previous years that use the different methodology"; total RA
#              46,169 MW vs 52,646 MW on the 2024 basis), and the report
#              itself says RA imports "were lower during the summer months
#              but higher during other periods compared to 2024". A spring-
#              weighted 60-hour average is a different aggregation from the
#              summer-day table the 2023/2024 rows come from, so adopting it
#              literally would make the firm block LESS representative (the
#              rule 14 [R-ACCURATE] misalignment exception, documented here as
#              that rule requires). No like-for-like 2025 figure exists in the
#              report (Figure 16.9 is a chart of peak-hour RA import bids by
#              price bin); the 2025 quarterlies publish only mixed YoY
#              bid-volume changes (+256/-6/-28/-37%) off unpublished monthly
#              bases. STILL OPEN: a reconciled 2025 value needs a same-basis
#              source (a summer-AAH cut of Table 16.7 or the CPUC RA
#              compliance filings); until then the 2024 value stands.
#   2. SPLIT PNW vs DSW = published Maximum Import Capability (MIC) per
#      branch group (data/raw/capacity-deliverability/caiso/caiso.csv, CAISO
#      "Maximum RA Import Capability for year YYYY" docs). RA imports require
#      MIC on the source intertie, so the corridor split follows the MIC share
#      north vs south of Path 15 (north = Malin 500, COTP, NOB [PDCI — PNW
#      source, CISO–BPAT interchange], Cascade, Summit, Round Mountain 230,
#      Cottonwood 230, Northwest 230, Marble, and the BANC/TIDC-area ties
#      [Tracy 230/500, Tracy-TEA, Westley-*, Standiford, Oakdale, New Melones,
#      Rancho Seco/Lake], matching CAISO_CORRIDOR_DIBA geography):
#        2023: north 7,411 / 16,055 = 46.2% → PNW 1,072, DSW 1,251
#        2024: north 7,603 / 16,452 = 46.2% → PNW 1,558, DSW 1,813
#        2025: north 7,500 / 16,148 = 46.4% → PNW 1,566, DSW 1,805
#      ("Merchant", 387–516 MW, is unmappable from the MIC doc alone and is
#      kept south; moving it north would shift the split by ~3%.)
# Boundary caveats (rule #14): CEC Total System Electric Generation NW/SW
# imports are all-California (LADWP/IID/BANC included) and CARB's specified
# split is the jurisdictional-importer boundary — both rejected as misaligned.
# EIA-930 net corridor flows cannot size a gross firm block (their low
# percentiles are negative: midday solar exports net against firm imports).
# Prices are unchanged Tier-3 contract-cost proxies (see
# CAISO_FIRM_IMPORT_TRANCHES). The static entry below carries the latest
# grounded (2025) volumes as the forward story — RA import contracting is a
# persistent market structure; backcast years use IMPORT_TRANCHES_BY_YEAR.
#
# PRICE-LADDER PROVENANCE (gap register G-26, issue #1350 / audit C-6): the
# volumes above are measured (DMM RA capacity × MIC split, cited above); the
# $/MWh values are still static-fitted-pending-measured — Tier-3 proxies, not
# a Q-Q derivation of measured flow x hub LMP like MISO_SEAM_LADDER_BY_YEAR /
# the NEISO ladders below. Labelled per rule 24/rule 11 honesty; values
# unchanged.
IMPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    "CAISO": [
        ("PNW_hydro_base", 1566.0, 28.0),
        ("PNW_midC", 1800.0, 36.0),
        ("DSW_solar_PV", 1805.0, 48.0),
        ("DSW_CCGT", 1800.0, 68.0),
        ("DSW_CT", 2200.0, 110.0),
        ("WECC_scarcity", 3000.0, 180.0),
    ],
    # PJM STATIC tranches (STATIC-FITTED-PENDING-MEASURED, gap register G-26,
    # issue #1350 / audit C-6): these two scarcity-rung tranches are bare
    # literals with no cited primary source and no by-year entry. They serve
    # ONLY the static-node path (reference_price_interface off) — the priced
    # reference seam now has its own measured Q-Q derivation,
    # PJM_SEAM_LADDER_BY_YEAR below (scripts/data/derive_pjm_seam_ladders.py,
    # 2026-07-10, closing C-6 for PJM's priced path the way
    # MISO_SEAM_LADDER_BY_YEAR / the NEISO ladders closed theirs). Labelled
    # per rule 24/rule 11 honesty; values unchanged.
    "PJM": [
        ("import_scarcity_1", 1000.0, 46.0),
        ("import_scarcity_2", 3000.0, 60.0),
    ],
    # NYISO import ladder (audit C-6 / gap register G-26 / issue #1350 closure,
    # 2026-07-21): measured total-net Q-Q derivation from
    # scripts/data/derive_nyiso_import_tranches.py — the anti-monotone duration
    # coupling of the measured NYISO Day-Ahead zonal-mean LBMP
    # (data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet) with the
    # measured hourly net external import (the four "SCH -" external seams —
    # HQ/IESO/PJM/NE — of the NYISO MIS ExternalLimitsFlows posting,
    # data/raw/NYISO/interface-flows/). Single import node → the AGGREGATE
    # net-import supply curve is the object reconciled to the model (rule 14),
    # not per-seam curves. HQ_hydro kept at the firm-base 900 MW so the
    # always-on firm-import floor (NYISO_FIRM_IMPORT_FLOOR_FRAC) is unchanged;
    # five equal-MW economic rungs span [900, ~4,350 MW SIL] (the clearable
    # range) so a rung lands at the off-peak operating depth and reprices it
    # measured; import_scarcity is the SIL-blocked deep tail. Replaces the
    # residual-fitted ladder whose IESO $22.5 → PJM_west $34.2 gap pinned ~3000
    # off-peak hours at $34.2 (the real seam cleared them at $20-28). Rule 23:
    # re-derive only when the interface-flow / DA-LMP source data extends. This
    # static entry is the POOLED 2023-2025 derivation (multi-year revealed
    # supply curve, forward story); backcast years use IMPORT_TRANCHES_BY_YEAR.
    "NYISO": [
        ("HQ_hydro", 900.0, 20.78),
        ("IESO_Ontario", 690.0, 26.36),
        ("PJM_shoulder", 690.0, 32.24),
        ("PJM_west", 690.0, 40.13),
        ("eastern_mid", 690.0, 51.03),
        ("ISONE_tie", 690.0, 71.46),
        ("import_scarcity", 2035.0, 152.97),
    ],
    # NEISO seams (audit C-6 closure, 2026-07-06): measured-data ladders from
    # scripts/data/derive_neiso_import_tranches.py — per-seam Q-Q duration coupling
    # of the measured ISO-NE DA hub LMP (SMD workbooks) with the measured
    # EIA-930 per-seam flows (ISNE↔HQT/NBSO/NYIS,
    # data/raw/eia-930-interchange/"ISNE interchange hourly.parquet"),
    # anchored on the NYISO proxy-bus DA LBMPs (NYISO_HQ = HQ's measured
    # opportunity cost; NYISO_NPX = the NY-side NY–NE interface price;
    # data/raw/_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet).
    # Capacities: measured p98 per-seam import depth (Highgate carved at its
    # published ~225 MW converter rating); scarcity rung = p99.9 total-import
    # depth beyond the per-seam rungs. Identification: measured (rule 23 —
    # re-derive only when the source data extends), replacing the
    # residual-fitted rungs the DOF ledger flagged. This static entry is the
    # POOLED 2023-2025 derivation — the multi-year revealed seam supply curve
    # carried forward (HQ water value, NY–NE arbitrage parity, NB surplus);
    # backcast years use IMPORT_TRANCHES_BY_YEAR/EXPORT_TRANCHES_BY_YEAR.
    "NEISO": [
        ("Highgate", 225.0, 26.53),
        ("HQ_PhaseII", 1830.0, 41.10),
        ("NB_north", 630.0, 59.15),
        ("NYISO_CT_base", 870.0, 34.79),
        ("NYISO_CT_peak", 870.0, 73.04),
        ("import_scarcity", 95.0, 286.12),
    ],
}

IMPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    # CAISO: only the two firm-block capacities vary by year (DMM RA import
    # capacity × MIC corridor share — full derivation in the IMPORT_TRANCHES
    # comment above). Spot tranches and all prices are identical to the static
    # ladder. 2025 firm total carries the 2024 DMM measurement (open data gap
    # until the DMM 2025 annual report publishes).
    #
    # PRICE-LADDER PROVENANCE (gap register G-26, issue #1350 / audit C-6):
    # the $/MWh values are STATIC-FITTED-PENDING-MEASURED and identical across
    # all three years — Tier-3 contract-cost proxies, not a measured Q-Q
    # derivation like MISO_SEAM_LADDER_BY_YEAR or the NEISO ladders below.
    # Labelled per rule 24/rule 11 honesty; values unchanged.
    #
    # 2022 ADDED 2026-09-07 (caiso-262, the rule-22 validation touchpoint) —
    # same source, same table, same recipe, ZERO new parameters. Without the
    # row a 2022 rung falls to the STATIC ladder (1,566 / 1,805) and runs a
    # firm block the keeper was never scored on, silently (caiso-259 §2, S-2).
    #   DMM 2022 Annual Report on Market Issues and Performance (July 11 2023),
    #   **Table 8.5** "Average system resource adequacy capacity, availability,
    #   and performance by fuel", p. 234 — the `Imports` row = **3,171 MW**.
    #   The sibling `Imports-MSS` row (273 MW) is EXCLUDED, which is not a
    #   judgment call: the DMM 2023 report's Table 8.4 `Imports` row is 2,323
    #   MW, exactly the committed 2023 level, while its `Imports-MSS` is 326 —
    #   so the committed convention is the `Imports` row alone, and 2022 follows
    #   it. (Figure 8.2's "about 2,900 MW" bid-in volume is a DIFFERENT object —
    #   a chart-read of bid-in MW in Aug/Sep peak hours — and is NOT used.)
    #   MIC north share 2022 = 7,411 / 15,780 = 0.46965 (published branch-group
    #   import limits, the same north-of-Path-15 partition), so
    #   PNW_hydro_base = round(3,171 x 0.46965) = 1,489 and DSW_solar_PV =
    #   3,171 - 1,489 = 1,682.
    # THE CONSTRUCTION WAS RE-PROVED BEFORE 2022 WAS WRITTEN: applying it to
    # 2023/2024/2025 reproduces the committed pairs 1072/1251, 1558/1813 and
    # 1566/1805 **to the MW, all three**. Two transcription traps it exposed,
    # recorded so the next lane does not re-hit them: (a) the north set must
    # include the 22 MW Westley branch group, which the caiso-188 census
    # probe's transcription omits — without it every year lands 3-5 MW low;
    # (b) CAISO RENAMED that branch group `Westley-Los Banos` -> `Westley-Fink`
    # for delivery year 2025, so a name-keyed north set silently drops it in
    # 2025 alone. Spot tranches and every price are identical to the other
    # years, i.e. the same STATIC-FITTED-PENDING-MEASURED Tier-3 proxies the
    # G-26 label above already declares.
    "CAISO": {
        2022: [
            ("PNW_hydro_base", 1489.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1682.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
        2023: [
            ("PNW_hydro_base", 1072.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1251.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
        2024: [
            ("PNW_hydro_base", 1558.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1813.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
        2025: [
            ("PNW_hydro_base", 1566.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1805.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
    },
    # NYISO year-grounded measured ladders (derivation + sources in the static
    # IMPORT_TRANCHES["NYISO"] comment above; scripts/data/
    # derive_nyiso_import_tranches.py). Year texture is real market history: the
    # rung prices scale with each year's measured DA LMP (mean $31.1 / $36.7 /
    # $60.7), and the 2023 off-peak marginal (PJM_west rung) falls to $27.9 —
    # the fitted ladder's $34.2 was the audit-C6 over-price that pinned the
    # 2023 trough. Offline (actual-DA-driven, SIL-capped) reproduction of the
    # measured net import: 98% of volume every year, duration RMSE ≤328 MW.
    #
    # 2018-2022 added 2026-07-31 (NYISO out-of-training DATA READINESS, rule 22
    # Option-2 owner authorization; NO solve, NO score). Same producer, same
    # frozen formula, same two measured sources — `derive_nyiso_import_tranches.py
    # --years 2018 2019 2020 2021 2022` — run AFTER the out-of-training DA blocks
    # of actual_lmp_hourly_NYISO.parquet were re-derived on the fixed
    # chronological clock, so the Q-Q coupling pairs price and flow on one clock.
    # Byte-identity proof: re-running the producer over 2023-2025 reproduces the
    # committed in-sample rungs below EXACTLY, so these years are the same
    # derivation extended, not a re-fit. Data-change citation per rule 23
    # [R-FROZEN-DERIVE]: new years of the measured series.
    #   Reproduction quality is materially looser in the high-import years than
    #   in-sample (duration RMSE 643/488/307/662/719 MW for 2018-2022 vs the
    #   in-sample <=328 MW; hourly corr +0.13 in 2018): the ladder is measured,
    #   not fitted, so this is disclosed rather than corrected. Grade it before
    #   any authorized 2018/2020/2021/2022 use.
    #   H1-2026 is deliberately ABSENT. The producer's Q-Q coupling has no
    #   partial-year mode, and on the H1 window it returns a degenerate ladder
    #   (top rungs $174/$294/$510/$761 against a 1,096 MW mean net import, and
    #   a NEGATIVE diurnal correlation of -0.74 — its own reproduction check
    #   says it reproduces the shape backwards). Landing it would post a
    #   misaligned number; rule 14's misalignment clause says don't. Needs a
    #   partial-window methodology decision first.
    "NYISO": {
        2018: [
            ("HQ_hydro", 900.0, 11.09),
            ("IESO_Ontario", 690.0, 14.04),
            ("PJM_shoulder", 690.0, 16.69),
            ("PJM_west", 690.0, 19.76),
            ("eastern_mid", 690.0, 23.50),
            ("ISONE_tie", 690.0, 28.27),
            ("import_scarcity", 2670.0, 56.24),
        ],
        2019: [
            ("HQ_hydro", 900.0, 9.56),
            ("IESO_Ontario", 690.0, 12.05),
            ("PJM_shoulder", 690.0, 14.29),
            ("PJM_west", 690.0, 17.36),
            ("eastern_mid", 690.0, 20.98),
            ("ISONE_tie", 690.0, 25.10),
            ("import_scarcity", 2365.0, 43.68),
        ],
        2020: [
            ("HQ_hydro", 900.0, 6.16),
            ("IESO_Ontario", 690.0, 10.46),
            ("PJM_shoulder", 690.0, 12.72),
            ("PJM_west", 690.0, 15.11),
            ("eastern_mid", 690.0, 18.51),
            ("ISONE_tie", 690.0, 22.93),
            ("import_scarcity", 1955.0, 41.41),
        ],
        2021: [
            ("HQ_hydro", 900.0, 11.30),
            ("IESO_Ontario", 690.0, 13.52),
            ("PJM_shoulder", 690.0, 16.28),
            ("PJM_west", 690.0, 20.42),
            ("eastern_mid", 690.0, 26.01),
            ("ISONE_tie", 690.0, 33.42),
            ("import_scarcity", 2560.0, 61.00),
        ],
        2022: [
            ("HQ_hydro", 900.0, 25.16),
            ("IESO_Ontario", 690.0, 34.27),
            ("PJM_shoulder", 690.0, 41.12),
            ("PJM_west", 690.0, 46.94),
            ("eastern_mid", 690.0, 53.35),
            ("ISONE_tie", 690.0, 62.59),
            ("import_scarcity", 2760.0, 126.79),
        ],
        2023: [
            ("HQ_hydro", 900.0, 15.20),
            ("IESO_Ontario", 690.0, 18.67),
            ("PJM_shoulder", 690.0, 22.91),
            ("PJM_west", 690.0, 27.88),
            ("eastern_mid", 690.0, 33.61),
            ("ISONE_tie", 690.0, 40.23),
            ("import_scarcity", 2230.0, 71.66),
        ],
        2024: [
            ("HQ_hydro", 900.0, 20.97),
            ("IESO_Ontario", 690.0, 25.70),
            ("PJM_shoulder", 690.0, 29.85),
            ("PJM_west", 690.0, 35.02),
            ("eastern_mid", 690.0, 41.83),
            ("ISONE_tie", 690.0, 54.38),
            ("import_scarcity", 2120.0, 122.71),
        ],
        2025: [
            ("HQ_hydro", 900.0, 31.32),
            ("IESO_Ontario", 690.0, 44.09),
            ("PJM_shoulder", 690.0, 59.82),
            ("PJM_west", 690.0, 79.19),
            ("eastern_mid", 690.0, 102.99),
            ("ISONE_tie", 690.0, 128.54),
            ("import_scarcity", 1725.0, 208.77),
        ],
    },
    # NEISO: year-grounded measured ladders (derivation + sources in the
    # static IMPORT_TRANCHES["NEISO"] comment; scripts/
    # derive_neiso_import_tranches.py). Year texture is real market history:
    # HQ deliveries collapse 10.6 → 2.8 TWh across 2023-2025 as HQ's measured
    # opportunity cost (NYISO_HQ proxy) rises $24.6 → $56.0/MWh, so the
    # HQ_PhaseII rung carries a growing energy-limitation (water-value)
    # premium over the anchor (+$0.1 / +$11.1 / +$51.9); the NYISO_CT rungs
    # bracket the measured NPX parity each year. 2024 has no scarcity rung —
    # the measured p99.9 total import sits within the per-seam p98 rungs.
    #
    # 2019-2022 added 2026-08-14 (neiso-93 envelope repair) from the SAME
    # producer and the same three measured sources, after the deriver was
    # proved to re-derive the committed 2023-2025 ladders (see below).
    # Data-change citation per rule 23 [R-FROZEN-DERIVE]: a SOURCE-COVERAGE
    # extension — both upstream extracts were widened from 2023-2025 to
    # 2019-2025 this session — not a re-tune, and nothing is fitted to any
    # year's residual. Before this block an out-of-training year silently took
    # the POOLED static ladder, embedding late-period HQ water value and NY-NE
    # arbitrage into an earlier year on a system where imports are a large
    # share of supply.
    # The year texture the pooled curve was erasing is large and physical: mean
    # measured HQT import runs -1,576/-1,559/-1,532/-1,541 MW across 2019-2022
    # against -1,204/-694/-315 MW in 2023-2025, i.e. HQ delivered roughly five
    # times as much in 2019 as in 2025, and its measured opportunity cost
    # (NYISO_HQ anchor) was $19.07 then vs $55.99 now. So the early years'
    # HQ_PhaseII rungs price BELOW their anchor (-$3.2/-$1.0/-$5.5/-$8.6) where
    # 2025's prices +$51.9 above it. 2019-2022 carry no import_scarcity rung
    # (measured p99.9 total import sits inside the per-seam p98 rungs) and no
    # export_HQ sink (no measurable HQT export depth — NEISO imported on that
    # seam essentially every hour).
    "NEISO": {
        2019: [
            ("Highgate", 225.0, 9.95),
            ("HQ_PhaseII", 1930.0, 15.86),
            ("NB_north", 810.0, 27.22),
            ("NYISO_CT_base", 835.0, 22.51),
            ("NYISO_CT_peak", 835.0, 43.31),
        ],
        2020: [
            ("Highgate", 225.0, 6.33),
            ("HQ_PhaseII", 1885.0, 13.25),
            ("NB_north", 805.0, 25.04),
            ("NYISO_CT_base", 760.0, 15.18),
            ("NYISO_CT_peak", 760.0, 25.71),
        ],
        2021: [
            ("Highgate", 225.0, 11.52),
            ("HQ_PhaseII", 1870.0, 20.25),
            ("NB_north", 845.0, 47.33),
            ("NYISO_CT_base", 805.0, 44.72),
            ("NYISO_CT_peak", 805.0, 78.58),
        ],
        2022: [
            ("Highgate", 225.0, 14.02),
            ("HQ_PhaseII", 1880.0, 40.60),
            ("NB_north", 765.0, 89.88),
            ("NYISO_CT_base", 850.0, 90.26),
            ("NYISO_CT_peak", 850.0, 162.69),
        ],
        2023: [
            ("Highgate", 225.0, 17.00),
            ("HQ_PhaseII", 1595.0, 24.70),
            ("NB_north", 625.0, 35.28),
            ("NYISO_CT_base", 790.0, 31.17),
            ("NYISO_CT_peak", 790.0, 53.81),
            ("import_scarcity", 115.0, 265.42),
        ],
        2024: [
            ("Highgate", 225.0, 22.04),
            ("HQ_PhaseII", 1840.0, 44.22),
            ("NB_north", 605.0, 73.34),
            ("NYISO_CT_base", 870.0, 30.90),
            ("NYISO_CT_peak", 870.0, 51.76),
        ],
        2025: [
            ("Highgate", 225.0, 56.35),
            ("HQ_PhaseII", 1935.0, 107.89),
            ("NB_north", 655.0, 129.96),
            # 44.47, not the 44.48 committed 2026-07-06: the deriver emits
            # 44.47 and always has. Verified this session by re-running it
            # against the PRE-SESSION committed inputs, which also give 44.47,
            # so this is a 1-cent hand-transcription slip in the original
            # paste-in, NOT an effect of the 2019-2025 source widening. Set to
            # the producer's own output so the whole block re-derives exactly.
            ("NYISO_CT_base", 880.0, 44.47),
            ("NYISO_CT_peak", 880.0, 112.57),
            ("import_scarcity", 105.0, 299.86),
        ],
    },
}

# CAISO and PJM export sinks below are STATIC-FITTED-PENDING-MEASURED (gap
# register G-26, issue #1350 / audit C-6) — bare literals with no cited
# primary source and no by-year entry, unlike the NEISO export ladder in
# EXPORT_TRANCHES_BY_YEAR, which is a measured derivation (same Q-Q method as
# its import-side counterpart). Labelled per rule 24/rule 11 honesty; values
# unchanged.
EXPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    "CAISO": [
        ("export_solar", 2500.0, 8.0),
        ("export_curtail", 4000.0, 0.0),
    ],
    "PJM": [
        ("export_firm", 700.0, 36.0),
        ("export_peak", 1700.0, 30.0),
        ("export_mid", 1700.0, 24.0),
        ("export_shoulder", 1800.0, 19.0),
        ("export_offpeak", 1800.0, 18.0),
        ("export_trough", 2100.0, 16.0),
    ],
    "NYISO": [
        ("export_surplus", 600.0, 10.0),
    ],
    # NEISO: measured per-seam export sinks (same derivation + sources as
    # IMPORT_TRANCHES["NEISO"]; pooled 2023-2025). Sink prices carry the
    # no-wash clamp (every sink < cheapest import rung − $0.01): the pooled
    # HQ_import node cannot host simultaneous counterflow (wheel-through), so
    # a sink priced above an import rung would be a same-node wash-trade
    # money pump — a documented rule-14 reconciliation of the measured
    # thresholds to the single-node representation.
    "NEISO": [
        ("export_NYISO", 1030.0, 22.30),
        ("export_NB", 380.0, 21.84),
        ("export_HQ", 835.0, 19.86),
    ],
}

# Year-grounded export-sink ladders — the export-side mirror of
# IMPORT_TRANCHES_BY_YEAR, resolved identically (an unmapped ISO/year falls
# back to the static EXPORT_TRANCHES entry). Added 2026-07-06 with the NEISO
# measured seam ladders: the export side has the same real year texture as
# the import side (NEISO's 2025 export_HQ sink is 940 MW where 2023 had no
# measurable HQ export depth at all).
EXPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    # NEISO: derivation + sources in the IMPORT_TRANCHES["NEISO"] comment
    # (scripts/data/derive_neiso_import_tranches.py). 2023 has no export_HQ sink
    # (no measurable export depth on the HQT seam); sinks clamped by the
    # no-wash ordering where the measured threshold crossed the year's
    # cheapest import rung (2023 export sinks at $16.99 = Highgate $17.00 −
    # $0.01; 2024 export_NB at $22.03 = Highgate $22.04 − $0.01).
    # 2019-2022 added 2026-08-14 (neiso-93), same producer/sources/provenance
    # as the import side above — a SOURCE-COVERAGE extension per rule 23, with
    # the deriver first proved to re-derive the committed 2023-2025 sinks. None
    # of the four early years has an export_HQ sink (no measurable HQT export
    # depth), and BOTH sinks are no-wash clamped in every one of them, so each
    # year's two sinks sit a cent below that year's Highgate rung.
    "NEISO": {
        2019: [
            ("export_NYISO", 515.0, 9.94),
            ("export_NB", 130.0, 9.94),
        ],
        2020: [
            ("export_NYISO", 310.0, 6.32),
            ("export_NB", 175.0, 6.32),
        ],
        2021: [
            ("export_NYISO", 860.0, 11.51),
            ("export_NB", 280.0, 11.51),
        ],
        2022: [
            ("export_NYISO", 910.0, 14.01),
            ("export_NB", 295.0, 14.01),
        ],
        2023: [
            ("export_NYISO", 950.0, 16.99),
            ("export_NB", 180.0, 16.99),
        ],
        2024: [
            ("export_NYISO", 1110.0, 21.37),
            ("export_NB", 455.0, 22.03),
            ("export_HQ", 590.0, 18.06),
        ],
        2025: [
            ("export_NYISO", 1040.0, 27.12),
            ("export_NB", 365.0, 26.02),
            ("export_HQ", 940.0, 28.33),
        ],
    },
}

# Per-hub external zones and the corridor link each terminates on.
CAISO_PER_HUB_IMPORT_ZONES: dict[str, str] = {
    "MALIN": "WECC_PNW",
    "PALOVRDE": "WECC_DSW",
}

# CAISO import tranche → the WECC neighbor hub.
CAISO_IMPORT_TRANCHE_HUB: dict[str, str] = {
    "PNW_hydro_base": "MALIN",
    "PNW_midC": "MALIN",
    "DSW_solar_PV": "PALOVRDE",
    "DSW_CCGT": "PALOVRDE",
    "DSW_CT": "PALOVRDE",
    "WECC_scarcity": "PALOVRDE",
    "DSW_surplus_clean": "PALOVRDE",  # caiso-87 surplus-clean depth tranche
    "DSW_overnight_clean": "PALOVRDE",  # caiso-93 overnight clean depth tranche
    "DSW_daytime_clean": "PALOVRDE",  # caiso-94 daytime trigger-OFF clean depth
    "DSW_lateevening_clean": "PALOVRDE",  # caiso-269 hod 22-23 window-gap tranche
}

# CISO DIBA → corridor, split geographically at Path-15.
CAISO_CORRIDOR_DIBA: dict[str, str] = {
    "BPAT": "WECC_PNW",
    "PACW": "WECC_PNW",
    "BANC": "WECC_PNW",
    "TIDC": "WECC_PNW",
    "AZPS": "WECC_DSW",
    "SRP": "WECC_DSW",
    "WALC": "WECC_DSW",
    "NEVP": "WECC_DSW",
    "IID": "WECC_DSW",
    "LDWP": "WECC_DSW",
    "CEN": "WECC_DSW",
}

CAISO_CORRIDOR_FLOW_PERCENTILE: float = 95.0

# Percentile of the measured total CISO corridor net import, per (month ×
# hour-of-day) bucket, defining the SHAPE of the firm/contracted import base
# when ScenarioConfig.caiso_firm_import_shape is on (caiso-73). The MEDIAN is
# the revealed typical-day schedule of the contracted/self-scheduled base —
# robust to scarcity spikes (which belong to the spot tranches) and to outage
# dips. The shape is normalized to unit mean before use
# (eia_loader.measured_firm_import_shape), so this percentile choice sets only
# the profile, never the level — the level stays the published DMM RA-import ×
# MIC-split sizing of IMPORT_TRANCHES_BY_YEAR. Identification: measured
# (rule 23 — re-derives only when the EIA-930 extract extends). Source:
# EIA-930 BA-to-BA interchange, CISO extract.
CAISO_FIRM_IMPORT_SHAPE_PERCENTILE: float = 50.0

# Strength of the midday solar deliverability derate.
CAISO_CORRIDOR_ATC_SOLAR_K: float = 1.5

# Per-hub external zone → ISO topology links.
IMPORT_NODE_LINKS: dict[str, list[tuple[str, float]]] = {
    "PJM": [
        ("PJM_ComEd", 7500.0),
        ("PJM_AEP_Ohio", 4900.0),
        ("PJM_ATSI", 5800.0),
        ("PJM_Dominion", 6300.0),
        ("PJM_EMAAC", 5700.0),
    ],
    # NYISO border links follow the physical landing zones of the external
    # ties (the MISO-Illinois/Indiana/East reconciled-split precedent below:
    # the seam envelope is measured at BA level, the split follows tie
    # geography, and the SIL still caps the simultaneous total):
    #   * Upstate_West — the northern/western seams: Hydro-Québec
    #     (Chateauguay 1,999 MW + Cedars 325 MW), Ontario/IESO (~1,900 MW)
    #     and the PJM western AC ties; their summed capability far exceeds
    #     the conservative 3,000 MW aggregate retained here.
    #   * Capital_Hudson — the EASTERN AC seams, which land east of the
    #     Central-East interface: the PJM→NY AC capability via the Ramapo
    #     345 kV ties into Zone G (~1,000 MW of the PJM seam) and the
    #     ISO-NE→NY AC ties into Zones F/G (New Scotland / Pleasant Valley
    #     corridor, ~600 MW of the NE seam). Without this link every seam
    #     MW is forced through the Upstate node BEHIND the measured
    #     Central-East limit (1,450-2,725 MW monthly in 2023, pre-NY-Transco),
    #     so the pre-upgrade backcast cannot reproduce the real market's
    #     eastern import response — the 2023 downstate VOLL over-formation
    #     root-caused by the nyiso-63 phantom-outage re-audit (the stale
    #     outage extract's phantom eastern capacity was compensating for the
    #     missing eastern seam landing). Source: NYISO Gold Book external
    #     interconnections (tie landing points); the split re-homes part of
    #     the same lumped seam capability, adds no import energy (the
    #     monthly EIA-930 reconciliation band still pins net volumes) and
    #     stays under the published ~4,350 MW SIL.
    #   * NYC / Long_Island — the downstate HVDC merchant ties at their
    #     converter ratings (HTP 660 + Linden VFT 315 into J; Neptune 660 +
    #     Cross Sound 330 + Northport-Norwalk 286 into K).
    "NYISO": [
        ("Upstate_West", 3000.0),
        ("Capital_Hudson", 1600.0),
        ("NYC", 1000.0),
        ("Long_Island", 1200.0),
    ],
    # MISO border links re-pointed at the six-zone refinement: the 7,300 MW
    # eastern (PJM/IESO) seam envelope splits across its three physical border
    # zones — Illinois (ComEd-facing, the heaviest tie set), Indiana
    # (AEP-facing) and East (Michigan↔Ontario, ~2 GW interconnection) — a
    # reconciled split of the same measured 7,300 MW total (rule #12: the
    # seam envelope is measured at BA level, not per model zone; the split
    # follows the physical tie distribution and the per-seam band caps still
    # bound the seam total). West carries the SPP/Manitoba 4,000 MW seam;
    # South keeps its 3,000 MW southern (SOCO/TVA/AECI) seam unchanged.
    "MISO": [
        ("MISO-Illinois", 3300.0),
        ("MISO-Indiana", 2000.0),
        ("MISO-East", 2000.0),
        ("MISO-West", 4000.0),
        ("MISO-South", 3000.0),
    ],
}

# ISOs whose backcasts serve interchange through the priced import/export
# node by default (no --priced-interchange flag required).
PRICED_INTERCHANGE_DEFAULT_ISOS: frozenset[str] = frozenset({"CAISO"})


def resolve_priced_interchange(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--priced-interchange`` tri-state flag for ``iso``."""
    if flag is not None:
        return flag
    return iso in PRICED_INTERCHANGE_DEFAULT_ISOS


# ISOs whose backcasts enable the reference-price interface by default.
REFERENCE_PRICE_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


# NeighborInterface and INTERFACE_NEIGHBORS — moved from constants.py.
@dataclass
class NeighborInterface:
    """One external seam to a neighboring balancing authority.

    Every field is a forecast input (a forward gas/load driver) or a
    physically-pinned structural constant — none is tuned to a
    net-interchange target.
    """

    name: str
    ba_code: str
    gas_basis: float
    marginal_heat_rate: float
    hurdle: float
    interface_limit_mw: float
    border_zones: tuple[str, ...]
    proxy_ba: str | None = None
    load_shape_exponent: float = 1.0
    load_shape_kind: str = "gross"
    import_emission_factor: float | None = None
    hr_by_year: dict[int, float] | None = field(default=None, compare=False)
    firm_export_floor_by_year: dict[int, float] | None = field(
        default=None, compare=False
    )
    firm_import_floor_by_year: dict[int, float] | None = field(
        default=None, compare=False
    )


# Each PJM tie line in the settlement-grade tie-line file -> the NAMED
# reference-price interface it belongs to (the ``name`` of the matching
# :class:`NeighborInterface` in ``INTERFACE_NEIGHBORS["PJM"]`` below).
#
# WHY THIS EXISTS (pjm-151, rule 14 [R-ACCURATE]). The seam deliverability cap
# ``model.interchange.pjm.inject_pjm_seam_flow_limit`` needs a PER-NEIGHBOUR
# envelope. It used to obtain one by building a per-model-ZONE envelope from
# ``data.eia930.envelopes._PJM_TIE_ZONE`` and summing it over each neighbour's
# ``border_zones`` — two structures that attribute the same physical seam
# differently (``_PJM_TIE_ZONE`` puts the whole TVA tie on ``PJM_Dominion``;
# this file's TVA interface spans ``PJM_AEP_Ohio`` + ``PJM_Dominion``), and the
# zone buckets mix counterparties, so each neighbour's cap picked up other
# neighbours' ties. Measured on PJM's own file at p90
# (``scripts/probes/pjm151_seam_envelope_attribution.py``): the TVA EXPORT cap
# came out 124x / 53x / 40x the direct construction in 2023/24/25 and the LGEE
# one 33x / 42x / 26x, neither binding in any (month x hod) cell of 2023-24;
# while the LGEE IMPORT cap came out at 0 MW against a measured ~520-550 MW, so
# the repair loosens as well as tightens.
#
# This map removes the zone intermediary for that purpose. It is an IDENTITY,
# not a derivation and not a fitted share: PJM labels every tie with the
# counterparty balancing authority / utility itself, and those labels are the
# same five counterparties ``INTERFACE_NEIGHBORS["PJM"]`` names. Rule 5
# [R-NO-MAGIC] is satisfied by construction — there is no number here.
#
# ``_PJM_TIE_ZONE`` is NOT replaced and is not wrong: a per-ZONE attribution is
# the right grain for the objects that are per-zone (the measured zonal
# net-position schedule ``pjm_zonal_interchange`` feeds ``load_demand``, and the
# star topology's per-border link caps). The two structures answer different
# questions and only conflicted where one was summed to serve the other.
#
# Ties with no named interface map to ``None`` and enter no neighbour's cap.
# ``OVEC`` appears in ``_PJM_TIE_ZONE`` but in none of the 2023-2025 files.
PJM_TIE_NEIGHBOR: dict[str, str] = {
    # MISO — Illinois / Iowa / Wisconsin / Dakotas / Indiana / Michigan
    "AMIL": "MISO",
    "ALTE": "MISO",
    "ALTW": "MISO",
    "CWLP": "MISO",
    "MEC": "MISO",
    "WEC": "MISO",
    "MDU": "MISO",
    "LAGN": "MISO",
    "CIN": "MISO",
    "IPL": "MISO",
    "NIPS": "MISO",
    "SIGE": "MISO",
    "MECS": "MISO",
    # NYISO — the AC tie plus the three merchant HVDC / VFT cables
    "NYIS": "NYISO",
    "NEPT": "NYISO",
    "HUDS": "NYISO",
    "LIND": "NYISO",
    # Carolinas — Duke Progress East / West + Duke Carolinas
    "CPLE": "Carolinas",
    "CPLW": "Carolinas",
    "DUK": "Carolinas",
    # single-counterparty seams
    "TVA": "TVA",
    "LGEE": "LGEE",
}

INTERFACE_NEIGHBORS: dict[str, list[NeighborInterface]] = {
    "PJM": [
        NeighborInterface(
            name="MISO",
            ba_code="MISO",
            gas_basis=0.0,
            marginal_heat_rate=12.9,
            hurdle=1.0,
            interface_limit_mw=7300.0,
            border_zones=("PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI"),
            load_shape_exponent=1.60,
            hr_by_year={2023: 12.38, 2024: 13.92, 2025: 12.03},
            firm_export_floor_by_year={2023: 1250.0, 2024: 100.0, 2025: 0.0},
        ),
        NeighborInterface(
            name="NYISO",
            ba_code="NYIS",
            gas_basis=GAS_BASIS_DIFFERENTIAL["NYISO"],  # EIA-923 delivered-gas basis
            marginal_heat_rate=10.4,
            hurdle=1.0,
            interface_limit_mw=3900.0,
            border_zones=("PJM_EMAAC",),
            load_shape_exponent=1.63,
            hr_by_year={2023: 8.65, 2024: 10.85, 2025: 11.59},
            firm_export_floor_by_year={2023: 900.0, 2024: 1400.0, 2025: 1650.0},
        ),
        NeighborInterface(
            name="Carolinas",
            ba_code="DUK",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=2400.0,
            border_zones=("PJM_Dominion",),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="TVA",
            ba_code="TVA",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=1600.0,
            border_zones=("PJM_AEP_Ohio", "PJM_Dominion"),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="LGEE",
            ba_code="LGEE",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=1100.0,
            border_zones=("PJM_West_APS", "PJM_AEP_Ohio"),
            load_shape_exponent=1.60,
        ),
    ],
    "MISO": [
        NeighborInterface(
            name="PJM",
            ba_code="PJM",
            gas_basis=0.0,
            marginal_heat_rate=12.3,
            hurdle=2.0,
            interface_limit_mw=7300.0,
            border_zones=("MISO-Illinois", "MISO-Indiana", "MISO-East"),
            load_shape_exponent=1.0,
            hr_by_year={2023: 11.2, 2024: 13.49, 2025: 12.18},
            firm_import_floor_by_year={2023: 2615.0, 2024: 1710.0, 2025: 1135.0},
        ),
        NeighborInterface(
            name="SPP",
            ba_code="SWPP",
            gas_basis=0.0,
            marginal_heat_rate=10.0,
            hurdle=2.0,
            interface_limit_mw=4000.0,
            border_zones=("MISO-West",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 9.24, 2024: 10.65, 2025: 7.7},
        ),
        NeighborInterface(
            # ba_code adjudicated by capx S-123 / director item D9 (2026-08-30,
            # closing the item miso-183 handed forward): SOCO is the one
            # southern counterparty MISO essentially never exports to
            # (0.1-0.3% of gross; the measured seam is TVA at 79-86% of gross
            # export — FINDING-miso182-south-export-driver-2026-08-24.md), so
            # as the seam's representative BA it is a rule-14 [R-ACCURATE]
            # misfit. It is retained UNCHANGED because its only role — the
            # EIA-930 load shape of the gas-elastic reference-price fallback —
            # is unreachable at HEAD everywhere it matters: (a) backcast
            # keeper years 2023-2025 are fully displaced by the armed measured
            # seam ladder (MISO_SEAM_LADDER_BY_YEAR covers every band row);
            # (b) forecast configs leave reference_price_interface OFF (MISO
            # forecast interchange is the Manitoba firm block alone); (c) an
            # armed-interface solve year >= 2026 resolves NO seam load shape
            # at all (no extract covers those calendar years), so the fallback
            # this code names never fires there either.
            # CORRECTED by miso-252 (2026-09-10): that enumeration is right on
            # (a)-(c) and MISSES A FOURTH domain in which the fallback IS
            # reachable and DOES fire — an armed-interface BACKCAST year before
            # 2023, i.e. the holdout ladder. All four MISO seam ladder tables
            # cover exactly 2023-2025, so inject_miso_seam_ladder_prices returns
            # at its first guard for every pre-2023 year and EVERY seam band
            # takes this single flat reference price in place of an eight-band
            # rising curve. Measured consequence: the seam stops modulating and
            # becomes bang-bang — the 2021 rung sits within 1% of its own
            # maximum flow in 8,654 of 8,760 hours (98.8%), against 3 / 1 / 2
            # hours (0.0%) in the ladder-priced keeper years. It cannot reach
            # the train tier or any forecast, so no determination moves; the
            # ba_code conclusion below is UNAFFECTED and still stands. Repair is
            # blocked on data (eia-930-interchange covers 2023-2025 only) and a
            # frozen-band-shape substitute was REFUSED on measurement (import
            # curves move CV 0.32-0.49 across the three years). Full trace:
            # docs/FINDING-miso252-seam-fallback-and-the-923-block-2026-09-10.md
            # The accurate re-point
            # (ba_code="TVA" + an EIA-930 TVA hourly extract intake) is routed,
            # not shipped — it would change no reachable behaviour today.
            # FINDING-capx-s123-miso-adequacy-2026-08-30.md carries the full
            # trace, including the routed armed-interface degradation (seam
            # rows keep their mc=0 build placeholder when no shape resolves).
            name="South",
            ba_code="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=12.0,
            hurdle=2.0,
            interface_limit_mw=3000.0,
            border_zones=("MISO-South",),
            load_shape_exponent=1.0,
        ),
    ],
    "CAISO": [
        NeighborInterface(
            name="WECC_DSW",
            ba_code="SRP",
            proxy_ba="CISO",
            gas_basis=0.30,
            marginal_heat_rate=12.97,
            hurdle=4.0,
            interface_limit_mw=10623.0,
            # Palo Verde/WOR import terminates on SP15_rest after the 2026-07-09
            # SP15 local-area split (re-pointed off the removed SP15 zone).
            border_zones=("SP15_rest",),
            load_shape_kind="net",
            load_shape_exponent=1.0,
            import_emission_factor=0.37,
            hr_by_year={2023: 17.01, 2024: 13.39, 2025: 8.50},
        ),
        NeighborInterface(
            name="WECC_PNW",
            ba_code="BPAT",
            proxy_ba="CISO",
            gas_basis=-0.30,
            marginal_heat_rate=18.50,
            hurdle=3.0,
            interface_limit_mw=4800.0,
            border_zones=("NP15",),
            load_shape_kind="gross",
            load_shape_exponent=1.0,
            import_emission_factor=0.0,
            hr_by_year={2023: 22.50, 2024: 21.20, 2025: 11.80},
        ),
    ],
    # ------------------------------------------------------------------
    # SPP — registered 2026-09-06 by lane SPP-20 under owner rulings P2 (MISO
    # + AECI seams) and P3 (ERCOT DC ties), SPP desk sitting r#2
    # (docs/handoffs/spp-desk-ledger-2026-09.md §2). ALL THREE ARE
    # DEFAULT-OFF: ``reference_price_interface`` is off for SPP
    # (REFERENCE_PRICE_DEFAULT_ISOS is untouched), so the first keeper serves
    # the measured EIA-930 ``Total interchange`` schedule
    # (eia930.envelopes.spp_net_interchange) and these blocks are a
    # byte-identical no-op: SPP has NO IMPORT_ZONE / IMPORT_NODE_LINKS entry
    # (plan §7 G7), so get_interchange_spec returns an EMPTY spec for SPP and
    # these blocks build no rows even under --priced-interchange. Lane SPP-51
    # (2026-09-07, PRECOMMIT-spp-51 §2) traced that gap and DESIGNED the
    # topology any LP test needs — two external buses, one per side of the
    # SPP-53 N<->S corridor (a single shared bus linked to both zones is a
    # free wheeling path around the 3,400 MW link, the defect
    # split_miso_south_external_node removes for MISO's RDT) — and ROUTED it
    # rather than building it, because its own rule-29 phase-0 gate KILLED
    # the spread-clearing arm on the MEASURED record before any solve: the
    # measured SPP hub minus the measured MISO-West / MISO-South anchor
    # predicts the measured seam direction in 0.42-0.50 of non-hold hours
    # (corr ~0) in every year and both runs (PRECOMMIT-spp-51 §3.5;
    # FINDING-spp-51). The SPP<->MISO flow is scheduled / JOA / loop flow,
    # not a function of the hourly spread — the same finding MISO's own lane
    # made from its side (PRECOMMIT-miso233 §104-113), which is why MISO's
    # keeper prices this seam as a measured hourly-anchored OFFSET ladder.
    # The blocks are kept, corrected and default-off as the registered P2/P3
    # forward objects; matrix cells priced_interchange /
    # reference_price_interface read R for SPP.
    #
    # Rule 25 [R-ISO-SCOPE]: nothing here is copied from another ISO's
    # fitted values — every number is read off the COMMITTED anchor file
    # named per block with HENRY_HUB_TRAJECTORIES' historical 2.54 / 2.19 /
    # 3.52 $/MMBtu, by scripts/data/derive_neighbor_hr_by_year.py --iso SPP
    # (its per-ISO anchor map is SPP-51's repair of SPP-33 R1) and pinned by
    # tests/iso/spp/test_spp_priced_seams.py.
    #
    # THE HH + BASIS CORRECTION (SPP-33 §4 R2, made by SPP-51). The seam
    # prices as (henry_hub + gas_basis) x HR x shape
    # (data/neighbor_price.py: neighbor_gas_price returns HH + basis;
    # neighbor_reference_price / seam_tranche_prices multiply it by
    # neighbor_heat_rate), so the HR that reproduces a measured annual mean
    # divides by HH + BASIS. SPP-20's flat values divided by bare HH and
    # mis-constructed their own anchors by +14/-24/-43 %. Per block below:
    # ``hr_by_year`` = mean_anchor_RT[y] / ((HH[y] + basis) x K[y]) with
    # K = 1.000000 exactly (load_shape_exponent 1.0), the MEASURED backcast
    # value neighbor_heat_rate resolves first; ``marginal_heat_rate`` = the
    # mean of the three hr_by_year cells, the FORWARD fallback (there is no
    # _HR_GAS_ELASTIC key for any SPP seam — SPP-33 §5 R3, reported, not
    # fixed: ERCOT's fit is degenerate and the MISO legs' names are now
    # unique, so a later lane may key them if it derives one).
    #
    # ``hurdle`` = 2.0 $/MWh on every seam: the SPP<->MISO seam is ONE
    # physical object and MISO's side already registers it at 2.0, so a
    # different dead-band from this side would make the same seam clear on
    # two rules (rule 19); AECI and ERCOT take the same Tier-3 dead-band
    # (never fitted). ``load_shape_exponent`` = 1.0, the parameter-free
    # mean-preserving default. Border zones follow the P1 state map:
    # MISO-West borders the Dakotas/MN/IA (North) and MISO-South borders
    # AR/LA (South); AECI is the Missouri co-op island (North); the ERCOT DC
    # ties (Oklaunion 220 + Monticello 600 MW) land in Oklahoma / east Texas
    # (South).
    "SPP": [
        # THE MISO SEAM IS TWO BLOCKS, ONE PER BORDERING MISO ZONE (SPP-51,
        # replacing SPP-20's single "MISO" block that averaged the two zones
        # equal-weight). SPP-20 itself anchored on "the two MISO zones
        # physically adjacent to SPP — one price per zone"; the two zones are
        # different prices (RT 28.75 / 27.43 / 40.19 West vs 27.04 / 25.12 /
        # 35.45 South, $1.7-4.7 apart) that border DIFFERENT SPP zones and, in
        # any LP landing, must sit on different sides of the N<->S corridor.
        # One block per zone is the per-zone form of the same registration:
        # the equal-weight mean of the two legs' hr_by_year reproduces
        # SPP-33 §3's combined table (9.82 / 10.55 / 9.90) exactly, which is
        # the check that nothing was re-derived. Limits: the MMU's ">6,000 MW
        # of AC interties" (SOM 2025 §2.8, PDF p. 70) split by the measured
        # |flow| share of SPP's own MISO-member tie columns in
        # TieFlows_Sep2025.csv — West/North members (AMRN MEC ALTW DPC GRE
        # MDU NSP OTP) 59.1 %, Entergy + Cleco (EES CLEC) 40.9 % over 673 h
        # (rule 14 reconciliation of a total onto our two-zone boundary;
        # stated as a one-month measurement). The measured hourly envelope on
        # the EIA-930 SWPP->MISO DIBA (both legs summed) is -5,377 .. +3,469
        # MW. gas_basis = MISO's own delivered basis (the NYISO-seam
        # precedent for referencing a neighbour's registry value); both legs
        # shape on the MISO BA-level EIA-930 load (no West/South extract).
        NeighborInterface(
            # Anchor: actual_lmp_hourly_zonal_MISO.parquet, zone MISO-West
            # (the MINN hub), annual-mean RT 28.7524 / 27.4275 / 40.1926 $/MWh
            # over HH + 0.30 = 2.84 / 2.49 / 3.82 -> 10.12 / 11.02 / 10.52;
            # flat = their mean 10.55.
            name="MISO_West",
            ba_code="MISO",
            gas_basis=GAS_BASIS_DIFFERENTIAL["MISO"],
            marginal_heat_rate=10.55,
            hurdle=2.0,
            interface_limit_mw=3550.0,
            border_zones=("SPP-North",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 10.12, 2024: 11.02, 2025: 10.52},
        ),
        NeighborInterface(
            # Anchor: actual_lmp_hourly_zonal_MISO.parquet, zone MISO-South
            # (ARKANSAS / LOUISIANA / MS / TEXAS hubs, the zone mean),
            # annual-mean RT 27.0420 / 25.1159 / 35.4525 $/MWh over
            # 2.84 / 2.49 / 3.82 -> 9.52 / 10.09 / 9.28; flat = their mean 9.63.
            name="MISO_South",
            ba_code="MISO",
            gas_basis=GAS_BASIS_DIFFERENTIAL["MISO"],
            marginal_heat_rate=9.63,
            hurdle=2.0,
            interface_limit_mw=2450.0,
            border_zones=("SPP-South",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 9.52, 2024: 10.09, 2025: 9.28},
        ),
        NeighborInterface(
            # AECI (Associated Electric Cooperative, MO) — the LARGEST net
            # measured seam (+2.36 / +2.63 / +1.98 TWh/yr SPP export,
            # 72-81 % export hours; FINDING-spp-11 §4.1) yet it publishes NO
            # LMP and has no EIA-930 hourly extract in the tree. Its price
            # anchor is therefore a PROXY, declared as such: the SPP system
            # hub itself (actual_lmp_hourly_SPP.parquet, annual-mean RT
            # 23.4732 / 23.3135 / 27.1112 over HH - 0.26 = 2.28 / 1.93 / 3.26
            # -> 10.30 / 12.08 / 8.32; flat = their mean 10.23). Stated at the
            # gate (SPP-33 §3; measured by SPP-51 PRECOMMIT §3.2): a seam
            # priced at SPP's OWN realized hub cannot discriminate an
            # AECI-side signal — whatever residual the LP's SPP price carries
            # over the hub becomes seam flow by construction. Load shape off
            # SWPP via ``proxy_ba`` (the CAISO SRP/BPAT precedent).
            # gas_basis = SPP's own (Panhandle Eastern; AECI sits in the same
            # Southern Star / Panhandle gas region). Interface limit: SOM 2025
            # §2.8 (PDF p. 70) ">5,000 MW of AC" interties; measured hourly
            # max 1,492 MW.
            name="AECI",
            ba_code="AECI",
            proxy_ba="SWPP",
            gas_basis=GAS_BASIS_DIFFERENTIAL["SPP"],
            marginal_heat_rate=10.23,
            hurdle=2.0,
            interface_limit_mw=5000.0,
            border_zones=("SPP-North",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 10.30, 2024: 12.08, 2025: 8.32},
        ),
        NeighborInterface(
            # ERCOT DC ties (owner ruling P3: border SPP-South): Monticello
            # (DC-East, 600 MW) + Oklaunion (DC-North, 220 MW), CDR rating
            # sum 820 — the value constants.ERCOT_DC_TIE_ZONE_MAP["SWPP"]
            # carries from ERCOT's side and SPP-20 registered here.
            # LIMIT = 835 MW (SPP-51, rule 14 [R-ACCURATE]): the measured
            # EIA-930 SWPP->ERCO series clips at a hard +835 MW in all three
            # years (max 835; min -832 / -833 / -818), and SPP's own 1-minute
            # tie meter (ERCOTE + ERCOTN, SPP-14 TieFlows_Sep2025.csv) agrees
            # at corr +1.0000, mean difference 0.1 MW (FINDING-spp-33 §8) —
            # the ties' scheduled operating envelope on two independent
            # meters. At 820 an armed seam would refuse flows the meter
            # recorded in 547 / 128 / 21 h of 2023 / 2024 / 2025 (SPP-33
            # §7b). MISALIGNMENT, stated: 835 is a metered scheduled MAXIMUM,
            # not a published rating; the 15 MW gap to the CDR sum and the
            # 115 MW gap to the MMU's printed 720 (SOM 2025 §2.8) are recorded,
            # not explained. ERCOT's own registry row stays 820 (rule 25).
            # Measured anchor: actual_lmp_hourly_ERCOT.parquet system RT
            # 48.3568 / 26.8250 / 32.4906 over HH - 0.50 = 2.04 / 1.69 / 3.02
            # -> 23.70 / 15.87 / 10.76 (2023 carries ERCOT's scarcity summer,
            # which is why the per-year re-anchor matters most here); flat =
            # their mean 16.78. SPP-33 §5: this seam's gas-elasticity fit is
            # DEGENERATE (R2 0.0001, negative hr_phys) and must never be
            # keyed — the flat value is its forward price.
            name="ERCOT",
            ba_code="ERCO",
            gas_basis=GAS_BASIS_DIFFERENTIAL["ERCOT"],
            marginal_heat_rate=16.78,
            hurdle=2.0,
            interface_limit_mw=835.0,
            border_zones=("SPP-South",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 23.70, 2024: 15.87, 2025: 10.76},
        ),
    ],
    # ------------------------------------------------------------------
    # NWPP — registered 2026-09-14 by lane NWPP-20 under owner ruling N4
    # (NWPP desk sitting #4: "SERVED MEASURED INTERCHANGE, PRICED LINKS
    # DEFAULT-OFF"). ALL THREE ARE DEFAULT-OFF: ``reference_price_interface``
    # is off for NWPP (REFERENCE_PRICE_DEFAULT_ISOS is untouched) and NWPP has
    # NO IMPORT_ZONE / IMPORT_NODE_LINKS entry (plan §7 G7), so
    # get_interchange_spec returns an EMPTY spec and these blocks build no
    # rows even under --priced-interchange; the first keeper serves the
    # measured energy-balance schedule (eia930.envelopes.nwpp_net_interchange)
    # instead. A priced seam is UNVALIDATABLE in the first keeper because
    # NWPP-13 read NO — the footprint has no admissible hourly price series
    # — so these are the registered forward objects for lever NWPP-56 and
    # nothing more. The counterparty sets are MEASURED off the seventeen
    # per-counterparty DIBA files (NWPP-11), 2023-2025: CISO reports through
    # BPAT / NEVP / PACW; BCHA through BPAT and AESO through NWMT; every other
    # external counterparty (LDWP, BANC, AZPS, WACM, WALC, PNM, SRP, GWA, WWA,
    # and the WAUW<->SWPP tie into the Eastern Interconnection) is the
    # residual set named WECC_SW by the charter (gate G10) — a name that also
    # holds BANC (Sacramento) and two Montana BAs, stated here so it is never
    # read as "Desert Southwest only".
    #
    # Rule 25 [R-ISO-SCOPE]: no number here is another ISO's fitted value.
    # HR anchors divide a MEASURED committed price by (HENRY_HUB 2.54 / 2.19 /
    # 3.53 + basis) per year, the SPP-51 construction (hr_by_year measured,
    # marginal_heat_rate = their mean, the forward fallback); there is no
    # _HR_GAS_ELASTIC key for any NWPP seam (the G10 uniqueness assert holds:
    # no key names CAISO / WECC_SW / WECC_CAN). load_shape_exponent 1.0, the
    # parameter-free default. ``hurdle``: the NWPP<->CAISO seam is ONE
    # physical object and CAISO's side (WECC_PNW above) registers 3.0, so this
    # side takes 3.0 (rule 19); the two seams with no registered counterpart
    # take SPP's never-fitted Tier-3 dead-band 2.0.
    "NWPP": [
        NeighborInterface(
            # CAISO — the COI / Path 66 seam plus NEVP's southern-Nevada ties.
            # Anchor: the seam's OWN price on CAISO's side, the MALIN intertie
            # scheduling-point LMP (data/raw/_validation-source/wecc_intertie_
            # lmp_hourly_CAISO.parquet, hub MALIN): annual mean 49.728 /
            # 40.076 / 37.999 $/MWh over HH + CAISO basis 1.20 = 3.736 / 3.392
            # / 4.729 -> 13.31 / 11.81 / 8.04; flat = their mean 11.05.
            # Limit = Path 66 COI N->S rating 4,800 MW (WECC 2024 catalogue
            # printed p. 63 — the same number CAISO's WECC_import->NP15 link
            # carries, card N4's double-count exposure, routed) + NEVP->CISO
            # measured hourly maximum 1,933 MW = 6,733 MW; the measured
            # three-leg envelope reads max export 3,884-4,316 / max import
            # 1,424-1,737 MW. Border zones = the reporting BAs' zones.
            name="CAISO",
            ba_code="CISO",
            gas_basis=GAS_BASIS_DIFFERENTIAL["CAISO"],
            marginal_heat_rate=11.05,
            hurdle=3.0,
            interface_limit_mw=6733.0,
            border_zones=("NWPP-NW", "NWPP-OR", "NWPP-SNV"),
            load_shape_exponent=1.0,
            hr_by_year={2023: 13.31, 2024: 11.81, 2025: 8.04},
        ),
        NeighborInterface(
            # WECC_SW — LDWP (PDCI, Path 65: NW->S 3,220 MW, printed p. 62;
            # plus NEVP / PACE ties), BANC, AZPS, WACM, WALC, PNM, SRP, GWA,
            # WWA and the WAUW<->SWPP DC tie. ba_code LDWP is the largest leg
            # (BPAT +5.6 / NEVP -9.3 / PACE -0.1 TWh in 2024); it has no
            # hourly extract in the tree, so the load shape is proxied on
            # NEVP (the Desert-adjacent member). Anchor: CAISO's PALOVRDE
            # intertie scheduling-point LMP — the Desert-Southwest hub price,
            # measured, declared as the seam's PROXY anchor (no DSW ISO is
            # registered): 47.909 / 33.343 / 32.467 over HH + 0.0 (no DSW
            # registry basis exists) = 2.536 / 2.192 / 3.529 -> 18.89 / 15.21
            # / 9.20; flat = their mean 14.43. Limit = the measured 2024-2025
            # aggregate envelope maximum, 6,049 MW (2025 export; import max
            # 4,361 in 2024; p99 3,197-4,602) — the 2023 series carries one
            # 60,037 MW artifact hour and is not used for the limit. GRID's
            # PNM / SRP / WALC legs are in this counterparty set but are
            # Desert-Southwest resources, not footprint exports — see
            # nwpp_net_interchange.
            name="WECC_SW",
            ba_code="LDWP",
            proxy_ba="NEVP",
            gas_basis=0.0,
            marginal_heat_rate=14.43,
            hurdle=2.0,
            interface_limit_mw=6049.0,
            border_zones=("NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"),
            load_shape_exponent=1.0,
            hr_by_year={2023: 18.89, 2024: 15.21, 2025: 9.20},
        ),
        NeighborInterface(
            # WECC_CAN — BC Hydro (Path 3 Northwest-British Columbia, printed
            # p. 10: N->S 3,150 / S->N 3,000 MW, through BPAT) and AESO (Path
            # 83 MATL, 325 southbound / 300 northbound, through NWMT). Canada
            # is OUT of the footprint (ruling N1) and this is its exogenous
            # seam. No Canadian market price is committed; the anchor is the
            # footprint's OWN traded hub, the Mid-C Peak ICE index Powerex
            # clears against (data/raw/nwpp-weim/midc_peak_daily.parquet,
            # NWPP-13): daily weighted-average 87.07 / 61.52 / 46.41 $/MWh —
            # PEAK-ONLY and DAILY, so an upward-biased PROXY, declared — over
            # HH + NWPP basis -0.19 = 2.346 / 2.002 / 3.339 -> 37.11 / 30.73
            # / 13.90; flat = their mean 27.25. Limit = Path 3 N->S 3,150 +
            # Path 83 325 = 3,475 MW published; measured envelope max export
            # 2,690-2,743 / max import 2,312-2,362 MW sits inside it.
            name="WECC_CAN",
            ba_code="BCHA",
            proxy_ba="BPAT",
            gas_basis=GAS_BASIS_DIFFERENTIAL["NWPP"],
            marginal_heat_rate=27.25,
            hurdle=2.0,
            interface_limit_mw=3475.0,
            border_zones=("NWPP-NW", "NWPP-INLAND"),
            load_shape_exponent=1.0,
            hr_by_year={2023: 37.11, 2024: 30.73, 2025: 13.90},
        ),
    ],
    # SOCO — the Southern Company BALANCING AUTHORITY, registered 2026-09-14
    # by lane SOCO-20 (owner card S4, desk r#3: "served measured EIA-930
    # interchange for the first keeper"; the priced blocks below register
    # DEFAULT-OFF for lever SOCO-56 "with SOCO-12's published transfer
    # capability as their input"). ALL EIGHT BLOCKS ARE INERT until
    # ``reference_price_interface`` is armed for SOCO, which no keeper does.
    #
    # One block per counterparty in SOCO's own EIA-930 BA-to-BA book
    # (FINDING-soco-11 §4.3: nine DIBAs, zero NaN hours, no impossible
    # print), except SEPA — the Southeastern Power Administration is a
    # federal hydro MARKETER whose ~2 TWh/yr into SOCO is a contract
    # allocation, not a priced seam, and is left in the served schedule.
    # Names are ``SOCO_<DIBA>`` so none can ever share a ``_HR_GAS_ELASTIC``
    # key with PJM's ``TVA`` / ``Carolinas`` or SPP's ``MISO_South`` blocks
    # (rule 25; SOCO plan §7 gate G10).
    #
    # ``interface_limit_mw`` = the 2024 Reserve Margin Study's WINTER "Avg TC"
    # (Average Transfer Capability into the Southern Company System, Table
    # I.2; summer Table I.1 in each comment), transcribed by SOCO-12
    # (data/raw/soco-planning/README.md §4c) — the ruling's named input.
    # RULE 14 [R-ACCURATE] MISALIGNMENT, stated once for all eight: these are
    # adequacy-study AVERAGE import capabilities, not tie ratings, and the
    # measured 2023-2025 hourly envelope on each DIBA (SOCO-11 §4.3, recorded
    # per block) exceeds them by 3-25x — TVA 480 vs a measured -3,150 .. +3,007
    # MW range. An armed seam at these limits would refuse flows the meter
    # recorded in most hours; SOCO-56 reconciles the two before arming
    # (the SPP-51 ERCOT-tie precedent), and until then the blocks are off.
    #
    # ``marginal_heat_rate`` anchors are TIER-3, labelled, default-off:
    #   * SOCO_MISO — MISO-South zonal RT mean over HH + MISO's own basis, the
    #     construction SPP-51 used for the same MISO zone: 27.0420 / 25.1159 /
    #     35.4525 $/MWh (actual_lmp_hourly_zonal_MISO, zone MISO-South) over
    #     HH 2.536 / 2.192 / 3.529 + 0.30 = 2.836 / 2.492 / 3.829 -> 9.54 /
    #     10.08 / 9.26; flat = their mean 9.63. gas_basis = MISO's registry.
    #   * every other neighbour publishes NO LMP (TVA, Duke, Dominion SC,
    #     Santee Cooper, the Florida BAs). The 11.6 flat is the value PJM's
    #     registry already carries for the SAME TVA / Carolinas systems
    #     (INTERFACE_NEIGHBORS["PJM"], "SERC coal/nuclear-set, no organized
    #     LMP") — one physical neighbour, one anchor (rule 19) — extended to
    #     the Florida BAs as a labelled placeholder; PJM's affine fit
    #     (5.6, 14.2) is PJM's and is NOT keyed here (rule 25). The SOCO-33 /
    #     SOCO-56 derive replaces these (candidate anchor: the SOCO-13 EQR
    #     store carries per-seller transaction prices for every one of these
    #     counterparties into SOCO POD).
    # ``hurdle`` = 2.0 $/MWh, the Tier-3 dead-band SPP's seams carry (never
    # fitted); the SOCO<->MISO seam is ONE physical object and MISO's own
    # ``South`` block registers it at 2.0 (rule 19). ``load_shape_exponent``
    # = 1.0, the parameter-free default. Load shape: MISO off its own
    # extract; the Florida BAs off the ``FLA`` (Florida region) extract via
    # ``proxy_ba``; TVA / DUK / SCEG / SC — no EIA-930 extract in the tree —
    # off ``SOCO`` itself, the proxy PJM's registry already uses for TVA and
    # the Carolinas. ``border_zones`` follow geography: TVA borders north
    # AL / GA / MS; Entergy (MISO-South) borders Mississippi; the Carolinas
    # (DUK / SCEG / SC) border Georgia at the Savannah River; FPL borders
    # Georgia on the peninsula and Alabama through FPL-Northwest (the former
    # Gulf Power area); Progress Florida (FPC) and Tallahassee border
    # south Georgia.
    "SOCO": [
        NeighborInterface(
            # Winter Avg TC 478 (summer 480); measured 2023-25 envelope
            # -3,150 .. +3,007 MW, the one genuinely two-way SOCO seam
            # (27 / 18 / 28 % of hours exporting; SOCO-11 §4.3).
            name="SOCO_TVA",
            ba_code="TVA",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=478.0,
            border_zones=("SOCO_AL", "SOCO_GA", "SOCO_MS"),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # Winter Avg TC 2,374 (summer 1,791); measured envelope
            # -683 .. +1,780 MW, 91-95 % of hours exporting, +4.4-4.7 TWh/yr.
            name="SOCO_MISO",
            ba_code="MISO",
            gas_basis=GAS_BASIS_DIFFERENTIAL["MISO"],
            marginal_heat_rate=9.63,
            hurdle=2.0,
            interface_limit_mw=2374.0,
            border_zones=("SOCO_MS",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 9.54, 2024: 10.08, 2025: 9.26},
        ),
        NeighborInterface(
            # Duke Energy Carolinas. Winter Avg TC 407 (summer 34); measured
            # envelope -1,954 .. +863 MW, a near-unidirectional IMPORT
            # (-3.7 .. -4.2 TWh/yr; 6-12 % of hours exporting).
            name="SOCO_DUK",
            ba_code="DUK",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=407.0,
            border_zones=("SOCO_GA",),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # Dominion Energy South Carolina (SCEG). Winter Avg TC 126
            # (summer 59); measured envelope -75 .. +2,123 MW — SOCO's
            # LARGEST export seam, +7.1 / +8.8 / +9.8 TWh, ~100 % of hours.
            name="SOCO_SCEG",
            ba_code="SCEG",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=126.0,
            border_zones=("SOCO_GA",),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # Santee Cooper (South Carolina Public Service Authority, EIA-930
            # ``SC``). Winter Avg TC 533 (summer 280); measured envelope
            # -189 .. +1,242 MW, 96-100 % of hours exporting, +4.1-4.8 TWh.
            name="SOCO_SC",
            ba_code="SC",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=533.0,
            border_zones=("SOCO_GA",),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # Florida Power & Light incl. FPL-Northwest (the former Gulf
            # Power area, merged into the FPL BA 2021). Winter Avg TC 153 +
            # 1,164 = 1,317 (summer 96 + 546); measured envelope -1,280 ..
            # +2,843 MW, 77-85 % of hours exporting, +2.8-2.9 TWh/yr.
            name="SOCO_FPL",
            ba_code="FPL",
            proxy_ba="FLA",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=1317.0,
            border_zones=("SOCO_GA", "SOCO_AL"),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # Duke Energy Florida (Progress FL, EIA-930 ``FPC``). Winter Avg
            # TC 50 (summer 31); measured envelope -354 .. +313 MW, small and
            # drifting from balanced to import (+0.08 / -0.02 / -0.42 TWh).
            name="SOCO_FPC",
            ba_code="FPC",
            proxy_ba="FLA",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=50.0,
            border_zones=("SOCO_GA",),
            load_shape_exponent=1.0,
        ),
        NeighborInterface(
            # City of Tallahassee. Winter Avg TC 20 (summer 12); measured
            # envelope -91 .. +294 MW, 89-95 % of hours exporting, +0.6-0.7
            # TWh/yr.
            name="SOCO_TAL",
            ba_code="TAL",
            proxy_ba="FLA",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=2.0,
            interface_limit_mw=20.0,
            border_zones=("SOCO_GA",),
            load_shape_exponent=1.0,
        ),
    ],
}

# MISO per-seam measured BA-to-BA deliverability envelope.
MISO_SEAM_DIBA: dict[str, tuple[str, ...]] = {
    "PJM": ("PJM", "IESO"),
    "SPP": ("SWPP", "SPA"),
    "South": ("SOCO", "TVA", "AECI", "LGEE", "SIKE"),
    # Manitoba (MHEB) — the two-way seasonal hydro seam. Present unconditionally
    # so measured_seam_import_envelope builds its (month × hour-of-day) two-way
    # deliverability envelope from the measured MHEB flow; the envelope is
    # applied only to Manitoba's seam BANDS, which exist only when
    # ScenarioConfig.miso_manitoba_seam builds them (miso-74, replacing the
    # import-only firm block). With the flag off there are no Manitoba bands, so
    # the envelope/ladder Manitoba entries are inert (inject_miso_seam_flow_limit
    # / _inject_seam_ladder are row-driven — "if not rows: continue") and every
    # existing bundle replays byte-identically. Adding MHEB→Manitoba leaves the
    # PJM/SPP/South DIBA pools (and their envelopes) unchanged (MHEB was
    # previously in no seam and dropped).
    "Manitoba": ("MHEB",),
}

# PJM tie line (DataMiner act_sch_interchange ``tie_line``) → priced seam.
# The PJM counterpart of MISO_SEAM_DIBA, at tie level because PJM's canonical
# measured boundary is its own settlement-grade tie-line file
# (data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_
# interchange.csv — the file behind eia_loader.pjm_net_interchange and the
# pjm_seam_flow_limit envelopes), not the EIA-930 BA-to-BA product (whose PJM
# submission disagrees with both this meter and the counterparty meters on
# the MISO seam; scripts/data/derive_pjm_seam_ladders.py BOUNDARY NOTE). Each tie
# maps to the neighbor BA it physically interconnects: the NJ–NY merchant
# HVDC ties (Neptune / Hudson / Linden) pool into the NYISO seam; Duke
# Progress East/West pool with Duke Carolinas; every MISO-member tie —
# including the MECS Michigan interface and the OVEC / LAGN dynamic
# schedules — pools into the MISO seam.
PJM_SEAM_TIE: dict[str, tuple[str, ...]] = {
    "MISO": (
        "ALTE",
        "ALTW",
        "AMIL",
        "CIN",
        "CWLP",
        "IPL",
        "LAGN",
        "MDU",
        "MEC",
        "MECS",
        "NIPS",
        "OVEC",
        "SIGE",
        "WEC",
    ),
    "NYISO": ("NYIS", "NEPT", "HUDS", "LIND"),
    "Carolinas": ("DUK", "CPLE", "CPLW"),
    "TVA": ("TVA",),
    "LGEE": ("LGEE",),
}

# PJM's MISO-facing western border heat rates (for border_anchor re-anchor).
MISO_PJM_BORDER_HR_BY_YEAR: dict[int, float] = {
    2023: 10.99,
    2024: 12.90,
    2025: 11.40,
}

# MISO per-seam measured band-price ladders (audit C-6 closure for MISO;
# gap register G-23 residual "2025 import starvation"): the revealed seam
# supply curve, derived by scripts/data/derive_miso_seam_ladders.py from two
# measured sources — the EIA-930 MISO BA-to-BA seam flows (pooled onto the
# three priced seams by MISO_SEAM_DIBA) Q-Q duration-coupled with the
# measured MISO Day-Ahead hub LMP (external transactions schedule in the DA
# market). Band k of a seam's import side is priced at the DA quantile whose
# exceedance duration equals the measured duration of the seam flowing
# deeper than the band's midpoint (export side mirrored), on the existing
# SEAM_FLOW_TRANCHES (8) equal-band grid of each seam's interface limit —
# capacities and the measured (month x hour-of-day) deliverability envelopes
# are untouched; ONLY the price ladder is measured.
#
# Why (rule #1 — right market structure): the measured PJM+IESO seam flow is
# a firm/scheduled base (imports in 97.5-99.5% of ALL hours, p10 0.9-1.7 GW,
# hourly flow uncorrelated with the RT spread r=+0.06, 2025 annual RT spread
# $0.00 while 28 TWh flowed) — firm PTP service, grandfathered agreements
# and JOA firm flow entitlements, not spot-spread arbitrage. A hurdle-gated
# gas x HR x load-shape seam structurally deletes that flow in a zero-spread
# year (the miso-45 2025 gross imports 3.4 TWh vs actual net 19.0). The
# ladder encodes the revealed willingness-to-flow as a rising supply curve
# the LP still clears ECONOMICALLY hour by hour against its own internal
# price — nothing is forced (contrast the rejected miso_firm_import_floor
# min_gen pin): at price extremes even the base band backs off, and flows
# respond to changed model conditions.
#
# Identification (rule 23): measured-behaviour, frozen formula, zero fitted
# parameters — re-derives ONLY when the source data extends (a new EIA-930 /
# settlement year). Forward story (rules 12/13): the pooled 2023-2025 ladder
# printed by the derive script is the multi-year revealed seam structure
# (persistent firm-transfer base + arbitrage increment) that regenerates as
# the measured record extends; forecast years keep the gas-elastic
# reference-price formula (the same two-track design as hr_by_year).
#
# Boundary reconciliations (rule 14, documented in the derive script):
# IESO's Ontario tie pools into the PJM seam per MISO_SEAM_DIBA (one eastern
# seam; its surplus-baseload economics land in the cheap base bands); the
# coupling anchor is the MISO hub-mean DA (in-repo canonical), with the PJM
# western-border DA (pjm_border_lmp_hourly_MISO.parquet: $28.86/$28.56/
# $41.45) reported as the interpretability anchor; same-seam no-wash
# ordering (every export band below the seam's cheapest import band) holds
# naturally in all years — cross-seam counterflow (import PJM while
# exporting South) is real wheel-through the multi-link external node
# carries, bounded by the measured per-seam envelopes.
#
# Applied by transmission.inject_miso_seam_ladder_prices under
# ScenarioConfig.miso_seam_measured_ladder (default off, backcast years
# below only); displaces miso_pjm_border_anchor / miso_pjm_lmp_import_pricing
# on the rows it prices (alternatives, never stacked).
MISO_SEAM_LADDER_BY_YEAR: dict[int, dict[str, dict[str, tuple[float, ...]]]] = {
    # 2020 + 2021 added by miso-260 (2026-09-16), completing the back-fill
    # miso-252 could only half-finish. RULE 23 [R-FROZEN-DERIVE] BASIS: THE
    # SOURCE DATA UPDATED, on 2026-09-13, in the two commits that close the two
    # halves `FINDING-miso252-seam-fallback-and-the-923-block-2026-09-10.md` §3(a)
    # named as blocking:
    #   * `f9259f91` landed MISO's 2020 and 2021 hourly DA/RT hub LMPs into
    #     `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet` (8,760 h
    #     each; 2021 DA 8,736 of 8,760) — the price half of the Q-Q coupling,
    #     which in that finding's table read "2022-2026" and was the reason
    #     miso-252 could arm 2022 and no earlier year;
    #   * `00249712` widened `data/raw/eia-930-interchange/MISO interchange
    #     hourly.parquet` to 2020-2026 — the flow half, which that same table
    #     recorded as "2023-2025, binding blocker" and which is false at HEAD.
    # NOT re-derived because a residual moved, and 2022-2025 below are LEFT
    # EXACTLY AS COMMITTED: `scripts/data/derive_miso_seam_ladders.py` at HEAD
    # reproduces all four committed years at **256 of 256 entries, max |diff|
    # 0.0000** (`scripts/probes/_miso260_seam_phase0.py`), so their source data
    # did not change and rule 23 forbids touching them. The rows below are
    # verbatim from that same frozen script, same construction, no new
    # parameter: every number is a quantile of a measured series at a
    # structurally fixed depth grid (rules 21 [R-DOF] / 24 [R-REGISTRY] — zero
    # free parameters, zero new ScenarioConfig fields).
    #
    # WHAT IT REPLACES, measured off the incumbent keeper's own committed
    # `unit_hourly` seam-band marginal costs (2026-09-16-miso-259-coal-fuel):
    # with no entry `inject_miso_seam_ladder_prices` returns at its first guard
    # and every band takes the flat gas-elastic reference price, which in these
    # two years is **degenerate across the band grid** —
    #   2021 South: all 8 import bands at $41.97 and all 8 export bands at
    #     $37.97, against a measured import ladder rising $65.86 -> $266.26;
    #   2021 Manitoba: import AND export at the SAME $39.97, i.e. a same-seam
    #     wash the ladder's no-wash reconciliation forbids by construction;
    #   2021 PJM import: $48.49 -> $49.02, a $0.53 spread over eight bands,
    #     against a measured $16.17 -> $82.19;
    #   2020 South: all 16 bands at $26.55 / $22.55; 2020 Manitoba: $24.55 both
    #     directions.
    # A band grid with no spread clears all-or-nothing, which is the bang-bang
    # miso-252 §2.4 measured (2021: four PJM import bands pinned within 1% of
    # their own maximum in EVERY hour of the year). It also inverts the seam
    # merit order: 2021 prices PJM imports ($48.5) ABOVE their measured floor
    # ($16.17) and South imports ($41.97) BELOW theirs ($65.86).
    #
    # MEASURED PER-SEAM CONSEQUENCE under the incumbent, model net flow vs the
    # EIA-930 measured net (TWh), sum of |per-seam error| over the four seams:
    #   2020 **36.29**, 2021 **25.41** (both unarmed) against 2022 8.84,
    #   2023 4.11, 2025 5.21 (all ladder-armed). Two seams carry the WRONG SIGN
    #   in the unarmed years: 2021 SPP model -2.98 vs measured +2.15, 2021
    #   South model +1.69 vs measured -7.66, 2020 South model +3.44 vs -2.93.
    #
    # NO NEIGHBOUR OVERLAY FOR 2020/2021, the same data boundary 2022 states:
    # `pjm_border_lmp_hourly_MISO.parquet` and the SPP hub series both start in
    # 2023, so the overlay tables carry no 2020/2021 key and the code degrades
    # to THIS base ladder — never to an unpriced seam — which is the documented
    # behaviour of `miso_seam_neighbour_*`, not a new path.
    #
    # Anchor: MISO hub DA mean $22.99 (2020, 8,760 priced hours) / $40.97
    # (2021, 8,739). Derive-script notes: none — the same-seam no-wash ordering
    # holds naturally in both years, with no clamp.
    #
    # 2019 added by R-MISO (2026-09-24, AUDIT-backcast-inputs-860-heatrate-
    # outage-2026-09-24 §5.3.3, the owner's 2019-2025 span). RULE 23 BASIS: the
    # SOURCE DATA EXTENDED to 2019 in this lane — MISO 2019 DA/RT hub LMPs
    # (`fetch_miso_hub_lmp.py --years 2019`, the monthly `*_pr_xls` route,
    # 365/365 days) and MISO 2019 BA-to-BA interchange
    # (`fetch_eia930_interchange.py --ba MISO --source bulk --years 2019
    # --merge`, 11 DIBAs x 8,759 h; every pre-existing row byte-identical).
    # Verbatim from the frozen derive script; the 2020 row above re-derives at
    # HEAD unchanged. Offline P9: PJM +36.61 vs +36.55, SPP +5.92 vs +5.92,
    # South -2.84 vs -2.85, Manitoba +7.88 vs +7.86 TWh. Anchor: MISO hub DA
    # mean $26.98. No neighbour overlay (same data boundary as 2020-2022).
    2019: {
        "PJM": {
            "import": (11.21, 13.54, 16.73, 21.02, 25.14, 30.54, 39.29, 60.16),
            "export": (11.01, 11.01, 11.01, 11.01, 11.01, 11.01, 11.01, 11.01),
        },
        "SPP": {
            "import": (20.67, 26.45, 35.15, 50.35, 110.58, 195.17, 195.17, 195.17),
            "export": (16.35, 13.51, 12.56, 11.01, 11.01, 11.01, 11.01, 11.01),
        },
        "South": {
            "import": (29.25, 32.94, 38.07, 44.55, 54.66, 77.38, 130.42, 195.17),
            "export": (26.24, 23.80, 21.70, 19.86, 17.92, 16.19, 14.73, 13.46),
        },
        "Manitoba": {
            "import": (20.43, 23.26, 25.08, 27.61, 32.34, 195.17, 195.17, 195.17),
            "export": (16.81, 15.09, 11.01, 11.01, 11.01, 11.01, 11.01, 11.01),
        },
    },
    2020: {
        "PJM": {
            "import": (8.09, 8.09, 10.14, 14.14, 17.88, 21.60, 26.74, 37.26),
            "export": (7.44, 7.44, 7.44, 7.44, 7.44, 7.44, 7.44, 7.44),
        },
        "SPP": {
            "import": (19.88, 25.41, 36.84, 55.39, 71.10, 81.95, 81.95, 81.95),
            "export": (14.76, 11.18, 8.42, 7.44, 7.44, 7.44, 7.44, 7.44),
        },
        "South": {
            "import": (25.69, 30.39, 36.98, 45.51, 55.00, 62.85, 69.97, 81.95),
            "export": (22.75, 20.40, 18.03, 15.74, 13.22, 11.24, 9.66, 8.88),
        },
        # Manitoba (MHEB) two-way seam — miso-74; P9 +10.79 vs measured +10.80 TWh.
        "Manitoba": {
            "import": (14.24, 16.96, 19.11, 21.46, 24.75, 33.92, 44.87, 81.95),
            "export": (11.16, 9.78, 8.09, 7.44, 7.44, 7.44, 7.44, 7.44),
        },
    },
    2021: {
        "PJM": {
            "import": (16.17, 17.34, 19.62, 23.62, 33.60, 52.07, 69.72, 82.19),
            "export": (14.21, 14.21, 14.21, 14.21, 14.21, 14.21, 14.21, 14.21),
        },
        "SPP": {
            "import": (31.27, 56.65, 87.17, 252.38, 547.48, 547.48, 547.48, 547.48),
            "export": (22.59, 20.10, 18.92, 18.54, 18.08, 17.69, 17.02, 15.66),
        },
        "South": {
            "import": (65.86, 76.38, 85.33, 97.28, 123.47, 150.94, 193.47, 266.26),
            "export": (53.43, 43.33, 33.67, 27.17, 23.37, 20.90, 18.87, 17.13),
        },
        # Manitoba (MHEB) two-way seam — miso-74; P9 +2.87 vs measured +2.89 TWh.
        "Manitoba": {
            "import": (31.27, 38.03, 46.80, 59.05, 81.00, 357.64, 547.48, 547.48),
            "export": (26.52, 23.09, 20.74, 18.31, 14.21, 14.21, 14.21, 14.21),
        },
    },
    # 2022 added by miso-252 (2026-09-10). RULE 23 [R-FROZEN-DERIVE] BASIS: the
    # SOURCE DATA UPDATED — `data/raw/eia-930-interchange/MISO interchange
    # hourly.parquet` was back-filled to 2020-2022 through the fetch script's own
    # documented keyless bulk route, which is the flow-duration half of the Q-Q
    # coupling; the MISO hub DA half already covered 2022 (8,232 of 8,760 h).
    # NOT re-derived because a residual moved, and 2023-2025 below are LEFT
    # EXACTLY AS COMMITTED: their source data did not change (proven — the derive
    # reproduces byte-identical output against the committed and the back-filled
    # extract), so rule 23 forbids touching them.
    #
    # WHAT IT REPLACES: with no entry, `inject_miso_seam_ladder_prices` returns
    # at its first guard and every 2022 seam band took ONE flat gas-elastic /
    # flat-HR price — PJM $74.21, SPP $35.78, South $77.03 — in place of an
    # eight-band rising curve. That inverted the merit order across seams: PJM
    # imports were priced far ABOVE their measured floor ($25.61) while SPP and
    # South were priced far BELOW theirs ($59.52 / $129.10), so the model
    # exported to PJM while importing SPP energy that really clears at $59+.
    # Verbatim from `scripts/data/derive_miso_seam_ladders.py --years 2022`;
    # anchor MISO hub DA mean $69.89 (the bench's own 2022 DA mean is $69.90).
    #
    # NO NEIGHBOUR OVERLAY FOR 2022, by data boundary: the PJM western-border and
    # SPP hub series both start in 2023, so `derive_pjm_neighbour` yields a NaN
    # anchor for 2022. The overlay tables below therefore carry no 2022 key and
    # the code degrades to THIS base ladder — never to an unpriced seam — which
    # is the documented behaviour of `miso_seam_neighbour_*`, not a new path.
    2022: {
        "PJM": {
            "import": (25.61, 34.38, 42.73, 54.11, 68.33, 91.28, 127.92, 172.37),
            "export": (18.01, 18.01, 18.01, 18.01, 18.01, 18.01, 18.01, 18.01),
        },
        "SPP": {
            "import": (59.52, 80.62, 106.31, 135.64, 160.01, 213.49, 289.85, 409.62),
            "export": (45.56, 37.44, 29.58, 24.78, 18.01, 18.01, 18.01, 18.01),
        },
        "South": {
            "import": (129.10, 152.71, 182.08, 327.98, 475.04, 475.04, 475.04, 475.04),
            "export": (106.10, 89.43, 76.42, 66.74, 59.10, 53.10, 47.77, 43.31),
        },
        "Manitoba": {
            "import": (48.85, 52.24, 56.26, 60.99, 70.02, 90.66, 130.79, 457.70),
            "export": (45.30, 41.83, 38.03, 26.62, 18.01, 18.01, 18.01, 18.01),
        },
    },
    2023: {
        "PJM": {
            "import": (13.40, 16.25, 19.79, 24.09, 27.87, 32.78, 37.99, 46.55),
            "export": (12.34, 11.72, 11.72, 11.72, 11.72, 11.72, 11.72, 11.72),
        },
        "SPP": {
            "import": (33.03, 44.43, 64.03, 111.92, 177.08, 204.68, 204.68, 204.68),
            "export": (25.00, 20.03, 16.25, 13.59, 12.38, 11.72, 11.72, 11.72),
        },
        "South": {
            "import": (50.99, 63.58, 85.76, 112.47, 204.68, 204.68, 204.68, 204.68),
            "export": (43.04, 36.49, 31.69, 27.70, 24.74, 22.09, 19.70, 17.34),
        },
        # Manitoba (MHEB) two-way seam — miso-74; P9 +5.35 vs measured +5.39 TWh.
        "Manitoba": {
            "import": (27.11, 29.83, 33.38, 37.44, 44.61, 60.76, 94.92, 175.93),
            "export": (23.67, 21.05, 17.51, 12.60, 11.72, 11.72, 11.72, 11.72),
        },
    },
    2024: {
        "PJM": {
            "import": (14.01, 17.18, 20.92, 24.58, 29.38, 37.03, 50.15, 73.78),
            "export": (11.32, 9.48, 8.43, 8.43, 8.43, 8.43, 8.43, 8.43),
        },
        "SPP": {
            "import": (31.20, 49.28, 116.01, 239.27, 284.59, 284.59, 284.59, 284.59),
            "export": (23.13, 18.85, 16.19, 14.75, 13.39, 12.63, 12.20, 11.73),
        },
        "South": {
            "import": (57.86, 82.81, 163.02, 241.36, 260.66, 284.59, 284.59, 284.59),
            "export": (46.72, 38.67, 32.32, 27.61, 23.76, 20.81, 18.47, 16.00),
        },
        # Manitoba (MHEB) two-way seam — miso-74; P9 +2.99 vs measured +3.01 TWh.
        "Manitoba": {
            "import": (26.50, 29.47, 33.14, 37.56, 49.71, 140.89, 284.59, 284.59),
            "export": (22.93, 20.01, 16.58, 12.40, 8.43, 8.43, 8.43, 8.43),
        },
    },
    2025: {
        "PJM": {
            "import": (21.82, 25.85, 31.31, 37.36, 46.47, 59.25, 82.59, 121.91),
            "export": (18.36, 16.40, 16.40, 16.40, 16.40, 16.40, 16.40, 16.40),
        },
        "SPP": {
            "import": (40.09, 64.24, 112.65, 198.83, 247.99, 296.90, 310.00, 406.47),
            "export": (28.65, 23.85, 21.43, 19.60, 17.91, 17.34, 16.40, 16.40),
        },
        "South": {
            "import": (68.46, 87.90, 121.12, 155.42, 258.05, 327.25, 433.12, 433.12),
            "export": (53.00, 44.14, 37.04, 32.38, 29.43, 26.61, 24.29, 22.35),
        },
        # Manitoba (MHEB) two-way seam — miso-74; P9 -0.99 vs measured -0.99 TWh
        # (the drought-2025 net export the import-only firm block cannot carry).
        "Manitoba": {
            "import": (44.82, 55.36, 73.92, 113.71, 202.95, 284.12, 327.25, 433.12),
            "export": (36.78, 31.27, 24.35, 19.40, 16.40, 16.40, 16.40, 16.40),
        },
    },
}


# miso-225 — the NEIGHBOUR-ANCHORED PJM seam ladder (the D-2 5(i) repair, armed
# by ScenarioConfig.miso_seam_neighbour_anchored_ladder, default off).
#
# THE DEFECT.  Every band above is priced at a quantile of MISO's OWN DA hub, so
# an import's merit position moves with the model's own price: when MISO clears
# cheaply the bands go out of merit and imports contract.  The real market does
# the OPPOSITE.  Measured on the same EIA-930 record the ladder above is derived
# from: in the hours MISO's DA cleared below $20 the seam carried **6,021 MW**
# (2023) against a 4,674 MW all-hours mean — MISO imports MOST when it is
# cheapest, because the neighbour is cheaper still.  miso-224 §4.2 sized the
# consequence: an arm that lowers MISO's price cuts imports to 1.45 GW in exactly
# those hours against a measured 4.89 GW.
#
# THE REPAIR (owner ruling 2026-09-06, the ONE admissible form).  An import is
# offered at the EXPORTING market's own measured price, so its merit position
# depends on the neighbour's supply cost — the real driver — and not on MISO's.
# The construction is byte-for-byte the one above (same Q-Q duration coupling,
# same midpoint-depth grid on the same SEAM_FLOW_TRANCHES, same measured seam
# flows, same same-seam no-wash reconciliation); the ONLY change is which
# measured price series the coupling reads: the PJM western-border DA
# (data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet), which the
# incumbent derivation already loads as its own interpretability anchor.  Zero
# fitted parameters; identical rule-23 re-derive trigger.
#
# WHAT IT MOVES (scripts/probes/_miso225_seam_neighbour_phase0.py, zero-LP): the
# neighbour anchor lowers EVERY import band in EVERY year — bands 1-4 by a mean
# of -$3.81 / -$3.03 / -$2.32 in 2023 / 2024 / 2025 — and in the MISO sub-$20
# hours the PJM border price is the cheaper of the two in 85 / 80 / 74 % of
# hours.  The two series correlate 0.81-0.88: related, so this is not a second
# copy of MISO's own signal, and not identical, so the repricing is not cosmetic.
#
# PJM ONLY, and that is a DATA boundary, not a choice (rule 14 [R-ACCURATE]'s
# misalignment clause): no measured SPP or SOCO/TVA price series is held under
# data/raw, so those two seams keep the incumbent MISO-hub anchor and the gap is
# stated here rather than papered over with a proxy.  Entries here OVERLAY the
# table above per year and per seam — an absent year or seam falls through to the
# incumbent ladder, so the flag is byte-identical off and partial by design.
#
# Derived by scripts/data/derive_miso_seam_ladders.py::derive_pjm_neighbour
# (rule 23 [R-FROZEN-DERIVE] — re-derives ONLY when the EIA-930 or border-LMP
# record extends; a re-derivation commit cites the data change).
MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR: dict[
    int, dict[str, dict[str, tuple[float, ...]]]
] = {
    2023: {
        "PJM": {
            "import": (9.71, 12.74, 15.71, 20.11, 24.30, 28.80, 34.22, 41.96),
            "export": (7.73, 7.02, 7.02, 7.02, 7.02, 7.02, 7.02, 7.02),
        },
    },
    2024: {
        "PJM": {
            "import": (10.90, 13.45, 17.68, 22.52, 28.17, 35.63, 47.93, 67.64),
            "export": (8.69, 7.55, 7.48, 7.48, 7.48, 7.48, 7.48, 7.48),
        },
    },
    2025: {
        "PJM": {
            "import": (18.07, 23.32, 29.54, 36.12, 44.43, 57.39, 78.08, 110.74),
            "export": (13.99, 11.17, 11.17, 11.17, 11.17, 11.17, 11.17, 11.17),
        },
    },
}

# MISO PJM seam — the HOURLY neighbour-anchored ladder, as per-band OFFSETS
# (miso-231).  Applied price: pi_k(t) = pjm_border(t) + delta_k, assembled at
# solve time against the measured hourly western-border DA series
# (data.eia_loader.measured_miso_pjm_border_prices — the SAME series
# miso_pjm_lmp_import_pricing already reads hourly into the solve).  So band k
# clears in hour t iff spread(t) = MISO_price(t) - border(t) > delta_k.
#
# THE DEFECT IT ATTACKS.  miso-226 measured what the annual neighbour anchor
# above does and does not do, and the miso-230 keeper carries the non-claim
# forward verbatim: it repairs the ladder's LEVEL and not its RESPONSIVENESS.
#   corr(imports, own price)  keeper +0.750 -> arm +0.725  vs MEASURED -0.101
#   price-decile slope d1-d10 keeper -3,573 -> arm -3,217   vs MEASURED +1,322
# 3 % of the distance on the correlation, 10 % of the sign error on the slope.
# The structural reason: a FIXED price ladder is cleared by the LP against its
# OWN internal price, so re-anchoring moves where the bands sit and not WHEN
# they clear — the bands still leave merit exactly when MISO's price falls,
# which is when MISO actually imports most.
#
# THE CONSTRUCTION is the synthesis of two mechanisms already registered here:
# miso_pjm_lmp_import_pricing's hourly measured anchor (which prices every band
# identically, "no flow-responsive slope") and the Q-Q ladder's per-band depth
# slope (which is frozen annually).  This is the first with both.  Derived by
# derive_miso_seam_ladders.py::derive_pjm_neighbour_hourly — byte-for-byte the
# incumbent estimator (same _derive_one/qq coupling, same midpoint-depth grid on
# the same SEAM_FLOW_TRANCHES, same measured EIA-930 flows, same no-wash
# reconciliation), reading the DA-minus-border SPREAD instead of either price.
# Zero fitted parameters; identical rule-23 [R-FROZEN-DERIVE] re-derive trigger.
#
# WHAT PHASE 0 MEASURES (scripts/probes/_miso231_hourly_seam_phase0.py, zero-LP),
# driven by the MEASURED record alone and scored against the MEASURED seam flow:
#   corr(sim, measured flow)   incumbent -0.253 / annual -0.262 / HOURLY +0.271
# i.e. both fixed ladders are NEGATIVELY correlated with the measured hourly
# flow — they get the hour-to-hour seam backwards — and the hourly form flips the
# sign.  It closes ~58 % of the correlation distance (vs the annual form's 3 %)
# and ~48 % of the slope's sign error; the slope STAYS NEGATIVE, so this is a
# partial repair and is reported as one.  It also undoes the annual form's own
# reported volume cost: 4,649 / 3,673 / 3,199 MW against the measured 4,674 /
# 3,678 / 3,198 — within 0.5 % in all three years.
#
# WHY THIS IS NOT THE REFUTED SPREAD HURDLE (derive_miso_seam_ladders' own
# docstring records the seam being moved OFF a spread basis because the measured
# flow "is uncorrelated with the RT LMP spread, r = +0.06"):
#   (1) that is the RT spread against MISO's hub; the DA spread against the PJM
#       western border correlates with flow at +0.240 / +0.265 / +0.194, against
#       corr(flow, MISO DA) of -0.136 / -0.039 / -0.059;
#   (2) a hurdle is ONE threshold, this is the same 8-band ladder, and the Q-Q
#       coupling puts the shallow bands at NEGATIVE offsets (band 1 at -$29.17 in
#       2023) so they clear even when MISO is far below PJM — exactly the
#       "46-56 % of import MWh inside the $2 hurdle" a hurdle deletes.
#
# The deeply negative EXPORT offsets are the measured record speaking, not a
# clamp: the PJM seam almost never exports, so P[flow < -L] ~ 0 and the export
# quantile lands at the spread's sample floor — an effectively never-clearing
# rung, the same role the annual ladder's flat $7.02 export bands play.
#
# PJM ONLY, a DATA boundary rather than a choice (rule 14 [R-ACCURATE]): no
# measured SPP or SOCO/TVA price series is held under data/raw.  Entries here
# OVERLAY the per-year table and DISPLACE the annual neighbour overlay on any row
# they cover (alternatives, never stacked — rule 19 [R-ONE-MECH]); no hurdle is
# added on top, since delta_k is a measured spread quantile that already embeds
# delivery/wheeling.  Gated by ScenarioConfig.miso_seam_neighbour_hourly_ladder
# (default off); byte-identical when False, and a no-op for any year absent here
# or when the measured border series is unavailable.
MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR: dict[
    int, dict[str, dict[str, tuple[float, ...]]]
] = {
    2023: {
        "PJM": {
            "import": (-29.17, -9.84, -3.98, -0.11, 2.43, 4.62, 7.05, 11.20),
            "export": (
                -93.98,
                -121.47,
                -121.47,
                -121.47,
                -121.47,
                -121.47,
                -121.47,
                -121.47,
            ),
        },
    },
    2024: {
        "PJM": {
            "import": (-13.87, -6.23, -1.91, 1.04, 3.46, 6.18, 10.47, 19.31),
            "export": (
                -35.03,
                -65.32,
                -74.37,
                -74.37,
                -74.37,
                -74.37,
                -74.37,
                -74.37,
            ),
        },
    },
    2025: {
        "PJM": {
            "import": (-15.79, -6.12, -0.67, 2.64, 5.82, 9.68, 16.93, 29.86),
            "export": (
                -60.49,
                -166.07,
                -166.07,
                -166.07,
                -166.07,
                -166.07,
                -166.07,
                -166.07,
            ),
        },
    },
}

#: The pooled 2023-2025 HOURLY neighbour-anchored PJM offsets — the FORWARD
#: story (rule 13 [R-MEASURED]): the multi-year revealed spread structure a
#: forecast year regenerates from, the same two-track design the incumbent and
#: annual neighbour ladders both use.
MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_POOLED: dict[str, dict[str, tuple[float, ...]]] = {
    "PJM": {
        "import": (-15.84, -6.72, -1.88, 1.16, 3.59, 6.23, 9.66, 16.08),
        "export": (
            -56.08,
            -152.99,
            -166.07,
            -166.07,
            -166.07,
            -166.07,
            -166.07,
            -166.07,
        ),
    },
}


# MISO SPP seam — the HOURLY neighbour-anchored ladder, as per-band OFFSETS
# (miso-233).  Applied price: pi_k(t) = spp_hub(t) + delta_k, assembled at solve
# time against the measured hourly SPP NORTH hub DA series
# (data.eia_loader.measured_miso_spp_hub_prices).  So band k clears in hour t
# iff spread(t) = MISO_price(t) - spp_hub(t) > delta_k.  Derived by
# derive_miso_seam_ladders.py::derive_spp_neighbour_hourly — byte-for-byte the
# estimator MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR's PJM entry uses (same
# _derive_one/qq coupling, same midpoint-depth grid on the same
# SEAM_FLOW_TRANCHES, same measured EIA-930 flows, same no-wash reconciliation);
# the ONE degree of freedom exercised is which measured series the coupling
# reads.  Zero fitted parameters; identical rule-23 [R-FROZEN-DERIVE] trigger.
#
# THE DEFECT IT ATTACKS — measured from the miso-232 keeper's own committed
# sidecars, zero LP (scripts/probes/_miso233_seam_slope_anatomy_phase0.py and
# _miso233_allseam_slope_attribution_phase0.py).  miso-232 repaired the seam's
# measured-price decile slope in SIGN but reached only 11 / 8 / 72 % of the
# measured magnitude, and its non-claim 1 left the magnitude open.  The
# per-seam decomposition says the shortfall is NOT on the repaired seam:
#   seam    reconstructed slope d1-d10      MEASURED seam slope
#   PJM     +2,377 / +2,611 / +2,704 MW     +1,319 / +1,052 / +815 MW
#   SPP       -414 /   -481 /   -553 MW       +317 /   +466 /   -50 MW
#   South     -919 / -1,135 /   -827 MW        +72 /    +60 /  +646 MW
# PJM is already STEEPER than measured (its cheapest decile loses only
# 194-271 MW to the deliverability envelope, so the "deep bands k=6-8
# under-clear in cheap hours" reading is falsified).  What cancels it is the
# two seams still on the INCUMBENT fixed MISO-hub ladder, which carries the
# exact defect miso-226 named: cleared against the model's OWN price, a fixed
# ladder leaves merit when MISO's price falls — which is when MISO imports.
#
# WHY IT COULD NOT BE DONE BEFORE, AND CAN NOW.  derive_pjm_neighbour_hourly's
# docstring states the exclusion as a DATA boundary: "no measured SPP or
# SOCO/TVA price series is held under data/raw".  Lane SPP-14 landed one on
# 2026-09-06 — data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet,
# SPPNORTH_HUB / SPPSOUTH_HUB DA+RT hourly, 8,754 of 8,760 hours in each of
# 2023-2025, from SPP's own portal.spp.org file-browser API — so the boundary
# has moved for SPP.  Rule 14 [R-ACCURATE] is then directly on point: the
# incumbent SPP anchor is an ESTIMATE standing in for the neighbour's price and
# the measured neighbour price now exists.
#
# STATED AT THE GATE — this is WEAKER evidence than the PJM case was.  The
# miso-231 admissibility statistic does not transfer: corr(measured SPP seam
# flow, MISO DA - SPP hub DA) = +0.041 / -0.020 / +0.050, against
# corr(flow, MISO DA) = -0.216 / -0.377 / +0.082 and against the PJM spread's
# +0.240 / +0.265 / +0.194.  The spread is UNINFORMATIVE about this seam's
# hourly flow; what it does is remove the WRONG-SIGNED response rather than
# supply a right-signed one (simulated-vs-measured flow correlation
# -0.213 / -0.289 / +0.065 -> +0.011 / -0.107 / +0.050).  The case is
# structural and rule-14, never the statistic, and it is recorded here so no
# later reader mistakes one for the other.
#
# THE ANCHOR HUB IS SPPNORTH_HUB, named on TOPOLOGY before any ladder existed
# (rule 14's misalignment clause): the seam is one collapsed link hosted on the
# MISO_external (Midwest) bus, so its MISO-facing counterparty is SPP North.
# SPPSOUTH_HUB is computed as a sensitivity in the phase-0 probe and selects
# nothing — choosing the hub that scored better would be the fitted-mechanism
# selection rule 1 [R-STRUCT] forbids.
#
# SOUTH REMAINS EXCLUDED and remains a DATA boundary: SOCO and TVA are not
# organised markets and publish no hub or nodal price, so no measured series
# exists to anchor that seam on.  It keeps the incumbent ladder.
#
# Entries here OVERLAY the per-year table and DISPLACE the annual neighbour
# overlay on any row they cover (alternatives, never stacked — rule 19
# [R-ONE-MECH]).  Gated by ScenarioConfig.miso_seam_neighbour_hourly_spp, a
# SUB-GATE of miso_seam_neighbour_hourly_ladder (never armed apart from its
# family); byte-identical when False, and a no-op for any year absent here or
# when the measured hub series is unavailable.
#
# CROSS-YEAR PAIRING REPAIR (miso-243, 2026-09-07).  The values below are the
# output of the frozen estimator on the CORRECTLY PAIRED frame.  The superseded
# 2023-2025 entries were derived through a join defect: derive_spp_neighbour_hourly
# received df.loc[year], indexed by `hour` ALONE, while load_spp_hub_da() is
# (year, hour)-MultiIndexed, so pandas PARTIAL-joined on the shared level and
# paired each year's 8,760 MISO rows against ALL THREE hub years -- drawing the
# Q-Q quantile from a three-year MIXTURE of the spread instead of the year's own.
# The estimator's flow-exceedance TARGETS were unaffected (replicating a sample
# three times does not change a share); only the quantile's sample was wrong.
#
# This is a rule 23 [R-FROZEN-DERIVE] re-derive citing a CONSTRUCTION DEFECT --
# NOT a source-data update and NOT a residual that moved.  The case is rule 14
# [R-ACCURATE] and rule 23's own construction; rule 1 [R-STRUCT]: the pairing was
# NOT selected by which arm scores better, and both ladders are fully determined
# by the estimator before any solve runs.  Rule 21 [R-DOF]: ZERO free parameters
# -- the repair removes an error, it does not add a knob.  K is unchanged at
# SEAM_FLOW_TRANCHES, the midpoint-depth grid, the measured flow series, the
# SPPNORTH_HUB anchor and the no-wash reconciliation are byte-for-byte the
# incumbent ones, and the no-wash clamp raised no note.
#
# THE FALSIFIABLE EVIDENCE THAT THE REPAIR IS THE RIGHT ONE, and it could have
# failed: the estimator asserts an identity -- on the derive's own spread the
# dead band [delta_1^export, delta_1^import] captures P(|flow| <= mid_1) by
# construction.  Measured, |Z_derive - Z_target| moves
# 0.0395 / 0.0144 / 0.0089  ->  0.0003 / 0.0000 / 0.0001 (2023/2024/2025),
# against a bar of 0.005.  The identity is essentially exact once the pairing is
# right.  Diagnosis confirmed on three independently refuting legs plus a PJM
# no-join control (ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md);
# repair pre-registered and gated in
# PREREG-miso243-repair-the-spp-ladders-cross-year-pairing-2026-09-07.md and
# ADDENDUM-miso243-my-own-p2-leg-failed-and-the-screen-year-is-2024-2026-09-07.md.
#
# THE POOLED FORWARD LADDER BELOW IS NOT AFFECTED and is NOT touched: df.loc[a:b]
# keeps the MultiIndex, so its join was always proper (verified: it reproduces at
# 0.0).  Rule 13's forward story is intact; only this per-year backcast table was
# implicated.  The defect can no longer be reintroduced from any caller: the
# derive itself now raises if the join changes the row count, and the rule-23 pin
# test asserts that row count too.
#
# CLOCK REPAIR RE-DERIVE (miso-248, 2026-09-09).  The values below are the output
# of the SAME frozen estimator on the SAME correctly-paired frame, recomputed
# after the SOURCE SERIES was repaired.  THE CITED DATA CHANGE, which is the
# rule 23 [R-FROZEN-DERIVE] trigger and the only one:
#
#   86e45462 (2026-09-09) "Repair the SPP actual-LMP clock: the sidecar was on
#   SPP's GMT market interval, the model is on fixed CST"
#
# rewrote data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet --
# THE SERIES load_spp_hub_da() COUPLES AGAINST AND THE SERIES
# eia_loader.measured_miso_spp_hub_prices() APPLIES AT SOLVE TIME.  Every
# committed offset below the repair was drawn against a hub series six hours
# ahead of the clock the model dispatches on, so every quantile moved.
#
# WHY IT IS NOT OPTIONAL.  The applied offer is pi_k(t) = spp_hub(t) + delta_k
# and the ANCHOR is UNGATED DATA -- no ScenarioConfig field, no cache-key entry
# -- so every solve after 86e45462 carries the repaired anchor whether or not it
# carries repaired offsets.  Between the repair and this re-derive the applied
# price was a MIXTURE: repaired-clock anchor, pre-repair-clock offsets.  Measured
# at zero LP (results/calibration/_miso248_spp_rederive_phase0.json, P-2): the
# anchor moved in 8,758 / 8,757 / 8,758 of 8,760 hours in 2023 / 2024 / 2025.
#
# WHAT IS **NOT** IN SCOPE, measured rather than assumed (P-1): the incumbent
# MISO_SEAM_LADDER_BY_YEAR reproduces its derivation at 192/192 entries, max
# abs 0.000000 -- derive() couples the seam flow duration curve to the MISO hub
# DA and never reads an SPP price, so the repair cannot reach it and it is
# untouched here.
#
# Rule 1 [R-STRUCT] / rule 14 [R-ACCURATE]: the trigger is the source-data
# repair, NEVER a residual -- no criterion, band or actual appears in the
# selection of anything below.  Rule 21 [R-DOF]: ZERO free parameters.  K stays
# at SEAM_FLOW_TRANCHES; the midpoint-depth grid, the measured EIA-930 flow
# series, the SPPNORTH_HUB anchor and the no-wash reconciliation are byte-for-
# byte the incumbent ones; the no-wash clamp raised no note.  The miso-243
# row-count pin holds in all three years (8,760 -> 8,760), so this is a source
# change and not a recurrence of the cross-year join defect.
#
# Pre-registered in PREREG-miso248-the-spp-hourly-ladder-rederive-on-the-
# repaired-clock-2026-09-09.md; phase 0 and the G-DRIFT audit in
# ADDENDUM-miso248-phase0-and-G-DRIFT-the-handoffs-table-name-is-corrected-
# 2026-09-09.md.
MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR: dict[
    int, dict[str, dict[str, tuple[float, ...]]]
] = {
    2023: {
        "SPP": {
            "import": (10.62, 25.73, 43.07, 62.47, 83.98, 90.56, 90.56, 90.56),
            "export": (
                0.24,
                -10.16,
                -25.87,
                -56.57,
                -153.04,
                -166.65,
                -166.65,
                -166.65,
            ),
        },
    },
    2024: {
        "SPP": {
            "import": (14.40, 33.33, 56.44, 109.27, 203.29, 203.29, 203.29, 203.29),
            "export": (2.84, -6.48, -14.46, -20.33, -27.41, -32.26, -36.24, -47.02),
        },
    },
    2025: {
        "SPP": {
            "import": (16.86, 37.50, 67.75, 140.17, 182.10, 232.18, 252.79, 290.12),
            "export": (
                0.34,
                -10.42,
                -18.49,
                -28.01,
                -45.96,
                -69.66,
                -140.45,
                -140.45,
            ),
        },
    },
}

#: The pooled 2023-2025 HOURLY neighbour-anchored SPP offsets — the FORWARD
#: story (rule 13 [R-MEASURED]): the multi-year revealed spread structure a
#: forecast year regenerates from, the same two-track design every other MISO
#: seam ladder uses.
MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED: dict[
    str, dict[str, tuple[float, ...]]
] = {
    "SPP": {
        # miso-248: re-derived on the 86e45462 clock repair, the same rule-23
        # trigger and the same frozen estimator as the per-year table above.
        # NO CONSUMER IN src/ -- this table is the rule-13 forward-story record
        # and reaches no solve -- so it moves nothing; it is re-derived so the
        # forward story and the backcast table stand on ONE clock.
        "import": (13.78, 32.17, 56.75, 111.27, 181.99, 232.18, 252.79, 290.12),
        "export": (1.19, -8.81, -18.30, -27.69, -40.28, -51.92, -68.67, -86.97),
    },
}


#: The pooled 2023-2025 neighbour-anchored PJM ladder — the FORWARD story
#: (rule 13): the multi-year revealed neighbour-priced seam structure a forecast
#: year regenerates from, the same two-track design the incumbent ladder uses.
MISO_SEAM_LADDER_NEIGHBOUR_POOLED: dict[str, dict[str, tuple[float, ...]]] = {
    "PJM": {
        "import": (12.39, 15.87, 20.44, 25.30, 30.72, 37.50, 47.58, 65.30),
        "export": (9.47, 7.48, 7.02, 7.02, 7.02, 7.02, 7.02, 7.02),
    },
}


# PJM per-seam measured band-price ladders (the MISO/NEISO audit-C-6 pattern
# applied to PJM; pjm-95 C1 root-cause lead "2023 interchange duration miss"):
# the revealed seam supply curve, derived by scripts/data/derive_pjm_seam_ladders.py
# from two measured sources — PJM's settlement-grade tie-line interchange
# (data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_
# interchange.csv, pooled onto the five priced seams by PJM_SEAM_TIE) Q-Q
# duration-coupled with the measured PJM Day-Ahead system LMP
# (actual_lmp_hourly_PJM.parquet; external transactions schedule in the DA
# market). Band k of a seam's import side is priced at the DA quantile whose
# exceedance duration equals the measured duration of the seam flowing deeper
# than the band's midpoint (export side mirrored), on the existing
# SEAM_FLOW_TRANCHES (8) equal-band grid of each seam's interface limit —
# capacities and the measured per-border (month x hour-of-day) deliverability
# envelopes (pjm_seam_flow_limit) are untouched; ONLY the price ladder is
# measured.
#
# Why (rule #1 — right market structure): the measured PJM interchange is
# direction-STRUCTURAL, not spread-driven — PJM exports to MISO/NYISO in
# ~97-100% of ALL hours (2023 import hours 0.4%/0.1%) while importing from
# the south (Carolinas/TVA/LGEE, 77-97% of hours): firm PTP service,
# long-term schedules and JOA entitlements revealed only statistically. The
# hurdle-gated gas x HR x load-shape seam clears on the hourly spot spread
# and structurally inverts that record (pjm-95 2023: imports in 46% of hours
# vs measured ~2%, diurnal corr -0.50 — phantom imports that displace
# CC_REGULAR dispatch, the C1 FAIL). The ladder encodes the revealed
# willingness-to-flow as a rising supply curve the LP still clears
# ECONOMICALLY hour by hour against its own internal price — nothing is
# forced: at price extremes even the base band backs off, and flows respond
# to changed model conditions. Import rungs at the sample extreme (e.g.
# $308.05 = the 2023 DA max) are bands deeper than the measured record's
# deepest flow — effectively never-clearing scarcity rungs, kept so the
# capability exists at the measured price of using it.
#
# Identification (rule 23): measured-behaviour, frozen formula, zero fitted
# parameters — re-derives ONLY when the source data extends (a new tie-line /
# settlement year). Forward story (rules 12/13): the pooled 2023-2025 ladder
# printed by the derive script is the multi-year revealed seam structure
# (persistent firm-transfer base + arbitrage increment) that regenerates as
# the measured record extends; forecast years keep the gas-elastic
# reference-price formula (the same two-track design as hr_by_year).
#
# Boundary reconciliations (rule 14, documented in the derive script):
# the tie-line meter is the chosen boundary (PJM's EIA-930 submission
# disagrees with it AND with the counterparty meters on the MISO seam —
# 56.6 vs 35.3 vs MISO's own 33.5 TWh in 2023; the tie file is the boundary
# the model already uses in pjm_net_interchange and the seam envelopes);
# offline P9 reproduces every seam's measured volume within ±0.06 TWh and
# the import-hour shares (MISO 0-1% vs 0-2% measured). Same-seam no-wash
# ordering held naturally in every year written before 2026-09-19 (no clamp
# fired); pjm-h11's 2020 row is the first where one does (MISO export band 1
# $66.94 -> $66.93), which is the reconciliation working, not a defect —
# 2020's MISO seam exports in essentially all hours, so its deepest export
# sink and its cheapest import band both land on the year's own DA maximum.
# Cross-seam
# counterflow (import TVA while exporting MISO) is real wheel-through the
# multi-link external node carries, bounded by the measured envelopes.
#
# Applied by transmission.inject_pjm_seam_ladder_prices under
# ScenarioConfig.pjm_seam_measured_ladder (default off, backcast years below
# only); displaces the firm scheduled-export floor
# (inject_reference_price_firm_export) on the years it covers — the firm
# base the floor pinned is exactly the deep-duration structure the ladder
# prices (alternatives, never stacked; rule 19).
#
# EXTENDED to 2019 / 2021 / 2022 on 2026-08-07 (session pjm-160, owner
# decision "does the KEEPER reproduce 2022 — derive the ladder first"). This
# is a rule-23 re-derivation because the SOURCE DATA EXTENDS, not because a
# residual moved: derive_pjm_seam_ladders.py runs the FROZEN formula over
# PJM_<year>_import_export_act_sch_interchange.csv (2018-2025 on disk) and
# actual_lmp_hourly_PJM.parquet `da` (2018-2025), and both inputs already
# covered these years. No parameter is introduced and the 2023-2025 entries
# are byte-identical (verified against the prior file).
#
# WHY IT MATTERS BEYOND TIDINESS: outside the years listed here PJM's seam
# runs the FORECAST track (the gas-elastic reference-price formula), because
# neither this ladder nor firm_export_floor_by_year has an entry — so the
# already-spent 2022 touchpoint did NOT run the keeper's own seam
# representation, in the channel carrying PJM's largest single-signed volume
# error. Adding 2022 is what makes a 2022 re-run a test of the keeper.
# The ladder remains NOT forecastable by construction (it needs that year's
# realized flows and prices); forecast years still fall through to the
# gas-elastic formula, and that two-track design is unchanged.
# Offline P9 reproduction of the added years: every seam's measured volume
# within ±0.02 TWh, duration RMSE 40-280 MW, import-hour shares within a few
# points — the same quality as 2023-2025.
# Evidence: results/calibration/ASSESSMENT-pjm160-final-declaration-2026-08-06.md §11.
PJM_SEAM_LADDER_BY_YEAR: dict[int, dict[str, dict[str, tuple[float, ...]]]] = {
    2019: {
        "MISO": {
            "import": (156.18, 156.18, 156.18, 156.18, 156.18, 156.18, 156.18, 156.18),
            "export": (100.41, 47.78, 33.55, 25.49, 20.82, 17.07, 13.41, 10.39),
        },
        "NYISO": {
            "import": (61.69, 131.38, 156.18, 156.18, 156.18, 156.18, 156.18, 156.18),
            "export": (40.59, 31.21, 24.7, 20.77, 17.88, 14.81, 12.47, 9.46),
        },
        "Carolinas": {
            "import": (22.34, 25.75, 29.84, 35.98, 44.48, 66.51, 93.61, 123.09),
            "export": (19.47, 17.47, 15.47, 14.06, 12.78, 11.92, 10.93, 8.6),
        },
        "TVA": {
            "import": (16.52, 18.85, 21.5, 24.33, 28.41, 34.35, 40.88, 49.94),
            "export": (14.65, 13.5, 12.2, 10.39, 8.6, 8.18, 8.18, 8.18),
        },
        "LGEE": {
            "import": (18.99, 21.36, 24.08, 26.85, 30.35, 34.72, 39.6, 49.34),
            "export": (16.99, 14.34, 12.17, 8.38, 8.18, 8.18, 8.18, 8.18),
        },
    },
    # 2020 ADDED by pjm-h11 (2026-09-19), closing the STALE-INVARIANT gap
    # pjm-h10 found: this table covered {2019, 2021..2025} and
    # firm_export_floor_by_year covers only 2023-2025, so PJM's keeper year
    # 2020 ran NEITHER measured seam mechanism and fell through to the
    # FORECAST gas-elastic reference-price track. pjm-160 extended the table to
    # 2019/2021/2022 and skipped 2020 -- correct then, because the keeper span
    # was 2023-2025 and the touchpoint reached back only to 2021; pjm-173
    # verified "covers every year PJM solves" on that span. 2020 entered PJM's
    # solved span later with pjm_d4_4_TP and nothing re-checked the claim.
    #
    # Rule 23 [R-FROZEN-DERIVE] re-derivation, ZERO new parameters: the frozen
    # Q-Q duration coupling of scripts/data/derive_pjm_seam_ladders.py over
    # sources that already cover 2020 (PJM_2020_import_export_act_sch_
    # interchange.csv; actual_lmp_hourly_PJM.parquet carries 2018-2025). Rule 21
    # [R-DOF]: every number is a quantile of a measured series at a structurally
    # fixed depth grid. Rule 24 [R-REGISTRY]: no ScenarioConfig field is added --
    # this is one key in an existing registry.
    #
    # VERIFIED before the row was written (PRECOMMIT-pjm-h11-2026-09-19.md §3.2):
    #   * adding 2020 to the estimator's frame moves NOTHING on any existing
    #     year -- 240 shared rungs compared against the original --years
    #     2023 2024 2025 derivation, 0 moved; 2019/2021/2022 reproduce the
    #     committed rows exactly.
    #   * export rungs monotone descending, import ascending, all five seams.
    #     One no-wash clamp (MISO export band 1 $66.94 -> $66.93), the same
    #     same-seam reconciliation every other year carries.
    #   * pjm-160's own acceptance bar met: offline P9 volume error <= 0.04 TWh
    #     (MISO -38.00 vs -38.04 actual, NYISO -10.13 vs -10.14, Carolinas
    #     -0.47 vs -0.47, TVA +6.24 vs +6.25, LGEE +0.77 vs +0.76), duration
    #     RMSE 40-276 MW, import-hour shares within 2-11 points.
    #
    # STATED AGAINST INTEREST, because rule 1 [R-STRUCT] requires it: this is
    # PREDICTED TO MAKE 2020's EXPORT RESIDUAL WORSE, quantified ex ante at zero
    # LP. 2020 currently has the SMALLEST shortfall of any PJM year (-2.816 TWh
    # against -8.5..-13.5 elsewhere) precisely BECAUSE the unmechanised forecast
    # track exports more; this ladder's GROSS ceiling at the model's own 2020
    # price is 37.340 TWh, BELOW the 38.810 TWh net the forecast track delivers
    # today, against 41.626 measured. The case is rules 14 [R-ACCURATE] / 23 --
    # a keeper year must run the keeper's own mechanism, and a small residual
    # reached through the wrong mechanism is the compensating estimate rule 14
    # describes -- and it is NOT a residual argument. If the residual worsens the
    # mechanism STAYS IN and the real root cause gets fixed. The root cause this
    # points at: 2020's model-price-to-measured-DA gap is 13.441 TWh, the largest
    # of any year (next 2021 at 7.82), the same defect as its CC_REGULAR +7.5 /
    # COAL_BIT +16.9 TWh over-run. The ladder converts a hidden price error into
    # a visible volume error, which is the point.
    2020: {
        "MISO": {
            "import": (66.94, 66.94, 66.94, 66.94, 66.94, 66.94, 66.94, 66.94),
            "export": (66.93, 57.12, 36.2, 25.46, 20.05, 15.95, 11.93, 8.68),
        },
        "NYISO": {
            "import": (64.23, 66.94, 66.94, 66.94, 66.94, 66.94, 66.94, 66.94),
            "export": (36.2, 22.34, 17.55, 14.66, 12.19, 9.93, 8.79, 7.35),
        },
        "Carolinas": {
            "import": (20.67, 24.51, 30.84, 37.56, 46.52, 58.22, 66.94, 66.94),
            "export": (17.88, 15.39, 13.03, 11.28, 9.85, 8.82, 5.31, 5.31),
        },
        "TVA": {
            "import": (11.76, 13.71, 15.82, 18.28, 21.41, 25.95, 34.18, 48.42),
            "export": (10.32, 9.2, 8.11, 5.31, 5.31, 5.31, 5.31, 5.31),
        },
        "LGEE": {
            "import": (18.24, 21.89, 28.17, 35.78, 49.0, 60.32, 66.22, 66.94),
            "export": (15.49, 12.35, 9.98, 8.79, 8.08, 5.31, 5.31, 5.31),
        },
    },
    2021: {
        "MISO": {
            "import": (169.76, 169.76, 169.76, 169.76, 169.76, 169.76, 169.76, 169.76),
            "export": (154.74, 84.76, 59.14, 37.72, 26.07, 20.99, 18.28, 16.98),
        },
        "NYISO": {
            "import": (148.1, 169.76, 169.76, 169.76, 169.76, 169.76, 169.76, 169.76),
            "export": (83.17, 51.67, 36.59, 28.03, 23.38, 19.92, 17.08, 14.92),
        },
        "Carolinas": {
            "import": (30.84, 41.67, 55.23, 68.31, 88.97, 154.74, 169.76, 169.76),
            "export": (24.8, 21.61, 19.09, 17.38, 16.38, 15.6, 14.94, 14.72),
        },
        "TVA": {
            "import": (19.9, 22.43, 27.43, 37.59, 53.36, 71.93, 117.54, 168.12),
            "export": (18.39, 17.35, 16.82, 16.41, 16.12, 15.93, 15.7, 15.5),
        },
        "LGEE": {
            "import": (25.75, 34.3, 48.3, 63.63, 79.93, 119.03, 161.25, 169.76),
            "export": (21.55, 18.56, 16.84, 15.98, 15.75, 15.62, 15.22, 15.01),
        },
    },
    2022: {
        "MISO": {
            "import": (398.79, 431.93, 431.93, 431.93, 431.93, 431.93, 431.93, 431.93),
            "export": (196.82, 119.08, 78.08, 58.48, 46.3, 37.14, 28.07, 19.23),
        },
        "NYISO": {
            "import": (187.54, 345.39, 398.79, 431.93, 431.93, 431.93, 431.93, 431.93),
            "export": (115.85, 79.66, 63.67, 54.76, 47.9, 42.35, 38.04, 27.71),
        },
        "Carolinas": {
            "import": (56.05, 65.28, 76.55, 90.99, 112.85, 149.96, 227.3, 375.18),
            "export": (47.79, 41.72, 37.53, 33.5, 29.51, 25.6, 20.04, 14.61),
        },
        "TVA": {
            "import": (36.28, 41.27, 48.6, 57.75, 70.08, 93.13, 123.22, 166.78),
            "export": (31.44, 26.97, 22.42, 19.66, 17.94, 16.67, 16.27, 15.83),
        },
        "LGEE": {
            "import": (42.45, 52.41, 63.45, 78.4, 99.51, 123.38, 150.78, 199.58),
            "export": (36.82, 32.43, 28.53, 24.18, 17.64, 14.12, 13.01, 13.01),
        },
    },
    2023: {
        "MISO": {
            "import": (140.34, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05),
            "export": (72.78, 52.34, 39.12, 31.75, 26.75, 22.22, 18.38, 14.67),
        },
        "NYISO": {
            "import": (308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05),
            "export": (86.28, 48.61, 36.0, 31.11, 27.2, 22.58, 18.08, 13.0),
        },
        "Carolinas": {
            "import": (20.51, 24.1, 28.52, 34.07, 41.91, 57.03, 78.04, 260.2),
            "export": (17.62, 15.32, 13.65, 12.06, 10.39, 9.88, 7.68, 7.68),
        },
        "TVA": {
            "import": (15.49, 18.43, 22.09, 26.85, 32.19, 38.54, 49.07, 69.66),
            "export": (13.54, 12.17, 10.95, 10.29, 9.08, 7.68, 7.68, 7.68),
        },
        "LGEE": {
            "import": (21.52, 25.79, 30.44, 36.2, 43.2, 51.02, 61.99, 72.81),
            "export": (17.96, 15.18, 13.58, 11.8, 9.88, 7.68, 7.68, 7.68),
        },
    },
    2024: {
        "MISO": {
            "import": (129.46, 179.14, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93),
            "export": (62.02, 41.54, 31.09, 24.99, 20.26, 16.13, 12.72, 10.47),
        },
        "NYISO": {
            "import": (276.93, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93),
            "export": (159.98, 95.88, 52.89, 37.29, 28.63, 21.6, 15.5, 9.73),
        },
        "Carolinas": {
            "import": (17.7, 20.81, 24.67, 30.1, 39.13, 55.25, 94.3, 148.67),
            "export": (15.55, 13.75, 12.5, 11.41, 10.5, 9.59, 8.99, 8.56),
        },
        "TVA": {
            "import": (14.75, 17.31, 20.98, 25.91, 33.2, 43.39, 65.02, 126.63),
            "export": (12.68, 11.45, 10.6, 9.57, 8.65, 7.77, 7.75, 7.75),
        },
        "LGEE": {
            "import": (19.08, 23.53, 28.98, 36.39, 46.87, 59.61, 76.77, 111.23),
            "export": (15.75, 12.67, 10.63, 9.22, 8.65, 7.75, 7.75, 7.75),
        },
    },
    2025: {
        "MISO": {
            "import": (166.87, 384.6, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65),
            "export": (84.96, 55.77, 40.86, 32.7, 27.02, 22.09, 17.85, 14.46),
        },
        "NYISO": {
            "import": (502.65, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65),
            "export": (381.93, 178.51, 92.15, 62.13, 44.27, 33.17, 26.61, 19.64),
        },
        "Carolinas": {
            "import": (29.92, 33.71, 38.15, 43.53, 49.96, 58.26, 71.37, 102.29),
            "export": (25.95, 22.74, 20.18, 18.02, 16.13, 15.08, 13.65, 13.0),
        },
        "TVA": {
            "import": (23.84, 28.08, 32.96, 39.08, 46.77, 58.18, 80.86, 126.23),
            "export": (21.09, 18.25, 16.14, 15.08, 13.76, 13.26, 11.65, 11.62),
        },
        "LGEE": {
            "import": (28.93, 34.09, 40.64, 49.81, 63.91, 86.47, 129.98, 259.9),
            "export": (24.18, 20.22, 17.04, 15.08, 13.65, 11.97, 11.88, 11.88),
        },
    },
}


# pjm-174: the HOURLY NEIGHBOUR-ANCHORED seam ladder — per-band OFFSETS on the
# seam SPREAD, not prices. The PJM application of the miso-231 form, for the
# defect pjm-174 measured on PJM's own record.
#
# THE DEFECT. PJM_SEAM_LADDER_BY_YEAR above is a FIXED ANNUAL PRICE ladder
# anchored on PJM's OWN DA hub. That is a Q-Q coupling to the MEASURED price
# duration curve, but the LP clears it against the MODEL's price duration
# curve — so the coupling is only as good as the model's ability to reproduce
# that curve, and the bands leave merit exactly when the model's price is
# wrong. Measured on the committed pjm-169 2022/2021 touchpoint, zero LP
# (results/calibration/FINDING-pjm174-seam-ladder-anchoring-2026-09-08.md §2):
# the incumbent ladder reproduces its OWN basis to -0.046 TWh (2022) and
# -0.011 TWh (2021) — the band prices are RIGHT — but fed the model's own
# price it loses -5.735 TWh (2022) and -12.699 TWh (2021) of net export, 57 %
# and 88 % of each year's total interchange miss. Correcting the model's price
# duration curve alone, with its hourly ranking untouched, recovers the
# measured volume exactly (31.732 / 37.805 TWh), which is what proves the band
# prices are not the defect and the ANCHORING is.
#
# THE FORM. Band k's offer becomes hourly, pi_k(t) = neighbour(t) + delta_k,
# so band k clears iff spread(t) > delta_k (import) / < delta_k (export), with
# spread = PJM hub DA - neighbour DA (the ISO's own price minus the
# neighbour's, the same own-minus-neighbour orientation the MISO derivation
# uses). The offsets are the IDENTICAL Q-Q duration coupling — same
# midpoint-depth grid on the same SEAM_FLOW_TRANCHES, same measured tie-line
# flows, same same-seam no-wash reconciliation — read off the SPREAD instead of
# PJM's own DA. That is the same single degree of freedom the MISO neighbour
# derivations exercise: which measured series the coupling reads. ZERO fitted
# parameters (rules 21/24). Derived by
# scripts/data/derive_pjm_seam_ladders.py --neighbour-hourly (rule 23: it
# re-derives only when its SOURCE DATA updates, never because a residual moved).
#
# THE ANCHOR IS NAMED ON TOPOLOGY, before any ladder was derived (rule 14
# [R-ACCURATE] misalignment clause, the miso-233 SPP_ANCHOR_HUB pattern) and
# never chosen by which one scores better:
#   MISO  -> equal-weight mean of MISO's three PJM-FACING zonal hubs
#            (MISO-Illinois / MISO-Indiana / MISO-East). The exact MIRROR of
#            MISO's own construction for this same physical seam, where
#            PJM_WEST is the equal-weight mean of the three MISO-facing PJM gen
#            hubs. PJM's MISO ties land on ComEd (Illinois), AEP-Ohio (Indiana)
#            and ATSI (Michigan/East) — envelopes._PJM_TIE_ZONE.
#   NYISO -> NYISO's reference DA, the ONLY measured NYISO series held under
#            data/raw, so there is nothing to select between.
# The MISO system hub is reported as a sensitivity by the derive and SELECTS
# NOTHING (2022 corr +0.270 / 2023 +0.323 against the topology anchor's +0.306
# / +0.425).
#
# COVERAGE — a row exists IFF the solve can arm it. Carolinas / TVA / LGEE are
# absent in every year: SERC publishes no hub or nodal price, the same DATA
# boundary derive_miso_seam_ladders states for SOCO/TVA, and those seams keep
# their incumbent own-hub ladder untouched. MISO is absent in 2021 (no full
# measured series; 2019 landed 2026-09-24, R-MISO) and in 2022 (ONE contiguous 525 h outage in the zonal DA,
# far past the repo-standard limit=3 interpolation) — full coverage or nothing,
# because _inject_seam_ladder applies one ladder per seam-year and a
# partially-derived row would be a row the solve never uses. Every omission
# degrades to the INCUMBENT ladder, never to an unpriced seam (rule 19
# [R-ONE-MECH]).
#
# READOUT A, driven by the MEASURED record and scored on the MEASURED seam flow
# (hourly corr, incumbent -> this form; volume preserved within 0.02 TWh in
# every seam-year):
#   NYISO  2019 -0.387 -> +0.568 | 2021 -0.231 -> +0.620 | 2022 +0.235 -> +0.723
#          2023 +0.071 -> +0.553 | 2024 +0.201 -> +0.544 | 2025 +0.001 -> +0.514
#   MISO   2023 +0.419 -> +0.425 | 2024 +0.487 -> +0.393 | 2025 +0.316 -> +0.391
# A SIGN FLIP on the NYISO seam in three of six years. REPORTED AGAINST IT: the
# MISO leg is roughly neutral and is WORSE in 2024 (-0.093); the repair is the
# NYISO leg, and this table claims no more than that.
PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR: dict[
    int, dict[str, dict[str, tuple[float, ...]]]
] = {
    2019: {
        # MISO 2019 ADDED 2026-09-24 by R-MISO (rule 23: SOURCE DATA EXTENDED —
        # that lane landed MISO's 2019 hub LMPs, so the MISO-facing zonal DA this
        # row's spread reads now covers 2019 in full). Verbatim from
        # derive_pjm_seam_ladders.derive_neighbour_hourly(2019), the frozen script;
        # the NYISO row re-derives unchanged. Inert for every registered PJM run
        # (none carries 2019); routed to R-PJM, which solves 2019.
        "MISO": {
            "import": (65.45, 65.45, 65.45, 65.45, 65.45, 65.45, 65.45, 65.45),
            "export": (26.17, 8.69, 2.5, -0.64, -2.64, -4.7, -8.99, -19.78),
        },
        "NYISO": {
            "import": (16.65, 74.19, 94.04, 94.04, 94.04, 94.04, 94.04, 94.04),
            "export": (9.45, 4.54, 1.2, -1.25, -4.19, -10.9, -38.31, -62.01),
        },
    },
    2021: {
        "NYISO": {
            "import": (55.28, 84.29, 84.29, 84.29, 84.29, 84.29, 84.29, 84.29),
            "export": (20.72, 7.63, 2.4, -1.92, -5.57, -12.28, -28.74, -56.68),
        },
    },
    2022: {
        "NYISO": {
            "import": (48.41, 139.39, 180.53, 213.56, 213.56, 213.56, 213.56, 213.56),
            "export": (22.9, 9.22, 2.24, -2.84, -7.67, -15.32, -35.67, -100.88),
        },
    },
    2023: {
        "MISO": {
            "import": (59.9, 141.61, 141.61, 141.61, 141.61, 141.61, 141.61, 141.61),
            "export": (23.07, 9.65, 3.52, 0.11, -2.22, -4.54, -7.54, -12.71),
        },
        "NYISO": {
            "import": (150.53, 150.53, 150.53, 150.53, 150.53, 150.53, 150.53, 150.53),
            "export": (28.88, 11.23, 4.46, 1.5, -1.16, -4.31, -9.0, -30.18),
        },
    },
    2024: {
        "MISO": {
            "import": (37.59, 73.18, 87.22, 87.22, 87.22, 87.22, 87.22, 87.22),
            "export": (13.7, 6.03, 1.98, -0.83, -3.08, -6.08, -10.56, -27.87),
        },
        "NYISO": {
            "import": (107.39, 107.39, 107.39, 107.39, 107.39, 107.39, 107.39, 107.39),
            "export": (42.96, 19.53, 6.92, 0.94, -3.46, -7.76, -17.93, -85.84),
        },
    },
    2025: {
        "MISO": {
            "import": (54.67, 147.14, 191.71, 191.71, 191.71, 191.71, 191.71, 191.71),
            "export": (19.96, 8.79, 2.58, -1.49, -5.51, -10.37, -20.23, -48.52),
        },
        "NYISO": {
            "import": (155.69, 155.69, 155.69, 155.69, 155.69, 155.69, 155.69, 155.69),
            "export": (89.74, 32.13, 11.44, 1.76, -4.48, -11.97, -32.81, -74.05),
        },
    },
}

#: The measured neighbour DA series each PJM seam's hourly ladder is anchored
#: on (pjm-174). ``(parquet stem under data/raw/_validation-source, zonal hubs
#: to equal-weight mean)``; an empty hub tuple means the file is a single
#: series. Named on TOPOLOGY — see the table comment above.
PJM_SEAM_NEIGHBOUR_ANCHOR: dict[str, tuple[str, tuple[str, ...]]] = {
    "MISO": (
        "actual_lmp_hourly_zonal_MISO",
        ("MISO-Illinois", "MISO-Indiana", "MISO-East"),
    ),
    "NYISO": ("actual_lmp_hourly_NYISO", ()),
}


@dataclass(frozen=True)
class CaisoHubNeighbor:
    """One CAISO WECC import corridor priced as a forward reference-price seam."""

    zone: str
    hub: str
    gas_basis: float
    marginal_heat_rate: float
    load_shape_kind: str
    load_shape_exponent: float
    atc_base_fraction: float
    atc_solar_floor: float


CAISO_PER_HUB_NEIGHBORS: dict[str, CaisoHubNeighbor] = {
    "WECC_PNW": CaisoHubNeighbor(
        zone="WECC_PNW",
        hub="MALIN",
        gas_basis=-0.30,
        marginal_heat_rate=16.0,
        load_shape_kind="gross",
        load_shape_exponent=1.0,
        atc_base_fraction=0.43,
        atc_solar_floor=0.30,
    ),
    "WECC_DSW": CaisoHubNeighbor(
        zone="WECC_DSW",
        hub="PALOVRDE",
        gas_basis=0.30,
        marginal_heat_rate=13.0,
        load_shape_kind="net",
        load_shape_exponent=1.0,
        atc_base_fraction=0.56,
        atc_solar_floor=0.30,
    ),
}


# --- NYISO-specific interchange constants ---

NYISO_FIRM_IMPORT_FLOOR_FRAC: dict[str, float] = {
    "HQ_hydro": 1.0,
    "IESO_Ontario": 0.0,
}

NYISO_IMPORT_RECON_BAND_FRAC: float = 0.02


# --- MISO Manitoba firm-hydro import constants ---

MISO_MANITOBA_FIRM_IMPORT_MW: float = 1400.0
MISO_MANITOBA_FIRM_IMPORT_OFFER: float = 8.0
MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC: float = 1.0
# The Manitoba↔US HVDC / 500 kV ties land in Minnesota (LRZ 1) = MISO-West.
MISO_MANITOBA_FIRM_IMPORT_ZONE: str = "MISO-West"
MISO_MANITOBA_FIRM_IMPORT_NAME: str = "Manitoba_firmhydro"

MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR: dict[int, float] = {
    2023: 726.0,
    2024: 531.0,
    2025: 224.0,
}

# --- MISO Manitoba two-way priced seam (miso-74) ---
# Replaces the import-only annual-flat firm block above with a fourth MEASURED
# two-way priced seam under ScenarioConfig.miso_manitoba_seam (default off).
# Built by transmission.build_reference_price_node (extra_neighbors) and priced
# by the frozen Q-Q ladder MISO_SEAM_LADDER_BY_YEAR["Manitoba"]; the two-way
# (month × hour-of-day) deliverability envelope comes for free from
# MISO_SEAM_DIBA["Manitoba"]. Every field is a physically-pinned structural
# constant (rule 23) — none tuned to a residual:
#   * interface_limit_mw 2900: the physical MHEB→MISO (Minnesota, LRZ 1)
#     transfer capability, pinned to the measured +2,827 MW import extreme
#     (EIA-930 "MISO interchange hourly.parquet"); the Q-Q fit is insensitive to
#     it in [2400, 3000] and the export bands self-limit at the ~1,400 MW
#     measured export capability via the export envelope.
#   * import_emission_factor 0.0: Manitoba Hydro is ~hydro — a clean import,
#     identical CO2 accounting to the fuel-free firm block it replaces (the EF
#     is a CARB-only price adder, inert for MISO which has no carbon program).
#   * border_zones ("MISO-West",): the Manitoba↔US HVDC/AC ties land in
#     Minnesota (LRZ 1) = MISO-West, the firm block's own zone.
# hurdle / gas_basis / marginal_heat_rate / load_shape are seam-family
# conventions, inert under miso_seam_measured_ladder (the ladder prices every
# band directly). No firm_import_floor_by_year — a firm import floor would force
# imports in the winter export hours the measured seam net-exports over. See
# docs/handoffs/miso-manitoba-seam-design-2026-07.md.
MISO_MANITOBA_SEAM_SPEC: NeighborInterface = NeighborInterface(
    name="Manitoba",
    ba_code="MHEB",
    gas_basis=0.0,
    marginal_heat_rate=10.0,
    hurdle=2.0,
    interface_limit_mw=2900.0,
    border_zones=("MISO-West",),
    load_shape_exponent=1.0,
    import_emission_factor=0.0,
)

MISO_FIRM_IMPORT_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


def resolve_miso_manitoba_firm_import_mw(year: int | None, mode: str) -> float:
    """Return the Manitoba firm-import block capacity (MW) for ``year``/``mode``."""
    if mode == "backcast" and year in MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR:
        return MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[year]
    return MISO_MANITOBA_FIRM_IMPORT_MW


def resolve_miso_firm_imports(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--miso-firm-imports`` tri-state flag for ``iso``."""
    if flag is not None:
        return flag
    return iso in MISO_FIRM_IMPORT_DEFAULT_ISOS


# ---------------------------------------------------------------------------
# Simultaneous Import/Export Limits (SIL/SEC) — per ISO
# ---------------------------------------------------------------------------
# These cap the total simultaneous flow across ALL external border links of an
# ISO's import/export zone, ensuring aggregate import (or export, when
# bidirectional) does not exceed the receiving (or sending) network's
# simultaneous transfer capability — which is materially less than the sum of
# individual path ratings because the paths share upstream/downstream network
# capacity.  The per-link TTC still binds each individual path; this constraint
# binds only when several paths would load simultaneously past the aggregate
# rating.
#
# Stored as (name, cap_mw, bidirectional) per ISO.  The link references are
# built dynamically from IMPORT_NODE_LINKS by
# :func:`~market_sim.model.transmission.extend_with_import_node`, so they
# always match the border links actually present in the topology.
#
# CAISO's equivalent (``WECC_import_simultaneous``, 7,500 MW) is baked directly
# into ``_caiso_config`` in iso_configs.py.  NEISO's (``HQ_import_simultaneous``,
# 3,850 MW) is baked into ``_neiso_config`` because HQ_import is a baked-in zone.
# ERCOT has no external import zone (DC ties ~1.2 GW embedded in demand).
EXTERNAL_SIMULTANEOUS_LIMITS: dict[str, tuple[str, float, bool]] = {
    # PJM Simultaneous Import Limit.  PJM publishes CETL (Capacity Emergency
    # Transfer Limit) per LDA via the RTEP process and conducts simultaneous-
    # feasibility studies for the RPM Base Residual Auction.  The system-wide
    # aggregate simultaneous import capability is ~10,500 MW — well below the
    # sum of individual seam limits (MISO 7.3 + NYISO 3.9 + Carolinas 2.4 +
    # TVA 1.6 + LGEE 1.1 = 16.3 GW) and far below the border-link TTC sum
    # (30.2 GW), because the western interfaces (AP-South, Bedington-BlackOak)
    # share downstream 500 kV capacity.
    # Source: PJM RTEP Annual Report (CETL tables); PJM Manual 14B §3.3
    # (simultaneous feasibility); RPM Base Residual Auction parameters.
    "PJM": ("PJM_simultaneous_import", 10500.0, True),
    # MISO Capacity Import Limit (CIL).  MISO publishes CIL/CEL with the annual
    # Planning Resource Auction (PRA) via the LOLE study.  The system-wide CIL
    # is ~8,700 MW — below the sum of individual seam limits (PJM 7.3 + SPP 4.0
    # + South 3.0 = 14.3 GW), because the contract-path RDT bottleneck between
    # MISO Midwest and MISO South limits how much of each seam can flow
    # simultaneously.
    # Source: MISO PRA clearing results; MISO LOLE Study Report; MTEP.
    "MISO": ("MISO_simultaneous_import", 8700.0, True),
    # NYISO Simultaneous Import Limit.  **PROVENANCE DEFECT — see
    # ScenarioConfig.nyiso_import_sil_retire (nyiso-100).**  The 4,350 MW here
    # is NOT an external NYCA seam limit: it is exactly the published G-J
    # LOCALITY Bulk Power Transmission Limit for capability year 2024/2025
    # (data/raw/capacity-deliverability/nyiso/nyiso.csv, area "G-J",
    # import_limit), an INTERNAL New York transfer boundary (Load Zones
    # G,H,I,J) frozen at one capability year's value (the published series
    # moves 3,425 / 3,425 / 4,350 / 4,500 across 2022/23-2025/26).  The
    # originally cited source does not contain it — the Gold Book publishes no
    # aggregate external simultaneous import limit, and its per-facility
    # transmission table (Table VI-1) is redacted as Critical Energy
    # Infrastructure Information in every 2023-2025 edition.  Measurement
    # falsifies it as an external cap: NYCA net import reached 5,929 / 5,662 /
    # 5,872 MW metered (EIA-930) and 7,078 / 7,298 / 6,727 MW scheduled (NYISO
    # MIS P-32) in 2023/2024/2025, exceeding 4,350 MW in 287/314/145 h and
    # 865/685/388 h respectively.  The stale arithmetic in the superseded
    # comment also omitted the Capital_Hudson border link: the actual
    # border-link TTC sum is 6.8 GW (Upstate_West 3.0 + Capital_Hudson 1.6 +
    # NYC 1.0 + Long_Island 1.2), not 5.2 GW.  Retained at its historical value
    # so every pre-nyiso-100 keeper replays byte-identically; set
    # ``nyiso_import_sil_retire=True`` to drop the mis-attributed constraint and
    # let the posted-rating-grounded per-link TTCs bound the seam.
    "NYISO": ("NYISO_simultaneous_import", 4350.0, True),
}

# Backwards-compatible aliases for the original CAISO-only WECC names.
WECC_IMPORT_TRANCHES: list[tuple[str, float, float]] = IMPORT_TRANCHES["CAISO"]
WECC_EXPORT_CAP_MW: float = EXPORT_TRANCHES["CAISO"][0][1]
WECC_IMPORT_EFORD: float = IMPORT_EFORD["CAISO"]


# ---------------------------------------------------------------------------
# InterchangeSpec dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Corridor:
    """One physical WECC corridor (CAISO per-hub import path).

    Attributes:
        name: Corridor identifier (e.g. ``"WECC_PNW"``).
        zone: External zone hosting the corridor generators.
        import_tranches: ``(name, capacity_mw, marginal_cost)`` ladder.
        export_cap_mw_fn: Returns the export-direction MW bound.
        ttc_mw: Physical line rating (MW).
        carbon_adder: Border carbon per MWh on unspecified imports.
        gas_coupling_fn: Optional callback to shift gas-set import tranches.
        solar_derate_fn: Optional callback returning hourly ATC derate.
    """

    name: str
    zone: str
    import_tranches: list[tuple[str, float, float]]
    export_cap_mw_fn: Callable[[], float] | None = None
    ttc_mw: float = float("inf")
    carbon_adder: float = 0.0
    gas_coupling_fn: Callable | None = None
    solar_derate_fn: Callable | None = None


@dataclass
class FirmImport:
    """A must-flow firm import block (e.g. Manitoba hydro into MISO-West).

    Attributes:
        name: Block name.
        zone: Zone the block lands in.
        capacity_mw: Maximum import MW.
        offer: $/MWh offer price.
        floor_frac: Fraction of capacity forced as must-flow.
    """

    name: str
    zone: str
    capacity_mw: float
    offer: float
    floor_frac: float = 1.0


@dataclass
class ReconciliationBand:
    """Monthly net-interchange reconciliation envelope (NYISO).

    Attributes:
        band_frac: Monthly band half-width as a fraction of net import.
        iso: ISO this applies to.
    """

    band_frac: float
    iso: str = "NYISO"


@dataclass
class InterchangeSpec:
    """Unified interchange specification for one ISO.

    Configures all external seams: static import/export tranches (the
    ``build_import_generators`` / ``build_export_sinks`` path), reference-
    price neighbors, CAISO corridors, firm imports, and monthly reconciliation.

    Attributes:
        iso: ISO identifier.
        import_zone: External zone name.
        import_tranches: Static import supply ladder.
        export_tranches: Static export sink ladder.
        neighbors: Reference-price seam neighbors.
        corridors: CAISO per-hub corridors (empty for non-CAISO).
        firm_imports: Must-flow firm import blocks.
        monthly_reconciliation: Optional monthly band constraint.
        eford: Forced-outage derate on import tranches.
        use_reference_price: Whether the seam is served by the reference-price
            node (``build_reference_price_node``) — the generic non-CAISO seam
            or CAISO's dedicated ``caiso_reference_price_seam``.
        use_corridors: Whether the CAISO per-hub corridor TOPOLOGY is active
            (the ``WECC_import`` node splits into ``WECC_PNW``/``WECC_DSW`` and
            the corridor ATC/flow envelopes may bind). True for both the
            per-hub intertie and the CAISO reference-price seam, matching the
            backcast's ``caiso_corridors`` resolution.
        caiso_mode: Which CAISO seam builder is active — ``"reference_seam"``
            (forward reference-price corridors), ``"per_hub"`` (two signed
            corridors priced at their own hubs), ``"bidir"`` (single signed
            tie), or ``None`` (static tranche ladder / non-CAISO). Resolved
            with the same mutual-exclusion ladder the backcast orchestrator
            has always used: reference seam supersedes per-hub supersedes
            bidir.
    """

    iso: str
    import_zone: str
    import_tranches: list[tuple[str, float, float]] = field(default_factory=list)
    export_tranches: list[tuple[str, float, float]] = field(default_factory=list)
    neighbors: list[NeighborInterface] = field(default_factory=list)
    corridors: list[Corridor] = field(default_factory=list)
    firm_imports: list[FirmImport] = field(default_factory=list)
    monthly_reconciliation: ReconciliationBand | None = None
    eford: float = 0.0
    use_reference_price: bool = False
    use_corridors: bool = False
    caiso_mode: str | None = None
    # MISO only: host the South seam's reference-price bands in their own
    # external zone (constants.MISO_SOUTH_EXTERNAL_ZONE) so they ride the
    # split topology of transmission.split_miso_south_external_node instead
    # of the shared MISO_external bus (which fabricates a free
    # South→external→Midwest wheel around the RDT). Resolved from
    # ScenarioConfig.miso_south_seam_split.
    miso_south_split: bool = False
    # MISO only: replace the import-only Manitoba firm block with the fourth
    # two-way priced seam (MISO_MANITOBA_SEAM_SPEC bands + the "Manitoba" Q-Q
    # ladder + the measured MHEB two-way envelope). Resolved from
    # ScenarioConfig.miso_manitoba_seam; when set, get_interchange_spec also
    # drops the Manitoba entry from firm_imports (miso-74).
    miso_manitoba_seam: bool = False
    # CAISO per-hub only: build the south-corridor surplus-clean depth tranche
    # (caiso-87; see the CAISO_DSW_SURPLUS_CLEAN_* block above). Resolved from
    # ScenarioConfig.caiso_dsw_surplus_clean; the tranche is built with zero
    # capacity and armed hourly by
    # transmission.inject_caiso_dsw_surplus_clean at the injection seam.
    caiso_surplus_clean: bool = False
    # CAISO per-hub only: build the south-corridor OVERNIGHT clean depth
    # tranche (caiso-93; see the CAISO_DSW_OVERNIGHT_CLEAN_* block above).
    # Resolved from ScenarioConfig.caiso_dsw_overnight_clean; zero capacity at
    # build, armed hourly by transmission.inject_caiso_dsw_overnight_clean.
    caiso_overnight_clean: bool = False
    # CAISO per-hub only: build the south-corridor DAYTIME trigger-OFF clean
    # depth tranche (caiso-94; see the CAISO_DSW_DAYTIME_CLEAN_* block above).
    # Resolved from ScenarioConfig.caiso_dsw_daytime_clean; zero capacity at
    # build, armed hourly by transmission.inject_caiso_dsw_daytime_clean.
    caiso_daytime_clean: bool = False
    # CAISO per-hub only: build the south-corridor LATE-EVENING clean depth
    # tranche (caiso-269; see the CAISO_DSW_LATEEVENING_CLEAN_* block above).
    # Resolved from ScenarioConfig.caiso_dsw_lateevening_clean; zero capacity
    # at build, armed hourly by transmission.inject_caiso_dsw_lateevening_clean.
    caiso_lateevening_clean: bool = False


def get_interchange_spec(config, iso: str, year: int | None = None) -> InterchangeSpec:
    """Build the ``InterchangeSpec`` for ``iso`` from ``config`` flags.

    Returns a spec that encodes which interchange model is active (static
    tranche ladder, reference-price seam, CAISO per-hub / bidirectional
    intertie) based on the scenario config flags.  The caller passes this to
    ``build_interchange_fleet`` to get the ``Generator`` list and to
    ``apply_interchange_topology`` to get the matching topology.

    The CAISO builder choice replicates the backcast orchestrator's
    long-standing mutual-exclusion ladder exactly (all gates are existing
    ``ScenarioConfig`` fields, every one default-off):

    1. ``caiso_reference_price_seam`` — forward reference-price corridors
       (``build_reference_price_node``), per-hub corridor topology.
    2. else ``caiso_per_hub_intertie`` — two signed corridors priced at their
       own hubs (``build_caiso_per_hub_intertie``), per-hub corridor topology.
    3. else — static import tranches + export sinks on the pooled node.

    (The former step 3, ``caiso_bidir_intertie`` — a single signed tie over one
    averaged hub — was DELETED at caiso-236 under rule 26 ``[R-DELETE]``: it was
    off on the keeper AND off in the ``ScenarioConfig`` defaults, i.e. dead in
    every shipped configuration, so its fitted 4,361 MW aggregate export cap was
    a re-armable answer key. ``caiso_per_hub_intertie`` is its successor.)

    The generic ``reference_price_interface`` path never applies to CAISO
    (CAISO's seam is the dedicated mode-1 above; the generic single-node path
    would land its per-corridor tranches with no corridor zones to host them).

    Args:
        config: Scenario config carrying the interchange gates.
        iso: ISO identifier.
        year: Solve year grounding the year-varying inputs
            (``IMPORT_TRANCHES_BY_YEAR`` ladder, measured Manitoba firm-import
            capacity in backcast mode). ``None`` falls back to
            ``config.weather_year`` — identical in a backcast, where the
            weather year is pinned to the solve year.
    """
    import_zone = IMPORT_ZONE.get(iso, "")
    if not import_zone:
        return InterchangeSpec(iso=iso, import_zone="")

    eford = IMPORT_EFORD.get(iso, 0.0)

    caiso_ref_seam = iso == "CAISO" and getattr(
        config, "caiso_reference_price_seam", False
    )
    caiso_per_hub = (
        (not caiso_ref_seam)
        and iso == "CAISO"
        and getattr(config, "caiso_per_hub_intertie", False)
    )
    caiso_mode = (
        "reference_seam" if caiso_ref_seam else "per_hub" if caiso_per_hub else None
    )
    use_ref = caiso_ref_seam or (
        getattr(config, "reference_price_interface", False)
        and iso in INTERFACE_NEIGHBORS
        and iso != "CAISO"
    )
    use_corridors = caiso_per_hub or caiso_ref_seam

    if year is None:
        year = getattr(config, "weather_year", None)
    tranches = IMPORT_TRANCHES.get(iso, [])
    exports = EXPORT_TRANCHES.get(iso, [])
    if year is not None:
        tranches = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year, tranches)
        exports = EXPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year, exports)

    neighbors = INTERFACE_NEIGHBORS.get(iso, []) if use_ref else []

    corridors: list[Corridor] = []
    if use_corridors:
        from market_sim.model.transmission import (
            wecc_border_carbon_adder,
        )

        # The corridor inventory's border adder prices off the RESOLVED carbon
        # signal (SCN-WS1a, plan §2.1 G-C2), the same resolution every other
        # border site uses (runner.py's build_interchange_fleet border,
        # interchange/caiso.py, import_nodes.py). Before this it read the raw
        # config.carbon_price field, which is 0.0 under the default
        # program-resolved posture, so the inventory reported a $0 adder where
        # the CARB trajectory says ~$12.85/MWh in 2026. The year is the spec's
        # own year when the caller passes one, else the run's start year (the
        # runner builds the interchange fleet once at start_year and re-prices
        # it per year through apply_interchange_injections). Lazy import:
        # policy.carbon imports config.scenarios, and this module must stay
        # importable from the config layer.
        from market_sim.config.constants import START_YEAR
        from market_sim.policy.carbon import resolve_carbon_price

        carbon_year = year
        if carbon_year is None:
            carbon_year = getattr(config, "start_year", None)
        if carbon_year is None:
            carbon_year = START_YEAR
        border = wecc_border_carbon_adder(
            resolve_carbon_price(config, int(carbon_year))
        )
        # Informational corridor inventory (zones + per-hub tranche split).
        # The per-hub GENERATORS are built by the canonical
        # transmission.build_caiso_per_hub_intertie, which uses the static
        # IMPORT_TRANCHES ladder (per-tranche capacities are contract
        # structure, not year-shaped) — so the corridor entries here carry the
        # same static split.
        for hub, zone in CAISO_PER_HUB_IMPORT_ZONES.items():
            hub_tranches = [
                (name, cap, mc)
                for name, cap, mc in IMPORT_TRANCHES.get(iso, [])
                if CAISO_IMPORT_TRANCHE_HUB.get(name) == hub
            ]
            corridors.append(
                Corridor(
                    name=zone,
                    zone=zone,
                    import_tranches=hub_tranches,
                    carbon_adder=border,
                )
            )

    firm_imports: list[FirmImport] = []
    # miso_manitoba_seam supersedes the import-only firm block with the two-way
    # priced seam (miso-74): drop the firm block here so inject_miso_firm_imports
    # finds no target uid and no-ops.
    if (
        getattr(config, "miso_firm_imports", False)
        and iso == "MISO"
        and not getattr(config, "miso_manitoba_seam", False)
    ):
        pmax = resolve_miso_manitoba_firm_import_mw(
            year,
            getattr(config, "mode", "forecast"),
        )
        firm_imports.append(
            FirmImport(
                name=MISO_MANITOBA_FIRM_IMPORT_NAME,
                zone=MISO_MANITOBA_FIRM_IMPORT_ZONE,
                capacity_mw=pmax,
                offer=MISO_MANITOBA_FIRM_IMPORT_OFFER,
                floor_frac=MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC,
            )
        )

    recon = None
    if getattr(config, "nyiso_import_reconciliation", False) and iso == "NYISO":
        recon = ReconciliationBand(
            band_frac=NYISO_IMPORT_RECON_BAND_FRAC,
            iso="NYISO",
        )

    return InterchangeSpec(
        iso=iso,
        import_zone=import_zone,
        import_tranches=tranches if not (use_ref or use_corridors) else [],
        export_tranches=exports if not (use_ref or use_corridors) else [],
        neighbors=neighbors,
        corridors=corridors,
        firm_imports=firm_imports,
        monthly_reconciliation=recon,
        eford=eford,
        use_reference_price=use_ref,
        use_corridors=use_corridors,
        caiso_mode=caiso_mode,
        miso_south_split=(
            iso == "MISO"
            and use_ref
            and getattr(config, "miso_south_seam_split", False)
        ),
        miso_manitoba_seam=(
            iso == "MISO" and use_ref and getattr(config, "miso_manitoba_seam", False)
        ),
        caiso_surplus_clean=(
            caiso_per_hub and getattr(config, "caiso_dsw_surplus_clean", False)
        ),
        caiso_overnight_clean=(
            caiso_per_hub and getattr(config, "caiso_dsw_overnight_clean", False)
        ),
        caiso_daytime_clean=(
            caiso_per_hub and getattr(config, "caiso_dsw_daytime_clean", False)
        ),
        caiso_lateevening_clean=(
            caiso_per_hub and getattr(config, "caiso_dsw_lateevening_clean", False)
        ),
    )


def build_interchange_fleet(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float = 0.0,
) -> list[Generator]:
    """Build ``Generator`` objects from an ``InterchangeSpec``.

    Delegates to the canonical builders in
    :mod:`market_sim.model.transmission` — the same functions the backcast
    orchestrator has always used inline — selected by the spec's mode flags,
    so both orchestrators produce identical ``Generator`` lists by
    construction:

    * ``use_reference_price`` → :func:`~market_sim.model.transmission.build_reference_price_node`
      (generic non-CAISO seam and CAISO's ``caiso_reference_price_seam``).
    * ``caiso_mode == "per_hub"`` → :func:`~market_sim.model.transmission.build_caiso_per_hub_intertie`.
    * otherwise → the static import-tranche + export-sink ladder (identical to
      ``build_import_generators`` + ``build_export_sinks`` on the spec's
      year-grounded tranches).

    Firm import blocks (``spec.firm_imports``) are appended last, matching the
    backcast construction order and byte-identical to
    :func:`~market_sim.model.transmission.build_miso_firm_imports`.
    """
    if not spec.import_zone:
        return []

    gens: list[Generator] = []

    if spec.use_reference_price:
        from market_sim.model.transmission import build_reference_price_node

        overrides = None
        if spec.miso_south_split:
            from market_sim.config.constants import MISO_SOUTH_EXTERNAL_ZONE

            # The South seam's bands ride the split topology
            # (transmission.split_miso_south_external_node) so they clear in
            # the zone actually linked to MISO-South.
            overrides = {"South": MISO_SOUTH_EXTERNAL_ZONE}
        # miso-74: append the two-way Manitoba seam's bands (replacing the
        # dropped firm block) so the ladder + measured MHEB envelope price them.
        extra = [MISO_MANITOBA_SEAM_SPEC] if spec.miso_manitoba_seam else None
        gens.extend(
            build_reference_price_node(
                spec.iso, zone_overrides=overrides, extra_neighbors=extra
            )
        )
    elif spec.caiso_mode == "per_hub":
        from market_sim.model.transmission import build_caiso_per_hub_intertie

        gens.extend(
            build_caiso_per_hub_intertie(
                border_carbon_per_mwh,
                surplus_clean=spec.caiso_surplus_clean,
                overnight_clean=spec.caiso_overnight_clean,
                daytime_clean=spec.caiso_daytime_clean,
                lateevening_clean=spec.caiso_lateevening_clean,
            )
        )
    else:
        gens.extend(_build_static_tranche_gens(spec, border_carbon_per_mwh))

    for fi in spec.firm_imports:
        gens.append(
            Generator(
                unit_id=f"{fi.zone}_{fi.name}",
                name=fi.name,
                zone=fi.zone,
                fuel_type="import",
                pmax_mw=fi.capacity_mw,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=fi.offer,
                eford=0.0,
            )
        )

    return gens


def _build_static_tranche_gens(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float,
) -> list[Generator]:
    """Build the static import tranche + export sink generators."""
    zone = spec.import_zone
    ef_map = IMPORT_TRANCHE_EF.get(spec.iso, {})
    gens: list[Generator] = []
    for name, capacity, marginal_cost in spec.import_tranches:
        ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
        tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=capacity,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=marginal_cost + tranche_carbon,
                eford=spec.eford,
            )
        )
    for name, capacity, price in spec.export_tranches:
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-capacity,
                heat_rate=0.0,
                vom=price,
                eford=0.0,
            )
        )
    return gens


def apply_interchange_topology(
    iso_config,
    spec: InterchangeSpec,
    config,
    *,
    year: int,
    extend_node: bool = True,
):
    """Apply the spec's interchange topology to ``iso_config``.

    The single topology sequence both orchestrators run, in the order the
    backcast has always used:

    1. ``extend_node`` — append the ISO's external import/export zone + border
       links (:func:`~market_sim.model.transmission.extend_with_import_node`;
       a no-op where the zone is baked in, e.g. CAISO/NEISO).
    2. ``config.capacity_deliverability_limits`` (Part A) — replace the
       calibrated simultaneous-import scalar with the ISO's published per-area
       SEAM import limit (CAISO branch-group MIC → ``WECC_import``), resolved
       for ``year``'s delivery year. No-op when the flag is off (default), the
       ISO publishes no seam ``import_limit``, or the clean data is absent.
    3. ``spec.use_corridors`` — split CAISO's single ``WECC_import`` node into
       the two per-hub corridors and re-home the import links + the
       simultaneous-import interface limit onto them
       (:func:`~market_sim.model.transmission.split_caiso_import_node_per_hub`).
       Applied after step 2 so the seam limit's structural identification
       (every link originates at the import node) matches, and the split then
       re-homes the replaced cap onto the corridor links.
    4. ``config.caiso_asymmetric_path_ratings`` — cap the internal Path 15 /
       Path 26 links at their WECC-accepted directional ratings
       (:func:`~market_sim.model.transmission.apply_caiso_asymmetric_path_limits`).
       Internal links only; applied last so the import-node identification in
       step 2 is untouched. No-op when the flag is off (default).

    Args:
        iso_config: ISO topology (possibly already carrying the import node).
        spec: The ISO's resolved :class:`InterchangeSpec`.
        config: Scenario config (reads ``capacity_deliverability_limits``).
        year: Solve year resolving the deliverability delivery year.
        extend_node: Whether to append the external node. Callers keep their
            existing gate (the forecast runner extends only when the priced
            node has generators; the backcast extends whenever priced
            interchange is on).

    Returns:
        The updated ``iso_config``.
    """
    import logging

    from market_sim.model.transmission import (
        apply_deliverability_seam_limit,
        extend_with_import_node,
        retire_misattributed_sil,
        split_caiso_import_node_per_hub,
    )

    logger = logging.getLogger(__name__)
    iso = spec.iso
    if extend_node:
        iso_config = extend_with_import_node(iso_config)
    if iso == "NYISO" and getattr(config, "nyiso_import_sil_retire", False):
        iso_config = retire_misattributed_sil(iso_config, iso)
        logger.info(
            "%s %d: nyiso_import_sil_retire — dropped the mis-attributed "
            "NYISO_simultaneous_import scalar (the published G-J LOCALITY "
            "Bulk Power Transmission Limit, an internal boundary); the seam "
            "is now bounded by the posted-rating per-link TTCs alone",
            iso,
            year,
        )
    # caiso-190: the seam cap is resolved through the SHARED derivation in
    # market_sim.data.resolved_inputs and the outcome is recorded there, so the
    # value persisted into run_config.json is the value this function hands the
    # LP rather than a re-derivation that could drift from it. The resolution
    # itself is unchanged statement-for-statement (same delivery year/season,
    # same per-area aggregation, same truthiness test); only its home moved.
    from market_sim.data.resolved_inputs import (
        record_seam_resolution,
        resolve_seam_import_cap,
    )

    _seam = resolve_seam_import_cap(config, iso, year, iso_config)
    record_seam_resolution(_seam)
    if getattr(config, "capacity_deliverability_limits", False):
        _dy = _seam.delivery_year
        _seam_mw = _seam.cap_mw if _seam.source == "mic_partition" else None
        if _seam_mw:
            iso_config = apply_deliverability_seam_limit(iso_config, iso, _seam_mw)
            logger.info(
                "%s %d: capacity_deliverability_limits — seam import cap "
                "set to %.0f MW (summed per-area import_limit, delivery "
                "year %s)",
                iso,
                year,
                _seam_mw,
                _dy,
            )
        else:
            # caiso-188: Part A resolves the published seam limit through the
            # GITIGNORED, disposable clean partition
            # (data/clean/capacity-deliverability/), which no solve auto-builds.
            # Absent, this branch used to pass silently while run_config.json
            # still recorded the flag as True — so a bundle could claim the
            # published MIC seam limit and solve against the baked fitted
            # scalar instead. That is what happened to every CAISO run from
            # caiso-175 onward, the designated keeper included: total import
            # pinned at the fitted 7,500 MW WECC_import_simultaneous cap in
            # 764/477/809 hours of 2023/24/25
            # (FINDING-caiso188-import-tranche-dof-2026-08-09.md §4). Warn
            # loudly and name the fallback the LP will actually solve against
            # (rule 24 [R-REGISTRY]: no unrecorded channel may decide a limit).
            # caiso-190: the resolution is ALSO persisted — run_config.json's
            # resolved_inputs.seam_import_cap now carries this cap and
            # source="baked_fallback", so a later session can tell a bundle
            # that solved on the published MIC from one that solved on the
            # fitted scalar without re-deriving anything.
            _baked = _seam.cap_mw
            logger.warning(
                "%s %d: capacity_deliverability_limits is ON but Part A did "
                "NOT apply — no published per-area import_limit resolved for "
                "delivery year %s (run scripts/data/curate_capacity_"
                "deliverability.py to materialise the clean partition). The "
                "solve keeps the BAKED simultaneous-import cap (%s MW), which "
                "is a fitted scalar; run_config.json still records the flag as "
                "True and now also records resolved_inputs.seam_import_cap "
                "source=baked_fallback — see FINDING-caiso188 §4, caiso-190",
                iso,
                year,
                _dy,
                "none" if _baked is None else f"{_baked:.0f}",
            )
    if spec.use_corridors:
        iso_config = split_caiso_import_node_per_hub(iso_config)
    # 4. ``config.caiso_asymmetric_path_ratings`` — cap the internal Path 15 /
    #    Path 26 links at their WECC-accepted directional ratings (the baked-in
    #    symmetric TTC is only one direction's rating). Internal links only, so
    #    it composes with the import-node steps above in any order; last keeps
    #    the import-node structural identification in step 2 untouched. No-op
    #    when the flag is off (default) or the ISO carries neither link.
    from market_sim.model.transmission import apply_caiso_asymmetric_path_limits

    iso_config = apply_caiso_asymmetric_path_limits(iso_config, config)
    # 5. ``spec.miso_south_split`` — re-home the MISO-South border link (and
    #    the South seam's SIL member) onto its own external zone, severing the
    #    free South→external→Midwest wheel around the RDT. Needs the import
    #    node from step 1, so it only fires when the node was extended.
    if spec.miso_south_split and iso == "MISO" and extend_node:
        from market_sim.model.transmission import split_miso_south_external_node

        iso_config = split_miso_south_external_node(iso_config)
        logger.info(
            "MISO %d: miso_south_seam_split — South seam re-homed onto its "
            "own external zone (RDT wheel-through bypass severed)",
            year,
        )
    # 6. ``config.miso_rdt_tcdc`` — replace the static JOA-limit RDT pair with
    #    the published 92% default derate + two-step TCDC priced tiers
    #    (transmission.apply_miso_rdt_tcdc). Internal links only, so it
    #    composes with every step above; last keeps the import-node
    #    identification untouched. ``config.miso_rpe_pricing`` rides the same
    #    transform: the RPE constraint's published $200/MWh demand value is
    #    added to both violation tiers (2023-2025 additive pricing, 2024 SOM
    #    §II.E/§III.B) — it has no meaning without the TCDC tiers, so arming
    #    it alone fails loud rather than silently doing nothing.
    rpe_pricing = getattr(config, "miso_rpe_pricing", False)
    if rpe_pricing and iso == "MISO" and not getattr(config, "miso_rdt_tcdc", False):
        raise ValueError(
            "miso_rpe_pricing requires miso_rdt_tcdc: the RPE demand value "
            "prices the RDT violation tiers, which only exist under the "
            "TCDC representation (transmission.apply_miso_rdt_tcdc)"
        )
    if getattr(config, "miso_rdt_tcdc", False) and iso == "MISO":
        from market_sim.model.transmission import apply_miso_rdt_tcdc

        iso_config = apply_miso_rdt_tcdc(iso_config, rpe_pricing=rpe_pricing)
        logger.info(
            "MISO %d: miso_rdt_tcdc — RDT pair replaced with 92%% default "
            "derate + $40/$500 TCDC tiers (2024 SOM §III.B)%s",
            year,
            (
                " + RPE $200 additive on violation tiers "
                "(miso_rpe_pricing, 2024 SOM §II.E/§III.B)"
                if rpe_pricing
                else ""
            ),
        )
    # 7. ``config.miso_zonal_loss_surface`` — split the Midwest-internal
    #    bilateral links (L1–L6) into one-way loss pairs so the measured
    #    marginal delivery-factor surface can enter the energy balance as
    #    hour-varying receiving-side loss fractions (miso-76 M3; the
    #    fractions themselves are built per solve year by
    #    transmission.build_miso_link_loss). Internal links only, so it
    #    composes with every step above (the RDT/South links are untouched
    #    — South separation stays RDT-owned, rule 19).
    if getattr(config, "miso_zonal_loss_surface", False) and iso == "MISO":
        from market_sim.model.transmission import apply_miso_zonal_loss_links

        iso_config = apply_miso_zonal_loss_links(iso_config)
        logger.info(
            "MISO %d: miso_zonal_loss_surface — Midwest L1-L6 split into "
            "one-way loss pairs (marginal delivery-factor physics, "
            "miso-76 charter §4)",
            year,
        )
    # 8. ``config.pjm_zonal_loss_surface`` — the PJM twin of step 7: split the
    #    internal PJM links into one-way loss pairs so PJM's own measured
    #    marginal delivery-factor surface can enter the energy balance as
    #    hour-varying receiving-side loss fractions (pjm-136 M2; the fractions
    #    are built per solve year by transmission.build_pjm_link_loss).
    #    Internal links only — the external star node keeps its per-border
    #    envelopes, measured ladders and net-position cut untouched, and the
    #    joint interface cuts match by zone pair with orientation signs, so
    #    this composes with every step above (rule 19).
    if getattr(config, "pjm_zonal_loss_surface", False) and iso == "PJM":
        from market_sim.model.transmission import apply_pjm_zonal_loss_links

        iso_config = apply_pjm_zonal_loss_links(iso_config)
        logger.info(
            "PJM %d: pjm_zonal_loss_surface — internal links split into "
            "one-way loss pairs (marginal delivery-factor physics, "
            "pjm-136 M2)",
            year,
        )
    # 9. ``config.caiso_zonal_loss_surface`` — the CAISO twin of steps 7-8:
    #    split the internal CAISO links into one-way loss pairs so CAISO's own
    #    measured marginal delivery-factor surface can enter the energy balance
    #    as hour-varying receiving-side loss fractions (caiso-164; the
    #    fractions are built per solve year by interchange.build_caiso_link_loss
    #    from CAISO_loss_surface.csv). Internal links only — the WECC seam keeps
    #    its measured hub prices, corridor groups and ATC envelopes untouched.
    #    Runs LAST so it splits the topology every earlier step has already
    #    settled; the caiso-163 directional path ratings are InterfaceLimits
    #    keyed on the zone PAIR, which build_interface_groups resolves onto
    #    both orientations with ±1 signs, so the published Path 15 / Path 26
    #    bounds survive the split exactly (rule 19 ``[R-ONE-MECH]``).
    if getattr(config, "caiso_zonal_loss_surface", False) and iso == "CAISO":
        from market_sim.model.interchange.caiso import apply_caiso_zonal_loss_links

        iso_config = apply_caiso_zonal_loss_links(iso_config)
        logger.info(
            "CAISO %d: caiso_zonal_loss_surface — internal links split into "
            "one-way loss pairs (marginal delivery-factor physics, caiso-164)",
            year,
        )
    # 10. ``config.nyiso_zonal_loss_surface`` — the NYISO twin of steps 7-9:
    #     split the four internal chain links (UW↔CH, CH↔LH, LH↔NYC, NYC↔LI)
    #     into one-way loss pairs so NYISO's own measured marginal
    #     delivery-factor surface can enter the energy balance as
    #     month-varying receiving-side loss fractions (nyiso-159; the
    #     fractions are built per solve year by
    #     interchange.build_nyiso_link_loss from NYISO_loss_surface.csv).
    #     Internal links only — the seam mechanisms (PAR attribution,
    #     deliverability envelope), import generators and every LCR/TSL cap
    #     act on generators/availability rather than these links and are
    #     untouched (rule 19). Runs LAST so it splits the topology every
    #     earlier step has already settled; the interface TTCs (incl. the
    #     year-varying Central-East overrides) ride on the links and
    #     transplant to both directions of each pair.
    if getattr(config, "nyiso_zonal_loss_surface", False) and iso == "NYISO":
        from market_sim.model.interchange.nyiso import apply_nyiso_zonal_loss_links

        iso_config = apply_nyiso_zonal_loss_links(iso_config)
        logger.info(
            "NYISO %d: nyiso_zonal_loss_surface — internal chain links split "
            "into one-way loss pairs (marginal delivery-factor physics, "
            "nyiso-159)",
            year,
        )
    return iso_config
