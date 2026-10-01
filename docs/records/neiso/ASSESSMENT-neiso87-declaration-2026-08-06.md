# ASSESSMENT — neiso-87: is NEISO ready to declare `final`?

**Session:** neiso-87, 2026-08-06 · **Branch:** `claude/neiso-87-declaration-assessment-khmvod`
**Keeper:** `2026-08-05-neiso-83-ca1-reclass` · **Markers:** `complete` HELD (2026-07-07),
`final` EMPTY · **Freeze:** `holdout-freeze.json` ACTIVE (re-armed 2026-08-06).
**No out-of-training year was solved, scored or registered in this session.** The only solves
run are in-sample (2023/2024/2025), for the §4 data correction.

---

## 0. Recommendation

> ### DO NOT DECLARE `final`. NEISO is **NOT READY** — and the reason is not the model.
>
> **2019 cannot be solved at HEAD.** The primary demand driver has no NEISO rows before 2021,
> so the LP cannot be constructed at all. Three further scoring inputs are also absent. And
> even with all of them closed, **2019 cannot exercise the criterion NEISO's frontier is
> declared on**: the real market had **zero** RT hours over $300 in 2019, so C3c would score a
> trivial small-count PASS whatever the model did.
>
> Spending the one-touch year now would burn the single most irreversible resource in the
> policy on a configuration that cannot run and a test that cannot discriminate.

**Separately, and before any `final` decision is put to the owner:** the governance record
currently says NEISO's locked test was already SPENT on 2026-07-07. **That claim is false**,
it is repeated in five places, and it is the reason `final` reads as "not re-grantable" rather
than "never granted". §1 documents the artifact search; the correction is proposed, not taken
unilaterally.

| task | verdict |
|---|---|
| **A** frontier re-verification | **C3c is still the binding frontier.** The repair strengthened that finding rather than weakening it (§2). |
| **B** `final` readiness | **NOT READY** — 1 hard blocker + 3 scoring blockers + a non-discriminating test year (§3). |
| **C** preparedness audit | 9 gaps enumerated, 4 of them blocking 2019, 2 blocking 2020 (§3.2). |
| **D** stale in-sample row | Corrected, A/B-solved, results in §4. |

---

## 1. The governance precondition: NEISO's locked test is **UNSPENT**

`calibration-complete.json` states, in the NEISO entry and again in the `final` block's own
note, that the 2019 + H1-2026 one-shot "was scored ONCE with the frozen neiso-53 config and
STANDS". **The artifact record contradicts this.** Searched this session, at HEAD:

| evidence | result |
|---|---|
| NEISO registry entries mentioning 2019 | **none** (the only hit is the 2022 touchpoint's `holdout` block) |
| any bundle, bench file or metrics for a NEISO out-of-training year | `bench/NEISO/` holds **2022–2025 only**; no 2019 anything |
| `actual_tail.json` NEISO | 2022, 2023, 2024, 2025 — **no 2019 row exists to score against** |
| the memo cited as the authorization (`neiso-calibration-complete-memo-2026-07.md`) | **contains no mention of 2019 at all** (`grep 2019` → 0 hits) |
| what `locked_test_scored_on` actually points at | `2026-07-07-neiso53-winter-fuelsec-coldsnap` — a run the memo's own §1 records as **"solved full-span 2023–2025"**. It is a **config id, not a 2019 run.** |
| the memo's decision record | the 2026-07-07 owner decision authorized a one-shot on **2022** (pre-dating the 2026-07-31 tier split, when "one-shot" still meant the validation year) — and **execution was HELD the same day** pending the G-19 data-equivalency register |

This is not a new finding. The **third-party peer review** reached it independently
(`docs/third-party-peer-review-2026-07.md` §6.3 item 1): *"On the evidence, no holdout year has
ever been solved, and the 'scored once and stands' claim is documentation drift that should be
corrected before it is ever cited as an out-of-sample result."*

**No correction has landed.** `git log --all` over `calibration-complete.json` shows no commit
touching the claim. The SPENT language is still live in **13 files**, of which the load-bearing
ones are: the marker's `locked_test` and `locked_test_note` fields, the `final._note`,
**CLAUDE.md rule 22 itself** ("NEISO is the latter"), `holdout-freeze.json`, the 2022
touchpoint's registry sidecar, `docs/mechanism-testing-matrix.md`, and **10 entries** in
`docs/calibration-log/neiso.md` — plus four handoff/audit docs that repeat it second-hand.

**Consequence for the decision in front of the owner.** The `final` question is not "may a
spent one-shot be re-granted" (it may not, and that framing forecloses it). It is **"should a
never-granted one-shot be granted now"** — and §3 answers that on the merits: not yet, because
the year is unrunnable. The record should be corrected so the question is asked correctly, and
so the false claim is never quoted as out-of-sample evidence. **This session proposes the
correction and does not write it** — editing a locked-tier marker is an owner act.

## 2. Task A — frontier re-verification on the keeper's own sidecars (no re-solve)

Read from the committed keeper bundle `results/calibration/neiso83_ca1reclass_B/hourly/`.

### 2.1 The keeper re-scores unchanged under rubric v3.1

`scripts/calibration_verdict.py --run-id 2026-08-05-neiso-83-ca1-reclass` at HEAD (committed
artifacts only, no solve) → **CALIBRATED-WITH-CAVEATS, 0 FAILs**, C3c the sole ledgered
caveat, C1 all 12/12 · free 8/8. v3.1 retired C7 and narrowed ledgering to C3c alone; NEISO is
unaffected by both, as the v3.1 commit stated.

### 2.2 What is actually limiting — measured, not asserted

| year | mean λ | p99 | **max λ** | h > $200 | h > $258 | **h > $300** | slack h | reserve-dual h ≠ 0 |
|---|---|---|---|---|---|---|---|---|
| 2023 | 38.43 | 182.58 | **248.97** | 58 | 0 | **0** | 0 | **0** |
| 2024 | 43.70 | 149.38 | **218.24** | 1 | 0 | **0** | 0 | **0** |
| 2025 | 70.05 | 195.75 | **280.85** | 76 | 16 | **0** | 0 | **0** |

Every reserve-family dual is **exactly $0.00 in all 26,280 hours** across all three families
(`ne_10min_spin` 600 MW, `ne_10min_total` 1,200 MW, `ne_30min_total` 1,800 MW), with
**zero shortfall MW in every hour**, and **zero unserved-energy hours**.

**The mechanism is therefore unambiguous and is a formation ceiling, not a tuning residual:**
the LP is never capacity-short and never reserve-short, so price is always the marginal cost
of the most expensive dispatched unit. That ceiling is dual-fuel oil parity — and it **tracks
the fuel year** (max λ 249 / 218 / 281, highest in the highest-gas year), which is exactly the
signature of a marginal-cost ceiling rather than a cap. **No hour in any training year can
reach $300**, so the C3c model count is structurally 0, not incidentally 0.

### 2.3 Did the gas-basis repair change what is limiting? **No — and the way it failed to is the finding**

Two independent legs:

**(a) In-sample, the repair could not have moved anything — verified, not assumed.** The
NEISO 2023–2025 basis rows are **byte-identical across the repair commit and at HEAD**
(`md5 382113c6…` on all three: pre-`972c44dc`, post-`972c44dc`, HEAD). Those years were already
on the measured ISO-NE MA index. The keeper never consumed a defective basis row.

**(b) Out-of-training, the repair moved exactly the criteria a fuel-level error would move —
and left C3c untouched.** Comparing the two registered 2022 runs (both already committed and
scored; **read here, not re-scored**):

| criterion | 2022 touchpoint (pre-repair) | 2022 corrected basis (post-repair) |
|---|---|---|
| C3a mean LMP | **FAIL** | **PASS** |
| C3b price duration/shape | **FAIL** | **PASS** |
| **C3c price tail / scarcity** | **FAIL** | **FAIL** |

This is the discriminating experiment neiso-85 said could not be run while the input was
inverted. It has now effectively been run, and it **exonerates the input and convicts the
formation**: correcting a seasonally-inverted fuel price repaired both price-*level* criteria
and did not touch the price-*tail* criterion. **C3c is not a fuel-input artifact.**

### 2.4 C3c's own anatomy is unchanged and remains frontier-blocked

From the neiso-75 charter, still standing:

| year | actual RT | actual DA | model | gate needs | verdict |
|---|---|---|---|---|---|
| 2023 | 15 | 5 | 0 | ≥ 8 | FAIL — **the real market's own DA cleared ≥$300 in only 5 h.** No DA-type formation can reach 8. **Measured-unreachable.** |
| 2024 | 8 | 5 | 0 | \|m−8\| ≤ 10 | PASS (small-count) |
| 2025 | 20 | 12 | 0 | ≥ 10 | FAIL — majority the **cross-ISO** systemic diurnal-amplitude defect (xiso-1), not a NEISO-local lever |

The one chartered lever was **refuted on both limbs at Phase-0 (neiso-76)**. 2023's leg is
measured-unreachable at the DA ceiling; 2025's leg belongs to the cross-ISO amplitude lane,
which is an open owner call on the rubric, not a NEISO mechanism.

**Verdict on task A: C3c remains the binding frontier, on stronger evidence than before.** No
new lever is proposed — the queue is genuinely exhausted, nothing marked `R`/`I`/`G` has new
evidence against it, and rule 22's C3c standing rule exists for precisely this situation.

## 3. Task B/C — `final` readiness and the preparedness audit

### 3.1 The hard blocker: 2019 cannot be dispatched

Rule 22 requires that when we hit go on 2019 it is **already configured precisely like the
keeper, with nothing left to prepare**. Direct loader check at HEAD (no LP built, no model
output produced — a data-layer resolvability probe):

```
NEISO 2019: BLOCKED   ValueError: No EIA-930 data for ISO 'NEISO' in year 2019
NEISO 2020: BLOCKED   ValueError: No EIA-930 data for ISO 'NEISO' in year 2020
NEISO 2021: RESOLVES  (peak 25,101 MW)
NEISO 2022: RESOLVES  (peak 24,233 MW)
```

`eia_demand_profiles.parquet` carries NEISO for **2021–2025 only**. The upstream raw extract
(`ISNE hourly.parquet`) *does* cover 2018–2025 — the gap is in the repair/normalisation step,
which the G-19 register classes as the cross-ISO **F3** structural gap ("full-8760 contract; a
partial year is unbuildable by design; no builder script exists in-repo").

**This alone is dispositive: 2019 is unsolvable, so `final` cannot be spent on it.** It also
takes **2020**, the bottom of the validation ladder, off the table.

### 3.2 Per-year input consistency — the audit rule 22 asks for

Checked every measured input the keeper's `run_config.json` arms. Status **for 2019**, the year
`final` would spend:

| input | 2019 | note |
|---|---|---|
| **`eia_demand_profiles`** (primary demand driver) | ❌ **BLOCKING** | 2021–2025 only. Cannot dispatch. |
| **`calibration_reference.json`** | ❌ **BLOCKING** | NEISO block exists for 2021–2025 only; blocks C1/C2 scoring. Same root cause as above. |
| **`actual_tail.json`** | ❌ **BLOCKING** | 2022–2025 only. `derive_actual_tail.py` hard-codes `CONSIDERED_HOLDOUT_YEARS = (2022, 2026)`; a **shared cross-ISO** constant, so widening it unlocks other ISOs too. Blocks C3c scoring. |
| **`NEISO_<y>_renewable_capacity.csv`** | ❌ **BLOCKING** | 2021–2025 only. |
| `capacity_actuals_neiso.csv` | ❌ | window 2021–2025. Capacity-hindcast scoring only. |
| `parasitic_load_factors` | ⚠️ | per-year rows for 2022–2025; 2019 falls to the pooled `year==0` row. Documented fallback, low materiality — but it **is** the same per-year provenance split the gas basis had. |
| `campd-unit-outages-NEISO.csv` | ⚠️ | 2018–2026 present (483 windows in 2019), but 2018–2022 were appended at a **different detector vintage** than the committed 2023–2025 rows. The file carries **no vintage column**, so the split is invisible in the data. Row density shows no cliff, which is reassuring but not dispositive. **Highest-materiality remaining instance of the gas-basis pathology.** |
| `algonquin_citygate_daily.csv` | ✅ | 56 prints in 2019 (2018–2025 now all 30–94; **2026 has 1**). |
| **`gas_basis_by_iso_month.csv`** | ✅ | **repaired by neiso-86** — 2019 fully measured, 12/12 months. |
| `plant_emission_rates_v2` | ✅ | 2018–2026, uniform. |
| `fossil_co2_rates` | ✅ | now 2018–2026 (register said 2022–2026; **closed since**). |
| `actual_lmp_hourly_NEISO.parquet` | ✅ | **2018–2025, 8760 rows/yr, real data** (register said 2018–2019 MISSING; **closed since**). |
| EIA-930 `ISNE_{fueltype,region}` | ✅ | 2018–2026. |
| EIA-860 vintage snapshots | ✅ | per-year folders present. |
| NOAA zone / load-weighted temps | ✅ | 2018–2025. |
| F923 delivered gas + oil | ✅ | 2018–2025. |

Also noted, **not** a per-year asymmetry (it fires identically on 2021/2022/2023): the demand
loader warns that the repaired `demand-profile` clean partition is absent and it is falling
back to "the corrupted legacy `eia_demand_profiles.parquet` series (PR #1426)", advising
`scripts/regenerate_clean.py demand-profile` before solving. This affects the **in-sample**
keeper equally and is therefore consistent across the span — but it is a live warning on the
model's primary driver and deserves its own look.

**Known gaps, not re-discovered (carried forward):** 2015–2017 basis still 100 % inverted
proxy; **2018 Mar–Jun unobtainable** (ISO-NE newswire migration) so 2018 is a mixed year with
an inverted June, and 2018 is in any case **dropped** from the working span by owner decision;
2026 basis is Jan–May only and AGT-daily has 1 print.

### 3.3 Even fully prepared, 2019 cannot test the frontier

Actual RT hours > $300 at the NEISO hub (`TAIL_THRESHOLD["NEISO"] = 300`), from the committed
bench — **an actuals-only statistic, no model output involved**:

| year | 2018 | **2019** | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| RT h > $300 | 32 | **0** | 0 | 2 | 117 | 15 | 8 | 20 |
| RT mean $/MWh | 43.55 | **30.67** | 23.39 | 44.84 | 84.92 | 35.70 | 39.54 | 65.88 |

C3c scores small counts by absolute difference (`TAIL_SMALL_COUNT = 10`): with actual = 0,
**any model tail from 0 to 10 hours PASSES**. 2019 is the lowest-priced year in the record and
had no scarcity at all.

**So the one-touch year would return a free PASS on the very criterion NEISO's frontier is
declared on.** It would still exercise C1/C2/C3a/C3b/C4 — real value — but it cannot
discriminate on the open question, and it can never be re-run to do so later. That is a strong
argument for spending it *after* the C3c lane resolves, not before.

## 4. Task D — the stale in-sample `NEISO,2025,8` row

Pre-registered in `PREREG-neiso87-aug2025-basis-refresh-2026-08-06.md`, committed before any
data byte was edited.

### 4.0 An unplanned finding: **the committed keeper no longer reproduces at HEAD in 2025**

The control arm was run because the keeper's `git.sha` is unresolvable in this shallow clone,
so zero code drift could not be *proven*. It turns out not to hold. Replaying the keeper's own
recipe at HEAD against the *unmodified* committed data:

| year | `class_hourly` | `system` | `storage` | `reserve_family` |
|---|---|---|---|---|
| 2023 | **identical** | **identical** | **identical** | **identical** |
| 2024 | **identical** | **identical** | **identical** | **identical** |
| **2025** | **differs** | **differs** | **differs** | **differs** |

The 2025 divergence is **confined entirely to January** — 731 of the year's 8,760 hours, every
one of them in Jan-2025 (hour index 0 → 743), none outside it. Magnitude: **max |Δλ| $25.52**
in a single hour, **mean Δλ over the year −0.334 $/MWh** (arm A $69.715 vs keeper $70.049).

Ruled out this session, by direct comparison rather than inference:

- **Not the AGT daily series.** Rebuilt via `hubs._algonquin_daily` under both the pre- and
  post-neiso-86 file: NEISO 2025 resolves to **identical prints in every month** (Jan-2025 has
  exactly one, 2025-01-29 @ $4.06), and Dec-2024 is unchanged too.
- **Not the monthly basis rows.** NEISO 2023–2025 are md5-identical pre-intake, post-intake and
  at HEAD (`382113c6…`).
- **Not the FFR-7B RPS change**, despite it naming NEISO: `backcast_config` sets
  `rps_enabled=False`, so the RPS row is inert in every backcast.

The keeper solved at merge-base `243b4ab1…` against a HEAD roughly fifty commits back; the
cause lies somewhere in that range and was not isolated here. **Consequences, stated plainly:**

1. **The A/B in §4.1 is unaffected.** Both arms are solved at the same HEAD, in the same
   year-chain, differing only in the edited row — which is exactly what the control was for.
   Had the committed keeper been used as arm A, this January-2025 drift would have been
   misattributed to the basis correction.
2. **The keeper's registered 2025 numbers are stale with respect to HEAD**, by −0.33 $/MWh on
   mean λ. Small, but it means **any future NEISO A/B must solve its own same-HEAD control** —
   the committed bundle is no longer a valid baseline. Flagged for the owner as an open item.

### 4.1 The correction and its A/B

## 5. What the owner is being asked to decide

1. **Correct the SPENT claim** (§1) so `final` is understood as never-granted rather than
   not-re-grantable — 13 files, listed. **Not written by this session:** editing a locked-tier
   marker, and CLAUDE.md rule 22's own text, is an owner act.
2. **Do not grant `final` yet** (§3). Grant it when 2019 is runnable and — recommended — after
   the C3c lane resolves, so the one-touch year is spent on a test that can discriminate.
3. **Authorise the 2019/2020 preparation work**, which needs no marker under rule 22 as
   rewritten but does need someone assigned: rebuild `eia_demand_profiles` for NEISO 2019–2020
   (the cross-ISO F3 gap), build the `calibration_reference` blocks and renewable-capacity
   CSVs that depend on it, and widen `CONSIDERED_HOLDOUT_YEARS` — the last being a **cross-ISO**
   change that needs a cross-ISO impact review first.
4. **Adjudicate the outage-detector vintage split** (§3.2), the highest-materiality remaining
   instance of the gas-basis pathology: either reconstruct the committed recipe or re-derive
   **all** years 2018–2025 at one pinned vintage. The latter changes keeper inputs.

## 6. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed, no lever proposed; §4 is an input correction judged on correctness, not residual. |
| 13 `[R-MEASURED]` | §4's replacement is a measured, forward-reproducible published index, not an outcome pinned to actuals. |
| 14 `[R-ACCURATE]` | The governing rule for §4 — an interpolation replaced by the measured figure that now exists. |
| 15 `[R-DASHBOARD]` | §4's run registered and committed in this session. |
| 16 `[R-ALLYEARS]` | Both §4 arms solve 2023 + 2024 + 2025 in one bundle, one invocation. |
| 22 `[R-HOLDOUT]` | **No out-of-training year solved, scored or registered.** Freeze untouched and not engaged; 2025 is in-sample. §1/§3 are preparedness and record-keeping, which rule 22 as rewritten places outside the marker regime. No skill claim from any out-of-training number. |
| 23 `[R-FROZEN-DERIVE]` | §4's commit cites the data change and its publication date only. |
| 25 `[R-ISO-SCOPE]` | No non-NEISO row or cell touched. |
| 27 `[R-PUSH]` | Opus session; edits made locally and pushed as exact on-disk bytes. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ no cell verdict minted** (duty d). No new `ScenarioConfig` field ⇒ duty (c) not engaged. §5.6 updated in this session (duty b). |
