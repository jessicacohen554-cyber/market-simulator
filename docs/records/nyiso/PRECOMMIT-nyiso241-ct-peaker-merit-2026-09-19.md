# PRECOMMIT — nyiso-241: the CT_PEAKER merit collapse, two grounded arms

**Session** nyiso-241 (orchestrator; rule 32 `[R-SHARD]` (a) — zero LP in this container).
**Date** 2026-09-19. **Pushed BEFORE the first LP**, per rules 1 `[R-STRUCT]` (c) and 29
`[R-SCREEN]` clause (0).

**Incumbent keeper** `2026-09-17-nyiso240-bench-attribution`, bundle
`results/calibration/nyiso240_benchfix_span`, years {2022, 2023, 2024, 2025}, determination
**CALIBRATED** (grade 7 of 8, fails 0, C3c the lone ledgered caveat).
**Solve-surface fingerprint** `bd2b4657f9b5df7e`.

---

## 0. G-DRIFT — form 4 is valid, and it is measured rather than asserted

Rule 29 `[R-SCREEN]` (b): the incumbent keeper's committed bundle **is** the control; no control
solve is spent. nyiso-240 established form 4 empirically rather than by hunk classification —
its four MER replay legs, solved at HEAD after 14 files / +3,176 lines of solve-path drift since
the keeper's `git_sha` `3edb8ad8`, reproduce the keeper's `dispatch/<yr>_P1.parquet` at
**sha256 byte identity in all four years** (RESULT §A.4). `origin/main` has not moved the solve
path since. This session re-verifies nothing and spends no LP on the question.

**This session's own edit DOES touch the solve path** (`scenarios.py`, `backcast_config.py`,
`run_calibration.py`, `run_calibration_full.py`), so the claim is narrower and is stated as a
gate below: the new field is **default `False`** and its off path never touches
`offer_curve_by_group`, so the control is byte-identical by construction. Gate **G-INERT**
checks it.

---

## 1. THE OBJECT

CT_PEAKER energy, model against the keeper's own committed benchmark (TWh):

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| model | 2.502 | 0.262 | 0.337 | 0.897 |
| actual | 2.829 | 2.114 | 1.911 | 2.812 |

Model CT peak capacity is intact at ~2,000–2,370 MW in every year, so the cause is **merit
order, not availability** (`docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md` §7).
The displaced energy is exactly the two C1 rows still inside half a band: 2023 `ST_GAS`
**+2.70 pp** and 2024 `CC_REGULAR` **+2.44 pp** against a ±3.0 pp band.

---

## 2. PHASE 0 — ZERO LP, and it re-aims the lever

Five probes, all on committed artifacts (the nyiso-240 MER legs, whose `dispatch/<yr>_P1.parquet`
are sha256-identical to the keeper's) plus the sanctioned `run_year(..., fleet_only=True)` rebuild
of the keeper's own recipe. Records:
`results/calibration/_nyiso241_{ct_merit_phase0,band_merit_phase0,ct_offer_anatomy,reachability_bound,lever_vs_bound}.json`.

### 2.1 The energy is NOT in the band the handoff's lever moves

Per-band CT_PEAKER dispatch (TWh) from the keeper's own `class_band_hourly` sidecars:

| band | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `committed` | 0.08 | 0.02 | 0.04 | 0.19 |
| `econlo` + `econhi` | 2.43 | 0.25 | 0.30 | 0.71 |
| `peak` | 0.00 | 0.00 | 0.00 | 0.00 |

The `committed` band carries **3.2 / 7.7 / 11.8 / 21.1 %** of the class's energy and 346.7 MW of
its 3,034.0 MW (11.4 %). The `econ` bands carry the rest and are already at the registered
**neutral 1.0**.

### 2.2 The offer anatomy, exactly

From the fleet-only rebuild (`mc_base`, `fuel_prices`) differenced against the committed P1 offer,
capacity-weighted, $/MWh:

| year | class | delivered fuel $/MMBtu | HR | fuel comp. | flat | base | startup | P1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | CT_PEAKER | **4.167** | 15.84 | 66.04 | −0.91 | 65.13 | **6.92** | 72.05 |
| 2023 | ST_GAS | 2.718 | 16.82 | 45.23 | 11.78 | 57.01 | **0.00** | 57.01 |
| 2023 | CC_REGULAR | 2.769 | 8.61 | 23.30 | 7.70 | 31.00 | 6.95 | 37.96 |

Two facts the object turns on, and neither is the band multiplier:

* **The CT fleet is charged a different delivered gas price, and the premium does not fall with
  the hub.** CT − CC_REGULAR is **+1.00 / +1.40 / +2.04 / +2.57 $/MMBtu** in 2022–2025 while
  Transco Z6 NY falls 6.86 → 1.98. At HR 15.8 that is **$16–41/MWh** of merit disadvantage. This
  is `nyiso_downstate_ct_gas_daily`'s measured LDC non-firm transport rate, and its growth tracks
  the published KEDLI/KEDNY rate steps (0.16080 → 0.22310 eff 2024-09 → 0.28530 eff 2025-04
  $/therm). It is **correct and adjudicated** — extending it to the LI CC/ST fleet is already
  REFUTED on measured evidence (matrix §5.5 DO-NOT-REDO, 2026-08-19) — so it is **not a lever and
  is not re-litigated here.**
* **`ST_GAS` pays ZERO startup amortization** (`gas_st_startup_cost` default off) while CT_PEAKER's
  `committed` rows pay **$11.97 / $16.48 / $15.78 / $13.22** per MWh. Arming it is **DO-NOT-REDO**
  for NYISO — nyiso-172 refused it two independent ways (direction on the code; grounding
  degenerate, model and measured ST_GAS both on in all 8,760 h with starts = 1) and nyiso-178/179
  re-affirmed. **This session offers no new evidence on grounding and does not re-test it.**

What that startup measurement DOES establish is the second ground for arm A below: the keeper
carries `tranche_startup_amortization`, so a 1.35 multiplicative "start hurdle" on the `committed`
rows is a **second charge for a start those rows already pay** — a rule 19 `[R-ONE-MECH]` double
count, measured rather than argued.

### 2.3 REACHABILITY — the measurement that sizes both arms

Against the keeper's **own** hourly zonal prices, a deliberately **generous** upper bound (the
fleet runs at full available capacity in every zone-hour its offer clears its own zone, with no
min-run, no ramp, no start and no competition — the LP can only do less), CT_PEAKER energy in TWh:

| year | actual | control | **arm A** frozen / relaxed | **arm B** frozen / relaxed |
|---|---:|---:|---:|---:|
| 2022 | 2.829 | 2.507 (89 %) | 3.119 / 3.320 (110 / 117 %) | 8.507 / 8.708 (301 / 308 %) |
| 2023 | 2.114 | 0.264 (12 %) | 0.334 / 0.544 (**16 / 26 %**) | 1.121 / 1.330 (**53 / 63 %**) |
| 2024 | 1.911 | 0.340 (18 %) | 0.445 / 0.646 (**23 / 34 %**) | 1.066 / 1.267 (**56 / 66 %**) |
| 2025 | 2.812 | 0.901 (32 %) | 1.010 / 1.145 (36 / 41 %) | 2.986 / 3.122 (106 / 111 %) |

*frozen* carries the keeper's startup markup unchanged (conservative — a row that runs more
amortizes over more hours); *relaxed* drops the moved rows' markup to their own class's `econ`
level (optimistic). Both bookends are declared here, before the numbers, rather than chosen after.

Class capacity-weighted offer scale: **arm A ×0.968–0.978; arm B ×0.788–0.875.**

**THE CONCLUSION THAT MATTERS, AND IT IS AGAINST BOTH ARMS.** In 2023 and 2024, even arm B — the
most aggressive legitimate offer-side move available, grounding *every* fuel-scaled CT band on
NYISO's own CAMPD measurement — leaves the **generous upper bound at 53–66 % of the metered
energy.** So **at least a third of the 2023/2024 CT_PEAKER object is not offer-reachable at all**,
and no offer lever should ever be proposed as its fix. The residual belongs to the price side (the
ledgered C3c tail: model 7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 / 42 actual) or to a
commitment / local-reliability obligation. Recorded here so no later session can read a favourable
C1 move as the object closing.

---

## 3. THE TWO ARMS, DECLARED EX ANTE

Both values are `_NYISO_OFFER_CURVE`'s **own registered `phys_*` measurements**
(`nyiso_campd_marginal_hr_summary.csv` p50s, n = 70). Nothing is chosen, nothing is swept, and no
value crosses an ISO boundary (rule 25 `[R-ISO-SCOPE]`: CAISO's 0.991 and NEISO's 0.985 are never
carried). Rule 21 `[R-DOF]`: **zero free parameters, zero new literals** — the arms substitute
measurements the band dict already carries.

### ARM A — `nyiso_ct_peaker_committed_measured` (NEW FIELD, this session)

`committed` 1.35 → **0.843**. `econ_low`/`econ_high` stay at the registered neutral 1.0; `peak`
stays at the $1,000-offer-cap scarcity wall 4.0.

Matrix cell **`ct_peaker_committed_measured` = `U`**, which the caiso-241 cross-ISO census recorded
verbatim as *"an ASK FOR THE NYISO LANE, never an arm from here"*. No DO-NOT-REDO applies.

Grounds, neither of them the residual:
1. **Rule 14 `[R-ACCURATE]` / rule 25.** 1.35 rests on a three-way citation ring — it reads
   "NYISO/CAISO-grounded" here, "NYISO-grounded" in CAISO and "NYISO/CAISO-grounded" in NEISO, and
   **no ISO cites a measurement.** NYISO's registered-to-measured ratio 1.35/0.843 = **1.60** is the
   largest in the model.
2. **Rule 19 `[R-ONE-MECH]`.** §2.2's measured double count with `tranche_startup_amortization`.

`authorized_price_tuning` = **NONE**, on the nyiso-232 precedent: rule 1's carve-out governs a band
identified by the **price residual**, and 0.843 is identified by NYISO's own CAMPD conduct.

### ARM B — `nyiso_ct_peaker_bands_measured` (EXISTING FIELD)

`committed` → 0.843, `econ_low` → 0.661, `econ_high` → 0.658. `peak` deliberately NOT grounded
(NYISO's 4.0 is the offer-cap wall, not a physics claim — grounding it would delete a mechanism
rather than repair a basis).

Matrix cell **`R`**, with a **sharpened re-test condition** set by nyiso-200: *"the three-way arm
on 2025 under the corrected gates of FINDING-nyiso200 §7 …, C3a-2025 the named risk; span only if
it clears; never alone."* Rule 28 `[R-MECH-MATRIX]` (a) requires new evidence to re-test an `R`
cell. The new evidence is stated plainly:

* **The partner the cell was waiting on is now armed on the keeper.** nyiso-200 stopped because
  `nyiso_gas_bridge_startup_aware` — its "commitment-real run screen" — was not yet on the keeper.
  `nyiso240_benchfix_span/meta.json` carries `nyiso_gas_bridge_startup_aware: True`,
  `nyiso_gas_commitment_bridge: True`, `nyiso_gas_bridge_min_run: True`.
* **"Never alone" is honoured**: arm B is the three-way — this field **plus**
  `cc_duct_peaking_row_scoped` (also `R`, same sharpened condition, same session) **plus** the run
  screen already on the keeper.
* **The "span only if the 2025 screen clears" staging is SPENT, not satisfied.** Rule 29
  `[R-SCREEN]` was removed 2026-09-16: *"A new config goes STRAIGHT TO THE FULL SPAN"*, and rules
  16 `[R-ALLYEARS]` / 34 `[R-SHARD-PROMOTABLE]` (c) now carry the whole of the how-many-years
  question. Arm B therefore goes to the full span directly. **C3a-2025 remains the named risk** and
  is gated below; the condition's substance survives even though its staging does not.

Arms A and B are **ALTERNATIVES, never stacked** (rule 19): B sets the same `committed` to the same
0.843. `backcast_config` raises if both are armed.

---

## 4. THE DECISION RULE — PRE-REGISTERED, AND IT IS STRUCTURAL

Owner instruction, this session: solve **both**, in parallel. The choice between them is fixed
here, **before** any result, so it cannot become residual selection (rule 1 `[R-STRUCT]`):

1. **Arm A is promotable on rule-14 grounds alone**, whatever the residual does — it replaces a
   transferred, uncited multiplier with NYISO's own measurement and removes a measured rule-19
   double count. A favourable C1 move is a **consequence**, never the case.
2. **Arm B supersedes A if and only if it clears the gates in §5** — and then it wins **because it
   grounds MORE of the offer on measurement** (rule 14 again), not because it scores better.
3. **If arm B fails a gate, arm A stands** on its own grounds.
4. **Neither arm is promotable as "the CT_PEAKER fix."** §2.3 forecloses that reading in advance.
5. **No band value moves from the two declared above.** If a gate fails, the arm is reported failed;
   it is never re-cut.

---

## 5. GATES — declared before the solve

Both arms, all four years, scored with `scripts/calibration_verdict.py` against the incumbent
keeper's committed bundle as the control (rule 29 (b) form 4).

| id | gate | bar |
|---|---|---|
| **G-INERT** | the new field OFF reproduces the keeper | control path never touches `offer_curve_by_group`; verified by construction + cache-key identity |
| **G-STRUCT** | confinement, pre-solve | arm A: exactly the CT_PEAKER `committed` rows move, max \|Δ\| **$0.00** in every other band, group and ISO; `pmax`/availability max \|Δ\| exactly 0 |
| **G-C1** | no C1 PASS → FAIL flip in any year | zero flips |
| **G-C3a** | price mean stays in band | no PASS → FAIL; **C3a-2025 is arm B's NAMED RISK** and a 2025 failure FAILS arm B |
| **G-C3b** | NRMSE no worse by > 0.01 in any year | held |
| **G-C8** | forced-share / D-2 | no new FAIL; no new D-4 conviction at the **span** guard (not a one-year union — the nyiso-150/200 scorer repair) |
| **G-CAVEAT** | caveat budget | ≤ 1 ledgered, 0 protective |
| **G-DET** | determination | does not fall below the incumbent's CALIBRATED |

**G-STRUCT is already measured for arm A** and recorded here so it cannot be re-read after the
fact: **22 rows move, 0 outside CT_PEAKER, 0 outside the `committed` band, max \|Δ\| elsewhere
exactly `$0.00e+00`, in all four years.** Committed-band offer 134.32 → 92.64 (2022),
62.92 → 49.27 (2023), 69.79 → 56.69 (2024), 105.74 → 80.80 (2025).

**Expected effect, declared so it can be wrong.** Arm A closes roughly **5–15 %** of the CT_PEAKER
miss and moves C3a by **well under $1/MWh** — the CAISO sibling, armed on an 11.0 %-of-class band
against NYISO's 11.4 %, closed **7.6 / 6.6 / 7.0 %** and moved C3a by
−0.078 / −0.043 / −0.017 $/MWh. Arm B closes materially more and carries the C3a-2025 exposure
(this field alone read −9.1 % at nyiso-199, against a ±10 % band).

---

## 6. SHARDS — rule 32 `[R-SHARD]` / 34 `[R-SHARD-PROMOTABLE]`

Two shards, launched in parallel (rule 12 `[R-PARALLEL]`: separate invocations, cap ~2 for a
per-plant multi-zone ISO; NYISO is ~4 min/year, so a four-year span is ~16–20 min).

* Each shard solves **`--year 2022 2023 2024 2025` in ONE invocation into ONE bundle** (rule 32(b);
  slim per-year fan-out is banned) and covers the ISO's **entire registered year union**
  {2022, 2023, 2024, 2025} (rule 34(c)).
* Each shard **pushes its own bundle to its own branch**, `dispatch/<yr>_P1.parquet` included, via a
  `.gitignore` negation plus a plain `git add` — never `git add -f` (rule 34(a), as corrected
  2026-09-12). A result that cannot back a promotion must not be produced (rule 34(b)).
* The parent composes, scores, registers and asks the promotion question (rule 32(d), rule 31
  `[R-RETAIN]`). Shards are archived only after fetch + checkout + verify (rule 33 (a)), and
  recovery is recorded by **full immutable SHA** (rule 33 (d)).

Out-dirs `results/calibration/nyiso241_ctcommitted_span` (arm A) and
`results/calibration/nyiso241_ctbands_span` (arm B).

---

## 7. WHAT THIS SESSION WILL NOT DO

* Not re-test `gas_st_startup_cost` (DO-NOT-REDO, nyiso-172; no new grounding evidence offered).
* Not re-litigate the downstate CT gas basis or extend it to the LI CC/ST fleet (DO-NOT-REDO,
  2026-08-19, refuted on measured EIA-923 Schedule 5 evidence).
* Not touch the winter / gas-deliverability / dual-fuel family (CLOSED, nyiso-240 §1), the
  Central-East seam or nested-cutset topology (CLOSED, nyiso-225), the hydro equality floor
  (REFUTED, nyiso-237), `nuclear_unit_availability` (`K`), or `nyiso_iroquois_winter_spread` (`R`).
* Not ground CT_PEAKER `peak` (4.0 is the offer-cap wall; `nyiso_campd_marginal_hr_summary.csv`
  carries no `peak` column, so grounding it needs a new measured artifact, not a sweep).
* Not re-cut any gate or band after seeing a result.

---

## 8. HANDED FORWARD, NOT THIS SESSION'S (carried from nyiso-240)

* `scripts/legitimacy_diagnostics.py` is **not reproducible** on nine measured columns at the 3rd
  decimal — same nine wobbles on a re-run of the identical bundle, so not drift, but it is a GATING
  artifact (C8, rule 20's conditional-pass path) and **nobody owns it**.
* `tests/scoring` carries **20 failures on clean main**; nyiso-239 and nyiso-240 each verified they
  add zero. Nobody owns it.
* The two nyiso-240 shared bench repairs move other ISOs' fossil `classFull` on their **next
  re-render** (42 C1 rows ≥ 0.05 pp, zero status changes, zero determinations flip). Those lanes are
  told, not pre-empted (rule 25).
* **G2 hydro loss** (−55.2 / −25.5 GWh in 2022/23) stays a LEDGERED OPEN ROOT-CAUSE ISSUE, not a
  caveat.
* **D-4 unit-conduct** reads False on plants 2480 / 8006 — pre-existing, identical before and after
  the nyiso-240 promotion, routes through rule 20's conditional-pass path, C8 PASSES.
* `data/raw/gas-prices/SOURCES_nyiso_downstate_ldc_transport.md` still carries a **"Quarantine:
  2023–2025 only; 2022 … holdout-quarantined (CLAUDE.md rule 22)"** note. `[R-HOLDOUT]` was removed
  2026-09-09 and the CSV now carries 12 rows of 2022 for both LDCs, so the note is stale prose over
  live data. Cosmetic; recorded, not fixed here.
