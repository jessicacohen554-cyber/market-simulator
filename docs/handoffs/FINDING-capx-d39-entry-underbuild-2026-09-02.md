# FINDING — capx D39 (Phase-0): the entry stack under-builds through ONE term — the energy leg's DISPERSION, discarded by the zone-flat tail-free stack re-price five ISOs share — while the attribute leg is exact (every RPS ISO's REC dual sits at its ACP), the capacity leg errs through the POSITION (D28/D33/D31, not the signal), and every VRE volume is CAP-set, so the signal lane can move timing and storage, never the RPS volume

**Lane:** capx D39, Phase-0 (characterize cross-ISO; NO repair). Branch
`claude/capx-d39-entry-underbuild`. **Date:** 2026-09-02. **HEAD at launch:** `0a3d22c7`
(origin/main). **Charter:** director ledger `docs/handoffs/capx-director-ledger-2026-08.md`
§0y (r#28 "Named-queued: D39") — T16-A outcome B (the NEISO REC dual pinned at the $50 ACP
in all 50 arm-years) and D36 (the storage arbitrage leg short by $50–150/kW-yr in every
year) converge on one object: the entry stack under-builds against both the RPS
constraint and every external view. The chartered route is the
`entry_forward_expectation_signal` family — cross-ISO, every screen, not a storage lane and
not an RPS lane.

**Docs only. ZERO solves.** Every number below is read from a committed artifact (the
committed `screen_signal_diag_*.npz`-derived dual-replay artifacts, the diagnostics-on
evolution ledgers, the golden-2 bundle, the registered `run_config.json`s) or computed by
re-running the entry screens' own revenue formulas — `new_entry.py`'s price-duration
integral and CF capture, `storage.py::estimate_storage_revenue` line for line — on the six
ISO keepers' committed hourly sidecars (`results/calibration/<keeper>/hourly/system_<year>.parquet`,
P1 pass, 2023–2025). No mechanism, no `ScenarioConfig` field, no matrix cell, no
keeper/board/verdict/marker write. The instrument and its validation against D36's own
numbers are in §2 and §9.

**Collision check at write (HEAD `0a3d22c7`):** no `FINDING-capx-d40-*`, `-d41-*` or a D32
floor-composition finding exists on `origin/main`; the position/requirement context is
cited from D33 (`FINDING-capx-d33-neiso-position-2026-09-02.md`, the denominator artifact
and its R-A devintage) and D31 (`FINDING-capx-d31-miso-caprev-repair-2026-09-02.md`, the
MISO capacity-revenue repair measured on the T1-H leg). Nothing here re-derives either.

## 0. Verdict (one paragraph, then the term table)

**Yes — the screen's forward expectation systematically understates what a marginal
entrant earns on the model's own realized price surface, and it does so through exactly
one term: the ENERGY leg, and specifically its DISPERSION, not its level.** Five of the six
ISOs (CAISO, PJM, MISO, NYISO, NEISO) price every capacity screen on the identical object:
`_lookahead_reprice_signal` — a static merit stack of time-mean full variable cost against
time-mean availability, searched at the entering year's net load, **tiled zone-flat, with no
scarcity tail** (`scarcity_price_overlay`/`scarcity_pricing_enabled` off for the screens in
all five) and **floored at the cheapest unit's cost** (no negative trough). Measured against
the model's own realized surface at each screen's own recorded variable cost (§3.1), that
object hands a new peaker **7–25 % of its realized energy margin** (MISO entering-2024/25:
0.20 / 0.09; CAISO 0.07 / 0.00; PJM 0.25 / 0.00) and a new CC **6–92 %** — the level is
roughly right (MISO signal mean $25.92 vs raw-dual mean $27.41; ERCOT 2024: 28.2 vs 31.5)
while the daily top-4/bottom-4 spread, the hours ≥ $100 and the zonal spread the realized
surface carries are absent by construction. **ERCOT is the counter-case, not the pattern:**
its armed posture (unified lookahead + FFR-8A expected-ORDC tail, the D12 forward reserve
leg and the D11-R exhaustion walk, Q15) OVERSTATES 21–29× at the tight step (entering-2023
gas_cc $3.29 M vs $0.15 M realized) and understates 8× two steps later — sign-varying, with
volume owned by the allocator (§3.2). **The other three terms do not understate.** The
attribute leg is EXACT by construction: the prior-year REC dual the screen credits equals
the ACP, and so does the LP's realized dual, in every committed forecast year of every RPS
ISO — CAISO $50, NEISO $50, NYISO $40, PJM $45, MISO $30 (§5) — so T16-A's NEISO result is
the cross-ISO signature, not a NEISO defect. The reserve leg exists only in ERCOT (D12
repaired it); everywhere else `reserve_price_signal` is `None` and the AS credit is $0. The
capacity leg is mis-expected through the POSITION the one adequacy seam evaluates
(NEISO's D33 denominator artifact, MISO's D31-repaired supply ratio, NYISO curve-OFF),
never through the price signal — and its expected-vs-COD-year realization flips sign
year to year (§3.3, the D28 oscillator seen from the entrant's side). Finally, **every VRE
entry in every committed forecast ledger is CAP-set** — NEISO solar/wind at the 2,000/1,000
MW per-tech caps or their 2× growth ladder, CAISO solar at 4,000, PJM solar/wind at
6,000/1,500, MISO wind at 4,000, NYISO wind at 1,000 (§5.2) — so the signal lane can change
WHEN and WHETHER a marginal technology (storage; a CT) clears, but cannot move the RPS
volume: that is the queue-cap/ladder object, whose NEISO values are LABELLED ESTIMATES.
Routed (§7): arm `entry_screen_diagnostics` on the next solve of every ISO (zero cost); open
the `entry_forward_expectation_signal` cells in the order **CAISO → MISO → NEISO**, with the
NEISO `U` cell opened only AFTER the D33 R-A requirement devintage (D40) lands, because
NEISO's thermal and storage capacity legs currently oscillate on the denominator artifact
and a signal A/B run before it would be confounded; **the NEISO cell should not open first.**
In the five tail-free ISOs the composed signal is, by construction, the "tail-free delta"
successor the ERCOT forward-expectation finding named (§6.1) — the two-scarcity-objects
defect that broke the ERCOT arm cannot arise there.

| term | ERCOT | CAISO | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| **energy leg** | armed tail: **over** 21–29× (tight step), ≈1.0, **under** 8× | **under** 1.1–14× (CC), 14×–∞ (CT); zonal spread 0 vs $9–21 | prior-dual posture (BLK-8): both signs 0.06–3.4×; current stack posture unmeasured | **under** 1.5–10× (CC), 5–11× (CT); FFR-4E: 21 % of the peaker leg | unmeasured (no diag) — realized surface has the widest zonal spread of the six ($4.8–12.2) | unmeasured (no diag) — realized 101–2,075 h ≥ $100 the stack cannot carry; storage sees $0.1–5/kW-yr (D36) |
| **reserve leg** | D12 phantom (realized-r) → repaired, armed Q15 | absent ($0) | absent ($0) | absent ($0) | absent ($0) | absent ($0) |
| **attribute leg** | n/a (no RPS) | exact: dual $50 = ACP | exact: $45 = ACP (T1-F); $0 in-sample | exact: $30 = ACP (d27/d31); $0 in the diag-on bundle | exact: $40 = ACP | exact: $50 = ACP |
| **capacity leg** | n/a (energy-only) | fixed $88.08 anchor = 94–100 % of CT revenue (FFR-3W) | curve-ON; fixed $74k/$60k in the diag bundle | $0 at every hindcast screen → D31: $13.83 vs real $79.07 | curve-OFF ⇒ fixed net-CONE $110 | curve at the D33-displaced position: $0–124/kW-yr, sign flips at COD |
| **volume binding** | exhaustion walk (armed) | solar cap 4,000; wind ladder 702 | solar/wind caps 6,000/1,500; CT ladder | wind cap 4,000 | wind cap 1,000; solar ≤ 2,000 cap | VRE cap/ladder; gas_cc 1,000 = cap; gas_ct 500 = cap; storage share cap (2050) |

## 1. What the "forward expectation" actually is — four terms, one seam, six postures

`apply_economic_new_entry` (`new_entry.py:789`) screens each candidate as
`margin = energy + attribute + capacity + AS − annualized fixed cost`, where:

- **energy** — thermal: `Σ_t max(price_t − vc, r_t)` on `prices.mean(axis=0)` (the ZONE-MEAN
  of the signal, `:1119`); VRE: the build zone's hourly CF dotted against that zone's row
  of `prices` (`:1253`); `prices` is `prior_results.price_signal`, which at
  `entry_lookahead_reprice=True` is `_lookahead_reprice_signal` (`runner.py:606`) — static
  stack, time-mean cost, time-mean availability, `np.searchsorted` into the cumulative
  stack, ORDC tail only if `scarcity_pricing_enabled AND scarcity_price_overlay` (`:812`),
  returned as `np.tile(prices_h, (n_zones, 1))` (`:874`).
- **reserve** — `reserve_price_signal{,_slow}`: ERCOT's realized post-solve adder (shipped)
  or the entering year's expected adder (`entry_forward_reserve_leg`, D12); `None` in every
  other ISO ⇒ the legacy annual AS credit, which `as_revenue_enabled=False` zeroes.
- **attribute** — `max(EAC, prior-year RPS dual at the build zone, clean-tier dual)`,
  never a sum (`:1283`); the dual is `prior_results.rps_shadow_price`, i.e. last year's LP
  REC dual.
- **capacity** — `capacity_revenue_per_mw_yr(iso, tech, EFORD, config, reserve_position,
  year)`: the ONE adequacy seam (`MarketDesign.capacity_price_per_firm_mw_yr` at
  `capacity_reserve_position`, D28 §1 / D36 §5) when `capacity_market_clearing` is on for
  the ISO, else a fixed net-CONE; VRE earns it only under `entry_vre_capacity_revenue`.

The registered posture per ISO, read from each bundle's committed `run_config.json`:

| ISO | bundle read | energy object the screens consume | tail | reserve leg | attribute (dual) | capacity leg | volume rule | expected side committed? |
|---|---|---|---|---|---|---|---|---|
| ERCOT | `ercot-2021-2025-realized-t1h-d12c-{control,armed}` (`28cef350`/`f061b264`) | unified lookahead (hourly availability, VRE potential, storage shave) + FFR-8A expected ORDC | **on** | entering-year expected adder (armed) | 0 (no RPS) | none (energy-only) | margin-exhaustion walk (armed) | yes — 4 `screen_signal_diag` npz per bundle; `entry_signal_l1_dual_replay_ercot.json` |
| CAISO | `caiso-2021-2025-realized-dumps` (`af508406`), `ffr4e/caiso-*` | shipped stack (no unified repairs) | off | none ($0) | $50 = ACP | fixed $88.08/kW-yr anchor (`caiso_ra_mpb_capacity_anchor` off) | bang-bang + ladder | yes — 2 npz; `entry_signal_l1_dual_replay_caiso.json` |
| PJM | `ff-t1f-s6-pjm/ledger`; `pjm-2021-2025-realized-blk8diag` | shipped stack (S-6); **prior-year duals** in the 2026-07-15 BLK-8 diag bundle | off | none ($0) | $45 = ACP (T1-F); $0 in-sample | curve-ON per `capacity_market_clearing_by_iso` (S-6); fixed $74k/$60k in BLK-8 | bang-bang + ladder | ledger rows at the OLD posture only |
| MISO | `miso-2021-2025-realized-t1h-{d27,d31}`; `ffr3v/miso-entry-diag` | shipped stack | off (`scarcity_price_overlay` False) | none ($0) | $30 = ACP (d27/d31); $0 in the diag-on bundle | RBDC curve (D31 supply ratio 0.8546); VRE capacity ON | bang-bang + ladder | ledger rows at the pre-D26/D31 posture only |
| NYISO | `ff-t1f-extcap/nyiso`; D10 | shipped stack | off (no overlay row) | none ($0) | $40 = ACP | curve-OFF ⇒ fixed net-CONE $110/kW-yr | bang-bang + ladder | **no** |
| NEISO | `ff-t3-neiso-golden/bau` (`706e7ba8`) | shipped stack | off (`scarcity_pricing_enabled` false) | none ($0; `as_revenue_enabled` false) | $50 = ACP | FCA curve at the entering position (2027–28 vintage hold-last) | bang-bang + ladder (`entry_rate_limits` true) | **no** (D36 §1 item 2) |

Two consequences of the table before any number: (i) **five ISOs share one price
object**, so a finding about that object is cross-ISO by construction and per-ISO only in
its magnitude; (ii) **the expected side is committed for ERCOT and CAISO (dumps + replay),
partially for MISO and PJM (diagnostics-on ledgers at superseded postures), and not at all
for NYISO and NEISO** — which is why D36's "precondition" (`entry_screen_diagnostics`,
output-only, no cache-key term) is the first routed item in §7, and why the NEISO rows
below are bounds rather than screen readings.

## 2. The instrument: the screens' own formulas on each keeper's realized surface

"What the model actually paid" is the in-model observable the charter names. The
forecast/hindcast bundles do not commit hourly prices (only ledgers, scores and, for
ERCOT/CAISO, the screen-side dumps), so the realized surface used here is **each ISO's
designated keeper backcast — the model's own P1 zonal duals for 2023, 2024 and 2025, on the
calibrated fleet** (`frontend/data/backcast/keepers/<ISO>.json` → `results/calibration/{ercot234_eastex_identity,
caiso231_b1_ungrounded, pjm_debugb_inputclock_A, miso198_oom_B, nyiso159_lossarm_B,
neiso99_joint_B}/hourly/`). This is the same stand-in the committed L-1 dual replay uses
(`dual_same_year`: "entering year's own realized model prices — foresight the screen cannot
have; diagnostic only"). Its one honest limit: the hindcast's own next-year fleet differs
from the keeper's (it has built what the screen decided), so the keeper surface is the
realized price of the year, not of the hindcast's fleet — a bounded difference the ERCOT
2024 row (ratio 1.04 / 0.92) shows is second-order outside the tight step.

**Validation.** On `neiso99_joint_B` the instrument returns li-ion 4 h arbitrage of
$1.24 / 0.13 / 2.74 k per MW-yr and iron-air $2.26 / 4.04 / 2.97 k (2023/24/25) — D36 §3.2's
committed 1.2 / 0.1 / 2.7 and 2.3 / 4.0 / 3.0 to the decimal. On `ercot223_release_arm`
(the replay's duals bundle) it returns li-ion 4 h $81,881 for 2023 — the committed
`dual_prior_solve` value exactly — when all seven zones are kept (the screen's own object;
ERCOT's no-load Panhandle row, mean $13.48 vs $29 elsewhere in 2024, sets the best-zone
spread, so the load-zone-only value is reported alongside).

| ISO | yr | zones | LW mean | zonal spread | daily top4−bot4 | h ≥ $100 | max | E(vc 25) | E(vc 35) | li-ion 4 h arb | iron-air arb | solar capture ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ERCOT | 2023 | 7 | 33.8 | 15.3 | 49.4 | 165 | 5,025 | 97.7 | 71.5 | 81.1 (46.6) | 246.4 (51.1) | 1.17 |
| ERCOT | 2024 | 7 | 29.1 | 15.7 | 36.3 | 74 | 5,000 | 63.7 | 42.4 | 60.4 (28.0) | 235.9 (27.4) | 0.96 |
| ERCOT | 2025 | 7 | 32.6 | 21.6 | 24.4 | 35 | 214 | 67.7 | 30.5 | 42.0 (6.5) | 238.8 (4.8) | 0.87 |
| CAISO | 2023 | 7 | 54.7 | 21.1 | 34.1 | 708 | 190 | 245.4 | 169.9 | 45.0 (27.6) | 62.7 (29.6) | 0.68 |
| CAISO | 2024 | 7 | 37.2 | 9.5 | 28.6 | 85 | 150 | 127.5 | 60.8 | 35.5 (22.4) | 79.3 (40.5) | 0.63 |
| CAISO | 2025 | 7 | 38.2 | 8.7 | 28.0 | 0 | 70 | 132.6 | 63.9 | 35.7 (25.6) | 59.9 (45.3) | 0.64 |
| PJM | 2023 | 9 | 30.9 | 3.2 | 8.3 | 2 | 111 | 52.7 | 7.7 | 1.8 | 0.0 | 1.01 |
| PJM | 2024 | 9 | 30.1 | 4.8 | 10.5 | 64 | 145 | 48.2 | 13.5 | 5.4 | 3.5 | 1.01 |
| PJM | 2025 | 9 | 40.8 | 7.2 | 15.4 | 65 | 432 | 134.6 | 59.3 | 10.8 | 9.2 | 0.99 |
| MISO | 2023 | 8 | 32.4 | 0.9 | 8.9 | 5 | 243 | 64.8 | 8.5 | 0.6 | 0.0 | 1.05 |
| MISO | 2024 | 8 | 30.0 | 1.8 | 10.2 | 47 | 500 | 48.7 | 11.8 | 2.1 | 5.3 | 1.03 |
| MISO | 2025 | 8 | 39.0 | 4.3 | 11.4 | 18 | 184 | 121.9 | 43.8 | 1.1 | 0.0 | 0.99 |
| NYISO | 2023 | 6 | 31.7 | 12.2 | 11.6 | 35 | 192 | 70.1 | 20.7 | 2.7 | 4.9 | 1.03 |
| NYISO | 2024 | 6 | 36.3 | 4.8 | 11.9 | 131 | 190 | 100.5 | 44.2 | 1.4 | 3.3 | 1.01 |
| NYISO | 2025 | 6 | 55.8 | 7.4 | 18.3 | 653 | 304 | 273.3 | 190.7 | 4.0 | 6.4 | 0.95 |
| NEISO | 2023 | 5 | 38.4 | 0.0 | 7.1 | 178 | 249 | 118.0 | 59.2 | 1.2 | 2.3 | 0.95 |
| NEISO | 2024 | 5 | 43.7 | 0.0 | 6.5 | 101 | 218 | 164.6 | 93.6 | 0.1 | 4.0 | 0.87 |
| NEISO | 2025 | 5 | 69.3 | 0.0 | 13.2 | 2,075 | 281 | 388.0 | 300.7 | 2.7 | 3.0 | 0.84 |

$/MWh for prices and spreads; `E(vc)` = `Σ max(p̄_t − vc, 0)` in $k/MW-yr on the zone-mean
price (the thermal screen's own basis); arbitrage in $k/MW-yr on all zones (load zones in
parentheses where they differ), li-ion 4 h at RTE 0.85 / $22.63/MWh degradation, iron-air
100 h at RTE 0.50 / $1.67 (the golden's own parameters, D36 §1); solar capture ratio = the
existing solar class's dispatch-weighted price ÷ the mean price. Zonal spread is the mean
hourly (max − min) across zones; NEISO's is 0.0 because the keeper's four load zones price
identically in P1 (its HQ node too) — NEISO's realized locational dispersion is itself a
backcast-lane object, noted and not pursued here.

## 3. Expected vs realized, per ISO

### 3.1 The energy leg at each screen's own variable cost (the load-bearing table)

Expected = the committed screen reading (the replay's `shipped_signal` energy margin, or the
diagnostics-on ledger's `energy_revenue_per_mw_yr`) at the variable cost the screen itself
recorded. Realized = the same integral on the entering year's keeper surface (§2).

| ISO | entering | tech | vc $/MWh | expected $/MW-yr | realized $/MW-yr | ratio | posture of the expected side |
|---|---|---|---:|---:|---:|---:|---|
| ERCOT | 2023 | gas_cc | 14.85 | 3,294,737 | 154,913 | **21.3** | armed tail, priced on the 2021 solve across the bridge |
| ERCOT | 2023 | gas_ct | 21.86 | 3,233,347 | 111,690 | **29.0** | " |
| ERCOT | 2024 | gas_cc | 12.65 | 136,425 | 131,347 | 1.04 | armed tail (adder mean $6.66) |
| ERCOT | 2024 | gas_ct | 18.71 | 85,428 | 92,615 | 0.92 | " |
| ERCOT | 2025 | gas_cc | 21.09 | 10,855 | 89,584 | **0.12** | armed tail (adder mean $1.17) |
| ERCOT | 2025 | gas_ct | 30.77 | 5,528 | 43,045 | **0.13** | " |
| CAISO | 2024 | gas_cc | 33.46 | 64,441 | 69,872 | 0.92 | tail-free stack |
| CAISO | 2024 | gas_ct | 48.32 | 1,103 | 16,833 | **0.07** | " |
| CAISO | 2025 | gas_cc | 41.90 | 1,927 | 28,176 | **0.07** | " |
| CAISO | 2025 | gas_ct | 60.38 | 0 | 413 | **0.00** | " |
| MISO | 2023 | gas_cc | 19.9 | 113,683 | 108,851 | 1.04 | bridge: 2021 raw duals |
| MISO | 2023 | gas_ct | 29.1 | 35,402 | 33,976 | 1.04 | " |
| MISO | 2024 | gas_cc | 17.7 | 72,118 | 107,159 | **0.67** | tail-free stack |
| MISO | 2024 | gas_ct | 25.9 | 8,727 | 43,068 | **0.20** | " |
| MISO | 2025 | gas_cc | 26.1 | 11,705 | 112,272 | **0.10** | " |
| MISO | 2025 | gas_ct | 38.0 | 2,750 | 29,698 | **0.09** | " |
| PJM | 2023 | gas_cc | 22.2 | 132,631 | 75,294 | **1.76** | prior-year duals (2022 gas spike) |
| PJM | 2023 | gas_ct | 32.4 | 45,729 | 13,380 | **3.42** | " |
| PJM | 2024 | gas_cc | 20.0 | 72,890 | 86,020 | 0.85 | prior-year duals |
| PJM | 2024 | gas_ct | 29.2 | 6,859 | 27,671 | **0.25** | " |
| PJM | 2025 | gas_cc | 28.5 | 6,037 | 105,074 | **0.06** | " |
| PJM | 2025 | gas_ct | 41.3 | 0 | 32,702 | **0.00** | " |

Three readings, each measured:

1. **The tail-free stack understates one-signed, and the miss is dispersion.** Every
   stack-posture row (CAISO, MISO 2024/25) sits at 0.00–0.92, and the peaker rows — the
   candidate whose margin IS the tail of the distribution — at 0.00–0.20. FFR-4E's MISO
   decomposition (signal max $39, 0 h > $39, vs 47 h ≥ $100 on the keeper) already names
   the mechanism: "~$30,300/MW-yr thrown away is 97 % sub-$200 dispersion, not scarcity",
   and its ORDC-tail counterfactual is worth "approximately nothing" at MISO's reserve
   floor. The same object, seen from CAISO's replay: shipped daily spread 12.7 / 14.4 vs
   35.5 / 30.0 on the duals, zonal range 0 vs 2.7 / 2.5, and the sign flips it produces —
   gas_cc −$82.7 k → **+$66.6 k** and solar −$6.2 → **+$2.9/MWh** at entering-2024.
2. **The prior-dual construction errs BOTH ways** (PJM 2023 at 1.8–3.4×, 2025 at 0.00–0.06):
   it is naive expectations — last year's outturn as next year's forecast — and it lags the
   gas price by one year. It is not a repair of the stack; it is the disarm corner the
   ERCOT lane already measured (terminal RM 40.24 %).
3. **ERCOT's armed tail is sign-varying, and the volume is not its to set.** 21–29× over
   at the post-bridge tight step (the FFR-8A expected adder on the 2021-vintage fleet, mean
   $347.71), 0.9–1.0 at 2024, 0.12 at 2025 — and D11-R/D12 have already established that
   the trajectory is the allocator's (three constructions spanning a ~$200/MWh swing in the
   entering-2024 mean produced one trajectory). ERCOT's energy leg is therefore not the
   under-build object; its remaining open item is the composed forward-expectation signal's
   two-scarcity-objects defect (cell `O`, §6.1).

### 3.2 Storage and VRE on the same surfaces (the screen's own formulas)

| ISO | entering | li-ion 4 h arbitrage: expected → realized ($k/MW-yr) | iron-air: expected → realized | solar capture ratio: expected → realized | source of the expected side |
|---|---|---|---|---|---|
| ERCOT | 2024 | 44.6 → 60.4 (81.9 on the prior-year duals) | 43.9 → 235.9 (253.7) | 1.38 → 0.96 (1.55 on prior duals) | replay `shipped_signal` vs §2 / `dual_prior_solve` |
| ERCOT | 2025 | 4.5 → 42.0 (60.0) | 1.5 → 238.8 (248.9) | 1.03 → 0.87 (1.28) | " |
| CAISO | 2024 | 2.9 → 35.5 (29.2) | 0.0 → 79.3 (32.0) | 0.90 → 0.63 (0.82) | " |
| CAISO | 2025 | 4.1 → 35.7 (24.6) | 2.0 → 59.9 (43.0) | 0.84 → 0.64 (0.79) | " |
| NEISO | 2027–2050 | bracket: < required $77–154 in every year; keeper surface 0.1–2.7 | crossed $79–83 only at the 2050 screen; keeper 2.3–4.0 | — | D36 §2–§3 (no committed screen reading) |

Two things the storage rows add to D36. **The stack's arbitrage blindness is not
NEISO-specific**: CAISO's shipped signal gives li-ion 4 h $2.9–4.1 k against $24.6–35.7 k
on the model's own duals — the identical object D36 §3.3 characterized ("no scarcity tail,
no negative trough, zone-flat, time-mean cost"), here on an ISO whose realized surface has
a 4–7 % negative-hour share the screen floors away. And **the realized surfaces of the four
ISOs whose LP has no intraday tail (PJM, MISO, NYISO, NEISO: li-ion 4 h $0.1–10.8 k) cannot
clear a $126–157/kW-yr machine either** — the D36 conclusion that the model's own price
formation offers 1/10–1/20 of the market's spread is a backcast-lane (C3c-ledgered)
object in every one of them, and no entry-signal construction can manufacture dispersion
the dispatch LP never priced. The signal lane's ceiling is the dual surface itself.

**VRE capture.** The zone-flat object mis-shapes capture in both directions: ERCOT's
shipped signal credits solar 1.38× the mean where the realized 2024 surface pays 0.96×
(the D-8 anti-correlation: the stack puts scarcity on solar's hours); CAISO's credits 0.90
where the duals pay 0.63–0.82 (the real cannibalization the stack cannot see). Under a $45–50
ACP attribute credit these misses are second-order for the VRE clearing decision (§5) —
they matter for storage and for CTs, whose entire margin is shape.

### 3.3 The capacity leg — expected at decision vs paid at COD (the position, not the signal)

NEISO golden-2, thermal decisions and the FCA-curve price the ONE seam pays at the entering
position (D36 §2 column "curve price", the position D33 §1 shows is evaluated against a
single-vintage requirement):

| decision year | tech (MW) | curve price the screen credited, $/kW-yr (position) | curve price at COD year (position) | Δ |
|---|---|---:|---:|---:|
| 2029 | gas_cc 1,000 (= cap) | 100 (1.004) | 2031: 124 (0.996) | +24 |
| 2030 | gas_ct 500 (= cap) | 107 (1.001) | 2032: 46 (1.031) | −61 |
| 2031 | gas_cc 1,000 | 124 (0.996) | 2033: 27 (1.045) | **−97** |
| 2033 | gas_cc 1,000 | 27 (1.045) | 2035: 94 (1.008) | +67 |
| 2035 | gas_cc 1,000 | 94 (1.008) | 2037: 38 (1.036) | −56 |
| 2049 | gas_cc 1,000 | 84 (1.012) | beyond horizon | — |

The entrant's own arrival (1,000 MW = the gas_cc per-tech cap, one-year lag, bang-bang)
moves the position across the curve's steep segment, so the leg it was credited is paid
within ±$97/kW-yr of itself with alternating sign — D28's "$0 when long, 2.6× reality when
it dips" seen from the entrant's side. Against a fixed cost of ~$147/kW-yr (gas_cc) that
is the whole decision. Nothing in the price signal touches this: it is the D33 denominator
artifact (`peak × 1.028607` frozen at one vintage) plus the convention seam, and D33 §5's
sign discipline already states the repair direction (revenue UP in long years, DOWN in the
dip years, oscillator killed in both directions). MISO's committed row is the same object
with a different sign history: $0 at every hindcast screen (D27 §5) where the real PRA
cleared $3.4–7.3/kW-yr, and after D31 $13.83 vs $79.07 at the market's own position. CAISO's
fixed $88.08 anchor is 94–100 % of a new CT's revenue (FFR-3W §1.2) and FFR-4F showed its
correction moved 0.0 MW of thermal. NYISO runs curve-OFF (fixed net-CONE $110/kW-yr) —
a position-blind leg. **In every capacity-market ISO the capacity leg's expected-vs-realized
error is a POSITION/requirement object already routed (D31 landed; D33 → D40), never a
signal object.**

## 4. Term attribution, per ISO, and what each under-build actually is

- **ERCOT** — energy leg sign-varying under the armed tail; reserve leg repaired (D12,
  Q15); no attribute or capacity leg; volume owned by the exhaustion walk. The remaining
  signal object is the composed forward-expectation signal's realized-vs-pro-forma
  scarcity mismatch (entering-2024 composed mean −$48.22/MWh; solar flipped off). Cell `O`,
  owner-gated; nothing here re-opens it.
- **CAISO** — the tail-free stack understates the peaker/CC energy leg 1.1–14× and the
  storage arbitrage leg 8–12× against the model's own duals (sign flips on gas_cc and
  solar in the 2024 screen; iron-air −$61.2 k → −$29.2 k, still short); the RA anchor is
  94–100 % of CT revenue and moves no MW when corrected; AS credit $0 (D-9). **The
  under-build object is the energy leg's dispersion; the residual after it is the value
  stack (D-9), not the signal.**
- **PJM** — the committed screen reading is at the superseded prior-dual posture (both-sign
  cobweb, 0.00–3.4×); at the current stack posture nothing is committed. Solar −100 % vs
  13.1 GW actual with attribute $0 in-sample and $45 = ACP from 2026 on (§5); wind
  cap-bound at 1,500 every year; gas_ct entry is the S-6 backstop ladder. **Energy leg by
  construction (BLK-8 term (a)), unmeasured at the live posture; volume cap/ladder-set.**
- **MISO** — energy leg 5–11× under for the peaker, 1.5–10× for the CC at the stack
  posture (FFR-4E's 21 %); capacity leg $0 → D31 $13.83 (vs $79.07 real); attribute $0
  in the diag-on bundle but $30 = ACP in d27/d31 — the screen the committed ledgers
  describe is NOT the screen the registered leg now runs (§5.3). **Energy leg dispersion
  plus the capacity position; wind cap-bound at 4,000; solar's clearing hinges on the $30
  attribute and the D31 capacity leg, neither of which is a signal object.**
- **NYISO** — no screen reading exists; the realized surface carries the widest zonal spread
  of the six ($4.8–12.2/MWh, Long Island/NYC vs Upstate) and 653 h ≥ $100 in 2025, all of
  it discarded by the zone-flat object; capacity leg position-blind (curve-OFF).
  **Unmeasured; first item is the diagnostics dump.**
- **NEISO** — attribute exact ($50 = ACP, every year); VRE, gas_cc and gas_ct volumes ALL
  cap-set (the T16-A uncapped arm sits exactly on 2,000/1,000; the golden's thermal
  entries are 1,000 = cap and 500 = cap); thermal timing set by the D33-displaced position
  (§3.3); storage short on the arbitrage leg (D36) against a realized surface that itself
  offers only $0.1–4/kW-yr. **The RPS under-build is the CAP object; the storage under-build
  is the energy-leg dispersion object bounded by the LP's own dispersion; the thermal
  timing is D33/D40's.**

## 5. The RPS/ACP signature is cross-ISO, and every VRE volume is cap-set

### 5.1 The attribute leg is exact — in every RPS ISO

Every committed forecast ledger's `rps_dual` (the value the NEXT year's screen credits as
the attribute price) across the repository:

| ISO | ACP (`STATE_RPS_ACP`) | forecast ledgers 2026+ | hindcast ledgers 2021–2025 |
|---|---:|---|---|
| CAISO | 50 | 50.0 in every year of every bundle (ffr3p/4d/4e/4f/ffrsc, 2026–2030) | — |
| NEISO | 50 | 50.0 in all 25 golden-2 years, both T16-A arms, s4b/s4hydro | 50.0 (mystic T1-H, crossover) |
| NYISO | 40 | 40.0 (extcap, 2026–2030) | 40.0 (realized T1-H) |
| PJM | 45 | 45.0 (s6, 2026–2030) | 0.0 (every hindcast bundle) |
| MISO | 30 | 30.0 (s123, arm3arm 2031–35) | 30.0 (d27/d31); **0.0** (ffr3v/ffr4b/ffr4c) |
| ERCOT | — | 0.0 | 0.0 |

The LP enters the ACP as the cost of an RPS escape column (`policy/rps.py:185`), so a
binding-and-unmet RPS row's dual is the ACP by construction; the screen credits last year's
dual; the LP realizes the same ACP. **Expected = realized, exactly, in every RPS ISO, every
forecast year.** T16-A's "the RPS target is unreachable at every VRE volume the entry stack
builds" is therefore the program-wide state of the RPS stack, not a NEISO finding — and it
cannot be an expectation defect. Whether a forward REC price should be the ACP rather than
a cleared REC-market price is a policy/RPS-lane question (context: MA Class I and NY Tier 1
RECs clear well below their ACPs; MISO state RECs in single digits) and is out of this
charter's scope; it is named so it is not mistaken for a signal object.

### 5.2 Every VRE volume in every committed forecast ledger is cap- or ladder-set

| ISO / bundle | decided wind / solar per year | binding object |
|---|---|---|
| NEISO golden-2 | 713/1,089 alternating with 287/911 (2027–2050); T16-A uncapped arm 1,000/2,000 | `entry_rate_limits` ladder (2× prior-max) under the 1,000/2,000 per-tech caps |
| CAISO ffr4e control | wind 702 every year; solar 4,000 in 2027/2029 | wind ladder; solar per-tech cap 4,000 |
| PJM s6 | wind 1,500, solar 6,000 (2027, 2029) | per-tech caps exactly |
| MISO s123 / d31 | wind 4,000 (2027; 2025 decision) | per-tech cap; solar 1,236 (d31) via the FFR-4B capacity leg |
| NYISO extcap | wind 1,000 (2027, 2029); solar 1,843 / 2,000 | per-tech caps |

So the margin decides WHETHER a VRE technology clears (with a $30–50 attribute credit it
clears everywhere it is not cannibalized below cost — PJM solar is the one committed case
that does not, at $0 attribute in-sample) and the caps decide HOW MUCH. NEISO's caps are
the least identified of the six: `QUEUE_CAP_GW["NEISO"] = 4` is a **LABELLED ESTIMATE**
("measured COD throughput ~0.5–1.5 GW/yr … forward-ceiling ESTIMATE above demonstrated
throughput", `capacity_market.py:4075`; `queue-cap-citation-2026-07.md` item 1 "strike a
real throughput number" still open) and the per-tech 1.0/2.0 GW rows carry no citation at
all (`:4082` — "ERCOT CDR, CAISO TPP — approximate"). The NEISO RPS under-build is a
throughput-identification question — the ISO-NE queue's demonstrated per-technology COD
series — before it is anything else.

### 5.3 A posture drift the MISO record now carries

The only MISO screen ledgers on disk (ffr3v/ffr4b/ffr4c) credit solar `attribute_price 0.0`
(rps_dual 0.0, "MISO's 11 % target is slack against a 16.9 % modelled VRE share",
FFR-3V §4.6), while the registered d27/d31 T1-H ledgers carry `rps_dual = 30.0` in every
solved year (post-D26/D29 defaults). At cf 0.22 that is a $57.8 k/MW-yr attribute credit
the committed screen rows never saw — enough on its own to flip the ledgers' solar margins
(−$22.7 k to −$35.9 k) positive. No diagnostics-on ledger exists at the live MISO posture;
this is a precondition item, not a finding about the sign.

## 6. What a repair would be identified FROM (rule 13), per ISO — and why the composition is cleaner outside ERCOT

### 6.1 The construction, and its ERCOT defect, in the tail-free ISOs

`entry_forward_expectation_signal` composes `signal[z,t] = duals[z,t] + (S_entering[t] −
S_current[t])` (`runner.py:877`): the run's own prior-year zonal dual surface, re-leveled
by the lookahead instrument's forward delta. The ERCOT arm's measured defect
(`FINDING-entry-signal-forward-expectation-2026-08-25.md` §4) was that `S_current` carried
the FFR-8A **pro-forma** tail while the duals carried only the **realized** overlay — two
scarcity objects, one subtraction, entering-2024 composed mean −$48.22. Its named successor
was "both S evaluations tail-free, so the duals carry all scarcity and the delta carries only
the merit-stack move". **In CAISO, PJM, MISO, NYISO and NEISO that is the construction as
shipped**: `scarcity_pricing_enabled AND scarcity_price_overlay` is false for the screens in
all five, so both `_lookahead_reprice_signal` evaluations return the bare stack and the
delta is exactly the merit-stack move; the duals carry whatever scarcity the LP priced
(CAISO's overlay included, `result.prices` at `runner.py:3471`). The composed object there
is locational, forward-looking, carries the LP's own tail and trough, and has zero fitted
parameters — the D-8 characterization's missing corner, with the ERCOT defect structurally
absent. This is why the five `U` cells test a cleaner instrument than the ERCOT `O` cell
did, and why they must not inherit its verdict (rule 25): each ISO's evidence is its own
dumps (§7 item 1), never a transfer.

### 6.2 Per-ISO identification sources (published data or the model's own objects, never a residual)

| ISO | energy-leg repair identified from | capacity-leg repair identified from | volume identified from |
|---|---|---|---|
| ERCOT | the successor tail-free delta (both `S` evaluations tail-free, or both pro-forma) on the committed dumps — exact arithmetic (cell `O`, owner-gated) | n/a | the armed walk; D-1 closed |
| CAISO | the committed L-1 dual replay (`entry_signal_l1_dual_replay_caiso.json`) + the two dumps: the composition's own `signal_zonal_usd_mwh` at the next solve; CAISO's realized overlay already lives in the duals | CPUC RA/MPB published values (`caiso_ra_mpb_capacity_anchor`, FFR-4F) — moved 0 MW | CAISO TPP deliverability throughput (cited) |
| PJM | a diagnostics-on ledger at the LIVE stack posture (none exists), then the composition; the disarm corner is already characterized as cobweb | the published VRR curve at the S-6 position + the ELCC resolver (R3/R4) for `entry_vre_capacity_revenue` (`U`) | per-tech caps are cited to the 2015–18 gas build-out; solar cap 6.0 |
| MISO | FFR-4E's own decomposition (model duals vs signal, 21 %); the OFF branch of `entry_lookahead_reprice` is the registered raw-dual alternative; the composition is the forward-looking one | D31 (landed): PRA supply tables + RBDC, ratio 0.8546 | MISO GI queue-cycle results (cited, 10 GW/yr) |
| NYISO | a diagnostics-on ledger first (none exists); the keeper's own zonal surface ($4.8–12.2 spread) is the identification of what the zone-flat object discards | the published ICAP demand curve (curve-ON, `O` — the FFR-2E wrong-arm citation must be repaired first) | Gold Book COD series — the 4 GW cap is a LABELLED ESTIMATE |
| NEISO | `entry_screen_diagnostics` on the next solve (D36 R-1 precondition), then the composition on the golden's own duals (2,243 h ≥ $100 in 2049 that the stack never handed the screen) | D33 R-A/R-B (→ D40): the per-CCP Net ICR series + one convention | ISO-NE Annual Markets Report Fig. 1-9 COD series per technology — the 1.0/2.0 GW per-tech caps are uncited |

## 7. Routed recommendation — which ISOs get repair lanes, in what order, and the NEISO `U` cell

1. **Precondition, every ISO, zero cost: `entry_screen_diagnostics=True` on the next solve
   of any kind** (output-only, no cache-key term, no solve-path change — the L-5 dump; D36
   R-1). Today the expected side is committed for two ISOs; after one solve per ISO it is
   committed for six, and the §3.1 table becomes a screen reading instead of a bound for
   NYISO/NEISO and a live-posture reading for PJM/MISO (§5.3).
2. **CAISO first.** Largest committed expected-vs-realized gap with the replay already in
   place (peaker 0.00–0.07, CC 0.07–0.92, storage 8–12×, sign flips in both the thermal and
   the VRE screen at entering-2024), a scarcity overlay the duals already carry, and a
   capacity leg whose correction is measured inert (0.0 MW) — so an A/B on the composition
   is the cleanest single-term isolation available anywhere in the program. Pre-declare on
   the replay's sign flips; the storage kill-gate is that a 4 h machine still cannot clear
   (the duals' own spread is $22–36 k against a $148 k cost — D-9's value stack is the
   residual, stated before the solve so it cannot be traded).
3. **MISO second.** FFR-4E's 21 % is the most exactly quantified energy-leg loss in the
   record; D31 has just landed the capacity leg, so a signal A/B on the d31 baseline is a
   one-term delta. Pre-declare that wind stays cap-bound at 4,000 (the signal cannot move
   it) and that the solar outcome is jointly the $30 attribute + D31 capacity leg + signal.
4. **NEISO third — after D40 (D33 R-A) lands, not before, and not first.** The NEISO thermal
   and storage capacity legs currently oscillate on the denominator artifact (§3.3, D36 §5);
   a signal A/B run on the golden's requirement would attribute position-driven timing
   moves to the signal. Sequence: D40 devintages the requirement → the D37 T1-H re-run at
   the armed posture carries `entry_screen_diagnostics` → the NEISO `U` cell opens on that
   committed expected side. What the NEISO cell can and cannot deliver is stated now so the
   lane is not chartered against the wrong object: it can move storage timing (the
   arbitrage leg reads the golden's own 2,243–2,446 h ≥ $100 and 6–7 % negative hours
   instead of a tail-free floor) and CT/CC timing; it cannot move the VRE volume (cap-set)
   or the REC dual (exact at ACP), and it cannot exceed the dispersion the dispatch LP
   itself prices (the keeper's $0.1–4/kW-yr, a backcast-lane object).
5. **PJM and NYISO** after their first diagnostics dump exists (item 1); NYISO's curve-OFF
   capacity leg and the FFR-2E wrong-arm citation are separate, prior items.
6. **ERCOT:** nothing new; the successor tail-free delta stays the owner-gated `O` cell.
7. **Two objects routed OUT of the signal family, so they are not re-chartered into it:**
   (a) the RPS/ACP pin in all five RPS ISOs (§5.1) — an RPS-stack question (target vs
   eligible supply vs the ACP as the forward REC price), and (b) the NEISO per-tech queue
   caps (§5.2) — a throughput-identification intake (ISO-NE per-technology COD series), the
   actual owner of "the entry stack under-builds against the RPS constraint".

**Rule 28:** no cell moves. The six `entry_forward_expectation_signal` cells are read; the
ERCOT `O` and five `U` verdicts stand; the routed order above is a recommendation to the
director, and each opened cell derives its own parameters (there are none — zero-DOF) and
its own verdict from its own ISO's dumps (rule 25).

## 8. Governance attestation

ZERO solves; no LP, no bench, no re-score, no registration; rule 15 does not fire. No
out-of-training year touched: the hourly sidecars read are the six keepers' 2023–2025
training years; every forecast bundle read is 2026+ (rule 22's unrestricted forecast
clause); the crossover/hindcast ledgers read are committed artifacts. Docs only: this
finding; no `src/`, no matrix shard, no board/verdict/keeper/marker/FC-row file, no
`neiso-t3` write, no workflow. Rule 25 held: every number is its ISO's own; the ERCOT
identification PATTERN (dumps → replay → composed construction → A/B) is cited, no ERCOT
number or verdict transfers. Rule 13: AEO and the corridor rows appear nowhere as targets;
the "actual additions" figures quoted are the committed hindcast scores' context. Rule 27:
no ≥300-line source file touched (this is a new file). Collision: D40/D41/D32 absent on
main at write; D33/D31 cited as current.

## 9. Reproduction (the instrument, committed inline)

```python
# realized_surface.py — zero solves; pandas + pyarrow only. Run from the repo root.
import math, sys, numpy as np, pandas as pd
KEEPERS = {"ERCOT": "results/calibration/ercot234_eastex_identity",
           "CAISO": "results/calibration/caiso231_b1_ungrounded",
           "PJM": "results/calibration/pjm_debugb_inputclock_A",
           "MISO": "results/calibration/miso198_oom_B",
           "NYISO": "results/calibration/nyiso159_lossarm_B",
           "NEISO": "results/calibration/neiso99_joint_B"}
STOR = {"li_ion_4hr": (4, 0.85, 22.63), "iron_air": (100, 0.50, 1.67)}  # (h, RTE, $/MWh degr.)
def storage_rev(P, d, rte, deg):  # storage.py::estimate_storage_revenue, verbatim logic
    bh = max(1, math.ceil(d / 12)) * 24; nb = P.shape[1] // bh
    o = np.sort(P[:, : nb * bh].reshape(P.shape[0], nb, bh), axis=2)
    ch, dis = o[:, :, :d].mean(axis=2), o[:, :, -d:].mean(axis=2)
    bz = np.argmax(dis - ch, axis=0); i = np.arange(nb)
    return float(np.maximum(dis[bz, i] - ch[bz, i] / rte - deg, 0).sum() * d)
rows = []
for iso, b in KEEPERS.items():
    for y in (2023, 2024, 2025):
        s = pd.read_parquet(f"{b}/hourly/system_{y}.parquet"); s = s[s["pass"] == "P1"]
        piv = s.pivot_table(index="zone", columns="hour", values="price")
        dem = s.pivot_table(index="zone", columns="hour", values="demand")
        load = dem.sum(axis=1) > 0
        P, PL, W = piv.to_numpy(float), piv[load].to_numpy(float), dem[load].to_numpy(float)
        p_lw = (PL * W).sum(0) / W.sum(0); p_mean = P.mean(0); T = P.shape[1]
        dd = np.sort(p_lw[: T // 24 * 24].reshape(-1, 24), axis=1)
        r = dict(iso=iso, year=y, lw_mean=p_lw.mean(),
                 zonal_spread=(P.max(0) - P.min(0)).mean(), h_ge_100=int((p_lw >= 100).sum()),
                 daily_top4_bot4=float((dd[:, -4:].mean(1) - dd[:, :4].mean(1)).mean()),
                 p_max=p_lw.max(), neg_frac=float((p_lw < 0).mean()))
        for vc in (15, 25, 35, 45): r[f"E_vc{vc}"] = float(np.maximum(p_mean - vc, 0).sum())
        for t, (d, rte, deg) in STOR.items():
            r[f"arb_{t}"] = storage_rev(P, d, rte, deg); r[f"arb_{t}_load"] = storage_rev(PL, d, rte, deg)
        c = pd.read_parquet(f"{b}/hourly/class_hourly_{y}.parquet"); c = c[c["pass"] == "P1"]
        for lab, pat in (("wind", "WIND"), ("solar", "SOLAR")):
            g = c[c["klass"].str.upper().str.contains(pat)].groupby("hour")["mw"].sum().reindex(range(T)).fillna(0).to_numpy()
            if g.sum() > 0: r[f"{lab}_capture_ratio"] = float((p_mean * g).sum() / g.sum()) / p_mean.mean()
        rows.append(r)
pd.DataFrame(rows).to_csv(sys.argv[1] if len(sys.argv) > 1 else "realized_surface.csv", index=False)
```

The §3.1 realized column is `Σ max(p_mean − vc, 0)` on the same `p_mean` at the variable
costs printed in the table (the replay's `var_cost_per_mwh` for ERCOT/CAISO; the ledgers'
for MISO/PJM). Expected-side sources: `results/calibration/entry_signal_l1_dual_replay_{ercot,caiso}.json`
(`steps.<year>.arms.shipped_signal` / `dual_prior_solve` / `dual_same_year`);
`results/ffr3v/miso-entry-diag/MISO/ca36ba26ebe1640f/evolution_<year>.json` and
`results/hindcast/pjm-2021-2025-realized-blk8diag/PJM/b6144d9d292349b1/evolution_<year>.json`
(`entry_screen_diagnostics` rows); `results/ff-t3-neiso-golden/bau/{full_horizon_summary.json,
NEISO/706e7ba8e6582d42/evolution_<year>.json}`; every `results/**/evolution_*.json`'s
`rps_dual` and `entry_decided_mw_by_tech` (§5). Validation: NEISO storage rows reproduce
D36 §3.2 to the decimal; ERCOT 2023 li-ion 4 h on `ercot223_release_arm` reproduces the
replay's `dual_prior_solve` $81,881 exactly.
