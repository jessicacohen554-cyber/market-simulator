# RESULT — SPP-48 (2026-09-19): the mid-vintage-year retiree gap, repaired and solved

**Base:** `4583e70b864a7d5c99a206b06eddf3c36af495bf`. **Lane branch:**
`claude/spp-mid-vintage-retiree-gap-vv07l6`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`) — **UNCHANGED, and proven
un-movable by this lane.**
**Run registered:** `2026-09-19-spp-48-midvintage-exit` (`results/calibration/spp48_arm_span`,
2019–2022). **Determination NOT-YET**, same failing set as the control.
**Method and full phase-0 measurement:** `PRECOMMIT-spp-48-midvintage-exit-2026-09-19.md`
(including Addendum A).

---

## 0. Headline

1. **SPP-47's root cause reproduces exactly — but it is ONE false assumption living at THREE
   seams, not one.** Fixing only the seam SPP-47 named produces a *structurally wrong* input:
   Oklaunion comes back online in **all twelve months of 2020**, three of them after it retired.
2. **The arm is LIVE and CONFINED.** Repaired at all three seams, the plant is available
   **May–September only**, on an envelope covering the CAMPD-metered generation in every month and
   **zero in exactly the months metered generation is zero**.
3. **Every criterion the arm moves, it improves; none degrades; nothing closes.** C1-2020
   `COAL_PRB` −10.85 → **−10.01 TWh**, still a clear FAIL — as pre-declared.
4. **The blast radius is SPP alone**, established before the shared seam was touched, from a
   code-level gate plus a census of **all 227 committed `run_config` records**.
5. **SPP-47 §2.2 is REFUTED**, and it matters: the *benchmark* drops the same plant by a
   **different** defect that this repair does not fix — and folding that in would have shrunk a
   failing criterion by deleting real metered generation. Filed as the named successor.

---

## 1. What was wrong, and the three seams

`load_retired_within_window`'s docstring states the assumption verbatim: *"the operable fleet
already has them."* True of a plant retiring **after** the vintage year; **false** of one retiring
**during** it, because that vintage's operable sheet is a **year-end** snapshot that has already
moved the plant to the Retired-and-Canceled sheet. The plant is then in **neither** sheet the
channel reads.

Oklaunion (plant 127, 720 MW nameplate / 650 MW summer, `ba_code SWPP`, EIA retirement **9/2020**)
is in the 2019 LP fleet and absent from 2020–2022, against **1,209.2 GWh** metered May–September
2020. EIA's own vintages pin it: `vintage_2019` operable **OP** with planned retirement 9/2020;
`vintage_2020` retired-and-canceled **RE**, retirement 9/2020.

| seam | what it drops | measured state of Oklaunion 2020 after fixing up to here |
|---|---|---|
| 1. the injection gate (`_mid_vintage_exit_rows`) | the plant, entirely | online **all 12 months** — a rule 17 `[R-FLOOR-WINDOW]` violation |
| 2. `fleet_to_bins` (the miso-191 defect) | the unit's own EIA-860 retirement | **Jan–Sep**, ids `COAL_SPP-North_p127_r202009_*` |
| 3. the outage derate **denominator** | the plant's own measured outage rows | **May–Sep**, 3,933.2 → **1,936.3 GWh** available |

Seam 3 matters because the committed `campd-unit-outages-SPP.csv` **already carries** Oklaunion's
real stops — `2020-01-01 → 2020-05-19` and `2020-09-26 → 2020-12-31` — matching CAMPD exactly, and
`outages._iso_plant_capacity`'s own comment predicts precisely this failure mode.

**The resulting envelope, against the meter:**

| | May | Jun | Jul | Aug | Sep | other |
|---|---|---|---|---|---|---|
| available GWh | 181.0 | 454.0 | 469.1 | 469.1 | 363.2 | **0.0** |
| metered GWh | 92.5 | 222.6 | 288.9 | 334.9 | 270.2 | **0.0** |
| implied CF | 0.511 | 0.490 | 0.616 | 0.714 | 0.744 | — |

Covers the meter in every month; zero in exactly the zero-metered months. **1,936.3 GWh available
against 1,209.1 metered (0.624).**

---

## 2. Blast radius — SPP alone, measured before the shared seam was touched

The channel is **backcast-only** (both call sites gate on `mode == "backcast"`). A backcast reaches
a native vintage only through `eia860_vintage_tracks_solve_year`, and across **all 227 committed
`run_config` records only SPP arms it**. Every explicit `eia860_vintage_year` pin (39 records) is a
`mode="forecast"` hindcast, which never reaches this channel.

Potential exposure elsewhere is large but **not live** — their canonical retiree parquet already
carries these plants (MISO 17/17, PJM 12/12, NEISO 2/2, SPP 2/2):
MISO 13,547.5 GWh · PJM 6,885.3 · NYISO 365.7 · **SPP 1,257.0** · CAISO 33.8 · ERCOT 11.3 ·
NEISO 4.8 · SOCO 0 · NWPP 0.

**The keeper cannot move**, by construction and by test: `vintage_2023/` and `vintage_2024/` ship
**no Retired-and-Canceled sheet at all** and 2025 has no vintage directory, so 2023/2024/2025 are
byte-identical on all 14 `FleetArrays` LP inputs. The gate is default-off and **not** armed in
`_spp_config`.

---

## 3. What the solve did

Fleet effect (control = the committed rung, differenced):

| year | units | Δ pmax | plant 127 |
|---|---|---|---|
| 2019 | 1126 → 1134 | +13.613 MW | present both sides, unchanged |
| **2020** | 1110 → 1127 | **+931.600 MW** | **absent → 5 tranches, 650.000 MW** |
| 2021 | 1109 → 1109 | 0.000 | absent both sides |
| 2022 | 1094 → 1109 | +54.000 MW | absent both sides (Ponca; zero-reach per SPP-45) |

### 3.1 Criteria — like-for-like, same benchmark frame

Verified rather than assumed: the arm bundle resolves `eia923-cda580e2f71c`, **the same frame the
control uses**, which carries plant 127 at 1,209,201 MWh and a 2020 `COAL_PRB` actual of
67.0581 TWh. **No part of the movement below is a changed denominator.**

| criterion | control | arm | |
|---|---|---|---|
| **determination** | NOT-YET | NOT-YET | unchanged |
| C1 2020 `COAL_PRB` | −10.85 TWh, −4.0 pp | **−10.01 TWh, −3.7 pp** | improves, **still FAIL** |
| C1 2022 `COAL_PRB` | +8.01 TWh, +2.3 pp | +8.01, +2.3 pp | unchanged |
| C3a 2020 | +24.0 % | **+23.4 %** | improves, still FAIL |
| C3b 2020 | NRMSE 0.319 | **0.316** | improves, still FAIL |
| C3b 2021 / 2022 | 0.213 / 0.213 | 0.213 / 0.213 | unchanged |
| C4 2022 gas | r 0.957, NRMSE 0.312 | identical | unchanged |
| C5a CO2 2020 *(reported-only)* | +17.5 % | **+16.4 %** | improves |
| C2 · C6 · C8 | PASS | PASS | held |

Failing set **unchanged**: {C1, C3a, C3b, C4}.

### 3.2 Reported at full magnitude — two classes degrade

Inside C1 at **class** grain (2020), where the banded rows do not show it:

| class | control miss | arm miss | |
|---|---|---|---|
| `COAL_PRB` | −10.8484 | **−10.0129** | +0.8355 improve |
| `CT_PEAKER` | +6.7508 | **+6.3680** | improve |
| `CC_REGULAR` | +3.9269 | **+3.7332** | improve |
| `ST_GAS` | −5.3599 | **−5.5365** | **degrade** |
| `COAL_LIGNITE` | −2.6650 | **−2.7235** | **degrade** |

Energy conserved to **0.001 TWh** on 262.64 TWh. Oklaunion delivered 0.8355 TWh of its 1.2092 TWh
of metered generation (69 %), displacing peakers and gas rather than replacing coal.

System: 2020 load-weighted price **20.4872 → 20.3776 $/MWh** (−0.53 %), max 40.78 → 36.59;
2022 slack **563.6284 → 501.3472 MWh**; 2019/2021 unchanged; **dump 0.0000 everywhere**.

---

## 4. SPP-47 §2.2 is refuted — the benchmark is a SEPARATE defect

SPP-47 predicted the benchmark question becomes moot once the fleet carries Oklaunion. **It does
not.** Two copies of the rung bundle differing **only** in `mid_vintage_exit_carry` rebuild to the
**same** content-addressed EIA-923 frame.

Root cause, in a different seam: the benchmark's ISO membership is `_iso_plant_ids` →
`zone_assignment.build_zone_lookup`, built from **eGRID-2023 coordinates** supplemented from the
**canonical (2025ER)** EIA-860 plant file. Neither knows a plant that retired in 2020, the
supplement is **forward-only** by its own docstring, and the lookup **does not follow**
`eia860_vintage_tracks_solve_year` — measured at 830 plants with 127 absent under *every* vintage,
one interpreter per vintage.

The asymmetry is the point: the **LP fleet** has a fallback-zone path for a plant eGRID lacks; the
**benchmark** has a hard `isin` filter with none. So a mid-window retiree can be **in the model and
out of the actual at once**.

A HEAD `--rebuild-benchmark` would move the 2020 `COAL_PRB` actual **67.0581 → 65.8489 TWh**,
improving the failing row by 11.1 % **entirely by deleting 1,209,201 MWh of real metered
generation**. Refused (rules 13 / 14) and filed as the successor. **This run is unaffected** — it
resolves the committed frame, checked rather than assumed.

---

## 5. Governance

* Rule 14 `[R-ACCURATE]` is the whole basis; the residual is not. Built and gated before any LP.
* Rules 21 / 24: **zero free parameters** — one boolean whose membership is a set difference over
  EIA's own two published sheets and whose timing is EIA's own published retirement month.
  `check_cache_key_registration.py` passes.
* Rule 19 `[R-ONE-MECH]`: membership is the strict complement of the partial-exit channel's; the
  exit-cohort router is **reused**, each membership behind its own flag.
* Rule 25 `[R-ISO-SCOPE]`: default OFF, **not** armed in `_spp_config`. Off-path byte-identity is
  structural — every widened outage call is made at its **original arity** while off, so the
  `lru_cache` key tuples are unchanged too.
* Rule 28 `[R-MECH-MATRIX]`: row + a cell in all nine ISO shards, SPP minted `O`
  (built, solved, **promotion undecided**). `check_mechanism_matrix.py --base` passes.
* Rule 29(b) form 4 **confirmed empirically**: the fleet-only control leg reproduces the committed
  `<year>_P1_fleet.parquet` **exactly** in all four years; and a zero-delta replay of both SPP
  registered runs found prices identical to 1e-14 with annual class energy within 0.006 % in
  exactly-offsetting within-family pairs (net 0.0000 TWh).
* Rule 30(c): held-out years **report**; SPP's headline stays **CALIBRATED** on 2023–2025.

### 5.1 Pre-existing failures on `main` — reported, not patched

`main` at `4583e70b` is red on **four** tests before this lane touches anything (verified by
stashing; for the ERCOT golden the failing `availability` hash is byte-identical at base and HEAD):
the ERCOT `FleetArrays` golden, the NYISO solve-surface pin, the capacity-evolution soundness
end-to-end, and the NEISO Mystic retiree test. With those deselected, **1,199 passed / 0 failed**
across the outage, retiree, COD-ramp, fleet, binning, CAMPD, cache-key and solve-surface suites.

---

## 6. The marginal-carbon control arm (owner instruction 2026-09-19)

Both shards owed were run and are **not** registered (a replay that reproduces a keeper is not a
new run).

| bundle | years | recover at |
|---|---|---|
| `results/calibration/spp_mer_20260919_keeper` | 2023–2025 | `22f3f9d929565ba0a14bce2662ea772b045990eb` |
| `results/calibration/spp_mer_20260919_rung` | 2019–2022 | `a71abb73e9ccef35d651683028b9561609b4bdf3` |

`marginal_emission_rate` present and non-degenerate in every year; absent from both committed
sidecars, confirming non-retroactivity. Load-weighted mean **0.7370 / 0.7174 / 0.7097** (2023–25)
and **0.7267 / 0.7333 / 0.6479 / 0.6530** (2019–22) tCO2/MWh; p10/median/p90 ≈ 0.38–0.43 / 0.51–0.64
/ 1.08–1.13; zone-hours at exactly 0.0 range **0/17,520** (2019) to **595/17,520** (2022).

**A finding worth the program's attention:** the committed bundles were solved on **highspy
1.14.0**, both replays on **1.15.1** — the environment is not pinned. Measured consequence at the
scored grain: **none** (prices identical to 1e-14; annual class energy within 0.006 %, net zero,
in within-family tie pairs). At *hourly* grain `class_hourly.mw` moves by up to 999 MW in thousands
of rows, which is alternate-optimum reshuffling, not drift — but a lane that differences hourly
class dispatch across containers should know it is there.

---

## 7. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

| bundle | where | promotion cost from here |
|---|---|---|
| `spp48_arm_span` (the arm) | pushed to `claude/spp-48-arm-span`, **43 files / 158 MB**, full `dispatch/` | **zero re-solves** — `git checkout 03a17b9acf9f47251057637d7f7285f3d61cc881 -- results/calibration/spp48_arm_span` |
| `spp_mer_20260919_keeper` | `22f3f9d929565ba0a14bce2662ea772b045990eb` | zero |
| `spp_mer_20260919_rung` | `a71abb73e9ccef35d651683028b9561609b4bdf3` | zero |

All three are on **local disk and gitignored**, and will **not** survive this container — the
immutable SHAs above are the durable copies. Nothing was deleted (rule 31 `[R-RETAIN]`).

---

## 8. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]` — asked, not pre-empted)

1. **Promote `2026-09-19-spp-48-midvintage-exit` to replace the 2019–2022 rung**
   `2026-09-16-spp-43-outage-intake`? The keeper needs no re-solve (byte-identical under the arm).
   On promotion the rung's `holdout.keeper` stamp must be **re-applied** and its corrected caveat
   text **re-authored** — a re-stamp resets it (known defect).
   *This session's reading, which is a recommendation and not a decision:* the arm is a
   zero-DOF measured-input repair that improves four measures, degrades none at criterion level,
   and leaves the determination unchanged. It is worth promoting on rule-14 grounds rather than
   on the residual.
2. **Arm `mid_vintage_exit_carry` as SPP's default posture** (a `_spp_config`
   `default_scenario_overrides` entry)? That is a default flip and therefore an owner ruling.
3. **Charter the benchmark-membership successor** (§4)? It is the larger and more general object,
   it reaches every ISO, and it currently makes the model and the actual disagree about which
   plants exist.
