# FINDING — ercot-166: ERCOT 2023 diagnosis triage, Oak Grove conduct solved, C3c model-class ledger (rubric v3.0)

**Session:** ERCOT-2023-diagnosis, 2026-08-05 (owner-directed). **No LP, no solve, keeper UNCHANGED**
(`2026-08-04-ercot165-unpooled-share`). Every number below is measured from the keeper's committed
hourly sidecars, the committed actuals, or the raw disclosure corpora — no model replay.

Owner directives executed here: (1) C3c becomes an accepted caveat across all three years
(§6 — rubric v3.0 amendment + three ledger entries); (2) diagnose the 2023 −30 % concentration,
the >$1000 missed hours, the year-round 17–19 h evening underrun, the timezone question, and the
Oak Grove lignite overnight withdrawal; (3) issue handoff charters (§7).

---

## 1. The 2023 −30 % is Aug/Sep tail mass — confirmed and decomposed

Load-weighted (model demand weights, hub RT actual), keeper sidecar `price` column (= energy dual
+ rtordpa_overlay + ordc_adder — the scored settlement basis; `reserve_price` is never summed in):

| | annual | Jun | Jul | Aug | Sep | non-summer months |
|---|---|---|---|---|---|---|
| model | 43.19 | 65.0 | 36.8 | 117.3 | 54.9 | 21–29 |
| actual RT | 61.97 | 72.8 | 47.1 | 220.2 | 107.0 | 19–31 |
| bias | **−30.3 %** | −10.7 % | −21.8 % | **−46.7 %** | **−48.7 %** | −12…+16 % |
| $-contribution to annual gap | −18.8 | −0.8 | −1.1 | **−11.6** | **−5.0** | ±0.3 |

Aug alone is 62 % of the annual gap; Aug+Sep 88 %. Consistent with
`FINDING-ercot-2023-summer-underrun-2026-08-04.md` (top-100 hours = 98.3 % of the gap). The hub-based
−30.3 % here vs the scorer's −32.6 % is the zonal-resolved `rt_lw` basis difference, not a discrepancy.

**Tail catch matrix 2023** (settlement basis vs actual RT hub): >$200 actual 181 h / model 58 h /
coincident 54 / model-only 4; >$1000: 61 / 22 / 21 / 1; >$3000: 17 / 8 / 7 / 1. The model has high
tail *precision* and 0.30 recall — it almost never invents scarcity, it misses it. The missed-hour
histogram is an evening-ramp object: hod 17 (29 h), 18 (27), 19 (18), 15 (14), months Aug (62) and
Sep (22).

**The model's scarcity REGIME is right; its pricing of the regime is not.** The `ercot_ordc_total`
family runs a shortfall > 0 in 217 hours of 2023, concentrated Aug (124 h) / Sep (35) / Jun (23) —
essentially the actual tail calendar (181 h). In the 61 actual >$1000 hours the model is
reserve-short in 57 (median shortfall 2.4 GW) yet the family dual prices it at p50 $1.3. That is
**consistent with the real 2023 ORDC** (measured RTORPA p50 ~$1–5, PRC ~5.8 GW at the missed hours —
ercot-102/ercot52): ERCOT did not price those hours through the ORDC either. It priced them through
the **energy offer stack** (storage standing offers $1,500–5,000; ercot-161), which is exactly the
adjudicated ercot-160→163 attribution and the basis of the §6 model-class ledger.

## 2. What generates in the scarcity hours ("assets that weren't available")

Model minus actual (EIA-930 fuels at the verified 0-lag alignment; CAMPD for the lignite split), mean
MW over the actual >$1000 hours (n=61):

| | wind | solar | COAL_PRB-class | COAL_LIGNITE-class | gas | storage (net) |
|---|---|---|---|---|---|---|
| model − actual | **+354** | +5 | **≈ +800** | ≈ −200 | **−1,950** | **+661** |

- **Solar overrun: RESOLVED** (was the ercot109 finding's +/-0; now +5 MW).
- **Wind +354** persists (ercot109 had +377/+560) — the daytime-curtailment open issue's tail.
- **Coal +569 net** is a *class split*: the PRB/sub-bituminous class (incl. Martin Lake) over ≈+800
  while the lignite class is ≈−200. Aug-heat partial derates are structurally absent for the sub-bit
  fleet beyond the plant-grain partial file (ercot-126's per-unit partial extract returned zero rows).
- **Storage +661 over-discharge** is the largest single physical overrun and the same object as the
  ercot-162 successor: real batteries at scarcity held capability back (AS + $500–3,000 standing
  offers); the model discharges at the flat $10 adder.
- The −1,950 gas is the mirror: the model meets the hour with cheap surplus and leaves gas headroom
  the real market ran.

**At the extreme the model is over-tight, not loose:** it sheds load in 4 hours of 2023 (Aug 30 18h
1,429 MW; Aug 25 18h 1,266; Aug 17 18h 556; Jun 20 17h 213) when real ERCOT shed none, and prices
them at VOLL-plus (settlement $15–21k with summed family duals vs the $5,000 cap). Balance check on
the top-10 actual hours: model demand = 930 demand − TI (DC-tie imports are correctly netted into
the demand basis — no missing-import distortion), but model gas tops out 1.7–3.1 GW below actual
delivered gas in those hours (model max-dispatch 49.5 GW vs actual NG max 51.2 GW). The extreme-hour
supply shortness and the ~2.7 GW CC headroom object named at ercot-163 are the same fleet-capability
question (§7 H2).

## 3. Evening 17–19 h underrun — real, year-round, NOT a clock artifact

Hour-of-day gap (model − actual, load-weighted $, excluding Jun–Sep to show the year-round part):

| hod | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|
| 2023 | +2.8 | −4.4 | **−22.6** | −12.1 | −8.7 | +1.6 |
| 2024 | −1.3 | −6.4 | **−12.0** | −1.0 | +19.4 | +15.9 |
| 2025 | +4.0 | −2.2 | **−13.9** | **−23.4** | −12.2 | −7.4 |

with a mirrored +3–6 overshoot at hod 12–15 — the ERCOT face of the cross-ISO diurnal-amplitude
deficit (`FINDING-xiso1-…`: amplitude 37–56 % of measured in 36/36 cells, peak *timing* correct).
2025's medians are negative too (−8 at 18 h): with the 9.6 GW battery fleet it is pervasive, not
tail-driven.

**Timezone/DST audit (owner question): CLOSED — no misalignment reaches the LP or the scoring
benchmark.** The model hour index is fixed CST hour-beginning (verified astronomically); demand,
HSL wind/solar, system actual LMP, CAMPD, cleared AS and the AS plan are all phase-correct at lag 0
in both DST and standard windows; there is **zero Mountain-time handling anywhere in the repo and
none is needed** — ERCOT publishes uniformly in Central Prevailing Time and the far-west counties
are a topology object (West zone), not a clock object. A 1-hour bug could not be year-round anyway
(DST is 8 months). Three real but DST-window-only data defects were found and ranked (none can move
the system marginal price; fix lane §7 H4):
1. `data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet` is on the prevailing clock
   (`scripts/data/derive_ercot_zonal_lmp.py` lacks the `_PrevailingShift` its system-parquet sibling
   got on 2026-07-15) — lag +1 Apr–Oct, identity in Jan–Feb; consumers: the C3a/C3b `rt_lw` bench
   join and several probes.
2. The `rt_lw` join (prevailing-clock zonal prices × CST demand weights) biases the *benchmark* low
   by $0.71/$0.19/$0.21 (2023/24/25) — it **understates** the underrun; fixing it makes C3a slightly
   worse, which is the honest direction.
3. `scripts/data/curate_zonal_shares.py` places ERCOT native-load zone shares on the prevailing
   clock (lag +1 Apr–Oct): ~150–250 MW of interzonal misallocation at h17–19, share-preserving.

**Storage timing (owner question):** the model's battery fleet size and basis are right (measured
60-Day capability caps: 2023 mean 2.88 GW; EIA-860 duration), discharge is correctly
evening-concentrated, and 930-BAT comparison (2025, full coverage) shows the model
**over**-discharging the peak (18/19/20 h: model 3,457/3,902/1,943 vs actual 2,995/2,634/1,283 MW
net) while still charging at 15–16 h when the real fleet is already discharging. Excess model
discharge at the evening peak *depresses* model evening prices in every year and grows with the
fleet — the same AS-vs-energy-split object as §2, and the principal evening-amplitude lever (§7 H1).

## 4. Oak Grove / C7 2023 lignite — conduct SOLVED from the disclosure corpora

CAMPD (ORIS 6180, both ~880 MW units): from **Aug 1 to Oct 28, 2023** — and in no other month of
2022–2024 — the units ran a nightly cycle to *exact LSL floors* (unit 1 → 386–392 MW, unit 2 →
492–494 MW, ~00:00–09:00) and back to ~870–910 MW for the day; daily energy fell 38.6 → 31.9
GWh/day (not conserved ⇒ not a fuel-budget/energy-limited signature); November snapped back to
baseload. The two-shift **paused Aug 15–19** (the tightest week — they ran flat-out through the
scarcity nights). Overnight hub price when backed down (p50 $21.3) equals the price when not
($21.4): a standing schedule, not hour-by-hour discretion. **The whole Luminant/sub-bit fleet
two-shifted in Aug–Oct 2023** (Martin Lake night 1,254 vs day 2,122; Parish 1,439/2,208; Limestone,
Sandy Creek, Fayette, Spruce similar) — Oak Grove is only the newest member, which is why the
LIGNITE class (Oak Grove = 70 %) fails the D-1 cv leg while PRB passes.

Why (measured, all three legs):
- **60-Day DAM** (`60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_*.parquet`): status ON,
  COP HSL ~full every night (855/800), **no DAM energy offer curve, no DAM award, zero AS awards**
  — Oak Grove is a pure self-scheduled/RT resource; nothing was withheld from ERCOT's view
  (the capacity counted toward PRC all night). This also refutes the AS-reservation reading for
  2023 directly (ERCOT-143 had refuted it on 2024/25).
- **60-Day SCED, delivery-August rows** (`data/raw/ercot/SCED/2023-10.part*.parquet` — **the corpus
  is publication-month-keyed: delivery month = filename − 2**; the ercot-157 re-upload made
  delivery-2023 complete): overnight TNO p50 406/460 ≈ LSL with HSL p50 825/805 (full), and the
  **submitted TPO's top step is $60.30** — vs **$4.50/$4.20 in June** (delivery-June = `2023-08`
  parts). At $18–25 overnight LMPs, SCED itself base-points the units to LSL; day prices ≫ $60
  restore full output; the Aug 15–19 pause is just overnight LMP > $60 those nights.
- So: **economic two-shifting executed through a seasonal repricing of the RT energy offer**, fully
  price-formation-native, and invisible to the keeper because `coal_perplant_offer_curves` is
  identified on the 2024/25 SCED corpus and **declared an extrapolation for 2023** in the DOF
  ledger (no 2023 corpus existed at identification time). ERCOT-143 closed the lignite offer lane
  as "NO MEASURED OBJECT — no 2023 SCED exists"; **that closure's own stated premise is dissolved**
  by the ercot-157 corpus, which post-dates it. This is a rule-23 source-data re-derivation trigger
  (per-year 2023 curves from delivery-2023 SCED), NOT a residual fit, and NOT a re-test of the
  closed slope/floor/commitment lanes (§7 H3 charter, with its DO-NOT-REDO fence).

## 5. Other defects surfaced (named, not chartered here)

- **2024 Apr/May over-pricing is 1–2 fabricated spike days** (Apr 27 +$356/h-day-mean, May 7
  +$219), concentrated hod 19–20, inside an otherwise ±10 % year — a maintenance-season
  availability-vs-actual question (phase-0 in §7 H4). Also 2025 May −19 %.
- **2025 HSL evening solar potential** hands the LP ~+2.0/+2.1 GW more h17–18 zero-MC supply than
  was delivered (June means) — a direct 2025 evening-suppression candidate (H1 phase-0 cross-check).
- `ordc_adder` in the keeper sidecar is the **cap-dual branch** output (≠ `ercot_ordc_total` dual in
  176 h of 2023) but `run_config.json`'s `calibration_flags` does not record
  `ercot_ordc_cap_dual_adder` (35-key block; the flag is recorded only in `meta.json`) — a
  run_config recorder gap to close next solve (R-REGISTRY hygiene).
- `render_calibration_html.py` labels the payload tail series "energy-only" but for ERCOT the
  sidecar `price` already carries rtordpa+ordc_adder; and the payload compares max-of-7-zones model
  vs single-hub actual (58 h either way at $200 — flagged for comment/doc accuracy only).
- **PJM keeper metrics are stale against the current scorer** (committed NOT-YET; both pre- and
  post-v3.0 scorer return CALIBRATED with criteria diffs) — pre-existing, PJM-lane, not touched
  here.
- The 6 failing tests in `tests/scoring/` (`test_forecast_parity`, `test_ff_readiness_battery`)
  pre-exist this session (verified by stash) — NYISO `nyiso_seam_deliverability_envelope` parity.

## 6. Executed: C3c accepted caveat (rubric v3.0) — owner decision 2026-08-05

- `scripts/calibration_verdict.py`: RUBRIC_VERSION 2.9 → 3.0; new `MODEL_LIMIT` classification
  ("ACCEPTED MODEL-CLASS LIMITATION") for exceptions entries with `"kind": "model-class"`;
  **supporting-tier-only, fail-closed** (a model-class entry against a load-bearing or protective
  criterion is ignored); shares the ≤3 non-protective ledgered budget. Tests added (3) —
  `tests/scoring/` passes except the 6 pre-existing failures above.
- `results/calibration/ercot165_unpooled_share_B/calibration_attestation.json`: three owner-signed
  `price_tail` model-class entries (2023 58 vs 181 h; 2024 20 vs 53; 2025 0 vs 31) citing the
  exhaustion record (ercot-95/97/102/107/108/155/159/161/162/163) and the open residual lanes.
- Keeper re-scored in place (`--write-metrics`): **C3c FAIL → CAVEAT [ledgered] ×3; C6 UNATTESTED →
  PASS** (the promotion-day metrics predated the attestation file — bookkeeping); determination
  stays NOT-YET with basis exactly `price_mean, price_shape, shape` — **the keeper's whole fail
  surface is now 2023** (C3a −32.6 %, C3b 0.610, C7 lignite cv 0.311). Registry sidecar annotated;
  `status/ERCOT.js` rebuilt; `audit_keepers --iso ERCOT` PASS.
- `docs/calibration-determination-rubric.md`: banner, §2 caveat kinds, C3c classification, §3
  model-class entry requirements (owner decision + exhaustion record + open lane), §9 v3.0 history
  with effects-at-amendment. All other keepers' determinations are unchanged by the scorer edit
  (their committed metrics lag only on the version string / reasons wording until their next
  registration, per the standing v2.x pattern).

## 7. Chartered successors (handoff prompts issued this session; matrix §5.1 items 10–12)

- **H1 / item 10 — `ercot_storage_as_energy_split`** (the ercot-162-named successor): storage
  capability at scarcity split between AS obligation and energy by *measured* AS awards +
  SOC/duration physics, replacing none of the offer machinery (the offer-surface arm stays R).
  Primary lever for C3a/C3b 2023 tail mass AND the year-round evening amplitude.
- **H2 / item 11 — CC headroom / capability identification** (the ercot-163-named successor):
  per-unit SCED-train ↔ model-unit crosswalk; adjudicate the ~2.7 GW undispatched CC capability
  (PUN/cogen hypothesis) as a rule-14 fleet-scope correction on `ercot_thermal_dam_availability_*`;
  also owns the §2 extreme-hour 1.7–3.1 GW gas shortness / 4 phantom shed hours.
- **H3 / item 12 — coal per-plant offer curves, per-year 2023 re-derivation** from the
  delivery-2023 SCED corpus (rule-23 trigger: ercot-157 data change dissolves the ERCOT-143
  closure premise). Owns C7 2023-lignite and the Aug–Oct coal fleet conduct.
- **H4 — no-solve data hygiene**: the three DST-window clock fixes + `rt_lw` bench regeneration +
  the 2024 Apr/May spike-day phase-0 + the run_config recorder gap.
