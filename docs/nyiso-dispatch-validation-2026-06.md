# NYISO dispatch validation — what actually mis-dispatches (2026-06)

Diagnostic solve `results/calibration/_diag_nyiso_baseline_2023` (keeper config:
`--iso NYISO --year 2023 --commitment --gas-monthly-actuals
--priced-interchange`). Throwaway single-year probe (rule #14) — **not** a
dashboard keeper; used only to localize the dispatch error before building
structure.

## Headline: the error is locational, and it is NOT a uniform "NYC under-runs"

Model vs **EIA-923** in-zone generation, 2023 (downstate thermal is fully
zone-mapped via `bin_assignments_NYISO.csv`; upstate's hydro+nuclear ~65 TWh is
not in the thermal map, so the upstate row is not comparable and is omitted):

| zone | model TWh | real TWh | model − real |
|---|---|---|---|
| Capital_Hudson | 19.54 | 20.75 | −1.21 |
| **NYC (J)** | **39.97** | **29.07** | **+10.90** |
| **Long_Island (K)** | **3.70** | **8.52** | **−4.82** |

So the downstate fleet is **mis-allocated**, not uniformly under-run:

- **NYC over-generates by ~11 TWh.** It self-supplies almost its entire load
  (~40 of ~41 TWh) because it cannot import enough cheap power — Central-East
  (1,750 MW, saturated by upstate hydro going east) bottlenecks the AC path and
  the priced node lands only ~1 GW into zone J (HTP + Linden DC cables). Real
  NYC imports ~12 TWh through Dunwoodie-South; the model imports ~1. **NYC needs
  *more delivered import / a looser internal path*, not an energy must-run** — a
  must-run floor would push it further over.
- **Long Island under-generates by ~4.8 TWh.** LI imports ~80 % of its load
  across the NYC→LI (1,650 MW) link + the ~1.2 GW external node; reality is
  ~52 % self-supply (cable-islanded + local-reliability rules force more in-zone
  running). The model freely floods cheap NYC gas into LI because nothing
  enforces LI's local-reliability self-supply. **LI is the in-city-floor
  target.**

## Price: the four downstate zones collapse to one LBMP

Model 2023 zonal LMP: Upstate_West / external **$27.57**; Capital_Hudson,
Lower_Hudson, NYC **$38.66**; Long_Island **$38.81** — i.e. everything east of
Central-East clears at one downstate gas price. Only **Central-East binds**;
the Lower_Hudson→NYC (Dunwoodie-South) and NYC→LI interfaces don't, so J/K/I/G
never separate. Recovering the LI premium requires LI to stop importing freely
(the LI floor) so its interface binds.

## NYC peakers are idle — a reserve/scarcity gap, not energy

NYC CT_PEAKER (1,664 MW, 21 plants) runs at **~0.2 % CF** (mean 3.7 MW), CT_CHP
~2 %. They are the EIA-923 −75 % / −44 % classes. They do not clear on energy
(downstate energy ~$38.66 < peaker MC) and there is no scarcity tail to call
them — this is **mechanism B (RCPF locational reserve scarcity)**, gated on NYC
headroom, *not* an energy must-run. (Confirms the residual-attribution doc.)

## Imports under-clear (16.56 vs 23.45 TWh measured)

Node clearing: HQ_hydro 900 MW firm-ish (always on, $13 < downstate price),
IESO_Ontario 780 MW avg, PJM_west 206 MW avg (~19 %), ISONE_tie ~0 (1.5 %),
import_scarcity 0. The deep blocks priced above the ~$38 downstate body never
clear; the gap is partly the documented EIA-930/EIA-923 basis floor (serving the
full wedge breaks the gas band). HQ/Ontario already clear ~fully in 2023, so a
firm-must-flow floor is **structurally correct but a minor 2023 lever** — its
value is cheap-overnight hours and lower-price years (2024) where the economic
node would otherwise back the baseload off.

## Validated fix list (revises the original three)

1. **LI in-city self-supply floor** — force Long_Island to generate ≥ a forward
   fraction of its own hourly load (cable + local-reliability rule). Recovers
   ~5 TWh LI gen, cuts LI over-import, separates the LI premium. **Clear win.**
2. **Firm imports (HQ + Ontario)** — mark the cheap baseload import as
   price-insensitive must-flow. Structurally correct; minor in 2023, matters in
   2024/low-price hours. Keep, don't oversell.
3. **NYC peaker recovery = RCPF reserve scarcity (mechanism B)**, re-gated on the
   corrected downstate headroom — NOT an energy must-run (NYC already
   over-generates by +11 TWh; an energy floor makes it worse).

The original "NYC in-city minimum-generation must-run" is **dropped**: the data
shows NYC over-, not under-generates. Imposing it would chase the peaker symptom
with the wrong (and non-physical-for-NYC) mechanism.

## Result of fixes #1 + #2 (2023 P2, both flags on)

`--nyiso-local-selfsupply --nyiso-firm-imports` on the keeper config, P2 (scored
pass; `min_gen` now preserved through commitment):

| zone | base TWh | + floors | real | verdict |
|---|---|---|---|---|
| Long_Island | 3.70 | **9.27** | 8.52 | **dispatch error fixed** (−4.8 → +0.75) |
| NYC | 39.97 | 38.37 | 29.07 | eased toward real (still over — import/peaker) |
| Capital_Hudson | 19.54 | 16.42 | 20.75 | drifted (floor pulled gen from Capital) |

LI fleet now runs its real mix — ST_GAS 0.4→2.5, CC 2.5→4.5, **oil 0→1.36 TWh**
(the dual-fuel LI units fire, as they do in reality). Firm imports were the
predicted near-no-op in 2023 (node 16.56→15.75 TWh).

**Honest trade-offs (rule #1 — the structural mechanism stays):**

- **Price MAE 7.90 → 8.16** (slightly worse). Forcing LI self-supply makes the
  system *longer*, pushing the already-under-priced downstate level down ~$3 (all
  four downstate zones 38.66 → 35.76). The **LI premium does not appear**: a
  `min_gen` floor makes the LI units *inframarginal*, so they set no price.
  Recovering the premium needs the LI cables to **bind** (local gas marginal),
  and the deeper under-pricing points straight at the **missing scarcity tail
  (fix #3 / RCPF)** — the floor sharpens, not solves, that need.
- **LI oil 1.36 TWh overshoots** the EIA-923 NYISO oil total (0.42); the 0.45
  fraction lands LI +9% over real. Both are second-order tunes (fraction /
  dual-fuel relabel), not reasons to revert the mechanism.

## Fix #3 status (NYC peaker / scarcity tail) — IMPLEMENTED 2026-06

In-LP **locational** reserve co-optimization is now wired for NYISO
(`energy_reserve_coopt` + `iso == "NYISO"`, default OFF). The existing
single-system reserve machinery (`model/dispatch._build_reserve_rows`) was
generalized to **multiple nested balance families**: the system NYCA tier
(`NYISO_RCPF_PRODUCTS`) plus the East ⊃ SENY ⊃ NYC regional tiers
(`NYISO_RCPF_LOCATIONAL`), each a balance row over its member zones, sourced
from the FERC ER21-502 / Rate-Schedule-4 anchors (`results.scarcity.
nyiso_reserve_coopt_inputs`; the per-zone `R_z` variables feed every family that
contains the zone, so a downstate shortage stacks the regional penalties into
the downstate LMP). ERCOT/PJM stay byte-identical (single all-zone family).

**Result (run `nyiso 19 locational-reserve-coopt`, 2023/24/25, registered
PROBE):** the reserve fires only in genuine summer scarcity (Jul/Aug/Sep;
reserve price $0 in winter), recovering the scarcity tail the NYCA-aggregate
curve and the post-solve RCPF adder cannot dispatch. The 2025 summer under-bias
eases markedly (Jun −30.7 → −14.6, Jul −22.1 → −15.8 vs the LI-floor probe);
2025 `price_shape` now PASSES (NRMSE 0.16) and 2024 price PASSES outright;
dispatch r 0.81–0.87 all years; 2023 body unchanged (BASE 12.31 → COOPT 12.27,
A/B-verified). It is **not** an energy must-run (NYC over-generates already).

**Why it was not yet a keeper — the residual moved to a NEW root cause.** With
the co-opt run still on the EIA-923 **receipt** monthly gas (`--gas-monthly-actuals`),
the aggregate was gated by a **winter/January downstate over-pricing** (2023
`price_mean` +13 %, NRMSE 0.40; downstate zones ~$98 in January vs upstate ~$40,
actual NYCA RT $37.8). A BASE-vs-COOPT A/B with the co-opt OFF reproduced the
*identical* January price, so it is **not** caused by fix #3.

## Root cause of the winter downstate over-price — IT IS THE GAS LEVEL, not topology (2026-06, run `nyiso 20`)

The January downstate over-price is the **gas-level artifact** the residual-
attribution doc (mechanism D) already diagnosed and the daily-Transco overlay
(`nyiso 16/17`) already fixed — **not** an import-topology bug. The keeper-
lineage `nyiso 17` was a daily-Transco run but *without* the fix-#3 mechanisms;
the co-opt probe `nyiso 19` had the mechanisms but burned the winter-inflated
receipt gas. Neither had run the obvious combination. **`nyiso 20
daily-coopt-floors` is that combination** —
`--commitment --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily
--priced-interchange --energy-reserve-coopt --nyiso-local-selfsupply
--nyiso-firm-imports`, 2023+24+25 — and it is the **new keeper**.

The measured daily Transco Z6 NY spot de-smears the January within-month cold
spike (the EIA-923 receipt's $10.02/MMBtu January is Winter-Storm-Elliott gas
billed into the receipt average). Effect, 2023:

| metric | receipt+coopt (`nyiso 19`) | daily+coopt (`nyiso 20`) |
|---|---|---|
| Jan downstate LMP | ~$98 | **$49** (upstate $34; actual NYCA $38) |
| Jan load-wtd residual | +44 | **+5.8** |
| NYC in-zone gen (real 29.07) | 38.4 | **33.6 TWh** |

`nyiso 20` **beats the keeper `nyiso 17` on price every year** (verdict
`price_mean`: 2023 +19.9 % vs +24.0 %, 2024 +2.1 % vs +7.2 % PASS, 2025 +1.2 %
vs +5.4 % PASS; `price_shape` 2023 0.212 vs 0.251). 2023 `co2` now PASSES and
the keeper's ST_GAS +5.05 TWh fuelmix overshoot is gone; volume bands held
within ~1 pp of the documented EIA-930/923 import basis floor. Registered +
promoted (`keepers.json`).

**Why import topology is NOT the lever for the remaining residual.** The import
node attaches to Upstate (3,000), NYC (1,000 = HTP 660 + Linden 315) and LI
(1,200 MW); Central-East carries the measured monthly TTC (1,750 MW mean 2023,
posted DAM `CENT EAST` TTC — keep per rule #11). With the gas fixed, the
remaining 2023 over-price is a roughly-**uniform +$5–7/MWh downstate body**
(Mar +12, Apr/May +7, Jul +6) — the import/**congestion** residual: the deep
import tranches do not clear because **PJM $34 > the downstate body $29–38**, and
serving the wedge anyway pushes in-state gas out of the EIA-923 band (the
documented EIA-930/923 floor, §2.A of the residual-attribution doc). So the
downstate clears on local gas; this cannot be closed without a fitted adder.
The other half is the **flat-annual Iroquois-Transco summer over-level** (fix
#1(b)) — the hub overlay reconstructs a single Iroquois-Z2 monthly level (HH +
basis) that every zone inherits via fixed annual offsets, so a real *monthly*
Iroquois would lower the summer body; a multiplicative/winter-concentrated
reconstruction is **mean-preserving on annual gas** and only trades summer for
winter (price is convex in gas → it would not lower the mean), so it is not a
clean substitute for the paywalled series. **Dec-2024 −27** and the short **2025
summer tail** (model 29 vs 118 h >$200) are the co-opt **winter/10-min
eligibility** follow-on (handoff #2), not gas or topology.

## Per-family reserve eligibility (10-min → quick-start) — `nyiso 21`, the eligibility lever is MINOR

Fix #1 of the handoff: each NYISO reserve *family* now carries its own
eligibility mask (commit `7be0a70`, on main). The 10-minute NYC/SENY families
draw only on the **quick-start** fleet (`QUICK_START_FUEL_TYPES` = gas-CT/oil,
plus fast storage) — class 1 — instead of the full all-thermal
`RESERVE_FUEL_TYPES` mask; 30-minute/total products keep the full dispatchable
class 0. Slow combined-cycle headroom can no longer satisfy a 10-minute
requirement (a unit-physics capability constraint, not a fitted requirement).
The keeper config re-solved on this code is **`nyiso 21 family-elig-coopt`**
(`results/calibration/nyiso_21_family_elig`, id `2026-06-23-nyiso-21-family-elig`,
all three years), identical flags to `nyiso 20`:
`--commitment --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily
--priced-interchange --energy-reserve-coopt --nyiso-local-selfsupply
--nyiso-firm-imports`. The solve logs `7 locational reserve families (3
10-min/quick-start), 721 full-fleet / 333 quick-start reserve-eligible units` —
the eligibility split is live.

**Result: the eligibility fix barely moves the backcast.** The verdict is
within noise of `nyiso 20` on every scored criterion (`price_mean` 2023 +20.0 %
vs +19.9 %, 2024 +2.1 %, 2025 +1.3 % vs +1.2 %; `price_shape` 2023 0.212 / 2024
0.250 / 2025 0.126; `sysvol`, `co2`, `fuelmix` identical). The load-weighted
NYCA scarcity tail thickens only marginally (2025 ~29 → ~32 h >$200 against
actual ~119; max ~$427 → ~$451) and the body holds — the **right direction per
rule #1, but a small lever**. So the eligibility mask was a real structural
gap worth closing, **but it is not the dominant cause of the short tail**.

**`nyiso 21` is the keeper** anyway (rule #1: same config re-solved on the
now-merged eligibility code is strictly *more structurally faithful* than
`nyiso 20`'s pre-fix bundle, and the fit is held — promotion is on faithfulness,
not on a fit improvement). Registered + promoted (`keepers.json`); `nyiso 6`
pruned for the 15-run NYISO retention.

**Where the tail actually lives (re-confirmed, the real next levers):**
* **Dec-2024 is an ENERGY/gas cold-event, not a reserve shortage.** It is
  *unchanged* by the eligibility fix (model $39 vs actual RT $68.3, monthly
  load-weighted). The lever is the December delivered-gas level (the daily
  Transco/Iroquois cold-day spike), not 10-minute reserve eligibility.
* **2025 summer/winter tail** is still short across the board (Feb $76 vs $94,
  Jun $54 vs $66, Dec $85 vs $96) — a body-wide under-level, not just a
  missing-shortfall-hours problem, so reserve eligibility alone cannot close it.
* **The dashboard cannot score `price_tail` for NYISO** — the committed run
  payload omits `ordc.hoursGt200`, so `score_price_tail` SKIPs (both `nyiso 20`
  and `nyiso 21`). The tail must be read off the dispatch parquet / system
  parquet by hand until the NYISO benchmark emits the `>$200` hours block.

## Gas offer curves grounded in the NYISO SOM — `nyiso 22`, and the merit-order fix is gas-TOTAL-blocked in 2024/25

Until now NYISO fell through the generic non-PJM/non-ERCOT branch of
`offer_curve_by_group{}` (`scripts/run_calibration.py`), carrying ERCOT-fitted
band multipliers that were **never validated for NYISO** — the root cause of the
gas-class merit-order substitution error in the `nyiso 21` fuelmix (CC_REGULAR
under-runs, legacy gas steam over-runs). Added a dedicated, SOM-grounded
`_NYISO_OFFER_CURVE` (merged on top of that branch, gas classes only):

* **The merit order was physically backwards.** Cap-weighted class heat rates
  (`bin_assignments_NYISO.csv`): CC_CHP 6.99, CC_REGULAR 7.76, ST_GAS 10.61,
  CT_PEAKER 11.95 MMBtu/MWh. The generic ST_GAS committed band (0.81×) put the
  legacy-steam min-load slice at 0.81·10.61 = **8.6 eff HR — *below* the top of
  CC_REGULAR's econ ramp** (1.27·7.76 = 9.9), so an inefficient steam boiler
  undercut an efficient CC. Fixes: ST_GAS committed 0.81→**0.97** (steam sits
  back above CC across its whole range), CC_REGULAR econ 1.06/1.27→**0.95/1.12**
  (CC marginal HR is ~flat and ~0.95× average — the efficient workhorse runs
  more), CC_CHP 0.96/1.12→0.98/1.15, CT_PEAKER committed 1.55→1.35.
* **Grounding (real, forward-reproducible — rule #12, not residual-fitted):**
  2023 & 2024 Potomac Economics SOM. §VI.A: NYISO is a competitive energy market,
  output gap 0.05 % at the mitigation threshold (offers ≈ short-run MC → the
  multipliers encode a near-MC *shape*, not a strategic markup). Figure 2 / §I.B
  (verbatim, both years): *"Steam turbine units appear to be the most
  economically challenged… their high operating costs and physical constraints…
  usually prevent steam units from earning much energy or reserve revenue, except
  in Long Island"* → steam must sit above CC and run only in high-load hours / on
  the LI floor. Figure 47: after the 2022 downstate-peaker retirements *"older
  more outage-prone steam turbines have been scheduled to operate more frequently
  in high load hours."* §VI.A also grounds the inflexible CC duct-firing peak
  wall (*"some combined cycles offer inflexibly… to manage… the duct-fired
  portion"*; duct burners not AGC/10-min capable).

**Result (`nyiso 22 gas-offer-som`, all 3 years, keeper flags).** The grounded
curve does exactly what offers *can* do, and the fit cleanly separates what they
*cannot*:

| class (grid-delivered TWh) | 2023 m→a | 2024 m→a | 2025 m→a | vs `nyiso 21` |
|---|---|---|---|---|
| CC_REGULAR | 31.81 / 33.01 | 33.23 / 37.35 | 32.80 / 34.78 | **+2.34 / +2.32 / +2.54** (the #1 miss, better every year) |
| ST_GAS | 11.40 / 8.14 | 9.11 / 10.87 | 11.24 / 15.62 | −2.19 / −2.26 / −2.24 |
| CC_CHP | 13.06 / 12.12 | 13.84 / 13.91 (PASS) | 15.17 / 13.41 | small |
| CT_PEAKER | 1.23 / 2.11 | 0.49 / 2.10 | 0.89 / 2.77 | ~flat (reserve/tail, not offers) |

Price/structure **held or improved**: `price_mean` 2023 +18.3 % (was +20.0 %),
2024 +1.4 % PASS, 2025 +0.6 % PASS; `price_shape` 2023 0.199 PASS / 2025 0.126
PASS; `dispatch_corr` r = 0.88 / 0.81 / 0.80; `co2` 2023 +4.3 % PASS; `sysvol`
gas total essentially unchanged (the curve rebalances *within* gas).

**Why full C1 is not reachable here — the binding constraint is the gas TOTAL,
not the offer curve.** `sysvol` gas: 2023 **+3.0 %** (on), but 2024 **−11.5 %**
(−7.8 TWh) and 2025 **−9.2 %** (−6.5 TWh). In 2024/25 the *entire* gas total is
short, so the CC_REGULAR / CT_PEAKER / ST_GAS under-runs sum to the deficit
(2024: −4.12 −1.61 −1.76 = −7.5 ≈ −7.8) — there is no surplus gas energy for any
offer-curve rebalance to allocate, by energy-balance. This is the documented
EIA-930-demand/EIA-923-net-generation **import-basis floor**
(`docs/calibration-best-so-far-nyiso.md`), explicitly **out of scope** for this
task (handoff: *"the 2025 body-wide under-level… is an ENERGY/gas… problem, not
reserve or offer curves"*). 2023, where the gas total is on, is the only year a
clean rebalance is possible — and there the ST_GAS over-run halves (+5.46→+3.26)
while CC_REGULAR recovers +2.34.

Two of the four gas classes are therefore **not offer-curve-addressable**:
* **CT_PEAKER** under-runs every year (−0.9/−1.6/−1.9) — the NYC-peaker **reserve
  scarcity / tail** gap (mechanism B; lowering the committed band 1.55→1.35 moved
  it +0.0/+0.1, because peakers are priced far above the downstate clearing
  price, not because their offer is wrong). Out of scope (the tail follow-on).
* **ST_GAS** is over in 2023 (+3.26, real, addressable) but under in 2024/25 (the
  gas-total deficit). A single curve cannot be both too cheap and too dear; the
  structurally-correct level (steam above CC, near-MC) is kept per rule #1, so the
  2024 band-loss vs `nyiso 21` is the **removal of the non-physical cheap-steam
  inversion** (`nyiso 21`'s 2024 ST_GAS PASS came *from* steam bidding below an
  efficient CC), not a regression to chase back with a fitted adder.

**Status:** `nyiso 22` is registered (rule #13). It is **more structurally
faithful** than `nyiso 21` (correct CC-above-steam merit order, the dominant
CC_REGULAR miss improved every year, every multiplier traceable to a SOM
citation) and holds price/co2/sysvol — but it does **not** meet the handoff's
literal keeper bar ("all gas classes INTO the C1 band across all 3 years")
because 2024/25 are gas-TOTAL-blocked (out of scope). The SOM-grounded curve is
the real deliverable; the residual C1 failures are not offer-curve-addressable.
