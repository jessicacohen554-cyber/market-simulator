# PRECOMMIT — miso-297 (NOT LAUNCHED: the identification failed its own pre-stated rule, §3.3) — the JOINT arm — MISO gas at marginal commodity + measured variable transport (owner-ruled form) AND the coal econ bands through the authorized channel, the multiplier identified ex ante by the IMM marginal-share census

```
STATUS  : NOT LAUNCHED. The §3.1 rules (pooling, grid, crossing) were committed at 025012a7 before the pooled curve
          existed; the joint leg's pooled coal marginal share peaks at 0.305 (m = 0.80) and never reaches the IMM
          pooled 0.3633, so by the crossing rule no m* exists, no arm table was written and no shard was launched.
          Reading and owner options: docs/records/miso/FINDING-miso297-census-identification-2026-10-01.md
LANE    : miso-297 (owner rulings 2026-10-01, miso-296 decision cards: "PRECOMMIT the joint arm (Recommended)" and
          "IMM marginal-share census (Recommended)"; FINDING-miso296 §7 named successor)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs solved at 8f765fef
ARM     : keeper recipe + THREE declared fields (§2): miso_gas_marginal_commodity_pricing=true,
          miso_gas_variable_transport=true, offer_curve_by_group replaced by the full table
          docs/records/miso/miso297-arm-offer-curve-by-group.json (keeper table sha256 6708af72b01cf4f6 ->
          arm table n/a (not written); the only cells that move are the four coal subclasses' econ_low / econ_high,
          each x m* = m*)
CONTROL : none solved. G-DRIFT 8f765fef..this SHA (§4): the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 arm legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake; every input the shards read is pinned in _miso297_shard_check.INPUT_SHA
DOF     : +0 new parameters. The existing rule-1 ledger entry (offer_curve_by_group, identified by owner ruling)
          takes a second ruling-identified value: the coal econ multiplier m*, identified by the IMM census (§3)
PHASE 0 : scripts/probes/_miso297_joint_census.py -> results/phase0/miso/_miso297_joint_census.json (zero LP)
```

## 1. The rulings, and how rule 1 (a)–(e) is met

**Owner rulings (2026-10-01, miso-296 decision cards; miso-296 could not log them, recorded verbatim here and in
`docs/calibration-log/miso.md`):**

- Card *"What should miso-297 do?"*: **"PRECOMMIT the joint arm (Recommended)"** — gas at hub + variable transport
  (owner-ruled form, O cells) PLUS a coal econ band multiplier through the authorized channel, one value all years, set
  ex ante with kill rules; then 7 shards (one per year).
- Card *"Multiplier ID"*: **"IMM marginal-share census (Recommended)"** — zero LP: the value at which the rebuilt
  stack's coal price-setting share matches the IMM SOM Table 1 coal SMP share (2019–2024, pooled). A structural
  statistic, not a gate.

The gas half is the convention the owner ruled on 2026-09-06 (miso-225 PRECOMMIT §1): a MISO gas offer is priced at
marginal commodity (the zone's measured daily hub: Chicago Citygate flow-day staircase for the Chicago and MidCon
zones, Henry Hub for MISO-South) PLUS the plant's measured variable transport (`data/raw/reference/
miso_gas_variable_transport.csv`, frozen derive). Its two standalone screens are on record: hub alone collapses coal
(miso-224, G-3/G-4 — CC_REGULAR +12.6 / COAL_PRB −11.9 TWh); with transport it passes the C1 gate and dies on the
coal-response fraction by 37 MW (miso-225, G-3). Both cells are `O` and are **never re-run alone** (matrix §5.4); this
arm is the named joint test, with the coal side now sized by FINDING-miso296 §4 (coal econ at ~$30–37 against a real
coal-marginal price of ~$15).

| rule 1 cond. | requirement | how this arm meets it |
|---|---|---|
| (a) | `offer_curve_by_group` band multipliers only | only `econ_low` / `econ_high` move, in the four coal subclasses. `committed`, `peak`, `phys_*`, `econ_low_share` and every non-coal class are byte-identical to the keeper (§2) |
| (b) | ONE config across every scored year | the same three fields and the same table for all seven legs, 2019–2025 |
| (c) | set ex ante, never swept | m* is read from the IMM census (§3) at zero LP, from a pooling rule and a crossing rule written before the curve existed; it goes into this document before any shard is launched and is never changed on a result. No gate selects it |
| (d) | merit-order adjustment is intended | coal econ tranches move down against CC and the seam ladders; that IS the object (the model's low-load margin is gas + seam, the IMM's is coal) |
| (e) | attestation `authorized_price_tuning` block + DOF ledger | §7: the block's `value` gains the coal econ multiplier with this ruling as its source; the ledger entry is amended, no new free parameter |

## 2. The arm (exactly three fields; one config for 2019–2025)

| field | keeper | arm | what it does |
|---|---|---|---|
| `miso_gas_marginal_commodity_pricing` | false | **true** | every MISO gas row priced at its zone's daily hub (`data.fuel.basis.miso.apply_miso_gas_marginal_commodity`); supersedes the EIA-923 average print, the winter shape overlay, the winter daily-delivered form (`miso_winter_gas_daily_delivered`, keeper `true`, never reached when this is armed — `run_calibration.py` ~5177, rule 19) and the zonal increment on those rows |
| `miso_gas_variable_transport` | false | **true** | adds the plant's measured variable transport over the hub (own-plant rung, else zone\|group, group, MISO-wide — the declared ladder of the frozen derive). Refused without the first field |
| `offer_curve_by_group` | keeper table | **arm table** | the four coal subclasses' `econ_low` and `econ_high` × m* (eight cells, §2.1). Nothing else |

`miso_winter_gas_daily_delivered` stays `true` in the recorded config and is INERT by construction under the first
field (the applier returns before it is called); the shard check requires its log line ABSENT and the
marginal-commodity line PRESENT **with** the transport clause (the bare-hub clause is the killed miso-224 form).

### 2.1 The table delta (eight cells; `committed` and `peak` held)

| class | committed (held) | econ_low keeper → arm | econ_high keeper → arm | peak (held) |
|---|---:|---:|---:|---:|
| COAL_PRB | 1.1 | 1.1 → 1.1·m* | 1.309 → 1.309·m* | 1.628 |
| COAL_BIT | 1.1 | 1.1 → 1.1·m* | 1.21 → 1.21·m* | 1.595 |
| COAL_LIGNITE | 1.1 | 1.254 → 1.254·m* | 1.265 → 1.265·m* | 1.705 |
| COAL_WC | 1.1 | 1.1 → 1.1·m* | 1.122 → 1.122·m* | 1.32 |

(`scripts/probes/_miso297_arm_table.py --m <m*>` writes the table and asserts exactly these eight cells move. **Not written: no m* was identified (§3.3).**)


**Why the econ bands only, and not all four as miso-275 did.** miso-275 undid a uniform lift, so it moved the four
bands uniformly. The owner-ruled identification here is the *marginal share*, and the IMM evidence is specific about
which coal is marginal: regulated coal that self-commits and is dispatchable above its schedule at its incremental
offer, "generally in off-peak hours" (SOM 2020 Table 1; SOM 2024 Table 7). In the keeper that increment is the econ
ramp (`econc00`–`econc05`, the six-step ramp between `econ_low` and `econ_high` — `offer_curves.py` ~542, so scaling
both by m scales every step by m). The `committed` band is the take-or-pay schedule itself (priced at ~$9 on its own
basis, infra-marginal at every load level: FINDING-miso296 §5 — it is marginal in 12 % of coal-marginal hours only
because it is reached before the econ ramp); moving it would not change which coal is marginal and would re-price a
quantity the IMM evidence says is self-scheduled. The `peak` band (1.6–1.7 × HR, ~$45+) is the top of the coal stack,
marginal in ≤ 2 % of coal-marginal hours and never off-peak; the evidence does not speak to it. So m applies to
`econ_low` and `econ_high` of COAL_PRB / COAL_BIT / COAL_LIGNITE / COAL_WC and to nothing else. Under
`coal_econ_srmc_bound` (keeper `true`) the coal FUEL passthrough of a marginal tranche is clamped ≥ 1.0; that clamp
acts on the delivered fuel price, not on the band multiplier, so the LP builds exactly the offer the census scaled
(`offer = base_hr × mult × delivered_fuel + VOM`; residual 0.00 on every coal econ row, §3.2).

## 3. The identification (zero LP; every number in `results/phase0/miso/_miso297_joint_census.json`)

### 3.1 Rules fixed before the curve existed

- **Statistic.** The share of hours in which a coal row is the marginal row of the P1 bid stack (base offers + the
  miso-287 startup markup recomputed from each P0 clear) cleared at the keeper's own P1 thermal quantity every hour —
  the miso-296 block-B construction, which reproduces the keeper's shares (2020: 0.254 vs 0.25 published).
- **Pooling.** Hours-weighted over the six published years 2019–2024. Every model year is 8760 hours, so this is the
  equal-year mean: IMM pooled coal = mean(0.47, 0.40, 0.35, 0.24, 0.36, 0.36) = **0.3633**. (2025 is unpublished and
  is solved but not pooled.)
- **Grid and crossing.** m ∈ {1.00, 0.95, …, 0.30}. On the JOINT leg (ruled gas form armed), m* is the first m,
  descending from 1.00, at which the pooled share reaches 0.3633, linearly interpolated between the bracketing grid
  points and rounded to 2 decimals so the shards carry it exactly. If the curve never reached it, no arm would be
  launched and the owner would get a card.
- **Legs.** coal-only (keeper gas, m scanned) and joint (ruled gas, m scanned); gas-only = joint at m = 1.00;
  keeper = coal-only at m = 1.00.

### 3.2 What the rebuild measured (identities)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| LP rows (fleet-only rebuild) | 3010 | 2998 | 2982 | 2983 | 2743 | 2727 | 3218 |
| gas fuel cap-wtd, keeper print → ruled form $/MMBtu | 2.958 → 3.299 | 2.441 → 2.748 | 4.855 → 5.053 | 6.882 → 7.203 | 3.076 → 3.121 | 2.757 → 2.903 | 3.871 → 4.066 |
| CC_REGULAR fuel cap-wtd, keeper → ruled | 2.686 → 2.796 | 2.238 → 2.306 | 4.529 → 4.616 | 6.670 → 6.809 | 2.920 → 2.675 | 2.606 → 2.477 | 3.674 → 3.626 |
| CC_REGULAR econ: max |Δmc − HR·Δfuel| $/MWh | 6.69 | 1.65 | 2.12 | 3.89 | 3.44 | 1.80 | 1.87 |
| non-gas rows identical between legs | yes | yes | yes | yes | yes | yes | yes |
| coal econ rows / cap GW (mean) | 498 / 14.5 | 462 / 11.7 | 462 / 12.7 | 438 / 11.8 | 324 / 8.6 | 300 / 8.6 | 492 / 9.1 |
| coal econ offer cap-wtd = HR·fuel + VOM + resid | 31.2 = 26.7 + 4.5 + 0.00 | 34.9 = 30.4 + 4.5 + 0.00 | 38.0 = 33.5 + 4.5 + 0.00 | 34.7 = 30.2 + 4.5 + 0.00 | 36.7 = 32.2 + 4.5 + 0.00 | 35.6 = 31.1 + 4.5 + 0.00 | 34.8 = 30.3 + 4.5 + 0.00 |

Reading: the two legs differ on gas rows only; the CC_REGULAR econ offer moves by exactly HR × Δfuel up to the few-$ rows the dual-fuel oil-parity cap touches (max-abs column). The coal econ residual is 0.00 in every year, so `offer(m) = offer − HR·fuel·(1 − m)` is exact. **The ruled gas form RAISES the gas fuel level in 2019–2022** (own-plant variable transport $0.24–0.36/MMBtu cap-weighted on CC_REGULAR, $0.71–0.84 on all gas, against a print-over-hub wedge of $0.13–0.39 in those years) **and lowers CC_REGULAR in 2023–2025** (−$0.25 / −$0.13 / −$0.05) — the opposite sign from the 2023-only miso-225 screen in the early years.


### 3.3 The census curve (pooled 2019–2024 bid-stack coal marginal share; IMM pooled 0.3633)

| m | coal-only pooled | joint pooled (P1 bid) | joint P0 | joint 2019 | joint 2020 | joint 2021 | joint 2022 | joint 2023 | joint 2024 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.00 | 0.274 | **0.284** | 0.257 | 0.462 | 0.275 | 0.384 | 0.161 | 0.221 | 0.204 |
| 0.95 | 0.281 | **0.288** | 0.265 | 0.474 | 0.289 | 0.368 | 0.152 | 0.228 | 0.216 |
| 0.90 | 0.292 | **0.296** | 0.274 | 0.492 | 0.304 | 0.365 | 0.142 | 0.241 | 0.230 |
| 0.85 | 0.292 | **0.303** | 0.279 | 0.500 | 0.342 | 0.355 | 0.129 | 0.254 | 0.240 |
| 0.80 | 0.298 | **0.305** | 0.287 | 0.486 | 0.376 | 0.339 | 0.122 | 0.256 | 0.252 |
| 0.75 | 0.296 | **0.302** | 0.284 | 0.476 | 0.384 | 0.330 | 0.107 | 0.261 | 0.257 |
| 0.70 | 0.288 | **0.297** | 0.284 | 0.466 | 0.397 | 0.293 | 0.107 | 0.257 | 0.261 |
| 0.65 | 0.274 | **0.282** | 0.271 | 0.425 | 0.398 | 0.264 | 0.103 | 0.246 | 0.256 |
| 0.60 | 0.257 | **0.267** | 0.259 | 0.375 | 0.399 | 0.234 | 0.097 | 0.239 | 0.257 |
| 0.55 | 0.232 | **0.241** | 0.235 | 0.319 | 0.362 | 0.209 | 0.096 | 0.222 | 0.238 |
| 0.50 | 0.207 | **0.216** | 0.213 | 0.265 | 0.338 | 0.183 | 0.098 | 0.192 | 0.222 |
| 0.45 | 0.175 | **0.183** | 0.180 | 0.207 | 0.289 | 0.157 | 0.096 | 0.155 | 0.195 |
| 0.40 | 0.149 | **0.161** | 0.157 | 0.190 | 0.245 | 0.147 | 0.096 | 0.121 | 0.166 |
| 0.35 | 0.125 | **0.133** | 0.129 | 0.166 | 0.181 | 0.135 | 0.094 | 0.094 | 0.129 |
| 0.30 | 0.107 | **0.116** | 0.111 | 0.149 | 0.149 | 0.132 | 0.093 | 0.080 | 0.095 |
| IMM | 0.363 | 0.363 | 0.363 | 0.47 | 0.40 | 0.35 | 0.24 | 0.36 | 0.36 |


**Declared value: m* = **none** — the joint leg's pooled share never reaches 0.3633: it rises from 0.285 (m = 1.00) to a maximum of **0.305 at m = 0.80** and falls to 0.116 at m = 0.30; the coal-only leg peaks at 0.298 (m = 0.80). By the crossing rule fixed in §3.1 **no arm is launched**** (the pooled maximum falls 0.058 short of the IMM; the low-gas years 2020 / 2023 / 2024 rise toward the IMM (2020 reaches 0.40 at m = 0.70) while 2019 / 2021 / 2022 fall as their coal econ ramp drops below gas and becomes fully infra-marginal; one value cannot serve both regimes)

### 3.4 Per-year shares at m* (joint leg) beside the IMM and the keeper

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMM SMP coal | 0.47 | 0.4 | 0.35 | 0.24 | 0.36 | 0.36 | n/a |
| keeper stack (coal-only m=1.00): coal all-hours | 0.432 | 0.254 | 0.371 | 0.177 | 0.215 | 0.197 | 0.277 |
| keeper stack (coal-only m=1.00): coal q1 / q5 | 0.16 / 0.63 | 0.07 / 0.48 | 0.38 / 0.28 | 0.32 / 0.06 | 0.11 / 0.29 | 0.07 / 0.34 | 0.22 / 0.17 |
| gas-only (joint m=1.00): coal all-hours | 0.462 | 0.275 | 0.384 | 0.161 | 0.221 | 0.204 | 0.282 |
| gas-only (joint m=1.00): coal q1 / q5 | 0.20 / 0.63 | 0.08 / 0.50 | 0.41 / 0.29 | 0.29 / 0.06 | 0.10 / 0.33 | 0.08 / 0.34 | 0.25 / 0.15 |
| joint m=0.80 (pooled max): coal all-hours | 0.486 | 0.376 | 0.339 | 0.122 | 0.256 | 0.252 | 0.239 |
| joint m=0.80 (pooled max): coal q1 / q5 | 0.35 / 0.55 | 0.17 / 0.57 | 0.51 / 0.14 | 0.28 / 0.02 | 0.16 / 0.27 | 0.14 / 0.33 | 0.31 / 0.08 |
| joint m=0.70: coal all-hours | 0.466 | 0.397 | 0.293 | 0.107 | 0.257 | 0.261 | 0.189 |
| joint m=0.70: coal q1 / q5 | 0.47 / 0.44 | 0.26 / 0.49 | 0.53 / 0.09 | 0.27 / 0.01 | 0.21 / 0.24 | 0.16 / 0.26 | 0.28 / 0.06 |
| keeper P1 (miso-296 published) | 0.42 | 0.25 | 0.37 | 0.19 | 0.21 | 0.20 | 0.28 |


### 3.5 Why both halves are needed (the legs)

| leg | pooled coal share 2019–2024 | what it says |
|---|---:|---|
| keeper (print gas, m = 1.00) | 0.274 | reproduces miso-296 block B within ±0.013 (2020 exact) |
| gas-only (ruled form, m = 1.00) | 0.284 | +0.010: the ruled form does NOT take coal's margin at zero LP — it raises CC fuel in 2019–2022 (§3.2) and lowers it only in 2023–2025 |
| coal-only maximum (print gas, m = 0.80) | 0.298 | the coal lever alone peaks 0.065 short |
| joint maximum (ruled gas, m = 0.80) | 0.305 | both together peak 0.058 short; the gas form adds ~0.01 at every m |


### 3.6 Merit-order consequence and the static price move at m* (joint leg vs keeper stack)

| joint m = 0.80 minus keeper stack (static, mean GW; ×8.76 = TWh/yr) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| coal | +3.00 | +1.88 | +2.05 | +0.73 | +1.31 | +1.33 | +1.60 |
| coal econ | +3.27 | +2.00 | +2.25 | +0.80 | +1.48 | +1.44 | +1.76 |
| CC_REGULAR | -1.85 | -1.12 | -1.65 | -0.68 | +0.11 | -0.24 | -0.98 |
| gas (all) | -2.30 | -1.69 | -1.84 | -0.76 | -0.60 | -0.88 | -1.23 |
| seam imports | -0.69 | -0.19 | -0.20 | +0.03 | -0.71 | -0.45 | -0.38 |
| coal econ dispatched share, keeper → m 0.80 | 0.28 → 0.50 | 0.18 → 0.35 | 0.59 → 0.77 | 0.89 → 0.96 | 0.32 → 0.49 | 0.26 → 0.42 | 0.59 → 0.79 |


| static bid-stack price, $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| actual q1 / q2 median | 19.2 / 21.2 | 15.1 / 17.1 | 23.3 / 25.8 | 40.2 / 48.4 | 19.6 / 23.1 | 16.9 / 20.4 | 24.2 / 27.7 |
| keeper stack: q1 / q2 / q5 median | 22.5 / 25.1 / 29.9 | 18.2 / 21.4 / 27.2 | 27.4 / 29.9 / 36.4 | 41.1 / 45.8 / 62.0 | 25.4 / 28.6 / 36.5 | 21.5 / 24.9 / 34.4 | 30.5 / 33.7 / 46.4 |
| keeper stack: LW err all / q1–q2 | +1.38 / +2.87 | +1.80 / +3.33 | -4.77 / -0.48 | -12.43 / -1.72 | +1.69 / +4.82 | +0.55 / +3.56 | -2.74 / +3.19 |
| gas-only: q1 / q2 / q5 median | 23.3 / 25.8 / 30.1 | 19.1 / 21.6 / 27.8 | 27.8 / 30.3 / 37.6 | 42.1 / 47.1 / 62.9 | 24.5 / 27.7 / 36.4 | 20.8 / 25.0 / 34.6 | 30.7 / 33.6 / 46.3 |
| gas-only: LW err all / q1–q2 | +1.84 / +3.41 | +2.24 / +3.81 | -4.36 / -0.13 | -11.62 / -0.54 | +1.22 / +4.06 | +0.45 / +3.17 | -2.60 / +3.18 |
| joint m 0.80: q1 / q2 / q5 median | 22.4 / 24.0 / 26.8 | 18.6 / 20.9 / 25.3 | 25.2 / 27.8 / 37.1 | 41.1 / 46.6 / 62.7 | 24.3 / 27.1 / 34.2 | 20.6 / 24.6 / 32.2 | 29.1 / 31.4 / 46.2 |
| joint m 0.80: LW err all / q1–q2 | -0.31 / +2.00 | +0.86 / +3.22 | -5.77 / -2.00 | -12.24 / -1.63 | +0.05 / +3.35 | -0.66 / +2.67 | -3.80 / +1.78 |
| joint m 0.70: q1 / q2 / q5 median | 21.3 / 22.5 / 26.0 | 18.2 / 20.5 / 23.7 | 23.6 / 26.9 / 36.8 | 40.6 / 46.4 / 62.8 | 23.9 / 26.4 / 33.8 | 20.4 / 23.9 / 31.4 | 27.9 / 30.8 / 46.2 |
| joint m 0.70: LW err all / q1–q2 | -1.35 / +1.03 | -0.03 / +2.69 | -6.34 / -2.98 | -12.45 / -2.08 | -0.60 / +2.81 | -1.29 / +2.25 | -4.22 / +1.12 |
| startup markup at the q1–q2 margin (median) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |


Reading rules: these are static re-merits at a fixed thermal quantity. miso-224/225 measured the LP's coal response at
0.27–0.275× the static prediction (commitment structure holds coal where the static stack does not), so the LP's
dispatch move is expected to be smaller than the table and its price move correspondingly different; the shards
decide. The quintile-1 overshoot is the C3a 2020 object (FINDING-miso296 §1); the West/Plains ~4.4 of 11.6 points
(`internal_congestion_split`, G) are not this arm's and remain at full magnitude.

### 3.7 Transport-table coverage of the 2019–2022 fleets (the table was derived on 2023–2025 receipts)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gas plants in fleet / with own-plant rung | 321 / 89 | 324 / 93 | 321 / 95 | 322 / 98 | 324 / 100 | 327 / 100 | 350 / 102 |
| gas capacity on own-plant rung | 68 % | 68 % | 70 % | 72 % | 73 % | 73 % | 74 % |
| CC_REGULAR capacity on own-plant rung | 86 % | 86 % | 88 % | 89 % | 91 % | 90 % | 91 % |
| v cap-wtd: CC_REGULAR / all gas $/MMBtu | 0.35 / 0.84 | 0.36 / 0.81 | 0.28 / 0.72 | 0.26 / 0.75 | 0.25 / 0.71 | 0.26 / 0.72 | 0.24 / 0.71 |
| CT_PEAKER / ST_GAS own-plant share | 64 % / 77 % | 65 % / 76 % | 66 % / 79 % | 66 % / 82 % | 67 % / 86 % | 66 % / 84 % | 67 % / 88 % |


Fallback, named: a plant absent from the table takes the declared ladder of the frozen derive — its `zone|group` pooled
rung, else its `group` rung, else the MISO-wide $0.5036 (`.pool.csv`). That is the mechanism's own documented
behaviour for every year, not a choice made here; the shares above say how much of each year's gas capacity is on the
own-plant rung. No re-derive (rule 23: no source-data update).

## 4. G-DRIFT — keeper legs `8f765fef` vs this SHA (rule 29(b))

Full hunk table: `docs/records/miso/GDRIFT-miso297-keeper-8f765fef-2026-10-01.md` (190 files in scope, +94,930 / −1,466;
81,217 of the additions are one ERCOT CSV). **Every hunk is INERT for a `replay_keeper.py` replay of the MISO 2019–2025
recipe; 0 LIVE.** Form 4 holds: the committed keeper is the control.

| hunk group | class | reason |
|---|---|---|
| `ScenarioConfig`: 37 new fields, all `False`, absent from the recipe; 0 changed defaults; `nyiso_firm_imports` removed (MISO meta records `None`, rule-26 inert list) | INERT | AST diff of the class, keeper vs HEAD |
| `constants.py` +505/−88: new names; `ISO_BA_JOINS` gains a PJM key; `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` | INERT | per-ISO dicts with no MISO row / ERCOT-tokened; `solve_surface_register.py --diff 8f765fef HEAD`: 19 names added (declared, move no key), MISO moved rows **0** |
| `lp/rows.py` coal-yard cumulative rows; `fleet/floors.py` net-load drag targets; dispatched-bin rosters; outage accumulator; `_bridge_floored_fleet`; `campd_fuel_split_selector`; `import_node_links("MISO")`; `_joining_ba_generators`; `apply_dual_fuel_pricing(skip_cells=None)`; `shed_penalty_voll`; `apply_cc_committed_offer_margin`; the four `p1_fleet_prep` chains | INERT | each traced to a byte-identical default branch under the keeper recipe (`n_cp_months == 1`, `k_plant={}`, `live_year=None`, `dated_bin_shares=None`, bool path, unchanged tail, same list, `[]`, early return, `miso_gas_ecomin_online_floor` off) |
| SPP-102/104/105/106, PJM-NEXT-7/8/16/17, NYISO-NEXT-11/15/17/23/25, R-CAISO-11/13/17/18/20, R-ERCOT-12/14/18/19/20/22/23, soco-96 | INERT | gated `iso == "<other>"` |
| forecast-only (capacity evolution, ensemble, uncertainty, structural prior), exports, argparse/tooling, ≈90 citation-only files (`docs/handoffs/…` → `docs/records/…`) | INERT | not on the backcast solve path / zero non-comment lines |
| `scripts/lib` (42 files, 10 new modules) | INERT | none imported by the three solve scripts (`run_calibration_full.py` imports only `bundle_io` and `solve_container`, both unchanged) |
| `data/raw/reference` (9 files): ERCOT custom bins / registry / DAM crosswalk, SOCO state weights, NWPP plant basis, NYISO solar split, PJM coal replacement + gas transport | INERT | each reader keyed on its own ISO |
| `data/raw/_validation-source/actual_lmp.json` MISO `rt_lw*` / `da_lw*` / `src_lw` (miso-294 zone-resolved basis) | INERT for the solve | read by the scorer, never by the replay; `actual_lmp_hourly_MISO.parquet` unchanged |
| **This arm's own fields and data**: `apply_miso_gas_marginal_commodity`, `_miso_gas_variable_transport_vector`, both field declarations, the transport table + pool, the zone→hub map, both daily hub series | byte-identical | AST-sliced sha256 equal; `git diff --stat` empty |

Record-only differences a HEAD replay shows (not solve-affecting): `solve_surface.fingerprint`/`rows` (shared names added to
the projected set; the key's `moved` set is the keeper's seven), `meta.json` gains four `None` kwargs and loses
`nyiso_firm_imports`, `scenario_config` gains the 37 `False` fields.

## 5. Predictions and kill rules (fixed now; directions only, never a value selected on them)

Predictions:

1. **CC_REGULAR** falls in 2019–2021 (coal econ below CC econ in more hours) and is near flat in 2023–2025 where the
   ruled gas form lowers CC fuel by ~$0.4–0.6/MMBtu (§3.2); **COAL_PRB / COAL_BIT** rise in every year, most in
   2019/2021/2022 where their headroom to the +8 TWh band is smallest (+6.40 / +5.69 / +5.28; COAL_BIT 2022 +5.69).
2. **Price** falls in load quintiles 1–4 where coal econ now sits at the margin, and in quintile 5. C3a 2020 improves
   in direction; C3a 2021 / 2022 / 2025 (already −5.6 / −5.1 / −1.1 %) move further negative.
3. **Imports** fall (the seam ladders go out of merit as the internal price falls, miso-224/225).
4. **ST_GAS** falls further from actual (dearer relative to coal and CC; miso-225 §3.2).
5. **C3b 2021** (storm month + fall conservation, routed) does not change status.

Kill rules (the arm is KILLED, no promotion recommended, if any fires):

- **K-1 no C1 class PASS→FAIL in any year** (band ±8 TWh / ±3 pp; 2025 C1 cells are SKIPPED by the preliminary
  vintage and are reported from the C2 family reconcile instead).
- **K-2 C1 COAL_PRB, COAL_BIT, COAL_LIGNITE and CC_REGULAR within band in every year, or moving toward actual.**
- **K-3 the model's coal marginal share** (the §3.1 statistic, recomputed on each leg's own P1 at its own thermal
  quantity — `_miso297_shard_readout.py`) **moves toward the IMM share in ≥ 5 of the 6 published years.**
- **K-4 the quintile-1–2 load-weighted price error shrinks in the low-gas years 2019, 2020, 2023 and 2024** (zone-
  resolved actual, measured zonal demand — the miso-296 block-A construction).
- **C3a 2020 is REPORTED at full magnitude and is not a gate**; nothing in this document is selected on it.
- Structural stops: S-1 recipe (every leg = keeper + exactly §2, shard check HARD 1), S-1b the seven `-splitremap-`
  companions read, S-2 log (marginal-commodity line WITH transport; winter-delivered and bare-hub lines ABSENT), S-3
  slack reported with its hours.

REPORTED-ONLY (never gates here): C3a 2022 (routed miss; the Elliott tail), C3b 2021 (Uri routed + Sep–Nov coal
conservation, not carriable), C1 ST_GAS 2019 (routed, South steam out of merit), West/Plains congestion (G), C3c
(ledgered caveat), D-A amplitude.

## 6. Decision rule and the promotion question's form

Every gate C1–C8 is reported per year, both runs, at full magnitude. If no kill rule fires and the full-span
determination is not worse than the keeper's (same three or fewer failing criterion-years), the RESULT recommends
promotion and the owner is asked, as a decision card: *"Promote 2026-10-01-miso-297-joint-gas-coal over
2026-09-28-miso-280-splitremap?"* with the gate table beside it. If a kill rule fires, the RESULT says KILLED, names
the rule and the number, moves `gas_marginal_commodity_pricing` / `gas_variable_transport` off `O` on the scored
result (the joint test the `O` verdicts waited for has then been run), and asks the owner what the next lane is.
Promotion is the owner's (rule 31); no solved bundle is deleted before the ruling.

## 7. DOF ledger and attestation text (written into the composite before the PR)

`governance.authorized_price_tuning` (keeper block, amended):

- `value`: "x1.10 on committed/econ_low/econ_high/peak for 8 non-steam fossil classes (…unchanged…); PLUS, miso-297:
  the four coal subclasses' econ_low / econ_high x m* = m* (COAL_PRB 1.1/1.309 -> ·m*/·m*, COAL_BIT
  1.1/1.21 -> ·m*/·m*, COAL_LIGNITE 1.254/1.265 -> ·m*/·m*, COAL_WC 1.1/1.122 ->
  ·m*/·m*); committed and peak held; phys_* and econ_low_share/pct_peaking untouched in every class"
- `ruling`: appended "— coal econ bands by owner ruling 2026-10-01 (miso-296 cards): 'PRECOMMIT the joint arm
  (Recommended)' + 'IMM marginal-share census (Recommended)'"
- `prereg`: appended "; docs/records/miso/PRECOMMIT-miso297-joint-gas-coal-2026-10-01.md @ <pin>"
- `dof_entry`: appended "; coal econ multiplier m* = m* identified by the IMM SOM Table 1 coal SMP share pooled
  2019–2024 (0.3633) on the zero-LP bid-stack census (miso-297, no new parameter: a second ruling-identified value on
  the same entry)"
- `years_held_basis`: this run's own seven single-year legs pinned to <pin>; table sha n/a (not written) byte-identical in
  all seven (composer MUST_AGREE).
- `mechanism_armed`: replaced by the miso-297 block (fields, level "m* = m* from the IMM census; transport
  table = the frozen derive, zero fitted scalars", basis, one_mechanism (rule 19: the hub form supersedes the print,
  the winter overlay, the winter daily-delivered form and the zonal increment on gas rows), control, prereg).
- A `miso297` block (precommit, pin, delta, ruling, legs, control, dof_added 0).

DOF ledger (`build_dof_ledger.py` entry `offer_curve_by_group`): identification stays the rule-1 channel; the ruling
text above is its source. **DOF +0.**

## 8. Arm command, shard check, compose

Per year Y, one shard each (`scripts/shard_prompt.py --iso MISO --all-years --sha <pin> --lane miso-297
--bundle results/calibration/miso280_span --set … --note …`):

```
python3 scripts/replay_keeper.py results/calibration/miso280_span --years <Y> \
  --out-dir results/calibration/miso_297_<Y> \
  --set miso_gas_marginal_commodity_pricing=true \
  --set miso_gas_variable_transport=true \
  --set "offer_curve_by_group=$(cat docs/records/miso/miso297-arm-offer-curve-by-group.json)" \
  --note "miso-297 joint arm <Y>: gas at hub + variable transport (owner-ruled form) + coal econ bands x m* (IMM census)"
```

Shard check: `scripts/probes/_miso297_shard_check.py --leg results/calibration/miso_297_<Y> --year <Y> --log <log>`
(recipe = keeper + exactly §2 incl. the table; the seven `-splitremap-` companions; pinned inputs incl. the two daily
hubs, the transport table + pool and the zone→hub map; vintage; classifier; log markers). Compose:
`scripts/probes/_miso297_compose_span.py` (MUST_AGREE now carries the two gas fields; `offer_curve_by_group` since
miso-275). Score: `scripts/calibration_verdict.py`; `scripts/legitimacy_diagnostics.py`; the K-3/K-4 readout
`scripts/probes/_miso297_shard_readout.py`.

## 9. Launch record

No shard launched (STATUS block). §5–§8 stand as the arm's pre-registered form should the owner re-identify m by a
new ex-ante rule (FINDING-miso297 §4 options); any such re-identification is a new ruling recorded before any shard.
