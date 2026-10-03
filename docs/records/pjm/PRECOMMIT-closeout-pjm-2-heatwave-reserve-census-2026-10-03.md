# PRECOMMIT — closeout-PJM-2 step 4: the June 23–25 2025 heat-wave reserve-scarcity census (zero LP)

**Approved by the desk on 2026-10-03** as step 4 of the lane. Keeper `2026-10-02-w0-pjm-fix2` (`w0_pjm_span`).
This step is zero LP: no shards, nothing armed, and no cell moves. **This file is committed before any number below
exists.** The record it serves is `FINDING-closeout-pjm-2-2025-regression-attribution-2026-10-03.md` §3, which
found that the W0 keeper's 2025 reserve dual is 0 in every hour. That includes Jun 23–25, when real system RT
reached $1,830.

**Already known before this file.** Wave-1 census 0c, for the keeper's 2019–25 years in general: the
`pjm_reserve_pergen` pool is not online-gated, about 25 GW of CT/oil headroom covers a 2.6–3.6 GW requirement, and
the dual is ≈ $0. The 2025 `reserve_family` requirement runs 2.3–4.1 GW. **Nothing about the window hours has been
computed.**

## Question

How much additional unavailable capacity would the model need in the heat-wave hours before its reserve dual binds?
Does PJM's published outage record supply that much more than the model already carries?

## Window and quantities

- **Window `H`:** Jun 23–25 2025, hour-of-year 4164–4174, 4188–4198 and 4212–4222 (12:00–22:00 EPT clock
  as the keeper's hour axis; 33 hours).
- **Headline subset `H*`:** the hours of `H` where the real load-weighted system RT is at least $400. Real system RT
  comes from `actual_lmp_zonal_PJM.parquet`, weighted by the keeper's zone demand.
- **Model headroom `G(h)`:** the requirement-net reserve headroom in the W0 P1 solve, defined as

  `G(h) = Σ_u min(cap_mw − mw, ramp10_u) − Σ_family requirement_mw(h)`

  - The sum runs over reserve-pool units.
  - Pool membership and `ramp10` come from a `rebuild_fleet` (fleet_only, w0 posture) of the keeper's 2025 recipe.
    The pool is `RESERVE_FUEL_TYPES` with `ramp10 > 0`, the `spec.py` rule.
  - `cap_mw` and `mw` come from the committed `unit_marginal_2025`.
  - First order, the dual binds when `G(h)` reaches 0.
  - Withdrawing available MW from a dispatched unit forces the same MW onto headroom, so `G(h)` is the extra
    unavailability needed for the dual to bind.
- **Model unavailable `U_m(d)`:** for each day d, the mean over `H` hours of `Σ_u (pmax_u − cap_mw_u)` over the
  thermal, nuclear and hydro units. `pmax` comes from the same rebuild.
- **Published unavailable `U_p(d)`:** from `data/raw/pjm-outages/by-year/gen_outages_by_type_2025.csv`, the RTO
  region at lead 0, summing forced, maintenance and planned MW.
- **Outage gap:** `ΔU(d) = U_p(d) − U_m(d)`.

**Basis caveat, written in advance.**
- The feed's MW is on PJM's ICAP/outage-ticket basis.
- `U_m` is on the model's pmax basis, which is seasonal summer under W0. The model also carries ambient derates
  inside `cap_mw`.
- The comparison is therefore a bound, not an identity, as in census 0b.

## Readings (fixed)

| id | reading | rule |
|---|---|---|
| R1 | How far the model is from binding | Report `G(h)` (min, median, max) over `H*`. The model is **near-binding** if median `G` over `H*` is ≤ 2,000 MW. |
| R2 | Can availability alone close it? | **Availability route CONFIRMED** iff `ΔU(d) ≥ G(h)` in at least 50 % of the `H*` hours (each hour compared with its own day's `ΔU`). **Otherwise NOT CONFIRMED.** |
| R3 | Where is the headroom? | The share of `Σ min(cap − mw, ramp10)` over `H*` held by offline units (`mw` = 0) and by the CT_PEAKER plus oil plant groups. **Reported, not gated.** It says whether the not-online-gated pool is what keeps `G` large. |

## Decision (fixed)

- **R2 CONFIRMED.** The heat-wave miss is an availability object: the published outages are larger than the
  modelled ones. The route is outage-input coverage for summer extremes, under the `unit_outage_*` family and
  rule 14.
  - That family is K, and NEXT-31 is building an outage-extract repair. This census hands its window to NEXT-31 (or
    to a follow-on) with the hours and MW named.
  - No new mechanism.
- **R2 NOT CONFIRMED and R3 offline-share ≥ 50 %.** The reserve dual stays at 0 mainly because offline CT/oil
  headroom counts as reserve. The open object is reserve-pool formulation (online gating / deliverability), not
  availability. Prior verdicts on that object:
  - `pjm_reserve_pergen_sync` is R (pjm-h3);
  - `reserve_deliverability_scoping` is I;
  - `ordc_scarcity_overlay` is G.

  So the result goes to the desk as a frontier candidate for 2025 C3a/C3b. **No lever is proposed without new
  evidence.**
- **Neither.** Record the numbers. 2025 C3a/C3b stay a documented FAIL and go to the desk.

## What this step will not do

- No solve.
- No change to the outage extract, the pool or the ORDC.
- No re-test of any R/G cell.
