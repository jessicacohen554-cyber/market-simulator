# FINDING miso-178 — the C3a-2025 anatomy at the measured-rho keeper: 82% of the miss is the 88-hour tail, the whole annual target is deterministic-reachable, and the lever plan is ranked

**Session:** miso-178 (2026-08-23). **Keeper:** `2026-08-22-miso-177-rho-measured`
(bundle `results/calibration/miso177_rho_B`), UNCHANGED.
**No LP solved, nothing armed, no `ScenarioConfig` field added, no cell verdict minted,
no registration** (the miso-142/…/167/171/174/176 no-LP precedent; rule 15
`[R-DASHBOARD]` not engaged).

**Charter.** The owner re-opened this lane in writing 2026-08-18 (*"2025 miso needs to
be calibrated in summer scarcity it's unacceptable that it doesn't"*, matrix §5.4),
lifting the miso-163 closure for this target. This session is the measurement +
planning deliverable that re-open requires: WHERE the −11.75% lives on THIS keeper
(zonal, hourly-bucket, seasonal, DA-foreseen vs RT-only, counterfactual ceilings), then
the ranked lever plan with rule-17 shape, rule-13 admissibility, measured reach bounds,
a PREREG sketch for the top candidate, and the owner decision points.

Instruments (all read-only, committed):
`scripts/probes/_miso178_c3a2025_anatomy.py` →
`results/calibration/_miso178_c3a2025_anatomy.json` (footing / zonal / buckets /
seasonal / foreseen / ceilings, plus the FULL miso-167 instrument re-run at this bundle
and the miso-171 scarce-set continuity assertion);
`scripts/probes/_miso178_c3a_decomposition.py` →
`results/calibration/_miso178_c3a_decomposition.json` (the pre-registered miso-156
three-channel Δ decomposition, miso-161 wrapper pattern, third application). Every
number below reproduces from committed artifacts by running those two scripts.

Footing (hard gate, passed): reproduced C3a **+1.2813 / −4.0643 / −11.7421%** vs
registered +1.279 / −4.056 / −11.747% (|Δ| ≤ 0.0083 pp). Sign convention throughout:
**pp = contribution to (model−actual)/bench in percentage points; negative = model
UNDER-priced there.** Band ±10% ⇒ 2025 needs **+1.75 pp**.

---

## 1. Where the miss lives: 82% in 88 hours, and the cancellation that used to hide it is eroding

Additive bucket decomposition of each year's C3a (buckets sum to the footing C3a minus
a named ≤0.011 pp residual — coverage hour + bench 2-dp quantization):

| pp of C3a | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| actual RT>$200 tail (30/37/**88** h) | −2.978 | −4.584 | **−9.614** |
| top-decile net-load ex-tail (869/862/829 h) | −1.076 | −2.517 | −3.569 |
| remainder (~7,860 h) | **+5.344** | **+3.034** | **+1.451** |
| **C3a** | **+1.281** | **−4.064** | **−11.742** |

Three structural facts:

1. **The tail owns the 2025 miss: −9.61 pp of −11.74 (82%).** The 88 hours are 1.0% of
   the year. Everything outside the tail and the top net-load decile is **over**-priced
   (+1.45 pp) even in 2025.
2. **The year-monotone worsening is the sum of two monotone moves**: the tail triples
   (30 → 37 → 88 h; −2.98 → −4.58 → −9.61 pp) while the compensating body over-price
   erodes (+5.34 → +3.03 → +1.45 pp). This is miso-167's "2023/2024 pass by
   cancellation" made exactly additive: the same flat-stack defect (slope ratio at this
   keeper 1.62× / 1.65× / **4.06×**, m167 re-run) prices the trough high and the peak
   low, and 2025 is the year the two halves stopped cancelling.
3. **Monthly (2025):** Jun −3.28 + Jul −3.69 + Sep −1.56 + Jan −1.43 pp carry −9.96 of
   the −11.74 (own-month misses −29.1 / −27.8 / −18.5 / −13.8%). Jun+Jul splits
   **tail −4.70 / body-ex-tail −2.26 pp** — the body hole is real but half the tail's
   size on the annual metric. **May 2025 runs the OTHER way: +0.82 pp (+14.4%
   own-month)** — the miso-148 §7.1 carried question is still open, unexplained, and
   now quantified: any May repair *costs* ~0.8 pp against the 2025 band and must be
   budgeted (rule 14 — it is still a real defect to fix when found).

## 2. Zonal: not "uniform" — a South-vs-Midwest dipole the single-hub benchmark half-hides

Per-zone demand-weighted own-error vs the committed zonal validation series
(`actual_lmp_hourly_zonal_MISO.parquet`; MISO-Plains via the documented MINN+ILLINOIS
hub-mean proxy):

| own err % | 2023 | 2024 | 2025 | 2025 model lw / actual lw |
|---|---:|---:|---:|---|
| MISO-East | +6.7 | −2.6 | **−15.2** | 38.74 / 45.66 |
| MISO-Indiana | +0.4 | −5.9 | **−15.1** | 38.92 / 45.84 |
| MISO-West | +9.1 | +4.7 | −9.5 | 38.66 / 42.70 |
| MISO-Plains (proxy) | +10.9 | +7.1 | −6.8 | 38.90 / 41.75 |
| MISO-Illinois | +12.7 | +8.6 | −4.3 | 39.06 / 40.81 |
| **MISO-South** | **+18.8** | **+21.0** | **+17.0** | **43.63 / 37.31** |

- **The model over-prices MISO-South by +17 to +21% in ALL three years.** In 2025 the
  real market ran a South **discount** (actual South 37.31, the cheapest zone, below
  every Midwest hub) while the model prices South at a **premium** (+$4.9 over its
  copper-plate Midwest) — the RDT/TCDC posture runs the wrong way in exactly the year
  the Midwest was scarce. Mechanism reading (evidence, not a new cell): the too-flat,
  too-cheap Midwest stack generates southward export pressure, binds the RDT N→S
  (5,086 h in 2025, miso-174), and manufactures a South congestion premium that 2025
  reality inverted. The South price symptom is plausibly **downstream of the Midwest
  slope defect** (rule 19: one mechanism, seen twice) — a falsifiable prediction for
  the top lever (§7).
- The 2025-specific increment is **Midwest**: East/Indiana swing +6.7/+0.4 → −15.2/−15.1
  from 2023 to 2025. The scored benchmark (Indiana Hub) reads the Midwest miss.
- **Benchmark-basis wedge, report-only:** the zone-resolved actual lw mean sits
  **$2.65/$3.02/$3.33 below** the scored Indiana-hub lw (2025: 42.12 vs 45.46; C3a
  would read −4.75% on the zone-resolved basis). This is composition (four low-priced
  South hubs, hub-mean grain), not model skill; the scored basis is the standing,
  miso-140-verified one. Recorded so nobody mistakes basis for progress — **not a
  lever, and no re-basing is proposed.**

## 3. The reach map: what a deterministic hourly LP may still claim

**The miso-171 §6 closure is CONFIRMED CURRENT at measured rho.** The m167 re-run on
this bundle: scarce-47 model reserve dual mean **$13.23** (was $10.71 at miso-160), max
**$98.00 = the full Schedule-28 step** — the reachable reserve surface is saturated
exactly as RESULT-miso177 said. DA-foreseen scarce-hour model mean **$110.32** (was
$102.72; the ~+$7.6 is the miso-169/177 capture), RT $546.68 — the remaining
DA-foreseen gap is the **energy stack**, not reserves. MISO's published scarce-hour ASM
MCP ($484.87, −2h alignment; levels key-sensitive, shares not) still ≈120% of the
energy gap; the miso-171 scarce-47 set is bit-identical across bundles (asserted), so
its committed product split (~29% supplemental, structurally ungateable) stays current.

**The two-term split** G = Σw(Pm−DA) + Σw(DA−RT) — deterministic-reachable vs the
RT-only wedge no deterministic LP can see (MISO's own DA market is the existence proof
of the reachable half):

| pp of C3a | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model → DA (deterministic-reachable) | −2.93 | −6.67 | **−13.71** |
| DA → RT wedge (RT-only class) | **+4.22** | **+2.61** | **+1.98** |

**The RT-only wedge is net POSITIVE for the model in every year.** In the 88 tail
hours RT deepens far past DA (−7.60 pp; RT-only 58 h alone −5.18 pp) — that half stays
structurally closed (ordc `G`, miso-163 grounds untouched). But across the other
~8,670 hours DA sits persistently above RT (+9.57 pp), and the two more than cancel.
So:

> **The annual C3a-2025 target does not require the RT-only model class.** The model
> sits −13.7 pp below MISO's own deterministic DA surface — −2.0 pp of it in the tail
> (30 DA-foreseen hours: model→DA −1.52; 58 RT-only hours: model→DA −0.50), the other
> **−11.7 pp in the body**. The reachable space is ~8× the +1.75 pp needed.

The 88-hour tail split at the miso-167 DA>$150 line: **DA-foreseen 30 h = −3.94 pp**
(2023/2024: 1 h / 2 h — the foreseen-tail population is a 2025 phenomenon),
**RT-only 58 h = −5.68 pp**.

## 4. The counterfactual ceilings (computed, not estimated)

| C3a if… | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| as-is | +1.28 | −4.06 | −11.74 |
| tail priced at actual RT (ceiling of ANY scarcity-only lever) | +4.26 | +0.52 | **−2.13** |
| model priced at actual DA everywhere (deterministic-LP ceiling) | +4.21 | +2.61 | **+1.96** |

Both ceilings clear the ±10 band in every year, 2023 included (against-interest: a
perfect-tail 2023 lands +4.26, inside band, C3b/C8 gates still watch). A
scarcity-shaped lever therefore has the room; the honest constraint is **shape**: the
2025 remainder is already +1.45 pp over, so a uniform level lift is the one move the
measurement forbids (it worsens 2023's +5.34 body over-price monotonically —
miso-167's against-interest bound, now in additive pp).

## 5. What the model dispatches in the 88 hours (the generation guard)

Model vs EIA-930 family means inside the 2025 tail hours (MW):

| family | model | measured | Δ |
|---|---:|---:|---:|
| gas | 33,387 | 38,713 | **−5,326** |
| net import | 4,754 | 2,681 | **+2,073** |
| solar | 3,190 | 4,929 | **−1,738** |
| coal | 28,379 | 27,262 | +1,117 |
| wind | 9,017 | 8,756 | +261 |
| nuclear / hydro | 10,501 / 2,059 | 10,724 / 2,068 | ~0 |

The same signature stands in 2023/2024 tails (gas −4.0/−4.7 GW, imports +2.3/+1.6 GW):
**the model meets the tail with phantom imports and cheap committed supply while 5+ GW
of real gas that actually ran stays idle** — the quantity face of the price-identity
defect (Δ₁ below): reality cleared expensive gas (implied HR ~29); the model clears
imports + efficient units at HR ~12 and never needs its own peakers (8.2 GW CT_PEAKER
idle, miso-167). The solar −1.7 GW is a named observation for the fleet lane (2025
EIA-860 vintage under-carry is a standing cross-ISO open item, miso-151 §9) — C1
passes annually, so this is tail-hour-specific and second-order here.

## 6. The Δ-channel attribution at this keeper (miso-156 instrument, third re-run)

2025 annual gap **+5.33 $/MWh** = **Δ₁ marginal-unit identity +10.50 (197%)** + Δ₂
cost level −6.44 (−121%) + Δ₃ above-cost +1.27 (24%) — miso-161's attribution stands
at the measured-rho keeper (V1/V4 gates pass; V2 report-only drifts with the
keeper lineage as expected; FLOORS_OFF twin brackets it). The miss is WHO sets the
price, not what the marginal unit costs: the model's price-setter is efficient
(implied HR ~12 MMBtu/MWh) where the market's was expensive (~29).

## 7. The ranked lever plan

Everything below respects the DO-NOT-REDO ledger (§8 anti-list) and is bounded by the
measurements above.

### Lever 1 — the ACROSS-UNIT offer-level dispersion object (miso-151 §8(A)'s named successor). RECOMMENDED CHARTER.

- **The object.** MISO's real offer book is nearly flat within each unit ($3.76
  top-of-own-curve rise) but disperses **across units** by $47.84/MWh p90−p10 (p95
  $91.44, p99 $298.03, Jul-2025 DA book — miso-151 G-5). The model compresses that
  across-unit spread into class-tranche multipliers, which is exactly a 4.06×-too-flat
  summer stack, a wrong marginal identity (Δ₁ = 197%), idle expensive gas in the tail
  (§5), and a body that over-prices at the trough (+1.45 pp remainder). The
  within-unit family is CLOSED (`measured_offer_surface` R); the across-unit family
  was explicitly named and never chartered.
- **Reach, bounded by this session's measurement:** the deterministic-reachable space
  it lives in is −13.7 pp (§3); the need is +1.75 pp. Its natural action is
  shape-correct: rank-preserving dispersion leaves the low stack (where the model is
  already over) and raises the high-rank offers — the only move §4 permits. It reaches
  the DA-foreseen tail (−3.94 pp), the Jun+Jul body (−2.26 pp), and the winter misses
  (Jan −1.43) with ONE all-hours mechanism, no window (rule 17: an all-hours
  supply-curve conduct property; driver = real across-unit cost/conduct dispersion —
  vintage heat-rate spread, fuel contracts, O&M, risk premia).
- **Falsifiable structural prediction (this is the rule-1 test, stated before any
  build):** if the Midwest stack steepens to measurement, southward export pressure
  falls, the RDT N→S premium unwinds, and **MISO-South's +17% over-price falls toward
  zero without any South-specific lever**. A dispersion arm that closes C3a-2025 but
  leaves the South dipole intact has NOT captured the real object.
- **Rule-13 admissibility:** the corpus offer columns are ex-ante participant
  declarations, admissible in kind (`data/raw/miso-energy-offers/README.md` fixes the
  line; award columns are dropped at curation and can never be read downstream). The
  identification path contains NO LMP and no residual. Masked units + the REFUTED
  class bridge (miso-138) force the honest form: a **distributional, rank-mapped
  markup-over-reference construction** — no unit pinning, no class crosswalk. The
  armed-conduct precedent exists (`ercot_storage_adaptive_expectation`, ercot-223
  keeper: measured-conduct constants, rule 23). The admissibility FORM (conduct
  distribution as solve input) is an owner ruling — put as D-1.
- **What would kill it:** (a) the measured across-unit dispersion sits mostly on
  self-scheduled/must-run units below the margin (dispersion without price-setting
  power) — the PREREG pre-check measures this before any LP; (b) the rank mapping is
  non-identifying at the model's tranche grain (a K-2-style apportionment objection);
  (c) 2023 leaves band / C3b NRMSE fails / C8-D-4 conduct regressions; (d) the Δ₂
  overshoot (model cost level already −121% the other way — the arm must fix identity,
  not stack a level adder).
- **Cost:** JJA 2023–25 corpus refetch ≈430 MB, 552 zips (payload is
  gitignored-by-design; README carries the fetch commands); LP A/B on the miso-169
  15 GB recipe.

### Lever 2 — the coincident-peak seam-RESPONSE envelope (PJM seam). BLOCKED ON THE STANDING 5(i) OWNER RULING; SEQUENCE AFTER LEVER 1.

- Re-measured on the 88-hour set: **+2.07 GW** phantom import (miso-174's +1.41 GW on
  the 47-hour summer set; same object, wider window). The physics is half-proven:
  miso-176 measured the pull-back as real, named JOA congestion management (MISO over
  its own FFE on 67/82/80% of scarce binding rows; binding 4–6× harder at stress) —
  not a residual-fit artifact.
- **Reach:** at the model's CURRENT slope, the entire reach is +3.3/+7.7/+3.9 $/MWh
  in scarce hours ≈ 1–2.5% of the miss (miso-174 §6) — near-inert alone. **After a
  slope repair the same GW re-prices up a ~4×-steeper curve**, which is why the
  sequencing is levers 1 → 2, and why an early 5(i) ruling matters even though the
  build waits.
- Admissibility is exactly the line the owner must draw (D-2): an envelope conditioned
  on the **neighbour's own load** (forward driver, regenerates, responds to changed
  conditions — admissible in kind) that inevitably **correlates with MISO scarcity by
  coincident summer peak**. A separate FFE-MW cap stays G (miso-176 K-2: no published
  seam-grain entitlement aggregate; no apportionment may be invented) unless new data
  appears.

### Lever 3 — the SOUTH under-EXPORT (+0.63/+0.35/+1.19 GW). EVIDENCE SESSION FIRST; PARTLY CONTINGENT ON LEVER 1.

- This session adds the price face: the model's standing **+17→+21% South over-price**
  and the 2025 sign inversion (§2). If lever 1's falsifiable prediction holds, part of
  the South symptom self-corrects; what remains is the physical export block to
  SOCO/TVA/AECI (outside the M2M record entirely — no M2M/CMP construct there). The
  admissible shape on the table is the Manitoba precedent: a **firm/contract export
  block** grounded in JOU/firm-service schedules, not spread arbitrage. The evidence
  session hunts that driver (D-3); no mechanism is proposed until it exists.

### Lever 4 — the May-2025 opposing object (honesty item, not a C3a lever).

+0.82 pp over-priced, +14.4% own-month, cause unknown since miso-148 §7.1 (the
−1,201 MW May CC availability deficit is a different cause from the summer one). Any
future May repair must be budgeted at ~−0.8 pp against C3a-2025. Left named.

## 8. The anti-list (adjudicated; none of this is re-proposed)

`ordc_scarcity_overlay` G (miso-163 grounds re-confirmed here: the RT-only 58 h stay
out of deterministic reach — and §3 shows they are not NEEDED for the annual band);
`m2m_seam_entitlement_cap` G (K-1/K-2 stand); `measured_interface_limits` R (K-PRE-1:
no capability violation — re-confirmed by §5's import excess sitting under observed
deliverability); within-unit `measured_offer_surface` R; `gas_hub_basis_overlay` R
(Δ₂ already runs the other way); reserve-requirement raises (rule 14 — model already
holds 7.06 GW vs 2.62 cleared in the scarce set, m167 re-run); supplemental gating
(rule 1); the sub-regional gated extension (inert, +0.03 pp); ANY new reserve family
(inherits miso-170's free-supply inertness — 69% of scarce-hour requirement clears at
dual $0); `ramp_envelopes` I (the model under-ramps reality at every quantile — ramp
limits cannot bind); `import_shape_lever` G; `internal_congestion_split` G /
`zonal_loss_surface` R (and §2's dipole is a LEVEL object, not a loss-surface object);
`dam_availability_rebasis` R; MOM daily-grain outage shape (≲0.11 pp);
`cc_nameplate_summer_derate` refused-insufficient. The maxgen slack-cost ceiling
($500/$1,000 in declared windows) is inert today (model max $227) but is the binding
ceiling any successful tail lever will eventually meet — noted for lever-1's A/B
expectations, not touched.

## 9. PREREG sketch for lever 1 (the D-1 charter deliverable, not a prereg)

- **Mechanism (proposed form):** one gated `ScenarioConfig` field (default off), e.g.
  `miso_offer_level_dispersion`: the class-tranche offer multipliers are replaced by a
  **measured across-unit markup-over-reference quantile vector**, grafted by rank
  correspondence within the merit stack at build time. Parameters = the measured
  quantiles + identification metadata; zero LMP-identified values; rules 23/24
  (re-derives only on data change; registered, run_config-recorded).
- **Identification:** pooled JJA 2023–2025 DA offer book (per-unit base level =
  cleared-agnostic declaration at each unit's own operating point), normalized to a
  cost reference so the vector is a markup DISTRIBUTION that regenerates forward
  (stationary conduct parameter; annual re-derivation from each year's published book,
  90-day lag — the ERCOT-223 pattern).
- **No-LP pre-check (kills before any solve):** (K-PRE-a) reconstruct the model's
  implied across-unit offer-level distribution at the summer top decile from the
  committed keeper artifacts + the offer-curve rebuild (the `_miso156.model_year`
  path, already running in `_miso178_c3a_decomposition.py`) and compare to the book's
  p50/p90/p95/p99 — if the model already carries ≥half the measured dispersion at the
  margin, the object is smaller than Δ₁ claims: STOP; (K-PRE-b) measure the
  price-setting eligibility of the dispersed mass (share of book units above the
  model's clearing rank that are NOT self-scheduled/must-run) — if the dispersion
  lives below the margin: STOP; (K-PRE-c) predicted 2023 shift vs band headroom.
- **A/B gates (successor LP session, 15 GB recipe per FINDING-miso169):** control
  bit-identity 12/12; C3a-2025 target improvement with **2023/2024 inside band**;
  C3b NRMSE ≤ gate all years; C8/D-4 zero new conduct failures; DOF ledger
  `n_residual` UNCHANGED (the quantile vector is measured, not fitted); the §7
  falsifiable prediction reported (South own-err movement); against-interest lines
  reported at full magnitude.
- **Kills:** K-PRE-a/b/c above; 2023/2024 band exit; C3b fail; any D-4 conduct
  failure; any parameter that can only be identified from a price residual.

## 10. Owner decision points

- **D-1 (lever 1):** charter the across-unit dispersion object? Two rulings inside
  it: (i) the admissibility FORM — a measured conduct distribution (ex-ante offer
  declarations, rank-mapped, no unit/class pinning) as a solve input, on the
  ercot-223 armed-conduct precedent; (ii) the ~430 MB corpus refetch. The PREREG
  sketch (§9) is ready to be written up in full on a yes.
- **D-2 (lever 2):** the standing 5(i) ruling — is a seam-import envelope conditioned
  on the neighbour's own coincident load admissible in kind (forward driver), or
  refused as residual-correlated? miso-176's FFE evidence is the factual base; the
  build would wait for lever 1 regardless.
- **D-3 (lever 3):** charter the South under-export evidence session (driver hunt:
  firm/JOU export schedules to SOCO/TVA — the Manitoba-block admissible shape), noting
  part of the South symptom is predicted to resolve via lever 1?
- **D-4 (posture):** the standing determination-posture question (matrix §5.4 item
  iv) — unchanged by this session, and moot if D-1 proceeds and lands. If D-1..D-3
  are all refused, §3's measurement stands as the honest record: the annual target is
  deterministic-reachable, so a refusal is a budget decision, not a model-class one.

## 11. Reproduction

```
cd <repo root>
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy --python 3.12 \
  python scripts/probes/_miso178_c3a2025_anatomy.py
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/probes/_miso178_c3a_decomposition.py
```

Records: `results/calibration/_miso178_c3a2025_anatomy.json`,
`results/calibration/_miso178_c3a_decomposition.json`. Holdout: 2023–2025 only
(rule 22; MISO holds neither marker; freeze active). The committed
`metrics.json` in the bundle predates the promotion attestation (its C6 line reads
UNATTESTED); the scored posture cited here is RESULT-miso177's — NOT-YET on C3a-2025
alone, C6 attested, C3c the single ledgered caveat.
