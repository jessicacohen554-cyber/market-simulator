# ERCOT session prompt — cool the residual 2025 LMP overshoot

**Goal:** close the **2025** demand-weighted LMP overshoot that run131 left on the
table — model **$43.7** vs actual **$32.5** (+$11.2; MAE 11.3) — and its fat
high-price tail (**>$200: 60 vs 31** actual; **>$500: 39 vs 3** actual) —
*without* disturbing the years that are already good or breaking the keepers.

**Do NOT touch 2023 or 2024.** They are calibrated: 2023 46.7 vs 48.1 (MAE 10.5,
tail 151/88 — a deliberate keeper), 2024 29.0 vs 26.7 (MAE 10.5, tail 49 vs 53).
**2025 is the lone outlier.** A change that cools 2025 by cooling 2023/2024 too
is a regression, not a fix.

## Baseline to beat — run131 (the current keeper)

- Bundle: `results/calibration/ercot_dam_lrcredit_3yr`; dashboard
  `2026-06-19-run131-load-resource-rrs`.
- run131 = the run129 CC-only DAM-offer recipe **+ energy/reserve co-opt +**
  the measured load-resource reserve credit (`--ercot-load-resource-reserve`:
  credits RRS-UFR, the under-frequency-relay responsive reserve only Load
  Resources provide, ~0.8–0.9 GW, into the co-opt reserve balance).
- **The dispatch/`system.parquet` outputs are gitignored** (large intermediates),
  so a fresh clone has only the slim bundle. **Re-run the recipe below to
  regenerate `system.parquet` before you can gate against run131.**

Background docs: `docs/ercot-run131-lmp-decomposition-2026-06.md` (the
decomposition + run131 result — **read this first**), `docs/ordc-overlay.md`
(the co-opt / ORDC mechanism), `docs/ercot-dam-offer-hrmults-2026-06.md` and
`docs/ercot-dam-offer-grounding-2026-06.md` (the offer curve), the prior handoff
`docs/ercot-lmp-cooling-session-prompt.md`.

## What is already known (don't re-litigate)

From the run131 decomposition (`docs/ercot-run131-lmp-decomposition-2026-06.md`):

1. **The overshoot is the co-opt ORDC reserve adder, not the energy/offer
   curve.** Energy-only 2025 lands ~$33.8 ≈ actual $32.5; the co-opt reserve
   adder lifts the mean and builds the tail. So the residual lives in the
   *reserve* side, not the merit order. **Lowering CT/ST offers below the
   measured DAM curve is a markup, not a fix** — out of scope (say so if tempted).
2. **The OBDRR048 $20/$10 floor is ruled out** (LOLP penalty already $25.68 at
   reserves ≤7000 MW; the floor never binds). The sub-$20 / 6-hrs body is the
   measured CC energy tranche — not independently movable without a markup.
3. **The load-resource credit (run131) already took $5.8 off 2025 MAE** and left
   volumes *exactly* unchanged (it moves the reserve clearing price, not
   dispatch). The remaining $11 is a *different* slice of the same adder.

So: **the residual 2025 overshoot is the co-opt reserve adder firing in hours
2025 reality was comfortable** (note >$500: 39 model vs 3 actual — the
VOLL-anchored top steps are firing ~13× too often). 2025 is the year ERCOT's
solar+storage buildout was largest, so real reserve margins were fat exactly
when the model still sees scarcity.

## First hour — diagnose *where* the 2025 adder over-fires (before any lever)

Don't sweep. First characterize the residual, per the handoff discipline:

- **Per-hour co-opt adder in 2025** = model RTSPP − model energy LMP (or read the
  reserve clearing dual). Plot its distribution by month and hour-of-day. Is the
  $11 a broad lift across all hours, or is it concentrated in a few hundred
  high-adder hours (the >$500 tail) that drag the mean? The tail counts (39 vs 3
  >$500) suggest the latter — confirm it.
- **Cross 2025 model-scarcity hours against actual.** For the hours the model
  prices >$200/>$500, what did actual RTSPP do? If actual was ~$30 in those
  hours, the model is inventing scarcity → reserve supply is still understated
  (or the curve is too steep) in those specific hours.
- **Check the 2025 fleet completeness** (the most-measured suspect): does the
  modeled 2025 storage + solar capacity match ERCOT's actual end-2025 buildout
  (~10+ GW batteries, large solar)? EIA-860 vintage/COD handling — if 2025
  storage/solar is undersized or mis-dated, model reserve/energy is too tight in
  exactly the comfortable hours. This is a data-faithfulness check, fully
  measured. Compare to 2024 (which calibrates well) to see what changed.

Land on *one* mechanism the evidence points to before building a lever.

## Candidate levers (measured-first, in priority order)

1. **2025 fleet completeness (storage/solar COD).** If the diagnostic shows the
   model under-counts 2025 storage/solar, fixing the fleet vintage is the
   cleanest measured fix and naturally year-specific (2025 only). Check
   `data/raw` EIA-860 storage and the COD-ramp masking in the run log
   ("COD ramp (ERCOT 2025): … masked offline").
2. **Additional measured load-side AS.** run131 credited only RRS-UFR. ERCOT
   Load Resources also clear **ECRS-Manual** (`ecrsm_mw`) and offline **NonSpin**
   (`nspnm_mw`) — but those services mix gen and load, so crediting them as load
   is *only* defensible with an attribution you can document (e.g. ERCOT's
   load-resource ECRS share). Don't credit total ECRS/NonSpin as load — that
   over-credits and would crater the tail. The per-service columns are in
   `data/raw/ercot-AS/ercot_<year>_as_up_mw.parquet`
   (`scripts/data/build_ercot_as_withholding.py`).
3. **ORDC LOLP curve realism for 2025.** The co-opt uses VOLL-anchored LOLP
   steps (`ercot_ordc_demand_steps`, params `ordc_lolp_mu_mw/sigma`, `ordc_voll`,
   `ordc_mcl_mw`). If 2025's real reserve margin was structurally higher, a
   year-flat curve over-fires. Only move this if you can ground it in ERCOT's
   *published* 2025 ORDC / reserve-margin data — **fitting mu/sigma to hit $32.5
   is a markup.** Treat as last resort and label it honestly if used.

The lever almost certainly wants to be **2025-specific by construction** (a fleet
or measured-AS fact that only applies to 2025), not a global knob — a global
change that cools 2025 will cool the good years too.

## Reproduce / gate

run131 recipe (regenerates `system.parquet`; ~13–20 min, 3 yr, co-opt LP):

    uv run python scripts/run_calibration_full.py --year 2023 2024 2025 \
        --storage-daily-cycling --battery-adder 10 --storage-as-commitment \
        --offer-curve-delta-json data/raw/_validation-source/offer_curve_deltas_cc_merit_ramp.json \
        --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
        --prb-floor 0.73 --prb-follower-floor 0.63 \
        --curve-mid 0.35 --btm-backfill-year 2024 --cc-duct-peaking \
        --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP \
        --energy-reserve-coopt --ercot-load-resource-reserve \
        --offer-curve-json data/raw/_validation-source/offer_curve_dam_hrmults_cconly.json \
        --out-dir results/calibration/ercot_dam_lrcredit_3yr

Your probe = the same line with your change and a fresh
`--out-dir results/calibration/ercot_dam_<probe>_3yr`. Then gate:

    # (the compare script reads data/raw/_validation-source/ directly — no path bridge needed post-W1)
    uv run python scripts/probes/_dam_offer_compare.py ercot_dam_<probe>_3yr ercot_dam_lrcredit_3yr

**Watch all three gates together** (the prompt's standing rule):
- Monthly LMP MAE/avg per year — push **2025** down toward actual, keep **2023
  and 2024 flat** (within ~$0.5 of run131).
- Tail >$200/>$500 — pull 2025 toward 31/3, **keep 2023 at 151/88** and don't
  collapse 2024 (49/28).
- Per-class TWh — keep ≥ run129's **12/18**; do **not** crater ST_GAS or over-run
  CT past bench. (run131's `DAM−BASE ≈ 0` is the bar; a price-only lever should
  stay there.)

## Dashboard — register every run (keeper or probe)

    uv run python scripts/dashboard_add_run.py --label "run132 <keyword>" \
        --bundle results/calibration/ercot_dam_<probe>_3yr
    # edit the sidecar frontend/data/backcast/registry/<id>.json: real definition,
    #   mark "(PROBE)" if rejected, with the gate numbers
    uv run python scripts/build_manifest.py    # rebuild gitignored shell; node --check it
    git add results/calibration/ercot_dam_<probe>_3yr \
            frontend/data/backcast/registry/<id>.json \
            frontend/data/backcast/runs/<id>.js frontend/data/backcast/bench/ERCOT
    # NEVER commit the generated backcast-results.html / manifest.js (gitignored)

Keep **top-10 per ISO**; prune oldest sidecars/payloads if over (ERCOT is at 7,
runs 125–131 — room for a few before pruning).

## Honesty (the standing gate)

Volumes stay the gated metric; LMP is the target but **not at the cost of the
run131 volume keeper**. The offer multipliers are measured (DAM-grounded) — if
you lower CT/ST below the measured distribution, or fit the ORDC LOLP curve to
hit $32.5, **that is a calibration markup: say so and justify it against the LMP
residual, don't dress it as measured.** Don't put model identifiers in
commits/PRs.

## Environment notes (managed remote; learned this session)

- Run Python via `uv run python …` (deps resolve through `uv`; no bare `python`).
- The EIA-930 `ERCO hourly.parquet` extract and per-ISO extracts **are committed
  on main now** (the recovery is done) — no offline rebuild needed.
- Two paths went stale in the data reorg and need bridging/awareness: the compare
  script's actual-LMP path (`data/raw/_validation-source/…`, bridge as above) — and note
  `build_ercot_as_withholding.py` was already fixed this session to write the
  canonical `data/raw/ercot-AS`.
- Actual RTSPP: `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`
  (columns `year, hour, rt`). The two run129 offer JSONs live in the same dir.
- The CLI arg was renamed `--offer-curve-override-json` → `--offer-curve-json`.
- **Recovered baseline bundles are input-only** (no `system.parquet`/dispatch) —
  always re-run a baseline on the current extract for a clean same-extract gate;
  do not compare against the offline-rebuild numbers in old notes (that mistake
  made run131 first look like a $1 lever when it was $5.8).
- Branch: develop on `claude/ercot-run131-offer-mults-v5pz98` (or a fresh
  `claude/ercot-run132-…`); push there, don't open a PR unless asked.
