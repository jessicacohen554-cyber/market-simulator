# PRECOMMIT — NYISO-NEXT-5: cap the Long Island seam envelope at the ties' posted import limits

Session NYISO-NEXT-5, 2026-09-27. ZERO LP (rule 32 (a)). **No shard is launched; the owner
decides whether to spend the LP.**

- Keeper: `2026-09-26-nyisonext3-tranche-basis-span` (bundle `results/calibration/nyisonext3_span`,
  `git_sha` 67fd3d1b), plus the stamped 2021 run (`nyisonext3_2021`).
- Probe: `scripts/probes/nyisonext5_li_tie_gap.py`. Record: `results/calibration/_nyisonext5_li_tie_gap.json`.
- Every number below comes from that record.

## 0. The intake was already done

The per-line LI tie schedules are **already committed**, 2018–2026, in
`data/raw/NYISO/interface-flows/` (Ask D1; MIS P-32 `ExternalLimitsFlows`, README and SHA256SUMS
in place). Three rows are the LI ties: `SCH - PJM_NEPTUNE`, `SCH - NPX_CSC` and `SCH - NPX_1385`.
Each row carries two things per hour:

- the mean scheduled flow;
- the hour's **posted import limit**. It is 0 when the line is out.

No new download was needed, and no year was fabricated. The NYISO 5-min zonal RT for 2021 and
2023–2025 (LONGIL bench) was fetched from `mis.nyiso.com/public/csv/realtime/` into scratch. It is
not committed, the same as NYISO-NEXT-4.

**Correction to the handoff's premise.** nyiso-125's identification refusal was never about Long
Island. It covers `Capital_Hudson` and `Upstate_West`, where `SCH - PJ - NY` spans the cutset.
All three LI ties land in Zone K. `seam_flow_envelopes` (K) already sums them with zero
attribution freedom.

## 1. What the model's LI import is, and what is observed

- The committed sidecars carry **no per-link flow**, so the model's LI import is not directly
  observed.
- What is observed exactly is its **cap**. `nyiso_seam_deliverability_envelope` is on, and it sets
  the cap as the p90 of the summed three-line net schedule in each (month × hour-of-day) bin. The
  probe rebuilds it with the production function at the production percentile.
- nyiso-225 §4 measured that link **at its bound in 99.6 % of 2022 hours**. So cap − measured is
  the model's over-import, to within that bound share.

## 2. The gap by year (gap = cap − measured LI net, MW)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Measured net (Neptune / CSC / 1385) | 617 (312/221/84) | 748 (481/212/55) | 844 (631/155/58) | 802 (616/177/9) | 777 (618/166/−8) |
| Model cap, mean | 752 | 906 | 988 | 972 | 929 |
| **Gap, mean / p50 / p90** | **136** / 103 / 330 | **158** / 120 / 385 | **144** / 105 / 350 | **169** / 141 / 365 | **152** / 108 / 360 |
| Gap, TWh | 1.19 | 1.39 | 1.26 | 1.48 | 1.33 |
| Gap with **all three lines posted up**, TWh | 0.68 | 0.90 | 0.64 | 1.07 | 0.93 |
| Unused posted MW when up (Neptune / CSC / 1385) | 294 / 72 / 88 | 166 / 97 / 99 | 10 / 106 / 112 | 12 / 143 / 174 | 21 / 142 / 133 |
| LI price miss, model − LONGIL RT ($/MWh) | −12.76 | −15.26 | −8.62 | −6.08 | −18.07 |
| of which tail (RT > $300) / non-tail | −4.33 / −8.44 | −12.68 / −2.59 | −2.68 / −5.94 | −2.17 / −3.92 | −10.02 / −8.04 |
| corr(gap, miss) | +0.04 | −0.11 | −0.21 | −0.07 | +0.00 |
| LI miss, gap quartile 1 → 4 ($/MWh) | −27.3 → −8.4 | −7.5 → −27.5 | −2.3 → −22.1 | −2.7 → −12.9 | −12.8 → −11.5 |

**Verdict on the gap: it is a LEVEL.**

- The model can import about **140–170 MW more** than the market scheduled, in every year. The
  cause is the p90 construction: a cap sits above the realised flow about 90 % of the time.
- The sign fits the LI low bias: surplus import depresses the LI price.
- Co-occurrence with the hourly miss is **weak**: |corr| ≤ 0.21. The gap quartiles order the miss
  monotonically only in 2022–2024. It is not a shape defect.
- **Most of the gap (51–72 %) remains with every line posted available.** That part is economic
  under-scheduling: CSC and 1385 run 70–175 MW below their posted limits when up. It is set by the
  neighbours' price spreads, not by a physical limit, so it is not identifiable as a measured input.
- The only lever that would remove it is a lower percentile. That is a swept free parameter, and
  rule 1 condition (c) refuses it. **Not proposed.**

**What the per-line data newly resolves** is the physical share. The envelope sums the lines
*before* taking the percentile, pooling each month's outage days with its in-service days. When a
line is out for part of a month, the bin's p90 still assumes it is in service. The model therefore
imports over a tie that is posting 0.

## 3. The lever

**`nyiso_li_seam_posted_limit_cap`** (proposed name, default off). In each hour:

`LI import cap = min(envelope, Σ posted import limit of NEPTUNE + CSC + 1385)`

- **Admissibility.** This is a physical availability event, the same object class as CAMPD
  outage windows (rule 13 names outage windows explicitly), from the same committed P-32 file the
  envelope already reads. It is **backcast/calibration only**, like every outage-window overlay.
  In a forecast year the envelope stands unchanged.
- **Zero free parameters** (rules 21/24). The posted limit is read as published; no percentile,
  threshold or scale is chosen.
- **Rule 19 [R-ONE-MECH].** It is a clip inside the one existing mechanism, not a second
  mechanism. It never raises a cap.
- **Rule 25.** It is NYISO-only, on NYISO's own postings.
- **Implementation (next session, Opus/Fable per rule 27).**
  - One clip in `data/nyiso_seam_envelope.py::seam_envelope_by_zone` for `Long_Island`, gated by
    the new field.
  - Add the field to `run_calibration.py`.
  - Rule 28(c): add the matrix row plus a cell line in every ISO shard, in the same PR.
  - The NYC ties (HTP, VFT) are **out of scope**. They were not measured here, and the PRECOMMIT
    does not extend to them.

## 4. Predicted footprint (exact, zero-LP)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Hours whose LI cap falls | 860 | 1,468 | 1,688 | 968 | 1,734 |
| Cap energy removed, TWh | 0.160 | 0.343 | 0.268 | 0.270 | 0.308 |
| Share of the gap | 13 % | 25 % | 21 % | 18 % | 23 % |
| Mean cut in those hours, MW | 186 | 233 | 159 | 279 | 178 |
| LI miss in those hours ($/MWh) | −8.49 | −7.19 | −14.01 | −8.74 | −6.68 |
| **Upper bound on system C3a move** ($/MWh; LI load share × LI miss contribution in cut hours) | — | **+0.15** | +0.37 | +0.12 | **+0.16** |

**Stated up front: this lever cannot close C3a.** The generous upper bound is +0.15 / +0.16 $/MWh
against −8.02 / −7.15 $/MWh system misses, which is about 2 %. The case for it is structure: a tie
posting 0 cannot deliver (rule 1). It is **not** the C3a lever.

## 5. G-DRIFT (keeper `67fd3d1b` → `origin/main` `df4bd585`)

Twelve solve-path files changed. **Every hunk is INERT for NYISO**, so form 4 is valid and the
keeper is the control. No control solve is owed.

| hunk source | classification |
|---|---|
| soco-72 `fuel_trajectories.py` | another ISO's table |
| neiso-119 winter fuel-security roster (`winter_fuel_inventory.py`, `scenarios.py`, `constants.py`, `solve_surface_declared.py`, `run_calibration.py`) | default-off `neiso_winter_fuelsec_conduct_roster`, NEISO-gated, absent from the keeper recipe (`neiso_winter_fuel_inventory: false`) |
| `nwpp_path76_alturas_link` (`iso_configs.py`, `ttc.py`, `runner.py`, `scenarios.py`, `run_calibration.py`) | default-off, NWPP-only |
| R-ERCOT-7 per-unit event cap (`outages.py`, `fleet/arrays.py`, `scenarios.py`) | default-off, ERCOT-only |
| SPP-86 coal extract basis (`outages.py`, `fleet/arrays.py`, `fleet/floors.py`, `scenarios.py`, `run_calibration.py`) | default-off, absent from the recipe |
| neiso-119 `forecast_parity_registry.py` | forecast-only accounting |

## 6. Gates (fixed before any solve; A/B = arm vs the keeper's committed bundle, form 4)

- **Solve shape.** Year-isolated shards per rule 36, covering every registered year: 2021–2025.
- **G-1, footprint (hard).** The arm's LI link cap equals §4 hour-for-hour, and no other link's
  limit column moves. Verify zero-LP on the arm's own inputs before reading any price.
- **G-2, sign (hard).** The LI load-weighted price rises, or stays flat, in every year. A fall in
  any year kills the arm: it means the clip does not act as a supply removal.
- **G-3, containment (hard).** No C1 class-year moves by more than 0.35 TWh, the largest single-year
  cut. No determination worsens on a criterion other than C3a/C3b. |Δ total energy| ≤ 0.05 TWh.
- **G-4, magnitude (reported, not a gate).** System C3a moves within [0, +0.4] $/MWh per year. A
  larger move is investigated as a defect, not celebrated.

## 7. Promotion rule (ex ante)

- **Promote iff G-1, G-2 and G-3 all pass.** The basis is rule 1 [R-STRUCT] (a tie posting 0
  cannot deliver) and rule 14. It is **not** a C3a improvement, which §4 bounds at about 2 %.
- A C3a or C3b move of either sign is reported at full magnitude and changes nothing.
- Any hard-gate failure means **R**, recorded in the matrix, with no successor by re-quantiling.
- Rule 31: the owner rules on promotion. The session recommends only.

## 8. What stays open

- 75–87 % of the LI gap is not removed by the clip. 51–72 % of the gap falls in hours with all three
  lines posted up, where it is economic under-scheduling of CSC and 1385. That part has no
  admissible measured input and is **not** chartered.
- The C3a 2022 / 2025 miss is unchanged by this lever, per NYISO-NEXT-4 §5: the 2022 Upstate_West
  pin (**R**) and the > $300 tail.

---

## 9. ADDENDUM — NYISO-NEXT-6, written before any solve (2026-09-27)

Implementation: `nyiso_li_seam_posted_limit_cap` (default off), `data/nyiso_seam_envelope.py::nyiso_li_posted_limit_cap`,
applied in `run_calibration.run_year` after the armed envelope. Nothing in §3–§7 is changed.

### 9.1 G-DRIFT, `df4bd585` → `origin/main` `18a2a3cb`

Every solve-path hunk is **INERT for NYISO**. Form 4 stays valid; the keeper stays the control.

| hunk source | classification |
|---|---|
| NWPP-NEXT-7 coal take floor (`scenarios.py`, `coal_fuel_inventory.py`, `lp/{__init__,model,rows}.py`, `pipeline/spec.py`, `run_calibration.py`) | default-off `coal_fuel_inventory_take_floor`, gated to `("NWPP",)` and requires `coal_fuel_inventory_plant_grain` — both absent from the keeper recipe; `coal_plant_floor` is `UNSET`/`None` off, leaving the 0 lower bound |
| `COAL_PLANT_GRAIN_ISOS` gains `"NWPP"` | another ISO |
| miso-277 hub nearest-year fallback (`fuel/basis/miso.py`) | MISO-only table |
| `_validation-source/pjm_offer_midcurve_*` | PJM artifact |
| `reference/camd-eia-crosswalk/` (new) | no consumer on any solve path (`git grep` over `src`, the two runners, `scripts/lib`: 0 hits) |

### 9.2 G-1 at zero LP (production functions, keeper config) — `scripts/probes/nyisonext6_g1_footprint.py`

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Hours whose LI cap falls | 860 | 1,468 | 1,688 | **969** | 1,734 |
| Cap energy removed, TWh | 0.160 | 0.343 | 0.268 | **0.269** | 0.308 |
| Mean cut in those hours, MW | 185.5 | 233.4 | 158.8 | 278.0 | 177.5 |
| Any hour raised | no | no | no | no | no |
| Max \|Δ\| on any other link, MW | 0 | 0 | 0 | 0 | 0 |

- **Exact match to §4 in 2021, 2022, 2023 and 2025.**
- **2024 differs by +1 hour / −0.001 TWh (§4: 968 / 0.270).** Cause: the NEXT-5 probe indexed posted
  limits by hours since 1 Jan **without dropping Feb 29**, while the envelope is on the model's fixed
  non-leap clock. After 28 Feb its limit and cap arrays were one day apart. The implementation uses the
  model clock (the outage-window convention). The 2024 reference value for G-1 is therefore the
  corrected **969 / 0.269**; this is a defect in the reference computation, not a change to the gate.
  The same misalignment touches §2's 2024 LI-price columns; they are not re-used here.
- The PAR-attributed envelope (the keeper arms it; it supersedes the nyiso-125 envelope) and
  `seam_envelope_by_zone` give **byte-identical** Long_Island caps in all five years, so §4's cap basis
  is the keeper's.
