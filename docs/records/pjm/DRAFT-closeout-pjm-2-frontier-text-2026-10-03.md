# DRAFT — closeout-PJM-2: frontier text for C1 COAL_BIT 2019–21 and C1 CT_PEAKER 2021 (for the owner card; NOT signed)

**Status: draft for the desk.** It goes to no exceptions ledger and no keeper `frontier` field before the owner
rules (R-30 (b)). Keeper `2026-10-02-w0-pjm-fix2`. Gate values: `frontend/data/backcast/status/PJM.js`.

**What a signature does under rubric v3.1.** C3c is the only ledgerable criterion
(`calibration_verdict.LEDGERABLE_CRITERIA`). A signed C1 statement therefore **documents** the FAIL (plan §6
phase 4, "no undocumented FAIL") but **does not reclassify it**. PJM stays NOT-YET on these rows whatever is signed.

**The current text is stale.** The keeper's `frontier` note (declared 2026-07-31 at pjm-142) still describes a
CALIBRATED keeper. The text below would replace it.

---

## Statement 1 — C1 COAL_BIT 2019 / 2020 / 2021 (+19.81 / +13.18 / +16.58 TWh, band ≈ ±8 TWh)

> **What the model lacks.** Real bituminous coal in PJM 2019–21 does not load to its available capacity when it
> is in the money. In hours where coal clears in both the model and reality (real implied HR ≥ 10), the LP runs
> COAL_BIT at 0.98 / 0.95 / 0.99 of its available `cap_mw`. CAMPD shows 0.90 / 0.88 / 0.91 against the same
> capacity, about 2–3 GW of in-money headroom that real units held back (NEXT-29 S2).
>
> **Why it is within-plant.** The excess is within-plant loading, not across-plant ordering. The keeper's
> within-plant loading contrast is 0.66 / 0.69 / 0.56 against real 0.30 / 0.25 / 0.19, while the across-plant
> order is close to real (NEXT-24 §1–2).
>
> **Why it is not the price floor.** It shows in every real-price bin. The low-price hours carry only 14–25 % of
> the gap (NEXT-29 S1).
>
> **Why it is year-specific.** It is ~0 in 2023/24, where the in-money loading matches (0.80 / 0.80).
>
> **What the LP cannot express.** A cost-based, hourly-independent LP dispatches every in-money MW of an available
> unit. The real fleet's behaviour cannot be written as a measured, forward-reproducible input under rules 13 and 24.
> That behaviour is partial loading of in-money coal: reserve and regulation holding (real coal carried
> 26 / 47 / 17 % of synchronized reserve in 2019–21, census 0c), fuel and contract conduct, and offer conduct
> above cost.

**Evidence chain.**

| record | what it established |
|---|---|
| NEXT-17 | LOAD carries 80–100 % of the gap. Coal's own offers do not discriminate the years (RoR 1.07 / 1.24 / 1.05). |
| NEXT-24 | The excess is within-plant and year-specific. |
| NEXT-27 | Per-year online_frac is dispatch-inert (Δprice ≤ 2e-8). The over-run is economic, not floor-forced. |
| NEXT-28 | The no-load committed-rung floor is 10–50× too small (unload 0.31–0.60 TWh against a 3 TWh bar). Route closed, R-30. |
| NEXT-29 | The low-hour floor is not the C1 operand. The operand is in-money loading. |
| closeout L2 | Incremental HR collapses to committed-rung pricing. Closed at phase 0. |
| R-13 | `gas_offer_margin_anchor_vintage` stays R: S4a/S3 fail, near-inert on price. |
| wave-1 0c | Coal already sits in the per-generator reserve pool, so L1 as written is a no-op. The model reserve dual is ≈ $0. |
| Elliott v2 | 2022 is data-limited (R-26). |

**Levers falsified** (PJM shard `mechanism-matrix/PJM.js`):

| verdict | lever | result |
|---|---|---|
| R | `committed_band_measured_basis` | h6/h8/h9 |
| R | `coal_passthrough_sigmoids` gas_mid joint re-centring and bituminous ceiling | h7, pjm-170; the family stays K |
| R | `cc_mustrun_conduct_window` | NEXT-17 |
| R | `pjm_gas_commitment_bridge` | NEXT-16 |
| R | `gas_commitment_bridge` | pjm-142 |
| R | `gas_offer_margin_anchor_vintage` | pjm-169, R-13 |
| R | `measured_offer_surface` | |
| R | `pjm_replacement_cost_fuel` | NEXT-13 |
| R | `mustrun_commitment_feasibility_clip` | h12 |
| R | `pjm_measured_outage_event_cap` | pjm-161 |
| R | `retiree_cems_cap` | deleted |
| R | `reserve_pergen` sync sub-leg | h3 |
| K, falsified as COAL_BIT levers | offered EcoMax (`offer_curve_by_group`) | NEXT-11 |
| K, falsified as COAL_BIT levers | per-year online_frac | NEXT-27 |
| K, falsified as COAL_BIT levers | the `pjm_midcurve_belt` L2 form | |
| K, falsified as COAL_BIT levers | the coal self-schedule floor | NEXT-12/24/26 |
| U, unreachable or double-counting | `coal_fuel_inventory` | |
| U, unreachable or double-counting | `coal_nameplate_summer_derate` | |
| U, unreachable or double-counting | `coal_offer_net_revenue_margin`, `coal_peak_offer_margin`, `coal_perplant_offer_level` | offers corpus unit-masked |

**What would re-open it.**
- **NEXT-30 per-unit decomposition (zero LP).** This is the open item. CAMPD unit-hourly output against the model's
  per-unit `cap_mw` in S2 hours, split into:
  - derates and outages outside the keeper's windows;
  - reserve and regulation headroom;
  - the net-vs-gross / nameplate basis of `cap_mw`;
  - plant concentration (the top 10 plants carry 65–73 %).

  Any measured, forward-admissible part of that decomposition is an input repair, not a frontier.
- Unit-identified PJM offers (the DataMiner corpus is masked).
- An online-gated synchronized-reserve mechanism that clears rule 19.

---

## Statement 2 — C1 CT_PEAKER 2021 (−8.07 TWh)

> **What the model lacks.** PJM's out-of-merit commitment of CTs. The operator commits CTs in real time for
> reliability and congestion: local voltage, transfer and reserve needs that are unpublished and unit-specific.
> PJM then pays them through balancing operating-reserve credits.
>
> **The size of it.** In 2021 CTs received 92.8 % of the $128 M of balancing generator credits (IMM SOM Table 4-3,
> as digitized in NEXT-26). Real CTs ran about 2.5× the keeper's run blocks (6,547 vs 2,621). They put 8.4 TWh into
> out-of-money shoulder hours, 6.6 TWh more than the keeper (NEXT-24 §1–2).
>
> **Where it sits.** The under-run is across plants and in specific places: AEP-Ohio and Dominion, with Tait,
> Doswell, Louisa and Marsh Run among the top BOR recipients (NEXT-25, NEXT-26). Within-plant loading matches real.
>
> **Why the model cannot express it.** An energy-only, cost-based LP commits only on its own economics. The
> commitment driver has no public, forward-reproducible series: DA must-run-for-reliability is 0.3 % of DA MWh, and
> the IMM dropped its zone tables after 2022. A floor built on observed CT output would be pinning (rule 13). The
> plan rules it "ledger (inadmissible as a lever)" (§3.6).

**Evidence chain.**
- NEXT-22 and NEXT-23: per-plant under-run at the dear CTs; the band is already at the measured 1.05.
- NEXT-24: across-plant ordering, real starts, shoulder energy.
- NEXT-25: zonal residual.
- NEXT-26: BOR census, weakly confirmed in 3 of 4 years.
- SHARD-PJM closeout research, L5.

**Levers.**

| verdict | lever | result |
|---|---|---|
| U | `ct_peaker_committed_measured` | Across-plant object, min-run would not bind, worsens 2024/25 (NEXT-22/23/24) |
| K | `netload_drag_floors` | CT −0.70 to −0.96 TWh (h13), not a closer |
| — | Tait 55248→2847 CAMPD remap | A rule-14 data repair that rides the next solve, worth ~$1–2/MWh; not a CT closer |

**What would re-open it.**
- A measured, forward-admissible out-of-merit commitment driver: unit-level BOR or RT-commitment records, or
  published local reliability requirements.
- The zonal DA pull, to separate locational from conduct effects.

---

## Discrepancies found while drafting (the desk should see these)

1. **85.7 % vs 92.8 %.** Plan §3.6 and SHARD-PJM L5 cite "IMM 2021: CTs took 85.7 % of balancing credits". NEXT-26's
   digitization of SOM Table 4-3 (`results/phase0/pjm/_pjmnext26_bor_credits_by_zone_type.csv`) gives 92.8 % for
   2021, and 85.7 % is its 2023 value. The draft uses 92.8 %. The plan line should be corrected or re-sourced.
2. **L1 no-op not recorded.** Wave-1 0c found L1 ("coal in the per-generator reserve pool") a no-op, because coal is
   already a member. The `reserve_pergen` cell's evidence does not record that, and plan §3.6 still names L1 as the
   COAL_BIT route.
3. **COAL_BIT conflict.** NEXT-29 §3 calls COAL_BIT card (a) **"OPEN, not a model-class limit"** and proposes
   NEXT-30. A model-class frontier signed now would contradict the latest record.
