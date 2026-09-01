# FINDING miso-198 — the out-of-merit steam conduct is REAL, LEVEL-shaped in its accounting and NOT level-repairable: the floor's window basis is the binding defect (2026-09-01)

**Session:** miso-198 (2026-09-01). **Keeper:** `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`). **Charter:** the FINDING-miso197 §8
named successor — re-identify the existing `st_gas_mustrun_*` / steam-host
conduct family to its MEASURED out-of-merit level (rule 19 `[R-ONE-MECH]`;
rule 13 `[R-MEASURED]` multi-year CAMPD derivation).

**Two zero-solve instruments, each with its rule frozen in its own docstring and
pushed + blob-verified BEFORE any adjudicating quantity, decided this session's
load-bearing question. Neither weighed anything against a price residual
(rule 1 `[R-STRUCT]`); C3a appears only as a pre-registered direction.**

---

## 1. The answer, in one paragraph

The out-of-merit conduct is real and large — **16.06 / 19.29 / 17.81 TWh/yr** of
measured ST_GAS energy in hours the model's own merit order says the class
should be off — and the keeper's armed floor asserts only about half of it, so
the **gap is 7.85 / 10.62 / 8.91 TWh/yr**. That gap partitions EXACTLY (an
identity, measured residual 0.0e+00) into population / window / level, and
**LEVEL is dominant in all three years (0.640 / 0.699 / 0.665)**. But when the
level family is then enumerated under a criterion frozen before any candidate's
number, **only the most conservative candidate is admissible, and it is LOWER
than the incumbent** — the two candidates that would recover ~4–5 TWh/yr buy it
by asserting **2.0–2.1 TWh/yr in hours the plants' own meters say they did not
operate**, 1.65–2.12× the incumbent's over-assertion share, which rule 17
`[R-FLOOR-WINDOW]` makes a bug by definition. The reason is structural and is
this session's real result: **a level that is honest inside its own sample
becomes dishonest once placed in the floor's window**, because the floor's
window is the top-`online_frac` fraction of hours ranked by SYSTEM LOAD while
the conduct's own hour set is the plant's COMMITMENT STATE. The two sets only
partly overlap. **The level family is therefore exhausted, and the binding
defect is the WINDOW BASIS.** The inherited directional pre-registration
(CC-2024 down / ST_GAS-2024 up) is **reversed** on this measurement, and the
reversal was declared in writing before the A/B solved.

## 2. The measured conduct object (M-1)

`scripts/probes/_miso198_stgas_oom_conduct_phase0.py`; record
`_miso198_stgas_oom_conduct_phase0.json`. The conditioning set is inherited
verbatim from miso-197 W3b — hours in which the measured MISO `CC_REGULAR`
fleet ran below **0.90** of its own **p99.5** that year, i.e. cheaper CC
capability demonstrably idle. Purely measured: no model dispatch, no price.
7,726 / 7,706 / 7,757 of 8,760 hours qualify.

| class | measured actual TWh 23/24/25 | measured OOM TWh 23/24/25 |
|---|---|---|
| ST_GAS | 20.59 / 24.39 / 22.42 | **16.06 / 19.29 / 17.81** |
| CT_CHP | 9.79 / 10.46 / 10.20 | 8.65 / 9.32 / 9.04 |
| ST_CHP | 0.0004 / 0.0004 / 0.0022 | ~0 |

**Forward-derivability (M-2) passes for ST_GAS**: stable plants (annual
`oom_level_mw` spread ≤ 0.35) carry **0.812** of the class's pooled OOM energy
against a 0.60 line, and 15 of 22 plants are pooled-representative. CT_CHP also
clears (1.00). **ST_CHP does not, and cannot** — see §6.

## 3. WHERE the identification loses it (M-3): the exact partition

`meas` is the measured net MW and `flr` the keeper's own armed
`MECH_ST_GAS_MUSTRUN_PER_PLANT` floor, both restricted to the out-of-merit
hours. `P` is measured energy at plants carrying no floor at all, `W` at
floored plants in hours the floor is zero, `L` the measured energy above the
floor in floored hours. `P + W + L == measured_oom − armed_in_oom` by
construction.

| year | measured OOM | armed | gap | P | W | **L** | O (over-assertion) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 16.059 | 8.213 | 7.846 | 1.274 (.162) | 1.548 (.197) | **5.024 (.640)** | 0.836 |
| 2024 | 19.294 | 8.674 | 10.620 | 1.468 (.138) | 1.733 (.163) | **7.420 (.699)** | 0.772 |
| 2025 | 17.814 | 8.902 | 8.912 | 1.628 (.183) | 1.360 (.153) | **5.924 (.665)** | 0.706 |

- **L-3a: DOMINANT = LEVEL**, 3 of 3 years over the 0.45 line.
- **L-3b: the POPULATION channel is NOT a clean identification defect.** The
  `mustrun_plant_exclusions` lay-up census excludes 9 of 16 artifact ST_GAS
  plants, and the census's own operating test (≥1,000 online hours AND ≥0.05
  TWh in ≥2 of 3 years) is cleared by only **5 of the 10** plants in the
  channel — R D Green 6639, Gerald Andrus 8054, Waterford 8056, Laskin 1891,
  Blount 3992 clear it; Lake Catherine 170, Burlington 1104, Streeter 1131,
  1400 and Dan E Karn 1702 do not. **So the exclusion census is not repaired
  here.** (It remains true that the census's stated distinguisher — "the
  per-cell quantifier is what distinguishes lay-up from a low capacity factor"
  — cannot separate a cycler online < 50 % in every 4-hour block from a
  mothball: R D Green reads `laid_up=True` at an `online_share` of 0.326 with
  0.42 TWh/yr on the meter. That is a real, named, **partly**-confirmed
  observation and it is handed on, not acted on, because L-3b did not clear.)
- **INSTRUMENT DEFECT, FOUND AND REPAIRED BEFORE THE ADJUDICATING RECORD,
  disclosed rather than absorbed.** The first census run called
  `generators_to_fleet_arrays` without `load_shape`, and the runtime's floor
  block falls through to `target[:] = level` when the load rank is absent
  (`arrays.py:2841`) — so the floor spanned all 8,760 hours instead of the
  plant's measured window, collapsing W to ~0 and pushing its content into L.
  The solve passes `load_shape=demand.sum(axis=0)`
  (`run_calibration.py:3176`); the repair reads exactly that vector from the
  keeper's committed `hourly/system_<year>` sidecar. **What it changed:** W
  0.355/0.118/0.099 → 1.548/1.733/1.360 and L 5.584/8.276/6.394 →
  5.024/7.420/5.924. **What it did not change: the verdict.** L stays dominant
  3 of 3. The repair was pushed and blob-verified (`9ad6b25c`) before the
  record above was written. Independent confirmation that the repaired
  reconstruction is byte-faithful to the solve: the control leg's own log
  prints `ST_GAS p25-level floor (MISO 2023): floored 7 plant(s), 10.52 TWh`
  against the probe's 10.5233 TWh.

## 4. The level family is EXHAUSTED (the selection)

`scripts/probes/_miso198_level_selection.py`, criterion frozen and pushed at
`88bf6af4` **before any candidate's level or assertion was computed**; record
`_miso198_level_selection.json`. Four candidates, all measured, all from the
frozen estimator, differing only in sample and percentile. Each candidate's
assertion is measured by rebuilding the FleetArrays through `run_year`'s own
chain with ONLY the level map swapped, so window, membership, availability clip
and lay-up mask are the runtime's own.

| candidate | raw assertion 23/24/25 (TWh) | over-assertion share | S-i conduct-grounded | S-ii non-pinning | S-iii ≤1.25× incumbent | |
|---|---|---|:--:|:--:|:--:|---|
| C0 incumbent p25 all-online | 10.523 / 11.022 / 11.086 | .081 / .072 / .065 | ✗ | ✓ | ✓ | — |
| **C1 p25 out-of-merit** | **9.932 / 10.386 / 10.441** | .070 / .067 / .057 | ✓ | ✓ | ✓ | **ADMISSIBLE** |
| C2 p50 out-of-merit | 13.975 / 15.010 / 15.185 | .144 / .119 / .138 | ✓ | ✓ | ✗ | — |
| C3 p50 all-online | 14.816 / 16.068 / 16.230 | .159 / .133 / .157 | ✗ | ✗ | ✗ | — |

**C2 is the one that would have delivered the charter's target** (+3.99 / +3.99
/ +4.10 TWh of assertion, against the inherited ≥4 TWh CC-2024 requirement) —
and it fails, not marginally: it asserts **2.02 / 1.79 / 2.10 TWh/yr in hours
the meter says the plant made less or nothing**, i.e. **about half the volume it
buys is bought by contradicting the plants' own record.**

**Why the median over-asserts even though half its own sample sits above it.**
The level's sample is the out-of-merit hour set; the floor's window is the
top-`online_frac` fraction of hours ranked by SYSTEM LOAD. A statistic that is
non-pinning inside its own sample is placed, at runtime, in a *differently
selected* set of hours. **That mismatch — window basis, not level — is the
binding defect**, and the census's own W channel (15–20 %) understates it,
because W measures only energy *outside* the window and never the window's
*misplacement*.

## 5. What was built, and the reversal

`ScenarioConfig.st_gas_mustrun_oom_level` (GATED, default off) replaces the
level SOURCE in the same slot inside the existing `st_gas_mustrun_p25_level`
block — membership, window, mechanism id and the cheapest-first
`pmax × availability` clip untouched (rule 19), zero free parameters (rule 21),
frozen deriver untouched (rule 23). Deriver
`scripts/data/derive_thermal_tranche_oom_level_mw.py`; artifact
`thermal_tranches_oom_level_mw_MISO.csv`; accessor
`campd_bins.thermal_tranche_oom_level`; test
`tests/unit/data/test_st_gas_oom_level.py` (9 cases). Matrix row + a cell in all
six ISO shards, same commit (rule 28(c)). Cache-key neutral (default key
`7a57fadff595ca83` with and without the field).

**Single-delta verified before any solve**: toggling the flag on `run_year`'s
own fleet chain reproduces the frozen selection's assertions exactly
(10.5233/11.0223/11.0863 → 9.9319/10.3857/10.4408 TWh) with the same 7 floored
plants and an identical floored-hour mask.

**THE INHERITED DIRECTION IS REVERSED, declared before the solve**
(PREREG-miso198 §2). FINDING-miso197 §8(1) pre-registered CC_REGULAR-2024 DOWN /
ST_GAS-2024 UP at confidence 0.85. The admissible level is lower than the
incumbent at every floored plant (Sabine 286.1 → 256.1 MW, Nine Mile Point
724.0 → 688.0, Greenwood 89.0 → 66.0, Lewis Creek 113.5 → 107.7, Harding Street
226.4 → 218.0, Little Gypsy 53.0 → 50.0, Ames unchanged), so this arm moves
**ST_GAS DOWN and CC_REGULAR UP**, bounded by the 0.591 / 0.637 / 0.646 TWh
assertion drop. The C3a face is pre-registered **UP** — the one direction that
would help the keeper's sole failing criterion — precisely so that a favourable
movement can never be presented as the reason the arm was kept (rule 1).

## 6. Out of reach of this instrument (named so it is not silently dropped)

**`ST_CHP` is effectively invisible to CEMS**: 0.0004 / 0.0004 / 0.0022 TWh
measured across 2023–2025 against a C1 deficit of −2.96 / −2.93 / −2.13 TWh. No
CAMPD-conditioned statistic can identify it. Its floor is `chp_steam_following`
on an EIA-923 delivery-implied basis — a different mechanism under a different
charter (rule 19). Its D-1 `profile_r` is **negative in every year**
(−0.809 / −0.733 / −0.650, ungated), which is a standing shape signal for that
lane. **`CT_CHP` IS visible** (9.79 / 10.46 / 10.20 TWh measured, L-2b
forward-derivable at a 1.00 stable-energy share) and is a real candidate for
the same treatment on its own mechanism.

## 7. Handed on

1. **The WINDOW BASIS of the per-plant must-run floors** (§4) — the named
   successor. It must NOT be attempted as another level move. Note that
   `mustrun_online_frac_per_year` (window *vintage*) is already **R** at MISO,
   and that a same-year meter-derived window is backcast-only under rule 13, so
   the successor needs a window basis that is forward-regenerating and is not
   the system-load ranking.
2. **The lay-up exclusion census's cycler/mothball boundary** (§3, L-3b) —
   partly confirmed, not cleared, not acted on.
3. **`CT_CHP`** as the visible half of the steam-host family (§6).
4. Unchanged from miso-197: the standing wind +5 TWh/yr over EIA-930, the 2023
   import +2.0 TWh face, the `_CC_PMAX_RECONCILED_PLANTS` order-dependence and
   the `run_year`-vs-`assembly` fleet-chain divergence.
5. **Not this lane's, but blocking others:** 11 `tests/unit/config` cache-key
   pin tests FAIL on clean HEAD `a40cfc68` — the capx-d24 cache-key-defect
   repair that landed 2026-09-01 deliberately moved the default key
   (`603c2498bf71d21d` → `7a57fadff595ca83`, owner ruling Q20 option b′-1) and
   its literal pins were not updated. Verified pre-existing by stashing this
   session's changes. Untouched here.

## 8. Governance

Rule 22: 2023–2025 only; MISO holds no `complete`/`final` marker; the holdout
freeze untouched; no marker read or written. Rule 12: solves run in-session,
never CI. Rule 25: only MISO's shard is edited. Rule 27: every push touching a
≥300-line file was blob-verified against the remote.

## 9. Reproduction

```
python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py --satisfiability
python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py
python3 scripts/probes/_miso198_level_selection.py --satisfiability
python3 scripts/probes/_miso198_level_selection.py --emit
python3 scripts/data/derive_thermal_tranche_oom_level_mw.py --iso MISO --years 2023 2024 2025 --compare
python3 -m pytest tests/unit/data/test_st_gas_oom_level.py
```
