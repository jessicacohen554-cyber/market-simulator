# MISO coal-vs-gas passthrough sigmoid re-derivation — 2026-07-09

**Status: PROBE (miso-50), not a keeper.** Promotion to keeper is an owner
decision after reviewing the before/after deltas below. `keepers.json` is
untouched.

## Rule-23 trigger (why now)

The coal-vs-gas passthrough sigmoid (`COAL_SIGMOID_DEFAULTS` in
`config/scenarios.py`) is a frozen measured-behaviour parameter set: it
re-derives ONLY when its SOURCE DATA updates, never because a residual moved
(CLAUDE.md rule 23). The trigger here is the **#1803 intake**, which added the
coal-commodity price series a real re-derivation needs and which were
previously absent (`docs/handoffs/coal-price-data-intake-2026-07.md`):

- **EIA Annual Coal Report** region × rank f.o.b.-mine price, 2001–2024 annual
  (`data/raw/coal-prices/eia_coal_price_by_rank.part*.csv`).
- **BLS PPI** coal-mining, 2010–2026 monthly (`bls_coal_ppi.csv`).
- Region → coal-plant crosswalk, per ISO
  (`data/raw/reference/coal_region_crosswalk.csv`).

Before #1803 the sigmoid `floor`/`ceil`/`gas_mid`/`gas_slope` were hand-tuned
per (ISO, supply) with no coal commodity price behind them, and **MISO's
`gas_mid`/`gas_slope` were literal byte-copies of ERCOT's `2.85`/`2.5`** — the
rule-24 cross-ISO-leak wart logged as issue #1347 / gap G-26. This re-derive
retires those copies.

**Honesty gate:** every parameter is fit to measured region f.o.b./PPI
movement (+ cited heat/transport/heat-rate constants + the observed gas
trough), never to any MISO price/volume residual (rules 10/11).

## Derivation (`scripts/data/derive_coal_sigmoid.py`)

The gas-keyed passthrough MECHANISM is kept (G-26 disposition R6
DOCUMENT-AND-KEEP; a take-or-pay / mine-mouth / rail coal contract makes
delivered fuel cost mostly fixed and NOT gas-indexed, so the tranche bids
toward its own delivered cost, discounting only to hold merit against cheap
gas). Only its four numbers are re-grounded, per (ISO, supply):

| param | grounded in | formula |
|---|---|---|
| `gas_mid` | region f.o.b. → delivered coal cost | `deliv$/MMBtu × HR_coal / HR_cc` (the coal-vs-gas-CC merit crossover in gas-price space) |
| `ceil` | cost-tracking basin economics | `1.0` — coal never bids above full measured delivered cost |
| `floor` | observed cheapest gas | `gas_min / gas_mid`, clipped `[0.50, ceil]` |
| `gas_slope` | cross-region delivered-cost dispersion + PPI | `1 / σ_gas`; single-region groups → baseline `2.5` |

Delivered cost lifts the f.o.b. by delivery mode (`COAL_DELIVERY_COMMODITY_SHARE`):
PRB-by-rail `/0.42` (long-haul rail dominates, the cited PRB decomposition →
~$2.01/MMBtu), Interior/Appalachian bituminous `/0.85` (short rail →
~$2.57/MMBtu), mine-mouth lignite `/1.00`. Heat contents by rank from EIA MER
A5; representative heat rates HR_coal 10.0 / HR_cc 6.7 from EIA Table 8; gas
trough $2.19 (MISO 2024 delivered gas). Capacity- and heat-rate-weighted over
each ISO's coal fleet via the crosswalk. All inputs are registry-resident in
`constants.py` (rule 24); the derived literals live in `COAL_SIGMOID_DEFAULTS`;
the full provenance table is `data/raw/_processed-legacy/coal_sigmoid_params.csv`.

### MISO before → after

| supply | | floor | ceil | gas_mid | gas_slope |
|---|---|---|---|---|---|
| prb | miso-49 (ERCOT copy) | 0.78 | 0.98 | **2.85** | 2.5 |
| prb | **re-derived** | 0.687 | 1.0 | **3.187** | 2.5 |
| prb_follower | miso-49 | 0.68 | 0.92 | **2.85** | 2.5 |
| prb_follower | **re-derived** | 0.598 | 1.0 | **3.187** | 2.5 |
| bituminous | miso-49 | 0.55 | 0.95 | **2.85** | 2.5 |
| bituminous | **re-derived** | 0.532 | 1.0 | **4.115** | **1.092** |

What moved and why (measured, not residual):
- **`gas_mid` is now region-specific.** MISO PRB (delivered ~$2.01) crosses
  gas-CC at $3.19; cheap ILB/App bituminous (delivered ~$2.57 — cheaper vs gas
  than the blend implies) only at $4.12, ABOVE the entire 2023–2025 observed
  gas range (2.19–3.52), i.e. MISO bituminous is inframarginal (deeply
  discounted, always in merit) across the window — economically correct for
  cheap Interior/Appalachian coal, and exactly what the flat 2.85 byte-copy
  mis-stated.
- **`ceil` → 1.0** everywhere: cost-tracking basins never mark up past full
  delivered cost (retires the residual-tuned 0.92–0.98 markdown).
- **`gas_slope` for bituminous → 1.092**: the real across-region delivered-cost
  spread (IL $2.4 / IN $3.0 / KY $3.9 / ENC $2.7 delivered) widens the
  crossover; single-region PRB keeps the baseline 2.5 (annual region f.o.b.
  resolves no within-group spread — the granularity caveat).

### Other ISOs (delivered, unused)

The derive computes ERCOT/PJM/NEISO region-weighted params too (in the
provenance CSV) — but their live `COAL_SIGMOID_DEFAULTS` entries are LEFT
UNCHANGED: their re-solves are separate owner lanes (PJM owner-midstream,
CAISO in-flight, NEISO complete, NYISO descoped). Only MISO is wired and
re-solved here.

## Granularity caveat (rule-23, expected-null-result clause)

The fit is annual f.o.b. (latest ACR = 2024; 2025 has no ACR yet, PPI-proxied)
and region-level. It resolves the crossover LEVEL but not daily basin-spot
movement (PRB 8800 / ILB / NAPP daily indices remain S&P/Argus-paywalled). **If
the re-derive does not move MISO's C2 sysvol / C3a coal-vs-gas residual, the
residual is genuinely daily-basin-spot-gapped, not something to force** — it is
NOT tuned to close it (rules 10/11).

## Before/after results (miso-50 vs miso-49 keeper)

Both bundles solve 2023–2025, per-plant, one bundle (rule 16). miso-50 is the
miso-49 recipe with ONLY the re-derived MISO sigmoid swapped in.

| criterion | miso-49 (keeper) | miso-50 (re-derive) | direction |
|---|---|---|---|
| C1 fuel-mix — classes pass (all / free) | 14/16 · 10/12 | **9/16 · 5/12** | worse |
| C1 2023 COAL_PRB | +8.84 TWh | **+30.60 TWh** | worse |
| C1 2023 COAL_BIT | (in band) | **+13.88 TWh** (new fail) | worse |
| C1 2024 COAL_PRB / COAL_BIT | (in band) | **+27.06 / +16.32 TWh** | worse |
| C2 sysvol 2025 gas / coal | −14.7% / +16.3% | **−16.5% / +24.5%** | worse |
| C3a mean LMP 2023 / 2024 / 2025 | −2.5% / −1.0% / −8.7% | **+18.0% / +6.3% / +5.2%** | worse (over) |
| C3b NRMSE 2023 / 2024 | (CAVEAT) | **0.280 / 0.291 FAIL** | worse |
| C3c tail 2023 (model vs DA) | 0h vs 1h | **33h vs 1h** (over) | worse |
| C4 coal dispatch corr 2023 / 2024 | PASS | **r 0.834 / 0.844 FAIL** | worse |
| C5a CO₂ 2023 / 2025 | PASS | **+13.1% / +10.8% FAIL** | worse |
| C6 / C7 / C8 protective | PASS | **PASS** | unchanged |
| C8 COAL forced share (D-2) | 0.1–0.3% | **0.1–0.2%** | unchanged |
| determination | NOT-YET | **NOT-YET** | unchanged label, more fails |

**Reading it (rules 1/10/11 — this is the discovered result, not a failure to
tune).** The re-derive grounds the MISO coal offer in measured f.o.b.: cheap
PRB (delivered ~$2.01, crossover $3.19) and cheaper-still Interior/Appalachian
bituminous (delivered ~$2.57, crossover $4.12 — above the whole 2.19–3.52
observed gas window) are, on their measured commodity cost, deeply
inframarginal, so the sigmoid discounts them harder across the observed range
(PRB passthrough ~0.74/0.71/0.90 vs miso-49's 0.84/0.81/0.95; bituminous
~0.60 vs 0.68 at 2023 gas). Result: MISO coal dispatches MORE, and the
pre-existing coal-for-gas over-substitution **worsens across the board**.

Crucially, **C8 shows COAL is only 0.1–0.2% forced** — the extra coal is
*economic merit*, not floor-forcing. So the measured offer genuinely makes coal
win; the model is not cheating it in. That is exactly the rule-11 signal: the
ERCOT byte-copy's shallower discount (higher floor/ceil) was silently
**compensating** for a miscalibration elsewhere by pricing coal artificially
UP. The real root cause of the MISO coal over-run is **gas-side / daily-basin-
spot granularity**: the annual ACR f.o.b. (and the annual gas price) cannot
resolve the daily gas troughs where gas decisively out-competes coal and coal
cannot ramp to parity; the daily basin spot indices that would close it are
S&P/Argus-paywalled (rule-23 granularity caveat, and the #1803 documented gap).
Per rule 11 the accurate measured input is **kept**; the fix is the root cause
(gas daily shape / seam imports / commitment), never an offer re-tune (rule 10).

**Rule-20 zero-forcing ablation twin** (`2026-07-09-miso-50-coalsigmoid-ablation`,
bundle `results/calibration/miso50_coalsigmoid-ablation`): the same recipe with
ALL commitment/forcing floors OFF is **near-identical** to the main run —
COAL_PRB +30.60→+30.65, COAL_BIT +13.88→+13.91, 2024 COAL_PRB +27.06→+27.22 TWh.
This is decisive evidence that the coal over-run is **100% economic merit**, not
floor-forcing (independently, C8 reads COAL 0.1–0.2% forced). The measured offer
genuinely wins coal on merit; the model is not forcing it.

The DOF ledger reflects the honest improvement: `COAL_SIGMOID_DEFAULTS[MISO]`
moves from a `residual` DOF to `measured-physical` (n_residual 4→3), and the
governance attestation carries `no_fit_to_price_residuals: true`.

## Keeper-swap recommendation — **HOLD (do not promote)**

Owner decision; I do not edit `keepers.json`. Recommendation: **do NOT promote
miso-50 as a fit improvement — it is not one.** The keeper stays
`2026-07-08-miso-49-tempderate`.

- **Keep the re-derived MISO sigmoid params in-tree** (they ship in this
  commit): they are the accurate, measured, forward-reproducible input and
  retire the rule-24 ERCOT byte-copy (#1347/G-26). Reverting them to chase the
  fit would re-bury the error inside an inaccurate input (rule 11 forbids this).
- **The keeper config resolves these same params**, so if/when the owner wants
  miso-49's *number*, note miso-49 was scored with the OLD sigmoid; a re-score
  of miso-49 at HEAD now uses the re-derived params (i.e. miso-49 and miso-50
  are now the same offer surface). The keeper's frozen bundle is unaffected, but
  a fresh miso-49 solve at HEAD would reproduce miso-50. **This is the real
  decision the owner must make:** either (a) accept the measured params as the
  new MISO offer surface and open the gas-side root-cause investigation (rule-1/
  rule-11 correct path), or (b) if the compensating effect is needed short-term,
  gate the re-derive behind a flag so the keeper's frozen surface is preserved
  until the root cause lands. I recommend (a).
- **Open root-cause item:** MISO coal-for-gas over-substitution is a gas-side /
  daily-spot-granularity gap, not a coal-offer-level problem — tracked for a
  future gas-daily-shape / seam / commitment investigation, NOT a sigmoid
  re-tune.

## Deliverables

- Derive script: `scripts/data/derive_coal_sigmoid.py`
- Derivation inputs: `src/market_sim/config/constants.py` (coal heat content,
  delivery commodity share, representative HRs, gas trough, slope baseline)
- Registry-resident params: `COAL_SIGMOID_DEFAULTS[("MISO", …)]` in
  `config/scenarios.py`
- Provenance artifact: `data/raw/_processed-legacy/coal_sigmoid_params.csv`
- Freeze/provenance test: `tests/test_derive_coal_sigmoid.py`
- Probe driver: `scripts/probes/_miso_coal_sigmoid_ab.py`
- Bundles: `results/calibration/miso50_coalsigmoid{,-ablation}/`
- Dashboard: registry sidecar + run payload for miso-50 (+ ablation twin)
