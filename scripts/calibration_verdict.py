"""Reproducible calibration determination for an ISO backcast keeper.

Implements ``docs/calibration-determination-rubric.md`` (RUBRIC v2, the
2026-07-06 fitness-for-purpose re-anchor): reads a run's COMMITTED artifacts
only — the registry sidecar, the run payload, the per-(ISO, year) benchmark
parts, the committed actual-tail part (``tail/actual_tail.json``), the bundle
config, the bundle's calibration attestation, and the bundle's
legitimacy-diagnostics artifact (``legitimacy_diagnostics.json``, written by
``scripts/legitimacy_diagnostics.py --json-out``, scored as C7 diurnal shape
and C8 forced-energy share) — and emits a ``PASS`` / ``CAVEAT`` / ``FAIL`` per
criterion plus one overall determination in
``{CALIBRATED, CALIBRATED-WITH-CAVEATS, NOT-YET}``. Criteria are tiered
(load-bearing / supporting / protective) against the §0 statement of intended
use; graded load-bearing criteria are two-band scored (target band ->
commercial-grade band, each anchored to a published external benchmark —
``docs/rubric-v2-benchmark-memo-2026-07.md``). It never re-solves the LP and
never touches the gitignored ``dispatch``/``system`` parquets, so re-running it
on any keeper reproduces the verdict byte-for-byte.

The generation-mix criteria (C1/C2/C4) score the grid-delivered basis (grid LP
dispatch, no behind-the-meter CHP add-back) against EIA-923 minus the per-class
BTM host supply (``classFull``) and EIA-930 grid totals — model-grid vs
actual-grid, the same numbers the dashboard renders
(``scripts/render_calibration_html.py``). C5a (system CO2) is the exception
(rubric v2.3, owner amendment 2026-07-09): the eGRID/CAMPD rates anchoring the
actual count each cogen's FULL net generation (host + grid), so both sides of
the CO2 comparison carry the measured BTM CHP host supply added back — the
payload's ``co2`` blocks are already on that full-plant basis.

Stdlib-only (json, gzip, base64, re, math) so it runs anywhere the committed
artifacts are checked out, with no pandas / numpy / model import.

Usage:
    python scripts/calibration_verdict.py results/calibration/<name>
    python scripts/calibration_verdict.py --run-id <id>
    python scripts/calibration_verdict.py --json results/calibration/<name>
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "frontend" / "data" / "backcast"
REGISTRY_DIR = DATA_DIR / "registry"
RUNS_DIR = DATA_DIR / "runs"
BENCH_DIR = DATA_DIR / "bench"
# Per-year EIA-923 completeness parts (scripts/audit_eia923_completeness.py): the
# committed source of truth for which (ISO, class) actuals are complete enough to
# gate in a preliminary-vintage year. Stdlib-readable so this scorer stays
# pandas/numpy-free.
COMPLETENESS_DIR = DATA_DIR / "completeness"

# Rubric version implemented by this scorer (rubric §0/§1/§9; v2 = the
# 2026-07-06 fitness-for-purpose re-anchor: criterion tiers, two-band
# target/commercial tolerances, DA-expressible C3c; v2.1 = the same-day owner
# amendments: C7/C8 materiality floor + C8 peaker cap 15%; v2.2 = the 2026-07-07
# owner amendment: C8 grounded-above-budget escalation — an over-cap class passes
# clean iff it clears D-4 provenance + D-1 shape, surfaced as a note; v2.3 = the
# 2026-07-09 owner amendments: C3a/C3b target bands set to the commercial values
# (±10% mean LMP / 0.20 NRMSE pass clean, no caveat band), and C5a re-based to
# the full-plant CHP-inclusive CO2 basis — the measured BTM CHP host supply is
# added back onto BOTH sides before the comparison, because the eGRID/CAMPD
# rates that anchor the actual count each cogen's full net generation;
# v2.4 = the 2026-07-09 owner amendment (second): C3a/C3b score on the
# LIKE-FOR-LIKE load-weighted actual (``rt_lw``/``da_lw`` bench fields —
# the committed hourly actual weighted by the same measured demand the
# model dispatches, zone-resolved where a zonal archive exists) instead of
# the legacy equal-hour hub mean. The legacy basis mixed a demand-weighted
# model mean with an equal-hour actual, a wedge that grows with tail
# realism — a byte-perfect ERCOT 2023 model scores +33.5% against its own
# actual on the old basis (docs/rubric-v24-price-basis-memo-2026-07.md,
# docs/handoffs/ercot-ordc-capdual-adder-2026-07.md §4). ISO-years without
# lw fields fall back to the legacy basis with an explicit label);
# v2.5 = the 2026-07-13 owner amendment: C2 gates ONLY fully-reported
# EIA-923 families — EIA-923 is the C2 source of truth, and a
# preliminary-vintage family (incomplete 923 booking, e.g. every ISO's
# 2025) is NOT gated against any fallback basis (the G-21b 930-derived
# family total or the CAISO CEMS anchor): those rows print as SKIPPED
# diagnostics and re-gate when the final vintage lands. Mirrors C1's
# incomplete-class skip — an incomplete benchmark can fabricate a miss in
# either direction, so it is evidence, not a gate;
# v2.6 = the 2026-07-16 owner amendments (session-logged, ERCOT-73 session):
# (a) C3c gates per-ISO on TAIL_BASIS — ERCOT moves to the RT hourly tail
# (the DA count becomes its report-only diagnostic; every other ISO stays
# DA-gated): ERCOT's DA tail runs ABOVE RT (2023: 311 vs 181 h) and the
# excess is the day-ahead forecast-risk premium, out of representation for
# a realized-weather backcast — see the TAIL_BASIS block comment; (b) C5c
# scores only OBSERVED months — the bench builder emits null (never 0.0)
# for months with no EIA-930 storage observation (pre-breakout months, e.g.
# ERCO battery before Oct-2024), and the existing null-month skip rule then
# holds the year out instead of correlating against fabricated zeros.
RUBRIC_VERSION = 2.6

# Statuses (per criterion-year and aggregated).
PASS, CAVEAT, FAIL, SKIPPED = "PASS", "CAVEAT", "FAIL", "SKIPPED"
# Failure classifications (rubric §1). A CAVEAT is one of:
#  - MEASURED_LIMIT: an out-of-tolerance criterion reclassified by an explicit
#    exceptions-ledger entry (the actual is the limitation) — BUDGETED.
#  - COMMERCIAL_BAND: inside the evidence-anchored commercial-grade outer band
#    but outside our stricter target band — auto-recorded, listed, NOT budgeted
#    (the certification claim of CALIBRATED-WITH-CAVEATS is exactly
#    "commercial-grade or better on every load-bearing criterion").
MODEL_MISS = "MODEL MISS"
MEASURED_LIMIT = "ACCEPTED MEASURED-INPUT LIMITATION"
COMMERCIAL_BAND = "WITHIN COMMERCIAL BAND (TARGET MISS)"
# Overall determinations.
CALIBRATED = "CALIBRATED"
CALIBRATED_CAVEATS = "CALIBRATED-WITH-CAVEATS"
NOT_YET = "NOT-YET"

# Criterion tiers (rubric §0 statement of intended use → §1 triage):
#  - load-bearing: certifies the intended uses directly (annual/monthly price
#    level & shape, generation mix by class, system CO2). Two-band scored where
#    a published commercial comparable exists.
#  - supporting: informative sub-annual dynamics (hourly correlation, storage
#    cycling, scarcity-tail counts) — single wide band; a gross breach still
#    FAILs, a documented data limitation may be ledgered.
#  - protective: the anti-self-deception gates (C6 governance, C7 diurnal
#    shape, C8 forced share). UNCHANGED from rubric v1 in logic, thresholds
#    and ledger behavior (CLAUDE.md rules 13/14/17-22).
TIER_LOAD, TIER_SUPPORT, TIER_PROTECT = "load-bearing", "supporting", "protective"

# --- fuel-family class membership (plant_taxonomy.classes_for_fuel930 roll-up) --
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL")
# Classes excluded from the per-class fuel-mix gate (C1), each justified in the
# rubric: CT_CHP is a BTM peaker the grid LP zeroes by construction; OTHER /
# OTHER_FOSSIL are the mixed-plant reconciliation bucket, not merit-order classes.
FUELMIX_EXCLUDED = frozenset({"CT_CHP", "OTHER", "OTHER_FOSSIL"})

# --- tolerances (rubric §1) -------------------------------------------------
# C1 fuel-mix — the universal class gate (mirrors classInTol in the run
# explorer, docs/codebase-site/backcast-runs.html; supersedes the old ±5%/±1 TWh
# size-tiered band): a class passes iff BOTH (a) its grid-delivered volume miss
# |model−actual| is within min(2.0% of ISO total load, 8 TWh), AND (b) its
# share of total generation is within 3.0 percentage points of the actual share.
# The volume band scales with system size (≈2 pp of load) but is capped at an
# absolute 8 TWh so it can't balloon on large ISOs (2% of an 800 TWh system would
# be 16 TWh, letting a small class drift far on the margin). Applied uniformly
# across classes and ISOs; the share band stops a class passing on volume alone
# while still misrepresenting the mix. Using total LOAD (= gen + net imports)
# rather than generation so net-importing ISOs get the correct ≈2 pp band; for
# energy-only ISOs with no interchange, load = gen and the band is unchanged.
# 2026-07-02 rubric re-balance (docs/calibration-determination-rubric.md §1):
# loosened from 1.0%/5 TWh/1.5 pp — the old bands failed keepers on ±1–2 TWh
# small-class residuals that are TWh noise, not a structural miss, while a
# genuine structural miss (e.g. MISO CC_REGULAR +47 TWh / +7.7 pp) still FAILs
# the new bands by a wide margin. Paired with a TIGHTER C3 (price) gate below.
FUELMIX_VOL_LOAD_FRAC = 0.02  # volume band = 2.0% of ISO total load ...
FUELMIX_VOL_CAP_TWH = 8.0  # ... but never more than an absolute 8 TWh
FUELMIX_SHARE_PP = 3.0  # +/-3.0 share percentage points of total generation
# Non-fossil fuels whose grid actual comes from EIA-930 (not 923) for the
# system-total used by the share/volume bands (matches totalGen in the run
# explorer, docs/codebase-site/backcast-runs.html).
NONFOSSIL_FUELS = ("nuclear", "wind", "solar")

# D-10 free-class rescore (audit §7 D-10 / §4 L-rows): the per-ISO set of C1
# classes whose actual is a MEASURED REALIZATION the model is pinned to — so a C1
# pass there scores plumbing, not skill. Declared from the audit L-rows, not
# inferred (mirrors the D-5 overlay registry pattern):
#   L1 wind/solar (delivered-CF upper bound), L3 nuclear (measured monthly CF),
#   L6 hydro (monthly budgets) + MISO Manitoba firm imports, L4 CHP (measured
#   export floor), L2 NYISO net imports (measured reconciliation band).
# C1 only scores the fossil gas/coal families, so in practice the free-class
# rescore drops the CHP subclasses (CC_CHP / ST_CHP; CT_CHP is already
# C1-excluded); wind/solar/nuclear/hydro/imports are declared for provenance and
# excluded harmlessly (they are never C1 rows). No gate — the number itself is
# the deliverable (the audit's "pinned-class gate inflation" made visible).
_PINNED_CLASSES_COMMON = frozenset(
    {"wind", "solar", "nuclear", "hydro", "CC_CHP", "CT_CHP", "ST_CHP"}
)
PINNED_CLASSES_BY_ISO: dict[str, frozenset[str]] = {
    "ERCOT": _PINNED_CLASSES_COMMON,
    "CAISO": _PINNED_CLASSES_COMMON,
    "PJM": _PINNED_CLASSES_COMMON,
    "MISO": _PINNED_CLASSES_COMMON | {"imports"},  # L6 Manitoba firm-hydro block
    "NYISO": _PINNED_CLASSES_COMMON | {"imports"},  # L2 net-interchange band
    "NEISO": _PINNED_CLASSES_COMMON,
}

SYSVOL_TOL = 0.025  # +/-2.5% gas/coal family grid-delivered (target band)
# Commercial-grade outer band for the preliminary-vintage EIA-930 family
# fallback (the only C2 path that applies a percent band): family-level
# generation-by-fuel error of ~5% is the best published comparable (EIA AEO
# retrospective short-horizon generation-by-fuel; ISO planning-study PCM
# benchmarks) and the fallback's own benchmark carries the 923-vs-930
# reconciliation uncertainty. Between 2.5% and 5% -> auto CAVEAT
# (COMMERCIAL_BAND); beyond 5% -> FAIL (ledgerable as before).
SYSVOL_COMMERCIAL = 0.05
SYSVOL_MIN_TWH = 10.0  # below this a family is immaterial: C1's per-class
# absolute band governs it, so the ±2.5% system-volume gate is N/A (e.g. NEISO
# coal ~0.3 TWh — a percent band on a near-zero family is pure noise).
DISP_MIN_TWH = 5.0  # below this a fleet's hourly r/NRMSE is degenerate (NEISO
# coal); the per-class C1 absolute band is the meaningful check, not correlation.
VINTAGE_RECONCILE_FRAC = 0.97  # render_calibration_html._VINTAGE_RECONCILE_FRAC
# ISOs whose EIA-930 "Natural Gas" cell is demonstrably corrupted against two
# independent measured sources, with the CEMS-anchored replacement committed in
# the bench part by render_calibration_html (owner-signed rework 2026-07-12;
# results/calibration/FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §5).
# CAISO: from ~2024-05 the CISO NG cell carries a growing noon-peaked,
# solar-shaped block no gas fleet produced (+4.2/+7.9 TWh unexplained in
# 2024/25 vs CEMS + cogens + fold-in). Effects here:
#  * C2 gas family fallback gates against the committed anchor fields
#    (``e930.gas_cems_grid`` + ``e930.gas_cogen_grid``) instead of the 930 cell.
#  * C4 gas hourly r/NRMSE is recomputed from the committed hourly series
#    (payload ``plants[].m`` vs bench ``plants[].campd`` + flat cogen block)
#    from the onset VINTAGE onward; pre-onset years keep the payload's 930-based
#    fit for continuity (the two agree there).
# Mirrors render_calibration_html.EIA930_NG_CELL_CORRUPT / _ONSET; membership
# is CEMS-evidence-gated per ISO, never generic (the other ISOs' NG cells show
# no corruption and keep G-21/G-21b unchanged).
CEMS_GAS_ANCHOR_ISOS: frozenset = frozenset({"CAISO"})
CEMS_GAS_ANCHOR_ONSET = {"CAISO": 2024}  # first contaminated vintage year
PRELIM_923_FROM_YEAR = 2025  # current-year preliminary EIA-923 vintage
# C3 price gates — rubric v2 two-band (2026-07-06 fitness re-anchor), target
# bands re-set by the 2026-07-09 owner amendment (rubric v2.3): the target
# band now COINCIDES with the evidence-anchored commercial-grade band
# (docs/rubric-v2-benchmark-memo-2026-07.md §2), so a run inside ±10% mean /
# 0.20 NRMSE is a clean PASS with no COMMERCIAL_BAND caveat; beyond it ->
# FAIL (ledgerable only as a measured-input limitation). The former stricter
# targets (±5% / 0.15 — the SEM regulator criterion) remain as reported
# magnitudes, not gates: the primary market signal is still price, but a
# caveat between the SEM criterion and the published commercial envelope
# graded honest runs as second-class for a miss no published model avoids.
#   Mean anchor: the SEM/Ireland regulator criterion for its official PLEXOS
#   model is +/-5% aggregate price error with monthly within +/-10% (ECA,
#   SEM-20-004); NYISO's accepted GE MAPS benchmark ran -2% to -17% zonal
#   (Outlook Appendix A); monitors' competitive re-simulations sit 0-4% from
#   actual prices (CAISO DMM / MISO SOM), the market-conduct noise floor.
PRICE_MEAN_TOL = 0.10  # PASS: +/-10% mean LMP (v2.3 owner amendment 2026-07-09)
PRICE_MEAN_COMMERCIAL = 0.10  # coincident outer band (memo §2)
#   Shape anchor: SEM's regulator-accepted backcast carried -9% winter-peak /
#   +11% off-peak period biases; published monthly norms run ~5-15% with
#   correct seasonality. A 12-month NRMSE of 0.20 is the outer edge of that
#   demonstrated band (also the pre-2026-07-02 value, now externally anchored).
PRICE_SHAPE_NRMSE_MAX = 0.20  # PASS: monthly NRMSE (v2.3 owner amendment)
PRICE_SHAPE_NRMSE_COMMERCIAL = 0.20  # coincident outer band (memo §2)
# C3c scarcity tail — v2 scores the hourly-expressible tail (rubric §1 C3c,
# §5) from the committed actual-tail part (frontend/data/backcast/tail/
# actual_tail.json, scripts/derive_actual_tail.py). The gated BASIS is per-ISO
# (TAIL_BASIS below; rubric v2.6 owner amendment 2026-07-16):
#   * default "da" — the DA-expressible tail, the same hourly commitment-aware
#     resolution as the model LP; the RT count is a reported diagnostic
#     (sub-hourly transients are out of representation —
#     miso-scarcity-tail-diagnosis.md §1: MISO 2023's entire 30-hour RT tail
#     is single-interval 5-minute events, DA tail 1 h).
#   * ERCOT "rt" — the RT hourly tail; the DA count is the reported
#     diagnostic. Both C3c actuals are hourly hub averages, but ERCOT's DA
#     tail runs ABOVE its RT tail (2023: 311 vs 181 h) — the excess is the
#     day-ahead weather/load forecast-risk premium, which a realized-weather
#     (perfect-foresight) backcast is out of representation to price: the
#     model cannot "worry" about weather it already knows, the mirror image
#     of the transient argument that keeps RT out of the MISO/PJM gate. The
#     keeper evidence is direct: the ERCOT-71 keeper reads 179 h vs RT 181 h
#     (0.99x) while sitting at 0.58x of the DA count.
# Band restored to [0.5x, 2x] on the scope-consistent benchmark: no commercial
# or public model publishes tail-hour-count accuracy at all, so the band's job
# is order-of-magnitude realism — a collapsed tail (0x) and an invented tail
# (>2x) both still FAIL. Counts below TAIL_SMALL_COUNT hours are scored by
# absolute difference (a ratio on a handful of hours is degenerate).
TAIL_LO, TAIL_HI = 0.5, 2.0  # tail hours within [0.5x, 2x] of the gated actual
TAIL_SMALL_COUNT = 10  # below this, |model-actual| <= TAIL_SMALL_COUNT passes
# Per-ISO C3c gated basis (rubric §5, v2.6 owner amendment 2026-07-16 — see
# the block comment above). Only ERCOT gates on the RT hourly tail; the other
# basis is always emitted as the report-only diagnostic row.
TAIL_BASIS = {"ERCOT": "rt"}  # default: "da"
DISP_R_FLOOR = 0.70  # fleet hourly pearson r floor (gas, coal)
DISP_NRMSE_MAX = 0.30  # fleet hourly NRMSE ceiling (gas, coal)
CO2_TOL = 0.07  # target: +/-7% vs eGRID (mid of the playbook's 5-10%)
# Commercial-grade outer band for system CO2: ~10% is the demonstrated
# public-model grade at short horizons (AEO retrospective energy-CO2 errors;
# eGRID-vs-model comparisons in academic PCM validations — memo §2).
CO2_COMMERCIAL = 0.10
STORAGE_TOL = 0.30  # +/-30% storage throughput (cycling realism)
STORAGE_SHAPE_R_FLOOR = 0.50  # monthly discharge pearson r floor (both sides
# on the positive/discharge basis — see rubric §C5c 2026-07-03 alignment fix)
STORAGE_SHAPE_MIN_CV = 0.25  # C5c degeneracy guard: actual monthly-discharge
# coefficient of variation below this leaves no seasonal shape to correlate
# (a flat TRUE model would score r=0 and fail); the year is SKIPPED and C5b
# scores the volume. Mirrors C4's degenerate-correlation rule.
VRE_TOL = 0.10  # +/-10% advisory band for solar/wind (report-only)

# Per-ISO scarcity-tail definition (rubric §5): (threshold $/MWh).
TAIL_THRESHOLD = {
    "ERCOT": 200.0,
    "PJM": 200.0,
    "MISO": 200.0,
    "CAISO": 200.0,
    "NYISO": 300.0,
    "NEISO": 300.0,
}

# Governance: outage sources that are exogenous availability events (rubric C6.4).
EXOGENOUS_OUTAGE_SOURCES = frozenset({"historic", "statistical"})
# scenario_config flags that, if truthy, indicate a forbidden fitted mechanism
# (output-pinning / price-residual adder). Curated by exact name to avoid false
# positives on legitimate structural terms (e.g. wefor_residual, a renewable
# forecast-error term). Empty today; extend as such a flag is ever introduced.
FORBIDDEN_FLAGS: tuple[str, ...] = ()

# Caveat budgets / quorum (rubric §2, v2). Two DISTINCT caveat kinds:
#  - Auto COMMERCIAL_BAND caveats (inside the evidence-anchored outer band,
#    outside target): UNBUDGETED — they are inside the certification claim by
#    construction; the scorer lists every one with its magnitude.
#  - LEDGERED caveats (beyond the outer band, reclassified by an explicit
#    exceptions-ledger entry as an accepted measured-input limitation):
#    budgeted. Protective criteria (C7/C8) keep the v1 hard budget of 1 —
#    unchanged enforcement of CLAUDE.md rule 20 / audit D-1/D-2. Non-protective
#    ledgered caveats: at most 3. Rationale (memo §3a, replacing the 2026-07-02
#    3->2 cut whose stated concern — price caveated wholesale — is now
#    structurally addressed by the commercial outer band): the recurring
#    documented data-limitation classes are three by construction
#    (preliminary-923 vintage, EIA-930 storage coverage, data-blocked scarcity
#    requirement series), and a budget of 2 mechanically forced NOT-YET on data
#    availability rather than model quality. Each ledgered caveat still
#    requires its own named measured-input reason — the budget bounds excuses,
#    it never grants them.
MAX_PROTECTIVE_CAVEATS = 1  # C7/C8 (C6 is never caveatable) — unchanged from v1
MAX_LEDGERED_CAVEATS = 3  # non-protective ledgered measured-input caveats

# C7/C8 materiality floor (rubric v2.1, owner amendment 2026-07-06): the
# protective shape / forced-share gates score only classes whose annual energy
# — max(model, actual), so a forced floor cannot hide a class below the line
# by its own inflation, and a model that zeroes a material class stays scored
# — is at least this fraction of total ISO load. Smaller classes are emitted
# SKIPPED-immaterial (reported by the D-1/D-2 diagnostics, never gated): a
# trivial class's diurnal r or forced share is not worth structural work
# (mirrors C2's 10 TWh / C4's 5 TWh immateriality cut-offs). 2% is the clean
# cut in the keeper data: NEISO ST_GAS 0.1-0.3%, NEISO CT 0.5-0.7% and NYISO
# CT 1.4-1.9% of load (the named trivial cases) fall below it, while CAISO CT
# 2023/24 (2.1-2.3% — the caiso-42 flat-floor case C7/C8 exist to catch),
# PJM/MISO CT (3.5-4.2%) and every material ST_GAS (2.1-10.6%) stay gated.
PROTECTIVE_MIN_LOAD_FRAC = 0.02
# C8 forced-share caps (rubric v2.1): the peaker cap was raised 0.10 -> 0.15
# by the same owner amendment (CLAUDE.md rule 20 amended in-place); merchant
# cap unchanged. The scorer derives PASS/FAIL from the artifact's MEASURED
# forced_share against these caps — the rubric owns tolerances, the S1
# artifact owns measurement — so committed artifacts written under earlier
# gate values keep scoring correctly without regeneration.
FORCED_SHARE_PEAKER_MAX = 0.15
FORCED_SHARE_MERCHANT_MAX = 0.30
FORCED_SHARE_PEAKER_CLASSES = ("CT_PEAKER",)

# C8 grounded-above-budget escalation (rubric v2.2, owner amendment 2026-07-07).
# The 15%/30% caps and the 2% materiality floor are UNCHANGED — a class within
# the cap still passes cheaply on volume alone. What changes is the treatment of
# a class ABOVE the cap: instead of an automatic FAIL, it escalates to a
# conditional pass on PROVENANCE + SHAPE (the true legitimacy question), because
# a class can legitimately be forced past the budget when the forcing is a real
# grid/RA/AS driver that reproduces the observed dispatch. A class above the cap
# passes iff BOTH:
#   (a) PROVENANCE — every binding *non-exempt* mechanism it is forced by clears
#       D-4 off-window binding (it binds only in its driver-justified window;
#       a mechanism with NO declared D-4 window fails here — rule 12, "no floor
#       without a window"), AND
#   (b) SHAPE — the class's D-1 hour-of-day profile clears the artifact's own
#       gates (profile r >= d1_min_profile_r AND off-peak CV ratio >=
#       d1_min_cv_ratio), applied to ANY escalating class (not only the default
#       D1_GATED_CLASSES) — this is the "shape mismatch means the forcing
#       variables are wrong" test.
# Both signals are already in every committed legitimacy_diagnostics.json
# (D1.rows / D2.rows / D4.rows / gates), so this stays scorer-only — no
# re-solve, no bundle regen — and existing keepers re-score in place. A pass
# here is a CLEAN PASS (owner decision 2026-07-07: surfaced as a report NOTE,
# never a caveat); a fail is classified as a forcing shape/provenance mismatch.
GROUNDED_ABOVE_BUDGET = "GROUNDED ABOVE BUDGET (D-4 window + D-1 shape clear)"
# Mechanism NAMES excluded from the C8 forced-share arithmetic — the union of
# data.floor_mechanisms.D2_EXEMPT_MECHS (structural must-run: nuclear / CHP-steam
# / coal take-or-pay) and NON_THERMAL_MECHS (interchange pseudo-unit boundaries).
# Kept as a local literal so this scorer stays stdlib-only (no market_sim import);
# floor_mechanisms is the source of truth and tests/test_calibration_verdict.py
# asserts this set matches MECH_NAMES for those id sets so it cannot silently
# drift. run_d2 already excludes these from a class's gated forced_share; the
# escalation re-derives the binding *merchant* mechanism set from the same names.
FORCED_EXEMPT_MECH_NAMES = frozenset(
    {
        "nuclear_mustrun",  # MECH_NUCLEAR
        "chp_steam",  # MECH_CHP_STEAM
        "coal_mustrun",  # MECH_COAL_MUSTRUN
        "firm_import",  # MECH_FIRM_IMPORT (non-thermal boundary)
        "nyiso_local_selfsupply",  # MECH_NYISO_SELFSUPPLY (non-thermal boundary)
    }
)

# Criterion id -> (label, tier). The v1 HARD/SOFT split conflated two things —
# strict data gates (C1/C2) and anti-gaming gates (C6/C7/C8); v2 tiers them by
# role in the intended-use certification (rubric §0/§1). Any FAIL on ANY tier
# still forces NOT-YET (unchanged v1 rule).
CRITERIA = {
    "fuelmix": ("C1 fuel-mix by class (grid-delivered)", TIER_LOAD),
    "sysvol": ("C2 system volume (gas/coal families)", TIER_LOAD),
    "price_mean": ("C3a mean LMP", TIER_LOAD),
    "price_shape": ("C3b price duration/shape", TIER_LOAD),
    # v2.6: the gated basis is per-ISO (TAIL_BASIS — ERCOT RT, others DA), so
    # the label is basis-neutral; each scored row's metric names its basis.
    "price_tail": ("C3c price tail / scarcity (hourly-expressible)", TIER_SUPPORT),
    "dispatch_corr": ("C4 fleet hourly dispatch correlation", TIER_SUPPORT),
    "co2": ("C5a CO2 vs eGRID", TIER_LOAD),
    "storage": ("C5b storage throughput", TIER_SUPPORT),
    "storage_shape": ("C5c storage dispatch shape", TIER_SUPPORT),
    "governance": ("C6 governance gate", TIER_PROTECT),
    "shape": ("C7 diurnal shape (D-1)", TIER_PROTECT),
    "forced_share": ("C8 forced-energy share (D-2)", TIER_PROTECT),
}


# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------
def _decode_run_js(text: str) -> dict:
    """Decode a ``runs/<id>.js`` payload (``window.BC.runGz[..]="<b64>"``)."""
    m = re.search(r'=\s*"([A-Za-z0-9+/=]+)"', text)
    if not m:
        raise ValueError("no gzip+base64 payload found in run js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def resolve_run_id(arg: str) -> str:
    """Return the run id for a CLI arg that is either a run id or a bundle dir.

    A run id resolves when its sidecar exists. Otherwise ``arg`` is treated as a
    bundle path and matched against each sidecar's stored ``bundle`` field.
    """
    if (REGISTRY_DIR / f"{arg}.json").exists():
        return arg
    p = Path(arg)
    cand = {arg, p.name, str(p)}
    try:
        cand.add(str(p.resolve().relative_to(REPO)))
    except ValueError:
        pass
    for side in sorted(REGISTRY_DIR.glob("*.json")):
        rec = json.loads(side.read_text())
        if rec.get("bundle") in cand or Path(rec.get("bundle", "")).name == p.name:
            return rec["id"]
    raise SystemExit(
        f"could not resolve a registered run from {arg!r} "
        f"(no registry sidecar and no bundle match)."
    )


def load_artifacts(run_id: str) -> dict:
    """Load every committed artifact the scorer needs for ``run_id``.

    Returns ``{sidecar, payload, bench, config, attestation}``; ``bench`` is
    ``{year: bench_payload}`` and missing pieces are ``None`` so the scorer can
    SKIP rather than crash.
    """
    side_path = REGISTRY_DIR / f"{run_id}.json"
    if not side_path.exists():
        raise SystemExit(f"no registry sidecar for run id {run_id!r}.")
    sidecar = json.loads(side_path.read_text())
    iso = sidecar.get("iso", "ERCOT")

    run_js = RUNS_DIR / f"{run_id}.js"
    payload = _decode_run_js(run_js.read_text()) if run_js.exists() else None

    bench: dict[int, dict] = {}
    for part in sorted((BENCH_DIR / iso).glob("*.json.gz")) if iso else []:
        obj = json.loads(gzip.decompress(part.read_bytes()))
        for y in obj.get("meta", {}).get("years", []):
            bench[int(y)] = obj.get("bench", {})

    bundle_dir = REPO / sidecar["bundle"] if sidecar.get("bundle") else None
    config = None
    attestation = None
    if bundle_dir and bundle_dir.exists():
        rc = bundle_dir / "run_config.json"
        meta = bundle_dir / "meta.json"
        config = {
            "scenario_config": (
                json.loads(rc.read_text()).get("scenario_config", {})
                if rc.exists()
                else {}
            ),
            "meta": json.loads(meta.read_text()) if meta.exists() else {},
        }
        att = bundle_dir / "calibration_attestation.json"
        if att.exists():
            attestation = json.loads(att.read_text())
    legitimacy = None
    if bundle_dir and bundle_dir.exists():
        legit_path = bundle_dir / "legitimacy_diagnostics.json"
        if legit_path.exists():
            legitimacy = json.loads(legit_path.read_text())
    return {
        "sidecar": sidecar,
        "payload": payload,
        "bench": bench,
        "config": config,
        "attestation": attestation,
        "legitimacy": legitimacy,
    }


# ---------------------------------------------------------------------------
# Small numeric helpers (stdlib only)
# ---------------------------------------------------------------------------
def _pct(model: float, actual: float) -> float | None:
    """Signed fractional error ``(model-actual)/actual``; None when undefined."""
    if actual is None or abs(actual) < 1e-9:
        return None
    return (model - actual) / actual


def _wmean(pairs: list[tuple[float, float]]) -> float | None:
    """Demand-weighted mean of ``(value, weight)`` pairs."""
    w = sum(wt for _, wt in pairs)
    if w <= 0:
        return None
    return sum(v * wt for v, wt in pairs) / w


def _nrmse(model: list[float], actual: list[float]) -> float | None:
    """Normalised RMSE of two equal-length monthly vectors (skip None cells)."""
    cells = [(m, a) for m, a in zip(model, actual) if m is not None and a is not None]
    if not cells:
        return None
    mean_a = sum(a for _, a in cells) / len(cells)
    if abs(mean_a) < 1e-9:
        return None
    rmse = math.sqrt(sum((m - a) ** 2 for m, a in cells) / len(cells))
    return rmse / mean_a


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------
def _ledger_match(exceptions: list[dict], criterion: str, year: int, key: str | None):
    """Return the ledger entry matching (criterion, year, class/family) or None.

    ``key`` is the class (fuelmix) or family (sysvol/dispatch_corr); criteria
    without a sub-key match on (criterion, year) alone.
    """
    for e in exceptions or []:
        if e.get("criterion") != criterion or int(e.get("year", -1)) != int(year):
            continue
        ekey = e.get("klass") or e.get("family")
        if key is None or ekey is None or str(ekey) == str(key):
            return e
    return None


def _apply_ledger(rec: dict, exceptions: list[dict]) -> dict:
    """Reclassify an out-of-tolerance result to CAVEAT iff the ledger documents it.

    A FAIL with a matching ledger entry becomes a CAVEAT classified ACCEPTED
    MEASURED-INPUT LIMITATION; a FAIL without one stays a FAIL (MODEL MISS).
    """
    if rec["status"] != FAIL:
        return rec
    entry = _ledger_match(exceptions, rec["criterion"], rec["year"], rec.get("key"))
    if entry:
        rec["status"] = CAVEAT
        rec["classification"] = MEASURED_LIMIT
        rec["ledger_reason"] = entry.get("reason", "")
    return rec


# ---------------------------------------------------------------------------
# EIA-923 completeness map (per-year committed part)
# ---------------------------------------------------------------------------
_COMPLETENESS_CACHE: dict | None = None


def _completeness_map() -> dict:
    """Return ``{year: {iso: {class: record}}}`` from the committed parts.

    Reads every ``completeness/eia923_<year>.json`` produced by
    ``scripts/audit_eia923_completeness.py``. Cached after the first load.
    Returns an empty map when the directory is absent (no preliminary-year
    completeness has been audited yet — every class then falls back to the blanket
    preliminary-vintage skip).
    """
    global _COMPLETENESS_CACHE
    if _COMPLETENESS_CACHE is not None:
        return _COMPLETENESS_CACHE
    out: dict[int, dict] = {}
    if COMPLETENESS_DIR.exists():
        for part in sorted(COMPLETENESS_DIR.glob("eia923_*.json")):
            obj = json.loads(part.read_text())
            out[int(obj["year"])] = obj  # full part: carries isos + families
    _COMPLETENESS_CACHE = out
    return out


def _band_result(err_abs: float, target: float, commercial: float):
    """Two-band scoring (rubric v2 §1): PASS inside the target band; auto
    CAVEAT (``COMMERCIAL_BAND``, listed but not budgeted) between the target
    and the evidence-anchored commercial-grade band; FAIL beyond it
    (ledgerable only as an accepted measured-input limitation)."""
    if err_abs <= target:
        return PASS, None
    if err_abs <= commercial:
        return CAVEAT, COMMERCIAL_BAND
    return FAIL, MODEL_MISS


# ---------------------------------------------------------------------------
# Actual scarcity-tail part (committed, scripts/derive_actual_tail.py)
# ---------------------------------------------------------------------------
TAIL_DIR = DATA_DIR / "tail"
_TAIL_CACHE: dict | None = None


def _tail_part() -> dict:
    """Return the committed actual-tail part (``tail/actual_tail.json``).

    ``{iso: {year(str): {threshold, da_gt, rt_gt, da_coverage, rt_coverage}}}``
    — the C3c DA-expressible benchmark (rubric §1 C3c / §5). Empty when the
    part is absent (C3c then SKIPs, never silently passes).
    """
    global _TAIL_CACHE
    if _TAIL_CACHE is not None:
        return _TAIL_CACHE
    p = TAIL_DIR / "actual_tail.json"
    _TAIL_CACHE = json.loads(p.read_text()).get("isos", {}) if p.exists() else {}
    return _TAIL_CACHE


def class_is_gated(iso: str, klass: str, year: int) -> bool:
    """Whether (iso, class) has a complete-enough 923 actual to gate in ``year``.

    Complete-vintage years (those with no completeness part) always gate — only a
    preliminary vintage with an audited completeness part restricts gating to the
    verified-complete, verified-complete-family classes
    (:func:`audit_eia923_completeness.audit`'s ``gate`` flag).
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True  # complete vintage / no preliminary audit -> gate as usual
    rec = cmap[year].get("isos", {}).get(iso.upper(), {}).get(klass)
    return bool(rec and rec.get("gate"))


def family_is_complete(iso: str, family: str, year: int) -> bool:
    """Whether ``family`` (``gas``/``coal``) is fully reported for (iso, year).

    Complete-vintage years (no completeness part) are always complete — C2 then
    defers to the per-class C1 gate as it always has. A preliminary year defers
    only the families the audit flagged complete; the rest fall back to the
    EIA-930 family aggregate gate.
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True
    return bool(cmap[year].get("families", {}).get(iso.upper(), {}).get(family))


# ---------------------------------------------------------------------------
# Per-criterion scoring (one record per criterion-year, pre-ledger)
# ---------------------------------------------------------------------------
def _gen_totals(ypay: dict, ybench: dict) -> tuple[float, float]:
    """System model/actual TOTAL generation (TWh), grid-delivered.

    Mirrors ``totalGen`` in the run explorer (docs/codebase-site/
    backcast-runs.html) exactly so the verdict's C1 bands match
    the dashboard scorecard. Each benchmarked class is counted ONCE: ``classFull``
    now carries the grid-delivered actual for every class — fossil (EIA-923 − BTM
    CHP), nuclear (EIA-923) and the variable renewables wind/solar on the EIA-930
    grid basis (distribution-connected / net-metered BTM PV removed in
    ``render_calibration_html``, the same source-authority as
    :func:`results.calibration.actuals_source`). actual = Σ ``classFull``; model =
    Σ ``gmModel`` over those same class keys. The earlier ``+ EIA-930
    nuclear/wind/solar`` term double-counted the renewables and re-introduced the
    BTM-inflated EIA-923 solar through ``classFull``, inflating the share
    denominator (NEISO 2023 read a_gen ≈ 128 vs the true grid ≈ 97 TWh).
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    a_gen = sum(float(v) for v in cf.values())
    m_gen = sum(float(gm.get(g, 0.0)) for g in cf)  # over the classFull keys
    return m_gen, a_gen


def _total_load(ypay: dict, a_gen: float) -> float:
    """Total load served (TWh) = sum of zone demand from the LMP payload.

    For ISOs with scheduled interchange folded into demand (NEISO, NYISO, …),
    this equals generation + net imports — the correct denominator for the
    ≈1 pp volume band.  Falls back to ``a_gen`` when zone data is absent.
    """
    lmp = ypay.get("lmp", {})
    if not lmp:
        return a_gen
    return sum(float(z.get("d", 0.0)) for z in lmp.values())


def score_fuelmix(
    year: int, ypay: dict, ybench: dict, iso: str = "ERCOT"
) -> list[dict]:
    """C1 — per-class grid-delivered fuel-mix, the universal gate.

    A class passes iff BOTH its grid-delivered volume miss is within
    min(2.0% of ISO total load, 8 TWh) AND its share of total generation is
    within 3.0 pp of actual (the run explorer's ``classInTol`` on the
    gmModel/classFull basis).

    Gating is restricted to (ISO, class) pairs whose EIA-923 actual is VERIFIED
    COMPLETE for the year. A complete-vintage year (no committed completeness part)
    gates every benchmarked class as before. A PRELIMINARY-EIA-923 year (e.g. 2025
    today) gates only the classes the completeness audit
    (:mod:`scripts.audit_eia923_completeness`) flagged ``gate`` — a class whose own
    plants ALL reported AND whose whole fossil family reported (so the
    vintage-reconcile leaves its per-class actual un-scaled). Every other class is
    emitted SKIPPED (recorded, never a silent pass): its plant data is incomplete,
    so there is no trustworthy per-class actual to gate against. The C2 family
    system-volume gate still covers the skipped classes via the authoritative
    EIA-930 grid reconcile. The map auto-extends as a year's 923 finalises: re-run
    the audit and the now-complete classes begin gating with no code change.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)
    out = []
    classes = [c for c in (*GAS_CLASSES, *COAL_CLASSES) if c not in FUELMIX_EXCLUDED]
    cmap_year = _completeness_map().get(year, {}).get("isos", {}).get(iso.upper(), {})
    for c in classes:
        a = cf.get(c)
        if a is None:
            continue  # class not benchmarked for this ISO-year
        a = float(a)
        m = float(gm.get(c, 0.0))
        d = m - a
        if m_gen > 0 and a_gen > 0:
            share_pp = 100.0 * m / m_gen - 100.0 * a / a_gen
        else:
            share_pp = None
        if not class_is_gated(iso, c, year):
            comp = cmap_year.get(c, {})
            why = comp.get("status", "incomplete")
            reasons = "; ".join(comp.get("reasons", [])) or "no per-class actual"
            rec = {
                "criterion": "fuelmix",
                "key": c,
                "year": year,
                "status": SKIPPED,
                "classification": None,
                "metric": f"{c} grid-delivered TWh + share of generation",
                "model": round(m, 3),
                "actual": round(a, 3),
                "share_pp": round(share_pp, 2) if share_pp is not None else None,
                "tol": None,
                "completeness": why,
                "magnitude": (
                    f"preliminary EIA-923 vintage: {why} plant data ({reasons}); "
                    "not gated — C2 family grid reconcile covers this class"
                ),
                "vintage_gap_twh": round(d, 3),  # report-only; does not gate
            }
            out.append(rec)
            continue
        vol_ok = a_gen > 0 and abs(d) <= vol_band
        share_ok = abs(share_pp) <= FUELMIX_SHARE_PP if share_pp is not None else True
        if vol_ok and share_ok:
            status, classification = PASS, None
        else:
            status, classification = FAIL, MODEL_MISS
        mag = f"{d:+.2f} TWh"
        if share_pp is not None:
            mag += f", share {share_pp:+.1f}pp"
        if status == FAIL:
            breach = "/".join(
                lab
                for lab, good in (("volume", vol_ok), ("share", share_ok))
                if not good
            )
            mag += f" ({breach} out of band)"
        rec = {
            "criterion": "fuelmix",
            "key": c,
            "year": year,
            "status": status,
            "classification": classification,
            "metric": f"{c} grid-delivered TWh + share of generation",
            "model": round(m, 3),
            "actual": round(a, 3),
            "share_pp": round(share_pp, 2) if share_pp is not None else None,
            "tol": (
                f"±min({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% ISO-load, "
                f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                f"& ±{FUELMIX_SHARE_PP:g}pp share"
            ),
            "completeness": cmap_year.get(c, {}).get("status", "complete"),
            "magnitude": mag,
        }
        out.append(rec)
    return out


def _fallback_coal_anchor(
    iso: str, ybench: dict, bench_all: dict | None
) -> tuple[float, float, int] | None:
    """CEMS-anchored coal-family actual for a preliminary-vintage year.

    Every coal unit ≥25 MW is CEMS-metered, so CAMPD coal is complete even when
    the EIA-923 vintage is not. The bench part carries the CEMS-net coal total
    (``e930["coal_cems"]``, written solely by ``render_calibration_html`` when the
    bench part is built — the earlier post-hoc splice script was deleted
    2026-07-12 to keep a single writer, per the owner default directive);
    this helper translates it onto the 923-grid family scale with the measured
    CEMS→923-grid ratio ``k`` from the run's own complete-vintage years
    (Σ classFull coal classes ÷ that year's ``coal_cems`` — the parasitic-factor
    / coverage gap, ~0.95–1.01 per ISO). Returns ``(anchor_twh, k, n_years)``
    or ``None`` when the bench predates the splice or no complete coal vintage
    is in the run (the caller then keeps the legacy raw-930 fallback).
    """
    cems = float((ybench.get("e930") or {}).get("coal_cems", 0.0) or 0.0)
    if cems <= 0.0 or not bench_all:
        return None
    ratios = []
    for y2, yb2 in bench_all.items():
        e2 = yb2.get("e930") or {}
        cems2 = float(e2.get("coal_cems", 0.0) or 0.0)
        if cems2 <= 0.0 or not family_is_complete(iso, "coal", int(y2)):
            continue
        grid2 = sum(
            float((yb2.get("classFull") or {}).get(c, 0.0)) for c in COAL_CLASSES
        )
        if grid2 > 0.0:
            ratios.append(grid2 / cems2)
    if not ratios:
        return None
    k = sum(ratios) / len(ratios)
    return cems * k, k, len(ratios)


def score_sysvol(
    year: int,
    ypay: dict,
    ybench: dict,
    iso: str = "ERCOT",
    bench_all: dict | None = None,
) -> list[dict]:
    """C2 — gas/coal family system volume, folded into the per-class universal gate.

    **Rubric v2.5 (owner amendment 2026-07-13): C2 gates ONLY fully-reported
    EIA-923 families.** EIA-923 is the C2 source of truth; a
    preliminary-vintage family (incomplete 923 booking) is NOT gated against
    any fallback basis — the G-21b 930-derived family total and the CAISO
    CEMS anchor below now print as SKIPPED diagnostics only, and the family
    re-gates when the final vintage lands. Mirrors C1's incomplete-class
    skip: an incomplete benchmark can fabricate a miss in either direction,
    so it is evidence, not a gate.

    For COMPLETE-VINTAGE years a family passes iff EVERY constituent fossil class
    is within the universal per-class gate (|model−actual| within the C1 volume
    band AND share within ±FUELMIX_SHARE_PP) — the same scale-relative band C1
    applies, evaluated per class rather than on the netted family aggregate. This
    retires the old ±2.5%-of-family percent band, which had two failure modes: it
    (a) INVENTED a family fail when a mid-size family's small absolute miss
    exceeded 2.5% of itself (e.g. ERCOT coal +1.75 TWh = +3.0% of a 58 TWh family,
    yet only +0.34 pp of generation and well inside the C1 volume band), and (b)
    MASKED a real per-class miss when offsetting class errors netted out across the
    family (e.g. a CT_PEAKER over-build cancelled by a CC under-build summing to
    ~0% at the family level). The per-class roll-up does neither: it nets nothing.

    For a PRELIMINARY-EIA-923 family — one the completeness audit flags as not
    fully reported (:func:`family_is_complete`) — there is no trustworthy per-class
    actual (missing plants under-report thermal; EIA-930 carries no per-class
    split), so the family aggregate vs the authoritative EIA-930 grid total is the
    only available volume check — retained here as the ±2.5% family fallback,
    explicitly scoped to the no-per-class-data case. A preliminary year whose
    family DID fully report (e.g. ERCOT coal 2025) defers to the C1 per-class gate
    exactly like a complete vintage — only the still-incomplete families fall back.

    The fallback compares like for like against the EIA-930 grid cell: the model
    gas sum spans every gas class PLUS the OTHER_FOSSIL scoring bucket (930 books
    mixed gas-thermal plants under NG:NG — same membership as
    ``render_calibration_html._GAS_GROUPS``), and when the bundle carries the
    EIA-930 "other" series the gas target is deflated by the genuinely-folded
    OTHER+biomass portion (post-Nov-2024 storage breakout, ERCO's Other series is
    ~biomass alone, so the 923 OTHER-class generation sits inside NG:NG).

    **G-21b (2026-07-12) — the fallback's per-fuel SPLIT is CEMS-anchored.**
    EIA-930's per-fuel gas/coal attribution is BA-reported and demonstrably
    unreliable against CEMS (every coal unit ≥25 MW is metered): on the
    complete vintages 930 coal runs −17..−21 TWh below CEMS in MISO and
    +7..+11 above in PJM, with the mirror error booked in the NG:NG cell —
    so gating a preliminary family on the raw 930 per-fuel cell fabricates
    misses of exactly that size (the same defect class the G-21 combined
    reconcile fixed for C1's ``classFull``). The fallback therefore keeps the
    930 level but corrects the split with measured data: an incomplete COAL
    family gates against the CEMS anchor (:func:`_fallback_coal_anchor` —
    CAMPD coal × the run's complete-vintage CEMS→923-grid ratio), and an
    incomplete GAS family gates against the 930 COMBINED fossil total minus
    the coal anchor (the anchor from classFull when coal is complete, else
    CEMS). A bench part predating the ``coal_cems`` splice — or a run with no
    complete coal vintage — keeps the legacy raw-930 cell, labelled as such.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    e930 = ybench.get("e930", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)
    out = []
    for fam, classes in (("gas", GAS_CLASSES), ("coal", COAL_CLASSES)):
        scored = [c for c in classes if c not in FUELMIX_EXCLUDED]
        m = sum(float(gm.get(c, 0.0)) for c in scored)
        a923 = sum(float(cf.get(c, 0.0)) for c in scored)
        a930 = float(e930.get(fam, 0.0)) or None
        use_family_fallback = not family_is_complete(iso, fam, year)
        if max(a923, a930 or 0.0) < SYSVOL_MIN_TWH:
            out.append(
                _skip(
                    "sysvol",
                    year,
                    f"{fam} family immaterial (<{SYSVOL_MIN_TWH:g} TWh); "
                    "governed by the C1 per-class absolute band",
                    key=fam,
                )
            )
            continue
        if use_family_fallback:
            # EIA-930 NG:NG includes ALL gas-fired generation at the grid
            # meter (CC, CT, ST — including CHP exports AND the genuinely-
            # mixed gas-thermal plants the scoring transform re-buckets into
            # OTHER_FOSSIL), so the model sum must also include every gas
            # class plus OTHER_FOSSIL, not just the C1-scored subset.  The
            # scored list excludes CT_CHP (a BTM class ungated in C1) and
            # OTHER_FOSSIL (not a merit-order class), but omitting them here
            # creates an apples-to-oranges gap of ~6 + ~1 TWh/yr in ERCOT —
            # the same family membership reconcile_vintage_classes uses
            # (render_calibration_html._GAS_GROUPS).
            fam_all = (*classes, "OTHER_FOSSIL") if fam == "gas" else classes
            m_fam = sum(float(gm.get(c, 0.0)) for c in fam_all)
            a923_fam = sum(float(cf.get(c, 0.0)) for c in fam_all)
            # G-21b: correct the 930 per-fuel split with the CEMS coal anchor
            # (docstring above); keep the 930 combined level. Falls back to
            # the legacy raw cell when the anchor is unavailable.
            anchor = _fallback_coal_anchor(iso, ybench, bench_all)
            actual = a930
            source = "EIA-930 grid (preliminary-923 vintage)"
            if (
                fam == "gas"
                and iso in CEMS_GAS_ANCHOR_ISOS
                and e930.get("gas_cems_grid") is not None
                and e930.get("gas_cogen_grid") is not None
            ):
                # Corrupted-NG-cell ISO: the family actual is the committed
                # CEMS anchor — CEMS bench-gas net (grid-delivered) + the
                # carried 923 non-CEMS cogen block — never the 930 NG cell
                # (which carries the fabricated solar-shaped block). No
                # fold-in deflation applies: the anchor contains no
                # geothermal/biomass by construction.
                actual = float(e930["gas_cems_grid"]) + float(e930["gas_cogen_grid"])
                source = (
                    "CAMPD CEMS bench-gas + EIA-923 non-CEMS cogen block "
                    "(930 NG cell corrupted; FINDING 2026-07-12)"
                )
                err = _pct(m_fam, actual) if actual else None
                # Rubric v2.5 (owner amendment 2026-07-13): a preliminary-923
                # vintage is never gated — the anchor comparison prints as a
                # SKIPPED diagnostic and re-gates when the final vintage lands.
                status, classification = SKIPPED, None
                out.append(
                    {
                        "criterion": "sysvol",
                        "key": fam,
                        "year": year,
                        "status": status,
                        "classification": classification,
                        "metric": (
                            f"{fam} family grid-delivered TWh "
                            "(preliminary vintage, CEMS-anchored diagnostic — "
                            "not gated, rubric v2.5)"
                        ),
                        "model": round(m_fam, 2),
                        "actual": round(actual, 2) if actual else None,
                        "tol": (
                            f"±{SYSVOL_TOL * 100:.1f}% target / "
                            f"±{SYSVOL_COMMERCIAL * 100:.1f}% commercial "
                            "(family, no per-class actual)"
                        ),
                        "magnitude": (
                            f"{err * 100:+.1f}%" if err is not None else "n/a"
                        ),
                        "source": source,
                        "vintage_reconciled": False,
                    }
                )
                continue
            if fam == "coal" and anchor is not None:
                actual, _k, _n = anchor
                source = (
                    "CAMPD CEMS coal × complete-vintage grid ratio "
                    f"(k={_k:.3f}, {_n} yr; G-21b split anchor)"
                )
            elif fam == "gas":
                coal930 = float(e930.get("coal", 0.0) or 0.0)
                coal_anchor = None
                if family_is_complete(iso, "coal", year):
                    _grid = sum(float(cf.get(c, 0.0)) for c in COAL_CLASSES)
                    coal_anchor = _grid if _grid > 0.0 else None
                elif anchor is not None:
                    coal_anchor = anchor[0]
                if coal_anchor is not None and a930 is not None and coal930 > 0.0:
                    actual = (a930 + coal930) - coal_anchor
                    source = (
                        "EIA-930 combined fossil minus coal anchor "
                        "(G-21b split correction)"
                    )
            if fam == "gas" and actual is not None and "other" in e930:
                # ERCO's post-Nov-2024 EIA-930 "Other" series carries roughly
                # biomass alone (the storage breakout moved batteries to
                # BAT/UES), so the OTHER-class generation the 923 books sits
                # inside NG:NG — subtract only the genuinely-folded portion
                # (mirrors render_calibration_html._gas_foldin_deflation).
                actual -= max(
                    0.0,
                    float(cf.get("OTHER", 0.0))
                    + float(cf.get("biomass", 0.0))
                    - float(e930.get("other", 0.0)),
                )
            reconciled = bool(actual and a923_fam < VINTAGE_RECONCILE_FRAC * actual)
            err = _pct(m_fam, actual) if actual else None
            # Rubric v2.5 (owner amendment 2026-07-13): a preliminary-923
            # vintage is never gated — the fallback comparison prints as a
            # SKIPPED diagnostic and re-gates when the final vintage lands.
            status, classification = SKIPPED, None
            out.append(
                {
                    "criterion": "sysvol",
                    "key": fam,
                    "year": year,
                    "status": status,
                    "classification": classification,
                    "metric": (
                        f"{fam} family grid-delivered TWh (preliminary "
                        "vintage diagnostic — not gated, rubric v2.5)"
                    ),
                    "model": round(m_fam, 2),
                    "actual": round(actual, 2) if actual else None,
                    "tol": (
                        f"±{SYSVOL_TOL * 100:.1f}% target / "
                        f"±{SYSVOL_COMMERCIAL * 100:.1f}% commercial "
                        "(family, no per-class actual)"
                    ),
                    "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
                    "source": source,
                    "vintage_reconciled": reconciled,
                }
            )
            continue
        breaches = [
            c
            for c in scored
            if cf.get(c) is not None
            and (
                abs(float(gm.get(c, 0.0)) - float(cf[c])) > vol_band
                or (
                    m_gen > 0
                    and a_gen > 0
                    and abs(
                        100.0 * float(gm.get(c, 0.0)) / m_gen
                        - 100.0 * float(cf[c]) / a_gen
                    )
                    > FUELMIX_SHARE_PP
                )
            )
        ]
        out.append(
            {
                "criterion": "sysvol",
                "key": fam,
                "year": year,
                "status": PASS,  # fully-reported family: governed by C1 per-class
                "classification": None,
                "metric": (
                    f"{fam} family — fully reported; per-class volume/share "
                    "governed by the C1 universal gate (no family netting/percent band)"
                ),
                "model": round(m, 2),
                "actual": round(a923, 2),
                "tol": (
                    f"per-class ±min({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% ISO-load, "
                    f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                    f"& ±{FUELMIX_SHARE_PP:g}pp share (via C1)"
                ),
                "magnitude": (
                    "all classes in band (C1)"
                    if not breaches
                    else f"C1 flags: {', '.join(breaches)}"
                ),
                "source": "EIA-923 − BTM (grid-delivered), per-class via C1",
                "vintage_reconciled": False,
            }
        )
    return out


def score_price_mean(year: int, ypay: dict, ybench: dict) -> dict:
    """C3a — system load-weighted mean LMP vs actual RT (fallback DA).

    The gated benchmark is named in the record's ``metric`` (``vs RT`` /
    ``vs DA``): the model is structurally a real-time analogue (a
    perfect-foresight dispatch LP prices RT physics, not day-ahead risk
    premia), so RT is the honest benchmark and DA is only a fallback when no
    RT actual is committed. The DA comparison is surfaced separately as a
    non-gated diagnostic (:func:`score_price_mean_da_diagnostic`).

    Rubric v2.4: the gated actual is the LIKE-FOR-LIKE load-weighted bench
    (``rt_lw``/``da_lw`` — the committed hourly actual weighted by the same
    measured demand the model dispatches; see the RUBRIC_VERSION note). The
    legacy equal-hour hub fields (``rt``/``da``) remain a labelled fallback
    for ISO-years the lw retrofit does not cover, so no year loses coverage.
    """
    lmp = ypay.get("lmp", {})
    avg = ybench.get("avgLMP") or {}
    # v2.4 basis ladder: load-weighted RT > load-weighted DA > legacy
    # equal-hour RT > legacy equal-hour DA.
    if avg.get("rt_lw") is not None:
        bench_kind, bench_key, lw_basis = "RT", "rt_lw", True
    elif avg.get("da_lw") is not None:
        bench_kind, bench_key, lw_basis = "DA", "da_lw", True
    elif avg.get("rt") is not None:
        bench_kind, bench_key, lw_basis = "RT", "rt", False
    else:
        bench_kind, bench_key, lw_basis = "DA", "da", False
    actual = avg.get(bench_key)
    # Like-for-like calendar coverage: when the actual series is partial (its
    # monthly vector has empty months — e.g. CAISO 2023, whose Jan–Feb aged
    # out of OASIS retention), the committed actual mean only averages the
    # covered months, so the model side must be masked to the SAME months.
    # Comparing a full-year model mean (which correctly carries the $190
    # gas-crisis January) against a Mar–Dec actual is a coverage artifact,
    # not a price error. Full-coverage years are byte-identical.
    actual_mon = avg.get(f"{bench_key}_mon")
    covered = [i for i, v in enumerate(actual_mon or []) if v is not None]
    masked = bool(actual_mon) and 0 < len(covered) < 12
    if masked:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None or actual is None:
        return _skip("price_mean", year, "no model or actual mean LMP")
    err = _pct(model, actual)
    status, classification = _band_result(
        abs(err), PRICE_MEAN_TOL, PRICE_MEAN_COMMERCIAL
    )
    basis = "load-weighted" if lw_basis else "LEGACY equal-hour basis"
    label = (
        f"vs RT ({basis})"
        if bench_kind == "RT"
        else f"vs DA ({basis}) — no RT actual committed"
    )
    if masked:
        label += f" (model masked to actual's {len(covered)}-month coverage)"
    return {
        "criterion": "price_mean",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": f"system load-weighted mean LMP $/MWh ({label})",
        "benchmark": bench_kind,
        "model": round(model, 2),
        "actual": round(actual, 2),
        "tol": (
            f"±{PRICE_MEAN_TOL * 100:.0f}% target / "
            f"±{PRICE_MEAN_COMMERCIAL * 100:.0f}% commercial"
        ),
        "magnitude": f"{err * 100:+.1f}%",
    }


def score_price_mean_da_diagnostic(year: int, ypay: dict, ybench: dict) -> dict | None:
    """C3a DA diagnostic — model mean LMP vs the DA actual, never gated.

    A perfect-foresight dispatch LP is a real-time analogue: the DA−RT spread
    (the DART risk premium — e.g. 2023 ERCOT DA $55.94 vs RT $48.36) is a
    forward risk premium the LP has no mechanism to price, and modeling it
    with offers/adders is forbidden (a fit to the price residual). C3a
    therefore gates on RT; this record makes the DA gap *visible* instead of
    hidden, as a SKIPPED (never PASS/FAIL) diagnostic row. Returns ``None``
    when the DA actual is absent or DA is already the gated fallback
    benchmark (no second series to diagnose).
    """
    avg = ybench.get("avgLMP") or {}
    # v2.4: diagnose on the load-weighted pair when both sides carry it, so
    # the DART premium is read on the same basis C3a gates on; legacy
    # equal-hour pair otherwise.
    if avg.get("rt_lw") is not None and avg.get("da_lw") is not None:
        rt, da = avg.get("rt_lw"), avg.get("da_lw")
        da_mon_key = "da_lw_mon"
    else:
        rt, da = avg.get("rt"), avg.get("da")
        da_mon_key = "da_mon"
    if rt is None or da is None:
        return None  # DA absent, or DA is already the gated benchmark
    lmp = ypay.get("lmp", {})
    # Mirror score_price_mean's partial-coverage masking (same calendar on
    # both sides when the DA actual has empty months).
    da_mon = avg.get(da_mon_key)
    covered = [i for i, v in enumerate(da_mon or []) if v is not None]
    if da_mon and 0 < len(covered) < 12:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None:
        return None
    err = _pct(model, da)
    return {
        "criterion": "price_mean",
        "key": "da_diagnostic",
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": "mean LMP vs DA (diagnostic — DART premium, not gated)",
        "benchmark": "DA",
        "model": round(model, 2),
        "actual": round(float(da), 2),
        "tol": "not gated",
        "magnitude": (
            f"{err * 100:+.1f}% vs DA (DA−RT premium ${float(da) - float(rt):+.2f})"
        ),
    }


def score_price_shape(year: int, ypay: dict, ybench: dict) -> dict:
    """C3b — monthly load-weighted price NRMSE (quantitative shape metric)."""
    lmp = ypay.get("lmp", {})
    # Model monthly = demand-weighted across zones of pMon by dMon.
    model_mon: list[float | None] = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        model_mon.append(_wmean(pairs) if pairs else None)
    avg = ybench.get("avgLMP") or {}
    # v2.4 basis ladder mirroring score_price_mean: load-weighted monthly
    # actual first, legacy equal-hour monthly as labelled fallback.
    actual_mon = avg.get("rt_lw_mon") or avg.get("da_lw_mon")
    lw_basis = actual_mon is not None
    if actual_mon is None:
        actual_mon = avg.get("rt_mon") or avg.get("da_mon")
    if actual_mon is None or all(v is None for v in model_mon):
        return _skip("price_shape", year, "no monthly model or actual LMP")
    nrmse = _nrmse(model_mon, actual_mon)
    if nrmse is None:
        return _skip("price_shape", year, "monthly NRMSE undefined")
    status, classification = _band_result(
        nrmse, PRICE_SHAPE_NRMSE_MAX, PRICE_SHAPE_NRMSE_COMMERCIAL
    )
    basis = "load-weighted" if lw_basis else "LEGACY equal-hour basis"
    return {
        "criterion": "price_shape",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": f"monthly load-weighted price NRMSE ({basis} actual)",
        "model": round(nrmse, 3),
        "actual": None,
        "tol": (
            f"≤{PRICE_SHAPE_NRMSE_MAX:.2f} target / "
            f"≤{PRICE_SHAPE_NRMSE_COMMERCIAL:.2f} commercial"
        ),
        "magnitude": f"NRMSE {nrmse:.3f}",
    }


def score_price_tail(year: int, ypay: dict, iso: str) -> list[dict]:
    """C3c — scarcity tail hours vs the per-ISO-basis hourly actual (rubric v2).

    The model tail (count of hours the LP's max zonal dual exceeds the per-ISO
    threshold, from the payload's ``ordc.hoursGt200.model``) is gated against
    the committed actual tail count (``tail/actual_tail.json``,
    ``scripts/derive_actual_tail.py``) on the ISO's ``TAIL_BASIS`` (rubric §5,
    v2.6 owner amendment 2026-07-16):

    * default **DA** — the hourly, commitment-aware market's own realization
      of scarcity, the model LP's temporal resolution; the RT count (sub-hourly
      transients included) is the report-only diagnostic row. Scope evidence:
      ``docs/multi-iso/miso-scarcity-tail-diagnosis.md`` §1 (MISO 2023's
      entire 30-hour RT tail is single-hour 5-minute transients; DA tail 1 h).
    * **ERCOT: RT** — the RT hourly hub tail; the DA count becomes the
      diagnostic. ERCOT's DA tail runs ABOVE its RT tail (2023: 311 vs 181 h):
      the excess is the day-ahead forecast-risk premium, out of representation
      for a realized-weather backcast (the mirror image of the transient
      argument — see the TAIL_BASIS block comment).

    Band: model within [TAIL_LO x, TAIL_HI x] of the gated actual. Small
    counts (actual < TAIL_SMALL_COUNT) are scored by absolute difference
    (|model − actual| ≤ TAIL_SMALL_COUNT) — a ratio on a handful of hours is
    degenerate, and it doubles as the invented-tail guard against a ~0 actual.
    """
    ordc = ypay.get("ordc")
    thr = TAIL_THRESHOLD.get(iso, 200.0)
    if not ordc or "hoursGt200" not in ordc:
        return [
            _skip(
                "price_tail",
                year,
                f"hourly scarcity series not in committed payload (tail>${thr:.0f})",
            )
        ]
    h = ordc["hoursGt200"]
    # G-20a (2026-07-07, owner-approved): score the SETTLEMENT price
    # (energy LMP + the published reserve/scarcity overlay) when the render
    # derived one for this ISO-year (``overlay`` present), else the energy-only
    # LP dual (``model``). Real RT settlement IS energy LMP + reserve price
    # (ERCOT RTSPP, PJM SRMCP-into-LMP, NYISO RCPF-into-LBMP); the adder is a
    # published, forward-reproducible input (CLAUDE.md rule 13), not fitted to
    # this residual. ``model`` stays emitted (and read below for the diagnostic
    # note) so the energy-only tail remains visible; the settlement count is the
    # gated one. Every VOLUME gate keeps reading the energy-only dual elsewhere.
    settled = h.get("overlay") is not None
    model = float(h["overlay"]) if settled else float(h.get("model", 0))
    energy_only = float(h.get("model", 0))
    tail_rec = _tail_part().get(iso, {}).get(str(year))
    # Gated basis per ISO (rubric §5, v2.5): the other basis is the diagnostic.
    basis_kind = TAIL_BASIS.get(iso, "da")
    gate_key, diag_key = (
        ("rt_gt", "da_gt") if basis_kind == "rt" else ("da_gt", "rt_gt")
    )
    gate_lbl, diag_lbl = ("RT", "DA") if basis_kind == "rt" else ("DA", "RT")
    out: list[dict] = []
    if tail_rec is None or tail_rec.get(gate_key) is None:
        out.append(
            _skip(
                "price_tail",
                year,
                f"no committed {gate_lbl} actual tail for this ISO-year "
                "(frontend/data/backcast/tail/actual_tail.json — run "
                "scripts/derive_actual_tail.py)",
            )
        )
    else:
        actual = float(tail_rec[gate_key])
        cov = tail_rec.get(f"{gate_key[:2]}_coverage", 1.0)
        cov_note = (
            f"; {gate_lbl} coverage {cov:.0%} — count is a lower bound"
            if cov < 0.999
            else ""
        )
        # ``model`` above is the settlement count when an overlay was derived;
        # note the basis and, when overlaid, the energy-only count it was lifted
        # from — so the tail's provenance (energy dual vs energy+reserve price)
        # is visible in the verdict, not just the number.
        basis = "settlement (LMP+overlay)" if settled else "energy-only LMP"
        settle_note = (
            f"; energy-only {energy_only:.0f}h + published overlay" if settled else ""
        )
        if actual < TAIL_SMALL_COUNT:
            ok = abs(model - actual) <= TAIL_SMALL_COUNT
            mag = (
                f"model {model:.0f}h [{basis}] vs {gate_lbl} actual {actual:.0f}h "
                f"(small-count |Δ|≤{TAIL_SMALL_COUNT}h, >${thr:.0f}){settle_note}{cov_note}"
            )
        else:
            ratio = model / actual
            ok = TAIL_LO <= ratio <= TAIL_HI
            mag = (
                f"model {model:.0f}h [{basis}] vs {gate_lbl} actual {actual:.0f}h "
                f"({ratio:.2f}×, >${thr:.0f}){settle_note}{cov_note}"
            )
        out.append(
            {
                "criterion": "price_tail",
                "key": None,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": (
                    f"hours {gate_lbl}-expressible "
                    f"{'settlement price' if settled else 'LMP'} > ${thr:.0f}/MWh"
                ),
                "model": model,
                "actual": actual,
                "tol": (
                    f"[{TAIL_LO:g}×, {TAIL_HI:g}×] of {gate_lbl} actual "
                    f"(|Δ|≤{TAIL_SMALL_COUNT}h when actual <{TAIL_SMALL_COUNT}h)"
                ),
                "magnitude": mag,
            }
        )
    # Companion basis — reported, never gated. On the default DA gate the RT
    # count includes the sub-hourly ramp/re-dispatch transients an hourly
    # deterministic LP is out of scope to reproduce; on the ERCOT RT gate the
    # DA count embeds the day-ahead forecast-risk premium a realized-weather
    # backcast is out of scope to price (v2.6).
    diag_actual = (
        float(tail_rec[diag_key])
        if tail_rec is not None and tail_rec.get(diag_key) is not None
        else (
            float(h["actual"])
            if diag_key == "rt_gt" and h.get("actual") is not None
            else None
        )
    )
    diag_why = (
        "includes sub-hourly transients, not gated"
        if diag_key == "rt_gt"
        else "embeds the DA forecast-risk premium, not gated"
    )
    if diag_actual is not None:
        out.append(
            {
                "criterion": "price_tail",
                "key": f"{diag_key[:2]}_diagnostic",
                "year": year,
                "status": SKIPPED,
                "classification": None,
                "metric": (
                    f"hours {diag_lbl} LMP > ${thr:.0f}/MWh (diagnostic — {diag_why})"
                ),
                "model": model,
                "actual": diag_actual,
                "tol": "not gated",
                "magnitude": (
                    f"model {model:.0f}h vs {diag_lbl} actual {diag_actual:.0f}h "
                    "(out-of-representation companion)"
                ),
            }
        )
    return out


def _pearson_nrmse(m: list, o: list) -> tuple[float, float]:
    """Pearson r and mean-normalized RMSE of two equal-length hourly series."""
    n = len(m)
    mm = sum(m) / n
    om = sum(o) / n
    sxy = sxx = syy = sse = 0.0
    for a, b in zip(m, o):
        da, db = a - mm, b - om
        sxy += da * db
        sxx += da * da
        syy += db * db
        sse += (a - b) * (a - b)
    denom = math.sqrt(sxx * syy)
    r = sxy / denom if denom > 0 else 0.0
    nrmse = math.sqrt(sse / n) / om if om > 0 else 9.9
    return r, nrmse


def _cems_gas_hourly_fit(
    ypay: dict, ybench: dict, model_twh: float | None
) -> tuple[float, float, float] | None:
    """C4 gas fit on the CEMS basis, from committed artifacts only.

    Returns ``(r, nrmse, actual_twh)`` of the model's hourly gas fleet against
    the MEASURED gas hourly actual — CEMS bench-gas hourly (bench part
    ``plants[].campd``, CAMPD net, grid-delivered via a flat BTM CHP removal)
    plus the flat non-CEMS cogen block (``e930.gas_cogen_grid``) — instead of
    the corrupted EIA-930 NG cell. Both sides decode the committed base64 CF%
    series (payload ``plants[].m`` / bench ``plants[].campd``, uint8 percent of
    nameplate): the model core is the CEMS-covered gas plants' dispatch, and
    the payload's remaining gas mass (plants with no CAMPD series) is added as
    a flat fill up to the committed fuel-row level ``model_twh`` — flat terms
    are pearson-invariant, so ``r`` measures the measured-fleet shape while
    NRMSE keeps the coherent grid level on both sides. Payloads rendered after
    the rework carry the same basis natively in ``fuelRows``; this recompute
    scores committed pre-rework payloads identically (to b64 quantization,
    ≤~0.01 in r). ``None`` when the committed artifacts lack the series.
    """
    e930 = ybench.get("e930") or {}
    cogen = e930.get("gas_cogen_grid")
    bplants = ybench.get("plants") or {}
    pplants = ypay.get("plants") or {}
    if cogen is None or not bplants or not pplants:
        return None
    t = 8760
    model = [0.0] * t
    act = [0.0] * t
    btm_twh = 0.0
    n_used = 0
    for code, bp in bplants.items():
        if bp.get("group") not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        camp_b64 = bp.get("campd")
        pp = pplants.get(str(code))
        if cap <= 0.0 or not camp_b64 or not pp or not pp.get("m"):
            continue
        scale = cap / 100.0
        for h, v in enumerate(base64.b64decode(camp_b64)[:t]):
            act[h] += v * scale
        for h, v in enumerate(base64.b64decode(pp["m"])[:t]):
            model[h] += v * scale
        btm_twh += float(bp.get("btm") or 0.0)
        n_used += 1
    if n_used == 0:
        return None
    btm_mw = btm_twh * 1e6 / t  # flat BTM CHP host removal (both sides carry it)
    act = [a - btm_mw + float(cogen) * 1e6 / t for a in act]
    core_twh = sum(model) / 1e6 - btm_twh
    fill_mw = 0.0
    if model_twh is not None:
        fill_mw = (float(model_twh) - core_twh) * 1e6 / t
    model = [m - btm_mw + fill_mw for m in model]
    r, nrmse = _pearson_nrmse(model, act)
    return round(r, 3), round(nrmse, 3), round(sum(act) / 1e6, 2)


def score_dispatch_corr(
    year: int, ypay: dict, ybench: dict | None = None, iso: str = "ERCOT"
) -> list[dict]:
    """C4 — fleet hourly r/NRMSE floors for the gas and coal fleets.

    For a :data:`CEMS_GAS_ANCHOR_ISOS` ISO from the onset vintage onward, the
    gas fit is recomputed on the CEMS basis (:func:`_cems_gas_hourly_fit`) —
    the committed payload's 930-based ``fuelRows`` values score benchmark
    corruption there, not the model. Pre-onset years and every other ISO keep
    the payload's committed fit unchanged.
    """
    rows = {r.get("fuel"): r for r in ypay.get("fuelRows", [])}
    out = []
    for fam in ("gas", "coal"):
        r = rows.get(fam, {})
        rr, nr = r.get("r"), r.get("nrmse")
        cems_fit = None
        if (
            fam == "gas"
            and iso in CEMS_GAS_ANCHOR_ISOS
            and year >= CEMS_GAS_ANCHOR_ONSET.get(iso, 9999)
            and ybench is not None
        ):
            cems_fit = _cems_gas_hourly_fit(ypay, ybench, r.get("m"))
            if cems_fit is not None:
                rr, nr = cems_fit[0], cems_fit[1]
                r = dict(r, b=cems_fit[2])
        if rr is None and nr is None:
            out.append(
                _skip("dispatch_corr", year, f"{fam} hourly fit absent", key=fam)
            )
            continue
        twh = max(abs(r.get("m") or 0.0), abs(r.get("b") or 0.0))
        if twh < DISP_MIN_TWH:
            out.append(
                _skip(
                    "dispatch_corr",
                    year,
                    f"{fam} fleet immaterial (<{DISP_MIN_TWH:g} TWh); "
                    "hourly correlation degenerate",
                    key=fam,
                )
            )
            continue
        ok = (rr is not None and rr >= DISP_R_FLOOR) and (
            nr is not None and nr <= DISP_NRMSE_MAX
        )
        out.append(
            {
                "criterion": "dispatch_corr",
                "key": fam,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": (
                    f"{fam} fleet hourly r / NRMSE"
                    + (
                        " (CEMS hourly + flat cogen block; 930 NG cell "
                        "corrupted — FINDING 2026-07-12)"
                        if cems_fit is not None
                        else ""
                    )
                ),
                "model": f"r={rr} nrmse={nr}",
                "actual": None,
                "tol": f"r≥{DISP_R_FLOOR:.2f}, NRMSE≤{DISP_NRMSE_MAX:.2f}",
                "magnitude": f"r={rr}, NRMSE={nr}",
            }
        )
    return out


def score_co2(year: int, ypay: dict, ybench: dict) -> dict:
    """C5a — CO2 vs eGRID; SKIPPED unless an emissions actual is committed.

    Both sides are the full-plant CHP-inclusive basis (rubric v2.3): the
    renderer/retrofit adds the measured BTM CHP host supply back onto the
    model's grid dispatch and onto the EIA-923 class totals before applying
    the eGRID/CAMPD intensities, because those per-plant rates are defined
    over each cogen's FULL net generation. Committed payloads carry the
    already-based numbers; this gate just compares them.
    """
    model = (ypay.get("co2") or {}).get("model")
    actual = (ybench.get("co2") or {}).get("egrid")
    if model is None or actual is None:
        return _skip("co2", year, "no CO2/eGRID actual in committed artifacts")
    err = _pct(model, actual)
    if err is None:
        return _skip("co2", year, "CO2 percentage undefined (zero actual)")
    status, classification = _band_result(abs(err), CO2_TOL, CO2_COMMERCIAL)
    return {
        "criterion": "co2",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": "system CO2 vs eGRID (full-plant basis, BTM CHP added back)",
        "model": model,
        "actual": actual,
        "tol": (
            f"±{CO2_TOL * 100:.0f}% target / ±{CO2_COMMERCIAL * 100:.0f}% commercial"
        ),
        "magnitude": f"{err * 100:+.1f}%",
    }


def score_storage(year: int, ypay: dict, ybench: dict) -> dict:
    """C5b — storage throughput; SKIPPED when EIA-930 has no storage breakout."""
    model = (ypay.get("storage") or {}).get("throughput_twh")
    actual = (ybench.get("storage") or {}).get("throughput_twh")
    if actual is None:
        return _skip(
            "storage",
            year,
            "EIA-930 has no battery/pumped-storage breakout for this BA-year"
            + (f" (model discharged {model:.3f} TWh)" if model else ""),
        )
    if model is None:
        return _skip(
            "storage",
            year,
            "model storage throughput absent (legacy bundle without storage.parquet)"
            + f" (actual {actual:.3f} TWh)",
        )
    err = _pct(model, actual)
    ok = err is not None and abs(err) <= STORAGE_TOL
    return {
        "criterion": "storage",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "storage discharge throughput TWh",
        "model": model,
        "actual": actual,
        "tol": f"±{STORAGE_TOL * 100:.0f}%",
        "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
    }


def score_storage_shape(year: int, ypay: dict, ybench: dict) -> dict:
    """C5c — monthly storage dispatch shape; SKIPPED when either side is absent."""
    model_mon = (ypay.get("storage") or {}).get("monthly_net_gwh")
    actual_mon = (ybench.get("storage") or {}).get("monthly_net_gwh")
    if actual_mon is None:
        return _skip(
            "storage_shape",
            year,
            "EIA-930 has no monthly storage dispatch breakout for this BA-year",
        )
    if model_mon is None:
        return _skip(
            "storage_shape",
            year,
            "model storage monthly dispatch absent (legacy bundle)",
        )
    if len(model_mon) != 12 or len(actual_mon) != 12:
        return _skip("storage_shape", year, "monthly vector length != 12")
    if any(x is None for x in model_mon) or any(x is None for x in actual_mon):
        return _skip(
            "storage_shape",
            year,
            "monthly vector has one or more missing (null) months",
        )
    m = [float(x) for x in model_mon]
    a = [float(x) for x in actual_mon]
    n = len(m)
    m_mean = sum(m) / n
    a_mean = sum(a) / n
    cov = sum((m[i] - m_mean) * (a[i] - a_mean) for i in range(n)) / n
    m_std = (sum((x - m_mean) ** 2 for x in m) / n) ** 0.5
    a_std = (sum((x - a_mean) ** 2 for x in a) / n) ** 0.5
    # Degeneracy guard (mirrors C4's <5 TWh rule): when the ACTUAL monthly
    # discharge is near-uniform (CV below the floor — e.g. NEISO 2025 PS,
    # CV≈0.14: Northfield cycles near-daily year-round on reserves/regulation),
    # there is no seasonal shape to correlate — the 12-point Pearson is set by
    # reporting noise, and a perfectly flat (i.e. TRUE) model would score
    # r = 0 and FAIL. A metric the truth itself cannot pass is degenerate, so
    # the year is SKIPPED (never a silent pass); the under/over-cycling volume
    # stays fully scored by C5b.
    if a_mean != 0.0 and a_std / abs(a_mean) < STORAGE_SHAPE_MIN_CV:
        return _skip(
            "storage_shape",
            year,
            f"actual monthly storage shape degenerate (CV="
            f"{a_std / abs(a_mean):.3f} < {STORAGE_SHAPE_MIN_CV}): near-uniform "
            "year-round cycling leaves no seasonal shape to correlate; volume "
            "is scored by C5b",
        )
    r = cov / (m_std * a_std) if m_std > 0 and a_std > 0 else 0.0
    ok = r >= STORAGE_SHAPE_R_FLOOR
    return {
        "criterion": "storage_shape",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "monthly discharge pearson r",
        "model": round(r, 3),
        "actual": None,
        "tol": f"r ≥ {STORAGE_SHAPE_R_FLOOR}",
        "magnitude": f"r={r:.3f}",
    }


_LEGIT_HOWTO = (
    "run scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO> "
    "--json-out <dir>/legitimacy_diagnostics.json and commit it"
)


def _class_load_share(klass: str, ypay: dict, ybench: dict) -> float | None:
    """Class annual energy as a fraction of total ISO load (C7/C8 materiality).

    Uses ``max(model, actual)`` energy for the class — a binding floor cannot
    hide a class below the materiality line by its own forcing (forcing raises
    model energy), and a model that zeroes a genuinely material class stays
    scored via the actual side. ``None`` when the totals are unavailable
    (caller then gates — conservative, never a silent skip).
    """
    m = float((ypay.get("gmModel") or {}).get(klass, 0.0))
    a = float((ybench.get("classFull") or {}).get(klass) or 0.0)
    _, a_gen = _gen_totals(ypay, ybench)
    load = _total_load(ypay, a_gen)
    if load <= 0:
        return None
    return max(m, a) / load


def _immaterial_protective(criterion, klass, year, share, extra=""):
    """SKIPPED-immaterial record for a C7/C8 class below the materiality floor."""
    rec = _skip(
        criterion,
        year,
        (
            f"{klass} immaterial ({share:.1%} of ISO load < "
            f"{PROTECTIVE_MIN_LOAD_FRAC:.0%} floor, max(model, actual) energy): "
            "reported by the D-1/D-2 diagnostics, not gated (rubric v2.1 owner "
            f"amendment 2026-07-06){extra}"
        ),
        key=klass,
    )
    return rec


def score_shape(year: int, legit: dict | None, ypay: dict, ybench: dict) -> list[dict]:
    """C7 — diurnal shape (audit D-1), from the bundle's committed artifact.

    Reads ``<bundle>/legitimacy_diagnostics.json`` (written by
    ``scripts/legitimacy_diagnostics.py --json-out``) — the verdict never
    recomputes the diagnostic, so the S1 suite stays the single
    implementation. A gated peaker/intermediate class (per the artifact's
    ``d1_gated_classes``) FAILs the year when its hour-of-day profile
    correlation or off-peak CV ratio breaches the artifact's D-1 gates — the
    caiso-42 flat-floor signature (model CV 0.000 vs actual 0.35-0.45) that
    annual-volume bands cannot see. Materiality floor (rubric v2.1): a class
    below ``PROTECTIVE_MIN_LOAD_FRAC`` of ISO load is SKIPPED-immaterial
    (reported, never gated). SKIPPED (never a silent pass) when the artifact
    or the year is absent.
    """
    if legit is None:
        return [
            _skip(
                "shape",
                year,
                f"no legitimacy_diagnostics.json in bundle — {_LEGIT_HOWTO}",
            )
        ]
    gates = legit.get("gates", {})
    rows = [
        r
        for r in legit.get("diagnostics", {}).get("D1", {}).get("rows", [])
        if int(r.get("year", -1)) == int(year) and r.get("gated")
    ]
    if not rows:
        return [
            _skip(
                "shape",
                year,
                "no gated-class D-1 rows for this year in legitimacy_diagnostics.json",
            )
        ]
    tol = (
        f"profile r ≥ {gates.get('d1_min_profile_r')} & off-peak CV ratio ≥ "
        f"{gates.get('d1_min_cv_ratio')} (h0-{gates.get('d1_offpeak_last_hour')}); "
        f"class ≥ {PROTECTIVE_MIN_LOAD_FRAC:.0%} of load"
    )
    out = []
    for r in rows:
        klass = r.get("class")
        share = _class_load_share(klass, ypay, ybench)
        if share is not None and share < PROTECTIVE_MIN_LOAD_FRAC:
            out.append(
                _immaterial_protective(
                    "shape",
                    klass,
                    year,
                    share,
                    extra=(
                        f"; D-1 reads profile r {r.get('profile_r')}, "
                        f"off-peak CV ratio {r.get('cv_ratio')}"
                    ),
                )
            )
            continue
        ok = r.get("verdict") != "FAIL"
        out.append(
            {
                "criterion": "shape",
                "key": klass,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": f"{klass} hour-of-day profile vs CAMPD (D-1)",
                "model": f"r={r.get('profile_r')} cv={r.get('model_offpeak_cv')}",
                "actual": f"cv={r.get('actual_offpeak_cv')}",
                "tol": tol,
                "magnitude": (
                    f"profile r {r.get('profile_r')}, off-peak CV ratio "
                    f"{r.get('cv_ratio')}"
                ),
            }
        )
    return out


def _binding_merchant_mechs(legit: dict, year: int, klass: str) -> list[str]:
    """Mechanism NAMES the class is forced by that count toward the C8 gate.

    From the committed D-2 per-(class, mechanism) rows: every mechanism with a
    positive ``share_of_class`` for ``(year, klass)`` that is NOT in
    :data:`FORCED_EXEMPT_MECH_NAMES` (structural must-run / non-thermal
    boundaries, which run_d2 already excludes from the class forced share). This
    is exactly the set whose forcing must be justified for a grounded-above-budget
    pass.
    """
    out: list[str] = []
    for r in legit.get("diagnostics", {}).get("D2", {}).get("rows", []):
        if int(r.get("year", -1)) != int(year) or str(r.get("class")) != str(klass):
            continue
        mech = str(r.get("mechanism", ""))
        if float(r.get("share_of_class", 0) or 0.0) > 0.0 and (
            mech not in FORCED_EXEMPT_MECH_NAMES
        ):
            out.append(mech)
    return sorted(set(out))


def _d4_provenance(legit: dict, year: int, klass: str, mechs: list[str]):
    """(ok, detail) — do ALL of the class's binding merchant mechanisms clear D-4.

    A mechanism clears when the committed D-4 off-window rows carry at least one
    entry for it (a declared, driver-justified window — the ``floor`` label is
    the mechanism name, optionally ``<mech> × <class>``) that applies to this
    class, and EVERY applicable entry passes (off-window share within the D-4
    tolerance). A mechanism with NO applicable D-4 row has no declared window —
    provenance fails for it (rule 12: no floor without a window). ``detail``
    names the offending mechanism(s) for the report.
    """
    if not mechs:
        # No attributable binding merchant mechanism (D-2 rows absent, or a
        # legacy artifact without them): forcing above the cap that cannot be
        # traced to a mechanism cannot be grounded — fail conservatively.
        return False, (
            "no attributable binding merchant mechanism in D-2 rows "
            "(provenance unverifiable)"
        )
    d4_rows = legit.get("diagnostics", {}).get("D4", {}).get("rows", [])
    unwindowed: list[str] = []
    offwindow: list[str] = []
    for mech in mechs:
        applicable = [
            row
            for row in d4_rows
            if int(row.get("year", -1)) == int(year)
            and str(row.get("floor", "")) in (mech, f"{mech} × {klass}")
        ]
        if not applicable:
            unwindowed.append(mech)
        elif any(str(row.get("verdict")) == "FAIL" for row in applicable):
            offwindow.append(mech)
    ok = not unwindowed and not offwindow
    bits = []
    if unwindowed:
        bits.append("no declared D-4 window: " + ", ".join(unwindowed))
    if offwindow:
        bits.append("binds off-window (D-4 FAIL): " + ", ".join(offwindow))
    return ok, ("; ".join(bits) if bits else "all binding mechanisms clear D-4")


def _d1_shape(legit: dict, year: int, klass: str):
    """(ok, detail) — does the class's D-1 hour-of-day profile clear the gates.

    Applies the artifact's own D-1 gates (``d1_min_profile_r`` /
    ``d1_min_cv_ratio``) to ``klass`` regardless of whether it is in the default
    ``d1_gated_classes`` — the escalation treats any above-budget class as
    shape-gated. A missing D-1 row (no profile to check) fails conservatively:
    an unverifiable shape cannot ground the forcing.
    """
    gates = legit.get("gates", {})
    min_r = float(gates.get("d1_min_profile_r", 0.8))
    min_cv = float(gates.get("d1_min_cv_ratio", 0.5))
    row = next(
        (
            r
            for r in legit.get("diagnostics", {}).get("D1", {}).get("rows", [])
            if int(r.get("year", -1)) == int(year) and str(r.get("class")) == str(klass)
        ),
        None,
    )
    if row is None:
        return False, f"no D-1 profile for {klass} (shape unverifiable)"
    r_val = row.get("profile_r")
    cv = row.get("cv_ratio")  # None when actual off-peak CV is degenerate
    r_ok = r_val is not None and float(r_val) >= min_r
    cv_ok = cv is None or float(cv) >= min_cv
    detail = (
        f"profile r {r_val} (≥{min_r}) & off-peak CV ratio "
        f"{cv if cv is not None else 'n/a'} (≥{min_cv})"
    )
    return (r_ok and cv_ok), detail


def score_forced_share(
    year: int, legit: dict | None, ypay: dict, ybench: dict
) -> list[dict]:
    """C8 — forced-energy share (audit D-2 / CLAUDE.md rule 20, as amended).

    Reads the D-2 per-class summary from the bundle's committed
    ``legitimacy_diagnostics.json`` — the share of a class's energy dispatched
    AT a binding non-exempt ``min_gen`` floor (nuclear / CHP-steam /
    coal-take-or-pay mechanisms exempt) — and gates the MEASURED share against
    the rubric's caps (< 15 % peaker / < 30 % merchant, rule 20 as amended
    2026-07-06; the artifact's own embedded verdict is ignored so artifacts
    written under earlier gate values score correctly). Materiality floor
    (rubric v2.1): a class below ``PROTECTIVE_MIN_LOAD_FRAC`` of ISO load is
    SKIPPED-immaterial (reported, never gated). Rebuilt-floor shares
    (``lower_bound``) are flagged in the record: a PASS there is a lower
    bound, never an upper one. SKIPPED when the artifact or the year is
    absent.

    Grounded-above-budget escalation (rubric v2.2, 2026-07-07): a class ABOVE
    its cap is no longer an automatic FAIL. It escalates to a conditional pass
    on PROVENANCE (every binding merchant mechanism clears D-4 off-window
    binding — :func:`_d4_provenance`) AND SHAPE (the class's D-1 profile clears
    the artifact gates — :func:`_d1_shape`). Both clear -> CLEAN PASS classified
    :data:`GROUNDED_ABOVE_BUDGET` (surfaced as a report note, not a caveat);
    either fails -> FAIL, the miss described as a forcing shape/provenance
    mismatch (the "forcing variables are wrong" signal). See the constant block
    for the full rationale.
    """
    if legit is None:
        return [
            _skip(
                "forced_share",
                year,
                f"no legitimacy_diagnostics.json in bundle — {_LEGIT_HOWTO}",
            )
        ]
    rows = [
        r
        for r in legit.get("diagnostics", {}).get("D2", {}).get("summary", [])
        if int(r.get("year", -1)) == int(year)
    ]
    if not rows:
        return [
            _skip(
                "forced_share",
                year,
                "no D-2 per-class summary for this year in legitimacy_diagnostics.json",
            )
        ]
    out = []
    for r in rows:
        klass = r.get("class")
        fs = float(r.get("forced_share", 0) or 0.0)
        share = _class_load_share(klass, ypay, ybench)
        if share is not None and share < PROTECTIVE_MIN_LOAD_FRAC:
            out.append(
                _immaterial_protective(
                    "forced_share",
                    klass,
                    year,
                    share,
                    extra=f"; D-2 reads {fs * 100:.1f}% forced",
                )
            )
            continue
        cap = (
            FORCED_SHARE_PEAKER_MAX
            if klass in FORCED_SHARE_PEAKER_CLASSES
            else FORCED_SHARE_MERCHANT_MAX
        )
        lb = (
            " (rebuilt floors exclude the P1-dependent RA bridge — share is a lower bound)"
            if r.get("lower_bound")
            else ""
        )
        base = f"{fs * 100:.1f}% forced ({r.get('forced_twh')} of {r.get('class_total_twh')} TWh)"
        if fs <= cap:
            # Within budget: passes cheaply on the share alone (unchanged).
            status, classification, magnitude = PASS, None, base + lb
        else:
            # Above budget: escalate on provenance (D-4) + shape (D-1).
            mechs = _binding_merchant_mechs(legit, year, klass)
            prov_ok, prov_detail = _d4_provenance(legit, year, klass, mechs)
            shape_ok, shape_detail = _d1_shape(legit, year, klass)
            if prov_ok and shape_ok:
                status, classification = PASS, GROUNDED_ABOVE_BUDGET
                magnitude = (
                    f"{base} — above the {cap * 100:.0f}% cap but GROUNDED: "
                    f"{prov_detail}; {shape_detail}{lb}"
                )
            else:
                status, classification = FAIL, MODEL_MISS
                miss = "; ".join(
                    part
                    for part in (
                        None if prov_ok else f"provenance — {prov_detail}",
                        None if shape_ok else f"shape — {shape_detail}",
                    )
                    if part
                )
                magnitude = (
                    f"{base} — above the {cap * 100:.0f}% cap and NOT grounded "
                    f"(forcing variables miscalibrated): {miss}{lb}"
                )
        out.append(
            {
                "criterion": "forced_share",
                "key": klass,
                "year": year,
                "status": status,
                "classification": classification,
                "metric": f"{klass} energy at binding non-exempt floors (D-2)",
                "model": fs,
                "actual": None,
                "tol": (
                    f"< {cap * 100:.0f}% of class energy, OR above-cap with D-4 "
                    f"window + D-1 shape clear (class ≥ {PROTECTIVE_MIN_LOAD_FRAC:.0%} "
                    "of load)"
                ),
                "magnitude": magnitude,
            }
        )
    return out


def _skip(criterion: str, year: int, reason: str, key: str | None = None) -> dict:
    """Build a SKIPPED record (recorded as not-scored, never a silent pass)."""
    return {
        "criterion": criterion,
        "key": key,
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": CRITERIA[criterion][0],
        "model": None,
        "actual": None,
        "tol": None,
        "magnitude": reason,
    }


def score_governance(config: dict | None, attestation: dict | None) -> dict:
    """C6 — governance gate (machine cross-check + required attestation).

    PASS iff config is clean (exogenous outage source, no forbidden flags) AND an
    attestation is present with all four assertions true. FAIL if the machine
    check trips or any assertion is false. UNATTESTED (-> NOT-YET) if no
    attestation file exists — a run cannot be certified unattested.
    """
    sc = (config or {}).get("scenario_config", {})
    meta = (config or {}).get("meta", {})
    outage = meta.get("outage_source") or sc.get("outage_source")
    machine_issues = []
    if outage is not None and outage not in EXOGENOUS_OUTAGE_SOURCES:
        machine_issues.append(
            f"outage_source={outage!r} is not an exogenous availability source"
        )
    for flag in FORBIDDEN_FLAGS:
        if sc.get(flag):
            machine_issues.append(f"forbidden fitted-mechanism flag active: {flag}")

    assertions = [
        "levers_trace_to_measured_input",
        "no_fit_to_price_residuals",
        "no_pinning_to_actuals",
        "outage_filter_exogenous_net_load",
    ]
    if attestation is None or not attestation.get("governance"):
        # A bundle whose attestation carries no governance block (e.g. only a
        # free_parameters DOF ledger) is exactly as unattested as one with no
        # file: nobody has asserted the four governance claims.
        status, detail = (
            "UNATTESTED",
            "no governance attestation in bundle"
            + ("" if attestation is None else " (attestation has no governance block)"),
        )
    else:
        gov = attestation.get("governance", {})
        false_asserts = [a for a in assertions if not gov.get(a, False)]
        if machine_issues:
            status, detail = FAIL, "; ".join(machine_issues)
        elif false_asserts:
            status, detail = FAIL, "attestation false: " + ", ".join(false_asserts)
        else:
            status = PASS
            detail = gov.get("attested_by", "attested")
    if attestation is None and machine_issues:
        detail = "; ".join(machine_issues) + "; and no attestation"
    return {
        "criterion": "governance",
        "key": None,
        "year": None,
        "status": status,
        "classification": None if status == PASS else MODEL_MISS,
        "metric": "every lever measured; no residual fit / pinning; exogenous outages",
        "model": None,
        "actual": None,
        "tol": "pass/fail",
        "magnitude": detail,
        "machine_issues": machine_issues,
    }


# ---------------------------------------------------------------------------
# Aggregation + determination
# ---------------------------------------------------------------------------
def _agg_status(records: list[dict]) -> str:
    """Aggregate per-year statuses for one criterion (FAIL>CAVEAT>PASS>SKIPPED)."""
    s = {r["status"] for r in records}
    if FAIL in s:
        return FAIL
    if CAVEAT in s:
        return CAVEAT
    if PASS in s:
        return PASS
    return SKIPPED


def free_class_score(iso: str, records: list[dict]) -> dict:
    """D-10 — recompute the C1 pass rate with the pinned classes excluded.

    ``records`` are the already-scored per-criterion records; this reads the C1
    (``fuelmix``) rows only. Returns both the all-class C1 pass rate and the
    "free-class" rate that excludes the ISO's pinned classes
    (:data:`PINNED_CLASSES_BY_ISO`) — the classes the audit L-rows show are
    pinned to a measured realization (wind/solar/nuclear/hydro/CHP/imports), so a
    pass there is plumbing. Pass = clean in-tolerance (``PASS``); the denominator
    is the gated (scored, non-``SKIPPED``) C1 rows. No gate — the number is the
    deliverable ("pinned-class gate inflation" made visible; audit §7 D-10).
    """
    pinned = PINNED_CLASSES_BY_ISO.get(iso.upper(), _PINNED_CLASSES_COMMON)
    scored = [
        r
        for r in records
        if r["criterion"] == "fuelmix" and r["status"] in (PASS, FAIL, CAVEAT)
    ]
    free = [r for r in scored if r.get("key") not in pinned]

    def _rate(rows: list[dict]) -> dict:
        return {
            "pass": sum(1 for r in rows if r["status"] == PASS),
            "total": len(rows),
        }

    all_rate, free_rate = _rate(scored), _rate(free)
    return {
        "iso": iso,
        "pinned_classes": sorted(pinned),
        "excluded_from_free": sorted(
            {r.get("key") for r in scored if r.get("key") in pinned}
        ),
        "all": all_rate,
        "free": free_rate,
        "headline": (
            f"C1 all {all_rate['pass']}/{all_rate['total']} · "
            f"free {free_rate['pass']}/{free_rate['total']}"
        ),
    }


def determine(run_id: str) -> dict:
    """Score one run from its committed artifacts (rubric §2)."""
    return determine_from_artifacts(run_id, load_artifacts(run_id))


def determine_from_artifacts(run_id: str, art: dict) -> dict:
    """Score one run's loaded artifacts and return the full verdict dict.

    Split out from :func:`determine` so the decision logic can be unit-tested on
    synthetic artifacts without reading files.
    """
    sidecar, payload, bench = art["sidecar"], art["payload"], art["bench"]
    iso = sidecar.get("iso", "ERCOT")
    exceptions = (art["attestation"] or {}).get("exceptions", [])

    target_years = [int(y) for y in sidecar.get("years", [])]
    scorable_years = sorted(int(y) for y in (payload or {}).get("years", {}))
    data_blocked = sorted(set(target_years) - set(scorable_years))

    # Score every criterion-year.
    records: list[dict] = []
    for year in scorable_years:
        ypay = payload["years"][str(year)]
        ybench = bench.get(year, {})
        records += score_fuelmix(year, ypay, ybench, iso)
        records += score_sysvol(year, ypay, ybench, iso, bench_all=bench)
        records.append(score_price_mean(year, ypay, ybench))
        da_diag = score_price_mean_da_diagnostic(year, ypay, ybench)
        if da_diag is not None:
            records.append(da_diag)
        records.append(score_price_shape(year, ypay, ybench))
        records += score_price_tail(year, ypay, iso)
        records += score_dispatch_corr(year, ypay, ybench, iso)
        records.append(score_co2(year, ypay, ybench))
        records.append(score_storage(year, ypay, ybench))
        records.append(score_storage_shape(year, ypay, ybench))
        records += score_shape(year, art.get("legitimacy"), ypay, ybench)
        records += score_forced_share(year, art.get("legitimacy"), ypay, ybench)

    # Apply the exceptions ledger (FAIL -> CAVEAT where documented).
    for r in records:
        _apply_ledger(r, exceptions)

    gov = score_governance(art["config"], art["attestation"])

    # Aggregate per criterion.
    per_criterion: dict[str, dict] = {}
    for cid, (label, tier) in CRITERIA.items():
        if cid == "governance":
            per_criterion[cid] = {
                "label": label,
                "tier": tier,
                "hard": True,  # legacy display key: protective = the v1 hard gate
                "status": gov["status"],
                "records": [gov],
            }
            continue
        recs = [r for r in records if r["criterion"] == cid]
        # A criterion at CAVEAT is LEDGERED when any of its caveat records was
        # earned by an exceptions-ledger entry (MEASURED_LIMIT — budgeted);
        # otherwise every caveat sits inside the commercial band (auto, listed
        # not budgeted).
        ledgered = any(
            r["status"] == CAVEAT and r.get("classification") == MEASURED_LIMIT
            for r in recs
        )
        per_criterion[cid] = {
            "label": label,
            "tier": tier,
            "hard": tier == TIER_PROTECT,
            "status": _agg_status(recs) if recs else SKIPPED,
            "caveat_kind": (
                ("ledgered" if ledgered else "commercial-band")
                if (_agg_status(recs) if recs else SKIPPED) == CAVEAT
                else None
            ),
            "records": recs,
        }

    # Caveat budgets (rubric §2 v2): protective ledgered caveats keep the v1
    # budget of 1; non-protective LEDGERED caveats are capped at 3; auto
    # commercial-band caveats are unbudgeted (inside the certification claim)
    # but every one is listed below with its magnitude.
    protective_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] == TIER_PROTECT and cid != "governance" and c["status"] == CAVEAT
    ]
    ledgered_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] != TIER_PROTECT
        and c["status"] == CAVEAT
        and c["caveat_kind"] == "ledgered"
    ]
    band_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] != TIER_PROTECT
        and c["status"] == CAVEAT
        and c["caveat_kind"] == "commercial-band"
    ]
    fails = [cid for cid, c in per_criterion.items() if c["status"] == FAIL]
    # An unscored criterion can never be a silent pass: it caps the
    # determination at CALIBRATED-WITH-CAVEATS and is named in the reasons
    # (protective skips — e.g. C7/C8 with no committed
    # legitimacy_diagnostics.json — are called out explicitly).
    skipped = [
        cid
        for cid, c in per_criterion.items()
        if cid != "governance" and c["status"] == SKIPPED
    ]
    skipped_protective = [
        cid for cid in skipped if per_criterion[cid]["tier"] == TIER_PROTECT
    ]

    # Determination (rubric §2).
    reasons: list[str] = []
    if gov["status"] != PASS:
        determination = NOT_YET
        reasons.append(f"governance gate {gov['status']}: {gov['magnitude']}")
    elif fails:
        determination = NOT_YET
        reasons.append(
            "undocumented out-of-tolerance (FAIL) criteria: " + ", ".join(fails)
        )
    elif (
        len(protective_caveats) > MAX_PROTECTIVE_CAVEATS
        or len(ledgered_caveats) > MAX_LEDGERED_CAVEATS
    ):
        determination = NOT_YET
        reasons.append(
            "caveat budget exceeded (protective "
            f"{len(protective_caveats)}/{MAX_PROTECTIVE_CAVEATS}, ledgered "
            f"{len(ledgered_caveats)}/{MAX_LEDGERED_CAVEATS})"
        )
    else:
        n_caveats = len(protective_caveats) + len(ledgered_caveats) + len(band_caveats)
        if n_caveats == 0 and not skipped and not data_blocked:
            determination = CALIBRATED
        else:
            determination = CALIBRATED_CAVEATS
            if band_caveats:
                reasons.append(
                    f"{len(band_caveats)} criterion(s) within the commercial-grade "
                    "band but outside target: "
                    + ", ".join(c["label"] for c in band_caveats)
                )
            if ledgered_caveats:
                reasons.append(
                    f"{len(ledgered_caveats)} ledgered measured-input caveat(s): "
                    + ", ".join(c["label"] for c in ledgered_caveats)
                )
            if protective_caveats:
                reasons.append(
                    f"{len(protective_caveats)} protective-gate ledgered caveat(s): "
                    + ", ".join(c["label"] for c in protective_caveats)
                )
            if skipped_protective:
                reasons.append(
                    "unscored PROTECTIVE criteria: " + ", ".join(skipped_protective)
                )
            other_skips = [c for c in skipped if c not in skipped_protective]
            if other_skips:
                reasons.append("unscored criteria: " + ", ".join(other_skips))
            if data_blocked:
                reasons.append(
                    "data-blocked target year(s): " + ", ".join(map(str, data_blocked))
                )

    # Report notes (not caveats): grounded-above-budget C8 passes — a class
    # forced past its cap that cleared the D-4 provenance + D-1 shape escalation
    # (owner decision 2026-07-07: a CLEAN PASS surfaced as a note so the high
    # forcing stays visible and auditable without counting against any budget).
    notes: list[str] = []
    for r in records:
        if (
            r.get("criterion") == "forced_share"
            and r.get("status") == PASS
            and r.get("classification") == GROUNDED_ABOVE_BUDGET
        ):
            notes.append(
                f"C8 {r['year']} {r.get('key')}: grounded above budget — {r['magnitude']}"
            )

    # Grade summary (reported): how many scored criteria sit at target grade
    # (clean PASS) vs commercial grade (auto band caveat) vs ledgered.
    scored = [
        c for cid, c in per_criterion.items() if c["status"] in (PASS, CAVEAT, FAIL)
    ]
    grade_summary = {
        "scored": len(scored),
        "target_grade": sum(1 for c in scored if c["status"] == PASS),
        "commercial_grade": len(band_caveats),
        "ledgered": len(ledgered_caveats) + len(protective_caveats),
        "fails": len(fails),
    }

    return {
        "run_id": run_id,
        "iso": iso,
        "label": sidecar.get("label", run_id),
        "rubric_version": RUBRIC_VERSION,
        "target_years": target_years,
        "scorable_years": scorable_years,
        "data_blocked_years": data_blocked,
        "determination": determination,
        "reasons": reasons,
        "notes": notes,
        "criteria": per_criterion,
        "free_class_score": free_class_score(iso, records),
        "grade_summary": grade_summary,
        "caveats": {
            "protective": [c["label"] for c in protective_caveats],
            "ledgered": [c["label"] for c in ledgered_caveats],
            "commercial_band": [c["label"] for c in band_caveats],
            "budget": {
                "protective_max": MAX_PROTECTIVE_CAVEATS,
                "ledgered_max": MAX_LEDGERED_CAVEATS,
            },
        },
        "ledger_entries": exceptions,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
_MARK = {PASS: "✓", CAVEAT: "~", FAIL: "✗", SKIPPED: "·", "UNATTESTED": "?"}


def render_text(v: dict) -> str:
    """Render the verdict as a compact, auditable text block."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"CALIBRATION DETERMINATION: {v['determination']}")
    lines.append(f"  run {v['run_id']}  ({v['iso']}: {v['label']})")
    yrs = ", ".join(map(str, v["scorable_years"])) or "none"
    lines.append(f"  scorable years: {yrs}")
    if v["data_blocked_years"]:
        lines.append(
            "  data-blocked years: " + ", ".join(map(str, v["data_blocked_years"]))
        )
    lines.append("=" * 72)
    _TIER_TAG = {TIER_LOAD: "LOAD", TIER_SUPPORT: "SUPP", TIER_PROTECT: "PROT"}
    for cid, c in v["criteria"].items():
        gate = _TIER_TAG.get(c.get("tier"), "?")
        kind = f" [{c['caveat_kind']}]" if c.get("caveat_kind") else ""
        lines.append(
            f"[{_MARK.get(c['status'], '?')}] {c['status']:7s} {gate:4s}  "
            f"{c['label']}{kind}"
        )
        for r in c["records"]:
            if r["status"] == PASS:
                continue  # keep the block focused on what isn't a clean pass
            key = f" {r['key']}" if r.get("key") else ""
            yr = f" {r['year']}" if r.get("year") else ""
            cls = f"  [{r['classification']}]" if r.get("classification") else ""
            lines.append(f"        {r['status']:7s}{yr}{key}: {r['magnitude']}{cls}")
            if r.get("ledger_reason"):
                lines.append(f"          ledger: {r['ledger_reason']}")
    lines.append("-" * 72)
    fcs = v.get("free_class_score")
    if fcs:
        lines.append(f"D-10 free-class C1: {fcs['headline']}")
        if fcs.get("excluded_from_free"):
            lines.append(
                "  pinned (excluded from free): " + ", ".join(fcs["excluded_from_free"])
            )
    if v["reasons"]:
        lines.append("determination basis:")
        for rsn in v["reasons"]:
            lines.append(f"  - {rsn}")
    else:
        lines.append("determination basis: all criteria pass, governance attested.")
    if v.get("notes"):
        lines.append("notes:")
        for note in v["notes"]:
            lines.append(f"  - {note}")
    lines.append("=" * 72)
    return "\n".join(lines)


def headline(v: dict) -> str:
    """One-line determination headline for the calibration-report skill output."""
    extra = f" — {v['reasons'][0]}" if v["reasons"] else ""
    return f"DETERMINATION: {v['determination']} [{v['iso']} {v['label']}]{extra}"


# ---------------------------------------------------------------------------
# Plaintext metrics sidecar (G-49, docs/verifying-dashboard-numbers.md
# "Proposed improvement: a plaintext metrics sidecar")
# ---------------------------------------------------------------------------
def condensed_metrics(v: dict) -> dict:
    """Condense a full verdict to the headline numbers a verifier checks first.

    Drops the per-class/per-year ``records`` detail that already lives in
    ``SUMMARY*.md`` / ``legitimacy_diagnostics.json`` / the ``runs/<id>.js``
    payload, keeping only the aggregate determination and per-criterion
    status — small enough to ``git show`` or ``jq`` directly.
    """
    return {
        "run_id": v["run_id"],
        "iso": v["iso"],
        "label": v["label"],
        "target_years": v["target_years"],
        "scorable_years": v["scorable_years"],
        "data_blocked_years": v["data_blocked_years"],
        "rubric_version": v.get("rubric_version", 1),
        "determination": v["determination"],
        "reasons": v["reasons"],
        "notes": v.get("notes", []),
        "criteria": {
            cid: {
                "label": c["label"],
                "tier": c.get("tier"),
                "status": c["status"],
                **({"caveat_kind": c["caveat_kind"]} if c.get("caveat_kind") else {}),
            }
            for cid, c in v["criteria"].items()
        },
        "caveats": v["caveats"],
        "grade_summary": v.get("grade_summary"),
        "free_class_score": v["free_class_score"],
    }


def bundle_dir_for(run_id: str) -> Path:
    """Return the repo-relative bundle directory a run id's sidecar points at."""
    sidecar = json.loads((REGISTRY_DIR / f"{run_id}.json").read_text())
    return REPO / sidecar["bundle"]


def write_metrics_sidecar(bundle_dir: Path, v: dict) -> Path:
    """Write the condensed metrics sidecar into ``bundle_dir/metrics.json``.

    This scorer remains the authoritative *generator*: the sidecar is its own
    condensed output, never a hand-maintained duplicate.
    """
    path = Path(bundle_dir) / "metrics.json"
    path.write_text(json.dumps(condensed_metrics(v), indent=2) + "\n")
    return path


def main() -> None:
    """CLI: score one run (by bundle dir or run id) and print its determination."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "run",
        nargs="?",
        help="bundle dir (results/calibration/<name>) or a run id",
    )
    ap.add_argument("--run-id", help="run id (alternative to the positional bundle)")
    ap.add_argument("--json", action="store_true", help="emit the machine verdict JSON")
    ap.add_argument(
        "--write-metrics",
        action="store_true",
        help=(
            "also write the condensed metrics.json sidecar (G-49) into the "
            "run's bundle dir"
        ),
    )
    args = ap.parse_args()
    target = args.run_id or args.run
    if not target:
        ap.error("provide a bundle dir or --run-id")
    run_id = args.run_id or resolve_run_id(target)
    verdict = determine(run_id)
    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_text(verdict))
    if args.write_metrics:
        path = write_metrics_sidecar(bundle_dir_for(run_id), verdict)
        print(f"wrote {path.relative_to(REPO)}")
    # Exit nonzero on NOT-YET so a CI gate / the forecast-validation check can
    # assert on the determination directly.
    sys.exit(0 if verdict["determination"] != NOT_YET else 1)


if __name__ == "__main__":
    main()
