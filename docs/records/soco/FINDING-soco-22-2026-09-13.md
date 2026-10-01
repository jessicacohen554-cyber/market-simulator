# FINDING — SOCO-22: the no-price determination class landed as rubric v3.8. **All seven keepers re-score byte-identically; SOCO and NWPP now read `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, never `CALIBRATED`.**

**Lane** SOCO-22 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/soco-22-rubric-determination-cnoxsz` · **Base** `33a7c961` (origin/main, pinned) ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-22-2026-09-13.md`, pushed at `8799e585` before the scorer was
edited · **Rulings** SOCO card S2 (desk r#2) and S11 (desk r#3), 2026-09-13; NWPP card N2 (both limbs) ·
**Data profile** `code` · **No LP ran.** Scorer-side only; no shard, nothing to archive, no bundle written.

## 0. The seven-keeper byte-identity proof, first

Every registered run (14: the 7 designated keepers plus 7 folded/superseded runs) was scored at `33a7c961`
before any edit and again after, on the full span and on each scorable year alone (`--years <y>`), with
`json.dumps(sort_keys=True, indent=2)` and `render_text` written to disk and diffed.

| ISO | keeper | before | after | JSON diff lines | text diff lines |
|---|---|---|---|---:|---:|
| CAISO | `2026-09-12-caiso-275-gascoupling` | CALIBRATED | CALIBRATED | 2 | 0 |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | CALIBRATED | CALIBRATED | 2 | 0 |
| MISO | `2026-09-12-miso-255-sil-measured` | NOT-YET | NOT-YET | 2 | 0 |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | CALIBRATED | CALIBRATED | 2 | 0 |
| NYISO | `2026-09-13-nyiso231-anchor-span` | NOT-YET | NOT-YET | 2 | 0 |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | CALIBRATED | CALIBRATED | 2 | 0 |
| SPP | `2026-09-13-spp-38-vintage-cache` | CALIBRATED | CALIBRATED | 2 | 0 |

The two JSON diff lines on every file are `"rubric_version": 3.7` → `3.8` and nothing else. Over all
54 verdict files (14 full-span + 40 per-year) the union of differing lines is exactly those two strings,
54 times each; all 14 `render_text` blocks are identical byte for byte. **Every category, row, status,
classification, magnitude and reason string is unchanged for every registered run.** The version field
moves because this is a rubric change (a new determination class), and the PRECOMMIT §5 declared it as
the one permitted diff before the change was made.

## 1. The final determination strings

```
PHYSICALLY-CALIBRATED (PRICE UNSCORED)                — clean rung
PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)   — caveat rung
NOT-YET                                               — unchanged, every failing route
```

**Why not the ruling's example `PHYSICALLY CALIBRATED — price unscored, no public price exists`.** The
scorer observes one fact: no committed benchmark exists for the region. It cannot know why. For SOCO the
why is "no public price exists" (plan §2.6; SOCO-12 §0.2 disqualifies the SEEM auditor's series on four
grounds). For NWPP it is the opposite — two public prices exist (WEIM, Mid-C) and both were refused as
benchmarks by NWPP-13's pre-registered STOP gate. A label asserting "no public price exists" would be
**false on the second region this amendment serves**. So the label states the observable fact,
`(PRICE UNSCORED)`; the determination-basis line names the ISO and the file; the plans and FINDINGs carry
the why. `PHYSICALLY-CALIBRATED` is the owner's own word and is accurate: what remains scored is C1 fuel
mix, C2 system volume, C4 hourly dispatch correlation, and the two protective gates C6/C8.

**Why two rungs.** A single label would read the same for a run carrying a C2 commercial-band caveat, an
unscored C8, or a data-blocked year as for a clean one — information the ordinary ladder carries. On the
criteria it does score, this class is exactly as strict as the ordinary one; the only thing it changes is
that the unscored price criteria no longer collapse the reading to a `CALIBRATED-WITH-CAVEATS` that
implies price was calibrated.

**Hyphenated tokens** follow the `CALIBRATED-WITH-CAVEATS` / `NOT-YET` grammar so `audit_keepers`'s
token scanner extends by two tokens (§6).

## 2. What the SOCO-shaped run reads — the determination basis at full magnitude

On the clean rung the basis has one line, which is therefore the headline:

> `PRICE UNSCORED — no actual_lmp.json block exists for SOCO, so C3a mean LMP, C3b price duration/shape
> and C3c price tail / scarcity (RT hourly) are NOT SCORED in any year (2024); this determination is
> scored on C1/C2/C4/C6/C8 ONLY and certifies NO price level, shape or tail (owner ruling card S2,
> 2026-09-13; rubric v3.8). It is not a CALIBRATED reading. Model system load-weighted mean LMP,
> MODEL-ONLY and UNVERIFIED — no measured reference exists to compare against: 2024: $29.00/MWh.`

The model's own annual mean price is printed so the unscored quantity is visible at full size, labelled
so it cannot pass for a scored number. **The line is appended last on every route — `NOT-YET` included** —
so a failing no-price run is never read as having failed on price, and it never displaces a downgrading
reason from the headline. The verdict carries a `price_unscored` block (`basis`, `criteria_unscored`,
`scored_on`, `model_mean_lmp_by_year`) **only on this class** — the `span_restricted` pattern — which is
what keeps every other run's verdict byte-identical; `render_text` and `condensed_metrics` print it when
present.

Measured on the synthetic clean fixture, every route of PRECOMMIT §3's table reads as declared:

| fixture | reading |
|---|---|
| SOCO, no `avgLMP`, C1/C2/C4/C8 clean, C6 attested | `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` |
| NWPP, same | `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` |
| SOCO with a C1 FAIL | `NOT-YET` — FAIL line first, price line last |
| SOCO unattested | `NOT-YET` — governance line first, price line last |
| SOCO with a data-blocked target year | `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)` |
| SOCO with no C8 artifact | `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)` — "unscored PROTECTIVE criteria: forced_share" |
| PJM, no `avgLMP` (block present) | `CALIBRATED-WITH-CAVEATS`, "unscored criteria: price_mean, price_shape" — today's reading, unchanged |
| PJM, `avgLMP` present | `CALIBRATED` |
| SOCO, `avgLMP` hand-built into the bench | `CALIBRATED` — leg (ii) refuses the branch |

## 3. The predicate, and what it does for ABSENT / REJECTED / PARTIAL

`_price_reference_absent(iso)` is True iff the committed `data/raw/_validation-source/actual_lmp.json`
has no top-level key for the ISO. The branch fires iff that holds **and** C3a, C3b, C3c are all `SKIPPED`
at the per-criterion level. No ISO name appears in it.

| region state | block? | branch? | reading |
|---|---|---|---|
| **ABSENT** (SOCO) | no | yes | the new class |
| **REJECTED** (NWPP: series built, gate D3 NO every year, `gate --land` refused) | no | yes | the new class — NWPP-13 §4 option (i), that lane's own recommendation for the first keeper |
| **PARTIAL** (MISO 2020/2021: block present, years missing) | yes | no | ordinary rubric, unchanged: per-criterion aggregation lets scored years carry the criterion; missing years are `price_reference_blocked_years` |

A rejected series never lands, so **absence is the rejection signal** and no flag was invented. If the
NWPP desk later rules a labelled series in (N2 option (ii)), the block appears and the ordinary rubric
takes over with no code change. Two fail-closed guards: an unreadable or non-dict reference returns
False (the run reads as before), and a scored price criterion can never be overridden (a lone scored C3c
is enough to refuse the branch — tested).

## 4. Scope fence — what was NOT touched

No criterion's tier, band or threshold; neither caveat budget; `LEDGERABLE_CRITERIA`; `_apply_ledger`;
the rule 22 `[R-C3C]` standing rule; `_no_price_reason`; `price_reference_blocked_years`; the cod_ramp
seam; any keeper shard, log, matrix shard, registry sidecar or payload; the plan; the ledger. The only
existing lines that changed in `determine_from_artifacts` are the two label assignments
(`determination = CALIBRATED` → `clean_label`, `CALIBRATED_CAVEATS` → `caveat_label`), which resolve to
the old constants whenever the predicate is False — §0 is the proof.

## 5. Tests and the lane

New file `tests/scoring/test_calibration_verdict_price_unscored.py`: **34 tests, 39 subtests, all pass**
(predicate on all seven registered ISOs / SOCO / NWPP / None / unreadable / non-dict / empty-block;
reached; basis-line content; NWPP; render + condensed; never-CALIBRATED; NOT-YET on FAIL and on
unattested C6; both caveat rungs; unreachable with a block whether price scored or not; unreachable by
leg (ii) on a hand-built bench and on a lone scored C3c; every registered run carries no block and none
of the new labels — the durable form of §0).

`tests/scoring/` full lane, this container (`code` profile): **before 19 failed / 1470 passed, after
19 failed / 1504 passed** (+34 = the new file). The 19 failing test ids are **identical before and after**
(diff of the two lists: 0 lines) and are pre-existing at `33a7c961` — 18 are profile/bundle-dependent
(`test_ff_readiness_battery`, `test_forecast_parity`, `test_golden_manifest_provenance`,
`test_replay_keeper_strict`, `test_audit_keepers_lineage`, `test_backcast_artifacts`,
`test_gate_a_provenance`) and one is `test_calibration_verdict.py::test_coverage_threshold_sits_in_an_empty_interval`,
which fails because a committed `actual_lmp.json` coverage value of **0.9677** now sits inside the interval
(0.3653, 0.9911) that test declares empty — a data-intake consequence for whichever lane landed it, named
here and not this lane's. `ruff check` and `ruff format --check` pass on both touched files.

**One deviation from PRECOMMIT §6, stated:** the caveat-rung test uses the data-blocked-year and
unscored-C8 routes rather than a C2 commercial-band miss. The rung's mechanics are route-independent
(the same `caveat_label` assignment), and both routes are cheaper to construct exactly; no other item
of §6 changed.

## 6. Routed — outside this lane's files, owed before the first no-price keeper registers

1. **`docs/calibration-determination-rubric.md`** needs a v3.8 entry. Paste-ready paragraph:
   > **v3.8 (owner ruling 2026-09-13, SOCO cards S2/S11; lane SOCO-22).** A region with **no committed
   > price benchmark** — no `actual_lmp.json` block — reads `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` or
   > `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)` in place of `CALIBRATED` /
   > `CALIBRATED-WITH-CAVEATS`; it never reads `CALIBRATED`. Scored on C1/C2/C4/C6/C8 only; C3a/C3b/C3c
   > are named together on the determination basis with the model's own mean LMP reported model-only, on
   > every route including `NOT-YET`. Keyed on the absence of the block, never on an ISO name; a region
   > with a block, however partial, takes the ordinary rubric. Fails closed on an unreadable reference and
   > on any scored price criterion. Every existing keeper re-scores byte-identically.
2. **`scripts/audit_keepers.py::_DET_TOKENS`** — add `"PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE
   UNSCORED)"` and `"PHYSICALLY-CALIBRATED (PRICE UNSCORED)"` ahead of the existing three (longest-first),
   or E5 will read a no-price keeper's definition as its `CALIBRATED` substring and fail it.
3. **`docs/codebase-site/js/calibration-status.js::detClass/detLabel`** — an unknown label renders
   `NOT CALIBRATED` (red) and the caveat rung renders `WITH CAVEATS` (its label contains "CAVEAT").
   Conservative until taught; SOCO's W2/W4 registration lane owns the two functions.
4. **`_MULTI_YEAR_ISOS`** gains `SOCO` in W2 (plan §3 defaults) — unrelated to this lane, noted so W2
   does not look for it here.

## 7. Rules

- Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]` / gate G17: no proxy, no neighbouring hub, no substitute
  series — the class exists so that the absence of a benchmark is **named**, not papered over.
- Rule 22 `[R-C3C]`: untouched; on this class C3c leaves the v3.7 exempt line because it is unscored for
  the same reason as C3a/C3b, and that is said in the code and on the basis line.
- Rule 24 `[R-REGISTRY]` / 25 `[R-ISO-SCOPE]`: no ISO name in the scorer; the predicate is the
  committed reference, so it serves SOCO and NWPP with one amendment (S11's stated reason).
- Rule 26 `[R-DELETE]`: nothing deprecated; nothing zeroed.
- Rule 27 `[R-PUSH]`: `scripts/calibration_verdict.py` (4,024 lines) was edited locally and pushed as
  the on-disk bytes over `git push`; the pushed blob is verified against the local sha256 in the commit
  that follows this doc (recorded in the lane's final report).
- Rule 28 `[R-MECH-MATRIX]`: no `ScenarioConfig` field, no mechanism, no CLI flag added — the guard's
  duties (b)/(c) are vacuous.
- Rule 31 `[R-RETAIN]` / 32 `[R-SHARD]` / 33 / 34: no solve, no bundle, no shard — nothing to retain,
  archive or delete.

## Log entry

## 2026-09-13 — SOCO-22: rubric v3.8, the no-price determination class (W1, zero-LP)

`scripts/calibration_verdict.py` gains one determination branch keyed on the absence of an
`actual_lmp.json` block: `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` / `-WITH-CAVEATS`, never
`CALIBRATED`, scored on C1/C2/C4/C6/C8, price gap on the basis at full magnitude on every route.
All 14 registered runs (7 keepers) re-score byte-identically on the full span and per year (only
`rubric_version` 3.7 → 3.8 moves). 34 new tests. Serves NWPP card N2 limb (b) with the same amendment.
Routed: rubric doc entry, `audit_keepers._DET_TOKENS`, `calibration-status.js` label map.
