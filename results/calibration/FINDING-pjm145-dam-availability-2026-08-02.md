# FINDING — pjm-145: `pjm_dam_availability` (measured PJM generation-outage availability)

**Session pjm-145, 2026-08-02.** PREREG:
`results/calibration/PREREG-pjm145-dam-availability-2026-08-02.md` (committed
before any measurement; the ex-ante instrument
`scripts/probes/_pjm145_damavail_exante.py` and the chain script
`scripts/probes/_pjm145_chain.sh` committed before running).

## §0 — Headline

*(filled after adjudication)*

## §1 — Session preamble: the two standing fixes

1. **Default cache key (handoff fix a): ALREADY REPAIRED UPSTREAM — no work
   was needed.** At this session's HEAD (f58339b), `ScenarioConfig().cache_key()`
   returns the pinned `603c2498bf71d21d` and all three handoff-named tests pass
   (`test_cc_committed_offer_margin`, `test_ramp_envelope_basis`,
   `test_forecast_xyear_warmstart_flag::test_default_cache_key_unmoved`, plus
   `test_persisted_identity` — 42 passed). The repair was the FFR-W1X Wave-1
   close (2026-08-02): `coal_prb_committed_dispatchable` +
   `coal_prb_committed_split` registered in `_CACHE_KEY_OPTIONAL_FIELDS`
   (scenarios.py:54–71 comment records it as occurrences six and seven of the
   unregistered-field failure), and pjm-144 registered its own two fields. An
   AST field-diff against the pin commit (36cfa4d) confirms all 10 fields added
   since the pin are registered and none was removed.
2. **Full-suite baseline on origin/main f58339b (handoff fix b), recorded
   BEFORE any edit:** `11 failed, 5869 passed, 31 skipped, 1 xfailed`
   (16 m 44 s). The failures:
   `tests/unit/data/test_measured_chp_heat_rates.py` ×7,
   `tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`,
   `tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`,
   `tests/curation/test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`,
   `tests/regression/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`.
   The first three groups are the handoff's known-red set; the last two are
   additional pre-existing failures on clean main (not present in the handoff's
   9950a5c list; both fail before any pjm-145 edit, so neither is a pjm-145
   regression). The handoff's three cache-key tests now PASS (item 1).
   `test_dispatch.py::test_full_year_200_generator_fleet` passed in this run.

## §2 — Queue provenance (rule 28a)

Taken: **`docs/mechanism-testing-matrix.md` §5.3 item 7** — `pjm_dam_availability`
(**U**, "intaken but untested"), the live head of the PJM queue and the one
cross-ISO queue head with committed data, built code, and no charter/data-ask
blocker (MISO has no live lever; ERCOT items 7–8 are data-intake-first; NEISO
requires a charter; CAISO's live items are a charter and a derive
re-identification). Matrix row `dam_availability_rebasis`, PJM column
(cells "KUUR.R", PJM = index 2). Rule 25: no ERCOT parameter or verdict
transfers; every PJM constant is the intake's own cited default.

## §3 — Local-data regeneration required by the keeper recipe (recorded for
the next session)

A fresh clone cannot replay the pjm-143b keeper as-is; two gitignored inputs
had to be regenerated first (both documented regeneration paths, not new
intakes):

- `data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023..2025}_*.parquet` — the
  keeper arms `pjm_da_virtual_bids`, whose loader hard-fails when the raw
  DataMiner2 feed is absent ("the mechanism never silently no-ops"). Re-pulled
  via `scripts/data/fetch_pjm_da_virtuals.py --feeds hrl_da_incs_decs`
  (36 monthly parquets; the feed is redistribution-restricted, hence
  gitignored — `data/raw/pjm-da-virtuals/README.md`).
- `data/raw/PJM-AS/pjm_{2023..2025}_as_up_mw.parquet` — the measured reserve
  requirement series, derived from the committed
  `reserve_market_results_*.parquet` by
  `scripts/data/build_pjm_as_withholding.py`.

Plus the standing setup: `uv sync --frozen`, the three curate scripts, and
`scripts/regenerate_clean.py transfer-interface-limits ramp-capability`.

## §4 — Ex-ante measurement (PREREG §3) and the kill verdict (PREREG §4)

*(filled from `results/calibration/_pjm145_damavail_exante.json`)*

## §5 — A/B

*(filled after the chains; control `pjm145_control_A`, arm `pjm145_damavail_B`,
both replays of `pjm143_hy_level_B` at HEAD f58339b + this session's committed
probe/chain scripts)*

## §6 — Construction gates (PREREG §5)

*(filled)*

## §7 — Kill gates (PREREG §6) and C3c, reported explicitly

*(filled)*

## §8 — Direction prediction, scored honestly (PREREG §7)

*(filled — the prediction was NET REMOVE / prices UP / C3a-2023 away,
2024/2025 toward / C3c tail counts up)*

## §9 — Verdict and registration

*(filled: matrix cell, dashboard registrations, keeper disposition)*
