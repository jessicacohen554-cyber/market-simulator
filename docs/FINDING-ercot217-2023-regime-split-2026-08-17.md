# FINDING — ercot-217 (THE 2023 REGIME LANE, Phase-0 read-only): the regime split the owner hypothesizes is **ALREADY BUILT, ARMED AND CORRECTLY DATED on the keeper** — every published 2023-vs-2024/25 market-design difference is CARRIED, most as measured per-year inputs, the rest as date-gated mechanisms keyed to the published instruments; the residual does NOT step at the design dates (it tracks scarcity episodes, whose pricing is the adjudicated conduct object); **no admissible regime lever exists and NOTHING IS BUILT** — the D-3 negative branch, reported at full magnitude. Phase-1 NOT entered, keeper UNCHANGED

**Session ercot-217, 2026-08-17, branch `claude/ercot-2023-regime-split-s4vgib`.**
Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json` at session
start AND end: **`2026-08-17-ercot215-arm-decontam`** — UNCHANGED; determination
NOT-YET, fail set {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c the ledgered
CAVEAT ×3 (68/181, 22/53, 1/31). **Phase-0 READ-ONLY as dispatched: no LP, no
solve, no year scored, no run registered, no bundle modified, no
`ScenarioConfig` field, no matrix cell verdict minted** (the
ercot-163/170/208/214/216 no-LP precedent). No precommit was pushed because no
solve was reached — the pre-solve gate is what this session did not pass.
Committed probe: `scripts/probes/ercot217_regime_phase0.py` →
`results/calibration/ercot217_regime_phase0.json`. Everything below is read
from the five committed lineage bundles' `hourly/` sidecars, the committed
actual-RT parquet, the committed measured AS inputs, and the re-fetched IMM
State-of-the-Market volumes (per `data/raw/ERCOT/README.md`; 2023/2024/2025
PDFs sha256-verified against the committed `SHA256SUMS.txt`). RETENTION HOLD
honoured: `2026-08-16-ercot213-ctl-headbase` and
`2026-08-15-ercot204-rule26-delete` NOT pruned (this lane's −33.2 % control).

## 0. THE OWNER DECISION THIS LANE EXECUTES (recorded verbatim, per the dispatch)

> "2023 was a weird year in ERCOT with a different market structure that caused
> super high scarcity pricing .. it should accordingly not have precisely the
> same parameters as 2024 and 2025[;] this is a known and real phenomenon. If
> it means the keeper for ERCOT backcast calibration is really the combination
> of two different configurations, one 2023 and before and one 2024 and after,
> that's an acceptable approach and finding."

With (D-1) Q-B FINAL suspended **for this lane only** (C3a/C3b-2023 spend
authorized strictly for regime-keyed structural work; the CC-headroom
crosswalk, item 11, stays CLOSED; R-A unchanged), (D-2) a regime-split keeper
an acceptable outcome — **one bundle whose config resolves the regime
internally per weather year** — and (D-3) a negative result equally acceptable
and reported at full magnitude.

## 1. VERDICT

1. **The owner's premise is TRUE and is the IMM's own headline finding**, now
   verified from the primary source (§2 row 2): ECRS-driven "artificial
   shortage pricing … doubled average energy prices between June and December
   2023" at a cost of "more than $12 billion" (2023 SOM). 2023's market
   structure genuinely differed from 2024/25's.
2. **The model already carries that structure, armed, correctly dated** —
   `ercot_ecrs_conservative_deployment=True` and
   `ercot_nonreleasable_as_withholding=True` on **every** bundle of the
   −33.2 → +0.4 → −40.1 lineage (probe `p0a_armed_regime_flags`), on top of the
   measured per-year ASPLANNP433 plan whose first ECRS row is the go-live day
   itself (2023-06-10). The keeper **is already** D-2's "one bundle whose
   config resolves the regime internally per weather year": ECRS held rigidly
   at VOLL all-2023 and through 2024-07-31, released on the ramp after the
   2024-08-01 reform; RRS/RegUp rigid until RTC+B (2025-12-05); ORDC
   parameters design-constant ($5,000 / 3,000 MW, the post-Uri vintage) with
   the one within-span change (the Nov-2023 OBDRR048 floor) date-gated in
   code. The −40.1 % is measured **with** the regime split in force.
3. **The residual does not step at a published design date** (§4). Pre-go-live
   2023 bias **+1.2 %**; the miss mass turns on with the first post-go-live
   heat event (Jun 10–23 −57.5 %), relaxes to **+15.4 %** in the cool
   fortnight that follows (Jun 24–Jul 7), peaks in August (−56 %), and is
   **gone by October** (Oct/Nov/Dec −2/−5/+3 %) while ECRS procurement and the
   sequestration design continue unchanged. The same calendar splits in
   2024/2025 are flat. And the tail-catch failure exists in *both* 2023
   regimes: the model missed 14 of the 15 pre-ECRS actual tail hours too.
   This is a scarcity-*episode* object inside the regime, not a regime-level
   object — exactly the adjudicated conduct tail (ercot-209 card R §2).
4. **No admissible regime lever exists** (§5). Every published design
   difference either (a) is already carried as a measured per-year input or a
   date-gated mechanism (§2, all rows), or (b) acts on prices through the
   scarcity-hour **energy offer at the clearing point** — the channel that is
   adjudicated model-class (storage conduct: Door A CLOSED at ercot-211,
   measured NOT-TRANSFERABLE and model-free non-identifiable even
   *within*-regime), forbidden as a measured input (rule 13: an equilibrium
   outcome), and closed on its depth leg (item 11, Q-B — which this lane's
   D-1 explicitly keeps closed). The admissible year-keyed measured
   re-identifications the ercot-168/192 precedent licenses were **already
   executed** (per-year 2023 coal curves; the year-keyed 2023 coal `_peak`
   level; ercot-169's 2023 invariance test of the margin constants —
   CONFIRMED invariant where identifiable). There is no parameter left whose
   2023 measured identification differs from its 2024/25 one.
5. **Phase-1 NOT entered; nothing is built** — the D-3 branch. The regime
   ledger (§2) is the deliverable, and its answer to the owner is: the
   two-configuration keeper you would accept **already exists inside the one
   bundle**, keyed to the published dates; what remains of the 2023 gap is not
   a configuration difference but the adjudicated conduct object.

## 2. (P0-A) THE REGIME LEDGER — published 2023-vs-2024/25 design differences × model status

Primary sources verified this session: the re-fetched IMM SOM volumes
(sha256-verified against `data/raw/ERCOT/SHA256SUMS.txt`); the measured inputs
on disk; the cited protocol/notice IDs as carried in the code's citation
blocks (`model/reserves/spec.py:97–127`, `:1440–1461`) and
`docs/parameter-citations.md`. Quantities below re-measured from the raw
parquets by the committed probe, not quoted from any prompt or comment.

| # | Design fact | Instrument + effective date | Primary source | Quantity it changes | Model status |
|---|---|---|---|---|---|
| 1 | **ECRS go-live** — new 10-minute contingency reserve product | ERCOT market notice M-D050523-01; Operating Day **2023-06-10** | IMM 2023 SOM ("introduction of ECRS in June 2023"; impact figure titled "June 10 – December 2023"); measured ASPLANNP433 first ECRS row **2023-06-10** | +~1.9 GW mean new reserve demand (2023 Jun–Sep monthly means 2,041–2,127 MW) | **CARRIED** — measured per-year plan (`ercot_as_plan_requirement_mw`, hourly, per-product; the onset is data-carried); forward path gated by `ERCOT_ECRS_LAUNCH_HOUR = 3840` |
| 2 | **ECRS sequestration, no price-based release** (go-live → 2024-07-31): awarded ECRS carved out of SCED's dispatchable range (HASL), released only by manual/automatic reliability deployment | Nodal HASL carve-out §6.5.7.6.2.3/§3.17; ERCOT Ancillary Services Study white paper (Sept 2024) | IMM 2023 SOM §II.G + rec 2023-3: "artificial shortage pricing as high as $5,000 per MWh when the system was not actually short of reserves … **Doubled average real-time energy prices from June through December 2023** … **more than $12 billion** through the end of November"; IMM 2024 SOM recap: "these reserves are withheld from the real-time energy market dispatch until manually deployed" | Removes the awarded ECRS MW from the RT energy supply stack at all prices | **CARRIED + ARMED** — `ercot_ecrs_conservative_deployment`: `ECRS_withheld` rigid family at `ordc_voll`, whole-2023 and 2024 h<5088 (`spec.py:1464–1471`); armed on **all five** lineage bundles |
| 3 | **ECRS release reform, 2024-08-01**: formal deployment criteria (500 MW increments on a ≥40 MW power-balance violation sustained 10 min), released capacity dispatched at resources' own offers — **no** administrative floor | NPRR1224 process implemented via operating procedures; the PUCT **rejected** NPRR1224's $750/MWh floor at its 2024-07-25 open meeting | IMM 2024 SOM rec 2023-3: "ERCOT still implemented the deployment process proposed by NPRR 1224, but without the $750 per MWh energy offer floor" | Ends the unconditional sequestration; releases become condition-triggered | **CARRIED** — `ERCOT_ECRS_RELEASE_REFORM_YEAR/HOUR = 2024 / 5088` (2024-08-01); ECRS reverts to the standing VOLL-anchored ramp from that hour |
| 4 | **Non-releasable RRS + Reg-Up** (all pre-RTC+B years): HASL carve-out with no price-based SCED release (RRS deploys on under-frequency/EEA; Reg-Up through LFC) | Nodal §6.5.7.6.2.3/§3.17; retired by RTC+B | IMM 2025 SOM (RTC: "Resources can now sell ancillary services directly into the real-time market") | RRS+RegUp MW (~3.1–3.4 GW) sequestered in both regimes | **CARRIED + ARMED** — `ercot_nonreleasable_as_withholding`, rigid while `ercot_market_regime == "ordc"`, ending at hour 8112 of 2025 |
| 5 | **AS procured quantities by product/month**, incl. the Jun-2023 NSPIN reduction (after the Mar-2023 VMP change), RRS *not* reduced at ECRS launch ("no offsetting reduction in RRS"), and the 2025 ECRS reduction | ERCOT AS Methodology years 2023/2024/2025 | IMM 2023 SOM (NSPIN competitiveness + "no offsetting reduction in RRS procurements"); measured ASPLANNP433: NSPIN May→Aug 2023 5,052→2,206 MW; RRS 2023/24/25 means 2,903/2,722/2,737; ECRS 2025 mean 1,424 vs 2024's 1,747 | Per-product hourly reserve demand | **CARRIED** — measured per-year hourly plan; probe `p0a_asplan_monthly_mw` re-measures every cell |
| 6 | **ORDC parameters in force**: post-Uri vintage **constant across 2023–2025** — HCAP/VOLL $5,000 (eff. 2022-01-01, 16 TAC 25.509 / PUCT 52631), MCL 3,000 MW (OBDRR038 / PUCT 52373); ONE within-span change: the **Nov-2023 multi-step ORDC price floor** (OBDRR048, the PCM "bridge solution") | PUCT orders as cited; OBDRR048 | IMM 2023 SOM ORDC history ("the PUCT further adjusted the ORDC on January 1, 2022 … In November 2023, ERCOT implemented a multi-step ORDC price floor"); ORDC market value 2023 = **$550 M** (vs the $12 B ECRS effect — the ORDC was NOT the 2023 price story) | ORDC curve level/shape | **CARRIED** — `ordc_voll 5000` / `ordc_mcl_mw 3000` constant (design-faithful: the design didn't change); floor date-gated `floor_active_mask` at 2023-11-01 (post-solve path; in-LP curve deliberately ungated, documented). NP6-576-ER seasonal LOLP table on disk but unarmed (ercot-206 B0 — not re-opened) |
| 7 | **RRS/FFR composition & battery AS share**: ESR takeover of AS; ECRS MCPC collapse $76.77 (2023) → $9.62 (2024); AS cost/load $3.74 → $0.98/MWh | — (market outcome of the design + fleet, not an instrument) | IMM 2024 SOM; IMM 2025 SOM ("ESRs … dominate the provision of ancillary services") | Which resources hold the AS (and therefore what the residual energy stack is) | **CARRIED (quantities)** — measured storage AS awards (aggregate 2022-25 + per-product 2023-25: battery ECRS award means 120/573/523 MW), LR RRS-UFR credit series, net-credits cap treatment (ercot-212/213/215 legs). The MCPC *prices* are outcomes, not inputs (rule 13) — the model co-optimizes its own reserve prices |
| 8 | **RDPA / conservative operations** (RUC posture): reliability adder +$0.84/MWh in 2023 | NPRR1092 lineage (RUC offer floor) | IMM 2023 SOM §II ("continuing conservative operations"; Figure 10) | Out-of-market commitment reflected in prices | **CARRIED** — measured RTORDPA overlay (keeper 2023 demand-weighted $0.75; the small gap is basis) |
| 9 | **RTC+B go-live 2025-12-05**: ORDC + RDPA retired; per-product ASDCs; RT AS sales; shortage pricing moves into energy | RTC+B | IMM 2025 SOM ("before RTC went live on December 5, 2025"; ORDC active 57 h in 2025, $0.02/MWh) | The whole RT scarcity-pricing design | **CARRIED as a boundary** — `ercot_market_regime` (ordc/rtcb), RTOLCAP NaN→uncapped past hour 8112, RTORDPA overlay zeroed, withholding retired; the ASDC design itself is a **further regime** (forecast-lane question). Measured weight in-span: Dec 5–31 2025 bias **+1.8 %**, 4 actual tail hours, 0 model |

**What the measured AS plan/awards do and do not reach** (the dispatch's
explicit question): they reach (i) the rigid/ramp withholding families (rows
2/4 — the *physical* sequestration), (ii) the ORDC total family's requirement
and credits, (iii) the storage SOC/power reservation, and (iv) the
supply-cap net-credits. They do **not** reach — and cannot reach — the *offer
price of the residual energy stack* at the sequestration-tightened hours.
That is where reality's 2023 dollars formed (row 2's $12 B is the IMM's
measurement of sequestration acting on **reality's** offer stack), and it is
the adjudicated conduct object, not a quantity.

**No ABSENT row exists with an admissible price-bearing parameter.** The one
partially-carried nuance (row 6's in-LP-vs-post-solve floor gating) is
documented, deliberate, and pre-dates this lane; the Nov/Dec-2023 residual it
could touch is −5/+3 %.

## 3. (P0-B) THE −33.2 → −40.1 DECOMPOSITION (committed sidecars; probe basis, hub actual; official values quoted from the promotion record)

Demand-weighted 2023 annual means, $/MWh (`p0b_component_decomposition`):

| bundle | price | = λ (energy dual) | + RTORDPA ovl | + written adder | c3a probe | c3a official | model tail h | adder h>$100 |
|---|---|---|---|---|---|---|---|---|
| ercot-204 (run192 lineage) | 36.57 | 35.55 | 0.75 | 0.27 | −24.4 % | **−33.2 %** | 57 | 2 |
| ercot-213-ctl (204 @ HEAD) | 36.57 | 35.55 | 0.75 | 0.27 | −24.4 % | −33.2 % | 57 | 2 |
| ercot-213-arm (net-credits + anchor) | 48.55 | 30.25 | 0.75 | 17.55 | +0.4 % | **+0.4 %** | 123 | 117 |
| ercot-215-ctl (213-arm repro) | 48.55 | 30.25 | 0.75 | 17.55 | +0.4 % | +0.4 % | 123 | 117 |
| ercot-215-arm (**keeper**) | 33.66 | 30.25 | 0.75 | 2.67 | −30.4 % | **−40.1 %** | 67 | 37 |

The plain statement the dispatch asks for:

* **The ercot-213 pair did two separable things.** Its LP half (net-credits)
  **lowered the 2023 energy dual by $5.30/MWh** — netting the credited MW off
  the measured caps un-saturated the reserve-supply constraint, freed reserve
  capability to serve load, and removed the 4 phantom VOLL-plus shed hours
  the ercot-204 recipe carried (G-SHED 4→0; those four hours alone are ≈$6 of
  annual demand-weighted mean). Its written-price half (the published
  anchor) **raised the written adder by $17.28/MWh** (0.27 → 17.55; 2 → 117
  deep hours) — of which ercot-214 measured 116/117 deep hours to be the
  AS-product shortfall-ramp contamination.
* **The ercot-215 decontamination removed $14.88/MWh of that adder**
  (17.55 → 2.67; 117 → 37 deep hours), touching λ not at all (post-solve
  delta, G-EXACT).
* **Net vs ercot-204: −$2.91/MWh** (36.57 → 33.66) = λ −5.30 + adder +2.40.
  So today's −40.1 % is *worse* than the −33.2 % control not because the
  decontamination "gave back" the 213 gains — it removed a channel the design
  cannot emit — but because the **validated measured-basis repair
  (net-credits) removed λ the gross-cap saturation had been manufacturing**
  (including the phantom shed), while the decontaminated adder legitimately
  restores only the published order of magnitude. Both moves are the
  structurally-correct direction (rule 1); the exposed gap is the true size
  of the 2023 model-class object.

## 4. (P0-C) THE STEP TEST — the residual does not step at a published design date

Keeper, demand-weighted model vs hub actual (`p0c_design_date_step_test`):

| split | 2023 | 2024 (placebo) | 2025 (placebo) |
|---|---|---|---|
| pre-ECRS-go-live (h<3840) | **+1.2 %** (15 tail h, 1 caught) | +10.8 % | +0.2 % |
| post-ECRS-go-live | **−38.9 %** (166 tail h) | +5.7 % | +0.7 % |
| straddle: May 27–Jun 9 | +0.4 % | +2.4 % | −7.6 % |
| straddle: Jun 10–23 | **−57.5 %** | +17.4 % | +4.5 % |
| straddle: Jun 24–Jul 7 | **+15.4 %** | +30.2 % | +6.0 % |
| pre/post reform (2024-08-01) | −14.3 / −40.2 % | +12.7 / **+1.7 %** | +1.2 / −0.3 % |
| pre/post RTC+B (2025-12-05) | — | — | +0.4 / **+1.8 %** (4 tail h, 0 model) |
| monthly, 2023 | Jun −42, Jul −17, **Aug −56, Sep −39**, **Oct −2, Nov −5, Dec +3** | | |

Read against the P0-C criterion — *"a regime hypothesis is only worth
building if the residual STEPS at a published design date"*:

1. **All of 2023's material miss mass lies after the go-live date** — and
   none of it survives past September, while the sequestration design runs
   unchanged through 2024-07-31. A design-regime driver does not switch off
   in October; Texas summers do.
2. **At the date itself there is no step**: the fortnight before is +0.4 %,
   the first miss arrives with the first heat event (first post-go-live tail
   day is Jun 14), and the fortnight after the heat breaks is **+15.4 %** —
   the model *over*-prices the post-go-live regime whenever conditions are
   calm.
3. **The episode signature is regime-invariant**: the model missed 14/15
   pre-ECRS 2023 tail hours, 36/53-tail hours of 2024 and 30/31 of 2025 on
   the same conventions (ercot-216 §3) — the same C3c-shaped failure in
   every design regime, catastrophic in 2023 only because 2023's episodes
   were deep and frequent (the IMM's finding: the design amplified the
   *episodes*, through offers).
4. The reform and RTC+B boundaries show nothing to key on either: 2024
   post-reform is +1.7 % (no failing criterion), and the 27 in-span RTC+B
   days are +1.8 % with 4 tail hours.

This is the measured shape of the ercot-200/card-W fine partition ("ECRS
launch" {2023} vs "ECRS normalised" {2024, 2025}, within-regime spread
$7.70/$3.02 vs tolerances 15/20.74 — the two post-launch years cohere, 2023
does not cohere with them) — reproduced here on the backcast price object,
and attributed: the incoherence lives in the scarcity episodes' price
formation, not at the design dates.

## 5. (P0-D) NAME THE LEVER, OR REFUSE — REFUSED, on measurement

The dispatch's admissibility tests, applied to every candidate the ledger
yields:

* **The sequestration itself (rows 1–5): already carried and armed**, with
  per-regime identification already satisfied — the quantities are each
  regime's own measured data (ASPLANNP433, awards, credits, caps) and the
  dates are the published instruments. There is no G-REGIME row to add: a
  regime split that re-states the existing structure differs in nothing.
  And the standing ERCOT-102 measurement (2026-07-24) forecloses "sequester
  harder": at the missed tail hours the rigid withheld families are **slack**
  (reserve dual binds 2/88 missed hours, mean $0.1) because the model holds
  the full measured plan *and still* carries more responsive headroom than
  the real grid retained — while at the hours the model does price, the
  co-opt binds 52/59. Withholding more cannot lift a slack dual; forcing the
  bind was tested and rejected at +700–800 % C3a (ercot41/43).
* **The residual stack's depth** (the ~2.7 GW CC-headroom/capability object —
  the model's 8–9 GW responsive wedge vs the real ~5.7 GW PRC): **item 11,
  CLOSED** — twice licence-failed (ercot-170/191, L1 0.3857 vs 0.90), Q-B
  automatic and final, and this lane's D-1 keeps it closed explicitly.
* **The scarcity-hour offer level** — the channel that actually carried
  reality's 2023 dollars (0.91 of the 1.10 GW offered ≥$500 at the top-100
  gap hours is storage, at published RTORPA p50 $1–5 with PRC ~5.8 GW;
  ercot-209/166). Every route is shut, and shut by *measurement*, not only
  by governance: Door A CLOSED (ercot-211: storage conduct NOT-TRANSFERABLE;
  T5 model-free — no function of quantity drivers whatsoever fits 95.1 % of
  driver-indistinguishable hour pairs, max irreducible error $2,487.50/MWh);
  the verbatim measured surface is the standing `R` cell
  (`ercot_storage_rt_offer_surface`, rule 13 — an equilibrium outcome); and
  decisively for THIS lane, **ercot-210's within-regime control refutes the
  regime label as the driver**: fit-2024→predict-2025, both post-ECRS, same
  SWCAP, one design regime — and storage conduct still does not transfer one
  year forward. A "2023-regime conduct parameter" therefore has no measured
  identification on **either** side of the boundary (G-REGIME unfulfillable
  in principle), and 2023's own tightest hours are not even its priced hours
  (Aug/Sep mean tightness percentile 0.470/0.372 — ercot-210).
* **An administrative regime adder** (price the 2023 sequestration into RT as
  a penalty/adder): the 2023–25 design cannot emit it — "True shortages in
  ERCOT are priced under the ORDC" (IMM 2023 SOM), published RTORPA at the
  missed hours p50 $0.84 with PRC 5.7 GW, and the model's own faithful
  RTORPA mirror already writes those (small) dollars. This is precisely the
  phantom channel ercot-214 identified and ercot-215 removed by owner
  promotion **this same week**; re-arming it under a regime label would
  rebuild the decontaminated leak (rules 1/19; the ercot-215 adjudication is
  not re-litigated).
* **The IMM's own quantification as identification** (×2 Jun–Dec, $12 B, or
  the 75 %-release counterfactual): outcome-scaling — the forbidden form of
  rule 13 (and the already-refused FFR-6A row-4 / card-W W-3 shape). The IMM
  numbers enter this record as *evidence about the mechanism*, never as an
  input.
* **The year-keyed measured re-identifications that ARE admissible** (the
  ercot-168/192 pattern the dispatch cites as precedent) **are already
  executed and armed**: per-year 2023 coal per-plant curves (ercot-168,
  keeper), the year-keyed 2023 coal `_peak` level 71.3378 (ercot-192,
  keeper), and ercot-169's test of the remaining margin constants on the
  delivery-2023 corpus — CONFIRMED fuel-invariant where identifiable (limb
  B), NOT-IDENTIFIABLE otherwise (limb A, twice). The 2023 corpus has been
  asked every admissible identification question the record knows how to
  ask; no constant is left that reads differently on 2023's own data.

**Therefore: no lever is named, none is built, and the lane reports the D-3
negative branch — with a constructive half the owner should have in hand:**
D-2's acceptable outcome is not buildable *because it is already the shipped
state*. The keeper is one bundle over `--year 2023 2024 2025` whose config
resolves the 2023-vs-2024/25 regime internally — through measured per-year
inputs and published date gates (rows 1–9), exactly the form D-2 asks for,
and it has been in that form on every keeper of this lineage. What the regime
structure cannot supply — and what no admissible parameter of this model
class can — is the conduct-priced level of 2023's scarcity episodes, which
stands adjudicated as the model-class object behind {C3a-2023, C3b-2023} and
the C3c ledger (card R §2, ercot-209/211, ercot-215 §3). NOT-YET remains the
honest public claim (R-A, untouched by this lane).

## 6. GOVERNANCE

Owner decision D-1/D-2/D-3 recorded verbatim (§0) in finding and log. The
Q-B suspension (D-1) was **used only for reading and reporting 2023 numbers
at full magnitude** — no solve, no probe fitted to them, no arm proposed on
them; item 11 untouched and cited only as a closure. DO-NOT-REDO honoured in
full: Door A (ercot-211) cited, not re-tested; item 11 closed; 
`energy_online_capability_cap` (R) and `ercot_storage_rt_offer_surface` (R)
not re-opened; the mid-band spill lane stays CLOSED (ercot-215) and the
published two-basis form stays un-built; LOLP-table arming not re-opened
(ercot-206 B0 — row 6 notes the table's on-disk presence without arming);
V0/ercot-201 honoured (no tightness-conditioned identification anywhere in
the probe — calendar windows and published dates only); 28a honoured (no
netting re-run; nothing was run). Rule 22: {2023, 2024, 2025} only, no
marker sought, no out-of-training year read, solved, scored or registered.
Rule 25: ERCOT only. Rules 5/23/24: no `ScenarioConfig` field, no constant,
no derive touched, nothing fitted — the probe is read-only and its two
"parameters" are published dates. Rule 15: no run produced, nothing to
register; keeper and dashboard untouched; RETENTION HOLD honoured (ercot-213
ctl and ercot-204 retained). Rule 28: no mechanism tested ⇒ no cell verdict
minted (28b); no new field ⇒ 28c not engaged; duty (a) discharged — the
queue holds no live in-model item (ercot-216 §5 read re-verified) and this
lane's off-queue charter is the owner dispatch itself; the
`ercot_multiproduct_as` cell note carries the ercot-217 Phase-0 attribution
(same-session edit, the ercot-214 precedent). Rule 27: edits local, exact
on-disk bytes pushed, pushed files ≥300 lines blob-verified. SOM PDFs
re-fetched per the corpus README and sha256-verified; payloads remain
gitignored (nothing tracked changes under `data/raw/ERCOT/`). No new
workflows, no cron, no CI job, no PR (push-and-stop on the designated
branch).

**Session consumed the ercot-217 shorthand. Next shorthand: ercot-218**
(ercot-199 remains unclaimed).
