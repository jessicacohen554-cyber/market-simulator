# HANDOFF — PJM price formation & commitment posture

## MISSION (unchanged — claude.md #1/#11/#12)
Bring the PJM backcast to production-cost grade. **NO magic numbers, NO
curve-fitting.** Every input measured and forecastable; a run is a keeper
because it is the most STRUCTURALLY FAITHFUL, not because it has the lowest MAE.
**Right market structure first, offer-curve tuning second; backcast match is not
the objective** (this is the user's stated methodology for price formation, per
`docs/multi-iso/pjm-reserve-ordc.md` §"Campaign").

## STEP 0 — DO THIS FIRST: re-gate the keeper on net-load-filtered outages
**This is a prerequisite, not optional.** The price-formation work below builds
on the *current* keeper, and the outage input under it just changed. Commit
`b0c41cb` (branch `claude/ercot-scarcity-tuning-handoff-nl1y3m`) regenerated
PJM's outage CSVs on the revealed-availability (high-NET-LOAD) filter:
capacity-weighted outage GW-days fell **~46%** (37,889→20,304), concentrated in
shoulder months (Apr −68k / Oct −63k outage-hrs), **summer binding outages
preserved** (Jul −728). Every PJM keeper was scored against the *pre-fix,
over-stated* outages. Fewer outages ⇒ more available coal/CC in the stack ⇒
**expect cooler shoulder/winter prices** — which directly moves the LMP residual
this session targets, so it must be settled before the co-opt build.
**Read `docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md` first**
(it lives on branch `claude/ercot-scarcity-tuning-handoff-nl1y3m`; on a stale
checkout: `git show origin/claude/ercot-scarcity-tuning-handoff-nl1y3m:docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md`).

- PJM consumes **BOTH** regenerated files: `data/raw/campd-outages-PJM.csv`
  (facility — PJM is the only non-ERCOT ISO with one) and
  `data/raw/campd-unit-outages-PJM.csv` (unit). Both are picked up automatically
  from `data/raw/` — **no flag change**, change ONLY the outage input.
- **Keeper to re-gate (reconcile this — the source prompt is stale):** the
  cross-ISO prompt names `pjm-35` ("cc-steam", `results/calibration/pjm_35`), but
  the registry's newest non-PROBE PJM entry is **`pjm-36` retiree-cems = bundle
  `results/calibration/pjm_37`** (this session's baseline: `pjm_35` config + the
  per-unit retiree COD fix + the within-window retiree CEMS cap). The registry is
  the source of truth — **re-gate from `pjm_37`** (retain the retiree fixes:
  re-solve via `_pjm_retiree_run.py`, `retiree_cems_cap=True`), not the older
  `pjm_35`. Confirm against `frontend/data/backcast/registry/` +
  `docs/calibration-best-so-far*.md` before solving.
- **Re-solve byte-faithfully** from the keeper's `run_config.json` (driver
  `scripts/run_calibration_full.py --iso PJM --year 2023 2024 2025`), changing
  ONLY the outage input. Don't re-tune offers/curves in the same step — isolate
  the outage effect. **Gate all 3 years AND the tail vs actuals**; report
  old-keeper vs new (mean, load-wtd LMP MAE, hrs>$200) per year. **PJM's coal
  over-run is a separate, settled issue — don't chase it here**
  (`pjm-coal-mustrun-floor.md`).
- Register on the dashboard (`calibration-report` skill, top-10 PJM retention);
  **make it the keeper only if it gates clean**, and update
  `docs/calibration-best-so-far*.md` if so. Then the price-formation work below
  proceeds on the re-gated keeper (bundle `pjm_38`).
- Memory/run guardrails are the same as below (one year at a time).

## WHY THIS SESSION (what the coal probe settled)
The prior branch (`claude/pjm-coal-mustrun-floor-clzoxa`) attacked the coal-over
and **refuted the coal must-run floor as the lever** — see
`docs/multi-iso/pjm-coal-mustrun-floor.md`. The three load-bearing findings,
all data-backed on the `pjm_37` keeper re-solved for 2025 (confound-free):

1. The PJM coal must-run floor is ALREADY CEMS-measured (`derive_thermal_tranches.py`
   `mustrun_pct` = P5 of available-CF); `COAL_MUSTRUN_BY_PLANT` is ERCOT-only.
2. In the production config (**`commitment=False`**) the coal `_mustrun` band
   carries **no forced `min_gen`** — it backs to 33% of cap at its trough and
   sits at ~zero 19% of unit-hours. There is **no coal floor forcing**; coal
   dispatches purely economically.
3. The +8.7% coal-over is a **uniform ~+2 GW merit-order level shift across the
   whole duration curve** (largest in HIGH-load hours), co-occurring with gas
   +3% and net-export **+28%** — i.e. it is the **forecast-native over-export**
   (single MISO HR 12.9 > measured) + merit order, NOT a floor artifact. Heat
   rate and the BIT passthrough are both refuted levers; do not touch coal cost.

**The coal-over is therefore not an independent frontier.** The remaining PJM
gap worth chasing is **price formation** — and the note in finding #2 of the
prior handoff stands: *coal flooring the stack cheap suppresses BOTH the coal
cycling AND the afternoon price; they are the same supply-cost/commitment
defect.* That is this session.

## THE PRICE RESIDUAL (the target)
`pjm_37` 2025: **LMP −11.8%** (model $37.81 vs actual $42.89). Localized in
`docs/multi-iso/pjm-lmp-residual.md`: the body (p50) matches; the miss is the
**$75–200 afternoon-peak regime** (11:00–18:00 ramp, peaking 16:00–17:00), with
a secondary **overnight +$2–6 overshoot** (too much committed/must-run supply
priced above the overnight clearing). The energy-only LP cannot make price >
marginal cost with adequate capacity — its price is the demand-constraint dual,
topped by the most expensive cleared offer (~$45 with cheap gas).

## THE ERCOT PLAYBOOK (verified this session — reuse it)
ERCOT solves the *identical* "perfect-foresight LP can't price scarcity" problem
with **two measured structures**, NOT commitment (ERCOT keepers run
`commitment=False` too):

1. **Scarcity TAIL → in-LP energy+reserve co-optimization** (`--energy-reserve-coopt`,
   in the ERCOT baseline command — `docs/ercot-dam-offer-hrmults-2026-06.md` §7
   reproduce, line ~225). Reserve decision vars enter the LP; the reserve
   requirement's **dual lifts the energy LMP**. The ORDC demand steps are
   **VOLL-anchored** (`0.5·VOLL·(LOLP_full+LOLP_half)`, clamped at VOLL) so the
   tail is endogenous and clamped at $5,000 (no double-count with the offer wall).
   - `src/market_sim/model/dispatch.py:475` `_build_reserve_rows(...)` — **generic,
     ISO-agnostic** (takes `reserve_requirement`, `reserve_eligible`,
     `ordc_penalties`, `ordc_step_widths`). This is the reusable core.
   - `src/market_sim/results/scarcity.py:586` `ercot_reserve_coopt_inputs`,
     `:451` `ercot_ordc_demand_steps`, `:437` `ercot_reserve_eligible` — the
     **ERCOT-specific** input builders the runner calls.
   - `src/market_sim/runner.py:596` — gated `if energy_reserve_coopt and iso == "ERCOT"`.
2. **Price BODY → measured DAM offer-curve heat-rate multipliers**
   (`docs/ercot-dam-offer-hrmults-2026-06.md`, `scripts/derive_dam_offer_hrmults.py`,
   `data/raw/_validation-source/offer_curve_dam_hrmults.json`). Each thermal band's
   `mult` is **measured from QSE-submitted 60-Day DAM energy offers** (`price /
   fuel / base_HR`), pooled 2023-25, capacity-weighted — *not* fit to the LMP.
   - The **CC-only** measured variant (`--only-groups CC_REGULAR,CC_CHP`, bundle
     `ercot_dam_offers_cconly_3yr`, run129) is the **defensible measured change**;
     the full-gas override craters ST_GAS/CT via the CT↔ST coupling (a swing-lever
     vs literal-offer conflict). **Lesson for PJM: land CC measured offers, leave
     the swing classes on the calibrated curve.**
   - **Coal excluded by design**: ERCOT coal Min Gen Cost is 2–3× HR (non-fuel
     dominated), but the model prices coal cheap *on purpose* (must-run =
     take-or-pay **sunk** fuel) so it stays in merit. Feeding measured coal
     collapses coal volume. **This is exactly why the coal-over is not a coal-cost
     fix** — confirms the prior session.

## WHAT'S ALREADY BUILT FOR PJM (don't rebuild)
- **Published ORDC step curve** (cited, measured-MCP-validated):
  `data/raw/_validation-source/pjm_ordc_curve.csv`, `docs/multi-iso/pjm-reserve-curve-source.md`.
  Vertical two-step `$850 (R<REQ) / $300 (REQ≤R<REQ+190) / $0`, three nested
  products (Synchronized⊆Primary⊆30-min), stable across 2023–26 (no regime switch).
- **Post-solve overlay** (`scripts/derive_pjm_ordc_overlay.py`, `scarcity.py`
  PJM section: `:830 pjm_reserve_cascade_mcp`, `:1048 pjm_online_reserve`). The
  **honesty gate is already run and is NEGATIVE**: the model holds 12–15 GW
  online reserve in PJM's real RT shortage hours (~5× the ~3.3 GW breakpoint), so
  the vertical step never fires — the residual is the **opportunity-cost reserve
  price (6–13 GW band)**, not the shortage/penalty regime. The post-solve overlay
  **cannot** reach the $75–200 band. (`docs/multi-iso/pjm-reserve-ordc.md` §honesty gate.)
- **Reserve withholding** (`as_reserve_withholding`, bundle `pjm_27_aswh`): the
  measured ~3 GW Primary Reserve removed from top-of-merit headroom **pre-solve**.
  Result: **~inert (~$0.1)** because it removes *idle* CT/oil headroom, not the
  *marginal* CC headroom that sets price. **Necessary structure, not sufficient.**
- **The campaign is already written**: `docs/multi-iso/pjm-reserve-ordc.md`
  §"Campaign" lays out Phase 1 (commitment posture) → Phase 2 (energy+reserve
  co-optimization, *the lever that prices the band*) → Phase 3 (retune offers).

## THE TWO GAPS TO IMPLEMENT
1. **PJM co-opt input builder + runner branch** (Phase 2 — the main lever):
   - Add `scarcity.pjm_reserve_coopt_inputs(config, fleet_arrays, hours)` →
     `(requirement, eligible, penalties, step_widths)`, analogous to
     `ercot_reserve_coopt_inputs` but built from PJM's **published vertical step
     curve** (`pjm_ordc_curve.csv`) and the **measured Primary requirement**
     (`as_req_mw`, the same series `build_pjm_as_withholding.py` already loads).
     Reserve-eligible = the thermal pool; the requirement must bind on
     **10-min-deliverable / synchronized** headroom, not total headroom — else it
     never binds (the honesty gate showed 14 GW total online vs 3 GW requirement).
     **Check whether `dispatch._build_reserve_rows` already caps reserve to a
     per-gen ramp slice; if not, that cap (`R[g] ≤ ramp10[g]`) is the piece that
     makes PJM's requirement bind** (`pjm-reserve-ordc.md` Phase 2 spells this out).
   - Add the runner branch: `elif iso == "PJM" and energy_reserve_coopt:` at
     `runner.py:596` calling the new builder. The generic `_build_reserve_rows`
     is reused as-is.
   - Forecast requirement already exists: `pjm_primary_reserve_requirement()`
     (≈1.5×LSC) + `largest_single_contingency_mw()`.
2. **Measured PJM body offers (Phase 3, secondary):** the ERCOT win was measured
   **CC** offers. **First check data availability** — does PJM publish a 60-Day
   DAM offer analogue (PJM markets are less transparent than ERCOT's 60-day
   disclosure)? If not, this phase is data-blocked and the body must come from
   co-opt's opportunity-cost lift alone. Do NOT fabricate a PJM offer curve.

## PRIORITIZED PROBES (all measured/forecastable)
- **#1 (the lever): PJM energy+reserve co-optimization.** Build gap #1 above on
  the `pjm_37` keeper config (keep `retiree_cems_cap=True` — clone
  `_pjm_retiree_run.py`, add `energy_reserve_coopt=True`). Hold the **measured**
  ~3 GW Primary requirement on the **marginal** (cheapest-opportunity-cost)
  deliverable headroom; the dual lifts the afternoon LMP by the offer-curve slope
  over ~3 GW — priced *inside* the solve, no overlay, no haircut. Withholding
  (`as_reserve_withholding=True`) is its **pre-condition** (removes the must-hold
  MW from the energy stack) — turn both on. Target: 2025 LMP −11.8% → less under;
  the $75–200 afternoon band populated; **overnight overshoot must NOT worsen**
  (watch the +$2–6); volumes/gates must not regress (gas stays PASS).
- **#2 (gate FIRST, then build): does the requirement bind?** Before a full
  3-year solve, confirm on one year that the PJM reserve requirement actually
  binds on deliverable headroom in the afternoon (the honesty gate's whole point
  — total online reserve is 5× the requirement). If it doesn't bind without the
  10-min ramp cap, add the cap. If it *still* can't bind, **stop and report**
  (claude.md #11) — do not lower the breakpoint or inflate the penalty.
- **#3 (only if data exists): measured PJM CC offers**, ERCOT-style, CC-only.
  Leave coal and the swing classes on the calibrated curve.

## GUARDRAILS / HONESTY GATES
- **Co-opt is memory-heavy at PJM plant-level** — the reserve `R[g,t]` columns
  add to an energy-only solve that already nears the 15 GB box. **Solve ONE YEAR
  AT A TIME; profile memory first** (`pjm-reserve-ordc.md` Phase 2 note).
- **No fitted scarcity adder, no fitted penalty, no lowered breakpoint.** The
  ORDC steps are VOLL-anchored from the published curve; the requirement is
  measured `as_req_mw`. If the structure can't price the band honestly, report
  that — a negative result is a valid deliverable (as the post-solve overlay and
  the coal-floor probe both were).
- **Commitment is likely NOT the lever** — ERCOT prices scarcity with
  `commitment=False`. The `pjm-reserve-ordc.md` "Phase 1 commitment posture"
  framing predates the co-opt build; treat commitment as a *fallback* only if
  co-opt's marginal-headroom lift proves insufficient. If you do test it,
  `commitment_enabled=True` runs the P0/P1/P2 screen (`commitment.py`); it adds
  startup/min-run economics to CC/CT (coal/nuclear always committed). It is a big,
  memory-heavy, cross-ISO change — gate it behind the flag and re-score keepers.
- **Don't chase the over-export or the coal-over** (settled this session as
  forecast-native / merit-order). Co-opt may shrink the over-export as a side
  effect (gas held as reserve exports less) — verify, don't target.

## ENVIRONMENT / GOTCHAS (carried forward, verified)
- Setup: `uv sync`; `git config user.email noreply@anthropic.com && git config
  user.name Claude`. Scoring symlinks (inputs/ gitignored):
  ```
  mkdir -p inputs/processed
  ln -sf ../data/raw/reference/custom-bin-assignments.csv inputs/custom-bin-assignments.csv
  ln -sf ../data/raw/reference/master-plant-registry.csv inputs/master-plant-registry.csv
  ln -sf ../../data/raw/_processed-legacy/plant_emission_rates.parquet inputs/processed/plant_emission_rates.parquet
  ln -sfn ../data/raw/_validation-source inputs/calibration
  ```
- **Branch rebase**: the working branch merges to main and goes stale between
  turns. `git fetch origin`; if your branch is behind, `git checkout -B <branch>
  origin/main` (your earlier commits are already in main once merged). This
  session the doc commit was already in origin/main and main had advanced 35
  commits.
- **MEMORY**: a per-plant PJM solve peaks ~8.7 GB; box is 15 GB → **RUN ONE YEAR
  AT A TIME** (two concurrent = silent OOM). One PJM year ~11 min. Co-opt will
  raise this — profile.
- **RUN PATTERN** (runner/scorer/merge under `scripts/probes/`):
  ```
  for y in 2023 2024 2025; do uv run python scripts/probes/<runner>.py $y results/calibration/<name>_$y; done
  uv run python scripts/probes/_pjm_aswh_merge.py results/calibration/<name> results/calibration/<name>_202{3,4,5}
  uv run python scripts/probes/_pjm_score.py <name>
  ```
  Clone `_pjm_retiree_run.py` (the `pjm_37` keeper runner, `retiree_cems_cap=True`)
  for any new PJM probe so the keeper baseline holds; add the new flags by keyword.
- **DASHBOARD**: `calibration-report` skill. Next dashboard label: **"pjm 38 …"**;
  next bundle dir: **`pjm_38`** (the prior session's dir/label diverged by one —
  do not compound it). Retention = top 10 PJM.
- `git add` aborts ALL pathspecs if ANY is missing; stage existing files
  separately from `git rm`'d deletions. Commits are SSH-signed (local `%G?` = N
  is a false positive; verifies on GitHub).

## KEY FILES (verified line refs)
- `src/market_sim/model/dispatch.py:475` `_build_reserve_rows` (generic reserve
  rows — reuse), `:601` `build_constraints`, `:1130` `solve_dispatch`.
- `src/market_sim/results/scarcity.py`: `:437/451/586` ERCOT co-opt input
  builders (the template), `:830 pjm_reserve_cascade_mcp`, `:1048
  pjm_online_reserve`, `:310 reserve_headroom` (online/offline split, ISO-generic).
- `src/market_sim/runner.py:596` co-opt wiring (ERCOT-gated — add the PJM branch).
- `src/market_sim/config/scenarios.py`: `energy_reserve_coopt`,
  `as_reserve_withholding`, `commitment_enabled`, `commitment_screen_coal`.
- `scripts/derive_pjm_ordc_overlay.py` (post-solve overlay + `--validate-mcp` /
  `--diagnostic` honesty gate), `scripts/build_pjm_as_withholding.py` (measured
  `as_req_mw` loader — reuse for the co-opt requirement).
- `scripts/probes/_pjm_{retiree_run,aswh_run,aswh_merge,score}.py`.
- `scripts/derive_dam_offer_hrmults.py` + `docs/ercot-dam-offer-hrmults-2026-06.md`
  (the measured-offer template, if PJM DAM offer data exists).
- DOCS: `docs/multi-iso/pjm-reserve-ordc.md` (the campaign + honesty gate — READ
  FIRST), `docs/multi-iso/pjm-lmp-residual.md` (the residual localization),
  `docs/multi-iso/pjm-reserve-curve-source.md` (curve citations),
  `docs/ordc-overlay.md` (ERCOT post-solve analogue),
  `docs/multi-iso/pjm-coal-mustrun-floor.md` (why the coal-over is not the frontier).

## FIRST STEPS
1. `git fetch origin`; recreate branch from `origin/main`; set git identity; make
   the symlinks; `uv sync`. Confirm `b0c41cb`'s regenerated PJM outage CSVs are in
   `data/raw/` (they're on main).
2. **STEP 0 — the outage re-gate (prerequisite, above).** Re-gate `pjm_37` on the
   net-load-filtered outages, all 3 years + tail; register; promote to keeper only
   if clean. The price-formation work then builds on whatever keeper this yields.
3. **Read `docs/multi-iso/pjm-reserve-ordc.md` end to end** — it is the campaign
   spec; this handoff is its execution plan with the ERCOT machinery mapped.
4. Probe #2 FIRST (the bind gate, one year, cheap): instrument whether the
   measured PJM Primary requirement binds on deliverable headroom in the afternoon
   under the existing `_build_reserve_rows`. Decide if the 10-min ramp cap is
   needed.
4. Then build gap #1 (`pjm_reserve_coopt_inputs` + runner PJM branch), solve 2025
   (`energy_reserve_coopt=True`, `as_reserve_withholding=True`, bundle `pjm_38`),
   score. Target: LMP −11.8% shrinks, afternoon $75–200 band populated, overnight
   not worse, gas/coal volumes don't regress.
