# FINDING miso-191 — the binning-aware exit-cohort delivery WORKS and is PROMOTED KEEPER (`2026-08-30-miso-191-bexit`) under the owner's in-session directive; the probe's mechanical kill-2 REJECT stands on the record, fired by two witnesses this session mis-froze

**Session miso-191 (2026-08-30/31).** Charter: the FINDING-miso190 §4 named
successor — binning-aware unit-grain exit timing for the partial-plant exit
set — granted by the miso-191 handoff. PREREG:
`PREREG-miso191-binning-aware-exit-2026-08-30.md` (pushed + blob-verified
BEFORE the mechanism existed; merged to main as PR #4379 before the legs).
Phase-0: `_miso191_binning_phase0.json`. Gates record:
`_miso191_ab_gates.json` (UNALTERED — its mechanical verdict stands).
Runs `2026-08-30-miso-191-control` (`miso191_bax_A`) /
`2026-08-30-miso-191-bexit` (`miso191_bax_B`, THE KEEPER) — both registered
per rule 15.

## 1. Ask A — zero-solve validation

PASS. `calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope`
reproduced the registered determination exactly: NOT-YET on {C3a-2025
−12.2965 %} alone; C1 16/16 all / 12/12 free; C3c the single ledgered
caveat; C6 attested; C8 PASS all years.

## 2. Phase-0 (zero-solve, committed before the PREREG) and the form freeze

The binning-path study localized the defect to ONE seam: `fleet_to_bins`
aggregates per `(plant_code, plant_group)` and builds tranche Generators
with `retirement_year=None`, so `effective_cod` falls back to the
plant-collapsed map — the per-unit preference seam itself was live and
untouched, needing only tranches that CARRY the retirement. **Form (a) —
date-scoped exit-cohort bins — was frozen ex ante** (PREREG §1) on four
recorded grounds: rule 19 (the COD ramp is THE single exit-timing
mechanism; form (b) would mint a parallel mask channel), blast radius (two
fleet-build functions vs the vectorized availability builder), fidelity
(the surviving plant's bin aggregates only survivors), and the whole-plant
precedent (Mystic/Grand Tower topology at (plant × exit-month) grain).
Frozen scope: leg-1 partial-exit units ONLY (loader-stamped provenance);
whole-plant retirees, leg-2 re-carries and announced operable retirements
NOT routed. The deliberate whole-plant non-scope was measured: exactly two
MISO staggered-exit plants, Crawfordsville (11.5 MW) + LaO Energy
(384.0 MW). Witness ceilings were frozen from the committed operable
snapshot at plant grain (the miso-190 §5.1 vacuous-witness repair), and a
zero-LP full-fleet pre-flight reproduced every witnessed cohort at its
exact frozen capacity before any leg ran.

## 3. The mechanism (single delta, rides the existing field)

`Generator.partial_exit_unit` (loader-stamped provenance, one consumer,
not a tunable) → `fleet_to_bins` cohort keys `(plant, group, ry, rm)` with
`Retirement_Year`/`Retirement_Month` columns → `bins_to_fleet` appends
`_r{yyyy}{mm}` to the bin id and stamps each cohort tranche's own
retirement → the EXISTING `cod_ramp.effective_cod` per-unit preference
ages the cohort out. **No change to `cod_ramp.py` or `arrays.py`**; unit
ids keep the `_p{plant}_` token (every plant-grain parser still resolves)
and the terminal tranche suffix. Byte-inert off (13 unit tests + 196
fleet regressions). Instrumentation added: the per-pass
`dispatch/<year>_<pass>_fleet.parquet` capacity listing (the PREREG named
FleetContext schema metadata as the capacity-witness channel, but the
dispatch parquet is a plain long table without it — same frozen
quantities, corrected channel, disclosed).

## 4. The A/B (PREREG-miso191 §4) — what the gates found

* **S-0 PASS.** The control reproduces the committed keeper
  value-identically — max |diff| = 0.0 on all 12 scored sidecars (fifth
  consecutive clean HEAD reproduction).
* **The mechanism acted exactly as designed at the LP grain:**
  * Cohort presence + capacity EXACT at all 8 witness plants × 3 years
    (Sherco-2 682.0, Karn 486.0, Brown 485.0, SOC 496.0, Petersburg
    421.8, Teche 250.0, Waterford 409.5, Wheaton 186.0 MW; every
    presence witness non-empty, absent from the control everywhere).
  * **Cohort dispatch EXACTLY 0 after every real exit month** — Karn from
    Jun-2023, Petersburg from Jul-2023, Brown from Nov-2023, Sherco-2
    from Jan-2024, Waterford from Apr-2024, SOC 5+6 from Jun-2024, Teche
    from Jul-2024, Wheaton from Jun-2025. **The miso-190 phantoms
    (~10 TWh/yr of measured-dead dispatch) are GONE.**
  * Plant survival (Sherco 1+3 and SOC 7+8 keep running post-exit),
    oracle drops (no Dallman-3 / Weston-2 cohort), Grand Tower still
    exactly 0, Rush Island still runs in both legs. Six of eight frozen
    plant-grain post-exit ceilings met (994 ≤ 1057.2, 6090 ≤ 1556.0,
    4041 ≤ 616.0, 8056 ≤ 417.3, 1702/6137/1400 at 0.0).
* **S-2 PASS: +5.3068 TWh coal-2023** (177.24 → 182.55), with 2024
  **+0.39** and 2025 **+0.017** — real 2023 supply, no phantom inflation
  (miso-190's poisoned rise was +7.0/+6.5/+9.3).
* **S-4 PASS.** Zero D-4 conduct failures, zero new; C8 PASS.
* **Charter kill 1 SILENT.** C3a-2025 −12.2965 → −12.3405 (0.044 pp,
  tolerance 0.10). The 2025 face is as measured in phase-0: ~zero.
* **S-5 at full magnitude:** C3a-2023 **+3.5008 → +0.0913** (the declared
  face landing at zero — phase-0 predicted "near 0 to +1"); C3a-2024
  −4.3034 → −4.5511 (the declared adverse face, small, in-band);
  2023 coal C1 Σ|err| **8.546 → 3.399 TWh** (COAL_PRB −2.212 → −0.067,
  COAL_BIT −5.764 → −2.704, all PASS); **zero PASS→FAIL flips**
  (C3b-2025 stays PASS — the miso-190 phantom flip is absent); no band
  exits; determinations NOT-YET → NOT-YET (same {C3a-2025}-alone shape);
  forced_share COAL 2023/2024 PASS → SKIPPED (the arm's bare-COAL class
  row reads 0.0 % of load — immaterial, coverage bookkeeping); C8 2023
  CT_PEAKER newly grounded-above-budget at 15.6 % vs the 15 % cap (all
  mechanisms clear D-4, profile r 0.971 — a clean PASS surfaced as a
  report note per rule 20).

## 5. Reported against interest — the two failed witnesses and the promotion basis

**Two pre-registered S-1 clauses FAILED AS FROZEN, and the instrument's
mechanical verdict — REJECT via charter kill 2 ("coal C1 improves while
any S-1 clause failed") — stands UNALTERED in `_miso191_ab_gates.json`.**
No witness was re-keyed, no threshold moved, no alternative statistic
replaced a frozen one. The root causes, measured from the frozen
quantities themselves plus committed records:

1. **`post_exit_ceilings p4014_CT_PEAKER` (frozen ceiling 0.0 MW).** The
   ceiling was IMPOSSIBLE for any correct arm: the committed operable
   snapshot carries five "Natural Gas Internal Combustion Engine" units
   (WHT09–13, 47.0 MW) at Wheaton that the phase-0 tech filter (the
   gas-CT technology string only) missed — and the **CONTROL violates the
   frozen ceiling byte-identically to the arm** (max Jun–Dec-2025 hourly
   dispatch 32.887855529785156 MW in BOTH legs). A clause the control
   fails identically measures keeper-baseline behavior and carries zero
   information about the flag's action. The Wheaton EXIT itself is
   verified independently: the r202505 cohort reads exactly 0 from
   June 2025.
2. **`leg2 6055 capacity delta` (frozen +517.0 MW).** The frozen number
   used the SNAPSHOT rating; the arm's measured deltas — **+520.0
   (2023), +554.1 (2024), 0.0 (2025)** — equal Big Cajun 2-1's
   YEAR-MATCHED VINTAGE net-summer ratings **to the decimal**
   (vintage_2023 520.0 / vintage_2024 554.1), which is the basis
   PREREG-miso190's leg-2 design text itself specifies ("the same
   per-unit build from the vintage rows"). Warrick (6705) matched its
   frozen deltas exactly (+126.4 / 0 / 0). The mechanism did what its
   design says; the witness froze the wrong basis.

**Promotion basis.** Because S-1 was not clean as frozen, the PREREG's
own promotion rule could not fire — so per the handoff's ask C the
adjudication went to the pre-registered **owner-escalation path with the
recommendation**. The owner's standing in-session instruction — *"Is this
a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."* —
given twice (2026-08-30/31), resolved the escalation in advance. The
recommendation was PROMOTE: every discriminating witness family passed,
both failed clauses are demonstrated instrument mis-freezes, structural
integrity strictly improves (the fleet no longer erases 7.7 TWh of real
2023 generation NOR carries measured-dead capacity — rules 1/13/14), and
every scored regression is in-band and disclosed. Reverting
`keepers/MISO.json` to `2026-08-30-miso-188-rvsscope` undoes the
promotion. (The miso-186/187 promotions are the precedent for this
basis.)

Also disclosed: (a) one benchmark-part cosmetic diff —
`bench/MISO/2023.json.gz` drops plant 992 (CC Perry K, the 3.4 MW ST_CHP
cohort) from the plants metadata map; zero numeric benchmark values move;
(b) the capacity-witness channel correction of §3; (c) the arm run id is
`-bexit` under the bundle-date `2026-08-30` though the adjudication
completed 2026-08-31 (the miso-187/188/190 naming precedent).

## 6. Keeper state after miso-191

Keeper `2026-08-30-miso-191-bexit` (bundle `miso191_bax_B`):
**NOT-YET on {C3a-2025 −12.3405 %} ALONE**; C1 16/16 all / 12/12 free;
C3c the single ledgered caveat (3/30, 6/37, 1/88 hours >$200); C6
attested — DOF ledger **37/2**, the new entry MEASURED (EIA-860 actual
retirement record + vintage status + energy-source codes, zero scalars);
C8 PASS with two grounded-above-budget report notes (2023 CT_PEAKER
15.6 %, 2025 ST_GAS 34.2 %). Cell `partial_plant_exit_carry` **R → K**
(the miso-190 R re-tested with this charter's new evidence, per the
handoff).

## 7. Standing OWNER items (restated, not decided)

(1) the C8 provenance-materiality floor; (2) committed-vs-regenerated
diagnostics exposure; (3) `RHO_CLIP` cross-ISO band; (4) **D-4 posture —
the C3a-2025 direction object** (~3.3 GW mc-idled/flat-stack model-class
residual; ~1.3 GW scarce-export concession) — **the lane's only open
road, unchanged by this session** (this repair's 2025 face was 0.010 TWh
by measurement and the kill-1 tolerance held it to 0.044 pp); (5) the
miso-189 §7.3 marginal-vs-average delivered-cost residue (adverse sign,
cross-ISO). The fleet-membership family is now, after four consecutive
repairs (miso-186/187/188/191), at its adjudicated frontier: every named
membership blind spot is closed.

## 8. Governance

Rule 22: 2023/2024/2025 ONLY; MISO holds neither marker; freeze
untouched; no new data fetch. Rules 15/16: BOTH legs registered, full
span, one invocation each. Rule 12: years sequential within each leg;
legs sequential; solves in-session. Rules 5/13/14/19/23/24: the existing
field, no new tunable (the provenance bool is loader-stamped plumbing);
identification measured, zero fitted scalars. Rule 25: only MISO's
shard/keeper/status files. Rule 27: exact on-disk bytes; every pushed
blob ≥300 lines verified. Rule 28: §5.4 queue stamp + prose-header
re-stamp + shard cell (R → K) + calibration-log entry in-session;
`check_mechanism_matrix.py` green. Keeper-auditor: PASS, 0 repairs.
THE OWNER MERGES; no PR opened.

## 9. Reproduction

```
python3 scripts/probes/_miso191_binning_phase0.py
python3 scripts/probes/_miso191_ab_gates.py
python3 scripts/probes/_miso191_attestation.py
python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-191-bexit
```
