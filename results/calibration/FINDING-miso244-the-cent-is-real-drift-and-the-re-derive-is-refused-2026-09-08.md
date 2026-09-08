# FINDING miso-244 — **THE CENT IS REAL DRIFT: NOT A ROUNDING ARTIFACT, NOT A NO-WASH CLAMP.** `t_max` **0.0049998** against a **1e-4** tie bar. **The re-derive is REFUSED on rule 23's citation requirement — and my own liveness gate did NOT stop it.** ZERO LP

**KEEPER UNCHANGED: `2026-09-07-miso-243-spp-pairing`** (bundle `results/calibration/miso243_sppair_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered non-downgrading caveat, DOF ledger **41/2**.
**Nothing was solved, armed, minted, registered or pruned.** MISO carries exactly **one** registered
run (rule 15) and still does. No `ScenarioConfig` field was created or changed. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was
solved, scored or registered.**

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — miso-243 §7.1's named successor,
the only lever in this lane with a confirmed construction defect behind it.

Pre-registration: `PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md`, pushed with its
probe and **before either ran** (`14bab7b3`). One addendum,
`ADDENDUM-miso244-the-verdict-is-not-a-tie-and-my-liveness-gate-named-the-wrong-bus-2026-09-08.md`,
pushed **before the numbers it governs** (`b7b217a5`). **Every decision rule applied below was fixed
in one of those two documents; none was written after seeing a number.** Probes:
`scripts/probes/_miso244_incumbent_ladder_cent_phase0.py` → `_miso244_incumbent_ladder_cent_phase0.json`;
`_miso244_liveness_gate.py` → `_miso244_liveness_gate.json`.

**Basis.** The incumbent ladder's coupling anchor is the measured Indiana-hub **DA**
(`actual_lmp_hourly_MISO.parquet` `da`); row sets are the derive's own per-seam `dropna`. The SPP
anchor, where it appears, is the measured SPP **NORTH** hub DA. The model basis is the keeper's
committed **P1** bus price. They are never interchanged, and miso-232's measured decile column
(+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST — five disclosures, and three of them cost this session something

### 0a. **MY OWN LIVENESS GATE DID NOT STOP THE ARM. I AM STOPPING ANYWAY, ON A DIFFERENT GROUND, AND I SAY SO**

PREREG §3 made the liveness gate the thing that decides whether LP is spent. **It did not refuse:**

| | bar | **measured** | |
|---|---|---:|---|
| `max_bus max_year L` | ≤ 0.001 | **0.00982** (86 h, 2024, `MISO_external_South`) | **fails the bar** |
| `max_bus max_year \|Δq̂\|` | ≤ 5.0 MW | **3.682 MW** | inside |

The rule is a conjunction, so **`INERT` is false and `screen_authorized` is true, with screen year
2024.** **This session nevertheless spends no LP**, and the reason is *not* the gate: it is rule 23
`[R-FROZEN-DERIVE]`'s standing requirement that *"re-derivation commits must cite the data change"*,
which §3 shows cannot be met, plus the fact that re-deriving now would **erase the only surviving
evidence of the drift**. **That is a different stop from the one I pre-registered, and presenting the
gate as though it had refused would be false.** It is stated here at full magnitude instead.

The distinction is testable rather than rhetorical: the citation problem is **independent of `L`** —
it would hold identically had `L` read `INERT` — and `L` would have authorised the spend had the
citation problem not existed. Neither was invented to rescue the other.

### 0b. **MY PRE-REGISTERED SUB-CLASSIFIERS CAME BACK EMPTY**

PREREG §2.3 offered exactly two named sub-classes for a `V-NOT-A-TIE` verdict and **the record
refuses both.** **D-4**: no mismatching entry is a no-wash-clamped band (`is_clamped_export` false
for all three) and HEAD's `derive()` raises **zero clamp notes in any year** — so the derive
docstring's and `spec.py`'s own claim that the ordering *"holds naturally in all years"* is
**confirmed**. **D-5**: the alternative clamp taken off the ROUNDED imports yields
**13.39 / 50.98 / 57.85** against committed **27.86 / 27.69 / 23.77** — not the mechanism. The
handoff's second candidate, *"a no-wash clamp that fired at derivation time and was
hand-transcribed"*, is **REFUTED**; its first, *"a rounding artifact"*, is refuted by the verdict
statistic. **The verdict is the third, and it lands in a sub-class my own PREREG did not name.**

### 0c. **§2.4 BINDS THIS SESSION AGAINST FINDING THE CAUSE, AND I HONOUR IT RATHER THAN READING AROUND IT**

PREREG §2.4 fixed, before any number existed: *"This is the ONLY alternative construction this
session will try … No second transformation is tried."* Written for the `V-ARTIFACT` branch, its
prohibition is **unconditional in form, so it binds here too.** It would be easy, and wrong, to
re-run the derive under a different quantile convention, a perturbed count or a re-fetched vintage
until the committed table reappeared, and to present whichever worked as "the cause". **This session
does not.** What it costs is stated plainly: **the drift is demonstrated but not attributed.**

**And this is a defect in my own drafting, not a property of the problem.** The clause's *purpose* is
narrow — stop a cause being manufactured by search — while its *text* also forbids a single
pre-declared falsifiable test. A successor can pre-register that test in one line (§7.1); it costs
about two minutes of compute. The lesson is the drafting, and it is recorded rather than quietly
worked around.

### 0d. **MY LIVENESS GATE NAMED THE WRONG BUS**, found before it ran and repaired STRICTER

PREREG §3 specified `L` on `MISO_external`. The keeper arms `miso_south_seam_split=True`, and
`split_miso_south_external_node`'s own docstring states the South seam's reference-price bands are
hosted in the **new** zone — `MISO_external_South`, which the committed sidecar carries with 8,760 P1
rows a year. A gate on `MISO_external` alone would have measured a South band move **on a bus that
band is not hosted on.** Disclosed in a pushed addendum **before the gate ran**, repaired to the
**maximum over both buses** — strictly harder to pass than either alone — with **every bar
unchanged**. The repair is what surfaced the real number: on the correct bus `L` is **0.00982**
against **0.00422** on the bus the PREREG named, so the wrong-bus gate would have failed to stop the
arm *for the wrong reason as well*.

### 0e. **A POST-HOC OBSERVATION, LABELLED AS SUCH, THAT MOVES NOTHING**

Computed **after** the gate: of the 86 hours `L` counts in 2024, **82 sit at a bus price of exactly
`23.77`** — the committed band value itself. The moving band is the **marginal price-setter** at that
bus in those hours, so a pre-solve footprint evaluated at the frozen committed price plausibly
**overstates** the LP's real response (a marginal band that moves takes the price with it).
**It changes nothing, and the arithmetic is shown rather than asserted:** the gate is a conjunction
that had already failed on `L`, this observation can only push `L` *down*, and **a smaller `L` moves
the gate toward `INERT`, i.e. toward the same stop this session takes on other grounds.** It is
therefore not load-bearing in either direction, and it is **not** used to justify the stop — §3 is.

---

## 1. THE INSTRUMENT PASSES EVERYTHING FIRST, INCLUDING THE LEG THAT COULD HAVE VOIDED THE FRAMING

`FAILED_LEGS: []`. Every reference value is a **literal in the probe**, so the legs adjudicate even
if the predecessor's artifact is missing.

| leg | what it reproduces, in the predecessor's own metric | bar | **measured** |
|---|---|---|---:|
| **G-RAW** *(instrument validity)* | this probe's own raw replication of `_derive_one` satisfies `round(raw,2) == derive()`, all 192 entries | exact | **0.0** |
| **G-P2** | miso-243's P-2 per-seam `max\|committed − derive\|`, all 12 cells | exact at 2 dp | **exact** |
| **G-SPP** | the committed per-year SPP hourly ladder reproduces from HEAD's repaired derive, 48 entries | exactly 0.0 | **0.0** |
| **G-POOL** | the committed POOLED forward SPP ladder reproduces, 16 entries | exactly 0.0 | **0.0** |
| **G-DOC** | the derive's own docstring `corr(measured SPP flow, MISO DA − SPP hub DA)` = +0.041 / −0.020 / +0.050 | ≤ 0.002 | **+0.0409 / −0.0200 / +0.0503** |
| **G-ROW** | 8,760 rows/year; hub join preserves the row count; `n(R_D)` = 8,754 / 8,757 / 8,757 | exact | **exact** |
| **I-1** *(identity, on the COMMITTED table)* | `P(flow > mid_k)` inside `[P(da > c_k) − 0.002, P(da ≥ c_k) + 0.002]`, all 192 entries, both sides, every seam's own row set | 0 excess | **0.0 everywhere** |

**G-RAW and I-1 each had the power to end the session.** G-RAW, because the whole verdict is computed
on `raw`: had this probe's replication not been the derive's own pre-rounding value, `t_max` would
mean nothing. **I-1, because a committed table that failed it did not come from this construction on
this row set — and §2's interpretation would have been void.** It passes with **zero excess in every
seam and every year**, which is what makes three cents out of 192 entries a *signal* rather than
noise: the committed table **is** this estimator's output on this row set, everywhere else exactly.

---

## 2. **THE VERDICT: `V-NOT-A-TIE`**, and the three entries located for the first time

The rule, fixed in PREREG §2.3 before any number existed: `t = |raw − committed| − 0.005` is how far
the current estimate sits **past** the half-cent boundary separating the two cents; **`V-ARTIFACT`
iff `t_max ≤ 1e-4`**.

| | |
|---|---:|
| entries compared | **192** |
| mismatching | **3** |
| **`t_max`** | **0.0049998** |
| bar for `V-ARTIFACT` | ≤ **1e-4** |
| **VERDICT** | **`V-NOT-A-TIE`** |

**It misses the tie bar by a factor of 50.** miso-243 published only per-seam maxima; the entries are:

| year | seam | side | band | committed | **raw at HEAD** | rounds to | `t` | live on the keeper? |
|---|---|---|---|---:|---:|---:|---:|---|
| 2023 | **PJM** | import | 5 | 27.86 | 27.8661823 | 27.87 | 0.00118 | **no — displaced by the hourly overlay** |
| 2023 | **South** | export | 4 | 27.69 | 27.6962804 | 27.70 | 0.00128 | **yes** |
| 2024 | **South** | export | 5 | 23.77 | 23.7600002 | 23.76 | **0.00500** | **yes** |

**Directions are MIXED** — committed is one cent LOW at the first two and one cent HIGH at the third.

**The tie hypothesis was worth testing and is refuted on the numbers, not on a hunch.** The `da`
column is stored **float32** (43,800 rows; only **4.7 %** of values are exactly 2-dp in float64), so
an interpolated quantile can land on a half-cent where a `1e-6` perturbation decides the cent.
**Reported, and it cannot move the verdict (PREREG §2.4):** the cause prediction's antecedent
(`V-ARTIFACT`) is false, so no falsification is owed; the measurement was made anyway and snapping
`da` to exact cents in float64 **does not** reproduce the committed table (`max_abs_delta`
0.01 / 0.01 / 0.00).

**LIVENESS, verified independently from the committed config and the injection code** (not taken from
the handoff): the keeper arms `miso_seam_measured_ladder`, `…neighbour_anchored_ladder`,
`…neighbour_hourly_ladder` and `…neighbour_hourly_spp`, and `inject_miso_seam_ladder_prices` overlays
the PJM-hourly then the SPP-hourly ladder **on top of** the incumbent table as alternatives that
displace and never stack — so **only `South` and `Manitoba` rows reach the LP**, Manitoba has no
mismatch in any year, and **the PJM 2023 cent is inert.** The handoff's claim, confirmed.

---

## 3. **WHAT MOVED WAS THE SAMPLE, NOT THE ESTIMATOR** — an elimination, and why the re-derive is refused

**The elimination is ARITHMETIC on D-1′'s already-computed output, not a new construction.** For each
mismatch the probe recorded the quantile's own interpolation — `n`, `q`, `lo_index`, `frac`, `x_lo`,
`x_hi`:

| entry | `frac` | `x_lo` | `x_hi` | committed |
|---|---:|---:|---:|---:|
| PJM 2023 import 5 | 0.6182 | 27.860001 | 27.870001 | **27.86 = round(x_lo)** |
| South 2023 export 4 | 0.6280 | 27.690001 | 27.700001 | **27.69 = round(x_lo)** |
| South 2024 export 5 | 0.6525 | **23.760000** | **23.760000** | **23.77 — neither** |

Entries 1 and 2 both require the **lower** order statistic. Entry 3 **refutes** it: there
`x_lo == x_hi == 23.760000`, a degenerate position where **all five members of numpy's `h = q·(n−1)`
family** (`linear`, `lower`, `higher`, `nearest`, `midpoint`) return `23.76`, while committed is
`23.77`. **No uniform change of estimator explains both**, which eliminates the "the code's
convention changed" family. The mixed directions of §2 say the same thing independently.

What remains is that the **sample** the table was derived from differs marginally from the sample at
HEAD. **The object is exact and it is handed forward with its coordinates** — the integer durations
the three quantiles are drawn at, recovered arithmetically from the published `q`: **5,415**,
**3,259** and **3,044** hours out of 8,760.

**AND THE INCUMBENT TABLE IS THE ONLY SURVIVING FINGERPRINT OF THAT SAMPLE.** Every other ladder
derived on the same series reproduces at **exactly 0.0** — the per-year SPP hourly offsets (G-SPP),
the pooled forward SPP ladder (G-POOL), and miso-243's own measurements of the PJM annual and PJM
hourly neighbour ladders. Those tables are recent (miso-225 / 231 / 233 / 243); the incumbent is the
oldest, from the original audit-C-6 closure. **So the three cents date a source-data vintage, and
they are the last copy of that date.**

**THE REFUSAL, and it is on governance rather than on any residual.** Rule 23 `[R-FROZEN-DERIVE]`
requires a re-derive commit to **cite its cause**. There is none to cite: §0c binds this session
against hunting for it, and the 2026-08-16 history rewrite makes archaeology unreliable by CLAUDE.md's
own statement. Re-deriving anyway would be a **blind refresh** that **destroys the evidence** — once
the table matches HEAD's derive, the fingerprint is gone and the successor's attribution test has no
object. That is exactly the order the handoff fixed: *"DIAGNOSE THE CENT BEFORE PROPOSING ANYTHING …
DO NOT re-derive first and diagnose after."* **The re-derive is refused FOR NOW, not forever**: it
becomes admissible the moment the cause is attributed, and §7.1 names the test.

**Why this is not miso-243's case.** miso-243 re-derived on a construction defect it could **name**
(the partial join), **demonstrate** (G-V1 / G-V2 / G-V3, each able to kill the diagnosis) and repair
with **zero DOF**. Here the cause is unnamed. The precedent does not reach this table.

---

## 4. THE LIVENESS GATE AT FULL MAGNITUDE — reported in both directions, and it refused nothing

Bars from PREREG §3, unchanged; buses per ADDENDUM §0c; both are **footprint** measures over two
ladders and one committed price series, with **zero scored criterion, zero band comparison and zero
residual** in them. Band membership is evaluated in each side's own operand form — import `p ≥ imp_k`,
export `p ≤ exp_k`, written as two explicit comparisons rather than an algebraic rearrangement, which
is exact in real arithmetic and **not** in IEEE at ties (the 43-hour tie that cost miso-242 a gate).

| bus | year | `L` | hours changed | `Δq̂` (MW) |
|---|---|---:|---:|---:|
| **`MISO_external_South`** *(the bands' own bus)* | 2023 | 0.00000 | 0 | 0.000 |
| | **2024** | **0.00982** | **86** | **+3.682** |
| | 2025 | 0.00000 | 0 | 0.000 |
| `MISO_external` *(the bus the PREREG named)* | 2023 | 0.00011 | 1 | −0.043 |
| | 2024 | 0.00422 | 37 | +1.584 |
| | 2025 | 0.00000 | 0 | 0.000 |

**`max L` 0.00982 > 0.001 ⇒ not `INERT` ⇒ a 2024 screen was authorized and deliberately not spent
(§0a).** `Δq̂` passed its own bar with room. **2025 moves nothing at all** — no entry mismatches
there. Provenance leg **G-MOVE** confirms the only South bands that move are the two this session
published in advance (2023 export 4: `27.69 → 27.70`; 2024 export 5: `23.77 → 23.76`) and nothing
else, in any year; **G-BUS** confirms 8,760 P1 rows on each bus in each year.

---

## 5. **THE DELIVERABLE — the missing rule-23 reproduction pin, and it is falsifiable in both directions**

PREREG F5 recorded the structural fact behind the whole episode: **`MISO_SEAM_LADDER_BY_YEAR` was the
only MISO seam ladder with no test that re-runs its derive and compares.** The registry carried shape,
monotonicity, no-wash ordering and one spot value; the reproduce-the-derivation pin beside it covers
the **SPP hourly** offsets alone. That is why a cent could sit there unseen — and a pin at the
SPP-hourly bar (`atol=0.005`) **would have failed on the day it appeared.**

`tests/iso/miso/test_miso_seam_ladder.py::TestLadderRegistry::test_incumbent_registry_reproduces_the_frozen_derivation`
now asserts all **192** entries at `atol=0.005`, **except** the three in
`_MISO244_KNOWN_LADDER_DIVERGENCES`, which are pinned **harder** — both the committed and the derived
value at their exact 2-dp values — so the known gap can neither grow, move, nor multiply silently.
The constant's docstring states that when the table is reconciled the entries are **DELETED** (rule 26
`[R-DELETE]`), never absorbed by a wider tolerance.

**PREREG §4.1 reserved this decision for the verdict, and the verdict decided it**: a pin written
against a *rounding tie* would flap; against a *stable, deterministic* divergence it does not. The
verdict is the latter.

**Falsified twice before it was kept**, because a pin that cannot fail is worse than none:

| perturbation | expected | **observed** |
|---|---|---|
| delete one known-divergence entry (as if reconciled) | FAIL | **FAIL** (`AssertionError`, line 184) |
| move one committed 2025 South import band by 6 c | FAIL | **FAIL** (`AssertionError`, line 185) |
| restore | PASS | **PASS** |

Whole file: **29 passed**. No `atol` was loosened anywhere and no assertion was removed.

---

## 6. G-DRIFT — every hunk INERT for MISO backcast, with **both** shared seams **MEASURED**

Baseline **`5b5fb538`** — the merged equivalent of the keeper's orphaned `git.sha = 710d4dad`
(verified: `710d4dad` is not a valid object in this clone; `5b5fb538` **is** an ancestor of
`origin/main`). Audited over `src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`: **11 files, +639 / −4.**

| hunk | classification |
|---|---|
| `scripts/run_calibration{,_full}.py` (+10 / +32) | ercot-256 CLI passthrough for `netload_drag_layup_window_mask`, applied only `if … is not None` — **INERT** (flag default-off, absent from the keeper's recipe) |
| `config/capacity_market.py` (+131), `capacity_evolution/{__init__,retirements}.py` (+111) | capx D84 PJM thermal-ELCC accreditation — **INERT** (forecast-only path; a `mode="backcast"` run never enters capacity evolution) |
| `config/constants.py` (+1), `config/solve_surface_declared.py` (+1) | a PJM ELCC table and its declared surface row — **INERT** (another ISO's branch, forecast-only) |
| `config/iso_configs.py` (+68) | `_pjm_config` `default_scenario_overrides` only — **INERT** (another ISO's branch) |
| `config/scenarios.py` (+179) | two new fields, both `= False`: `netload_drag_layup_window_mask`, `pjm_thermal_accreditation_vintage` — **INERT** |
| `data/fleet/floors.py` (+110) | the ercot-256 lay-up window mask — a **SHARED** module, so **MEASURED, not classified from its gate**: `_resolve_drag_layup_shares(keeper_config, "MISO", y, 8760)` returns **len 0** in **2023, 2024 and 2025** |
| `data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet` | the loader path is ISO-keyed (`eia930/envelopes.py:503, 582`, `f"wecc_intertie_lmp_hourly_{iso.upper()}.parquet"`) and **no `…_MISO.parquet` exists** in that directory — **MEASURED INERT**; another ISO's artifact |

**Corroborated as the handoff requires:** `surface_stamp("MISO", keeper_config)` reproduces the
keeper's fingerprint **`8ee657ee4c7c49b0`**, **rows 208**, **`moved: {}`**, **`epochs: []`**.
**No LIVE hunk, so no control solve was earned — and none was spent.**

---

## 7. What is handed forward

1. **THE ATTRIBUTION TEST, pre-specifiable in one line** (this session is barred from running it,
   §0c): *if the committed table came from this estimator on a marginally different sample, each
   mismatching entry's committed value is reachable by perturbing that entry's own integer
   exceedance/depth COUNT by at most ±1 hour out of 8,760, holding estimator and price series fixed;
   a single entry needing more REFUTES it.* The three counts are **5,415 / 3,259 / 3,044**. **Zero
   LP.** If it attributes the cause, the re-derive becomes admissible under rule 23 and the screen is
   already sized: **2024, `L` = 0.00982, `Δq̂` = +3.682 MW.** If it refutes it, the drift is bigger
   than a sample nudge and the source-data provenance is the object.
2. **THE FINGERPRINT IS PERISHABLE, and the pin now protects it.** The incumbent table is the last
   copy of its own derivation vintage (§3). Do **not** re-derive it before the cause is attributed;
   the pin (§5) makes any further drift fail loudly instead of accumulating.
3. **THE STRUCTURAL ITEM RULE 1 NAMES IS UNTOUCHED** and this session does not close it: the model's
   SPP seam is 0.70–0.79 spread-correlated while the measured one is +0.0409 / −0.0200 / +0.0502.
   The seam being idle is not the anomaly; its being spread-driven is.
4. **C3c REMAINS THE DESIGNATED FRONTIER** (MISO model 3 / 7 / 11 h > $200 vs measured 30 / 37 / 88).
   It opens only by a new admissible measured identification under its own charter **plus an owner
   ruling** — never by an offer adder, ORDC offset, scarcity multiplier or any level tuned to the
   tail. **None was proposed, computed or armed here.**
5. **A DRAFTING LESSON, recorded because it cost this session something** (§0c): a pre-commitment
   written for one branch of a verdict binds on every branch unless it says otherwise. Scope such a
   clause to its branch.
6. **UNCHANGED AND NOT RE-TESTED** (miso-235…243): the SPP quantity-side charter stays **REFUSED — no
   DOF-free form** (miso-241 §5, C1–C7, census DONE); queue item 1 stays **ANSWERED AND DECOMPOSED**;
   the merit test's sign and basis stay **REFUTED**; the PJM/SPP idle contrast stays a
   **measured-record** fact; the external-bus-price identification half stays **CLOSED**; the per-seam
   external-node split **REFUSED at zero LP**; saturation **REFUTED**; miso-239 Q-A **MIXED** / Q-C
   **SURVIVES**; miso-240 Q-B **UNRESOLVED**; the `(month × hod)` template hypothesis **REMOVED**; the
   PJM import/export asymmetry **CLOSED FOR PJM**; South's neighbour-state route **CLOSED**;
   `miso_manitoba_seam` **CLOSED as already-armed**; `internal_congestion_split` **G**;
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**; `miso_south_firm_export_block`
   **G**; `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**.
7. **SOUTH stays excluded from the hourly form** and that stays a **DATA boundary**: SOCO and TVA
   publish no hub price.

---

## 8. Governance

Rule 1 `[R-STRUCT]`: the diagnosis is argued on construction and rule 23, **never on a residual**;
no criterion, band or residual appears in any bar; the arm is refused on governance, not because a
number moved the wrong way. Rule 12 `[R-PARALLEL]`: **no solve at all.** Rule 13 `[R-MEASURED]`: no
measured outcome entered anything; the forward pooled ladder is untouched and reproduces at 0.0.
Rule 14 `[R-ACCURATE]`: the accurate input is *not* deferred to protect a fit — it is deferred
because which input is accurate is exactly what is unattributed, and §3 says so. Rule 15
`[R-DASHBOARD]`: **no run was produced, so there is nothing to register**; MISO carries exactly one
registered run and it is unchanged; nothing pruned. Rule 16 `[R-ALLYEARS]`: no bundle exists.
Rule 17 `[R-FLOOR-WINDOW]`: no floor. Rule 19 `[R-ONE-MECH]`: nothing added. Rule 21 `[R-DOF]`:
**41/2, unchanged**; zero free parameters added. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no marker
sought; no out-of-training year touched. Rule 23 `[R-FROZEN-DERIVE]`: **this rule is the session's
result** — a re-derive is refused for want of a cited cause, and the missing reproduction pin is
added instead. Rule 24 `[R-REGISTRY]`: no field, no env knob, no CLI flag. Rule 25 `[R-ISO-SCOPE]`:
MISO's shard, section, lane and tests only; the SPP hub series is read as a measured **price input**,
never as SPP's calibration. Rule 26 `[R-DELETE]`: the pin's known-divergence entries are documented
to be **deleted** on reconciliation, never widened into a tolerance. Rule 27 `[R-PUSH]`: on-disk
edits only; every pushed blob ≥ 300 lines verified against local after push. Rule 28(a): the
handoff's recommended item taken; every standing adjudication is corroborated or untouched, never
re-tested. Rule 28(b): the tested cell's evidence updated in **MISO's shard only**, in-session; the
keeper is unchanged so no keeper stamp moves. Rule 29 `[R-SCREEN]`: clause 0 (zero-LP phase 0)
satisfied twice over; clause (b) — **G-DRIFT `5b5fb538..HEAD`, every hunk classified, both shared
seams MEASURED, `surface_stamp` reproducing `8ee657ee4c7c49b0` with `moved: {}`; no LIVE hunk, no
control solve spent**; clauses 1–2 not reached, because the arm is refused before a screen.
Rule 31 `[R-RETAIN]`: **nothing was solved, so there is nothing on local disk to lose**, and the
promotion question is surfaced explicitly in §9.

## 9. Non-claims, and the decision this session asks for

1. **No mechanism exists.** No `ScenarioConfig` field created or changed, DOF ledger unchanged, no
   cell verdict moved in either direction, keeper unchanged.
2. **No bundle was produced, so rule 31 has no object** — there is nothing on local disk that will be
   lost when this container is reclaimed, and no promotion question about a solve.
   **The decision this session does ask for is different and is stated plainly: (a) whether a
   successor may run §7.1's attribution test — this session was barred by its own pre-commitment,
   not by any rule of the programme; and (b) whether, if it attributes the cause, the 2024 screen
   already sized here should be spent.**
3. **The drift is demonstrated, not attributed**, and nothing here claims otherwise.
4. **`L` did not stop the arm** (§0a) and this document does not present it as though it had.
5. **No out-of-training year was solved, scored or registered**, and no marker was sought.
6. **MISO has no failing gate**, this session did not invent one, and nothing here trades a passing
   gate for anything.
7. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage** and no 2025 C1 pass is read as
   evidence anywhere above.
