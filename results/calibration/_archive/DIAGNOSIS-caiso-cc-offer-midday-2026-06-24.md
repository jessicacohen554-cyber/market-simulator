# CAISO in-state midday body via CC offer curves — PROBE rejected (2026-06-24)

Branch: `claude/caiso-phase2-cc-chp-cod-wq4k7n`. Task A: lower the CC_REGULAR +
CC_CHP econ band to bring the in-state midday body toward actual (2024 $35.85,
2025 $34.62) now that the structural rows (interchange + diurnal) are green —
the sanctioned "tune offer curves to calibrate the level" phase (rule #1).

Keeper reproduced exactly as the baseline (`caiso_phase2_baseline_3yr`): 2024
mean 46.38 / 2025 49.79, matching the dashboard keeper.

## Where the midday floor comes from (grounded on the solved keeper dispatch)

Midday (h10–14) generation share, 2024: **CC_REGULAR 19.6%** (the dominant
dispatchable gas) sets the ~$33.7 midday clearing; CC_CHP 3.3% and CT_CHP 2.7%
run flat baseload and are not marginal (see the CHP diagnosis). The corridor
deliverability cap correctly removed the phantom midday imports, so the model now
**backfills midday with in-state CC_REGULAR gas** (2024 model gas 76.88 vs
EIA-923 67.68 TWh, +9.2 = the removed-import backfill) at ~$33.7, where reality
is long (solar glut, midday $16.7, 755 neg hrs). **The model is short midday
where reality is long.**

The arithmetic rules out an offer-curve close: to clear midday at ~$20 the
marginal CC HR multiplier would have to fall from econ_high 1.27 to ~0.70 —
**below** the committed band (0.92), inverting the curve. No realistic CC offer
reaches the midday level (rule #1: don't reach the number via an unreal curve).

## Probe: CC_REGULAR + CC_CHP econ_low/econ_high −0.10 (`caiso_cc_econ_minus10_3yr`)

committed/peak left untouched (protect the well-matched evening and the overnight
band). `--offer-curve-delta-json '{"CC_REGULAR":{"econ_low":-0.10,"econ_high":
-0.10},"CC_CHP":{...}}'`.

| metric (2024 / 2025) | keeper | CC econ −0.10 | actual |
|---|---|---|---|
| mean LMP (P1 load-wt) | 46.38 / 49.79 | 45.39 / 48.57 | 35.85 / 34.62 |
| midday h9–15 | 33.5 / 42.7 | 32.8 / 41.6 | 16.7 / 17.1 |
| evening h18–21 | 60.5 / 55.5 | 59.7 / 54.5 | 58.0 / 49.3 |
| neg-price hours | 271 / 24 | **271 / 24** | 755 / 561 |
| **diurnal net-import corr** | **+0.08 / +0.03** | **−0.03 / −0.08** | (→ +) |
| net interchange (TWh) | −28.34 / −36.31 | **−24.70 / −32.84** | −32.38 / −36.16 |

## Verdict — REJECT (breaks the won structure; non-specific lever)

1. **Breaks the #1 guardrail.** The diurnal net-import correlation **flips
   negative both scored years** (+0.08→−0.03, +0.03→−0.08) and net interchange
   under-imports (2024 −24.70, below the −28 floor). Cheaper CC displaces imports
   in exactly the midday/shoulder hours the corridor cap fixed, re-distorting the
   diurnal shape the keeper won. The in-state CC offer and the WECC interchange
   structure are **coupled, not separable** — lowering CC re-breaks the diurnal row.
2. **It's a non-specific level lever, not a midday fix.** CC is marginal across
   most hours, so the cut lowers midday, evening AND overnight ~uniformly
   (−1 to −4), pulling the already-matched 2023 evening *under* actual (82.1→77.9
   vs 83.2). It improves mean MAE the wrong way (rule #1: a level cut that lowers
   a correct evening to shave MAE is not structurally faithful).
3. **It does not recover the negative tail.** Neg-hours unchanged (271→271,
   24→24): the cut shaves the midday floor ~$1 but never tips it into the
   oversupply/negative regime reality shows. The deficit is structural (the model
   lacks cheap midday supply after the phantom imports were correctly removed),
   not an offer-curve level.

The corridor keeper stays as-is. The midday body residual #2 is confirmed
**structural** (model short midday) under the new corridor structure — not
closeable by the CC offer curve without sacrificing the won diurnal/interchange
rows. The next grounded lever is a measured **midday cheap-supply / export**
mechanism (the corridor diagnosis's evening-import-shortfall + a long-midday
export path), not offer-curve tuning. Registered as a PROBE.
