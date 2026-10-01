# ADDENDUM to PRECOMMIT SPP-51 — the as-coded WINDOW may make the arm nearly inert where it matters

**Written and pushed BEFORE any shard returned a number.** Shards were launched at base
`f80de3e1` and were still provisioning when this was measured; no arm bundle existed on any disk
reachable from this session. This **sharpens** the §5 prediction against this lane's own
hypothesis and makes it easier to falsify, which is the only reason to write it now rather than
after.

## The measurement

`fleet/arrays.py:2884-2903` floors each coal plant in the **top-k hours ranked by system LOAD**,
`k = round(online_frac × 8760)`, with an all-hours override only at `online_frac ≥ 0.99`
(`_COAL_SYNC_FORCE_ALL`). **No SPP coal plant reaches that threshold** — the maximum is 0.987.

Aggregating SPP's 24 `status=ok` COAL rows over each year's own committed load shape:

| quantity | value |
|---|---|
| total online-Pmin band, all 24 plants | **4.090 GW** |
| aggregate floor in the **lowest-load decile** (mean) | **0.840 GW** |
| aggregate floor in the **single lowest-load hour** | **0.000 GW** |
| that low-decile floor ÷ the model's own coal annual max | **4.2 – 5.0 %** |

Identical in all seven years, because it is a property of the ranking and the artifact, not of
the year.

## Why this matters, stated as a correction to §5's own reading

The zero-coal collapse lives in the **bottom 6–14 % of load** (PRECOMMIT §7: median load rank
0.055–0.139). The as-coded window floors a plant in its top-`online_frac` load hours, so with
`online_frac` 0.435–0.987 the bottom decile retains only the handful of plants above ~0.90 —
and the extreme low-load hours retain **none**. **The floor is placed almost everywhere except
where the defect is.** The real SPP PRB fleet never falls below **8.1–17.5 %** of its own annual
max; this window supplies **4.2–5.0 %** in the low decile and **0 %** at the bottom.

## Revised predictions — these SUPERSEDE §5 where they differ

| # | §5 said | REVISED | why |
|---|---|---|---|
| P-1 | coal +0.85 TWh/yr | **unchanged**, but the energy arrives in **mid-load** hours, not the oversupply hours | the deficit `Σ max(0, F−coal)` is concentrated where the window is live |
| P-2 | wind −0.6 to −0.9 TWh/yr | **unchanged in magnitude, weakened in kind** — displacing mid-load thermal, not spilling wind at the margin | wind is not at the margin in mid-load hours |
| P-4 | negative hours UP | **NOW DOUBTFUL, possibly ~0 change** | the floor does not bind in the hours where wind could become marginal |
| P-4b | — | **NEW: the 149–293 zero-coal hours will LARGELY REMAIN** | no floor is active there |
| P-5 / P-6 | C3a down, C3b down | **weakened toward "small"** | both were predicated on the floor reaching the low-price hours |
| P-7 | min price stays −26.000 | **unchanged** | structural |

**The falsification is now sharp in both directions.** If the arm moves negative-price hours
materially, the window is doing more than this measurement says and P-4 stands. If negative
hours and the zero-coal count barely move while coal rises ~0.85 TWh, then **the mechanism is
right and its window is wrong**, and the object is R-bd (net-load ranking), not this arm.

## What this does NOT change

* **The arm is still worth solving, and is still the correct first test.** It is the zero-code,
  zero-new-parameter, measured form of the mechanism, and rule 1 `[R-STRUCT]` charters it on the
  fleet fact (12 of 24 SPP coal plants carry no min-load band at all), not on the residual.
  Solving it is what distinguishes "the window is wrong" from "the mechanism is wrong" — and
  those two have completely different successors.
* **Nothing is re-cut.** `online_frac`, `mustrun_online_pct` and `_COAL_SYNC_FORCE_ALL` are
  untouched. Changing the ranking to net load is a shared-path code change that PJM and MISO
  runs would inherit (rule 25 `[R-ISO-SCOPE]`), and it gets its own PRECOMMIT or none.
* **No gate is re-read.** §5's C8 risk stands exactly as written; if anything this measurement
  makes a C8 failure *less* likely, since a floor that binds in fewer hours forces less energy.
