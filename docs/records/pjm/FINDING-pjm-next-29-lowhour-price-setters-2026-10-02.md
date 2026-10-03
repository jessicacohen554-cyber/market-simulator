# FINDING — PJM-NEXT-29: who sets the model's price in PJM's real low-price hours (zero LP)

**Keeper unchanged:** `2026-10-02-w0-pjm-fix2` (bundle `w0_pjm_span`). **Zero LP, zero shards.**
Probe `scripts/probes/_pjmnext29_lowhour_setters.py` → `results/phase0/pjm/_pjmnext29_lowhour_setters.json`.
Lane: COAL_BIT side card (a) is OPEN. The excess is within-plant econ-band loading, and at PJM's own offers it is
driven by the model's price level in sub-$25 hours (NEXT-17 1b). The model's p10 implied HR is 7.0–8.5 × gas against
4.8–5.5 real. Committed rungs are not the price-setters (NEXT-28). This FINDING asks which tranches are.

## §1 Readings, fixed ex ante (written and committed before any number was computed)

**Population.** `L_y` is the set of hours where the real PJM DA LMP / delivered gas < 6.5. Sources:
`actual_lmp_hourly_PJM.parquet` `da`; gas from the NEXT-11 series (HH daily ffill + `GAS_BASIS_DIFFERENTIAL['PJM']`);
hour axis is hour-of-year at lag 0, the `_pjmnext11` convention. Fail years are 2019/20/21 (COAL_BIT C1 +22/+16/+18
TWh) and controls are 2023/24 (COAL_BIT within gate). All seven years are reported.

**Attribution.** As in NEXT-28: each zone-hour is anchored to the hour's `marginal == 1` unit with the nearest
`mc` in ratio, within `ANCHOR_TOL` = 0.06. A cell is `plant_group` × tranche, where the tranche comes from the unit-id
suffix: `econcNN`→econc, `econlo`, `econhi`, `peak`, `committed`, `mustrun`, `sync`, else `other`. Zone-hours carry
load weights; zone `PJM_external` and interchange pseudo-units are excluded.

- **R1 — model price-setters in `L_y`.** The load-weighted share of anchored `L_y` load by cell, plus the
  unanchored share. `T*` is the smallest set of cells covering ≥ 60 % of anchored `L_y` load, pooled over 2019–21.
  Reading: **concentrated** iff `|T*|` ≤ 3.
- **R2 — fuel alignment against the IMM.** IMM Marginal Fuel Postings (time-weighted) are averaged over `L_y`, by
  fuel. They are compared with the model's anchored `L_y` attribution mapped to the same fuels (gas, coal, nuclear,
  wind/solar, other). Reading: a fuel is **mis-assigned** iff |model − IMM| ≥ 0.15 in two or more of 2019/20/21.
- **R3 — offer level of the setters.** For each `T*` cell, the median `mc`/gas over its anchored `L_y` hours is
  compared with the median real DA LMP/gas over the same zone-hours. The reported gap is Δ = model − real (implied
  MMBtu/MWh).
- **R4 — the stranded band (which capacity sits between the real price and the model's).** For each `L_y` hour, take
  the P1 thermal units with `cap_mw` > 0 and `p_real < mc ≤ p_model`, where `p_model` is the load-weighted model
  price. Report their mean MW by cell, and COAL_BIT's own dispatched MW in that band. Reading: a cell is **stranding**
  iff it holds ≥ 25 % of the band's mean MW in two or more fail years.
- **R5 — PJM's own offers (fleet-level; the feed is unit-masked, so it carries no plant identity).** For 2019, 2021 and
  2024 `L_y` hours, take the offer-implied MW at or below the real DA LMP (`_pjmnext11_offered_ecomax.offer_dispatch`,
  summed over all offering units). Compare it with the model's capacity at `mc ≤ p_real`: P1 units excluding
  interchange; VRE, hydro and nuclear at their hourly `cap_mw`. Report ΔQ = PJM − model in GW (median hour).
  Reading: **quantity-short** iff median ΔQ ≥ 5 GW in 2019 and 2021. Population caveat: PJM offers include units
  with no model counterpart, and the model carries no virtuals or imports here, so this reading is a bound, not an
  identity.

**Decision rule (ex ante).**
- If R1 is concentrated and R4 names the same cell(s) as stranding, that cell's offer level is the next lever
  candidate. It is chartered only if R3's Δ for it is ≥ 1.0 and its rung is not an `R`/`I`/`G` matrix cell without new
  evidence.
- If R2 flags gas as model-high and coal as model-low (real low hours coal-set), the floor is a coal-offer-level
  object. The real coal setters then offer below the model's coal econ rungs.
- If R5 is quantity-short, the object is supply availability below the real price, not offer level, and R4 names
  where the missing quantity would have to come from.
- Otherwise, record the attribution and keep card (a) OPEN.

## §2 Result

Probe output: `results/phase0/pjm/_pjmnext29_lowhour_setters.json`.

- Real low hours `L_y` are 30 / 37 / 32 / 19 / 20 / 18 / 19 % of hours in 2019–25. The model prices 0–3.4 % of hours
  that low.
- Median implied HR inside `L_y`, real vs model: 5.8 vs 7.2 (2019), 5.5 vs 7.6 (2020), 5.7 vs 7.3 (2021).
- Anchored share of `L_y` load: 70–72 % in 2019–22 and 51–57 % in 2023–25.

**Price-setters in `L_y`.** Load-weighted share of anchored load:

| year | COAL_BIT econc | CC_REGULAR econc | CC_REGULAR committed | ST_CHP committed |
|---|---|---|---|---|
| 2019 | .38 | .30 | .12 | .06 |
| 2020 | .33 | .32 | .11 | .09 |
| 2021 | .28 | .36 | .12 | .11 |
| 2022 | .11 | .40 | .20 | .09 |
| 2023 | — | .41 | .10 | .13 |
| 2024 | .11 | .27 | — | .18 |
| 2025 | .20 | .27 | .07 | — |

**Model vs IMM marginal fuel in `L_y`:**

| year | model coal | IMM coal | model gas | IMM gas |
|---|---|---|---|---|
| 2019 | .48 | .24 | .52 | .70 |
| 2020 | .39 | .19 | .61 | .72 |
| 2021 | .34 | .20 | .66 | .71 |
| 2022 | .14 | .09 | .86 | .78 |
| 2023 | .12 | .07 | .88 | .85 |
| 2024 | .20 | .10 | .80 | .75 |
| 2025 | .24 | .09 | .76 | .71 |

IMM VRE is .04–.18; the model has no VRE price-setter in these hours.

**R3, median implied HR, setter offer vs real price** (2019 / 2020 / 2021):

| cell | 2019 | 2020 | 2021 |
|---|---|---|---|
| COAL_BIT econc | 7.18 vs 5.89 | 7.85 vs 5.84 | 7.35 vs 5.78 |
| CC_REGULAR econc | 7.20 vs 5.79 | 7.52 vs 5.53 | 7.32 vs 5.77 |

Δ is +1.3…+2.0 in these years, and +1.9…+3.2 in 2023/24.

**R4 stranded band.** The mean thermal MW with `p_real < mc ≤ p_model` is 24–31 GW in every year:
- CC_REGULAR committed holds 42–54 % of it, and CC_REGULAR econc 26–38 %.
- COAL_BIT econc dispatch inside the band is 10.0 / 7.0 / 14.5 TWh in 2019 / 20 / 21, against 0.6 / 0.8 in 2023 / 24.

**R5 offers.** PJM offered MW at ≤ real LMP, against model capacity at `mc ≤ p_real`, as the median `L_y` hour:

| year | PJM offered | model capacity | ΔQ (IQR) |
|---|---|---|---|
| 2019 | 89.1 GW | 50.5 GW | 34.0 GW (27.8–42.8) |
| 2021 | 97.7 GW | 50.3 GW | 45.5 GW (40.3–49.5) |

PJM's offered quantity exceeds load. The model's quantity at the real price falls ~25 GW short of load, so its price
must rise above `p_real`. The ΔQ magnitude is a population bound, not an identity: offline units also carry offer
rows (NEXT-17).

### Readings

| reading | result |
|---|---|
| R1 | **Concentrated.** `T*` = {COAL_BIT:econc, CC_REGULAR:econc}, covering 0.66. |
| R2 | **Coal mis-assigned** (model − IMM +.24 / +.20 / +.14 in 2019 / 20 / 21; ≥ 0.15 in two of three). Gas not flagged. |
| R3 | CC_REGULAR econc Δ ≥ 1.0 in every year. |
| R4 | **Stranding:** CC_REGULAR committed and CC_REGULAR econc. |
| R5 | **Quantity-short** (≥ 5 GW in 2019 and 2021). |

**Decision rule, applied:**
- R1 ∩ R4 = CC_REGULAR econc. R3 passes. R5 says the same thing as a quantity: CC rungs sit above the real price,
  where PJM's offered stack does not.
- Every channel that sets that rung's level is already adjudicated:
  - `offer_curve_by_group`: K; econ_low 0.96 is the rule-1 band.
  - `pjm_midcurve_belt`: K; L2 closed at phase 0.
  - `measured_offer_surface`: R.
  - `gas_offer_margin_anchor_vintage`: R (R-13).
  - `zonal_gas_basis`: K; the hub-commodity alternative is DATA-BLOCKED, with no daily PJM-area hub series.
- This lane adds no new evidence to any of those cells, so **NOT CHARTERED.** The candidate for any future floor
  lever is the CC_REGULAR econ/committed level in low-load hours. It needs a daily production-area hub series
  (rule 14) to re-open it.

### Post-hoc supplementary (NOT a pre-registered reading)

Probe `scripts/probes/_pjmnext29_coalbit_bins.py` → `results/phase0/pjm/_pjmnext29_coalbit_bins.json`.

**S1 — COAL_BIT model − CAMPD by real implied-HR bin** (TWh, with the bin's model/real price ratio in brackets):

| year | < 6.5 | 6.5–8 | 8–10 | 10–13 | ≥ 13 |
|---|---|---|---|---|---|
| 2019 | +4.5 (1.27) | +6.8 (1.12) | +4.5 (1.02) | +2.5 (0.91) | +0.9 (0.73) |
| 2020 | +1.8 (1.39) | +5.2 (1.19) | +3.9 (1.09) | +1.4 (0.95) | +0.6 (0.75) |
| 2021 | +3.9 (1.31) | +4.4 (1.14) | +3.9 (1.01) | +2.6 (0.89) | +0.6 (0.75) |
| 2024 | +0.1 (1.76) | +0.1 (1.34) | +0.2 (1.16) | +0.5 (0.97) | −0.2 (0.68) |

- **The low-hour bin carries only 14–25 % of the 2019–21 gap.**
- The excess appears in every bin, including bins where the model's price is at or below the real price.
- In 2023/24 the same price-ratio pattern gives a ~0 gap.
- So the low-end floor is not year-discriminating for COAL_BIT and is **not the C1 operand**.
- The R4 band dispatch (10.0 / 7.0 / 14.5 TWh) exceeds the realized `L_y` gap (4.5 / 1.8 / 3.9). Real coal also runs
  much of that energy below the model's offer (NEXT-11's price-flat real coal). A floor fix would therefore over-unload
  `L_y` and leave about three quarters of the gap.

**S2 — hours with real implied HR ≥ 10 (coal in the money in both).** Model COAL_BIT output ÷ its available `cap_mw`,
against CAMPD output ÷ the same `cap_mw`:

| year | model | CAMPD |
|---|---|---|
| 2019 | 0.98 | 0.90 |
| 2020 | 0.95 | 0.88 |
| 2021 | 0.99 | 0.91 |
| 2022 | 0.92 | 0.83 |
| 2023 | 0.81 | 0.78 |
| 2024 | 0.80 | 0.80 |
| 2025 | 0.94 | 0.89 |

In the fail years the model runs in-the-money coal at nearly full available capacity, while real output stays about
7–9 pp below it. In 2023/24 coal is less often in the money, the model sits near 0.80, and the two match.

**S3 — accounting.** Model COAL_BIT energy at plants with no bench COAL_BIT CAMPD record is 2.15 / 0.31 / 1.49 TWh
(2019 / 20 / 21). That is small, and it is not the gap.

## §3 Consequence

COAL_BIT side card (a) stays **OPEN, not a model-class limit**, and is re-pointed:
- **Ruled out:** the operand is not the low-end price floor (S1). NEXT-17 1b's "price level under $25" reading was
  fleet-level at PJM's offers. Hour by hour against CAMPD, the excess is uniform across price levels and specific to
  the fail years.
- **New operand:** the **deep-in-the-money loading of COAL_BIT**. The model's available capacity is ~8 % above what
  real units deliver when every unit is in the money, in 2019–22 and 2025 only.
- **Next zero-LP question (PJM-NEXT-30):** decompose that gap per unit (CAMPD unit-level hourly vs the model's
  per-unit `cap_mw` in S2 hours) into:
  - partial derates and outages outside the keeper's windows;
  - reserve and regulation headroom (0c: real coal carried 26 / 47 / 17 % of sync reserve in 2019 / 20 / 21);
  - the net-vs-gross / nameplate basis of `cap_mw`;
  - per-plant concentration (S2 top-10 plants carry 65–73 % of the gap).
  - NEXT-13 tested monthly max ÷ available (0.95–0.99), not in-money typical loading. A typical-vs-max gap is new
    evidence for the availability family; NEXT-13's verdict was on monthly max.

Nothing was built, solved or registered, and no matrix cell moves.
