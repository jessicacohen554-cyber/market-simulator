# FFR-3T — implementing D-10: cross-year warm start OFF for forecast bundles

**Session:** FFR-3T (2026-08-04) · **Lane:** small · **HEAD at dispatch:** `15f9d296` ·
**rebased onto:** `8b920ed6` · **implementation commit:** `730b4155`
**Decision:** owner D-10, signed 2026-08-04, `docs/handoffs/ffr-owner-sitting-2026-08-02.md`
Addendum K.3, on FFR-3M's measured adjudication
(`docs/handoffs/ffr-3m-kill-resume-verdict-2026-08-04.md`)
**Measurement driver:** `scripts/probes/_ffr3t_cache_key_census.py` (committed with this doc)

---

## 0. Summary

D-10 is implemented as an **explicit argument from the three shipped forecast runners**, not
as a flip of the `ScenarioConfig` default. That choice is scope item 1 and it is the load-
bearing finding of this session, because **the form the decision's own coordination note
anticipated — flipping the default — does the opposite of what the note expected, in both
directions, and I measured both.**

| | default flip (NOT taken) | explicit argument (SHIPPED) |
|---|---|---|
| forecast cache keys | **24 of 24 UNMOVED** — a cold run silently re-uses a warm bundle | **24 of 24 MOVED** |
| backcast keeper keys | **6 of 6 MOVED** — every keeper cache orphaned | **6 of 6 UNMOVED** |
| backcast solve path | changed (runner-driven backcast goes cold) | untouched |
| pinned default key | `603c2498bf71d21d` unmoved | `603c2498bf71d21d` unmoved |

Cache epoch **2026-08-04** declared in `src/market_sim/results/cache.py`. The kill-resume
drill result is §5. The horizon-scale solve-time cost is §6.

---

## 1. Scope 1 — where `False` is made effective, and why there

### 1.1 What ships

`market_sim.config.scenarios.FORECAST_BUNDLE_XYEAR_WARMSTART = False` is the single
declaration of the posture, sited beside the field it governs. It is read through
`scripts.lib.forecast_posture.shipped_forecast_xyear_warmstart()` — the ONE-reader pattern
the owner signed as C.4(a) B1 for the capacity-clearing posture — and passed explicitly by
each shipped forecast-bundle runner:

| runner | tier | call site |
|---|---|---|
| `run_full_horizon.reference_config` | T1-F | `scripts/run_full_horizon.py` |
| `run_capacity_hindcast.build_config` | T1-H / T1-X / T1-FF | `scripts/run_capacity_hindcast.py` |
| `ff_readiness_battery.golden_posture_config` | the §2.1a golden posture, incl. the drill | `scripts/ff_readiness_battery.py` |

The `ScenarioConfig` default stays `True`.

### 1.2 Why not the default — measured, not argued

Two independent facts, both verified at this HEAD.

**(a) The runner's year loop is mode-agnostic.** `runner.py:890` builds the cross-year basis
holder from `config.forecast_xyear_warmstart`, and `runner.py:2135` passes the same field as
the explicit `xyear_warmstart` gate. Both sit inside the single year loop opened at
`runner.py:908`; the mode gates in that function are all *before* it (lines 483–782) and the
only one after is 2445. So a **backcast** driven through `runner.run_scenario_iso` reads this
field too, and flipping its default would take that path from warm to cold. The primary
calibration lane is insulated for a different reason — `scripts/run_calibration_full.py` has
its own year loop and passes **no** `xyear_warmstart`, so it resolves from
`MARKET_SIM_WARMSTART_XYEAR` (default ON) via `solve.py:219-223` — but "the CLI I happen to
use is insulated" is not the same as "the backcast is out of scope", and the decision says
*for forecast bundles*.

**(b) `cache_key` compares against the LIVE default, so a flip does not move a key.**
`ScenarioConfig.cache_key` drops a `_CACHE_KEY_OPTIONAL_FIELDS` member when it equals
`getattr(ScenarioConfig(), name)` — recomputed per call, not a frozen sentinel. A post-flip
forecast config at the new `False` default therefore hashes exactly as a pre-flip config at
the old `True` default did. This is the FFR-3A blocker-4 hazard already written into the
cache-epoch ledger, which closes with "it will silently recur on the next default flip".
It recurred here, and §3.2 is the measurement.

The explicit-argument form inverts both: forecast configs carry a **non-default** `False`
that enters the hash, backcast configs keep the untouched default and are byte-stable in key
and in path. Rule 24 `[R-REGISTRY]` is satisfied throughout — the tunable is still a
`ScenarioConfig` field and the passed value lands in each run's `run_config.json`.

### 1.3 Effect on the backcast path — none, stated explicitly

No backcast solve changes. The calibration lane's cross-year warm start is still resolved
from `MARKET_SIM_WARMSTART_XYEAR` (default ON, `--no-xyear-warmstart` to disable); no keeper
cache key moves (§3.1); no keeper needs re-solving. A runner-driven backcast also keeps its
warm start, because the default it reads is unchanged.

### 1.4 What is deliberately NOT provided

No CLI flag to re-arm warm start on a forecast runner. A probe that genuinely needs the warm
arm builds the config directly and overrides it — which is exactly what the existing D-9 A/B
driver `scripts/probes/_d9_forecast_warmstart_ab.py` already does
(`reference_config(...).with_overrides(forecast_xyear_warmstart=warm)`), and that probe is
unaffected by this change because it sets **both** arms explicitly. Adding a flag would put a
signed posture one keystroke from silent reversal.

---

## 2. Scope 2a — confirming the cache-key registration at HEAD

`forecast_xyear_warmstart` is registered in `_CACHE_KEY_OPTIONAL_FIELDS`
(`src/market_sim/config/scenarios.py`), declared at `"True"` in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, and its registration comment states that a run which
opts out "enters the key as a distinct scenario". **Confirmed at HEAD**, and confirmed to
behave that way — but only for an *explicit* `False`, which is the distinction §1.2(b) makes.
`scripts/check_cache_key_registration.py` passes after the change: *678 ScenarioConfig
fields, 125 registered, all resolve; 125 declared defaults all match HEAD.*

---

## 3. Scope 2b — before/after key census, both paths

Six ISOs × four shipped forecast configs, plus the six designated keepers' committed
`run_config.json` payloads. Keys measured in-process at the pre-change HEAD and again after.

### 3.1 Backcast — the check that proves the decision was not exceeded

Every key **UNCHANGED**.

| ISO | keeper | bundle | cache key before | cache key after |
|---|---|---|---|---|
| ERCOT | 2026-08-03-ercot158-pool-arm | `ercot158_poolarm_B` | `f95a5d2aab761873` | `f95a5d2aab761873` |
| PJM | 2026-08-03-pjm-151-seam-envelope | `pjm151_seam_B` | `c20ec90ee9626b07` | `c20ec90ee9626b07` |
| CAISO | 2026-08-04-caiso164-zonal-loss-surface | `caiso164_zonal_loss_surface` | `df6220a243add2ad` | `df6220a243add2ad` |
| NYISO | 2026-08-04-nyiso-120-c119-scope | `nyiso120_c119_scopegate` | `c3b175a9fcf4af8d` | `c3b175a9fcf4af8d` |
| NEISO | 2026-08-03-neiso-caiso156-meter-screen | `neiso_c156_meter_screen_B` | `6ff540e9a9ee3b2f` | `6ff540e9a9ee3b2f` |
| MISO | 2026-08-04-miso-124-dualfuel-rearm | `miso124_dualfuel_B` | `dfe9d5c68e15c54c` | `dfe9d5c68e15c54c` |

Pinned default `cache_key(ScenarioConfig())` = `603c2498bf71d21d` before and after.

*Reading note:* these are keys of configs **reconstructed** from each bundle's committed
`scenario_config` block (671 fields), which is what makes them comparable before/after in one
process. The 2023 solve year is not part of the key — the cache is
`results/{iso}/{cache_key}/year_{year}.parquet`, so one scenario key covers all of an ISO's
solve years, 2023 included.

### 3.2 Forecast — all 24 keys move (and would NOT have, under a default flip)

| config | before | after (SHIPPED) | under a default flip |
|---|---|---|---|
| T1-F ERCOT | `e8ce5b85cc254830` | `02d559f6a00f24b7` | `e8ce5b85cc254830` *(unmoved)* |
| T1-F CAISO | `c6ccbcd1ac9a47d6` | `24ab6f39d0d0bb86` | unmoved |
| T1-F PJM | `8a19b75fbc6dc271` | `dda7f7c43ca0d7c9` | unmoved |
| T1-F MISO | `5ed798a1c40dd2bd` | `1e8f173aa965b0bf` | unmoved |
| T1-F NYISO | `a1b69edd31fa45cf` | `ac018d6b0450fec0` | unmoved |
| T1-F NEISO | `6d8b6b71f9001328` | `8a1629c0f7c0a801` | unmoved |
| T1-H ERCOT | `66e61f6267d53a8e` | `def1ee1e8514c384` | unmoved |
| T1-H CAISO | `8915b57448b7562e` | `d13af45fc76bdf89` | unmoved |
| T1-H PJM | `9f5fb3d9cbe10c70` | `f9d5d795106d9c74` | unmoved |
| T1-H MISO | `4c09a710b0894c6c` | `b6f997c653722595` | unmoved |
| T1-H NYISO | `5bd336b5b9a39959` | `fc6f628c90eb7eda` | unmoved |
| T1-H NEISO | `cee8181a253afd6a` | `688dd67264951c7e` | unmoved |
| T1-X ERCOT | `49a8aeccccfcf253` | `3c4edf579674f0f0` | unmoved |
| T1-X CAISO | `0bd3bab2088858b9` | `af40e7e7bede6474` | unmoved |
| T1-X PJM | `36ddca3d48d25fe2` | `4d43d95faf04bce6` | unmoved |
| T1-X MISO | `cfc28a698fb5b1ba` | `d10167c50411416e` | unmoved |
| T1-X NYISO | `3d483c5c82e45ea4` | `27989c835ef55ade` | unmoved |
| T1-X NEISO | `caf7824b3de069f1` | `80a6752279ffe182` | unmoved |
| battery/golden ERCOT | `e8ce5b85cc254830` | `02d559f6a00f24b7` | unmoved |
| battery/golden CAISO | `c6ccbcd1ac9a47d6` | `24ab6f39d0d0bb86` | unmoved |
| battery/golden PJM | `8a19b75fbc6dc271` | `dda7f7c43ca0d7c9` | unmoved |
| battery/golden MISO | `5ed798a1c40dd2bd` | `1e8f173aa965b0bf` | unmoved |
| battery/golden NYISO | `a1b69edd31fa45cf` | `ac018d6b0450fec0` | unmoved |
| battery/golden NEISO | `6d8b6b71f9001328` | `8a1629c0f7c0a801` | unmoved |

*(T1-F and the golden-posture battery config coincide by construction at
`--golden-posture`; both are listed because they are separate call sites and a future edit
could separate them.)*

**The default-flip column was produced by actually making the edit**, measuring, and
reverting — an in-process monkeypatch of the dataclass field is not sufficient, because the
generated `__init__` bakes the default into its signature and the patched value never
reaches a constructed config. Under that flip the six backcast keeper keys move:
ERCOT `f95a5d2aab761873 → 86cdfc027116b309`, PJM `c20ec90ee9626b07 → c562ac25bb545281`,
CAISO `df6220a243add2ad → 6ebf884e0c8cbead`, NYISO `c3b175a9fcf4af8d → d33da31978f8a364`,
NEISO `6ff540e9a9ee3b2f → 8a68a7150325379e`, MISO `dfe9d5c68e15c54c → 6d4a6207d5172da0`.

---

## 4. Scope 2c — the declared cache epoch

Declared as **Epoch 2026-08-04** in the ledger at `src/market_sim/results/cache.py`, and
typed honestly against that ledger's own taxonomy: **this is a KEY ADVANCE for the
forecast-bundle family, not a same-key invalidation.** It is recorded in the same ledger
anyway because that is where a reader asking "why did every forecast key move on 2026-08-04"
will look, and because the ledger is the only place the *rejected* same-key form is visible.

Consequences, stated in the entry:

* **No purge is required for correctness.** A post-D-10 cold config cannot be served a
  pre-D-10 warm bundle — they are addressed by different keys. Pre-D-10 warm forecast
  bundles simply become unreachable by the shipped runners; delete them to reclaim disk, or
  leave them. (The ledger's standing warning applies to any purge: the documented
  `find … -delete` loop reaches **tracked** files under `results/`; check `git status
  --short` afterwards and restore anything showing `D`.)
* **Nothing backcast is invalidated** — six keeper keys byte-identical, pinned default
  unmoved, calibration solve path untouched.

---

## 5. Scope 3 — the kill-resume drill on the shipped config

**PENDING at this commit — the drill is running in this session and this section is
completed by a follow-up commit before the lane closes.** It is `scripts/ff_readiness_battery.py
kill-resume` (the FFR-3J `ef5695b0` discriminator), NEISO 2026–2028, on the shipped config —
which now carries the D-10 posture, because the drill builds its config through
`golden_posture_config`. FFR-3M measured GREEN for exactly this posture in its cell C, so
reproducing it is confirmation, not a new claim; if it does NOT come back green that means the
cause was not fully identified, and the correct outcome is to report that rather than chase it.

---

## 6. Scope 6 — the horizon-scale solve-time cost, plainly

The cost is **accepted with the decision and is not mitigated here**. No basis is pinned, no
tie-break introduced, no ordering frozen, and nothing is tuned to recover the speedup.

The horizon-scale number already exists as a controlled A/B and is the right instrument, so
it is quoted rather than re-run: the **D-9 arming experiment** (Exp 5,
`docs/handoffs/wallclock-baseline-2026-07.md`), ERCOT full horizon **2026–2050**, 8760 h,
`threads=1`, warm vs cold:

* total wall **25.1 min warm → 51.1 min cold**, i.e. **+26.0 min per ISO-arm**;
* **2.04×** overall, **2.20×** on the warm-startable years 2027–2050 (year one is cold in
  both arms, which is why the overall factor is below the steady-state one);
* the capacity trajectory was **bit-identical in all 25 years** across those arms — which is
  why the speedup was takeable in the first place, and why giving it back costs wall clock
  and nothing else.

Read forward: a six-ISO full-horizon T1-F sweep costs roughly **+2.6 h of wall in aggregate**
at these anchors, and a 3-year T0 window costs almost nothing (only the second and third
years were ever warm-startable). The expensive case is exactly the full-horizon T1 lane the
flag was introduced for; the cheap case is the T0 drill and every hindcast window.

---

## 7. Sequencing — what I checked, and what I could not

**FFR-3Q-2: no evidence yet that it has landed, and no evidence either way that it is
running.** Checked at `8b920ed6`:

* **Open PRs: none** (the list is empty).
* **Closed/merged PRs**, most recent 12 — nothing titled or branched FFR-3Q-2. The FFR-3Q
  branch `claude/ffr-3q-window-recut-aolov4` last merged as #3491 (Task 1 stop-the-line +
  the quarantined-arm ignore), which is FFR-3Q, not its re-probe.
* **`docs/handoffs/` for today** — `ffr-3q-window-recut-2026-08-04.md` is FFR-3Q's own
  deliverable; there is no FFR-3Q-2 write-up.
* **`origin/main` since 2026-08-03** — no commit touching `frontend/data/forecast/`,
  `frontend/data/hindcast/` or a T1-FF run directory for that lane.

Absence of a PR is not absence of a running session — a session burns ~65 min on `uv sync` +
`regenerate_clean.py` before it can push anything, so **"no evidence yet" is the correct
report and "not running" would not be.** What makes it safe to push regardless: FFR-3Q-2's
own dispatch tells it to **pin its HEAD**, so a flip landing on `main` cannot reach an
in-flight solve. If that lane rebases onto this change afterwards, its forecast cache keys
move (§3.2) and its A/B legs must be re-keyed — but its arms are an explicit
old-default/new-default pair, so the correct remedy there is to set
`forecast_xyear_warmstart` explicitly on **both** arms, which is what
`_d9_forecast_warmstart_ab.py` already does and what keeps an A/B's two arms independent in
the on-disk cache.

**Other forecast lanes checked and found not in flight on this file:** FFR-3K (the FC-7
`.yaml`/`.json` defect) is recorded as still never dispatched; FFR-3S (D-9(ii) COD-shifted
scoring) is scorer-side and touches no cache key; the FFR-3A-4 / MISO T1-X pre-registration
(`00b0637c`) landed as a pre-registration with no solve.

---

## 8. Scope 4 — the pinning test

`tests/unit/pipeline/test_forecast_bundle_xyear_warmstart.py` (29 cases) pins:

1. `FORECAST_BUNDLE_XYEAR_WARMSTART is False` and that the reader returns it;
2. **every shipped runner × every ISO** builds a config with
   `forecast_xyear_warmstart is False` — T1-F, T1-H, T1-X and the golden posture;
3. the `ScenarioConfig` default is still `True`, with the reason stated on the assertion;
4. the **key separation**: a forecast config's key differs from its warm twin, and a
   backcast config's key equals the one that names the default explicitly.

Between this file and the two pre-existing pins (`test_forecast_xyear_warmstart_flag.py`,
`test_xyear_warmstart_default.py`), a future default flip cannot silently revert D-10: the
flip breaks those two, and removing the explicit argument to make them pass breaks this one.

---

## 9. Scope 5 — rule 28 matrix

New row `forecast_xyear_warmstart` (`cat: structure`, `mode: F`), backcast cells `......`
(the calibration lane never reads the field), forecast cells `RRRRRR`.

The note states plainly what those six R's are and are not: **one ISO-agnostic owner decision
disarming a solve-path knob, not six per-ISO market verdicts.** Rule 25 `[R-ISO-SCOPE]` is
not stretched by them because nothing market-behavioural is transferred — the LP optimum is
basis-independent, so this row never claims anything about any ISO's market. Per-ISO evidence
is cited where it exists (NEISO: FFR-3M's three cells; ERCOT: the D-9 arming A/B and the
`cross-year-warmstart.md` retirement tie-flip that made basis-pinning unacceptable) and the
decision itself is cited under `All`. The row carries no line anchors, deliberately — the
anchors ratchet records that they decay.

---

## 10. Also corrected in passing

`scripts/run_calibration.py::resolve_xyear_warmstart_default`'s docstring claimed the
forecast loop "passes `xyear_cache=None` and cannot consume the basis regardless of the env
var". That stopped being true at D-9, and it is the same stale premise FFR-3M recorded as
dispatch premise (a). Corrected to state what actually isolates the two lanes now — the
explicit gate argument, not an absent holder — and to record that D-10 makes the forecast
cold-only again by decision rather than by plumbing. `docs/cross-year-warmstart.md` gains its
D-10 status update and its header no longer mis-describes the wiring.
