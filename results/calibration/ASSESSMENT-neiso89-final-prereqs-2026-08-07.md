# ASSESSMENT — neiso-89: the `final` prerequisites, closed and re-assessed

**Session:** neiso-89, 2026-08-07 · **Branch:** `claude/neiso-89-final-prereqs-8lzotm`
**Keeper (unchanged):** `2026-08-05-neiso-83-ca1-reclass` · **Markers:** `complete` HELD,
`final` EMPTY · **Freeze:** `holdout-freeze.json` ACTIVE.
**No out-of-training year was solved, scored or registered.** Every solve in this session is
in-sample (2023/2024/2025) and is a rule-16 throwaway diagnostic probe; none is registered.
No mechanism was tested, no `ScenarioConfig` field added, no matrix cell verdict minted.

---

## 0. Headline

> **Three of the four items neiso-87 §5 put to the owner are CLOSED. The fourth — `final` —
> is still NOT YET, and for a *better* reason than before.**
>
> - **Task 1 (data prep): DONE for what is preparable.** NEISO 2019 and 2020 now carry
>   `calibration_reference.json` blocks and renewable-capacity CSVs; every pre-existing
>   ISO-year block and CSV is byte-frozen. The third gap, `actual_tail.json` NEISO 2019, is
>   **not a gap** — it is the locked-tier interlock working, and closing it would require
>   disarming a rule-22 gate.
> - **Task 2 (the keeper defect): the premise is REFUTED — there is nothing to bisect.**
>   The keeper's own sha `f8f803dd` and HEAD `c710d17e` produce **byte-identical** NEISO 2025
>   output across ~373 commits. The drift is not code. It is not the inputs either
>   (content-addressed input hashes are identical). It is the **LP basis path**, reached
>   through an env-var knob that is not in `run_config.json` — a rule-24 hole.
> - **Task 3 (outage vintage split): CLOSED — there is no split.** One derivation created
>   2018–2026 in a single commit; the guard filtered all nine years in one pass. Zero cost,
>   no keeper input changed, no re-audit.
> - **Task 4 (`final`): DO NOT DECLARE.** neiso-87 §3.3 stands untouched and is now the
>   *whole* argument: 2019 had **zero** actual RT hours > $300, so C3c cannot discriminate on
>   NEISO's declared frontier. **This half of the session was run concurrently by neiso-90,
>   whose PR merged first; where they differ, neiso-90 governs** — it reaches the same verdict
>   on stronger evidence and corrects two things this session got wrong (§5.2, §5.2b).

**Rebased onto `main` after the fact.** Tasks 1a, 1b and 3 merged as **PR #3693** and are
already in `main`; this document and the §3 bisect are what remained. In the interval,
**neiso-90 (PR #3700) merged a concurrent `final` re-assessment** that builds on those closed
prerequisites — §5 has been reconciled against it rather than left to contradict the record.
**§3, the bisect, is unique to this session and is not covered by neiso-90.**

| task | verdict |
|---|---|
| **1a** reference + renewable CSVs | **CLOSED** — 2019 and 2020, in-sample byte-frozen (§1). |
| **1b** `actual_tail` 2019 | **NOT A GAP** — locked-tier interlock, correct as-is. A second private year ladder deleted instead (§2). |
| **2** keeper HEAD non-reproduction | **MISATTRIBUTED — code exonerated.** Cause localised to the unrecorded warm-start knob (§3). |
| **3** outage-detector vintage split | **DOES NOT EXIST** (§4). |
| **4** `final` readiness | **NOT YET** — one argument left, and it is the strong one (§5). |

---

## 1. Task 1a — NEISO 2019/2020 reference, prepared and frozen

**The recorded blocker was wrong, and the right one was already fixed.** neiso-87 §3.1 read
NEISO 2019/2020 as *"cannot dispatch"*; neiso-88 §2.3 corrected that to a `load_demand_meta`
artifact. This session confirms it end to end and takes the same F3 closure pjm-160 built for
PJM 2019 — `curate_demand_profile.curate_pre_window`, which writes each ISO's pre-window
`demand-profile` partition from **that ISO's own `DEMAND_LOADERS` adapter**, i.e. the exact
series `load_demand` serves.

**NEISO 2020 is included where PJM's is not, and the reason is measured:**

| year | hours | NaN | flagged by the physical-bounds screen | peak / median | TWh |
|---|---|---|---|---|---|
| NEISO 2019 | 8,760 | 0 | **0** | 23,973 / 13,190 = **1.82** | 118.28 |
| NEISO 2020 | 8,760 | 0 | **0** | 24,697 / 12,790 = **1.93** | 115.29 |
| *(PJM 2020, for contrast)* | 8,760 | 0 | 0 | **192,229** MW peak | 768.0 |

Both NEISO years sit inside the screen's *empirical* 2.1× bound, let alone its 5.0× ceiling.
PJM's 2020 exclusion is a PJM metering artifact and does not transfer.

**Merge, not replace — verified before the write.** The builder regenerates the whole file, so
the freeze was checked rather than assumed:

- `_demand_totals` replayed against the **committed** NEISO 2021–2025 and PJM 2019–2025 blocks
  with the new partitions present: **11 of 11 MATCH exactly** (pre-flight);
- every pre-existing ISO-year block in `calibration_reference.json` **byte-frozen** (md5 over
  the sorted block; only the top-level `generated` stamp moved);
- all 29 pre-existing `*_renewable_capacity.csv` **byte-identical** (`cmp`);
- exactly two new files: `NEISO_{2019,2020}_renewable_capacity.csv`.

**The new blocks are coherent, not merely present.** Solar 1,365.6 → 1,670.4 → 2,215.1 →
2,923.9 MW and wind 1,424.0 → 1,496.6 → 1,516.4 → 1,536.4 MW across 2019/2020/2021/2023; the
EIA-923 by-fuel benchmark resolves in full for both years, with nuclear 29.8 → 25.6 TWh across
Pilgrim's mid-2019 retirement.

## 2. Task 1b — `actual_tail.json` NEISO 2019 is an interlock, not a gap

**The cross-ISO impact review the task asked for overturns the task's premise.**
`CONSIDERED_HOLDOUT_YEARS = (2022, 2026)` was recorded as what blocks NEISO 2019. Measured
against the marker file at HEAD, it is not:

> 2019 is **locked-test** tier → needs `final` → the `final` block is **EMPTY for every ISO**
> → the tier gate refuses it whatever that tuple says.

Widening it therefore **cannot** produce a NEISO 2019 row, and this session produced none.
What the tuple actually withheld is the **validation ladder**. Full enumeration over every
(ISO, year) in the six hub series:

| | newly emitted by deleting the tuple |
|---|---|
| **6 rows** | NEISO / NYISO / PJM × {2020, 2021} — every one **validation** tier for an ISO that **already holds the validation marker** |
| **0 rows** | 2019 and H1-2026, for all six ISOs (locked tier, no `final`) |
| **0 rows** | 2018, for all six (dropped from the ladder 2026-08-06 → fail-closed to locked) |
| **0 rows** | anything for ERCOT / CAISO / MISO (no marker at all) |

**So the deliverable is the opposite of a widening: the second ladder is DELETED** (rule 26
`[R-DELETE]` — removed, not emptied, so it cannot be re-armed). Its own comment justified it on
a regime rule 22 no longer has (*"staged owner decisions taken one at a time"*); the 2026-08-06
rewrite replaced that with *"what is held out is the SCORE, never the DATA"* and made 2020–2022
the iterable touchpoints a `complete` marker exists to authorize. The emission gate now has
exactly **one** point of control — the tier marker — which is what `holdout_policy`'s own
docstring describes and what the other three rule-22 gates already do.

Four cases are pinned by test, including two that previously asserted the opposite and are
rewritten with the reason in their docstrings rather than silently flipped
(`tests/scoring/test_holdout_year_gate.py`, 27 passed). All 18 in-sample rows and all 4
pre-existing 2022 rows are md5-identical across the re-derive; the keeper re-scores unchanged
(**CALIBRATED-WITH-CAVEATS**, C3c sole caveat, C1 12/12 · free 8/8) and
`audit_keepers.py --iso NEISO` passes **0 failures / 0 warnings**.

**The interlock is armed and was verified directly** (`enforce_holdout_year_gate` at HEAD):

```
NEISO [2023,2024,2025]  --holdout-authorized=False : ALLOWED
NEISO [2022]            --holdout-authorized=True  : REFUSED (ACTIVE HOLDOUT SPEND FREEZE)
NEISO [2020]            --holdout-authorized=True  : REFUSED (ACTIVE HOLDOUT SPEND FREEZE)
NEISO [2019]            --holdout-authorized=True  : REFUSED (ACTIVE HOLDOUT SPEND FREEZE)
```

Preparing the 2019 tail row is a **one-command step at grant time** (`derive_actual_tail.py`),
not a preparation gap — and the count is already known and published from the committed bench
without it (§5).

## 3. Task 2 — the keeper defect: **there is nothing in the commit range to bisect**

### 3.1 The instruction was to bisect ~50 commits. The first measurement ends the bisect.

Two replays of the keeper's own recipe for **2025**, run against the **same data root** and
differing only in the checked-out code — one at the keeper's own sha `f8f803dd`, one at HEAD
`c710d17e`, **373 commits apart**:

| | `class_hourly` | `system` | `storage` | `reserve_family` | price |
|---|---|---|---|---|---|
| `f8f803dd` vs `c710d17e` | **identical** | **identical** | **identical** | **identical** | **0 of 8,760 hours differ**, max \|Δλ\| **0.0** |

> **The code is exonerated.** neiso-87 §4.0's premise — *"the cause lies somewhere in that
> range"* — is refuted by direct measurement. No commit in the range changes NEISO's 2025
> dispatch, so no bisect can converge and no code fix exists to find.

### 3.2 What the same replays *do* reproduce, exactly

Every fresh solve reproduces neiso-87's signature to the digit, and **they all agree with each
other**:

| arm | code | chain | xyear | Jan hours | Jan mean Δ | max \|Δλ\| | year-mean Δ |
|---|---|---|---|---|---|---|---|
| `neiso87_control_A` (already committed) | `63a8d1b9` | 2023–25 | OFF | **731** | **−3.9372** | **25.5244** | **−0.3344** |
| this session, standalone | `f8f803dd` | 2025 only | n/a | **731** | **−3.9372** | **25.5244** | −0.3344 † |
| this session, standalone | HEAD | 2025 only | n/a | **731** | **−3.9372** | **25.5244** | −0.3344 † |
| this session, chained | HEAD | 2023–25 | **ON** | **731** | **−3.9372** | **25.5244** | −0.3344 † |

† these three also carry an **August** component — 744 h, mean **−3.7250** — which is *expected
and explained*: it is neiso-87's own committed correction of the `NEISO,2025,8` basis row
(+0.04 → −0.38, measured ISO-NE MA index). `neiso87_control_A` predates that edit, which is
exactly why it shows January alone. Splitting the two: −3.9372 × 744/8760 = **−0.3344**
(January, = neiso-87's reported −0.334) and −3.7250 × 744/8760 = −0.3164 (August), summing to
the −0.6503 the post-edit arms report.

### 3.3 Five candidate causes, each eliminated by measurement rather than argument

| candidate | the test | verdict |
|---|---|---|
| **Code drift** (the recorded hypothesis) | `f8f803dd` vs HEAD, same data root, 2025 | **EXONERATED** — byte-identical (§3.1). |
| **Input data** | content-addressed `shared_inputs` hashes | **EXONERATED** — `neiso87_control_A` consumed byte-identical `campd`, `eia923`, `eia930` **and all five outage artifacts** to the keeper. (Also an independent confirmation of §4.) |
| **Solver version** | the bundle records `highspy`; the replay harness warns on mismatch | **EXONERATED** — `neiso87_control_A` ran **1.14.0**, the keeper's own version, and still diverges by the identical 731 hours. |
| **Cross-year LP warm-start** — ON by CLI default, pinned OFF by `replay_keeper` | full 2023–25 chain with the pin removed (`scripts/probes/_neiso89_replay_xyear.py`) | **EXONERATED** — 2025 output **bit-identical** to the xyear-OFF arms; 2023 and 2024 **prices bit-identical to the keeper** (0 of 8,760 hours, max \|Δ\| 0.0). The 2024 primal difference is the documented zero-aggregate marginal-tie reshuffle: **total generation Δ = 0.0 GWh**, every class's annual energy Δ = 0. |
| **A missing gitignored `data/clean/` partition** — the solve logs warn `no hydro-plant-modes clean partition for NEISO` | curated it (`curate_hydro_plant_modes.py --iso NEISO`, 174 plants / 1,911 MW), re-solved 2025 | **EXONERATED** — **identical** to the arm without it, all four sidecars, 0 of 8,760 hours. |

### 3.4 The conclusion, stated plainly

**The committed bundle is the outlier, not the replays.** Four independent solves — three code
versions, two chain lengths, both warm-start settings, two clean-cache states — agree with one
another *to the bit* and all differ from the committed artifact by the identical 731-hour
January pattern. The bundle's January-2025 does not reproduce from its own recorded recipe under
anything this session could vary, so the residual cause is **solve-time state the bundle does not
record**, not a change anyone can bisect.

**What this changes for the record (neiso-87 §4.0 / owner decision D-88.3):**

1. **The bisect is closed with a negative result** — a real one, not an unfinished search. There
   is no offending commit; D-88.3's premise does not hold.
2. **"Every NEISO A/B must solve its own same-HEAD control" still stands — for a different
   reason.** Not code drift (there is none) but bundle irreproducibility. The practical cost is
   the same; the diagnosis is not.
3. **The reproducible answer is now known.** A keeper replay at HEAD lands on 2025 mean λ
   **69.399 $/MWh** (with the corrected Aug-2025 basis) against the bundle's registered
   **70.0493** — and, unlike the bundle, it reproduces exactly on re-run.

### 3.5 Two reproducibility holes this surfaced, worth reporting beyond NEISO

- **`MARKET_SIM_WARMSTART_XYEAR` is a solve-affecting env knob absent from `run_config.json`**
  (rule 24 `[R-REGISTRY]`: *"no env-var knobs"*). It is excused in
  `run_calibration_full.py`'s own docstring as *"basis-neutral by design"*. This session
  **verified that the neutrality claim holds at NEISO** — so the excuse is sound on the merits
  here — but the supporting evidence in `docs/cross-year-warmstart.md` covers **ERCOT and MISO
  only**, and already documents a MISO-2025 dual-degeneracy price exception. A per-ISO-evidenced
  claim is not a design guarantee, and the gate's resolved value should be recorded in the
  bundle so a replay can match it instead of assuming.
- **`highspy` is unpinned** (`pyproject.toml`: `highspy>=1.7`), so every fresh container installs
  whatever is current. **The committed bundle fleet has already split mid-program**: surveying
  every `run_config.json` on disk, **73 bundles record 1.14.0 and 11 record 1.15.1**, the break
  falling on **2026-08-05/06** and spanning **all six ISOs** (ERCOT, MISO, NYISO, NEISO, CAISO).
  The replay harness detects and *warns* on the mismatch — it warned in this session — but
  nothing pins it. This is cross-ISO infrastructure and is reported, not changed here.

### 3.6 The fix, recommended and deliberately not taken

**Re-solve and re-register the NEISO keeper at HEAD** — one bundle, `--year 2023 2024 2025`,
in-sample, rule-16 compliant. It replaces an irreproducible artifact with a reproducible one and
picks up the neiso-87 Aug-2025 basis correction in the same step; the expected 2025 mean λ is
**69.399**. This session does **not** do it, because re-registering the designated keeper is a
promotion-class act with obligations attached that belong to the session that takes it: the
rule-15 dashboard registration, `audit_keepers` check M1, and the rule-22 **D-5(b)
determination re-verification** against `calibration-complete.json` (NEISO holds `complete`, so
its entry re-keys and its determination must be re-verified — and a *worse* determination stops
the promotion and escalates to the owner). Diagnosis was this session's remit; the promotion is
the owner's call.

## 4. Task 3 — the outage-detector vintage split does not exist

Four independent legs, recorded in full in the register's own note
(`docs/holdout-data-equivalency-register-2026-07.md`, NEISO model-inputs section):

1. **One creation, all years.** `campd-unit-outages-NEISO.csv` does not exist in `59f8bc30^`.
   Commit `59f8bc30` (2026-07-24) **creates** it — git raw status `A`, `000000 → 100644`,
   **4,484 insertions / 0 deletions** — covering 2018–2026 in a single derivation. Never
   deleted, never renamed; exactly two commits have ever touched it.
2. **The second commit filtered uniformly.** `6a8f285c` (2026-07-26, neiso-65) is
   **0 insertions / 1,294 deletions**, and the layup companion it created carries exactly those
   1,294 windows spanning **2018–2026** (138/173/146/209/161/104/153/187/23). The merit-order
   guard ran on all nine years in one pass. 4,484 − 1,294 = **3,190** = the current line count.
3. **The detector fingerprint is uniform.** Identical `capacity_source` taxonomy every year;
   the **5.00-day minimum-duration floor is exactly the minimum in every year 2018–2026**;
   median duration 10.5–15.1 d with no cliff at the 2022/2023 boundary; 33–35 distinct
   facilities/yr for 2018–2024. The lone gradient (`eia923_netzero`: 2/2/1 in 2020–2022 then
   2/3/23 in 2023–2025) runs *through* the in-sample window, so it is not a
   2018-2022-vs-2023-2025 signature.
4. **The superseded counts are the tell.** The register's own figures — 573/656/587/606/502
   appended windows and a "committed 968 rows" prefix — match nothing in the current file
   (**434/483/441/397/340** for 2018–2022, **981** for 2023–2025). The `scripts/archive/`
   appenders it cites are archived because they were retired.

Independently corroborated by the content-addressed input hashes in §3: **all five outage
artifacts are byte-identical across the keeper, the neiso-87 control and both of this
session's arms.**

The entry was **true when written** and describes a predecessor artifact the 2026-07-24 all-ISO
backfill superseded two days before the register's NEISO section was written. The identical
conclusion was already recorded for NYISO in the mechanism matrix §5.6; only the register
lagged. **Neither remedy the task offered is needed** — no reconstruction, no re-derivation, no
keeper-input change, no re-audit. *(Rule 25: the NYISO row carries the same stale premise and is
left for the NYISO lane, with the method flagged in the note.)*

## 5. Task 4 — `final` readiness, re-assessed

### 5.1 The blockers neiso-87 listed, re-measured at HEAD

| neiso-87 §3.2 item | status now |
|---|---|
| `eia_demand_profiles` — "**BLOCKING**, cannot dispatch" | **NOT A BLOCKER, and never was.** `load_demand` resolves NEISO 2019/2020 at 8,760 h off the per-BA `ISNE hourly` extract (neiso-88 §2.3; re-confirmed here). |
| `calibration_reference.json` — **BLOCKING** | **CLOSED** (§1). |
| `NEISO_2019_renewable_capacity.csv` — **BLOCKING** | **CLOSED** (§1). |
| `actual_tail.json` 2019 — **BLOCKING** | **NOT A GAP** (§2) — the locked-tier interlock, and a one-command step at grant time. |
| `campd-unit-outages-NEISO.csv` vintage split — "highest-materiality remaining" | **DOES NOT EXIST** (§4). |
| `capacity_actuals_neiso.csv` (2021–2025) | **DISSOLVED** — neiso-90 measured **zero consumers in `src/market_sim/`**; it is the capacity-hindcast target, not a backcast input (§5.2). |
| `parasitic_load_factors` — per-year 2022–2025, 2019 on the pooled `year==0` row | **DISSOLVED** — the per-year rows have **no consumer**; the only solve-path reader takes the pooled `year==0` rows exclusively (§5.2). My original "open, bounded item" framing was wrong. |
| AGT daily / monthly basis / emission rates / CO2 rates / EIA-930 / EIA-860 / NOAA / F923 | all confirmed present for 2019 (AGT 2019 has **56** prints — more than 2025's 30). |

### 5.2 The `parasitic_load_factors` asymmetry — **REPORTED HERE, THEN REFUTED BY neiso-90**

This section originally recorded `parasitic_load_factors.parquet` as a live-but-bounded input
asymmetry: per-year rows for `{2022, 2023, 2024, 2025}` only, with 2019/2020/2021 falling to
the pooled `year == 0` row. I judged it non-blocking (2021 shares the fallback, so it is not a
`final` prerequisite) and declined to close it because `derive_parasitic_load.py` rewrites a
**cross-ISO** file and recomputes the pooled row every keeper consumes.

**That framing is wrong, and neiso-90 (merged PR #3700) measured why.** The asymmetry is not
merely low-materiality — it is **inert**. The only solve-path consumer,
`campd_bins._ramp_parasitic_factor_map`, reads the pooled `year == 0` rows **exclusively**; the
per-year rows have no consumer at all. So there is nothing for a missing per-year row to
degrade, and no cross-ISO re-audit question to weigh. neiso-90 dissolves
`capacity_actuals_neiso.csv` the same way — **zero consumers in `src/market_sim/`**; it is the
capacity-hindcast target, not a backcast input.

Both rows in §5.1 should be read through that correction: neither is an open item.

### 5.2b Correction, and a hazard this session got wrong

**§5.3 below is superseded in one important respect by neiso-90's merged re-assessment
(`ASSESSMENT-neiso90-final-reassessment-2026-08-07.md`), and the difference is not cosmetic.**

This session (following neiso-87 §3.3) predicted that spending 2019 would yield a **free
small-count PASS** on C3c. neiso-90 shows the realistic outcome is **worse than that**:
`actual_tail.json` has no NEISO 2019 row, and `derive_actual_tail.py` is a **hand-run**
committed part, so a 2019 solve run before someone re-runs the deriver makes C3c **SKIP**, not
pass. A SKIP caps the determination at `CALIBRATED-WITH-CAVEATS` and names C3c unscored, and
the rule-22 C3c standing rule does **not** rescue it — that rule opens on `status == FAIL`, and
a SKIP is not a FAIL. **That is a live ordering hazard on the touch-once year**, and it is a
direct consequence of the interlock §2 correctly declines to disarm: the row cannot exist until
`final` is granted, so the grant and the deriver re-run must be sequenced together.

neiso-90 also sharpens the discrimination argument past where this session took it: 2019's
*whole-year* RT hub maximum is **$261.35**, $38.65 under the threshold (2020: $236.11), and
across NEISO's whole working span the **only** out-of-training year that can fail C3c is
**2022** — validation tier, already authorized, already spent twice, re-spendable. So no
never-touched year can ever test the criterion the frontier is declared on. Their instrument
recommendation supersedes this section's: if out-of-training evidence is wanted now, spend a
**validation touchpoint (2021, then 2020)**, which needs a freeze lift rather than a `final`
grant.

### 5.3 The argument that decides it, unchanged and now standing alone

neiso-87 §3.3, re-read from the committed bench — **an actuals-only statistic, no model output
involved**:

| year | 2018 | **2019** | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| actual RT h > $300 | 32 | **0** | 0 | 2 | 117 | 15 | 8 | 20 |
| actual RT mean $/MWh | 43.55 | **30.67** | 23.39 | 44.84 | 84.92 | 35.70 | 39.54 | 65.88 |

C3c scores small counts by absolute difference (`TAIL_SMALL_COUNT = 10`), so with actual = 0
**any model tail from 0 to 10 hours PASSES**. NEISO's declared frontier is C3c — the sole
ledgered caveat on the keeper, its one chartered lever refuted at Phase-0 (neiso-76), its
mechanism measured as a *formation ceiling* rather than a tuning residual (every reserve-family
dual exactly $0.00 in all 26,280 training hours; zero unserved-energy hours; max λ tracking the
fuel year at 249 / 218 / 281).

> **So the one-touch year would return a free PASS on the very criterion the ISO's frontier is
> declared on.** It would still exercise C1/C2/C3a/C3b/C4 — real value — but it cannot
> discriminate on the open question, and it can never be re-run to do so later.

### 5.4 Recommendation

> ### DO NOT DECLARE `final`. The reason is no longer "the inputs are not ready" — they now are, with §5.2's two remaining ⚠ rows dissolved outright. The reason is that **2019 cannot test what NEISO is blocked on.**

Spend the one-touch year **after** the C3c lane resolves, so it lands on a test that can
discriminate. `final` is an owner act and nothing in this session grants, implies or prepares
one; NEISO stays absent from `final`, the freeze stays ACTIVE, and the gates refuse every
out-of-training year (verified in §2).

**This verdict is concurrent with, and superseded in its detail by, neiso-90's merged
re-assessment**, which reached the same DO-NOT-GRANT conclusion on a stronger and partly
different basis (§5.2b). Where the two differ, **neiso-90 governs**: the expected C3c outcome
is a SKIP rather than a free PASS unless the deriver re-run is sequenced with the grant; the
named condition for spending the one-shot inverts to *specificity* testing once a tail-forming
mechanism is armed; and the recommended next instrument is a validation touchpoint (2021, then
2020), not the locked test. This section is retained as the record of what this session
concluded from its own evidence, not as a competing verdict.

**Carried forward for the owner, unchanged and not written by this session:** neiso-87 §1's
correction of the SPENT claim. The `lift_scope` field of `holdout-freeze.json` was corrected on
2026-08-06, but its **`history` entry of the same date still reads** *"the SPENT one-shot stands
as scored on the input it consumed"*. Editing a locked-tier record is an owner act; flagged, not
touched.

## 6. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed, no lever proposed, no offer curve touched. |
| 12 `[R-PARALLEL]` | Independent replay invocations run concurrently; years sequential **within** each invocation. |
| 13 `[R-MEASURED]` | §1's new blocks are measured EIA-860/-923/-930 inputs, forward-reproducible; no outcome pinned to actuals. |
| 15 `[R-DASHBOARD]` | **Nothing registered — and nothing registrable.** Every solve here is a rule-16 throwaway diagnostic probe (a single in-sample year, or a chained control), written outside `results/` and never a candidate or keeper. The keeper is unchanged. |
| 16 `[R-ALLYEARS]` | The single-year solves are the rule's explicitly permitted "throwaway diagnostic probe to isolate a single-year effect"; the chained arm covers 2023+2024+2025 in one invocation. No single-year bundle is registered. |
| 22 `[R-HOLDOUT]` | **No out-of-training year solved, scored or registered.** All solves are in-sample 2023–2025. §1/§2 are data preparation, which the 2026-08-06 rewrite places outside the marker regime; the interlock was verified still refusing 2019/2020/2022. |
| 23 `[R-FROZEN-DERIVE]` | No measured-behaviour parameter re-derived. §1/§2 re-derivations cite the data/policy change, not a residual. |
| 24 `[R-REGISTRY]` | §2 **deletes** an off-registry year ladder; §3 reports an unrecorded env-var knob as a live instance of this rule. |
| 25 `[R-ISO-SCOPE]` | No non-NEISO tuning touched. The six `actual_tail` rows added for NYISO/PJM are their own markers' authorization, enumerated in advance; the NYISO register row and the cross-ISO `parasitic_load_factors` change are left to their lanes. |
| 26 `[R-DELETE]` | `CONSIDERED_HOLDOUT_YEARS` removed outright, not emptied. |
| 27 `[R-PUSH]` | Opus session; local `Edit` only, exact on-disk bytes pushed, blob-verified for every file ≥300 lines. |
| 28 `[R-MECH-MATRIX]` | No mechanism tested ⇒ **no cell verdict minted** (duty d); no new `ScenarioConfig` field (duty c not engaged); §5.6 block added in-session (duty b). |
