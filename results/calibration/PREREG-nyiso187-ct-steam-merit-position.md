# PRE-REGISTRATION — nyiso-187 (`ct-steam-merit` lane): WHY the NYC / Capital-Hudson combined cycles take the hours the market gave to combustion turbines and steam — the merit-position decomposition at the LP's installed offer, its owning mechanism, and the ONE repair with a measured input (the Astoria registry split's availability half)

**Session:** nyiso-187, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-187-ct-steam-merit`, fresh off `origin/main` at `f71031f5`
(carries PR #4698, the nyiso-186 keeper promotion).
**Keeper at entry:** `2026-09-04-nyiso-186-astoria-identity`
(`results/calibration/nyiso186_astoria_identity`) — NOT-YET, target grade 5,
fail set **{C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.4 %
(owner-court, NOT touched), C3c}**.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST
MEASUREMENT OF THIS SESSION.** No hourly dispatch, no reduced cost, no
bucket share and no solve of this session's making exists at the time of
writing.

---

## §0 — DISCLOSURE

**This session runs in the SAME container and the SAME model context as
nyiso-186** and holds everything nyiso-186 measured: the per-plant CC
attribution (C3 0.875 / 0.745 / 0.853; Cricket Valley / Zeltmann / Astoria
Energy II), the when-online loading table (Zeltmann 0.96 vs 0.68; Cricket
Valley on 0.995 vs 0.878), the M6 gas-family identity (67.80 vs 67.80 TWh;
`CT_PEAKER` −1.66, `CT_CHP` −1.29, `ST_GAS` −1.09 in 2024), the Astoria
registry split (heat-rate half repaired and promoted; availability half sized:
the `perunitmerit` extract routes CT1 / CT2 at 297.5 MW and CT3 / CT4 at 313.0
MW ALL to EIA plant 55375 against a 1,221 MW denominator; 57664 carries no
extract rows in any year; 2025 EIA-923 at 57664 falls to 2.12 TWh on an outage
the model cannot see, model +2.65 TWh), and the arm's per-plant energy moves.

Read this session: `FINDING-nyiso175` §0, §3, §5, §7 (`CT_PEAKER` LEVEL-limited,
starts 2.5–4.9× too few, cause `scuc_load_pocket_commitment` cell **G**,
owner-closed at nyiso-163b, DO-NOT-REDO; `CT_CHP` RESPONSE-limited, sole
mechanism `chp_steam`, no hourly steam driver exists; the outage overlay reaches
neither CT class by design); `FINDING-nyiso178` §8–§9, `FINDING-nyiso179` §1,
§9 and `FINDING-nyiso180` §1, §7 and `FINDING-nyiso181` §1, §11 (the `ST_GAS`
"un-run in-the-money" object is RETIRED as an instrument artifact — on the LP's
installed `mc` the matched-population ratio is 0.992 / 0.991 / 0.992; the
premise "mc ≤ price ⇒ should run" is wrong under eleven armed mechanisms, the
optimality condition is the reduced cost; the `ST_GAS` offer-position lane is
BLOCKED on C3a-2025; `gas_st_committed_hr_mult`, the `peak` 4.20, the dear-hour
gas basis + `dual_fuel_switching`, the availability family, the merit guard, a
steam duty curve and `gas_st_startup_cost` are all CLOSED lines);
`FINDING-nyiso96` §5 (**53–66 % of measured NYISO CT energy clears BELOW its own
bare SRMC at its own zonal price**; `tranche_startup_amortization` rejected on
rule 1 there yet armed on the current keeper). Matrix §5.5 (nyiso-186 queue)
and the NYISO shard cells `scuc_load_pocket_commitment` (G),
`nyiso_downstate_ct_gas_basis` (K), `dual_fuel_switching` (K),
`nysdec_peaker_rule_availability` (K), `energy_reserve_coopt` (K),
`nyiso_spin_reserve_online` (I), `gas_offer_margin_zonal_anchor` (K),
`tranche_startup_amortization` (K), `nyiso_incity_commitment_obligation` (R),
`cc_capacity_reconcile` (U), `egrid_identity_heat_rates` (K).

Code read: the `ScenarioConfig` comment blocks for `nyiso_zonal_gas_basis`,
`nyiso_downstate_ct_gas_daily`, `gas_hub_basis_daily`, `dual_fuel_switching`,
`gas_offer_margin_anchor_by_zone`, `tranche_startup_amortization`,
`tranche_startup_measured_runs`, `nysdec_peaker_rule_availability`;
`scripts/data/derive_campd_unit_outages.py` (the remap is applied BEFORE the
group lookup at lines 405 / 1568 — **nyiso-186 §3 / §5.2 item 2 were wrong to
say the `CAMPD_UNIT_PLANT_REMAP` does not reach the outage derive; only the
merit-order PANEL reads raw parquets**), `build_capacity_index`; the CLI flag
sets of `derive_campd_unit_outages.py` and `derive_thermal_tranches.py`; the two
artifacts' `.meta.json` `derive_invocation` blocks; `legitimacy_diagnostics.load_bench`
(per-plant CAMPD hourly series with `group` / `zone`).

Inputs read (not dispatch): the keeper's armed flags (`tranche_startup_amortization`
True, `tranche_startup_measured_runs` True, `gas_st_startup_cost` False,
`ramp_limits` True, `nyiso_zonal_gas_basis` True, `nyiso_downstate_ct_gas_daily`
True, `gas_hub_basis_daily` True, `dual_fuel_switching` True,
`nysdec_peaker_rule_availability` True, `nyiso_nyc_lcr_tsl` / `nyiso_li_lcr_tsl`
True, `local_capacity_constraints` False, `nyiso_incity_commitment_obligation`
False, `nyiso_gas_bridge_ct` False); the 2024 zone × class roster from the unit
sidecar's static attributes (NYC: `CT_PEAKER` 21 plants / 1,496 MW, `CT_CHP` 8 /
299, `ST_GAS` 3 / 3,228, `CC_REGULAR` 5 / 2,073, `CC_CHP` 4 / 1,173;
Capital-Hudson: `ST_GAS` 3 / 2,502, `CC_REGULAR` 6 / 4,211, `CT_PEAKER` 4 / 81);
the bench plant coverage by zone × class; the `actual_lmp_hourly_NYISO.parquet`
schema (ISO-level hourly `rt` / `da`, 2024 mean 36.0); the NYISO zonal RT
archive's 2024 months (Feb–Jun, Sep — a SAMPLE, never an hourly series).

**Not read:** any `mc` / `red_cost` value; any hour-level dispatch of any CT,
steam or CC unit; any bucket share; any zonal actual price value.

---

## §1 — THE OBJECT, in two parts

**Object 1 (attribution, no LP).** In the hours the market ran NYC /
Capital-Hudson combustion turbines and steam that the model did not, WHY did the
model's cheapest available CT / steam capacity not clear — at the LP's own
installed offer (`unit_hourly.mc`, the nyiso-181 instrument) against the LP's
own zonal price (`system.price`) and against the actual RT price — and which
armed mechanism owns each part. The answer is a **decomposition of the 2024
CT / steam deficit energy into three buckets**, per class and zone, fixed now:

* **A — priced out at the MODEL price but in the money at the ACTUAL price**:
  the cheapest available un-run unit's `mc` > model `price_z` and ≤ actual RT
  (ISO-level `rt`, zonal premium reported from the sample months). Owner:
  price LEVEL / SHAPE (C3a / C3b) — downstream of the owner-court C3a lane
  and nyiso-168's C3b object. **No lever here.**
* **B — out of the money at BOTH prices**: `mc` > actual RT too. Owner:
  out-of-market commitment (SCUC load-pocket / BPCG make-whole, cell **G**,
  owner-closed) or a measured-input defect on the CT / steam side (fuel, heat
  rate, availability) — the ONLY bucket where a lever could live, and only if
  a NAMED measured input is wrong.
* **C — in the money at the MODEL price yet un-run**: `mc` ≤ model `price_z`
  and capacity below its bound. Owner: rows beyond the balance (ramp, reserve
  headroom, floors elsewhere) — measured by the reduced cost:
  `charge = red_cost − (mc − price_z)`; nyiso-180 §7 / nyiso-181 already bound
  this bucket small for `ST_GAS`; it is re-measured here per class and zone
  on the same instrument.

**Object 2 (repair with a measured input).** The Astoria registry split's
availability half — the ONE input defect already established on source
evidence (nyiso-186 §3): add the split-facility entries `(55375, "CT3") →
57664`, `(55375, "CT4") → 57664` to `campd.CAMPD_UNIT_PLANT_REMAP` (the
caiso-196 El Segundo form for the identical defect class: CEMS files a unit
under a legacy / sibling ORISPL while EIA-860 carries it under its own plant),
then re-derive the two artifacts the keeper resolves from that routing —
`campd-unit-outages-perunitmerit-NYISO.csv` (+ its `-layup-` companion, the
same derive) and `thermal_tranches-perunitmerit-NYISO.csv` — with their
committed `derive_invocation` blocks verbatim, citing the data change (rule 23:
EIA-860's CT3 / CT4 / ST2 under 57664 vs CAMPD facility 55375). Zero
parameters. Every other artifact that reads NYISO CAMPD through the normalizer
is re-derived ONLY if its `--check` (or byte-compare) shows it moved — the
footprint is measured and listed, never assumed.

## §2 — RULE 19 `[R-ONE-MECH]`: every armed mechanism that prices a NYC / CH `CT_PEAKER`, `CT_CHP` or `ST_GAS` unit AGAINST a `CC_REGULAR` unit (from the code)

| # | mechanism (armed) | CT_PEAKER | CT_CHP | ST_GAS | CC_REGULAR | asymmetry it creates |
|---|---|---|---|---|---|---|
| F1 | `nyiso_zonal_gas_basis` (K) | zone hub offset | same | same | same | none within a zone |
| F2 | `nyiso_downstate_ct_gas_daily` (K) | **delivered gas SET to Transco Z6 NY daily + LDC premium** | — | — | — | CTs price on the daily interruptible city-gate; CC / ST on the monthly hub + basis |
| F3 | `gas_hub_basis_daily` (K) | daily shape of the monthly basis | same | same | same | none |
| F4 | `dual_fuel_switching` + oil parity (K) | min(gas, oil) where flagged | same | same (Ravenswood, Arthur Kill, Astoria …) | same where flagged | caps dear-hour gas |
| O1 | `offer_curve_by_group` bands (K, DOF entry) | committed 1.35 / econ 1.0 / peak 4.0 (`phys` 0.843 / 0.661 / 0.658 / 1.0) | CT_CHP curve | 1.05 / 1.08–1.13 / 4.2 (`phys` 1.104 / 0.83 / 0.83 / 1.0) | 0.90 / 0.95–1.00 / 2.25 (`phys` 0.964 / 0.784 / 0.925) | **the CT committed markup 1.35 vs a measured 0.843; the CC committed 0.90 vs 0.964** — DOF-ledger residual entries, NOT tunable here (rule 21) |
| O2 | `gas_offer_net_revenue_margin` + zonal anchors (K) | markup as fixed $/MWh at the zone anchor | same | same | same | none beyond O1 |
| O3 | `tranche_startup_amortization` + `measured_runs` (K; nyiso-96 R on a prior keeper, armed since) | **start cost ÷ measured run on econ / peak CT tranches** | ? (measured per class) | `gas_st_startup_cost=False` → none | **excluded by design** ("block-loading a committed CC is not a fast start") | CTs carry a start markup, CCs and steam do not |
| A1 | `nysdec_peaker_rule_availability` (K) | ozone-window derates on listed units | — | — | — | CT-only availability loss |
| A2 | `campd_per_unit_attribution` + merit guard extract (K) | **not reached** (`_generic_unit_outage_target → None`) | not reached | reached | reached | CT classes carry no measured outages; CC / ST do |
| A3 | `cc_nameplate_summer_derate` (K) | — | — | — | seasonal capability | — |
| C1 | `nyiso_gas_commitment_bridge` (K; CT limb `nyiso_gas_bridge_ct` False) | none | none | min-load floor | min-load floor | floors hold CC / ST on, never CTs |
| C2 | reliability-floor limbs (K; downstate `tmax` limbs OFF) | none | none | NYC / LI / CH `ST_GAS` limbs | none | — |
| C3 | `chp_steam_following` (K) | — | **sole floor** | — | — | — |
| R1 | `energy_reserve_coopt` + `nyiso_*_locational_reserve` (K) | eligible | eligible | eligible | eligible | headroom held on whichever is cheapest to hold |
| R2 | `ramp_limits` (K) | ramp groups | same | same (nyiso-180 §6: transient only) | same | — |
| G | `scuc_load_pocket_commitment` | **the diagnosed cause of the LEVEL deficit** — cell G, owner-closed | — | — | — | out-of-market commitment the LP cannot see |

**Ownership rule, fixed now.** Bucket A is owned by the price level / shape
(C3a owner-court; C3b). Bucket B is owned by G unless M4 names a measured input
(F2's delivered CT gas, O3's start markup, a CT heat rate) that is WRONG on
source evidence — a residual-driven move of O1 / O2 / O3 constants is forbidden.
Bucket C is owned by R1 / R2 / C1–C3 rows, attributed by the reduced-cost charge.
The CC side is the mirror: in the same hours the CC's own `mc − price_z` says
how deep in the money the fill is; a CC-side lever is proposed by NO bucket.

## §3 — MEASUREMENT (no LP; the keeper's own 2024 sidecars, bit-identical at HEAD per nyiso-186 G-CONTROL)

* **M1 — the deficit hours.** Per class ∈ {`CT_PEAKER`, `CT_CHP`, `ST_GAS`} and
  zone ∈ {NYC, Capital_Hudson} (Long Island reported alongside), measured
  hourly class MW from the bench's per-plant CAMPD series (`load_bench`,
  `corrected_unit_class` crosswalk) vs model hourly class MW from
  `unit_hourly`. Deficit energy `D = Σ_t max(0, meas − model)`; the CC excess
  `X = Σ_t max(0, model_CC − meas_CC)` on the same grid. **Hourly coincidence:**
  `r`(deficit_t, CC-excess_t) and the share of `X` falling in deficit hours.
* **M2 — the bucket decomposition.** For each deficit hour, the un-run
  available capacity of the class in the zone is ordered by `mc`; the deficit
  MW is filled from the cheapest un-run capacity and each MW lands in A / B / C
  by comparing its `mc` with model `price_z[t]` and actual `rt[t]` (ISO-level;
  the zonal sample premium for NYC reported as a sensitivity: A/B split
  re-read with `rt + premium`). Shares `a, b, c` of `D` per class × zone.
* **M3 — bucket C attribution.** For bucket-C MW, `charge = red_cost − (mc −
  price_z)`; distribution reported; C's share of `D` compared with nyiso-181's
  bound.
* **M4 — bucket B, source check (the only place a lever can live).** For the
  bucket-B capacity: its `mc` decomposed into fuel × HR + VOM + markup (from the
  keeper's own arrays via `resolve_fuel_prices` / `assemble_mc` on the
  reconstruction, the nyiso-181-repaired instrument), and each term checked
  against its source: delivered CT gas vs the curated Transco Z6 daily index
  the flag reads; the unit's model HR vs its CAMPD running-hour HR (merged);
  the start markup vs the measured run. A term is WRONG only if it departs
  from its own published source, never if it departs from the residual.
* **M5 — the CC mirror.** In deficit hours, the NYC / CH CC units' `price_z −
  mc` (depth in the money) and their reserve headroom (`cap − mw`).

**Verdict rules, fixed now.**
* **OWNER = LEVEL/SHAPE** iff `a ≥ 0.50` of `D` for the class-zone.
* **OWNER = OUT-OF-MARKET (G)** iff `b ≥ 0.50` AND M4 finds no term wrong on
  its source. If M4 finds a wrong term, OWNER = that named input (the only
  admissible CT/steam-side repair form: the input's source, zero parameters).
* **OWNER = ROWS** iff `c ≥ 0.50`; then M3 names the row family.
* Mixed (no bucket ≥ 0.50): reported as such; no lever.
* **Object 2 verdict (A/B):** arm = keeper replay with the re-derived artifacts;
  control = the committed keeper (bit-identical at HEAD, nyiso-186 G-CONTROL,
  re-measured here on the arm's own `hourly/system_<year>` if any doubt).
  **G-DELTA:** zero `scenario_config` fields; the artifact diff is confined to
  rows keyed on 55375 / 57664 (any other plant's rows changing is a STOP — it
  would mean the remap reached something the identity does not cover).
  **REJECTED PROBE** iff C2 / C3a / C3b / C8 flips PASS → FAIL; else **KEEPER
  CANDIDATE** to the owner with every regression at full magnitude.
  **Pre-declared expectations (falsifiable, not bars):** (i) 57664's 2025
  energy FALLS (its 2025 outage becomes visible); (ii) 55375's availability
  RISES (no longer derated for its sibling) and its energy rises; (iii) the
  2024 C1 `CC_REGULAR` cell moves little (family pinned); (iv) no price claim.

## §4 — FORBIDDEN

F1 no band, anchor, start-cost, min-load or floor coefficient moves (O1–O3, C1–C3
are DOF-ledger or measured constants); F2 no per-plant dict beyond the
registry entry the caiso-196 precedent established for this defect class; F3
no availability haircut, no pin to CEMS, no rescale to a residual; F4 no
re-opening of G (`scuc_load_pocket_commitment`), of the nyiso-178/179/181
closed lines, of C3a-2025; F5 no second solve-affecting change in the arm; F6
no edit of any bar after M2 is read; F7 no CAISO edits (the remap's CAISO rows
untouched); F8 2023–2025 only, no marker requested.

## §5 — STOP CONDITIONS

S0 the keeper's `unit_hourly.mc` does not reproduce `assemble_mc` on the
reconstruction to `max|d| = 0` (nyiso-181 standard) ⇒ the M4 term
decomposition is not used; buckets still read. S1 G-DELTA fails (rows beyond
55375 / 57664 move) ⇒ the arm is not solved. S2 memory: at most two concurrent
invocations. S3 every completed non-control solve is registered THIS session.
S4 a repair whose owner-rule did not name a measured input is not built.
