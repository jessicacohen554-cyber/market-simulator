# PRECOMMIT — SPP-57b: the Oklahoma pocket, re-issued with the constituent sets re-declared ex ante (SPP-57 R-12)

**Lane** SPP-57b · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-57b-oklahoma-pocket-973wcd` (stem `claude/spp-57b-oklahoma-pocket-sets-h3km`) ·
**Data profile** `spp` · **Charter** plan §8 W5 SPP-57b (issued r#8, `docs/multi-iso/spp-addition-plan-2026-09.md`) ·
**Predecessors** PRECOMMIT-/FINDING-spp-57 (design objects, instruments, the CSWS split, the identification
tables), PRECOMMIT-/FINDING-spp-53 (the FCITC construction), FINDING-spp-42 (keeper-2, the control),
FINDING-spp-41 table 0b (the seam moves no 2025 series).

**Pushed before any limit, price or flow of this lane is derived or solved.** Everything below is a
construction rule, a membership rule, an exclusion rule, a direction convention, a gate with its thresholds,
or arithmetic on numbers already committed by SPP-57 / SPP-53. Nothing here is revised after the result;
a miss of any declared condition is reported at full magnitude in the FINDING.

---

## 0. THE PIN, the control, the preconditions

```
dcb609f4   origin/main at PRECOMMIT time (branch cut from it)
33034499   keeper-2 git.sha (results/calibration/spp42_crosswalk_B/run_config.json)
f5926636   SPP-57's three-zone design commit (on origin/main history; its solve-path files were reverted
           by SPP-57 at 91b5d6fb, so main carries the two-zone keeper topology)
```

| precondition | check | result |
|---|---|---|
| SPP-57 landed (PR #5496): instruments under `docs/handoffs/spp57/`, both sidecars, `data/raw/eia-861/` | in tree at the pin (`tstar_n_ok.csv`, `tstar_ok_s.csv`, `psi_ok_s.csv`, `limits_2026_oklahoma_by_constraint.csv`, `spread_identification.csv`, `rtbm_bc_oklahoma_limits_2026.parquet`, `actual_lmp_hourly_area_SPP.parquet`) | **yes** |
| SPP-42 landed — keeper-2 is the control | `frontend/data/backcast/keepers/SPP.json` → `2026-09-07-spp-2-crosswalk-hydro`; bundle `spp42_crosswalk_B` + `hourly/` (system / class_hourly / class_band_hourly / storage × 2023–2025) | **yes** |
| SPP-43 (keeper-3, the screened-input re-solve) | `git ls-remote --heads origin` → no `claude/spp-43*` head; `git log origin/main --grep=SPP-43` → only the r#8 ledger commit | **NOT LANDED** at the pin — the screen differences against keeper-2 (the SPP-41 seam is INERT in 2025, §0.1 hunk 6); the full span, if reached, differences against keeper-3 if it has landed by then, else keeper-2 with the 2023 wind hunk declared LIVE and the 2023 column caveated |
| the 17 solve-path files of `f5926636` unmoved on main since its parent | `git diff --stat 91b5d6fb origin/main -- <the 17 files + the three SPP renewable-capacity CSVs>` → empty | **yes** — `git checkout f5926636 -- <files>` lands exact bytes (rule 27), then the two link ratings are edited in place |
| rule 12 concurrency | `ps` → no other `run_calibration*` process in this container (15 GB RAM, 4 cores); SPP-43 runs in its own container, so it shares no memory with this lane's solve | one per-plant solve at a time here; the desk is told rather than asked (the lane runs autonomously) |
| `data/raw` hydrated for the `spp` profile | `spp-binding-constraints/`, `spp-wind-shape/`, `eia-861/`, `zone-specific-demand/SPP`, `_validation-source` present (6.1 GB) | **yes**; `data/clean` absent → `load_zonal_shares` takes its raw-file fallback, which is byte-identical to the clean parquet by construction (`zonal_shares.py` docstring) |

**The control (rule 29(b), form 4) = keeper-2**, `2026-09-07-spp-2-crosswalk-hydro`, bundle `spp42_crosswalk_B`,
its committed `hourly/` sidecars and FINDING-spp-42 §2.2 / §3 numbers. Its recipe: the spp-1 recipe +
`--hydro-backfill-year 2024 --hydro-eia930-monthly` + the coal supply-class crosswalk CSV (LP-inert). **The screen
runs on exactly that recipe plus the topology.**

### 0.1 G-DRIFT audit (rule 29(b)) — keeper-2 `33034499` → `dcb609f4`

```
git diff --stat 33034499 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

11 files, 9,341 / −22 lines; `scripts/run_calibration*.py`, `scripts/lib`, `data/raw/reference` untouched.

| # | file | hunk | verdict for the SPP 2025 backcast | reason |
|---|---|---|---|---|
| 1 | `_validation-source/README.md`, `actual_lmp_hourly_area_SPP.parquet` | SPP-57's residual-South price sidecar + its README row | **INERT** | a validation-source record "NOT read by any scorer" and read by no loader on the solve path; it is the identification input, not a solve input |
| 2 | `_validation-source/caiso-supply-consistent-demand/*` | CAISO 2022 demand csv + provenance | **INERT** | CAISO-only artifact |
| 3 | `config/constants.py` | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO key |
| 4 | `config/fuel_trajectories.py` | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` + comments | **INERT** | CAISO key; SPP has no carbon program |
| 5 | `config/scenarios.py` | capx D76-ARM-B: `capacity_screen_peak_measured_hindcast` default `False → True`, appended to `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, plus the `__post_init__` coercion back to the frozen declaration whenever `not config.hindcast` | **INERT** | a `mode="backcast"` run is not a hindcast, so half 2 coerces the field to its frozen value and `cache_key()` drops it; the SPP plain-backcast key `989da50bbf0f99d8` is listed unmoved in the `results/cache.py` epoch note; re-proved here by `tests/regression/test_persisted_identity.py` and `solve_surface_register --diff` (§4) |
| 6 | `data/eia930/actuals.py` | SPP-41: `_screen_fuel_spike_columns` — the EIA-930 `NG:` unit-slip screen on every reader (benchmark AND the LP's delivered wind profile) | **INERT for 2025; LIVE for 2023** | FINDING-spp-41 table 0b: the ONLY input series that moves in 2021–2025 is SPP **2023** wind (−3,585.7 GWh, h3907); every 2024 / 2025 series is byte-identical. The 2025 screen is therefore form-4 valid against keeper-2. A full span (if reached) carries a LIVE 2023 hunk: the 2023 column is differenced against keeper-3 if landed, else caveated against keeper-2 (the charter's instruction), never re-solved as a control |
| 7 | `model/interchange/spec.py` | three CAISO DSW depth dicts + `IMPORT_TRANCHES_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO keys; SPP's `INTERFACE_NEIGHBORS` block byte-identical (this lane edits its `border_zones` for the third zone, which is the arm, not drift; the block is default-off) |
| 8 | `pipeline/backcast_config.py` | `_SPP_OFFER_CURVE` identity bands on the five coal keys, `econ_low_share` 0.55 | **INERT as drift** | keeper-2's OWN recorded dirty change (`run_config.json` `changed_files` / `diffstat` +29/−5) — the keeper solved WITH it |
| 9 | `results/cache.py` | the D76-ARM-B epoch docstring | **INERT** | prose only; no code line changes (the same hunk 5 governs the key) |

**All hunks INERT for a 2025 backcast ⇒ form 4 is valid for the screen: keeper-2's committed 2025 numbers are
the control and no control solve is spent.** Hunk 6 is the one LIVE-in-2023 hunk and is handled as the
charter says if the span is reached.

---

## 1. The object — unchanged from SPP-57 §1, restated in one paragraph

Same three bubbles, same chain, same residual stated at the gate: a sub-BA-defined Oklahoma zone holds
western-Oklahoma wind and OKC/Tulsa load on the same side of the `oklahoma_internal` elements, so it cannot
trap wind behind Gracemont–Anadarko or Osage–Webber Tap; what it CAN do is bound the Oklahoma bubble's own
exchange with the North on one side and the Panhandle / Arkansas–Louisiana residual on the other. The
residual South is still two disjoint pockets joined by a copperplate (SPP-54's object, not this lane's).

**What SPP-57 measured and this lane corrects:** the *union* membership rule pooled the `oklahoma_internal`
group into the N↔OK set (and the same group plus CSWS-only `other` rows into the OK↔S set). Its western-Oklahoma
delivery elements identify on BOTH spreads in opposite directions (Gracemont–Anadarko ψ = +0.030 on OK−N and
−0.032 on S−OK; Cimarron, Woodward, Cornville–Naples likewise — FINDING-spp-57 §3.3), which inflated both
pipes to 6,500 / 6,700 MW, past any flow the bubbles produce (both inert; the arm killed on legs (i)–(iii)).
The corrected construction below removes that group from both sets **by a rule written before any number
of this lane is derived**.

---

## 2. Designs (A), (C), (D) — REUSED from `f5926636`, not re-derived

| design | what | status |
|---|---|---|
| (A) the pocket | `SPP-Oklahoma` = OKGE + GRDA + WFEC + w_OK · CSWS; residual `SPP-South` = SPS + (1 − w_OK) · CSWS; fleet by the state map (OK → Oklahoma; TX NM AR LA → South); **w_OK = the MEASURED EIA-861 PSO / (PSO + SWEPCO) retail-sales ratio 0.5216 (2023) / 0.5383 (2024) / hold-last 0.5383 (2025)**; static shares N 0.5125 / OK 0.2830 / S 0.2045 | **reused verbatim** (rule 23: a measured value re-derives only on a source change) |
| (C) the identification | the three-point RT spread `spread_identification.csv` (OK−N signed mean +1.95 / +8.42 / **+0.15**; S−OK +1.15 / +3.42 / **+11.29**), the two ψ regressions (`psi_n_ok.csv` = SPP-53's own; `psi_ok_s.csv` on p_S − p_OK), the L_f table `limits_2026_oklahoma_by_constraint.csv` | **reused verbatim**; no regression is re-fitted, no L_f re-read |
| (D) registries, sidecars, tests, wind shapes, reference block | every file of `f5926636` (`_spp_config`, `zone_assignment`, `curate_zonal_shares` + the CSWS split accessor, `renewables` allocation, `interchange/spec` border zones, `meanzero` gas-hub rows, three wind-shape parquets, `calibration_reference.json` SPP block + the three renewable-capacity CSVs, `iso-topologies.json`, four test files) | **cherry-picked as exact bytes** (`git checkout f5926636 -- …`), then ONLY the two `ttc_mw` values, their citation comments, the pinned link assertions in `test_iso_config.py`, and the two `ttc_mw` numbers in `iso-topologies.json` are edited |

Zero-LP proofs owed before the screen, as SPP-57 §2.3 listed them: `validate_topology()`;
`solve_surface_register.py --diff origin/main HEAD` → 0 moved for the six keepers (rule 25);
`tests/regression/test_persisted_identity.py` green; the SPP test files green; an on-recipe
`run_year(fleet_only=True)` three-zone census (`docs/handoffs/spp57b/census.csv`) for 2023–2025 — expected
identical to SPP-57's `census.csv` because the zones, shares and recipe are unchanged and a link rating does
not enter a `fleet_only` build; a difference is reported.

---

## 3. Design (B′) — THE LINKS, the construction, the sets (the whole difference from SPP-57)

Topology: the chain `SPP-North ↔ SPP-Oklahoma ↔ SPP-South`, two symmetric `TransferLink`s, the direct
N↔S link RETIRED for the three reasons of PRECOMMIT-spp-57 §3.1 (unchanged). Direction convention (fixed):
link 1 positive flow = **N→OK**; link 2 positive flow = **OK→S**.

**The construction is SPP-53's FCITC reading, verbatim:** T*_f = L_f / |ψ_f| per identified constituent,
aggregated as the **binding-hours-weighted (2023–2025 pooled) median over the identified constituents of the
link's membership set, rounded to the nearest 100 MW**; identified iff |ψ_f| ≤ 1 and (ψ_f > 0, t ≥ 2.0)
for the forward direction or (ψ_f < 0, t ≤ −2.0) for the reverse; L_f by the SPP-53 join order (2026
limit-at-bind on the same `Constraint Name` with ≥ 100 BINDING/BREACHED intervals, else the same
`Monitored Facility`, else the registry rating, else drops out — the values already in `tstar_n_ok.csv` /
`tstar_ok_s.csv` are reused as they stand). **The named direction is data-named**: the direction whose
identified set carries more pooled binding hours; the link's TTC is that set's weighted median; the reverse
set's weighted median is reported beside it, or "none" if R1 fails there.

### 3.1 Membership — one group per link, and an exclusion rule

| link | dependent spread | membership set (constituents ≥ 263 pooled binding hours) | what is EXCLUDED, and why |
|---|---|---|---|
| **N↔OK** | p_OK − p_N (`SPPSOUTH_HUB − SPPNORTH_HUB`) | **`n_s_corridor` ALONE** — SPP-53's set, SPP-53's regression, SPP-53's L_f. The corridor-only reading is already on the record (`tstar_n_ok.csv`: weighted median 3,355 → **3,400**, FINDING-spp-57 §3.3 "corridor-only 3,355 (= SPP-53's 3,400)") and is **carried unchanged** — the number `_spp_config` holds today | `oklahoma_internal` (16 fwd / 9 rev identified) — its elements identify on both spreads |
| **OK↔S** | p_S − p_OK (p_S = the residual-South price, `actual_lmp_hourly_area_SPP.parquet`) | **`sps_tie` ALONE** — the 7 constituents `groups.py` assigns to `sps_tie` with ≥ 263 h (`SPPSPSTIES`, `SPSNMTIES`, the Potter County 345/230 kV constraint names, `TMP703_28546`), on SPP-57's `psi_ok_s.csv` regression (not re-fitted) | `oklahoma_internal` (1 fwd / 18 rev) AND the CSWS-only `other` rows (SPP-57 admitted them; this lane does not — the charter says `sps_tie` ALONE, and the PSO↔SWEPCO ties are an intra-CSWS object whose zone the split assigns by a ratio, not a measured interface) |

**The exclusion rule, written down:** a constituent that identifies (|t| ≥ 2) on BOTH zonal spreads is an
object the hub-pair decomposition attributes to whichever link's regression is run — it prices a transfer
*through* the Oklahoma hub, not *across* a bubble boundary — so it is the intra-pocket residual §1 already
states a bubble cannot hold, and it is admitted to NEITHER link. Applied as a group rule (the whole
`oklahoma_internal` group), not per element, so that no element is cherry-picked in or out by its T*. The
FINDING reports, per group, how many of the excluded constituents actually double-identify, so the rule's
coverage is visible.

### 3.2 What the record already says, disclosed rather than discovered

This lane cannot claim the OK↔S number is unread: FINDING-spp-57 §3.3 already printed the SPS-tie-set-alone
forward reading — **"10,705 → 10,700 (Potter County 345/230 kV 10,705 and 3,850, `SPSNMTIES` 11,409,
`SPPSPSTIES` 3,602; LOYO 8,395 / 10,490 / 14,796)"** — and the charter that issued this lane quotes the four
constituent T* values and adds *"expected order 3,000–4,000 from the constituents' T*, but the rule decides,
not the expectation."* Three things follow, stated before the derivation runs:

1. **The rule is not chosen with that number in view.** The construction above is SPP-53's verbatim and the
   set is the charter's; the only decisions this lane makes are the exclusion rule (§3.1, a group rule) and
   the direction convention (§3, data-named) — both fixed by SPP-57's PRECOMMIT and re-affirmed here, neither
   selectable by a result.
2. **The charter's expectation is contradicted by the record.** The weighted median over the four
   identified SPS-tie constituents does not land on the two ~3,600–3,850 readings but on Potter County's
   `TEMP50_23126` (2,231 h, ψ 0.047, 10,705) because it carries the most binding hours. If the derivation in
   §3.3 reproduces the record, the OK↔S rating is **10,700 MW, OK→S-named**, with **no reverse-identified
   constituent** (R1 fails for S→OK: 0 of 7). That is reported as the expectation being wrong, at full
   magnitude, and the rating is NOT re-cut toward the expectation.
3. **The direction the charter's parenthesis names ("the data-named (S→OK) direction") was SPP-57's
   union-set result.** Under the `sps_tie` set the data names **OK→S** (6,177 identified hours vs 0), which
   is physically coherent: the SPS ties (`SPPSPSTIES` SECI→SPS, `SPSNMTIES`, Potter County) bind on imports
   INTO the Panhandle, which in the chain is flow OK→S; the residual South reads DEARER than the Oklahoma hub
   on the annual mean in every year (§2, design C). Gate leg (i) therefore tests the OK↔S link against OK→S,
   and the FINDING says so beside SPP-57's S→OK column.

### 3.3 The derivation (run once, after this push; instrument `docs/handoffs/spp57b/aggregate_ttc_57b.py`)

Reads `spp57/tstar_n_ok.csv` and `spp57/tstar_ok_s.csv` (which already carry hours, ψ, t, L_f and T* per
constituent) and `spp57/psi_ok_s.csv` (LOYO ψ columns); filters each link to its §3.1 set; prints, per link
and per direction: n identified, pooled hours, weighted median → rounded TTC, weighted p25 / p75 and their
ratio, the LOYO weighted medians (drop 2023 / 2024 / 2025), and R1–R4 below. Writes `tstar_n_ok_57b.csv`,
`tstar_ok_s_57b.csv`. It reads no price, no limit file and no keeper output.

### 3.4 Rejection conditions per link — PRECOMMIT-spp-57 §3.3 R1–R4, unchanged, at the measured w_OK

Residual-blind bounds (2023 minimum hourly loads at w_OK = 0.5216; EIA-860 2025 ER capability):
B_plaus Oklahoma **11,085** / residual South **3,481** / North **23,300**;
B_hard Oklahoma **24,383** / residual South **13,119** / North **37,400**.

| id | condition | consequence |
|---|---|---|
| R1 | fewer than **3** identified constituents carry an L_f in the link's NAMED direction | that link's construction FAILS |
| R2 | link TTC ≥ max over its two zones of B_plaus — N↔OK: max(23,300, 11,085); OK↔S: max(11,085, 3,481) = **11,085** | rejected as a non-binding placeholder |
| R3 | link TTC ≥ the same max of B_hard | rejected a fortiori |
| R4 | weighted p75 / p25 of the identified T* > **10×** | no single transfer level; FAILS |

On FAIL of either link the topology is not landed in that state; the FINDING says so and the lane routes to
SPP-DESK. No set, threshold or dependent is re-specified. **R2 is noted before the number is derived to be
the tightest of the four for OK↔S** (the record's 10,700 sits 3.5 % under 11,085); it is applied as written.

---

## 4. The SCREEN (rule 29(a)) — year, gate, thresholds: IDENTICAL to SPP-57 §6

**Screen year = 2025**, the year of the largest `oklahoma_internal` footprint (5,822 binding hours, 0.665,
$311.80 mean |shadow|) — the mechanism's own measured footprint, NOT the residual (2025 is also keeper-2's
worst C3a year before the hydro repair, +21.7 %, which is exactly why the choice is stated on the footprint).
One `--year 2025` invocation:

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2025 \
    --out-dir results/calibration/_spp57b_screen --hydro-backfill-year 2024 --hydro-eia930-monthly
```

keeper-2's recipe unchanged except the topology (every band 1.0; served interchange; no floors / bridges /
adders; `authorized_price_tuning` NONE). The bundle is TEMPORARY: deleted before the PR (rule 29(c)); every
number cited from it lives in the FINDING and `docs/handoffs/spp57b/grade_screen_2025.log`.

**STOP gate — structural, kill-only, ex-ante thresholds (E-6). It never reads C3a / C3b.** Graded by
`spp57b/grade_screen.py` (SPP-57's instrument with the OK↔S named direction set from §3.2 item 3 and the
census path pointed at `spp57b/`).

| leg | condition | STOP if |
|---|---|---|
| (i) liveness + direction, per link | hours at bound (\|flow\| ≥ TTC − 1 MW) / 8,760; share of at-bound hours in the link's data-named direction (N↔OK: **N→OK**; OK↔S: the direction §3.3 names — the record says **OK→S**) | at bound < **5 %** OR named-direction share < **55 %** — for EITHER link |
| (ii) sign, per spread | sign of the annual mean of the modelled zonal spread (p_OK − p_N; p_S − p_OK, from `system_2025.parquet`) vs the measured RT annual mean (**+0.15**; **+11.29**) | either sign disagrees (a link that never binds yields a spread of exactly 0, which is graded as a mismatch, as SPP-57 graded it) |
| (iii) the pocket traps something | wind re-curtailment = 1 − delivered / potential (`class_hourly_2025.parquet` vs the census potential) | re-curtailment = **0.0 %** exactly (magnitude REPORTED, never gated) |
| (iv) no new unserved energy | hours with slack > 0 | any hour outside keeper-2's set **{h8507}** (2025-12-21 11:00, 89.3 MWh) — the zone may be `SPP-Oklahoma` or `SPP-South` |
| (v) fuel families within an order of magnitude | each family's TWh vs `calibration_reference.json` 2025 | any family with a real actual outside [0.1×, 10×]. **Hydro reads against the reference's EIA-923-preliminary 0.02 TWh (SPP-57 R-15, a scorer-side vintage defect keeper-2's repair replaced); it is reported and is NOT a miss** |

Control numbers (keeper-2, 2025, form 4): link 3,400 at bound 1,573 N→S / 228 S→N h (20.6 %); mean |S−N|
$1.35; negative-price hours 6; re-curtailment 0.0 % (wind 122.25 TWh); coal 83.20 / CC 32.57 / CT 22.35 /
ST 9.83 / hydro 8.82 / nuclear 15.78 / wind 122.25 TWh; load-weighted $29.97; unserved 89.3 MWh in 1 h.
Reported beside the legs, never gated: load-weighted price, zone means, negative-price hours (measured
~1,018), hours > $200, the by-class TWh, and — as SPP-57 §5.3 did — the hours at/over bound each link would
show at other ratings, from the screen's own flows (a report on the construction question, never a re-cut).

**A kill is this session's result; the full span is then not spent. A pass promotes nothing.**

### 4.1 Ex-ante expectations, written so they can be wrong (not gates)

| item | expectation | basis |
|---|---|---|
| N↔OK 3,400 | live and N→OK-dominant (order 20 % of hours at bound, ~90 % N→OK) | the killed screen's own flows at 3,400: 2,065 h at/over bound, 1,931 N→OK / 134 OK→N (FINDING-spp-57 §5.3) — with the caveat that those flows were produced with OK↔S at 6,700, so the number will move |
| OK↔S at the §3.3 rating | **NOT live**, and leg (ii) S−OK then fails by construction | if the rating reproduces the record (10,700): the killed screen shows 3 h at/over 6,000 and 0 at 6,700; the residual South's census bounds (2025 load 5,153–11,135 MW, capability ~17.9 GW) reach a 10,700 MW transfer only when it imports nearly its whole peak with its 12.8 GW of thermal off (OK→S) or exports nearly its whole capability (S→OK). Tightening N↔OK to 3,400 lowers the North energy transiting OK toward S, which moves the OK→S flow DOWN, not up |
| re-curtailment | > 0 | at 3,400 the N→OK pipe binds ~2,000 h against the North's 64 TWh of wind potential (2025 census) |
| verdict | **STOP on leg (i) for OK↔S** is the honest expectation; the screen adjudicates it | §3.2 |

The lane runs the screen despite this expectation because (a) the gate is the adjudicator, not the lane's
arithmetic; (b) the expectation depends on the killed screen's flows under a different N↔OK rating; and
(c) the LP is ~160 s. What it will NOT do on a kill: re-cut either rating, change a set, or screen a
second construction — a second arm is a new PRECOMMIT.

---

## 5. If the screen clears (every leg): the full span

One `--year 2023 2024 2025` invocation, years sequential (rule 12; the `spp` memory class at three zones
is 5.1 GB), `--out-dir results/calibration/spp57b_okpocket_B`; registered as a **CANDIDATE** (rule 15);
LOYO (rule 22) reported — every year's criterion table beside the control's at full magnitude; control =
keeper-3 if landed, else keeper-2 with the 2023 column caveated for the LIVE SPP-41 hunk (§0.1 #6);
`stamp` nothing, promote nothing (P15 is the desk's). **DOF ledger expected**: the CSWS split is a
MEASURED value, both TTCs are measured constructions, **zero tuned scalars**; the inherited
`wefor_multiplier` 0.7 residual entry carries over unchanged.

## 6. Deliverables and files

| file | change |
|---|---|
| the 17 solve-path files + 3 CSVs of `f5926636` | cherry-picked exact bytes; then `_spp_config` link ratings + comments, `test_iso_config.py` link assertions, `iso-topologies.json` `ttc_mw` |
| `docs/handoffs/spp57b/` | `aggregate_ttc_57b.py` (+ log, `tstar_*_57b.csv`), `census.py` / `census.csv`, `grade_screen.py` / `grade_screen_2025.log` |
| `docs/handoffs/FINDING-spp-57b-2026-09-07.md` | construction (B′) as executed, the OK↔S T* table, the STOP-gate table beside SPP-57's, LOYO if the span ran, DOF, the P15 recommendation |
| `docs/calibration-log/spp.md` spp-5; plan §5 row; ledger row; matrix shard `SPP.js` `measured_interface_limits` (rule 28(b)) | the record |

Not touched: any other ISO's config, maps, rows or shard; `ScenarioConfig` (no field, G8); offer bands;
`keepers/SPP.json`; `calibration-complete.json`; `docs/handoffs/spp57/` (SPP-57's record — read only);
`frontend/data/forecast/`.

## 7. What is not a rejection condition

Any comparison of a modelled price or flow with the measured one except the sign test in (ii). No band
moves, no TTC is re-cut after a solve, no set changes after a number is seen, and no gate reads a
criterion of the rubric.
