# PRECOMMIT — closeout-B: W0 EIA-860 settlement foundation (phases 1 + 2, zero LP)

Lane: `claude/closeout-b-w0-foundation`, chartered by the Backcast close-out desk
(2026-10-02). Base: `origin/main` 4d459da3. Plan: `docs/backcast-closeout-plan-2026-10.md`
§2.1 (W0) and §5.0 R-2 (owner approved Q1–Q8). Spec: audit
`AUDIT-eia860-capacity-vintage-settlement-2026-10-02.md` §E.1–E.9.

**This session runs no LP** (rule 32). Phase 3 (one full-span re-solve per ISO)
waits for the desk to merge phases 1+2.

## 1. What phase 1 implements (E.1–E.9)

| Audit item | Construction | Field / seam |
|---|---|---|
| E.1 seasonal basis | thermal unit carried at B = max(summer, winter) of the solved vintage; summer share Jun–Sep, winter share Oct–May; blank winter → summer, blank summer → nameplate; non-CC winter ≤ max(nameplate, summer); CC under the always-on max(nameplate, CAMPD p99.9) guard; flat class derate deleted on covered rows | **new** `seasonal_capacity_basis` (backcast default ON, per-plant fleets) |
| E.2 / E.5 vintage + retirement | solved year reads `vintage_<Y>/` (2025 = Final, landed by #7015); operable-sheet `Planned Retirement` never read in a backcast; vintage diffs committed | **new** `backcast_actual_retirement_only` (backcast default ON) |
| E.3 registry-read repairs | default-on in backcast everywhere, `--no-…` escapes: `commission_year_cod_fallback`, `cc_block_summer_rating`, `cc_steam_part_capacity`, `retiree_vintage_status_scope`, `partial_plant_exit_carry`, `mid_vintage_exit_carry`; steam-part predicate in every ISO; block predicate everywhere, NG blocks included where no demonstrated-peak table exists | F1 two-half landing (flip + coercion outside backcast) |
| E.4 status | `admit_standby_units` backcast default ON; bin constituents read the same status set; OA/OS envelope reported by the census | flip |
| E.6 load-time BA | generator tables regenerated unfiltered + `nerc_region`; readers use `generator_footprint_mask` / `program_footprint_mask` | data + code |
| E.7 census | `scripts/build_fleet_census.py` → `fleet_census_<Y>.json`; `promote_keeper.py` preflight refuses a new keeper without it; `audit_keepers.py` E15 | new script |
| Q7 crosswalk | EPA CAMD-EIA + PUDL subplant ids = crosswalk of record; every `CAMPD_UNIT_PLANT_REMAP` row confirmed or a cited override | `data/campd_crosswalk.py` |
| Q5 ERCOT CSV | per-vintage audit of `custom-bin-assignments.csv` inside the ERCOT census | `--ercot-csv-audit` |
| E.8 | eight named regression tests (+ crosswalk test) | tests |
| E.9 | `solve_surface.json` carries `eia860_vintages` sha256 per directory read; freeze rule in the EIA-860 README | stamp |

## 2. Declared departures from the letter of the charter (stated ex ante)

1. **Companion flip: `unit_outage_dispatched_bin_denominator` backcast default ON.**
   Not one of the seven named flags. Reason (rule 19): E.1 moves every thermal
   bin's pmax and E.3 moves the bins it repairs; the reconstructed outage
   denominator cannot follow them, the dispatched-bin denominator is the LP's
   own pmax by definition. It yields (coerced off) to an explicitly armed
   alternative denominator (`unit_outage_extract_basis_share`,
   `unit_outage_coal_extract_basis_share`, `unit_outage_lp_capacity_basis`), so
   no recipe is refused. The reconstructed map also now carries the block and
   steam-part repairs (`paths.set_eia860_fleet_row_repairs`), so the miso-272
   point-of-use guard fires only where the two bases genuinely differ.
   **DESK-CONFIRMED 2026-10-02** (session_017wUwd6…, reported to the owner as a
   desk-confirmed addition to R-2), conditions: (a) `--no-unit-outage-dispatched-bin-denominator`
   on `run_calibration_full.py` reaches the pre-arm posture (or `replay_keeper --set
   unit_outage_dispatched_bin_denominator=false`); (b) the yield rule is tested
   (`tests/unit/data/test_unit_outage_dispatched_bin_denominator.py::test_yields_to_an_explicit_alternative_denominator`)
   and resolves per keeper as below; (c) the matrix row's definition states the
   backcast default and every shard already carries its cell; (d) G-DRIFT
   toggles it ALONE per ISO (`gdrift_2023.json`), attributed separately from E.1;
   (e) the NEISO tripwire was evaluated WITH it on.

   | Keeper recipe | denominator posture | resolved under W0 |
   |---|---|---|
   | ERCOT `r_ercot24_span` | none (ERCOT branch caps on its bin sheet) | inert (non-ERCOT construction) |
   | CAISO `rcaiso20_A_*` | `unit_outage_extract_basis_share` | **yields → off** |
   | PJM `pjmnext16_A_span` | none | **on** |
   | MISO `miso280_span` | already armed | on (unchanged) |
   | NYISO `nyisonext26p_*` | `unit_outage_extract_basis_share` | **yields → off** |
   | NEISO `neiso119_span` | none | **on** |
   | SPP `spp100_arm_span` | `unit_outage_coal_extract_basis_share` | **yields → off** |
   | NWPP `nwppnext16c_span` | none | **on** |
   | SOCO `soco96_span` | none | **on** |
2. **E.4 benchmark parity by the ruling's "fleet admits what the benchmark
   counts" branch.** The EIA-923 benchmark is not status-filtered (an OA status
   is a year-END snapshot; the plant may have generated during Y — filtering it
   would remove measured energy, rule 14). SB is admitted fleet-wide; the
   OA/OS-only envelope is reported per ISO-year in the census, never fitted
   (ruling Q2).
3. **E.1 scope.** ERCOT's curated bin sheet keeps its nameplate basis (Q5:
   "audit now, migrate later"); nuclear/oil/biomass rows (no thermal group)
   stay on net summer. Both named in the census.
4. **Vintage diffs** are written under the W0 census records, not
   `data/raw/eia-860/vintage_diffs/` (derived evidence; `data/raw` is the
   immutable source root).
5. **EPA NEEDS** is not intaken: its published URL returned 404 from this
   container (§F 4) — a manual download for the owner.

## 3. Phase 2 (zero LP)

- NEISO tripwire FIRST: `scripts/probes/_w0_neiso_tripwire.py` on 2019 and
  2025, recorded vs W0 posture: Pilgrim 1590 / Mystic 1588 carries, Kendall
  1595 basis, Canal 3 1599 class. The C3a > 2 pp criterion needs an LP and is
  read from the first W0 span (phase 3).
- Census per ISO-year, both postures, every keeper year →
  `W0-census/<ISO>/fleet_census_<Y>_{w0,recorded}.json`.
- G-DRIFT (rule 29 (b)) per ISO: `scripts/probes/_w0_gdrift_fields.py` toggles
  each W0 field alone on the 2023 keeper recipe and hashes every LP-visible
  fleet array + `mc_base`: INERT (no hash moves — the measurement is the
  reason) or LIVE (earns the phase-3 span). Code-only hunks (month sentinels,
  E.6 regeneration, E.9 stamp, census/promote/audit tooling) are classified
  from their own measurements in the RESULT.

## 4. Gates

No tuning to a residual (rule 23); tolerances (1 % family / 0.5 % total vs
860, 3 % vs ISO report) are the owner's (Q8) and are reported, not targeted —
a census OUTSIDE tolerance is a named residual for the phase-3 lane, not a
reason to move a parameter.
