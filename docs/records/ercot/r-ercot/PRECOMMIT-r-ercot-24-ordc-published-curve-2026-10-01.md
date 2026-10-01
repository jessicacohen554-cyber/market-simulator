# PRECOMMIT — R-ERCOT-24: ERCOT's published ORDC curve (`ercot_ordc_published_curve`)

- **Lane:** ERCOT, R-ERCOT-24 (handoff `HANDOFF-r-ercot-24.md`, Task 1).
- **Incumbent / control:** keeper `2026-10-01-r-23-swcap-hourly`, bundle `results/calibration/r_ercot23_span` (2019–2025). The committed bundle is the control (rule 29(b)); no control solve.
- **Phase 0:** `scripts/probes/_r_ercot24_ordc_vintage_id.py` → `r_ercot24_phase0.json` (zero LP).
- **Owner decision card (2026-10-01):** answer verbatim *"All years incl. 2023 (Recommended)"*. The build moves the 2023 owner-hold year's ORDC curve only; its k=33 carve-out is untouched.

## 1. The two deviations (both zero-DOF)

**(a) The first-half curve.** ORDC OBD §2.3, identical in all 20 vintages 2019-02-13 → 2024-10-01 (ERCOT's archive zip): `SLOLP_s = 1 − CDF(0.5·μs, 0.707·σ)` with `μs = μ + S·σ`. The shift halves with the mean. The model applies `μ/2 + S·σ/√2`.

**(b) The parameters.** ERCOT re-derives μ and σ each season (NP6-576-ER, report 13233). Since 2019 there is one value per season, with no time-of-day blocks. The model uses a flat `μ = 0, σ = 1,400`.
- **Source.** The NP6-576 listing on the free MIS path returns no documents (retention). The credentialed API is owner-declined. So the values are read from Figure 3 of ERCOT's 2022 and 2024 Biennial ORDC Reports. Both PDFs and their figure images are committed under `data/raw/ercot/ordc-biennial/`.
- **Digitization** (`scripts/data/derive_ercot_ordc_mu_sigma.py` → `data/raw/ercot/ercot_ordc_mu_sigma_seasonal.csv`):
  - The MW axis is calibrated in-figure on the MCL line (2,000 / 3,000 MW).
  - The quarter grid is anchored on the MCL step at 2022-01-01.
  - Resolution is 6.3 MW/px (2022 report) and 11.5 MW/px (2024 report).
  - The 15 seasons both reports show agree to −8 ± 5 MW (μ) and −5 ± 5 MW (σ). No offset is applied.
- **Rule-14 status.** This is a declared reconciliation (±15 MW). The plotted "ORDC Mu" includes the shift: its Mar-2019 and Mar-2020 steps are each ≈ 0.25σ.
- **2025:** the last published season (Sep-2024: μs 879, σ 1,305) is carried forward. The model's 2025 ORDC adder is $0.00 either way.

## 2. Identification (formula on ERCOT's measured RTOLCAP / RTOFFCAP / λ ÷ measured RTORPA)

The keeper's LCAP window, protocol cap and (from 2023-11-01) OBDRR048 floor apply in every variant.

| Year | Keeper | + (a) | + (b) | (a)+(b) = the build |
|---|---|---|---|---|
| 2019 | 1.04 | 0.99 | 0.97 | **0.94** |
| 2020 | 1.45 | 1.26 | 0.94 | **0.84** |
| 2021 | 1.14 | 1.07 | 1.11 | **1.06** |
| 2022 | 1.08 | 0.92 | 1.00 | **0.86** |
| 2023 | 1.09 | 0.96 | 0.95 | **0.85** |
| 2024 | 0.90 | 0.84 | 0.85 | **0.81** |

- **The build reads below 1 in five of six years. That is the expected sign.** The curve is convex in reserves, and the formula is evaluated on hourly-mean reserves where ERCOT evaluates it per SCED interval (Jensen). The keeper's > 1 readings were compensating errors.
- **Not a fit.** On mean |log ratio| the build and the keeper tie (0.135 each). The case is the published formula and the published values (rule 1), not the score.

## 3. The change

`ScenarioConfig.ercot_ordc_published_curve` (default off; ERCOT-gated; backcast-only; zero DOF):
- `results.scarcity.resolve_lolp_params(config, T, year=)` returns the hourly published values, with μ unshifted so `lolp(..., S)` lands on the published μs.
- It refuses forecast mode and `ordc_lolp_params_path` (one μ/σ source, rule 19).
- `ordc_adder` and `ercot_ordc_demand_steps` gain `obd_half_shift`. With hourly μ/σ, the demand steps use one reserve grid topped at the year's largest `mcl + μs + 5σ`, and return `(n_steps, T)` penalties. Widths and requirement stay static.
- `model.reserves.spec._ercot_ordc_curve` feeds both ERCOT co-opt families (the single-product family and the multiproduct ORDC-total family).
- `build_reserve_dispatch_kwargs` promotes hourly penalties, following the NYISO hourly-widths precedent. `lp.costs.build_cost_vector` accepts `(n_ordc_steps, T)`; the R-23 SWCAP hour scale multiplies it.
- Off, the code is byte-identical: the scalar path is unchanged and the field is dropped from the cache key at default.
- **Tests:** `tests/unit/pipeline/test_ercot_ordc_published_curve.py`.

## 4. G-DRIFT and solve set

- **G-DRIFT `651723e3..main` (fe07b594): all INERT.**
  - 133 changed `src`/runner files are AST-identical modulo docstrings and comments (the cleanup-C path rewrites).
  - The 14 AST-changed files are:
    - path strings in messages;
    - SOCO-only FERC-714 additions;
    - the default-off PJM `cc_mustrun_conduct_window`, whose `arrays.py` branch runs only when armed;
    - parity-registry declarations and a probe-records path in `scripts/lib`.
  - Data drift covers only NYISO benchmark entries, NEISO/PJM/SOCO artifacts and committed eGRID sheet mirrors (cache copies of the same xlsx).
- **Solve set (rule 36):** all seven years, one shard each, at the pinned SHA. The build moves every year's curve, so no leg is reused.
- **Shard command:** `replay_keeper.py results/calibration/r_ercot23_span --years <Y> --set ercot_ordc_published_curve=true`. Each year's partition overlay (the 2023 carve-out included) comes from the bundle, so the recipe is otherwise unchanged.

## 5. Predictions (fixed before any solve)

Zero LP on the keeper. Each hour's cleared ORDC-total reserve level is re-priced on the new curve, with λ and dispatch held. The ranges allow for re-dispatch.

| Year | ORDC adder LW $/MWh (keeper → pred; measured RTORPA) | LW $/MWh | C3a | h > $1k | h > $200 | ΔLW by band (< $100 / $100–1k / > $1k) | Determination |
|---|---|---|---|---|---|---|---|
| 2019 | 10.92 → **10.0–10.7** (9.63) | 49.81 → **49.0–49.6** | +7.0 → **+5.3 to +6.6 %** | 30 → 27–30 | 100 → 88–98 | −0.24 / −0.58 / +0.29 | NOT-YET (=) |
| 2020 | 3.17 → **1.9–2.6** (2.64) | 26.73 → **25.5–26.2** | +5.2 → **+0.4 to +3.1 %** | 3 → 1–3 | 38 → 22–32 | −0.24 / −0.62 / −0.07 | NOT-YET (=) |
| 2021 | 26.73 → **26.0–26.5** | 167.58 → **166.6–167.4** | +1.0 → **+0.4 to +0.9 %** | 113 → 110–113 | 653 → 645–653 | −0.03 / −0.23 / −0.30 | CALIBRATED (=) |
| 2022 | 6.46 → **6.0–6.4** (6.87) | 68.07 → **67.5–67.95** | −9.3 → **−9.5 to −10.1 %** | 17 → 13–17 | 96 → 90–96 | −0.01 / −0.31 / +0.03 | NOT-YET (=) |
| 2023 hold | 2.64 → **2.3–2.6** (1.27) | 49.28 → **49.0–49.25** | −24.2 → **−24.3 to −24.6 %** | 34 → 30–34 | 140 → 136–140 | −0.01 / −0.09 / −0.09 | NOT-YET (=) |
| 2024 | 0.34 → **0.30–0.34** (0.24) | 27.72 → **27.65–27.72** | −11.1 → **−11.1 to −11.3 %** | 0 | 12 → 10–12 | −0.01 / −0.02 / 0 | NOT-YET (=) |
| 2025 | 0.00 → **0.00** | 33.13 ± 0.05 | −9.2 ± 0.15 % | 0 | 0 | ≈ 0 | CALIBRATED (=) |

- **C1 / C8:** each class moves at most ±0.3 TWh. C8 ST_GAS moves at most ±1 pp.
- **C3b:** 2019 and 2020 fall by at most 0.02, in the band where the adder drops. Both stay FAIL. Other years change by at most ±0.01.
- **Slack:** 2021 stays 3,194 ± 50 MWh (Uri, HCAP hours). It is 0 in every other year.
- **Disclosed risk:** 2022 C3a sits at the ±10 % edge. A crossing adds a second failed criterion to a year that is already NOT-YET on C1. The determination does not change.
- **ISO:** NOT-YET (=).

## 6. Promotion rule

- **Promote** under the owner's standing instruction if both hold:
  - the ORDC adder moves toward measured RTORPA in 2019, 2020, 2022, 2023 and 2024;
  - no year's determination worsens.
- This holds even if 2022 C3a crosses −10 %. The change is structural (rule 1), and that year is already NOT-YET.
- **Stop and put it to the owner** in either case:
  - 2021 or 2025 leaves CALIBRATED;
  - any year's adder moves away from measured.
