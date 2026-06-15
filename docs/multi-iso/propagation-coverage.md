# Wave W1c — Generic-improvement coverage, per ISO

Records the verification that the ERCOT engine improvements which are
*already* ISO-agnostic (they read per-ISO config) actually **fire for every
registered ISO**, and notes any per-ISO config datum backfilled to close a
gap. This is the acceptance artifact for
`docs/multi-iso/09-ercot-propagation-prompt-pack.md` §1B / W1c.

Verified by `tests/test_iso_coverage.py` (parametrized over every ISO in
`config.iso_configs._ISO_BUILDERS`). **No engine code was changed** and **no
config backfill was required** — every datum the generic capabilities read
was already present and consistent with each ISO's real-world mechanism.

## Where each generic improvement reads its per-ISO config

| Improvement | ISO-agnostic engine code | Per-ISO datum |
|-------------|--------------------------|---------------|
| Full fossil/nuclear economic retirement | `capacity.apply_economic_retirements` (keys off `_THERMAL_FOM`) | per-fuel `ScenarioConfig` defaults (`fixed_om_*`, `retirement_years_*`, `retirement_fom_multiplier_*`) — global, not per-ISO |
| Gas-CT peaker new entry | `capacity._NEW_ENTRY_TECHS` incl. `gas_ct`; entry screen | `QUEUE_CAP_PER_TECH_GW[iso]["gas_ct"]`; `NEW_ENTRY_COSTS["gas_cc"/"gas_ct"]` |
| Price-duration entry economics | `capacity.estimate_expected_revenue` (price shape) | none — universal |
| Priced import/export node | `transmission.build_import_generators` / `build_export_sinks` | `IMPORT_TRANCHES[iso]`, `EXPORT_TRANCHES[iso]`, `IMPORT_ZONE[iso]` |
| State/regional carbon pricing | `policy.carbon.state_carbon_price` | `STATE_CARBON_PRICE_BY_ISO[iso]` |

## Per-ISO coverage matrix

Legend: ✓ = config present & fires · — = deliberately none (matches reality)

| ISO | Retirement (all 7 thermal fuels) | gas_ct new entry | Import node | State carbon | Notes |
|------|:---:|:---:|:---:|:---:|-------|
| **ERCOT** | ✓ | ✓ | — | — | Energy-only, electrical island: no import node, no RGGI/CARB. **Parity baseline.** |
| CAISO | ✓ | ✓ | ✓ | ✓ | WECC import tranches + export sinks; CARB cap-and-trade. |
| PJM | ✓ | ✓ | ✓ | — | Import/export tranches; no single ISO-wide carbon price. |
| MISO | ✓ | ✓ | — | — | No priced import node configured (serves measured interchange). |
| SPP | ✓ | ✓ | — | — | No priced import node configured. |
| NYISO | ✓ | ✓ | ✓ | ✓ | Import tranches + small export sink; RGGI. |
| NEISO | ✓ | ✓ | ✓ | ✓ | Import/export tranches; RGGI (all six NE states). |

Retirement coverage is identical across ISOs because the per-fuel thresholds
are global `ScenarioConfig` defaults applied to whatever thermal units the ISO
fleet contains — the screen covers coal, gas_cc, gas_ct, gas_st, oil,
gas_cc_ccs and nuclear for every ISO.

## Backfill

None. Every per-ISO datum required by the generic improvements was already
present, so no value was added to `constants.py` and no new citation was
needed in `docs/parameter-citations.md`.

## ERCOT parity

No ERCOT value changed. The test pins ERCOT's coverage to today's behaviour:
no import tranches, no `IMPORT_ZONE` entry, an empty import-node build, and a
`None` state carbon price.
