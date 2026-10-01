# Benchmark-basis staleness inventory (G-21/G-21b, all ISOs) — 2026-07-12

**Owner directive 2026-07-12** (session_01SfBzT4EggvRfh35MYgoYXH): the G-21/G-21b
class & fuel-total scoring basis is the **go-forward default for every ISO**,
unconditional (rubric §0b, methodology spec §1.8, guard
`tests/test_benchmark_basis_default.py`). This session settles and guards that
rule and **IDs which ISOs' committed benchmarks are stale** against it. **No
solve, no re-render, no registration** was performed here — refreshing a stale
bundle is the owner's to run in a separate non-Fable session.

## What "stale" means here (and why it is a per-ISO property)

A run is scored `model payload (gmModel) × committed bench part (classFull /
e930)`. The **model side never changes** under a benchmark fix; only the
**actual side** (the per-ISO-year bench parts,
`frontend/data/backcast/bench/<ISO>/<year>.json.gz`) does. Those parts are
**shared by every run of an ISO**, so benchmark staleness is a **per-ISO
property** — the keeper AND the most-recent run of an ISO share the exact same
bench, hence the same staleness. Refreshing an ISO's three bench parts refreshes
every run's score at once.

## The three mechanisms and where each already stands

| Mechanism | Where it lives | Data/coverage today |
|---|---|---|
| **Fix 1 — G-21 combined reconcile** | `render_calibration_html.reconcile_vintage_classes` | Present in the renderer since **before** the last pre-fix bench render (`8198621`, 2026-07-11) — verified: `reconcile_vintage_classes` was already combined (`_tgt = e930[gas] + e930[coal]`) at that commit. So **every committed bench already carries fix 1.** |
| **Fix 2 — #2049 backfill bucketing** | `run_calibration_full._backfill_eia923_with_campd` × `_plant_class_shares` | Merged `aecf00b` (2026-07-12 00:04Z). **NOT present at `8198621`.** This is the **sole live staleness driver.** |
| **Fix 3 — G-21b C2 CEMS split anchor** | `calibration_verdict.score_sysvol` + `_fallback_coal_anchor`; anchor `e930.coal_cems` written in `render_calibration_html` | `coal_cems` spliced into **all 18 bench parts** (`50dbb54`, 2026-07-12) and the anchor is now built inside the renderer (`2fcc6d6`). **Every re-score already takes the anchor path** regardless of when classFull was last rendered. |

**Conclusion: the only thing a pre-fix bench is missing is fix 2 (#2049).** Fix 2
only moves a benchmark where a **genuinely mixed-fuel plant is mapped
last-generator-wins to its _minority_ class** (double-counting its whole CAMPD
net on top of the reported majority row). Its material bite therefore depends
entirely on whether an ISO's fleet contains such plants.

## Per-ISO staleness ID

Provenance = git history of `frontend/data/backcast/bench/<ISO>/2024.json.gz`
(when `classFull` was last regenerated). Litmus = PJM Linden p2406 `c_ann` ≈ 4.74
(split-corrected) vs ≈ 9.47 (whole-net double-count).

| ISO | keeper / newest run | classFull last regen | fix-2 driver present in fleet? | **Verdict** |
|---|---|---|---|---|
| **PJM** | pjm-98 (keeper) / pjm-99 | `1c2ceb7` 2026-07-12 03:53Z — G-21 corrected basis | — (already split) | **CURRENT** — litmus confirmed (Linden p2406 `c_ann`=4.74) |
| **MISO** | miso-60 (keeper) / miso-60 | `ee8d50b`/`dbb1002`/`2fcc6d6` 2026-07-12 — post fix 2 | — (already split) | **CURRENT** — keeper 2025 gas C2 source = "combined fossil minus coal anchor" |
| **ERCOT** | ercot56-nucwin (keeper) / ercot59 | `8198621` 2026-07-11 (pre-fix-2) | **No** — ERCOT uses the curated-bin path (`class_shares=None`), which fix 2 leaves **byte-identical** | **STALE-BENIGN** — fix 2 is a structural no-op for ERCOT; effectively current |
| **CAISO** | caiso-77 (keeper) / caiso-77 | `8198621` 2026-07-11 (pre-fix-2) | Minor — few mixed CC+CT plants; ~0 coal (fix 1/3 already no-op) | **STALE-BENIGN** — C2-2025 print unchanged on the port to the G-21b bench (calibration-log 2026-07-12 CAISO port note); a refresh is a low-priority housekeeping re-render, not a determination risk |
| **NEISO** | neiso-56 (keeper) | `8198621` 2026-07-11 (pre-fix-2) | **No material target** — committed bench has **no** CT_PEAKER/ST_GAS/ST_CHP plant > 0.3 TWh; fleet is ~99% CC_REGULAR (56.6 TWh) | **STALE-BENIGN** — fix 2 has essentially nothing to re-bucket; coal immaterial (fix 1/3 no-op). Refresh to confirm, but no row is expected to move materially |
| **NYISO** | nyiso-61 (keeper) | `8198621` 2026-07-11 (pre-fix-2) | **Yes** — NYC/Long-Island dual-fuel steam + CC fleet (Ravenswood, Northport, Arthur Kill, Astoria, …), material ST_GAS energy that fix 2 re-splits | **STALE-MATERIAL** — per-class gas rows (ST_GAS vs CC_REGULAR/CT_PEAKER split) and the C1 gas-family mix can move; the keeper's C1/C2 determination must be re-verified on the corrected basis |

### Rows that move for the one material ISO (NYISO)

Committed-source candidates (2024 bench, group ∈ {ST_GAS, ST_CHP, CT_PEAKER},
`e_ann` > 0.3 TWh) whose net fix 2 would re-split across the plant's measured
prime-mover shares rather than book whole to one class:

- Ravenswood (p2500), Northport (p2516), Arthur Kill (p2490), Astoria (p8906),
  Bowline Point (p2625), E F Barrett (p2511), Bethpage (p50292), Bayonne (p56964).
- **Affected scored rows:** `ST_GAS`, `CC_REGULAR`, `CT_PEAKER` per-class volumes
  and their generation shares (C1); the gas-family aggregate (C2, 2025 preliminary
  fallback now anchored — no coal in NYISO so the fallback reduces to the 930 gas
  level). NYISO has ~0 coal, so **fix 1 and fix 3 are no-ops** for it; the entire
  move is fix 2.

The exact magnitudes require the corrected re-render (owner-scheduled); this
inventory names the rows to check, not certified deltas.

## Refresh instructions (owner, separate non-Fable session — NO solve needed)

Only **NYISO** is materially stale; **NEISO/CAISO** are benign refreshes if
desired; **ERCOT/PJM/MISO** need nothing. A refresh is a **benchmark re-render on
committed raw sources**, not an LP solve — the sanctioned #2049 path
(cf. the 2026-07-12 pjm-98 re-score, calibration-log): regenerate the ISO's three
`classFull` parts via the production helpers (`_benchmark_eia923_frame` with the
fixed backfill + `reconcile_vintage_classes`), re-score the keeper (and its
ablation twin) with `calibration_verdict.py --write-metrics` against the corrected
parts, patch the sidecar/attestation from the **scored** metrics (never memory),
run the keeper-auditor after any `keepers.json` change, and commit the slim bench
parts + run payloads via `mcp__github__push_files`. Rule 16 stands (all years one
bundle); rule 22 stands (2023–2025 only). **Determination flips are honest and
stand** (pjm-98 CAVEAT→FAIL precedent) — nothing may be tuned to un-flip them
(CLAUDE.md rules 1/13/23).
