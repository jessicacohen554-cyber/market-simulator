# PRECOMMIT — capx lane D3: attribution of MISO's T1-H `retire.total_gw` PASS→FAIL flip (the cap-grain G3 regression)

**Lane:** capx D3 (r#21), charter `docs/handoffs/capx-director-prompt-pack-2026-08.md` §D3.
**Session date:** 2026-08-31. **Branch:** `claude/miso-t1h-retire-g3-regression-i97mkq`.
**Discipline:** PRECOMMIT-FIRST — this document is pushed BEFORE any attribution
measurement. Phase 0 is ZERO-SOLVE, committed artifacts only. No mechanism, no tuning, no
solve; if attribution requires an A/B, the lane STOPS at the finding and routes it.

## 0. The object (fixed from the committed record before this precommit)

MISO's T1-H `retire.total_gw` FC-3 band row flipped PASS→FAIL between the FFR-3A-2 record
(`ff-verdicts.json` key `miso-t1h`, scored `8ba592814d92`) and the FFR-3A-3 re-measure
(key `miso-2021-2025-realized-ffr3a3-t1h`, solved `941f4983`, scored `e2a422c191aa`,
provenance: "post-FFR-3F HEAD, G3 cap-grain fix 2adfb49 in force"). The re-measure's
recorded rationale (`program-status.json` refresh note): FFR-3A-2's provenance ceiling
flagged its battery as measuring a superseded configuration because "FFR-3F's G3 cap-grain
fix (2adfb49) is unconditional and moves the admitted exit set under every T1-H finding."

**Census disclosure (honesty about what was already sighted):** locating the committed
artifacts required grepping the battery-close docs for the metric name; the grep output
surfaced the headline table rows (MISO actual 15.227 GW; FFR-3A-2 model 13.734 PASS;
FFR-3A-3 model 12.716 FAIL, −16.5 %; the doc's own label "FLIPPED BACK"), plus the same
direction of movement in NEISO (8.221→7.585) and PJM (22.415→18.862). No analysis,
decomposition, or scorer read has been performed. The candidate classes and adjudication
rule below were fixed before any of that.

## 1. Candidate driver classes (ex ante, per charter §D3)

- **(a) Scorer-grain artifact** — cap-grain target vs binned-fleet execution. The FC-3
  hindcast scorer may measure `retire.total_gw` from the capacity-evolution ledger (the
  decided/admitted exit set, unit/cap grain) while MISO's LP fleet is plant-binned and —
  per the miso-190 committed truth — per-unit retirement identity does not survive
  `fleet_to_bins`; the miso-191 keeper (backcast lane, 2026-08-31) changed exit delivery
  for exactly this reason. If so, the scorer may be measuring a fleet the LP never
  carried, and a score movement can be a movement in the *ledger*, not in anything the
  dispatch model did.
- **(b) Real retirement-volume regression arriving with the FFR-3A-3 solve** — the
  post-FFR-3F HEAD genuinely admits/executes a smaller exit volume in the 2021–2025
  hindcast window than the FFR-3A-2 HEAD did. Prime suspect within the HEAD delta: the
  G3 cap-grain fix itself (admission cap tested at the execution-year requirement —
  larger projected peak → larger requirement → more retention → fewer GW retired). Note
  ex ante: if this is the driver, the fix is the *correct* grain (FFR-3F §1.3 verified
  it against FFR-3C's synthetic); under rule 14 `[R-ACCURATE]` a worse fit under the
  accurate grain is a discovered miscalibration elsewhere, and the routed repair is a
  root-cause lane, never a revert of the fix.
- **(c) Basis/vintage misalignment** (the NEISO-RC §2.1 class) — the actual-side target,
  band definition, or actuals vintage moved between the two scorings, so the flip is on
  the measuring stick, not the model.

These are not mutually exclusive: the *flip driver* (which class moved the number across
the band edge) and the *measurement validity* (whether the number measures a fleet the LP
carried at all) are adjudicated as two separate verdicts.

## 2. Distinguishing evidence (committed artifacts only, enumerated ex ante)

- **E1 — the two scorecards:** `results/ffr3a2/scorecard/scorecard.json` vs
  `results/ffr3a3/scorecard/scorecard.json` (+ their `.txt` and the battery-close docs
  `ffr-3a2-battery-close-2026-08-03.md` / `ffr-3a3-battery-close-2026-08-04.md`).
  Extract MISO `retire.total_gw`: model value, actual, band, and any per-metric basis
  fields, for both eras.
- **E2 — the scorer's grain:** `scripts/build_ffr3a3_scorecard.py` and the hindcast
  scoring path it reads (wherever `retire.total_gw` is computed). Establish from source
  which artifact the metric is computed from — the evolution ledger (decided exits), the
  year-over-year fleet capacity delta, or the LP-carried (binned) fleet — and whether the
  scorer itself changed between the two scoring shas.
- **E3 — the HEAD delta between the two solves:** the FFR-3F handoff
  (`ffr-3f-exit-throughput-2026-08-03.md`) enumerates its two tasks (G3 cap-grain fix,
  unconditional; `exit_rate_limits`, default-off). The FFR-3A-3 battery-close doc records
  what it held fixed ("scored like-for-like with FFR-3A-2"). Establish from these
  committed records whether the G3 fix is the only solve-affecting delta for the MISO
  T1-H leg, or whether other candidates cannot be excluded.
- **E4 — mechanism signature:** the FFR-3F fix retains units at the admission cap. From
  the committed docs (FFR-3A-3's per-ISO sections, FFR-3F's own MISO evidence if any) and
  the older committed MISO realized evolution ledgers (`results/hindcast/miso-2021-2025-
  realized*/…/evolution_*.json`, earlier vintages — the FFR-3A-2/-3A-3 MISO t1h bundles
  are NOT committed, see §4), characterize whether a −1.0 GW-scale movement is consistent
  with admission-cap retention (a retention delta on the economic-exit cohort) vs
  lag/timing, entry, or announced-exit changes.
- **E5 — unit-vs-bin truth:** `FINDING-miso190-partial-plant-exit-carry-2026-08-30.md` /
  `FINDING-miso191-binning-aware-exit-2026-08-31.md` + the forecast-mode fleet-build path
  (does a ledgered exit actually leave the binned LP fleet in the hindcast solve, at what
  grain and timing?). This decides the measurement-validity verdict for class (a).

## 3. Adjudication rule (frozen ex ante)

1. **Kill (c) first:** if E1 shows the actual and band for MISO `retire.total_gw`
   identical across the two eras, class (c) is REFUTED for this flip; if they differ, (c)
   is the primary driver and the finding stops there (repair routes to the basis lane).
2. **Flip driver:** with (c) dead, the driver is the model-side movement. Attribute it to
   the G3 cap-grain fix iff BOTH: (i) E3 shows the fix is the only unexcluded
   solve-affecting delta between the two HEADs for this leg, and (ii) E4's signature is
   consistent with admission-cap retention (volume removed from the *economic* exit
   cohort, not timing/entry/announced). If (i) fails — any other delta cannot be excluded
   on committed artifacts — the attribution is INCOMPLETE: state exactly which candidates
   remain, STOP, and route the discriminating A/B (post-FFR-3F HEAD vs the same HEAD with
   the decision-year grain restored) as the director's decision. No solve in this lane.
3. **Measurement validity (independent verdict):** from E2+E5, state at which grain the
   scorer measures `retire.total_gw` and whether the binned LP fleet executed the
   ledgered exits in the hindcast window. If the scorer is ledger-grain and the LP fleet
   did not carry the exits, the row is additionally a scorer-grain artifact in the
   miso-190/191 sense, and the routed repair is R3-style dual-basis reporting (report
   ledger-grain and LP-fleet-grain retire totals side by side) — regardless of which
   class drove the flip.
4. **Verdict vocabulary:** the finding names exactly one PRIMARY driver class for the
   flip, any SECONDARY validity findings, and the routed repair. "The fix is correct and
   the band got worse" is an admissible outcome (rule 14; rule 1 — never judge a
   structurally-correct mechanism by the fit), and in that outcome the routed repair
   is the root-cause investigation, never a revert.

## 4. Kills / stop conditions (frozen ex ante)

- **K1 (evidence floor):** if neither the scorecards nor the battery-close docs carry
  per-metric model/actual/band for MISO `retire.total_gw` in both eras, STOP: record the
  attribution as blocked on uncommitted evidence and route the re-measure.
- **K2 (no solve):** any step requiring a solve, re-score, or bundle regeneration STOPS
  the lane at the finding; the A/B is routed, not run.
- **K3 (history):** the live `miso-2021-2025-realized-ffr3a3-t1h` / `miso-t1x-…ffr3a4`
  keys carry D5-R-annotated mismeasured co2 rows with bundles never committed. This lane
  works from what is committed and NAMES what is not — it never regenerates or edits
  history, and never touches the co2 rows.
- **K4 (deconfliction):** miso-193 (cc_duct_peaking, BACKCAST) is mid-A/B on
  `claude/miso-cc-duct-peaking-5ww6h1` — collision check re-run at session start, clear.
  This lane never touches miso-193's PREREG, scorer, or backcast registrations, nor any
  backcast keeper/registry surface.
- **K5 (I13 stays open):** the I13 cobweb closure on the live MISO t1f record is an
  unattributed SCORER-READ. This lane treats "why did I13 close" as OPEN, never cites it
  as a settled repair, and does not adjudicate it — it is NOT the G3 flip.

## 5. Exit contract

Finding `docs/handoffs/FINDING-capx-d3-miso-retire-g3-2026-08-31.md` with the attributed
driver class + routed repair (or the clean adjudicated "scorer-grain, repair = R3-style
dual-basis reporting"), the MISO G3 board row refreshed in
`frontend/data/forecast/program-status.json` (MISO block only — no other ISO's fields, no
verdict/gate flips), pushed blob-verified per rule 27.
