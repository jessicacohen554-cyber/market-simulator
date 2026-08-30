# FINDING — capx-NEISO-RC Phase 0: attribution of the D14 retirement-composition miss

**Session:** NEISO-RC PHASE-0 (capacity-expansion / Forecast Finalization track, director
refresh #19 lane NEISO-RC). Branch `claude/capx-neiso-rc-phase0-c0q8qs`, off `3960244`.
**Charter:** ZERO SOLVES. Attribution of the capx-D14 retirement COMPOSITION miss
(`FINDING-capx-d14-neiso-t1x-2026-08-30.md` §0.2/§5: run
`neiso-2023-2027-crossover-capxd14` — gas_cc over-retired 3.128 vs 1.884 GW actual;
biomass / coal / gas_ct / oil exits missed entirely; recall 2/6) from COMMITTED artifacts
only. No mechanism change, no `ScenarioConfig` field, no matrix cell, no board edit, no
verdict touch. Repair chartering is the director's next-batch decision on this finding.

## 1. PRE-DECLARATION (the charter's candidate drivers, and what distinguishes them)

The four candidate drivers stand PRE-DECLARED IN THE DISPATCH CHARTER itself (director
refresh #19, this lane's prompt) — that charter text, committed in the director ledger
before this session existed, is the ex-ante record:

- **(a) Screen materiality path** — the screen prices only classes with meaningful energy
  margins; small biomass/oil/ct classes never clear the screen's materiality path.
  *Distinguishing evidence:* the screened-unit set per fuel. If oil/gas_ct units are absent
  from the screen's margin evaluation (no margin rows at all), (a) holds; if they ARE
  priced and adjudicated, (a) is refuted in its stated form and the protection lies
  elsewhere.
- **(b) Per-fuel FOM/threshold inputs vs NEISO's actual exit economics.*
  *Distinguishing evidence:* the per-fuel bar sides (net revenue vs going-forward cost)
  and whether the per-fuel constants (FOM levels, execution lags), rather than the margin
  ordering, determine which fuels' failures become in-window exits.
- **(c) Non-economic instruments the forecast has no channel for** (age/permit/RMR/consent
  decree) — a REPRESENTATION gap, not a tuning gap. *Distinguishing evidence:* per
  actual-exit unit, the real-world exit instrument vs the run's admissible channels
  (confirmed registry rows + instrument dates vs the vintage cutoff 2023-12-31; the
  announced channel's fossil no-op).
- **(d) The gas_cc over-retirement as the mirror of (a)–(c)** — the screen concentrating
  ALL exit pressure on the one fuel it prices richly. *Distinguishing evidence:* whether
  the modeled gas_cc exit MW is sized/allocated by gas_cc's own margins or by a shared
  budget (e.g. the adequacy floor) that other fuels escape.

**Sequencing disclosure (recorded against interest).** This session's measurement did not
strictly follow "commit the skeleton, then measure": the READ-FIRST pass (D14/S-4b
findings, `crossover_score.json`, spec §5.2, screen code, the confirmed registry and the
actuals CSV) flowed directly into extracting the committed S-4b evolution-ledger margin
rows BEFORE this file was committed. The charter's (a)–(d) were fixed ex ante by the
dispatch prompt and are tested as chartered; nothing here was re-declared after the fact,
and the s4b-ledger extraction is reported at full magnitude in §3 whatever it says about
the candidates. The measurement sections (§2 onward) were completed after this commit.

## 2. (to follow) The measured decomposition

## 3. (to follow) Per-fuel attribution table

## 4. (to follow) Distinguished drivers

## 5. (to follow) Routed repair candidates with rule 13/21/23 admissibility
