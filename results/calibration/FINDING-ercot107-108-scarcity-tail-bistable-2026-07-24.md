# FINDING — ERCOT-107/108: the 2023 scarcity tail is structurally bounded; the on-line-capacity envelope is BISTABLE and the ORDC span is NOT the over-fire confound

**Date:** 2026-07-24 · **Lane:** ERCOT scarcity tail (ERCOT-101 successor)
**Keeper:** `2026-07-23-ercot100-netrev-margin-keeper` — **UNCHANGED** (no promotion, no
config change).
**Runs registered:** `2026-07-24-ercot107-envelope-pricing-basis`,
`2026-07-24-ercot108-envelope-in-lp` (both PROBE, both NOT-YET).
**Disposition:** the ERCOT-107 charter's hypothesis is **REFUTED**. The decision fork
lands on **STOP tuning → close via the C6 governance attestation** (owner lane).

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
(under, tail slack) or ~$502–514 (over, whole year repriced). **STOP tuning.**

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
