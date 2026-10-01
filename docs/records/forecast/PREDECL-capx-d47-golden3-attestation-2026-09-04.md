# PRE-DECLARATION — capx D47: the GOLDEN-3 attestation, and two records items

**Committed and pushed BEFORE `forecast_attestation.json` is authored and before the
re-score is run.** That sequence is the whole governance content of this lane: D46
deliberately left GOLDEN-3's FC-7 failing rather than author an attestation *after*
reading that the row fails without one, and routed a properly pre-declared one to the
director (`FINDING-capx-d46-remeasure-2026-09-03.md` §4.6, §9 item 6). This document is
that pre-declaration. Nothing below is written after seeing a re-scored row.

**Lane:** capx D47 — a RECORDS lane. **ZERO SOLVES.** Branch
`claude/capx-d47-golden3-attestation-vwn9os`, FRESH off `origin/main` `a8464861`.

**Scope guardrails, restated as binding:** no `ScenarioConfig` field added or moved, no
parameter value changed, no keeper / shard / marker / matrix verdict touched, gate (a)
never moved, rule 22 untouched, the backcast namespace untouched (rules 5, 13, 21, 22,
24, 25, 27, 28). No mechanism is proposed or tested, so this lane incurs no rule-28
matrix duty.

---

## 1. What moves, declared before it is measured

### 1.1 The one row

**`FC-7` row 4, `attestation`.** Today it reads:

```
UNATTESTED  attestation: no forecast_attestation.json (a golden run cannot be certified unattested)
```

After this lane authors `results/ff-t3-neiso-golden/bau-d46/forecast_attestation.json`,
`forecast_verdict._score_attestation` will read it and return **`PASS`** —
*"all §5 checklist assertions present and true"* — **if and only if** all six
`ATTESTATION_ASSERTIONS` are present and true. **If any assertion is not true it is
recorded `false`, the row reads `FAIL` at full magnitude, and nothing is softened to
clear it.** That is the same commitment GOLDEN-2 pre-declared
(`FINDING-capx-t3-golden2-2026-09-01.md` §3) and it binds here identically.

### 1.2 What must stay byte-identical — asserted, and checked before registration

| surface | requirement |
|---|---|
| `FC-1` … `FC-6`, `FC-8` | **every category, every row, byte-identical** (label, applicability, status, each row's `row`/`status`/`detail`/`gating`) |
| `FC-7` rows 1–3 (`run_config`, `overlay-off`, `dof ledger`) | **byte-identical** |
| `determination` | **`HOLD`, unchanged** |
| `caveats` | `["FC-5 external corridor", "FC-6 driver response"]`, unchanged |
| `tier`, `iso`, `schema`, `rubric_version` | unchanged |

**If the re-score moves ANY row other than `FC-7`'s `attestation` row, this lane STOPS,
does not register, and routes to the director.** Declared now so the stop condition
cannot be renegotiated after the fact.

### 1.3 Two derived surfaces that necessarily move, named so they are not ambiguous

These are aggregates *computed from* the one row, not independent movements. Declaring
them here means neither can later be presented as a surprise:

1. **`categories["FC-7"].status`: `FAIL` → `PASS`.** The category status is the roll-up
   of its four rows; retiring the only non-PASS row retires the category failure.
2. **`reasons`: the line `"FC-7 provenance & DOF FAIL"` is dropped.** The list becomes
   the four remaining entries (FC-1, FC-2, FC-3, FC-4), in order, unchanged in wording.
   **`determination` stays `HOLD`** — GOLDEN-3 carries four independent FC failures
   (FC-1 I3 renewable dump, FC-2 cobweb, FC-3 T1-H bands, FC-4 T1-X dispatch skill), none
   of which this lane touches. **The attestation cannot promote anything.**

### 1.4 What this lane does NOT claim

Restoring FC-7 restores an **instrument** row, not a model result. It certifies that the
bundle's provenance evidence is complete and attested; it says nothing about whether
GOLDEN-3 is accurate, and it moves no accuracy row. The determination is `HOLD` before
and after, and the board reading is unchanged (D46 §4.6 already recorded that "nothing
the board reads is changed by it").

---

## 2. The attestation is READ from the committed bundle, not authored

**Nothing is invented that the bundle does not already carry.** Every assertion below is
backed by a committed artifact, and every fact quoted was verified from those bytes
**before** this document was written — which is the correct order: the pre-declaration
must state what will be attested, and it can only do that truthfully if the evidence was
read first. What was *not* read first is the re-scored verdict, and that is the sequence
the routing protects.

**The bundle:** `results/ff-t3-neiso-golden/bau-d46/`, run id
`neiso-2026-2050-t3-golden3-bau`, cache key **`67678e58b2d0526c`**, solved
2026–2050 (25/25 years) at git sha `012ec403` (basis
`d375bde39a325e531bb4195ec58cd1ca6f5bbc66`) by
`run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 --golden-posture
--full-solve-authorized`.

The six §5 assertions and the committed evidence each will cite:

| assertion | evidence read from the committed bundle | verified reading |
|---|---|---|
| `dof_ledger_complete` | `dof_ledger.json` — sha256 `c8cd36557f867961`, built by the committed `scripts/build_forecast_dof_ledger.py` from this bundle's own `run_config.json`, `run_git_sha 012ec403` | 7 entries, **7 IDENTIFIED, 0 UNIDENTIFIED, 0 unattested, 0 `residual`** → **true** |
| `run_config_reproducible` | `fc6/arms/base/` — a full 25-year re-solve of the identical `reference_config` construction, same environment, same HEAD | base-arm cache key `67678e58b2d0526c` = campaign key; `trajectory` (25 rows) and `invariants` (14 rows) **byte-identical**; the only differing top-level fields are `total_wall_s`, `per_year_perf`, `global_peak_rss_mb`, `run_config_path` → **true** |
| `honest_unfit_referenced` | `frontend/data/forecast/program-status.json` `honest_unfit` register (5 entries) + the bundle-specific items in D46 §4.6 and GOLDEN-2 §4 | register present and pointed to → **true** |
| `quarantine_attested` | this bundle's `run_config.json` `solved_years` + `mode` | `mode="forecast"`, years 2026–2050 only — rule 22's explicitly permitted class; **no year was solved, scored or read by this lane at all**; FC-3/FC-4 enter as committed bytes from their own lanes → **true** |
| `no_off_registry_knobs` | `run_config.json` full resolved surface (**778 keys**) + `dof_ledger.json` scope (non-default solve-affecting fields) | 7 non-default fields, all in `ScenarioConfig`, all identified; two CLI flags only (`--golden-posture`, `--full-solve-authorized`); no env-var knob, no per-plant dict, no `getattr` fallback → **true** |
| `registered` | `frontend/data/hindcast/neiso-2026-2050-t3-golden3-bau.json` (committed sidecar) + verdict key `neiso-t3` in `ff-verdicts.json`, prior preserved at `neiso-t3-pre-d46` | registered by the **producing** session (capx-D46) on the forecast namespace only; the backcast registry was not written (plan §7.5) → **true** |

**Two disclosures the attestation will carry on its face, rather than letting the row
read cleaner than the facts:**

1. **The author is not the producing session.** Rubric §5 names "the producing session
   (T3)" as the attestation's author. D46 produced this bundle; **D47 authors the
   attestation**, executing the director's routed item (D46 §9 item 6, which states in
   terms that a follow-up pre-declaring one "restores FC-7 with no re-solve"). This is a
   deviation from the rubric's default authorship and it is stated in the artifact's
   `attested_by` field, not buried. It is the price of D46 having correctly refused to
   author one post-hoc; the alternative — a post-hoc attestation from the producing
   session — is the thing the rule exists to forbid.
2. **`quarantine_attested` is asserted about producing THIS bundle**, which is what
   rubric §5.4 asks. The FC-3 input (`neiso-2021-2025-realized-t1h-d46`) is a separate,
   already-committed forecast-mode hindcast whose own solve spans `[2021, 2023, 2024,
   2025]` with `scored_years [2023, 2024, 2025]` and information cutoff `2020-12-31`; the
   FC-4 input (`neiso-2023-2027-crossover-rcrepair`) spans 2023–2027 in the permitted
   crossover window. Both are consumed here as **committed bytes** and their own
   quarantine postures belong to their own lanes' records. The attestation will say
   exactly that and will not describe those spans loosely.

---

## 3. The scorer invocation, declared verbatim

Artifact-only, **no LP is solved**. The `--attestation` argument is the sole difference
from the control:

```
python3 scripts/forecast_verdict.py --tier t3 \
  --summary            results/ff-t3-neiso-golden/bau-d46/full_horizon_summary.json \
  --run-config         results/ff-t3-neiso-golden/bau-d46/run_config.json \
  --dof-ledger         results/ff-t3-neiso-golden/bau-d46/dof_ledger.json \
  --paired-invariants  results/ff-t3-neiso-golden/bau-d46/fc6/paired_invariants.json \
  --driver-battery     results/ff-t3-neiso-golden/bau-d46/fc6/driver-battery-neiso-2026-09-03.json \
  --hindcast-score     results/hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json \
  --crossover-score    results/hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json \
  --corridor           results/ff-corridor/dispositions/neiso-t3.json \
  --benchmark-corridor results/ff-corridor/benchmark-corridor-anchors.json \
  --attestation        results/ff-t3-neiso-golden/bau-d46/forecast_attestation.json \
  --json-out           results/ff-t3-neiso-golden/bau-d46/forecast_verdict.json
```

**CONTROL-FIRST, ALREADY EXECUTED BEFORE THIS PRE-DECLARATION.** The same command
**without** `--attestation` was run at HEAD `a8464861` and reproduces the committed
`neiso-t3` record with **ZERO non-provenance diffs** — all eight categories, every row,
`determination`, `reasons`, `caveats` — and is identically equal to the committed
`bau-d46/forecast_verdict.json` on those fields. The baseline is therefore *proven*, not
assumed, and the input set above is *established*, not guessed. (Establishing it mattered:
GOLDEN-3's FC-3 consumes D46's own re-solved T1-H `neiso-2021-2025-realized-t1h-d46`, not
GOLDEN-2's `neiso-2021-2025-curve`; scoring with the latter yields a different FC-3 band
list and would have been a silently wrong control.)

---

## 4. Registration — preserve-then-overwrite, declared in advance

1. The current bare **`neiso-t3`** entry (D46's GOLDEN-3 record) is preserved
   **BYTE-EQUAL** at **`neiso-t3-pre-d47`** in
   `frontend/data/forecast/ff-verdicts.json`, with its own `provenance` block intact
   (`scored_at_sha e659a6eaecdc`, `scored_at_date 2026-09-03T11:42:51Z`,
   `cache_epoch 67678e58b2d0526c`, `run_id neiso-2026-2050-t3-golden3-bau`,
   `session capx-D46`).
2. The bare **`neiso-t3`** key then takes this re-score, stamped `session capx-D47`
   against the same `cache_epoch` and `run_id` — **the run is unchanged; only the
   scoring inputs gained one artifact.**
3. The existing preserved chain (`-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`,
   `-pre-p2scope`, `-prera-2026-08-31`, `-pre-d46`) is **untouched**.
4. The committed run-explorer sidecar
   `frontend/data/hindcast/neiso-2026-2050-t3-golden3-bau.json` is **not rewritten** —
   its embedded stamps are D46's registration-time provenance and stay that way. The
   forecast-namespace `registry/`, `runs/`, `manifest.js`, `program-status.js` are
   generated and gitignored; `--reindex` is run locally for the `file://` preview only.
5. `results/ff-t3-neiso-golden/bau-d46/forecast_verdict.json` is rewritten in place with
   the re-scored verdict (it is the bundle's own copy of the same record).

**No other verdict key, no other bundle, no other ISO is touched.** D45-R owns the
PJM/NYISO forecast surfaces and the NEISO default-posture leg; the audit programme's
stage-0 re-captures own `results/regression-goldens/`. Nothing here reaches either.

---

## 5. The two records items, pre-declared as records-only

Neither re-scores anything, and neither changes a determination.

- **(D46 §9 item 7) The `-pre-d46` like-for-like table.** A short table in this lane's
  finding giving, per `-pre-d46` key: its vintage (solve cache epoch + solve git sha,
  **not** the scoring sha), which of the three refresh axes its delta spans, and whether
  a delta against it is attributable. Pre-declared expectation, from the config bytes
  already read: **§9 item 7 enumerates four keys but SIX exist** — it omits
  `miso-t1h-pre-d46` entirely and mis-scopes `neiso-t1f-pre-d46`. The table will cover
  all six and say so plainly; the correction is to the *enumeration*, not to §4.6's
  substantive scope caveat, which stands.
- **(D46 §9 item 4) The `neiso-t1h` posture disclosure.** A dated note appended to the
  board's NEISO FC-3 carrier field `isos.NEISO.t1h_provenance` in
  `frontend/data/forecast/program-status.json` (the field D37 itself edited — the
  precedent), plus the same disclosure in the finding. It states that the bare
  `neiso-t1h` key carries `neiso_net_icr_requirement=true` while the shipped default is
  `false`, that this inverts director ruling r#33 ("a bare key carries the SHIPPED
  posture"), that its origin is D37 registering the ARMED leg bare and the control under
  the suffixed `neiso-t1h-d37-control`, and that D45-R's default-posture NEISO leg
  replaces it. **This lane does not re-solve, does not flip the field, and does not move
  the `neiso-t1h` determination** (`HOLD`, unchanged).

---

## 6. Pre-declared failure modes, to be graded at full magnitude

1. **Any non-attestation row moves** → STOP, do not register, route to the director (§1.2).
2. **Any of the six assertions reads false on the committed evidence** → it is recorded
   `false`, FC-7 reads `FAIL` on it, and the failure is reported rather than repaired by
   softening the assertion.
3. **The control fails to reproduce at re-run time** → the input set is wrong; stop and
   re-establish it rather than registering a verdict whose baseline is unproven.
4. **`--reindex` or `check_gate_a_provenance.py` regresses** → repair or route; gate (a)
   is never moved by this lane, and its reading is re-checked at close.

Rule 27 applies to every file ≥300 lines this lane pushes —
`frontend/data/forecast/ff-verdicts.json` (9,299 lines) and
`frontend/data/forecast/program-status.json` (1,156 lines) in particular: local `Edit`
only, exact on-disk bytes pushed, blob verified (line count + hash) immediately after
each push and before the next commit.

---

**Pre-declared 2026-09-04, capx D47, before `forecast_attestation.json` existed and
before any re-score was run.**
