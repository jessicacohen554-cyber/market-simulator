# PRE-COMMITMENT — capx D76 phase 1: the capacity-screen peak on the MEASURED hindcast load

**Pushed BEFORE any solve.** Lane capx D76 (director r#47, phase 1 released by the owner
2026-09-06). Branch `claude/capx-d76-peak-census-fjw289`, base `origin/main` `131291b5`.
Phase 0 record: `FINDING-capx-d76-2026-09-06.md` (six-ISO census, screen years fixed, HIT/MISS
reading, the seam and every consumer). Predicate: `FINDING-capx-d67-2026-09-06.md` §2.2 and §8(a).

**NOTHING ARMS IN THIS LANE.** The gate ships default-OFF with no `ISOConfig` override in any ISO.
Arming changes the screen operand of every hindcast bundle in the repository and therefore every
FC-1 / FC-3 T1-H row on the forecast board, so it is an owner card.

---

## 1. The mechanism, as BUILT (before the screen)

**One gate, one seam, zero scalar fields, zero free parameters.**

`capacity_screen_peak_measured_hindcast: bool = False` (`ScenarioConfig`). Armed, and only where
the LP's own branch predicate holds —

```python
config.capacity_screen_peak_measured_hindcast
and config.hindcast
and not config.is_crossover_forward_year(year)
```

— the capacity screens' seam peak (`runner.py`, top of the year loop) is the solve year's **own
measured load** instead of the weather year's load de-grown across the span by `_scale_demand`.

It **REPLACES** the de-grown peak; it never stacks on it (rule 19 `[R-ONE-MECH]`). The measured
array is loaded ONCE per year by the new shared constructor `runner._hindcast_measured_demand`, and
the LP's own `year_base_demand` **reuses that same object** — so the screens and the LP are handed
one array, not two equal-by-inspection reads, and an armed hindcast year performs exactly one
measured load, as it always did.

**Rule 13 `[R-MEASURED]` forward test.** A forecast year has no measured load, so the growth path
stays THE forecast methodology and the gate is inert there by construction — as it is for every
crossover FORWARD year and every backcast. The measured peak is a reproducible physical input for a
realized year (the same quantity, from the same loader, that the LP already dispatches), never an
outcome pinned to a residual.

**Rule 14 `[R-ACCURATE]`.** The measured load is the accurate input; the synthesized historical peak
is an estimate. Phase 0 measured what the estimate costs: −22,702 MW (−15.18 %) to +12,886 MW
(+15.42 %) on the bare T1-H recipes and −19,721 MW (−23.31 %) to +2,495 MW (+8.61 %) on the
crossover recipes, across all six ISOs.

**Rule 24 `[R-REGISTRY]` / rule 25 `[R-ISO-SCOPE]`.** Registered in `_CACHE_KEY_OPTIONAL_FIELDS`,
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (`"False"`) and `TIER_TAGS`, in the same commit as the field.
Harness flag `run_capacity_hindcast.py --capacity-screen-peak-measured-hindcast` (`--no-` is the
explicit OFF control), recorded in `run_config.json`. The gate carries **no per-ISO number and no
transferred value** — it is the same repair in every ISO because the defect is in one shared seam.

## 2. G-CTRL — form 4 is VOID, a control at HEAD is EARNED

Rule 29(b) makes the committed keeper the default control. It cannot be here, and this is settled by
measurement rather than by a "files changed" heuristic: D67 §2.2 established that
`DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` moved **0.036 → 0.064645** in the SCN-LOAD refresh, and
phase 0 §2.1 measured every ISO's rate at HEAD. **Every committed T1-H bundle is PRE-hunk on
`DEMAND_GROWTH_RATES`**, so differencing an arm against one would attribute the demand-table refresh
to this gate — the LIVE-hunk case rule 29(b) reserves a control solve for. The charter grants it
("control at HEAD … form 4 is void everywhere").

**STOP re-base, recorded before the solve.** The bare `pjm-t1h` recipe key at THIS base is
**`aaa82749a51911d5`**, not the `aef81c84c4609c76` D67 and D74 both record — `main` moved it between
their bases and this one. The value is re-based here, and the attribution is not this lane's to
make; what this lane asserts is only that **its own change moves nothing**, proven in §4 STOP 1.

## 3. THE SCREEN — PJM, screen year 2023, window 2021-2023 (rule 29 `[R-SCREEN]`)

**ISO: PJM. Screen year: 2023.** Both named by phase 0 §3.1 before any solve, on the mechanism's own
measured footprint among binding + solved years — never on a residual. PJM is the only ISO of the
six whose named screen year is not the window's last year, so it is the only genuine early screen
(2 LP solves instead of 4); it also carries the largest absolute footprint of any ISO and exercises
every consumer class in §4 of the finding (floor, backstop, entry screen, accreditation census,
CR-1 position). Phase 0 also records, against interest, that ERCOT's footprint is proportionally
larger (+15.42 %) — but ERCOT is energy-only, so its backstop is off and its I7 is the
retirement-bounded nameplate floor, reaching fewer consumers.

The window floor is fixed at 2021, so the screen is `--start-year 2021 --end-year 2023`: 2021 seeds
(its screens do not bind — no `prior_results`), **2022 is the bridge** (evolved against the seam
peak, never solved) and **2023 is the graded year**.

| leg | flag | cache key | window |
|---|---|---|---|
| CONTROL | `--no-capacity-screen-peak-measured-hindcast` | `36f6240ced74ebb5` | 2021-2023 |
| ARM | `--capacity-screen-peak-measured-hindcast` | `46971ddf07bdeb18` | 2021-2023 |

Both at the SAME HEAD, run as two concurrent invocations with separate `--out-dir` (rule 12: two
simultaneous PJM per-plant LPs is the stated cap; years sequential within each).

The measured peaks the arm must produce, from phase 0 §2.1 (computed at zero LP, fixed here before
the solve): **2022 = 148,528 MW, 2023 = 147,605 MW**. The control's seam peaks, likewise fixed:
**2022 = 135,090.596 MW, 2023 = 143,823.528 MW**. Implied deltas **+13,437.4** and **+3,781.5 MW**.

## 4. STOP GATES — structural, and a STOP gate only (rule 29)

Pre-registered here so none can be written to fit a result. A STOP **may kill the arm; it may never
promote it**, it contributes to no determination, and **not one of these is gated on a residual**.

- **STOP 1 — no pre-existing cache key moves.** All six ISOs' bare T1-H and T1-X keys, and every
  backcast keeper key, byte-identical with the field present; the explicit-OFF arm equals the bare
  key; an armed run keys distinctly. *(Already measured green before this push: six ISOs × both
  recipes, before-vs-after diff IDENTICAL; `check_cache_key_registration.py` green at 812 fields /
  267 registered.)*
- **STOP 2 — the identity.** The arm's `screen_peak_demand_mw` equals the year's MEASURED peak **to
  the MW** in every binding year: 2022 → 148,528, 2023 → 147,605, and it equals the ledger's own
  `peak_demand_mw` in every solved year. A miss of more than 0.001 MW kills the arm.
- **STOP 3 — every non-peak operand byte-identical.** The control and arm differ in the seam peak
  and in what the screens do with it, and in nothing else: fuel path, fleet vintage, outage overlay,
  every gate recorded in `run_config.json`, and the 2021 pre-screen year's ledger identical in both.
- **STOP 4 — the footprint is confined to the rows the mechanism claims.** Only quantities
  downstream of the seam peak move: `screen_*` ledger fields, retirement/entry/backstop decisions,
  the CR-1 position. The LP's own `peak_demand_mw` and `adequacy_requirement_mw` are pure functions
  of the measured load, which is identical in both arms, so they must be **identical**.

  > **CORRECTION, made before any result existed** (2026-09-06T17:01Z; the two bundles were still
  > solving and no ledger had been written, let alone read — verified: `find … -name
  > 'evolution_*.json'` returned 0). As first written this STOP also required the ledger's
  > `reserve_margin` to be identical. **That was an error in the pre-registration, and it is fixed
  > here rather than excused later.** `reserve_margin` is `accredited_firm_mw / peak − 1` computed
  > **after** evolution (`runner.py:4788`) — an EXITING-side quantity that moves with the fleet the
  > screens leave behind, which is the mechanism's own claimed footprint, not a violation of it.
  > This is precisely the mistake the D67 lane recorded against interest (its first grading script
  > carried `reserve_margin` into an entering-side gate and reported a FAIL on it; the SCRIPT was
  > corrected to the pre-registered text and the gate was not relaxed). Here the pre-registered text
  > itself is what was wrong, so the text is corrected — in the open, before the evidence — and
  > `reserve_margin` moves to §5 as REPORTED, not gated. Nothing else in §4 changes, and no STOP is
  > weakened: the two quantities that are invariant *by construction* are still required to be
  > identical to the digit.
- **STOP 5 — no non-target load-bearing criterion flips PASS → FAIL.**
- **STOP 6 — one measured load per armed year.** Asserted by test; a second read would mean the
  screens and the LP are no longer sharing one array.

## 5. PRE-DECLARED EXPECTATIONS — reported, NOT gates

Stated before the solve so they can be graded either way, and **nothing here can kill or promote the
arm**; only §4 can.

1. **Direction.** In both binding years the arm's peak is HIGHER than the control's (+13,437 MW in
   2022, +3,781 MW in 2023), so the requirement rises, the reliability floor retains MORE and the
   backstop is likelier to build. **Expect fewer economic exits and/or more forced capacity in the
   arm**, i.e. the 2023 fleet is longer than the control's.
2. **Magnitude, order of magnitude only.** PJM's 2021-2024 requirement is `peak × FPR` at
   FPR ≈ 1.0868/1.0901, so the requirement moves ≈ +14.6 GW (2022) and ≈ +4.1 GW (2023) — phase 0
   §2.1's `req Δ` column, which is the pre-solve arithmetic STOP 2's dispatch response is checked
   against for direction and order of magnitude.
3. **The D67 interaction is NOT tested here.** D67 is default-off at HEAD (Q52's arming leg has not
   landed), so this screen runs on the peak-dependent `peak × FPR` path. Once D67 arms for PJM the
   requirement leg of this gate goes to zero in every in-table DY and the remaining effect runs
   through accreditation and the CR-1 position — **stated now, not discovered later.**
4. **`reserve_margin`** (moved here by the §4 correction above): expected to RISE in the arm in
   both binding years, since a higher bar retains more firm capacity against an unchanged measured
   peak. Reported at whatever it is.
5. **What would surprise me.** A 2023 fleet that is SHORTER in the arm, or any movement in a
   renewable/storage/hydro row, would mean the peak is reaching something §4 of the finding did not
   enumerate — which is a STOP 4 failure, not a finding.

## 6. Delete before merge (rule 29(c))

The screen and control bundles are deleted from `results/` before this PR merges. This PRECOMMIT and
the FINDING carry every number the lane will ever cite; git history is the record for the bytes.

## 7. Collisions

Audited in phase 0 §4.4 and unchanged: PR #5091 (the wallclock P1 basis seed) landed docs and golden
manifests only, its code change is on `pipeline/solve.py`; the most recent `runner.py` commit
(`2c5b8242`, SCN-WS3b) has no hunk in the year-loop preamble; and the D67 lane owns
`gross_adequacy_requirement_mw`, which this lane does not touch.
