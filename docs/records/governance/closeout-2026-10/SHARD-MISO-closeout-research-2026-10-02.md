# MISO — calibration close-out research (read-only shard, 2026-10-02)

Zero LP, no repo edits. Sources: keeper bundle `results/calibration/miso280_span/`, `docs/calibration-log/miso.md`
(miso-265 … miso-298), `docs/records/miso/` (FINDING/RESULT/PRECOMMIT miso-281 … miso-298), the MISO matrix shard
`docs/codebase-site/data/mechanism-matrix/MISO.js`, `docs/mechanism-testing-matrix.md` §5.4, the rubric, and the external
documents cited in §5. Every number below is quoted from a record or computed from committed data at zero LP; nothing is modelled here.

## 1. STATUS TABLE

Keeper `2026-09-28-miso-280-splitremap` (bundle `results/calibration/miso280_span`, 7 single-year legs composed, solve SHA `8f765fef`,
`run_config.json`). Scored on rubric v3.9 in `metrics.json`, re-verified on v3.13 (`docs/calibration-log/miso.md:15478`).
Determination **NOT-YET** (`metrics.json`: "undocumented out-of-tolerance (FAIL) criteria: fuelmix, price_mean, price_shape"); train tier
2023–2025 **CALIBRATED** with C3c the lone ledgered caveat. Grade summary: scored 8, target-grade 4, ledgered 1, fails 3.

| year | C1 fuel-mix | C2 sysvol | C3a mean (zone-resolved RT lw) | C3b shape NRMSE | C3c tail (>$200, model/RT actual) | C4 | C6 | C8 |
|---|---|---|---|---|---|---|---|---|
| 2019 | **FAIL** ST_GAS −8.00 TWh (band 8.00) | PASS | PASS +8.7 % | PASS 0.114 | **SKIP** (no committed actual; RT actual = 17 h, model 0 h, see §2.4) | PASS | PASS | PASS |
| 2020 | PASS | PASS | **FAIL +11.6 %** | PASS 0.165 | **SKIP** (RT actual = 8 h, model 0 h → would read PASS, \|Δ\|≤10) | PASS | PASS | PASS |
| 2021 | PASS | PASS | PASS −5.6 % | **FAIL 0.201** (cap 0.20) | **SKIP** (RT actual = 48 h, model 0 h → would read CAVEAT) | PASS | PASS | PASS |
| 2022 | PASS | PASS | PASS −5.1 % | PASS 0.122 | CAVEAT 0/116 h (RT coverage 86.3 %, ledgered model-class) | PASS | PASS | PASS |
| 2023 | PASS | PASS | PASS +8.4 % | PASS 0.104 | CAVEAT 3/30 h | PASS | PASS | PASS |
| 2024 | PASS | PASS | PASS +5.1 % | PASS 0.101 | CAVEAT 7/37 h | PASS | PASS | PASS |
| 2025 | SKIP (preliminary EIA-923) | SKIP | PASS −1.1 % | PASS 0.083 | CAVEAT 9/88 h | PASS | PASS | PASS |

Sources: `(session scratch, not committed) fails_MISO.txt`; `RESULT-miso298-gas-form-alone-2026-10-01.md` §2.2–2.3 (keeper column); model/actual >$200 counts
from the decoded keeper payload `frontend/data/backcast/runs/2026-09-28-miso-280-splitremap.js` (`years.<y>.ordc.hoursGt200`).

What blocks the determination (rule 30, worst-of over every registered year): three load-bearing criterion-years — C1 ST_GAS 2019,
C3a 2020, C3b 2021 — all three owner-ruled **routed misses** (miso-281, miso-294, miso-280). "No frontier" is the owner's standing
ruling because the rubric does not clear every year (`FINDING-miso281` §6).

Bundle facts that shape the close-out:
- `hourly/` carries class_band_hourly / class_hourly / reserve_family / storage / system only — **no `unit_hourly` and no
  `unit_marginal_<year>.parquet`** (rule 15 since 2026-10-01). `promote_keeper.py` preflight refuses a new keeper with neither, so
  **the next promotion requires a full 7-year re-solve** regardless of which lever it carries (miso-298's shards did write the layer).
- DOF ledger (`calibration_attestation.json`): 44 entries, 2 residual-identified (`offer_curve_by_group`, `offer_curve_smoothing`).
  The attestation's `authorized_price_tuning` key is **null** although the keeper carries the miso-275 CC_REGULAR/CC_INTERMEDIATE
  exemption from the ×1.10 lift through the rule-1 channel (`docs/calibration-log/miso.md` miso-275 header) — a rule 1(e) declaration
  to verify at the next attestation.
- Legitimacy: D-1/D-2/D-4 FAIL rows = 11 (`RESULT-miso298` §2.1), C8 PASS.
- Keeper inputs of note (`run_config.json`): `eia860_vintage_tracks_solve_year=true`, `mid_vintage_exit_carry=true`,
  `partial_plant_exit_carry=true`, `unit_outage_dispatched_bin_denominator=true`, `coal_fuel_inventory(_plant_grain)=true`,
  `measured_coal_heat_rates=true`, `maxgen_emergency_tier_pricing=true`, `miso_winter_gas_daily_delivered=true`,
  `miso_seam_neighbour_hourly_ladder=true`, `energy_reserve_coopt=true`, `miso_measured_reserve_requirements=false`,
  `scarcity_pricing_enabled=false`, `wind_ptc_vintage_offers=false`, `admit_standby_units=false`.

## 2. ROOT-CAUSE MAP

### 2.1 C1 ST_GAS 2019 (−8.003 TWh vs band 8.00 — a 3 GWh miss)
- Diagnosis (settled): *"In 2019 the real plants produced 85 % of their energy in hours when the measured hub LMP was below their own
  measured marginal cost … What it lacks is the extra out-of-merit commitment the real system ran in 2019–2020 above what the
  2023–25-measured floors carry."* (`FINDING-miso281-south-steam-2019-out-of-merit-2026-09-28.md` §1). South 2019: 20.2 TWh actual,
  17.1 out of merit, model floor 9.5 → ~7.6 TWh missing (§3). Model offers match measured cost (±$3), model South price is *above* the
  hubs, availability not binding (§2).
- Mechanism located, level unidentifiable: ~76 % of South OOM steam 2019–25 sits on the MTEP15 VLR-eligible plants (Ninemile DSG 24.5 TWh,
  Sabine WOTAB 19.3, Lewis Creek 9.4, Little Gypsy 6.8, Waterford 1.7); it falls as in-pocket CCs enter (St Charles 2019, Lake Charles/
  Washington Parish/NOPS 2020, Montgomery County 2021). *"The quantity a floor or constraint needs, MW of local generation per pocket (or
  the pocket import limit), is set by MISO/Entergy Operating Guides that are not published."* (`FINDING-miso284-ro2-identification` §1–§3).
  `scuc_load_pocket_commitment` → **G** 2026-09-29 (owner: "Mark blocked").
- Tried and refused: own-year floor (rule 13), ST_GAS band multiplier (rule 1(b), wrong mechanism), `mustrun_online_frac_per_year`
  (R, re-measured 2026-09-26), `admit_standby_units` (U, parked: admits 0 MW ST_GAS in 2019; Taconite Harbor phantom coal without an
  outage companion, `FINDING-miso284-standby-census`).
- Open: a published pocket requirement or import limit (MTEP voltage-stability transfer limits — §6). Note the knife-edge: the miss is
  3 GWh on an 8 TWh band; any legitimate rule-14 input repair in 2019 could flip it, but a lever chosen *because* it finds 3 GWh is rule-1
  residual-chasing. Diagnosis certainty: high.

### 2.2 C3a 2020 (+11.6 %, +$2.54/MWh; FAIL only since the zone-resolved basis of 2026-10-01)
- Diagnosis: *"a level shift over the bottom four load quintiles, not a night object and not a tail object … The same low-load overshoot
  is present in every year"* (`FINDING-miso296-lowload-stack-2026-10-01.md` §1.1). Who is marginal: *"In the lowest load quintile the
  model's marginal row is gas in 65 %, the seam … in 28 % and coal in 7 % of hours (bid stack, 2020). The IMM reports that coal set MISO's
  system marginal price in 40 % of 2020 intervals, 'generally in off-peak hours'"* (§1.2). *"Coal is not at the margin because the
  model's coal offer curve has a hole where the real one is flat"*: mustrun ~$4.5, committed ~$9 (take-or-pay discount), econ ~$29.6
  (HR 13.0 × $1.91 + $4.50 VOM, ×1.10 lift); real coal margin ~$15 (§1.4). Quantity is not the object (model vs CAMPD within ±1 GW, §1.5).
- Decomposition: West/Plains congestion separation ≈ 4.4 of the 11.6 points (counterfactual +7.2 % PASS) → `internal_congestion_split`,
  **G** (killed 2026-10-01, reopens on RO-1 only); the other ~7.2 points are the margin level in every zone (§1.6). At the CC margin the
  EIA-923 print sits $0.27–0.39/MMBtu (2019–21) over the Chicago flow-day hub = $2.0–2.6/MWh of a $3.5–3.7 gap (§1.3).
- Tried: joint arm identification by IMM marginal-share census — *"no crossing … one value across years (rule 1 (b)) cannot serve both
  regimes"* (`FINDING-miso297` §1); gas form alone solved full span — C3a 2020 **+11.6 → +14.1 %**, K-1 fired (`RESULT-miso298` §2.3);
  merchant-CC EcoMin floor pre-check killed (<$0.5, `FINDING-miso286`); P1-over-P0 night residual $0.8–1.5 every year, coal-dual years
  2022/2025 (`FINDING-miso287`); coal-pile variants (miso-288/289/290) killed on 2022 night gates; coal line **CLOSED** (owner 2026-09-30).
- Open: the coal offer-curve *shape* between $9 and $30 (§4 L3/L4). Diagnosis certainty: medium — the 4.4/7.2 split rests on a
  "West+Plains at rest-of-footprint error" counterfactual, and the margin-level part is a bid-stack reconstruction at the keeper's own
  quantity, not a solved arm.

### 2.3 C3b 2021 (NRMSE 0.201 vs 0.20)
- Diagnosis: *"C3b 2021 = Feb Uri (24 % of SSE, routed) + Sep–Nov (60 %): North-wide level miss (Oct model $38 vs $53–60 actual), model
  burns coal the real fleet held back (coal +2.8/+4.5/+4.0 TWh, gas −5.2/−7.3/−6.8 TWh vs EIA-930)"* (`RESULT-miso294` Part B;
  `docs/calibration-log/miso.md:15509`). The fall object is coal conservation 2021: *"In 2021: Jun–Aug burn ran 10.3 Mt over receipts, then
  the fleet held the pile … by taking units offline (online GW Aug→Nov −18.5, vs −8 to −13 in other years)"* and *"Not carriable: the
  keeper's flat B/12 limb binds in summer, when the real fleet did not conserve. A fall-only row needs the year's own stock path (rule 13)"*
  (`FINDING-miso295`, log :15529). The Feb object: Chicago-zone storm-month shape defect and no admissible daily Gulf print
  (`FINDING-miso269` §1; owner "Leave as routed miss", miso-280).
- Tried: D1 daily delivered gas (miso-276 R, Uri print pass-through 0.416; miso-277 as ruled 0.290 → 0.254), fuel-split/stcov/splitremap
  companions (0.254 → 0.201 with the basis change), gas form alone **0.201 → 0.192 PASS but K-1** (`RESULT-miso298` §2.1).
- Open: the per-year variable-transport table (§4 L1) — the one successor miso-298 named and did not sweep. Diagnosis certainty: high on
  localisation; the "not admissibly carriable" reading of fall conservation is a governance judgement (§9 Q1), not a measurement.

### 2.4 C3c 2019–2021 SKIPPED — a derive gap, closable at zero LP today
- `frontend/data/backcast/tail/actual_tail.json` carries MISO 2022–2026 only. `scripts/data/derive_actual_tail.py::_year_emittable`
  returns True for every year since 2026-09-09 and `derive()` groups every year in `actual_lmp_hourly_MISO.parquet`; the parquet carries
  2019–2021 RT at 99.99–100 % coverage (`data/raw/_validation-source/actual_lmp.json` `rt_cov`). The part simply was not regenerated after
  the 2019–2021 hub series landed (rule 23: the re-derive cites that data change).
- Zero-LP pre-read from the raw chunks (`data/raw/lmp-data/MISO/miso_hub_lmp_<y>_rt_p*.csv`, INDIANA.HUB = `SYSTEM_HUB` in
  `scripts/data/derive_miso_hub_lmp.py:211`): RT hours >$200 = **17 (2019), 8 (2020), 48 (2021)**; 2022 reproduces the committed 116.
  Model hours >$200 (payload `ordc.hoursGt200`): 0/0/0. Readings once derived: 2019 CAVEAT (0×, model-class, same class as 2022),
  **2020 PASS** (actual <10 h → |0−8| ≤ 10), 2021 CAVEAT. Determination unchanged; three SKIPs become scored.

### 2.5 C3c 2022–2025 CAVEAT (ledgered model-class / measured-input limitation) — unchanged; the IMM confirms the realised tail is
emergency-pricing and sub-hourly (2021 SOM: emergency offer floors $500/$1,000 from Sep 2021; 2025 SOM: ~40-minute shortage at ~$3,100).

## 3. RETEST CANDIDATES (rule 28: only where the premise demonstrably changed; "new evidence" must be real)

| mechanism | prior verdict / date / evidence | milestone(s) that changed the premise | real new evidence | gate | expected direction | cost |
|---|---|---|---|---|---|---|
| `coal_prb_committed_dispatchable` | R, 2026-07-31, `FINDING-miso111` (rejected on pre-registered G1+G2 of the retired C7 amplitude lane; keeper 109b, 2023–25 only) | C7 retired 2026-08-06; measured coal HR + yard-grain budget + dispatched-bin denominator (09-23/24); 2019–2021 span; zone-resolved C3 basis made C3a 2020 the failing gate (10-01) | miso-296 §3: model low-load coal marginal share 7 % vs IMM 40 % (2020); miso-297 §3: "a structural statement about the coal offer curve's SHAPE, not its level" — exactly the committed-band question these cells adjudicated for a different criterion | C3a 2020 (and the same q1–q4 overshoot in 2019/2023/2024) | down at low load (coal offers appear between $9 and $30) | zero-LP census on the miso-297 bid-stack machinery first; 7 shards only if the census crosses |
| `coal_prb_committed_split` | R, 2026-08-01, `FINDING-miso112` (G2; cycling slice bid *full* delivered cost, so it created no intermediate offer) | same as above | same; the split's cycling slice at full SRMC is why it could not fill the hole — the measured within-run night level (`coal_prb_committed_split_MISO.csv`) is still the right quantity statistic | C3a 2020 | down at low load | as above |
| `miso_coal_night_floor` | I, 2026-08-02, `FINDING-miso113` (binds 1–4 TWh, moves nothing scored) | — | none: a floor adds inframarginal energy; miso-285 §1 shows coal already sits at mustrun+committed at night | — | not a candidate (keep I) | — |
| `gas_variable_transport` / `gas_marginal_commodity_pricing` | R, 2026-10-01, `RESULT-miso298` (K-1: frozen 2023–25 transport table > 2019–22 print wedge) | n/a — fresh | the successor is a *different artifact* (per-year table), so it is a new lever (§4 L1), not a re-test | C3b 2021, C3a 2021–25 | see §4 | zero-LP then 7 shards |
| `internal_congestion_split` | G, 2026-10-01, `DESIGN-miso293` (≥17 DOF conventions on HIFLD; reopen on RO-1 only) | — | none in hand; RO-1 needs MISO-published shift factors / zone-aligned limits (not public) | C3a 2020 (≈4.4 pts) | — | keep G; §6 lists what would reopen it |
| `scuc_load_pocket_commitment` | G, 2026-09-29, `FINDING-miso284` | — | reopens on a published MW requirement/import limit — §6 item 4 | C1 ST_GAS 2019 | up South steam | blocked on data |
| `measured_offer_surface` | R, 2026-08-11, miso-151 (improved both gates, refused on identification: within-unit rise 0.04× prior, across-unit dispersion is the real object) | rule-1 channel 09-05 does not reach it (not a band) | none; MISO's masked offer corpus still carries no fuel attribute | — | keep R | — |
| `ordc_scarcity_overlay` | G, owner ruling (miso-163) | — | none; note the realised MISO ORDC 2019–21 had a $200 step removed only in Dec 2021 (§5) | C3c | — | keep G, ledger |

No other R/I/G cell in the MISO shard has new evidence that reaches a failing gate. `coal_passthrough_sigmoids` (R, MISO-53) is a
gas-keyed fitted form and stays refused under rule 13; `measured_interface_limits` / `miso_rdt_measured_limit` (R) were refuted on
pre-registered sanity rules that the later keepers did not change.

## 4. NEW LEVERS (no fitted adders/haircuts/offsets; each enters through an existing registry field or one new zero-DOF field)

| # | name | mechanism (how it enters the LP) | measured driver | forward story (rule 13) | targets | expected direction / bounded magnitude | risks / doubts |
|---|---|---|---|---|---|---|---|
| L1 | **Per-year variable gas transport table** (successor named in `RESULT-miso298` §4(B), unswept) | `miso_gas_variable_transport` reads a per-plant transport leg; re-derive the table from each solve year's own EIA-923 receipts instead of the frozen 2023–25 pool | EIA-923 plant purchase price − flow-day hub, per plant-month (already on disk; `gas_plant_monthly_pricing` K) | transport is a tariff; a forward year carries the latest measured table — same admissibility as F923 delivered fuel | C3b 2021 (0.201), C3a 2021/22/23/25 q1–q2 | the 2019–22 K-1 flips came from transport ($0.24–0.36) > print wedge ($0.13–0.39) in those years (`FINDING-miso297` §1.4); an own-year table removes that sign error, so the miso-298 gains (C3b 2021 → 0.192) are the ceiling and the C1 COAL_PRB 2019 flip (+6.40 → +8.63) is the risk | the transport leg may still exceed the wedge in 2019 (print premium only $0.27–0.39); must clear K-1/K-2 in the zero-LP census before any shard |
| L2 | **Max Gen declaration registry 2019–2021** (data completion for the keeper mechanism `maxgen_emergency_tier_pricing`, K) | emergency-tier offer floors on slack inside declared windows (already structural) | MISO's declaration history (§6 item 3): Jan 30 2019 Event (Central/North), May 16–17 2019 South LMR event, Jul 7 2020 Event Step 1a (North/Central), Aug 27 2020 Laura (South), Feb 15–17 2021 South (only Feb 15 registered), Jun 10 2021 Midwest Step 2a 14:00–18:00 EST | declared windows are the ISO's own instrument; forecast uses none (rule 13 overlay class) | C3c 2019/2021 (tail 0 h), C3b 2021 Feb | model tail rises only where slack or emergency supply binds inside a window; 2019/2020 windows are a few hours, so C3c 2019 likely stays CAVEAT — this is correctness (rule 14), not a gate-closer | floor **vintage**: the $500/$1,000 Tier floors date from Sep 2021 (2021 SOM p.xii); pre-Sep-2021 windows need the then-effective floors — a constants citation the lane must settle first |
| L3 | **Coal econ offers at measured incremental heat rate** (`coal_econ_two_sided`, U; needs `coal_incremental_hr_ratio_MISO.csv`) | committed/econ coal tranches priced at incremental HR (CAMPD hourly heat-input vs load slope) instead of average HR | CAMPD unit hourly heat input and gross load (on disk) | unit physics; regenerates for any fleet | C3a 2020 (and 2019/2023/2024 same object) | lowers the ~$30 econ level by the (avg−incr)/avg ratio, typically 5–15 % → ~$26–28; miso-297's m-grid bounds this: m 0.85–0.95 moved the pooled low-load coal share only 0.285 → 0.303 and q1–q2 error by ≤ $1; **alone it cannot close +11.6 %** | C1 COAL_PRB 2019 +6.40 TWh sits 1.6 TWh inside the band (K-1 risk per miso-297 §5); derive is SOCO-scoped today (rule 25: MISO derives its own) |
| L4 | **Coal committed-band continuum: cycling slice at incremental cost, take-or-pay fuel sunk only to contract minimum** (a re-build of L3 + miso-112's split; `coal_committed_nested_on_mustrun` U / `coal_takeorpay_committed` K) | committed band split at measured night p50; the cycling slice bids incremental HR × (spot share × delivered price) rather than full SRMC | EIA-923 Page 5 contract-vs-spot shares (miso-290: coal ~95 % contracted), CAMPD night p50 | contracts and physics, both forward-known | C3a 2020 | this is the only form that puts coal offers *at ~$15* where the IMM says coal is marginal; magnitude unbounded until a census is run | rule 19: must replace, not stack on, the regulated take-or-pay discount; miso-102 (`sunk_fixed`, R) is the nearest prior and must be distinguished in the PRECOMMIT |
| L5 | **PTC-vintage negative wind offers** (`wind_ptc_vintage_offers`, keeper false; MISO cell `.`) | wind MC = −PTC within the 10-year §45 window | EIA-860 wind COD vintage (on disk) | statutory; forward-known | D-A / low tail; C3a 2020 only +$0.25 of +$2.54 (`FINDING-miso296` §1.1) | small, correct-direction; IMM Table 1: wind set LMPs in 61–62 % of intervals (congestion) | not a gate-closer; worth arming for structure only if a full span is being run anyway |
| L6 | **VLR local-commitment constraint with a published import limit** (reopens `scuc_load_pocket_commitment`) | min online MW per pocket = pocket load − published import capability, met by cheapest in-pocket units | MTEP22/24 voltage-stability transfer limits (WOTAB: Mt Olive–Hartburg 500 kV; DSG/Amite South: Franklin–McKnight 500 kV) — §6 item 4 | fleet evolution does the year-to-year work (`FINDING-miso284` §2) | C1 ST_GAS 2019 (needs ≥ 3 GWh) | up South steam by whatever the pocket balance requires; the IMM confirms VLR = 25 % of MISO-wide RSG and recommends local STR requirements (IMM South, Jul 2025, slides 7–13) | blocked until the MW is public; identification from conduct is refused (nyiso-97 §5 precedent) |

## 5. EXTERNAL RESEARCH (confirmed from a primary source unless marked *inference*)

**Coal commitment and the off-peak margin (the C3a 2020 object).** Potomac Economics, *A Review of the Commitment and Dispatch of
Coal Generators in MISO* (draft 2020-09-14): of 1,795 coal starts in 2019, 41 % were offered economically, 43 % must-run and
profitable, 17 % unprofitable; merchant commitments were 100 % profitable in 2019 and 98 % offered economically, while integrated
utilities' unprofitable starts rose to 18 % (pp. 4–7). Inefficient losses were ~5 % of efficient net operating revenues in 2019; the five
least-efficient owners carried ~80 % of them. https://www.potomaceconomics.com/wp-content/uploads/2020/09/Coal-Dispatch-Study_9-30-20.pdf.
MISO's own April-2020 analysis: ~76 % of coal self-scheduled and economic, 12 % uneconomic over 2017–2019
(https://www.utilitydive.com/news/miso-majority-of-coal-is-self-committed-12-was-uneconomic-over-3-year-pe/577508/). 2021 SOM Table 1:
coal set the SMP 40 % (2020) / 35 % (2021) of intervals "generally in off-peak periods"; gas 57 % / 64 %; wind set LMPs 61–62 %
(https://www.potomaceconomics.com/wp-content/uploads/2022/06/2021-MISO-SOM_Report_Body_Final.pdf p.6). The keeper's statistic
(miso-296 §3) is the model-side counterpart — the comparison is like-for-like and the gap (7 % vs 40 % at low load) is the headline.
*Inference:* a cost-based LP with a two-level coal curve (discounted committed band, full-SRMC econ band) cannot reproduce a margin that the
real market forms on a continuum of self-committed units offering near incremental cost; this is the model-class reason the IMM census
could not identify one multiplier (miso-297).

**2020 COVID low load.** 2020 SOM appendix: COVID reduced load in spring and fall ("ghost bar", Fig. A8); Jul 7 2020 Max Gen Event elevated
to Step 1a in North/Central at 1 p.m. (https://www.potomaceconomics.com/wp-content/uploads/2021/05/2020-MISO-SOM_Appendix_Compiled_Final_rev-6-1-21.pdf
pp. 5, 17). Model demand is measured (EIA-930), so COVID is not a model object; the 2020 miss is the all-years low-load overshoot reading
worst because its tail deficit is only −$1.0 (miso-296 §1.1).

**Winter Storm Uri (Feb 2021).** 2021 SOM: Max Gen Event Step 2c in the South on Feb 15 evening; South prices averaged $823/MWh; 300–800 MW
of firm load shed for 32 h in the Western Load Pocket under a Local Transmission Emergency (not a capacity emergency, so VOLL did not
set price); >$730 M of congestion; exports to SPP >4 GW through the event (pp. 12–15). The registry carries only the Feb 15 South row
(`data/raw/maxgen-events/miso/miso.csv`). The keeper's Feb miss is routed on gas; the IMM says the price was congestion/emergency, which an
energy-only zonal LP without the SPP wheel cannot form — consistent with the owner's routing.

**June 10 2021.** Max Gen Event Step 2a, Midwest, 14:00–18:00 EST; 3.2 GW of LMRs committed; ELMP set prices $200–400 from 2 pm to ~3:30 pm;
the IMM's STR-based simulation gives <$150 (2021 SOM pp. 43–44). Not in the registry (§6 item 3).

**Fall 2021 coal conservation.** 2021 SOM: "fuel limitations and other supply chain issues compelled many coal resources to begin
conserving coal … we consulted with many coal resource owners to establish reference levels that accurately reflect these limitations"
(pp. 46–47); output gap 0.4 % of load, "largely attributable to coal conservation measures" (p. ~150). IMM Winter-2022 quarterly (via
S&P/MISO summaries): coal capacity conserving fell from >18 GW at the start of Q4 to 8 GW by Dec 1 2021
(https://spglobal.com/platts/en/market-insights/latest-news/electric-power/102721-miso-warns-of-potential-winter-capacity-shortfalls-tight-us-coal-supplies).
The real mechanism is an opportunity-cost adder in reference levels (also IMM 2022 SOM §IV.H, per `FINDING-miso288`) — the same form as
the LP's fuel-budget dual, which the keeper carries at the wrong grain (flat B/12). Whether a measured fall stock path is an admissible
backcast overlay is the open owner question (§9 Q1).

**ELMP / ORDC / emergency pricing 2019–2022.** VOLL $3,500/MWh (Schedule 28, since 2007); the ORDC $200 step was removed in Dec 2021;
emergency offer floors raised to $500 (Tier 1, Max Gen Warning) / $1,000 (Tier 2, Max Gen Event Step 2) in Sep 2021, with a Tier 0 at Max Gen
Alert; MISO proposes Pricing VOLL $10,000 / System VOLL $35,000 and an EDR cap fixed at $3,500 (MISO Updated Shortage Pricing White Paper,
Nov 2024, pp. 1–3, 10–23: https://cdn.misoenergy.org/MISO%20Updated%20Shortage%20Pricing%20White%20Paper%20-%20Nov%202024663437.pdf;
2021 SOM p. xii). The keeper prices declared windows at $1,000 (2023) / $500 (2024) (`RESULT-rmiso` S-2); for pre-Sep-2021 windows the
then-effective floors apply (§9 Q2). `ordc_voll=5000` in `run_config.json` is the shared default, not MISO's $3,500 — a citation to check
if scarcity pricing is ever armed for MISO (it is off: `scarcity_pricing_enabled=false`).

**VLR / load pockets (the C1 ST_GAS 2019 object).** 2021 SOM: "almost all day-ahead VLR costs are accumulated in two load pockets in MISO
South"; day-ahead RSG 2021 $98.5 M of which VLR $16.2 M and Western Op Guide (WOTAB) $55.7 M; three new CCs >3 GW entered MISO South May 2019
– Jan 2021 "which should reduce the need for VLR commitments" yet monthly VLR more than doubled in 2021 because the WOTAB operating guide
was not updated for a >1 GW entrant (pp. 44–46). IMM South report Jul 2025: VLR = 25 % of MISO-wide RSG; May 25 2025 600 MW load shed in
Amite South after a 500 kV outage cut flows from Southeast Texas; recommendations: local STR requirements for load pockets and PRA capacity
zones that reflect electrical load pockets (https://cdn.misoenergy.org/20250729%20ERSC%20Item%2005%20IMM%20South710660.pdf slides 7–13).
MTEP22 voltage-stability scope names the two transfer paths (Entergy → WOTAB via Mt Olive–Hartburg 500 kV; Entergy → DSG/Amite South via
Franklin–McKnight 500 kV) (https://cdn.misoenergy.org/20220412%20PSC%20Item%2005b%20MTEP22%20Voltage%20Stability%20Analysis623903.pdf).
*Inference:* a pocket-balance constraint (load − import limit) is how production-cost models (PLEXOS/Aurora "must-run for voltage" or nodal
security constraints) carry VLR; our zonal LP can carry it only with a published import limit.

**How established models treat these phenomena (inference from public documentation, not verified against our code line by line):**
ReEDS/NEMS carry no unit commitment and no VLR; PLEXOS/Aurora backcasts treat self-committed coal with min-stable floors and heat-rate
curves (piecewise incremental), reproducing off-peak coal margins through the incremental segment — the L3/L4 form; ISO IMMs (Potomac)
price coal conservation via reference-level adders. None publishes a tail-hour accuracy (rubric C3c note).

**MISO price-archive retention (data).** Daily `docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv` serves 2023-01-01 onward
(200) and returns 404 for 2019–2022 dates (re-probed 2026-10-02; same floor as `FINDING-miso254`). The 2019–2021 hub series on disk came
through the fetcher's monthly route (`PRECOMMIT-rmiso-corrected-inputs` §2.3); 2022 Nov 12–Dec 31 RT is the remaining hole.

## 6. DATA GAPS (FREE sources only)

| # | what | why / gate | source (URL) | directions | lands at | effort |
|---|---|---|---|---|---|---|
| 1 | MISO 2019–2021 RT/DA actual tail counts | C3c 2019–2021 SKIP → scored (2019 CAVEAT, 2020 PASS, 2021 CAVEAT) | none — data already on disk | `python scripts/data/derive_actual_tail.py` (every year emittable since 2026-09-09); commit the part citing the 2019–2021 hub intake (rule 23) | `frontend/data/backcast/tail/actual_tail.json` | minutes |
| 2 | MISO 2022 RT hub LMP Nov 12 – Dec 31 (DA Dec 10–31) | C3c 2022 count is a lower bound (86.3 % coverage); C3a/C3b 2022 masked to Jan–Oct/Nov; Elliott (Dec 23) unscored | MISO Data Exchange Pricing API (free registration) https://www.misoenergy.org/markets-and-operations/rtdataapis/ ; Market Reports https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/ | obtain `MISO_PRICING_API_KEY`; `scripts/data/fetch_miso_hub_lmp.py --years 2022` then `derive_miso_hub_lmp.py` (closes the tail per the register, `docs/holdout-data-equivalency-register-2026-07.md` §MISO update); try the monthly route that landed 2019 first | `data/raw/lmp-data/MISO/miso_hub_lmp_2022_{rt,da}_p??.csv` | owner registration + 1 fetch |
| 3 | Max Gen declaration history 2019–2021 (dates, hours, region, step) | `maxgen_emergency_tier_pricing` (K) has no 2019/2020 rows and one 2021 row; C3c 2019/2021, C3b 2021 Feb | "Maximum Generation Emergency Declarations through June 2024" (MISO on OATI): https://www.oasis.oati.com/woa/docs/MISO/MISOdocs/Capacity_Emergency_Historical_Information.pdf (SSL-blocked from the container; opens in a browser) | transcribe Alert/Warning/Event rows with declared hours and region into the schema (`iso,region,level,start_local,end_local,declared_precision,source_url,...`); keep EEA levels in notes per the schema's closed vocabulary | `data/raw/maxgen-events/miso/miso.csv` | 1 h transcription |
| 4 | Pocket import limits for WOTAB and DSG/Amite South (MW) | reopens `scuc_load_pocket_commitment` (G) → C1 ST_GAS 2019 | MTEP22 Chapter 4 Reliability Studies https://cdn.misoenergy.org/MTEP22%20Chapter%204%20-%20Reliability%20Studies627350.pdf ; MTEP22 report/appendices https://cdn.misoenergy.org/MTEP22%20Report627345.pdf ; MTEP24 scope https://cdn.misoenergy.org/20240313%20PSC%20Item%2005b%20MTEP24%20Voltage%20Stability%20Analysis632126.pdf ; PUCT docket 46416 (MTEP15 VLR study) | look for P-V transfer-limit results (MW) for "MISO South to WOTAB" and "MISO South to DSG"; if only deltas/paths are given, record as absent | new rows in `data/raw/capacity-deliverability/miso/miso.csv` (`area_type=pocket`, `metric=import_limit`) | 1–2 h; may yield nothing |
| 5 | LOLE study CIL/CEL by LRZ for PY2019-20, 2020-21, 2021-22 | `iso_configs.py:853` applies PY2025-26 summer CIL/CEL in every backcast year; `capacity-deliverability/miso/miso.csv` starts at 2022/23 | PY2021-22 https://cdn.misoenergy.org/PY%202021%2022%20LOLE%20Study%20Report489442.pdf ; PY2020-21 (mirror) https://www.readkong.com/page/planning-year-2020-2021-loss-of-load-expectation-study-6980925 ; PY2019-20 via MISO's LOLE page | transcribe the CIL/CEL/LRR table (one page per report) | `data/raw/capacity-deliverability/miso/miso.csv` | 1 h |
| 6 | MISO ASM reserve MCP / cleared MW 2019–2022 | `miso_measured_reserve_requirements` has no input before 2023 | confirmed **ungettable** (purged; register §MISO, re-probed 2026-09-10) | none automatable; a human MISO historical-data request is the only route | — | n/a |
| 7 | EIA N3045 delivered gas, LA/MS 2018–2021 (withheld months) | MISO-South zonal gas basis 2018–2021 MISSING (register) | https://www.eia.gov/dnav/ng/ng_pri_sum_a_EPG0_PEU_DMcf_m.htm (state electric-power price) | check which months are withheld; the plant-level EIA-923 route already prices South CCs (miso-283: within ±$0.1) | `data/raw/miso_zonal_gas_hub.csv` | low value |
| 8 | 2019 MISO SOM report body | citations for 2019 VLR $ and the Jan 30 2019 event hours | appendix is live: https://www.potomaceconomics.com/wp-content/uploads/2020/06/2019-MISO-SOM_Appendix_Final.pdf ; body via https://www.potomaceconomics.com/document-library/ | reference only (not a model input) | — | minutes |

## 7. CAPACITY / VINTAGE (EIA-860) — MISO-specific findings

| item | status / numbers | source |
|---|---|---|
| Per-solve-year EIA-860 vintage | armed (`eia860_vintage_tracks_solve_year=true`) since R-MISO 2026-09-24; required companion `mid_vintage_exit_carry=true` because a plant retiring during year Y is absent from both of vintage_Y's sheets: 3.1 / 1.0 / 1.5 / 2.8 GW missing in 2019–2022 without it (Coffeen, Havana, Duck Creek, Duane Arnold, Dolet Hills, Palisades, E D Edwards, Meramec); arm B turned 2019 C1 COAL_BIT −13.17 FAIL → PASS and restored Duane Arnold (+4.1 TWh nuclear 2020) | `RESULT-rmiso-corrected-inputs-2019-2025-2026-09-24.md` §4.1 |
| Within-window retirees at class heat rate (pre-F1) | 9,766 / 11,420 MW (2019) down to 645 / 2,299 (2024); measured coal/CT/CHP rates now armed, `measured_coal_heat_rates=true` | audit §3b `docs/records/governance/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` |
| CC fleet membership by vintage | vintage_2023 carries 1.36 GW less LP CC_REGULAR than the canonical snapshot (Magnolia −679, Edwardsport −481, Cottonwood +565 MW) — "fleet membership, not heat rates"; routed, open | `RESULT-rmiso` §4.2 |
| Block-rated CC (Edwardsport IGCC) | EIA-860 reports the 555 MW block on the CA row with CTs blank → nameplate fill carried 1,036 MW; `cc_block_summer_rating` (K) repairs | log miso-272 |
| Standby (SB) units | Baxter Wilson 1 (545 MW ST_GAS) is SB in the 2021–22 vintages yet generated 0.75 / 0.31 TWh; Taconite Harbor (155 MW coal) SB and dark every year; Louisiana 2 (138 MW) no record; `admit_standby_units` parked (needs an outage companion to avoid ~1 TWh/yr phantom coal) | `FINDING-miso282` §4, `FINDING-miso284-standby-census` |
| CAMPD facility split | West Riverside CT-03/CT-04 remapped 55641 → 64020, seven companions re-derived (`campd_split_remap_companions`, keeper) | log miso-280 |
| Outage derate denominator | `outages._iso_plant_capacity` returned a static 50,365 MW of coal in every year vs the LP's 54,238 → 53,392; repaired by `unit_outage_dispatched_bin_denominator` (K, miso-266/267) — the resolution of the miso-265 "envelope infeasible vs meter" finding: 23,849 → 3,234 contradicted plant-hours, 84.5 % of the broader contradiction survives as level-short/wrong-hours shapes at per-plant-binned grain and was reported, not absorbed | log miso-266 |
| Interface limits vintage | CIL/CEL constants are PY2025-26 summer values applied to every year (`src/market_sim/config/iso_configs.py:853–902`); internal links carry 40,000 MW placeholders; RDT 3,000 N→S / 2,500 S→N matches the IMM's stated agreement limits (IMM South Nov 2024 slide 6) | code; `data/raw/capacity-deliverability/miso/miso.csv` (2022/23 onward only) |
| UCAP cross-check | IMM UCAP 2020/2021: coal 46,341 / 43,123 MW, gas 58,334 / 59,901, nuclear 11,866 / 11,701, wind 4,304 / 4,454 (≈29 GW installed) — the LP's 54.2 GW coal nameplate (2020) is consistent with ~85 % UCAP/ICAP | 2021 SOM Table 1 |
| Benchmark membership | bench fuel-family attribution settled at zero LP (classFull coal reproduces an EIA-923-by-BA reconstruction to four decimals); `benchmark_membership_vintage_union` stays O | log miso-261 |
| 2025 | C1/C2 SKIPPED on the preliminary EIA-923 vintage; re-scores when the final 2025 EIA-923 posts | `RESULT-miso298` §2.2 |

Settled, in my reading: available capacity and COD for the backcast span are now year-matched (vintage + exit carry + partial-plant carry);
the two open vintage items are the CC membership delta at Magnolia/Edwardsport/Cottonwood (routed) and the PY2025-26 interface limits
applied to 2019–2022 (data gap 5). Neither touches a failing gate directly.

## 8. RECOMMENDED CLOSE-OUT SEQUENCE

| step | kind | action | gate | pre-fixed pass reading | P(closes) |
|---|---|---|---|---|---|
| 0a | zero-LP | run `derive_actual_tail.py`; commit the MISO 2019–2021 rows citing the hub intake | C3c 2019–2021 SKIP | 2019 CAVEAT (0 vs 17), 2020 PASS (\|Δ\|=8 ≤ 10), 2021 CAVEAT (0 vs 48); determination unchanged | high (mechanical) |
| 0b | zero-LP (owner data) | transcribe Max Gen 2019–2021 declarations (gap 3); settle the pre-Sep-2021 emergency floor vintage with a constants citation; verify `ordc_voll` is not read for MISO | C3c 2019/2021, C3b 2021 Feb (inputs correctness) | windows become priced only where slack binds; expect C3c 2019 to stay CAVEAT | low for the gate, high for rule-14 hygiene |
| 1 | zero-LP census | L1 per-year transport table: derive 2019–2022 rows from own-year EIA-923; rerun the miso-297 bid-stack census and the miso-298 K-1/K-2 static checks | C3b 2021 (0.201) | census must show CC fuel ≤ keeper in 2019–2022 and no static C1 flip; then 7 shards | medium (ceiling 0.192 from miso-298; the 2019 COAL_PRB flip is the risk) |
| 2 | zero-LP census | L3 + L4 coal offer continuum: derive the MISO incremental-HR ratio; census the low-load coal marginal share and q1–q4 price at the keeper's quantity | C3a 2020 (+11.6 %) | needs ≥ −$1.0/MWh at q1–q4 without COAL_PRB 2019/2021/2022 leaving the band; the miso-297 bounds say L3 alone gives ≤ $1 — L4 is the form that can reach the ~$15 real margin | low–medium; honest ceiling without congestion is ≈ +7 % (miso-296 §1.6) only if the whole margin-level part closes |
| 3 | full span (7 shards) | one bundle carrying 0b + whichever of 1/2 passed its census; writes `unit_marginal_<y>.parquet` (rule 15) — required for any promotion | all | kill rules ex ante as in PRECOMMIT-miso298 §5 | — |
| 4 | zero-LP | C1 ST_GAS 2019: after step 3, re-read the 3 GWh miss; do not build anything aimed at it (rule 1) | C1 2019 | only an incidental rule-14 move closes it | low |

Likely NOT closable in this model class (energy-only zonal LP, no MIP, no scarcity adders beyond the structural ORDC family) and better
ledgered with the owner's routing: (a) the West/Plains congestion share of C3a 2020 (~4.4 pts; `internal_congestion_split` G);
(b) C1 ST_GAS 2019 as VLR out-of-merit commitment without a published level (G); (c) C3b 2021 February (Uri congestion/emergency pricing
and storm-month gas); (d) the fall-2021 coal conservation unless the owner admits a measured stock path (§9 Q1); (e) C3c tails everywhere
(emergency-tier and sub-hourly scarcity, already ledgered). If (a)–(d) stay routed, MISO's full-span determination remains NOT-YET by the
owner's own "no frontier" rule, and the honest close-out is a documented frontier statement plus the step-0/3 hygiene above.

## 9. OPEN QUESTIONS FOR THE OWNER

1. **Rule 13 scope of EIA-923 monthly coal receipts/stocks.** F923 delivered *fuel price* is an admitted backcast overlay; are measured
   monthly receipts and month-end stocks (the same form, per yard) admissible as a backcast fuel-availability overlay? If yes, the fall-2021
   conservation (60 % of the C3b 2021 SSE) becomes a buildable per-yard monthly take ceiling with a forward analogue (contract delivery
   rate); if no, C3b 2021 is a permanent routed miss and the coal line stays closed.
2. **Emergency-floor vintage and Max Gen registry completion.** Authorize transcribing the OATI declaration history (gap 3) and rule which
   floors apply before Sep 2021 (the $500/$1,000 tiers did not exist; VOLL was $3,500).
3. **C1 ST_GAS 2019 at 3 GWh outside the band.** Keep it routed, or accept that an incidental rule-14 input move (e.g. the standby
   companion, bench membership) may flip it without a dedicated lever?
4. **Attestation rule 1(e).** The keeper's `authorized_price_tuning` block is null while the miso-275 CC exemption from the ×1.10 lift is a
   rule-1 channel use; confirm whether the next attestation must declare it.
5. **Interface-limit vintage.** Adopt per-planning-year LOLE CIL/CEL for 2019–2022 (gap 5) or keep the PY2025-26 static values; this
   matters only if the CIL/CEL groups ever bind, which no record says they do.
