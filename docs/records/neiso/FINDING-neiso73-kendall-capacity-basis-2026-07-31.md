# FINDING — neiso-73: Kendall Square (EIA 1595) capacity basis — ARTIFACT, no missing capacity, NO LP spent

| | |
|---|---|
| Session | neiso-73 |
| Standing keeper | `2026-07-31-neiso-72-hy-window` (CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered C3c caveat) — **untouched** |
| Lever | Handoff Lever A (PRIMARY): NEISO CC_CHP capacity basis, the neiso-71 §1 named successor |
| Probe | `scripts/probes/_neiso73_kendall_capacity_screen.py` (reproducible, raw sources only) |
| LP / bundles / scoring | **None.** No solve, no bundle, no dashboard registration; the keeper and every criterion stand as-is |
| Years read | CAMPD MA 2018–2025 + EIA-923/EIA-860 vintages (raw-source reads, no-LP — the rule 22 posture neiso-72's probe used) |

## §1 — The question, as chartered

neiso-71 §1 blocked the CC_CHP host-steam floor on a capacity contradiction:
CAMPD facility 1595 unit "4" (unitType "Combined cycle") meters **278/299/283
MW median gross** (max 321) against an EIA-860 CHP basis of **213.4 MW
nameplate / 206.0 MW summer** (= the model pmax, `apply_cc_summer_guard`
22.9 + 183.1). Read as electrical, that is ~90 MW of missing capacity on 42 %
of NEISO's CC_CHP class. This session's charter: establish the correct basis
from primary sources and decide **EIA-860 understatement vs
co-location/attribution artifact** — *then* change one thing with a
pre-registered A/B, **iff** a change is warranted.

## §2 — Verdict: ARTIFACT. The EIA-860 basis is correct; no model change; no A/B

CAMPD `grossLoad` on this CHP unit is **not gross electrical MW** — it is a
basis that embeds the district-steam host output (Kendall serves the Cambridge
/ Vicinity Energy steam system; CAMPD units "2"/"3" at the same facility are
steam-only auxiliary boilers filing `steamLoad` with zero `grossLoad`,
confirming the site's large non-electric product). Five independent evidence
blocks, every one reproducible from the committed raw data:

| # | Evidence | Number | Implication |
|---|---|---|---|
| E1 | Physical bound | max gross **317–323 MW every year 2018–2025** vs **294.9 MW** = summed nameplate of every generator EVER installed at 1595 (incl. the retired 1949/1951 steam gens 1/2 and both DFO jets) | The channel exceeds any possible electrical reading for the site, in any era |
| E2 | Thermodynamic bound | implied gross heat rate **6.36–6.59 mmBtu/MWh** (53–54 % HHV) — beyond any 2002-vintage F-class 1×1 with a 1958 steam turbine; on the EIA-923 net basis **9.31–10.07** | "Gross" divides fuel by a number larger than the electricity made; the net-basis rate is exactly right for this cogen vintage |
| E3 | Basis stability | EIA-923-net / CAMPD-gross = **0.654–0.687 across 96 months × 8 years**, flat through the 2018 unit-1/2 retirement; monthly gap 60–96 avg MW | A fixed metering-basis transformation — not station use (2–5 % typical), not the post-2024 district-steam electric boiler |
| E4 | Saturation | Dec-2023 monthly avg **net 209.3 MW vs the EIA-860 winter rating 210.3 MW (99.5 %)**; repeatedly 204–209 in winter months across years | EIA-860 and EIA-923 are mutually consistent: the plant is capacity-limited at the filed rating |
| E5 | Vintage stability | EIA-860 vintages 2019–2024 identical (GEN4 186.2/183.1 + gen "3" 27.2/22.9); no uprate/derate ever filed; the 2018→2019 step is the documented units-1/2 retirement | No 860 filing drift to explain away |

**Closure on neiso-71's saturated statistic:** mean gross/net = **1.483** vs
the saturated `steam_level_cf` of **1.461** — the WP-3 statistic, computed on
the CAMPD gross numerator, was measuring the *basis ratio itself*, not a steam
obligation. neiso-71's diagnosis ("broken denominator — the nameplate") is
hereby corrected to **contaminated numerator — the CAMPD gross channel**; the
nameplate was never wrong.

Annual reconciliation (probe output): CAMPD unit-4 gross 2.246/2.320/2.262 TWh
(2023/24/25) vs EIA-923 plant net **1.524/1.583/1.535 TWh** — the net series
sits comfortably *inside* the 206 MW ceiling (max 1.805 TWh/yr), so the
model's capacity basis cannot be the CC_CHP shortfall's cause.

## §3 — Why no A/B was run (and why running one would have been wrong)

The chartered change ("fix the ~90 MW") is refuted by the evidence: raising
Kendall's pmax toward the CAMPD gross reading would inject capacity two
independent EIA sources say does not exist, violating rule 14 `[R-ACCURATE]`
in reverse (CAMPD gross is not an accurate *capacity* measurement — it is a
mis-based channel for that purpose). With no admissible delta there is nothing
to pre-register and nothing to solve; per the neiso-71 §1 precedent this lands
as a no-LP adjudication. The `nameplate_mw` provenance-orphan hazard
(miso-95) was honoured: **no thermal-tranche re-derivation was touched**; for
Kendall specifically the committed column is now shown *consistent with the
primary source*, which narrows (but does not close) miso-95.

## §4 — What this changes for the floor lane (successor, NOT this session)

The neiso-71 DO-NOT-REDO ("no CC_CHP floor until the capacity item closes")
is now **discharged** — the capacity item is closed with "capacity was never
the problem." Two of neiso-71's conclusions update:

1. **A Kendall host-steam identification becomes derivable — on the NET
   basis.** Kendall's measured net loading-when-on is **184.1/197.4/186.5 MW
   = 89.4/95.8/90.5 % of pmax** (923 net ÷ CAMPD on-hours), on-frequency
   94.5/91.3/94.0 % — the unit genuinely IS a flat baseload steam host at its
   *net* rating. neiso-71's structural claim ("NEISO merchant CC_CHP carries
   no host-steam obligation") remains true **only for the non-Kendall cogens**
   (2.2 %/3.6 % levels, real cyclers, 15.0 MW combined floor).
2. **Any future derivation touching 1595 must de-base or avoid the CAMPD
   gross channel** — both the steam level (`steam_level_cf`) *and* any
   `measured_chp_heat_rates`-family heat rate (gross-basis HR at 1595 reads
   6.4, ~32 % low). A net-basis identification (EIA-923-anchored, or CAMPD ×
   the measured 923/CAMPD basis ratio) regenerates yearly from filings and
   responds to changed conditions — rule 13-admissible. Whether the resulting
   ~90–96 % floor on 42 % of the class is *promoted* is that session's A/B to
   run, with the neiso-71 over-closing hazard (shortfall 0.34–0.68 TWh vs a
   ~1.6–1.7 TWh floor effect) stated in its prereg. It is **out of scope
   here** (handoff: the floor lane needs Lever A landed first — it now is).

## §5 — Governance

* **No LP, no bundle, no registration** — rule 15 attaches to completed
  backcast runs; none was produced. The keeper, its criteria, its C3c ledger
  and the DOF ledger are untouched.
* **Zero parameters** introduced, tuned, or re-derived; no `ScenarioConfig`
  field added (no new matrix row owed under rule 28c).
* Matrix duties (rule 28b): `measured_chp_heat_rates` NEISO cell note + ev
  updated in this session (cell **stays `O`** — nothing armed, nothing
  refuted); §5.6 item 6 prerequisite marked adjudicated; NEISO header
  `gates` text refreshed (it still cited the neiso-71 keeper).
* Holdout: no out-of-training year solved or scored; probe reads of
  2018–2022 raw source files are no-LP data reads (the posture rule 22
  permits and neiso-72's probe used). Locked test remains SPENT, untouched.
* Levers B (PS cycling depth) and C (930-hourly 2022 extract rebuild) were
  **not taken** — one arm per session; both remain queued for neiso-74.
