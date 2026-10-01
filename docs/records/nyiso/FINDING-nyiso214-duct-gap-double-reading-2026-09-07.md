# FINDING nyiso-214 — the EIA-860 `nameplate − net_summer` gap is read **TWICE** inside `CC_REGULAR`, and which reading a plant gets is decided by a flag, not by the physics. All four pre-registered predictions fire; the efficiency hypothesis is refuted at zero LP.

**Session:** nyiso-214, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-1m6c2q`, on `main` at `c5369f27`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **Keeper unchanged; nothing promoted, nothing armed, nothing registered.**
**Pre-registration:** `results/calibration/PREREG-nyiso214-duct-gap-double-reading.md`, committed
and pushed at `bc3ec7ec`-lineage **before P1–P4 were measured** and not edited since.
**Machine record:** `results/calibration/_nyiso214_duct_gap_census.json` (every number below).
**Instrument:** `scripts/probes/nyiso214_duct_gap_census.py`. **ZERO LP: no solve was spent.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads CALIBRATED with **zero failing
criteria** across 2023–2025. Nothing below was selected because a residual moved (rule 1
`[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`); no residual was consulted at any point.

---

## 0. The result in one paragraph

The nyiso-213 hand-forward object (B) — Cricket Valley 57185 under-running its own meter by
~0.75 TWh at corrected availability while `CC_REGULAR` over-runs in aggregate — is **not an
efficiency defect**: the model's heat rate for 57185 sits 2.3–4.3 % above its own CAMPD rate,
which is where every other material CC in the class sits too. The within-class merit order is
instead set by the **peak-band share**, which spans **0.0 %–22.6 %** across the class while base
heat rates span ±4 %, and which is allocated by `cc_duct_peaking_pct` from the EIA-860
`nameplate − net_summer` gap **gated on a `Duct Burners == Y` flag**. Measured here for the first
time: **the same gap, at the same plants, is simultaneously read by `cc_nameplate_summer_derate`
as ambient derate and removed in Jun–Sep** — at **11 plants carrying 819.5 MW of peak band**, and
at 57185 both mechanisms are proved to read one EIA-860 pair to 0.0 pp and 4 × 10⁻⁵. The flag
decides which plants get the second reading, and it does not track the physics: **Athens 55405
carries a 19.42 % gap and receives 0.0 MW of peak band, while Cricket Valley 57185 carries a
22.58 % gap and receives 245.6 MW.** Across the five boundary-clean material plants the peak
band's size has **no relationship** to the plants' own demonstrated reach above the rating it is
derived from (ρ = **−0.10**) — the plant with the largest band has the *smallest* reach. This is
a rule 19 `[R-ONE-MECH]` collision of the same family nyiso-212/213 repaired, and it is handed to
the owner as a decision card (§6), not levered here.

---

## 1. P1 — the double reading exists and is material: **FIRES**

Declared bar: **≥ 6 plants** carrying **≥ 400 MW** of peak band that BOTH receive a nonzero
`cc_duct_peaking_pct` band AND take a Jun–Sep summer-derate multiplier `< 1`.

Measured: **11 plants, 819.462 MW** — 57185, 2539, 56940, 57664, 55375, 56234, 54574, 50292,
10621, 56188, 10190.

Every one of the eight material (≥ 350 MW) `CC_REGULAR` plants carries a summer multiplier below
1 — **including both plants that receive no band at all** (55405 at 0.9246, 56196 at 0.8464). So
the gap is removed as ambient derate at flagged and unflagged plants alike; only the flagged ones
are additionally handed a second, contradictory reading of the same MW as duct-firing capability
priced at `2.25 × base` heat rate, in **all twelve months**.

## 2. P2 — the asymmetry is NOT explained by the physical gap: **FIRES**

Declared: **≥ 8.0 %** at EACH of the two material zero-band plants; **< 4.0 % REFUTES** the
session's framing (declared in advance precisely because it hurts the preferred answer);
**[4.0, 8.0) INDETERMINATE**.

| plant | EIA-860 nameplate | net summer | **gap %** | duct flags | peak band | summer mult |
|---|---:|---:|---:|:--|---:|---:|
| **55405 Athens** | 1,221.6 | 984.4 | **19.417** | N, X | **0.0 MW** | 0.9246 |
| **56196 Zeltmann** | 528.0 | 474.0 | **10.227** | N, X | **0.0 MW** | 0.8464 |
| *57185 Cricket Valley (comparator)* | 1,312.5 | 1,016.1 | *22.583* | **Y**, X | *245.6 MW* | *0.9349* |

Both clear 8.0 % and neither is near 4.0 %. **Athens' gap is the second-largest of any material
`CC_REGULAR` plant** — larger than five of the six flagged plants that *do* receive a band — and
it receives none. The zero band is a property of the **flag**, not of the plant's capability gap.

The flag itself is not inaccurate: Cricket Valley genuinely files `Y` on its three CA rows and
Athens genuinely files `N`. What fails is the **quantity the flag is applied to**. EIA-860 carries
no duct-burner MW field at all — `cc_duct_peaking_pct`'s own docstring says so — so a plant-level
capability gap is used as the proxy, and that gap is the identical ambient/auxiliary quantity the
summer derate reads. Duct-burner *presence* does not convert an ambient derate into duct
capability.

## 3. P3 — reproduction bar, and the VOID that did not fire: **FIRES**

Declared: **< 40 %** of 57185's gap on the `Y` rows (nyiso-198 reproduction); **> 50 % VOIDS**
the census.

Measured: the plant files six CC rows — three CA rows at `Y` (174.2 np / 143.3 ns each) and three
CT rows at `X` (263.3 / 195.4 each). Gap on `Y` rows **92.7 MW**, on non-`Y` rows **203.7 MW**,
`Y` share **31.275 %**. The 203.7 MW reproduces nyiso-198's committed census **exactly**, on this
session's own HEAD and active vintage, so the instrument is confirmed by reproduction and the
VOID condition did not fire.

A duct burner fires into the HRSG and raises the **steam** turbine's output; EIA-860 reports the
attribute at that grain and reads `X` on every CT row in the whole operable CC population. **Two
thirds of Cricket Valley's peak band is the gas turbines' own ambient derate booked as duct
capability** — and the remaining third is the steam turbines' ambient derate, which is not a duct
increment either.

## 4. P4 — the two mechanisms provably read ONE EIA-860 pair: **FIRES**

At 57185: `peak_MW / carried = 245.639 / 1,086.9 = 22.6 %` against `cc_duct_peaking_pct = 22.6`
— **Δ 0.0 pp**; and the measured Jun–Sep multiplier **0.9349** against
`min(1, net_summer / carried) = min(1, 1,016.1 / 1,086.9) = 0.9349` — **Δ 4 × 10⁻⁵**.

The rule-19 characterisation is therefore not an argument: `cc_nameplate_summer_derate` (on
nyiso-213's reconciled basis) and `cc_duct_peaking` are demonstrably reading the same
`(nameplate = 1,312.5, net_summer = 1,016.1)` pair at the same plant in the same solve, and
drawing opposite physical conclusions from it.

## 5. The efficiency hypothesis, refuted — and the allocator's relationship to the meter

**Refuted (this session's first result, a clean negative).** On a `fleet_only` rebuild of the
keeper's 2025 fleet, 57185's base heat rate is **7.013 MMBtu/MWh** against its own CAMPD gross
rate of 6.854 / 6.803 / 6.721 — a model/measured ratio of **1.023 / 1.031 / 1.043**, inside the
band every other material CC occupies (55405 1.017–1.028, 55375 1.028–1.037, 56196 1.011–1.036,
56234 1.035–1.041, 56940 0.992–0.996). **The model does not penalise Cricket Valley on
efficiency**, and a per-plant measured heat-rate repair is not this object's lever. Base heat
rates across the eight material plants span 6.75–7.38 (±4 %) while the peak-band share spans
0.0–22.6 %: the band, not the heat rate, is the within-class merit allocator.

**And the allocator does not track the meter.** Over the five material plants whose CAMPD facility
is comparable to the model plant (§7), the share of each plant's own online hours spent **above
its published net-summer rating** — the very rating the band is derived from:

| plant | peak band (% of carried) | reach 2023 | 2024 | 2025 | mean |
|---|---:|---:|---:|---:|---:|
| **57185 Cricket Valley** | **22.6** | 8.67 % | 2.58 % | 11.43 % | **7.56 %** |
| 56940 CPV Valley | 15.1 | 30.49 % | 30.65 % | 40.46 % | 33.87 % |
| 56234 | 9.1 | 44.19 % | 41.30 % | 40.53 % | 42.01 % |
| 2539 Bethlehem | 9.0 | 0.00 % | 32.56 % | 13.86 % | 15.47 % |
| **55405 Athens** | **0.0** | 8.84 % | 17.85 % | 13.01 % | **13.23 %** |

Rank correlation **ρ = −0.10**: **no relationship**. The plant handed the largest above-rating
band has the *smallest* measured above-rating reach, and the plant handed none has nearly twice
57185's. Every one of these plants exceeds its published net-summer rating in a material share of
its running hours, which is the deeper rule-14 `[R-ACCURATE]` reading: at these plants
`nameplate − net_summer` is not a capability gap the fleet cannot reach — it is a rating the
fleet routinely runs through.

## 6. OWNER DECISION CARD — which membership construction, if any

**Nothing is built, armed or proposed here.** A symmetric construction is a NEW `ScenarioConfig`
field needing its own matrix row (rules 24 `[R-REGISTRY]` / 28(c) `[R-MECH-MATRIX]`), and the
choice between forms is a modelling decision with a forward story at stake, not this lane's call.
The forms are sized by **arithmetic on the census and the plants' own meters — no form was
selected, and no residual was consulted** (rule 1). Sizing over the 16 multi-tranche
`CC_REGULAR` plants:

| form | construction | peak band MW | 57185 | 55405 | 56196 |
|---|---|---:|---:|---:|---:|
| **A** (status quo) | Y-gated, gap over ALL the plant's CC rows | **716.8** | 245.6 | 0.0 | 0.0 |
| **B** `cc_duct_peaking_row_scoped` (built, default off, cell **R**) | Y-gated, gap over `Y` rows only | 203.4 | 77.2 | 0.0 | 0.0 |
| **C** symmetric-none | the gap is ambient everywhere; the summer derate owns it alone | 0.0 | 0.0 | 0.0 | 0.0 |
| **D** symmetric-all | every CC plant gets its own gap, flag ignored | 1,065.8 | 245.5 | 206.7 | 57.3 |
| **E** demonstrated headroom | `max(0, carried − net_summer)`, symmetric | 688.5 | 70.8 | 80.3 | 86.0 |

**Reported at full magnitude and NOT a reason to prefer any form (rule 1):** form E is the only
one that redistributes *within* the class at near-constant class total (716.8 → 688.5 MW), moving
band MW **off** the plant that under-runs its meter and **onto** the two that over-run. That is
the direction object (B) describes — and it is stated here as an observation, **not** as
evidence, because **this session has no dispatch evidence of any kind** (zero LP) and the only
dispatch evidence that exists points the other way: nyiso-200 measured that form B's reduction at
Cricket Valley made `CC_REGULAR` over-run **more** in 2023 (+0.83 → +1.43 TWh). A form must be
chosen on its physics and screened under rule 29, never on this table.

**Costs and defects of each form, stated at the gate:**

* **A** — the incumbent. Its defect is §§1–4: one quantity, two contradictory readings, allocated
  by a flag that ρ = −0.10 says is unrelated to the physics.
* **B** — already built and byte-inert while off; its NYISO cell is **R** with a re-test condition
  ("the three-way arm on 2025 … never alone") that this session did **not** re-open. It narrows
  the numerator but keeps the Y-gate, so **it does not touch P2's asymmetry at all**: Athens and
  Zeltmann still receive 0.0.
* **C** — the cleanest rule-19 resolution (one quantity, one mechanism) and the only form needing
  no new measured input. It removes the class's entire scarcity band; what replaces it (the class
  default `pct_peaking = 8.0`, or nothing) is itself a decision.
* **D** — symmetric, but keeps the proxy §3 falsifies and grows the band 49 %.
* **E** — symmetric and half-measured, with a real seam: `carried` is the CAMPD demonstrated peak
  **only at the 15 `cc_capacity_reconcile` plants**; elsewhere `carried` IS nameplate and **E
  degenerates exactly to D** (measured: 2539 and 57664, where E = D to 0.0 MW).
* **E′** (`CAMPD demonstrated peak − net_summer`, fully measured, fully symmetric) — **REFUTED as
  constructed, this session, before it could be proposed.** At the boundary-contaminated plants
  the CAMPD facility spans more than the model plant, so E′ reads **694.0 MW at 55375** and
  **1,669.5 MW at 2500** (demonstrated/carried 2.05× and 7.05×). Reported, not proposed. This is
  nyiso-211 §4.4's warning firing on a new construction.

**The question for the owner:** the Y-flag gate is a *plant-selection* rule that no session has
previously questioned — nyiso-194 tested the band's price, nyiso-198/-200 tested its numerator,
and both left the gate itself standing. Should the gate stay (A/B), be resolved into the summer
derate (C), or be replaced by a symmetric construction (D/E) — and if E, is the reconcile-only
measured basis acceptable given it degenerates to D at unreconciled plants?

## 7. Named and NOT pursued — measured, reported, no claim made

* **Seven small `CC_REGULAR` plants are represented by a SINGLE tranche labelled `_peak`** —
  10621, 54034, 7784, 10620, 54592, 50744, 54593, **441.7 MW** — so their *entire* capacity is
  offered at `2.25 × base` heat rate all year. Their model/CAMPD annual heat-rate ratios read
  1.44–2.69 against 0.99–1.04 for the material fleet. **Two of them (50744, 54593) carry no `Y`
  row at all**, so this is a different path from the duct mechanism. Recorded because a census
  that found this and stayed silent would be the more misleading report (nyiso-211 §8's standard);
  they are 6 % of class capacity and no claim is made about them.
* **Six plants are boundary-contaminated** and every measured-side statistic at them is unusable:
  57664 / 7784 / 54808 (no CAMPD facility of their own — 57664 reports under 55375, the nyiso-186
  merged identity) and 55375 / 56196 / 2500 (facility spans more than the model plant, at 2.05× /
  1.25× / 7.05× carried). **56196 Zeltmann is boundary-contaminated**, so its §2 gap of 10.227 %
  stands on the EIA-860 filing alone — which is the basis P2 was declared on — while its *reach*
  numbers are excluded from §5's ρ. 2500 Ravenswood was already named by nyiso-194 as a CAMPD
  boundary misalignment; this session reproduces that independently and extends it to five more
  plants.
* **The `phys_peak = peak = 2.25` price** is untouched and no price change is proposed. nyiso-194
  already measured that no NYISO quantity identifies a higher value, and rule 1's carve-out
  conditions for a band multiplier are not met here.

## 8. Governance and environment

* **Rule 29 `[R-SCREEN]`:** step 0 only. **No screen, no control, no bundle, no LP.** Nothing to
  delete before merge under 29(c); the control question does not arise because no arm was solved,
  so no G-DRIFT audit is owed (rule 29(b) form 4 is not invoked).
* **Rule 22 `[R-HOLDOUT]`:** training-tier only — the census reads 2023–2025 CAMPD and the
  keeper's 2025 fleet. **No out-of-training year was solved, scored or registered.** `final`
  untouched, the locked-test freeze untouched, 2020/2021 unspent. The 2022 rung's failures are
  named nowhere as a target.
* **Rule 15 `[R-DASHBOARD]`:** no run was produced, so there is nothing to register and keeper-only
  retention is untouched. Rule 28(b): the NYISO matrix shard is stamped in this session.
* **Markers:** none moved. No promotion contemplated, so D-5(b) does not attach.
* **The FIVE PENDING OWNER RULINGS are untouched** (nyiso-206 floor_pct basis; nyiso-207
  identification-vs-application; nyiso-203 §6; DECISION-CARD-nyiso193 §5/§5.1 unit-grain;
  nyiso-208 out-of-training CAMPD read). §6 opens a **new, sixth** card and prejudges none of them.
* **Instrument validation:** `scripts/probes/nyiso196_rebuild_checks.py --year 2024` reproduces its
  committed record with `git status --porcelain -uno` **empty**; and §3's 203.7 MW reproduces
  nyiso-198's committed census exactly.
* **Re-measured after the rebase onto `321867c5` (a HEAD 8 solve-path files removed from the
  `c5369f27` the census was taken at — `iso_configs.py`, `scenarios.py`, `eia930/actuals.py`,
  `fuel/basis/meanzero.py`, `renewables.py`, `zone_assignment.py`, `interchange/spec.py`,
  `results/cache.py`, +575/−242): the whole census regenerates **BYTE-IDENTICALLY**
  (sha256 `11ecdc43a435ebd1…` on both). The drift is confirmed inert for this measurement by
  execution, not by reading.
* **Environment, measured at HEAD `c5369f27`:** `data/clean` rebuilt with
  `curate_capacity_deliverability.py` + `curate_nyiso_interface_flows.py` only. Test set run this
  session, **named rather than inherited**: `tests/scoring/test_gate_a_provenance.py`,
  `tests/unit/data/test_cc_summer_derate_reconciled_basis.py`,
  `tests/scoring/test_holdout_render_parity.py`, `tests/unit/data/test_campd_bins.py` — **75 passed, 0 failed**. `ruff format --check .` reads
  1,403 files already formatted and `ruff check` passes. **No pre-existing failure was found at
  this HEAD**: the `test_gate_a_provenance::test_live_board_passes` failure that nyiso-210/-211/
  -212 recorded, and that nyiso-213 re-measured as repaired, is still passing.

## 9. Reported at full magnitude

* **This session produced no dispatch evidence.** Every claim above is about the fleet's
  construction, not about what it dispatches. The one piece of dispatch evidence that exists on
  the adjacent question (nyiso-200's form-B screen) points **against** a naive band reduction at
  Cricket Valley, and it is cited in §6 rather than omitted.
* **Form E's favourable direction was noticed after it was derived**, and §6 says so explicitly.
  It is not offered as a reason, and no form is recommended.
* **P2's refuting outcome was live**, not decorative: had either plant read < 4.0 %, the
  docstring's defense would have held and the framing would have been reported as refuted. It was
  declared in the PREREG before the EIA-860 rows for those two plants were read.

*(nyiso-214, 2026-09-07. Zero LP. The gates were written before the census; all four fired; the
object moved from a hypothesis about efficiency — refuted — to a measured rule-19 collision, and
the choice of successor was handed to the owner rather than taken.)*
