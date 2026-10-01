# FINDING (pjm-h4, step 3) — the COAL `phys_*` arm is KILLED AT PHASE 0, and the
# measurement inverts its own premise: PJM's coal committed band is a DISCOUNT
# below measured physics, not a markup above it

**Session** `pjm-h4` · **ISO** PJM · **Date** 2026-09-13 · **Base** `origin/main` @ `33a7c961`
**ZERO LP.** Six `run_calibration.run_year(fleet_only=True)` rebuilds on the bundles' OWN
`meta.json` recipes — the rule-29 `[R-SCREEN]` clause-0 path. No shard was launched and the
parent ran no LP (rule 32 `[R-SHARD]` (a)). Nothing armed, nothing registered, no
`ScenarioConfig` field added, no matrix cell verdict moved.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNCHANGED.**
Step 1-2 of this session: `docs/RESULT-pjm-h4-bench-move-landed-2026-09-13.md`.

---

## 1. RESULT

> **The arm `FINDING-pjm-h2b` §3 left standing — register PJM's measured COAL `phys_*` keys and
> gate the coal tranches into the existing `gas_offer_net_revenue_margin` seam — does not reach
> a solve. Three measurements kill it, none of them a residual.**
>
> 1. **It cannot touch the largest measured gap, BY CONSTRUCTION.** 56 % of PJM's coal capacity
>    (27,732 of 49,365 MW) carries a markup of exactly **zero**: `mustrun`/`sync` are never
>    marked up, and the `committed` band's cap-weighted multiplier is **0.5539** against a
>    measured `phys_committed` of **0.916**. The mechanism is `max(0, mult − phys)` — a markup
>    COMPRESSOR — so a band sitting **0.362 × base-HR BELOW its own measured burn** is invisible
>    to it. **h2b §3's premise was that PJM coal "keeps the fully fuel-scaled multiplicative
>    markup". On the bands that carry the capacity, PJM coal carries a fuel-scaled DISCOUNT.**
> 2. **What it CAN reach is small, because PJM's measured incremental coal burn is flat.**
>    `marg_econ_low_p50` 0.803 and `marg_econ_high_p50` 0.809 differ by **0.006**. Cap-weighted
>    over the whole econ band the markup is **0.1202 → markup_hr 1.342 MMBtu/MWh**; `peak`
>    (992 MW) adds 0.0441 → 0.492.
> 3. **The pre-solve offer-array delta is SUB-DOLLAR fleet-wide in every one of the six years**
>    — **+0.51 / +0.54 / +0.16 / −0.17 / −0.09 / +0.02 $/MWh** (2020…2025), against a 2020
>    COAL_BIT residual of **+22.83 TWh**.
>
> **And rule 19 `[R-ONE-MECH]` is decisive on top of the magnitude:** coal's markup role is
> already owned by the gas-keyed passthrough sigmoid, whose above-1.0 limb is worth
> **$9.59/MWh in 2022 against this arm's $0.38** — **25×**. The prompt's own clause (c)
> requires REPLACEMENT of that role, never stacking; replacing it is a different and far larger
> change than registering `phys_*` keys, and it would move the 8/8 keeper.

## 2. THE CENSUS, AND WHY IT IS ON THE REAL KEEPER FLEET

Six `fleet_only` rebuilds, each on its own bundle's `meta.json` (2020-2022 →
`pjm_d4_4_TP`, 2023-2025 → `pjm_d4_4_A`), so every band multiplier, per-plant base heat rate,
tranche capacity and delivered fuel price is the keeper's own.

**ONE DECLARED SIMPLIFICATION, AND IT IS VERIFIED RATHER THAN ASSERTED.** The census runs with
`pjm_da_virtual_bids=False`: that layer APPENDS pseudo-units (`fleet = fleet + virtual_units`)
and writes bid prices onto THEIR OWN `fuel_prices` rows, and its corpus is licence-restricted
and ships README-only. Measured on 2022 with the corpus fetched, both ways: **553 coal tranches
either way, IDENTICAL on `unit_id`, `heat_rate`, `pmax` and delivered-fuel mean and standard
deviation for all 553.**

**An independent check that the artifact's population and the model's fleet coincide.** The
census's cap-weighted coal base heat rate is **11.176 MMBtu/MWh** against the artifact's COAL
`base_hr` of **11.197** — 0.2 %. That is the rule-14 `[R-ACCURATE]` admissibility test the
transplant would have to pass, and it passes; the arm does not fail for want of a valid
measurement, it fails on what the measurement SAYS.

### 2.1 The band structure, measured (2020; the fleet is stable across the span)

| band | MW | cap-wtd mult | measured phys | **markup** | markup_hr (MMBtu/MWh) |
|---|---:|---:|---:|---:|---:|
| `mustrun` | 14,059 | 1.0000 | — (never marked up) | **0.0000** | 0.000 |
| `sync` | 1,124 | 1.0000 | — (never marked up) | **0.0000** | 0.000 |
| **`committed`** | **12,550** | **0.5539** | **0.916** | **0.0000** | **0.000** |
| `econc00` | 3,440 | 0.6771 | 0.8032 | 0.0000 | 0.000 |
| `econc01` | 3,440 | 0.7432 | 0.8039 | 0.0000 | 0.000 |
| `econc02` | 3,440 | 0.8092 | 0.8045 | 0.0047 | 0.053 |
| `econc03` | 3,440 | 0.9035 | 0.8054 | 0.0981 | 1.096 |
| `econc04` | 3,440 | 1.0261 | 0.8066 | 0.2195 | 2.453 |
| `econc05` | 3,440 | 1.1487 | 0.8078 | 0.3409 | 3.810 |
| `peak` | 992 | 1.0374 | 1.000 | 0.0441 | 0.492 |

The econ band is six equal-capacity smoothing slices on the registered 0.6556 → 1.2664 ramp;
each slice's physical basis is interpolated at its own position, and because the measured basis
is flat (0.803 → 0.809) the interpolation is nearly a constant 0.806. **Two of the six slices
carry no markup at all and a third carries 0.0047.**

PJM has four coal supply curves; **bituminous is 91 % of the fleet** (44,879 of 49,372 MW) and
resolves to `COAL_BIT` {committed 0.548, econ_low 0.6556, econ_high 1.2664, peak 1.044} — the
KEEPER's `offer_curve_overrides` values, which deep-merge band-by-band over
`_PJM_OFFER_CURVE`, so registered `phys_*` keys would survive the override exactly as the gas
ones do.

## 3. STEP 3(c) — THE ANCHOR, IDENTIFIED

**A = 3.0970 $/MMBtu**: the 2023-2025 capacity-weighted mean of the model's OWN delivered coal
price AT THE LP SEAM (per-plant EIA-923 receipts under the keeper's `coal_plant_monthly_pricing`,
read off `fuel_prices` in the rebuild). This is the construction
`constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO` already states for this mechanism family, evaluated
on PJM's own series. Per year the seam reads **2.1551 / 2.1229 / 2.7247 / 3.2250 / 3.1145 /
2.9519**.

*(The flat 2.300 $/MMBtu `resolve_annual_coal_price` trajectory is NOT the seam price for this
keeper and must not be used for the anchor — the per-plant monthly receipts move the
capacity-weighted level by −6 % to +40 % across the span.)*

## 4. STEP 3(b) — THE PRE-SOLVE OFFER-ARRAY DELTA, PER BAND PER YEAR

`Δmc[g,t] = markup_hr[g] × (A − fuel[g,t])`, the exact form `apply_gas_offer_margin` applies.
Capacity-weighted $/MWh; `mustrun`, `sync` and `committed` are **identically zero in every year**
and are omitted.

| yr | econ Δ$/MWh | peak Δ$/MWh | **ALL-COAL Δ$/MWh** | econ footprint (10³ MW·$/MWh) |
|---|---:|---:|---:|---:|
| 2020 | **+1.206** | +0.458 | **+0.514** | **+24.9** |
| **2021** | **+1.266** | +0.474 | **+0.539** | **+26.1** |
| 2022 | +0.380 | +0.177 | +0.163 | +7.9 |
| 2023 | −0.396 | −0.068 | −0.167 | −8.2 |
| 2024 | −0.216 | −0.012 | −0.090 | −4.5 |
| 2025 | +0.035 | +0.073 | +0.016 | +0.7 |

### 4.1 Step 3(d) — the screen year on FOOTPRINT is 2021, not 2020

The card's metric is `|mult − phys| × |anchor − fuel| × coal energy`, and it predicted 2020 "on
the pjm-h2 table". Once the anchor exists the metric resolves to **2021 (26.1) ahead of 2020
(24.9)** — a 5 % gap, so the two are effectively tied, and both are ~3× 2022. Recorded because
the card's parenthetical was a prediction made before the anchor was computed, and a screen year
is pre-registered on the measured footprint, never on the residual.

### 4.2 The direction, REPORTED and explicitly NOT a gate

Rule 1 `[R-STRUCT]` forbids selecting a mechanism on whether it moves the residual, so this is
a report line and nothing else. The delta makes coal **dearer** in 2020/2021 (where COAL_BIT is
+22.83 / −3.71 TWh) and **cheaper** in 2023/2024 — the two training years whose COAL_BIT sits at
+2.10 and −0.12 TWh inside an 8 TWh band on an 8/8 keeper. **The arm's own sign is against the
keeper in the training span.** It is not why the arm is killed, and it would not have saved it.

## 5. WHY THIS IS A KILL RATHER THAN A SMALL-BUT-REAL PASS

**(a) It cannot reach the defect the same artifact reports.** §2.1's largest measured
discrepancy is `committed`: registered **0.5539** vs measured **0.916** on **12,550 MW**. That
is PJM's coal min-load block offered at 55 % of base heat rate while those exact units burn
92 % of base at min load. A markup compressor cannot act on it — `max(0, ·)` is clip-at-zero by
design ("no compression, no negative margin"). So the mechanism arrives at PJM's coal offer
surface, finds the one large measured gap pointing the wrong way for it, and prices the small
one.

**(b) Rule 19 `[R-ONE-MECH]`: the incumbent markup is the sigmoid, and it is 25× bigger.** PJM
bituminous runs a gas-keyed logistic {floor 0.65, ceil 1.32, gas_mid 3.40, slope 2.5} whose
above-1.0 limb is a markup by its own code comment ("> 1.0 marks the bid up to suppress
over-dispatch"). On `FINDING-pjm-h2b` §1.1's keeper-series passthroughs, that limb is worth, at
this census's cap-weighted base HR and seam fuel:

| yr | passthrough (h2b) | **sigmoid markup $/MWh** | this arm, econ $/MWh | ratio |
|---|---:|---:|---:|---:|
| 2020 | 0.674 | **0.000** (a discount) | +1.206 | — |
| 2021 | 1.011 | 0.261 | +1.266 | 0.2× |
| **2022** | **1.315** | **9.593** | **+0.380** | **25×** |
| 2023 | 0.757 | 0.000 (a discount) | −0.396 | — |
| 2024 | 0.753 | 0.000 (a discount) | −0.216 | — |
| 2025 | 0.965 | 0.000 (a discount) | +0.035 | — |

The card's clause (c) requires the new gate to REPLACE the sigmoid's markup role. Doing that
means clipping the sigmoid at 1.0 — which removes **$9.59/MWh** from PJM's 2022 coal offer and
would move the keeper materially. That is a legitimate change to charter, but it is a different
change from "register the measured `phys_*` keys", it is the dominant term rather than the one
being proposed, and it cannot ride in as a side effect of this arm.

**(c) The magnitude is short of its own object by an order of magnitude, on PJM's own yardstick.**
The record's calibration of "how much coal moves per $/MWh of offer": pjm-170's coal-sigmoid
ceiling probe moved COAL_BIT **+2.70 → +4.09 TWh** (1.4 TWh), and the registered 1.25 → 1.32
ceiling change moved the dear-gas year **+6.3 → +3.3 TWh** (3.0 TWh) — both of them shifts on
the WHOLE coal offer, every band, every hour. This arm delivers **+1.21 $/MWh on 42 % of the
fleet and exactly nothing on the other 58 %**, i.e. strictly less offer movement than levers
already measured at 1.4-3.0 TWh. The object is **22.83 TWh**.

## 6. WHAT I ROUTE RATHER THAN OPEN

**The committed-band gap is a real rule-14 `[R-ACCURATE]` finding and it is NOT this
mechanism's.** PJM's registered coal `committed` 0.548 sits against a measured min-load
block-average burn of 0.916 on 12.5 GW, and the same artifact PJM already trusts for its gas
bands says so. Re-pricing it is a **band-multiplier** change — the authorized price-tuning
channel of the rules 1/13 amendment, not a new mechanism — and it is large: +65 % on the
min-load block of 12.5 GW, which would make PJM coal much dearer at min load in every year and
every hour it is committed. That needs its own charter, its own ex-ante declaration and its own
year-invariance argument under condition (b). **I do not open it here and I do not recommend it
on the strength of a residual.**

**Not adjudicated, and stated so:** whether the coal sigmoid should be clipped at 1.0. It is the
rule-19 incumbent, its parameters' own provenance is a 2023-2025 volume residual (the rule-23
`[R-FROZEN-DERIVE]` wart h2b §1.1 already flagged), and it is the dominant markup on PJM coal in
the dear-gas years. That is a bigger and more consequential question than the arm I was asked to
phase-0, and it belongs to the owner-declared-closed pjm-142 price-formation frontier.

**Consequence for the lane, stated plainly:** with this arm killed, **PJM's held-out C1 residual
has no open admissible arm.** 2020 COAL_BIT **+22.83 TWh** is untouched by the bench move (step
1) and unreachable by this mechanism; CC_REGULAR 2021/2022, now **+16.98 / +12.81 TWh** after
the bench move, remains h2b §1.2's on-hours object, which a price-position lever does not reach.

## 7. WHAT WAS NOT DONE, AND WHY

* **No solve, no shard, no screen year spent.** Rule 29 `[R-SCREEN]` clause 0 is explicit that
  the zero-LP phase exists to kill arms, and the card required (a)-(d) before any LP. (b) and
  (c) are delivered above and (b) does not clear a structural pre-registration, so nothing was
  launched. The 2020 and 2021 legs the card contemplated are **not spent**.
* **No build.** Registering COAL `phys_*` and adding a gate would have been ~5 source files plus
  a matrix row in every ISO shard (rule 28(c)); building a mechanism whose own arithmetic says
  it is inert on 56 % of the fleet and sub-dollar on the rest is the cost rule 29 clause 0
  exists to avoid. **No `ScenarioConfig` field was added, so no matrix row is owed** — and no
  cell verdict moves, because nothing was tested (rule 28 `[R-MECH-MATRIX]` (b) governs a
  mechanism that was TESTED; `coal_offer_net_revenue_margin` stays `U` on pjm-146's standing
  instrument block, which this session does not disturb).
* **Nothing deleted** (rule 31 `[R-RETAIN]`). Nothing was solved, so there is nothing to retain
  or promote from step 3.

## 8. RULES

Rule 1 `[R-STRUCT]` (the arm is judged on what the mechanism DOES; §4.2's direction is reported
and gates nothing) · rule 14 `[R-ACCURATE]` (the measured artifact is preferred and its
population validated at 0.2 %; §6 keeps the discrepancy it exposes on the books rather than
burying it) · rule 19 `[R-ONE-MECH]` (§5(b) — the sigmoid is the incumbent markup and this arm
would stack on it) · rule 21 `[R-DOF]` (no free parameter was introduced) · rule 28
`[R-MECH-MATRIX]` (no cell verdict moves; nothing tested) · rule 29 `[R-SCREEN]` clause 0 (the
zero-LP phase killed the arm — the pre-registered good outcome) · rule 30(c) (no held-out year
touches PJM's determination) · rule 31 `[R-RETAIN]` (nothing solved) · rule 32 `[R-SHARD]` (a)
(the parent ran no LP).
