# PRECOMMIT — nyiso-232: the ST_GAS econ bands carry ERCOT's de-leaked 1.21 multiplicatively

**Session** nyiso-232 · **ISO** NYISO · **Date** 2026-09-13 · **DATA PROFILE: nyiso**
**Incumbent keeper** `2026-09-13-nyiso231-anchor-span` (`results/calibration/nyiso231_anchor_span`),
UNCHANGED unless §8 says otherwise. **Rule 32 `[R-SHARD]` (a): the parent runs ZERO LP.**
Written and pushed **before** the arm is launched. Every number below is measured at zero LP by
`scripts/probes/_nyiso232_st_gas_phase0.py` (→ `_nyiso232_st_gas_phase0.json`) and the exposure
probe (→ `_nyiso232_exposure.json`), both committed with this document.

---

## 1. THE GATING QUESTION THE HANDOFF POSED, SETTLED FIRST AND AT ZERO LP

The handoff required, before any arithmetic is applied: **is this a rule 23 `[R-FROZEN-DERIVE]`
re-derivation, or a correction of a propagation the rule-25 de-leak missed?** And: the block claims
**two** identifications which now disagree — **which is load-bearing?**

### 1.1 It is a PROPAGATION MISS, not a re-derivation

Rule 23 governs re-deriving a **measured-behaviour parameter** from **source data**, and forbids
doing so "because a residual moved".

* The ST_GAS source data — `nyiso_campd_marginal_hr_summary.csv` p50s, n = 25 — is **UNCHANGED and
  untouched**. The `phys_*` keys keep it verbatim. Nothing is re-derived from a data source.
* What moves is a **borrowed multiplier applied on top of it**, whose numerator a governance action
  already removed elsewhere.
* Rule 23's own trigger is **not engaged**: no residual moved, and the change pushes price the
  **wrong** way for C3a in two of four years (§5). A rule written to stop residual-chasing cannot
  be the rule that blocks a change the residual argues against.

**What it actually is: an incomplete rule 25 `[R-ISO-SCOPE]` enforcement.** `_NYISO_OFFER_CURVE`'s
ST_GAS block states its own basis as the native steam marginal HR × *"the CC class's own defensible
reach ratio (CC econ_high **1.21** / native CC marginal 0.925 = 1.31×)"*. The **same file** says by
name that 1.21 is ERCOT's — *"the SAME fit ERCOT's keeper uses (committed 0.87 / econ_low 0.92 /
econ_high 1.21)"* — and records it as **REMOVED** under rule 25 (audit C-13, B-NYI-1), neutralized
to 1.00 with the exposed C3a hole ledgered as an OPEN ROOT CAUSE (issue #1344).

So **ST_GAS's econ bands contain ERCOT's 1.21 as a multiplicative factor.** The de-leak removed the
value from the cell where it was *written* and left it standing in the cell where it had been
*multiplied in*. Rule 26 `[R-DELETE]` — *"a deprecated parameter that still parses is a re-armable
answer key"* — one derivation step removed.

**The construction is verifiable, and I am correcting the handoff's precision.** The handoff says
the registered 1.08 matches the cited construction "to 0.2 %". That is **not any of the readings**:

| native steam marginal read | × reach 1.30811 | vs registered `econ_low` 1.08 |
|---|---:|---:|
| `phys_econ_low` 0.830 (the band dict) | 1.08573 | **0.531 %** |
| `phys_econ_high` 0.828 (the band dict) | 1.08311 | **0.288 %** |
| 0.825 (the run-28 note's own triple 0.818/0.825/0.830) | 1.07919 | **0.075 %** |

Every reading lands within **1 %** of 1.08 — which is what identifies the construction — and the
block's own stated form (*"~0.82–0.83 × 1.31 ≈ 1.08"*) is exact at the precision it states. The
file records **two different** native triples for ST_GAS, which is why a single-number claim was
never available. **On the CURRENT reach (1.00/0.925 = 1.08108) the same construction gives 0.8973 —
16.9 % away — so the registered band is not reproducible from the file's own inputs today.**

### 1.2 Of the two identifications, the CONSTRUCTION is load-bearing and the OUTCOME one cannot rescue it

The block also claims the level *"Recovers the legacy-steam under-run (2023 ST_GAS −1.26 → −0.01
TWh, near-EXACT → the flat measured band reproduces measured steam volume, **validating the level a
priori, not residual-fitted**)"*.

**That sentence settles it in the block's own words.** "Validating the level *a priori*" means the
value was fixed by the construction **first** and the volume agreement is **corroboration**. A
corroboration cannot be promoted to *the* identification once the construction fails, because doing
so inverts the epistemics: the value's basis would change from "derived from a stated construction"
to "selected because the model's output matched an actual". That is precisely rule 13
`[R-MEASURED]`'s forbidden move — *"rescaling an input so the model's output lands on the actuals"*
— and it fails rule 13's forward test outright, since a forecast year has no measured volume to
match against.

**Steelman, and why it fails.** One could argue the markup is unobservable in NYISO (no offer
disclosure), so dispatched volume is the only observable that constrains it, making the volume match
a legitimate measured identification. It is not: rule 13 asks *"could this same quantity be produced
for a forward year from forward drivers?"* An offer markup identified by matching modelled to
metered volume cannot be. It is an **outcome fed back in**.

**⇒ The load-bearing identification is broken, and the band is un-identified.** Under rule 21
`[R-DOF]`, a value that can only be defended by the residual it closes is an open root-cause issue,
not a parameter.

## 2. THE CONSTRUCTION — declared ex ante, and narrower than the handoff proposed

**`ST_GAS.econ_low := 1.0` and `ST_GAS.econ_high := 1.0`. Nothing else.**
Field `nyiso_st_gas_econ_bands_deleaked` (ScenarioConfig, **default off**, NYISO-gated, hard error
off-ISO and hard error without its `phys_*` basis; CLI `--nyiso-st-gas-econ-bands-deleaked`;
honoured on kwarg-**or**-field, with a fail-loud `run_year` guard for the `prb_overrides` no-op
seam). **ZERO new literals, ZERO free parameters, no DOF ledger entry, `authorized_price_tuning`
NONE** — 1.0 is the neutral rules 24/25 prescribe (*"generic fallbacks carry neutral (1.0) bands"*),
and it is the **identical remedy this same file applied, in this same audit**, to
`CC_REGULAR.econ_high` (1.21 → 1.00) and to `CT_PEAKER.econ_low`/`econ_high`. It is the exact
registered state CT_PEAKER carries today.

**Three constructions were on the table; this is why the other two were refused.**

1. **The handoff's: propagate the reach (0.8724 / 0.8973 / 0.9388).** REFUSED. The current reach's
   numerator — CC `econ_high` 1.00 — is a declared **neutrality placeholder**, not a measurement:
   the de-leak's own words are *"it neutralizes to the neutral 1.0 band"* with the hole left as an
   OPEN ROOT CAUSE. Propagating it dresses a placeholder as a derivation and invents three new
   literals where the chartered remedy invents none.
2. **`band := phys` (the nyiso-199 template).** REFUSED here. That cell sits at **R** with a stated
   re-test condition and an explicit *"never alone"*; and its ground (2) — a band the file declares
   a placeholder with a named missing input that now exists — does not transfer to ST_GAS, whose
   bands are declared a *derivation*, not a placeholder. It also zeroes the markup outright, which
   is the run-28 error (the bare CEMS marginal HR is the **cost**, not the **offer**).
3. **The neutral 1.0** — chartered, zero-literal, and it leaves a markup in place rather than
   stripping the offer to cost.

**`committed` AND `peak` ARE EXCLUDED — exactly as nyiso-199 excluded them, and the second exclusion
was found by measurement, not assumed.**

* `peak` 4.20 is the **$1,000-offer-cap scarcity wall** the file states it as, not the reach
  construction. Grounding it would delete a mechanism rather than repair a basis (rule 19).
* `committed` 1.05 sits **below** its own `phys_committed` 1.104, so its markup
  `max(0, mult − phys)` **clips to 0 in BOTH legs** — the leaked reach never reaches a margin
  there. What the multiplier still does at markup 0 is scale **FUEL**, so moving it to 1.0 would
  price the steam min-load block **9.4 % below its own measured burn** on no ground at all. The
  probe's first pass measured that at **−$4.09/MWh (2022)**, which is how it was caught. Excluding
  it is what keeps this a de-leak rather than a new fitted value.

**WHAT THIS DOES NOT DO, stated at the gate.** It does **not identify** ST_GAS's competitive markup.
There is nothing to identify it *with*: the de-leak declared CC's own markup un-identified, so
nothing can be transferred from it, and NYISO publishes no offer data. The markup identification
therefore remains an **OPEN ROOT CAUSE against NYISO scarcity/reserve (RCPF/AS) price formation,
issue #1344** — the same ledger entry the CC de-leak made. This removes a prohibited value and names
the hole; it does not fill it.

## 3. PHASE 0 — MEASURED, ZERO LP, ALL FOUR REGISTERED YEARS

On-recipe `fleet_only` rebuild through the sanctioned `replay_keeper.run_year_kwargs` +
`derived_run_year_inputs` path, control and arm, offer arrays diffed row-for-row.

**CONFINEMENT IS EXACT.** In every one of 2022/2023/2024/2025:

| | measured |
|---|---|
| non-`ST_GAS` offer max\|Δ\| | **$0.0000000000/MWh** over 665–671 matched rows |
| non-`ST_GAS` `pmax` max\|Δ\| | **0.0000000000 MW** |
| `ST_GAS` `pmax` total | **8902.4000 → 8902.4000 MW** |
| `ST_GAS` `committed` band mean offer | **Δ $0.0000** (byte-identical) |
| `ST_GAS` `peak` band mean offer | **Δ $0.0000** (byte-identical) |

**EFFECT, and why it is year-varying.** `gas_offer_net_revenue_margin` prices the removed markup at
the **solve year's own zonal anchor** (the mechanism this lane promoted yesterday), so one band edit
produces four different $/MWh deltas:

| year | ST_GAS econ offer ctl → arm ($/MWh) | Δ | ST_GAS econ energy (TWh) | **footprint** |
|---|---|---:|---:|---:|
| 2022 | 102.19 → 93.57 | **−8.61** | 4.426 | **38.1** |
| 2023 | 44.36 → 41.20 | −3.17 | 6.349 | 20.1 |
| 2024 | 44.87 → 42.07 | −2.80 | 5.696 | 16.0 |
| 2025 | 69.96 → 64.55 | −5.41 | 5.776 | 31.2 |

**A KNOWN, INTENDED STRUCTURAL CONSEQUENCE — DECLARED, NOT DISCOVERED.** `econ_low == econ_high` is
a flat econ ramp, so the 6-slice `econc00..05` smoothing ladder collapses to `econlo`/`econhi`:
**ST_GAS 88 → 44 LP rows**, identically in all four years. That is the state **CT_PEAKER already
carries**, and it is **faithful to the measurement** — the block itself calls the measured steam
ramp *"essentially FLAT (legacy steam part-load HR is no better than full-load, matching the
2023/24 SOM)"* and describes the 1.05 → 1.13 spread as imposed *"to keep a valid rising offer"*,
never as measured. The screen's gates are therefore written on per-(unit, band-family) aggregates,
because a row-for-row diff is not defined across the collapse.

**The field route is verified identical to the probe**: arming via the real
`nyiso_st_gas_econ_bands_deleaked` reproduces the probe's arm offer array to
**max\|Δ\| = 0.000000000000 $/MWh**, with the resolved bands reading
`committed 1.05 / econ_low 1.0 / econ_high 1.0 / peak 4.2`.

## 4. G-DRIFT (rule 29(b)) — RECORDED BEFORE THE ARM SOLVES, SO FORM 4 IS VALID

`git diff 0acedb7ea317b0cf2ac0b5b2d0149784abf7ae64 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` returns
**six** changed paths. Every one is classified **INERT for NYISO**:

| changed path | commit | classification |
|---|---|---|
| `data/fleet/campd_bins.py`, `data/fleet/eia860.py`, `data/outages.py` | `760012f7` (SPP-38 card A) | **INERT** — a cache-**keying** repair whose behaviour is reachable only under `eia860_vintage_tracks_solve_year`. The NYISO keeper records that flag **`False`** and `eia860_vintage_year` **`None`**, so the active EIA-860 directory is constant through the run and a directory-keyed cache is a strict no-op. Verified on the keeper's own `run_config.json`, not on the commit message. |
| `data/raw/_validation-source/actual_lmp.json` | same window | **INERT** — benchmark data, never a solve input; and **0** of its +640 added lines contain "NYISO". |
| `actual_lmp_hourly_MISO.parquet`, `actual_lmp_hourly_zonal_MISO.parquet` | same window | **INERT** — another ISO's benchmark (rule 25). |

**Corroborated empirically, which is stronger than the classification.** Re-scoring the committed
keeper at **this HEAD** reproduces the nyiso-231 log exactly — C3a 2022 **−9.9 %**, C1-2022
`CC_REGULAR` **+5.20 TWh / +3.9 pp**, C3b-2022 **0.209**, C1 20/21 free 14/15 — so the scoring path
is measured unmoved, not merely argued to be.

**⇒ ALL HUNKS INERT ⇒ rule 29(b) form 4 holds: the committed keeper IS the control. NO CONTROL
SOLVE IS SPENT.** (Reinforced by nyiso-231's measurement that the solver-version question is exactly
zero for NYISO — 52,560 zonal prices and 6,648,840 unit-hours identical to 1e-9.)

## 5. DIRECTION IS DISCLOSED, IT IS MIXED, AND IT IS THE HAZARD — NOT THE ARGUMENT (rule 1)

**On volume, the sign flips by year**, which corrects the handoff's framing (it cited a single
2024 under-run of 1.378 TWh; the scored grid-delivered C1 residual is −1.064 TWh):

| ST_GAS C1, model − actual | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| TWh | **−1.148** | **+1.989** | **−1.064** | −4.677 *(SKIPPED: preliminary EIA-923, 70 % of plants missing)* |

Cheaper ST_GAS runs more, which is **right** for 2022 and 2024 and **wrong** for 2023. The anchor
makes the effect largest exactly where the under-run is (2022, 2025) and smallest where the
over-run is (2023) — a consequence worth recording, **not a justification**, and it is not why the
change is made.

**On price the direction is uniformly adverse, and the exposure is large.** C3a currently reads
**−9.9 % (2022)** and **−5.9 % (2025)** inside a ±10 % band. The zero-LP exposure probe finds an
ST_GAS econ offer sitting inside the window the repair moves in **80.8 % of 2022 hours** and
**53.1 % of 2025 hours**, with the in-merit ST_GAS econ envelope widening **2.662 → 4.236 TWh**
(2022) and **3.905 → 5.718 TWh** (2025).

> **I therefore expect this screen to STOP on C3a-2022, and I am pre-registering that expectation
> rather than discovering it.** It is recorded here, before the solve, so the result cannot be read
> as a surprise and the gate cannot be re-cut afterwards.

**This mechanism MUST NEVER be proposed as a C1 or C3a lever.**

## 6. THE SCREEN — year, and the STOP gates, fixed before the solve

**SCREEN YEAR: 2022.** Named on the mechanism's **own measured footprint** (§3: 38.1, the largest of
the four by a clear margin over 2025's 31.2) exactly as rule 29 `[R-SCREEN]` clause (1) requires,
and **never** on the residual. One year, one arm, `--nyiso-st-gas-econ-bands-deleaked`, differenced
against the committed keeper (form 4, §4).

Rule 29: **the screen may kill an arm; it may never promote one.** No gate below reads the target
residual.

| gate | STOPS the arm if |
|---|---|
| **G-CONFINE** | any non-`ST_GAS` class's P1 energy moves by more than 0.5 % of ISO load, **or** `ST_GAS` `committed`/`peak` band energy moves in a way not attributable to re-dispatch (the offer arrays for those bands are byte-identical, §3) |
| **G-DEMAND** | served demand differs from the keeper's 2022 by more than 1e-4 TWh, **or** dump ≠ 0, **or** slack ≠ 0. *(Gate on SERVED DEMAND only — never on class-hours or non-gas mc: P1 mc is a BID cost, so a gas offer change legitimately re-prices other classes' committed tranches.)* |
| **G-MAGNITUDE** | ST_GAS P1 energy does **not** rise, or rises by more than the pre-solve in-merit envelope widening of **1.574 TWh** (§5). Direction and order of magnitude must match the pre-solve arithmetic. |
| **G-ROWS** | the solved ST_GAS row count is anything other than **44** (the declared ladder collapse, §3) |
| **G-NONTARGET** | any **non-target load-bearing** criterion flips **PASS → FAIL** on 2022 — i.e. C1 (a class other than `CC_REGULAR`/`ST_GAS`), C2, C3a, or C3b. *(C3b-2022 and C1-2022 `CC_REGULAR` already FAIL and cannot flip; C3c-2022 is an auto-ledgered caveat on an out-of-training year, rubric v3.6, and is not a gate.)* |

**Pre-registered disposition if G-NONTARGET stops on C3a-2022 ALONE.** The arm is **not promoted**
— a screen has no power to promote, and I will not override a gate I wrote. The session reports the
stop, the structural finding stands as documented, and the bundle is **pushed and retained** (rules
31 `[R-RETAIN]`, 34 `[R-SHARD-PROMOTABLE]`) so the question the owner's standing formula raises —
*"If structural integrity improves but gates regress that may still be a keeper"* — can be answered
**without a re-solve**. That is the owner's call, and §8 asks it explicitly. Naming the disposition
in advance is not re-cutting the gate: the gate still stops the arm.

**If every gate clears**, the full span `--years 2022 2023 2024 2025` is spent as ONE invocation and
ONE bundle (rules 16 `[R-ALLYEARS]`, 32(b) `[R-SHARD]`), covering the union of NYISO's registered
years (rule 35(b) `[R-PROMOTE]`: `{2022, 2023, 2024, 2025}`, enumerated from the registry **before**
anything is pruned).

## 7. RULES

1 `[R-STRUCT]` — structure first; the direction is disclosed as a hazard and is never the argument;
no band is swept against any gate, and the value is declared here before the solve.
13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — the outcome-based identification is refused as an outcome
fed back in; the measured `phys_*` basis is preserved untouched.
19 `[R-ONE-MECH]` — `peak` and `committed` excluded so nothing is repaired twice.
21 `[R-DOF]` / 24 `[R-REGISTRY]` — zero free parameters, zero new literals, no DOF entry; the field
is registered in `ScenarioConfig` and reaches `run_config.json`; a `prb_overrides`-only arming
raises rather than silently no-opping.
23 `[R-FROZEN-DERIVE]` — settled in §1.1: not engaged.
25 `[R-ISO-SCOPE]` — this IS the rule being enforced; the field hard-errors off-NYISO and no verdict
transfers (every other ISO's matrix cell is `U`).
26 `[R-DELETE]` — a removed value surviving inside a derived constant is removed, not re-levelled.
28 `[R-MECH-MATRIX]` — base row + a cell line in all seven shards, added in this same change.
29 `[R-SCREEN]` — phase 0 first; one screen year named on footprint; gates fixed here; G-DRIFT
recorded before the arm (§4) so form 4 is valid and no control solve is spent.
31 `[R-RETAIN]` / 34 `[R-SHARD-PROMOTABLE]` — the screen shard PUSHES its bundle; nothing is deleted
before the owner rules.
32 `[R-SHARD]` — the parent runs zero LP.

## 8. THE PROMOTION QUESTION THIS SESSION WILL ASK (rule 31)

Recorded now so it cannot be quietly dropped at the end: **if the screen stops only on C3a-2022 — a
structurally-correct de-leak that removes a rule-25-prohibited value and costs a load-bearing price
criterion on one out-of-training year — does the owner want it armed?** Rule 1 says a real market
behaviour stays in even when it makes the fit worse; the owner's standing formula says a gate
regression may still be a keeper. Both point one way, and neither is mine to decide.

---

# ADDENDUM A — OWNER RULING: **ARM IT.** The span is authorized and pre-registered here.

**Date** 2026-09-13 · appended **before** the span solve is launched, per rule 29 `[R-SCREEN]` and
rule 1 `[R-STRUCT]` (a value is declared ex ante, never selected against a gate).

## A.1 The ruling, and what it settles

The screen STOPPED on G-NONTARGET (C3a-2022 −9.86 % → −11.61 %) and §8 put the promotion question
to the owner verbatim. **The owner ruled: "Arm it."**

That is the disposition §8 named, and it is the one rule 1 `[R-STRUCT]` contemplates: *a real market
behaviour stays in even if it makes the fit worse — then fix the actual root cause.* **The gate is
NOT re-cut and the screen's STOP is NOT rescinded.** What changes is only who decided: a screen can
kill an arm and never promote one, and it did not promote this one — the **owner** did, on the
evidence the screen produced, which is exactly the division of authority rules 29 and 31 set up.

**The C3a-2022 miss is therefore a KNOWN, ACCEPTED and REPORTED cost, not a discovered one.** It was
pre-registered in §5 as the expected outcome before the solve; it is reported at full magnitude on
the determination basis; and it is **not** absorbed, re-banded, or argued away.

## A.2 The arming route — recipe-level, the minimal and reversible one

`nyiso_st_gas_econ_bands_deleaked` is armed **on NYISO's keeper recipe** (the CLI flag, recorded in
`meta.json` / `run_config.json`), and the `ScenarioConfig` dataclass default **stays `False`**.

Route chosen to match the sibling exactly: nyiso-231 armed `gas_offer_margin_zonal_anchor_vintage`
the same way ("ONE REGISTERED FIELD MOVES: False → True"), and NYISO's
`iso_configs._nyiso_config` `default_scenario_overrides` carries **only** two capacity-requirement
fields — no offer or anchor mechanism. So:

* **zero cache keys move** for any other ISO or any other run — every committed bundle stays
  byte-identical;
* the flip is **reversible** by dropping one flag, and `--no-nyiso-st-gas-econ-bands-deleaked`
  reaches the pre-arm posture and keeps its key;
* **no declared default flip** is spent, so the `(b′-1)` cache-key machinery is untouched.

## A.3 The span, pre-registered

* **ONE shard, ONE `--years 2022 2023 2024 2025` invocation, ONE bundle** (rules 16 `[R-ALLYEARS]`,
  32(b) `[R-SHARD]`), years sequential inside it (rule 12).
* **Year set enumerated BEFORE anything is pruned** (rule 35(b) `[R-PROMOTE]`, because the prune
  destroys the evidence): the union over **every** registered NYISO sidecar is
  **{2022, 2023, 2024, 2025}** — one registered run, `2026-09-13-nyiso231-anchor-span`, with no
  folded touchpoints. The span covers that union exactly, so rule 35(c) is met by the bundle itself
  and no stamped companion is needed.
* **ONE registered field moves**: `nyiso_st_gas_econ_bands_deleaked` `False → True`. Everything else
  is the incumbent keeper's recipe, replayed.
* The shard **pushes its bundle**, `dispatch/<year>_P1.parquet` included (rule 34
  `[R-SHARD-PROMOTABLE]`).

## A.4 WHAT IS PRE-REGISTERED AS EXPECTED — so the span cannot be read as a surprise

Stated before the numbers exist, from the screen's measured 2022 leg and phase 0's four-year offer
deltas (−$8.61 / −$3.17 / −$2.80 / −$5.41 per MWh):

1. **C3a-2022 FAILS at ≈ −11.6 %.** Measured on the screen. This is the accepted cost.
2. **C3a-2025 is the year at risk and is NOT yet measured.** It sits at −5.9 % with an econ-offer
   delta of −$5.41/MWh — 63 % of 2022's. A proportional move would land it near **−7 to −8 %**,
   inside ±10 %, but that is an extrapolation, not a measurement, and **2025 could also fail**.
3. **C3a-2023 / 2024 have the smallest deltas** (−$3.17 / −$2.80) against residuals of +0.6 % and
   +1.1 %, so both are expected to move *toward* zero and stay PASS.
4. **C1 should improve**: ST_GAS under-runs in 2022/2024/2025 and the arm adds ST_GAS energy.
   2023 is the exception — ST_GAS **over**-runs there (+1.989 TWh) and the arm makes that worse.
5. **C8/D-2 is the open flag** (§A.5).

**None of these is a gate.** The span is being spent on an owner ruling, not on a criterion, and
every one of these numbers is reported at full magnitude whichever way it lands.

## A.5 THE D-2 / C8 FLAG IS INVESTIGATED IN PARALLEL, AND IT IS NOT ASSUMED AWAY

The screen's arm read **C8 FAIL** (2022 ST_GAS forced share 33.6 % > 30 %), driven **entirely** by a
denominator that reconciles with no dispatch-side measurement in either leg (RESULT §7). **C8 is
PROTECTIVE tier, and the caveat budget for protective caveats is ZERO** — so if the span reproduces
it, the promoted keeper reads **NOT-YET** on that basis, independently of C3a.

That is too important to leave at "uncorroborated". The parent therefore **investigates D-2's
denominator at zero LP while the span solves**, on the two bundles already on disk. The three
possible outcomes are named here, before the investigation, so the conclusion cannot be fitted:

* **(i) a scorer defect in D-2's class attribution** under a tranche-structure change → the repair is
  the scorer's, it is reported and handed to whoever owns `legitimacy_diagnostics.py`, and C8 is
  re-scored on the corrected basis;
* **(ii) a real forced-share increase** → C8 genuinely fails, the keeper reads NOT-YET on a
  protective criterion, and that is reported as the cost of the arming rather than worked around;
* **(iii) unresolved** → it is reported as unresolved and the keeper carries the C8 failure at full
  magnitude.

**No outcome is allowed to be selected by what it does to the determination**, and the arming
proceeds either way because the owner ruled on the mechanism, not on the score.

## A.6 WHAT THE PROMOTION WILL AND WILL NOT CLAIM

The keeper will be promoted with its determination **reported as measured**, whatever that is. If
the span reads NOT-YET — on C3a-2022, on C8, or both — **it is promoted as a NOT-YET keeper and
said so plainly**, because the owner armed a structural repair and rule 1 `[R-STRUCT]` says a run is
a keeper for being the most structurally faithful, not for having the lowest residual. **No caveat
is ledgered that the rubric does not itself grant, and no gate is re-read.**
