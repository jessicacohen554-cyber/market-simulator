# PREREG miso-191 — BINNING-AWARE PARTIAL-PLANT EXIT TIMING: the miso-190 exit-cohort delivery repair (FINDING-miso190 §4 form (a), frozen ex ante)

**Session miso-191 (2026-08-30).** Registered **BEFORE the mechanism exists
and before any adjudicating quantity is computed** (the phase-0
characterization quantities restated below were computed first and are
committed in `_miso191_binning_phase0.json`; no A/B leg exists and no gate
quantity of §4 has been computed). Target: the **FINDING-miso190 §4 named
successor** — binning-aware unit-grain exit timing for the partial-plant
exit set — on the keeper `2026-08-30-miso-188-rvsscope` (bundle
`miso188_rvs_B`), determination NOT-YET on {C3a-2025 −12.2965 %}, C1 16/16
all / 12/12 free, C3c the single ledgered caveat, DOF ledger 36/2.
**Charter:** the miso-191 handoff prompt, ask B — *"execute the
BINNING-AWARE partial-plant exit repair (the FINDING-miso190 §4 named
successor — GRANTED BY THIS PROMPT)"*. Like miso-190's, this is a **rule-14
MEMBERSHIP/DELIVERY repair (structural integrity), not a C3a-2025 lever**;
the owner's standing posture directive applies (*"If structural integrity
improves but gates regress that may still be a keeper"*, sittings
2026-08-25/-30, **re-affirmed by the owner in this session**) — to
scored-face regressions on a structurally-clean arm, never to a failed
witness.

**Mechanism-in-kind boundary (rule 28 decidability).** NO new
`ScenarioConfig` field: the repair rides the EXISTING gated
**`partial_plant_exit_carry`** (rule 19 `[R-ONE-MECH]` and the handoff's
explicit instruction — one field for one phenomenon; the miso-190 cell `R`
is re-tested WITH the new evidence this charter constitutes). The
identification — membership rule, oracle form, status set, timing source,
supply-code registry — is **PREREG-miso190 §1 and §3 VERBATIM, carried in
full and not re-argued here**: every input is the same published EIA-860
record, zero fitted scalars, no threshold, no per-unit hand-list. What
changes is ONLY the **fleet-side delivery**: the injected units must
survive `fleet_to_bins`, which today pools them into their surviving
plants' bins and discards the per-unit retirement before the COD ramp can
see it (FINDING-miso190 §3–§4).

## 0. What has been looked at, and what has not (the pre-registration boundary)

Phase-0 (this session, zero-solve, committed sources only; probe
`scripts/probes/_miso191_binning_phase0.py` → committed record
`results/calibration/_miso191_binning_phase0.json`) computed, before this
document:

* **Ask A validation:** `calibration_verdict.py --run-id
  2026-08-30-miso-188-rvsscope` reproduces the registered determination
  exactly (NOT-YET on {C3a-2025 −12.3 %} alone; C1 16/16 · 12/12 free; C3c
  the single ledgered caveat; C6 attested; C8 PASS all years with the 2025
  ST_GAS grounded note).
* **The binning-path study** (`fleet_to_bins` /
  `bins_to_fleet` / `cod_ramp.effective_cod` / the arrays COD-ramp block):
  the per-unit retirement dies at exactly one seam — `fleet_to_bins`
  aggregates per `(plant_code, plant_group)` and the tranche Generators are
  built with `retirement_year=None`, so `effective_cod` falls back to the
  plant-collapsed map. The per-unit preference seam (`effective_cod` lines
  "when the generator carries its own per-unit retirement, prefer it") is
  live and untouched — it only needs tranches that CARRY the retirement.
* **Witness ceilings** (committed operable snapshot, MISO BA, OP rows,
  net-summer basis — the loader's pmax): per witness plant, the surviving
  same-technology capacity that bounds every post-exit month:
  994 AES Petersburg coal **1057.2 MW** (ST2 −421.8 from Jul-2023);
  1400 Teche gas-ST **0.0** (unit 3 −250.0 from Jul-2024);
  1702 Dan E Karn coal **0.0** (1A/1B/2A/2B −486.0 from Jun-2023);
  4014 Wheaton gas-CT **0.0** (1–4 −186.0 from Jun-2025);
  4041 South Oak Creek coal **616.0** (5+6 −496.0 from Jun-2024);
  6090 Sherburne County coal **1556.0** (unit 2 −682.0 from Jan-2024);
  6137 A B Brown coal **0.0** (1+2 −485.0 from Nov-2023);
  8056 Waterford gas-ST **417.3** (unit 1 −409.5 from Apr-2024).
* **Leg-2 pooling facts:** Big Cajun 2 (6055) keeps operable coal unit 3
  (551.3 MW) — the re-carried 2-1 (517.0) pools with it; Warrick (6705)
  keeps operable coal units 1/3/4 (538.7 MW) — the re-carried unit 2
  (126.4) pools with them. So leg-2 witnesses are frozen at **capacity
  grain via the dispatch parquet's FleetContext metadata** (per-unit
  `unit_ids` + `pmax_mw` — dispatch-independent, entailed by construction),
  not at dispatch-behavior grain.
* **Whole-plant staggered-exit census (the deliberate non-scope):** exactly
  TWO MISO whole-plant retiree plants carry more than one distinct exit
  month — Crawfordsville (1024, 2 units, 11.5 MW) and LaO Energy Systems
  (52006, 6 units, 384.0 MW). Cohort routing does NOT touch the whole-plant
  channel (both legs keep today's plant-collapsed timing there), and this
  measures what that leaves on the table: ≤ 395.5 MW of small-plant timing
  heterogeneity, disclosed, not chartered.
* **Environment facts:** 15 GB RAM / 4 cores; the 8 GB swapfile +
  `MALLOC_ARENA_MAX=2` + `MARKET_SIM_HIGHS_THREADS=4` miso-169 recipe is
  applied before any leg, and `swapon --show` is RE-CHECKED before the arm
  leg (the miso-190 container-restart OOM lesson). Full data tree present,
  no new data fetch of any kind.

**No A/B leg has been solved; no gate quantity of §4 has been computed; the
mechanism code does not yet exist.** This PREREG is pushed and
blob-verified BEFORE the mechanism lands (the miso-188/190 order).

## 1. The form choice — FROZEN EX ANTE: form (a), date-scoped exit-cohort bins

FINDING-miso190 §4 names two admissible forms. **Form (a) is chosen and
frozen now**, before any leg: route the partial-exit rows into their OWN
date-scoped bins — one cohort bin per (plant × plant_group × retirement
month), so the injected rows never pool with the surviving plant's bins and
the existing `effective_cod` per-unit-retirement seam applies to their
tranches. The Grand Tower / Mystic topology generalized to (plant ×
exit-month) grain. Reasons (recorded in the phase-0 JSON verbatim):

1. **Rule 19 `[R-ONE-MECH]`.** The COD ramp is THE single COD/exit-timing
   mechanism for the whole fleet (the arrays.py COD block's own comment).
   Form (a) delivers unit-grain timing THROUGH it; form (b) — a monthly
   bin-capacity availability mask — would mint a second, parallel
   exit-timing channel for the same phenomenon.
2. **Blast radius.** Form (a) touches only the two fleet-build functions
   (`fleet_to_bins` aggregation key + retirement column carry;
   `bins_to_fleet` retirement stamp + a cohort bin-id suffix). Form (b)
   would thread a new mask through the vectorized availability builder,
   where it multiplies into outage overlays, seasonal derates and min_gen
   floors.
3. **Fidelity.** Under (a) the surviving plant's bin aggregates only
   surviving units — its capacity-weighted heat rate and tranche split are
   computed on the capacity that actually survives. Under (b) dead capacity
   stays inside the bin's heat-rate weighting and tranche percentages
   forever.
4. **Precedent.** The whole-plant retiree channel already validates the
   "retiree rows form their own bins and the COD ramp ages them out"
   topology in production keepers.

**Frozen scope of the cohort routing** (the anti-blast-radius line):

* Cohort routing applies ONLY to the leg-1 partial-exit injected units,
  identified by loader-stamped provenance (a `Generator.partial_exit_unit`
  bool, set exclusively by `load_retired_within_window` on the rows
  `_partial_plant_exit_rows` produced; read-only plumbing, not a config
  tunable — no residual can be closed by it, rule 24 unaffected).
* The whole-plant retiree channel keeps today's plant-collapsed COD timing
  in BOTH legs (identical to the keeper; the ≤395.5 MW disclosure above).
* Leg-2 OS/SB re-carries keep whole-year vintage scoping and pooling
  (they behaved in miso-190; unchanged code).
* Operable-fleet units with ANNOUNCED future planned retirements are
  untouched — routing them would restructure live plants' bins on
  announcement data, far beyond the charter.
* Naming: a cohort bin's unit ids are
  `{group}_{zone}_p{plant}_r{yyyy}{mm:02d}_{tranche}` (e.g.
  `COAL_MISO-West_p6090_r202312_committed`) — the `_p{plant}_` token is
  preserved so every existing plant-grain parser still resolves the plant,
  and the tranche suffix stays terminal for the `rsplit("_", 1)` tail
  consumers.

## 2. The work (mechanism first, then the A/B — both legs at ONE HEAD)

1. **`Generator.partial_exit_unit: bool = False`** — provenance field,
   stamped by `load_retired_within_window` on leg-1 partial rows only.
2. **`fleet_to_bins`** — when `config.partial_plant_exit_carry` is on, a
   generator with `partial_exit_unit` and its own `retirement_year`
   aggregates under `(plant_code, group, retirement_year,
   retirement_month)` instead of `(plant_code, group)`; the cohort row
   carries `Retirement_Year` / `Retirement_Month` columns (None on every
   other row and on the ERCOT curated path).
3. **`bins_to_fleet`** — reads the two columns (absent-tolerant), appends
   the `_r{yyyy}{mm:02d}` bin-id suffix, and stamps
   `retirement_year`/`retirement_month` on every tranche Generator of a
   cohort row. `effective_cod` then does the rest — **no change to
   `cod_ramp.py`, none to `arrays.py`.**
4. **Unit tests** — cohort key formation, retirement column carry, tranche
   stamp, bin-id form, byte-inertness with the flag off, and the
   whole-plant/leg-2 non-routing.
5. **Matrix duty (rule 28b)** — the existing `partial_plant_exit_carry`
   row/cell is RE-STAMPED with this charter's outcome in MISO's shard
   in-session (no new row: no new field).
6. **The A/B (§4)** — control + arm `replay_keeper` replays of
   `miso188_rvs_B`, both AFTER the mechanism push, at one HEAD.

## 3. Anti-sweep (binding)

PREREG-miso190 §3 carries in full: membership = the sheet complement;
timing = the sheet's own actual retirement month per unit; oracle = the
armed miso-188 form verbatim; supply codes = the unit's own `Energy Source
1` through the committed map, gated. **No CEMS quantity enters
membership**; no unit is added to or removed from any census because of
what a leg later shows; the Waterford-1 and Blue Lake accepted misses
stand; Dallman-3 and Weston-2 stay oracle-dropped whatever the residual
does. NEW and specific to this session: the FORM is frozen at §1 before
any leg — no switch to form (b), no hybrid, whatever the A/B shows (a
failed form (a) is reported as such and the cell stamped, never silently
re-formed); the cohort-routing SCOPE is frozen at §1 (no widening to the
whole-plant channel or to announced retirements after seeing a result);
the witnesses, gates and thresholds below are frozen; no alternative
statistic may be quoted after seeing a result. A result against interest
is reported at full magnitude. A missing/deficient input STOPs with the
deficiency disclosed.

## 4. The A/B (PREREG-miso190 §4 re-keyed to plant/capacity grain — the §5.1 vacuous-witness repair)

Control and arm are `replay_keeper` replays of `miso188_rvs_B` at one HEAD,
run SEQUENTIALLY (rule 12; miso-169 memory recipe), each the FULL span
2023 2024 2025 in ONE invocation (rule 16):

```
python3 scripts/replay_keeper.py results/calibration/miso188_rvs_B \
  --out-dir results/calibration/miso191_bax_A \
  --note "miso-191 CONTROL: byte-faithful keeper replay at HEAD (partial_plant_exit_carry default off)"
python3 scripts/replay_keeper.py results/calibration/miso188_rvs_B \
  --out-dir results/calibration/miso191_bax_B \
  --set partial_plant_exit_carry=true \
  --note "miso-191 ARM: partial-plant exit carry, binning-aware exit-cohort delivery (single delta; PREREG-miso191)"
```

Registration ids `2026-08-30-miso-191-control` / `2026-08-30-miso-191-bexit`
(a bundle-timestamp date shift is a naming deviation, disclosed, per the
miso-187/188/190 precedent) — **BOTH registered whatever the outcome**
(rule 15, full span, rule 16).

Witness grains, named once: **capacity grain** = the per-unit `unit_ids` +
`pmax_mw` lists in `dispatch/<year>_P1.parquet`'s FleetContext schema
metadata (dispatch-independent); **dispatch grain** = the same parquet's
hourly MW. A unit "of plant P, tech T" = unit_id prefix matches T's class
and contains the `_p{P}_` (or `_p{P}_r…`) token. **Every presence witness
asserts PRESENCE (fails on an empty match set)** — the miso-190 §5.1
vacuous-witness lesson, structurally enforced.

* **S-0 CONTROL INERTNESS (ABANDON).** Every scored sidecar of the control
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical to the committed keeper's (`miso188_rvs_B`). Anything
  else ⇒ HEAD drift — STOP, report, no arm conclusion (five consecutive
  sessions have reproduced committed values exactly; this gate
  adjudicates).
* **S-1 EXACTNESS (KILL).** The arm's `run_config.json` records exactly the
  single delta `partial_plant_exit_carry=true` (control false/absent).
  The flag demonstrably acted AT THE LP GRAIN:
  * **(a) COHORT PRESENCE (capacity grain):** for each of
    `(994, r202306)`, `(1400, r202406)`, `(1702, r202305)`,
    `(4014, r202505)`, `(4041, r202405)`, `(6090, r202312)`,
    `(6137, r202310)`, `(8056, r202403)`: at least one arm unit id carries
    `_p{plant}_r{tag}_` in EVERY solved year, and NO control unit id does
    in any year. Per-cohort arm pmax sum within ±2 MW of the exited MW
    (§0 table; tranche-dust tolerance).
  * **(b) UNIT-GRAIN EXIT TIMING (dispatch grain, the charter's own
    object):** every cohort unit's dispatch is EXACTLY 0 in every hour
    after its retirement month — `p6090_r202312`: all 2024 + 2025;
    `p1702_r202305`: Jun–Dec 2023 + all 2024/2025; `p994_r202306`:
    Jul–Dec 2023 + all 2024/2025; `p6137_r202310`: Nov–Dec 2023 + all
    2024/2025; `p4041_r202405`: Jun–Dec 2024 + all 2025; `p1400_r202406`:
    Jul–Dec 2024 + all 2025; `p8056_r202403`: Apr–Dec 2024 + all 2025;
    `p4014_r202505`: Jun–Dec 2025.
  * **(c) PLANT-GRAIN POST-EXIT CEILINGS (dispatch grain — the handoff's
    primary, form-independent):** in every post-exit month (after the
    plant's last exit month, within and after the exit year), the arm's
    hourly dispatch summed over the plant's same-tech units ≤ the §0
    frozen ceiling + 0.001 MW: 1702 coal ≤ 0 from Jun-2023; 6137 coal ≤ 0
    from Nov-2023; 6090 coal ≤ 1556.0 from Jan-2024; 994 coal ≤ 1057.2
    from Jul-2023; 4041 coal ≤ 616.0 from Jun-2024; 1400 gas-ST ≤ 0 from
    Jul-2024; 8056 gas-ST ≤ 417.3 from Apr-2024; 4014 gas-CT ≤ 0 from
    Jun-2025.
  * **(d) PLANT SURVIVAL (no whole-plant timeout):** plant 6090 same-tech
    (coal) dispatch > 0 in the arm in 2024 AND 2025; plant 4041 coal
    dispatch > 0 in the arm in Jul–Dec 2024.
  * **(e) ORACLE DROPS:** no arm unit id carries `_p963_r202403` (Dallman-3)
    or `_p4078_r202301` (Weston-2) in any year.
  * **(f) LEG-2 SCOPE (capacity grain, re-keyed from miso-190 S-1(e)):**
    plant 6055 coal pmax sum: arm = control + 517.0 ± 2 in 2023 AND 2024;
    arm = control ± 0.5 in 2025. Plant 6705 coal pmax sum: arm = control +
    126.4 ± 2 in 2023; arm = control ± 0.5 in 2024 and 2025.
  * **(g) miso-188 REGRESSION GUARD:** plant 862 (Grand Tower) total
    dispatch EXACTLY 0 in the arm in every year; plant 6155 (Rush Island)
    total dispatch nonzero in BOTH legs in 2023 and 2024.
  * Waterford-1 (8056) and the small-unit tail are gated only through
    (a)/(b)/(c); their dispatched MWh is REPORTED.
* **S-2 STRUCTURE (the charter's structural gate, miso-190 form
  verbatim).** The arm's 2023 combined coal-class energy (P1
  `class_hourly`, sum over `COAL_PRB` + `COAL_BIT` + `COAL_LIGNITE` + any
  bare `COAL` row) EXCEEDS the control's by **≥ 0.50 TWh**.
* **THE CHARTER KILLS (two-sided, fixed by the handoff).**
  1. **C3a-2025 must not regress:** |arm C3a-2025 %| > |control C3a-2025 %|
     + **0.10 pp** ⇒ REJECTED regardless of every other number.
  2. **Identification integrity (miso-188/190 form):** an arm whose scored
     2023 coal-side C1 improves while ANY S-1 clause fails is an
     unidentified level lever wearing a repair's name ⇒ REJECTED (rule 1's
     enforcement).
* **S-4 CONDUCT (KILL).** Zero NEW D-4 conduct failures on the arm's
  regenerated `legitimacy_diagnostics.json` vs the control's; C8 not FAIL
  in any year.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill).** The
  complete verdict scorer on both legs; every movement reported at full
  magnitude. **Declared adverse faces, measured not assumed (the handoff's
  own numbers):** the miso-190 arm moved C3a-2023 +3.50 → −0.52 and
  C3a-2024 −4.30 → −6.66 on ~7 TWh including phantoms — the phantom-free
  effect will be SMALLER but REAL and DOWNWARD in both years; report at
  full magnitude. **C3b-2025 flipped PASS→FAIL in the phantom arm — verify
  it stays PASS phantom-free.** Any gated-criterion PASS→FAIL flip in any
  year, or a C3a movement out of the commercial band in 2023/2024, fires
  the **owner-escalation path** — never an auto-reject and never an
  auto-keeper (a band exit is never self-adjudicated).

**Promotion rule (fixed now, PREREG-miso190 §4 re-keyed).** The arm is
promoted keeper **iff S-0 is clean, S-1 and S-4 are clean, S-2 passes,
both charter kills are silent, and S-5 records ZERO gated-criterion
PASS→FAIL flips AND no C3a band exit in 2023/2024** — the 2023 coal-class
C1 improvement is predicted but NOT required (rules 1/14; the owner's
standing posture directive covers a scored-face regression short of a
criterion flip or band exit). S-1 clean but S-2 failing ⇒ MIXED:
registered, cell `I`, keeper unchanged, owner escalation with both faces.
Any S-5 criterion flip or band exit ⇒ registered, keeper unchanged, **owner
escalation with the recommendation** (ask C: never self-adjudicate a
structural split). Any charter kill or S-1/S-4 firing ⇒ NOT promoted, cell
stays `R` with the new evidence cited. Registration + matrix stamp +
calibration-log entry in-session regardless of outcome; a promotion
re-stamps `keepers/MISO.json`, rebuilds `status/MISO.js`, and fires the
calibration-keeper-auditor. MISO holds no `complete`/`final` marker, so no
rule-22 D-5(b) re-key is owed. DOF ledger on promotion: one new entry,
identification MEASURED (EIA-860 actual retirement record + vintage status
+ energy-source codes), `n_scalars` 0, `n_residual` unchanged at 2 (ledger
36/2 → 37/2).

## 5. Instrument

`scripts/probes/_miso191_ab_gates.py` →
`results/calibration/_miso191_ab_gates.json` — the miso-190 scorer
re-keyed (KEEPER `miso188_rvs_B` / CONTROL `miso191_bax_A` / ARM
`miso191_bax_B`; the §4 witnesses at capacity/dispatch grain), committed
**after this PREREG and before it is run** (the miso-184 order). The
verdict-scorer step resolves registered bundles, so both legs are
registered before it runs (the miso-190 §5.2 order, disclosed there and
repeated here by design). If promoted, the attestation generator is
re-keyed from miso-188's with the new MEASURED ledger entry; the control
stays unattested.

## 6. DO-NOT-REDO and governance

**DO-NOT-REDO (miso-188 §6 + miso-189 + miso-190 carried in full):** the
offer family at BOTH grains (miso-179 `R` / miso-180 `I`);
`miso_south_firm_export_block` `G`; `miso_south_export_ladder_rt_tail`
`R`; `miso_seam_coincident_envelope` `R`; `measured_interface_limits` `R`;
`m2m_seam_entitlement_cap` `G`; `import_shape_lever` `G`;
`internal_congestion_split` `G`; `zonal_loss_surface` `R`;
`measured_offer_surface` `R`; `gas_hub_basis_overlay` `R` (with miso-189's
scarce-set corroboration); `ramp_envelopes` `I`; `dam_availability_rebasis`
`R`; the ordc/reserve and dispersion families; reserve-requirement raises.
The 2025 scarce N→S RDT residual stays the adjudicated
mc-idled/flat-stack MODEL-CLASS object — NOT re-opened here (this lever's
2025 face is 0.010 TWh of measured generation and every ≥40 MW unit exits
before the scarce window; charter kill 1 enforces it; ask D's object stays
in owner D-4 posture court). `retiree_vintage_status_scope`,
`unit_outage_fleet_status_scope`, `nuclear_unit_availability`,
`carry_operating_mothballs` are the keeper (`K`/armed) — not re-tested;
all ride unchanged in both legs. The miso-189 §7.3 marginal-vs-average
delivered-cost residue is OWNER COURT — untouched.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; freeze ACTIVE;
MISO holds NO marker (fail-closed); no new data fetch of any kind. Rule
12: years sequential within each leg; legs sequential; solves in-session,
never CI. Rules 5/13/14/19/23/24: the existing field, recorded in
`run_config.json`, no off-registry channel, zero new tunables (the
provenance bool is loader-stamped plumbing, not a knob). Rule 28: §5.4
queue stamp + calibration-log entry + MISO shard cell re-stamp adjudicated
in-session, negative outcomes included; `check_mechanism_matrix.py` before
every matrix push. Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed
blob ≥300 lines verified; on HTTP 408/500 set `git config http.version
HTTP/1.1` and retry before concluding anything. Rule 25: only MISO's
shard/keeper/status files. No new `.github/workflows`. THE OWNER MERGES;
no PR unless asked.
