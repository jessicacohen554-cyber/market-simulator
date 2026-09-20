"""Legitimacy diagnostic suite — D-1 / D-2 / D-4 / D-5 / D-9 (audit §7).

Implements the keeper-gating diagnostics from
``docs/model-legitimacy-audit-2026-07.md`` §7 against a calibration bundle
directory plus the committed dashboard payloads:

* **D-1 diurnal shape** — per plant-class hour-of-day mean profile, model vs
  CAMPD (``frontend/data/backcast/bench/<ISO>/<year>.json.gz``): profile
  correlation and the model/actual coefficient-of-variation ratio over the
  off-peak hours (h0-14 local). A peaker/intermediate class fails when
  r < 0.8 or model CV < 0.5 × actual CV — the caiso-42 flat-floor signature
  (model CV 0.000 vs actual 0.35-0.45).
* **D-2 forced-energy attribution** — TWh dispatched AT a binding
  ``min_gen`` floor, by class × mechanism, using the int8 mechanism-id array
  threaded through ``FleetArrays`` (``data.floor_mechanisms``). Gates:
  forced share < 10 % for peaker classes, < 30 % for any merchant class
  (nuclear / CHP-steam / coal-take-or-pay exempt).
* **D-4 off-window binding** — per driver-gated floor, the share of floored
  MWh outside its justified hour window; fail > 5 %.
* **D-5 forecast/backcast parity** — the mechanism set active for the same
  ScenarioConfig in ``mode="backcast"`` vs ``mode="forecast"`` (including
  entry-point wiring: a mechanism built only in ``scripts/run_calibration.py``
  and never in ``src/market_sim/runner.py`` is backcast-only in practice);
  every difference must be on the declared backcast-overlay list built from
  ``docs/backcast-measured-data-audit-2026-06.md``.
* **D-9 overlay quarantine** — assert the measured-outcome overlay probes are
  OFF in the bundle's ``run_config.json`` (``ct_deployment_overlay``,
  ``reliability_deployment_overlay``, ``ct_mustrun_per_plant``,
  ``ordc_reliability_deployment_mw``, ``caiso_gas_commitment_floor``) and
  that a non-ERCOT ISO resolves no offer band from the ERCOT-fitted generic
  fallback (``data/offer_curves.py`` ``_GAS_TRANCHE_SHARES`` + the
  ``getattr`` heat-rate-multiplier literals) — neutral/per-ISO bands only.
  ``--keepers`` sweeps every keeper bundle registered in
  ``frontend/data/backcast/keepers.json`` (the CI quarantine mode).
* **D-6 holdout quarantine (CI, in ``--keepers`` mode)** — assert NO
  registered bundle (keeper or probe) declares a solve year outside the
  2023-2025 calibration window unless its ISO carries a calibration-complete
  marker in ``frontend/data/backcast/calibration-complete.json`` (which
  authorizes the one-shot frozen-config holdout score of 2022 / H1-2026 —
  CLAUDE.md rule 22, amended 2026-07-04).
* **D-2 recompute-vs-committed (CI, in ``--keepers`` mode, gap G-06)** —
  re-derive each keeper's D-2 forced-energy shares from the bundle's own
  committed data (dashboard run payload + a deterministic floor rebuild) and
  diff against the committed ``<bundle>/legitimacy_diagnostics.json``. Fails
  only on a discrepancy between the two (a stale/hand-edited artifact) —
  never on a forced-share breach that the committed artifact already
  discloses (those are known NOT-YET findings, not this gate's job).
* **D-10 free-class-only rescore** — per (year, fuel) wind/solar renewable-
  bound provenance (``market_sim.data.renewables.renewable_bound_provenance``):
  flags rows riding the L1 delivered-outcome bound (§4) as ``PINNED`` so a
  C1-style pass on them is never quoted as forecast skill. Report-only —
  wind/solar are already advisory-only in ``calibration_verdict.py`` and
  never gate a keeper verdict.

Model dispatch source: ``<bundle>/dispatch/<year>_P2.parquet`` (falling back
to ``_P1``) when present; otherwise the committed dashboard run payload
(``frontend/data/backcast/runs/<id>.js``, located via the registry sidecar
whose ``bundle`` field matches). Floors source: ``<bundle>/floors/
<year>_<pass>.npz`` (written by ``run_calibration_full.py`` since this
change); otherwise rebuilt through the real calibration prep path
(``run_year(fleet_only=True)``) from the bundle's ``meta.json`` flags — the
same code the run used, minus the LP solves. The rebuild carries every
fleet-level floor; the P2-layer RA must-offer bridge needs the P1 solution
and is therefore absent from rebuilt floors (noted in the report).

Usage::

    python scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO> \
        [--years 2023 2024 2025] [--report out.md] [--rebuild-floors]
    python scripts/legitimacy_diagnostics.py --keepers   # D-9/D-6/D-2 across keepers

Exits non-zero when any gate run in the invocation fails.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.data.floor_mechanisms import (  # noqa: E402
    D2_EXEMPT_MECHS,
    MECH_CAISO_GAS_COMMITMENT_FLOOR,
    MECH_CC_MUSTRUN_PER_PLANT,
    MECH_CHP_STEAM,
    MECH_COAL_MIN_CONFIG,
    MECH_COAL_MUSTRUN,
    MECH_CT_NETLOAD_DRAG,
    MECH_ERCOT_RUC_COMMITMENT,
    MECH_FIRM_IMPORT,
    MECH_GAS_COMMITMENT_BRIDGE,
    MECH_MISO_COAL_NIGHT_FLOOR,
    MECH_NYISO_GAS_COMMITMENT_BRIDGE,
    MECH_SOCO_GAS_ST_CAMPAIGN,
    MECH_SPP_GAS_COMMITMENT_BRIDGE,
    MECH_HYDRO_MIN_FLOW,
    MECH_HYDRO_ROR_FLAT,
    MECH_NAMES,
    MECH_RA_MUSTOFFER,
    MECH_RELIABILITY_FLOOR,
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
    MECH_ST_NETLOAD_DRAG,
    NON_THERMAL_MECHS,
)

# Single materiality line shared with the determination rubric: the D-2
# quarantine gate consumes the SAME constant the C7/C8 keeper scorer uses
# (calibration_verdict.PROTECTIVE_MIN_LOAD_FRAC), so the quarantine side can
# never run looser than the rubric it cites (CLAUDE.md rules 17/20/23 — one
# materiality line, no off-registry duplicate constant).
from scripts.calibration_verdict import PROTECTIVE_MIN_LOAD_FRAC  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import bench_multiclass as bm  # noqa: E402
from scripts.lib import holdout_policy  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402
from scripts.lib.known_unsynced_keepers import UNSYNCED_KEEPERS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("legitimacy_diagnostics")

# ---------------------------------------------------------------------------
# Gate constants (audit §7). Every threshold cites its audit row.
# ---------------------------------------------------------------------------

# D-1: peaker/intermediate diurnal-shape gate (audit §7 D-1; §1.1 evidence).
D1_MIN_PROFILE_R: float = 0.8
D1_MIN_CV_RATIO: float = 0.5
D1_OFFPEAK_LAST_HOUR: int = 14  # off-peak window = local hours 0..14 inclusive
# Classes gated; every class is still reported. Peaker + intermediate duty
# (the original caiso-42 set) plus, since the rubric v2.8 coal
# gate-blindness correction (ERCOT-121, 2026-07-27 — RATIFIED as an OWNER
# AMENDMENT 2026-07-27, miso-96; it shipped without the marker every prior
# tolerance change carries, and widening a PROTECTIVE gate set retroactively
# re-grades keepers in other lanes, so it is an owner call by construction.
# Rubric §9 ratification note), the merchant coal
# classes — ERCOT COAL_LIGNITE 2023 (profile r 0.745, cv_ratio 0.294: the
# lignite fleet pinned flat at its availability ceiling) carried the exact
# C7 failure signature ungated. CHP classes stay ungated (host-steam-pinned
# duty, same rationale as D2_EXEMPT_CLASSES).
# NOTE (rubric v3.1, owner amendment 2026-08-06): the C7 criterion this set
# used to feed is RETIRED — ``calibration_verdict.score_shape`` and its
# ``C7_GATED_CLASSES`` mirror of this tuple are deleted, so there is no longer
# a second set to keep in sync. D-1 itself is NOT retired: these rows are still
# computed, still written to every bundle, and still gated — by C8's
# grounded-above-budget escalation (``calibration_verdict._d1_shape``), which
# applies the ``gates`` block below to whichever class is over its forced-energy
# budget rather than to a fixed tuple. This set now governs only which rows
# carry a baked ``gated`` flag for reporting.
D1_GATED_CLASSES: tuple[str, ...] = (
    "CT_PEAKER",
    "ST_GAS",
    "COAL",
    "COAL_LIGNITE",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_WC",
)

# D-2: forced-share gates (audit §7 D-2 / §8 rule 19).
D2_PEAKER_CLASSES: tuple[str, ...] = ("CT_PEAKER",)
# Raised 0.10 -> 0.15 by owner amendment 2026-07-06 (CLAUDE.md rule 20 as
# amended; rubric v2.1). The calibration verdict (C8) gates each row's
# MEASURED forced_share against the rubric's own caps, so artifacts written
# under the old value re-score correctly without regeneration; this constant
# keeps future artifacts' embedded verdicts consistent with the rubric.
D2_PEAKER_MAX_SHARE: float = 0.15
D2_MERCHANT_MAX_SHARE: float = 0.30
# Materiality guard (owner directive, 2026-07-06): a merchant class is
# force-gated only when its energy exceeds this share of total system load. A
# class dispatching below the line is not "the dispatch model" for anything, so
# a high forced SHARE on it is a near-zero-denominator artifact, not the rule-20
# concern (floors propping up otherwise-economic dispatch). It is still reported
# per class (with load_share + an immaterial flag) but never raised to a FAIL.
# The threshold is the SINGLE rubric constant PROTECTIVE_MIN_LOAD_FRAC (0.02)
# imported from calibration_verdict — the C7/C8 keeper scorer's own line — so
# the quarantine gate and the rubric cannot diverge (they did: this gate used a
# duplicate 0.025, 0.5pp looser than the 0.02 the rubric/CLAUDE.md rule 20 cite,
# leaving a 2.0-2.5%-of-load class gated by the rubric yet skipped here). The
# materiality denominator is max(model, actual) class energy (mirroring
# score_shape / _class_load_share), so a binding floor cannot push a class under
# the line by its own forcing, and a model that zeroes a material class stays
# scored via the actual side. Total load = Σ payload fuelRows[*].m — the model's
# served-energy balance (per-fuel annual generation incl. signed net interchange).
# Classes whose floors are structural must-run, exempt from the share gates
# (their mechanisms are also in D2_EXEMPT_MECHS; the class-level exemption
# covers CHP tranches floored by any mechanism).
D2_EXEMPT_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")
# "At the floor" tolerance: quantization of the dashboard payload byte
# encoding (round(100*mw/nameplate) -> +-0.5% of nameplate) plus a relative
# band; a floor below FLOOR_MIN_MW is noise, not forcing.
D2_FLOOR_MIN_MW: float = 1.0
D2_REL_TOL: float = 0.02
# Which weight decided each year's D-2 plant-class vote (nyiso-233), recorded
# into the committed artifact so a fallback to the superseded ROW COUNT basis
# can never be silent. "capacity" is the basis; "row_count_fallback" means the
# year's floor rows carry no pmax AND the fleet_only backfill could not supply
# it, so that year's class denominators are exposed to the tranche-count defect
# of docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md.
PLANT_CLASS_VOTE_CAPACITY: str = "capacity"
PLANT_CLASS_VOTE_ROW_COUNT: str = "row_count_fallback"
_plant_class_vote_basis: dict[int, str] = {}
# Which DISPATCH SOURCE produced each year's per-plant rows (nyiso-242),
# recorded into the committed artifact for exactly the reason the vote basis
# above is: the substitution must never be silent. The two sources are NOT
# interchangeable — ``dispatch/<year>_<pass>.parquet`` carries every model
# plant, while the dashboard run payload carries only plants with a CEMS meter
# — and the parquet is gitignored, so it is absent from every committed bundle
# and a re-run from a clean checkout silently takes the payload path.
#
# MEASURED (nyiso-242, NYISO keeper `nyiso241_ctcommitted_span`): re-running
# the suite against the bundle WITH its `dispatch/` layer restored reproduces
# the committed artifact on every gating numeric (18 differing leaves of 1,851,
# ZERO of them a gating value); re-running WITHOUT it moves 1,416 leaves and
# 148 gating numerics. The script itself is byte-deterministic — two
# back-to-back runs are sha256-identical — so what was recorded in
# docs/RESULT-nyiso240-bench-attribution-promotion-2026-09-19.md §A.6 as a
# "3rd-decimal non-reproducibility" is this substitution, not nondeterminism.
_dispatch_source_basis: dict[int, str] = {}
# G-06: tolerance for the --keepers D-2 recompute-vs-committed staleness check,
# on the per-class GATED forced SHARE (rule-20 units). The keeper recompute is a
# LOWER-BOUND reconstruction, NOT a bit-faithful replay: it decodes dispatch from
# the committed dashboard payload (the solve `dispatch/*.parquet` is gitignored-
# absent) and rebuilds floors via run_year(fleet_only=True), which has no P0/P1
# solution and so OMITS the whole P0-run-pattern commitment-bridge family
# (ra_mustoffer_bridge, gas_commitment_bridge, nyiso_gas_commitment_bridge,
# miso_coal_night_floor — the check excludes those mechanisms from the
# committed side below; caiso-155 widened the exclusion from the RA leg to the
# family). The residual, once the bridges are
# excluded, is class-denominator attribution jitter: a boundary plant that bins
# into a different class across fleet builds shifts a class total by ~0.08 TWh.
# Measured worst case across the 6 keepers is CAISO CT_PEAKER at 1.65 pp (0.08
# TWh on a 2.1 TWh class); every other material class reproduces to < 0.2 pp. So
# 2.5 pp passes every faithful reproduction with margin while still catching a
# stale / hand-edited artifact (a material-class share off by > 2.5 pp — the
# #1488-class NYISO re-derivation staleness moved shares far more than that).
# Immaterial classes (< PROTECTIVE_MIN_LOAD_FRAC of load) are skipped entirely:
# their marginal floors bind on a knife edge, so the payload-decode reconstruction
# is numerically unstable there (e.g. NEISO ST_GAS swings ~15 pp) — reported,
# never gated, exactly as the C7/C8 rubric treats them.
D2_VERIFY_SHARE_TOL: float = 0.025

# D-4: justified hour windows per driver-gated floor mechanism, keyed
# (mechanism_id, plant_class) with None matching any class. Hours are local
# standard [start, end) — the model's t % 24 clock. Fail > 5 % off-window.
D4_MAX_OFFWINDOW_SHARE: float = 0.05
# D-4 PER-UNIT CONDUCT RIDER (owner decision 2026-08-16, nyiso-140 §5/§6.3 —
# adopted WITH K6', implemented at nyiso-143). The off-window test above is
# TAUTOLOGICAL for a floor whose declared window is all 24 hours: offwindow_
# share is 0.0 BY CONSTRUCTION, so an h0-23 mechanism can never fail D-4 and
# K6' leg (a) / rule 20 [R-FORCED-BUDGET]'s grounded-above-budget escalation
# both rest on a check that cannot fire. (Measured: every one of NYISO's six
# D-4 rows in the designated keeper declares h0-23.)
#
# The rider restores rule 17 [R-FLOOR-WINDOW]'s SUBSTANCE for those rows —
# does the driver evidence support binding in these hours? — at the grain the
# defect lives at. The class aggregate cannot see it: at nyiso-140 a single
# economically laid-up plant (Port Jefferson, 2517) absorbed 72.6 % of what
# the always-on Long_Island ST_GAS limb forced while its own CAMPD conduct was
# median CF exactly 0.000 in every hour block of every training year, and both
# live checks passed (D-4 by construction, D-2 because it is class-aggregate).
#
# The statistic is THRESHOLD-FREE and carries no free parameter (rule 5
# [R-NO-MAGIC] / rule 21 [R-DOF]): a floored plant fails provenance when its
# OWN measured (CAMPD bench) median hourly output over the declared window is
# EXACTLY ZERO — i.e. the meter says the unit is offline in at least half the
# hours the floor asserts it must be online. Materiality reuses the module's
# existing D2_FLOOR_MIN_MW; nothing new is introduced.
#
# SCOPE, deliberately narrow: all-hours windows only. A sub-daily window can
# already fail the off-window test on its own, so the rider is confined to the
# rows where that test is vacuous. Plants with no measured series (hydro,
# nuclear, renewables, interchange pseudo-units) are NOT scored and are
# disclosed by count — the rider is a measured-conduct test and cannot speak
# where there is no meter. It never fails a mechanism for a missing meter.
D4_CONDUCT_ALLHOURS_ONLY: bool = True
# CT reliability commitment is an evening-ramp phenomenon: the CAMPD
# derivation found overnight CT CF ~ 0 even at high net load
# (docs/caiso-ct-netload-drag-2026-06.md), so the justified window matches
# the ct_netload_drag ramp window [15, 22).
#
# The reliability_floor x CT_PEAKER window is [14, 22): the ct_netload_drag is
# the [15, 22) mechanism, but the temperature reliability-floor CT ramps carry
# their own driver-derived HB14-21 window (start_hour=14) — NYISO NYC_CT_ev /
# LI_CT_ev, reliability_floor_coeffs_NYISO.csv. Measured downstate CT CF at h14
# is 0.11-0.23 (CAMPD 2023-25 pooled NYC/LI), squarely inside the class's active
# ramp — h14 forcing there is driver-supported, not overnight over-firing. The
# prior [15, 22) inherited from the drag mislabeled that legitimate h14 binding
# as off-window (~27% of floored CT MWh) — a diagnostic-window artifact, not a
# rule-15 bug (G-05, docs/handoffs/g05-forced-energy-caiso-ct-nyiso-stgas-2026-07
# .md). Widening to [14, 22) affects ONLY NYISO (the only ISO whose CT ramp
# starts at h14; MISO's is [15, 21], ERCOT/PJM are 24h hot-day) and can only
# LOWER an off-window share (h14 moves in-window) — it never newly-fails an ISO.
D4_WINDOWS: dict[tuple[int, str | None], tuple[int, int]] = {
    # chp_steam (MECH_CHP_STEAM — fleet.py chp_grid_pmin_mw, the structural
    # steam-host grid floor; level from the p2 artifact / eia923_cf columns,
    # or the measured steam operating level under chp_steam_floor_p25 —
    # since WP-3 (owner-ruled 2026-07-19) the loading-when-on construction
    # for CAMPD-visible cogens plus the EIA-923 delivery-implied level for
    # CEMS-invisible ones, superseding the all-hours p25): the
    # driver-justified window is ALL 24 hours BY MEASUREMENT — host thermal
    # demand is around-the-clock (CAISO CC_CHP steam fleet: CEMS net flat
    # 0.65-0.76 GW across every hour-of-day, May-2023, hod max/min 1.16;
    # the ERCOT industrial-cogen conduct the original CHP_PMIN_CF_BY_PLANT
    # p2 floors were derived from is the same shape).
    #
    # **THE SECOND HALF OF THIS JUSTIFICATION WAS FALSE AND IS CORRECTED IN
    # PLACE, NOT DELETED (caiso-293, 2026-09-20).** It claimed: *"Under the
    # level swap the statistic additionally enforces the window per plant: a
    # rarely-online cogen's on-frequency (or delivered energy) collapses its
    # level toward 0 and it carries no operating-level floor (cyclers keep only
    # their p2/923-CF never-below base)."* This diagnostic's OWN per-unit
    # conduct rider falsified it on the CAISO keeper: 28 failing rows, 7
    # plants, all four years, every one of them a plant whose ``chp_pmin_cf``
    # is 0.0 — so the swap CREATED the whole floor rather than superseding a
    # smaller one — and whose hour-of-day on-frequency max/min is 12.4-35.0
    # (the evening ramp) against 1.00-1.04 for the three flat steam hosts the
    # first half cites. The statistic dilutes the LEVEL and leaves the HOURS at
    # 8760; those are different objects, and five metered floored plants were
    # thereby forced above their own whole-year meter.
    #
    # THE WINDOW STAYS (0, 24) ANYWAY, and deliberately. The repair
    # (``ScenarioConfig.chp_steam_duty_window``) confines the floor to a
    # per-plant TOP-K-BY-SYSTEM-LOAD window, which is a LOAD RANK and not an
    # hour-of-day band — D-4's window test cannot express it in either
    # direction, so narrowing this tuple would mis-score the repair as surely
    # as it mis-scored the defect. **The test that actually binds this
    # mechanism is the per-unit conduct rider below, not this row**, which is
    # why the defect surfaced there. D2-exempt structural must-run; row exists
    # for the rule-12/17 declaration, not for a C8 escalation path.
    (MECH_CHP_STEAM, None): (0, 24),
    # coal_min_config (MECH_COAL_MIN_CONFIG — the coal MINIMUM ONLINE
    # CONFIGURATION floor, config.ercot_coal_min_config_floor, ercot128): the
    # driver-justified window is ALL 24 hours BY DRIVER. The driver is the
    # plant's registered unit inventory — the least MW it can hold with at
    # least one unit synchronized, min_u MinLoad_u from EIA-860 — which is a
    # standing physical property, not an event. There is no hour in which the
    # driver says the bound does not apply: whenever the plant is synchronized
    # it applies, and whenever it is NOT (an outage) the floor is already zero
    # because min_gen is clipped to pmax x availability, so the mechanism binds
    # nowhere off-window by construction rather than by measurement. Rule 17
    # [R-FLOOR-WINDOW] forward story: the level re-derives from the next EIA-860
    # vintage with no model input (scripts/data/derive_eia860_coal_min_config.py).
    (MECH_COAL_MIN_CONFIG, None): (0, 24),
    # coal_mustrun (MECH_COAL_MUSTRUN — the coal SYNCHRONIZATION floor,
    # config.coal_sync_srmc_tranche, arrays.py::_compose_min_gen_floors step
    # 3a): the driver-justified window is ALL 24 hours BY DRIVER, and the row
    # exists so the CONDUCT leg can see the floor at all. The driver is the
    # plant's own CEMS-measured synchronization Pmin plus its measured online
    # SHARE (thermal_tranches_<ISO>.csv mustrun_online_pct / online_frac): the
    # floor is already hour-of-day-blind and instead load-ranked — a plant
    # measured synchronized all year is held every hour, a measured cycler
    # only in its top online_frac fraction of hours by system (or net) load.
    # So there is no hour-of-day the driver says it is off, and (0, 24) is the
    # faithful declaration; what D-4 then scores on this floor is entirely its
    # per-plant CONDUCT leg, i.e. whether the plant's own meter reads zero
    # across the hours the floor asserts it must be online.
    #
    # ADDED 2026-09-20 (pjm-h14). Until now MECH_COAL_MUSTRUN carried NO
    # D4_WINDOWS entry, so D-4 emitted no coal rows in any ISO and the coal
    # synchronization floor was the one commitment floor the rule-17 diagnostic
    # could not see. That is exactly the state rule 20 [R-FORCED-BUDGET]
    # describes ("its mechanism needs a cited D4_WINDOWS entry ... and that
    # bundle re-generated so the D-4 row exists"). This is a DIAGNOSTIC-ONLY
    # addition: it touches no solve path, changes no dispatch and moves no
    # scored band by construction — coal's D-2 forced share (0.4-3.7 % of
    # class energy in PJM) sits far below rule 20's 30 % budget, so the
    # over-budget escalation that reads D-4 never engages and no criterion can
    # move. Existing keepers re-score in place; new coal rows appear the next
    # time any bundle's diagnostics are regenerated, and a FAIL there is a
    # REPORTED rule-17 finding on that keeper, not a determination change.
    (MECH_COAL_MUSTRUN, None): (0, 24),
    # ercot_ruc_commitment (ercot-227 F3, MECH_ERCOT_RUC_COMMITMENT —
    # pipeline.commitment.wrap_ercot_ruc_floor_prep): BY-CONSTRUCTION 24 h
    # window. The floor is the measured NP3-965 ONRUC instruction-state LSL
    # sum per class-hour (derive_ercot_ruc_committed.py) — its driver-
    # justified window IS the measured instruction set, and the floor is
    # exactly zero wherever the series is zero, so an off-window bind is
    # impossible by construction (rule 17: driver = the operator's RUC
    # instruction, an outage-window-class input; forward story = no
    # disclosure forward, the bridge/drag commitment machinery governs).
    (MECH_ERCOT_RUC_COMMITMENT, None): (0, 24),
    # firm_import (MECH_FIRM_IMPORT — the CAISO/MISO/NYISO firm must-flow
    # import blocks: inject_caiso_firm_import_selfschedule,
    # inject_miso_firm_imports, inject_nyiso_firm_imports): the
    # driver-justified window is ALL 24 hours BY DRIVER. The driver is a
    # standing CONTRACT — RA/LTC import must-offer (CPUC D.20-06-028) and the
    # Manitoba / HQ firm delivery contracts — which obliges delivery around the
    # clock and names no hour at which it lapses; the shaped capability the
    # floor rides on already collapses the floor toward 0 in hours the measured
    # base is small, so the mechanism binds nowhere off-window by construction
    # rather than by measurement.
    #
    # ADDED at caiso-151. Until then MECH_FIRM_IMPORT carried NO row here and
    # is in both NON_THERMAL_MECHS (D-2 exempt) and MECH_ABLATION_KEPT, so a
    # 19-28 TWh/yr must-flow floor sat outside every legitimacy gate the repo
    # runs and had never been window-tested by anything (FINDING-caiso150 §A).
    # This row exists for VISIBILITY and the rule-12/17 declaration — with an
    # all-hours window an off-window FAIL is structurally impossible, so it is
    # not an escalation path; what it buys is that the floored TWh now appears
    # in every bundle's D-4 table instead of nowhere.
    #
    # The defect caiso-150 found was in the floor's LEVEL, not its window: its
    # shape basis (EIA-930 realised net corridor interchange) measures realised
    # flow = a price-insensitive core PLUS a price-elastic economic layer, so
    # the floor forced more price-insensitive import than CAISO's entire
    # measured price-insensitive intertie position in 47-49 % of 2024/25 hours.
    # That is reconciled by config.caiso_firm_import_selfsched_clip (caiso-151),
    # which clips the floor at the measured ceiling — a level fix, which is why
    # the window declared here is unchanged by it.
    (MECH_FIRM_IMPORT, None): (0, 24),
    (MECH_RELIABILITY_FLOOR, "CT_PEAKER"): (14, 22),
    (MECH_RELIABILITY_FLOOR, "CT_CHP"): (14, 22),
    # ct_netload_drag: the ERCOT/CAISO/PJM declaration. Their driver is SOLAR
    # COLLAPSE producing a sharp afternoon-evening net-load ramp, and their
    # measured CT CF profile peaks there. MISO's does NOT — see
    # D4_WINDOWS_BY_ISO below, which overrides this row for MISO alone.
    (MECH_CT_NETLOAD_DRAG, None): (15, 22),
    # ST_GAS netload drag: the driver-justified window is ALL 24 hours — the
    # CAMPD evidence base (docs/ercot-st-gas-netload-drag-2026-06.md) shows the
    # gas-steam fleet "committed every day and every night, never fully off",
    # with the overnight (23-05h) CF itself rising 0.03->0.36 with net-load
    # (Spearman rho 0.82, year-stable 2023-25). Unlike CT (overnight CF ~ 0),
    # there is no hour the class's own driver evidence says it is offline, so
    # the all-hours boiler floor (fleet.apply_gas_st_netload_drag_floor,
    # ramp_window=None) binds nowhere off-window by measurement, and this row
    # exists so rubric-v2.2 over-budget escalation scores it on evidence
    # rather than failing it for a missing declaration (rule 12).
    (MECH_ST_NETLOAD_DRAG, None): (0, 24),
    # reliability_floor × ST_GAS: the driver-justified window is ALL 24 hours.
    # Live blast radius is NYISO-only: the NYC/LI persistent-24h base limbs
    # (reliability_floor_coeffs_NYISO.csv, threshold −50 °C ⇒ always flagged,
    # no sub-daily window) are the only ENABLED ST_GAS limbs a keeper's floor
    # still owns — PJM's enabled ST_GAS limbs are drag-owned in its keeper
    # (gas_st_netload_drag drops them via iso_configs.
    # drop_drag_owned_reliability_specs) and every other ISO's are disabled.
    # Evidence base (G-05 adjudication, docs/handoffs/g05-forced-energy-caiso-
    # ct-nyiso-stgas-2026-07.md): measured CAMPD 2023-25 downstate steam is
    # online 100 % of the year with overnight CF 0.11-0.20 — there is NO hour
    # the class's own driver evidence says it is offline (the opposite of the
    # CT overnight-offline signature), so the persistent base binds nowhere
    # off-window by measurement; D-1 diurnal shape passes every year (profile
    # r 0.95-0.96, cv_ratio 0.69-0.90). The all-hours gas_st_netload_drag
    # alternative (the ERCOT-46/PJM-94 keeper mechanism, which post-dates
    # G-05's windowed-[15,22) rejection premise) was re-evaluated 2026-07-09
    # and REJECTED on its own honesty gates
    # (scripts/data/derive_nyiso_st_gas_netload_drag.py): the downstate base is
    # flat vs net-load below ~15 GW and its level drifts across years at
    # equal net-load (overnight Spearman rho 0.32/0.39/0.72 class-wide,
    # 0.30/0.28/0.57 NYC+LI-only — not year-stable), and the pooled hinge
    # overshoots the 2023 measured class energy (142 %). The commitment is an
    # UNCONDITIONAL local-reliability base (downstate DARU/SRE commitments +
    # steam-boiler min-run blocks), not a net-load-hinged one, so the
    # persistent reliability_floor remains the class's single grounded
    # mechanism (rule 19) and this row exists so rubric-v2.2 over-budget
    # escalation scores it on evidence rather than failing it for a missing
    # declaration (rule 12).
    (MECH_RELIABILITY_FLOOR, "ST_GAS"): (0, 24),
    # Midday NG:NG slab window (h9-16) — the probe's own gate
    # (transmission.inject_caiso_gas_commitment_floor).
    (MECH_CAISO_GAS_COMMITMENT_FLOOR, None): (9, 17),
    # cc_mustrun_per_plant (per-plant gas local-reliability commitment,
    # fleet.py cc_mustrun_pmin_mw, CC_REGULAR only): the floor's REAL window
    # is intrinsic and per-plant — each plant's committed tranche binds only
    # in its top measured-online_frac fraction of hours ranked by system
    # load, so the mechanism is self-windowing by construction. The
    # hour-of-day row here declares where that placement is driver-justified:
    # a committed CC is SYNCHRONIZED around the clock inside its window (the
    # CEMS online_frac it is sized from counts overnight min-stable hours —
    # same evidence shape as the ST_GAS rows above), so CC_REGULAR is
    # all-hours. (The mechanism's CT_PEAKER leg was probed 2026-07-11 under a
    # declared h7-22 window and DROPPED for 12.8% overnight off-window
    # binding — the rule-12 check this registry exists to perform.)
    (MECH_CC_MUSTRUN_PER_PLANT, "CC_REGULAR"): (0, 24),
    # st_gas_mustrun_per_plant (the ST_GAS leg of the same per-plant
    # local-reliability commitment floor, fleet.py cc_mustrun_pmin_mw with
    # MECH_ST_GAS_MUSTRUN_PER_PLANT attribution): self-windowing by
    # construction like the CC leg — each plant's committed tranche binds
    # only in its top measured-online_frac fraction of hours ranked by
    # system load. The driver-justified hour-of-day window is ALL 24 hours:
    # the evidence base is the Entergy MISO-South VLR/self-commitment trace
    # (Nine Mile synchronized 98.2% of ALL hours 2023-2025 incl. overnight
    # min-stable, Sabine 85.6%, Lewis Creek 87.8%), the same around-the-
    # clock-synchronized evidence shape as the ST_GAS rows above — no hour
    # the class's own driver evidence says these boilers are offline
    # (opposite of the CT overnight-offline signature). Row exists so
    # rubric-v2.2 over-budget escalation scores on evidence rather than
    # failing a missing declaration (rule 12).
    (MECH_ST_GAS_MUSTRUN_PER_PLANT, "ST_GAS"): (0, 24),
    # ercot_gas_commitment_bridge (ERCOT-63, MECH_GAS_COMMITMENT_BRIDGE —
    # pipeline.commitment.ercot_gas_bridge_p1_floor_fleet): the P1-native
    # gas-CC committed-state bridge. Rule-12 declaration:
    # * WINDOW — self-windowing by construction, ALL 24 hours by driver. Two
    #   placements, both anchored to the model's own P0 run pattern rather than
    #   to any clock hour:
    #   (a) GAP legs (default): the floor exists inside an idle gap between two
    #       P0-detected runs of the same plant, each gap shorter than the unit's
    #       physical min-down (a restart bar) or bounded by one DA operating day
    #       (DA_COMMITMENT_HORIZON_HOURS) on the economic leg. Measured incidence
    #       is overnight-dominated (the keeper's 2023 dispatch cycles 902 CC
    #       plant-nights/yr off overnight between run-days, ~1.07 GW mean —
    #       diagnosis §5), the overnight analogue of the CAISO midday gap.
    #   (b) ONLINE-HOURS leg (ercot141, ScenarioConfig.ercot_gas_bridge_online_
    #       hours, default off): the floor ALSO covers every hour of a detected
    #       RUN. The gap legs model the restart DECISION; this leg models the
    #       committed STATE those gaps interpolate between — a synchronized unit
    #       cannot operate below its minimum stable load, so its LSL block is
    #       must-take in every online hour. There is no hour of day the driver
    #       declares it off (being synchronized is not a clock-hour property),
    #       and it binds nowhere off-window BY CONSTRUCTION rather than by
    #       measurement: the leg only floors hours the model's own P0 pattern
    #       already has the plant online, and min_gen is clipped to
    #       pmax × availability, so an offline or outaged plant carries a zero
    #       floor. It cannot force a start. (Same rationale shape as
    #       MECH_COAL_MIN_CONFIG above: a standing physical property, not an
    #       event.) Bounded above by measurement, too — the floor target clips
    #       at the committed tranche's own capacity, whose gas-CC share (p50
    #       0.250, max 0.550, 41/41 plants) is BELOW the measured LSL fraction
    #       0.574, so the leg never holds more than the unit's real minimum.
    # * DRIVER — DAM one-operating-day commitment + the unit-commitment
    #   restart inequality (published per-MW startup costs, physical
    #   min-down, the model's own P0 duals); min-load = the measured
    #   committed-CC LSL/HSL cap-weighted p50 (60-Day DAM disclosure).
    # * FORWARD STORY — regenerates in any forecast year from the model's
    #   own P0 run pattern + physical constants; no measured series enters
    #   (the CAISO RA bridge convention, rules 13/18).
    (MECH_GAS_COMMITMENT_BRIDGE, "CC_REGULAR"): (0, 24),
    # nyiso_gas_commitment_bridge (nyiso-87, MECH_NYISO_GAS_COMMITMENT_BRIDGE —
    # pipeline.commitment.build_nyiso_gas_bridge_p1_prep): the P1-native
    # committed-state bridge on NYISO's merchant slow-start gas fleet, the
    # REPLACEMENT for the h14-21 peak-window reliability-floor limbs (owner
    # directive 2026-07-27). Rule-12 declaration, for both floored classes:
    # * WINDOW — self-windowing by construction, ALL 24 hours by driver. The
    #   floor exists ONLY (a) inside an idle gap between two P0-detected runs
    #   of the same plant — shorter than the unit's physical min-down (a
    #   restart bar) or bounded by one DA operating day on the economic leg —
    #   or (b) in the hours immediately following a P0 run-start that are
    #   inside the unit's own MINIMUM RUN DURATION, or (c) when the
    #   ONLINE-HOURS leg is armed (nyiso_gas_bridge_online_hours, the
    #   ercot141 floor_online_hours leg), in every hour of a P0-detected run
    #   itself — the LSL must-take of the committed STATE the gap legs
    #   interpolate between; still anchored to the model's own run pattern,
    #   never a clock hour, and capped at the base tranche's own capacity.
    #   No placement is a clock-hour rule: all are anchored to the model's
    #   own run pattern, so there is no hour of day the mechanism is declared
    #   off. That is the POINT of the substitution — the boxcar it replaces
    #   asserted a fixed afternoon window and bound in hours (overnight CT
    #   CF ~= 0) its own driver evidence said the class was offline.
    # * DRIVER — unit-commitment physics only: minimum run duration, minimum
    #   down time, and the restart inequality (published per-MW startup costs
    #   from NREL/SR-5500-55433, the model's own P0 duals). Minimum stable
    #   load is the measured per-class CAMPD loading-when-on statistic
    #   (CC 0.523 / ST_GAS 0.239 — derive_campd_gas_commitment_params.py).
    # * FORWARD STORY — regenerates in any forecast year from the model's own
    #   P0 run pattern plus physical constants; no measured series enters the
    #   detector (rules 13/18), and the min-load fractions re-derive only when
    #   the CAMPD vintages update (rule 23).
    (MECH_NYISO_GAS_COMMITMENT_BRIDGE, "CC_REGULAR"): (0, 24),
    (MECH_NYISO_GAS_COMMITMENT_BRIDGE, "ST_GAS"): (0, 24),
    # CT_PEAKER leg of the SAME mechanism (nyiso-90,
    # ScenarioConfig.nyiso_gas_bridge_ct): day-ahead BLOCK COMMITMENT on the
    # fast-start peaker class. This row needs its own justification because the
    # CT overnight-offline signature is exactly what rule 17 [R-FLOOR-WINDOW]
    # exists to catch, and a CT floor was rejected on it before (the
    # cc_mustrun_per_plant CT leg, G-20 probe 2026-07-11, 12.8 % overnight
    # binding under a declared h7-22 window).
    # * WHY THIS IS NOT THAT FLOOR — the G-20 leg placed CT capacity by an
    #   EXOGENOUS CLOCK (a plant's top-online_frac hours ranked by system load),
    #   so it could and did assert CT output in hours the class was offline.
    #   This leg has no clock at all: on a CT ONLY the min-run extension can
    #   fire (1 h min-down makes the physical bridge unreachable and fails
    #   RA_BRIDGE_ECON_MIN_DOWN_HOURS for the economic one), and the extension
    #   can only extend a run the MODEL ITSELF STARTED in P0 on its own
    #   economics. It cannot start a unit; it can only refuse to stop one
    #   inside its minimum run. An overnight-floored CT hour is therefore
    #   always the tail of a model-chosen evening start.
    # * WINDOW — ALL 24 hours by driver, and the class's own measured evidence
    #   supports it HERE where it did not there: the CAMPD 2023-2025 CT record
    #   is 34,024 runs with a cap-weighted p50 of 4 h and p90 of 14 h
    #   (campd_ct_commitment_params_NYISO.csv), and a 14 h run necessarily
    #   spans night hours. "The fleet's overnight CF is ~0" and "a started
    #   turbine stays on ~4 h" are both true and are not in conflict: the first
    #   is about STARTS, which this mechanism never creates.
    # * DRIVER — minimum run duration only. Level = the measured CT
    #   loading-when-on statistic (0.238 cap-weighted p50); horizon = 2 h, the
    #   cap-weighted p25 of the measured run distribution (the low order
    #   statistic, because an observed run bounds a min-run CONSTRAINT from
    #   above). Both from derive_campd_gas_commitment_params.py --ct.
    # * FORWARD STORY — regenerates in any forecast year from the model's own
    #   P0 run pattern plus the two measured class constants, which re-derive
    #   only on a CAMPD vintage change (rules 13/23).
    (MECH_NYISO_GAS_COMMITMENT_BRIDGE, "CT_PEAKER"): (0, 24),
    # spp_gas_commitment_bridge (SPP-44, MECH_SPP_GAS_COMMITMENT_BRIDGE —
    # pipeline.commitment.build_spp_gas_bridge_p1_prep): the SPP leg of the
    # same P1-native committed-state bridge, on SPP's merchant slow-start gas
    # fleet by the rule-18 physics gate (CC min-down 4-6 h / $50 per MW;
    # ST_GAS 8-12 h / $35; the CT classes fail on their 1 h min-down and are
    # never bridged). Rule-17 declaration, both floored classes
    # (PRECOMMIT-spp-44-2026-09-07 §3):
    # * WINDOW — self-windowing by construction, ALL 24 hours by driver: the
    #   floor exists ONLY inside an idle gap between two P0-detected runs of
    #   the same plant (shorter than the unit's min-down, or bounded by one DA
    #   operating day on the restart-economics leg) or in the hours after a
    #   P0 run-start inside the plant's own measured minimum run. No clock
    #   hour is declared off. The measured record supports it: SPP's eligible
    #   plants show ~1,100-1,300 CC and ~300 ST_GAS idle gaps of min-down…24 h
    #   per year in CAMPD 2023-2025 (spp44/footprint.csv).
    # * DRIVER — unit-commitment physics only: minimum run, minimum down and
    #   the restart inequality at the model's own P0 duals; level = the
    #   measured PLANT-basis minimum stable load
    #   (constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC, CC 0.209 / ST_GAS 0.090) and
    #   the measured plant-basis run-length p25
    #   (constants.SPP_GAS_BRIDGE_MIN_RUN_HOURS, 15 / 5 h).
    # * FORWARD STORY — regenerates in any forecast year from the model's own
    #   P0 run pattern plus four measured constants that re-derive only on a
    #   CAMPD vintage change (rules 13/23).
    (MECH_SPP_GAS_COMMITMENT_BRIDGE, "CC_REGULAR"): (0, 24),
    (MECH_SPP_GAS_COMMITMENT_BRIDGE, "ST_GAS"): (0, 24),
    # soco_gas_st_campaign_commitment (SOCO-53d, MECH_SOCO_GAS_ST_CAMPAIGN —
    # pipeline.commitment.build_soco_gas_st_campaign_p1_prep): the SOCO leg of
    # the same P1-native committed-state family, on SOCO's gas-STEAM fleet
    # alone. ST_GAS is a MATERIAL class for SOCO (>= 2 % of load), so under
    # rule 20 [R-FORCED-BUDGET] this row is the escalation path a forced share
    # above the 30 % cap would be scored on — it must exist. Rule-17
    # declaration (PRECOMMIT-soco-53d-2026-09-19 §4):
    # * WINDOW — self-windowing by construction, ALL 24 hours by driver, and
    #   here the driver evidence is unusually direct. Only two legs of the
    #   detector are armed: the measured minimum-RUN extension and the
    #   online-hours LSL state floor. Both are anchored to the model's OWN P0
    #   run pattern — the floor exists in the hours of a P0-detected run, or in
    #   the hours following a P0 run-start that lie inside the plant's own
    #   measured minimum campaign. There is no clock hour anywhere in the
    #   mechanism, so no hour of day is declared off, and it can never START a
    #   plant: it can only refuse to let one sink below its minimum stable load
    #   inside a campaign the model itself began. The restart legs are NOT
    #   armed (startup_bridge off), so no gap is ever bridged.
    # * DRIVER — campaign-commitment physics, and its evidence is the plant's
    #   OWN meter: SOCO's gas boilers are synchronized 63.9-92.0 % of all hours
    #   with 5.0-9.7 campaigns a year (CAMPD 2023-2025, plant grain,
    #   campd_gas_st_campaign_params_SOCO.csv), against 10-349 model starts of
    #   2-11 h median. MEMBERSHIP is that same statistic: a plant synchronized
    #   less than half the year is standby iron and is never floored, which is
    #   what keeps this mechanism out of the failure mode rule 17 exists to
    #   catch. Measured at the arm, every plant-year's floored share lands at
    #   or below that plant's own synchronized share.
    # * FORWARD STORY — regenerates in any forecast year from the model's own
    #   P0 run pattern plus a per-plant artifact that re-derives only on a
    #   CAMPD vintage change (rules 13/23). No measured generation enters the
    #   detector; the meter sets the LEVEL and the POPULATION, never the
    #   placement.
    (MECH_SOCO_GAS_ST_CAMPAIGN, "ST_GAS"): (0, 24),
    # miso_coal_night_floor (miso-113, MECH_MISO_COAL_NIGHT_FLOOR —
    # pipeline.commitment.build_miso_coal_night_floor_p1_prep): the P1-native
    # within-run NIGHT floor on MISO's regulated PRB/subbituminous coal fleet,
    # the successor to the two REJECTED offer-side arms (miso-111
    # coal_prb_committed_dispatchable, miso-112 coal_prb_committed_split).
    # COAL_PRB is a MATERIAL class (>= 2 % of MISO load), so under rule 20
    # [R-FORCED-BUDGET] this row is the escalation path a forced share above
    # the 30 % cap is scored on — it must exist, and it is keyed on the
    # mechanism alone so the row appears whichever coal class label the
    # bundle's attribution carries. Rule-12/17 declaration:
    # * WINDOW — self-windowing by construction, ALL 24 hours by driver. The
    #   floor exists ONLY inside a P0-detected committed RUN of the plant's
    #   own `_committed` tranche (the ercot141 online-hours leg), or inside an
    #   idle gap shorter than that unit's physical min-down — a restart bar,
    #   not a commitment choice. There is no clock-hour rule anywhere in it,
    #   so no hour of day is declared off; and because the runs come from the
    #   MODEL's own P0 pattern, a plant the model has offline is never
    #   floored. The mechanism cannot start a unit, only refuse to let one
    #   sink below its measured night level while it is already running —
    #   which is why it cannot reproduce the failure mode rule 17 exists to
    #   catch (a floor asserting output in hours its driver says the class is
    #   offline).
    # * DRIVER — regulated SELF-COMMITMENT. MISO SOM Table 7: 53-56 % of coal
    #   starts in the training window are self-committed rather than
    #   market-committed, i.e. the commitment decision is made by a
    #   cost-of-service owner outside the energy market's economics, which is
    #   exactly the decision an economic LP cannot represent. Population =
    #   the EIA-860 regulated / cost-of-service-majority set
    #   (eia860_selfcommit_scope_plants), the same scope the take-or-pay
    #   discount already uses.
    # * LEVEL — each plant's OWN measured within-run night loading
    #   (night_p50 = p50 of load/HSL over online hours h0-5, pooled 2023-2025,
    #   WP-3 loading-when-on), NET of that plant's own `_mustrun` band so the
    #   plant TOTAL is exactly night_p50 x capacity and never mustrun + night
    #   (rule 19 [R-ONE-MECH]); composed by MAXIMUM against reliability_floor,
    #   so the two can never sum on a shared unit-hour.
    # * FORWARD STORY — regenerates in any forecast year from that year's own
    #   P0 run pattern plus the frozen measured level, which re-derives only
    #   on a CAMPD vintage change (rule 23 [R-FROZEN-DERIVE],
    #   scripts/data/derive_prb_committed_split.py).
    (MECH_MISO_COAL_NIGHT_FLOOR, None): (0, 24),
    # hydro_min_flow (caiso-124, MECH_HYDRO_MIN_FLOW — data.hydro.
    # build_hydro_fleet / allocate_min_flow_floor -> FleetArrays.min_gen): the
    # conventional-hydro minimum-flow floor. Rule-12/17 declaration:
    # * WINDOW — ALL 24 hours BY PHYSICS. River inflow and the environmental /
    #   FERC-licence minimum releases a licensed project must pass are
    #   around-the-clock obligations; there is no hour the driver evidence says
    #   the class is off, which the measured series states directly (CISO
    #   EIA-930 NG:WAT 2023-25 never approaches zero in ANY hour-of-day bucket —
    #   the diurnal minimum-of-means is 1.7/1.4/1.2 GW at hod 11-13, and the
    #   hourly p5 over the whole year is 954/876/738 MW). Contrast the CT
    #   overnight-offline signature that rule 12 exists to catch. The floor
    #   therefore cannot bind off-window, and this row makes that scorable
    #   rather than a missing declaration.
    # * DRIVER — run-of-river inflow that physically cannot be stored plus
    #   licence minimum flows. The hydro budget family caps monthly ENERGY with
    #   no lower bound, so the economic LP parks the fleet at 0 MW (CAISO keeper:
    #   268/688/592 h below 10 MW in 2023/24/25) where reality does not.
    # * LEVEL — the fleet's measured monthly exceedance level (Q95;
    #   constants.HYDRO_MIN_FLOW_PERCENTILE is the MIRROR of the ceiling's
    #   HYDRO_ENVELOPE_PERCENTILE, so no new free parameter enters), allocated
    #   per plant pro-rata by its own share of the month's energy budget. The
    #   level is MONTH-CONSTANT by design: a (month x hour-of-day) floor would
    #   pin the measured diurnal shape (rule 13) and measures out at ~75 % of
    #   the annual budget, against 36-46 % for the month-constant form.
    # * FORWARD STORY — re-derives from the same EIA-930 history the ceiling
    #   uses (own year in a backcast, pooled HYDRO_CLIMATOLOGY_YEARS otherwise)
    #   and scales with the water year through the budget it is clipped to.
    # Non-thermal forcing (NON_THERMAL_MECHS): reported by D-2, excluded from
    # the merchant thermal forced-share arithmetic — hydro units also carry no
    # CAMPD plant_group, so they sit in the unclassified '' bucket the D-2
    # summary never gates. Row exists for the rule-12/17 declaration, not for a
    # C8 escalation path.
    (MECH_HYDRO_MIN_FLOW, None): (0, 24),
    # hydro_ror_flat (caiso-126, MECH_HYDRO_ROR_FLAT — data.hydro.
    # build_hydro_fleet under config.hydro_ror_split -> FleetArrays min_gen +
    # availability, min == max == budget[g,m]/hours[m]): run-of-river flat
    # dispatch. Rule-12/17 declaration:
    # * WINDOW — ALL 24 hours BY PHYSICS, same evidence as hydro_min_flow
    #   above: run-of-river/conduit inflow is an around-the-clock quantity;
    #   the flat level is month-constant so no diurnal shape is pinned
    #   (rule 13).
    # * DRIVER — plants the external hydro-plant-modes classifier (ORNL EHA
    #   FY2024 Mode + the documented HILARRI reservoir-association /
    #   canal-type / Corps-dam completion) marks NON-shapeable cannot chase
    #   price; the budget LP otherwise gives them full within-month shaping
    #   freedom (caiso-125 §4c: degenerate per-plant water values, the fleet
    #   rides the envelope as one bang-bang block).
    # * LEVEL — the plant's OWN monthly energy budget spread flat
    #   (budget[g,m]/hours[m]) — a quantity every solve already loads; zero
    #   new free parameters (the classifier is categorical, no threshold).
    # * FORWARD STORY — the classification is a static plant attribute
    #   (re-curated only when the EHA/HILARRI sources update, rule 21); the
    #   level rides the budget, so it regenerates for any forecast year and
    #   scales with the water year automatically.
    # Rule 19: ONE family with hydro_min_flow — an RoR unit never also
    # carries a min-flow stamp (build_hydro_fleet allocates the reconciled
    # floor over the reservoir class only). Non-thermal forcing
    # (NON_THERMAL_MECHS), unclassified '' plant_group bucket — the row
    # exists for the rule-12/17 declaration, not a C8 escalation path.
    (MECH_HYDRO_ROR_FLAT, None): (0, 24),
    # unit_outage_maxgen_events (M-2 declared-event-window revealed derates)
    # carries NO row here BY CONSTRUCTION, and this note is its rule-12
    # window declaration (the design's "D4_WINDOWS entry for the maxgen
    # mechanism id" — docs/handoffs/miso-price-formation-design-2026-07.md
    # §3/M-2): D-4 scores min_gen FLOOR mechanisms (this registry's keys are
    # floor-mechanism ids from data/floor_mechanisms.py), while the maxgen
    # channel is an AVAILABILITY DERATE that never raises min_gen and so can
    # never bind at all, on- or off-window. Its declared window set is
    # exactly the maxgen-events registry windows (data/raw/maxgen-events/,
    # hour-granular, clipped to the declared start/end): the derate arrays
    # are 1.0 outside those windows by construction — enforced by the
    # deriver's window clipping + the loader's half-open hour masks and
    # asserted by tests/test_maxgen_outages.py (off-window byte identity).
    # An off-window derate is therefore structurally impossible, which is
    # the property D-4 exists to check; the channel's admissibility
    # declaration lives in the D-5 registry ("unit_outage_maxgen_events",
    # backcast_only).
    #
    # maxgen_emergency_tier_pricing (F5 declared-window ELMP emergency-tier
    # pricing) likewise carries NO row here BY CONSTRUCTION, and this note is
    # its rule-12 window declaration (frozen design docs/handoffs/
    # miso-f5-scarcity-depth-design-2026-07.md §1d): it is a PRICE-SIDE
    # load-slack repricing (min(voll, SOM-footnoted tier floor) inside
    # registry windows declared at Max Gen Warning or higher) that never
    # raises min_gen and so can never bind as a floor, on- or off-window.
    # Its declared window set is exactly the maxgen-events registry's
    # Warning+ rows on the same hour-granular model clock as the M-2
    # derates; outside those windows the slack cost EQUALS the ISO voll by
    # construction (data.maxgen_events.emergency_tier_slack_cost initializes
    # at voll and only ever lowers via min), so an off-window pricing effect
    # is structurally impossible — asserted by
    # tests/test_maxgen_tier_pricing.py (off-window/off-state byte
    # identity). Admissibility declaration: D-5 registry
    # ("maxgen_emergency_tier_pricing", backcast_only).
    #
    # caiso_charge_allocation_schedule (M1, caiso-104 — the owner-granted
    # caiso-103 belly ask) likewise carries NO row here BY CONSTRUCTION, and
    # this note is its rule-12 window declaration: it is a CHARGE-SIDE
    # per-day allocation floor on the fleet battery Chg columns
    # (dispatch._build_storage_alloc_rows — Chg_fleet[h] >= alloc_share[hod]
    # x da_frac x day-total charge, the Fourier-Motzkin elimination of the
    # ask's S[d] variable) that never raises any generator's min_gen and
    # creates NO merchant-class generation, so D-2/D-4 (which score thermal
    # min_gen floor mechanisms) cannot see it and C8 is untouched by
    # construction. Its declared window is the measured DAM-allocation shape
    # support (hod with alloc_share > 0 — hod 1-17 in every derived year;
    # evening/late shares are measured ~0, so the floor forces nothing there
    # BY CONSTRUCTION: a zero share is a zero row). Volume-holding: a
    # zero-charge day is feasible (S=0), asserted by
    # tests/test_caiso_charge_allocation.py. Statistics: the committed
    # rule-23 derive data/raw/reference/caiso-charge-allocation-profile.csv
    # (scripts/data/derive_caiso_charge_allocation.py); binding-share and
    # forced-reallocation MWh are reported per-leg in the FINDING from the
    # solved bundle's storage.parquet (charge-side conduct, not gated here).
}

# PER-ISO overrides of a :data:`D4_WINDOWS` declaration (miso-230, 2026-09-06).
#
# The base registry can declare only ONE window per (mechanism, class), which is
# correct for a mechanism whose driver-justified hours are the same everywhere.
# It is WRONG for a mechanism whose window is DERIVED from the ISO's own
# measured conduct, because that derivation has a different answer in each
# market — and rule 25 [R-ISO-SCOPE] forbids carrying one ISO's answer into
# another. Declaring a single window then convicts the ISO whose real driver
# sits elsewhere, which is a defect in the declaration, not in the mechanism.
#
# ct_netload_drag is exactly that mechanism. ERCOT's / CAISO's / PJM's [15, 22)
# is justified by SOLAR COLLAPSE producing a sharp evening net-load ramp. MISO
# carries far less solar, and its measured CT_PEAKER conduct says the commitment
# is a broad high-net-load DAYTIME phenomenon: pooled 2023-2025 CAMPD hourly CF
# over the model's 127 pure-play CT_PEAKER plants rises from 0.0284 at h00 to a
# 0.1567 peak at h17 and falls back to 0.0340 by h23, with Spearman
# rho(CF, net load) positive in EVERY hour and >= 0.69 across h10-h20 — while
# MISO's MIDDAY block (rho 0.743/0.691/0.734) is as strongly driven as its
# evening (0.706/0.636/0.743). Declaring ERCOT's [15, 22) for MISO would score
# h10-h14 — carrying 1,744-2,359 MW of mean floor, the largest part of the
# mechanism's footprint — as OFF-WINDOW binding, i.e. would fail the drag for
# binding in the hours MISO's own driver evidence says it should.
#
# MISO's window [10, 21) is DERIVED, with zero free parameters, by
# scripts/data/derive_miso_ct_netload_drag.py: the maximal contiguous run of
# local-standard hours whose pooled mean CF is at or above the fleet's OWN 24-h
# mean CF (0.0850 — the data's own daily average, not a chosen level) and whose
# rho(CF, net load) is positive. Re-derived independently per year by the same
# rule it reads [9, 21) / [10, 21) / [11, 22), i.e. year-stable to +/-1 h. The
# frozen record is data/raw/reference/miso_ct_netload_drag.json (ISO-stamped)
# and the derivation is rule 23 [R-FROZEN-DERIVE] frozen against residuals.
#
# As with every windowed floor in this registry, the drag is ZERO outside its
# configured window BY CONSTRUCTION (fleet.apply_netload_reliability_floor's
# ``ramp_window`` gate), so an off-window bind is structurally impossible and
# this row is a rule-12/17 DECLARATION rather than an escalation path. What it
# buys is that the declaration names the window MISO's driver actually
# justifies, so the rule 18 [R-FORCED-BUDGET] conditional-pass leg (a) scores
# the mechanism on its own evidence instead of on another market's.
D4_WINDOWS_BY_ISO: dict[str, dict[tuple[int, str | None], tuple[int, int]]] = {
    "MISO": {
        (MECH_CT_NETLOAD_DRAG, None): (10, 21),
    },
}


def resolve_d4_windows(
    iso: str | None,
) -> dict[tuple[int, str | None], tuple[int, int]]:
    """Return :data:`D4_WINDOWS` with *iso*'s per-ISO overrides applied.

    A mechanism whose driver-justified window is derived from the ISO's own
    measured conduct gets its window from :data:`D4_WINDOWS_BY_ISO`; every other
    row is the shared declaration. An ISO with no override entry (and ``None``)
    gets the base registry unchanged, so every existing bundle scores exactly as
    before.

    Args:
        iso: The bundle's ISO, or ``None`` when it is not known.

    Returns:
        The window registry D-4 should score this bundle against.
    """
    over = D4_WINDOWS_BY_ISO.get((iso or "").upper())
    if not over:
        return D4_WINDOWS
    return {**D4_WINDOWS, **over}


# D-9: overlay probes that must be OFF/zero in every keeper run_config.json
# (audit §7 D-9; measured-outcome pins, CLAUDE.md #13).
D9_FORBIDDEN_FLAGS: dict[str, object] = {
    "ct_deployment_overlay": False,
    "reliability_deployment_overlay": False,
    "ct_mustrun_per_plant": False,
    "ordc_reliability_deployment_mw": 0.0,
    "caiso_gas_commitment_floor": False,
}
# The ERCOT-fitted getattr fallback literals in the offer path
# (offer_curves.py:535-550): (plant groups, committed override, econ
# override + literal, peak override + literal).
D9_HR_FALLBACKS: tuple[tuple[tuple[str, ...], str, str, float, str, float], ...] = (
    (
        ("CC_REGULAR", "CC_CHP"),
        "cc_committed_hr_override",
        "cc_econ_hr_override",
        1.2,
        "cc_peak_hr_override",
        1.8,
    ),
    (
        ("ST_GAS",),
        "gas_st_committed_hr_override",
        "gas_st_econ_hr_override",
        1.0,
        "gas_st_peak_hr_override",
        1.5,
    ),
    # (The CT_CHP row stood here on the ct_*_hr_override triple; deleted
    # 2026-08-03 with the fields themselves — rule 26 [R-DELETE], nyiso-114.
    # The triple was unreachable on every committed bundle in every ISO, so
    # this D-9 row could never have reported a non-neutral band.)
)
# The ERCOT-mirrored generic gas tranche shares (offer_curves.py:130-143)
# engaged by config.gas_offer_curve on non-CAMPD fleets.
D9_GENERIC_SHARE_GROUPS: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "ST_CHP",
    "CT_PEAKER",
    "CT_CHP",
)

# The P0-run-pattern commitment-bridge family: all four ride the shared
# detector (model.commitment.caiso_ra_mustoffer_min_gen) on the model's own
# P0 solution, so NO fleet_only rebuild can reproduce their floors — the G-06
# recompute subtracts their committed contributions before comparing
# (caiso-155 widened the exclusion from the RA leg to the family).
BRIDGE_MECHS: tuple[int, ...] = (
    MECH_RA_MUSTOFFER,
    MECH_GAS_COMMITMENT_BRIDGE,
    MECH_NYISO_GAS_COMMITMENT_BRIDGE,
    MECH_MISO_COAL_NIGHT_FLOOR,
    MECH_SPP_GAS_COMMITMENT_BRIDGE,
)

# D-6 holdout quarantine (CLAUDE.md rule 22, amended 2026-07-04; TIER-AWARE
# 2026-07-31): the in-sample calibration window. Any registered bundle carrying
# a solve year OUTSIDE this window is a holdout breach unless its ISO carries
# the marker for THAT YEAR'S TIER in frontend/data/backcast/calibration-complete
# .json — the 'complete' block for the iterable validation ladder, the 'final'
# block for the touch-once locked test. Tier membership and the block mapping
# live in scripts/lib/holdout_policy.py. Extend only when a new year is
# formally promoted from holdout to in-sample with a new designated holdout.


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    """One diagnostic's verdict: rows for the report plus failure strings.

    ``summary`` carries per-(year, class) aggregate rows where the detail
    ``rows`` are finer-grained (D-2's rows are class × mechanism; its summary
    is the per-class total forced share the rule-19 gate and the rubric's C8
    criterion consume).
    """

    name: str
    rows: list[dict] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    summary: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True when no gate failed."""
        return not self.failures


# ---------------------------------------------------------------------------
# D-1 — diurnal shape
# ---------------------------------------------------------------------------


def d1_shape_metrics(
    model_mw: np.ndarray, actual_mw: np.ndarray
) -> tuple[float, float, float]:
    """Return (profile r, model off-peak CV, actual off-peak CV) for a class.

    ``model_mw``/``actual_mw`` are aligned hourly class-total series
    (T = full 8760, or any multiple of 24 for the trivial-case tests). The
    profile is the hour-of-day mean; the CVs are taken over the profile's
    off-peak points h0-``D1_OFFPEAK_LAST_HOUR`` — the audit §1.1 statistic,
    where the caiso-42 flat floor scores model CV 0.000 vs actual 0.35-0.45
    (a per-sample pooled CV would hide the flat line behind the day gate's
    on/off day-to-day variance).
    """
    t = model_mw.size
    prof_m = model_mw.reshape(-1, 24).mean(axis=0)
    prof_a = actual_mw[:t].reshape(-1, 24).mean(axis=0)
    if prof_m.std() <= 0.0 or prof_a.std() <= 0.0:
        r = 0.0  # a constant profile carries no shape to correlate
    else:
        r = float(np.corrcoef(prof_m, prof_a)[0, 1])
    off = np.arange(24) <= D1_OFFPEAK_LAST_HOUR

    def _cv(x: np.ndarray) -> float:
        m = float(x.mean())
        return float(x.std() / m) if m > 1e-9 else 0.0

    return r, _cv(prof_m[off]), _cv(prof_a[off])


def run_d1(
    model_by_class: dict[str, np.ndarray],
    actual_by_class: dict[str, np.ndarray],
    year: int | str = "",
    gated_classes: tuple[str, ...] = D1_GATED_CLASSES,
) -> GateResult:
    """D-1 diurnal shape test over aligned per-class hourly series."""
    res = GateResult("D-1 diurnal shape")
    for klass in sorted(set(model_by_class) & set(actual_by_class)):
        model = np.asarray(model_by_class[klass], dtype=float)
        actual = np.asarray(actual_by_class[klass], dtype=float)
        if model.sum() <= 0.0 and actual.sum() <= 0.0:
            continue
        r, cv_m, cv_a = d1_shape_metrics(model, actual)
        ratio = cv_m / cv_a if cv_a > 1e-9 else float("nan")
        gated = klass in gated_classes
        fail_r = gated and r < D1_MIN_PROFILE_R
        fail_cv = gated and np.isfinite(ratio) and ratio < D1_MIN_CV_RATIO
        res.rows.append(
            {
                "year": year,
                "class": klass,
                "profile_r": round(r, 3),
                "model_offpeak_cv": round(cv_m, 3),
                "actual_offpeak_cv": round(cv_a, 3),
                "cv_ratio": round(ratio, 3) if np.isfinite(ratio) else None,
                "gated": gated,
                "verdict": "FAIL" if (fail_r or fail_cv) else "pass",
            }
        )
        if fail_r:
            res.failures.append(
                f"{year} {klass}: profile r {r:.3f} < {D1_MIN_PROFILE_R}"
            )
        if fail_cv:
            res.failures.append(
                f"{year} {klass}: off-peak CV ratio {ratio:.3f} "
                f"(model {cv_m:.3f} / actual {cv_a:.3f}) < {D1_MIN_CV_RATIO}"
            )
    return res


# ---------------------------------------------------------------------------
# D-2 — forced-energy attribution / D-4 — off-window binding
# ---------------------------------------------------------------------------


def at_floor_mask(
    dispatch: np.ndarray, min_gen: np.ndarray, npl: np.ndarray | None = None
) -> np.ndarray:
    """Boolean (n, T) mask of rows dispatched AT their binding min-gen floor.

    ``npl`` (per-row nameplate) widens the tolerance for payload-decoded
    dispatch, whose byte encoding quantizes to ~1 % of nameplate.
    """
    atol = np.full(dispatch.shape[0], D2_FLOOR_MIN_MW)
    if npl is not None:
        atol = atol + 0.01 * np.asarray(npl, dtype=float)
    return (min_gen > D2_FLOOR_MIN_MW) & (
        dispatch <= min_gen * (1.0 + D2_REL_TOL) + atol[:, None]
    )


def run_d2(
    dispatch: np.ndarray,
    min_gen: np.ndarray,
    mechanism: np.ndarray,
    klass: np.ndarray,
    year: int | str = "",
    npl: np.ndarray | None = None,
    ra_floor_missing: bool = False,
    total_load_mwh: float | None = None,
    actual_by_class: dict[str, float] | None = None,
    dispatch_substituted: np.ndarray | None = None,
    floor_klass: "FloorClassMatrix | None" = None,
) -> GateResult:
    """D-2 forced-energy attribution over aligned (n, T) row arrays.

    ``floor_klass`` (:class:`FloorClassMatrix`, the plant-hour floor class
    under maximum-composition) attributes each at-floor cell's forced energy
    to the class of the unit CARRYING the floor rather than to the row's
    plant-majority label — the unit-grain repair of the mixed-class
    mis-attribution (miso-170 K-1 forensic / miso-171 charter item (a)).
    Class DENOMINATORS stay on the row label (the dispatch grain): at-floor
    plant-hours have dispatch ≈ the floor, so the re-attributed numerator is
    the floored slice's own energy to within the at-floor tolerance. A floor
    class with no labeled rows reports its detail rows but has no denominator
    and is skipped by the summary (disclosed pathology — it would need a
    (plant, class) denominator split, which the payload dispatch grain cannot
    support). ``None`` = row labels attribute (the pre-repair rule; direct
    callers and legacy artifacts re-score exactly as before).

    Rows may be LP units or plants (floors aggregated per plant with the
    binding mechanism's id) — the arithmetic is identical. ``klass`` labels
    each row; forced energy is ``dispatch`` MWh in at-floor row-hours,
    attributed to the binding mechanism id.

    ``total_load_mwh`` (annual system load) activates the materiality guard:
    a merchant class whose energy is < ``PROTECTIVE_MIN_LOAD_FRAC`` of total
    load is immaterial — its forced share is reported but never a FAIL (owner
    directive 2026-07-06, rubric v2.1). ``None`` disables the guard (every
    class is gated, the pre-directive behaviour). The materiality numerator is
    ``max(model, actual)`` class energy: ``actual_by_class`` (annual MWh per
    class from the CAMPD benchmark) supplies the actual side so a binding floor
    cannot push a class under the line by its own forcing, and a model that
    zeroes a genuinely material class stays scored via the actual side — the
    exact ``max(model, actual)`` denominator ``calibration_verdict``'s C7/C8
    scorer (``_class_load_share`` / ``score_shape``) uses. ``None`` (or a class
    absent from it) falls back to the model side alone.

    ``dispatch_substituted`` (bool per row) marks rows whose dispatch IS their
    own floor because the active dispatch source carries no series for them
    (:func:`build_plant_matrices`, pjm-149 §3.2). Such a row contributes an
    UPPER bound to the numerator and a LOWER bound to the denominator, so every
    class holding one is stamped ``upper_bound: True`` on its summary row: the
    share is sound as a PASS, INDETERMINATE as a FAIL. ``None`` = none
    substituted (the parquet path, and every direct caller).
    """
    res = GateResult("D-2 forced-energy attribution")
    mask = at_floor_mask(dispatch, min_gen, npl)
    substituted = (
        np.zeros(dispatch.shape[0], dtype=bool)
        if dispatch_substituted is None
        else np.asarray(dispatch_substituted, dtype=bool)
    )
    row_classes = [str(k) for k in np.unique(klass)]
    total_by_class = {
        k: float(np.clip(dispatch[klass == k], 0.0, None).sum()) for k in row_classes
    }
    if floor_klass is None:
        classes = list(row_classes)
    else:
        # Floors may be carried by a class none of the rows is labeled with
        # (a minority slice of a mixed plant): those classes still get their
        # detail rows, so the attribution is complete.
        classes = sorted(set(row_classes) | set(floor_klass.present_under(mask)))
    mechs = [m for m in np.unique(mechanism[mask]) if m != 0]
    forced_gated: dict[str, float] = {k: 0.0 for k in classes}
    for k in classes:
        cells = (
            (klass == k)[:, None] & mask
            if floor_klass is None
            else floor_klass.eq(k) & mask
        )
        for m in mechs:
            sel = cells & (mechanism == m)
            mwh = float(dispatch[sel].sum())
            if mwh <= 0.0:
                continue
            total_k = total_by_class.get(str(k), 0.0)
            res.rows.append(
                {
                    "year": year,
                    "class": str(k),
                    "mechanism": MECH_NAMES.get(int(m), str(m)),
                    "forced_twh": round(mwh / 1e6, 4),
                    "class_total_twh": round(total_k / 1e6, 4),
                    "share_of_class": round(mwh / total_k, 4) if total_k > 0 else 0.0,
                }
            )
            if int(m) not in D2_EXEMPT_MECHS and int(m) not in NON_THERMAL_MECHS:
                forced_gated[k] += mwh
    for k in classes:
        # The empty ('') class is the unclassified bucket: plants carrying no
        # CAMPD plant_group — nuclear / hydro / renewable must-run whose floors
        # are non-thermal/exempt by construction. It is NOT a merchant class,
        # so it never gates a forced-share limit, and its per-plant dispatch is
        # only reconstructible from the full dispatch frame (the run payload
        # carries these as scalar non-fossil aggregates, not per plant) — a
        # nuclear-inclusive '' denominator therefore diverges by an order of
        # magnitude between the parquet and payload paths. Excluding it keeps
        # the summary path-independent and every merchant row per-class
        # truthful (#1488, rule 20).
        total_k = total_by_class.get(str(k), 0.0)
        if str(k) in D2_EXEMPT_CLASSES or str(k) == "" or total_k <= 0.0:
            continue
        share = forced_gated[k] / total_k
        limit = (
            D2_PEAKER_MAX_SHARE
            if str(k) in D2_PEAKER_CLASSES
            else D2_MERCHANT_MAX_SHARE
        )
        # Materiality denominator: max(model, actual) class energy — mirrors
        # calibration_verdict._class_load_share so the quarantine gate and the
        # C7/C8 rubric scorer draw the same line (a forcing floor inflates the
        # model side; the actual side keeps a zeroed-but-material class scored).
        actual_energy = (
            float((actual_by_class or {}).get(str(k), 0.0)) if actual_by_class else 0.0
        )
        material_energy = max(total_k, actual_energy)
        load_share = (
            material_energy / total_load_mwh
            if total_load_mwh and total_load_mwh > 0.0
            else None
        )
        immaterial = load_share is not None and load_share < PROTECTIVE_MIN_LOAD_FRAC
        breach = share > limit and not immaterial
        # pjm-149 §3.2: does this class hold a floor-substituted row? A breach
        # is NOT suppressed when it does — silently weakening rule 18 would be
        # worse than an over-strict flag, and the substitution can only inflate
        # the share — but the flag travels with the number so a breach on such
        # a class reads as INDETERMINATE and escalates rather than convicting.
        is_upper_bound = bool(substituted[klass == k].any())
        if floor_klass is not None and not is_upper_bound:
            # A substituted row whose floor is CHARGED to this class (a
            # mixed-plant minority slice) inflates its numerator the same way.
            contributing = substituted & (floor_klass.eq(k) & mask).any(axis=1)
            is_upper_bound = bool(contributing.any())
        res.summary.append(
            {
                "year": year,
                "class": str(k),
                "forced_twh": round(forced_gated[k] / 1e6, 4),
                "class_total_twh": round(total_k / 1e6, 4),
                "forced_share": round(share, 4),
                "limit": limit,
                "load_share": round(load_share, 4) if load_share is not None else None,
                "immaterial": bool(immaterial),
                "lower_bound": bool(ra_floor_missing),
                # pjm-149 §3.2: the class holds >= 1 plant whose dispatch was
                # substituted by its own floor, so this share is an upper bound
                # — a pass is sound, a breach is indeterminate.
                "upper_bound": is_upper_bound,
                "verdict": "FAIL" if breach else "pass",
            }
        )
        if breach:
            res.failures.append(
                f"{year} {k}: forced share {share:.1%} > {limit:.0%} "
                f"({forced_gated[k] / 1e6:.2f} of {total_k / 1e6:.2f} TWh "
                "at binding non-exempt floors)"
                + (
                    " [UPPER BOUND — the class holds a floor-substituted plant "
                    "(pjm-149 §3.2); indeterminate, escalate rather than convict]"
                    if is_upper_bound
                    else ""
                )
            )
    if ra_floor_missing:
        res.notes.append(
            f"{year}: floors reconstructed via run_year(fleet_only=True) — the "
            "P2 RA must-offer bridge floor (needs the P1 solution) is NOT "
            "included, so CC/CT forced shares are lower bounds."
        )
    return res


def run_d4(
    dispatch: np.ndarray,
    min_gen: np.ndarray,
    mechanism: np.ndarray,
    klass: np.ndarray,
    year: int | str = "",
    npl: np.ndarray | None = None,
    windows: dict[tuple[int, str | None], tuple[int, int]] | None = None,
    pids: list[str] | None = None,
    bench_pl: dict[str, dict] | None = None,
    substituted: np.ndarray | None = None,
    floor_klass: "FloorClassMatrix | None" = None,
) -> GateResult:
    """D-4 off-window binding: floored MWh outside each declared window.

    ``floor_klass`` (:class:`FloorClassMatrix`) selects each window's
    (mechanism × class) cells by the class of the unit CARRYING the floor
    rather than by the row's plant-majority label — the unit-grain repair of
    the mixed-class mis-attribution (miso-170 K-1 forensic: plant 1104's
    CT_PEAKER netload floor was tested, and convicted, under the ST_GAS
    conduct row). ``None`` = row labels select (the pre-repair rule).

    Two checks share the gate, discriminated by each row's ``check`` field:

    ``window``
        the original off-window energy share, one row per declared
        (mechanism, class) window.
    ``unit-conduct``
        the PER-UNIT CONDUCT RIDER (owner decision 2026-08-16, nyiso-140 §5),
        emitted only for windows spanning all 24 hours, where the off-window
        test is vacuous by construction. A floored plant whose OWN measured
        median hourly output over the window is exactly zero fails provenance
        for its mechanism regardless of the class aggregate. Requires ``pids``
        (row keys, aligned to ``dispatch``) and ``bench_pl`` (the plant-level
        measured view); without them the rider is skipped and says so.

    Conduct rows carry the mechanism's own ``floor`` label so
    ``calibration_verdict._d4_provenance`` — which matches on that label —
    picks them up with no change to its matching rule.
    """
    res = GateResult("D-4 off-window binding")
    windows = D4_WINDOWS if windows is None else windows
    mask = at_floor_mask(dispatch, min_gen, npl)
    t = dispatch.shape[1]
    hod = np.arange(t) % 24
    conduct_ok = pids is not None and bench_pl is not None
    subbed = (
        np.zeros(dispatch.shape[0], dtype=bool)
        if substituted is None
        else np.asarray(substituted, dtype=bool)
    )
    unmetered: set[str] = set()
    skipped_substituted: set[str] = set()
    ct_only_skipped: set[str] = set()
    for (mech_id, k_filter), (start, end) in windows.items():
        in_window = (hod >= start) & (hod < end)
        if k_filter is None:
            class_cells = np.ones(dispatch.shape, dtype=bool)
        elif floor_klass is not None:
            class_cells = floor_klass.eq(k_filter)
        else:
            class_cells = (klass == k_filter)[:, None] & np.ones((1, t), dtype=bool)
        sel = mask & (mechanism == mech_id) & class_cells
        total = float(dispatch[sel].sum())
        if total <= 0.0:
            continue
        off = sel & ~in_window[None, :]
        off_mwh = float(dispatch[off].sum())
        share = off_mwh / total
        label = f"{MECH_NAMES.get(mech_id, mech_id)}" + (
            f" × {k_filter}" if k_filter else ""
        )
        res.rows.append(
            {
                "year": year,
                "check": "window",
                "floor": label,
                "window": f"h{start}-{end - 1}",
                "plant": "",
                "floored_twh": round(total / 1e6, 4),
                "offwindow_twh": round(off_mwh / 1e6, 4),
                "offwindow_share": round(share, 4),
                "binding_hours": "",
                "measured_median_mw": "",
                "measured_zero_share": "",
                "verdict": "FAIL" if share > D4_MAX_OFFWINDOW_SHARE else "pass",
            }
        )
        if share > D4_MAX_OFFWINDOW_SHARE:
            res.failures.append(
                f"{year} {label}: {share:.1%} of floored MWh outside its "
                f"justified window h{start}-{end - 1} (> "
                f"{D4_MAX_OFFWINDOW_SHARE:.0%})"
            )
        # --- per-unit conduct rider ------------------------------------
        # Only where the off-window test is vacuous (all-hours window).
        if not conduct_ok or (end - start) < 24 or not D4_CONDUCT_ALLHOURS_ONLY:
            continue
        for global_i in np.flatnonzero(sel.any(axis=1)):
            floored_mwh = float(dispatch[global_i][sel[global_i]].sum())
            if floored_mwh <= 0.0 or float(min_gen[global_i].max()) <= D2_FLOOR_MIN_MW:
                continue
            pid = str(pids[global_i])
            if subbed[global_i]:
                skipped_substituted.add(pid)
                continue
            b = bench_pl.get(pid)
            if b is None:
                unmetered.add(pid)
                continue
            if b.get("ct_only"):
                # The benchmark's own CT-only CEMS flag: EIA-923 net exceeds
                # CAMPD gross by >10 %, so this plant's CAMPD HOURLY series is
                # incomplete and the benchmark scores it on EIA-923 MONTHLY.
                # A median of zero in a series the benchmark already declines
                # to trust is a metering artifact, not conduct — the rider
                # must not convict on it (rule 14 [R-ACCURATE]).
                ct_only_skipped.add(pid)
                continue
            meas = np.asarray(b["mw"], dtype=float)[:t]
            if meas.size < t:
                unmetered.add(pid)
                continue
            # MEASURE OVER THE PLANT'S OWN BINDING HOURS, not the whole
            # declared window. The adopted wording is "a floored unit whose
            # own measured CF is ~0 across the declared window" (nyiso-140
            # §5), and for the limb that motivated it — the Long_Island
            # always-on base, which binds in all 8,760 h — the two are the
            # same set. They are NOT the same for a limb that lives inside an
            # all-hours DECLARED window but is gated by its own driver, e.g.
            # NYISO's Capital_Hudson x ST_GAS tmax limb (threshold 31.1 degC,
            # no start/end hour): a unit that runs only on design-cooling days
            # has an annual median of 0 and would fail a window-wide test even
            # though its conduct in the hours the floor actually forces it is
            # exactly what the driver predicts. Scoring the binding hours is
            # both the faithful reading of "the hours the floor asserts it
            # must be online" and the only one that cannot manufacture a
            # false positive out of a driver-gated limb.
            bind_h = sel[global_i] & in_window
            if not bind_h.any():
                continue
            win = meas[bind_h[: meas.size]]
            if win.size == 0:
                continue
            med = float(np.median(win))
            zero_share = float((win <= 0.0).mean())
            fail = med <= 0.0
            res.rows.append(
                {
                    "year": year,
                    "check": "unit-conduct",
                    "floor": label,
                    "window": f"h{start}-{end - 1}",
                    "plant": pid,
                    "floored_twh": round(floored_mwh / 1e6, 4),
                    "offwindow_twh": "",
                    "offwindow_share": round(floored_mwh / total, 4),
                    "binding_hours": int(bind_h.sum()),
                    "measured_median_mw": round(med, 3),
                    "measured_zero_share": round(zero_share, 4),
                    "verdict": "FAIL" if fail else "pass",
                }
            )
            if fail:
                res.failures.append(
                    f"{year} {label}: plant {pid} is floored for "
                    f"{floored_mwh / 1e6:.4f} TWh ({floored_mwh / total:.1%} of "
                    f"the mechanism's forced energy) while its own measured "
                    f"median output over the {int(bind_h.sum())} hours the "
                    f"floor actually binds for it (inside h{start}-{end - 1}) "
                    f"is 0.000 MW ({zero_share:.1%} of them at zero) — the meter "
                    f"says it is offline in at least half the hours the floor "
                    f"asserts it must be online (per-unit conduct rider)"
                )
    if conduct_ok and ct_only_skipped:
        res.notes.append(
            f"{year}: per-unit conduct rider skipped {len(ct_only_skipped)} "
            "floored plant(s) carrying the benchmark's CT-only CEMS flag "
            "(EIA-923 net > 1.1x CAMPD gross ⇒ scored on EIA-923 MONTHLY, "
            "hourly CAMPD incomplete) — a zero median in a series the "
            "benchmark itself declines to trust is a metering artifact, not "
            "conduct: "
            + ", ".join(sorted(ct_only_skipped)[:20])
            + (" …" if len(ct_only_skipped) > 20 else "")
        )
    if conduct_ok and skipped_substituted:
        res.notes.append(
            f"{year}: per-unit conduct rider skipped "
            f"{len(skipped_substituted)} floored row(s) whose dispatch is "
            "SUBSTITUTED by their own floor (no series in the active source) "
            "— their at-floor set is the whole floor-positive set by "
            "construction, so a conduct verdict on them would be an artifact: "
            + ", ".join(sorted(skipped_substituted)[:20])
            + (" …" if len(skipped_substituted) > 20 else "")
        )
    if conduct_ok and unmetered:
        res.notes.append(
            f"{year}: per-unit conduct rider skipped {len(unmetered)} floored "
            "row(s) with no measured series (hydro / nuclear / renewables / "
            "interchange pseudo-units) — the rider is a measured-conduct test "
            "and never fails a mechanism for a missing meter: "
            + ", ".join(sorted(unmetered)[:20])
            + (" …" if len(unmetered) > 20 else "")
        )
    elif not conduct_ok:
        res.notes.append(
            f"{year}: per-unit conduct rider NOT RUN (caller supplied no "
            "pids/bench view) — every all-hours window row below is an "
            "off-window test that cannot fail by construction"
        )
    return res


# ---------------------------------------------------------------------------
# D-5 — forecast/backcast parity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechanismSpec:
    """One row of the D-5 parity registry.

    ``mode``: "backcast_only" / "forecast_only" / "both" — the *intended*
    availability by ScenarioConfig.mode. ``backcast_symbols`` /
    ``forecast_symbols``: builder symbols whose presence in the mode's entry
    script proves the mechanism is actually wired there (empty tuple = wired
    via shared modules, no entry-point call needed). ``declared``: on the
    declared backcast-overlay list (docs/backcast-measured-data-audit-2026-06
    .md), so a backcast/forecast difference is sanctioned.

    ``iso``: restrict the row to one ISO. Only needed for a row with no
    config toggle (``toggle=None``) — an always-on ISO-exclusive overlay would
    otherwise report itself as active in every other ISO's bundle. Rows gated
    by a per-ISO flag are already scoped by the toggle and leave this ``None``.
    """

    name: str
    toggle: str | None  # scenario_config/calibration_flags key; None = always on
    mode: str
    declared: bool
    backcast_symbols: tuple[str, ...] = ()
    forecast_symbols: tuple[str, ...] = ()
    note: str = ""
    iso: str | None = None  # None = applies to every ISO


# Declared backcast-overlay list, built from
# docs/backcast-measured-data-audit-2026-06.md (admissible measured-input
# overlays + the demoted default-off probes, which are declared *as probes* —
# D-9 separately enforces that they stay off in keepers).
D5_REGISTRY: tuple[MechanismSpec, ...] = (
    MechanismSpec(
        "historic_outage_overlay",
        "outage_source",
        "backcast_only",
        True,
        note="CAMPD outage windows (physical availability events)",
    ),
    MechanismSpec(
        "unit_outage_maxgen_events",
        "unit_outage_maxgen_events",
        "backcast_only",
        True,
        note="declared capacity-emergency event-window revealed derates "
        "(M-2): CAMPD per-unit derates inside the maxgen-events registry's "
        "declared windows only, under the frozen guards of "
        "scripts/data/derive_campd_maxgen_outages.py ($150 DA in-merit "
        "certificate, ±45d capability basis, best-event-hour credit, "
        "disjointness vs std/short) — same CAMPD outage-window "
        "admissibility family as the parent overlay; the D-4 window "
        "declaration for this channel is the registry window set itself "
        "(see the D4_WINDOWS availability-overlay note)",
    ),
    MechanismSpec(
        "maxgen_emergency_tier_pricing",
        "maxgen_emergency_tier_pricing",
        "backcast_only",
        True,
        backcast_symbols=("emergency_tier_slack_cost",),
        note="declared-window ELMP emergency-tier pricing (F5): load-slack "
        "repriced to min(voll, SOM-footnoted tier offer floor — $500 Tier 1 "
        "Warning/Step 1, $1,000 Tier 2 Step 2+) inside the maxgen-events "
        "registry's declared Warning+ windows only; the RBDC/zonal-ORDC "
        "curves are never edited (rule 19) and the cost never rises (min). "
        "Same declared-instrument admissibility family as the maxgen "
        "derates; the D-4 window declaration is the registry Warning+ "
        "window set itself (see the D4_WINDOWS availability-overlay note); "
        "frozen design docs/handoffs/miso-f5-scarcity-depth-design-"
        "2026-07.md",
    ),
    MechanismSpec(
        "eia860_vintage_snapshot",
        None,
        "backcast_only",
        True,
        note="historical fleet vintage pin (runner.py:239 mode gate)",
    ),
    MechanismSpec(
        "retired_within_window_fleet",
        None,
        "backcast_only",
        True,
        note="within-window plant exits injected into the base fleet",
    ),
    MechanismSpec(
        "planned_additions_pipeline",
        None,
        "forecast_only",
        True,
        note="EIA-860 construction-committed pipeline — the declared "
        "forecast complement of the backcast fleet boundary",
    ),
    MechanismSpec(
        "renewable_cf_measured",
        None,
        "backcast_only",
        True,
        note="delivered EIA-930/HSL renewable CF upper bound (leakage L1)",
    ),
    MechanismSpec(
        "nuclear_flat_mustrun",
        None,
        "backcast_only",
        True,
        note="measured monthly nuclear CF + flat must-run floor (L3)",
    ),
    MechanismSpec(
        "ordc_floor_active_mask",
        None,
        "backcast_only",
        True,
        note="ERCOT scarcity-floor measured active-hours mask",
    ),
    MechanismSpec(
        "hydro_eia930_monthly",
        "hydro_eia930_monthly",
        "backcast_only",
        True,
        note="EIA-930 monthly hydro budgets (L6)",
    ),
    MechanismSpec(
        "hydro_min_flow_floor",
        "hydro_min_flow_floor",
        "both",
        True,
        note="conventional-hydro minimum-flow floor (caiso-124): the LOWER "
        "half of the measured two-sided hydro capability envelope whose "
        "upper half is hydro_dispatch_envelope. Mode PARITY by "
        "construction — data.eia_loader.measured_hydro_min_flow_level "
        "reads the solve year's own EIA-930 NG:WAT in a backcast and falls "
        "back to the pooled HYDRO_CLIMATOLOGY_YEARS per-month percentile "
        "for any year the extract does not cover, so a forecast year gets "
        "the same mechanism off a normal-water-year level (the "
        "measured_hydro_hourly_envelope pattern). Adds no free parameter: "
        "HYDRO_MIN_FLOW_PERCENTILE is the mirror of the ceiling's",
    ),
    MechanismSpec(
        "hydro_ror_split",
        "hydro_ror_split",
        "both",
        True,
        note="conventional-hydro run-of-river split (caiso-126): plants the "
        "external hydro-plant-modes classifier (ORNL EHA FY2024 Mode + the "
        "documented HILARRI/Corps-dam completion, "
        "data/clean/hydro-plant-modes) marks non-shapeable dispatch flat at "
        "their own monthly water budget[g,m]/hours[m]; reservoir-class "
        "plants keep the envelope/budget machinery. Mode PARITY by "
        "construction — the classification is a static plant attribute and "
        "the level is the plant's own budget, which both backcast and "
        "forecast paths already supply. Zero free parameters (categorical "
        "classifier, no threshold). Rule 19: one reconciled family with "
        "hydro_min_flow_floor (the RoR base subsumes its share of the Q95 "
        "evidence; the reservoir class carries the remainder)",
    ),
    MechanismSpec(
        "gas_monthly_actuals",
        "gas_monthly_actuals",
        "backcast_only",
        True,
        note="F923 delivered monthly gas (admissible fuel input)",
    ),
    MechanismSpec(
        "gas_hub_basis_overlay",
        "gas_hub_basis_overlay",
        "backcast_only",
        True,
        note="measured monthly hub-spot basis overlay",
    ),
    MechanismSpec(
        "coal_plant_monthly_pricing",
        "coal_plant_monthly_pricing",
        "backcast_only",
        True,
        note="F923 per-plant delivered coal cost",
    ),
    MechanismSpec(
        "storage_as_commitment",
        "storage_as_commitment",
        "backcast_only",
        True,
        note="measured storage up-AS power reservation",
    ),
    MechanismSpec(
        "chp_export_floor_measured",
        "chp_export_floor_measured",
        "backcast_only",
        True,
        note="CHP export floor at measured class CF (mode-gated, L4)",
    ),
    MechanismSpec(
        "ct_mustrun_per_plant",
        "ct_mustrun_per_plant",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "ct_deployment_overlay",
        "ct_deployment_overlay",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "reliability_deployment_overlay",
        "reliability_deployment_overlay",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "caiso_gas_commitment_floor",
        "caiso_gas_commitment_floor",
        "backcast_only",
        True,
        backcast_symbols=("inject_caiso_gas_commitment_floor",),
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "reliability_floor",
        "reliability_floor",
        "both",
        True,
        backcast_symbols=("inject_reliability_floor",),
        forecast_symbols=("inject_reliability_floor",),
        note="declared admissible overlay (2026-06 audit); a wiring gap in "
        "the forecast entry is reported but sanctioned by the declaration",
    ),
    MechanismSpec(
        "gas_st_netload_drag",
        "gas_st_netload_drag",
        "both",
        False,
        backcast_symbols=("apply_gas_st_netload_drag_floor",),
        forecast_symbols=("apply_gas_st_netload_drag_floor",),
        note="forward-native drag — must be wired in BOTH modes",
    ),
    MechanismSpec(
        "ct_netload_drag",
        "ct_netload_drag",
        "both",
        False,
        backcast_symbols=("apply_ct_netload_drag_floor",),
        forecast_symbols=("apply_ct_netload_drag_floor",),
        note="forward-native drag — must be wired in BOTH modes",
    ),
    MechanismSpec(
        "caiso_ra_mustoffer",
        "caiso_ra_mustoffer",
        "both",
        True,
        backcast_symbols=("caiso_ra_mustoffer_min_gen",),
        forecast_symbols=("caiso_ra_mustoffer_min_gen",),
        note="RA must-offer is market design (mode-independent) and rule-13 "
        "admissible in BOTH modes — the bridge is detected from the model's "
        "own base-cost P0 run pattern against the physical CC_COMMITMENT_PARAMS "
        "min-down time, so no measured outcome enters. The parity difference "
        "is the known w2-caiso-ra-p2 WIRING GAP: caiso_ra_mustoffer_min_gen is "
        "called from scripts/run_calibration.py and never from runner.py, so "
        "the mechanism is backcast-only in practice though not by intent. "
        "DECLARED 2026-09-20 (caiso-294) in "
        "docs/backcast-measured-data-audit-2026-06.md — same posture as the "
        "reliability_floor row above: the gap is reported and sanctioned by "
        "the declaration, NOT claimed harmless. Closing it is a forecast-path "
        "model change (docs/audit-wiring-iso-gaps/prompt-pack/w2-caiso-ra-p2.md) "
        "needing its own PRECOMMIT and an owner ruling; it is deliberately not "
        "bundled into the declaration",
    ),
    MechanismSpec(
        "nyiso_synchronised_reserve",
        "nyiso_synchronised_reserve",
        "both",
        False,
        backcast_symbols=("reserve_adequacy_commit",),
        forecast_symbols=("reserve_adequacy_commit",),
        note="market-design reserve commitment — mode-independent by intent",
    ),
    MechanismSpec(
        "nyiso_local_selfsupply",
        "nyiso_local_selfsupply",
        "both",
        False,
        backcast_symbols=("inject_nyiso_local_selfsupply",),
        forecast_symbols=("inject_nyiso_local_selfsupply",),
        note="LMIC market-design rule — mode-independent by intent",
    ),
    MechanismSpec(
        "nyiso_central_east_measured_ttc",
        None,
        "backcast_only",
        True,
        iso="NYISO",
        backcast_symbols=("apply_iso_year_ttc", "apply_iso_monthly_ttc"),
        note="measured Central-East DAM transfer capability (nyiso-104): the "
        "month-mean of NYISO's posted MIS ATC_TTC 'TTC (DAM)' series for the "
        "CENT EAST interface, applied to Upstate_West->Capital_Hudson as a "
        "per-hour envelope (NYISO_INTERFACE_TTC_BY_MONTH) over the annual mean "
        "(_BY_YEAR). Classified an OVERLAY, not a mechanism, on the source "
        "data's own forward reproducibility: across the two years that share "
        "the post-AC-Transmission topology (2024/2025) the level-normalized "
        "monthly shape correlates at only r=+0.21 (Spearman +0.16, dihedral-"
        "null p=0.25) and the deepest-derate month MOVES Sep->Apr, so the "
        "series is that year's realized transmission-outage schedule, not a "
        "seasonal rating that regenerates forward. Same admissibility family "
        "as historic_outage_overlay — a physical availability event, on the "
        "network instead of on a unit. Deliberately NOT wired forward: the "
        "LEVEL already has its forward channel (the transmission-expansion "
        "registry + the static 2,850 MW, itself the measured post-upgrade DAM "
        "mean), and pushing these numbers into a forecast would import one "
        "historical year's outage schedule into every forward year",
    ),
    MechanismSpec(
        "cc_mustrun_per_plant",
        "cc_mustrun_per_plant",
        "both",
        False,
        note="per-plant gas local-reliability commitment floor — "
        "parameter-based (CEMS committed share + online_frac, "
        "thermal_tranches artifact), applied inside the shared fleet "
        "builder (fleet.bins_to_fleet / generators_to_fleet_arrays) so "
        "both mode entries reach it; no entry-script symbol to measure",
    ),
    MechanismSpec(
        "ercot_wtx_curtailment_driver",
        "ercot_wtx_curtailment_driver",
        "both",
        False,
        backcast_symbols=("wtx_curtail_multipliers",),
        forecast_symbols=("forecast_wtx_curtail_multipliers",),
        note="WP-B West-corridor curtailment ceiling — net-load-indexed "
        "structural mechanism, mode-independent by intent (backcast rides "
        "the measured-HSL potential, forecast the reference-rate gross-up)",
    ),
    # --- ercot-219 Option-B stage attributions (B-1; PRECOMMIT-ercot219) ---
    MechanismSpec(
        "ercot_capability_reconciliation",
        "ercot_capability_reconciliation",
        "backcast_only",
        True,
        note="stage-1 measured NP6-905 aggregate-capability reconciliation "
        "(B-1 SIGNED by dispatch of ERCOT-219 2026-08-18): single hourly "
        "tighten-only scalar on merchant-thermal availability to the "
        "published rtolhsl aggregate net of measured wind/solar HSL + "
        "storage capability, CHP boundary excluded both sides. DRIVER: the "
        "published real-time telemetered capability state. WINDOW: all "
        "telemetered hours (a standing measured physical state, not an "
        "event window); inert on NaN hours (2025 post-RTC+B tail). Rule-19 "
        "owner of the aggregate RT online LEVEL only — the DAM availability "
        "family keeps class/plant-grain declared availability.",
        iso="ERCOT",
    ),
    MechanismSpec(
        "ercot_exhaustion_expectation",
        "ercot_exhaustion_expectation",
        "backcast_only",
        True,
        note="stage-2 within-day exhaustion expectation: P_exhaust(t) = "
        "max over [t..end-of-day] of the registered LOLP curve at the "
        "model's own post-reconciliation margin (capability − load − armed "
        "*_withheld AS requirement rows). Zero new scalars; the ordc_lolp_* "
        "constants enter as an EXPECTATION input (ercot-206 B0 untouched — "
        "no price channel changes). Forward-computable by construction "
        "(regenerates from model state; collapses post-reform/RTC+B); wired "
        "in the backcast driver only today, hence declared backcast-only. "
        "Audit trail: hourly/exhaustion_<year>.parquet.",
        iso="ERCOT",
    ),
    MechanismSpec(
        "ercot_storage_reservation_offer",
        "ercot_storage_reservation_offer",
        "backcast_only",
        True,
        backcast_symbols=("p1_storage_discharge_cost",),
        note="stage-3 storage reservation-price offer, P1-ONLY at the "
        "pipeline.solve P0→P1 seam: discharge offer = max(vom_base, "
        "P_exhaust × ordc_voll), raise-only (self-extinguishing as "
        "P_exhaust → 0). DRIVER: the sequestration-induced within-day "
        "exhaustion expectation (stage 2). WINDOW: the within-day "
        "exhaustion window its own driver defines — binds only where "
        "P_exhaust × VOLL exceeds the keeper's own offer; ordinary hours "
        "keep the keeper's storage dispatch. Energy-only (card §7.4).",
        iso="ERCOT",
    ),
    # --- ercot-221 adaptive-expectation storage offer (owner card by dispatch;
    # PRECOMMIT-ercot221 + Amendments 1-3) ---
    MechanismSpec(
        "ercot_storage_adaptive_expectation",
        "ercot_storage_adaptive_expectation",
        "backcast_only",
        True,
        backcast_symbols=("ercot221_adaptive",),
        note="adaptive-expectation storage scarcity offer, P1-only two-pass: "
        "batteries price scarce SOC at their experienced recent deep-scarcity "
        "frequency. DRIVER: the model's OWN pass-1 realized spike experience "
        "(daily demand-weighted P1 lambda >= $1,000 — pure model, zero "
        "measured content in the armed path, precommit Amendment 3), trailing "
        "EWMA half-life 30 d x beta 3.0077 (the two rule-23 constants, "
        "identified Phase-0 v2 on the measured 2023 daily evening storage "
        "offer surface and FROZEN). WINDOW: evening net-peak hours h17-20 "
        "CST, on days the model's own trailing state is active — a spike-free "
        "year collapses the floor to vom (self-extinguishing). FORWARD STORY: "
        "regenerates from the model's own price path in any year (wired in "
        "the backcast driver only today, hence declared backcast-only). "
        "Rule-19: exclusive with ercot_storage_reservation_offer on the "
        "p1_storage_discharge_cost seam; ordinary-hour cycling untouched by "
        "the window scoping. Audit trail: hourly/adaptive_<year>.parquet.",
        iso="ERCOT",
    ),
    # --- ercot-226 held-location carve (owner program by dispatch;
    # PRECOMMIT-ercot226-held-sequestration-2026-08-22 §2 F2, waiver W-3
    # (ercot-226)). D-4 NOTE — carries NO row BY CONSTRUCTION: a reserve-
    # requirement/allocation mechanism never touches min_gen, so it can never
    # bind a dispatch floor on- or off-window; its window set is the rigid-
    # family date gates (spec._ercot_rigid_end) ∩ the measured file's
    # published coverage, and off-coverage hours are byte-identical to
    # flag-off (held = 0 ⇒ no class families built). Its engagement is
    # observable in hourly/reserve_family_<year>.parquet (the *_held family
    # rows) and gated by ercot226_gates.py G-SHORTFALL (arm shortfall
    # hour-set ⊆ control's, precommit Amendment 1). ---
    # --- ercot-227 F1/F1b held-depth (Amendment 3; D-4: NO row BY
    # CONSTRUCTION — a requirement max never touches min_gen; window =
    # rigid gates (F1) / published coverage (F1b); off-coverage byte-
    # identical: held = 0 ⇒ max(plan, 0) = plan). ---
    MechanismSpec(
        "ercot_ruc_commitment_floor",
        "ercot_ruc_commitment_floor",
        "backcast_only",
        True,
        note="measured RUC INSTRUCTION-STATE commitment floor (ercot-227 F3, "
        "Amendment 3 / waiver W-3): per class-hour ONRUC LSL sums "
        "(NP3-965, derive_ercot_ruc_committed.py) pro-rata over class "
        "available capacity, clipped at class capability. DRIVER: the "
        "operator's RUC instruction (outage-window-class input, rule 13 — "
        "never realized output; the D-9 deployment overlays pin measured "
        "ENERGY and ct_mustrun_per_plant pinned annual outcome commitment; "
        "this is hourly instruction state at physical LSL). WINDOW: the "
        "measured instruction set, zero floor off it by construction "
        "(D4_WINDOWS by-construction entry). Rule-19: max-composition after "
        "the gas bridge / ST_GAS drag incumbents, per-mechanism D-2 "
        "attribution (MECH_ERCOT_RUC_COMMITMENT).",
        iso="ERCOT",
    ),
    MechanismSpec(
        "ercot_as_held_requirement",
        "ercot_as_held_requirement",
        "backcast_only",
        True,
        note="held-DEPTH max(plan, telemetered held) on the rigid RegUp/RRS/"
        "ECRS requirements inside their rigid windows (NP3-965 system "
        "responsibilities, derive_ercot_as_responsibility.py — a measured "
        "power reservation, rule 13's admissible example). Measured prior: "
        "held < plan everywhere on the Gen-ONLINE basis, so the armed arm "
        "is the inertness MEASUREMENT (PRECOMMIT-ercot226 Amendment 3).",
        iso="ERCOT",
    ),
    MechanismSpec(
        "ercot_as_held_requirement_nspin",
        "ercot_as_held_requirement_nspin",
        "backcast_only",
        True,
        note="the F1b NSPIN leg of the held-depth max — same series (nsrs "
        "column), full published coverage, ramp-released family (NSPIN is "
        "not rigid). Same zeros-fallback and inertness prior as F1.",
        iso="ERCOT",
    ),
    MechanismSpec(
        "ercot_as_held_location",
        "ercot_as_held_location",
        "backcast_only",
        True,
        note="measured held-LOCATION of the rigid-product AS (NP3-965 60-Day "
        "SCED telemetered per-class responsibilities, "
        "derive_ercot_as_responsibility.py): per thermal class a new reserve "
        "class + class-scoped headroom row + rigid VOLL-step family requiring "
        "the class's measured held MW (clipped at the class's own "
        "pmax×availability), with a CONSERVING credit on the product "
        "requirements — location only, total held quantity unchanged "
        "(rule 19). DRIVER: the published HASL carve (Nodal §6.5.7.6.2.3/"
        "§3.17) — WHERE the sequestered MW physically sat. WINDOW: the rigid "
        "no-release design windows ∩ published disclosure coverage "
        "(delivery-2023 in the tracked corpus; uncovered years byte-identical "
        "to flag-off). FORWARD STORY: a forecast year carries no disclosure "
        "and uses the endogenous allocation, exactly like "
        "outage_source='historic'. Class grain (the committed RESTYPE map) — "
        "per-unit grain is Q-B-closed (item 11); distinct from the "
        "R-adjudicated capability-level objects (no capability level enters; "
        "class capacity is only a clip).",
        iso="ERCOT",
    ),
    # --- caiso-205 adaptive-expectation storage offer, CAISO leg (owner order
    # caiso-205 branch 1 over the caiso-204 recorded Phase-0 G-BOOT FAIL) ---
    MechanismSpec(
        "caiso_storage_adaptive_expectation",
        "caiso_storage_adaptive_expectation",
        "backcast_only",
        True,
        backcast_symbols=("caiso205_adaptive",),
        note="adaptive-expectation storage scarcity offer, CAISO leg, P1-only "
        "two-pass: batteries price scarce SOC at their experienced recent "
        "spike frequency. DRIVER: the model's OWN pass-1 daily demand-"
        "weighted P1 lambda >= $200 (CAISO's frozen scarcity-tail threshold; "
        "pure model, zero measured content in the armed path — CAISO's "
        "scored backcast price IS the energy-only dual, caiso-137b), "
        "trailing EWMA half-life 30 d x beta 0.5945 (the two rule-23 "
        "constants, identified caiso-204 Phase-0 on the measured 2023-2025 "
        "daily evening storage offer surface, PUB_BID_DAM subset, daily corr "
        "0.704, and FROZEN). WINDOW: evening net-load-peak hours h18-21 PT, "
        "on days the model's own trailing state is active — a spike-free "
        "year collapses the floor to vom (self-extinguishing; the caiso-204 "
        "G-BOOT wall predicts exactly this on the caiso-200 keeper path). "
        "FORWARD STORY: regenerates from the model's own price path in any "
        "year (wired in the backcast driver only today, hence backcast-"
        "only). Rule-25: CAISO's own identified constants, never ERCOT's "
        "(beta 0.5945 vs 3.0077). Battery-only (caiso-204 S4 excluded "
        "pumped storage from the conduct population). Audit trail: "
        "hourly/adaptive_<year>.parquet.",
        iso="CAISO",
    ),
)


def _toggle_on(spec: MechanismSpec, cfg: dict) -> bool:
    """Return whether the spec's config toggle is on in a run_config dict."""
    if spec.toggle is None:
        return True
    val = cfg.get(spec.toggle)
    if spec.toggle == "outage_source":
        return val == "historic"
    return bool(val)


def run_d5(
    cfg: dict,
    iso: str,
    backcast_entry_src: str,
    forecast_entry_src: str,
) -> GateResult:
    """D-5 parity: diff the active mechanism sets, backcast vs forecast.

    ``cfg`` is the bundle's merged run-config (calibration_flags +
    scenario_config); the two ``*_src`` strings are the full text of the
    mode entry scripts (``scripts/run_calibration.py`` for backcast,
    ``src/market_sim/runner.py`` for forecast) so wiring is *measured*, not
    asserted — when the w2 gap is closed the diagnostic sees it.
    """
    res = GateResult("D-5 forecast/backcast parity")
    for spec in D5_REGISTRY:
        if spec.iso is not None and spec.iso != iso:
            continue
        if not _toggle_on(spec, cfg):
            continue
        wired_b = all(s in backcast_entry_src for s in spec.backcast_symbols)
        wired_f = all(s in forecast_entry_src for s in spec.forecast_symbols)
        active_b = spec.mode != "forecast_only" and wired_b
        active_f = spec.mode != "backcast_only" and wired_f
        if active_b == active_f:
            continue
        side = "backcast-only" if active_b else "forecast-only"
        res.rows.append(
            {
                "mechanism": spec.name,
                "difference": side,
                "declared_overlay": spec.declared,
                "note": spec.note,
                "verdict": "declared" if spec.declared else "FAIL",
            }
        )
        if not spec.declared:
            res.failures.append(
                f"{spec.name}: active {side} for this config but NOT on the "
                "declared backcast-overlay list "
                "(docs/backcast-measured-data-audit-2026-06.md)"
            )
    return res


# ---------------------------------------------------------------------------
# D-9 — overlay quarantine
# ---------------------------------------------------------------------------


def run_d9(run_config: dict, iso: str, label: str = "") -> GateResult:
    """D-9 quarantine for one bundle's run_config.json (see module docstring)."""
    res = GateResult("D-9 overlay quarantine")
    sc = run_config.get("scenario_config", {})
    flags = run_config.get("calibration_flags", {})
    prefix = f"{label}: " if label else ""
    for key, required in D9_FORBIDDEN_FLAGS.items():
        val = sc.get(key, flags.get(key))
        ok = (not bool(val)) if required is False else (not val or float(val) == 0.0)
        res.rows.append(
            {
                "bundle": label or "-",
                "check": key,
                "value": val,
                "verdict": "pass" if ok else "FAIL",
            }
        )
        if not ok:
            res.failures.append(f"{prefix}{key} = {val!r} (must be {required!r})")
    if iso != "ERCOT":
        curves = sc.get("offer_curve_by_group") or {}
        if sc.get("gas_offer_curve"):
            uncovered = [g for g in D9_GENERIC_SHARE_GROUPS if g not in curves]
            if uncovered:
                res.failures.append(
                    f"{prefix}gas_offer_curve=True engages the ERCOT-mirrored "
                    f"generic tranche shares (_GAS_TRANCHE_SHARES) for "
                    f"{uncovered} — non-ERCOT ISOs must carry per-ISO or "
                    "neutral bands (offer_curves.py:130-143)"
                )
        for (
            groups,
            committed_key,
            econ_key,
            econ_lit,
            peak_key,
            peak_lit,
        ) in D9_HR_FALLBACKS:
            if sc.get(committed_key) is None:
                continue
            exposed = [g for g in groups if g not in curves]
            if not exposed:
                continue
            for key, lit in ((econ_key, econ_lit), (peak_key, peak_lit)):
                if sc.get(key) is None:
                    res.failures.append(
                        f"{prefix}{committed_key} set with {key} unset for "
                        f"{exposed}: the offer path falls back to the "
                        f"ERCOT-fitted literal {lit} (offer_curves.py:535-550)"
                    )
    return res


def run_d9_keepers(repo_root: Path) -> GateResult:
    """D-9 across every keeper bundle in the sharded keeper store
    (``frontend/data/backcast/keepers/<ISO>.json``; legacy monolith fallback)."""
    res = GateResult("D-9 overlay quarantine (all keepers)")
    for run_id in keeper_store.keeper_list(repo_root):
        side_path = repo_root / "frontend/data/backcast/registry" / f"{run_id}.json"
        side = json.loads(side_path.read_text())
        bundle = repo_root / side["bundle"]
        rc_path = bundle / "run_config.json"
        if not rc_path.exists():
            # A keeper whose bundle was never committed cannot be D-9 screened
            # (there is no run_config.json to inspect). Tolerate ONLY the tracked
            # known-unsynced ids (scripts/lib/known_unsynced_keepers.py); any
            # other missing bundle is a real break and FAILs.
            if run_id in UNSYNCED_KEEPERS:
                res.notes.append(
                    f"{run_id}: bundle {side['bundle']} not committed — D-9 "
                    "skipped (known-unsynced keeper; payload re-sync owed)"
                )
                continue
            res.failures.append(
                f"{run_id}: bundle {side['bundle']} missing run_config.json — "
                "cannot run D-9 overlay quarantine"
            )
            continue
        rc = json.loads(rc_path.read_text())
        sub = run_d9(rc, side.get("iso", ""), label=run_id)
        res.rows.extend(sub.rows)
        res.failures.extend(sub.failures)
    return res


def run_d2_keepers_verify(repo_root: Path) -> GateResult:
    """G-06: verify each keeper's committed D-2 forced-energy is reproducible.

    Prior to this gate, CI trusted each bundle's committed
    ``legitimacy_diagnostics.json`` at face value — nothing re-derived it, so
    a stale artifact (hand-edited, or generated before a later code/data
    change) would sail through unnoticed. This recomputes D-2 straight from
    the bundle's own committed data (the dashboard run payload for dispatch
    when ``dispatch/*.parquet`` is gitignored-absent, per-plant floors
    rebuilt via ``run_year(fleet_only=True)`` when ``floors/*.npz`` is
    likewise absent — the same deterministic fallback ``diagnose_bundle``
    already uses for local `--bundle` runs) and diffs the recomputed per-class
    GATED forced share against the committed one.

    The recompute is a LOWER-BOUND reconstruction, not a bit-faithful replay,
    so the comparison reconciles the two known, structural reasons it cannot
    equal a faithfully-generated committed artifact:

    1. **The P0-run-pattern commitment bridges.** ``run_year(fleet_only=True)``
       runs no LP, so every bridge detected from the model's own P0 solution
       (``model.commitment.caiso_ra_mustoffer_min_gen``: CAISO
       ``ra_mustoffer_bridge``, ERCOT ``gas_commitment_bridge``, NYISO
       ``nyiso_gas_commitment_bridge``, MISO ``miso_coal_night_floor``) is
       absent from rebuilt floors (``load_or_rebuild_floors`` returns
       ``ra_floor_missing``; ``run_d2`` flags the summary ``lower_bound``).
       Their forced energy is real and disclosed on the keeper (e.g. caiso-58
       CC_REGULAR 3.24 TWh; nyiso109 CC_REGULAR 3-5 pp), so we do NOT demand
       the recompute reproduce it: the committed side's bridge contributions
       are subtracted before comparing, leaving the REBUILDABLE gated share on
       both sides (caiso-155 widened this from the RA leg to the family —
       ``ct_netload_drag`` / ``reliability_floor`` are fleet-level and rebuild
       exactly).
    2. **Denominator attribution jitter.** A boundary plant can bin into a
       different class across fleet builds, shifting a class total by ~0.08 TWh
       and the forced share by ≤ ~1.65 pp on a small material class (measured
       worst case: CAISO CT_PEAKER). ``D2_VERIFY_SHARE_TOL`` (2.5 pp) absorbs
       this while still catching a stale/hand-edited artifact (a material-class
       share off by more).

    This stays a staleness check, NOT a re-litigation of the D-2 threshold: a
    committed FAIL that reproduces to the same FAIL is a ``pass`` here, and
    immaterial classes (numerically unstable on the knife-edge payload decode)
    are skipped, exactly as the C7/C8 rubric treats them.
    """
    res = GateResult("D-2 forced-energy recompute (all keepers)")
    keeper_ids = keeper_store.keeper_list(repo_root)
    if not keeper_ids:
        return res
    bridge_names = {MECH_NAMES[m] for m in BRIDGE_MECHS}
    for run_id in keeper_ids:
        side_path = repo_root / "frontend/data/backcast/registry" / f"{run_id}.json"
        side = json.loads(side_path.read_text())
        bundle = repo_root / side["bundle"]
        iso = side.get("iso", "")
        years = [int(y) for y in side.get("years", [])]
        committed_path = bundle / "legitimacy_diagnostics.json"
        if not committed_path.exists():
            res.notes.append(
                f"{run_id}: no committed legitimacy_diagnostics.json to verify "
                "against — skipped (see G-01/G-02)"
            )
            continue
        committed = json.loads(committed_path.read_text())
        committed_d2 = committed.get("diagnostics", {}).get("D2", {})
        committed_summary = {
            (row["year"], row["class"]): row for row in committed_d2.get("summary", [])
        }
        # Committed forced energy attributed to the non-rebuildable commitment
        # bridges, per (year, class): subtracted from the committed gated share
        # so the comparison is over the REBUILDABLE floors the recompute can
        # produce. The whole P0-run-pattern bridge family is excluded, not
        # just the CAISO RA leg (caiso-155): every bridge detected by
        # model.commitment.caiso_ra_mustoffer_min_gen needs the P0 solution,
        # which run_year(fleet_only=True) never has — nyiso109's armed
        # nyiso_gas_commitment_bridge carries 3-5 pp of CC_REGULAR's gated
        # share, so subtracting only the RA leg false-fails a faithful keeper.
        committed_bridge_twh: dict[tuple[int, str], float] = {}
        for row in committed_d2.get("rows", []):
            if row.get("mechanism") in bridge_names:
                k = (row["year"], row["class"])
                committed_bridge_twh[k] = committed_bridge_twh.get(k, 0.0) + row.get(
                    "forced_twh", 0.0
                )
        try:
            recomputed = diagnose_bundle(
                bundle, iso, years, repo_root=repo_root, only={"D2"}
            )
        except FileNotFoundError as exc:
            # The D-2 recompute rebuilds floors via run_year, which needs the
            # keeper's FETCHED raw inputs — uncommitted (e.g. data/raw/
            # pjm-da-virtuals/ tracks only a README). Absent them this keeper
            # can't be recomputed: note and skip rather than crash. The fast CI
            # gate skips D-2 wholesale (--no-d2-recompute); this keeps a local
            # --keepers run on a partial tree from aborting the whole sweep.
            res.notes.append(
                f"{run_id}: D-2 recompute needs fetched raw inputs absent on "
                f"this tree ({exc}) — skipped"
            )
            continue
        d2 = next((r for r in recomputed if r.name.startswith("D-2")), None)
        recomputed_summary = (
            {(row["year"], row["class"]): row for row in d2.summary}
            if d2 is not None
            else {}
        )
        for key in sorted(set(committed_summary) | set(recomputed_summary)):
            year, klass = key
            c_row = committed_summary.get(key)
            r_row = recomputed_summary.get(key)
            # An IMMATERIAL class (generation < PROTECTIVE_MIN_LOAD_FRAC of
            # load) never gates, so its exact forced_share is not gate-relevant
            # evidence — and on its near-zero denominator the share is
            # numerically unstable (the payload decode + floor rebuild flip a
            # knife-edge marginal floor in/out of "at floor", so e.g. NEISO
            # ST_GAS swings ~15 pp). Skip it: the staleness check verifies the
            # MATERIAL (gate-relevant) shares are reproducible.
            if (c_row and c_row.get("immaterial")) or (
                r_row and r_row.get("immaterial")
            ):
                res.rows.append(
                    {
                        "run": run_id,
                        "year": year,
                        "class": klass,
                        "committed_share": c_row["forced_share"] if c_row else 0.0,
                        "recomputed_share": r_row["forced_share"] if r_row else 0.0,
                        "verdict": "skip (immaterial)",
                    }
                )
                continue
            # A class absent from one side's summary means run_d2's own
            # total_by_class[k] <= 0.0 filter dropped it there (e.g. a
            # non-thermal class with no dispatch in that recompute) — the
            # same substantive fact as an explicit forced_share of 0.0, not
            # a discrepancy. Comparing missing-as-zero still catches a real
            # drift (a class with a genuine nonzero share on one side and no
            # row on the other legitimately fails below).
            c_share = c_row["forced_share"] if c_row else 0.0
            r_share = r_row["forced_share"] if r_row else 0.0
            # Subtract the committed P2 ra_mustoffer_bridge contribution (the
            # recompute cannot rebuild it) so both sides carry only the
            # REBUILDABLE gated floors. The recompute never contains the bridge
            # (fleet_only, no P2), so its share needs no adjustment.
            c_total = c_row.get("class_total_twh", 0.0) if c_row else 0.0
            bridge_share = (
                committed_bridge_twh.get(key, 0.0) / c_total if c_total > 0.0 else 0.0
            )
            c_rebuildable = max(0.0, c_share - bridge_share)
            ok = abs(c_rebuildable - r_share) <= D2_VERIFY_SHARE_TOL
            res.rows.append(
                {
                    "run": run_id,
                    "year": year,
                    "class": klass,
                    "committed_share": c_share,
                    "committed_rebuildable": round(c_rebuildable, 4),
                    "recomputed_share": r_share,
                    "verdict": "pass" if ok else "FAIL",
                }
            )
            if not ok:
                res.failures.append(
                    f"{run_id} {year} {klass!r}: committed rebuildable forced "
                    f"share {c_rebuildable:.4f} (of {c_share:.4f} gated, less "
                    f"{bridge_share:.4f} non-rebuildable commitment bridges) != "
                    f"recomputed {r_share:.4f} beyond {D2_VERIFY_SHARE_TOL:.3f} — "
                    "committed legitimacy_diagnostics.json is stale vs the bundle "
                    "it describes"
                )
    return res


# ---------------------------------------------------------------------------
# D-10 — free-class-only rescore (renewable-bound provenance)
# ---------------------------------------------------------------------------


def run_d10(
    iso: str, years: list[int], fuels: tuple[str, ...] = ("wind", "solar")
) -> GateResult:
    """D-10 free-class-only rescore: flag wind/solar rows pinned by L1.

    Report-only (wind/solar never gate a keeper verdict — they are advisory
    in ``calibration_verdict.py``), so this diagnostic never fails; it
    exists to make the L1 finding (docs/model-legitimacy-audit-2026-07.md
    §4: delivered EIA-930 output used as the renewable CF upper bound
    wherever no HSL/potential series exists) visible per bundle, per year,
    per fuel, so a C1-style pass on a "delivered_pinned" row is never quoted
    as forecast skill. Uses
    :func:`market_sim.data.renewables.renewable_bound_provenance` — the same
    logic the dispatch build consumes — never re-derives it.
    """
    from market_sim.data.renewables import (  # noqa: PLC0415 (optional heavy import)
        RENEWABLE_BOUND_DELIVERED_PINNED,
        renewable_bound_provenance,
    )

    res = GateResult("D-10 free-class-only rescore (renewable-bound provenance)")
    for year in years:
        for fuel in fuels:
            provenance = renewable_bound_provenance(iso, year, fuel)
            pinned = provenance == RENEWABLE_BOUND_DELIVERED_PINNED
            res.rows.append(
                {
                    "year": year,
                    "fuel": fuel,
                    "provenance": provenance,
                    "pinned": pinned,
                    "verdict": "PINNED (advisory-only, excluded from skill claims)"
                    if pinned
                    else "free",
                }
            )
    n_pinned = sum(1 for r in res.rows if r["pinned"])
    res.notes.append(
        f"{iso}: {n_pinned}/{len(res.rows)} wind/solar (year, fuel) rows ride "
        "the L1 delivered-outcome bound; their advisory-only C1 rows measure "
        "plumbing, not model skill (never gate the keeper verdict)."
    )
    return res


def _decode_cf_bytes(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode an 8760-byte CF%-encoded series to hourly MW.

    Bytes are ``round(100 * mw / nameplate)`` (render_calibration_html._b64);
    when the annual total is available the series is rescaled to it exactly,
    removing the byte quantization from every energy sum.
    """
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def load_bench(repo_root: Path, iso: str, year: int) -> dict[str, dict]:
    """Load the CAMPD bench file: plant key -> {group, zone, npl, mw}.

    Keys are the bench wire keys: bare ``"<code>"`` for a single-class plant,
    ``"<code>:<KLASS>"`` per class slice of a multi-class plant (the nyiso-88
    §5 attribution fix). D-1 pairs these slice keys directly; plant-level
    consumers (D-2/D-4) aggregate them via :func:`bench_plant_view`.
    """
    path = repo_root / "frontend/data/backcast/bench" / iso / f"{year}.json.gz"
    data = ba.load_bench_part(path)
    plants = {}
    for pid, p in data["bench"]["plants"].items():
        if p.get("nodata") or not p.get("campd"):
            continue
        plants[pid] = {
            "group": p["group"],
            "zone": p.get("zone"),
            "npl": float(p.get("npl") or 0.0),
            "ct_only": bool(p.get("ct_only", False)),
            "mw": _decode_cf_bytes(
                p["campd"], p.get("c_ann"), float(p.get("npl") or 0.0)
            ),
        }
    return plants


def bench_plant_view(bench: dict[str, dict]) -> dict[str, dict]:
    """Aggregate a (possibly slice-keyed) bench to plant level.

    ``{"<code>": {npl, mw}}`` with slice npl/mw summed per plant — the view
    D-2/D-4 consume (their plant class attribution is the floors-majority
    convention, deliberately independent of the bench grouping).
    """
    out: dict[str, dict] = {}
    for key, b in bench.items():
        code = str(bm.plant_code_of_key(key))
        # ``ct_only``: the benchmark's own CT-only CEMS flag (EIA-923 net >
        # 1.1x CAMPD gross), which marks a plant whose CAMPD HOURLY series is
        # incomplete and which the benchmark therefore scores on EIA-923
        # MONTHLY instead. Carried through so the D-4 per-unit conduct rider
        # can decline to read an hourly meter the benchmark itself does not
        # trust; a plant is flagged if ANY of its class slices is.
        ct_only = bool(b.get("ct_only", False))
        cur = out.get(code)
        if cur is None:
            out[code] = {
                "npl": float(b["npl"]),
                "mw": np.asarray(b["mw"], float),
                "ct_only": ct_only,
            }
        else:
            cur["npl"] += float(b["npl"])
            cur["mw"] = cur["mw"] + np.asarray(b["mw"], float)
            cur["ct_only"] = cur.get("ct_only", False) or ct_only
    return out


def ct_only_span_union(
    repo_root: Path, iso: str, years: "list[int] | tuple[int, ...]"
) -> set[str]:
    """Plant codes flagged ``ct_only`` in ANY scored year's bench — the D-4
    vintage guard's union set.

    ``ct_only`` (EIA-923 net > 1.1× CAMPD gross ⇒ the benchmark scores the
    plant on EIA-923 monthly) is a metering-configuration CHARACTER of the
    plant, not a year property; in a preliminary-vintage year the ratio's
    ``e_ann`` falls back to ``c_ann`` and computes exactly 1.00, silently
    un-flagging the plant. The union restores the flag in those years so the
    per-unit conduct rider cannot convict on a series the benchmark's own
    complete-vintage years decline to trust (protective direction only — it
    can only ever SKIP a conviction). Measured on NYISO 2023–2025 at
    introduction (nyiso-150): ten plants lose the flag in 2025, zero gain it.

    **The union is taken over the ISO's whole TRAINING SPAN, not only the
    bundle's own scored years** (nyiso-200). A rule-29 one-year screen bundle
    scores a single year, and until nyiso-200 its union was that year alone —
    so a 2025-only screen had NO sibling vintage to restore the flag from and
    the rider convicted exactly the plants the span scorer skips: nyiso-199's
    2025 screen stopped on NYISO 7314 / 50978, both ``ct_only`` in the
    complete 2023 and 2024 vintages and un-flagged only by the preliminary
    2025 one (the nyiso-145 §3 artifact, re-fired through a different door).
    The guard's own premise is that the flag is a character of the plant, so
    the set it unions over is every training-span year with a bench, plus the
    bundle's own years; a span keeper (years == the training span) re-scores
    byte-identically. Still protective-direction only.
    """
    return _ct_only_union_over(
        repo_root, iso, ct_only_guard_years(repo_root, iso, years)
    )


def ct_only_guard_years(
    repo_root: Path, iso: str, years: "list[int] | tuple[int, ...]"
) -> list[int]:
    """Years the D-4 vintage guard unions ``ct_only`` over for ``iso``.

    The bundle's own scored ``years`` plus every training-span year
    (``holdout_policy.CALIBRATION_YEARS``) whose bench part exists on disk.
    Training years are a fixed, published set (rule 22), so adding them
    never reads a held-out year's answer; a year with no bench is skipped
    rather than raised on, so an ISO whose span is partial still scores.
    """
    out = {int(y) for y in years}
    for y in sorted(holdout_policy.CALIBRATION_YEARS):
        if y in out:
            continue
        if (repo_root / "frontend/data/backcast/bench" / iso / f"{y}.json.gz").exists():
            out.add(int(y))
    return sorted(out)


def _ct_only_union_over(repo_root: Path, iso: str, years: "list[int]") -> set[str]:
    """Union of ``ct_only`` plant codes over exactly ``years`` (no widening)."""
    union: set[str] = set()
    for y in years:
        for pid, b in bench_plant_view(load_bench(repo_root, iso, y)).items():
            if b.get("ct_only"):
                union.add(pid)
    return union


def aggregate_model_plants(
    model_plants: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Sum a (possibly slice-keyed) model per-plant map to bare plant codes."""
    out: dict[str, np.ndarray] = {}
    for key, arr in model_plants.items():
        code = str(bm.plant_code_of_key(key))
        out[code] = arr if code not in out else out[code] + arr
    return out


def find_registry_sidecar(repo_root: Path, bundle: Path) -> dict | None:
    """Find the dashboard registry sidecar whose ``bundle`` field matches."""
    rel = str(bundle.resolve().relative_to(repo_root.resolve()))
    reg_dir = repo_root / "frontend/data/backcast/registry"
    for path in sorted(reg_dir.glob("*.json")):
        side = json.loads(path.read_text())
        if side.get("bundle") == rel:
            return side
    return None


def load_payload_plants(
    repo_root: Path, sidecar: dict, year: int, bench: dict[str, dict]
) -> dict[str, np.ndarray]:
    """Decode the run payload's per-plant hourly model MW for one year."""
    txt = (repo_root / sidecar["file"]).read_text()
    run = ba.decode_run_js(txt)
    plants = run["years"][str(year)]["plants"]
    out = {}
    for pid, p in plants.items():
        if not p.get("m"):
            continue
        npl = bench.get(pid, {}).get("npl", 0.0)
        out[pid] = _decode_cf_bytes(p["m"], p.get("m_ann"), npl)
    return out


def load_payload_total_load_mwh(
    repo_root: Path, sidecar: dict, year: int
) -> float | None:
    """Total system load (~ served energy) for a payload year, in MWh.

    Sum of the payload's per-zone demand (``lmp[<zone>].d``, TWh) — the SAME
    quantity, from the same field, that ``calibration_verdict._total_load``
    uses for the C8 materiality denominator it computes independently, so the
    quarantine gate and the rubric scorer draw one line rather than two.
    Returns ``None`` when the payload carries no ``lmp`` block, which leaves
    the guard disabled so no breach is hidden by a missing denominator.

    **CORRECTED nyiso-242.** This summed ``fuelRows[*].m`` instead, described
    as "the model's served-energy balance, i.e. total load". It is neither,
    and it was wrong by ~2.25x: ``fuelRows`` carries only gas / coal / nuclear
    / wind / solar / interchange, so it **omits hydro** — 26.2 TWh of NYISO's
    152.7 TWh in 2022, the single largest omission — and biomass and storage,
    **and it SUBTRACTS the signed net-interchange row** when a net importer's
    imports are part of the load it serves. Measured on the NYISO keeper's own
    payload, 2022: ``fuelRows`` gives 67.92 TWh against a true 152.68 TWh
    (gas 63.5 + coal 0.67 + nuclear 26.75 + wind 4.7 + solar 0.11 **− 27.81**
    interchange). Understating the denominator INFLATES every class's load
    share, so the rule-20 ``PROTECTIVE_MIN_LOAD_FRAC`` floor bound at roughly
    half its intended level and gated classes rule 20 says are "reported by
    the D-1/D-2 diagnostics but never gated". The replacement reproduces
    ``calibration_verdict._total_load`` exactly (NYISO 2022: 152.682 TWh from
    both, and from the bundle's own ``hourly/system_2022.parquet`` demand).
    """
    txt = (repo_root / sidecar["file"]).read_text()
    try:
        run = ba.decode_run_js(txt)
    except ValueError:
        return None
    lmp = run.get("years", {}).get(str(year), {}).get("lmp") or {}
    total_twh = sum(float(z.get("d", 0.0) or 0.0) for z in lmp.values())
    return total_twh * 1e6 if total_twh > 0.0 else None


def load_bundle_total_load_mwh(bundle: Path, year: int) -> float | None:
    """Total system load (MWh) from the bundle's OWN committed sidecar.

    ``hourly/system_<year>.parquet`` (a rule-15 keeper sidecar, so present in
    every committed bundle) carries per-zone hourly ``demand``; summing the
    final pass over the internal zones is the same served-energy total
    :func:`load_payload_total_load_mwh` reads from the registered payload.

    **Why this exists (nyiso-242).** The payload route needs a registry
    sidecar, and the artifact is written **at solve time — before the run is
    registered** — so ``sidecar`` is ``None`` and the materiality denominator
    was simply missing. Measured across every committed bundle: **285 of 315
    D-2 summary rows (90 %) carry ``load_share: null``**, which disables the
    rule-20 materiality guard in the artifact and leaves ``immaterial`` False
    on classes far below the floor. NEISO's keeper publishes five D-2 FAILURES
    on classes at 0.08-0.80 % of load in consequence. (No determination moved:
    ``calibration_verdict`` computes its own share from its own ``_total_load``
    and correctly SKIPs them — an undocumented redundancy that is the only
    reason this was latent rather than live.)

    Returns ``None`` when the sidecar is absent or carries no demand, leaving
    the guard disabled exactly as before — never a silent substitution.
    """
    import pandas as pd

    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["pass", "zone", "demand"])
    if "pass" in df.columns and len(df):
        # The final pass is the one every other diagnostic scores on.
        for label in ("P2", "P1"):
            if (df["pass"] == label).any():
                df = df[df["pass"] == label]
                break
    # External/import proxy nodes carry no native load.
    df = df[~df["zone"].astype(str).str.contains("external", case=False, na=False)]
    total = float(df["demand"].sum())
    return total if total > 0.0 else None


def load_dispatch_parquet(bundle: Path, year: int):
    """Return the year's final-pass dispatch frame, or None when absent."""
    import pandas as pd

    for label in ("P2", "P1"):
        path = bundle / "dispatch" / f"{year}_{label}.parquet"
        if path.exists():
            return pd.read_parquet(path), label
    return None, None


# meta.json key -> run_year kwarg, where the names differ. The three generic
# override channels MUST be threaded (caiso-155 addendum Part 0): run_year
# accepts them as prb_overrides / bit_overrides / coal_bit_sigmoid (the same
# mapping scripts/replay_keeper.py::_REMAP applies for solve_and_persist), and
# dropping them rebuilt floors WITHOUT every mechanism armed through the
# channel — CAISO's firm-import trio rides ONLY there (the caiso-150 §E2
# silent trap), and five of six keepers arm floor mechanisms through it
# (PREREG-caiso155-ADDENDUM-rebuild-channel-2026-08-02.md §A). Keys that
# remain unmapped after this are price/demand-side (no min_gen stamp) and are
# the rebuild's documented residual fidelity limit, absorbed by G-06's
# D2_VERIFY_SHARE_TOL. tests/scoring/test_legitimacy_diagnostics.py asserts
# this map's targets exist in run_year's signature and that it agrees with
# replay_keeper._REMAP wherever both map a key run_year accepts.
REBUILD_META_RENAMES: dict[str, str] = {
    "commitment": "commitment_enabled",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
}


def _rebuild_fleet_arrays(bundle: Path, iso: str, year: int):
    """Rebuild a bundle-year's ``FleetArrays`` via ``run_year(fleet_only=True)``.

    Builds no LP (rule 32 ``[R-SHARD]``): it constructs the fleet from the
    bundle's OWN ``meta.json`` flags and stops. Shared by the floor rebuild and
    by :func:`_backfill_pmax`, so both read the identical recipe — a backfilled
    ``pmax`` and a rebuilt floor can never come from different fleets.

    The recipe is ``meta.json`` **plus**
    :data:`scripts.replay_keeper.DERIVED_RUN_YEAR_INPUTS` — the ``run_year``
    inputs ``solve_and_persist`` derives from its own locals, which the bundle
    therefore never records and which no amount of ``meta.json`` reading can
    recover. See the ``derived`` comment below for why omitting them rebuilt a
    different fleet than the one being scored.
    """
    import inspect

    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {}
    dropped = []
    for k, v in meta.items():
        k2 = REBUILD_META_RENAMES.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    # caiso-292: ``meta.json`` is NOT the whole recipe. ``solve_and_persist``
    # derives some ``run_year`` inputs from its own locals, so they are
    # invisible to the loop above however many keys it maps — the gap
    # ``replay_keeper.DERIVED_RUN_YEAR_INPUTS`` names and
    # ``derived_run_year_inputs`` closes by reading the bundle's OWN committed
    # ``hourly/class_hourly_<year>.parquet``. Today that is
    # ``inject_biomass_mustrun``, which ``run_year`` forwards as
    # ``drop_biomass_units``: the solve REMOVES the raw biomass LP units
    # because the same energy is injected as a measured EIA-923 must-run
    # profile, and a rebuild that omits the flag carries phantom biomass rows
    # the scored solve never had (caiso-248, which invalidated caiso-247's
    # DOM_OTHER attribution). Measured on the CAISO keeper
    # (``xiso8_leftedge_span`` 2024): 1,905 rebuilt rows against the solve's
    # 1,705 — a strict SUPERSET of exactly 200 biomass rows, so the rebuilt
    # fleet was not row-aligned with the bundle's own per-unit artifacts; with
    # the splat it reproduces the solve fleet unit-for-unit IN ORDER, with
    # ``pmax`` exact to 0.000000000 MW on all 1,705 rows. ``replay_keeper`` has
    # stated this duty since caiso-248 ("every fleet-only rebuild should splat
    # this") and ``scripts/lib/bundle_fleet.reconstruct_bundle_fleet``
    # discharges it for the probe lane — THIS rebuild, the one rule 19
    # ``[R-FORCED-BUDGET]``'s "keepers re-score in place" promise runs through,
    # did not. Applied AFTER ``kwargs`` so the solve-side value always wins.
    # Raises ``FileNotFoundError`` when the sidecar is absent rather than
    # assuming ``False``: every registered bundle carries it, and a silent
    # ``False`` is the defect (:func:`_backfill_pmax` catches the failure and
    # records its documented row-count fallback, so the degradation is never
    # silent there either).
    derived = derived_run_year_inputs(bundle, year)
    kwargs.update(derived)
    logger.info(
        "fleet rebuild: %d flags passed (incl. derived %s), dropped %s",
        len(kwargs),
        derived,
        dropped,
    )
    gas_prices = meta.get("gas_prices", {})
    gas_price = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
    state = run_year(
        year,
        iso,
        int(meta.get("hours", 8760)),
        gas_price,
        {},
        fleet_only=True,
        **kwargs,
    )
    return state["fleet_arrays"]


def _backfill_pmax(arrays: dict, bundle: Path, iso: str, year: int) -> dict:
    """Add ``pmax`` to floor arrays persisted before nyiso-233 wrote the key.

    The D-2 plant-class vote is capacity-weighted, but ``floors/*.npz`` written
    before 2026-09-13 carry no ``pmax``. It is recovered by joining the npz's
    ``unit_ids`` to a ``fleet_only`` rebuild (zero LP) — an EXACT recovery, not
    a reconstruction, because ``pmax`` is a fleet property that no P0/P1 pass
    changes. **The floors themselves are untouched**: only the vote weight is
    added, so the committed numerator stays the numerator the LP saw.

    The join is BY ``unit_id`` and never positional — measured on the NYISO
    keeper, the npz and the rebuilt fleet share every unit but not their order
    (715 npz rows resolving into an 829-row fleet), so a positional alignment
    would be silently wrong.

    Returns ``arrays`` unchanged if the rebuild is unavailable or does not cover
    every row; the caller then scores on the row-count fallback and records
    ``plant_class_vote_basis`` accordingly, so the degradation is never silent.
    """
    uids = np.asarray(arrays["unit_ids"]).astype(str)
    try:
        fa = _rebuild_fleet_arrays(bundle, iso, year)
    except Exception as exc:  # pragma: no cover - environment-dependent
        logger.warning(
            "%s %s: pmax backfill unavailable (%s); D-2 plant-class vote falls "
            "back to the pre-nyiso-233 ROW COUNT basis",
            iso,
            year,
            exc,
        )
        return arrays
    if fa.pmax is None:
        logger.warning(
            "%s %s: rebuilt fleet carries no pmax; row-count fallback", iso, year
        )
        return arrays
    by_uid = dict(zip([str(u) for u in fa.unit_ids], np.asarray(fa.pmax, dtype=float)))
    missing = [u for u in uids if u not in by_uid]
    if missing:
        logger.warning(
            "%s %s: %d of %d floor rows have no rebuilt pmax (e.g. %s); "
            "D-2 plant-class vote falls back to the ROW COUNT basis",
            iso,
            year,
            len(missing),
            len(uids),
            missing[:3],
        )
        return arrays
    out = dict(arrays)
    out["pmax"] = np.array([by_uid[u] for u in uids], dtype=float)
    logger.info("%s %s: backfilled pmax for %d floor rows", iso, year, len(uids))
    return out


def load_or_rebuild_floors(
    bundle: Path, iso: str, year: int, force_rebuild: bool = False
) -> tuple[dict, bool]:
    """Return unit-level floor arrays for a bundle-year.

    Prefers the persisted ``floors/<year>_<pass>.npz`` (P2 first — it carries
    the RA must-offer layer); otherwise rebuilds through
    ``run_year(fleet_only=True)`` with the bundle's own ``meta.json`` flags
    and caches the result as ``floors/<year>_rebuilt.npz``. Returns
    ``(arrays, ra_floor_missing)`` — the flag marks a rebuild, whose floors
    exclude the P1-dependent RA bridge.
    """
    floors_dir = bundle / "floors"
    if not force_rebuild:
        for name, ra_missing in (
            (f"{year}_P2.npz", False),
            (f"{year}_P1.npz", True),
            (f"{year}_rebuilt.npz", True),
        ):
            path = floors_dir / name
            if path.exists():
                with np.load(path, allow_pickle=False) as z:
                    arrays = {k: z[k] for k in z.files}
                if "pmax" not in arrays:
                    arrays = _backfill_pmax(arrays, bundle, iso, year)
                return arrays, ra_missing

    logger.info("%s %s: rebuilding floors via run_year(fleet_only=True)", iso, year)
    fa = _rebuild_fleet_arrays(bundle, iso, year)
    if fa.min_gen is None:
        n, t = len(fa.unit_ids), int(fa.availability.shape[1])
        min_gen = np.zeros((n, t), dtype=np.float32)
        mech = np.zeros((n, t), dtype=np.int8)
    else:
        min_gen = fa.min_gen.astype(np.float32)
        mech = (
            fa.min_gen_mechanism
            if fa.min_gen_mechanism is not None
            else np.zeros(fa.min_gen.shape, dtype=np.int8)
        )
    groups = (
        fa.plant_group
        if fa.plant_group is not None
        else np.array([""] * len(fa.unit_ids), dtype=object)
    )
    arrays = {
        "min_gen": min_gen,
        "mechanism": np.asarray(mech, dtype=np.int8),
        # The D-2 plant-class vote weight (nyiso-233). Persisted so a cached
        # rebuild never needs a second fleet build to recover it.
        "pmax": np.asarray(
            fa.pmax if fa.pmax is not None else np.zeros(len(fa.unit_ids)), dtype=float
        ),
        "unit_ids": np.array(list(fa.unit_ids), dtype=str),
        "plant_code": np.asarray(fa.plant_code, dtype=np.int64),
        "plant_group": np.array([str(g) for g in groups], dtype=str),
    }
    floors_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(floors_dir / f"{year}_rebuilt.npz", **arrays)
    return arrays, True


# Key prefix marking a non-plant (pseudo-unit) row in the D-2/D-4 matrices:
# a unit with ``plant_code <= 0`` that carries a positive floor (interchange
# firm-import tranches). Cannot collide with the numeric plant keys.
PSEUDO_PLANT_KEY_PREFIX = "u:"


@dataclass(frozen=True)
class FloorClassMatrix:
    """Per plant-HOUR class of the floor's max-contributing unit, vocab-encoded.

    The unit-grain repair of the D-4 plant-grain class-attribution defect
    (miso-169 §5 ask 2 → miso-170 K-1 forensic → the miso-171 charter item):
    ``aggregate_floors_by_plant`` labels each ROW with its plant's most-common
    unit group, so a mixed-class site's floor carried by a MINORITY-class unit
    was charged to the majority class's D-2 mechanism rows and D-4 provenance
    leg (the live case: plant 1104's CT_PEAKER netload floor charged to
    ST_GAS's C8 provenance in every pre-repair MISO artifact). This matrix
    resolves the class the same way the plant-hour MECHANISM is already
    resolved — maximum-composition: the class of the unit contributing the
    largest floor that hour — so floors are attributed to the class that
    actually carries them, while the plant stays one row (the metering and
    dispatch grain). Empty unit groups impute to the plant's majority
    non-empty group first (the #1488 rule, unchanged), so single-class plants
    are attributed exactly as before.

    ``codes`` is (n, T) int16 into ``names``; unfloored cells carry the row's
    own label code (inert under the at-floor mask, kept meaningful).
    """

    codes: np.ndarray
    names: tuple[str, ...]

    def eq(self, name: str) -> np.ndarray:
        """Boolean (n, T) mask of cells whose floor class is ``name``."""
        try:
            code = self.names.index(str(name))
        except ValueError:
            return np.zeros(self.codes.shape, dtype=bool)
        return self.codes == code

    def present_under(self, mask: np.ndarray) -> list[str]:
        """Class names holding at least one cell of ``mask`` (sorted)."""
        codes = np.unique(self.codes[mask])
        return sorted(self.names[int(c)] for c in codes)


@dataclass(frozen=True)
class PlantMatrices:
    """The aligned (n, T) D-2/D-4 input matrices plus each row's provenance.

    ``substituted`` marks rows whose dispatch was SUBSTITUTED by their own
    floor because the active dispatch source carries no series for them
    (pjm-149 §3.2). ``substituted_pseudo`` / ``substituted_plants`` split those
    keys by kind for the two disclosure notes.
    """

    pids: list[str]
    disp: np.ndarray
    floors: np.ndarray
    mechs: np.ndarray
    klass: np.ndarray
    npl: np.ndarray
    substituted: np.ndarray
    substituted_pseudo: list[str]
    substituted_plants: list[str]
    #: Per-cell floor class (FloorClassMatrix) aligned to the full row set —
    #: what D-2 mechanism attribution and D-4 selection key on when present.
    #: None on legacy/direct paths: row labels attribute, the pre-repair rule.
    floor_klass: FloorClassMatrix | None = None


def build_plant_matrices(
    model_plants_plant: dict[str, np.ndarray],
    pid_strs: list[str],
    floor_sum: np.ndarray,
    mech_plant: np.ndarray,
    groups: np.ndarray,
    bench_pl: dict[str, dict],
    t: int = 8760,
    floor_klass: FloorClassMatrix | None = None,
) -> PlantMatrices:
    """Assemble the D-2/D-4 row matrices from a dispatch map and a floors fleet.

    **The row set is PATH-INDEPENDENT** (pjm-149 §3.1): it is every dispatch-map
    plant that carries a class in the floors fleet, UNION every floored key —
    whether or not the active dispatch source happens to cover it. Before
    pjm-149 the set was a comprehension over the dispatch map alone, so a plant
    that was floored but absent from that map was dropped silently, with no row,
    no failure and no note. The map is the solve's own
    ``dispatch/<year>_<pass>.parquet`` (every model plant; gitignored, so absent
    from every committed bundle) or, failing that, the CAMPD-bench-keyed
    dashboard run payload — which carries only plants with a CEMS meter, so at
    PJM it dropped all 14 CC_CHP plants and at every ISO the nuclear must-run
    block (17-90 TWh/yr). The committed keeper corpus is SPLIT across the two
    paths, which is what made the attribution silently non-comparable between
    bundles (FINDING-pjm149 §2).

    **Dispatch for a floored plant the map does not cover is its OWN FLOOR**
    (``disp := min_gen``) — PREREG-caiso155 §3's floor-energy convention,
    generalized from ``plant_code <= 0`` pseudo-units to real plants, and
    justified by a one-sided bound rather than by availability alone
    (PREREG-pjm149 §3.2):

    * forced energy sums ``dispatch`` over at-floor hours only, and at-floor
      means ``dispatch ~= min_gen``, so true forced energy <= the floor energy
      — substituting the floor is an UPPER bound on the D-2 numerator;
    * LP feasibility gives ``P >= min_gen`` whenever the unit is available, so
      the plant's true dispatch >= its floor energy — substituting the floor
      UNDERSTATES the class denominator.

    The reported ``forced_share`` is therefore an UPPER BOUND on the true
    share. Rule 18 ``[R-FORCED-BUDGET]`` fails HIGH, so the bound is sound on a
    pass (under the cap proves under the cap) and INDETERMINATE on a fail —
    never a valid FAIL on its own. ``run_d2`` stamps ``upper_bound`` on the
    summary row of every class holding such a plant so the bound travels with
    the number.

    UNFLOORED plants absent from the map stay excluded: they carry no floor and
    must not perturb any class denominator (PREREG-caiso155 §2 P3 / pjm-149 C5,
    which counted 5-381 such plants per ISO-year).
    """
    klass_by_pid = dict(zip(pid_strs, groups))
    # Class totals need EVERY plant of the class, floored or not: rows below
    # carry all model plants, floors zero-filled outside the floored set.
    # Plants absent from the FLOORS fleet (e.g. non-thermal payload rows) are
    # excluded — they carry no class in the model fleet.
    covered = [p for p in model_plants_plant if p in klass_by_pid or p in pid_strs]
    absent_floored = [
        p
        for j, p in enumerate(pid_strs)
        if p not in model_plants_plant and floor_sum[j].max() > D2_FLOOR_MIN_MW
    ]
    all_pids = covered + absent_floored

    disp = np.zeros((len(all_pids), t))
    floors = np.zeros((len(all_pids), t))
    mechs = np.zeros((len(all_pids), t), dtype=np.int8)
    klass = np.empty(len(all_pids), dtype=object)
    npl = np.zeros(len(all_pids))
    index = {p: i for i, p in enumerate(all_pids)}
    for p, i in index.items():
        if p in model_plants_plant:
            disp[i] = model_plants_plant[p][:t]
        klass[i] = klass_by_pid.get(p, "")
        npl[i] = bench_pl.get(p, {}).get("npl", float(disp[i].max()))
    for j, p in enumerate(pid_strs):
        if p in index:
            floors[index[p]] = floor_sum[j][:t]
            mechs[index[p]] = (
                mech_plant[j][:, :t] if mech_plant[j].ndim > 1 else mech_plant[j][:t]
            )
    substituted = np.zeros(len(all_pids), dtype=bool)
    for p in absent_floored:
        disp[index[p]] = floors[index[p]]
        substituted[index[p]] = True
    fk_full: FloorClassMatrix | None = None
    if floor_klass is not None:
        # Align the floors-fleet floor-class matrix onto the full row set:
        # rows outside the floors fleet carry their own label code (inert
        # under the at-floor mask — they hold no floor).
        code_of = {n: c for c, n in enumerate(floor_klass.names)}
        row_label = np.array(
            [code_of.get(str(klass[i]), 0) for i in range(len(all_pids))],
            dtype=np.int16,
        )
        codes = np.repeat(row_label[:, None], t, axis=1)
        for j, p in enumerate(pid_strs):
            if p in index:
                codes[index[p]] = floor_klass.codes[j][:t]
        fk_full = FloorClassMatrix(codes=codes, names=floor_klass.names)
    return PlantMatrices(
        pids=all_pids,
        disp=disp,
        floors=floors,
        mechs=mechs,
        klass=klass,
        npl=npl,
        substituted=substituted,
        floor_klass=fk_full,
        substituted_pseudo=[
            p for p in absent_floored if p.startswith(PSEUDO_PLANT_KEY_PREFIX)
        ],
        substituted_plants=[
            p for p in absent_floored if not p.startswith(PSEUDO_PLANT_KEY_PREFIX)
        ],
    )


def aggregate_floors_by_plant(
    arrays: dict,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, FloorClassMatrix]:
    """Aggregate unit-level floors to plants: keys, floor sum, binding mech, class.

    The plant floor is the sum of its units' positive floors; the plant-hour
    mechanism is the id of the unit contributing the largest floor that hour
    (maximum-composition at plant level). Loops over plants, never hours.
    Keys are strings: ``str(plant_code)`` per aggregated plant, plus one
    ``"u:<unit_id>"`` row per FLOORED ``plant_code <= 0`` pseudo-unit.

    The fifth return is the :class:`FloorClassMatrix` — the plant-hour FLOOR
    class under the same maximum-composition rule as the mechanism (the class
    of the unit contributing the largest floor that hour, empty groups imputed
    to the plant majority first). It is what D-2 mechanism attribution and
    D-4 selection key on, so a mixed-class site's minority-class floor is
    charged to the class that carries it rather than to the plant label (the
    miso-170 K-1 forensic / miso-171 charter item (a); see
    :class:`FloorClassMatrix`). The plant LABEL below (fourth return) is
    unchanged and still names the row and its class denominator.

    The plant class is the non-empty unit group carrying the **most CAPACITY**
    in the plant — NOT the first unit's group, and (since nyiso-233) NOT the
    most common one. A single plant frequently mixes classified units with an
    unbinned/unclassified component (e.g. NEISO plant 546 carries 8 ``ST_GAS``
    units + 1 empty-group unit); taking the first unit's group let that lone
    empty label capture the whole plant into the ``''`` bucket, so its dispatch
    (and any binding floor) was mis-attributed away from its real merchant class
    and the class denominator was under-counted (#1488, rule 20).

    **VOTE WEIGHT — why capacity and not row count (nyiso-233).** The vote was
    a plain ROW COUNT until 2026-09-13, and the number of LP rows a class
    contributes to a plant is a property of the **offer curve's band structure**,
    not of the plant: a mechanism that collapses or expands a class's econ
    smoothing ladder could move a whole site's dispatch between class
    denominators with no physical change at all, and flip C8 (protective tier,
    zero caveat budget) on it. Measured on the NYISO keeper: Ravenswood
    (plant 2500) carries **1724.8 MW of ``ST_GAS`` against 268.5 MW of
    ``CC_REGULAR``** — 6.4:1 — yet its rows read 4 vs 7, so the row-count vote
    labelled a 87 %-steam site ``CC_REGULAR``. Capacity is the right weight
    because the bands of a plant-class **partition that class's capacity however
    many bands there are**, so the vote is band-invariant by construction; and
    because ``pmax`` depends on no dispatch outcome, so a plant's class
    denominator is a property of the plant rather than of the solve. (Energy
    weighting is also band-invariant and needs no fleet rebuild, but it was
    REJECTED for that second reason — arm and control would legitimately label a
    plant differently whenever dispatch moved.) Defect, fragility census and the
    blast-radius analysis:
    ``docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md``;
    repair and its pre-registered stop conditions:
    ``results/calibration/PRECOMMIT-nyiso233-d2-capacity-weighted-vote.md``.
    Landed on an explicit owner ruling, since a shared scorer reaches every ISO
    (rule 25 ``[R-ISO-SCOPE]``).

    The weight is ``arrays["pmax"]`` when present. ``load_or_rebuild_floors``
    backfills it into any pre-nyiso-233 ``floors/*.npz`` (which predate the key)
    from a ``fleet_only`` rebuild, so the fallback below is not reached in
    normal operation; when it IS reached the vote reverts to row count and the
    caller records ``plant_class_vote_basis="row_count_fallback"`` in the
    diagnostics artifact, so no run is ever scored on the defective basis
    without saying so.
    A plant whose units are *all* unclassified (nuclear / hydro / renewables,
    which carry no CAMPD plant_group) stays ``''`` — those non-thermal must-run
    rows are excluded from the merchant forced-share summary in ``run_d2``.

    Pseudo-unit rows (caiso-151 §F / caiso-155): a ``plant_code <= 0`` unit
    with a floor above ``D2_FLOOR_MIN_MW`` in any hour — an interchange
    firm-import tranche (``MECH_FIRM_IMPORT``: CAISO RA/LTC blocks, MISO
    Manitoba, NYISO HQ) — was previously DROPPED here, leaving 2-8 TWh/yr of
    must-flow floor invisible to D-2 and D-4. Each now rides as its own
    per-unit row (no plant to aggregate to), keyed by unit id, carrying its
    own ``plant_group`` (empty for interchange tranches, so the ``''``-bucket
    exclusion above still governs the gated summary). UNFLOORED
    ``plant_code <= 0`` rows (economic import bands, export sinks, seam
    bands) stay excluded — they carry no floor and must not perturb any
    class denominator.
    """
    plant_code = np.asarray(arrays["plant_code"])
    keep = plant_code > 0
    pos = np.clip(np.asarray(arrays["min_gen"], dtype=float)[keep], 0.0, None)
    mech = np.asarray(arrays["mechanism"])[keep]
    groups = np.asarray(arrays["plant_group"]).astype(str)[keep]
    pc = plant_code[keep]
    order = np.argsort(pc, kind="stable")
    pos, mech, groups, pc = pos[order], mech[order], groups[order], pc[order]
    # Vote weight: CAPACITY when the arrays carry it, else one-per-row (the
    # pre-nyiso-233 basis, kept only as a declared fallback — see the
    # "vote weight" paragraph of the docstring and ``plant_class_vote_basis``).
    if arrays.get("pmax") is not None:
        weight = np.clip(
            np.asarray(arrays["pmax"], dtype=float)[keep][order], 0.0, None
        )
    else:
        weight = np.ones(pc.size, dtype=float)
    starts = np.flatnonzero(np.r_[True, pc[1:] != pc[:-1]])
    bounds = np.r_[starts, pc.size]
    t = pos.shape[1]
    n_plants = starts.size
    floor_sum = np.add.reduceat(pos, starts, axis=0)
    mech_plant = np.zeros((n_plants, t), dtype=np.int8)
    group_plant = np.empty(n_plants, dtype=object)
    vocab: dict[str, int] = {"": 0}
    fcode = np.zeros((n_plants, t), dtype=np.int16)
    label_code = np.zeros(n_plants, dtype=np.int16)
    hours_idx = np.arange(t)
    for i in range(n_plants):
        block = slice(bounds[i], bounds[i + 1])
        rel = np.argmax(pos[block], axis=0)
        mech_plant[i] = mech[block][rel, hours_idx]
        sel = groups[block] != ""
        nonempty = groups[block][sel]
        if nonempty.size:
            vals, inv = np.unique(nonempty, return_inverse=True)
            claim = np.bincount(inv, weights=weight[block][sel], minlength=vals.size)
            if not claim.any():
                # Every classified row carries zero capacity (a fully derated
                # or retired site): capacity cannot discriminate, so this ONE
                # plant falls back to the row-count vote rather than to the
                # alphabetically-first label ``argmax`` would otherwise pick.
                claim = np.bincount(inv, minlength=vals.size).astype(float)
            # ``vals`` is sorted and ``argmax`` takes the FIRST maximum, so the
            # tie-break is the same deterministic rule the row-count vote used.
            group_plant[i] = str(vals[claim.argmax()])
        else:
            group_plant[i] = ""
        label_code[i] = vocab.setdefault(group_plant[i], len(vocab))
        # Floor class, maximum-composition (FloorClassMatrix): the class of
        # the SAME max-contributing unit the mechanism is taken from; empty
        # unit groups impute to the plant majority (the #1488 rule).
        eff = np.where(groups[block] == "", group_plant[i], groups[block])
        codes_block = np.array(
            [vocab.setdefault(str(g), len(vocab)) for g in eff], dtype=np.int16
        )
        fcode[i] = codes_block[rel]
    mech_plant[floor_sum <= 0.0] = 0
    fcode = np.where(floor_sum <= 0.0, label_code[:, None], fcode)
    keys = [str(int(p)) for p in pc[starts]]

    dropped = ~keep
    if dropped.any():
        pos_d = np.clip(np.asarray(arrays["min_gen"], dtype=float)[dropped], 0.0, None)
        floored = pos_d.max(axis=1) > D2_FLOOR_MIN_MW
        if floored.any():
            uids = np.asarray(arrays["unit_ids"]).astype(str)[dropped][floored]
            groups_d = np.asarray(arrays["plant_group"]).astype(str)[dropped][floored]
            mech_d = np.asarray(arrays["mechanism"])[dropped][floored].copy()
            pos_f = pos_d[floored]
            mech_d[pos_f <= 0.0] = 0
            keys += [PSEUDO_PLANT_KEY_PREFIX + u for u in uids]
            floor_sum = np.vstack([floor_sum, pos_f])
            mech_plant = np.vstack([mech_plant, mech_d])
            group_plant = np.concatenate([group_plant, groups_d.astype(object)])
            # A pseudo-unit row IS one unit: its floor class is its own group.
            codes_d = np.array(
                [vocab.setdefault(str(g), len(vocab)) for g in groups_d],
                dtype=np.int16,
            )
            fcode = np.vstack([fcode, np.repeat(codes_d[:, None], t, axis=1)])
    names = tuple(sorted(vocab, key=vocab.get))
    return (
        np.array(keys, dtype=object),
        floor_sum,
        mech_plant,
        group_plant.astype(str),
        FloorClassMatrix(codes=fcode, names=names),
    )


# ---------------------------------------------------------------------------
# Report / CLI
# ---------------------------------------------------------------------------


def _md_table(rows: list[dict]) -> str:
    """Render a list of dicts as a GitHub-flavored markdown table."""
    if not rows:
        return "_no rows_\n"
    cols = list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out) + "\n"


# Short ids for the machine artifact / rubric wiring: GateResult.name prefix
# -> key. The rubric's C7 reads D1; C8 reads D2's per-class summary.
_JSON_KEYS = {
    "D-10": "D10",  # checked before "D-1" (a prefix of "D-10") below
    "D-1": "D1",
    "D-2": "D2",
    "D-4": "D4",
    "D-5": "D5",
    "D-9": "D9",
}


def build_json_report(
    results: list[GateResult], bundle: str, iso: str, years: list[int]
) -> dict:
    """Assemble the machine-readable diagnostics artifact for a bundle.

    This is the committed contract the calibration rubric's C7 (diurnal
    shape, D-1) and C8 (forced-energy share, D-2) criteria score from:
    ``scripts/calibration_verdict.py`` reads ``<bundle>/
    legitimacy_diagnostics.json`` — it never recomputes the diagnostics, so
    the S1 suite stays the single implementation. Gate thresholds are
    embedded so the verdict re-states, never re-types, them.
    """
    diagnostics = {}
    for res in results:
        key = next(
            (v for k, v in _JSON_KEYS.items() if res.name.startswith(k)), res.name
        )
        diagnostics[key] = {
            "name": res.name,
            "passed": res.passed,
            "rows": res.rows,
            "summary": res.summary,
            "failures": res.failures,
            "notes": res.notes,
        }
    return {
        "schema": "legitimacy-diagnostics/v1",
        "bundle": bundle,
        "iso": iso,
        "years": [int(y) for y in years],
        # nyiso-233: the weight that decided each year's D-2 plant-class vote.
        # Absent years ran no D-2. A "row_count_fallback" entry marks a year
        # whose class denominators carry the superseded tranche-count basis.
        "plant_class_vote_basis": {
            str(y): _plant_class_vote_basis[int(y)]
            for y in years
            if int(y) in _plant_class_vote_basis
        },
        # nyiso-242: which dispatch source produced each year's per-plant rows.
        # Absent years built no per-plant matrices. See _dispatch_source_basis.
        "dispatch_source": {
            str(y): _dispatch_source_basis[int(y)]
            for y in years
            if int(y) in _dispatch_source_basis
        },
        "diagnostics": diagnostics,
        "gates": {
            "d1_min_profile_r": D1_MIN_PROFILE_R,
            "d1_min_cv_ratio": D1_MIN_CV_RATIO,
            "d1_offpeak_last_hour": D1_OFFPEAK_LAST_HOUR,
            "d1_gated_classes": list(D1_GATED_CLASSES),
            "d2_peaker_max_share": D2_PEAKER_MAX_SHARE,
            "d2_merchant_max_share": D2_MERCHANT_MAX_SHARE,
            "d2_exempt_classes": list(D2_EXEMPT_CLASSES),
            "d4_max_offwindow_share": D4_MAX_OFFWINDOW_SHARE,
        },
    }


def render_report(
    results: list[GateResult], bundle: str, iso: str, years: list[int]
) -> str:
    """Render the full diagnostic report as markdown."""
    overall = all(r.passed for r in results)
    lines = [
        "# Legitimacy diagnostics report",
        "",
        f"Bundle: `{bundle}` · ISO: {iso} · years: {years}",
        f"Overall: **{'PASS' if overall else 'FAIL'}**",
        "",
        "Diagnostics per `docs/model-legitimacy-audit-2026-07.md` §7; "
        "generated by `scripts/legitimacy_diagnostics.py`.",
        "",
    ]
    for res in results:
        lines.append(f"## {res.name} — {'PASS' if res.passed else 'FAIL'}")
        lines.append("")
        if res.failures:
            lines.append("**Gate failures:**")
            lines.extend(f"- {f}" for f in res.failures)
            lines.append("")
        if res.notes:
            lines.extend(f"_{n}_" for n in res.notes)
            lines.append("")
        if res.summary:
            lines.append("**Per-class gate summary:**")
            lines.append("")
            lines.append(_md_table(res.summary))
        lines.append(_md_table(res.rows))
    return "\n".join(lines)


def diagnose_bundle(
    bundle: Path,
    iso: str,
    years: list[int] | None,
    repo_root: Path = REPO_ROOT,
    rebuild_floors: bool = False,
    only: set[str] | None = None,
) -> list[GateResult]:
    """Run the requested diagnostics against one calibration bundle."""
    run_config = json.loads((bundle / "run_config.json").read_text())
    meta_path = bundle / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    cfg = {
        **run_config.get("calibration_flags", {}),
        **run_config.get("scenario_config", {}),
    }
    if years is None:
        years = meta.get("years") or run_config.get("calibration_flags", {}).get(
            "years", []
        )
    only = only or {"D1", "D2", "D4", "D5", "D9", "D10"}
    sidecar = find_registry_sidecar(repo_root, bundle)
    results: list[GateResult] = []

    d1 = GateResult("D-1 diurnal shape")
    d2 = GateResult("D-2 forced-energy attribution")
    d4 = GateResult("D-4 off-window binding")
    # D-4 VINTAGE GUARD (nyiso-150; queue item nyiso-145 §3). ``ct_only``
    # marks a plant whose CAMPD hourly series is structurally incomplete
    # (EIA-923 net > 1.1× CAMPD gross, so the benchmark scores it on EIA-923
    # monthly) — a metering-CONFIGURATION character of the plant, not a year
    # property. In a year whose EIA-923 vintage is preliminary the ratio's
    # e_ann falls back to c_ann and computes exactly 1.00, silently
    # un-flagging the plant: NYISO plant 7314 was convicted by the per-unit
    # conduct rider in 2025 alone — the one year whose vintage cannot
    # evaluate the flag — and skipped in both complete years. C1 already
    # guards this vintage by name; the rider now does too, by UNION-ing the
    # flag across the scored span. Protective direction only: the union can
    # only ever SKIP a conviction, never create one (measured on NYISO
    # 2023–2025: ten plants lose the flag in 2025, zero gain it).
    ct_only_span = ct_only_span_union(repo_root, iso, years) if "D4" in only else set()
    for year in years:
        # Bench (per-plant nameplate + class) is needed by D-2/D-4 too, not
        # just D-1: it supplies each plant's ``npl`` for the payload dispatch
        # decode (``_decode_cf_bytes`` rescales to the annual total, falling
        # back to ``raw/100 * npl`` when a plant has no ``m_ann``) and for the
        # at-floor tolerance in ``at_floor_mask``. Loading it only for D-1 made
        # the D-2 recompute path (``only={"D2"}``) silently use a degraded
        # ``npl`` (``disp.max()`` / 0.0) and so disagree with the full
        # ``--bundle`` run that writes the committed artifact — the exact
        # path-divergence G-06 exists to catch (#1488).
        bench = load_bench(repo_root, iso, year) if {"D1", "D2", "D4"} & only else {}
        frame, pass_label = (
            load_dispatch_parquet(bundle, year)
            if {"D1", "D2", "D4"} & only
            else (None, None)
        )
        # ``model_plants`` is keyed LIKE THE BENCH (bare plant codes plus
        # "<code>:<KLASS>" slices for multi-class plants) and feeds D-1's
        # per-key pairing; ``model_plants_plant`` is the bare plant-level view
        # D-2/D-4 consume (floors are per plant).
        model_plants: dict[str, np.ndarray] = {}
        model_plants_plant: dict[str, np.ndarray] = {}
        # Names the resolved dispatch source for the pjm-149 coverage note, so
        # a reader of the artifact can see WHICH source a floor-substituted row
        # was missing from.
        dispatch_source: str | None = None
        if frame is not None:
            sub = frame[frame["plant_code"] > 0]
            wide = (
                sub.groupby(["plant_code", "hour"], observed=True)["mw"]
                .sum()
                .unstack("hour", fill_value=0.0)
            )
            model_plants_plant = {
                str(int(pc)): wide.loc[pc].to_numpy(dtype=float) for pc in wide.index
            }
            model_plants = dict(model_plants_plant)
            slice_keys = [k for k in bench if bm.KEY_SEP in k]
            if slice_keys:
                # The bench slices classes POST the OTHER_FOSSIL scoring
                # relabel (render_calibration_html applies it before
                # grouping), so mirror it here before slicing the frame.
                from market_sim.data.fleet import apply_other_fossil_scoring

                sub_k = apply_other_fossil_scoring(
                    sub, int(year), plant_col="plant_code"
                )
                widek = sub_k.groupby(["plant_code", "klass", "hour"], observed=True)[
                    "mw"
                ].sum()
                for key in slice_keys:
                    code, kl = bm.parse_key(key)
                    try:
                        series = widek.loc[(code, kl)]
                    except KeyError:
                        continue
                    model_plants[key] = series.reindex(
                        range(8760), fill_value=0.0
                    ).to_numpy(dtype=float)
            dispatch_source = f"dispatch/{year}_{pass_label}.parquet"
            _dispatch_source_basis[int(year)] = dispatch_source
            logger.info(
                "%s %s: model dispatch from dispatch/%s_%s.parquet (%d plants)",
                iso,
                year,
                year,
                pass_label,
                len(model_plants_plant),
            )
        elif sidecar is not None and {"D1", "D2", "D4"} & only:
            model_plants = load_payload_plants(repo_root, sidecar, year, bench)
            model_plants_plant = aggregate_model_plants(model_plants)
            dispatch_source = f"run payload {sidecar['file']}"
            _dispatch_source_basis[int(year)] = dispatch_source
            logger.info(
                "%s %s: model dispatch from run payload %s (%d plants)",
                iso,
                year,
                sidecar["file"],
                len(model_plants_plant),
            )
        bench_pl = bench_plant_view(bench) if bench else {}
        if ct_only_span:
            extended = sorted(
                p
                for p in (ct_only_span & bench_pl.keys())
                if not bench_pl[p].get("ct_only")
            )
            if extended:
                d4.notes.append(
                    f"{year}: ct_only vintage guard extended the flag from "
                    f"sibling-year vintages for {len(extended)} plant(s): "
                    + ", ".join(extended)
                )
            for p in ct_only_span & bench_pl.keys():
                bench_pl[p]["ct_only"] = True

        if "D1" in only and model_plants and bench:
            model_by_class: dict[str, np.ndarray] = {}
            actual_by_class: dict[str, np.ndarray] = {}
            for pid, b in bench.items():
                if pid not in model_plants:
                    continue
                k = b["group"]
                model_by_class.setdefault(k, np.zeros(8760))
                actual_by_class.setdefault(k, np.zeros(8760))
                model_by_class[k] += model_plants[pid][:8760]
                actual_by_class[k] += b["mw"][:8760]
            sub_res = run_d1(model_by_class, actual_by_class, year=year)
            d1.rows.extend(sub_res.rows)
            d1.failures.extend(sub_res.failures)

        if {"D2", "D4"} & only and model_plants_plant:
            arrays, ra_missing = load_or_rebuild_floors(
                bundle, iso, year, force_rebuild=rebuild_floors
            )
            _plant_class_vote_basis[int(year)] = (
                PLANT_CLASS_VOTE_CAPACITY
                if arrays.get("pmax") is not None
                else PLANT_CLASS_VOTE_ROW_COUNT
            )
            pids, floor_sum, mech_plant, groups, floor_klass = (
                aggregate_floors_by_plant(arrays)
            )
            pid_strs = [str(p) for p in pids]
            klass_by_pid = dict(zip(pid_strs, groups))
            # The D-2/D-4 row set and the floor-energy convention for rows the
            # dispatch source does not cover both live in build_plant_matrices
            # (pjm-149 §3.1/§3.2) — a pure function so the path behaviour is
            # unit-testable without a bundle.
            mats = build_plant_matrices(
                model_plants_plant,
                pid_strs,
                floor_sum,
                mech_plant,
                groups,
                bench_pl,
                floor_klass=floor_klass,
            )
            all_pids = mats.pids
            disp, floors, mechs = mats.disp, mats.floors, mats.mechs
            klass, npl = mats.klass, mats.npl
            t = disp.shape[1]
            if mats.substituted_pseudo:
                # caiso-151 §F / caiso-155: plant_code <= 0 interchange
                # tranches have no dispatch series on ANY path (the payload is
                # CAMPD-keyed by construction; the parquet filter is
                # plant_code > 0), so the convention is path-independent for
                # them. The true at-floor dispatch stays a probe-level
                # statistic on unaggregated LP rows (caiso-151 §F measured
                # 15.47 of 22.68 TWh for CAISO 2024 — a DIFFERENT, narrower
                # statistic than the 22.68 reported here).
                pseudo_note = (
                    f"{year}: {len(mats.substituted_pseudo)} floored "
                    "pseudo-unit row(s) (plant_code <= 0 interchange tranches) "
                    "scored under the floor-energy convention "
                    "(dispatch := min_gen; PREREG-caiso155 §3) — reported TWh "
                    "is the mandated floor energy, an upper bound on at-floor "
                    "dispatch: " + ", ".join(sorted(mats.substituted_pseudo))
                )
                d2.notes.append(pseudo_note)
                d4.notes.append(pseudo_note)
            if mats.substituted_plants:
                # pjm-149: REAL plants the active dispatch source does not
                # cover. Unlike the pseudo-unit family this IS path-sensitive
                # — the same plant carries true dispatch when
                # dispatch/<year>_<pass>.parquet exists — so the note names the
                # source, and every affected class's summary row is stamped
                # upper_bound below.
                by_klass: dict[str, int] = {}
                for p in mats.substituted_plants:
                    k = klass_by_pid.get(p, "") or "(unclassified)"
                    by_klass[k] = by_klass.get(k, 0) + 1
                plant_note = (
                    f"{year}: {len(mats.substituted_plants)} floored plant(s) "
                    f"carry NO dispatch series in the active source "
                    f"({dispatch_source or 'unknown'}) and are scored under the "
                    "floor-energy convention (dispatch := min_gen; "
                    "PREREG-pjm149 §3.2) — their forced TWh is the MANDATED "
                    "floor energy and every affected class's forced_share is an "
                    "UPPER BOUND, sound on a pass and indeterminate on a fail. "
                    "By class: "
                    + ", ".join(f"{k} x{n}" for k, n in sorted(by_klass.items()))
                    + ". Plants: "
                    + ", ".join(sorted(mats.substituted_plants))
                )
                d2.notes.append(plant_note)
                d4.notes.append(plant_note)
            if "D2" in only:
                # Prefer the registered payload (the scorer's own basis); fall
                # back to the bundle's own committed system sidecar so the
                # rule-20 materiality guard is populated at SOLVE TIME too,
                # when no registry sidecar exists yet (nyiso-242).
                total_load_mwh = (
                    load_payload_total_load_mwh(repo_root, sidecar, year)
                    if sidecar is not None
                    else None
                )
                if not total_load_mwh:
                    total_load_mwh = load_bundle_total_load_mwh(bundle, year)
                # Actual (CAMPD) annual MWh per class over the SAME plant set as
                # the model denominator — feeds the max(model, actual)
                # materiality guard so a forcing floor can't push a class under
                # the line and a zeroed material class stays scored.
                actual_by_class: dict[str, float] = {}
                for p in all_pids:
                    b = bench_pl.get(p)
                    if b is None:
                        continue
                    k = klass_by_pid.get(p, "")
                    actual_by_class[k] = actual_by_class.get(k, 0.0) + float(
                        np.asarray(b["mw"][:t], dtype=float).sum()
                    )
                sub_res = run_d2(
                    disp,
                    floors,
                    mechs,
                    klass,
                    year=year,
                    npl=npl,
                    ra_floor_missing=ra_missing,
                    total_load_mwh=total_load_mwh,
                    actual_by_class=actual_by_class,
                    dispatch_substituted=mats.substituted,
                    floor_klass=mats.floor_klass,
                )
                d2.rows.extend(sub_res.rows)
                d2.failures.extend(sub_res.failures)
                d2.notes.extend(sub_res.notes)
                d2.summary.extend(sub_res.summary)
            if "D4" in only:
                sub_res = run_d4(
                    disp,
                    floors,
                    mechs,
                    klass,
                    year=year,
                    npl=npl,
                    # Per-ISO window declarations (miso-230): a mechanism whose
                    # driver-justified hours are DERIVED from the ISO's own
                    # measured conduct is scored against that ISO's derivation,
                    # never another market's (rule 25 [R-ISO-SCOPE]). An ISO with
                    # no override gets D4_WINDOWS unchanged.
                    windows=resolve_d4_windows(iso),
                    pids=all_pids,
                    bench_pl=bench_pl,
                    substituted=mats.substituted,
                    floor_klass=mats.floor_klass,
                )
                d4.rows.extend(sub_res.rows)
                d4.failures.extend(sub_res.failures)
                d4.notes.extend(sub_res.notes)

    if "D1" in only:
        results.append(d1)
    if "D2" in only:
        results.append(d2)
    if "D4" in only:
        results.append(d4)
    if "D5" in only:
        backcast_src = (repo_root / "scripts/run_calibration.py").read_text()
        forecast_src = (repo_root / "src/market_sim/runner.py").read_text()
        results.append(run_d5(cfg, iso, backcast_src, forecast_src))
    if "D9" in only:
        results.append(run_d9(run_config, iso, label=bundle.name))
    if "D10" in only and years:
        results.append(run_d10(iso, list(years)))
    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bundle", type=Path, help="calibration bundle dir")
    parser.add_argument("--iso", help="ISO id (ERCOT/CAISO/PJM/MISO/NYISO/NEISO)")
    parser.add_argument("--years", type=int, nargs="*", default=None)
    parser.add_argument(
        "--only",
        nargs="*",
        choices=["D1", "D2", "D4", "D5", "D9", "D10"],
        default=None,
        help="run a subset of the diagnostics",
    )
    parser.add_argument(
        "--rebuild-floors",
        action="store_true",
        help="force floor reconstruction even when floors/*.npz exists",
    )
    parser.add_argument(
        "--keepers",
        action="store_true",
        help="run the D-9 quarantine, D-6 holdout quarantine, and the D-2 "
        "recompute-vs-committed staleness check across every keeper bundle "
        "(CI mode)",
    )
    parser.add_argument(
        "--no-d2-recompute",
        action="store_true",
        help="in --keepers mode, skip the D-2 recompute-vs-committed staleness "
        "check. That check rebuilds per-plant floors via run_year (needs each "
        "keeper's fetched raw inputs, uncommitted, and minutes of compute), so "
        "it is unfit for the fast hermetic per-PR CI gate — the D-9 overlay + "
        "D-6 holdout quarantines (the rule-22 enforcement) still run. Run the "
        "full --keepers (D-2 included) locally / in a data-provisioned tier.",
    )
    parser.add_argument("--report", type=Path, help="write a markdown report")
    parser.add_argument(
        "--json-out",
        type=Path,
        help="write the machine-readable diagnostics artifact (the committed "
        "rubric contract for C7/C8 is <bundle>/legitimacy_diagnostics.json)",
    )
    args = parser.parse_args(argv)

    results: list[GateResult] = []
    bundle_label, iso, years = "-", args.iso or "-", args.years or []
    if args.keepers:
        results.append(run_d9_keepers(REPO_ROOT))
        if not args.no_d2_recompute:
            results.append(run_d2_keepers_verify(REPO_ROOT))
        bundle_label = "all keepers"
    if args.bundle:
        if not args.iso:
            parser.error("--iso is required with --bundle")
        bundle = args.bundle.resolve()
        results.extend(
            diagnose_bundle(
                bundle,
                args.iso,
                args.years,
                rebuild_floors=args.rebuild_floors,
                only=set(args.only) if args.only else None,
            )
        )
        bundle_label = str(bundle)
        if not years:
            meta_path = bundle / "meta.json"
            if meta_path.exists():
                years = json.loads(meta_path.read_text()).get("years", [])
    if not results:
        parser.error("nothing to do: pass --bundle/--iso and/or --keepers")

    report = render_report(results, bundle_label, iso, years)
    print(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
        logger.info("report written to %s", args.report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(build_json_report(results, bundle_label, iso, years), indent=1)
            + "\n"
        )
        logger.info("machine artifact written to %s", args.json_out)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
