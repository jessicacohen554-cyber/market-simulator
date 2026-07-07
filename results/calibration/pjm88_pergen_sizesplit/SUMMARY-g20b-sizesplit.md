# PJM 88 — size-split pergen pooling tier (pjm-87 diagnosis remedy)

**Probe (not a keeper decision). Keeper stays pjm-83-srmc-reground.** Full
span 2023–2025, one bundle, years sequential. The pjm-87 recipe verbatim +
`pjm_reserve_pergen_size_split=True` (new). Owner-directed follow-up after
the pjm-87 A/B: investigate why the per-gen opportunity-cost co-opt's
magnitude clustered in $0–10 instead of the targeted $10–80 band.

## Diagnosis that motivated this run (fleet-reconstruction probe, no re-solve)

None of the 4 measured balance rows (Primary/Synchronized × RTO/MAD) ever
came close to binding — supply margin stayed 8–14× even at the tightest
hour of all 3 years. The observed opportunity-cost duals came from the
per-**pool** joint headroom row instead (energy competing with reserve for
one pool's capacity), and with only 39 uniform (zone, fuel-class) pools the
LP could almost always source PJM's small measured requirement from some
idle pool — diluting the signal even when one specific dominant plant was
fully energy-loaded.

## The remedy

`pjm_reserve_pergen_size_split` splits each base pool's plants whose
capacity exceeds `PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE` (2.0×) times the
pool's own mean plant capacity into individual reserve columns; smaller
plants stay pooled together exactly as the base tier — self-normalizing
threshold (no absolute MW cutoff, rule 5). Measured on the real fleet: 95
pools / 190 sync-split R columns (vs the base 39 / 78) — 2023 landed at 91
pools / 182 columns (fleet composition varies slightly by year). A
deliberate middle ground short of the memory-infeasible full per-plant tier
(407 pools / 814 columns, ~10× the base tier).

## Memory — SAFE, no OOM

All three years solved cleanly. addRows peak transients: 2023 P0 ~13.7 GB,
P1 ~14.6 GB (settling to ~4.2/5.0 GB); 2024 P0 ~14.1 GB, P1 ~14.8 GB — all
comparable to (not worse than) the base 39-pool sync tier's peak, despite
~2.3× more reserve-block rows. The 6 GB swap buffer set up this session was
never meaningfully drawn on (0 → 66.8 MB used throughout).

## Result — MORE hours fire, but the magnitude did not sharpen

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| reserve dual > 0 (h), pjm-88 | **205** | **54** | **70** |
| reserve dual > 0 (h), pjm-87 | 133 | 44 | 50 |
| band $0–10 (h) | 203 | 48 | 60 |
| band $10–80 (h) | 2 | 6 | 10 |
| max dual ($) | 11.4 | 12.9 | 34.7 |
| mean dual when positive ($) | 1.0 | 4.4 | 7.4 |

More granular pooling exposes ~50% more hours where *some* pool is tight
(fewer generators averaging together means a single dominant plant's
tightness shows up more often), but the **depth** of the opportunity cost
per event is essentially unchanged — still ≥90% of positive hours land in
the $0–10 band in every year. Finer pooling addresses *frequency*, not
*magnitude*: the underlying limiter is not pooling dilution alone but the
offer-curve spread between the marginal reserve-eligible unit and its
next-cheapest alternative, which stays modest in most hours regardless of
granularity.

## C1–C8 verdict — criterion-identical to pjm-86/pjm-87

Full `calibration_verdict.py` scoring shows the same PASS/FAIL/CAVEAT/SKIPPED
status on every criterion as both `pjm-86` (flag-off baseline) and `pjm-87`
(base sync tier) — C3c (price tail) still FAILs in all three.

## A real, isolable dispatch shift in 2025 (not present in pjm-87)

Unlike pjm-87 (fuel-mix deltas ≤0.03 TWh/yr in every year, "no dispatch
distortion"), pjm-88's 2025 class volumes move materially vs pjm-87 itself
(isolating the size-split's own effect): CC_REGULAR **+1.44 TWh**, COAL_BIT
+0.28 TWh, ST_GAS +0.27 TWh, import +0.55 TWh, **CT_PEAKER −2.53 TWh**
(≈8% of its ~32 TWh class total). 2023/2024 stay near-zero (≤0.013 TWh),
matching pjm-87's pattern — the shift is 2025-specific (the tightest year:
mean Synchronized requirement margin bottoms at 3.83× even online-scoped,
the lowest of the three years per the diagnosis probe).

This shift does **not** register in the scored C1 fuel-mix criterion for
2025 specifically because that year's per-class checks show `SKIPPED` in
both pjm-87 and pjm-88 — a pre-existing EIA-923 2025 partial-current-year-
release completeness gate (unrelated to this session's changes; the raw
EIA-923 2025 column already carries `—` for several fuels in every PJM
bundle's generation-mix table). The shift is real regardless of whether the
scorer currently sees it.

## #1484 (CT_PEAKER C8 drag share) — re-verified, NOT a non-event this time

Per rule 19 reconciliation (`legitimacy_diagnostics.py` D-2, `ct_netload_drag`
mechanism, CT_PEAKER class):

| year | pjm-87 share | pjm-88 share | Δ |
|---|---|---|---|
| 2023 | 8.91% | 8.91% | 0.00 pp |
| 2024 | 13.58% | 13.59% | +0.01 pp |
| 2025 | 10.54% | **11.93%** | **+1.39 pp** |

2023/2024 are unchanged (matching pjm-87/pjm-83's already-registered
9.0/14.6%). **2025 moves up** — CT_PEAKER's class total shrinks from
31.80 → 29.23 TWh while the drag's forced numerator (frozen, rule 24) ticks
up slightly (3.353 → 3.486 TWh), so the ratio rises. **Still well under the
15% rubric-v2.1 peaker cap** (11.93% < 15%) — no gate crossed, no D-2 FAIL —
but this is a genuine, reportable movement, unlike pjm-87's "no material
movement" finding. The reserve co-opt is now measurably interacting with
the CT_PEAKER drag mechanism in the tightest year.

## Honest read

The size-split tier is memory-safe and does increase how often the
mechanism engages, but:

1. It does **not** meaningfully sharpen the opportunity-cost magnitude into
   the targeted $10–80 band — the distribution shape is essentially
   unchanged from the base tier.
2. It introduces a real (if gate-non-crossing) energy redispatch in 2025
   that the base tier did not have, and a real #1484 CT_PEAKER drag-share
   movement (+1.39pp, still under the 15% cap).

No breakpoint/penalty edit (rule 11); the size-split threshold is a
granularity/LP-structure choice (rule 5), not a fitted price parameter.
Not a promotion case — the frequency gain doesn't buy a magnitude gain, and
it costs a real (small) dispatch-distortion tradeoff pjm-87 didn't have.
Keeper stays `pjm-83`. Registered per rule 15; disposition (which of
pjm-87/pjm-88, if either, gets retained as the documented probe for the
next cycle) referred to the owner.
