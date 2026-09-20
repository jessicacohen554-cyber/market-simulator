# RESULT — nyiso-245: the shape-only offer surface is REFUSED on NYISO's own book, and the refusal locates the object precisely — it is CROSS-UNIT DISPERSION of the conditional LEVEL, not a within-unit shape

**Session** nyiso-245 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `5c0bec8b`, **rebased mid-session onto `e8b80102`**
at the owner's instruction.
**PRECOMMIT** `docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md`, committed at
**`398f0437`** before any gated number was computed; the rebase moved that commit to **`5cbf4fef`**
with its content unchanged.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025} — **UNCHANGED.
Nothing armed, promoted or registered for this mechanism. No `ScenarioConfig` field survives in
the tree. NYISO still reads `CALIBRATED` on its ISO tier, with C3c the lone ledgered caveat.**
**Predecessor** `docs/RESULT-nyiso244-the-object-is-in-the-body-not-the-top-2026-09-20.md` §7.

> ## HEADLINE
> 1. **BOTH LIMBS OF nyiso-244's RE-OPEN CONDITION WERE SATISFIED, AND THE MECHANISM WAS REFUSED
>    ANYWAY, ON A THIRD GATE.** That re-open condition is now **SPENT** and must not be cited
>    again.
> 2. **THE FORM EXISTS AND REACHES.** `miso_offer_surface_measured` is an econ/midcurve form that
>    is class-free *by construction* — a within-unit price RISE on a within-unit position
>    coordinate — so P-27's masking cannot block it. Its own row gate tags **3,702.3 MW of the
>    4,715.7 MW object, 78.5 %**, against the 50 % bar nyiso-244 set and this session carried over
>    unchanged. nyiso-244's peak-rung form reached 15.8 %.
> 3. **AND RULE 19 CLEARS, WITH A FINDING INSIDE IT.** Five armed non-base writers, zero tagged
>    rows that are also base rows, an assignment form that replaces rather than stacks. On the way:
>    in the 70 missed winter hours the armed `gas_offer_net_revenue_margin` contributes a
>    **capacity-weighted mean of −$51.75/MWh** to those very rows, negative in **88.3 %** of
>    row-hours. Its term is `markup_hr × (anchor − fuel)`, so it goes negative exactly when
>    delivered gas spikes above the frozen anchor.
> 4. **G3a REFUSES IT: 0.0 % of 12 populated cells are monotone, against an 80 % bar.** NYISO's
>    measured Δ ladder rises to position 0.6–0.8 and then **collapses** at the top, where the
>    capacity-weighted median is **$0.03–$1.62**. Its largest value **anywhere** is **$7.28/MWh**.
>    This is a corpus-shape test decided on the derived artifact alone — **not** on any residual
>    (rule 1 `[R-STRUCT]`).
> 5. **AND THE DIAGNOSTIC SAYS WHY, WITH NO COHORT AND NO COMPOSITION ASSUMPTION.** Within-unit
>    differences over gens present in **both** windows, so the ~9.4 GW fleet-scope gap cancels
>    exactly. Missed minus ordinary winter 2022, capacity-weighted median $/MWh:
>
>    | | curve BOTTOM | within-unit RISE |
>    |---|---:|---:|
>    | **market** (P-27, all gens) | **+26.66** | **+0.12** |
>    | **market, multi-block only** (203 gens, 31,547 MW — every price taker excluded) | **+19.01** | **+1.03** |
>    | **model** (the keeper) | **+40.00** | **+11.34** |
>
>    **The market does not steepen within units, and the model already steepens 11× more than it
>    does.** There is no conditional SHAPE object to transfer, which is why a shape-only form is
>    blind to the object **by construction rather than by accident**.
> 6. **WHAT THE MARKET ACTUALLY DOES IS DISPERSE.** Its level response is **+$19 at the median,
>    +$112.05 at p75 and +$231.59 at p90** — a fat right tail of units that reprice enormously. The
>    model moves nearly every unit by the same **~$40** (p75 +$44.36) and **none** by more. **The
>    object is the cross-unit DISPERSION of the conditional level response.**
> 7. **NO ARM SHARD, DELIBERATELY** (rule 34 `[R-SHARD-PROMOTABLE]`). **Four CONTROL shards were
>    spent and are a separate, independently owed deliverable** — see §6.

---

## 1. WHAT WAS GATED, AND THE ONE THING THIS SESSION DID DIFFERENTLY

nyiso-244 §7 left a two-limb re-open condition. This session's PRECOMMIT satisfied both **before**
proposing anything, then added four more gates, and fixed all six at `398f0437` before a single
gated number was computed. The gate that refuses — **G3a** — is a property of NYISO's own submitted
book. It cannot be argued with and it does not depend on what the model does.

**The mechanism under design.** `ScenarioConfig.nyiso_offer_surface_measured`, a NYISO member of
the `miso_offer_surface_measured` family (`data/offer_curves.py::apply_miso_offer_surface`,
`scripts/data/derive_miso_offer_surface.py`):

```
p_j = step_mw_j / uol_mw            own-curve POSITION, (0, 1]
D_j = price_j   - price_1           own-curve RISE, $/MWh
mc[g, t] := mc[base(g), t] + D(p̄_g, state_bin(t), gas_bin(t))
```

**Why this family and not another.** MISO adopted it for the reason NYISO needs it, in its derive's
own words: *"Class-free by necessity, not by preference. MISO's masked corpus carries no fuel or
technology attribute and miso-138 built and REFUTED the offer-side class bridge."* **nyiso-244 §4 is
NYISO's miso-138** — the cohort NYISO's masking allows, selected by NYISO's own published 10-Minute
Non-Synchronized Reserve product, passed V1 scope at 0.043 and failed V2 (0.303) and V3 (1.328).
Both of this form's coordinates are within-unit, so it **never asks what the masked gen is**.

**Rule 25 `[R-ISO-SCOPE]`.** Reused: the method, the population rules, the code shape and the
family's registered bin geometry. **Refused: every MISO Δ value.** Every number below is measured on
NYISO MIS P-27 against NYISO's own delivered-gas series and NYISO's own measured net load.

**Derive:** `scripts/data/derive_nyiso_offer_surface.py` → committed artifact
`data/raw/_validation-source/nyiso_offer_surface_positional.json`. Its self-test passes T-1
(recovery of a known answer), **T-2 (level invariance — shifting every unit's whole curve by a
constant leaves every Δ bit-identical)** and T-3 (a single-block price taker's Δ is 0).

---

## 2. G1 — REACH. IT CLEARS, AND THE REASON IS A MEASUREMENT nyiso-244's SCOPE COULD NOT SEE

Construction is nyiso-244 §3.2's, unchanged so the two sessions' arithmetic stays comparable: per
class and hour the class's own committed P1 dispatch is served by its cheapest rows, so the idle set
is its most expensive available capacity. 70 missed winter hours, 2022, median MW:

| class | idle < $300 | on the family's row gate | on a plant-structural gate |
|---|---:|---:|---:|
| ST_GAS | 2,079.9 | **1,661.8** | 1,661.8 |
| CT_PEAKER | 1,208.2 | **997.1** | 997.1 |
| CC_CHP | 1,128.6 | **846.3** | 1,093.4 |
| CC_REGULAR | 911.7 | **197.1** | 672.7 |
| CT_CHP | 50.3 | 0.0 | 13.1 |
| ST_CHP | 5.1 | 0.0 | 3.6 |
| **TOTAL** | **5,383.8** | **3,702.3** | **4,441.7** |

**Reach = 78.5 % against a 50 % bar. PASS**, on the incumbent-tag gate, so the PRECOMMIT's
alternative plant-structural gate (94.2 %) was **not taken** — it was available only if the first
missed, and it did not.

**Why it clears where nyiso-244's form did not, stated as a measurement.**
`gas_offer_net_revenue_margin` is **LIVE on NYISO's ECON bands**: `econ_low`/`econ_high` sit above
their `phys_*` on CT_PEAKER (1.000 vs 0.661/0.658), ST_GAS (1.000 vs 0.830/0.828), CC_REGULAR (0.950
vs 0.784; 1.000 vs 0.925) and CC_CHP (1.240 vs 1.103). So **298 of 715 rows** carry
`offer_markup_hr > 0`, and they are econ-dominated (`econlo` 55/59, `econhi` 54/58, `econc00–05`
30/33 each, `peak` 38/76, `committed` 2/80). nyiso-244 §2.1 enumerated the **peak** band only —
correctly, for its own scope, where `phys_peak == peak` makes the mechanism inert — so this was
outside what that session had to look at.

---

## 3. G2 — RULE 19 `[R-ONE-MECH]` ON THE ECON RUNG. IT CLEARS, AND CARRIES A FINDING

**(a) Enumeration, from the keeper's own `run_config.json` and not from memory.** Five armed fields
can write a NYISO non-base rung: `gas_offer_net_revenue_margin`, `gas_offer_margin_zonal_anchor`,
`gas_offer_margin_zonal_anchor_vintage`, **`nyiso_st_gas_econ_bands_deleaked`** and
`nyiso_ct_peaker_committed_measured`. One field name-matched the screen and is **adjudicated rather
than filtered**: `nyiso_zonal_loss_surface` splits internal transmission **chain links**
(`model/interchange/nyiso.py`, `spec.py:3844`) and writes no generator row.

**(b) Replace, never stack — measured, not asserted.** The form is an **assignment**, so nothing an
incumbent wrote into a tagged row survives. The one way that could fail is a row that is both a
target and some other target's base: **zero tagged rows are also base rows.**

**(c) The de-leak's own open root cause.** `nyiso_st_gas_econ_bands_deleaked` sets ST_GAS
`econ_low = econ_high = 1.0` and its code comment states it *"does NOT identify the markup … the
identification stays an OPEN ROOT CAUSE against NYISO scarcity/reserve (RCPF/AS) price formation,
issue #1344."* A measured surface pricing the rise above that neutral band is **the successor that
open item names**, not a second mechanism beside it.

**THE FINDING INSIDE G2, reported because it outlives this refusal.** The incumbent's own
contribution to the tagged rows, `markup_hr × (anchor − fuel)`:

| window | median | p05 | p95 | share of row-hours negative | cap-weighted mean |
|---|---:|---:|---:|---:|---:|
| all 8,760 h | +0.006 | −39.67 | +21.08 | — | — |
| **70 missed winter hours** | **−9.98** | **−389.74** | +2.78 | **88.3 %** | **−51.75** |

**In the hours the model fails to price, the armed mechanism is pushing those very offers down by
~$52/MWh.** That is intended behaviour on its own grounding — it holds the margin fuel-invariant —
but §5 measures the real book doing the opposite, and that is the live hypothesis a successor
inherits.

---

## 4. G3 — THE CORPUS. THIS IS THE GATE THAT REFUSES

### 4.1 The artifact

Pooled 2022–2025, DAM, capacity-weighted median Δ per (gas × state × position) cell. Gas bin edges
**[3.0711, 5.0953] $/MMBtu**. The ladder, gas bin 2 (highest tercile), $/MWh:

| state bin | 0.0–0.2 | 0.2–0.4 | 0.4–0.6 | 0.6–0.8 | 0.8–0.9 | **0.9–1.0** |
|---|---:|---:|---:|---:|---:|---:|
| 0 (loosest) | 0.03 | 1.07 | 1.77 | 4.88 | 4.12 | **0.03** |
| 1 | 0.03 | 1.12 | 2.38 | 5.58 | 5.03 | **0.03** |
| 2 | 0.03 | 0.78 | 3.23 | 6.67 | 5.03 | **0.03** |
| 3 (tightest) | 0.03 | 0.03 | 4.28 | **7.28** | 5.03 | **0.03** |

Every cell in every gas bin has this shape. The top position bin carries by far the most weight
(68–78 M MW-hours against 1–36 M elsewhere), because the P-27 blocks are cumulative and the last one
equals the UOL.

### 4.2 The verdicts

* **G3a — MONOTONICITY: FAIL. 0.0 % of 12 populated cells**, against an **80 %** bar. A real
  submitted curve rises; this ladder rises and then falls. **Under PRECOMMIT §3 this refuses the
  mechanism before a shard.**
* **G3b — THE CONDITIONING DRIVER: PASS, 3 of 4 years** (bar 3), and honestly rather than
  comfortably — the quantity it passes on is $0.03–$1.62:

  | year | loosest state bin | tightest | rises |
  |---|---:|---:|---|
  | 2022 | 0.025 | 0.025 | **no** |
  | 2023 | 0.075 | 1.625 | yes |
  | 2024 | 0.375 | 1.625 | yes |
  | 2025 | 0.075 | 0.625 | yes |

* **G3c — CONTAMINATION: reported at full magnitude, gated on nothing**, exactly as pre-registered.
  Single-block price takers are **34–43 % of unit-hours** and **9.1–12.7 % of capacity**
  (2022 0.4322/0.1266 · 2023 0.4062/0.1083 · 2024 0.3382/0.0914 · 2025 0.3508/0.0974). **They were
  NOT excluded**, because the PRECOMMIT fixed in advance that the family's own population rules keep
  them and that excluding them *"is a DIFFERENT mechanism and needs its own PRECOMMIT"* — and
  because the bias is conservative. §5 shows the refusal survives excluding them anyway, so nothing
  turns on it.

---

## 5. G4 / G5, AND THE DIAGNOSTIC THAT LOCATES THE SUCCESSOR

### 5.1 G4 and G5, measured by simulating the reprice in numpy at zero LP

* **G4 — NOT INERT: PASS.** 8,247.5 MW of repriced capacity moves ≥ $1.00/MWh in the median missed
  winter hour (bar 500 MW). But the **median move is −$1.32/MWh** and **72.7 % of row-hours move
  DOWN**: faithfully applied, the measured ladder would *flatten* the model.
* **G5 — C1/C2 EXPOSURE, as the PRECOMMIT required in advance.** **61.6 % of thermal capacity**
  sits on repriced rows; median move −$3.38/MWh over all hours, p95 +$6.72. This is a large
  intervention, which is exactly why the standing bar was written down before the derive.
* **REPORTED, GATING NOTHING** (rule 1 `[R-STRUCT]` forbids gating on the residual): the induced
  movement in nyiso-244 §6.1's differenced statistic — MW withdrawn from below *P*, missed vs
  ordinary.

  | | model now | with the surface | move | market |
  |---|---:|---:|---:|---:|
  | $150 | 3,610.7 | 4,533.9 | +923.2 | 7,674.5 |
  | $200 | 1,213.1 | 1,891.7 | +678.6 | 6,202.5 |

  It moves toward the market, by 14 % and 11 % of the gap. **This is not why the mechanism is
  refused and could not have been** — G3a is decided on the artifact alone.

### 5.2 THE DIAGNOSTIC — descriptive, and the most useful thing in this session

*Not a gate. The six gates were decided before it ran and nothing here flips one.* Every statistic is
a **within-unit difference between the two windows, over gens present in BOTH**, then a
capacity-weighted median — so fleet scope and composition cancel exactly, the discipline nyiso-243
Leg 2 and nyiso-244 §6.1 imposed on themselves. Missed minus ordinary winter 2022, $/MWh:

| | curve BOTTOM | curve TOP | within-unit RISE |
|---|---:|---:|---:|
| **market** (P-27, all gens) | **+26.66** *(p25 0.00, p75 +137.06)* | +27.00 | **+0.12** |
| **market, multi-block only** (203 gens, 31,547 MW) | **+19.01** *(p75 +112.05, p90 +231.59)* | +15.93 | **+1.03** *(p75 +1.01, p90 +33.52)* |
| **model** (the keeper) | **+40.00** *(p25 0.00, p75 +44.36)* | +68.43 | **+11.34** |

**Read the RISE column first.** The market's within-unit shape response to the event is **+$0.12**,
and **+$1.03 with every single-block price taker excluded** — so G3c's contamination is not what
killed it. The model's is **+$11.34**. There is no conditional shape object to transfer, and the
model already over-steepens by 11×. A shape-only form is blind to this object by construction, and
substituting the market's shape for the model's would make the model *flatter* — which is precisely
what G4 measured from the other side.

**Then read the BOTTOM column's spread.** The market's level response is **+$19 at the median but
+$112.05 at p75 and +$231.59 at p90**. The model's is **+$40 at the median and +$44.36 at p75** —
nearly uniform, with no tail at all. The market's conditional response is concentrated in a minority
of units that reprice by hundreds of dollars; the model moves everything by the same amount.

**So the object is the CROSS-UNIT DISPERSION of the conditional LEVEL response.** That is a
different class of mechanism from anything NYISO has tested, and the repo already carries one for
it: `miso_offer_spread_anchored` / `miso_offer_level_dispersion` (miso-179/180), *"anchored
SPREAD-ONLY across-unit dispersion graft"*. Under rule 28(d) it enters NYISO as **`U`** and must
derive its own parameters from NYISO's own book.

---

## 6. THE FOUR CONTROL SHARDS — A SEPARATE, INDEPENDENTLY OWED DELIVERABLE

**These are not the refused mechanism's shards.** They were launched because the **G-DRIFT** audit
(rule 29 `[R-SCREEN]` (b)) found a **LIVE** hunk on the backcast path since the keeper's `git_sha`
`5356fb71`: commit **`cb1e60b7`**, which defaulted `MARKET_SIM_WARMSTART_XYEAR` and
`MARKET_SIM_P1_BASIS_SEED` **OFF** and added rule 36 `[R-YEAR-ISOLATION]`. Rule 36 (f) states the
consequence plainly: *"Every ISO's keeper was solved through the CLI with both knobs ON, so every
keeper carries some of this artifact and its registered numbers will move when it is next
re-solved,"* and *"its size is unmeasured outside MISO."*

So the committed NYISO keeper is **not a valid form-4 control** for anything solved at HEAD, and the
NYISO re-solve rule 36 (f) anticipates was owed to this lane regardless of the offer surface. Four
shards, **one year each** (rule 36 (a) — the one place rule 32 (b)'s fan-out ban does not apply),
replaying the keeper's own recipe at the pinned SHA `4a01ae6086afa9f2f5a4776f9bfaaf1bda592a86` with
both knobs off.

They also regenerate `legitimacy_diagnostics.json` through the current
`scripts/legitimacy_diagnostics.py`, which is the handoff's object (2) — the stale NYISO gating
artifact nyiso-242 left behind after landing three scorer fixes — discharged **by re-deriving it
rather than by hand-patching it**.

The other 14 changed files in the G-DRIFT window are classified INERT for a NYISO backcast: four new
`ScenarioConfig` fields, **all `bool = False`** and none in the keeper's recipe
(`measured_st_heat_rates`, `caiso_citygate_blackout_bridge`, `commitment_floor_window_netload`,
`benchmark_membership_vintage_union`); another ISO's branch (`3b719484` PJM seam ladder, `49a8f17b`
NWPP, the caiso-288/289 citygate work); and a forecast-only path
(`3fc20b97`, `model/capacity_evolution/new_entry.py`, which a `mode="backcast"` run never enters).

### 6.1 What 2022 measures — and what it deliberately does NOT

**NYISO 2022, replayed at HEAD with year isolation and both knobs OFF, reproduces the committed
keeper EXACTLY.**

| statistic | result |
|---|---|
| max \|Δ class TWh\| over 12 classes | **0.0000** |
| zonal price cells moved (P1, internal zones) | **0 of 43,800** |
| mean zonal price | 76.159 → **76.159** $/MWh |
| hours with max zonal dual > $300 (the C3c statistic) | 7 → **7** |

**This is one year and it is the LEAST informative one.** In the MISO incident that produced rule 36
the **first year of each solve leg reproduced** (max \|Δ class TWh\| 0.0048 and 0.1440) and the
divergence appeared in the **later** years (7.1586 / 24.1796 / 4.0034). 2022 is the first year of
NYISO's span, so an exact reproduction here is what the defect itself predicts. **2023, 2024 and
2025 are the years that decide whether NYISO carries it**, and until they land nothing about NYISO's
exposure is established — see §8 for their status.

### 6.2 Object (2) — the stale `legitimacy_diagnostics.json` — ANSWERED FOR NYISO, AND IT IS A NO-OP

The handoff asked for the nyiso-242 scorer fixes to be confirmed on NYISO before committing.
Regenerated from the control bundle through the current `scripts/legitimacy_diagnostics.py` and
compared row-for-row against the keeper's committed artifact, 2022:

| | D1 | D2 | D4 | D5 | D9 | D10 |
|---|---:|---:|---:|---:|---:|---:|
| rows (keeper / control) | 7 / 7 | 8 / 8 | 23 / 23 | 0 / 0 | 0 / 0 | 2 / 2 |
| rows only on one side | 0 | 0 | 0 | 0 | 0 | 0 |
| **numeric moves** | **0** | **0** | **0** | **0** | **0** | **0** |
| `passed` | True / True | True / True | False / False | True / True | True / True | True / True |

**Zero numeric moves in total, every gate verdict identical, and every gate threshold unchanged.**
The only structural difference is the new `dispatch_source` stamp (nyiso-242's first fix), present in
the regenerated artifact and absent from the keeper's. **So no NYISO determination moves**, which is
what the handoff predicted cross-ISO and is now measured on NYISO itself.

*One thing NOT claimed.* nyiso-240 §A.6 recorded nine rows that wobble at the 3rd decimal on
re-running against an **identical** bundle. This comparison is against a **fresh solve**, so 0 moves
is evidence the wobble is not systematic here — but it is 2022 only and it does not close that open
item.

**Status and the retrievability statement (rule 34 `[R-SHARD-PROMOTABLE]` (e)): see §8.**

---

## 7. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — every bar was fixed at `398f0437` before any gated number, and two of
  them (the 50 % reach bar, the 3-of-4 driver bar) are nyiso-244's own, carried over **unchanged**
  so they cannot be accused of having been re-set to fit. The refusal rests on **G3a, a corpus-shape
  test on the derived artifact**, never on a residual; the numbers that **favour** the mechanism are
  reported at full magnitude beside it (G1 78.5 %, G2 clean, G3b 3/4, G4 clears, and the +923 /
  +679 MW movement toward the market).
* **Rule 13 `[R-MEASURED]`** — the artifact is pooled 2022–2025 and never per-year; all three
  drivers exist in a forecast year; Δ is a **submitted offer**, never a cleared price, a realised
  dispatch or a residual.
* **Rule 19 `[R-ONE-MECH]`** — §3, discharged on the econ rung against a different armed set than
  nyiso-244 faced.
* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters. The position grid and net-load
  percentiles are the family's / the registered cross-ISO geometry, adopted unchanged **because
  inventing NYISO's own invites a sweep**; only the gas edges are NYISO's own, and they are
  quantiles of NYISO's own series. **No ScenarioConfig field survives in the tree.**
* **Rule 23 `[R-FROZEN-DERIVE]`** — both geometries frozen in the PRECOMMIT before any measurement.
* **Rule 25 `[R-ISO-SCOPE]`** — the method crosses; no Δ does.
* **Rule 26 `[R-DELETE]`** — the `ScenarioConfig` fields and the `apply_nyiso_offer_surface` applier
  written for the refused form were **REVERTED, not committed default-off**. A refused mechanism
  that still parses is a re-armable answer key, and it would also have obliged a matrix base row
  plus a cell line in all seven ISO shards for something that does not exist. **Git history is the
  record.**
* **Rule 28 `[R-MECH-MATRIX]`** — `measured_offer_surface` NYISO **stays `G`**, its evidence
  rewritten, nyiso-244's re-open condition marked **SPENT**, and a new one written naming the
  dispersion class. **No `ScenarioConfig` field is added, so duty (c) has no subject.**
  `check_mechanism_matrix.py` passes.
* **Rules 31–36** — §6 and §8.
* **Rule 27 `[R-PUSH]`** — no existing source file ≥300 lines is modified in the final tree:
  `scenarios.py` (21,896 lines) and `offer_curves.py` (1,847 lines) are **byte-identical to
  `origin/main`** after the revert.

**`tests/scoring`** — this session ships **no solve-path code**, so it adds zero to the unowned
22-failure baseline (`test_audit_keepers_lineage`, `test_golden_manifest_provenance`), which remains
unowned and unclaimed here.

---

## 8. ARTEFACTS, AND THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`)

| artefact | what it is |
|---|---|
| `docs/PRECOMMIT-nyiso245-…-2026-09-20.md` | the six gates, fixed at `398f0437` / `5cbf4fef` |
| `scripts/data/derive_nyiso_offer_surface.py` | the derive, with its T-1/T-2/T-3 self-test |
| `data/raw/_validation-source/nyiso_offer_surface_positional.json` | the derived artifact (§4.1) |
| `scripts/probes/nyiso245_position_surface_gates.py` → `_nyiso245_gates_g1g2.json` | G1, G2 |
| `scripts/probes/nyiso245_surface_effect.py` → `_nyiso245_surface_effect.json` | G3, G4, G5 |
| `scripts/probes/nyiso245_level_vs_shape.py` → `_nyiso245_level_vs_shape.json` | §5.2, the diagnostic |
| `scripts/probes/_nyiso245_fleet_cache.py` | the zero-LP fleet/gas cache (gitignored output) |
