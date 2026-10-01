# PRECOMMIT — CAISO: the 2019-2022 retiree window + the measured monthly gas LEVEL

**Session:** `caiso-fuelvintage-1` · **Date:** 2026-09-09 · **ISO: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`).
**Base:** `claude/caiso-fuelvintage-1`, merged clean onto `origin/main` (0 behind) before any LP.
**Owner ruling carried (handoff §A7, verbatim):** *"these should be promoted as keepers on both 860
and gas shape counts regardless of inertness."*

**Everything in §§1-4 below is measured BEFORE any LP is spent and is pushed before the first
solve, so no gate in it can be written to fit a result.**

---

## 0. What moved under this lane before it started

- **The keeper did NOT move.** `frontend/data/backcast/keepers/CAISO.json` still designates
  **`2026-09-06-caiso-260-b1-demand`** (bundle `caiso260_demand_vintage`), determination
  **CALIBRATED**. Session caiso-267 registered `2026-09-09-caiso-267-fossil92` (the fossil
  offer-band ×0.92 arm) but did **not** promote it — the owner ruled C4-2025 alone holds it at
  NOT-YET. So every bundle path in the handoff stands as written.
- **CAISO's 2022 touchpoint is ALREADY SPENT — twice.** `2026-09-07-caiso-262-2022-touchpoint`
  (stamped `holdout.keeper = 2026-09-06-caiso-260-b1-demand`) and
  `2026-09-09-caiso-267-fossil92-2022` (the caiso-267 re-test, unstamped). 2022 is
  **validation tier**, which rule 22 makes *iterable by design*, so re-spending it on a changed
  fleet is exactly its purpose — not a second consumption of a one-shot. Stated because the
  handoff asked.
- **The handoff's §8 status RED is ALREADY CLEARED.** Measured at this branch's tip:
  `build_status.py --check --iso CAISO` → *"status parts in sync (1 keepers: CAISO)"*;
  `audit_keepers.py --iso CAISO` → **PASS, 0 failures, 0 warnings**. caiso-267's rebuild
  (`1152d593`) cleared it. Nothing for this lane to repair.

---

## 1. G-DRIFT (rule 29(b)) — the code audit is IMPOSSIBLE, and the replacement is stronger

`results/calibration/caiso260_demand_vintage/meta.json` records **`git_sha: e162147b`**. That
object **does not exist in this repository** (`git cat-file -t e162147b` → *"Not a valid object
name"*; absent from `docs/governance/citation-commit-map.txt`; not reachable from any of the 543
commits on any ref). The keeper was solved on a shard branch whose sha never survived to a
reachable ref. **The `git diff <keeper git_sha> HEAD` form of G-DRIFT cannot be executed for
CAISO at all** — this is the same unresolvable-`git_sha` finding `PRECOMMIT-pjm-fuelvintage-2026-09-09.md`
§2 recorded for PJM, reached independently here.

**The replacement, pre-registered here, is a MEASURED drift detector that costs zero extra LP.**
Card A is measured (§2) to be **exactly zero** in 2024 and 2025 and non-zero only in 2023, and
Card B is measured (§3) to be **exactly zero** in 2023. Therefore:

> **G-DRIFT-M.** If the T1-2024 and T2-2025 solves return **max |class-hour delta| = 0.000000 MW**
> against the committed keeper's `hourly/class_hourly_2024.parquet` / `class_hourly_2025.parquet`,
> then HEAD carries **no live drift on CAISO's backcast solve path**, and G-CTRL **form 4** is
> valid: the committed keeper bundle is the control, and the 2023 delta is attributable to the one
> object §2 names. If either year moves, form 4 is falsified and this lane says so.

This is *stronger* than the code audit it replaces — it tests the LP's own output rather than a
reading of which hunks looked inert — and it is decided by years this lane must solve anyway.
**NO CONTROL SOLVES** either way (rule 29(b)).

---

## 2. CARD A — MEASURED, AND IT IS NOT INERT IN 2023. This is a STOP, root-caused.

**Method (zero LP):** CAISO's fleet built twice through `run_calibration.run_year(fleet_only=True)`
on the committed keeper's own `meta.json` recipe, differing **only** in which retiree parquet
`paths.active_eia860_dir` serves — the committed 2019-window artifact versus a
`planned_retirement_year >= 2023` filter that reproduces the pre-`7934e92c` artifact. Nothing
under `data/raw` is modified (the alternate vintage is a temp dir of symlinks).
Probe: `scripts/probes/_caiso_fuelvintage_phase0.py <year> A`.

| CAISO | 2023 | 2024 | 2025 |
|---|---|---|---|
| LP rows, 2019-window (HEAD) | 1,910 | 1,904 | 1,909 |
| LP rows, 2023-window (pre-`7934e92c`) | 1,846 | 1,840 | 1,845 |
| injected rows | 64 | 64 | 64 |
| rows lost | 0 | 0 | 0 |
| **injected rows' effective MW-h** (`pmax × availability`, 8,760 h) | **0.0000000000** | **0.0000000000** | **0.0000000000** |
| shared-row max &#124;Δ pmax&#124; | **144.000 MW** | 144.000 MW | 144.000 MW |
| shared-row max &#124;Δ availability&#124; | 0.0 | 0.0 | 0.0 |
| shared-row max &#124;Δ mc_base&#124; | 0.0 $/MWh | 0.0 $/MWh | 0.0 $/MWh |
| **shared-row Δ effective MW-h** | **+3,367,624.32 (+0.8478 %)** | **0.000000 (+0.0000 %)** | **0.000000 (+0.0000 %)** |

**The handoff's §A9 is HALF right, and the half it got right is not the half that matters.**
§A9 measured the **COD mask** and closed the case: every injected unit ages out on its own month,
and the 64 injected rows' effective MW-h is **exactly 0.0000000000** in all three years — that is
confirmed here independently, to ten decimals. But §A9 measured the *unit-level mask* and never
measured the *plant-level binned capacity*. CAISO's fleet is **plant-binned**, and the binning
folds a dead unit's nameplate into the plant total **before** the tranche split, so the mask never
sees it.

**Root cause — one plant, and it is the very plant §A9 told this lane to stop looking at:**

```
plant 356  AES Redondo Beach (ST_GAS, LA basin)
  gen 7        480 MW   retired 2019-10   <- injected by the 2019 window, correctly masked offline
  gens 5, 6, 8         retired 2023-12   <- online through 2023, and they absorb gen 7's 480 MW
```

The redistribution onto the eight surviving tranche rows, exact to the MW:

| row | pre-`7934e92c` | HEAD | Δ |
|---|---|---|---|
| `ST_GAS_LA_BASIN_p356_committed` | 249.0000 | 393.0000 | **+144.0000** |
| `ST_GAS_LA_BASIN_p356_econc00…05` (×6) | 76.0833 | 120.0833 | **+44.0000** each |
| `ST_GAS_LA_BASIN_p356_peak` | 124.5000 | 196.5000 | **+72.0000** |
| **total** | | | **+480.0000 MW** |

144 + 6×44 + 72 = **480.0 MW exactly** — gen 7's whole nameplate, made dispatchable in 2023 as
CAISO gas-ST, nine quarters after it stopped existing.

**Why 2024 and 2025 are clean:** the same +480 MW appears on `pmax` there too, but gens 5/6/8
retired 2023-12, so the COD ramp zeroes the *whole plant's* availability — `pmax × availability`
is 0 either way. The leak needs a surviving sibling to land on, and after 2023 plant 356 has none.

**CAISO CORROBORATES THE PJM LANE'S FINDING, INDEPENDENTLY AND IN A DIFFERENT MECHANISM CLASS**
(`docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md`: W H Sammis, 720 MW of coal,
+0.0615 % of PJM's 2023 effective capacity). CAISO's relative leak, **+0.848 %**, is **~14× PJM's**,
on a *gas-ST* plant rather than coal. The cross-ISO exposure table in that finding lists CAISO at
480.0 MW; **that number is confirmed here as exact and fully realised in 2023.**

**PRE-REGISTERED DISPOSITION — NOT REPAIRED BY THIS LANE, and the reason is scope, not timidity.**
The fix is in the shared plant-binning path, so it moves **every ISO's fleet in every year** and
would invalidate the other lanes' in-flight LPs. Rule 25 `[R-ISO-SCOPE]` makes that not a CAISO
lane's call, and the PJM lane has already routed it to the owner with the measurement. **This lane
solves at HEAD and reports 2023 as carrying the leak**, which — because Card B is measured inert
(§3) — makes CAISO's 2023 arm-minus-keeper delta a **clean, isolated measurement of the
redistribution defect itself**. That is the most useful thing CAISO can contribute to the owner's
ruling, and it is why the leak is reported rather than absorbed.

---

## 3. CARD B — the fuel seam, MEASURED INERT AT ZERO LP (handoff §A2's census, landed)

### 3a. Coverage — the admission test, verified rather than assumed

`iso_electric_power_monthly_level('CAISO', y)`:

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **None** | **None** | **None** | 12 mo | 12 mo | 12 mo | 12 mo |

**2019/2020/2021 are REFUSED by the admission test**, exactly as the handoff §5 pre-registered —
California prints only 11 of 12 N3045 months in each. So `gas_electric_power_monthly_level` is
**inert by coverage** in H1 (2020, 2021), and CAISO's existing construction stands byte-for-byte
there with the flag armed. The admitted monthly means are 9.486 (2022), 7.033 (2023), 3.606
(2024), 4.275 (2025) $/MMBtu, reconciling to `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md`
§3's CAISO rows to three decimals.

### 3b. Reach — the written-cell census (§A2's named, scoped work, now DONE)

Same two-build method, at HEAD, flag OFF vs ON (`_caiso_fuelvintage_phase0.py 2023 B`):

| CAISO 2023 | shape | cells moved | max &#124;Δ&#124; |
|---|---|---|---|
| `fuel_prices` | (1910, 8760) | **0 / 16,731,600** | **0.0000000000** |
| `mc_base` (the offer the LP solves on) | (1910, 8760) | **0 / 16,731,600** | **0.0000000000** |

**The seam reaches nothing.** Not one of 16.7 million delivered-fuel cells and not one of 16.7
million offer cells moves. The ordering the handoff §5 predicted is confirmed as *total*, not
merely dominant: `gas_hub_basis_overlay` (SoCal / PG&E Citygate) covers 12/12 months of every
CAISO year and supersedes the state-average level, and `gas_plant_monthly_fuel_pricing = True`
overwrites what is left with each plant's own F923 print (the run log shows 81 generators priced
from their own plant, 1,376 gap-filled, then **1,443 gas generators repriced at the measured hub
spot in 12/12 months**). Since `pmax`, `availability`, `fuel_prices` and `mc_base` are the LP's
entire fuel-borne input surface and all four are bit-identical, **the armed 2023 LP is
bit-identical to the unarmed one by construction** — the coal passthrough sigmoid included, since
its effect would show in `mc_base`.

**Rule 29 clause (0) is therefore satisfied and exceeded: the pre-solve gate did not merely pass,
it ANSWERED the question.** The F shard is retained anyway, as the cheapest possible conversion of
"provably inert by construction" into "measured inert in dispatch", and because the owner's §A7
ruling promotes the gas-shape count on its correctness rather than on its footprint.

### 3c. The one CAISO month where it could bite — pre-registered prediction

`FINDING …§3`: **CAISO Dec-2022 model 11.419 vs measured 27.477 $/MMBtu — a 16.058 $/MMBtu gap**
(~120 $/MWh at a CC heat rate), the western gas crisis. 2022 is admissible for the seam and open
under the `complete` marker, so H2 is the one place the mechanism could reach.

> **PREDICTION, fixed before H2 solves: it will NOT reach it, and H2-2022 will be inert too**, for
> the same ordering reason 2023 is — CAISO's hub overlay covers 12/12 months of 2022 and the
> Dec-2022 spike is *in the hub index the keeper already uses*. Predicted `mc_base` cells moved:
> **0**. Predicted C3b move: **0.000 to three decimals**. If H2-2022 moves materially, the
> ordering is wrong — **STOP AND REPORT, do not bank it.**

---

## 4. Pre-registered predictions for the solves

**Card A capacity predictions** (handoff: 2020 +1,120.5 MW, 2021 +278.6, 2022 +60.1, all on a
fleet of tens of GW):

- **H1-2020** is the only touchpoint with a plausible signal (+1,120.5 MW, ~1.5 % of CAISO's
  gas-ST + gas-CC stack). Prediction: prices **fall**, gas-ST/CC generation **up**, both modest.
- **H1-2021 (+278.6 MW) and H2-2022 (+60.1 MW): NO material price movement.** A large 2021 or
  2022 move **is a bug to investigate, not a win** (handoff, verbatim).
- **T1-2023** moves by the §2 leak alone: +480 MW of dispatchable ST_GAS at plant 356. Prediction:
  **ST_GAS generation up, price down, both small** — it is 480 MW of high-heat-rate steam that
  sits far up CAISO's stack and clears rarely.
- **T1-2024 / T2-2025: BIT-IDENTICAL to the committed keeper** (§2: Δ effective MW-h exactly 0;
  §3: seam moves 0 cells). This is G-DRIFT-M's test (§1).

**Criteria.** Every criterion is reported at full magnitude and **none is a gate on this
mechanism** (rule 1 `[R-STRUCT]`): the two changes land because they are correct inputs
(rule 14 `[R-ACCURATE]`) and because the owner ruled to promote them (§A7). Specifically
**C3a is not consulted in any promotion decision here**, and a worse fit is a root cause to
open, never a reason to revert to the estimate.

**Charter task 3, restated honestly.** The task asks for max |class-hour delta| = 0.000000 MW in
all three training years. **It will hold in 2024 and 2025 and it will NOT hold in 2023**, and §2
is the root cause, found before the solve rather than after. The STOP was honoured: the lane
stopped, measured, root-caused, and routed — it did not wave the delta through, and it did not
silently repair a shared path mid-flight.

---

## 5. Governance

- **Rule 31 `[R-RETAIN]`: nothing is deleted.** Every bundle this session produces is gitignored
  (which is what discharges rule 29(c) — not `rm`) and kept on local disk, and the promotion
  question is asked explicitly in the final report.
- **Rule 15 `[R-DASHBOARD]`:** every completed run is registered in this session.
- **Rule 16 `[R-ALLYEARS]`:** T1 (2023, 2024) and T2 (2025) are **composed into ONE bundle**
  covering 2023-2025 before registration. No fragment is ever a keeper.
- **Rule 30 `[R-TOUCHPOINT-FOLD]`:** H1/H2 are stamped to the keeper; 30(c) — a held-out year
  **never** downgrades CAISO's determination, which stays the train-tier verdict.
- **Rule 28:** only `docs/codebase-site/data/mechanism-matrix/CAISO.js` is edited.
- **Rule 12 `[R-PARALLEL]`:** years sequential within every invocation; the shards are separate
  child sessions, each running `scripts/prepare_solve_container.py` first (§A6).
