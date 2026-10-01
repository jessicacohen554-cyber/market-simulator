# FINDING — capx D83: `evolution_2022.json`'s missing adequacy block is a WRITER defect

**Lane:** capx D83, under owner ruling **Q60** (2026-09-07, capx ledger §0bd.3(c) — "D84 first,
D83 after"; D84 landed and was armed, so this lane became due). Branch
`claude/capx-d83-evolution-2022-adequacy`. **DATA PROFILE: pjm.** MODEL: Opus.

**Charter scope:** a diagnosis, and its repair *only if* the cause is a writer defect. No mechanism,
no arm, no default change, no re-registration — and none is proposed.

> **Independently verified 2026-09-08** — `FINDING-capx-d83-2026-09-08.md`. The (i) verdict
> holds and is *strengthened*: the affirmative operand proof of §2 is generalized from this one
> reproduced bundle to the whole committed corpus (10/10 post-D52 bridge ledgers carry a
> non-`None` screen operand; **0/26 show the failed-guard signature**; the 16 silent ones are a
> pre-D52 vintage whose *solved* years lack the block too). The recurrence guard and the
> zero-key-move census were both re-measured at a later HEAD. §7's routed item is still open.

---

## 0. The verdict, and the line

**(c)(i) — a RECORDING defect.** The screen ran correctly in 2022 and the writer failed to record
what it ran on. It is **not** (ii): the year's capacity decisions were taken on exactly the operands
its neighbours use, and this finding proves that affirmatively rather than inferring it from the
repair looking small (§2).

**The named line is `src/market_sim/runner.py:2525`** — the `if is_bridge:` evolution-ledger writer
inside `run_scenario_iso`. It builds its payload as a **second, hand-maintained field list** instead
of sharing the solved-year writer's, and that list had fallen eight fields behind.

The gate is `runner.py:237`:

```python
HINDCAST_BRIDGE_YEARS = frozenset({2022, 2026})
```

2022 is a rule-22 quarantined year that a capacity-hindcast window spans but must never solve. The
fleet is still evolved across it; the LP never runs. That branch `continue`s at line 2558, so the
bridge year never reaches the solved-year ledger writer at line ~4930 — and nothing connected the
two lists.

**There is no year-scoped branch, no early return past the screen, no missing delivery-year mapping,
no 2022-only data gap, and no swallowed exception.** Each was ruled in or out by reading, not
guessing; the branch above is the whole cause.

### The predicate holds with zero exceptions

Over **all 72 committed `evolution_2022.json` / `evolution_2026.json` ledgers** in the repository:

| | count |
|---|---|
| carrying the adequacy block | 46 |
| **missing it** | **26** |
| …of those 26, `bridge: true` | **26 / 26** |

By ISO the 26 are PJM 11, MISO 7, NEISO 3, NYISO 3, CAISO 1, ERCOT 1. The 46 that carry the block
are the `evolution_2026.json` ledgers of **forecast-mode** runs, where `is_hindcast_bridge_year`
returns `False` because `hindcast` is `False` — so 2026 is solved, not bridged. *Missing adequacy
block ⟺ `bridge=True`* is exact. This is not a PJM problem and never was.

---

## 1. (a) Reproduced at my own HEAD

| | |
|---|---|
| invocation | `python3 scripts/run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2022 --out-dir results/hindcast/pjm-d83-repro` |
| bundle | `results/hindcast/pjm-d83-repro/PJM/5600d19386a1aba9` |
| file | `evolution_2022.json` |
| tree | `origin/main` @ `4e4ad90d`, runner **unmodified** (the run was launched before the repair was written and Python had already imported the module) |
| harness banner | `this window SOLVES [2021] and BRIDGES [2022]` |

The eight fields are absent, exactly as D75 §6 item 3 and `FINDING-capx-d75r-2026-09-06.md` §6
item 1 report:

```
adequacy_requirement_mw · capacity_reserve_position · firm_clean_accredited_mw
renewable_credit_applied · solar_cap_mw · storage_firm_mw · storage_power_mw · wind_cap_mw
```

**Within one artifact family, as the charter requires.** The window's own 2021 carries every one of
them, and the committed `pjm-2021-2025-realized-t1h-d78-sectorgate` bundle
(`git_sha 99245361`, `solved_years [2021, 2023, 2024, 2025]`, `bridged_years [2022]`) carries them in
2021 and 2023–2025 and drops exactly those eight — and **only** those eight, with no bridge-only
key — in 2022. The comparison is one run, not a cross-vintage one.

*(A one-line caveat on the neighbouring D78 bundle: it is a genuine one-run comparison, but its
`entry_screen_diagnostics` key is config-gated and my HEAD-default repro does not arm it. That key is
present in the D78 bundle's 2022 bridge ledger, so it is not part of the defect.)*

---

## 2. (c) Why this is (i) and not (ii) — the affirmative proof

The stop gate asks for evidence that the adequacy operand **existed at screen time**. Four
independent lines, three of them from the bridge year's own artifacts.

### 2.1 The screen block runs BEFORE the bridge branch, and consumes the pools

`runner.py:2214–2240`, unconditional, ~300 lines above the bridge branch:

```python
screen_requirement_mw = resolve_adequacy_requirement_mw(config, iso, peak_demand, year)
screen_entering_firm_mw = accredited_firm_capacity_mw(
    fleet,
    float(prior_results.get("wind_cap_mw", 0.0) or 0.0),
    float(prior_results.get("solar_cap_mw", 0.0) or 0.0),
    float(prior_results.get("storage_firm_mw", 0.0) or 0.0),
    ...
)
```

The three quantities threaded there are three of the four the charter names as missing. In
`accredited_firm_capacity_mw` they are literal additive terms:
`internal = storage_firm_mw + wind_pool*credit("wind") + solar_pool*credit("solar") + …`.

### 2.2 The bridge year's own ledger already proves the call executed

`evolution_2022.json` records, *pre-repair*:

```
screen_adequacy_requirement_mw : 163268.9
screen_entering_firm_mw        : 185264.153
screen_reserve_position        : 1.134718
```

`screen_entering_firm_mw` is non-`None`, so the guard
(`fleet is not None and prior_results is not None and peak_demand > 0`) passed and the accreditation
ledger was built **with the pools inside it**. The pools it used are recoverable from the previous
solved year — 2021 records `wind_cap_mw 10153.9`, `solar_cap_mw 4549.8`, `storage_firm_mw 3801.526`,
all non-zero — which is precisely the manual reconstruction D75-R had to perform twice.

### 2.3 The 2022 screen made real decisions, and logged them

From the reproduction's own log, in the bridge year:

```
year 2022 PJM capacity supply clearing: price 90.41 $/MW-day (33.00 $/kW-yr),
  cleared 170224 of 181435 MW (position 1.0426; census 1.1113),
  price takers 23332 MW, 1399 offers / 133 uncleared [marginal_offer_sets_price]
year 2022: R-NEW pipeline executed 103 exit(s), 8693 MW
```

A year with no adequacy operand cannot clear 1,399 offers against a requirement, leave 133 uncleared
and execute 103 pipeline exits. The pre-repair 2022 ledger records the outcome in full — a
`capacity_clearing` block of 16 keys, **147** retirement rows, 6 `thermal_additions`,
`entry_decided_mw_by_tech` and `sector_gated` — identically in the reproduction and in the committed
D78 bundle. The screen ran; the writer stayed silent.

### 2.4 The restored values reconcile against their neighbours

Post-repair (§4), every restored field lands where an interpolation between 2021 and 2023 says it
must, and one identity closes exactly:

| field | 2021 | **2022 (restored)** | 2023 |
|---|---|---|---|
| `wind_cap_mw` | 10153.9 | **10153.9** | — |
| `solar_cap_mw` | 4549.8 | **4549.8** | — |
| `storage_firm_mw` | 3801.526 | **3801.526** | — |
| `storage_power_mw` | 5357.6 | **5357.6** | — |
| `renewable_credit_applied` | wind .41 / solar .1064 | **wind .41 / solar .1064** | — |
| `firm_clean_mw` | 3283.7 | **3286.2** | 3287.5 |
| `firm_clean_accredited_mw` | 1247.806 | **1248.756** | 1249.25 |

The four pool/storage rows are unchanged from 2021 because 2022's evolution added no VRE and no
storage (`renewable_additions: []`, `storage_additions: []`) — the arithmetic the ledger should
always have shown. `firm_clean_mw = 3286.2` matches the run's own
`Loaded PJM 2022 hydro budget: … 3286 MW nameplate` to the tenth. And the restored
`capacity_reserve_position = 1.134718` **equals the already-recorded `screen_reserve_position` to
all six decimals** — the same identity that holds in every solved year of the D78 bundle
(2023: 1.076898 = 1.076898; 2024: 1.063785; 2025: 1.011564).

**Conclusion.** The operand existed, was consumed, and drove decisions. Repairing the writer records
what happened; it does not paper over a real absence.

---

## 3. The repair

`src/market_sim/runner.py`, the `if is_bridge:` block **only**. The solved-year writer is not
touched — deliberately, so no solved year's ledger can move by construction.

Every restored field uses the **identical expression** the solved writer uses, and every input was
already live in scope at the branch:

| field | why it exists at the bridge point |
|---|---|
| `wind_cap_mw` / `solar_cap_mw` | `wind_cap` / `solar_cap` are loaded once outside the loop and grown **in place** by this year's own `renewable_additions` at `runner.py:2410` — above the branch |
| `storage_power_mw` | `storage_units` is post-entry (`apply_storage_new_entry`, above the branch) |
| `storage_firm_mw` | same `storage_units`, through the one `storage_accreditation_credit` resolver (rule 19). It cannot be read off `prior_results`, which the bridge leaves pointed at the last **solved** year by design |
| `renewable_credit_applied` | `renewable_credits_applied(...)` on the same fleet, pools, peak and `accreditation_year` the screen used |
| `firm_clean_mw` / `firm_clean_accredited_mw` | fleet state plus `modelled_hydro_nameplate_mw`, which is cached per `(iso, year)` and **was already called for this year** by the screen's own `accredited_firm_capacity_mw` |
| `capacity_reserve_position` | `curve_reserve_position`, computed at `runner.py:2143` — above the branch |

**Four fields stay `None`, and that is faithful rather than a second gap.** `peak_demand` is
**re-derived from the LP's own load at `runner.py:2640`, below the branch**, so a bridge year has no
LP peak; `adequacy_requirement_mw` and `reserve_margin` are defined on that peak, and `rps_dual` is an
LP dual. They are now recorded as explicit `None` so the two years share one schema. The **seam**
peak and requirement the screens really consumed were already recorded by the capx D52
`screen_ledger_fields` block, and remain the reproducible record.

**Zero new data reads.** Every helper invoked was already invoked for the same year by the screen.

### 3.1 Scope note, stated rather than slipped in

`firm_clean_mw` was *present* and explicitly `None`, so it is not one of the eight absent keys the
charter names. It is repaired anyway, for one reason: it is the documented companion of
`firm_clean_accredited_mw` (FFR-3B — "reported alongside rather than replacing the nameplate basis,
because silently changing a field's units is how the next reader gets misled a second time"), and
adding the accredited half while leaving the nameplate half `None` would recreate exactly the
misreading that comment guards against. It is fleet state, not LP state, and costs no new read.

---

## 4. Proving the repair inert where it must be

### 4.1 Zero key moves — measured, both ways

`scripts/probes/capxd83_bridge_ledger_key_census.py` computes the **live** `ScenarioConfig.cache_key()`
for every committed `run_config.json` payload. Run on the pre-repair tree and the post-repair tree:

```
hashed 230 committed payloads (reproduced 123, mismatch 107, unbuildable 0)   [before]
hashed 230 committed payloads (reproduced 123, mismatch 107, unbuildable 0)   [after]
diff docs/handoffs/d83/key-census-{before,after}.json  ->  IDENTICAL
```

**230 payloads, zero moves.** The `mismatch` count is the known instrument caveat, not a result of
this change: it is identical on both sides and is the same reproduction gap
`scripts/check_key_provenance.py` exists to gate (capx D85 §3.5 / D85-R — payloads predating a key
change, and the D79 solve-surface re-key of ERCOT/CAISO). The diff is what this lane claims, and it
differences the same construction on both sides.

**The mechanism-level reason it is zero:** `cache_key()` hashes the config payload plus the capx D79
`__solve_surface__` fingerprint over `solve_surface.SURFACE_MODULES` — seven `config`/value modules.
`runner.py` is not one of them and is not imported by `scenarios.py`, so the repair is outside the
key's input set. The census is the measurement of that argument, not a substitute for it.

**Independent runtime confirmation.** Re-running the identical window on the repaired tree served
2021 straight from the pre-repair bundle at the same key —
`year 2021 phase timing: data_prep=15.3s cached=True total=15.3s`, `cache_key=5600d19386a1aba9` — so
the repaired code found and reused a bundle written by the unrepaired code. No LP was re-solved.

### 4.2 No solved year changes

The window's `evolution_2021.json` is **byte-identical** before and after the repair
(`json.dumps(..., sort_keys=True)` equal). The solved-year writer was not edited.

### 4.3 No committed bundle is rewritten

None of the 26 defective committed ledgers is touched. Only runs solved after this lands carry the
restored block — D85-R repair 2's rule, binding here identically. The 26 are listed by ISO in §0 so
a later reader knows which bundles read `absent` for "not recorded" rather than "not measured".

### 4.4 What the repair actually produced

Re-running the window on the repaired tree, `evolution_2022.json` gains exactly:

```
+ adequacy_requirement_mw    = None            + solar_cap_mw             = 4549.8
+ capacity_reserve_position  = 1.134718        + storage_firm_mw          = 3801.526
+ firm_clean_accredited_mw   = 1248.756        + storage_power_mw         = 5357.6
+ renewable_credit_applied   = {solar: 0.1064, wind: 0.41}
+ wind_cap_mw                = 10153.9
~ firm_clean_mw              : None -> 3286.2
```

Nothing removed. Against an **evolved solved year** (the D78 bundle's 2023) the repaired bridge
ledger's key set is now complete: **zero solved-only keys, zero bridge-only keys**, once the
config-gated `entry_screen_diagnostics` is set aside.

### 4.5 Reader audit

The four readers that branch on a bridge year — `check_forecast_invariants.py:694`,
`run_capacity_hindcast.py:2569–2570`, `validate_capacity_prices.py:803`,
`build_forecast_dof_ledger.py:165` — all key on the `bridge` flag itself, which is unchanged. Two
readers filter on key *presence* (`run_driver_battery.py:976`, `run_full_horizon.py:697`); the latter
is forecast-mode and has no bridge years at all, and the former takes the last row carrying the key,
which a bridge year can only become if a window **ends** on one — in which case the bridge year's
post-evolution fleet state is the correct final state, so including it is right rather than wrong.
Named here rather than left to be discovered.

---

## 5. The recurrence guard

`tests/unit/results/test_bridge_ledger_field_parity.py` — four source-level (AST) assertions that
the two ledger writers supply one field list, in the idiom
`tests/unit/pipeline/test_p1_prep_wiring.py` already establishes for exactly this failure mode (a
missing name in an expression, with no error and no log line).

It fails **in both directions**: a field added to the solved writer and not the bridge writer is as
loud as one removed from the bridge writer. It also asserts the scan found *both* writers, so a
rename cannot turn it into a vacuous pass on an empty set.

Verified against the defect it exists to catch:

```
pre-repair tree  : 3 failed, 1 passed
post-repair tree : 4 passed
```

Wider suites: `tests/unit/results/` + `tests/unit/config/test_solve_surface.py` → **314 passed,
1 xfailed**; `tests/unit/config/` + `test_p1_prep_wiring.py` → **845 passed, 25 skipped**.
`scripts/check_mechanism_matrix.py --base origin/main` → **exit 0** (its warnings are anchor drift
the tool itself labels "pre-existing, not this PR"). No `ScenarioConfig` field is added and no
calibration CLI flag changes, so rules 24/29 raise no matrix duty.

---

## 6. G-DRIFT — with the charter's correction applied

**The charter is right that `git diff <keeper git_sha> HEAD` is dead here.** Confirmed:
`git cat-file -t 457ae04` → `fatal: Not a valid object name`. The 2026-08-16 history rewrite removed
it, as it did every pre-rewrite keeper sha.

Anchored instead on a commit that **does** resolve — `99245361`, the `git.sha` recorded by the
committed PJM bundle whose `evolution_2022.json` raised the object:

- `git diff 99245361 HEAD -- src/market_sim/runner.py` → 8 hunks, +120/−14.
- **`is_bridge` appears 0 times in that diff.**
- The bridge block is **byte-identical**: `md5 3ee6a4df81d06632db117c7f73932045` at both revisions.

So the writer that produced the committed defective ledger is the same writer HEAD runs, and the
at-HEAD reproduction (§1) is a reproduction of the same code, not a coincidence. **Drift on this
lane's object: none.** I did not audit the wider solve-path diff (86 files) hunk by hunk — that
question is not this lane's and I am not asserting either way about it.

---

## 7. Routed, not absorbed — one item that needs an owner, and it is not mine to touch

**A bridge year reads year-2022 measured data at HEAD, while three places assert it does not.**

The runner's own bridge comment says *"no year-specific data is read"*, and the harness prints
`BRIDGES [2022] (evolved across, LP never solved, measured data never read — rule 22)`. Both are now
false, in two ways, and my reproduction shows it:

1. **capx D76.** `capacity_screen_peak_measured_hindcast` is `True` in the reproduction's own
   `run_config.json` (dataclass default since 2026-09-07, owner ruling **Q58**). Its predicate at
   `runner.py:2109–2118` is `config.hindcast and not config.is_crossover_forward_year(year)` — it
   carries **no `is_bridge` term**, and it sits above the bridge branch. The bridge year's seam peak
   in my HEAD run is **148528.0 MW**; the pre-D76 D78 bundle recorded **135090.596 MW** for the same
   year. The screens' `peak_demand` moved ~13.4 GW.
2. **The hydro budget.** The reproduction logs `Loaded PJM 2022 hydro budget: 74 plants, …` inside
   the bridge year — reached through the screen's own `accredited_firm_capacity_mw` call. This one
   predates D76.

**Why I am not touching it.** D76 is an armed, owner-ruled mechanism (Q58) and this charter
authorizes no mechanism change, no arm and no default change. It is also not obviously a rule-22
breach: rule 22 gates the **spend** — solving, scoring or registering — and a bridge year is none of
those. What is certain is narrower and still worth the owner's attention: **the invariant the code
and the harness banner both state is no longer true**, the operand it changes is decision-bearing
(the seam peak feeds the reliability floor, the entry screen and the backstop), and D76's own
arming record reasons about hindcast *solve* years without addressing bridged ones.

Two candidate resolutions, neither taken here: add `not is_bridge` to the D76 predicate (a mechanism
change, owner's call), or correct the comment and the banner to state what a bridge year does read
(a record change). **Routed, deliberately unabsorbed.**

*(Two further observations, recorded without action: `capacity_reserve_position` and
`screen_reserve_position` are equal in every year of every bundle checked, so one of them is
redundant — but both are established published fields and deduplicating them is not a recording
repair. And 2026, the other `HINDCAST_BRIDGE_YEARS` member, is a bridge year only in hindcast mode;
in forecast mode it is solved and its ledgers were never defective, which is why 46 of the 72
committed 2022/2026 ledgers are clean.)*

---

## 8. What is on local disk, and the promotion question

Per rule 31 `[R-RETAIN]`, nothing is deleted. `results/hindcast/pjm-d83-repro/` was **gitignored the
moment it was written** (before any solve), which is what discharges rule 29 `[R-SCREEN]` (c) — it
cannot reach `main` and cannot turn the parity gate red.

**The bundle is on local disk in an ephemeral container and will not survive this session.** It cost
one PJM 2021 LP (~5 min P0 + P1) plus two bridge evolutions. It is a **diagnostic reproduction, not
a keeper and not a registerable run** — a 2021+2022 window, not the rule-16 full span — so I am not
proposing it for promotion and there is nothing to register. If you want the pre/post ledger pair
kept as evidence beyond the numbers already transcribed into §4.4, say so and I will commit the two
JSON files (~40 KB) rather than only the census; otherwise the doc is the record, as rules 15/29
provide.

**Nothing else in this lane is awaiting a decision.** The repair, the census, the probe and the test
are committed and pushed.

---

## 9. Files

| file | what |
|---|---|
| `src/market_sim/runner.py` | the repair — `if is_bridge:` writer only |
| `tests/unit/results/test_bridge_ledger_field_parity.py` | the recurrence guard |
| `scripts/probes/capxd83_bridge_ledger_key_census.py` | the key census instrument |
| `docs/handoffs/d83/key-census-{before,after}.json` | its two byte-identical outputs |
| `.gitignore` | `results/hindcast/pjm-d83-*/` (rule 31) |

Boundary respected: `tests/unit/model/test_d62_published_going_forward_bar.py`,
`test_d74_no_default_cap_convention.py` and the D62/D74 mechanism code are **untouched** — the
diagnosis never reached them.
