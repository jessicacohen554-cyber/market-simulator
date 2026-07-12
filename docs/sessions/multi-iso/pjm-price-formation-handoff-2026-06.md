# PJM HANDOFF — price formation ($75–200 afternoon) + open issues (2026-06)

MISSION (claude.md #1/#11/#12): production-cost-grade PJM backcast. NO magic
numbers, NO curve-fitting to the residual; every input measured & forecastable.
Keeper = most STRUCTURALLY FAITHFUL run, not lowest MAE. Right structure first,
offer tuning second. A negative result is a valid deliverable.

SETUP: `uv sync`; `git config user.email noreply@anthropic.com; git config
user.name Claude`; scoring symlinks (inputs/ gitignored):
```
mkdir -p inputs/processed
ln -sf ../data/raw/reference/custom-bin-assignments.csv inputs/custom-bin-assignments.csv
ln -sf ../data/raw/reference/master-plant-registry.csv inputs/master-plant-registry.csv
ln -sf ../../data/raw/_processed-legacy/plant_emission_rates.parquet inputs/processed/plant_emission_rates.parquet
ln -sfn ../data/raw/_validation-source inputs/calibration
```
Branch merges to main & goes stale between turns: `git fetch origin`; if behind
`git checkout -B <branch> origin/main`. MEMORY: a per-plant PJM solve peaks
~8.7 GB on a 15 GB box → ONE YEAR AT A TIME (2 concurrent = silent OOM);
~7–11 min/yr. Co-opt adds reserve columns → memory-heavier; profile first.
Run pattern: clone `_pjm_retiree_run.py` (keeper runner, retiree_cems_cap=True)
per year → `_pjm_aswh_merge.py` → `_pjm_score.py` → `analyze_lmp_residual.py`.

KEEPER: `results/calibration/pjm_38` (`pjm 38 outage-regate`), config in
`pjm_38/{run_config,meta}.json`. (NOTE: the dashboard payload
`frontend/data/backcast/runs/2026-06-21-pjm-38-outage-regate.js` is NOT on the
remote — git proxy was down, too large to inline via API; regenerate with
`dashboard_add_run.py --bundle results/calibration/pjm_38` and push, else the
dashboard run entry 404s.)

========================================================================
THE ISSUE: LMP runs UNDER actual; the $75–200 afternoon regime is EMPTY
========================================================================
pjm_38 LMP load-wtd resid −1.1 / −11.4 / −19.3% (2023/24/25); the 11:00–18:00
ramp carries the gap, model ~0 hrs>$75 in Jul/Aug vs actual 57/110/124; p90+ of
the duration curve never reaches actual. PJM's real RT price = energy LMP + a
reserve price from the co-optimized ORDC; an energy-only LP cannot make that
component. ALREADY BUILT & VALIDATED (do NOT rebuild): the published vertical
step curve (`data/raw/_validation-source/pjm_ordc_curve.csv`, measured-MCP
validated), the post-solve overlay (`derive_pjm_ordc_overlay.py`, honesty gate
NEGATIVE — model holds 12–15 GW online reserve in real shortage hrs vs ~3.3 GW
breakpoint, so the step never fires; the residual is the OPPORTUNITY-COST band,
not shortage), and reserve withholding (`as_reserve_withholding`, ~inert alone).
Full context: `docs/multi-iso/pjm-reserve-ordc.md` (READ END TO END) +
`pjm-lmp-residual.md`.

========================================================================
THE LEVER: in-LP energy+reserve CO-OPTIMIZATION — with the findings I verified
========================================================================
This session investigated the build but did NOT execute it. Concrete findings
(verified by reading source), so the next session starts from them:

1. **`dispatch._build_reserve_rows` (dispatch.py:475) is ZONE-AGGREGATE, with
   NO per-gen ramp cap.** It builds `R_z` per zone with the shared-headroom row
   `sum_g P[g] + R_z <= sum_g cap[g]` (zone TOTAL eligible headroom) and a
   balance row `sum_z R_z + sum_k ORDC_k >= requirement`. The CLASS docstring
   (dispatch.py:47) claims "one reserve var per thermal generator R[g,t]" — that
   is NOT what the implementation does (`n_reserve == n_zones`). This mismatch is
   the crux.
2. **Predicted bind-gate result (probe #2, run it CHEAP first):** PJM zone-total
   headroom (~14 GW) >> requirement (~3 GW), so holding 3 GW of reserve uses FREE
   idle headroom — the headroom row is slack, its dual is 0, the reserve clears at
   $0, and the energy LMP gets NO lift. i.e. the requirement "binds" but at zero
   price. Confirm this empirically on pjm_38 (one year) before building anything.
3. **The fix that makes the requirement bind on MARGINAL headroom:** reserve must
   be limited to 10-min-deliverable (ramp) headroom so holding it displaces
   part-loaded (marginal) energy and the dual becomes the offer-curve slope over
   ~3 GW. Two options:
   - (faithful, memory-heavy) switch PJM to PER-GEN `R[g,t]` with `P[g]+R[g] <=
     cap[g]` AND `R[g] <= ramp10[g]` — the design dispatch.py:47 already names.
   - (lighter) keep zone-aggregate but cap `R_z` by the zone's deliverable
     (ramp10) headroom of ONLINE units — harder because online/P is endogenous.
   Try the per-gen path; profile memory (energy-only already nears the box).
4. **Inputs to build:** `scarcity.pjm_reserve_coopt_inputs(config, fleet, hours)`
   analogous to `ercot_reserve_coopt_inputs` (scarcity.py:586). Requirement =
   MEASURED hourly Primary requirement `pr_req_mw`/`as_up_mw` from
   `data/raw/PJM-AS/pjm_<yr>_as_up_mw.parquet` (~3.4 GW, built by
   `build_pjm_as_withholding.py`). Steps = published vertical curve via
   `load_pjm_ordc_curve` (scarcity.py:767) + `pjm_ordc_shortfall_steps`
   (scarcity.py:1002) on the (Primary, RTO) key `[(0,850),(190,300)]`. Eligible
   mask = `ercot_reserve_eligible` (generic, RESERVE_FUEL_TYPES). NOTE: ORDC step
   widths are CONSTANT `(n_ordc_steps,)` but the balance RHS is hourly `(T,)`, so
   pass `reserve_requirement(t) = as_req(t)+190` (hourly) and widths
   `[190, large_const]` — the hourly-varying PJM requirement maps cleanly.
5. **Runner branch:** runner.py:596 currently gates the co-opt path to
   `iso=="ERCOT"`. Add `elif iso=="PJM" and energy_reserve_coopt:` building from
   `pjm_reserve_coopt_inputs`; reuse `_build_reserve_rows` (after the ramp-cap
   piece is in). Set `as_reserve_withholding=True` (the co-opt pre-condition) and
   keep `retiree_cems_cap=True`.

========================================================================
PROBES (measured/forecastable only)
========================================================================
- **#2 FIRST (cheap, one year, gate):** confirm whether the measured ~3 GW
  requirement BINDS with a NONZERO dual under `_build_reserve_rows` as-is. It
  almost certainly will NOT (finding #2). If not, add the `R<=ramp10` deliverable
  cap (finding #3) and re-test. If it STILL can't bind, STOP AND REPORT
  (claude.md #11) — do NOT lower the breakpoint or inflate the penalty.
- **#1 the lever (one year):** build `pjm_reserve_coopt_inputs` + runner branch,
  solve 2024 (worst LMP year) with `energy_reserve_coopt=True` and
  `as_reserve_withholding=True`. Target: LMP −11.4% shrinks; $75–200 band
  populated; overnight +$2–6 overshoot does NOT worsen; gas/coal volumes don't
  regress. Profile memory; solve one year at a time.
- **#3 (only if data exists):** measured PJM CC body offers, CC-only — FIRST
  verify PJM publishes a 60-Day DAM offer analogue; if not, data-blocked, do NOT
  fabricate (`derive_dam_offer_hrmults.py`, `ercot-dam-offer-hrmults-2026-06.md`).

GUARDRAILS: ORDC steps VOLL/penalty-anchored from the PUBLISHED curve;
requirement = MEASURED as_req_mw. No fitted scarcity adder / lowered breakpoint /
inflated penalty. Commitment is likely NOT the lever (ERCOT prices scarcity with
commitment=False) — treat "commitment posture" as a fallback, gate behind its flag,
re-score other keepers if touched. A negative result is a valid deliverable.

========================================================================
OTHER OPEN ISSUES (sequence behind whichever the user prioritizes)
========================================================================
- **Coal over-run + over-export** (now the LARGEST structural miss after the
  outage re-gate): coal-tot +17/14/23%, net-export up to +204%. Full handoff in
  `docs/multi-iso/pjm-coal-offer-handoff-2026-06.md` (export-seam vs marginal-coal
  -offer vs CC-body levers behind a decomposition probe). NOTE: this is LINKED to
  the LMP-under here — cheap marginal coal both over-dispatches AND suppresses the
  price, so the coal fix and the price-formation lever may interact; do the coal
  decomposition probe (#0 there) before assuming co-opt alone closes the LMP gap.
- **Operational:** push the pjm_38 dashboard payload (above) once the git proxy
  recovers; this session's git proxy returned 502/413 on every push and `git
  fetch` could not resolve refs, and the commit-signing key
  (`/home/claude/.ssh/commit_signing_key.pub`) is EMPTY — so all commits went via
  the GitHub MCP API (verified by GitHub). If the proxy is still down, push via
  the API (`mcp__github__push_files`); inline payloads >~1 MB won't fit — split
  or wait for the proxy.

FIRST STEPS: (1) fetch/rebase, identity, symlinks, uv sync; confirm pjm_38 keeper
(registry) and reproduce/score it; regenerate+push its dashboard payload. (2) read
pjm-reserve-ordc.md end to end. (3) Probe #2 (bind gate) on pjm_38 BEFORE building
the co-opt. (4) build the input builder + runner branch + ramp cap; gate one year,
then all 3 + tail; register ("pjm 39 …", top-15 retention); promote only if clean.
Push to a PJM feature branch via the API if the git proxy is down; no PR unless asked.
