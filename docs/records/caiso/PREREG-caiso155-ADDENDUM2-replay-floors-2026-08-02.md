# PREREG-caiso155 ADDENDUM 2 — A1b failed for the rebuild instrument (as pre-registered); the regen instrument upgrades to REPLAY-SOURCED REAL FLOORS under the same gates. Committed before any replay-based number exists

**Session:** caiso-155. **Date:** 2026-08-02. Second amendment to
`PREREG-caiso155-diagnostics-plant-set-2026-08-02.md`; gates keep their
meaning, the regen INSTRUMENT changes. Addendum 1's Part 0 (threading) stands
and is load-bearing here.

## A. The A1b verdict on the rebuild instrument (measured, on the record)

Ladder run on the three census-affected keepers (transcripts in the session
scratchpad; headline numbers to be quoted in the FINDING):

* **Gated material-class D-2 shares reproduce** through the threaded rebuild
  at CAISO (max |Δ| 0.0001 after the documented `ra_mustoffer_bridge`
  subtraction) and MISO (max |Δ| 0.0006, no subtraction needed) — the G-06
  premise holds for what G-06 actually compares.
* **A4 anchors exactly**: CAISO firm_import floor energy 17.938 / 22.684 /
  22.494 TWh vs the caiso-151 §C clipped exposure — equal to the 3rd decimal.
* **MISO has NO firm-import exposure at its current keeper**: the channel
  arms `miso_manitoba_seam` (miso-74), which REPLACES the legacy firm block
  (16 unfloored seam band rows; zero `firm_import` stamps). The census's
  6.36/4.65/1.96 TWh was the UNTHREADED rebuild hallucinating the legacy
  default — defect 2 manufactures replaced floors as well as losing armed
  ones. MISO's committed artifact is correct as committed; NO MISO regen.
* **A1b FAILS for a rebuild-sourced regen everywhere else it matters** —
  `run_year(fleet_only=True)` structurally cannot rebuild solve-state floors:
  NYISO's P1-native `nyiso_gas_commitment_bridge` (5.31 / 3.14 pp of
  CC_REGULAR's gated share — the committed rows are real and would be LOST),
  CAISO's P1-seam `ra_mustoffer_bridge` D-2 detail rows, and the
  post-fleet-exit nuclear/hydro/CHP floor applications (missing
  `hydro_min_flow` D-4 rows, `nuclear_mustrun`/`chp_steam` detail).
  Per Addendum 1 §C: **no artifact regen ships from the rebuild.**

## B. The upgraded instrument (pre-registered before its numbers exist)

For CAISO and NYISO only: an **in-place, full-span keeper replay**
(`scripts/replay_keeper.py <bundle>` — byte-faithful recipe, timestamp
restored, no `--set`, no partial years), which regenerates the gitignored
`floors/<year>_P1.npz` + `dispatch/*.parquet` the artifact generation
consumed when the committed artifacts were first written. Rule-15 note
licenses keeper replays "for unit-level questions"; per-tranche floors are
one. Replays run SEQUENTIALLY (15 GB box; each peaks ~7 GB — rule 12's
memory cap). A replay is not a new run: nothing is registered, no dashboard
entry, no marker.

**Fidelity gate D-13 (pass/fail, per ISO):** after the replay, every
COMMITTED bundle file must be byte-identical to git HEAD — `hourly/*.parquet`
(the committed solve fingerprint), `meta.json` (timestamp restored),
`metrics.json`, `run_config.json`, `calibration_attestation.json`. Any diff
= the HEAD code no longer reproduces the keeper solve → that ISO's regen is
ABORTED, committed bundle files are restored from git, and the divergence is
reported (caiso-154 §H: reproductions are not a standing guarantee).

**Then the SAME gates re-run with replay floors:**

* A1b′ — regen (fixed scorer, real floors, parquet dispatch path) vs
  committed: every pre-existing D-1/D-2/D-4 row reproduces (D-2 shares
  within the G-06 tolerance WITHOUT any bridge carve-out, since the bridge
  is now in the floors; D-4 mechanism set ⊇ committed; D-1 within the
  HEAD-code drift already measured, all verdict-stable).
* A2′ — additions only: D-2 rows with class `""` × exempt mechanisms, D-4
  `firm_import` rows, notes. (A pre-existing-row VALUE may move only where
  the dispatch source upgrades from payload-decode to the exact parquet —
  reported per row if it occurs; verdict flips still gate.)
* A3 — xiso-3 production-rubric re-score on the installed artifacts:
  criterion profiles and determinations IDENTICAL, else stop rule S1.
* A4 — unchanged CAISO anchor.

D-1 note, measured before this addendum: regenerating at HEAD moves D-1
`cv_ratio`/`profile_r` ONLY on C7-exempt CHP classes (worst gated-class move:
CT_PEAKER r −0.002) with ZERO verdict changes — HEAD-truth refresh, not a
gate event. It ships with the regen and A3 adjudicates it.

## C. Shipping rule

An ISO's regenerated `legitimacy_diagnostics.json` is committed IN PLACE iff
D-13, A1b′, A2′, A3, A4 all pass for that ISO. Any failure → that ISO ships
nothing, committed bytes stay, and the failure is the FINDING's result. MISO
ships nothing by measurement (§A). PJM stays S3-blocked; ERCOT/NEISO have
empty populations (no exposure, no regen).
