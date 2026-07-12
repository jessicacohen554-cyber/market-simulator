# Gap register (2026-07) - G-19 (holdout data-equivalency gate)

The 2026-07 calibration cycle's gaps are tracked across the lane/prompt file
(`docs/gap-register-2026-07-prompts.md`) and the per-gap handoffs under
`docs/handoffs/`. This file is the owner-designated home for the **G-19** status
- the cross-ISO holdout data-equivalency gate - recorded here as it lands.

## G-19 - Cross-ISO holdout data-equivalency gap register (GATE)

**Owner order (2026-07-07):** no holdout solve, no holdout score, and no holdout
result may be recorded for ANY ISO until a series-by-series register confirms
each holdout year's input coverage (drivers, fleet/overlays, bench actuals, and
their granularity/vintage) matches the keeper years', **and the owner signs off
per ISO**. The NEISO one-shot execution is HELD on exactly this
(`docs/handoffs/neiso-calibration-complete-memo-2026-07.md` §6; the memo's
§4/§5 execution + irreversibility terms apply whenever the gate clears).

**Status (2026-07-12): register CREATED - `docs/holdout-data-equivalency-register-2026-07.md`.**

- **NEISO 2022 readiness DONE** (2026-07-12 data-readiness lane). The register
  (`docs/holdout-data-equivalency-register-2026-07.md`) is the shared cross-ISO
  doc the parallel NYISO lane merged; the **NEISO section is added additively by
  this lane's lander** (`apply_neiso_2022_readiness_docs.py`, run by
  `holdout-intake-neiso-2022.yml`) and its full audit lives here + in
  out-of-sample §1.3. NEISO 2022 intake is prepared under the 2026-07-12 owner
  authorization (MERGE-not-replace, all 2023-2025 in-sample rows byte-frozen;
  no-LP, no solve - the G-19 HOLD stands). Verdict tally for NEISO 2022:
  **EQUIVALENT 21 / DEGRADED 2 / MISSING 1 (non-default limb) / accepted-absence 1**.
  - **DEGRADED**: (1) daily Algonquin gas basis - weekly-anchored, densified
    38 -> 62 prints, still sparse; (2) outage-window detector vintage - 2022 is
    a HEAD re-derive, committed in-sample windows are an older vintage
    (calibration-owner decision, not resolved).
  - **MISSING**: NEISO-AS measured hourly reserve requirements (raw absent all
    years) - needed only by the non-keeper dynamic-RR limb (neiso-57), not the
    frozen keeper; owner decision on committing the raw exports.
  - **accepted-absence**: EIA-930 storage breakout for 2022 (C5b/C5c SKIP -
    structural, holds in-sample too).
  - **H1-2026**: BLOCKED (publication horizon - CAMPD Q2-2026, delivered gas
    May-2026+, F3 demand profiles, F4 reference-year registration). Locked test
    (rule 22, touch-once); executes later under the same marker.
- **ERCOT / PJM** (2022 intake landed 2026-07-04, out-of-sample §1.1):
  equivalency audit PENDING (their own lane).
- **CAISO / MISO**: no holdout intake - register rows start MISSING.
- **NYISO**: register **§NYISO DONE** (its own lane, merged to main) -
  EQUIVALENT 24 / DEGRADED 4 / MISSING 5 for the 2022 window (2026-07-12 intake);
  owner sign-off + a `complete.NYISO` marker still pending per its section.

**Exit:** owner sign-off per ISO. For NEISO, the sign-off decision also carries
two surfaced items (register "Exit criterion"): the keeper-identity
reconciliation (one-shot marker names neiso-54; dashboard keeper is neiso-56 -
audited input files are invariant across them) and the outage-window vintage
choice (reconstruct-committed vs pinned-vintage-re-derive). Separately, an
in-sample keeper-repro drift on main (+0.22/+0.38/+0.68 $/MWh, dual-fuel tranche
drift after `7f968f3`) stays in its own NEISO/main lane. Until owner sign-off,
the one-shot stays HELD.
