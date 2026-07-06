# G-04 — E7 keeper-staleness adjudication (2026-07-06)

**Gap:** G-04 (E7 keeper-staleness WARN, non-blocking). `scripts/audit_keepers.py --check`
raises E7 for four ISOs because a newer-dated registry run exists than the current
keeper. E7's heuristic fires on *date* alone; it does not inspect whether the newer
run is a keeper candidate or a diagnostic probe/twin.

**Scope of this memo:** decision only. No keeper was swapped, `keepers.json` was not
edited, the gap register was not edited. Swapping a keeper is an owner decision under
CLAUDE.md #1 (keeper = most structurally faithful, NOT lowest error) and #11 (a real
mechanism stays even if it worsens fit). Keeper requirements: full all-years bundle
(rule #16) + `calibration_attestation.json` + DOF ledger + zero-forcing ablation twin
(rule #24); a statmode twin / single-lever A/B / attribution twin is never a keeper by
itself (rules #1/#13).

## Swap test

A newer run supersedes the keeper only if it is **(a)** a full all-years (2023–2025)
scored bundle, **(b)** at least as structurally faithful — *more real mechanism, not a
better-fitted number*, AND **(c)** not a default-off diagnostic probe/twin, AND it
carries the keeper governance package (attestation + DOF ledger + ablation twin).
Failing (c) or the governance package = not a candidate = E7 is a construction-only
false-positive.

## Summary

| ISO | Newer run | What it is | Recommendation |
|-----|-----------|-----------|----------------|
| ERCOT | `ercot38-measured-hsl-2425` | One-delta measured-HSL probe, all years, **unattested** (no DOF/ablation) | **NEEDS-OWNER-JUDGMENT — escalate** |
| CAISO | `caiso51-statmode-v2` | D-7 statistical-mode attribution twin (all overlays off) | **KEEP** (E7 false-positive) |
| NYISO | `nyiso-54-downstate-daily` | Measured-daily-gas refinement probe, fully attested, self-adjudicated not-promoted | **KEEP** (E7 false-positive; see note) |
| NEISO | `neiso-wfuelsec-ab-v2off` | Winter-fuel A+B v2-off attribution twin | **KEEP** (E7 false-positive) |

---

## ERCOT — keeper `2026-07-06-ercot34-stage4-overlay-off` vs `ercot38-measured-hsl-2425`

**What the newer run is.** A deliberate one-delta probe of the ercot34 keeper: identical
recipe, the *only* change is `renewables.hsl_potential_mw` now resolving the **real
2024/2025 ERCOT NP4-732/737 HSL parquets** in place of the prior G7
reference-curtailment-rate gross-up fallback (registry definition; `run_config.json`).
Covers all three years (2023/2024/2025).

**All-years vs probe.** All years — but the run **self-declares "NOT a keeper swap …
(PROBE)"** and, critically, ships **no keeper governance package**: the bundle
`results/calibration/ercot38_measured_hsl_2425/` contains only
`legitimacy_diagnostics.json`, `meta.json`, `metrics.json`, `run_config.json` and the two
parquets — **no `calibration_attestation.json`, no DOF ledger, no ablation twin** (rule
#24 keeper requirements are absent; Governance shows UNATTESTED). The keeper, by
contrast, carries `calibration_attestation.json` + a 12-entry DOF ledger + a linked
zero-forcing ablation twin (`2026-07-06-ercot34-stage4-overlay-off-ablation`).

**Structural-faithfulness comparison.** The delta is in the rule-#10 *direction*:
measured HSL is a strictly more-measured physical input than the curtailment-rate
gross-up fallback it replaces, and it would regenerate for a forward year. The fit
movement is **mixed, not a clean improvement**: C3a mean-LMP CAVEAT→PASS (2025
commercial-band miss +8.2% resolved) and C5c storage-shape CAVEAT→PASS (2024 r=0.422
resolved), but **C2 system volume CAVEAT→FAIL** (2025 gas −5.0%→−6.4%, out of band —
measured HSL dispatches slightly more wind/solar, displacing gas). C3b/C3c price-shape
and tail stay FAIL (pre-existing structural misses, untouched).

**Recommendation — NEEDS-OWNER-JUDGMENT (escalate).** This is the one newer run that is
not merely a twin: it introduces a genuinely more-measured input (rule #10) with two
resolved caveats. It **cannot be swapped as-is** — it fails the swap test on the
governance package (no attestation / DOF ledger / ablation twin) and its fit is a wash
(one caveat regresses to FAIL). The correct disposition is an **owner decision to
commission a full, attested keeper re-run on measured HSL** (with DOF ledger + ablation
twin), not an automatic swap and not silent suppression. **E7 should be escalated here,
not suppressed** — it is pointing at a real more-measured input awaiting promotion.

---

## CAISO — keeper `2026-07-06-caiso-58-v2-regate` vs `caiso51-statmode-v2`

**What the newer run is.** A D-7 **statistical-mode attribution probe**: a byte-faithful
replay of the caiso-51 recipe with **every per-hour/per-year measured overlay turned off**
(`outage_source=statistical`, `ct_deployment_overlay=False`,
`reliability_deployment_overlay=False`, `wefor_residual/groups=None`,
`coal_plant_monthly_pricing=False`). Registry definition states verbatim: **"Probe only —
not a keeper, per CLAUDE.md #1/#13."**

**All-years vs probe.** All years present, but it is a diagnostic twin by construction.
Bundle `results/calibration/caiso51_statmode_v2/` has **no `calibration_attestation.json`**
(no DOF ledger, no ablation) — fails rule #24.

**Structural-faithfulness comparison.** It is strictly **less** structurally faithful than
the keeper: it deliberately *removes* measured mechanism (the whole point of a statmode
twin is to quantify what the overlays contribute). The keeper (caiso-58) is an
owner-promoted baseline carrying the drag mechanism + `use_plant_emission_rates_v2` +
`calibration_attestation.json`.

**Recommendation — KEEP.** Fails swap-test (c) outright: it is a default-off attribution
twin, and less faithful by design. **E7 is a false-positive here** — it fires only because
the twin carries a newer date. Suppress as a known E7 construction artifact.

---

## NYISO — keeper `2026-07-06-nyiso-53-li-tsl` vs `nyiso-54-downstate-daily`

**What the newer run is.** An L-11 follow-up to the nyiso-53 keeper: the downstate
CT-peaker gas re-grounded on the **measured DAILY delivered index** (`nyiso_downstate_ct_gas_daily`:
Transco Z6 NY daily spot + monthly LDC premium) replacing the monthly-premium adder,
**zero new free parameters**. Keeps `nyiso_li_lcr_tsl` + `use_plant_emission_rates_v2`.
Registry definition prefixes **"(PROBE / CANDIDATE — keeper stays
2026-07-06-nyiso-53-li-tsl)."**

**All-years vs probe.** All years, and notably it is the **only** newer run of the four
carrying a full governance package — `results/calibration/nyiso54_downstate_daily/` has
`calibration_attestation.json`, `legitimacy_diagnostics.md`, and a linked ablation twin
(`2026-07-06-nyiso-54-downstate-daily-ablation`). So it is a *complete* bundle, not a bare
probe.

**Structural-faithfulness comparison.** Strictly more-measured delivered-fuel physics
(daily vs monthly grounding — rule #10 direction, zero new params). But the author already
ran the proper head-to-head vs nyiso-53 and it is **not ≥ the keeper**: C1 PASS=PASS; C3a
−9.1/−10.7/−10.4% vs −9.0/−10.9/−10.6% (wash); C3b 0.185/0.222/0.181 vs 0.182/0.221/0.190
(wash); **C8 ST_GAS forced share marginally worse** (64.8/75.9/59.7% vs 60.8/69.8/59.7%).
Per rule #1, a structurally-faithful refinement that does not move the residual is kept
**as a default-off datatype, not promoted** — the daily gas signal is masked by the #1344
reserve-scarcity commitment frontier (data-blocked) and the PR-#1442 temperature floors.

**Recommendation — KEEP (with note).** The author correctly self-adjudicated this as a
non-promoted candidate: same structure as the keeper plus a default-off more-measured
datatype, a wash on fit, marginally worse on C8. It does not clear the swap test
(structural-faithfulness parity, not superiority, and it is a default-off datatype).
**E7 is a false-positive.** *Note for owner:* this is the closest of the four to a real
candidate (only one with full governance and a strictly-more-measured input), so if the
owner wishes to honor rule #10 by turning the daily-gas datatype on in the keeper despite
a wash fit, that is a legitimate owner call — but it is optional, not indicated by the fit,
and lower priority than the ERCOT measured-HSL question.

---

## NEISO — keeper `2026-07-06-neiso-50-head-repro` vs `neiso-wfuelsec-ab-v2off`

**What the newer run is.** A **v2-off attribution twin** of the winter-fuel A+B probe:
Winter-fuel Component A + Component B enabled with `use_plant_emission_rates_v2` **OFF**,
run to isolate the winter-fuel mechanism from the v2 flip (emissions-co2-rate-plan §9.6).
Registry definition: **"(PROBE, v2-OFF ATTRIBUTION TWIN …) … keeper stays neiso-48."**

**All-years vs probe.** All years nominally, but it is the barest of the four:
`results/calibration/neiso_wfuelsec_ab_v2off/` has **no `calibration_attestation.json`
and no `metrics.json`** — only `legitimacy_diagnostics.{json,md}`, `meta.json`,
`run_config.json`. It is an attribution twin, not a scored keeper candidate.

**Structural-faithfulness comparison.** Its stated result is that it is **byte-identical
to the v2-on probe** on price, fuel mix, storage, and CO2 — i.e. it exists to *prove
`use_plant_emission_rates_v2` is dispatch-inert for the NEISO backcast*, not to advance
the fit. It does not add mechanism over the keeper; it removes/holds one to attribute an
effect. The keeper (neiso-50-head-repro) is a byte-reproducible re-solve carrying
`calibration_attestation.json` + a solved/linked ablation twin (E9-clearing).

**Recommendation — KEEP.** Fails swap-test (c) plainly: a default-off attribution twin
with no metrics and no attestation. **E7 is a false-positive** — newer date only. Suppress
as a known E7 construction artifact.

---

## Closing note

- **Genuine owner swap/promotion question — ERCOT only.** `ercot38-measured-hsl-2425`
  introduces a real more-measured input (measured NP4-732/737 HSL, rule #10) and resolves
  two caveats, but is an unattested probe with a mixed fit (C2 regresses). It cannot be
  auto-swapped; the owner should decide whether to **commission a full attested keeper
  re-run on measured HSL**. Escalate G-04/ERCOT to the owner. Keep E7 live for ERCOT until
  that decision.
- **E7 false-positives — CAISO, NYISO, NEISO.** All three newer runs are diagnostic
  twins/probes by construction — a statmode attribution twin (CAISO), a self-adjudicated
  not-promoted default-off datatype refinement (NYISO), and a v2-off attribution twin
  (NEISO). None clears the swap test; two carry no attestation at all. E7 fires only
  because a newer-*dated* non-keeper run exists. These may be suppressed as known E7
  construction artifacts. **NYISO carries a secondary, optional owner note** (rule-#10
  daily-gas datatype), lower priority than ERCOT.
- No keepers were changed; no `keepers.json`, gap-register, or dashboard edits were made.
