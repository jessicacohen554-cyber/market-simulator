# FINDING — ERCOT-107/108: the 2023 scarcity tail is structurally bounded; the on-line-capacity envelope is BISTABLE and the ORDC span is NOT the over-fire confound

**Date:** 2026-07-24 · **Lane:** ERCOT scarcity tail (ERCOT-101 successor)
**Keeper:** `2026-07-23-ercot100-netrev-margin-keeper` — **UNCHANGED** (no promotion, no
config change).
**Runs registered:** `2026-07-24-ercot107-envelope-pricing-basis`,
`2026-07-24-ercot108-envelope-in-lp` (both PROBE, both NOT-YET).
**Disposition:** the ERCOT-107 charter's hypothesis is **REFUTED**. The decision fork
lands on **STOP tuning the reserve-side (cap/ORDC) family**. This is a scoped result,
**not** a finding that the phantom depth is unaddressable — the quantity-side successor
(re-price the startable-but-OFF increment at start-inclusive offers) is measured,
chartered, unbuilt and owner-gated. **See §6 before signing anything.**

---

## 1. What was chartered vs what was actually testable

The ERCOT-107 charter proposed "the one untested combination": cap phantom headroom
(envelope) **+** remove the ORDC-span over-fire confound (realized-adder RTORPA,
right-sized to the ~5.5 GW the market actually held) **+** the recovered 2023 RT SCED
offer wall.

Two premises of that charter turned out to be false, and both are load-bearing.

**(a) The prescribed flag set was not new — it is `ercot103`.** The charter's
`--set` block (`ercot_multiproduct_as_coopt` + `ercot_ordc_only_scarcity` +
`ercot_ordc_total_reserve=false` + `ercot_online_capacity_envelope_extreme`) is the
flag-for-flag configuration already solved as `ercot103_realized_adder` (2026-07-24
04:29). ERCOT-107 reproduces it: **$41.46 → $41.21** zonal `model_lw`. The only new
ingredient was the recovered wall, and the wall is fit-neutral in this composition
exactly as it is in the keeper composition (`ercot105`: $46.76 → $46.50).

**(b) The "cap phantom headroom" leg never entered the LP.** `ercot_ordc_only_scarcity`
and an in-LP envelope cap are *mutually exclusive by construction*, not merely by the
rule-19 `__post_init__` guard. In `model/reserves/spec.py` (v3 comment, ~L1280):

```python
online_capacity_pricing_mw = online_capacity_cap
online_capacity_cap = None          # <- the LP row is NOT installed
```

Under `ordc_only` the envelope becomes a **pricing-only basis** for the post-solve
realized-room RTORPA; the LP carries no committed-capability constraint. So the
charter's leg 1 (cap headroom) and leg 2 (realized adder) can never be composed — the
run tested legs 2+3 with leg 1 inert. Declaring the tail "structurally bounded" off
that run alone would have rested on a partially-inert test.

ERCOT-108 was therefore solved to fill the genuinely-missing cell — the envelope as a
real **in-LP** supply cap with the ORDC total-reserve span **off**, i.e. the charter's
*intent* (headroom capped, reserve demand right-sized to the measured AS plan rather
than the ~10.7 GW span). That cell existed in no prior run.

## 2. The completed 2×2 (2023, zonal C3a on the rubric-v2.4 `rt_lw` basis)

Actual `$64.32`. C3c settle counts vs the 181-hour actual tail.

| run | envelope | ORDC total-reserve span | RT scarcity pricing | `model_lw` | **C3a** | C3c |
|---|---|---|---|---|---|---|
| keeper `ercot100` | off | **in-LP** | in-LP span | $46.76 | **−27.3 %** | 76/181 |
| `ercot105` (+wall) | off | **in-LP** | in-LP span | $46.50 | **−27.7 %** | 72/181 |
| `ercot103` | pricing-only | off | realized RTORPA | $41.46 | **−35.5 %** | 71/181 |
| **`ercot107`** (+wall) | pricing-only | off | realized RTORPA | $41.21 | **−35.9 %** | 69/181 |
| `ercot106` (+wall) | **IN-LP cap** | **in-LP** | in-LP span | $514.31 | **+699.7 %** | 963/181 |
| **`ercot108`** (+wall) | **IN-LP cap** | **off** | measured AS plan only | $502.07 | **+680.6 %** | 963/181 |

Target band was `model_lw` ≈ $55–90 (C3a within ~±25 %). **No cell reaches it.**

## 3. The two findings

**F1 — the envelope is BISTABLE; there is no intermediate state.** Whenever the
envelope is an in-LP row the model prices **963** hours above the $200 tail against an
actual 181 (5.32×), with the `[30,80)` band — 1,948 hours whose actual mean is $44.7 —
clearing at **$921–954**. Whenever it is not an in-LP row the model prices 69–76 tail
hours (0.38–0.42×). The mechanism has no calibrated middle: it either does not bind
in the LP at all, or it binds across the whole year. The over-fire is not a scarcity
tail that overshoots — it is the entire year repriced (48.7 % of `ercot108`'s gap sits
in the `[30,80)` band alone).

**F2 — the ORDC total-reserve span is NOT the over-fire confound.** This was the
charter's core diagnostic claim, and it is refuted directly. Holding the in-LP
envelope fixed and turning the span **off** moves the result by $12.24/MWh — from
+699.7 % to +680.6 %, **2.7 % of a 700 % over-fire** — with the tail count *identical*
at 963/181. Right-sizing reserve demand from the ~10.7 GW span to the ~5.5 GW measured
AS plan changes essentially nothing: once reserve *supply* is capped at the envelope,
the measured plan alone is sufficient to bind the reserve rows at VOLL across ~11 % of
the year. The over-fire is owned by the envelope cap's own granularity, not by what it
is competing against.

**Corollary — the realized-room RTORPA is inert at the missed hours.** ERCOT-107's
adder is `mean $0.06/MWh, >$10 in 11 h, max $129` year-wide, and `$0.1` at the MISSED
tail hours. Meanwhile switching the span off *removes* the model's own working
scarcity-price-former: hours priced above tail fall 42 → 24 and the reserve dual binds
in 79 % of scarcity hours rather than 98 % (`ercot102_reserve_slack`). That is why
ERCOT-107 is not merely flat but a **regression** (−27.3 % → −35.9 %): the realized
adder restores far less than the span it replaces. The MISSED hours stay slack
(reserve dual $0.9) under every non-capped variant — the ERCOT-102 phantom-headroom
diagnosis is reconfirmed, and remains unaddressable by any reserve-side mechanism in
this family.

## 4. Disposition (charter decision fork)

The fork's UNDER-fire branch is met, now on complete rather than partially-inert
evidence: **the 2023 scarcity tail is structurally bounded within the
envelope/ORDC mechanism family.** Every reachable configuration is either ~$41–47
(under, tail slack) or ~$502–514 (over, whole year repriced). **STOP tuning *this
family*** — see §6 for the lane that remains open.

Per rule 1/11 no residual-motivated variant is attempted, and per rule 13 no measured
*outcome* is fed back. Closure is the honest governance route: the C6 attestation in
`docs/handoffs/ercot-101-governance-attestation-draft-2026-07.md` →
CALIBRATED-WITH-CAVEATS, **owner sign-off required**.

Note that the rule-26 concern flagged in the charter (turning `ercot_ordc_total_reserve`
off re-opens the ORDC-family design, so promotion needs owner sign-off) is **moot** —
neither ERCOT-107 nor ERCOT-108 is a promotion candidate.

## 5. Required correction to the attestation draft

The draft's `price_mean` / 2023 exception currently reads:

> "The only 2023 offer corpus on disk is the DAM disclosure … **no 2023 SCED/RT
> re-offer disclosure exists.** Unfixable with measured constructions."

That premise is **now false** — the 2023 RT SCED offer wall was recovered and is on
main (`ercot_sced_offer_wall_condbinned.json` carries 2022/2023/2024/2025). The
conclusion survives, but its reasoning must be restated on the stronger evidence: the
2023 RT wall **exists, is in the stack, and is fit-neutral** (keeper $46.76 → $46.50
with it; `ercot103` $41.46 → $41.21). The bound is **depth, not height** — the model
carries ~1.5 GW too much cheap supply at the spike hours, so the real high RT offers
never become marginal. This is a materially better-evidenced caveat than "the data
doesn't exist", and the exception text should say so before signature. Suggested
replacement text is in §5 of the log entry for this session.

---

**Files.** Bundles `results/calibration/ercot107_env_ordconly_rtwall`,
`results/calibration/ercot108_envlp_spanoff_rtwall`. No `src/` changes (flag-composition
replays only). Keeper untouched.

---

## 6. SCOPE CORRECTION — what is NOT closed (added 2026-07-24, same session)

The §4 disposition above is scoped to the **reserve-side (cap/ORDC) family**. It must
not be read as "the phantom depth is unaddressable" — that would be wrong, and the
ERCOT-89 charter had already predicted this session's result *and* named the
admissible alternative before it was run (§3(ii)):

> a **cap** that compresses the co-opt's shared headroom re-opens the rejected family
> and the rule-26-frozen ORDC design — the admissible shape is a **re-pricing of the
> offline increment** (capability stays available, at its true start-inclusive offer),
> which creates no phantom reserve shortage

So ERCOT-107/108 re-confirmed a dead end the charter had already marked, rather than
testing the live successor.

**The phantom's three documented causes (ERCOT-89 §2), and their status:**

| cause | status |
|---|---|
| Day grain (class-DAY mean flat over 24 h) | **FIXED** — ERCOT-96 `_hourly`, ON in keeper |
| Plant grain (which plant carries the derate) | **FIXED** — ERCOT-97 `_plant`, ON in keeper |
| **Only-OUT-is-out** (OFF/OFFQS/OFFNS priced as online at base offers) | **OPEN** |

**Measured this session — the size of the open cause at the tail hours.** Config-collapsed
60-Day DAM Gen_Resource disclosure (the derive's own `_site` collapse), 2023, at the
146 actual >$300 mean-zonal tail hours:

| class | ON | startable-but-OFF | OFF share of available |
|---|---|---|---|
| CC | 16.25 GW | **8.58 GW** | 34.6 % |
| CT | 1.23 GW | **8.36 GW** | 87.2 % |
| **CC+CT** | 17.48 GW | **16.94 GW** | — |

The availability overlay counts all 16.9 GW as available — **correctly**, it *is*
available (rule 13: startability is a physical fact, and the derive says so explicitly:
"an `OFF` (uncommitted but startable) resource contributes its reported HSL —
commitment state is not an availability event"). The defect is that the **LP then prices
it at base offers with no start cost and no min-run**. Per the attestation the model
clears within **~480 MW** of $200 at the Aug missed hours — i.e. it needs only a few
hundred MW of that 16.9 GW mispriced block to cap the price below scarcity.

This is a **pricing error on a correctly-measured quantity**, not an availability error
— which is exactly why a reserve-side *cap* is the wrong instrument for it (it removes
capability the market genuinely had, hence the bistability) and why re-pricing is the
right one (capability stays, cost becomes honest, no phantom reserve shortage, no
rule-26 ORDC re-opening).

**The untested experiment.** `ercot_faststart_pool_offer` (ERCOT-88, merged
**default-off**, REPLACE-BY-MASK, one owner per row-hour) already implements this shape
— but only for the **fast-start CT slice**, and ERCOT-88 found "the LP simply cleared
around it" because the cheap **CC** offline block (8.58 GW at tail hours) was never
repriced. The charter names the successor explicitly: *"a quantity-side successor that
widens the re-priced slice (larger measured offline share; CC at its own measured start
economics) would EXTEND this machinery, never stack a second markup on the same rows
(rule 19)."* That has never been run — and never with the recovered 2023 RT wall in the
stack, which changes what the LP clears *into* once the cheap offline increment stops
being the cheapest thing on the curve.

**Status: OWNER-GATED** (ERCOT-89 §7 step 2 — never authorized, never started). Not run
this session. Cadence if authorized: single-year rule-16 probe with the C3a level guard,
the zero-spurious gate, and the ercot41/43 failure-signature guard (2023 tail + C3b/C3c
must not degrade), then full-span + LOYO (rule 24) before any promotion.

---

## 7. ERCOT-109 — the mix at the true scarcity hours (added 2026-07-24, owner question)

Probe `scripts/probes/ercot109_scarcity_mix.py` (no LP; keeper hourlies + committed
zonal actuals + EIA-930 `ERCO hourly`). Visual companion:
`results/calibration/ercot109-scarcity-mix-julsep-2023.html`
(published artifact: <https://claude.ai/code/artifact/5b067fa6-eed9-4f4c-9712-fd2d4b931d3e>).

**122 true scarcity hours** in Jul–Sep 2023 (actual load-weighted zonal ≥ $300 — hours
selected from the ACTUALS only), 83 % of the year's 147. Actual $1,349 vs model $578;
the model reaches $300 in 31 and falls under $200 in 69.

The model serves the same load — total generation matches within **679 MW** (and load is
a measured input, so the level matches by construction). The composition does not:

| fuel | actual | model | Δ | hours model over by >250 MW | max |
|---|---|---|---|---|---|
| gas | 47,090 | 45,379 | **−1,711** | 0 (0 %) | — |
| coal | 11,271 | 11,695 | +424 | **71 (58 %)** | +1,943 |
| wind | 8,183 | 8,559 | +377 | **59 (48 %)** | +2,233 |
| hydro | 174 | 350 | +176 | 54 (44 %) | +470 |

The mean understates it: wind's median is only +139 MW but its p90 is +1,078 — the
over-run is skewed, not uniform. Taken together the **cheap stack**
(wind+coal+solar+hydro) runs a surplus in **118 of 122** hours (median +871 MW, max
+3,470; >1 GW in 48 hours), gas is under in **121 of 122**, and
**corr(cheap surplus, gas deficit) = −0.77** — near one-for-one merit-order
displacement. This is the "~1.5 GW too much cheap supply" of the ERCOT-101 diagnosis,
now measured hour-by-hour at the scarcity hours themselves.

**Storage is the one leg this cannot test.** EIA-930 publishes no battery series for
ERCOT 2023 and the committed artifacts carry model storage only as an annual total
(0.77 TWh throughput; Aug 116 GWh ≈ 156 MW monthly mean). That bounds the model's
battery contribution at these hours to a few hundred MW against a 1.7 GW gas gap but
does not resolve it — whether the model over-discharges batteries into scarcity hours
is **OPEN** and needs an hourly series on both sides.

### Correction to §6's proposed next step

§6 proposed "widen the re-priced slice to CC" via `ercot_faststart_pool_offer`. **That is
wrong on the mechanism** and is withdrawn:

1. **CC cannot ride this flag.** Eligibility is unit physics —
   `min_down_hours ≤ FASTSTART_POOL_MIN_DOWN_HOURS` (= 2.0) — so CC (4–8 h) fails by
   construction, as does ST_GAS (8–12 h). Widening to CC is a NEW leg, not this knob.
2. **The flag is inert for 2023.** `ercot_faststart_pool_condbinned.json` is YEAR-SCOPED
   with no pooled fallback (rule 13) and carries **2024/2025 only**; the 2023 SCED
   Gen_Resource corpus is **not on disk** (only 2024/2025 sample-day parquets are). The
   2023 RT *wall* entry was added by ERCOT-105 from a re-uploaded corpus that was not
   retained — note the wall's `_provenance.source` still reads "delivery years 2024-2025"
   and is stale relative to its own `ercot105_added` field.

So the available single-knob test is `ercot_faststart_pool_offer=true` on **2024/2025**,
where the artifact is live — worth running because ERCOT-88 judged that flag on the
**ercot86** keeper, before netrev-margin (ERCOT-100), state-off (ERCOT-99), the NP6 HSL
+ AS-clock fixes (ERCOT-98), the gas commitment bridge, and hourly/plant availability
grain (ERCOT-96/97) all landed. Testing it on 2023 first requires re-uploading the 2023
SCED corpus — an owner-authorized data intake, not a model change.
