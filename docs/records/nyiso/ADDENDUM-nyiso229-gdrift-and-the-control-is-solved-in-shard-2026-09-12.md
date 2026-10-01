# ADDENDUM 1 to PRECOMMIT-nyiso229 — the G-DRIFT audit, and why the control is solved IN THE SHARD

**Session:** nyiso-229 · **Date:** 2026-09-12 · **ZERO LP.** Written **before** the arm is solved,
as `PRECOMMIT-nyiso229` §3 requires, so it cannot be written to fit a result.

This changes **one** thing in the PRECOMMIT: G-CTRL moves from **form 4** (difference against the
recovered nyiso-228 control's committed numbers) to **a control solved in the same shard, at the same
SHA, in the same container**. Every gate, the screen year and the reporting rules are untouched.

---

## 1. THE AUDIT — `d4f97391` (the nyiso-228 arm-C control) → `8e71aa54` (HEAD)

```
git diff d4f97391 HEAD -- src/market_sim scripts/run_calibration.py \
  scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

Twelve changed paths. Every one classified, with its reason:

| path | Δ | classification |
|---|---|---|
| `data/raw/_validation-source/README.md` | 2 | **INERT** — prose |
| `data/raw/_validation-source/actual_lmp.json` | +644 | **INERT for NYISO** — a *scoring* instrument, not a solve input, and the added keys are **SPP only**: 16 `"SPP` keys added, **zero** NYISO. Verified by diffing the added lines for every ISO token. |
| `actual_lmp_hourly_SPP.parquet` | bin | **INERT** — SPP |
| `actual_lmp_hourly_zonal_SPP.parquet` | bin | **INERT** — SPP |
| `src/market_sim/model/lp/model.py` | 15 | **INERT** — pure memory management. `_all_cols` becomes `np.ndarray \| None`, released after `h.changeColsCost` and rebuilt lazily on the next pass (118 MB across the solve peak). The **same index vector and the same costs** reach HiGHS; no coefficient, bound, cost or row is touched. |
| `src/market_sim/config/scenarios.py` | +52 | **THIS SESSION'S** — the field + its two cache-key registry entries. Byte-inert at `False` (proven: cache-key agreement 15/15, and the field is dropped at its frozen default). |
| `src/market_sim/data/outages.py` | +28/−1 | **THIS SESSION'S** — the `hour_grain` selector limb. Off ⇒ the same file the selector always returned (proven in all five postures). |
| `src/market_sim/data/fleet/arrays.py` | +10 | **THIS SESSION'S** — threading, gated on both siblings. |
| `src/market_sim/data/resolved_inputs.py` | +5 | **THIS SESSION'S** — provenance only. |
| `scripts/run_calibration_full.py` | +77 | **THIS SESSION'S** (41, the CLI + kwarg threading) **plus the container preflight call** (see below). |
| `scripts/run_calibration.py` | +18 | **the container preflight call** — see below. |
| `scripts/lib/solve_container.py` | +485 | **NEW FILE — the one hunk I will NOT certify INERT.** See §2. |

## 2. THE ONE LIVE-CANDIDATE HUNK, and I am not waving it through

`scripts/lib/solve_container.py` (2026-09-09, rule 32 `[R-SHARD]` clause (c)(8)) is called by
`run_calibration.py` and `run_calibration_full.solve_and_persist` **before the first loader**. It
reads the binding-cgroup ceiling, provisions swap, **and applies a single-thread / arena-pinned solve
profile — `OMP_NUM_THREADS=1` among others.**

Its own header states *"None of it changes the LP: swap and the thread count are workspace choices."*
**That is the file's claim, not a proof, and a claim is not a classification.** The control at
`d4f97391` predates the file, so it solved **without** those pins; an arm at HEAD solves **with**
them. A thread-count change cannot move a coefficient, but it can move which of several **alternate
optima** a degenerate LP lands on — the exact effect the NEISO lane measured and reported (426.95 MW
on a class-hour at identical total generation, mean |price delta| 0.0039 $/MWh). NYISO's LP carries
the rule 9 `[R-EPSILON]` storage tiebreaker precisely because degeneracy is real here.

So: **LIVE, or at least not provably inert.** Under rule 29(b) that is the one thing that earns a
control solve, *"and then only for the years the screen needs"* — which is **2022**, and one year
only.

## 3. THE RESOLUTION IS BETTER THAN A FORM-4 DIFFERENCE, NOT A CONCESSION TO IT

**Both legs are solved in the SAME shard, at the SAME SHA, in the SAME container, from the SAME
committed recipe.** The thread profile, the swap state, HEAD drift, the package set and the container
itself then appear on **both sides and cancel**, so the arm-minus-control difference is **exactly the
one registered field** — which is what the A/B was always supposed to isolate, and what a form-4
difference against a bundle solved in a *different* container at a *different* SHA could not have
given me.

The control basis is the **committed** 2022 touchpoint bundle
`results/calibration/nyiso_fuelvintage_H2` (registry `2026-09-09-nyiso-221-fuelvintage-tp2022`,
`meta.years = [2022]`, `git_sha c430970e`) — the designated keeper's own recipe on 2022, tracked on
`main`, so the shard has it from its clone and needs nothing gitignored. Both legs replay that one
`meta.json` through `scripts/replay_keeper.py`, so the recipe is **literally the same object** and
`--set` applies the single delta:

```
# CONTROL
python3 scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_H2 \
  --years 2022 --out-dir results/calibration/nyiso229_ctrl_y2022
# ARM — the single registered delta
python3 scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_H2 \
  --years 2022 --set unit_outage_window_hour_grain=true \
  --out-dir results/calibration/nyiso229_arm_y2022
```

**Cost:** two 2022 solves in one shard. NYISO's 3-year span ran 13 m 35 s in one shard at nyiso-227,
so one year is ~4–5 min and two legs ~10 min — inside rule 32(b)'s 20-minute budget, which is why
this does not need subdividing.

**What it costs me in evidence, stated plainly:** the nyiso-228 arm-C control span is no longer the
comparator, so this screen says nothing about drift between `d4f97391` and HEAD. That is the right
trade — the screen's question is what the *field* does, and a common-mode container answers it more
cleanly. The drift question is separable, is not this arm's to answer, and §1 already answers it for
every hunk but one.

## 4. WHAT DOES NOT CHANGE

Screen year **2022** (footprint and liveness, never residual). All seven gates verbatim, G-DEMAND
still on **served demand**. The C3c precision/recall reporting rule. The declared-ex-ante price
direction, still not gated on. Rule 16 `[R-ALLYEARS]` if the screen clears. Rule 31 `[R-RETAIN]` —
nothing deleted, and the promotion question is the owner's.
