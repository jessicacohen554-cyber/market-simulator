# FINDING — why the clean UC (uc-1.5) under-commits gas at peak (UC-DIAG, zero LP)

**Lane:** UC-DIAG · **Chartered by:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-diag-undercommit` off `main` `d99bf94d` (pin `302043c3` + #7248 SPP UC-3 RESULT, records only).
**LP in this lane:** zero. No `src/` change, no solve, nothing registered.
**Evidence:** committed bundles only:
- SPP UC-3 arms A/B (`docs/records/spp/ucmilp/data/ucmilp3_spp_{a,b}_span`, uc-1.5);
- CAISO, NYISO and NEISO UC-3 spans (uc-1.4, so **defect 7 is present**, which biases them against commitment; read their shape only);
- MISO UC-2 span;
- keeper bundles `results/calibration/closeout_{spp_nuc,caiso_w1_a2}_span`;
- EIA-930 `data/raw/eia-930-hourly/`.

Readings and scripts are in `data/diag/`.

**Correction to the charter premise:** the SPP −600 to −1,400 MW peak de-commitment is **arm B** (floors off; RESULT-ucmilp3-spp §3). Arm A holds about 0.9 GW of ST_GAS headroom through its floors.

## 0. Ranked causes

| # | cause | verdict | size at peak (top-100 load hours) | fix (rules 1, 13, 19) | kind |
|---|---|---|---|---|---|
| 1 | **No reserve need tied to commitment `u`.** SPP and CAISO UC runs carry **no reserves at all** (`energy_reserve_coopt=false` in every `run_config`). Where reserves are armed (NYISO, NEISO, ERCOT, MISO 2019–21), the headroom row's right-hand side is `pmax·a` (`reserve_rows.py:193, 808`), so a cluster at `u=0` still counts as full reserve. Only MISO 2023–25 is P-gated (ρ 0.176). | **Real structural gap; primary** | SPP arm B 2020: committed slow headroom is CC **0**, ST_GAS 14 and coal 429 MW, about **0.44 GW** in total. The SPP spin floor is about 0.7 GW (50 % of the RSG contingency reserve, 0.964 × 1.2 × MSSC; MSSC ≈ 1.2 GW is inferred, not computed from the fleet). Regulation-up is not modelled at all. So the gap is **≥ 0.3 GW of spin alone**. NEISO 2023: 0.08 GW committed against a 0.6 GW 10-min spin, a gap of about 0.5 GW. NYISO 2023: 0.93 GW committed against 0.655 GW spin, so roughly no gap. CAISO 2023: 0.65 GW committed against about 1.4 GW spin, but about 4.4 GW of idle battery power at peak would cover it, so roughly no gap. | Engine change: inside the window, add a **u-gated synchronized-headroom row** per reserve family, `Σ_c (p̄·a·u_c − ΣP_c) + storage room + online-CT room ≥ spin/reg requirement`. Use the requirement the ISO's existing reserve spec already defines (SPP RSG, CAISO max(MSSC, 6 % load), NYISO/NEISO RCPF), so nothing new is tuned. Config change: arm `energy_reserve_coopt` for SPP and CAISO in the UC arm; that is its own PRECOMMIT. Rule 19: this replaces nothing. The window refuses posture pools, so nothing is stacked. | engine + config |
| 2 | **Perfect foresight.** The UC commits on realized load, while real DA/RUC commits on the forecast. Measured EIA-930 BA day-ahead forecast minus actual at the top-100 load hours (median): **SPP +0.8 to +1.3 GW** (2019–22), +0.17 (2023), −0.63 (2024). **MISO +1.9 / +5.5 GW** (2024 / 2023). CAISO +0.1 to +1.3 (2020); NEISO about 0; ERCOT about 0; NYISO −0.6 GW (under-forecast). | **Real; co-primary for SPP and MISO; absent for CAISO, NEISO and ERCOT** | SPP 2019–22: the forecast exceeds load at peak by about as much as the de-commitment (0.6–1.4 GW). Causes 1 and 2 together come to about 1.1–1.7 GW, enough to cover the SPP gap. | Engine change: the window takes a **commitment demand** separate from the P1 demand. Backcast: the measured DF series. `curate_load.py` already writes `load_forecast_mw`, and nothing reads it. Forward: realized load plus the measured multi-year DF bias by hour of day and season. Owner ruling needed on rule 13: the backcast series is a year-specific overlay, like outage windows, and the forward analog is the error distribution. EIA-930 DF is the BA's own forecast, not the DA-cleared or RUC load. NEISO DA bids exist only via the fetcher; they are not on disk. | engine + data |
| 3 | **Min-up `ut_h` is measured on the plant and applied per unit.** It is p25 of on-runs where any unit is on (`scripts/lib/uc_params/__init__.py:220-224`; `params.py:423`), has no cap, and is an *economic* run length used as a *physical* bound. Cap-weighted medians: SPP CC 18 h, ST_GAS 55 h, coal 57 h; NYISO CC 19 h; CAISO CC 13 h. Tails run to hundreds or thousands of hours. | **Real data defect; explains the start ratio, not peak MW** | Offline share at peak **does not rise with `ut_h`**: SPP ST_GAS is 78 / 99 / 95 / 79 % offline in the ≤ 8 / 9–24 / 25–72 / > 72 h bins; CAISO ST_GAS with `ut ≤ 8 h` is 82 % offline. It does suppress cycling, which matches CC starts at 0.46–0.89× CEMS. | Data change: derive `ut_h` from CAMPD **unit**-level runs, or use the published class min-up (rule 18: physics by parameter), with p25 of observed runs kept only as a diagnostic upper bound. Rule 23: this is a derivation-defect fix, not a residual fit, and the commit cites the defect. Owner confirmation needed. | data |
| 4 | **Ruling (a): non-integer gas capacity.** | **Not a cause** | Non-integer share of available capacity at peak: SPP CC 20 %, ST_GAS 19 %, coal 9 %; CAISO CC 9 %, ST_GAS 0 %. SPP has no all-budget-pinned cluster. Non-integer capacity stays at `pmax·a`, so it is always available. The deficit sits entirely in integer ST_GAS and CC. | none | — |
| 5 | **Window horizon** (24 h kept + 12 h look-ahead, windows at local hour 0). | **Not a cause** | Evening-peak starts land at hours 12–17, inside the kept window, and the look-ahead reaches noon of the next day. There is a small churn at the edge, hour 0: SPP 49 starts / 96 stops per year, against 3 / 179 at hour 23. That is at midnight, not at peak. | none (optional: report hour-0 churn in the solve log) | — |
| 6a | **Cost parity of ST_GAS and CT.** In SPP the CT P1 bid matches the ST_GAS incremental cost at peak: median $28.2 vs $28.9/MWh (2020) and $80.3 vs $84.7 (2022). Offline ST_GAS earns a mean of only $1.8/MWh above its mc at peak. With perfect foresight and no reserves, a ST_GAS start never covers its start plus no-load, so CTs set the price 0.24 → 0.42–0.51 of the time. | **Mechanism, not a defect.** This is why causes 1 and 2 decide ST_GAS. | — | none; the fix is causes 1 and 2 |
| 6b | **CAISO midday decommitment.** CC/ST online falls from 6.4 GW at hour 0 to 3.2 GW at hours 10–11, then returns to 7.2 GW at hours 18–20. Stops peak at hours 7–8 and starts at hours 15–17. | **Plausible; not quantified** | Real CAISO holds CCs through the solar trough for evening ramp uncertainty (flexible ramp up / FRP). The model has no ramp-uncertainty requirement, and no measured FRU series is on disk. | Engine plus data: a u-gated ramp-capability requirement from the published FRU requirement. Needs an intake first. | engine + data |
| 6c | **Row (a) uses the cluster-mean availability `a`** (`params.py:156`). With a whole-unit outage, each committed unit carries only `p̄·a`, which biases against committing a partially outaged plant. | Real, minor, not quantified | — | Engine change: bound by the online units' own availability. Low priority. | engine |

## 1. Readings (top-100 load hours, P1)

| bundle | committed CC / ST_GAS / coal online (GW) | synchronized headroom on committed (MW) | keeper dispatch → arm dispatch, ST_GAS (GW) |
|---|---|---|---|
| SPP B 2020 | 8.23 / 1.27 / 16.31 | 0 / 5 / 418 | 4.51 → 1.38 |
| SPP A 2020 | 8.19 / 3.03 / 15.71 | 0 / 732 / 532 | 4.51 → 2.97 |
| SPP B 2022 | 8.56 / 1.58 / 18.61 | 0 / 4 / 0 | — |
| CAISO 2023 (uc-1.4) | 11.77 / 0.64 / — | 142 / 417 / — | 0.17 → 0.22 |
| NYISO 2023 (uc-1.4) | 5.67 / 5.96 / — | 169 / 762 / — | — |
| NEISO 2023 (uc-1.4) | 7.05 / 0.00 / — | 82 / 0 / — | — |
| MISO 2024 (UC-2) | 24.48 / 5.24 / coal continuous | 483 / 298 / (coal 3,470, `pmax·a`) | — |

In the clean SPP arm, every committed CC MW is dispatched at peak. All upward room sits on CTs that are not running, and the model counts that room because it reads `pmax·a`. That is what the missing u-gated reserve looks like in the output.

## 2. What to do next (desk)

1. **UC-FIX-6 (engine, Opus/Fable):** add the u-gated synchronized-headroom row in `model/uc/window.py`. Its requirement comes from the existing `model/reserves/spec.py` families. Unit tests: 1 generator, 1 zone, 24 h; a requirement that forces a second unit online.
2. **Config arm (PRECOMMIT):** SPP and CAISO UC arms with `energy_reserve_coopt` on. NYISO and NEISO already carry reserves and gain only the u-gate.
3. **Commitment demand from DF (engine + owner ruling on rule 13):** SPP and MISO first, where the measured bias is large. Not needed for CAISO, NEISO or ERCOT. It would go the wrong way for NYISO.
4. **`ut_h` re-derivation (data, owner confirmation under rule 23):** unit-basis runs or the class table. This targets the start ratio.

## 3. Caveats

- CAISO, NYISO and NEISO bundles are uc-1.4 (defect 7), so their committed MW is biased low. Read them for shape, not level.
- SPP MSSC is inferred (≈ 1.2 GW; one unit ≥ 600 MW nameplate × availability), not recomputed from the fleet.
- EIA-930 DF is BA-level; rows off by more than 30 % are dropped as data errors (SPP 2019–21: 12–45 h).
