# FFR-3U — Fix the bridge/un-bridge seam, and discharge D-11

**Session.** FFR Wave 3, the seam-fix lane, chartered by **owner decision D-11 + Addendum L.4**
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum L, signed 2026-08-04). Branch
`claude/ffr-3u-bridge-seam-fix-oj1fzo`, off `origin/main` **`6d24a84d`** (the packet's stated
HEAD `bf43122e` was already stale at session start; re-verified per the packet's own
instruction).

**Nothing is promoted, no default is flipped, no band is widened, no threshold is moved, no
marker is spent, and no window is widened to make anything legal.** The gate re-cut is a LATER
lane. **FH-4/FH-5 remains a MANAGER box** (Addendum I.1) and reporting this lane green does not
open it.

---

## 0. Headline

1. **The seam is FIXED and the illegal window now FAILS CLOSED.** The un-bridging clause is
   *scoped* to genuine T1-X crossover forward years, not deleted. At base 2021 the runner again
   bridges **2022** (validation tier) and **2026** (locked-test tier). §1.
2. **One definition, not two.** `_validate_window` now policy-checks the set the **runner** will
   actually solve, through the runner's own predicate over the boundary `build_config` actually
   sets. Three predicates became one. §2.
3. **The banner can no longer lie.** Its promise is derived from that same predicate and
   **asserted against the realized evolution ledgers at completion**; a mismatch is a hard
   `SystemExit`, not a warning. §3.
4. **D-11's three conditions: (a) DISCHARGED by verified absence, (b) DISCHARGED mechanically,
   (c) DISCHARGED.** The one that protects the tier — (b), the cache-key invalidation — is a
   refusal in code at the single cache path seam, not a ledger note. §5.
5. **Exposure audit: 0 affected artifacts, as a MEASUREMENT.** All **82** committed
   hindcast-harness legs were replayed through the fixed predicate using each leg's own recorded
   window and boundary. None solved a year the bridge contract required. §6.
6. **Solve-inert: all seven measured cache keys byte-identical before and after**, and no keeper
   moved. §7.
7. **One finding to report, not a threshold relaxed:** the FC-7 artifact fixture was asserting a
   solve-year set inconsistent with its own declared window, and the new parity assertion
   correctly refused it. The fixture was made honest; the assertion was not weakened. §4.2.

---

## 1. The fix — scoped, not deleted

### 1.1 What was wrong (not re-derived; measured by FFR-3Q §2.2.1, confirmed here)

Two predicates disagreed about what a "forward year" is.

```python
# runner.py, before
is_bridge = (config.hindcast and year in HINDCAST_BRIDGE_YEARS
             and not config.is_crossover_forward_year(year))
```

A T1-FF full-forward window points `crossover_forward_year` at its **own base year**. At base
2021 that made *every* year ≥ 2021 a "crossover forward year", so 2022 was un-bridged and
**solved** — and 2026 would have been too, for any window that reached it.

### 1.2 Why the clause is scoped rather than removed

The clause is **correct for its original purpose**. A genuine T1-X crossover's forward years are
2026/2027, solved in forecast mode on forward drivers, consuming no measured H1-2026 actuals —
which rule 22 `[R-HOLDOUT]` explicitly permits. Deleting the clause would break that legal path
(the T1-X window would stop solving 2026 and the crossover instrument would silently lose a
year). What was wrong was not the permission but its **reach**: re-pointing the boundary at a
base year extended a 2026-specific permission to a year for which it was never true.

The new predicate (`config/scenarios.py::crossover_unbridges_year`) requires **both** conjuncts:

| conjunct | closes |
|---|---|
| the boundary sits **past** the window's own base year (a genuine T1-X, not a T1-FF) | 2022 **and** 2026, for every full-forward posture |
| `year >= CROSSOVER_FORWARD_BOUNDARY_YEAR` (2026) | 2022, for **any** run whose boundary is ever pointed below 2026 |

Either conjunct alone closes the FFR-3Q breach; both are kept because they close it for
different reasons, and a future posture that defeats one should still hit the other.

**Both exposures measured at this HEAD**, T1-FF base 2021 (boundary 2021):

| year | before (`is_crossover_forward_year`) | **after** (`is_crossover_unbridged_year`) | ⇒ `is_bridge` |
|---|---|---|---|
| 2022 | un-bridged → **SOLVED** | bridged | **True** |
| 2026 | un-bridged → would be solved | bridged | **True** |

Genuine T1-X (boundary 2026, start 2023) is **unchanged**: `solved [2023, 2024, 2025, 2026,
2027]`, `bridged []`.

### 1.3 The separation the defect collapsed

`is_crossover_forward_year` is retained, unchanged, and is still the gate of the **input stack**
(the measured demand loader, the F923 overlay, the forward gas trajectory) — 2022 on a base-2021
T1-FF run genuinely *is* a forward year for its drivers. `is_crossover_unbridged_year` is the
new, separate **rule-22 legality** predicate. Two questions, two predicates; one predicate
answering both is what produced the breach. Pinned by
`test_forward_stack_and_bridge_legality_are_different_questions`.

### 1.4 What was deliberately NOT changed

`runner.py`'s entry-lookahead guard (`next_year not in HINDCAST_BRIDGE_YEARS`) still suppresses
the look-ahead into 2026 even on a genuine crossover, where 2026 is solved. Routing it through
the shared predicate would *enable* a read that is currently suppressed — a behaviour change on
a legal path, in the permissive direction, outside this lane's charter. It is conservative, it
leaks nothing, and it is left alone. Recorded here so a later lane does not mistake it for an
oversight.

---

## 2. One definition, not two (rule 19 `[R-ONE-MECH]`, applied to the guard)

Before this lane the same question was answered in **three** places, with three different
expressions — and, of the three, the one at `assert_forward_drivers` was already correctly
scoped, which is why the leak surfaced as an inconsistency rather than an error.

| site | before | after |
|---|---|---|
| `runner.run_scenario_iso` (decides what solves) | `not config.is_crossover_forward_year(y)` | `runner.is_hindcast_bridge_year(...)` |
| `run_capacity_hindcast._validate_window` (decides what is checked) | own set from the `--crossover` **CLI flag** | `window_solve_years(...)` → the runner's predicate |
| `run_capacity_hindcast.assert_forward_drivers` | `y >= 2026 and config.is_crossover_forward_year(y)` | `config.is_crossover_unbridged_year(y)` |

New single sources:

* `market_sim.config.scenarios.crossover_unbridges_year` — the un-bridging clause, and
  `ScenarioConfig.is_crossover_unbridged_year`, its config-bound delegate.
* `market_sim.config.scenarios.CROSSOVER_FORWARD_BOUNDARY_YEAR = 2026` — the literal moved into
  `src` (it is half of the bridge predicate, which `src` owns).
  `run_capacity_hindcast.CROSSOVER_FORWARD_YEAR` is now an **alias** of it, the same
  anti-drift pattern `HINDCAST_BRIDGE_YEARS` already used.
* `market_sim.runner.is_hindcast_bridge_year` / `hindcast_solve_years` — the bridge decision and
  the realized solve set.
* `run_capacity_hindcast.window_forward_boundary` — **one** resolution of the boundary, read by
  BOTH `build_config` (which sets the field) and `_validate_window` (which checks it). This is
  the exact gap FFR-3Q fell through: the guard read a CLI flag, the runner read the config's
  boundary, and nothing forced them to be the same window.

Consequence: **no year can be exempted by the guard that the runner would solve as a
quarantined bridge year**, because the exemption and the solve are now the same expression.

---

## 3. The banner remedy — a promise that is mechanically checked

`run_capacity_hindcast.main` now:

1. computes `promised_solve_years = window_solve_years(...)` and its complement
   `promised_bridge_years` **from the runner's predicate**, immediately after `_validate_window`;
2. prints them, for **every** run, freeze or not:

   ```
   [governance] this window SOLVES [2021, 2023, 2024, 2025] and BRIDGES [2022] (evolved
   across, LP never solved, measured data never read — rule 22). Asserted against the
   realized evolution ledgers at completion.
   ```

   The old freeze banner's static clause `bridges [2022, 2026] are never solved or read` was
   **removed**: it was a true statement about the *constant* and, as FFR-3Q showed, not
   necessarily about the *run*. The new line states this window's own resolved sets.
3. after the solve, compares the promise to `solved` / `bridged` **read back from the evolution
   ledgers the solve itself wrote**, and on mismatch raises:

   ```
   SOLVE-YEAR PARITY FAILURE (rule 22 STOP-THE-LINE): the launch banner promised
   solved [...] / bridged [...], but the run realized solved [...] / bridged [...].
   ```

It raises rather than warns because by the time it can fire, the quarantined year has already
been solved and its data read; the only correct remaining behaviour is to refuse to emit a
`meta.json`, a `run_config.json`, or anything registrable from that bundle, and to name the
cache key as contaminated in the message. A governance banner not tied to behaviour is
decoration — this is the tie.

---

## 4. The tests, and the class they close

All in `tests/scoring/test_full_forward_hindcast.py::TestBridgeSeam` (11 tests, 11 subtests).

### 4.1 What each closes

| test | closes |
|---|---|
| `test_base_2021_bridges_2022` | **(a)** the instance: `is_bridge(2022)` is True at base 2021 and the realized solve set is `[2021, 2023, 2024, 2025]` |
| `test_base_2021_bridges_2026` | **(c)** the 2026 analogue — the locked-test exposure nothing has reached yet |
| `test_forward_stack_and_bridge_legality_are_different_questions` | the §1.3 separation, so a future "simplification" back to one predicate fails here |
| `test_genuine_crossover_still_unbridges_2026` | the clause is scoped, **not deleted** — T1-X still solves 2026/2027 |
| `test_plain_hindcast_unchanged` | T1-H byte-posture: `[2021, 2023, 2024, 2025]` |
| **`test_guard_and_runner_agree_on_every_posture`** | **(b)** the CLASS |
| `test_guard_checks_the_boundary_the_config_carries` | the specific gap: guard flag vs config boundary |
| `test_banner_and_completion_assertion_share_the_predicate` | the banner remedy is wired, not merely printed |
| `test_no_second_predicate_at_either_site` | rule 19 at the source level: neither site may re-derive bridging |
| `test_boundary_constant_is_single_sourced` | the 2026 literal cannot drift between `src` and `scripts` |
| `test_contaminated_cache_keys_refuse_a_present_bundle` | D-11 condition (b) |

### 4.2 The parity test — what class it closes

`test_guard_and_runner_agree_on_every_posture` runs **seven** CLI postures (plain T1-H long and
short, T1-FF at bases 2021/2023/2024, T1-X long and short). For each it asserts:

* `_validate_window` accepts the window (it is legal), **and**
* the set the guard policy-checked equals the set the runner will realize — where the runner's
  set is rebuilt **from the config `build_config` actually produces**, i.e. the chain
  *CLI args → `build_config` → runner predicate*, not a re-reading of the guard's own inputs;
* and no quarantined year survives into the solve set except as a genuine crossover forward year.

That is the whole family, not the instance: re-pointing a boundary, adding a new posture flag,
or re-deriving either side from a different predicate breaks **this test** instead of breaking a
holdout year. It is the test whose absence made FFR-3Q's banner unfalsifiable.

**Verified it actually catches the defect.** The old semantics were replayed into
`crossover_unbridges_year` (`return year >= crossover_forward_year`) and the suite re-run: **4
tests fail**, including the parity subtest on exactly the `(2021, 2025, crossover=False,
forward_from_base=True)` posture. In that replay `_validate_window(2021, 2025, False, True)`
**raises `SystemExit`** — i.e. with the guard sharing one predicate, the illegal window now
**fails closed** instead of silently dropping the year. Restored and re-verified green.

### 4.3 One finding — a fixture, not a threshold

`tests/scoring/test_hindcast_run_config_artifact.py` stubbed the solve seam with a single
hard-coded ledger `{2022: bridge, 2023: {}}` for **every** leg, including the T1-H leg whose
window is 2021–2025 and the T1-X leg whose window is 2023–2027. The new parity assertion
correctly refused all three legs: a fixture modelling a run that solved years its own declared
window never contained cannot exercise the tail it claims to.

**The fixture was made honest; the assertion was not relaxed.** `TIER_LEGS` now declares each
leg's `(start, end, crossover, forward_from_base)` window and the stub ledger is *built from it*
through `window_solve_years`, so the fixture models the run the argv actually describes — and
the tests now additionally exercise the parity path. Reported here per the charter: a
previously-passing test changed, and this is the reason.

### 4.4 Suite state

* `tests/scoring/` + `tests/unit/config/` + `tests/unit/pipeline/`: **1573 passed**, with **6
  pre-existing failures on clean `main`** — `test_cache_key_default_flip_guard` ×2
  (`ercot_storage_rt_offer_surface` missing from `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`) and
  `test_ff_readiness_battery` ×4. Baselined by stashing this lane's diff and re-running: all six
  fail identically on `main`, none is touched by this change, and none is owned here (Addendum
  K.5 records them unowned).
* `tests/regression/`: **370 passed, 5 skipped, 7 failed** — all 7 **environmental, and
  identical on clean `main`**: this container has not run `scripts/regenerate_clean.py` (a
  ~65 min prerequisite this lane did not need, since it runs no solve), so
  `data/clean/confirmed-retirements` is absent and every end-to-end leg refuses with
  `confirmed-retirements: clean partition for ERCOT is absent`. Baselined by stashing the diff:
  `test_fleet_arrays_golden` and `test_soundness::test_rerun_is_deterministic` fail the same way
  with this lane's changes reverted.
* `scripts/check_mechanism_matrix.py`: **rc=0**. The 222 anchor-drift warnings are pre-existing
  and **unchanged in count** before/after this diff (measured both ways).
* `scripts/check_cache_key_registration.py`: fails on the same pre-existing
  `ercot_storage_rt_offer_surface` gap, unrelated to this lane.

---

## 5. D-11's three conditions — per-condition discharge

Owner decision D-11 (Addendum L.2) makes the no-spend determination for ERCOT 2022
**conditional** on all three. Each is reported with how it was verified.

### (a) Delete the two quarantined bundles — **DISCHARGED by verified absence**

| check | result |
|---|---|
| `find / -xdev -maxdepth 8 -type d -name b99600bceb8cb6b8 -o -name 5c352508039513da` | **no match anywhere on the box** |
| `find / -xdev -name QUARANTINE-DO-NOT-REGISTER.txt` | **no match** |
| `git ls-files \| grep 'b99600bceb8cb6b8\|5c352508039513da'` | **0** |
| `git rev-list --all --objects \| grep ...` | **0** — never committed, on any branch, at any point |
| `git ls-files \| grep -E 'year_(2022\|2026)(_p1)?\.parquet'` | **0** committed dispatch artifacts for any bridge year |

**Stated plainly:** the bundles were produced in FFR-3Q's own ephemeral session container, which
has since been reclaimed; they were never committed or pushed, so they exist in no reachable
location I can find, and there is no `rm` for me to run. That is *confirmed absence*, which is
what the condition's substance asks for ("a deleted bundle is a fact"), but it is not me having
executed the deletion, and the difference is the owner's to weigh. The residual risk — someone
restoring an old results tree — is covered by (b), which makes a re-materialized bundle at
either key a hard error rather than a silent cache hit.

### (b) Invalidate the two cache keys — **DISCHARGED, mechanically**

This is the condition that protects the tier, and a ledger note would not have done it. **The
seam fix moves no cache key** (§7), so the very config that solved 2022 still hashes to
`b99600bceb8cb6b8` / `5c352508039513da`; without a refusal in code, a later run with that config
would cache-hit the contaminated 2022 solve **with no banner at all** — exactly the hazard
Addendum M.1 restated as live and undischarged.

Implemented as `market_sim.results.cache.CONTAMINATED_CACHE_KEYS` +
`assert_cache_key_uncontaminated`, called from **`get_cache_path`** — the single seam every
cache read *and* write routes through (`is_cached`, `save_result`, `load_result`,
`get_config_path` all resolve through it), so no reader can bypass it.

Scope chosen deliberately: **a bundle directory existing at either key is a hard `RuntimeError`**
naming the key, the reason, and the path to delete; an **absent** directory is a no-op. That
closes the reuse channel permanently without blocking the eventual re-probe, which re-solves on
a clean tree — and under the fixed seam that re-solve *bridges* 2022 rather than solving it.

**How it was verified:**

* `test_contaminated_cache_keys_refuse_a_present_bundle` — under a temporary cache root, with the
  directory absent both keys are a no-op and `is_cached` returns False; with the directory
  present, `get_cache_path` **and** `is_cached` both raise `RuntimeError: … QUARANTINED …`; a
  non-denylisted key under the same root is untouched. Green.
* The key set is asserted to be exactly `{b99600bceb8cb6b8, 5c352508039513da}`, so a later
  edit that empties or widens the denylist fails the test.
* Recorded as **cache epoch 2026-08-04b** in `results/cache.py`'s ledger, naming what is
  invalidated (exactly two bundles) and what is not (everything else).

### (c) Disclose on the peer-review §4 standing list — **DISCHARGED**

Added to `docs/forecast-readiness-peer-review-2026-07.md` §4, **inside the quoted disclosure
block** that every forecast deliverable carries verbatim — not in a lane doc and not as a
footnote. It states the incident, the defect in one sentence, that no number was ever read, the
D-11 determination *and its conditions*, the fix, the audit result, and why a
holdout-discipline incident is material to reading any out-of-sample claim in this program.

**None of the three could not be met.** The determination does not flip on this lane's evidence.
The one judgement call the owner may want to revisit is (a)'s form — verified absence rather
than an executed deletion — and it is stated above rather than papered over.

---

## 6. Exposure audit — a result, not an expectation

FFR-3Q §2.2.4 item 4 flagged this as *reasoned, not audited*: no prior T1-FF window contains a
bridge year, "so the exposure looks nil — but that is reasoning from the window list."

**Method.** Every committed `.json` under `frontend/data/`, `results/` and `docs/` carrying a
`solved_years` field was replayed through the **fixed** predicate
`runner.is_hindcast_bridge_year`, using **that artifact's own recorded `start_year` and
`crossover_forward_year`** — not a list of windows I believe were run. A solved year the fixed
predicate calls a bridge year is a hit.

**Scope split, stated explicitly.** Hindcast-harness legs (`hindcast=True`: T1-H / T1-X / T1-FF)
carry the bridge contract and are the audited set. Full-horizon forecast legs (`run_full_horizon`,
`hindcast=False`) carry no bridge contract at all — 2026+ is an ordinary forecast year there,
which rule 22 permits — so they are counted and reported, never flagged.

**Result.**

| | |
|---|---|
| hindcast-harness legs audited | **82** — 18 `crossover` (boundary 2026), 18 `full_forward` (boundary **2023**), 46 plain `hindcast` (boundary None) |
| full-horizon forecast legs counted and skipped | 144 |
| **legs that solved a year the bridge contract required** | **0** |
| hindcast legs whose window *contains* 2022 | 46 — every one solved `[2021, 2023, 2024, 2025]`, i.e. 2022 correctly bridged |
| committed `evolution_2022.json` records | 25, **all** carrying `bridge: true` |
| committed `year_2022*.parquet` / `year_2026*.parquet` dispatch artifacts | **0** |

**Audited, not assumed:** all 18 committed `full_forward` legs carry boundary **2023**, i.e.
every one is base 2023 — which is what FFR-3Q *expected* from the window list and what this
audit now *measures* from the artifacts. FFR-3Q's inference was correct.

**One artifact worth naming so nobody trips on it.**
`results/calibration/neiso61_netrev_margin_2022/` holds `class_hourly_2022.parquet` /
`system_2022.parquet`. That is a **backcast calibration** bundle, not a hindcast-harness leg: it
carries no bridge contract, and NEISO holds a `complete` marker authorizing the 2022 validation
ladder. Its authorization is outside this lane's scope and was not audited here; it is flagged
only because a text search for "2022" hits it and a reader deserves to know why it is not a
finding.

**No second STOP-THE-LINE.** No committed artifact solved 2022 or a quarantined 2026.

---

## 7. Solve-inertness on the legal path

A guard fix must not move a key or a keeper.

**Cache keys, measured before the first edit and after the last** (identical command, same
process shape, `MARKET_SIM_DATA_ROOT` unset):

| config | before | after |
|---|---|---|
| `ScenarioConfig()` (pinned default) | `603c2498bf71d21d` | `603c2498bf71d21d` |
| ERCOT 2023 backcast | `df386bca96a1d288` | `df386bca96a1d288` |
| CAISO 2023 backcast | `a9afddae291525c1` | `a9afddae291525c1` |
| PJM 2023 backcast | `9834b2018b598423` | `9834b2018b598423` |
| MISO 2023 backcast | `2a1252c3acae89e9` | `2a1252c3acae89e9` |
| NYISO 2023 backcast | `fd15030b3ee60f11` | `fd15030b3ee60f11` |
| NEISO 2023 backcast | `5b1633171fead559` | `5b1633171fead559` |

`diff` of the two captures is **empty**. No `ScenarioConfig` field was added, removed or
re-defaulted, so no key *could* move — and it was measured rather than argued. **No keeper is
touched**; no keeper shard, no `calibration-complete.json` entry, no `holdout-freeze.json`.

**Legal postures still validate** (measured, §4.2's seven-posture table):

* `_validate_window(2023, 2025, crossover=False, forward_from_base=True)` → **PASS**
* plain T1-H `_validate_window(2021, 2025, crossover=False, forward_from_base=False)` → **PASS**,
  realized solve years **`[2021, 2023, 2024, 2025]`**, 2022 bridged — unchanged
* T1-X `_validate_window(2023, 2027, crossover=True)` → **PASS**, `[2023, 2024, 2025, 2026,
  2027]` — unchanged
* `_validate_window(2021, 2026, crossover=False, forward_from_base=True)` → **REFUSED** (the
  end-year cap, which is the outer of the two closures on the 2026 exposure)

---

## 8. Governance position

* **No marker spent, no marker file modified.** `final` still EMPTY, `complete` unchanged,
  `holdout-freeze.json` unmodified, `scripts/lib/holdout_policy.py`'s tier sets untouched.
* **No window was widened to make anything legal.** The fix makes the illegal window fail
  closed; it never makes an illegal solve permitted. Verified by the defect replay in §4.2.
* **No solve was run.** This lane ran no LP, solved no T1-FF window, and did not re-run the FH-1
  §3.3 gate.
* **Rule 28 `[R-MECH-MATRIX]`: no cell was touched, and that is the correct outcome.** No
  mechanism was proposed, tested or added — no `ScenarioConfig` field was added, removed or
  re-defaulted, and nothing here is a solve-affecting lever. `check_mechanism_matrix.py` passes
  at rc=0. A guard that decides *which years may be solved* is holdout policy, not a market
  mechanism, and giving it a matrix row would misfile it.
* **Rule 27 `[R-PUSH]`:** every edit was made locally with the Edit tool; no file was rewritten
  from response content. Blob verification after push is recorded in §9.

### What this lane does NOT claim

* **The gate re-cut is a LATER lane.** G.5(a)'s FH-1 §3.3 re-probe is unexecuted. FFR-3Q §2.1's
  pre-registration survives intact and is reused verbatim by whoever runs it.
* **FH-4/FH-5 remains a MANAGER box** (Addendum I.1). This lane landing does not open it, and
  reporting green is not the lift.
* **The re-probe's result is unknown and unpredicted here.** Nothing in this lane says anything
  about what the base-2021 window will show.
* **D-11(a) is discharged by verified absence, not by an executed deletion** (§5a) — stated so
  the owner can weigh the form, not just the outcome.

---

## 9. Files changed

| file | change |
|---|---|
| `src/market_sim/config/scenarios.py` | `CROSSOVER_FORWARD_BOUNDARY_YEAR`, `crossover_unbridges_year`, `ScenarioConfig.is_crossover_unbridged_year` |
| `src/market_sim/runner.py` | `is_hindcast_bridge_year`, `hindcast_solve_years`; the year loop's `is_bridge` routes through them |
| `src/market_sim/results/cache.py` | `CONTAMINATED_CACHE_KEYS` + `assert_cache_key_uncontaminated` at `get_cache_path`; cache-epoch ledger entry 2026-08-04b |
| `scripts/run_capacity_hindcast.py` | `window_forward_boundary` / `window_solve_years`; `_validate_window` and `build_config` share the boundary; `assert_forward_drivers` uses the shared predicate; banner derived + SOLVE-YEAR PARITY assertion; `CROSSOVER_FORWARD_YEAR` aliased to `src` |
| `tests/scoring/test_full_forward_hindcast.py` | `TestBridgeSeam` (11 tests) |
| `tests/scoring/test_hindcast_run_config_artifact.py` | window-consistent stub ledger (§4.3) |
| `docs/forecast-readiness-peer-review-2026-07.md` | §4 standing-disclosure entry (D-11 condition c) |
