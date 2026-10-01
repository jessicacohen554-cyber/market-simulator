# FINDING — nyiso-162: the parked "leg2 winter-locational candidate" RE-VERIFIED against the live keeper — there is NO candidate, and the object that exists scores IDENTICALLY to the keeper on every criterion, every year

**Session:** nyiso-162, 2026-08-31. **Authority:** owner ruling **R-C**
(2026-08-31 director sitting): *re-verify the parked leg2 winter-locational
candidate against the LIVE keeper before any promote-or-archive is served —
nothing promotes on a stale comparison.* **Lane discipline:** zero-solve,
committed artifacts only (the Card-3 standing-rule pattern,
`docs/calibration-log/governance.md` 2026-08-30). **This lane rules nothing
and moves no keeper, shard, marker or matrix cell.**

**Live keeper at HEAD:** `2026-08-30-nyiso-159-loss-surface` (bundle
`results/calibration/nyiso159_lossarm_B`), determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}; `audit_keepers.py --iso NYISO` **PASS 0 failures /
0 warnings** at this head.

---

## §1 — What the leg2 session actually produced: no candidate exists

The named session is **nyiso-160**, branch
`claude/nyiso-leg2-winter-locational-wymoa4`, merged as **#4385** (records:
`results/calibration/FINDING-nyiso160-leg2-stop-and-tpaudit-2026-08-30.md` +
`scripts/probes/_nyiso160_tpaudit.py`) and **#4393** (registration + bundle +
log entry). Both PRs are merged; **the remote branch is deleted and no commit
from it is unmerged** (`git fetch origin claude/nyiso-leg2-winter-locational-wymoa4`
→ `couldn't find remote ref`; both merge commits `b5050e9`/`e65bbba` are on
`main`). There is no third PR and no stranded work.

**Leg 2 (the MyNYISO AORR intake) STOPPED WITH CAUSE AT ACCESS** — the
artifacts `INTAKE-SPEC-nyiso156-winter-locational-2026-08-30` §2 requires
never landed in `data/raw`, and the owner, asked in-session, answered
*"Cannot produce them."* The stop happened **at Step 1, before any mechanism
was designed**. Consequently the session produced:

* **no pre-registration** — no `PREREG-nyiso160-*` exists;
* **no armed mechanism** — no `ScenarioConfig` field, no `--set`, no derive;
* **no A/B pair and no control run** — the registry holds no
  `2026-08-30-nyiso-160-*-control`; the run is not an arm, so it has no
  control to be compared against;
* **no winter-locational lever of any kind** — nyiso-158 §1.4 had already
  measured that no admissible driver reaches the winter face, and the
  nyiso-97 §5 re-open bar (binding through the spec) forbids inferring the
  requirement from conduct, BPCG uplift, LBMP or the residual.

**The session's sole registered run is `2026-08-30-nyiso-160-tpaudit-replay`**
(bundle `results/calibration/nyiso160_tpaudit_replay`) — the handoff's
designated fallback: a **zero-delta replay of the keeper's own recipe at
HEAD**, registered under rule 15 as an audit probe. Its own records already
declare it *"NEVER a keeper candidate — it is the keeper itself, re-established
at HEAD"* (finding §4; log entry (3)).

**So the object the ruling calls "the parked leg2 winter-locational candidate"
does not exist as a candidate.** What is parked is a disposition question about
an **audit-probe registration**, not a promotion question about a mechanism.
This finding re-verifies that object against the live keeper anyway, exactly as
ordered, and reports the result at full magnitude.

## §2 — The mechanism / config delta the run carries

**Against its own control: none — there is no control, because there is no
arm.** Against the live keeper (the only meaningful baseline), the delta is
**zero solve-affecting levers**, independently re-derived here rather than
taken from the prior session's prose.

Method: recursive flatten of both bundles' `run_config.json` to leaf scalars
(978 leaves keeper / 981 candidate), volatile provenance keys excluded by name
at every path segment.

| class of difference | count | what |
|---|---|---|
| leaves only in the **keeper** | **0** | — |
| leaves only in the **candidate** | **3** | `entry_forward_reserve_leg` = `False`; `ercot_offer_surface_cleared_share_rt_room` = `False`; `ercot_offer_surface_cleared_share_rt_room_path` = `None` |
| shared leaves with differing values | **7** | 4 × environment package version; `git.branch`; `git.sha`; `model_changes_note` (the run's own description string) |
| **solve-affecting levers differing** | **0** | — |

All three candidate-only leaves are `ScenarioConfig` fields **registered after
the keeper's recipe was recorded**, present at their registered defaults
(`scenarios.py:9227`, `:9230`, `:4260`; default map `:1505`, `:1506`, `:1551`)
— rule-24 surface widening, and all three are ERCOT/entry-side fields with no
NYISO reach. **Two corrections to the nyiso-160 record, both immaterial to its
verdict:** (a) it named **two** such keys; there are **three** — it omitted
`ercot_offer_surface_cleared_share_rt_room_path`; (b) it reported the levers as
the only difference, but the two bundles also solved on **different package
versions**, including **HiGHS 1.15.1 (keeper) vs 1.14.0 (replay)**, plus
pandas 3.0.5/3.0.3, pyarrow 25.0.1/24.0.0, pydantic 2.13.5/2.13.4. That is
*strengthening* evidence, not drift: the value-identity in §3 held **across a
solver-version change**.

## §3 — The re-verification against the LIVE keeper (this lane's own work, zero solve)

Four independent legs. **No LP solve of any year; no `data/raw` hydration
beyond the `code` profile; the holdout freeze is untouched and every year read
is in-training {2023, 2024, 2025}.**

**R1 — scorecard, `calibration_verdict.py --json` on both runs (committed
artifacts only, rubric v3.5).** 60 scored records each (8 criteria × class ×
year). Diffed record-by-record on `status`, `model`, `actual`, `magnitude`,
`classification`, `share_pp`:

> **ZERO record-level differences.** The single difference anywhere in either
> scorecard is the **C6 governance attestation narrative string** — the prose
> describing what the run was. No status, no number, no classification, no
> band, no tier differs. `reasons`, `caveats`, `ledger_entries`,
> `grade_summary`, `free_class_score`, `scorable_years` and
> `data_blocked_years` are identical objects.

**R2 — recipe.** §2 above: 0 differing levers.

**R3 — hourly sidecars, recomputed from the committed parquets.** Every value
column of every sidecar, all three years — `system` (price / slack / dump /
demand / reserve_price), `class_hourly` (mw), `reserve_family` (dual /
requirement_mw / held_mw / shortfall_mw), `storage` (charge_mw / discharge_mw):

> **max |Δ| = 0 (exactly zero) over 1,043,280 data rows**, and every
> non-numeric label column matches element-wise.
>
> *Method note.* The parquet **files** are **not** byte-identical (identical
> byte lengths, differing hashes — consistent with the differing pyarrow
> writer-version string embedded in the footer), so a hash comparison would
> have been inconclusive in the wrong direction. The identity claim here rests
> on the **decoded value comparison**, which is the load-bearing test.

**R4 — `metrics.json`.** 60 leaves each; **58 identical**; the 2 differing are
`run_id` and `label` — the run's own identity strings.

## §4 — The ruling's premise, checked: the comparison was never stale

R-C's stated trigger is that *"NYISO has since promoted 157 →
2026-08-30-nyiso-159-loss-surface, so the candidate's comparison baseline is
superseded."* **On the artifact record that trigger does not hold for this
session.** The 157 → 159 promotion happened at **nyiso-159**, the session
*before* leg2; nyiso-160 opened with `2026-08-30-nyiso-159-loss-surface`
already designated and audited **against 159 throughout** (its own finding
header: *"Keeper under audit: 2026-08-30-nyiso-159-loss-surface"*). The keeper
has not moved since — the shard, `status/NYISO.js` and `audit_keepers` all
read 159 at this head, and the only NYISO session after leg2 (nyiso-161, the
winter-face waiver decision card, #4420) is records-only and explicitly
promotes nothing.

Recording this is part of executing the ruling, not a challenge to it: the
ruling is executed in full, and it returns a **null candidate on a baseline
that was already current**. The re-verification stands on its own regardless —
§3 is a fresh, independent measurement at today's head.

## §5 — THE VERDICT: neither improvement nor regression — exact equality

**Does the candidate improve on 159's scorecard, worsen it, or read mixed?
NONE OF THE THREE. It is numerically identical**, criterion by criterion, year
by year, at full magnitude:

| criterion | tier | keeper `nyiso-159-loss-surface` | candidate `nyiso-160-tpaudit-replay` | Δ |
|---|---|---|---|---|
| **C1** fuel-mix by class | load-bearing | **PASS** — all 14/14 · free 10/10 | **PASS** — all 14/14 · free 10/10 | **0** |
| **C2** system volume | load-bearing | **PASS** — gas family in band 2023/2024; gas-2025 −1.0 % (SKIPPED, preliminary vintage diagnostic, v2.5); coal SKIPPED ×3 (immaterial) | identical | **0** |
| **C3a** mean LMP | load-bearing | **FAIL** — 2023 **+2.3 %** · 2024 **−1.2 %** · 2025 **−11.5 %** (band ±10 %) | 2023 +2.3 % · 2024 −1.2 % · 2025 −11.5 % | **0.00 pp ×3** |
| **C3b** price duration / shape | load-bearing | **PASS** — NRMSE 0.114 / 0.174 / 0.198 | 0.114 / 0.174 / 0.198 | **0** |
| **C3c** price tail / scarcity (RT) | supporting | **FAIL** — 1 h / 0 h / 1 h vs actual 10 / 13 / 42 h > $300 | 1 / 0 / 1 vs 10 / 13 / 42 | **0 h ×3** |
| **C4** dispatch correlation | supporting | **PASS** — gas r 0.938 / 0.904 / 0.842 | identical | **0** |
| **C6** governance gate | protective | **PASS** | **PASS** | **0** *(attestation prose differs)* |
| **C8** forced-energy share (D-2) | protective | **PASS** | **PASS** | **0** |
| **determination** | — | **NOT-YET** {C3a-2025, C3c} | **NOT-YET** {C3a-2025, C3c} | **unchanged** |
| grade summary | — | scored 8 · target-grade 6 · ledgered 0 · fails 2 | identical | **0** |
| *(reported-only)* C5a CO2 | — | +2.7 / +0.9 / +4.6 % | identical | **0** |

**The equality is structural, not coincidental.** The candidate cannot improve
or worsen the keeper's scorecard **because it is the keeper's own recipe and
the keeper's own dispatch**, re-established at HEAD: 0 levers differ (§2) and
max |Δ| = 0 on every hourly value (§3). Its C3c is **not lone** here (C3a-2025
also fails), so the rule-22 standing rule stays silent on both records — as it
does on the keeper.

**What the re-verified record therefore supports, stated for the owner's
decision and not decided here:**

* **Promotion would be a formal no-op** — same config, same dispatch, same
  determination — and would replace the keeper designation's evidentiary
  basis (the nyiso-159 A/B against `2026-08-30-nyiso-159-loss-control`, with
  its prereg, gates JSON and promotion note) with an audit replay that has no
  control and tests no mechanism. Nothing is gained and the promotion basis is
  weakened.
* **Archiving costs nothing evidentially** — the touchpoint-prep verdict is
  durable in `results/calibration/_nyiso160_tpaudit.json`, the nyiso-160
  finding, the log entry and this finding, none of which depend on the run
  staying registered.
* The genuine open choice is therefore **dashboard retention**, not promotion:
  the run post-dates the keeper and was not "rejected wholesale", so the
  2026-08-15 site-retention directive does not itself dispose of it either
  way. **Owner's call.**

## §6 — Matrix, and what this session did NOT do

**No mechanism-matrix cell moves.** Rule 26 duty (b) is not triggered: this
re-score adjudicates no mechanism's verdict, because the object carries no
mechanism (§1–§2). `scuc_load_pocket_commitment` stays **G** and already
carries the nyiso-160 access-stop on its evidence line; the §5.5 queue
annotation is current. Duty (c) is not triggered — no `ScenarioConfig` field
is added.

Not done, deliberately: **no LP solve of any year**; no keeper, shard, marker,
frontier or determination change; no holdout year touched and no freeze
interaction (all three years read are in-training); nothing armed, disarmed,
re-scoped or re-tuned; no derive re-run (rule 23); no other ISO's files touched
(rule 25); no promote-or-archive act — **that decision stays with the owner on
this re-verified record.**

## §7 — Reproduction

```
python3 scripts/calibration_verdict.py --run-id 2026-08-30-nyiso-159-loss-surface  --json
python3 scripts/calibration_verdict.py --run-id 2026-08-30-nyiso-160-tpaudit-replay --json
python3 scripts/audit_keepers.py --iso NYISO
```

then diff the two scorecards record-by-record, flatten-diff the two bundles'
`run_config.json` with volatile provenance excluded, and decode-compare every
value column of `results/calibration/{nyiso159_lossarm_B,nyiso160_tpaudit_replay}/hourly/*.parquet`.
All four legs are stdlib/pyarrow reads of committed artifacts; none re-solves.
