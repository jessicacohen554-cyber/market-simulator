# PJM CT overnight-reliability evidence check — the drag window is correct (2026-07-06, L-13 step 3)

**Owner question.** The `ct_netload_drag` (PJM CT_PEAKER's single commitment
mechanism) binds only in hours **[15,22)** on a net-load hinge (zero-crossing
~90 GW). Hypothesis: real PJM CTs also run **overnight** at times for
reliability, so the class's true deployment is broader than the evening window
and the [15,22) gate is missing real structure. **Resolve empirically, not by
intuition** — and if overnight running is real, capture it by *widening the
measured mechanism*, never by relaxing the D-2 forced-energy cap (rules 1/19;
the long-run home for reliability commitment is per-gen reserve/ORDC
co-optimization, G-20 Phase 2, memory-gated — not built here).

**Method.** Measured CAMPD pure-play PJM CT_PEAKER fleet CF (the exact model
CT_PEAKER plant codes, the same series the drag is regressed from), pooled
2023–2025 (26,280 h), cross-tabulated by hour-of-day × net-load decile,
season × hour-block, and overnight-vs-ramp at matched net-load
(`scripts/diag_pjm_ct_overnight_evidence.py`, rule-15 throwaway, no LP).

## Verdict: the [15,22) window is CORRECT. Do NOT widen it.

Overnight CF is **not zero** but it is (a) a flat ~2 % economic baseline that is
**net-load-insensitive** across the normal overnight range, i.e. merit-order
territory the LP already prices — not a reliability floor; plus (b) a genuine
but **small** condition-responsive uptick confined to the extreme top of the
overnight net-load distribution (>110 GW, ~24 h/yr) that is **3–5× weaker than
the ramp-window relationship at the same net-load**. Extending the ramp hinge
overnight would **over-floor** those hours 2–3× — the exact rule-1/rule-13
violation the framing warns against. The extreme-net-load overnight uptick is
the domain of per-gen reserve/ORDC (G-20 Phase 2), not a widened min-gen floor.

### (a) hour-of-day × net-load decile — overnight is flat and net-load-insensitive

Overnight hours 0–3 sit at ~0.013–0.017 CF across **every** net-load decile up
through D7 (<99 GW); they lift only in the top two deciles (D8 <109, D9 <150),
and D9 overnight is a handful of extreme hours. The ramp block (15–21) by
contrast climbs 0.043→0.40 across the same deciles. Hours 4–5 are the morning
ramp-up (transition), not overnight reliability.

### (b) season × hour-block — overnight running is NOT cold-snap-driven

| block | winter | shoulder | summer |
|---|---|---|---|
| overnight 0–5 | 0.028 | 0.030 | 0.016 |
| morning 6–9 | 0.090 | 0.091 | 0.064 |
| midday 10–14 | 0.054 | 0.099 | **0.238** |
| ramp 15–21 | 0.078 | 0.145 | **0.273** |
| late 22–23 | 0.037 | 0.035 | 0.049 |

Overnight CF is ~2–3 % in **every** season — winter ≈ shoulder > summer, all
tiny. This **refutes** the "cold-snap overnight reliability" hypothesis as a
material effect. The large seasonal signal is the **summer afternoon–evening
ramp** (cooling load) — exactly what [15,22) already captures.

### (c) overnight vs ramp at matched net-load — the ramp hinge would over-floor overnight

| net-load (GW) | n_overnight | CF_overnight | n_ramp | CF_ramp | ramp-hinge pred |
|---|---|---|---|---|---|
| 60–70 | 1541 | 0.021 | 196 | 0.049 | 0.000 |
| 70–80 | 2324 | 0.024 | 1163 | 0.086 | 0.000 |
| 80–90 | 1554 | 0.020 | 2210 | 0.110 | 0.000 |
| 90–100 | 801 | 0.025 | 1529 | 0.113 | 0.055 |
| 100–110 | 270 | 0.056 | 1036 | 0.174 | 0.165 |
| 110–120 | 63 | **0.174** | 748 | 0.247 | 0.276 |
| 120–130 | 9 | 0.306 | 449 | 0.364 | 0.387 |

Across the whole range where the hinge is active (90–120 GW), overnight CF runs
**3–5× below** the ramp-window CF at the same net-load, and **2–3× below** the
ramp-hinge prediction (e.g. 100–110 GW: measured overnight 0.056 vs hinge
0.165). The net-load→CF relationship is genuinely *different* overnight — the
reserve/ramp-deployment duty the drag stands in for is an afternoon-evening ramp
phenomenon; overnight the system carries more committed-baseload headroom. Only
at the extreme (110–130 GW overnight, ~24 h/yr) does overnight CF approach ramp
CF, and those hours are precisely the scarcity/reserve-shortage regime.

## Disposition (rules 1/13/17/19)

1. **Keep the [15,22) window and the frozen hinge unchanged.** Rule 17's premise
   ("a floor binding where its driver says the class is offline is a bug") holds:
   overnight the class is at its economic ~2 % baseline, net-load-insensitive.
   Widening the ramp hinge overnight would force 2–3× the measured overnight CF —
   a fabricated floor, not real structure (rules 1/13).
2. **The small real overnight uptick (>110 GW, ~24 h/yr) is reserve/ORDC
   deployment, owned by G-20 Phase 2** (per-gen reserve/ORDC co-optimization,
   `docs/multi-iso/pjm-reserve-ordc.md`; memory-gated, ramp rates absent from
   FleetArrays). It is *not* captured — and must not be — by widening the drag
   or relaxing the D-2 cap. Noted as the correct long-run home; **not built
   here.**
3. **The CT under-dispatch the drag was hypothesized to fix is NOT a window
   problem.** The 2024 CT_PEAKER shortfall vs actuals is denominator-driven (C8
   memo §3) and is attacked instead by the G-21 ST_GAS de-flood (step 2) — which
   frees merit-order energy to CC_REGULAR, not CT_PEAKER, leaving the residual
   CT deployment gap to G-20 Phase 2.

Mirrors the neiso-48/caiso-52 CT tmax scrubs and the burndown's rule-19
one-mechanism principle: measured evidence, not fit, sets the window.
