# Shared-key group fixture (capx D24 §4.5)

Three committed `run_config.json` pairs, each pair sharing one `cache_key`, that
reproduce the D24 §4.5 invariant `tests/unit/results/test_cache_config_agreement.py`
asserts: `results.cache.config_disagreements` (owner ruling Q20, option (c′))
**refuses exactly the two true positives and permits the designed case**, where
strict equality — option (c) — would refuse all three.

## Why this fixture exists

The test used to build its corpus live, from `git ls-files '*run_config.json'`.
Rule 15 `[R-DASHBOARD]` as amended 2026-09-05 (keeper-only retention) then
deleted the corpus out from under it. In PR #4808 (merge `95739d60`):

| commit | what it deleted | `run_config.json` deleted |
| --- | --- | --- |
| `e090fc1f` | `results/calibration` pruned to keeper bundles (18 unmapped bundles) | 17 |
| `9fd5e5b3` | 109 unregistered `results/hindcast` dirs, 36 superseded sidecars, `ffr*` lane outputs | 101 |

The census went **193 → 72** tracked `run_config.json` across that merge, and the
shared-key groups (`>1` member at one key) went **20 → 7**. One of the two true
positives lost a member, so its key stopped being a group at all:
`f061b2646bfaac8b`'s `-d12c-armed` side was deleted by `9fd5e5b3`, leaving only
`-d4m`. The test's floor (`>= 14` groups) and its exact refused-key set both went
red — see `docs/handoffs/FINDING-y23-cache-agreement-fixture-2026-09-06.md`.

A census over `results/` is a **retention hazard**: rule 15 requires the corpus
to shrink, so an invariant that reads it can only survive by accident. This
fixture moves the invariant's object under `tests/`, where retention does not
reach. The live-corpus replay is kept as a second, skip-when-sparse pass.

## Provenance

Every file is the `scenario_config` of a real committed `run_config.json`,
recovered **verbatim** from `d6891edd600611d04679c12fee732a02fd60cc16`
(= `95739d60^`, the tree immediately before the prune merged). The record
wrapper keeps only `cache_key`, `timestamp`, `iso`, `kind`, plus the
`source_path` / `source_blob` provenance; `git`, `environment`, `run_dir`,
`scenario_config_source`, `solved_years` and `bridged_years` are dropped because
nothing in the comparison reads them.

| group | file | source blob | source path | fate on `main` |
| --- | --- | --- | --- | --- |
| `07e416f3f8072e7c` | `01-neiso-2023-2027-crossover-capxd14.json` | `b86cc1484195cecdcbe50710fd0caf701b51c233` | `results/hindcast/neiso-2023-2027-crossover-capxd14/run_config.json` | alive |
| `07e416f3f8072e7c` | `02-neiso-2023-2027-crossover-rcrepair.json` | `53be92877aede89160f83a5b3fb11147ac8f67c0` | `results/hindcast/neiso-2023-2027-crossover-rcrepair/run_config.json` | alive |
| `f061b2646bfaac8b` | `01-ercot-2021-2025-realized-t1h-d12c-armed.json` | `5830fa724ed1009e82efb8a350a118a3762c7434` | `results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed/run_config.json` | **deleted** by `9fd5e5b3` |
| `f061b2646bfaac8b` | `02-ercot-2021-2025-realized-t1h-d4m.json` | `5c5219816fa5d7154ebd635c4505139dbe3fee0c` | `results/hindcast/ercot-2021-2025-realized-t1h-d4m/run_config.json` | alive |
| `5925e67c572a910f` | `01-neiso-2021-2025-realized-t1h-d37-control.json` | `4733f5cc7980f9cd49933487799ccc79ee8a333e` | `results/hindcast/neiso-2021-2025-realized-t1h-d37-control/run_config.json` | **deleted** by `9fd5e5b3` |
| `5925e67c572a910f` | `02-neiso-2021-2025-realized-t1h-d45r-datesoff.json` | `c8308393afb5ffb92ba70081ce78fdb25fad3ed2` | `results/hindcast/neiso-2021-2025-realized-t1h-d45r-datesoff/run_config.json` | **deleted** by `9fd5e5b3` |

Re-recover any of them with
`git cat-file blob <source blob>`, or `git show d6891edd:<source path>`.

## What each group pins

The comparison runs **oldest-as-stored** (the `NN-` filename prefix is that
order, and `timestamp` is what the test sorts on), which is the direction a
cache hit takes. The requesting side is restricted to fields `ScenarioConfig`
still has, because a run today cannot ask for a field that no longer exists.

| group | form | absent-from-stored | differing-common | strict (c) | (c′) |
| --- | --- | ---: | ---: | --- | --- |
| `07e416f3f8072e7c` | **D24 §4.2** — absent vs armed default | 5 | 0 | refuse | **REFUSE** |
| `f061b2646bfaac8b` | **D24 §4.1** — differing common field | 0 | 2 | refuse | **REFUSE** |
| `5925e67c572a910f` | designed — ordinary schema growth | 15 | 0 | refuse | **permit** |

Both refusals name the same pair, and only that pair:
`['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']`.

* `07e416f3f8072e7c` is the nastier form: the stored config predates both fields
  entirely (760 fields vs 765), this one carries them at a default that has
  since been **armed** to `True`, and neither value is in the key — nothing in
  the pair of files looks like more than schema growth.
* `f061b2646bfaac8b` is the plain form: both configs carry both fields, stored
  `False` against wanted `True`, and the key dropped them because each sat at
  whichever value was the default on the day it was hashed.
* `5925e67c572a910f` is what decides (c′) over strict (c): 15 fields the stored
  config predates (769 → 784), **every one of them** at the value its absence is
  equivalent to. Strict equality refuses this bundle; (c′) serves it, because it
  is the same dispatch.

## Why the configs are kept whole

The invariant is "refuses on **exactly** two fields, out of ~765". Trimming the
payloads to the fields that differ would make that assertion circular — it would
assert the answer the trimming chose. The recovered payloads are therefore
verbatim, at ~31 KB each (190 KB total), and the count of fields on each side
is itself evidence: 760 / 765 / 765 / 765 / 769 / 784 is the schema growth the
(c′) rule exists to tolerate.

Checkout-absolute paths are left as recovered. `config_disagreements` folds them
to sentinels on both sides before comparing (`_normalize_cache_key_paths`), and
where a fixture's root does not match the checkout the two sides still carry the
same string, so the comparison is checkout-independent either way.
