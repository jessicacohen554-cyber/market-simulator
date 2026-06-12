# ERCOT calibration — best config so far

Keeper: **run 91 / dashboard `run91 cc shave`** (2026-06-12, bundle
`results/calibration/run91_cc_shave055`, highspy 1.14.0). **Supersedes run 85
(`run85_coal_soft`)** on the size-aware volume bar (see "Success bar" below):
run 91 has 3 in-scope fails vs run 85's 4, shrinks the 2024 cheap-gas cluster
7.37 → 3.65 TWh (PRB 2024 −7.9 → −4.9% now PASSES; CC_REGULAR 2024
+2.1 → +0.4%), improves hourly coal NRMSE (0.198 → 0.182 in 2024) and holds
the LMP gate. It adds two CC_REGULAR-side moves on top of run 85's config —
the coal sigmoids and everything else are unchanged. Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run91 deltas> \   # run_config.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.75 --lignite-ceil 1.00 \
    --prb-floor 0.74 --prb-follower-floor 0.64 \
    --curve-mid 0.35
```

Run 85 remains the documented predecessor; its config and table are in the git
history of this file and the "ERCOT Runs 85–87" / "ERCOT Runs 89–91"
calibration-log entries.

## Success bar (size-aware)

Judge each class by size, not a flat percentage (a flat % is loosest exactly
where the system mix is dominated):

- class total **≥ 20 TWh** (CC_REGULAR, CC_CHP, COAL_PRB): within **±5%** every
  year.
- class total **< 20 TWh** (ST_GAS, COAL_LIGNITE, CT_PEAKER, CT_CHP): within
  **±1 TWh** (absolute) every year.
- CT_CHP excluded (known +28% 2025 CHP-benchmark gap).

Never regress a class vs the keeper. Under this bar run 91 has 3 in-scope
fails vs run 85's 4, all still in the single 2024 cheap-gas year and all
marginal: ST_GAS −1.12 TWh, lignite −1.31 TWh, CT_PEAKER −1.22 TWh. The
honest caveats: PRB 2024 (−4.9%) and ST_GAS 2023 (+0.95 TWh) pass with
<0.1 TWh margin, the CC moves spend 2023 CC_REGULAR headroom (−2.7 → −4.6%,
still in tolerance, −6.6 TWh on the 144-TWh class), and total |class error|
is flat vs run 85 (~21.0 TWh) — the win is distributional (fail count + the
2024 cluster), not aggregate.

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- Coal passthrough sigmoids (the run-85 adds, unchanged in run 91):
  - `coal_lignite_passthrough_sigmoid = on`, floor 0.75 / ceil 1.00.
  - `coal_prb_passthrough_floor = 0.74`, `coal_prb_follower_floor = 0.64`.
  - Gas-mid/slope at the built-in defaults (2.85 / 2.5) for all tiers. The
    run-90 probe measured why these must NOT be retuned for 2024: the PRB
    TWh response is ~65 TWh per unit passthrough in 2024 but ~142 in 2023
    (2023 sits on the coal-gas knife edge), and no single logistic can cut
    below $2.1 shaped gas while tracking the run-85 curve at $2.29+.
- **`offer_curve_smoothing_mid = 0.35`** (`--curve-mid 0.35`, the run-89 add):
  the n=6 econ-ramp shape anchor f(0)=0, f(0.5)=0.35, f(1)=1. CC_REGULAR's
  econ ramp is nearly flat (econ_low 1.06 → econ_high 0.96) so the anchor
  barely moves it, while the steep-ramp classes (PRB econ_low 0.40 →
  econ_high 1.38, ST_GAS, CT) get cheaper middles — draining CC_REGULAR's
  2024 mid-merit surplus into them. (m > 0.5 moves volume the OTHER way —
  the rejected first probe, bundle `run89_midpoint065`.)
- **CC_REGULAR offer-curve delta retune (the run-91 add):** econ_high
  −0.45 → **−0.40**, peak +0.25 → **+0.32** (everything else identical to
  run 79's deltas). Jacobian-direction, dose set at 55% of the measured
  full-dose response (bundle `run91_cc_shave_full` is the β=1 endpoint;
  the feasibility box on the measured B→full vector is β ∈ [0.39, 0.74]).
- `storage_daily_cycling = on`; **`battery_dispatch_adder = 10.0`** $/MWh
  (E2, unchanged); nuclear per-year EIA-923 monthly CF overlay (−0.7%/yr).
- Full offer-curve deltas vs calibrated defaults (recorded in the bundle's
  `run_config.json`): CC_REGULAR {committed −0.05, econ_low −0.10, econ_high
  −0.40, peak +0.32}; CC_CHP {econ_high +0.43, peak −0.50, pct_peaking −4};
  CT_CHP {committed −0.20, econ_low −0.08, econ_high +0.10, peak −0.08};
  CT_PEAKER {committed −0.34, econ_high +0.20}; ST_GAS {committed −0.385,
  econ_low −0.13, econ_high −0.35, peak −1.0}; COAL_PRB {committed −0.04,
  econ_low −0.30, econ_high +0.44, peak +0.082}; COAL_LIGNITE {committed
  −0.07, econ_low +0.076, econ_high −0.037}.

## Results (P1, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −4.6% | +0.4% | −1.0% |
| CC_CHP | +1.1% | +0.9% | +2.1% |
| COAL_PRB | +4.3% | −4.9% | +0.7% |
| COAL_LIGNITE | +2.1% | −9.4% | +1.9% |
| CT_PEAKER | −0.8% | −14.8% | −0.9% |
| ST_GAS | +5.7% | −6.1% | +2.9% |
| nuclear | −0.7% | −0.7% | −0.7% |
| coal hourly NRMSE | 0.150 | 0.182 | 0.168 |
| LMP MAE vs actual RT ($/MWh) | 31.1 | 9.2 | 11.5 |

Unserved energy 0.000 in all years. Plant guard: Martin Lake / Limestone 2023
at +914/+948 GWh (under the ~1 TWh line; run 85 was +614/+810); Martin Lake
2025 +1.50 TWh (run 85 +1.35 — watch on any further coal-side move). The
residual is the smaller 2024 trio above plus the 2023 LMP level miss (missing
ORDC scarcity pricing — localized in the "ERCOT Runs 85–87" log entry, still
the structural follow-up).

## History

Run 85 (`run85_coal_soft`, coal passthrough sigmoids) was the keeper through
2026-06-12 and is superseded by the above; run 79 (`e2_4_retune`) before it.
The run-80/81/82/84 probes, runs 86/87 (Jacobian gas counter-move; measured
monthly gas) and run 90 (2024-keyed PRB sigmoid retune — the year-gradient
finding) were net-negative; see the calibration-log entries. The previous flat
`coal_prb_passthrough = 0.83` keeper (git `249fec7`) predates the sigmoid
family entirely.
