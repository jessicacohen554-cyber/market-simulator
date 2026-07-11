# PJM bituminous = marginal/price-responsive — session handoff (2026-06)

**Thesis (user, 2026-06-22):** PJM bituminous coal should **not** carry a
PRB-style take-or-pay must-run sigmoid like ERCOT. In PJM, bituminous buys coal
on more spot/market terms (not mine-mouth take-or-pay), so it is the **marginal,
price-responsive swing fuel** that backs down when gas is cheap — not cheap
baseload held flat. The current config discounts it like PRB, which over-runs
its capacity factor.

## Where we are

- **Branch:** `claude/pjm-coal-bituminous-campd-xc26g4` (4 commits ahead of
  `main`). The CAMPD benchmark NaN fix (`campd.plant_hourly_net`) is **already
  merged to main**.
- **Keeper on dashboard:** `pjm_42_campdfix` = "pjm 42 campd-nan-fix"
  (id `2026-06-22-pjm-42-campd-nan`). Config = `_pjm_retiree_run.py` (pjm_28
  base + `retiree_cems_cap`). Determination NOT-YET (the documented structural
  coal/LMP miss; C6 governance attested).
- **Benchmark is now trustworthy.** The NaN bug had halved the per-plant CAMPD
  series for multi-unit coal/CT plants on the unit-level extracts (OH/WV/IN/KY/
  VA). Fixed → COAL_BIT CAMPD 104/108/128 TWh (was 48/48/62) vs EIA-923 ~105/
  110/131. So the **charts-page per-class hourly r / NRMSE and the per-plant
  commitment heatmaps are valid now** — judge changes on hourly shape, not just
  annual TWh. (Method check: `gross×parasitic`+heat-proxy is most faithful to
  923, −1.5/−2.0/−2.0%; see `docs/multi-iso/pjm-coalbit-campd-nan-2026-06.md`.)

### Current scorecard (pjm_42_campdfix, corrected benchmark)

| year | coal-tot | COAL_BIT | COAL_PRB | gas | LMP | net-export |
|---|---|---|---|---|---|---|
| 2023 | +9.2% FAIL | +9.1% | +28.9%* | +2.8% | +3.0% | +27% |
| 2024 | +1.6% PASS | +1.2% PASS | +33.3%* | +5.1% | −7.8% | +15% |
| 2025 | +9.4% FAIL | +7.8% | +48.6%* | +2.9% | −14.5% | +82% |

*COAL_PRB residuals are large in % but small in TWh (PRB is a minor PJM class).
The coal-bit over is ~92–94% in the take-or-pay BASE tranches and is
export-driven (`pjm-coal-overrun-decomp-2026-06.md`).

## How bituminous is currently treated (the levers to revisit)

PJM uses **per-plant CAMPD bins** (`bins_to_fleet`, `fleet.py:~5051`), and the
active coal flags are:

- `coal_mustrun_per_plant = True` → bituminous plants get a measured must-run
  floor from `COAL_MUSTRUN_BY_PLANT` (`fleet.py:3715`). The `_mustrun` tranche
  bids **VOM+carbon+NOx only (fuel sunk)** → always in merit, no Pmin needed.
- `coal_bit_passthrough_sigmoid = True`, `coal_bit_passthrough_floor = 0.76`
  (`config/scenarios.py:879-880`; applied in the coal passthrough,
  `fleet.py:~2045-2090`). This discounts the must-run+committed **fuel** ~24%,
  so bituminous bids **~$6–7/MWh below delivered cost** → clears as cheap
  baseload. This is the PRB-style treatment the user wants OFF for bituminous.
- Measured anchor: delivered bituminous **$3.03/MMBtu** (2024, EIA-923,
  qty-wtd) × physical HR **~10.5** ⇒ full-cost SRMC ~$32 + VOM; the model's
  sole-marginal COAL_BIT clears ~$29 (implied HR ~9.6) — confirming the 0.76
  under-bid.

## The work: make bituminous marginal, verify on hourly shape

1. **Raise `coal_bit_passthrough_floor` 0.76 → ~1.0** (full delivered-cost
   passthrough on the above-must-run tranches) so bituminous bids its real
   marginal cost and is dispatched by price, not held as discounted baseload.
   Ground the value in measured delivered cost + physical HR (above), **not**
   tuned to the volume residual (CLAUDE.md #1/#11).
2. **Reduce the bituminous must-run floors** (`COAL_MUSTRUN_BY_PLANT` for
   bit-classed plants) toward what CAMPD actually shows as the minimum sustained
   level — the must-run share is what keeps the base tranche cheap-and-on. The
   floors should reflect real PJM bituminous min-gen behaviour (cycling, spot
   coal), which is lower/more variable than PRB mine-mouth. Keep PRB's sigmoid +
   floors as-is (mine-mouth take-or-pay is correct for PRB).
3. **Judge on the now-correct per-plant hourly CAMPD**, not the annual gate:
   per-plant **hourly r, NRMSE, and CF-shape** for Cardinal (2828), Kyger Creek
   (2876), Gavin (8102), Amos (3935), Cardinal etc. A faithful marginal-bit
   model should track the real CF *shape* (down in low-price hours, up in
   high-price) — the charts page now shows this. Annual COAL_BIT TWh passing is
   necessary but not sufficient.

### The caveat that killed this as a standalone fix before — and why it's
### worth re-testing now

The earlier probe (floor 0.76→1.0, 2024) flipped COAL_BIT/coal-tot to PASS but
**relabelled ~7 TWh coal→gas** (gas over deepened +5.7→+7.8%) and lifted LMP
only +$0.5, because gas is co-marginal ~50% of hours and refills at the same
price (`pjm-coal-overrun-decomp-2026-06.md`, probe #2). The over-run is
~92% base + export-driven (PJM LMP ~$8–10 low → over-export pulls cheap coal
across the seam). **So pair the bit-marginal change with the price-formation
frontier** (gas-marginal offer body / reserve-scarcity pricing — the parked
`pjm-reserve-ordc` / `derive_dam_offer_hrmults` lever C). Lift PJM's afternoon
clearing price toward actual and the export spread (hence the cheap-coal-over)
collapses with it.

**What's different now:** the benchmark is fixed, so for the first time we can
see whether marginal-bit improves the *hourly merit-order placement / CF shape*
per plant — which is the structurally-honest test (right plants running the
right hours), independent of the annual coal→gas relabel. If marginal-bit makes
the per-plant CF *shape* track CAMPD better even where the annual total barely
moves, that's a keeper on faithfulness grounds (CLAUDE.md #1), and the residual
level is then the price-formation job.

## Commands (env: `.venv/bin/python`; PJM per-plant solve is GB-heavy → ONE year at a time)

```bash
# score / decompose the current keeper
.venv/bin/python scripts/probes/_pjm_score.py pjm_42_campdfix
.venv/bin/python scripts/probes/_pjm_coal_decomp.py pjm_42_campdfix
# CAMPD->net-MWh method check (gross×parasitic vs heat/HR vs steam-corrected)
.venv/bin/python scripts/probes/_pjm_coalbit_campd_method.py

# re-solve with the bit-marginal change (clone _pjm_retiree_run.py, set
# coal_bit_passthrough_floor≈1.0 and lowered COAL_MUSTRUN_BY_PLANT for bit) —
# all three years, one at a time (memory), then merge + register:
.venv/bin/python scripts/probes/_pjm_<new>_run.py 2023 results/calibration/<b>_y2023
.venv/bin/python scripts/probes/_pjm_<new>_run.py 2024 results/calibration/<b>_y2024
.venv/bin/python scripts/probes/_pjm_<new>_run.py 2025 results/calibration/<b>_y2025
.venv/bin/python scripts/probes/_pjm_aswh_merge.py results/calibration/<b> \
    results/calibration/<b>_y202{3,4,5}
# register on dashboard (/calibration-report skill or):
.venv/bin/python scripts/dashboard_add_run.py --label "pjm 43 <kw>" --bundle results/calibration/<b>
```

Per-plant hourly model-vs-corrected-CAMPD CF compare (reused this session):
build the corrected CAMPD via `run_calibration_full._campd_hourly_frame(year,
"PJM", _parasitic_factor_map(), 8760)`, the model from
`<bundle>/dispatch/<year>_P1.parquet` (group by `plant_code`), and compare
hourly CF + count `model-on & campd-off` hours.

## Key files

- `src/market_sim/data/fleet.py` — `bins_to_fleet` (~5051), `COAL_MUSTRUN_BY_PLANT`
  (3715), coal passthrough/take-or-pay discount (~2045-2090), `split_coal_tranches`
  (~1889).
- `src/market_sim/config/scenarios.py` — `coal_bit_passthrough_sigmoid` /
  `coal_bit_passthrough_floor` (879-880), PRB equivalents (847+).
- `scripts/run_calibration_full.py` — `solve_and_persist` (passes the coal flags).
- `scripts/probes/_pjm_retiree_run.py` — the keeper recipe to clone.
- `scripts/render_calibration_html.py` (`build_payload`) + `scripts/probes/_backcast_shell.py`
  — the charts page (per-class r/NRMSE, commitment heatmaps).
- Docs: `pjm-coalbit-campd-nan-2026-06.md` (this session), `pjm-coal-overrun-decomp-2026-06.md`
  (lever audit), `pjm-coal-offer-handoff-2026-06.md`, `pjm-reserve-ordc.md`.

## Guardrails (CLAUDE.md)

- #1/#11: right structure first; ground the floor/passthrough in measured
  delivered cost + physical HR, never tune to the price/volume residual. A
  marginal-bit change that worsens the annual fit but tracks the real CF shape
  is a keeper; a fitted number that hits the total is not.
- #12: EIA-923 stays the class-total gate; CAMPD is the hourly-shape diagnostic.
- #13: solve & register ALL years (2023-2025) in one bundle; top-15-per-ISO
  retention, PJM labelled `pjm N <keyword>` (next is `pjm 43`).
- Memory: PJM per-plant LP is several GB — solve one year at a time, no pandas
  probes during a live solve.
