# FINDING — caiso-189: the CAISO keeper's **C6 UNATTESTED** and its **empty C3c ledger** were ONE mechanical cause — a governance attestation nobody wrote. Repaired post-hoc; **C6 UNATTESTED → PASS, C3c FAIL → ledgered CAVEAT, fails 2 → 1**, and **C3a remains the sole FAIL with the determination unchanged at NOT-YET**

**Outcome: a BOOKKEEPING REPAIR. No LP solved, no bundle regenerated, no solver code,
`ScenarioConfig` default, `configs/` entry or data byte touched.** Keeper **UNCHANGED** at
`2026-08-09-caiso-188-d1-micseam`. DOF ledger **11 / 8**, carried **byte-identical**.
`calibration-complete.json` / `holdout-freeze.json` untouched (owner acts; CAISO holds
neither `complete` nor `final`, so rule 22 D-5(b) re-keying does not fire). **2023–2025
only** — no out-of-training year was solved, scored, read or registered.

**No PRECHECK was written and none is owed.** A PRECHECK exists to fix an identification
before a value exists, so that a measurement cannot be steered by its own result. This
session measures nothing about the market: it writes a governance record, adds an audit
check, and corrects the written record. There is no arm, no gate and no number that could
have been tuned. **C3a was never read as a target** and is reported below only as the
unchanged FAIL it already was.

**Rule 28 `[R-MECH-MATRIX]` statement, as required.** The **CAISO lever queue is EMPTY,
with every cell adjudicated** (caiso-185, re-confirmed caiso-188). **This session is
off-queue by design**: it is governance/attestation repair and record truth-up — **no
lever, no mechanism, no solve.** **No matrix cell changes**; the §5.2 block gains a
session note and one arithmetic correction (§4).

Instrument: `scripts/gen_caiso189_attestation.py` (every premise computed, not typed).
Record: this file, plus the §8 addendum appended to
`FINDING-caiso188-import-tranche-dof-2026-08-09.md`.

---

## §1 — STEP 1: the premise, verified first-hand before anything was written

Three checks, all run against the working tree at `90ba0e1b` (which carries the stated
base `767b29c3` as an ancestor):

| claim | verified | result |
|---|---|---|
| keeper attestation's top-level keys are `["free_parameters"]` only | `json.load(...).keys()` on `results/calibration/caiso188_d1_micseam/calibration_attestation.json` | **CONFIRMED** — exactly `['free_parameters']`, 16,545 bytes |
| `scripts/gen_caiso188_attestation.py` is absent | `ls scripts/gen_caiso*_attestation.py` | **CONFIRMED** — 16 generators, series runs …183, 184 and **stops**; no 185–188 |
| `status/CAISO.js` shows C6 UNATTESTED and 0 ledgered | parsed `frontend/data/backcast/status/CAISO.js` | **CONFIRMED** — `governance.status "UNATTESTED"`, magnitude *"no governance attestation in bundle (attestation has no governance block)"*; `ledger_entries: []`; `grade_summary.ledgered 0`, `fails 2`, `scored 7`; `determination "NOT-YET"`; sole reason *"governance gate UNATTESTED"* |

The paired control `caiso188_d0_control` has the **identical** gap (`['free_parameters']`
only). It is **KNOWN AND NOT FIXED**: the charter scopes this repair to the designated
keeper, and a control's attestation carries no rubric consequence for any registered
determination.

### 1a. The mechanism, stated exactly

`calibration_verdict.score_governance` treats a `free_parameters`-only attestation as
**exactly as unattested as no file at all** — its own comment says so. That single absence
produces both symptoms:

* **C6 UNATTESTED**, which alone forces `NOT-YET` (`determine_from_artifacts`: `if
  gov["status"] != PASS: determination = NOT_YET`);
* **an empty exceptions ledger.** `determine_from_artifacts` reads
  `exceptions = (attestation or {}).get("exceptions", [])`, so the incumbent's four
  entries never carried and C3c's two failing years read as **undocumented** FAILs. The
  owner's C3c standing rule could not cover them either: `_apply_c3c_standing_rule`
  requires **both** a passing governance gate **and** a lone failure, and C3a fails here.

`scripts/audit_keepers.py` check **E8** validates `free_parameters` and nothing else, so it
reported "0 entries, all with root causes" — **green** — on an attestation nobody had
signed. That is why the gap survived every audit (§3).

---

## §2 — STEP 2: the generator, and what it proves rather than asserts

`scripts/gen_caiso189_attestation.py`, modelled on `gen_caiso184_attestation.py` and
`gen_caiso183_attestation.py` ("four fail-closed legs"). Precedent for post-hoc generation
is `gen_pjm153_collapse_attestation.py`, written for `pjm152_collapse_A`, which likewise
shipped its bundle and gate record without its attestation.

**Five fail-closed legs. A failure aborts without writing.** Measured output:

| leg | what it proves | measured |
|---|---|---|
| **G-DELTA** | one flag flipped, nothing else | arms differ on **exactly** `capacity_deliverability_limits`, `False → True`, across 710 config keys |
| **G-SEAM** | Part A **actually resolved** — not merely armed | control at the fitted **7,500.0 MW** limit, binding **764 / 477 / 807 h**, mean dual −2.903 / −0.223 / −0.368; keeper at the published MIC **16,055 / 16,452 / 16,148 MW**, binding **0 h**, dual **exactly 0.0 in every hour of every year**, max group flow 9,497.0 / 9,169.0 / 10,451.5 MW |
| **G-MACHINE** | the machine half of C6, using `calibration_verdict`'s OWN constants so the generator cannot drift from the gate | `outage_source='historic'` ∈ `EXOGENOUS_OUTAGE_SOURCES`; no `FORBIDDEN_FLAGS` active |
| **G-DOF** | the ledger is CARRIED, never rewritten | `n_entries` 11 / `n_residual` 8; `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` `n_scalars` **6**; and the rendered `free_parameters` block is **byte-identical** to the on-disk block (both sit one level deep at `indent=2`, so the section is compared directly, not semantically) |
| **G-EXC** | every carried magnitude is this bundle's own | table in §2b |

**G-SEAM is the one that matters most.** The whole caiso-188 promotion rests on the claim
that Part A now resolves through the published MIC partition instead of no-oping to the
fitted scalar — and a bundle where it silently no-oped would still carry 7,500.0 MW here.
Reading each arm's **own** committed `hourly/network_<year>.parquet` is what makes the
governance note's central sentence checkable rather than asserted.

### 2b. Magnitude verification — two entries were stale, and that is itself a defect

All four exceptions are carried from `2026-08-09-caiso-184-c1-lpbasis` with
`classification`, `reason` and `ledgered_by` **byte-identical**; this session creates no
caveat and spends no ledger slot. Only `magnitude` is refreshed, and the carried text is
quoted **verbatim** beside each new measurement, so nothing is overwritten.

| entry | carried magnitude (source bundle) | measured on `caiso188_d1_micseam` | verdict |
|---|---|---|---|
| C3c 2023 | model **0 h** > $200 (`caiso163_asym_path_ratings`) | model **0 h** vs RT actual 47 h | **unchanged** |
| C3c 2024 | model **0 h** > $200 (`caiso163_asym_path_ratings`) | model **1 h** vs RT actual 35 h | **REFRESHED** |
| C3a 2025 | λ **39.3543** $/MWh (`caiso166_measured_loss_zones`) | **38.87** vs RT 34.42 (**+12.9 %**) | **REFRESHED** |
| C3a 2024 | λ **38.5678** $/MWh, +11.5 % (`caiso166_measured_loss_zones`) | **38.27** vs RT 34.65 (**+10.4 %**) | **REFRESHED** |

Three of four magnitudes were measured on a bundle two or three promotions old. A carried
magnitude measured on a superseded bundle is its own governance defect — an attestation
that states a number the bundle it sits on does not produce — so refreshing them is part of
the repair, not an embellishment of it.

**Two facts that constrain what was carried:**

* **C3c 2025 PASSES on this bundle** (model 0 h vs RT actual 8 h; small-count `|Δ| ≤ 10 h`),
  and caiso-184's ledger carries **no** 2025 C3c entry. None was invented.
* **The two C3a entries are INERT.** Under rubric v3.1 `LEDGERABLE_CRITERIA` is
  `price_tail` **alone**, so `_apply_ledger` returns early for `price_mean` and the FAIL
  stands at full magnitude. They are carried as the historical record only.

**A reading hazard, recorded so nobody misreads the dashboard.** The scorer's
`ledger_entries` field is a **raw echo** of the attestation's `exceptions` list
(`"ledger_entries": exceptions`), so it now shows **four** rows including the two C3a ones.
The binding accounting is elsewhere and is correct: `caveats.ledgered` is
`['C3c price tail / scarcity (RT hourly)']` — **one** criterion — and
`grade_summary.ledgered` is **1** against a budget of 1. No C3a caveat was granted.

`free_parameters` is preserved exactly as found; the byte-identity of that section is
asserted by the generator itself, not claimed here.

---

## §3 — STEP 3: `audit_keepers` check **E10**, which closes the blind spot

E8 could never have caught this: the missing blocks are precisely the ones it does not
look at. **E10** checks the rest of the attestation shape on the same loaded object, with
each leg graded by what it actually costs the verdict:

* **FAIL** — no attestation file; no `governance` mapping (C6 UNATTESTED); any of the four
  assertions missing, **non-boolean** or false (C6 FAIL); or no `exceptions` **list** (every
  ledgered caveat silently vanishes). Truthy non-booleans (`"yes"`, `1`) are rejected: an
  assertion is a signed claim, not a coercion. An **empty** `exceptions` list is fine — most
  keepers ledger nothing — but an **absent** key is not, because then nobody has said
  whether there are exceptions at all.
* **WARN** — everything load-bearing is present but the documentary `schema` version tag is
  missing. `calibration_verdict` never reads `schema`, so no determination moves.

`attestation_shape_finding()` is pure over its input (matching the E9 helper's style) and
is covered by **11 unit tests**, including the exact caiso-188 shape —
`tests/scoring/test_audit_keepers_attestation_shape.py`.

**Cross-ISO finding, REPORTED NOT FIXED (rule 25 `[R-ISO-SCOPE]`).** The ERCOT keeper
`2026-08-09-ercot185-shaped-partial` (bundle `ercot185_shapedarm_B`) carries a **complete**
`governance` block (all four assertions `True`) and a 3-entry `exceptions` list, but **no
`schema` key** — so it surfaces as the WARN above. **Its C6 scores PASS and its
determination is unaffected**; this is a documentary gap, not the caiso-188 gap. It is
another lane's to close, on its next regeneration. No ERCOT file was touched.

`scripts/audit_keepers.py --check` over **all** ISOs: **PASS, 0 failures, 1 warning** (the
ERCOT `schema` tag). CAISO, PJM, NYISO, NEISO, MISO, the holdout gate, the marker gate and
the status parts all read *all checks passed*.

---

## §4 — STEP 4: the record truth-up, and a THIRD contradiction found while doing it

Every correction is dated, sourced, and **annotates rather than replaces**.

**(a) Five un-logged CAISO sessions backfilled** into `docs/calibration-log/caiso.md` —
**caiso-182, 183, 184, 185, 187** — each opening with
*"[backfilled 2026-08-11 by caiso-189 from `<path>`; the session wrote no log entry]"* and
condensed faithfully from that session's own FINDING and PRECHECK. Two of the five
(**183** and **184**) are **keeper promotions** that had no log entry at all. caiso-186 and
caiso-188 already had entries and were not rewritten.

**(b) The caiso-188 log entry** gains a dated correction block above its opening line:
"Keeper … UNCHANGED; no promotion proposed" is **SUPERSEDED** — the owner promoted
`2026-08-09-caiso-188-d1-micseam` in the same session
(`docs/handoffs/caiso-186-owner-sitting-2026-08-09.md`: "**KEEPER PROMOTED, OWNER-DIRECTED
IN THE SAME SESSION**"). The rest of the entry stands as written.

**(c) `FINDING-caiso188` gains a §8 ADDENDUM** recording the promotion, the missing
attestation, the repair and the verdict delta. **No existing text was altered** — the same
pattern caiso-183's own finding uses for its promotion addendum.

**(d) `frontend/data/backcast/keepers/CAISO.json`'s `disposition_note`** had two clauses
that were **false in bytes** at promotion, now corrected with the superseded wording quoted:

* *"C3c FAIL (**the single ledgered caveat, carried VERBATIM** — no new slot spent, no new
  caveat created)"* — **nothing was carried**: `ledger_entries` was empty and C3c's two
  failing years read as undocumented FAILs.
* *"**C8/C6 as the incumbent**"* — **C6 was not as the incumbent**: caiso-184 *has* a
  governance block and this bundle did not.

A third clause was aspirational in the same way: the note's "**8 criteria scored**" was
**7** while C6 was unattested. All three are true **now**, and only because this session
made them so — the note says exactly that. `FINDING-caiso188` §5 had stated the true
position all along (both arms NOT-YET on C6 UNATTESTED), which is why the charter's rule
that FINDINGs outrank the log held here.

**(e) The stale "7 live fitted scalars" — and the contradiction that stopped a blind
renumber.** The charter directed correcting these 7 → 6, citing the ledger's
`n_scalars: 6`, "matrix §5.2 first". **Only one of the two named places was actually
wrong**, and the other is at a different scope:

| place | prints | scope | disposition |
|---|---|---|---|
| `docs/mechanism-testing-matrix.md` §5.2 header | 7 | the **`IMPORT_TRANCHES[CAISO]` ROW**, over its own "4 spot capacities + 2 firm prices" enumeration | **WRONG — 4 + 2 = 6.** Corrected 7 → 6, annotated, citing `n_scalars: 6` |
| `docs/handoffs/caiso-186-owner-sitting-2026-08-09.md` §3.3 + §5 row 4 | 7 | the **CROSS-ROW** CAISO total: `battery_dispatch_adder` **1** + firm prices **2** + spot capacities **4** | **CORRECT at its own scope** — its §3.3 table sums to exactly 7. **NOT renumbered**; a dated scope clarification added instead |

The ledger's `n_scalars: 6` is the `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` row **alone**;
the memo's 7 includes `battery_dispatch_adder`, which is its own separate ledger row.
Renumbering the memo to 6 would have made its own arithmetic wrong — falsifying a correct
record in the name of a correction.

This also **corrects `FINDING-caiso188` §1**, which asserts that "this block's own earlier
text **and the caiso-186 sitting memo** both print '7 live fitted scalars' over the same
enumeration (4 + 2)". The first half is right; **the second is not** — the memo prints 7
over a 1 + 2 + 4 enumeration across three rows. Recorded here and in the memo's own
clarification block rather than edited into the finding, which is addendum-only.

---

## §5 — STEP 5: the verdict delta, measured

`scripts/calibration_verdict.py --run-id 2026-08-09-caiso-188-d1-micseam`, committed
artifacts only, **no solve**:

| | before | after |
|---|---|---|
| **C6 governance** | **UNATTESTED** | **PASS** |
| **C3c price tail** | **FAIL** (undocumented) | **CAVEAT**, `caveat_kind: ledgered` (2023 + 2024; **2025 PASSES**) |
| failing criteria | **2** (`price_mean`, `price_tail`) | **1** (`price_mean`) |
| scored criteria | 7 | **8** |
| ledgered caveats | 0 | **1 / 1** (C3c) |
| target-grade criteria | 5 | 6 |
| **determination** | **NOT-YET** | **NOT-YET** *(unchanged)* |
| determination basis | *"governance gate UNATTESTED"* | *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |

**C3a mean LMP is unchanged and is reported, not treated**: +3.4 % (2023, PASS), **+10.4 %**
(2024, FAIL), **+12.9 %** (2025, FAIL) against a ±10 % band. It is now the **sole**
load-bearing FAIL and the **only** thing standing between this keeper and
`CALIBRATED-WITH-CAVEATS`. Its open root cause is unchanged and is not a session lever: the
**walled hourly pumped-storage water state** (`FINDING-caiso140` §B / caiso-141 A2), an
owner-funded intake.

**The C3c standing rule correctly stayed silent.** With C3a failing, the lone-failure guard
in `_apply_c3c_standing_rule` blocks it — which is the guard working. C3c reached CAVEAT
through the **explicit** exceptions ledger (the ERCOT/MISO route), exactly as predicted.

Also run: `scripts/build_status.py --iso CAISO` (rebuilt part committed);
`scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` → **D-9 overlay quarantine
PASS**, **D-6 holdout quarantine PASS**; `ruff check .` clean;
`scripts/check_mechanism_matrix.py` → integrity OK, keeper stamps and §5.x prose headers
match every shard.

---

## §6 — Governance

* **No LP, no solve, no bundle regenerated.** No edit to solver code, `ScenarioConfig`
  defaults, `configs/` or any data file. No other ISO's lane touched (rule 25).
* **`free_parameters` content is untouched** and its byte-identity is machine-asserted.
* **No existing FINDING text was altered** — `FINDING-caiso188` is addendum-only.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only; no out-of-training year solved, scored, read or
  registered. Both markers untouched; CAISO holds neither `complete` nor `final`, so the
  never-granted locked test (2019, H1-2026) remains unspent and unavailable.
* **Rule 20 `[R-DOF]`:** ledger unchanged at 11 / 8; the attestation now actually lists it
  under a signed governance block, which is what the rule asks for.
* **Rule 28 `[R-MECH-MATRIX]`:** no mechanism tested, no cell changed; §5.2 carries this
  session's note and the §4(e) arithmetic correction.

---

## §7 — Known-open, carried forward

1. **C3a remains the sole load-bearing FAIL** (+10.4 / +12.9 %). Root cause open and
   owner-level: the walled hourly PS water state. **Nothing in this session touches it.**
2. **`caiso188_d0_control` still has a `free_parameters`-only attestation.** Known, not
   fixed — a control carries no registered determination. E10 does not reach it (it audits
   keepers), so it will not resurface as a gate failure; it is recorded here so a future
   session that promotes a control knows to generate one first.
3. **The ERCOT keeper's missing `schema` tag** (§3) — another lane's, WARN-level, no
   determination effect.
4. **`FINDING-caiso188` §1's mis-attribution** of the "7 live fitted scalars" print to the
   caiso-186 sitting memo (§4e) — corrected in the memo and here, not in that finding.
5. **Still owed from caiso-188, untouched here:** the forecast orchestrator has no
   `check_clean_partitions` guard call; nothing committed records which seam cap a bundle
   solved against; the dormant `hydro_ror_split` is its own A/B.
6. **The generator series is per-promotion by construction.** E10 now fails a keeper whose
   promotion skips it, but the underlying pattern — a bespoke script per promotion — means
   the next owner-directed same-session promotion can still ship without one **until** the
   audit runs. E10 makes that loud instead of silent; a shared generator would make it
   impossible. Filed, not built.

---

SESSION-REPORT caiso-189 c6-attestation
STATUS: COMPLETE
VERDICT DELTA: C6 UNATTESTED→PASS · C3c unledgered→ledgered CAVEAT (2023+2024; 2025 PASSES) · fails 2→1 (sole remaining: C3a price_mean) · determination NOT-YET (unchanged)
FILES PUSHED: `scripts/gen_caiso189_attestation.py`, `results/calibration/caiso188_d1_micseam/calibration_attestation.json`, `frontend/data/backcast/status/CAISO.js`, `scripts/audit_keepers.py`, `tests/scoring/test_audit_keepers_attestation_shape.py`, `docs/calibration-log/caiso.md`, `results/calibration/FINDING-caiso188-import-tranche-dof-2026-08-09.md`, `frontend/data/backcast/keepers/CAISO.json`, `docs/mechanism-testing-matrix.md`, `docs/handoffs/caiso-186-owner-sitting-2026-08-09.md`, `results/calibration/FINDING-caiso189-c6-attestation-2026-08-11.md`
CONTRADICTIONS FOUND: (1) the charter states caiso-184's attestation holds "4 C3c price_tail entries" — in bytes it holds **2 `price_tail` (2023, 2024) + 2 `price_mean` (2025, 2024)**, and the 4th carries `ledgered_by` instead of `carried_from`. All four were carried; the two `price_mean` entries are INERT under rubric v3.1. (2) the charter states `docs/handoffs/caiso-186-owner-sitting-2026-08-09.md` "already carries the 7→6 correction" — it does **not**; the correction lives in the **matrix**'s caiso-188 block, while the matrix's own §5.2 **header** was still stale. Reversed from the charter. (3) NEW — the memo's "7" is **not** stale: it is a CROSS-ROW total (`battery_dispatch_adder` 1 + firm prices 2 + spot capacities 4 = 7) whose own §3.3 table sums to 7, a different scope from the ledger's row-level `n_scalars: 6`. Renumbering it would have falsified a correct record, so it was annotated instead — and this also corrects `FINDING-caiso188` §1, which mis-attributes the row-level 4+2 print to that memo.
OPEN ITEMS / HANDOFF: C3a (+10.4 / +12.9 %) is now the SOLE load-bearing FAIL and the only barrier to `CALIBRATED-WITH-CAVEATS`; its root cause is the owner-funded walled hourly PS water-state intake, unchanged and untouched. `caiso188_d0_control` keeps the same attestation gap (control, no registered determination — known, not fixed). ERCOT keeper `2026-08-09-ercot185-shaped-partial` lacks a `schema` tag (WARN, no determination effect, another lane's under rule 25). caiso-188's own still-owed items are untouched: the forecast orchestrator's missing guard call, no committed record of which seam cap a bundle solved against, and the dormant `hydro_ror_split` A/B.
