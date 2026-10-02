# FINDING — SPP close-out wave 1 (zero LP): 0b summer-derate audit and W3 C3c decomposition

- **Lane:** closeout-SPP wave 1 (desk `session_017wUwd6xxLRQKAYiT8G722P`, charter 2026-10-02), branch
  `claude/closeout-spp-wave1`, base `4d459da3`.
- **Plan:** `docs/backcast-closeout-plan-2026-10.md` §3.4 rows 0b and C3c; §5.0 R-10, R-12.
- **Keeper (read only):** `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span`.
- **LP spent:** zero. Nothing was armed, solved, registered or deleted.
- **Probes:**
  - `scripts/probes/_spp_closeout_ct_pmax_basis.py` → `results/phase0/spp/_spp_closeout_ct_pmax_basis.json`
  - `scripts/probes/_spp_closeout_c3c_decomposition.py` → `results/phase0/spp/_spp_closeout_c3c_decomposition.json`

## 0. Lane-overlap check (charter "FIRST")

- **SPP-107 is held by another live session.** Session `session_01AdnPmeuEobd5SfMxSk5FLx` holds it on branch
  `claude/spp-mmu-offer-carrier-repair-gonc4e`, under owner card "Build + solve EXR". It carries a PRECOMMIT
  (`docs/records/spp/spp107/PRECOMMIT-spp-107-mmu-carrier-repair-2026-10-02.md` on that branch). Seven year
  shards had pushed bundles by 04:47Z (`claude/spp107exr-2019..2025`).
- **This lane therefore does not write a second SPP-107 PRECOMMIT.** R-12's "one PRECOMMIT" is met by that
  lane's SPP-107 PRECOMMIT plus the pairing PRECOMMIT in this lane
  (`PRECOMMIT-spp-pair-posture-exr-2026-10-02.md`). The pairing PRECOMMIT adopts SPP-107's arm by
  reference and adds nothing to it.
- The SPP-107 solve ran before W0 merged. That conflicts with the desk sequencing call in plan §6.1, so it is
  flagged to the desk.

## 1. 0b — CT pmax basis vs `SUMMER_CLASS_DERATE`: **a double count, ≈ 2 GW every summer**

**Code path (keeper recipe, every year):**
- The recipe sets `plant_level_fleet=True`. It sets `summer_derate_basis_aware`, `cc_nameplate_summer_derate`
  and `temp_dependent_derate` all to `False`.
- SPP is absent from `CAMPD_BINNING_ISOS` (`config/capacity_market.py`), so `build_base_fleet` takes the
  per-plant EIA-860 loader.
- That loader sets `pmax = net_summer_capacity_mw, else nameplate` (`data/fleet/eia860.py`, "pmax =" block).
- `arrays.py` (flat-derate block, `_SUMMER_CLASS_DERATE.get`) then multiplies Jun–Sep availability by
  0.875 (CT_PEAKER / CT_CHP) and 0.90 (CC_REGULAR / CC_CHP).
- This is the same object miso-141 measured and miso-148 repaired in MISO.

**Measured (the loader the solve calls, per vintage year):**

| year | CT_PEAKER pmax, GW | share on net summer | share on nameplate | measured np→ns gap | flat | CT_PEAKER MW removed twice | CC_REGULAR on ns / removed | total double count (Jun–Sep) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 10.23 | 93.4 % | 0 % | 14.3 % | 12.5 % | 1,195 | 70.9 % / 706 | **1,985 MW** |
| 2020 | 10.23 | 93.5 % | 0 % | 14.0 % | 12.5 % | 1,196 | 69.7 % / 697 | **1,976 MW** |
| 2021 | 10.12 | 93.6 % | 0 % | 13.9 % | 12.5 % | 1,183 | 69.7 % / 636 | **1,903 MW** |
| 2022 | 10.40 | 93.8 % | 0 % | 13.8 % | 12.5 % | 1,220 | 69.6 % / 635 | **1,939 MW** |
| 2023 | 10.50 | 94.1 % | 0 % | 14.2 % | 12.5 % | 1,235 | 69.7 % / 635 | **1,955 MW** |
| 2024 | 10.57 | 94.0 % | 0 % | 13.9 % | 12.5 % | 1,242 | 69.4 % / 625 | **1,952 MW** |
| 2025 | 11.68 | 93.9 % | 0 % | 13.5 % | 12.5 % | 1,371 | 71.8 % / 651 | **2,106 MW** |

- CT_CHP is 100 % on net summer (~42 MW), and so is CC_CHP (~42 MW); both are in the total.
- **CT_PEAKER:** the rest of its pmax (~6 %) matches neither rating within 1 %. These are mixed-technology
  plants; the probe reports them as `pmax_other_mw`.
- **CC_REGULAR:** 1.4–2.2 GW is clipped by the CC guard onto a nameplate-like basis. On those plants the
  ambient derate is legitimate, and the probe leaves them out of the double count.
- **2022 anomaly:** the CC measured gap reads −1.2 % in the 2022 vintage. That is EIA-860 2022 summer-above-
  nameplate rows. The probe's totals do not depend on it.

**Verdict.**
- The flat derate is a second ambient haircut on a capacity that already carries it. For CT_PEAKER, the
  measured 13.5–14.3 % gap is already inside pmax.
- It removes 1.9–2.1 GW of thermal capability every Jun–Sep hour, in every SPP year.
- **The fix belongs to W0** (plan §2.1 row 2, E.1: "the flat class derate is deleted for plant-level fleets").
  It is not made here, and it was routed to the W0 lane (`session_018DsgkLcN1h8NQc2yJegmdN`) the same day.

**Interaction with SPP-106/107.**
- Under `spp_mmu_offer_unavailability`, every fossil row skips the flat derate (`_mmu_row` in `arrays.py`).
  The MMU's measured Jun–Sep ambient MW replaces it.
- So the W0 deletion is **LIVE on the current keeper** (spp100), and **INERT for fossil rows on an EX/EXR
  keeper**.
- **Consequence for SPP-107's prediction.** Part of EXR's solved Δ is the removal of this double count, a
  correctness repair, and the rest is the MMU bands. A post-W0 control would separate them; the SPP-107 RESULT
  should not attribute the whole Δ to the MMU classes.

**Matrix:** the SPP `summer_derate_basis_aware` cell stays **U**, because nothing was armed. The evidence is
appended (rule 28).

## 2. W3 — C3c decomposition, every registered year (zero LP; for the owner's R-10 classification)

**Scored quantities:**
- **Actual:** the RT hub average above $200 (`TAIL_THRESHOLD["SPP"]`).
- **Model:** the P1 max zonal dual above $200.
- **DA:** SPP's own day-ahead hub average in the same hour.
- **LMP components:** hub means of `actual_lmp_components_hourly_zonal_SPP`.
- **Reserve MCPs:** zone-hour means of the 5-minute RTBM posts (`spp-or-mcp`).

| | 2019 | 2020 | 2021 | 2022 | **2023** | **2024** | **2025** |
|---|---:|---:|---:|---:|---:|---:|---:|
| RT tail hours (actual) | 47 | 23 | 140 | 99 | **42** | **59** | **68** |
| model hours > $200 (keeper) | 0 | 0 | 352 | 0 | **0** | **7** | **2** |
| … of which inside the RT tail | 0 | 0 | 99 | 0 | 0 | 2 | 0 |
| DA hours > $200 (whole year) | 0 | 0 | 154 | 12 | 6 | 35 | 0 |
| tail hours with DA > $200 | 0 | 0 | 90 | 1 | **0** | **14** | **0** |
| tail hours with DA $100–200 | 0 | 0 | 1 | 49 | 2 | 13 | 2 |
| tail hours with DA ≤ $100 | 47 | 23 | 49 | 49 | **40** | **32** | **66** |
| median RT / DA in tail hours, $ | 260 / 33 | 255 / 31 | 526 / 2,061 | 264 / 101 | **272 / 37** | **244 / 72** | **292 / 47** |
| median RT − DA, tail / all hours, $ | +238 / −3 | +232 / −3 | −640 / −6 | +182 / −7 | **+227 / −4** | **+182 / −4** | **+244 / −6** |
| RT premium carried by the energy component (MEC) | 102 % | 99 % | 104 % | 99 % | **98 %** | **95 %** | **99 %** |
| median RT congestion (MCC) in tail hours, $ | 0.0 | 0.0 | −10.7 | 3.0 | −1.0 | 5.1 | 0.0 |
| RegUp MCP median, tail / all hours, $/MW | 196 / 5 | 187 / 6 | 282 / 9 | 169 / 9 | **154 / 5** | **129 / 7** | **167 / 7** |
| Spin MCP median, tail / all, $/MW | 136 / 2 | 163 / 2 | 204 / 2 | 74 / 2 | **34 / 1** | **28 / 1** | **32 / 0** |
| tail hours with hour-mean Spin MCP > $100 (offer cap) | 27 | 14 | 92 | 37 | **15** | **16** | **16** |
| RampUp MCP median, tail / all, $/MW | — | — | — | 17 / 0 | **12 / 0** | **9 / 0** | **14 / 0** |
| keeper P1 price, median in tail hours, $ | 26 | 26 | 252 | 64 | **30** | **34** | **36** |

**Reading for 2023–25 (the C3c FAIL rows):**
1. **An RT-only object.**
   - SPP's own hourly, security-constrained DA market clears ≤ $100 in 40/42, 32/59 and 66/68 tail hours.
   - It clears > $200 in 0, 14 and 0 of them.
   - The tail hour's median RT − DA wedge is +$227 / +$182 / +$244, against −$4 to −$6 in an ordinary hour.
   - 2024's 14 DA-visible hours are the January 2024 Heather event: DA reached $564, and the keeper prices 7
     hours above $200 that year.
2. **System-wide energy, not congestion.**
   - 95–99 % of the tail-hour RT premium is in the energy component.
   - Median congestion is between −$1 and +$5. This confirms SPP-29 §1b on the current keeper.
3. **Co-occurs with 5-minute reserve and ramp scarcity.**
   - RegUp clears at a median $129–154/MW in tail hours, against $5–7 elsewhere.
   - The ramp-up product (posted from 2022) clears $9–14 in tail hours and $0 at the median elsewhere.
   - The hour-mean Spin MCP exceeds the $100/MW contingency-reserve offer cap in 15/16/16 of the
     42/59/68 tail hours. At least one interval in those hours priced on the demand curve.
   - In this hourly read, shortage pricing explains the tail in roughly a quarter to a third of tail hours,
     not all of them. The rest is the RT offer markup SPP-29 measured: a median $208–254 over the marginal
     unit's cost.
4. **Quantity is not the cause.**
   - The keeper's tail-hour price ($30–36) sits on the DA level ($37–72), not on RT.
   - SPP-29 §2 measured net load right to 0.25–0.52 GW, against the 5.8–11.1 GW that would have to vanish.

**2019–2022 for completeness (not C3c-failing rows):**
- **2021 (Uri):** both DA and the model see the tail. The model over-counts (352 h vs 140), and C3c reads on its
  own band.
- **2022:** gas-price-driven. Half the tail hours had DA at $100–200.

**Proposed owner classification (R-10, D-P5):**
> SPP C3c 2023–2025 is **`model-class`**: 5-minute real-time scarcity and offer markup. Of the RT tail hours, 42/42, 45/59 and 68/68
> clear at or below $200 in SPP's own hourly day-ahead market (100 / 76 / 100 %). The tail premium is ≥ 95 % energy component. It co-occurs with 5-minute
> RegUp / Spin / ramp-up shortage pricing. An hourly, perfect-foresight, energy-only LP is out of
> representation for it (rubric §C3c).

- The classification is for 2023–25 only; 2024's 14 DA-visible Heather hours are named inside it.
- 2019–22 is out of scope, because C3c is not a failing row there.

## 3. Not done here, and why

| item | status |
|---|---|
| 0a shadow-score on the 930-aligned basis | **waits** on lane closeout-D (R-4 study), per the charter |
| 0c `_spp96_reserve_coopt_phase0.py` on posture legs | **not runnable**: the SPP-102 legs are gitignored and not on disk (RESULT-spp-102 §5). Re-run on the pairing bundle (PRECOMMIT-spp-pair §6). |
| step 3 (STB EP 724 rail) | **waits** on the owner's download (R-17 defer) |
| SPP-107 PRECOMMIT | **held by another session** (§0) |

## 4. Rules

- **1 / 13 / 14:** no value was chosen on a residual. The probes read published EIA-860 ratings, SPP market
  prints, and the committed keeper bundle.
- **19:** the 0b finding names a stacked mechanism. The repair is routed to one place (W0) and not duplicated.
- **28:** only `mechanism-matrix/SPP.js` was edited. Cells stay as they were, with evidence appended.
- **29:** zero-LP phase 0.
- **31:** nothing was deleted.
