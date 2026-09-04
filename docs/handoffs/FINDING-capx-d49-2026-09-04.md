# FINDING — capx D49: the two D46 Phase-0s. (1) ERCOT's carbon-free CCS conversions are a construction, not economics — §45Q is credited on the host's per-MWh CO2 while the capture island is charged at a flat H-class $/kW, so every host above ~0.46 t/MWh clears, and D41's "nothing clears in PJM/MISO" does not survive unit grain either. (2) MISO's exit-side margin is bimodal, never near the bar: floor-capped in 2022–23, cleared wholesale by a 0↔CONE capacity-price cliff in 2024–25 that a double-netted reserve position flips — the D43 wall accounts for nothing

**Lane:** capx D49 — a ZERO-SOLVE diagnostic over artifacts D46 committed. Branch
`claude/capx-d49-d46-phase0s-eaw7am`, fresh off `origin/main` `8a18e9e1`.
**Date:** 2026-09-04. **Pre-declaration:**
`docs/handoffs/PREDECL-capx-d49-2026-09-04.md`, pushed at `e2a7fbf2` BEFORE either
probe script existed; graded at full magnitude in §1.6 and §2.7, misses included.
**Nothing solved, armed, moved or repaired.** No `ScenarioConfig` field touched,
no keeper / shard verdict / marker moved, no CI job. Rules 13, 14, 21, 22, 25,
27, 28 hold. Data: `data/raw` arrived fully hydrated; `data/clean` was
regenerated for the fleet datatypes only (`fleet reference egrid
emissions-unit-annual fuel-prices outages …`) so the base fleets could be
rebuilt through `build_base_fleet` — stated because the dispatch asked.

**Committed with this finding:** `scripts/probes/_capxd49_ercot_ccs_reconstruction.py`
→ `results/calibration/capxd49_ccs_reconstruction.json`;
`scripts/probes/_capxd49_miso_exit_margin.py` →
`results/calibration/capxd49_miso_exit_margin.json`; evidence appends to the
ERCOT `ccs_retrofit_screen` cell and the MISO `economic_retirement_screen`,
`capacity_market_clearing`, `adequacy_internal_supply_accounting` cells (no
verdict letter moves; `check_mechanism_matrix.py` clean).

---

## 0. The two verdicts

**Half 1 — (c), a construction; seam named; STOP.** Reconstructing the screen's
own arithmetic (`ccs.py::apply_ccs_retrofit`) at the D41-corrected constants on
the rebuilt ERCOT fleet, all 14 converting rows (2,741.8 MW) clear at the
**hour ceiling** — Δ·avail·8760 − ΔFOM ≥ capex/12 — and a surface flat at the
ledger's own screen mean reproduces every conversion exactly. No ERCOT-specific
screen input exists: every field the screen reads is identical to PJM's and
MISO's except the two D41 constants. What clears the ERCOT hosts is their
**heat rate**: the regular-CC hosts run 8.2–11.3 MMBtu/MWh with measured CO2
rates 0.47–0.56 t/MWh that equal the physical `hr × 0.057` to within ±10 %, so
the §45Q offset (63 × er $/MWh) is $18–24/MWh against a bar that needs ~$16.6
at every hour. The seam: **the credit scales with the host's CO2 flow per MWh,
the capex does not** — `ccs_retrofit_capex_kw` is the ATB capture-island
increment for an H-class (≈6.4 MMBtu/MWh) host, charged flat per kW to hosts
emitting 40–90 % more CO2 per kW. Run identically on PJM's and MISO's own
converting units (decided at the stale constants), **99 % of PJM's 2028
converting MW and 100 % of MISO's clear at the ceiling on the corrected
constants too** — there the term is the CHP hosts' measured per-electric-MWh
rate (1.07–1.96 × physical), the same seam entered through a second door. D41
§4.3's zero-clearing result was a class-average artifact, and D46 §4.5's
"does not extend past PJM/MISO" is bounded the other way: it never held for
them at unit grain. Physical-plausibility line: satisfied by the seam, not a
band — the model clears 2.7 GW of merchant retrofits on 45Q alone because it
sizes the credit to the host and the island to a reference host.

**Half 2 — neither H-WALL nor "the D43 wall mirrored"; a named margin-side
object with its repair and source.** On the D46 MISO ledgers the undated
cohort's screen margins are **bimodal and never within reach of the bar**:
in the 2022/2023 screens 76.6 / 73.0 GW of the 98.1 GW undated fleet fails
(energy-only margins $0–20/kW-yr against bars of 21–58.5, capacity term $0 at
position 1.032 on the vertical PY2023 vintage) and **every failing MW is
`entry_capped`** by the admission floor; in 2024/2025 **no unit fails**
because the capacity term alone ($111–117/kW-yr at 0.976 on the vertical 2024
vintage; $448–473 at 0.949 on the RBDC plateau) exceeds every bar. The D43
dispersion band mirrored onto exits moves **0.00 GW in the exit direction**
(8.74 GW of coal sits within band, in the rescue direction). Of the 7.570 GW
miss, 4.79 GW is exempt or absent MW no margin-side object can reach; the
reachable 2.785 GW of undated real exits is 100 % floor-capped in 2022–23
and 100 % capacity-cleared in 2024–25; H-WALL 0 %. The margin-side object is
the **position, not the curve**: under the dates-ON posture the consumed
position sits 5.8 / 6.9 pts SHORT of the market's own where D31 dates-OFF was
within 0.2 / 3.8, because the 0.8546 accounting ratio was identified on a
fleet that still carried the exits the dates channel now removes — the same
MW netted twice. Its repair is zero-DOF and routed, not made (§2.6).

---

## 1. Half 1 — ERCOT CCS at carbon = 0

### 1.1 What was compared, like-for-like

| | ERCOT | PJM | MISO |
|---|---|---|---|
| bundle / key / sha | `ff-t1f-d46/ercot` `873d8c0e6cab52ae` @ `dd10e9fe` | `ff-t1f-s6-pjm/ledger` `31a19d815fa319a7` @ `54ca19a` | `ff-t1f-s123/verify` `587dc5b32ba71ceb` @ `54ca19a` |
| constants the run solved at | **corrected** 1521.4 / 65.0 | stale 900 / 25.0 | stale 900 / 25.0 |
| conversions in the ledger | 2028 11 rows / 2,130.9 MW; 2029 3 / 610.9 | 2028 26 / 2,998.5; 2029 9 / 2,998.8; 2030 10 / 2,998.0 (cap-bound) | 2028 14 / 2,998.9; 2029 30 / 2,998.7; 2030 17 / 2,994.0 (cap-bound) |
| every other screen input | identical across all three (carbon 0, attr 0, no CES, transport 15, VOM adder 8, HR penalty 0.12, capture 0.9, cap 3 GW/yr, life ≥ 15, 45Q window 12 / last year 2032) | | |
| gas (mid HH + basis) 2028 | $3.17 | $4.34 | $3.97 |
| the price object the screen consumed | the lookahead stack signal (`entry_lookahead_reprice`), zone-FLAT: 2028-screen mean **$41.37**, max 160.2; 2029-screen mean $64.06 | no rows in the ledger (no screen level recoverable) | 2028-screen mean $37.73; 2029/30 $41.60 |

The reconstruction is the screen's own arithmetic (PREDECL §1.2), replicating
D41 §4.3 to the hour on the class-average rows (PJM 2028: Δ 11.34 / 12.57 /
15.03 $/MWh, H\* 13,485 / 12,167 / 10,178 — identical), so every difference
below is a unit-grain fact, not a different model. Learned capex on the
run's own tracker: 2028 **1,323.6** $/kW (all three), 2029 1,218.2 (ERCOT,
its own 2.13 GW fed back) / 1,200.6 (PJM, MISO), 2030 1,178.3 / 1,131.9.

### 1.2 The 14 ERCOT converting rows, reconstructed

Δ = the per-hour uplift ceiling; ceil = Δ·avail·8760 − 35,000; bar = capex/12;
H\* = in-merit-equivalent hours needed (all $k/MW-yr). "phys-er" re-runs the
ceiling with er := hr × 0.057; "flat" is every hour at the ledger's screen mean.

| unit (2028 screen, gas $3.17, capex 1,323.6) | MW | hr | plant hr | er | er/phys | vint | Δ $/MWh | ceil | bar | H\* | ceiling | flat $41.37 | phys-er |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| CC_CHP_Houston_p55464_econ | 352.8 | 5.94 | 6.24 | 0.530 | 1.56 | 2003 | 23.14 | 157.6 | 110.3 | 6,609 | Y | Y | **N** |
| CC_CHP_Houston_p55464_peak | 117.6 | 8.61 | 6.24 | 0.530 | 1.08 | 2003 | 22.13 | 149.1 | 110.3 | 6,913 | Y | Y | Y |
| CC_CHP_Houston_p55470_econ | 213.8 | **34.75** | 36.49 | **2.061** | 1.04 | 2003 | 108.62 | 868.9 | 110.3 | 1,408 | Y | Y | Y |
| CC_REGULAR_Houston_p56806_committed | 294.5 | 11.13 | 11.13 | 0.553 | 0.87 | 2009 | 22.61 | 153.1 | 110.3 | 6,766 | Y | Y | Y |
| CC_REGULAR_Houston_p56806_econ | 187.4 | 9.94 | 11.13 | 0.553 | 0.98 | 2009 | 23.06 | 156.9 | 110.3 | 6,633 | Y | Y | Y |
| CC_REGULAR_South_p3631_committed | 106.0 | 10.95 | 10.95 | 0.561 | 0.90 | 2003 | 23.17 | 157.8 | 110.3 | 6,601 | Y | Y | Y |
| CC_REGULAR_South_p3631_econ | 67.5 | 9.78 | 10.95 | 0.561 | 1.01 | 2003 | 23.62 | 161.5 | 110.3 | 6,477 | Y | Y | Y |
| CC_REGULAR_South_Central_p4937_committed | 316.0 | 11.33 | 11.33 | 0.561 | 0.87 | 2014 | 23.05 | 156.8 | 110.3 | 6,636 | Y | Y | Y |
| CC_REGULAR_South_Central_p4937_econ | 201.1 | 10.12 | 11.33 | 0.561 | 0.97 | 2014 | 23.51 | 160.7 | 110.3 | 6,505 | Y | Y | Y |
| CC_REGULAR_West_p56233_econ | 53.9 | 8.21 | 9.20 | 0.468 | 1.00 | 2005 | 18.36 | 117.8 | 110.3 | 8,331 | Y | Y | Y |
| CC_REGULAR_West_p56349_econ | 220.2 | 8.53 | 9.38 | 0.470 | 0.97 | 2007 | 18.38 | 118.0 | 110.3 | 8,320 | Y | Y | Y |
| **2029 screen** (gas $3.34, capex 1,218.2, flat $64.06) | | | | | | | | | | | | | |
| CC_REGULAR_South_Central_p7900_econ | 278.6 | 7.37 | 8.11 | 0.439 | 1.05 | 2004 | 16.72 | 104.1 | 101.5 | 8,595 | Y | Y | **N** |
| CC_REGULAR_West_p56233_committed | 84.6 | 9.20 | 9.20 | 0.468 | 0.89 | 2005 | 17.80 | 113.1 | 101.5 | 8,075 | Y | Y | Y |
| CC_REGULAR_West_p56349_committed | 247.7 | 9.38 | 9.38 | 0.470 | 0.88 | 2007 | 17.87 | 113.7 | 101.5 | 8,043 | Y | Y | Y |

Three readings, each checkable in the table:

1. **Every row clears at the ceiling and every row clears flat-at-level** —
   the arithmetic in PREDECL §1.2 IS the screen's (the falsifier did not fire),
   and the screen's zone-flat stack signal at $41.37 sits ABOVE the unabated
   bid of every host (b_unab = hr × 3.17 + VOM ≈ $28–38), so each hour pays the
   full Δ. The ledger's own price object is what supplies the hours.
2. **The rate is physical; the heat rate is what is high.** Eleven of fourteen
   rows carry er/phys within 0.87–1.08; replacing er by hr × 0.057 drops only
   two rows below the ceiling (P4 MISS). The regular-CC hosts are 2003–2014
   vintage plants whose CAMPD per-plant heat rate is 8.1–11.3 MMBtu/MWh —
   CT-class efficiency — and at $85/t on 0.9 × er the §45Q offset is
   $18–24/MWh where the corrected bar needs ≥ $16.6 at every hour
   (PREDECL §1.2). The one plain data artifact is `CC_CHP_Houston_p55470`:
   heat rate **34.75**, CO2 rate **2.061 t/MWh** — a CHP plant whose CEMS
   fuel is charged to its net electric MWh — which clears with Δ = $108/MWh
   and a 1,408-hour break-even.
3. **The stand-in surfaces bracket the ledger.** On the ERCOT T1-H dump's
   stack signal re-levelled to $41.37 (median $25.9, only 410 h ≥ $37), 3 of
   11 rows clear; on the flat surface 11 of 11; the ledger converted 11 of 11.
   The screen's 2027 signal therefore has a body that sits mostly above ~$37
   (the reserve margin falls 8.9 % → 3.0 % across 2027–28), i.e. it is closer
   to flat than the 2024-hindcast stand-in. The realized-duals stand-in is
   uninformative after an additive re-level (its $88 mean is 265 tail hours
   over a $21 median) and is reported only as such.

**Fleet census at the ceiling (corrected constants, 2028):** ERCOT 3.79 GW of
37.2 GW gas_cc could clear (min clearing hr 5.94 — the CHP row; every
regular-CC host clearing has hr ≥ 8.2); the model converted 2.13 GW; on the
skewed stand-in 0.92 GW.

### 1.3 The identical construction on PJM's and MISO's own converting units

| ISO · screen | rows (MW) | clear at ceiling on CORRECTED constants | phys-er at ceiling | hr p10/50/90 | er p10/50/90 | er/phys p50 | CHP rows | fleet gas_cc clearing at ceiling |
|---|---|---|---|---|---|---|---|---|
| PJM 2028 | 26 (2,999) | **19 rows / 2,960 MW (99 %)** | 5 / 318 MW | 6.36 / 7.12 / 10.62 | 0.364 / 0.606 / 0.707 | **1.32** | 20 (943 MW) | 5.74 of 58.8 GW |
| PJM 2029 | 9 (2,999) | 5 / 995 MW | 3 / 343 | 7.25 / 7.57 / 10.41 | 0.415 / 0.463 / 0.548 | 1.01 | 1 | 6.23 GW |
| PJM 2030 | 9 (2,098) | 0 | 1 / 85 | 6.30 / 6.71 / 7.48 | 0.359 / 0.364 / 0.409 | 0.96 | 5 | 6.57 GW |
| MISO 2028 | 14 (2,999) | **14 / 2,999 MW (100 %)** | 4 / 62 MW | 6.56 / 7.30 / 9.03 | 0.518 / 0.616 / 0.799 | **1.48** | **14 (2,999 MW)** | 5.00 of 34.4 GW |
| MISO 2029 | 29 (2,991) | 22 / 1,839 MW | 15 / 986 | 6.18 / 7.84 / 10.22 | 0.415 / 0.512 / 0.583 | 1.07 | 25 (2,270 MW) | 6.12 GW |
| MISO 2030 | 17 (2,994) | 0 | 3 / 221 | 5.60 / 7.04 / 7.92 | 0.311 / 0.388 / 0.430 | 0.97 | 6 | 6.12 GW |

Same seam, second door. PJM's and MISO's 2028 conversions are CHP-dominated
(PJM 20 of 26 rows, MISO 14 of 14), and there the measured per-electric-MWh
CO2 rate runs 1.3–1.5 × the tranche's `hr × 0.057` — the steam-side fuel
charged to electric output. Substituting the physical rate empties the 2028
set (19 → 5 rows at PJM, 14 → 4 at MISO), which is exactly the P4 test that
FAILED at ERCOT: **at ERCOT the credit is high because the host heat rate is
high; at PJM/MISO because the CHP rate is inflated.** Both are the one
construction — credit ∝ CO2 per MWh, capex flat per kW. The 2030 rows at
both ISOs (er 0.31–0.43, efficient hosts) clear at the stale constants only
and would not at the corrected ones, which is the part of D41 §4.3 that does
survive: **the corrected constants remove the EFFICIENT hosts, not the
retrofits.** At the 3 GW/yr cap, 5.0–5.7 GW of ceiling-eligible gas_cc per
ISO means Stage 3's PJM/MISO re-solve should expect the cap to bind in 2028
on the corrected constants, not the conversion count to go to zero.

### 1.4 What the term is, and what it is not

- **Not (b).** The config diff is exhaustive over the screen's reads: only
  `ccs_retrofit_capex_kw`, `fixed_om_gas_cc_ccs` (the D41 pair) and the two
  ERCOT price-signal flags (`scarcity_price_overlay`,
  `capacity_screen_scarcity_restoration`) differ. Δ is a per-hour ceiling, so a
  tail cannot raise the uplift; the ERCOT signal's role is its compressed
  BODY (mean above every host's unabated bid), which the flat surface shows
  and the stand-in confirms by failing to reproduce the ledger.
- **Not (a) in the sense the dispatch meant.** "Higher energy margins" do not
  enter: the uplift is Δ per in-merit hour, and the unabated energy margin
  cancels out of the incremental comparison. What differs by host is Δ, and
  Δ is 63 × er − 0.12 × hr × gas − 8 — a function of the host's CO2 rate.
- **(c), the seam:** `apply_ccs_retrofit` prices the island at
  `ccs_retrofit_capex_kw × 1000` per MW for every host. The ATB increment D41
  identified (3,104.7 − 1,583.3 $/kW) is for ATB's own gas_cc host (NREL ATB
  2024 NG-CC, hr ≈ 6.4 MMBtu/MWh, ≈ 0.36 t/MWh). A capture island is sized to
  CO2 flow; a 0.55 t/MWh host needs ~1.5 × the island per kW, a 2.06 t/MWh CHP
  row ~5.7 ×. The screen scales the credit with er and holds the capex fixed,
  so the retrofit margin is monotone INCREASING in host emissions — the
  inverse of the "efficient hosts win" the docstring intends and of the
  market, where no merchant NGCC retrofit has cleared on §45Q alone. Second
  limb of the same seam: CHP hosts' CAMPD rates per NET ELECTRIC MWh count
  the steam host's fuel (ERCOT p55470 at 2.06 t/MWh; PJM/MISO CHP at
  1.3–1.5 × physical), so the credit is paid on tonnes the electric island
  would not exist to capture.
- **The price object (D43's wall, in the retrofit screen).** The uplift is an
  hours construction, and the zone-flat lookahead stack signal has no low
  body — at ERCOT it sits above every host's unabated bid in nearly every
  hour, so a host that in the LP's own duals would be out of merit a third
  of the year is credited the full Δ at 8,760 hours. This is the same
  discarded-dispersion object D43 measured on the entry screens, entering
  the retrofit screen with the opposite sign (there it under-expects; here
  it over-counts hours).

### 1.5 Routing (STOP — a defect is the director's to lane)

Three seams, one repair lane, all identified from committed sources and
none from a residual:

1. **Capex scaled to CO2 flow.** `retrofit_capex_per_mw = capex_kw × 1000 ×
   (captured_t_per_mwh / captured_ref)`, with `captured_ref` = 0.9 × the ATB
   gas_cc host's rate (`NEW_ENTRY_COSTS["gas_cc"]` heat rate × 0.057) — the
   basis D41's increment already carries. Zero DOF; source: the ATB extract.
2. **CHP hosts.** Either exclude `CC_CHP` from the retrofit candidate set
   (the island cannot capture the steam host's flue gas at the electric
   plant's cost basis) or rate them on electric-only fuel; the p55470 row
   (hr 34.75) is a data-quality flag for the ERCOT curated sheet regardless.
3. **The price object.** Reading the retrofit screen on the prior year's
   duals (the `econ_prices` fallback the D43 dumps commit) instead of the
   stack signal is the same one-line posture D43 §9 named; this lane makes
   no recommendation on arming, only records that the flat-vs-skewed
   bracket in §1.2 is where 2.13 GW of ERCOT conversions live.

### 1.6 Pre-declaration §1.5, graded

| # | prediction | outcome |
|---|---|---|
| P1 | no screen input differs but the D41 pair (+ the two scarcity flags) | **HIT** — verified over every field the screen reads |
| P2 | ≥ 10 of 14 rows er ≥ 0.46; MW-weighted er ≥ 0.50 | **HIT** — 13 of 14; MW-weighted 0.639 (2028 0.691, 2029 0.456) |
| P3 | every one of the 14 clears at the ceiling | **HIT** — 14/14, and 14/14 flat-at-level |
| P4 | phys-er substitution drops ≥ 8 of 14 → verdict (c) via inflated rate | **MISS** — drops 2 of 14; the ERCOT rates ARE physical. Verdict is still (c), on the seam the rate led to (credit ∝ er, capex flat), not on an inflated rate. PJM/MISO are the inflated-rate case (19 → 5, 14 → 4) |
| P5 | ≥ 20 % of PJM's and MISO's converting MW would clear at the ceiling on corrected constants | **HIT, by a wide margin** — PJM 2028 99 %, MISO 2028 100 %; D41 §4.3 does not survive unit grain |
| P6 | the `_peak` tranche's clearing is (c′) (marked-up bid) | **MISS** — with the plant's base hr as the bid it still clears at the ceiling; (c′) is not what clears it (immaterial, 117.6 MW) |
| P7 | plausibility line satisfied by the seam if (c) | **HIT** — §1.4 |
| falsifier | a converting row that cannot clear at the ceiling | did not fire |

**Tally: 5 hits, 2 misses.** The two misses are the same lesson: I expected
the CO2 rate to be the inflated term at ERCOT; it is the physical term, and
what is high is the host itself. That sharpened the seam rather than
weakening the verdict.

---

## 2. Half 2 — the MISO exit-side margin

### 2.1 The instrument

`results/hindcast/miso-2021-2025-realized-t1h-d46` (`eff2c890746ec966`, dates
ON, keeper miso-202) and `…-d42-control` (dates OFF) — every unit that fails
the bar in a screen year carries the FFR-5A decomposition on its
`pipeline_events` row (net revenue, going-forward cost, energy leg, capacity
leg, screen price mean, `mc_mean`, availability); units that pass carry no
row. The D46 `screen_signal_diag_{2023,2024}` dumps carry the stack signal the
screen consumed and the LP's own duals. The capacity term is evaluated
through the model's own seam (`capacity_price_per_firm_mw_yr` ×
`thermal_accreditation_fraction`) at the position the ledger says the
screens consumed (`capacity_reserve_position`, the D45 observability field).
2024/2025 margins for units with no D46 row are reconstructed from the same
unit's D42-control 2024 row (same price object, energy leg) plus the D46
capacity term — a stated approximation that has to reproduce "no unit
fails", and does.

### 2.2 The capacity term the screens consumed, and the market's

| screen year | position consumed | vintage | capacity term $/kW-yr (coal … gas_cc, UCAP-accredited) | MISO PRA cleared, annualized | at the market's own position |
|---|---:|---|---|---:|---|
| 2022 (bridge) | none | — | 0 | — | — |
| 2023 | **1.0322** | PY2023 vertical step | **0** | 3.65 | 0 |
| 2024 | **0.9764** | PY2024 vertical step (gross-CONE anchor 123.5) | **113.6 – 117.3** | 7.33 | **0** (at 1.034) |
| 2025 | **0.9488** | PY2025-26 RBDC, cap plateau (79.8 net-CONE anchor) | **458.4 – 473.3** | 79.07 | 90.8 (at 1.0174); 13.8 at D31's dates-OFF 1.0571 |

The 2021–2024 vintages are the published vertical PRA: CONE at or short of
the requirement, zero just long of it. At 1.032 the whole fleet earns $0; at
0.976 the whole fleet earns the gross-CONE anchor. **A 5.6-point move in the
position is a $0 ↔ $117/kW-yr cliff for every unit at once** — and 5.6 points
is exactly the dates-OFF → dates-ON move (D31's 1.0321 → D46's 0.9764).

### 2.3 The cohort census, every screen year

Undated = every ledger-known thermal unit not at one of the 48 live
`announced_fossil_schedule` plants (112 rows; cancelled/reversed excluded).

| screen year | undated units / GW | failing units / GW | of which `entry_capped` | gap p10 / p50 / p90 $/kW-yr (coal · gas_cc · gas_ct · gas_st) | |band| p90 / max | within band, EXIT direction | within band, RESCUE direction | capacity term alone ≥ bar |
|---|---|---|---|---|---|---|---|---|
| 2022 | 1,601 / 98.1 | 1,487 / **76.6** | **76.6 GW (100 %)** | −38.5/−15.8/−4.0 · −30.0/−21.5/−16.1 · −21/−21/−20.5 · −35/−35/−35 | 2.3 / 17.8 | **0.00 GW** | 8.74 GW | 0 |
| 2023 | 1,601 / 98.1 | 930 / **73.0** | **73.0 GW (100 %)** | same rows (the 2023 screen consumed the same 2021-based signal as the bridge) | 2.3 / 17.8 | **0.00 GW** | 8.74 GW | 0 |
| 2024 | 1,601 / 98.1 | **0** | — | reconstructed net = energy + 111–117 → every unit above its bar | — | 0 | 0 | **98.1 GW** |
| 2025 | 1,601 / 98.1 | **0** | — | +404/+417/+432 · +444/+461/+473 · +448 · +429 | 20.2 / 21.9 | 0 | 0 | **98.1 GW** |

Band = energy leg on the LP's own duals minus on the stack signal it screened
(the 2023 dump bounds the 2022/23 screens, whose 2021-based signal is not
committed; stated). The band is small — the MISO forecast LP's duals carry a
$46 max and zero hours ≥ $100 in 2023, four VOLL hours in 2024 — and for coal
it is POSITIVE (+7.6 to +15.7 $/kW-yr): pricing the energy leg on the duals
would lift the failing coal further toward passing, never toward exit. Gas
bands are ±1.

### 2.4 The undated real-exit cohort, plant by plant

Published record: 16.361 GW thermal exits 2021–2025 (+0.812 nuclear + 0.196
biomass = the 17.369 GW target); **12.897 GW at dated plants** (the channel's
reach); **3.465 GW undated**, of which 3.037 GW is in the ledger-known fleet
and 2.785 GW is reachable at plant+fuel grain. The rows the screen actually
saw (fail/capped MW; gap and band MW-weighted $/kW-yr; cap = the capacity term):

| plant | fuel | actual exit MW (yr) | model MW | 2022 · 2023 screen | 2024 screen | 2025 screen |
|---|---|---:|---:|---|---|---|
| 6055 Big Cajun 2 | coal | 657.9 (2025) | 1,110.0 | 799/799 capped, gap −6.6, band +7.6, cap 0 | cleared, cap 114 | cleared, gap +412.6, cap 458 |
| 4041 South Oak Creek | coal | 598.4 (2024) | 1,112.0 | 1,112/1,112 capped, −11.6, +13.7, 0 | cleared, 114 | +416.4, 458 |
| 52006 LaO Energy Systems | gas_cc | 464.5 (2023) | 384.0 | 384/384 capped, −19.3, +0.3, 0 | cleared, 117 | +467.3, 473 |
| 1400 Teche | gas_st | 348.5 (2024) | 331.4 | 331/331 capped, −35.0, −0.6, 0 | cleared, 115 | +429.3, 463 |
| 862 Grand Tower | gas_cc | 336.8 (2021) | 264.0 | 264/264 capped, −20.2, +1.1, 0 | cleared, 117 | +465.4, 473 |
| 10075 Taconite Harbor | coal | 168.0 (2023) | — (absent) | — | — | — |
| 6705 Warrick | coal | 166.6 (2025) | 721.5 | 343/343 capped, −15.8, +12.3, 0 | cleared, 114 | +412.5, 458 |
| 4078 (gas_st + gas_ct) | gas_st / gas_ct | 81.6 + 76.3 | 75.4 + 62.6 | all capped, −35.0 / −21.0, −0.6 | cleared | +429 / +448 |
| 1439, 54748, 2067, 1734, 10234, 1167, 1073, 50969, 54201 … | mixed | 5–79 each | present | all failing, all capped (gas −21/−35; coal −8 to −22, band +10 to +16) | cleared | +420 to +465 |
| 24 oil / small gas plants (1–24 MW) | oil / gas | 0.43 GW total | — (absent from the fleet) | — | — | — |

Every reachable megawatt tells the same story: **below the bar by 7–35 $/kW-yr
with the floor holding it in 2022–23, then 400+ $/kW-yr above the bar in 2025
on the capacity term alone.** No unit is ever within a band of the bar in the
exit direction.

### 2.5 The decomposition against the −43.6 % miss (7.570 GW)

| component | GW | share of the miss |
|---|---:|---:|
| exits at dated plants the record shows but the channel deferred / Dec-rolled / verified away (D42 §0 (ii)–(iii)), plus the 0.43 GW of undated small oil/gas absent from the fleet and Taconite Harbor | **4.785** | 63.2 % — exempt or absent; no margin-side object reaches it |
| undated real exits reachable by the screen | **2.785** | 36.8 % |
| — of which H-FLOOR (failed the bar AND `entry_capped`, 2022/23) | 2.779 | 36.7 % |
| — of which H-BAR (cleared 2024/25 with the capacity term alone ≥ bar) | 2.785 | 36.8 % |
| — of which H-WALL (within the dispersion band, exit direction, any year) | **0.000** | **0.0 %** |

H-FLOOR and H-BAR are the SAME megawatts read in different years, so they do
not add: the reachable cohort is floor-capped in the years it fails and
capacity-cleared in the years it does not. The D43 wall, mirrored onto exits,
accounts for nothing; the coal within band (8.74 GW fleet-wide, 1.30 GW of the
cohort) would be RESCUED by dispersion, not released.

### 2.6 The named margin-side object, its repair and its source

**Object.** The reserve position the three capacity screens consume under the
dates-ON posture. D31 identified `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]
= 0.8546` as PRA offered ÷ the model's census-fleet internal supply on the
2023/2024 overlap years (122,375.6 + 123,395.6) / (143,822.1 + 143,749.5). That
census fleet still carried the 2021–2023 real exits (St Clair, Schahfer,
Meramec, Edwards, Trenton Channel, Dolet Hills, River Rouge, Gallagher …) the
PRA had already dropped, so the ratio absorbed them. Since Q30/D44 the
fossil-dates channel removes those same plants explicitly — 5,960.6 MW
`announced` + 3,838.3 MW `announced_derate` in the D46 window — and the ratio
still applies. Netted twice, the position falls from D31's 1.0321 / 1.0571 to
0.9764 / 0.9488 — 5.8 / 6.9 pts short of the market's own 1.034 / 1.0174 —
and on the vertical 2024 vintage that is the whole cliff.

**Repair (zero DOF, identified from the accounting record, routed as a
candidate lane — NOT made here).** Re-identify the ratio on the model fleet
in the SAME posture the run applies: PRA offered ÷ model accredited internal
supply NET of the dated exits, on the same two overlap years, from the same
`data/raw/miso-pra/` record. The arithmetic is D31 §2's with one term moved;
nothing is sized by the exit residual. Back-of-envelope only, to size the
direction: removing ~4.6 / 7.7 GW of accredited dated capacity from the two
denominators puts the ratio near 0.88 / 0.91 and the 2024 position back
near 1.03.

**Rule-14 sign line, stated as pre-declared.** A faithful position moves the
2024 capacity term back to **$0** and the 2025 term to ≈ $91–110/kW-yr (the
market paid $79), so the reachable cohort returns BELOW the bar in 2024 and
exits get harder, not easier, in 2025. **The repair does not close the
under-build**: it returns the cohort to the floor-capped regime, where D32's
objects (the admission floor's class-constant retention key, the ~100 GW
failing pool) decide the composition. That is D32 R2/R3's lane, not a new one.

### 2.7 Pre-declaration §2.4, graded

| # | prediction | outcome |
|---|---|---|
| Q1 | H-WALL < 5 % of the miss; |band| < $8/kW-yr for ≥ 90 % of cohort MW | **HIT** — 0.0 %; |band| p90 $2.3 (max $17.8, coal, rescue direction) |
| Q2 | H-FLOOR: ≥ 70 % of undated actually-exited MW fails and is capped in both 2022 and 2023 | **HIT** — 2.779 of 2.785 GW (99.8 %) |
| Q3 | H-BAR: capacity term alone ≥ every bar for ≥ 95 % of cohort MW in 2024/25 | **HIT** — 98.1 of 98.1 GW, both years; reconstruction reproduces "no unit fails" |
| Q4 | consumed positions 5–9 pts short of the market's; D31 dates-OFF within < 1 pt | **HIT on the object** (5.8 / 6.9 pts short); the D31 clause was overstated — 0.2 pt in 2024 but 3.8 pts in 2025 |
| Q5 | undated actual exits 3.5–4.5 GW; H-FLOOR ≥ 70 %, H-WALL ≈ 0 | **HIT at the low edge** — 3.465 GW undated (2.785 reachable); 99.8 % / 0 % |
| Q6 | faithful position → 2024 term $0, cohort below the bar; 2025 RBDC ≈ $110 vs market $79 | **HIT in direction, off in level** — $0 in 2024; $90.8 at the market's 1.0174, $13.8 at D31's 1.0571 |
| falsifiers | any year ≥ 30 % in band; any undated unit failing 2024/25; positions within 2 pts of market | none fired |

**Tally: 6 hits (two with a stated overstatement), 0 misses.** The H-FLOOR
hypothesis was named in the pre-declaration because the disclosed census
already showed it (PREDECL §0); it is graded as a prediction only in the
sense that its magnitude (99.8 %) was not known.

---

## 3. What the two halves share

Both screens fail the same way: **a term that should scale with the unit is
held at a class constant, and a price object without a body supplies the
hours.** In the retrofit screen the class constant is the capex per kW and
the body-less object is the stack signal; in the retirement screen the class
constant is the per-fuel FOM bar against an energy leg priced on the same
stack signal, with a capacity term that is a class-wide cliff. Neither miss is
a dispersion miss. D43's construction, mirrored, would over-count at the
retrofit screen and rescue at the retirement screen; it is not the object in
either place.

---

## 4. Matrix (rule 28)

No mechanism tested, no verdict letter moves. Evidence appended to the ERCOT
`ccs_retrofit_screen` cell (which carried none) and the MISO
`economic_retirement_screen`, `capacity_market_clearing`,
`adequacy_internal_supply_accounting` cells; `check_mechanism_matrix.py`
integrity / anchors / keeper stamps / §5.x headers all OK. PJM's shard is not
touched (rule 25) even though §1.3 reads PJM's ledger: the PJM reading is a
like-for-like control for the ERCOT question, not a PJM verdict, and it is
for the Stage-3 PJM lane to stamp on its own re-solve.

## 5. Routed to the director

1. **Half 1 seam → a candidate repair lane** (§1.5): capex ∝ captured CO2
   per kW against the ATB reference host; CHP host exclusion or electric-only
   rating; the p55470 curated-sheet row (hr 34.75) as a data flag. Any of the
   three changes forecast-year ≥ 2028 behaviour only and re-keys every
   forecast config (the D41 §6.2 precedent) — blast radius to be measured
   before it lands.
2. **Stage 3 expectation correction.** D41 §7 item 1 priced the PJM/MISO t1f
   re-solve as "conversions go to zero". At unit grain 5.0–5.7 GW of gas_cc
   per ISO clears the corrected bar at the ceiling in 2028, cap-bound; the
   re-solve should expect the cap to bind in 2028 and the EFFICIENT 2030 hosts
   to drop out. If the half-1 repair lands first, that expectation changes
   again — sequence matters.
3. **Half 2 object → the MISO adequacy-accounting re-identification** (§2.6),
   a rule-23 data-change re-derivation (the dates posture changed the fleet
   the ratio was identified on). Its expected effect is to return the cohort
   to the floor regime; the under-build itself stays with D32 R2/R3.
4. **The vertical-vintage cliff is a modelling hazard on its own.** A
   ±3-point position error flips $0 ↔ $123/kW-yr for 98 GW at once on the
   2021–2024 MISO vintages. D31 §4 adjudicated the vertical-era floor out;
   this lane records that the step's x = 1.0 location, not its height, is
   what the screen is sensitive to.
5. **Oil is not being screened after 2022.** 549 oil rows fail in the 2022
   bridge screen; 0 (D46) / 10 (control) appear in 2023 while 3.51 GW of oil
   stays in `fleet_by_fuel_before`. Not this lane's question (0.543 GW of
   real oil exits, all small); recorded so the next MISO lane does not read
   "oil passes" as a margin fact.

## 6. Governance attestation

Zero solves. No holdout year touched (every artifact read is 2021–2025 T1-H
or 2026–2030 t1f, all in-window). No keeper, marker, freeze file, backcast
registry or forecast sidecar written. No `ScenarioConfig` field added or
moved; no default flipped. Rule 27: every ≥300-line file pushed is
blob-verified after push. Rule 25: only the ERCOT and MISO shards edited.
Rule 21/13/14: no parameter identified from a residual; the half-2 repair is
named with its published source and its sign stated against the residual.
Collision: read-only over committed artifacts; D45-R / D48 own the live
forecast surfaces and nothing here touches them.

## 7. Reproduction

```
uv run python scripts/regenerate_clean.py fleet reference egrid emissions-unit-annual fuel-prices outages confirmed-retirements
uv run python scripts/probes/_capxd49_ercot_ccs_reconstruction.py --out results/calibration/capxd49_ccs_reconstruction.json
uv run python scripts/probes/_capxd49_miso_exit_margin.py --out results/calibration/capxd49_miso_exit_margin.json
uv run python scripts/check_mechanism_matrix.py
```
