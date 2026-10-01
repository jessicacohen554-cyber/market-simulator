# FOM defaults flip + foresight A/B on reconciled code (2026-07-07, G-32)

*Closes G-32 (`docs/gap-register-2026-07.md`): the ATB FOM flip that Stage
2/5 (`fom-scarcity-joint-protocol-2026-07-05-stage2.md`,
`fom-scarcity-joint-protocol-2026-07-06-stage5-energy-only-floor.md`) left
frozen-but-unflipped, plus the foresight A/B re-run on reconciled code those
stages deferred. Forecast probes only — nothing here touches the backcast
dashboard, a keeper, or a holdout year (rule 22).*

## 1. The flip

`fixed_om_gas_ct` 8.0 → **21.0**, `fixed_om_gas_cc` 12.0 → **30.0**,
`fixed_om_coal` 40.0 → **45.0** (`config/scenarios.py`) — the NREL ATB 2024 /
EIA-S&L targets both Stage 2 and Stage 5 identified and froze without
flipping, each pending "a real reason" (the accredited floor / adequacy
backstop masking the bar, not a rejection of the target itself). Five
mechanism tests in `tests/test_capacity.py` that hard-coded crafted margins
against the legacy 8/12/40 bars now pin those values explicitly via
`with_overrides` so they stay independent of the default (behavioral
identification tests should not silently ride a default they don't intend to
exercise).

## 2. Foresight A/B re-run (plan §2.4) on the flipped default

Same harness, same grid shape as the 2026-07-06 run
(`docs/handoffs/foresight-ab-ercot-2026-07-06.{md,json}`, the legacy-FOM
baseline): ERCOT, 2026-2040, legacy equal-width bins, backstop ON, scarcity
pricing ON, 4 arms × {high, mid} growth. New report:
`docs/handoffs/foresight-ab-ercot-2026-07-07.{md,json}`.

**Causal isolation.** Between the legacy baseline's commit and this run's
HEAD, six non-FOM commits touched `capacity.py`/`runner.py`/`scenarios.py`/
`offer_curves.py`/`dispatch.py`. Each was audited and is inert for this
grid: an ERCOT `on_line_capacity_envelope` probe (default-off, rejected); a
G-26 dead-code deletion explicitly stated "no dispatch values changed"
(confirmed CAMPD-bin-only in `plant_tranche_bands`, unreachable under this
grid's `use_campd_bins=False`); the CAISO P2→P1-native RA bridge port
("byte-identical for non-CAISO"); the NEISO RPS-ACP infeasibility fix
("ERCOT/PJM byte-identical, rps_target 0"); two `cc_duct_peaking` CAMPD
peaking-default commits, both scoped to `backcast_config.py` and CAMPD
per-plant bands (this grid never calls `backcast_config.py` and runs
`use_campd_bins=False`); and a reserve-block memory-peak optimization
pinned byte-identical by its own CSR-hash test. **The FOM flip is the sole
behaviorally-relevant change** between the two reports for this ERCOT
legacy-bin forecast path.

### 2.1 Headline comparison vs the legacy-FOM baseline

| Growth | Arm | Legacy FOM ΔCO₂ | Legacy backstop | Flipped FOM ΔCO₂ | Flipped backstop | retired GW (flipped) |
|---|---|---:|---:|---:|---:|---:|
| high | ewma | +4.8% | 31.8→35.9 GW | +4.6% | 28.5→32.7 GW | 6.3 |
| high | lookahead | **+18.1%** (wrong-direction) | 31.8→**91.2 GW** | **−6.7%** (preferred) | 28.5→**0 GW** | 0.0 |
| high | both | +8.9% (wrong-direction) | 31.8→69.2 GW | **−9.9%** (preferred) | 28.5→**0 GW** | 0.0 |
| mid | ewma | +0.2% | 47.1→43.9 GW | −0.1% | 41.0→38.6 GW | 0.0 |
| mid | lookahead | −5.8% (preferred) | 47.1→43.2 GW | **−30.4%** | 41.0→**0 GW** | **12.68 (= 100% of coal fleet)** |
| mid | both | −6.5% (preferred) | 47.1→44.1 GW | −15.3% | 41.0→**0 GW** | 0.0 |

The legacy-FOM run's headline blocker — the high-growth stress case moving
CO₂ the *wrong* direction under `lookahead` (+18.1%, backstop nearly
tripling) — **does not reproduce under the flipped FOM**: both `lookahead`
and `both` are now CO₂-reducing and backstop-eliminating in high growth,
with the mid-growth benefit direction preserved and larger.

### 2.2 What actually changed, mechanism by mechanism

**High growth (clean read).** `lookahead`/`both` retire **zero** MW
(`retired_mw_by_fuel: {}`) and the backstop and floor are **zero in every
year 2027-2040**. Cumulative economic entry rises to 154-165 GW (vs 101 GW
base) across a diversified mix (gas_cc/ct, solar, wind, nuclear,
geothermal) — the high-growth regime stays in permanent scarcity (base mean
price still ≈$807/MWh) regardless of FOM, so no unit — old or new — ever
fails the going-forward bar; the entire growth gap is met by front-loaded
economic entry, and the backstop is never needed. This is the plan §2.4
mechanism working exactly as designed: a materially higher-fidelity signal
(the re-priced stack) pulls entry forward enough that the reserve-margin
backstop, a blunt instrument, has nothing left to do.

**Mid growth, `lookahead` (flagged, not a clean read).** `retired_mw_by_fuel:
{"coal": 12678.0}` — **the entire ERCOT coal fleet retiring in what the
per-year series shows as a single step** (CO₂ falls from 193.0 Mt in 2032 to
174.6 Mt in 2033, price jumps 25.3→44.3 $/MWh the same year, then climbs
monotonically to $495/MWh by 2040 as the system never fully recovers). This
is the exact fingerprint Stage 5 diagnosed as the **G-31 zone-bin
re-aggregation cliff**
(`capacity-economics-retirement-grain-2026-07.md`): under legacy equal-width
bins the fleet is one aggregated tranche per fuel-class-zone after year 1,
so an economic-retirement verdict fires for the *whole* class at once
instead of a staggered, plant-by-plant exit. Stage 5 tripped this cliff via
`market_design_retirement_floor` (disabling the floor for energy-only
ERCOT); this run trips the **same underlying grain artifact** via a
different route — the higher ATB FOM bar finally makes the coal-vs-revenue
comparison bind (Stage 2/5 found the legacy 8/12/40 bars too low to ever
bind), and the lookahead price signal's more decisive verdict pushes the
whole aggregated bin over the line together. **The mid-growth −30.4% number
is not clean evidence the lookahead mechanism is working as designed — it is
the same known fleet-representation artifact, now triggered by the FOM
flip instead of the floor-disable flag.** `both` (mid) retires 0 GW and
shows a smaller, cliff-free −15.3% move, closer in shape to the legacy
run's −6.5% (same direction, larger magnitude) — the EWMA blend evidently
smooths the same signal enough to avoid tripping the aggregated-bin
threshold in that one arm.

### 2.3 Recommendation (not a promotion decision — owner's call, as before)

This session's job was the flip + the reconciled-code re-run, not the
foresight-mechanism promotion decision (still explicitly "decision pending
owner" per `foresight-adjudication-memo-2026-07-06.md`). New evidence for
that decision: the flipped-FOM high-growth reversal that blocked promotion
is gone, and the mechanism's *clean* cells (high-growth both arms, mid
`both`) are now consistently CO₂-reducing and backstop-eliminating. But the
mid-growth `lookahead` cell's magnitude is inflated by G-31, so it cannot be
quoted as the mechanism's effect size until G-31 lands. **G-31 remains the
blocking prerequisite** for any promotion that leans on retirement-pace or
CO₂-magnitude evidence from a legacy-bin grid — unchanged from Stage 5's
conclusion, now with a second, independent trigger route demonstrating the
same artifact.

## 3. Backcast invariance (rule 22 — no holdout touched)

`fixed_om_*` fields are read in exactly one place in `src/`:
`model/capacity.py`'s `_THERMAL_FOM` lookup, consumed by
`apply_economic_retirements`/`resolve_adequacy_requirement_mw` — both called
only from the forecast capacity-evolution path (`evolve_fleet`,
`runner.py`'s per-year forecast loop). `scripts/run_calibration.py` and
`scripts/run_calibration_full.py` (the backcast harnesses) never call
`evolve_fleet` or any economic-retirement/entry function — backcast mode
has no capacity evolution by construction (methodology spec §5.1 applies to
forecast years only). No backcast keeper, registry entry, or dashboard file
changes as a result of this flip. Confirmed with a repo-wide grep for
`fixed_om_gas_ct|fixed_om_gas_cc|fixed_om_coal|_THERMAL_FOM` (hits only in
`capacity.py`/`scenarios.py`) and a grep of both calibration scripts for
`evolve_fleet`/`apply_economic_*` (zero hits). This session touched no
holdout year (2022, H1-2026) — forecast probes only, 2026-2040.

## 4. Tests

`tests/test_capacity.py`: 5 tests in `TestRetirementMargin`,
`TestScreenReserveValue`, and `TestReliabilityFloorAccredited` pinned their
crafted FOM bars explicitly (they were previously riding the legacy default
incidentally, not by design) — one `going_forward_cost` assertion updated
from the legacy 40×1.3 product to the new 45×1.3 product. Full
`test_capacity.py` + `test_golden_forecast_bands.py` (fixture-parse tier)
green except the one pre-existing, unrelated `TestConfirmedExits` failure
present on `main` before this session.

## 5. Artifacts

- Flip: `config/scenarios.py` (`fixed_om_gas_ct`/`fixed_om_gas_cc`/`fixed_om_coal`).
- Tests: `tests/test_capacity.py` (5 tests re-pinned, 1 assertion updated).
- Harness resumability (unblocks future re-runs, not itself a finding): per-arm
  checkpointing + resume in `scripts/run_foresight_ab.py` (`--fresh` to force
  a clean re-run), so an interrupted grid resumes from whichever year/arm it
  last completed instead of restarting from scratch.
- A/B report: `docs/handoffs/foresight-ab-ercot-2026-07-07.{md,json}`.
- Prior baseline (legacy FOM, for comparison): `docs/handoffs/foresight-ab-ercot-2026-07-06.{md,json}`.

*Produced 2026-07-07. Nothing here is a keeper, a registered backcast run,
or a holdout-year solve.*
