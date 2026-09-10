# RESULT — caiso-273: the caiso-271 arm is RECOVERED and REGISTERED; two corrections to its own record

**Session caiso-273, 2026-09-10. CAISO only (rule 25 `[R-ISO-SCOPE]`). ZERO LP SPENT.**
Cards: **A** — register the caiso-271 arm or establish it is gone. **B** — the 2020/2021 intake,
launched as a separate parallel session (rule 12). **C** — no new lever lane opened (charter's
instruction honoured; see §7).
**KEEPER UNCHANGED at `2026-09-10-caiso-269-lateevening-clean`. NOT PROMOTED — the owner's call (§6).**

---

## §1 — Card A in five lines

1. **THE BUNDLES SURVIVE. The rule 31 `[R-RETAIN]` failure mode the charter anticipated did NOT
   occur.** caiso-271's four shard branches were auto-merged and then un-merged from `main`'s tip
   (`d96f2756`), so the commits remain reachable and all four per-year slim bundles **and** their
   `dispatch/` sidecars were recovered with `git checkout` at **zero LP cost**. No re-solve was
   needed and none was proposed.
2. **Registered** as `2026-09-10-caiso-271-egrid-family`, bundle
   `results/calibration/caiso271_egrid_family_span` — the four per-year shards composed into ONE
   4-year bundle in the parent (rules 16 `[R-ALLYEARS]` / 32 `[R-SHARD]` (d)).
3. **The recovered artifacts reproduce every published caiso-271 value** (§3). That is the check
   that this bundle IS that arm, done on the artifacts rather than taken on trust.
4. **Two corrections to `RESULT-caiso271`, both against interest** (§4): its G-IDENT count was
   wrong (two fields differ, not one — the second provably inert), and its G-DRIFT is now audited
   at code level rather than inferred from caiso-270's re-solve.
5. **A registration defect was found and repaired that is generic to every sharded lane** (§5) —
   it silently destroyed three committed CAISO bench parts on the first attempt and manufactured a
   false C4 failure. Reverted and fixed; worth knowing before the next composite is registered.

## §2 — Determination

```
RUN_ID=2026-09-10-caiso-271-egrid-family
DETERMINATION: NOT-YET [CAISO caiso 271 egrid family]
  — undocumented out-of-tolerance (FAIL) criteria: price_mean, price_shape
```

Rubric v3.6. Grade summary: scored 7 · target_grade 3 · commercial_grade 0 · ledgered 1 · fails 2.
Caveat ledger: `protective []`, `ledgered ["C3c price tail / scarcity (RT hourly)"]`,
`commercial_band []` (budgets protective_max 0, ledgered_max 1).

| criterion | tier | status | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** | PASS | PASS | PASS | PASS |
| C2 system volume | load-bearing | **PASS** | PASS | PASS | PASS | PASS |
| C3a mean LMP | load-bearing | **FAIL** | **FAIL +13.0 %** | PASS +4.4 % | PASS +8.7 % | PASS +7.9 % |
| C3b price duration/shape | load-bearing | **FAIL** | **FAIL 0.240** | PASS 0.082 | PASS 0.139 | PASS 0.107 |
| C3c price tail / scarcity | supporting | CAVEAT (ledgered) | — | 23 h vs 47 h | 0 h vs 35 h | — |
| C4 dispatch correlation | supporting | **PASS** | PASS | PASS | PASS | PASS |
| C6 governance | protective | **PASS** | — | — | — | — |
| C8 forced-energy share | protective | **PASS** | PASS | PASS | PASS | PASS |

**The determination is 2022 and nothing else.** Every 2023-2025 criterion passes. This is the
run-level aggregate rule 30 `[R-TOUCHPOINT-FOLD]` (b) warns about — a 4-year bundle carries ONE
determination that can hide rungs which passed on their own — and it is why the per-year column is
given here rather than a headline. **Rule 30(c) is untouched: a 2022 miss never downgrades the
ISO**, whose determination is the train-tier verdict on the keeper.

D-10 free-class C1: **all 6/6 · free 4/4** (pinned, excluded from free: CC_CHP, ST_CHP).
Reported-only C5a CO2 vs eGRID: 2022 −7.6 % · 2023 −11.2 % · 2024 −6.4 % · 2025 −5.3 %.

## §3 — Integrity: the recovered bundle reproduces caiso-271's published numbers

Scored from the recovered artifacts, against `RESULT-caiso271` §2 as published:

| year | C3a published | C3a re-scored | C3b published | C3b re-scored |
|---|--:|--:|--:|--:|
| 2022 | +12.999 % | **+13.0 %** | 0.2403 | **0.240** |
| 2023 | +4.383 % | **+4.4 %** | 0.0824 | **0.082** |
| 2024 | +8.659 % | **+8.7 %** | 0.1392 | **0.139** |
| 2025 | +7.882 % | **+7.9 %** | 0.1070 | **0.107** |

Every value matches to the scorer's printed precision.

**Config signature, re-verified in the parent on all four `run_config.json` (never from a shard's
claim):** `egrid_family_heat_rates true`, `mode backcast`, `git_sha 9ee5319b`,
`gas_price_override` 6.45 / 2.54 / 2.19 / 3.52, `weather_year` 2022 / 2023 / 2024 / 2025.

**Load-bearing artifact check:** `resolved_inputs.seam_import_cap` reads `source: "mic_partition"`
in all four (`cap_mw` 15780.0 / 16055.0 / 16452.0 / 16148.0), so no bundle solved on the retired
fitted fallback import scalar (rules 20 `[R-DOF]` / 24 `[R-REGISTRY]`).

**Composition legitimacy:** the four shard `scenario_config`s differ in **exactly two fields**,
`gas_price_override` and `weather_year`, both year-scoped by construction — so ONE config spans
every scored year, which is what rule 1 `[R-STRUCT]` condition (b) requires of a multi-year run.

## §4 — Two corrections to `RESULT-caiso271`, both against interest

### (1) G-IDENT counted one differing field; there are two

`RESULT-caiso271` §3 states G-IDENT verified "only `egrid_family_heat_rates` differs". Re-measured
against the keeper's own recorded `run_config`, **two** `ScenarioConfig` fields differ in every
year. The second is `nyiso_total_east_cutset_ttc`, `None → False`.

It is **provably inert for CAISO, three independent ways**:

* `pipeline/ttc.py::apply_iso_monthly_ttc` returns before ever reading it — `if iso != "NYISO":
  return ttc`;
* at the single read site the value is coerced, and `bool(None) == bool(False) == False`;
* the field **came into existence** at nyiso-224 (`5af5d6fb`) inside the 4-commit window between
  the keeper's `git_sha 8d627e64` and the arm's `9ee5319b`, and is recorded as a declared
  cache-key default-flip — so `None` is the keeper's "field absent", not a different setting.

**The one-mechanism claim stands; the count did not.** The correction changes no number and no
verdict, and is recorded because a G-IDENT that says "exactly one" when the artifact says two is
the kind of claim that erodes trust in every other gate in the same table.

### (2) G-DRIFT is now audited at code level, not inferred

`RESULT-caiso271` rested G-CTRL form 4 on caiso-270's keeper re-solve reproducing published
values. That is evidence, but rule 29 `[R-SCREEN]` (b) asks for a **code-level** audit. Done here
over `8d627e64..9ee5319b` (`src/market_sim`, `scripts/lib`, the calibration runners) — four
commits, **every changed hunk INERT for CAISO**:

| commit | what it touches | classification |
|---|---|---|
| `5af5d6fb` nyiso-224 | `pipeline/ttc.py`, NYISO constants, one `ScenarioConfig` field | INERT — hard `if iso != "NYISO"` gate |
| `15beb03c` CI repair | `scenarios.py` cache-key registration + a test inventory line + a solve-surface transcription repair | INERT — its own commit message states it **RESTORES** the pre-merge keys and leaves an armed run's key untouched |
| `9be52b9e` FR-22 | `scripts/lib/forecast_parity_registry.py` only | INERT — forecast path; a `mode="backcast"` run never enters it |
| `87bd1999` | merge commit | INERT — no content |

**All hunks INERT ⇒ form 4 valid ⇒ the keeper IS the control**, independently of caiso-270.

## §5 — A registration defect generic to every sharded lane

**Symptom.** The first registration attempt produced `DETERMINATION: NOT-YET — price_mean,
price_shape, **dispatch_corr**` with C4 reading `r=None, NRMSE=9.9` for 2024/2025 and "gas hourly
fit absent" for 2022, and C1 scoring **6/6** rows where the 3-year keeper scores 12/12.

**Cause.** Each rule-32 shard writes its own content-addressed input cache under
`results/calibration/_shared/<ISO>/` containing **only its own year**. A composite that inherits
one shard's `meta.json` `shared_inputs` therefore points at a **single-year** `campd` / `eia923` /
`eia930`, and `render_calibration_html.build_payload` rebuilds the benchmark from those — yielding
`plants=0, classFull=0` for every year but the one the inherited cache holds. Measured:

| year | bench plants (inherited 2023 cache) | after union |
|---|--:|--:|
| 2022 | 0 | 86 |
| 2023 | 86 | 86 |
| 2024 | 0 | 86 |
| 2025 | 0 | 85 |

**Collateral damage, and it was real.** `dashboard_add_run.py` rewrites the per-(ISO, year) bench
part for every year the run covers, so the empty benches were written over the **committed** ones:
`bench/CAISO/2022.json.gz` 180,689 → **714 bytes**, 2024 139,179 → **698**, 2025 117,724 → **685**.
Those parts are what every registered CAISO run is scored against.

**Repair.** Reverted the four bench parts to their HEAD bytes; unioned the three per-year caches
through the project's own writer (`scripts/lib/bundle_io.write_shared_input`, so the content-address
convention is unchanged); repointed the composite's `shared_inputs`; re-registered. After the
repair, `bench/CAISO/{2023,2024,2025}.json.gz` are **byte-identical to HEAD** and 2022 differs only
by the display-taxonomy label `COAL_PRB` being added to `meta.groupLabel` — **zero measured values
moved**, verified by a recursive JSON diff.

**The false C4 failure is retracted: C4 PASSES in all four years.** It was an artifact of scoring
against a benchmark this session had just emptied, not a property of the arm.

**For the next sharded composite:** union the per-year `_shared` caches *before* the first
`dashboard_add_run.py` call, and diff the bench part sizes against HEAD immediately after it.

## §6 — Disclosures against interest, and the promotion question

1. **The determination is NOT-YET**, on 2022's C3a and C3b — the same two criteria the charter
   already records as adjudicated closed.
2. **C3a degrades in all four years** versus the keeper (+0.100 / +0.053 / +0.115 / +0.012 pp).
   Unchanged from `RESULT-caiso271`; restated here so the registration does not read better than
   the run.
3. **D-1 ST_GAS FAILs in 2024 and 2025** (`profile_r` 0.468 and −0.036 against a 0.8 gate). These
   are **pre-existing in the keeper** — 0.417 and −0.009 there, so the arm is *better* in 2024 and
   worse in 2025 — and they do not gate: ST_GAS is 0.06 % of ISO load with 0.0 forced share, below
   rule 17 `[R-FORCED-BUDGET]`'s 2 % materiality floor. The keeper carries the same rows and reads
   CALIBRATED.
4. **D-4 off-window binding FAILs 28 of 52 rows**; the keeper carries 20 of 29. Comparable per
   year, pre-existing, and not this arm's doing.
5. **I did not re-derive the mechanism's own case.** §3-§4 of `RESULT-caiso271` stand as written
   apart from the two corrections in §4 above.

### RULE 31 `[R-RETAIN]`: THE PROMOTION QUESTION, PUT EXPLICITLY

**I have NOT promoted this. The keeper stays `2026-09-10-caiso-269-lateevening-clean`.**

The registered bundle's slim files are **committed**, so unlike caiso-271 this run is durable
independent of any container. The heavy layers (`dispatch/`, `unit_hourly`, `floors/`) are on this
container's local disk and are gitignored — **they will not survive session reclamation**, but they
are also still in git history at the four shard commits, so they are recoverable exactly as this
session recovered them.

The trade, unchanged and stated once: **all four pre-registered stop gates pass; C1 dispatch
improves in most cells and crosses no band; C3a degrades by 0.012-0.115 pp; the 2022 rubric failure
is untouched.**

* **(a) PROMOTE.** Defensible on the owner's standing ruling — *"if structural integrity improves
  but gates regress that may still be a keeper"* — and on rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`:
  a measured input replacing a blend that is a measured number for neither family, zero free
  parameters, which also retires the `MIXED_FACILITY_STEAM_HR` hand number.
* **(b) DO NOT PROMOTE, keep the flag default-off.** The honest reading of "it costs price and the
  dispatch gain is small". The code and the CAISO artifact stay for a later lane.
* **(c) PROMOTE THE ARTIFACT AND THE CODE, HOLD THE KEEPER.** caiso-271's own recommendation.

**caiso-273 makes no recommendation between them** — this session recovered and verified the run;
it did not re-open its merits.

## §7 — Card C: no new lever lane opened

The charter's instruction is honoured. This session proposed no object for the C3a/C3b-2022
residual and therefore owed no `caiso-272 §3.2` segment placement. The adjudication stands:
68 % of the +1.105 HR bias is the λ-in-a-gap hours (caiso-250/168, CLOSED), 35 % is the CT/ST tail
(caiso-261, DECLARED PERMANENT), and the CC offer ladder contributes −3 %.

**Carried forward, not acted on** (the charter is explicit that this is not this session's to
decide): 70.2 % of the C3a-2022 dollar miss is the DA-RT premium the rubric's out-of-representation
row calls something the test must not demand — this run's own scorer prints it as
`2022 da_diagnostic: +3.6 % vs DA (DA−RT premium $+7.65)` against the +13.0 % vs RT that fails.
**No rebase is proposed.** Counter-evidence is `caiso-272` §5.1 and must be carried at full
magnitude whenever this is quoted.

## §8 — Card B

Launched as a separate parallel session (rule 12), pinned to
`5df291c5254ec0871f9a84ed36ea6cc4e2a9f9f7`, branch `claude/caiso274-intake-2020-2021`: the
2020/2021 extension of `data/raw/reference/caiso-supply-consistent-demand/` and
`frontend/data/backcast/bench/CAISO/`, phase-0 availability census first. It runs zero LP and its
only writable paths under `frontend/data/backcast/` are `bench/CAISO/{2020,2021}.json.gz`.

---

**Next number: caiso-275.**
