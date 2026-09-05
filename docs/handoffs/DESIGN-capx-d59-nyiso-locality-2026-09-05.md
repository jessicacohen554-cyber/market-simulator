# DESIGN — capx D59: the NYISO LOCALITY half — NYC (J) and Long Island (K) priced on their own published ICAP demand curves at their own published requirements, settled by the ICAP Manual's locality-stacking rule (`locality_capacity_curves`, GATED default-OFF, zero DOF)

**Lane:** capx D59, the first of the three routes D52 §8(2) names (locality half → 2025/26
vintage / 2025 SOM transcription check → the P9 (a)/(b)/(c) re-run). Branch
`claude/capx-d59-nyiso-locality-3p7sju`, fresh off `origin/main` (`db057c5d`). Fable session.
**This document is pushed BEFORE any code** (the D52 discipline); its §8 pre-declaration is
fixed here, its §8.4 cache keys are appended after the build and BEFORE any solve, and it is
graded at full magnitude in the D59 finding. **NOTHING ARMS.**

DATA PROFILE: nyiso. Comparator: `nyiso-t1h-d52-curveon` (`589f031432b6dc7d`, the D52
posture — both requirement gates ON, NYCA curve ON). Control for byte-inertness: the bare
`nyiso-t1h` (`91686abe7a744a88` at the D52 HEAD; re-resolved at this HEAD in §8.4).

## 0. The design in one paragraph

NYISO's spot market is the one capacity market whose real mechanism IS "evaluate the
published curve at the supplied quantity" (D28 §4, D54 §4.9), and it does that **per
locality**: the ICAP Manual §5.15.2 clears a Market-Clearing Price for the NYCA *and for
each Locality* — the Locality's price is where its own supply meets its own Demand Curve,
**"unless the Market-Clearing Price determined for Rest of State is higher, in which case
the Market-Clearing Price for that Locality will be set at the Market-Clearing Price for
Rest of State."** The model today represents NYISO adequacy as one NYCA position (D52 put
that position within ±3 pts of the market) and pays a Ravenswood steam unit the NYCA price
where the market paid Zone J 3.4× that in 2024/25. This design adds, behind one default-OFF
gate, the locality instance of the same census-evaluated-curve mechanism the NYCA half
already is: per representable locality L ∈ {NYC, LI}, **position_L = the model's
in-locality ICAP supply ÷ the published Locational Minimum ICAP Requirement** (the ICAP
Manual §2.6 translation-factor identity makes the UCAP position equal this ratio — §2.2),
**price_L = the locality's own published vintage curve at position_L** (the same
`_nyiso_icap_vintage_curve` construction the NYCA curve uses, on the locality's published
reference point, maximum clearing price, curve length and Annual Reference Value), and a
unit in zone z earns **max(NYCA price, price of every locality containing z) × its accredited
MW** — the §5.15.2 rule verbatim. The same locational price reaches the thermal-entry screen
(a candidate is also screened sited in each locality, at that zone's own LP prices, the
locality price and the published locality Gross-CONE cost differential), the VRE RA payment
at the sited zone, and storage's load-share-weighted capacity value. G-J is NOT
representable on the 5-zone partition and is excluded by rule (§1). The shipped Part-B
long-zone collapse is **superseded** for NYISO, never stacked (§5.2). Zero free parameters:
every number is a published curve parameter, a published requirement, or a published
rights table (§4). The pre-stated sign (rule 14): downstate steam retires HARDER — the
946 MW NYC share of D52's 1,801 MW 2025 gas_st wave is the cohort at stake; the 855 MW
Rest-of-State share is NOT reached by this design and is expected to fire again (§8).

## 1. (a) The locality set representable on the model's zones — the rule

NYISO's five model zones (`iso_configs._nyiso_config`) aggregate the eleven load zones as
Upstate_West = A–E, Capital_Hudson = **F+G**, Lower_Hudson = H+I, NYC = J, Long_Island = K.
NYISO's three Localities (ICAP Manual §2.6): New York City = J, Long Island = K, the G-J
Locality = G+H+I+J.

**Rule: a locality is representable iff it is a union of model zones.** NYC = {NYC} and LI =
{Long_Island} are unions of one zone each (the crosswalk's two `leaf` rows,
`capacity_area_crosswalk._NYISO`). G-J = G+H+I+J would need {Capital_Hudson − F,
Lower_Hudson, NYC}; Capital_Hudson fuses F (Capital, Rest-of-State) with G (Hudson Valley,
inside G-J), so no union of model zones equals G-J and **G-J is excluded** (the crosswalk's
existing `aggregate` row, unchanged). Consequence, stated with its published magnitude:
units in H–I (Lower_Hudson) and G are settled at the NYCA price where the market pays the
G-J price; the committed spot record bounds the premium — G-J = NYCA in 2020/21, 2024/25,
2025/26; +$0.14/kW-month (2022/23) and +$0.06 (2023/24) otherwise, i.e. ≤ $1.7/kW-yr in
every committed year (`auction-price/nyiso/nyiso.csv`). Representing G-J would need a
zone-partition change (F split from G), which is the topology's — not this lane's — and is
routed, not built. NYC and LI are also the two localities where the premium is material
(NYC $191.6 / $141.1 / $131.8 per kW-yr vs NYCA $49.3 / $41.6 / $51.4 in 2023/24 · 2024/25 ·
2025/26; LI ≥ NYCA by construction).

## 2. (b) Per locality: requirement, supply, position, curve

### 2.1 Requirement — the published Locational Minimum ICAP Requirement, through the existing reader

`R_L(y)` = `capacity_deliverability.requirement_by_area("NYISO", delivery_year)[L]`
(`value_mw` of the committed `capacity-deliverability/nyiso/nyiso.csv` `requirement`
rows: NYC 9,224 / 8,985 / 8,673 MW, Long Island 5,400 / 5,348 / 5,423 MW for 2023/24 ·
2024/25 · 2025/26), the ICAP MW the LCR reports publish as `[G] = [C]/(1 − [E]) + [F]`
(re-verified this session against the fetched 2023-24 / 2024-25 LCR Reports and the
2025-26 Final TSL Floor Values sheet, sha256 in §9 — every committed MW row and LCR %
reconciles; LI's 2023/24 and 2025/26 MW are the adopted LCR × the forecast peak where the
TSL floor was not binding, 5,133 × 1.052 and 5,092 × 1.065). Delivery-year label:
`capdel.resolve_delivery_year("NYISO", y)` → the capability year beginning May 1 of model
year y, the SAME information gate D52 uses for Table D.2 (the row of CY y/y+1 is on file
before May 1 of y and is read in model year y only). Before the first committed CY
(2022/2023 is the earliest with MW rows; 2018/19 carries only %): no row ⇒ the locality is
not priced that year (the NYCA price alone, exactly today's behaviour) — never a
hold-first of a MW requirement. Beyond the last committed CY: **hold-last of the LCR %
× the model's own locality forecast peak** (the load-share of the ISO forecast peak, the
same object the NYCA half's seam peak is) — a ratio holds like D52's factor pair; a MW
requirement would fail the rule-13 forward test.

**The published `import_limit` rows (the TSL: NYC 2,875 / LI 275 MW) do NOT enter the
locality supply.** This is the seam the charter asked to be read before designing: the
shipped Part-B construction (`deliverability_headroom_by_zone`) defines
`deliverable = in-zone firm + import_limit`, which is right for a PJM LDA (CETL is supply
against the LDA's whole-load requirement) and WRONG for NYISO, whose LCR is already net
of the import capability — the TSL floor is literally `UCAP floor = (forecast peak −
TSL)/peak` (LCR Report TSL-floor table rows [B]–[D]), so adding the TSL to supply would
count the imports twice and read NYC ~30 pts long. The rows are consumed only as a
consistency assertion (`LCR ≥ TSL floor` for each committed CY — true in every row).

### 2.2 Supply and position — the ICAP-basis identity (ICAP Manual §2.6)

The market's locality position is `UCAP supplied ÷ UCAP requirement`, where (§2.6, quoted):
*"the NYISO will convert the Locational Minimum Installed Capacity Requirements of LSEs
into Locational Minimum Unforced Capacity Requirements by multiplying such Locational
Minimum Installed Capacity Requirements by the quantity one (1) minus the Locational
translation factor. The Locational translation factor shall be calculated by taking the
quantity one (1) minus a value equal to: (a) the total amount of Unforced Capacity that
all resources electrically located in the relevant Locality are qualified to provide
during such Capability Period … divided by (b) the sum of the Installed Capacity values
used to determine the Unforced Capacity …"*. Substituting: UCAP_req = ICAP_req ×
ΣUCAP/ΣICAP, hence

    position_L = ΣUCAP_L / UCAP_req_L = ΣICAP_L / ICAP_req_L        (exact, by the tariff's own construction)

The locality position is therefore evaluated **on the ICAP basis with the model's own fleet
census**: `S_L(y)` = Σ over the ENTERING fleet's units in zone(L) of `pmax_mw` (the ICAP /
DMNC analogue; tranche rows of a plant-binned unit sum to the plant), plus the LP's zonal
renewable nameplate (`wind_cap[z]`, `solar_cap[z]` — the runner's own zonal arrays, NOT a
load-share split of an ISO total), plus in-zone storage `power_cap_mw`, plus the
**External UDR rights into L** (§2.3). Position_L = S_L / R_L. Why this and not
"model UCAP ÷ published UCAP requirement with a published translation factor": (i) the
identity makes the position independent of the model's class-EFORd assumption, so it
measures the one thing the model actually represents — the census — and nothing else;
(ii) it needs no intake of monthly translation factors and no misaligned proxy (the LCR
reports' `[E]` is a 5-year IRM-study EFORd, a different window from the capability-period
translation factor); (iii) it IS the tariff's construction. It is computed once per year on
the ENTERING fleet, at the same point and on the same fleet object as the NYCA
`curve_reserve_position` (runner ≈ line 1972), so the two positions the settlement
compares are contemporaneous (rule 19).

**What the census excludes, stated with its published magnitude (never adjusted for):**
Special Case Resources (the LCR table's `[F]`, inside `[G]`): NYC 417.5 / 442.4 / 478.7 MW
≈ 4.5 / 4.9 / 5.5 pts of position; LI 33.7 / 35.3 / 30.6 MW ≈ 0.6 pt; the model carries no
SCR supply at the NYCA level either (the NYISO shard's `pjm_demand_response_supply` note),
so the treatment is one census across both halves — an SCR series enters NYISO only through
a NYISO lane's own derivation (D52 §5 item 2, routed). The pre-declaration (§8.2) reports
the SCR-adjusted reading as an information row so the census gap is visible, not absorbed.

### 2.3 External UDRs — the locality-attributable part of the D2 tie, from the published rights table

The D2 tie credit (`ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]`, Gold Book Table V-1 net
purchases, 3,168.5 MW ICAP) already counts the UDR-backed products at the NYCA level. A
locality's share is published: ICAP Manual §4.9.6 "UDRs awarded" — Cross Sound Cable
330 MW (→ Zone K), Neptune 660 MW (→ K), Linden VFT 315 MW (→ J), Hudson Transmission
Project 660 MW (→ J; CRIS expired 2022-04-30, 85 MW CRIS elected 2024 — footnote 1),
Champlain Hudson Power Express 1,250 MW (→ J; in service CY 2026/27 onward). Registry
`NYISO_LOCALITY_UDR_ICAP_MW` (locality, line, MW, first CY, last CY, source), dated per
the manual's own footnotes: LI 990 MW every CY; NYC 315 + 660 through CY 2021/22, 315 in
2022/23–2023/24, 315 + 85 from 2024/25, +1,250 from 2026/27. Enters the locality ICAP
supply only (no generator, no dispatch effect); the NYCA half is untouched (no double
count — the tie is already inside it). Rule 13: rights are re-published in every manual
revision and respond to conditions (the HTP CRIS lapse IS such a response).

### 2.4 The locality curve — the NYCA construction on the locality's published parameters

`price_L(y)` = `evaluate_demand_curve(curve_L(vintage(y)), position_L) × ARV_L(vintage(y))
× 1000` $/firm-MW-yr, with `curve_L` = `_nyiso_icap_vintage_curve(ref_point_summer,
max_clearing_summer, length_L)` — the identical straight-line construction the NYCA
vintages use (net-CONE fraction 1.0 at position 1.0, zero at 1 + length, the cap where
the summer max/reference ratio meets the line) on the locality's own published rows of
`demand-curve/nyiso/nyiso.csv` (all committed; re-verified this session against the
fetched Demand Curve Parameters sheets — every row reconciles):

| CY | locality | ARV $/kW-yr | summer ref $/kW-mo | summer max | length | zero-cross | cap frac | cap x |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023/24 | NYC | 154.53 | 21.20 | 29.63 | 18 % | 1.18 | 1.398 | 0.928 |
| 2023/24 | LI | 66.26 | 13.08 | 24.21 | 18 % | 1.18 | 1.851 | 0.847 |
| 2024/25 | NYC | 150.98 | 19.84 | 31.63 | 18 % | 1.18 | 1.594 | 0.893 |
| 2024/25 | LI | 61.24 | 11.29 | 26.59 | 18 % | 1.18 | 2.355 | 0.756 |
| 2025/26 | NYC | 140.47 | 17.37 | 41.30 | 18 % | 1.18 | 2.378 | 0.752 |
| 2025/26 | LI | 49.61 | 6.80 | 28.16 | 18 % | 1.18 | 4.141 | 0.435 |
| 2026/27 | NYC | 144.08 | 17.81 | 42.67 | 18 % | 1.18 | 2.396 | 0.749 |
| 2026/27 | LI | 57.58 | 7.89 | 29.09 | 18 % | 1.18 | 3.687 | 0.516 |
| 2021/22, 2022/23 | NYC / LI | (no ARV published) | 21.28 / 17.60 ; 22.77 / 17.59 | — | 18 % | — | flat anchor = ref × 12, `()` shape — the NYCA convention for those two vintages | |

Vintage resolution is `resolve_demand_curve_vintage`'s step function on a per-locality
table (`LOCALITY_MARKET_DESIGN_VINTAGES["NYISO"][L]`), hold-first / hold-last exactly as the
NYCA table. The locality curves live as `MarketDesignVintage` constants reconciled to the
csv rows by test (the repo's curve convention, `test_nyiso_curve_matches_published`'s
pattern per locality), the requirement rows through the curated reader (§2.1) — rule 6.

**A construction limit shared with the NYCA curve, stated not changed.** The repo's
annualization places the Annual Reference Value at position 1.0, while the published
sheet defines the ARV as the annual revenue at the tariff-prescribed *Level of Excess*
(NYCA 100.52 %, G-J 101.62 %, NYC 102.23 %, LI 103.77 % in 2025/26) on a two-season
reference-point construction. At the LOE the repo's line therefore pays ARV × f(LOE) —
0.957 × ARV for NYCA, 0.876 × for NYC, 0.79 × for LI — an under-read whose sign is
conservative for this design (locality prices read LOW, so downstate retention is
under-stated, never manufactured). It is the CR-3 seasonal item the NYCA code comment
already names; a curve-shape change is barred by D45 §9 without new evidence and is
identical across both arms of the A/B, so it is recorded in the finding, not built.

### 2.5 The observables (validation, never targets)

Published summer UCAP margins per locality (Potomac SOM Tables 9/11/9, re-extracted this
session): 2023/24 NYCA 4.3 / G-J 8.5 / NYC 2.6 / LI 13.1 %; 2024/25 5.8 / 16.4 / 5.7 /
11.7 %; 2025/26 — **the 2025 SOM Table 9 prints the 2024 row verbatim (5.8 / 16.4 / 5.7 /
11.7) while its own "Net Change from Previous Yr" row reads −2.3 / +1.0 / +2.1 / +0.5 and
its narrative says the systemwide margin FELL and NYC's surplus INCREASED; the implied
2025/26 margins are 3.5 / 17.4 / 7.8 / 12.2 %** (§7). Published full-year spot prices:
§1. The model's locality positions are compared with these; nothing is fitted to them.

## 3. (c) Settlement — the ICAP Manual §5.15.2 stacking rule

For a unit (or candidate, or storage MW) in model zone z:

    capacity_price(z) = max( P_NYCA , max_{L ∋ z} P_L )          $/firm-MW-yr
    capacity_revenue  = capacity_price(z) × accredited MW         (the existing accreditation seam)

P_NYCA is the EXISTING seam price, `MarketDesign.capacity_price_per_firm_mw_yr(config,
reserve_position, iso, year)` — the NYCA curve at the D52-repaired NYCA position when the
curve gate is ON. The locality term is the §5.15.2 clause quoted in §0: a Locality clears
on its own curve *unless Rest of State is higher*. The max is implemented as ONE optional
argument on the one seam (`capacity_revenue_per_mw_yr(..., locality_price_per_firm_mw_yr=)`
→ `price = max(price, locality)`), so every screen prices through the same function and no
screen-specific curve exists (rule 19). Zones in no locality (Upstate_West, Capital_Hudson,
Lower_Hudson) pass no locality price and are byte-identical to today.

**The gate requires the NYCA curve gate ON for NYISO.** Predicate
`locality_capacity_curves_armed(config, iso)` = the field AND `iso ∈
LOCALITY_MARKET_DESIGN_VINTAGES` (NYISO alone — rule 25) AND
`resolve_capacity_market_clearing(config, iso)`. With the NYCA leg on the flat $110 stub
the stacking max is meaningless (a flat $110 exceeds every locality price except NYC's
short side), so the field is inert there (logged once) — the D54 §7.1 guard in the same
form. The A/B posture is therefore the D52 curve-ON recipe plus this field (§8.4).

## 4. (d) Zero DOF — the ledger

| number | source |
|---|---|
| `R_L(y)` | published Locational Minimum ICAP Requirement MW (LCR Reports / TSL sheet), committed `capacity-deliverability/nyiso/nyiso.csv` `requirement` rows, through the existing reader |
| `S_L(y)` | the model's own entering fleet by zone (`pmax_mw`), the LP's zonal `wind_cap` / `solar_cap`, in-zone storage power — the solve's own objects |
| UDR rights by locality | ICAP Manual §4.9.6 table + footnote 1 (dated) |
| `curve_L`, `ARV_L` | the committed `demand-curve/nyiso/nyiso.csv` locality rows (Demand Curve Parameters sheets 2023-24 … 2026-27), the NYCA construction |
| the stacking rule | ICAP Manual §5.15.2, verbatim |
| Gross-CONE cost differential (entry side, §5.5) | the same sheets' "Gross Cost of New Entry ($/kW-Year)" row per locality per CY |
| representable-locality rule | a partition statement (§1), not a value |

No adder, no floor, no haircut, no zone premium, no per-fuel term. Cleared spot prices and
SOM margins enter nothing (they are §2.5 observables).

## 5. (e) Interactions — decided and cited

### 5.1 The D52 requirement gates (the NYCA half) — sat on, never re-derived
P_NYCA is whatever the NYCA half produces; this design reads `reserve_position` and never
touches `resolve_adequacy_requirement_mw`, the composite, the floor or the admission cap.
The A/B arms both D52 gates so the NYCA position is the repaired one (D52 §3.1).

### 5.2 The shipped Part-B long-zone collapse — SUPERSEDED for NYISO (rule 19, one locational mechanism per ISO)
Part B (`capacity_deliverability_limits`) collapses the payment in a LONG zone to $0 on a
binary headroom test with the TSL counted as supply (§2.1). For NYISO the locality curve
IS the locational mechanism: a long locality's price falls along its own published curve
to $0 at 1 + length, a short one's rises to the published cap, and a unit is never paid
below the NYCA price. The two cannot co-exist: `__post_init__` raises when both
`locality_capacity_curves` and `capacity_deliverability_limits` are set on a NYISO config
(fail-closed, rule 19); the Part-B code path is untouched for the other ISOs (Part A's
CAISO seam limit is unaffected). The NYISO shard's `capacity_deliverability` cell stays
`fc: U` (never solved for NYISO) with a note that the NYISO instance is this field.

### 5.3 The dates channel (rule 19: a dated unit is not screened)
Unchanged. Step-0/1b exits (confirmed instruments, owner-filed EIA-860 dates) bypass the
screen and therefore never see a capacity price; the locality price reaches only the
UNDATED residual the economic screen decides. The 2023 NYC gas_ct 416 MW `announced`
exits of the comparator are unaffected by construction.

### 5.4 The reliability floor and the admission cap
Both NYCA-level and unchanged (`_zone_is_long` exemption stays a no-op — Part B is off).
No locality floor is added: NYISO's real retention mechanism when a locality is short is
the price (the curve rises to the published cap: NYC 2.378 × ARV = $334/kW-yr in 2025/26),
and out-of-market retention is the RMR channel (SOM 2025 Table 4, NYC reliability
commitments), which is the dates/instrument channel's, not a floor. A locality reading
BELOW its TSL floor is written to the ledger as an observable (`below_tsl_floor: true`),
never acted on.

### 5.5 The entry side — new downstate entry MUST see the locality price
Today the thermal candidate loop prices energy at the ISO-mean LP price and the capacity
leg at the default build zone (Upstate_West for NYISO — never a locality), so downstate
entry never sees a locality price. Under the gate each thermal candidate is ALSO screened
sited in each representable locality, on the machinery the screen already carries (the
D33 `_choose_vre_zone` shape, extended to thermal for NYISO): energy margin on THAT zone's
LP price row (`prices[zi]`, the same reserve legs), capacity leg `max(P_NYCA, P_L) ×
accreditation`, and fixed cost × the published locality Gross-CONE ratio
`GrossCONE_L(vintage) / GrossCONE_NYCA(vintage)` — NYISO's own peaking-plant cost
differential (2025/26: NYC 222.73 / 127.71 = 1.744, LI 137.03 / 127.71 = 1.073; 2024/25
229.11 / 132.98 and 186.37 / 132.98; 2023/24 212.81 / 120.04 and 168.15 / 120.04; 2026/27
230.10 / 131.94 and 141.57 / 131.94 — rows for 2023/24–2025/26 are INTAKEN this lane into
`nyiso.csv` `gross_cone`, the same source documents the ARV rows already cite, sha256 in
§9; 2026/27 is already committed). The candidate is sited at its argmax margin; a tie
keeps the default zone (D33's discipline: never relocate on no information). Cost is
otherwise zone-invariant (capex, FOM, CRF unchanged). VRE: `_vre_cap_payment(tech,
ra_zone)` passes the sited zone's locality price (D33's zone chooser then ranks on it —
offshore wind sited in Long_Island sees LI's price). Storage: the build is distributed
by load_share, so its expected capacity value is the load-share-weighted
`max(P_NYCA, P_z)` over zones (the `_deliverability_capacity_factor` shape), passed to
`compute_storage_capacity_value` through the same optional argument. Expected effect in
the hindcast: none pulled (a NYC gas_ct at NYC's 2025 price ≈ $80/kW-yr × 0.93 against a
1.744× fixed cost does not clear — consistent with the SOM's own reading that no new
gas-fired capacity has been developable in NYC since 2019); the point is forward
symmetry — exits and entry see the same locational price.

### 5.6 CCS retrofit screen, backstop, RPS
Unaffected (no capacity leg in the retrofit uplift; the backstop is NYCA-level and gated
off; RPS is an LP constraint).

## 6. (f) The 2025/26 vintage / 2025 SOM transcription check — done, zero-solve

1. **The committed 2025-2026 curve rows are exact.** Fetched `Demand-Curve-Parameters-
   2025-2026.pdf` (sha256 `175492d0…`): NYCA / G-J / NYC / LI ARV 50.55 / 50.66 / 140.47 /
   49.61; summer reference points 5.72 / 6.15 / 17.37 / 6.80; winter 4.33 / 5.29 / 14.64 /
   8.78; summer maxima 21.69 / 23.25 / 41.30 / 28.16; winter 16.39 / 19.99 / 34.83 /
   36.37; lengths 12 / 15 / 18 / 18 % — every committed row matches. The 2023-24 and
   2024-25 sheets (ICAPWG decks p.31 / p.30, sha256 `89d6ce92…` / `80d557cb…`) likewise
   reconcile every committed locality ARV / reference / maximum row. **No transcription
   defect in the curve intake.** The 2025/26 half-price reading D52 flagged is therefore
   a real property of the published 2025-2029 DCR reset (a 200 MW 2-hour battery
   peaking plant, LCR Report 2025-26 §III), not a records error.
2. **The 2025 SOM Table 9 UCAP-margin row is a carry-over of the 2024 SOM Table 11 row —
   a defect in the SOURCE.** Both print NYCA 5.8 / G-J 16.4 / NYC 5.7 / LI 11.7 %; the
   2025 table's own "Net Change from Previous Yr" row (−2.3 / +1.0 / +2.1 / +0.5) and its
   narrative ("the systemwide capacity margin fell and prices rose"; "the New York City
   capacity surplus increased in 2025") imply 2025/26 margins of **3.5 / 17.4 / 7.8 /
   12.2 %**. The 2024 row is internally consistent with 2023 (2023/24 4.3 % + 1.5 = 5.8).
   Consequence for D52's record: the published 2025 NYCA position is 1.035, not 1.058; the
   model's seam position (1.052) is then **+1.7 pts LONG** of the market rather than
   −0.6 SHORT — still inside the ±3-pt band, so P9 (c) still reads YES; the D45 instrument
   JSON row is a faithful transcription of a defective source cell and is left as
   committed, with this reading recorded beside it. The curve at the corrected position
   pays $35.8/kW-yr against the $51.36 full-year spot (−30 %), not $26.12 (−49 %).
3. **"Zone J cleared at $141" is the 2024/25 figure** ($11.76/kW-month × 12); the 2025/26
   NYC full-year average is $10.98 × 12 = **$131.8/kW-yr** (2025 SOM Table 9). The
   charter's and D52 §4's "$141" for 2025 is a one-year label slip; the argument is
   unchanged (NYC pays 2.6× NYCA in 2025/26, 3.4× in 2024/25, 3.9× in 2023/24).
4. **The $51.36 NYCA figure is a UCAP-basis full-year average** over the capability year
   (May 2025–Apr 2026); the model's curve is evaluated at one summer-basis position on
   the ICAP-priced curve (UCAP price = ICAP price ÷ (1 − translation factor), +15 % at
   the 2025/26 NYCA factor). Part of the D52 "half the real spot" gap is therefore basis
   and averaging, not curve level — recorded, not corrected here (the same convention
   sits under every NYCA year and both A/B arms).

## 7. Records — what the finding will carry
Per year and locality (ledger fields, additive, decision-neutral, cache-key-neutral, written
whether or not the gate is on — the D52 `screen_*` convention): `locality_icap_supply_mw`,
`locality_icap_requirement_mw`, `locality_position`, `locality_price_per_kw_yr`,
`nyca_price_per_kw_yr`, `settled_price_per_kw_yr`, `udr_icap_mw`, `below_tsl_floor`; per
retirement-screen row the settled zone price. The finding tabulates these beside §2.5's
published margins and spot prices per year.

## 8. (g) The pre-declaration — fixed here, graded at full magnitude in the finding

### 8.1 What is fixed before any number is computed
- **FC-3 sign (rule 14):** downstate steam retires HARDER. On D52's committed curve-ON
  ledger the 2025 gas_st wave (1,801 MW, 17 units) is NYC 946.0 MW (5 units) +
  Capital_Hudson 656.9 MW (4) + Upstate_West 197.9 MW (8). The design reaches ONLY the
  NYC cohort. A NYC gas_st unit fails the 2025 screen at a capacity leg of
  0.93 × $28.65 = $26.6/kW-yr against a ~$35 bar with ≈ $0.2 of energy margin; it passes
  iff its settled price ≥ ≈ $37.6/kW-yr, i.e. iff `max(28.65, P_NYC) ≥ 37.6`, i.e. iff the
  model's 2025 NYC position ≤ **1.132** on the 2025/26 NYC curve (140.47 × (1.18 − x)/0.18
  ≥ 37.6). **Prediction P1:** if the instrument's 2025 NYC position (§8.2) is ≤ 1.132, the
  946 MW NYC cohort does not fire and `retire.total_gw` reads ≈ 1.457 + 0.855 = **2.31 GW
  (+35 %)** with `false_retire` ≈ (0.256 + 0.855)/2.31 ≈ **0.48**; if it is > 1.132, the A/B
  is byte-identical to the comparator on FC-3 (P1′). Either way the 855 MW Rest-of-State
  share fires again at the NYCA $28.65 — this design cannot reach it, by construction.
- **P2 — P9 re-read.** (c) YES in every scored year (the NYCA positions are D52's,
  unchanged by construction: −2.6 / −1.8 / +1.7 pts on the corrected 2025 reading);
  (a) NO unless P1 removes the whole wave AND the residual 0.855 GW stays (+35 % is
  outside ±10 %); (b) NO (≥ 0.48). **Expected: one of three ⇒ the NYCA curve stays OFF
  after this lane too**, and the reason narrows to the Rest-of-State gas_st cohort at the
  2025/26 NYCA vintage — which is a curve-level / seasonal-construction object (§2.4,
  §6 items 1 and 4), not a locality or position object.
- **P3 — 2023 / 2024 screens:** no economic exits in either arm (every failing 2023 row
  already passes at $58.9 in the comparator; a higher NYC price cannot fail anything).
  Entry: `gas_cc 1.0 / gas_ct 0.0 / storage 0.000` unchanged (no candidate clears in a
  locality at the Gross-CONE ratio — §5.5); LOYO folds and T-R10 change only through P1.
- **P4 — positions vs the market (§2.5), the validation observable:** the model's NYC
  position is expected ABOVE the published margins in every year by roughly the SCR share
  (§2.2, 4.5–5.5 pts) less any census under-count; LI's is expected near the published
  11–13 % once the 990 MW of UDR rights are counted and well below it without them. The
  pre-declared band for "the census is the market's" is |model − published| ≤ 6 pts
  after the SCR information adjustment; a miss is a census finding (fleet zone assignment
  — e.g. an NJ-sited Zone-J resource such as Bayonne Energy Center, or a UDR treatment),
  routed, never tuned.
- **P5 — byte-inertness:** the bare `nyiso-t1h` key and the pinned default key are
  unmoved; every backcast key unmoved; the field coerces to its dataclass default in a
  plain backcast; PJM / MISO / NEISO / ERCOT / CAISO inert with the flag armed (test).
- **The falsifier:** a build that reproduces a published locality price only by tuning
  (any adder, floor, premium or census scalar) is refused. The design has no such knob;
  if the A/B's NYC price sits far from the published NYC spot, the finding reports the
  gap at full magnitude and names the census / construction cause, and the field is
  recommended NOT to arm.
- **The flip condition (P9-style, for the locality gate itself):** RECOMMEND ARM iff
  (i) every locality position is within the P4 band in every scored year, (ii) FC-3 moves
  in the pre-stated direction (NYC gas_st exits ↓, no new false exits, no locality entry
  the record contradicts), and (iii) the settled NYC price at the model's position is
  within a factor 1.5 of the published NYC spot in every scored year (the §2.4
  under-read bounds the tolerance; tighter is not honest on an annualized curve).
  Otherwise RECOMMEND DO NOT ARM and route the named cause.

### 8.2 The zero-solve instrument (appended before the build; no model code)
`docs/handoffs/d59/locality-predecl-2026-09-05.py` rebuilds the D52 curve-ON entering
fleet per year from the same loaders the hindcast runs (`load_or_synthesize_bins` →
`build_base_fleet` at the 2020 vintage, then the ledger's own per-unit exits / derates /
additions applied year by year, validated against each ledger's `fleet_by_fuel_before`
to the MW), sums the in-zone ICAP with the LP's zonal renewable nameplate and the UDR
registry, and evaluates HEAD's `_nyiso_icap_vintage_curve` construction on the locality
rows. Its rows + stdout are committed beside it. The table below is filled by it.

_(§8.2 table, §8.3 census check and §8.4 keys: appended by this lane before the build /
before any solve, in that order — nothing below this line was written before the
instrument ran.)_

### 8.2 The instrument's readings (appended 2026-09-05 after the instrument ran, BEFORE any code was committed)

`docs/handoffs/d59/locality-predecl-2026-09-05.py` → `.json` + `-stdout-….txt` beside it,
plus `goldbook-zone-jk-summer-capability-2026-09-05.json` (Gold Book Table III-2a sums).
**Reconstruction caveat, stated up front:** the instrument rebuilds the base fleet through
the hindcast's own loaders but does not reproduce the runner's base fleet exactly at the
NYCA level (per fuel vs the D52 2021 ledger: gas_ct −444 MW because the announced NYC
gas_ct exits of 2023 are applied at the base rather than in 2023; nuclear +123; oil −317;
biomass −58; gas_cc +35; gas_st +5 — loader-posture details the runner threads that this
zero-code instrument does not). The NYC and LI subsets are what matter here and are
checked against the published census (§8.3). The A/B ledger's own `locality_capacity`
block is the exact record the finding grades against; these are the expected values.

| CY | locality | fleet ICAP (model) | +VRE +storage | +UDR rights | supply | published ICAP req | **position** | published summer margin ⇒ position | gap (pts) | SCR-adjusted gap (info) | locality curve @ position | NYCA @ ledger position | **settled** | published spot |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | NYC | 9,187 (+416 gas_ct still entering in the runner ⇒ 9,603) | 5 | 315 | 9,507 (9,923) | 9,224 | **1.031 (1.076 with the 416)** | 1.026 | +0.5 (+5.0) | +5.0 (+9.5) | $128.2 ($89.3) | $63.34 | **$128.2 ($89.3)** | $191.6 |
| 2023 | LI | 5,145 | 138 | 990 | 6,273 | 5,400 | **1.162** | 1.131 | +3.1 | +3.7 | $6.7 | $63.34 | **$63.34** | $49.3 |
| 2024 | NYC | 9,187 | 5 | 400 | 9,592 | 8,985 | **1.067** | 1.057 | +1.0 | +6.0 | $94.3 | $48.04 | **$94.3** | $141.1 |
| 2024 | LI | 5,145 | 138 | 990 | 6,273 | 5,348 | **1.173** | 1.117 | +5.6 | +6.3 | $2.4 | $48.04 | **$48.04** | $43.2 |
| 2025 | NYC | 9,187 | 5 | 400 | 9,592 | 8,673 | **1.106** | 1.078 (implied, §6) | +2.8 | +8.3 | $57.8 | $28.65 | **$57.8** | $131.8 |
| 2025 | LI | 5,145 | 138 | 990 | 6,273 | 5,423 | **1.157** | 1.122 (implied) | +3.5 | +4.1 | $6.4 | $28.65 | **$28.65** | $51.4 |

Readings, pre-stated:
- **P1 resolves to the first branch.** The model's 2025 NYC position (1.106) is below the
  1.132 threshold, so the NYC gas_st cohort (946.0 MW, 5 units) is expected to PASS at a
  settled $57.8/kW-yr (× 0.93 = $53.8 ≫ the ~$35 bar) and NOT fire; the Rest-of-State
  855 MW fires again. **Expected FC-3: `retire.total_gw` ≈ 2.31 (+35 %), `false_retire`
  ≈ 1.11 GW / 0.48; `gas_st` model 0.855 GW; LOYO −2023 / −2024 folds' false ≈ 0.88 GW,
  −2025 ≈ 0.35; T-R10a/b still FAIL (gas_st still the first mover).** P9 stays (c) YES,
  (a) NO, (b) NO.
- **P4 (positions vs the market): expected to HOLD on the bare census** — every locality
  within +0.5…+5.6 pts of the published position (the 2023 NYC reading is +5.0 if the
  416 MW of announced gas_ct are still entering, as the runner has them). The
  SCR-adjusted information row overshoots (+4…+8 pts), which says the market's counted
  ΣICAP sits BELOW the Gold Book summer capability (DMNC / ICAP-ineligible / mothballed
  units) by about the SCR term; recorded, not adjusted for.
- **P6 (the price observable, the flip condition's limb (iii)): expected to FAIL.** At the
  model's positions the NYC settled price reads 0.47 / 0.67 / 0.44 of the published NYC
  spot (2023 / 2024 / 2025); even at the published positions the annualized curve reads
  0.69 / 0.73 / 0.60 (§2.4: the ARV-at-1.0 convention against a two-season reference-
  point construction, plus monthly-position variation). LI prices settle at the NYCA
  price in every year (the locality curve reads $2–7 at 1.16–1.17, below NYCA), which
  matches the SOM's own narrative ("the Long Island price was set by the NYCA price in
  all months of 2023/24"). **The expected recommendation is therefore DO NOT ARM on limb
  (iii), with the cause named as the shared annualization construction (a CR-3 object,
  identical in both arms, not this lane's) — while the mechanism moves FC-3 in the
  pre-stated direction.** If the A/B's NYC price lands within 1.5× in every year, the
  recommendation flips to ARM; the condition is fixed now either way.
- **The 2023 NYC price is the one that decides nothing:** $89–128 > $63 NYCA, but the
  2023 screen fails nothing in the comparator, so no 2023 row can move.

### 8.3 The census check (STOP condition §10 — cleared)

| CY | Gold Book Zone J summer capability | of which NJ-sited (Linden Cogen, Bayonne EC — Zone J resources) | model NYC fleet ICAP | Δ model − Gold Book | Gold Book Zone K | model LI | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 9,231.9 | 1,391.1 | 9,187 (9,603 with the 416) | −45 (+371) | 5,005.7 | 5,145 | +139 |
| 2024 | 8,718.9 | 1,335.7 | 9,187 | +468 | 5,072.5 | 5,145 | +72 |
| 2025 | 8,704.7 | 1,353.0 | 9,187 | +482 | 5,195.5 | 5,145 | −50 |

The model's NYC fleet already carries Linden Cogen (p50006, 915 MW) and Bayonne Energy
Center (p56964, 598 MW) as NYC units — the master plant registry places them electrically
in Zone J — so the NJ-siting concern of §8.1 P4 does NOT arise. The +468 / +482 MW in
2024–2025 is the 2023–24 Peaker-Rule / DEC exit set the Gold Book has dropped and the
2020-vintage hindcast fleet still carries (the reachable-set question of the retirement
scorer, not a census defect). LI is within 3 %. **STOP condition not triggered.**
The published TSL-floor consistency assertion (`LCR ≥ TSL floor`) holds in every
committed row (NYC 0.817/0.804/0.785 vs floors 0.745/0.743/0.718; LI 1.052/1.053/1.065
vs 0.937/0.953/0.939).

### 8.4 Cache keys — appended after the build, before any solve

_(filled by this lane once the field exists; nothing below this line was written before
the code.)_

## 9. Sources fetched this session (sha256)
| document | sha256 | used for |
|---|---|---|
| NYISO Installed Capacity Manual (icap_mnl.pdf, 281 pp.) | `b0104a503be85aa705250221360fd1016addaee6ccf41a78aed7fe488659a497` | §2.6 locational translation factor / UCAP requirement (manual p.7); §4.9.6 UDR table (p.94); §5.15.2 Spot Market Auction locality clearing rule (p.206) |
| Demand Curve Parameters 2025-2026 | `175492d0037ce8d6c3f99de59746505818647df5a67448af20e51cd399b7280c` | §6 item 1; §5.5 gross CONE 2025/26 |
| Annual Update for 2023-2024 ICAP Demand Curves (ICAPWG 2022-11-14) | `89d6ce92ba9e009814e9fba79e07bc4b120f47e407ef69ecec773340a9db76f5` | §2.4 / §5.5 (p.31) |
| Annual Update for 2024-2025 ICAP Demand Curves (ICAPWG 2023-11-17) | `80d557cbb22f53646a033ea586ab9b2a809721b3f69947bfa4e4ef3ba3df5271` | §2.4 / §5.5 (p.30) |
| NYISO 2023-2024 LCR Report | `d8c2489694c00af17f41f0b5a283beff3320affa8a01ce549d255ac3953f92aa` | §2.1 TSL-floor table |
| NYISO 2024-2025 LCR Report (Apr-2024 revision) | `6ca1017f3c0a5f5747df0d7910c9123c59553cce0ee5252b6c4d40fa0e78ba46` | §2.1 (corrected Zone J derating factor 2.89 %) |
| NYISO 2025-2026 LCR Report (Clean) | `97c357287863e9e98305d0985244e252114a794df08f939fe9d153e0d2257039` | §2.1 (table is an image; MW from the TSL sheet below) |
| Final 2025-2026 TSL Floor Values (icap, 2024-11-04) | `59f1a0b1f5365ad441e79e084fb36f6da1366ad5117830faeded83967f5840ae` | §2.1 2025/26 peaks, derating factors, SCR MW, ICAP requirements |
| NYISO 2023 SOM (Potomac, 2024-05-13) | `e240893a62c6f49a1d44fbe090c502501972d8db6333d609f49b3905d0f25167` | §2.5 Table 9 margins |
| NYISO 2024 SOM (2025-05-14) | `d2b27a93269dbf4d54ffad9ba3d4b721784b7b9c75ad80780c12aad94d3b3a04` | §2.5 Table 11 margins |
| NYISO 2025 SOM (2026-05-19) | `80c27d0b75e4c0ecb3c1ad69b3b6e2bea6797f1c0b4c9abce37f6fefaf4e218c` | §2.5 / §6 Table 9 (the carry-over) |

## 10. The seam list for the build (this lane, after this document is pushed)

| seam | change |
|---|---|
| `config/scenarios.py` | `locality_capacity_curves: bool = False` (end of field list); `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` at `"False"`; `TIER_TAGS` 1; backcast coercion to the dataclass default (kept in a hindcast); `__post_init__` raises with `capacity_deliverability_limits` on NYISO (§5.2) |
| `config/capacity_market.py` | `LOCALITY_MARKET_DESIGN_VINTAGES` (NYISO → NYC / LI vintage tuples, §2.4), `NYISO_LOCALITY_UDR_ICAP_MW` (§2.3), `NYISO_LOCALITY_GROSS_CONE_BY_ISO` (§5.5), `LOCALITY_ZONE_MEMBERSHIP` derived from the crosswalk's leaf rows; constants facade re-exports |
| `model/capacity_evolution/retirements.py` | `locality_capacity_curves_armed`, `locality_capacity_positions(iso, year, fleet, config, wind_by_zone, solar_by_zone, storage_by_zone) -> dict[L, LocalityPosition]`, `locality_prices_by_zone(...)` (the stacking max per zone), `capacity_revenue_per_mw_yr(..., locality_price_per_firm_mw_yr=None)`; `apply_economic_retirements(..., locality_prices_by_zone=None)` |
| `model/capacity_evolution/new_entry.py` | thermal locality siting leg (§5.5) + `_vre_cap_payment` zone price; `apply_economic_new_entry(..., locality_prices_by_zone=None, locality_cost_ratio_by_zone=None)` |
| `model/storage.py` | `compute_storage_capacity_value(..., locality_price_per_firm_mw_yr=None)`; `apply_storage_new_entry(..., locality_prices_by_zone=None)` (load-share weighting) |
| `model/capacity_evolution/evolve.py` | thread the two dicts into the screens |
| `runner.py` | compute once per year beside `curve_reserve_position` (the entering fleet, the zonal `wind_cap` / `solar_cap`, `storage_units` by zone); ledger block `locality_capacity` (§7); pass to `evolve_fleet` and `apply_storage_new_entry` |
| `scripts/run_capacity_hindcast.py` | `--locality-capacity-curves` (BooleanOptionalAction, `None` inherits), `FromConfig` meta row |
| `scripts/register_forecast_run.py` | `VERDICT_MAP` row `nyiso-2021-2025-realized-t1h-d59-locality` → `nyiso-t1h-d59-locality` |
| data | `demand-curve/nyiso/nyiso.csv`: `gross_cone` rows 2023-2024 / 2024-2025 / 2025-2026 × {NYCA, G-J, NYC, LI} (12 rows) + README block; `regenerate_clean.py capacity-market-demand-curve` green |
| `.gitignore` | evolution-ledger carve-out for `nyiso-2021-2025-realized-t1h-d59-*` |
| matrix (rule 28c) | base row `locality_capacity_curves` (cat capacity, mode F) + a cell in all six shards; NYISO `fc: O` after measurement; `check_mechanism_matrix.py --base origin/main` green |
| tests | `tests/unit/model/test_capacity.py::TestNyisoLocalityCapacityCurves`: trivial 1-gen/1-zone cases first; curve rows reconcile to csv per locality; §2.6 identity; stacking max; default-off byte-identity incl. the same-object price; other-ISO inertness; the Part-B exclusivity raise; backcast coercion / hindcast keep / distinct key; the UDR dating; the TSL consistency assertion; the thermal siting tie rule |
| `docs/capacity-deliverability-wiring.md` | a paragraph: the NYISO instance is `locality_capacity_curves`, why the TSL is not supply for NYISO |

STOP conditions (the lane halts and routes, never absorbs): the instrument's census check
(§8.3) shows a NYC ICAP supply that differs from the Gold Book Zone-J summer capability by
more than the SCR + UDR terms can explain (a fleet-assignment object — the backcast lane's
keeper shard, COLLISION clause); a locality curve row that does not reconcile; any
temptation to add a scalar.
