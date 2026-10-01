# FINDING — capx D85-R: the four record repairs, landed

**Session:** capx D85-R, executing `docs/handoffs/FINDING-capx-d85-key-provenance-2026-09-07.md`
§5's recommended repairs **(ii)** and **(v-a)/(v-b)/(v-c)** (owner ruling **Q59**'s follow-on;
capx ledger **§0bc.3(c)**). **Model:** Opus. **DATA PROFILE:** code. **Branch:**
`claude/capx-d85r-record-repairs-wyrs3y`, fresh off `origin/main` at `12e71b89` (2026-09-07).
Pre-registration, written before any edit: `docs/handoffs/PRECOMMIT-capx-d85r-record-repairs-2026-09-07.md`.

**Record hygiene only. No solve, no key rewritten, no registration, no gate moved.**

---

## 0. The census line, first

```
223 committed run configs at 12e71b89: 179 reproduce, 29 have no key, 15 mismatch
  15 KNOWN (listed exceptions), 0 UNKNOWN
  keys: 129 reproduce under BOTH constructions, 50 only with the surface AT DECLARATION
        (capx D79's designed re-key), 0 only with the LIVE surface
```

**Fifteen known, ZERO unknown**, every one recipe-verified against its own recorded literal,
and both key constructions reported. `scripts/check_key_provenance.py` exits 0.

---

## 1. What D85 established, and what this lane inherited

D85's verdict — **BOOKKEEPING, NOT A DEFECT** — is not re-litigated here. Nor are its two
refusals, which bind this lane and were honoured in full:

* **No committed `cache_key` was rewritten.** A committed key is what that bundle actually
  solved under; rewriting it makes the artifact lie about its own provenance.
* **No lagging field was re-registered.** `caiso_offer_surface_measured_ungrounded` stays exactly
  as it is; curing the 6 `lag` rows that way orphans every key produced since 2026-09-02 that
  carries the field.

Also untouched, by rule and by check: `_CACHE_KEY_OPTIONAL_FIELDS`,
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, `_CACHE_KEY_REGISTRATION_TIME_DEFAULTS`,
`config/solve_surface_declared.py`, every bundle, every registration, and
`tests/golden/ercot_2026_2040*.json` with its owner-signed D-7 staleness waiver.

## 2. The drift against D85, reported as instructed

D85 measured `214 / 169 / 30 / 15` at `db0c1d85`; this lane measures `223 / 179 / 29 / 15` at
`12e71b89`. Net **+9 = 11 added, 2 pruned**, all enumerated in the PRECOMMIT §1: the added are
`spp43_screened_B` plus ten `scn-campaign-policy-2026-09-06` policy configs (CAISO ×4, MISO ×4,
PJM ×2); the pruned are `spp40_baseline_B` and `spp42_crosswalk_B`, superseded by the spp43 screen.

**The 15 mismatching files are SET-EQUAL to D85's 15** — checked, not assumed. The counts are
measurements and will drift again; **ZERO UNKNOWN is the gate.**

Class (c) also grew, exactly as D79 designs: `reproduces_at_declaration_only` is now **50**
(CAISO 21, was 17; ERCOT 29, unchanged), against `moved_rows` = ERCOT
`{NUCLEAR_MONTHLY_CF_BY_YEAR}`, CAISO `{NUCLEAR_MONTHLY_CF_BY_YEAR, STATE_CARBON_PRICE_BY_ISO}`.

## 3. Repair 1 — the checked exception record

**`docs/governance/key-provenance-exceptions.json`** — 15 entries, one per non-reproducing
committed record, each carrying its ISO, its recorded literal, its solve timestamp and sha, its
**class**, its **executable recipe**, its derivation prose, and its citation into D85 §3.
Class totals: `lag` 6 · `pre-ledger-flip` 3 · `pre-ledger-flip+split-root` 5 ·
`vintage+resolved` 1. **The entries were DERIVED, not typed**: they are the classifier's own
output converted to the executable schema, so the list cannot assert a derivation the instrument
does not reproduce.

The record's own `what_this_is_not` block states, in the artifact, that it is not a licence to
rewrite a key, not a licence to re-register a field, not a place to park a new mismatch, and not
about the solve-surface re-key.

**The instrument is now standing tooling.** D85's one-off `docs/handoffs/d85/
key_provenance_census.py` was promoted to `scripts/lib/key_provenance.py` (library) plus
`scripts/check_key_provenance.py` (CLI gate). D85's own measurement record
`docs/handoffs/d85/key-provenance-census.json` stays as untouched evidence, and D85's §7
reproduction block is annotated rather than rewritten.

### The five gates, and which direction each catches

| gate | fires when | offline? |
|---|---|:--:|
| **G1_UNKNOWN** | a committed record does not reproduce and is **not listed** — a SIXTEENTH | ✅ |
| **G2_STALE** | a listed record now **reproduces** — dead scaffolding (rule 26 `[R-DELETE]`) | ✅ |
| **G3_RECIPE** | a listed record does not reproduce its literal under **its own recipe** | one row |
| **G4_PRESENT** | a listed `run_config.json` is no longer committed (bundle pruned) | ✅ |
| **G5_KEY** | a listed `recorded_cache_key` is not the key the file itself records | ✅ |

**Both failure directions are demonstrated by test, not asserted in prose**
(`tests/regression/test_key_provenance_exceptions.py`): a synthetic sixteenth mismatch trips G1
and only G1; a listed entry doctored to reproduce trips G2 and only G2, with a message that says
*delete it*. G3/G4/G5 are demonstrated too. **9 tests, all passing, and all passing again under a
simulated blobless checkout with `fetch_commit` wired to raise** — so the gate is real on a CI
runner, not only on a hydrated dev box. It rides the existing **blocking** fast pytest tier; no
new workflow was added (the repo bans per-task workflows).

**The one declared degradation, stated at the gate rather than discovered later.** The golden
fixture's recipe is `vintage+resolved` and needs the `f0f7c67d` `scenarios.py` blob, which a
`blob:none` shallow clone does not hold. The CLI fetches it at depth 1 and verifies for real; the
offline test reports that one gate as `G3_UNVERIFIED` — never as `G3_RECIPE`, which would mean
*checked and wrong* — while G1/G2/G4/G5 still bind on all 15. A related split was needed inside
the classifier for the same reason: `unclassified` (the whole ladder ran and nothing derived the
literal — a finding) is now distinct from `unclassified-unreachable-commit` (a property of the
checkout). Collapsing the two would have made this gate red on every CI run, which is how a
checked record turns into a disabled one.

## 4. Repair 2 — fold roots in the run record

`pipeline/persist.environment_block()` now records **`cache_key_path_roots`** — the
`(sentinel, absolute-prefix)` pairs `_cache_key_path_roots()` returned, in the order `cache_key`
applied them — and **`market_sim_data_root`**, the raw env var behind them (`""` when unset).

This is the gap D85 §3.3 named: the five `fc6` arms produced a *different, equally correct* key
because `MARKET_SIM_DATA_ROOT` was relocated away from the checkout, and **nothing in the record
said so** — those keys are recoverable today only because two findings happened to state the
environment in prose. Verified both ways: the ordinary case records
`[["<repo>", "…/market-simulator"]]`, and under `MARKET_SIM_DATA_ROOT=/tmp/altroot` it records
`[["<data_root>", "/tmp/altroot"], ["<repo>", "…"]]` — which is *exactly* the `roots` shape the
exception record's split-root recipe consumes. A future split-root key is derivable from
`run_config.json` alone.

**Inert, verified not assumed:** `cache_key` never reads the environment block, `--reuse-solved`
ignores it (`test_environment_block_is_ignored_by_reuse`),
`replay_keeper._warn_on_environment_mismatch` compares only `python_version` / `platform` /
`packages` so no new warning appears, and `audit_keepers.E11_META_PROVENANCE` excludes
`"environment"` from the recipe block (pinned against `replay_keeper._IGNORE` by
`test_audit_keepers_lineage`). **No key moves; only runs solved after this lands carry the new
keys; no committed record is rewritten.**

## 5. Repair 3 — resolved config in the golden writer

`scripts/golden_forecast_bands.py` serialized `dataclasses.asdict(config)` — the **request** —
while `run_scenario_iso` applied ERCOT's `default_scenario_overrides =
{"scarcity_price_overlay": True}` and hashed the **resolution**. The committed fixture therefore
records `scarcity_price_overlay: False` for a solve that ran it `True`, and its `cache_key` is
unreproducible from its own payload: the sole `vintage+resolved` exception.

New `resolved_scenario_config(run_dir)` reads the solve's own `config.yaml` verbatim —
the same rule, from the same source, that `scripts/lib/run_record.write_run_config` states for
every other runner ("the pre-solve object is a REQUEST and the on-disk dump is the RESOLUTION").
It **raises rather than falling back** to the request: a fixture recording the wrong config is
worse than a seed that stops, and a seed is an owner-authorized invocation somebody is watching.
The request kwargs are still recorded, under the honest name `scenario_request_kwargs`, because
`check_bands` re-solves from them and a reader must not have to guess which half they hold.

**Nothing is reseeded.** Seeding is owner-gated (`REGEN_POLICY` + the §2.1b schedulability guard
+ D-7), so `tests/golden/ercot_2026_2040.run_config.json` is byte-identical and entry 15 stays a
listed exception. `test_golden_fixture_present_and_well_formed` and
`test_golden_fixture_config_identity_is_current` both still pass unchanged.

## 6. Repair 4 — both keys in the census

`cache_key()` appends a `__solve_surface__` block for any ISO whose `config/solve_surface.py` rows
have moved off their frozen declaration, so there are **two constructions**, and D85 surfaced that
the census reported one and was blind to the other. Every row now carries **`key_at_declaration`**
and **`key_live_surface`**, a row reproduces when **either** matches, and the summary names which:

| | count |
|---|---:|
| reproduce under **both** constructions | **129** |
| reproduce **only** with the surface **at declaration** — D79's designed re-key | **50** (CAISO 21 · ERCOT 29) |
| reproduce **only** with the **live** surface | **0** |
| reproduce under neither (the listed 15) | **15** |
| no recorded key | **29** |

`179 = 129 + 50`, and `test_census_reports_both_key_constructions` pins that identity so the split
cannot silently stop accounting for every validated record.

**The 50 are not a defect and are not repaired here.** They are the D79/Q54 mechanism behaving
as designed — "a re-derived registry table re-keys the ISOs whose rows moved" — and re-declaring
the moved ERCOT/CAISO rows is D85 §5 row (vi), explicitly not this lane's call: it belongs to the
ISO lane that re-solves its frontier on the new table. The repair was to the **instrument's
reporting**, so a reader can tell a designed re-key from a genuine mismatch at a glance.

The `scripts/probes/capxd76arm_default_flip_key_census.py` `_key` docstring — which claimed
unconditionally to reproduce `cache_key()` — carries a correction saying it hashes the
at-declaration key, and why that lane's own measurement is nonetheless unaffected (it differences
two variants of the same payload; the omitted block is identical on both sides, so every move
count stands).

## 7. What this lane deliberately did NOT do

* **No committed `cache_key`, bundle, registration, flip entry, or surface declaration changed.**
  If a key rewrite is ever the right repair, that is an owner card, not a lane's act.
* **No solve.** No dashboard registration, no keeper touched, no matrix stamp (rule 28: no
  mechanism was tested or armed).
* **The 50 at-declaration-only records were left alone**, per §6.
* **The golden fixture was not reseeded**, per §5.
* **One asymmetry OBSERVED and reported, not changed.**
  `test_golden_fixture_config_identity_is_current` compares the fixture's seeded key — which is
  the **resolution**'s — against `ScenarioConfig(**REFERENCE_SCENARIO_KWARGS).cache_key()`, a
  **request** hash. That is the same request-vs-resolution class repair 3 fixes in the writer, and
  the test is internally consistent with itself and unaffected by anything here. Changing it would
  move a test's semantics under an owner-signed waiver, so it is named for the lane that reseeds
  and left as it is.
* **D83 / D84 untouched.** No `ScenarioConfig` field added or changed; no CI workflow added.

## 8. Reproduction

```bash
uv sync
# One recipe needs a vintage blob; the CLI fetches it itself, or fetch by hand:
git fetch --depth=1 origin f0f7c67d937c11e487255784e8298faf3c98c0c1
.venv/bin/python scripts/check_key_provenance.py            # exit 0: 15 KNOWN, 0 UNKNOWN
.venv/bin/python -m pytest tests/regression/test_key_provenance_exceptions.py -q   # 9 passed
```

## 9. Validation run, including the pre-existing red

* `scripts/check_key_provenance.py` — exit 0, `15 KNOWN, 0 UNKNOWN`.
* `tests/regression/test_key_provenance_exceptions.py` — **9 passed**, and 9 passed again under a
  simulated blobless checkout (`_git_blob` stubbed to `None`, `fetch_commit` wired to raise).
* Targeted guards, all green: `test_golden_forecast_bands`, `test_reuse_solved`,
  `test_audit_keepers_lineage`, `test_persisted_identity`,
  `test_cache_key_default_flip_guard` (73 passed, 1 skipped).
* `ruff check` + `ruff format` clean across every touched file.
* **Full fast tier** (`pytest -n 2 -m "not slow and not integration and not fulldata"`):
  **7 failed, 9066 passed, 53 skipped, 1 xfailed, 695 subtests passed** in 10m27s.

**The 7 are pre-existing `main` red and none is this lane's**, established by measurement rather
than by inspection: with `src/market_sim/pipeline/persist.py` and
`scripts/golden_forecast_bands.py` reverted to `origin/main` and this lane's new test file removed,
**the same 7 fail identically** —

```
tests/scoring/test_forecast_parity.py::test_all_seven_keepers_resolve
tests/scoring/test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers
tests/scoring/test_gate_a_provenance.py::test_live_board_passes
tests/unit/data/test_caiso_st_gas_peak_measured.py::…::test_registry_value_matches_the_committed_artifact
tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none
tests/unit/results/test_cache_solve_surface.py::…::test_a_bundle_solved_on_S1_is_not_addressed_on_S2
tests/unit/results/test_cache_solve_surface.py::…::test_sidecar_is_written_beside_the_config
```

They belong to other lanes (forecast keeper parity, the Gate-A board, a CAISO registry artifact,
an RPS registry row, and the D79 solve-surface sidecar) and are **reported, not touched** — fixing
another lane's red is outside record hygiene, and silencing one would be worse.
