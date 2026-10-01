# FF-2A-posture — `entry_lookahead_reprice` default-ON (owner-approved 2026-07-18)

_Forecast Finalization Program, Wave-2 lane **FF-2A-posture** (plan §2.1a item e).
Opus. One `ScenarioConfig` default flip + the owner-decision record, applied
exactly as FF-1F applied DC=mid / derate=ON: a recorded default flip with a
backcast byte-identity guard, **not** a re-tuning (rules 1/13/14/22/23/24/27;
§7 binds). Report-only findings; no backcast or hindcast bundle moves._

**One line.** The owner approved the FF-2A item-4 posture: `entry_lookahead_reprice`
**`False → True`** — the zero-DOF, G-30-validated entry-screen lookahead reprice
(the developer's pro-forma: re-price the entering year's known net load against
the current fleet with the published ORDC curve, every input an existing model
quantity). Forecast/screen-only; backcast keepers **and** existing hindcast legs
are byte-identical (backcast `cache_key` unchanged; the harness passes the flag
explicitly). No new tuned value anywhere.

---

## 1. What changed

| File | Change |
|---|---|
| `config/scenarios.py` (field default) | `entry_lookahead_reprice` default `False` → `True`; comment records owner-approved default-ON (FF-2A 2026-07-18), the G-30 validation, and the forecast-only/byte-identity story. Field stays on-registry (`TIER_TAGS` row + the runner read site unchanged). |
| `config/scenarios.py` (`__post_init__`) | coerce `entry_lookahead_reprice=False` whenever `mode=="backcast"` — belt-and-braces with the runner's `mode=="forecast"` read gate, keeping every calibration/keeper `cache_key` + `run_config.json` byte-identical after the flip (the exact FF-1F `datacenter_load_path` coercion pattern; NOT triggered in hindcast, which is `mode=="forecast"`). |
| `docs/forecast-development-plan-2026-07.md §2.1a` | posture-defaults table row **e** + the FF-2A-posture byte-identity attestation. |
| `docs/handoffs/ff-2a-posture-entry-lookahead-2026-07-18.md` | this findings note. |

**Scope discipline.** Only `entry_lookahead_reprice` was flipped. The three
sibling FF-2A entry gates (`entry_vre_capacity_revenue`, `entry_rate_limits`,
`entry_commissioning_lag`) stay **default-off** — their arming decision is the
owner's per-run choice (FF-2A §4.2), untouched here. No band widened, no derive
script re-run, no residual-fitted value (rules 1/13/14/23).

## 2. Why default-ON — the evidence the owner approved (FF-2A §4.1)

The lookahead is a **pure price-signal change with zero fitted parameters**
(rule 13 admissible: it regenerates from forward drivers in any year). G-30
single-term isolation (`docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md`,
its ablation twin differing **only** in this flag) measured that arming it:

- unlocked the first **non-zero ERCOT solar entry** (0 → 4 GW),
- halted the **gas_st over-retirement** (8.83 → 1.87 GW), and
- carried the intended **negative feedback** (the 2024→2025 pro-forma weakens as
  2024's entry re-fills the stack) — a self-correcting developer pro-forma, not a
  tuned adder.

It is the screen-side half of the pro-forma a real developer runs. The honest
counter-evidence stands and is unchanged by this flip: the lookahead alone does
**not** close BLK-8's ERCOT solar term-(a) residual (FF-1A ran it ON and still
delivered solar = 0 at the production footing), and its pro-forma *level* is not
independently validated. Default-ON is a **posture** decision (make the developer
pro-forma the production default), not a claim that it closes the entry gap; the
T1 gate battery re-baselines against it.

## 3. Byte-identity — backcast keepers and hindcast legs are unaffected

`entry_lookahead_reprice` is **forecast/screen-only**. It feeds ONLY the capacity
screens (retirement / new entry / storage) via `prior_results.price_signal`; it
never touches dispatch, results, or persisted prices, and a **backcast runs no
capacity evolution at all**.

- **Runner read gate (mechanism no-op).** The single consumption site
  (`runner.py`, the `_lookahead_reprice_signal` call) is guarded by
  `... and config.mode == "forecast" and ...`; in `mode=="backcast"` the branch is
  never entered and `price_signal` passes `econ_prices` through unchanged. The
  field is genuinely not read on the backcast path.
- **`__post_init__` coercion (byte-identity).** `entry_lookahead_reprice` is
  **not** in `_CACHE_KEY_OPTIONAL_FIELDS`, so its value always enters the
  `cache_key`. Left to inherit the flipped default, a backcast config would record
  `True` and its key would shift. `__post_init__` therefore coerces it `False`
  whenever `mode=="backcast"` (the exact FF-1F `datacenter_load_path` pattern), so
  the keeper key + `run_config.json` keep their pre-flip bytes. The coercion
  catches **every** backcast config — those built via `backcast_config()` and any
  hand-built `ScenarioConfig(mode="backcast", …)` — a strictly stronger guarantee
  than a builder-local pin. It is **not** triggered in hindcast (`mode=="forecast"`).
- **Hindcast harness (explicit pass-through).** `scripts/run_capacity_hindcast.py`
  `build_config()` passes `entry_lookahead_reprice=<harness arg>` where the
  harness parameter defaults to `False`; existing hindcast legs therefore build
  the flag **explicitly** `False` and are invisible to the model-default flip.
  Probe legs that armed it (`--entry-lookahead-reprice`) already ran `True`.

**Empirical proof (measured on the FF-2A-posture branch off `origin/main`):**

| config | `entry_lookahead_reprice` | `cache_key` pre-flip | `cache_key` post-flip |
|---|---|---|---|
| backcast keeper — ERCOT 2024 (`backcast_config`) | `False` (coerced) | `c44c3d9b7549de73` | **`c44c3d9b7549de73`** ✓ identical |
| backcast keeper — all six ISOs (`backcast_config`) | `False` (coerced) | — | CAISO `269871a5…` / PJM `05f545cf…` / MISO `86fa3f27…` / NYISO `9c5abaf7…` / NEISO `2d028b69…` (all coerced `False`, byte-stable) |
| raw `ScenarioConfig(mode="backcast")` (no builder) | `False` (coerced) | — | coercion catches it too — strictly stronger than a builder pin |
| forecast default (bare `ScenarioConfig`) | `True` (new default) | `cdf095573872a069` | `1d4a8acfa187a505` (shifts — **intended**: the golden posture is a distinct scenario) |
| hindcast default arm (`build_config`, no `--entry-lookahead-reprice`) | `False` (explicit) | — | flip invisible ✓ |

The backcast key is byte-stable → existing cached backcast solves still hit and
no keeper bundle's identity changes. **No keeper or hindcast bundle was
re-solved.** The 57 config/cache + 9 FF-2A-entry/golden-fixture unit tests pass
with the flip applied.

## 4. T0 invariant smoke — ERCOT 2026–2028, `entry_lookahead_reprice` OFF vs ON

One short ERCOT forecast leg, solved twice, differing in **exactly one config
field** — measured pre-solve: `config_diff = {entry_lookahead_reprice:
[false, true]}`, nothing else. Footing = the FF-1B/G-30 measurement footing
(`scarcity_pricing_enabled=True`; ERCOT's `scarcity_price_overlay` auto-on via
`default_scenario_overrides`) so the lookahead's ORDC pro-forma can act and the
intended screen-side effect is visible. Both legs are otherwise pure defaults —
no tuned value anywhere (rules 1/13/14).

| leg (`entry_lookahead_reprice`) | cache_key | FAIL | WARN | invariant detail |
|---|---|--:|--:|---|
| **OFF** (`False`) | `33fed8f74c66946b` | **1** | 2 | I3 FAIL (2027 unserved/slack 0.03% of load), I12 WARN (2027 RM 13.4% < 13.8% floor), I14 WARN (2027 price sanity) |
| **ON** (`True`, new default) | `c30cb4ed1e21235e` | **0** | 1 | I12 WARN (2028 RM 30.3% > 28.7% ceiling) |

**Invariant status delta (OFF → ON), attributable entirely to the flag:**

- **I3 `FAIL → PASS`** — the lookahead **closes** the 2027 unserved-energy slack.
  This is the mechanism doing exactly what G-30 validated: the entering-year
  pro-forma sees the 2027 tightness the in-year LP misses, so the screens unlock
  earlier/more entry and the gap does not materialise as slack.
- **I14 `WARN → PASS`** — the 2027 price-sanity WARN clears with the relieved gap.
- **I12** stays a single WARN but **flips sign**: OFF is a 2027 reserve-margin
  **deficit** (13.4% < floor — the under-build), ON is a 2028 **surplus** (30.3% >
  ceiling — the intended earlier entry building ahead of need in this 3-year
  window). A benign upper-band overshoot, not a regression; it is the honest
  earlier-entry consequence (rules 1/13: keep the accurate posture, the entry
  lane FF-2A/2B owns the sizing).

**Verdict.** Invariants are **green on the ON (new-default) leg** (0 FAIL) and
strictly **improve** vs the OFF baseline (FAIL 1 → 0, WARN 2 → 1); the ONLY config
delta is `entry_lookahead_reprice`. The T0 gate (I1–I14 no-FAIL on the feature
probe, plan §2.1) is met, and the flip demonstrably relieves the ERCOT 2027
entry-gap it was approved to help — consistent with the G-30 isolation. (Artifacts:
`scratchpad/ff2a_smoke_out/{off,on,summary}.json`; report-only, not registered.)

## 5. Attestation

- **Rules:** forecast-only posture (rule 22 — no backcast/keeper touched, no
  quarantined-year solve; the smoke is 2026–2028 forecast-mode, unrestricted per
  plan §2.3). No off-registry knobs (rule 24 — `entry_lookahead_reprice` is a
  `ScenarioConfig` field in `run_config.json`). Zero new DOF (rule 13 — every
  lookahead input is an existing model quantity; nothing residual-fitted, rules
  1/14/23). One mechanism per phenomenon (rule 19 — the lookahead is the screen's
  own price signal, not a stacked floor).
- **Model:** Opus (rule 27 — `src/market_sim/` + `scenarios.py` edits).
- **Push (rule 27):** fresh branch off latest `origin/main`; pushed via
  `mcp__github__push_files`; `scenarios.py` (≥300 lines) blob-verified after the
  push touching it.

_Produced 2026-07-18 (FF-2A-posture, Opus)._
