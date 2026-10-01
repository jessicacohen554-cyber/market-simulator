# PREREG — C8 unit-grain sweep: prediction registered BEFORE the four pending ISOs are measured

**Session:** gpk4xr (NYISO calibration status lane). **Date:** 2026-09-06.
**Instrument:** `scripts/probes/c8_unit_grain_class_basis.py` (unit-grain numerator over
D-2's own `class_total_twh`, so plant grain and unit grain are like-for-like).
**Status when written:** NEISO and NYISO MEASURED and committed; ERCOT, CAISO, MISO, PJM
**NOT YET SOLVED** — the `data/clean` rebuild is still running and the replays are queued
behind it, serially (a concurrent replay was OOM-killed, rc=137).

This file exists so the cross-ISO claim in §2 is a **prediction**, not a post-hoc
rationalisation of numbers already seen. Diagnostic only (rule 13 `[R-MEASURED]`):
nothing is re-scored and C8's committed plant-grain verdict stands.

## 1. The predictor

**Grain exposure is a property of the MECHANISM, not of the plant-grain share.**
`aggregate_floors_by_plant` loses forced energy exactly when a floor pins a *subset of
units inside a plant whose other units run free*. So:

- **Unit-subset floors** — `chp_steam` above all (it floors the CHP steam host beside
  free-running siblings), and `coal_min_config` (a min-config at a multi-unit coal
  station) — should produce a LARGE unit-grain jump.
- **Plant-wide floors** — `reliability_floor`, `coal_mustrun`, `ct_netload_drag`,
  `st_netload_drag`, `winter_fuelsec_mustrun` — should produce a SMALL one.

Calibration points already measured (2024, like-for-like basis):

| ISO | class | mechanism | plant | unit | jump |
|---|---|---|---|---|---|
| NYISO | CC_CHP | `chp_steam` | 0.003 | 0.223 | **~70×** |
| NYISO | ST_GAS | `reliability_floor` (+bridge) | 0.224 | 0.312 | 1.4× |
| NEISO | CC_REGULAR | `reliability_floor` | 0.008 | 0.014 | 1.8× |

The two plant-wide floors moved by <2×. The one unit-subset floor moved by ~70×.

## 2. The predictions (falsifiable, per ISO, on gated material classes)

Materiality is C8's own ≥2 %-of-ISO-load floor; classes the committed scorer already
skips as immaterial are excluded (PJM `ST_GAS` 1.4 %, CAISO `ST_GAS` 0.6 %, etc.).

| # | ISO · class | TWh | mechanism | plant | prediction |
|---|---|---|---|---|---|
| P1 | MISO · CC_CHP | 18.11 | `chp_steam` | 0.193 | **BREACHES 0.30** — highest confidence |
| P2 | ERCOT · CC_CHP | 28.51 | `chp_steam` | 0.449 | already over; goes HIGHER (not a new verdict) |
| P3 | CAISO · CC_CHP | 7.54 | `chp_steam` | 0.592 | already over; goes HIGHER (not a new verdict) |
| P4 | PJM · **no gated class breaches** | — | plant-wide only | — | **PJM stays clean** |
| P5 | ERCOT · CC_REGULAR | 143.88 | `gas_commitment_bridge` | 0.008 | no breach |
| P6 | MISO · COAL | 170.00 | `reliability_floor` | 0.003 | no breach |
| P7 | PJM · CC_REGULAR | 335.87 | `cc_mustrun_per_plant` | 0.032 | no breach |
| P8 | MISO · CT_PEAKER | 11.50 | `reliability_floor` | 0.183 | no breach (weak) |
| W1 | ERCOT · COAL | 56.81 | `coal_min_config` | 0.082 | **WATCH** — unit-subset mechanism, large denominator |
| W2 | CAISO · CC_REGULAR | 46.26 | `ra_mustoffer_bridge` | 0.067 | **WATCH** — genuinely uncertain |

**A single wrong call on P1–P8 falsifies the predictor** and the §3 reading has to be
withdrawn with it.

## 3. What it means for the nyiso-193 ruling, if the predictor holds

Re-basing D-2/C8 to unit grain (option A) does **not** produce a wave of new
determination failures. It concentrates a new obligation in one place: the **CHP steam
floors of ERCOT, CAISO, MISO and NYISO**, whose classes would sit above the cap and
therefore need rule 20's conditional-pass path — a cited `D4_WINDOWS` entry plus a
clean D-1 shape — before those ISOs' C8 could read PASS again.

So the ruling's real cost is **grounding `chp_steam`'s D-4 window in four ISOs**, not a
determination cliff. That is a bounded, well-specified piece of work, and it is a
different (and much smaller) thing than the card's framing implies. PJM, on this
prediction, is unaffected either way.

## 4. What this file does NOT claim

It does not recommend A or B — that is the owner's ruling on
`docs/DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md`. It does not re-score any
criterion. It does not touch a keeper, a marker, or a matrix cell. The replay bundles
live in the gitignored `scratch/` tree and are never registered (rule 29(c)).
