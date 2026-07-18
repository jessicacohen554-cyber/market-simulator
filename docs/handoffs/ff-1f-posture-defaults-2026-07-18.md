# FF-1F — Owner-decided forecast posture defaults (DC=mid, correlated derate ON)

_Forecast Finalization Program, Wave-1 lane **FF-1F** (plan §2.1a, §6). Opus.
Two `ScenarioConfig` default flips + the owner-decision record. Forecast-only
posture change: backcast keepers proven byte-identical, no keeper re-solve
(rules 5/13/22/23/27; §7 binds)._

**One line.** The owner fixed the default forecast posture:
`datacenter_load_path` **off → mid** (model the published DC boom as a flat,
energy-invariant block — FF-1C §7) and `correlated_forced_outage` **False →
True** (the measured Uri/Elliott/Heather cold-event derate — FF-1B §3). Both are
forecast-only; backcast keepers are byte-identical (DC coerced `off` in
backcast/hindcast, derate a mechanism-level no-op there), proven by an unchanged
backcast `cache_key`. The full owner-decision set (incl. two later-lane items) is
recorded in plan §2.1a.

---

## 1. What changed

| File | Change |
|---|---|
| `config/scenarios.py:190` | `datacenter_load_path` default `"off"` → `"mid"`; comment cites FF-1F/FF-1C. |
| `config/scenarios.py:1521` | `correlated_forced_outage` default `False` → `True`; comment cites FF-1F/FF-1B, records the ORDC-sigma seam holding with the flag ON. |
| `config/scenarios.py` `__post_init__` | The DC backcast guard is now a **coercion**: `mode=="backcast" or hindcast` forces `datacenter_load_path="off"` (was: hard-raise on non-off backcast). Since the default is now the forecast posture `"mid"`, coercion — not a raise — keeps every backcast/hindcast byte-identical without per-site boilerplate; the label check still raises, and the standalone `data.datacenter.validate_datacenter_config` still hard-errors on a mutated/bypassed non-off backcast. |
| `pipeline/backcast_config.py` | `backcast_config()` now pins `correlated_forced_outage=False` (belt-and-braces with the mechanism's own mode gate; keeps the calibration/keeper `cache_key` + `run_config.json` byte-identical after the flip). |
| `tests/test_datacenter.py`, `tests/test_runner.py`, `tests/test_correlated_outage.py` | Updated the default-value / backcast-guard assertions to the new posture; added coverage: hindcast DC coercion, default-ON derate forms a derate, flag-OFF no-op. |
| `docs/parameter-citations.md`, `frontend/data/parameters.json` | Regenerated locally (`generate_parameter_registry.py` "value-refreshed 2": `off→mid`, `False→True`; no other row). **Derived + CI-ungated + 1.5 MB — not committed** (regenerate on demand); the substantive citations live in the `scenarios.py` docstrings + this doc + plan §2.1a. |
| `docs/forecast-development-plan-2026-07.md §2.1a` | The owner-decision record (this session). |

**Scope discipline (task step 3):** only the two knobs above were flipped.
`neiso_gas_coldsnap_derate` and every other availability knob are untouched.

## 2. Byte-identity — backcast keepers are unaffected (task steps 1, 2)

Both knobs are **forecast-only**; a backcast keeper carries the actual events
through the measured CAMPD outage overlays (rule 13) and pins measured load, so
neither knob may change a scored backcast.

- **`datacenter_load_path`:** `__post_init__` coerces it to `"off"` whenever
  `mode=="backcast"` or `hindcast` is set. A backcast config therefore holds the
  *same* `"off"` value it held under the legacy default — dispatch and config
  identical. `add_datacenter_block` is a no-op at `"off"`.
- **`correlated_forced_outage`:** `apply_correlated_outage_derate` is a hard
  no-op in backcast — it returns immediately on `mode != "forecast"` AND on
  `outage_source == "historic"` (data/outages.py). Availability is untouched, so
  the LP, its duals, and every downstream result are identical. `backcast_config`
  additionally pins the flag `False`.

**Empirical proof (cache_key, computed old-vs-new via `git stash`):**

| config | field values (new) | `cache_key` old | `cache_key` new |
|---|---|---|---|
| backcast (ERCOT 2024, `backcast_config`) | DC `off`, derate `False` | `cb8082905cc329db` | **`cb8082905cc329db`** ✓ identical |
| forecast (bare `ScenarioConfig`) | DC `mid`, derate `True` | `0413e6076b8e7c97` | `06277cf676cb2e4b` (shifts — intended: the golden posture is a distinct scenario) |

The backcast key is byte-stable → existing cached backcast solves still hit and
no keeper bundle's identity changes. **No keeper was re-solved.** The hindcast
validation legs WILL shift when re-solved with the derate armed (they run
`mode="forecast"`); that is an expected validation-lane consequence (FF-1A/2A),
documented here, not executed.

> **Update 2026-07-18 (code landed, rebased onto current main).** This doc + the
> FF-1F tests merged first (PRs #2468/#2476/#2480), so the two `scenarios.py`
> flips + the `backcast_config` pin were applied in a follow-up commit rebased
> onto the latest `origin/main` (which had gained the FF-2A entry-stack fields).
> The hashes above were measured on the pre-FF-2A base; **re-measured on the
> current main base the backcast `cache_key` is `0aca0164b861d62d` — unchanged
> old-vs-new** (the flip never touches it), and the forecast key shifts
> `c9bf456fde28558d` → `f062591032a72f65`. The byte-identity claim holds
> identically. The 50 FF-1F dispatch/config unit tests pass with the flips applied.

### 2.1 The FF-1B ORDC double-count seam holds with the flag ON

The derate injects **only** a deterministic reduction of the *mean* availability
the ORDC point reserve reads (`scarcity.reserve_headroom` → `pmax × avail`); the
LOLP convolution's `sigma` keeps carrying the stochastic reserve-error spread.
`correlated_outage_sigma_scale` stays `1.0` (its `__post_init__` gate still
rejects a non-1.0 value — verified with the derate now default-ON: the guard
condition `sigma != 1.0 and not derate` is unaffected because the derate is on),
so no forced-outage variance term is double-counted (FF-1B §3 / charter D.6).

## 3. T0 smoke — NEISO + ERCOT 2026-2028 (task step 4)

### 3.1 DC=mid reshapes load to the FF-1C anchors (analytic, `_scale_demand → add_datacenter_block`)

| ISO/yr | off peak GW | mid peak GW | Δpeak | off TWh | mid TWh | ΔE | FF-1C anchor (peak/TWh) |
|---|--:|--:|--:|--:|--:|--:|--:|
| ERCOT 2026 | 100.1 | 93.7 | −6.4% | 544.6 | 544.6 | 0.0% | 100.1 / 544.6 |
| ERCOT 2028 | 117.8 | 105.0 | −10.9% | 641.1 | 641.1 | 0.0% | 117.8 / 641.1 |
| NEISO 2026 | 21.5 | 21.5 | 0.0% | 106.5 | 106.5 | 0.0% | 21.5 / 106.5 |
| NEISO 2028 | 22.1 | 22.1 | 0.0% | 109.3 | 109.3 | 0.0% | 22.1 / 109.3 |

The refreshed growth rates put the **level** on the FF-1C anchors exactly
(off-peak = anchor). DC=mid is **energy-invariant** (ΔE = 0 — the FF-1C §5
relocation) and **flattens ERCOT's peak** (−6 to −11%, FF-1C §7: ~120 vs ~139 GW
by 2030). NEISO ships an empty DC table (`{}`, FF-1C §4 — no material source), so
its peak is unchanged there — correct, not an omission.

### 3.2 The derate forms in-year scarcity (solved, before/after)

ERCOT 2026-2028 forecast, DC=mid, ORDC overlay on (the FF-1B measurement footing:
`scarcity_pricing_enabled=True`, ERCOT's `scarcity_price_overlay` auto-on), derate
OFF vs ON — the only delta is `correlated_forced_outage`:

| year | derate **OFF** (max $ / hrs≥$2000 / RM) | derate **ON** (max $ / hrs≥$2000 / RM) |
|---|---|---|
| 2026 | $45 / 0 / 14.6% | $45 / 0 / 14.6% |
| 2027 | **$45 / 0** / 13.4% | **$5,000 / 49** / 13.4% |
| 2028 | $5,000 / 21 / 10.7% | $110 / 0 / 17.6% |

- **The derate forms the 2027 in-year scarcity** (max $5,000 = ORDC VOLL, 49 h ≥
  $2000) that the control never prints ($45, 0 h). Magnitude matches FF-1B's
  Heather validation (real event $3-5k RT). This is the whole point of the flip —
  default-off, the forecast ORDC prints $0 through a Uri/Heather-scale event (the
  G-31 finding).
- **The 2028 reversal is the capacity-evolution feedback, not noise:** the
  derate-ON leg's 2027 scarcity feeds the entry screen → earlier entry → 2028 RM
  17.6% and no scarcity; the derate-OFF leg sees no 2027 signal, under-builds, and
  2028 (RM 10.7%) is the tight year that slacks instead. Early honest scarcity →
  earlier honest entry.

### 3.3 Invariants — no new structural defect from the posture

| leg | FAIL | WARN | reading |
|---|---|---|---|
| ERCOT derate OFF (DC=mid, scarcity on) | **0** | I12 | clean |
| ERCOT derate ON (DC=mid, scarcity on) | I3 (2027 slack 0.03%) | I12, I14 | the derate surfaces the known ERCOT entry gap as scarcity |
| NEISO (DC=mid, derate no-op) | I4 (2028 coal 54 MW), I7 (2026 firm 27171<28797) | I12 (RM 9.2%) | **byte-identical to FF-1C §6.2** |

- **NEISO is a posture no-op:** I4/I7/I12 reproduce FF-1C §6.2's numbers to the MW
  (empty DC table, no ERCOT curve — the flip cannot touch NEISO). The pre-existing
  base-year adequacy FAIL (plan §1.2 item 5) is unchanged.
- **ERCOT's I3/I12/I14 are the FF-1C §6.2 entry-stack under-build, not the flip**
  (rules 1/13: keep the accurate posture, the entry lane FF-2A/2B owns the fix).
  The derate-OFF ERCOT leg is FAIL-free; the derate-ON leg's lone I3 slack is the
  derate correctly pricing the entry gap as a Heather-scale shortage.
- **DC=mid materially RELIEVES the reserve margin** the audit flagged: ERCOT RM
  14.6 / 13.4 / 17.6% (2026-28) vs FF-1C's DC=off 7.3 / 10.7 / 5.5% (all < the
  13.8% band). Flattening the DC peak lifts two of three years into band — a
  structural bonus of the `mid` posture, exactly the peaker-over-build relief
  FF-1C §7 predicted.

## 4. Owner-decision set (recorded in plan §2.1a)

| # | Decision | Value | Where |
|---|---|---|---|
| a | Capacity-market clearing | ON for PJM/MISO/NYISO/NEISO/CAISO (all but ERCOT) | per-ISO by readiness in **FF-2C** (owner-gated) — NOT flipped here |
| b | NYISO R5a | **Option B** (NYCA-wide static proxy) | **FF-3D** |
| c | `datacenter_load_path` default | **mid** | **FF-1F** (this session) |
| d | `correlated_forced_outage` default | **ON** | **FF-1F** (this session) |

## 5. Attestation

- **Rules:** forecast-only posture (rule 22 — no backcast/keeper touched, no
  quarantined-year solve; the smoke is 2026-2028 forecast-mode, unrestricted per
  plan §2.3). No off-registry knobs (rule 24 — both are `ScenarioConfig` fields
  in `run_config.json`). One mechanism per phenomenon (rule 19 — the derate
  relocates the WEFOR event share, does not stack). Derive scripts frozen
  (rule 23 — no residual-driven change). Every number cited (the `scenarios.py`
  docstrings + this doc carry FF-1F/FF-1C/FF-1B provenance; the CI-ungated
  auto-registry regenerates the 2 refreshed defaults on demand — §1).
- **Model:** Opus (rule 27 — core `src/market_sim/` + `scenarios.py` edits).
- **Push (rule 27 §2):** fresh branch off latest `origin/main`; pushed via
  `mcp__github__push_files`; `scenarios.py` (≥300 lines) blob-verified after each
  push touching it.

_Produced 2026-07-18 (FF-1F, Opus)._
