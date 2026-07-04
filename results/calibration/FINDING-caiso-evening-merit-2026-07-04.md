# FINDING — CAISO evening CT-vs-CC merit order (2026-07-04)

**Thread:** open root cause disclosed by the caiso-52 CT-floor scrub (keeper caiso-51).
**Question (task step 2):** with the CT forcing stack removed, evening CT merit dispatch is
far under actual while CC_REGULAR over-runs and imports are under-represented. *Why does the
P1 merit order dispatch CC (and not CTs / imports) in the evening net-load ramp?* Adjudicate
the three candidates: (A) CC committed band too cheap; (B) import tranches mispriced in the
evening; (C) CT startup/min-run amortization making CT offers too dear in P1.

**Method.** Reproduced the caiso-52 recipe (caiso-51 flags; CT scrub already in `main`) for
2024 as a single-year diagnostic (`results/calibration/caiso_diag_evening_2024`,
`--year 2024`, per rule 15 a throwaway diagnostic — NOT dashboard-registered). Extracted P1
per-class hourly dispatch, per-tranche import flows, and zonal LMP
(`scratchpad_diag_evening.py`), and reconstructed the class SRMC ladder from the loaded fleet
heat rates + measured 2024 SoCal gas + CARB $35.23/tCO₂.

## The evening ramp, 2024, model P1 vs CAMPD actual (mean MW, h15–21)

| class | model | actual | Δ |
|---|---|---|---|
| CT_PEAKER | 598 | 770 | **−172** |
| CC_REGULAR | 8508 | 6320 | **+2188** |
| CC_CHP | 1015 | 735 | +280 |
| ST_GAS | 115 | 15 | +100 |

CT_PEAKER **diurnal shape is clean** (≈0 overnight, evening-concentrated — the scrub held);
the miss is a magnitude deficit in the evening peak (model peaks ~900 MW at h19–20, actual
~1077 MW at h18). CC_REGULAR over-runs **in every hour** — overnight 9357 vs 6128 (+3229),
midday 5500 vs 3100 (+2400), evening +2188 — i.e. the over-run is NOT confined to the ramp,
so it is not a ramp phenomenon; it is a persistent over-supply of cheap CC.

## The SRMC ladder resolves it (gas $3.0 SoCal evening, CARB $35.23)

| band | CC_REGULAR (HR 7.6, 0.38 t/MWh) | CT_PEAKER (HR 10.4, 0.60 t/MWh) |
|---|---|---|
| committed | **$38** (0.90×) | $67 (1.35×) |
| econ_low | **$39** (0.95×) | **$59** (1.10×) ← CT's cheapest |
| econ_high | **$45** (1.21×) | $71 (1.50×) |
| peak | $68 (2.25×) | $149 (4.00×) |

**SP15 evening LMP: mean $51, p50 $51, p90 $67, p99 $78.** CT_PEAKER's *cheapest* offer
($59) exceeds the evening LMP in **~70% of evening hours** (only 29.4% of evening hours clear
≥ $59). CC covers the ramp through its committed/econ_low/econ_high bands ($38–$45), all below
the LMP; CC peak ($68) is the ceiling. So:

- **CTs are priced out on energy merit** — not by a too-dear offer, but because CC (HR 7.6) is
  thermodynamically ~35% more efficient than CT (HR 10.4); even CC's *peak* band ($68) sits at
  CT's *committed* band. The CT that does clear (evening ~600 MW) is exactly the ~30% of hours
  where the LMP tops $59. This is the correct LP answer to an energy-only, ramp-free, zonal
  problem.

## Candidate adjudication

- **(C) CT amortization too dear in P1 — REJECTED.** `tranche_startup_amortization=false` in
  this recipe; CT offers are their SRMC bands, and CTs *do* clear whenever the LMP reaches
  their SRMC (~30% of evening hours). CT offers are not artificially inflated; they are
  correctly above the marginal price. The reason reality runs ~1000 MW of evening CT is
  **ramp-rate + min-up/down commitment** (fast net-load ramp → fast-start CTs) and
  **locational** need (LA-basin load pockets) — neither is representable in an energy-only,
  ramp-free, 3-zone LP. **The caiso-51 CT floor was papering over the absence of ramp/local
  structure.** Closing CT evening dispatch *through merit* is not achievable without those
  structural mechanisms; a floor is the only alternative, and is forbidden (rules #1/17–20).

- **(A) CC over-supply — CONFIRMED as the CC/import driver.** The audit-flagged sub-SRMC CC
  offer (committed 0.90×, econ_low 0.95× — below the physical 1.0× SRMC floor;
  audit §2) offers ~92% of the CC fleet at/below cost, flooding cheap CC around the clock
  (the +3229 MW overnight over-run has no ramp excuse) and pinning the LMP at ~$42 avg — below
  CT SRMC and below the spot-import cost.

- **(B) imports "mispriced" — REFRAMED.** The spot import tranches are *not* mispriced; they
  are **undercut** by the over-cheap CC. Evidence (2024 tranche utilisation, evening h15–21):

  | tranche | cap MW | evening util | ann TWh | note |
  |---|---|---|---|---|
  | PNW_hydro_base (firm $28) | 800 | **86%** | 5.85 | capacity-limited |
  | DSW_solar_PV (firm $48) | 1800 | 62% | 8.15 | heavily used |
  | DSW_CCGT (spot ~$60) | 1800 | 16% | 5.91 | undercut by CC |
  | DSW_CT (spot ~$70) | 2200 | 0.4% | 0.48 | never clears |
  | PNW_midC (spot ~$49) | 1800 | 18% | 5.07 | undercut |

  The cheap **firm** blocks are near-maxed (PNW_hydro_base 86% evening) while the spot blocks
  sit idle with headroom — so the under-import (net 24.7 vs 32.4 TWh actual) is set by (i) the
  firm blocks being **undersized** and (ii) domestic CC being cheaper than spot imports. The
  model even **exports** on the evening corridors (export_MALIN −673, export_PALOVRDE −380 MW,
  h15–21) — physically wrong (CAISO is a heavy evening importer) and a direct artifact of the
  over-cheap CC (domestic $45 < Malin hub $49 → the LP exports cheap CC). Net evening import is
  only 1488 MW vs 3273 overnight / 3367 midday — backwards.

## Conclusion — two real structural levers, one non-lever

1. **CT evening merit (task headline): STRUCTURAL GAP, not merit-fixable.** CT is
   thermodynamically dominated by CC; it runs in reality for ramp/locational reasons absent
   from the energy-only zonal LP. Options: add CC ramp-rate/min-up-down commitment physics
   and/or sub-zonal (LA-basin) transmission so the ramp forces fast-start CT starts. Large
   structural build. **Do NOT re-floor** (rule #1).

2. **CC over-run + import under-run (coupled): addressable.**
   - **Lever A (code-only, evidence-indicted):** correct the un-grounded CC sub-SRMC committed/
     econ_low discount (0.90/0.95× → the physical avoided-startup floor ≈1.0×; audit §2, DOF
     rationale = a running unit's SRMC is its fuel+VOM+carbon). Raises the domestic marginal
     cost, stops the evening export artifact, lifts the LMP toward CT SRMC, and lets spot
     imports clear. *Expected impact modest* — CC stays cheapest, so dispatch reduction is
     bounded; it mainly reprices, not re-dispatches.
   - **Lever B (data intake, task step 1):** ground the firm import-tranche VOLUMES to real
     published specified-import data. PNW_hydro_base at 86% evening utilisation is the smoking
     gun that the firm block is undersized. **Requires** real CAISO-boundary specified-import
     volumes by corridor; the cleanest published source (CEC "Total System Electric
     Generation": 2023 NW 15,925 GWh / SW 49,593 GWh) is on the **all-California** boundary
     (LADWP/IID/BANC included) — misaligned to CAISO per rule #14, so it needs reconciliation,
     not literal use. CARB's specified-vs-unspecified split (the firm fraction) is published as
     an emissions aggregate on the jurisdictional-importer boundary — a third boundary. A
     defensible firm-block sizing needs the CAISO-boundary specified-import MWh by path
     confirmed from a primary source; do not resize the blocks to a residual-improving value
     (rule #14 forbids it).

**Neither lever delivers the task's stated success (CT closing *through merit*) this session:**
lever 1 is a large structural build; lever 2 closes import volume + CC over-run but, by adding
cheap supply, would if anything *lower* the LMP and clear *fewer* CTs. The CT-merit target and
the import-volume target are in tension under an energy-only LP.

## Files
- `results/calibration/caiso_diag_evening_2024/` — single-year diagnostic bundle (P1/P2
  dispatch, flows, system). NOT dashboard-registered (single-year, rule 15).
- `scratchpad_diag_evening.py` — extraction/diagnosis script.
