# FH-2 — As-of driver plumbing: demand growth, capacity prices, policy

**Session:** FH-2 `[OPUS]`, Wave FH (`docs/hindcast-forward-plan-2026-07.md` §6).
**Base:** `origin/main` @ `9950a5c` (2026-08-02). Branch
`claude/fh-2-vintage-addressable-ox2bsl`.
**Scope shipped:** the demand-growth as-of vintage mechanism + resolver + tests
(plan §4 row 6, the second BLOCKER); the `_scale_demand` backward-span repair;
the capacity-price `year`-threading audit with a regression suite on the
committed PJM anchors (row 13); and the two smallest-first policy as-of rows
(row 14) with an explicit disclose list for what stays open.

**No solve. No default moved. No driver VALUES landed** — the demand-growth
vintage registry ships empty and is FH-3's to fill. Nothing here was tuned
against a residual (rules 1/5/11/13/21/23). `adequacy.py` / `evolve.py`
untouched (FFR ownership); no GitHub Actions workflow added.

---

## 0. Headline

| Task | Verdict |
|---|---|
| 1. Demand-growth vintage | **SHIPPED** — `DEMAND_GROWTH_RATES_VINTAGES` + `ScenarioConfig.demand_growth_vintage`, resolver, cache-key + matrix rows, 12 tests. Registry EMPTY (FH-3 lands values); every vintage request raises today, by design. |
| 2. `_scale_demand` backward no-op | **FIXED** — silent 1.0 replaced by a hard error in the T1-FF lane and correct de-growth everywhere else. 5 tests. |
| 3. Capacity prices | **AUDIT: the plan's premise is STALE — all three screens already thread `year`.** Verified end-to-end on the committed PJM 2021/22–2025/26 anchors and pinned by 6 new tests so it cannot silently regress. One un-threaded consumer found (`plant_financials`, a report) — disclosed, not threaded. |
| 4. Policy | **PARTIAL, as chartered** — RGGI 2021 membership and CAISO's statutory historic RPS knots landed; four ISOs' RPS, the carbon anchor and RGGI-2022 stay disclosed with reasons (§5.3). |

Byte-identity: `cache_key(ScenarioConfig())` is **`603c2498bf71d21d`** before and
after every edit in this session, and the four other attestation configs are
likewise unmoved (§6).

---

## 1. What "as-of addressable" means here

Every channel below has the same shape of defect: a forward driver resolves for
a historic year, but resolves to a value that could only have been known
*later*. That is not a forecast miss — it is an information leak that makes the
resulting "skill" number meaningless. FH-2 does not fix the values; it makes the
channel **addressable at a base year** so FH-3 can land the values and FH-4 can
select them, and it makes every unaddressable path **loud** instead of silent.

Three of the four channels were, at HEAD, silent in a specific way worth naming:

* demand growth resolved a **2025/2026-edition** rate for a 2021 target,
* `_scale_demand` resolved a **factor of exactly 1.0** for a backward span,
* the CAISO RPS resolved the **2026** target for every year before 2026.

None raised, none logged. All three now either resolve correctly or refuse.

---

## 2. Demand growth (plan §4 row 6 — the second BLOCKER)

### 2.1 The defect

`DEMAND_GROWTH_RATES` (`constants.py`) is a two-era per-ISO table
**re-derived in FF-1C from the 2025/2026 LTLF / Gold Book / CELT / IEPR
editions**, and `DEMAND_GROWTH_TRANSITION_YEAR = 2030` puts every historic year
in the `near` era — the era that carries the data-center boom. ERCOT `mid` near
is **8.5 %/yr**. Applied 2021 → 2023 that is **+17.7 %** against roughly +2 %
actual. There were no vintage variants, so a T1-FF Arm K run launched from a
2021 or 2023 base had no way to ask for the rates its base year actually knew.

### 2.2 The mechanism

One growth mechanism, two addresses (rule 19 `[R-ONE-MECH]`) — deliberately not
a second input stack:

* **`constants.DEMAND_GROWTH_RATES_VINTAGES`**, keyed
  `{as_of_year: {iso: {low|mid|high: {near, long}}}}` — the *same inner shape* as
  `DEMAND_GROWTH_RATES`, so one resolver serves both and the PB-1 path/percentile
  levers keep working unchanged on a vintage table (tested).
* **`ScenarioConfig.demand_growth_vintage: int | None = None`** — registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` (cache-neutral at `None`) and `TIER_TAGS` (tier 1),
  and carried into `run_config.json` by `asdict` like every other field
  (rule 24 `[R-REGISTRY]`).
* **`config.scenario_resolvers.resolve_demand_growth_table(config)`** — the single
  seam that owns the table choice; `resolve_demand_growth_rate` now reads through
  it, and `config.scenarios` re-exports it (facade contract).

### 2.3 Fail-closed, in three places

An unknown vintage **RAISES**, and never falls back to the current table — a
silent fallback IS the leak. Enforced at:

1. **config build** (`__post_init__` calls the resolver), so a bad vintage aborts
   before a multi-hour run burns — the FH-1 pre-solve-guard precedent;
2. **the resolver itself**, so a config mutated after build cannot slip through;
3. **per-ISO**: a vintage that exists but carries no row for the run's ISO also
   raises, rather than borrowing today's rate for that one ISO.

Plus: a vintage set in **backcast mode raises** — a backcast pins measured load
and never growth-scales it, so a vintage there would be an inert no-op.

The registry **ships EMPTY**, so *every* vintage request raises today. That is
the intended FH-2 state: the mechanism is proven by tests against an injected
table, and FH-3 lands the cited per-ISO edition values (ERCOT LTLF, PJM LTLF,
NYISO Gold Book, ISO-NE CELT, MISO LTLF, CEC IEPR). Arm K at any base is
therefore still on today's rates until FH-3 lands — unchanged from the FH-1
handoff's §9 statement, and now with the instrument in place to change it.

Arm R is unaffected either way: its growth spans are zero-year by construction
(`crossover_solve_year_weather` re-seeds each solve year from itself), so the
growth table never binds there. This is the demand half of **Arm K's** posture.

---

## 3. `_scale_demand`'s backward span (plan §4 row 6, compounding defect)

`runner._scale_demand` compounded over `range(config.weather_year, year)`. For
`year < weather_year` that range is **empty**, so the function returned
`base_demand * 1.0`: a 2025 load level presented as 2021's, with no de-growth
and no error. FH-1 correctly noted it is unreachable in the two shipped arms
(Arm R spans zero years; Arm K pins the base at/below every solve year) — but it
is live for any future posture, and it is exactly the silent-defect class
FR-7/FR-8 belong to.

Two explicit behaviours replace the silence, each in the domain where it is
right:

* **Full-forward hindcast → hard error.** Both arms pin the weather base at or
  below every solve year, so a backward span there is a posture
  misconfiguration; and de-growing a *later* measured weather year into an
  "as-of" forecast would import post-base information (rule 13 `[R-MEASURED]`).
  Raised with the fix named in the message.
* **Everywhere else → correct de-growth**, the exact inverse of the forward
  compounding over the same span (each year's own rate), and a `logger.warning`
  so it is never silent. Tested: forward-then-backward composes to identity.

Forward spans and the `year == weather_year` identity are byte-identical.

---

## 4. Capacity prices (plan §4 row 13) — audit result

**The plan's premise is stale.** Row 13 says "today `year` reaches the seam only
from storage entry (`model/storage.py:1092`); the thermal retirement and entry
call sites need auditing." At HEAD **all three screens already thread it** — the
RC-1A/RC-1B wiring landed after the plan text was written:

| Screen | Seam call | `year` source | Status |
|---|---|---|---|
| Thermal retirement | `retirements.py:1736` → `capacity_revenue_per_mw_yr(..., year)` → `capacity_price_per_firm_mw_yr(iso=, year=)` | `apply_economic_retirements(year=…)`, passed by `evolve.py:497` | **threaded** |
| Thermal entry | `new_entry.py:902` (thermal) and `:1012` (VRE) | `apply_economic_new_entry(fleet, prices, year, …)`, positional from `evolve.py:601` | **threaded** |
| Storage entry | `storage.py:1092` → `estimate_capacity_value(..., year=year)` | `storage.py:1319` in the entry screen | **threaded** |

So nothing needed threading. What was missing is a **guard**: only the retirement
and storage seams had year-threading tests, and nothing pinned the thermal-entry
screen or the historic anchors. `tests/unit/config/test_fh2_as_of_channels.py::TestCapacityPriceYearThreading`
now pins all three, plus gate-off year-invariance and ERCOT's energy-only zero.

**Verification on the committed PJM anchors** (gate armed, reserve position 1.0,
i.e. at the requirement; anchors recomputed in the test from the published
$/MW-day figures rather than read off the constant they check):

| Model year | Vintage | Anchor $/kW-yr | Payment @ rp=1.0 ($/MW-yr) |
|---|---|---|---|
| 2021 | 2021/2022 | 117.37 | 170,382 |
| 2022 | 2022/2023 | 95.08 | 115,020 |
| 2023 | 2023/2024 | 100.36 | 121,404 |
| 2024 | 2024/2025 | 107.01 | 129,453 |
| 2025 | 2025/2026 | 83.52 | 123,200 |
| 2026 | 2026/2027 | 77.43 | 103,062 |
| 2027+ | 2027/2028 | 88.52 | 108,431 (hold-last) |

`year=None` prices the registry default (103,062) at every year — which is what
every gate-off path and every legacy caller still gets, byte-identically.

**No default flipped**: the CR-1 clearing gate (`capacity_market_clearing` /
`capacity_market_clearing_by_iso`) stays owner-armed, so in a shipped run the
whole vintage branch is inert and the flat net-CONE governs.

**One un-threaded consumer, disclosed not fixed:**
`results/plant_financials.py:537` prices its reported capacity revenue with
`iso=` but no `year=`, so a hindcast financial report values historic capacity
at the 2026/27 registry curve. It is a *reporting* path — it never enters the LP
or a screen — and threading it would change committed report output for no
decision effect, so it is listed here rather than changed in a plumbing PR.

---

## 5. Policy (plan §4 row 14) — smallest-first

### 5.1 RGGI membership: 2021 landed

`RGGI_MEMBER_STATES_BY_YEAR` covered 2023–2025 only. 2021 is the hindcast **seed
solve year** (`holdout_policy.HINDCAST_SEED_YEARS`), so the model genuinely
solves it — and `per_generator_membership` falls back to
`max(RGGI_MEMBER_STATES_BY_YEAR)` for an absent year, i.e. the **2025,
post-Virginia-exit** set. A 2021 solve therefore un-enrolled every Virginia plant
in the very year Virginia joined (9 VAC 5-140, effective 2021-01-01).

Landed as a published legal fact carrying no measured quantity. Byte-neutral for
2023–2025 (a new key only), and inert on the mass-cap path: no 2021 per-state
budget exists, so `_published_power_sector_budget(2021)` still returns `None` and
the row stays unbuilt (the mass-cap gate is default-off regardless).

### 5.2 CAISO RPS: statutory historic knots landed

`STATE_RPS_FLOORS` knots started at **2026**, and `get_rps_target` edge-holds
below the first knot — so every pre-2026 year in a forward-lane run received the
2026 target. All three hindcast harness modes (T1-H / T1-X / T1-FF) are
`mode="forecast"` with `rps_enabled=True`, so a 2021 solve was compelled to a
**50 % clean share five years before the law required it**.

Landed for CAISO, from the statute itself (rule 5 `[R-NO-MAGIC]`):

| Knot | Value | Source |
|---|---|---|
| 2021 | 0.33 | SB X1-2 (2011), Pub. Util. Code §399.15(b)(2)(B) — 33 % by 31 Dec 2020, the standing requirement through compliance period 4 (2021–2024) |
| 2024 | 0.44 | SB 100 (2018), same section — 44 % by 31 Dec 2024 |

Resulting targets: 2021 0.330 → 2022 0.367 → 2023 0.403 → 2024 0.440 → 2025
0.470 → **2026 0.500 (unchanged)**. Every knot at/after 2026 is untouched, so
plain 2026+ forecasts are byte-identical.

**No backcast keeper can be affected by any RPS change**:
`pipeline/backcast_config.py:1253` sets `rps_enabled=False`, so a backcast never
builds an RPS row at all. The blast radius is exactly the forward-lane historic
years — which is the leak being closed.

### 5.3 What stays disclosed, and why

| Channel | As-of status | Why it stays open |
|---|---|---|
| **Demand growth** | **ADDRESSABLE** (mechanism); values pending | FH-3 lands the per-ISO published editions. Until then any vintage request raises — no silent leak. |
| **Capacity prices — 3 screens** | **AS-OF CORRECT** | Vintage-complete registry + `year` threaded; pinned by tests. Binds only with the owner-armed CR-1 gate. |
| **Capacity prices — plant financial report** | **DISCLOSED** | `plant_financials.py:537` passes no `year`; reporting-only, no decision effect (§4). |
| **RGGI membership 2021** | **AS-OF CORRECT** | Landed (§5.1). |
| **RGGI membership 2022** | **DISCLOSED — refused deliberately** | 2022 is the evolved-never-solved bridge year whose contract is that its data is never read (FH-1 §6); this file's own convention omits 2022/H1-2026 rows under rule 22, whose intake clause requires per-window owner authorization this session does not hold. *This is a scoped deviation from the FH-2 prompt, which asked for 2021 **and** 2022 — flagged rather than taken silently. If the owner authorizes it, the row is one line and the membership set is identical to 2021's.* |
| **RPS — CAISO** | **AS-OF CORRECT** | Landed (§5.2). |
| **RPS — PJM, MISO, NYISO, NEISO** | **DISCLOSED** | Their 2026 knots are not published scalars but this repo's own load-weighted blends of per-state renewable-tier schedules (see the PJM/MISO blocks in `capacity_market.py`). A historic knot means re-blending each state's **then-current** schedule on that year's load weights — a cited derivation of the same kind FH-3 does for demand growth, never an interpolation of the 2026 blend. Landing an invented value here would be exactly the rule-13 violation this program exists to remove. Bounded intake, sized for a follow-up session. |
| **Carbon anchor (`projected_price`)** | **DISCLOSED** (as chartered) | `projected_price` returns the *last measured* clearing price for any `year <= last_year`, so a forecast-mode 2021 gets the **2025** allowance price — structurally the same back-hold trap FH-1 hard-errored on for gas. Measured 2021 RGGI/CARB auction averages *do* exist and would be rule-13-admissible as a backcast measured input, but landing them is a data intake for an out-of-training year and needs its own owner authorization (rule 22 channel 1). Not invented, not back-cast. Two candidate fixes for the successor: intake the measured 2021 anchors, or give `projected_price` the same below-first-knot hard error `resolve_annual_gas_price` now carries. |
| **Gas basis differential** | **DISCLOSED** (unchanged, plan row 9) | Year-invariant per-ISO scalar derived from 2023–2025 receipts; applying it to 2021 is an as-of violation in spirit. Out of FH-2 scope. |

---

## 6. Byte-identity attestation

`ScenarioConfig.cache_key()` measured at `9950a5c` **before** any FH-2 edit and
re-measured **after** all of them — all five identical:

| Config | Key (before == after) |
|---|---|
| `ScenarioConfig()` default | `603c2498bf71d21d` |
| ERCOT plain forecast (2026–2030) | `b1bf77e3fcf7f7aa` |
| PJM plain hindcast (2023–2025) | `f635420c2783e5d0` |
| ERCOT T1-X crossover (boundary 2026) | `edef3cdbb85e7b4d` |
| CAISO backcast (weather 2024) | `74e4d97968003b7e` |

The default key `603c2498bf71d21d` is the **pinned literal** that
`tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py::test_default_cache_key_unmoved`
asserts — reported failing at `a92ae97` in the FH-1 handoff, and **passing at
this session's base**: FFR-W1X's Wave-1 close registered the four leaked fields
(`_CACHE_KEY_OPTIONAL_FIELDS` comment at `scenarios.py:53-70`), restoring the
pin. FH-2 keeps it.

Guards: `scripts/check_cache_key_registration.py --base origin/main` →
*"ok: 1 new field(s), all registered: demand_growth_vintage"*;
`scripts/check_mechanism_matrix.py --base origin/main` → integrity OK, keeper
stamps match; `ruff check` + `ruff format --check` clean.

### Test runs

| Suite | Result |
|---|---|
| `tests/unit/config/test_fh2_as_of_channels.py` (new) | **28 passed** |
| `tests/unit/config` + `test_capacity_demand_curve` + `test_entry_stack_ff2a` + `test_scenarios_facade` | 505 passed, 18 subtests |
| `tests/unit/pipeline` + `tests/unit/policy` + `tests/regression` | 653 passed, 5 skipped, 31 subtests, **7 failed** — see below |
| `tests/regression/test_persisted_identity.py` + `test_forecast_xyear_warmstart_flag.py` (the BLOCKING CI pins) | 19 passed |

**The 7 failures are environmental or pre-existing, none caused here:**

* 6 × `tests/regression/test_soundness.py` — `data/clean/confirmed-retirements`
  is derived and gitignored, so a fresh checkout has no partition and
  `confirmed_exits_enabled` refuses to degrade silently (its own error message
  says so). After
  `PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py`, all
  **30 pass** on this branch.
* 1 × `tests/regression/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`
  — `availability` and `min_gen` hashes drift from the committed golden.
  **Reproduced identically on unmodified `origin/main` content** in this same
  environment (checked out `origin/main -- src/market_sim tests docs`, re-ran,
  same two fields, same hashes), so it is a **pre-existing main red**, filed
  here and not this session's to fix. FH-2 touches nothing in the fleet-array
  path.

---

## 7. What FH-3 / FH-4 inherit

* **FH-3**: land per-ISO values into `constants.DEMAND_GROWTH_RATES_VINTAGES`
  under the keys `2021` and `2023`, each ISO row carrying `low`/`mid`/`high` ×
  `near`/`long` and each value cited to its edition + table. A vintage must
  carry **every ISO the run will ask for** — a missing ISO raises rather than
  borrowing today's rate. Nothing else in FH-2's mechanism needs touching;
  `test_registry_ships_empty_at_fh2` will fail on the way in, which is the
  intended handshake (update it to assert the landed vintages).
* **FH-4**: `--arm asknown` should set `demand_growth_vintage = base_year`
  alongside its gas path — that wiring is **not** done here (the harness is
  FH-1/FH-4's file, and there is nothing to select until FH-3 lands). Until it
  is wired *and* FH-3 has landed, Arm K's forward demand still grows on today's
  rates, exactly as FH-1 §9 stated.
* **Successor lanes named above**: the carbon `projected_price` back-hold (§5.3),
  the four-ISO RPS historic blend (§5.3), `plant_financials` year-threading (§4),
  RGGI 2022 pending owner authorization (§5.3).
* **Unaffected by all of it**: FH-4/Phase A remains BLOCKED on FH-1's §3.3 gate
  (the I6 over-retirement reproduced at the T1-FF posture). FH-2 is mechanism
  plumbing and neither lifts nor deepens that block.
