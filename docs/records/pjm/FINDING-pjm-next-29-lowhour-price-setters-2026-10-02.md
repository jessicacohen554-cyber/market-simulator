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

*(filled after the computation; §1 is not edited)*
