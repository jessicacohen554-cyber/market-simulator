# ASSESSMENT — neiso-101: NEISO's 2019 scoring inputs prepared (precondition #2), no spend

**Session:** neiso-101 · **Date:** 2026-08-18 · **Keeper at HEAD:** `2026-08-17-neiso-99-joint-p1`
**Mode: INTAKE ONLY.** No LP was constructed. No year of any tier was solved, scored or registered.
**Nothing is granted.** `final` remains absent and this session does not request it.

Executes **precondition #2 only** of the neiso-100 owner decision card
(`ASSESSMENT-neiso100-declaration-reassess-2026-08-18.md` §4.3) and nothing else from it.

---

## 0. Headline

| question | answer at HEAD |
|---|---|
| Is `final` precondition #2 CLOSED? | **The data half is CLOSED. One item remains, and it is NOT a data item** — see §1.3. |
| Were the card's three "absent 2019 inputs" absent? | **NO — two of three were already closed.** The card quoted neiso-87 forward; neiso-89 had landed them. §1.1 |
| Did preparing anything move a tuned-year number? | **NO.** Zero tracked files modified; determination reproduces `CALIBRATED`; `actual_tail` re-derive **byte-identical**. §3 |
| Did the keeper move since neiso-99? | **NO** — task 4 correctly SKIPPED, not repeated. §4 |
| 2025 EIA-923 final vintage | **STILL NOT LANDED.** Re-checked, reproduces exactly. §5 |
| Was anything built? | **NOTHING.** No input was absent-and-preparable. Rule 15: no run, no registration. §6 |

**Two items the card did not list were surfaced by the span walk** (§2), and one of them changes
what "prepared" can mean for the bench part.

---

## 1. The measurement — every keeper input, re-walked across the FULL 2019–2025 span

The charter said to re-measure rather than trust the list, and that was the right instruction:
**the card's list was two-thirds stale.** Probe `scripts/probes/neiso101_2019_input_prep.py`,
record `results/calibration/_neiso101_2019_input_prep.json`. It reuses neiso-90's eighteen
per-input probes by rebinding that module's year globals rather than copying them, so the two
audits cannot drift apart.

Why the whole span and not just 2019: rule 22's 2026-08-06 clarification — *"an input is either
the best measured representation of a physical/market quantity or it is not, and if it is, it
belongs in EVERY year"*. A per-year walk is the only thing that catches an input that is *present*
for 2019 but **provenance-split** against the tuned years, which is precisely the pathology the
NEISO gas basis carried (neiso-85/86).

```
input                                            19   20   21   22   23   24   25
---------------------------------------------------------------------------------
load_demand (LP demand array)                    OK   OK   OK   OK   OK   OK   OK
backcast_config (the keeper recipe, built)       OK   OK   OK   OK   OK   OK   OK
load_hydro_budget (neiso-72 window)              OK   OK   OK   OK   OK   OK   OK
load_neiso_reserve_requirements                  OK   OK   OK   OK   OK   OK   OK
henry_hub_actual (per-year gas price)            OK   OK   OK   OK   OK   OK   OK
calibration_reference.json (C1/C2 target)        OK   OK   OK   OK   OK   OK   OK
actual_lmp_hourly_NEISO (C3a/C3b/C3c upstream)   OK   OK   OK   OK   OK   OK   OK
actual_tail.json (C3c benchmark part)           GAP   OK   OK   OK   OK   OK   OK
NEISO_<y>_renewable_capacity.csv                 OK   OK   OK   OK   OK   OK   OK
gas_basis_by_iso_month.csv                       OK   OK   OK   OK   OK   OK   OK
algonquin_citygate_daily.csv                     OK   OK   OK   OK   OK   OK   OK
campd-unit-outages-NEISO.csv                     OK   OK   OK   OK   OK   OK   OK
plant_emission_rates_v2                          OK   OK   OK   OK   OK   OK   OK
fossil_co2_rates                                 OK   OK   OK   OK   OK   OK   OK
parasitic_load_factors (pooled map)              OK   OK   OK   OK   OK   OK   OK
capacity_actuals_neiso.csv                      GAP  GAP   OK   OK   OK   OK   OK
EIA-930 ISNE_fueltype                            OK   OK   OK   OK   OK   OK   OK
EIA-930 ISNE_region                              OK   OK   OK   OK   OK   OK   OK
```

**Seventeen of eighteen inputs resolve for 2019**, including the keeper recipe itself:
`backcast_config(2019, "NEISO", …)` **builds**, and `load_demand("NEISO", 2019)` returns a full
`(5, 8760)` array. The 2019 configuration is not a sketch — it assembles.

### 1.1 The card's three items, adjudicated individually

| card item | measured at HEAD | verdict |
|---|---|---|
| `calibration_reference` | `isos.NEISO` carries **2019–2025**, all seven | **ALREADY CLOSED** (neiso-89 / PR #3693) |
| renewable-capacity | `NEISO_2019_renewable_capacity.csv` **present** | **ALREADY CLOSED** (same PR) |
| `actual_tail` | `isos.NEISO` carries 2020–2025; **no 2019 row** | **OPEN — but gate-blocked, not data-blocked.** §1.3 |

Present is not the same as complete, so both closures were checked for **content**, not existence:

* `calibration_reference` is **schema-uniform across the whole span** — every year carries the same
  4 top-level keys, the same **9** `generation_twh` classes, the same 5 `demand` keys and the same 2
  `renewables` keys. The single deviation is 2025's extra `eia923_incomplete` flag, which is the
  standing data blocker being correctly *marked* (§5), not a gap.
* The renewable-capacity CSVs are uniform in schema (120 rows = 2 fuels × 5 zones × 12 months, every
  year) and physically coherent in content: July solar 1,191 → 3,548 MW and wind 1,386 → 1,721 MW,
  monotone across 2019–2025. 2019 is a genuinely built year, not a stub.

### 1.2 Consistency, not just presence — the provenance check the pathology demands

The two inputs neiso-87 §3.2 flagged as the highest-risk provenance splits were re-measured:

**Gas basis — 2019 is the SAME PROVENANCE CLASS as the tuned years.** Classifying every NEISO row
in `gas_basis_by_iso_month.csv` by source:

| year | measured ISO-NE newswire prints | EIA N3050MA3 proxy |
|---|---|---|
| **2019** | **12 / 12** | **0** |
| 2020 – 2025 | 12 / 12 each | 0 each |

**Span uniform: TRUE.** The proxy survives only at 2015–2017 (100 %) and 2018 (4 months, Mar–Jun —
the unrepairable ISO-NE newswire migration), and **2018 and earlier are DROPPED from the working
span**. Across 2019–2025 the NEISO hub basis is uniformly measured. This is the strongest available
answer to neiso-87's concern: 2019's basis is identical *in kind* to the basis the keeper is tuned on.

**CAMPD outage extract — neiso-87's ⚠ is CLOSED.** That warning was that 2018–2022 had been
appended at a different detector vintage than 2023–2025, invisibly, because the file carries no
vintage column. It is closed not by finding a vintage column but by a **whole-file re-derive**:
neiso-99's `ef9e911` deleted 257 rows and added **zero**, and its own control re-derivation
reproduced every surviving row byte-identically on every column. The file is HEAD-reproducible end
to end, which is what a vintage column could only have asserted. Row density carries no cliff at the
old seam either — 2019 is the *densest* year in the file (457 windows vs 400 / 401 / 338 for
2018 / 2020 / 2023).

### 1.3 The one genuine gap: `actual_tail` 2019 is withheld by the GATE, not missing from the data

This is the substantive finding, and it **reframes precondition #2**.

Evaluating the deriver's own gate function (`derive_actual_tail._year_emittable`, which reads
`scripts/lib/holdout_policy` — the same module the other three rule-22 gates read) per year:

| year | tier | marker required | NEISO holds it | emittable | row committed |
|---|---|---|---|---|---|
| **2019** | **locked_test** | **`final`** | **NO** | **False** | **False** |
| 2020 / 2021 / 2022 | validation | `complete` | yes | True | True |
| 2023 / 2024 / 2025 | train | — | — | True | True |

The upstream is **ready**: `actual_lmp_hourly_NEISO.parquet` carries 2019 at **8,760 rows,
coverage 1.0000**. The row is fully computable from that measured input at HEAD — the probe
computes it in memory and **deliberately does not emit it**, because emission is what the tier gate
governs.

**So precondition #2's residual is not a data-prep item at all — it collapses into precondition #5
(the `final` marker).** There is nothing a session can prepare that would close it, and routing
around the gate would *be* the grant. The moment `final` exists, **one command**
(`scripts/data/derive_actual_tail.py`) completes it with nothing else outstanding — which is exactly
the state rule 22 asks an out-of-training year's configuration to be in.

---

## 2. Two items the card did not list

### 2.1 The bench part is NOT a preparable input — it is a byproduct of the spend

The charter lists `bench/NEISO/` (2022–2025, no 2019) among the absent 2019 scoring inputs. It is
absent. But it is **structurally impossible to prepare in advance**, and that is worth stating
plainly rather than carrying it forward as an open task forever.

Traced to its writer: `scripts/render_backcast.py::generate` →
`backcast_artifacts.write_bench_part`, fed by `render_calibration_html.build_payload`, which reads
**a registered bundle's own input snapshots** (`bundle_input_path(bdir, "eia923"/"eia930"/"campd")`)
and iterates that bundle's `meta["years"]`. A bench year therefore exists **if and only if** a
bundle covering that year has been rendered. It is downstream of the very spend it would support.
There is no run-free code path that emits one, and adding one would mean building a scoring artifact
for an unauthorized year.

**Recommendation: drop the bench part from precondition #2's list.** It is not a precondition; it is
an output of satisfying the others.

### 2.2 `capacity_actuals_neiso.csv` has no 2019/2020 rows — and it is not this lane's

Newly surfaced by the span walk (the card did not list it). It is **not a backcast-rubric input**:
no criterion C1–C8 reads it. It is the **forecast** program's capacity-hindcast scoring target
(W2-P5, plan §1.2.3), read only by `scripts/score_capacity_hindcast.py`.

Its window start is derived, not incidental: `build_capacity_actuals.WINDOW = range(2021, 2026)` with
`FLEET_VINTAGE_YEAR = min(WINDOW) - 1`, tying it to `run_capacity_hindcast.py --vintage 2020`
(plan §1.1, first scored year 2021). Moving it to 2019 would re-key that hindcast's base fleet
vintage to **2018** — a year the working span drops — and `WINDOW` is shared by every ISO's build.
That is a cross-ISO **forecast-lane** change. **FILED, not acted on** (rule 25 `[R-ISO-SCOPE]`).

### 2.3 A durability note on the 2019 inputs — measured, and worth the next session's attention

The 2019 `calibration_reference` block and the renewable-capacity CSVs are **committed**, so their
content survives a fresh clone. But the builder that produced them
(`build_calibration_reference.py`) reads `load_demand_meta`, which for a pre-2021 year resolves only
through the **`demand-profile` clean partition** — and `data/clean/` is gitignored and disposable.
Measured at HEAD in this session, with the partition absent:

| year | `load_demand` (the LP driver) | `load_demand_meta` (build-time only) |
|---|---|---|
| 2019 / 2020 | **OK** `(5, 8760)` | **ERR** — `No EIA-930 data for ISO 'NEISO' in year 2019` |
| 2021 – 2025 | OK `(5, 8760)` | OK |

**Solve-path impact: NONE.** `load_demand` resolves for every year in the span, and
`load_demand_meta` has no solve-path consumer (neiso-88 §2.3). So the 2019 inputs are **durable to
use** and **conditional to rebuild**: a session that ever needs to *regenerate* a pre-2021 block must
run `scripts/data/curate_demand_profile.py` (or `regenerate_clean.py demand-profile`) first.

Checked for asymmetry, which is the part that matters: the partition's absence degrades the **tuned
years identically** — `load_demand` emits the same fallback warning on 2023 as on 2019 — so this is
a span-wide condition, **not a 2019-specific handicap**. It does not disturb the keeper.

---

## 3. Rule 13 admissibility, stated per input

The charter asks this explicitly. The test: *could this same quantity be produced for a FORWARD year
from forward drivers, and would it respond to changed conditions?*

| input | role | rule-13 branch | verdict |
|---|---|---|---|
| `henry_hub_actual` (from `calibration_reference`) | **model input** — `gas_price_override` | delivered fuel price; forward analogue = a forward gas curve | **ADMISSIBLE** — rule 13 names delivered fuel prices explicitly |
| `gas_basis_by_iso_month` / `algonquin_citygate_daily` | **model input** — hub basis | delivered fuel price; forward analogue = basis forwards | **ADMISSIBLE**, same branch |
| `NEISO_<y>_renewable_capacity.csv` | **model input** — renewable upper bound (CF × capacity) | installed nameplate by fuel/zone/month; forward analogue = the interconnection queue / planned additions, and it responds to build-out | **ADMISSIBLE** |
| `campd-unit-outages-NEISO.csv` | **model input** — availability | physical availability event | **ADMISSIBLE** — rule 13 names unit outage windows explicitly |
| `plant_emission_rates_v2`, `fossil_co2_rates` | **model input** — MC term | plant-specific CEMS rates | **ADMISSIBLE** — named in rule 13 |
| `calibration_reference` `generation_twh`/`demand`/`renewables` | **scoring target only** | rule 13's benchmark branch — a measured outcome used ONLY as a validation target | **ADMISSIBLE as a target**; never enters a solve |
| `actual_tail.json`, `actual_lmp_hourly_NEISO`, `bench/` | **scoring target only** | same benchmark branch | **ADMISSIBLE as targets**; never enter a solve |

**No input adjudicated here fails the test, so nothing becomes a default-off diagnostic probe.**
The critical negative is worth stating: **no measured *outcome* is fed back into any solve path.**
Nothing prepared or verified in this session pins a unit to observed generation, adds an offset
tuned to a residual, or rescales an input so the model's output lands on the actuals.

---

## 4. Verification that no tuned-year artifact moved (charter step 3)

Not assumed — measured four ways, and any one of them moving would have stopped the session under
rule 14 `[R-ACCURATE]`:

| check | result |
|---|---|
| **Tracked files modified** | **ZERO.** `git status --porcelain -uno` is empty; the only new paths are this assessment, the probe and its record. |
| **Determination** | `calibration_verdict.py --run-id 2026-08-17-neiso-99-joint-p1` → **`CALIBRATED`**, scorable years 2023/2024/2025, **0 FAILs**, C1 · C2 · C3a · C3b · C4 · C6 · C8 all PASS, C3c the lone ledgered caveat, D-10 free-class C1 **12/12 · free 8/8**. Reproduces neiso-100 §2.1 exactly. |
| **`actual_tail` re-derivation** | `derive()` re-run in memory and diffed against the committed file: **byte-identical**, **0 cell diffs**, **0 tuned-year diffs**. |
| **Keeper audit** | `audit_keepers.py --iso NEISO` → **PASS, 0 failures / 0 warnings** (holdout · marker · status). |

Nothing moved, so nothing was pushed through.

---

## 5. The standing data blocker — re-checked, and the answer is unchanged

`scripts/audit_eia923_completeness.py --year 2025 --no-write` (no write; the canonical part is
untouched). **The FINAL 2025 EIA-923 vintage has still NOT landed**, reproducing the committed
block exactly:

| class | status | reporting |
|---|---|---|
| CC_REGULAR | **INCOMPLETE** | **13 / 30 prior plants missing (57 %)** |
| CC_CHP | **INCOMPLETE** | **3 / 7 missing (57 %)** |
| CT_CHP | INCOMPLETE | 15 / 24 missing (38 %) |

The 2025 C1 CC rows stay **SKIPPED by design** and C2's 2025 gas row stays SKIPPED, both visible in
the verdict output above. **Nothing was estimated around it.**

---

## 6. What this session did NOT do

* **Built nothing.** No input was both absent and preparable, so no file was written beyond this
  assessment, the probe and its JSON record. Manufacturing an artifact to have something to show
  would have been the wrong outcome.
* **Registered nothing** (rule 15) — no run was produced and there is no in-sample delta.
* **Skipped charter step 4 deliberately.** The keeper is unmoved (`2026-08-17-neiso-99-joint-p1`,
  and `frontier.reverified` already carries neiso-100's 2026-08-18 stamp), so the retargeted
  recheck and the `frontier.reverified` re-stamp are **correctly not repeated**. A ceremonial
  repeat adds nothing.
* **Did not re-score the 2022 touchpoint under v3.3.** neiso-100 §3.2 considered and refused it on
  the freeze; that stands as an owner decision and this session does not revisit it.
* **Opened no C3c lever** — every `R`/`I`/`G` cell in the NEISO shard is DO-NOT-REDO.
* **Did not edit `calibration-complete.json`'s `locked_test` field.** neiso-100 §4.1c supplies a
  replacement sentence for the OWNER to adopt; it is not a session's to apply. (For the record, this
  session's own measurement **re-confirms** the clause's premise is false: 2019 **is**
  demand-solvable at HEAD — `load_demand("NEISO", 2019)` returns `(5, 8760)`. Its *conclusion* is
  unaffected; legs (a) and (b) of neiso-100 §4.1 remain live and each is sufficient alone.)
* **Touched no other ISO's** keeper shard, status part or matrix shard.

---

## 7. `final` precondition #2 — the answer the charter asks for

> **The data half of precondition #2 is CLOSED. Precondition #2 as written is NOT fully closed, and
> its entire residual is the `final` grant itself — precondition #5 — not any preparable input.**

Decomposed:

| # | item | status |
|---|---|---|
| 2a | `calibration_reference` 2019 | **CLOSED** (neiso-89), verified schema-complete and span-uniform |
| 2b | renewable-capacity 2019 | **CLOSED** (neiso-89), verified schema-uniform and physically coherent |
| 2c | `actual_tail` 2019 | **NOT a data item.** Upstream ready (8,760 h, coverage 1.0000); row computable; emission gated on `final`. One command after the grant. |
| 2d | `bench/NEISO/2019` | **NOT a precondition.** Byproduct of registration — recommend removing it from the list (§2.1) |

**Nothing further can be prepared for 2019 without the grant.** The 2019 configuration is otherwise
input-complete: seventeen of eighteen inputs resolve, the keeper recipe builds, and every measured
input is the same provenance class as the tuned years.

**Precondition #1 (fleet-vintage retiree window) and #3 (2019 cannot discriminate on C3c) are
untouched by this session and remain exactly as neiso-100 left them.** #3 in particular is not an
engineering item and this session's work does not move it: 2019 remains the one year on the board
that cannot test the criterion NEISO's frontier is declared on.

---

## 8. Rule compliance

* **Rule 1 `[R-STRUCT]`** — no mechanism was tested, tuned, or judged by a residual.
* **Rule 13 `[R-MEASURED]`** — every input adjudicated in §3; no measured outcome enters a solve path.
* **Rule 14 `[R-ACCURATE]`** — no accurate input was reverted; the tuned-year checks in §4 were
  treated as a stop condition, not a formality.
* **Rule 15 `[R-DASHBOARD]`** — **no run produced, nothing registrable.** Zero in-sample delta.
* **Rule 16 `[R-ALLYEARS]`** — not engaged; no solve.
* **Rule 22 `[R-HOLDOUT]`** — **no out-of-training year was solved, scored or registered.** Every
  out-of-training read was of a **measured input** with no model side. The freeze was verified
  **ACTIVE** (`scope.frozen_operations` = solve / score / dashboard registration) and nothing in it
  was spent. The 2019 `actual_tail` row was computed in memory and **deliberately not emitted**.
  NEISO's locked test remains **NEVER GRANTED, NEVER SPENT**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script was re-run against a residual; the only
  derivation performed was a read-only identity check.
* **Rule 25 `[R-ISO-SCOPE]`** — only NEISO was touched; §2.2 was filed to the forecast lane rather
  than acted on, and the neiso-99 cross-ISO routing items are carried forward unchanged (§9).
* **Rule 27 `[R-PUSH]`** — no existing file ≥300 lines was rewritten; the only files added are new.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moves.** An intake session with no mechanism surface
  tests no mechanism, so `docs/codebase-site/data/mechanism-matrix/NEISO.js` is correctly left
  untouched.

---

## 9. Carried forward for other lanes (rule 25), still open

The neiso-99 liquid-fuel-CT routing guard would drop mis-routed rows at **PJM** 593 Edge Moor 10
(33), **MISO** 2001 New Ulm 7 (114) and 8056 Waterford 4 (103), and **NYISO** 2516 Northport UGT001
(42). Each needs that lane's own re-solve. **No cell outside NEISO is stamped here.** (The
`ercot215_control_A` payload-parity item is RESOLVED at HEAD and is not carried.)

## 10. Artifacts

* This assessment.
* `scripts/probes/neiso101_2019_input_prep.py` — the full-span input-preparedness audit.
* `results/calibration/_neiso101_2019_input_prep.json` — its record.

**Next shorthand: `neiso-102`.** No NEISO tuning lever is open. The lane's remaining items are
unchanged: the **data wait** (2025 EIA-923 final vintage) and the **owner decisions** neiso-100
§4.3 enumerates — to which this session adds one small recommendation, that the bench part be struck
from precondition #2's list because it is an output of the spend, not an input to it.
