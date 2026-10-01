# PRE-REGISTRATION — capx D78: the sector-gate / clearing seam repaired — fixed BEFORE any code and BEFORE any solve

**Lane:** capx D78 (director r#47; owner ruling **Q53 = READING 1**, capx ledger §3, 2026-09-06).
Branch `claude/capx-d78-sector-gate-offer-seam-d1tfcd`, fresh off `origin/main` **`ba894c9c`**.
Companion: `DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` (the market rule with its
Manual 18 citations, the one seam, every consumer, the other exemption channels). Instrument:
`docs/handoffs/d78/keys_probe.{py,json}` (zero LP). DATA PROFILE `pjm`. Model Fable.
**Date:** 2026-09-06. **Pushed before the first line of mechanism code and before any solve.**

**NOTHING ARMS.** No new field, no default flip, no `_pjm_config` override (the D67-ARM lane owns
`_pjm_config` this window), no parameter value. The owner decides on §7.

---

## 0. Preconditions, checked — and one stated deviation

| precondition | reading |
|---|---|
| Q53 ruled READING 1 in the capx ledger §3 | **PASS** (`71096e60`, r#47 am.1) |
| `retirement_sector_gate` on main (D53), default-off, registered at `"False"` | **PASS** (`scenarios.py:15960`, `:2024`) |
| `capacity_market_supply_clearing_by_iso` armed for PJM through `_pjm_config` (D57 / Q44) | **PASS** (`iso_configs.py:130–132`: `pjm_accreditation_design_vintage`, `pjm_demand_response_supply`, `{"PJM": True}`) — the bare `pjm-t1h` recipe clears the stack |
| D74's `retirements.py` hunks on main (the adjacent-region collision the charter's hold protected) | **PASS** — `64477801` (build), `be313ecd` / `18213f28` / #5114 (instruments) are ancestors of `ba894c9c`; the D74 class skip sits at `retirements.py:3235–3241`, the D78 partition point is after `:3613` |
| **D74's SCREEN landed on main** (the charter's literal start condition) | **NOT MET, and this lane starts anyway — stated.** There is no `FINDING-capx-d74-*.md` on main, no open D74 PR (`search_pull_requests "D74 in:title"` → three closed PRs, all build/instruments/director), and the ledger's last D74 row reads *"Session IDLE at 'control-B still solving' — re-hand from the PRECOMMIT if no screen commit by next sitting"*. The hold's stated purpose — *"same file, adjacent region — a merge-order care line"* — is discharged by D74's build being on main; a D74 screen landing would carry a FINDING, a shard cell and possibly a `retirements.py` repair. **Mitigation:** the lane rebases onto `origin/main` before every leg and before every push, re-audits the delta (§2 discipline), and never drops a D74 hunk. If a D74 screen landing touches `retirements.py` between two legs, the affected legs are re-solved on the rebased HEAD (§3 HEAD guard). *(Also noted for the director: PJM's shard cell `capacity_no_default_cap_convention` on main already cites `FINDING-capx-d74-2026-09-06.md`, which does not exist — a dangling citation D74's landing will resolve; not this lane's to edit.)* |

---

## 1. The mechanism, fixed here (design §3) — one seam, no field

| # | piece | where |
|---|---|---|
| 1 | `apply_economic_retirements(..., exempt_unit_ids=frozenset(), exit_exempt_unit_ids=frozenset(), ...)`: the NEW set's members have their margin evaluated on the unchanged code path and their accredited MW offered into the D57 stack at `max(0, GFC − EAS)/(A_g × 365)`; they are settled; then **`margins` is partitioned to exclude them AFTER `_settle_capacity_supply_clearing` (and the D74 ledger block) and BEFORE `_screen_stack` / the pipeline rule / the legacy loop**. `exempt_unit_ids` keeps its meaning (out of the screen entirely: dated plants, this-year retrofits). A unit in both sets is `exempt_unit_ids`. | `retirements.py` |
| 2 | `evolve_fleet`: `exempt_unit_ids=_retrofitted_ids \| _dated_exempt`, `exit_exempt_unit_ids=_sector_exempt`; the D53 comment amended; the `sector_gated` ledger block unchanged. | `evolve.py:670` |
| 3 | `results/cache.py` epoch entry: **same key, semantic change** for `retirement_sector_gate=True` on a clearing-armed ISO; blast radius zero committed bundles (D58's deleted; every MISO gate-on bundle has the clearing off and is byte-identical; no PJM gate-on run was ever registered). | `results/cache.py` |
| 4 | Tests T1–T5 (design §3.6) in `TestRetirementSectorGate`; the evolve spy split into the two parameters. | `tests/unit/model/test_capacity.py` |
| 5 | **No `ScenarioConfig` field, no cache-key registration, no matrix row** (rule 28(c) not triggered); PJM's `retirement_sector_gate` cell updated in PJM's shard only (rule 28(b), 25). | — |

**The screen's failing set under the gate** (design §2.4): the uncleared set restricted to the
decision partition; a gated uncleared unit is *uncleared and retained*, reported, never forced.

---

## 2. G-DRIFT (rule 29(b)) — every solve-path hunk since D58's solve HEAD `99c75b3d`, classified — **VERDICT: ALL INERT for this recipe; the key move is D65-B's CCS re-key**

D58 solved its two screen legs at `99c75b3d` (FINDING §1). The pre-declared identity of §4 G0
("D58's arm at HEAD reproduces D58's 566.3 MW to the MW") is a direct test of this audit, and
the audit is recorded here so it cannot be written to fit that result.

**Config axis.** `keys_probe.json`: the bare recipe resolves to **`15a723ba3b6dc856`** at HEAD
(D58: `aef81c84c4609c76`), the gate-on recipe to **`bc387828f931e0ac`** (D58:
`f546407cf3489761`), the screen span to **`afda79ba04cbfdbf`** / **`d527c3299b8c00b5`** (D58:
`e47fee08f5f37d6f` / `0265ce2b262ad37f`). **Reverting the two capx D65-B (`fb93b76e`) value
changes on the same recipe — `ccs_retrofit_vom_adder` 2.95 → 8.0 and
`ccs_retrofit_fixed_cost_co2_scaling` True → False — returns all four keys to D58's exactly**
(`move_attributed_to_d65b_entirely: true`). So the whole move is D65-B's, and D65-B is a
CCS-retrofit re-key: both fields are read only inside `apply_ccs_retrofit` **after** its first
statement `if year < config.ccs_retrofit_available_year: return` (`ccs.py:354`; the default is
2028, `scenarios.py:4119`; the VOM adder is read at `:452`, the shape gate at `:384`) and
nowhere else on the solve path (grep: `results/cache.py` prose only). **Inert on every year of a
2021–2025 hindcast, by construction.** A moved key is not a LIVE verdict; the audit is.

**Code axis, `99c75b3d..HEAD` on the solve path** (17 files, +1,591 / −156; `git diff --stat`
over `src/market_sim scripts/run_capacity_hindcast.py scripts/lib data/raw/_validation-source
data/raw/reference`), hunk by hunk on every `src/` file:

| file(s) | hunks | class |
|---|---|---|
| `config/scenarios.py` (+345) | D65-B: the two value changes above + the `_resolve_ccs_retrofit_fixed_cost_pair` validator refactor (reads the same two fields); D74: `capacity_no_default_cap_convention_by_iso` (default `None`, dropped from the key, backcast-coerced); miso-224: `miso_gas_marginal_commodity_pricing` (default `False`, MISO-scoped) | **INERT** (CCS: below 2028; D74: off; miso-224: off and not this ISO) |
| `config/capacity_market.py` (+62), `config/constants.py` (+2) | D74's `resolve_capacity_no_default_cap_convention` + its refused-log set, re-exported through the facade | **INERT** (returns False with the field `None`) |
| `data/avoidable_cost_rate.py` (+33) | D74's `no_default_cap_class` predicate — called only under `no_default_cap_armed` (`retirements.py:3235`) | **INERT** |
| `model/capacity_evolution/retirements.py` (+62) | D74: `no_default_cap_armed` resolution (False), the class skip inside `if no_default_cap_armed`, the ledger block inside `if event_sink is not None and no_default_cap_armed` | **INERT** (every hunk is behind a False predicate) |
| `model/capacity_evolution/evolve.py` (+6) | D74: forwards `no_default_cap_price_takers` if present (absent) | **INERT** |
| `data/fuel/basis/miso.py` (+164), `data/fuel/resolve.py` (+25), `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` (+2 each) | miso-224: `apply_miso_gas_marginal_commodity` returns `None` unless `config.miso_gas_marginal_commodity_pricing` (`miso.py:377`) and raises for a non-MISO ISO; on `None` `resolve_fuel_prices` takes the pre-hunk branch (`apply_miso_winter_citygate_daily`, itself MISO-gated) and `skip_for_miso` is unchanged for a non-MISO run | **INERT** (off, other ISO) |
| `model/commitment.py` (+34), `pipeline/commitment.py` (+31) | nyiso-201: a `per_unit` census inside `screen_stats` (a diagnostics dict the floor arithmetic never reads) and a per-plant log line in the NYISO gas-bridge floor (NYISO-only, `nyiso_gas_commitment_bridge`) | **INERT** (diagnostics; other ISO) |
| `results/cache.py` (+58) | the D65-B epoch prose | **INERT** |
| `scripts/run_capacity_hindcast.py` (+55) | the D74 flag pair, `Derived` record line, `None`-drop plumbing — additive; omitted on every D78 leg | **INERT** |
| `data/raw/_validation-source/caiso_offer_*` (3 files) | CAISO offer-surface measurements | **INERT** (other ISO's inputs) |
| `scripts/lib/*` | no solve-path change | — |

**Consequence.** Every hunk since `99c75b3d` is INERT for a PJM 2021–2025 hindcast on this
recipe, so **D58's control and arm numbers are reproducible at HEAD to the MW** — which §4 G0
tests rather than assumes. The three-leg screen the charter names is solved anyway: control-P
and D58's arm because the charter requires them **at HEAD** (and because D58's bundles are
deleted — there is no committed gate-on control to difference against, so form 4 does not
arise), and the repaired arm because it is the mechanism. The audit is recorded before any leg
is solved and is not revisited; a rebase between legs gets a delta re-audit as an addendum.

---

## 3. SCREEN (rule 29 [R-SCREEN]) — named here, before it runs

**SCREEN YEAR = the 2022 screen (DY 2022/23), span `--start-year 2021 --end-year 2023`** — D58's
own screen span (solve years {2021, 2023}, 2022 the rule-22 bridge, never scored). It is the year
the seam's **own measured footprint is largest**: 34,172.4 MW of accredited capacity moved out of
the stack AND the only year of the two where the price moved (67.760 → 61.207 $/MW-day; 2023 sat
on a flat VRR segment at 0.00 %). Measured from D58 §3.2, never from a residual.

**Three legs, all PJM solo, sequential (rule 12; a PJM year is ~7–9 GB on this 15 GB / 4-core
box), each under a HEAD guard (`H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" =
"$H0" ] || exit 90`):**

| leg | recipe | code | role |
|---|---|---|---|
| **control-P** | bare `pjm-t1h` (gate off) | the phase-0 commit (its `src/` byte-identical to `ba894c9c`) | the differencing pair |
| **D58's arm** | `--retirement-sector-gate`, **seam as built** | the phase-0 commit | reproduces D58 (§4 G0) or STOP |
| **repaired arm** | `--retirement-sector-gate`, seam repaired | the phase-1 build commit | the mechanism |

Recipe (all legs): `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2023 --vintage
2020 --fuel-variant realized --entry-screen-diagnostics --out-dir results/hindcast/pjm-2021-2023-
realized-t1h-d78-<leg>`. Legs 1–2 must run on the pre-fix code, so they are solved on the phase-0
commit while the fix is built in a separate worktree; leg 3 runs after the build lands on the
branch. The delta between the two commits is **this lane's own hunk plus tests and docs**, listed
in the FINDING by `git diff --stat`; the control is unaffected by it (gate off ⇒ the new set is
empty ⇒ byte-identical), which T1 asserts. Rebase onto `origin/main` between legs; any delta
re-audited as an addendum before the next leg.

**The screen gate is STRUCTURAL and a STOP gate only** (it may kill the arm, never promote it;
no gate reads `retire.total_gw`, `false_retire`, recall, precision or any residual):

| # | question | pass condition |
|---|---|---|
| **G0** | the audit's own test | D58's arm at HEAD reproduces D58's 2022 screen **to the MW**: failing pool 29,161.6 MW (control-P 29,727.9 − 566.3), `n_offers` 1,000, `offered_mw` 116,684.8, `price_takers_mw` 64,750.2, price 61.207 $/MW-day, 41 arm-only merchant rows / 2,910.2 MW, and control-P reproduces 677 rows / 29,727.9 MW, 1,370 offers, 150,857.2 / 30,577.9 MW, 67.760 $/MW-day (ledger rounding, ±0.001 MW / ±0.000001 $/MW-day). **A miss here is a LIVE hunk §2 missed: STOP, re-audit, no leg 3.** |
| **G1** | the stack identity | repaired arm vs control-P, 2022: `n_offers` **1,370**, `offered_mw` **150,857.2**, `price_takers_mw` **30,577.9**, `requirement_mw` and `census_mw` identical; **every row of `offer_stack` identical** (unit, fuel, offer to 1e-9, `A_g` to 1e-6, cleared flag) |
| **G2** | the price identity | 2022 price **67.760 $/MW-day** and `cleared_position` identical to control-P's (±0.000001, the ledger's precision; the D57 indifference guard `_CLEARING_INDIFFERENCE_RTOL` = 1e-9 is the only rounding on the path), `how` identical |
| **G3** | the partition, exact | the repaired arm's 2022 failing pool (`decided` ∪ `entry_capped` rows) = control-P's **minus exactly the 226 sector-1 rows / 3,476.5 MW** = **451 rows / 26,251.4 MW**; **zero merchant rows change state** (the arm-only set is EMPTY; the control-only set is all sector-1); every shared row's MW identical to the decimal |
| **G4** | the convention's own identity | zero sector-1 rows and zero unknown-sector rows in any `pipeline_events` row of 2021–2023; every unit in the `sector_gated` set that has dispatch rows and `A_g > 0` **appears in the 2022 `offer_stack`**; `sector_gated` reads 384 units / 41,221.6 MW as in D58 |
| **G5** | no non-target flip | 2022: `thermal_additions`, `renewable_additions`, `storage_additions`, `announced_derates`, `confirmed_derates`, `ccs_retrofits`, `entry_decided_mw_by_tech`, `peak_demand_mw`, `screen_peak_demand_mw`, `screen_adequacy_requirement_mw` identical to control-P; the `retirements` rows differ ONLY by sector-1 exits absent and the admission cap's re-fill (§6 P4). 2023: the same keys identical **up to the fleet delta 2022's exits create** (every unit present in both 2023 stacks carries an identical offer and `A_g`; the requirement identical; the census differs by the exit delta alone) |
| **G6** | the sign line restored | 2022 economic exits (`retirements` rows with `reason == "economic"`) **≤ control-P's 7,333.7 MW**; 2023's **≤ 3,105.5 MW** (D58 measured the arm ABOVE both: +457.2 / +205.4) |

**ALL PASS ⇒ the full window (§6); any FAIL ⇒ the arm is killed, the remaining years are never
spent, and the kill is the session's result.** The three screen bundles are throwaway probes:
never registered, never a keeper, never quoted as a keeper number, **DELETED from `results/`
before the PR merges** (rule 29(c)); this document, the FINDING and `d78/screen_compare.json`
carry every number.

---

## 4. Cache keys (resolved through `run_capacity_hindcast.build_config` → `apply_iso_scenario_defaults` → `cache_key()`; `d78/keys_probe.json`)

| config | key | check |
|---|---|---|
| control-P, screen span 2021–2023 | **`afda79ba04cbfdbf`** | = D58's `e47fee08f5f37d6f` with D65-B reverted |
| D58's arm AND the repaired arm, screen span | **`d527c3299b8c00b5`** | the same key, by design §3.4 — the two legs live in different out-dirs and are told apart by `meta.json`'s git sha |
| control-P, full span 2021–2025 | **`15a723ba3b6dc856`** | = D58's `aef81c84c4609c76` with D65-B reverted |
| repaired arm, full span | **`bc387828f931e0ac`** | = D58's `f546407cf3489761` with D65-B reverted; no collision under `results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/` (D58's bundles deleted) |
| `ScenarioConfig()` default / bare backcast pins | unmoved by this lane | asserted by test (no field added) |

**K-a:** any collision, or a realized key ≠ its value here unexplained from the resolved config →
STOP for that leg.

---

## 5. PRE-DECLARED SIGNS — graded at full magnitude, misses included

1. **2022 stack, price, position — IDENTICAL to control-P** (G1, G2). Point: 1,370 offers,
   150,857.2 / 30,577.9 MW, 67.760 $/MW-day.
2. **2022 failing pool = 451 rows / 26,251.4 MW, exactly the control minus its sector-1 rows**
   (G3). Falsifier: any merchant row in either one-sided set.
3. **2022 admitted (`decided`) MW re-fills from the merchant pool**: control-P admitted 12,635.5
   MW in D58's reading (S4); the repaired arm admits **11.5–13.5 GW, all non-sector-1**, drawing
   on a capped pool that is 7.6 GW smaller than before only by the sector-1 rows (the rider
   mechanic of D53 / D58 §2.3). Falsifier: admitted < 10.5 GW.
4. **2022 economic exits ≤ 7,333.7 MW; 2023 ≤ 3,105.5 MW** (G6) — the rule-14 sign line a
   candidate-set gate must obey and D58's arm violated.
5. **2023**: `n_offers` **> 659** (D58's arm) and equal to control-P's 907 **minus** the units
   the exit delta removed **plus** any the delta kept; every shared unit's offer identical; the
   price **equal to control-P's 67.760 unless the census delta crosses a VRR breakpoint** (2023 sat
   on a flat segment for a 34 GW move, so the expectation is *unchanged*). Reported either way.
6. **Sector-1 uncleared, retained** (design §2.4): the gated units that do not clear in 2022 —
   from D58's control-P stack (where they DID offer) the uncleared-by-fuel totals were the
   control's own, so the pre-declared reading is **the control-P's uncleared set restricted to
   sector-1 units: 226 rows / 3,476.5 MW nameplate** (the same rows the exit decision releases;
   G3's control-only set), reported in accredited MW too.
7. **Full window (§6)**: `retire.total_gw` moves **DOWN** from the same-HEAD control (the sign
   line), by an amount bounded above by the sector-1 rows the gate releases across the window
   and below by the admission cap's re-fill; unit recall **11–13 / 20** (D58 P5's band, restated:
   a matched large sector-1 exit is no longer reachable). **Neither is a criterion.**

Rule 14's line, stated before the solve: D58 PREDECL §3 P5 already stated that PJM's control
OVER-retires, so a reduction moves the band *toward* the actual; that remains a consequence
reported at full magnitude and never evidence for the mechanism, and a worse band would not be
evidence against it.

---

## 6. The full window — only if §3 clears

**One `--start-year 2021 --end-year 2025` invocation per leg, at HEAD, PJM solo, sequential:
the repaired arm and a same-HEAD control-P** (D58's arm is dead and is not re-solved on the full
span). Registration: the arm **SUFFIXED** — `pjm-2021-2025-realized-t1h-d78-sectorgate` →
`VERDICT_MAP` `pjm-t1h-d78-sectorgate` — through `register_forecast_run.py --bundle` (the
committed hindcast sidecar + the slim `results/hindcast/<dir>/{meta,run_config,forecast_verdict}.json`
files, as D57/D62/D63 did); the bare `pjm-t1h` key is untouched; the control is never registered.
**Board lock (D65-B, sole writer of `ff-verdicts.json` / `program-status.json` until its batch
lands):** D65-B's batch did not run (two STOPs fired, `002cfa8d`); this lane treats the lock as
standing, commits the sidecar and the `VERDICT_MAP` entry, and **holds the `ff-verdicts.json`
snapshot row** unless the director has released the lock by landing time — stated in the
FINDING either way. The full-window control bundle is deleted before merge (rule 29(c)); the
arm's full bundle keeps only its slim registered files, exactly as every registered PJM T1-H run
does (`git ls-files results/hindcast/pjm-*`).

Full-window gates are §3's G1–G6 on the 2022 screen (identities exact, since the 2022 fleet is
identical) and G5/G6's fleet-delta form on 2023–2025.

---

## 7. The flip condition — the arming recommendation, PRE-STATED (D58 §5 / PREDECL-d58 §7, restated for the repaired seam)

Recommend **ARM for PJM** (`retirement_sector_gate: True` in `iso_configs._pjm_config`
`default_scenario_overrides` — **recommended, never written by this lane**: the D67-ARM lane owns
`_pjm_config` this window; a ScenarioConfig default flip is a broader act and is not recommended
from this leg) **iff ALL of**:

- **(a) purity** — the seam is closed: G1 / G2 / G5 hold on the full window's 2022 screen and in
  the fleet-delta form on 2023–2025 (the gate is once more a candidate-set partition that touches
  no second seam);
- **(b) fidelity** — G3 / G4 hold: zero sector-1 rows anywhere, every gated unit offers, the
  failing pool falls by exactly the sector-1 rows on the first screen;
- **(c) composition** — from the full window's `score.json`: window `economic` release precision
  **does not fall below the same-HEAD control's** (D58's control read 11.6 % on the pre-hunk
  bundle; the same-HEAD control's value is the bar, read before the arm is scored), and every
  admitted / decided / executed row is at a non-sector-1 plant;
- **(d) LOYO** — `retire.unit_recall_gt300` LOYO does not lose a fold the same-HEAD control holds.

Recommend **HOLD-and-route** if (a) fails (the seam is not closed, or a third seam moved).
Recommend **DECLINE** if (b) or (c) fails. **`retire.total_gw`, `false_retire`, recall and
precision are explicitly NOT conditions in either direction** (rule 14) — the sign of §5 item 7
is a consequence, reported.

---

## 8. STOPs — any one kills the arm; none is promoted past

1. **G0 miss** — D58 not reproduced to the MW at HEAD: a LIVE hunk §2 missed. Re-audit; no leg 3.
2. **Any key ≠ §4** unexplained from the resolved config, or a collision.
3. **`ScenarioConfig()` / any bare backcast or T1-H key moved by THIS lane.**
4. **A merchant row changing state on the 2022 screen** (G3) — the decoupling reaches something
   other than the sector-1 set.
5. **A gated unit absent from the 2022 offer stack while in the fleet with `A_g > 0`**, or
   present in any pipeline row (G4).
6. **The 2022 price, `requirement_mw` or `census_mw` moving by any amount** (G1/G2).
7. **A gated unit reaching the pipeline state, the floor's `new_units`, `retired`, or
   `floor_retained` by any route** — asserted by T2/T5 before any solve; a ledger violation is a
   STOP.
8. **Wall/RSS beyond the D57 envelope** (14 min / 9.3 GB per solve year).
9. **A dated-plant or retrofit unit's stack membership moving** — this lane moves the sector set
   only (design §4); the control's `price_takers_mw` returning exactly is the check.

---

## 9. Rules, stated

Rule 1 — structure first: the tariff text chooses the mechanism; every gate is an identity. Rules
13 / 14 — published market design; the sign line stated before the solve; the D58 inversion is
the defect diagnosed, not a residual chased. Rule 19 — one filter, one job: the rule-19 violation
D58 found is what this lane removes. Rule 21 — zero DOF. Rule 22 — 2021–2025 hindcast in forecast
mode; nothing outside training solved, scored or registered. Rules 24 / 25 — no tunable added or
changed; PJM's cell only. Rule 27 — local edits, exact bytes, blob-verified after every push
touching a ≥300-line file. Rule 28 — cell update (b) in PJM's shard; no row (c). Rule 29 — phase 0
zero-LP and pushed first; the screen year named from the seam's footprint; STOP-only structural
gates; the incumbent has no committed gate-on bundle, so a same-HEAD control-P is solved as the
charter names; bundles deleted before merge.

## 10. Reproduction of §2 / §4 (committed instruments)

```
uv run python docs/handoffs/d78/keys_probe.py      # -> keys_probe.json (zero LP)
```
