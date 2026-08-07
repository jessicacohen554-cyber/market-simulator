# ARM-MISO — Arm `miso_rps_compliance_regions` as the MISO forecast default

**Lane:** governance/config (owner decision **D-26**, sitting Addendum **Y.4**, signed
2026-08-06). The D-2' pattern — a small arming lane that adds one
`ISOConfig.default_scenario_overrides` entry and its evidence trail, on the precedent set by
`entry_vre_capacity_revenue` (D-2', Addendum O).
**Measured basis:** FFR-7B-2 §3.1 (`docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md`),
registered pair `miso-2026-2030-ffr7b2-rpsk-{ctrl,armed}`.
**Head at lane start:** `origin/main` `c710d17e`. **Branch:** `claude/arm-miso-rps-regions-6rckbk`.
**No solve was run** — see §5.

## 0. Headline

* **`miso_rps_compliance_regions` is now the MISO forecast default**, armed via
  `ISOConfig.default_scenario_overrides` in `config/iso_configs.py::_miso_config`. The
  ScenarioConfig field default stays `False`; MISO's ISO-level override is what arms it, so
  rule 25 `[R-ISO-SCOPE]` holds by construction — no other ISO's config carries the key.
* **The backcast is untouched, and that is PROVEN BY TEST, not asserted in a comment**
  (`tests/unit/config/test_miso_rps_region_arming.py`, 13 assertions, all passing). The
  flag's forecast restriction is enforced at **consumption**, so this needed a test — §2.
* **The gate predicate was extracted** to `runner._rps_region_grain_active` — behaviour
  preserving, on the existing `_confirmed_exits_active` precedent — because the gate was
  inline inside the ~1,300-line `run_scenario_iso` and therefore untestable. §2.1.
* **Matrix re-stamped** `O → K` in the MISO forecast lane (rule 28b). §4.
* **`miso_clean_tier_rows` (Arm 3) stays UNARMED**, blocked on the open §45U composition
  (D-22 / X.2) — not this lane's decision. §6.

## 1. The change

`src/market_sim/config/iso_configs.py::_miso_config`:

```python
default_scenario_overrides={
    "entry_vre_capacity_revenue": True,
    "miso_rps_compliance_regions": True,
},
```

with a cited comment naming D-26 / Y.4, the FFR-7B-2 §3.1 measured basis (MI pins $30 every
year, IL from 2027, delivery-based MN/WI/MO correctly slack, control blind until 2029), the
rule-19 replacement semantics, the rule-25 scope, and the consumption-gate note.

The forecast lane reaches the arming through
`run_full_horizon.py → pipeline.api.run_scenario → runner.run_scenario_iso`, which applies
`default_scenario_overrides` to any field the caller left at its ScenarioConfig default. The
**D-2' caveat carries over verbatim**: because the override fires on value-equality with the
default, an explicit `--no-miso-rps-compliance-regions` (which sets `False`, the default) is
**re-armed** here and does **not** reach a gate-off control for MISO. Anyone building a
control arm must do it the way FFR-7B-2 did — before the arming, or by patching the ISOConfig.

## 2. The backcast-untouched proof

The prompt's condition — *"if the gate is mode-checked at consumption (not construction),
prove it with a test"* — **applies**: the gate is at consumption
(`runner.py`, formerly the inline `iso == "MISO" and config.mode == "forecast" and …`).
The override is applied *unconditionally* by `run_scenario_iso`, so a backcast-mode MISO
config carrying `miso_rps_compliance_regions=True` is a **reachable** state and must still
resolve the legacy ISO-wide row. It does.

**Three independent layers insulate the backcast, each with its own test:**

| # | Layer | Mechanism | Test |
|---|---|---|---|
| 1 | `rps_enabled` is `False` in every backcast by construction | the whole `if config.rps_enabled …` block is skipped — neither grain is built at all | `test_rps_is_disabled_in_every_backcast` |
| 2 | the calibration lane never applies `default_scenario_overrides` | `run_calibration_full.py`'s only mention of them is an argparse help string; the application lives solely in `runner.run_scenario_iso` + two forecast-side export tools | `test_backcast_builder_never_arms_the_flag` |
| 3 | the mode leg of the gate itself | `_rps_region_grain_active` requires `mode == "forecast"` | `test_backcast_miso_resolves_the_legacy_row_even_when_armed` |

**Layer 2 is load-bearing for cache identity, not just dispatch** — the finding worth
recording. `miso_rps_compliance_regions` is a `_CACHE_KEY_OPTIONAL_FIELDS` member registered
at `False`, so an armed backcast config hashes **distinctly** while solving **identically**
(the gate suppresses the grain). Measured on a 2024 MISO backcast:

```
backcast key as built (flag False) : bf9e6b3ac426dadd
same config with flag forced True  : bc1d15d723d2981b
```

That would silently orphan every MISO backcast keeper's cached results. The hazard is pinned
by `test_an_armed_backcast_would_move_the_cache_key`, so a future session cannot wire the
overrides into the calibration lane unnoticed. **As shipped, every MISO backcast keeper keys
exactly as before** (`test_backcast_key_is_byte_stable_across_the_arming`).

Rule 25 is re-checked at both ends: no non-MISO ISOConfig carries the key
(`test_no_other_iso_arms_it`), and a hand-armed non-MISO config is still refused at the gate
(`test_forecast_non_miso_never_builds_the_grain`).

### 2.1 The gate extraction

The gate was an inline `if` inside `run_scenario_iso`, a ~1,300-line function whose only
entry point is a full multi-year solve — untestable without one. It is now
`runner._rps_region_grain_active(config, iso)`, a module-level predicate with a docstring
(rule 11 `[R-DOCSTRING]`) documenting all three legs, called from the one site it came from.
This follows the **existing precedent in the same file**: `_confirmed_exits_active` is a
private module-level forecast-mode gate predicate imported directly by
`tests/unit/data/test_confirmed_retirements.py`. The change is behaviour-preserving — same
three conjuncts, same order, same short-circuit.

The stale call-site comment (`GATED miso_rps_compliance_regions (default OFF)`) was corrected:
the *field* default is still off, but MISO's ISOConfig now arms it.

## 3. Tests run — honest state

All run at branch HEAD with `.venv/bin/python -m pytest`. **Zero failures caused by this
lane.** One unrelated pre-existing failure is enumerated below, not absorbed.

| Suite | Result |
|---|---|
| `tests/unit/config/test_miso_rps_region_arming.py` (new) | **13 passed** |
| `tests/unit/model/test_dispatch.py::TestRpsComplianceRegionRows` + `test_rps.py` + `test_clean_tiers.py` | **33 passed** |
| `tests/unit/config/` (full) | **474 passed**, 18 subtests |
| `tests/unit/model/` + `tests/unit/policy/` (full) | **1261 passed**, 13 subtests, 1 pre-existing unrelated `ConstantInputWarning` in `test_reliability_floor.py` |
| `scripts/check_mechanism_matrix.py` | integrity OK; anchors OK (189 field + 44 row + 128 path); keeper stamps + §5.x headers match every shard |
| `ruff check` + `ruff format --check` on the three changed `.py` files | clean / already formatted |
| `pytest -k "runner or scenario_iso or forecast_mode or iso_config"` | 244 passed, **1 pre-existing failure** (below) |

### 3.1 The one pre-existing failure — enumerated, not absorbed

`tests/regression/test_soundness.py::TestEndToEnd::test_runner_produces_cached_results`
**FAILS, and fails identically on a clean tree.** Verified by `git stash push -u` back to
`origin/main` `c710d17e` and re-running the single test: same `RuntimeError`, same line.

```
RuntimeError: confirmed-retirements: clean partition for ERCOT is absent while
confirmed_exits_enabled is on in forecast mode. data/clean is derived and gitignored,
so a fresh checkout has no registry; refusing to silently degrade to the economic screen
```

It is an **environment** condition, not a code defect: `data/clean/` is derived and
gitignored, so a fresh container checkout has no `confirmed-retirements` partition and the
step-0 loader refuses to degrade silently (working as designed, W1-B B3). It concerns ERCOT
confirmed exits and touches nothing in this lane. The fix, if a session needs that test, is
the remediation the error itself prints:
`PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py`. **Not run here** — this
lane has no reason to materialise ERCOT's retirement registry.

The K=1 byte-identity contract is the pre-existing
`TestRpsComplianceRegionRows::test_k1_all_zones_reproduces_legacy_row_byte_identical` — it
proves the K=1/mask-all region build reproduces the legacy single row byte-identically
(matrix **and** bounds), with a masked build shown to differ so the identity is non-vacuous.
That is what makes "falls through to the legacy row" a complete statement of the backcast
behaviour.

## 4. Matrix re-stamp (rule 28b)

`docs/codebase-site/data/mechanism-matrix.js`, row `miso_rps_compliance_regions`:

* `fc: "...O.."` → `fc: "...K.."` (index 3 = MISO; `cells` — the backcast lane — stays
  `"......"`, since `rps_enabled` is `False` in every backcast).
* `def` updated: field default-OFF **but armed as the MISO forecast default** via
  `default_scenario_overrides`, gate named `runner._rps_region_grain_active`.
* `note`: the FFR-7B-2 `O` verdict is preserved as the historical record and the `O → K`
  transition appended with D-26, the no-new-solve statement, and the three-layer
  backcast-untouched proof incl. the cache-key hazard.
* `ev.C`: this handoff + D-26/Y.4 first, then the FFR-7B-2 measurement and the FFR-6B/FFR-7B
  design/charter chain.

## 5. No solve was run — and why that is correct

The prompt states the FFR-7B-2 registered pair **is** the evidence, and it is: a bounded
2026–2030 MISO T1-F pair, control `0723d2cc432fa346` vs armed `ff144cd25848e4d8`, solved
serially and registered to the forecast namespace as
`miso-2026-2030-ffr7b2-rpsk-{ctrl,armed}`. Arming changes **which value a config field
takes**, not what the armed configuration computes — the armed leg already exists, is
registered, and is exactly what a confirmation solve would reproduce. A re-solve would
consume ~62 min/leg and ~9.6 GB RSS to regenerate a committed artifact. **I did not run one
and do not believe one is needed.** Nothing in this lane touches the backcast, so rule 15's
dashboard-registration duty is not triggered by a new run; the existing forecast-namespace
registrations stand.

## 6. `miso_clean_tier_rows` stays UNARMED — and the Arm-3 registration is not an arming

Two statements the prompt asked be recorded explicitly:

1. **Arm 3 is not armed and this lane does not arm it.** `miso_clean_tier_rows` remains
   default-off with **no** `default_scenario_overrides` entry in any ISO
   (`test_clean_tier_rows_stays_unarmed_everywhere`). Its arming is blocked on the open
   **§45U-vs-clean-dual composition for nuclear** (owner D-22 / sitting Addendum X.2):
   §45U(b)(2)'s gross-receipts phase-down implies phase-down-then-add, not `max()`, while the
   retirement screen currently composes `max(max(eac, §45U), clean)` — the existing doctrine,
   provisional. That is an owner decision, **not this lane's**.
2. **The Arm-3 armed leg already on the dashboard is measurement evidence, not an arming.**
   `miso-2026-2030-ffr7b2-clean-armed` (key `587dc5b32ba71ceb`) is a registered probe leg
   showing the clean rows slack in every window year; a registered run is never a default.
   Its matrix cell stays `O` and was not touched by this lane.

### 6.1 One behaviour change worth flagging

Because the D-26 override is applied **before** the runner's Arm-3 dependency check, passing
`--miso-clean-tier-rows` **alone** on a MISO **forecast** run no longer raises the
`miso_clean_tier_rows requires miso_rps_compliance_regions` `ValueError` — the dependency is
now auto-satisfied. Verified empirically.

This is **not** a governance breach and does not arm Arm 3: the flag is still default-off and
still requires an explicit operator opt-in, which is exactly the act the block governs. The
error existed to catch a *wiring* mistake (Arm 3 riding machinery that isn't built), and for
MISO forecast runs that machinery is now always built, so the condition it guarded cannot
occur. The error still fires correctly everywhere it should — MISO backcast (overrides not
applied) and any non-MISO ISO. Flagged here rather than left to be discovered.

## 7. Files changed

| File | Change |
|---|---|
| `src/market_sim/config/iso_configs.py` | the D-26 override entry + cited comment |
| `src/market_sim/runner.py` | `_rps_region_grain_active` extracted (behaviour-preserving); call site + stale comment updated |
| `tests/unit/config/test_miso_rps_region_arming.py` | **new** — the 13-assertion backcast-untouched proof |
| `docs/codebase-site/data/mechanism-matrix.js` | MISO forecast cell `O → K` + def/note/ev |
| `docs/handoffs/arm-miso-rps-regions-2026-08-07.md` | this document |

## 8. Open items handed forward

* **§45U-vs-clean-dual composition** (D-22 / X.2) — blocks Arm 3's arming. Owner decision.
* **The MN clean-tier mask** — FFR-7B-2 §3.2's one stated divergence from FFR-6B §6.2
  (host-zone-only vs delivery-based eligibility). Data, one line in
  `MISO_CLEAN_TIER_REGIONS`; needs an owner adjudication of §216B.1691's carbon-free tier.
* **A margin-decided entry window** is where the per-zone REC credit will actually move MW.
  FFR-7B-2's 2026–2030 window had only an adequacy-backstop VRE build, so the corrected
  credit moved zero MW there. That measurement needs a full-horizon authorization and is
  chartered to nobody yet.
