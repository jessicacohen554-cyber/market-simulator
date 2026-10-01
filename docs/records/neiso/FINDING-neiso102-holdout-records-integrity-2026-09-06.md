# FINDING — neiso-102: NEISO's status card was showing 2022 twice, and the auditor could not see it

**Session** neiso-102 · **Date** 2026-09-06 · **ISO** NEISO · **LP minutes spent: ZERO**
**Branch** `claude/neiso-records-integrity-rkr3xt`
**Nothing solved, scored, registered or promoted. No mechanism tested. No verdict moved.**

---

## 1. Verdict

Two defects, one live and one latent, both closed.

| # | Defect | Status |
|---|---|---|
| **A** | `keepers/NEISO.json` carried a hand-authored `holdout_touchpoint` block naming a **pruned** run. The live Calibration Status card rendered **2022 twice, with different determinations**, the upper one a dead link. | **FIXED** — block deleted, status part rebuilt |
| **B** | `audit_keepers.py` was **structurally blind** to defect A — it never read `holdout_touchpoint` at all (0 occurrences at HEAD). | **FIXED** — new check **E12** |

NEISO was **the last of the six ISOs** still carrying such a block. PJM's was
removed one day earlier by pjm-166 (`3001f913`); ERCOT, CAISO, MISO and NYISO
never had one.

**Rule 30(c) holds throughout: NEISO's determination is unchanged at `CALIBRATED`.**
That is the train-tier (2023–2025) verdict and a held-out year never moves it.

---

## 2. Defect A — the contradiction, measured

The shard block named `2026-08-06-neiso-2022-corrected-basis`. That run was
pruned on 2026-09-05 under the ercot-248 keeper-only retention directive
(rule 15) and superseded on the same year by
`2026-09-05-neiso-2022-touchpoint-k99`, **whose own sidecar declares
`"supersedes": "2026-08-06-neiso-2022-corrected-basis"`**.

`build_status.py:574` copies the block through **unvalidated**;
`calibration-status.js:406` renders it. So the card showed:

| Panel | Year | Determination | Run link | Source |
|---|---|---|---|---|
| Hand-authored `holdout_touchpoint` | 2022 | `CALIBRATED-WITH-CAVEATS` | `2026-08-06-neiso-2022-corrected-basis` | **absent from registry — dead link** |
| Derived `holdout_ladder` | 2022 | **`CALIBRATED`** | `2026-09-05-neiso-2022-touchpoint-k99` | live |

Same year, same ISO, same card, two different answers — and the one printed
*first* was the stale one.

The staleness was already worse than a dead link. The neiso-100 probe
(`results/calibration/_neiso100_touchpoint_staleness.json`) had measured the
pruned run's recipe as **diverging from the current keeper on 4 of 7 data axes**
(`campd`, `eia923`, `eia930`, `unit_outages`, `unit_outages_layup`), so the
block was not merely pointing at a pruned run — it was quoting a result taken
on a **different recipe** than the keeper it was rendered beneath.

### The derived ladder, which strictly dominates it

| Year | Tier | Determination | Run |
|---|---|---|---|
| 2020 | validation | `NOT-YET` (price_mean) | `2026-09-05-neiso-2020-2021-touchpoints` |
| 2021 | validation | `CALIBRATED` | `2026-09-05-neiso-2020-2021-touchpoints` |
| 2022 | validation | `CALIBRATED` (C3c ledgered, rubric v3.6) | `2026-09-05-neiso-2022-touchpoint-k99` |

Per-year rather than one run-level verdict, auto-derived from the registry so it
cannot drift, and every rung naming a live run. Rule 30(b) is explicit that this
is the only correct shape: *"never to hand-author a block that would go stale the
moment a rung is re-spent."*

**Repair:** delete the block (22 lines, no re-authoring), rerun
`build_status.py --iso NEISO`. Diff is 22 deletions in the shard and 1 line in
the status part — byte-for-byte the same shape as the PJM precedent.

---

## 3. Defect B — the detection gap, and why the obvious guard is WRONG

The handoff's charter was "assert every shard-referenced run id exists in the
registry." **A census shows that guard would red `main` immediately.**

Run ids in structured shard fields, checked against the registry:

| Field | ISO | Target | Kind |
|---|---|---|---|
| `holdout_touchpoint.run_id` | NEISO | **MISSING** | **live pointer — the defect** |
| `config_partition.configs[].source_run_id` ×2 | ERCOT | MISSING | historical provenance |
| `de_designation_history.former_keeper` / `.control_run` | NYISO | MISSING | historical genealogy |
| `superseded.prior_superseded.chain…former_keeper` ×10 | NYISO | MISSING | historical genealogy |
| `frontier_withdrawn_*.keeper_at_*` ×4 | NYISO | MISSING | historical genealogy |
| `keeper`, `config_partition.configs[].run_id`, `superseded.former_keeper` | all | present | live |

**18 of the 19 dangling ids are historical citations that are pruned BY DESIGN.**
Rule 15's keeper-only retention makes that the norm, and the shards say so in
terms — NEISO's own `site_retention_note`: *"Run-id citations … may now point at
runs no longer on the site — deliberately, on the owner's instruction. NOTHING IS
RETRACTED."* A guard over all of them would fight the retention discipline, and
"fix" it by re-attaching records the owner ordered detached.

### The line that actually matters

The defect is not "a citation dangles." It is **"the SITE RENDERS a dead
pointer."** So E12's scope is *derived from the render sites*, not hand-picked:
the fields `build_status.py` copies into `status/<ISO>.js` **and**
`calibration-status.js` turns into a `run-id-link` href.

```
LIVE_RUN_POINTERS = config_partition.configs[].run_id
                    holdout_touchpoint.run_id
                    standing_note.probe_run_id
```

`keeper` is deliberately excluded — **E1** already fails a keeper with no
sidecar, and duplicating it would double-report. Keeper genealogy and narrative
prose are out of scope permanently and on purpose.

A regression test pins the scope against `calibration-status.js` itself, so a
newly-rendered pointer added to the page without extending the tuple fails
loudly rather than silently re-opening the hole.

### Measured

| | pre-fix shards | post-fix shards |
|---|---|---|
| CAISO / ERCOT / MISO / NYISO / PJM | clean | clean |
| **NEISO** | **FAIL ×1** (`holdout_touchpoint.run_id`) | clean |

The guard fires on exactly the defect, on exactly one ISO, and on nothing else.

**Ordering is load-bearing:** E12 lands *after* the fix **in the same commit**,
because CI runs `audit_keepers --check` across every ISO and the guard would
otherwise red `main`.

---

## 4. Predictions scored against interest

Three claims that would have embarrassed this session had they been false, all
checked rather than assumed:

| Prediction | Result |
|---|---|
| The detection gap is genuine, not a re-check of something E1/E6/M1 already caught | **HELD.** `git show HEAD:scripts/audit_keepers.py \| grep -c holdout_touchpoint` → **0**. The auditor never read the field. |
| Only NEISO carries the pattern | **HELD.** All five other shards clean, pre- and post-fix. |
| A naive all-ids guard is safe to ship | **REFUTED** — and this is the session's main technical result. It would fail 18 deliberate historical citations across ERCOT and NYISO. Scope narrowed to the rendered set. |

---

## 5. What was NOT done, and why

* **No solve.** Rule 29 phase 0 answers the whole question at zero LP cost.
* **No verdict moved** in `mechanism-matrix/NEISO.js`. No mechanism was tested —
  this is a records repair. pjm-166/167 are the precedent: refuting an object or
  repairing records **appends evidence, moves no cell**.
* **No dashboard registration or prune** — no run was produced.
* **No prose citation repaired.** The shard's narrative fields deliberately name
  pruned runs and are explicitly not retracted (rule 15).
* **The 2022/2021/2020 touchpoints were NOT re-run.** They are spent and
  registered; re-spending them is exactly what rule 22 forbids.

---

## 6. Records changed

| File | Change |
|---|---|
| `frontend/data/backcast/keepers/NEISO.json` | `holdout_touchpoint` block DELETED (−22) |
| `frontend/data/backcast/status/NEISO.js` | rebuilt by `build_status.py --iso NEISO` |
| `frontend/data/backcast/calibration-complete.json` | `complete.NEISO.site_retention_2026_08_09` — dated append, **pure**: 0 keys added, 0 removed, 1 key changed |
| `scripts/audit_keepers.py` | **+E12** `dangling_pointer_findings`, wired into `audit()`, documented in the check registry |
| `tests/scoring/test_audit_keepers_pointers.py` | new — 9 tests, both scope halves + the render-site pin |

### The two stale claims closed in `calibration-complete.json`

1. *"the same keeper recipe on 2022"* — that run is itself now pruned and
   superseded.
2. *"a single combined 2022-2025 bundle … NOT yet done, blocked by the ACTIVE
   holdout spend freeze"* — **MOOT on both halves.** Rule 30(a)'s fold delivers
   exactly that reading with **no combined solve**; and the freeze has named
   `scope.tiers = ['locked_test']` alone since 2026-08-26, so it no longer
   refuses a validation-tier year.

The closure points at `frontend/data/backcast/status/NEISO.js` as the ladder's
home — *not* at `keepers/NEISO.json`. pjm-166's auditor pass wrote the latter and
needed a follow-up commit (`e7f990bd`) to correct it; the pointer is verified
here rather than repeated.

---

## 7. Verification

```
E12 pre-fix  : NEISO FAIL ×1, five ISOs clean
E12 post-fix : all six clean
audit_keepers --iso NEISO --check : PASS  0 failures / 0 warnings
audit_keepers --check (unscoped)  : PASS  0 failures / 0 warnings
pytest tests/scoring/test_audit_keepers_pointers.py : 9 passed
pytest (5 sibling audit_keepers/keeper_store files) : 53 passed, 2 subtests
check_registry_payload_parity.py : OK (14 runs, 47 bundle dirs)  exit 0
check_mechanism_matrix.py        : exit 0
blob verify scripts/audit_keepers.py : re-fetched from GitHub, 1109 lines,
    sha 5833ac0592d5d21eef32dba32f6fec8b58bf5cd9 == local (rule 27)
```

`holdout_touchpoint` is absent from both the shard and the status part; the
ladder is present with all three rungs; zero live references to the pruned run
id remain.

---

## 8. Open items for the next NEISO session

Unchanged by this session — it opened no lever and closed no calibration question.

* **No NEISO tuning lever is open.** The frontier is declared; the training
  window is done at zero failing criteria.
* **The 2020 rung reads `NOT-YET` on `price_mean`.** Under rule 30(c) this does
  **not** downgrade the ISO and is reported, not chased. Note P-5's PJM analogue:
  whether NEISO 2020's inputs are as prepared as 2021/2022's is *not* established
  here and would be a phase-0 question if anyone wants the rung to mean more.
* **`final` remains NEVER GRANTED for NEISO** and NOT YET on the merits —
  2019 is unsolvable at HEAD (Pilgrim absent from the 860 operable snapshot;
  no demand rows before 2021) and cannot discriminate on C3c.

**Next shorthand: `neiso-103`.**
