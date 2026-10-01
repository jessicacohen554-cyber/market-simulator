# FINDING — caiso-74: the measured battery AS-award reservation is EX-ANTE INERT on the zone-aggregate fleet — the phantom battery discharge windows are a SOC-trajectory/foresight phenomenon, not a power-headroom one (2026-07-11)

**Probe:** `2026-07-11-caiso-74-storage-as` (+ `2026-07-11-caiso-74-storage-as-ablation`
twin), pre-registered single-delta A/B on the caiso-73 recipe:
`caiso_storage_as_reservation=True` — the measured CAISO battery AS-award MW
reserved out of the battery fleet's dispatch headroom. Data = the NEW
`storage-as-awards` intake (CAISO Daily Energy Storage Report quarterly xlsx,
`data/raw/storage-as-awards/CAISO`, curated per the data-dictionary contract):
system-level LESR awards by product, hourly DA (IFM) + 15-min RT (RTPD),
2023–2025; DA battery means 1,010/1,484/1,652 MW reproduce the DMM-published
1,040/1,500 MW anchors to ~1 %. Mechanism = the exact ERCOT
`storage_as_commitment` pattern (upward award reg-up+spin+non-spin subtracted
from the battery power cap pro-rata, batteries only) plus a SOC floor at the
tariff 30-min sustain (`CAISO_AS_SUSTAIN_DURATION_H` = 0.5 h) of the
spin/non-spin award. Zero fitted parameters. Driver:
`FINDING-caiso72-step0-evening-displacement-2026-07-10.md` channel #1 /
`FINDING-caiso73-firm-import-shape-2026-07-10.md` live lead #1. Scripts:
`scripts/probes/_caiso74_storage_as_ab.py`. Scored on rubric v2.4. Registered
per rule 15; NOT proposed for promotion.

## Pre-registered directions vs outcome (2023/2024/2025)

| metric | caiso-73 main | **caiso-74 main** | direction called | actual outcome |
|---|---|---|---|---|
| CT_PEAKER (TWh) | 1.68 / 1.13 / 0.79 | **1.69 / 1.13 / 0.79** | up toward 4.56/5.24/3.09 | **NO MOVE** |
| CC_REGULAR (TWh) | 62.30 / 63.36 / 64.03 | **62.30 / 63.36 / 64.03** | ambiguous (disclosed) | **IDENTICAL** |
| battery h15-17 phantom discharge | (STEP-0 +0.4-1.3 GW vs actual) | unchanged | down | **NO MOVE** |
| C5b storage throughput | over vs actual | unchanged (2025: 10.47 TWh discharged) | down toward actual | **NO MOVE** |
| C3a evening (risk) | +23.5/+33.8/+47.4 % | unchanged | may rise (disclosed) | did not materialize (non-binding) |

Verdict (v2.4): **NOT-YET** — C6 governance PASS (attestation carried, ZERO new
free parameters), C7 PASS, C8 PASS; the load-bearing FAIL cluster (C1, C2,
C3a/b/c, C4, C5a) is byte-inherited from caiso-73 because **the dispatch is
identical to 0.01 TWh in every class-year**.

## Why: the reservation never binds

Measured on the caiso-74 bundle itself:

- 2024 battery fleet (EIA-860, zone-aggregate): **13,209 MW / 59,229 MWh**.
- LP battery discharge: max **9,548 MW**, p99 **6,657 MW** (2024); 2023 max
  5,975 (p99 4,966); 2025 max 9,851 (p99 6,950).
- Upward award subtracted from the cap: mean 439/741/842 MW, max
  1,808/2,750/2,555 MW → derated cap ≥ ~10.4 GW (2024) — **0.9–3.7 GW above
  the LP's maximum hour and ~5 GW above its p99**.
- SOC sustain floor: mean 45/142/200 MWh vs 59 GWh fleet energy —
  three orders of magnitude below the binding surface.

The LP's battery behaviour is energy/economics-limited, not power-limited —
and so is the real fleet's (real CAISO battery peak discharge ≈ 8 GW on a
13 GW fleet). The real AS commitment therefore does not constrain the real
fleet's *energy arbitrage power* either; what it changes is the **SOC
trajectory and the revenue trade-off** (awarded units hold state and follow
AGC instead of perfect-foresight arbitrage). A fleet-aggregate power-cap
derate cannot represent that. The ERCOT analogy fails quantitatively: ERCOT
batteries carry ~2-3 GW of AS on a much smaller fleet — "a large share of the
battery fleet" — where the same construction does bind.

## Disposition (caiso-71 precedent)

- `caiso_storage_as_reservation` ships **default-off**, documented ex-ante
  inert on the CAISO zone-aggregate fleet; NOT carried into subsequent CAISO
  recipes (an always-slack constraint is dead weight, and rule 1 protects
  binding real structure, not no-ops). The intake, mechanism, tests and this
  measurement stay — the measured award series is now on disk for the
  follow-up mechanisms.
- **The battery-operational-realism lead re-attributes** from "AS power
  withheld" to the SOC-trajectory/cycling channel. Measured-groundable
  candidates (queued, in leverage order):
  1. **Cycling/degradation economics**: the LP cycles the fleet with
     `battery_dispatch_adder = 0`; the real fleet runs ≈ 1 cycle/day. A cited
     physical degradation cost (cell wear $/MWh-throughput) is a rule-13
     input, not a tune — needs a primary source, not a residual fit.
  2. **AS-aware SOC posture inside the reserve co-opt** (the
     `_caiso_design` storage duration-gate machinery already exists;
     caiso-59/62 measured the co-opt price-inert, but the SOC-posture effect
     on *dispatch shape* was never isolated).
  3. Non-anticipativity (no perfect foresight) — structural, hardest.
- The pre-registered CT/battery-shape directions were **not confirmed**; the
  evening CT gap attribution stays with the caiso-72/73 ledger's commitment
  channel (see `docs/handoffs/caiso-evening-cc-commitment-design-2026-07.md`,
  whose §0 re-measure gate now applies to the caiso-75 line).

## Ablation twin

Zero-forcing ablation registered alongside
(`2026-07-11-caiso-74-storage-as-ablation`); both reservation legs are
capability bounds and survive ablation by construction. CT_PEAKER ablation
2.82/1.87/0.98 TWh (vs main 1.69/1.13/0.79) — the caiso-70 RA-bridge crowding
signature, unchanged from caiso-73's twin, again confirming the commitment-side
displacement is floor-borne.

## Intake delivered (independent of the probe outcome)

`storage-as-awards` is a permanent, contract-clean datatype: schema
`data/dictionary/schema/storage-as-awards.schema.yaml`, per-ISO registry
module (`scripts/lib/storage_as_awards/`), curation + tmp-CLEAN_DIR tests,
loader `market_sim/data/storage_as_awards.py` with model-frame alignment
(DST-exact, verified vs the DMM anchors), README provenance, raw xlsx
committed by the `apply-caiso74-intake` runner. The 2026 quarterly files
extend the series when rule-22 windows are authorized.
