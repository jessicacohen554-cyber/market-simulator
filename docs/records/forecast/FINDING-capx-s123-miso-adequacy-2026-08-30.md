# FINDING — capx S-123: the MISO adequacy package (S-1 + S-2 + S-3), with the D9 disposition

**Session:** S-123 MISO ADEQUACY PACKAGE (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-30 · **Branch:** `claude/capx-s123-miso-adequacy-ukgiow`
**Charter:** execute the three published-source terms of
`FINDING-capx-d2b-i7-ledger-2026-08-25.md` §8 (lanes S-1/S-2/S-3) as one
package against MISO's 6,037 MW 2026 base-year I7 gap — "together they
plausibly account for the whole 6,037 MW base-year gap, and none may be sized
against the residual" (§10 rec. 1) — riding the director's D9
(`ba_code="SOCO"`) with it.

---

## 0. Headline

**All three terms shipped, each from a single published operand chosen by a
pre-stated rule; together they swing the 2026 position by +15,380.1 MW —
2.5× the 6,037 MW gap — so the closure is over-determined, not fitted.**
The per-term contributions, each declared before the verification solve:

| term | operand | source | 2026 effect (at the FFR-1C epoch peak 128,548.607) |
|---|---|---|---:|
| **S-1** requirement re-vintage | PRM ICAP 15.7% paired with its own 1.079/1.157 conversion (composite = peak × 1.079) | MISO PY 2025-26 LOLE Study Report, Module E-1 (same document, both halves; citation was already in-repo at the ratio entry) | **−2,637.4 MW** of requirement — exactly the charter's pre-declared number |
| **S-2** external-capacity intake | External Resources cleared 3,505.9 MW ZRC, Summer 2025 | MISO PY 2025/26 PRA Results Posting (05/29/2025 corrections), p.22 Summer supply trend table | **+3,505.9 MW** of accredited firm |
| **S-3a** LMR/DR reconciliation | Demand Resources cleared 9,004.4 MW ZRC ÷ Initial PRMR 135,213.4 (f = 0.0665940) | same posting, p.22 (numerator) and p.18 System column (denominator) | **−9,236.8 MW** of requirement (on the S-1 base) |
| **package** | | | position −6,037.0 → **+9,343.2 MW** (pre-solve arithmetic) |

**The honesty tests, carried as declared.** S-1 was shipped because the
source updated (PY 2025-26 publishes both halves of the pair), and its
−2,637.4 MW lands on the charter's advance declaration to the decimal. S-2's
pre-declared band was "O(10³) MW against a 6 GW gap — a large minority": the
published operand is 3,505.9 MW = 58% of the gap, O(10³) as declared, at the
upper edge of "minority" — and it was fixed by the posting's category row
before any solve. No term was "finished off" against the residual: S-2 and
S-3a were each read off the same already-committed-cited PRA posting the
repo's other MISO capacity anchors use, and the package *overshoots* the gap
by 2.5× — the NYISO-intake overshoot signature (77× there), not a tuned
closure.

**D9 is adjudicated, not shipped:** `ba_code="SOCO"` is unreachable at HEAD
on every lane (§5) — the accurate TVA re-point is routed with its data
prerequisite, and a NEW latent defect found on the same trace (armed-interface
forecast years leave seam rows at their mc=0 build placeholder) is routed to
the director.

Verification: §6 (the solo MISO T1-F re-measure and FC-1 re-score).
**VERIFIED 2026-08-31 (S-123-V, run `miso-2026-2030-s123-verify`):** the
+15,380.1 MW pre-solve swing measures **+15,380.2 MW**, every requirement-side
term lands to the decimal, and **I7 closes in all five years** (FC-2 CAVEAT →
PASS). **The determination does NOT move: it stays HOLD**, because FC-1 still
fails — on **I3** (unserved energy 2029/2030), not I7. With the requirement
corrected the adequacy backstop no longer triggers (0 MW, every year) and the
un-backstopped fleet thins past the I3 gate. Full magnitude and the measured
mechanism in §6.

---

## 1. S-1 — requirement re-vintage (shipped)

`PLANNING_RESERVE_MARGIN_BY_ISO["MISO"]` 0.179 → **0.157**
(`src/market_sim/config/capacity_market.py`). The shipped composite had
multiplied the **PY 2024-25** ICAP PRM (17.9%) by the **PY 2025-26**
ICAP→UCAP conversion (1.079/1.157) — peak × 1.09952, equal to NEITHER
planning year's published requirement. The re-vintage takes the SAME
document's pair (PY 2025-26 LOLE Study Module E-1: "Summer PRM stated both
ways: ICAP 15.7%, UCAP 7.9%", the citation block already at the ratio
entry), so the composite is now peak × 1.157 × (1.079/1.157) = **peak ×
1.079** — the document's own UCAP-stated requirement construction.

* **Rule 23 basis: the source data updated.** PY 2025-26 publishes both
  halves; nothing here responds to a residual — the −2,637.4 MW effect was
  declared by the chartering finding *before* this session existed.
* **Not a bookkeeping push.** The requirement feeds the retirement
  reliability floor and the backstop in every forecast solve (the declared
  reason the D2-B session routed rather than shipped it); hence the §6
  re-measure. It does NOT reach any backcast solve: no consumer of the PRM /
  DR / external-tie registries exists in the dispatch/pipeline/results path
  (verified by sweep), and the backcast solves every year with `fleet=None`
  so `evolve_fleet` — the only route to `resolve_adequacy_requirement_mw` —
  never runs. The charter's stop-condition (backcast-solve behaviour
  reached) was checked and is NOT triggered.
* Pinned by `TestMisoAdequacyPackage::test_s1_prm_pair_is_same_document_py2025_26`
  (the pair composes to 1.079 to 9 places).

## 2. S-2 — external-capacity intake (shipped)

`ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"] = 3_505.9` — MISO's published PRA
external-resource accreditation on the FF-2B construction, the second
instance of the NYISO external-capacity defect (dispatch floors a 1,400 MW
Manitoba firm-hydro block in every hour, default-on, while the adequacy
ledger credited 0 MW external).

* **The operand:** PY 2025/26 PRA Results Posting, p.22 "Summer Supply
  Offered and Cleared Comparison Trend", category **External Resources,
  Cleared (ZRC), Summer 2025 = 3,505.9 MW** (offered equals cleared). The
  five category rows (Generation 120,738.6 / External 3,505.9 / BTMG 4,282.8
  / DR 9,004.4 / EE 27.6) sum to the System committed total 137,559.3 — the
  row is one line of MISO's own supply accounting of what cleared against
  the PRMR, i.e. exactly "what the ISO's ledger counted for the delivery
  year" (the PJM Table-7 / NEISO FCA / NYISO Gold-Book discipline).
* **One basis, and the conversion is the identity.** A ZRC is 1 MW of
  Seasonal Accredited Capacity — MISO's availability-based UCAP-equivalent
  unit, the basis the (1 + PRM_UCAP) requirement is stated on. The NYISO
  entry's × 0.8679 translation is therefore the identity here; the pin that
  the entry is the verbatim published operand replaces the NYISO lane's
  factor-identity test.
* **Rejected bases, pinned by test:** the 1,400 MW Manitoba dispatch
  constant (inherited ladder spec constant, not an accreditation); the zonal
  tables' ERZ-column committed **1,580.1 MW** (only the portion clearing in
  the External Resource Zones proper — the category row is the full
  external-resource count); any CIL (a deliverability limit — the
  CAISO-entry discipline).
* **Vintage:** PY 2025-26, the anchor vintage of every other MISO adequacy
  input (PRM pair, DLOL hydro credit, RBDC/CONE). Deliberately NOT the
  PY 2026-27 posting — mixing it with the PY 2025-26 requirement pair would
  remake the mixed-vintage composite S-1 just removed. Routed: refresh all
  four MISO operands together on a PY 2026-27 re-anchor (rule 23).
* **Corroboration:** the PY 2025-26 Indicative DLOL results credit "Firm
  External Support UCAP" 1,953 MW (Summer) in the study-side construction —
  same order of magnitude under a methodology not yet in force (DLOL goes
  live PY 2028-29); the PRA cleared record is the market-implementation
  quantity and is the intake.
* **Environment note:** `cdn.misoenergy.org`, HTTP-403 at the July intake
  attempts, now fetches — both source PDFs were re-fetched and hand-read
  this session; sha256 identity records added to `data/raw/miso-pra/
  SOURCES.md` (payloads not committed, the corpus posture). The posting's
  p.18 zonal table reproduces the committed `auction-price/miso/miso.csv`
  PY 2025-26 summer rows to the digit.

## 3. S-3 — ledger differencing (solve-free), and the shipped S-3a term

### 3a. The LMR/DR documented reconciliation (shipped)

`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"] = 9_004.4 / 135_213.4`
(= 0.0665940). MISO does not net load-modifying resources from its load
forecast — LMRs qualify as ZRCs and clear the PRA as capacity **supply**
toward the PRMR, the exact PJM situation, so the entry is a documented
reconciliation (rule 14), never a raw fraction of peak:

* **Numerator:** Demand Resources cleared, Summer 2025 = 9,004.4 MW ZRC
  (offered equals cleared; p.22).
* **Denominator:** the System Summer **Initial PRMR** 135,213.4 MW SAC
  (p.18) — the pre-auction requirement, peak_forecast × (1 + PRM_UCAP), the
  exact analogue of the PJM entry's pre-auction RTO Reliability Requirement.
  Because the registry nets the gross peak BEFORE the (1 + PRM) × ratio
  multiplication, dividing by the published requirement makes the netted MW
  reproduce MISO's supply-side counting: f × peak × 1.079 = 9,004.4 ×
  (model peak × 1.079 / 135,213.4).
* **Excluded, conservatively** (the PJM PRD-exclusion precedent — omitting
  under-credits): BTM Generation (4,282.8 MW ZRC) — an unmeasurable share of
  registered BTMG operates at peak in the normal course and is then already
  embedded in the model's EIA-930 metered demand path, so netting the full
  ZRC risks a double count; Energy Efficiency (27.6 MW) — embedded in
  metered demand by construction, and immaterial. Routed refinement: an
  operating-mode split of MISO's registered BTMG fleet would license the
  BTMG share as a published-source intake.
* Rule 13: recurring seasonal product, condition-responsive (Summer cleared
  DR 7,694.6 → 8,109.4 → 9,004.4 over 2023→2025).

### 3b. The class-by-class differencing (the FFR-3P Table-1.1 method) — fork 2 ADJUDICATED

Model 2026 base-year ledger (the FFR-1C after-ledger, reproduced by D2-B to
the MW) against MISO's own two published records — the PY 2025/26 PRA Summer
cleared supply (SAC/ZRC) and the PY 2025-26 Indicative DLOL class UCAP table
(Summer column):

| class | model firm MW | PRA cleared (SAC) | DLOL indicative (UCAP) |
|---|---:|---:|---:|
| thermal | 124,464.4 (UCAP = 1−EFORd on 132,889.8 nameplate) | — (inside Generation) | 104,108 (Biomass 260 + Coal 34,977 + DualFuel 6,572 + Gas 20,318 + CC 28,797 + Nuclear 11,922 + Oil 1,262) |
| wind | 5,312.0 (32,000 × 0.166) | — | 2,190 |
| solar | 1,260.0 (7,000 × 0.18) | — | 2,861 |
| storage | 2,797.6 | — | 2,604 (PS 2,564 + Storage-SQ 40) |
| hydro | 1,470.3 (2,371.5 × 0.62 RoR) | — | 2,567 (Reservoir 1,846 + RoR 721) |
| **internal generation total** | **135,304.3** | **120,738.6** ("Generation") | 114,288 ([N], all classes) |
| external | 0 → 3,505.9 (S-2) | 3,505.9 | 1,953 ("Firm External Support") |
| BTMG | — (excluded, §3a) | 4,282.8 | 4,050 |
| DR | — (netted via f, §3a) | 9,004.4 | 7,852 |

**Fork 2 (fleet-snapshot under-count) is REFUTED as a deficit driver.** The
model's internal-generation ledger EXCEEDS MISO's own cleared internal
generation by **+14,565.7 MW** (+12.1%) and the DLOL indicative class total
by +21.0 GW — the CAISO lesson (a missing battery vintage worth 90% of the
deficit) has no MISO analogue. The whole 6,037 MW gap lived on the
requirement side (S-1, S-3a) and the external term (S-2). Per-class notes:
the model's wind credit (5,312) sits between MISO's two published
constructions (DLOL 2,190; the PY 25-26 seasonal capacity-credit report's
marginal ELCC 20.8% × 28,335 MW ≈ 5,894); storage matches DLOL within +7%;
hydro is the documented conservative RoR-class floor (1,470 vs the 2,567
two-class blend — the routed per-plant class-split refinement of the
FFR-1C registry).

### 3c. The peak-basis check (B-4 class, diagnostic — nothing shipped)

The model's simulated 2026 weather-year peak **128,548.6 MW** against MISO's
own planning quantities: **+3,235.0 MW (+2.6%)** above the PRA-implied
1-in-2 coincident forecast (Initial PRMR / 1.079 = 125,313.6), **+4,972.6
(+4.0%)** above the DLOL document's system peak (123,576). Both published
anchors are summer-2025 planning values while the model peak is 2026, so
roughly one year of real growth (~1.0-1.3 GW at MISO's ~0.8-1%/yr) is
legitimate inside the difference; the residual ~2-3.7 GW same-year excess is
the same sign and order as FFR-3P's CAISO +3,435 MW B-4 measurement. The
model's requirement deliberately rides its own simulated peak (structural
self-consistency), so this is recorded as measurement, not repaired.

## 4. What the package changes, and what it cannot touch

* Consumers of the three registries: `resolve_adequacy_requirement_mw`
  (reliability floor + backstop + I7/I12 checker), the CR-1 reserve
  position / capacity-price path, `accredited_firm_capacity_mw`
  (`_firm_import_mw`), and two scorer surfaces (`forecast_verdict` FC-2
  terminal band — T2/T3 only; `ff_readiness_battery` info row). All
  forecast-lane; **no dispatch/pipeline/backcast-path consumer exists**
  (swept). No `ScenarioConfig` field was added, no mechanism armed — matrix
  guard green, no cell edited, none required (registry constants with
  published citations are inputs, rule 28's own carve-out).
* Deconfliction honoured: no keeper shard, `status/*.js`,
  `calibration-complete.json`, offer curve, commitment bridge, or MISO
  backcast matrix cell touched. `git ls-remote` at session start: no MISO
  backcast branch in flight.
* `frontend/data/parameters.json` (the parameter-citation registry) still
  carries the pre-package values — it was last generated 2026-08-18 and
  already lags several landed lanes (e.g. no NYISO external-tie row); CI
  does not gate on it. Left for the next registry regeneration, noted here
  so the drift is attributed.

## 5. D9 — the MISO South seam `ba_code="SOCO"` (adjudicated UNREACHABLE; routed, with one new defect found)

miso-183 handed forward: the South seam names SOCO as its representative BA
while SOCO is the one southern counterparty MISO essentially never exports
to (0.1-0.3% of gross; TVA is 79-86%). This session measured the field's
actual reach — its only role is selecting the EIA-930 demand shape of the
gas-elastic reference-price fallback (`data/neighbor_price.py::
_neighbor_load`), and that fallback is unreachable at HEAD on every lane:

1. **Backcast keeper years 2023-2025:** the armed measured seam ladder
   (`MISO_SEAM_LADDER_BY_YEAR`, verified: all 8 bands × both directions ×
   all four seams × all three years) displaces every South band price
   (`import_nodes.py::_inject_seam_ladder`) — miso-183's trace, re-verified.
2. **Default forecast configs:** `reference_price_interface` is default-OFF
   (`REFERENCE_PRICE_DEFAULT_ISOS` arms it for MISO *backcasts* only via the
   calibration CLI); the T1-F interchange is the Manitoba firm block alone.
   The seam nodes are never built, so the fallback cannot fire.
3. **An armed-interface forecast solve year ≥ 2026:** measured directly this
   session — `interface_reference_prices("MISO", y)` resolves NO seam load
   shape for y ≥ 2026 (no EIA-930 extract carries a full calendar year
   there: MISO/PJM/SWPP end H1-2026, SOCO ends 2025), so the SOCO fallback
   never fires there either.

**Disposition: documented at the spec** (citation comment at
`INTERFACE_NEIGHBORS["MISO"]`'s South entry) **and routed, not shipped.**
The accurate re-point (`ba_code="TVA"` per miso-182's measured counterparty
shares) requires an EIA-930 TVA hourly-extract intake and would change no
reachable behaviour today — a no-op re-point naming a BA whose extract does
not exist would resolve through `proxy_ba` back to SOCO and merely *look*
fixed. Routed for whichever lane next arms the interface in a year the
ladder does not cover: (a) intake the TVA extract, (b) re-point
`ba_code="TVA"`, keeping SOCO available as `proxy_ba` if desired.

**New defect found on the same trace (routed to the director):** in an
armed-interface solve year with NO resolvable seam shape (every year ≥ 2026
at HEAD), `inject_reference_price_mc` prices nothing and returns False, and
the seam band rows keep the **mc = 0 placeholder** from
`build_reference_price_node` with live bounds — up to ~14.3 GW of free
import capacity (and free export sinks) in the LP. No default or keeper
config reaches this today (which is why it has never surfaced), but any
future "arm the reference interface in forecast" experiment would silently
solve on free seams. The fix wants a mechanism decision (a flat gas × HR
fallback price when no shape resolves, or a hard refusal), which is outside
this lane's charter.

## 6. Verification — the solo MISO T1-F re-measure and FC-1 re-score

*Pre-solve predictions, recorded in-session before the run* (at the FFR-1C
epoch peak 128,548.607; the HEAD demand path may have drifted — any drift is
decomposed separately below, the NYISO-lane discipline):

* 2026 requirement 141,341.4 → **129,467.1** (S-1 −2,637.4, then S-3a
  −9,236.8); accredited 135,304.4 → **138,810.3** (S-2 +3,505.9); position
  −6,037.0 → **+9,343.2**. I7 2026 → PASS.
* I12: post-package requirement-implied floor (1−f) × 1.079 − 1 = **+0.71%**;
  ledger rm at the epoch peak = **+7.98%** → in-band ([floor, floor+15pp]).
  The very low floor is the honest consequence of MISO's own UCAP-netted
  construction (the PJM FPR-below-1 analogue), and I12's floor moves with
  the resolver by design.
* 2027: the backstop (which closed 2,378 MW net at the old requirement)
  should fire less or not at all; the 2027 leg's residual is measured by the
  run, not predicted here.

**RESULTS (filled by session S-123-V, 2026-08-31).**

**Headline: the package delivers exactly what it declared — I7 CLOSES in all
five years and FC-2 goes CAVEAT → PASS — but MISO's T1-F determination does
NOT move. It stays HOLD, because FC-1 still FAILS on a DIFFERENT invariant:
I3 unserved energy in 2029-2030. The failure moved, it did not clear.** That
consequence was not predicted above, and it is reported here at full
magnitude rather than absorbed: it is an ENDOGENOUS RESPONSE to the package,
with the mechanism measured (below), not a defect in the three terms.

**Run identity.** `miso-2026-2030-s123-verify` · cache key
`587dc5b32ba71ceb` · bundle `results/ff-t1f-s123/verify/MISO/587dc5b32ba71ceb`
· git `54ca19a`, clean tree · `mode=forecast`, 2026-2030, **5/5 years solved**
· wall **1,451.8 s (24.2 min)**, median year 236.5 s · peak RSS **9,877.6 MB
(9.65 GB)**, solo, nothing co-run (rule 12). Posture read off the RESOLVED
config (765 keys), not `args`: `--golden-posture` ⇒
`capacity_market_clearing_by_iso[MISO]=True`; `retirement_rule="pipeline"`;
both entry dampers on; `confirmed_exits_enabled=True`; and MISO's three
`default_scenario_overrides` (`miso_rps_compliance_regions`,
`miso_clean_tier_rows`, `entry_vre_capacity_revenue`) all inherited True —
the same posture the prior bare `miso-t1f` carried.

**Per-year adequacy ledger, with the three-term decomposition.** Each year's
counterfactual is computed on that year's OWN measured peak, so the package
effect is isolated from any HEAD drift (the NYISO-lane discipline). `pre` =
the pre-package registry (PRM 0.179, no DR netting, no external tie; ratio
1.079/1.157 unchanged by the package, verified at `a61b3ec^`).

| year | peak MW | rm | req pre | req post | accr pre | accr post | pos pre | pos post |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026 | 128,548.6 | 9.11% | 141,341.4 | 129,467.1 | 136,756.8 | 140,262.7 | −4,584.5 | **+10,795.6** |
| 2027 | 129,880.6 | 7.75% | 142,806.0 | 130,808.7 | 136,445.8 | 139,951.7 | −6,360.1 | **+9,143.1** |
| 2028 | 131,336.9 | 7.08% | 144,407.1 | 132,275.3 | 137,124.7 | 140,630.6 | −7,282.3 | **+8,355.4** |
| 2029 | 132,921.1 | 2.93% | 146,149.0 | 133,870.8 | 133,313.9 | 136,819.8 | −12,835.1 | **+2,949.0** |
| 2030 | 134,637.3 | 1.17% | 148,036.0 | 135,599.3 | 132,700.8 | 136,206.7 | −15,335.3 | **+607.3** |

| year | S-1 (req) | S-3a (req) | S-2 (accr) | total swing |
|---|---:|---:|---:|---:|
| 2026 | −2,637.4 | −9,236.8 | +3,505.9 | **+15,380.2** |
| 2027 | −2,664.7 | −9,332.6 | +3,505.9 | +15,503.2 |
| 2028 | −2,694.6 | −9,437.2 | +3,505.9 | +15,637.7 |
| 2029 | −2,727.1 | −9,551.0 | +3,505.9 | +15,784.1 |
| 2030 | −2,762.3 | −9,674.4 | +3,505.9 | +15,942.6 |

**Against the pre-solve declaration — every requirement-side number lands
exactly.**

| quantity | pre-declared | measured | Δ |
|---|---:|---:|---:|
| 2026 peak | 128,548.607 | 128,548.6 | **0.0** |
| 2026 requirement | 129,467.1 | 129,467.1 | **0.0** |
| S-1 term | −2,637.4 | −2,637.4 | **0.0** |
| S-3a term | −9,236.8 | −9,236.8 | **0.0** |
| S-2 term | +3,505.9 | +3,505.9 | **0.0** |
| 2026 accredited | 138,810.3 | 140,262.7 | **+1,452.4** |
| 2026 position | +9,343.2 | +10,795.6 | **+1,452.4** |
| I7 2026 | PASS | **PASS** (all 5 yrs, "held") | ✓ |
| I12 floor | +0.71% | **+0.71%** | 0.0 |
| I12 rm 2026 | +7.98% | +9.11% | +1.13 pp |
| 2027 backstop | "fire less or not at all" | **0 MW, every year** | ✓ |

**The single deviation is on the accreditation side, and the demand path has
ZERO drift.** The 2026 and 2027 pre-package requirements reproduce the prior
`miso-t1f` vintage's own I7 row (141,341 and 142,806 MW) to the digit, so the
peak path at HEAD is identical to the FFR-3A-2 epoch (2026-08-03) — the drift
the charter told us to decompose separately is not in demand at all. It is
+1,452.4 MW of *starting-fleet accreditation* in 2026 (prior 135,304 → 136,756.8
pre-tie), a year in which this run executes **zero additions and zero
retirements**, so it is fleet-vintage drift and cannot be a package effect.
The 2027 comparison is *not* clean drift and is not reported as such: the
prior vintage's 2027 accredited (139,147) includes the backstop's 2,378 MW net
close, which this run does not build — −2,378 of the −2,701.2 gap is the absent
backstop (an endogenous package effect), leaving ≈ −323 MW of residual drift.

**Why I3 fails — the measured mechanism, in five steps.**

1. The backstop is **ARMED**: `reserve_margin_build_enabled=None` resolves ON
   for MISO (`resolve_reserve_margin_build_enabled` — capacity-market ISO).
   It is not disarmed; it simply never triggers.
2. The backstop and the reliability floor share **one** requirement
   (`resolve_adequacy_requirement_mw`). Pre-package the position was negative
   in every year (−4,584.5 … −15,335.3), so the backstop had a live trigger;
   post-package it is positive in every year (+10,795.6 … +607.3), so it does
   not fire. **Measured: 0 MW of backstop build in all five years.**
3. Nothing force-builds. Additions are 769.8 MW, all `planned` (EIA-860
   pipeline); economic entry is 0 MW.
4. Retirements total **4,318.3 MW** (2027 gas_st 389.5; **2029 oil 3,295.8**;
   2030 nuclear 617.0 + biomass 16.0) against peak growth of **+6,088.7 MW**.
   Net fleet change **−3,548.5 MW**. Reserve margin falls 9.11% → 1.17%.
5. Slack is present from 2026 and grows monotonically with that thinning,
   crossing the I3 gate (0.01% of load) in 2029:

| year | slack MWh | % of load | hours > 0 | peak slack MW | vs gate |
|---|---:|---:|---:|---:|---|
| 2026 | 35,621.1 | 0.0052% | 7 | 7,756.5 | under |
| 2027 | 45,109.5 | 0.0064% | 8 | 9,008.2 | under |
| 2028 | 56,098.1 | 0.0077% | 11 | 9,875.9 | under |
| 2029 | 145,993.2 | **0.0194%** | 31 | 14,567.7 | **FAIL** |
| 2030 | 231,272.1 | **0.0299%** | 58 | 17,328.8 | **FAIL** |

**Honest limit on the attribution.** Steps 1-4 are directly measured from the
committed ledgers, and step 2's trigger arithmetic is a property of the shared
resolver, not an inference. What is NOT measured is the strict counterfactual:
no HEAD control run with the pre-package constants was solved, because this
charter authorises zero config change (rule 21) and the year budget was the
verification leg alone. So the correct claim is bounded: **the package removed
the backstop's trigger — that is measured — and the un-backstopped fleet thins
past the I3 gate.** Slack already exists in 2026 at 0.0052% with an unchanged
fleet, so the package did not *create* unserved energy; it stopped force-building
against a pre-existing thinning trend. Reading it the other way — that an
over-stated requirement was masking that trend behind ~2.4 GW/yr of manufactured
firm MW — is consistent with every number here and with rule 1, but it is an
interpretation, and a paired control is the instrument that would settle it
(routed, §7 item 7).

**FC re-score** (`scripts/forecast_verdict.py --tier t1f`, committed artifacts
only; `forecast_verdict.json` written beside the bundle):

| gate | before (miso-t1f) | after | note |
|---|---|---|---|
| **FC-1** | FAIL `['I7']` | **FAIL `['I3']`** | I7 closes; I3 2029/2030 opens |
| **FC-2** | CAVEAT (I12 WARN 5.3%/7.1% vs floor 10.0%) | **PASS** | I12 in-band, floor +0.71%; I13 PASS; backstop share PASS |
| FC-3 / FC-4 | n/a | n/a | not scored on a T1-F leg |
| FC-5 / FC-6 | SKIPPED | SKIPPED | no committed corridor / driver battery |
| FC-7 | CAVEAT | CAVEAT | DOF ledger absent — the program-wide FC-7 gap D8 is building |
| FC-8 | CAVEAT | CAVEAT | peak RSS 9.9 GB ≥ 8.6 GB budget |
| **determination** | **HOLD** | **HOLD** | unchanged; basis moves I7 → I3 |

**Observation (routed, not shipped): the three terms are OUTSIDE the cache-key
digest.** `ScenarioConfig.cache_key` hashes `asdict(self)` — ScenarioConfig
fields only — and all three S-123 operands are module-level registry dicts in
`config/capacity_market.py`, not config fields. A container already holding the
pre-package bundle at this key would therefore serve a STALE result for a
post-package run, silently. **This run is unaffected and was verified so before
launch**: the bundle directory did not exist and all five years solved fresh
(`solve_counts` present, 24.2 min of real LP). Filed as §7 item 8 in the same
posture S-123 used for the mc=0 seam defect — named, evidenced, routed, not
repaired inside a verification lane.

**Registration.** Sidecar `frontend/data/hindcast/miso-2026-2030-s123-verify.json`
(single path, `register_forecast_run.py --summary`, `--kind t1f --label
s123-verify`); `run_config.json` + `full_horizon_summary.json` committed (the
`ff-t1f-s123` slim-vs-heavy gitignore block keeps parquet/npz/hourly out).
`ff-verdicts.json` merged preserve-then-overwrite: treatment takes the bare
**`miso-t1f`** key; the pre-package FFR-3A-2 vintage is preserved verbatim
under **`miso-t1f-pre-s123`**. MISO's `program-status.json` board block
refreshed (FC-1/FC-2 rows, I7/I12 detail, S-123 provenance); no other ISO's
block, no backcast surface, no matrix cell touched.

## 7. Routed items (consolidated)

1. **PY 2026-27 whole-package re-vintage** — PRM pair + external ZRC + DR
   fraction, all four operands from the PY 2026-27 documents in one pass
   (rule 23; keeps the vintage unmixed). The PY 2026-27 PRA posting was
   403-blocked at the July intake; `cdn.misoenergy.org` now fetches.
2. **BTMG operating-mode split** — would license the BTMG share of the S-3a
   netting as a published-source intake (§3a).
3. **Per-plant hydro class split** — the FFR-1C routed refinement, restated:
   MISO's own two-class blend (0.793 MW-weighted) vs the shipped
   conservative 0.62 RoR floor (§3b).
4. **TVA extract intake + South-seam re-point** — D9's accurate fix, with
   its reachability precondition stated (§5).
5. **Armed-interface mc=0 seam degradation** — the new defect, to the
   director for a mechanism decision (§5).
6. **`parameters.json` regeneration** — inherited registry lag (§4).
7. **The paired pre-package control, and MISO's late-horizon adequacy** (S-123-V,
   §6) — the instrument that would settle whether the pre-package run shows the
   same I3, i.e. whether the old requirement was masking a real fleet-thinning
   trend behind ~2.4 GW/yr of backstop build. A one-leg HEAD control with the
   pre-package constants (2026-2030, same posture) answers it; it needs its own
   charter because a control arm reverts shipped registry values. The
   substantive object underneath is MISO's own late-horizon adequacy: 4,318.3 MW
   retires against +6,088.7 MW of load growth with 769.8 MW of planned entry and
   zero economic entry, leaving rm at 1.17% and a +607.3 MW position by 2030.
8. **Registry constants sit outside the cache-key digest** (S-123-V, §6) —
   `ScenarioConfig.cache_key` hashes ScenarioConfig fields only, so a change to
   `PLANNING_RESERVE_MARGIN_BY_ISO` / `ADEQUACY_EXTERNAL_TIE_FIRM_MW` /
   `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` does not move the key and a
   pre-existing bundle would be served stale. Same shape as the §5 mc=0 defect:
   no default path reaches it in a fresh container, and it wants a mechanism
   decision (fold the adequacy registries into the digest, or a
   `assert_cache_key_uncontaminated`-style guard) rather than a lane-local fix.

## 8. Governance

* **Rule 22:** forecast-mode 2026+ only; no out-of-training backcast year
  solved, scored or registered; freeze untouched; MISO holds neither marker
  and none was touched. Data intake (two PDF re-fetches) is channel-1
  unrestricted, no-LP.
* **Rule 13/21/23:** every shipped number is a single published operand;
  effects were declared in advance (S-1 by the chartering finding, S-2/S-3a
  in-session before the verification solve); nothing was sized against a
  residual; the package overshoots the gap 2.5×.
* **Rule 28:** no mechanism proposed/tested/armed; no ScenarioConfig field;
  no matrix cell edited, none required; `check_mechanism_matrix.py` green.
* **Rule 27:** Fable session; edits via local Edit + `git push` of exact
  on-disk bytes; post-push blob verification recorded for all ≥300-line
  files (remote head sha == local, per-file content compare OK).
* **Tests:** fast lane 7,327 passed / 8 failed — all 8 reproduce identically
  on the un-edited tree (4 × a CAISO reference CSV absent from this
  session's `miso` hydration profile, 1 × ERCOT keeper parity-registry
  drift from another lane, 1 × marker-state, 1 × CAISO locational-AS, 1 ×
  clean-io datatype list). `TestMisoAdequacyPackage` (7 tests) green.
