# FINDING (scoping) — R-CAISO-29: CAISO `PRC_FUEL` decomposed against the model's delivered gas

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`), unchanged. **Zero LP, no build, no shard,
no `ScenarioConfig` field, no cell moved.** Probe: `scripts/probes/_rcaiso29_prc_fuel_decomp.py` (48 OASIS
months, 2022-01..2025-12, all retrieved). The model series is rebuilt through the keeper's own code path
(`hubs._caiso_hub_daily_gas_prices` on the keeper's `scenario_config`, + `CAISO_CITYGATE_TRANSPORT_ADDER` 0.46).

## 0. Result

R-CAISO-25 §4.1's +2.9 / +4.1 $/MMBtu offset is **three terms**, and the largest is **not a fuel cost the model
is missing**:

| 2024 median, $/MMBtu | FRPGE2 (PG&E) | FRSCE2 (SCE) | FRSDG2 (SDG&E) |
|---|--:|--:|--:|
| **PRC_FUEL (non-GHG) − model** (R-CAISO-25 reproduced) | **+4.17** | **+2.89** | **+2.87** |
| (a) LDC cap-and-trade charge = non-GHG − GHG twin | 1.83 | 1.77 | 1.73 |
| **PRC_FUEL (GHG twin) − model** = the comparable gap | **+2.35** | **+1.13** | **+1.14** |
| (b) hub basis: CAISO hub index − NGI CA composite | +0.58 | −0.02 | −0.02 |
| (c) intrastate transport (GHG twin) − model's 0.46 | 2.19 − 0.46 = +1.73 | 1.62 − 0.46 = +1.16 | 1.60 − 0.46 = +1.14 |

(b) + (c) reproduce the GHG-twin gap to ≤ 0.04 (medians, so not exactly additive).

1. **(a) is carbon, and the model already charges it.** CAISO builds two fuel regions per CPUC-jurisdictional
   LDC: a covered-entity region (`…GHG`, transport net of the LDC's cap-and-trade credit) and a non-covered one
   (CAISO BRS, Bidding Rules Enhancements / Commitment Cost Improvements). CA gas generators are covered entities
   and the model prices their CO2 directly (`emission_rate × carbon_price`). Comparing the model to a non-GHG
   region counts carbon twice. R-CAISO-25 used non-GHG regions; **~1.8 of the 2024 gap is that double count.**
2. **(b) is small and region-specific.** The NGI CA composite sits near the SoCal citygate (−0.02 in 2024) and
   below PG&E citygate (+0.58).
3. **(c) is the real term, and it varies 0.07–2.6 by region.** The model's single 0.46 sits at the low end.

### 0.1 All regions, GHG-twin gap and its parts (median $/MMBtu)

| Region | Transport, GHG twin 2022 / 23 / 24 / 25 | GHG-twin gap vs model 2022 / 23 / 24 / 25 |
|---|---|---|
| FRPGE1 = FRPGE3 | 0.39 / 0.07 / 0.07 / 0.31 | +0.64 / +0.38 / +0.24 / +0.26 |
| FRPGE7 | 0.41 / 0.29 / 0.66 / 0.80 | +0.68 / +0.59 / +0.80 / +0.77 |
| FRPGE2 = FRPGE4 | 1.47 / 1.35 / 2.19 / 2.58 | +1.72 / +1.65 / +2.35 / +2.55 |
| FRSCE3 / FRSCE5 | 0.32–0.43 / 0.49–0.56 / 0.84–0.90 / 0.66–0.72 | −0.09–+0.03 / +0.77–0.98 / +0.38–0.42 / +0.79–0.84 |
| FRSCE2 / FRSDG2 | 0.99 / 1.24 / 1.61 / 1.49 | +0.59 / +1.51 / +1.13 / +1.61 |
| FRSCE1 / FRSDG1 | 1.75 / 2.16 / 2.52 / 2.61 | +1.32 / +2.43 / +2.04 / +2.73 |
| LDC C&T charge (a), all regions | 0.97–1.10 / 0.97–1.21 / 1.73–1.83 / 1.50–1.83 | — |

Transport is identified as `PRC_FUEL − EIA weekly-narrative citygate print` (flow day = trade + 1), 24–51 print
days per year. **Validated** against CAISO's published 2025 components (Gas Price Template, Tariff §39.6.1.6.1):
FRPGE2GHG 2.58 vs 2.58; FRPGE1GHG 0.31 vs 0.30–0.32; FRPGE7GHG 0.80 vs 0.80; FRSCE2GHG 1.49 vs 1.47–1.53;
FRSDG2GHG 1.50 vs 1.48–1.55. The C&T split matches too (FRPGE2 − FRPGE2GHG = 1.50 vs published 4.08 − 2.58).

## 1. The fleet-weighted gauge: EIA's own census

Which region each CAISO gas unit sits in is a Master File field and is **not public**, so CAISO's table cannot
be fleet-weighted. EIA's measured CA delivered-to-electric-power price (N3045CA3, in the repo) **is** fleet-weighted:

| Year | Model delivered (annual median of months) | EIA N3045CA3 | Model − EIA | EIA − NGI composite (implied fleet transport + basis) |
|---|--:|--:|--:|--:|
| 2022 | 8.09 | 8.27 | −0.21 | +0.67 |
| 2023 | 4.69 | 5.21 | **−0.74** | +1.20 |
| 2024 | 2.67 | 3.29 | **−0.69** | +1.15 |
| 2025 | 3.46 | 4.06 | **−0.82** | +1.28 |

(Mcf → MMBtu at 1.037.) The census implies ~+1.15–1.28 over the composite in 2023–25. That sits inside the CAISO
GHG-region range (+0.24 to +2.7) and is consistent with it. **The model's delivered gas is ~$0.7–0.8/MMBtu below
the fleet's measured delivered cost in 2023–25.**

**Why, in one line:** the 0.46 was measured as `N3045CA3 − N3050CA3` (delivered minus EIA citygate) but is applied
on top of the NGI CA composite, which runs **0.9–1.2 below** N3050CA3 in 2023–25. The adder and the base it rides
on were measured against different references (a rule-14 basis mismatch, the same family as caiso-242/244).

## 2. What this does and does not mean

- **Not a C3c lever.** It is a level term, flat year-round (r ≈ 0.97). It does not create evening tails.
- **Not a price error yet.** The keeper's offer-band multipliers were derived against the NGI composite staircase
  with no adder (caiso-242 §3, caiso-244). Raising delivered gas alone would shift every gas offer up by
  ≈ $0.7 × HR ≈ **$5–8/MWh** with no re-derivation, and the multipliers would no longer round-trip to the
  measured bids. **Any fix must move the adder and the offer-surface denominator together**, or it double-shifts.
- **What it settles for the open methodology ask** (`CAISO_CITYGATE_TRANSPORT_ADDER`, CAISO shard
  `measured_offer_surface`): a measured, public, forward-reproducible transport basis exists (CAISO's own
  per-region tariff components, published monthly), and the current 0.46 under-states the fleet's measured
  delivered cost by ~0.7–0.8. The comparator is the **GHG** region, never the non-GHG one.
- **Not resolved:** the fleet weighting across regions (not public). EIA N3045CA3 is the only measured
  fleet-weighted gauge.

## 3. Owner ruling

Two decision cards, 2026-10-01:

1. **Queue a joint re-basis** (selected). Not selected: "record only, keep 0.46"; "proceed to link 12" as the answer
   to this card. New link: re-identify the transport adder against the base it actually rides on (the NGI CA
   composite; EIA N3045CA3 − composite ≈ 1.15–1.28 in 2023–25, GHG-region comparator only) **and** re-derive the
   offer-surface denominator on the same basis, so the measured multipliers still round-trip. Scoping + PRECOMMIT
   first; a full-span solve later.
2. **Order: after link 14, as link 15.** R-CAISO-30 stays link 12 (TRNS_USAGE intake); links 13 and 14 follow;
   the re-basis is link 15.

## Sources

- CAISO, Gas Price Component of Projected Proxy Cost (Gas Price Template), effective Jan 2025 – Oct 2026:
  https://www.caiso.com/documents/projected-proxy-cost-gas-price-component-and-projected-greenhouse-gas-allowance-price-effective-2025.pdf ,
  https://www.caiso.com/documents/projected-proxy-cost-gas-price-component-projected-greenhouse-gas-allowance-price-effective-2026.pdf
- CAISO BRS, Bidding Rules Enhancements – Generator Commitment Cost Improvements (GHG fuel regions):
  https://www.caiso.com/Documents/BusinessRequirementsSpecification-BiddingRulesEnhancements-GeneratorCommitmentCostImprovements.pdf
- CAISO OASIS `PRC_FUEL`, `fuel_region_id=ALL`; window on Pacific-day boundaries (07Z under PDT, 08Z under PST —
  the R-CAISO-25 "empty months" were 08Z windows in PDT months, not throttling).
- EIA N3045CA3 / N3050CA3 (repo: `data/raw/gas-prices/`).

## Retrievability (rule 34(e))

Nothing was solved. The probe re-fetches OASIS (~15 min); no data file is committed.
