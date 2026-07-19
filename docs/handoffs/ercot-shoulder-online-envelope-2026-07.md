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

*(filled after the model-side replays completed — see below)*
