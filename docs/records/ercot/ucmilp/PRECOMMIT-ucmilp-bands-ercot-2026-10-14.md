# PRECOMMIT — UC-BANDS-ERCOT phase 1 (proposed; owner ruling required before anything runs)

Lane UC-BANDS-ERCOT, 2026-10-14. Pin `580c4fbf`. Evidence: `FINDING-ucmilp-bands-ercot-2026-10-14.md`.
**Status: proposal.**
- No derive is written and no solve is launched until the owner rules through UC-DESK.
- This changes no keeper.

## 1. Decision rule (fixed before phase 1; from the charter)

- **Branch 1** applies when the bands are measured offers whose identification does not depend on commitment. Rules 23 and 14 then freeze them: report, route the residual to the engine/UC lane, and stop.
- **Branch 2** applies when any band's identification depends on the bridge or commitment structure, or when the band is a rule-1 channel set under the bridge. Branch 2 means: propose an ex-ante measured re-derivation, with the owner ruling.
- **Phase 0 lands in branch 2.** FINDING §2 shows:
  - the CC committed anchor is all-in (Min Gen Cost on an average heat rate), which the UC's explicit no-load double-counts;
  - every residual delta and the ×33 were fitted against gates on bridge-armed keepers;
  - the ST_GAS and CT_PEAKER committed bands are declared start-cost proxies.

## 2. Proposed method (ex ante; zero tuned values)

**Object.** A UC-basis `offer_curve_by_group` for the classes whose bands set price in the 2019 gap hours: CC_REGULAR, CC_CHP, ST_GAS and CT_PEAKER. The bands are `committed`, `econ_low`, `econ_high` and `peak`.

**Data.** The 60-Day SCED Gen Resource Data (NP3-965) corpus already on disk, read through the same shard selection and delivery-year filter as `derive_ercot_sced_offer_wall.py`. It uses:
- the `Submitted TPO` curves (MW / price steps);
- `LSL` and `HSL`;
- `Telemetered Resource Status` ONLINE rows only;
- `Resource Type` mapped to class: CCGT90 / CCLE90 → CC, SCGT90 / SCLE90 → CT, the gas steam types → ST_GAS. The resource → plant mapping comes from the existing `build_ercot_dam_resource_crosswalk.py`.

**Construction.** This mirrors `derive_dam_offer_hrmults.py` with three basis changes, and nothing else:
1. **Committed = the TPO price at LSL (incremental).** It is not the DAM Min Gen Cost. Under the UC, no-load and start are paid in the objective (DESIGN §1.2, D-3), so the committed tranche carries incremental energy only. This removes the double count and the start-cost proxy in one place (rule 19).
2. **Normalization on the UC's own cost basis.** Price ÷ the delivered EP-anchored gas price of the day ÷ the plant's incremental heat rate. The incremental heat rate is the slope of the same per-unit CAMPD regression (heatInput on grossLoad) whose intercept the UC carries as `noload_mmbtu_h` (`derive_uc_cluster_params.py`). With it, band × base on the UC's basis reproduces the offer. The derive writes only the intercept today, so carrying the slope is part of the open choice below.
   - **Open choice for the owner:** whether to carry the slope as a new per-plant fleet heat rate (a new field, an engine change), or to express it as a ratio to the existing average rate. The second is no new field, but the band then absorbs the average-to-incremental ratio. §5, item 2.
3. **Peak = the capacity-weighted p50 of the top-of-curve TPO price.** Peak mode B, the adopted lineage's mode, including near-cap steps. It is clipped at the year's SWCAP, as `ercot_offer_swcap_clip` already does.

**Aggregation.** The same as the DAM lineage:
- each resource contributes its own median per band;
- resources are then capacity-weighted by HSL;
- the whole corpus is pooled into **one value per class × band, for every scored year 2019–2025**;
- no year partition, no × k, no deltas.
- **2019–2022 is an extrapolation.** No SCED exists on disk for those years, which is the same representation bound declared for `coal_perplant_offer_curves` (ERCOT-144).

**What it is not:**
- Not the rule-1 channel. These are measured inputs (rules 13 and 14), so there is no `authorized_price_tuning` declaration, and the DOF-ledger row moves from `residual` to `measured-physical` for those bands.
- No change to `phys_*`, the structural shares, any adder, offset or haircut, or any per-year value (charter).
- Frozen at derive time against residuals (rule 23).
- **It replaces the × 33 carve-out in the UC configuration.** That reopens R-51 for the UC arm only, and the owner should rule on it knowingly. The incumbent keeper keeps × 33.

**Registry.** One new ScenarioConfig path field pointing at the frozen artifact, default off, ERCOT-scoped. It gets a matrix row plus a cell in every shard (rules 24 and 28). No env knob.

## 3. Zero-LP effect (phase 1a, before any solve)

1. Write the derive and the artifact. Report every value next to the keeper value, with the p25–p75 spread and n resources.
2. Re-price the f832aa52 bundle's marginal tranches with the new bands, holding dispatch fixed. That gives a first-order Δ C3a for 2019, reported with its stated bias: it ignores re-dispatch, and so ignores the merit-order effects.
3. Stop and report if the derived CC econ bands sit outside the DAM-measured p25–p75. That would signal a basis error, not a finding.

No number from 1a gates phase 1b. It is reported only (rule 1: never swept against the gates).

## 4. Phase 1b (only on a ruling that names it)

- **Arm:** keeper + `unit_commitment_milp` + `ercot_gas_commitment_bridge=false` + the new artifact.
- **Shards:** one per year, 2019–2025, via `scripts/shard_prompt.py` (full 40-char SHA, ≤ 720 min each, own out-dir and branch).
- **Control:** the uc-1.4 legs that exist (2019 `f832aa52`); other years use the UC-2-ERCOT legs re-pinned per G-DRIFT.
- **Pre-registered kills:**
  - K1: the recipe diff equals exactly the band keys plus the path field;
  - K2: 0 unserved;
  - K3: D-2 / C8 within budget.
- **Reported at full magnitude, not gated:** C1, C3a, C3b, C3c.
- **Promotion question:** goes to the owner on structure (rule 1), whatever the direction of the fit.
- Nothing is registered and nothing deleted. Shards are archived only after their bundles are verified.

## 5. Questions for the owner (via UC-DESK)

1. Run phase 1a (derive plus zero-LP re-price; no LP)? **Recommended: yes.**
2. Basis for the incremental heat rate: a new fleet field (structurally exact, an engine change) or a ratio to the average rate (no new field, band absorbs the ratio)? **Recommended: the new field.** The engine lane already owns the matching no-load double count (FINDING §3 engine note), and the two are one fix.
3. Include CT_PEAKER? It is non-integer under the UC, so its committed start proxy stacks on the P1 markup in the keeper too. **Recommended: yes for econ and peak; committed only together with removing the stacked proxy.**
