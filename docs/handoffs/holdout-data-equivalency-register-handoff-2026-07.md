# HANDOFF — Holdout data-equivalency gap register (all six ISOs)

Owner-ordered gating deliverable (2026-07-07): **no holdout solve, no holdout
score, and no holdout result may be recorded for ANY ISO** until this register
exists and the owner signs off per ISO. Tracked in gap-register G-19; the
NEISO one-shot execution is HELD on exactly this. Read CLAUDE.md fully —
rule 22 governs; also rules 13/14/23. Push ONLY via `mcp__github__push_files`
(text) / the marker-guarded Actions workflow (binaries); never `git push`.
Branch: `claude/neiso-calibration-complete-w1c-fvbyui` (PR to main when done)
or a fresh lane branch if that one has merged.

## The question the register answers

For each ISO × holdout window (2022; H1-2026), series by series: **is the
holdout year's input set EQUIVALENT to the keeper years' (2023–2025) input
set** — same source, same series, same *granularity*, same *vintage/derivation
recipe* — for every input the keeper recipe actually consumes and every bench
series the verdict scores against? "Present" is not the bar; **parity** is.
The output is a per-ISO table with one row per input:

`input | keeper-years source+grain | holdout source+grain | EQUIVALENT /
DEGRADED / MISSING | materiality for that ISO's price/volume scoring | fix
(fetch/parser/derive) or accepted`

An input is DEGRADED (not equivalent) when any of: sparser time grain
(weekly-anchored vs daily), different derivation vintage (detector/args drift
vs the committed in-sample artifact), proxy/stand-in vintage (wrong-year
eGRID), partial-year coverage, or a source substitution.

## Residual landing checklist (do FIRST — the closing session could not push everything)

The closing session's container may be gone; everything below is either on
the branch already or regenerable from committed scripts. On branch
`claude/neiso-calibration-complete-w1c-fvbyui` as of close: `bc78449` (intake
tooling + Actions workflow + gated scripts + test + README), two prune
commits (`d1dbe9f`/`b311a81` — REVERT these two by restoring both files from
`bc78449`: `git show bc78449:frontend/data/backcast/registry/2026-07-04-neiso-dailybasis-oil-underrun.json`
and the matching `runs/…js`, then push them back — the prune's justification
was scrubbed), the memo with the HELD decision, this handoff, and (if the
closing session got that far) the out-of-sample doc + register updates.

Land whatever of this set is missing from the branch (each regenerates
deterministically; in-sample rows must assert byte-frozen before writing —
the §1.2 table lists every producer command):

- `docs/out-of-sample-results-2026-07.md` — §1.2 NEISO intake record (if
  absent, reconstruct from the §1.2 producer commands + this handoff).
- `docs/gap-register-2026-07.md` — 2026-07-07 addendum (declaration + HELD),
  G-19 row (intake landed; equivalency register REQUIRED; H1-2026 blocked),
  §4 NEISO row (declared; execution held). The memo §6 is the authoritative
  wording source.
- Text data (regenerate per §1.2 producers if absent):
  `campd-unit-outages-NEISO.csv` (committed 968 windows byte-frozen + 325
  appended 2022 rows from `derive_campd_unit_outages.py --iso NEISO --years
  2022 2023 2024 2025`, keeping ONLY its 2022-start rows),
  `algonquin_citygate_daily.csv` (+38 2022 prints, MERGE not replace),
  `neiso_zone_temp_daily.csv` / `neiso_load_weighted_temp_daily.csv` (2022
  extension, in-sample frozen), `calibration_reference.json` (splice ONLY
  `isos.NEISO.2022` from a rebuild; restore all other churn),
  `NEISO_2022_renewable_capacity.csv`, `actual_lmp.json` (+NEISO 2022: DA
  $85.56 / RT $84.92), `frontend/data/backcast/tail/actual_tail.json`
  (+NEISO 2022: DA 27h / RT 117h).
- Binaries: dispatch `.github/workflows/holdout-intake-neiso-2022.yml` on the
  branch once (marker-guarded, idempotent) — lands the six CAMPD 2022
  parquets, the v2 emission-rates merge, the actual-LMP hourly parquet, and
  the SMD xlsx relocation, with a sha256 report in its log.
- Then PR to main (never `git push`; API only). No `manifest.js`/
  `benchmark.js`/`completeness.js` hand-commits (deploy-owned).

## What exists already (start here, do not redo)

- `docs/out-of-sample-results-2026-07.md` §1 (coverage table), §1.1
  (ERCOT+PJM 2022/H1-2026 intake, 2026-07-04), §1.2 (NEISO 2022 intake,
  2026-07-07 — includes the two known NEISO asymmetries below).
- `docs/handoffs/holdout-policy-memo-2026-07.md` (quarantine mechanics,
  Option-2 decision, the `--holdout-authorized` gate).
- The marker-gated intake tooling (all landed): `fetch_campd_unit_level.py
  --holdout-intake`, `curate_emissions_unit_annual.py --holdout-intake`,
  `derive_plant_emissions_v2.py --holdout-intake` (frozen-row merge),
  marker-aware `derive_actual_tail.py`, and the Actions binary lander
  `.github/workflows/holdout-intake-neiso-2022.yml` (fetch-workflow pattern;
  generalize per ISO when needed).
- NEISO 2022 data itself is landed (§1.2) with in-sample rows byte-frozen.
  If the intake branch was never merged, first verify the branch still
  carries: the §1.2 text-data files, the tooling commit (`bc78449`), and
  dispatch the workflow once to land the binaries (CAMPD ×6, v2 parquet,
  actual-lmp hourly parquet, SMD xlsx move, sha256 report in its log).

## Known DEGRADED/asymmetric items to seed the register (verified)

1. **NEISO daily Algonquin gas (`gas-prices/algonquin_citygate_daily.csv`)** —
   weekly-anchored EIA-narrative scrape in ALL years (~30–50 prints/yr; 38
   for 2022). Days between prints fall back to the monthly plateau; this
   understates spiky winters most, and 2022's Jan/Feb blowouts are the
   costliest place to be sparse. Densification leads (owner ordered this
   collection): (a) the 2022-era Weekly Update pages carry MORE prints than
   `scripts/fetch_algonquin_daily_spot.py` extracts — 42/99 pages yielded
   nothing yet `archivenew_ngwu/2022/01_20/` contains e.g. "rose to a weekly
   high of $26.94/MMBtu in advance of the holiday weekend" (2022 phrasing
   differs from 2023+; widen the narrative regexes, keep the `source`
   provenance column); (b) UNVERIFIED: older page formats may carry an
   Algonquin row in the compact "Spot Prices" TABLE (~5 dated prints/page ≈
   250/yr) — check the 2022 pages' table first, it dominates lead (a) if
   present. EIA only (free, citable); ICE/Platts/NGI dailies are paywalled —
   out; constructing dailies from HH_daily + monthly basis is an estimate,
   not a measurement (rule 14) — do not fabricate. MERGE, never replace: the
   fetcher REPLACES the CSV (known trap) — committed 2023–2025 rows are
   keeper inputs and stay BYTE-FROZEN (densifying in-sample years is a
   calibration-owner decision, not this lane); assert-frozen before writing.
2. **NEISO outage-window vintage (`campd-unit-outages-NEISO.csv`)** — the
   committed file does not reproduce from a default-args re-derivation at
   HEAD: fresh `--years 2023 2024 2025` gives 965 windows vs committed 968,
   silently dropping all 34 Merrimack (2364) coal windows and adding 30
   others (Indian Orchard, Dartmouth); `--no-inmerit-filter` gives 1,422 (not
   it either). So 2022 windows (HEAD derivation) are a different detector
   vintage than the committed in-sample windows (unknown args/code vintage,
   last touched PR #1593). The register must adjudicate: reconstruct the
   committed recipe, or re-derive ALL years at a pinned vintage (calibration-
   owner decision — it changes keeper inputs).
3. **H1-2026 (all ISOs)** — publication-blocked: EPA CAMPD Q2-2026 hourly
   unposted; EIA delivered gas May-2026+; `eia_demand_profiles` full-8760
   contract unbuildable from a partial year (F3); reference-year registration
   deferred (F4). Register rows should carry "blocked-until" dates.
4. **ERCOT/PJM 2022 intake (2026-07-04, §1.1)** — present but NOT yet
   equivalency-audited: e.g. the 2022 Waha row is an annual-average basis
   from an EIA narrative (−1.23) vs monthly F923-derived values in-sample;
   PJM 2022 wide extract was rebuilt from the long union while in-sample
   years use the original extract lineage (§1.1 notes 24/22/6 restored
   hours). Grade them with the same DEGRADED/EQUIVALENT lens.
5. **CAISO / MISO / NYISO — zero holdout intake** (G-19 option B). Their
   register rows start as MISSING for every non-multi-year series. Multi-year
   files that already span 2022 (EIA-930 BA hourly files, BALANCE bulk,
   monthly basis, Henry Hub) should be verified-then-marked EQUIVALENT.
6. **Bench-side vintages** — check each ISO's 2022 scoring targets: eGRID2022
   real workbook exists (national); F923 2022 Final Revision exists
   (national, richer than 2025's preliminary); per-ISO LMP actuals for 2022
   are ISO-specific (NEISO: SMD workbook landed; CAISO OASIS ages out —
   verify retrievability; NYISO DAM archives 2023–2025 only on disk; MISO/
   PJM/ERCOT per their §1 rows). EIA-930 storage breakout does not exist for
   2022 in most BAs (C5b/C5c will SKIP — record as an accepted structural
   absence, not a gap to fill).

## Method (per ISO)

1. Enumerate the keeper recipe's actual inputs: read the keeper bundle's
   `run_config.json` + `meta.json` (`frontend/data/backcast/keepers.json` has
   the ids) and the loader map in out-of-sample §1. The Explore-agent map
   pattern used for NEISO (§1.2) is the template: loader → file(s) → holdout
   status → producer (+key needed).
2. For every input, compare grain/vintage/recipe against 2023–2025, not just
   existence. Verify with loader dry-runs / row counts / byte checks — NO LP
   solves of holdout years (the `--holdout-authorized` + marker gate stays;
   in-sample solves are unrestricted but not needed for this).
3. Write the per-ISO table into a new
   `docs/holdout-data-equivalency-register-2026-07.md`, one section per ISO,
   with a top summary matrix (ISO × {2022, H1-2026} → EQUIVALENT n / DEGRADED
   n / MISSING n / blocked). Update G-19 and the register addendum when done.
4. Fixable DEGRADED items (like the AGT parser) may be fixed and landed for
   HOLDOUT years only, under the same byte-frozen in-sample discipline;
   anything touching keeper-year inputs is flagged for the calibration owner
   instead of changed.
5. Owner sign-off per ISO is the exit criterion; only then may a one-shot be
   re-authorized (rule 22 terms in the NEISO memo §4–§5 then apply verbatim).

## Also flagged (in-sample maintenance, separate lanes — do not fix here)

- The NEISO keeper recipe at current main no longer reproduces the keeper's
  registered 2023–25 prices (+0.22/+0.38/+0.68 $/MWh; dual-fuel tranche
  count changed after the keeper's solve commit `7f968f3` — 184/189 at HEAD
  vs 190/195 at the keeper sha). In-sample repro drift, NEISO/main lane.
- `run_calibration.py` (non-`_full`) still has no holdout year gate
  (holdout-policy memo (b)(2) residual).
