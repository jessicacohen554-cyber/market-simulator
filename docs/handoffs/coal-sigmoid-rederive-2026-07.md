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

## Derivation (`scripts/derive_coal_sigmoid.py`)

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

_[FILLED AFTER SOLVE]_

| criterion | miso-49 | miso-50 | Δ |
|---|---|---|---|
| C1 fuel-mix (classes pass) | 14/16 | | |
| C2 sysvol 2025 gas / coal | −14.7% / +16.3% | | |
| C3a mean LMP 2025 | −8.7% | | |
| C3c tail 2024 / 2025 | 6h / 3h vs 24h / 38h | | |
| determination | NOT-YET | | |

## Keeper-swap recommendation

_[FILLED AFTER SOLVE]_

## Deliverables

- Derive script: `scripts/derive_coal_sigmoid.py`
- Derivation inputs: `src/market_sim/config/constants.py` (coal heat content,
  delivery commodity share, representative HRs, gas trough, slope baseline)
- Registry-resident params: `COAL_SIGMOID_DEFAULTS[("MISO", …)]` in
  `config/scenarios.py`
- Provenance artifact: `data/raw/_processed-legacy/coal_sigmoid_params.csv`
- Freeze/provenance test: `tests/test_derive_coal_sigmoid.py`
- Probe driver: `scripts/probes/_miso_coal_sigmoid_ab.py`
- Bundles: `results/calibration/miso50_coalsigmoid{,-ablation}/`
- Dashboard: registry sidecar + run payload for miso-50 (+ ablation twin)
