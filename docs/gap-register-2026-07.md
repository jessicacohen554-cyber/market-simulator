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

- **NEISO 2018-2022 readiness DONE, register §NEISO complete** (2026-07-13
  lane, extending the 2026-07-12 2022-only readiness). Owner authorization
  (verbatim, `calibration-complete.json` intake_log): *"This data can
  literally be collected for all years — we're not running anything on it.
  Fetch it all at once for 2018-2022 and first half 2026 if available."* The
  2026-07-12 landing residuals (§NYISO N5: no NEISO 2022 in `actual_lmp*`/
  tail, no `NEISO_2022_renewable_capacity.csv`, this file a placeholder stub)
  are now CLOSED, and readiness extended back to 2018 where source data
  permits (`scripts/land_neiso_2022_readiness.py` +
  `scripts/land_neiso_holdout_multiyear.py`). Full audit:
  `docs/holdout-data-equivalency-register-2026-07.md` §NEISO. Verdict tally
  for the 2018-2022 window: **EQUIVALENT 12 / DEGRADED 8 / MISSING 6 (zero
  unresolved — every MISSING row carries an explicit fix or acceptance)**.
  - **DEGRADED**: outage-window detector vintage (all appended years, same
    class as the original 2022 finding); daily Algonquin gas (still
    2023-2025-only — monthly basis covers every year as the accepted
    fallback); fleet statics + dual-fuel switch roster + winter-fuel-security
    figures (static, accepted); parasitic load factors + fossil CO2 rates
    2018-2021 (pooled-fallback / v2-superseded, accepted).
  - **MISSING**: driver-demand model profile (`eia_demand_profiles.parquet`)
    2018-2020 — **HIGH**, blocks dispatch outright, same F3/F4 class as the
    ERCOT/PJM doc, not fixed in this data-only lane; `calibration_reference`
    2018-2020 (same root cause); ISO-NE SMD LMP bench 2018-2019 (no workbook
    on disk, hand-obtained artifact class); `actual_tail.json` 2018-2021
    (deriver's `HOLDOUT_YEARS` constant is shared cross-ISO, not hand-edited
    here); plant emission rates v1 (accepted-structural, same as NYISO);
    NEISO-AS measured hourly reserve requirements (unchanged from
    2026-07-12 finding, non-keeper limb).
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
