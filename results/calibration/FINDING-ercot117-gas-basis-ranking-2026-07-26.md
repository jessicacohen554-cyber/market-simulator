# FINDING — ERCOT-117: the mid-merit ranking bias owns the coal LEVEL, not the seasonal term — and the coal supply curve itself is exonerated

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Arm** `ercot117_gas_basis_probe` = the ercot115 keeper + `ercot_thermal_dam_availability_coal`
+ `ercot_zonal_gas_basis=false` (`replay_keeper`, two declared deltas) ·
**Run id** `2026-07-26-ercot117-gas-basis-probe` ·
**Pre-commit** `PRECOMMIT-ercot117-gas-basis-probe-2026-07-26.md` (pushed at `39b3a0f` with the
no-LP probe `scripts/probes/ercot117_coal_gas_ranking.py` BEFORE any year was solved) ·
**Determination** NOT-YET (rejected probe **by design** — it disarms a measured input; keeper unchanged)

## 1. The no-LP measurements that preceded the solve (probe §A–§F)

The ERCOT-116 charter asked **which side of the $15–25 coal-vs-CC crossing is displaced**.
Measured before any mechanism was written:

1. **The model's coal supply curve is exonerated.** The real coal fleet's RT (SCED TPO)
   supply reaches 0.65–0.71 of telemetered HASL at ≤$20 and **0.91–0.92 at ≤$25** — stable
   across 2024/2025 and tail/control day families, with HASL ≈ 0.99 × HSL (nothing
   telemetered away). The model's coal supply: 0.66 at ≤$20, 0.91 at ≤$25. Same knee, same
   top. The DAM picture (energy awards only 6–17 % of live capability; offered curves
   saturating ~5.4 GW) is QSE self-supply bypassing DAM transaction, not withheld capability.
2. **The coal fuel-price basis is confirmed** (the charter's named F923 lead): both
   F923-reporting PRB plants price within ±$0.06/MMBtu of the model's reporter-proxy basis
   ($1.71/$1.81 vs $1.75). San Miguel lignite measures $3.56 vs the model's $1.45 — but it
   is 410 MW, offers at $19–20 in the DAM, and is not the crossing's owner.
3. **The model's CC supply is displaced dear in the crossing band, every year**: at ≤$15
   the model carries 1.8 / 4.6 / 0.4 GW (2023/24/25 summer) against a measured committed
   DAM supply of 12.5 / 14.3 / 15.1 GW (offer curves floored at committed LSL).
4. **The consequence, visible in the keeper's own sidecars**: in actual-$15–25 hours
   (~3,000–3,700 h/yr) the keeper's load-weighted price runs **+$5.0 / +$4.4 / +$7.0 above
   actual** (and +$7–11 in actual-$10–15 hours), both seasons, all years. Every
   correctly-priced coal tranche ≤$25 clears in hours reality cleared at ~$20.

Root-cause hypothesis registered in the pre-commit: every ERCOT gas offer-surface artifact
normalizes measured offers by **HH daily − 0.50** while the keeper prices dispatch gas at the
**EP-anchored zonal level** (+0.50 / +0.41 / +0.04 $/MMBtu above that basis in 2023/24/25) —
so the measured offer surface is repriced ~+25 % in 2023/24. The ablation
`ercot_zonal_gas_basis=false` restores derivation⇄dispatch consistency in 2023/24 and is a
null control in 2025.

## 2. The arm (G0: armed and biting)

Marginal-HR floor 3/3 years; `COAL plant-grain redistribution` fired every year; the
`ERCOT zonal gas basis` log line is **absent** in all years and `run_config.json` records
`ercot_zonal_gas_basis: false`. Coal moved +3.0/+1.9/+10.3 TWh vs the keeper (BITE PASS).

## 3. Verdict against the pre-committed predictions

| prediction | result |
|---|---|
| **P1** excess vs the ercot116 envelope arm falls ≥4 pp in 2023+2024; 2025 within ±1.5 | **REFUTED**: 10.04→11.16 (+1.1), 12.87→13.83 (+1.0); 2025 13.38→13.68 (+0.3, null holds) |
| **P2** G1-as-coded passes all years | **FAILED narrowly**: −8.0 / **−4.7** / −6.9 (2024 misses the −5.0 line) |
| **P3** G3 fails via C3a (mid-merit repricing exposes the netted scarcity-low error) | **CONFIRMED**, larger than predicted: C3a −16.6→−30.9, +1.3→−16.1, +1.5→−7.1 |
| **P4** crossing-band elevation drops ≥$2.5 (2023/24), <$1 (2025) | **CONFIRMED 2023/24** ($25.23→$21.78, $24.92→$21.53); 2025 dropped $2.0 (more than predicted) |
| **P5** BITE | PASS |

Scorer gates (`ercot116_seasonal_shape.py`, verbatim): G1 **FAIL** (2024 −4.7 pp), G2 PASS
(−0.117/−0.119/−0.087, mean 0.108), G3 **FAIL**, BITE PASS. Registered NOT-YET: C3a
energy-only −40.5/−23.6/−15.7 %, C3b/C3c fail — and **C1 goes 16/16 (free 12/12)**: with the
mid-merit price repriced down, the class volume mix is the cleanest of any ERCOT arm.

## 4. What ERCOT-117 establishes

1. **The ranking bias is real and it owns the coal LEVEL over-run.** Restoring
   derivation-basis consistency drops the crossing-band price elevation by $3.4/$3.5/$2.0
   and coal by −3.7/−7.3/−2.6 TWh **vs the envelope arm under the identical measured
   envelope** (annual coal ratio 1.061/1.132/1.154 → 1.001/1.008/1.114), with the freed
   energy landing in gas (C1 16/16). The mid-merit price elevation — caused in 2023/24
   chiefly by pricing HH−0.50-derived offer multipliers on EP-anchored gas — is what let
   coal clear hours the real market cleared $4–7 cheaper.
2. **The seasonal term is NOT the ranking bias.** A season-invariant repricing of the whole
   gas surface (a ~$3.5 swing over ~3,600 mid-merit hours) left the matched-band seasonal
   excess unchanged (+1 pp) in every year. The ERCOT-116 premise "a season-invariant
   ranking bias expresses seasonally through mid-merit hour counts" is **refuted**: the
   post-envelope residual (~11–14 pp) is **price-FLAT** — the arm's summer coal gap is
   +13–15 pp (2024) / +17–19 pp (2025) in *every* actual-price band from $15 through $60+,
   while the shoulder *under*-runs −5 to −13 pp in the sub-$15 bands. Real summer coal
   delivers ~13–19 pp of envelope LESS than its own RT offered supply even at $30–60
   prices; model coal (correctly, per its exonerated curve) delivers to it. The remaining
   seasonal driver is a summer-specific, price-insensitive utilization offset — a
   quantity/operations phenomenon (ERCOT-113 §7's conclusion, now measured at the offer
   level), plus a shoulder-side base-composition defect (the model's price-taking coal base
   is 0.28 of capability vs the measured RT 0.49–0.52).
3. **The EP-anchored gas level is vindicated as an input, and the ablation can never be a
   keeper.** Without it C3a collapses (−40.5/−23.6/−15.7 % energy-only) — the measured
   delivered-gas level is required for annual price formation. Per rules 13/14 the fix is
   NOT to revert the measured gas input but to fix the root cause it exposed: **the offer
   multipliers must be re-derived on the same EP-anchored series the model dispatches on**
   (per-year tables, retiring the stale HH−0.50 normalization and the pooled p50s whose
   2025 leg carries the residual displacement). That is the ERCOT-118 program.

## 5. Successor lanes (in priority order)

1. **ERCOT-118 — re-ground the ERCOT gas offer surface on the dispatch gas basis.**
   Re-derive `derive_dam_offer_hrmults` (+ the mid-curve / cleared-share / conditional
   walls) normalized by the EP-anchored delivered-gas series, with per-year tables; re-fit
   the keeper's offer deltas on the re-grounded base. Expected yield: the +$4–7 mid-merit
   elevation and the coal LEVEL displacement close with the measured gas level KEPT; C1
   16/16 (this probe) is the volume-side upper bound of what's available.
2. **The summer price-flat coal utilization offset** (the true owner of the remaining
   seasonal term): find the driver that holds real summer coal ~13–19 pp under its own RT
   offered supply at every price — sustained-rate/duty physics not in HASL, RT down
   deviations, or operations. ERCOT-114's receipts/stock work closed fuel PRICE response;
   this is delivery/duty on the OUTPUT side.
3. **The coal price-taking base** (shoulder troughs): model 0.28 of capability vs measured
   RT 0.49–0.52 — a base-composition re-grounding on the measured TPO base share.

## 6. Declared-not-counted, honoured

No price-MAE argument is made in either direction; the C3a collapse was predicted (P3) and
is reported as the designed cost of the ablation, not evidence against the zonal basis
(rule 14 — the measured input stays); the G1 2024 miss (−4.7 vs −5.0) is reported as coded
with no post-hoc gate edit; and no keeper change is recommended in any branch — the keeper
remains `2026-07-26-ercot115-coal-marginal-hr` with the envelope default-off until the
ERCOT-118 re-grounding lets the joint arm clear G3.
