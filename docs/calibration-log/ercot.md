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
2025 derive — owner to re-intake or remove. Keeper UNCHANGED; nothing registered
(no solve). Next number: ercot-95.
