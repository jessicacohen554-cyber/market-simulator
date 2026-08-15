# ASSESSMENT — neiso-94: the `final` question on the repaired envelope, and the Pilgrim adjudication

**Session:** neiso-94, 2026-08-15 · **Branch:** `claude/neiso-94-final-pilgrim-x539z0`
**Keeper:** `2026-08-14-neiso-93-envelope` (read from `frontend/data/backcast/keepers/NEISO.json`)
**Markers:** `frontier` HELD (2026-07-11) · `complete` HELD (2026-07-07, validation tier) · `final` **EMPTY**
**Freeze:** `holdout-freeze.json` **VERIFIED ACTIVE AT HEAD** — `"active": true`, re-armed 2026-08-06,
scope `isos: ALL`, tiers `[validation, locked_test]`. No grant is inferred and none exists. NEISO's
locked test remains **NEVER GRANTED and NEVER SPENT** (owner decision D-23).

**NO YEAR WAS SOLVED, SCORED OR REGISTERED — in or out of sample.** No LP was constructed. No model
output was *produced*; the only model output *read* is the committed keeper bundle's own hourly
sidecars, for the §3.3 verification. Every other number is a committed input or a published actual.
Under rule 22 as rewritten 2026-08-06 — *"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA"* — input
inspection is unrestricted; the spend is looking at an out-of-training answer, which nothing here
does. No mechanism was tested, no lever opened, no matrix cell verdict minted, no keeper changed,
no governance file edited.

Probes: `scripts/probes/neiso94_pilgrim_vintage_audit.py` → `results/calibration/_neiso94_pilgrim_vintage_audit.json`
(new), and `scripts/probes/neiso90_final_prereq_audit.py` re-run at the post-neiso-93 HEAD.

---

## 0. Recommendation

> ### DO NOT GRANT `final`. The answer is still NO on the merits — and neiso-93's work moved it **further** from a grant, not closer.
>
> **The C3c reason has not moved and cannot move.** 2019's whole-year RT hub maximum is
> **$261.35** against a $300 threshold, and its actual RT hours > $300 is **0**. That is a property
> of the 2019 market, not of the model or the repo, so no input repair can touch it. neiso-93
> changed model-side inputs only; C3c discrimination is a function of the **actuals**. neiso-90 §3
> stands verbatim.
>
> **And neiso-93's own new blocker is, on measurement, a disqualifier rather than a caveat.** The
> Pilgrim fleet-vintage gap is **−2.146 TWh** of missing nuclear concentrated in Jan–May 2019,
> against a C1 fuel-mix volume band for that year of **±2.366 TWh**. A single known, already
> diagnosed, *repairable* input defect consumes **91 % of the entire C1 error budget** before the
> model makes its first mistake — and, because nuclear is a pinned class C1 never scores, the
> shortfall does not surface where it originates. Energy balance exports it onto the C1-scored gas
> row and the seam imports, where it is **indistinguishable from model error**.
>
> **The gap is repairable, the mechanism already ships, and the fix is not NEISO-local.** See §2:
> (a) **YES**, (b) **YES — 264 plants / 21.5 GW across all six ISOs**, (c) **YES, it disqualifies
> 2019**. The named next object is the charter written this session,
> `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`.

| prompt question | answer |
|---|---|
| **1a** Is the Pilgrim gap repairable? | **YES.** The mid-year-retiree mechanism ships and is correct; the blocker is one constant, `RETIREMENT_WINDOW_START = 2023` (§2.2). |
| **1b** Is it ISO-agnostic, needing its own charter? | **YES.** One global constant, one cross-ISO builder, **264 plants / 21,467.5 MW** added across all six. NYISO's Indian Point is the same defect and the same fix (§2.3). Charter written; **no patch landed** (§2.5). |
| **1c** Does it disqualify 2019 as a locked test? | **YES** — 91 % of the C1 band, laundered onto a scored row, on a year that can never be re-scored (§2.4). |
| **2** What moved in the prerequisite audit at HEAD? | **Exactly one row** — parasitic-load factors 463 → 544 plants, neiso-93's gap 4. **Neither GAP moved.** Exactly one neiso-90 reason survives, and it is the C3c one (§3). |
| **3** Does the C3c discrimination objection still hold? | **YES, unchanged and permanently.** Nothing neiso-93 landed could have touched it (§4). |
| **4** Recommendation | **DO NOT GRANT.** Conditions in §5. |

---

## 1. neiso-93's state at HEAD, verified before anything is built on it

All of neiso-93 is in `main` and every claim the prompt makes about it checks out. Verified
directly rather than assumed, because this assessment's task list depends on it:

| claim | verified at HEAD |
|---|---|
| Four envelope gaps closed 2019–2025 | **CONFIRMED, all four.** Gap 1 nuclear anchor + NRC per-reactor overlay (3,288 → 7,670 rows); gap 2 seam tranches 2019–2025 + widened EIA-930/NYISO-proxy extracts; gap 3 `eia860_chp_by_year.parquet` now `years [2018 … 2025]`; gap 4 NEISO parasitic-load factors 2019–2025. |
| Keeper promoted to `2026-08-14-neiso-93-envelope` | **CONFIRMED.** Bundle `results/calibration/neiso93_envelope_A` committed with hourly sidecars; shard re-keyed; `audit_keepers.py --iso NEISO` reported 0 failures / 0 warnings. |
| `FINDING-neiso93-envelope-repair-2026-08-14.md` | **PRESENT.** |
| Freeze untouched, no out-of-training year spent | **CONFIRMED.** Freeze `active: true` at HEAD; the neiso-93 solve is 2023–2025 in one invocation (rules 12 / 16). |

**One prior assessment is corrected by neiso-93's gap 4, and the correction is visible in this
session's audit re-run.** neiso-90 §2 dismissed the parasitic-load row as a non-gap, on the
correct observation that the only solve-path consumer reads the pooled `year == 0` map and is
therefore year-independent — but concluded *"Nothing is disadvantaged."* That second step was
wrong: the shared file held **zero NEISO plants in any year**, tuned years included. Gap 4 raised
the pooled map from **463 to 544 plants** (§3.1), and it is the one neiso-93 change that moves the
in-sample result. Year-independence was right; harmlessness was not.

**Secondary finding, reported and deliberately NOT fixed (§6).** The keeper shard's
`disposition_note` is byte-**unchanged** across the promotion and still describes the superseded
run — including disclosed defect (i) as a live defect of "THIS KEEPER", which §3.3 shows the new
keeper closed.

---

## 2. Task 1 — the Pilgrim adjudication

### 2.1 The gap, measured independently of neiso-93, and self-validating

Pilgrim Nuclear Power Station (EIA **1590** — *not* 6098, which is Big Stone, a South Dakota coal
plant; the mis-citation was corrected by neiso-93) ran Jan–May 2019 and retired 31 May 2019. The
model's NEISO nuclear fleet is **3,355.4 MW** in three units — Millstone 2 (863.43), Millstone 3
(1,244.97), Seabrook (1,247.00). Pilgrim is in none of them.

neiso-93 sized the gap from EIA-923 at 2.177 TWh. This session re-derives it by a different route,
the **envelope self-test**: integrate the committed per-reactor availability overlay against the
model fleet's own pmax and compare to EIA-930 ISNE `NUC` hourly telemetry. Because the overlay is a
*fraction applied to units already in the fleet*, this isolates fleet-membership error and nothing
else — and it tests neiso-93's whole extension in the same pass.

| year | overlay-implied TWh | EIA-930 actual TWh | gap TWh |
|---|---|---|---|
| **2019** | **27.698** | **29.821** | **−2.123** |
| 2020 | 25.567 | 25.537 | +0.030 |
| 2021 | 27.092 | 27.026 | +0.066 |
| 2022 | 27.370 | 27.370 | −0.001 |
| 2023 | 23.159 | 23.171 | −0.012 |
| 2024 | 26.562 | 26.487 | +0.075 |
| 2025 | 27.611 | 27.460 | +0.151 |

**The repaired envelope reproduces actual nuclear to ±0.15 TWh in every year 2020–2025, and is
short 2.123 TWh in 2019 alone** — a 14–70× outlier against its own noise floor. This is a strong
result in *both* directions: it independently corroborates neiso-93's extension across 2020–2022
from a collection the anchor does not use, and it isolates 2019 as the sole defective year.

The monthly decomposition settles the cause beyond argument:

| mo | model GWh | actual GWh | gap GWh | gap avg MW |
|---|---|---|---|---|
| 01 | 2,496.4 | 2,937.5 | −441.1 | **−593** |
| 02 | 2,254.8 | 2,702.6 | −447.8 | **−666** |
| 03 | 2,471.4 | 2,970.1 | −498.7 | **−670** |
| 04 | 1,667.0 | 2,135.5 | −468.5 | **−651** |
| 05 | 1,972.2 | 2,262.1 | −289.9 | **−390** |
| 06 | 2,391.7 | 2,400.1 | −8.3 | −12 |
| 07–12 | — | — | +3.6 … +10.6 | **+5 … +15** |

**Jan–May −2.146 TWh; Jun–Dec +0.023 TWh.** A ~600 MW step that vanishes to telemetry noise in the
exact month Pilgrim retires, against a 670 MW EIA-860 nameplate. A CF mis-derivation does not
produce a step function at a retirement date; a missing generator does, and only that.

### 2.2 (a) Is it REPAIRABLE? **YES — the mechanism already ships and is correct.**

The prompt asks whether the fleet builder can carry a retired-within-year unit "the way the
COD-ramp path already masks mid-year COD/retirement unit-months". **It already does, exactly.**

`src/market_sim/data/cod_ramp.py:326-357`, `monthly_online_mask`:

```python
if retirement_year is not None:
    if retirement_year < run_year:
        on[:] = False                                   # already gone
    elif retirement_year == run_year:
        on &= months <= (retirement_month if retirement_month is not None else 12)
```

Applied at `src/market_sim/data/fleet/arrays.py:3091-3157` as a monthly **availability** mask
(`availability *= ramp`; `min_gen *= ramp`) — `pmax` untouched. Gated backcast-only
(`arrays.py:3106-3111`), `cod_ramp_enabled` default `True`.

The injection path for units the current operable snapshot no longer carries also ships:
`build_within_window_retirees` (`scripts/data/process_eia860.py:248+`) →
`eia860_generator_retired_within_window.parquet` → `load_retired_within_window`
(`data/fleet/eia860.py:1826-1891`) → injected at `runner.py:1208-1212` under
`if config.mode == "backcast"`. Its docstring names Mystic (plant 1588, ~1.4 GW CC, retired
mid-2024) as the case it was built for — **the identical shape of problem, already solved.**

**The single blocker is one constant.** `scripts/data/process_eia860.py:74`:

```python
RETIREMENT_WINDOW_START: int = 2023
```

applied at line 323 as `df = df[df["planned_retirement_year"] >= cutoff_year]`. The shipped
artifact carries **477 rows / 141 plants / retirement years 2023–2024 only / zero nuclear**. Its
own comment states the intent honestly — *"First backcast year the within-window retiree snapshot
supports … Bump only if the supported window moves."* **The supported window has moved**: rule 22
as amended 2026-08-06 makes the program's working span **2019–2025**. The constant is stale
relative to the policy, and nothing else about the design is wrong.

**The source record is already on disk.** `data/raw/eia-860/vintage_2019/eia860_generator_retired_and_canceled.parquet`
carries Pilgrim as `plant_id 1590, Retirement Year 2019, Retirement Month 5, Nameplate 670.0 MW,
BA → NEISO` — precisely the record the COD ramp needs to carry it Jan–May and zero it from June,
in a file **no fleet code reads today**. Both downstream sub-gates pass it: Pilgrim is absent from
the operable snapshot (so it survives the whole-plant-exit filter, `process_eia860.py:341`), and it
is a single-unit plant (so it satisfies `cod_ramp.py:306-312`'s "retire the plant only when every
unit has a planned retirement").

> **Verdict (a): REPAIRABLE, with zero new mechanisms and zero new free parameters.** It is a
> **source-coverage change** in the sense of rule 23 `[R-FROZEN-DERIVE]` — the window moves because
> the supported backcast span moved, not because a residual moved. It is squarely required by rule
> 14 `[R-ACCURATE]`: a real 670 MW machine that really ran is currently represented by nothing.

### 2.3 (b) Is it ISO-agnostic with six-ISO blast radius? **YES — and that decides the disposition.**

`RETIREMENT_WINDOW_START` is a **single global constant**, and `build_within_window_retirees` maps
every plant through `BA_CODE_TO_ISO` in one pass. There is no per-ISO parameter and no place to put
one without inventing an off-registry tuning channel (rule 24 `[R-REGISTRY]`). Lowering the cutoff
2023 → 2019 rebuilds the artifact for **all six ISOs simultaneously**:

| ISO | plants added | MW added |
|---|---|---|
| PJM | 83 | 8,125.4 |
| MISO | 83 | 6,682.6 |
| **NYISO** | **15** | **3,417.6** |
| CAISO | 49 | 1,361.7 |
| ERCOT | 13 | 966.0 |
| **NEISO** | **21** | **914.2** |
| **TOTAL** | **264** | **21,467.5** |

Two observations that matter:

- **NEISO's own share is Pilgrim.** Of 914.2 MW, Pilgrim is **670 MW (73 %)**; the remaining 20
  plants are all ≤ 45 MW.
- **NYISO's Indian Point is confirmed to be the same defect with the same fix.** The added NYISO
  plants include **2497 (Indian Point 2, retired 2020-04, 1,299 MW)** and **8907 (Indian Point 3,
  retired 2021-04, 1,012 MW)**, plus 6082 (655 MW, retired 2020-03). That is the `~2,060 MW of
  retired downstate nuclear` the `NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']` caveat
  (`constants.py:2111-2118`) calls permanent — *"A 2018-2021 solve is short that capacity regardless
  of this overlay."* One constant closes both ISOs' caveats.

> **Verdict (b): ISO-AGNOSTIC, six-ISO blast radius, and therefore NOT eligible to be landed as a
> NEISO-local patch in this session.** The prompt's deliverable-3 condition — *"NOT a patch landed
> in this session unless it is provably NEISO-local and in-sample-validated on 2023-2025"* — fails
> its first clause on measurement. A charter is written instead:
> **`docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`**.

**The in-sample risk is real but bounded and testable, which is what makes it charterable.** All
264 added plants retired *before* 2023, so `monthly_online_mask` returns all-`False` for every year
of the 2023–2025 training window and their availability is identically zero — dispatch *should* be
bit-identical. But `pmax` is deliberately untouched by the ramp, so fleet capacity totals, per-class
denominators, CAMPD binning and tranche construction, `_join_egrid_heat_rate` (a long-retired plant
may carry no eGRID rate), the plant-group/outage crosswalks and the LP column count all change. The
charter's gate is that this be **proven bit-identical on 2023–2025 for all six ISOs**, not assumed.

### 2.4 (c) Does the gap disqualify 2019 as a locked test? **YES.**

Not on magnitude alone — on magnitude *relative to the budget*, and on **where the error lands**.

**The budget.** C1's fuel-mix volume band (`calibration_verdict.py:322-324`) is
`min(2.0 % × ISO total load, 8 TWh)`. NEISO 2019 total load (EIA-930 `Net Generation − Total
Interchange`) is **118.28 TWh**, so the band is **±2.366 TWh**.

> **2.146 TWh ÷ 2.366 TWh = 91 % of the entire C1 volume band, consumed by one known input defect,
> before the model makes its first error.**

**Where it lands is worse than the size.** `nuclear` is in `_PINNED_CLASSES_COMMON`
(`calibration_verdict.py:~344`) and, as the code's own comment states, *"C1 only scores the fossil
gas/coal families … wind/solar/nuclear/hydro/imports … are never C1 rows"*. So the shortfall is
**invisible on the row where it originates**. Demand is a measured input in backcast mode, so the LP
must still serve it: energy balance pushes 2.146 TWh of Jan–May energy onto the margin, which in a
New England winter is gas CC and the seam imports. It therefore arrives on the **C1-scored gas row
and the interchange**, wearing the costume of a model error, with nothing in the scored output to
distinguish it from one.

**And it biases the one test 2019 could ever carry, in the wrong direction.** neiso-90 §5.2
identified the only future value of 2019: not *sensitivity* (can the model find scarcity? — never,
at actual = 0) but **specificity** (does a new mechanism *invent* scarcity in a year that had none?).
At actual = 0 h the small-count guard **FAILs any model tail > 10 h**. A 2.1 TWh nuclear hole
concentrated in the tightest five months of the year is precisely the condition that manufactures
phantom scarcity hours. So the defect pushes 2019 toward **the single failure mode C3c can detect
there** — an unrecoverable false FAIL attributable to a known, repairable input bug, on the one year
that can never be re-scored.

> **Verdict (c): DISQUALIFYING, not disclosable.** A disclosable limitation is one a reader can
> price. This one cannot be priced from the scored output, because it is laundered through energy
> balance onto criteria that do not name it — and the tier is touch-once, so it can never be
> re-measured after the repair. The asymmetry is decisive: repairing first costs a charter;
> spending first costs the year, permanently.

### 2.5 What this session deliberately did NOT do

No patch was landed. `RETIREMENT_WINDOW_START` is unchanged at 2023, `process_eia860.py` is
untouched, no fleet artifact was rebuilt, no `ScenarioConfig` field was added (so rule 28
`[R-MECH-MATRIX]` duty (c) is not engaged, and duty (d) mints no cell — no mechanism was tested).
The repair is specified in a charter and left for a session scoped to carry six ISOs' in-sample
proof.

---

## 3. Task 2 — the prerequisite audit re-run at HEAD

### 3.1 Exactly one row moved, and it is gap 4

`scripts/probes/neiso90_final_prereq_audit.py` re-run at the post-neiso-93 HEAD, diffed against the
committed neiso-90 output. **One row differs:**

| row | neiso-90 | HEAD |
|---|---|---|
| `parasitic_load_factors (pooled map)` | 463 plants | **544 plants** |

Everything else — 15 further input rows across 2019 / 2020 / the 2023 control — is byte-identical,
**including both GAPs**:

- **`actual_tail.json` 2019 — still absent.** Still the tier gate, not the data (neiso-90 §1.2):
  the source series holds 8,760 h at coverage 1.000, and `derive_actual_tail._year_emittable`
  withholds the row pending the `final` marker. Still circular and self-healing; still the ordering
  hazard of neiso-90 §1.3 — **a `final` grant that does not re-run the deriver first spends the
  touch-once year with C3c SKIPPED.**
- **`capacity_actuals_neiso.csv` 2019/2020 — still absent, still not a prerequisite** (zero
  consumers in `src/market_sim/`; a capacity-hindcast scoring target on a deliberate 2021–2025
  window).

That the audit is otherwise unmoved is the expected signature, not a null result: gaps 1–3 extended
inputs the probe already found resolvable, so closing them changes an input's *content*, not its
*availability*, which is what this probe measures.

### 3.2 Which of neiso-90's reasons survives

| neiso-90 reason | status at HEAD |
|---|---|
| **2019 cannot exercise C3c** (§5.1, the load-bearing reason) | **SURVIVES, untouched.** §4 below. |
| Re-run `derive_actual_tail.py` as step one of any grant (§5.2) | **SURVIVES** — unchanged, still un-run, still an ordering hazard. |
| H1-2026 is independently hard-blocked (§5.3) | **SURVIVES.** `actual_lmp_hourly_NEISO.parquet` still carries 2018–2025 and **no 2026 rows**; `bench/NEISO/` still 2022–2025. neiso-93 touched neither. |
| neiso-87's "2019 is unsolvable at HEAD" | **Remains withdrawn** (neiso-88 / neiso-90 §2); the audit re-confirms every solve-path input resolves for 2019. |

**Did neiso-93's four closures retire any of it? No — and they could not have.** All four gaps are
**model-side inputs**. Every surviving reason is a property of the **actuals** (the 2019 tail, the
missing 2026 benchmark) or of the **tier gate**. There is no path by which a model input could
retire one.

### 3.3 What neiso-93 DID retire — verified on the keeper's own artifacts

The prior keeper's disclosed **defect (i)** — solved on the stale `NEISO,2025,8` gas-basis row
(`+0.04`) while HEAD carried the measured `−0.38` — is **CLOSED**. Verified from the new keeper
bundle's own committed sidecar `results/calibration/neiso93_envelope_A/hourly/system_2025.parquet`:
**2025 P1 mean λ = 69.3989**, against the superseded keeper's 69.7149 and the **69.399** the old
shard predicted for a fully-current re-solve. neiso-93's gap-2 in-sample correction (2025
`NYISO_CT_base` 44.48 → **44.47**, a disclosed 2026-07-06 transcription slip) is carried in the same
run.

> **So the "the keeper is not current with HEAD" objection is retired, and it is no longer a
> precondition for a grant.** This is the one place neiso-93 moved the `final` question in the
> favourable direction — it is recorded as such, and it does not change the recommendation, because
> the two live reasons (§4, §2.4) are untouched by it.

---

## 4. Task 3 — the C3c discrimination question

**It still holds, exactly as neiso-87 §1 / D-23 and neiso-90 §3 state. No route is manufactured.**

The prompt asks whether the corrected 2019 nuclear timing overlay and seam tranches change it.
**They cannot, by construction.** C3c compares a *model* tail to an *actual* tail; whether 2019 can
discriminate is determined by the actual alone, and neiso-93 changed only model inputs. The actuals
are re-read this session from `data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet` and are
bit-unchanged:

| year | RT max $/MWh | RT h > $300 | C3c branch on a 0 h model tail |
|---|---|---|---|
| **2019** | **261.35** | **0** | small-count `\|Δ\| ≤ 10` → free PASS (**SKIP** at HEAD, no `actual_tail` row) |
| 2020 | 236.11 | 0 | free PASS |
| 2021 | 375.28 | 2 | free PASS |
| 2022 | 2,254.35 | **117** | ratio → the only out-of-training year that can FAIL |
| 2023 | 1,161.97 | 15 | ratio → ledgered CAVEAT |
| 2024 | 2,112.77 | 8 | free PASS (already taken silently, in-sample) |
| 2025 | 1,110.22 | 20 | ratio → ledgered CAVEAT |

2019's whole-year maximum misses the threshold by **$38.65**. It is not a year that narrowly lacked
a tail; it had no scarcity formation at all. And at HEAD the outcome is the *worse* of the two
branches — a **SKIP**, which caps the determination at CALIBRATED-WITH-CAVEATS and names C3c as
unscored, so the touch-once year would be spent producing a verdict silent on the very criterion
NEISO's frontier is declared on.

**Per the prompt's instruction: this still holds, so it is said and the matter stops here.** No
alternative route to a `final` grant is proposed, and §2.4's Pilgrim finding is offered as an
*additional* disqualifier, not a substitute route.

---

## 5. Task 4 — the recommendation

### 5.1 **DO NOT GRANT `final`.** Two independent reasons, one permanent and one repairable.

1. **Permanent — 2019 cannot exercise C3c** (§4). Unchanged since neiso-87; untouched by neiso-93;
   not addressable by any future work, because it is a property of the 2019 market.
2. **Repairable — the Pilgrim fleet-vintage gap** (§2). 91 % of the C1 volume band, laundered onto
   scored rows, biasing the one specificity test 2019 could ever carry. This one **can** be closed,
   and the charter says how.

Granting today would spend the single most irreversible resource in the policy on a year that
cannot test the open question **and** is known to be short a real 670 MW generator.

### 5.2 The conditions that would change it

Carried forward from neiso-90 §5.2, still the trigger: **the C3c lane arming a tail-forming
mechanism**, at which point 2019 becomes valuable as a *specificity* test. Today, with the model's
tail identically 0 in every year, that test is passed trivially and carries no information.

**Added this session, a hard precondition rather than a trigger:**

3. **The Pilgrim gap must be closed before 2019 is spent** — otherwise the specificity test in
   condition 1 is run on a fleet biased toward inventing the very scarcity it tests for.

**Retired this session:** the "re-solve the keeper at HEAD and re-key the shard" precondition, done
by neiso-93 and verified in §3.3.

Subordinate conditions from neiso-90, both still live and both cheap: re-run
`scripts/data/derive_actual_tail.py` as **step one** of any grant (§3.1), and resolve or split off
the H1-2026 half, which is independently hard-blocked (§3.2).

### 5.3 What this session does not do

`final` is an owner declaration. Nothing here declares, grants, or prepares a grant. No marker file,
no `final` block, and `holdout-freeze.json` are touched. The freeze was verified ACTIVE and never
engaged. No out-of-training year was solved, scored or registered.

---

## 6. Secondary finding — reported, not fixed

**The keeper shard's `disposition_note` is stale after the neiso-93 promotion.** Diffing
`frontend/data/backcast/keepers/NEISO.json` across the promotion, `keeper`, `prior_keeper_note` and
`note` all changed; **`disposition_note` is byte-unchanged.** It therefore still, under the current
keeper `2026-08-14-neiso-93-envelope`:

- describes the run as *"criterion for criterion identical to the superseded
  2026-08-05-neiso-83-ca1-reclass keeper"* — the wrong genealogy, since the superseded keeper is now
  `2026-08-06-neiso-87-control`; and
- discloses **defect (i)**, the stale Aug-2025 gas-basis row, as a live defect of *"THIS KEEPER"* —
  which §3.3 measures as **closed** on the new keeper's own sidecars.

The substance is harmless (the note is over-conservative, not over-claiming) and the determination
is unaffected, but a reader of the shard alone would draw a false conclusion about the current
keeper. **Not edited here**, following the neiso-90 §6 posture: repairing keeper prose is the
`calibration-keeper-auditor`'s job, and it is outside this session's scope. Flagged for the next
NEISO session.

Carried forward and still open, not re-investigated: **NEISO remains the only one of six ISOs
running the archived P2 commitment pass** (keeper frontier note item 5), escalated and unresolved.

---

## 7. Deliverables produced

| deliverable | path |
|---|---|
| This assessment | `results/calibration/ASSESSMENT-neiso94-final-readiness-2026-08-15.md` |
| Pilgrim/vintage charter (§2.3) | `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md` |
| Reproducible probe | `scripts/probes/neiso94_pilgrim_vintage_audit.py` |
| Machine-readable measurements | `results/calibration/_neiso94_pilgrim_vintage_audit.json` |
| Calibration-log continuation | `docs/calibration-log/neiso.md` |

---

## 8. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed or proposed as a fit. The Pilgrim repair is argued on structural fidelity and rule 14, explicitly **not** on any expected effect on a residual — and §2.4 declines to predict its sign. |
| 13 `[R-MEASURED]` | No measured outcome fed back anywhere. §3.3 reads the keeper's own committed sidecar to *verify a disclosed defect is closed*; nothing is pinned, tuned or fed back. |
| 14 `[R-ACCURATE]` | The core finding **is** this rule: a real 670 MW machine that really generated is represented by nothing, and the assessment refuses to let a known-inaccurate fleet be spent on a touch-once year. |
| 15 `[R-DASHBOARD]` | **No run produced ⇒ nothing to register.** No solve of any kind. |
| 16 `[R-ALLYEARS]` | Not engaged — no bundle produced. Carried into the charter's in-sample gate (all of 2023–2025, all six ISOs). |
| 22 `[R-HOLDOUT]` | **Freeze VERIFIED ACTIVE at HEAD and never engaged. NO year solved, scored or registered — 2019, 2020, 2021, 2022 and H1-2026 all untouched.** `holdout-freeze.json` and `calibration-complete.json` are unedited. All probes read committed inputs and published actuals only. No skill claim from any out-of-training number. NEISO's locked test remains **NEVER GRANTED and NEVER SPENT**. |
| 23 `[R-FROZEN-DERIVE]` | The charter's window change is justified as **source-coverage** (the supported span moved to 2019–2025 by owner amendment), never as a residual response; the charter forbids tuning the cutoff to a fit. |
| 24 `[R-REGISTRY]` | No tunable touched. §2.3 explicitly rejects a per-ISO cutoff as an off-registry channel. |
| 25 `[R-ISO-SCOPE]` | **NEISO files only.** No other ISO's shard, keeper, marker or matrix cell edited. NYISO's Indian Point is *cited as evidence* of shared blast radius (§2.3) and its cell is untouched; the charter enters every non-NEISO ISO as work to be done in its own lane. |
| 27 `[R-PUSH]` | Opus session (`claude-opus-5`). All files new or append-only; no existing file ≥300 lines rewritten. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ NO cell verdict minted** (duty d). No `ScenarioConfig` field added ⇒ duty (c) not engaged. No lever opened; the NEISO queue stays cleared and no `R`/`I`/`G` cell was re-tested. |

---

## Appendix — reproduction

```
uv run python scripts/probes/neiso94_pilgrim_vintage_audit.py
uv run python scripts/probes/neiso90_final_prereq_audit.py
git diff results/calibration/_neiso90_prereq_audit.json   # one row: 463 -> 544 plants
```
