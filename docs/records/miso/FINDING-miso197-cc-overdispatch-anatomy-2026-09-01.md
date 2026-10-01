# FINDING miso-197 — the CC_REGULAR over-dispatch root-caused: a chronic ~10 TWh/yr out-of-merit gas-steamer/CHP allocation defect, exposed at the CC line in the one year the gas-family level lands (2026-09-01)

**Session:** miso-197 (2026-09-01). **Keeper:** `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`), **UNCHANGED**. Zero solve, zero
LP, no field added, no matrix cell tested, no registration (rule 15 not
engaged — nothing ran). This is the FINDING-miso196 §7a/§8.1 named successor:
a root-cause census, not a lever.

**Charter question:** why is MISO CC_REGULAR **+6.664 TWh over** on C1-2024 at
all — the excess the pro-rata outage application was masking, which killed the
W3-unrefuted `cc_outage_derate_from_top` arm (miso-196 K-1) and the duct-cap
arm (miso-193 K-1) before it.

**Method:** the frozen phase-0 census
`scripts/probes/_miso197_cc_overdispatch_phase0.py` — rule frozen in the
docstring and **pushed + blob-verified at `251fb0e2` BEFORE any adjudicating
quantity** (remote blob `076e298c` == local, rule 27), satisfiability-verified
with one disclosed basis correction (slice-keyed plants → per-(plant, class)
ceilings) made pre-freeze. Record:
`results/calibration/_miso197_cc_overdispatch_phase0.json`. Bases: the
keeper's committed sidecars + dashboard payload/bench artifacts, the miso-196
B1 tranche build, raw CAMPD heat-input, the miso-193 duct map. No witness was
weighed against the price residual (rule 1); C3a appears nowhere in the
census.

---

## 1. The answer, in one paragraph

The +6.664 is **not** a CC-specific defect at all. It is the **visible face of
a chronic intra-gas allocation defect**: every year the model under-runs the
price-insensitive gas conduct classes — ST_GAS −3.73/−7.55/−6.55, ST_CHP
−2.96/−2.93/−2.13, CT_CHP −2.82/−2.84/+0.63 (2023/2024/2025, C1 basis) —
about **9–10 TWh/yr** in 2023–2024, because reality dispatches old gas
steamers and cogens **out of merit** (W3b: in the top-quartile ST_GAS hours of
2024, the actual CC class runs at a median **83%** of its own p99.5 — reality
burns 10.2-HR steam gas while 7.1-HR CC capability sits idle; the strict-merit
LP does the opposite) and the keeper's armed `st_gas_mustrun_*` floors carry
only ~5.15 TWh of that conduct (D-2). The LP hands the steamers' energy to the
cheapest gas class — CC_REGULAR (plus CT_PEAKER in 2024). **In 2023 and 2025 a
second, family-level defect masks this at the CC line**: the model's scored
gas family runs **−12.0 / −1.6 / −9.1 TWh** against actuals — its total-gas
response to the 2023→2025 delivered-gas cycle ($2.54 → $2.19 → $3.52) swings
**2.3× the measured swing** (model 187.3 → 205.5 → 185.3 TWh vs actual
199.3 → 207.1 → 194.5) — so in the cheap-gas year 2024 the overshoot crosses
the actual family level (family Δ −1.6 ≈ 0), the mask drops, and the
allocation defect stands naked at the CC line: **+6.664**. In 2023/2025 the
family under-run (−12/−9) swallows it and CC reads −3.7/−2.5. One defect,
two faces: the CC excess and the persistent ST_GAS deficit are the same
object, and the family-amplitude overshoot is plausibly the *same missing
price-insensitive conduct* — a fleet that self-schedules does not double its
switching response when gas gets cheap.

## 2. WHERE (W1) — broad, level-like, shape-neutral

| witness | frozen line | 2024 result |
|---|---|---|
| W1a zonal | top-2 ≥ 70% of positive Δ ⇒ concentrated | **NOT CONCENTRATED** (63.9%): Plains +2.32, Indiana +1.91, South +1.35, Illinois +1.04; East −0.43, West −0.98 |
| W1b monthly | ≥9 pos months & max ≤25% ⇒ level-like | **LEVEL-LIKE**: 10/12 positive, max month 21.2%; spring-tilted (Mar+Apr+May = 3.18 TWh) |
| W1c hour-of-day | max normalized gap ≤ 0.10 ⇒ shape-neutral | **SHAPE-NEUTRAL** (0.047), confirming the committed D-1 r=0.993 |

A broad, all-day, most-months, four-of-six-zone excess — the signature of a
class-level allocation phenomenon, not an event, a zone, or a plant story.

## 3. WHOSE (W2) — spread; not duct, not availability, not a ceiling

- **W2a SPREAD** (top-5 = 54.2% < 60%; Σ positive Δ 13.43 TWh over 40+ bench
  plants). Largest single carrier: **Edwardsport `1004:CC_REGULAR` +2.59 TWh**
  (model 3.75 vs CEMS 1.16) — the known coal-gasification CC slice
  (`cc_steam_part_reclass` U-cell object); real but only 39% of one band.
- **W2b NOT DUCT-SPECIFIC**: duct-flagged plants carry 31.9% of the positive Δ
  on 57.2% of capacity — the miso-193 population is *under*-represented.
- **W2c the jump**: the model's 2023→2024 CC energy jump (+10.04 TWh over
  bench-covered plants vs actual +3.02) is spread across upper-Midwest CCs —
  Mankato +2.91 (actual +0.08), Port Washington +2.06 (actual −0.97), Fox
  +1.73 (actual +0.12) — with plant ceilings essentially flat. The jump is
  merit-order-driven, not fleet- or availability-driven.
- **W2d NOT CEILING-LIMITED in any year** (B1 class ceiling 173.5/172.8/163.3
  TWh vs model 138.1/150.1/135.5 — headroom 22.7–35.4 TWh): the 2023/2025 CC
  *unders* are not an availability bound, and the 2024 over had room. (The
  solve's fleet is ≥ the B1 instrument's at the one divergent plant — §6 — so
  this holds a fortiori.)
- **W2e NOT 2024-AVAILABILITY**: class mean availability 0.722/0.711/0.672 —
  the 2024 "bump" vs neighbors is +1.4 pp < the frozen 2 pp line. (Carries the
  §6 instrument caveat at ±~1 pp; the year-difference is what the line reads.)

## 4. WHAT IT DISPLACES (W3) — the conduct face, and what it is not

- **W3a**: not a clean *monthly* seesaw (corr −0.236 > −0.5) — but the
  **annual** cancellation is near-total: |ΔCC + ΔST| / (|ΔCC| + |ΔST|) =
  **0.119** in 2024 (+6.66 vs −7.55 nets to −0.89). The pair trades at year
  grain, not month grain — consistent with a standing conduct level, not a
  month-shaped event.
- **W3b THE CONDUCT WITNESS**: in the 2,190 top-quartile ST_GAS hours of 2024
  (ST ≥ 2,671 MW), actual CC utilization median **0.833** (p25 0.712 / p75
  0.947) of its own p99.5 — **reality runs ST_GAS while CC has headroom**.
  The model in the same hours: 0.908. Real ST_GAS dispatch is not
  strict-merit against CC; the LP's is. This is the structural driver.
- **W3c HR INPUTS NOT IMPLICATED**: model HR(ST_GAS)/HR(CC) = 11.272/7.395 =
  1.524 vs CAMPD-measured 10.19/7.092 = 1.437 (31 CC / 11 ST_GAS guarded
  facilities) — +6.1%, inside the ±15% line. The mis-ordering is not a
  heat-rate input error; with `offer_curve_overrides = {}` on this keeper,
  the gas offer surface is physical HR × delivered gas + margin, and
  miso-179 already measured the model +$15 *over* the eligible book at
  median rank — the model's gas offers are not "too cheap".
- **W3d absorbers** (scored basis, model − actual): coal family −3.4/−8.3/−7.7
  every year; **wind +4.7/+5.1/+5.1 every year** (model wind above the EIA-930
  actual — a standing ~5 TWh zero-MC over-supply, named for the fleet/
  curtailment lane); imports **+2.0 (2023, over the frozen +2 line)** / +1.5 /
  −0.2 (the miso-178 §5 phantom-import face at annual grain, 2023 only);
  hydro ~−1, nuclear ~−0.3, oil ~−0.4. The `other` panel's +14/+12.8/+5.1 is
  **not** model error — it is the 923-class vs 930-series booking wedge (§5).

## 5. FAMILY GRAIN (W4) — the exposure mechanism

| year | gas family Δ (scored, C1 basis) | CC Δ | W4a intra-family? |
|---|---:|---:|---|
| 2023 | **−11.997** | −3.674 | no — family-level under |
| 2024 | **−1.584** | **+6.664** | **YES — |family| < |CC|: pure reallocation** |
| 2025 | **−9.115** | −2.456 | no — family-level under |

The 2024 CC excess survives at family grain as a **−1.6** — the family is
essentially right and the miss is allocation inside gas. W4b (reported, not
gated): the classFull-sum vs EIA-930 gas wedge is 24.9/27.1/25.2 TWh —
booking basis, not model error; every gate-relevant statement above is on the
scored 923/classFull basis.

## 6. INCIDENTAL — the probe fleet chain is NOT the solve's fleet chain at one plant (disclosed; instrument caveat, not a model defect)

Post-census supplemental diagnosis, clearly labeled as such. The frozen W2d(ii)
"actual > 1.02 × plant ceiling" list fired on Riverside 55641 (2.7×),
Cottonwood 55358 (1.7–2.1×), Moselle/Zeeland (~1.2×). Traced:

- **Riverside is a split-identity accounting artifact, not a defect**: CEMS
  books the whole site under 55641 while the model (and EIA-923) split it into
  55641 + West Riverside 64020; at site grain model 8.07 vs CEMS 8.48 TWh —
  closes. (The W2a per-plant table must be read site-aware for this pair:
  55641 shows −5.94 and 64020 is "model-only" +5.53; they cancel.)
- **Cottonwood is a PROBE-INSTRUMENT divergence**: the solve's own payload
  runs the plant to 1,061 MW (annual mean 630 MW) while the miso-196-pattern
  B1 chain (`load_or_synthesize_bins → bins_to_fleet`) carries **580.4 MW** —
  reproduced in a fresh 2024-first process, and invariant to `year=` scoping
  of `load_fleet_from_csv`. The load-bearing solve does NOT take that chain:
  `run_calibration.run_year` synthesizes bins through **its own copy**
  (`fleet_to_bins(load_fleet_from_csv(...))` → `build_base_fleet` →
  `build_dispatch_fleet`), whose divergence risk the code itself documents
  (the nyiso-89 flag-forwarding note, run_calibration.py:3049). Scanned over
  every CC plant: **Cottonwood is the only genuine divergence** (a Nine Mile
  Point 1403 hit was my scan's own grain error — the scoring transform books
  that mixed plant OTHER_FOSSIL on both sides, correctly outside the CC
  population). Blast radius: per-plant ceilings/availability at ~0.5 GW of
  27.7 GW; every class-grain line above survives (in the safe direction —
  the solve's fleet is larger). **Consequence for the record:** probes must
  treat run_year's own chain as the fleet basis, not
  `fleet.assembly.load_or_synthesize_bins`; miso-196's B1 premise ("the
  shipped path the backcast itself takes") is wrong at exactly such plants,
  though its A/B verdict is unaffected (both its legs were solved runs, and
  its census witnesses were relative on a shared basis). Where run_year's
  extra Cottonwood capacity comes from is NOT identified here — named as a
  handoff item, and it belongs with the already-chartered
  `_CC_PMAX_RECONCILED_PLANTS` order-dependence repair (the same
  fleet-sourcing state family).

Also disclosed: the probe's console summary loop (cosmetic, after the record
was written) crashed on int keys and was fixed post-freeze
(`isinstance(k, str)`); no frozen line or record value was touched.

## 7. What this rules OUT (each on its frozen witness, all against the DO-NOT-REDO ledger)

| hypothesis | verdict | witness |
|---|---|---|
| offer-curve level error (CC too cheap) | **out** — family closed R/I (miso-179/180), HR physics clean, offers measured +$15 over book | W3c |
| duct-band population | **out** | W2b |
| 2024 availability/outage composition | **out** (with §6 caveat) | W2e |
| availability ceiling (any year) | **out** | W2d |
| zonal/topology story | **out** — 4-of-6-zone spread | W1a |
| single-plant/fleet-identity story | **out** — spread; Edwardsport largest at 39% of one band | W2a |
| diurnal-shape story | **out** — shape-neutral, D-1 confirmed | W1c |
| HR inputs | **out** | W3c |
| demand level | **out** — C2/C4 pass standing | public record |

## 8. §5 of the charter — directional pre-registration + materiality, honest to a C1 quantity target

**The repair object** (the successor's charter, not built here): ground the
**out-of-merit conduct of ST_GAS (and the steam/CHP classes)** at its
*measured* level — a re-identification of the EXISTING `st_gas_mustrun_*` /
steam-host family (rule 19: reconcile the mechanism that already owns this
phenomenon; never a new floor stacked beside it), identified from multi-year
CAMPD conduct (rule 13: regenerates for a forward year from the same
derivation, responds to fleet turnover; the existing p25-level identification
already passes this test — the defect is that it carries ~5.15 TWh of a
~12–13 TWh measured conduct).

**Materiality, stated against the C1 quantity target.** CC_REGULAR-2024
+6.664 and ST_GAS-2024 −7.553 both currently PASS C1 (band ±8.00) — the
target is not a flip but the quantity defect itself, which (a) **blocks the
W3-unrefuted `cc_outage_derate_from_top`** (its arm frees +5.29 TWh of
realized CC energy, so re-offering it needs CC-2024 ≤ ~+2.7 → the repair must
move **≥ ~4 TWh** off CC-2024), (b) is the quantity face of the miso-178 Δ₁
price-identity defect (the model's price-setter at implied HR ~12 where the
market's was ~29 — un-run steam gas IS the missing expensive marginal unit),
and (c) sits 1.34 TWh from the band edge, one structural lever from a kill.
The donor pool is sufficient: ST_GAS+ST_CHP scored under-dispatch is −10.5 TWh
in 2024.

**Directional pre-registration for the successor A/B** (frozen here so the
next session inherits it, not decides it):

1. C1 CC_REGULAR-2024 **DOWN** (toward 0) and ST_GAS-2024 **UP** (toward 0),
   each by roughly the grounded conduct increment. Confidence 0.85.
2. **Declared adverse face #1 — 2023/2025 CC.** The same increment pushes
   CC-2023 (−3.67) and CC-2025 (−2.46) further under; with the family-level
   under-run (−12.0/−9.1) unrepaired, CC-2023 can approach its −8 band edge.
   A clean repair of the allocation defect may therefore EXPOSE the
   family-amplitude defect as a new C1 miss — that is the rule-14 pattern
   working as intended (fix the next root cause, never re-mask), and the
   successor must pre-register it as a kill/escalation branch, not discover
   it.
3. **Declared adverse face #2 — C8/rule-20.** ST_GAS 2025 forced share is
   already 34.2% (grounded above the 15%-peaker/30% budget via the D-4+D-1
   provenance path). A larger measured floor raises it further; the repair
   survives C8 only on the grounded path — its mechanism needs a cited
   `D4_WINDOWS` entry and its D-1 shape must stay clean (ST_GAS profile_r is
   0.942–0.977 today; the added conduct must not flatten it).
4. **Price face: design-dependent, must be pre-registered per design.** A
   pure `min_gen` floor is a price-taker — it lowers residual demand and
   moves C3a **DOWN** (the miso-193/196 adverse direction) — while a
   committed-with-real-offer form (min-load + economic segment at the
   steamer's true cost) can let ST_GAS SET price in the hours it really ran,
   moving C3a **UP** and directly at the Δ₁ identity. The successor states
   its form and freezes the direction before solving; per rule 1 the price
   face is reported, never the promotion criterion.
5. **Zero-forcing alternative stated against interest**: if the measured
   conduct can be carried as a *bid-side* object (self-schedule/bilateral
   cost-insensitivity in the offer, not a floor), the C8 exposure vanishes;
   if it cannot be identified forward-reproducibly, the floor form with D-4
   windows is the honest fallback.

**Also named, not chartered** (each its own lane): the standing **wind +5
TWh/yr** over-supply vs EIA-930 (curtailment/930-basis question — it
displaces ~5 TWh of thermal every year); the 2023 **import +2.0 TWh**
annual-grain excess (miso-178 §5's face); the §6 run_year-vs-assembly
fleet-chain divergence (joins the `_CC_PMAX_RECONCILED_PLANTS`
order-dependence charter); Edwardsport's +2.59 (the `cc_steam_part_reclass`
U-cell, owner court per its shard note).

## 9. Governance

Rule 22: 2023–2025 only, no marker touched, holdout freeze untouched, zero
solve. Rule 15: nothing ran, nothing to register. Rule 28: no mechanism
tested — no cell verdict changes; the census is evidence for the queue, cited
from the log. Keeper `2026-08-30-miso-191-bexit` unchanged; C1 16/16 stands.

## 10. Reproduction

```
python3 scripts/probes/_miso197_cc_overdispatch_phase0.py --satisfiability
python3 scripts/probes/_miso197_cc_overdispatch_phase0.py
```
