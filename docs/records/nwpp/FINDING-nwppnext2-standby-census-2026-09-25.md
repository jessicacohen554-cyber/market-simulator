# FINDING — NWPP-NEXT-2: EIA-860 standby (`SB`) census, fleet vs benchmark population (zero LP)

Probe `scripts/probes/_nwppnext2_sb_census.py` (read-only; no solve). Follows
`FINDING-nwppnext2-ctpeaker-2026-09-25.md` §(A). Membership mirrors the run's two seams: **fleet** =
EIA-860 `balancing_authority_code ∈ fleet.models.ba_codes(iso)`, then `status == "OP"`
(`data/fleet/eia860.py:1261`; also :751 eGRID HR reconcile, :3319 mothball re-carry); **benchmark** =
`run_calibration_full._iso_plant_ids(iso, year)` → `_eia923_frame`. Vintage per year = `vintage_<Y>/`
(`eia860_vintage_tracks_solve_year`), 2025 = top-level 2025 ER. EIA-923 = raw plant net generation (C1's
`classFull` scales it ×0.886–0.911). "SB-only plant" = no generator OP in that vintage.

**Verdict.** (1) A **structural population mismatch**: `_iso_plant_ids` is plant-grain eGRID/860 geography
with **no status filter**, so 100 % of SB-only plants' EIA-923 generation is in the C1 benchmark in every ISO
(MISO 0.998), while the fleet carries none of their capacity. (2) In NWPP it is **two plants** — Fredonia
and Sun Peak, 598 MW gas CT, SB in all seven vintages, never partially OP — carrying 0.25–1.00 TWh/yr of
benchmarked CT generation. (3) **Systemic, not NWPP-specific**: PJM, SPP and MISO carry comparable
generating SB gas. (4) Recommended fix: admit `SB` as available capacity by status alone (zero DOF);
selecting on same-year EIA-923 generation is refused (rule 13).

## 1. NWPP SB units (all 7 vintages 2019–2025)

| Plant (ORIS, BA) | gens / PM | nameplate (summer) MW | partial OP? | Σ923 GWh 2019–25 |
|---|---|---|---|---|
| Fredonia (607, PSEI) | 4 × GT, NG, 1984/2001 | 376 (280) | no | 2,682 |
| Sun Peak (54854, NEVP) | 3 × GT, NG, 1991 | 222 (222) | no | 347 |
| 3 IPCO small hydro (50362/50895/50896) | HY | 25 | no | 307 |
| 6 oil IC / small (7080, 3853, 7039, 2196, 817, 56932) | IC, DFO | 27–39 | no | ≤11/yr |
| Univ. of Oregon CPS (54950) | CA/CT/IC | 18 | no | 2 |
| Biomass One, Star Peak, UW PP, Sinclair, Hurricane, Sheep Creek | ST/BT/IC/HY | 16–32 SB | **yes** | plant-grain, not separable |

Only the two gas CTs are material (≥10 GWh/yr) besides three ≤10 MW run-of-river hydro. Partially-OP SB MW
is 16–32 MW/yr (none of it gas CT), so **no material SB plant is already partly in the fleet**.

**Per plant-year, EIA-923 net / CAMPD gross (GWh)**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025* |
|---|---|---|---|---|---|---|---|
| Fredonia 923 / CAMPD | 196/33 | 195/32 | 386/194 | 273/62 | **967**/296 | 554/151 | 110/15 |
| Sun Peak 923 / CAMPD | 54/59 | 119/128 | 73/80 | 34/40 | 32/37 | 36/42 | **0**/35 |

CAMPD reports only Fredonia CT3/CT4 (2 × 58.9 MW); CT1/CT2 (2 × 129 MW) are absent from CAMPD, so the CAMPD
hourly CT shape used by the ctpeaker finding under-covers Fredonia. *2025 EIA-923 is partial (7,653 rows vs
17,087 in 2023): Sun Peak's 0 is a reporting gap (CAMPD 35 GWh), and the 2025 column is a floor.

## 2. NWPP totals: capacity with no LP representation vs benchmarked generation

| SB-only plants | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025* |
|---|---|---|---|---|---|---|---|
| MW, all classes | 682 | 693 | 710 | 712 | 690 | 666 | 740 |
| MW, CT_PEAKER (gas) | 601 | 601 | 601 | 601 | 598 | 598 | 598 |
| 923 TWh, all classes | 0.330 | 0.394 | 0.522 | 0.373 | **1.055** | 0.597 | 0.112 |
| 923 TWh, CT_PEAKER | 0.250 | 0.314 | 0.460 | 0.307 | **0.999** | 0.590 | 0.110 |
| 923 TWh, hydro/other | 0.079 | 0.079 | 0.059 | 0.055 | 0.055 | 0.005 | 0.000 |
| 923 TWh, oil | 0.001 | 0.001 | 0.003 | 0.011 | 0.001 | 0.001 | 0.002 |
| in C1 benchmark population | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % |

No SB coal, CC-gas or ST_GAS in NWPP. The CT row is the ctpeaker finding's (A) column before C1's ×0.89
reconciliation (−0.22 … −0.90 TWh there).

**OS / OA, for completeness.** OS-only plants: 144–185 MW, 0–0.16 TWh (all "other": biomass/hydro/landfill).
OA-only plants: 18–223 MW, 0.001–0.385 TWh, all hydro/biomass (American Falls 262 GWh 2023; Lookout Point
175 GWh 2024; Cosmo Fibers 100 GWh 2022). The large OA/OS MW (2.3–3.1 GW/yr) are **individual units at
otherwise-OP federal hydro plants** (John Day, Rocky Reach, Chief Joseph, Lower Granite, The Dalles,
Bonneville …) — a hydro-fleet question, not a thermal one; not pursued. No OS/OA gas CT/CC generates.
The existing `carry_operating_mothballs` re-carries an OA unit only if OP in `vintage_<Y>`; it cannot reach
a unit that is SB in every vintage.

## 3. Other footprints (SB-only plants, same seams)

| SB-only gas (CT/CC/ST_GAS) | MW 2019–25 | 923 TWh 2019 / 20 / 21 / 22 / 23 / 24 / 25* | material plants |
|---|---|---|---|
| **NWPP** | 605–623 | .25/.31/.46/.31/1.00/.59/.11 | Fredonia, Sun Peak |
| **PJM** | 864–917 | .47/.34/.37/.47/.37/.27/.00 | NAEA Lakewood 288 MW (1.72 TWh Σ), Elizabeth River 389, Hazelton 172 |
| **SPP** | 548–650 | .23/.21/.28/.35/.41/.52/.22 | H.D. Mattison 349 MW (0.94), El Dorado Refinery 39 MW (1.24) |
| **MISO** | 96–642 | .00/.00/.75/.31/.00/.02/.00 | Baxter Wilson 545 MW, SB 2021–22 only |
| CAISO | 74–91 | .00–.10 | Elk Hills Cogen 47 MW |
| ERCOT / NYISO / NEISO / SOCO | 0–44 | ≤0.001 | none |

Non-gas SB generation is small except PJM Commonwealth Chesapeake (403 MW oil GT, 14–56 GWh/yr). PJM 2022's
1.76 TWh all-class SB total is an artifact: Waukegan (883) retired its coal in 2022 and its surviving CT is SB, so
plant-grain 923 carries coal from units the retiree channel already models — a caveat on any plant-grain
reading. Partially-OP SB MW is material in MISO (718–962 MW/yr) and PJM (212–361); those SB units are also
missing from the fleet, and their plant's 923 cannot be split by status. **Conclusion: systemic.** Four ISOs
carry 0.2–1.0 TWh/yr of benchmarked gas generation on capacity the LP does not have.

## 4. Admissibility rule — recommendation

EIA-860 `SB` = "Standby/Backup — available for service but not normally used for this reporting period".

- **Recommended (Rule A): admit `SB` generators as ordinary available fleet capacity, by status alone.**
  Status is a published EIA-860 field, known ex ante from the year's own vintage (backcast) or the current
  snapshot (forecast), and it regenerates for any forward year. It responds to changed conditions, and the unit
  takes the standard offer construction (heat rate, fuel, VOM, outages), so the LP decides whether it runs.
  Zero free parameters (rules 13, 14, 21, 24). A high-mc standby unit simply does not clear; admitting one that
  never runs costs nothing in energy. The one-seam change is the OP filter at `eia860.py:1261`, with :751
  (eGRID HR reconcile) widened alongside it so admitted units get the same reconciliation. Implement it as an
  ISO-agnostic, default-off `ScenarioConfig` bool with a mechanism-matrix row (rule 28). Each ISO arms it
  through its own lane (rule 25). Rule 19: it adds units, it does not stack a floor.
- **Refused (Rule B): admit SB units whose same-year EIA-923 generation is > 0 (or ≥ X).** That selects capacity
  on the measured outcome being scored (rule 13), and the threshold is a free parameter (rule 21). A lagged
  prior-year version is also outcome selection, and Rule A makes it unnecessary.
- **Side effects to check before arming (not a gate on the residual):** SB MW would enter reserve co-opt
  headroom and, in forecast mode, accredited capacity (the reliability floor, entry and retirement screens).
  That is correct for real RA resources (Fredonia is PSE's peaking RA). The census still has to be run per ISO
  before the capacity screens move, and the PJM/MISO forecast lanes own that call. Unit-outage coverage for
  newly admitted units must be checked, since CAMPD misses Fredonia CT1/CT2.

**Expected NWPP effect of Rule A.** Capacity: +682–740 MW nameplate, of which +598 MW gas CT (Fredonia 376 +
Sun Peak 222; 502 MW summer) in every year 2019–2025. Energy: the upper bound is the benchmarked generation
the admission makes representable, 0.25 / 0.31 / 0.46 / 0.31 / 1.00 / 0.59 / 0.11 TWh CT (2019–25, raw 923).
The LP will pick up **less** than that, because the ctpeaker finding (B) shows NWPP CT dispatch is price-bound.
At the keeper's own model CT-class CF (6.0 / 15.8 / 5.1 / 5.9 / 8.6 / 12.7 / 20.6 %), 598 MW gives about
+0.31 / +0.83 / +0.27 / +0.31 / +0.45 / +0.67 / +1.08 TWh. That estimate assumes the admitted units run like
the class average. Fredonia CT1/2 (1984 units) likely sit above average mc, so this is an upper scoping number.
Direction by year: it closes part of the 2021–2024 CT shortfall (at most about 10–25 % of it) and **adds** to
the 2020 and 2025 CT over-runs. Per rule 1 that is not a reason to withhold it, because the units exist and
are benchmarked. Other hydro/oil SB units add ≤0.08 TWh/yr, and the run-of-river hydro would route via the
hydro fleet rather than as thermal.

**Caveats.** Partially-OP plants' 923 is not status-split; 2025 EIA-923 is partial; 10 GWh/yr is a
**reporting** threshold only; class labels are a coarse PM × fuel map (`_classify_f923` agrees on NWPP rows).
