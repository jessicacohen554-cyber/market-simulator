# PRECHECK — caiso-192 (lane 1): CAMPD outage-overlay mechanical-vs-economic identification

**Committed and pushed BEFORE the filtered extract is built and before any classification
output exists** (GATESPEC §7, rule 27 `[R-PUSH]` ordering discipline). Nothing in this
document is this session's choice: every gate below is transcribed **unchanged** from
`GATESPEC-caiso192-overlay-identification-2026-08-11.md`, authored by caiso-191 before any
lane-1 measurement existed. This session **may not amend, re-anchor, or re-scope** them and
does not.

Authorization: owner ruling 1 (`caiso191-owner-rulings-2026-08-11.md`) — caiso-187 option 1,
GRANTED. Rule 28 duty (a): the CAISO lever queue is **EMPTY and CLOSED**; this is chartered
campaign work under a closed lane inventory, **not a new lever**.

Keeper at session open: **`2026-08-09-caiso-188-d1-micseam`** (NOT-YET). Untouched by this
document.

---

## 0. Direction-hazard regime (transcribed verbatim from GATESPEC §0, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

The favorable error direction is concrete: reclassifying an outage span as economic layup
DROPS it from the overlay and RESTORES capability, which lowers price. Every ambiguity rule
below therefore resolves the other way.

---

## 1. What is being separated, and with what

The CAMPD-derived CAISO outage overlay's detector identifies **downtime**, not **mechanical
unavailability** (FINDING-caiso187 §3). This lane separates the two for the CAISO gas classes
the overlay carries — **CC_REGULAR and CC_CHP** — using the machinery already shipped for
exactly this question:

* `scripts/lib/outage_detect.py::build_merit_order_panel`
* `scripts/lib/outage_detect.py::filter_merit_order_layup`
* driven through the shipped CLI flag `scripts/data/derive_campd_unit_outages.py
  --merit-order-guard`

caiso-181's zero-interior-contradiction result stands untouched: it proved the units were
down; this lane classifies **why**.

Rule 23 `[R-FROZEN-DERIVE]` recital: this re-derivation is licensed by a **defect in the
measured input's own classification**, measured by caiso-187 and granted by the owner — **not
by a residual move**. The commit message cites caiso-187 §3 and ruling 1 as the cause.

---

## 2. Exogenous instrument closure (GATESPEC §2, unchanged)

The classifier and every gate statistic may touch ONLY:

* CAMPD unit-level operation (`grossLoad`, `heatInput`, `steamLoad`, `primaryFuelInfo`) —
  the committed `data/raw/campd-unit-level/` parquets;
* delivered fuel prices — the F923 delivered-coal ladder and the ISO delivered gas hub series;
* EIA-860 fleet identity (unit/plant capacities, class membership);
* EIA-930 CISO net load — for the seasonality DIAGNOSTIC only, never in the classifier
  decision itself.

**FORBIDDEN anywhere in any classifier or derivation: every LMP/price series** — DA/RT/hub/
OASIS LMPs, model duals, any scored residual, any benchmark. **Any price read voids the
session.**

---

## 3. The numeric gates (GATESPEC §3, transcribed unchanged)

| gate | bar |
|---|---|
| **G-RATE** | Post-filter CC_REGULAR mechanical-removal rate, measured through the SHIPPED loader (`outages.unit_outage_derate_factors`, the caiso-187 §2 `X_c` basis), within **[0.07, 0.15]** in EACH of 2023 / 2024 / 2025. |
| **G-STAB** | Post-filter year-over-year change ≤ **3 pp** (absolute rate), **and** post-filter 2025 rate ≤ **1.5 ×** post-filter 2023 rate. |
| **G-SEP** | (a) capacity-weighted mean out-of-merit share of RECLASSIFIED (layup) span-hours ≥ **0.80**; (b) separation vs RETAINED (mechanical) spans' mean out-of-merit share ≥ **30 pp**; (c) the reclassified span-hours' Mar–May share strictly exceeds the retained spans' Mar–May share. |
| **G-LOYO** | The shipped frozen constants (`MERIT_RCC_PCTL = 0.90`, `MERIT_OOM_FRAC = 0.90`, `REAL_RUN_CF`, `MIN_REAL_RUN_HOURS`, `MERIT_HR_MIN/MAX`) are used **AS SHIPPED**. Any new threshold must be (i) committed in this PRECHECK before any classification output exists and (ii) LOYO-stable within 2023–2025. |

**G-LOYO DECLARATION — this session introduces NO new threshold and NO new parameter.** The
guard runs on its shipped constants at their shipped values, driven by the shipped CLI flag
at its default `--merit-oom-frac` / `--merit-rcc-pctl`. Nothing is swept, tuned, or chosen.
G-LOYO is therefore satisfied by construction, with **no free parameter to hold out** — and
the DOF ledger cannot rise (GATESPEC §5: a DOF ledger increase is an automatic fail).

---

## 4. Conservative-default rules (GATESPEC §4, unchanged — bias AGAINST the C3a-favorable direction)

1. **Ambiguous spans STAY MECHANICAL (stay removed).** A span whose unit is unidentified (no
   measured heat rate, no delivered price for its fuel), cogenerating (any non-zero measured
   `steamLoad`), or unpriceable over the span returns to the mechanical set. This is the
   shipped fail-safe (`filter_merit_order_layup` keeps every window when the panel is `None`
   or the unit is absent; `MeritOrderPanel.is_economic_layup` returns `False` on an
   unidentified unit or unpriceable span). **This session verifies it and does not weaken
   it.**
2. **No partial-span splitting.** A window is reclassified whole or kept whole.
3. **No subset arming.** The filtered extract applies to the whole covered class population
   or not at all.

*Declared consequence of rule 1, stated in advance so it cannot later read as a surprise:*
the shipped panel **excludes every cogenerating unit** (`if steam.any(): continue`), so
**CC_CHP windows are expected to be retained wholesale as mechanical**. That is the fail-safe
operating as designed, not an under-fire to be repaired, and this session will not touch it.

---

## 5. Kill criteria (GATESPEC §5, unchanged)

* Any gate in §3 fails ⇒ the filtered extract is **NOT adopted**; nothing promoted; the
  matrix cell is stamped from this evidence.
* Post-filter rate **below 0.07** ⇒ over-reclassification; **kill** (this is the
  favorable-direction overshoot, and it is a **failure**, not a success).
* Any LMP/price series read anywhere in the classifier path ⇒ **session void**.
* Any threshold chosen, changed, or re-run after any classification output or any solve
  output is seen ⇒ **session void** (value shopping).
* DOF ledger increase ⇒ automatic fail.

**Kill before solve is honorable.** If the gates fail, the outcome is the recorded rejection
— never an improvised variant. The lane inventory is CLOSED.

---

## 6. A/B protocol (GATESPEC §6, unchanged)

* **CONTROL** — `--replay-bundle results/calibration/caiso188_d1_micseam` (never a remembered
  CLI string), with the two environment conditions the integration protocol §3 fixes:
  the capacity-deliverability clean partition **MATERIALIZED** (verified by the
  `seam import cap set to 16055 / 16452 / 16148 MW` log lines — **check the DATA, not the
  flag**) and `hydro_ror_split` explicitly **False**, the override disclosed.
  Control must meet the **ratified reproduction tolerance — per year |ΔC3a| ≤ 0.1 pp and
  |ΔC3b| ≤ 0.005** — BEFORE any arm solves, and the achieved deltas are quoted as the
  **noise floor first**. A control outside tolerance is a stop-the-line finding about the
  head: no arm solves, escalate.
* **ARM** — control + the filtered overlay extract. **ONE mechanism** (rule 19): the extract
  swap and nothing else; the full `scenario_config` diff is empty.
* Rule 16: each arm one invocation covering **2023 + 2024 + 2025**; years sequential, arms
  sequential (rule 12). Both runs registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`; the attestation must pass `audit_keepers` E10.
* Required verbatim in the FINDING: *"The A/B delta is the merit-order-filtered CAISO outage
  extract; no other input, field, or constant differs."*

---

## 7. Order of operations this session is bound to

1. **This PRECHECK committed and pushed** — before the filtered extract is built. ✅ (this commit)
2. Build the filtered extract + measure the identification
   (`scripts/probes/_caiso192_overlay_identification.py` →
   `results/calibration/_caiso192_overlay_identification.json`).
3. Evaluate G-RATE / G-STAB / G-SEP / G-LOYO and the §4 conservative defaults. **Any gate
   fails ⇒ no adoption, no solve.**
4. **Only on a full pass**, solve CONTROL then ARM.

## 8. Holdout

**2023–2025 ONLY** (rule 22). CAISO holds no `complete` marker and no `final` marker; both
are owner acts and are **untouched** by this session. No out-of-training year is solved,
scored, or registered.

## 9. Interaction disclosure carried forward (GATESPEC §8)

If this lane's filtered extract is accepted, the Wave-2 composed rung must re-verify
`X_c^filtered ≥ W_c` for CC_REGULAR and CC_CHP through the frozen caiso-187 §2 formula before
lane 2 composes on top (integration protocol §5). This PRECHECK records that obligation; it
does not license recomputing lane 2's value.
