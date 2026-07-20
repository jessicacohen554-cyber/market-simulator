# ERCOT-89 (design/charter) — the shoulder-hour online-capability lane: quantity-side successor to the mid-band offer lanes

**Status: chartered 2026-07-19 (owner go-ahead: "charter the successor,
measurement/charter scoping only"). §4 step 1 (measure-first) EXECUTED this
session — see §8. No apply seam, no mechanism, no solve beyond the throwaway
keeper replays that supplied the model-side hourlies. The §7 step 2 build is
OWNER-GATED, not started.** Successor lane to ERCOT-87/88
(`ercot-residual-midband-formation-lane-2026-07.md`), opened per that
charter's §10 disposition: the offer-surface enumeration for the
moderate-tightness band is CLOSED — the residual is quantity-side.

## 0. One-line answer

The un-formed $150–500 band hours are hours where the REAL merchant fleet ran
a razor-thin **online** margin — CC essentially fully ON with a few hundred MW
of spare, CT committed far above its same-net-load norm with ~100 MW spare,
the rest of the capability OFF — while the model's availability basis
(`ercot_thermal_dam_availability`: class-DAY mean, only-OUT-is-out, flat
within the day) hands the LP that same capability as base-offer-priced,
always-online headroom every hour. The band cannot form because the model has
no **hour-level commitment state**: it never distinguishes a thin-spare
shoulder hour from a fat-spare hour at the same net load. The lane's object is
that hour-level online-capability envelope — measured first, mechanism only if
the measurement supports a conditional, forward-native driver.

## 1. The target (inherited from ERCOT-86/88, unchanged)

From ERCOT-88 (calibration log 2026-07-19; ercot86 keeper base): at the
actual $150–500 hours the keeper forms 5/68 (2024) and 4/65 (2025); the
un-formed ~60 hours/year sit in the diffuse Apr/May/Jul/Oct/Dec shoulder
regime. The annual level is closed (C3a −1.3 % / +1.4 %) and zero spurious
in-band hours — this lane is **pure shape (band occupancy), never level**.
Both measured offer surfaces are built and faithful and neither fills the
band: the ERCOT-86 online-spare RT wall (adopted, in the keeper) prices the
ON-status spare that exists, and the ERCOT-88 offline fast-start pool
(merged default-off) prices the startable increment — which the LP then
clears only where already scarce, because **cheaper online headroom carries
the shoulder hours**. Where that headroom comes from is this charter's §4
measurement.

## 2. The quantity-side diagnosis (why the model carries phantom online headroom)

The model's thermal capability in a backcast hour is
`pmax × availability(g,t)` where, for the covered merchant classes, the
availability is RESCALED to the measured DAM-disclosure class-day fraction
(`fleet.py` DAM overlay; `derive_ercot_thermal_dam_availability.py`). Three
structural properties follow, each measured in §8:

1. **Only-OUT-is-out.** The measured fraction counts every non-OUT status —
   ON, OFFQS/OFFNS (startable), plain OFF — as available. Correct for
   *availability* (offline units can be started), but the LP prices ALL of it
   at base offers: an OFF CC train enters the merit order with no start, no
   min-run, no start-inclusive offer. (ERCOT-88 re-priced only the
   fast-start-CT slice above its measured pool boundary — min-down ≤ 2 h,
   OFFQS/OFFNS — and found the LP simply cleared around it.)
2. **Day grain.** The overlay is a class-DAY mean broadcast flat over 24
   hours. Intra-day structure — evening HSL recovery, midday derates, units
   OUT for part of a day — is invisible, so the model's capability in the
   day's tightest hour equals its capability at 3 am.
3. **No commitment state.** P1 has no ON/OFF distinction for these classes in
   the shoulder regime (the gas commitment bridge floors committed-CC
   *minimums* in tight-day windows; nothing restricts the *ceiling* of what
   is instantaneously online). The real market's SCED clears against the
   telemetered ON fleet; starts arrive at start-inclusive offers with lags.

The hypothesis: in the residual band hours reality's ON-status capability and
spare were far below the model's every-hour capability, and that wedge — not
offer heights — is why the model clears those hours at $50–65.

## 3. Prior art and rule-19/26 reconciliation (read before any build)

* **`ercot_online_capacity_envelope` (+`_extreme`) — the ercot41/43 REJECTED
  probe family** (`ercot-online-capacity-envelope-2026-07.md`). A hard LP row
  capping energy + reserve at the measured online capability, aimed at the
  2023 **scarcity tail**. Correctly identified, it still over-fired
  catastrophically ($347–455 hub 2023) because the cap forces energy to
  compete with the full ~10.7 GW ORDC total-reserve span inside it (its §7.4
  structural conclusion). ANY ERCOT-89 mechanism must be reconciled against
  that finding, and three design lines follow: (i) the target regime here is
  the sub-scarcity shoulder band, not the ORDC tail; (ii) a **cap** that
  compresses the co-opt's shared headroom re-opens the rejected family and
  the rule-26-frozen ORDC design — the admissible shape is a **re-pricing of
  the offline increment** (capability stays available, at its true
  start-inclusive offer), which creates no phantom reserve shortage; (iii)
  the ercot41/43 lesson that a binding-regime-mean identification hides tail
  shape errors applies to any conditional ON-share driver built here.
* **`ercot_faststart_pool_offer` (ERCOT-88, merged default-off)** already
  implements exactly that admissible shape for the fast-start CT slice:
  measured pool boundary, measured ladder, REPLACE-BY-MASK, one owner per
  row-hour. A quantity-side successor that widens the re-priced slice
  (larger measured offline share; CC at its own measured start economics)
  would EXTEND this machinery, never stack a second markup on the same rows
  (rule 19). The ERCOT-88 D-2 enumeration (charter §9.1) remains the row-
  ownership map; any new leg re-derives it.
* **`ercot_gas_commitment_bridge` (ON in the keeper)** owns committed-CC
  min-gen floors. An online-capability mechanism touches the CEILING side
  (what is NOT online), so overlap is possible only if a variant tried to
  force offline-ness via floors — forbidden here by construction (§6).
* **The DAM availability overlay (ON)** is the quantity seam itself: §2's
  properties 1–2 are ITS grain choices. A refinement (hour grain; status-
  resolved pricing) modifies/extends that seam — never a second stacked
  availability channel (rule 19).

## 4. The measurement (step 1 — executed this session, §8)

Probe: `scripts/probes/ercot89_shoulder_online_measure.py` → artifact
`data/raw/_validation-source/ercot89_shoulder_online_measurement.json`.
MEASUREMENT ONLY. Corpus: the four on-disk NP3-965 60-Day SCED Gen Resource
sample-day parquets (ERCOT-74/75/86 intake — no new fetch); merchant scope
CCGT90/CCLE90 → CC, SCGT90/SCLE90 → CT (the wall's universe). Model side:
throwaway single-year replays of the ercot86 keeper (rule-16 diagnostics,
never registered, deleted after measurement) supply the hourly
demand-weighted P1 price and per-class dispatched MW.

Per covered hour × class it measures: HSL by telemetered status family
(ON / OFFQS / OFFNS / plain OFF / OUT), ON Base Point, ON spare
(HASL−BP and HSL−BP), the day-mean non-OUT HSL (the corpus-basis analogue of
the model's class-day capability), the model's price, class dispatch, and an
estimated model capability (`cap_hat ×` DAM class-day availability — the
bundle persists no availability; cap_hat inferred from the replay's own peak
dispatch/avail ratio, disclosed). Hour sets: **residual** (actual RT in band,
model < $150), **formed** (both in band), and **bin-matched controls** (both
< $150, same net-load bins as the residual set) — the controls carry the
condition-specificity question. Coverage is disclosed per bin (the corpus
covers ~35/68 and ~37/65 of the band hours; the Jan-2024 winter-morning
cluster remains un-intaken, inherited from ERCOT-87 §8).

## 5. Pre-committed adjudication criteria (set BEFORE the model side was read)

* **H1 — the wedge is real.** In residual hours the model's class capability
  (and its headroom above own dispatch) materially exceeds the measured
  ON-status capability (and measured ON spare) — the phantom-online-headroom
  hypothesis. Refuted if reality's ON spare + startable pool is comparable to
  the model's headroom (then the band forms some other way — demand side, AS,
  net-load error — and this lane closes as measurement-refuted).
* **H2 — a conditional driver exists (rules 12/13).** The residual hours'
  ON share / spare must be distinguishable from bin-matched controls (thinner
  spare at the SAME net load), and the distinction must project onto
  measurable conditioning (finer net-load structure, season × hour block,
  intra-day position, outage state) — not only onto the hour's own identity.
  If band hours are indistinguishable from controls on every measurable
  conditional, an hour-level envelope has no forward driver and only a
  per-hour outcome pin could implement it — rule-13-forbidden, lane closes.
* **Class attribution.** The measurement must say WHERE the model's cheap
  headroom sits (CC vs CT vs outside the merchant scope entirely). If the
  binding headroom is outside merchant CC/CT (coal, ST_GAS, storage,
  imports), the successor lane is re-scoped before any build.

## 6. Admissibility rules for any step-2 mechanism (rule ledger)

* **Rule 13 — the bright line.** The per-hour telemetered ON series is an
  operational OUTCOME of the day's commitment; pinning it into the backcast
  hour-by-hour would be a quantity-side answer key (no forward analogue,
  fails the regenerate-for-a-forward-year test). What IS admissible is the
  **conditional structure**: measured ON-share / online-spare distributions
  per (net-load bin × season × hour block), regenerating forward from the
  same drivers — exactly the construction standard of the ERCOT-86 ladders
  and the rejected-but-admissible ercot41/43 shares. The measurement may use
  the hourly series to BUILD and VALIDATE the conditional object, never ship
  it raw.
* **Rule 12.** Any commitment-state gate rides on unit physics (min-down,
  startup cost), never class tuples; a mechanism must state its window,
  driver, and forward story.
* **Rule 19.** One owner per phenomenon: extend the ERCOT-88 pool seam / the
  DAM availability seam — never a third channel stacked on the same rows;
  re-derive the D-2 enumeration before any seam is written.
* **Rules 1/11.** Never reject a structurally-correct mechanism on fit; never
  reach the band with a knob that isn't real (an offline share tuned to the
  residual is exactly that). The ercot41/43 §6.1 pre-committed evaluation
  rule carries over: degrading the current-design years is a rejection.
* **Rule 23.** Any derived conditional ON-share artifact freezes against
  residuals; re-derives only on SCED/DAM source update.
* **Candidate shapes (sketches only, NOT designed here):** (a) generalize the
  ERCOT-88 pool leg to the full measured conditional offline share of
  merchant CT — and CC at its own measured start-inclusive economics — so the
  offline increment is priced, not free; (b) refine the DAM availability
  overlay from class-day to class-hour grain from the same disclosure
  (captures intra-day OUT/derate structure; does NOT touch ON/OFF); (c) an
  explicit conditional online-capability state for merchant classes (the full
  envelope). Each is its own gated design with its own D-2 enumeration; (c)
  must additionally clear the §3(ii) no-cap line.

## 7. Recommended path (for the owner to authorize)

1. **Read §8.** If H1+H2 hold: authorize ONE step-2 design round (pick among
   §6 shapes against the measured attribution), default-off gate, single-year
   2024 rule-16 probe with the C3a level guard + zero-spurious gate + a NEW
   guard — the 2023 scarcity tail and C3b/C3c must not degrade (the
   ercot41/43 failure signature) — then 2025, then full-span LOYO, the
   ERCOT-86 cadence.
2. If H1 or H2 fails, the lane closes as a documented measurement limit;
   ercot86's partial fill stands as the honest result (its standing
   attestation exception already names this successor lane).
3. **Keeper stays ercot86** throughout (rule 27, owner-only swap).

**Deliverable of this charter:** this document + the §4 probe + artifact +
§8 results. The build is chartered, not started, pending owner go-ahead.

## 8. Measurement results — §4 step 1 executed (2026-07-19)

Artifact: `data/raw/_validation-source/ercot89_shoulder_online_measurement.json`.
Coverage: **35/68** (2024) and **37/65** (2025) actual band hours on sample
days (residual = model < $150 at those hours: 35 and 33; the 4 formed 2025
hours fall on sample days, the 5 formed 2024 hours do not; Jan-2024
winter-morning cluster still un-intaken, inherited). Model side from
single-year throwaway replays of the ercot86 keeper (deleted after
measurement; their slim class/system hourlies harvested into
`results/calibration/ercot86_rtwall_fullspan/hourly/`).

### 8.1 H1 — the phantom online margin is real (CONFIRMED, both years)

Medians over covered residual hours; "spare" = ON-status HASL − Base Point,
"headroom" = estimated model capability − model dispatch:

| year | class | meas ON HSL | meas BP | meas ON spare | model cap (est) | model MW | model headroom |
|---|---|---|---|---|---|---|---|
| 2024 | CC | 22,080 | 21,913 | **325** | 22,169 | 19,697 | **2,274** |
| 2024 | CT | 6,892 | 6,795 | **100** | 5,688 | 3,558 | **1,924** |
| 2025 | CC | 27,126 | 24,927 | **446** | 25,503 | 23,380 | **2,117** |
| 2025 | CT | 7,113 | 7,043 | **77** | 5,408 | 4,065 | **1,437** |

The real market ran the residual band hours on a **~0.4–0.5 GW total
merchant online margin**; the model carries **~3.6–4.2 GW** of base-offer
headroom in the same hours — **8–10×**. This is the direct block on band
formation: the ERCOT-86 wall prices spare at the measured per-MW-rank
ladders, so with ~10× the spare MW the model's marginal rank sits deep in
the cheap rungs. **The quantity is the error, not the price** — with
reality's spare, the already-measured ladders would price the band.

### 8.2 H2 — the thin-margin state is condition-specific (CONFIRMED; CT by
ON share, CC by loading depth)

Vs bin-matched controls (same net-load bins, actual & model < $150):

* **CT commits FOR the band hours**: ON share 0.76 vs 0.49 (2024) and 0.71
  vs 0.52 (2025), separated in EVERY net-load bin (e.g. 2024 bin 1: 0.71 vs
  0.28; 2025 bin 4: 0.64 vs 0.45), with resid spare thinner than control
  spare in nearly every bin. The discriminator survives net-load
  conditioning — a conditional driver exists beyond annual net-load
  percentile (candidates for step 2: finer net-load structure, season ×
  hour block, ramp position).
* **CC is ~always ON** (share 0.97–0.99 in both sets); its state variable is
  **loading depth**: ON spare collapses control → resid (867 → 325 MW in
  2024; 1,079 → 446 in 2025). The model reproduces the direction but not
  the level (headroom 4.0 → 2.3 GW in 2024) — it never gets thin.
* OUT is also higher in 2024 resid hours (CC 2,646 vs 1,895 MW) — intra-day
  outage structure the day-mean overlay partially smooths (§2 property 2).

### 8.3 Class attribution — where the model's cheap energy comes from

Total gas is RIGHT in both hour sets (2024 resid: model ≈ 34.0 GW vs
EIA-930 NG 34.7); the failure is **composition and state within gas**.
Control → resid, reality surges merchant CT (BP 4.3 → 6.8 GW, via starts —
the ERCOT-87 measured 12–18 starts/hour) and loads CC to its ON ceiling;
the model instead rides **ST_GAS 4.1 → 6.1 GW** (2024; 6.1 GW again in
2025) and under-dispatches merchant CC+CT by ~4.5–5.5 GW vs measured Base
Points. Inference (not directly measured — the corpus lacks ST restypes):
reality's non-CHP steam-gas contribution in these hours is ~1–2 GW, so the
model's ST_GAS is ~3× over-dispatched in exactly these hours; a
CAMPD-based ST_GAS hourly check is the named follow-up measurement if step
2 needs it. Secondary signal, a fortiori: the model carries ~4.6 GW LESS
VRE than reality in the 2024 resid hours (evening solar shape) and still
clears $30–80.

### 8.4 Caveats

(a) Merchant-scope offset: corpus CC/CT restypes ≠ model CC_REGULAR/
CT_PEAKER exactly (2025 meas ON CC 27.1 GW > model cap 25.5; meas nonOUT CT
9.5–10.6 GW vs model cap 5.4–5.7) — within-basis shares/deltas carry the
evidence, cross-basis levels do not. (b) `model cap` is the disclosed
cap_hat × DAM-day-avail estimate. (c) Hourly lambda smooths intra-hour
spikes. (d) ST_GAS attribution is inferred, not measured.

### 8.5 Verdict for §7

H1 and H2 both hold; the class attribution names two coupled quantity-side
objects for the owner-gated step 2: **(i)** the merchant CC/CT hour-level
online margin (the envelope proper — §6 shapes (a)/(c), CT by conditional
ON share, CC by conditional loading depth), and **(ii)** the ST_GAS
shoulder-hour dispatch level (rule-19-owned by the ST_GAS drag lane — any
fix there is that lane's, not this one's; the two must be reconciled in the
step-2 D-2 enumeration, not stacked). The lane proceeds to the §7 owner
decision with the measurement supporting a build.

## 9. Step-2 build record (ERCOT-89, 2026-07-19 — owner-authorized design round)

The owner authorized ONE step-2 design round. Mechanism built:
`ScenarioConfig.ercot_shoulder_online_span` (default **off**) — §6 shape (a)
implemented as a GEOMETRY correction of the two existing seams (rule 19: the
wall and the pool stay the owners of their rows; the span is a measured
conditional parameter of both, never a third channel):

* **Wall seam** (`fleet.build_ercot_offer_surface_cleared_share_markup`): the
  RT/SCED spare-offer ladder's rel denominator re-anchors from the full
  DAM-available span to the measured conditional online span —
  `rel = (share − boundary) / (span(cell) − boundary)`, clipped to the ladder
  top above the span. The ERCOT-86 ladder is measured on the ONLINE fleet's
  Base-Point→HASL segments; stretching it over capability that is telemetered
  OFF at the same conditions is exactly the §8.1 8–10× phantom-headroom wedge.
  Same owner, same rows, same ladders — only the coordinate mapping changes.
* **Pool seam** (`fleet.build_ercot_faststart_pool_markup`): the boundary
  generalizes from the ERCOT-88 static `1 − pool_frac(bin)` to the span
  (clamped below by the bin's DA cleared share), so the FULL offline CT
  increment — not just the OFFQS/OFFNS quick-start slice — is PRICED at the
  measured start-inclusive ladder. Physics gate unchanged (rule 12,
  `min_down ≤ 2 h`); slow rows above the span keep the wall's ladder-top
  clamp. §3(ii) is honoured by construction: no LP row, no cap, no floor, the
  co-opt's shared reserve headroom untouched; D-2 forced-share / D-4
  off-window exposure vacuous (no forced energy anywhere in the mechanism).

**The conditional driver** (rule 13): `scripts/data/
derive_ercot_shoulder_online_span.py` →
`data/raw/_validation-source/ercot_shoulder_online_span_condbinned.json` —
mean telemetered ON share of non-OUT capability per (net-load bin × season ×
4h block), hierarchically coverage-gated (≥6 corpus hours per cell, fallback
bin×block → bin×season → bin), year-scoped 2024/2025 with NO pooled fallback,
zero fitted scalars, frozen against residuals (rule 23). The non-OUT
denominator is the DAM-availability overlay's own only-OUT-is-out basis, so
the span coordinates map exactly onto the capability the overlay leaves in
the LP.

### 9.1 Driver adjudication (pre-build, leave-one-out)

The conditional structure is REAL but PARTIAL. Cell-mean LOO assignment vs
the measured per-hour truth over residual/control hours:

| year | measured resid vs control ON share | best conditional (bin×season×block ±idr) LOO gap | share of separation carried |
|---|---|---|---|
| 2024 | 0.752 vs 0.480 (gap +0.27) | 0.63–0.65 vs 0.50 (gap +0.14–0.15) | ~½ |
| 2025 | 0.713 vs 0.530 (gap +0.18) | 0.60–0.61 vs 0.55 (gap +0.05–0.07) | ~⅓ |

The remainder is day-of commitment information (forecasts, outages, RUC
decisions) with no forward analogue — deliberately NOT encoded (rule 13's
bright line). H2's kill criterion (indistinguishable on every measurable
conditional) is NOT triggered; the build proceeds on the partial driver, its
partial reach disclosed in the artifact provenance.

### 9.2 Static supply-stack screen (design-time, pre-LP)

A fixed-dispatch re-clearing of the keeper's gas-trio demand against the
re-priced stack (keeper sidecar hourlies + the artifacts), run before the
seam was written:

* **Standalone the mechanism is predicted near-band-inert**: with the span
  compression active, the residual hours' static median moves only $27→$34
  (2024) / $48→$72 (2025); the marginal supply in the residual hours is NOT
  merchant CT — it is ~2.3–2.4 GW of CC mid-rungs at $40–130 plus ST_GAS
  headroom, i.e. exactly the §8.3 ST_GAS displacement wedge (the model's CC
  slack exists because ST_GAS over-dispatches into the hours where reality
  loaded CC to its ON ceiling). The mechanism's band potency is therefore
  CONDITIONAL on the ST_GAS lane closing its shoulder-hour level —
  pre-registered here before the probes ran.
* Spurious risk small (6–12 static hours); 2024 static scarcity-tail median
  moves +$60 toward actual (watch the pre-committed tail guard, both
  directions).

### 9.3 Rule-19 / D-2 attribution enumeration (re-derived for this seam)

Baseline: the ERCOT-88 §9.1 map (`ercot-residual-midband-formation-lane`).
Deltas for the span:

1. `ercot_offer_surface_conditional` (ON) — PEAK rungs, untouched; the span
   touches econ* rows inside the wall builder only. The pool's
   REPLACE-BY-MASK may own peak row-hours above the span, the unchanged
   ERCOT-88 semantic (one owner per row-hour, wider mask).
2. `ercot_offer_surface_cleared_share` + `_state` + `_rt` (ON) — the span
   MODIFIES this owner's rel geometry; DAM and RT legs compress identically;
   the state weight and replace/tier composition are untouched.
3. `ercot_faststart_pool_offer` (REQUIRED armed) — boundary parameter
   generalized; ladder, physics gate, composition unchanged.
4. `ercot_gas_commitment_bridge` (ON) — merchant-CC min-gen FLOORS (quantity
   side); the span is bid-side only on econ rows — disjoint axes, no
   overlap. No CT floor exists in the recipe → the rule-17 hazard is
   structurally impossible.
5. `ercot_thermal_dam_availability` (ON) — the quantity seam is untouched:
   the span re-prices within the availability, never removes MW; no
   phantom reserve shortage is possible (the ercot41/43 §7.4 conclusion
   stays closed).
6. Reserve side (`ercot_reserve_supply_cap`, `ercot_nonreleasable_as_
   withholding`, ON) — quantity-side, status-agnostic; the span never
   touches reserve rows or headroom tiers.
7. **ST_GAS — RECONCILED, NOT FIXED** (§8.5(ii)): the drag lane owns the
   ST_GAS level; the span deliberately leaves ST_GAS rows untouched
   (`ercot_offer_surface_cleared_share_steam` stays off in the recipe). The
   §9.2 finding quantifies the coupling: the band residual cannot close from
   this lane alone while the displacement wedge stands.

### 9.4 Probe results (rule-16 single-year throwaways, pre-committed guards)
— REJECTED AS ARMED, no retune

Base = the committed ercot86 keeper 2024/2025 hourly sidecars; probe =
`replay_keeper --set ercot_shoulder_online_span=true --set
ercot_faststart_pool_offer=true`; analyzer
`scripts/probes/_ercot89_span_check.py`. The mechanism ENGAGED both years
(466/473 walled rows re-anchored; 486/497 fast-start rows on the span
boundary vs ERCOT-88's 173/91 — not inert by mis-wiring):

| year | C3a resid (base→probe) | band formed | spurious Δ | h>$200 model (actual) | NRMSE proxy | gates |
|---|---|---|---|---|---|---|
| 2024 | −1.3% → **+3.0%** | 5/68 → 7/68 | **+2** (7→9) | 13→21 (53) | 2.044→2.109 | C3a **DEGRADED**; spurious **TRIPPED**; tail HELD |
| 2025 | +1.4% → **+4.8%** | 4/65 → 10/65 | **+5** (2→7) | 1→10 (31) | 0.970→0.957 | C3a **DEGRADED**; spurious **TRIPPED**; tail HELD |

Failure decomposition (both years, same signature): the level/spurious trip
is **death-by-small-lifts** — ~230 (2024) / ~228 (2025) hours with actual
< $150 rise $9–19 each, because the cell-mean span compresses in
conditioning cells that MIX residual hours with same-cell control hours
(the §9.1 partial-driver limit realized). The new spurious hours are 1–2 h
bleeds around real price events (2024: the May cluster whose core hour
cleared $912 actual; 2025: an October shoulder cluster). Band fill is
modest (+2 / +6 formed hours). The true sub-scarcity tail moves TOWARD
actual in both years (2024: mean +$141 in actual->$500 hours, h>$200
13→21 vs 53; 2025: 1→10 vs 31) — real but belonging to the standing C3c
successor lane's regime, and not grounds to keep a mechanism that trips
the level and spurious guards in both current-design years (the §6.1-style
pre-committed rule inherited at §3: degrading the current-design years is
a rejection; rules 1/11: no re-sweep of the frozen span table against
this residual).

### 9.5 Disposition and structural conclusion

**REJECTED as armed; the mechanism stays MERGED default-OFF** (the
ercot41/43 rejected-probe pattern: machinery + artifact + tests + this
record kept, byte-identical when off — the flag-off no-op is
test-enforced). Keeper stays **ercot86**; nothing registered (rule-16
throwaway bundles deleted after analysis). The structural findings:

1. **H1's wedge is real but its rule-13-admissible projection is too
   coarse to form the band.** The conditional ON-share structure carries
   ~½ (2024) / ~⅓ (2025) of the residual-vs-control separation; the
   band-forming remainder is day-of commitment information (forecasts,
   outages, RUC) with no forward analogue. At cell-mean grain the
   compression cannot distinguish a residual hour from a control hour in
   the same (bin × season × block) cell — it lifts both, and ~230 lifted
   control hours/year is exactly the C3a/spurious signature observed.
   Sharper conditioning within rule 13 needs a materially broader
   SCED-disclosure corpus (finer cells with ≥6-hour coverage — a
   data-intake question, not a mechanism question).
2. **The ST_GAS displacement wedge remains the binding blocker** (§9.2,
   confirmed by the probes): even where the span binds, the LP re-clears
   the shoulder hours on CC mid-rungs + ST_GAS headroom that reality did
   not have. Re-visit shape (a) only AFTER the ST_GAS drag lane closes
   its shoulder-hour level — the two lanes' coupling is now quantified.
3. **The tail improvement is a lead for the C3c lane**, not this one: the
   span geometry materially helps exactly where dispatch is pinned at
   capability (the ercot86 keeper's known h>$200 deficit). If that lane
   ever re-opens the scarcity-formation design, the span-anchored ladder
   in the TOP bins (where commitment saturates and control-hour
   contamination vanishes) is measured, built, and dormant here.

The §0/§1 objective stands honestly un-met: the ERCOT-86 partial fill
remains the keeper result, now with the quantity-side envelope measured,
built, probed, and adjudicated rather than hypothesized.
