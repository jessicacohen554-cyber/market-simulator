# FINDING — nyiso-191: the `CC_CHP` scope extension of `cc_capacity_reconcile` is **REJECTED on rule 19 `[R-ONE-MECH]`** — `chp_layup_duty_curve` already owns the phenomenon for that class and binds tighter at every plant; and the object the session was opened on turns out not to be a capacity defect at all

**Session:** nyiso-191, `backcast-calibration` lane
(`claude/nyiso-191-ccchp-capacity-scope`), 2026-09-05. **Solves run: TWO** — the
same-HEAD control (`results/calibration/nyiso191_control`, registered
`2026-09-05-nyiso-191-control`, an instrument) and the one arm
(`results/calibration/nyiso191_ccchp_scope`, registered
`2026-09-05-nyiso-191-ccchp-capacity`, **a rejected probe**).
**Keeper at entry AND at exit: `2026-09-05-nyiso-189-steam-identity`** —
CALIBRATED, grade 7, fails 0, C3c ledgered. **Nothing is promoted; the
canonical `cc_capacity_reconcile_NYISO.csv` is restored byte-for-byte to the
`origin/main` blob `e0b1610` (sha256 `a3d407f9…`), so the keeper keeps reading
its own artifact.**
**Markers: D56 HAD LANDED at entry.** `complete.NYISO` exists, already keyed to
the current keeper with its determination re-verified without a solve by the
D56-R records lane, and `audit_keepers.py --iso NYISO` PASSes — **the rule-22
D-5(b) duty was already discharged, so this session re-keyed nothing and
requested no marker.** Training years only (2023–2025).
**Pre-registration:** `results/calibration/PREREG-nyiso191-ccchp-capacity-scope.md`,
pushed to `origin` BEFORE the derive was edited and before any solve; every bar
and branch is executed verbatim below.
**Machine records:** the arm's computed `calibration_attestation.json`
(`scripts/gen_nyiso191_attestation.py`, six checks, refuses on any failure),
`results/calibration/_nyiso191_ccchp_scope_phase0.json`,
`_nyiso191_stgas_placement.json`, probes
`scripts/probes/nyiso191_ccchp_scope_phase0.py` / `nyiso191_stgas_placement.py`,
and the two tables preserved bundle-local
(`nyiso191_ccchp_scope/cc_capacity_reconcile_NYISO_widened.csv`,
`nyiso191_control/cc_capacity_reconcile_NYISO_prechange.csv`).

---

## 1. The result in one paragraph

The nyiso-190 handoff opened this session on the claim that
`cc_capacity_reconcile`'s `CC_REGULAR` scope filter is what keeps the mechanism
off the model's three largest per-plant over-runners. **Phase 0, run before the
derive was touched, refuted that**: the frozen population rule reaches none of
them — Sithe Independence 54547 gets a **RAISE** (its demonstrated peak 1,170 MW
*exceeds* its 1,157.8 MW model capacity, so its +3.19 TWh over-run is a **duty**
defect, not a capacity one), Brooklyn Navy Yard 54914 is declined by the frozen
CT-only guard, and Empire 56259 sits inside the frozen 1.10 margin. What the
widening does reach is 8 rows of small-to-mid cogen, net −542.5 MW, and phase 0
predicted in advance — from the keeper's own registered dispatch — that it would
be **very nearly energy-inert** (model energy above the proposed caps:
0.0000 / 0.0143 / 0.0000 TWh). It was run anyway, on a rule 14 `[R-ACCURATE]` +
rule 13 licence stated before the build, because phantom LP capacity is a
misrepresentation whether or not it binds in a backcast year. **Every bar came
back as pre-registered**: the control is BIT-IDENTICAL to the keeper (0 of
52,560 prices differ, all years); G-DELTA is the artifact and nothing else; B1
engaged (the arm caps 19 plants for −1,282 MW against the control's 12 for
−740 MW); **B2's falsifiable prediction HELD** (worst gas-family movement
0.0034 TWh against a 0.05 TWh bar); and B3 shows **no criterion-level status
flip** — the arm reads CALIBRATED, grade 7, C3c ledgered, identical to the
control, with every magnitude moving ≤ 0.01 TWh. **The arm is nevertheless
REJECTED, and not on the residual.** Chasing *why* six of the eight rows never
reached the LP found the real answer: **`chp_layup_duty_curve` — a keeper-armed
`K` mechanism (matrix row `offer_curve_by_group`, nyiso-149) — already withholds
those plants' capacity to a MEASURED price-conditional duty that binds tighter
than the demonstrated-peak cap at every one of the six cohort members.** Widening
`cc_capacity_reconcile` into `CC_CHP` therefore stacks a second bound on an
owned phenomenon, which is exactly what rule 19 `[R-ONE-MECH]` forbids. The two
rows outside that cohort pull in **opposite** directions, and the harmful one is
the bigger: World Generation X improves (CF 0.675 → 0.523 against a measured
0.353) while **Sithe's raise pushes the model's single largest over-runner
further out** (0.932 → 0.939 against 0.618). Structural integrity does not
improve — the plant-grain offsetting misallocation is unchanged at 7.38 / 8.18
TWh in 2023 / 2024 and **0.07 TWh worse** in 2025.

---

## 2. The bars, executed verbatim (PREREG §3)

| bar | what it fixed in advance | result |
|---|---|---|
| **V1** control identity | control must be bit-identical to the keeper | **PASS** — 0 of 52,560 P1 zonal prices differ in each of 2023/2024/2025, max \|Δ\| 0.0 |
| **V2** other-ISO invariance | re-deriving at the DEFAULT `--classes` must reproduce each committed table | **PASS** — NEISO (14 rows), CAISO (7), PJM (20), MISO (23) reproduce byte-for-byte on `plant_code`/`reconciled_mw`/`mode`; ERCOT's raise-path filter is proven identical at the default (`isin(("CC_REGULAR",))` ≡ `== "CC_REGULAR"` over the real bin CSV, 41 rows) since its own input (a solved bundle's `campd.parquet`) is not in the repo |
| **G-DELTA** | the ONLY config difference is the table the flag reads | **PASS** — `delta_fields = ['cc_capacity_reconcile_path']`, nothing rode along, `cc_capacity_reconcile` `True` on both sides; the artifact differs by exactly the 8 phase-0 rows with the 15 pre-existing ones byte-identical |
| **B1** engagement | the arm must carry the capped plants at their reconciled MW | **ENGAGED** — arm applies 19 caps + 4 raises (−1,282 MW) vs the control's 12 + 3 (−740 MW); the −542 MW delta is exactly phase 0's |
| **B2** *my own falsifiable prediction* | ≤ 0.05 TWh of movement, else my phase-0 reasoning was wrong | **HELD** — worst \|Δ gas family\| **0.0034 TWh** (0.0001 / 0.0000 / 0.0034) |
| **B3** the rejection rule | rejected iff C2 / C3a / C3b / C8 flips PASS → FAIL | **NO FLIP** — every criterion identical: C1 PASS, C2 PASS, C3a PASS, C3b PASS, C3c CAVEAT (ledgered), C4 PASS, C6 PASS, C8 PASS; **CALIBRATED, grade 7** on both sides |
| **B4** structural integrity | reported whatever the gates do | **NO GAIN** — see §4 |

The realised class movement (control → arm, TWh): `CC_CHP` −0.0056 / −0.0092 /
−0.0158, absorbed almost entirely by `CC_REGULAR` +0.0030 / +0.0047 / +0.0095 —
i.e. released cogen energy lands on the class whose cell is closest to its band,
the direction the pre-registration named as the adverse one, at 0.15 % of that
cell's 3.33 TWh miss. **C1-2024 `CC_REGULAR` +3.33 → +3.34 TWh** (share +2.8 pp
unchanged). Load-weighted price +0.031 % / +0.016 % / +0.019 %.

---

## 3. WHY it is rejected — rule 19, found by chasing the inertness

B1 said the arm engaged; the LP said otherwise. Per-plant LP capacity (P1
`unit_hourly`, per-hour tranche sum, max over hours) moved at only **2 of the 8**
plants. The cause is not that the caps failed to apply — at the bin level every
row binds (the derive's `current_mw` equals the bin capacity exactly for all 8).
It is that **something already holds these plants far below their caps**:

| plant | bin cap → reconciled | `chp_layup_duty_curve` measured duty (econ+peak MW) | which binds | LP capacity moved? |
|---|---|---|---|---|
| Selkirk Cogen 10725 | 753.8 → 378.0 | **199.4** | duty | no |
| Lockport 54041 | 221.3 → 142.3 | **48.9** | duty | no |
| Indeck Yerkes 50451 | 84.8 → 54.6 | **28.2** | duty | no |
| Indeck Oswego 50450 | 75.4 → 58.5 | **37.1** | duty | no |
| CH Res. Beaver Falls 10617 | 107.8 → 84.6 | **34.1** | duty | no |
| Indeck Olean 54076 | 90.6 → 80.9 | **45.5** | duty | no |
| World Generation X 54131 | 65.7 → 45.8 | *not in cohort* | cap | **yes** (41.5 → 28.9 MW) |
| Sithe Independence 54547 | 1,157.8 → 1,170.0 (raise) | *not in cohort* | raise | **yes** (+11.9 MW) |

`chp_layup_duty_curve` (`ScenarioConfig`, nyiso-149; seam
`campd_bins.fleet_to_bins` + the load-bearing `assembly.bins_to_fleet` override;
matrix row **`offer_curve_by_group`**, NYISO cell **`K`**, armed on the keeper)
gives a census cogen plant only its **measured price-conditional duty** —
`pct_econ` at the class econ band, `pct_peak` at the class peak band, *the
remainder withheld from energy and reserves*. Its cohort has 7 members and **6 of
them are exactly the 6 plants above**. Its own code comment names Selkirk 10725
as the motivating case.

**So the class is already covered, by a purpose-built mechanism, on a measured
basis, binding tighter in every instance.** Adding a demonstrated-peak cap on top
is a second mechanism on one phenomenon — rule 19 `[R-ONE-MECH]`, whose remedy is
"replace or reconcile, never stack". Nothing here re-opens or re-adjudicates
`chp_layup_duty_curve`; the cell stays `K`.

### 3.1 The two rows that do bite, and why they do not rescue the arm

* **World Generation X 54131 — the one defensible cap**, and it moves toward
  reality (model CF 0.675 → 0.523 against a measured 0.353, −0.088 TWh). But it
  carries a caveat found while checking it: **the bench flags this plant
  `ct_only` at 1.378× in 2024**, while the derive's **pooled** CT-only test
  admits it, because its 2025 EIA-923 row is **0.0000 TWh** and drags the pooled
  ratio to 0.60. A pooled test diluted by an incomplete vintage let through a
  plant the per-year test rejects — recorded in §6 as its own item, not repaired
  here.
* **Sithe Independence 54547 — a raise on the worst over-runner.** The rule
  raises it 1,157.8 → 1,170.0 MW because its demonstrated peak exceeds its model
  capacity; LP capacity +11.9 MW and model CF **0.932 → 0.939** against a
  measured 0.618. The mechanism is behaving correctly (the plant really did reach
  1,170 MW) — which is precisely the point: **Sithe's defect is duty, not
  capacity**, and a capacity mechanism can only make it worse.

---

## 4. B4 — structural integrity, reported whatever the gates did

| year | plant-grain gross over / under (TWh) | offsetting misallocation, control → arm |
|---|---|---|
| 2023 | +11.86 / −7.38 | 7.38 → **7.38** (unchanged) |
| 2024 | +11.25 / −8.18 | 8.18 → **8.18** (unchanged) |
| 2025 | +11.22 → +11.29 / −9.29 → −9.36 | 9.29 → **9.36** (0.07 TWh **worse**) |

**The arm buys no structural accuracy.** Under the owner's standing formula
("if structural integrity improves but gates regress that may still be a
keeper") it fails the *antecedent*, not the consequent: integrity does not
improve and the gates do not move. It is not a keeper candidate on any reading,
and the recommendation is **do not promote**.

---

## 5. What was done with the change

* **The canonical artifact is REVERTED** to the `origin/main` blob `e0b1610`
  (verified by hash), so the keeper reads its own 15-row table. The widened
  23-row table is preserved **bundle-local** as
  `results/calibration/nyiso191_ccchp_scope/cc_capacity_reconcile_NYISO_widened.csv`
  (sha256 `bcf5d1ec…`), and the control's pre-change copy as
  `nyiso191_control/cc_capacity_reconcile_NYISO_prechange.csv`, so both solves
  remain reproducible from committed bytes.
* **The derive's `--classes` parameterisation is KEPT** — it is what made this
  adjudication reproducible, V2 proves it a no-op at its default for every ISO,
  and it carries tests
  (`tests/curation/test_derive_cc_capacity_reconcile_scope.py`: the default
  equals the pre-change filter, the frozen thresholds are asserted against their
  literals, `CC_CHP`'s registered parasitic load equals `CC_REGULAR`'s so no
  constant was added, and **no committed table of any ISO carries a widened
  scope**). The matrix records the NYISO verdict so the DO-NOT-REDO discipline
  applies.
* **Both runs are registered** (rule 15) — the arm explicitly labelled
  `(PROBE — REJECTED)` with the rule-19 reason in its sidecar definition, the
  control as the bit-identical instrument. Registration pruned two 2026-08-30
  nyiso-159 runs under the top-15 NYISO retention.

---

## 6. Handed forward

1. **Sithe Independence 54547 is a DUTY object, not a capacity object** — model
   CF 0.93 / 0.97 against a measured 0.62 in 2024 / 2025, at a plant whose
   demonstrated peak the model already respects. It is **not** in the
   `chp_layup_duty_curve` cohort (its meter never reads a zero median), so
   neither mechanism reaches it. This is the largest single per-plant over-run in
   the NYISO fleet (+3.19 / +3.48 TWh) and it is now un-owned. **Measure the
   cohort-admission rule against it before proposing anything.**
2. **The derive's CT-only test is POOLED and can be diluted by an incomplete
   EIA-923 vintage** (§3.1: World Generation X reads `ct_only` 1.378× in 2024 but
   0.60 pooled, because its 2025 row is 0.0000 TWh). The bench's per-year test
   and the derive's pooled test disagree on exactly the row that binds. A
   per-year (or complete-vintage-only) test is the rule-23 route; it affects
   every ISO's table, so it is a cross-ISO change and not this lane's to make
   unilaterally.
3. **`ST_GAS` is a ZONAL placement error** (object 2, measured, no lever
   proposed — `_nyiso191_stgas_placement.json`). The sign is **stable in all four
   zones across all three years**: NYC **over** (+4.26 / +2.24 / +0.41 TWh,
   Ravenswood and Arthur Kill), Long Island **under** (−1.65 / −2.26 / −2.28,
   Northport and E F Barrett), Capital-Hudson **under** (−0.95 / −1.03 / −1.66,
   Bowline Point and Roseton), Upstate-West **under** (−0.51 / −0.32 / −0.16,
   Greenidge). The class net (+1.15 / −1.37 / −3.70) hides an offsetting
   misallocation of 3.28 / 2.53 / 0.84 TWh. The model runs NYC steam where the
   market ran Long Island and Capital-Hudson steam — a locational signature
   (zonal price formation, the LI import limit, zonal delivered-gas basis), not a
   plant-cost one. Ravenswood's *availability* was adjudicated at nyiso-183 and
   its *merit position* is the open `offer_curve_by_group` defect; this is the
   zone-level view of the same object.
4. Unchanged and untouched: C3a-2025 −8.3 % (`DECISION-CARD-nyiso148` Q1,
   confirmed still pending, owner-court); cell **G**
   (`scuc_load_pocket_commitment`) stays `G` — nyiso-97 §5 and the nyiso-160
   access closure stand; the nyiso-190 provenance bars; the Bethlehem object.
   **Forecast lane:** `egrid_steam_collapse_heat_rates` regenerates per eGRID
   vintage (`APPLIED_VINTAGE = 2023`); **eGRID 2025 has not landed** —
   `data/raw/fleet-egrid` holds vintages through `egrid2024_data.xlsx` only.

## 7. Governance

Rule 1 `[R-STRUCT]`: bars and outcome branches fixed and pushed before the
derive was edited and before any solve; the phase-0 refutation of the session's
own premise was disclosed in the pre-registration, not after the result; the
rejection is on a structural collision (rule 19), never because the residual
failed to move — indeed the gates did not move at all. Rule 5 / 21 / 24: zero
new constants, zero retuned constants, zero new `ScenarioConfig` fields, zero
new DOF entries; every threshold asserted against its literal in the attestation
and in tests. Rule 13 `[R-MEASURED]`: the demonstrated peak regenerates from any
CAMPD vintage. Rule 14 `[R-ACCURATE]`: the licence the arm was run under, stated
before the build. Rule 19 `[R-ONE-MECH]`: the finding. Rule 15: both solves
registered, the arm as a rejected probe. Rule 16: 2023–2025 in one bundle each.
Rule 22 `[R-HOLDOUT]`: training years only; D56 had landed and the D-5(b) duty
was already discharged by the records lane, so nothing was re-keyed and no
marker was requested. Rule 25 `[R-ISO-SCOPE]`: `--classes` defaults to the
pre-change behaviour and V2 proves no other ISO's table moves; only the NYISO
shard is edited. Rules 15 / 28: registration and matrix duties discharged in this
session. Rule 27 `[R-PUSH]`: on-disk bytes pushed, every ≥300-line blob verified
after each push.

*(nyiso-191, 2026-09-05. Two solves. Keeper unchanged. Artifact reverted.)*
