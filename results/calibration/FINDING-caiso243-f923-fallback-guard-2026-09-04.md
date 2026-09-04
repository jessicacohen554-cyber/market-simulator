# FINDING — caiso-243: the F923 low-volume fallback defect is REPAIRED at its root cause, every pre-registered gate passes, the run is PROMOTED — and the session's own instrument was found broken and fixed before any result was read

**Session caiso-243, 2026-09-04. Branch `claude/caiso-f923-lowvolume-defect-dnegou`.**
Pre-registered in `PRECOMMIT-caiso243-f923-fallback-guard-2026-09-04.md`
(pushed to `origin` **before any solve-path code was written**) and
`PRECOMMIT-caiso243-ADDENDUM-recipe-repair-2026-09-04.md` (pushed **while the
solve was in year 2023, with no bundle output read**).

**ONE bundle, three years, one invocation** (rules 12/16):
`caiso243_b1_f923_fallback_guard` → run **`2026-09-04-caiso-243-b1-f923`**.
**NO control solve was spent** — G-CTRL took form 2 at the owner's choice.

**Keeper: `2026-09-03-caiso-241-b1-ctpeaker` → `2026-09-04-caiso-243-b1-f923`.**
Determination **UNCHANGED at NOT-YET**, C3a the sole load-bearing FAIL, C3c the
single ledgered caveat. CAISO holds **no `complete` and no `final` marker**; the
holdout spend freeze is **ACTIVE**; every read and the one solve stayed inside
**2023–2025**.

---

## §1 — HEADLINE

**Five results, in the order they were established:**

1. **THE DEFECT'S ROOT CAUSE IS ONE MISSING ARGUMENT, AND IT IS EVERY
   PLANT-LEVEL ISO'S.** `bins_to_fleet` constructed every `Generator(...)`
   without `state`, so `FleetArrays.state` was **empty on 100 % of the CAISO gas
   fleet — 1,453 of 1,453 LP rows, 29,278 MW** — and the F923 fallback's
   documented state-first donor tier, **the only tier carrying a
   distinct-reporter floor**, was skipped fleet-wide. The same on PJM, MISO,
   NYISO and NEISO, whose keepers all run `plant_level_fleet=True`.
2. **THE REPAIR IS ARMED AT ZERO FREE PARAMETERS AND ITS FOOTPRINT WAS EXACT.**
   The coded mechanism reproduces the pre-registered footprint **byte for byte
   in all five G-STRUCT cases**.
3. **EVERY PRE-REGISTERED GATE PASSES**, and the two inert years are inert
   **exactly**, not merely inside tolerance: 2023 and 2024 reproduce the
   predecessor at **0.000 TWh in every class and 0.000 $/MWh**, with the zonal
   price arrays **bit-identical**.
4. **THE PROMOTION BASIS IS STRUCTURAL AND EXCLUDES C3a BY PRE-REGISTRATION.**
   C3a-2025 improves **+15.5 % → +14.4 %** and no verdict flips anywhere. That
   is a disclosure, not the case.
5. **THE SESSION FOUND ITS OWN INSTRUMENT BROKEN AND SAID SO BEFORE READING ANY
   RESULT.** Every zero-LP probe in this lane since caiso-202 rebuilt the keeper
   recipe on a lookalike config. Fixed, re-measured, envelope **tightened**, and
   the consequence for caiso-242's published ratios filed as an owner ask.

---

## §2 — THE OBJECT, LOCATED IN CODE

### §2.1 — D1's root cause

`data/fleet/assembly.py::bins_to_fleet` built every generator of the CAMPD-bin /
`plant_level_fleet` path **without a `state` argument**; `Generator.state`
defaults to `""` and only the EIA-860 loader ever set it. Measured on the
keeper's own rebuild: **1,443 / 1,448 / 1,453 of 1,443 / 1,448 / 1,453** gas
rows empty in 2023 / 2024 / 2025. The `plant_level_fleet` docstring claims the
fleet *"retains its EIA plant code, plant group and state"*; it never did.

### §2.2 — The tier attribution, 2025 live months (Sep–Nov)

Only **7** CAISO-fleet gas plants report in F923 at all in 2023–2025. **Two zone
pools are pools of ONE in every one of the 36 months:**

| tier the keeper actually used | zone | MW | plants |
|---|---|--:|--:|
| zone pool = 2 | LA_BASIN | 9,027.5 | 48 |
| zone pool = 3 | NP15 | 8,564.9 | 66 |
| ISO-month default | ZP26 | 3,295.0 | 33 |
| **zone pool = 1 (55077, NV)** | **SP15_rest** | **2,445.1** | 6 |
| **zone pool = 1 (55985)** | **SDGE** | **2,194.3** | 20 |
| own | — | 2,921.0 (55077 itself: 370.1) | 7 |

The arithmetic proving the path is caiso-242's and stands: NV's ten reporting
gas plants that month are quantity-weighted at **$3.54** and CA's fifteen at
**≈$4.5**, so **neither tier could produce $96.161 except from a pool of one**.
**SDGE is the same structure with a sane donor** ($4.524 in November) — which is
precisely why a pool-of-one guard alone is a guard, and the state stamp is the
repair.

### §2.3 — Footprints, measured on the real seam (zero LP)

| form | rows | MW | months | Nov-2025 cap-wt $/MMBtu | note |
|---|--:|--:|---|---|---|
| **(a)** zone donor floor | 228 | 4,639.4 | 9–11 | 52.82 → 4.45 | the two pool-of-one zones only |
| **(c)** EIA-860 state | 1,364 | 25,526.9 | 9–11 | 13.48 → 4.38 | every CA plant → the 6-reporter state mean |
| **(a)+(c)** | 1,364 | 25,526.9 | 9–11 | **byte-identical to (c)** | (a) is inert on top of (c) |
| (b) ≤ 2 % / 2× | **0** | 0 | — | **misses the motivating row** (55077-Nov is 2.62 %) | not armed |
| (b) ≥ 5 % | 257 | 6,110.2 | 11 | 46.70 → 4.38 | not armed |

**2023 and 2024: 0 rows under every form** (12/12 overlay coverage). Non-gas
rows moved: **0**. By class, (c) moves CC_REGULAR 12,647.7 MW, CT_PEAKER
7,254.9, ST_GAS 2,946.8, CC_CHP 1,689.3, CT_CHP 988.2.

### §2.4 — Why (b) was not armed

Every candidate cut is a **new parameter pair with no measured identification**
(rule 5 `[R-NO-MAGIC]`) — the census sweep is a sensitivity table, not a
derivation — and **the tightest cut does not even catch the row that motivated
it**. The owner declined it; D3 stays an open ask.

---

## §3 — THE ARM

Two `ScenarioConfig` fields, both **ISO-generic, both default OFF** (every other
ISO's keeper replays byte-identical), **armed on CAISO alone** (rule 25):

* **`fleet_state_from_eia860`** — form (c), the root-cause repair of D1:
  `bins_to_fleet` stamps each generator's USPS state from
  `data/raw/eia-860/eia860_plant.parquet` (already a solve-path source), making
  the designed tier order reachable.
* **`nearby_fuel_price_zone_donor_guard`** — form (a), D2: the zone tier
  requires the **same registered floor** the state tier already carries
  (`nearby_fuel_price_min_state_plants`, resolved 2 on this lane).

**No new constant, no value chosen, ZERO free parameters** (rule 21). Rule 19
`[R-ONE-MECH]`: two defects, two mechanisms, each reconciled to the tier it
governs.

---

## §4 — GATES, ALL SCORED ARM − KEEPER. EVERY ONE PASSES.

| gate | verdict | measurement |
|---|---|---|
| **G-STRUCT** (pre-solve, zero LP) | **PASS** | the coded path reproduces the measured footprint **byte for byte** in all 5 cases (`_caiso243_gstruct_presolve.json`); flags-off byte-identical to HEAD |
| **G-CTRL, form 2** | **PASS** | 2023 and 2024 reproduce the keeper at **0.000 TWh in every class**, **0.000 $/MWh**, and a **max absolute zonal price difference of 0.0** — exact identity, not tolerance |
| **G-INERT** | **PASS** | 2025 moves (1,364 rows) |
| **G-C1** | **PASS** | 12/12, free 8/8, unchanged |
| **G-C3b / G-C8 / G-CAVEAT / G-C6** | **PASS** | **every scored criterion's verdict identical** to the keeper's; 1 ledgered / 0 protective; C6 attested |
| **G-C3a, envelope leg** | **PASS** | 2025 measured **−0.3867 $/MWh** inside the registered **[−2.5006, +0.3109]**; 2023/2024 exactly **0.000** |
| **G-C3a, verdict leg** | *deliberately excluded from the promotion basis* (§5.6/§5.7) | +3.9 PASS / +12.3 FAIL / **+14.4** FAIL (was +15.5); **no flip in any year** |

**G-CTRL form 4 is VOID BY ITS LETTER, and that is reported rather than used.**
One commit since the predecessor's `git_sha 607f9324` touched the solve path —
`b9384baf`, *"Apply ruff format"* — on `campd_bins.py` and `offer_curves.py`;
**both are AST-identical** to the keeper's blobs (`ast.dump` equality). The
falsifier as written fires, so the gate fell to **form 2**, which binds because
the arm has two measured-inert years, under the owner's caiso-241 §B2 carve-out:
*"an arm with even one inert year takes the caiso-240 dispatch-identity leg and
spends nothing."* **No LP was spent on a control.**

---

## §5 — THE DISPATCH RESPONSE, 2025

| class | Δ TWh |
|---|--:|
| import | **−0.4734** |
| CC_REGULAR | **+0.4423** |
| CT_PEAKER | −0.0301 |
| CC_CHP | +0.0296 |
| ST_GAS | +0.0107 |
| CT_CHP / COAL / solar | −0.0023 / −0.0007 / −0.0002 |

CC_REGULAR's monthly mean rises **Oct 4,476 → 4,770** and **Nov 5,348 → 5,744 MW**
(+396 MW), i.e. exactly where the defect was. Load-weighted system price
**39.748 → 39.361 $/MWh**.

---

## §6 — PREDICTIONS, SCORED AGAINST INTEREST

| # | prediction | verdict |
|---|---|---|
| **P-1** | inert years reproduce the keeper to 0.001 TWh | **HOLDS** — at **0.000**, exact |
| **P-2** | ΔC3a-2025 ∈ [−0.60, 0.00] **and** no C3a verdict flip in any year | **HOLDS** — −0.3867, verdicts PASS/FAIL/FAIL unchanged |
| **P-3** | ΔC3a-2023 = ΔC3a-2024 = 0.000 exactly | **HOLDS** |
| **P-4** | CC_REGULAR-2025 rises < 0.5 TWh **and** < 500 MW in November | **HOLDS** — +0.442 TWh, +396 MW. caiso-242's against-interest reading (cost misallocated *within* the class, no class-level hole) **survives its own test** |
| **P-5** | CT_PEAKER falls **and** imports fall by less than CC rises | **FALSIFIED on its second leg** — CT_PEAKER does fall (−0.030), but **imports fall 0.473 TWh against CC_REGULAR's +0.442 TWh rise**. §7.1 |
| **P-6** | no verdict change; C3c-2025 stays PASS at 0 h > $200 | **HOLDS** |
| **P-7** | the DOF ledger does **not** move | **HOLDS** — 9 entries / 6 residual, and it is **not** claimed as progress |
| **P-8** | G-STRUCT exact | **HOLDS** — byte-identical, 5/5 |

**Seven hold, one falsified.** The three written to be uncomfortable (P-2, P-4,
P-5) are the ones that constrain the claim, and **the falsified one is among
them**.

---

## §7 — DISCLOSURES AGAINST INTEREST

### §7.1 — P-5's second leg is falsified, and what it means

Imports fall by **more** than CC_REGULAR rises (0.473 vs 0.442 TWh). The
prediction assumed the repaired capacity would mostly return to its own class;
it instead displaces slightly more import energy than it adds. **This is the
first measurement of the displacement caiso-242 §2.5 predicted structurally** —
that an over-priced domestic offer surface makes imports win hours domestic gas
should win — and it lands on the standing, unfunded `IMPORT_TRANCHES[CAISO]`
object rather than on this repair.

### §7.2 — THE THIRD CONSECUTIVE FAVOURABLE DIRECTION

caiso-241, caiso-242 and caiso-243 have each had to disclose that their repair
moves C3a in the helpful direction. **Stated as such rather than hidden**: it is
a property of where this lane's remaining defects sit — every one an over-priced
or withheld domestic gas offer that lets imports win. Per rule 1 `[R-STRUCT]`
it is **never** an argument, and the promotion rule was fixed in advance to
exclude C3a's verdict in either direction.

### §7.3 — AN INSTRUMENT DEFECT IN THIS LANE'S OWN PROBE PATTERN

Full record: `PRECOMMIT-caiso243-ADDENDUM-recipe-repair-2026-09-04.md`, pushed
**while the solve was running and before any bundle output was read**.

Every `run_year(fleet_only=True)` probe in this lane **since caiso-202**
reconstructed the keeper recipe as *"the meta.json keys whose names match
`run_year`'s parameters"*, which **silently drops every key whose solve kwarg is
spelled differently** — above all `coal_prb_sigmoid_overrides` →
`prb_overrides`, the bag carrying **36 CAISO structural flags**
(`caiso_citygate_spot_level`, `capacity_deliverability_limits`, scarcity, the RA
bridge, hydro, measured heat rates, WEFOR, …). The sanctioned reconstruction,
`replay_keeper.build_kwargs`, was never used by a probe.

**How it surfaced:** the live replay logged *"hub-basis overlay (CAISO 2023,
**daily**): **1443** gas generators … winter max 24.75"*; every probe rebuild
logged *"**monthly**: **1401** … 28.08"*. **The keeper prices gas at the daily
spot level; the probes rebuilt it on the monthly survey.**

**Repaired and re-measured.** The object, its form, the inert years and every
gate survive; the numbers moved at the second digit, and the **envelope
tightened** from [−2.634, +0.311] to **[−2.501, +0.311]** *before* the solve was
read. The corrected rebuild now reproduces the live solve's own log lines
exactly.

**Consequence, filed and not minimised:** **caiso-242 §3's gas-basis identity
ratios (1.298 / 1.310 / 1.327) were measured against the wrong model gas series
and must be re-measured by their own lane before anyone cites them again.** That
session's §5 defect — this keeper's object — is **confirmed on-recipe** and needs
nothing.

### §7.4 — WHAT THIS DOES NOT REPAIR

**Plant 55077's OWN November row is untouched**: 370.1 MW of CC_REGULAR still
carries its reported $96.161/MMBtu (≈$736/MWh) for 720 hours, because tier 1
(*"the plant's own measured months win outright"*) is not a fallback. **Defect
D3 stays open**, sized at **0.27 TWh** of capability — 13 % of the caiso-242
headline. The 2025 overlay coverage gap (9/12) is likewise untouched, and the
CT_PEAKER volume object is not addressed at all.

---

## §8 — CROSS-ISO: MEASURED, FILED AS ASKS, NEVER ARMED (rule 25)

Gas plant-months 2023–2025 by each ISO's own plant set; "anomalous" = quantity
≤ 2 % of the plant-year median **and** price ≥ 2× its volume-weighted mean:

| ISO | plant-months | anomalous rows / plants | max $/MMBtu | rows > $20 | hub overlay |
|---|--:|--:|--:|--:|---|
| CAISO | 245 | 1 / 1 | 96.16 | 7 | **9/12 in 2025** |
| PJM | 894 | **4 / 3** | **191.64** | 14 | **none** |
| MISO | 3,832 | **12 / 9** | **198.46** | 79 | **none** |
| NYISO | 179 | 0 / 0 | 11.86 | 0 | yes |
| NEISO | 45 | 0 / 0 | 19.62 | 0 | yes |
| ERCOT | 813 | 1 / 1 | 56.36 | 15 | n/a (both flags off by design) |

**PJM and MISO have no hub overlay**, so their fallback layer is live in all 36
months, and their state tier is **equally empty**. Whether a pool-of-one zone
serves an anomalous row there is **their lanes' first probe**; both fields ship
default-off for them to arm on their own evidence.

---

## §9 — OWNER ASKS CARRIED

1. **D3, the 55077 own-row residual** (§7.4) — needs an identified volume
   threshold; the measured fact that the 2 % cut misses it is on the record.
2. **Re-run caiso-242's four probes on-recipe** before its §3 ratios are cited
   again (§7.3).
3. **Retire the probe pattern** — a shared helper for fleet-only rebuilds, so no
   future probe reconstructs a recipe by parameter name.
4. **The 2025 overlay coverage gap** (9/12), unchanged from caiso-242 ask 4.
5. **PJM / MISO exposure** (§8) — asks for those lanes.
6. **The DOF-provenance instrument** — re-filed, unmoved; this is the **sixth**
   consecutive repair the counter cannot see.
7. Unchanged from caiso-242 §10: the narrow-scope basis arm, the
   fuel-invariant-margin flatness, the residual CT_PEAKER root cause, caiso-238
   objects 3/4, the SoCalGas OFO arm, `IMPORT_TRANCHES[CAISO]`.

---

## §10 — DO-NOT-REDO ADDS

1. **The F923 fallback's D1 and D2 are CLOSED for CAISO.** The state tier is
   reachable and the zone tier is guarded. Do not re-propose either.
2. **Form (b) is REFUSED for now on rule 5**, and the refusal has a measured
   edge: the tightest swept cut misses the row that motivated the object. Any
   future proposal needs an *identified* threshold, not a swept one.
3. **`nearby_fuel_price_zone_donor_guard` is measured INERT on CAISO on top of
   the state stamp.** It is armed as the protective generic guard; do not
   re-test it as a CAISO lever.
4. **Never rebuild a keeper recipe by matching `run_year` parameter names.**
   Use `replay_keeper.build_kwargs` (§7.3).
5. **Never cite caiso-242 §3's basis ratios until they are re-measured
   on-recipe.** Its §5 defect is confirmed and needs nothing.
6. **G-CTRL form 4 is void whenever any solve-path file differs**, formatting
   included. Form 2 is available whenever an arm has an inert year, and it costs
   nothing.

---

## §11 — DELIVERABLES

`PRECOMMIT-caiso243-f923-fallback-guard-2026-09-04.md`;
`PRECOMMIT-caiso243-ADDENDUM-recipe-repair-2026-09-04.md`; this finding;
`scripts/probes/_caiso243_{fallback_footprint,price_envelope,gstruct_presolve,arm_vs_keeper}.py`
with their four artifacts; `scripts/gen_caiso243_attestation.py`;
`tests/unit/data/test_f923_fallback_guards.py`; two `ScenarioConfig` fields with
their CLI flags, replay overrides and cache-key registrations; two
mechanism-matrix rows with a cell in every ISO shard; run
**`2026-09-04-caiso-243-b1-f923`** (**keeper**).

**Next number: caiso-244.**
