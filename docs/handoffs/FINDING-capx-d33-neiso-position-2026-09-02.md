# FINDING — capx D33: the NEISO position defect decomposed — the accreditation basis is (approximately) the published one; the +21/+6/+7 is dominated by a REQUIREMENT-DENOMINATOR artifact (a single-vintage composite ratio held flat across delivery years whose published Net ICRs are already committed in-repo), and the model's census supply is actually SHORT of what the real FCAs cleared

**Lane:** capx D33 (the NEISO half of D28's position defect; NEISO-RC-R §10.4(2)
executed). Branch `claude/capx-d33-neiso-position-8e9nzk`. **Docs only, ZERO
solves:** every number below is read from a committed artifact (the
`neiso-2023-2027-crossover-rcrepair` evolution ledgers, the R2 demand-curve
intake rows, the icr-ara extract, `capacity_market.py` registry values) or
computed by evaluating HEAD's own committed curve machinery
(`evaluate_demand_curve` / `resolve_demand_curve_vintage`) on those artifacts —
pure config evaluation, no LP. No mechanism, no `ScenarioConfig` field, no
matrix cell, no keeper/board/verdict/marker write, no `neiso-t3` row, no FC-6
touch (D35/D38 own those). No fetch was performed (no intake is funded for
NEISO); the one tightly-scoped intake ask this lane surfaces is FILED in §6 and
stops there.

## 0. Verdict (one paragraph)

RC-R §10.4(2) routed two candidate causes for the model's long NEISO position —
the accreditation basis, and cleared-vs-qualified. Measured, **neither is the
dominant cause.** (i) The accreditation basis is **adjudicated approximately
published-faithful**: the model's thermal firm MW is EIA-860 **net summer
capability** × 1.0 (`eia860.py:1036-1038` — the Phase-0 finding's "firm =
nameplate" shorthand is corrected here), which is the same demonstrated-rating
family as ISO-NE's Seasonal-Claimed-Capability-median Qualified Capacity
(tariff §III.13.1.2.2.1.1, R5b research), and the model's census supply lands
**within −3.6 % of the real FCA's cleared quantity at the 2023 entry point —
SHORT of it, not long** (32,735 vs 33,956 MW on the common convention). (ii)
What actually produces +21/+6/+7 is the **requirement denominator**: HEAD
resolves the NEISO adequacy requirement as `peak × 1.028607` — one composite
ratio built from the CCP-2026/27 ARA-3 restatement (`(1 − 2,639.682/30,050) ×
(30,050/26,648)`) — applied to **every** delivery year, while the published
per-CCP Net ICRs (already committed, FCAs 11–18) fell 32,490 → 30,550 MW over
the window and the model's hindcast weather-year peaks sit far below the
FCA-vintage 50/50 forecasts. In 2023 the model's requirement is **6,018 MW
(−18.5 %) below the published Net ICR**, worth **+23.8 points** of the +21.4
gap on its own; the requirement term decays to +2.0–2.5 pts at the 2026/27
anchor vintage exactly as a frozen-vintage artifact must. The oscillation is
then endogenous: the too-small requirement inflates the floor's exit budget
(cap 6,263 MW where the published requirement leaves ~0.5–1.9 GW), the 2024
wave crashes the supply term to −17.1 pts, the dip over-pays the curve
($116/kW-yr entering 2026 vs real $31.08), 1.2 GW of storage plus CT entry
rebounds it, and the terminal year ends +3.7 pts supply-long. **One denominator
defect, two endogenous supply excursions — not two independent defects.** The
repair is formulaic and mostly in-repo already: devintage the requirement onto
the published per-CCP Net ICR series exactly as PJM's FPR path already does
(§4 R-A), align the curve-evaluation convention (§4 R-B), and devintage the two
frozen side-cars (imports, DR) when the one filed intake lands (§6). Sign
discipline §5: at the repaired denominator the 2023-entry curve payment is
**≈ the real clearing price** ($28 [0–67] vs $24.01), capacity revenue in long
years moves UP, retirements get HARDER, and the floor's wave budget collapses
~80 % — none of which sized anything here.

## 1. The modelled object (what exactly was measured)

One seam prices adequacy for all three screens (D28 §1, D36 §5):
`MarketDesign.capacity_price_per_firm_mw_yr` evaluated at
`capacity_reserve_position = accredited_firm_capacity_mw /
resolve_adequacy_requirement_mw` (`adequacy.py:346-393`), once per year on the
entering fleet. For NEISO at HEAD:

- **Numerator** (`accredited_firm_capacity_mw`, `adequacy.py:260-343`):
  thermal `pmax × 1.0` (`claimed_capability` basis,
  `THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"]`,
  `retirements.py:1159-1167` — QC has no EFORd derate, R5b), where `pmax` is
  EIA-860 **net summer capability**, nameplate-filled only when missing
  (`eia860.py:1036-1038`); wind × 0.16 and solar × 0.18 (**generic**
  `RENEWABLE_CAPACITY_CREDIT` — `RENEWABLE_CAPACITY_CREDIT_BY_ISO` carries no
  NEISO entry); conventional hydro × 0.7352 (published SCC aggregate ÷ model
  nameplate — the capx-S4 intake, `capacity_market.py:2933`); storage at
  duration-ELCC; **+ 409.31 MW** firm imports
  (`ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]` — CCP 2026/27 net import CSO incl.
  ARA 3, held flat for every year).
- **Denominator** (`resolve_adequacy_requirement_mw`,
  `retirements.py:1077-1129`): NEISO has no published-FPR entry
  (`FORECAST_POOL_REQUIREMENT_BY_ISO` is PJM-only) and no ICAP→UCAP ratio, so
  every year takes the fallback composite `peak × (1 − f_DR) × (1 + PRM)` =
  `peak × 0.912157 × 1.127664` = **`peak × 1.028607`**, with both factors
  anchored to the SAME single vintage — the ARA-3 restatement of CCP 2026/27
  (`PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"] = 30,050/26,648 − 1`;
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"] = 2,639.682/30,050`).
  Algebraically the construction IS the published one — `requirement =
  (Net ICR − DCR CSO) × peak/CELT_peak` — **at exactly one delivery year.**
  Every other year inherits that year's ratio.
- **Curve x-convention:** the R2 vintage curves' x is **cleared MW ÷ Net ICR**
  (`_NEISO_MRI_CLEARING_POINTS`, `capacity_market.py:980-1001` — the raw
  convention, demand resources IN the quantity, Net ICR un-netted), while the
  position fed to them is the DR-netted net convention above. At 4.5 % surplus
  this mis-pairing adds ~+0.4 pts; at the 2023 position, +2.3 pts (§2).

Peaks: the crossover's 2023–2025 ledger peaks (23,475 / 24,255 / 25,898 MW)
are weather-year realized peaks; 2026–2027 (26,234.7 / 26,575.7) are grown
forecasts that land within −1.6 %/+0.6 % of the CELT 50/50 pairs the committed
ARA extract carries (26,648 / 26,417) — so the peak half of the denominator
artifact is a **hindcast-years problem**; the forecast side inherits mainly the
ratio-vintage half.

## 2. The reconciliation — model vs real FCA, per delivery year

All model rows from the committed `neiso-2023-2027-crossover-rcrepair` ledgers
(post-evolution accredited firm = `peak × (1 + reserve_margin)`); all real rows
from the committed R2 intake (`demand-curve/neiso/neiso.csv`). Model year *y*
maps to CCP *y*–*y+1* (FCA *y−2009*). Positions: **net** = HEAD's convention
(`firm/(peak × 1.028607)` — the D28 rows, reproduced exactly); **raw** = the
FCA convention (`(firm + DR_model)/(peak × 1.127664)` vs `cleared/Net ICR`).

| yr (FCA) | model firm | model req (net) | model supply (raw) | real cleared | model req (raw) | real Net ICR | pos net | pos raw | pos real |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 (14) | 30,410 | 24,147 | 32,735 | 33,956 | 26,472 | 32,490 | 1.2594 | 1.2366 | 1.0451 |
| 2024 (15) | 27,532 | 24,949 | 29,935 | 34,621 | 27,351 | 33,270 | 1.1035 | 1.0944 | 1.0406 |
| 2025 (16) | 26,775 | 26,639 | 29,340 | 32,810 | 29,204 | 31,645 | 1.0051 | 1.0047 | 1.0368 |
| 2026 (17) | 28,308 | 26,985 | 30,907 | 31,370 | 29,584 | 30,305 | 1.0490 | 1.0447 | 1.0351 |
| 2027 (18) | 30,019 | 27,336 | 32,652 | 31,556 | 29,968 | 30,550 | 1.0982 | 1.0895 | 1.0329 |

**The gap, decomposed** (net-convention gap = convention term + supply term +
requirement term; supply term = (model supply − cleared)/model raw req;
requirement term = cleared × (Net ICR − model raw req)/(model raw req × Net
ICR)):

| yr (FCA) | gap (pts) | = convention | + supply | + requirement |
|---|---:|---:|---:|---:|
| 2023 (14) | **+21.4** | +2.3 | **−4.6** | **+23.8** |
| 2024 (15) | **+6.3** | +0.9 | **−17.1** | **+22.5** |
| 2025 (16) | −3.2 | +0.0 | −11.9 | +8.7 |
| 2026 (17) | +1.4 | +0.4 | −1.6 | +2.5 |
| 2027 (18) | **+6.5** | +0.9 | **+3.7** | +2.0 |

Readings, each measured:

1. **The requirement term is the defect.** +23.8/+22.5 pts in 2023/24 — the
   model's raw-convention requirement sits 6,018 / 5,919 MW below the published
   Net ICR — decaying monotonically to +2.0–2.5 pts at the 2026/27 anchor
   vintage (−721/−582 MW). A frozen-vintage artifact decays to zero at its
   anchor by construction; this one does exactly that. Two published movements
   it cannot track: the Net ICR series itself fell 32,490 → 30,550 MW
   (committed rows), and the hindcast weather peaks sit below the CELT 50/50
   class the requirement was built on — 23.5/24.3/25.9 GW realized (2023–25)
   vs the 26.6-GW-class committed 2026 pair, i.e. −12/−9/−3 % even against
   that LATER, lower-demand vintage; the FCA-14/15-era forecasts were higher
   still.
   Splitting those two halves exactly needs the per-FCA paired peaks — intake
   §6(c).
2. **The supply term REFUTES the naive census-long hypothesis.** At the 2023
   entry point the model's raw-convention supply (32,735 MW = 30,410 firm +
   2,325 model-netted DR) is **1,221 MW SHORT of the 33,956 MW the real FCA 14
   actually cleared** — the census does not over-count the market; if anything
   it under-counts it (attribution §3.2). The −17.1/−11.9 mid-window values are
   not a census property at all: they are the 2024 exit wave (2,877.7 MW
   executed: 2,171.0 retirement + 706.7 Mystic derate rows, ledger-exact) —
   the screens' endogenous response to the denominator defect.
3. **The oscillator closes the loop on the entry side.** The post-wave dip
   enters the 2026 screen at position 0.9922, where the FCA-17 vintage curve
   pays **$116.14/kW-yr** against the real FCA 17 clearing of $31.08 — and the
   screens buy 1,200 MW of storage (the 2026 ledger's iron-air + li-ion adds)
   plus 226.8 MW CT, then 1,489.4 MW more thermal in 2027, swinging the supply
   term to +3.7 pts by 2027. Both supply excursions — the wave down, the entry
   back up — are priced off positions the denominator artifact displaced.
4. **The convention term is real but third-order** (+0.9 to +2.3 pts): HEAD
   evaluates net-convention positions on raw-convention curves (§1). It grows
   with surplus, so it maximally inflates exactly the long years the $0
   readings occur in.
5. **Cross-validation.** The curve machinery evaluated at the REAL positions
   reproduces the real clearing prices to the cent in all five years
   ($24.01/$31.33/$31.09/$31.08/$42.96) — the R2 curves are point-exact at the
   auctions' own positions, re-confirming D28's "curve exonerated" with this
   lane's independent arithmetic; and the model-position rows reproduce D28 §2
   ($0/$0/$81.19/$15.11/$0) and RC-R §10.2's "the new curve contributing
   $34/kW-yr at 1.034" ($34.30 at the 2025 entering position 1.0335) exactly.

## 3. Adjudication of the two routed halves

### 3.1 Accreditation basis: approximately published-faithful — NOT the repair target

- **Thermal.** `pmax = net_summer_capacity_mw` (nameplate-filled only when the
  summer value is absent/zero, `eia860.py:1036-1038`) × accreditation fraction
  1.0. ISO-NE's Qualified Capacity is the 5-year median of summer Seasonal
  Claimed Capability with **no EFORd derate** (tariff §III.13.1.2.2.1.1,
  quoted in the R5b research README) — a demonstrated net-summer rating. The
  model's basis is therefore the right FAMILY (net summer demonstrated, no
  outage derate) even though it is the EIA-860 rating rather than ISO-NE's own
  SCC median. The Phase-0/RC-R shorthand "`claimed_capability` makes firm =
  nameplate" (`FINDING-capx-neiso-rc-phase0-2026-08-30.md` §0.2/§3.2) is
  hereby corrected: the ×1.0 multiplies **net summer capability**. The FOM
  ladder's allocation consequence there is unaffected (no unit ATTRIBUTE
  modulates the ladder either way).
- **Hydro** is already accredited on ISO-NE's own per-resource published record
  (0.7352 = Σ summer SCC / model nameplate — the capx-S4 construction), and
  **storage** on the duration-ELCC table. Neither moved the reconciliation
  (hydro 1,383–1,396 firm MW; storage 1,584–2,592).
- **Wind/solar** are the one basis divergence with a name: generic 0.16/0.18
  where ISO-NE's published basis is the intermittent QC (median output over
  reliability hours, per-asset, in the same SCC workbook the hydro intake
  already parses). Materiality TODAY: 744 firm MW of a 30.4 GW ledger —
  second-order for this window, first-order for the golden's out-years (37 GW
  VRE by 2050). Repair §4 R-D.
- **Verdict:** the numerator construction is not the artifact. Its residual
  audit (EIA-860 net-summer vs ISO-NE per-asset SCC/QC, aggregate) is exactly
  one column-sum of the §6(d) workbook extract.

### 3.2 Cleared-vs-qualified: inverted from the routed hypothesis, and the wedge is named

The routed question assumed the census counts capacity the FCA did not clear.
Measured at the 2023 entry point the sign is opposite (supply −1,221 MW vs
cleared). Attribution of that shortfall, each piece named with its published
source (exact MW need §6(a)-(b); brackets from committed values only):

- **Demand resources:** the model nets its single-vintage 2,325 MW-equivalent
  (scaled 2,639.682) where the FCA-14-era DR CSO was materially larger
  (committed points: FCA-17 initial 2,940; ARA-3 2026/27 2,639.682; CCP
  2027/28 2,604.224/2,540.066 — a DECLINING series whose 2020-21-era head is
  not in-repo; bracketed [2,600, 4,000] in §5's arithmetic).
- **Imports:** 409.31 MW held flat (CCP 2026/27 ARA-3 net import CSO) where
  the FCA-vintage import CSOs of the early window were larger (the committed
  2025-CELT point for the SAME CCP is already 564.1 MW at the FCA-nearer
  vintage — the ARA restatement direction; FCA 11 cleared 200 MW on the New
  Brunswick interface ALONE at a separated price, committed auction-price
  row). The early-window gap is plausibly 500–900 MW; series = §6(b).
- **New-entrant CSOs** the operable census cannot yet carry, vs **energy-only
  census units** holding no CSO — opposite signs, neither measurable in-repo
  (§6(a) carries both: per-FCA qualified/cleared/de-list splits).
- **The de-list wedge (qualified − cleared)** remains the real market's
  supply-withholding mechanism the model's census evaluation cannot represent
  (D28's half (ii), the cross-ISO clearing-half question). This lane's
  contribution is the measured bound: whatever the wedge's size, it is NOT
  what makes the model long — the model is not even at the market's cleared
  quantity, let alone its qualified one. The per-FCA qualified totals (§6(a))
  would size the wedge exactly; the in-repo confirmed-retirements registry
  (the de-list tracker intake) carries the unit instruments but no per-FCA MW
  aggregates.

### 3.3 The artifact: the requirement denominator (and its convention seam)

`peak × 1.028607` is the published construction evaluated at one vintage and
frozen. It is not wrong AS a 2026/27 number — it is wrong as a **series**: the
FCA requirement is a per-delivery-year published quantity (five committed Net
ICR rows across the window, six more back to FCA 11), and the composite
tracks none of its movement. The convention seam (§1) compounds it: even a
correct net-convention position would be evaluated on curves whose x is the
raw convention. **This is the position defect.** Both halves are repairable
from the committed record alone (§4).

## 4. Repairs — identified formulaically (rule 13), never from the residual

Routed to the director for chartering (this lane lands none of them; a repair
lane arming R-A/R-B takes the rule-28 duties — the requirement resolution is
solve-affecting, so its lever gets a matrix row + per-ISO cells, default-off,
and its verdict is scored leave-one-year-out per rule 22 before any keeper
moves).

- **R-A — devintage the requirement (load-bearing).** Resolve the NEISO
  adequacy requirement from the **published per-CCP Net ICR series** exactly
  as `resolve_adequacy_requirement_mw` already prefers PJM's published FPR
  over the composite (`retirements.py:1086-1096`), with the card C-A hold-last
  convention beyond FCA 18 (the last auction ever held — the FCM sunsets;
  CAR-SA's successor parameters, expected Q4 2026, become the series'
  continuation on publication, rule 23). Two admissible shapes: (i)
  **absolute published MW** for delivery years ≤ the last published CCP —
  `requirement = Net ICR − DCR CSO` (net convention) with the model's peak
  dropping out, matching the auction's own denominator exactly; (ii) **ratio
  form** `(Net ICR − DCR CSO)/CELT_peak_ccp × model peak` — the current
  algebra, per-CCP-vintaged. Shape (i) is constructible TODAY for FCAs 11–18
  from committed rows (DR CSO committed for 2 of the 5 window years; §6(b)
  completes 3); shape (ii) additionally needs the per-FCA paired peaks
  (§6(c)). Forward story (rule 13): the requirement is a recurring published
  planning quantity that regenerates every capability year and responds to
  load/BTM-PV/tie conditions by construction.
- **R-B — one convention for position and curve (land WITH R-A).** Either
  feed the raw-convention position `(firm + DCR CSO)/Net ICR` to the
  raw-convention curves, or re-normalize the vintage curves' x onto the
  net convention — one basis on both sides of `evaluate_demand_curve`. Sized
  +0.4 to +2.3 pts (§2 row 4); identified from the curves' own committed
  derivation (x = cleared/Net ICR).
- **R-C — devintage the two frozen supply side-cars (with §6(b)).**
  `ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]` and
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]` become the per-CCP CELT
  4.1 series (net import CSO; DCR CSO) instead of single ARA-3 points — same
  source class the current values already cite, extended across vintages.
- **R-D — ISO-NE-published intermittent accreditation (with §6(d)).** Replace
  the generic wind 0.16 / solar 0.18 with class aggregates of ISO-NE's own
  per-asset intermittent QC from the full SCC workbook — the EXACT committed
  hydro construction (`HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"]` = Σ SCC /
  model nameplate) extended from unit types HDP/HDR/HW/HL to all types. The
  registry's own design comment ("a generic value must never masquerade as an
  ISO's published basis") is the standing authorization to prefer this.
- **R-E — thermal-basis residual audit (measurement only, no mechanism).**
  One aggregate: Σ EIA-860 net-summer (the model census) vs Σ summer SCC (the
  workbook) over matched assets — bounds whatever daylight exists between the
  two demonstrated-rating vintages. Expected small (§3.1); if it is not, that
  is a discovered data question, not a knob.

## 5. Consequence for the FCA-curve revenue leg (rule-14 sign discipline)

Arithmetic consequence at the **as-solved census** (supply frozen at the
ledger rows; DR bracketed [2,600, 4,000] MW for FCAs 14–16, committed points
for 17/18), using HEAD's own vintage curves:

| yr (FCA) | HEAD pays | at repaired denominator (R-A(i)) | real cleared |
|---|---:|---:|---:|
| 2023 (14) | $0 | **$28.0** [0 – 66.8] @ pos 1.042 [1.017–1.067] | $24.01 |
| 2024 (15) | $0 | $167.2 @ 0.919 [0.898–0.941] | $31.33 |
| 2025 (16) | $81.19 | $148.8 @ 0.945 [0.922–0.969] | $31.09 |
| 2026 (17) | $15.11 | **$32.2** @ 1.0345 | $31.08 |
| 2027 (18) | $0 | $0 @ 1.0742 | $42.96 |

- **Where the census is clean (2023 entry, before any endogenous response),
  the repaired denominator alone puts the model ON the real market:** position
  1.042 vs real 1.0451, curve payment ≈ the real clearing price. The same
  holds at the anchor-adjacent 2026 row ($32.2 vs $31.08). The 2024/25 rows'
  over-payments are NOT a repair prediction — they price the as-solved ledger's
  post-wave fleet, and the wave itself is the artifact's product: at the
  repaired 2023 requirement the floor's admissible exit budget is `30,410 −
  (32,490 − DR)` ≈ **0.5–1.9 GW where HEAD's was 6,263 MW** — the mass-exit
  wave that produced those rows cannot recur at ~20 % of its budget cap. The
  2027 row's $0 correctly prices the residual +3.7-pt supply overshoot (the
  entry wave), which a re-solve under R-A would also damp at its source (the
  $116 dip-year signal becomes ~$31–45).
- **Direction, stated so it cannot be traded (D28 §5 discipline):** shortening
  the position moves capacity revenue **UP** in the long years ($0 → $24–43
  class) and **DOWN** in the dip years ($81–116 class → $31–45 class) — it
  kills the oscillator, in both directions at once. Revenue UP makes NEISO
  retirements HARDER and entry EARLIER; the floor budget collapse makes the
  wave SMALLER. Against the RC-R vintage-basis exit level (+24.2 % over) the
  net exit-level movement is not predictable from this arithmetic and was not
  used to size anything: every quantity above is a published number or a
  committed ledger row.
- **Storage RA leg (D36 §5's bound, re-confirmed):** the same seam prices the
  storage stack, so R-A moves the RA leg by at most the D36 bracket (up
  ≤ $18/kW-yr li-ion / ≤ $31 iron-air in long years; down $20–57 in the dip
  years) — second-order against the arbitrage leg, unchanged conclusion: the
  stack clears later, not earlier.

## 6. The filed intake ask (FILED, not fetched — one source class, four extracts)

Everything below is the ISO-NE FCA/CELT published-record class the R2 intake
and the icr-ara extract already draw on (D28 §6.4 sourcing; sha-identity
discipline per the R2 README). Tightly scoped: ~25 numbers plus one workbook
re-parse, no new source class, no tariff research.

- **(a) Per-FCA (14–18) auction quantity splits:** existing + new QUALIFIED
  capacity MW; cleared demand-resource CSO; cleared import CSO; retirement /
  permanent de-list MW. Sources: the FCA results filings / initial-results
  press releases ALREADY sha-pinned in the R2 README identity table +
  ISO-NE's informational filings for each FCA. Completes §3.2's attribution
  and sizes the qualified-vs-cleared de-list wedge exactly.
- **(b) Per-CCP CELT Table 4.1 CSO summaries for CCPs 2023-24 … 2025-26**
  (DCR CSO total; net import CSO) from the 2023/2024 CELT vintages — the
  exact extract class already committed for 2025/2026 CELT in
  `data/raw/capacity-market/icr-ara/neiso/ara_requirement_values.csv`.
  Completes R-A(i)'s DR netting and R-C's series.
- **(c) Per-FCA ICR-related values: the paired 50/50 summer peak** (ICR,
  HQICC, Net ICR are already committed for every FCA) — the per-FCA ICR
  filings (`icr_for_aras.pdf` class; likely one sheet of the already-pinned
  `summary_of_historical_icr_values.xlsx`). Enables R-A(ii) and splits §2's
  requirement term into its peak-basis and ratio-vintage halves exactly.
- **(d) The full-workbook SCC extract** (all unit types, not only hydro) from
  the ALREADY-fetched, sha-pinned August-2026 SCC workbook via the committed
  `scripts/data/fetch_isone_scc_hydro.py` pattern — per-asset summer/winter
  SCC for R-D's intermittent class factors and R-E's thermal audit.
  (The workbook is re-fetchable by the committed script; the extract is the
  committed deliverable, matching the hydro precedent.)

## 7. Cross-read: GOLDEN-2 §6.2 and D36 §5 — one position object or several?

**One object, three consumers, two very different exposure windows.**

- **D36 §5 asked and answered "one mechanism?" for the storage RA leg — yes**,
  and this lane's decomposition inherits that seam identity: R-A/R-B move the
  retirement screen, the thermal-entry screen and the storage RA leg through
  the single `capacity_reserve_position` value. There is no second NEISO
  position object to repair. D36's quantified bracket for the storage
  consequence stands unchanged (§5 above).
- **GOLDEN-2 §6.2 measured the stakes of this surface:** the golden-1→golden-2
  delta was DOMINATED by the RC-R capacity-revenue intake expressing through
  the same term — re-timing 3.4 GW of exit waves and 3 GW of entry with zero
  instrument rows. R-A is a larger movement of the same surface than the R2
  curve intake was in the hindcast years (+20-pt denominator vs the curve's
  sub-point reshaping at long positions), so the golden's exit/entry
  composition is expected to re-time again under it — the GOLDEN-2 caveat
  (ii) discipline (the D14 composition defect underneath) carries.
- **The exposure split matters for chartering:** the denominator artifact is
  anchored at CCP 2026/27, so the CROSSOVER/hindcast window (2023–25) carries
  the 9–24-pt defect while the golden's forecast years carry only the
  +2–2.5-pt anchor residue, the convention term, and the frozen side-cars —
  until CAR-SA publishes a successor requirement the hold-last must track.
  R-A therefore primarily repairs the crossover lane (FC-4 pricing, the D14
  composition story, RC-R's §10.2 oscillator) and hardens the golden's
  forward requirement discipline rather than re-drawing its 2026-vintage
  positions.

## 8. Governance attestation

- **ZERO solves; no fetch.** Sources: the committed
  `neiso-2023-2027-crossover-rcrepair` evolution ledgers (the R4 tracked-set
  bundle), `data/raw/capacity-market/demand-curve/neiso/neiso.csv` +
  `icr-ara/neiso/ara_requirement_values.csv` + `scc/neiso/` +
  `elcc/neiso/` + `accreditation-filings/neiso/README.md` (R5b),
  `auction-price/neiso/neiso.csv`, `confirmed-retirements/neiso.csv`, and
  `src/market_sim/config/capacity_market.py` / `model/capacity_evolution/`
  at HEAD, cited by path/line. Curve payments were computed by importing
  HEAD's own `evaluate_demand_curve` + `resolve_demand_curve_vintage` on
  those committed inputs (pure config evaluation; validated by reproducing
  the five real clearing prices at the real positions to the cent, and D28's
  own pay rows exactly). No out-of-training year touched; the holdout freeze
  is not implicated (nothing solved or scored).
- **No mechanism, no `ScenarioConfig` field, no matrix cell, no board /
  verdict / keeper / marker / `neiso-t3` / FC-6 write** — rule 28 does not
  fire for this lane; §4 names the duties the repair lane will owe. Rule 15
  does not fire (no run produced). The deliverable is this finding; the D28
  §5 / charter sign discipline is restated in §5 where it bites, and no
  quantity anywhere in §4–§6 was sized from any residual.
- **Collision check at write:** GOLDEN-2 is CLOSED (registration complete);
  D35 owns the FC-6 P2 row and D38 the FC-5 disposition file — neither
  surface touched. The Phase-0/RC-R correction in §3.1 ("nameplate" →
  "net summer capability") is recorded HERE, not edited into the parent
  finding (append-only discipline; the parent's mechanism conclusions are
  unaffected).
