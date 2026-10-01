# PRECOMMIT — capx D85-R: the four record repairs

**Session:** capx D85-R, executing the recommendations of
`docs/handoffs/FINDING-capx-d85-key-provenance-2026-09-07.md` §5 — repairs **(ii)** and
**(v-a)/(v-b)/(v-c)**. Owner ruling **Q59**'s follow-on; capx ledger **§0bc.3(c)**.
**Model:** Opus. **DATA PROFILE:** code. **Branch:** `claude/capx-d85r-record-repairs-wyrs3y`,
fresh off `origin/main` at `12e71b89` (2026-09-07).

**Written BEFORE any edit.** Everything below — the expected exception membership, the expected
census output, the drift against D85 — was measured at `12e71b89` on an unmodified tree and is
recorded here so no number in the close can have been chosen to fit a result.

---

## 0. The refusals this lane inherits, restated so they bind

D85 refused (iii) re-registering the lagging field and (iv) rewriting any committed
`cache_key`, and this lane inherits both. **Nothing here changes a committed key, bundle,
registration, `_CACHE_KEY_OPTIONAL_FIELDS` entry, `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`
entry, or `solve_surface_declared.py` row, and nothing is solved.** If a key rewrite turns out
to be the right repair, that is an owner card, not this lane's act.

---

## 1. The census at `12e71b89`, and the drift against D85

D85 measured `214 / 169 / 30 / 15` at `db0c1d85`. This lane measures, on an unmodified tree:

| | D85 (`db0c1d85`) | **D85-R (`12e71b89`)** |
|---|---:|---:|
| committed `run_config.json` | 214 | **223** |
| reproduce recorded key | 169 | **179** |
| no recorded key | 30 | **29** |
| **do NOT reproduce** | **15** | **15** |

**Net +9 is 11 added and 2 pruned**, all measured, none touching the mismatch set:

* **added (11):** `results/calibration/spp43_screened_B`; and ten
  `results/scn-campaign-policy-2026-09-06/…` policy configs — CAISO `ALL-CLEAN`,
  `CAP-STATE-TIGHT`, `CES-P20+VOL-HI`, `CES-P60`; MISO `ALL-CLEAN`, `CARB-LO`, `CARB-MID`,
  `CES-P20+VOL-HI`; PJM `CAP-STATE-TIGHT`, `CES-P20+VOL-HI`.
* **pruned (2):** `results/calibration/spp40_baseline_B`, `results/calibration/spp42_crosswalk_B`
  (superseded by the spp43 screen).

**The 15 mismatching files are SET-EQUAL to D85's 15** (checked, not asserted). The COUNTS are
measurements and will drift again; **ZERO UNKNOWN is the gate.**

Class (c) also moved, as D79 designs it to: `reproduces_at_declaration_only` is now
**CAISO 21 (was 17) · ERCOT 29 (unchanged)** = **50 records (was 46)**, against
`moved_rows` = ERCOT `{NUCLEAR_MONTHLY_CF_BY_YEAR}`, CAISO `{NUCLEAR_MONTHLY_CF_BY_YEAR,
STATE_CARBON_PRICE_BY_ISO}`.

---

## 2. Repair 1 — the checked exception record: PRE-REGISTERED MEMBERSHIP

Exactly **15 entries**, by `run_config` path and class. This is the expected membership; the
gate is that the mismatch set at HEAD equals it, with nothing unclassified on either side.

| # | run_config | ISO | recorded key | class | recipe |
|--:|---|---|---|---|---|
| 1 | `results/ff-t1f-s123/verify` | MISO | `587dc5b32ba71ceb` | `pre-ledger-flip` | drop R-A pair |
| 2 | `results/ff-t1f-s6-pjm/ledger` | PJM | `31a19d815fa319a7` | `pre-ledger-flip` | drop R-A pair |
| 3 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31` | NEISO | `a4b11ef4aaa1be35` | `pre-ledger-flip` | drop R-A pair |
| 4 | `…/bau-prera-2026-08-31/fc6/arms/base` | NEISO | `0365174ab16cc318` | `pre-ledger-flip+split-root` | drop R-A pair + fold under D21/D26 roots |
| 5 | `…/bau-prera-2026-08-31/fc6/arms/carbon25` | NEISO | `7924eccc695c0168` | `pre-ledger-flip+split-root` | same |
| 6 | `…/bau-prera-2026-08-31/fc6/arms/carbon_plus25` | NEISO | `7784d408fc955785` | `pre-ledger-flip+split-root` | same |
| 7 | `…/bau-prera-2026-08-31/fc6/arms/gaspm5` | NEISO | `1de43201e2040f7f` | `pre-ledger-flip+split-root` | same |
| 8 | `…/bau-prera-2026-08-31/fc6/arms/gasup150` | NEISO | `13f9357712250600` | `pre-ledger-flip+split-root` | same |
| 9 | `results/ff-t3-neiso-golden/bau` | NEISO | `706e7ba8e6582d42` | `lag` | un-drop `caiso_offer_surface_measured_ungrounded` |
| 10 | `…/bau/fc6/arms/base` | NEISO | `706e7ba8e6582d42` | `lag` | same |
| 11 | `…/bau/fc6/arms/carbon_plus25` | NEISO | `f7cced798488ddac` | `lag` | same |
| 12 | `…/bau/fc6/arms/gaspm5` | NEISO | `2d017ed9675aa386` | `lag` | same |
| 13 | `…/bau/fc6/arms/gasup150` | NEISO | `65662ca117959ee5` | `lag` | same |
| 14 | `results/hindcast/miso-2021-2025-realized-t1h-d27` | MISO | `501b5f64b8adf8d4` | `lag` | same |
| 15 | `tests/golden/ercot_2026_2040.run_config.json` | ERCOT | `0d6f2710f8dedf56` | `vintage+resolved` | vintage `f0f7c67d` rules + ERCOT `default_scenario_overrides` |

Class totals: `lag` 6 · `pre-ledger-flip` 3 · `pre-ledger-flip+split-root` 5 ·
`vintage+resolved` 1 · **unclassified 0.**

### The gates the checker enforces

| gate | fails when | needs network? |
|---|---|---|
| **G1 UNKNOWN** | a mismatch at HEAD is not in the list (a **sixteenth**) | no |
| **G2 STALE** | a listed entry now REPRODUCES under HEAD rules (dead scaffolding, rule 26) | no |
| **G3 RECIPE** | a listed entry does not reproduce its recorded key under its own recorded recipe | only row 15 |
| **G4 PRESENT** | a listed entry's `run_config.json` is no longer committed (pruned bundle ⇒ delete the entry) | no |
| **G5 KEY** | a listed entry's `recorded_cache_key` ≠ the file's own `cache_key` | no |

**G1 and G2 are the load-bearing gates and both are fully offline.** Only row 15's recipe
(`vintage+resolved`) needs the `f0f7c67d` blob; the checker fetches it at depth 1 when missing
and, with `--no-fetch` on an offline runner, reports that one recipe `unverified` while G1/G2/G4/G5
still bind. That degradation is declared here, not discovered later.

### Expected census output after repair 1 (at `12e71b89`)

```
223 committed run configs at 12e71b89
  179 reproduce · 29 no recorded key · 15 mismatch
  15 KNOWN (listed exceptions, every recipe verified) · 0 UNKNOWN
```

---

## 3. Repair 2 — fold roots in the run record. Expected effect: **none, anywhere**

`pipeline/persist.environment_block()` gains two additive keys —
`cache_key_path_roots` (what `_cache_key_path_roots()` returned) and `market_sim_data_root`
(the raw `MARKET_SIM_DATA_ROOT`, `""` when unset). Pre-verified inert:

* `cache_key()` does not read the environment block, so **no key moves**;
* `--reuse-solved` ignores the block (`tests/regression/test_reuse_solved.py::test_environment_block_is_ignored_by_reuse`);
* `replay_keeper._warn_on_environment_mismatch` compares only `python_version`, `platform` and
  `packages` — new keys are not compared, so no new warning;
* `audit_keepers.E11_META_PROVENANCE` contains `"environment"`, so the block is **excluded** from
  the E11 recipe block, and `tests/scoring/test_audit_keepers_lineage.py` pins that set against
  `replay_keeper._IGNORE` — neither moves.

Expected: **zero determinations, zero gates, zero keys move.** Only bundles solved *after* this
lands carry the new keys; no committed record is rewritten.

## 4. Repair 3 — resolved config in the golden writer. Expected effect: **none until a reseed**

`scripts/golden_forecast_bands.py` writes `run_config.json`'s `scenario_config` from
`dataclasses.asdict(config)` — the **request** — while the runner hashed the **resolution**
(ERCOT's `default_scenario_overrides = {"scarcity_price_overlay": True}`). It will instead read the
solve's own `run_dir/config.yaml`, the same provenance rule
`scripts/lib/run_record.write_run_config` states ("the pre-solve object is a REQUEST and the
on-disk dump is the RESOLUTION").

`seed` is owner-gated (`REGEN_POLICY` + the §2.1b schedulability guard + the D-7 waiver), so this
lane **does not reseed** and `tests/golden/ercot_2026_2040.run_config.json` is untouched. Expected:
`test_golden_fixture_present_and_well_formed` and
`test_golden_fixture_config_identity_is_current` both unchanged (the identity test reads
`cache_key` and `scenario_config` field-wise; neither moves without a reseed), and the waiver is
untouched.

## 5. Repair 4 — both keys in the census. Pre-measured split

The instrument already computed both keys per row but its summary named neither. Measured now,
over the 223:

| | count |
|---|---:|
| reproduce under **both** constructions (ISO's surface still at declaration) | **129** |
| reproduce **only** with the surface **at declaration** (D79's designed re-key) | **50** (CAISO 21 · ERCOT 29) |
| reproduce **only** with the **live** surface | **0** |
| reproduce under neither (the 15) | **15** |
| no recorded key | **29** |

So `179 = 129 + 50`. The census will state which key "reproduces" means and report both.
**The 50 are not a defect and are not repaired** — re-declaring the moved ERCOT/CAISO rows is
D85 §5 row (vi), explicitly **not this lane's call**.

---

## 6. Stop gates armed for this session

1. A **sixteenth** unclassified mismatch → STOP and report; a new finding, not a list entry.
2. Any repair that would change a committed key, bundle, registration, flip entry or surface
   declaration → STOP.
3. The exception check passing while a listed config reproduces → the CHECK is wrong; fix the
   check, never the list.
4. Any determination or gate moving anywhere → STOP. This is record hygiene.

## 7. Declared NOT in scope

* No solve, no registration, no dashboard touch, no matrix stamp (rule 28: no mechanism tested).
* No `ScenarioConfig` field added or changed; no CI workflow added (the repo bans per-task
  workflows) — the gate rides an existing test lane.
* D83 / D84 untouched.
* The golden identity test's own request-vs-resolution asymmetry (it compares the seeded
  **resolved** key against a **request** hash at HEAD) is OBSERVED and reported in the close,
  **not changed**: altering it would move a test's semantics under an owner-signed waiver.
