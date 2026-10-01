# PREREG miso-198 — re-condition the ST_GAS must-run floor LEVEL on the plant's out-of-merit hours (2026-09-01)

**Session:** miso-198. **Keeper:** `2026-08-30-miso-191-bexit`
(`results/calibration/miso191_bax_B`). **Lever:** `st_gas_mustrun_oom_level`
(new field, matrix row + six shard cells added in the same commit, rule 28(c)).
**Legs:** `miso198_control_A` (byte-faithful keeper replay, zero delta) and
`miso198_oom_B` (single delta `st_gas_mustrun_oom_level=true`), years
**2023 2024 2025 in one bundle each** (rule 16).

**This document is committed and pushed BEFORE either leg's result is read.**
The control leg was already solving when it was written; nothing in it is
informed by any solved quantity of either leg.

---

## 1. The object, and how it was identified (published before this prereg)

FINDING-miso197 §8 chartered a re-identification of the existing
`st_gas_mustrun_*` family to the MEASURED out-of-merit level. Two frozen,
blob-verified, zero-solve instruments did that identification, in order:

**(a) The census** — `scripts/probes/_miso198_stgas_oom_conduct_phase0.py`
(rule frozen at `33facea4`, basis repaired and re-frozen at `9ad6b25c`, both
blob-verified before the adjudicating run). It partitioned the ST_GAS gap
between the measured out-of-merit conduct and the keeper's own armed floor
**EXACTLY** — an identity asserted to 1e-6 and measured at 0.0e+00 — into
population / window / level:

| year | measured OOM | armed | gap | P | W | **L** |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 16.059 | 8.213 | 7.846 | 0.162 | 0.197 | **0.640** |
| 2024 | 19.294 | 8.674 | 10.620 | 0.138 | 0.163 | **0.699** |
| 2025 | 17.814 | 8.902 | 8.912 | 0.183 | 0.153 | **0.665** |

**L-3a: DOMINANT = LEVEL, 3 of 3 years over the 0.45 line.** The POPULATION
channel did **not** clear L-3b (5 of its 10 plants fail the operating test), so
the lay-up exclusion census is *not* a clean identification defect and is not
touched. The WINDOW channel never reaches the dominance line. Hence a LEVEL
re-identification of the mechanism that already owns the phenomenon (rule 19
`[R-ONE-MECH]`) and nothing else.

**(b) The selection** — `scripts/probes/_miso198_level_selection.py`, a
criterion frozen and pushed at `88bf6af4` **before any candidate's level or
assertion was computed**. Four candidates, all measured, all from the frozen
estimator, differing only in sample and percentile. Admissible iff **S-i**
conduct-grounded, **S-ii** non-pinning (level ≤ the plant's own median over its
conditioning set), **S-iii** over-assertion share ≤ 1.25× the incumbent's every
year (the D-4 conduct direction, rule 17 `[R-FLOOR-WINDOW]`).

| candidate | raw assertion 23/24/25 (TWh) | over-assertion share | S-i | S-ii | S-iii | |
|---|---|---|:--:|:--:|:--:|---|
| C0 incumbent p25 all-online | 10.523 / 11.022 / 11.086 | .081/.072/.065 | ✗ | ✓ | ✓ | — |
| **C1 p25 out-of-merit** | **9.932 / 10.386 / 10.441** | .070/.067/.057 | ✓ | ✓ | ✓ | **ADMISSIBLE** |
| C2 p50 out-of-merit | 13.975 / 15.010 / 15.185 | .144/.119/.138 | ✓ | ✓ | ✗ | — |
| C3 p50 all-online | 14.816 / 16.068 / 16.230 | .159/.133/.157 | ✗ | ✗ | ✗ | — |

**C1 SELECTED.** The candidates that would have recovered the volume (C2/C3,
+4.0 to +5.1 TWh/yr) buy it by asserting **2.02 / 1.79 / 2.10 TWh/yr in hours
the plants' own meters say they did not operate** — 1.65–2.12× the incumbent's
over-assertion share. Rule 17 verbatim: a floor binding in hours its own driver
evidence says the unit is offline is a bug by definition, whatever it does to
the residual.

**Single-delta verified before any solve.** Rebuilding the fleet through
`run_year`'s own chain with the flag toggled reproduces the selection's
assertions exactly (10.5233/11.0223/11.0863 → 9.9319/10.3857/10.4408 TWh), with
the **same 7 floored plants** and an **identical floored-hour mask**.

## 2. THE INHERITED DIRECTIONAL PREREG IS REVERSED — declared here, before the solve

FINDING-miso197 §8(1) pre-registered, at confidence 0.85: *"C1 CC_REGULAR-2024
DOWN (toward 0) and ST_GAS-2024 UP (toward 0)."*

**The measurement reverses it.** The only admissible level statistic is **lower
than the incumbent at every floored plant** (Sabine 286.1 → 256.1 MW, Nine Mile
Point 724.0 → 688.0, Greenwood 89.0 → 66.0, Lewis Creek 113.5 → 107.7, Harding
Street 226.4 → 218.0, Little Gypsy 53.0 → 50.0, Ames 33.0 → 33.0). So:

**FROZEN DIRECTION FOR THIS ARM:**

1. **ST_GAS-2024 DOWN** (further under, away from 0) and **CC_REGULAR-2024 UP**
   (further over, away from 0). Confidence **0.85**. Magnitude bound: the
   assertion falls **0.591 / 0.637 / 0.646 TWh**, so |Δ class energy| ≤ ~0.65
   TWh/yr per class and the realised conversion is < 1 (miso-196 measured 74 %
   on its own arm).
2. **C3a face: UP** — a *smaller* price-taking floor raises residual demand, so
   the marginal unit moves up the stack. This is the OPPOSITE face from
   miso-193/196, and it is the ONE direction that would help the keeper's sole
   failing criterion (C3a-2025, −12.3405 %, 2.34 pp from the band). **Per rule 1
   `[R-STRUCT]` this is pre-registered and reported, and is NEVER the promotion
   criterion.** It is named here precisely so that a favourable C3a movement
   cannot later be presented as the reason the arm was kept.
3. **C8 face: DOWN (improving).** Less forced energy ⇒ a lower ST_GAS forced
   share. The keeper's grounded 34.2 % in 2025 should fall.

**Why an arm with an adverse C1 face is run at all** (stated against interest):
rule 1 forbids judging a structurally-correct mechanism by whether it improves
the fit, and rule 14 `[R-ACCURATE]` says a more faithful measured input stays in
even when the fit worsens — the worse fit is then a *discovered bug*, not a
reason to revert. The census proved the incumbent statistic measures the wrong
sample; C1 measures the right one. If C1 makes CC-2024 worse, that is the
rule-14 signal that the remaining conduct is not floor-shaped at all — which is
this session's central structural claim (§5).

## 3. Gates

**Sanity (must pass or the A/B is void):**

- **S-0 CONTROL INTEGRITY** — `miso198_control_A` reproduces the keeper's
  12/12 committed sidecars, `max_abs_diff == 0`.
- **S-1 SINGLE DELTA** — the two legs' `run_config.json` differ in exactly
  `st_gas_mustrun_oom_level: false → true`.
- **S-2 FLOOR LIVENESS** — the arm's D-2 `st_gas_mustrun_per_plant` forced
  energy falls in every year, by a magnitude within ±50 % of the pre-registered
  assertion drop (0.591 / 0.637 / 0.646 TWh). Reported UNSCORED, never
  silently passed, if the basis is absent.

**Kills (any one fires ⇒ REJECT; frozen before the solve):**

- **K-1 C1 BAND** — any class-year that PASSES C1 (±8.00 TWh) on the control
  and FAILS on the arm. Named ex ante as the live risk: **CC_REGULAR-2024
  (+6.664 on the keeper, 1.34 TWh of headroom)** and **CC_REGULAR-2023
  (−3.674)**. This is the FINDING-miso197 §8(2) declared adverse face arriving
  through the opposite door.
- **K-2 C3b** — arm NRMSE through 0.20 in any year.
- **K-3 NEW D-4** — any new per-unit conduct failure on the arm.
- **K-4 SHAPE** — ST_GAS D-1 `profile_r` below the 0.80 gate, or `cv_ratio`
  below 0.50, in any year (control: 0.942 / 0.957 / 0.977 and 1.755 / 1.227 /
  1.453).
- **K-5 RECORD FLIPS** — any PASS → non-PASS flip among the scored records
  other than those K-1/K-2/K-4 already name.
- **K-6 DOF** — `n_residual` above the keeper's 2.

**Not gates, reported only:** C3a in all three years (§2.2), C5a `co2`, and the
D-2 forced shares.

## 4. Promotion posture, frozen

- **All kills silent** ⇒ the arm is a **keeper candidate**: it is the
  conduct-grounded statistic, single-delta, zero-DOF, and it *reduces* forced
  energy. Promotion then follows the standard per-ISO lane (keeper shard +
  `build_status.py --iso MISO`), and the C3a movement is reported on the
  determination basis, never cited as the reason.
- **Any kill fires** ⇒ **REJECT**, keeper unchanged, cell `R`, and the finding
  records the reversal and the structural reading of §5. A pre-registered kill
  that fires is not renegotiated (miso-196's standing rule: promoting through a
  fired kill would make the pre-registration decorative).
- **Inert** (every scored record identical) ⇒ cell `I`, keeper unchanged.

## 5. What this A/B decides, and what it hands on either way

**It closes the LEVEL family.** The census says LEVEL is 64–70 % of the gap; the
selection says no admissible level statistic recovers it. Whatever the LP
returns, after this run the honest statement is that **the remaining ~7–10
TWh/yr of measured out-of-merit steam conduct cannot be carried by a level
change to this floor.**

**The named successor, and the mechanism-level reason.** C2 is admissible
*within its own sample* (it IS the median, so half the conduct sits above it)
yet over-asserts 2 TWh/yr **once placed in the floor's window** — because the
floor's window is the top-`online_frac` fraction of hours ranked by SYSTEM LOAD,
while the conduct's own hour set is the plant's commitment state. A level that
is honest in its sample becomes dishonest in a differently-selected window.
**The residual defect is therefore the WINDOW BASIS, not the level** — and the
census's own W channel (15–20 %) *understates* it, because W measures only
energy outside the window, never the window's misplacement. That is the next
charter, and it must not be attempted as another level move.

**Out of reach of this instrument, stated so it is not silently dropped:**
`ST_CHP` measures **0.0004–0.0022 TWh/yr in CAMPD** across 2023–2025 — the class
is effectively invisible to CEMS, so its −2.96/−2.93/−2.13 TWh C1 deficit cannot
be identified by this census at all. It belongs to `chp_steam_following` and its
EIA-923 delivery-implied basis, a different mechanism under a different charter
(rule 19). `CT_CHP` IS visible (9.79/10.46/10.20 TWh measured, L-2b
forward-derivable at a 1.00 stable-energy share) and is a real candidate for the
same treatment on its own mechanism.

## 6. Governance

Rule 22: 2023–2025 only; MISO holds no `complete`/`final` marker; the holdout
freeze is untouched; no marker read or written. Rule 12: solves run in-session,
never CI; the two legs are separate concurrent invocations, years sequential
within each. Rule 15: both legs register on the backcast dashboard in this
session, keeper or rejected. Rule 25: only MISO's shard/keeper/status files are
touched. Rule 28(b): the `st_gas_mustrun_oom_level` MISO cell is stamped with
this A/B's verdict in this session.

## 7. Reproduction

```
python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py --satisfiability
python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py
python3 scripts/probes/_miso198_level_selection.py --satisfiability
python3 scripts/probes/_miso198_level_selection.py --emit
python3 scripts/data/derive_thermal_tranche_oom_level_mw.py --iso MISO --years 2023 2024 2025 --compare
python3 scripts/replay_keeper.py results/calibration/miso191_bax_B --out-dir results/calibration/miso198_control_A
python3 scripts/replay_keeper.py results/calibration/miso191_bax_B --out-dir results/calibration/miso198_oom_B --set st_gas_mustrun_oom_level=true
```
