# Calibration Log — ERCOT

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for ERCOT calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — ERCOT-89 (charter + measure-first, owner-authorized): the shoulder-hour online-capability lane CHARTERED and its step-1 measurement EXECUTED — H1 CONFIRMED (model carries 3.6–4.2 GW base-offer merchant headroom in the residual band hours where reality ran a 0.4–0.5 GW online margin, 8–10×), H2 CONFIRMED (CT commits FOR the band hours: ON share 0.71–0.76 vs 0.49–0.52 at bin-matched controls, every bin, both years; CC discriminates by loading depth), attribution = merchant under-dispatch backfilled by ST_GAS; step-2 build OWNER-GATED, keeper UNCHANGED (ercot86)

**Task.** The owner authorized the quantity-side successor charter to the closed
mid-band offer lanes (ERCOT-88 disposition), scope "measurement/charter only".
Charter: `docs/handoffs/ercot-shoulder-online-envelope-2026-07.md` — quantity-side
diagnosis (the DAM availability overlay is class-DAY, only-OUT-is-out, day-flat:
no hour-level commitment state), rule-19/26 reconciliation against the REJECTED
ercot41/43 envelope family (no-cap line: re-price the offline increment, never
compress the co-opt's shared headroom), pre-committed H1/H2 adjudication, and the
rule-13 bright line (conditional ON-share structure admissible; per-hour ON
pinning forbidden).

**Measurement (probe `scripts/probes/ercot89_shoulder_online_measure.py`, artifact
`data/raw/_validation-source/ercot89_shoulder_online_measurement.json`).** NP3-965
sample-day corpus (no new intake), merchant CC/CT statuses + capability per
covered hour, model side from two single-year throwaway replays of the ercot86
keeper (rule 16 — deleted after measurement; slim class/system hourlies harvested
into `results/calibration/ercot86_rtwall_fullspan/hourly/` so future diagnostics
stop re-solving the keeper). Coverage 35/68 (2024), 37/65 (2025) band hours.

**Findings (charter §8).** (1) H1: reality ran the residual band hours on ~325+100
MW (2024) / ~446+77 MW (2025) of merchant ON spare; the model carries 2.3+1.9 /
2.1+1.4 GW of base-offer headroom in the same hours — the quantity is the error,
not the price: at the ERCOT-86 wall's measured per-MW-rank ladders, 10× the spare
MW puts the model's marginal rank deep in the cheap rungs. (2) H2: the thin-margin
state survives net-load conditioning (CT ON share separated in every bin, both
years; CC spare collapses 867→325 / 1,079→446 MW control→resid) — a conditional
forward driver exists. (3) Attribution: total gas matches actuals in both hour
sets; the model substitutes ST_GAS (4.1→6.1 GW control→resid, vs inferred ~1–2 GW
real non-CHP steam) for the merchant CT surge (measured BP 4.3→6.8 GW via starts)
and CC ON-ceiling loading it under-dispatches by ~4.5–5.5 GW. ST_GAS is
rule-19-owned by its own drag lane — reconcile, never stack, in any step-2 D-2
enumeration. Secondary: model carries ~4.6 GW less VRE than reality in the 2024
resid hours (evening solar shape) and still clears $30–80 — a fortiori.

**Disposition.** Measurement supports a build; step 2 (one design round among
charter §6 shapes (a)/(b)/(c) against the §8.5 attribution, default-off gate,
single-year 2024 probe with C3a level guard + zero-spurious + no-scarcity-tail-
degradation guard, then 2025, then full-span LOYO) is OWNER-GATED, not started.
Keeper stays ercot86; nothing registered (the replays reproduce the keeper).
Ops: charter + probe + artifact + sidecars + this entry committed and pushed on
`claude/ercot-88-midband-offer-closed-b997ar`. Next number: ercot-90.

## 2026-07-19 — ERCOT-89 (step-2 build, owner-authorized design round): the conditional online-span mechanism BUILT (wall-ladder geometry re-anchor + generalized pool boundary, `ercot_shoulder_online_span`, default-off) and REJECTED AS ARMED — both single-year probes trip the pre-committed C3a level guard (−1.3→+3.0% / +1.4→+4.8%) and zero-spurious gate (+2/+5) via ~230 same-cell sub-$150 hours lifted $10–20; the rule-13-admissible conditional carries only ~½ (2024) / ~⅓ (2025) of the measured ON-share separation; mechanism stays MERGED default-OFF, keeper UNCHANGED (ercot86)

**Task.** The owner authorized ONE step-2 design round for the shoulder-hour
online-capability lane (charter §7.1 cadence). Built: charter §6 shape (a) as a
GEOMETRY correction of the two existing seams (rule 19 — no third channel):
`ercot_shoulder_online_span` re-anchors the ERCOT-86 RT wall ladder's rel
denominator on the measured CONDITIONAL online span (`rel = (share − boundary) /
(span(cell) − boundary)`, ladder-top clamp above the span — the SCED spare ladder
is measured on the ONLINE fleet, and stretching it over capability telemetered
OFF at the same conditions is the §8.1 8–10× wedge), and generalizes the ERCOT-88
fast-start pool boundary from `1 − pool_frac(bin)` to the span so the FULL
offline CT increment is PRICED at the measured start-inclusive ladder — never an
LP cap (§3(ii): the ercot41/43 envelope family stays closed; no floor, no
reserve-headroom compression, D-2/D-4 vacuous). Driver:
`derive_ercot_shoulder_online_span.py` → year-scoped 2024/2025 conditional
ON-share table (net-load bin × season × 4h block, hierarchical ≥6-hour cells,
zero fitted scalars, rule-23 frozen; the per-hour ON series never ships).
Hard-error composition (wall + RT + pool required); 11 trivial-case tests +
artifact invariants; year-absent and span=1.0 paths byte-identical (tested).

**Pre-build adjudication (charter §9.1–§9.3, written before the seam).**
(1) Driver is PARTIAL: leave-one-out cell means recover +0.14/+0.27 (2024) and
+0.05–0.07/+0.18 (2025) of the residual-vs-control CT ON-share separation — the
remainder is day-of commitment information with no forward analogue, deliberately
not encoded (rule 13 bright line). (2) A pre-LP static supply-stack screen
predicted standalone near-band-inertness: the residual hours' marginal supply is
~2.3 GW of CC mid-rungs + ST_GAS headroom — the §8.3 ST_GAS displacement wedge
(rule-19-owned by the drag lane, RECONCILED not fixed; coupling now quantified).
(3) D-2 enumeration re-derived: span modifies the wall's geometry and the pool's
boundary parameter — same owners, no stacking; bridge/availability/reserve seams
untouched.

**Probes (rule-16 single-year throwaways; base = the committed ercot86 keeper
hourly sidecars; analyzer `scripts/probes/_ercot89_span_check.py`).** Mechanism
ENGAGED (466/473 walled rows re-anchored, 486/497 pool rows vs ERCOT-88's
173/91):

| year | C3a resid (base→probe) | band formed | spurious Δ | h>$200 (act) | gates |
|---|---|---|---|---|---|
| 2024 | −1.3% → **+3.0%** | 5/68 → 7/68 | **+2** | 13→21 (53) | C3a DEGRADED; spurious TRIPPED; tail HELD |
| 2025 | +1.4% → **+4.8%** | 4/65 → 10/65 | **+5** | 1→10 (31) | C3a DEGRADED; spurious TRIPPED; tail HELD |

**Finding — the admissible conditional is too coarse to price the band.** The
failure is death-by-small-lifts: ~230/228 hours with actual < $150 rise $9–19
each, because cell-mean compression cannot distinguish a residual hour from a
control hour in the SAME (bin × season × block) cell — it lifts both. The new
spurious hours are 1–2 h bleeds around real price events (May-2024 $912 core;
an Oct-2025 cluster). Band fill is modest (+2/+6). The sub-scarcity tail moves
TOWARD actual in both years (2024: +$141 mean at actual>$500, h>$200 13→21 vs
53) — real, but the C3c successor lane's regime, and no offset for tripped
level/spurious guards in both current-design years (pre-committed rejection
rule; rules 1/11 — the frozen span table is NOT re-swept against the residual).

**Disposition (charter §9.5).** REJECTED as armed; mechanism stays MERGED
**default-OFF** (ercot41/43 rejected-probe pattern — machinery + artifact +
tests + record kept, byte-identical off). Keeper stays **ercot86**; NO
registration (single-year throwaways, deleted after analysis; a full-span solve
of a guard-tripped mechanism would register nothing but harm). Frontier
recorded in charter §9.5: (i) sharper conditioning within rule 13 needs a
broader SCED corpus (data-intake question); (ii) revisit shape (a) only after
the ST_GAS drag lane closes the shoulder-hour displacement (the binding
blocker, now quantified); (iii) the span's tail behaviour is a measured,
dormant lead for the C3c scarcity-formation lane.

**Ops.** Mechanism + derive + artifact + tests + analyzer + charter §9 record
committed and pushed on `claude/ercot-89-shoulder-online-mechanism-jdyxl7`
(rebased onto main post-#2627). Probe bundles deleted (rule 16). Next number:
ercot-90.

## 2026-07-20 — ERCOT-90 (measure-first, step 1): the §8.3 CAMPD ST_GAS hourly check EXECUTED — the ~3× displacement inference is REFUTED in magnitude (measured real steam-gas in the residual band hours is 4.2–4.8 GW, not ~1–2; model over-dispatch is ×1.27–1.37, +1.3–1.7 GW), the over-dispatch is ECONOMIC not floor-forced (above even an upper-bound drag-floor reconstruction in 97–100 % of residual hours), owning seam = the ST_GAS commitment-state/offer surface (`ercot_offer_surface_cleared_share_steam`, default-off), with a separable winter drag season-shape finding; step 2 OWNER-GATED, keeper UNCHANGED (ercot86)

**Task.** ERCOT-89 §9.5(2) named the ST_GAS shoulder-hour displacement as the
binding blocker on the mid-band and §8.3 named this measurement as its follow-up.
Executed measure-first (no apply, no mechanism, no solve): probe
`scripts/probes/ercot90_stgas_shoulder_measure.py` → artifact
`data/raw/_validation-source/ercot90_stgas_shoulder_measurement.json`; charter
`docs/handoffs/ercot-stgas-shoulder-2026-07.md`. Measured side: CAMPD/CEMS
unit-level TX hourly gross for the model's own 17-plant ST_GAS fleet (split
facilities unit-routed per `data.outages`; CT/CC unit types dropped; ×0.95 net).
Model side: the committed ercot86 keeper hourly sidecars ONLY (no replay).
Hour sets: ERCOT-89 conventions at full-8760 coverage (residual 63/61,
controls 6,471/6,506, 2024/2025) + the ERCOT-89 covered subsets re-scored.

**Findings (charter §3).** (1) The e89-subset model medians reproduce §8.3's
6.1 GW exactly, but measured reality ran 4.5/4.8 GW in those hours — the ~1–2 GW
inference (930-residual arithmetic, §8.4(a) merchant-scope offset) is refuted;
reality surges steam into the band hours just as the model does (2.1→4.2 GW
control→resid measured vs 2.4→5.4 model). The wedge is +1.3–1.7 GW, ~⅓ the
assumed size. (2) Residual-hour over-dispatch is economic: model MW exceeds even
the UPPER-bound floor (`frac(NL_hat)×8,923 MW`, keeper-armed params) in 100 %/97 %
of residual hours by ~2.9 GW median — model runs 61–64 % CF at $48–62 model
prices where reality, facing actual $150–500, had ~47 % of the same base online;
measured output IS the online capability, so the excess is the ERCOT-89 §2
no-commitment-state wedge expressed on ST_GAS. NOT a drag-level miss in the band
hours. (3) Separable winter finding: DJF sub-$150 controls model 1.6–1.9 GW vs
measured 0.6–1.1 GW, only 40–55 % of hours above floor_ub — the season-blind
drag curve over-carries winter at this grain (overnight curve still tracks its
source, ρ 0.69/0.75); any fix is a season-resolved re-derive of the same CAMPD
source, never a residual re-tune (rule 22). (4) Availability notes: model max
10.4/8.7 GW vs measured max concurrent 8.7/7.4; CFB (56708) never runs; annual
model +25 %/+24 % vs the same-plant CAMPD net basis. (5) Coupling re-quantified:
an ST_GAS fix frees ≤1.3–1.7 GW of the §9.2 ~2.3–2.4 GW+ re-clearing wedge —
necessary-but-not-sufficient; the span re-probe stays the combined test.

**Disposition.** Verdict routes a step-2 build (OWNER-GATED, not started) to the
existing owners only: arm/extend `ercot_offer_surface_cleared_share_steam` (the
band-hour seam) and/or season-resolve the drag derive (the winter seam) — no new
channel, no LP cap (rule 19; ercot41/43 no-cap line). Pre-committed guards in
charter §6: C3a level + zero-spurious + no scarcity-tail/C3b/C3c degradation,
2024 rule-16 throwaway → 2025 → full-span LOYO, keeper stays ercot86. ERCOT-89
§8.3 carries a superseded-note pointing here. Ops: probe + artifact + charter +
this entry committed on `claude/ercot-90-stgas-shoulder-edgsep`. Next number:
ercot-91.
