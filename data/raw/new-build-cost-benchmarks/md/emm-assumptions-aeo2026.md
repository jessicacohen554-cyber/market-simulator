# EMM_Assumptions_AEO2026 — full text extraction

Converted from PDF via pdfplumber for QA/QC. Page markers preserve source pagination.


---

## [page 1]

Assumptions to the Annual
Energy Outlook 2026:
Electricity Market Module
April 2026
www.eia.gov
U.S. Department of Energy
Washington, DC 20585

---

## [page 2]

The U.S. Energy Information Administration (EIA), the statistical and analytical agency within the
U.S. Department of Energy (DOE), prepared this report. By law, our data, analyses, and forecasts are
independent of approval by any other officer or employee of the U.S. Government. The views in this
report do not represent those of DOE or any other federal agencies.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module i

---

## [page 3]

April 2026
Table of Contents
Overview ....................................................................................................................................................... 1
Regions..................................................................................................................................................... 1
Key Assumptions ........................................................................................................................................... 3
Generating capacity types ....................................................................................................................... 3
New electric-generating plant characteristics ......................................................................................... 4
New construction financing ..................................................................................................................... 9
Technological optimism and learning .................................................................................................... 10
International learning ............................................................................................................................ 13
Distributed generation .......................................................................................................................... 13
Demand storage .................................................................................................................................... 13
Coal-to-gas conversion .......................................................................................................................... 14
Representing electricity demand ........................................................................................................... 15
Intermittent and storage modeling ....................................................................................................... 16
Capacity and operating reserves ........................................................................................................... 16
Variable heat rates for coal-fired power plants .................................................................................... 17
Endogenous plant retirement modeling ............................................................................................... 17
Biomass co-firing ................................................................................................................................... 19
Nuclear uprates ..................................................................................................................................... 19
Interregional electricity trade ................................................................................................................ 19
International electricity trade ................................................................................................................ 20
Electricity pricing ................................................................................................................................... 20
Fuel price expectations .......................................................................................................................... 21
Nuclear fuel prices ................................................................................................................................. 22
Legislation and Regulations ........................................................................................................................ 22
Cross-State Air Pollution Rule and Clean Air Act Amendments of 1990 ............................................... 22
Heat rate improvement retrofits ........................................................................................................... 25
Mercury regulation ................................................................................................................................ 27
Power plant mercury emissions assumptions ....................................................................................... 28
Tax credit for carbon oxide sequestration ............................................................................................. 29
Carbon capture and sequestration retrofits .......................................................................................... 29
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module ii

---

## [page 4]

April 2026
State air emissions regulations .............................................................................................................. 30
State and federal revenue support for existing nuclear power plants .................................................. 31
Federal tax credits for new construction ............................................................................................... 32
Notes and Sources ...................................................................................................................................... 33
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module iii

---

## [page 5]

April 2026
Table of Figures
Figure 1. Electricity Market Module regions ................................................................................................. 1
Figure 2. Cross-State Air Pollution Rule ...................................................................................................... 23
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module iv

---

## [page 6]

April 2026
Table of Tables
Table 1. National Energy Modeling System’s Electricity Market Module regions ........................................ 2
Table 2. Generating capacity types represented in the Electricity Market Module ..................................... 3
Table 3. Cost and performance characteristics of new central station electricity generating technologies 6
Table 4. Total overnight capital costs of new electricity generating technologies by region ...................... 7
Table 5. Learning parameters for new generating technology components ............................................. 10
Table 6. Component cost weights for new technologies ............................................................................ 12
Table 7. Component capacity weights for new technologies ..................................................................... 13
Table 8. Coal plant retrofit costs ................................................................................................................. 24
Table 9. Existing pulverized-coal plant types in the National Energy Modeling System’s Electricity Market
Module ........................................................................................................................................................ 26
Table 10. Heat rate improvement (HRI) potential and cost (capital as well as fixed operations and
maintenance) by plant type and quartile as used for input into the National Energy Modeling System .. 27
Table 11. Mercury emission modification factors ...................................................................................... 29
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module v

---

## [page 7]

April 2026
Overview
The Electricity Market Module (EMM) in the National Energy Modeling System (NEMS) is made up of four
primary submodules: electricity load and demand, electricity capacity planning, electricity fuel dispatching,
and electricity finance and pricing. EMM also includes the ReStore Submodule, which interfaces with both
the renewable and electricity modules, and represents nonutility capacity and generation as well as
electricity transmission and trade. Our publication, The Electricity Market Module of the National Energy
Modeling System: Model Documentation 2025, describes the EMM further.
Based on fuel prices and electricity demands that other NEMS modules provide, the EMM determines the
most economical way to supply electricity within environmental and operational constraints. Each EMM
submodule includes assumptions about the operations of the electric power sector and the costs of various
options. This document describes the model parameters and assumptions used in the EMM and discusses
legislation and regulations that we incorporate in the EMM.
Regions
We use 25 electricity supply regions to represent U.S. power markets. The regions follow North American
Electric Reliability Corporation (NERC) assessment region boundaries and independent system operator
(ISO) and regional transmission organization (RTO) region boundaries (as of early 2019). Subregions are
based on regional pricing zones (Figure 1 and Table 1).
Figure 1. Electricity Market Module regions
Source: U.S. Energy Information Administration
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 1

---

## [page 8]

April 2026
Table 1. National Energy Modeling System’s Electricity Market Module regions
Number Abbreviation NERC/ISOa subregion name Geographic nameb
1 TRE Texas Reliability Entity Texas
2 FRCC Florida Reliability Coordinating Council Florida
3 MISW Midcontinent ISO/West Upper Mississippi Valley
4 MISC Midcontinent ISO/Central Middle Mississippi Valley
5 MISE Midcontinent ISO/East Michigan
6 MISS Midcontinent ISO/South Mississippi Delta
7 ISNE Northeast Power Coordinating Council/ New England New England
8 NYCW Northeast Power Coordinating Council/ New York City & Long Island Metropolitan New York
9 NYUP Northeast Power Coordinating Council/Upstate New York Upstate New York
10 PJME PJM/East Mid-Atlantic
11 PJMW PJM/West Ohio Valley
12 PJMC PJM/Commonwealth Edison Metropolitan Chicago
13 PJMD PJM/Dominion Virginia
14 SRCA SERC Reliability Corporation/East Carolinas
15 SRSE SERC Reliability Corporation/Southeast Southeast
16 SRCE SERC Reliability Corporation/Central Tennessee Valley
17 SPPS Southwest Power Pool/South Southern Great Plains
18 SPPC Southwest Power Pool/Central Central Great Plains
19 SPPN Southwest Power Pool/North Northern Great Plains
20 SRSG Western Electricity Coordinating Council/Southwest Southwest
21 CANO Western Electricity Coordinating Council/California North Northern California
22 CASO Western Electricity Coordinating Council/California South Southern California
23 NWPP Western Electricity Coordinating Council/Northwest Power Pool Northwest
24 RMRG Western Electricity Coordinating Council/Rockies Rockies
25 BASN Western Electricity Coordinating Council/Basin Great Basin
Data source: U.S. Energy Information Administration
a NERC=North American Electric Reliability Corporation; ISO=independent system operator
b Names are intended to describe approximate locations. Exact regional boundaries do not necessarily correspond to state borders
or to other regional naming conventions.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 2

---

## [page 9]

April 2026
Key Assumptions
Generating capacity types
The EMM considers many capacity types for electricity generation (Table 2).
Table 2. Generating capacity types represented in the Electricity Market Module
Capacity type
Existing coal steam plantsa
Ultra-supercritical coal (USC)b
USC with 30% carbon capture and sequestration (CCS)
USC with 95% CCS
Oil or natural gas steam—oil or natural gas steam turbine
Combined-cycle (CC)—single-shaft (1x1x1)c configuration
Combined-cycle—multi-shaft (2x2x1)d configuration
Combined-cycle with CCS—single-shaft configuration with 95% CCS
Combustion turbine (CT)—aeroderivative
CT—industrial frame
Fuel cell—solid oxide
Hydrogen turbinee
Conventional nuclear
Advanced nuclear—advanced light water reactor
Advanced nuclear small modular reactor
—
Conventional hydropower—hydraulic turbine
Pumped storage—hydraulic turbine reversible
Battery storage—four-hour lithium-ion battery
Geothermal
Municipal solid waste (MSW)—landfill gas-fired internal combustion engine
Biomass—fluidized bed
Biomass with 95% CCS
Solar thermalf
Solar photovoltaic (PV) with single-axis tracking
Solar PV with battery storageg
Wind
Wind offshore
Data source: U.S. Energy Information Administration
a The Electricity Market Module represents 32 types of existing coal steam plants based on the different
possible configurations of nitrogen oxide, particulate, and sulfur dioxide emission control devices as well as
options for controlling mercury and carbon (Table 9).
b AEO2026 assumes new coal plants without CCS cannot be built because of emission standards for new
plants that were in effect as of December 2025. These technologies exist in the modeling framework, but
they are assumed to be unavailable to be built in the projections except in cases using Alternative Electricity
assumptions.
c Single-shaft (1x1x1) configuration with one H-class combustion turbine, one heat recovery steam
generator, and one steam turbine generator.
d Multi-shaft (2x2x1) configuration with two H-class combustion turbines, two heat recovery steam
generators, and one steam turbine generator.
e Hydrogen turbine modeled after an industrial frame CT, as modified to burn 100% hydrogen.
f Existing solar thermal plants are represented in the module but are not assumed as a new technology
option.
g Includes 150 megawatts (MW) of PV and 50 MW of four-hour battery storage coupled through a direct
current bus and connected to the grid through a 150-MW inverter.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 3

---

## [page 10]

April 2026
New electric-generating plant characteristics
The inputs to the Electricity Capacity Planning Submodule are the cost and performance characteristics of
new generating technologies (Table 3). In addition to these characteristics, we use fuel prices from the
NEMS fuel supply modules and expectations for future fuel prices to compare options when new capacity is
needed. We assume heat rates for new fossil-fueled technologies remain constant throughout the
projection period.
We base initial cost inputs for new technologies on cost estimates developed by a 2024 report prepared by
Sargent & Lundy, adjusted for learning cost adjustments for any capacity added since 2023 (Table 3).1 This
report uses a consistent estimation methodology across all technologies to develop cost and performance
characteristics for technologies that we consider in the EMM. We do not use the costs that the consultant
developed for geothermal and hydro plants; instead, we use previously developed site-specific costs.
We reviewed and updated input costs for the combined-cycle and turbine technologies for AEO2026 based
primarily on a study by the Brattle Group and Sargent & Lundy for the PJM Interconnection’s cost for new
entry analysis.2 This study found that the costs for new natural gas-fired plants have increased significantly
in recent years due to supply shortages and tight markets for both materials and labor for combustion
turbines. The change by component cost was estimated and applied to the original cost inputs from the
2024 report, resulting in about a 40% increase in simple-cycle turbine costs and a 20% increase in combined-
cycle plant costs. Hydrogen turbine costs were also adjusted, as they are assumed to be consistent with the
natural gas-fired turbine technology.
Except as noted below, the overnight costs represent the estimated cost of building a plant before adjusting
for regional cost factors (Table 3). Overnight costs exclude interest expenses during plant construction and
development. The base overnight costs include project contingencies to account for undefined project
scope, pricing uncertainty, and owners’ cost components. Technologies with limited commercial experience
may include a technological optimism factor to account for the tendency during technology research and
development to underestimate the full engineering and development costs for new technologies. A cost-
adjustment factor, based on the producer price index for metals and metal products, allows the overnight
capital costs in the future to drop if this index decreases or to rise if it increases. The base year for this
commodity cost index is consistent with the base year of the cost estimates, so the initial cost estimate for
AEO2026 also reflects changes in the commodity index between 2023 and 2025.
All technologies demonstrate some degree of variability in cost, based on project size, location, and access
to key infrastructure (such as grid interconnections, fuel supply, and transportation). For onshore wind and
solar photovoltaic (PV) energy sources, in particular, the cost favorability of the lowest-cost regions
compounds the underlying variability in regional cost and creates a significant differential between the
unadjusted costs, the average regional costs, and the capacity-weighted average national costs as observed
from recent market experience. To reflect this difference, we report the weighted-average cost for both
onshore wind and solar PV based on the regional cost factors assumed for these technologies in AEO2026
and the actual regional distribution of wind and solar builds that occurred in 2024 (Table 3).
Table 4 lists the overnight capital costs for each technology and EMM region for the resources or
technologies that are available to be built in each region (Figure 1). The regional costs reflect the impact of
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 4

---

## [page 11]

April 2026
locality adjustments, including one to address ambient air conditions for technologies that include a
combustion turbine and one to adjust for additional costs associated with accessing remote wind and solar
resources. Temperature, humidity, and air pressure can affect the available capacity of a combustion
turbine, and our modeling addresses this possibility through an additional cost multiplier by region. Unlike
most other generation technologies where fuel can be transported to the plant, wind and solar generators
are located in areas with the best resources. Sites that are located near existing transmission with access to
a road network or are otherwise located on lower development-cost lands are generally built up first, after
which additional costs may be incurred to access sites with less favorable characteristics. We represent this
trend through a multiplier applied to the wind and solar plant capital costs that increases as the best sites in
a given region are developed.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 5

---

## [page 12]

April 2026
Table 3. Cost and performance characteristics of new central station electricity generating technologies
Base
overnight Techno- Total Variable
First Lead costb logical overnight O&Mf Fixed O&M
available Size time (2025$/ optimism costd,e (2025$/ (2025$/ Heat rateg
Technology yeara (MW) (years) kW) factorc (2025$/kW) MWh) kWy) (Btu/kWh)
USC with 30% carbon capture and sequestration (CCS) 2030 650 5 $5,360 1.03 $5,520 $8.68 $49.80 9,751
USC with 95% CCS 2030 650 5 $7,400 1.05 $7,770 $14.36 $90.70 12,293
Combined-cycle—single-shaft 2028 627 3 $1,086 1.00 $1,086 $3.49 $16.23 6,226
Combined-cycle—multi-shaft 2028 1,227 3 $1,032 1.00 $1,032 $3.57 $12.69 6,226
Combined-cycle with 95% CCS 2029 543 4 $2,567 1.10 $2,824 $5.29 $25.93 7,239
Combustion turbine—aeroderivativeh 2027 211 2 $2,275 1.00 $2,275 $5.97 $9.99 9,447
Combustion turbine—industrial frame 2027 419 2 $1,158 1.00 $1,158 $4.17 $7.18 9,142
Fuel cells 2028 10 3 $7,818 1.06 $8,287 $0.72 $37.77 6,469
Hydrogen turbine 2027 237 2 $1,215 1.00 $1,215 $5.52 $8.59 8,295
Nuclear—light water reactor 2031 2,156 6 $7,862 1.05 $8,255 $2.62 $163.40 10,445
Nuclear—small modular reactor 2031 480 6 $8,937 1.10 $9,831 $3.32 $127.62 10,445
Battery storagei 2026 150 1 $1,521 1.00 $1,521 $0.00 $41.84 NA
Biomass 2030 50 5 $4,843 1.00 $4,843 $5.93 $154.26 13,300
Biomass with 95% CCS 2030 50 5 $12,631 1.08 $13,642 $10.09 $273.21 19,965
Geothermali, j 2029 50 4 $3,282 1.00 $3,282 $0.00 $167.86 3,412
Conventional hydropoweri,j 2029 100 4 $3,280 1.00 $3,280 $1.71 $51.30 3,412
Winde 2028 200 3 $1,712 1.00 $1,712 $0.00 $34.57 3,412
Wind offshorei 2029 900 4 $3,711 1.00 $3,711 $0.00 $161.09 3,412
Solar photovoltaic (PV) with trackinge,k 2027 150 2 $1,484 1.00 $1,484 $0.00 $23.60 3,412
Solar PV with storage k 2027 150 2 $1,903 1.00 $1,903 $0.00 $40.00 3,412
Data source: Sargent & Lundy, Cost and Performance Estimates for New Utility-Scale Electric Power Generating Technologies, January 2024; Hydroelectric: Oak Ridge National Lab, An Assessment
of Energy Potential at Non-Powered Dams in the United States, 2012, and Idaho National Engineering and Environmental Laboratory, Estimation of Economic Parameters of U.S. Hydropower
Resources, 2003; Geothermal: National Renewable Energy Laboratory, Updated U.S. Geothermal Supply Curve, 2010
Note: MW=megawatt; kW=kilowatt; MWh=megawatthour; kWy=kilowattyear; kWh=kilowatthour; Btu=British thermal unit
a The first year that a new unit could become operational.
b Base cost includes project contingency costs.
c We apply the technological optimism factor to the first four units of a new, unproven design; it reflects the demonstrated tendency to underestimate actual costs for a first-of-a-kind unit.
d Overnight capital cost includes contingency factors and excludes regional multipliers (except as noted for wind and solar PV) and learning effects. Interest charges are also excluded. The capital
costs represent current costs for plants that would come online in 2026.
e Total overnight cost for wind and solar PV technologies in the table are the average total cost across all 25 electricity market regions, as weighted by the respective capacity of that type installed
during 2024 in each region to account for the substantial regional variation in wind and solar costs (Table 4). The input value used for onshore wind in AEO2026 is $1,502/kW, and for solar PV with
tracking, it is $1,396/kW, which represents the cost of building a plant excluding regional factors. Region-specific factors contributing to the substantial regional variation in cost include
differences in typical project size across regions, accessibility of resources, and variation in labor and other construction costs throughout the country.
f O&M=operations and maintenance
g The nuclear average heat rate is the weighted average tested heat rate for nuclear units as reported on the Form EIA-860, Annual Electric Generator Report. No heat rate is reported for battery
storage because it is not a primary conversion technology; conversion losses are accounted for when the electricity is first generated, and electricity-to-storage losses of 15% are accounted for
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 6

---

## [page 13]

April 2026
through the additional demand for electricity required to meet load. For hydropower, wind, solar, and geothermal technologies, the heat content of electricity (3,412 Btu/kWh) is used to calculate
primary energy consumption from the generation of these resources.
h Combustion turbine aeroderivative units can be built by the module before 2027, if necessary, to meet a region's reserve margin.
i Capital costs are shown before investment tax credits are applied.
j Because geothermal and hydropower cost and performance characteristics are specific for each site, the table entries show the cost of the least expensive plant that could be built in the
Northwest region for hydro and the Great Basin region for geothermal, where most of the proposed sites are located.
k Costs and capacities are expressed in terms of net AC (alternating current) power available to the grid for the installed capacity.
Table 4. Total overnight capital costs of new electricity generating technologies by region
2025 dollars per kilowatt
Technology 1 TRE 2 FRCC 3 MISW 4 MISC 5 MISE 6 MISS 7 ISNE 8 NYCW 9 NYUP 10 PJME 11 PJMW 12 PJMC 13 PJMD
USC with 30% CCS $5,175 $5,312 $5,735 $5,890 $5,937 $5,382 $6,334 NA $6,207 $6,374 $5,519 $6,874 $5,933
USC with 95% CCS $7,014 $7,326 $8,226 $8,339 $8,260 $7,660 $8,868 NA $8,388 $8,919 $7,730 $10,520 $7,919
CC—single-shaft $980 $1,007 $1,122 $1,108 $1,124 $1,036 $1,194 $1,513 $1,150 $1,196 $1,055 $1,325 $1,098
CC—multi-shaft $930 $957 $1,065 $1,057 $1,069 $988 $1,139 $1,445 $1,094 $1,138 $1,002 $1,262 $1,044
CC with 95% CCS $2,504 $2,591 $2,943 $2,898 $2,949 $2,676 $3,154 $5,674 $3,022 $3,173 $2,739 $3,586 $2,860
CT—aeroderivative $2,058 $2,096 $2,365 $2,323 $2,361 $2,176 $2,495 $2,946 $2,414 $2,456 $2,226 $2,671 $2,294
CT—industrial frame $1,033 $1,058 $1,212 $1,188 $1,210 $1,101 $1,287 $1,585 $1,240 $1,272 $1,131 $1,408 $1,170
Fuel cells $7,953 $8,076 $8,445 $8,810 $8,642 $8,301 $8,965 $10,555 $8,601 $8,888 $8,189 $9,586 $8,441
Hydrogen turbine $1,084 $1,110 $1,272 $1,248 $1,271 $1,156 $1,351 $1,664 $1,301 $1,335 $1,187 $1,479 $1,228
Nuclear—light water $7,866 $8,055 $8,344 $8,971 $8,518 $8,625 $9,165 NA $8,575 $8,898 $8,195 $9,792 $8,366
reactor
Nuclear—small modular $9,366 $9,568 $10,059 $10,334 $10,136 $9,922 $10,615 NA $10,189 $10,541 $9,785 $11,568 $9,913
reactor
Battery storage $1,500 $1,512 $1,519 $1,589 $1,535 $1,570 $1,593 $1,698 $1,550 $1,565 $1,513 $1,626 $1,538
Biomass $4,493 $4,616 $4,997 $5,163 $5,174 $4,683 $5,749 $7,804 $5,768 $5,869 $4,935 $5,962 $5,624
Biomass with 95% CCS $12,344 $12,832 $14,306 $14,447 $14,342 $13,295 $15,155 NA $14,569 $15,536 $13,481 $17,616 $13,976
Geothermal NA NA NA NA NA NA NA NA NA NA NA NA NA
Conventional hydropower $4,786 $5,847 $2,326 $1,546 $3,148 $4,658 $2,155 NA $4,410 $4,580 $3,992 NA $4,052
Wind $1,562 NA $1,693 $1,592 $1,704 $1,516 $2,205 $2,383 $2,445 $2,203 $1,633 $2,261 $2,378
Wind offshore $3,526 $4,057 $3,895 NA $3,818 NA $4,072 $4,886 $3,894 $4,021 $3,655 $4,419 $3,775
Solar PV with tracking $1,342 $1,364 $1,426 $1,430 $1,428 $1,385 $1,466 $1,885 $1,579 $1,623 $1,738 $1,583 $1,754
Solar PV with storage $1,840 $1,867 $1,931 $1,959 $1,940 $1,908 $1,999 $2,510 $2,144 $2,197 $2,369 $2,123 $2,391
Technology 14 SRCA 15 SRSE 16 SRCE 17 SPPS 18 SPPC 19 SPPN 20 SRSG 21 CANO 22 CASO 23 NWPP 24 RMRG 25 BASN Average
USC with 30% CCS $5,337 $5,359 $5,481 $5,559 $5,662 $5,416 $5,649 NA NA $5,937 $5,589 $5,800 $5,748
USC with 95% CCS $7,548 $7,588 $7,796 $7,361 $8,002 $7,697 $8,019 NA NA $8,585 $7,664 $8,294 $8,078
CC—single-shaft $1,011 $1,020 $1,050 $1,003 $1,064 $1,012 $952 $1,280 $1,252 $1,123 $875 $1,003 $1,102
CC—multi-shaft $965 $970 $1,001 $952 $1,011 $960 $905 $1,224 $1,196 $1,071 $830 $956 $1,049
CC with 95% CCS $2,604 $2,637 $2,722 $2,585 $2,773 $2,625 $2,477 $3,450 $3,356 $2,959 $2,268 $2,624 $2,954
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 7

---

## [page 14]

April 2026
CT—aeroderivative $2,143 $2,144 $2,215 $2,115 $2,225 $2,152 $1,966 $2,561 $2,515 $2,350 $1,864 $2,091 $2,289
CT— industrial frame $1,082 $1,086 $1,124 $1,069 $1,135 $1,093 $1,002 $1,345 $1,315 $1,209 $946 $1,070 $1,175
Fuel cells $8,299 $8,188 $8,379 $8,287 $8,461 $8,195 $8,309 $9,520 $9,410 $8,701 $8,149 $8,680 $8,641
Hydrogen turbine $1,136 $1,140 $1,180 $1,122 $1,191 $1,147 $1,052 $1,412 $1,381 $1,269 $993 $1,123 $1,233
Nuclear—light water $8,600 $8,295 $8,630 $7,994 $8,379 $8,090 $8,532 NA NA $8,970 $8,086 $8,894 $8,538
reactor
Nuclear—small modular $9,867 $9,768 $9,981 $9,560 $9,975 $9,739 $10,028 NA NA $10,432 $9,713 $10,288 $10,061
reactor
Battery storage $1,570 $1,531 $1,564 $1,504 $1,529 $1,503 $1,540 $1,646 $1,650 $1,581 $1,503 $1,580 $1,560
Biomass $4,658 $4,669 $4,768 $4,829 $4,967 $4,773 $5,112 $6,549 $6,401 $5,286 $5,065 $5,064 $5,319
Biomass with 95% CCS $13,073 $13,180 $13,519 $12,925 $13,995 $13,510 $13,817 $17,165 $16,777 $14,862 $13,400 $14,292 $14,267
Geothermal NA NA NA NA NA NA $3,345 $3,317 $2,685 $3,246 NA $3,282 $3,175
Conventional hydropower $2,256 $4,893 $2,529 $4,841 $2,040 $1,918 $3,889 $4,114 $3,961 $3,280 $3,917 $4,280 $3,627
Wind $1,877 $1,859 $1,520 $1,600 $1,670 $1,478 $1,894 $4,335 NA $1,986 $1,620 $1,737 $1,963
Wind offshore $3,754 NA NA NA NA NA NA $4,421 $4,390 $4,100 NA NA $4,046
Solar PV with tracking $1,378 $1,381 $1,395 $1,367 $1,409 $1,387 $1,548 $1,949 $1,920 $1,452 $1,385 $1,430 $1,520
Solar PV with storage $1,901 $1,891 $1,917 $1,867 $1,917 $1,887 $2,115 $2,642 $2,607 $1,980 $1,885 $1,958 $2,070
Data source: U.S. Energy Information Administration, Office of Long-Term Energy Modeling
Note: Costs include contingency factors, regional cost multipliers, and ambient condition multipliers. Interest charges are excluded. The costs are shown before investment tax credits are
applied.
NA=not available: the plant type cannot be built in the region because of a lack of resources, sites, or specific state legislation.
SC=ultra-supercritical; CCS=carbon capture and sequestration; CC=combined cycle; CT=combustion turbine; PV=photovoltaic
Electricity Market Module region map
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 8

---

## [page 15]

April 2026
New construction financing
The Electricity Capacity Planning Submodule of the EMM assumes that new power plants are built in a
competitive environment and that different generating technologies generally have the same financing
options available. We describe a few exceptions in this section. The EMM assumes projects are financed
by both debt and equity, and it uses the after-tax weighted average capital cost as the discount rate
when calculating the discounted cash flow analysis for building and operating new plants.
In the EMM, the corporate tax rate is set at 21%, and all new construction is immediately expensed
through a one-year depreciation schedule. This depreciation schedule was made permanent by the One
Big Beautiful Bill Act of 2025 (OBBBA) and affects both retail price calculations and costs of financing
new generation, transmission, and distribution builds.
The OBBBA made updates to existing tax credits (discussed later in this chapter) and introduced new
Foreign Entity of Concern (FEOC) rules for plants to be eligible for the tax credits. The rules require an
increasing share of key components be sourced from non-FEOC entities (for example, excluding China
and Russia). To reflect the uncertainty regarding tax credit eligibility for wind, solar, and battery storage
plants, a risk premium is added to the financing of affected projects during the time period that tax
credits are available. The risk premium is implemented as a three-percentage-point adder to the cost of
capital (both equity and debt) when evaluating the investment decision.
In the EMM, the assumed debt fraction for new builds is 60%, with a corresponding 40% equity fraction.
The EMM bases the cost of debt on the Industrial Baa bond rate, passed to the EMM as an annual
projection from the Macroeconomic Module. The cost of debt in AEO2026 averages 5.7% for capacity
builds from 2025 through 2050. The cost of equity is calculated using the Capital Asset Pricing Model
(CAPM), which assumes the return is equal to a risk-free rate plus a risk premium that is specific to the
industry (described in more detail in the EMM documentation). The average cost of equity in AEO2026 is
11.1%, and the resulting discount rate with a 60/40 debt/equity split is 7.1% from 2025 through 2050.
The AEO2026 includes a three-percentage-point adder to the cost of capital (both equity and debt)
when evaluating investments in new coal-fired power plants without full carbon capture and
sequestration (CCS) and in new natural gas-fired combined-cycle (NGCC) plants. We also apply the adder
to pollution control retrofits to reflect financial risks associated with major investments in long-lived
power plants with a relatively higher rate of CO emissions. Coal technology that captures 30% of CO
2 2
emissions is still considered a high emitter relative to other new sources and may continue to face
potential financial risk if carbon emission rules are further expanded. The only coal technology that does
not receive the three-percentage-point increase in cost of capital is the technology designed to capture
95% of CO emissions. The EMM includes the adder on NGCC plants as more state and federal incentives
2
are put in place to encourage low- or zero-carbon emitting technologies, making builds of new natural
gas-fired plants subject to increased risk of changing policies that could shorten their effective cost
recovery period. The adder is not applied to simple-cycle combustion turbine plants because those plant
types are most often built for reserve capacity and do not contribute as much to emissions.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 9

---

## [page 16]

April 2026
Technological optimism and learning
We calculate overnight costs for each technology as a function of regional construction parameters,
project contingencies, technological optimism, and learning factors.
The technological optimism factor represents the demonstrated tendency to underestimate actual costs
for a first-of-a-kind, unproven technology. As experience is gained, the technological optimism factor is
gradually reduced to 1.0.
NEMS determines the learning function at a component level. It breaks each new technology into major
components: revolutionary, evolutionary, or mature. We assume each component has different learning
rates, based on the experience with the design component (Table 5). If technologies use similar
components, these components learn at the same rate that these units are built. For example, we
assume the underlying turbine generators are basically the same for a combustion turbine, combined-
cycle, and integrated coal-gasification combined-cycle unit. Therefore, construction of any of these
technologies would contribute to learning cost reductions for the turbine component.
Table 5. Learning parameters for new generating technology components
Period 1 Period 2 Period 3
learning learning learning
rate rate rate Period 1 Period 2 Annual minimum
Technology component (LR1) (LR2) (LR3) doublings doublings learning
Pulverized coal — 10% 1% — 5 0.38%
Hydrogen 20% 10% 1% 3 5 0.77%
Combustion turbine—natural gas — 10% 1% — 5 0.38%
Heat recovery steam generator (HRSG) — — 1% — — 0.19%
Gasifier — 10% 1% — 5 0.38%
Carbon capture and sequestration 20% 10% 1% 3 5 0.77%
Balance of plant—turbine — — 1% — — 0.19%
Balance of plant—combined cycle — — 1% — — 0.19%
Fuel cell 20% 10% 1% 3 5 0.77%
Advanced nuclear 5% 3% 1% 3 5 0.77%
Biomass — 10% 1% — 5 0.38%
Geothermal — 8% 1% — 5 0.38%
Hydropower — — 1% — — 0.19%
Battery storage—balance of plant 20% 10% 1% 1 5 0.77%
Battery storage—battery component 20% 10% 1% 1 5 0.77%
Wind — — 1% — — 0.19%
Wind offshore 20% 10% 1% 3 5 0.77%
Solar photovoltaic (PV)—module 20% 10% 1% 1 5 0.77%
Balance of plant—solar PV — 10% 1% — 5 0.38%
Data source: U.S. Energy Information Administration, Office of Long-Term Energy Modeling
Note: The text describes the methodology for learning in the Electricity Market Module. If a column does not contain a value, the
learning period has already passed for that technology.
The learning function, OC, has the following nonlinear form:
OC(C) = a*C-b,
where C is the cumulative capacity for the technology component.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 10

---

## [page 17]

April 2026
The progress ratio (pr) is defined by speed of learning (that is, how much costs decline for every
doubling of capacity). The reduction in capital cost for every doubling of cumulative capacity (learning
rate, or LR) is an exogenous parameter input for each component (Table 5). The progress ratio and
learning rate are related by the following:
pr = 2-b = (1 - LR).
The parameter b is calculated from the second equality above (that is, b = -(ln(1-LR)/ln(2))). The
parameter a is computed from the following initial conditions:
a =OC(C )/C –b,
0 0
where
C = the initial cumulative capacity.
0
Once the LR and the cumulative capacity (C ) are known for each interval, we can compute the
0
parameters (a and b). We developed three learning steps to reflect different stages of learning as a new
design is introduced into the market. New designs with significant untested technology will have high
rates of learning initially, and more conventional designs will not have as much learning potential. If the
calculated factor is less than the annual minimum learning assumption, then we apply the minimum
learning to reflect developments due to ongoing research and development.
Once we calculate the learning rates by component, we calculate a weighted-average learning factor for
each technology. We base the weights on the share of the initial cost estimate that is attributable to
each component (Table 6). For technologies that do not share components, we calculate this weighted-
average learning rate exogenously and input it as a single component. These technologies may still have
a mix of revolutionary components and more mature components, but we do not need to include this
detail in the module unless capacity from multiple technologies would contribute to component
learning.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 11

---

## [page 18]

April 2026
Table 6. Component cost weights for new technologies
Balance of
Carbon Balance plant—
Pulverized Combustion capture and of plant— combined
Technology coal Hydrogen turbine HRSG sequestration turbine cycle
USC with 30% CCS 90% 0% 0% 0% 10% 0% 0%
USC with 95% CCS 80% 0% 0% 0% 20% 0% 0%
Combined-cycle—single-
shaft 0% 0% 25% 10% 0% 0% 65%
Combined-cycle—multi-shaft 0% 0% 25% 10% 0% 0% 65%
Combined-cycle with 95%
CCS 0% 0% 15% 5% 40% 0% 40%
Combustion turbine—
aeroderivative 0% 0% 50% 0% 0% 50% 0%
Combustion turbine—
industrial frame 0% 0% 50% 0% 0% 50% 0%
Hydrogen turbine 0% 5% 48% 0% 0% 48% 0%
Data source: U.S. Energy Information Administration, Office of Long-Term Energy Modeling
Note: HRSG=heat recovery steam generator; CCS=carbon capture and sequestration
In the case of solar PV technology, we assume the module component accounts for 38% of the cost, and
we assume the balance of system components account for the remaining 62%. Because the amount of
end-use PV capacity (existing and projected) is significant relative to total solar PV capacity and the
technology of the module component is common across the end-use and electric power sectors,
calculating the learning factor for the PV module component also takes into account capacity built in the
residential and commercial sectors. The PV with battery storage cost is split between the battery
components (25%), the PV module (30%), and the PV balance of system (45%). The battery storage
technology is also broken out between the balance of system component (40%) and the battery (60%).
The battery component learning factor incorporates batteries installed for electricity vehicles in the
transportation sector as well as the power sector builds. For the offshore wind technology, we assume
that offshore-specific components make up 50% of the cost and that the remaining 50% overlaps with
the onshore wind technology.
Table 7 shows the capacity credit toward component learning for various technologies. For all
combined-cycle technologies, we assume the turbine unit contributes two-thirds of the capacity, and
the heat recovery steam generator (HRSG) contributes the remaining one-third. Therefore, building one
gigawatt (GW) of natural gas or oil combined-cycle capacity would contribute 0.67 GW toward turbine
learning and 0.33 GW toward HRSG learning. Components that do not contribute to the capacity of the
plant, such as the balance of plant category, receive 100% capacity credit for any capacity built with that
component. For example, when calculating capacity for the balance of plant component for the
combined-cycle technology, we would count all combined-cycle capacity as 100%, both single-shaft and
multi-shaft.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 12

---

## [page 19]

April 2026
Table 7. Component capacity weights for new technologies
Balance of
Carbon Balance plant—
Pulverized Combustion capture and of plant— combined
Technology coal Hydrogen turbine HRSG sequestration turbine cycle
USC with 30% CCS 100% 0% 0% 0% 100% 0% 0%
USC with 90% CCS 100% 0% 0% 0% 100% 0% 0%
Combined-cycle—single- 0%
shaft 0% 67% 33% 0% 0% 100%
Combined-cycle—multi-shaft 0% 0% 67% 33% 0% 0% 100%
Combined-cycle with 90% 0%
CCS 0% 67% 33% 100% 0% 100%
Combustion turbine—
aeroderivative 0% 0% 100% 0% 0% 100% 0%
Combustion turbine—
industrial frame 0% 0% 100% 0% 0% 100% 0%
Hydrogen turbine 0% 100% 100% 0% 0% 100% 0%
Data source: U.S. Energy Information Administration, Office of Long-Term Energy Modeling
Note: HRSG=heat recovery steam generator; CCS=carbon capture and sequestration
International learning
The learning algorithm incorporates international capacity for onshore wind, offshore wind, battery
storage, and solar PV technologies because of significant overlap in the market for major plant
components. Existing international capacity that is consistent with technology characteristics used in
U.S. markets counts toward the base capacity amount. Assumed future additions are added to EMM
projections of new U.S. capacity additions, which contributes to future doubling of capacity and
associated learning cost reduction. The international projections for new capacity come from the
International Energy Outlook 2023 projections for countries outside of the United States. We apply a
weighting factor to reduce the international capacity projections to reflect components of the project
cost that may not apply to U.S. markets, such as country-specific labor or installation costs.
Distributed generation
We model distributed generation in the end-use sectors (as described in the relevant AEO2026
assumptions documents). Although model structure is available to include utility-initiated distributed
resource (DG) additions, this option was turned off for AEO2026 as the market for using utility-owned
DG resources to displace transmission and distribution upgrade costs has not significantly materialized.
Demand storage
Although not modeled in AEO2026, the EMM includes a demand storage technology that could simulate
load shifting through programs such as smart meters. The demand storage technology would be
modeled as a new technology capacity addition but with operating characteristics similar to pumped
storage. The technology can decrease the load during peak periods, but it must generate replacement
electricity at other times. The EMM uses an input factor to identify the replacement generation needed,
where a factor of less than 1.0 can represent peak shaving rather than purely shifting the load to other
times. The EMM no longer projects builds of this technology type because we added a more detailed
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 13

---

## [page 20]

April 2026
modeling of battery storage (as described in the Intermittent and storage modeling section). This
storage technology also reduces and shifts peak demand use.
Coal-to-gas conversion
The EMM includes existing coal plants that were converted to burn natural gas, based on the current
configuration and primary fuel use of the plants, as reported to EIA. In recent years, a number of
companies have retrofitted their coal plants to operate as single-cycle, natural gas steam plants to
reduce emissions from the plant or to take advantage of low natural gas prices. The EMM includes the
option to convert additional coal plants to natural gas-fired steam plants, if economical. The EMM also
reflects both existing capacity and retrofit options that represent coal plants that are now co-firing with
significant levels of coal and natural gas. These plants are listed as fossil steam plants in the AEO2026
reports but may use both coal and natural gas fuels.
We base the modeling structure for coal-to-natural gas conversions on the U.S. Environmental
Protection Agency’s (EPA) modeling for the 2023 Reference case.3 For this modeling, coal-to-natural gas
conversion means an existing boiler is modified to burn natural gas. Coal-to-natural gas conversion, in
this instance, is not the same as adding a natural gas turbine, replacing a coal boiler with a new natural
gas combined-cycle plant, or gasifying coal for a combustion turbine. The cost for retrofitting has two
components: boiler modification costs and the cost to extend natural gas lateral pipeline spurs from the
boiler to a natural gas main pipeline. The same retrofit costs are assumed for either conversion to 100%
natural gas or conversion to co-fire with coal and natural gas.
Allowing natural gas firing in a coal boiler typically means installing new natural gas burners, modifying
the boiler, and potentially modifying the environmental equipment. EPA’s engineers developed the cost
estimates based on discussions with industry engineers. These estimates were designed to apply across
the existing coal fleet. In the EMM, costs are estimated for eligible coal plants that EPA identified, which
excludes units of less than 25 megawatts (MW) and units with fluidized-bed combustion or stoker
boilers. The EMM does not include any capacity penalty for converting to natural gas, but it assumes a
5% heat rate penalty to reflect reduced efficiency as a result of lower stack temperature and the
corresponding higher moisture loss when natural gas is combusted instead of coal. The EMM assumes
that converted plants have 33% lower fixed operations and maintenance (O&M) costs because these
plants need fewer operators, maintenance materials, and maintenance staff. Variable O&M costs are
25% lower because of lower waste disposal and other costs. The incremental capital cost (in 2022 dollars
per kilowatt [kW]) is described by these functions:
For pulverized-coal-fired boilers:
Cost per kW = 484.75 * (75 / CAP)0.35
For cyclone boilers:
Cost per kW = 346.25 * (75 / CAP)0.35
where
CAP = the capacity of the unit in megawatts.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 14

---

## [page 21]

April 2026
To get unit-specific costs, we use EPA’s assumptions for natural gas pipeline requirements, which are
based on a detailed assessment of every coal boiler in the United States, to determine natural gas
volumes needed, distance to the closest pipeline, and size of the lateral pipeline required. The resulting
cost per kilowatt (kW) of boiler capacity varies widely; an average cost is $231/kW (in 2025 dollars).
Representing electricity demand
The annual electricity demand projections from the NEMS demand modules are converted into load-
duration curves for each of the EMM regions by using historical hourly load data. The system load
shapes by EMM region are based on data from 2018 to 2022 reported on the Form EIA-9304 and
normalized for weather by developing a regression model using temperature, wind speed, relative
humidity, and parameters related to the time of day, using 30 years of weather data. The projected load
shapes in the module can change over time by applying end-use specific shapes to incremental demand
growth relative to an initial base year. End-use load shapes for the residential and commercial end uses
use the National Renewable Energy Lab (NREL)5 RESTOCK6 and COMSTOCK7 databases, and the building
types and end-use equipment are aligned with the categories modeled by the NEMS building modules.
The transportation demand module represents multiple types of electric vehicles (EVs) and determines
where the charging for light-duty vehicles will occur (residential or commercial sites). We used several
sources to develop load shapes for the different modes of EV charging, but we primarily used NREL.8
When modeling sector demand and prices in the EMM, the EV charging demands are allocated to the
site where the charging occurs, either residential or commercial, rather than as a transportation sector
demand.
For both types of load shapes described above, the inputs are developed to reflect a 24-hour profile for
each of three typical day-types—weekday, weekend, and a single peak day per month—and each month
of the year. These profiles are then aggregated into the load-duration curve for the EMM, which has
nine time periods. First, we split the load data into three seasons: winter (December through March),
summer (June through September), and the shoulder seasons (October through November and April
through May). Within each season, the load data are sorted from high to low, and three load segments
are created: a peak segment representing the top 1% of the load and then two off-peak segments
representing the next 49% and 50%, respectively. Before sorting the demand to assign hourly time
periods to each time slice, we determine the net load (gross demand net of expected variable renewable
generation) at each hour. We then use net load to determine the time slice definitions. The height of the
time slice (demand requirement) is based on the average original gross load over the hours in the time
slice. However, the sorting that determines which hours are in the modeled time slices is based on net
load. This method ensures that the slices will be ordered so that the peak time period represents the
hours where peaker capacity such as combustion turbines operate and result in the highest marginal
cost. Hours with lower net demand will have different generating resources setting the marginal cost,
and these hours will be grouped as intermediate and base time segments in a given season to reflect
declining costs.
Our Residential Demand Module and Commercial Demand Module provide end-use consumption to the
EMM, including demand from the grid and from onsite generation. Most of the onsite generation is
supplied by behind-the-meter PV generation (in other words, rooftop PV generation), and the end-use
modules only provide an annual amount. The EMM dispatches both electric power sector and end-use
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 15

---

## [page 22]

April 2026
PV capacity using detailed solar resource profiles to more accurately reflect when the generation occurs.
For non-PV onsite generation, the EMM assumes the onsite end-use generation has a uniform capacity
factor throughout the year. In the residential and commercial reporting, the end-use consumption
reflects the total electricity consumed by end use, whether provided from generation onsite or
purchased from the grid. However, the reported electricity sales by sector only reflect the demand from
the grid, and the onsite generation is reported as direct use.
Intermittent and storage modeling
The EMM includes the ReStore Submodule to provide the detail needed to represent renewable
availability at a greater level than the nine time periods described in the previous section. We developed
this submodule to adequately model the value of four-hour battery storage technology, which can be
used to balance renewable generation in periods of high intermittent output but low demand. The
ReStore Submodule solves a set of linear programming sub-problems within the EMM to provide the
capacity planning and dispatch submodules with information on the value of battery storage and the
level of variable renewable energy curtailments. The sub-problems solve a set of 576 representative
hours for the year, and the results are aggregated back to the nine time periods the EMM uses. The
ReStore Submodule’s additional time granularity better represents hydroelectric dispatch, determines
wind and solar generation and any required curtailments, and determines the optimal use of any battery
storage capacity. Because it includes hourly level dispatch, the ReStore Submodule represents the costs
or constraints to ramping conventional technologies up and down to respond to fluctuations in
intermittent generation. It also provides the planning module with information on the value of storage
to determine future builds.
Capacity and operating reserves
Reserve margins (the percentage of capacity above peak demand that is needed to adequately maintain
reliability during unforeseeable outages) are established for each region by its governing body: public
utility commission, NERC region, ISO, or RTO. Because of uncertainty and differences in how these
entities measure peak demand and account for capacity accreditation for renewable and battery
technologies relative to how they are measured in our modules, we do not use reported reserve margins
directly. We calculated the implied reserve margin for 2024 from the model output to reflect the
achieved levels and assumed those would be maintained, ranging from 1% to 19%. We used the
reference reserve margins reported to NERC as a maximum value if our calculated values were higher.9
The reserves required are based on the assumed percentage multiplied by peak demand. We calculate
the total capacity required as the average of the net peak load hours (net of variable renewable
generation) plus reserves. Dispatchable technologies contribute to the reserve margin constraint fully,
but intermittent and storage technologies have a capacity credit that we calculate based on their
availability during the net peak load hours.
In addition to the planning reserve margin requirement, system operators typically require a specific
level of operating reserves (in other words, generators available within a short amount of time to meet
demand in case a generator goes down or another supply disruption occurs). These reserves can be
provided by plants that are operating at less than full capacity (spinning reserves) or by capacity that is
not operating but can be brought online quickly (non-spinning reserves). This assumption is particularly
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 16

---

## [page 23]

April 2026
important as more intermittent generators are added to the grid because technologies such as wind and
solar have unpredictable availability. The capacity and dispatch submodules of the EMM include explicit
constraints requiring spinning reserves in each load time period. We compute the amount of spinning
reserves required as a percentage of the load height for the time period plus a percentage of the
distance between the load for the time period and the seasonal peak. An additional calculated
requirement is a percentage of the intermittent capacity available in that period to reflect the greater
uncertainty associated with the availability of intermittent resources. All technologies (except
intermittent plant types and distributed generation) can be used to meet spinning reserves. We
developed different operating modes for each technology type to allow the module to choose between
operating a plant to maximize generation or contributing to spinning reserves or a combination of the
two. Minimum generation levels are required if a plant is contributing to spinning reserves, and these
minimums vary by plant type. Plant types typically associated with baseload operation have higher
minimums than those that can operate more flexibly to meet intermediate or peak demand. We assume
that battery storage capacity can provide spinning reserves when there is remaining charge not
projected to be discharged in a given hour by the ReStore Submodule and when there is remaining
discharge capacity.
Variable heat rates for coal-fired power plants
Low natural gas prices and rising shares of intermittent generation have shifted coal plant operations
from baseload to greater levels of cycling. The efficiency of coal plants can vary based on their output,
and a plant’s efficiency can decrease when it runs in a cycling mode or provides operating reserves. The
EMM models variable heat rates for coal plants based on the operating mode the EMM chooses to
better reflect actual fuel consumption and costs.
We constructed the relationship between operating levels and efficiencies from data available for 2013
through 2015 in the EPA’s continuous emission monitoring system (CEMS) and other EMM plant data.
We used a statistical analysis to estimate piecewise linear equations that reflect the efficiency as a
function of the generating unit’s output. We estimated the equations by coal plant type, taking into
account the configuration of existing environmental controls, and by geographic coal demand region,
based on plant-level data. We developed equations for up to 10 coal plant configurations across the 16
coal regions used in the EMM. The form of the piecewise linear equations for each plant type and region
combination can vary, and they have between 3 and 11 steps.
Within the EMM, these equations calculate heat-rate adjustment factors to normalize the average heat
rate in the input plant database (which is based on historical data and is associated with a historical
output level) and to adjust the heat rate under different operating modes. The EMM allows six different
modes within each season for coal plants. These modes are based on combinations of maximizing
generation, maximizing spinning reserves, or load following, and they can be invoked for the full season
(all three time periods) or for about half the season (only peak and intermediate time periods). Each of
these modes is associated with different output levels, and we calculate the heat-rate adjustment factor
based on the capacity factor implied by the operating mode.
Endogenous plant retirement modeling
Fossil fuel-fired steam plant retirements and nuclear and wind retirements are determined
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 17

---

## [page 24]

April 2026
endogenously within the module. We assume plant operators retire generating units when continuing to
run them is no longer economical. Each year, the module determines whether the market price of
electricity is high enough to support the continued operation of existing plant generators. We project
that a generating unit will be retired if the expected revenues from the generator are not enough to
cover the annual going-forward costs and if building replacement capacity will lower the overall cost of
producing electricity. Going-forward costs include fuel, O&M costs, and annual capital expenditures
(CAPEX), which are unit-specific and based on historical data. The average annual capital additions for
existing plants are $14/kW for oil and natural gas steam plants and $58/kW for nuclear plants (in 2025
dollars). We add these costs to the estimated costs at existing plants regardless of their ages. Beyond 50
years old, the retirement decision includes an additional $23/kW capital charge for nuclear plants to
reflect additional costs associated with the impacts of aging. Age-related cost increases are attributed to
capital expenditures for major repairs or retrofits, subsequent license renewals and regulatory
compliance costs, and increases in maintenance costs to reduce the effects of aging. For wind plants, an
additional aging cost of $5/kW is added beyond 30 years, rising to $9/kW beyond 40 years. These annual
cost adders reflect cost recovery of major capital expenditures to replace major component parts to
continue operating.
In 2018, we commissioned Sargent & Lundy (S&L) to analyze historical fossil fuel O&M costs and CAPEX
and to recommend updates to the EMM.10 The study focused particularly on whether age is a cost factor
over time. S&L found that for most technologies, age is not a significant variable that influences annual
costs, and in particular, capital expenditures seem to be incurred steadily over time rather than as a step
increase at a certain age. Therefore, we do not model step increases in O&M costs for fossil fuel
technologies. For coal plants, the report developed a regression equation for capital expenditures for
coal plants based on age and whether the plant had installed a flue gas desulfurization (FGD) unit. We
incorporated the following equation in NEMS to assign capital expenditures for coal plants over time:
CAPEX (2017 dollars per kilowattyear) = 16.53 + (0.126 × age in years) + (5.68 × FGD)
where
FGD = 1 if a plant has an FGD; zero otherwise.
For the remaining fossil fuel technologies, the module assumes no aging function. Instead, both O&M
and CAPEX remain constant over time. We updated the O&M and CAPEX inputs for existing fossil fuel
plants using the data set analyzed by S&L, and S&L’s report describes them in more detail. We assigned
costs for the EMM based on plant type and size category (three to four tiers per type), and we split
plants within a size category into three cost groups to provide additional granularity for the module. We
assigned plants that were not in the data sample (primarily those not reporting to the Federal Energy
Regulatory Commission [FERC]) an input cost based on their size and the cost group that was most
common in their regions.
The report found that most CAPEX spending for combined-cycle and combustion-turbine plants is
associated with vendor-specified major maintenance events, generally based on factors such as the
number of starts or total operating hours. S&L recommended that CAPEX for these plants be recovered
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 18

---

## [page 25]

April 2026
as a variable cost. So, we assume no separate CAPEX costs for combined-cycle or combustion-turbine
plants, and we incorporate the CAPEX data into the variable O&M input cost.
We assume that all retirements reported as planned on the Form EIA-860, Annual Electric Generator
Report, will occur. This assumption includes 36.2 GW of coal capacity retirements after 2025.
For AEO2026, we updated existing nuclear unit operating costs based on an evaluation of aggregated
plant data reported for the most recent five-year period available (2020 2024). We developed average
–
plant costs for several categories:
• Design type (pressurized water reactor or boiling water reactor)
• Single- or multi-unit plant
• Regulated or deregulated ownership
• Region
We assigned individual plant costs by averaging the category averages based on each plant’s
characteristics. In general, we found that operating costs were lower for deregulated plants versus
regulated plants and multi-unit plants had lower costs than single-unit plants. Cost variations based on
design type or region were much smaller.
Biomass co-firing
We assume coal-fired power plants co-fire with biomass fuel if doing so is economical. Co-firing requires
a capital investment for boiler modifications and fuel handling. We assume this expenditure is $696/kW
of biomass capacity. A coal-fired unit modified to allow co-firing can generate up to 15% of the total
output using biomass fuel, assuming sufficient residue supplies are available.
Nuclear uprates
The AEO2026 nuclear power projection assumes capacity increases at existing units. Nuclear plant
operators can increase the rated capacity at plants through power uprates, which are license
amendments that the U.S. Nuclear Regulatory Commission (NRC) must approve. Uprates can vary from
small (for example, less than 2%) increases in capacity, which require very little capital investment, to
extended uprates of 15% to 20%, which require significant plant modifications. We assume that uprates
reported as planned modifications on Form EIA-860 will take place; several small uprates totaling 200
MW are planned through 2030. The NRC reports no pending applications for uprates,11 and AEO2026
assumes no additional uprates during the projection period.
Interregional electricity trade
The EMM represents both firm and economy electricity transactions among utilities in different regions.
In general, firm electricity transactions involve trading capacity and energy to help another region satisfy
its reserve margin requirement, and economy electricity transactions involve energy transactions
motivated by the marginal generation costs of different regions. The existing capacity limits constrain
the flow of power from region to region. We primarily derive the interregional capacity limits from
transmission capacity inputs to the National Renewable Energy Laboratory’s ReEDS (Regional Energy
Deployment System) model. Additional sources include the Western Electricity Coordinating Council’s
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 19

---

## [page 26]

April 2026
(WECC) seasonal reliability assessments and the New York Independent System Operator’s Reliability
Needs Assessments. International capacity limits are derived from the Northeast Power Coordinating
Council’s (NPCC) and WECC’s seasonal assessments, the Electricity Reliability Council of Texas’s DC Tie
Operations Documents, and Canadian Provincial Electricity websites. Known firm power contracts are
compiled from FERC Form 1, Annual Report of Major Electricity Utility, and we also consult utility
Integrated Resource Plan documents, individual ISO reports, and Canadian Provincial Electricity
websites. The EMM includes an option to add interregional transmission capacity. In some cases,
building generating capacity in a neighboring region may be more economical, but expanding the
transmission grid may incur additional costs. Explicitly expanding the interregional transmission capacity
may also make the transmission line available for additional economy trade.
We determine economy transactions in the dispatching submodule by comparing the marginal
generating costs of adjacent regions in each time period. If one region has less expensive generating
resources available in a given time period (adjusting for transmission losses and transmission capacity
limits) than another region, we assume the regions exchange power.
International electricity trade
The EMM represents two components of international firm power trade: existing and planned
transactions as well as unplanned transactions. We compile data on existing and planned transactions
from FERC Form 1 and provincial reliability assessments. The EMM endogenously determines
international electricity trade on an economic basis based on surplus energy that we expect to be
available from Canada by region in each time period. We determine Canada’s surplus energy using a
mini-dispatching submodule that uses Canadian provincial plant data, load curves, demand forecasts,
and fuel prices to determine the excess electricity supply by year, load slice, supply step, step cost, and
Canadian province. The projected data on Canada come from the International Energy Outlook 2023.
Electricity pricing
We project electricity pricing for the 25 electricity market regions for fully competitive, partially
competitive, and fully regulated supply regions. The price of electricity to the consumer includes
generation, transmission, and distribution prices and applicable taxes.
In AEO2026, transmission and distribution remain regulated, so the prices of transmission and
distribution are based on the average cost to build, operate, and maintain these systems using a cost-of-
service regulation model. We project continued capital investment in the transmission and distribution
system as a function of changes in peak demand, based on historical trends. We add additional
transmission capital investment with each new generating build to account for the costs to connect to
the grid. We developed regression equations to project transmission and distribution operating and
maintenance costs as a function of peak demand and overall customer sales. The total electricity price in
the regulated regions consists of the average cost of generation, transmission, and distribution for each
customer class.
In competitive regions, the generation price includes the marginal energy cost, taxes, and a capacity
payment. The marginal energy cost is the cost of the last (or most expensive) unit dispatched, reflecting
fuel and variable costs only. We calculate the capacity payment as a weighted average of the levelized
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 20

---

## [page 27]

April 2026
costs for combustion turbines and the marginal value of capacity calculated within the EMM, which
reflects the cost of maintaining the assumed reserve margin. We calculate the capacity payment for all
competitive regions, and these payments should be viewed as a proxy for additional capital recovery
that must be procured from customers rather than as representing a specific market. The capacity
payment also includes the costs associated with meeting the spinning reserves requirement. The EMM
calculates the total cost for both reserve margin and spinning reserve requirements in a given region
and allocates it to the sectors, based on their contributions to overall peak demand.
The total electricity price in regions with a competitive generation market is the competitive cost of
generation summed with the average costs of transmission and distribution. The price for mixed regions
includes the load-weighted average of the competitive price and the regulated price, based on the
percentage of electricity load in the region that is subject to deregulation.
The AEO2026 assumes full competitive pricing in the two New York regions and in the mid-Atlantic and
Metropolitan Chicago regions, and it assumes 95% competitive pricing in New England (Vermont being
the only fully regulated state in that region). Eleven regions fully regulate their electricity supply:
• Florida
• Carolinas
• Southeast
• Tennessee Valley
• Southern Great Plains
• Central Great Plains
• Northern Great Plains
• Upper Mississippi Valley
• Mississippi Delta
• Southwest
• Rockies
All other regions reflect a mix of both competitive and regulated prices.
Regulated price components allocate costs to the end-use sectors based on a variety of allocation
methods. For example, fuel and variable costs are shared based on the sector’s share of total demand,
while capital and other fixed costs use allocation methods related to the sector’s contribution to peak
demand. Adding to peak demand typically requires more investment in new capacity, so more of the
costs will go to the sectors contributing to peak demand. As described earlier, EV charging is now
allocated to residential and commercial sectors, and the EV charging demand patterns are often based
on overnight charging that does not coincide with typical peak demand periods. Therefore, increases in
EV charging demand may affect sector prices differently and will depend on where the charging occurs
as well as the charging profile assumed.
Fuel price expectations
We base capacity planning decisions in the EMM on a life-cycle cost analysis during a 30-year period,
which requires foresight assumptions for fuel prices. We derive expected coal, natural gas, and oil prices
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 21

---

## [page 28]

April 2026
using rational expectations, or perfect foresight. In this approach, we define expectations for future
years by the realized solution values for these years in a previous model run. The expectations for the
world crude oil price and natural gas wellhead price are set using the resulting prices from a previous
model run. We calculate the markups to the delivered fuel prices based on the markups from the
previous year within a NEMS run. We determine coal prices using the same coal supply curves
developed in the NEMS Coal Market Module. The supply curves produce prices at different stages of
coal production as a function of labor productivity, mine costs, and utilization. The EMM develops
expectations for each supply curve based on the actual demand changes from the previous run
throughout the projection period, resulting in updated mining utilization and different supply curves.
The perfect foresight approach generates an internally consistent scenario from which we can form
expectations consistent with the projections realized in the model. The NEMS model involves iterative
run cycles until the expected values and realized values for variables converge between cycles.
Nuclear fuel prices
We develop projected nuclear fuel prices offline and input them into the EMM because NEMS does not
have an internal fuel supply module for uranium processing and nuclear fuel fabrication. We updated
the nuclear fuel price projections for AEO2026 based on a logarithmic trend of reported nuclear plant
fuel costs over the past 15 years.
Legislation and Regulations
AEO2026 represents, to the extent possible within the NEMS model framework, current laws and
regulations applicable to the electric power sector. Because of the time lags involved in model
development and publication, laws and regulations in force as of December 1, 2025, are included in the
Counterfactual Baseline case and other applicable cases of the AEO2026. Changes to laws and
regulations resulting from executive action, judicial review, or the legislative subsequent to December 1,
2025, are not included in AEO2026 and will be included as possible in future AEO publications.
Cross-State Air Pollution Rule and Clean Air Act Amendments of 1990
AEO2026 continues to include the Cross-State Air Pollution Rule (CSAPR), which addresses the interstate
transport of air emissions from power plants. Under CSAPR, 27 states must restrict emissions of sulfur
dioxide (SO ) and nitrogen oxide (NO ), which are precursors to fine particulate matter (PM2.5) and
2 x
ozone forming. CSAPR establishes four allowance-trading programs for SO and NO composed of
2 x
different member states, based on each state’s contribution to downwind nonattainment of the
National Ambient Air Quality Standards (Figure 2). In addition, CSAPR splits the allowance-trading
program into two regions for SO , Group 1 and Group 2, and trading is permitted only between states
2
within a group (estimated in NEMS by trade between coal demand regions) but not between groups. On
March 15, 2021, EPA finalized an update to the CSAPR to require additional emissions reductions of NO
x
from power plants in 12 states and to revise the budgets for their emissions from 2022 to 2024.
The AEO2026 does not reflect changes that would have been introduced through EPA’s 2023 Good
Neighbor Plan to further revise NO standards because the U.S. Supreme Court issued a stay on
x
implementation. The requirements under CSAPR remain in place.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 22

---

## [page 29]

April 2026
Figure 2. Cross-State Air Pollution Rule
Data source: U.S. Environmental Protection Agency, Clean Air Markets
In addition to interstate transport, the Clean Air Act Amendments of 1990 (CAAA1990) require existing
major stationary sources of NO located in nonattainment areas to install and operate NO controls that
x x
meet Reasonably Available Control Technology (RACT) standards. To implement this requirement, EPA
developed a two-phase NO program that took effect for existing coal plants in 1996 and 2000. The
x
EMM assumes all operating plants have made the necessary retrofits to comply with these standards
and calculates plant emissions based on the reported environmental controls on each plant. All new
fossil fuel units must meet current standards. These limits are 0.11 pounds per million British thermal
units (MMBtu) for conventional coal, 0.02 pounds/MMBtu for advanced coal, 0.02 pounds/MMBtu for
combined cycle, and 0.08 pounds/MMBtu for combustion turbines. The EMM incorporates these RACT
NO limits.
x
Table 8 shows the average capital costs for environmental control equipment in NEMS for existing coal
plants as retrofit options to remove SO , NO , mercury (Hg), and hydrogen chloride (HCl). In the EMM,
2 x
we calculate plant-specific costs based on the size of the unit and other operating characteristics, and
these numbers reflect the capacity-weighted averages of all plants in each size category. We assume
FGD units remove 95% of the SO and selective catalytic reduction (SCR) units remove 90% of the NO .
2 x
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 23

---

## [page 30]

April 2026
Table 8. Coal plant retrofit costs
2025 dollars per kilowatt
Coal plant size
(megawatts) FGD capital costs FF capital costs SCR capital costs
<100 $1,196 $342 $491
100–299 $842 $258 $349
300–499 $668 $220 $307
500–699 $612 $205 $299
>=700 $550 $189 $284
Data source: U.S. Energy Information Administration, Office of Long-Term Energy Modeling
Notes: FGD=flue gas desulfurization unit; FF=fabric filter; SCR=selective catalytic reduction unit
In April 2024, EPA finalized its Section 111 of the Clean Air Act (CAA) regulating CO emissions from
2
existing coal, oil, and natural gas-fired steam generating units and new natural gas-fired combustion
turbines.12 The ruling requires existing steam turbines at coal-fired power plants to either convert to a
natural gas-fired steam unit or cofire with at least 40% natural gas by 2030 if the units are intended to
operate until January 1, 2039, or they must be retrofitted with a carbon capture and sequestration (CCS)
system with a 90% capture rate by 2032 if they are intended to operate beyond January 1, 2039;
otherwise they must retire. AEO2026 represents these requirements for existing coal plants, allowing
the model to make economic decisions regarding conversion fully to natural gas-fired operation,
conversion to co-fire with natural gas, or retrofit with a CCS system by the appropriate deadlines.
EPA also revised carbon pollution standards for new, modified, and reconstructed power plants under
CAA Section 111(b). The emission rate for newly constructed coal steam units maintains the 2015
standard of 1,400 pounds of CO per megawatthour, which requires at least partial sequestration. The
2
EMM allows new coal technologies (ultra-supercritical technology) with either 30% or 95% removal
rates to be built if economical. The 2024 rule also created different categories for compliance by new
natural gas-fired technologies. Plants that intend to run as base load (greater than 40% capacity factor)
must operate with 90% CO capture by 2032, while plants operating at intermediate or low load levels
2
have standards consistent with current efficient designs and use of low-emitting fuel. The AEO2026
represents this restriction in operation on any new natural gas-fired combined-cycle plants that are built
without CCS. The EMM does not explicitly represent modified or reconstructed power plants, which are
also covered by the rule.
In June 2025, EPA proposed to repeal all greenhouse gas emissions (GHG) standards for the power
sector under Section 111 of the CAA,13 which would remove all requirements imposed from the 2024
rule. In February 2026, EPA announced the final rule repealing the 2009 GHG Endangerment Finding that
served as the basis for the Section 111 provisions noted above. The promulgation of this rule occurred
after the December 2025 cut-off that EIA used to determine which policies could be modeled for
AEO2026; therefore, it is not reflected in the Counterfactual Baseline or core side cases. The Alternative
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 24

---

## [page 31]

April 2026
Electricity case was run to reflect the impacts of removing the 2015 and 2024 requirements discussed
above. It does not necessarily reflect any specific provisions of the final rule, which was not available to
EIA at the time the policy assumptions were finalized.
Heat rate improvement retrofits
The EMM can evaluate heat rate improvements at existing coal-fired generators. A generator with a
lower heat rate can generate the same amount of electricity while consuming less fuel, which reduces
corresponding emissions of SO , NO , Hg, and CO . Improving heat rates at power plants can lower fuel
2 x 2
costs and help them comply with environmental regulations. Heat rate improvement is a planning
activity because it considers the tradeoff between the investment expenditures and the savings in fuel
and environmental compliance costs. The amount of potential increase in efficiency can vary depending
on the type of equipment installed at a unit and the beginning configuration of the plant. The EMM
represents 32 configurations of existing coal-fired plants based on different combinations of particulate,
SO , NO , Hg, and CO emissions controls (Table 9). These categories form the basis for evaluating the
2 x 2
potential for heat rate improvements.
We contracted with Leidos, Inc., to develop a methodology to evaluate the potential for heat rate
improvement at existing coal-fired generating plants.14 Leidos performed a statistical analysis of the
heat rate characteristics of coal-fired generating units that we modeled in the EMM. Specifically, Leidos
developed a predictive model for coal-fired electric generating unit heat rates as a function of various
unit characteristics, and Leidos employed statistical modeling techniques to create the predictive
models.
For the EMM plant types, Leidos categorized the coal-fired generating units into four equal groups, or
quartiles, based on observed versus predicted heat rates. Units in the first quartile (Q1), which operated
more efficiently than predicted, were generally associated with the least potential for heat rate
improvement. Units in the fourth quartile (Q4), representing the least efficient units relative to
predicted values, were generally associated with the highest potential for heat rate improvement.
Leidos developed a matrix of heat rate improvement options and associated costs, based on a literature
review and engineering judgment.
Little or no coal-fired capacity exists for the EMM plant types with mercury and carbon-control
configurations; therefore, Leidos did not develop estimates for those plant types. These plant types
were ultimately assigned the characteristics of the plant types with the same combinations of
particulate, SO , and NO controls. Plant types with relatively few observations were combined with
2 x
other plant types that had similar improvement profiles. As a result, Leidos developed nine unique plant
type combinations for the quartile analysis, and for each of these combinations, Leidos created a
maximum potential for heat rate improvement along with the associated costs to achieve those
improved efficiencies.
Leidos used the minimum and maximum characteristics as a basis for developing estimates of midrange
cost and heat rate improvement potential. The EMM used the midrange estimates as its default values
(Table 10).
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 25

---

## [page 32]

April 2026
Table 9. Existing pulverized-coal plant types in the National Energy Modeling System’s Electricity
Market Module
Particulate SO2 NOx Mercury Carbon
Plant type controls controls controls controls controls
B1 BH None Any None None
B2 BH None Any None CCS
B3 BH Wet None None None
B4 BH Wet None None CCS
B5 BH Wet SCR None None
B6 BH Wet SCR None CCS
B7 BH Dry Any None None
B8 BH Dry Any None CCS
C1 CSE None Any None None
C2 CSE None Any FF None
C3 CSE None Any FF CCS
C4 CSE Wet None None None
C5 CSE Wet None FF None
C6 CSE Wet None FF CCS
C7 CSE Wet SCR None None
C8 CSE Wet SCR FF None
C9 CSE Wet SCR FF CCS
CX CSE Dry Any None None
CY CSE Dry Any FF None
CZ CSE Dry SCR FF CCS
H1 HSE/Oth None Any None None
H2 HSE/Oth None Any FF None
H3 HSE/Oth None Any FF CCS
H4 HSE/Oth Wet None None None
H5 HSE/Oth Wet None FF None
H6 HSE/Oth Wet None FF CCS
H7 HSE/Oth Wet SCR None None
H8 HSE/Oth Wet SCR FF None
H9 HSE/Oth Wet SCR FF CCS
HA HSE/Oth Dry Any None None
HB HSE/Oth Dry Any FF None
HC HSE/Oth Dry Any FF CCS
Data source: U.S. Energy Information Administration
Note: Particulate controls: BH=baghouse; CSE=cold-side electrostatic precipitator; HSE/Oth=hot-side electrostatic precipitator,
other, or none. SO 2 =sulfur dioxide; NO x =nitrogen oxide. SO 2 controls: wet=wet scrubber; dry=dry scrubber. NO x controls:
SCR=selective catalytic reduction. Mercury controls: FF=fabric filter. Carbon controls: CCS=carbon capture and sequestration.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 26

---

## [page 33]

April 2026
Table 10. Heat rate improvement (HRI) potential and cost (capital as well as fixed operations and
maintenance) by plant type and quartile as used for input into the National Energy Modeling System
Average fixed operations and
Plant type and Capital cost maintenance cost
quartile Count of total Percentage HRI (million 2014 dollars (2014 dollars per megawatt per
combination units potential per megawatt) year)
B1-Q1 32 (s) $0.01 $200
B1-Q2 15 1% $0.10 $2,000
B1-Q3 18 4% $0.20 $4,000
B1-Q4 20 6% $0.90 $20,000
B3-Q1 13 (s) $0.01 $300
B3-Q2 24 1% $0.05 $1,000
B3-Q3 16 6% $0.20 $3,000
B3-Q4 15 9% $0.60 $10,000
B5C7-Q1 16 (s) (s) $80
B5C7-Q2 42 1% $0.03 $700
B5C7H7-Q3 84 7% $0.10 $2,000
B5C7H7-Q4 59 10% $0.20 $4,000
B7-Q1 27 (s) (s) $70
B7-Q2 25 1% $0.04 $800
B7-Q3Q4 30 7% $0.30 $5,000
C1H1-Q1 148 (s) $0.01 $200
C1H1-Q2 117 1% $0.10 $2,000
C1H1-Q3 72 4% $0.40 $8,000
C1H1-Q4 110 7% $1.00 $30,000
C4-Q1 15 (s) (s) $80
C4-Q2 27 1% $0.04 $900
C4-Q3 32 6% $0.20 $2,000
C4-Q4 39 10% $0.30 $5,000
CX-Q1Q2Q3Q4 15 7% $0.20 $4,000
H4-Q1Q2Q3 13 3% $0.20 $3,000
IG-Q1 3 (s) (s) $60
Total set 1,027 4% $0.30 $6,000
Data source: U.S. Energy Information Administration, based on data from Leidos, Inc.
Note: Leidos selected the plant type and quartile groupings so that each grouping contained at least 10 generating units,
except for the integrated gasification combined-cycle (IG) type, which has essentially no heat rate improvement potential.
(s)=less than 0.05% for HRI potential or less than 0.005 million dollars per megawatt for capital cost.
Mercury regulation
The Mercury and Air Toxics Standards (MATS) were finalized in December 2011 to fulfill EPA’s
requirement to regulate mercury emissions from power plants. MATS also regulates other hazardous air
pollutants (HAPS) such as hydrochloric acid (HCl) and fine particulate matter (PM2.5). MATS applies to
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 27

---

## [page 34]

April 2026
coal- and oil-fired power plants with a nameplate capacity greater than 25 MW, and it required that all
qualifying units achieve the maximum achievable control technology (MACT) for each of the three
covered pollutants by 2016. We assume that all coal-fired generating units affected by the rule meet HCl
and PM2.5 standards, which the EMM does not explicitly model.
All power plants must reduce their mercury emissions to 90% less than their uncontrolled emissions
levels. When plants alter their configuration by adding equipment, such as an SCR to remove NO or an
x
SO scrubber, mercury removal is often a resulting co-benefit. The EMM considers all control
2
combinations and can choose to add NO or SO controls purely to lower mercury if it is economical to
x 2
do so. Plants can also add activated carbon-injection systems specifically designed to remove mercury.
Activated carbon can be injected in front of existing particulate-control devices, or a supplemental fabric
filter can be added with activated carbon injection capability.
We assume the equipment to inject activated carbon in front of an existing particulate control device
costs about $8 (2025 dollars) per kilowatt of capacity.15 We also calculate the costs of a supplemental
fabric filter with activated carbon injection (often referred as a COPAC unit) by unit (Table 8). The
amount of activated carbon required to meet a given percentage removal target is given by the
following equations.16
For a unit with a cold-side electrostatic precipitator (CSE) that uses subbituminous coal and simple
activated carbon injection, the following equation is used:
ACI = activated carbon injection rate in pounds per million actual cubic feet of flue gas
• Hg Removal (%) = 65 - (65.286 / (ACI + 1.026))
For a unit with a CSE that uses bituminous coal and simple activated carbon injection, we use:
• Hg Removal (%) = 100 - (469.379 / (ACI + 7.169))
For a unit with a CSE and a supplemental fabric filter with activated carbon injection, we use:
• Hg Removal (%) = 100 - (28.049 / (ACI + 0.428))
For a unit with a hot-side electrostatic precipitator (HSE) or other particulate control and a supplemental
fabric filter with activated carbon injection, we use:
• Hg Removal (%) = 100 - (43.068 / (ACI + 0.421))
Power plant mercury emissions assumptions
The EMM represents 36 coal plant configurations and assigns a mercury emissions modification factor
(EMF) to each configuration. Each configuration has different combinations of boiler types, particulate
control devices, SO control devices, NO control devices, and mercury control devices. An EMF is the
2 x
amount of mercury in the fuel that remains after passing through all the plant’s systems. For example,
an EMF of 0.60 means that 40% of the mercury in the fuel is removed by various parts of the plant. Table
11 provides the assumed EMFs for existing coal plant configurations without mercury-specific controls.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 28

---

## [page 35]

April 2026
Table 11. Mercury emission modification factors
Configuration EIA EMFs EPA EMFs
particulate Sub Lignite Sub Lignite
SO2 control control NOx control Bit coal coal coal Bit coal coal coal
None BH — 0.11 0.27 0.27 0.11 0.26 1.00
Wet BH None 0.05 0.27 0.27 0.03 0.27 1.00
Wet BH SCR 0.10 0.27 0.27 0.10 0.15 0.56
Dry BH — 0.05 0.75 0.75 0.50 0.75 1.00
None CSE — 0.64 0.97 0.97 0.64 0.97 1.00
Wet CSE None 0.34 0.73 0.73 0.34 0.84 0.56
Wet CSE SCR 0.10 0.73 0.73 0.10 0.34 0.56
Dry CSE — 0.64 0.65 0.65 0.64 0.65 1.00
None HSE/Oth — 0.90 0.94 0.94 0.90 0.94 1.00
Wet HSE/Oth None 0.58 0.80 0.80 0.58 0.80 1.00
Wet HSE/Oth SCR 0.42 0.76 0.76 0.10 0.75 1.00
Dry HSE/Oth — 0.60 0.85 0.85 0.60 0.85 1.00
Data source: U.S. Environmental Protection Agency emission modification factors (EPA EMFs). EIA EMFs not from EPA:
Lignite EMFs, Mercury Control Technologies for Coal-Fired Power Plants, presented by the Office of Fossil Energy on July 8,
2003. Bituminous coal mercury removal for a Wet/HSE/Oth/SCR configured plant, Table EMF1, Analysis of Mercury Control
Cost and Performance, Office of Fossil Energy & National Energy Technology, U.S. Department of Energy, January 2003,
Washington, DC
Note: Under SO 2 control: SO 2 =sulfur dioxide; wet=wet scrubber; dry=dry scrubber. Under particulate control: BH=fabric filter
or baghouse; CSE=cold-side electrostatic precipitator; HSE/Oth=hot-side electrostatic precipitator, other, or none. Under NO x
control: NO=nitrogen oxide; SCR=selective catalytic reduction.
x
— =not applicable; Bit=bituminous coal; Sub=subbituminous coal. The NO control system is not assumed to enhance
x
mercury removal unless a wet scrubber is present, so we left it blank (—) in such configurations.
Tax credit for carbon oxide sequestration
The Section 45Q sequestration tax credit was modified as part of the Inflation Reduction Act of 2022
(IRA).17 The AEO2026 represents the sequestration tax credit and the captured carbon market in the
Carbon Capture, Allocation, Transportation and Sequestration submodule. The 45Q credits are available
to both power and industrial sources that capture and permanently sequester CO in geologic storage or
2
use CO in enhanced oil recovery (EOR). Credits are available to plants that start construction or begin a
2
retrofit after December 31, 2022, and before January 1, 2033. The tax credits are applied for the first 12
years of operation. The IRA increased the credit values starting in 2023, relative to the previous versions
of the credit, if qualified facilities meet the prevailing wage and apprenticeship requirements for the
additional bonus credit (as assumed in the AEO2026 cases). The OBBBA updated the credit value so that
CO used for EOR now receives the same, higher value that was previously provided only for CO that is
2 2
permanently sequestered.
Carbon capture and sequestration retrofits
The EMM includes the option of retrofitting existing coal and natural gas-fired combined cycle plants
with CCS. The modeling structure for CCS retrofits within the EMM was developed by the National
Energy Technology Laboratory (NETL)18 and uses a generic model of retrofit costs as a function of basic
plant characteristics (such as heat rate). EIA’s retrofit costs for both types of plants use the public power
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 29

---

## [page 36]

April 2026
generation CO capture retrofit database models provided by NETL,19 using plant-specific characteristics
2
from EIA’s power plant surveys. We assume the CCS retrofits remove 90% of the carbon input. Adding
CCS equipment results in a capacity derate and a reduced efficiency of about 30% at the existing coal
plant. The costs depend on the size and efficiency of the plant; capital costs average $2,468/kW for coal
retrofits and $1,475/kW for natural gas retrofits. For coal plants, this analysis assumes that only plants
greater than 500 MW and with heat rates lower than 12,000 Btu per kilowatthour (kWh) would be
considered for CCS retrofits.
State air emissions regulations
AEO2026 continues to model the Northeast Regional Greenhouse Gas Initiative (RGGI), which applies to
fossil fuel-powered plants larger than 25 MW in northeastern and certain mid-Atlantic states. After
withdrawing in 2011, New Jersey adopted rules to rejoin the program in 2019.20 In July 2020, Virginia
passed legislation to join the program and was included beginning in 2021,21 resulting in 11 states in the
accord from 2021 to 2023. In June 2023, Virginia’s Air Pollution Control Board voted to exit the program,
becoming effective December 31, 2023. The rule caps CO emissions from covered electricity-generating
2
facilities and requires that they account for each ton of CO emitted with an allowance purchased at
2
auction. EMM incorporates all subsequent updates to the original rule, which include amended caps, a
specific cap through 2030, modifications to the Cost Containment Reserves (available if defined
allowance-price triggers are exceeded), and an Emissions Containment Reserve (to be used if prices fall
lower than established trigger prices). The cap reflects adjustments to the budget allocation as
additional states join or exit.
The California Senate Bill 32 (SB32), passed in October 2016, revises and extends the greenhouse gas
(GHG) emission reductions that were previously in place to comply with Assembly Bill 32 (AB32), the
Global Warming Solutions Act of 2006. AB32 implements a cap-and-trade program in which the electric
power sector as well as industrial facilities and fuel providers must have met emission targets by 2020.
SB32 requires the California Air Resources Board (CARB) to enact regulations to ensure the maximum
technologically feasible and cost-effective GHG emission reductions occur, and it set a new state
emission target of 40% lower than 1990 emission levels by 2030.
A companion law, Assembly Bill 197 (AB197), directs the CARB to consider social costs for any new
programs to reduce emissions and makes direct emission reductions from stationary, mobile, and other
sources a priority. The California Assembly Bill 398 (AB398), passed in July 2017, clarifies how the new
targets will be achieved.
AEO2026 continues to assume that a cap-and-trade program remains in place, and it sets annual targets
through 2030 that remain constant afterward. The emissions constraint is in the EMM but accounts for
the emissions determined by other sectors. Within the electric power sector, emissions from plants
owned by California utilities but located outside of the state, as well as emissions from electricity
imports into California, count toward the emission cap. Estimates of these emissions are included in the
EMM constraint. We calculate and add an allowance price to fuel prices for the affected sectors. We
model a limited number of allowances for banking and borrowing as well as an allowance reserve and
offsets, as specified in the bills. These provisions provide some compliance flexibility and cost
containment. Changes in other modules to address SB32 and AB197, such as assumed policy changes
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 30

---

## [page 37]

April 2026
that affect vehicle travel and increases in energy efficiency, are described in the Transportation Demand
Module assumptions, Commercial Demand Module assumptions, Residential Demand Module
assumptions, and the Summary of Legislation and Regulations on the Assumptions to the Annual Energy
Outlook 2026 web page.
State and federal revenue support for existing nuclear power plants
Three states have legislation to support prices for existing nuclear units that could be at risk of early
closure because of declining profitability. The New York Clean Energy Standard,22 established in 2016,
created zero emission credits (ZEC) that apply to certain nuclear units. The Illinois Future Energy Jobs
Act,23 passed in 2017, also created a ZEC program covering a 10-year term. The Clinton and Quad Cities
nuclear plants were selected to receive payments under the original ZEC program. In September 2021,
the Illinois Climate and Equitable Jobs Act24 was passed and includes carbon mitigation credits available
to additional nuclear power plants, which led to the reversal of plans to shut down the Byron and
Dresden plants. In 2018, the New Jersey Senate passed bill S. 2313,25 which established a ZEC program
that is funded by a $0.004/kWh annual charge that equals about $300 million per year. Three nuclear
reactors are eligible to receive payments from the fund during the year of its implementation plus the
three following years, and they may be considered for additional three-year renewal periods thereafter.
Although each program has different methods for calculating payments and eligibility, this legislation is
modeled more generally in EMM by explicitly requiring nuclear units located in Illinois, upstate New
York, and New Jersey to continue to operate through the specific program’s period (the module cannot
choose to endogenously retire the plant). We determine the cost of each program by comparing the
affected plants’ costs with the corresponding revenues based on the modeled marginal energy prices to
evaluate plant profitability. If plant costs exceed revenues, the module applies a subsidy payment. The
plant recovers the subsidy payment cost through retail prices as an adder to the electric distribution
price component to represent ZEC purchases by load-serving entities.
In addition, a federal nuclear credit program was passed as part of the Infrastructure Investment and
Jobs Act in August 2021.26 The program aims to support nuclear power plants that are struggling to
remain economically viable in competitive electricity markets and are at risk of shut down. The Secretary
of Energy will determine specific unit eligibility and credit level under a $6 billion budget. The EMM
models this program by expanding the state ZEC logic to all competitive states that are not already
receiving state payments, but for these additional states, the costs are not passed through to electricity
prices.
The Inflation Reduction Act of 2022 (IRA) introduces a zero-emission nuclear power production tax
credit (PTC) for existing plants that were in service before the act was enacted. The credit value starts at
0.3 cents/kWh (2022 dollars), but this base value is reduced if a plant’s average revenues exceed 2.5
cents/kWh (where revenues include any payments from programs listed previously). The tax credit can
then be increased by a factor of five if facilities meet certain labor requirements. In the EMM, we
calculate the value of this credit endogenously based on the modeled plant revenues received, and we
assume all existing plants meet the labor requirements. The tax credit is available for electricity
generated in 2024 through 2032. OBBBA affirmed availability of this tax credit through 2032.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 31

---

## [page 38]

April 2026
Federal tax credits for new construction
The federal tax credits available to certain electric-generating technologies initiated in the Energy Policy
Act of 1992 (EPACT1992) and amended in the Energy Policy Act of 2005 (EPACT2005) have been further
amended through a series of acts that we have implemented in NEMS over time. AEO2026 reflects the
most recent changes implemented through the OBBBA.
The IRA created investment tax credits (ITC) and production tax credits (PTC) available to all clean
electricity technologies, defined as those with a zero GHG emission rate. New advanced nuclear and
small modular reactor facilities placed in service after December 31, 2024, are eligible to take either
credit, both of which are adjusted for bonuses if certain conditions are met regarding employee wages,
domestic content (which requires certain construction materials to be produced in the United States),
and development in key communities. AEO2026 assumes that new nuclear facilities will opt to take the
clean electricity PTC. This PTC starts with a base value of 0.3 cents/kWh in 1992 dollars that is adjusted
for inflation each year based on IRS guidelines. For new nuclear plants, we assume that the wage and
apprenticeship requirements are met to increase the base level by a factor of five and that the plants
receive a 10% bonus for meeting the domestic content requirement. The OBBBA introduces a 10%
bonus for advanced nuclear facilities built in "nuclear energy communities," which was not modeled due
to lack of data and guidance to determine the communities at the EMM regional level.
New battery storage technologies are eligible for the clean electricity ITC, and AEO2026 assumes that
the wage and apprenticeship requirements are met, resulting in a 30% ITC level. Federal tax credit
assumptions for renewable technologies are discussed in detail in the Renewable Fuels Module (RFM)
assumptions, including updates through the OBBBA to significantly accelerate the tax credit expiration
for wind and solar plants. For all other eligible electricity technologies, the OBBBA imposes a firm
deadline of 2032 (based on construction start), after which they phase out over three years. Plants that
are under construction in 2032 will still receive 100% of the tax credit, but the value will fall to 75% in
the next year and 50% in the following year. Plants under construction in 2036 or later will not receive
tax credits.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 32

---

## [page 39]

April 2026
Notes and Sources
1 Cost and Performance Estimates for New Utility-Scale Electric Power Generating Technologies, Sargent & Lundy,
January 2024.
2 Brattle 2025 CONE Report for PJM, The Brattle Group and Sargent & Lundy, April 9, 2025.
3 Documentation for 2023 Reference Case, EPA’s Power Sector Modeling Platform 2023 Using IPM, April 2024.
4 U.S. Energy Information Administration, Hourly and Daily Balancing Authority Operations Report, EIA 930.
5 The National Renewable Energy Lab was renamed as the National Laboratory of the Rockies in December 2025.
All work and data cited herein were accessed and utilized prior to this change in name; citations reflect the name
used when the work was published and accessed by EIA.
6 National Renewable Energy Lab, End-Use Load Profiles for the U.S. Building Stock, RESTOCK.
7 National Renewable Energy Lab, End-Use Load Profiles for the U.S. Building Stock, COMSTOCK.
8 National Renewable Energy Lab, Electric Vehicle Infrastructure – Projection Tool, EVI-Pro Lite.
9 North American Electric Reliability Corporation, 2021 Long-Term Reliability Assessment, December 2021.
10 Generating Unit Annual Capital and Life Extension Costs Analysis, Sargent & Lundy Consulting, December 2019.
11 U.S. Nuclear Regulatory Commission, Status of Power Uprate Applications.
12 U.S. Environmental Protection Agency, Greenhouse Gas Standards and Guidelines for Fossil Fuel-Fired Power
Plants, April 25,2024
13 U.S. Environmental Protection Agency, Repeal of Greenhouse Gas Emissions Standards for Fossil Fuel-Fired
Electric Generating Units, Federal Register, Vol. 90, No. 115, June 17, 2025.
14 Analysis of Heat Rate Improvement Potential at Coal-Fired Power Plants, May 2015, Leidos, Inc.
15 We developed these costs by using the National Energy Technology Laboratory’s Mercury Control Performance
and Cost Model, 1998.
16 U.S. Department of Energy, Analysis of Mercury Control Cost and Performance, Office of Fossil Energy & National
Energy Technology Laboratory, January 2003.
17 Inflation Reduction Act, Public Law 117-169, (August 16, 2022), https://www.congress.gov/bill/117th-
congress/house-bill/5376.
18 Retrofitting Coal-Fired Power Plants for Carbon Dioxide Capture and Sequestration—Exploratory Testing of NEMS
for Integrated Assessments, DOE/NETL-2008/1309, P.A. Geisbrecht, January 18, 2009.
19 National Energy Technology Laboratory, Carbon Capture Retrofit Studies, Natural Gas Combined Cycle CO2
Capture Retrofit Database and Pulverized Coal CO2 Capture Retrofit Database, March 2023.
20 New Jersey Department of Environmental Protection, Press Release on Governor Murphy’s Executive Order
No.7, February 28, 2018.
21 “Virginia Becomes First Southern State to Join Regional Greenhouse Gas Initiative,” Virginia Governor News
Release, July 8, 2020.
22 State of New York Public Service Commission, Order Adopting a Clean Energy Standard, August 1, 2016.
23 State of Illinois, Future Energy Jobs Act, SB2814, Public Act 099-0906, June 1, 2017.
24 State of Illinois, Climate and Equitable Jobs Act, SB2408, September 15, 2021.
25 State of New Jersey, Senate Bill No. 2313, May 23, 2018.
26 U.S. Congress, Infrastructure, Investment and Jobs Act, HR3684, November 15, 2021.
U.S. Energy Information Administration | Assumptions to the Annual Energy Outlook 2026: Electricity Market Module 33
