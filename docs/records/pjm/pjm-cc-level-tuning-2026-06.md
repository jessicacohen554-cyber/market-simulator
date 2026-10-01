# Handoff — PJM CC offer-level / cycling tuning direction (research, no reruns)

> **Status (2026-06-25): the NYISO instance of this offer-level lever is DONE.**
> The `nyiso 27 cc-offer` keeper re-levelled `_NYISO_OFFER_CURVE` CC `econ_high`
> to the CAMPD CC marginal-HR reach (`CC_REGULAR 1.12 → 1.21`, `CC_CHP 1.15 →
> 1.24` — the same `1.21×` fit ERCOT's keeper uses), closing most of NYISO's
> mild CC over-run (`2023 CC_REGULAR +2.09 → +1.70`, `2024 +2.39 → +2.09 TWh`)
> and recovering `C3a` (2023 `−8.9 %` → in-band, 2024 `−11.0 %` → `−9.7 %`)
> without re-walling capacity or a residual-fitted adder. `econ_high` is now at
> the grounded reach, so the offer lever is spent at its landing; the residual is
> at that ceiling and not chased (rule #12). See
> `docs/cc-high-cf-investigation.md` (NYISO confirmation/resolution) and
> `docs/calibration-best-so-far-nyiso.md`. **PJM's larger (+65 TWh) over-run
> still wants the structural levers ranked below — the NYISO close confirms the
> offer-level trim is a real, grounded second step, but it is the smaller lever
> for PJM.**
>
> **Update (2026-06-25): the `1.21×` NYISO reach above is BORROWED from ERCOT,
> and the `nyiso 28 native-hr` probe tested removing that borrow.** It re-grounded
> the NYISO CC/ST curve in NYISO's OWN CAMPD incremental HR (new tool
> `scripts/data/derive_campd_marginal_hr.py`, the CEMS analogue of
> `derive_dam_offer_hrmults.py`) and found NYISO's native CC reach is **0.925×**
> (not 1.21) — re-grounding to it **craters `C3a`** to −24/−26.5/−23.5 %. The
> lesson, which **applies directly to PJM**: CEMS gives the marginal **cost**, not
> the **offer**; the borrowed reach was proxying the competitive offer **markup**
> that an ISO without 60-Day-style offer disclosure (NYISO, PJM) cannot measure
> from CEMS alone. **Standing pattern: each ISO's per-class offer curve is grounded
> in that ISO's OWN measured data — never a scalar carried from another ISO — but
> for a no-offer-disclosure ISO the *markup* component must be grounded separately
> (the next step is a measured markup ON TOP of the native marginal HR, not a
> restored ERCOT borrow).** So for PJM, derive PJM's own CAMPD marginal HR with
> the new tool (`--iso PJM`) as the cost floor, then ground a PJM markup on top —
> do not import ERCOT's reach. The steam-side re-level was directionally right for
> NYISO (halved its 2024 `ST_GAS` under-run); keeper stays `nyiso 27`.

**This is an ANALYSIS task, not a compute task. Do NOT launch calibration solves.**
Your job is to read the repo + publicly available data + how other dispatch models
handle combined-cycle dispatch, and recommend the **best tuning direction** (with
priority and evidence) to close the over-generation that the structural fix in
this session exposed. End with a concrete, ranked recommendation a follow-up
session can then implement and solve.

## Context — what was done and what it exposed

A structural CC bug was fixed for the net-summer ISOs (PJM/NYISO/NEISO).
Full write-up: `docs/cc-high-cf-investigation.md` §"PJM and the net-summer ISOs:
the mirror-image bug (2026-06-24)". One-paragraph version:

- These ISOs run the per-plant EIA-860 fleet with LP capacity pinned at the
  **net-summer** rating, then summer-derated it **two more times** (the flat 10 %
  `_SUMMER_CLASS_DERATE`, and `cc_duct_peaking` re-pricing the nameplate−summer
  gap as an expensive duct wall) plus statistical WEFOR on top of the historic
  outage overlay. Net: CCs walled at ~75 % of nameplate (the verdict-C1 symptom).
- Fix (`ScenarioConfig.cc_nameplate_summer_derate`, on for PJM/NYISO/NEISO; ERCOT
  byte-identical): CC carries **full nameplate**, with **one** per-plant
  **measured** summer derate (`net_summer/nameplate`), POF/age-derate dropped in
  backcast (overlay covers them), `cc_duct_peaking` capped at 8 % so the duct band
  sits at the top of nameplate. Wall moved 75.7 % → 92 % (Guernsey).
- **Exposed:** with the wall gone, PJM 2024 CC_REGULAR runs **73 % annual CF vs
  CAMPD 61 %**, **+64.7 TWh** over CAMPD net, offline **12.5 %** vs real **22 %**,
  with **135 600 h at 95–100 % CF vs CAMPD's 34 500**. Model gas ≈ 437 TWh vs
  ~370 actual; coal ≈ 92 vs ~120. Model peak ≈ CAMPD peak (ratio 1.00) — genuine
  over-generation, not a normalization artifact. This is the `CLAUDE.md` rule-11
  signal: the wall had been masking a CC offer level that is too cheap. **The fix
  must be the real mechanism, never a new wall.**

The single-year diagnostic dispatch is at
`/tmp/.../scratchpad/pjm_npderate_2024/` (gone after the container is reclaimed —
re-derive numbers from the doc, don't depend on it). The eval that produced the
band table is `scratchpad/eval_cc_bands.py` (model `dispatch/<yr>_P1.parquet`
`mw` by `klass`/`plant_code` vs CAMPD `net_mw`, `check_cf_band_occupancy`).

## The two distinct misses to explain (keep them separate)

1. **Too many ON hours** — offline 12.5 % vs 22 %. The cheap committed block
   (PJM `committed = 0.66 × base_hr`) clears overnight LMP, so CCs never shut
   down. Real CCs two-shift / cycle. → a **commitment / offer-floor** question.
2. **Too high when ON** — the 95–100 % CF pile. No reserve headroom is held and
   the 8 % duct band (mult 2.25×, ≈ $45/MWh on 2024 gas) clears in cheap-gas
   high-demand hours. Real CCs hold spinning/30-min reserve and rarely duct-fire.
   → a **reserve co-optimization / duct-pricing** question.

A single lever will not fix both; rank them.

## What to read in the repo (evidence already here)

- **ERCOT's richer curve is the cleanest in-repo comparison.** ERCOT keeper
  (`results/calibration/run124_storage_as_keeper/run_config.json`) CC_REGULAR =
  `committed 0.87, econ_low 0.92, econ_high 1.21, peak 2.57, pct_peaking 8`.
  PJM = `committed 0.66, econ 0.76→1.14, peak 2.25 (capped 8 %)`. ERCOT's higher
  **committed (0.87 vs 0.66)** and **econ_high (1.21 vs 1.14)** hold its CCs lower
  *with commitment and reserves OFF* — quantify how much of the PJM gap a
  move toward ERCOT-like SRMC levels would close, and what it does to the
  gas↔coal C1 balance (coal is currently *under*; some shift is wanted, but PJM
  coal was only ~15 % of 2024 generation — don't over-rotate to coal).
- **The commitment screen exists but is OFF.** `model/commitment.py`, `runner.py`
  P2 (`commitment_enabled`). Read why it is off for PJM (cost/memory) and what the
  3-solve screen would do to overnight CC runs (IRR hurdle + min-run/min-down).
  This is the most direct lever on miss #1.
- **In-LP energy↔reserve co-optimization is the real fix for miss #2 but is
  memory-blocked.** `docs/multi-iso/pjm-reserve-ordc.md` (note: the shipped PJM
  ORDC overlay is **post-solve, price-only — it does NOT reserve MW**, so it
  cannot cap CC energy CF), the `energy_reserve_coopt` flag, and the note that
  per-gen `R[g]` reserve columns OOM the box at PJM plant scale. Assess a
  **zonal/aggregated** reserve formulation (reserve held at the class/zone level,
  not per-gen) as the memory-tractable way to hold CC headroom → structurally
  caps the 95–100 % pile without a wall. PJM reserve products + requirements:
  `data/raw/PJM-AS/`, Manual 11 §4.3.3.
- **Capacity reconciliation, both directions.** `scripts/derive_cc_capacity_
  reconcile.py`, `cc_capacity_reconcile`. 12/69 PJM CC plants have model nameplate
  >1.1× their CAMPD demonstrated peak; those over-run the top purely on capacity.
  A raise-only reconcile won't help here — consider whether a *demonstrated-peak*
  cap (lower nameplate to CAMPD p99.9 where nameplate exceeds it) is the right,
  measured complement to the seasonal derate.
- **Fuel/merit level.** `data/fuel.py`, `GAS_BASIS_DIFFERENTIAL`, per-plant
  EIA-923 gas. The repo comment says the gas *level* correction is done by the
  basis, not the offer curve — check whether PJM delivered gas is too cheap vs
  EIA-923 before attributing the whole miss to offers.

## What to pull from publicly available data

- **EIA-860/923 / EIA Electricity Data Browser:** the PJM CC fleet's *actual*
  annual capacity factor (the 61 % CAMPD figure should reconcile to ~55–65 %),
  and its seasonal/diurnal cycling shape. Confirm "real CCs run 61 %, not 73 %"
  is right and not a CAMPD-coverage artifact.
- **PJM Manuals 11 (Energy & Ancillary Services) and 15 (Cost Development):**
  cost-based offer construction (min-load cost, start cost, no-load) and the
  Synchronized / Primary / 30-Minute reserve requirements. This is the
  *published* basis for both a realistic committed/min-load floor (miss #1) and
  the reserve headroom (miss #2) — i.e. parameters that are **measured, not
  fitted** (rule #12).
- **PJM State of the Market (Monitoring Analytics):** CC marginal-cost vs offer
  behaviour, markup, and how often CCs are marginal vs inframarginal — tells you
  whether raising `committed`/`econ` toward SRMC is grounded or would overshoot.

## How other dispatch models handle this (the modeling-best-practice axis)

Characterize, with citations, how the realistic CC CF distribution is produced
elsewhere, and map each mechanism to a repo lever:

- **Unit commitment with start-up / min-load / min-up-down** (PLEXOS, GE-MAPS,
  PROMOD, Dayzer, EPA IPM, EIA NEMS, NREL ReEDS→PLEXOS): the standard answer for
  why CCs cycle off overnight and don't run flat-out. A pure economic-dispatch LP
  with a cheap committed block over-runs cheap units — a **documented limitation**
  of dispatch-only models. Map → repo P2 commitment screen.
- **Operating-reserve co-optimization** (every ISO RT/DA market): thermal units
  hold headroom for reserves, so energy CF tops out below nameplate. Map → in-LP
  reserve co-opt (zonal formulation).
- **Heat-rate curves rising near full load** vs a flat cheap block: real CC
  incremental heat rate is flat-to-slightly-rising; the part that holds them off
  the top is reserves + commitment, not a duct wall. Cross-check against the
  ERCOT-curve discussion in `docs/cc-high-cf-investigation.md`.

## Deliverable

A short ranked recommendation (no solves), e.g.:

1. **Primary structural lever** — likely the P2 commitment screen for PJM (miss
   #1: overnight cycling, the bulk of the +65 TWh) and/or a memory-tractable
   zonal reserve co-opt (miss #2: the 95–100 % pile). State which, why, expected
   direction of effect, and the implementation cost/risk (memory).
2. **Offer-level trim** — how far to move PJM `committed`/`econ_high` toward
   ERCOT-like SRMC, grounded in Manual 15 / SOM, with the C1 gas↔coal guardrail
   (coal is under but only ~15 % of PJM — bound the shift).
3. **Capacity reconciliation** — whether to cap the 12 over-nameplate plants at
   their CAMPD demonstrated peak.
4. **Duct band** — whether the 8 % / 2.25× band clears too readily and should be
   re-grounded.

For each: cite the repo file / public source, say whether it is measured (rule
#12) or a fitted knob (avoid), and predict the sign of its effect on (a) CC total
volume, (b) the 95–100 % CF mass, (c) the gas↔coal C1 balance. **Do not run
`run_calibration_full` or the PJM harness** — leave the solve to the
implementation session, and explicitly say which single change you would test
first.

## Guardrails

- ERCOT and CAISO/MISO/SPP must stay byte-identical (the new flags are gated off
  for them) — any proposal that touches shared code must keep that.
- Generalization: the same structural fix is already wired for NYISO/NEISO; the
  level work likely differs per ISO (their fleets, reserve markets and gas basis
  differ) — flag NYISO/NEISO-specific considerations but keep the focus on PJM.
- Honor `CLAUDE.md` #1/#11/#12: real structure first, never tune to the residual,
  never re-introduce a wall, prefer measured/published parameters.
