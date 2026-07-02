NYISO load / demand-basis fix — session handoff (the gas-TOTAL deficit)

>>> RESOLVED 2026-06-23 — td_loss STAYS 0; the premise below is REFUTED. <<<
>>> The NYISO Gold Book Table I-2 actual NYCA Annual Energy (Note 1: includes
>>> T&D losses) = 147,050 GWh (2023) = the EIA-930 demand the model already
>>> serves, so the demand is ALREADY loss-inclusive and a td_loss gross-up would
>>> double-count (rules #11/#12). The handoff's "~6 TWh / 4.5%" mistakenly
>>> compared to FULL EIA-923 (129.7, incl. BTM CHP) instead of the grid-
>>> delivered 125.0 the dashboard scores. The residual gas deficit is the
>>> EIA-923/EIA-930 benchmark-basis reconciliation (1-3%/yr, not a dispatch
>>> error) plus zero-sum import-node economics. No model change.
>>> FULL WRITE-UP + 3-year baseline: docs/nyiso-td-loss-resolution-2026-06.md.
>>> Do NOT reopen the td_loss decision without new evidence against that doc.

CONTEXT
LP-based electricity-market dispatch simulator. READ CLAUDE.md FIRST — esp. rule
#1 (right STRUCTURE first; never judge a real mechanism by the fit; NO fitted
adders/haircuts), #11 (prefer measured/accurate data; a worse fit is a DISCOVERED
BUG, find the root cause, don't bury it in an inaccurate input), #12 (forward-
reproducible physical/market inputs only; no pinning to actuals), #13 (register
EVERY run on the dashboard, results live there not in chat), #14 (all 3 years —
2023/2024/2025 — in ONE bundle, never a single-year keeper). Honor the "Git &
Pushing (avoid the 413 loop)" section: rebase fresh onto the LATEST origin/main
BEFORE pushing, small commits, never hand-commit the deploy-generated dashboard
data files (manifest.js / benchmark.js / completeness.js).

Read first:
  - docs/nyiso-dispatch-validation-2026-06.md  (the "Gas offer curves grounded in
    the NYISO SOM — `nyiso 22`" section is the latest state — the offer-curve work
    that PRECEDED this task; it diagnosed but did NOT fix the gas-total deficit)
  - docs/calibration-best-so-far-nyiso.md  (the "gas-total basis floor" section —
    the prior calibration's td_loss=0 decision THIS TASK IS REOPENING)

ENVIRONMENT
  - venv: source .venv/bin/activate (pandas/highspy present). pip works via uv:
    `uv pip install --python .venv/bin/python <pkg>` (pypi is in noProxy). pdfminer.six
    extracts the Gold Book / SOM PDFs.
  - Solve (~3 min/yr now — NYISO P2 commitment is a CONFIRMED no-op, dropped):
      python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
        --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
        --priced-interchange --energy-reserve-coopt \
        --nyiso-local-selfsupply --nyiso-firm-imports --out-dir <dir>
    (this is the CURRENT NYISO keeper config — `--commitment` was dropped this
    session: P1≡P2 byte-identical on fuel mix AND price for NYISO, all 3 years,
    because the LI floor + CHP must-run + reserve co-opt leave no unprofitable
    CC/CT run for the IRR screen and the adequacy backstop holds the rest.)
  - Scoring = the DASHBOARD VERDICT. Register: run_calibration_full.py
    --rebuild-benchmark <dir>; then python scripts/dashboard_add_run.py --label
    "..." --bundle <dir>; then python scripts/calibration_verdict.py
    results/calibration/<name> --json (criteria fuelmix C1, sysvol, price_mean,
    price_shape, dispatch_corr, co2; price_tail SKIPs on NYISO).
  - Actuals: data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet; fuelmix
    actuals are EIA-923 grid-delivered TWh per class (in the bench sidecar
    classFull, frontend/data/backcast/bench/NYISO/<year>.json.gz).

THE DIAGNOSIS (already done this session — do NOT re-derive, build on it)
The NYISO gas TOTAL is structurally short in 2024/25 (sysvol gas: 2023 +3.0% =
ON; 2024 −11.5% = −7.8 TWh; 2025 −9.2% = −6.5 TWh). It is NOT offer curves and
NOT the in-state non-gas fleet — nuclear / hydro / wind / solar all match EIA-923
within noise every year, so they are not displacing gas. The deficit decomposes:

1. **DOMINANT (~6 TWh): the load→net-generation BASIS gross-up (td_loss).** The
   model serves load with generation+imports and `td_loss_factor = 0`
   (scenarios.py:789), so modeled generation == load EXACTLY. But the gas C1
   benchmark is EIA-923 **net generation** (busbar), which must EXCEED load by
   **T&D losses (+ exports)**. With no gross-up the model generates only the
   load, so gas (the swing fuel) is short by the entire loss volume.
     - **The load LEVEL is already correct** — do NOT chase it. The NYISO
       published actual load (data/raw/zone-specific-demand/NYISO/
       NYISO_load_actuals_<year>.csv, 11 zones, sub-hourly MW) totals
       147.0 / 150.5 / 151.6 TWh, which MATCHES the model's served demand
       147.3 / 150.6 / 151.8 TWh. EIA-930 NYIS demand ≈ NYISO load. The user's
       hypothesis that the load basis was too low is REFUTED — the gap is the
       loss gross-up, not the load level.
     - **The zonal SHAPE is already wired** — eia_loader.nyiso_zonal_load_shares
       (eia_loader.py:1351, called from load_demand at :1999) maps the 11 NYISO
       zones (CAPITL CENTRL DUNWOD GENESE HUD VL LONGIL MHK VL MILLWD N.Y.C.
       NORTH WEST) onto the 6 model zones (Upstate_West, Capital_Hudson,
       Lower_Hudson, NYC, Long_Island, NYISO_external). VERIFY it actually fires
       for all 3 years and that any td_loss gross-up is applied PER ZONE (scales
       each zone's load, preserving the downstate-heavy shape that drives the
       NYC/LI congestion + LMP split) — a flat system gross-up would smear it.
     - Energy identity per year (EIA-923 in-state net gen + measured net imports
       − NYISO load = losses+exports): 2023 +1.4 TWh (1.0%), 2024 +4.4 (2.9%),
       2025 +1.4 (1.0%). This is YEAR-INCONSISTENT (real NY T&D losses are a
       stable ~4–5%), so a single loss factor will not perfectly close all three
       — the variance is partly item 2 below (the import node). The authoritative
       loss factor lives in the **NYISO Gold Book** (data/raw/NYISO/
       2023/2024/2025-Gold-Book-Public.pdf, "Load & Capacity Data" — the official
       transmission-loss percentage); extract it (pdfminer) and use THAT, not a
       residual-minimizing value (rule #12).

2. **SECONDARY (~1.3–2.5 TWh, cross-year-NEUTRAL): the priced import node does
   not track measured net interchange.** The --priced-interchange node clears a
   roughly flat ~18–22 TWh/yr on economics, while the measured EIA-930 net
   interchange DECLINES: 23.45 (2023) → 20.35 (2024) → 19.09 TWh
   (eia_loader.nyiso_net_interchange, :1793). Model imports: 18.53 / 21.65 /
   21.63 — so the node UNDER-imports by 4.9 in 2023 (gas runs over to fill, which
   is why 2023 gas looks fine) and OVER-imports by 1.3 / 2.5 in 2024/25 (backing
   that much gas out). Pinning/penalizing the node toward the measured annual net
   interchange (rule #11 — measured > economic-clearing) recovers 2024/25 gas but
   costs 2023 ~5 TWh, because the demand-basis floor must land somewhere. Treat
   it as the SECONDARY lever AFTER td_loss; the firm-import floor is at
   run_calibration.py ~1717 and the priced node is built in the dispatch path.

THE TASK
Reopen the `td_loss_factor = 0` decision and close the gas-TOTAL deficit with a
REAL, forward-reproducible loss gross-up (rule #11/#12 — NOT a fitted adder):

1. Extract NY's official transmission-loss factor from the NYISO Gold Book
   (data/raw/NYISO/<year>-Gold-Book-Public.pdf) and any exports figure needed to
   reconcile the identity above. Document the source like the gas-hub Figure-A6
   citations in data/raw/nyiso_zonal_gas_hub.csv.
2. Set NYISO `td_loss_factor` to that measured value (per-year if the Gold Book
   gives per-year; scenarios.py:789, threaded through runner.py:210 →
   eia_loader.load_demand :1837/:1882, which scales allocated demand by
   1+td_loss_factor). Confirm the gross-up is applied AFTER/with the zonal-share
   allocation so each zone scales, not a flat system add. (The ERCOT convention
   td_loss=0 stays; this is NYISO-specific — gate it on iso.)
3. Re-examine the import node so 2024/25 stop over-importing vs the measured net
   interchange WITHOUT degrading the 2023 match — reconcile, don't just scale
   (rule #11 caveat: degrading a measured match to paper over a basis gap is
   overfitting). Decide whether the node should be capped/penalized to the
   measured annual net interchange, or whether the td_loss gross-up alone
   suffices once generation = load + losses.
4. The prior calibration's argument for td_loss=0 ("EIA-930 demand is
   transmission-metered, gross-up double-counts") is in docs/calibration-best-so-
   far-nyiso.md and the playbook §8.1 — address it head-on: the gas benchmark is
   net generation (above losses) while the served demand is at the meter (below
   transmission losses), so generation MUST exceed served load by the losses;
   td_loss=0 is the bug that starves gas. If you keep td_loss=0, you must explain
   why gas should equal load−imports with no loss volume.

WORKFLOW / DEFINITION OF DONE
  - Run tests first:
      python -m pytest tests/test_nyiso_local_floors.py tests/test_transmission.py \
        tests/test_reserve_coopt.py -q
    (add a load/demand test if you touch load_demand or nyiso_zonal_load_shares —
    e.g. assert the per-zone gross-up preserves the zonal shares and the annual
    total = NYISO load × (1+loss)).
  - Re-solve ALL 3 years on the current NYISO keeper config (above, NO
    --commitment) in ONE bundle.
  - DONE when sysvol gas moves into tolerance (target EIA-923 grid-delivered gas
    ~59.2 / 67.8 / 70.25 TWh) and the C1 gas classes (CC_REGULAR, CC_CHP,
    CT_PEAKER, ST_GAS) move toward band, WITHOUT breaking price_mean /
    price_shape / dispatch_corr / co2 and WITHOUT a fitted adder. Note the gas
    classes also carry the SOM-grounded offer curve from `nyiso 22` (committed in
    the preceding session, scripts/run_calibration.py _NYISO_OFFER_CURVE) — keep
    it; the merit-order split is already correct, this task adds the missing
    total. CT_PEAKER's residual is the reserve/scarcity tail (out of scope here).
  - Register on the dashboard (calibration-report skill / dashboard_add_run, rule
    #13). If gas comes into tolerance and price holds, it is a KEEPER — update
    frontend/data/backcast/keepers.json (replace 2026-06-23-nyiso-21-family-elig),
    run python scripts/build_status.py, prune the oldest NYISO run for the 15-run
    retention. Commit the slim bundle (meta.json+run_config.json — parquets
    gitignored) + sidecar + runs/<id>.js + changed bench/ + keepers.json +
    status.js; never the deploy files. Rebase onto latest origin/main before
    pushing (413 avoidance).

NOTE (do not re-litigate): the SOM-grounded gas OFFER CURVE (`_NYISO_OFFER_CURVE`,
scripts/run_calibration.py — CC_REGULAR/CC_CHP lowered, ST_GAS committed raised
0.81→0.97 to remove the legacy-steam-undercuts-CC merit inversion, grounded in
the 2023/24 Potomac SOM Figure 2 / §VI.A) is DONE and committed. It fixes the
merit-order SPLIT (CC_REGULAR +2.3–2.5 TWh every year) but cannot add gas TOTAL —
that is THIS task. The NYISO P2 commitment screen is a confirmed no-op and was
dropped from the keeper config. This task is purely the load/demand-basis gross-up
(td_loss) + import-node reconciliation that sets the gas TOTAL.
