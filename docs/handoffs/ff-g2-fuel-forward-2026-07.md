# FF-G2 — fuel-forward trajectories: AEO2026 vintage bump + near-term grounding (2026-07-20)

**Session.** Lane L-INP. Owner ask: refresh the one-vintage-stale, demonstrably
low fuel-forward inputs (Henry Hub the highest-sensitivity forecast input),
mechanical AEO2025→AEO2026 bump plus a deep-research grounding doc; triangulate
the near-term against STEO + the NYMEX strip; present a findings-first
owner-decision box on a near-term blend (implement nothing beyond the refresh
without the owner's pick). Branch `claude/henry-hub-fuel-forward-ohbpw0`.

**Standing deliverable:** `docs/fuel-forward-methodology-2026-07.md` (design,
field survey, per-fuel grounding, delta ledger, near-term triangulation, owner
box, gaps, maintenance). This handoff records the audit trail + verification.

---

## 1. What changed (all forecast-only)

| Artifact | Change |
|---|---|
| `scripts/data/fetch_eia_aeo.py` | vintage-aware: `SCENARIOS_BY_AEO` ({2025: ref2025, 2026: cb2026}), `_out_csv_for`/`_scenarios_for`, edition-aware `--start-year` default; docstring |
| `scripts/data/derive_fuel_trajectories.py` | `--aeo-year` (default 2026), `_SCENARIO_TO_PATH_BY_AEO`, `_load_aeo(year)`, dollar-year-aware block labels; nuclear explicitly NOT re-derived |
| `data/raw/eia-aeo/eia_aeo2026_fuel_prices.csv` | NEW — 858 rows (11 series × 3 scenarios × 26 yr, 2025-2050), real 2025$ |
| `src/market_sim/config/constants.py` | `HENRY_HUB_TRAJECTORIES` low/mid/high **2026-2050 only** re-vintaged (2023/2024/2025 actuals kept); `COAL_PRICE_TRAJECTORIES` + `OIL_PRICE_TRAJECTORIES` whole tables (2025-2050); all three comment headers |
| `data/raw/fuel-forward-benchmarks/` | NEW datatype — STEO snapshot + stale-flagged EIA NYMEX feed + sha256 README (MANUAL row for the current CME strip) + `md/` conversion |
| `scripts/data/fetch_fuel_forward_benchmarks.py` | NEW — STEO + EIA-free-NYMEX fetch |
| `tests/test_fuel_trajectory_consistency.py` | NEW (10) — constants == AEO2026 derivation, historical actuals fixed, nuclear unchanged |
| `tests/test_uncertainty.py`, `tests/test_fuel.py` | 2 value-tests updated for the new vintage |
| `docs/fuel-forward-methodology-2026-07.md`, `CHANGELOG.md`, `data/raw/eia-aeo/README.md`, `docs/parameter-citations.md` | docs |

**Nuclear (`NUCLEAR_FUEL_PRICE_HISTORICAL`) unchanged** — its EIA Uranium
Marketing source did not update, so rule 23 does not re-trigger it (stays real
2024$).

## 2. Headline numbers

Mid Henry Hub, $/MMBtu (pre-basis):

| year | AEO2025 (old) | **AEO2026 (new)** | STEO Jul-2026 |
|---|---|---|---|
| 2026 | 2.74 | **3.88** | 3.67 |
| 2027 | 2.62 | **3.62** | 3.49 |
| 2028 | 2.73 | **3.67** | — |

The old mid was ~$0.9 *below* STEO for 2026; the bump closes and slightly
overshoots it (+$0.21). Gas 2050 low/high spread widened ($2.75/$13.67), lifting
the forecast-only `uncertainty.GasMarginal` AEO σ floor 0.555 → 0.843.

## 3. Byte-identity for backcast (the gate — PROVEN structurally)

The task required demonstrating the backcast path never reads the refreshed
trajectories, or stopping if it does. Traced in `data/fuel.py`:

- **Coal & oil trajectories are forecast-only.** `resolve_fuel_prices` gates:
  `if config.mode == "forecast": resolve_annual_coal_price(...)` else flat
  `COAL_PRICE_ESCALATION`; oil `resolve_annual_oil_price(...) if forecast else
  OIL_PRICE_PER_MMBTU`. Backcast never reads either table.
  (`test_coal_price_backcast_still_uses_flat_escalation` pins this.)
- **Gas trajectory is read in backcast only for years ≤2025**, and only via the
  neighbor-price seam (`data/neighbor_price.py::neighbor_gas_price` →
  `HENRY_HUB_TRAJECTORIES[scenario][year]`, year ∈ {2023,2024,2025} for a
  backcast). Those three entries are **held byte-identical** (the refresh
  discards AEO2026's own 2025 base value $3.47 in favour of the measured $3.52).
  The main gas resolver uses `gas_price_override` (measured) in backcast; even
  without an override it would read ≤2025, which is unchanged.
- **Nuclear** is read in both modes → left byte-identical (not re-derived).

Conclusion: no backcast surface sees any changed value. **No backcast keeper
input changes** (asserted). The only "measured overlay" concern — F923 delivered
fuel — is untouched by construction (this session edits only forecast
trajectories).

## 4. Verification record

- **New consistency tests** `tests/test_fuel_trajectory_consistency.py` — 10
  passed: gas forecast-years == derivation; ≤2025 actuals fixed and ≠ AEO2026
  base $3.47; coal/oil == derivation; anchors 2025; nuclear unchanged & 2024;
  AEO2026 raw is 2025$; low<mid<high 2050.
- **Fuel/uncertainty/neighbor/crossover suites:** 130 passed after the two
  value-test updates.
- **Full suite** (`pytest -q`, 4589 passed / 51 failed / 673 s): the **51
  failures are ALL pre-existing on clean `origin/main`** — verified by stashing
  this session's changes and re-running: the `test_transmission_expansion::
  TestScenarioGate` cluster fails identically with the work stashed (a main
  `TypeError`, unrelated to fuel), and the remainder are the fresh-checkout
  gitignored-`data/clean` failures the sibling capacity-cost session also
  documented. None touch fuel trajectories. [Full stash-diff of the 51 recorded
  in §7 below.]
- **F923 basis re-check (§4.5 of the doc):** `GAS_BASIS_DIFFERENTIAL` adders are
  already measured EIA-923 / EIA-NG-Weekly delivered bases — they pass the
  rule-13 admissibility test verbatim and are unchanged (the vintage bump is a
  Henry Hub *level* change only).

## 5. T0 forecast probe (optional, §2.1b ≤5 solve-years)

ERCOT 2026 single-year forecast, before/after the vintage bump. Status recorded
in §7 (the single-year ERCOT LP exceeds the foreground window; run in-session in
the background). First-order expectation: delivered ERCOT gas 2026 rises
$2.24 → $3.38/MMBtu (+$1.14; Henry Hub +$1.14 + the −$0.50 Waha basis), i.e.
≈ +$8/MWh on gas-marginal hours (CC HR ~7 MMBtu/MWh) — a large, expected,
forecast-only price lift that is the whole point of correcting the low bias.

## 6. Owner decision — near-term reconciliation (findings-first, NO default flip)

Per plan §7.6, nothing beyond the AEO2026 refresh is implemented. **Finding:**
the vintage bump alone closed the near-term gap (now +$0.2 vs STEO, was −$0.9),
so a strip/STEO near-term blend is now low-value.

- **Option A (RECOMMENDED): pure AEO2026 annual paths (status quo shape).**
  Single-source, derivation-locked, no new machinery; near-term already within
  ~$0.2 of the market reference.
- **Option B: formulaic near-term blend** (STEO/NYMEX strip over 12-24 mo
  decaying into AEO). Rule-13 admissible if formulaic; but post-bump it moves
  the near term only ~$0.2 (downward) and adds a maintained second source + a
  test + a probe.

Benchmarks/strips are context, never fit targets, regardless of the pick.

## 7. Open items / notes for the record

- **Parameter registry (`frontend/data/parameters.json`, 1.5 MB) push
  DEFERRED** — the same transport limit the capacity-cost session hit (§4c,
  2026-07-19): the 1.5 MB JSON exceeds a safe single `push_files` payload. It is
  regenerated locally (values refreshed; henry_hub/coal/oil citations retargeted
  to AEO2026 in the JSON), `validate_parameters.py` passes against main's
  registry (no structural change — no params added/removed), and the standalone
  registry-reconcile chore picks the values up by construction. The
  human-readable `docs/parameter-citations.md` (small diff) carries the refreshed
  values + the AEO2026 henry_hub citation and is pushed.
- **FF plan §1.2-11 provenance-gaps frontier row + `docs/gap-register-2026-07.md`
  §3.11 FF-G2 row:** the task said these landed 2026-07-19 via FF-G1's
  core-wiring patch — **they are ABSENT on `origin/main`** (grep found no `FF-G2`
  or `1.2-11` provenance row in either file). Per the task's instruction I did
  **not** create them; noting here instead. The gap-register/plan status update
  is an open item for whoever lands the FF-G1 patch or a follow-up.
- **`docs/handoffs/ff-wave-manager-ledger-2026-07.md`** — not edited
  (manager-owned, per the task).
- **FC-5 external-corridor pin** stays on AEO2025 (FF-0F's choice) — out of
  scope; the AEO2026 vintage is now available should the owner re-pin.
- **Full 51-failure stash-diff:** captured in
  `scratchpad/fails_mytree.txt` vs a stashed-main re-run of the same files; all
  pre-existing (env gitignored-clean-data + the main ScenarioGate TypeError).

## 8. Transport

constants.py (350 KB) + CHANGELOG.md exceed a safe single `push_files` payload;
per the FF-G1 / capacity-cost precedent they ship via a committed, verified
patch (`docs/handoffs/patches/ff-g2-fuel-forward.patch`) if the API push path is
used; the owner directed `git push` for this session, so the branch carries the
real on-disk bytes directly. Everything else (scripts, the AEO2026 CSV, the
benchmark datatype, new tests, docs) is source-sized.
