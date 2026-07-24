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

## 2026-07-20 — ERCOT-91 (step 2, authorized design round): band-hour steam-wall arm REJECTED (zero-spurious/C3a trips both years, alone and composed — the trip is intrinsic to the DAM-basis ST ladder in cold-snap hours, not the drag); winter seam PASSES — `gas_st_drag_seasonal`, the rule-22 season-grain re-derive of the drag curve from its own CAMPD source (DJF zero-crossing ~31 GW vs pooled 15.2), all guards held both years, full-span candidate `ercot91_seasonal_drag_fullspan`; keeper UNCHANGED (ercot86)

**Task.** The ERCOT-90 §4 verdict's two seams, one design round (charter §6
guards pre-committed): (a) arm the ERCOT-77 steam extension of the cleared-share
wall (`ercot_offer_surface_cleared_share_steam`); (b) season-resolve the
`gas_st_netload_drag` curve from the same CAMPD source. D-2 enumeration
re-derived first: `st_netload_drag` is the class's only floor (26.7-32.0 %
forced share); the wall is bid-axis-only inside the existing cleared-share
owner; peak rungs/conditional, bridge (CC-only), pool/span (off) all disjoint —
no stacking. Probes: `replay_keeper` single-delta throwaways off the ercot86
keeper, 2024 → 2025 → composition, scored with `_ercot89_span_check` + the
ercot90 measurement re-run + winter C1/C4 rows.

**Band-hour seam (a) — REJECTED as armed (charter §8.1).** Engages as designed
(516 walled rows; ST boundary/wall + measured ST state weight, DAM basis) and
moves the LEVEL toward measured everywhere (2024 residual 5,445→5,315 MW vs
measured 4,247, controls +540→+158, annual +25 %→+15 %; 2025 residual
5,672→5,012, annual +24 %→+10 %; freed energy → CC/CT, reality's surge
pattern) — but trips the pre-committed gates in BOTH years: 2024 spurious 7→15
(all 8 new hours ONE Jan-14 cold-snap cluster, actual $85-107 → probe $153),
2025 C3a +1.4 %→+3.5 % DEGRADED + spurious 2→3; band fill unchanged (5/68,
4/65). Composition with the winter seam refutes the coupling hypothesis — the
same 8 Jan hours trip with the seasonal drag armed (C3a +2.8 %): the trip is
intrinsic to pricing the un-cleared steam increment on the DAM-basis ST ladder
in tight-winter hours (the ERCOT-84/86 measured-cheap/mis-based DAM-ladder
lesson, now on ST). ercot41/43 pattern: machinery stays merged default-off,
byte-identical; frontier = an RT/SCED-basis ST ladder + finer state
conditioning (data-intake, a new charter). The ERCOT-89 §9.5(2) span revisit
stays parked (no ST_GAS band-hour fix armed).

**Winter seam (b) — PASSES (charter §8.2).** New standing derive
`scripts/data/derive_ercot_stgas_drag_seasonal.py` (same CAMPD source,
drag-covered plants unit-routed, EIA-930 ERCO net-load, overnight 23-05h,
NYISO/PJM-family hinge estimator) → frozen artifact
`ercot_stgas_drag_seasonal.json`: DJF 0.01354/−0.4257/0.270 (crossing 31.4 GW),
MAM 0.00731/−0.1073/0.241, JJA 0.01149/−0.2800/0.359, SON 0.00601/−0.0810/0.276;
pooled re-fit check ≈ armed scalars. LOYO 2-year re-fits: MAM/JJA/SON stable,
DJF knee 24-38 GW (winter-event variance) but always ≫ the pooled 15.2 GW.
Mechanism: `gas_st_drag_seasonal` (default off, tier 3, ISO-guarded rule 25)
swaps the pooled scalars for per-season coefficients inside
`apply_gas_st_netload_drag_floor` — same mech id/rows/window, flag-off
byte-identical (test-enforced). Probes: ALL gates held both years (2024 C3a
−1.3 %→−0.6 % improved; 2025 +1.4 %→+2.0 % inside threshold); DJF over-carry
+1.77→+0.52 TWh (2024) and +1.39→+0.23 (2025); annual +25 %→+12 % / +24 %→+10 %
over the CAMPD basis; winter C4 flat-to-improved; residual band hours barely
move (economic, as pre-registered). Disclosed cost: MAM/SON shift slightly
further under measured (floor released MW the econ layer doesn't re-add — the
ST_GAS econ-offer axis, not the floor; rule 14 keeps the finer-grain curve).

**Disposition.** Keeper stays **ercot86** (owner-only swap). Band-hour probe
bundles deleted (rule 16). Winter full-span 2023-2025 candidate solved and
registered as `2026-07-20-ercot91-seasonal-drag-fullspan` (NOT-YET —
governance attestation absent by design for a candidate; C-rows in the
sidecar definition). Full-span gates vs TRUE bases, all three years, ALL
HELD: 2023 resid −24.0 % → −23.7 % (the keeper's committed bundle lacks its
2023 hourly sidecars — vs rule 15 — so the base was re-established by a
byte-recipe keeper replay; the definition text's "−11.6" is the same number
in $ on the simple-mean basis; the seasonal floor cannot bind in 2023's
scarcity hours — dispatch 7.5-8.5 GW ≫ floor ~3 GW — so August is untouched
by construction); 2024 C3a −1.3 % → −0.6 %, 2025 +1.4 % → +2.0 %,
spurious/tail/NRMSE flat, band fill unchanged. Bonus, scorer-verified: D-2
ST_GAS forced share 29.0/26.7/32.0 % → **20.8/18.8/22.8 %** — the keeper's
only D-2 failure (2025 over-cap, rubric-v2.2 grounded) passes under the
30 % budget outright in the candidate; D-1 shape passes all years
(profile_r 0.969-0.998). The candidate bundle commits its hourly sidecars
for ALL THREE years (closing the sidecar gap class the ercot86 2023 miss
exemplifies). Pre-existing main breakage noted for the owner (not this lane):
`tests/test_net_cone_forward.py` fails collection on main (FF-G3 merge imports
`NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` missing from `constants.py`).
Ops: derive + artifact + mechanism + tests + charter §8 + this entry on
`claude/ercot-91-stgas-shoulder-seams-tgrv1j`. Next number: ercot-92.

**Promotion amendment (same session, owner directive "Promote").**
`2026-07-20-ercot91-seasonal-drag-fullspan` is the ERCOT KEEPER, superseding
`2026-07-19-ercot86-rt-wall-fullspan`. Executed: `calibration_attestation.json`
written (ercot86's governance + exceptions carried forward with updated
magnitudes — 2023 C3a −32.5 % vs −32.8 %, C3b 0.631 vs 0.632, tail byte-flat;
DOF ledger +1 measured-physical entry for the seasonal curve, superseding the
pooled scalars); keeper shard swapped (`keeper_store.py --set ERCOT`);
`market_story` added to the sidecar; verdict re-scored (NOT-YET on the same
basis as ercot86 — `price_tail` undocumented beyond 2023, the standing C3
successor lane); `build_status.py --iso ERCOT` rebuilt;
`calibration-keeper-auditor --iso ERCOT` PASS (one prose repair: sidecar
definition candidate→keeper). Branch rebased onto main post-#2651.

## 2026-07-20 — ERCOT-92 (measure-first, corpus adjudication): the RT/SCED steam-basis frontier RESOLVED FROM COMMITTED DATA — the ERCOT-89 §8.3 "corpus lacks ST restypes" note is OVERTURNED (all four NP3-965 sample-day parquets carry GSNONR/GSREH/GSSUP: 44 resources, 100 %-populated SCED2 curves, telemetered statuses), the RT/SCED-basis ST ladder (ERCOT-86 construction, steam leg) DERIVED and FROZEN (`ercot_sced_offer_wall_steam_condbinned.json`, 2024/2025, fleet-scoped, zero fitted scalars); step-2 arming OWNER-GATED, keeper UNCHANGED (ercot91)

**Task.** The ERCOT-91 §8.1 rejection named the band-hour frontier as two
data-intake questions: an RT/SCED-basis ST ladder and finer state conditioning.
Scope: measure-first corpus adjudication (no apply, no mechanism, no solve),
deliverable = a derivability verdict, plus the frozen artifact if committed data
suffices. Record: `docs/handoffs/ercot-stgas-shoulder-2026-07.md` §9.

**Adjudication (§9.1).** (a) The on-disk NP3-965 SCED corpus CARRIES steam —
the §8.3 parenthetical described the derived CC/CT artifact's `CLASS_OF_RESTYPE`
scope, not the raw data: 44 gas-steam resources per file, SCED1/SCED2 curves
100 %-populated on ON-family rows (median 8 steps), BP/HASL present, positive
online spare on ~half the ON rows; §8.3 corrected in place (rule 14). (b) The
60-Day DAM disclosure's steam rows (45 resources, full-year) carry only the
QSE-submitted DAM offer curve + awards + ex-ante status — no SCED curves, no
BP/HASL, no telemetry: NOT SCED-usable; it is exactly the measured-cheap DAM
basis the ERCOT-91 trip refuted. (c) Steam ON/OFF resolves at hour grain from
the same corpus's per-interval `Telemetered Resource Status` (sample days only:
25+22 d 2024, 11+24 d 2025) — the state-conditioning half is also
committed-data-derivable if a step-2 round wants it. **Verdict: derivable from
committed data, 2024/2025; no intake, no data authorization needed; 2023 stays
DAM-basis unreachable (no sample days + regime bar).**

**Artifact (§9.2–§9.3).** New standing derive
`scripts/data/derive_ercot_sced_offer_wall_steam.py` →
`data/raw/_validation-source/ercot_sced_offer_wall_steam_condbinned.json`
(+ 9 tests). ERCOT-86 construction byte-shared (helpers imported from the
frozen CC/CT derive — which stays byte-identical and ST-free, test-enforced;
rule 19: the steam ladder is the steam-owner seam's own basis). Fleet-scoped to
the model's own 17 plants via an exact 36-resource name map validated
per-plant against nameplate (CFB absent from the corpus, consistent with its
zero CEMS operation; 8 excluded ≤49 MW industrial/CHP resources ≈ 0.2 % of
ON-spare, disclosed; unmapped corpus name = hard error). Year-scoped
2024/2025, no pooled fallback, deterministic, frozen rule 23. All 7 net-load
bins populated both years (168-505 intervals/bin). Headline: from bin 1 up the
RT steam surface's upper rungs stand far above the DAM ST ladder (2024 b3-b5
q90 153-184 vs DAM 81-91; 2025 b5 q90 438 vs 84 — regression-tested on the
mid-band bins), and the keeper's whole steam offer stack (econ mult 10.8,
committed 14.8 = 0.97/1.32 × 11.18 fleet HR) prices at the measured RT
surface's ~q10-q30 in every mid/high bin — the ERCOT-91 §8.1 trip's root
cause, now carrying its measured replacement. Disclosed, not encoded: b0 and
2024-b6 exceptions (scarcity-bin ON steam runs near-fully loaded; thin cheap
residual spare vs DAM cap-level rungs).

**Disposition.** STOP per charter — step-2 arming (ladder-source swap in the
steam wall leg; state-weight basis question; Jan-14-2024 cold-snap regression
first) is a separate owner-gated round with the ERCOT-91 §6 guards inherited,
bases from the ercot91 keeper's committed hourly sidecars (all years, no
replays). Keeper UNCHANGED (`2026-07-20-ercot91-seasonal-drag-fullspan`);
nothing registered (no solve). Out of scope, unchanged: LP caps (ercot41/43),
frozen-artifact re-tunes (rule 23), the C3c tail lane, the ERCOT-89 span
re-probe (§9.5(2) condition still unmet). Ops: derive + artifact + tests +
handoff §9 + envelope §8.3 correction + this entry on
`claude/stgas-band-hour-frontier-1kn1fl`. Next number: ercot-93.

## 2026-07-21 — ERCOT-93 (step-2 arming + full-year corpus intake): ST_GAS steam RT/SCED-basis wall + telemetered online span BUILT and PROBED — REJECTED (zero-spurious cold-snap trip, intrinsic to the RT wall's net-load-bin-only price ladder); full-year NP3-965 corpus re-freezes both offer walls (2023 now populated); machinery default-off, keeper UNCHANGED (ercot91)

**Deliverable 1 — full-year corpus re-derive.** Both offer walls re-derived on the
full-year 60-Day SCED Disclosure publication-month corpus
(`data/raw/ercot/YYYY-MM.part*.parquet`), replacing the tail-biased sample-day
extracts. **2023 is populated for the first time** (the big scarcity year); the
thin b0/2024-b6 bins gain real coverage; mid-band p50s drop (the sample days were
tail-biased) — a rule-23 data-basis correction, byte-identical on re-run. The
CC/CT RT wall is keeper-consumed (`cleared_share_rt`), so the refresh moves the
keeper's 2024 C3a base (~−2.3 → ~−5.0 %): the accurate walls reveal the model is
*more* under-priced than the biased sample showed (rule 11 — the open C3 tail is
the real issue, not the walls).

**Deliverable 2 — ST_GAS steam RT wall + telemetered online span.** Built in the
`ercot_offer_surface_cleared_share_steam` owner (default-off): the steam RT/SCED
ladder in its own artifact (`ercot_sced_offer_wall_steam_condbinned.json`, rule
19) + the hour-level online-span conditional
(`ercot_shoulder_online_span_steam_condbinned.json`,
`scripts/data/derive_ercot_shoulder_online_span_steam.py`; 2023 ON-share b0→b6
0.14→0.99). Measurement: the shoulder over-carry is ~97–98 % ECONOMIC (offer
surface owns it, not the drag).

**Probe verdict: REJECTED.** Holds C3a and improves mid-band fill but TRIPS the
pre-committed zero-spurious §6 gate (+11) on the Jan-14/15 winter cold-snap
cluster (reality $85–107 → model $185–216). RT-only isolation trips +10 (all
cold-snap) → the trip is intrinsic to the RT steam WALL, not the span. Full-span:
C3a 2023 −18.4 % / 2024 +2.5 % / 2025 +10.8 %; spurious 28/18/19. Root: the wall's
price ladder is net-load-percentile-bin-conditioned ONLY, so the not-RT-scarce
winter high-net-load cold snap draws the summer-scarcity-dominated expensive
high-bin ladder. Machinery MERGED default-OFF (`git apply`
`docs/handoffs/ercot93-core-mechanism.patch`; 11 steam-RT tests pass), keeper
UNCHANGED (`2026-07-20-ercot91-seasonal-drag-fullspan`). Next number: ercot-94.

## 2026-07-21 — ERCOT-94 (season-offer-wall charter → measure + diagnose): the season-conditioned offer wall is REJECTED as the 2023-summer-LMP lever — it is a WINTER fix (fixes the ERCOT-93 cold-snap trip) but orthogonal to the blocker, which is an ORDC/reserve scarcity-pricing COLLAPSE (C3c tail); keeper UNCHANGED, no solve, no registration

**Charter (owner reframe).** The lane goal was sharpened to "fix 2023 summer LMP".
The ercot91 keeper is NOT-YET, blocked by **C3c price-tail FAIL** (2023 model 40 h
vs RT 181 h >$200, 0.22×; 2024 13 h vs 53 h); C3a-2023 = −32.5 % (load-weighted) is
a ledgered caveat sharing the same root per its own attestation
("SCARCITY-TAIL COLLAPSE ON THE CORRECTED AVAILABILITY ENVELOPE").

**Measure (full-year corpus, `scripts/probes/_ercot94_season_offer_gap.py`).** The
DJF-vs-JJA offer-level split is real but is a **winter-cheaper** signal: summer
high bins barely move (ST b4 pooled 29.5 → JJA 32.5, ~+10 %; b5 ~+2 %; CC/CT
JJA≈pooled), and **b6 — the scarcity-tail bin — has ZERO DJF coverage in 2023**
(already pure-summer, nothing to un-blend).

**Diagnose (ercot91 2023 sidecar, rule 15, no re-solve).** The model's ORDC adder
fires only **3 hours all of 2023** (annual-mean $0.27/MWh); the 40 model >$200
hours are the **energy dual hitting HCAP** in genuine shortage, not the overlay.
Price mass: [50,100)=236 h, near-miss **[100,200)=9 h**, [200,1000)=11 h,
[1000+)=29 h. The ~141 missing tail hours are model-priced ~$50–100 vs actual
>$200 — a scarcity-PRICING gap the offer wall's 2–10 % mid-band bump cannot bridge
(offers top ~$150 outside shortage). **The season wall is orthogonal; do not
promote it.** Real lane = ORDC/reserve scarcity recalibration on the corrected
envelope without phantom fleet tightness (rules 1/11) — `src/market_sim/results/
scarcity.py`; full diagnosis + ERCOT-95 handoff in
`docs/handoffs/ercot94-scarcity-tail-diagnosis-2026-07.md`.

**Ops.** Full-year offer-wall artifacts re-derived on the clean corpus (all three
present; the ercot91 keeper should be re-solved on them in the ERCOT-95 lane).
Corpus defect surfaced + quarantined: `data/raw/ercot/2026-02.part0001-0009.parquet`
(Dec 3–9 2025 delivery, "Add files via upload") lack the HASL column and crash the
2025 derive — owner to re-intake or remove. Keeper UNCHANGED. Next number: ercot-95.

**Follow-up (same session) — keeper re-solved on the refreshed walls + registered
(owner directive).** The ercot91 keeper config was re-solved on the full-year
refreshed offer walls (single 3-year `replay_keeper` invocation) and registered as
`2026-07-22-ercot91-refreshed-walls` — a NOT-YET, governance-unattested **non-keeper
documentation run** (keeper pointer UNCHANGED). Finding: the full-year 2023 CC/CT RT
wall (ABSENT on the old sample-day basis) lifts 2023 P1 mean $36.9 → $40.0 and tail
hours >$200 **40 → 69** (toward the 181 actual) via energy-side pricing, while the
ORDC adder still fires only 3 h — so the refreshed 2023 wall closes ~1/3 of the tail
gap and the ORDC/reserve scarcity collapse (ERCOT-95) remains the dominant remaining
lever. 2024 ~flat ($26.7 → $26.0, tail 13 → 12), 2025 flat. Transport note: the run's
sidecar + 1.3 MB payload + binary bench/bundle are committed locally (dc60fa9a) but the
LIVE-dashboard push is blocked from this container (the documented 413 + push_files
response-budget wall — the rule27 base64-staging path needs a working-`git push`
environment to assemble); this log entry is the durable record until then. Also flagged
for the owner: pre-existing registry/payload parity failures on `2026-07-13-nyiso-64`
and `2026-07-21-nyiso-69-dr-reserve` (sidecars with no `runs/<id>.js` payload → invisible
in the Run Explorer; the latter is the NYISO keeper).

## 2026-07-22 — ERCOT-96 (Lane A of the ERCOT-95 hand-off, measured-grain build round): the class-day-FLAT DAM availability overlay is refined to class-HOUR grain — the measured afternoon phantom (+216 MW mean on the 181 actual 2023 tail hours) removed at its own grain; every 2023 gate moves the right way (C3c 40→51 h, C3a −32.5%→−27.8%, NRMSE 0.631→0.539, summer hod-corr 0.885→0.908, C7/C8 PASS), LOYO clean; full-span candidate `2026-07-22-ercot96-dam-hourly-grain` registered NOT-YET (2024/2025 tail rows unledgered); keeper UNCHANGED (ercot91) pending owner adjudication

**Charter.** Close the 2023-summer C3c miss on its MEASURED owner (ERCOT-95 Finding 6): the
`ercot_thermal_dam_availability` overlay collapses the per-resource×per-hour 60-Day DAM
disclosure to `(date, class)` and applies a flat 24-h block, discarding the hourly
ambient-derate shape and the per-plant concentration. NOT the reserve-side ORDC lane
(ERCOT-95 refuted it three ways).

**A-1 MEASURE (solve-free, `scripts/probes/_ercot96_phantom_measure.py`).** On the 181
actual 2023 RT tail hours (56 days; 169/181 in hod 13-19; PRC median 5,648 / min 2,697 MW):
hod-shape phantom (day-mean − hour, CC+CT, under the derive's own rating-clip semantics —
the model-relevant measure; Finding 6's +668/+1,147 were unclipped raw) = **+216 MW mean,
+433 p90, +578 max**; per-plant misallocation a class-grain overlay cannot place = 259 MW
mean — but it is net-zero REDISTRIBUTION (merit-mix/zonal placement, not tightness), spread
wide (top-10 sites = 25% of the 6.7 GW mean tail-hour derate). ST_GAS tail-hour phantom ≈ 0.

**A-2 BUILD (zero fitted parameters).** `ercot_thermal_dam_availability_hourly`
(ScenarioConfig, default off; ERCOT+backcast, refines the armed day mechanism — rule 19 one
mechanism, finer grain): derive extended to emit `--hourly-out`
`data/raw/ercot-thermal-dam-availability-hourly.csv` (per-HE class fraction from the SAME
site-hour intermediate; day CSV byte-identical under the refactor; per-HE present-site
denominator so DST/partial coverage cannot bias; uncovered HE → NaN → statistical stack,
hour by hour), loader `outages.ercot_thermal_dam_availability_hourly_series`, and the fleet
water-fill applied per HOUR (restore a′=a+λ(1−a), remove a′=a·(t/cur) — cap-weighted
class-hour mean lands exactly on the measured fraction). Rules 13/23: same measured source,
finer grain/schema; nothing touched a residual. Plant×hour deferred: no DAM-site→EIA-plant
crosswalk exists (~290 mnemonic sites — DDPEC/CBECII/WHCCS2…), the measured per-plant
residual is redistribution-only, and an unreviewed auto-map risks silently corrupting a
plant's availability (CAISO reviewed-crosswalk pattern is the follow-up, ERCOT-97).

**A-3 A/B (2023 rule-16 throwaways, never registered).** Base = byte-recipe ercot91 replay
on the 4ff3118 tip tree — reproduces the keeper's committed 2023 EXACTLY (tail 40 h, mean
$36.94), so tree drift since b8cada7 is solve-neutral and the A/B reads against the keeper
itself. Probe (+hourly grain): C3c tail 40→51 h (in-actual 38→46; 5 spurious, ALL Jun-18/19
near-misses on the known June over-formation days, 3 of 5 within 1-2 h of an actual tail
hour), C3a mean-px gap −26.0%→−22.1%, Aug afternoon mean 271→327, summer hod-profile corr
0.885→0.908, trough (hod 0-8) untouched — the overnight restore is non-binding, exactly the
C7 risk that did not materialize. CC_REGULAR −22 GWh (the phantom), ST_GAS +24 GWh backfill.

**Full span + LOYO.** `2026-07-22-ercot96-dam-hourly-grain` (2023 byte-reused from the
probe, recorded in meta.reuse; 2024/2025 fresh): 2024 tail 13→13, C3a −7.3%→−6.6%; 2025
tail 1→0 — the removed hour was SPURIOUS (correctly absent now), C3a −4.5%→−4.8%
(negligible). Zero fitted parameters → LOYO reduces to no-held-out-degradation: clean.
Verdict on the registered artifacts: C1 16/16, C2/C4/C5a/C6 PASS, **C7 PASS, C8 PASS**,
C3a/C3b ledgered CAVEATs (magnitudes improved), C3c 2023 CAVEAT (0.28×) + 2024/2025 FAIL
(unledgered) → **NOT-YET**, driver unchanged in kind, reduced in size.

**Where this leaves C3c.** The measured phantom was 0.2-0.6 GW against afternoon slack
measured in GW; the grain fix recovered what the measurement said it owed (+11 h, +8
in-actual). The remaining ~130-h miss is the chartered supply-mix/conduct frontier:
plant-grain crosswalk (concentration + zonal placement), measured RUC held-out capacity
(SCED telemetered `ONRUC` status — corpus already in-repo), West/Panhandle split (own
charter), and Lane B (published seasonal ORDC LOLP table into the co-opt curve —
correctness item, ~28 h on the measured envelope; deliberately NOT probed this session,
moved to ERCOT-97 by owner direction). If ERCOT-97 exhausts these without band entry, the
disposition designed by ERCOT-95 stands: LEDGER C3c 2024/2025 (3/3 MAX_LEDGERED_CAVEATS →
CALIBRATED-WITH-CAVEATS via `calibration_verdict.determine`) — owner sign-off, never
unilateral.

**Transport (rule 27).** git push 413s in this environment; the 7-file core change shipped
as ONE atomic verified patch (`docs/handoffs/ercot96-lane-a-core.patch`, blob 8c9331f3 —
the per-blob verification caught and fixed two real transcription defects this session) +
manifest (`docs/handoffs/ercot96-thermal-dam-grain-2026-07.md`). The 1.48 MB runs payload +
bundle hourly parquets + the 594 KB hourly CSV cannot transit a model response; delivered
to the owner as a placement tar.gz (sha256-manifested) via the session file channel.
Keeper UNCHANGED (ercot91); promotion + C3c ledgering are the owner's calls.

**Addendum (2026-07-22, same session) — OWNER-PROMOTED to keeper.** Owner directive
"Promote this to keeper": `2026-07-22-ercot96-dam-hourly-grain` is the ERCOT keeper,
superseding `2026-07-20-ercot91-seasonal-drag-fullspan`. Attestation updated
(OWNER-PROMOTED), `keepers/ERCOT.json` re-pointed, `status/ERCOT.js` rebuilt
[ERCOT:NOT-YET], `audit_keepers.py --iso ERCOT` PASS (0 failures). C3c ledgering
was NOT taken with this promotion — determination stays NOT-YET on the unledgered
2024/2025 tail rows; that remains a separate owner action (with the ERCOT-97 lanes
as the alternative close-out). ERCOT-97 baselines on THIS keeper.

## 2026-07-22 — ERCOT-97 (three lanes on the 2023-summer C3c frontier, on the ercot96 keeper): plant-grain DAM availability BUILT + directional-A/B'd (structural win — summer hod-corr 0.40→0.60, spurious tail 32→24 — at a merit-mix C3a-level cost; NOT a clean C3c closer); measured RUC conduct SIZED and found IMMATERIAL (~281 gas unit-hours vs the bridge's ~51k, 178x → no mechanism, rule 19/14); published ORDC-LOLP swap REJECTED (adds real+spurious tail, zero-spurious fails). Keeper UNCHANGED — owner adjudication.

**Charter.** Baselined on `2026-07-22-ercot96-dam-hourly-grain` (owner-promoted keeper),
three lanes to move the NOT-YET C3c: (A) DAM-site→EIA-plant crosswalk + plant×hour
availability, (B) measured RUC-conduct commitment state, (C) the ERCOT-95 Finding-4 ORDC
LOLP swap. Base assembled from `docs/handoffs/ercot96-lane-a-core.patch` (7 files, all 7
post-apply blob SHAs verified against the manifest) + the committed hourly CSV (blob
7d93a2eb, verified); `solve_and_persist` carries `ercot_thermal_dam_availability_hourly`
→ True.

**Lane A (PRIMARY) — plant grain BUILT, directional A/B.**
- A-1 crosswalk (`scripts/data/build_ercot_dam_resource_crosswalk.py` →
  `data/raw/reference/ercot-dam-plant-crosswalk.csv`): 262 DAM sites (58 CC 30.5 GW / 165
  CT 11.3 GW / 39 ST 10.4 GW) proposed against `custom-bin-assignments.csv` with per-row
  evidence (p98 rating, settlement points, QSE, capacity ratio, distinctive-abbreviation
  corroboration). ERCOT substation mnemonics do NOT token-match EIA names and 2-char
  initialisms collide (WHCCS2→Wharton is a FALSE match, correctly rejected; it is Wolf
  Hollow II) — so a strict, collision-aware accept gate: strong+distinctive corroboration
  AND unique-in-class AND capacity-plausible, plus the 3 forensic seeds. 22 auto-accepted
  (12 CC / 6 CT / 4 ST), every one hand-verified correct (zero false positives); the rest
  accepted=0 → class-hour envelope fallback (CLAUDE.md rules 1/11 — accepted-gated
  identification metadata, not a tuning channel). CC is the coverage priority.
- A-2 mechanism (`ercot_thermal_dam_availability_plant`, default off, requires `_hourly`):
  the derive emits a site×hour parquet (the live_sh/rating intermediate it already
  computes; reconciles to the class-hour grain exactly); the fleet hook pins each accepted
  plant to its OWN measured site-hour fraction and water-fills the unmapped remainder so
  the class-HOUR total is UNCHANGED — a within-class REDISTRIBUTION, zero fitted
  parameters (unit-tested: class total preserved exactly, plants pinned, missing-file
  no-op).
- A-3 A/B (2023 rule-16 throwaway, keeper-config base vs +plant probe, both re-solved this
  session; base gas bridge floored 51,607 unit-hours — matches the keeper's ~50k, base is
  faithful): plant grain moves spurious tail 32→24 (−8), real-tail capture 45→47 (+2),
  summer hod-profile corr vs actual 0.40→0.60 (+0.19) — the afternoon price SHAPE improves
  markedly. Dispatch shifts to CC_REGULAR (+1278 GWh) from ST_GAS/CT/coal (the predicted
  merit-mix redistribution). BUT mean price 37.66→33.58 drops further below actual (49.93)
  — a C3a-LEVEL cost from the cheaper-CC merit shift. Verdict: a genuine STRUCTURAL
  refinement but NOT a clean C3c closer (C3a level worsens); the gate "C3a not worse" is
  not met on the price level. Needs the full rubric + LOYO + owner judgment — not
  promoted. (2023 site-hour parquet is Dec-short pending the 2024_Jan-Mar spillover file;
  ~17.5k CC plant-hours fell back to class grain, so the effect is a floor.)

**Lane B (SECOND) — measured RUC conduct IMMATERIAL, no mechanism.**
`scripts/probes/_ercot97_ruc_measure.py` over the slim SCED tail/control-day subsets that
survived the purge (2024/2025; 2023 SCED absent — re-fetch to extend): ONRUC (RUC-committed)
≈ 303 unit-hours total (281 gas: ST_GAS ~236 / CC ~28 / CT ~17), evening-ramp weighted
(hod 18-20 peak, 49% in hod 13-19), dominated by the old gas-steam fleet (Olinger, Lake
Hubbard, Mountain Creek, Spencer, V H Braunig — the units the ST_GAS drag already governs).
vs the keeper gas bridge's ~51k unit-hours ⇒ 178x smaller ⇒ NOT material. Lane B step 2
(thread a measured RUC commitment-state input) NOT triggered: a RUC floor would replace a
tiny slice of the bridge, not change the committed state (rule 19 one-mechanism, rule 14
measured-over-derived both better served by leaving the bridge + ST_GAS drag in place).

**Lane C (LAST) — published ORDC-LOLP swap REJECTED.**
Keeper 2023 replay with `--set ordc_lolp_params_path=.../ercot_ordc_lolp_params.csv`
(summer mu 0→904, sigma 1400→1333): tail 77→112 (real captured 45→62, +17) BUT spurious
32→50 (+18); mean price 37.66→39.70 (toward actual). The published LOLP envelope raises
scarcity pricing but adds MORE spurious tail than real — the zero-spurious gate FAILS.
Not adoptable standalone (charter: "adopt ONLY if C7 + zero-spurious hold"; predicted "NOT
a C3c closer" — confirmed).

**Disposition.** All three lanes landed/exhausted; C3c still out of band. Plant grain is a
real structural asset (better summer hod shape, fewer spurious tails) banked as a
default-off, LOYO-pending mechanism; RUC is immaterial; the LOLP swap is refuted
standalone. Keeper UNCHANGED. The ERCOT-95/96 close-out still stands as the owner's option:
LEDGER C3c 2024/2025 (3/3 MAX_LEDGERED_CAVEATS → CALIBRATED-WITH-CAVEATS) — owner sign-off,
never unilateral. Code + crosswalk + probe on branch `claude/ercot-97-c3c-frontier-rtd17r`;
no dashboard registration (2023-only throwaways, rule 16).

**Transport (rule 26/27).** git push from the blob-filtered partial clone triggers a
multi-GB promisor backfill that disconnects (each attempt leaves a multi-GB tmp pack);
worked around by pushing with partial-clone disabled + pre-fetching the boundary blobs
individually. Full detail + repro in `docs/handoffs/ercot97-results-2026-07.md`.

## 2026-07-22 — ERCOT-97 KEEPER TRACK (owner directive "structurally more accurate = new keeper"): plant-grain DAM availability SOLVED + SCORED full-span 2023-2025. Structurally faithful (C7/C8/D-9/D-10 PASS, zero fitted params); marginal ledgerable price cost (C3a −27.8→−27.9%, C3b 0.539→0.545). Recommend promotion — OWNER SIGN-OFF PENDING.

**Reframe (owner, rule 1).** The three-lane entry above banked plant grain as "default-off,
LOYO-pending" because it worsened the C3a level. Owner correction: a mechanism that is
STRUCTURALLY more faithful (measured plant-hour availability vs a class envelope) is the
keeper *even if the fit worsens* — the C3a cost is a rule-11 root-cause signal, not grounds
to reject the structure. So Lane A was run full-span as a keeper candidate.

**Reproducibility (the "ercot96 not on disk" issue, RESOLVED).** ercot96's class-hour base
(`ercot-thermal-dam-availability-hourly.csv`) reproduces BYTE-IDENTICALLY from source
(md5 7ea628f1…) once the 2026_Jan-Mar 60-day-disclosure spillover file is materialized (it
carries the 2025 Nov-Dec delivery days; the derive already scans year+1 and filters on
Delivery Date). 2023 (335d, Dec genuinely absent) and 2024 (366d) reproduce as-is. So the
class-hour base is UNCHANGED and the plant grain is a PURE delta on ercot96 (not a new base).

**Run.** `2026-07-22-ercot97-plant-grain-fullspan` (registered): ercot96 keeper recipe +
`ercot_thermal_dam_availability_plant`, via `replay_keeper --set …plant=true --years 2023
2024 2025`, one bundle (rule 16). Site-hourly parquet re-derived full-span (2023:335d /
2024:366d / 2025:365d), committed. Base A/B twin = ercot96 recipe replayed same-box (plant
OFF), which reproduces the ercot96 committed C3a −27.8% / C3b 0.539 EXACTLY (validates the
same-box comparison); the twin is A/B-only, not registered on the dashboard.

**A/B (candidate plant-ON vs base plant-OFF, same box, all 3 years in one bundle each):**
- C1 fuel-mix / C2 volume / C4 dispatch-corr / C5a CO₂: **PASS** (both).
- C3a mean LMP 2023: base −27.8% → candidate **−27.9%** (marginal, ledgered CAVEAT).
- C3b price shape 2023: base NRMSE 0.539 → candidate **0.545** (marginal, ledgered CAVEAT).
- C3c tail: SKIPPED both (no committed RT actual_tail for ERCOT-year; not a differentiator).
- **C7 diurnal shape (D-1): PASS all classes** (CC_REGULAR profile_r 0.99, CT_PEAKER 0.974,
  ST_GAS 0.998; gated classes clear). The finer grain keeps the afternoon supply shape
  faithful — the structural payoff (cf. the 2023 A/B: summer hod-corr 0.40→0.60, spurious
  tail 32→24).
- **C8 forced-share (D-2): PASS** — CT_PEAKER 13.6% < 15%, ST_GAS 20.2% < 30%, CC_REGULAR
  bridge 0.7% + reliability 0.4%; CHP classes exempt. Forced energy budgeted.
- D-9 overlay quarantine PASS; D-10 renewable-provenance PASS.

**DOF / LOYO (rule 15/22).** Plant grain adds ZERO free parameters — it is a within-class
REDISTRIBUTION of the (unchanged) class-hour availability total onto measured per-plant
site-hour fractions, water-filling the unmapped remainder (22 crosswalked plants, all
hand-verified; 12 CC / 3 CT / 3 ST in 2023). No tuned value can move, so the LOYO test is
trivially clean (same argument the ercot96 hourly-grain carried).

**Determination.** Same gate PROFILE as the ercot96 keeper — C1/C2/C4/C5a PASS, C3a/C3b
ledgered CAVEATs, C3c NOT-YET — plus a strictly MORE faithful measured grain (C7 PASS at
plant resolution, zero params). By rule 1 and the owner's directive this is the more
structurally-faithful keeper. **Verdict: CALIBRATED-WITH-CAVEATS candidate, recommend
promotion to ERCOT keeper, superseding `2026-07-22-ercot96-dam-hourly-grain`.** Promotion is
OWNER-ONLY and still requires the C6 governance attestation + keeper-shard flip +
`audit_keepers.py --iso ERCOT` + the calibration-keeper-auditor — NOT taken unilaterally.

**Committed.** Slim bundle (meta/run_config/metrics/legitimacy_diagnostics + hourly
sidecars) + registry sidecar + runs payload + full-span parquet, all on branch
`claude/ercot-97-c3c-frontier-rtd17r` (rebased onto main after PR #2791 merged the ERCOT-97
code). Engineering detail: `docs/handoffs/ercot97-results-2026-07.md`.

**PROMOTED 2026-07-22 (owner directive "promote it as the keeper but I'm not willing to
call it calibrated yet").** ERCOT keeper flipped to `2026-07-22-ercot97-plant-grain-fullspan`
(`keepers/ERCOT.json`), `status/ERCOT.js` rebuilt **[ERCOT:NOT-YET]**, DOF ledger seeded into
the bundle attestation (`build_dof_ledger.py`), `audit_keepers.py --iso ERCOT` **PASS** (0
failures). The keeper designates the most structurally-faithful run; the DETERMINATION
REMAINS **NOT-YET** — C6 governance intentionally left UNATTESTED and C3a/C3b intentionally
NOT ledgered, so the verdict stays NOT-YET (not calibrated). Supersedes
`2026-07-22-ercot96-dam-hourly-grain`.

## 2026-07-23 — ERCOT-98 (owner charter: RE / AS-ECRS / zonal-deliverability attribution of the 2023 summer tail, on the owner-uploaded NP6 GEO data): all three suspects REFUTED against measured data — the 135 missed tail hours are OFFER-driven SCED λ (RTORPA p50 $1, PRC p50 5.8 GW); two measured-input alignment fixes landed (2023 HSL UMass→NP6; AS-plan CPT→CST clock) and the keeper config re-solved full-span on the honest inputs → `2026-07-23-ercot98-np6-hsl-fullspan` registered NOT-YET (C3a 2023 −27.9→−33.5 %, C3c 51→42 h — the stale inputs were compensating); keeper UNCHANGED (ercot97) — owner adjudication

**Charter.** Owner handoff (supersedes prior): with 2023 ERCOT NP6 HSL landed in-repo
(`np6/2023/`, NP4-742 wind / NP4-745 solar GEO variants), test the three named suspects for
the 2023 summer scarcity miss — system-wide RE over-credit, AS/ECRS holdout, West/Panhandle
deliverability — measured-comparison first, then re-solve the keeper on the accurate input.
Full forensics: `docs/DIAGNOSIS-ercot-2023-summer-tail-attribution-2026-07.md`; probe
`scripts/probes/ercot98_tail_attribution_measure.py` (no-LP, committed inputs only).

**Attribution (keeper ercot97 baseline, 2023).** Actual RT tail 181 h; model 51 (46 caught /
135 missed / 5 phantom). At the missed hours, measured reality: RTORPA p50 **$1.0** (max
$262), PRC p50 **5,765 MW**, SCED λ > 0.8×RT in **92 %** — no reserve scarcity; the market
cleared $500–5,000 on the August heat-wave offer wall (Aug 71 of the 135; Aug 4–13 alone
carry 42, incl. the 8/10 peak-load day at 8/8 missed). Model physical balance at the same
hours is faithful (gas −305 MW, coal +432, nuclear −13, RE **−1,683** model-UNDER, demand
−704 vs EIA-930/native). The three suspects:
* **RE over-credit — REFUTED.** NP6 GEO delivered matches EIA-930 (−0.3 % wind / +0.03 %
  solar); the model runs RE *under* actual at the missed hours, and the accurate input
  RAISES model RE there (+1.7 GW mean at the missed hours; +1.13 TWh annual dispatch).
  Solar's +13.7 % vs EIA-923 is 930-vs-923 scope, not an over-count.
* **AS/ECRS under-hold — REFUTED as tail owner** (requirement level measured-faithful,
  ercot57 §2b re-confirmed incl. the 9/6 duplicate-posting artifact); found + FIXED the
  loader placing CPT stamps unconverted on the CST clock — 1 h late through every DST
  season, ±600 MW at individual evening hours, −174 MW mean summer-evening all-product
  holdout, 5,639 hours touched (`scarcity.ercot_as_plan_requirement_mw`).
* **W/P deliverability — REFUTED at the event evenings** by two independent measurements:
  actual RT zonal spreads ≈ 0 (8/30 HE20 uniform $4,843 at every LZ+hub; LZ_WEST ≥
  LZ_HOUSTON on 8/17 and 9/6), and the NEW zonal HSL sidecar shows W+P wind curtailment
  ≈ 0 MW at the event peaks (8/17: exactly 0 all evening; 9/6 ≤ 488 MW). Jul–Sep evening
  W+P share of ERCOT wind is 57.9 % — the zonal series stays load-bearing for the West
  topology / WP-B curtailment lanes, just not for this tail.

**Fixes landed (rule 11 — measured-input alignment, no knobs).**
1. 2023 HSL rebuilt from the published NP6 GEO reports (delivered ≡ EIA-930 → the loader's
   footprint reconciliation is now a no-op for every year; UMass fallback retained).
2. NEW zonal HSL sidecars `ercot_<year>_hsl_zonal_hourly.parquet` (2023 full-year both GEO
   vocabularies, sum-of-regions = 1.0000; 2024/25 wind LZ) — `--zonal-only` builder mode.
3. `scarcity.ercot_as_plan_requirement_mw` CPT→CST conversion (DSTFlag-disambiguated;
   winter byte-identical, levels unchanged; feeds all four multiproduct AS families).
4. `actual_tail.json` deriver-path note fix + ERCOT status shard S1 refresh (keeper C3c
   rows now score vs the committed tail: 51/181, 13/53, 0/31 — out of band low all years).

**Run.** `2026-07-23-ercot98-np6-hsl-fullspan` — full-span 2023–2025 re-solve of the
byte-faithful ercot97 keeper config (replay_keeper, no config deltas) on the corrected
inputs. **NOT-YET** (C6 governance unattested — keeper-parity). Scores vs keeper: C3a 2023
**−27.9 → −33.5 %**, C3b NRMSE **0.545 → 0.647**, C3c **51 → 42 h** (2024: 13 → 12; 2025:
0 → 0, clock-only deltas); C1 16/16, C2, C4, C5a, C7, C8 all PASS (structure holds). The
worse 2023 price fit is the rule-11 EXPECTED outcome and quantifies the compensation the
stale inputs were providing (~5.6 pp of C3a, ~9 tail hours of artificial tightness): the
residual now belongs entirely to its real owner. Input-alignment fixes, not structural
mechanism changes → no LOYO (rule 22 scopes LOYO to mechanism changes; precedent: ercot56
nuclear windows, ercot57 DAM availability). 2024/25 inputs differ only by the AS-plan
clock, so the year deltas isolate: 2023 = NP6+clock, 2024/25 = clock only.

**Successor lane (pre-registered).** The tail residual's owner is offer formation at high
net load (ercot57 §4's named channel): the conditional offer surface's repriced peak band
is never marginal at the missed hours because the model's cheap mid-stack is deeper than
reality's cleared stack. Candidates (measured, rule-13): widen the measured cleared-share
repricing below the peak rungs in the top net-load bins; the G-22 DA-boundary family.
Forbidden (pre-registered): room-pin to RTOLCAP (ERCOT-79), any residual-tuned
adder/offset. Honest bound: an hourly perfect-foresight LP smooths the intra-hour 5-min
SCED dynamics contributing to some of these hourly means.

**Disposition.** Keeper UNCHANGED (`2026-07-22-ercot97-plant-grain-fullspan`, NOT-YET).
ercot98 is the same structure on strictly more accurate inputs — by rules 1/11 the
more-faithful run — registered as the honest-inputs successor candidate; promotion is the
owner's call. (Housekeeping note, other lane: parity check flags a pre-existing CAISO
orphan sidecar `2026-07-22-caiso-112-export-floor` with no payload — invisible in the Run
Explorer; needs its session's bundle to regenerate.)

## 2026-07-23 — ERCOT-98 KEEPER TRACK (owner sign-off "if so promote", same session): ERCOT keeper → `2026-07-23-ercot98-np6-hsl-fullspan`

Promotion executed on the ERCOT-98 recommendation: same structure as ercot97
(byte-faithful config replay, zero knob deltas) on strictly more accurate measured
inputs (2023 NP6 GEO HSL; AS plan on the correct CST clock), and ercot97 is no longer
reproducible from the committed tree — the keeper now designates the run main can
regenerate. Determination remains **NOT-YET** (C6 governance unattested, keeper-parity);
honest-inputs price cost carried in the frontier note (C3a 2023 −27.9 → −33.5 %, C3b
0.545 → 0.647, C3c 51 → 42 h vs RT 181 — the stale-input compensation, rule 11). Keeper
sidecar carries a market_story (ercot97's had none); status shard rebuilt;
`audit_keepers --iso ERCOT` + calibration-keeper-auditor both PASS with zero repairs.
ercot97 stays registered as the prior-keeper comparison. The offer-formation successor
lane (ERCOT-98 §Successor) now works against this honest baseline.

## 2026-07-23 — ERCOT-99 (offer formation at high net load, the 2023-2025 C3c tail): the cleared-share commitment-loading STATE weight prices loaded-at-scarcity gas at COST — a premise the measured DA/RT prices falsify. Turning it off (structural correction, single flag) lifts the 2023 econ offer wall at the scarcity hours ONLY (>=p97 bin): C3a 2023 −33.5→−26.3%, C3b 0.647→0.520, C3c 42→70/181; 2024/2025 byte-identical (RT-ladder years, unweighted). Candidate `2026-07-23-ercot99-state-off-fullspan` registered NOT-YET; keeper UNCHANGED pending owner adjudication

**Charter (ERCOT-98 successor).** Make the measured offer wall the keeper already carries
reachable where it was marginal in reality — with measurements, no residual tuning.
Full forensics: `docs/DIAGNOSIS-ercot-99-offer-formation-high-netload-2026-07.md`; no-LP
probes `scripts/probes/ercot99_{intrahour_bound,reach_gap,model_offer_curve,reanalyze_offer,real_dam_wall,as_contamination,score_probe}.py`.

**Honest denominator (intra-hour).** Splitting the 2023 missed hours by 15-min HB_HUBAVG
hotness (reconstructed on the committed CST clock, reproduces 181): 83 sustained
(>=3/4 intervals >$200), 14 transient (<=1/4). Reach ceiling (caught + sustained-missed)
= 123/181; transients are only 10%. 2024 ceiling 37/53, 2025 25/31 (2025's 0/31 collapse
is NOT transients — 25 of 31 sustained). C3c PASS needs 90 — inside the ceiling.

**Reach gap = DEPTH.** 92/141 missed hours are already in the >=p97 bin where the surface
fires, yet the model clears $56 median (max $128). The reconstructed P1 offer curve (no-LP
monkeypatch capture; marginal cross-checks the sidecar hub within $2) is a flat cheap block
— 58 GW < $50 — with a 4.5 GW cushion of cheap gas ($50-200) above the margin. The
conditional PEAK surface reprices peak rungs +$1076 (to $200-5000) but they sit ABOVE the
cushion; the cleared-share ECON floor adds only +$5.4 — inert.

**Root cause = the state weight.** `ercot_offer_surface_cleared_share_state`'s CC series is
w=0.00 (median) at the missed hours — it stands the econ wall down, on the premise that
RUC/self-committed capacity prices near cost. But the measured actuals at those hours are
DA p50 $327 (93/141 > $200) and RT p50 $488 — loaded-at-scarcity gas clears at the wall,
not cost. The cost-pricing is the wrong sign (falsified premise, like the ercot98 clock).

**Suspects refuted (recorded).** AS-contamination of the ladder — re-deriving above
(energy+AS)-award LOWERS the CC p90 ($93→$54); the DAM CC offers are genuinely cheap, not
AS-held. A 2023 RT ladder — no 2023 SCED energy-offer disclosure exists (only DAM; the
60-Day SCED disclosure is 2024/2025 sample-days). Cross-applying the 2024/25 RT ladder —
the measured CC RT ladder is itself cheap (p50 $57). Residual-tuned adder / RTOLCAP
room-pin — rule 13 / ERCOT-79 pre-registered forbidden. So the wall level cannot be raised
beyond the measured DAM offer quantiles.

**Mechanism (structural, rule 1).** `ercot_offer_surface_cleared_share_state=false`: price
the above-boundary capacity at the measured DAM offer wall (base + (wall−base)) instead of
cost. Effect is ENTIRELY in the >=p97 bin (reach-gap: bins 0-2 byte-unchanged, bin-3
catches 38→61, missed-hour mean hub $70→$133) — no moderate-day over-lift. Adds NO fitted
DOF (removes a derived input's application; DOF ledger 9/8 == keeper).

**Run.** `2026-07-23-ercot99-state-off-fullspan` (full-span 2023-2025, single-flag replay
of the ercot98 keeper). Official `calibration_verdict` vs keeper: C3a 2023 −33.5→−26.3%,
C3b 0.647→0.520, C3c 2023 42→70/181 (0.39×), 2024 12/53 & 2025 0/31 byte-identical (only
2023 lacks the RT ladder and so carries the state-weighted DAM wall). C1 16/16, C2, C4,
C5a, C7 (D-1), C8 (D-2) all PASS; C6 governance UNATTESTED (owner lane). Determination
NOT-YET (C6), structurally more faithful than the keeper. Does NOT reach C3c PASS — the
residual is the unmeasured 2023 RT re-offer wall + the depth of the cheap merit stack,
bounded by what the measured DAM offers contain, not tuned (rule 1).

**LOYO.** Degenerate by construction: the flip reprices 2023 alone (2024/2025 byte-identical),
adds no year-specific parameter (DOF unchanged), and the 2023 correction is justified by
2023's own measured DA/RT prices — no in-sample-gain/held-out-degradation trade to overfit.

**Disposition.** Keeper UNCHANGED (`2026-07-23-ercot98-np6-hsl-fullspan`, NOT-YET). The
candidate is registered as the structurally-more-faithful successor; promotion is the
owner's call.

## 2026-07-23 — ERCOT-100: gas-offer net-revenue margin ADOPTED as ERCOT's go-forward offer form + PROMOTED to keeper (owner directive, rule 1/11) — structurally-correct fuel-invariant markup supersedes the fuel-scaled HR multiplier; gate profile byte-identical to ercot99, determination NOT-YET

**Owner directive** ("no matter what this should become the keeper it is more
structurally sound"), on the standing "structurally more accurate = new keeper"
standard and the cross-ISO net-revenue-margin adoption (NEISO keeper `neiso-61`;
CAISO `2026-07-23-caiso-netrev-margin-keeper`, owner directive same day, rule
1/11). Charter rollout of the `gas_offer_net_revenue_margin` mechanism to ERCOT —
the heaviest, highest-risk ISO, which the design charter pre-flagged as "quite
possibly NOT a keeper" because of the ORDC-wall composition.

**Identification** (branch `claude/gas-offer-net-revenue-isos-1px5vg`, merged):
ERCOT `phys_*` keys on all five gas classes (`_ERCOT_OFFER_CURVE`, cited to the
measured `ercot_campd_marginal_hr_summary.csv` p50s;
`committed→avg_committed_p50`, `econ→marg_econ_{low,high}_p50`, `peak→2.25`
F-class duct ratio for CC / `1.0` full-output bound for CT,ST) + anchor
**2.2494 $/MMBtu** (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`). Flag-on the solve compresses
**1132 tranches at anchor 2.2494** (median fixed margin $18.23/MWh, max
$392.46/MWh — the `CT_PEAKER` peak is the $5,000-ORDC 13.15× wall, which
`phys_peak=1.0` converts to a ~$298/MWh fixed margin on the p50 unit).

**Structural result (the lead — the mechanism does exactly what it claims, zero
fitted scalars).** The offer decomposition is exact: `mc_margin = mc_base +
markup_hr·(anchor − fuel)`, so at `fuel == anchor` the offer reduces
*algebraically* to the registered multiplier form, and only the markup's
fuel-elasticity changes 1→0 (physical burn `phys·HR·fuel` keeps full delivered-fuel
tracking; the markup piece becomes the fixed `markup_hr·anchor`). The markup LEVELS
are the already-registered `offer_curve_by_group` surface (rule 24/25); zero DOF
delta (DOF ledger 9/8 == ercot99; the anchor is a derived measured input, not a
free parameter). Two-sided behaviour confirmed: firms offers below anchor (2024),
compresses above anchor (2023, 2025).

**A/B** (same-HEAD `replay_keeper` of the `ercot99_state_off_fullspan` recipe,
single delta `gas_offer_margin=true`, full 2023–2025, RT-scored
`scripts/probes/netrev_margin_ab.py` + full rubric `scripts/calibration_verdict.py`;
bundles `ercot_netrev_base` / `ercot_netrev_margin`). BASE reproduces the keeper
**byte-exactly** (hourly demand-weighted price MAE 0.000 all three years —
solver-lib env pinned to the recorded highspy 1.14.0 / pandas 3.0.3 / pyarrow
24.0.0):

| year | gas vs anchor | C3a (probe) base→margin | C3b dur-NRMSE base→margin | tight top-1% Δ |
|---|---|---|---|---|
| 2023 | above (compress) | −22.8 → −23.5 % | 2.1518 → 2.1600 | −5.58 |
| 2024 | below (firm)     | −10.0 →  −9.5 % | 1.5276 → 1.5298 | +0.80 |
| 2025 | ≫ (compress)     |  −7.8 → −10.2 % | 0.8352 → 0.8517 | −0.78 |

**Rubric gate profile — BYTE-IDENTICAL to the ercot99 keeper** (the actual
promotion test, per the CAISO `92db03c` precedent): C1 16/16 PASS, C2 PASS,
`dispatch_corr` PASS, `co2` PASS, C7 shape (D-1) PASS, C8 forced_share (D-2) PASS;
**C3a/C3b/C3c FAIL** (ERCOT's ledgered scarcity/tail frontier, ERCOT-94/99 — FAIL
in BOTH arms, not introduced here); C6 governance UNATTESTED (owner lane).
**DETERMINATION: NOT-YET**, identical to ercot99.

**Verdict: KEEPER (`2026-07-23-ercot100-netrev-margin-keeper`).** The strict A/B
refutation bar ("C3b dur-NRMSE ≤ base every year") trips — the duration shape
dips slightly in all three years — but per that criterion's own **rule-1 clause**
(and the CAISO caiso-112→adoption precedent) the structure is the correct one and
the level miss is a *root-cause* problem, not an offer-form one: the >$300 scarcity
tail is under-priced by 600–1300 $/MWh in **both** forms (model tail 660/473/75 vs
actual 1322/1058/724), and the net-rev form merely stops the HR multiplier's
fuel-scaled markup from partially masking it at above-anchor gas (rule 11, exposing
not causing). ERCOT's ORDC scarcity price is itself administrative and
fuel-invariant (set off VOLL/LOLP, not the gas bill), so a fixed-margin peak wall
is the structurally-faithful form — the initial "the margin form is the wrong
direction for ERCOT" read (this session, pre-CAISO-precedent) is **withdrawn**: it
conflated the offer form with the separate scarcity-formation lane. No rubric gate
regresses; the board does not regress in isolation (keeper NOT-YET before and
after). Closing ERCOT's scarcity tail stays the ledgered ORDC/reserve lane
(ERCOT-94/99), not an offer-form change.

**No tuning attempted** (rule 1). 2022 holdout NOT touched (ERCOT carries no
calibration-complete marker; and NOT-YET keepers do not re-check it). A/B bundles
committed (slim meta/run_config/metrics/attestation/legitimacy + hourly sidecars):
MARGIN promoted to keeper, BASE registered as the drift-control diagnostic
(`2026-07-23-ercot100-netrev-base-drift`). Design-doc adoption status updated
(ERCOT → ADOPTED). This entry committed on
`claude/ercot-gas-offer-netrev-margin-9rhqf9`. Next number: ercot-101.

## 2026-07-24 — ERCOT-101: the 2023–2025 scarcity-tail residual is an ATTRIBUTED measured-input bound (no fix), C6 governance attestation DRAFTED + proven to certify → CALIBRATED-WITH-CAVEATS pending owner sign-off. All-no-LP: closed the measurable 2024 tail (cheap up to p90 → attributed), decomposed 2023 (97% is the >$300 tail, one residual with C3a/C3b), bounded 2025 (RT-only scarcity + largest congestion). Keeper UNCHANGED (ercot100 margin keeper); NO solve, NO tuning (rule 1/11/13)

**Task.** Successor to ERCOT-100 (net-revenue-margin keeper). The realistic route
off NOT-YET is CALIBRATED-WITH-CAVEATS via attribution + the owner C6 gate, not a
forced C3c PASS. All lanes no-LP on the committed margin-keeper sidecars +
committed measured corpora. Forensics:
`docs/DIAGNOSIS-ercot-101-scarcity-tail-attribution-2026-07.md`; draft attestation
`docs/handoffs/ercot-101-governance-attestation-draft-2026-07.md`. New probes
`scripts/probes/ercot101_{price_decomp,sced_wall_quantiles}.py`; ERCOT-99 toolkit
re-baselined on the margin keeper.

**Lane B (2023, load-bearing).** Exact load-weighted band decomposition
(`ercot101_price_decomp`, reproduces official C3a −27.1% / rt_lw $64.12):
**97% of the mean-price gap is the >$300 tail** ([300,1000) 27.9% + [1000,∞)
69.4%); the mid-merit [80,200) under-prediction (12.8%) is offset by the cheap-band
[0,30) OVER-prediction (−20.5%). So C3a, C3b (its monthly image) and C3c-2023 are
ONE residual. Hub-level scarcity (LZ−hub congestion only +$15 p50 at the tail), not
a network artifact. `ercot99_model_offer_curve` on the margin keeper: at the Aug
missed hours the model clears $93–184 with a ~480 MW cushion below $200 while
actual RT is $318–2100 — marginal ST_GAS/CT_PEAKER re-offering $500–5000 in RT vs
their measured DAM/merit basis. The only 2023 offer corpus on disk is the DAM
disclosure (wall p50 $327; model tail already forms $211–1244, i.e. above it); **no
2023 SCED/RT re-offer disclosure exists.** Attributed; rule 13 forbids the adder.
Reach ceiling 123/181.

**Lane A (2024, measurable — resolved to an attributed bound).**
`ercot101_sced_wall_quantiles` re-reads the exact 60-Day SCED corpus the frozen
ladder is built from, at extended quantiles: the CC top-net-load-bin wall is
**cheap up to p90** (p50 $41, p90 $115); only p95–p99 ($150–VOLL) is expensive, and
it is (i) sample-day-selection-biased (tail-days corpus) and (ii) VOLL-adjacent
scarcity re-offers = the ORDC overlay's domain (double-count in energy merit). Per
the handoff's own Lane A3 criterion, that is an attributed bound.
`ercot99_model_offer_curve`: the surface reprices ~8 GW but ABOVE the model
marginal (~$70, 706 MW cushion to $200) — depth, not height. `ercot99_reach_gap`:
only ~10/45 missed hours are top-bin; 15/45 are below p80 (moderate net load —
structurally unreachable by a net-load surface). NO ladder-quantile extension: the
apply asserts `rt_q == ladder_q` (couples the load-bearing 2023 DAM wall), it is
residual-motivated (rules 1/23), and it blurs the merit/ORDC boundary.

**Lane C (2025).** RT-only scarcity: DA merit cheap at the tail (DA p50 $91), model
catches 0/31, **largest LZ−hub congestion of the three years (+$64 mean)** above
system lambda a copperplate/reduced-network LP cannot form (network-representation
bound; West/Panhandle split is its own charter). Same attributed family. NB the
margin form left 2025 C3a −8.3% / C3b 0.106 (PASS but nearer thresholds) — another
reason a 2025 RT-ladder re-derive is not pursued (would risk C3a past −10%).

**Lane D (governance — DRAFTED, proven, surfaced for owner).** C6 machine check is
already clean (`outage_source=historic` exogenous; no forbidden flags). Drafted the
four governance assertions + a 5-entry exceptions ledger (collapsing to the three
ledgered criteria C3a/C3b/C3c, 3/3 within the ledger budget). Swapping the draft
attestation onto the registered keeper and re-running `calibration_verdict` yields
**CALIBRATED-WITH-CAVEATS** — 8 gates PASS, C3a/C3b/C3c ledgered as ACCEPTED
MEASURED-INPUT LIMITATIONS, C6 PASS. DOF ledger unchanged (9/8, zero delta). NOT
self-attested — surfaced for owner sign-off; until signed the keeper stays NOT-YET
and the draft handoff is the standing artifact.

**Disposition.** Keeper UNCHANGED (`2026-07-23-ercot100-netrev-margin-keeper`,
NOT-YET). No solve, no dashboard run (all diagnostics no-LP), no tuning. The tail
stays attributed, not tuned (rule 1). Next number: ercot-102.

## 2026-07-24 — ERCOT-102: the "AS-holdout" reopening is REFUTED — the measured ASPLANNP433 plan is ALREADY held out of the energy stack (rigidly at VOLL) and is NON-BINDING at the missed 2023 tail (reserve dual ≈ $0), so holding more AS out cannot reprice it; forcing it to bind over-fires (ercot41/43). The ERCOT-101 attributed bound STANDS, sharpened. Keeper UNCHANGED; NO solve, NO tuning (rule 1/11/13)

**Task.** Successor to ERCOT-101; owner reopened the "attributed bound" to test
whether the 2023–2025 scarcity under-pricing is a structural AS-holdout
(energy-supply) miss — hold the measured ERCOT AS plan out of the energy stack
and re-price scarcity. All no-LP on the committed `ercot100` margin-keeper
sidecars + measured corpora + code. Forensics:
`docs/DIAGNOSIS-ercot-102-as-holdout-refutation-2026-07.md`. New probes
`scripts/probes/ercot102_{reserve_slack,as_holdout_attribution}.py`.

**Lane A (the premise is factually wrong).** The keeper is
`ercot_multiproduct_as_coopt=True`, so `get_reserve_design` uses
`_ercot_multiproduct_design` (spec.py:483). There, with
`ercot_as_forward_requirement=False` (the keeper/backcast value), each product's
requirement falls to `ercot_as_plan_requirement_mw` — the **measured ASPLANNP433
plan** — NOT the forward formula (`ERCOT_AS_ECRS_BASE_MW`, which is the forecast
path only, never evaluated in the keeper). The demanded ONLINE plan (RegUp+RRS
+ECRS, Jun–Sep mean) = **4936 / 4837 / 4378 MW** for 2023/24/25 — *exactly* the
charter's "measured ONLINE AS held out" figures. RegUp/RRS/ECRS are held rigidly
at VOLL via the `ercot_nonreleasable_as_withholding` + `ercot_ecrs_conservative_
deployment` withheld families. The charter's "co-opt holds RegUp 177 + RRS 859 +
ECRS 504 ≈ 1,540 MW" are the **net-of-credit THERMAL residuals** (measured
battery award 1.5/2.2/3.1 GW + Load-Resource RRS credit net the requirement,
correctly — those resources supply that AS in reality), not the total held.

**Lane A1 (no-op proof).** `ercot_ecrs_requirement` is read ONLY in the
single-product `_ercot_design` (spec.py:904), NEVER in the multiproduct builder,
so on the keeper it is byte-identical (CLI path only records it in run_config).
The `ercot101_ecrs_req_probe` bundle (lost with the bare container) did not need
re-running — a ~30-min per-plant solve to reproduce the keeper exactly.

**Lane A (decisive — reserve slack).** `ercot102_reserve_slack` splits the actual
>$300 tail into HIT (model also priced scarcity) and MISSED (model priced
sub-scarcity) and reads the reserve dual (sum of every co-opt family's balance
dual, incl. the rigid VOLL families) from the committed sidecar. 2023: MISSED 88 h
(model $104 / act $862) reserve binds **2/88, mean $0.1**; HIT 59 h (model $1443)
reserve binds 52/59, mean **$4,088**. When the model DOES price >$300, the reserve
binds 41/42 (98%). Same pattern 2024 (MISSED 3/23; HIT 4/5 mean $6,616) and 2025
(0/18, model forms no tail). So the reserve co-opt is the model's own
scarcity-price-former and it works **when the headroom is scarce enough to bind**;
at the MISSED hours it is SLACK — the measured AS is fully held but the model
carries phantom responsive headroom (the ~8–9 GW P1 wedge) where the real 2023
grid retained ~5.7 GW (PRC). Holding *more* AS out cannot lift a dual that is
already slack.

**Lane B (no double-count).** Composition is sound: NonSpin held via the normal
ramp not VOLL (correct — largely offline); battery/LR credits net the requirement
(the measured AS→thermal relationship); `ercot_storage_as_deployment` is the
holdout's ramp mirror; `ercot_ordc_total_reserve` explicitly does not re-add ECRS
(spec.py:1351). Nothing to add without double-counting.

**Lane C/D (moot).** No mechanism change → no LOYO, no new keeper, no dashboard
run. The bind-forcing path (on-line-capacity envelope) is already built,
identified, and REJECTED — ercot41 (2023 hub $46→$347, C3a +797%) and ercot43
(2023 $455, C3a +708%; lifts 2024 +61%) — `docs/handoffs/ercot-online-capacity-
envelope-2026-07.md`. Its §7.4 root cause (energy forced to compete with the full
~10.7 GW ORDC span while the real market ran ~5 GW below it, pricing via ENERGY
offers not the reserve adder) is the same wall from the reserve side.

**Frontier (filed, NOT built).** The genuine untested lever is reserve-DEMAND
right-sizing: cap the headroom at measured RTOLCAP **and** reduce the demand from
the ~10.7 GW ORDC span toward the measured AS plan, so the holdout binds at the
measured level. This re-opens the rule-26-frozen ORDC-family design → owner-
sanctioned round only. First-order caveat: after correct battery+LR credits the
thermal AS demand is ~1.5 GW (< the envelope's ~5.4 GW collapsed room), so a naive
composition likely lands inert, not on target — the demand-side redesign must be
done carefully.

**Disposition.** Keeper UNCHANGED (`2026-07-23-ercot100-netrev-margin-keeper`,
NOT-YET). No solve, no dashboard run (all diagnostics no-LP), no tuning. The
AS-holdout thesis is refuted (already held & non-binding); the ERCOT-101
attributed bound stands, sharpened. C6 governance route unchanged (owner sign-off
pending). Branch `claude/ercot-102-as-holdout-repricing-aq6o1e`. Next number:
ercot-103.

## 2026-07-24 — ERCOT-103/104: owner-authorized reserve-demand right-sizing (rule-26 round) and West/Panhandle split BOTH bounded by measured data — neither closes the 2023 tail, no keeper. ERCOT's own settlement data: the 2023 scarcity tail is 97% ENERGY DUAL, 3% reserve adder (RTORPA $42); the faithful realized-room RTORPA UNDER-fires (probe regressed C3a −16.8→−24.4%), the in-LP envelope OVER-fires (ercot41/43); the §3 West congestion is NODAL (station lines $3,387 shadow) not zonal (interfaces $15) → no measured zonal import limit (rule 11). Keeper UNCHANGED

**Task.** After ERCOT-102 the owner authorized (2) the rule-26 ORDC-family
reserve-demand right-sizing round and (3) the West/Panhandle topology split.
Both pursued to a decisive result. Forensics:
`docs/DIAGNOSIS-ercot-103-104-reserve-demand-and-wp-split-2026-07.md`. New probe
`scripts/probes/ercot104_west_congestion_nodal.py`; registered solve probe
`2026-07-24-ercot103-realized-adder-rtorpa` (one-year 2023 diagnostic, REJECTED).

**ERCOT-103 (reserve-demand right-sizing) — REFUTED.** ERCOT publishes the settled
RT scarcity components (`ercot_2023_ordc_reserves_hourly.parquet`): at the 2023
tail (settled >$300, 146 h) the price is **97% system λ (energy) $1,307 / 3%
RTORPA (reserve adder) $42**, with the market holding only ~5.5 GW PRC. So a
reserve-side mechanism has a ~3% ceiling on the tail. The faithful realized-room
RTORPA (`ercot_ordc_only_scarcity` + extreme envelope pricing-basis, in-LP span
off) **regressed**: C3a −16.8→−24.4% (hub) / −27.3→−35.5% (zonal), C3c 76→71,
model priced >$300 in 20 h (keeper 42) — because `ordc_only` drops the RegUp/RRS
withheld families to the plan-hold epsilon (removing the keeper's reserve-VOLL
tail-formation, ERCOT-102 §2), and the realized RTORPA is only $18 (< measured
$42, phantom-headroom-diluted). The in-LP envelope OVER-fires (ercot41/43). The
keeper's reserve-VOLL co-opt is the least-bad proxy. Frozen ORDC constants
untouched (rule 26); nothing swept to a price.

**ERCOT-104 (West/Panhandle split) — BLOCKED (rule 11).** Panhandle is already a
distinct zone; the wind-corridor export interfaces (WESTEX/PNHNDL/NE_LOB) are
already `TransferLink`s at measured GTC limits. The §3 residual is an
import-direction premium, but `ercot104_west_congestion_nodal` on the measured
NP6-86 SCED archive shows the congestion rent is **NODAL** (station-to-station
60–518 MW lines, mean shadow **$3,387**: KINGNW $5251, VERN_69T1 $3294, …) not
zonal (interfaces mean shadow **$15**). A 7-zone reduced network cannot form nodal
congestion, and no measured *zonal* import limit exists because the phenomenon
isn't zonal. Prior art (Far_West REVERTED, WP-A DEFERRED) confirms the
copper-plate no-op. It is also 2025-only (2023 congestion +$15) and Tier-0 —
would not touch the load-bearing year. Not built.

**Disposition.** Keeper UNCHANGED (`2026-07-23-ercot100-netrev-margin-keeper`,
NOT-YET). Both authorized lanes closed as bounded/blocked by measured data; the
2023 tail residual is the energy-offer / RT-conduct bound (no 2023 SCED source),
now confirmed FOUR independent ways (offer side ERCOT-101, reserve-holdout side
ERCOT-102, settlement decomposition ERCOT-103, congestion resolution ERCOT-104).
C6 governance route unchanged (owner sign-off pending). Branch
`claude/ercot-102-as-holdout-repricing-aq6o1e`. Next number: ercot-105.
