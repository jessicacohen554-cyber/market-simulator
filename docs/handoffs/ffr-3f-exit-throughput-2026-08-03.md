# FFR-3F — The G-31 exit-throughput fix lane: cap grain first, then the measured throughput term

**Session.** FFR Wave 3, the G-31 fix lane, chartered by **owner decision D-8**
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum F.1, signed 2026-08-03) to
FFR-3C §6's specification. Branch `claude/g31-exit-throughput-fix-gsy4md`, off `origin/main`
**`edf5c5a`** (the packet's stated HEAD `01b6a6a` was already stale at session start; `98ad9c1`
at first fetch, `edf5c5a` by the time the first commit was pushed).

**Nothing is promoted and no default is flipped.** Both are owner boxes. `exit_rate_limits`
ships **default-OFF**; D-1 and D-2 stay armed exactly as Addendum D left them; no band was
widened and no threshold moved.

---

## 0. Headline

1. **The G3 cap-grain defect is fixed and landed** (commit `2adfb49`). The pipeline's admission
   cap now resolves its adequacy requirement at the schedule's **execution horizon** rather than
   the decision year. No new parameter. Verified to change the admitted exit set in a
   discriminating unit test (the old grain admits 1 unit where the corrected grain retains 2).
2. **The exit-throughput term is built, measured, registered and default-off** (commit
   `db5ff91`). Identification is external — the EIA-860 retired sheet — and reproduces the
   values D-8 cites for the two test ISOs exactly (ERCOT 4.42 GW/yr, PJM 5.24). The synthetic
   demonstration is decisive: FFR-3C's 12-unit cohort exits in **one** year uncapped and over
   **three** capped, with the **total identical** — the cap moves the calendar and does not
   touch the level.
3. **Measurement and the FH-1 §3.3 re-probe: see §5 and §6.**

---

## 1. Task 1 — the G3 cap-grain fix

### 1.1 What was wrong

FFR-3C §1.2 G3: the R-NEW pipeline's admission cap screens **one counterfactual fleet** — the
current fleet with the whole scheduled exit set removed at once — but resolved the adequacy
requirement that fleet is tested against at the **decision** year, while the exits it admits
execute at `decided_year + L_f`, one to three years later. In FFR-3C's synthetic the cap tested
a 2026 requirement of 21,990 MW against exits landing on 2028's 24,244 MW: **+10.3 % of
requirement the cap never saw.**

### 1.2 The fix

`_admission_cap_horizon` (`src/market_sim/model/capacity_evolution/retirements.py`) returns the
year at which the counterfactual fleet actually exists — `max(decided_year + L_f)` over the
scheduled set — and the peak projected to it. **Both** year-dependent inputs to
`resolve_adequacy_requirement_mw` move there, because both matter:

* the **year**, which selects the ISO's published-FPR delivery year; and
* the **peak** the requirement is a fraction of, compounded on the run's own demand-growth path
  (`resolve_demand_growth_rate` — the identical per-year rate `runner._scale_demand` uses).

No new `ScenarioConfig` field and no identification work: the horizon is a function of the
already-identified per-fuel execution lags and the growth path already driving demand, so it
regenerates for any forward year and responds to changed conditions (rule 13 `[R-MEASURED]`).

**Inert where the grain was already right**, byte-identically: a lag-1 fuel executes in the
screen year itself, and an empty schedule has nothing to project — both return
`(year, peak_demand)` unchanged. The realized-year execution floor is untouched; it was always
evaluated at the year its exits land.

### 1.3 Verification

| check | result |
|---|---|
| Horizon reproduces FFR-3C's synthetic | coal cohort decided at the 2031 screen (loss year 2030) + `L_coal` 3 → cap tested at **2033**, peak × 1.025² — the same 2-year offset G3 measured |
| Discriminating behavioural test | ERCOT, peak 3,095.5 MW: decision-year requirement 3,316.91 MW ⇒ **1** unit retained; execution-year requirement 3,484.82 MW ⇒ **2**. Reverting the call to the decision-year grain **fails the test (1 != 2)**, verified by patching it out and re-running |
| Inert cases | lag-1 fuel and empty schedule both `(year, peak_demand)` |
| Existing pipeline suite | 209 pre-existing tests still pass; the one existing test that exercises the admission cap is grain-invariant by construction (retaining gas_st alone clears both requirements) and its stale arithmetic comment was corrected rather than left to mislead |

### 1.4 What the fix does NOT do

The **fleet** side of the cap stays at the decision year — entry commissioning between decision
and execution is not credited. That is the cap's pre-existing grain, out of this correction's
scope, and it biases the cap conservative (toward retaining). Recorded as open, not silently
closed.

---

## 2. Task 2 — the exit-throughput term

### 2.1 The rule-19 seam, stated explicitly

D-8 ruled queue **latency** and queue **throughput** two mechanisms. The seam:

| | owns | operator |
|---|---|---|
| `retirement_execution_lag_*` (latency, **unchanged**) | **WHEN** a decided unit becomes eligible to leave | rigid per-fuel time shift, `decided_year + L_f` |
| `exit_rate_limits` (throughput, **new**) | **HOW MANY MW** may actually leave in one year | FIFO budget over the year's due set |

They cannot double-count because they act on **different quantities in sequence**: the lag sets
*membership* of the year's DUE set; the cap sets *how much of that due set is processed*. A unit
the cap defers **stays pipelined** and re-presents at the head of next year's queue through the
identical "execution deferred, re-latched next year" path the reliability floor already uses
(pipeline component 5) — so no second deferral mechanism is introduced either.

`staged_oversupply_thinning` stays **deleted** (rule 26 `[R-DELETE]`). This is a new, externally
identified, default-off gate, not a revival of the fitted knob.

### 2.2 Identification — every value cited to EIA-860

Reader: `src/market_sim/data/build_exit_throughput.py` (`max_annual_exit_gw`), the mirror of
`build_throughput.py` — same fuel classes, same `_map_fuel_type` crosswalk, same BA→ISO map, so
the two halves of one queue are measured on one basis. Source: EIA-860
`eia860_generator_retired_and_canceled`, `Status == "RE"` (excluding `CN` cancelled and `IP`
indefinitely-postponed, neither of which is a deactivation).

**Measured maximum single-year thermal deactivation, 11-year window:**

| ISO | seed through 2023 (GW) | max year | seed through 2025 (GW) | cap at 2.0× through 2023 (MW/yr) | D-8's cited value |
|---|--:|--:|--:|--:|--:|
| **MISO** | 7.46 | 2016 | 7.46 | 14,920 | 7.57 |
| **PJM** | **5.24** | 2015 | 5.24 | **10,485** | **5.24** ✓ |
| **ERCOT** | **4.42** | 2018 | 4.42 | **8,840** | **4.42** ✓ |
| CAISO | 2.39 | — | 1.48 | 4,774 | 1.48 |
| NEISO | 0.98 | — | 0.45 | 1,950 | 0.45 |
| NYISO | 0.31 | 2021 | 0.31 | 625 | 0.31 |

**Both test ISOs reproduce D-8's cited identification exactly.** MISO differs by 1.5 %
(7.46 vs 7.57) and CAISO/NEISO differ on the pre-2015 window — FFR-3C's reader was session
scratch and is not committed, so its exact construction cannot be diffed. The shipped
construction is the defensible one because it is the entry side's, verbatim; the deltas are
recorded rather than reconciled to an unavailable script, and **neither affects a tested ISO**.

**The windowing choice carries no DOF for the tested ISOs — measured, not assumed.** ERCOT, PJM
and MISO return the identical maximum under the 11-year window, the entry side's 10-year window,
and the **unwindowed** full EIA-860 retired record back to 1978, at both the 2023 and 2025
vintages. Only CAISO/NEISO/NYISO are window-sensitive, and none is a test ISO here.

**The 2.0 multiplier is not a chosen number.** It is the entry side's own
`ENTRY_GROWTH_LIMIT_MULTIPLE` (the ReEDS growth-constraint hard bound, "not allowed to exceed
200 % of the prior maximum"), transferred unchanged. FFR-3C §1.4's finding *is* the asymmetry —
exit uncapped while entry is capped at 2× its measured record — so holding one queue to **one**
envelope is the structurally faithful repair (rule 1 `[R-STRUCT]`), and it leaves no exit-side
multiplier to fit. There is no residual channel into any of this (rule 23
`[R-FROZEN-DERIVE]`): nothing in the reader can see a model result, a price, or a score.

### 2.3 The window, the driver, the forward story (rule 17 `[R-FLOOR-WINDOW]` analogue)

* **Driver.** RTO/ISO deactivation-queue processing capacity — deactivation studies, RMR
  determinations, decommissioning logistics — externally identified by the largest single-year
  deactivation each ISO has actually achieved.
* **When it may bind.** Only in a year whose decided-and-due exit volume exceeds **2× the ISO's
  historical single-year record**. Over the historical window it is inert by construction: the
  seed *is* that record.
* **Forward regeneration.** Re-derives from the EIA-860 retired sheet at the run's vintage; a
  future edition recording a larger deactivation year raises the cap automatically. An ISO with
  no measured deactivation carries **no cap** (rule 25 `[R-ISO-SCOPE]` neutral fallback — a
  missing measurement must never invent a zero that forbids exit).

### 2.4 A vintage-directory defect found and closed

The first armed leg ran **inert** and said so loudly: the committed `vintage_2023/` directory is
a **reduced 10-sheet set** and does not contain the retired sheet at all, so the seed resolved to
`None` and no cap was applied. The reader now falls back to the canonical release **with a
WARNING**, which is as-of-safe *here and only here* because the window bound is on **retirement
year**, not publication vintage: `through_year` already excludes every deactivation after the
cutoff, so the canonical sheet contributes no post-vintage event.

The residual exposure is reporting **completeness** at the boundary year, and it is measured to
be immaterial for every ISO this cap is armed on — the binding maximum predates the 2023 boundary
by 5–8 years in every case (ERCOT 2018, PJM 2015, MISO 2016), so no boundary-year revision can
move the seed:

| ISO | annual thermal deactivation (GW), 2013→2023 | max |
|---|---|--:|
| ERCOT | 1.44 · 0.63 · 0.15 · 0.67 · 0.98 · **4.42** · 0.38 · 0.32 · 0.03 · 0.41 · 1.01 | 2018 |
| PJM | 1.01 · 2.40 · **5.24** · 0.32 · 0.48 · 1.32 · 1.95 · 1.92 · 1.07 · 2.95 · 5.05 | 2015 |
| MISO | 2.74 · 0.29 · 2.31 · **7.46** · 1.52 · 5.44 · 3.54 · 2.15 · 3.67 · 3.08 · 3.63 | 2016 |

The runner's log line for an unresolved seed was also corrected: it said "no measured thermal
deactivation" when the real cause was a missing sheet, and now names both possibilities and
states plainly that **the arm is inert this run**.

### 2.5 Mechanics

Strict **FIFO by decided year** — a deactivation queue is processed oldest-request-first. The
year stops at the first request that does not fit, and remaining headroom is **not** backfilled
with a smaller later unit: reordering by size is not something a real queue does, and it would
make exit composition depend on unit size rather than request date. The head of the queue is
**always** admitted even when it alone exceeds the cap, otherwise the cap would silently become
an immortality rule for large units rather than a rate limit.

Deferrals are recorded as their own ledger event kind (`throughput_deferred`), never folded into
`floor_retained`, so D-2 mechanism attribution stays readable.

### 2.6 Registration (rules 5 / 24 / 28)

| duty | done |
|---|---|
| `ScenarioConfig.exit_rate_limits`, default-off | ✓ |
| Cache-key registered; default key **`973a0acdef818e91` verified UNMOVED** before/after | ✓ |
| `docs/parameter-citations.md` + `frontend/data/parameters.json` cited entry (not `needs-citation`) | ✓ |
| Constants in their own per-domain module `config/retirement_config.py` with citations | ✓ |
| CLI arm `--exit-rate-limits` / `--no-exit-rate-limits`, recorded in `meta` **from the config object the solve ran on** | ✓ |
| Rule-28 matrix row in the **same PR** (duty c) | ✓ |
| No env knob, no per-ISO hardcoded dict, no `getattr` fallback literal | ✓ |

The stale rule-19 comment in `scenarios.py` that asserted the argument D-8 overturned was
amended in place rather than left to mislead the next reader.

---

## 3. Synthetic demonstration — the property that was missing

FFR-3C §1.2 G2: *"with only the latency term, exit-wave width is invariant at exactly one year
no matter how many units fail."* Driving the shipped screen over a 12 × 500 MW all-failing coal
cohort (6 GW, `L_coal` = 3), floor inert:

| year | uncapped (shipped) | capped at 2 GW/yr |
|---|--:|--:|
| 2028 | **12 units = 6.0 GW** | 4 units = 2.0 GW (8 deferred) |
| 2029 | — | 4 units = 2.0 GW (4 deferred) |
| 2030 | — | 4 units = 2.0 GW |
| **wave width** | **1 yr** | **3 yr** |
| **total exited** | **6.0 GW** | **6.0 GW** |

The total is identical. That invariant is the point: a throughput cap adjudicates the
**calendar**, never the **level** — the level remains the revenue lane's (BLK-6/BLK-9), exactly
as FFR-3C §1.4 scoped it.

---

## 4. Prerequisites and blockers found

1. **The container had NO project dependencies at all** — not merely `data/clean`. `python -c
   "import pandas"` failed; `regenerate_clean.py` reported **50/50 datatypes failed** with
   `ModuleNotFoundError: No module named 'pandas'` within seconds. `pip install -r
   requirements.txt --ignore-installed PyYAML` (the debian-owned PyYAML blocks a plain install)
   plus `pip install highspy==1.14.0` (the resolver silently takes 1.15.1 otherwise, and the
   HiGHS version moves LP results) is the recipe. **This belongs with FFR-3A blocker 1 and is
   strictly larger than it.**
2. **`tzdata` is still not in `pyproject.toml`** even though `requirements.txt`'s own comment
   claims *"pyproject pins it unconditionally"*. It does not. `pip install tzdata` is still
   required by hand (FFR-3C blocker 9). Not fixed here — out of lane — but the drift is between
   two committed files and is a one-line repair for whoever owns the dependency manifest.
3. **`data/clean` regeneration: 49/50 clean.** `egrid` exits `-6` (`terminate called without an
   active exception`) — but **after** writing all seven year files, so the partition is
   complete and the abort is an interpreter-teardown crash, not a data failure. Total ≈ 65 min,
   1.6 GB, 54 datatype directories.
4. **A broad pre-existing cache-key pin drift at HEAD.** `ScenarioConfig().cache_key()` is
   `973a0acdef818e91` while `PINNED_DEFAULT_CACHE_KEY` is `603c2498bf71d21d`. The test's own
   message says *"Do not update the literal to silence this — find what changed."* Not mine (my
   change leaves the key untouched, verified both directions) and not fixed here, but it means
   **every on-disk cache is already orphaned relative to the pins at this HEAD**, which any
   keeper-reproducibility claim needs to account for.
5. **Pre-existing test failures, itemized** (FFR-3C blocker 6, now enumerated). All verified to
   fail identically at `origin/main` with my branch stashed; **my changes introduce none**:
   `test_persisted_identity` (×3), `test_fh2_as_of_channels` cache-key neutrality,
   `test_fleet_arrays_golden`, `test_cc_committed_offer_margin` + `test_ramp_envelope_basis`
   byte-stable keys, `test_outages::test_unknown_iso_degrades_to_empty`,
   `test_ercot_thermal_as_endogenous::TestScreenMutualExclusion` (×2). Separately,
   `test_integration::test_full_year` fails **only under `-n 4`** and passes serially — it is a
   wall-clock performance assertion, not a correctness failure.
6. **413 on first push, both documented causes present.** A stale tracking ref
   (`origin/claude/g31-exit-throughput-fix-gsy4md`, pruned) *and* a stale `origin/main`. `git
   remote prune origin` + `git fetch origin main` + rebase reduced the push to 11 objects and it
   went through. No PR had ever existed for the branch (`search_pull_requests` → 0), so no
   merged-branch restart was needed.

---
