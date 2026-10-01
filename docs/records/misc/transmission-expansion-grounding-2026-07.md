# Transmission-expansion grounding — session record (FF-G1, 2026-07-19)

**Scope:** the FF-G1 deep-research grounding session (WAVE FI): committed
transmission-expansion registry (6 ISOs) + the gated forward TTC channel, in
the capacity-cost-grounding template. Standing reference:
`docs/transmission-expansion-methodology-2026-07.md` (design, survey,
grounding tables, V1 exclusions, maintenance rules — read that first; this
file is the audit trail + verification record).

This session also opened WAVE FI itself: the forward-input provenance audit
(FF plan §1.2-11), the FF-G2…G5 companion prompts (fuel forwards, net-CONE
vintages, load-shape memo, nuclear registry — delivered to the owner in-chat,
summarized in plan §6), and gap-register §3.11.

## 1. What landed (files)

- Schema `data/dictionary/schema/transmission-expansion.schema.yaml`; lib
  `scripts/lib/transmission_expansion/` (`__init__.py` + 6 ISO spec modules);
  curation `scripts/data/curate_transmission_expansion.py` (live-topology
  resolvability validation); fetch/pin
  `scripts/data/fetch_transmission_expansion_sources.py`;
  `scripts/regenerate_clean.py` DATATYPES + data-dictionary entries.
- Registry `data/raw/transmission-expansion/`: README (delta convention,
  base-static vintages, watchlist, re-query items) + 6 CSVs (35 rows: 10
  applied deltas, 1 superseded audit row, the rest 0-delta documentation /
  recorded-not-applied `import_tranche`/`intra_zonal`) + `md/` (7 sha256-pinned
  primary documents + page-marked conversions + generated `README-SOURCES.md`).
- Consumption seam `src/market_sim/data/transmission_expansion.py`; gate
  `ScenarioConfig.transmission_expansion_enabled` (default off,
  `_CACHE_KEY_OPTIONAL_FIELDS`, backcast+hindcast coercion); runner wiring at
  the per-year `year_ttc` seam (+ per-year interface-group rebuild preserving
  corridor extension groups); `data.transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE`;
  `scripts/run_full_horizon.py --transmission-expansion`.
- Tests: `tests/test_transmission_expansion.py`,
  `tests/test_curate_transmission_expansion.py` (32 tests).
- Docs: methodology + this handoff + CHANGELOG entry + FF plan §1.2-11 /
  §6 WAVE FI + gap-register §3.11.

## 2. Research provenance

Three parallel web-research sweeps (ERCOT+MISO, NYISO+NEISO+PJM,
CAISO+WECC seam) against primary instruments (PUCT/ERCOT board items, MISO
MTEP/board approvals, PJM board whitepapers, CAISO board decisions,
NYPSC/NYSERDA/NYISO, MA-83D/ISO-NE, WECC progress reports), 2026-07-19.
Verification highlights the registry encodes: NECEC energized 2026-01-16;
CHPE commercial 2026-05-13; Clean Path NY terminated 2024-11-27 (watchlist,
not a row); Smart Path Connect completed 2026-06 (intra-zonal — NOT a
Central-East re-rate; the 2,850 static is the measured post-Segment-A/B
2024-25 mean); ERCOT 765 route cases pending (Docket 59029 abated June 2026 —
schedule-risk noted per row); MISO Tranche 1 Table 7-3 per-LRZ CIL deltas
(Future-1-2040 basis — delta-not-level transferred, rule 14); Tranche 2.1 has
NO public CIL table (0-delta row + re-query item); JTIQ subscription-contingent
(watchlist only); CAISO 2025-26 plan cancelled Serrano–Del Amo–Mesa
(superseded audit row); SWIP-North's 1,117.5 MW board-stated ISO entitlement
vs the flat advisory MIC (tension documented, methodology §6.6); TransWest
slipped to ~2031 (recorded, supply-side).

## 3. Degrees of freedom / admissibility

No fitted parameters. Every applied delta is a published instrument quantity
(converter rating, board-stated entitlement, published CIL delta, published
GTC re-rate) applied additively to a documented base; the only judgment calls
are MAPPINGS, each recorded in the row's mandatory `mapping_note` with
`mapping_confidence`: the ERCOT 8:3 export split (follows the repo's existing
WESTEX convention), the MISO union-zone member-sums (follows the CIL groups'
documented ceiling construction), NECEC/SWIP simultaneous-cap uplifts
(converter/entitlement basis). Where no MW is published the delta is 0.0 —
never estimated. `TRANSMISSION_BASE_STATIC_VINTAGE` is a documented property
of the existing statics' sources, not a tunable.

## 4. Verification record (all on this branch, 2026-07-19)

1. **Tests:** 32 new tests green; full suite green (re-run at push time).
2. **Cache keys:** `ScenarioConfig()` key byte-stable with the field at
   default (drop verified); ON produces a distinct key. Note for future
   sessions: cache keys embed absolute data paths, so cross-checkout key
   comparison is meaningless — compare at one path.
3. **Off = identical:** NEISO 2026 forecast, pre-change code (e87bf7d
   snapshot) vs this branch with the flag off — result frames `equals()=True`
   and objective values exactly equal (4,359,069,996.485064); the only
   parquet byte differences are wall-clock `build_time` metadata (never
   byte-stable) and the path-embedded cache-key directory name.
4. **T0 smoke ON (NEISO 2026–2028, ≤5 solve-years per plan §2.1b):** 3/3
   years solved, no error; 2026 applies `HQ_import→North 900→2,100` and
   `HQ_import_simultaneous 3,850→5,050`. Measured effect: HQ import legs
   re-route onto the new capability (HQ→Boston mean 1,611.8→1,930.4 MW,
   HQ→CT 1,117.7→1,429.9, HQ→North net export leg deepens −741.9→−1,372.7)
   while TOTAL HQ import is unchanged (1,987.6 MW mean) — the energy depth is
   bound by the import-tranche supply curve, not the wires, so zonal prices
   move ≈ 0 in 2026. This is the documented V1 exclusion (methodology §6.1)
   observed live: the link-half applies; NECEC's energy-half needs the
   per-year import-tranche seam follow-up.
5. **Invariants:** smoke shows `I4 FAIL (2028: coal off by 54.0 MW)` and
   `I12 WARN (2027 RM 16.0% vs band ≤15.2%)` — attributed below.

## 5. OFF-leg attribution (CONCLUSIVE)

Same-code paired legs on the final rebased tree (base `4ebc113`), NEISO
2026–2028, fresh out-dirs (`results/txexp-off3b` vs `results/txexp-smoke3b`):
the flag-OFF leg reproduces the **identical** `I4 FAIL (2028: coal off by
54.0 MW)` and `I12 WARN (2027 RM 16.0%)` — both pre-exist the channel on the
base NEISO forecast path and are unrelated to this change (candidates: the
Merrimack confirmed-exit MW accounting / NEISO reserve-margin band; not
chartered here). Load-weighted prices are identical OFF vs ON in all three
years (45.093 / 43.866 / 45.658 $/MWh) — consistent with §4.4: the wire
uplift re-routes HQ flows but energy stays import-tranche-depth-bound, so the
channel's 2026–2028 NEISO price effect is ≈ 0 until the energy-depth seam
lands.

## 8. APPLY-SPEC — core-wiring patch (push-integrity rule 27 / Git §4)

`scenarios.py` (522 KB) and the other large edited files exceed the API
push-payload budget for full-file pushes, so — per the capacity-cost-grounding
§4d precedent — every EDITED pre-existing file's exact diff ships as ONE
committed patch (all full-content pushes on this branch are brand-new files):
`docs/handoffs/patches/ff-g1-core-wiring.patch` (419 lines), generated by
`git diff` from the verified local tree and proven exact by
reverse-application (`HEAD == base 4ebc113 + patch`). It carries:
`src/market_sim/config/scenarios.py` (gate field + coercion +
`_CACHE_KEY_OPTIONAL_FIELDS`), `src/market_sim/runner.py` (pre-loop load +
per-year seam), `CHANGELOG.md` (top entry),
`scripts/render_data_dictionary.py` (dictionary entry),
`scripts/regenerate_clean.py` (DATATYPES registration),
`scripts/run_full_horizon.py` (`--transmission-expansion` flag),
`docs/forecast-development-plan-2026-07.md` (§1.2-11 + WAVE FI), and
`docs/gap-register-2026-07.md` (§3.11).

To apply (owner or a follow-up session, from repo root on this branch):

```
git apply --3way docs/handoffs/patches/ff-g1-core-wiring.patch
# byte-verify (expected post-apply git blob hashes + line counts):
#   183026f9aecb2d3a645ac0e8dc2955e1972c2dfb  7996  src/market_sim/config/scenarios.py
#   d8b5eb364b22fcf5e93277fd883cca2d3905cc98  2543  src/market_sim/runner.py
#   00024d1d0687318a694cf8677c5b645bfc30971e  4562  CHANGELOG.md
#   7d6522a968ecd6352d1ce677b40d6c22c3ae7f0f  1239  scripts/render_data_dictionary.py
#   f4e10df34418b12ac29dd1c8896f091ef9edca4f   146  scripts/regenerate_clean.py
#   e81d77e9cfae24af660fcb1cb3d0cd21c8e7e41a   396  scripts/run_full_horizon.py
#   8343d9b6de60a8567f7cdfecd01b65f8f404ba82  1165  docs/forecast-development-plan-2026-07.md
#   9a25867b786819f0902db6f43c147181ff8aa837   111  docs/gap-register-2026-07.md
git hash-object <each file>   # must match; then
PYTHONPATH=. python scripts/render_data_dictionary.py   # regenerate data-dictionary.md
PYTHONPATH=.:src python -m pytest tests/test_transmission_expansion.py tests/test_curate_transmission_expansion.py -q
```

UNTIL the patch is applied, the pushed branch is deliberately
default-off-complete: the loader/curation/registry/tests all work, `runner.py`
is main's (unwired — `getattr` default keeps behavior identical), and the two
`TestScenarioGate`-class tests + the `--transmission-expansion` CLI flag
activate only post-apply. Nothing on the branch changes any default behavior
either way.

## 6. Follow-ups (named, not silent — methodology §6 is authoritative)

Import-tranche per-year seam (CHPE/SunZia/TransWest energy halves + NECEC
energy depth); ERCOT import-direction one-way split (PBRP +2,105 MW);
hindcast RC-1B information gate; no-published-MW re-rates (PJM via the
measured transfer-interface-limits intake post-COD, Propel NY, Gates–Los
Banos No. 3, IV–NoSONGS LCT re-rate); MISO T2.1 CIL table intake; browser
re-fetch of the 4 MANUAL-DOWNLOAD sources (MISO cdn ×2, ERCOT board items
×2); watchlist promotions (ISO-NE LTTP selection ~Sep 2026, CAISO Trout
Canyon–Lugo sponsor ~late 2026). Gate flip is owner territory after a
chartered T1-F A/B.

## 7. How to reproduce

```
PYTHONPATH=. python scripts/data/curate_transmission_expansion.py
PYTHONPATH=. python scripts/data/fetch_transmission_expansion_sources.py --to-markdown
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  PYTHONPATH=. python scripts/run_full_horizon.py --iso NEISO \
  --start-year 2026 --end-year 2028 --transmission-expansion \
  --out-dir results/txexp-smoke/neiso
```
