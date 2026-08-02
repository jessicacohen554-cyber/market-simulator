# FFR-2B — Retirement-rule + entry-damper evidence (the owner's D-1/D-2 case)

**Charter.** FFR-2B of `docs/forecast-readiness-prompt-pack-2026-07.md` §Wave 2:
re-probe `retirement_rule="pipeline"` (audit **FR-4**) and the FF-2A entry
dampers (audit **FR-5**) at post-Wave-1 HEAD, and deliver the measured
before/after the owner sitting needs for decisions **D-1** and **D-2**. Amended
priority per pack §0d (2026-08-02): FH-1's §3.3 harness-defect gate FAILED — the
I6 over-retirement reproduces at the T1-FF posture — and the defect lives in the
retirement layer this session measures, so §4 adds an explicit **FH-4
cross-read**.

**This session changes no `ScenarioConfig` default and flips nothing.** The
flips are the owner's, executed at FFR-3A step 0. Rules 1, 5, 11, 12, 14, 15,
22, 24, 27, 28 govern.

---

## 0. Pre-registration (written and committed BEFORE any leg was solved)

Registered here so the §3 grading protocol of
`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` is honoured:
expectations first, measurement second. **Bands are imported by reference and
never restated looser.**

### 0.1 The arms

Six legs, all solved **COLD**. The 2026-08-02 cache epoch
(`src/market_sim/results/cache.py` ledger; pack §0c-3) invalidates every
forecast-mode bundle produced before the Wave-1 merges **at any solve year** —
FR-1/FR-2 change fleet MW from a confirmed exit's year+1 onward and FR-7 re-keys
the age-based availability escalation onto the solve year. Every leg below is a
forecast-mode leg with capacity evolution and aging-sensitive availability, so
**no committed BEFORE leg qualifies for reuse** under the pack §0c-9 duty — the
BEFORE arms are re-solved at HEAD too, which is also the only way the
before/after is measured on one tree.

| # | Leg | Instrument | Arms |
|---|---|---|---|
| 1 | `miso-2026-2030-t1f-base-ffr2b` | T1-F (2026–2030) | shipped defaults |
| 2 | `miso-2026-2030-t1f-dampers-ffr2b` | T1-F (2026–2030) | `pipeline` + `entry_rate_limits` + `entry_commissioning_lag` |
| 3 | `miso-2021-2025-cmc-legacy-ffr2b` | T1-H (2021–2025, 2022 bridged) | curve-ON, `legacy` |
| 4 | `miso-2021-2025-cmc-pipeline-ffr2b` | T1-H | curve-ON, `pipeline` |
| 5 | `pjm-2021-2025-cmc-legacy-ffr2b` | T1-H | curve-ON, `legacy` |
| 6 | `pjm-2021-2025-cmc-pipeline-ffr2b` | T1-H | curve-ON, `pipeline` |

Rule 12: strictly sequential — one invocation at a time (FFR-2C holds the
program's other concurrency slot), years sequential within each invocation,
≤5 solve-years per invocation. Rule 22: every leg is inside the training window
plus the enumerated `{2021}` hindcast seed; 2022 is bridged, never solved; the
T1-F legs are forecast-mode 2026+ and read no measured actuals. The holdout
freeze is not implicated and no marker is spent.

### 0.2 Pre-registered expectations

**D-1 (`retirement_rule`), per FF-1A's committed measurement
(`ff-retirement-rule-implementation-2026-07.md` §4–§7).** The redesign fixes
decision ORDER and COMPOSITION, not signal LEVEL — so:

- **E1.** MISO's gas_st false-retire collapses toward 0 under `pipeline`
  (FF-1A measured 8.643 → 0.0 GW); T-R10a/b PASS on the economic channel.
- **E2.** PJM's coal wave is recovered under `pipeline` (recall 0 % → ~76 %).
- **E3.** The LEVEL residuals persist and are NOT expected to close: MISO
  under-retires thermal, PJM over-retires coal depth. Both route to the revenue
  lane (BLK-6/BLK-9, RD-4) — never a fuel patch (rule 1).
- **E4.** If Wave 1 moved these numbers materially versus FF-1A's committed
  values, the movement is FR-1/FR-2/FR-7's, and is reported as such rather than
  re-attributed to the rule.

**D-2 (entry dampers), per FF-2A + audit FR-5/FR-13.**

- **E5 (the latent-defect test).** FR-13 said arming `entry_commissioning_lag`
  would make **I4 fail by the commissioned MW in every COD year**, because
  step-4.5 commissioned units entered the fleet before the additions baseline
  snapshot. FFR-1A is recorded as having fixed the accounting. Expectation:
  **I4 stays PASS with the lag armed.** An I4 failure here is a live FR-13
  regression and is reported as a blocker, not tuned around.
- **E6.** I13 (cobweb) is expected to improve or hold — the COD lag is the
  structural anti-cobweb.
- **E7.** BLK-10 backstop fired MW falls under `entry_rate_limits` (the ladder
  caps the one-pass full-deficit rebuild).

**FH-4 cross-read (§4).** I6 is `econ_mw / prior_thermal` per solve year against
a 20 % cap. Measured on both arms of legs 3–6. No claim about FH-1's own gate
probe is made from these legs, and the block is not declared lifted — that needs
a retirement-lane fix plus FH-1's own re-probe.

### 0.3 Harness work this session required

Both probe runners needed the arms exposed before anything could be measured;
neither change moves a default (`ScenarioConfig().cache_key()` verified
unchanged at `603c2498bf71d21d`).

1. **`scripts/run_capacity_hindcast.py`** — FFR-1D deleted the three FF-2A
   `--entry-*` flags on 2026-07-31 (rule 26, audit FR-15) because they wrote
   their state into a bundle's meta while arming nothing, and left the successor
   an explicit instruction: *"a session that needs them wires the passthrough for
   real, one line each; it does not resurrect a flag that lies."* This session
   is that successor. The meta entries are now read from the **solved config**,
   never from `args`, so the record cannot diverge from what was armed.
2. **`scripts/run_full_horizon.py`** — had no `--retirement-rule` and no entry
   arms at all, so the D-2 question could not be asked on a forecast-mode
   window. `reference_config()` now forwards all four; passing none of them is
   byte-identical to the pre-change reference forecast.

---

## 1. Measured results

All numbers below are read from the legs' own committed `score.json` /
evolution ledgers via `scripts/score_capacity_hindcast.py` (+ `--flip-gate-extras`)
and `scripts/probes/ffr2b_arm_compare.py`. Nothing is quoted from an absent
bundle and no band is restated.

### 1.1 MISO T1-H, curve-ON — `legacy` (BEFORE) at post-W1 HEAD

Bundle `results/hindcast/miso-2021-2025-cmc-legacy-ffr2b/MISO/df5c3de1bad16670`;
report `docs/hindcast-reports/miso-2021-2025-cmc-legacy-ffr2b-2026-08-02.md`.

| quantity | actual | model (`legacy`, post-W1) | FF-1A's `D1=3` BEFORE (pre-W1) | band |
|---|--:|--:|--:|:--|
| thermal GW retired (T-R1) | 15.227 | **15.202 (−0 %)** | 12.986 | ✅ PASS |
| unit recall > 300 MW | 17 | **2 matched (12 %)** | — | ❌ FAIL |
| false-retire raw | — | **12.920 GW (85 % of model)** | 8.643 | ❌ FAIL |
| coal econ (cum) | 10.934 | 1.497 (−86 %) | — | under-retire |
| **gas_st econ (cum)** | **0.0** | **12.920** | **8.643** | inversion |
| gas_ct / gas_cc / oil econ | 2.435 / 0.521 / 0.502 | 0.0 / 0.0 / 0.0 | — | −100 % |
| T-R10a / T-R10b | — | **FAIL / FAIL** (first mover `gas_st`) | FAIL / FAIL | ❌ |
| LOYO holds ≥ 2/3 | — | recall ✗ · T-R10a ✗ · T-R10b ✗ | — | ❌ |
| BLK-10 backstop fired | — | **0.0 GW** | — | — |
| I6 worst single year | ≤ 20 % cap | **9.06 % (2023)** | — | ✅ PASS |
| 2025 system CO₂ (Mt) | 301.4 | 343.7 (+14 %) | — | ❌ FAIL |

**Two findings already, before the AFTER arm.**

1. **E4 fires — Wave 1 moved the legacy leg, and moved it the wrong way.** The
   MISO `gas_st` false-retire is **8.643 → 12.920 GW (+49 %)** versus FF-1A's
   committed `D1=3` BEFORE, and cumulative thermal 12.986 → 15.202 GW. Nothing
   in the decision rule changed between those measurements, so the movement is
   FR-1/FR-2/FR-7's — most plausibly FR-7 (age-based availability now keys on
   the solve year, so an aging fleet's screens see lower availability and
   thinner attainable margins). **The pre-W1 FF-1A numbers are therefore not a
   valid BEFORE for this decision**, which is exactly why the §0c-9 duty
   requires the cold re-solve. Any D-1 argument that quotes the 8.643 GW figure
   as the current baseline is quoting a stale tree.
2. **The `legacy` thermal LEVEL passes while its composition is entirely
   wrong.** 15.202 vs 15.227 GW actual is a −0 % T-R1 PASS built from 12.920 GW
   of a fuel that retired **zero** MW in reality plus 1.497 GW of the coal that
   actually retired 10.934. This is the sharpest available illustration of why
   rule 1 orders structure before level: the aggregate band is *passing on a
   cancellation of two large opposite-signed composition errors*, and a
   level-only reading of this leg would call it the best MISO retirement result
   on record.

### 1.2 MISO T1-H, curve-ON — `legacy` → `pipeline`, measured on one tree

Both arms solved cold at the same HEAD, same window, same curve-ON posture;
the ONLY difference is `retirement_rule`. Bundles
`…/MISO/df5c3de1bad16670` (legacy) and `…/MISO/0a4455fd0d642364` (pipeline).

| quantity | actual | `legacy` | `pipeline` | verdict |
|---|--:|--:|--:|:--|
| **unit recall > 300 MW** | 17 | 2 (12 %) ❌ | **13 (76 %)** ✅ | **restored** |
| **false-retire raw** | — | 12.920 GW (85 % of model) ❌ | **0.997 GW (8 %)** ✅ | **−92 %** |
| **gas_st econ (A = 0)** | 0.0 | **12.920 GW** | **0.0 GW** | **inversion closed** |
| **coal econ (cum)** | 10.934 | 1.497 (−86 %) | **11.932 (+9 %)** | **wave restored** |
| T-R10a / T-R10b | — | FAIL / FAIL | **PASS / PASS** | first mover `gas_st` → `coal` |
| LOYO holds ≥ 2/3 (recall · a · b) | — | ✗ · ✗ · ✗ | **✓ · ✓ · ✓** | **rule-22 bar MET** |
| thermal GW retired (T-R1 level) | 15.227 | 15.202 (−0 %) ✅ | 12.716 (−16 %) ❌ | level regresses |
| plant-exact recall (report-only) | 17 | 1 (6 %) | **8 (47 %)** | — |
| 2025 system CO₂ (Mt) | 301.4 | 343.7 (+14 %) ❌ | **322.6 (+7 %)** ✅ | improves |
| BLK-10 backstop fired | — | 0.0 GW | 0.0 GW | unchanged |
| I6 worst single year (cap 20 %) | — | 9.06 % (2023) ✅ | 8.37 % (2024) ✅ | both PASS |
| wind / solar / gas_cc / gas_ct / storage adds (GW) | 7.2 / 18.649 / 3.867 / 1.379 / 0.744 | 8.0 / 0.0 / 4.146 / 2.0 / 4.0 | **8.0 / 0.0 / 4.146 / 2.0 / 4.0** | **byte-identical** |

**LOYO folds (scorer-side, within 2023–2025, no re-solve):**

| fold | `legacy` recall · false raw · T-R10a/b | `pipeline` recall · false raw · T-R10a/b |
|---|---|---|
| −2023 | 2/14 FAIL · 0.0 GW · PASS/PASS | **11/14 PASS** · 3.814 GW · PASS/PASS |
| −2024 | 0/13 FAIL · 12.926 GW · FAIL/FAIL | 0/13 FAIL · **0.006 GW** · PASS/PASS |
| −2025 | 2/17 FAIL · 12.920 GW · FAIL/FAIL | **13/17 PASS** · 1.012 GW · PASS/PASS |

**Readings.**

- **Flip-gate items 3 and 4 clear for MISO, LOYO-robust.** T-R10a/b hold **3/3**
  folds and recall holds 2/3 — the rule-22 promotion criterion. The −2024 recall
  fold is zero for the same measured reason FF-1A recorded: the model's coal
  wave executes almost entirely in 2024 (decisions 2021 + coal execution lag 3)
  while the real exits spread 2023–2025. That is a **calendar-spread** finding
  for the revenue lane, not a membership failure — the wave's membership is
  fold-robust.
- **T-R1(e) "additions bands not degraded vs BEFORE" is met in the strongest
  possible form: they are unchanged to the MW.** The decision rule moves
  retirements and nothing else on the additions side, so nothing in the D-2
  entry evidence is confounded by D-1.
- **The one regression is the aggregate LEVEL band, and it is the honest
  trade rule 1 predicts.** `legacy`'s −0 % was 12.920 GW of a zero-real fuel
  cancelling a 9.4 GW coal shortfall; `pipeline`'s −16 % is a coal wave at
  **+9 % of actual** with the residual carried by gas_ct/gas_cc/oil exits the
  screens still do not value (2.435 / 0.521 / 0.502 GW actual, 0.0 modelled).
  That residual is the **known revenue-lane gap** (BLK-6/BLK-9, RD-4: the
  screens under-value peaking-adjacent classes without scarcity/AS revenue) —
  it is not closable by the decision rule and must not be closed with a fuel
  patch (rule 1). Reported as an open blocker, not a parameter (rule 11/21).
- **CO₂ improves as a by-product**, +14 % → +7 %, crossing back inside the
  ±10 % band — consistent with retiring the right fuel.

## 2. D-1 decision box

_(populated after the legs land)_

## 3. D-2 decision box

_(populated after the legs land)_

## 4. FH-4 cross-read

_(populated after the legs land)_
