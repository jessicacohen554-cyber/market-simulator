# FH-1 — T1-FF full-forward hindcast mode + the four sub-2026 information leaks

**Session:** FH-1 `[FABLE]`, Wave FH (`docs/hindcast-forward-plan-2026-07.md` §6).
**Base:** `origin/main` @ `a92ae97` (2026-08-02). Branch
`claude/fh-1-full-forward-hindcast-7fqjr3`.
**Scope shipped:** the `--forward-from-base` harness mode (T1-FF, plan §2) with
both pre-registered arms wired; the four §4 leak closures (rows 2/7/11/12); the
generalized run-time forward-driver guard; the rule-22 carve-outs moved into
`scripts/lib/holdout_policy.py` with the harness fail-closed against them and
the freeze file; the scorer's symmetric `< 2023` refusal; 28 contract tests;
the rule-28c matrix row; and the §3.3 harness-defect gate probe (§7 below).

Nothing here tunes anything: no ScenarioConfig default moved, no threshold
moved, no residual was closed by a value (rules 1/5/11/13/21/23).
`adequacy.py` / `evolve.py` untouched (FFR ownership).

---

## 1. The instrument, as built

`ScenarioConfig.is_full_forward_hindcast` — true iff `crossover_forward_year`
is set at/below `start_year` — is the single discriminator every change gates
on. T1-FF is the existing T1-X seam re-pointed (rule 19: one mechanism), not a
second input stack:

- `--forward-from-base` sets `crossover_forward_year = start_year`, so every
  solve year takes the forward branch of the three seam consumers
  (`runner.py` measured-demand skip, `plant_prices.py` F923 skip,
  `trajectories.py` gas re-path) plus the entry-lookahead's measured
  next-year-demand read, which is now seam-gated too (§5).
- Window rules are the PLAIN-hindcast rules, unchanged: 2021 floor,
  `end <= 2025`, `{2021}` seed, 2022 bridged (evolved, never solved, its data
  never read). Vintage must be `<=` the base year (Phase A: 2023/2023,
  Phase B: 2021/vintage 2020 — both accepted by `_validate_window`).
- **Arm R (`--arm realized`)**: `gas_price_path = crossover_forward_gas_path =
  "hindcast_realized"`; `weather_year = base`; new field
  `crossover_solve_year_weather=True` → each solved forward year re-seeds
  `base_demand` + `wind_cf`/`solar_cf` from ITSELF (runner rebind, transient
  `wx_config = replace(config, weather_year=year)` at the three
  `_scale_demand` call sites — the recorded config and cache key never
  mutate). Growth scaling therefore spans zero years: given-weather,
  perfect-foresight-driver posture (plan §2.1, rule-13 admissible).
- **Arm K (`--arm asknown`)**: gas = `hindcast_asknown_aeo<base>`;
  `weather_year = base` for every solve year; the posture field stays off.
  Base 2023 **hard-errors today** — `hindcast_asknown_aeo2023` does not exist
  until FH-3's intake lands; the harness refuses to substitute a
  different-vintage path (that would be the §4-row-7 trap wearing a different
  hat). Base 2021 runs on the existing cited AEO2021 entry.
- `meta.json` records `kind="full_forward"`, `arm`, `base_year`,
  `weather_posture` (`solve_year` / `base_year`), and
  `holdout_freeze_active_at_launch`. `score_crossover.py` accepts
  `full_forward` bundles on the identical scoring path and carries
  arm/base/posture into the score.

New ScenarioConfig field (rule 24/28c): `crossover_solve_year_weather`,
default False, registered in `_CACHE_KEY_OPTIONAL_FIELDS` (cache-neutral at
default) and in the mechanism matrix as `t1ff_solve_year_weather` (backcast
cells n/a — `__post_init__` refuses the posture off a full-forward run).

## 2. Leak: planned additions (§4 row 2 — the LIVE BUG)

`EIA860_OPERABLE_VINTAGE` (2025) was compared against every vintage's proposed
sheet. Fix: `data.fleet.operable_vintage_year(data_dir)` derives the bound
from the ACTIVE snapshot dir (`vintage_<year>/` → `<year>`, top-level → the
constant — byte-identical for every non-vintage run), the `_clean_fleet_year`
pattern generalized and shared.

**Every consumer audited** (grep `EIA860_OPERABLE_VINTAGE`, all call sites):

| Consumer | Disposition |
|---|---|
| `data/fleet/eia860.py` planned-additions filter (`eff_year > bound`) | **fixed** → `operable_vintage_year(data_dir)` |
| `data/renewables.py` proposed-capacity augmentation ×3 (monthly-capacity gate, `_add_proposed_capacity` filter, PTC-window tally gate) | **fixed** → same resolver, `data_dir` already in scope |
| `model/capacity_evolution/retirements.py::apply_announced_retirements` default `vintage` param (announced non-fossil horizon `vintage + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`) | **fixed** → default `None` resolves the active vintage in-function (call site is `evolve.py`, FFR-owned, untouched) |
| `config/capacity_market.py:1588` horizon comment | comment updated (the consumed value is the retirements fix above) |
| `data/fleet/models.py::_clean_fleet_year` | IS the pattern; now delegates to the shared resolver |
| `scripts/generate_financial_reports.py` | reporting-only, never sets a vintage → resolver would return the constant; left as-is |

**Proof (proposed-sheet rows passing the firm-status + ISO filter):**

| Vintage | ISO | BEFORE (`eff > 2025`) | AFTER (`eff > vintage`) |
|---|---|---|---|
| 2021 | ERCOT | **0** | 49 |
| 2021 | PJM | **0** | 37 |
| 2021 | MISO | **0** | 50 |
| 2021 | CAISO | **0** | 72 |
| 2021 | NYISO | **0** | 21 |
| 2021 | NEISO | **0** | 23 |
| 2023 | ERCOT | **0** | 71 |
| 2023 | PJM | 4 | 71 |
| 2023 | MISO | 2 | 82 |
| 2023 | CAISO | 2 | 74 |
| 2023 | NYISO | 2 | 59 |
| 2023 | NEISO | 0 | 54 |

Through the full `load_planned_additions` pipeline (thermal-only, U/V/TS,
fuel-mapped): ERCOT vintage-2021 0 → **11 units / 490 MW** (CODs 2022-2023),
vintage-2023 0 → **8 units / 356 MW** (CODs 2024); canonical snapshot
unchanged (30 units). The channel was silently zero for every vintage-seeded
run — **including the committed T1-H/T1-X runs**, which is why this fix
intentionally changes vintage-seeded behavior (see §8).

## 3. Leak: emission-rate window (§4 row 12)

`measured_plant_rates` forecast branch took the last N years *present in the
artifact*. Measured basis at HEAD (window = 2): every ISO's pre-2026
forecast-mode solve drew **[2024, 2025]** — and NYISO drew **[2025, 2026]**,
a quarantined year live inside the forecast input.

Fix, two scoped parts (deviation from the plan's unconditional one-liner,
reason in §8):

- `as_of_year` bound: the trailing window admits only years `<= as_of`.
  **Hindcast-lane callers** (`config.hindcast`) pass their solve year;
  the **plain forecast lane passes None and keeps its basis byte-identical**
  — its solve targets are 2026+ (bound would be a no-op there anyway), but
  its CAMPD-bins base-fleet build keys the estimator on `weather_year`
  (2024/2025), which the unconditional target bound would have shrunk —
  a T1-F behavioral change with no cache-epoch bump available (§8).
- `exclude_quarantined` (T1-FF only, from `is_full_forward_hindcast`): drops
  `{2022}` and `>= 2026` from the basis, **asserted** post-selection, so no
  quarantined year can enter a T1-FF rate basis. Threaded through
  `apply_plant_emission_rates_v2` → `_measured_plant_rate_map_v2` (both new
  args in its lru key) and the CHP BTM reconstruction
  (`runner._chp_measured_co2_inputs`), so grid and BTM stay on one basis.

Resulting T1-FF bases (real artifact, window 2): target 2023 → **[2021, 2023]**
every ISO; target 2021 (Phase B seed) → **[2020, 2021]**. Backcast branch
untouched.

## 4. Leak: hydro climatology (§4 row 11)

`build_hydro_fleet` gains `as_of_year` (threaded from the assembly seam when
`is_full_forward_hindcast`, `None` → byte-identical otherwise). On the
forecast-budget path it (a) trims the normal-water-year level climatology to
`full_forward_climatology_years(base)` — members of `HYDRO_CLIMATOLOGY_YEARS`
at/before the base, quarantined 2022 excluded — with the miso-110/neiso-72
PS-fold predicate mirrored onto the same trimmed window; and (b) clamps the
budget *shape* year (per-plant within-month shares) to the base, exactly as a
real base-vintage forecast would (its latest final EIA-923 vintage is `<=` its
base).

- Base 2023 climatology: **(2021, 2023)**.
- Base 2021 climatology: **(2021,)** — a single water year. **Finding, not a
  fix:** a one-year "climatology" is not a climatology; Phase B's hydro level
  is effectively "2021's water repeated", and 2021 was a dry year in the
  west. Disclosed per the task ("say so as a finding rather than widening the
  window") and already anticipated by FH-5's caveat list. The window
  regenerates from the as-of date; it is never widened by hand (rule 13).
- Residual (disclosed, not fixed): the hydro capability envelope / min-flow
  pooled windows (`eia930/envelopes.py`) still read the full
  `HYDRO_CLIMATOLOGY_YEARS` — all their consumers are default-off config
  gates (`hydro_dispatch_envelope`, `hydro_min_flow_floor`, `hydro_ror_split`)
  that no T1-FF arm arms, so nothing live leaks; a future session arming them
  in T1-FF must extend the same `as_of_year` thread.

## 5. Guards (§4 row 7 + run-time coverage)

- `assert_forward_drivers` generalized: iterates every non-bridge solve year
  at/above the boundary (for T1-FF, that is EVERY solve year — the old
  `max(start, boundary)` start now lands on the start year instead of
  no-opping below 2026), asserts (a) the year is seam-flagged forward — the
  single predicate both measured loaders (demand at `runner.py`, F923 at
  `plant_prices.py`) gate on at run time, (b) resolved gas equals the
  declared forward trajectory, surfacing the back-hold trap as a violation,
  (c) the realized-path leak check. It now runs **PRE-solve** (abort before a
  multi-hour run burns) and again post-solve for the meta record.
- **Back-hold hard error** (`resolve_annual_gas_price`): a full-forward year
  below the resolved trajectory's earliest knot RAISES (`mid` knots start
  2023 → a base-2021 run on `mid` dies loudly at 2021 instead of silently
  pricing it at 2023's $2.54 vs the $3.91 actual). Interior-gap back-hold
  (2022 bridge drawing 2021) is deliberately untouched — that is the
  documented bridge behavior.
- Entry-lookahead seam gate: the G-30 probe's hindcast branch read the NEXT
  year's measured demand even for crossover-forward next-years; it now falls
  to the growth-scaled fallback for them (no committed run armed the flag —
  byte-identical everywhere), and the harness additionally refuses
  `--entry-lookahead-reprice` with `--forward-from-base` outright.

## 6. Governance (plan §5)

- The prose-only carve-outs are now code, in their single home:
  `holdout_policy.HINDCAST_SEED_YEARS = {2021}`,
  `HINDCAST_BRIDGE_YEARS = {2022, 2026}`, `HINDCAST_SOLVE_YEARS = training ∪
  seed`, `hindcast_solve_year_violations()` (fail-closed, names the refused
  year's tier), and `FREEZE_FILE`. The harness imports them, parity-asserts
  the runner's own bridge constant at import time, and `_validate_window`
  fail-closes on the policy check after its local rules.
- The harness reads the freeze file and prints the explicit legality record
  at launch (active freeze + why this run spends nothing), records it in
  `meta.json` — "deliberate rather than accidental" (plan §5.3). Verified
  live in the §7 probe log.
- Scoring lower bound: `score_crossover._assert_scoreable_year` now refuses
  `< 2023` symmetrically to the existing `>= 2026` refusal, so a seed year
  can never be scored and no pre-2023 bench/actual is ever opened.
- `run_calibration_full.py` untouched (its freeze constant stays value-equal
  per the repo's separate-literals convention; parity-tested).

## 7. §3.3 harness-defect gate (I6 over-retirement) — RESULT

Probe: ERCOT, base 2023, vintage 2023, window 2023-2025 (3 solve years — T0
scale), Arm R, `results/hindcast/ercot-2023-2025-t1ff-armr-fh1gate`
(hindcast namespace, `kind="full_forward"`).

The T1-X reference (`docs/handoffs/ff-t1-gate-2026-07.md` §4.2): FC-1 I6
FAIL — 25.6 % of prior thermal economically retired in a single forward year
by 2025, adjudicated "a legacy-bin crossover-harness property, not the T1-F
config."

**RESULT: REPRODUCED — STOP-THE-LINE for Phase A (FH-4 must not start).**

The run itself is mechanically clean — solved [2023, 2024, 2025], zero
leakage-guard violations, both Arm R weather rebinds fired (2024/2025 log
lines), the hydro shape/level pinned to the base ("ERCOT 2023 hydro budget"
while building 2025), gas on `hindcast_realized` every year, freeze legality
printed. The defect is the retirement layer, and it carries over exactly as
§3.3 predicted:

| Year | Prior thermal | Econ retired | I6 fraction |
|---|---|---|---|
| 2023 | 78.2 GW | 0.00 GW | 0.0 % |
| 2024 | 78.2 GW | 0.00 GW | 0.0 % |
| 2025 | 78.5 GW | **21.05 GW** | **26.8 %** — I6 FAIL (> 20 % cap) |

Cumulative by 2025: 21.05 GW = 26.9 % of the initial vintage-2023 thermal
fleet — vs the T1-X reference 25.6 %. The full FC-1 signature reproduces, not
just I6: the registered invariant battery reads **I6 FAIL** (26.8 % single-year
econ retirement), **I7 FAIL** (2025 thermal 57.5 GW < the retirement-bounded
floor 78.5 GW), **I12 WARN** (reserve-margin band exits) — the same
I6/I7/I12 triple `ff-t1-gate-2026-07.md` §4.2 adjudicated on the vintage-2023
T1-X crossover.

**Reading (rule 11 — root cause, not tuned):** the property follows the
harness posture, not the input stack — Arm R feeds the screens *realized*
weather/gas and the wave still fires entering 2025, once the two-consecutive-
loss counters mature on the 2023/2024 perfect-foresight margins of an
over-supplied vintage fleet (the s3/G-31 root cause, unchanged). It is
therefore a **harness/screen-grain defect upstream of T1-FF**, exactly as the
T1-X adjudication said ("a legacy-bin crossover-harness property, not the
T1-F config"), now measured at the T1-FF posture. Nothing here is tuned in
response; the open remediation lanes are the already-chartered ones (FF-1A
R-NEW retirement pipeline / G-31 grain / FFR retirement-calibration lane).

**Consequences:** (a) FH-4/Phase A is BLOCKED on an over-retiring harness —
its REQUIRES line already demands this gate PASSED; the block stands until a
retirement-lane fix lands and a re-probe passes. (b) The probe's dispatch-
skill numbers (registered for the record: price gaps 2.1/54.0/2.3, fuel-mix
gaps 9.8/13.6/28.1 vs keeper ercot149) are GATE CONTEXT ONLY — they must
never be quoted as T1-FF skill, because 2024's price and 2025's fuel mix are
dominated by the defect (2024 scarcity from the pre-wave tight fleet, 2025
mix from the post-wave gutted one). (c) The probe is registered on the
hindcast namespace (`ercot-2023-2025-t1ff-armr-fh1gate`, kind
`full_forward`) with the failing invariants in its sidecar, so the record is
the dashboard, not this prose.

## 8. Byte-identity attestation + deviations

**Attestation instrument:** `build_config` outputs and `ScenarioConfig` cache
keys, measured at `a92ae97` BEFORE any FH-1 edit and re-measured AFTER all of
them — all five identical:

| Config | Key (before == after) |
|---|---|
| `ScenarioConfig()` default | `0e9fce2fb55b889f` |
| ERCOT T1-X crossover CLI | `52831f438fa42bdd` |
| PJM T1-X crossover CLI (+cmc) | `e946234919bb158c` |
| ERCOT plain T1-H CLI | `89f1d5acf26e35d7` |
| PJM plain T1-H CLI | `f14a9df6483642f8` |

The full crossover + T1-FF contract suites pass (19 + 28), and the touched
modules' unit suites pass (emission rates / hydro / fleet / fuel 363, capacity
+ campd bins 251, pipeline 150, config 107 after installing the env's missing
`tzdata`).

**Pre-existing drift, filed (not caused, not fixed here):** the keys above do
NOT match the 2026-07-19 committed crossover sidecars
(`frontend/data/hindcast/ercot-2023-2027-crossover.json` `1e0260169cddd989`,
`pjm…` `3524d5023b1b9163`) — the keys had already moved at `a92ae97` before
this session's first edit. Consistent cause: FFR-1D's config hygiene
(`b9ca991`, merged #3245) deleted dead ScenarioConfig flags, and a field
deletion is never cache-neutral (`asdict` payload shrinks; rule 26 accepts
this — deleted means deleted). Same event broke the pinned-default-key test
(`tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py::TestFieldRegistration::test_default_cache_key_unmoved`,
pins `603c2498bf71d21d`) — **failing at origin/main today**, independent of
FH-1. Both belong to the pending §W1-X cache-epoch bump (which this session
was instructed not to take); the re-pin should land with that bump. A third
pre-existing failure, unrelated:
`tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`
still asserts PJM holds no marker, stale against PJM's 2026-07-31 `complete`
declaration (both inputs untouched by FH-1; the battery/board refresh is
FFR-3A's, per the pack's §0a item 5).

**Scoped deviations from the letter of the prompt, with reasons (rule 11 —
root cause, stated):**

1. *Emission bound is `as_of_year`-parameterized, not the unconditional
   target-year one-liner.* The unconditional bound is byte-identical for
   every solve-year target ≥ 2026, but the plan's inventory missed one call
   site: the CAMPD-bins base-fleet build applies v2 rates at
   `year = weather_year` (2024/2025) in EVERY default forecast — the
   unconditional bound would have changed the T1-F lane with no epoch bump
   available. The parameterized bound delivers the identical fix on every
   solve-year target while keeping the plain forecast lane byte-stable.
2. *Vintage-seeded T1-H/T1-X data behavior changes by design.* The additions
   fix (§2) and the hindcast-lane emission as-of bound (§3) alter what a
   NEW T1-H/T1-X run loads — that is the leak being closed (row 2 is "a LIVE
   BUG for any vintage-seeded run"). Committed bundles are immutable records
   under per-run out-dirs (no shared-cache poisoning); the attestation above
   is at the config/cache-key surface, which is what "the committed
   ERCOT/PJM crossover meta + cache keys" pins. The next T1-X re-run will
   differ from the committed one for these documented reasons.
3. *T1-H/T1-X (non-T1-FF hindcast) emission bases now include 2022 rows for a
   2023 target* (`[2022, 2023]` at window 2). The T1-FF quarantine trim is
   scoped to full-forward runs per the task; whether the plain-hindcast lane
   should also exclude 2022 (its bridge contract says "its data never read")
   is flagged for the program owner rather than widened unilaterally.

## 9. What FH-2/FH-3/FH-4 inherit

- Arm K base 2023 is BLOCKED on FH-3's `hindcast_asknown_aeo2023` intake (the
  harness hard-errors with the pointer). Arm K base 2021 runs today.
- The demand-growth BLOCKER (§4 row 6) is untouched here: Arm K's forward
  demand still grows at today's near rates (ERCOT mid 8.5 %/yr) until
  FH-2/FH-3 land the vintage table. Arm R is unaffected (zero-year spans).
- `_scale_demand`'s backward no-op (FH-2 item 2) is unreachable in the
  shipped arms (Arm R spans are zero-year; Arm K weather = base ≤ every
  solve year) but remains open for any future posture.
- FH-4 must arm nothing beyond the two arms; the §7 gate result below is its
  precondition.
