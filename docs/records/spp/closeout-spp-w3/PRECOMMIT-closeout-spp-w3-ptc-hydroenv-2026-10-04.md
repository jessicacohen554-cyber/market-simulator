# PRECOMMIT — closeout-SPP-w3: `wind_ptc_vintage_offers` + `hydro_dispatch_envelope` on the SPP keeper (7 shards)

Pushed before any shard is launched. Evidence: `FINDING-closeout-spp-w3-phase0-2026-10-04.md`.

## 1. The arm

- **Recipe:** keeper `closeout_spp_nuc_span` (replay_keeper), plus `--set wind_ptc_vintage_offers=true --set
  hydro_dispatch_envelope=true`.
- **Fields:** both are existing default-off ScenarioConfig fields with matrix rows and cells, so there is no `src/`
  edit. Pin: a full SHA of this branch.
- **Shards:** one per year, 2019–2025 (rules 32/34/36).
- **G-DRIFT** (8c3ea461 → 90cea720, rule 29b): every hunk on the SPP backcast path is INERT.
  - The SPP solve-surface `moved` set is identical.
  - `measured_hydro_min_flow_level`, `measured_hydro_hourly_envelope` and `load_demand` were checked for SPP 2019–25 at
    both commits: identical arrays.
  - So there is no control solve. The keeper's committed bundle is the control.
- **Free parameters:** none new.
  - `HYDRO_ENVELOPE_PERCENTILE` is the existing constant.
  - The PTC table is the existing `WIND_PTC_STATUTORY_USD_PER_MWH`. Years 2019–22 fall back to the flat $26; the
    statutory 25/25/25/26 differs by ≤ $1 on a floor that binds in 0.3–8 % of hours. This is declared, not repaired.
- **Attribution (ex ante):** one combined arm.
  - The PTC part is computed exactly at zero LP: re-price the keeper's floor zone-hours.
  - The hydro part = arm − keeper − the PTC part.
  - Each cell gets its verdict from that split.

## 2. Bars (fixed now)

| id | bar | predicted (zero LP) |
|---|---|---|
| **T1 target** | C3a 2024 moves ≥ +1.2 pts (−11.2 → ≥ −10.0 %, FAIL→PASS) | +1.67 (PTC +1.04, hydro +0.62) |
| T2 | C3b 2024 falls (direction); a flip needs ≤ 0.200 | 0.216 → ~0.209 (flip **not** predicted) |
| T3 | C3a 2023/2025 move toward 0 | −6.4 → ~−4.7; −4.3 → ~−2.5 |
| **D1 declared PASS→FAIL** | **none predicted**. Every C1 record keeps its status: wind/solar/nuclear are pinned; hydro energy is conserved monthly; the hydro shift is about 2 TWh/yr between hours | — |
| D2 | C3a 2021 stays ≤ +10 % | +7.1 → ~+8.0 |
| D3 | 2019/2020 C3a/C3b worsen by ≤ 1.5 pts / 0.015 (already FAIL; declared) | +0.4 / +0.8 pts |
| C3a/C3b band | no train-year C3a moves away from 0 by > 1 pt; no C3b rises > 0.01 | — |

## 3. Kills (any one = cell verdicts from the split, no promotion request)

- **K1:** any record flips PASS→FAIL that D1–D3 did not declare.
- **K2:** C3a 2024 moves < +0.8 pts. The mechanism is not acting as described.
- **K3:** unserved energy above the keeper in any year, or a new D-4 row, or C6/C8 FAIL.
- **K4:** annual hydro energy differs from the keeper by > 0.5 % in any year (the budget must be conserved).
- **K5:** the wind-floor zone-hour count moves by > 25 % in any of 2021–25. The re-price would no longer be the
  mechanism.

## 4. Decision rule

- **T1 met and K1–K5 clear:** send the desk the scored flips and the promotion cost, and request the slot (no
  promotion here).
- **T1 missed and K1/K3 clear:** record both cells with the split, and take the next candidate (FINDING §2) or close
  the queue with reasons.
