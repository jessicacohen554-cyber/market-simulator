# FINDING — miso-274: the keeper's CC_REGULAR shortfall is a MERIT object, not an availability one. Candidates 1 and 2 cannot close it; no LP is earned. Candidates 3 and 4 wait on the owner.

```
LANE    : miso-274 (MISO lever queue §5.4; routed by RESULT-miso273 §3)
KEEPER  : 2026-09-25-miso-273-screened-coal (results/calibration/miso273_span) — unchanged
LP      : none. Zero-LP phase 0 only (rule 29 clause 0 practice)
PROBES  : scripts/probes/_miso274_cc_phase0.py        -> results/calibration/_miso274_cc_phase0.json
          scripts/probes/_miso274_cc_basis_census.py  -> results/calibration/_miso274_cc_basis_census.json
PRUNE   : rule-35 carry-over from miso-273 done first (PR #6696): miso-272 run pruned, audit_keepers --iso MISO PASS 0/0
```

## 1. The question

The miso-273 keeper under-dispatches CC_REGULAR by −0.70 / −6.68 / **−13.69 / −10.47 / −8.85** / −3.68 / −3.58 TWh
(2019–2025). The 2023 value is the train tier's only failure. There are two possible roots:
- **Availability:** the CC fleet is clipped, so the LP *cannot* run it.
- **Merit:** CC has headroom in the hours in question, and the LP *chooses* coal.

## 2. Availability does not bind (zero LP, keeper fleet rebuilt with `fleet_only`)

The hourly CC_REGULAR available MW (`pmax × availability`) was joined to the keeper's committed
`hourly/class_hourly_<Y>.parquet` P1 dispatch.

| year | CC avail TWh | CC dispatch TWh | hours dispatch ≥ 99 % of avail | CC headroom TWh | headroom in hours coal runs above its committed band |
|---|---:|---:|---:|---:|---:|
| 2019 | 138.34 | 103.93 | 0 | 34.41 | 34.41 |
| 2020 | 140.59 | 104.67 | 0 | 35.92 | 35.92 |
| 2021 | 146.72 | 94.34 | 0 | 52.39 | 52.39 |
| 2022 | 171.70 | 118.55 | 0 | 53.15 | 53.15 |
| 2023 | 181.46 | 137.91 | 3 | 43.55 | 43.55 |
| 2024 | 181.14 | 146.37 | 4 | 34.77 | 34.77 |
| 2025 | 170.73 | 138.70 | 13 | 32.02 | 32.02 |

**Reading:**
- The fleet availability constraint binds in 0–13 hours a year.
- Coal is dispatched above its committed band in **all 8,760 hours** of every year.
- So every MWh of CC headroom coincides with coal on the margin.

The shortfall is decided by the offer stack, not by availability.

## 3. Candidate 2 — per-plant availability vs EIA-923 (the Cottonwood pattern)

Per-plant CC_REGULAR available TWh was compared with EIA-923 net generation (CT/CA/CS prime movers) for the
same plant codes.

| year | plants below own 923 output | shortfall TWh | main plants |
|---|---:|---:|---|
| 2019 | 2 | 0.36 | Perryville 55620, Magnet Cove 55714 |
| 2020 | 5 | 3.87 | Riverside 55641 (0.50 avail vs 2.66 metered), 862 (0.22 vs 1.14), 55620 |
| 2021 | 3 | 2.08 | Riverside 55641 (1.47 avail vs 3.23 metered), Magnet Cove 55714 |
| 2022 | 3 | 0.89 | 55714, 55641, Delta Energy Park 63259 |
| 2023 | 4 | 0.96 | Perryville 55620, 55641, 55714, 63259 |
| 2024 | 6 | 1.20 | 55620, 55641, Zeeland 55087, 1007 |
| 2025 | 7 | 2.26 | Edwardsport 1004 CC part, Cottonwood 55358, 55087 |

A plant clipped below its own meter is a real defect, but it tops out at 0.4–3.9 TWh/yr of availability. With
32–53 TWh of fleet headroom, the LP substitutes another CC plant. **Candidate 2 cannot close the shortfall.**

## 4. Candidate 1 — CC outage numerator basis (census, exact accumulator)

The census re-runs the keeper's own shared accumulator (`_unit_outage_factors_from_events`: keeper flags, LP
roster) on the ≥ 5-day unitroute and < 5-day short-gas CC_REGULAR rows, twice:
- as the keeper does it (`ucap / cap_LP`);
- with each row's `ucap` rescaled by `cap_LP / basis`, so that the same divide yields the extract's own fraction
  `ucap / basis` (the nyiso-196 construction, with `basis` from `_extract_basis_index`).

| year | keeper removes TWh | extract-own-basis removes TWh | excess TWh | largest bins |
|---|---:|---:|---:|---|
| 2019 | 54.89 | 52.68 | 2.21 | 55173, 55380, 55714 |
| 2020 | 63.46 | 58.51 | 4.95 | **55641 2.03**, 862, 55714 |
| 2021 | 64.93 | 61.23 | 3.70 | **55641 1.73**, 55087, 55714 |
| 2022 | 52.42 | 48.53 | 3.89 | 55641 0.93, Black Dog 1904, 55714 |
| 2023 | 47.75 | 43.73 | 4.02 | 55641 0.67, R D Morrow 6061, Cottonwood 55358 |
| 2024 | 49.53 | 45.68 | 3.85 | 6061, 55641, 55620 |
| 2025 | 57.78 | 52.99 | 4.78 | 1904, 55358, 55641 |

**The basis defect is real: 2–5 TWh/yr of CC availability over-removed.** For the same reason as §2, it cannot move
CC volume materially: the added availability lands in hours that already have tens of GW of CC headroom.

**The largest bin is not a basis defect. It is a mis-route.**
- CAMPD facility 55641 (Riverside Energy Center, WI) reports four CTs: CT-01 to CT-04.
- EIA-860 files CT-03/CT-04 under a different plant: **West Riverside Energy Center 64020** (CTG3 / CTG4 / STG2,
  2020 COD).
- The outage router (`_generic_unit_outage_target`) takes `facility_id` as the plant code. So West Riverside's
  commissioning-era and later outages derate the old 552 MW Riverside bin, which is why 55641 is carried at CF
  0.31 against a metered 0.67 in 2021. West Riverside's own bin (64020) receives none of them.
- Neither construction is right at this plant: the extract-own-basis fraction still charges 27 % of the old bin
  per West Riverside CT.
- The right repair is **unit-level routing of CAMPD stacks to their EIA plant**. No EPA–EIA unit crosswalk is
  committed, and the CAMPD unit-level parquet carries no associated-generator field. That makes this a
  data-intake question, routed below, not a solve.

**Design note for whoever arms candidate 1 (rule 19).** `unit_outage_extract_basis_share` and
`unit_outage_dispatched_bin_denominator` are mutually exclusive in the loader, because both set the
denominator. One construction serves both:
- membership and the non-CC divide from the LP roster (miso-266);
- the CC_REGULAR removed **fraction** on the extract's own basis (nyiso-196), applied to `cap_LP`;
- CHP bins unchanged.

This census is exactly that construction, with the Riverside mis-route inside it. Its zero-LP footprint is the
table above.

## 5. The merit side (what is left)

**EIA-923 fleet-realized CC heat rate** (the same plants): **7.27 / 7.29 / 7.13** MMBtu/MWh in 2021 / 2022 / 2023.
- The CAMPD-measured per-plant rate the keeper uses (`measured_cc_heat_rates`) agrees with it. At Union 55380, for
  example, the artifact reads 7.265 and EIA-923 reads 7.221.
- The LP's CC econ-band offer rate is **~×1.12 higher**: gen-weighted 7.98 econ and 7.90 committed against 7.13
  measured in 2023.
- That uplift is the keeper's `offer_curve_by_group` CC_REGULAR band multipliers: committed 1.1055, econ_low 1.045,
  econ_high 1.188, over physics 1.005 / 0.887 / 1.008.

The coal bands' mean offer levels (cap-weighted, 2021 / 2022 / 2023):

| class | econ band | committed band | must-run band |
|---|---|---|---|
| COAL_PRB | $29.6 / 33.0 / 33.2 | $8.7–10.9 | ~$5 |
| COAL_BIT | $32.4 / 39.4 / 43.7 | — | — |

The coal band multipliers are 1.1 / 1.1 / 1.309 (PRB) and 1.1 / 1.1 / 1.21 (BIT). The CC econ band sits at
$41.0 / 55.4 / 27.2.

The relative level of those two sets of band multipliers is the only thing that moves the ~9–14 TWh.
- **That is the owner's authorized channel** (rules 1 and 13, 2026-09-05 amendment): one config across every
  scored year, set ex ante, declared in a PREREG, and never swept against the gates.
- This lane does not choose it.

Imports are **not** the displacer. EIA-930 MISO net imports are 35.4 / 31.0 / 37.9 TWh (2021–23), against the
model's 33.7 / 22.8 / 40.1.

## 6. Verdict and routing

| candidate | verdict | basis |
|---|---|---|
| 1 CC outage numerator basis | real, 2–5 TWh/yr of availability; **cannot close** the C1 gap | §2, §4 |
| 1a Riverside / West Riverside mis-route | real; needs a CAMPD-unit → EIA-plant crosswalk (**data ask**) | §4 |
| 2 per-plant clip vs EIA-923 | real, 0.4–3.9 TWh/yr of availability; **cannot close** | §3 |
| 3 coal vs CC band multipliers | **the lever**; owner channel, **ASK** | §5 |
| 4 C3b 2021 February gas array (D1) | unchanged, owner decision pending, **ASK** | — |

No LP is earned by candidates 1 or 2 as a C1 lever. Under rule 1, candidate 1 remains a legitimate structural
repair. If the owner wants it armed on structure alone, it is a 7-shard span (one per year, 2019–2025; rules 34(c)
and 36). Its expected C1 effect is small by §2.
