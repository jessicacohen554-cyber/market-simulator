# PRECOMMIT — miso-251: the MISO validation-touchpoint ladder (2022 → 2021 → 2020) and the C3c check

```
SESSION NUMBER  : miso-251
ISO             : MISO
DATA PROFILE    : miso
MECHANISM       : NONE. This is a holdout-year REPLAY of the designated keeper's frozen recipe
                  (`results/calibration/miso_fuelvintage_A`, run `2026-09-09-miso-250-ep-gas`) on a
                  year outside 2023-2025. The only config delta is the DECLARED input degradation
                  of §3, forced by a purged source — it is not a lever and it is not tuned.
DECIDED BY      : owner instruction 2026-09-10, verbatim: "on miso, please ensure all data needed is
                  populated in the repo to run holdout years 2020-2022, and run the 2022 touchpoint
                  on the current keeper config, then add it to the current keeper entry in the html
                  and add results to calibration status page. Do not make it a new run, make it look
                  like part of the current run. Don't run a control arm or check for drift just use
                  the current keeper. If 2022 stays calibrated, run 2021 and do the same thing. If
                  that stays calibrated run 2020."
YEARS           : 2022 first (this launch). 2021 and 2020 conditional on §5.
BASELINE/CONTROL: the incumbent keeper's COMMITTED bundle — `2026-09-09-miso-250-ep-gas`,
                  `results/calibration/miso_fuelvintage_A`. NO control solve (rule 29(b) form 4),
                  and NO G-DRIFT audit: the owner explicitly waived the drift check for this lane.
RUN ID          : 2026-09-10-miso-251-tp2022
SHARDS          : ONE — the SPAN shard (single year, so span == year). Declared in §6.
```

---

## 1. THE C3c QUESTION, ANSWERED BEFORE ANY SOLVE — AND MISO NEEDS NO C3c FIX

The owner's premise ("a C3c miss should not create a calibrated-with-caveats tag … so miso needs a
fix") is **already the live rule, and MISO is already reading it correctly.** Measured at HEAD
`066d6c9f`, not asserted:

```
$ python3 -c "import calibration_verdict as cv; cv.determine('2026-09-09-miso-250-ep-gas')"
FULL: CALIBRATED
   - 1 ledgered caveat(s) … NOT determination-downgrading under rubric v3.3: C3c price tail
2023 CALIBRATED
2024 CALIBRATED
2025 CALIBRATED-WITH-CAVEATS
     - unscored criteria: fuelmix, sysvol          <-- THE CAUSE
     - 1 ledgered caveat(s) … NOT determination-downgrading … C3c price tail
```

* MISO's **ISO-level determination is `CALIBRATED`**, with C3c its single ledgered, reported,
  non-downgrading caveat. Rubric v3.3 (rule 22 `[R-C3C]`) is doing exactly what the owner
  describes, and `scripts/calibration_verdict.py::_apply_c3c_standing_rule` needs no change.
* The **one** `CALIBRATED-WITH-CAVEATS` string anywhere in MISO's status part is the **2025
  per-year row**, and **C3c is not what downgrades it**. Its cause is `unscored criteria: fuelmix,
  sysvol` — all **8 of 8** MISO C1 classes are `SKIPPED` on the *preliminary 2025 EIA-923 vintage*
  (`7/41` CC_REGULAR plants missing, `73/98` CT_PEAKER, …), which cascades to C2. The unscored-
  criteria route is one the v3.3 amendment explicitly **preserved** as downgrading ("every OTHER
  route to a caveat still downgrades: commercial-band target misses, protective-gate caveats,
  unscored criteria and data-blocked years are untouched").
* It is **not MISO-specific**: CAISO, NEISO and NYISO all read `CALIBRATED-WITH-CAVEATS` on 2025
  for the same reason. ERCOT escapes only because some of its C1 classes still score. This is the
  annual EIA-923 publication lag, not a rubric defect and not a MISO defect.

**Therefore no scorer change is made in this session.** Loosening the unscored-criteria route to
make 2025 read `CALIBRATED` would be a real gate loosening the owner did not ask for and that v3.3
deliberately refused; and removing C3c from `caveats.ledgered` would violate rule 22 guard (d),
which requires the miss stay listed and named at full magnitude on a `CALIBRATED` run.

**Consequence for this ladder, stated up front:** on 2020/2021/2022 the rubric v3.6 out-of-training
limb drops the lone-failure condition, so a C3c miss on a touchpoint year is a ledgered CAVEAT
whatever else that year does. C3c can therefore never be the reason a MISO rung fails to read
`CALIBRATED`.

---

## 2. PHASE 0 (ZERO LP) — WHAT IS ACTUALLY ON DISK FOR 2020-2022

Method: `market_sim.model.lp.solve_dispatch` monkeypatched to raise, then the keeper's `meta.json`
replayed through `replay_keeper.build_kwargs` → `run_calibration_full.solve_and_persist` for each
year. Every loader on the solve path runs; the LP is never built. Cost: minutes, zero LP.

### 2.1 The ONE blocker, and it is the same in all three years

```
PHASE0 2022: BLOCKER FileNotFoundError: miso_measured_reserve_requirements=True but the measured
cleared-reserve series is absent: data/raw/MISO-AS/asm_rt_cleared_mw_2022.parquet
```

`data/raw/MISO-AS/` holds **2023, 2024, 2025, 2026 only**. It is **not fetchable**, and that is
re-verified in this session rather than carried from the register:

| probe | 2022-07-01 | 2022-12-15 | 2023-04-01 |
|---|---|---|---|
| `…/{ymd}_asm_exante_damcp.csv` | **404** | **404** | 200 |
| `…/{ymd}_asm_rtmcp_final.csv` | **404** | **404** | 200 |
| `…/{ymd}_asm_rt_co.zip` | **404** | **404** | 200 |
| `…/{ymd}_da_expost_lmp.csv` (2020/2021/2022) | **404** | **404** | 200 |

`docs.misoenergy.org` keeps a rolling ~3.5-year window; 2018-2022 has aged off entirely. The
documented fallback (MISO Data Exchange Pricing API) needs `MISO_PRICING_API_KEY`, which is present
in **neither the environment nor the repo**. The 2026-07-31 intake already ran the authoritative
full daily sweep (`fetch_miso_asm.py --years 2018..2022`, 5,481 requests, **0 days published**).
**This is a closed source wall, not an intake to-do.**

### 2.2 Everything else resolves, in all three years

With §3's declared degradation applied, `PHASE0 2020`, `PHASE0 2021` and `PHASE0 2022` each reach
the LP call with **every** input resolved — fleet, CAMPD binning, unit-outage/short-window/lay-up
overlays, maxgen tiers, F923 delivered fuel, zonal gas basis, winter citygate, dual-fuel switching,
COD ramp, per-plant must-run levels, CT net-load drag, the reliability-floor registry, the seam /
reference-price interface, and demand:

| year | MISO demand (EIA-930, 6 zones) | peak |
|---|---|---|
| 2020 | 622.5 TWh | 112.9 GW |
| 2021 | 642.3 TWh | 114.2 GW |
| 2022 | 653.2 TWh | 116.4 GW |

(2020's 622.5 TWh reproduces the holdout audit's own published MISO row, 623.)

### 2.3 The SCORING-side gaps — which are what actually bound the ladder

| bench artifact | 2020 | 2021 | 2022 |
|---|---|---|---|
| `actual_lmp.json` MISO block (C3a/C3b) | **MISSING** | **MISSING** | present |
| `actual_lmp_hourly_MISO.parquet` (C3c) | **MISSING** | **MISSING** | present, **DEGRADED** — DA 94.0 % / RT 86.3 % (staged raws stop 2022-12-09 DA / 2022-11-11 RT) |
| `calibration_reference.json` MISO (C1/C2) | **MISSING** | present | present |
| EIA-930 hourly / demand (C2/C4) | present | present | present |

So **2022 is the only rung that can be scored on the load-bearing price criteria at all.** 2021
would score C1/C2/C4/C8 with C3a/C3b/C3c unscored; 2020 would score only C4/C8. Both are blocked by
the same purged source as §2.1 — an unscored load-bearing criterion downgrades, so **neither 2021
nor 2020 can read `CALIBRATED` no matter how the model performs.** That is a data fact, not a model
result, and it is reported rather than worked around: no proxy price series is substituted (rule 14
`[R-ACCURATE]` misalignment exception does not reach a *different market's* prices, and a proxy
benchmark would make the "fit" measure the proxy).

**THE ONE THING THAT UNBLOCKS 2021 AND 2020 IS `MISO_PRICING_API_KEY`.** With it:
`python3 scripts/data/fetch_miso_hub_lmp.py --years 2020 2021` then
`python3 scripts/data/derive_miso_hub_lmp.py` closes both, and also closes 2022's Nov/Dec tail.

---

## 3. THE DECLARED INPUT DEGRADATION — the only config delta, and why it is not a lever

For the touchpoint years **only**, two flags are disarmed:

```
--set miso_measured_reserve_requirements=false
--set miso_reserve_online_gated=false
```

* `miso_measured_reserve_requirements` is a **rule-13 measured overlay whose series does not exist
  before 2023** (§2.1). The loader hard-errors rather than falling back — by design, so the flag
  can never "solve on the static estimates it claims to replace".
* `miso_reserve_online_gated` is a **dependent** of it, not an independent choice: the code refuses
  the pair (`miso_reserve_online_gated requires miso_measured_reserve_requirements … a
  forward-basis generator is a forecast-lane charter, not a silent fallback`). Disarming one forces
  the other.
* What the run then uses is **MISO's own published construction** — the RBDC market-wide
  requirement at fleet-MSSC + regulating with the published 12-step ORDC ladder ($200-$3,500), and
  the published zonal curve steps for MISO-South and Midwest. Measured at phase 0: 2022 market-wide
  3,382 MW at h0; 2021 —; 2020 3,394 MW at h0. **This is exactly the construction a FORECAST year
  uses**, so rule 13 `[R-MEASURED]`'s forward test is met by construction.
* It is **not tuned, not swept, and not selected on any residual** (rules 1 `[R-STRUCT]` / 13). It
  is the same disarm in every touchpoint year, chosen before any solve, and it is the *only*
  admissible way to run the recipe on a year MISO has purged.
* **2023-2025 are untouched** — the keeper's own bundle is not re-solved and not re-keyed.
* Precedent: this is the ERCOT `*_from_year` shape (`ercot_dam_as_overlay_from_year`,
  `ercot_ecrs_requirement_from_year`, `ercot_reserve_supply_cap_from_year`) — a measured overlay
  self-disarming before its record exists — applied by CLI override rather than by adding a
  ScenarioConfig field, so no new tuning channel is registered (rules 24 `[R-REGISTRY]` /
  28 `[R-MECH-MATRIX]`).

**This degradation is reported on the run's definition, on the keeper panel and on the Calibration
Status page. A reader must never see this rung without seeing it.**

---

## 4. WHAT THE RUN IS AND IS NOT (rules 22 / 30)

* It is the keeper's frozen recipe on a held-out year, folded INTO the keeper via
  `scripts/stamp_touchpoint_holdout.py` (rule 30(a)) — **not a new card to click into.**
* It is **iterable model-SELECTION evidence, never a certified out-of-sample skill number.** Since
  `[R-HOLDOUT]` was removed (2026-09-09) no year is protected from being iterated against, so no
  year certifies. Quoted accordingly.
* **It cannot decertify MISO** (rule 30(c)). MISO's determination is the train-tier 2023-2025
  verdict and nothing else.

---

## 5. THE LADDER'S PRE-REGISTERED STOP RULE

1. **2022** solves and scores. If it reads `CALIBRATED`, proceed.
2. **2021** and **2020** are launched only if their price bench exists at that time. On today's
   evidence (§2.3) it does not, and the ladder therefore stops after 2022 with the blocker reported
   and the exact one-command remedy handed to the owner. **No LP is spent on a rung whose
   load-bearing criteria cannot be scored** — that is rule 29 `[R-SCREEN]`'s own economy.
3. If 2022 does **not** read `CALIBRATED`, the miss is diagnosed and a single-year LP screen is
   launched on 2022 per the owner's instruction, before any full-span shard is spent.

---

## 6. SHARD TABLE (rule 32 `[R-SHARD]`, protocol `docs/handoffs/shard-launcher-protocol-2026-09-09.md`)

| shard | branch | scope | registerable? |
|---|---|---|---|
| **SPAN** (single year, so span == year) | `claude/miso251-tp2022` | 2022 | **YES — the only one** |

The parent (this session) runs **no LP**. It did phase 0, wrote this PRECOMMIT, launches the shard,
and afterwards owns the seam: the fold stamp, `build_status.py --iso MISO`, the keeper text, the
calibration log, the mechanism-matrix stamp and the promotion question.

