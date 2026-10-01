# RESULT — R-ERCOT-23: the 2021 LCAP window and the protocol price cap — PROMOTED; ISO stays NOT-YET

- **Promotion basis:** the owner's standing instruction, *"Is it an improvement? Then promote"* (rules 31/35).
- **Keeper:** `2026-10-01-r-23-swcap-hourly`, bundle `results/calibration/r_ercot23_span`, 2019–2025. It supersedes `2026-10-01-r-22-ordc-shift`, which is pruned.
- **Records:**
  - PRECOMMIT: `PRECOMMIT-r-ercot-23-swcap-effective-hourly-2026-10-01.md`, pinned SHA `651723e30ac9598689bffb9782493a58eb493445`.
  - Phase 0: `scripts/probes/_r_ercot23_lcap_id.py`, which writes `r_ercot23_phase0.json`.
  - Scorecard: `r_ercot23_scorecard.json`.

## 1. What was wrong in 2021: the VOLL, not the curve

The published RTORPA formula was evaluated on ERCOT's measured RTOLCAP, RTOFFCAP and λ. The two terms were split using measured RTOFFPA.

- **Uri (February) reproduces:** formula 65.1k vs measured 58.0k $·h.
- **April–November is 8–10× over** in every month.
- **Why:** Uri crossed the Peaker Net Margin threshold. ERCOT moved Real-Time to the **LCAP of $2,000 from Operating Day 2021-03-04** (notice M-B030321-01; 16 TAC 25.505(g)(6)). The ORDC's VOLL equals the SWCAP (OBD §2.1).
- **ERCOT says so directly.** Its 2022 Biennial ORDC Report §1.3: *"SWCAP (and therefore VOLL) was reduced to the LCAP of $2,000/MWh from March 4, 2021, until the end of that year."*

**A second defect: the protocol cap.** Protocols limit λ + all adders to the SWCAP (same report, §1.2). The model added measured RTORDPA uncapped, so the 2021 written price reached $10,771.

## 2. Identification (formula ÷ measured RTORPA)

| Year | Keeper curve | + LCAP | Diagnostic: OBD half-hour form | Diagnostic: + ERCOT Fig. 3 μ/σ |
|---|---|---|---|---|
| 2019 | 1.04 | 1.04 | 0.99 | 0.94 |
| 2020 | 1.43 | 1.43 | 1.25 | **0.85** |
| **2021** | **1.59 (r 0.876)** | **1.14 (r 0.985)** | 1.07 | 1.06 |
| 2022 | 1.08 | 1.08 | 0.92 | 0.88 |
| 2023 | 1.09 | 1.09 | 0.96 | — |
| 2024 | 0.85 | 0.85 | 0.79 | — |

**The 2020 residual has the same cause as 2021's post-LCAP 1.41×: the curve-parameter vintage.** That covers two things:
- The OBD's 30-minute curve takes mean 0.5·(μ + Sσ). Our code applies μ/2 + S·0.707σ.
- ERCOT publishes seasonal μ (shift included) and σ: ≈640 / 1,210 MW (2019), ≈900 / 1,210 (2020–21), ≈880 / 1,280 (2022). These are digitized from the figure to about ±15 MW. Our model uses a flat fallback of 0 / 1,400.

Together these take 2020 to 0.85×. They are **carded, not built** (§6): they move every year, including the 2023 hold.

## 3. The change

**`ercot_swcap_effective_hourly`**: default off, ERCOT-gated, zero DOF. It is one hourly SWCAP series, used at the four places the cap binds:
- the VOLL-anchored reserve-family penalties, scaled by SWCAP_t / VOLL;
- the load-shed cost;
- the offer clip;
- the post-solve protocol cap λ + adders ≤ SWCAP.

Solves:
- **G-DRIFT:** `f4d29d72..main` is empty on the solve path.
- **Re-solved:** 2019 and 2021, one shard each (rule 36). Legs: 2019 `1bc2fa1d…`, 2021 `48e7a633…`. Both shards are archived.
- **Reused:** 2020, 2022, 2023, 2024 and 2025 are the r-21 legs. Their hourlies are byte-identical to the r-22 keeper's, and the flag binds in zero hours of those years.
- **2023** is the carve-out on owner hold and is not armed.

## 4. Per year, r-22 → r-23 (P1, `calibration_verdict --years`)

| Year | Det. | C3a | LW $/MWh | C3b | C3c h > $200 (model/actual) | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | h > $1k | max $ | slack MWh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | NOT-YET (=) | +7.5 → **+7.0 %** | 50.03 → 49.81 | 0.231 → **0.219** F | 100 / 106 (=) | +8.85 F | −10.48 F | +3.29 | 17.6 % | 30 | 9,656 → 9,000 | 0 |
| 2020 | NOT-YET (=) | +5.2 % | 26.73 | 0.221 F | 38 / 56 | +10.41 F | −11.77 F | +2.88 | 23.6 % | 3 | 1,903 | 0 |
| **2021** | CAL (=) | +4.2 → **+1.0 %** | 172.88 → **167.58** | 0.063 → 0.062 | 664 → 653 / 258 (ledgered) | −2.07 | −1.67 | −0.01 | 22.0 % | 122 → 113 | 10,771 → 9,000 | 3,194 (=) |
| 2022 | NOT-YET (=) | −9.3 % | 68.07 | 0.175 | 96 / 196 | −9.87 F | +5.84 | −0.94 | 29.6 % | 17 | 3,312 | 0 |
| 2023 hold | NOT-YET (=) | −24.2 % | 49.28 | 0.380 F | 140 / 181 | +0.65 | −2.17 | −0.76 | 18.7 % | 34 | 5,025 | 0 |
| 2024 | NOT-YET (=) | −11.1 % F | 27.72 | 0.197 | 12 / 53 | −4.28 | −0.95 | −1.20 | 15.5 % | 0 | 882 | 0 |
| 2025 | CAL (=) | −9.2 % | 33.13 | 0.126 | 0 / 31 | — | +3.64 | — | 21.0 % | 0 | 142 | 0 |

- **2021 LCAP-window ORDC adder** (LW contribution): 4.60 → **1.02** $/MWh, against measured RTORPA of 0.47.
- **Dispatch:** at most 0.002 TWh moved per class in 2021, and nothing moved in 2019.

## 5. Prediction scorecard (PRECOMMIT §5)

| Prediction | Outcome |
|---|---|
| 2021 LW 166.5–169.0 | HIT (167.58) |
| 2021 C3a +0.5 to +2.0 % | HIT (+1.0 %) |
| 2021 LCAP-window adder 0.8–1.3 | HIT (1.02) |
| 2021 max 9,000; h > $1k 110–116; C3c 645–658 | HIT (9,000; 113; 653) |
| 2021 C3b 0.055–0.065; slack 3,194 ± 50; C1 ± 0.5 TWh | HIT (0.062; 3,194; ≤ 0.002) |
| 2019 LW 49.7–49.9; C3a +7.0 to +7.3 %; max 9,000 | HIT (49.81; +7.0 %; 9,000) |
| 2019 C3b 0.225–0.232 | **MISS, favourable** (0.219). The capped Uri-scale hours carried more shape error than mean. |
| Determinations unchanged; ISO NOT-YET | HIT |

## 6. Cards (not built)

**ORDC curve-parameter vintage** (diagnostic in §2):
- What it is: the OBD half-hour mean form plus ERCOT's published seasonal μ/σ.
- It is structural and zero-DOF.
- It moves every year, including the 2023 owner-hold year.
- The 2023–25 values need ERCOT's 2024 Biennial ORDC Report.
- Expected effect: the 2019–2022 adder goes to about 0.85–0.94× of measured RTORPA, and the 2020 model adder gap (+0.5 $/MWh LW) closes.
- It needs an owner call on the 2023 hold before it is built.

**2019/2020 C1 coal/CC mirror:** fenced coal conduct. There is no new admissible evidence, so it is not raised.

## 7. Promotion (rule 35)

- **Year union** before the prune: {2019 … 2025}. Covered.
- **Re-keyed:**
  - `keepers/ERCOT.json`: keeper, three configs, `r_ercot23_extension`
  - `calibration-complete.json`: `keeper_rekey_2026_10_01_r23`; the marker stays withdrawn
  - `forecast/program-status.json`: ERCOT gate (a) only; `marker complete=False final=False` kept
  - `status/ERCOT.js`
  - ERCOT matrix shard: keeper, gates, and the cell `ercot_swcap_effective_hourly` = **K**
  - `mechanism-testing-matrix.md` §5.1
- **Checks:**
  - `audit_keepers` between promote and prune: only the expected E13 on r-22.
  - `prune_iso_runs --iso ERCOT --force-uncite` removed r-22's three stores.
  - `audit_keepers` after the prune: 0 failures, 0 warnings.
  - `check_promotion_completeness --iso ERCOT`: OK.

## 8. Where the bytes are (rule 34(e))

- **On `main` with this PR:** the slim bundle `results/calibration/r_ercot23_span` with its hourly sidecars, the registry sidecar and the run payload.
- **Legs are provenance only** (rule 33(d)): 2019 `1bc2fa1db8ddfe4e40513daa244756b71babb5c2`, 2021 `48e7a6334b8eaf8d7214edf2aced4526664fb240`. Recovering a leg is costed as a re-solve of about 20 minutes per year.

**Refs for the owner to delete** (sessions cannot delete refs, rule 33(f)):
- `claude/r-ercot23-arm-2019`
- `claude/r-ercot23-arm-2021`
- `claude/r-ercot22-arm-2019`
- `claude/r-ercot-22-handoff` (merged)
- `claude/r-ercot-22-tail-slope` (merged)

The `r-ercot21/20-arm-*` refs listed in the handoff are already gone.

## 9. Routed, unchanged

- **Pre-existing failures on `main`, not this lane's:**
  - `tests/unit/config/test_d53_sector_gate_miso_arming.py`
  - `test_ccs_retrofit::test_off_is_byte_identical_and_cache_neutral` and `test_d60_arming_batch` (Q42 pins)
  - `test_export`
  - `test_soundness` end-to-end
  - `test_fleet_arrays_golden` (ERCOT 2023 golden)
  - CAISO/MISO/NEISO/NYISO solve-surface pins
  - Each of these fails identically on clean `main`.
- Wharton CC marginal-HR estimator (card only).
- Bench display rows 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts.
