# FINDING — soco-75: coal incremental heat rate is measurable, but its only carrier is a one-sided floor; building the SOCO arm needs an owner ruling (zero LP, no solve)

Lane soco-75, 2026-09-27. Keeper `2026-09-26-soco72-gas-basis-window` (bundle `soco72_span`) is **unchanged**. No
PRECOMMIT, no shard, no registration. Task 1 stops at the handoff's rule-19 instruction ("if a registered field already
carries a tranche heat-rate slope, do not stack a second mechanism").

- **Probe:** `scripts/probes/_soco75_incremental_hr.py` (modes `measure`, `greedy --basis {year,pooled} --scope
  {all,mustrun}`). Greedy re-uses soco-73's instrument (`_soco73_phase0.greedy`, `c1_rows` = scorer-exact
  `calibration_verdict.score_fuelmix`, `c4_coal`), baseline-differenced.
- **Inputs:** CAMPD unit-level hourly AL/GA/FL/MS 2019–2025; the seven soco72 legs at the full SHAs in
  FINDING-soco-73 (gitignored locally).

## 1. How SOCO's coal econ tranches are priced today

- `offer_curve_by_group` for all four coal subclasses is **1.0 on every band** (committed, econ_low, econ_high, peak).
- Every coal tranche is therefore priced at `fuel × plant-year AVERAGE HR + $4.50 VOM`. The HR is
  `campd_coal_heat_rates_SOCO.csv` (`sum(heatInput)/sum(grossLoad)`, opTime ≥ 0.99, net via 0.93).
- Consequence: at a plant with a measured must-run floor, the `_committed`/`_econ*` tranches above the floor are
  offered at the average rate, which includes no-load heat the floor has already sunk.

## 2. Rule 19: a registered carrier already exists — and it points the other way

`coal_econ_marginal_hr_bound` (`scenarios.py:12391`, ERCOT keeper default-on, `data/coal.py:
apply_coal_econ_marginal_hr_floor`) reads the same measurement (`derive_campd_marginal_hr.py`: CEMS I/O slope,
quadratic, econ_low at x = 0.5, econ_high at x = 0.9). Two facts decide it:

| property | registered carrier | what this task asks |
|---|---|---|
| direction | **floor**: raises a band up to incremental HR, never lowers | lower econ offers **to** incremental HR |
| grain | class band multiplier (`offer_curve_by_group`) | per plant |
| SOCO effect if armed | **inert**: bands are 1.0, measured incremental is below 1.0 at every plant (§3) | — |

- ERCOT's promotion explicitly kept offers above incremental as "genuine markup … passes through untouched". Lowering
  econ offers is a polarity reversal of that design, not an arming of it.
- soco-74's note that there is "no registered field" for this object is **corrected**: there is one, and it is
  inert for SOCO.
- A new field would stack a second mechanism on the same tranches and measurement. The handoff forbids that. The
  non-stacking route (a two-sided, per-plant mode of `coal_econ_marginal_hr_bound`) changes an ERCOT-keeper mechanism
  and runs through the band channel the handoff lists as not a lever. **That is the owner's call** (§6).

## 3. Measurement: incremental / average HR, per plant, 2019–2025

Frozen derive construction; ratio to the artifact average the tranche is priced at (both gross, so the parasitic
factor cancels). Plant-year values are generation-weighted over coal units.

| plant | floor? | econ_low mean (sd) | econ_high mean (sd) | linear OLS cross-check | years |
|---|---|---|---|---|---|
| Bowen | must-run | 0.981 (0.025) | 1.003 (0.031) | 0.995 | 7 |
| Miller (PRB) | must-run | 0.924 (0.020) | 0.993 (0.039) | 0.963 | 7 |
| Scherer (PRB) | must-run | 0.931 (0.023) | 0.972 (0.043) | 0.952 | 7 |
| Daniel | must-run | 0.893 (0.040) | 0.910 (0.089) | 0.900 | 7 |
| Gaston | must-run | 0.904 (0.074) | 0.892 (0.083) | 0.952 | 7 |
| Barry | cycler | 0.953 (0.080) | 0.974 (0.125) | 0.999 | 7 |
| Wansley | cycler | 0.909 (0.012) | 0.897 (0.030) | 0.905 | 4 |
| Crist | cycler | 0.934 (0.049) | 0.949 (0.063) | 1.026 | 2 |

- **Identifiable, and small.** Incremental sits 0–11 % below average: about $0–3.5/MWh at SOCO fuel prices. The
  soco-73 H2-2020 gap is $7–23/MWh.
- **Stable where it matters.** Bowen, Miller and Scherer: sd ≤ 0.04 and quadratic within ~0.04 of linear.
- **Weak where it is noisy.** Gaston ranges 0.80–1.03 by year. Barry's 2024–25 layup years read 1.05–1.18.
- **Consistent with SOCO-64 §2.** Coal no-load share is 3–6 % of full-load input.
- **Forward story (rule 13).** Pooled per-plant ratio in a forecast year, same-year in backcast. That is the same
  year-0 / per-year convention the average-HR artifact already uses. Zero new scalars (rule 21).

## 4. Physics: only the must-run-floored plants are admissible (rule 14, rule 18)

- **SOCO-63 §5 applies to the cyclers.** In a start-cost-free tranche LP, the average HR is the only place no-load fuel
  lives. Tranches carry no `pmin` (`docs/binning-methodology.md`), so a cycler's `_econlo` priced at incremental would
  clear before its own min-load block. That deletes a real cost.
- **It does not apply to Bowen, Miller, Scherer, Daniel or Gaston.** Their measured `_mustrun` floor keeps the boiler
  on, so the no-load heat is sunk and the next MWh costs the incremental rate.
- Scope is set by a unit parameter (a measured must-run row), never by a class or plant list (rule 18).

## 5. Reach: greedy, baseline-differenced (arm − baseline through the same instrument)

**Admissible arm (must-run plants only).** Values are year basis / pooled basis. The LP moved about 3× the greedy in
soco-72.

| row | keeper | arm (year / pooled) | at ~3× LP (year) |
|---|---|---|---|
| **2019 C1 COAL_BIT** | −4.24 pp FAIL | −4.01 / −4.18 **FAIL** | ≈ −3.6 pp, ≈ −9.6 TWh vs ±7.64: **still FAIL** |
| **2020 C4 coal NRMSE** | 0.304 FAIL | 0.289 / 0.294 | would PASS |
| 2022 COAL_PRB (thinnest) | +2.69 | +2.72 / +2.72 | ≈ +2.78, **thinner** |
| 2021 ST_GAS | −2.73 | −2.74 / −2.75 | thinner |
| 2019 CC_REGULAR | +2.86 | +2.71 / +2.70 | better |
| 2019 CT_PEAKER | +2.71 | +2.47 / +2.04 | better |
| 2020 CC_REGULAR | +2.26 | +1.97 / +2.05 | better |
| 2023 CT_PEAKER | +2.40 | +2.35 / +2.36 | better |
| 2019 COAL_PRB | +0.71 | +1.03 / **+1.84** | pooled ×3 ≈ +3 pp: **FAIL risk** |

C4 coal by year, keeper → arm (year basis): 2019 0.263 → 0.242; 2020 0.304 → 0.289; 2021 0.208 → 0.205;
2022 0.240 → 0.251; 2023 0.268 → 0.258; 2024 0.256 → 0.243. 2025 is skipped (preliminary EIA-923).

- **Over-run years are untouched.** Wansley and Barry are cyclers, out of scope. Their deltas are +0.000 in 2021
  and 2022.
- **2020 C4 moves through Miller (+0.85 TWh) and Scherer (+0.45).** Bowen, which carries 20 % of that error, moves
  +0.001: its incremental ratio is 0.995 in 2020.
- **Unscoped arm (cyclers included), reported and refused (§4).** 2019 COAL_BIT −4.24 → −2.94 pp, still FAIL on
  volume. That comes from Wansley +2.0 TWh in 2019, and it adds +1.76 TWh to Wansley's 2021 over-run of +5.0.

**Verdict.** The admissible arm probably closes 2020 C4 (greedy margin to 0.30: 0.011 year / 0.006 pooled). It does not close 2019 COAL_BIT
and thins 2022 COAL_PRB, 2021 ST_GAS and 2022 C4. Pooled, it puts 2019 COAL_PRB at FAIL risk.

## 6. Owner question

Authorize a **SOCO-scoped, per-plant, two-sided mode of `coal_econ_marginal_hr_bound`**?

- **What it does.** Above-floor coal tranches of plants carrying a measured `_mustrun` row are priced at their own
  measured incremental HR. Same-year in backcast, pooled forward. ERCOT's floor semantics stay byte-identical.
- **Why it is a reconciliation, not a stack (rule 19).** It is one mechanism with a mode. It needs `src/` work (an
  Opus/Fable lane), a matrix row, seven shards and a PRECOMMIT.
- **Expected.** 2020 C4 → pass. 2019 COAL_BIT stays failing. 2022 COAL_PRB thins.
- **If declined.** The cell stays `I` for SOCO and the object stays open.

## 7. Matrix / retrievability

- **Matrix.** `coal_econ_bound` SOCO cell U → **I**. The registered floor is inert for SOCO by measurement: every
  plant's incremental HR is below the 1.0 band. The two-sided reading is recorded as an open owner question.
- **Retrievability.** Nothing was solved, so nothing is promotable. The soco72 legs remain recoverable only at the
  FINDING-soco-73 SHAs (cost any re-use as a re-solve, rule 33(d)).
