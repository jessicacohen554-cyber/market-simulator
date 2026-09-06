# PRE-REGISTRATION — capx D78-R: the sector-gate seam repair on the FULL 2021–2025 window, with the sign line moved to where a candidate-set gate can obey it — the DECIDED COHORT and the WINDOW TOTAL

**Lane:** capx D78-R (director r#48; pack §D78-R; D78 §8 item 2 is this lane's spec).
Predecessors: `PRECOMMIT-capx-d78-sector-gate-offer-seam-2026-09-06.md` (§6 the full-window leg
runner, already committed as `docs/handoffs/d78/run_full.sh`; §7 the flip condition) and
`FINDING-capx-d78-2026-09-06.md` (§0–§4 the exact screen, §5 the pre-declaration graded).
Branch `claude/capx-d78r-full-window-csniwn`, fresh off `origin/main` **`2485e611`**.
DATA PROFILE `pjm`. Model **Opus**. **Date:** 2026-09-06.
**Pushed BEFORE any solve.** No mechanism code is written by this lane at all — the seam repair is
already on main (#5144); this is two solves and a grading.

**NOTHING ARMS.** No new field, no default flip, no `_pjm_config` override, no parameter value, no
keeper, no marker. `retirement_sector_gate` stays default-off and un-overridden for PJM whatever
this window says. The owner decides on §7.

---

## 0. Preconditions, checked

| precondition | reading |
|---|---|
| the D78 seam repair (`exit_exempt_unit_ids`) is on main | **PASS** — #5144, merged; `retirements.py` carries the partition after `_settle_capacity_supply_clearing` |
| `retirement_sector_gate` default-off, registered at `"False"` | **PASS** (`scenarios.py`; unchanged by this lane) |
| `capacity_market_supply_clearing_by_iso` armed for PJM through `_pjm_config` | **PASS** — the bare `pjm-t1h` recipe clears the stack (D57 / Q44), which is what makes the seam observable |
| D78's screen identities G0–G5 already MET on the 2021–2023 span | **PASS** — FINDING-capx-d78 §2, §3 |
| the full-window leg runner is committed | **PASS** — `docs/handoffs/d78/run_full.sh` (D78 PRECOMMIT §6), used verbatim; this lane adds only a zero-LP differencing instrument |
| board lock: D65-B-R is sole writer of `ff-verdicts.json` / `program-status.json` until its batch registers | **STANDING** — no D65-B-R FINDING or registration is on main at `2485e611`. §9 states what this lane commits and what it holds. |
| `data/clean` present | absent at session start; rebuilt in full with `scripts/regenerate_clean.py` before any leg (as D78 did) |

**No form-4 control exists.** Rule 29(b) prefers the incumbent's committed bundle as the control.
PJM's bare `pjm-t1h` committed bundle (`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing`)
resolves at cache key **`f0e050e820c1159a`**; the same recipe at HEAD resolves at
**`15a723ba3b6dc856`** (§3). The differencing pair must share a key, so form 4 is void by
construction and the charter's same-HEAD **control-P** is solved — exactly as D78 and D74 did, and
exactly as D74 §9 item 3 anticipates for a lane in this position.

---

## 1. What will be solved — TWO legs, no code change

| leg | recipe | out-dir | key (pre-declared) |
|---|---|---|---|
| **control-P** | bare `pjm-t1h`, gate off | `results/hindcast/pjm-2021-2025-realized-t1h-d78-control-P` | **`15a723ba3b6dc856`** |
| **arm** | `--retirement-sector-gate`, seam repaired (main) | `results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate` | **`bc387828f931e0ac`** |

Both: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics`, through `docs/handoffs/d78/run_full.sh`
(`control-P` / `arm`). **Solve years {2021, 2023, 2024, 2025}; 2022 is the rule-22 bridge and is
never scored** (`HINDCAST_BRIDGE_YEARS`); forecast mode; no out-of-training year solved, scored or
registered. PJM solo, the two legs **sequential** (rule 12), years sequential within each.
**HEAD guard around each leg** (`run_full.sh` exits 90 if HEAD moves); rebase onto `origin/main`
**between** legs, never during — a rebase that changes any solve-path file re-solves the affected
leg and gets a delta re-audit as an addendum to §2. Then, per leg:
`score_capacity_hindcast.py --bundle <dir>` and `--flip-gate-extras` (LOYO / T-R10 / BLK-10),
both scorer-side, no re-solve.

**This lane writes no `src/`, `scripts/` or `tests/` code.** The only files it adds are this
document, the FINDING, `docs/handoffs/d78r/window_compare.py` (zero-LP differencing) and its JSON,
the registration sidecar, and PJM's matrix-shard cell.

---

## 2. G-DRIFT (rule 29(b)) — every solve-path hunk from D78's close `f3fb0988` to HEAD `2485e611`, classified — **VERDICT: ALL INERT for this recipe**

`git diff f3fb0988 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/run_capacity_hindcast.py scripts/lib
data/raw/_validation-source data/raw/reference` → **10 files, +598 / −750**. Hunk by hunk:

| file | hunks | class |
|---|---|---|
| `config/scenarios.py` (+72) | **miso-225**: two new fields `miso_gas_variable_transport` and `miso_seam_neighbour_anchored_ladder`, both `bool = False`; their `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS "False"` registrations (dropped at default); one `_BACKCAST_ONLY_OVERLAY_FIELDS` entry; two `TIER_TAGS` entries; and a **comment-only** block where a cross-field `__post_init__` validator was removed in favour of point-of-use guards | **INERT** — both default-off, both MISO-scoped, and each REFUSED without its MISO host flag; the `__post_init__` hunk adds no statement |
| `data/fuel/basis/miso.py` (+141) | miso-225 variable-transport wedge; built only inside the armed hub-repricing branch and raises for a non-MISO ISO | **INERT** (off, other ISO) |
| `model/interchange/miso.py` (+29) | `inject_miso_seam_ladder_prices(..., neighbour_anchored=False)`; the function returns `False` at `if iso != "MISO"` before reading the argument | **INERT** (off, other ISO) |
| `model/interchange/spec.py` (+75) | the new `MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR` / `MISO_SEAM_LADDER_NEIGHBOUR_POOLED` tables — pure module-level data, read only from the MISO injector above under the armed flag | **INERT** (unreferenced on this path) |
| `scripts/run_calibration.py` (+30/−) | miso-225's point-of-use pair guard and the `neighbour_anchored=` plumbing in `run_year` | **INERT, twice over** — (i) **off this lane's solve path entirely**: `run_capacity_hindcast.py` reaches the LP through `market_sim.pipeline.api.run_scenario` and never imports `run_calibration` (checked: no `run_calibration` symbol in its import graph); (ii) MISO-scoped and default-off regardless |
| `data/raw/reference/miso_gas_variable_transport{,.pool}.csv` (+135) | miso-225's frozen derive (rule 23) | **INERT** — read only under `miso_gas_variable_transport` |
| `data/raw/_validation-source/caiso_offer_curve_measured.json`, `caiso_offer_surface_condbinned.json`, `caiso_offer_surface_summary.csv` (±866) | CAISO offer-surface measurements | **INERT** (another ISO's inputs) |

**No hunk is LIVE.** Nothing on a PJM forecast-mode hindcast path changed between D78's close and
this lane's HEAD: the entire delta is MISO's miso-225 pair (default-off, host-flag-refused,
ISO-guarded) plus CAISO measurement files plus a backcast-only runner this path does not import.
So D78's measured control-P and arm numbers (FINDING §2–§4) are the correct brackets for §5, and a
control solve is spent here only because **form 4 is void on the key** (§0), not because a hunk is
live.

**Corroboration, not the verdict** (rule 29(b): a matched key is not a G-DRIFT verdict, and neither
is a moved one). Re-running `docs/handoffs/d78/keys_probe.py` at HEAD reproduces **all four** of
D78 PRECOMMIT §4's keys **exactly** — `15a723ba3b6dc856`, `bc387828f931e0ac`,
`afda79ba04cbfdbf`, `d527c3299b8c00b5` — so the config axis is unmoved as well, which is the
expected consequence of two optional fields registered at their defaults.

---

## 3. Cache keys (through `build_config` → `apply_iso_scenario_defaults` → `cache_key()`)

| config | key | check |
|---|---|---|
| control-P, 2021–2025 | **`15a723ba3b6dc856`** | = D78 PRECOMMIT §4; resolved at HEAD |
| arm (gate on), 2021–2025 | **`bc387828f931e0ac`** | = D78 PRECOMMIT §4; resolved at HEAD |
| collisions under `results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/` | **none** — both keys appear only in D74/D78 prose and `d78/keys_probe.json`; no committed bundle carries either |
| `ScenarioConfig()` default / every bare backcast pin | **unmoved by this lane** — no field is added or changed (no code is written) |

**K-a:** a realized key ≠ this table, unexplained from the resolved config, or any collision →
**STOP for that leg**.

---

## 4. Why G6 was the wrong sign line, and what replaces it

D78's G6 asked that **executed** economic exits not rise **in either screen year**. It fired: 2022
went 7,333.7 → 8,736.7 MW. The ledgers showed, unit by unit, that nothing leaked — the failing pool
shrank by exactly the 226 sector-1 rows (G3 exact) and **zero merchant rows changed state**. What
moved was *when*: the R-NEW admission cap is a **budget**, and removing 226 admitted-or-capped
sector-1 candidates (mostly lag-3 coal spending the 2024 budget) frees room the cap re-spends
cheapest-firm-adequacy-first on 70 capped merchant gas-steam / CHP rows with lag 1 — **the same
rows the control executes in 2023**. Decided MW moved 13,177.5 → 13,354.7, **+1.35 %**.

So a candidate-set gate **cannot** obey a per-year execution sign line: the cap re-fill moves
executions across years by construction, and D78's own PRECOMMIT §5 item 3 predicted precisely that
re-fill (band 11.5–13.5 GW, HIT at 13,354.7). The two objects it **can** obey are:

1. **The DECIDED COHORT** — *composition*, an exact identity. A gated unit is removed from the
   decision partition, so it can never be decided, executed, capped or floor-retained. Nothing
   about the cap's budget can put a sector-1 row back.
2. **The WINDOW TOTAL** — *aggregate*, immune to the timing shift that fired G6, because a row
   moved from 2023 to 2022 lands in the same window sum.

**Per-year executions are REPORTED at full magnitude and are NOT gated in either direction.**

---

## 5. THE PRE-DECLARED SIGN LINE and the STOPs — stated before any solve

All brackets below are ratios **to control-P's own realized values**, read off the leg this lane
solves — never off the pre-hunk committed stack (D74 §9 item 3's procedure). The absolute control
numbers do not exist yet and are filled in from control-P in the FINDING.

### 5.1 S1–S5 — STOPs: exact identities. Any one kills the arm.

| # | question | pass condition |
|---|---|---|
| **S1** | keys | both legs' realized keys = §3; no collision (K-a) |
| **S2** | **cohort purity** (the decided-cohort sign line, exact, **every year 2021–2025**) | **zero sector-1 rows** in the arm's `pipeline_events` (`decided`, `entry_capped`, `executed`), in `retirements[reason=="economic"]`, in `floor_retained` and in `throughput_deferred`; and **zero unknown-sector rows** in `pipeline_events` (fail-open check). A single sector-1 row anywhere in the arm's decision ledger is a leak. |
| **S3** | **the must-offer identity** (D78 G4, extended to the window) | every unit in each year's `sector_gated` set that is in the fleet with `A_g > 0` **appears in that year's `offer_stack`** at its net-ACR cap; `sector_gated` is non-empty in every year |
| **S4** | **the auction is untouched on the identical-fleet year(s)** | on every year whose *entering* fleet is identical in both legs: `n_offers`, `offered_mw`, `price_takers_mw`, `requirement_mw`, `census_mw`, clearing price, `cleared_position` and `how` identical to control-P (±0.001 MW / ±1e-6 $/MW-day), and **every `offer_stack` row identical** (unit, fuel, offer ≤1e-9, `A_g` ≤1e-6, cleared flag). The 2022 screen is that year by D78's measurement; 2021 is checked the same way. |
| **S5** | resources | wall/RSS inside the D57 envelope (≈14 min and ≈9.3 GB per solve year); no `MemoryError`. RSS is reported only if `/usr/bin/time` exists on this box (it did not for D78) |

### 5.2 S6 — the WINDOW-TOTAL sign line (the G6 replacement)

Both legs' **window totals** over 2021–2025, arm ÷ control-P:

| quantity | band | why this band |
|---|---|---|
| **window-total DECIDED MW** (Σ over years of `pipeline_events[event=="decided"]` MW) | **[0.85, 1.15]** | the direct output of the exit decision, immune to both the timing shift and the execution lag. D78 measured the move at **+1.35 %** in the single year of the gate's largest footprint (the whole 41.2 GW sector-1 set released at once). A ±15 % band is an order of magnitude above that, so it **cannot** fire on the re-fill; it still falsifies the structural question it exists for — *did the gate change the cap's budget rather than the candidate set?* — which a doubling or a halving would show. |
| **window-total EXECUTED economic MW** (Σ over years of `retirements[reason=="economic"]` MW) | **[0.80, 1.25]** | additionally exposed to window-edge truncation: a row pulled forward into the window from beyond it raises the sum without any leak. D78's 2-year screen total rose **+11.3 %** for exactly that reason (17 merchant gas-CC rows / 1,982.6 MW the control never reached inside the span). A 5-year window dilutes the one edge year, so [0.80, 1.25] brackets it with room. |

**S6 additionally requires attribution, not just a number.** Any excess above 1.00 on either
quantity must be **attributable row by row** to (i) rows the control also decides in-window but with
a later `execute_year`, or (ii) rows the control leaves `entry_capped`. An excess with rows that are
in **neither** control set is an unexplained gain and **fires S6** even inside the band.

**S6 is a STOP gate only** — it may kill the arm, it may never promote it, and it reads no residual,
no `retire.total_gw`, no recall, no precision, no `false_retire`.

### 5.3 Reported at full magnitude, gated by nothing

Per year and window: executed economic exits by year and fuel; `decided_by_execute_year`;
`entry_capped`; `floor_retained`; `throughput_deferred`; each year's clearing price, position,
offers and price-takers; the sector-1 uncleared-and-retained set; FC-3 `retire.total_gw`,
`unit_recall_gt300`, `false_retire` (raw + IS-2020), the whole FC board and any non-target
criterion that moves. **Rule 14:** none of these is a criterion in either direction, and a worse
band is not evidence against the mechanism any more than a better one is evidence for it.

### 5.4 Pre-declared expectations — graded as HIT / MISS in the FINDING, criteria for nothing

1. **S2 holds exactly**: zero sector-1 rows in every arm decision ledger, all five years.
2. **S4 holds exactly on 2021 and 2022**: the auction is byte-identical (D78 measured this on 2022).
3. **Fidelity (b)**: in every year, the arm's failing pool = control-P's **minus exactly that
   year's sector-1 rows**, with zero merchant rows in either one-sided set on the identical-fleet
   years, and every one-sided merchant row on 2023–2025 explained by the fleet delta the earlier
   exits create (a unit absent from one leg's fleet). Falsifier: an unexplained merchant row.
4. **Window-total decided MW within ±5 %** of control-P (tighter than S6's ±15 % band; the
   *expectation*, not the gate — D78's single-year move was +1.35 % and the 2-year decided total
   moved ≈ −0.3 %).
5. **Window-total executed economic MW ABOVE control-P's, by 0–15 %**, entirely from pull-forward.
   Stated in the direction D78 measured, so a *fall* is also a MISS of this expectation — and
   neither direction is a criterion.
6. **Per-year executions move EARLIER**: 2022 up, 2023 down (D78's measured pattern), with 2024–2025
   free.
7. **`retire.total_gw` moves DOWN** from control-P (PJM's control over-retires; D58 P5), and
   `unit_recall_gt300` lands **11–13 / 20** (D58 P5's band, restated: a matched large sector-1 exit
   is no longer reachable). **Neither is a criterion** (rule 14).
8. **Precision (c)**: window `economic` `plant_release_precision` **does not fall below**
   control-P's own value. This one IS a condition — see §7.

---

## 6. The four-condition grade (a)–(d) — the instrument named

Graded from the two bundles' committed ledgers and `score.json`, zero further LP, by
`docs/handoffs/d78r/window_compare.py` (written and pushed with this document):

- **(a) purity** — S4 on the identical-fleet years, and its **fleet-delta form** on 2023–2025: every
  unit present in *both* legs' `offer_stack` carries an identical offer and `A_g`; `requirement_mw`
  identical; `census_mw` differs by the exit delta **alone**; and every footprint key
  (`thermal_additions`, `renewable_additions`, `storage_additions`, `announced_derates`,
  `confirmed_derates`, `ccs_retrofits`, `entry_decided_mw_by_tech`, `peak_demand_mw`,
  `screen_peak_demand_mw`, `screen_adequacy_requirement_mw`) identical up to that delta.
  *The charter's "every non-sector-1 row byte-identical in every year" is exact only where the
  entering fleet is identical; once the arm's own exits change the fleet, byte-identity is
  impossible and the fleet-delta form is the same question asked correctly — D78 §3.4's reading.*
- **(b) fidelity** — S2 + S3 + §5.4 item 3, every year.
- **(c) composition** — window `economic` release precision ≥ control-P's, **and** every
  admitted / decided / executed row at a non-sector-1 plant (which is S2). `retire.total_gw`,
  recall and `false_retire` reported at full magnitude beside it, criteria for nothing.
- **(d) LOYO** — `retire.unit_recall_gt300` LOYO (`score.json` `loyo.holds_2of3`) **does not lose a
  fold control-P holds**; `tr10a` / `tr10b` reported.

---

## 7. The arming recommendation — PRE-STATED

**Recommend ARM for PJM** (`retirement_sector_gate: True` in `iso_configs._pjm_config`
`default_scenario_overrides` — *recommended, never written by this lane*; D67-ARM owns `_pjm_config`
this window, and a `ScenarioConfig` default flip is a broader act and is not recommended from this
leg) **iff (a), (b), (c) and (d) are ALL MET**.

**Recommend HOLD-and-route otherwise** — the charter's pre-stated fallback, and the correct verdict
whichever limb fails: (a) failing means a seam is still open and the object is a seam lane's; (b)
failing means the gate leaks and the defect is D53's; (c) failing means the released cohort is worse
selected than the control's, which is a composition question the D32/D55 precision lane owns; (d)
failing means the result does not hold out within the window.

**Any STOP of §5.1–§5.2 kills the arm outright** — the remaining grading is reported, the
recommendation is HOLD-and-route, and no gate is promoted past however right the diagnosis
(the D62 / D78 discipline).

**`retire.total_gw`, `false_retire`, recall and precision-as-a-level are explicitly NOT conditions
in either direction** (rule 14). Only precision **relative to control-P** is, through (c).

---

## 8. Registration and the board lock

The **arm** registers **SUFFIXED** — `results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate` →
`VERDICT_MAP` **`pjm-t1h-d78r-sectorgate`** — through `scripts/register_forecast_run.py --bundle`.
The bare `pjm-t1h` key is untouched. **control-P is never registered**, and its bundle is
**deleted before merge** (rule 29(c)); the arm's bundle keeps only its slim registered files
(`meta.json`, `run_config.json`, `forecast_verdict*.json` and the committed per-year
`evolution_*.json` + `score.json` sidecars every registered PJM T1-H run carries).

**Board lock:** D65-B-R is the sole writer of `frontend/data/forecast/ff-verdicts.json` and
`program-status.json` until its batch registers, and its batch is **not on main** at `2485e611`.
This lane therefore commits the bundle sidecar and the `VERDICT_MAP` entry and **HOLDS the
`ff-verdicts.json` snapshot row**, stating so in the FINDING. If the lock has been released by
landing time, the row is written then and the FINDING says so instead.

---

## 9. STOP list (the §5 gates, gathered)

1. **S1** — a realized key ≠ §3, or a collision.
2. **S2** — a sector-1 (or unknown-sector) row anywhere in the arm's decision ledger, any year.
3. **S3** — a gated unit in the fleet with `A_g > 0` absent from that year's `offer_stack`, or any
   sector-1 row reaching the pipeline / floor / retired ledgers.
4. **S4** — the price, `requirement_mw`, `census_mw` or any `offer_stack` row moving by any amount
   on a year whose entering fleet is identical in both legs.
5. **S5** — wall/RSS beyond the D57 envelope.
6. **S6** — a window total outside its §5.2 band, **or** inside the band with an excess this lane
   cannot attribute row by row to pull-forward.
7. **HEAD moved during a leg** (`run_full.sh` exit 90) — that leg is re-solved on the new HEAD after
   a §2 delta re-audit, recorded as an addendum before the re-solve.

---

## 10. Rules, stated

**Rule 1 `[R-STRUCT]`** — the mechanism is PJM's must-offer rule (D78 design §1) and the gate is
D53's ownership partition; every STOP is an identity or a bracketed sign, none is a residual, and
no gate reads FC-3. **Rule 12** — PJM solo, two legs sequential, years sequential within each.
**Rules 13 / 14** — a published market rule that regenerates per delivery year; the sign line is
stated here before the solve, its brackets are computed on this lane's own control leg, and every
number is reported at full magnitude whichever way it lands. **Rule 19 `[R-ONE-MECH]`** — exit
candidacy and capacity offering are two declarations on two parameters, one consumer set each
(the D78 repair being exercised). **Rule 21 `[R-DOF]`** — zero DOF: no parameter is identified, and
the two band widths are *gate* brackets read off D78's measurement, not model inputs. **Rule 22** —
2021–2025 forecast-mode hindcast; solve years {2021, 2023, 2024, 2025}; 2022 bridged and never
scored; nothing outside training solved, scored or registered; the holdout freeze asserted by each
run banner. **Rules 24 / 25** — no tunable added or changed (no code at all); PJM's shard cell only,
MISO's `K` untouched. **Rule 27** — no `src/` file is written; every pushed file is exact local
bytes, blob-verified after any push touching a ≥300-line file. **Rule 28** — cell update (b) in
PJM's shard; no new row (c) — no field. **Rule 29** — the screen already ran and cleared in D78;
this is its §6 full window, G-DRIFT audited hunk by hunk in §2 before any leg, STOP-only gates,
control-P deleted before merge, and every number this lane will ever cite lives in this document,
the FINDING and `docs/handoffs/d78r/window_compare.json`.

## 11. Reproduction

```
uv run python docs/handoffs/d78/keys_probe.py                       # keys at HEAD (zero LP)
bash docs/handoffs/d78/run_full.sh control-P
bash docs/handoffs/d78/run_full.sh arm --retirement-sector-gate
uv run python scripts/score_capacity_hindcast.py --bundle <dir>
uv run python scripts/score_capacity_hindcast.py --bundle <dir> --flip-gate-extras
uv run python docs/handoffs/d78r/window_compare.py --ctl <ctl-dir> --arm <arm-dir>
```
