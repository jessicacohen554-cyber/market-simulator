# FINDING — capx D63: the two negatives D60-R3 routed are closed, six rows and no seventh, FC-7 the only row that moved on either bundle — and D62's suffixed registration landed

**Lane:** capx D63. **ZERO LP** — no solve, no re-solve, no control solve, nothing armed, no
`ScenarioConfig` field or value changed, no marker, no freeze, no mechanism-matrix cell.

**Pre-declaration:** `PREDECL-capx-d63-2026-09-06.md`, pushed to the branch (and merged to
`main` as PR #5105) **before a single row was authored** — the sequence owner ruling **Q37**
(capx ledger §3, r#34, rubric §5 second limb) exists to enforce.

---

## 0. Verdict (one paragraph)

The six rows are written, both bundles re-scored artifact-only, and **every §3 prediction of
the pre-declaration HIT to the letter**: `miso-t1f` FC-7 **CAVEAT → PASS** on a 7-of-7 ledger,
`caiso-t1f` **CAVEAT → PASS** on 2-of-2, and **neither determination moved** — both stay
**HOLD** on FC-1 + FC-2 FAIL, because a retiring caveat cannot clear a reason. **FC-7 was the
ONLY row that moved on either bundle**, measured row-by-row across all eight categories, against
a control reproduction run **first**. No STOP fired. The scope is **six fields, not the
charter's seven** — measured before any row existed, there is no seventh — and that deviation
is recorded rather than reconciled. One movement is reported against interest: the regenerated
ledgers' **reported-only** `epoch_field_gaps` block grew by five `ScenarioConfig` fields added
to HEAD since the runs solved; rebuilding the same ledgers at the same HEAD with the six rows
**removed** produces the identical epoch block, so that is HEAD's drift and not this lane's.
Separately, capx **D62's arm is registered SUFFIXED** as `pjm-t1h-d62-pubbar` (**HOLD** on FC-3
FAIL) carrying **D62's own §8 DO-NOT-ARM verdict** as its provenance string; the bare `pjm-t1h`
and every PJM board row are untouched.

---

## 1. THE SCOPE WAS SIX, NOT SEVEN — measured before any row was authored

The charter names *"the SEVEN fields"*, then enumerates six by name and adds *"any other
`unattested` entry the committed `miso-t1f` / `caiso-t1f` `dof_ledger.json` carries"*. Measured
from the two committed artifacts at the lane's base, **before any row existed**:

| bundle | committed ledger | entries | UNIDENTIFIED |
|---|---|---|---|
| `miso-t1f` | `results/ff-t1f-d60/miso/dof_ledger.json` | 7 | **5** |
| `caiso-t1f` | `results/ff-t1f-d60/caiso/dof_ledger.json` | 2 | **1** |

**There is no seventh.** The identified remainder was already curated by earlier lanes: MISO's
`adequacy_accounting_ratio_dated_net` (D60-R3's Q40 row) and `forecast_xyear_warmstart` on both
(the D-10 posture row). Six rows owed, six written. The deviation from the charter's count is
recorded here and in the pre-declaration §1, never silently reconciled.

---

## 2. THE SIX ROWS AND THEIR COMMITTED IDENTIFICATION SOURCES

All six live in `CURATED_IDENTIFICATIONS` in `scripts/build_forecast_dof_ledger.py`, keyed
**`(ISO, field)`** — never `("*", field)` — and every one carries `requires: "iso-registry"`.

| # | key | ident. | the committed source that identifies the value | evidence |
|---|---|---|---|---|
| 1 | `("MISO", "entry_vre_capacity_revenue")` | `design-decision` | **Owner decision D-2′** (sitting Addendum O, signed 2026-08-04, lane FFR-4B): MISO's PRA **accredits and pays** wind and solar like any other Planning Resource, so denying VRE entry the RA payment is not modelling MISO's market. VRE was the only accredited class denied a payment that thermal entry, the thermal retirement screen and storage entry all took through the **same** seam (`capacity_price_per_firm_mw_yr`) — while its accredited MW were already on the supply side of the adequacy ledger. Arming **removes an exception**; it adds no second channel (rule 19). | `iso_configs.py::_miso_config` cite block; `ffr-3v-miso-entry-screen-2026-08-04.md` §3.3 / §7 item 1a |
| 2 | `("MISO", "entry_vre_zone_selection")` | `design-decision` | **capx D33**: single-bucket VRE siting in MISO is wrong **in kind** — `RENEWABLE_ZONE_ALLOCATION` sent every economically-entered solar MW to MISO-South, the one model zone excluded from every state compliance region's eligible-zone mask, so the screen priced new solar at a $0 REC credit while the run's own zonal REC vector peaked at the $30/MWh ACP. A siting-**representation** repair reading the run's own vector and the existing masks. | `_miso_config` cite block; `FINDING-capx-d33-miso-additions-repair-2026-09-02.md` §2 |
| 3 | `("MISO", "miso_rps_compliance_regions")` | `design-decision` | **Owner decision D-26** (Addendum Y.4, signed 2026-08-06, lane ARM-MISO): the single MISO-wide RPS row silently asserts **free intra-ISO REC trade**, false in MISO (MCL 460.1029; CEJA's centralized IPA procurement; MN's delivered-to-retail construction) — it let Iowa's surplus pay Michigan's bill. Armed, that row is **replaced** (rule 19, never stacked) by K=5 per-state rows, each with its statute's mask, obligated-load RHS and $30 ACP escape. | `_miso_config` cite block; `ffr-7b2-rps-krow-clean-rows-2026-08-06.md` §3.1; `tests/unit/config/test_miso_rps_region_arming.py` |
| 4 | `("MISO", "miso_clean_tier_rows")` | `design-decision` | **Owner decision D-29** (Addendum AK.8, signed 2026-08-11, lane ARM-3-ARM): a **second independent** row family riding the Arm-2 K-row machinery — MN carbon-free (Minn. Stat. §216B.1691 subd. 2g) and MI clean (2023 PA 235 / MCL 460.1029), each with its statute's mask, RHS and $30 ACP escape. Both blockers closed on the record: the §45U composition by owner D-28 option A, the zone-mask defect by ARM3-FIX. | `_miso_config` cite block; `arm3-fix-zone-mask-2026-08-09.md` §4 (R1–R5) |
| 5 | `("MISO", "retirement_sector_gate")` | `design-decision` | **capx D53**, armed for MISO ONLY by owner instruction on the measured A/B: a **pure candidate-set partition** — 59 GW of regulated-utility capacity whose owners never subject it to a merchant test leaves a merchant screen, so the pool the reliability floor masks is the merchant pool (10 % real-exit density vs 4 %) and the floor's release lands at plants that actually exit (**99.8 %** plant-grain precision vs 1.1 %). All four pre-stated limbs MET; every retirement row byte-identical on the bare recipe. | `_miso_config` `retirement_sector_gate` cite block; `FINDING-capx-d53-2026-09-05.md` §6 / §6.1; `DESIGN-capx-d53-sector-gate-2026-09-05.md` |
| 6 | `("CAISO", "negative_renewable_offers")` | `design-decision` | The representation of **CAISO's actual renewable offer conduct**: CA renewables bid **below $0** in oversupply for their RPS/REC and federal-PTC keep-running value, so the marginal (curtailed) midday unit clears negative (2024 RT `da_pct`: p5 −$10, p1 −$24, min −$41). Without it the model's availability-capped wind/solar slices are never marginal and it floors at $0. CAISO's by the **ERCOT-65 rule-25 adjudication** in the same registry block. | `scenarios.py::negative_renewable_offers` + `::renewable_keep_running_value` cite blocks; `_caiso_config` cite block; `policy.eac.apply_negative_renewable_offer_floor` + `tests/test_negative_renewable_offers.py`; **the CAISO backcast keeper record** — keeper `2026-09-05-caiso-252-b1-notrim` carries the field `True` at `renewable_keep_running_value: 20.0` in `results/calibration/caiso252_b1_notrim/run_config.json`; CAISO matrix cell **`K`** on caiso-216 |

**Rule 21 `[R-DOF]` holds by inspection: no value was chosen here.** Every row cites a document
already committed before this lane opened. **Every one of the six values is a boolean gate**
selecting *which representation* the model uses — an accreditation payment, a siting resolver, a
compliance grain, a screen partition, an offer floor — so **no row identifies a magnitude**, and
the builder's own guard (`design-decision` may never identify a number) would refuse any that
did. CAISO's floor **level** ($20/MWh) is the separate registered field
`renewable_keep_running_value`, held at its shipped default and therefore **not an entry of this
ledger at all**; the gate identifies no number.

**Rule 25 `[R-ISO-SCOPE]` holds by construction and by test:** an `(ISO, field)` key cannot
identify another ISO's value even if that ISO later arms the same field.

**Tests** (`tests/scoring/test_forecast_dof_ledger.py`, new `D63CuratedRowTests` — 6 tests,
24 subtests; module total **26 passed / 29 subtests**): every row is ISO-keyed, registry-gated
and carries no `expected` pole; each identifies at the live registered value with provenance
`iso-registry`; the `requires` gate **refuses** with the refusal recorded when the registry match
fails; another ISO's run never borrows a row; and — the lane's own object end to end — the full
MISO and CAISO registry override sets now carry **zero** `unattested` entries, which the scorer
reads as **FC-7 PASS**. `ruff format` + `ruff check` clean on both edited files.

---

## 3. THE CONTROL, RUN FIRST

Before a single row was authored, each committed verdict was **reproduced at HEAD from its own
committed artifacts** with the same invocation the re-score would use, so the ledger input is
provably the only delta (the capx-D8-RE / D60-R3 protocol):

| bundle | committed vs reproduced, every field except `provenance` | `cache_epoch` |
|---|---|---|
| `miso-t1f` | **IDENTICAL** | `b1a73a087064ffd8` = `b1a73a087064ffd8` |
| `caiso-t1f` | **IDENTICAL** | `29f8eb372810195f` = `29f8eb372810195f` |
| `pjm-t1h-d57-clearing` *(the t1h invocation's own control)* | **IDENTICAL** | `f0e050e820c1159a` = `f0e050e820c1159a` |

The third row is what licenses §5: the `--tier t1h --hindcast-score … --run-config …`
invocation used to score D62's arm reproduces D57's committed `forecast_verdict.json`
byte-for-byte, so the shape is verified on a known answer before it is used on a new one.

---

## 4. THE TWO ARTIFACT-ONLY RE-SCORES — before and after

Same bundle, same bytes, same cache key, same run. Only the ledger's **labels** changed.

| bare key | ledger before | ledger after | FC-7 | caveats before → after | determination |
|---|---|---|---|---|---|
| `miso-t1f` | 7 entries, **5 unattested** | 7 entries, **7 identified / 0 unattested** | **CAVEAT → PASS** (`7 entries well-formed (0 open residual DOF listed)`) | `FC-7 provenance & DOF`, `FC-8 runtime feasibility: over runtime budget` → **`FC-8` alone** | **HOLD → HOLD** |
| `caiso-t1f` | 2 entries, **1 unattested** | 2 entries, **2 identified / 0 unattested** | **CAVEAT → PASS** (`2 entries well-formed (0 open residual DOF listed)`) | `FC-7 provenance & DOF` → **`[]`** | **HOLD → HOLD** |

**Every §3 prediction of the pre-declaration HIT**, including both blunt negatives it insisted
on: **neither determination moves.** Both runs read HOLD on
`FC-1 structural integrity (I1-I14) FAIL` + `FC-2 adequacy & equilibrium behavior FAIL`; MISO's
FC-1 keeps `['I12','I7']` and CAISO's keeps `['I12','I7']`. **This lane closed a measurement gap
and moved no model result.**

### 4.1 FC-7 was the ONLY row that moved — measured, not asserted

Diffed row-by-row across **all eight categories** of both bundles, comparing status,
applicability, row set, row status and row detail:

| bundle | rows that moved |
|---|---|
| `miso-t1f` | `FC-7` CAVEAT → PASS; `FC-7/dof ledger` CAVEAT → PASS. **Nothing else.** |
| `caiso-t1f` | `FC-7` CAVEAT → PASS; `FC-7/dof ledger` CAVEAT → PASS. **Nothing else.** |

Determination, reasons, cache epoch and every FC-1 / FC-2 / FC-3 / FC-4 / FC-5 / FC-6 / FC-8 row
are byte-identical to the records they replace. That is what makes the re-score honest: a
`CURATED_IDENTIFICATIONS` row is read by **one** consumer, `_apply_curation`, and cannot reach a
`ScenarioConfig` field, a cache key, a solve, a trajectory or any other FC category. **STOPs
D63-1 through D63-4 did not fire.**

### 4.2 One movement REPORTED AGAINST INTEREST, and attributed away from this lane

The regenerated ledgers' `epoch_field_gaps.fields_added_since_epoch` block grew by five entries
on **both** bundles — `nyiso_ct_peaker_bands_measured`, `nyiso_gas_bridge_startup_aware`,
`voluntary_clean_demand_path`, `voluntary_eligible_fuels`,
`voluntary_wtp_ceiling_usd_per_mwh` — because the ledgers are rebuilt at a HEAD later than
D60-R3's, and those five `ScenarioConfig` fields landed in between.

**It is HEAD's drift, not this lane's, and that is measured rather than argued.** Rebuilding
both ledgers at **this same HEAD** with the six rows **removed from the table** produces:

* the **identical** `epoch_field_gaps` block (equal to the with-rows build, **not** to the
  committed one), and
* the **identical** pre-repair counts, 5 and 1 `unattested`.

So the rows own the identification change and **nothing else**, and the epoch delta would have
appeared on any rebuild at this sha. Epoch drift is **reported, never scored** (the builder's own
scope statement), and it appears in no FC row — which §4.1's row-by-row diff independently
confirms.

A second, purely cosmetic delta is the builder's own property and not a movement: an entry's
`attestation_question` field is emitted **only while the entry is UNIDENTIFIED**
(`build_forecast_dof_ledger.py`, `if entry["status"] == "UNIDENTIFIED"`), so it disappears on
each newly-identified entry — exactly as it did on D60-R3's own row in that lane's committed
diff.

---

## 5. D62's SUFFIXED REGISTRATION

The registration capx D62 withheld while D60-R3 owned `ff-verdicts.json`.

* **Key `pjm-t1h-d62-pubbar`.** The bare **`pjm-t1h` is UNTOUCHED** — it stays D57 arm A
  (`f0e050e820c1159a`), which is this arm's own control.
* Already committed and unchanged by this lane: the hindcast sidecar
  `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar.json`, the bundle, and the
  `VERDICT_MAP` row in `scripts/register_forecast_run.py`. The run is already in the Y-24
  `registration_ratchet_baseline`, so the invariant-declaration gate is satisfied for it and
  **this lane declares no invariant failure and adjudicates none**.
* **What D63 added:** the `ff-verdicts.json` entry the FF-2D snapshot was missing, scored
  **from committed artifacts only** —
  `forecast_verdict.py --tier t1h --hindcast-score …/PJM/b98060898fceb3da/score.json
  --run-config …/run_config.json` — the invocation §3 verified on D57 first. **Zero LP.**

**Reading, and it is the pre-declared one:**

| field | value |
|---|---|
| determination | **HOLD** |
| reasons | `FC-3 capacity-evolution skill (T1-H hindcast) FAIL` |
| caveats | `FC-7 provenance & DOF` |
| FC-1 / FC-8 | SKIPPED (no committed invariant record, no perf ledger) — as on the D57 control |
| cache epoch | `b98060898fceb3da` |

**The FC-3 band list is itself the evidence for D62's two headline claims**, and it differs from
the D57 control's in exactly the way D62 §5.4 measured:

* **drops** `add.by_tech.gas_cc` and `add.shares.gas_cc` — the spurious +4.0 GW of 2023 gas-CC
  entry disappearing, `additions.gas_cc` **FAIL → PASS**;
* **gains** `add.shares.wind` — the wind SHARE band flipping PASS → FAIL as arithmetic on the
  smaller denominator, wind's absolute build being identical.

**Provenance string = D62's own verdict, not this lane's.** The note carries §8 verbatim in
substance: **DO NOT ARM as it stands**, because the lane's own pre-registered **STOP 5 FIRED**
(2024/25 price 165.84 → 188.57 $/MW-day, through the **census** — 172,158.6 → 170,576.6 MW, the
arm's own 2022–2023 exits leaving 1,582 MW fewer standing — not the offer side), FC-3 worsens
where it already failed (`retire.total_gw` 18.702 → 20.144 against an actual 15.062, recall
0.60 → 0.55), and **4.137 GW of oil over-exits** because its published bar falls $1.64/kW-yr
while the clearing price falls $29.32 — set against what the measurement does establish: the
2022/23 clearing price 1.522× → **0.936×** the published RCP at a cleared position −0.477 →
**+0.267** pt, at **zero free parameters**. D67 and D66 are routed ahead of any arming, and every
other ISO stays `U` under rule 25. **NOTHING ARMS**, and **D63 adjudicates nothing about D62**.

---

## 6. WHAT MOVED ON THE BOARD, AND WHAT DID NOT

`frontend/data/forecast/program-status.json`, asserted key-by-key against the pre-edit file:

| ISO row | change |
|---|---|
| **MISO** | `fc["FC-7"]` **CAVEAT → PASS**. `t1f_determination` **HOLD, unchanged**. Nothing else. |
| **CAISO** | `fc["FC-7"]` **CAVEAT → PASS**. `t1f_determination` **HOLD, unchanged**. Nothing else. |
| ERCOT · PJM · NYISO · NEISO | **byte-identical** |

Plus one new top-level record block, `d63_dof_rows`. `frontend/data/forecast/ff-verdicts.json`:
the two re-scored entries (prior notes preserved **verbatim**, the D63 note appended) and one new
key; **all 102 other board keys byte-identical**, asserted programmatically.

The generated namespace (`registry/`, `runs/`, `manifest.js`, `program-status.js`) is gitignored
and rebuilt by the Pages deploy; `--reindex` was run locally as a validation and assembled 94
runs, baking `determination: HOLD` / `verdict_key: pjm-t1h-d62-pubbar` onto D62's sidecar.

---

## 7. THE D60-R4 COLLISION, RESOLVED ON THE RECORD

The charter makes D60-R4 the sole writer of `ff-verdicts.json` / `program-status.json` **until
its PR merges**. State, measured at this lane's start and re-measured before the board write:

* D60-R4's commits are on `origin/main` (`5d639e31`, `fc8e2921`, `f4ebc611`, PRs **#5093** and
  **#5097**, both merged) and **no `claude/capx-d60r4-*` branch exists on origin** at either
  check.
* Its `Addendum E.4 — The control's result` is committed **empty**, so its earned control solve
  is outstanding — which is why this lane treated it as **LIVE** and took the conservative
  branch: **steps 1 and 2 touched no board file**, and the board write waited behind a
  re-check of `origin/main`.
* **The hold condition is discharged, not waived:** everything D60-R4 has produced has merged,
  nothing of it is open, and its outstanding control is *"registered NOWHERE, and its bundle is
  deleted before the PR merges"* by its own §E.3 — so it will not write a verdict key. The
  collision surface is its board **provenance text** alone, and the two lanes' keys are
  disjoint: D60-R4 reads PJM `t1f` and NEISO `t3`; D63 writes MISO `t1f`, CAISO `t1f` and the
  new PJM `t1h-d62-pubbar`. **STOP D63-5 did not fire.**

A rebase happened **between** steps and never during one: PR **#5105** auto-merged step 1 alone
while step 2 was being pushed, so the branch was rebased onto the resulting `main` and step 2
replayed on top.

---

## 8. WHAT THIS LANE DOES NOT CLOSE

1. **Neither determination moves, and neither ISO is any closer to PROMOTE.** `miso-t1f` and
   `caiso-t1f` both stay HOLD on **FC-1 `['I12','I7']` + FC-2**, which is where the real work is.
   FC-7 was a *measurement* gap; the model gaps are untouched and unrelieved.
2. **MISO keeps its FC-8 caveat** (over runtime budget). Outside this lane's scope entirely.
3. **The rows are only as durable as the registry they gate on.** Each applies iff the run's
   value byte-matches the live registered override; if a later lane arms a **seventh** MISO or
   CAISO override without its curated row, FC-7 silently reverts to CAVEAT on the next re-score.
   `test_the_miso_and_caiso_registry_override_sets_are_now_fully_identified` is the guard that
   makes that fail loudly instead.
4. **D62 is unadjudicated by this lane.** Registering a run is not promoting it; §8's DO-NOT-ARM
   stands, D67 and D66 stay routed ahead of it, and the arming question remains an owner card.
5. **The `epoch_field_gaps` growth of §4.2 is disclosed, not repaired.** It is a property of
   re-emitting an old run's ledger at a new HEAD; it is reported-only and scores nothing, and no
   lane owes it a fix — but a reader diffing two vintages of the same ledger should expect it.

---

## 9. GOVERNANCE ATTESTATION

* **Rule 21 `[R-DOF]`** — the ledger REPORTS identification and never supplies one. Every row
  cites a document committed before this lane opened; **no value was chosen**; all six values are
  booleans, so no row identifies a magnitude. Six fields were owed and six written — none was
  skipped for want of a citable source, and none was invented for want of one.
* **Rule 22 `[R-HOLDOUT]`** — no out-of-training year solved, scored or registered. The two
  re-scored bundles are 2026–2030 forecast-mode runs; D62's is a 2021–2025 realized hindcast. No
  marker, freeze or tier read or written.
* **Rule 24 `[R-REGISTRY]`** — no tunable added, moved or renamed. `CURATED_IDENTIFICATIONS` is a
  reporting table read by one consumer and cannot change a solve.
* **Rule 25 `[R-ISO-SCOPE]`** — every row keyed `(ISO, field)`, never `("*", field)`; asserted by
  test in both directions.
* **Rule 27 `[R-PUSH]`** — `scripts/build_forecast_dof_ledger.py` (1,158 → 1,341 lines) and
  `tests/scoring/test_forecast_dof_ledger.py` (406 lines) edited locally and pushed as exact
  on-disk bytes, **blob-verified after the push** (hash and line count, local vs remote);
  `ff-verdicts.json` and `program-status.json` likewise.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moved.** This lane tests no mechanism, proposes no
  lever and adds no `ScenarioConfig` field. D62's own cell
  (`PJM.js::capacity_going_forward_bar_published`, `cell: "."`, `fc: "O"`) already records the
  suffixed registration and needed no edit.
* **Rule 29 `[R-SCREEN]`** — not applicable: zero LP, no arm, no screen, no control solve, no
  bundle created or deleted.

---

## 10. REPRODUCTION

```
# control first — both committed verdicts reproduce at HEAD from committed artifacts
python scripts/forecast_verdict.py --tier t1f \
  --summary     results/ff-t1f-d60/<iso>/full_horizon_summary.json \
  --run-config  results/ff-t1f-d60/<iso>/run_config.json \
  --dof-ledger  results/ff-t1f-d60/<iso>/dof_ledger.json

# the re-score: rebuild the ledger, then re-score on the same bytes and the same key
python scripts/build_forecast_dof_ledger.py results/ff-t1f-d60/<iso>
python scripts/forecast_verdict.py --tier t1f ... \
  --json-out    results/ff-t1f-d60/<iso>/forecast_verdict.json

# D62's suffixed registration, committed artifacts only
python scripts/forecast_verdict.py --tier t1h \
  --hindcast-score results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/PJM/b98060898fceb3da/score.json \
  --run-config     results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/run_config.json \
  --json-out       results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/forecast_verdict.json

python -m pytest tests/scoring/test_forecast_dof_ledger.py -q   # 26 passed, 29 subtests
python scripts/check_mechanism_matrix.py                        # exit 0 (anchor warnings pre-exist)
```

**The full `tests/scoring/` run and its four failures, disclosed rather than left for a reader
to trip over.** `1453 passed, 4 failed, 5 skipped, 80 subtests` — the four are
`test_ff_readiness_battery.py::{test_walk_inputs_trivial_single_year,
test_resolve_report_no_hard_fail_full_horizon,
test_ercot_confirmed_horizon_is_reported_not_failed,
test_build_registration_scorecard_no_iso_gate_open}`. They are **pre-existing and
environmental**, not this lane's: each fails on *"clean partition unbuilt (`data/clean` is
gitignored)"* under this lane's declared `DATA PROFILE: code`, and **all four reproduce
identically at the base with every change of this lane stashed** (`4 failed, 20 passed`).
`check_mechanism_matrix.py` exits 0; its anchor warnings name `scenarios.py` rows this lane
never touched.

---

*capx D63 · 2026-09-06 · zero LP · owner ruling Q37 · pre-declared before authoring.*
