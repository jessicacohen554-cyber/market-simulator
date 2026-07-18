# PJM coal operations — first-principles characterization & model audit (2026-06)

**Date:** 2026-06-23. **Type:** characterization + audit (NO LP solve, no keeper).
**Update 2026-06-24:** Thread D layers 1-3 are now BUILT and solved — keeper
*pjm 47 sync-srmc* (online%-scaled SRMC synchronization forcing on the fully
re-derived thermal tranches). See the updated Thread D below; the only remaining
structural step is 3b (reserve co-opt), still memory-blocked.
**Probe:** `scripts/probes/_pjm_coal_opfingerprint.py` (CAMPD/CEMS hourly + PJM
hourly hub LMP, reproducible). **Status:** the empirical groundwork the prior
coal sessions skipped — it refines (does not overturn) the standing conclusion
that the residual is downstream of price formation, and it pins *exactly* where
the model's coal representation is unphysical and what a data-grounded rebuild
looks like.

## TL;DR

1. **PJM bituminous is a synchronized partial price-FOLLOWER, not rigid
   baseload and not a full-cost swing fuel.** Fleet (24 plants, ~110-133 TWh/yr):
   annual CF **0.46-0.54**, low-price-quartile / high-price-quartile CF ratio
   **0.63-0.76**, corr(hourly CF, LMP) **+0.17 to +0.23**, afternoon CF clearly
   above overnight. It backs down ~30% between cheap and dear hours but **never
   collapses** — it stays *synchronized* (large units online 80-100% of the year)
   at a low technical minimum. Year-stable 2023-25.
2. **The real online minimum (Pmin) is ~15-31% of max**, not the 40-60% the model
   forces. The model's `mustrun_pct` floor is ~2x the level CEMS shows these units
   actually hold, and it is **forced on** while **bidding sub-cost** (VOM+carbon
   only, fuel treated as 100% sunk take-or-pay). That single tranche both
   over-produces coal volume *and* suppresses the price coal sets when marginal.
3. **Merit-order inversion (the cross-cutting finding):** in cheap-gas 2024 PJM
   gas CC is *more* baseload than coal — CC fleet low/hi-price CF ratio **0.86**
   (corr +0.10) vs coal **0.63** (corr +0.23). Real merit order: cheap CC carries
   baseload, **coal swings on top**. The model prices coal *below* gas (sub-cost
   must-run + 0.76 sigmoid discount), inverting this → coal baseloads, both
   coal and gas flood the over-export, and the LMP is suppressed.
4. **Part-load heat-rate degradation is small** (Pmin HR penalty 0-8%, often ~0).
   The offer-curve *slope* is NOT a heat-rate-curve problem; it comes from the
   take-or-pay/spot fuel split. Do not over-engineer a piecewise HR curve.
5. **The data-grounded rebuild** (Thread D) replaces the forced sub-cost floor
   with three physically-sourced layers — a small **take-or-pay sunk floor**
   (EIA-923 Schedule-5 *Purchase Type*), a **synchronization min-load** that stays
   online but bids real SRMC, and **full-delivered-cost dispatchable** tranches
   above. This reproduces the observed "synchronized but price-following" behaviour
   *endogenously*. It must be co-designed with reserve co-optimization (the
   afternoon $75-200 price), which carries the LMP level the coal offer alone
   cannot (coal is sole price-setter only ~9% of hours).

---

## Thread A — how PJM bituminous ACTUALLY operates (CEMS ground truth)

Per-plant fingerprint from EPA CAMPD hourly gross MW + heat input, priced against
PJM Western Hub RT LMP. Pmax = P99.5 of unit gross; Pmin = P5 of gross over
online hours. Bituminous = the model's own `coal_supply_PJM.csv` rank.

### 2024 top plants (operation & price response)

| plant | id | Pmax MW | ann CF | online Pmin% | online% | starts | %hrs<40% | CF lowP-q | CF hiP-q | **low/hi** | corr(CF,LMP) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Harrison | 3944 | 2110 | 0.62 | 26 | 100 | 1 | 23 | 0.61 | 0.68 | **0.89** | 0.13 |
| Gavin | 8102 | 2901 | 0.44 | 24 | 80 | 10 | 22 | 0.28 | 0.56 | **0.50** | 0.24 |
| Amos | 3935 | 3132 | 0.38 | 15 | 100 | 1 | 64 | 0.33 | 0.49 | **0.66** | 0.39 |
| Cardinal | 2828 | 1939 | 0.60 | 26 | 99 | 2 | 17 | 0.50 | 0.68 | **0.73** | 0.21 |
| Spurlock | 6041 | 1483 | 0.65 | 20 | 100 | 1 | 20 | 0.52 | 0.74 | **0.71** | 0.23 |
| Miami Fort | 2832 | 1121 | 0.62 | 31 | 87 | 8 | 7 | 0.37 | 0.77 | **0.48** | 0.29 |
| Clifty Creek | 983 | 1310 | 0.50 | 25 | 100 | 1 | 37 | 0.45 | 0.55 | **0.82** | 0.16 |
| Kyger Creek | 2876* | 1113 | 0.56 | 20 | 96 | 2 | 19 | 0.47 | 0.65 | **0.73** | 0.25 |
| Rockport | 6166 | 2745 | 0.22 | 20 | 52 | 7 | 23 | 0.14 | 0.35 | **0.39** | 0.29 |
| Mountaineer | 6264 | 1423 | 0.42 | 54 | 66 | 5 | 1 | 0.41 | 0.49 | **0.84** | 0.09 |
| Mitchell (WV) | 3948 | 1672 | 0.31 | 18 | 82 | 8 | 50 | 0.26 | 0.38 | **0.68** | 0.23 |

\*`coal_supply_PJM.csv` ranks 2876/879 subbituminous (PRB); shown for the
named-plant comparison. The Pmax = P99.5-of-gross basis differs from the model's
nameplate basis, so CF *levels* are not directly comparable to `median_cf`; the
**ratios and correlations are denominator-free** and are the load-bearing result.

### Fleet aggregate (GWh-weighted), year-stable

| year | plants | TWh | ann CF | online Pmin% | overnight/afternoon CF | **low/hi price ratio** | corr(CF,LMP) |
|---|---|---|---|---|---|---|---|
| 2023 | 24 | 110.4 | 0.47 | 27 | 0.42 / 0.51 | **0.76** | 0.17 |
| 2024 | 24 | 116.8 | 0.46 | 27 | 0.41 / 0.49 | **0.63** | 0.23 |
| 2025 | 23 | 133.2 | 0.54 | 31 | 0.50 / 0.55 | **0.65** | 0.19 |

**Reading.** A pure baseload price-taker would show low/hi ≈ 1.0 and corr ≈ 0; a
full-cost merit swing fuel would show low/hi ≪ 0.5 and a steep collapse in cheap
hours (the pjm_43 outcome, coal -46%). PJM bituminous sits **between** at ~0.63
with a real positive price correlation: it *does* back down when prices are low
(refuting "rigid baseload") but *does not* collapse (refuting "full-cost swing").
There is a **spectrum**: a few large supercritical units are near-baseload
(Harrison 0.89, Mountaineer 0.84, Clifty 0.82); the rest are moderate swingers
(Gavin/Miami Fort/Rockport 0.39-0.50). Smaller/older units cycle (Rockport online
52%, 7 starts; Gavin 10 starts); the big supercriticals stay synchronized
(Harrison/Amos/Spurlock/Cardinal online 99-100%) but **deeply backed down** (Amos
online 100% yet <40% of max in 64% of hours).

### Part-load heat rate (CEMS heatInput / gross MW, median by load band)

| plant | 30-45% | 45-60% | 60-80% | 80-100% | Pmin HR penalty |
|---|---|---|---|---|---|
| Harrison | 9.35 | 9.28 | 9.32 | 9.32 | ~0% |
| Amos | 9.87 | 9.57 | 9.40 | 9.32 | +6% |
| Cardinal | 9.80 | 9.70 | 9.61 | 9.48 | +3% |
| Clifty Creek | 10.18 | 10.10 | 9.87 | 9.46 | +8% |

The part-load HR penalty is **small** (0-8%). The offer-curve slope is not a
heat-rate-curve artifact; flat tranche HR multipliers are adequate. The slope
that matters is the **fuel-cost** split (sunk take-or-pay vs avoidable spot).

---

## Thread B — what drives the offer (mapped to data)

| offer component | reality | data source (forward-reproducible) | in model today |
|---|---|---|---|
| delivered fuel | ~$3.0/MMBtu bit 2024; bit SRMC ~$32/MWh (HR ~10.5) | EIA-923 Sch-5 receipts ($/MMBtu) | yes (`derive_coal_supply`/`fuel`) |
| **take-or-pay vs spot** | the must-burn sunk share that holds coal on below cost | **EIA-923 Sch-5 `Purchase Type`** (Contract/Spot/Tolling) — *deriver + wiring now built (default off)* | **assumed** (must-run = 100% sunk) → measured when `coal_takeorpay_from_data` |
| part-load HR | small (0-8% at Pmin) | CEMS heatInput/gross | flat tranche multipliers — adequate |
| VOM + reagents (SCR/SNCR, FGD) | modest $/MWh | constants/citations | yes |
| NOx/SO2 (CSAPR) | allowance $ in SRMC | CSAPR allowance prices | partial (nox_rate) |
| CO2 | none in PJM (VA left RGGI) | per-state | n/a |
| start cost / min-run | high coal start cost → self-commit, avoid cold starts | NREL start costs (`BIN_STARTUP_COST_PER_MW` COAL=100) | P1 amortized markup only (no true UC) |
| **CP must-offer** | Capacity-Performance resources must offer energy + face non-perf penalties → a real reason committed coal stays offered through cheap gas | PJM capacity construct (structural) | not represented (proxied by forced floor) |
| commitment hysteresis | stay synchronized at min-load rather than two-shift | — (UC economics) | proxied by forced must-run floor |

**The honest reframe (confirmed):** the keeper's "forced must-run floor + 0.76
sub-cost discount" is a **reduced-form UC + take-or-pay + CP-must-offer proxy**.
The data shows the proxy is mis-sized in two ways: the floor is **too high**
(40-60% vs real online Pmin ~25%) and **too rigid** (forced flat, no price
response, when CEMS shows low/hi 0.63), and its **bid is too cheap** (fuel-free
when much of the burn is avoidable spot and the unit is often above gas in merit).

---

## Thread C — model representation audit

Source: `scripts/data/derive_thermal_tranches.py`, `thermal_tranches_PJM.csv`,
`fleet.apply_coal_tranches`, `COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]`.

**Must-run floor** (`derive_thermal_tranches.py:449`): coal `mustrun_pct` = P5 of
**all-hours** available-CF (net / nameplate·avail), capped **0.60**. Resulting
floors: Keystone/Cardinal/Harrison **60**, Conemaugh 58, Spurlock 56, Kyger 48,
Gavin 48, Mt Storm 44, Mountaineer 40, Rockport 39, Amos ~37. This tranche is
**forced on** and bids **VOM+carbon+NOx only** (fuel sunk). Two problems vs CEMS:
- **Level:** the level a unit holds 95% of its *online* time is ~15-31% of max
  (denominator-adjusted ~20-30% of nameplate), roughly **half** the 40-60% floor.
  The all-hours-P5-on-nameplate metric reads high because (a) nameplate < CEMS
  P99.5 gross, (b) outage-derate inflates avail-CF, (c) for an ~always-online unit
  the all-hours P5 sits in its normal operating band, not its true minimum.
- **Rigidity + price:** forced + sub-cost = flat cheap baseload. CEMS shows
  price-following backdown (low/hi 0.63) the forced floor cannot produce, and the
  sub-cost bid is what suppresses the LMP coal sets when marginal and feeds the
  over-export.

**Gas-keyed sigmoid** (`COAL_SIGMOID_DEFAULTS` floor 0.76 / ceil 1.32 / mid 3.40):
discounts above-must-run bit fuel to 76% of delivered when gas is cheap. This is a
**calibrated discount, not a measured contract share** — the ungrounded knob. It
exists to hold coal in merit against cheap gas, i.e. it is a *fitted* stand-in for
take-or-pay + CP-must-offer.

**Commitment:** P0→P1(+amortized startup)→P2 (decommit, **OFF** for PJM). No true
min-run/min-down, so the synchronization hysteresis that keeps real coal online at
min-load is carried entirely by the forced floor.

**Net:** both coal layers (forced floor + sigmoid) bid **below cost**, so the
whole coal stack clears under gas → coal baseloads below gas (merit inversion §E),
floods the over-export, and suppresses LMP — exactly the keeper's symptom
(coal +9%, net-export +27/+15/+82%, LMP -3/-8/-15%).

---

## Thread D — the data-grounded rebuild (LP-only, no MIP)

Replace the single forced sub-cost floor with **three physically-sourced layers**,
each forward-reproducible (CLAUDE.md #11), so the synchronized-but-price-following
behaviour emerges instead of being forced:

1. **Take-or-pay sunk floor (small) — BUILT (default off).** Size from EIA-923
   Schedule-5 `Purchase Type` = the contract (must-burn) share of each plant's
   delivered tonnage; only that fraction bids fuel-free. Implemented this session:
   `scripts/data/derive_coal_takeorpay.py` writes `coal_takeorpay_<ISO>.csv`,
   `fleet.coal_takeorpay_share` loads it, and `ScenarioConfig.coal_takeorpay_from_data`
   makes the coal must-run tranche pass `1 - contract_share` of its fuel instead
   of the hardcoded 0.0 (`campd_tranche_fuel_frac`). This is the *measured* version
   of the 0.76 discount. **Remaining:** run the deriver where the raw `f923_*.zip`
   archives live, then re-solve PJM 2023-25 with the flag on.
2. **Synchronization min-load — floor re-sizing BUILT (default off).** The first
   half (the floor *level*) is implemented: the deriver
   (`derive_thermal_tranches.py`) writes per coal plant a
   `mustrun_online_pct` = P5 of online *net MW* / nameplate — the genuine online
   Pmin (~20-30%) — alongside the all-hours `mustrun_pct` (~40-60%, which reads
   high for an always-online unit). `ScenarioConfig.coal_mustrun_online_pmin`
   (threaded through `thermal_tranche_overrides` → `fleet_to_bins` and the
   calibration solve path) selects it for coal.
3. **SRMC-priced synchronization tranche + forced synchronization — BUILT (step
   3a, default off).** `ScenarioConfig.coal_sync_srmc_tranche` splits the
   online-Pmin coal min-load band by the measured EIA-923 contract share into a
   fuel-free `_mustrun` floor (contracted) + a full-SRMC `_sync` band (spot), and
   **forces both ON** via `FleetArrays.min_gen` (`Generator.coal_sync_pmin_mw`),
   so the unit holds synchronized at min-load bidding real SRMC instead of
   price-following to zero, while the **full-delivered-cost dispatchable
   tranches above still back down in cheap hours** (the observed low/hi 0.63).
   The forcing is **online%-scaled** (`Generator.coal_sync_online_frac`, sized by
   a new `online_frac` column in `thermal_tranches_PJM.csv` = hours any unit is
   synchronized / 8760): a supercritical synchronized ~all year (online_frac
   ≥0.99, e.g. Amos 0.94, Harrison 1.0, Spurlock 1.0) is held every hour, while a
   two-shifting cycler (Rockport 0.57, Keystone 0.41) is forced only in its
   top-online_frac hours by system load — mirroring the CT must-run load-shaping
   and the CEMS fingerprint (Thread A: big units stay online 99-100%, cyclers
   two-shift). The thermal-tranche artifact was fully re-derived 2023-25 in the
   process, which also corrected the pre-NaN-fix `online_hours`/`committed_pct`/
   `mustrun_online_pct` for the multi-unit coal+gas plants (the campd.py NaN-
   poisoning fix; CLAUDE.md #12).

   **Keeper result (pjm 47 sync-srmc, 2023-25).** Online%-scaling FIXES the
   moderate-gas over-hold (the keeper-vs-pjm_43 failure mode): 2023 coal C2 from
   the round-2 over-hold to in-tolerance. The accurate re-derive (lower committed
   band) deepens the **cheapest-gas 2024 coal under-run** (C2 ~-14% grid-basis),
   and that under-run is **structural, not an offer-curve lever**: the bituminous
   sigmoid floor was swept 0.68 → 0.76 → 0.90 with 2024 bit pinned at -9.4%
   (saturated). The residual is the **missing energy+reserve co-optimization
   (step 3b)** — corroborated by C3c (model 0 scarcity hours >$200 vs 6/18/59
   actual): coal is sole price-setter only ~9% of hours, so the afternoon/dear-gas
   scarcity volume and price the under-run reflects need the reserve co-opt, not
   a cheaper coal bid. C3a mean-LMP / C3b / C4 / C5a all PASS; determination
   NOT-YET pending 3b. 2025 PRB cyclers (876/879) remain the largest per-class
   miss; their dear-gas over-run is the same reserve-co-opt lever (a steeper
   subbit sigmoid trades it for a 2024 under-run via dispatch-weighting coupling,
   so it is not pursued).

Why this avoids both failure modes already on the dashboard:
- vs **keeper** (floor 0.60 sub-cost): smaller floor → less forced over-volume /
  over-export; SRMC-priced floor → higher LMP when coal is marginal.
- vs **pjm_43** (Pmin=0, full cost, collapse to -46%): the synchronization floor +
  take-or-pay keep units online, so coal does not collapse; pjm_43 failed because
  it removed *all* floor *and* let units two-shift to zero, which CEMS refutes
  (large units stay online 99-100%).
- vs **pjm_44** (dispatchable + keep sigmoid, -21/-28/-13%): replaces the fitted
  sigmoid with the measured take-or-pay share — same direction, now grounded.

**CP must-offer** can be added as a structural floor-priced-at-min-load obligation
(a forward-reproducible input from the capacity construct), reinforcing layer 2.

**Co-design with price formation (mandatory).** Coal is the sole price-setter only
~9% of zone-hours; gas is co-marginal ~50%. So the coal restructure fixes
**volume + over-export + the price coal sets when marginal**, but the afternoon
$75-200 LMP level needs the **energy+reserve co-optimization** lever
(`pjm-reserve-ordc.md` Phase 2: per-gen `R[g]≤ramp10[g]`), currently blocked on
(a) memory at PJM plant scale and (b) ramp data absent from `FleetArrays`.
Sequence: build layers 1-3 (structure), then co-opt (price), then retune levels.

**Data dependency for implementation:** the take-or-pay deriver + scenario wiring
are built (`derive_coal_takeorpay.py`, `coal_takeorpay_share`,
`coal_takeorpay_from_data`, default off; `_RENAME` extended to keep `Purchase
Type`) **and the per-ISO `coal_takeorpay_<ISO>.csv` artifacts are now derived**
(EIA-923 2023-25, all 7 ISOs). PJM has the **lowest** contracted share of any ISO
— tons-weighted **86%** (mean 73%) vs MISO 97% / CAISO 96% — with real per-plant
spread the flat sigmoid cannot capture: Gavin/Harrison/Clifty 100% contracted,
Spurlock 62%, Mt Storm 78%, Miami Fort (2832) **0% (all spot)**. This empirically
confirms Thread B: PJM bituminous carries more avoidable spot coal, consistent
with it being the swing fuel. Steps 1+2+3a are now **built and solved** (keeper
pjm 47 sync-srmc, 2023-25; recipe `scripts/probes/_pjm_sync_srmc_run.py`,
`coal_takeorpay_from_data` + `coal_mustrun_online_pmin` + `coal_sync_srmc_tranche`
all on). The measured contract share now SIZES the fuel-free vs SRMC split (not a
residual-tuned discount). **The one remaining structural step is 3b (energy+
reserve co-optimization)**, still blocked on memory at PJM plant scale — the
keeper's NOT-YET (2024 cheap-gas coal under-run, 0 scarcity hours) is its
fingerprint, confirmed by the bit-floor saturation sweep (the under-run is not an
offer-curve lever). Do NOT substitute a residual-tuned discount to close it.

---

## Thread E — CC_REGULAR characterization (parallel)

CEMS gas combined-cycle fleet, PJM 2024 (88 plants, ~455 TWh):

| metric | value | reading |
|---|---|---|
| annual CF (GWh-wtd) | 0.71 | high utilization (cheap gas) |
| %hrs > 80% of own max | 60% | model keeper 74% — only mildly over |
| **low/hi-price CF ratio** | **0.86** | weak price response — closer to baseload than coal |
| corr(CF, LMP) | +0.10 | modern H-class CCs run flat (Guernsey/Greensville/Lackawanna lo/hi 0.90-1.00, CF ~0.75) |

**Reading.** The "CC modeled too baseload" symptom is **real but small** (model 74%
vs CEMS 60% > 80%-of-max) — and partly *correct*: modern PJM CCs genuinely run
near-baseload in cheap-gas years. The dominant defect is **not** CC being slightly
too flat; it is the **merit inversion** — coal (lo/hi 0.63) is *more* price-
responsive than CC (lo/hi 0.86), i.e. coal is the swing fuel above cheap CC. The
model prices coal below gas, so it baseloads coal and treats CC as the swinger,
backwards from the data. Fixing coal pricing (Thread D, coal above cheap gas) is
the lever; a modest CC offer-curve flattening (committed_pct) is secondary.

---

## Reproduce

```bash
# Bituminous operational fingerprint (no solve; ~1 min/yr):
.venv/bin/python scripts/probes/_pjm_coal_opfingerprint.py \
    --rank bituminous --years 2023 2024 2025 --top 12
# Other ranks: --rank subbituminous | --rank waste
# CC characterization (Thread E):
.venv/bin/python scripts/probes/_pjm_coal_opfingerprint.py --cc --years 2024 --top 12
```
