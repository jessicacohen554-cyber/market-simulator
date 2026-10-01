# CHARTER — pjm-129: PJM keeper re-audit on the guard-corrected CAMPD envelope

**Opened** 2026-07-26, executing the last unresolved cell of
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §5/§8 that this
session can reach. **Pre-registered before any result was read.**
**Model assignment:** Opus/Fable (charter scope, core infrastructure — rule 27).

## 1. Scope, and what this lane may not do

Replay the designated PJM keeper **verbatim** against the guard-corrected
availability envelope. **Nothing is tuned**: no offer curve, no free parameter,
no ledger entry widened or added. The keeper recipe is the arm; the only delta
against its own registered numbers is the committed CAMPD extract.

Not permitted: any year outside 2023–2025 (PJM has no calibration-complete
marker and `holdout-freeze.json` is additionally `active=true` — rule 22, parent
charter §6); registering a single-year bundle (rule 16); re-deriving any
measured-behaviour constant (rule 23 — this lane has no source-data change of
that kind to cite); lifting the freeze by inference (parent charter §6).

## 2. Arms

* **A0 = the keeper itself**, `2026-07-25-pjm-121-cc-belt`
  (`results/calibration/pjm121_ccbelt`), solved 2026-07-25 on the
  **pre-adoption** envelope. The guard is byte-inert when off, so an A0 re-solve
  would be the keeper by construction; no solve is burned on it. Its committed
  `hourly/` sidecars and `metrics.json` are the baseline.
* **A1 (the deliverable)** — the same recipe at HEAD on the corrected extract,
  `--years 2023 2024 2025` in **ONE** bundle (rule 16) →
  `results/calibration/pjm129_meritguard_a1`. Registered on the dashboard
  whatever the verdict (rule 15).

**A0-validity check, done before solving (the caiso-123 lesson).** The CAISO
cell's verdict was withdrawn because its A0 read a derived-not-committed input.
For PJM the extract axis is verified single-delta: `git log --follow` on
`data/raw/campd-unit-outages-PJM.csv` is checked to change exactly once after
the keeper's own `git_sha`, at the guard-adoption commit, and the keeper's blob
is confirmed byte-identical at that sha. Recorded in the finding either way.

## 3. Prerequisites (`data/clean/` is derived and absent in a fresh container)

Regenerated **before** solving, per `RESULTS-neiso65-crossiso-reaudit-2026-07.md`
§2. PJM's recipe carries `pjm_measured_interface_limits`,
`measured_ramp_capability` and `pjm_da_virtual_bids`, so all of:

| prerequisite | why | status |
|---|---|---|
| `transfer-interface-limits` (PJM, 3 yr × 87,600 rows) | `pjm_measured_interface_limits`, hard-fails | regenerated |
| `ramp-capability` (PJM, 749 rows) | `measured_ramp_capability` | regenerated |
| `capacity-deliverability` (PJM, 155 rows) | belt-and-braces after the miso-93 silent-degradation trap | regenerated |
| `data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023,2024,2025}_*` (36 months, gitignored) | `pjm_da_virtual_bids`, hard-fails on any missing month | re-fetched |

Both `curate_ramp_capability.py` and `curate_capacity_deliverability.py` need
`PYTHONPATH=.` or they abort with `ModuleNotFoundError: No module named
'scripts'`. **Every solve log is audited for missing-input warnings before any
number from it is quoted.**

## 4. Method — the staged one-year-per-process `--reuse-solved` chain

The two prior attempts (neiso-65 on `pjm119_overlay_restore`, and its
re-attempt on `pjm121_ccbelt`) both completed 2023 running alone and were then
SIGKILLed at 15.9 GB building 2024, in this same 15 GB / 4-core container. Both
concluded "needs ≥24 GB". That conclusion is **superseded** by miso-90/miso-92:
the year loop's retained floor is ~1.0 GB (attributed and 35 % of it removed by
miso-92) and the *single-year* peak is the ceiling. One fresh process per
solve-year removes the floor and is what made the MISO 3-year bundle fit here.

```
replay_keeper.py results/calibration/pjm121_ccbelt --years 2023 \
    --out-dir results/calibration/pjm129_a1_y23
replay_keeper.py results/calibration/pjm121_ccbelt --years 2023 2024 \
    --out-dir results/calibration/pjm129_a1_y2324 --reuse-solved results/calibration/pjm129_a1_y23
replay_keeper.py results/calibration/pjm121_ccbelt --years 2023 2024 2025 \
    --out-dir results/calibration/pjm129_meritguard_a1 --reuse-solved results/calibration/pjm129_a1_y2324
```

Each stage solves exactly ONE fresh year; earlier years byte-copy forward.
`_copy_reused_year` does **not** carry the `hourly/` sidecars, so
`class_hourly_2023` / `system_2023` are assembled from stage 1 and the 2024 pair
from stage 2 into the final bundle's `hourly/` (rule 15 — keeper-class bundles
commit their hourlies). Intermediate bundles are deleted after their sidecars
are lifted; no partial-year bundle is registered (rule 16).

**Per-year memory telemetry is read from each stage's own release-block line**
(`year %d memory after release: resident=… peak=… | accumulators …`) and
reported — this is the PJM-specific half of the "is the year loop leaking?"
question that the two blocked attempts left open.

## 5. Pre-registered pass/fail bar

Scored by `scripts/calibration_verdict.py` on the unmodified rubric. The
keeper's standing is the reference — PJM's **first all-pass determination**:

| criterion | keeper standing | threshold |
|---|---|---|
| C1 per-class mix | PASS, 16/16 (free 12/12) | `min(2 % load, 8 TWh)` **and** 3 pp |
| C2 family volume | PASS | ±2.5 % |
| C3a mean LMP | 2023 **+5.6 %** / 2024 **−2.5 %** / 2025 **−9.3 %** — all PASS | ±10 % |
| C3b shape / C3c tail | PASS | C3b ≤0.20 |
| C4 / C5a / C6 / C7 / C8 | PASS | C5a ±7 % |
| determination | **CALIBRATED, 10/10** | — |

**Verdict rule, fixed in advance:**

* **FIX-IN-PLACE** — determination stays `CALIBRATED` 10/10 with no new failing
  gate and no new caveat. A1 becomes the reproducible bundle for those numbers.
* **RE-TUNE REQUIRED** — any currently-passing gate fails, or a caveat would
  have to be ledgered. Reported as a trigger with its magnitude; **no tuning in
  this session**, and the keeper designation is not changed (an owner call).

## 6. Named exposure, declared before solving

Measured from the two committed extract blobs, **no solve** — the guard removes
and adds nothing:

| | 2023 | 2024 | 2025 | 2023–25 |
|---|---|---|---|---|
| GW-days removed (layup companion) | 2,001 | 1,109 | 1,513 | **4,624** (903 windows) |
| kept envelope GW-days | 13,059 | 11,387 | 10,595 | 35,041 |
| **relief, % of envelope** | **15.3 %** | **9.7 %** | **14.3 %** | **11.7 %** |

Class mix of the removal, 2023–25: **ST_GAS 2,528 GW-days (54.7 %)**, COAL 984
(21.3 %), CC_REGULAR 841 (18.2 %), CC_CHP 191, CT_CHP 80. That is the same
signature the charter predicted and MISO measured (gas steam priced out of merit
for weeks, booked as mechanically unavailable): returning it **adds supply and
lowers the clearing price**.

PJM's relief (11.7 % of envelope) is close to MISO's (12.8 %), and MISO's
measured price effect was **−$0.445 / −1.38 pp of C3a** with a per-year spread of
−$0.467 / −$0.445 / −$0.396.

**The single pre-registered exposure is C3a-2025.** It sits at −9.3 % with
**0.7 pp** of margin against the −10 % veto, and 2025 carries the second-largest
relief (14.3 %). A MISO-sized −1.4 pp move lands it at ≈**−10.7 %, outside the
band**. A move as small as −0.7 pp fails it.

Secondary, and expected to hold: 2023 (+5.6 %) is *over*-priced, so relief moves
it toward the centre and cannot fail it; 2024 (−2.5 %) has ~7.5 pp of room. C1
is 16/16 with 12 free slots and an 8 TWh band; the ST_GAS volume gain should
largely cancel against CC/CT **within** the C2 gas family. C8's ST_GAS forced
share is expected to rise (as at MISO) and to stay grounded.

Recording this now so neither outcome can be narrated as predicted afterwards.
If the magnitude comes out wrong, that is recorded too.

## 7. Definition of done

A1 solved for all three years in one bundle, scored, and **registered on the
dashboard with its finding, this session** (rule 15) — whichever verdict lands.
The parent charter's §8 PJM cell is closed either way; the freeze is untouched.
