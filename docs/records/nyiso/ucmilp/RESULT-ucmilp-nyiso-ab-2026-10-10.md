# RESULT — UC-2-NYISO: MILP unit-commitment A/B on every NYISO backcast year (a CALIBRATED control) — **R: the control does not stay calibrated**

**Lane:** UC-2-NYISO · **Session:** `session_01HoVUBRJhqpY4TQdLq6NkPR` (Fable) · **Date:** 2026-10-10 · **Branch:** `claude/ucmilp-2-nyiso-ab-y5h8`
(rebased onto the pin). **PRECOMMIT:** `PRECOMMIT-ucmilp-nyiso-ab-2026-10-10.md` (pushed `1268e70d` before any shard; Addenda A–E before each
relaunch and the span). **Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`); owner: *"launch shards for other ISOs to test"*.
**Pin solved:** `f2bf73bfffa0946176432df2e11349bf8fcc2bfa` (main at the merge of PR #7224; engine uc-1.1 + UC-1-FIX + lean preset +
slim window + the two NYISO-found window fixes). **LP in this session:** zero (five year-isolated shards, rule 36; one bench gate shard).
**Registered:** nothing (desk ruling on the SPP probe: E13 admits keepers and folded runs only). Slim span under
`docs/records/nyiso/ucmilp/data/ucmilp_nyiso_span/`; full leg bundles on their shard branches. Rubric 3.20 for both arms.

## 0. Headline

**Replacing the P0-detected NYISO gas commitment bridge by the integer commitment stage does not leave the CALIBRATED control
calibrated.** The UC decommits 3.8–6.0 TWh/yr of CC_REGULAR and 0.9–2.1 TWh/yr of ST_GAS in every year and imports fill the gap
(+5.3 to +6.4 TWh/yr): C1 CC_REGULAR flips PASS → FAIL in 2021 (+1.31 → **−4.71 TWh**) and 2023 (+0.61 → **−4.03 TWh**), C1 ST_GAS
2021 (−3.44 → **−4.31 TWh**) and C1 CC_CHP 2023 (+2.81 → **+3.32 TWh**, share +3.4 pp) flip with it, and the price body moves the
"wrong" way for a control: UP in 2021 / 2023 / 2024 (+$1.0 / +1.5 / +1.1 per MWh; 2024 C3a −0.8 → **+1.9 %**, 2.7 pp against the
1 pp bar) and DOWN in 2022 / 2025 (−$0.6 / −1.8), where **2025 C3a crosses the band (−7.7 → −10.2 %, PASS → FAIL)**. Unlike SPP, the
lower-tercile error does not fall (it rises in four of five years) and the model still prints zero hours ≤ $15. Cycling collapses as
in SPP (CC starts 0.55–0.79× CEMS, ST_GAS 0.35–0.57×). Every window solved (1,825/1,825 Optimal, 0 time-limit hits), uplift
1.4–1.8 % of energy cost (under the 2 % bar), and the kept `reliability_floor` did NOT stack (its ST_GAS share is unchanged; the
MECH 28 share adds 6–11 pp on top and C8 stays under the cap even as the scorer prints it). **Kill #3 (control flips on real moves)
fired; T2 and T3 are breached → verdict `R`** (PRECOMMIT §7). Wall ratios 4.0–22.9× the year's own P0 + P1 (D-2 ceiling 3×; reported).

### 0.1 GATESPEC §6.3 gate table — control (keeper `2026-10-02-w0-nyiso`) → arm, every registered year

Control and arm scored on the SAME bench parts (registration rewrote none: the control re-scored at the pin is byte-identical to its
registered record — the STALE BENCHMARK alarm of PRECOMMIT §1 moved nothing). C3c CAVEAT → FAIL is the probe's missing attestation
(C6 UNATTESTED; PRECOMMIT T1), not a model move, except where noted. 2021 carries the §9 drift caveat; its deltas are classified in §1.

| year | C1 (class rows, Δ TWh vs actual) | C2 | C3a | C3b | C3c | C4 | C8 (as printed; MECH 28 inside) | D-2 MECH 28 share CC / ST_GAS | wall ratio | reading met? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | **CC_REGULAR +1.31 → −4.71 PASS → FAIL; ST_GAS −3.44 → −4.31 PASS → FAIL**; CC_CHP +1.52 → +1.94; CT_PEAKER +1.16 → +1.69 | PASS → PASS | +4.3 → +6.6 % PASS | 0.117 → 0.120 PASS | 0 h / 3 h PASS → PASS | r 0.918 → 0.926 PASS | ST_GAS 22.1 → 29.1 % PASS; CC 0.6 → 2.4 % | 2.4 / 8.1 % | 7.06 | control: **2 flips** (UC-attributable, §1) |
| 2022 | CC_REGULAR +1.24 → −2.39 PASS; ST_GAS −2.19 → −3.29 PASS; CC_CHP +2.43 → +2.39 | PASS → PASS | −0.7 → −1.4 % PASS | 0.149 → 0.171 PASS | 5 h / 101 h CAVEAT → FAIL* | r 0.826 → 0.828 PASS | ST_GAS 14.9 → 25.0 % PASS | 2.1 / 11.0 % | 13.38 | no flip |
| 2023 | **CC_REGULAR +0.61 → −4.03 PASS → FAIL; CC_CHP +2.81 → +3.32 (+3.4 pp) PASS → FAIL**; ST_GAS +1.34 → −0.43 PASS | PASS → PASS | +2.0 → +6.5 % PASS | 0.129 → 0.168 PASS | 0 h / 10 h CAVEAT → FAIL* | r 0.919 → 0.918 PASS | ST_GAS 11.3 → 17.1 % PASS; CC 1.0 → 4.8 % | 4.8 / 6.2 % | 4.03 | control: **2 flips** |
| 2024 | CC_REGULAR +2.02 → −2.40 PASS; ST_GAS −0.51 → −2.60 PASS; CC_CHP +0.84 → +1.31 | PASS → PASS | **−0.8 → +1.9 % PASS (Δ +2.7 pp)** | 0.118 → 0.156 PASS | 0 h / 13 h CAVEAT → FAIL* | r 0.890 → 0.885 PASS | ST_GAS 13.6 → 21.8 % PASS | 3.6 / 7.5 % | 22.94 | **T2 breached** (bar \|Δ\| ≤ 1 pp) |
| 2025 | (C1 SKIPPED: preliminary EIA-923) CC_REGULAR 35.39 → 31.10 TWh (−4.3); ST_GAS 10.25 → 8.62 | SKIPPED | **−7.7 → −10.2 % PASS → FAIL** | 0.148 → 0.178 PASS | 8 h / 42 h → **0 h** / 42 h CAVEAT → FAIL*† | r 0.841 → 0.840 PASS | ST_GAS 11.8 → 17.7 % PASS | 5.5 / 6.1 % | 4.85 | control: **flip** (C3a) |

\* attestation artefact (C6 UNATTESTED on a probe bundle; the ledger route is unavailable); magnitudes identical in 2022–2024.
† 2025's C3c magnitude also moved (8 → 0 hours > $300) — with C3a 2025 failing the lone-failure ledger would not apply anyway.
Determination: **CALIBRATED → NOT-YET** (arm: 7 scored, 3 FAIL criteria — C1, C3a, C3c — plus the unattested C6).

### 0.2 GATESPEC §6.1 wall rows (every shard, standard solve container, `MARKET_SIM_HIGHS_THREADS=1`, 4 cores; baseline = the same shard's P0 + P1, PRECOMMIT §5 proxy)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** total/(P0+P1) | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB (UC) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NYISO 2021 | 490.2 | 221.3 | 2,880.0 (7.73 / 37.69) | 268.9 | 3,460.3 | **7.06** | 1,188 (33 of 74 clusters) | 1 / 30 | 8.6e-4 | 0 | 6.25 |
| NYISO 2022 | 465.6 | 201.3 | 5,678.9 (15.39 / 34.77) | 264.3 | 6,228.9 | **13.38** | 1,224 (34 of 79) | 16 / 84 | 9.9e-4 | 0 | 6.26 |
| NYISO 2023 | 373.8 | 150.1 | 1,060.3 (2.77 / 8.14) | 223.7 | 1,505.2 | **4.03** | 1,188 (33 of 78) | 1 / 30 | 8.9e-4 | 0 | 6.20 |
| NYISO 2024 | 279.6 | 132.2 | 6,085.1 (16.54 / 40.28) | 147.4 | 6,412.7 | **22.94** | 1,224 (34 of 78) | 7 / 62 | 9.7e-4 | 0 | 6.08 |
| NYISO 2025 | 305.0 | 148.2 | 1,115.1 (2.92 / 7.48) | 156.8 | 1,479.1 | **4.85** | 1,224 (34 of 77) | 1 / 26 | 9.5e-4 | 0 | 6.09 |

Every window Optimal (1,825 of 1,825); 0 time-limit hits (W2 met); no pre-fixing; slim window on (`uc_slim_window=True`, ~63 % of
columns removed before HiGHS). Unlike SPP (every window at the root), **NYISO windows branch**: nodes p50 16 and p95 84 in 2022, 7 / 62
in 2024; the branch-and-bound tail is 70–93 % of the stage (2022: 5,285 of 5,679 s; 2021: 2,508 of 2,880 s; 2023/2025 ≈ 70 %); presolve 3–4 %. Year-to-year wall
varies 5×: 2023/2025 ≈ 2.8–2.9 s per window, 2022/2024 ≈ 15–17 s. Whole-shard wall 25–107 min. **D-2 is ruled at 3×** (plan §8.1):
every year is above the ceiling; the ratio is reported, not judged, and E10 month-parallel / the engine's next wall lever are the
owner's and the desk's calls.

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5)

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | no PASS → FAIL flip, any year / criterion / class row | CALIBRATED, every scored row PASS (C3c ledgered) | **5 real flips**: C1 CC_REGULAR 2021, 2023; C1 ST_GAS 2021; C1 CC_CHP 2023; C3a 2025 (+ 4 C3c and C6 attestation artefacts) | zero | **breached → kill #3** |
| T2 | \|ΔC3a\| ≤ 1 pp on 2024 | −0.8 % (39.27 vs 39.57) | **+1.9 %** (40.34 vs 39.57), Δ **+2.7 pp** | arm ∈ [−1.8, +0.2] | **breached** |
| T3 | C1 CC_REGULAR PASS in 2021–2024 (replacing the bridge must not move CC energy outside the band) | +1.31 / +1.24 / +0.61 / +2.02 TWh | **−4.71 FAIL / −2.39 / −4.03 FAIL / −2.40** TWh; 2025 −4.29 TWh (SKIPPED by the scorer) | PASS ×4 | **breached** (2021, 2023) |
| T4 (reported) | M3 low-price-hour ratios; lower-tercile error | ratios 0.00; lower error +12.0 / +23.0 / +9.5 / +6.7 / +8.9 $/MWh | ratios **0.00 in every year** (0 of 689 / 50 / 450 / 171 / 136 hours ≤ $15; 0 negative); lower error **+12.6 / +22.9 / +10.8 / +8.3 / +10.1** | sign: ratios up, error down | **wrong sign** in 2021, 2023, 2024, 2025 (up); flat in 2022 |
| T5 (reported) | kept `reliability_floor` ST_GAS forced TWh / share; C8 with and without MECH 28 | 1.66 / 1.29 / 1.26 / 1.52 / 1.43 TWh = 21.9 / 14.4 / 10.9 / 13.3 / 11.5 % | **1.34 / 1.07 / 1.08 / 1.26 / 1.24 TWh = 21.0 / 14.0 / 10.9 / 14.3 / 11.6 %** — the floor's own forced energy FELL 0.2–0.4 TWh (class energy fell); C8 as printed 29.1 / 25.0 / 17.1 / 21.8 / 17.7 % (MECH 28 inside, PASS everywhere, 2021 at 0.9 pp under the cap); with MECH 28 removed (R4) = the floor's share, 21.0 % at most | reported | no C8 flip under either reading; **no stacking** (the SPP interaction did not appear) |
| control | every leg P1 Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | 0 MWh; 137 D-4 rows, 0 FAIL | P1 Optimal ×5; unserved **0.0 MWh** every year; **one new D-4 FAIL row** in 2021 / 2023 / 2024: `reliability_floor × ST_GAS` plant 2480 floored 0.5 / 1.5 / 0.02 GWh (≤ 0.1 % of the mechanism's forced energy) while its meter reads zero in those 23 / 78 / 1 hours (per-unit conduct rider) | — | **breached by the letter** (1.5 GWh); immaterial in magnitude, named |
| S1 | MECH 28 share | 0 | CC_REGULAR 2.1–5.5 %, ST_GAS 6.1–11.0 % (0.60–1.64 TWh and 0.52–0.84 TWh per year); the bridge's rows (CC 0.3–1.0 %, ST_GAS 0.2–0.5 %) are gone | reported (R4) | — |
| S2 | starts per plant-year vs CEMS (M1) | CC 1,258 / 780 / 1,605 / 1,336 / 1,165 vs 797 / 727 / 740 / 649 / 804 (1.1–2.2×); ST_GAS 761–1,163 vs 162–210 (4–7×) | **CC 439 / 431 / 464 / 511 / 584 = 0.55 / 0.59 / 0.63 / 0.79 / 0.73× CEMS; ST_GAS 64 / 83 / 85 / 93 / 108 = 0.35 / 0.42 / 0.46 / 0.57 / 0.51×** | toward CEMS | overshoots (as SPP): both classes now under-cycle; M2(a) (CEMS on, model off) → 0.00 TWh in every year, M2(b) 0.01–0.05 TWh |
| S3 | online capacity vs a measured series | no NYISO comparator on disk | SKIPPED (PRECOMMIT §4); `online_mw` is in `uc_schedule_<y>.parquet` for a later comparator | — | — |
| S4 | integer set, fallback | UC-0 M6: 32 clusters 14.5 GW; 4 CC on the no-load fallback | 33–34 integer clusters of 74–79 (166–174 fleet rows), 1,188–1,224 integers per window; `uc_solve_log_<y>.json clusters[].src` | reported | — |
| S5 | M4 reserve dormancy | model 1.00 / 0.999 / 0.999 / 1.00 / 0.996 vs actual 0.85 / 0.79 / 0.83 / 0.83 / 0.68 | **1.00 / 0.999 / 1.00 / 1.00 / 0.998** — unmoved; mean MCP $0.00–0.09 vs $2–7 | reported | no move (as SPP) |
| W1 | wall rows | — | §0.2 | reported | — |
| W2 | time-limit hits | — | 0 / 365 every year | ≤ 3 | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ·load | — | **1.60 / 1.78 / 1.36 / 1.38 / 1.83 %** ($109 M / $231 M / $72 M / $84 M / $173 M on $6.8 / 13.0 / 5.3 / 6.1 / 9.4 B) | ≤ 2 % | met |
| W4 | infeasible windows | — | 0 (at the pin; see §4 for the two infeasibilities the gate caught at earlier pins) | 0 | met |
| kill #1 | infeasible window | — | none in the span; fired TWICE at the gate (A.2, C) and fixed upstream before any span shard | — | not fired in the span |
| kill #2 | non-determinism | — | not exercised (one completed run per year; no relaunch) | — | — |
| kill #3 | control flip | — | **fired** (5 real flips) | — | **R** |

**2021 under the §9 drift rule.** C3a 2021 moves +4.3 → +6.6 % (Δ 2.3 pt > the 1.1 pt drift envelope) and C1 CC_REGULAR moves
−6.0 TWh (≫ 0.10 TWh): both 2021 flips are **UC-attributable**, not drift. The known `59490433` drift (one CT_CHP unit's May–June
markup, ≤ 2.72 $/MWh on 10,544 zone-hours) is inside the arm's 2021 leg and is not separable here; it is bounded and routed as before.

## 2. What the UC did to the dispatch (zero LP, from the composed sidecars)

| year | CC_REGULAR TWh | ST_GAS TWh | imports TWh | CT_PEAKER TWh | CC_CHP TWh | load-weighted mean price $/MWh | zone-hours > $200 |
|---|---|---|---|---|---|---|---|
| 2021 | 31.63 → **25.61** (−6.0) | 5.87 → 5.00 | 27.48 → **33.45** (+6.0) | 3.32 → 3.84 | 16.29 → 16.71 | 43.95 → 44.94 (**+1.00**) | 1 → 1 |
| 2022 | 36.35 → **32.52** (−3.8) | 6.99 → 5.78 | 25.88 → **31.41** (+5.5) | 2.40 → 2.44 | 17.45 → 17.41 | 85.70 → 85.09 (−0.61) | 563 → 473 |
| 2023 | 33.67 → **29.03** (−4.6) | 9.67 → 7.89 | 23.12 → **28.45** (+5.3) | 0.47 → 0.68 | 17.63 → 18.14 | 34.59 → 36.11 (**+1.52**) | 1 → 1 |
| 2024 | 36.11 → **31.70** (−4.4) | 9.51 → 7.42 | 23.15 → **28.86** (+5.7) | 0.56 → 0.68 | 17.87 → 18.34 | 39.27 → 40.34 (**+1.07**) | 47 → 61 |
| 2025 | 35.39 → **31.10** (−4.3) | 10.25 → 8.62 | 19.59 → **25.94** (+6.4) | 1.31 → 1.05 | 19.33 → 19.44 | 63.90 → 62.14 (−1.75) | 475 → 415 |

Nuclear, hydro, wind, solar, OTHER are unchanged to 0.01 TWh (budget-governed or must-run). Unserved energy 0.0 MWh in every year.

- **Imports for CC.** With start and no-load paid once and 21-h / 6-h min-up / min-down on CC, the stage keeps fewer CC plants online
  through the day and the P1 LP buys the energy at the ties instead (imports float within TTC in P1; the window pin is a stage-internal
  construct): +5.3 to +6.4 TWh/yr. In SPP the same decommit went to coal; NYISO has no coal, so it goes to the seam. The monthly landing band
  (`nyiso_import_landing_band`) brackets each link's monthly net flow, so the extra imports sit inside the measured P-32 band.
- **Prices up where the troughs were CC-set.** Removing the bridge's min-load CC (0.19–0.32 TWh/yr held at min load) and decommitting
  further CC raises the marginal unit in trough and shoulder hours in 2021 / 2023 / 2024 (lower-tercile error up $0.6–1.6/MWh); in the
  high-gas years 2022 and 2025 the body falls instead (−$0.6 / −1.8) and 2025 crosses the −10 % edge. The model-wide trough excess
  UC-0 measured (F1) is therefore not a commitment-state artefact in NYISO: the integer stage makes it slightly worse.
- **Cycling collapses** to 0.55–0.79× CEMS for CC and 0.35–0.57× for ST_GAS: the stage under-cycles both slow classes, the same
  overshoot SPP showed.
- **The kept floor did not stack.** `reliability_floor` ST_GAS forced energy fell 0.2–0.4 TWh/yr (the class shrank); its share is
  within 1 pp of the control. MECH 28 adds 6–11 pp of ST_GAS energy on top, so C8 as printed reaches 29.1 % in 2021 (0.9 pp under the
  cap) — PASS under both readings (R4). The one D-4 row is a per-unit conduct rider at ≤ 1.5 GWh.
- **Reserves untouched**: reserve MCP < $1 in ≥ 99.8 % of hours, as in the control.
- **Uplift** $72–231 M/yr, 1.4–1.8 % of wholesale energy cost.

## 3. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7: kill #3 fired; T2 and T3 breached; T4 wrong sign). The mechanism is structurally real (integer
  commitment on measured physics, zero free parameters, every window Optimal), and on a calibrated ISO it moves CC energy 4–6 TWh/yr
  out of the C1 band toward imports and the 2025 price past the C3a edge. This is the control reading the GATESPEC wrote for exactly
  this case: the UC as built does not leave NYISO calibrated.
- **Matrix:** NYISO `unit_commitment_milp` → **R**, evidence this RESULT (stamped by this lane as its last commit; integer state is the
  new evidence against the K bridge cell's re-open clause, rule 28 — the clause is now exercised and the answer is R).
- **D-6 card (copy-paste):** *"UC-2 NYISO A/B — record R. The MILP UC stage at f2bf73bf solves every NYISO year (1,825/1,825 windows
  Optimal, 0 time-limit hits, 4–23× the P0+P1 wall). Replacing the gas commitment bridge by the UC decommits 3.8–6.0 TWh/yr of
  CC_REGULAR (imports fill it): C1 CC_REGULAR 2021/2023, ST_GAS 2021 and CC_CHP 2023 flip PASS → FAIL; C3a 2024 moves −0.8 → +1.9 %
  (2.7 pp, bar 1 pp); C3a 2025 −7.7 → −10.2 % flips; the trough error rises in 4 of 5 years; CC starts fall to 0.6–0.8× CEMS; uplift
  1.4–1.8 %; the kept reliability floor did not stack. Options: (1) record R, stage stays default-off for NYISO [recommended]; (2) hold
  for an engine change that keeps the bridge's P0-anchored commitment as the UC's warm/initial state (the decommit is the whole delta);
  (3) promote on structure (not recommended: 5 real control flips on a CALIBRATED ISO)."*
- **Not a tuning invitation.** No `uc_*` value was moved; the floors were not touched; the readings are reported as they fell.
- **For the program (GATESPEC §7.2 / plan §6):** NYISO was the control the no-flip bar was written to protect, and it did its job. The
  SPP and NYISO A/Bs agree on the mechanism's signature (CC decommitted, cycling under CEMS, reserves unmoved) and disagree on the price
  sign (SPP body down, NYISO body up in 3 of 5 years): the price effect is set by what replaces the decommitted CC (coal in SPP, imports
  in NYISO), not by the commitment stage itself.

## 4. The gate that paid for itself (process record; PRECOMMIT Addenda A–E)

| pin | what the L1 gate found | fix | span shards spent |
|---|---|---|---|
| `2f872a62` | (a) `YearCapture.save` cannot pickle NYISO's bridge-hook closure (bench harness); (b) **engine defect 3**: time-major `ttc`/`ttc_import` `(8760, 13)` reach the 36-h window unsliced | PR #7221 (`dc3860be`) | 0 |
| `dc3860be` | **engine defect 4 (kill #1 at the gate)**: `import_link_band` (4 landing links × 12 months = 48 rows) passes the window slicer with the year's monthly MWh bounds; LP relaxation infeasible a priori — root-caused zero-LP in the parent (C.1) | PR #7224 (`f2bf73bf`): the band joins the window's budget set; banded links' flows pinned to P0 | 0 |
| `f2bf73bf` | **PASS**: window 0 Optimal 7.75 s / 6 nodes / gap 1.4e-4; January 31/31, 0 TL, gap_max 9.4e-4, 565 s | — | 5 (all solved) |

Three bench shards (one container-hour of P0 + P1 captures), zero span shards wasted; the SPP lane's precedent (21 span shards for 7
legs) is why the gate exists. Bench branches `claude/ucmilp-bench-nyiso-2024-L1` (`aa9f123e`: the defect-4 dump) and
`claude/ucmilp-bench-nyiso-2024-L1-r3` (`5d83b39`: the passing gate) carry JSON/markdown only.

## 5. Bundles, cost, what survives (rule 31: nothing deleted)

| artefact | where | promotable? |
|---|---|---|
| five leg bundles (full, incl. `dispatch/<y>_P1.parquet`, 51–55 MB each; `unit_hourly_<y>.parquet` rode along under the out-dir negation) | shard branches `claude/ucmilp-nyiso-2021` `ac60993b` · `-2022` `f1a9dd7a` · `-2023` `b2af1ece` · `-2024` `eacb860f` · `-2025` `af7f52b6` (all parented on `f2bf73bf`); checked out locally under `results/calibration/ucmilp_nyiso_<y>/` | yes in form (rule 34); no promotion recommended |
| composed span `results/calibration/ucmilp_nyiso_span` | slim copy in this PR: `docs/records/nyiso/ucmilp/data/ucmilp_nyiso_span/` (hourly sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`; `uc_solve_log_<y>.json`; `meta.json`, `metrics.json`, `run_config*.json`; regenerated `legitimacy_diagnostics.json`; `readings/` = the control and arm `calibration_verdict --json` outputs and the arm M1/M3/M4) | not registered (E13) |
| shared benchmark frames | respanned to the keeper's own hashes (`campd-651a393cda7b`, `eia923-4bf3ca54ed56`, `eia930-cdfb8908ef53`) — the arm is scored on the control's benchmark basis | — |

Composition deviations, disclosed (SPP Addendum D precedent): the committed `_ucmilp_compose_span.py` aborts on `gas_price_override`
(recorded per year by this keeper) and lacks `_respan_shared_inputs`; a scratch copy with `gas_price_override` added to
`PER_YEAR_FIELDS` and the W0 composer's respan called after `meta.json` is written was run (no repo script edited; routed to the
engine lane again). Local registration for scoring (`dashboard_add_run.py --no-prune`) wrote only the sidecar and payload, both moved
out of the tree and never committed; no bench part changed.

Cost: 3 bench + 5 span containers; the span 25–107 min wall each; zero LP in the parent. Cost to reproduce the arm: five shards at
`f2bf73bf`, ~2.5 container-hours of UC. **Promotion question: none is proposed**; the lane recommends `R`. Shard branches are
transport (rule 33): the owner may delete the five `claude/ucmilp-nyiso-<y>` and two `claude/ucmilp-bench-nyiso-*` branches once
this PR merges (a session cannot, 403). Shards: 8 launched (3 bench + 5 span), 8 archived; none left alive.

## Log entry

- 2026-10-10 · UC-2-NYISO `session_01HoVUBRJhqpY4TQdLq6NkPR` (Fable) · `claude/ucmilp-2-nyiso-ab-y5h8` · zero LP in the parent ·
  PRECOMMIT `1268e70d` before any shard · L1 gate (new) caught two engine defects before any span shard: time-major TTC unsliced
  (#7221) and the monthly import-link band unsliced → window 0 infeasible a priori (#7224, root-caused zero-LP in the lane); gate
  PASS at `f2bf73bf` (window 0 Optimal, Jan 31/31) · span 5/5 solved, 1,825/1,825 windows Optimal · **verdict R**: C1 CC_REGULAR
  2021/2023, ST_GAS 2021, CC_CHP 2023 and C3a 2025 (−7.7 → −10.2 %) flip PASS → FAIL; C3a 2024 −0.8 → +1.9 % (T2 breached); CC
  −3.8 to −6.0 TWh/yr → imports; trough error up in 4 of 5 years; CC starts 0.55–0.79× CEMS; uplift 1.4–1.8 %; kept reliability
  floor did not stack; wall 4.0–22.9× P0+P1 · nothing registered (E13); slim span under `docs/records/nyiso/ucmilp/data/` · cell
  `unit_commitment_milp` NYISO → R · D-6: record R · no promotion proposed.
