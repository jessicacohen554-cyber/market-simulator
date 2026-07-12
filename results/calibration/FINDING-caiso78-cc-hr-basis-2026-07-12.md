# FINDING — caiso-78 STEP-0: nothing "holds CC online" through the evening ramp — the CT under-run is pure offer-band ordering, and the ordering itself is corrupted by a heat-rate/capacity-basis bug (`cc_nameplate_summer_derate` deflates every CC plant's base HR by its net-summer/nameplate ratio) (2026-07-12)

**STEP-0 for the post-caiso-77 session Task 1** (the C1-2023 CC_REGULAR +4.50 TWh
residual and the CT_PEAKER evening-ramp under-run, lead (c)). Model side: the
caiso-77 keeper payload (`2026-07-12-caiso-77-firm-selfschedule`, the scorers'
own decode). Actual side: CAMPD CA unit-level gross load, bench-restricted
(same fleet both sides). Diagnostic script:
`scripts/probes/_caiso78_step0_ramp_mechanism.py` (stage 1 = payload+CAMPD;
stage 2 = `run_year(fleet_only=True)` rebuild of the keeper's own fleet/mc —
the G-22 convention, the SAME offer prices the LP solved on; no LP built).

## 1. The mechanism candidates, decided by measurement

The session task named three candidates for what keeps model CC online through
the ramp (summer h17-20, winter mornings h5-7) while reality serves it with CT
starts. All three are now decided:

**(a) RA-bridge floors — NO.** D-2 (committed bundle): `ra_mustoffer_bridge`
forces 2.36/1.87/1.75 TWh of CC (3.2-3.8 % of class) and ~0.1-0.3 % of CT.
Even attributing every bridge-MWh to the ramp windows cannot reach the CC-over
(+5.7 TWh same-fleet 2023), and the D-1 CC profile passes. Not the holder.

**(b) Min-down / cycling physics — NO (and the measured-run CC amortization
lead is refuted ex-ante).** The "model CC never cycles" premise (written on the
caiso-76 payload, pre-must-flow-imports) is dead on caiso-77: model CC starts
2963/3038/2661 vs actual 2996/2681/2688, cap-weighted median run 15.5/15.0/16.0 h
vs actual 19.0/17.0/17.0 h, overnight-off day share 8.7/9.4/6.4 % vs actual
9.0/11.6/13.1 %. Model CC cycles *about as much as* reality — slightly MORE
(shorter runs). The stage-2 startup-amortization arithmetic (the caiso-70/71
decide-before-solving method): the keeper's P0-run amortization is p50
$3.23/3.57/3.03 per MWh; the counterfactual amortization over each plant's
MEASURED CAMPD run length is p50 $2.63/2.78/2.78 — *lower*, because actual runs
are LONGER than model runs. A CC analogue of the CT v3 measured-run lever
(`tranche_startup_measured_runs`, today CT-only by construction) would re-order
CC vs CT for **0.0 %** of CC capacity in every year (the CT−CC base-mc gap is
$43-82/MWh). Do not build it.

**(c) Offer-band ordering — YES, totally.** Stage 2, every year, both ramp
windows: the cheapest CT offer is cheaper than the model's marginal CC offer in
**0.0 % of hours** (2023 sum-eve: marginal CC p50 $55.7 vs cheapest CT p50
$64.8; 2024: $41.1 vs $52.9; 2025: $44.2 vs $59.4), and the LP always holds
0.98-4.4 GW (p50) of idle CC capacity priced BELOW the cheapest CT — enough to
cover the hour's whole CT deficit in 60-99 % of ramp hours. In a pure LP with
that stack, CT cannot clear until the sub-CT-priced CC is exhausted. No floor,
no commitment mechanism, no reserve product is involved (consistent with every
prior negative: caiso-70 bridge-decrowding, caiso-70/71 system+locational AS,
ramp-envelope inert, LCR +39 MW).

## 2. But the ordering itself is wrong — the CC-over is six plants, not a class

Same-fleet CC_REGULAR excess (model − CAMPD), by plant, TWh:

| plant | name | zone | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 260 | Moss Landing | NP15 | +1.94 | +3.27 | +3.28 |
| 62115 | AES Huntington Beach EC | LA_BASIN | +1.62 | +1.71 | +2.99 |
| 62116 | AES Alamitos EC | LA_BASIN | +1.53 | +1.82 | +2.66 |
| 55345 | Otay Mesa EC | SDGE | +1.39 | +1.04 | +1.56 |
| 55151 | La Paloma | ZP26 | +1.28 | +0.89 | +1.32 |
| 55656 | **Pastoria** | SP15_rest | **−1.79** | **−1.69** | **−1.71** |
| (whole class) | | | +5.74 | +7.66 | +12.32 |

Five plants ≈ the entire class excess, every year, offset by ONE persistent
under-plant. The signature is a within-CC merit-order scramble, not a broad
class-level economics error. (Month×hod: the excess loads overnight h0-5 and
the morning shoulder h6-11, growing 2023→2025 — the same locus as before, but
now attributable.)

## 3. Root cause — a heat-rate/capacity-basis bug in `fleet_to_bins`

`data/fleet.py::fleet_to_bins` accumulates each plant's capacity-weighted heat
rate on **net-summer** weights (`hr_cap += pmax_net_summer × heat_rate`), then
under `cc_nameplate_summer_derate` (keeper-resolved **True** for CAISO; also
PJM/NYISO/NEISO) rescales the plant's capacity up to full EIA-860 nameplate
(`cap = cap / ratio`, ratio = net_summer/nameplate — intended: the LP carries
nameplate, the availability builder reapplies the summer derate seasonally) —
and only THEN divides: `base_hr = hr_cap / cap`. Heat rate is an intensive
property; dividing by the *inflated* capacity deflates every CC plant's base
heat rate — and every offer-curve band built on it — by exactly its own
net-summer/nameplate ratio. Verification against the keeper's own built fleet:

| plant | source HR (EIA/923 parquet) | derate ratio | built base HR | ratio × source | CEMS 2023 gross HR |
|---|---|---|---|---|---|
| 260 Moss Landing | 7.277 | 0.7296 | 5.310 | 5.310 ✓ | 7.03 (net ≈ 7.28) |
| 62116 Alamitos EC | (vintage-bin 6.30) | 0.9010 | 5.676 | 5.676 ✓ | 6.80 |
| 55345 Otay Mesa | 7.135 | 0.8340 | 5.951 | 5.951 ✓ | 6.89 |
| 55151 La Paloma | 7.645 | 0.8737 | 6.680 | 6.680 ✓ | 7.30 |
| 55656 Pastoria | 7.691 | 0.9718 | 7.474 | 7.474 ✓ | 8.28 |

The deflation is **differential** — that is why it scrambles the merit order
and produces exactly the observed plant table: the biggest nameplate-vs-summer
gaps (Moss Landing −27 %, Otay Mesa −17 %, La Paloma −13 %, the AES ECs −10/−11 %)
get the biggest artificial fuel-cost discount, jump the stack and run
near-flat; Pastoria (−2.8 %, the smallest discount in the cohort) is priced
correctly relative to its own physics but *relatively* over-priced vs its
deflated peers, and under-runs by the same ~1.7 TWh every year. Across the 51
CAISO CC plants with an EIA-860 ratio: median offer understatement 9.9 %,
p10-plant 22 %, worst 75 %. The parquet HR is the plant's real net heat rate
(Moss Landing 7.28 ≈ CEMS gross 7.03 / 0.965 aux) — the deflation is pure
accounting error, not an alternative estimate.

**History note (how it survived):** the run-26/27 comments in
`pipeline/backcast_config.py` record the symptom appearing the day the flag was
enabled — "the un-walled CC fleet cleared its now-exposed top slices too cheap
and mildly over-ran on energy (+2 TWh/yr) while DEPRESSING the marginal LMP" —
and the response was an offer-LEVEL re-tune (econ_high 1.12 → 1.21). That
re-level (itself CAMPD-grounded) compensated part of the MEAN deflation but
could never fix the CROSS-PLANT scramble, which is what C1 has been printing
since. A related sibling was caught earlier (the PJM duct-band 8 % cap notes
the nameplate-vs-summer gap "folds the ambient summer derate into the duct
band") — the HR side of the same rescale was missed.

**Blast radius (rule 24 note):** `cc_nameplate_summer_derate` is default-on for
PJM, NYISO, NEISO and CAISO. Every keeper of those ISOs solved with a
CC offer stack deflated per-plant by net-summer/nameplate. Their frozen bundles
stay (recorded configs/shas); their lanes must re-gate on the fixed code —
flagged as an open item per ISO, NOT silently re-solved here (their offer
multipliers were partly calibrated on the deflated base). ERCOT (curated CAMPD
bins, never `fleet_to_bins`) and MISO (flag off) are unaffected.

## 4. Probe caiso-78 (pre-registered before solving)

**The fix, not a flag:** `fleet_to_bins` computes `base_hr` on the SAME
capacity basis the weights were accumulated on (before the nameplate rescale).
Code-level correction of a measured physical input (rule 14 — the accurate
value is known and the deflated one is a bug); regression-tested
(`tests/test_fleet.py::TestCcNameplateRescaleHeatRate`). The
capacity rescale itself (nameplate in the LP, summer derate via availability)
is intended and unchanged.

Recipe: byte-identical to the caiso-77 keeper
(`scripts/probes/_caiso78_cc_hr_basis_ab.py` = the caiso-77 script on the
fixed code), main + zero-forcing ablation twin, 2023-2025 in one bundle.
Zero new free parameters; zero flags. The offer-curve multipliers
(committed 1.00 / econ 0.95-1.21 / peak 2.25) are untouched — they are
CAMPD-grounded RELATIVE bands and now multiply the correct base. Fix
verified on the rebuilt 2023 fleet: Moss Landing base HR 5.310 → 7.277
(= its EIA/923 parquet value; CEMS-consistent), Pastoria 7.474 → 7.691,
AES ECs → their vintage-bin 6.300 (parquet HR absent); capacity rescale
(nameplate in the LP) byte-unchanged.

Directions, called before the solve:

- **C1 CC_REGULAR (the target)**: falls toward the band in all years — the five
  deflated plants (Moss Landing, both AES ECs, Otay Mesa, La Paloma) drop down
  the merit toward their actual CFs; Pastoria rises toward its actual. The
  within-class scramble (the §2 table) compresses.
- **CT_PEAKER**: rises MODESTLY, and honesty demands the ceiling be stated:
  re-running the stage-2 ordering test on the FIXED fleet (payload dispatch
  held fixed), the 2023 sum-eve marginal CC offer p50 moves $55.7 → $58.3
  while the cheapest CT stays $64.8 — the class-margin ordering does NOT
  flip. The lift comes from the repriced high-gap plants' top slices and
  from pocket/zonal margins, not from a wholesale re-ordering; most of the
  CT volume gap is expected to REMAIN open and stays owned by the
  local-commitment granularity lane (caiso-71 §3, QUEUED Bay-Area/LA-Basin
  topology).
- **C5a CO₂**: falls with the CC MWh (2024/25 +11.8/+28.3 % → down).
- **C4 gas r**: rises (the scrambled plants' profiles were the biggest
  same-fleet misfits).
- **DISCLOSED — C3a/C3b (LMP)**: overnight/belly λ RISES (the marginal CC
  offer is ~10 % higher), so the already-failing C3a overprice (+21.8/+29.9/
  +38.2 %) prints WORSE. Per rules 1/14 the corrected heat rate stays
  regardless: the deflated HR was silently compensating for whatever really
  overprices the body (fuel-basis level? demand basis? — lane 4's open
  root-cause question), and burying it back inside a wrong heat rate is
  exactly what rule 14 forbids.
- **DISCLOSED — C2 family basis**: model gas falls; the 930-family C2 rows
  (2023 already −1.67 TWh under on a basis whose non-CEMS residual is −5 TWh)
  may print further under while the CEMS same-fleet truth improves — the same
  adjudication posture as caiso-77 §5 (the family-basis rework, session
  Task 2, stays open and becomes more pressing).

**Promotion bar** (vs caiso-77, v2.4, G-21b bench): C6+C7+C8 PASS hold; the
targeted C1 cluster improves (2023 magnitude down, 2024 stays in band) with the
§2 plant table visibly compressed; C5a improves; C2/C3a moves adjudicated per
the disclosures above (a C3a/C3b print regression from correcting a measured
physical input is a disclosed counter-move, not a mechanism regression — rule
14). LOYO exemption claimed per the caiso-76/77 precedent: nothing is fit — the
delta is a code-level correction of a measured input, identical in all years by
construction; flagged for owner review.

## 5. Files

- `scripts/probes/_caiso78_step0_ramp_mechanism.py` — the STEP-0 diagnostic
  (stage 1 payload+CAMPD, stage 2 fleet-only offer stack; rule-15 visibility,
  derives nothing, writes nothing).
- `src/market_sim/data/fleet.py::fleet_to_bins` — the fix.
- `tests/test_fleet.py::TestCcNameplateRescaleHeatRate`.
- `scripts/probes/_caiso78_cc_hr_basis_ab.py` — the pre-registered A/B recipe.
