# brattle-pjm-cone-2025 — KEY-TABLE EXTRACT

Trimmed conversion: cover + Table ES-1 CONE estimates (all five CONE areas,
Gas CT / Gas CC / BESS 4-hr) + the per-technology overnight-capital-cost
tables (CT p.43-44, CC p.56, BESS p.66). Full 112-page markdown regenerates
via scripts/data/fetch_cost_benchmark_sources.py --to-markdown; QA performed
against the full conversion in the intake session (2026-07-19).
Source PDF sha256: cf0e1805f81aa0691cef9fba8db7f7b0c082e090b21e3a77b3b34f4d02725588

---

## [page 1]

Brattle 2025 CONE Report for PJM
Informing Parameters for PJM’s RPM Auctions for Delivery Year 2028/29 through 2031/32
PREPARED BY PREPARED FOR
The Brattle Group PJM Interconnection, LLC
Samuel A. Newell
Andrew W. Thompson
Bin Zhou
Nathan Felmus
Harsha Haribhaskar
Sargent and Lundy
Sang H. Gang
Joshua C. Junge
Hyojin Lee
Liam Tawelian

---

## [page 2]

NOTICE
This report was prepared for PJM Interconnection, in accordance with The Brattle Group’s
engagement terms, and is intended to be read and used as a whole and not in parts. The report
reflects the analyses and opinions of the authors and does not necessarily reflect those of The
Brattle Group’s clients or other consultants.
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | i

---

## [page 11]

reservation price an entrant would need if anticipating future downward reversion of market
revenues as supply chains expand. We therefore present several alternative calculations that
reflect distinct concepts for the Net CONE or Reference Price to inform VRR curve parameter
recommendations: (1) Level-Nominal CONE and Net CONE, which is the traditional level-nominal
calculation given premium current costs and forward E&AS revenues; (2) Long-Run Net CONE
Estimates, which provide indicators of long-run marginal costs absent current premium pricing;
and (3) Short-Term Reservation Prices, which reflect the first-year or short-term clearing price for
capacity needed to attract current entrants considering both of the above.
Concept 1: Level-Nominal CONE and Net CONE
Estimated capital costs are translated into the level-nominal net revenues the resource owner
would need to earn an adequate return on and of capital, assuming a 20-year economic life with
real all-in net revenues declining at the rate of inflation. This calculation also involves a cost of
capital. We estimate an after-tax weighted-average cost of capital (ATWACC) of 9.5% for a
merchant generation investment, based on analysis of publicly-traded merchant generation
companies and other reference points. While the CONE calculation only depends on the ATWACC
and not on the individual components, we do present self-consistent financial parameters based
on our analysis of comparable companies. The 9.5% ATWACC thus corresponds to a return on
equity of 16.0%, a 5.8% cost of debt, and a 55/45 debt-to-equity capital structure with an
effective combined state and federal tax rate of 27.7%.9 This ATWACC is higher than in the prior
9 5.8% × 55% × (1 − 27.7%) + 16.0% × 45% = 9.5%. The tax rate of 27.7% is a combined federal-state tax rate, where
state taxes are deductible for federal taxes (= 8.5% + (1 − 8.5%) × 21%). Note that the ATWACC applied to the
four CONE Areas varies slightly with applicable state income tax rates, as discussed in later sections.
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 7

---

## [page 12]

Quadrennial Review primarily because of an increase in interest rates. Table ES-1 below shows
the resulting 2028/29 CONE estimates for all three technologies and all five CONE Areas.
TABLE ES-1: CONE ESTIMATES
(NOMINAL$ FOR JUNE 2028 ONLINE YEAR)
Overnight Capital Year 1 Capital Levelized Gross CONE
CONE Area Technology
Capital Cost Charge Rate Recovery Fixed O&M ICAP
[A] [B] [C] [D] [E]
Nominal$ for 2028 Online Year $/kW %/year $/MW-day $/MW-day $/MW-day
Gas CT $1,395 16.0% $611 $59 $670
1. EMAAC Gas CC $1,517 17.0% $705 $112 $816
BESS 4-hr $1,832 9.6% $483 $197 $680
Gas CT $1,339 15.9% $585 $91 $676
2. SWMAAC Gas CC $1,411 16.9% $653 $166 $819
BESS 4-hr $1,753 9.6% $463 $208 $671
Gas CT $1,361 15.9% $593 $69 $663
3. Rest of RTO Gas CC $1,419 16.9% $656 $157 $813
BESS 4-hr $1,750 9.6% $462 $191 $652
Gas CT $1,390 15.9% $606 $58 $664
4. WMAAC Gas CC $1,476 16.9% $682 $132 $814
BESS 4-hr $1,784 9.6% $471 $196 $667
Gas CT $1,495 17.8% $730 $58 $789
5. COMED Gas CC $1,649 18.8% $849 $105 $953
BESS 4-hr $1,980 9.6% $521 $204 $726
Sources and Notes:
[A], [B], [D]: Outputs from CONE Model.
[C]: [A] x [B] x (1000 / 365).
[E]: [C] + [D].
Focusing on representative CONE Area 3, the Gross CONE estimates for CCs and CTs exceed those
from the 2022 Quadrennial Review by 44% and 47% respectively in real terms. The CC CONE from
the prior Review was $566/MW-day ICAP in 2028 dollars. Higher equipment costs net of greater
economies of scale with the new GE 7HA.03 turbines added $80/MW-day; a higher capital charge
rate accounting for extended construction periods, higher cost of capital, and loss of bonus
depreciation added $140/MW-day; and higher fixed O&M that relates to capital costs and higher
firm gas transportation costs added $28/MW-day, for a total current CC CONE of $813/MW-day,
an increase of 44%. The CONE for CTs increased by 47% in real terms, a slightly higher percentage
due to the higher-cost combustion turbines with dual-fuel capability accounting for a larger share
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 8

---

## [page 13]

of capital costs but with a partial offsetting cost reduction since they avoid buying natural gas
under firm fuel arrangements. BESS CONE estimates are now 11% lower than in the 2022 Review,
primarily because the currently available 30% ITC more than offsets the higher cost of capital and
modest increase in capital costs which are predominately due to current tariffs.10 Yet BESS still
has higher Net CONE than the other technologies in most areas.
Estimating a current level-nominal value for Net CONE involves subtracting forward E&AS offsets
from the CONE estimates above. Forward E&AS offsets are currently substantially above
historical levels, presumably due to the impact of much tighter reserve margins on spark spreads.
The results are reported in Table ES-2 below. Overall, these Level-Nominal Net CONE estimates
provide a somewhat higher-end estimate of the likely long-run marginal cost of supply,
considering that they incorporate temporary cost premiums and extended construction timelines
that will moderate over time and potentially toward the end of the Review period.
Concept 2: Long-Run Net CONE Estimates
More normalized long-run costs can be derived from the 2022 CONE Study, prior to current
turbine scarcity. We thus assume 2022-vintage costs per kW for major equipment and other EPC
costs, adjusted for inflation; and update the non-EPC costs and cost of capital to the same as in
our current level-nominal calculations above to arrive at “long-term CONE” estimates. For
indicative E&AS Offsets, we show the same current forward values as above (“Forward E&AS”)
and, alternatively, a 10-year average of E&AS revenues (“10-yr Average E&AS”). The forward
approach likely overstates long-term E&AS and the 10-yr average approach likely understates
long-term E&AS, so we consider both.
Another indicator of long-run Net CONE can be derived from clearing prices that sufficed to
attract new generation in the past, often referred to as empirical Net CONE. For the delivery
periods 2014/15 to 2022/23, when plentiful new generation (almost entirely CCs) entered, we
derived a comparable estimate of empirical Net CONE by averaging the historical clearing prices,
adjusted for inflation, increasing the cost of capital to current conditions, and adjusting to
account for the current accreditation approach (i.e., multiplied by old UCAP ratings divided by
current ELCCs). The resulting “Adjusted Empirical Net CONE” is $241/MW-day in 2028 dollars.
This measure does not necessarily incorporate all factors that may affect current costs of building
new supply, but it provides a useful benchmark to inform what supply costs might be after
removing the temporary pricing premiums affecting supply entry. Overall, we interpret these
10 BESS capital costs have actually decreased substantially since the 2022 PJM CONE Study but are slightly higher
when including prevailing tariffs for batteries.
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 9

---

## [page 43]

TABLE 11: CAPITAL COSTS FOR A CT
(NOMINAL$ FOR JUNE 2028 ONLINE YEAR)
Capital Costs (in $millions) Escalated Overnight Capital Costs: 06/2028
Units Nominal$ Nominal$ Nominal$ Nominal$ Nominal$
EMAAC SWMAAC Rest of RTO WMAAC COMED
Net Summer Capacity (MW) 392 395 387 383 393
OFE+ EPC Costs $438 $420 $421 $427 $473
Owner-Furnished Equipment (OFE)
Gas Turbines $159 $159 $159 $159 $159
SCR $53 $53 $53 $53 $53
Sales Tax $0 $0 $0 $0 $13
Engineering, Procurement, and Construction Costs (EPC)
Equipment
Other Equipment $34 $34 $34 $34 $34
Construction Labor $73 $60 $60 $65 $86
Other Labor $28 $27 $27 $28 $29
Materials $15 $15 $15 $15 $15
Sales Tax $0 $0 $0 $0 $2
EPC Contractor Fee $36 $35 $35 $35 $39
EPC Contingency $40 $38 $38 $39 $43
Non-EPC Costs $109 $108 $105 $105 $114
Project Development $22 $21 $21 $21 $24
Mobilization and Start-Up $4 $4 $4 $4 $5
Non-Fuel Inventories $2 $2 $2 $2 $2
Net Start-Up Fuel Costs -$1 $0 -$2 -$3 $1
Electrical Interconnection $22 $22 $22 $22 $22
Gas Interconnection $35 $35 $35 $35 $35
Land $1 $1 $0 $1 $1
Fuel Inventories $4 $4 $4 $4 $4
Owner's Contingency $7 $7 $7 $7 $8
Financing Fees $12 $11 $11 $11 $13
Total Overnight Capital Costs $547 $528 $526 $532 $587
Overnight Capital Costs ($/kW) $1,395 $1,339 $1,361 $1,390 $1,495
Installed Cost ($/kW) $1,715 $1,647 $1,674 $1,710 $1,837
Sources and Notes: Net start-up costs in ComEd and land costs in Rest of RTO are non-zero but less than $500,000.
1. OFE and EPC Costs
a. Project Developer and Contract Arrangements
The scope of an EPC contract typically includes handling, storage, and installation of the OFE
(including the gas turbines and major equipment), balance-of-plant engineering, procurement of
other equipment, construction, commissioning, and delivery of a fully operational facility to meet
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 39

---

## [page 44]

certain performance guarantees. The contracting scheme for procuring professional EPC services
in the US is typically implemented with a single contractor at a single, fixed, lump-sum price. A
single contract reduces the owner’s responsibility with construction coordination and reduces
the potential for missed or duplicated scope compared to multiple contract schemes. The
estimates and contractor fees herein reflect this contracting scheme.
b. Equipment, Materials, and Sales Tax
OFE is typically purchased by the plant owner through the EPC contractor. The owner and EPC
contractor typically sign a fixed-price contract with equipment manufacturers early in the
development process, effectively locking in the price of OFE and other equipment. The OFE costs
shown reflect the total equipment cost including freight to site. Additional related costs including
EPC handling costs, on-site storage and protection, equipment installation, and commissioning
are included in the EPC’s construction labor and other labor cost components. Due to the current
tight market for turbines, combustion turbine costs which now represent 30% of total incurred
overnight capital costs, have increased from $225/kW to $409/kW in 2025 dollars, or by 81% in
real terms, since the 2022 PJM CONE Study. The rate of change has been rapid in these tight
conditions. Since August 2024 alone, turbine costs have increased by 37% in real terms, from
$298/kW to $409/kW in 2025 dollars.37
Materials include all construction materials associated with the EPC scope of work, material
freight costs, and consumables during construction. This includes commodity-type materials such
as concrete, formwork, rebar, wiring, cabling, raceways, instrumentation, steel, piping, fittings,
specialties, and small valves. Material costs were estimated using S&L proprietary data, vendor
catalogs, and publications. Estimates for the quantity of materials needed to construct simple-
and combined-cycle plants are based on S&L’s experience with similarly sized and configured
facilities.
Other Equipment includes inside-the-fence balance-of-plant equipment required for
interconnection and associated spare parts and special tools. This equipment includes (as
applicable) air cooled condensers, auxiliary boilers, fuel gas conditioning equipment, pumps,
fans, heat exchangers, compressors, tanks, water treatment systems, fire protection systems,
37 Based on costs in CONE Area 3. Current costs are expressed pre-escalation, in 2025$. 2022 PJM CONE Affidavit
turbine costs of $232/kW in 2026$ were deflated from June 2026 to January 2025 using the long-term inflation
rate assumed in the 2022 PJM CONE Study. August 2024 comparison is based on preliminary CONE estimates
published in November 2024, which were derived from S&L cost estimates as of August 2024. See Newell et. al.,
Sixth Review of PJM’s RPM VRR Curve Parameters Preliminary Gross CONE and E&AS Methodology, November
26, 2024.
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 40

---

## [page 56]

TABLE 15: CAPITAL COSTS FOR A CC
(NOMINAL$ FOR JUNE 2028 ONLINE YEAR)
Capital Costs (in $millions) Escalated Overnight Capital Costs: 06/2028
Units Nominal$ Nominal$ Nominal$ Nominal$ Nominal$
EMAAC SWMAAC Rest of RTO WMAAC COMED
Net Summer Capacity (MW) 1,289 1,289 1,276 1,264 1,294
OFE + EPC Costs $1,684 $1,555 $1,556 $1,608 $1,831
Owner-Furnished Equipment (OFE)
Gas Turbines $296 $296 $296 $296 $296
HRSG / SCR $120 $120 $120 $120 $120
Steam Turbines $126 $126 $126 $126 $126
Sales Tax $0 $0 $0 $0 $34
Engineering, Procurement, and Construction (EPC) Costs
Equipment
Condenser $72 $72 $72 $72 $72
Other Equipment $104 $104 $104 $104 $104
Construction Labor $497 $395 $396 $437 $570
Other Labor $75 $70 $70 $72 $78
Materials $102 $102 $102 $102 $102
Sales Tax $0 $0 $0 $0 $11
EPC Contractor Fee $139 $128 $129 $133 $151
EPC Contingency $153 $141 $141 $146 $166
Non-EPC Costs $273 $265 $255 $256 $302
Project Development $84 $78 $78 $80 $92
Mobilization and Start-Up $17 $16 $16 $16 $18
Non-Fuel Inventories $8 $8 $8 $8 $9
Emission Reduction Credits $2 $2 $2 $2 $2
Net Start-Up Fuel Costs -$25 -$21 -$26 -$31 -$12
Electrical Interconnection $72 $72 $71 $70 $72
Gas Interconnection $49 $49 $49 $49 $49
Land $6 $6 $3 $6 $7
Owner's Contingency $17 $17 $16 $16 $19
Financing Fees $42 $39 $39 $40 $46
Total Overnight Capital Costs $1,956 $1,820 $1,811 $1,864 $2,133
Overnight Capital Costs ($/kW) $1,517 $1,411 $1,419 $1,476 $1,649
Installed Cost ($/kW) $1,929 $1,795 $1,806 $1,877 $2,096
The following capital costs were estimated for the CC:
OFE AND EPC COSTS
• OFE: Estimated using the same method as for the CT described in Section IV.B.1. Due to the
tight market for turbines and other major equipment paired with the current high-demand
environment for dispatchable power, turbine costs, which now represent 16% of total
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 52

---

## [page 66]

Based on the technical specifications for the BESS described above, the total capital costs for
plants with an online date of June 1, 2028 are shown in Table 19. Comparisons to costs from the
2022 PJM CONE Study are expressed in 2025 dollars to align them with the basis of our initial cost
estimates. All costs presented in this section are expressed in ICAP terms unless specified
otherwise.
TABLE 19: CAPITAL COSTS FOR A BESS
(NOMINAL$ FOR JUNE 2028 ONLINE YEAR)
Capital Costs (in $millions) Escalated Overnight Capital Costs: 06/2028
Units Nominal$ Nominal$ Nominal$ Nominal$ Nominal$
CONE Area EMAAC SWMAAC Rest of RTO WMAAC COMED
Net Summer Capacity (MW) 200 200 200 200 200
Engineering, Procurement and Construction (EPC) $321 $306 $306 $312 $348
BESS Equipment
Batteries and Enclosures $181 $181 $181 $181 $181
PCS and BOP Equipment $51 $51 $51 $51 $51
Project Management $13 $12 $12 $13 $13
Construction & Materials $76 $61 $62 $67 $88
Sales Tax $0 $0 $0 $0 $15
Non-EPC Costs $46 $45 $44 $45 $48
Project Development $16 $15 $15 $16 $17
Mobilization and Start-Up $3 $3 $3 $3 $3
Owner's Contingency $12 $12 $12 $12 $12
Land $1 $1 $1 $1 $2
Electrical Interconnection $12 $12 $12 $12 $12
Financing Fees $2 $2 $2 $2 $2
Total Overnight Capital Costs $366 $351 $350 $357 $396
Overnight Capital Costs ($/kW) $1,832 $1,753 $1,750 $1,784 $1,980
Installed Cost ($/kW) $1,987 $1,901 $1,898 $1,935 $2,146
The following capital costs were estimated for the BESS:
EPC COSTS
• Batteries and Enclosures: This is the largest share of plant costs at 52% of overnight costs.
Cost estimates are derived from S&L’s detailed data on numerous current projects under
development and corroborated through interviews with battery developers and integrators
to ensure that estimated costs are accurate and up-to-date.
Batteries and enclosures are generally imported from China and are therefore subject to
tariffs, but more limited domestic substitutes tend not to cost any less. The costs reported in
this study assume a 48.4% total tariff comprised of a 25% Section 301 tariff, a 3.4% duty, and
a 20% tariff from the current administration before the further increases ordered on April 2,
BRATTLE 2025 CONE REPORT FOR PJM Brattle.com | 62
