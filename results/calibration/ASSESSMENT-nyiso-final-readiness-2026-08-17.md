# ASSESSMENT — NYISO `final` (locked-test) readiness under rubric v3.3

**Session:** iso-final-readiness (PJM/NYISO/NEISO sweep) · **Date:** 2026-08-17 ·
**HEAD:** `d1932e8` · **Branch:** `claude/iso-final-readiness-assessment-gx3iei`
**Keeper:** `2026-08-16-nyiso-140-layup-exclusion` (bundle `results/calibration/nyiso140_exclusion_arm`)
**Markers:** `complete` HELD (2026-07-31, re-keyed 2026-08-16) · `final` **EMPTY** ·
**Freeze:** `holdout-freeze.json` **ACTIVE** at HEAD.

**THIS DOCUMENT GRANTS NOTHING AND SPENDS NOTHING.** No year — in or out of training — was
solved, scored or registered. No LP was constructed. Every number below is a committed
artifact, an on-disk measured input, or a published actual.

---

## 0. Recommendation

> ## **NOT YET.** On the merits — and NYISO is the **least** ready of the three ISOs in this sweep.

**Read §1 first.** NYISO's keeper reads CALIBRATED at HEAD, but that status is carried
**entirely by the v3.3 caveat re-reading**, not by a criterion that changed. Under v3.2 the
same run, on the same artifacts, reads CALIBRATED-WITH-CAVEATS. **No new evidence of model
standing was produced by the amendment, and the amendment is therefore not declaration
evidence.** The task prompt asked for this to be said plainly if found; it is what was found.

Four independent grounds, any one sufficient:

| # | ground | status |
|---|---|---|
| 1 | **Neither locked-test year can be built on the frozen keeper config.** The keeper arms `nyiso_dynamic_reserve_requirements=True`; the required series exists for **2022–2025 only** and the loader **raises** rather than falling back (§3.1). H1-2026 fails even earlier — `load_demand` raises. | **blocking** |
| 2 | **2019 cannot be scored.** `calibration_reference.json` has **no NYISO 2019 block** (2022–2025 only) and `NYISO_2019_renewable_capacity.csv` does not exist. C1 and C2 — two load-bearing criteria — have no benchmark (§3.3). | **blocking** |
| 3 | **2019 cannot exercise the criterion NYISO is caveated on.** The real market had **1** RT hour over $300 in 2019, below `TAIL_SMALL_COUNT`, so C3c is scored one-sided (§3.4). | **blocking** |
| 4 | **The touchpoint loop has never been entered.** NYISO has run **no** validation year — not 2022, not 2021, not 2020 (§4). It is the only ISO of the three with zero out-of-training evidence of any kind. | **blocking** |

Plus the **ACTIVE freeze**, which is owner-level and outranks the marker.

**Ground 4 is the one that should decide it even if the others were closed.** `final` sits
above a ladder NYISO has not set foot on. Spending the touch-once tier first inverts the ladder
completely.

---

## 1. Determination — confirmed, and it **is** a v3.3 artifact

`python3 scripts/calibration_verdict.py --run-id 2026-08-16-nyiso-140-layup-exclusion`,
committed artifacts only, no solve, run at HEAD this session:

> **CALIBRATED** · scorable years 2023, 2024, 2025

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | **PASS** |
| C2 system volume (gas/coal families) | LOAD | **PASS** |
| C3a mean LMP | LOAD | **PASS** |
| C3b price duration/shape | LOAD | **PASS** |
| **C3c price tail / scarcity (RT hourly)** | SUPP | **CAVEAT [ledgered]** |
| C4 fleet hourly dispatch correlation | SUPP | **PASS** |
| C6 governance gate | PROT | **PASS** |
| C8 forced-energy share (D-2) | PROT | **PASS** |

D-10 free-class C1: all 14/14 · free 10/10. 0 FAILs, **1 ledgered caveat**.
Determination basis, verbatim: *"1 ledgered caveat(s) (measured-input or model-class) —
REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity
(RT hourly)."*

### **Is CALIBRATED carried by the v3.3 re-reading, or by criteria that actually pass?**

> **By the v3.3 re-reading. Say it plainly: this status is a relabelling, not a result.**

Three independent confirmations:

1. **The determination basis line says so itself** — the only thing on it is the ledgered
   caveat and the note that v3.3 does not downgrade on it. On a run carried by passing
   criteria the basis reads *"all criteria pass, governance attested"* (compare PJM).
2. **The marker's own preserved prior text** records the same run, same artifacts, reading
   **CALIBRATED-WITH-CAVEATS** before the amendment.
3. **The v3.3 amendment block's measured effect list** names
   `2026-08-16-nyiso-140-layup-exclusion` explicitly as one of the two keepers that flipped
   CALIBRATED-WITH-CAVEATS → CALIBRATED, *"NO SOLVE RAN — this is a scorer-side
   reclassification on the committed artifacts."*

**What did not change, and matters more than the label.** C3c still reads **CAVEAT, never
PASS**; the miss is still reported at full magnitude; it is still listed in `caveats.ledgered`
and counted in `grade_summary.ledgered`; it still spends the single ledgerable slot. The
underlying misses are unchanged:

| year | model RT h > $300 | actual | ratio |
|---|---|---|---|
| 2023 | 21 | 10 | **2.10×** (over-produced) |
| 2024 | 3 | 13 | **0.23×** (under-produced) |

Both outside the `[0.5×, 2.0×]` band, and **in opposite directions** — the model both invents
and misses scarcity depending on the year. That is a live, diagnosed, unclosed structural
limitation of the five-zone representation (Zone-K reliability carried by two proxies, a
too-tight transfer bound and a min_gen floor, that trade against each other — nyiso-130 K6).
v3.3 changed what that costs the *label*. It changed nothing about the model.

**Implication for `final`:** a determination that improved without a single criterion moving
supplies no new evidence for the most irreversible decision in the policy. NYISO's substantive
standing today is exactly what it was on 2026-08-16.

## 2. Rule 22 D-5(b) re-key — verified, no drift, no repair required

`python3 scripts/audit_keepers.py` → **PASS: 0 failure(s), 0 warning(s)**.

| check | NYISO state |
|---|---|
| `complete.NYISO.keeper` | `2026-08-16-nyiso-140-layup-exclusion` — **matches the current designated keeper** |
| `complete.NYISO.determination` | re-verified 2026-08-17 without a solve, under v3.3, with the improvement and its cause both recorded; D-5(b) worse-determination stop correctly did not fire |
| `keeper_at_declaration` / `keeper_at_prior_rekey` | `2026-07-30-nyiso-100-silretire` / `2026-08-08-nyiso-133-cod-arm` — preserved |
| `rekey_history` | present, 5+ entries |
| check **M1** | **PASS** |

**No drift found; nothing was edited in NYISO's shard or anywhere else.** The marker text is
notably honest about the amendment — it states that no criterion moved and that the holdout
posture is untouched. That framing is correct and this assessment adopts it.

## 3. `final` readiness on the merits

### 3.1 Neither locked-test year can be built on the frozen keeper config

**Verified at HEAD this session, not inherited.** The keeper's `run_config.json`:

```
calibration_flags.nyiso_dynamic_reserve_requirements = True
scenario_config.nyiso_dynamic_reserve_requirements  = True
```

The required intake exists for **2022–2025 only**:

```
data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{2022,2023,2024,2025}.csv
```

and the loader **fails closed** (`src/market_sim/data/reserve_requirements.py:226-232`):

> `FileNotFoundError: nyiso_dynamic_reserve_requirements=True but the measured requirement
> series is absent: … the flag must not solve on the static requirements it claims to replace.`

So **2019 cannot be built on the frozen config**, and closing the gap would require choosing a
covering requirement series *after* the config was frozen — a methodology decision a touch-once
test cannot absorb.

**H1-2026 fails one step earlier still:**

```
NYISO 2026: BLOCKED  ValueError: No EIA-930 data for ISO 'NYISO' in year 2026
```

`eia_demand_profiles.parquet` carries 2021–2025 only. The year is **unsolvable**, not merely
unscoreable.

### 3.2 2019 demand *does* resolve — the one thing that is ready

Data-layer resolvability probe (no LP, no model output):

| year | shape | system peak | annual energy | zero hours |
|---|---|---|---|---|
| **2019** | (5, 8760) | **27,622 MW** | **131.3 TWh** | 0 |
| 2023 | (5, 8760) | 26,753 MW | 123.6 TWh | 0 |

A dense, plausible full 8760. Recorded so the next session does not re-derive it — but it is
moot while §3.1 stands, because the LP still cannot be constructed on the keeper's own flags.

### 3.3 Two load-bearing criteria have no 2019 benchmark

| scoring input | NYISO 2019 | note |
|---|---|---|
| `calibration_reference.json` | ❌ **BLOCKING** | NYISO block covers **2022–2025 only** (PJM and NEISO both carry 2019). Blocks **C1** and **C2**. |
| `NYISO_<y>_renewable_capacity.csv` | ❌ **BLOCKING** | `_validation-source` holds NYISO **2022–2025 only** (PJM has 2019; NEISO has 2019 *and* 2020). |
| `actual_tail.json` | ⚠️ by design | no 2019 row for any ISO; `derive_actual_tail.py` sets `ALLOWED_YEARS = CALIBRATION_YEARS` and emits out-of-training rows only on the tier marker. Materializes on grant — correctly fail-closed, not a gap. |
| `actual_lmp_hourly_NYISO.parquet` | ✅ | 2018–2026, 8760 rows/yr. |
| demand | ✅ | §3.2. |

**NYISO is the only ISO of the three missing 2019 rows in both `calibration_reference` and
`renewable_capacity`.** Both are data prep — unrestricted under rule 22, no marker or lift
needed — but both must land *before* a grant, not after.

### 3.4 2019 cannot exercise the criterion NYISO is caveated on

Actuals-only, from the committed `actual_lmp_hourly_NYISO.parquet` hub series. No model output
involved. `TAIL_THRESHOLD["NYISO"] = 300.0`, `TAIL_SMALL_COUNT = 10`.

| year | 2018 | **2019** | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1-2026 |
|---|---|---|---|---|---|---|---|---|---|
| RT h > $300 | 25 | **1** | 1 | 3 | 101 | 10 | 13 | 42 | **85** |
| RT mean $/MWh | 35.15 | **24.96** | 19.41 | 37.04 | 74.74 | 30.28 | 35.97 | 60.72 | 71.75 |
| RT max $/MWh | 1,224 | **372** | 343 | 584 | 2,944 | 1,175 | 1,064 | 1,982 | 1,900 |

2019's actual count is **1 < TAIL_SMALL_COUNT**, so C3c is scored by absolute difference:
**any model tail of 0–11 hours PASSES.** The test is one-sided. It can catch gross
over-production (the keeper produced 21 h in 2023, which *would* fail), but it is structurally
**incapable of testing the under-production half of NYISO's actual miss** (2024: 3 vs 13). Half
the diagnosed defect is invisible in 2019 by construction.

**The year that would discriminate is H1-2026 — 85 actual tail hours in 4,343 h — and that year
is unsolvable (§3.1).** This is the sharp point of NYISO's position: the informative locked-test
year cannot be run, and the runnable one cannot inform.

### 3.5 The freeze is ACTIVE

`"active": true`, re-armed 2026-08-06, scope `isos: ALL`, tiers `[validation, locked_test]`.
Checked before the marker, fails closed. Owner-only to lift.

## 4. Touchpoint loop (rule 22) — never entered

| rung | run | determination | state |
|---|---|---|---|
| **2022** | — | — | **never run** |
| **2021** | — | — | **never run** |
| **2020** | — | — | **never run** |

Confirmed three ways: no NYISO registry sidecar declares a year outside 2023–2025;
`frontend/data/backcast/bench/NYISO/` holds **2023/2024/2025 only** (PJM and NEISO both hold
2022); and `keepers/NYISO.json` has **no `holdout_touchpoint` block at all** — the only shard
of the three without one.

**Nothing is undiagnosed, because nothing has been surfaced.** That is the problem, not a
clean bill: NYISO has **zero out-of-training evidence** and the loop's diagnose→re-train→
re-test cycle has never run once.

**The 2022 rung was formally refused on data readiness** (`ASSESSMENT-nyiso134-2022-readiness-
2026-08-14`): three measured inputs — RGGI, Central-East TTC, SCR/EDRP vintage — were degraded
for 2022 and **all three failed silently**. Its §7 records all three as **FIXED later the same
session** across 2018/2019–2022, so the standing blocker is now the freeze rather than the
data. **The 2022 touchpoint is therefore the correct next step for NYISO — and it needs only an
owner lift, not a `final` grant.**

One further item, carried from `ASSESSMENT-nyiso142-final-readiness-2026-08-17` and not
re-measured here: nyiso-141 found the **2025 ST_GAS benchmark inflated by ≈1.31 TWh**, so every
NYISO run ever scored on 2025 — this keeper included — was selected against an inflated target.
The measuring instrument changed; the keeper should be re-scored on the corrected one before
any one-shot is contemplated.

## 5. What would change the answer

1. **Walk the ladder.** Spend 2022 first (owner lift only — the data is now ready), then 2021,
   then 2020, running the full diagnose → re-train-on-2023–2025 → re-test loop.
2. **Intake `NYISO_reserve_requirements_2019.csv`** (or the owner adjudicates the frozen
   config's requirement source for 2019) so the LP can be built.
3. **Extend `calibration_reference.json` and `renewable_capacity` to 2019** so C1/C2 can score.
4. **Re-score the keeper on the corrected 2025 ST_GAS benchmark.**
5. **Make H1-2026 solvable** — it is the only locked-test year that can actually discriminate
   on C3c for NYISO.
6. The owner **lifts the freeze**.

Items 2, 3 and 5 are data prep and need no grant. Item 1 needs a lift, not a `final`
declaration. **None of this requires spending the locked tier, and all of it should precede it.**

---

*Precedent for a NOT-YET-on-the-merits recommendation:
`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md`.
Immediate predecessor for NYISO: `ASSESSMENT-nyiso142-final-readiness-2026-08-17` (same day,
pre-v3.3 framing); this assessment independently re-verifies its grounds 1 and 3 at HEAD, adds
the v3.3 determination analysis (§1) and the touchpoint-loop finding (§4).*
