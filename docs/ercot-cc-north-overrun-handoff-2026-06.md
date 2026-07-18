# ERCOT handoff — localize the CC_REGULAR over-run to the North/DFW plant pockets

**Branch off `main`.** **Keeper:** run145
(`results/calibration/run145_rtordpa`, the RTORDPA-overlay keeper; recipe =
run143_redo local-band outages + measured RTORDPA price overlay).
**Read first:** `docs/ercot-offer-curve-meritorder-2023-adder-2026-06.md` (the
within-gas ledger + the offer-stack finding that CC is genuinely cheapest on
energy), `docs/ercot-reserve-supply-scarcity-handoff-2026-06.md`,
`docs/ercot-run131-lmp-decomposition-2026-06.md`, and the 2026-06-17
nodal-pockets session note (referenced in the keeper
`calibration_attestation.json` CC_REGULAR reason: "94% of SCED binding-constraint
rent is on <200 kV local pockets; no unmodelled aggregate GTC isolates the North
over-run").

ENV: `uv sync --extra dev`; co-opt LP ~3–4 min/yr, run **SEQUENTIALLY** (OOM at 4
cores/16 GB if parallel); 3-yr ~13 min. Push to a fresh branch.

---

## The question — and why it is likely the SAME problem as the within-gas miss

The CC_REGULAR class over-runs **+2.7% / +10.3% / +8.8%** (2023/24/25, model vs
CAMPD GWh) — but the over-run is **NOT spread across the fleet**. It is
concentrated in a handful of **North/Northeast (DFW-area) plants**, while
**West / South_Central / Houston (Permian, San-Antonio, coastal) CC plants
under-run**. The net class over-run is a **spatial reallocation**: the zonal LP
puts too much CC generation in the North and too little in the load pockets.

**This is very likely the same phenomenon as the within-gas ST_GAS/CT under-run,
NOT a separate problem.** (Earlier framing called the within-gas swap "settled and
ledgered" — that was too strong: it only established that *lowering* ST_GAS/CT
offers to force them on is a markup (barred). It did NOT establish the volume miss
is irreducible.) The under-runners across **all three gas classes cluster in the
same load-pocket zones** the spatial finding starves:

- **CC under-runners (2024):** Guadalupe (−20%, SC/San Antonio), Quail Run (−25%,
  W/Permian), Odessa-Ector (−10%, W/Permian), Rio Nogales (−15%, SC), Cedar Bayou 4
  (Houston).
- **CT_PEAKER under-runners:** Permian Basin & Ector County (W/Permian), HO Clarke
  & Greens Bayou & Braes Bayou (Houston), Decker Creek (SC/Austin), Victoria (South).
- **ST_GAS under-runners** = the very steamers the keeper ledger named: **Cedar
  Bayou** steam (Houston) and **CPS Energy's O W Sommers / V H Braunig** (SC/San
  Antonio). (These map to `plant_group=OTHER` in the per-plant CEMS fit; the ST_GAS
  C1 benchmark comes from the curated bin sheet.)

So the model **floods the North with cheap CC (Midlothian, Wolf Hollow I) and
starves the Houston / San-Antonio / Permian load pockets**, where in reality local
**CT, ST_GAS, and local CC run behind transmission constraints to serve local
load**. The offer-stack result is the *other half* of the same story: ST_GAS/CT
genuinely offer **above** CC on energy (min-gen ST_GAS $47–71, CT $22–38 vs CC
$7–20), so they only ever run when a **local transmission constraint binds and
forces local generation** — exactly the constraint a 7-zone LP with too-loose
inter-zone transfer limits fails to represent. Re-derive the spatial
representation and **both** the North CC over-run **and** the load-pocket
ST_GAS/CT/CC under-run should shrink **together, from one measured lever** — no
offer markup. The CC-North over-run investigation below IS the within-gas
investigation.

Figure out **why those specific North plants over-run** (= why the load pockets
under-run), decide whether it is a fixable zonal/transfer/availability miss or a
genuinely sub-zonal (nodal) limitation that must be **ledgered** (the rubric's
documented zonal-LP limitation), and do not fit
to the per-plant residual.

### The miss, per plant (run145, model vs CAMPD GWh — verified, this is the target)

| plant (code) | zone (approx) | 2023 | 2024 | 2025 | HR / cap |
|---|---|---|---|---|---|
| **Midlothian Energy (55091)** | North/NE (Ellis) | +3346 GWh (+63%) | **+3760 (+60%)** | +3891 (+56%) | 7.78 / 1734 MW |
| **Ennis Power (55223)** | North/NE (Ellis) | +291 (+20%) | +923 (+56%) | +722 (+46%) | 7.62 / 418 |
| **Wise County (55320)** | North (Wise) | +876 (+26%) | +623 (+18%) | +1278 (+38%) | 7.07 / 822 |
| **Wolf Hollow I (55139)** | North (Hood) | +832 (+27%) | +774 (+24%) | +704 (+23%) | 7.56 / 788 |
| Forney Energy (—) | Northeast (Kaufman) | — | +1293 (+13%) | — | 7.30 |
| Temple (—) | North/SC (Bell) | — | +1308 (+18%) | — | 7.80 |
| Nueces Bay, Barney Davis, Sand Hill | South / SC | — | +1274 (+75%) / +875 (+56%) / +1106 (+52%) | — | 7.8–8.3 |
| **Wolf Hollow II (59812)** — *on target* | North (Hood) | +0.2% | **+4.5%** | +11.5% | 6.83 / 1231 |

**Counter-examples that kill the easy hypotheses (check these first):**
- **Heat-rate merit does NOT explain it.** Midlothian (HR **7.78**, the
  "inefficient" bin) over-runs +60%, while co-located **Wolf Hollow II** (HR
  **6.83**, efficient) is on target. A pure heat-rate merit order would over-run
  the *efficient* unit, not the inefficient one — so the offer-curve class
  multipliers (identical across CC_REGULAR) are **not** the lever (consistent with
  the offer-stack finding that CC is genuinely cheapest on energy).
- **The under-runners are spatial opposites:** 2024 biggest under-runs are
  **Guadalupe −1255 GWh (−20%, San Antonio/SC)**, Quail Run −765 (−25%, Permian/W),
  Odessa-Ector −761 (−10%, Permian/W), Rio Nogales −730 (−15%, SC),
  Thomas Ferguson −514 (−22%, SC). The model **under-serves West/South_Central CC
  and over-serves North/Northeast CC.**

---

## Hypotheses, cheapest-first (decide the shape before spending an LP solve)

1. **Zonal demand allocation (cheapest, no solve).** The model splits ERCOT load
   across 7 zones (West, Panhandle, North, Northeast, Houston, South_Central,
   South). If the **North/Northeast zone demand share is too high** (or West/SC too
   low), the LP fills the excess North demand by running North CCs up the merit
   order — including inefficient Midlothian/Wolf Hollow I — while West/SC CCs idle.
   Check the zonal demand shares (`scripts/data/derive_load_shares.py` /
   `data/raw/zone-specific-demand/`) against the actual zonal load (ERCOT
   ACTUALSYSLOADWZNP6345, the WZ load files already in `data/raw/reference/`).
   This is the single most likely cause and costs no solve.
2. **Inter-zone transfer / interface limits.** Even with correct zonal demand, if
   the **North→South / North→West / North→Houston** export interface limits are too
   tight (or the West/SC import limits too loose), the LP cannot move cheap
   West/SC/coastal generation into the North, so North CCs serve North load
   locally. Inspect the ERCOT interface/transfer limits the model uses
   (`scripts/data/derive_interface_limits.py` / `derive_ttc_limits.py`,
   `data/raw/iso-specific-transmission/`). The 2026-06-17 nodal session ruled out
   an *aggregate GTC* isolating the North — so look at the **directional CSC/SCED
   interface limits between the 7 model zones**, not a single aggregate GTC.
3. **Per-plant delivered gas basis.** CC dispatch order within a zone is
   `HR × gas_delivered + offer`. If North/DFW plants are priced on **too-cheap
   delivered gas** vs West/Permian plants, the merit order inverts. Check the F923
   per-plant monthly delivered gas (`coal_plant_monthly_pricing` analogue for gas;
   `scripts/data/process_f923_fuel_costs.py`) for Midlothian/Ennis/Wise vs
   Guadalupe/Rio Nogales/Quail Run. Permian gas (Waha) is often **cheaper** than
   DFW — if the model has that backwards or flattened to a single hub, West would
   under-run and North over-run exactly as seen.
4. **Per-plant availability / outages.** The CAMPD net-load outage filter is
   class/unit-level; confirm the North over-runners weren't **derated/out** in
   hours the model ran them (compare `campd_op_hours` and the unit-outage CSV vs
   the model's availability for codes 55091/55223/55320/55139). Real Midlothian
   runs ~34% CF (registry `annual_capacity_factor`) vs the model's ~66% — is part
   of the gap real outages/economic-idle the filter missed?
5. **Genuinely sub-zonal (nodal) → LEDGER.** If 1–4 are all measured-correct, the
   residual is intra-North congestion (<200 kV local pockets, e.g. the DFW
   import-constrained load pocket pulls Midlothian/Wolf Hollow I to serve local
   load behind a constraint a 7-zone LP cannot resolve). That is the documented
   **zonal-LP limitation** — ledger the per-plant CC_REGULAR over-run as an
   ACCEPTED MEASURED-INPUT LIMITATION (it already is at the class level), with the
   spatial decomposition as the evidence. **Do not** add a per-plant haircut/offer
   to force Midlothian down — that is a fit to the residual (barred).

## Non-negotiable gates

- **No fit to the per-plant residual.** Any lever (zonal demand share, interface
  limit, gas basis) must trace to a **measured** input (ERCOT WZ load, measured
  CSC/TTC limits, F923 delivered gas), not be dialed until Midlothian = 6.3 TWh.
- **Re-gate the whole fleet, not just these plants.** A zonal-demand or interface
  change moves *every* zone's dispatch — re-solve 3-yr and confirm C1/C2 across all
  classes and the LMP/duration curve do not regress. The intended direction is that
  CC_REGULAR / ST_GAS / CT_PEAKER all move *toward* bench together (the within-gas
  ledger entries shrink); watch that other classes (coal, CC_CHP) don't regress as
  the spatial reallocation unwinds.
- **Spatial check, not just total.** Success = the North/NE CC over-run AND the
  load-pocket (Houston/SC/West) CC+CT+ST_GAS under-run both shrink (the reallocation
  closes), not just the net class total. Score per-plant with the diagnostic below.

## Reproduce / score

```bash
# Per-plant CC_REGULAR over/under-run from the keeper bundle (no solve):
python - <<'PY'
import pandas as pd
f=pd.read_parquet('results/calibration/run145_rtordpa/plant_hourly_fit.parquet')
r=pd.read_csv('data/raw/reference/master-plant-registry.csv')[
   ['plantid','plant_name','plant_group','nameplate_capacity_mw','annual_heat_rate']]
cc=f.merge(r,left_on='plant_code',right_on='plantid').query("plant_group=='CC_REGULAR'")
cc['diff_gwh']=cc.model_gwh-cc.campd_gwh; cc['pct']=100*cc.diff_gwh/cc.campd_gwh
print(cc.sort_values('diff_gwh',ascending=False)[
   ['year','plant_name','model_gwh','campd_gwh','diff_gwh','pct','annual_heat_rate']
   ].query('year==2024').head(15).to_string(index=False))
PY

# Zonal demand shares (hypothesis 1) vs actual WZ load:
#   data/raw/reference/*ACTUALSYSLOADWZNP6345* (ERCOT weather-zone load)
#   scripts/data/derive_load_shares.py ; src/.../iso_configs.py ERCOT zone_names

# Re-solve + score after a measured lever:
python scripts/probes/_keeper_2023as_run.py <out> 2025 2023 '{"ST_GAS":{"committed":0.0}}'   # add KEEPER_RTORDPA=1 to keep the keeper's overlay
python scripts/calibration_verdict.py results/calibration/<out>
python scripts/probes/_ercot_lmp_shape_score.py results/calibration/<out>
# register every run (calibration-report skill, top-15 ERCOT).
```

## Relationship to the within-gas ledger (corrected)
- The offer-stack finding stands and stays in force: ST_GAS/CT genuinely offer
  **above** CC on energy, so **lowering their offers to force them on is a markup
  (barred)**. That bars the *offer-curve* lever only.
- It does **NOT** mean the within-gas volume miss is settled. The spatial/zonal
  lever in this doc is the open, measured candidate that plausibly explains **both**
  the CC over-run and the ST_GAS/CT under-run at once (they sit in opposite zones).
  The keeper's current ST_GAS/CT/CC_REGULAR ledger entries are an **interim** accept
  pending this spatial investigation — if the spatial lever closes the gap, those
  entries should be *removed*, not kept; if it proves the residual is truly
  sub-zonal/nodal (un-representable by any zonal topology), the ledger reason should
  be **updated** to cite the spatial decomposition rather than "AS commitment."

## Out of scope / parallel
- The 2023 out-of-market price tail (RTORDPA overlay + the deferred reserve-supply
  lever) and the 2024-Jan winter tail stay as documented.
