# Authoritative `inputs/` dead-path re-inventory (2026-07-26)

Closes the plan's §10 verify-first item — *"the `inputs/` dead-path inventory
(10/18/34 — produce one authoritative list with resolution semantics)"* — and
the dead-path half of §6-E (Workstream E, scripts/ phase 2).

## Why the three audit counts disagreed

They counted different things at different times, and none of them was wrong
when it was taken:

* The counts predate waves 1–5D. Most `inputs/` call sites had **already** been
  routed through `config/paths.py` by the time this re-inventory was taken; what
  they left behind is a *comment* at each site recording the W1 relocation.
* The larger counts include those provenance comments (and `docs/`,
  `scripts/archive/`, `scripts/probes/`) as hits. Those are load-bearing history,
  not defects — CLAUDE.md's own directory map documents the same relocation.
* Only the smallest count approximated *live path expressions*.

**Method used here** (re-measured 2026-07-26, not inherited): grep the token
`inputs/` and the path segment `"inputs"` across every tracked `*.py` / `*.sh` /
`*.yml` / `*.yaml` / `*.json` / `*.toml` / `Makefile`, **excluding** the frozen
and generated trees (`scripts/archive/`, `scripts/probes/`, `results/`,
`docs/sessions/`, `scope2-lce-portfolio/`, `frontend/data/`) — 1,166 files
scanned — then classify every hit by whether it *resolves a path at runtime*.

**Result: 13 hits across 7 files; 3 live defects.** That is the honest number,
and it is small because waves 1–5D did the bulk of the work.

## The inventory, with resolution semantics

### A. Live defects — fixed in this change

| # | Site | Semantics | Resolution |
|---|---|---|---|
| A1 | `scripts/render_calibration_html.py` `_actual_lmp_table` | Second candidate `REPO / "inputs" / "calibration" / "actual_lmp.json"`, kept "as a fallback so an older checkout still resolves". **Unreachable**: W1 was a pure `git mv`, so no post-W1 checkout has an `inputs/` root at all. It was also the *only* one of ~10 `actual_lmp.json` readers carrying the fallback — every other reader already resolved to `CALIBRATION_DIR` alone. | Fallback deleted, not zeroed (rule 26 `[R-DELETE]`); resolves through `paths.CALIBRATION_DIR` only. |
| A2 | `tools/launcher.py:279` | User-facing empty-state string `— no tranche CSVs in inputs/ —`. The *discovery* code was already fixed (it globs `REFERENCE_DIR` + `configs/`), so the UI pointed users at a directory that no longer exists. | Text now names the two directories actually searched. |
| A3 | `src/market_sim/config/paths.py` `INPUTS_DIR` | `DATA_ROOT / "inputs"`, self-declared "retained for backward compatibility". **Zero consumers repo-wide** (verified incl. `docs/`, `archive/`, `probes/`; the `scope2-lce-portfolio` `DEFAULT_INPUTS_DIR` hits are that sub-project's own unrelated tree). | Removed. A dead path constant that still resolves is a re-armable dead path — rule 26 `[R-DELETE]`. |

### B. Stale prose — repaired in this change

| # | Site | Issue |
|---|---|---|
| B1 | `scripts/render_calibration_html.py` `_actual_lmp_hourly_by_hour` docstring | Asserted that `derive_ordc_overlay`'s `CAL_DIR` "still points at the pre-W1 `inputs/calibration` tree". It does not — that was repaired earlier. Claim dropped. |

### C. Routed through `config/paths.py` — done in this change

| # | Site | Note |
|---|---|---|
| C1 | `scripts/data/derive_ordc_overlay.py:59` | `CAL_DIR = REPO / "data" / "raw" / "_validation-source"` → `paths.CALIBRATION_DIR`. Resolved path is byte-identical; this is the exact file B1 names, so the two travel together. |

### D. Adjudicated — correct as-is, annotated not changed

| # | Site | Why it stays |
|---|---|---|
| D1 | `scripts/data/derive_offer_curve_jacobian.py:952` | `git diff --quiet <sha0> <sha1> -- src/ inputs/ data/`. This is a **git pathspec over history**, not a filesystem path: the sha pair can straddle W1, where the tree really did have an `inputs/` root. A pathspec matching nothing is a no-op for post-W1 pairs, so keeping it costs nothing while dropping it would blind the change-detector to pre-W1 input changes. Rationale added to the docstring so it is not "cleaned up" by a later sweep. |
| D2 | `scripts/export_lce_lmp.py` (3 hits) | `scope2-lce-portfolio/data/inputs/` is the **sub-project's own** inputs directory, unrelated to the retired repo-root `inputs/`. Not dead. |

### E. Load-bearing provenance prose — left exactly as-is

The remaining hits are W1-relocation comments of the form *"the pre-W1
`inputs/raw-data` path was removed by the relocation"*, sitting beside call
sites that already resolve correctly (`paths.py` module docstring and lines
51–62; ~20 comments across `scripts/data/*`; `validate_neighbor_price.py:62`;
`export_iso_bin_assignments.py:75`; `export_tranche_config.py:172`;
`tag_mixed_plants.py:46`; `tools/launcher.py:33`;
`derive_offer_curve_jacobian.py:299/945/1045`). These are the provenance record
for a completed migration and must not be swept.

## The three §6-E-named items, re-verified

All three were **already fixed** before this session; only the residue above
was left:

* **"Two silently-skipping validation gates."** Both now fail loudly rather
  than degrading to a no-op. `validate_neighbor_price._actual_lmp` raises
  `FileNotFoundError` on an absent measured-LMP parquet (a missing reference
  can no longer hide a broken gate); `export_iso_bin_assignments._chp_floor_status`
  raises `SystemExit` on an absent thermal-tranche artifact instead of returning
  `{}` and silently dropping every CHP `Must_Run_Source` to `chp_sector_default`.
* **`tools/launcher.py` config discovery.** Globs `paths.REFERENCE_DIR` +
  `configs/`. Only the empty-state UI string was stale (A2).
* **`export_tranche_config.py --out`.** Defaults to
  `REFERENCE_DIR / "plant-tranche-config.csv"`.

## Out of scope — recorded, not swept

Two adjacent path-hygiene findings surfaced during the census. Neither is an
`inputs/` dead path, and sweeping either here would be scope creep:

1. **Hand-rolled `REPO / "data" / "raw" / …` is the prevailing idiom** across
   ~150 sites in `scripts/data/` — they resolve *correctly* but bypass the
   `config/paths.py` registry that CLAUDE.md's directory map makes canonical.
   That is its own workstream, not a dead-path fix.
2. **`scripts/data/derive_nyiso_import_ladder.py:53`** opens
   `"data/raw/_validation-source/actual_lmp.json"` as a **CWD-relative literal**
   at module import time — correct only when run from the repo root. A real
   defect, different class.
