# PRE-COMMIT — ERCOT-145b: `gas_daily_shape` on ERCOT (matrix §5.1 item 4, the five-ISO fuel-stack consistency A/B)

**Pushed BEFORE the solve.** Session ERCOT-145, 2026-07-31. The session's first
lane (item 5, `tranche_startup_amortization`) closed no-solve with the cell
stamped `G` (`docs/DIAGNOSIS-ercot145-tranche-startup-2026-07-31.md`); the
chartered alternate is item 4 — the five-ISO fuel-stack consistency audit
(`gas_daily_shape` / `gas_monthly_actuals` / `gas_plant_monthly_fuel_pricing`)
on ERCOT. Baseline keeper: `2026-07-31-ercot144-coal-perplant-offer` (bundle
`ercot144_perplant_arm`, determination NOT-YET, fails {C3a, C3b, C3c, C7}).

## 0. The objective, stated so it is not misread

This is an **input-correctness A/B under rules 14/1, not a residual chase.**
The Phase-1 audit (below) found ERCOT is the only ISO pricing gas at a FLAT
month level while a measured daily commodity series exists on disk. Rule 14
`[R-ACCURATE]` prefers the accurate input; rule 1 forbids judging it by
whether the backcast fit improves. The keeper decision is made on **structural
faithfulness + the pre-registered guards**, with C3a/C3b movement reported but
NOT required (and NOT tuned for). The ex-ante correlation evidence (§1c) is
deliberately weak-to-mixed — this precommit records that a fit gain is NOT
predicted, so nobody later mistakes whatever gain appears for the lane's
justification.

## 1. Phase 1 — the audit (no LP), and the decision

**(a) The five-ISO posture, measured from the keepers' own `run_config.json`:**

| flag | ERCOT | CAISO | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| `gas_daily_shape` | **off** | on | on | on | on | on |
| `gas_monthly_actuals` | **off** | on | on | **off** | on | on |
| `gas_plant_monthly_fuel_pricing` | **off** | on | on | on | on | on |

(CAISO `caiso146_ctheatrate_B`, PJM `pjm140_rampenv_B`, MISO
`miso101_tempgrain_B` — checked across miso102/106/109 controls too, all
identical — NYISO `nyiso100_silretire`, NEISO `neiso61_netrev_margin`.)

**(b) Two of the three ERCOT cells are ALREADY adjudicated, not untested:**

- `gas_monthly_actuals` on ERCOT was **rejected at Run-77** (the postmortem
  recorded in the `gas_hh_monthly_shape` docstring, `scenarios.py`): the
  ~20 %-coverage EIA-923 reporter sample runs ~+$1/MMBtu above the merchant
  hub, so the LEVEL swap is a biased input for ERCOT. Its admissible
  descendant is `gas_hh_monthly_shape` (shape-only, level-preserving) — built
  for exactly this reason, currently unarmed, and **carrying no matrix row**
  (a rule-26c gap, surfaced to the owner in §6, not decided here).
- `gas_plant_monthly_fuel_pricing` is off for ERCOT **by documented measured
  design** (`backcast_config.py:2023`: `(iso != "ERCOT")`; the flag's own
  docstring): ERCOT EIA-923 gas coverage is ~12 % of CC MW, so per-plant
  pricing creates a spurious intra-zone asymmetry (the Jack County incident).
  Same-hub merchants buy in the same market; the sparse reporters are not a
  better measurement of the marginal unit's gas cost.

Both cells are stamped from the RECORD (`G`, citations in the matrix note) —
an audit stamping history, not a new adjudication. **The single live cell is
`gas_daily_shape`** (`U`), and it is the only lever this precommit solves.

**(c) Ex-ante evidence on the keeper's own sidecars**
(`scripts/probes/ercot145_gas_daily_exante.py` reproduces it):

- Factor magnitude (measured HH daily staircase / month mean —
  `fuel.hubs.gas_daily_shape_factors`, mean-preserving per month by
  construction): 2023 is TAME (std 0.076, max 1.276 — the queue's
  "C3b-2023 winter-volatility candidate" premise is **weak on the HH side**);
  2024 carries Winter Storm Heather (max **3.287**, 14 days >1.25×, 44 days
  <0.8×); 2025 std 0.167, max 2.143.
- Within-month correlation of the keeper's DAILY price residual (act − model)
  with the daily factor: 2023 **−0.011** (nil), 2024 **−0.061** (slightly
  adverse), 2025 **+0.127** (Feb +0.41, Dec +0.44 — real winter signal).
- Decision: the mechanism is armed on measured-input correctness (rule 14),
  five-ISO structural consistency, zero fitted parameters, and a clean rule-19
  slot (no other ERCOT mechanism represents within-month daily gas variation —
  verified in `fuel/resolve.py`: ERCOT has no citygate-daily or basis-daily
  row, and the ERCOT-144 coal surface is fuel-invariant by measurement so the
  swing reaches only gas SRMC). A fit gain is NOT predicted.

## 2. The arm — ONE mechanism, one bundle

Single delta off the keeper, full span in one bundle (rule 16):

```
nohup python scripts/replay_keeper.py results/calibration/ercot144_perplant_arm \
    --set gas_daily_shape=true \
    --out-dir results/calibration/ercot145_gas_daily_arm \
    --note "ercot145 item-4 A/B: measured HH daily within-month gas shape" &
```

`--set` rides the generic prb_overrides ScenarioConfig channel (applies last,
wins; the run mints its own dated id). No ScenarioConfig field is added — the
flag, its artifact (`data/raw/gas-prices/henry_hub_daily.csv`) and its matrix
row all exist. Default cache key untouched (verified byte-stable this
session: `603c2498bf71d21d`).

### 2.1 Rule 19 — the slot is empty

Enumerated from the keeper's config: ERCOT gas is priced at the annual
override × `GAS_MONTHLY_SEASONALITY` shape + the ERCOT zonal basis (West
discount) + West delivered floor. Nothing represents day grain. The factors
multiply the hourly gas series BEFORE the additive zonal basis
(`resolve.py:146`), which lands un-shaped — same composition order as every
other ISO. No stacking, no replacement needed.

### 2.2 DOF — zero new entries

The factors are a measured commodity series (rule 13-admissible: forward
years use a forward monthly level × a representative daily shape; the shape
responds to conditions), re-derived only on source updates (rule 23). The DOF
ledger's `n_residual` must stay **6** — `build_dof_ledger.py` is a
post-solve gate, not a hope.

## 3. Predictions — fixed before the solve

1. **Dispatch**: coal/gas flip days resolve — gas takes the cheap-factor
   shoulder days from coal, coal holds the spike days. Annual class energy
   moves LITTLE (mean-preserving level): coal and CC within their C1 bands.
2. **Price**: daily price dispersion rises within months carrying factor
   spread; monthly means move only through dispatch nonlinearity (small).
   2025 winter months (Feb/Dec, the +0.4 corr cells) should improve their
   daily shape; 2024 January may WORSEN daily shape locally (corr −0.15)
   while possibly adding legitimate Heather-day near-tail hours.
3. **C3b**: no NRMSE flip predicted in either direction (monthly means are
   ~preserved). C3a: no material move predicted.
4. If the solve shows a large C3a/C3b move in either direction, that is a
   FINDING about nonlinearity, to be reported — not the promotion basis.

## 4. Pre-registered failure modes — the decision rule, fixed now

The arm is **rejected** (registered as rejected, cell stamped `R`) if ANY of:

- **Zero-spurious guard**: model >$200 tail hours in hours where the actual
  RT is <$200 must not exceed the keeper's own **2/2/0** (2023/24/25). A
  Heather-day model tail hour coinciding with an actual tail hour is
  legitimate structure and does NOT trip this guard.
- **C3c no-drain**: the model tail counts **47/6/0** must not DECREASE in any
  year (the ERCOT-119 drain pattern).
- **C1/C2 held**: any C1 class-band flip PASS→FAIL, or a C2 flip, in any
  year is an ordinary rejection.
- **C7 2024/2025 COAL_LIGNITE** must stay passing on both legs (profile_r,
  cv_ratio). (2023's C7 COAL_LIGNITE cell is already failing and attributed;
  its movement is reported, not gated.)

Otherwise the arm is a **keeper candidate on structural grounds** (rule 14:
the accurate input stays in), surfaced with the full guard table; promotion
follows the ERCOT-137 structural standard. LOYO within 2023–2025: the
mechanism carries ZERO fitted parameters (each year uses its own measured
factors), so there is nothing to leave out — recorded as structurally
LOYO-exempt with the per-year guard table standing in.

## 5. Honest limits, declared before it runs

- Day-scale only (the pjm-139 W1 bound): factors repeat per calendar day —
  this lever cannot move any intra-day differential, and the ERCOT-145
  item-5 diagnosis showed the dominant sub-$200 high-load residual is an
  intra-day/dispersion object. This lever does not target it.
- HH is the national commodity swing; ERCOT's local (Waha/HSC/Katy) daily
  basis swing is NOT represented (the `winter_citygate_daily` ERCOT cell
  stays untested — a separate, data-intake-first candidate).
- 2023's C3b 0.637 is NOT expected to close (2023 factors are tame).

## 6. Open owner rulings surfaced (NOT decided here)

1. `gas_hh_monthly_shape` carries no matrix row (rule-26c gap) — the
   admissible ERCOT descendant of the Run-77 rejection; untested everywhere.
2. The matrix `gas_monthly_actuals` MISO cell reads `K` but every recent
   MISO bundle (miso101/102/106/109) records `False` — cell drift, corrected
   this session to match the measured record (MISO prices via per-plant F923 +
   citygate daily + zonal basis instead).
3. Carried from the morning lane: per-gate dispositions of the attributed
   gates; `split_coal_tranches` delete-vs-inert; `ercot_offer_hrmult_ep_*`
   matrix rows; Martin Lake composition (ERCOT-143 §7.3).

## 7. Post-steps (in order, same session)

`--rebuild-benchmark` → `legitimacy_diagnostics.py` → `build_dof_ledger.py`
(n_residual == 6) → `dashboard_add_run.py` → `calibration_verdict.py
<ABSOLUTE path> --write-metrics` → `build_status.py --iso ERCOT` (keeper
promotion only if the owner-standard is met) → matrix cells + §5.1 queue +
calibration log, same session (rules 15/26b). Keeper-commit set slim; run
payload via `git push` (457 KB cap); blob-verify ≥300-line files.
