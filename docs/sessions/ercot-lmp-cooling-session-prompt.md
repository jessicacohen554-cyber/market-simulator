# Handoff: cool the ERCOT 2024/2025 LMP hot bias from run129

## Task

Continue ERCOT calibration on branch `claude/ercot-dam-offer-hrmults-ycl68p`
(commit + push when done). Starting point is **run129** — the CC-only measured
DAM-offer curve, the current best on curve-fit + asset-class volume matching.
**Goal: pull down the 2024 and 2025 LMP hot bias without regressing run129's
volume gate (12/18 in-tolerance).** Gated change (moves prices AND volumes) —
recalibrate/compare on the dashboard, don't silently cut a keeper.

## Where run129 stands (the baseline-to-beat)

- Bundle: `results/calibration/ercot_dam_offers_cconly_3yr` (dashboard run
  `2026-06-18-run129-dam-offers-cc`). Anchor: run127
  (`results/calibration/ercot_baseline_3yr`, dashboard
  `2026-06-18-run127-dam-baseline-keeper`).
- Recipe = the baseline command (co-opt, storage-AS, lignite-sigmoid/PRB-floor,
  cc_merit_ramp delta) + `--offer-curve-override-json
  data/raw/_validation-source/offer_curve_dam_hrmults_cconly.json` (measured CC bands
  only; CT/ST left on the calibrated curve to avoid the -0.25 CT<->ST coupling
  crater that sank run128).
- Volume gate: **12/18 classes in tolerance** (vs 13/18 baseline). CC_CHP fixed
  (+18/+19/+23% -> +0.4/+0.5/+3.6%), CT_PEAKER under-runs (-29/-33/-7%), ST_GAS
  drifts a little high (+11.9/+5.4/+16.3%).
- LMP avg ($/MWh): 2023 46.7 vs act 48.1 (fine); **2024 34.7 vs act 26.7
  (+30%); 2025 49.5 vs act 32.5 (+53%)** — the problem.

## The LMP hot bias is NOT (mostly) the CT/ST econ body — decompose first

Measured (`scripts/probes/_dam_offer_compare.py` + a monthly/price-band split):

- **2024**: concentrated in a few **spike months** (Apr +30, Aug +33, Oct +50);
  median model $18.6 ~ actual $19.8, and the model has *fewer* $40-80 hours
  (68 vs 699). => a handful of tight days are overpriced (scarcity/co-opt tail),
  not a broad body lift.
- **2025**: **broad** (+17 to +44 most months) **and a missing cheap tail** —
  the model prices **only 6 hours <$20 all year vs 2329 actual**; median model
  $30 vs $25.9. => a too-high price *floor*, not just a high body.

"lower CT/ST offers" was the first instinct but run130 (below) ruled it out —
the evidence points at:
  1. **The 2025 floor** — why does the model almost never clear below $20?
     Suspects: the co-opt ORDC **reserve adder lifting non-scarce hours**, the
     **ORDC multistep floor** ($20 at reserves <=6500 MW / $10 at 6500-7000;
     `ordc_multistep_floor`, `ORDC_FLOOR_STEPS` in
     `src/market_sim/results/scarcity.py`), and/or the committed-band bids of the
     marginal CC/CT keeping the overnight clear price up. Check the co-opt
     `reserve_price` contribution per hour (reserve-balance dual; `runner.py`
     ~L560, `ercot_reserve_coopt_inputs`).
  2. **The 2024 spikes** — localize Apr/Aug/Oct overpriced days; co-opt scarcity
     (reserve demand too steep — `ordc_mcl_mw`, `mu/sigma` via
     `resolve_lolp_params`) or a too-high CT/ST peak wall firing?
  3. **CT/ST offer heights** (the user's ask) — CT_PEAKER peak is **13.15** (a
     huge price wall), econ_high 2.18; ST_GAS econ_high 1.20 / peak 3.20.
     Lowering CT econ_high/peak pulls the upper-mid body down. Coupling caveat:
     cheaper CT clears MORE (CT under-runs today, volume-helpful) but cheaper ST
     clears more too and **ST already over-runs** — so lower CT's price wall
     (econ_high/peak) before touching ST. run128 showed that dropping CT peak to
     ~5.4 AND feeding measured ST *worsened* 2025 LMP (18.2) because ST left
     merit and CC/CT set higher prices — so move CT alone first, keep ST put.

Spend the first hour on the decomposition (which lever owns each year) before
sweeping — a single static curve change hits all three years, and 2023 is
already good, so don't break it.

## First probe — CT offer lever is RULED OUT (run130)

run130 (`results/calibration/ercot_dam_ctcool1_3yr`, dashboard
`2026-06-18-run130-ct-peak-cool`) lowered CT_PEAKER econ_high 2.18->1.58 and peak
13.15->7.15 (ST untouched) on top of run129, via
`data/raw/_validation-source/offer_curve_deltas_ctcool1.json`. **Result: the LMP hot bias
barely moved** — 2025 MAE 17.06->16.62 (avg -0.45), 2024 -0.21, 2023 flat. So the
CT (and by extension the gas econ/peak) offer curve is **not** the lever for the
2024/2025 hot bias — this confirms the decomposition below. It did help volumes
(CT_PEAKER -7%->+2% in 2025, ST over-run trimmed; gate still 12/18), so it is a
mild volume win, but it does NOT fix LMP.

**=> Do not keep sweeping CT/ST offer heights for LMP. Go after the co-opt/ORDC
layer:** the 2025 price floor (the model clears <$20 only 6 h/yr vs 2329 actual)
and the 2024 scarcity spikes (Apr/Aug/Oct). The reserve adder / ORDC floor /
reserve-demand steepness are the live levers; offers are spent.

## Levers & wiring

Layer changes on top of run129 via offer-curve deltas (cheapest to iterate). The
run takes ONE `--offer-curve-delta-json`, so a CT/ST tweak must be merged with
the cc_merit_ramp deltas into a single file (build it from
`offer_curve_deltas_cc_merit_ramp.json`); the CC-only `--offer-curve-override-json`
stays unchanged beneath it. Deltas ADD to the resolved curve.
- e.g. CT cooling: `{"CT_PEAKER":{"econ_high":-0.4,"peak":-6.0}}` merged into the
  cc_merit_ramp deltas.
- Floor/scarcity hypotheses: co-opt knobs are ScenarioConfig fields
  (`ordc_mcl_mw`, `ordc_lolp_shift_sigma`, `ordc_multistep_floor`,
  `ordc_lolp_params_path`); `--energy-reserve-coopt` is already on. See
  `docs/ordc-overlay.md` and `scripts/data/derive_ordc_overlay.py`.

## Run + compare — NAME THE BUNDLE

Run = the run129 command with the new delta swapped in, everything else
identical, explicit `--out-dir results/calibration/ercot_dam_<probe>_3yr`:

    python scripts/run_calibration_full.py --year 2023 2024 2025 \
        --storage-daily-cycling --battery-adder 10 --storage-as-commitment \
        --offer-curve-delta-json data/raw/_validation-source/<your_new_delta>.json \
        --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
        --prb-floor 0.73 --prb-follower-floor 0.63 \
        --curve-mid 0.35 --btm-backfill-year 2024 --cc-duct-peaking \
        --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP \
        --energy-reserve-coopt \
        --offer-curve-override-json data/raw/_validation-source/offer_curve_dam_hrmults_cconly.json \
        --out-dir results/calibration/ercot_dam_<probe>_3yr

Each run ~13 min (3 yr). Env: `uv venv .venv && . .venv/bin/activate && uv pip
install -e ".[dev]"`. Compare:

    python scripts/probes/_dam_offer_compare.py ercot_dam_<probe>_3yr ercot_dam_offers_cconly_3yr

Watch all three gates together: monthly LMP MAE/avg per year (push 2024/2025
DOWN toward actual, keep 2023 ~ flat), the >$200/>$500 tail (stay ~151/88 in
2023 — co-opt owns it, don't collapse it), and per-class TWh (keep >= run129's
12/18; do NOT crater ST_GAS or over-run CT past bench).

## Dashboard — register EVERY run (keeper or probe)

After each completed bundle:

    python scripts/dashboard_add_run.py --label "run13N <keyword>" --bundle results/calibration/ercot_dam_<probe>_3yr
    # edit sidecar frontend/data/backcast/registry/<id>.json: real definition, mark "(PROBE)" if rejected
    python scripts/build_manifest.py    # rebuild gitignored shell; node --check it
    git add results/calibration/ercot_dam_<probe>_3yr \
            frontend/data/backcast/registry/<id>.json \
            frontend/data/backcast/runs/<id>.js frontend/data/backcast/bench
    git commit && git push

ERCOT uses the runNN scheme (next is run131 after run130). Keep top-10 per ISO;
prune oldest sidecars/payloads if over. Never commit the generated
`backcast-results.html`/`manifest.js`/`benchmark.js` (gitignored).

## Honesty

Volumes stay the gated metric; LMP is the new target but not at the cost of the
run129 volume keeper. The offer multipliers are measured (DAM-grounded) — if you
lower CT/ST below the measured distribution, that's a calibration markup, so say
so and justify it against the LMP residual, don't dress it as measured. Don't put
model identifiers in commits/PRs. Background: `docs/ercot-dam-offer-hrmults-2026-06.md`
(run127/128/129), `docs/ercot-dam-offer-grounding-2026-06.md` (the CT<->ST
coupling), `docs/ordc-overlay.md`, `docs/lmp-decomposition-2026-06.md`.
