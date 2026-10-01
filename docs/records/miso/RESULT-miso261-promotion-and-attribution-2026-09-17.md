# RESULT — miso-261: the owner's promotion was never executed; executed it at ZERO LP, settled the bench attribution, and split COAL_BIT into two objects

```
SESSION : miso-261        ISO: MISO        LP SPENT: ZERO. No shard launched.
KEEPER  : 2026-09-16-miso-259-coal-fuel -> 2026-09-16-miso-260-seam-ladder
          (bundle results/calibration/miso260_seam_span, span 2020-2025)
TRAIN   : 2023-2025 CALIBRATED, zero fails, C3c the lone ledgered caveat.
          MISO's card reads CALIBRATED. Full registered span reads NOT-YET on the
          validation rungs, reported at full magnitude and never gating (rule 30(c)).
ESCALATED: three things, in section 6 -- none absorbed.
```

---

## 0. THE STATE I ACTUALLY INHERITED IS NOT THE STATE MY CHARTER DESCRIBES

`HANDOFF-miso261` opens *"KEEPER YOU INHERIT: 2026-09-16-miso-260-seam-ladder, bundle
`results/calibration/miso260_seam_span`, span 2020-2025 ... MISO's card reads CALIBRATED."*

**None of that was on `main`.** Measured at `origin/main` `73281357`, before I touched anything:

| what the charter assumes | what was actually there |
|---|---|
| keeper `2026-09-16-miso-260-seam-ladder` | `frontend/data/backcast/keepers/MISO.json` read `2026-09-16-miso-259-coal-fuel` |
| bundle `miso260_seam_span` | no MISO bundle directory existed at all |
| the run registered | `registry/` held one MISO sidecar, `miso-259`'s |
| MISO's card CALIBRATED | true, but on the **superseded** keeper |

miso-260's own `RESULT` explains why: ADDENDUM A.1 records the owner's ruling (*"Is this a
recommended keeper candidate? If so plz promote"*), and A.3 records the span *"as launched"* —
two shards, pinned SHAs, out-dirs, branches. **A.3 is not where that session stopped.** It
launched the legs and opened PR #6259, which went conflicted and never merged. The promotion the owner
ruled on has been outstanding since 2026-09-16, and so has miso-260's own forecast gate-(a)
re-key.

## 1. THE PROMOTION, EXECUTED AT ZERO LP

Rule 31 `[R-RETAIN]` trigger (i) had already fired — the owner ruled — so this is execution, not
a new decision. Rule 34 `[R-SHARD-PROMOTABLE]` (d) is why it cost nothing: **both shard branches
survived and both carried their bundles, `dispatch/<y>_P1.parquet` included.**

| leg | branch | **full recovery SHA** | years | bundle | files | size |
|---|---|---|---|---|---|---|
| V | `claude/miso260-span-v` | `5bb6b99690d74b55ca79247b1113fe0a81525035` | 2020-2022 | `miso260_seam_v` | 37 | 592 MB |
| T | `claude/miso260-span-t` | `5478c2ac2e1985b602ef163459809ef0d919b977` | 2023-2025 | `miso260_seam_t` | 37 | 607 MB |

Verified before composing: both legs carry `miso_seam_measured_ladder: true`,
`coal_fuel_inventory: true`, `reference_price_interface: true`, both solved at the **same**
`git 36ac2560`, and the two-config reserve partition runs in the declared direction
(`miso_measured_reserve_requirements` / `miso_reserve_online_gated` False in V, True in T).

Then, in order: `_miso260_compose_span.py` → `stamp_config_partition.py` (+ `--check`:
*"every year resolves identically"*) → `run_calibration_full.py --rebuild-benchmark` →
`dashboard_add_run.py` → `gen_miso260_attestation.py` → re-score.

### 1.1 A BUG IN THE COMPOSE PROBE, REPORTED NOT WORKED AROUND

`_miso260_compose_span.py::regenerate_diagnostics` treats a non-zero exit from
`legitimacy_diagnostics.py` as a regeneration failure and prints *"FAILED (exit 1) — C8 would
score SKIPPED; do not register."* But `legitimacy_diagnostics.py` exits 1 to report its own
**verdict** (`Overall: FAIL`, which MISO's D-1/D-2/D-4 rows have always produced), not a crash.
The artifact was written correctly — all six years, well-formed `gates` and `D1/D2/D4/D5/D9/D10`
blocks — and the script's own real check (*"years in the regenerated artifact == expected"*)
never ran because it returned early. **C8 scores PASS on the composite**, so the warning was a
false stop. Left in place and reported rather than patched: rule 32(c)(6) keeps infrastructure
edits out of a solve lane, and this is the successor's to fix deliberately.

## 2. THE GATE TABLE, AS SCORED — INCLUDING THE ONE MY CHARTER GOT WRONG

| gate | verdict | measured |
|---|---|---|
| `check_registry_payload_parity` | **as charted** | 4 unmapped dirs: the 2 pre-existing (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) **+ my own 2 untracked leg dirs**, which are a filesystem-walk artifact (rule 31's 2026-09-16 correction) and invisible to CI. Neither `rm`'d. The composite maps cleanly and does not appear. |
| `audit_keepers --iso MISO` | **PASS** (0 failures, 1 warning) | E13 fired before the prune exactly as rule 35(f) predicts, then cleared. E3 (`meta.json` years vs `calibration_flags` years) is the pre-existing warning the charter names. |
| `build_status --iso MISO --check` | **PASS** | *"status parts in sync (1 keepers: MISO)"* |
| `check_mechanism_matrix --base origin/main` | **PASS** | Also cleared a **MISO-owned** warning the charter did not mention: §5.4's prose header did not name the designated keeper. Re-stamped. Remaining warnings are pre-existing `scenarios.py` anchor drift. |
| `check_cache_key_registration --base origin/main` | **PASS** | no new `ScenarioConfig` fields; 851 fields / 306 registered / 305 solve-surface names all resolve. |
| `check_gate_a_provenance` | **MISO repaired; charter WRONG about it** | The charter says *"MISO's row was repaired by miso-260"*. **It was not** — the row cited `2026-09-12-miso-255-sil-measured`, i.e. it was **TWO** promotions stale, because miso-260's re-key never landed for the same reason its promotion did not. Re-keyed here. NEISO / NYISO / SPP still fail and are not mine. |
| `check_bench_freshness --iso MISO` | **PASS** | 6 parts, 0 STALE. |
| `pytest tests/scoring` | **PASS — and the charter's number is WRONG** | see §2.1 |
| `node --check` on the matrix shard | **PASS** | 333 cells before and after; the 25.7 KB shrink is entirely the `gates` stamp being replaced (30,342 → 3,895 bytes), which is that field's purpose. |
| `_miso260_bench_parity.py --iso MISO --base origin/main` | **PASS, run TWICE** | max \|Δ actual class TWh\| = **0.000000** in all six years, both **before** and **after** registration. |
| `_miso257_btm_identity.py` | **PASS** | worst \|diff\| over the CHP classes **0.8326 TWh**, against the ±17-20 TWh signature of the miso-257 defect; CC_CHP holds to ±0.0000 in 2020-2024. |

### 2.1 The pytest baseline is 22, not 19 and not 18 — measured both ways as instructed

The charter says *"THE BASELINE IN THESE CONTAINERS IS 19 FAILURES, not the 18 an older handoff
quotes; measure it yourself both ways rather than trusting either number."* I did, in the same
container, same interpreter, by stashing only the tracked changes and moving the three new
untracked files aside:

```
baseline (origin/main state) : 22 failed, 1530 passed, 18 skipped, 178 subtests passed
with this session's changes  : 22 failed, 1530 passed, 18 skipped, 178 subtests passed
diff of the FAILED name sets : IDENTICAL
```

**Zero new failures.** The number in this container is **22**. *(CORRECTED 2026-09-18: I wrote
that the charter's 19 was "as stale as the 18 it corrects". That was unfair — PR #6259 §C.5
shows miso-260 measuring **19 at HEAD and 19 reverted, identical sets**, so 19 was accurate
when written. `main` added tests between its session and mine and the baseline moved to 22.
The charter's instruction — measure it yourself both ways — is the durable point, and it is
why this drift was caught rather than mistaken for a regression.)*

## 3. WHAT THE KEEPER SCORES, WITH EVERY REGRESSION AT FULL MAGNITUDE

**Train tier 2023-2025 — CALIBRATED.** C1 / C2 / C3a / C3b / C4 / C6 / C8 all PASS; C3c CAVEAT
(ledgered, non-downgrading under rubric v3.3). Per year: 2023 CALIBRATED, 2024 CALIBRATED, 2025
CALIBRATED-WITH-CAVEATS (unscored criteria on the preliminary EIA-923 vintage).

**Registered full span — NOT-YET, and every failing cell is a validation rung:**

| criterion | year | magnitude |
|---|---|---|
| C1 | 2020 COAL_BIT | **−10.29 TWh** (−1.5 pp), out of the ±8 TWh band — **was −7.00 under the predecessor** |
| C1 | 2022 CC_REGULAR | −9.47 TWh (−1.2 pp) |
| C3a | 2020 | +16.3 % |
| C3a | 2022 | −14.6 % |
| C3b | 2021 | NRMSE 0.299 |

The COAL_BIT row is miso-260's own G-NOFLIP failure and it is a **real regression this promotion
carries**. The owner's ruling covers it in terms (*"If structural integrity improves but gates
regress that may still be a keeper"*), and rule 30(c) keeps it off the headline — but it is the
cost, and the successor's object is sitting inside it (§4).

**C6 was UNATTESTED at first registration** — the incumbent keeper's defect, diagnosed in
`RESULT-miso260` A.4 — and the run first scored NOT-YET on the train tier for that reason alone.
`gen_miso260_attestation.py` closes it: 6 exceptions carried, 4 re-measured on this bundle's own
records, **43 DOF entries carried and 0 added**, because the arm adds no `ScenarioConfig` field
and no free parameter.

**The status headline needed a second edit the README does not mention.** After the keeper flip,
`build_status --iso MISO` still printed `MISO:NOT-YET`, because the shard's `config_partition`
block pins a `run_id` **per config** and both still named `miso-259` — whose bundle is not on
disk, so both configs scored UNATTESTED. Re-keying the two `run_id`s restored `MISO:CALIBRATED`,
truthfully, on the live scorer. The partition's 2026-09-14 owner authorization is untouched.

## 4. THE CHARTER'S COAL_BIT FRAMING IS HALF RIGHT — IT IS TWO OBJECTS, NOT ONE

Phase 0, zero LP, from the recovered keeper's own `hourly/unit_hourly_<y>.parquet`, joining the
bench part's per-plant `COAL_BIT` / `COAL_PRB` / `COAL_LIGNITE` map onto the dispatch rows (the
`plant_group` column carries only `COAL`). **Capacity-weighted `mc` quantiles over unit-hours:**

| yr | class | util | q10 | q25 | **q50** | **q75** | **q90** |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020 | COAL_BIT | 0.715 | 4.50 | 4.50 | 4.95 | **28.77** | **31.29** |
| 2020 | COAL_PRB | 0.710 | 4.50 | 4.50 | 5.44 | **28.73** | **32.47** |
| 2023 | COAL_BIT | 0.726 | 4.50 | 4.50 | 4.91 | **37.84** | **45.81** |
| 2023 | COAL_PRB | 0.792 | 4.50 | 4.50 | 5.65 | **33.08** | **37.93** |
| 2025 | COAL_BIT | 0.835 | 4.50 | 4.50 | 4.98 | **35.40** | **39.40** |
| 2025 | COAL_PRB | 0.864 | 4.50 | 4.50 | 5.62 | **32.74** | **37.93** |

Two readings, and they do not agree with each other:

* **2023 and 2025 — the charter's intra-coal merit split is REAL, and it is confined to the
  UPPER tranches.** Both classes floor identically at $4.50 through q25 (the must-run /
  take-or-pay band) and both sit near $5 at the median, so the must-run stacks are
  indistinguishable. The divergence is entirely economic/peaking: COAL_BIT's q75 runs **$4.76
  (2023) / $2.66 (2025)** above COAL_PRB's and its q90 **$7.88 / $1.47** above. BIT's marginal
  blocks therefore sit behind PRB's, and BIT's utilization is correspondingly lower (0.726 vs
  0.792; 0.835 vs 0.864). That is exactly the shape of "BIT persistently short while PRB swings".
* **2020 — the merit split DOES NOT EXIST, yet 2020 carries the LARGEST BIT deficit.** q75 is
  28.77 vs 28.73 and q90 is 31.29 vs 32.47 — the distributions essentially coincide, and
  utilization is 0.715 vs 0.710, i.e. BIT is *marginally higher*. A merit split that is absent
  cannot explain a −7.00 TWh miss, still less the armed −10.29.

**So COAL_BIT is two objects.** The charter's *"One coal class persistently short and the other
swinging is an INTRA-COAL MERIT-ORDER SPLIT, not a coal-volume problem"* holds for 2023-2025 and
is **falsified for 2020**. And the fact that the *seam ladder* arm is what pushed 2020 COAL_BIT
from −7.00 to −10.29 points the 2020 object at the **import/seam channel displacing BIT**, not at
coal's own offer stack. A successor that tunes the BIT offer bands to close 2023-2025 will not
touch 2020 and may widen it. This session did not test either object and claims no mechanism.

## 5. THE BENCH FUEL-FAMILY ATTRIBUTION IS SETTLED — SEPARATE DOCUMENT

The charter's **first task**. Answered at zero LP, nothing fetched, in
**`docs/FINDING-miso261-bench-fuel-attribution-2026-09-17.md`**. Headline: the bench is not
mis-attributing gas; miso-253's 68.1 TWh differenced a **grid-delivered** benchmark against a
**full-plant** telemetry cell, and the coal leg is the EIA-930 MISO COL cell reading **17.5-21.1
TWh below CAMPD in every year** — which `render_calibration_html.py:260` already records. The
rival BFG/OG relabelling hypothesis is refuted on magnitude (2.2-5.9 TWh against a 33.5 TWh
number). **The ±33 TWh caveat is LIFTED**, and `fuelRows` remains the wrong basis to open a gas
lane on. One genuine coverage gap found and reported, not acted on: **West Riverside Energy
Center** (EIA 64020, 1.9→5.0 TWh 2020-2025, absent from the dispatch set in all six years).

miso-253's *"neither on disk — intake work, not a solve"* was wrong about the first of its two
named settling sources: `data/raw/_processed-legacy/eia923_monthly_generation.parquet` carries
`ba_code` per plant per fuel per year and has throughout.

## 6. WHAT I ESCALATED RATHER THAN ABSORBED

**AMENDED 2026-09-18, and item 1 is now CLOSED and item 3 RE-DIAGNOSED.** The owner pointed me
at **PR #6259** — miso-260's own promotion PR, opened 2026-09-17T03:07:23Z, **five minutes
before this session began**, and never merged. Everything below is corrected against it.

1. **The compose probe's false stop — FIXED, and miso-260 had already fixed it.** PR #6259
   carries the exact repair: check that the ARTIFACT exists and spans every year, rather than
   reading `legitimacy_diagnostics.py`'s exit status, *"so a nonzero exit is the normal case and
   says nothing about whether the artifact was written."* Recovered onto `main` 2026-09-18. I
   diagnosed this correctly and then left it unpatched under rule 32(c)(6); the fix existed in an
   unmerged PR the whole time, which is itself an instance of item 3.
2. **`check_gate_a_provenance` still fails for NEISO, NYISO and SPP**, each citing a superseded
   keeper. Unchanged, and still not mine (rule 25 / the keeper README's per-ISO scope).
3. **THE PROMOTION-LOSS MODE — MY ORIGINAL DIAGNOSIS WAS WRONG.** I wrote that miso-260 *"ran out
   of session before it could compose"* and that *"nothing in the rules makes the composition step
   survive a session boundary."* **Both are false.** miso-260 composed, stamped, attested,
   registered, promoted, pruned, re-keyed gate-(a), ran its gates and opened a PR — a complete,
   correct promotion. What failed is one step later and entirely mundane: **its PR went
   `mergeable_state: dirty` and nobody merged it.** Rule 34 protects the bytes and worked; rule 35
   sequences the promotion and miso-260 discharged it in order. The unprotected step is the
   LAST one — **a fully-executed promotion sitting in an unmerged PR is invisible to every gate in
   this repo.** `audit_keepers`, `build_status`, `check_gate_a_provenance` and the parity sweep all
   read the working tree or `main`; none of them can see that the ISO's real promotion is sitting
   in an open PR. So a successor clones `main`, sees the superseded keeper, and does the whole
   thing again — which is exactly what this session did, at the cost of a duplicated promotion and
   a wrong root cause published in five places. The cheap guard is the one I did not have and the
   next lane now does: **before building on a keeper, check for an open PR against that ISO's
   files.** Reported for the owner as the real gap; it is not a rule-34 or rule-35 defect.
4. **A duplicate-work cost, stated plainly.** Because #6259 never merged, `main` carried
   miso-260's RESULT without its Addendum C and its calibration-log entry without its promotion
   section — the whole of the STRUCTURAL-IMPROVEMENT case for this keeper. My own §3 reported the
   regressions faithfully and could not report the wins at all, because the before/after
   comparison needs miso-259's bundle, which is not on disk. Both are recovered verbatim
   2026-09-18 (RESULT ADDENDUM C; the log's promotion section), and they are what the owner's
   standing rule actually turns on: **failing criterion records over the registered span go
   7 -> 5**, C1 2021 CC_REGULAR **-9.46 FAIL -> -2.92 PASS**, C1 2021 COAL_BIT **-8.36 FAIL ->
   -7.02 PASS**, C3b 2020 **0.246 FAIL -> PASS**, C3a 2020 **+22.9% -> +16.3%**, and the D-2 2021
   ST_GAS forced-share failure cleared — against the one loss this document already carried, C1
   2020 COAL_BIT -7.00 -> -10.29. miso-260 also measured what I could not: across **27 commits of
   `main`**, 2022, 2023 and 2025 each reproduce the incumbent keeper at **max |d class TWh| =
   0.000000**, so the train tier provably did not move.

## 7. RETRIEVABILITY AND THE PROMOTION QUESTION (rules 31 / 34)

**Nothing is deleted and nothing is pending.** The promotion question this session existed to
close was already answered by the owner on 2026-09-16; it is now **executed and pushed**, so the
keeper's bytes are in `main`, not on ephemeral disk.

| artifact | where it lives now | what a promotion would cost from that state |
|---|---|---|
| `miso260_seam_span` (the keeper) | committed and pushed on this branch | nothing — it *is* the keeper |
| `miso260_seam_v`, `miso260_seam_t` (the legs) | untracked on this container's disk **and** on their shard branches at the full SHAs in §1 | nothing — `git checkout <sha> -- <path>` reproduces either leg |

**Shards**: this session **launched none** (rule 32(a): the parent ran zero LP). The two shard
branches it recovered from are miso-260's; they are **left alive and undeleted** deliberately,
under rule 33(f)(3) — they carry the only copies of the per-year leg bundles outside this
ephemeral container, and this session did not archive sessions it did not create.

**Still open, and the successor's:** COAL_BIT, now correctly framed as two objects (§4).
ST_CHP (6/6 negative, σ < 0.4 TWh) and ST_GAS (5/6) are untouched and remain as the charter
describes them.

## 8. RULES

* Rule 32 `[R-SHARD]` (a) — **zero LP; no shard launched.** Every number is from committed or
  recovered artifacts.
* Rule 31 `[R-RETAIN]` — nothing deleted; the outgoing keeper's stores were removed only under
  trigger (i), the owner's own promotion ruling, and only after `audit_keepers` verified the
  incoming keeper (rule 35(e) order).
* Rule 35 `[R-PROMOTE]` — (a) prune in the promoting session ✓; (b) year-set union
  {2020…2025} recorded **before** the prune ✓; (c) incoming keeper covers it exactly ✓;
  (d) `--force-uncite` used as the intended route, the citation being this session's own
  promotion note ✓; (e) promote → verify → delete ✓; (f) E13 clear ✓.
* Rule 30 `[R-TOUCHPOINT-FOLD]` (c) — the validation rungs are reported at full magnitude on both
  surfaces and never downgrade the ISO.
* Rule 1 `[R-STRUCT]` / 21 `[R-DOF]` — no mechanism tested, no parameter tuned, 43 DOF entries
  carried and **0 added**.
* Rule 28 `[R-MECH-MATRIX]` (b) — the `seam_neighbour_hourly_ladder` cell and the MISO shard's
  keeper/gates stamps updated in this session.
