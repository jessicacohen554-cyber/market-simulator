# FINDING — Y-15: flip-set sweep to 6-of-6 under R-AU

**Lane:** Y-15 (Model Audit & Release-Finalization Program)
**Date:** 2026-09-06
**Pin:** `76886c2e` (== `origin/main` at fetch; the director's pin `a22afd02` is an ancestor)
**Charter:** R-AU (owner, 2026-09-05 ~23:00Z, card "Flip") — *"Charter Y-13, flip at next
6-of-6"*; the flip lands at the first head reading 6-of-6 **after Y-13 and Y-14 merge**.
R-AH's condition is unchanged; R-AU sequences it.

**Precondition check.** Both gating lanes are on `main` at this pin:
`FINDING-y13-ci-plumbing-2026-09-05.md` (`60b0fe5c`) and
`FINDING-y14-ercot-golden-forward-2026-09-05.md` (`0db93bb2`). R-AU's sequencing condition
is therefore satisfied and a 6-of-6 head is actionable.

---

## 0. HEADLINE — the dispatch's two named reds were closed by other lanes before this pin; a
## third, unnamed, had opened; the bench item resolves AGAINST re-stamping on the dispatch's own rule

The director's reading was taken at `a22afd02` (ci.yml run 2541, id `34000187173`, head
`4b28c93f`, merged as #4891): 4 of 6, with Ruff and the Fast tier red. `main` advanced through
several merges before this lane pinned. At `76886c2e`:

| dispatch task | state at this pin | this lane's act |
|---|---|---|
| 1. Ruff — `tests/unit/model/test_ccs_retrofit.py` | **already fixed** by `a802936c` ("Hygiene: ruff format …; red on main"). A **different** file had since gone red: `scripts/calibration_verdict.py`, landed unformatted by `17b9294f` (rule 30 `[R-TOUCHPOINT-FOLD]`) | **fixed here** — `ruff format`, 1 insertion / 3 deletions, formatting only |
| 2. Gate-(a) — MISO row cites superseded keeper | **already re-keyed** by `4d1ed3ad` (capx director desk, standing duty Q34) to `2026-09-05-miso-220-nonsteam-lift`; NYISO likewise by `32f8de52` to `2026-09-06-nyiso-196-extract-basis`. `check_gate_a_provenance.py` **exits 0** (6 rows) | **no edit** — verified only; `program-status.json` untouched by this lane |
| 3. Bench freshness — ERCOT/2022 stale | **still red**, exactly as dispatched (`b2f21b9a00d3` vs HEAD `4254168edcfe`; 24 parts, 1 stale, 23 engine-drift warnings) | **NOT re-stamped** — the dispatch's own decision rule resolves against it; see §3 |

**Net:** one substantive repair (Ruff), one verification, one adjudicated-and-declined re-stamp
with a defect in the deciding instrument reported.

---

## 1. Ruff — `scripts/calibration_verdict.py`

Run 2541's job `101397530937` read *"Would reformat: tests/unit/model/test_ccs_retrofit.py"*
(capx D65, PRs #4890/#4891). That file is **already formatted at this pin**; `a802936c` repaired
it. The check is nonetheless red at `76886c2e`, on a **different** file:

```
$ uv run --frozen ruff format --check .
Would reformat: scripts/calibration_verdict.py
1 file would be reformatted, 1337 files already formatted
EXIT=1
```

Introduced by `17b9294f` ("Rule 30 `[R-TOUCHPOINT-FOLD]`: a touchpoint publishes AS the keeper,
not beside it"). The whole delta is one call re-joined onto a single line:

```diff
@@ -1110,9 +1110,7 @@
         if tier != holdout_policy.TIER_TRAIN:
-            _reclassify(
-                rec, "c3c-holdout-year-2026-09-05", C3C_HOLDOUT_RULE_REASON
-            )
+            _reclassify(rec, "c3c-holdout-year-2026-09-05", C3C_HOLDOUT_RULE_REASON)
```

Formatting only; no scoring logic touched. `scripts/calibration_verdict.py` is 3,437 → 3,435
lines, so rule 27 `[R-PUSH]` applies: the edit is the on-disk `ruff format` write (never
regenerated model content), pushed as exact local bytes, and blob-verified after the push (§6).

After the fix, repo-wide with `$?` read directly: `ruff format --check .` **EXIT=0**
(1,338 files), `ruff check .` **EXIT=0** ("All checks passed!").

---

## 2. Gate-(a) provenance — no repair owed at this pin

`check_gate_a_provenance.py` **exits 0** at `76886c2e`:

```
gate-(a) provenance OK (6 row(s) checked: keeper identity + marker state match the
backcast store; no determination read)
```

The MISO row the dispatch names was re-keyed by `4d1ed3ad` before this lane pinned — by the capx
director desk under the standing Q34 duty, from `2026-09-05-miso-217-intermphys` to
`2026-09-05-miso-220-nonsteam-lift`, recorded there as *"the TWELFTH firing of
scripts/check_gate_a_provenance.py, the TENTH promoter miss since R-T"*. NYISO's row moved in the
same window (`32f8de52`, thirteenth firing / eleventh miss). Both re-keys record the gate verdict
as **unmoved** (MISO fail→fail, marker absent on both sides; NYISO fail→fail, marker withdrawn),
which is the R-T convention.

`tests/scoring/test_gate_a_provenance.py` — the Fast tier's single red in run 2541 (job
`101397530884`) — passes at this pin as part of the tier (§4).

**This lane made no edit to `frontend/data/forecast/program-status.json`.** The repair the
dispatch assigned had already been performed by its owner; re-writing the row would have
duplicated the R-T stamp for no verdict change.

---

## 3. Bench freshness — ERCOT/2022 is NOT re-stamped, and the deciding instrument is degenerate

### 3.1 The gate is not in the flip set

`scripts/check_bench_freshness.py` appears in **no** workflow under `.github/workflows/`. It is
this desk's gate, as the dispatch states. Leaving it red does **not** affect the six R-AE checks
and does not block R-AU's flip.

### 3.2 The reading

```
builder fingerprint at HEAD: 4254168edcfe
::error frontend/data/backcast/bench/ERCOT/2022.json.gz:: STALE — carries b2f21b9a00d3
bench freshness: 24 part(s) checked, 1 STALE, 23 with engine drift
EXIT=1
```

The 23 engine-drift lines are **warnings, not gates** (3–10 intervening commits under
`src/market_sim/data/`, `src/market_sim/config/`), recorded here as warnings per the dispatch.

### 3.3 Lineage — a merge race, established from the artifacts

Fingerprints computed with HEAD's instrument (`bench_stamp.builder_fingerprint`, the AST hash
Y-12 introduced) applied to the builder sources at each commit:

| commit | AST fp | byte fp |
|---|---|---|
| `HEAD` (`76886c2e`) | `4254168edcfe` | `abdc9f0d03d3` |
| `3d0fd19d` (Y-12, 22:34:10Z) | `4254168edcfe` | `abdc9f0d03d3` |
| `3d0fd19d^` == `677b605a` | `96e5860ce4ec` | **`b2f21b9a00d3`** |
| `9b62c6de` (part commit's parent) | `4254168edcfe` | `abdc9f0d03d3` |
| `f1561c2d` (the part's commit) | `4254168edcfe` | `abdc9f0d03d3` |

The part carries **`b2f21b9a00d3`**, which is the **byte** fingerprint at `3d0fd19d^`. So the
part was *written* by a pre-Y-12 checkout, while the byte-era stamp was still in force.

Y-12 is nonetheless an ancestor of the part's commit parent (`git merge-base --is-ancestor
3d0fd19d 9b62c6de` → yes). So the ercot-249/250 lane **built** the part before Y-12, then merged
onto a post-Y-12 `main` and committed the already-built part without re-rendering it. A merge
race, not a builder defect.

Y-12 landed as a pair: `3d0fd19d` changed the hash to the AST, and the sibling commit
**`404f1908` — "Y-12: re-stamp all 20 bench parts at builder 4254168edcfe"** — re-stamped
every part then on `main`. ERCOT/2022 was in flight at that moment and so was never in the set.

### 3.4 The dispatch's decision rule resolves against re-stamping

> *"If the builder AST at the part's build commit equals HEAD's AST … re-stamp … If the ASTs
> differ, do NOT re-stamp: report it and leave the part red for the calibration desk's lane."*

AST at the part's build state = `96e5860ce4ec`. AST at HEAD = `4254168edcfe`. **They differ.**
Per the rule as written, this lane does **not** re-stamp, and the part stays red for the
calibration desk to rebuild with `--rebuild-benchmark` — a solve-side act, not this desk's.

### 3.5 THE DEFECT — the aggregate AST test cannot discriminate, and is degenerate for every pre-Y-12 part

Decomposing the fingerprint per source between the part's build state and HEAD:

| builder source | AST | bytes |
|---|---|---|
| `scripts/render_calibration_html.py` | SAME | **byte-identical** |
| `scripts/render_backcast.py` | SAME | **byte-identical** |
| `scripts/lib/backcast_artifacts.py` | SAME | **byte-identical** |
| `scripts/lib/bench_stamp.py` | **MOVED** | differs |

The entire divergence is `bench_stamp.py` — the module that **computes the stamp**, and which
contributes nothing to the bench payload. The three sources that actually produce the payload are
**byte-identical** between the part's build state and HEAD. By the guarantee `bench_stamp.py`'s
own docstring states (*"two sources with identical ASTs compile to identical behaviour, so a part
written under either is byte-identical by construction"*), ERCOT/2022's payload **is** what the
builder at HEAD would produce.

The instrument cannot say so, because **`bench_stamp.py` is a member of its own
`BUILDER_SOURCES`**. Y-12's edit to it therefore moved the aggregate fingerprint for **every**
part in existence. Consequences:

1. **The aggregate AST test can never return "equal" for any part built before Y-12.** Under the
   dispatch's rule read literally, no such part is ever re-stampable — every one would need a
   full re-solve.
2. **That contradicts the program's own practice.** `404f1908` re-stamped 20 parts across the
   very same boundary, by exactly the Y-8 method. If the literal rule were right, that commit
   would have been wrong.
3. The self-inclusion is not itself a mistake — a change to the stamping logic *should*
   invalidate parts. But it makes the aggregate hash unusable as the *payload-reproducibility*
   test, which is the question a re-stamp turns on.

**Recommendation (director's call, not taken here).** Either (a) give
`bench_stamp` a payload-only fingerprint over the three payload-producing sources, and decide
re-stampability on that while keeping the aggregate hash as the staleness stamp; or (b) authorize
this single re-stamp explicitly under the `404f1908` precedent. Option (a) is the durable one and
removes the judgment call from every future lane. **Neither is taken in this PR** — the part is
left red exactly as the dispatch directs, and the ERCOT keeper's C1 verdicts remain scored
against a part whose payload is provably HEAD's but whose stamp does not say so.

---

## 4. Local gate sweep at this pin (`$?` read directly)

| check | exit |
|---|---|
| `ruff check .` | **0** |
| `ruff format --check .` | **0** (after §1) |
| `scripts/audit_keepers.py --check` | **0** — "PASS: 0 failure(s), 0 warning(s)" |
| `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` | **0** |
| `scripts/check_registry_payload_parity.py` | **0** — 14 runs, 47 bundle dirs, 0 known-unsynced |
| `scripts/check_golden_manifest.py` | **0** |
| `scripts/check_gate_a_provenance.py` | **0** — 6 rows |
| `scripts/check_cache_key_registration.py` (HEAD + `--base origin/main`) | **0** — 798 fields, 253 registered, defaults match |
| `python -m compileall -q src scripts` | **0** |
| `scripts/ci_refactor_guards.py` | **0** — import-walk OK, script-refs OK |
| facade + persisted-identity (10 files) | **0** — 90 passed |
| cache-key-pin tests (2 files) | **0** — 24 passed |
| Fast tier (`-n 2 -m "not slow and not integration and not fulldata"`) | see §6 |
| `scripts/check_bench_freshness.py` | **1** — §3, desk gate, not in the flip set |
| `scripts/check_forecast_parity.py` | **1** — §5, not in the flip set |

---

## 5. Reds outside the flip set, recorded and not chased (dispatch task 5)

**`check_forecast_parity.py` (job "FR-22 backcast→forecast parity") — EXIT=1, two failures:**

```
FAIL  ERCOT: ercot_storage_as_soc_reserve is armed in the keeper with no
      forecast-orchestrator consumer and no registry declaration
FAIL  NYISO: nyiso_seam_deliverability_envelope is armed in the keeper with no
      forecast-orchestrator consumer and no registry declaration
```

Pre-existing at this pin and **not caused by this PR** — the checker reads the keeper shards and
`scripts/lib/forecast_parity_registry.py`, none of which this lane touches. FR-22 is **not one of
R-AE's six**, so it does not bear on the flip. **Owner:** the lanes that armed those two
mechanisms in their keepers, or the forecast-orchestrator desk, via a consumer or an explicit
backcast-only-by-design declaration in `forecast_parity_registry.py`. Recorded, not chased.

**`check_bench_freshness.py`** — §3. Desk gate, not CI; adjudicated and declined.

---

## 6. CI reading on this PR — the six R-AE checks

*(filled in from the PR's own run, job by job)*

