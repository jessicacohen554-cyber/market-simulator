# OVERRIDE-FIX — making an ISO-armed flag turn-off-able at the `apply_iso_scenario_defaults` seam

**Lane.** OVERRIDE-FIX `[OPUS]`, branch `claude/iso-armed-flags-turnoff-e425y7`,
developed off `origin/main` **`016b659`** and **rebased onto `5b05f84`** before
pushing (main advanced mid-lane; see the push note in §6 — that rebase is also
what unblocked the push). Dispatch: sitting §0ap-1 / Addendum AQ.2,
upgraded from blocker to **live two-ISO exposure remediation** (MISO D-29 +
ERCOT D-30).

**Scope.** Config-only. No solve, no dashboard registration, no new mechanism,
no keeper / marker / rubric touch, no matrix cell change (a seam repair is not a
mechanism test; `scripts/check_mechanism_matrix.py` run anyway, exit 0, anchor
warnings unchanged at 236 = the pre-existing count on `main`).

**Source of record for the defect and its resolution:**
`docs/handoffs/FINDING-ffr-9c-iso-override-precedence-2026-08-12.md` — its
landed text plus the **RESOLUTION ADDENDUM** this lane appended. That addendum is
the authoritative narrative; this file is the execution record.

---

## 1. The defect, in one line

`apply_iso_scenario_defaults` inferred "the caller left this field unset" by
comparing the caller's value to the `ScenarioConfig` default. Every promotable
flag defaults `False`/`None`, so **the OFF value was exactly the value that
could not be requested** — an explicit `entry_pipeline_aware_signal=False` was
silently re-armed, and a control arm for any ISO-armed flag was inexpressible
through the config path, in ERCOT (five stage-B flags) and MISO alike.

## 2. What landed

**FINDING §4 remedy 2** — track the fields the caller actually passed and
consult that record at the seam.

| File | Change |
|---|---|
| `src/market_sim/config/scenarios.py` | Wraps the generated dataclass `__init__` (post-decoration) to record passed field names on the **non-field** attribute `_explicitly_set_fields`; adds the public reader `explicitly_set_fields(config)`; `with_overrides` now carries the record forward as a **union**; `as_zero_forcing_ablation` routes through `with_overrides`. |
| `src/market_sim/config/iso_configs.py` | `apply_iso_scenario_defaults` consults the record; docstring + the ERCOT `default_scenario_overrides` precedence comment restated. |
| `src/market_sim/config/scenario_resolvers.py` | `resolve_policy_bundle` uses `with_overrides` (it runs **before** the seam in `run_scenario_iso`). |
| `src/market_sim/runner.py` | The weather-year rebind and the outage-overlay `fleet_config` use `with_overrides`. |
| `scripts/run_full_horizon.py` | `reference_config`'s two MISO row-family params become `None`-sentinels; both CLI flags get `default=None`. **This is the one real call-site dependency** — see §3. |
| `tests/unit/config/test_iso_override_precedence.py` | **NEW** — 56 tests pinning the fixed seam. |
| `tests/unit/config/test_ercot_stageb_arming.py` | Docstring only: its "KNOWN LIVE EXPOSURE" note marked CLOSED. **No assertion touched.** |

### The design constraint that shaped it

The tracking record is a **non-field instance attribute**, so it cannot reach
`asdict()` → `cache_key()`. A tracking *field* would have entered every digest,
orphaned every on-disk bundle and moved the global pin. Consequently **rule 28's
cache-key ledger duty does not arise** — no `_CACHE_KEY_OPTIONAL_FIELDS` or
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` entry was added, and none was needed.
Pickle identity is unmoved (`ScenarioConfig` still physically defined at
`market_sim.config.scenarios`).

### The copy-path trap (worth knowing before touching this seam again)

On Python 3.11 `dataclasses.replace(cfg, …)` re-invokes `__init__` with **every**
field — indistinguishable from a caller who set everything. A naive record would
mark a whole config "explicitly set" after any `replace`, and then **no ISO
default would ever apply again** — a worse failure than the original, sitting
right in the production path. Two defences:

1. **`with_overrides` is the tracked copy path** (union semantics); the `src/`
   sites that used bare `replace` now route through it.
2. **All-fields-supplied records `None` = provenance unknown**, and unknown
   **falls back to the pre-fix value comparison**. An untracked copy therefore
   degrades to *today's behaviour*, never to a stripped posture.

The seam's predicate keeps both clauses — not-in-record **and** still-at-default
— which makes the change a **strict narrowing**: it can only apply *fewer* ISO
defaults than before, never more.

## 3. The call-site grep — and why the static one wasn't enough

The dispatch asked for a grep of call sites passing an overridden field at its
default value, "expected: none". **Two scans were run, and the prediction was
wrong.**

**Static (AST over all 2,325 `.py` files):** 16 hits, **all benign** — `dict()` /
`SimpleNamespace()` / `_Cfg()` fakes that are not `ScenarioConfig` at all
(`test_reserve_config.py`, `test_pipeline_kwargs.py`), and `with_overrides` /
`replace` calls on an **already-resolved** config followed only by `cache_key()`
or a direct assertion (`_arm3arm_cache_epoch.py`,
`test_caiso_keeper_defaults.py`, `test_miso_rps_region_arming.py`,
`test_negative_renewable_offers.py`). None flows back through the seam; all
their modules pass unchanged.

**Dynamic differential (the one that mattered):** resolve all 15 ISO-overridden
fields + the `cache_key`, for **6 entry points × 6 ISOs**, on clean `main` and on
the fix, and diff. It caught what a grep structurally cannot see:

> `scripts/run_full_horizon.py::reference_config` declared
> `miso_rps_compliance_regions: bool = False` / `miso_clean_tier_rows: bool = False`
> and forwarded both into `ScenarioConfig` **unconditionally**. The literal is a
> *forwarded function parameter*, not a literal at the construction site.
> Post-fix it would have **won**, silently un-arming owner decisions **D-26** and
> **D-29** in exactly the T1-F legs that runner launches. The CLI compounded it:
> `action="store_true"` yields an explicit `False` when the flag is absent.

This is the **FFR-3A step-0 hazard in mirror image** — and that file already
carries a standing comment predicting it ("*a mirrored literal here would have
silently overridden both flips*"). Repaired with that file's own idiom:
`bool | None = None`, folded into the `arms` dict filtered by `if v is not None`,
plus `default=None` on both CLI flags. `_arm3arm_cache_epoch.py` **failed on the
intermediate state** and returns its declared MISO poles byte-identically after
the repair — it is the instrument that caught this.

**Standing lesson: for this defect class the grep IS the dynamic differential.**
A future promotion into `default_scenario_overrides` should re-run it (§5).

## 4. One deliberate new raise

Turning off **only** `capacity_screen_unified_lookahead` now raises: the ISO
override still arms `capacity_screen_scarcity_restoration` (genuinely unset), and
`__post_init__` refuses restoration-without-lookahead (FFR-8A). Pre-fix that
posture was unreachable. The raise is the **loud** half of the remedy — the
caller is told the combination is untested instead of silently receiving the
posture it asked to turn off. **The ERCOT screen-pair control arm is both-off**,
as the dispatch stated. Pinned by
`test_turning_off_half_the_screen_pair_RAISES`.

## 5. Reproducing the differential

```python
# for each entry point x ISO: apply_iso_scenario_defaults(build(iso), iso)
# then record {field: value} for every field in every ISO's
# default_scenario_overrides, plus resolved.cache_key(); diff vs clean main.
ENTRY_POINTS = {
    "bare":                   lambda iso: ScenarioConfig(iso=iso),
    "bare_forecast":          lambda iso: ScenarioConfig(iso=iso, mode="forecast"),
    "reference_config":       lambda iso: rfh.reference_config(iso=iso, start_year=2031, end_year=2032, cmc=False),
    "reference_config_golden":lambda iso: rfh.reference_config(iso=iso, start_year=2031, end_year=2032, cmc=False, golden_posture=True),
    "backcast_config":        lambda iso: backcast_config(2024, iso, 8760, 3.0),
    "calibration_config":     lambda iso: rc._calibration_config(2024, iso, 8760, 3.0),
}
```

Result: **identical**, every entry point × ISO, before vs after.

## 6. Acceptance — all green

| # | Check | Result |
|---|---|---|
| 1 | Explicit-off wins (`entry_pipeline_aware_signal`, `smr_available_year=None`, `vre_procurement_additions_enabled`, `scarcity_price_overlay` on ERCOT; `miso_clean_tier_rows` on MISO; screen pair both-off) | **PASS** — repro snippet prints `False` |
| 2 | `scripts/probes/_ffr9c_stageb_cache_epoch.py` — three reads | **PASS**, exit 0, unchanged |
| 2b | `scripts/probes/_arm3arm_cache_epoch.py` (MISO, not dispatched but load-bearing) | **PASS**, exit 0 |
| 3 | `test_persisted_identity.py` + `test_cache_key_default_flip_guard.py` + `test_ercot_stageb_arming.py` | **32 passed**, no assertion changed |
| 4 | `scripts/check_cache_key_registration.py` | **exit 0** (714 fields, 167 registered) |
| 5 | NEW `test_iso_override_precedence.py` | **56 passed, 11 skipped** (skips = bool fields in the "non-default value" leg: a bool has only two values, both already taken) |
| — | `ruff check src/ scripts/ tests/…` | clean |
| — | `scripts/check_mechanism_matrix.py` | exit 0, warnings unchanged vs `main` |

**Cache-key reads, all unmoved:** global pin `603c2498bf71d21d`; ERCOT armed pole
`8d9ef77edb3e44cb`; ERCOT pre-arm pole `062d440558103f81`; MISO forecast poles
`cd2403cc031515db` / `9337e00504e1e72a`.

**Full sweep** (`tests/unit/` + `tests/iso/`, run twice independently):
**4,637 passed, 7 failed** — all 7 verified pre-existing by re-running them on the
parent commit (see below).

### CI verdict — the "Pinned default cache key" check

`.github/workflows/ci.yml` triggers on **`pull_request` only** (no `push:` key),
so a branch push produces **zero** workflow runs and the check cannot report a
verdict until a PR exists. No PR was opened — this lane was not asked for one.
Every gating job was therefore run locally with **the exact command CI runs**:

| CI job | Command | Result |
|---|---|---|
| Pinned default cache key | `pytest -q tests/regression/test_persisted_identity.py tests/unit/config/test_cache_key_default_flip_guard.py` | **22 passed**, exit 0 |
| Ruff lint + format | `ruff check .` / `ruff format --check .` | clean; 1,281 files already formatted |
| cache-key-guard | `check_cache_key_registration.py --base <main>` | exit 0 — "no new ScenarioConfig fields in this PR" |
| mechanism-matrix-guard | `check_mechanism_matrix.py --base <main>` | exit 0; anchor warnings self-labelled "(pre-existing, not this PR)" |
| Rule-22 quarantine gates | `audit_keepers.py --check`, `legitimacy_diagnostics.py --keepers --no-d2-recompute`, `check_registry_payload_parity.py` | all exit 0 |

Opening a PR is the only way to obtain the check's own verdict; the local runs
above are the same commands on the same commit.

### Push note — HTTP 500/408 was a STALE BASE, not pack size

Worth recording, because the symptom points the wrong way. `git push` failed
**nine consecutive times** with `RPC failed; HTTP 500` (and once `408`), through a
healthy proxy (`__agentproxy/status`: `recentRelayFailures: []`), on a pack of
**20 objects / ~3 KB**. `--no-thin`, `http.version=HTTP/1.1`,
`http.postBuffer=500M` and exponential-backoff retries all failed identically.
The cause was that `origin/main` had advanced (`016b659` → `5b05f84`) while the
lane worked, leaving the branch based on a superseded tip. `git fetch origin main`
+ `git rebase origin/main` and the **first** push succeeded. This is the Git &
Pushing §1 rule ("start fresh on main — this is what keeps a pack small") showing
up as a *server 500* rather than as a size error. **Diagnose a repeated 500 by
re-checking the base before touching transport settings.**

Rule-27 verification was done as a real round-trip: the branch was re-fetched
into an independent 584 KB blobless clone and every file compared by line count
and SHA-256. All nine byte-identical — `scenarios.py` 13,359 lines,
`iso_configs.py` 1,599, `runner.py` 4,046, `run_full_horizon.py` 981.

### Pre-existing failures, verified on clean `main` by stash-and-rerun — NOT this lane's

- `tests/unit/config/test_configs_yaml_roundtrip.py::…[data-profiles.yaml]` —
  `configs/data-profiles.yaml` matches no loader route (from the fast-clone
  data-profile work). Fails identically on `main`.
- `tests/iso/ercot/test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion` (2 tests)
  and `tests/unit/results/test_export.py` + `test_cache.py::TestConfigSidecar` (5 tests) —
  all 7 fail identically on the parent commit (`retirement_rule='pipeline' requires a
  simulation year`, and the missing CLEAN partition below).
- `tests/regression/test_soundness.py::TestEndToEnd` (6 tests) — `data/clean` is
  derived and gitignored and this session runs the **`code` data profile**, so
  the confirmed-retirements CLEAN partition is absent. Fails identically on
  `main`.

## 7. Out of scope, deliberately untouched

- `full_forward_climatology_years` empty-window fail-closed — **same defect
  class, separate dispatch** (FH-5 §7.1). Not touched.
- Anything that solves; any keeper, marker, rubric or dashboard artifact.
- The 236 pre-existing `mechanism-matrix` anchor-drift warnings (a `--fix-anchors`
  sweep is its own change and would collide with parallel ISO lanes).

## 8. Follow-ups worth a future lane

1. **A guard against the mirrored-literal shape.** `reference_config` is now
   correct, but nothing *prevents* the next runner parameter from mirroring a
   promotable field's default and forwarding it unconditionally. A CI check —
   "no function parameter whose default equals the `ScenarioConfig` default of a
   field in any `default_scenario_overrides` may be forwarded unconditionally" —
   would make §3's lesson mechanical instead of remembered.
2. **A negative CLI form.** The seam can now express an off arm, but
   `run_full_horizon.py` exposes no `--no-miso-clean-tier-rows` /
   `--no-entry-pipeline-aware-signal`. Until it does, an ERCOT or MISO control
   arm is reachable through the **config path only**. Cheap to add
   (`BooleanOptionalAction`), but it changes a runner CLI surface, so it is a
   deliberate follow-up rather than a silent widening here.
