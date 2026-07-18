# CAISO CT_PEAKER net-load-drag reliability floor

*2026-06-27 — Step 2 (Lever B) of the CAISO shape-first calibration overhaul
(`docs/caiso-lever-audit-2026-06.md`). Replaces the temperature/TMAX floor in
`docs/caiso-ct-reliability-floor-2026-06.md`. Companion to the ERCOT net-load
drag (`docs/ercot-ct-netload-drag-2026-06.md`).*

## What changed and why

The audit confirmed the CAISO CT_PEAKER local-RA floor was **the right idea with
the wrong shape**. The old `inject_caiso_ct_reliability_floor` floored CT_PEAKER
over h15-22 at `clip(0.049 + 0.047·(TMAX−25), 0.049, 0.46) × capacity`. Because
TMAX is a *daily constant*, the floor was constant across the whole evening
window — a **flat ~771 MW rectangle** — and its `0.049` baseline (the cool-day
median CF) bound 61 % of binding hours. That baseline is a level target tuned to
a CF, which CLAUDE.md #1 forbids, and it destroys the diurnal shape: the real
CT_PEAKER fleet runs a **sharp evening-ramp triangle peaking at h18-19**, not a
rectangle.

The fix is to key the same local-RA commitment to system **net-load**
(`load − wind − solar`) instead of TMAX. Net-load *varies within the day* — it
peaks in the evening ramp as solar collapses — so a floor proportional to it
**rises through the afternoon and peaks in the evening**, reproducing the shape a
flat band cannot. This is the identical mechanism already validated on ERCOT
(`fleet.apply_ct_netload_drag_floor`): a min-gen floor
`clip(slope·netGW + intercept, 0, cap) × available CT_PEAKER capacity`, gated to
the afternoon-evening ramp window `[15, 22)` (h15-21 local-standard), composed
with any existing floor via `maximum`, dispatched economically above. Both the
trigger (net-load) and the magnitude (a physical min-gen) are forward-derivable
and condition-responsive, so it is admissible in backcast **and** forecast
(CLAUDE.md #10/#11) — explicitly **not** the measured-actuals
`ct_mustrun_per_plant` pin.

## CAISO coefficients (re-regressed — not ERCOT's)

`scripts/data/derive_caiso_ct_reliability_floor.py` regresses the measured CAMPD
CT_PEAKER **evening** (h15-21 local-standard) capacity factor on EIA-930 `CISO`
net-load, 2023-2025, time-aligned to the model's naive local-standard 8760-hour
clock:

* CT_PEAKER measured = CA CAMPD `grossLoad` for units the canonical
  `classify_plant` EIA-923 dominant-class map routes to CT_PEAKER (after the
  AES/HB split remap) — the same class the dispatch fleet uses.
* CF denominator = the **model** CT_PEAKER nameplate (7.62 GW, `load_fleet_from_
  csv`), so the fraction reproduces the right MW when applied to the model fleet.
* net-load = EIA-930 `CISO` `Demand − NG:SUN − NG:WND`, UTC−8 (PST, no DST).

Pooled median-per-2-GW-bin least-squares line on the evening block, capped at the
95th-percentile evening CF:

```
frac = clip(0.00901·netGW − 0.1124, 0, 0.36)   ramp window [15, 22)
       zero-crossing 12.5 GW   cap 0.36 (hottest-ramp ceiling)
```

These become the CAISO `ScenarioConfig` defaults in
`run_calibration._calibration_config` (do **not** reuse ERCOT's
`0.00703 / −0.1427 / 0.47`). Non-CAISO ISOs keep the ERCOT field defaults
(byte-identical).

## Config

`_calibration_config` (CAISO only; byte-identical for every other ISO):

| field | old (TMAX keeper) | new (net-load drag) |
|---|---|---|
| `caiso_ct_reliability_floor` | `True` | **`False`** (re-armable via `--caiso-ct-reliability-floor`) |
| `caiso_ct_floor_base` | `0.049` | **`0.0`** |
| `ct_netload_drag` | `False` | **`True`** |
| `ct_drag_slope_per_gw` | 0.00703 (ERCOT) | **0.00901** |
| `ct_drag_intercept` | −0.1427 (ERCOT) | **−0.1124** |
| `ct_drag_cap` | 0.47 (ERCOT) | **0.36** |
| `ct_drag_ramp_start / _end` | 15 / 22 | 15 / 22 (unchanged) |

Integration note: CAISO runs `plant_level_fleet` (no CAMPD bins) and does **not**
set `gas_offer_curve`, so each CT_PEAKER plant is a single non-`_peak` LP unit.
`apply_ct_netload_drag_floor` therefore targets the whole CT_PEAKER fleet and
distributes the per-hour target cheapest-first — the convention the other floors
use; no fleet-split adaptation was needed.

## Shape deltas (acceptance gate — `scripts/caiso_shape_probe.py`, P1)

Both runs solved per-plant multi-zone 2023·2024·2025 on the **same**
curtailment-fixed base (after the Lever D solar-deliverability merge), keeper
flags `--priced-interchange --negative-renewable-offers --caiso-import-gas-
coupling --caiso-per-hub-intertie --caiso-corridor-flow-limit
--gas-hub-basis-overlay`. Metrics are hourly Pearson *r* and the diurnal band,
never MAE.

**CT_PEAKER hourly r and annual TWh (model / measured):**

| year | r base→new | TWh base→new (meas) | band× base→new |
|---|---|---|---|
| 2023 | 0.68 → **0.73** | 1.92 → 1.55 (3.08) | 0.77 → 0.63 |
| 2024 | 0.67 → **0.70** | 2.32 → 1.53 (3.30) | 0.98 → 0.64 |
| 2025 | 0.45 → 0.44 | 1.87 → 1.06 (1.65) | 1.87 → 1.05 |

**CT_PEAKER diurnal MW by hour-of-day (baseline | new | CAMPD):**

```
2024   h15   h16   h17   h18   h19   h20   h21   h22
base   765   778   788   795   798   791   790   776   <- FLAT rectangle
new    133   229   459   709   867   852   798    83   <- rises to h19 evening peak
CAMPD  395   676   974  1077   974   758   537   367   <- sharp h18 peak

2023   h15   h16   h17   h18   h19   h20   h21   h22
base   653   653   656   657   657   656   656   654   <- FLAT rectangle
new    141   296   581   792   832   807   759    36   <- rises to h19 evening peak
CAMPD  381   745  1166  1304  1123   815   459   250   <- sharp h18 peak
```

**Verdict against the acceptance criteria:**

* ✅ **Rectangle is gone.** The flat 653/765/636 MW band across h15-21 becomes a
  rising evening ramp that **peaks h18-19** like CAMPD (2023/2024 peak h19; 2025
  peaks late h20-21 with a small fleet).
* ✅ **Hourly r rises above 0.67** for 2023 (0.68→0.73) and 2024 (0.67→0.70).
  2025 is unchanged-low (0.45→0.44) — both regimes; the 2025 CT fleet is tiny and
  noisy.
* ✅ **Old flat floor is zero-bind.** The new dispatch sits *far below* the old
  653/765 MW floor at h15-17 (141/133 vs 653/765), which is impossible if the old
  floor were active — confirming it is off.
* ✅ **Total under-runs (expected).** Model CT_PEAKER 1.5 vs measured ~3.1 TWh.
  This is the **evening-scarcity bug handed to Step 3** — peakers should clear
  inframarginally on merit in the ramp; the residual is **not** to be recovered by
  re-inflating a floor (CLAUDE.md #1/#11). The new floor over-floors the late
  ramp slightly (it tracks the net-load peak at h19-21, a touch later than the
  measured h18 CT peak) and drops at h22 (window ends [15,22)), both part of the
  same scarcity residual.

CC_REGULAR (the over-running counterpart) is unchanged in character: 1.1-1.4×
over with a too-flat midday, the larger structural item still open. Solar now
matches well (band× ~1.0) after the Lever D curtailment fix.

**Not a keeper.** Per the Step-2 brief, no dashboard run is registered yet — the
shape fix is structural groundwork; the under-run residual is Step 3's input.

## Re-derive

```
python scripts/data/derive_caiso_ct_reliability_floor.py            # 2023-2025
```

Reads the committed CAMPD (`data/raw/campd-unit-level/CA_*.parquet`) and EIA-930
(`data/raw/eia-930-hourly/CISO hourly.parquet`) archives; no network needed.
