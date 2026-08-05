# FFR-5C — Landing the entry-cap fix: un-net the stock, give the pro-forma eyes

**Lane:** implementation (Wave 5) for FFR-4A's escalations E-1 + E-2; owner
decision D-17(a), sitting Addendum R.2/R.5, signed 2026-08-05.
**Head at start:** `origin/main` `547a7c38`.
**Scope discipline held:** no LP solve, no forecast/hindcast registration, no
keeper contact, no default flip, no arming in any `ISOConfig`
`default_scenario_overrides`. The field ships **OFF everywhere**.

---

## 0. Headline

One gated `ScenarioConfig` field — **`entry_pipeline_aware_signal`**, default
**OFF** — lands both halves of FFR-4A's recommendation together, so the
anti-cobweb guard **relocates** from the annual flow caps to the pro-forma
price signal rather than being deleted (rule 19 `[R-ONE-MECH]`).

The shipped path is byte-identical until armed, and that is **proved, not
asserted** (§2). Armed, the paired arm reproduces FFR-4A §5.2's measured
Arm-B series **to the MW on all four legs, with zero deviation** (§3).

**This does not rescue MISO solar.** Every number below is a cap **CEILING the
arithmetic permits**, not a build: the harness forces every tech profitable and
runs no dispatch. FFR-3V's MISO-solar leg decides **zero** on revenue grounds
before any cap is consulted (pre-registered as false by FFR-4A §4 and carried
here per the owner's acceptance at Q.3).

---

## 1. What landed

### 1.1 The field

`entry_pipeline_aware_signal: bool = False` (`config/scenarios.py:3036`),
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
+ `TIER_TAGS`, so it appears in every run's `run_config.json` (rule 24
`[R-REGISTRY]`) and the default-arm cache key does not move.

**The name.** It names what the field makes *true* — the entry pro-forma becomes
aware of its own committed pipeline — rather than the netting it deletes,
because the deletion is a **consequence** of moving the guard, not the
mechanism. Off, the pipeline is visible only to the caps; on, only to the
signal. Exactly one of the two is true at a time, which is the rule-19 property
the field exists to preserve.

### 1.2 Half E-1 — the stock leaves both flow caps

`model/capacity_evolution/new_entry.py`. `_pending_by_tech` (the queue **state**)
is still computed; a new alias `_pending_netting_mw` is what the two caps
subtract, and it is `{}` when armed. Both sites move together:

* `group_remaining` — the static per-tech queue cap `QUEUE_CAP_PER_TECH_GW`;
* `_ladder_remaining` — the endogenous ladder `ENTRY_GROWTH_LIMIT_MULTIPLE ×
  prior max`.

Off, `max(0.0, cap − 0.0) == cap` is the identical expression the shipped code
evaluates, so the off path is unchanged at the level of the arithmetic, not
merely of the result.

**Neither `K` nor `L` moves** (rule 23 `[R-FROZEN-DERIVE]`): `K = 2.0` keeps its
ReEDS 200 %-of-prior-maximum citation and its corroboration against the measured
EIA-860 growth-ratio distribution (p75 < 2.0 < p90, FFR-4A §3.4(ii));
`L = 2` keeps LBNL *Queued Up* 2024's median IA→COD. A regression test asserts
both, so a later session cannot quietly re-tune them under cover of this fix.

### 1.3 Half E-2 — the pro-forma sees the pipeline

New public helper `capacity_evolution.new_entry.pipeline_lookahead_units`
(re-exported through the `model.capacity` facade) splits the pipeline rows that
are **online in the priced year** (`cod_year <= through_year`) into

* **thermal** rows → `Generator`s built by the **same** `_make_new_generator`
  call `evolve_fleet`'s step-4.5 commissioning makes, carrying the same id
  convention, so the pro-forma unit and the unit it anticipates trace to one
  decision cohort;
* **VRE** rows → `{(zone, tech): mw}`, because VRE enters this model as zonal
  pools and never as a `Generator`.

New runner helper `_pipeline_lookahead_terms` values them:

* thermal → `generators_to_fleet_arrays` → `resolve_fuel_prices` →
  `assemble_mc`, i.e. **the same seam the current fleet's own stack is built
  from**, at **this year's** fuel and carbon basis so the pro-forma's two halves
  share one cost basis (rule 19 — no second cost construction to drift);
* VRE → `mw ×` that zone's own hourly capacity factor, the same array that
  upper-bounds `W[z,t]`/`S[z,t]` in the LP.

`_lookahead_reprice_signal` gains three parameters, all defaulting to `None`:
`pipeline_mc`, `pipeline_arrays` (appended to the merit stack on the identical
time-mean-cost / availability-derated-capacity basis as the fleet) and
`pipeline_vre` (added to the net-load VRE term).

**Zero new tunables.** Every quantity is either a field the pipeline row already
carries (`mw`, `cod_year`, `zone`, `tech`, `seq`, `decision_year`) or is read
from a shipped helper. Nothing was invented, so §2 of the prompt's escalation
clause never fired.

A row whose zone is not a model zone is **skipped with a warning**, not silently
mis-assigned.

---

## 2. Byte-identity proof

| claim | evidence |
|---|---|
| Field defaults OFF | `test_field_defaults_off` |
| Default cache key unmoved | `cache_key(ScenarioConfig())` = `603c2498bf71d21d`, the documented value on both sides; `scripts/check_cache_key_registration.py` → `ok: 685 fields, 132 registered, all resolve; 132 declared defaults all match HEAD` |
| The E-1 off-path decision series is unchanged | `test_miso_solar_frozen_at_the_ladder_seed` asserts **1,236 MW/yr for 12 straight years** (FFR-4A §5.2 Arm 0) and `test_miso_wind_alternates_at_the_static_cap` asserts the **4,000 / 0** alternation with mean **2,000 = C/L** — both driven through the real `apply_economic_new_entry`, over a multi-year path, with the field off |
| The E-2 signature change is inert at its defaults | `test_lookahead_signal_identical_without_pipeline_terms` — `assert_array_equal` (exact, not `allclose`) between the no-argument call and the explicit all-`None` call |
| Nothing else in the suite moved | `pytest tests/unit` → **3,340 passed**, 5 failures; `pytest tests/regression` → **369 passed**, 8 failures. **All 13 are pre-existing on a clean `origin/main`**, verified by stashing and re-running each: `test_outages.py::…test_unknown_iso_degrades_to_empty`, the four `test_export.py::TestExportScenarioJson` cases, the six `test_soundness.py::TestEndToEnd` cases and `test_fleet_arrays_golden.py` (all needing a regenerated clean store this session deliberately did not spend the hour building), plus `test_constants_facade.py::test_moved_surface_is_complete` (an unrelated `STORAGE_MEASURED_BASE_FLEET_ISOS` facade gap from another lane). `test_capacity_evolution_facade.py` — which pins the re-export surface this change adds `pipeline_lookahead_units` to — **passes**. |

The regression the prompt asked for is `TestShippedPathUnchanged` in
`tests/unit/model/test_entry_pipeline_aware_signal.py` (17 tests total, all
green).

---

## 3. Paired-arm measurement

**Instrument:** `scripts/probes/ffr5c_paired_arm.py` — the FFR-4A harness
pattern (the real `apply_economic_new_entry`, the real step-4.5 commissioning,
the real prior-max ladder update, other techs suppressed with a zero ladder row
so MISO's shared 10 GW/yr ISO budget cannot mask the cell) with **one
difference that is the point of this lane**: the arm is selected by the
**shipped field**, not by hand-deleting source lines and `git checkout --`-ing
them back. The measurement now reproduces from a clean checkout.

Both FFR-4A cells are run — **MISO solar** (ladder-first: seed 0.618 GW ⇒ ladder
1,236 MW/yr *below* the 6,000 MW/yr static cap) and **MISO wind**
(static-cap-first: seed 4.367 GW ⇒ ladder 8,734 MW/yr *above* the 4,000 MW/yr
static cap).

### 3.1 MISO solar — the ratchet

| year | shipped (Arm 0) | armed (Arm B) |
|---|---|---|
| 2022 | 1,236 | 1,236 |
| 2023 | 1,236 | 2,472 |
| 2024 | 1,236 | 4,944 |
| 2025 | 1,236 | **6,000** |
| 2026 | 1,236 | 6,000 |
| … | 1,236 forever | 6,000 = the static cap, now the true binder |
| **commissioned 2021–25** | **2.472 GW** | **3.708 GW** |
| **decisions 2022–33** | **14.832 GW** | **62.652 GW** |
| **steady-state mean** | **1,236** | **6,000 = C** |

### 3.2 MISO wind — the alternation

| year | shipped | armed |
|---|---|---|
| 2022–2033 | 4,000 / 0 / 4,000 / 0 … | **4,000 every year** |
| **steady-state mean** | **2,000 = C / L** | **4,000 = C** |
| **commissioned 2021–25** | 4.000 GW | 8.000 GW |
| **decisions 2022–33** | 24.000 GW | 48.000 GW |

### 3.3 Scoring against FFR-4A §5.2

| FFR-4A §5.2 measured | reproduced here | |
|---|---|---|
| Arm 0 solar frozen at 1,236; 2.472 GW; 14.832 GW | identical | ✅ |
| Arm B solar 1,236 → 2,472 → 4,944 → 6,000 → 6,000; 3.708 GW; 62.652 GW | identical | ✅ |
| Arm 0 wind 4,000/0, mean 2,000 = C/L; 4.000 GW | identical | ✅ |
| Arm B wind (implied by §3.3's law: the netting removed, `C` binds per year) | 4,000 flat; mean 4,000 = C; 48.000 GW | ✅ |

**Zero deviation on any leg**, so there is no finding to explain and nothing was
tuned away. The FFR-4A general law `D ≤ C/L` is measured directly in the shipped
arm of the wind cell and is exactly what disappears in the armed arm.

---

## 4. The backstop asymmetry — recorded, unchanged, not made worse

FFR-4A §1.3: the two consumers of the **one** ladder budget net differently.

* the **economic screen** netted the pending stock (`new_entry.py`);
* the **reserve-margin backstop** nets only **this year's** decisions
  (`evolve.py:708–713`, `_decided_mw_by_tech`) and commissions **in-year**
  (`adequacy.py:497–500` appends the unit straight to the fleet, writing no
  `entry_pipeline` row), so it neither reads nor creates pending state.

**Not mine to reconcile, and I did not touch either file.** Statement for the
record, in both directions:

* **Armed, the asymmetry is not made worse — it is made smaller.** The
  divergence was that one consumer subtracted a stock and the other did not.
  Armed, the screen stops subtracting the stock too, so both consumers now net
  the same object (this year's decisions; the screen's `remaining` /
  `group_remaining` / `_ladder_remaining` decrements, the backstop's
  `_decided_mw_by_tech`). The *remaining* difference — that the backstop
  commissions in-year with no pipeline row while the screen defers to
  `cod_year` — is untouched and is the older, separate issue.
* **One consequence to flag, because it is a real direction change and not an
  improvement:** armed, the screen can decide up to the full ladder/static cap
  every year, so in a year where the screen exhausts the budget the backstop's
  `_gas_ct_rate_budget` residual is smaller than it would have been under the
  netting. That is the *intended* behaviour of the caps binding as flows, but it
  does mean the two consumers' contention for one budget is tighter under the
  armed arm. It is measured nowhere in this lane — no solve was run — so it is
  a flag, not a finding.

---

## 5. What I did **not** separate

* **No LP solve, no dispatch, no prices, no revenue.** Every number in §3 is a
  ceiling the cap arithmetic permits. They must never be quoted as build
  forecasts, and §3 is not evidence about any ISO's forecast bands.
* **The E-2 half is not measured by the paired arm, by construction.** The
  harness's price is exogenous and flat-profitable, so it bypasses
  `_lookahead_reprice_signal` entirely. E-2 is covered by unit tests only —
  that the pipeline rows reach the stack, that they are valued through the
  shipped cost seam, and that they push the pro-forma price *down*. Its
  magnitude in a real forecast is **unmeasured** and needs a solve.
* **The pro-forma's HORIZON is still one year, and that is a separate open
  gap.** The relocation makes the priced year's stack *correct* — capacity that
  will be online in `next_year` now appears in it. But
  `_lookahead_reprice_signal` prices `year + 1` while the entry decision is for
  `year + L`. So a decision in flight for `Y+2` is still absent from the signal
  the `Y+1` screen consumes, because it is genuinely not online in `Y+1`. The
  cobweb is therefore **reduced, not closed**: the guard now stops the
  re-decision of capacity that has *arrived*, not of capacity still in
  construction. Closing the rest means extending the pro-forma horizon to the
  COD year, which needs a future demand path and a future fleet — a **new
  mechanism with its own charter**, not a widening of this one. Recorded as the
  escalation in §7.
* **VRE enters the pro-forma on a potential (pre-curtailment) basis**, one notch
  richer than the realized-dispatch VRE term it is added to. The pro-forma has
  no curtailment model, and inventing a haircut would be a fitted parameter
  (rules 5 / 24). Documented at the helper.
* **Two cells measured, twenty-four mapped.** As in FFR-4A: MISO solar and MISO
  wind, one of each signature. The other 22 cells inherit the analysis, not a
  measurement.
* **Nothing was armed anywhere.** No ISO default, no keeper, no forecast lane.

---

## 6. E-3, carried into the code so it cannot be re-introduced blind

FFR-4A §7.2's E-3 is now written into the field's own docstring, not only into a
handoff: under the **old** construction the growth factor is `K − L + 1`, so it
reaches **zero at `L = 3`** and goes negative beyond — economic entry shuts off
entirely while every parameter still carries a valid citation. The per-tech
IA→COD refinement that `ff-entry-stack-completion-2026-07.md` records as future
work would very plausibly push wind past 2 years and silently kill wind entry.
The armed path removes the trap. This is an argument for arming **before** `L`
is ever refined, and it is the reason the note lives next to the field a future
session will read rather than in a document it might not.

`L` itself is untouched (a test asserts it).

---

## 7. Open / escalated

* **Arming is an owner decision.** The field ships OFF in every ISO. The paired
  arm above is the evidence the decision needs on the E-1 half; the E-2 half
  needs a solve to size.
* **Pro-forma horizon (new).** `_lookahead_reprice_signal` prices `year + 1`
  against a decision for `year + L`. Escalated per §5; not chartered here.
* **`QUEUE_CAP_PER_TECH_GW`'s eastern-ISO values remain self-declared
  engineering judgment** (FFR-4A E-4). The armed arm makes them **bind
  harder** — under the netting the effective ceiling was `C/L`, and armed it is
  `C` — so the standing rule-11 follow-up
  (`docs/handoffs/queue-cap-citation-2026-07.md`) is more load-bearing after
  this change than before it. Flagging, not widening scope.
* **Pre-existing red not caused by this lane, left for its owner:**
  `scripts/check_cache_key_registration.py` passes, but `ruff` reports **F601**
  on `src/market_sim/config/scenarios.py` — `"ercot_storage_rt_offer_surface"`
  appears twice in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (lines 741 and 764) with
  **identical** values, so it is cosmetic. It is present on clean `origin/main`
  (verified by stash). Not touched here: the duplicate belongs to whichever lane
  most recently added it, and editing that hunk from this branch only creates a
  merge conflict for them.

---

## 8. Rule discharge

* **Rule 1 `[R-STRUCT]`** — nothing was tuned to a band; the fix deletes an
  uncited term and moves a guard to the object its own phenomenon lives on.
* **Rule 19 `[R-ONE-MECH]`** — E-1 and E-2 are **one** field. The guard
  relocates; it neither vanishes nor duplicates.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the identification is FFR-4A §3.4's EIA-860
  statistics, cited and not re-derived. No residual was consulted.
* **Rule 24 `[R-REGISTRY]`** — one `ScenarioConfig` field, in the cache-key
  ledger and `TIER_TAGS`, visible in `run_config.json`. No env knobs, no
  hardcoded dicts, no `getattr` fallback literals that change a number.
* **Rule 25 `[R-ISO-SCOPE]`** — the mechanism is ISO-agnostic and carries no
  per-ISO value. The matrix cell is `O` in **MISO only** (where it was
  measured); every other ISO is `U`.
* **Rule 27** — `new_entry.py` and `runner.py` were edited locally with the Edit
  tool and pushed as exact on-disk bytes over `git push`; no `push_files`
  full-file rewrite of any ≥300-line file. Blob verification recorded at §9.
* **Rule 28(c)** — the `entry_pipeline_aware_signal` matrix row lands in the
  **same PR** as the field; `scripts/check_mechanism_matrix.py --base
  origin/main` exits 0 with integrity, anchor, gap-ratchet and shared-ratchet
  legs all clean. The 220 repaired line anchors are a mechanical consequence of
  inserting the field into `scenarios.py` (`--fix-anchors`; the diff is digits
  only, verified line by line).

---

## 9. Artifacts

| what | where |
|---|---|
| the field | `src/market_sim/config/scenarios.py` (`entry_pipeline_aware_signal`) |
| E-1 | `src/market_sim/model/capacity_evolution/new_entry.py` (`_pending_netting_mw`) |
| E-2 | `new_entry.pipeline_lookahead_units`, `runner._pipeline_lookahead_terms`, `runner._lookahead_reprice_signal` |
| regression + coverage | `tests/unit/model/test_entry_pipeline_aware_signal.py` (17 tests) |
| paired arm | `scripts/probes/ffr5c_paired_arm.py` |
| matrix row | `docs/codebase-site/data/mechanism-matrix.js` → `entry_pipeline_aware_signal` |
