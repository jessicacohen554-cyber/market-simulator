# PRECOMMIT — PJM close-out L2: incremental-heat-rate pricing of the CC_REGULAR econ tranches

Lane `closeout-PJM` (branch `claude/closeout-pjm-wave1`), 2026-10-02. Plan `docs/backcast-closeout-plan-2026-10.md` §3.6 step 2; chartered by census 0d (`results/phase0/pjm/_pjmco_0d_incremental_hr_census.json`, record `FINDING-pjm-closeout-wave1-censuses-2026-10-02.md` §4). **No solve is authorised by this document**: solves HOLD until W0 (`claude/closeout-b-w0-foundation`) merges and the desk releases the lane. **The mechanism is not built**; building it is a `src/` change with its own matrix row (rule 28) and is gated on the owner question in §6.

## 1. Census 0d result (the charter condition)

Capacity-weighted CC_REGULAR, MMBtu/MWh, whole-plant net basis:

| | 2019 | **2020** | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| model econ-band HR (keeper P1 offers) | 7.54 | **8.06** | 7.99 | 7.87 | 8.10 | 8.83 | 8.82 |
| measured incremental HR (CAMPD slope) | 6.76 | **6.94** | 6.88 | 6.88 | 6.95 | 6.90 | 6.92 |
| gap | +0.77 | **+1.12** | +1.11 | +0.99 | +1.15 | +1.94 | +1.89 |

Pre-fixed reading: gap ≥ 0.8 cap-weighted ⇒ charter L2. **2020 PASS (+1.12)**; 2020–2025 clear, 2019 just under.

**Where the gap sits (declared against the lever):** entirely in the upper econ slices, where the CC_LIKE midcurve shape ratio climbs ≈1.04 → 1.5. The cheapest econ slice (the one that sets the low-end price) is already at incremental HR in every year (−0.19 to +0.14). The committed rung sits ≈0.4 above incremental (average HR including no-load). So L2 mainly cheapens the CC ramp above min-load; its effect on the C3a 2020 low-end floor is expected to be **small** (the plan's ≈ −$1/MWh annual bound is an upper bound, not a forecast).

## 2. Mechanism (rule 19: replace, never stack)

With `pjm_offer_midcurve_shape_segments=['CC_LIKE']` the belt **sets** the CC_REGULAR econ rows by a signed replacement, `bid = (mc_committed − vom)·m(s_g)/m(s_c) + vom`. L2 is a second construction on the same rows, so it can only **replace** the CC_LIKE shape scope:

- new field (proposed) `pjm_cc_econ_incremental_hr: bool = False` — when armed, CC_REGULAR econ-tranche `mc = HR_incr[plant] × fuel + vom + emissions`, with `HR_incr` the CAMPD heat-input-vs-gross-load slope (Huber fit, steady-state hours, CT-only meters levelled by EIA-923 net), derived once by a frozen derive script (rule 23); and it **removes CC_LIKE from the shape segments** in the same arm (the belt keeps LONG_RUN). The committed rung is unchanged (no-load stays there).
- Rule 13: unit physics, regenerates forward. Rule 21: zero free parameters (the slope is measured; the fit filters are fixed here: opTime ≥ 0.99 in h−2..h+1, load in [max(p5, 0.4·p99), p99], ≥ 200 h, slope ∈ [3, 15]).

## 3. Gates (fixed now)

STOP: S1 identity — armed econ `mc` equals `HR_incr × fuel + vom + emissions` to 1e-6 for every CC_REGULAR econ row; S2 footprint — every non-CC_REGULAR unit's `mc` is identical to the control; S3 direction — CC_REGULAR econ `mc` falls in every year (median); S4 no non-target flip — C2, C4, C8 do not go PASS → FAIL.
Pre-fixed outcome reading (reported; promotion on structure, owner's call): **C3a 2020 ≤ +10 %**, C3a 2023–2025 stay inside ±10 % (they pass by cancellation, so watch 2023 +5.2 %).

## 4. Control

Post-W0 PJM incumbent span (as in the R-13 PRECOMMIT §4); G-DRIFT zero-LP audit; 7 shards.

## 5. Interaction with R-13

R-13 (`gas_offer_margin_anchor_vintage`) moves the markup term on the same CC tranches. The two are run as separate single-delta arms against the same control, never jointly in a first solve.

## 6. Owner question (blocks building, not the PRECOMMIT)

The CC_LIKE shape form is identified on **measured PJM offers** (`pjm_offer_midcurve_*`, cell K). Replacing it with physics-incremental cost is measured-for-measured, not estimate-for-measured, but it drops the offer markup above incremental cost that real PJM CCs bid. Rule 14 asks for the more accurate quantity; for LMP formation, PJM's price is set by the offer, so the offer-derived shape may be the more faithful one. **Ruling needed:** may L2 replace the CC_LIKE shape scope (as here), or must it be redefined as the shape form on an incremental base (keep the measured offer ratio, swap the base HR from average to incremental)? The second form touches only the base and keeps the measured markup; this PRECOMMIT's gates apply to either.

**Desk ruling (2026-10-02, close-out desk `session_017wUwd6xxLRQKAYiT8G722P`):** REPLACE — L2 replaces the CC_LIKE midcurve scope (rules 19/26: one mechanism), and the PR that builds L2 deletes the old CC_LIKE shape scope in the same change. Build and solve wait for the post-W0 PJM keeper (the §4 control).
