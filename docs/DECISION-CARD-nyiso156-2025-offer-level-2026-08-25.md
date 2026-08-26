# DECISION CARD — nyiso-156: the 2025 offer-level object, measured to completion on the hydro-repair keeper

**Filed:** 2026-08-25, session nyiso-156. **Decision owner:** the model owner.
**Nothing is armed, changed or promoted by this card.** The NYISO keeper
remains `2026-08-25-nyiso-155-hydro-repair` (determination **NOT-YET**, written
explicitly on owner instruction; failing C3a-2025 −10.8 % and, via the
silenced lone-failure guard, C3c).

This card **supersedes the numbers** of
`docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md` (filed
against the pre-CHP, pre-hydro-repair keeper); the questions it put to the
owner are restated here against what is now measured. Evidence:
`results/calibration/_nyiso156_offer_level_phase0.json` (probe
`scripts/probes/_nyiso156_offer_level_phase0.py`, declared in
`PRECOMMIT-nyiso156-offer-level-phase0-2026-08-25.md` before measurement; no
solve — everything is read from the two registered nyiso-155 bundles, a
same-HEAD pair, so arm−control is exactly the hydro repair).

---

## 1. WHAT THE OWNER IS BEING ASKED

**Q1 (restated).** The nyiso-148 card asked "charter the 2025 offer-level
object as its own NYISO lane?" That framing is now **overtaken by
measurement**: the object is fully decomposed into components that each sit in
a terminal state for a lane, and **no lane lever now known can move it**
(§4). The live decision is:

> **Authorize the winter locational identification intake (the BLOCKER-B
> class), or leave the keeper standing NOT-YET?** *(Options and
> recommendation: §5.)*

**Q2 (dissolved).** The nyiso-148 card asked whether to annotate the then-
keeper's C3a-2025 −2.2 % PASS as cancellation-held. That number no longer
exists: the promoted keeper reads the 2025 miss at full magnitude (−10.8 %
FAIL) and the Calibration Status page says NOT-YET. There is nothing left to
annotate; no decision is requested.

## 2. THE MEASUREMENT — the 2025 lw gap, decomposed on the keeper

C3a gates on the **load-weighted** RT mean: actual 66.43, model 59.24,
gap **−$7.19/MWh (−10.8 %)**. The monthly decomposition below is on the
demand-weighted hub construction, which reproduces the scorer's annual
numbers to $0.24 (anchors: model side exact at 61.04/59.24; committed actual
lw reproduced to $0.09 in 2025, $0.01 in 2024, $0.20 in 2023 — a demand-series
construction difference reported per the precommit, immaterial to every 2025
number here).

**Contributions to the annual 2025 lw gap (keeper arm; $/MWh of the annual
mean):**

| component | contribution | detail |
|---|---|---|
| **Winter face: Jan + Feb** | **−3.92** | whole-month, sustained: Jan model 89.07 vs actual 111.20 lw; Feb 76.66 vs 99.40. Dec is now small (−0.27; 95.17 vs 98.12) |
| **Summer face: ten scarcity-event days** | **−3.94** | Jun 22–26 (120 h): model **86.89 vs actual 214.25** lw, −2.42 of the annual mean; Jul 1/25/28–30 (120 h): **80.47 vs 159.71**, −1.53 |
| Non-event summer hours | ~+0.1 | the rest of Jun/Jul slightly over-prices (whole-month Jun+Jul −3.83 < events −3.94) |
| Rest of year (Mar–May, Aug–Nov) | **+0.59** | systematic mild over-pricing (May +4.05/MWh monthly, Aug +2.58, Sep +2.10) |
| **Total** | **−7.43** | vs scorer −7.19 (construction diff $0.24) |

**Both faces pre-exist the hydro repair** (control: Jan+Feb −3.49, events
−3.87, rest-of-year +1.37, total −5.64). **The repair created no new
component**: its −$1.79 spreads across all twelve months (monthly price delta
−0.89 to −2.85 $/MWh; monthly gap contribution −0.04 to −0.27) — it uniformly
removed the phantom-scarcity over-price that was masking the two faces'
full magnitude, exactly as `FINDING-nyiso-hydro-truncation-repair-2026-08.md`
§4.4 inferred. The restored 3.01 TWh lands in every month (+0.09 to +0.40
TWh/month).

**The zonal signature is unchanged and confirms the standing typing:** the
model's 2025 annual gradient is $0.81 (control $0.74) vs actual $14.83;
Upstate_West is **+1.0 %** while the four downstate zones carry the whole
miss (CH −11.6, LH −11.2, NYC −16.0, LI −19.1 %). In the winter months the
model is flat statewide with upstate nearly exact (Jan: UW 87 vs 90 actual;
NYC 87 vs **134**; LI 88 vs **131**) — the miss is entirely the downstate
premium, precisely the object nyiso-150 proved locational at the LP.

**The load-conditional profile (new):** model−actual hub error by
system-demand decile is monotone in **all three years** — 2025: +6.9 $/MWh
(lowest decile) → **−33.7** (highest), with the top two deciles contributing
−7.10 of the −7.19; 2023: +6.8 → −5.2; 2024: +4.9 → −6.8. The equal-hour
2024 hub gap is −$0.03 — essentially exact — while its lw gap is −$0.66. The
model's price–load curve is systematically too flat everywhere; 2023/2024
pass because the over-priced troughs cancel the under-priced peaks in the
annual mean, and dear-gas 2025 is where the high-load half grows past what
cancellation can hide. **This is a characterization, not a new mechanism
claim**: the high-load under-pricing in 2025 *is* the two faces above (both
are high-load phenomena); the low-load over-pricing is real, small in lw
terms, and any "repair" of it would *widen* C3a-2025 — it is recorded, not
actionable on this criterion.

## 3. WHAT THE OBJECT IS — final typing

Every dollar of the C3a-2025 miss now attributes to an **already-adjudicated
object**; there is no third component and no unexplained remainder:

1. **The winter downstate premium (−3.9)** — PROVEN LOCATIONAL by solve
   (nyiso-150 §2.2: an $8–13/MMBtu measured zonal gas spread yields < $1 of
   price spread; the mainland prices as one coupled block). Every lane route
   is adjudicated: fuel-side REFUTED-AS-ARMED, the `SCH - PJ - NY` seam split
   UNIDENTIFIABLE from public data (rule-20 refusal, standing), interface
   tightening REFUTED by the as-enforced limits, the CE TTC accurate as
   carried. **Blocked on identification — the BLOCKER-B intake class**: the
   sub-zonal in-city formation parameters are MyNYISO-walled (as-enforced
   AORR; the public Appendix B carries no derivable NYC parameter).
2. **The summer scarcity events (−3.9)** — the **ledgered C3c face seen in
   the mean**: ten days whose event-hour lw under-pricing ($127 and $79/MWh
   during the windows) is the same scarcity-formation limitation the owner
   ledgered under the rule-22 standing rule (the model makes 1/0/0 h > $300
   vs 10/13/42 actual). The C3c queue is CLOSED; nothing here re-opens it.
3. **A small shoulder over-pricing (+0.6)** that partially offsets — real,
   recorded, not a C3a remedy in any admissible direction.

## 4. THE DECISIVE NEW FACT — either face alone restores the band

The ±10 % band edge for 2025 is −$6.64. The faces are ~$3.9 each:

* Winter face closed, summer untouched: −7.43 + 3.92 → **≈ −5.3 % — IN
  BAND.**
* Summer events closed, winter untouched: −7.43 + 3.94 → **≈ −5.3 % — IN
  BAND.**

And with C3a-2025 in band, C3c reverts to the **lone** failing criterion and
the rule-22 standing rule reclassifies it to its ledgered CAVEAT — the
determination returns **CALIBRATED** (subject to scoring, guards unchanged).
The object does **not** require both faces closed; each remains a real,
reported defect regardless.

Consequently the nyiso-148 recommendation "charter it as a lane" has nothing
left to charter: the summer face is ledgered model-class (its queue closed by
owner rule), the winter face is blocked on access-walled data (not on ideas
or effort), the offer-side queue was closed at nyiso-151 (two levers proven
bit-insensitive), and rules 13/21 forbid every shortcut that remains (a
fitted adder or rescale tuned to this residual is the exact thing
`[R-MEASURED]` bans). **The only path that moves C3a-2025 through structure
is new data.**

## 5. Q1 — OPTIONS

| # | option | what it costs | what it buys |
|---|---|---|---|
| **A** | **Authorize the winter locational identification intake** (BLOCKER-B: MyNYISO-grade access to the as-enforced sub-zonal in-city commitment/AORR parameters, and/or a source that splits the Capital_Hudson seam leg) *(RECOMMENDED)* | an owner-funded/authorized data intake; then one ordinary lane A/B under its own prereg | the ONLY structural route to the winter face (−3.9); measured expectation per §4: winter face closure alone returns C3a-2025 to ≈ −5.3 % and the determination to CALIBRATED, with the summer face still honestly reported inside the ledgered C3c caveat |
| B | **Leave the keeper standing NOT-YET** | nothing now; the determination stays NOT-YET indefinitely (both faces are terminal for a lane) | fully honest state (rule 1): the miss is reported at full magnitude; the lane works the remaining non-C3a queue (owner rulings, hygiene items) |
| C | Extend the C3c ledger to cover its C3a-mean shadow (rubric change: let the summer face's contribution to the annual mean read as the same ledgered limitation) | **NOT RECOMMENDED**: C3a is load-bearing tier, and the v3.0 guard restricting model-class classification to supporting-tier criteria is one of the rubric's core protections; breaching it for a load-bearing criterion is a governance cost far exceeding the benefit, and §4 shows the same determination is reachable through structure (option A) | avoids the intake; reads CALIBRATED without new data |

**Why A.** It is the only option that closes a face with structure rather
than accounting. The intake question is precisely typed (nyiso-97/122/150
record exactly which parameters are walled and why the public postings
cannot substitute), the downstream lane work is ordinary and pre-registrable,
and §4 gives the owner a measured, falsifiable expectation for what the
intake buys before spending anything on it. B is the honest default if the
intake is not worth its cost now; the card only asks that the choice be
explicit, because until one of A/B is taken the NYISO lane has no
determination-bearing work available.

## 6. WHAT THIS CARD DOES NOT ASK FOR

* **No holdout spend** — the freeze is ACTIVE; everything here is 2023–2025,
  read-only, no solve.
* **No re-arm, softening or re-tune of the hydro input pair** (rule 14): it
  is correct and stays; hydro volume statistics remain tautological by
  construction under the 930 pin and none is banked here.
* **No C3c lever** — that queue stays closed; the summer face is quantified
  here only to attribute the C3a mean.
* **No new mechanism, scalar, or ScenarioConfig field**; the matrix is
  untouched (no mechanism was tested — phase-0 measurement only).

## 7. EVIDENCE

* `results/calibration/_nyiso156_offer_level_phase0.json` — M1–M6 in full
  (lw monthly faces, eqh/lw split, demand deciles, zonal continuity, hydro
  calendar, event windows), plus every anchor check.
* `results/calibration/PRECOMMIT-nyiso156-offer-level-phase0-2026-08-25.md`
* `docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md` §4.4, §7
* `results/calibration/ASSESSMENT-nyiso150-frontier-2026-08-22.md` §1–§2, §4
* `docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`
  (superseded numbers; question genealogy)
