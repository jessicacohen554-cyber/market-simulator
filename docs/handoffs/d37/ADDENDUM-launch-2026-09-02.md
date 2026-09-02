# ADDENDUM A — capx D37 launch record (appended AFTER the pre-declaration was pushed, BEFORE any result was read)

This file records two pre-solve events. **It amends no prediction.** The frozen
predictions in `PREDECL-capx-d37-neiso-t1h-armed-2026-09-02.md` §3 stand exactly as
pushed (commit on `claude/capx-d37-neiso-t1h-armed-o98iy1`, blob-verified: 365 lines,
sha256 `1d32c222…`); nothing below touches them, and both entries were written before any
ledger, score or position from either arm had been read.

## A.1 The pre-solve cache-key table was resolved one layer too shallow — CORRECTED, and every predicted RELATIONSHIP holds

Pre-declaration §1.1 predicted the ARM would key at `0c08990cce1f1a18` and the CONTROL at
`17f74b5ffc1808c9`, and said in terms that *"a realized key differing from the table above is
itself a reportable finding."* The realized keys are **`313ba0612435b963`** (ARM) and
**`5925e67c572a910f`** (CONTROL). Reporting it, with the cause pinned:

**Cause: my pre-solve resolution called `build_config(...)` and hashed that, but the runner
hashes the config only AFTER `apply_iso_scenario_defaults(config, "NEISO")`.** Applying that
one missing layer reproduces both realized keys **exactly**:

| arm | `build_config` alone | `+ apply_iso_scenario_defaults` | realized in the run |
|---|---|---|---|
| ARM (D37 posture) | `0c08990cce1f1a18` | **`313ba0612435b963`** | **`313ba0612435b963`** ✓ |
| CONTROL (diag only) | `17f74b5ffc1808c9` | **`5925e67c572a910f`** | **`5925e67c572a910f`** ✓ |

So this is an **instrument error in my pre-solve arithmetic, not a disagreement between the
config the run resolved and the config the posture intended.** The corrected table at the
runner's own layer:

| arm | `entry_screen_diagnostics` | `neiso_net_icr_requirement` | cache key |
|---|---|---|---|
| bare HEAD | False | False | `b0fcad25a90a6449` |
| diagnostics only (**CONTROL**) | **True** | False | **`5925e67c572a910f`** |
| lever only | False | **True** | `714440df53e1ffac` |
| **ARM (D37 posture)** | **True** | **True** | **`313ba0612435b963`** |

**Every relationship the pre-declaration relied on survives the correction, re-measured at the
correct layer:** the lever moves the key; the diagnostics flag moves the key (so §1.2's
finding that the D36/D39 *"no cache-key term"* claim is **FALSE** stands — `b0fcad25a90a6449`
→ `5925e67c572a910f`); ARM ≠ CONTROL; and **neither collides with any committed NEISO bundle**
(`e118e887b306da37`, `b50062a643832c25`). Both runs' logs confirm the intended posture
directly — ARM `'neiso_net_icr_requirement': True`, CONTROL `False`, both
`'entry_screen_diagnostics': True` — so the A/B is one field apart as designed, and the
stale-bundle guard (fresh out-dirs + `CACHE_ROOT` redirect) is discharged as written.

## A.2 Both arms failed fast on absent derived data, and were relaunched after regenerating it

The first launch of both arms aborted within seconds, identically:

```
RuntimeError: confirmed-retirements: clean partition for NEISO is absent while
confirmed_exits_enabled is on in forecast mode. data/clean is derived and gitignored,
so a fresh checkout has no registry; refusing to silently degrade to the economic screen
```

This is the guard doing its job on a fresh session checkout — `data/clean` is derived and
disposable by design (CLAUDE.md's data tree), and this container had none. Remedy, exactly as
the error prescribes: `scripts/data/curate_confirmed_retirements.py` (5 partitions written;
**NEISO 16 rows, 16 live**), with `scripts/regenerate_clean.py` — the sanctioned single
entrypoint — run alongside for the remaining datatypes. **No configuration, flag or constant
was changed to get past it**; the failed out-dirs were deleted so each arm relaunched into a
verified-empty directory, preserving the guard of §1.1.

Relaunched 2026-09-02 16:13Z (ARM) and 16:15Z (CONTROL), both past the data-load stage and
into the solve, at the keys in A.1.
