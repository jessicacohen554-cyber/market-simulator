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

**Status: a draft pending PJM-NEXT-31, not a frontier to sign.**
- PJM-NEXT-30 (`docs/records/pjm/FINDING-pjm-next-30-coalbit-inmoney-loading-2026-10-03.md`) decomposed the
  in-money loading object, and its §4 owner ruling charters PJM-NEXT-31: an outage-extract repair, solved on all
  seven years.
- This statement is signable only for the residual left after that repair.

The COAL_BIT gap has two separate parts.

### 1a. Capability overstatement: a rule-14 object, ROUTED (not frontier)

- **The size.** The keeper's `cap_mw` sits about 0.5–1.9 GW above what COAL_BIT plants revealed they could deliver
  that year or week (NEXT-30 §2, pieces basis + derate + offline).
- **What it is.** 62–89 % of it falls in CAMPD whole-unit dark hours that the keeper's outage windows do not carry.
  The rest is a rating basis at small plants (evidence appended to `coal_nameplate_summer_derate`, still U).
- **It is present in every year, 2023/24 included.** It is a measured-input defect (rule 14), not a model-class
  limit. It is routed to NEXT-31 (owner ruling: build the extract repair and keep it on structure even if 2023/24
  regress, rule 1).

### 1b. Merit-position residual: the CANDIDATE frontier (after NEXT-31)

> **The cancellation.** The 2023/24 COAL_BIT pass is a cancellation, not a match. In NEXT-29's S2 hours (real
> implied HR ≥ 10), the model loads in-money coal below real in 2023/24 (loading piece −340 / −517 MW), and that
> offsets the same capability overstatement that adds to the gap in the fail years (NEXT-30 §2).
>
> **What separates the years.** Only the model's own coal merit position against the price. The model runs COAL_BIT
> at 0.98 / 0.95 / 0.99 of available `cap_mw` in 2019–21, against CAMPD 0.90 / 0.88 / 0.91
> (`docs/records/pjm/FINDING-pjm-next-29-lowhour-price-setters-2026-10-02.md` S2). It backs off below real in
> 2023/24. Real coal does neither.
>
> **Where it is not.** It is not the low-price floor: it appears in every real-price bin, and the low hours carry
> 14–25 % (NEXT-29 S1). It is within-plant (keeper loading contrast 0.66 / 0.69 / 0.56 vs real 0.30 / 0.25 / 0.19,
> NEXT-24).
>
> **Why the model cannot express it.** A cost-based, hourly-independent LP dispatches every in-money MW at its
> offer. The real fleet's price-flat loading cannot be written as a measured, forward-reproducible input under rules
> 13 and 24. That loading reflects reserve holding (the IMM coal-held reserve is 0.7–2.2× the NEXT-30 loading
> piece), fuel and contract conduct, and offer conduct above cost. Every channel that sets the coal offer level and
> shape is adjudicated.

**Evidence chain.**

| record | what it established |
|---|---|
| NEXT-17 | LOAD carries 80–100 % of the gap. Own offers do not discriminate the years. |
| NEXT-24 | The excess is within-plant and year-specific. |
| NEXT-27 | Per-year online_frac is dispatch-inert. The over-run is economic. |
| NEXT-28 | The no-load committed-rung floor is 10–50× too small. Route closed, R-30. |
| NEXT-29 | The floor is not the operand. In-money loading is. |
| NEXT-30 | Overstatement vs merit position, and the 2023/24 cancellation. |
| closeout L2 | Collapses to committed-rung pricing. |
| R-13 | `gas_offer_margin_anchor_vintage` R. |
| wave-1 0c | L1 reserve-pool membership is a no-op, since coal is already a member. |
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
| K, falsified as COAL_BIT levers | `coal_drop_pof` | NEXT-30 |
| U, unreachable or double-counting | `coal_fuel_inventory` | |
| U, unreachable or double-counting | `coal_offer_net_revenue_margin`, `coal_peak_offer_margin`, `coal_perplant_offer_level` | offers corpus unit-masked |

**What would re-open 1b.**
- NEXT-31's all-years result. If the repair moves the fail years and 2023/24 differently from NEXT-30's
  per-MW-of-cap prediction, 1b is re-measured on the repaired keeper.
- Unit-identified PJM offers.
- An online-gated synchronized-reserve mechanism that clears rule 19.

**Recommended card.** Sign 1b only after NEXT-31 reports, and re-measure it on whatever keeper NEXT-31 leaves.

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
3. **COAL_BIT status.** NEXT-29 and NEXT-30 both keep card (a) "OPEN, not a model-class limit". This draft is
   therefore split: 1a is routed to NEXT-31 (rule 14), and 1b is the candidate frontier, pending NEXT-31.
