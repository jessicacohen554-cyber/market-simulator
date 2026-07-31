# FFR-1A — Confirmed-exit accounting: ledger the derates, complete the exits (2026-07-31)

**Session:** FFR-1A (forecast-readiness prompt pack Wave 1, `[FABLE]`; audit §4 row P1-a).
**Findings fixed:** FR-1 (I4/A1 capacity-accounting leak, BLOCKER), FR-2 (partial-year exit
ghost, HIGH), FR-13 (latent additions-baseline gap, MED), FR-23 (docstring drift, the
`evolution_ledger.py` schema text + the `retirements.py` hydro claim slice only).
**Branch:** `claude/forecast-readiness-fr-fixes-typcr5` — strictly ordered:
`a47a949` (arm 1, bookkeeping, dispatch-inert) → `4bad95c` (arm 2, behavioral, cited) →
`53a8f4d` (arm-2 over-subscription cap, found by this session's own probe evidence before
any arm-2 probe was registered — §3).
**Baseline:** `origin/main` @ `40ecb0a` (2026-07-31). No default, band, threshold, or curve
changed; no cache-epoch bump (§W1-X owns it) — all probes below use isolated `--out-dir`
caches via `run_full_horizon.py --out-dir` (redirected cache). Every invocation ≤ 5
solve-years (§2.1b).

---

## 1. What was wrong (root cause, verified live)

`apply_confirmed_exits` derates plant-binned tranches **in place** — the tranche's
`unit_id` survives with a smaller `pmax_mw` — while the `evolve_fleet` events recorder
emitted retirement rows only for unit_ids **absent** from the surviving fleet (set-diff),
and the documented `confirmed_derates` ledger key had a reader
(`run_driver_battery.py`) but **no writer**. The derated MW left the fleet with no ledger
record, so I4 (`fleet_after == fleet_before − retirements + additions`, per fuel) failed by
exactly the derated MW.

Captured live in the NEISO before-probe (`evolution_2028.json`, pre-fix code):

```
retirements: []            confirmed_derates: <key absent>
coal before: 108.0         coal after: 54.0        → I4 FAIL "2028:coal off by 54.0 MW"
```

The 54.0 MW is Merrimack's plant-binned coal tranche (fleet carries 108.0 MW for plant
2364; the registry's 459.2 MW exit ≥ the binned MW, so the reduced leg floors at 0)
derated by the month-6 annual-average factor 6/12 — FR-1 (the missing rows) and FR-2 (the
ghost half that would never leave) in one number.

Two adjacent defects fixed in the same arms:

- **FR-13 (latent):** step-4.5 commissioned pipeline units were inserted into the fleet
  *before* the step-5 additions-recorder baseline snapshot, so arming
  `entry_commissioning_lag` would add MW with no `thermal_additions` row — an I4 failure
  of the opposite sign in every COD year. The recorder baseline now snapshots pre-insert;
  the decision-grain baseline (`entry_decided_mw_by_tech`, the gas_ct backstop budget)
  stays post-insert, so nothing double-counts.
- **Reason split:** the recorder stamped every step-0/step-1 exit `reason="known"` in one
  conflated diff. It now attributes `confirmed` (step 0) and `announced` (step 1)
  separately — the RC-1B-documented vocabulary both downstream readers
  (`score_capacity_hindcast.py`, `run_driver_battery.py`) already consume, keeping their
  legacy-`known` tolerance for old bundles.

## 2. Arm 1 — bookkeeping (commit `a47a949`, dispatch-inert by construction)

- `evolve.py`: step-0 recorder seam writes `confirmed_derates` rows
  (`unit_id, fuel, mw_before, mw_after, derate_mw`) for surviving-but-shrunk unit_ids and
  `reason="confirmed"` retirement rows for dropped ones; step-1 recorder diffs against the
  post-step-0 fleet with `reason="announced"`. Additions-recorder baseline moved above the
  step-4.5 insert (FR-13).
- `evolution_ledger.py`: `new_events()` creates the `confirmed_derates` key; module schema
  text updated to be true of the writers (FR-23).
- `check_forecast_invariants.py`: I4 closes the per-fuel balance including derates —
  `after == before − retirements − confirmed_derates + additions (± CCS shifts)`. Legacy
  ledgers (key absent) stay scoreable.
- `retirements.py`: the `_FIRM_CLEAN_FUELS` comment no longer claims hydro is routed
  through the accreditation rebuild (it structurally cannot be — FR-3; fix is FFR-1C's;
  `adequacy.py` untouched).
- Tests: `TestEvolveFleetLedgerReconciliation` — the per-fuel reconciliation suite at the
  `evolve_fleet` seam FR-26 called out as exactly-missing (trivial 2-unit fixture, binned
  derate, reason split, commissioned-unit row) + I4 derate-close/derate-leak checker cases.

Every recorder change is gated on `events is not None` and touches no fleet object — the
solve path is byte-identical by construction; §4 verifies it empirically.

## 3. Arm 2 — behavioral (commit `4bad95c`, registry rows cited in the commit)

Each confirmed-exit row now carries a fixed two-leg MW-removal schedule (absolute MW, which
composes exactly across years — factor-of-factor arithmetic cannot):

- `exit_month ≤ 6`: effective year removes `(12−m)/12 × mw` (the annual-average share the
  old code removed); **the following year removes the remaining `m/12 × mw`** (the
  completion leg — new). Derate branch only; a unit-grain row drops its whole unit at the
  effective year (annual-grain convention unchanged).
- `exit_month > 6` / no month: single full-MW leg at the effective year (numerically
  unchanged).
- Pre-start backlog (`apply_backlog=True`): rows effective before the first simulated year
  remove their **full** MW (both legs already due) — the old code re-applied the
  annual-average blend to first-half backlog rows, so V H Braunig (March 2025) still held
  3/12 of its 477 MW in a 2026-start ERCOT fleet.

Live rows affected (all eight `exit_month ≤ 6` rows; instruments in the commit):
ERCOT V H Braunig 1/2 (2025-03, backlog), NEISO Merrimack 1/2 (2028-06),
PJM Brandon Shores 1/2 + Wagner 3/4 (2029-05).

**Over-subscription cap (`53a8f4d`).** The arm-1 probe detail showed both live
completion cases are *over-subscribed* — the registry exit MW exceeds the plant's binned
fleet MW (Merrimack 459.2 registry vs 108.0 binned; Brandon Shores 1370.2 vs 1273.0 —
and Wagner (1554) has **no binned representation at all** in the PJM fleet, so its
743.7 MW of registry rows act on nothing; the audit's "2,144 MW" of RMR registry rows
reach the fleet as plant 602's 1,273 MW). Uncapped, the effective-year leg would have cut
deeper than the annual-average (NEISO 2028: 108→0 instead of 108→54). The current/prior
removal is now apportioned by `binned/raw` when `raw > binned`, reproducing the pre-fix
effective-year factor exactly in every subscription regime; the uncapped completion leg
floors the factor at 0 the following year, finishing the plant at `max(0, binned − mw)`.
The first NEISO/ERCOT arm-2 probe pair was killed and re-run at `53a8f4d`; nothing from
the uncapped build was registered.

## 4. Acceptance evidence

### 4.1 Arm 1 byte-identity (ledger-only change)

NEISO T1-F 2026–2030, `origin/main` (`40ecb0a`) vs arm 1 (`a47a949`), identical
config → identical cache key (`ff63ca9a0a1d65c6`), isolated out-dirs:

- **Every value column of every `year_<y>.parquet` is identical** (hour, dispatch,
  wind, solar, slack, dump, price, storage_charge/discharge/soc, flows, demand —
  element-wise array equality, all 5 years), and the LP `objective_value` is equal to
  the last decimal (e.g. 2028: `4492371766.675091` both sides).
- `year_*_floor_retentions.json` byte-identical (all years).
- The only parquet **byte** difference is the embedded `market_sim` metadata blob's
  `build_time` / `solve_time` wall-clock fields — non-deterministic run-to-run timing,
  not a code effect (verified per year: `meta_diffs=['build_time','solve_time']` only).
- The evolution ledgers differ exactly as intended: the new `confirmed_derates` rows +
  the `confirmed`/`announced` reason split; fleet totals unchanged.

PJM T1-F 2026–2030, same protocol: **all five years value-identical** (every parquet
column element-wise equal, objective equal), `meta_diffs=['build_time','solve_time']`
only, floor-retention JSONs byte-identical. Arm 1 is dispatch-inert on both probe ISOs.

### 4.2 I4 before/after — T1-F 2026–2030, NEISO + PJM (the two FC-1-on-I4-alone ISOs)

| ISO | leg | I4 | detail |
|---|---|---|---|
| NEISO | before (`40ecb0a`) | **FAIL** | `2028:coal off by 54.0 MW` |
| NEISO | arm 1 (`a47a949`) | **PASS** | `closes` — 2028 ledgers 3 Merrimack tranche derates (`COAL_North_p2364_{committed,econ,peak}`) summing 54.0 MW |
| PJM | before (`40ecb0a`) | **FAIL** | `2029:coal off by 742.6 MW` — I4 is PJM's ONLY failing invariant (audit's "743 MW", Brandon Shores month-5 derate branch; Rockport's 2,600 MW IS ledgered — full-drop path) |
| PJM | arm 1 (`a47a949`) | **PASS** | `closes` — 2029 ledgers 3 Brandon Shores tranche derates (`COAL_PJM_SWMAAC_p602_{committed,econ,peak}`: 132.2 + 595.5 + 14.9 = 742.6 MW) beside the 4 Rockport `confirmed` full-drop rows (2,600.0 MW) |
<!-- PJM-I4-ROWS -->

The PJM decomposition pins the audit's number: plant 602's binned fleet MW is 1,273.0
(vs 1,370.2 registry — over-subscribed), so the month-5 annual-average leg removes
(7/12) × 1,273.0 = 742.6 MW; Wagner's rows have no binned fleet counterpart and act on
nothing. **Arm-1 acceptance met on both target ISOs: I4 FAIL→PASS with dispatch
value-identical, no other invariant moved.**

NEISO ledger trace (identical dispatch both legs): coal 108.0 → 108.0 → **108.0→54.0
(2028)** → 54.0 → 54.0; before-leg `retirements=[]` with no `confirmed_derates` key —
the leak — vs arm-1 `confirmed_derates` totalling 54.0 in 2028 and 0 elsewhere. The
54 MW ghost that persists 2029–2030 in BOTH legs is FR-2's separate defect (arm 2,
§4.3). NEISO's I12 band failure (2027–2030, margin above the requirement-implied band)
is pre-existing at `origin/main`, identical across legs, and outside this session's
scope (§6).

<!-- I4-TABLE -->

### 4.3 Arm-2 T0 probes (NEISO + ERCOT) and T1-F re-probes (PJM + NEISO) — MW deltas, attributed

<!-- ARM2-DELTAS -->

## 5. Registered runs

<!-- REGISTERED -->

## 6. Out of scope / follow-ups

- **I12 (reserve-margin band) FAILs in the NEISO T1-F probes** (2027–2030 above the
  requirement-implied band) — pre-existing at `origin/main`, unrelated to the ledger seam
  (no capacity decision changed in arm 1; arm 2 removes ghost MW, which cannot raise the
  margin). Stays with its owning lane (the §2.1b gate re-score, FFR-3A).
- FR-3 (hydro in the accredited ledger) — FFR-1C.
- FR-7/FR-8 (solve-year availability) — FFR-1B.
- The cache-epoch bump for the fleet-affecting arm 2 — §W1-X at Wave-1 close (this
  session's probes are all isolated-cache by construction).
- No `ScenarioConfig` field added → no mechanism-matrix row (checked; CI guard
  `check_mechanism_matrix.py` agrees).
