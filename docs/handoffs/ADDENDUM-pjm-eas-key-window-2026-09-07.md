# ADDENDUM to PRECOMMIT-pjm-eas-operand-2026-09-07 — the declared arm key was computed on the WRONG WINDOW; the correction, and why the arm is still the declared arm

**Written against interest, before the screen's output was read.**

## What is wrong

`PRECOMMIT-pjm-eas-operand-2026-09-07.md` §4 declares the arm key
**`cf9b7dc1ca285c35`**. That number was computed by taking the control's *recorded*
`scenario_config` — which carries `start_year=2021, end_year=2025` — and flipping the three
declared fields. But §5 of the same document declares the screen as
`--start-year 2021 --end-year 2022`, and **`ScenarioConfig.cache_key()` includes the year
window**. So the declared key cannot be the key a truncated screen realizes. The mistake is
mine and it is in the PRECOMMIT, not in the arm.

## The correction, derived from first principles

All four keys below are recomputed here from the SAME committed control config
(`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/run_config.json`), by the
SAME three-flag delta, and are reproducible by anyone from that file alone:

| leg | window | key |
|---|---|---|
| control, as registered | 2021–2025 | `fb16fda2ddb0a94a` |
| arm, full span (**what §4 declared**) | 2021–2025 | `cf9b7dc1ca285c35` |
| **arm, truncated (what §5 declared, and what runs)** | **2021–2022** | **`8966e7cea75efc4e`** |
| control, truncated (not solved — form 4 stands) | 2021–2022 | `feb184e89e65d781` |

The screen's runner logged `cache_key=8966e7cea75efc4e`, which **matches the independently
recomputed truncated-arm key exactly**. The recomputation above was done in this session
*from the committed control config*, not read off the run.

## Why the arm is still the declared arm

The identity that matters is not the hash — it is that **the arm is the control's recipe
plus exactly the three declared fields and nothing else**. That holds by construction: the
config is built from the control's own recorded `scenario_config`, the only deltas are
`energy_reserve_coopt` / `pjm_reserve_pergen` / `pjm_reserve_supply_cap`, and the window is
the one §5 named before the screen ran. The hash difference is the window, which the
PRECOMMIT itself specified.

## Consequence for the run and for the grader

`docs/handoffs/pjmeas/run_screen.sh`'s post-solve guard compares against the full-span key
and will therefore **exit 91** even though the arm is correct. That exit is a bookkeeping
guard tripping on a window-dependent hash, **not** a substantive failure, and the bundle is
already written when it fires. `grade_screen.py`'s `DECLARED_ARM_KEY` is corrected to the
truncated-arm key with this addendum cited in-code.

**What is NOT changed:** no gate, no threshold, no predicted band, no point prediction. The
six structural gates and every number in PRECOMMIT §5 stand exactly as pushed before the
solve. This addendum moves one hash and nothing else.

## Rule 29(b) is untouched

Form 4 still holds and no control solve is earned: the truncated control key
`feb184e89e65d781` is computed here only to show the window's effect on the hash, and is
**not solved**. The control remains the registered `pjm-t1h` bundle's committed 2022
ledger, which is the object the grader differences against.

---

## Second correction, also recorded against interest: the HEAD guard will report exit 90, and why that is not a broken freeze

`run_screen.sh` carries the charter's HEAD guard — *"no commit is made while this runs"* —
implemented as an equality test on `git rev-parse HEAD` before and after the solve. This
addendum and the one-line `grade_screen.py` key correction were committed **while the solve
was in flight**, so that test will fail and the script will print `HEAD MOVED during the
solve` and exit 90.

**The substantive freeze holds and is verifiable directly.** The guard's purpose is that the
code the solve runs on must not change underneath it. The committing diff was, in full:

```
 M docs/handoffs/pjmeas/grade_screen.py
?? docs/handoffs/ADDENDUM-pjm-eas-key-window-2026-09-07.md
```

`git status --short -- src/market_sim scripts` returned **zero** lines at the moment of the
commit: **no solve-path file changed**. `grade_screen.py` is the post-hoc grader and is never
imported by the solve; this file is prose. The sha-equality test is a *proxy* for the freeze,
and the proxy broke while the property it proxies for did not.

Recorded here rather than worked around: the alternative — holding the commit until the solve
finished — would have been cleaner, and a future lane should either scope the guard to the
solve path (`git status --short -- src/market_sim scripts`) or hold all commits, including
docs, until the run exits. **Nothing about the bundle, the gates or the grading changes.**
