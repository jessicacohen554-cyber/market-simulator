# CAISO Lever D — solar under-curtailment fix (local deliverability derate)

**Date:** 2026-06-27  **Mode:** implementation pass (no dashboard keeper — Step 6)
**Baseline:** current `main` (post Lever-A, PR #973: gas commitment floor default-OFF,
replaced by the `caiso_ra_mustoffer` commitment).
**Probe:** `scripts/caiso_shape_probe.py` (hourly Pearson *r* + diurnal band, never MAE).
**Reproduction:** per-plant multi-zone 3-yr, keeper flags, two bundles —
`results/calibration/_stepD/{baseline_main,leverD}` (baseline = `--no-…` defaults,
Lever-D = `caiso_solar_deliverability` default-ON for CAISO).

---

## The problem (confirmed on the fixed probe)

The dispatch is handed the *uncurtailed* HSL solar potential and is supposed to
re-curtail endogenously, but even post-Lever-A it dispatches ≈ the full potential
every year and curtails ≈ 0 — the over-run (model − delivered) is essentially the
*entire* real curtailment volume:

```
year  model solar  delivered  potential  over-run  real curtailment
2023     39.79       37.14      39.65      2.65          2.51
2024     47.89       44.64      47.81      3.25          3.17
2025     53.35       49.65      52.17      3.70          2.52 (partial)
```

Root cause (audit Lever D): real CAISO curtailment is ~70 % **local**
(distribution / sub-area congestion) the reduced 3-zone topology cannot see, plus
system oversupply. Disabling negative offers recovers only ~0.6 TWh — a minor
contributor that **stays ON** (real RPS/PTC keep-running value).

## The mechanism (structural, default-ON for CAISO)

`transmission.caiso_solar_deliverability_derate` — the solar-generation analogue
of the accepted WECC corridor ATC derate (`forward_corridor_atc_envelope`). It
caps the per-zone solar dispatch upper bound at

```
solar_pot[z,t] × clip(1 − k × solar_frac(t), floor, 1)
```

where `solar_frac(t)` = `eia_loader.caiso_solar_fraction` (CISO solar / demand) is
a **forward driver** that responds to a changed solar build and load — never the
measured curtailment outcome. As midday solar penetration rises, the local network
evacuates a smaller share of the concentrated solar and the surplus curtails.

`k = 0.15` is derived as the **reference-year** midday curtailment rate ÷ midday
solar penetration — CAISO 2023/2024 midday curt/HSL 0.073 ÷ solar_frac 0.441/0.499
→ k ≈ 0.166 / 0.146, **stable across both reference years** (a structural
sensitivity, not a per-year fit). `floor = 0.50` guards against an unphysical deep
cut and never binds at observed penetrations. The curtailed **volume** emerges
per-year from that year's own forward penetration × potential build — it is not
pinned to actuals (CLAUDE.md #1/#11). The forward-derivable reference-rate pattern
mirrors the already-accepted `renewables._reference_curtailment_rate`.

Wiring: `config.caiso_solar_deliverability` (CAISO default-ON via
`_calibration_config`), `caiso_solar_deliverability_k` (0.15),
`caiso_solar_deliverability_floor` (0.50); applied to `solar_cf` in
`run_calibration._apply_caiso_solar_deliverability`. Toggle off with
`--no-caiso-solar-deliverability`.

An **interim stopgap** (`caiso_solar_cap_at_delivered`, `--caiso-solar-cap-at-
delivered`) caps solar at the measured EIA-930 delivered profile. It PINS solar to
the measured outcome (no forward analogue) and is a **default-off DIAGNOSTIC only**
— never a keeper, never quoted as forecast skill (CLAUDE.md #11).

## Shape result — ACCEPT criteria met (all 3 years)

```
            model solar   delivered   curtailment emerged   real curt    r     band×(vs delivered)
year      base → leverD                base → leverD                   base→D   base → leverD
2023     39.79 → 37.23      37.14       0.00 → 2.42          2.51      .93→.93   1.06 → 0.99
2024     47.89 → 44.47      44.64       0.00 → 3.34          3.17      .93→.93   1.09 → 1.00
2025     53.35 → 49.21      49.65       0.00 → 2.96          2.52*     1.0→1.0   1.07 → 0.98
```
`*` 2025 real curtailment is a partial-year workbook (understated).

* **model solar TWh → ~delivered** every year ✓
* **curtailment 2.42 / 3.34 / 2.96 TWh emerged ENDOGENOUSLY** from the forward
  penetration × build (real 2.51 / 3.17 / 2.52), not pinned ✓
* **solar diurnal r stays ≥ 0.92** (0.93 / 0.93 / 1.00) ✓
* **solar band× falls toward 1.0** (1.06→0.99, 1.09→1.00, 1.07→0.98) ✓

The `solar+curt pot` band× moves from ≈ 1.00 (model on potential) to ≈ 0.91–0.93
(model now below potential by the curtailment), confirming the model re-curtails
off the HSL instead of riding it.

## Midday $0 price — did NOT return; discovered root cause

Expected (task thesis): with the gas floor gone, Lever-D oversupply curtailment
should supply CAISO's midday ~$0 price. It did **not**:

```
midday (h9-15) load-weighted system LMP      <=$0 share
            base (A-only)   leverD            base → leverD
2023          $70.6          $71.9            0.2% → 0.0%
2024          $43.1          $44.7            2.4% → 1.4%
2025          $48.8          $50.0            0.0% → 0.0%
```

Root cause (diagnosed, **not** papered over): a local-deliverability cap *removes*
midday solar supply, so the LP serves midday load with **more** gas, not less —
2024 midday CC_REGULAR rises 10.99 → 12.04 TWh as solar falls 34.71 → 32.00 TWh.
Gas therefore stays marginal midday and the LMP stays positive. The midday ~$0
price is a **system-oversupply** phenomenon (curtailed solar marginal at its
negative offer), which the LP reaches only once the midday CC fleet backs down to
near-zero — the audit's structural fact #1 ("CC_REGULAR over-runs and is too flat
midday"). Curtailing solar works *against* the $0 price; the price is gated by the
midday CC over-run / insufficient back-down, a **separate root cause** belonging to
the CC-back-down / evening-scarcity workstream — not to be faked here (CLAUDE.md
#1: a real mechanism stays in even if the residual doesn't move; fix the real root
cause).

## Status

Lever D ships the structurally-correct solar curtailment (shape/volume mandate fully
met). The midday-$0-price residual is handed to the CC-back-down step. **No dashboard
keeper registered** (Step 6).
