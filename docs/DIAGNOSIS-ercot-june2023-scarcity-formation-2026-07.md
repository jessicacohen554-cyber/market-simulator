# ERCOT June-2023 scarcity-formation compensation — root-cause forensics (the ercot56 lane)

**Session 2026-07-11 (ercot57 round). Keeper under test: `2026-07-10-ercot56-nucwin`
(CALIBRATED-WITH-CAVEATS, rubric v2.4). Open lane (adopted knowingly at promotion): with the
real June-2023 nuclear structure in place (CP-1 trip + measured ~0.73 late-June derate),
June-2023 overshoots +22 % (was +7 % under the smear) — a rule-15 discovered compensation.
Task: find what over-forms June scarcity, measured-comparison first, no retune of the nuclear
input, offer curves, sigmoids or ORDC (rules 1/13/15/26).**

**Verdict in one line: the June (and September) 2023 overshoot is manufactured by the co-opt's
per-product reserve-shortfall ladders pricing a PHANTOM product-requirement deficit into the
energy duals — phantom because the model's June-evening gas availability runs 2.6–4.1 GW
tighter than ERCOT's measured online capability (statistical WEFOR/EFOR stack vs the 60-Day
DAM disclosure's measured HSL), while the requirement side is measured-faithful and reality's
own ORDC priced ≈$0 at those hours (RTORPA ≤ $15, PRC ≥ 4,880). The measured-input fix is the
`ercot_thermal_dam_availability` class-day rescale (the thermal analogue of ercot56's nuclear
windows); the forward supply-cap and offer-surface suspects are REFUTED (slack / not the
price-setter).**

## 1. June-2023 reconstruction (all measured; keeper payload `lmpDeltaHr` + zonal archive)

Keeper June-2023: model $77.40/MWh equal-hour vs actual RT (HB_BUSAVG) $61.65 → **+25.5 %
equal-hour (+22 % lw, the scorer basis)**. Five days carry the whole overshoot — and the one
genuinely scarce day is UNDER-priced:

| June day | DA>200 h (max) | RT>200 h (max) | model>200 h (max) | PRC min | RTORPA max | share of June gap |
|---|---|---|---|---|---|---|
| 14 | 0 ($101) | 1 ($311) | 5 ($1,354) | 4,883 | $15.0 | 29.9 % |
| 16 | 0 ($190) | 5 ($488) | 5 ($1,331) | 5,341 | $2.8 | 17.1 % |
| 18 | 6 ($392) | 1 ($238) | 5 ($1,378) | 5,039 | $9.3 | 30.8 % |
| 19 | 7 ($529) | 0 ($152) | 7 ($939)  | 5,438 | $1.4 | 34.7 % |
| 20 | 7 ($2,489) | 7 ($4,907) | 8 ($4,246) | 4,125 | $66.5 | **−153 $/h (model UNDER)** |
| 26 | 8 ($1,720) | 0 ($89) | 4 ($468)  | 5,847 | $0.4 | 14.3 % |

The model's over-form prices are QUANTIZED: ~$470 / ~$900 / ~$1,350 (and Jun-20 $2,583 /
$3,514 / $4,246) — exactly the co-opt product-family shortfall-step penalties k×VOLL/12
(VOLL 5,000, `ercot_as_n_ramp` 12, `ercot_as_critical_frac` 0 → $417/$833/$1,250/…/$4,167)
plus the marginal fuel cost. On every over-formed day measured RTORPA ≤ $15 and PRC ≥ 4,880 —
reality priced **no** reserve scarcity there (the real June DA tails on 18/19/25/26 are
DA-boundary offer/expectation formation, RT ≤ $250 — the G-22 family). **Sep-2023 shares the
defect**: +19.1 % equal-hour, concentrated on Sep 20/22/23/24/26 (RTORPA ≤ $7, PRC ≥ 5,288,
model $522–2,734 at the same rungs); the real Sep 7–8 events (RTORPA $273/$108) are roughly
captured.

## 2. Attribution — each suspect tested against measured data

Method: rule-16 throwaway 2023 re-solve of the keeper config with capture wrappers at the
`apply_reserve_coopt` / `run_energy_solve` seams (June parity vs the committed keeper payload:
mean within 0.4 %, 36/720 h differ ≥$1 — alternate optimal duals at degenerate step vertices).

* **(b) requirement side — FAITHFUL.** Per-product requirements are the measured AS plan
  (ASPLANNP433) minus the measured LR-RRS credit (~770–860 MW) and measured battery AS-award
  credit (~1.3–1.9 GW): June evenings fast ≈ 3.0–3.5 GW + NSPIN 2.7–3.6 GW. Zero June hours
  with fast-req > measured RTOLCAP; only Jun-20 HE16-20 has all-req > RTOLCAP+RTOFFCAP — the
  real event, correctly the tightest.
* **(c) reserve-supply cap rows — REFUTED as driver.** The keeper's WS-A forward cap
  (`ercot_reserve_supply_forward=True`) sits at 10.3–10.7 GW (fast) at the over-form hours —
  far ABOVE the fleet's headroom — and its dual is 0.0 everywhere in June. The cap is slack;
  measured-vs-forward cap choice is immaterial to this defect.
* **(c′) offer surface — NOT the price-setter.** The conditional surface reprices 426 gas
  peak rungs in the top net-load bins (binds 263 h/yr); the observed clearing levels are the
  reserve-step penalties + mc, not surface rungs. (On Jun-20 the surface's measured wall is
  what the depth SHOULD come from — see §4.)
* **(a) availability — THE DEFECT.** At every over-form hour the model's entire spare
  responsive capacity is already holding reserve (headroom == cleared reserve, 4.2–6.6 GW) and
  the four product families short by 0.3–2.6 GW, all equalizing at the same marginal step. The
  physical shared-headroom rows bind, so the step penalty flows into the energy dual (the
  supply-cap dual carries none of it). Model vs measured at those hours:

  | hour | model headroom | measured RTOLCAP | +RTOFFCAP | model deficit vs product req |
  |---|---|---|---|---|
  | Jun 14 HE20 | 4,780 | 5,836 | 7,757 | 2,154 |
  | Jun 16 HE17 | 4,824 | 6,929 | 7,969 | 1,646 |
  | Jun 18 HE19 | 4,249 | 6,968 | 7,531 | 1,881 |
  | Jun 19 HE19 | 4,530 | 8,444 | 8,658 | 1,464 |
  | Jun 26 HE13 | 6,493 | 8,506 | 9,139 | 177 |

  Energy side is faithful (model thermal dispatch −0.2..−1.2 GW vs EIA-930 fossil+nuclear at
  the same hours), so the whole headroom gap is availability: **the model's available
  responsive capacity runs ≈4 GW below reality's demonstrated level (930-gen + measured
  capability basis)**. The fifth co-opt family (`ercot_ordc_total`, the real ORDC total-reserve
  curve) prices $15–43 at those reserve levels — matching measured RTORPA — and $254–1,383 on
  Jun-20: that family is CORRECT; the per-product VOLL-ramp ladders are what print.

## 3. Availability forensics (May-2024 method: DAM Gen_Resource OUT, config-collapsed + CEMS)

* **Discrete windows are broadly right, with identified edge errors.** June-2023 real
  thermal+nuclear DAM-OUT runs 4.0–8.0 GW. Top model-zeroed CC plants on Jun 14 check out
  as genuinely OUT (Frontera 529, Victoria 300, Sand Hill CC 448); errors found: Bastrop
  (~815 MW) zeroed from Jun 14 but real OUT starts Jun 16 (2-day-early edge); Tenaska Gateway
  (~257 MW) zeroed on days DAM shows ON (the May-2024 repeat offender); T H Wharton
  (~1,092 MW) zeroed while DAM shows the trains OFF-but-available (HSLs alive) — the CF<5 %
  facility-mask idle-vs-out ambiguity, though Wharton ran ≈never (commitment question, not
  pure availability).
* **The statistical layer is the big term.** June-evening model class derates (Jun 14–26,
  HE19-21): CC_REGULAR 23.8 % (7.9 GW; 5.0 GW windows-zeroed + 3.4 GW statistical at ~12.8 %
  on the running fleet), CT_PEAKER 23.9 % (0.78–0.82 statistical baseline — WEFOR relief is
  configured for ST_CHP/ST_GAS only, CC/CT carry the full statistical stack on top of the
  windows), COAL 18.0 %, vs DAM-disclosure OUT of only ~6-7 % (CC) / ~3.8 % (CT). Matched
  class-day basis (config-collapsed live HSL / site ratings): measured June CC 0.79–0.83 and
  CT 0.85–0.87 vs the model's 0.76 — the statistical estimate is 7–10 pp tighter than the
  measured realization of the same quantity exactly at the June margin. (ST_GAS runs ~2.3 GW
  LOOSE — idle steamers the detector exclusions keep available — partially masking the CC/CT
  tightness in fleet totals; separate documented lane.)
* **ercot55 cross-check:** Jun 14/16 over-formed in ercot55 too (day-means $213/$211 vs
  actual $54/$95 — nuclear was ~full those days); the nuclear windows only deepened Jun
  18/19/26 (+75/+38/+18 $/day-mean) and correctly improved Jun-20 (+189 toward actual). The
  defect PRE-DATES ercot56; the honest nuclear input moved more days over the same cliff.

## 4. Named owner and the fix

**Owner: the co-opt's per-product VOLL-ramp shortfall ladders pricing a phantom product
deficit created by the statistical availability stack at the summer-evening reserve margin.**
Two coupled parts:

1. **Input (fixed this round, rules 13/14/15):** `ercot_thermal_dam_availability` — measured
   class-day thermal availability from the 60-Day DAM disclosure (config-collapsed live HSL /
   site ratings; CC_REGULAR + CT_PEAKER scope), applied in backcast as a RESCALE of the
   finished availability so each class-day mean equals the measured fraction (the model's own
   windows stay as the within-class distribution — no stacking, no double-count; uncovered
   dates keep the statistical model; forecast unchanged — the G4 mode-aware seam; zero fitted
   parameters). Deriver `scripts/data/derive_ercot_thermal_dam_availability.py` →
   `data/raw/ercot-thermal-dam-availability.csv` (frozen, rule 23).
2. **Mechanism (documented, NOT changed this round — owner design call):** the per-product
   shortfall penalties (`nyiso_rcpf_product_shortfall_steps`, k×VOLL/12 from step 1 = $417)
   are an imported NYISO-RCPF construction with no pre-RTC+B ERCOT analogue: 2023-25 ERCOT
   has NO real-time per-product scarcity pricing — RT reserve scarcity prices through the
   ORDC total-reserve curve only (the model's fifth family, verified ≈measured RTORPA at
   matching reserve levels), and a product-vs-capability squeeze triggers RUC commitment, not
   a price. With faithful availability the ladders rarely bind (reality always covered its
   plan), so the input fix defuses them; if a future residual still traces to the ladder
   design, that is a G-lane market-design change needing its own spec (and it would also
   re-open how the Jun/Aug-2023 depth forms — on Jun-20 the model currently reaches $4,246
   via step-10, where reality's λ $4,761 at RTORPA $66 was OFFER-driven: post-fix, depth on
   true event days must come from the measured offer surface, the structurally right channel).

**Expected honest trade (logged up front):** the 2023 C3c tail count currently leans on the
phantom June/Sep hours (28 + 16 of the model's 171 h sit on days measured RTORPA < $10 —
while Jul/Aug DA-shoulder days under-form). Removing phantom scarcity can pull C3c-2023 below
the 162-h owner gate; per rules 1/15 that residual then belongs to its real owner (the G-22
offer-formation family), not to phantom availability. Keeper promotion is the owner's call.

## 5. Session artifacts

* Fix: deriver + CSV + `ScenarioConfig.ercot_thermal_dam_availability` + fleet rescale +
  both-CLI wiring + tests (`tests/test_outages.py::ErcotThermalDamAvailabilityTest`).
* Runs: rule-16 2023-only probe (never registered) → full-span 2023–2025 ercot57 bundle +
  zero-forcing twin, solved and registered via CI (see the ERCOT-57 calibration-log entry for
  scores and disposition).
* Refuted suspects recorded here so they are not re-run: forward reserve-supply cap (slack,
  dual 0), offer-surface bin boundaries (not the price-setter), AS-plan requirement level
  (measured-faithful), demand/renewables inputs (clean; E-gap −0.2..−1.2 GW).
