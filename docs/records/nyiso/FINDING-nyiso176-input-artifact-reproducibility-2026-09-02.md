# nyiso-176 — the NYISO input-artifact reproducibility gap: the drift is attributed, the headline number is withdrawn, and the repair is wired

**Session:** nyiso-176 (NYISO backcast-calibration track), 2026-09-02.
**Keeper:** `2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}. **Untouched by this session.**
**Pre-registration:** `results/calibration/PREREG-nyiso176-input-artifact-reproducibility.md`,
committed with the probe at `60653b59` **before either was run** — the ninth
consecutive NYISO session to honour this.
**Probe:** `scripts/probes/nyiso176_input_artifact_reproducibility.py` →
`results/calibration/_nyiso176_input_artifact_reproducibility.json`.
**No C3c lever was opened. No parameter, band, floor or offer value changed.**
Every year read is 2023 / 2024 / 2025 for any solve-relevant statistic; the
outage extract's own multi-year span is an *object of study* and a **data-prep**
activity, which rule 22 `[R-HOLDOUT]` explicitly does not gate ("what is held
out is the SCORE, never the DATA").

---

## 1. The one-paragraph answer

nyiso-175b stopped at the artifact boundary because both NYISO solve inputs
looked non-reproducible at HEAD, the outage extract by "**−40 %**, from nothing
but re-running the deriver". **That number is an invocation-span artifact and
its sign is wrong.** The committed extract spans 2018–2026; the deriver's
`--years` default is 2023–2025; the comparison put nine years against three. On
a like-for-like basis the direction **reverses**: 1,495 → 2,632 windows, **+76
%**. Re-derived over the committed span the count is **6,455**, and **3,767 of
the committed 4,423 windows (85.2 %) reproduce EXACTLY**. What remains is not
one blob of drift but **three named, separately-sized channels**, only one of
which is a defect — and that one is **already repaired**, by nyiso-175b's own
default-off flags. So this session did the thing the blocker was blocking:
**wired the repair into the solve** (the 11 hardcoded call sites nyiso-175b
listed as NOT BUILT), **closed the coupling gap nyiso-175b disclosed in its own
§7 item 2**, regenerated both companions on a mutually consistent basis, and
**structurally closed the reproducibility gap going forward** by making the
outage deriver record its own invocation.

**The honest headline is a correction, not a discovery.** The blocker that
stopped a session was, in its largest part, two extracts derived over different
year spans and never labelled as such. And when the unblocked A/B finally ran,
it **failed its own pre-registered gate** (§8a): the repair closes C3a-2025 and
breaks three other criteria, which is the trap R6 was written to catch.

---

## 2. Gate R1 — the span hypothesis: **FAILS**, and the failure re-sizes the object

`derive_campd_unit_outages.py --years` defaults to `[2023, 2024, 2025]`
(line 1053). The committed extract's `outage_start` spans **2018–2026**.

Re-derived at HEAD over the committed span:

| leg | windows | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| committed | **4,423** | 621 | 516 | 537 | 539 | 533 | 540 | 464 | 491 | 182 |
| HEAD, committed span | **6,455** | — | 943 | 862 | 943 | 841 | 922 | 868 | 842 | 234 |
| HEAD, deriver default | **2,632** | — | — | — | — | — | 922 | 868 | 842 | — |

**R1 FAILS** on both legs of its own bar (total within 5 %; every year within
10 %). It is reported as a failure, not quietly rescued. But the failure is
informative in a way a pass would not have been:

* **nyiso-175b's "4,423 → 2,632, −40 %" is the first and third rows of that
  table.** It is a nine-year artifact against a three-year derivation. **The
  quantity is withdrawn.** On a like-for-like 2023–2025 basis the committed
  extract carries **1,495** windows and HEAD carries **2,632** — the direction
  is **+76 %**, not −40 %.
* **The committed extract is 85.2 % exactly reproducible.** 3,767 of its 4,423
  `(facility_id, unit_id, outage_start)` triples appear byte-for-byte in the
  HEAD derivation. Only **656** do not.
* **621 of those 656 are the 2018 rows, and their loss has a name.** HEAD
  cannot derive 2018 for NY at all: `data/raw/campd-unit-level/` carries
  `NY_2019` … `NY_2026` and no `NY_2018`, because **BLOAT-S2 (2026-08-17)
  untracked the `campd-unit-level` 2018 vintage** and the 2026-08-16 history
  rewrite stripped it, so **recovery is re-fetch only, never a pin**
  (`docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md`;
  `docs/FINDING-history-rewrite-2026-08-16.md`). This is a **documented data
  decision**, not drift.
* Netting 2018 out, **3,674 of the 3,802 non-2018 committed windows (96.6 %)
  reproduce exactly** under the repaired routing.

---

## 3. Gate R2 — attribution: three channels, one 2×2, and only one defect

R2 is a **reporting duty, not a gate** (so pre-registered). It is discharged in
full.

### 3.1 The orthogonal decomposition

Four re-derivations at HEAD, 2023–2025, against the committed artifact's own
1,495 windows in those years:

|  | full-stop override ON | override OFF |
|---|---|---|
| **incumbent routing** | **2,632** (the S-0 control) | 1,645 |
| **per-unit routing** | 1,996 | **1,344** |

*Committed = 1,495, which lies between the two override-OFF cells.*

Main effects, of the **+1,137** gap:

| channel | size | verdict |
|---|---|---|
| **full-stop duration override** | **+987** (87 %) at incumbent routing; +652 at per-unit routing | **NOT a defect** — see §3.2 |
| **`fac_group` routing short-circuit** | **+636** at override-on; +301 at override-off | **A DEFECT — already repaired** (nyiso-175b) |
| 2018 vintage prune | 621 windows (outside 2023–2025) | **A documented data decision** |

The two toggles overlap on the same machines, which is why they do not add: both
act on idle peaker windows, above all **E F Barrett (2511)**, whose 16 `U000xx`
combustion turbines carry **18 committed 2023–2025 windows against 610 at
HEAD** — and **20** under the per-unit crosswalk. That single plant is **54 %
of the whole 2023–2025 gap**, and its cause is exactly the defect nyiso-174 §6
item 1 named and nyiso-175b repaired: `_resolve_unit_group` short-circuits on a
**last-writer-wins** facility group, so a steam plant's jet peakers are written
as `ST_GAS` and their economic idling is emitted as steam-bin outages.

### 3.2 The override survives its own falsifier — reported because it could have gone the other way

The full-stop duration override (`FULL_STOP_OVERRIDE_DAYS` / `_CF`,
`scripts/lib/outage_detect.py`) keeps a sustained dead stop as a mechanical
outage even where it does not overlap the in-merit band. It is the **dominant**
channel, and the obvious hypothesis was that it over-detects on units with
sparse CAMPD coverage: at HEAD, Lockport (54041) goes from 67 to 6,341
unit-outage-days, Carr Street (50978) from 26 to 3,214, on identical unit
rosters.

**The direct test refutes that.** Across five affected plants in 2024, of the
**60,024 unit-hours** HEAD's windows cover, only **622 (1.0 %)** show **any**
metered generation (committed: 25 of 24,456 = 0.1 %). The windows are **not**
asserting unavailability against a running meter — those units really are dark.
The override is a **deliberate, cited detector feature that the committed
extract simply predates**, and nothing here proposes changing it.

### 3.3 Two suspects eliminated cleanly

* **Parasitic factors: EXACTLY INERT.** Ablating `_parasitic_factor_map` moves
  **0 of 78** tranche rows — every ablated `online_hours` equals its control
  value. The suspect is removed from the list, not merely deprioritised.
* **The in-merit revealed-availability filter is INTACT at HEAD.** The
  attractive silent-degradation story — `high_load_mask` returns `None` when
  the EIA-930 BA file is missing, and BLOAT-S2 untracked "the `eia-930` per-BA
  long files" — is **REFUTED by measurement**: `NYIS hourly.parquet` is present
  and covers 2015–2026, and the mask returns 1,172 / 1,194 / 1,233 / 1,225
  high-net-load hours for 2019 / 2023 / 2024 / 2025. The filter is doing its
  job. Recorded because it was the most plausible hypothesis in the session and
  it was wrong.

---

## 4. Gates R3 / R4 — the tranche artifact: MULTI-CHANNEL, and one bit-exact identification

Both tranche legs already sit at HEAD over the **same 3-year span** (committed
`online_hours` max 26,253; control max 26,271), so the tranche delta is **not**
a span artifact and had to be attributed to a mechanism.

**R3 (pre-registered metric: rows whose `online_hours` matches committed within
24 h, of 78 common rows; a channel is DOMINANT at ≥ 60):**

| leg | `n_match` |
|---|---|
| S-0 control | 44 |
| **A** — outage-derate overlay ablated | **47** |
| **B** — parasitic factors ablated | 44 |

**Verdict: MULTI-CHANNEL.** No single ablation reaches 60. Reported at the bar
that was set in advance, not at a bar chosen afterwards.

Per-row, 44 rows reproduce, **6 are explained exactly by the derate channel**
(2493 `ST_CHP`, 2500 `ST_GAS`, 2682 `ST_GAS`, 54034, 56196, 56940) and 28 are
residual — but the residual rows are mostly small and **A moves almost all of
them toward committed and overshoots**, which is the signature of *a different
outage extract*, not of a different mechanism.

**Channel C — fleet nameplate**, measured directly: exactly **3 rows**
(7314 199.5→170.0, 10190 92.0→72.0, 56196 662.0→560.0). These are HEAD's own
fleet reconciliations, logged at load as "*corrupt summer-capacity rows —
reconciled*". **HEAD is right**; this is an improvement, not drift.

**R4 — the S A Carlson (2682) forensic: PASSES, and not marginally.** The bar
was "within 10 % of the committed 3,913 online hours". Ablating the outage
derate returns **3,913 online hours and `median_cf` 84.4 — the committed values
EXACTLY**, from a control reading **120 h at `median_cf` 150.0**, the
`np.clip(acf, 0, 1.5)` cap and therefore a physically meaningless number.

**That bit-exact match is the finding.** `avail_cap = nameplate × avail_mult`
enters both the online test (`series > _ONLINE_FRAC × avail_cap`) and the
`finite` mask (`avail_cap > 0`), so a derate deletes hours outright. The
committed tranche artifact was therefore derived when the outage extract carried
**no `(2682, ST_GAS)` windows**; the committed extract now carries **55**, on
the `optime_proxy_steam` capacity source. **The two committed inputs are
mutually inconsistent** — the tranche artifact is derived against an *older*
outage extract than the one the solve actually reads. That, not "drift", is the
real blocker, and it is what arming the gate resolves.

---

## 5. R5 — the re-baseline decision, discharged as pre-registered

The rule was fixed before any measurement and **no score of any kind was
consulted in choosing the branch**.

* **R5-(iii) applies to the tranche artifact** — R3 declared MULTI-CHANNEL, so
  the route is (a), re-baseline, with the drift documented row-by-row.
* **R5-(i) applies to the routing channel** — a nameable defect, so repair it
  and re-derive only that.

**Both land in the same act, and it is better than either alone.** The
`-perunit-` companions ARE the re-baselined inputs, and they are selected by a
**default-off gate** rather than by overwriting the incumbents. So:

* the incumbent artifacts stay **byte-untouched** and the keeper is unchanged;
* the re-baseline is an **adjudicated single delta** (an A/B against the
  keeper's own recipe), never a silent import;
* the routing repair and the re-baseline **cannot be separated**, which is
  correct — they are the same object.

**Rule 23 `[R-FROZEN-DERIVE]` is satisfied by citing the defect, never a
residual.** No residual was looked at.

---

## 6. What was built

### 6.1 `ScenarioConfig.campd_per_unit_attribution` — ONE gate, BOTH artifacts

nyiso-175b left the repair unreachable from a solve. This session wires it.

* `data/fleet/campd_bins.py::thermal_tranche_csv_for_iso` is the single
  resolver; **all 11 hardcoded call sites** (`campd_bins` ×9, `coal.py`,
  `chp.py`) now go through it, threaded from `config` via `assembly.py`,
  `arrays.py`, `offer_curves.py` and `model/reserves/spec.py`.
* `data/outages.py::unit_outage_csv_for_iso` gains `per_unit_crosswalk`, which
  **takes precedence over** the narrower `-unitroute-` companion — measurably
  wrong where the two disagree (nyiso-175b K3 routes Ravenswood's gas-fired
  block CTs to `CT_PEAKER` and drops them from the overlay).
* **One field, not two, by design (rule 19 `[R-ONE-MECH]`).** A tranche row's
  statistics are computed over an outage-derated denominator, so the two
  artifacts must move together; a single gate makes that structural rather than
  a discipline a successor could forget.
* Registered with the field in the same commit (`_CACHE_KEY_OPTIONAL_FIELDS`
  plus the default-string registry, the nyiso-119 / caiso-186 discipline);
  `--campd-per-unit-attribution` reaches both `solve_and_persist` and
  `run_replay_bundle`, and the value lands in `run_config.json` (rule 24).
* **Byte-inert off**: the companions are separate files and the resolver falls
  back to the incumbent artifact wherever one has not been derived — today,
  every ISO but NYISO (rule 25 `[R-ISO-SCOPE]`). Zero free parameters; the
  inputs are EIA-860 prime movers and CAMPD unit types (rule 13
  `[R-MEASURED]`).

**Completeness is CI-enforced, not asserted.**
`tests/unit/data/test_campd_per_unit_attribution.py` (10 tests) fails if any
`src/` module reads `thermal_tranches_<ISO>.csv` outside the resolver, or if a
reader that resolves the path cannot receive the selector. That is the invariant
that stops a solve reading **two artifact vintages inside one LP** — a failure
mode nothing in the output would reveal.

### 6.2 The coupling fix, in the deriver rather than in prose

`derive_thermal_tranches` now sources its derate from the per-unit outage
companion under `--per-unit-attribution`, closing nyiso-175b §7 item 2.

### 6.3 Both companions regenerated on a consistent basis

* **Outage companion**: 2023–2025 → **2019–2026**, 1,996 → **4,928** windows.
  The old 2023-2025-only companion would have silently lost every window that
  begins in 2022 and runs into 2023, because `unit_outage_derate_factors` clips
  to the run year. **Byte-identical on re-derivation.**
* **Tranche companion**: re-derived against that repaired extract. **15 of 85
  rows move**, the largest being 8906 `ST_GAS` 17,027 → 8,823 h and 50978
  `CC_REGULAR` `median_cf` 70.7 → 141.4.

### 6.4 The reproducibility gap closed going forward

`derive_campd_unit_outages` now writes a **provenance sidecar** beside every
extract it emits, for every ISO: year span, `min_outage_days`, the routing
flags, the in-merit and full-stop thresholds, row count and the year histogram.
**The absence of exactly this record is why this session's headline comparison
was ambiguous in the first place** — a successor comparing two extracts can now
read two sidecars and see immediately whether it is looking at drift or at a
different invocation.

---

## 7. One negative result, at full strength

**The physically-impossible `median_cf > 100` census goes 10 → 11.** The
coupling fix is correct in construction and it makes one statistic *worse*:
50978 `CC_REGULAR` enters at **141.4** because the derate now bites at a plant
whose CAMPD coverage is sparse. Under rule 14 `[R-ACCURATE]` the accurate
construction is **kept** and the artefact is **recorded**, never reverted — and
it joins nyiso-175b's own refuted claim that `median_cf > 100` is a signature of
the attribution defect. **It is not.** Above-nameplate CEMS gross has other
causes that neither repair touches.

---

## 8. Honest expected value

**What is delivered.** The chartered object — the drift — is attributed to
three separately-sized channels, with the committed record's headline number
**withdrawn and corrected in sign**, two suspects **eliminated by measurement**,
and one identification that is **bit-exact**. The repair that was blocked is now
**wired, tested and reachable from a solve**, its internal inconsistency closed
in the deriver, both artifacts regenerated consistently, and the class of bug
that caused all of this **structurally prevented** for every ISO.

**What is NOT delivered, and will not be oversold.** The C3a-2025 expectation of
the per-unit repair is **~ZERO** and this must never be presented otherwise:
both East River bins carry heat rate 7.4205 and the same delivered gas, so
moving energy between them changes **no unit's marginal cost and no marginal
price**. nyiso-175b's gate **K5 — which FAILS a large favourable C3a move —
is carried forward verbatim as R6**. This is a rule 1 `[R-STRUCT]` C1 /
representation repair plus an input-integrity repair. **The re-baseline itself
has no pre-registered sign**: it may move scores either way, and under rule 14 a
worse backcast after a more accurate input is a **discovered bug elsewhere**,
never a reason to revert.

**The A/B was solved, and it is reported in §8a below — it FAILS its own
pre-registered gate.**

---

## 8a. THE A/B — solved, scored, and REJECTED on its own pre-registered gate

Two three-year bundles, one invocation each, both registered on the dashboard
(rules 15/16):

| run id | bundle | gate |
|---|---|---|
| `2026-09-02-nyiso-176-rebaseline-control` | `nyiso176_ctl_A` | OFF |
| `2026-09-02-nyiso-176-perunit-attribution` | `nyiso176_arm_B` | ON |

### 8a.1 The control is a result in itself: the NYISO keeper reproduces BIT-IDENTICALLY at HEAD

| year | max abs class-energy delta | hourly zonal prices differing |
|---|---|---|
| 2023 | **0.000 TWh** | **0 of 52,560** |
| 2024 | **0.000 TWh** | **0 of 52,560** |
| 2025 | **0.000 TWh** | **0 of 52,560** |

**HEAD has not drifted for NYISO since 2026-08-30.** The keeper is reproducible
from its own recipe, and the A/B against it is an unambiguous single delta. This
also **retires nyiso-175b's stated reason for needing a control leg** — that
reason was artifact drift, and the drift is now attributed.

### 8a.2 The arm fires gate R6

**R6, carried verbatim from nyiso-175b's K5, FAILS a large FAVOURABLE C3a move.
That is exactly what the arm produces.**

| criterion | tier | control (= keeper) | arm |
|---|---|---|---|
| **C1** fuel mix | load-bearing | **PASS** | **FAIL** — CC_REGULAR 2024 38.77 vs 34.06, MODEL MISS |
| **C2** system volume | load-bearing | PASS | PASS |
| **C3a** price level | load-bearing | FAIL **2025 only** (58.81 vs 66.43, −11.5 %) | FAIL **2023 only** (37.86 vs 32.25, **+17.4 %**) |
| **C3b** price shape | load-bearing | **PASS** | **FAIL** — 2023 NRMSE 0.215 |
| C3c price tail | supporting | FAIL | FAIL |
| C4 dispatch corr | supporting | PASS | PASS |
| C8 forced share | protective | PASS | PASS |
| **target grade / fails** | | **5 / 2** | **3 / 4** |

**The arm closes the keeper's sole load-bearing failure** — C3a-2025 goes
−11.5 % → **−6.7 % and PASSES** (58.81 → 61.96 against an actual 66.43) — **and
pays for it with a +17.4 % blow-out in 2023 and two new load-bearing
failures.**

The mechanism is legible. Class energy moves out of steam and into combined
cycle:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| `ST_GAS` | **−5.28** | −2.39 | −1.05 |
| `CC_REGULAR` | +3.29 | +1.56 | +0.32 |
| `CC_CHP` | +1.22 | +0.96 | +0.44 |
| `CT_PEAKER` | +0.53 | +0.19 | +0.30 |
| load-wtd price | **+14.71 %** | +7.32 % | +5.36 % |

Both determinations read **NOT-YET**; the governance gate is UNATTESTED (a
replay bundle carries no `calibration_attestation.json`), but the arm's
load-bearing failures stand on their own and do not depend on that.

### 8a.3 Disposition — REJECTED as a keeper, NOT rejected as an input

**The arm is not promotable, and the keeper is untouched.**

**But rule 14 `[R-ACCURATE]` binds explicitly, and it was stated in this
session's pre-registration before any of this was measured:** a more accurate
input that makes the backcast worse is a **discovered bug elsewhere**, never a
reason to revert. Something in the NYISO keeper was silently compensating for
the mis-attribution, and the A/B has now exposed it rather than created it. The
repair stays in the codebase, default-off, and the root cause is the successor's
object.

**Leading suspect, and where to start:** **Ravenswood (2500)**. Its 1,724.8 MW
`ST_GAS` bin loses its committed share (10.7 → 20.3 %) to a **new 222.2 MW
`CC_REGULAR` bin at committed 70.0**, while its three steam boilers' outage
windows move `CC_REGULAR` → `ST_GAS` so the steam bin takes its own derates for
the first time. Both changes push the same way, and `ST_GAS` is where the
−5.28 TWh comes from.

**The year signature is itself diagnostic and is unexplained.** 2023 is the only
year whose price *overshoots*, and it overshoots hard (+14.71 %) while 2025 —
the year the keeper misses low — improves. A single mis-attribution repair
should not be that year-heterogeneous.

**DO-NOT-REDO:** do not re-run this A/B unchanged. The next step is the
root-cause decomposition, and the cheapest instrument is arming the two halves
**separately as a diagnostic** — which the single gate deliberately forbids for
a *keeper* (the two artifacts must ship together, §6.1) but which is entirely
legitimate for attribution.

### 8a.4 One provenance caveat, disclosed

Both bundles' `run_config.resolved_inputs` were written by the code as it stood
when the solves started, which is **before** this branch's `resolved_inputs`
fix: the arm's block therefore names `campd-unit-outages-NYISO.csv` although it
actually read the `-perunit-` companion, and neither bundle carries a
`thermal_tranches` block. The artifacts each leg consumed, by sha256:

| leg | unit-outage extract | tranche artifact |
|---|---|---|
| control | `587dd6fa…` (450,345 B) | `0dae176b…` (6,045 B) |
| arm | `ce40c46a…` (501,759 B) | `a4250a73…` (7,424 B) |

The gate's effect is independently corroborated in both directions: the arm
derates **305** plant-tranches in 2023 against the control's **278**, and the
tranche readers move East River's committed share from the steam bin (32.0) to
the turbine bin (30.1) with `chp_pmin_cf` 30.0 → 1.5. The fix is committed in
this same PR, so the next solve records correctly.

---

## 9. Handed forward

1. **THE ROOT CAUSE OF THE ARM'S DEGRADATION — the successor's object.** The
   A/B is done (§8a) and the arm is rejected as a keeper, but under rule 14 the
   accurate input stays and the degradation is a discovered bug. Start at
   Ravenswood (2500) and at the 2023-only price overshoot. The cheapest
   instrument is arming the tranche and outage halves **separately as a
   diagnostic** — forbidden for a keeper by the single-gate design, legitimate
   for attribution. A control leg is no longer needed: §8a.1 establishes that
   the keeper reproduces bit-identically at HEAD, so the committed keeper *is*
   a valid control.
2. **The cross-ISO question, which this session deliberately did not open.**
   **Nothing in the diagnosis is NYISO-specific.** The `fac_group`
   short-circuit's own docstring calls it "a deliberate pjm-75 conservatism",
   and **neiso-99 already carved a rule 14 exception out of it** — so the defect
   family is known to be present in at least two other ISOs and was handled
   per-plant rather than by the general rule. Each `U` cell in the matrix states
   its own transfer question, and **all four are answerable from committed bytes
   without a solve**: does the ISO's tranche artifact attribute a plant's
   conduct to a bin its own units do not carry, and does its outage extract
   route any unit through the short-circuit?
3. **Every other ISO's tranche artifact has the same unrecorded provenance.**
   The xiso-6 backfill gave them descriptive sidecars that state in terms that
   they make no claim about what HEAD would emit. The outage half is now
   self-recording; **the tranche half is not**, and giving
   `derive_thermal_tranches` the same treatment for the incumbent artifacts is a
   small, obviously-correct piece of work.
4. **`--fix-anchors` on the shared mechanism matrix** — the standing governance
   round. This session's new `ScenarioConfig` field adds to the existing
   line-number drift below its insertion point and deliberately did **not** run
   the fixer, which would rewrite every row of a file five other lanes edit.
5. **nyiso-175b's and nyiso-175's other carry-forwards stand unchanged**: the
   D-2 `dispatch_source` provenance stamp, the `CT_CHP` maintenance shape
   (recorded, not proposed), `wefor_residual = null`, and
   `nyiso_gas_bridge_ct`'s missing matrix cell.

---

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — every change is justified by the primary record
  (EIA-860 prime movers, CAMPD unit types, the deriver's own invocation
  surface). No residual was consulted, and no LP output entered any decision.
* **Rule 13 `[R-MEASURED]`** — inputs are static unit attributes that regenerate
  for a forward year. No measured *outcome* enters.
* **Rule 14 `[R-ACCURATE]`** — the accurate inputs are kept, including where
  they make a statistic worse (§7). The binding is stated in advance: a worse
  backcast is a discovered bug elsewhere.
* **Rule 19 `[R-ONE-MECH]`** — ONE `ScenarioConfig` field over both artifacts;
  `-perunit-` **replaces** `-unitroute-` where both exist rather than stacking.
* **Rule 21 `[R-DOF]`** — zero free parameters.
* **Rule 22 `[R-HOLDOUT]`** — every solve, score and registration is 2023–2025. Deriving a multi-year *input* is data prep, which the rule
  explicitly does not gate. NYISO's `complete` marker was **not** requested.
* **Rule 23 `[R-FROZEN-DERIVE]`** — both re-derivation commits cite the defect
  (span mismatch; derate coupling), never a residual.
* **Rule 24** — the new tunable is in `ScenarioConfig` **and** `run_config.json`.
  No off-registry channel.
* **Rule 25 `[R-ISO-SCOPE]`** — the code is ISO-agnostic; **only NYISO's
  artifacts were derived.** Every other ISO's committed tranche and outage CSVs
  are byte-untouched, and no verdict crossed an ISO boundary.
* **Rule 27 `[R-PUSH]`** — every pushed file ≥ 300 lines was blob-verified
  (line count + hash against local) immediately after the push.
* **Rule 28 `[R-MECH-MATRIX]`** — the new mechanism's base row plus a cell line
  in **every** ISO shard, same PR (duty c), and the tested cell updated in the
  same session (duty b): NYISO closes at **R**. `check_mechanism_matrix.py`
  reports no errors.
* **Rule 15 / 16** — both completed solves are registered on the dashboard,
  keeper and rejected probe alike, all three years in one bundle each.
* **Tests** — `tests/unit` + `tests/iso/nyiso`: **1,792 passed, 17 skipped**.
  The **14** failures in `tests/regression` + `tests/scoring` **reproduce
  identically on a clean stash of HEAD** and are pre-existing (the brief named
  one of them; there are fourteen).
