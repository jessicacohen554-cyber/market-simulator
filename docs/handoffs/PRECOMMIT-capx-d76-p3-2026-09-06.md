# PRE-COMMITMENT — capx D76 phase 3: the measured screen peak on the two DEFERRED ISOs (NEISO / NYISO), 2021-2023

**Pushed BEFORE any solve.** Lane capx D76 phase 3. Branch
`claude/capx-d76-p3-neiso-nyiso-pjm-sraz8b`, base `origin/main` **`0f7a4842`**.
Charter: the phase-3 card in `docs/handoffs/capx-director-prompt-pack-2026-08.md`
(r#51 §D76 PHASE 3). Protocol carried verbatim from
`PRECOMMIT-capx-d76-p2-2026-09-06.md` + Addendum 1 and
`FINDING-capx-d76-p2-2026-09-06.md`; instruments **extended, not forked**
(`docs/handoffs/d76/p2_predeclare.py`, `p2_gate.py`, `p2_consumer_probe.py`,
`p2_accreditation_probe.py`).

**NOTHING ARMS IN THIS LANE.** The exit deliverable includes an arming card
**drafted for** the director; drafting a card is not serving it.

---

## 0. SCOPE CHANGE, declared first because it is a departure from the charter

The charter's **dispatch STOP** requires D75-R-ARM merged to `main` before this
phase starts. **It is not met, and this document records that rather than
working around it.** Measured at `0f7a4842`:

| precondition | required | actual on `origin/main` |
|---|---|---|
| `git log origin/main --grep="D75-R-ARM"` | shows the FINDING commit | **no commits**; branch `claude/capx-d75r-arm-pjm` does not exist on the remote |
| `iso_configs.py::_pjm_config` | carries `pjm_vre_accreditation_vintage=True` | **absent** — the string does not occur in `iso_configs.py`; `scenarios.py:16579` has the field at its dataclass default `False` |

The ledger's own sequencing confirms it: D75-R-ARM is **"CHARTERED r#51 —
SEQUENCED: dispatch after D65-B-R's board write merges"**
(`capx-director-ledger-2026-08.md:6147`), and D65-B-R is at leg 6 of 7 on `main`
(`46cb32c3`). Owner ruling Q55 ruled ARM; the arm has not been executed.

**The lane reported the STOP, and the director then authorized, in session, a
reduced scope: run the two ISOs that do not depend on D75-R-ARM now, and defer
PJM.** So:

- **NEISO and NYISO are SOLVED and GRADED here** — four legs, not six. Neither
  ISO's verdict depends on the PJM ELCC vintage in any way: the gate under test
  is per-ISO, and `pjm_vre_accreditation_vintage` is PJM-keyed.
- **PJM is NOT re-measured.** The charter's PJM question — *is the accreditation
  census still peak-inert now that the ELCC vintage is armed?* — **cannot be
  asked at this HEAD**, because the vintage is not armed at this HEAD. A PJM leg
  solved now would re-measure phase 2's own verdict at a HEAD Q55 supersedes,
  and reporting it as "re-measured post-Q55" would be false on its face.
- **Consequence for the exit deliverable, pre-declared here.** The redrafted §9
  card will carry **five measured ISO rows and one unmeasured** (PJM: phase 2's
  verdict, explicitly stamped *conditional on the ELCC clamp, not re-measured*).
  It is **not** the six-ISO card the charter asked for, and the FINDING will say
  so in those words rather than presenting a five-of-six table as complete.

## 1. HEAD GUARD and G-DRIFT — the audit, recorded before the first LP

**HEAD = `0f7a4842`** (`origin/main` at session start; branch is fresh off it
with no commits ahead). The gate under test is unchanged on `main`:
`capacity_screen_peak_measured_hindcast: bool = False`.

**G-CTRL: form 4 is VOID and a control at HEAD is EARNED**, carried verbatim
from phase 2 §1 — every committed T1-H bundle is PRE-hunk on
`DEMAND_GROWTH_RATES`, so differencing an arm against a committed bundle would
attribute the demand-table refresh to this gate. **Both legs of every A/B are
solved at the same HEAD**, so each A/B carries zero code drift by construction.

**G-DRIFT, `e6a0402f` (phase 2's base) → `0f7a4842` (this base), hunk by hunk.**
Five non-merge commits touch the solve path
(`src/market_sim`, `scripts/run_capacity_hindcast.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference`):

| commit | change | classification for THIS lane (NEISO / NYISO) |
|---|---|---|
| `beb74f0f` | pjm-167 F1 — `eia860_vintage_tracks_solve_year: bool = False`; `paths.resolve_backcast_eia860_vintage`; one `runner.py` call site | **INERT, two independent reasons.** (a) The new resolver gives an explicit `eia860_vintage_year` **precedence 1**, so with the gate off it returns the pin unchanged. (b) Its solve-year and tracking arguments are both hard-gated on `config.mode == "backcast"`, and **both ISOs resolve `mode="forecast", hindcast=True`** (§2.1) — the backcast branch is unreachable in this lane. Default-OFF and absent from both recipes besides |
| `cd96fa26` | pjm-167 F2 — `pjm_interface_feed_admissibility_gate: bool = False`; new behaviour in `transfer_interface_limits.py` | **INERT, two independent reasons.** Every new branch is inside `if admissibility_gate:` with a `False` default, and the touched functions are `pjm_eastern_interface_hourly` / the PJM western-interface path — a **PJM** artifact neither of these ISOs reads. Absent from both recipes |
| `16210868` | capx D79 phase 1 — the solve-surface fingerprint enters the cache key (owner ruling Q54) | **INERT for key VALUES, measured not asserted.** `SURFACE_MODULES` is seven modules (`constants`, `capacity_market`, `fuel_trajectories`, `ercot_envelopes`, `plant_taxonomy`, `entry_config`, `offer_curve_base.generic`); **none was touched by any commit in this delta** — pjm-167 hit `scenarios.py` / `paths.py` / `transfer_interface_limits.py`, D78-R2 hit `retirements.py` / `evolve.py`, miso-230 hit a JSON. Corroborated by the shipped instrument: `solve_surface.moved_rows(iso)` returns **0 for all six ISOs** at this HEAD, so every name is at its declared hash and nothing new enters the key |
| `bf97317f` | capx D78-R2 STEP 0 — delete the producer-less `exempt_unit_ids` | **INERT.** The deleted parameter's default was `frozenset()` and the single deleted call-site argument was `exempt_unit_ids=frozenset()`; removing an always-empty filter is byte-identical. Same classification phase 2 gave it, re-verified at this head on the hunks themselves |
| `0e769df0` | miso-230 — `data/raw/reference/miso_ct_netload_drag.json` + derive/probe scripts | **INERT.** Still **no `src/` reader** at this head (`grep` over `src/` is empty; the only readers are `scripts/probes/`, `scripts/data/derive_*`, `scripts/legitimacy_diagnostics.py` — the BACKCAST diagnostic — and `scripts/gen_miso230_attestation.py`), so nothing a hindcast solve imports can reach it. MISO-scoped besides |

**All five hunks INERT for this lane.** Per rule 29(b) that would make G-CTRL
form 4 available; it is **not taken** anyway, for phase 2's own reason (the
`DEMAND_GROWTH_RATES` pre-hunk), and both legs of each A/B are solved at this
one HEAD.

**On the charter's own drift expectation, stated because it is now moot.** The
charter pre-warned that *"D75-R-ARM and D79 are LIVE for PJM keys by
construction — say so and pre-declare the new PJM control key."* Measured:
**D75-R-ARM is not in the delta at all** (it never merged, §0), and **D79 moved
zero rows in any ISO**, so no PJM control key moves at this HEAD and there is no
new one to pre-declare. The charter's expectation was written against a HEAD
that would carry the arm; this HEAD does not.

**A matched cache key is NOT a G-DRIFT verdict**, and none is claimed as one:
the audit above is a code-level classification of every changed hunk, and the
keys in §3 identify the legs.

## 2. WHAT THE TWO ISOs' OWN GATES DO TO THIS MECHANISM — pre-declared, before the first solve

This is the most important pre-declaration in this document, and it is made
**before** the first LP.

### 2.1 The resolved recipe, both ISOs

Both resolve `mode="forecast"`, `hindcast=True`, `weather_year=2024`,
`demand_growth_vintage=2020`, `renewable_elcc_curves=True`,
`caiso_nqc_accreditation=False`, `capacity_deliverability_limits=False`,
`locality_capacity_curves=False`, every `pjm_*` gate `False`, and
`resolve_reserve_margin_build_enabled(...) == True` — **the reserve-margin
backstop is ON in both**, which is the consumer that carried CAISO's entire
phase-2 effect. They differ in exactly the D52 pair:

| gate | NEISO | NYISO |
|---|---|---|
| `nyiso_requirement_forecast_peak` | `False` | **`True`** |
| `nyiso_requirement_vintage_factors` | `False` | **`True`** |

### 2.2 The pre-declared verdicts, written down before solving

- **NYISO is expected INERT end-to-end, exactly like PJM-at-phase-2.** Its D52
  gates make the adequacy requirement **peak-INDEPENDENT**: the shipped resolver
  evaluated at both peaks gives `req Δ = 0.0 MW` in **all three years** (§3.1,
  `req_peak_independent: true`). Phase 2 measured the requirement as the **only
  live consumer of six**; mooting it should moot the mechanism. **Pre-declared
  consequence: NYISO's whole-ledger diff moves `screen_peak_demand_mw` and
  nothing else, in every year.** A non-zero move anywhere else is a finding —
  reported, not gated — and would mean phase 2's "one live consumer" enumeration
  is incomplete.
- **NEISO is expected LIVE on the requirement**, which is the peak × FPR path
  there: `req Δ = −1,419.3 / −344.8 / +617.9 MW`. **2023 is a REVERSAL year**
  (seam 24,075.7 > measured 23,475.0), so the arm's bar is **LOWER** and the
  expectation is *more* exits / a *shorter* fleet — the same falsifiability cell
  CAISO 2023 and PJM 2025 provided in phase 2, and the reason this lane can tell
  a real mechanism from a one-way retention adder.

## 3. THE LEGS — fixed here, before the first LP

Every leg is `scripts/run_capacity_hindcast.py --vintage 2020
--entry-screen-diagnostics`, realized variant, plain hindcast.
`--entry-screen-diagnostics` is on **both** sides of every A/B so it cancels.

| leg | ISO | window | flag | cache key |
|---|---|---|---|---|
| 5-C | NEISO | 2021-2023 | `--no-capacity-screen-peak-measured-hindcast` | `ca4b163f62c4f52f` |
| 5-A | NEISO | 2021-2023 | `--capacity-screen-peak-measured-hindcast` | `69688c797d7bac80` |
| 6-C | NYISO | 2021-2023 | `--no-…` | `0641a92f61740d55` |
| 6-A | NYISO | 2021-2023 | `--…` | `236b56818bed34e9` |

Leg numbering continues phase 2's 1-4. Every control key **equals its bare
recipe key** at this head and every arm key is distinct
(`p3_predeclare.json`, `leg_keys[*].control_equals_bare == true`). Keys resolved
from the shipped resolver at HEAD and machine-emitted into a committed JSON
**before** the first solve, never typed.

**All legs run SEQUENTIALLY, one LP at a time**; rule 12's two-concurrent
allowance is deliberately not taken (15 GB box, 4 cores — phase 2's own reason).
**NO COMMIT OF ANY KIND between the two legs of an A/B** — not a rebase, not a
docs commit: phase 2 took a literal STOP 3 FAIL in PJM because two docs commits
between its legs moved the `git` block in `run_config.json` (its §5). The branch
is frozen for the duration of each A/B, and this document is pushed **before the
first LP** precisely so nothing needs committing during one.

### 3.1 The pre-declared peak and requirement moves (`p3_predeclare.json`)

| ISO | year | seam peak MW | measured MW | Δ MW | Δ % | req Δ MW | req peak-indep | binds |
|---|---|---:|---:|---:|---:|---:|---|---|
| NEISO | 2021 | 23,721.208 | 25,101.0 | −1,379.792 | −5.50 % | −1,419.286 | False | · |
| NEISO | 2022 | 23,897.849 | 24,233.0 | −335.151 | −1.38 % | −344.845 | False | Y |
| NEISO | 2023 | 24,075.667 | 23,475.0 | +600.667 | +2.56 % | +617.887 | False | Y |
| NYISO | 2021 | 27,986.311 | 30,919.0 | −2,932.689 | −9.49 % | **0.0** | **True** | · |
| NYISO | 2022 | 28,316.913 | 30,505.0 | −2,188.087 | −7.17 % | **0.0** | **True** | Y |
| NYISO | 2023 | 28,651.470 | 30,206.0 | −1,554.530 | −5.15 % | **0.0** | **True** | Y |

"binds" is phase 0 §1(e): the requirement/position block at `runner.py:2125` is
guarded on `prior_results is not None`, so 2021 writes a `screen_peak_demand_mw`
no screen consumed. **The 2022 bridge year is exercised but never solved** — it
evolves the fleet against the seam peak and writes its `screen_ledger_fields`.

**Two intake notes, recorded now so neither can be produced later as an
explanation.** (a) NEISO has no committed zonal load file for 2021-2024
(`data/raw/zone-specific-demand/NEISO/NEISO_load_hourly_<year>.csv` absent), so
both legs fall back to the system load — identically, on both sides, so it
cancels within the A/B while making NEISO's absolute peaks system-level. (b) The
phase-2 PRECOMMIT quoted NEISO's footprint as "−1,462 MW at its screen year"
from the phase-0 census; this lane's re-derivation at THIS head gives −1,379.792
(2021) / −335.151 (2022). The lane uses **its own** re-derived numbers, which
are the ones the identity is graded against.

## 4. STOP GATES — structural, and STOP gates ONLY (rule 29 `[R-SCREEN]`)

Carried **verbatim** from phase 2 §4, which is the point: the grader is the
phase-2 grader and its partition is unchanged, so nothing here can be written to
fit a phase-3 result. A STOP **may kill an arm; it may never promote one**, it
contributes to no determination, and **not one is gated on a residual.**

- **STOP 1 — no pre-existing cache key moves.** All six ISOs' bare T1-H and T1-X
  keys: explicit-OFF == bare, armed distinct. *(Already measured green at this
  head before this push, 12/12 — `p3_predeclare.json.stop1_pass`.)*
- **STOP 2 — the identity, to the MW.** The arm's `screen_peak_demand_mw` equals
  the year's PRE-DECLARED measured peak (§3.1) to the MW in every year, and
  equals the ledger's own `peak_demand_mw` in every solved year. A miss of more
  than 0.001 MW kills the arm.
- **STOP 3 — every non-peak operand byte-identical.** The nested
  `scenario_config` in `run_config.json` differs in **exactly one field, this
  lane's own gate**, and in nothing else; the five top-level per-leg bookkeeping
  keys (`cache_key`, `run_dir`, `scenario_config`, `scenario_config_source`,
  `timestamp`) are not the pre-registered object. 2021 must be identical in every
  ledger field EXCEPT `screen_peak_demand_mw` (phase 2's pre-registered
  correction, carried), and **any DECISION field moving in 2021 kills the arm**.
  *Phase 2's `git`-block failure mode is prevented here by the no-commit rule in
  §3, not by relaxing the gate: the gate is unchanged.*
- **STOP 4 — the footprint is confined to the rows the mechanism claims.** Every
  Class-A INVARIANT ledger key (§4.1) is identical in every year, and **no key
  moves that belongs to no declared class.**
- **STOP 5 — no non-target load-bearing criterion flips PASS → FAIL.** Graded
  from `scripts/score_capacity_hindcast.py` on both legs. The TARGET criterion is
  **FC-3**; every other FC row is non-target and load-bearing. Phase 2 §7
  corrected phase 1's belief that a truncated 2021-2023 window produces no scorer
  output — it scores fine — so this STOP **is** testable for both legs here, and
  is graded.
- **STOP 6 — one measured load per armed year.** Already asserted by test at HEAD
  (`tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py`); re-run,
  not re-derived.

### 4.1 THE LEDGER PARTITION (D81 rec 4) — unchanged from phase 2

The whole-ledger diff assigns **every** moved key of **every** year to one of six
pre-declared classes. A key that moves and belongs to none is reported
`UNCLASSIFIED` and **kills the arm under STOP 4** — the partition cannot be
widened after a result to absorb a surprise. Classes as coded in
`p2_gate.py`: **A INVARIANT** (`peak_demand_mw`, `adequacy_requirement_mw`,
`iso`, `year`, `ledger_version`, `mode`, `hindcast`, `bridge` — a move is a
KILL); **B SEAM** (`screen_peak_demand_mw`); **C SCREEN**
(`screen_adequacy_requirement_mw`, `screen_entering_firm_mw`,
`screen_reserve_position`, `capacity_reserve_position`, `locality_capacity`);
**D DECISION** (`retirements`, `thermal_additions`, `renewable_additions`,
`storage_additions`, `ccs_retrofits`, `floor_retained`, `entry_pipeline`,
`entry_decided_mw_by_tech`, `entry_screen_diagnostics`, `pipeline_events`,
`announced_derates`, `confirmed_derates`); **E FLEET**
(`fleet_by_fuel_after`, `fleet_by_fuel_before`, `firm_clean_mw`,
`firm_clean_accredited_mw`, `storage_firm_mw`, `storage_power_mw`, `wind_cap_mw`,
`solar_cap_mw`, `renewable_credit_applied`, `reserve_margin`); **F ACCOUNTING**
(`rps_dual`, `solve_counts`).

### 4.2 The PARTITION OF EXPECTED-MOVED FIELDS, per ISO — pre-declared

Required by the charter, and fixed here so the whole-ledger diff has a
prediction to be graded against rather than merely described:

| ISO | year | expected to move | expected identical |
|---|---|---|---|
| NEISO | 2021 | **B** `screen_peak_demand_mw` only (pre-screen year) | everything else, incl. every DECISION field |
| NEISO | 2022 | **B** + **C** `screen_adequacy_requirement_mw`, `screen_reserve_position` | A; and D/E/F unless the −344.845 MW bar change crosses a screen threshold |
| NEISO | 2023 | **B** + **C** (incl. possibly `capacity_reserve_position`); **D/E plausible** — the reversal year, with the backstop ON, is where a decision change is most likely | A always |
| NYISO | 2021 | **B** only | everything else |
| NYISO | 2022 | **B** only | everything else — the requirement is peak-independent (§2.2) |
| NYISO | 2023 | **B** only | everything else |

**These are expectations, not gates.** Only §4 can kill an arm. A NEISO decision
change is *permitted* by the partition and would be the lane's substantive
result; a NYISO move beyond **B** would be a finding against my own
pre-declaration and would be reported as one.

## 5. PRE-DECLARED EXPECTATIONS — reported, NOT gates

1. **Direction, per ISO-year.** The control's screen peak is the **seam** peak
   and the arm's is the **measured** peak, so `arm − control = −Δ`:

   | arm − control | ISO-years | expectation |
   |---|---|---|
   | **arm peak HIGHER** (Δ < 0) | NEISO 2021 (+1,379.8), 2022 (+335.2); NYISO 2021 (+2,932.7), 2022 (+2,188.1), 2023 (+1,554.5) | a HIGHER bar ⇒ **fewer economic exits / a longer fleet** |
   | **arm peak LOWER** (Δ > 0) | **NEISO 2023 (−600.7)** | a LOWER bar ⇒ **more exits / a shorter fleet** |

   NEISO 2023 is this lane's only reversal cell and is graded HIT/MISS.
2. **Magnitude, order of magnitude only.** NEISO's requirement moves by §3.1's
   `req Δ` (the peak × FPR path); **NYISO's moves by 0.0** (§2.2).
3. **FC-3 at full magnitude, REPORTED and NEVER GATED** (charter). Both ISOs'
   FC-3 rows are reported for both legs, **including where the arm is worse**.
4. **`reserve_margin`** is an EXITING-side quantity (`firm/peak − 1`, computed
   after evolution) and is Class E, REPORTED not gated — phase 1's correction,
   carried forward as written.
5. **What would surprise me.** Any movement in a Class-A key; any `UNCLASSIFIED`
   key moving; **any NYISO move beyond the SEAM field** (which would contradict
   phase 2's one-live-consumer enumeration); or a NEISO fleet that moves opposite
   to expectation 1's sign. The first two are STOP 4 kills; the last two are
   findings, reported.

## 6. Delete before merge (rule 29(c))

All four bundles are deleted from `results/hindcast/` before this PR merges. This
PRECOMMIT, the phase-3 FINDING and `docs/handoffs/d76/p3_gate_<iso>.json` +
`p3_predeclare.json` carry **every number the lane will ever cite**; git history
is the record for the bytes. An unregistered bundle directory reaching `main` is
a parity-gate RED, and `KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route for a
screen or a control.

## 7. Registration and matrix duties

**Nothing is registered on any dashboard** — a screen bundle is never registered.
Matrix duty (rule 28 `[R-MECH-MATRIX]`): this lane updates the gate's cell
verdict + evidence citation in **NEISO.js and NYISO.js only**, and touches no
other ISO's shard (rule 25 `[R-ISO-SCOPE]`). **PJM.js is NOT touched** — this
lane did not test PJM, and phase 2's cell stands as phase 2 left it.

## 8. Instruments — extended, not forked (charter)

`p2_predeclare.py` gains `--isos` over a six-ISO `SPANS` registry with the
phase-2 four as the unchanged default, so a bare invocation still reproduces
phase 2's declaration; `p2_gate.py` gains `--predeclare`; the two probes gain
`--predeclare` (and the accreditation probe now globs the bundle's single
cache-key dir instead of a pasted-in key, which is what had made it single-ISO).
No default changed, so **every phase-2 number remains reproducible from the same
files** — verified, not asserted: `p2_predeclare.py` run with its bare default at
THIS head and diffed against the copy committed before phase 2's first LP is
**byte-identical**, all eight phase-2 cache keys and all 42 peak / measured /
requirement-delta rows included. That is also an independent corroboration of the
§1 G-DRIFT verdict — if any hunk in the `e6a0402f → 0f7a4842` delta had been live
for a hindcast key or a seam peak, this diff would not be empty.

## 9. Collisions

Re-checked at this base: the D67 lane owns `gross_adequacy_requirement_mw`, which
this lane does not touch, and `capacity_adequacy_requirement_published_by_iso`
resolves `None` for both ISOs (it is PJM-keyed), so D67-ARM is inert here and
NEISO's requirement is the peak × FPR path — which is precisely why NEISO, unlike
PJM, still has a live requirement channel. The D52 gates are NYISO's own and are
`True` there by ISO default, not by anything this lane sets.
