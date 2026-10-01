# GATESPEC — caiso-192 (lane 1): CAMPD outage-overlay mechanical-vs-economic identification

**Authored by caiso-191 on 2026-08-11, BEFORE any lane-1 measurement exists.** These
gates are fixed and fail-closed; the measuring session may not amend, re-anchor, or
re-scope them. Authorization: owner ruling 1 (caiso-187 option 1, GRANTED —
`caiso191-owner-rulings-2026-08-11.md`).

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

The favorable error direction here is concrete: reclassifying an outage span as
economic layup DROPS it from the overlay and RESTORES capability, which lowers price.
Every ambiguity rule below therefore resolves the other way.

## 1. Objective

The CAMPD-derived CAISO outage overlay's detector identifies **downtime**, not
**mechanical unavailability** (FINDING-caiso187 §3: a CC uneconomic for a fortnight in
the spring solar surplus is indistinguishable, on CF alone, from one that is broken).
The lane separates the two for the CAISO gas classes carried by the overlay
(CC_REGULAR, CC_CHP), using the machinery already shipped for exactly this question —
`scripts/lib/outage_detect.py::build_merit_order_panel` / `filter_merit_order_layup` —
so that only MECHANICAL spans derate the LP. caiso-181's zero-interior-contradiction
result stands untouched: it proved the units were down; this lane classifies WHY.

Rule 23 `[R-FROZEN-DERIVE]` recital: this re-derivation is licensed by a defect in the
measured input's own classification, measured by caiso-187 and granted by the owner —
not by a residual move. The commit message must cite caiso-187 §3 and ruling 1 as the
cause.

## 2. Exogenous instrument closure

The classifier and every gate statistic may touch ONLY:

* CAMPD unit-level operation (`grossLoad`, `heatInput`, `steamLoad`,
  `primaryFuelInfo`) — the committed `data/raw/campd-unit-level/` parquets;
* delivered fuel prices — the F923 delivered-coal ladder and the ISO delivered gas
  hub series (rule-13 admissible measured inputs);
* EIA-860 fleet identity (unit/plant capacities, class membership);
* EIA-930 CISO net load — for the seasonality DIAGNOSTIC only, never in the
  classifier decision itself.

**FORBIDDEN anywhere in any classifier or derivation: every LMP/price series** —
DA/RT/hub/OASIS LMPs, model duals, any scored residual, any benchmark. The revealed
clearing cost (RCC) is built only from measured heat rates × delivered fuel prices,
as the shipped panel already does. Any price read voids the session.

## 3. Numeric gates — each with its written anchor

| gate | bar | anchor (never the values under adjudication) |
|---|---|---|
| **G-RATE** | Post-filter CC_REGULAR mechanical-removal rate, measured through the SHIPPED loader (`outages.unit_outage_derate_factors`, the caiso-187 §2 `X_c` basis), within **[0.07, 0.15]** in EACH of 2023/2024/2025. | Published expectation `POF 0.05 + WEFOR 0.05 ≈ 0.10` for CC_REGULAR — the keeper runs `coal_drop_pof=True`, so the overlay carries planned outages too (FINDING-caiso187 §3a). The band's width covers fleet-age dispersion around the published rate; it is anchored to the published rates, NOT to the measured 21.6/26.2/31.9 % under adjudication. |
| **G-STAB** | Post-filter year-over-year change ≤ **3 pp** (absolute rate), and post-filter 2025 rate ≤ **1.5 ×** post-filter 2023 rate. | Physical stationarity: mechanical failure + planned-maintenance rates do not grow ~48 % in two years on a 28-plant, 15.3 GW fleet; economic displacement does (caiso-187 §3b). |
| **G-SEP** | (a) Capacity-weighted mean out-of-merit share of RECLASSIFIED (layup) span-hours ≥ **0.80**; (b) separation vs RETAINED (mechanical) spans' mean out-of-merit share ≥ **30 pp**; (c) seasonality signature: the reclassified span-hours' Mar–May share strictly exceeds the retained spans' Mar–May share (the spring-surplus concentration). | The guard's own frozen identification record (`outage_detect.py` doc block): window-grain out-of-merit share is near-binary (NEISO p25 = 0.00, p75 = 1.00) — a pre-existing repo measurement. A clean identification separates; a muddy one does not deserve to relieve capability. The seasonal leg is caiso-187 §3c's shape, used here as a one-sided signature, not a fit target. |
| **G-LOYO** | The shipped frozen constants (`MERIT_RCC_PCTL = 0.90`, `MERIT_OOM_FRAC = 0.90`, `REAL_RUN_CF`, `MIN_REAL_RUN_HOURS`, `MERIT_HR_MIN/MAX`) are used AS SHIPPED — rule 23 forbids re-fitting them here. If the session introduces ANY new threshold or parameter, it must be (i) committed in the PRECHECK before any classification output exists, and (ii) LOYO-stable within 2023–2025: identified on any two years, the held-out year's G-RATE and G-STAB verdicts must not flip. | The caiso-83/86/86b lesson: an estimator that fails leave-one-year-out is not an identification. Stability, not level, is the bar — nothing here anchors to the quantity being measured. |

## 4. Conservative-default rules (bias AGAINST the C3a-favorable direction)

1. **Ambiguous spans STAY MECHANICAL (stay removed).** A span whose unit is
   unidentified (no measured heat rate, no delivered price for its fuel), cogenerating
   (any non-zero measured `steamLoad`), or unpriceable over the span returns to the
   mechanical set. This is the shipped fail-safe (`filter_merit_order_layup` keeps
   every window when the panel is `None` or the unit is absent); the session must
   verify it and MUST NOT weaken it.
2. **No partial-span splitting.** A window is reclassified whole or kept whole — no
   carving a window at the hour grain to harvest its out-of-merit hours.
3. **No subset arming.** The filtered extract applies to the whole covered class
   population or not at all (the caiso-186 §6b PRECHECK §6.4 principle: a subset
   chosen after measurement is a residual-fitted mechanism).

## 5. Kill criteria

* Any gate in §3 fails ⇒ the filtered extract is NOT adopted; nothing promoted; the
  cell is stamped from this evidence.
* Post-filter rate **below 0.07** ⇒ over-reclassification; kill (this is the
  favorable-direction overshoot, and it is a failure, not a success).
* Any LMP/price series read anywhere in the classifier path ⇒ session void.
* Any threshold chosen, changed, or re-run after any classification output or any
  solve output is seen ⇒ session void (value shopping).
* DOF ledger increase ⇒ automatic fail.

## 6. A/B protocol

* **CONTROL** — the caiso-188 keeper recipe re-solved in the session's own
  environment via `--replay-bundle results/calibration/caiso188_d1_micseam` (never a
  remembered CLI string), with the two environment conditions the integration
  protocol §3 fixes: the capacity-deliverability clean partition MATERIALIZED (verify
  the `seam import cap set to 16055/16452/16148 MW` log lines — check the DATA, not
  the flag; caiso-188 §7 item 5) and `hydro_ror_split` explicitly **False** (the
  keeper's proven-effective configuration, caiso-188 G-CTRL), the override disclosed.
  Control must meet the ratified reproduction tolerance (C3a ±0.1 pp/yr, C3b ±0.005)
  BEFORE any arm solves; the achieved deltas are quoted as the noise floor first.
* **ARM** — control + the filtered overlay extract. **ONE mechanism** (rule 19): the
  extract swap and nothing else; the full `scenario_config` diff is empty.
* Rule 16: each arm one invocation covering 2023+2024+2025; years sequential, arms
  sequential (rule 12). Both runs registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json` so C8 stays scored.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is the
  merit-order-filtered CAISO outage extract; no other input, field, or constant
  differs."

## 7. Required artifacts

* `results/calibration/PRECHECK-caiso192-overlay-identification-2026-08-12.md` (or
  the session's date) — committed and pushed BEFORE the filtered extract is built,
  restating these gates unchanged and declaring any new threshold per G-LOYO.
* Probe + record: `scripts/probes/_caiso192_overlay_identification.py`,
  `results/calibration/_caiso192_overlay_identification.json` — per-span
  classification, out-of-merit shares, per-year post-filter rates, LOYO table.
* Run bundles `caiso192_l1_control`, `caiso192_l1_overlay`.
* `results/calibration/FINDING-caiso192-overlay-identification-2026-08-12.md` with
  the gate tally, the direction-hazard clause quoted, and the matrix duty-(b) cell
  update in the same session.

## 8. Interaction disclosure (binding on wave 2)

Lane 2's granted `wefor_residual = 0.0` is arithmetically grounded in
`X_c ≥ W_c` measured on the UNFILTERED overlay. If this lane's filtered extract is
accepted, the Wave-2 composed rung must re-verify `X_c^filtered ≥ W_c` for
CC_REGULAR and CC_CHP through the frozen caiso-187 §2 formula before lane 2 composes
on top (integration protocol §5). This spec creates that obligation; it does not
license recomputing lane 2's value.
