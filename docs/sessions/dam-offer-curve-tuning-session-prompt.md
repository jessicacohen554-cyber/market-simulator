# Session prompt — DAM-tuned offer curves (ERCOT)

> Status: RECORD (frozen 2026-07-17) — executed one-shot session prompt.

Paste the block below into a fresh Claude Code session on this repo. It is
self-contained; everything it references is committed.

---

## Task

Replace ERCOT's **chosen** offer-curve heat-rate (HR) multipliers with
**measured** ones derived from ERCOT's 60-Day DAM disclosure, per asset class,
averaged across 2023–2025 — including the genuine scarcity-bid behaviour up to
the $5,000 offer cap where the data shows it — then re-run the 3-year bundle and
compare to the current-offer-curve baseline.

Branch: `claude/ercot-ordc-lmp-scarcity-73pmtw` (continue on it; commit + push
when done). This is a **gated** change (it moves dispatch volumes and prices) —
recalibrate/compare, do not silently cut a keeper.

## Why now (context from the prior session)

- **Scarcity is now produced inside the LP**, not by a post-solve adder: the
  energy+reserve co-optimization (`config.energy_reserve_coopt`, ERCOT) puts the
  published ORDC reserve demand curve into SCED, and **storage backs reserve**
  (`reserve_storage=True`, the dominant ERCOT RRS/ECRS provider). Full-year 2023
  result: **224 h >$200 / 140 h >$500** vs ~181 / ~104 actual — accepted as the
  scarcity foundation. See `docs/ordc-overlay.md` (energy+reserve co-opt section).
- With scarcity now realistic, the remaining LMP gap is in the **energy-stack
  body** ($20–$300 band) — which the offer curves shape. Today those curves use
  *chosen* per-class HR multipliers (`ScenarioConfig.cc_committed_hr_mult=1.23`,
  `ct_committed_hr_mult=1.28`, `coal_committed_hr_mult=1.22`, the `*_econ_hr_mult`
  set, etc.). The goal is to ground them in real submitted offers.
- **Baseline to beat** (current offer curves + co-opt, 3 years): committed at
  `results/calibration/ercot_baseline_coopt_3yr/` (its `meta.json` records the
  exact recipe = run124 keeper + `--energy-reserve-coopt`). Demand-weighted
  system-LMP tail of that baseline — compare the DAM run against these:

  | year | mean $/MWh | h>$200 | h>$500 | actual h>$200 / >$500 |
  |---|---|---|---|---|
  | 2023 | 45.8 | 151 | 88 | ~181 / ~104 |
  | 2024 | 34.0 | 78 | 52 | ~53 / ~16 |
  | 2025 | 48.4 | 83 | 56 | ~31 / ~3 |

  Note: 2024/2025 **overshoot the deep tail** (flat 10,700 MW co-opt reserve
  requirement fires too hard in comfortable years). That is a co-opt-side issue,
  not an offer-curve one; the offer-curve change mainly moves the body/mean.
  Don't expect DAM offer tuning to fix the 2024/25 >$500 overshoot.

  Regenerate the report any time with
  `python scripts/run_calibration_full.py --report results/calibration/ercot_baseline_coopt_3yr`.

## The data (already in the repo — no external fetch; ercot.com is egress-blocked)

`data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet`
for **2023, 2024, 2025** (multiple files per year by month range). Schema
(verified): per `Delivery Date` × `Hour Ending` × `Resource Name`:

- `Resource Type` — maps to asset class (CCGT90/CCLE90/CC… , GSREH/GSNONR… ST,
  SCGT90 CT, PWRSTR storage, etc.).
- `QSE submitted Curve-MW1..10` / `QSE submitted Curve-Price1..10` — the
  **monotone step energy offer curve** ($/MWh vs MW). This is the bid to mine.
- `HSL`, `LSL`, `Min Gen Cost`, `Start Up Hot/Inter/Cold`, `Resource Status`,
  `Awarded Quantity`, `Energy Settlement Point Price`, and the AS awards/MCPCs.

Companion files if useful: `…_EnergyOnlyOffers_*` (virtual/EOO offers),
`…_EnergyBids_*`. Fuel (gas) price by day: `data/raw/gas-prices/` and the
model's own `gas_price_override` / `iso_hub_daily_gas_prices`
(`market_sim.data.fuel`). Per-class/plant base heat rates come from the model
fleet (the CAMPD bins / `Plant_Avg_HR_MMBtu_MWh`); reuse `load_fleet_from_csv` /
the binned fleet so the HR you divide by is the *same* base HR the offer curve
is later multiplied against.

## Method (grounded — measured, not fit to the LMP residual)

1. **Implied HR multiplier per offer point.** For each resource-hour and each
   curve point *k*: `implied_HR_k = Curve-Price_k / fuel_price(day)` (subtract
   VOM if you include it in the model's base). `hr_mult_k = implied_HR_k /
   base_HR(resource)`. Use the resource's mapped class base HR (or its own EIA
   heat rate) — be consistent with what the model multiplies.
2. **Position on the curve → tranche.** Express each point by its MW position as
   a fraction of HSL (or of (MW − LSL)/(HSL − LSL)). The model's tranches are
   Committed (≈min-load block), Econ-Low, Econ-High, Peak (see
   `docs/offer-curve-methodology.md`). Bin offer points into those positions so
   you get a per-class multiplier for each tranche.
3. **Aggregate by class, across 2023–2025.** Capacity- or award-weighted mean
   (and report the distribution — median + p25/p75 — so the spread is visible,
   not just a point). Average the three years as the user asked.
4. **Scarcity bids.** Separate the **competitive body** (the markup units bid in
   non-scarcity hours) from genuine **near-cap bids**. Report how often / under
   what conditions each class actually bids toward $5,000 (e.g. share of
   resource-hours with a curve point ≥ $1,000 / ≥ $4,500, and in which system
   conditions). Do **not** blend cap bids into the body average — that inflates
   a fake "average" multiplier. The body multipliers feed the Committed/Econ
   tranches; the near-cap behaviour informs the Peak tranche.

## The one real modeling decision — surface it, don't guess

**Double-count risk with co-opt.** ERCOT's RTSPP = energy LMP (from offers, can
reach the cap) **+** RTORPA reserve adder, with the **sum capped at the $5,000
systemwide offer cap**. In the model the co-opt reserve price already produces
the scarcity tail. So you must pick (and tell the user):

- **(A, recommended) Competitive-body offers + co-opt owns the tail.** Feed only
  the body markups (steps below the scarcity bids) into the offer tranches; let
  co-opt's reserve price provide the spike. Cleanest, no double-count, keeps the
  validated 224-hour tail. The Peak tranche stays modest.
- **(B) Full empirical offers (incl. cap bids) + cap the sum at VOLL.** Bake the
  near-cap Peak tranche from the data and ensure the LMP+reserve sum is clamped
  at `ordc_voll` (the model already caps the ORDC adder at VOLL; verify the
  *combined* price never exceeds $5,000, else you double-count the tail).

Ask the user A vs B before wiring the Peak tranche. The body multipliers (steps
1–3) are identical either way, so derive those first.

## Wiring into the model

- Per-class multipliers live as `ScenarioConfig` fields
  (`cc_committed_hr_mult`, `cc_econ_hr_mult`, `ct_*`, `gas_st_*`, `coal_*`) and
  per-group via `offer_curve_overrides` / `offer_curve_deltas`
  (`--offer-curve-override-json` / `--offer-curve-delta-json`). Prefer feeding
  the measured numbers through a committed JSON (e.g.
  `data/raw/_validation-source/offer_curve_dam_hrmults.json`) so the provenance is a data
  artifact, not a code edit — mirror `offer_curve_deltas_cc_merit_ramp.json`.
- Keep the derivation script under `scripts/` (e.g. `derive_dam_offer_hrmults.py`)
  so the JSON is regenerable from the 60-day DAM parquets.

## Run + compare

Baseline (current offer curves + co-opt), already produced last session:
```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 --storage-as-commitment \
    --offer-curve-delta-json data/raw/_validation-source/offer_curve_deltas_cc_merit_ramp.json \
    --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
    --prb-floor 0.73 --prb-follower-floor 0.63 \
    --curve-mid 0.35 --btm-backfill-year 2024 --cc-duct-peaking \
    --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP \
    --energy-reserve-coopt
```
DAM run = the same command with the DAM-derived HR multipliers swapped in (via
the new JSON / overridden config fields), everything else identical so the offer
curves are the only change, **and name the bundle** with an explicit
`--out-dir` (do NOT let it land in a bare timestamp dir):
```
    ... --energy-reserve-coopt \
    --offer-curve-override-json data/raw/_validation-source/offer_curve_dam_hrmults.json \
    --out-dir results/calibration/ercot_dam_offers_3yr
```
(`--out-dir <path>` sets the bundle directory; otherwise it defaults to
`results/calibration/ERCOT/<timestamp>/`.)

Compare on: monthly LMP MAE per year (the gate), the >$200/>$500 tail-hour
counts (should stay ~near the 224/140 the co-opt sets — confirm offer changes
don't blow up the tail), and per-class generation (volumes must stay calibrated).
Register on the dashboard with the `calibration-report` skill if it helps.

## Honesty rules (non-negotiable)

- HR multipliers come from **measured offers ÷ measured fuel cost**, not tuned to
  the LMP residual. Report the measured distribution; if a class's measured
  multiplier worsens a gate, that's a finding, not a license to hand-pick.
- Volumes stay the gated metric; the offer-curve change is gated and must be
  re-validated before any keeper.
- Don't put model identifiers in commits/PRs.
