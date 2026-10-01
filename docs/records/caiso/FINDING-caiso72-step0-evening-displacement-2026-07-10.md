# FINDING — caiso-72 STEP-0: the evening CT displacement is TEMPORAL (perfect-foresight water + storage hoarding, flat firm imports), not a loose transmission cap (2026-07-10)

**Successor to** `FINDING-caiso71-locational-as-inert-2026-07-10.md` and
`FINDING-caiso70-bridge-decrowding-negative-2026-07-10.md`. Throwaway 2024-only
diagnostic solve on the caiso-70 main recipe (`scripts/probes/_caiso72_step0_diag.py`
→ `results/calibration/caiso72_step0_diag2024`, local only, never registered —
rule 16), analyzed hourly by zone × source × link
(`scripts/probes/_caiso72_step0_analyze.py`). This is the STEP-0 measurement the
handoff demanded before any mechanism change.

## The question and the answer

**Q: in the hours reality runs CT peakers, what does the model serve that load
with instead, and over which link does it arrive?**

**A: mostly not over a link at all.** The model substitutes *time-shifted
domestic flexibility* — LP perfect-foresight hydro + storage hoarded into the
evening block — plus a pre-evening import surplus, for reality's evening gas
and evening imports. The leading transmission hypothesis (WECC imports flowing
into SoCal displace local CT) is **refuted by the flows**: in the deep evening
the model imports **1.4–2.2 GW LESS** than the measured corridors actually
delivered.

Summer (Jun–Sep) 2024, mean MW, model − actual (EIA-930, model-clock-aligned;
water = conventional hydro + pumped storage; batt from the 930 OTH swing):

| hod | gas | water (hyd+PS) | battery(+other) | net_import | model demand − supply-implied load |
|----:|----:|----:|----:|----:|----:|
| 15 | **−2,115** | −1,322 | +445 | **+994** | −1,601 |
| 16 | **−2,569** | −1,265 | **+1,265** | +532 | −1,723 |
| 17 | **−1,920** | −554 | +788 | −111 | −1,649 |
| 18 | −1,197 | +457 | +384 | −770 | −1,061 |
| 19 | −1,216 | **+1,594** | +576 | **−1,380** | −421 |
| 20 | −960 | **+1,514** | +1,017 | **−1,857** | −270 |
| 21 | −336 | **+1,367** | **+1,218** | **−2,202** | +68 |
| 22 | +367 | +924 | **+1,353** | −2,036 | +625 |

Actual CT_PEAKER (CAMPD, summer, mean MW) ramps **621 → 1,115 → 1,706 → 1,955**
across h15–18 and falls to 461 by h22; the model runs a flat **166–720** plateau
sitting 1–2 h later. Three displacement channels, in order of size:

1. **The flexible-fleet hoard (h18–23).** Hydro is a per-plant monthly energy
   budget with `max_mw = nameplate` (`data/hydro.py`) — the LP freely
   concentrates it into the top price hours: model water runs **+1.4–1.6 GW
   over** actual through h19–21 while running **−1.3 GW under** in the h15–16
   ramp (annual: model evening p95 exceeds the measured evening p95 by
   **1–2+ GW in 9 of 12 months**; Jan 5,843 vs 3,568, Dec 5,326 vs 3,024,
   Aug 6,147 vs 5,309). Batteries (`battery_dispatch_adder = 0`, no AS/SOC
   withholding) cycle with perfect foresight: the model discharges
   **+0.4–1.3 GW at h15–17 while the real fleet is still net-charging**, and
   stretches **+1.2–1.7 GW further into h21–23** than the real (4-h,
   AS-committed, uncertainty-bound) fleet does. Together the hoard covers
   ~2.1–2.5 GW of the deep-evening hours that reality serves with gas+imports.
2. **The evening import deficit (h18–23).** The firm/contracted base is
   **3.37 GW flat** (`caiso_perhub_firm_base`) while measured corridor net
   imports ramp 1.8 → 5.6 GW across the evening; spot tranches priced at the
   measured (evening-expensive) Malin/Palo-Verde hubs don't close the gap. The
   model under-imports the deep evening by **1.4–2.2 GW** and over-imports the
   pre-evening (+0.5–1.0 GW at h15–16, +2.3 GW at h14 annual) — the import
   *shape* miss already flagged as Tier-2 in
   `docs/handoffs/caiso-transmission-ttc-diagnosis-2026-07-09.md` §4.
3. **The afternoon demand-basis deficit (h12–17).** The model's demand input is
   the EIA-930 `Demand` series (verified value-identical after clock mapping),
   which in summer runs **1.4–1.7 GW below** the supply-implied actual load
   (930 `net_gen − interchange`; CAISO's own TAC actuals sit in between at
   h14–17) and ~+0.6–1.1 GW above it at h22–23. The model therefore never sees
   ~1.5 GW of the real h14–17 ramp stress — exactly the actual CT window. This
   is a measured-data conflict (two published series disagree), not a loader
   bug: lag tests clear the clock (winter −1 h vs true local is the model's
   documented fixed-PDT convention; summer aligns at lag 0, corr 0.999).

## The links (the topology question the handoff asked)

- **SP15_rest → LA_BASIN (LCT 12,008 MW): never binds.** Evening flow 6.0–7.0
  GW (57 % of LA_BASIN's ~10.9 GW evening load; annual evening max 11,546).
  The pocket boundary exists and is measured — it just is not the constraint
  that calls local CT, because 12 GW ≈ the basin's whole evening load.
- **ZP26 → SP15_rest (Path 26, 4,000 MW): at cap in 85 % of evening hours** —
  the NorCal surplus (hydro hoard + Diablo + CC + **+0.8–1.0 GW over-imported
  COI**: model 1.65–1.73 GW vs measured 0.4–0.9 GW evening) wheels south hard.
  Actual DA evening spreads (NP15−SP15 +$0.8–7.3 in 2024) say real Path-26
  N→S congestion in the evening is mild — the model manufactures the surplus
  it then ships.
- **WECC_DSW → SP15_rest: 1.5–1.8 GW evening — BELOW the measured 2.7–4.7 GW.**
  The 10.6 GW link TTC and the p95 corridor envelope are not what limits it;
  economics (hub price vs SP15) is. Tightening any southern import cap cannot
  create CT energy the model already refuses to import.
- **SP15_rest → SDGE (LCT 1,436 MW): at cap in 27 % of evening hours** — the
  one pocket link doing its job; model SDGE CT (98 MW evening) actually
  *exceeds* its CAMPD actual (48 MW).
- **NorCal CT is missing too** (actual 388 MW evening vs model 14): the Bay
  Area local-capacity pockets (Greater Bay LCR ≈ 7.3 GW) do not exist in the
  5-zone topology — same class of miss as caiso-71 §1 flagged, on the other
  side of Path 26.

## What this closes and what it opens

**Closed** (adds to the caiso-70/71 ledger):
- ~~WECC import links over-serving SoCal evening~~ — model **under**-imports
  the deep evening; corridor/pocket cap tightening is a dead end for the CT
  gap (it would push the mix *further* from actual imports).
- ~~LA_BASIN pocket import cap as the CT driver~~ — the measured LCT link
  never binds; the 2023-static vs per-year choice
  (`caiso_per_year_import_caps`) is immaterial to this gap (per-year values
  are *looser*).

**Open — the ranked structural candidates (all rule-13/14 measured inputs):**
1. **Hydro deliverability envelope** (the largest single displacer): cap the
   hydro fleet's hourly dispatch at the measured per-(month × hod) p95 of
   EIA-930 `WAT` — the exact structural pattern of the keeper-blessed corridor
   ATC envelope (`measured_corridor_flow_envelope`): a capability ceiling the
   LP clears *below*, never a flow pinned to the residual. Physical driver:
   head/flow/min-flow scheduling limits that nameplate-pmax ignores.
   Forward story: multi-year climatological envelope conditioned on
   `hydro_year`, scaling with the monthly budget. Multi-year 930 history
   (2018–2026) is already on disk. Disclosed risk: removes ~1.5 GW of evening
   supply in 2023 too, where the model already prints a spurious 540 h tail —
   rule 1 applies (a real limit stays in; the 2023 tail's root cause is chased,
   not buried).
2. **Shaped firm import base** (Tier-2 of the TTC diagnosis, complementary):
   replace the 3.37 GW flat firm base with the measured overnight/evening
   shape (DMM RA-import + EIM). Without it, an hydro cap partially refills
   from extra spot imports; with it, evening imports land at their measured
   level and the residual falls to gas.
3. **Battery operational realism** (needs new data intake — deferred): the
   model battery fleet discharges into h15–17 and h21–23 windows the real
   AS-committed fleet does not; a measured storage-AS power reservation
   (rule 13's own example) is the honest mechanism, but CAISO storage AS-award
   volumes are not yet on disk.
4. **Demand basis decision** (data question, not a mechanism): adjudicate
   930-`Demand` vs supply-implied load vs CAISO TAC actuals for the backcast
   demand input (rule 14: prefer the accurate measurement; the three disagree
   by ~1.5 GW in the CT ramp window).

caiso-72 builds #1 (with #2 as its pre-registered follow-on), A/B on the
caiso-70 recipe, all three train years, main + zero-forcing ablation twin,
scored on rubric v2.4. Pre-registered directions: CT_PEAKER up toward
4.56/5.24/3.09 TWh with the D-1 profile advancing into h15–18; evening water
p95 down toward measured; C1/C2/C4/C5a move together; disclosed risk on the
2023 tail (may worsen — does not gate the mechanism, rule 1).
