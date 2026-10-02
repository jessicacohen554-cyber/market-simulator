# LEDGER — miso-301: lever exhaustion for MISO's three open full-span failures. C1 ST_GAS 2019 is exhausted; C3a 2020 and C3b 2021 each have one sized, admissible lever not yet adjudicated in MISO, and both are already assigned to the parallel close-out lane. No solve.

```
LANE    : miso-301 (owner ruling 2026-10-02, miso-300 card "What should miso-301 do?": "Record; next zero-LP object (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, legs at 8f765fef), unchanged
LP      : none. Records only, plus one fleet-free probe (the PRB proxy pool series, §4.4)
SOURCES : the records cited per row; docs/codebase-site/data/mechanism-matrix/MISO.js (every U/O cell swept, §4);
          docs/backcast-closeout-plan-2026-10.md §3.3 and §5.0 (owner rulings R-3 and R-15, 2026-10-02)
CELLS   : no verdict moves. Evidence added to coal_prb_proxy_own_iso (O) and committed_band_measured_basis (U)
```

## 0. Pre-stated readings (written before any phase-0 number on either candidate)

Two candidates pass the §4 screen: sized to a failure, admissible with a non-residual identification source, and
not adjudicated R/I/G in MISO under another name. Neither is run here (§5 says why). These are the readings any
lane that runs them should be held to.

**R-A. L3 + L4 coal offer continuum, for C3a 2020** (`coal_econ_two_sided` U, plus a rule-28 retest of
`coal_prb_committed_split` R with new evidence; replaces the `coal_takeorpay_committed` K discount, never stacks
on it).
- Target. C3a 2020 is +11.6 % (+$2.54 on $21.97). The gate needs ≤ +10 %, i.e. **−$0.35/MWh** load-weighted.
  Quintiles 1–4 each carry +$0.67–0.73 (miso-296 §2).
- Expected direction. The cycling slice and the econ tranches priced at measured incremental heat rate fill the
  $9→$30 hole in the coal curve (miso-296 §1.4). Coal enters the low-load margin, and q1–q4 prices fall. An
  average of −$0.5/MWh across q1–q4 hours would clear the gate.
- Expected size. L3 alone moves up to ~−$1 at q1–q2 (close-out plan §3.3); q1–q2 are 40 % of hours, so at most
  ≈ −$0.4 annual. L4 is the form that can reach the ~$15 real coal margin.
- The kill risk is quantity, not price. Lower coal offers mean more coal burned. Keeper C1 COAL_PRB is +6.40 (2019)
  and +5.69 (2021) against an 8.00 band: 1.6 and 2.3 TWh of headroom. miso-298 flipped COAL_PRB 2019 to +8.63 by
  moving gas the other way.
- **Reading:** the lever clears C3a 2020 only if the static census shows q1–q4 falling ≥ $0.5 in 2020 **and**
  static coal ≤ +1.5 TWh in 2019 and ≤ +2.2 TWh in 2021. If the census meets the price bar but misses the coal
  bar, it reproduces the miso-297 regime split, and the lever is recorded rather than solved.
- **Ceiling:** about +7.2 %. The West/Plains congestion share, ~4.4 pts, is G (`internal_congestion_split`) and is
  not reachable by any offer lever.

**R-B. EIA-923 receipts + month-end stock take ceiling (owner ruling R-3), for C3b 2021**
(`coal_fuel_inventory` family; the vehicle is the `coal_monthly_pile_measured_receipts` form, U and NWPP-gated).
The ceiling is per yard and month: burn ≤ receipts + (opening stock − `stock_min`). Under rule 19 it **replaces**
the pooled B/12 limb and the yard rows (both K); it never stacks on them.
- Target. C3b 2021 is 0.201 against a 0.20 cap, so it needs about a 1 % cut in the summed squared error (SSE).
  Sep–Nov carry 60 % of the SSE; Feb (Uri, routed) carries 24 % (RESULT-miso294 Part B).
- **Fall, Sep–Nov.** Do not expect it to bind at fleet grain:
  - The real pile sat at 57.6 days, against a prior-years minimum (`d_min`) of 46.1 days, so there is ~11.5 days
    (≈ 4.4 Mt) of slack each month (FINDING-miso295 §4.5).
  - The model's fall coal excess is +1.7 / +3.6 / +3.3 TWh/month, about 10–20 % of monthly burn. The ceiling cuts
    only where a yard's excess exceeds ~38 % of its monthly burn.
  - The real hold was precautionary: the pile was held above any admissible `stock_min`. Setting `stock_min` at
    the realized level would be choosing the answer (rule 13).
- **Summer, Jun–Aug.** Expect it to relieve:
  - The real fleet burned 10.3 Mt above receipts, so a ceiling built from receipts plus stock cannot hold the model
    below actual burn.
  - Replacing B/12 lifts the keeper's Jul/Aug coal shortfall (−3.3 / −3.9 TWh) and lowers summer prices that run
    +$3.2 / +$4.1 high.
- **Reading:** if C3b 2021 clears, it clears through summer relief, not the fall hold. That pass is legitimate only
  as the structural consequence of retiring B/12 under rule 19, and the PRECOMMIT must say so before any solve.
- **Kill risk:** 2022. The B/12 cap binds May–Sep there (miso-288); relieving it raises summer-night coal, and
  2022 C1 COAL_PRB (+5.28) and the 2022 night premium are the guards. The fall-2021 share of C3b stays a ledger
  row unless the per-yard census shows yards binding in Sep–Nov.

## 1. The three failures (keeper, live scorer)

| failure | keeper value | band | status | owner routing |
|---|---:|---:|---|---|
| C1 ST_GAS 2019 | −8.003 TWh | ±8.00 | FAIL by 3 GWh | ROUTED (miso-281 ruling 2026-09-28; re-affirmed R-15 2026-10-02: "keep C1 ST_GAS 2019 routed") |
| C3a 2020 | +11.6 % | ±10 % | FAIL | not routed; no admissible identified lever until this ledger |
| C3b 2021 | 0.201 | ≤ 0.20 | FAIL | Feb Uri share ROUTED (miso-269/280); the fall share is the coal-conservation object (miso-294/295) |

Under the owner clarification of 2026-09-28, a routed miss is still a failure, so MISO is not at frontier.

## 2. Levers tested or refused, per failure

### 2.1 C1 ST_GAS 2019 (−8.003 TWh)

| lever / mechanism | MISO cell | adjudicating record | outcome for this miss |
|---|---|---|---|
| `campd_st_gas_span_coverage` (ST_GAS tranche rows 2019–25 from own CEMS) | K | RESULT-miso279 (promoted) | −8.46 → −8.20 |
| `campd_split_remap_companions` | K | RESULT-miso280 (promoted) | −8.20 → −8.003 |
| in-merit shortfall hypothesis | — | FINDING-miso281 §2 | refuted: model ST_GAS = its price-taker envelope; 85 % of real 2019 South steam ran below its own marginal cost |
| `scuc_load_pocket_commitment` (VLR pocket commitment, RO-2) | **G** | FINDING-miso284-ro2 (owner "Mark blocked") | identification-blocked: the pocket MW/limit is unpublished |
| `admit_standby_units` | U (PARKED by owner) | FINDING-miso282 §4, FINDING-miso284-standby | admits **0 MW** of ST_GAS in 2019 — cannot reach this miss |
| per-year ST_GAS floor from 2019's own CEMS | — | rule 13 | refused: pins a class to observed generation |
| `mustrun_window_commitment_grain` (SPP's ST_GAS online-hour floor form) | U | not run | rule 19: the 2023–25-measured floors already carry the floor part (miso-281 §2); the miss is out-of-merit commitment *above* the floors, and a 2019-measured window would be the refused form above |
| W0 seasonal capacity basis (R-2) | n/a (foundation lane) | close-out §2.1 | not a lever: available ST_GAS 56.2 TWh vs model 14.1 (miso-281 §2); capacity does not bind |

**Exhausted.** The owner ruled it routed twice (2026-09-28, 2026-10-02 R-15: "do not build for a 3 GWh miss").
It closes only on an incidental rule-14 move or a published pocket limit.

### 2.2 C3a 2020 (+11.6 %)

| lever / mechanism | MISO cell | adjudicating record | outcome |
|---|---|---|---|
| zone-resolved C3a basis | adopted (owner) | RESULT-miso294 Part A | flipped 2020 PASS→FAIL (+11.6 %); basis is correct (rule 14) |
| `internal_congestion_split` (West/Plains, ~4.4 pts) | **G** | DESIGN-miso293, CHARTER-miso292 §9 | killed; reopens on RO-1 only |
| `diurnal_price_amplitude` | **G** | miso-287 | closed |
| `miso_gas_ecomin_online_floor` | **I** | FINDING-miso286 | night median ≤ $0.12 |
| coal budget-grain family (`coal_fuel_inventory_monthly_pile`, `_take_floor`) | **R** / **R** (`coal_fuel_inventory` K) | FINDING-miso289/290/295 | closed; budget dual ≤ $0.94 of the night residual in glut years |
| startup markup | — | FINDING-miso287 | zero at the low-load margin |
| `gas_marginal_commodity_pricing` + `gas_variable_transport` (owner-ruled gas form) | **R** / **R** | RESULT-miso298 (K-1 kill), FINDING-miso299, FINDING-miso300 | C3a 2020 +11.6 → +14.1 % solved; per-year and lag-aware re-fits fail their pre-stated rules |
| `offer_curve_by_group` coal econ bands via the IMM SMP-share census | K (channel) | FINDING-miso297 | not identifiable under rule 1(b): one value, two regimes |
| `seam_neighbour_hourly_ladder` | K | RESULT-miso260, FINDING-miso296 §3 | not re-opened |
| `measured_offer_surface` | **R** | miso-151 | identification refuted |
| coal self-commitment floor | refused | miso-224 (rule 19) | miso-53 per-plant must-run band is the representation |
| `negative_renewable_offers` / `wind_ptc_vintage_offers` (L5) | `·` | FINDING-miso296 §1.5 | <$10 tail is +$0.25 of +$2.54: a companion at most, never the carrier |
| `committed_band_measured_basis` | U | FINDING-miso283 §3 | §4.2: wrong sign |
| **L3 `coal_econ_two_sided` + L4 committed-band continuum** | U / retest of R with new evidence | not yet run in MISO | **candidate R-A (§0)** |

### 2.3 C3b 2021 (0.201)

| lever / mechanism | MISO cell | adjudicating record | outcome |
|---|---|---|---|
| Feb 2021 Uri (24 % of SSE) | routed (owner "Leave as routed miss") | RESULT-miso280, miso-269 | no admissible daily Gulf-hub print |
| `miso_winter_gas_daily_delivered` | K | RESULT-miso277 | 0.290 → 0.254 |
| `gas_coldsnap_derate` | **I** | miso-194 | refuted at its absorption line |
| `maxgen_emergency_tier_pricing` | K | miso-210 | in keeper |
| `ordc_scarcity_overlay` | **G** | miso-163 | closed |
| gas form, per-year / lag-aware transport | **R** | RESULT-miso298, FINDING-miso299/300 | the solved arm took C3b 2021 to 0.192 but was killed on K-1; both re-fits fail |
| fall coal conservation via the budget family (pile, take floor) | **R** / K | FINDING-miso289/290/295 | closed; the fall row needed the year-Y stock path (then rule-13 refused) |
| **R-3 receipts + stock take ceiling** | family K/R; vehicle U | owner ruling R-3 (2026-10-02) lifts the miso-295 §4.3 rule-13 objection | **candidate R-B (§0)** |

## 3. Owner rulings that bear on the ledger (verbatim where recorded)

- 2026-09-28 (miso-281): "do NOT call MISO 'frontier' while the rubric does not clear across all years, holdouts
  included. Owner-ruled routed misses are still failures."
- 2026-10-02 R-3: "EIA-923 monthly coal receipts and month-end stocks are admissible as a backcast
  fuel-availability overlay (rule 13) — a per-plant monthly take ceiling (receipts + stock envelope with a declared
  `stock_min`), never the burn; forward analogue = contract delivery rate."
- 2026-10-02 R-15: "MISO: transcribe the Max Gen declaration history (owner downloads the OATI PDF); keep C1
  ST_GAS 2019 routed."

## 4. Sweep of every U and O cell in MISO.js against the three failures

Test applied to each cell: (i) sized to a failure, (ii) admissible under rules 1/13/14/19 with a declared
non-residual identification source, (iii) not already adjudicated R/I/G in MISO under another name. The read for
each cell was written before computing anything about it. Only §4.4 then ran a probe, a fleet-free price series.

### 4.1 Pass all three: the two candidates of §0
- `coal_econ_two_sided` (U). (i) C3a 2020 q1–q2; (ii) identified from CAMPD heat-input-vs-load slopes;
  (iii) never run in MISO, because the incremental-HR ratio is derived for SOCO only. Its L4 extension retests
  `coal_prb_committed_split` (R, miso-112). That R was adjudicated on the retired C7 amplitude criterion, before
  measured coal HR, the yard grain and the zone-resolved basis. The close-out plan §3.3 names miso-296/297 as new
  evidence. → **R-A**.
- `coal_monthly_pile_measured_receipts` (U, NWPP-gated) as the vehicle for R-3. (i) The C3b 2021 fall share, and
  through rule-19 replacement the summer share. (ii) Owner ruling R-3. (iii) The family's R cells were refused on
  identification that R-3 now admits. → **R-B**.

### 4.2 Fail (i): sized against the failure, or the wrong sign
- `committed_band_measured_basis` (U). miso-283 §3: it raises coal committed by +$18–29/MWh on 17 GW. That moves
  coal **up** toward the ~$30 econ level, which fills the hole from above and raises low-load prices: the wrong sign
  for C3a 2020. It also collides with the take-or-pay basis under rule 19. Not a candidate.
- `mustrun_chp_btm_holdout` (O, miso-253). A rule-14 correction that cuts injected "other" (model 2.3 GW vs
  EIA-930 0.7 GW at low load in 2020; miso-296 §5). Removing must-run supply at low load **raises** q1 prices: the
  wrong sign for C3a 2020. Under rule 14 a correct input that worsens fit is still taken, and the overshoot is then
  understated by today's keeper. It is not a lever for any failure.
- `vre_curtailment_oversupply_allocation` (U). Corrects the +4.7–5.1 TWh wind gross-up (miso-206/234). Less wind
  raises low-load prices: the wrong sign for C3a 2020. Same rule-14 note.
- `coal_subclass_at_load` (O). Moves only the former generic-bucket plants: 2,140 MW in 2019, 20 MW by 2024. Not
  sized to C3a 2020; carried by the next re-solve.
- `unit_outage_extract_basis_share` (O, miso-274). CC_REGULAR availability binds in 0–13 h/yr; not a price lever.
- `admit_standby_units` (U, parked). 0 MW ST_GAS in 2019 (§2.1); the C3 years are price objects.
- `gas_commitment_bridge`, `cc_mustrun_conduct_window`, `measured_ramp_capability` (U). The CC commitment object
  is sized at ≤ $0.12 (miso-286, I), so rule 19 points at the I cell.
- `benchmark_membership_vintage_union`, `outage_artifact_provenance` (O). Benchmark and provenance hygiene, not
  failure levers.

### 4.3 Fail (iii): already adjudicated under another name (rule 28 / rule 19)
- `gas_offer_margin_zonal_anchor_vintage` (U). The MISO resolver refuses the cell (a build task). The gas-price
  object is closed R (miso-298/299/300), and `gas_offer_margin_anchor_vintage` is K: a rule-19 collision.
- `coal_sync_*`, `coal_committed_nested_on_mustrun`, `mustrun_window_commitment_grain`,
  `commitment_floor_window_netload`, `reliability_floor_layup_window_mask`, `mustrun_commitment_feasibility_clip`,
  `coal_mustrun_requires_measured_row` (U). Floor and commitment forms. The coal self-commitment floor was refused
  under rule 19 (miso-224), `miso_coal_night_floor` is I (miso-113), and C3a 2020 is an offer-level object, not a
  quantity object (miso-296 §5).
- `coal_offer_net_revenue_margin`, `coal_peak_offer_margin`, `coal_perplant_offer_level` (U). Coal offer-level
  adders. The only admissible coal-price channel is the rule-1 band (K; not identifiable, miso-297), and a per-plant
  level fitted to the residual is forbidden (rule 1).
- The `unit_outage_*`, `campd_*`, `iso_*` membership, heat-rate-family, hydro, storage and capacity-evolution
  (forecast) U/O rows. Quantity and fleet hygiene, or forecast-only; none is sized to the three failures.

### 4.4 Settled by a cheap probe: `coal_prb_proxy_own_iso` (O)
Read stated first: a rule-25 correctness repair. MISO non-reporting PRB plants are priced on ERCOT-pool rail
economics; its sign for C3a 2020 depends on whether MISO's own PRB reporters paid more or less than ERCOT's.

Probe: `market_sim.data.fuel.coal._prb_monthly_actuals(None)` vs `("MISO")`, annual means of the monthly series,
$/MMBtu:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ERCOT pool (keeper) | 1.788 | 1.664 | 1.731 | 1.936 | 1.823 | 1.752 | 1.615 |
| MISO own PRB pool | 1.905 | 1.797 | 1.928 | 2.182 | 2.184 | 2.147 | 2.186 |
| Δ | +0.117 | +0.133 | +0.197 | +0.246 | +0.361 | +0.395 | +0.571 |

Arming the repair **raises** the proxied plants' delivered cost (2020: +$0.13 × HR ~11 ≈ +$1.5/MWh on their
offers). That is the wrong sign for C3a 2020. It would trim C1 COAL_PRB 2019/2021/2022 slightly; those are passing
and not failures. Read: a correct rule-25 repair for the next MISO re-solve, **not a lever** for any failure. The
cell stays O.

## 5. Why this lane does not run R-A or R-B

The DESK orchestrator launched the parallel close-out lane (`closeout-MISO`, branch `claude/closeout-miso-wave1`)
at 05:13 the same morning, under close-out plan §3.3. It runs exactly R-A (step 2, "L3 + L4 census") and R-B
("R-3 conservation"), after the C3c 2019–21 tail derive (step 0a). Running the same censuses here would produce two
records of one object, and conflicting edits to `MISO.js` and `docs/calibration-log/miso.md`. This ledger therefore
fixes the readings (§0) and hands them to that lane. The owner decides whether the miso chain folds into it (§6).

## 6. Owner decision (put as a card)

- (A) **Fold the miso chain into the close-out lane (recommended).** It runs R-A and R-B against §0 and writes the
  PRECOMMIT if a reading clears. No miso-302.
- (B) Launch miso-302 to wait for the close-out census, then PRECOMMIT.
- (C) Record MISO train-tier CALIBRATED / full-span NOT-YET and move the chain to another ISO. This is not a
  frontier declaration.

## 7. Where MISO stands

Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span NOT-YET on C1 ST_GAS 2019 (routed,
exhausted), C3a 2020 (+11.6 %; candidate R-A) and C3b 2021 (0.201; candidate R-B). **No frontier.**
