# FINDING — capx-D20: reconstructed `run_config` provenance — the label, the cap, the seven keys

**Lane:** capx-D20 (director r#22 ruling §0s.5, `docs/handoffs/capx-director-ledger-2026-08.md`
— the ruling this lane *executes*, not re-decides)
· **Branch:** `claude/capx-d20-reconstruction-provenance-7amx23`
· **Base:** `origin/main` @ `663605c5` · **Date:** 2026-09-01 · **Zero solves.**

## §0 Headline — the standing rule, made executable

**A reconstruction can reach CAVEAT, never PASS.** The seven legacy legs' `run_config`
artifacts are post-hoc RECONSTRUCTIONS (capx-D8 §4), not artifacts the solve wrote.
Adoption-as-original was REFUSED at r#22 §0s.5 because it would flip seven committed FC-7
`run_config` rows FAIL → PASS and thereby assert exactly the provenance FC-7 exists to
measure. This lane lands the admissible route instead:

1. **The label** — all seven debt bundles carry an explicit top-level
   `provenance: "reconstruction"` on both `run_config.json` and `dof_ledger.json`.
   One inserted line per file; **every other byte untouched**; no reconstruction upgraded,
   re-derived, or adopted.
2. **The scorer** — `scripts/forecast_verdict.py` recognises the label and caps the FC-7
   provenance rows at **CAVEAT with a named reason**, never PASS.
3. **The re-emission** — exactly seven `ff-verdicts.json` keys, control-first.

**Movement, all seven, identically: FC-7 category FAIL → CAVEAT; DETERMINATION UNCHANGED
(HOLD → HOLD, every leg).** No key outside the seven moved. No criterion other than FC-7
moved on the seven. **No STOP condition fired.**

The only route to a clean FC-7 on these legs is a **genuine re-run**. That is a charter
decision and is **not** this lane's — see §6.

## §1 The control — and the one thing it could NOT cover, stated up front

**FC-7 control, run BEFORE any edit: all seven committed FC-7 blocks reproduce
BYTE-FOR-BYTE** under the *unmodified* scorer (status, detail, `gating`, row order, and the
aggregated category status — compared as canonicalised JSON):

| key | tier | committed FC-7 reproduced by the unmodified scorer |
|---|---|---|
| `miso-2021-2025-realized-ffr3a3-t1h` | t1h | **byte-exact** |
| `neiso-2021-2025-realized-ffr3a3-t1h` | t1h | **byte-exact** |
| `nyiso-2021-2025-realized-ffr3a3-t1h` | t1h | **byte-exact** |
| `pjm-2021-2025-realized-ffr3a3-t1h` | t1h | **byte-exact** |
| `ercot-2023-2027-crossover-ffr3a3-t1x` | t1x | **byte-exact** |
| `pjm-2023-2027-crossover-ffr3a3-t1x` | t1x | **byte-exact** |
| `miso-2023-2027-crossover-ffr3a4-t1x` | t1x | **byte-exact** |

Re-run *after* the scorer change with the label absent: still byte-exact on all seven — the
change is **strictly additive**.

**What the control could not cover, and why the whole record was therefore NOT re-scored.**
The charter asks for the seven committed records reproduced whole. **That is not possible
and the reason is a records fact, not a shortcut:** the FFR-3A-3 / FFR-3A-4 bundles were
never committed (`results/ffr3a3`, `results/ffr3a4` are gitignored by design; only their
README + scorecard are tracked), so `results/hindcast/<leg>/` holds **zero tracked files**
for all seven, and no `score.json` / `crossover_score.json` exists. Measured, not asserted:
an artifact-free whole-record re-score moves `miso-…-t1h` **FC-3 FAIL → SKIPPED** and
`miso-…-t1x` **FC-4 FAIL → SKIPPED** — it would silently erase the legs' *measured* skill
failures.

So this lane **splices**: FC-7 is re-derived by the scorer from the labelled reconstruction;
**every other category is carried VERBATIM** from the committed record; and
`determination` / `reasons` / `caveats` are recomputed by the scorer's own `_determine` over
the spliced category map. **No value written here is hand-authored.** The splice also makes
the charter's STOP condition "no criterion other than FC-7 moves" true *by construction*,
and it is asserted category-by-category anyway (§4).

## §2 The label (leg 1)

`results/run-config-debt/<leg>/{run_config.json,dof_ledger.json}` — 14 files, **+1 line
each**, inserted textually after the opening brace so the remaining bytes are unmoved
(asserted: `text[2:] == new_text[2 + len(line):]`, and the re-parsed document minus the new
key is JSON-identical to the original).

```
 "provenance": "reconstruction",
```

The ledgers are labelled too: a fully-identified DOF ledger read off an artifact the solve
never wrote cannot certify identification either. Without that half, a future lane passing
`results/run-config-debt/<leg>/dof_ledger.json` would have drawn a **PASS off a
reconstruction** — the precise failure the ruling refused. Closing it costs one branch.

The label is **asserted, never inferred**: the pre-existing prose block
(`reconstruction.status = "RECONSTRUCTED — NOT ORIGINAL"`) does **not** trip the cap, and is
unit-tested not to (§5).

## §3 The scorer (leg 2) — `scripts/forecast_verdict.py`

* `RECONSTRUCTION_PROVENANCE = "reconstruction"` and `RECONSTRUCTION_REASONS` (per-row named
  reasons), beside the other FC-7 structural constants.
* `_is_reconstruction(artifact)` — reads the artifact's top-level `provenance` **string**.
  Total: a `forecast-provenance/v1` **stamp dict** under the same key is *not* a
  reconstruction claim and never trips it; any other shape reads `False`.
* `_cap_reconstruction(row, artifact)` — **a ceiling, not a floor.** PASS → CAVEAT; a row
  that already FAILs a real check (no mode, wrong mode, malformed ledger) **keeps its FAIL**;
  every capped row is prefixed with its named reason so the reason travels onto the board.
  An unlabelled artifact is returned untouched.
* Applied at **FC-7 row 1** (`rows[-1] = _cap_reconstruction(rows[-1], rc)`, after whichever
  branch produced the row, so the cap cannot be routed around) and at **FC-7 row 3**
  (`_score_dof_ledger` now resolves the ledger, delegates scoring to `_dof_ledger_row`, and
  caps the result).

**Absence is still FAIL.** The cap never softens `run_config.json absent` into a caveat —
pinned by test, because that is what every pre-D20 committed record reads.

## §4 The re-emission (leg 3) — per-leg before/after

All seven are identical row-for-row apart from the config-key counts (674, or 678 for the
MISO FFR-3A-4 leg) and the ledger entry counts (1, or 2 for the same leg):

| FC-7 row | BEFORE (committed) | AFTER (this lane) |
|---|---|---|
| `run_config` | **FAIL** — `run_config.json absent` | **CAVEAT** — `run_config is a post-hoc reconstruction — mode=forecast; 674 config keys; gates ['capacity_market_clearing']` |
| `overlay-off` | *(row did not exist — no run_config to check)* | **PASS** — `no backcast overlay armed (outage_source='statistical')` |
| `dof ledger` | CAVEAT — `DOF ledger absent (identification unproven)` | **CAVEAT** *(status unchanged)* — `DOF ledger is derived from a post-hoc reconstruction — 1 entries well-formed (0 open residual DOF listed)` |
| **FC-7 category** | **FAIL** | **CAVEAT** |

Determination movement, all seven:

| key | determination | reasons | caveats |
|---|---|---|---|
| `miso-2021-2025-realized-ffr3a3-t1h` | HOLD → **HOLD** | drops `FC-7 … FAIL`; keeps `FC-3 … FAIL` | `[]` → `['FC-7 provenance & DOF']` |
| `neiso-2021-2025-realized-ffr3a3-t1h` | HOLD → **HOLD** | same | same |
| `nyiso-2021-2025-realized-ffr3a3-t1h` | HOLD → **HOLD** | same | same |
| `pjm-2021-2025-realized-ffr3a3-t1h` | HOLD → **HOLD** | same | same |
| `ercot-2023-2027-crossover-ffr3a3-t1x` | HOLD → **HOLD** | drops `FC-7 … FAIL`; keeps `FC-1 SKIPPED (required, unscored)` + `FC-4 … FAIL` | `[]` → `['FC-7 provenance & DOF']` |
| `pjm-2023-2027-crossover-ffr3a3-t1x` | HOLD → **HOLD** | same | same |
| `miso-2023-2027-crossover-ffr3a4-t1x` | HOLD → **HOLD** | same | same |

That is **exactly the label route's own direction** — a FAIL-for-missing-provenance becoming
a CAVEAT-for-reconstruction — and nothing else. The FC-7 FAIL was never load-bearing for any
of these determinations: each leg is held by its own FC-3, or FC-1 + FC-4.

**Asserted programmatically against `HEAD` before commit** (all PASS, no STOP fired):

* the board's **key set and key ORDER** are unchanged; **exactly the seven** keys differ;
* on each of the seven, **every non-FC-7 category is byte-identical**, as are `schema`,
  `rubric_version`, `tier`, `iso`;
* each key's **`cache_epoch`, `solved_at_sha`, `session` and `note` are PRESERVED verbatim**
  (only `scored_at_sha` / `scored_at_date` carry this re-emission: `663605c58e0a` @
  `2026-09-01T17:36:52Z`). The reconstruction carries no `cache_key` under that name, so a
  blind re-stamp would have **nulled a recorded epoch** — the epoch that matters is the one
  the run solved under;
* every committed `notes` entry is preserved as a **prefix** (the D5-R co2-instrument notes
  included), with one appended capx-D20 lane note per key;
* the file is written in its canonical on-disk format (`indent=1`, **key order preserved**,
  not `sort_keys`), verified against HEAD, so the diff is the seven entries alone.

### §4.1 Board seed (`program-status.json`) — two annotations + one lane block

Records only; **no gate cell, no `fc` map, no ISO determination, no keeper/marker/golden
field** (asserted field-by-field against HEAD, plus a whole-document identity assertion with
the three edits stripped back out).

1. `isos.MISO.t1x_provenance` said *"Determination HOLD on FC-4 FAIL + FC-7 FAIL"* — the
   FC-7 half is now stale. Bracketed annotation added; FC-4 and the determination are
   untouched and named as such.
2. `d8_re_emission.routed_to_director[3]` (the routed item) annotated **DISCHARGED — but not
   as written**: the FAIL → PASS flip it describes was refused; FAIL → CAVEAT landed.
3. New `d20_reconstruction_provenance` block (the established
   `what_changed` / `what_did_NOT_change` convention) + one `sources` line.

The three `gate.c_crossover_gap` cells cite three of the seven keys, but on **FC-4
measurement** ("passes on measurement, not on the verdict"). FC-4 is untouched, so **no gate
moved**. The D5-R disposition — *"NOT re-emitted — their bundles were never committed"* —
still stands for FC-4 and is deliberately left as written.

## §5 Tests

`tests/scoring/test_forecast_verdict.py` — two new classes, 8 tests + 7 subtests, all
passing:

* a labelled `run_config` that would otherwise PASS reads **CAVEAT** with the named reason,
  and its FC-7 category can never read PASS; same for a labelled DOF ledger;
* **ceiling-not-floor**: a labelled config with the wrong `mode`, and a labelled ledger with
  a root-cause-less residual, both keep their **FAIL**;
* **absence is still FAIL** (`run_config.json absent`, detail asserted verbatim);
* **strictly additive**: unlabelled artifacts score exactly as before and gain no detail
  prefix (the cross-lane re-grade rule, pinned);
* a `forecast-provenance/v1` **stamp dict** is not a reconstruction claim;
* the label must be **asserted, never inferred** — prose mentioning a reconstruction does not
  cap;
* committed-artifact test: **all seven** debt bundles are labelled and score their FC-7
  CAVEAT (never PASS) at their own tier.

`tests/scoring/`: **1191 passed** (was 1183 + 8 new), 3 skipped, 1 xfailed. The **7 failures
are pre-existing at `663605c5`**, verified by re-running them with this lane's changes
stashed — identical failure set, unrelated to FC-7
(`test_crossover_harness` demand loader, `test_ff_readiness_battery` ×5,
`test_forecast_parity` ERCOT parity-registry gap).

**Stdlib CI guards, all green with this change:** `check_mechanism_matrix.py` (bare and
`--base origin/main`), `check_registry_payload_parity.py`, `check_golden_manifest.py`,
`check_gate_a_provenance.py`, `check_cache_key_registration.py`, `ci_refactor_guards.py`,
`audit_keepers.py --check`, `legitimacy_diagnostics.py --keepers --no-d2-recompute`,
`register_forecast_run.py --reindex` (assembles; 33 runs), `ruff check` + `ruff format
--check`. `check_forecast_staleness.py` raises nothing new — its standing WARN improves from
31 to 25 unscored stamps. Two guards fail **identically at HEAD** and are not this lane's:
`check_forecast_invariants.py --sidecar-dir` (`miso-2021-2025-realized-t1h-d27`'s undeclared
I3 — lane D27's) and `check_forecast_parity.py` (NYISO ×2 / MISO ×1 seam fields).

## §6 The standing rule, restated — and what it does NOT open

> **A reconstruction can reach CAVEAT, never PASS.** The only route to a clean FC-7 on these
> seven legs is a **genuine re-run** — a fresh solve that writes its own `run_config`. That
> is a **charter decision**, not this lane's, and it was not taken here.

Corollaries worth having in the record:

* **The debt is now visible rather than closed.** Seven legs carry a permanent FC-7 caveat
  naming its cause. That is the honest middle the ruling asked for — not a repair.
* **The cap cannot become an escape hatch upward.** It only ever *worsens* a row; it can
  never lift a FAIL, and it never touches a category other than FC-7.
* **Nothing here re-opens the adoption question.** If a future sitting wants a clean FC-7 on
  these legs, the instrument now makes the price explicit: re-solve, or keep the caveat.

## §7 Guardrail compliance

Zero solves. Rule 1 `[R-STRUCT]`: no re-grade, no widened band, no hand-edited status —
every scored value is `forecast_verdict.py`'s own output. Rule 13 `[R-MEASURED]`: no measured
outcome fed back; the FC-3/FC-4 measurements are carried untouched precisely so none is
softened. Rule 15 `[R-DASHBOARD]`: forecast namespace only — **no backcast surface, no
keeper, no shard, no marker**. Rule 22 `[R-HOLDOUT]`: no year solved, scored or registered;
the quarantine gates pass. Rule 24 `[R-REGISTRY]` / 28 `[R-MECH-MATRIX]`: **no
`ScenarioConfig` field, no mechanism** — matrix duty (c) not triggered, guard clean. Rule 27
`[R-PUSH]`: `forecast_verdict.py` (1 980 → 2 046 lines) and the test module were edited **locally
with the Edit tool** and pushed as the exact on-disk bytes — never a regenerated full-file
rewrite — and blob-verified after the push. The **cross-lane re-grade rule** was the
operating mode throughout: the scorer edit is strictly additive, proved by re-running the
seven-key control *after* the change, and the board movement is confined to the seven keys
the ruling named.

**Collision handling:** T3-GOLDEN-2 (`neiso-t3`) and D31 (`miso-t1h`) touch keys that are
**not** among the seven — only dead legacy legs are. `ff-verdicts.json` was written with key
order preserved and `program-status.json` edited in a distinct block, so both rebase cleanly
against those lanes.
