# FINDING — PJM-NEXT-26 side card (a): IMM balancing operating reserve credits by zone vs the CT location residual

Zero LP. Probe `scripts/probes/_pjmnext26_bor_zone_census.py`; data
`results/phase0/pjm/_pjmnext26_bor_credits_by_zone_type.csv` (294 rows, table and page per row, digitized from
IMM State of the Market Section 4, `monitoringanalytics.com/reports/PJM_State_of_the_Market/<Y>/<Y>-som-pjm-sec4.pdf`,
2019–2025; PDFs not committed); output `results/phase0/pjm/_pjmnext26_bor_zone_census.json`.

## 1. Sign correction to the handoff

The handoff described card 2 as "AEP-Ohio / Dominion over, ComEd under" for the model's CTs. In
`_pjmnext25_ct_location.json` the field is `real_minus_model_twh`: AEP-Ohio +1.7…+3.7 and Dominion +1.5…+2.4
(2019–22) mean the **model under-runs** CTs there; ComEd −2.4…−5.2 (2022–25) means the model **over-runs** ComEd CTs.

## 2. What the IMM publishes

- Balancing credits by unit type every year: CTs take 86.3 / 91.2 / 92.8 / 75.2 / 85.7 / 76.1 / 56.4 % (2019–25) of
  $52 / 58 / 128 / 182 / 84 / 121 / 518 M.
- Credits by control zone only 2019–2022 (the geography table, DA + balancing, all unit types); dropped from 2023–25.
- No zone × unit-type table; the top-10 recipients table covers 13–51 % of balancing credits.

## 3. Pre-fixed reading and result

Reading (fixed before the numbers): CONFIRMED if, in ≥ 2 testable years, the most model-under-run zone is top-2 by
real credit share AND every model-over-run zone sits below its load share.

| zone | load share | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|
| AEP_Ohio | .218 | .205 (+2.55) | .245 (+1.73) | .246 (+3.02) | .215 (+3.70) |
| ComEd | .119 | .223 (+0.46) | .237 (+0.64) | .217 (+1.37) | .098 (−2.38) |
| Dominion | .150 | .164 (+2.13) | .153 (+1.47) | .194 (+2.23) | .185 (+2.44) |
| SWMAAC | .074 | .214 (+0.47) | .133 (+0.82) | .078 (+1.09) | .226 (+0.49) |
| EMAAC | .167 | .094 (−0.61) | .114 (+0.03) | .116 (−0.17) | .110 (+0.18) |

(credit share, real − model CT TWh in brackets; ATSI, Central_PA and West_APS in the JSON.)

**CONFIRMED, weakly: 3 of 4 testable years (2020, 2021, 2022), under the correct sign.** 2022 passes on Central_PA by
.0016; with the charges column as the load proxy it fails, leaving 2 of 4. The top-10 CT recipients are almost all
Dominion (Marsh Run, Louisa, Doswell) and AEP (Mone, Riverside, Foot Hills); one ComEd CT appears (Elgin 2022, 1.1 %).

## 4. Consequence

The CT energy the model misses sits where PJM pays the most out-of-merit balancing credits: CT commitment for
reliability and operator conduct that a price-dispatched LP cannot reproduce. This supports the plan §3.6 ledger
entry for CT_PEAKER 2021 ("out-of-merit commitment; inadmissible as a lever"). It is evidence for a ledger or frontier
row, not a lever. The ComEd over-run years (2023–25) have no zone data, so they are untestable on this source.
