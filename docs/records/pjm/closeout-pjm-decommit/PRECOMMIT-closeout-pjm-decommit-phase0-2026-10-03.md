# PRECOMMIT — closeout-PJM-decommit phase 0: a decommitment mechanism for PJM coal (ZERO LP)

Lane: closeout-PJM-decommit (branch `claude/closeout-pjm-decommit`, cut from `6277de60`). Chartered by the
backcast close-out desk on **owner ruling R-55** (2026-10-03, verbatim): *"Find a mechanism to get it to
decommit."* Keeper under test: `2026-10-03-closeout-pjm-nuc-keeper` (bundle
`results/calibration/closeout_pjm_nuc_full_span`, merged #7152). Phase 0 is zero LP; this file fixes every
reading before any number is computed. Probe (written after this commit):
`scripts/probes/_closeoutpjm_decommit_reach.py` → `results/phase0/pjm/_closeoutpjm_decommit_reach.json`.

## 0. What already floors and prices COAL_BIT (rule 28 check, D-2 enumeration, rule 19)

| Mechanism (PJM.js cell) | Verdict | Role on COAL_BIT |
|---|---|---|
| `coal_mustrun_per_plant` / `coal_mustrun_online_pmin` | K | must-run tranche (`_mustrun`, offered near VOM) — a floor |
| `coal_sync_srmc_tranche` + `coal_sync_window_commitment_grain` | K | synchronization tranche (`_sync`) at day grain — a floor |
| `tranche_startup_amortization` | K | start-up cost amortized into the P1 econ/peak bids |
| `offer_curve_by_group["COAL_BIT"]`, `coal_passthrough_sigmoids`, `pjm_offer_midcurve_conditional` | K | the incremental offer surface (NEXT-34: 3–9 $/MWh below measured going cost, as PJM's own offers are) |
| `committed_band_measured_basis` | R | not re-tested |
| `online_capacity_envelope` (PJM leg: `pjm_commitment_posture`, merchant gas on the pergen pool) | R | gas posture rejected (online headroom 2.66–3.14× measured); never applied to coal |
| `coal_committed_nested_on_mustrun` | U | candidate (b1) |
| `commitment_floor_window_netload` | U | candidate (b2) |

Censuses already on file (no re-test): NEXT-32 (commitment; floors hold 9 % of the model-runs-freed MWh `X`, the
price clears 92 %), NEXT-33 (price; at **zonal** grain the keeper price in the real dark spells is within
+0.3/+1.9/+1.2 $/MWh of real DA in 2019–21 — NEXT-32's "price above real" was a system-price artefact), NEXT-34
(offer; the keeper and PJM's own offers sit below the plant's measured average going cost `G`, and real darkness is
cost-consistent at `G` on 0.54–0.86 of the dark weight).

**What is new here.** No record has asked what the LP would do if a coal plant carried a *commitment state with
its measured no-load cost*. Real PJM coal offers incremental energy below its average cost (NEXT-34) and is still
dark when the price sits below `G`: that is the three-part-offer commitment calculus (incremental offer +
no-load + start-up, PJM Manual 11 §2.3), which a tranche LP cannot represent. The existing posture family
(start-up + min-load + min-down, no no-load) cannot reduce a price-cleared plant's output by construction:
without a cost on being online, any hour with price ≥ offer has non-negative margin and staying on is never
worse than leaving. This phase measures both forms.

## 1. Candidates and their measured parameters (zero fitted)

- **(a0) Friction posture on coal** — the existing family form on coal pools: online column `U`, start-up `SU` at
  `BIN_STARTUP_COST_PER_MW["COAL_BIT"]` = 100 $/MW, min-down `COAL_BIN_MIN_DOWN_HOURS` = 16 h, measured min-load.
  Replaces the coal `_mustrun` + `_sync` floors (rule 19); those MW become priced at the plant's own `committed`
  tranche offer.
- **(a1) Three-part coal commitment** — (a0) plus a **measured no-load cost** on `U`: per plant-year, the CAMPD
  unit-hour regression `heatInput = a_u + b_u · grossLoad` over full online hours (`opTime == 1`,
  `grossLoad > 0`), `NL_p = Σ_u a_u` (MMBtu/h), charged per online MW as `NL_p / Σ_u peak_u` × the plant's own
  EIA-923 monthly delivered coal price (`eia923_monthly_fuel_costs.parquet`, fuel group Coal; missing month →
  plant-year mean → PJM coal state-month mean). Rule 13: a machine heat-input intercept and a delivered fuel
  price both regenerate from forward drivers.
- **(a1-real)** — (a1) evaluated at the real zonal DA instead of the keeper price. Diagnostic only (answers (c)).
- **(b1) `coal_committed_nested_on_mustrun`** — committed band nested on must-run (`thermal_tranches_PJM.csv`
  measured rows); the removed MW move from the `committed` to the cheapest `econc` offer.
- **(b2) `commitment_floor_window_netload`** — re-windows the sync floor by net load. Its reach ceiling is the
  floor MWh that sits in real-dark hours (relocating a floor cannot remove more than that).

Min-load for (a0)/(a1): the plant's measured `committed_pct` from `thermal_tranches_PJM.csv` (P5 of online-hour
CF) × available capacity; plants without a row use the PJM keeper's own floor share (`_mustrun` + `_sync` +
`_committed` cap over plant cap). Min-up: none (no cited coal min-up constant exists; omitting it can only
increase reach).

## 2. Reach method (static, price-taker — an UPPER bound)

Per keeper COAL_BIT plant and year, from `unit_marginal_<y>` (P1 tranche `mw`, `cap_mw`, `mc`) and the plant's
keeper zone price (`system_<y>`): an exact two-state dynamic programme over 8,760 h (on / off with an off-age
counter to 16 h) maximizing Σ_t [Σ_tr (p − mc_tr)·x_tr − NL·A_t] − startup·A_t·1{start}, where `A_t` is the
plant's keeper available capacity, tranches load cheapest-first when `mc ≤ p`, and an online plant generates at
least `mlf·A_t`. Initial state: online. Output `mw_dp`; the decommitted energy is `Δ = mw_keeper − mw_dp`.

**Re-clear (side effects, static).** Per hour, the system net `ΣΔ` is re-supplied from the keeper's non-coal-BIT
units with spare headroom (`cap_mw − mw`) in ascending `mc` from the hour's price (zones pooled, no
transmission); the last unit used sets the re-cleared price `p'` for every zone that hour (shifted by
`p' − p_sys`). Gives the per-class C1 reallocation and the C3a/C3b shift. Prices are held at the keeper's in the
DP, so the reach ignores the price rise its own decommitment causes: every bar below is read on this upper bound,
and a candidate that fails on the upper bound is dead.

**Real dark.** A COAL_BIT plant-hour's real dark MW = `K*·Σ_u w_u·1{opTime_u = 0}` (NEXT-32 weights, all dark
hours, covered or not).

## 3. Bars (fixed ex ante)

- **B0 MEASURED BASIS (a1).** The no-load regression is identified: intercept `a_u > 0` on ≥ 0.8 of unit-years by
  capacity, capacity-weighted median R² ≥ 0.9, and implied full-load average HR within 8–14 MMBtu/MWh. Else (a1)
  has no measured basis and is not chartered.
- **B1 REACH.** COAL_BIT decommitted energy `ΣΔ⁺` (static) ≥ 0.5 × the excess over the band edge in each of 2019,
  2020, 2021: ≥ 5.87 / 2.37 / 4.36 TWh (keeper +19.73 / +12.74 / +16.72 vs ±8.00).
- **B2 NO C1 PASS→FAIL 2022–25** (and none in 2019–21 for any other class): after the re-clear, every class-year
  that PASSes now stays inside its ±8.00 TWh band (2022: COAL_BIT ≥ −8; CC_REGULAR 2022 is already FAIL and may
  not worsen by more than 1 TWh). 2025 is unscored (preliminary EIA-923) and reported only.
- **B3 PRICE.** No C3a or C3b PASS→FAIL in any year: C3a model mean shifted by the re-clear's load-weighted
  Δp stays within ±10 % (2020 has the least room: +9.0 % today), C3b (monthly NRMSE) shifted by the re-clear
  delta stays ≤ 0.20.
- **B4 WHERE.** ≥ 0.6 of `ΣΔ⁺` (2019–21 pooled, and in each of those years) lands in real-dark plant-hours
  (`min(Δ⁺, real dark MW)`).
- **B5 DIRECTION (a0 only).** (a0) is reported, and is expected to read `ΣΔ⁺ ≈ 0` with `ΣΔ⁻ > 0` (it adds
  min-load energy through troughs). If (a0) clears B1–B4 the expectation is refuted and that is reported.

**Verdict.** A candidate is CHARTERED (build default-off, PJM-scoped, `--no-` flag, tests, 7 shards) iff it
clears B0 (a1 only), B1, B2, B3 and B4. Otherwise NOT CHARTERED with the reach table. (c) is answered from
(a1) vs (a1-real) and the NEXT-33 setter census: if (a1-real) clears B1 and (a1) does not, the price is the
carrier and is named; if both clear, the missing operand is the commitment cost, not the price.

## 4. What a charter would cost (stated now)

(a1): `src` change — a coal leg of the posture family (`_build_posture_energy_rows`) with a no-load cost on `U`
(`model/lp/costs.py`), PJM-scoped ScenarioConfig field `pjm_coal_three_part_commitment` (default off,
`--no-` flag), replacing the coal `_mustrun`/`_sync` floors when armed (rule 19), the P1 start-up amortization
zeroed on postured coal (as `zero_posture_markup` does for SPP gas), a matrix row plus a cell in every shard
(`check_mechanism_matrix.py`), fast-lane tests, then 7 shards. (b1)/(b2): no src change (existing fields), a
recipe `--set` and 7 shards.
