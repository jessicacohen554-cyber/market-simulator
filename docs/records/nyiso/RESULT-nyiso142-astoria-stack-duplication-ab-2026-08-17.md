# RESULT nyiso-142 — the pre-registered Astoria stack-duplication A/B, executed

**Session nyiso-142, 2026-08-17.** Executes
`PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md` **as written**. Every
prediction below is quoted from the pre-registration; none was rewritten after
seeing the result, and the one that failed is reported first among the
predictions rather than last.

* control **`2026-08-17-nyiso-142-control`** — bundle `results/calibration/nyiso142_control`
* arm **`2026-08-17-nyiso-142-stackdup`** — bundle `results/calibration/nyiso142_stackdup`

Readout: `scripts/probes/_nyiso142_ab_readout.py`.

---

## 0. HEADLINE

**The correction lands, all six gates are clean, and the arm re-scores
CALIBRATED-WITH-CAVEATS with C3c the lone ledgered caveat — criterion for
criterion identical to the incumbent keeper.** The pre-registration's own
honest headline is confirmed: **most of the 2025 movement is the TARGET moving,
not the model improving** — the benchmark falls 1.204 TWh while the model falls
0.213.

Summed ST_GAS |error| over 2023–2025 goes **6.916 → 5.986 TWh**, but that number
is not the argument and was pre-committed not to be (rule 1 `[R-STRUCT]`, and
nyiso-140 is the precedent for promoting *with* a worse fit).

**One pre-registered prediction is REFUTED, and in the opposite direction: P7.**
See §2.

## 1. HOW THE PAIR WAS CONSTRUCTED

The correction had already merged to `main` by the time this session opened, so
the arm is HEAD and it is the **control** that carries the local delta:

| | `campd.CAMPD_STACK_DUPLICATE_UNITS` | `plant_emission_rates_v2` | `chp-btm-share` |
|---|---|---|---|
| **control** | emptied — a 1-line local revert, restored before the arm | the committed **defective** artifact | built from it |
| **arm** | HEAD, `{8906: {"32SH": "31RH", "52SH": "51RH"}}` | the **repaired** artifact, 18 duplicate rows folded onto their primaries | rebuilt from it |

The artifact was repaired by the surgical route
(`scripts/data/repair_v2_stack_duplicate_rows.py`), never by re-deriving — the
default derive path is a REPLACE and would have destroyed the 2018 rows (no
longer buildable since rule 22 dropped 2018 from `regenerate_clean`) and the
2022/2026 holdout-intake rows (unrepeatable by construction), the hazard
`FINDING-nyiso141` §4.2 flagged. The repair reproduces a freshly curated
`emissions-unit-annual` **MATCH on every field, including `starts` and
`op_hours`, for all six years the clean tree can still build** (2019, 2020,
2021, 2023, 2024, 2025), which is what licenses applying the same arithmetic to
the three it cannot (2018, 2022, 2026).

`chp-btm-share` turned out to be **byte-identical across the correction in every
ISO** — Astoria is ST_GAS, not CHP, so it never enters that datatype. The
clean-tree channel is therefore empty and the pair differs by exactly the source
table and the 18 artifact rows.

## 2. THE PRE-REGISTERED PREDICTIONS, SCORED

| # | prediction (verbatim, abbreviated) | outcome |
|---|---|---|
| **P7** | *"CO₂ metrics for NYISO **rise** — the class emission total was understated by construction."* | **REFUTED — it FELL.** 2025 benchmark eGRID total **29.167 → 28.335 Mt** (−0.832), ST_GAS byClass **8.096 → 7.264**. 2023/2024 unchanged. |
| P1 | 2025 ST_GAS **benchmark** falls by ≈1.31 TWh (Astoria 2.672 → ~1.359) | **CONFIRMED**, magnitude slightly smaller: classFull **16.003 → 14.799 (−1.204)**; Astoria's own entry **2.6722 → 1.3590**, the §4.1 hand computation to the digit |
| P2 | 2023 / 2024 ST_GAS benchmarks **unchanged** | **CONFIRMED exactly** — 8.7040 and 11.0713 byte-unchanged, Astoria `e_ann` unchanged at 0.7298 / 0.8709 |
| P3 | model ST_GAS falls slightly in all three years; expected small | **CONFIRMED** — **−0.085 / −0.146 / −0.213 TWh**. At source: Astoria's own dispatch **0.728→0.588, 0.809→0.584, 1.589→1.252** |
| P4 | 2025 \|error\| improves, −3.737 → roughly −2.4 | **CONFIRMED**, −3.737 → **−2.746** (a little short of the estimate, because the model fell too) |
| P5 | 2023 stays ≈ +2.2 and is **not** addressed by this fix | **CONFIRMED** — +2.263 → **+2.178** |
| P6 | system LMP moves < 0.3 $/MWh in any year | **CONFIRMED** — **+0.059 / +0.098 / +0.207 $/MWh** (upward, as Astoria's carbon-adjusted offer rises) |

### 2.1 Why P7 was wrong — stated plainly

P7 reasoned from the **unit-level rates**, which genuinely double (279–322 →
563–641 kg CO₂/MWh). But the doubling in CAMPD was in **generation only**: heat
and the emission masses were always split correctly and always summed
correctly. So the class CO₂ *mass* was never understated — and in 2025, where
the backfill put Astoria's doubled generation into the benchmark, the class
total was if anything **over**stated. Correcting the generation pulls the
benchmark CO₂ down with it.

This is a reasoning error in the pre-registration, caught by the
pre-registration. C5a is a REPORTED-ONLY stream (demoted at rubric v2.9) and
gates nothing, so nothing turns on it — but the prereg committed to disclosing
any material CO₂ move, and this is that disclosure.

### 2.2 An effect that was NOT pre-registered, and must be

**The 2025 correction moves SIX class benchmarks, not one.** As ST_GAS falls
1.204 TWh the other classes' 2025 `classFull` rise by the same total:

| class | 2025 benchmark move |
|---|---:|
| ST_GAS | **−1.204** |
| CC_REGULAR | +0.787 |
| CC_CHP | +0.281 |
| CT_PEAKER | +0.066 |
| CT_CHP | +0.056 |
| ST_CHP | +0.015 |

This is the ISO-total reconciliation redistributing what Astoria no longer
claims. It is a real property of the benchmark's construction and it flatters a
second residual we did not set out to touch: **CC_REGULAR 2025 error
+2.877 → +2.229.** Nobody predicted this and it should not be read as evidence
for anything; it is disclosed because it changes numbers the dashboard shows.

### 2.3 The adverse case that DID occur

The pre-registration's §5 first adverse case — *"model ST_GAS falls by more than
the benchmark does, so |error| gets worse"* — **did not occur in 2025** (target
−1.204 against model −0.213) **but DID occur in 2024**, where the benchmark
correctly does not move and the model still falls 0.146:

| year | error, control vs old benchmark | error, arm vs new benchmark |
|---|---:|---:|
| 2023 | +2.263 | **+2.178** (better) |
| 2024 | −0.916 | **−1.062** (WORSE) |
| 2025 | −3.737 | **−2.746** (better) |

2024's degradation is the correction working as designed — Astoria is genuinely
dearer than the model thought, so it runs less — landing on a year whose target
was already right. Under rule 14 `[R-ACCURATE]` that is a **discovered bug, not
a verdict on the correction**, and it belongs to the same open successor object
as the rest.

## 3. THE KILL GATES

| gate | pass condition | result |
|---|---|---|
| **K1′** diff scope | source diff = the stack-duplicate table + its two call sites; `run_config.json` byte-identical | **PASS, exactly as pre-registered.** **718 / 718** `scenario_config` fields identical; sha256 of the sorted config **identical** (`cf19a1d894215b90`) on both runs. The artifact diff is **17 changed CSV lines, every one keyed `NYISO,8906`** |
| **K2** feasibility | slack and dump identically 0.0, both runs, all three years | **PASS** — 0.0 / 0.0 in all six run-years |
| **K3** liveness | Astoria's benchmark falls 2.672 → ~1.359 in 2025, unchanged 2023/24; unit CO₂ rates land in 520–600 kg/MWh | **PASS.** Benchmark exactly as specified. On the rates: all eighteen merged rows land in **563–641**, matching `FINDING-nyiso141` §4.1's own target table to the decimal (2023 `51RH` 641.2, 2024 591.4/591.8, 2025 585.4/563.0). Two values sit **above** the gate's nominal 600 ceiling; the §4.1 target table is the precise pre-registered expectation and the 520–600 band was its approximation, so this is scored against §4.1 and stated openly rather than quietly widened |
| **K4** scope | no non-NYISO ISO's artifacts change; no plant other than 8906 moves | **PASS** — **0** other plants move `e_ann` in any year; the only changed files outside this session's own run namespace are the two v2 artifacts, whose entire diff is `NYISO,8906` |
| **K5** gated-criterion regression | no criterion goes PASS → FAIL on the arm | **PASS** — control and arm carry **identical** criterion statuses (C1/C2/C3a/C3b/C4/C8 PASS, C3c the miss) |
| **K6′** provenance + shape | no D-2 mechanism's forced share rises without clearing D-4 and D-1 | **PASS** — D-1 / D-2 / D-4 all pass in both arms with **0 failures**, and **no D-2 forced share moves at all**. The only movement is D-1 profile-r wobble ≤ 0.010, and ST_GAS's own D-1 profile-r *improves* (0.966→0.967 in 2023, 0.969→0.970 in 2025) |

## 4. DETERMINATION — and a caution about reading the pair's

| run | determination | why |
|---|---|---|
| control `…-142-control` | **NOT-YET** | C6 **UNATTESTED** — a fresh probe bundle carries no `calibration_attestation.json`. Following the nyiso-140 convention, the control is left unattested |
| arm `…-142-stackdup` | **CALIBRATED-WITH-CAVEATS** | C1/C2/C3a/C3b/C4/C6/C8 **PASS**, C3c the **lone ledgered caveat** — identical, criterion for criterion, to the incumbent keeper |

**Do not read the pair's determinations as an improvement.** The gap is the
attestation, not the model: on the scored criteria the two runs are the same.
C3c is **bit-unchanged** across the correction — model 21 / 3 / 24 h against RT
actual 10 / 13 / 42 h in both arms — which is expected, since C3c scores against
the hub LMP series and not the generation benchmark the correction moves.

The arm's attestation is emitted by `scripts/gen_nyiso142_attestation.py` (the
generator is the source of truth). It carries **zero new degrees of freedom**:
`n_entries` and `n_residual` are unchanged from the incumbent, because a data
correction adds no parameter.

## 5. GOVERNANCE CONSEQUENCE — the benchmark moved, so old 2025 numbers are not comparable

**Every NYISO run ever scored on 2025 was scored against an inflated ST_GAS
target**, this session's own incumbent keeper included. Registering the arm
regenerates the shared `bench/NYISO/*.json.gz`, so the keeper's *displayed* 2025
figures move too, with no re-solve. That is correct — the instrument was wrong
and is now right — but it means **post-correction 2025 figures must never be
compared to committed pre-correction ones**, and this note should travel with
any table that mixes them.

**The keeper's own determination survives the instrument change.** Re-scored on
the corrected benchmark from its committed artifacts with no solve, keeper
`2026-08-16-nyiso-140-layup-exclusion` reads **CALIBRATED-WITH-CAVEATS with
every criterion status identical** — `build_status.py --iso NYISO` moves only
its `generated` timestamp. What moves is its *reported residual*, and in its
favour:

| keeper, 2025 | error vs old benchmark | vs corrected |
|---|---:|---:|
| ST_GAS | −3.737 | **−2.533** |
| CC_REGULAR | +2.877 | **+2.091** |

2023 and 2024 are unchanged to the digit. This is the measurement
`ASSESSMENT-nyiso142-final-readiness-2026-08-17.md` §6 asked for before any
`final` decision, and it closes that objection — at the cost of one in-training
A/B rather than an irreversible locked-test year.

Two further disclosures:

* **2023 and 2024 bench files changed bytes without changing the scored
  target.** Astoria's displayed `c_ann` (CAMPD gross) falls 1.546 → 0.780 and
  1.850 → 0.930 — the hand-computed values — while its `e_ann` and the class
  `classFull` are byte-unchanged, because those years used metered EIA-923 and
  the backfill never fired. P2 is confirmed on its substance; the byte diff is
  the correction reaching the *displayed* CAMPD series.
* **The control reproduces the committed benchmark exactly.** Registering the
  control alone changed **no** bench file — an implicit control check nobody
  asked for, and a useful one.

## 6. WHAT THIS DOES NOT CLOSE

Restated because the pre-registration required it (§6) and because the improved
summed error invites the opposite reading:

* **≈ −2.75 TWh of genuine 2025 downstate ST_GAS under-production remains**, and
  **+2.18 TWh of 2023 over-production is untouched.**
* **2024 got worse** (−0.916 → −1.062), for the reason in §2.3.
* The CC-for-steam substitution is unexplained by this correction. It is
  identified separately, and localised to Zone J, in
  `FINDING-nyiso142-incity-cc-outage-substitution-2026-08-17.md`, whose named
  successor is `nyiso_incity_commitment_obligation` (matrix cell `U`, **named
  there, not armed**).

Any reading of this A/B as "the downstate ST_GAS residual is explained" is
unsupported.

## 7. HOLDOUT AND SCOPE

`--year 2023 2024 2025` in ONE bundle each, sequential within the run (rules 12,
16). **No year outside the training window was solved, scored or registered.**
The holdout spend freeze is untouched and remains ACTIVE. Rule 25
`[R-ISO-SCOPE]`: NYISO only; the correction table carries one facility and the
diff is Astoria-only.

The Astoria repair *did* rewrite `plant_emission_rates_v2` rows for 2018, 2022
and 2026 — which is not a spend and needs no marker. Rule 22 as rewritten
2026-08-06: *"an input is either the best measured representation of a
physical/market quantity or it is not, and if it is, it belongs in every year"*,
and *"Data intake needs NO per-ISO/per-window authorization and no marker."* The
`--holdout-intake` one-shot guard is untouched — that path *adds* quarantined
rows and may run once; this repair *corrects rows already present* under a
byte-freeze assertion on everything else.

**No keeper change is made by this session.** The arm is a promotion
*candidate* on the record — same recipe, corrected intake, zero DOF, no gated
criterion regressing — and
`ASSESSMENT-nyiso142-final-readiness-2026-08-17.md` §6 argues the re-score
should precede any `final` decision. Promoting it is the owner's call.
