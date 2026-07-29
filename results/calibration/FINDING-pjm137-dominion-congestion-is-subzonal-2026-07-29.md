# FINDING — pjm-137: **the Dominion congestion the CT leg needs is SUB-ZONAL, and PJM's own records say so three independent ways.** Only **3.1–6.3 %** of PJM's day-ahead congestion rent sits on a zonal-scale interface — `AEP-DOM`, the exact boundary the pjm-133…136 lineage has been trying to make price, is **0.04 / 0.07 / 0.24 %** of it. The constraints that dominate the hours Dominion separates are Loudoun-County 500 kV transformers and 230 kV lines with **both ends inside `PJM_Dominion`**, and there is **more price separation inside the Dominion zone (mean $6.18 / $8.68 / $16.78) than across the whole DOM–AEP boundary ($4.76 / $6.13 / $14.42)**. The zonal-congestion route to the CT leg is **CLOSED BY MEASUREMENT**.

**All four measurements were run; no LP was solved for them.** Probes:
`scripts/probes/_pjm137_dominion_ct_congestion.py` (M1/M2/M3),
`scripts/probes/_pjm137_intrazonal_ehv_spread.py` (M4). Machine output:
`results/probes/pjm137_dominion_ct_congestion.json`,
`results/probes/pjm137_intrazonal_ehv_spread.json`. Inputs are the committed
`pjm136_lossurf_B` keeper `hourly/` sidecars, the committed CAMPD unit-level
record, the committed benchmark payload, the pjm-136 zonal LMP-component
intake, and two **new** pjm-137 intakes (§2.0).

---

## §0 — the verdict in one table

| test | question | result | verdict |
|---|---|---|---|
| **M1** where the model prices NOW | did pjm-136's loss surface leave a congestion-shaped residual? | **yes, and it is the whole remainder.** The new keeper separates on `AEP_Ohio→Dominion` in **96.1 / 98.9 / 96.9 %** of hours (was 0.0 %) at a mean of **−0.54 / −0.82 / −1.43**, reproducing the measured **loss** component (−0.54 / −1.06 / −1.90) — and leaving the measured **congestion** (−3.65 / −4.42 / **−12.44**) entirely unproduced | the deficit is real and it is congestion |
| **M2** what PJM says was binding | is that congestion on a boundary an 8-zone model represents? | **NO.** Across 228,795 day-ahead binding constraint-hours, only **6.34 / 3.06 / 6.19 %** of the absolute shadow-price record sits on a named zonal-scale interface; **80.0–87.8 %** sits on monitored facilities rated **≤ 230 kV**. `AEP-DOM` is **0.041 / 0.071 / 0.236 %**. In the top-decile DOM-separation hours the dominant constraints are **PLEASNTV TX3 500 kV, GOOSECRE TX1 500 kV, PLEASNTV-ASHBURN 230 kV, ASHBURN-GOOSECRE 230 kV, BRAMBLET-EVRGREEN** — Loudoun County, **both ends inside `PJM_Dominion`** | **the route is closed** |
| **M3** does the CT leg even want congestion | do Dominion's real CTs run in congested hours, and how big is the model's price deficit there? | **yes, and it is large.** The 9-plant / 40-turbine roster (CAMPD `unitType == 'Combustion turbine'`) runs **68.3 / 54.4 / 62.4 %** of hours; CT-energy-weighted measured DOM LMP **$50.78 / $62.04 / $103.41** against the model's **$33.06 / $35.35 / $48.80** — a deficit of **$17.72 / $26.69 / $54.61**, of which the measured congestion component is **$9.09 / $12.32 / $27.73 (51 / 46 / 51 %)**. **62.4 / 64.5 / 80.0 %** of real CT energy is produced in hours with DOM congestion above $5 | the defect is price formation, and half of it is unreachable congestion |
| **M4** can the reduction carry it | how much separation lives *inside* a model zone? | **more than across the boundary.** Intra-`PJM_Dominion` EHV dispersion **$6.18 / $8.68 / $16.78** vs inter-zonal DOM-vs-AEP **$4.76 / $6.13 / $14.42** — ratio **1.30 / 1.42 / 1.16×**; > $10 in **13.0 / 17.4 / 31.6 %** of hours. Widest intra-zone pairs: **LOUDOUN vs MT STORM**, **GRNSVIL vs PLEASANT VIEW** | **no zonal mechanism can reach it** |
| **§3a** how big is the defect really | does the quoted `CT_PEAKER` actual match the benchmark? | **NO — it is ~1.9× too large.** The benchmark's own per-plant record puts Dominion `CT_PEAKER` at **3.066 / 4.048 / 5.218 TWh**, not the **7.38 / 8.68 / 9.64** every handoff and the keeper note carry; the quoted figure is those nine plants' **whole-plant** energy, which counts Doswell Energy Center's combined-cycle blocks (4.45 TWh in 2025) as peaker output. The real gap is **−2.34 / −2.67 / −2.30 TWh**, i.e. the model is at **24 / 34 / 56 %** of actual | **the target was mis-stated** |

---

## §1 — M1: the loss surface did exactly what it claimed, and the residual is congestion

`FINDING-pjm136` §1 read the *old* keeper's duals and found every Dominion-facing
link separating in **0.0 % of 26,280 hours**. Re-run on the promoted keeper
(`pjm136_lossurf_B`), the picture is completely different — and the difference is
precisely the measured loss component, not one dollar more.

| model link | model sep-share (23/24/25) | model mean Δ | measured **loss** Δ | measured **congestion** Δ |
|---|---|---|---|---|
| **AEP_Ohio→Dominion** | **96.1 / 98.9 / 96.9 %** | −0.54 / −0.82 / −1.43 | **−0.54 / −1.06 / −1.90** | **−3.65 / −4.42 / −12.44** |
| **West_APS→Dominion** | 100.0 / 99.9 / 100.0 % | −0.72 / −0.61 / −0.87 | −0.72 / −0.66 / −1.05 | −3.08 / −4.32 / −12.05 |
| **SWMAAC→Dominion** | 100.0 / 100.0 / 100.0 % | +0.25 / +0.44 / +0.59 | +0.25 / +0.49 / +0.70 | +1.49 / +1.99 / −3.71 |
| ComEd→AEP_Ohio | 79.1 / 92.7 / 92.2 % | −0.84 / −1.10 / −1.49 | −1.31 / −1.48 / −1.94 | −3.60 / −4.52 / −7.12 |
| West_APS→SWMAAC | 100.0 / 100.0 / 100.0 % | −0.97 / −1.05 / −1.46 | −0.96 / −1.14 / −1.75 | −4.57 / −6.31 / −8.34 |
| SWMAAC→EMAAC | 100.0 / 100.0 / 100.0 % | +0.56 / +0.11 / −0.05 | +1.09 / +0.90 / +1.45 | +12.04 / +10.74 / +13.33 |

The all-eight-at-one-dual share is **0.00 %** in all three years and the mean max
zonal spread is **$2.12 / $3.03 / $4.59** — against PJM's measured
$16.83 / $18.06 / $29.64. **The copper-plate is gone; the congestion is still
entirely absent.** On the chartered boundary the model now produces 100 %, 77 %
and 75 % of the measured loss and **0 %** of the measured congestion.

## §2 — M2: PJM publishes which constraint bound, and it is not a zonal boundary

### §2.0 — two new intakes, both public, both gitignored bulk with committed manifests

* **`data/raw/pjm-binding-constraints/`** — DataMiner2 `da_marginal_value`: one
  row per **binding** day-ahead constraint per hour with its
  `monitored_facility`, `contingency_facility` and **`shadow_price`**. This is
  PJM's analogue of MISO's `bc_HIST`, and it is *directly comparable to the
  model's own transmission duals* — the day-ahead market is the hourly,
  commitment-aware full-network optimization the LP mirrors. 228,795
  constraint-hours over 2023-2025 across 836–1,058 distinct facilities.
  Fetcher: `scripts/data/fetch_pjm_binding_constraints.py`.
* **`data/raw/pjm-ehv-lmp/`** — DataMiner2 `da_hrl_lmps` filtered `type = EHV`:
  the day-ahead LMP and components at PJM's `AGGREGATE` pnode for each 500 kV
  station, ~135 nodes across 15 zones, **38 inside DOM alone**. Fetcher:
  `scripts/data/fetch_pjm_ehv_lmp.py`. (The server-side `zone` filter 400s on
  archived rows, so the fetcher pulls every zone and filters locally — which is
  why M4 covers all eight model zones rather than one.)

### §2.1 — interface vs facility: the split that decides reachability

PJM names a binding constraint one of two ways. A **zonal-scale transfer
interface** carries no voltage rating (`AEP-DOM`, `APSOUTH`, `BED-BLA`, `WEST`,
`EAST`, `CENTRAL`, `BCPEP`) — that is the class an 8-zone reduction can express,
and it is exactly what `pjm_measured_interface_limits` already carries. A
**monitored facility** carries its rating in its own name (`PLEASNTV TX3
XFORMER H 500 KV`). The split is read off PJM's naming, not assigned by hand:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| binding constraint-hours | 73,529 | 78,110 | 76,889 |
| distinct facilities | 857 | 836 | 1,058 |
| **rent on named zonal INTERFACES** | **6.34 %** | **3.06 %** | **6.19 %** |
| rent on facilities **≤ 230 kV** | **82.56 %** | **87.76 %** | **80.00 %** |
| — `AEP-DOM` alone | **0.041 %** | **0.071 %** | **0.236 %** |
| — `APSOUTH` | 0.125 % | 0.247 % | 0.241 % |
| — `BED-BLA` | 0.230 % | 0.381 % | 0.857 % |

Pooled over the three years the voltage profile is **115–138 kV 54.9 %,
230 kV 23.0 %, ≤ 100 kV 5.0 %, 345 kV 6.0 %, 500 kV 4.0 %, 765 kV 0.7 %**.
**PJM's congestion is a low-voltage, sub-transmission phenomenon.** The entire
inter-zonal transfer-interface family — every lever the pjm-133/134/135/136
lineage has proposed, armed or refused — is competing for **3–6 %** of the
rent, and the specific interface the Dominion charter rests on is a
**quarter of one percent** of it in its biggest year.

### §2.2 — and inside the hours Dominion separates, it is Loudoun

Restricting to the top decile of measured DOM-vs-AEP congestion (876 hours/yr,
threshold $7.09 / $11.10 / $34.75), constraints were ranked by their rent share
in those hours against their own annual baseline — a **lift** statistic, so the
set surfaces from the data rather than from a hand-drawn substation map:

| constraint (pooled, top by hot-hour rent share) | hot-hour share | baseline | **lift** |
|---|---|---|---|
| **PLEASNTV TX3 XFORMER 500 KV** | 7.43 % | 2.45 % | **+4.98 pp** |
| **GOOSECRE 500 KV TX1** | 3.10 % | 1.03 % | **+2.07 pp** |
| **GOOSECRE TX1 XFORMER 500 KV** | 2.77 % | 0.87 % | **+1.90 pp** |
| Yorkana B43 CB 230 KV | 3.81 % | 1.99 % | +1.81 pp |
| COOLSPRI 230 KV COL-MIL | 3.03 % | 1.35 % | +1.68 pp |
| **ASHBURN-GOOSECRE 227D 230 KV** | 2.80 % | 1.24 % | **+1.56 pp** |
| **PLEASNTV-ASHBURN 274D 230 KV** | 2.49 % | 1.04 % | **+1.45 pp** |
| **BRAMBLET-EVRGREEN 2172B** | 1.94 % | 0.56 % | **+1.38 pp** |
| LENOX-NMESHOPP 115 KV (PPL, the ISO's single largest constraint) | 5.18 % | 14.81 % | −9.64 pp |

**Every one of those substations is inside the DOM transmission zone — verified
against PJM's own pnode registry, not inferred from the names.** Querying
`/api/v1/pnode` (23,711 rows) for each returns `zone = DOM` and nothing else:

| substation | PJM `zone` | | substation | PJM `zone` |
|---|---|---|---|---|
| PLEASNTV / PLEASANT VIEW | **DOM** | | BRAMBLET | **DOM** |
| GOOSECRE | **DOM** | | EVRGREEN | **DOM** |
| ASHBURN | **DOM** | | LOUDOUN | **DOM** |
| MORRISVILLE | **DOM** | | MT STORM | **DOM** |

These are the northern-Virginia data-centre pocket — the load concentration
`constants.py:1376` already anchors at a ~0.55 near-2030 data-centre share for
`PJM_Dominion`. **Both ends of every one of these constraints map to the same
model zone.** In a single-node zone those constraints do not exist: the LP has
one dual for the whole of Dominion, so a limit between two points inside it is
not representable at any parameter value.

For contrast, the non-Dominion hot-hour constraints resolve to other single
zones too — `YORKANA` → METED (`PJM_Central_PA`), `NOTTINGH` → PECO
(`PJM_EMAAC`), `CONASTON` → BGE (`PJM_SWMAAC`), `LENOX` → PENELEC/AECO. They
are facility constraints inside zones, not the interfaces between them.

Note also what *loses* share in the hot hours: `LENOX-NMESHOPP 115 KV`, the
single largest constraint in the whole ISO (14.8 % of all rent), is a PPL-area
115 kV line that has nothing to do with Dominion. The model's congestion
deficit is not one missing interface — it is 800–1,000 facility constraints it
does not have and structurally cannot have.

## §3 — M3: the CT leg is a price-formation defect, and half of the missing price is that congestion

The roster is taken from the **committed benchmark payload** — the exact plants
the model's own fleet assigns to `PJM_Dominion` / `CT_PEAKER` — and then
narrowed to those plants' CAMPD `unitType == 'Combustion turbine'` units, the
same filter the CT heat-rate derive applies. **Both steps are required**: three
of the nine are mixed sites, and taking a plant whole would count its
combined-cycle blocks as peaker output (§3a). Nine plants, **40 turbines**,
**3.177 / 4.225 / 5.462 TWh** gross — which reconciles with the benchmark's own
unit-split actual (3.066 / 4.048 / 5.218 net) to within the parasitic factor.

| CT-energy-weighted, $/MWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured DOM LMP | **50.78** | **62.04** | **103.41** |
| model Dominion dual, same hours | **33.06** | **35.35** | **48.80** |
| **price deficit** | **−17.72** | **−26.69** | **−54.61** |
| of which measured **congestion** (MCC) | **9.09** | **12.32** | **27.73** |
| congestion share of the deficit | **51 %** | **46 %** | **51 %** |
| CT energy in hours with DOM MCC > $5 | 62.4 % | 64.5 % | **80.0 %** |
| CT energy in hours with \|DOM MCC\| ≤ $1 | 2.6 % | 6.5 % | 4.7 % |

Two things follow. **(a) The CT leg is not an availability defect.** The real
turbines are synchronised in **68.3 / 54.4 / 62.4 %** of all hours — extremely
high duty for a peaking fleet — with a 2025 diurnal profile rising from ~65 MW
at 01:00 to **1,317 MW at 19:00** on a 4,198 MW maximum. A fleet running in two
hours out of three is not held back by an outage envelope; the model under-runs
it because its Dominion price is **$18–55/MWh short in exactly the hours that
fleet is producing**. **(b) About half of that shortfall is the congestion §2
just proved unreachable** — and the concentration is striking: **80 % of 2025's
real CT energy is produced in hours PJM prices Dominion congestion above $5**,
against 4.7 % in hours it prices it at essentially nothing. The other half is
system-energy-price formation, which is a different (and open) question.

### §3a — the chartered defect has been overstated ~1.9×: the quoted "actual" counts Doswell's COMBINED-CYCLE output as peaker

Every handoff in this lineage — and the `PJM.json` keeper note — states the
Dominion `CT_PEAKER` actual as **7.38 / 8.68 / 9.64 TWh**. **The benchmark does
not say that.** Joining the committed run payload's per-plant model series to the
committed benchmark's per-plant actual — the same join
`docs/codebase-site/js/backcast-runs.js` renders — gives, on the nine
`PJM_Dominion` / `CT_PEAKER` keys:

| TWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| model (matches the quoted figure exactly) | 0.724 | 1.380 | 2.923 |
| **benchmark actual, CAMPD** | **3.066** | **4.048** | **5.218** |
| benchmark actual, EIA-923 | 3.019 | 4.012 | 5.162 |
| *quoted in the keeper note / handoffs* | *7.38* | *8.68* | *9.64* |

The quoted figure is the **whole-plant** CAMPD net energy of those nine plants —
recomputed here as **7.320 / 8.635 / 9.632 TWh**, matching to 0.1–0.8 %. The
benchmark's own figure is the **unit-level split**: its Doswell record carries
`split: "unit_hourly"` and puts that site's `CT_PEAKER` share at 1.079 TWh in
2025 against 4.454 TWh for its `CC_REGULAR` blocks. CT-only metered energy for
the nine plants recomputes to **3.082 / 4.114 / 5.298 TWh net**, matching the
benchmark to 0.5–1.5 %.

**So the benchmark and the dashboard have always been right; the prose number
carried forward in the notes was computed on the wrong basis** — the same
mixed-facility trap that corrupted this session's own first pre-computation of
the heat-rate delta (`PREREG-pjm137` §2a), and the same one
`measured_ct_heat_rates` exists to fix.

Restated, the chartered defect is:

| Dominion CT_PEAKER | 2023 | 2024 | 2025 |
|---|---|---|---|
| gap (model − actual), TWh | **−2.342** | **−2.668** | **−2.295** |
| model as a share of actual | **24 %** | **34 %** | **56 %** |
| *as previously stated* | *−6.66 / 10 %* | *−7.30 / 16 %* | *−6.72 / 30 %* |

The leg is **~2.3 TWh short and 56 % closed in 2025**, not "~94 % unclosed".
pjm-136's `+0.411 TWh` therefore closed **≈15 %** of the true remaining 2025 gap,
not 5.8 %. Nothing about this session's other measurements changes — M1, M2 and
M4 never used the class total — but the *size* of the target does, and every
statement of it downstream of this document should use the benchmark's own
number. **This has not been propagated into `PJM.json` or the matrix by this
session**; it is reported here for the owner, because rewriting a keeper's note
is a promotion-lane act.

## §4 — M4: there is more separation INSIDE Dominion than across its boundary

`FINDING-pjm136` §3 tested topology adequacy with PJM's published trading hubs
and concluded the reduction can carry the DOM-vs-AEP boundary. **That
conclusion stands for the boundary** — the inter-zonal quantity is real and
expressible. What it could not test is Dominion's *interior*: PJM publishes no
hub inside `PJM_Dominion`. The EHV aggregate pnodes do cover it, 38 of them, and
they say:

| model zone | EHV nodes | mean intra-zone dispersion (23 / 24 / 25) | > $10 (2025) | widest intra-zone pair (2025) |
|---|---|---|---|---|
| PJM_West_APS | 19 | 7.57 / 10.20 / **18.58** | 36.3 % | BEDINGTON vs SOUTHBEND $11.49 |
| **PJM_Dominion** | **38** | **6.18 / 8.68 / 16.78** | **31.6 %** | **GRNSVIL vs PLEASANT VIEW $10.95** |
| PJM_Central_PA | 20 | 9.07 / 8.63 / 12.38 | 39.7 % | HUNTERSTOWN vs LACKAWAN $9.14 |
| PJM_AEP_Ohio | 28 | 4.30 / 5.98 / 9.40 | 21.7 % | JOSHUA FALLS vs REYNOLD2 $6.12 |
| PJM_SWMAAC | 7 | 5.24 / 7.27 / 7.35 | 18.2 % | BURCHESHILL vs CONASTONE $6.68 |
| PJM_EMAAC | 19 | 2.90 / 2.50 / 2.87 | 3.9 % | DLTAPLNT vs ROSELAND $2.33 |
| PJM_ComEd | 3 | 0.65 / 1.06 / 1.93 | 4.9 % | 112 WILTON vs 167 PLANO $1.90 |
| *inter-zonal DOM-vs-AEP, for comparison* | — | **4.76 / 6.13 / 14.42** | — | — |

**Intra-Dominion / inter-zonal ratio: 1.30 / 1.42 / 1.16×.** The 2024 widest
pair is **LOUDOUN vs MT STORM** — the data-centre pocket against the western
generation station — exactly the geography §2.2's binding constraints describe.

This also explains why the hub-based test read clean: the two zones PJM
publishes multiple hubs inside, **ComEd and AEP_Ohio, are the two most
internally-uniform zones in PJM** (ComEd $0.65–$1.93). pjm-136 §3 sampled the
best case available to it. With the EHV nodes the sample is complete, and six of
the seven measurable model zones carry intra-zone dispersion at or above the
inter-zonal spread the model is chartered to reproduce.

## §5 — DO-NOT-REDO (binding on successors)

- **Do not propose any zonal congestion mechanism against the Dominion CT leg.**
  This is the ERCOT/MISO `internal_congestion_split` refusal class, now
  established for PJM on PJM's own published records, three ways: the rent is
  3–6 % inter-zonal (§2.1), the hot-hour constraints are intra-Dominion
  facilities (§2.2), and the intra-zone dispersion exceeds the inter-zone
  spread (§4). A mechanism that makes an internal *model* link price would be
  reproducing a boundary that carries **0.04–0.24 %** of the real rent. This
  **supersedes the open question** `FINDING-pjm136` §5 handed forward ("make an
  internal PJM constraint actually price, or prove it can't") with the second
  branch: **it can't, and here is PJM's own arithmetic.**
- **Do not read this as licence to split `PJM_Dominion`.** A NoVA/Loudoun pocket
  is the structurally correct representation, but PJM publishes metered load by
  *transmission zone* only — there is no measured NoVA load series — so the
  split's load share would be a fitted scalar (rule 5 `[R-NO-MAGIC]` /
  rule 24 `[R-REGISTRY]`). It is filed as a handover lead in §6, **not**
  chartered. The same bar that closed the star node closes this until a
  measured sub-zonal load basis exists.
- **Do not re-test `measured_ct_heat_rates` on the Dominion CT leg without new
  evidence.** §6 pre-computes it: the nine Dominion CT plants are all pure-CT
  facilities whose eGRID plant rate is already within 0.04–0.7 MMBtu/MWh of
  their measured loaded rate, so the mechanism moves the zone by **−0.168
  MMBtu/MWh ≈ −$0.59/MWh** against a **$10–38/MWh** deficit. (It is still
  chartered as an accuracy correction — see the pre-registration — but it is
  pre-registered INERT on this defect.)
- **Do not quote M3's price deficit as an offer-curve error.** It is a *zonal
  price* deficit, and §2/§4 attribute 52–63 % of it to congestion the model
  cannot represent. Only the remainder is available to any offer-side lever.
- **Do not quote `7.38 / 8.68 / 9.64` as the Dominion `CT_PEAKER` actual again**
  (§3a). It is a whole-plant figure that counts Doswell's combined-cycle blocks
  as peaker output. The benchmark's own unit-split number is
  **3.066 / 4.048 / 5.218**, the gap is **−2.34 / −2.67 / −2.30 TWh**, and any
  successor sizing this defect — or claiming a share of it closed — must use the
  benchmark's number. Whenever a class actual is quoted for a zone, take it from
  the committed `frontend/data/backcast/bench/<ISO>/<year>.json.gz` per-plant
  record (which carries `split: "unit_hourly"` at mixed sites), never by summing
  CAMPD over a plant roster.
- Carried forward unchanged: `FINDING-pjm134` §5/§8, `FINDING-pjm135` §7, and
  `FINDING-pjm136` §5 in full — including that the delivery-factor surface may
  never be multiplied, scaled, haircut, blended, floored, capped or
  scarcity-exempted (PREREG-pjm136 §4 no-feedback ceiling).

## §6 — handover leads, stated but NOT built here

1. **A `PJM_Dominion` NoVA/Loudoun split is the structurally correct fix and is
   blocked on one measured input**: a sub-zonal load basis. PJM's metered-load
   feed stops at the transmission zone. If a defensible NoVA load series exists
   (Dominion IRP filings, PJM load-forecast reports by sub-area, or the
   data-centre interconnection queue), the split becomes a zero-DOF measured
   mechanism and this defect becomes reachable. Until then it is a fitted
   scalar and is refused.
2. **The other half of the CT price deficit is system-energy-price formation**,
   not congestion. Netting the measured congestion component out of §3's
   deficit leaves **+$8.63 / +$14.37 / +$26.88 /MWh** (49 / 54 / 49 % of it) that
   a zonal model *could* in principle produce: the measured DOM **MEC** alone
   runs at a p50 of $35.94 / $41.35 / **$58.86** in CT hours against the model's
   whole Dominion dual at $32.07 / $32.28 / **$42.72**. That is an ISO-wide
   marginal-unit question and connects to open root cause (6) in the keeper note
   (fitted coal rungs owning the $40–150 region the measured corpus assigns to
   the CC top belt and CT_FAST). **This, not congestion, is where a successor
   should look** — and note it is only ~half the gap, so even closing it fully
   would not close the CT leg.
3. **`PJM_West_APS` and `PJM_Central_PA` carry intra-zone dispersion as large as
   Dominion's** ($18.58 and $12.38 in 2025). Whatever representation-boundary
   disclosure Dominion gets, those two need it as well — and EMAAC's, filed at
   pjm-136 §3 from the hub test, is now measured at only $2.50–2.90 at EHV
   level, i.e. **smaller** than the hub-based reading suggested.
4. Carried from pjm-135, still open: the `_PJM_TIE_ZONE` / `INTERFACE_NEIGHBORS`
   TVA disagreement, and PJM `CC_CHP` running +42 %.

---

## §7 — the A/B result: **the measured heat rates are ACCURACY-CORRECT and, against the pre-registration's own expectation, FAVOURABLE on the Dominion leg**

Arms `pjm137_control_A` / `pjm137_ctheatrate_B`, 2023+2024+2025 each in one
invocation (rule 16), solved sequentially (rule 12). Scorer:
`scripts/probes/_pjm137_ctheatrate_ab.py`; machine output
`results/probes/pjm137_ctheatrate_ab.json`.

**Verified single-delta.** Arm A reproduces the committed `pjm136_lossurf_B`
**byte-identically — 0.000000000 MW over 166,440 class-hours, each of the three
years** (K5), and `run_config.json` shows `measured_ct_heat_rates` False in A and
True in B with `pjm_zonal_loss_surface` True in both.

| gate (PREREG §2/§3) | result | verdict |
|---|---|---|
| **P2** material and two-signed | **29 of 71** plants move > 0.5 MMBtu/MWh; **35 cheaper / 36 dearer**; ISO energy-weighted **+0.229 MMBtu/MWh (+$0.80/MWh)** | **PASS** |
| **K3** physical-band exclusions ≤ 10 % of energy | **0 plants, 0.00 %** excluded | **PASS** |
| **K4** zero slack / zero dump, both arms | 0 / 0 in every year | **PASS** |
| **K5** arm-A identity | **0.000000000 MW**, all three years | **PASS** |
| **K1** the C3c standing kill | **PASS in both arms, and UNCHANGED** — the model's tail-hour counts are identical (3 / 10 / 32 h) | **PASS** |
| **K2** C1 per class | **16/16, free 12/12 in BOTH arms** | **PASS** |
| **K6** solve cost | no new rows or columns; coefficient values only | reported |

**Both arms carry a `CALIBRATED` determination with every criterion passing.**

### §7a — the chartered defect: Dominion GAINS while the ISO-wide class FALLS

| PJM_Dominion, TWh | 2023 A → B | 2024 A → B | 2025 A → B | benchmark actual (§3a) |
|---|---|---|---|---|
| **CT_PEAKER** | 0.724 → **0.721** | 1.380 → **1.448** | 2.923 → **3.162** | 3.066 / 4.048 / 5.218 |
| CC_REGULAR | 32.352 → 32.501 | 42.591 → 42.852 | 50.087 → 50.320 | — |
| **ISO-wide CT_PEAKER** | 22.410 → **19.553** | 23.081 → **20.446** | 29.934 → **27.140** | — |

**The ISO-wide class loses 2.6–2.9 TWh in every year while Dominion gains** —
the same pure-reallocation signature pjm-136 produced, and for a different
reason: this is a per-plant re-pricing, so the zones whose peakers were most
over-credited by the eGRID plant average give up energy to those whose were not.

Against the benchmark's own actual, the Dominion gap goes **−2.342 → −2.345**
(2023, flat), **−2.668 → −2.600** (2024), and **−2.295 → −2.056** (2025) — the
2025 year closes **10.4 %** of the remaining gap, comparable to pjm-136's
+0.411 TWh.

**This contradicts the pre-registration, which is the point of writing one.**
`PREREG-pjm137` §4 predicted the delta would push the Dominion leg *the wrong
way*, because Dominion's energy-weighted rate rises the most of any zone
(+0.634 MMBtu/MWh). It rose — and Dominion still gained, because the mechanism
is **per plant**, not per zone: Doswell (+2.324) and Gravel Neck (+3.204) are
correctly made dearer while Remington (−0.329) and Ladysmith (−0.001) are not,
and Dominion's cheaper turbines improve their standing against other zones'
peakers that got dearer. A zone-average prediction could not see that, and the
pre-registration is recorded as **refuted on its own expected direction** rather
than quietly re-written.

### §7b — the honest costs

1. **ISO-wide `CT_PEAKER` volume moves further from its class total in two of
   three years**: |error| 0.75 → 2.11 (2023) and 0.94 → 3.57 (2024) against the
   EIA-923 class totals, while 2025 improves markedly (6.11 → 3.32). C1 still
   passes 16/16 in both arms, so no band breaks, but the class-level trade is
   real: `CC_REGULAR` (7.42 → 6.07, 3.03 → 1.84) and `COAL_BIT` (0.87 → 0.29,
   2.15 → 1.62) both improve as CT energy moves into them.
2. **C8 `CT_PEAKER` forced share rises** — 15.1 → 16.9 % (2024), 15.6 → 17.1 %
   (2025), and 2023 newly appears above the 15 % peaker cap at 16.3 %. All three
   are **GROUNDED** (every binding mechanism clears D-4; profile r 0.923–0.973
   and off-peak CV ratio 0.703–1.083), so under rule 20 this is a clean PASS
   surfaced as a report note. It is nonetheless a shrinking class carrying a
   larger forced fraction, and the next session should watch it.
3. **The mechanism does not address the congestion half of the price deficit**
   (§3), and was never claimed to.

### §7c — what this says about rule 14

The eGRID plant-average heat rate is an *estimate*; the measured loaded rate is
the machine's real rate; and at Doswell the estimate was wrong by
**2.32 MMBtu/MWh ≈ $8/MWh** because eGRID publishes one number for a site that
is six combined-cycle blocks and three peaking turbines. Replacing it is
mandatory under rule 14 `[R-ACCURATE]` independently of any residual — and here
it happens to cost nothing: no criterion fails, C3c is untouched, C1 holds at
16/16, and the chartered defect improves. **PREREG §4's no-feedback ceiling was
honoured: no multiplier, blend, scale, floor, cap, per-plant override or band
widening was applied to the derived rates, and none may be.**

**Determination: ACCURACY-CORRECT, ZERO-DOF, FAVOURABLE-ON-THE-DOMINION-LEG,
RUBRIC-COMPLETE.** `n_residual` unchanged at 6; the DOF ledger goes 16 → 17
entries, the new one `measured-physical`.
