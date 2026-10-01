# PRECOMMIT — R-CAISO-13 (2026-09-28): `caiso_eia930_clock_repair`

Owner decision card, 2026-09-28: "Build + solve now".
Keeper: `2026-09-28-caiso-r11-tacpst` (bundle `rcaiso11_A_span`, 2022–25).
Fold: `2026-09-28-caiso-r11-tacpst-touchpoints` (bundle `rcaiso11_A_tp_2019_2021`).

## 1. The defect (zero LP; probe `scripts/probes/_rcaiso13_storage_timing.py`)

**Clock of the measured battery series.** CAISO Outlook "Total batteries" is stamped in Pacific prevailing time. `build_storage_dispatch_actuals.py` converts it prevailing → UTC → fixed PST, hour-beginning. That is the model's clock, so the measured series was already on the right clock.

**The model is on the wrong clock.** The EIA-930 CISO extract is published one hour LATE in two windows. The windows are given as hour-ending `UTC time` stamps; the constant is `EIA930_CISO_CLOCK_LATE_WINDOWS_UTC`.

| Column family | Late window | Evidence |
|---|---|---|
| Generation, `NG:*`, interchange | 2023-11-01 08:00 → 2025-12-02 22:00 | Best lag of d(NetGen−TI) vs d(OASIS TAC) = +1 in every month of the window and 0 outside it. `NG: SUN` centroid is 12.5–13.0 h PST in every month of the window, against 11.6–11.9 outside it (solar noon ≈ 12.0) |
| Demand | 2022-06-16 08:00 → 2025-12-02 22:00 | Best lag of d(Demand) vs d(TAC) = +1, r 0.96–0.999 in every month. The hour-level scan pins the end at 2025-12-02 22:00Z. 06-14/15 are mixed, so the window starts at 06-16 |

- The EIA API long series is byte-identical to the extract, so the defect is EIA's, not the download's.
- caiso-75 used the generation frame as its reference clock. It therefore saw only the *relative* lag: Demand late Jan–Oct 2023, and "aligned" afterwards, when in fact both series were late.

**Keeper symptoms:**
- Its own dispatched solar centroid is 12.9 h PST in 2024–25, against ~11.9 in 2022–23.
- Battery net-profile correlation with Outlook, lag 0 → +1: 0.921 → 0.993 (2024) and 0.909 → 0.996 (2025). In 2023 the best lag is 0 (0.955).

**Not the clock (reported, no lever).** The evening ramp-peak gap:
- 2023 has the largest gap and no generation-frame defect.
- The LP identity holds: across interior-discharge hours the price spread has a median of $1.8–11.4/MWh, over a median of 6–9 such hours per day. Storage sets the plateau, and no SOC or power bound binds.
- Daily h18–22 price CV: model 0.006–0.057 vs DAM 0.034–0.134.
- All remaining storage levers are on the handoff's do-not-redo list.

## 2. The arm

`caiso_eia930_clock_repair=true` (new, gated, default off, CAISO-only, zero parameters).
- **Frame seam** (`frames._repair_clock_late_windows` inside `_repair_published_extract`): every CISO reader sees the true hour.
- **caiso-80 supply-consistent artifact:** its EIA-930 term (NetGen − NG_cell − TI) is moved the same way. The CEMS and flat terms are untouched.
- **`caiso_demand_clock_realign`:** superseded (rule 19).

Arm liveness, rows changed (Demand / NG: SUN / SC demand):

| Year | Rows changed |
|---|---|
| 2019–21 | 0 / 0 / 0 |
| 2022 | 4776 / 0 / 0 |
| 2023 | 8752 / 1140 / 1465 |
| 2024 | 8758 / 7666 / 8755 |
| 2025 | 8049 / 6943 / 8051 |

2019–22 are expected to be inert in the LP. They are solved anyway, because the keeper carries every year (rules 34(c), 35(c)).

**G-DRIFT** (tree diff keeper solve sha `9005dc81` → `origin/main` `14c1d70e`, solve paths). Every hunk is INERT for CAISO:
- `pjm_da_virtual_settle_financial`: flag default off, PJM-only.
- SPP-98 `CAMPD_UNIT_PLANT_REMAP` rows: SPP ORIS only.
- soco-83 plant partition: inert with `st_gas_mustrun_per_plant` off.
- `ferc714.load_ferc714_system_lambda`: not on the CAISO path.
- `virtual_bids.settle_virtuals_financially`: PJM flag.
- `scripts/lib/seam_neighbour_price/*`: NEISO/NYISO/PJM/IESO.
- `data/raw`: NEISO/NYISO files only.

The keeper's committed bundle is the control (rule 29(b)).

## 3. Pre-registered predictions and decision rule (fixed before any solve)

- **P1.** 2024–25 model solar centroid moves to 11.5–12.0 h PST in every month.
- **P2.** 2024–25 battery net-profile best lag vs Outlook moves from +1 to 0.
- **P3.** The 2024–25 SP15 Jun–Sep price peak hour moves earlier by about 1 h (model 19 → 18 in 2024).
- **P4.** 2019–22 are byte-identical to their keeper legs in class TWh and price, to within solver noise (|Δ| < 0.01 TWh).
- **P5.** No prediction on C1–C4 levels. They are reported at full magnitude.

**Decision.** Promote if 2022–25 stays CALIBRATED, on structure (rule 14), whatever the residual does (rule 1). If the determination drops, that is a trade the owner decides: it goes to a decision card and is not taken in-session.

## 4. Solve

- Recipe: keeper recipe + `--set caiso_eia930_clock_repair=true`.
- One shard per year, 2019–2025 (rule 36), at the pinned SHA of this PRECOMMIT's commit.
- Shard prompt: `docs/records/caiso/r-caiso-13/shard-prompt.md`.
- `{SRC}`: `rcaiso11_A_tp_2019_2021` (2019–21), `rcaiso11_A_span` (2022–25).
- `{SDCAP}`: 1436.0 (2019–23), 2074.0 (2024), 2071.0 (2025).
