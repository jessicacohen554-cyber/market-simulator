# FINDING (caiso-111, FRESH-LOOK SCOPING): the belly over-import has TWO structural drivers, not one — a NEW **export-floor asymmetry** (the model's WECC node is inject-only, so it imports in the ~700–900 belly hours/yr reality EXPORTS) accounts for ~half the belly wedge, alongside the import-depth pricing the prior lanes chased. BTM/demand-netting is CLEAN (not a driver); solar is +2.5–3 TWh over purely from Lever-D UNDER-curtailment; zone granularity is NOT the lever. A field survey shows every production/academic CAISO model uses a BIDIRECTIONAL, endogenously-cleared WECC import — exactly the structure we lack — and none publishes error bars as tight as our C-gates. The endogenous WECC node (caiso-110) is REINFORCED (fixes both halves); recommended next delta is a cheap bidirectional-tie diagnostic before the full West-MC build. No mechanism armed, no solve, keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.

**Session 2026-07-21 (CAISO-111 — research/scoping charter; DERIVE-FIRST +
DERIVE-FIRST). NO SOLVE, NO LP, nothing registered.** All measurements from
committed artifacts + raw data on disk. Instrument:
`scripts/probes/_caiso111_belly_attribution.py` (keeper-proxy `caiso104_m1_B`
hourly + EIA-930 CISO extract + CAISO HSL workbook + the caiso-109 CEMS-basis
gas reconstruction). Keeper reproduces NOT-YET, fail {C3c, C4, C5a(2024
CAVEAT)} (`scripts/calibration_verdict.py --run-id 2026-07-19-caiso-102-hourfix`).

The charter asked for a fresh, broader look before pouring more sessions into
the one import-pricing mechanism: are we missing something structural (BTM
solar? demand netting? zone granularity?), and are our gates even calibrated to
what production CAISO models call "acceptable"? Both questions are answered
below with measured evidence.

---

## 0. What the fresh look had to settle

The keeper's load-bearing fail is C5a (CO2 −11.1/−9.1/−12.1 %), driven by a
~8 TWh/yr belly/daytime over-import that displaces CA gas ~1:1 (caiso-108/109
P0). Two whole lever classes are already KILLED by derive-first measurement —
CA-price observables (caiso-107) and west-wide surplus QUANTITY (caiso-109) —
so the belly transfer is genuinely endogenous to the co-evolving CA+West
fleets, and the chartered structural fix (endogenous WECC node, caiso-110)
floods on Henry-Hub-priced West thermal. Before another session on that one
mechanism, this charter interrogates R1 (BTM/solar/demand), R2 (zone
granularity), R3 (measured inputs), R4 (how others run CAISO + what
"calibrated" means), R5 (fold the WECC node in or set it aside).

---

## R1 — BTM / rooftop solar + demand netting

### (a) Demand basis is CLEAN — BTM is single-netted, not double-netted, not missing

The keeper feeds the LP the **supply-consistent** demand series
(`caiso_supply_consistent_demand=True`, caiso-80). The chain, verified in
`src/market_sim/data/eia930/demand.py`: EIA-930 CISO metered demand is measured
at the transmission level and is **already net of CAISO's ~15+ GW of BTM PV**;
caiso-80 reconstructs it CEMS-anchored; the model then dispatches **only
front-of-meter** resources against it. Annual TWh:

| year | raw 930 Demand cell | NetGen − TI identity | scored supply-consistent (= model served) |
|---|---|---|---|
| 2023 | 218.2 | 212.9 | 207.4 |
| 2024 | 223.5 | 222.9 | 212.2 |
| 2025 | 224.0 | 222.5 | 205.6 |

The model serves exactly the scored series (belly `scored − model_served` ≈ 0).
BTM PV is netted **once**, on the demand side, and the supply side carries no
BTM generator — the two conventions are the dual of each other and are **not
double-counted**. This is the same convention the field's net-load models use
(§R4). **BTM/demand-netting is not a hidden driver of the belly defect.**

### (b) The P0 "solar +2.5–3 TWh over" is entirely Lever-D UNDER-curtailment

`caiso_solar_deliverability` (Lever-D, the structural solar-curtailment derate)
is ON in the keeper, yet the model dispatches solar at ~the full uncurtailed
HSL potential:

| year | HSL potential | delivered (actual) | model | model curt | **actual curt** | **model − delivered** |
|---|---|---|---|---|---|---|
| 2023 | 39.68 | 37.17 | 39.65 | 0.03 | 2.51 | **+2.48** |
| 2024 | 47.81 | 44.64 | 47.18 | 0.63 | 3.17 | **+2.54** |
| 2025 | 53.14 | 49.66 | 52.70 | 0.44 | 3.48 | **+3.04** |

The P0 "+2.5–3 TWh over" **is** `model − delivered`, and it is exactly the
curtailment the model fails to take: actual CAISO curtailment is 2.5–3.5 TWh/yr;
Lever-D removes only 0.03–0.63 TWh. By hour, in the belly (hod 10–15) the model
curtails ~0.1–0.37 GW while reality curtails ~0.9–1.4 GW — the model runs
**+0.8 GW more belly solar** than reality. Lever-D is real (right mechanism,
rule 1) but **under-strength by ~4–40×** at the midday-penetration where it
matters (k = 0.15 / floor = 0.50 under-shoots the measured 2.5–3.5 TWh). This is
a genuine, independent, derive-first-admissible lever (the curtailment target is
a measured actual, forward-regenerable from that year's penetration), but it is
**secondary** to imports in magnitude.

### (c) Belly component ledger + the NEW export-floor finding

Model − actual, GW mean, belly (hod 10–15), the full energy balance:

| component | 2023 | 2024 | 2025 |
|---|---|---|---|
| solar | +0.81 | +0.74 | +0.92 |
| wind | +0.04 | +0.07 | +0.07 |
| hydro | −0.61 | −0.59 | −0.55 |
| nuclear | −0.01 | −0.02 | −0.01 |
| **gas (CEMS)** | **−1.21** | **−1.21** | **−1.02** |
| **net_import** | **+2.58** | **+2.63** | **+2.24** |
| dump (model-only midday curtail) | −0.12 | −0.29 | −0.16 |

The model over-imports +2.2–2.6 GW and over-solars +0.8 GW in the belly, while
under-dispatching gas −1.0–1.2 GW and under-running hydro −0.6 GW — the C5a/C4
signature. **The new result is *where* the over-import comes from.**

**EXPORT-FLOOR ASYMMETRY (new).** Reality net-**EXPORTS** in a large, spring-
concentrated block of hours; the model's `WECC_import` node is a set of
inject-only pseudo-generators (min net import = **0 MW** — the tie can never
reverse), so in exactly those hours the model **imports**:

| year | actual net-EXPORT hrs | % of yr | belly-export hrs | export mean | model min net import |
|---|---|---|---|---|---|
| 2023 | 1235 | 14.1 % | 916 | −1529 MW | 0 (cannot export) |
| 2024 | 963 | 11.0 % | 703 | −1524 MW | 0 |
| 2025 | 799 | 9.1 % | 636 | −1258 MW | 0 |

Export hours concentrate Apr–Jul (2024: 183/245/85/68 in Apr/May/Jun/Jul) —
CAISO's south-to-north spring-solar surplus, which the CAISO DMM 2024 annual
report names explicitly ("south-to-north congestion during solar hours
throughout much of the year", §R4). Decomposing the belly import wedge
(model − actual net import) into its export-hour and import-hour parts:

| year | belly wedge | export-hours part | (of which the reality<0 "floor" part) | import-hours part |
|---|---|---|---|---|
| 2023 | +2.58 | **+1.37** | (+0.69) | +1.21 |
| 2024 | +2.63 | **+1.38** | (+0.53) | +1.25 |
| 2025 | +2.24 | **+0.94** | (+0.38) | +1.30 |

In the belly export-hours the model is +3.2–4.3 GW off (actual −1.66 GW vs model
+1.6/+2.6/+1.9 GW). **~half the belly over-import wedge is the export-floor** —
the model literally cannot represent CAISO net-exporting its spring-solar
surplus to the West, so it imports instead. This is a **topology/sign gap,
independent of import pricing** (the killed lanes), and it is a *second*
independent driver alongside the import-depth pricing (the import-hours part,
~+1.2–1.3 GW). The model resolves the resulting oversupply by charging storage
harder midday and dumping ~1–2 TWh/yr — and that dump lands **entirely in the
WECC_PNW/DSW import zones (0 in every CA zone)**, i.e. the oversupply is a tie
phenomenon, not a CA-locational one (see R2).

**R1 verdict:** the belly defect is NOT a BTM/demand-netting artifact (clean).
It has TWO structural drivers — (i) an **export-floor asymmetry** (~half the
wedge; the model can't net-export) and (ii) the **import-depth pricing** the
prior lanes chased (~half) — plus a **supporting solar over-run** (Lever-D
under-curtails by 2–3 TWh/yr). Driver (i) is new and is reachable by neither the
import-depth pricing lanes nor the killed observable-conditioning lanes.

---

## R2 — Zone granularity: NOT the lever

The failing gates are C3c (scarcity tail), C4 (gas hourly), C5a (CO2) — all
belly/import-priced. Measured evidence that the residual is **system-level, not
locational**:

- **Gas under-dispatch is uniform, not pocketed.** caiso-109 §1 established the
  gas under-dispatch spans 66–70 % of all hours with the high-r/low-level
  NRMSE signature of a uniform economic de-commit — not a binding internal path
  or a local-RA pocket (which would concentrate the miss in specific hours/zones).
- **Model oversupply dumps only at the tie.** Model dump is 1.7 TWh in WECC_PNW
  + 0.5 TWh in WECC_DSW and **0.0 in every CA zone** (NP15/ZP26/LA_BASIN/SDGE/
  SP15_rest), belly and annual. The oversupply the belly defect creates is
  evacuated at the import node, not congested inside CA.
- **The defect is the tie sign/price**, which the 6-zone reduced network already
  represents at the granularity that matters (the SP15 LCR split already landed
  and moved nothing here).

Finer intra-CA granularity (WEIM/EDAM sub-areas, a binding internal path) cannot
move a residual that lives on the CAISO↔West interchange sign and price.
**Granularity is a distraction; no zone should be added for these gates.** (A
per-zone C4/C3c concentration probe would confirm this directly and is a cheap
follow-up when a full working tree is present; the committed caiso-109 evidence
+ the zero-CA-dump result already settle it.)

---

## R3 — Measured inputs that could sharpen (enumerated, ranked by value)

| candidate input | fetchable? | schema-mappable? | rule-13 forward-regenerable? | value | verdict |
|---|---|---|---|---|---|
| **Measured delivered West hub LMP** (Palo Verde + Malin, hourly) | YES — partly already on disk as the `measured_import_hub_prices` / DSW_CCGT coupling series the existing tranches use; OASIS nodal LMP fetchable for gaps | YES (existing hub-price contract) | YES (a forward West price driver) | **HIGH** — the exact input the caiso-110 West-MC fix needs; DMM 2024 corroborates the level (DSW $31 / PNW $49 mean) | **WIRE / CONFIRM FIRST** |
| WEIM/EDAM transfer + GHG-attribution data | YES (CAISO WEIM reports) | new datatype | YES (forward market) | MED — the caiso-87 "no carbon wedge" question; relevant only if the endogenous node under-fits | file (2nd priority) |
| CEC/EIA BTM PV capacity+CF series | YES (CEC IEPR, EIA-861) | new datatype | YES | **LOW** — R1(a) shows BTM is already correctly single-netted; a BTM series would only be needed to switch to the gross-load convention, which buys nothing | file (not needed) |
| Measured RA must-offer volumes | partial (CPUC RA reports) | new datatype | weak (regulatory, not a physical driver) | LOW — overlaps `caiso_ra_mustoffer`; the caiso-109 midday-gas lane | file |
| CAISO 60-day DAM/RTM disclosure | YES (large) | heavy | YES | LOW for these gates | file |

The single highest-value input is the **measured delivered West hub LMP**, and
it is largely already available — the West-MC fix is a *re-pricing using an
existing measured series*, not a new intake. (Wiring a genuinely new datatype
through `write_clean`/`read_clean` was not undertaken this scoping session
because the top candidate is already on disk; the intake to open, if the
endogenous node needs it, is the WEIM GHG-attribution series.)

---

## R4 — How other models run CAISO + what "calibrated" means there

Survey with citations. Two findings dominate: (1) **every** production/academic
CAISO representation uses a **bidirectional, endogenously-cleared** WECC import
(hurdle-rate zonal or full nodal), and **un-nets or explicitly models BTM PV**;
(2) **none publishes backcast error bars as tight as our C-gates** — planning
PCMs validate procedurally (ADS) or on the input side (RESOLVE), and the one
quantitative academic dispatch backcast accepts ~21 % price SMAPE.

| model | CAISO representation | import treatment | BTM PV treatment | validation reported | error called "good/calibrated" |
|---|---|---|---|---|---|
| **WECC ADS** (GridView, nodal) | full nodal; CAISO = 4 IOU load areas under `CA_CISO`; GE PSLF power-flow seed | **WECC-wide econ dispatch with hurdle rates** on inter-BAA interfaces (TAC from OASIS + grid-mgmt + friction); Mead/Palo Verde/Malin hubs zero export hurdle; **bidirectional** | **gross-load basis**; E3/LBNL BTM estimates added back to each BA's load + explicit DG resources added to offset | **procedural** — stakeholder subcommittee review; load reviewed vs historic shapes; final check = unserved-load + reserve tally | **no published numeric tolerance** |
| **CPUC RESOLVE** (E3) | zonal; WECC → 7–8 zones; 2024–26 cycle splits CAISO into 3 IOU zones (PGE/SCE/SDGE) with interzonal limits | **hurdle-rate zonal dispatch** from neighbor WECC zones; net-import limit 11,040 MW, simultaneous export 5,000 MW, 4,000 MW cap on import→PRM (SERVM enforces peak 4–10pm Jun–Sep); CARB 0.428 tCO2/MWh on unspecified imports | **supply-side ELCC resource, NOT netted**; gross peak reconstructed as managed net load + hourly BTM PV (CEC IEPR) | **input-side calibration** — scale zonal peaks so managed net peak matches CEC forecast | **no backcast-error tolerance** |
| **Astrapé SERVM** (CPUC IRP) | zonal, CEC forecast zones | hurdle-rate; 4,000 MW import→PRM cap enforced peak, ramping to 11,040 MW off-peak | BTM PV by CEC forecast zone (IEPR hourly); BTM storage = load modifier | reliability (LOLE/EUE) focus | reliability metrics, not price/dispatch % |
| **PLEXOS WECC** (Energy Exemplar) / CAISO stochastic PCM | full nodal; 240 historical contingencies, 1,226 monitored lines from CAISO DA/RT reports (CY2022–23); PLEXOS v8.3 | full nodal WECC co-optimization | dataset-dependent | MAE / RMSE / SMAPE used as **tools**; "historical data for benchmarking" | **no published pass threshold** |
| **NREL Cambium / ReEDS** | zonal (ReEDS BAs); CAISO within WECC | endogenous inter-regional transmission + hurdle | national BTM in load projections | scenario documentation | no backcast % tolerance |
| **Academic — PyPSA-Eur hindcast** (Karkossa et al., arXiv 2606.16486, 2020–24, 35 countries) | zonal/nodal | endogenous co-optimization | n/a (Europe) | **price SMAPE**; generation qualitative | best config (dynamic prices + rolling horizon) **20.8 % SMAPE** on daily load-weighted price (static 53.5 %); success = "well below 100 % … same order of magnitude as observed" |

**Structural features the field includes that bear on our defect:**
- **Bidirectional imports are universal.** ADS carries hurdle rates both
  directions; RESOLVE has an explicit 5,000 MW export limit. Our inject-only
  `WECC_import` node (min = 0, R1c) is a structural gap the field does **not**
  share — it is the direct cause of the export-floor half of our belly wedge.
- **Endogenous / hurdle-rate WECC dispatch is universal.** Nobody uses fixed
  import profiles for a calibrated CAISO. Our static clean-depth tranches
  (caiso-87/93/94) are the **outlier**; the endogenous WECC node (caiso-110)
  moves us onto the field-standard structure.
- **BTM PV is un-netted** (ADS gross-load + DG; RESOLVE supply-side ELCC). We
  use the equivalent net-load-minus-FOM dual convention, correctly (R1a).
- The West hub price levels in the caiso-110 West-MC fix are **corroborated by
  CAISO's own DMM**: WEIM 2024 averaged ~$40/MWh, PNW $49 (highest), Desert
  Southwest $31 (lowest) — matching the Palo Verde/Malin ~$33-mean / $56-evening
  recipe. So the West re-price is measured, not fitted.

**On our gates (the owner's question):** our C-thresholds — C5a CO2 within the
commercial band (~±7–10 %), C4 gas hourly r ≥ 0.70 & NRMSE < 0.30, C3c scarcity-
hour counts, C3b monthly-shape — are **stricter and more quantitative than
anything the field publishes for a planning PCM.** The field's notion of
"calibrated" for these models is procedural (ADS unserved-load tally) or
input-side (RESOLVE scale-to-CEC-forecast); the only published quantitative
dispatch backcast (PyPSA-Eur) treats ~21 % price SMAPE as good **and exhibits
the very same gas-under-dispatch signature we have** ("gas-fired generation is
largely avoided for most of the year … ENTSO-E historical indicates gas ran
nearly constant"; daily price spikes "not captured well"). **The gates are
ambitious, not too-loose — they should not be relaxed.** The actionable field
lesson is not "loosen the gates" but "adopt the field-standard import structure
(a bidirectional, endogenously-cleared West) that our export-floor finding shows
is the missing piece."

---

## R5 — The endogenous WECC node (caiso-110): REINFORCED, not secondary

The export-floor finding (R1c) is decisive here. The belly wedge splits ~half
export-floor / ~half import-depth, plus a supporting solar over-run. **The
endogenous WECC node fixes BOTH halves at once:** (a) it makes the tie
bidirectional, so CAISO exports its spring-solar surplus to the West node
instead of importing (fixes the export-floor); and (b) it clears the flow on the
West's endogenous price rather than a static hub tranche (fixes the depth, once
the West-MC is right). The export-floor is therefore a **second symptom of the
same missing structure** (no real neighbor that can absorb CA surplus) — it
**reinforces** the caiso-110 lane rather than competing with it. R4 shows this is
also the field-standard structure, and DMM corroborates the West price level the
fix needs. Import pricing stays central (it is the import-hours half), so the
caiso-110 West-MC fix remains the direct structural continuation — but the export-
floor half is now an independent, cheaper thing to test first.

---

## 6. Ranked surviving levers (derive-first go/no-go) + recommended next A/B

| lever | go/no-go | what it fixes | measured identification it needs | cost |
|---|---|---|---|---|
| **L1a — bidirectional tie (export sink at measured West hub)** | **GO (do first)** | the export-floor half (~+1.0–1.4 GW belly) | measured delivered West hub LMP (on disk); tie TTC (measured) | **cheap**, single-delta, interior tie so no 84-min degeneracy |
| **L1b — full endogenous WECC node (caiso-110 West-MC fix)** | **GO (continuation)** | the import-depth half + folds in L1a | West thermal re-priced to measured Palo Verde/Malin (+ CARB wedge) + ε flow_cost | larger; the chartered build |
| **L2 — Lever-D strengthening (solar curtailment)** | **CONDITIONAL GO (supporting)** | the +0.8 GW belly solar over-run (2–3 TWh/yr) | re-derive k from actual midday curt/penetration (HSL on disk) | cheap, but secondary in magnitude |
| **L3 — midday gas commitment / min-load** (caiso-109 opt B) | FILED (partial) | raises belly gas floor | measured CHP/CCGT min-load; risk C8, overlaps `caiso_ra_mustoffer` | one session |
| zone granularity (R2) | **NO-GO** | nothing (residual is system-level) | — | — |
| CA-price / west-surplus-quantity depth gates | **KILLED** (caiso-107/109) | — | none exists (year-non-stationary) | — |

**Recommended next single-delta A/B — L1a (bidirectional-tie diagnostic),
before the full West-MC build.** Give the existing `WECC_import` tie an export
path priced at the measured delivered West hub (Palo Verde/Malin), leaving
everything else byte-identical. This isolates the export-floor half — the LP
exports when CA λ falls below the West hub — and quantifies how much of the belly
wedge (and C5a) the sign-fix alone recovers, without the endogenous fleet's
84-min tie-pinned degeneracy. **Pre-registered gates** (single-delta B vs a fresh
same-machine `caiso102_repro_A`, all three years one bundle, rule 16; solves
in-session):

- **PRIMARY C5a** CO2 −11.1/−9.1/−12.1 % → toward 0 (gas TWh rises toward
  74.2/61.0/51.6), no overshoot past +7 %.
- **Net import** annual → toward actual 28.9/32.4/36.2 TWh; belly export hours
  appear (model net-exports in the spring-solar block).
- **C4** gas NRMSE < 0.30, r ≥ 0.70. **C3c** scarcity tail up.
- **GUARD** C3a mean LMP + C3b shape STAY PASS; belly/evening residuals not
  worsened. **C8** forced-share within budget (rule 20). **Rule-22** LOYO before
  any promotion.
- **KILL** → escalate to L1b (full West-MC node): if L1a recovers the export-
  floor half but the import-hours depth keeps C5a failing (the model still
  over-imports at hub/EF0 in import hours), the depth half needs the endogenous
  West price, i.e. the chartered caiso-110 West-MC fix is the continuation.

This sequences the two halves cleanly and respects the charter's "don't sink a
session into the 84-min solve until the degeneracy is fixed."

---

## 7. Verdict + what stays / what's next

- **Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.** No mechanism armed, no
  solve, nothing registered (measurement-only, like caiso-108/109).
- **New structural finding:** the belly over-import has TWO drivers — a NEW
  **export-floor asymmetry** (the WECC node is inject-only; ~half the belly
  wedge) and the import-depth pricing (~half). BTM/demand-netting is clean; the
  solar over-run is Lever-D under-curtailment (2–3 TWh/yr, supporting).
- **Zone granularity is not the lever** (residual is a tie sign/price
  phenomenon; model dump is 0 in every CA zone).
- **Field survey:** every production/academic CAISO model uses a bidirectional,
  endogenously-cleared WECC import and un-nets BTM; none publishes error bars as
  tight as our C-gates. Our gates are ambitious, not loose — keep them; adopt the
  field-standard bidirectional/endogenous West structure our export-floor finding
  points to.
- **The endogenous WECC node (caiso-110) is reinforced** (fixes both halves;
  field-standard; West price DMM-corroborated). Recommended next delta: **L1a**,
  a cheap bidirectional-tie diagnostic isolating the export-floor half, with the
  pre-registered gates above; **L1b** (the caiso-110 West-MC fix) as the
  continuation if the depth half persists.

## 8. Session artifacts
- No solve, no bundle, nothing registered. Keeper UNCHANGED.
- Reproduces from committed artifacts + raw data on disk:
  `scripts/probes/_caiso111_belly_attribution.py` (R1 a/b/c + export-floor) and
  `scripts/calibration_verdict.py --run-id 2026-07-19-caiso-102-hourfix` (the
  fail set). R4 sources: CAISO DMM 2024 Annual Report on Market Issues and
  Performance (Aug 7 2025); WECC ADS Data Development & Validation Manual;
  CPUC 2024–26 IRP RESOLVE/SERVM inputs & assumptions; Energy Exemplar PLEXOS
  WECC Nodal Dataset notes; NREL Cambium 2023 documentation; Karkossa et al.,
  "Can Optimal Dispatch Models Recreate Reality?", arXiv 2606.16486.
