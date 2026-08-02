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

## 0a. Bottom line

- **D-1 (`retirement_rule` → `pipeline`): FLIP.** The pre-registered bar is met
  in **both** curve-ON ISOs — T-R10a and T-R10b go FAIL→PASS and hold **3/3**
  LOYO folds, recall goes FAIL→PASS (MISO 12 %→76 %, PJM 53 %→76 %), bands
  imported and never widened, **no new invariant failure**, and additions are
  **byte-identical** across the arms. The zero-real-fuel inversions close
  completely (MISO gas_st 12.920→0.0 GW; PJM gas_st 10.358→0.0 and gas_ct
  11.379→0.0).
- **D-2 (arm `entry_rate_limits` + `entry_commissioning_lag`): ARM, as a
  disclosed adequacy change.** The FR-13 precondition is confirmed fixed —
  **I4 stays PASS with the commissioning lag armed**. But the packet's bar is
  only partly met and should be signed knowing so: the rate limit **re-phases
  rather than reduces** cumulative backstop MW (−0.07 %), I13 had **no cobweb
  to remove**, and I12 goes **WARN→FAIL** because the dampers stop concealing
  a shortfall the base arm closed with an unbuildable 4.9 GW single-year CT
  wave. `entry_vre_capacity_revenue` is **unprobed** and stays separately
  signable.
- **Two findings the owner packet does not yet carry.** (1) **Wave 1 made the
  shipped legacy rule substantially worse** with no rule change — MISO
  false-retire 8.643→**12.920 GW**, PJM 4.097→**22.342 GW (5.5×)** — so FR-4's
  evidence base is *understated*, and the pre-W1 FF-1A numbers are not a valid
  baseline for this decision. (2) **MISO legacy's thermal LEVEL band passed
  (−0 %) purely by cancellation** of two large opposite-signed composition
  errors; reading that as the better result is the exact rule-1 failure mode.
- **FH-4 cross-read: `pipeline` moves I6 DOWN** (PJM 12.68 %→8.55 %, −33 %
  relative; MISO 9.06 %→8.37 %) — **but neither curve-ON ISO ever FAILS I6**,
  so this cannot show a failing I6 converted to passing and makes no claim
  about FH-1's ERCOT gate. **The block is not lifted.** New evidence for the
  lane: the **single-year lumping survives removing the legacy counters
  entirely**, so the concentration is upstream of the decision rule — G-31
  screen grain, separable from FF-1A magnitude.

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

### 1.3 MISO T1-F 2026–2030 — the entry dampers (D-2)

Both arms solved cold, 5 solve-years, shipped forecast posture. The armed arm
adds `retirement_rule=pipeline` + `entry_rate_limits` + `entry_commissioning_lag`
(the `entry_vre_capacity_revenue` leg is **not** armed — the owner packet makes
it separately signable, so it needs its own probe row). Runs
`miso-2026-2030-ffr2b-t1f-base` / `-dampers`.

**Thermal entry by source (MW), the BLK-10 row:**

| year | BASE economic | BASE backstop | BASE renew | ARMED economic | ARMED backstop | ARMED renew |
|---|--:|--:|--:|--:|--:|--:|
| 2026 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2027 | **3,000** (gas_cc) | **4,894.1** | **4,000** (wind) | 0 | **1,349.8** | 0 |
| 2028 | 0 | 222.6 | 0 | 0 | 2,699.6 | 0 |
| 2029 | 0 | 3,455.6 | 0 | **3,000** (gas_cc) | **5,240.6** | **4,000** (wind) |
| 2030 | 0 | 2,623.1 | 0 | 0 | 1,897.7 | 0 |
| **total** | 3,000 | **11,195.3** | 4,000 | 3,000 | **11,187.7** | 4,000 |

**Invariants:**

| invariant | BASE | ARMED |
|---|:--|:--|
| **I4 capacity accounting** | PASS | **PASS** ← the FR-13 latent-defect test |
| I6 econ-retire sanity | PASS (0.0 % every year) | PASS (0.0 % every year) |
| I13 cobweb | PASS | PASS |
| I7 reliability floor | FAIL — 2026 only | FAIL — **2026, 2027, 2028** |
| I12 reserve-margin band | **WARN** — 2026 only (5.3 %) | **FAIL** — 2026 (5.3 %), 2027 (5.2 %), 2028 (6.5 %) |

**Readings.**

- **E5 CONFIRMED — I4 stays PASS with the commissioning lag armed.** FR-13's
  predicted failure ("I4 fails by the commissioned MW in every COD year") does
  **not** occur. The mechanism is verified in code as well as in the run:
  `capacity_evolution/evolve.py:559` snapshots the additions-recorder baseline
  `_pre_commission_ids` **before** the step-4.5 commissioned insert, so
  commissioned units land in the step-5 `thermal_additions` diff, while the
  decision-grain baseline `_pre_entry_ids_all` stays post-4.5 so nothing
  double-counts at COD. **FFR-1A's fix holds; the FR-5 precondition is met.**
- **E7 is only HALF met, and the half that fails is the important one.** The
  rate limit does **not** reduce the backstop's magnitude — cumulative fired MW
  is 11,195.3 → 11,187.7, a **−0.07 % change, i.e. invariant**. What it changes
  is the *concentration*: the first-wave burst is cut **4,894.1 → 1,349.8 MW
  (−72 %)** and the deficit is deferred into 2028–2029. The measured ladder is
  exactly the cited construction working as specified — MISO's EIA-860 gas_ct
  seed is 0.742 GW/yr, so the 2027 cap is 2.0 × 0.742 = **1.484 GW** (fired
  1.350), and the cap then doubles endogenously each year as the model's own
  builds raise the prior max (1,349.8 → 2,699.6 → 5,240.6 ≈ ×2 each step).
  **Correction of the record for the owner:** FF-2A's "2.5 → 1.103 GW" is a
  *first-wave* number and was read in the packet as a sizing fix; measured
  cumulatively at post-W1 HEAD on MISO it is a **re-phasing, not a reduction**.
- **The COD lag does exactly what it is built to do.** The identical economic
  package (3,000 MW gas_cc + 4,000 MW wind) moves from COD 2027 to COD 2029 —
  a clean +2-year shift matching `ENTRY_COD_LAG_YEARS = 2` (LBNL IA→COD median).
- **The dampers make near-term adequacy WORSE, and this is the load-bearing
  cost the owner must price.** I12 goes **WARN → FAIL** and I7's failing set
  goes from one year to three. Mechanically this is not a defect of the
  dampers: it is the undamped backstop's instantaneous full-deficit rebuild
  that was concealing the shortfall — MISO's *actual* 2021–2025 gas_ct
  additions were 1.379 GW total, so a 4.9 GW single-year CT build is not a
  physical option and the base arm's 2027 "recovery" is an artifact. Under
  rule 1 the damped arm is the structurally faithful one and the new I7/I12
  failures are a **disclosed adequacy shortfall, not a regression to tune
  away**. But it is a real change in what the MISO forecast board will show,
  and D-2 should be signed with that in view rather than discovered afterwards.
- **I13 PASSES in both arms**, so this 5-year MISO window does not reproduce
  the FC-2 cobweb the audit cites; the anti-cobweb claim for the COD lag is
  **not tested here** (no cobweb to remove). Reported as untested, not as a win.

### 1.4 PJM T1-H, curve-ON — `legacy` → `pipeline`, measured on one tree

Bundles `…/PJM/e29d4571e9a062da` (legacy) and `…/PJM/f28791014e454366` (pipeline).

| quantity | actual | `legacy` | `pipeline` | verdict |
|---|--:|--:|--:|:--|
| **unit recall > 300 MW** | 17 | 9 (53 %) ❌ | **13 (76 %)** ✅ | **restored** |
| **false-retire raw** | — | 22.342 GW (76 % of model) ❌ | **11.968 GW (63 %)** ❌ | −46 %, still FAIL |
| thermal GW retired (T-R1 level) | 11.121 | 29.373 (+164 %) ❌ | **18.862 (+70 %)** ❌ | over-fire halved |
| **gas_st econ (A = 0)** | 0.0 | **10.358 GW** | **0.0 GW** | **inversion closed** |
| **gas_ct econ** | 3.491 | 11.379 (+226 %) | 0.0 (−100 %) | over → under |
| coal econ (cum) | 6.885 | 3.530 (−49 %) | 14.756 (**+114 %**) | under → over |
| nuclear (announced channel) | 0.0 | 4.097 | 4.097 | unchanged — Byron/Dresden reversal |
| T-R10a / T-R10b | — | FAIL / FAIL (first movers `gas_ct`,`gas_st`) | **PASS / PASS** (`coal`) | ✅ |
| LOYO holds ≥ 2/3 (recall · a · b) | — | ✗ · ✗ · ✗ | **✓ · ✓ · ✓** | **rule-22 bar MET** |
| **BLK-10 backstop fired** | — | **8.652 GW** | **3.258 GW** | **−62 %** |
| gas_ct additions (cum) | 0.447 | 8.652 (+1834 %) | 3.258 (+628 %) | improves, still FAIL |
| wind / solar / gas_cc / storage adds | 1.619 / 13.066 / 8.525 / 0.283 | 6.0 / 24.0 / 4.118 / 0.0 | **6.0 / 24.0 / 4.118 / 0.0** | **byte-identical** |
| I6 worst single year (cap 20 %) | — | **12.68 % (2023)** ✅ | **8.55 % (2024)** ✅ | −4.1 pp |
| 2025 system CO₂ (Mt) | 448.7 | 328.7 (−27 %) ❌ | 287.4 (−36 %) ❌ | worsens |
| invariants (non-PASS) | — | **none** | I12 WARN | — |

**LOYO folds:**

| fold | `legacy` recall · false raw · T-R10a/b | `pipeline` recall · false raw · T-R10a/b |
|---|---|---|
| −2023 | 6/9 FAIL · 4.097 GW · PASS/PASS | **9/9 PASS** · 14.372 GW · PASS/PASS |
| −2024 | 4/16 FAIL · 22.916 GW · FAIL/FAIL | 0/16 FAIL · **4.097 GW** · PASS/PASS |
| −2025 | 9/16 FAIL · 22.371 GW · FAIL/FAIL | **12/16 PASS** · 12.413 GW · PASS/PASS |

**Readings.**

- **Flip-gate items 3 and 4 clear for PJM too, LOYO-robust** (T-R10a/b 3/3,
  recall 2/3, the −2024 fold zeroing for the same coal-execution-concentration
  reason as MISO).
- **E4 fires much harder on PJM than on MISO.** FF-1A's committed `D1=3`
  BEFORE recorded PJM false-retire **4.097 GW raw / 0.0 IS-2020** and coal
  recall 0 %. At post-W1 HEAD the same legacy rule gives **22.342 GW** — a
  **5.5×** deterioration with no rule change. Together with MISO's +49 %, this
  is a Wave-1 effect (FR-7's solve-year availability keying is the leading
  candidate: an aging fleet thins attainable margins and more units fail the
  screen). **The consequence for D-1 is that the audit's FR-4 case is
  understated, not overstated** — the rule the default still executes is
  substantially worse today than the evidence the decision was framed on.
- **The PJM residual is over-retirement of coal DEPTH (+114 %), and it is the
  already-known revenue-lane bar question**, not a rule defect: FF-1A recorded
  the PJM coal break-even at ≈ 92 $/kW-yr against the current 58.5 $/kW-yr
  going-forward bar, with the margin trace straddling 92 rather than 58.5.
  Routed to BLK-6/BLK-9 / RD-4 as an open blocker (rule 11/21); **not** closable
  by a coal-specific threshold (rule 1).
- **CO₂ moves the wrong way** (−27 % → −36 %) because the deeper coal exit
  removes more emitting energy than reality did — the same level residual seen
  from the emissions side, not an independent failure.
- **BLK-10 improves substantially on PJM** (8.652 → 3.258 GW, −62 %), the
  opposite of the MISO T1-F finding in §1.3 where the cumulative was invariant.
  The two are consistent: on PJM the backstop shrinks because the *retirement
  wave* it is responding to shrank (a D-1 effect); on MISO T1-F the wave was
  already zero, so the ladder had only phasing to change (a D-2 effect). **The
  rate limit and the rule act on different halves of the over-fire.**

## 2. D-1 decision box — `retirement_rule` `legacy` → `pipeline`

**The audit's own bar (owner packet D-1): "flip iff FFR-2B's post-W1 probes
clear the T-R battery + T-R10 + LOYO with bands unchanged."**

### Measured before → after, both curve-ON ISOs, one tree, bands unchanged

| gate | MISO | PJM |
|---|:--|:--|
| **T-R10a no-inversion** | FAIL → **PASS** | FAIL → **PASS** |
| **T-R10b no-inversion** | FAIL → **PASS** | FAIL → **PASS** |
| **LOYO ≥ 2/3 (recall)** | ✗ → **✓** | ✗ → **✓** |
| **LOYO ≥ 2/3 (T-R10a/b)** | ✗ → **✓ (3/3)** | ✗ → **✓ (3/3)** |
| **recall band** | FAIL (12 %) → **PASS (76 %)** | FAIL (53 %) → **PASS (76 %)** |
| false-retire | 12.920 → **0.997 GW** ✅ | 22.342 → **11.968 GW** (−46 %, still ❌) |
| zero-real-fuel exits | 12.920 → **0.0 GW** | 10.358 → **0.0 GW** |
| T-R1 thermal level | PASS (−0 %) → **FAIL (−16 %)** | FAIL (+164 %) → **FAIL (+70 %)** |
| additions bands (T-R1e) | **unchanged to the MW** | **unchanged to the MW** |
| BLK-10 backstop | 0.0 → 0.0 GW | 8.652 → **3.258 GW** |
| new invariant failures | **none** | **none** (I12 WARN appears) |
| 2025 CO₂ | +14 % ❌ → **+7 %** ✅ | −27 % → −36 % ❌ |

### What the flip re-opens

**Expected: nothing — and measured: nothing.** The pipeline rule is an
identified construction (uniform bar = the unchanged `net_revenue <
going_forward_cost`; joint entry capped by the *existing* adequacy requirement;
soft latch at the same bar; five rule-23-identified EIA-860 execution-lag
medians). Its DOF ledger is **−7 fitted-adjacent integers, +5 identified lags,
2 open DOFs held and none tuned** (FF-1A §2). Concretely:

- **No new invariant failure in either ISO.** I4/I6/I7/I13 PASS in all four
  T1-H arms. PJM gains an I12 WARN; MISO's I9/I12 rows are bit-identical
  across arms.
- **Additions are byte-identical across the arms in both ISOs**, so no
  additions verdict, and no part of the D-2 evidence, is disturbed.
- **The field is cache-key-registered at non-default**, so the flip moves
  forecast cache keys by construction — no silent bundle reuse, and no epoch
  debt from the flip itself.
- **Re-solve cost** is the one already scheduled: every T1-H FC-3 verdict, at
  FFR-3A step 1.

### Recommendation

**FLIP.** The pre-registered bar is met in both curve-ON ISOs on both no-inversion
gates and on recall, LOYO-robust at 3/3 folds for T-R10 — with bands imported,
never widened, and with no new invariant failure and no additions movement.

Two things the owner should sign this with in view, neither of which is a
reason to hold:

1. **The aggregate thermal LEVEL band gets worse in MISO (PASS → FAIL) and
   stays failing in PJM.** MISO's `legacy` −0 % PASS was arithmetic
   cancellation between 12.920 GW of a zero-real fuel and a 9.4 GW coal
   shortfall; treating that as the better result is precisely the rule-1
   failure mode. The remaining level residuals — MISO under-retiring
   gas_ct/gas_cc/oil, PJM over-retiring coal depth against a 58.5 vs ≈ 92
   $/kW-yr going-forward bar — are the **revenue lane's** (BLK-6/BLK-9, RD-4)
   and are recorded here as open blockers, not parameters (rule 11/21).
2. **The case is stronger than the audit states.** At post-W1 HEAD the legacy
   rule's false-retire is **12.920 GW in MISO (vs 8.643 pre-W1)** and
   **22.342 GW in PJM (vs 4.097 pre-W1, a 5.5× deterioration)**. FR-4's
   evidence base was measured on a pre-Wave-1 tree and understates the defect.

**Sign-off:** ☐ FLIP ☐ HOLD ☐ DEFER

## 3. D-2 decision box — arm `entry_rate_limits` + `entry_commissioning_lag`

**The audit's own bar (owner packet D-2): "arm the two dampers iff FFR-2B shows
I4 green with the lag armed and I13/BLK-10 improved without new invariant
failures."** Graded literally, on MISO T1-F 2026–2030 (§1.3):

| condition | measured | verdict |
|---|---|:--|
| **I4 green with the lag armed** (the FR-13 test) | **PASS** — and the fix verified in code at `evolve.py:559` | ✅ **MET** |
| **I13 improved** | PASS → PASS; **no cobweb existed in this window to remove** | ⚠️ **untested, not met** |
| **BLK-10 improved** | cumulative **11,195.3 → 11,187.7 MW (−0.07 %)**; first wave 4,894 → 1,350 MW (−72 %) | ⚠️ **re-phased, not reduced** |
| **no new invariant failures** | **I12 WARN → FAIL**; I7 failing years 1 → 3 | ❌ **NOT met** |

### What the flip re-opens

More than the packet anticipated. The packet expected "FC-2 (I13) verdicts and
the BLK-10 backstop-sizing record; nothing else." Measured, it also re-opens
**MISO's I7/I12 adequacy rows**: delaying entry by the cited 2-year COD lag and
capping the backstop at the cited growth ladder leaves MISO short of its own
adequacy requirement for 2026–2028 instead of 2026 alone.

### Recommendation

**ARM — but as a disclosed adequacy change, not a quiet damper, and score the
two gates separately.**

The reasoning is rule 1 [R-STRUCT] applied straight. Both mechanisms are
identified constructions with zero free parameters (ReEDS 200 %-of-prior-max;
LBNL "Queued Up" IA→COD median), and the invariant regressions are not the
dampers inventing a shortfall — they are the dampers **ceasing to conceal
one**. The base arm closes its 2027 adequacy gap by building **4,894 MW of
gas_ct in a single year** in an ISO whose *actual* 2021–2025 gas_ct additions
totalled **1.379 GW**. That build is not a physical option, so an I12 that
passes because of it is passing on a fiction. Under rule 1 the mechanism stays
in even though the gate goes red, and the red gate becomes the finding.

What the owner is really deciding is therefore not "damper or no damper" but
**"does MISO's forecast disclose a 2026–2028 adequacy shortfall or paper over
it with an unbuildable CT wave."** Recommend disclosing.

Three caveats to sign with:

1. **`entry_rate_limits` does not fix BLK-10's magnitude on this evidence.**
   Cumulative fired MW is invariant to 0.07 %. The packet's "2.5 → 1.103 GW"
   is a *first-wave* figure; read cumulatively it is re-phasing. If the owner's
   intent for D-2 was to shrink total backstop over-fire, **this arm does not
   deliver it** — §1.4 shows that shrinkage comes from D-1 instead (PJM 8.652
   → 3.258 GW, −62 %, from the smaller retirement wave the rule produces).
   The two decisions act on different halves and should not be credited twice.
2. **The anti-cobweb claim is untested**, not validated: I13 passed in both
   arms, so this window contained no cobweb to damp.
3. **`entry_vre_capacity_revenue` is unprobed** and remains separately
   signable, exactly as the packet says. It changes entry economics (BLK-7
   term c), not entry dynamics, and no evidence is offered here. **Do not sign
   it on this session's evidence.**

**Sign-off:** ☐ ARM BOTH ☐ ARM `entry_rate_limits` only ☐ ARM
`entry_commissioning_lag` only ☐ HOLD ☐ DEFER · `entry_vre_capacity_revenue`:
☐ separate probe first

## 4. FH-4 cross-read (pack §0d item 3)

**The question asked:** do the armed arms move the I6 single-year
econ-retirement fraction, and in which direction?

**Answer: yes — `pipeline` REDUCES I6 in both curve-ON ISOs, materially in PJM.**

| leg | I6 worst single year | year | verdict (cap 20 %) |
|---|--:|--:|:--|
| MISO T1-H `legacy` | 9.06 % | 2023 | PASS |
| MISO T1-H `pipeline` | **8.37 %** | 2024 | PASS |
| PJM T1-H `legacy` | 12.68 % | 2023 | PASS |
| PJM T1-H `pipeline` | **8.55 %** | 2024 | PASS |
| MISO T1-F both arms | 0.00 % | — | PASS |
| _FH-1 gate probe, ERCOT T1-FF base 2023 (reference, not re-run)_ | _26.8 %_ | _2025_ | _FAIL_ |

Direction: **down**. PJM −4.13 pp (12.68 → 8.55 %, a **−33 % relative**
reduction); MISO −0.69 pp. In both ISOs the concentration year also moves
2023 → 2024, consistent with the measured per-fuel execution lags (coal = 3).

**Three qualifications, stated so this is not over-read.**

1. **Neither ISO I can measure ever FAILS I6, under either rule.** The worst
   legacy value across both curve-ON ISOs is PJM's 12.68 %, comfortably inside
   the cap. So this evidence shows `pipeline` moving I6 **in the right
   direction**, but it **cannot demonstrate that `pipeline` converts a failing
   I6 into a passing one** — the failing case is ERCOT's, and ERCOT is outside
   this session's arms.
2. **The single-year lumping SURVIVES the rule change.** In all four T1-H arms
   the economic exits land in exactly **one** year (MISO 2023→2024, PJM
   2023→2024) with zero in the other three. `pipeline` reduces *how much* is
   lumped and shifts *when*, but it does not spread the wave. Since the legacy
   consecutive-loss counters are removed entirely under `pipeline`, **the
   concentration cannot be the counters' doing alone** — it survives their
   removal. That points the root cause upstream of the decision rule, to the
   screens all flipping on one common perfect-foresight margin path across an
   over-supplied vintage fleet: exactly the **G-31 screen-grain** diagnosis
   FH-1 §7 and the T1-X adjudication both named.
3. **This does not lift the FH-4 block and is not offered as doing so.** FH-4's
   `REQUIRES` demands FH-1's own gate re-probed and passing. FH-1's gate probe
   was **not** re-run here (out of charter), and nothing above licenses a claim
   about ERCOT's 26.8 %.

**Routing (charter: name the owning lane, do not fix).** The evidence points at
**two** lanes, not one, and they are separable:

- **FF-1A R-NEW pipeline (owner D-1)** owns the *magnitude*. Flipping it is
  measured here to cut the worst single-year fraction by a third in PJM, so it
  is a real and probably necessary part of an FH-4 unblock — but on this
  evidence it is **not demonstrated to be sufficient**, because a 33 % relative
  cut applied to ERCOT's 26.8 % would land near ~18 %, i.e. inside the cap only
  narrowly and only if the effect transfers, which rule 25 forbids assuming
  across ISOs.
- **G-31 screen grain** owns the *concentration*, and this session supplies new
  evidence that it is the independent term: the lumping is invariant to
  removing the counters. An FH-4 re-probe that flips only the rule and still
  fails should be read as confirming G-31, not as refuting the rule.

**Recommended sequencing for whoever owns the unblock:** flip D-1 first (it is
independently justified by §2 and cuts the magnitude), then re-run FH-1's gate
probe unchanged. If it still fails, the residual is G-31's by elimination, and
the measurement above is the evidence for that attribution.

## 5. Governance & scope record

**Rule 22.** Every leg is inside the training window plus the enumerated
`{2021}` hindcast seed. Solved years: T1-H `[2021, 2023, 2024, 2025]` with
**2022 bridged and never solved** in all four arms; T1-F `[2026 … 2030]`,
forecast-mode, reading no measured actuals. The **holdout freeze was active and
is recorded in every bundle's meta** (`holdout_freeze_active_at_launch: true`).
**No out-of-training year was solved, scored or registered; no marker was
spent.** Leakage guards: **zero violations** on all four T1-H legs.

**Rule 12.** Strictly one invocation at a time (FFR-2C held the program's other
slot), years sequential within each invocation, ≤ 5 solve-years per invocation.
PJM and MISO legs never co-ran.

**Rule 24 / 28c.** **No `ScenarioConfig` default was changed.**
`ScenarioConfig().cache_key()` is unchanged at `603c2498bf71d21d`;
`check_cache_key_registration.py` reports 669 fields / 113 registered, all
resolving. No field was added, so no new cache-key registration was needed.

**Rule 15.** All six probe runs are registered on the **forecast-validation
namespace** (`frontend/data/hindcast/`), never the backcast registry:
`miso-2021-2025-cmc-{legacy,pipeline}-ffr2b`,
`pjm-2021-2025-cmc-{legacy,pipeline}-ffr2b`,
`miso-2026-2030-ffr2b-t1f-{base,dampers}`.

**Rule 28.** `economic_retirement_screen` and the newly-added `entry_dampers`
rows are updated in `docs/codebase-site/data/mechanism-matrix.js` in this
session, with evidence citations. No keeper moved, so the matrix header is not
restamped. The `entry_dampers` row is itself a rule-28c repair: three
solve-affecting fields had no matrix row.

**Harness changes made (both byte-identical at defaults, neither a flip).**

| file | change | why |
|---|---|---|
| `scripts/run_capacity_hindcast.py` | wired `--entry-vre-capacity-revenue` / `--entry-rate-limits` / `--entry-commissioning-lag` for real; meta entries read from the **solved config**, not `args` | FFR-1D deleted the previous flags because they wrote state into a bundle's meta while arming nothing, and left this exact instruction for the successor session |
| `scripts/run_full_horizon.py` | `reference_config()` forwards `retirement_rule` + the three dampers, with CLI flags | the T1-F runner had no retirement arm at all, so D-2 could not be asked on a forecast-mode window |
| `tests/scoring/test_crossover_harness.py` | contract test: dampers default-off **and** arm for real | the defect FFR-1D removed the old flags over must not recur |
| `scripts/probes/ffr2b_arm_compare.py` | ledger → D-1/D-2 rows; **imports** the I6 cap from `check_forecast_invariants` rather than restating it | a diagnostic must not be able to quote a looser bound than the checker enforces |

**What this session did NOT do**, deliberately: change any default; widen any
band; register anything on the backcast registry; touch an out-of-training
year; add a GitHub Actions workflow; schedule a full-horizon run; re-run FH-1's
gate probe; probe `entry_vre_capacity_revenue`; or attempt a fix in the
retirement layer (findings are routed, per charter).

**Open blockers recorded, not closed (rule 11/21):** the MISO
gas_ct/gas_cc/oil under-retirement and the PJM coal-depth over-retirement are
signal-LEVEL residuals owned by the revenue lane (BLK-6/BLK-9, RD-4 — the
58.5 vs ≈ 92 $/kW-yr going-forward bar). Neither is closable by the decision
rule and neither may be closed by a fuel-specific value.
