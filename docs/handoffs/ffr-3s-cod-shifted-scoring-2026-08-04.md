# FFR-3S — capacity additions are scored against the DECISION year

**Session:** 2026-08-04 · **Owner decision:** D-9(ii), signed 2026-08-04 (sitting Addendum K.2)
**Class:** instrument change (scorer-only). **Lands BEFORE the next battery scores anything.**
**Base:** `origin/main` 292f577e · **Branch:** `claude/capacity-additions-decision-year-n0musi`

---

## 1. The defect

`evolve_fleet` books an economic-entry decision at year *Y* into `entry_pipeline` with
`cod_year = Y + ENTRY_COD_LAG_YEARS[tech]` (2 years for wind/solar/gas_cc/gas_ct — the LBNL
"Queued Up" 2024 median IA→COD). `score_capacity_hindcast.model_additions` read additions by
the **ledger year they commission in**. In the 2021→2025 T1-H window the 2024 and 2025 decision
cohorts commission in 2026/2027 and were therefore **never scored** — half the solved decision
years were invisible to the metric.

`entry_commissioning_lag` is armed by default (owner decision D-2, 2026-08-02) and is `true` on
every registered T1-H leg, so the censoring was live, not hypothetical.

**The censoring is permanent; no window length removes it.** Per FFR-3Q §3.2 (argument not
re-derived here, and **no window was widened**): forward requires scoring 2026 — a locked-test
year, `final` is empty and the holdout freeze is active — and 2027, which has no actuals;
`_validate_window` hard-caps a non-crossover window at `end <= 2025`; backward hits the 2021
demand floor and 2020's validation tier.

## 2. What changed

All of it is scorer-side. **No LP was solved and no out-of-training year was touched.**

| File | Change |
|---|---|
| `scripts/score_capacity_hindcast.py` | `model_additions(ledgers, basis=...)`; `_entry_pipeline_rows`; `additions_basis_record`; `load_solved_config`; `score_additions(..., basis=...)` stamps the basis; `main`/`_rescore` emit `additions` + `additions_cod_basis` + `additions_basis`; report renders the basis + comparison table |
| `scripts/score_crossover.py` | Shares the scorer, so it would have inherited the new default **implicitly** — the basis is now passed explicitly and the crossover score carries the same three blocks |
| `tests/scoring/test_capacity_hindcast_scoring.py` | 8 new tests (below) |
| `docs/forecast-readiness-peer-review-2026-07.md` | §4 standing disclosure entry |

### 2.1 Decision year is *read*, not reconstructed

Scope item 1 required deriving the decision year from the ledger rather than subtracting a lag
constant "unless the ledger records nothing better". **The ledger records it directly**:
`evolve_fleet` writes `events["entry_pipeline"]` with `decision_year` *and* `cod_year` on every
row, tagged `event: "decided"` or `event: "commissioned"`. `ENTRY_COD_LAG_YEARS` is never read
by the scorer.

The decision basis is an **exact net-out** against the COD-basis rows, not a re-derivation:

* every `commissioned` row is reversed out of its `cod_year` (where step 4.5 folded it into that
  ledger's `thermal_additions` / `renewable_additions`);
* every `decided` row is added at its `decision_year`.

This is exact for VRE too, where the commissioned MW folds into a *zonal pool aggregate* and so
cannot be identified by `unit_id`. Consequences that fall out for free and are correct:

* a decision made in-window whose COD lands after it now **counts** (the defect);
* a commissioning whose decision predates the window is **dropped** — that decision was not the
  window's, and crediting it would be the mirror-image error.

**Storage is unaffected by the basis.** Its build channel is the runner's `storage_additions`
value stack, outside the economic-entry screen, so it never enters `entry_pipeline`; decision
and COD coincide for it by construction.

### 2.2 The basis is explicit and recorded (scope item 2)

A basis-implicit verdict is the record-provenance defect class FFR-3R closed, so this reuses
`scripts/lib/run_record.py` rather than opening a parallel channel:

```python
ADDITIONS_BASIS_RECORD_SPEC = RecordSpec({
    "additions_basis": FromArgs("the SCORER's attribution instrument, not a property of the
        solved config: one solve is scorable on either basis, so no ScenarioConfig field can
        answer which basis produced this verdict"),
    "entry_commissioning_lag": FromConfig(cast=bool, why="the solved-config gate that separates
        decision from COD; when False the two bases coincide by construction"),
})
```

The block is built from the bundle's `run_config.yaml` — the **solved** config, not the CLI
request — and `assert_sourced` runs before the record is written. A bundle with no dump records
`entry_commissioning_lag: null` plus a `config_source` note: **"not measured", never "off"**.
Guessing the gate from `meta.json` or from argparse would have been instance six.

Every new `score.json` (and, via `register_hindcast`, every hindcast sidecar, which embeds
`score.json` wholesale) now carries:

```
additions            → the graded verdict, decision basis, with "basis": "decision"
additions_cod_basis  → the same solve on the COD basis (scope item 3), reported not graded
additions_basis      → provenance: basis, definition, decision citation, ledger span,
                       pipeline row counts, entry_commissioning_lag (config-checked), and
                       the two quantified deltas below
```

The two deltas make the instrument's effect auditable per run:
`decided_in_window_cod_after_window_gw` (what the COD basis censored) and
`commissioned_in_window_decided_before_window_gw` (what it over-credited).

## 3. Tests (scope item 4)

`uv run pytest tests/scoring/test_capacity_hindcast_scoring.py` — **33 passed** (25 pre-existing
+ 8 new).

* **`test_decision_basis_scores_cohorts_the_cod_basis_censors`** — the required
  fails-old/passes-new case. 2 GW of wind decided in each of 2021-2025 (10 GW) against a 10 GW
  actual: the COD basis sees 6 GW (−40 %, **FAIL**) because the 2024/2025 cohorts commission in
  2026/2027; the decision basis sees 10 GW (0 %, **PASS**). `BANDS` is untouched — the band did
  not move, the attribution did.
* **`test_retirements_scoring_untouched_by_the_basis_change`** — the required retirements-side
  test. The same ledgers with and without `entry_pipeline` rows produce frame-identical
  `model_retirements` and identical `score_retirements` / `score_channels` / `score_tr10`, and
  the fixture is proven non-vacuous (the same rows *do* move additions, 0 → 4000 MW).
* Plus: decision basis is the default and says so; pre-window decisions are dropped; the bases
  coincide when no `entry_pipeline` key exists (legacy/lag-off bundles — an absent key is
  backward-compatible); the record block is explicit and quantified; the record is checked
  against a solved config; an unknown basis raises.

Full suite: `uv run pytest tests/scoring` → **892 passed, 3 skipped**.
`tests/scoring/test_ff_readiness_battery.py` has **4 failures that are pre-existing on
`origin/main`** (verified by stashing) and are not in this lane.

## 4. Solve-inertness (scope item 5)

No `ScenarioConfig` field was added or changed; nothing under `src/market_sim/` was touched.
Cache keys before and after, same method as FFR-3R:

| config | before | after |
|---|---|---|
| `ScenarioConfig()` | `603c2498bf71d21d` | `603c2498bf71d21d` |
| ERCOT 2023 backcast | `df386bca96a1d288` | `df386bca96a1d288` |
| PJM 2023 backcast | `9834b2018b598423` | `9834b2018b598423` |
| CAISO 2023 backcast | `a9afddae291525c1` | `a9afddae291525c1` |
| NYISO 2023 backcast | `fd15030b3ee60f11` | `fd15030b3ee60f11` |
| NEISO 2023 backcast | `5b1633171fead559` | `5b1633171fead559` |
| MISO 2023 backcast | `2a1252c3acae89e9` | `2a1252c3acae89e9` |

**All seven identical.** No keeper moves: the change touches no keeper shard, no backcast
registry file, and no backcast artifact of any kind (`git status` is four files, all listed in
§2). Keepers verified unchanged at session start against the shards themselves — ERCOT
`2026-08-03-ercot158-pool-arm`, PJM `2026-08-03-pjm-151-seam-envelope`, CAISO
`2026-08-04-caiso164-zonal-loss-surface`, NYISO `2026-08-04-nyiso-120-c119-scope`, NEISO
`2026-08-03-neiso-caiso156-meter-screen`, MISO `2026-08-04-miso-124-dualfuel-rearm`.

Rule 28: no `ScenarioConfig` field was added and no mechanism was tested, so no matrix cell
changes state. `scripts/check_mechanism_matrix.py` exits 0 (its 221 warnings are pre-existing
anchor-line drift across unrelated rows).

## 5. The cost — stated, not softened

The owner signed this knowing it, and it is now on the peer-review §4 standing disclosure list:

* **The additions metric now MEANS something different.** Every historical additions verdict is
  **non-comparable** to any new one.
* **The FF-2D regression baseline stops being usable for additions specifically.** An additions
  band that appears to move across 2026-08-04 may be measuring the instrument, not the model.
  Re-establishing an additions baseline requires re-measuring forward on the new basis.
* **Retirements-side comparability is unaffected.** The retirement channel has no commissioning
  lag and reads no `entry_pipeline` row — asserted by a test, not by prose.
* **Nothing committed was retro-edited and no committed leg was re-scored** to pick up the
  change. Every re-measurement is a future battery's job, run forward on the new basis.
* Within a single *new* run the two bases ARE comparable — that is what `additions_cod_basis`
  is for.

## 6. MISO FC-3 — reported, NOT closed

MISO's registered T1-H leg (`miso-2021-2025-realized-ffr3a3`, `entry_commissioning_lag: true`)
fails FC-3 additions on all five techs, most starkly **solar: model 0.0 GW vs actual 18.649 GW**
(−100 %). It is also the only registered T1-H leg with an empty retirement-FAIL set.

**The new basis cannot explain this, and nothing here closes it.** The arithmetic, from the
committed sidecar alone: with a 2-year lag and a window starting 2021, the decision cohorts of
**2021, 2022 and 2023 commission in 2023, 2024 and 2025 — inside the window, and therefore
already visible under the COD basis.** The COD-basis solar total is 0.0 GW, so those three
cohorts decided **zero** solar. Only the 2024 and 2025 cohorts were censored, so the decision
basis can move MISO's solar number by at most two decision years — and a 2-year shift cannot
explain a zero, exactly as the owner stated.

Three cohorts of zero solar build in the ISO that actually added 18.6 GW is an entry-screen
root cause (rules 1/11/14), not a scoring artifact. **This is the finding; it stays open.**

No number for MISO on the new basis is quoted here, because producing one would mean re-scoring
a committed leg — prohibited by this session's charter, and the ledgers a re-score needs live in
the disposable `results/<iso>/<cache_key>/` cache, not in the committed bundle. Measuring it is
a future battery's job, run forward.

## 7. For the next session

* The next capacity-hindcast battery scores on the decision basis automatically; read
  `score.json → additions_basis` to confirm which basis produced a verdict.
* When comparing any additions number to a pre-2026-08-04 one: **don't.** Re-measure both sides.
* `additions_cod_basis` exists for within-run comparison only. It is not the graded instrument
  and must not be quoted as a verdict.
* MISO FC-3 solar (§6) is open and is an entry-screen investigation, not a scorer one.
