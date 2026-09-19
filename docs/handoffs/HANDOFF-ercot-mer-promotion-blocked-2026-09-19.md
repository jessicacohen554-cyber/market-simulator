# HANDOFF — ERCOT MER keeper promotion: PREPARED, BLOCKED AT THE REGISTRATION STEP

**Session:** ercot-mer (parent), 2026-09-19. Branch `claude/ercot-keeper-configs-60kit8` (rebased onto `origin/main` `995f7b7e`).
**Owner instruction:** "Promote." (2026-09-19) — rule 31 `[R-RETAIN]` trigger (i); the owner has ruled.
**Status:** every zero-LP preparation step is COMPLETE and verified. The promotion itself is blocked by the
Claude Code **auto-mode permission classifier** ([Modify Shared Resources]), not by any model or data problem.

---

## 1. What is DONE and verified

| step | state | evidence |
|---|---|---|
| Five per-year legs solved & pushed | ✅ | branches `claude/ercot-mer-<year>-v2`, 18 files each, SHAs in §4 |
| Per-leg config signature | ✅ PASS ×5 | 2021/2022 carve-out A; **2023 carve-out B `ep_referenced=false`**; 2024/2025 forward |
| `marginal_emission_rate` present & non-zero | ✅ ×5 | statistics in `RESULT-ercot-mer-keeper-resolve-2026-09-19.md` |
| Composite bundle built | ✅ | `results/calibration/ercot_mer20260919_five_year` (752 MB) |
| Root parquets concatenated | ✅ | system 306,600 rows / storage 254,040 / flows 438,000 / btm 25, all 5 years |
| Per-year files copied | ✅ | 55 files across `hourly/`, `dispatch/`, `floors/` |
| `config_partition_overrides` stamped | ✅ | 3 recipe groups reproduced |
| Partition `--check` re-derives | ✅ | "every year resolves identically (3 overlaid years)" |
| **Partition identical to the incumbent keeper's** | ✅ | 2021/2022/2023 blocks compare `True` key-for-key |
| `legitimacy_diagnostics.json` regenerated | ✅ | `years: [2021,2022,2023,2024,2025]`, D-10 PASS |
| Benchmark parquets rebuilt (zero-LP) | ✅ | `--rebuild-benchmark`, exit 0 |
| Branch rebased onto latest main | ✅ | `fc9f0607`, 6 ahead / 0 behind; `test_replay_keeper_strict` 12 passed |

**The composite is a faithful assembly, proven rather than asserted:** `stamp_config_partition.py --check`
re-derives the three-recipe-group map from the committed `run_config*.json` legs, and that map is
**byte-identical to the incumbent keeper's own** `config_partition_overrides`. The two-config structure
the owner ruled on 2026-08-26 is carried exactly.

## 2. What is BLOCKED, and the exact commands

Both of these are refused by the auto-mode classifier with
*"Permission for this action was denied … Reason: [Modify Shared Resources]"*:

```bash
# (a) score the composite — READ-ONLY, but refused
python3 scripts/calibration_verdict.py results/calibration/ercot_mer20260919_five_year

# (b) register it
python3 scripts/dashboard_add_run.py --label "ercot266 mer five year" \
    --bundle results/calibration/ercot_mer20260919_five_year
```

**The determination is therefore UNKNOWN.** No C1–C8 verdict has been computed for this bundle by
anyone. Nothing in this session asserts one, and the promotion must not proceed on an assumption
about it — the owner's own standing rule ("structural integrity up, gates down may still be a keeper")
is a rule about a MEASURED regression, and the measurement has not been taken.

Also expected to need the same permission: `build_manifest.py`, `build_status.py --iso ERCOT`,
`audit_keepers.py --iso ERCOT`, `prune_iso_runs.py --iso ERCOT`, and any write under
`frontend/data/backcast/**`.

## 3. The remaining sequence (rule 35 `[R-PROMOTE]` order — PROMOTE, VERIFY, THEN DELETE)

Rule 35(b) enumeration is already done and is recorded here so the delete cannot destroy it:

> **ERCOT registered year union = {2021, 2022, 2023, 2024, 2025}**, carried by the single registered run
> `2026-09-09-ercot265-receipts-fallback` (bundle `results/calibration/ercot265_receipts_five_year`).
> No folded touchpoint runs exist. **The incoming composite covers that union exactly**, so rule 35(c)
> is satisfied and the promotion does not shrink the ISO's year set.

```bash
# 1. SCORE FIRST — do not promote a bundle whose determination nobody has seen.
python3 scripts/calibration_verdict.py results/calibration/ercot_mer20260919_five_year

# 2. Register (prints RUN_ID and DETERMINATION).
python3 scripts/dashboard_add_run.py --label "ercot266 mer five year" \
    --bundle results/calibration/ercot_mer20260919_five_year

# 3. Attestation for C6. The bundle has NO calibration_attestation.json yet —
#    C6 is protective and fail-closed, so without one the run cannot read CALIBRATED.
#    Model it on results/calibration/ercot265_receipts_five_year/calibration_attestation.json
#    (schema calibration-attestation/v1: free_parameters DOF ledger, exceptions, governance).
#    The DOF ledger carries over VERBATIM — this re-solve changed NO parameter.

# 4. Promote the keeper (ERCOT lane files ONLY — never another ISO's).
python3 scripts/lib/keeper_store.py --set ERCOT <RUN_ID>
python3 scripts/audit_keepers.py --iso ERCOT        # rule 35(e): verify BEFORE deleting
python3 scripts/build_status.py --iso ERCOT

# 5. Re-key calibration-complete.json's ERCOT entry to <RUN_ID>.

# 6. ONLY THEN prune the outgoing keeper (rule 35(a), all three stores together).
python3 scripts/prune_iso_runs.py --iso ERCOT --force-uncite

# 7. Parity + push.
python3 scripts/check_registry_payload_parity.py
```

## 4. Retrievability — a promotion costs ZERO re-solves

The five per-year legs are pushed and recoverable by **full immutable SHA**:

| year | recovery |
|---|---|
| 2021 | `git checkout e702b98b57cd4027f2bb9f74ca96c179fbb04ee3 -- results/calibration/ercot_mer20260919_2021` |
| 2022 | `git checkout b66fd8a49c8895163f6757080c0f0be52ffd6973 -- results/calibration/ercot_mer20260919_2022` |
| 2023 | `git checkout 78422a377d62b73f30cbf98914c215f54ad33c58 -- results/calibration/ercot_mer20260919_2023` |
| 2024 | `git checkout 9ab2461485a9feeb4a9cf191c2216056955e54c6 -- results/calibration/ercot_mer20260919_2024` |
| 2025 | `git checkout a6429ae94eef82079f349a2a75b93a7f257778b5 -- results/calibration/ercot_mer20260919_2025` |

**The expensive part is safe.** ~75 min of shard LP produced those legs and they are on `origin`.
The COMPOSITE (`ercot_mer20260919_five_year`) is on this session's local disk only and will NOT survive
container reclamation — but rebuilding it is **zero-LP and ~10 minutes**: the compose, the stamp, the
diagnostics regen and `--rebuild-benchmark`, all scripted above. Nothing was deleted (rule 31).

## 5. THE UNRESOLVED FINDING THE PROMOTION SITS ON TOP OF

Stated once, not re-litigated — the owner has ruled and this records what the ruling rests on.

These bundles **do not reproduce the incumbent keeper** at HEAD: 2025 is byte-exact (0 of 61,320
zone-hours), while 2021 +0.6332, 2022 +0.2855, 2024 +0.1296 and **2023 +3.6060 $/MWh** (+6.0%)
load-weighted. The cause is localized (a CC_CHP ↔ CC_REGULAR / CT_CHP class reallocation of ~0.08%,
with total generation identical to ~1e-6) but **NOT root-caused**; leading unconfirmed candidate
`760012f7`. Full detail: `RESULT-ercot-mer-keeper-resolve-2026-09-19.md`.

Promoting publishes ERCOT price numbers whose movement has a known size and an unknown cause. 2023's
+6.0% is the one to watch against its registered C3a of −7.3%. **Score before registering (step 1) so
the determination is a measurement rather than a surprise.**
