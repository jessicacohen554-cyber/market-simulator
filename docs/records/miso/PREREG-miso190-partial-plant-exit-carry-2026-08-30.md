# PREREG miso-190 — PARTIAL-PLANT MID-WINDOW EXIT CARRY: the units retired 2023–2025 whose plants survive, injected at unit grain and timed out on their own actual EIA-860 retirement months

**Session miso-190 (2026-08-30).** Registered **BEFORE the mechanism exists
and before any adjudicating quantity is computed** (the phase-0
characterization quantities restated below were computed first and are
committed in `_miso190_partial_exit_phase0.json`; no A/B leg exists and no
gate quantity of §4 has been computed). Target: the **FINDING-miso188 §6.6
charter object** — the partial-plant mid-window exit gap — on the keeper
`2026-08-30-miso-188-rvsscope` (bundle `miso188_rvs_B`), determination
NOT-YET on {C3a-2025 −12.2965 %}, C1 16/16 all / 12/12 free, C3c the single
ledgered caveat, DOF ledger 36/2. **Charter:** the miso-190 handoff prompt,
ask B — *"execute the partial-plant mid-window exit repair (the
FINDING-miso188 §6.6 named-and-sized charter — GRANTED BY THIS PROMPT)"* —
explicitly a **rule-14 MEMBERSHIP repair (structural integrity), not a
C3a-2025 lever**; the owner's standing posture applies (*"If structural
integrity improves but gates regress that may still be a keeper"*, sittings
2026-08-25/-30).

**Mechanism-in-kind boundary (named now so rule 28 is decidable):** a NEW
gated `ScenarioConfig` field, **`partial_plant_exit_carry`** (default off,
byte-inert while off, default cache key unmoved), completing the
fleet-membership-by-contemporaneous-status family (rule 19 `[R-ONE-MECH]`:
one family, coverage extended, no new phenomenon owner) with its two
remaining blind spots, both adjudicated by the SAME instruments already
armed in this keeper's recipe:

* **Leg 1 — the retired-sheet gap.** `build_within_window_retirees` emits
  *whole-plant* exits only: any plant still present in the operable
  snapshot is dropped, because the plant-keyed COD map cannot time out a
  single unit. But `cod_ramp.effective_cod` **already prefers a
  generator's own per-unit retirement over the plant-collapsed date** (the
  Homer City repair, in its docstring) — the "un-maskable over-count" the
  builder feared has been maskable since that seam landed. When the flag
  is on, `load_retired_within_window` ADDITIONALLY reads the committed
  `eia860_generator_retired_and_canceled.parquet` (+ `eia860_plant.parquet`
  for the BA join), selects the ISO's units with actual
  `Retirement Year >= 2023` whose plant IS in the operable snapshot (the
  exact complement of the builder's filter — zero overlap with the
  whole-plant parquet by construction), builds them in the canonical
  schema (actual retirement → `planned_retirement_*`, `status` → OP,
  `operating_month` carried) and unions them into the channel **before**
  the armed `retiree_vintage_status_scope` oracle, which then scopes both
  memberships uniformly. Each injected unit ages out at unit grain on its
  own actual retirement month via the existing `effective_cod` per-unit
  preference — **no change to `cod_ramp.py`**.
* **Leg 2 — the snapshot-status gap.** `load_mothballed_but_operating`
  re-carries snapshot-OA units OP in the year-matched vintage; its
  docstring reserves OS/SB: *"deliberately out of scope: extending the
  channel needs its own probe."* This PREREG is that probe. When the flag
  is on, the snapshot status set widens from `{OA}` to `{OA, OS, SB}` —
  same vintage-OP oracle, same per-unit build from the vintage rows, same
  no-vintage-2025-carries-nothing owner default (the Cottonwood charter
  §10 accepted 2025 under-carry).
* **The reporting seam.** Coal plants unresolved by `coal_supply_class`
  (A B Brown 6137, Dan E Karn 1702) would land injected dispatch in a bare
  `COAL` class the EIA-923 bench never has. The fix is a **flag-gated
  registry** in `data/coal.py` (`register_partial_exit_coal_supply`),
  populated by the loader ONLY for injected units, from each unit's own
  committed `Energy Source 1` code via the canonical
  `COAL_CODE_TO_SUPPLY` (Brown BIT → bituminous, Karn SUB → prb),
  consulted after the three existing resolution sources. NEVER an ambient
  classifier change: the phase-0 census measured the ambient-extension
  blast radius anyway and it is EMPTY (zero current-fleet coal plants in
  any of the six ISOs are unresolved-with-a-retired-sheet-coal-row), but
  the gate is kept on principle — with the flag off the registry is empty
  and every path is byte-identical.

Rule 28(c) duties fire: one new matrix row + a cell line in every ISO
shard, in the same push as the field. Rule 25 `[R-ISO-SCOPE]`: the
mechanism is ISO-generic by construction (it reads each ISO's own rows) but
is tested and armed HERE for MISO only; every sister cell is minted `U`.

## 0. What has been looked at, and what has not (the pre-registration boundary)

Phase-0 (this session, zero-solve, committed sources only; probe
`scripts/probes/_miso190_partial_exit_phase0.py` → committed record
`results/calibration/_miso190_partial_exit_phase0.json`) computed, before
this document:

* **Ask A validation:** `calibration_verdict.py --run-id
  2026-08-30-miso-188-rvsscope` reproduces the registered determination
  exactly (NOT-YET on {C3a-2025 −12.3 %} alone; C1 16/16 · 12/12 free;
  C3c the single ledgered caveat; C6 attested; C8 PASS all years with the
  2025 ST_GAS grounded note).
* **The leg-1 census:** 59 MISO units / 3,999 MW summer on the committed
  retired-and-canceled sheet with actual retirement ≥ 2023 and a surviving
  plant — every FINDING-miso188 §6.6 named unit reproduced at unit grain
  (Sherco-2 682 MW ret 2023-12; SOC 5+6 496 ret 2024-05; A B Brown 1+2
  485 ret 2023-10; Dan E Karn 1A/1B/2A/2B 486 ret 2023-05; Petersburg-ST2
  422 ret 2023-06; Teche-3 250 ret 2024-06; Dallman-3 159 ret 2024-03),
  plus Waterford-1 409.5 ret 2024-03, Wheaton 1–4 ret 2025-05, Blue Lake
  1–4 ret 2025-05, Weston 2/31/32 ret 2023, and ~239 MW of <40 MW
  stragglers.
* **The armed-oracle verdicts on that census** (the SAME
  `retiree_vintage_status_scope` oracle, already on in this keeper):
  Dallman-3 is **dropped** (OS in vintage_2023 — and CAMPD-dark both
  years, the oracle exactly right), Weston-2 dropped (OS in
  vintage_2022, dark); every named runner is kept. Waterford-1 is kept
  (OP in vintage_2023) though CAMPD-dark — the Lansing-class accepted
  miss, disclosed in §1 and NOT patched.
* **The leg-2 census:** 31 MISO snapshot-OS/SB units OP in a year-matched
  vintage; at ≥40 MW exactly TWO — **Big Cajun 2-1** (517 MW coal, OS in
  snapshot, OP in vintage_2023 AND vintage_2024, the §6.6 named unit) and
  **Warrick 2** (126.4 MW coal, OS in snapshot, OP in vintage_2023 only —
  OA in vintage_2024, so carried 2023-only), plus ~133 MW of small units.
* **CAMPD sizing, unit-matched:** measured gross generation of the
  oracle-kept missing set = **7.683 TWh (2023) / 0.597 (2024) / 0.010
  (2025)**. The charter's 5.93 TWh (2023) reconciles EXACTLY as the named
  set MINUS Dan E Karn (5.933): the §6.6 sizing omitted Karn's 0.677 TWh
  under a CAMPD unit-id mapping gap (EIA generators 1A/1B/2A/2B vs CAMPD
  boilers 1/2), and omitted Warrick-2's 1.038 TWh (found by this census,
  not named in §6.6). 2024 reconciles directly (0.573 named vs 0.57
  quoted). The gap is real, **mostly a 2023 coal-side under-carry**, and
  lands on the classes the keeper under-carries: raw 2023 model−actual
  COAL_BIT **−5.765 TWh** / COAL_PRB **−2.212** vs the missing set's
  measured coal ≈ 5.9 (bituminous+unresolved) + 1.6 (prb) TWh.
* **Class landing at HEAD:** Sherco/SOC/Big Cajun → prb, Petersburg/
  Warrick/Dallman → bituminous, **A B Brown and Dan E Karn unresolved →
  bare COAL** (the registry's motivation); disjointness verified (zero
  units on both the operable and retired(≥2023) sheets — the two legs
  cannot double-inject); ambient-extension risk census EMPTY (above).
* **Environment facts:** 15 GB RAM / 4 cores; the 8 GB swapfile +
  `MALLOC_ARENA_MAX=2` + `MARKET_SIM_HIGHS_THREADS=4` miso-169 recipe is
  applied before any leg. Full clone, `data/raw` complete, no new data
  fetch of any kind.

**No A/B leg has been solved; no gate quantity of §4 has been computed; the
mechanism code does not yet exist.** This PREREG is pushed and
blob-verified BEFORE the mechanism lands (the miso-188 order, 1c00633
precedent).

## 1. The identification (measured, zero fitted scalars)

The dispatch fleet is missing real, running units through BOTH remaining
membership blind spots, and EIA's own record supplies each unit's exit at
month precision:

* A unit retired 2023–2025 whose plant survives leaves the operable sheet
  (it is retired), never enters the whole-plant retiree parquet (its plant
  survives), and cannot be represented by the plant-keyed COD map (its
  plant must stay online). Its actual `Retirement Year/Month` is published
  on the committed retired-and-canceled sheet — the same record, same
  vintage discipline, as the whole-plant channel's source. **Sherco-2
  alone is 682 MW that really generated 1.263 TWh in 2023.**
* A unit the snapshot marks OS/SB but the year-matched vintage marks OP is
  the exact status-symmetric case `carry_operating_mothballs` already
  covers for OA — the snapshot's contemporaneous judgment postdates the
  solve year, the vintage's does not. **Big Cajun 2-1 (517 MW) ran 0.335
  TWh in 2023 and 0.149 in 2024; Warrick-2 (126 MW) ran 1.038 TWh in
  2023.**

**Admissibility (rules 13/14):** every input is a published,
contemporaneous, forward-regenerable EIA-860 record — the actual
retirement date/month (a physical availability event, the same class as
outage windows), the vintage status sheet (the identical oracle three
armed mechanisms already read), and the unit's own energy-source code (the
identical fallback the whole-plant channel and the EIA-923 bench already
apply). Zero fitted scalars; no threshold, no size floor, no per-unit
hand-list — the membership rule is the sheet complement, the timing rule
is the sheet's own month, the status rule is the armed oracle. The
identification is year-independent (nothing is identified against any
year's outcome), so the standing LOYO note is satisfied structurally
(rules 20/22). Rule 13's forbidden line is respected: **no CEMS quantity
enters membership** — Waterford-1 (OP in vintage_2023, CAMPD-dark 2023)
and Blue Lake 1–4 (OP in vintage_2024, CAMPD-dark 2025) are carried by
the status record and their phantom risk is disclosed and accepted, the
Lansing precedent applied to the ADD side.

**A-priori scored-face expectation, declared now** (bases: the raw
model−actual class errors above; the miso-188 measured price slope of
~0.41 pp C3a per TWh of supply removed/added, 2.71 TWh → 1.10 pp):

* **2023 (the object's year):** coal classes rise toward actuals
  (COAL_BIT −5.77 and COAL_PRB −2.21 both move toward zero; COAL_PRB may
  overshoot positive — model in-merit dispatch of struggling coal
  typically exceeds its measured CF; band ±8 TWh holds it). **C3a-2023
  falls from +3.5008 %** — at the measured slope, ~6–8 TWh of in-merit
  supply is −2.5 to −3.3 pp, landing near 0 to +1; an overshoot below
  −5 % would be a band exit → S-5 escalation, declared possible but not
  expected. ST_GAS-2023 **rises from +4.06** (Teche-3, Waterford-1 —
  the declared adverse face; in-band). CC_REGULAR-2023 falls from −1.00
  (coal displaces CC — adverse direction, in-band).
* **2024:** CC_REGULAR-2024 falls from +6.820 (improves, further inside
  the band it just re-entered). COAL_PRB-2024 rises from −4.007 toward 0
  (Big Cajun 2-1 model-dispatched at merit; SOC Jan–May). **C3a-2024
  falls from −4.3034 — the ADVERSE face with band-exit risk declared at
  full magnitude:** the model already under-prices 2024, and adding real
  supply lowers prices further; at the measured slope, 2.5–5 TWh of
  in-merit additions is −1.0 to −2.1 pp, i.e. a landing between −5.3 and
  −6.4 is genuinely possible. Per §4 this fires the owner-escalation
  path, never an auto-reject and never an auto-keeper — rule 14's posture
  (a worse fit from an accurate input is a discovered miscalibration
  elsewhere, never a reason to bury the input) and the owner's standing
  structural-integrity directive are the adjudication frame.
* **2025:** near-zero face BY MEASUREMENT, not by construction (unlike
  miso-188): the oracle-kept set's measured 2025 generation is 0.010 TWh;
  the live 2025 capacity is Wheaton 1–4 (186 MW gas CT) + Blue Lake 1–4
  (147 MW oil) + Prairie Creek-1 (14.6 MW) through their 2025-05 /
  2025-12 exits, plus nothing from leg 2 (no vintage_2025). Every
  ≥40 MW unit is exited before the 2025 scarce set's summer window. The
  charter kill (§4) adjudicates any 2025 regression. **This lever makes
  no C3a-2025 claim** — ask D's object stays where miso-189 left it: the
  adjudicated mc-idled/flat-stack model-class residual, owner D-4 posture
  court.

## 2. The work (mechanism first, then the A/B — both legs at ONE HEAD)

1. **The field** — `ScenarioConfig.partial_plant_exit_carry: bool =
   False`, registered with the nyiso-119/caiso-186 discipline **in the
   same commit**: `_CACHE_KEY_OPTIONAL_FIELDS` entry, default-ledger
   `"False"` entry, measured-record entry ("EIA-860 actual retirement +
   vintage generator status"), and the dataclass docstring comment. No
   new CLI flag (the `replay_keeper --set` channel carries it, exactly as
   miso-186/187/188's fields).
2. **Leg 1** — `load_retired_within_window(...,
   partial_plant_exit_carry=False)`: when on, union the partial-plant
   exit rows (per §1's membership rule) into the channel frame BEFORE the
   vintage-status oracle; register the supply codes of injected coal
   plants unresolved at HEAD; INFO-log the injected units + MW per year.
   Threaded from `scripts/run_calibration.py` and `runner.py`'s backcast
   branch, gated on the field.
3. **Leg 2** — `load_mothballed_but_operating(..., status_scope)`: the
   snapshot status filter widens `{OA}` → `{OA, OS, SB}` when the field
   is on. Nothing else changes.
4. **The registry** — `data/coal.py::register_partial_exit_coal_supply`
   consulted as resolution source 4 in `coal_supply_class`; empty (and
   the function byte-inert) while the flag is off.
5. **Unit tests** — the membership complement, the per-unit exit timing
   through `effective_cod`, the leg-2 status widening, the registry
   gating, and byte-inertness with the flag off.
6. **Matrix duties (rule 28c)** — new row in
   `docs/codebase-site/data/mechanism-matrix.js` + a cell line in EVERY
   ISO shard (`U` for MISO pending the A/B; `U` for sisters);
   `scripts/check_mechanism_matrix.py` green before push.
7. **The A/B (§4)** — control + arm `replay_keeper` replays of
   `miso188_rvs_B`, both AFTER the mechanism push, at one HEAD.

## 3. Anti-sweep (binding)

The membership rule, oracle form, status set, timing source and registry
mapping are frozen by this document: membership = the ISO's
retired-and-canceled rows with actual retirement ≥ 2023 and plant present
in the operable snapshot (leg 1) plus snapshot-OS/SB-vintage-OP (leg 2);
exit timing = the sheet's own actual retirement month, per unit, via the
existing `effective_cod` preference; oracle = the armed miso-188 form
verbatim; supply codes = the unit's own `Energy Source 1` through the
committed `COAL_CODE_TO_SUPPLY`, gated. **No CEMS quantity enters
membership**; no unit is added to or removed from any census because of
what a leg later shows; the Waterford-1 and Blue Lake accepted misses
stand; Dallman-3 and Weston-2 stay oracle-dropped whatever the residual
does. No size threshold exists to sweep; no deriver is re-tuned; the
committed retiree parquet is NOT regenerated. The witnesses, gates and
thresholds below are frozen; no alternative statistic may be quoted after
seeing a result. A result against interest is reported at full magnitude.
A missing/deficient input STOPs with the deficiency disclosed.

## 4. The A/B (PREREG-miso188 §4 gates verbatim where they apply, re-keyed to this lever's structure and the miso-188 baselines)

Control and arm are `replay_keeper` replays of `miso188_rvs_B` at one
HEAD, run SEQUENTIALLY (rule 12; miso-169 memory recipe: 8 GB swapfile,
`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=4`), each the FULL span
2023 2024 2025 in ONE invocation (rule 16):

```
python3 scripts/replay_keeper.py results/calibration/miso188_rvs_B \
  --out-dir results/calibration/miso190_ppx_A \
  --note "miso-190 CONTROL: byte-faithful keeper replay at HEAD (partial_plant_exit_carry default off)"
python3 scripts/replay_keeper.py results/calibration/miso188_rvs_B \
  --out-dir results/calibration/miso190_ppx_B \
  --set partial_plant_exit_carry=true \
  --note "miso-190 ARM: partial-plant mid-window exit carry (single delta; PREREG-miso190)"
```

Registration ids `2026-08-30-miso-190-control` /
`2026-08-30-miso-190-ppexit` (a bundle-timestamp date shift is a naming
deviation, disclosed, per the miso-187/188 precedent) — **BOTH registered
whatever the outcome** (rule 15, full span, rule 16).

* **S-0 CONTROL INERTNESS (ABANDON).** Every scored sidecar of the
  control (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical to the committed keeper's (`miso188_rvs_B`). Anything
  else ⇒ HEAD drift — STOP, report, no arm conclusion (the miso-177 R-0
  discipline; miso-188/189 reproduced committed values exactly under
  disclosed toolchain point-version drift, and this gate adjudicates).
* **S-1 EXACTNESS (KILL).** The arm's `run_config.json` records exactly
  the single delta `partial_plant_exit_carry=true` (control
  false/absent); every other input byte-identical between legs. The flag
  demonstrably acted, witnessed from the legs' own
  `dispatch/<year>_P1.parquet` `unit_id` sets and hourly MW (frozen now;
  unit ids are `{plant_id}_{generator_id}`):
  * **(a) INJECTION (leg 1):** each of `6090_2`, `1702_1A`, `1702_1B`,
    `1702_2A`, `1702_2B`, `994_ST2`, `6137_1`, `6137_2`, `4041_5`,
    `4041_6`, `1400_3`, `8056_1` is PRESENT in the arm's unit set in
    every solved year and ABSENT from the control's in every year.
  * **(b) UNIT-GRAIN EXIT TIMING (the charter's own object):** in the
    arm, dispatch is EXACTLY 0 in every hour after each unit's actual
    retirement month — `6090_2`: all 2024 + 2025; `1702_*`: Jun–Dec 2023
    + all 2024/2025; `994_ST2`: Jul–Dec 2023 + all 2024/2025; `6137_1`/
    `6137_2`: Nov–Dec 2023 + all 2024/2025; `4041_5`/`4041_6`: Jun–Dec
    2024 + all 2025; `1400_3`: Jul–Dec 2024 + all 2025; `8056_1`:
    Apr–Dec 2024 + all 2025.
  * **(c) PLANT SURVIVAL (no whole-plant timeout):** plant 6090 total
    dispatch > 0 in the arm in 2024 AND 2025, and plant 4041 total
    dispatch > 0 in the arm in Jul–Dec 2024 — the surviving units keep
    running after the sibling's unit-grain exit, in the same LP.
  * **(d) ORACLE DROPS:** `963_3` (Dallman-3) and `4078_2` (Weston-2)
    ABSENT from the arm's unit set in every year.
  * **(e) LEG-2 SCOPE:** `6055_1` (Big Cajun 2-1) PRESENT in the arm in
    2023 and 2024 and ABSENT in 2025; `6705_2` (Warrick-2) PRESENT in
    2023 and ABSENT in 2024 and 2025. Both ABSENT from the control in
    every year.
  * **(f) miso-188 REGRESSION GUARD:** Grand Tower (plant 862) total
    dispatch EXACTLY 0 in the arm in every year (the armed oracle's
    drops persist under the widened membership); Rush Island (plant
    6155) total dispatch nonzero in BOTH legs in 2023 and 2024.
  * Waterford-1 `8056_1` and the small-unit tail are REPORTED (presence,
    windows, dispatched MWh), never gated beyond (a)/(b).
* **S-2 STRUCTURE (the charter's structural gate).** The arm's 2023
  combined coal-class energy (P1 `class_hourly`, sum over `COAL_PRB` +
  `COAL_BIT` + `COAL_LIGNITE` + any bare `COAL` row) EXCEEDS the
  control's by **≥ 0.50 TWh** — an order of magnitude under the missing
  set's 7.68 TWh measured gross (≈6.9 coal-side), the miso-188 floor
  discipline. (The class-sum form is frozen so the gate cannot be
  defeated or gamed by the PRB/BIT/registry split.)
* **THE CHARTER KILL (two-sided, fixed by the handoff).**
  1. **C3a-2025 must not regress:** |arm C3a-2025 %| > |control
     C3a-2025 %| + **0.10 pp** ⇒ REJECTED regardless of every other
     number (the handoff's own kill; the 0.10 tolerance is ~5× the
     largest cross-year pool interaction miso-188 measured, 0.022 pp).
  2. **Identification integrity (miso-188 form):** an arm whose scored
     2023 coal-side C1 improves while the S-1 witnesses show the flag
     did not act as specified (any S-1 clause failing) is an
     unidentified level lever wearing a repair's name ⇒ REJECTED
     (rule 1's enforcement).
* **S-4 CONDUCT (KILL).** Zero NEW D-4 conduct failures on the arm's
  regenerated `legitimacy_diagnostics.json` vs the control's; C8 not
  FAIL in any year.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill).** The
  complete verdict scorer on both legs; C3a all years, C1/C2/C3b/C3c/C4,
  every movement reported at full magnitude. Any **gated criterion
  PASS→FAIL flip in any year**, or a C3a movement out of the commercial
  band in 2023/2024 (the §1 declared risk on 2024), fires the
  **owner-escalation path** — never an auto-reject and never an
  auto-keeper (the miso-187 structural-split precedent: never
  self-adjudicated).

**Promotion rule (fixed now).** The arm is promoted keeper **iff S-0 is
clean, S-1 and S-4 are clean, S-2 passes, both charter kills are silent,
and S-5 records ZERO gated-criterion PASS→FAIL flips AND no C3a band exit
in 2023/2024** — the 2023 coal-class C1 improvement is predicted but NOT
required for promotion (rules 1/14: the membership correction is
structurally right whatever the residual does; the owner's standing
posture directive covers a scored-face regression short of a criterion
flip or band exit). S-1 clean but S-2 failing (the mechanism acted, the
coal total did not move) ⇒ MIXED: registered, cell `I`, keeper unchanged,
owner escalation with both faces. Any S-5 criterion flip or band exit ⇒
registered, keeper unchanged, **owner escalation with the recommendation**
(ask C of the handoff: never self-adjudicate a structural split). Any
charter kill or S-1/S-4 firing ⇒ NOT promoted, cell `R`. Registration +
matrix stamp + calibration-log entry in-session regardless of outcome; a
promotion re-stamps `keepers/MISO.json`, rebuilds `status/MISO.js`, and
fires the calibration-keeper-auditor. MISO holds no `complete`/`final`
marker, so no rule-22 D-5(b) re-key is owed. DOF ledger on promotion: one
new entry, identification MEASURED (EIA-860 actual retirement record +
vintage status + energy-source codes), `n_scalars` 0, `n_residual`
unchanged at 2 (ledger 36/2 → 37/2).

## 5. Instrument

`scripts/probes/_miso190_ab_gates.py` →
`results/calibration/_miso190_ab_gates.json` — the miso-188 scorer
re-keyed (KEEPER `miso188_rvs_B` / CONTROL `miso190_ppx_A` / ARM
`miso190_ppx_B`; the S-1 witnesses, S-2 class-sum form and charter kills
above), committed **after this PREREG and before it is run** (the
miso-184 order). If promoted, the attestation generator is re-keyed from
miso-188's with the new MEASURED ledger entry; the control stays
unattested.

## 6. DO-NOT-REDO and governance

**DO-NOT-REDO (miso-188 §6 + miso-189 carried in full):** the offer
family at BOTH grains (miso-179 `R` / miso-180 `I`);
`miso_south_firm_export_block` `G`; `miso_south_export_ladder_rt_tail`
`R`; `miso_seam_coincident_envelope` `R`; `measured_interface_limits`
`R`; `m2m_seam_entitlement_cap` `G`; `import_shape_lever` `G`;
`internal_congestion_split` `G`; `zonal_loss_surface` `R`;
`measured_offer_surface` `R`; `gas_hub_basis_overlay` `R` (now with
miso-189's scarce-set corroboration); `ramp_envelopes` `I`;
`dam_availability_rebasis` `R`; the ordc/reserve and dispersion families;
reserve-requirement raises. The 2025 scarce N→S RDT residual is the
adjudicated mc-idled/flat-stack MODEL-CLASS object — NOT re-opened here
(this lever's 2025 face is 0.010 TWh of measured generation and every
≥40 MW unit exits before the scarce window; the charter kill enforces
it). `retiree_vintage_status_scope`, `unit_outage_fleet_status_scope`,
`nuclear_unit_availability`, `carry_operating_mothballs` are the keeper
(`K`/armed) — not re-tested; all ride unchanged in both legs (the S-1(f)
witnesses pin the first; leg 2 EXTENDS `carry_operating_mothballs`'
status set under the new flag without touching its OA behavior).
`mustrun_online_frac_per_year` `R` — untouched (this lever changes no
floor and no online_frac). The miso-189 §7.3 marginal-vs-average
delivered-cost residue is OWNER COURT — not a lane lever, untouched.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; freeze
ACTIVE; MISO holds NO marker (fail-closed); no new data fetch of any kind
(all sources committed). Rule 12: years sequential within each leg; legs
sequential. Rules 5/13/14/19/23/24: per §1; the field is registered
(4-site discipline, same commit), recorded in `run_config.json`, no
off-registry channel; the registry carries no tunable value (committed
code mapping, gated, empty when off). Rule 28: §5.4 queue stamp +
calibration-log entry + MISO shard cell (new row) adjudicated in-session,
negative outcomes included; `check_mechanism_matrix.py` before every
matrix push. Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed blob
≥300 lines verified; on HTTP 408/500 set `git config http.version
HTTP/1.1` and retry before concluding anything. No new
`.github/workflows`. THE OWNER MERGES; no PR unless asked.
