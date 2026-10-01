# OWNER-ASK (CAISO-98 / WP-3): rule-23 authorization to revise the CT_CHP steam-floor LEVEL derive

**Status: GRANTED at scope (a)+(b) (owner ruling, 2026-07-19 CAISO-101
session — delivered in-session via the owner question gate).** Both lenses of
the CT_CHP level defect re-derive as one rule-23 change per §3's
recommendation: (a) the loading-when-on statistic for CEMS-visible cogens and
(b) the EIA-923-delivery-anchored level for CEMS-invisible cogens, executed
per §5 (A/B probe, registered whatever the result). Original filing context
below is preserved verbatim.

## 1. What WP-3 would change (one derive statistic)

`scripts/data/derive_thermal_tranches.py` emits each CHP cogen's steam-host
operating floor as `p25_allhr_cf` — the **25th percentile of the plant's
all-hours available-CF distribution** (`_CHP_P25_ALLHR_PCTILE = 25`, lines
105-123), consumed by `ScenarioConfig.chp_steam_floor_p25` and surfaced as the
D-2 mechanism `chp_steam` (caiso-89). Outage hours drop out of the sample;
economic/host-driven offline hours count as zeros. For a genuinely flat steam
host the p25 keeps its online level; for a cogen that is online only a minority
of its available hours the p25 collapses toward 0.

WP-3 = replace that **level statistic** with one that matches the host's
**measured sustained operating conduct**, per rule 23 (a derive-script change
that re-derives because the *source-data evidence* says the statistic
mis-measures the class — **not** because a residual moved).

## 2. The source-data evidence (rule-23 citation — FINDING-caiso95 §5)

Measured against the metered CAISO CT_CHP fleet (CAMPD CEMS `CA_{y}.parquet` +
EIA-923 classFull), 2023/2024/2025:

- **Loading-when-on is a baseload, not a p25 trickle.** The measured host runs
  at **≥70 % loading in 79 / 85 / 88 %** of its on-capacity-hours; the model's
  floor-carried class sits at **12-14 %** loading (~28 MW flat, ~40 % of the
  time on) — an 81-90 % floor-carried class whose *level* is wrong, not whose
  *mechanism* is wrong (rule 19 clean: one mechanism owns the class).
- **The measured host has a daytime hump** (32-70 MW avg by hod) the flat p25
  level misses.
- **Most of the gap is CEMS-invisible.** The class energy gap is
  **−1.84 / −1.76 / −1.08 TWh** (model − EIA-923 classFull), but the
  CEMS-visible slice is only ~0.4 TWh — i.e. **the bulk is CEMS-invisible
  cogens whose grid delivery the CEMS-based p25 statistic cannot see at all.**
- C5a mass: **−0.60 / −0.57 / −0.34 Mt** (× eGRID intensity 0.32-0.33 t/MWh) —
  small but chronic, and structurally the cleanest of the three C5a components.

Every number above is measured conduct / metered delivery. None is a price or
volume residual. This satisfies the rule-23 admissibility test: the revised
statistic would regenerate for a forward year from the same CEMS/EIA-923
drivers and respond to a changed host operating pattern.

## 3. Candidate replacements (owner picks the approach — flagged, not chosen)

The evidence splits into two defects with two different fixes; the owner should
rule on scope:

- **(a) CEMS-visible under-loading (the ~0.4 TWh slice).** The p25-of-all-hours
  statistic under-states a host that runs a high baseload when on. A faithful
  replacement is a **loading-when-on** construction: floor ≈ (measured on-hour
  frequency) × (p50 loading-conditional-on-online), which reproduces §5's
  "≥70 % in 79-88 % of on-hours" directly, instead of the p25 that mixes
  offline zeros into the level. (A simple percentile bump p25 → p50 does *not*
  fix it — it still averages the offline zeros; the statistic has to condition
  on being online.)
- **(b) CEMS-invisible cogens (the −1.4 to −1.8 TWh bulk).** These plants never
  enter the CEMS-based derive at all, so no CEMS-percentile change reaches
  them. Closing this needs an **EIA-923-annual-delivery-anchored** steam floor
  for the CEMS-absent CHP plants (implied baseload = 923 net generation spread
  over the host's operating profile). This is the larger, and larger-scope,
  half — it adds an EIA-923 branch to the CHP-floor derive, not just a
  parameter edit.

**Recommendation:** authorize **both (a) and (b)** as one rule-23 re-derivation
(they are the same class's level defect from two data lenses), OR authorize
(a)-only as the minimal, mechanically-trivial first step and hold (b) for a
follow-up if the owner wants the smaller change first. Either way the D-2
mechanism (`chp_steam`) and its window are unchanged — only the level moves.

## 4. Guardrails already established (do NOT redo — from FINDING-caiso95 §8)

- Do not cut the caiso-92 measured CT offer multipliers (rule 23 — the CT rungs
  are measured and are not the CT_CHP defect).
- Do not add a new stacked floor (rule 19) — CT_CHP is already
  single-mechanism (`chp_steam`); WP-3 re-levels that mechanism, it does not add
  one.
- CT_CHP is **D-2 EXEMPT** as a CHP class (the C8 forced-share gate does not
  bind it), but a re-leveled floor must still clear the **D-1 diurnal-shape**
  gate — the daytime hump must not become a flat over-floor. This is the
  principal probe risk for WP-3 and the report-back must watch it.

## 5. If granted — the execution plan (per rule 15, register whatever the result)

1. Revise `derive_thermal_tranches.py` per the ruled approach, **citing §5's
   measured evidence in the commit** (rule 20: re-derivation commits cite the
   data change, not a residual).
2. Re-derive the CHP floors artifact; confirm the CT_CHP level now reproduces
   the measured loading-when-on baseload (and the EIA-923 delivery for the
   CEMS-invisible plants if (b) is in scope).
3. Probe-solve A/B on a fresh same-machine repro (A = the caiso-98 keeper
   recipe = `caiso98_repro_A`; B = A + the re-derived level), 2023-2025 in one
   bundle (rule 16), sequential (memory).
4. Pre-registered report-back: CT_CHP energy gap (−1.8/−1.8/−1.1 TWh) closes
   toward EIA-923; **C1 must hold 12/12**; C3c identical; C7/C8 PASS; **D-1
   CT_CHP diurnal shape must clear** (the daytime hump, no flat over-floor); no
   λ-ladder degradation (belly/evening unchanged — CT_CHP is a small class).
5. Register the result on the dashboard whatever it is (rule 15); score any
   verdict flip leave-one-year-out within 2023-2025 before promotion.

## 6. The ask

**Owner: do you authorize the WP-3 rule-23 re-derivation of the CT_CHP
steam-floor level, and if so, scope (a)-only or (a)+(b)?** Until ruled, this
stays PENDING and no derive-script change or WP-3 solve is made.
