# FINDING closeout-nuclear-rows — PJM / NWPP / SPP 2019–2022 measured nuclear CF rows (zero LP)

Lane `claude/closeout-nuclear-rows`, 2026-10-03. Owner ruling **R-35** (2026-10-03):
*"Data PR now; re-solve with each ISO's next solve"*. **No LP, no shard, no
promotion.** Desk: session_01ALecU5Wjde4tkbLrnMExT9.

Probe: `scripts/probes/_closeout_nuc_rows.py`. Output:
`docs/records/governance/closeout-2026-10/nuclear-rows/nuc_rows.{csv,out.txt}`.

## 0. The defect

`constants.NUCLEAR_MONTHLY_CF_BY_YEAR` carried only 2023–2025 for PJM, NWPP and SPP.
Their keepers' 2019–2022 legs therefore read the forecast fallback in
`fleet.arrays._nuclear_monthly`: `NUCLEAR_MONTHLY_CF[iso] × (1 − EFORD)`, the same
CF every year. The signature is model nuclear that is identical across years:
PJM 271.90 TWh in 2021 and 2022, NWPP 8.44 in 2020–22, SPP 15.80 in all four
years (closeout-SOCO-2 FINDING §d). None of the three keepers arms an NRC daily
overlay.

MISO and ERCOT run under an armed NRC overlay and are out of scope (an overlay
question, no change here). SOCO's 2019–22 rows are in `claude/closeout-soco-2`
and are not duplicated here: this PR touches the PJM, NWPP and SPP rows only.

## 1. The derive (rule 23: coverage extension, not a re-derive)

The rows come from the same frozen script, `scripts/data/derive_nuclear_monthly_cf.py`.
It reads the same source as the committed rows: EIA-923 Page 1 monthly net
generation (`data/raw/_processed-legacy/eia923_monthly_generation.parquet`) over
the model fleet's nuclear plants. The source data did not change. These are new
years of the measured series.

- `--isos {PJM,NWPP,SPP} --years 2023 2024 2025 --check` printed *"committed table
  matches the EIA-923 derivation"* for each ISO before the edit. Every existing
  value is byte-unchanged.
- After the edit, `--years 2019 … 2025 --check` passes for all three ISOs.

| ISO | Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PJM | 2019 | 1.00 | 0.99 | 0.87 | 0.87 | 0.96 | 0.98 | 0.99 | 0.98 | 0.95 | 0.88 | 0.93 | 1.00 |
| PJM | 2020 | 1.00 | 0.97 | 0.90 | 0.88 | 0.93 | 1.00 | 0.99 | 0.99 | 0.96 | 0.90 | 0.96 | 1.00 |
| PJM | 2021 | 1.00 | 1.00 | 0.87 | 0.83 | 0.89 | 0.99 | 0.97 | 1.00 | 0.97 | 0.88 | 0.93 | 1.00 |
| PJM | 2022 | 1.00 | 0.99 | 0.92 | 0.82 | 0.93 | 0.98 | 0.99 | 0.97 | 0.94 | 0.84 | 0.94 | 1.00 |
| NWPP | 2019 | 0.99 | 1.00 | 1.00 | 0.99 | 0.28 | 0.30 | 0.98 | 0.99 | 0.99 | 1.00 | 1.00 | 1.00 |
| NWPP | 2020 | 1.00 | 0.90 | 1.00 | 1.00 | 0.92 | 0.51 | 0.89 | 0.99 | 0.99 | 1.00 | 0.96 | 1.00 |
| NWPP | 2021 | 1.00 | 0.99 | 0.99 | 0.90 | 0.18 | 0.37 | 0.99 | 0.99 | 0.98 | 0.99 | 1.00 | 0.74 |
| NWPP | 2022 | 1.00 | 0.98 | 1.00 | 1.00 | 0.99 | 0.78 | 0.98 | 0.98 | 0.99 | 1.00 | 1.00 | 1.00 |
| SPP | 2019 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.81 | 0.41 | 0.90 | 1.00 |
| SPP | 2020 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | 0.68 | 0.97 | 1.00 |
| SPP | 2021 | 1.00 | 1.00 | 0.88 | 0.41 | 0.70 | 0.86 | 1.00 | 0.93 | 1.00 | 1.00 | 1.00 | 0.99 |
| SPP | 2022 | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 | 0.90 | 0.94 | 0.91 | 0.10 | 0.38 | 0.98 |

The dips are each fleet's real refuelling cadence:
- NWPP: Columbia's biennial May–Jun outage in 2019 and 2021, plus a shorter
  2020 outage and a 2021 Dec dip.
- SPP: Wolf Creek in fall 2019 and 2022; Cooper in fall 2020 and spring 2021.

The fallback pattern smears those outages into a fixed seasonal shape.

## 2. Zero-LP verification table

The columns are defined as follows:
- **Fallback CF / derived CF** are annual, energy-weighted over the derive's fleet
  (online pmax × hours).
- **Implied TWh** = Σ CF × online fleet pmax × hours. This is the availability
  energy the LP may dispatch.
- **EIA-923** is the same plants' uncapped net generation.
- **Keeper gap** = keeper model nuclear − bench (`classFull`), from the
  closeout-SOCO-2 §d table.
- **Implied gap after** = keeper gap + (derived − fallback implied TWh). This is a
  first-order estimate that assumes nuclear runs at its availability cap.

| ISO | Year | Fallback CF | Derived CF | Fallback TWh | Derived TWh | EIA-923 TWh | Derived − EIA-923 | Keeper gap | Implied gap after |
|---|---|---|---|---|---|---|---|---|---|
| PJM | 2019 | 0.951 | 0.950 | 272.19 | 272.00 | 272.70 | −0.71 | −0.93 | −1.12 |
| PJM | 2020 | 0.951 | 0.957 | 272.95 | 274.70 | 275.75 | −1.05 | −3.70 | −1.95 |
| PJM | 2021 | 0.951 | 0.944 | 272.19 | 270.28 | 271.69 | −1.41 | +0.21 | −1.70 |
| PJM | 2022 | 0.951 | 0.943 | 272.19 | 270.09 | 270.59 | −0.49 | +1.31 | −0.78 |
| NWPP | 2019 | 0.837 | 0.876 | 8.44 | 8.84 | 8.87 | −0.03 | −0.34 | +0.05 |
| NWPP | 2020 | 0.838 | 0.931 | 8.47 | 9.41 | 9.43 | −0.02 | −0.99 | −0.05 |
| NWPP | 2021 | 0.837 | 0.842 | 8.44 | 8.49 | 8.51 | −0.02 | −0.07 | −0.02 |
| NWPP | 2022 | 0.837 | 0.975 | 8.44 | 9.83 | 9.85 | −0.02 | −1.41 | −0.02 |
| SPP | 2019 | 0.904 | 0.926 | 15.41 | 15.78 | 16.20 | −0.42 | −0.40 | −0.03 |
| SPP | 2020 | 0.904 | 0.964 | 15.45 | 16.47 | 16.77 | −0.30 | −0.97 | +0.05 |
| SPP | 2021 | 0.904 | 0.898 | 15.41 | 15.29 | 15.46 | −0.16 | +0.34 | +0.23 |
| SPP | 2022 | 0.904 | 0.849 | 15.41 | 14.47 | 14.60 | −0.13 | +1.20 | +0.26 |

**Reading.** The derived rows close the availability-energy gap to the derive's
own tolerance, which is the 1.0 monthly clip:
- NWPP: −0.02 to −0.03 TWh.
- SPP: −0.13 to −0.42 TWh. The two units run above model pmax in cold months.
- PJM: −0.49 to −1.41 TWh. This is the cost of the cap on a 32.7 GW fleet; the
  table's own comment documents ~0.5–1.0 TWh a year for 2023–25.

On the keeper-gap view, Σ|gap| moves as follows:
- NWPP: 2.81 → 0.14 TWh.
- SPP: 2.91 → 0.57 TWh.
- PJM: 6.15 → 5.55 TWh.

**PJM honesty note.** PJM 2021 and 2022 had keeper gaps of +0.21 and +1.31 TWh
because the fallback CF happened to sit above that year's measured outcome. With
the measured rows the first-order gaps become −1.70 and −0.78 TWh. Those gaps are
one-signed and clip-driven, the same sign as 2023–25. For 2021 that is a
**larger** magnitude than before. Rule 14 [R-ACCURATE] governs: a measured input
is not reverted because the year-invariant estimate landed closer by accident.
The remaining PJM residual is (a) the clip and (b) the keeper dispatching
0.3–0.9 TWh below its fallback availability, which is a dispatch matter and not
a data one.

**TMI-1 / Crane (EIA 8011), desk addition, measured; stopped before repair.**

What the registry says: `NUCLEAR_DORMANT_UNTIL[8011] = 2027`, the first year the
unit is expected to generate. Both consumers drop the unit in every backcast year
before 2027:
- the derive excludes it from fleet and numerator;
- `fleet.arrays._nuclear_monthly` zeroes its availability.

What actually happened: EIA-923 Page 1 shows 8011 at about 0.57–0.63 TWh a month
from January to August 2019. September 2019 is 0.351 TWh, a partial month. The
first zero-generation month is **October 2019**, giving **5.21 TWh** for 2019. The
NRC status row (`data/raw/nuclear-license-status/pjm.csv`) records "permanently
shut **2019-09-26**".

What the keeper leg loses: about **nothing**. The PJM keeper arms
`nuclear_dormancy_defers_to_vintage_exit` and `mid_vintage_exit_carry` (both
`True` in `w0_pjm_span/run_config_2019.json`). Under them, a unit the 2019 EIA-860
vintage records as a mid-year exit is not zeroed, and its retirement mask removes
it after the exit month (PJM-NEXT-2 card 3, rule 19). That is why the keeper's 2019
nuclear is 276.99 TWh, about 4.8 TWh above the 272.19 TWh the derive-fleet
fallback implies.

With the new measured row, the LP applies the row's CF to TMI-1 too, since the CF
is applied uniformly to every nuclear row. At the 2019 row's CF, TMI-1 has about
5.02 TWh of Jan–Sep availability against the 5.21 TWh measured. The §2 PJM 2019
implied gap (−1.12 TWh) is already computed keeper-to-bench with TMI-1 on both
sides.

Carrying TMI-1 in the derive's 2019 fleet as well (through September) would move
the 2019 row by only two cells: Mar 0.87 → 0.88 and Sep 0.95 → 0.94.

Why the requested one-date repair was not made: one `until` year cannot express
"ran January–September 2019, dormant October 2019 through 2026".
- Setting it to 2019 would re-admit TMI-1 at full availability for 2020–2026.
  That is the ~6.5 TWh/yr phantom this entry was created to remove.
- The LP already carries the 2019 operation through the vintage-exit deferral.
  A second mechanism for it would stack (rule 19).
- Teaching the derive the operating window means changing its fleet definition,
  for example reading the mid-vintage-exit units. That is a code change beyond the
  one registry date the desk authorised, so this step stopped and was reported. No
  registry value changed.

## 3. Cache-key / SolveEpoch consequence

| ISO | Mechanism that re-keys | Scope |
|---|---|---|
| PJM | `NUCLEAR_MONTHLY_CF_BY_YEAR["PJM"]` is **declared** in `solve_surface_declared.DECLARED`; its live hash moves off the frozen line (`moved_rows("PJM")` gains it, `fc29510f69d6bb45`), **and** SolveEpoch `2026-10-03b` | backcast PJM (epoch + row); forecast PJM also re-keys through the declared row, though forecast years never read 2019–22 (inert re-key, unavoidable for a declared by-ISO table) |
| NWPP | row undeclared → SolveEpoch `2026-10-03b` only | backcast NWPP |
| SPP | row undeclared → SolveEpoch `2026-10-03b` only | backcast SPP |

The epoch id is **`2026-10-03b`**, because `2026-10-03a` on `main` is the
NWPP-anchor lane's. **Collision flagged to the desk:** `claude/closeout-soco-2`
also declares `2026-10-03a` (SOCO) on its unmerged branch. When it merges `main`
it must take the next free letter, since epoch ids are append-only (rule 26).
The ledger entry is in `results/cache.py` ("Epoch 2026-10-03b").
`check_cache_key_registration.py --base origin/main` is clean.

**What is not invalidated:**
- every other ISO;
- NWPP and SPP forecasts;
- the PJM/NWPP/SPP 2023–25 physics (rows byte-identical; only the key moves).

## 4. Keeper replay consequence

The three keepers' recorded `run_config_<Y>.json` cannot carry these rows. The
table is a `constants.py` registry value, not a `ScenarioConfig` field, so the
rows appear only in each record's `solve_surface` block:
- `w0_pjm_span` (PJM, keeper `2026-10-02-w0-pjm-fix2`): recorded `moved` has no
  `NUCLEAR_MONTHLY_CF_BY_YEAR`; recorded epochs `[2026-10-02c, 2026-10-02d]`.
- `nwppnext22b_span` (NWPP, keeper `2026-10-03-nwpp-next-22b-w0`): recorded
  epochs `[2026-10-02c, 2026-10-02d]`.
- `w0_sppr_span` (SPP, keeper `2026-10-02-w0-spp107r`): recorded epochs
  `[2026-10-02e]`.

**Preflight 0d / replay fidelity does not see this change, by construction.**
- `promote_keeper.ensure_replay_recipe` → `replay_recipe.replay_config_diffs`
  diffs the resolved `ScenarioConfig` against the recorded one.
- `_registered_after_solve` and `replay_keeper.flipped_default_overlay` only
  reason about `ScenarioConfig` fields (fields added after the solve, and
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`).
- A constants-table extension is neither, so 0d's diff stays empty and 0d passes.
  It is right to pass: the recipe did reproduce.

**A replay of any of the three keepers at HEAD would therefore DIFFER from the
recorded bundle in 2019–2022.** The replay rebuilds the same recipe, but
`_nuclear_monthly` now finds a measured row, so nuclear availability moves by
−1.9 to +1.8 TWh per ISO-year (§2 derived − fallback). Everything downstream
(merit order, prices, emissions) moves with it.

The guard that keeps this from being silent is the cache key, not 0d:
- PJM: the declared row moves, plus epoch `2026-10-03b`.
- NWPP and SPP: the epoch.

So a replay or re-solve at HEAD gets a fresh key and is never served the recorded
bundle. `check_key_provenance.py --no-fetch` was run before and after the edit.
Both runs exit 0 with identical counts: 224 run configs, 171 reproduce, 33
mismatch, 0 SOLVE-EPOCH-MOVED. Every failure is a shallow-clone
`G1_LAG_UNVERIFIED` on `ff-t3-neiso-golden`, present on `main` too. The only
difference in the output is PJM's `surface rows off declaration` gaining
`NUCLEAR_MONTHLY_CF_BY_YEAR: fc29510f69d6bb45`. No guard was weakened. The 2023–25 legs re-key with byte-identical nuclear input. Per R-35
the re-solves happen in each ISO's next lane solve, not here.

## 5. Recurrence guard

`tests/unit/config/test_nuclear_cf_coverage.py` checks every year any registered
backcast run carries, for all nine ISOs. Each year must have a
`NUCLEAR_MONTHLY_CF_BY_YEAR` row, or the ISO's keeper must record an armed
`nuclear_unit_availability` / `ercot_nuclear_unit_availability` in its
`run_config.json`.

- The test fails closed: a missing keeper record or config raises, and the
  failure names every uncovered ISO-year.
- Against `main`'s table it fails on exactly the 12 PJM/NWPP/SPP ISO-years.
- SOCO 2019–22 is a named `_PENDING_ROWS` allowance for the closeout-SOCO-2 lane.
  A companion test fails once those rows land, so the allowance must be deleted
  in that merge and cannot outlive it.

## 6. Docs and matrix

- `docs/parameter-citations.md` carries no entry for this table, so none is added.
  The citation lives in the `constants.py` comment block for each ISO.
- Mechanism matrix: no cell moves (data coverage, not a mechanism). No PJM, NWPP
  or SPP cell's evidence claims the fallback is measured, so no correction is
  prepended.
