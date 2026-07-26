# miso-91 apply bundle

The miso-91 work (DOF-declare + re-home `SUMMER_WEFOR_SHARE`) is complete and
was verified locally, but the session could **not** `git push`. It ships as this
bundle instead.

## Why this is a bundle and not a commit

The git proxy at `127.0.0.1:41729` rejects `git-receive-pack` **by policy**:
403 on an empty POST, 413 with a body — and it does so for a **zero-object**
push, so it is not a pack-size problem and no client-side setting fixes it
(`http.postBuffer` large → 413, small → 502, `--no-thin` → 413). Direct
`api.github.com` from bash is refused too (403, "GitHub access is not enabled
for this session"). The remaining channel is the MCP `push_files` tool, which
needs file content inline — fine for new files, but pushing modified
`constants.py` (2603 lines) or `arrays.py` (2389 lines) that way means
reproducing a large existing file from the model's response, which is exactly
what CLAUDE.md rule 27 forbids and exactly what truncated `constants.py` once
before.

> **Correction for future sessions.** The miso-91 handoff states that `git push`
> "WORKS from this web container (re-verified 2026-07-26, four commits)" and
> that CLAUDE.md's API-only section is stale. That is **wrong**, at least as of
> 2026-07-26. CLAUDE.md is correct.

## Apply order

From a clean checkout of `main`:

```bash
# 1. the source change (re-homes the two constants; values byte-identical)
git apply docs/handoffs/patches/miso-91-summer-wefor-dof-src.patch

# 2. the data-ask section 2a
git apply docs/handoffs/patches/miso-91-data-ask-section-2a.patch

# 3. the three DERIVED artifacts (registry entries, citations render,
#    DOF ledger, governance addendum). Idempotent.
python docs/handoffs/patches/miso-91-register-and-declare.py

# 4. the regression test and the calibration-log entry
git mv docs/handoffs/patches/miso-91-test_summer_availability_constants.py \
       tests/test_summer_availability_constants.py
cat docs/handoffs/patches/miso-91-calibration-log-entry.md \
    >> docs/calibration-log/miso.md

# 5. regenerate the status shard (timestamp only; determination unchanged)
python scripts/build_status.py --iso MISO
```

Then delete this README and the two consumed fragments.

## Verification (all of these were green in the session)

```bash
python scripts/calibration_verdict.py results/calibration/miso88_egrid_hr
#   -> CALIBRATED-WITH-CAVEATS, 3 ledgered caveats  (UNCHANGED)
python scripts/audit_keepers.py --iso MISO
#   -> PASS: 0 failure(s), 0 warning(s)   (E8: 28 entries, 4 residual)
python scripts/validate_parameters.py
#   -> FAIL: 48   <-- this is the CORRECT result: 48 is the PRE-EXISTING
#      backlog on main. Before the registry entries it was 53; the five new
#      constants are registered, so the count returns to baseline. It cannot
#      reach 0 in this bundle.
python -m pytest tests/test_summer_availability_constants.py -q
#   -> 12 passed, 13 subtests passed
python -m pytest tests/test_fleet.py tests/test_fleet_facade.py -q
#   -> 124 passed
```

Targeted regression baseline, unchanged by this work: the `run_calibration_full`
importer modules stay at **8 failed / 186 passed** (all 8 are pre-existing
`test_pipeline_facade_shims` failures). The full suite measured **93 failed /
5020 passed** with `-p no:randomly` and the two usual collection-error modules
ignored — recorded because the inherited number is disputed (the handoff says
108, miso-90 measured 90); no failure is in a file this session touched.

## Equivalence evidence

Applied to a pristine `origin/main` worktree, steps 1–3 reproduce **all seven**
changed non-generated files byte-for-byte against the session's local commit,
confirmed by `git hash-object`:

```
MATCH  src/market_sim/config/fuel_trajectories.py
MATCH  src/market_sim/config/constants.py
MATCH  src/market_sim/data/fleet/arrays.py
MATCH  frontend/data/parameters.json
MATCH  docs/parameter-citations.md
MATCH  results/calibration/miso88_egrid_hr/calibration_attestation.json
MATCH  docs/handoffs/miso-outage-grain-data-ask-2026-07.md
```

The replay script is idempotent — a second run is a no-op.

## What the change is, in one paragraph

`_SUMMER_WEFOR_SHARE = 0.30` was uncited (rule 5), unregistered and undeclared
(rule 21). Those are one defect, not three: it lived in `data/fleet/arrays.py`
as a module-private literal, and `validate_parameters.py` scans only
`vars(constants)` + `ScenarioConfig` defaults, skipping private and
non-uppercase names — invisible three ways over, a rule 20 `[R-REGISTRY]`
violation by location. The fix re-homes it (and `SUMMER_CLASS_DERATE`) to
`config/fuel_trajectories.py` beside the `THERMAL_AVAILABILITY` table they
modify, **values byte-identical**, and declares both in the keeper's DOF ledger
with open root causes. Measured (no LP): the share governs **all six non-coal
thermal classes**, not CT_PEAKER alone as miso-90 recorded — ≈3.9–5.8 GW of
MISO summer-peak capability. **The value was deliberately not changed**: that
blast radius is the same order as the ~10 GW under-derate ledgered as C3b, so a
hand-set value would be an answer key for an already-ledgered miss (rule 24).
Full reasoning: `docs/handoffs/miso-91-summer-wefor-dof-charter-2026-07.md`.
