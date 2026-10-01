# PRECOMMIT — pjm-d4-4: the forced-outage composition gap, stage-0 kill gate

**Session:** pjm-d4-4 · **Date:** 2026-09-10 · **Branch:** `claude/pjm-forced-outage-gap-o0kzlz`
**Scope:** PJM only. **LP spent at the time of writing: ZERO, and none is authorised by this
document.** This file registers the stage-0 kill bar *before* the measurement that tests it, so the
bar cannot be written to fit the result (rule 29 `[R-SCREEN]` clause 0).

Predecessors: `docs/handoffs/pjm-d4-4-missing-price-tail-2026-09-10.md` (the card),
`docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md` (the price-side measurement),
`results/calibration/FINDING-pjm162-outage-envelope-basis-closure-2026-08-15.md` §3–§5,
`docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md` §6.

---

## §1 — the proposition under test

The card's thesis, in one line: **2022's C3a failure is a missing RT price tail, the reserve
co-optimisation that should form it is inert, and the reason is that the model's outage envelope is
the wrong SHAPE — 5.8–7.0 % forced-like against PJM's published 23.0–29.4 %.** The proposed arm is to
extend the sub-5-day short-window outage overlay (`unit_outage_short_windows`, armed in the keeper)
from its coal-only scope to the gas classes, recovering the 0–3 d stratum that
`UNIT_OUTAGE_MIN_DAYS = 5` discards for CC_REGULAR / CT_PEAKER / ST_GAS / the CHP classes.

**The arm is not proposed here and no field is added by this document.** What is registered here is
the bar that decides whether it is ever built.

## §2 — the duration boundary is DATA-IDENTIFIED, not swept (rule 21 `[R-DOF]`)

pjm-162 §4 declined this route partly because "any specific [duration] cut is a **free parameter**",
having swept the CUMULATIVE family and found corr positive across 2–10 days with no optimum. **The
PER-STRATUM sign is a different statistic and it is categorical.** From the committed
`results/calibration/_pjm162_split_derivability.json`, `corr_vs_published_FORCED`:

| stratum | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| 0–3 d   | **+0.164** | **+0.234** | **+0.398** | **+0.222** |
| 3–7 d   | **+0.321** | **+0.126** | **+0.221** | **+0.089** |
| 7–21 d  | −0.213 | −0.035 | −0.087 | −0.477 |
| 21–60 d | −0.654 | −0.226 | −0.563 | −0.468 |
| > 60 d  | −0.704 | −0.211 | −0.647 | −0.435 |

**The sign flips at exactly 7 days in all four years — 8 positive cells, 12 negative, zero
exceptions.** No value was chosen to make a criterion pass, and the classification is invariant to
any cut placed inside a stratum. **This boundary is NOT re-swept in this session**, and the
mechanism's own floor (`UNIT_OUTAGE_MIN_DAYS = 5`) sits inside the positive region on either side of
the 3 d/7 d strata boundaries, so nothing about the sign flip is sensitive to it.

## §3 — THE KILL BAR, registered before the measurement

The measurement (stage 0, zero LP) is: run the existing frozen detector in `--short-windows` mode
with its **coal-only scope widened to the gas classes**, for PJM, and measure the recovered family's
removed-availability MW. Two numbers decide the card.

**G-KILL-1 (PRIMARY — tail-hour capability).**
> Recovered gas sub-5-day family, mean removed-availability MW over **2022's 92 actual RT > $200
> hours**, must be **≥ 2,425 MW**.

*Identification of the bar:* 2,425 MW is **one quarter of the +9.7 GW** model-minus-meter thermal
over-dispatch measured in exactly those 92 hours (ADDENDUM §3). The card's thesis is that this
composition gap **IS** the missing tail. Rule 19 `[R-ONE-MECH]` is one mechanism per phenomenon: a
mechanism that delivers less than a quarter of the defect it is proposed to close is not the
mechanism for that phenomenon, and closing the remainder would require stacking three or more
further mechanisms, which rule 19 refuses. One quarter is deliberately **generous** — it admits the
arm even if it is only a plurality carrier rather than the dominant one.

**G-KILL-2 (SUPPORTING — composition ratio).**
> Recovered gas sub-5-day family, **annual-mean MW in 2022**, must be **≥ 700 MW**.

*Identification of the bar:* 700 MW is **10 % of 2022's +6,999 MW forced gap** (handoff table:
model 2,333 MW forced-like ≤7 d against PJM published FORCED 9,332 MW). At 700 MW the model's
forced-like share moves 6.8 % → 7.5 % against a published 26.6 %; below it the composition ratio the
card is built on is qualitatively unchanged, and the repair does not repair the thing it names.

**DISPOSITION RULE, registered now.** The arm proceeds to stage 1 (build) **only if BOTH clear**. If
**G-KILL-1 fails the arm is DEAD** and that is the session's result — no stage-1 build, no screen
shard, no full span. A pass on one and a failure on the other is reported as such and put to the
owner; it does not authorise a solve on its own.

**The measurement is an UPPER BOUND, and this asymmetry is registered too.** The gas leg is run with
**no gas-specific identification guard beyond the frozen revealed-availability in-merit filter** —
in particular the coal `SHORT_BASELOAD_CF ≥ 0.55` baseload guard is *not* applied to gas, because it
is a coal guard and gas cyclers fail it by design. So:
* a **FAILURE is conclusive** — no admissible gas guard can recover *more* than the unguarded
  family, so a bound below the bar kills the arm for every guard I might have chosen; and
* a **PASS is not a promotion** — it would still owe the ex-ante gas identification guard that
  stage 1 must derive from gas conduct before any solve (the handoff's "HARD PART").

A second, strictly-larger ceiling (**in-merit filter OFF**) is reported alongside it purely to bound
how much of any shortfall could conceivably be recovered by loosening identification. It is a
diagnostic ceiling and **is not eligible to clear either bar** — clearing a gate by disabling the
economic-idling filter would be exactly the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids.

**What is NOT gated, in either direction:** C3a, C3b, C1 and every other criterion. No price residual
appears in either bar. Both bars are stated in MW of availability against MW of measured defect.

## §4 — the identification objection that is already on the record, engaged before the measurement

ERCOT's lane struck a near-neighbour of this arm from its own queue
(`docs/calibration-log/ercot.md`, the `--short-windows` 2×2 adjudication), verbatim: the short mode
admits only `SHORT_BASELOAD_CF ≥ 0.55` units *"because a cycling unit's brief stop can be economic
dispatch while a baseload unit's 1-5 day full stop … is a forced event"*, and *"the only signal
separating a 2-day lay-up from 2-day cycling in a low-duty-cycle unit is the unit's own metered
on/off state, and consuming that hour-by-hour is rule 13 `[R-MEASURED]` pinning."*

Rule 28(d) means that verdict is **ERCOT's and does not fill PJM's cell** — but the *reasoning*
transfers as reasoning, and it is the strongest objection this arm faces. It is registered here, in
advance, as a **stage-1 blocker independent of the kill gate**: even a family that clears both bars
must show an ex-ante gas identification guard that separates a forced stop from a cycling stop
without reading the unit's metered on/off state as the answer. The one asymmetry in PJM's favour,
also registered in advance: the ≥5-day gas extract *already* uses the event-based dead-span detector
(`detect_outages_eventbased` at `ST_GAS_CF_PEAK`) rather than the coal sustained-gap rule, and that
detector is already accepted in the keeper at ≥5 days — so the open question is the **duration**, not
the detector.

## §5 — rule compliance registered in advance

* **Rule 32 `[R-SHARD]`:** the parent never solves. Stage 0 is a derive, not an LP. No shard is
  launched by this document.
* **Rule 31 `[R-RETAIN]`:** `results/calibration/pjm_d4_*/` is already gitignored (`.gitignore`
  line 1757), so this session's bundle family is out of `main` by construction and nothing is ever
  `rm`'d to discharge rule 29(c).
* **Rule 29(b) G-DRIFT:** not owed at stage 0 (no solve, no control). It is owed before any screen
  shard, from `pjm_d4_2_TP.meta.git_sha` = `5f133fd5`.
* **Rule 30(c):** PJM's training span reads CALIBRATED on keeper `2026-09-10-pjm-d4-2-stgas` and is
  not touched by anything in this session.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the derive is re-run because its **scope** was wrong (coal-only),
  a construction repair — not because a residual moved. The instrument's default path is verified
  byte-identical before any widened run (§6).
* **Rules 21/24/28:** no `ScenarioConfig` field, no matrix row and no cache-key entry is added by
  stage 0. They are stage-1 deliverables and are owed in the same commit as the field, if there is
  one.

## §6 — the instrument, and its inertness check

`scripts/data/derive_campd_unit_outages.py` gains `--short-window-groups {coal,gas,gas_cc,all}`,
default `coal`. Non-coal units admitted by it are detected with the **event-based dead-span rule**
(never the coal sustained-gap rule) and are not subject to `SHORT_BASELOAD_CF`; the
revealed-availability in-merit filter still applies. `--partial-windows` stays coal-only.

**Inertness verified before the widened run:** `--iso PJM --short-windows --years 2022` at the
default produces a file **byte-identical** to the same command on the unpatched script
(`diff` clean, 136 rows). Against the committed `campd-unit-outages-short-PJM.csv` the same command
reproduces 133 of 134 committed 2022 rows and adds 3 (a CAMPD source-vintage drift, +3/−1 of 134);
the coal control for every comparison below is **my own re-derive**, not the committed file, so the
drift cancels.

**If the gate fails, this instrument is REVERTED and not committed** — rule 26 `[R-DELETE]`: a
measurement knob left in the tree with no consumer is a re-armable answer key.

## §7 — the successor, named before the result so it is not invented afterwards

If the family is immaterial, the card's own named successor stands and is handed on rather than
guessed at: PJM's published forced outage may be largely **PARTIAL derates** — a unit on a forced
derate still generates — which a **stop-detector cannot see at any duration**. pjm-162 measured a
model PARTIAL block of 14,653 MW against a HARD-ZERO block of 27,009 MW. That is a different
detector, not a different threshold, and PJM's matrix carries
`ercot_partial_outage_shaped_derate` at `·` (n/a) — an unbuilt cell, not a refused one.
