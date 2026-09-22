# PRECOMMIT — pjm-h16: PJM's coal synchronization window is placed on SCATTERED PEAK HOURS, and PJM's own meter says the fleet does not commit that way. Test `coal_sync_window_commitment_grain` (2026-09-22)

**Session:** pjm-h16 · **Branch:** `claude/pjm-h16-calibration-akyfty` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)). Twelve shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)) —
six ARM years and six same-HEAD CONTROL years, for the reason §3 states.
**Keeper under test:** `2026-09-20-pjm-h15-coalwindow-span` (2023–2025, CALIBRATED, 8/8 PASS, zero
caveats) + folded touchpoint `2026-09-20-pjm-h15-coalwindow-touchpoint` (2020–2022, NOT-YET).
Bundles `results/calibration/pjm_h15_coalwindow_{span,touchpoint}`, solved at `6de36475`.

**EVERY GATE IN §5 IS FIXED BEFORE ANY SOLVE AND IS NEVER RE-READ ONCE A NUMBER LANDS.**

---

## 0. The chartered lever, and the queue check (rule 28(a))

The handoff's **LEVER A** was `mustrun_window_commitment_grain`, *"THE WINDOW-PLACEMENT SIBLING"*,
with two conditions attached: *"(a) PJM's OWN coal online-hour-of-day census from CAMPD as the
chartering measurement, and (b) most likely a COAL-scoped sibling gate, exactly as pjm-h15 did for
the vintage."* Phase 0 satisfies (a) and the build takes (b). Both conditions bind and neither is
skipped.

PJM's shard reads `mustrun_window_commitment_grain` = `U` with the note *"the chartering measurement
is SPP's own ST_GAS online-hour-of-day census; rules 25 `[R-ISO-SCOPE]` / 28(d) mean SPP's verdict
fills no other ISO's cell."* Nothing adjudicated `R`/`I`/`G` is re-tested: the DO-NOT-REDO list
(`coal_sync_online_frac_per_year` K, `coal_mustrun_requires_measured_row` K,
`eia860_vintage_tracks_solve_year` R, `mustrun_commitment_feasibility_clip` R, the hourly seam
ladder, re-deriving `thermal_tranches_PJM.csv`) is untouched.

**LEVER B and LEVER C are deliberately NOT taken**, and §7 says why in terms rather than by silence.

---

## 1. The defect, stated as a fact about PJM's own meter

`arrays.py::_compose_min_gen_floors`, the `coal_sync_any` block, places a coal plant's
synchronization floor in `load_rank[:k]` — the top `k = round(online_frac × 8760)` **INDIVIDUAL
HOURS** by the window series. A coal plant's synchronization is a **whole-operating-day decision**.
The floor therefore inherits the diurnal shape of LOAD instead of the shape of COMMITMENT.

Measured at zero LP on PJM's own CAMPD record and the keeper's own committed system load
(`scripts/probes/pjm_h16_coalgrain_phase0.py`; 29 covered coal plants × 6 years = **173 plant-years,
152 of them reachable**). Nothing below reads a residual.

**(a) RULE 17 `[R-FLOOR-WINDOW]` — DRIVER EVIDENCE, from the class's own measured behaviour.**

| statistic (152 reachable plant-years) | min | p25 | median | p75 | max |
|---|---:|---:|---:|---:|---:|
| `p2m_online` — peak-to-mean of P(online \| hour-of-day), the PLANT's own meter | 1.0001 | 1.0051 | **1.0091** | 1.0217 | 1.3097 |
| `na_online` — overnight(00–05) on-share ÷ afternoon(14–19) on-share | 0.7876 | 0.9868 | **0.9968** | 1.0010 | 1.0270 |
| `p2m_hourwin` — the same statistic for the INCUMBENT top-k-hours window | 1.0132 | 1.1278 | **1.3011** | 1.4740 | 4.8608 |
| `p2m_daywin` — the same statistic for a whole-operating-day window | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 |

`p2m_online ≤ 1.10` on **143 of 152** plant-years and `≤ 1.05` on 136; `na_online ∈ [0.9, 1.1]` on
**145 of 152**. **When a PJM coal unit is synchronized it runs THROUGH the overnight trough.**
Against that, **the incumbent window is MORE PEAKED THAN THE PLANT ON 152 OF 152 PLANT-YEARS.**
Rule 17 clause (b) — *the hours it may bind and why* — fails in both directions: the floor binds at
the daily peak and is absent overnight **on the same committed day**.

**(b) RULE 18 `[R-PHYSICS]` — the incumbent window implies a start count no coal boiler can make.**
Implied starts = contiguous blocks in the window; metered starts = off→on transitions on the plant's
own net series.

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| metered coal starts, fleet | 238 | 290 | 303 | 302 | 302 | 334 |
| implied by the INCUMBENT hour window | 3,963 | 4,354 | 4,689 | 5,517 | 4,992 | 4,356 |
| **× the meter** | **16.7** | **15.0** | **15.5** | **18.3** | **16.5** | **13.0** |
| implied by a whole-day window | 403 | 434 | 460 | 473 | 452 | 437 |
| × the meter | 1.69 | 1.50 | 1.52 | 1.57 | 1.50 | 1.31 |

Worst single plant-year: **1,299 MW plant 6264 in 2024 — 253 implied starts against 4 measured
(63×)**; 2,600 MW plant 6166 in 2022, 241 against 5.

**(c) THE SHARP TEST — actuals only, in the hours the two grains disagree.** `only_h` = the
incumbent HOLDS and a day window RELEASES; `only_d` = a day window HOLDS and the incumbent RELEASES.

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | fleet |
|---|---:|---:|---:|---:|---:|---:|---:|
| mean metered MW, `only_h` | 273.3 | 312.2 | 277.1 | 214.9 | 247.1 | 297.2 | **267.9** |
| mean metered MW, `only_d` | 279.3 | 335.8 | 304.5 | 279.9 | 268.7 | 320.7 | **297.2** |
| online frequency, `only_h` | 0.5302 | 0.5279 | 0.5607 | 0.4689 | 0.5002 | 0.5557 | **0.5217** |
| online frequency, `only_d` | 0.6961 | 0.6957 | 0.6867 | 0.6560 | 0.6346 | 0.6677 | **0.6713** |

**+29.4 MW and +15.0 points, in all six years.** The day-only set carries higher online frequency on
**113 of 152** plant-years. 89.3 % of the incumbent window's hours are shared with the day window, so
this is a statement about the ~10.7 % that move — not a re-shuffle of the whole year.

**(d) IT IS NOT A SIZE CHANGE, on the operand that cannot hide behind a moving denominator.** Total
asserted coal floor-HOURS move **0.000 / +0.018 / +0.033 / −0.025 / −0.046 / +0.019 %** across
2020–2025 (the `round(k/24)·24` vs `k` rounding, nothing else), and per plant-year that rounding
moves **UP in 70, DOWN in 73, and is exact in 9** of 152, |Δ| ≤ 12 hours.

---

## 2. The mechanism

`coal_sync_window_commitment_grain` (`scenarios.py`, dataclass default **`False`**). Armed, the coal
window becomes `round(k/24)` whole operating days off `_commitment_day_order` — **the mechanical lift
of the incumbent's OWN ranking to the commitment period**: same series, same ordering statistic, one
grain coarser. **One seam**, `arrays.py::_compose_min_gen_floors`'s `coal_sync_any` block, reusing
the `_commitment_day_order` / `_mustrun_window_hours` helpers spp-27 already built.

- **Its OWN gate, not a widening of `mustrun_window_commitment_grain`** — three reasons, stated
  rather than assumed. (i) The gas gate's own comment says in terms that *"the COAL synchronization
  floor (`coal_sync_online_frac`) and the CT_PEAKER floors keep the hour grain — they are separate
  mechanism ids whose own conduct evidence this gate does not carry, and SPP's own ST_GAS census
  cannot speak for them (rule 25)."* (ii) **Widening the shared field would move SPP's DESIGNATED
  KEEPER**, which arms it and has coal, with no SPP lane measuring anything — rules 25 / 28(d)
  forbid exactly that. (iii) It is the pjm-h15 precedent applied unchanged, where
  `coal_sync_online_frac_per_year` was built as the coal sibling of `mustrun_online_frac_per_year`
  rather than as a widening.
- **A SEPARATE PHENOMENON from both gates it sits beside** (rule 19 `[R-ONE-MECH]`):
  `coal_sync_online_frac_per_year` (armed in the keeper) fixes the window's **SIZE**;
  `commitment_floor_window_netload` (SPP-66, default off here) fixes its **DRIVER**; this fixes
  **WHICH HOURS** the window occupies at that size on that driver. The three compose and none reads
  another.
- **Rule 21 `[R-DOF]`: ZERO free parameters.** No threshold, share, multiplier or length — the grain
  is the operating day, and `round(k/24)` is arithmetic on the size the incumbent already chose. The
  DOF ledger is carried **verbatim** at 19 entries / 6 residual.
- **Rule 13 `[R-MEASURED]`: forward-native and MODE-BLIND.** NOT registered in
  `_BACKCAST_ONLY_OVERLAY_FIELDS`, exactly like its gas sibling: the day ranking is computed from the
  model's **OWN** window series precisely as the hour ranking is, so a forecast year regenerates it
  from forward drivers and responds to changed conditions. **Nothing measured enters the placement**
  — the CAMPD census in §1 is the *evidence for* the change, never an input to it.
- **Rule 19: the window is REPLACED, never stacked.** SIZE (`coal_sync_online_frac`, pooled or
  per-year), LEVEL (`coal_sync_pmin_mw`), MEMBERSHIP and the `pmax × availability` clip are
  untouched; the two gas seams and the CT_PEAKER floors keep whatever grain their own gates give
  them.
- **Rule 23 `[R-FROZEN-DERIVE]` NOT ENGAGED.** No artifact is derived, regenerated or read that the
  control does not read. xiso-5's refusal to regenerate `thermal_tranches_PJM.csv` stands untouched
  and is not needed.
- **Rule 24 `[R-REGISTRY]` / the nyiso-119 discipline:** registered in `_CACHE_KEY_OPTIONAL_FIELDS`
  **and** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit as the field. Verified the direct
  way (pjm-h15 correction #8 — the 19 `cache_key` pin tests fail at `origin/main` before this branch
  touches anything, so they decide nothing): PJM-backcast default key
  **`c8a2ffdeca6546a6`, byte-identical to `origin/main`**; armed key **`63f2f85f710b9ca7`**, distinct.
- **Rule 25 `[R-ISO-SCOPE]`:** default off, no per-ISO number, no artifact. Every keeper in every ISO
  is byte-identical. PJM's cell enters as its own test; the base row plus a cell in all nine shards
  land in this same PR (rule 28(c)).

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — the audit says INERT, and this lane SOLVES ITS OWN CONTROL ANYWAY

Audit window `6de36475` (the keeper pair's solve SHA) → `origin/main`. **Six commits, 16 files,
+945/−152 on the backcast solve path.** Every hunk classifies INERT for a PJM backcast:

| file(s) | change | classification |
|---|---|---|
| `config/scenarios.py` | `+measured_cc_heat_rates`, `+hydro_pondage_bound`, both `bool = False`, plus their two cache-key registrations | **INERT** — default-off and absent from the PJM keeper's recipe |
| `data/fleet/{eia860,campd_bins,assembly,__init__}.py` | `measured_cc_heat_rates` threaded; the CC_REGULAR override runs only when the loader dict is non-empty, which requires the flag | **INERT** — same gate |
| `data/hydro.py` | `+load_hydro_pondage` (178 lines, pure addition) | **INERT** — reached only under `hydro_pondage_bound` |
| `pipeline/kwargs.py` | `resolve_hydro_cascade` gains `hydro_monthly_energy` + a `pondage_on` branch + a mutual-exclusion raise | **INERT** — with both gates off the `not (cascade_on or pondage_on)` early return is the identical path |
| `config/constants.py` | `+HYDRO_PONDAGE_EXTRA_NID_BY_PLANT`, NYISO key only | **INERT** — new constant, read only under the pondage gate |
| `config/solve_surface_declared.py` | three new declared drops at frozen values | **INERT to the answer** — a solve-surface fingerprint decides cache reuse, never a number |
| `runner.py` | the `resolve_hydro_cascade` kwarg, in `run_scenario_iso` | **INERT** — the FORECAST orchestrator; a backcast goes through `run_calibration.run_year` |
| `model/lp/{__init__,model}.py` | `full_extract` (default `True`); the P0 call site passes `False`, skipping post-solve *diagnostic* extraction only — no HiGHS call, no row, coefficient, bound or objective entry | **INERT** — and `_marginal_emission_rate` was deliberately **NOT** put in the skip set because it measured warm-start-class |
| `model/lp/rows.py` | `_add_bounds` accumulator replaces ~20 successive `np.concatenate` calls; same pieces, same order, same dtype; two offset reads become a running counter | **INERT** by construction |
| `pipeline/solve.py` | the same-year P1 basis seed un-nested from the cross-year gate, given its own env var + an optimality guard | **INERT** — verified at HEAD: `resolve_p1_basis_seed_default(False)` → **False** and `resolve_xyear_warmstart_default(False)` → **False**, and `_p1_seed` additionally requires the env var to be explicitly non-zero. Both knobs were already off when the keeper solved (rule 36(d), 2026-09-19, predates `6de36475`) |
| `scripts/run_calibration{,_full}.py` | the two `--no-…` flags, the container preflight | **INERT** — defaults unchanged |

**So form 4 is valid on the audit.** This lane nonetheless spends **six same-HEAD CONTROL years**,
and the reason is stated so it is not mistaken for belt-and-braces:

1. **The byte evidence behind the two PERF-C hunks is CROSS-ISO.** `e107949d` records a byte gate at
   `atol=rtol=0` on the **NEISO** keeper, six years, 16 goldens identical by content hash. That is
   real evidence and it is not PJM's. `rows.py` and `model.py` are genuine edits on the LP build and
   extract path, and rule 36(e) is this repo's own record of a basis-neutrality claim that did not
   hold when someone finally measured it.
2. **pjm-h15's G2 failed for exactly one avoidable reason**: its 2020–2022 control was a
   *regeneration* of diagnostics over a bundle carrying **no `dispatch/`**, which read
   `chp_steam × CT_CHP` at 0.0145–0.0290 against a committed family of 0.19–0.38. A same-HEAD control
   **solve**, whose bundle carries `dispatch/<y>_P1.parquet` under rule 34(a), makes the arm and the
   control diagnostics comparable **at the root** instead of disclosing an instrument defect after
   the fact.
3. **It costs no wall-clock.** Shards are parallel containers; twelve is the same elapsed time as six.
   pjm-h11 spent twelve for this same reason and it is the established shape.

**The control for every number in this lane is the same-HEAD control solve.** The committed keeper's
numbers are reported beside it as the **measured drift of HEAD against the registered keeper** —
a deliverable in its own right, since it tells PJM's next lane how far the registered numbers move
when the ISO next re-solves, armed or not.

---

## 4. What this card can and cannot reach — fixed by rule, BEFORE any arm number exists

**REACHABILITY RULE.** A D-4 `coal_mustrun` unit-conduct row is REACHABLE by a window-GRAIN change
iff **(i)** the plant-year has a window at all — `0 < coal_sync_online_frac < 0.99`
(`_COAL_SYNC_FORCE_ALL`) — **and (ii)** `binding_hours ≥ 0.5 × k`, so the window's own conduct
statistic is informative about the set the rider actually scores. Applied to the keeper's committed
rows, with no result consulted:

| control FAIL row | `floored_twh` | `binding_h` | `k` | ratio | REACHABLE? |
|---|---:|---:|---:|---:|---|
| **2023 / 1384** | 0.2031 | 2,664 | 2,952 | 0.902 | **YES** |
| **2023 / 7213** | 0.1123 | 821 | 894 | 0.918 | **YES** |
| 2021 / 7213 | 0.0003 | 23 | 2,672 | 0.009 | no — the proxy is blind |
| 2022 / 7213 | 0.0008 | 30 | 1,568 | 0.019 | no — the proxy is blind |

**UNREACHABLE BY CONSTRUCTION, named rather than absorbed:**
1. **21 of 173 covered coal plant-years sit at `frac ≥ 0.99`** — floored in all 8,760 h, no window to
   place. Byte-identical under the arm (plants 983, 2828, 2876, 3935, 3944, 6041, 8102).
2. **The two 0.0003/0.0008 TWh `7213` rows** whose binding sets are 23 and 30 hours. This charter
   makes **no claim** about them in either direction.
3. **C3a 2020 (+18.5 %) and 2022 (−10.7 %); C3b 2020 (NRMSE 0.208) and 2022 (0.245).** A coal
   commitment-window gate does not reach a price-level defect that carries **opposite signs in two
   years** — that is the handoff's LEVER B and it needs a year-specific input, not a level knob.
4. **C1 CT_PEAKER 2021 (−9.24 TWh)** — not a coal row, and the CT_PEAKER floors keep the hour grain
   by design here.
5. **The price-variance compression** (D-A diurnal amplitude 29.9–32.9 % of measured, phase correct)
   — the handoff's LEVER C, reported-only and band-free, untouched by this card.

**PREDICTED, ex ante, so the charter can be wrong in public:** row **2023/1384** improves and may
clear (window zero-share 0.4963 → 0.4499; window median 0.88 → 67.01 MW), and row **2023/7213**
**stays FAIL** — its window zero-share falls 0.7013 → 0.5923, a real 11-point fall in exposure that
does **not** cross the 0.5 the median test needs.

---

## 5. THE GATES — fixed here, never amended after a number lands

| | gate | bar | instrument |
|---|---|---|---|
| **G1** | **the arm fires** | D-2 `coal_mustrun` forced TWh differs from the same-HEAD control by > 0.01 TWh in **≥ 5 of 6** years | solver |
| **G2** | **WINDOW ONLY — scope proven on the floor ARRAY, never on another mechanism's D-2** | on a `fleet_only` A/B in every year: (a) max \|Δ `pmax_mw`\| and \|Δ `coal_sync_pmin_mw`\| **< 1e-6 MW**; (b) the **only** mechanism id whose `min_gen` cells move is `MECH_COAL_MUSTRUN` | zero LP |
| **G3** | **RULE 18 `[R-PHYSICS]`, through the REALIZED array** | implied starts of the **armed** coal floor array (contiguous binding blocks, fleet-wide) **≤ 2.0×** the fleet's metered starts, in every year | zero LP |
| **G4** | **RULE 17 SERVED on the reachable population** | (a) the two reachable rows' combined floored FAIL energy **0.3154 → ≤ 0.1577 TWh**, OR at least one clears to `pass`; **and** (b) six-year total conduct-FAIL energy **≤ the control's** | solver |
| **G5** | **no NEW conduct failure** | **zero** added D-4 `coal_mustrun` FAIL rows across the six years, against the same-HEAD control's own dispatch-backed rows | solver |

**Why G2 drops the cell-count leg pjm-h15's G5 carried.** The coal mechanism id is stamped only where
the floor **RAISES** `min_gen`, so moving hours legitimately changes which cells the mechanism owns
(another floor may already dominate a peak hour; nothing may occupy a trough hour). A bar on that
count would fail for a reason that is not a defect — the charter-scoping error pjm-h12 and pjm-h15
each made and disclosed. Scope is (a) + (b), which are exact statements; the cell count and the
asserted floor **energy** are **REPORTED, not gated**.

**G3 is a real bar, not a restatement of §1(b).** §1(b)'s 1.31–1.69× is the *pre-solve day count*.
The realized array is clipped by `pmax × availability` and max-composed with every other floor, so a
whole-day block can fragment. The control reads 13.0–18.3× on the same instrument.

---

## 6. REPORTED AT FULL MAGNITUDE, declared reported-only EX ANTE so it selects nothing

C1 by class and year, C2, C3a, C3b, C3c, C4, C6, C8, and both determinations. **None of these is a
gate and none may be read as one.**

**THE EX-ANTE PREDICTION, and rule 1 `[R-STRUCT]` stated before the solve.** ~10.7 % of the coal
window's hours move from peak hours into the overnight troughs of those same high-load days. In a
trough the model's coal is more often out of merit, so the floor is **more likely to bind**; in the
released peak hours coal was likely already dispatched above the floor, so releasing costs little.
**I therefore predict MORE forced coal energy and a WORSE C1 COAL_BIT in most years** — against a
standing PJM error that is already large and positive (+25.70 TWh in 2020, +19.62 in 2021) — with
CC_REGULAR improving as coal displaces gas. Magnitude: pjm-h15 measured the dispatch response
running **~20× behind** the asserted-floor footprint, and here the asserted *hours* barely move, so
I expect the C1 move to be small — order 0.1–1.0 TWh — and adverse in most years.

**If that is what lands, the mechanism stays in.** Rule 1 `[R-STRUCT]`: a structurally-correct
mechanism is never judged by the residual and never reverted because the residual did not move. The
basis for this card is PJM's own meter — a window more peaked than the plant on **152 of 152**
plant-years, implying **13–18×** the starts the fleet physically made — and an adverse C1 would be
rule 14 `[R-ACCURATE]`'s own diagnosis restated: the peak-scattered window was silently compensating
for something else, and that something else is the next lane's target, not this one's excuse.

**The one thing that WOULD make this not a keeper** is a G2 breach: if the arm moves `pmax_mw`, the
floor LEVEL, or a mechanism id other than `MECH_COAL_MUSTRUN`, it is not a window change and the
card is withdrawn regardless of every other number.

---

## 7. Why LEVER B and LEVER C are not taken here

**LEVER B** (the C3a/C3b 2020+2022 price object) is not refused, it is **not localised yet**. The
handoff's own reading is decisive: 2020 is **+18.5 %** mean LMP and 2022 is **−10.7 %** — opposite
signs — which argues against a single level knob and for a year-specific input. pjm-h11's seam ladder
and pjm-h12's D-2 both already touched it. Bundling a price card with a commitment-window card would
make either verdict unattributable (rule 19 `[R-ONE-MECH]`), and §4 names it as out of reach rather
than pretending this card might catch it.

**LEVER C** (the price-variance compression, D-A amplitude 29.9–32.9 % of measured with phase
correct) is the largest uncaught PJM defect and a genuinely big structural card. It is REPORTED-ONLY
and BAND-FREE, so no gate catches it and nothing here moves it. It stays queued.

---

## 8. Retrievability and retention, declared before the shards launch

Every shard pushes its **FULL** bundle — `dispatch/<y>_P1.parquet` included — to its own branch via a
`.gitignore` **negation** plus a **plain `git add`** (rule 34 `[R-SHARD-PROMOTABLE]` (a); `-f` is the
command the auto-mode classifier refuses, which cost miso-255 a re-solve). All six years the ISO
carries are solved (rule 16 `[R-ALLYEARS]`, rule 34(c)); **no year is left out.** The parent composes
the arm legs into the span (2023–2025) and the touchpoint (2020–2022), runs
`run_calibration_full.py --rebuild-benchmark` on each (pjm-h15 correction #1 — **mandatory**,
zero LP), generates `calibration_attestation.json` (correction #2), regenerates
`legitimacy_diagnostics.json` over each **composite** (pjm-h13's method note: per-year leg
diagnostics are not comparable to a composed span), scores, and registers.

**Nothing is deleted before the owner rules on promotion** (rule 31 `[R-RETAIN]`). The control
composites are **gitignored, never `rm`'d**, and the promotion question is asked explicitly in the
final report.
