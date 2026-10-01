# PREREG — ARM-3-ARM: arm the corrected MISO clean-tier rows as the shipped forecast default

**Pushed BEFORE the arming edit and BEFORE any solve.** Owner card **D-29 is SIGNED**
(2026-08-11, sitting Addendum AK.8). This lane EXECUTES a signed decision; it does not
re-decide it. If a measurement here CONTRADICTS the signed evidence, the lane STOPS and
escalates — it does not "fix" the discrepancy.

**Branch:** `claude/arm-miso-clean-tier-default-jqwfpc` off a freshly fetched
`origin/main` (`e346cfb`).

**Scope:** MISO only (rule 25 `[R-ISO-SCOPE]`), forecast mode only (rule 22 —
the holdout freeze is ACTIVE and MISO holds no marker), forecast namespace only
(rule 15's forecast clause). No keeper contact. No backcast-registry touch.

---

## 1. What is being armed, and by which seam

`miso_clean_tier_rows` (FFR-7B Arm 3 / FFR-6B E-2) becomes the **MISO forecast
default**. The seam is `ISOConfig.default_scenario_overrides` in
`config/iso_configs.py::_miso_config` — **the identical seam D-26 used to arm
Arm 2** (`miso_rps_compliance_regions`), not a change to the `ScenarioConfig`
field default.

That choice is forced, not stylistic:

* The `ScenarioConfig` field default must stay `False`, because flipping it would
  arm the family for **every** ISO — a rule-25 violation — and would break the
  strict Arm-2 dependency (`runner.py` refuses `miso_clean_tier_rows` without
  `miso_rps_compliance_regions`) for the five ISOs that never carry the K-row grain.
* `default_scenario_overrides` is **forecast-lane-scoped at CONSUMPTION**:
  `runner._rps_region_grain_active` requires `config.mode == "forecast"`, and
  `run_calibration_full.py` never applies `default_scenario_overrides` at all. The
  backcast lane is doubly insulated, which is what rule 22 requires here.

## 2. THE CACHE EPOCH — declared, and measured before the fact

A default flip moves the resolved key of every MISO **forecast** run. This is
arithmetic on the config, not a solve outcome, so it is measured now and pinned
here (`scripts/probes/_arm3arm_cache_epoch.py`, committed with this prereg):

| key | value | moves? |
|---|---|---|
| GLOBAL pinned default `ScenarioConfig()` | `603c2498bf71d21d` | **NO — unmoved** |
| MISO forecast lane default, **pre-arm** (clean OFF) | `cd2403cc031515db` | — |
| MISO forecast lane default, **post-arm** (clean ON) | `9337e00504e1e72a` | **YES** |

**`cd2403cc031515db` → `9337e00504e1e72a` IS the cache epoch for the MISO forecast
lane.** Every MISO forecast bundle addressed under the pre-arm key is superseded;
none is silently re-used, because the armed value differs from the registered
`_CACHE_KEY_OPTIONAL_FIELDS` default and therefore enters the digest.

Two facts that make this epoch safe rather than merely declared:

* **The global pin does not move.** `miso_clean_tier_rows` stays a registered
  `_CACHE_KEY_OPTIONAL_FIELDS` member at field-default `False`, and the pinned
  default key is computed on `ScenarioConfig()` (iso ERCOT, no ISO override
  applied). `tests/regression/test_persisted_identity.py` and the ~10 other
  pins on `603c2498bf71d21d` must all stay green. **This is the CI verdict the
  lane waits for before merging.**
* **The two poles are exactly the signed pair's keys.** The post-arm key
  `9337e00504e1e72a` and pre-arm key `cd2403cc031515db` reproduce the ARM3-FIX
  armed/control legs **byte-exactly at HEAD** — verified before this prereg was
  written. The armed default therefore resolves to *the very scenario the signed
  evidence measured*, not to a lookalike.

  (Posture note for reproducers: the ARM3-FIX pair ran `--golden-posture` with
  the **scalar** `capacity_market_clearing` left False — the golden posture
  supplies the per-ISO `capacity_market_clearing_by_iso` seam instead. The
  sidecars' `capacity_market_clearing: true` is MISO's *resolved* per-ISO value,
  not the scalar. Reproducing with `cmc=True` yields a different key and is the
  wrong posture.)

## 3. THE BINDING PRE-FLIGHT GUARD — stop-the-line

**D-26's armed MISO forecast default (Arm 2) must be untouched by arming Arm 3.**

> **PASS iff the per-region RPS duals read exactly `[0, 30, 0, 30, 0]`
> (MN, MI, WI, IL, MO) in EVERY year 2031–2035 of the armed-default solve.**

Any dual that moves — any year, any region — is a **STOP-THE-LINE event**: the
measurement is committed, the owner is escalated, **nothing is promoted**, and the
arming commit is not merged.

This is the guard's informative side. Arm 3 can only disturb Arm 2 where Arm 3 is
ON, and the arm-off pole is the pre-arm posture already measured three times
(FFR-7B-2 §3.1, ARM3-MEASURE, ARM3-FIX §4.1) — all reading `[0,30,0,30,0]`, the
last of them under the key `cd2403cc031515db` this prereg reproduces at HEAD.

**Control-leg reachability is a KNOWN, DOCUMENTED CONSEQUENCE of arming, stated
here before the fact so it is not later mistaken for an omission.**
`apply_iso_scenario_defaults` applies an ISO override to any field whose value
EQUALS the `ScenarioConfig` default. `miso_clean_tier_rows` is a bool defaulting
to `False`, and `--miso-clean-tier-rows` is `store_true` with no negative form —
so after arming, **no CLI invocation can reach a clean-tier-off MISO forecast
leg.** This is the caveat `iso_configs.py` already records for
`entry_vre_capacity_revenue` and D-26's Arm 2, now extended to Arm 3. The
arm-off pole is consequently the **committed** ARM3-FIX control bundle, addressed
by the key reproduced in §2 — not a re-solve, and it cannot be one.

## 4. The solve — protocol, fixed before it runs

One leg, the shipped armed default, on a freshly regenerated `data/clean`:

```
uv run python scripts/run_full_horizon.py --iso MISO --start-year 2031 --end-year 2035 \
    --golden-posture --out-dir results/arm3arm/miso-2031-2035-armed-default
```

**No clean-tier flag is passed.** That is the point: the leg must arm itself from
the ISO default, exactly as every downstream MISO forecast run now will.

* Rule 12: 5 solve-years in one invocation, **years sequential**, **1 concurrent**
  (peak RSS ~9.8 GB against 15 GB — two MISO legs would OOM). No PJM work in this
  session; a concurrent ERCOT lane is expected and permitted.
* Rule 22: forecast mode, 2031–2035, 2026+ clause. No measured actual is read or
  scored. No out-of-training backcast year is solved.
* Reads via `scripts/probes/_arm3_clean_row_horizon.py`, **reused byte-identical**
  (the committed prereg protocol: reuse, do not re-derive).

## 5. Pre-stated expectations — written before the solve

Falsifiable, and taken from the signed ARM3-FIX §4 evidence. **A miss on E1–E3 is a
contradiction of the signed card and escalates rather than being "fixed".**

* **E1 (the guard, §3).** RPS duals `[0,30,0,30,0]` in all five years.
* **E2 — resolved posture.** The run's own `run_config.json` /
  `full_horizon_summary.json` report `miso_clean_tier_rows: true` and
  `miso_rps_compliance_regions: true`, both `Derived` off the RESOLVED config, with
  **no flag passed**. Cache key `9337e00504e1e72a`.
* **E3 — clean duals.** MI **exactly 0.0000** in 2031–2034 (RHS-0 arithmetic
  certainty: MI's obligation is 0.0000 until 2035) and **binding at the $30 ACP
  ceiling in 2035** (obligation 0.4560; in-mask supply 57.351 TWh vs 95.771 TWh
  required, −38.420 TWh ⇒ ~$1.15 bn of ACP). **MN slack in all five years** under
  the shipped 5-zone mask.
* **E4 — E-1 discipline (no build limb).** Capacity events identical to the signed
  armed leg's; the row's only output is a price. The 2035 dual first reaches a
  capacity screen in 2036, outside this window.
* **E5 — alternate-optima tolerance.** 2031–2034 are slack-row years where the fix
  is a proven solve no-op; small objective wobble against the signed leg is
  alternate-optima noise, not a finding. **E1–E3 carry no such tolerance** — they
  are exact.

## 6. What this lane does NOT do

* Does not touch MISO's backcast keeper `2026-08-09-miso-148-basis-aware`, whose
  NOT-YET at HEAD (fail set: C3a 2025 −15.6 %, C3b 2025 NRMSE 0.212) is the
  promotion's **own declared result**, not re-scoring drift (Addendum AK.4). This
  lane is forecast-side and does not contact it.
* Does not resolve the **MN eligibility-mask reading** (in-state West-only would
  flip MN to binding at $30 in all five years, short 27.1–41.9 TWh; the shipped
  5-zone delivery mask leaves it inert). That stays the owner's open statutory
  call, unchanged by arming.
* Does not touch another ISO's shard, verdicts or defaults (rule 25). Rule 28
  writes land in `docs/codebase-site/data/mechanism-matrix/MISO.js` only.
* Adds no `ScenarioConfig` field, no new tunable, no CI workflow.

## 7. Rule-28 commit shape

One commit carries: the `iso_configs.py` override, the `_CACHE_KEY_OPTIONAL_FIELDS`
comment + defaults-ledger line for `miso_clean_tier_rows`, the stale
"ARMING BLOCKED" prose wherever it is now false, and the MISO shard's cell
(`fc: "O"` → its solved verdict, with citation and the cache-epoch declaration).
`scripts/check_mechanism_matrix.py` runs before the push.
