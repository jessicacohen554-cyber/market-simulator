# PRECOMMIT — soco-67: `unit_outage_precod_clip` on the SOCO keeper recipe, 2019–2025

Lane soco-67, 2026-09-25. This was written and pushed **before any shard was launched**. The parent solves nothing
(rule 32(a)). Each year is solved in its own shard (rule 36), and each shard pushes its full bundle (rule 34).
The evidence is in `FINDING-soco-67-2026-09-25.md`.

## 1. Lever

**`unit_outage_precod_clip`** is a new `ScenarioConfig` field, gated and off by default. It is registered in
`_CACHE_KEY_OPTIONAL_FIELDS` and in the drop map at `"False"`. The code is
`data/outages.py::clip_precod_unit_windows`, applied inside `unit_outage_derate_factors(precod_clip=)`.
`data/fleet/arrays.py` threads it through.

**Why a new lever.** It is not on SOCO's §5.8 queue, because the queue's CT levers are:

- `tranche_startup_amortization`, which is `G` with the SOCO-65 owner question open.
- The `offer_curve_by_group` bands, which cannot be identified for SOCO (rule 1(c)).

Phase 0 found that the excess sits on a CC fleet pinned at its ceiling. It also found that one ceiling is a
rule-19 double count, and that defect is independent of both of those levers. This is not a re-test of any
`R`/`I`/`G` cell.

**The construction.** A CAMPD unit-outage window is **pre-commercial** when both of these hold:

- **(i)** Its unit is absent from every earlier year of the CAMPD unit-level record. At least one earlier year must
  exist.
- **(ii)** Its own bin `(plant, BIN_GROUP_TO_FUEL[group])` has an EIA-860 constituent whose operating month begins
  after the window start. The constituents come from `cod_ramp.load_unit_cod_map`, the same map the COD ramp reads.

The window's hours before the **earliest** such month are removed. If the window lies wholly before that month, it
is dropped. **Zero free parameters.** Both conditions are categorical, and "earliest" is the conservative choice.

**Rule check:**

| rule | how this lever meets it |
|---|---|
| 19 | The COD ramp alone owns pre-COD absence. |
| 14 | The model's availability is below the plant's own measured output. |
| 13 | It regenerates wherever a CAMPD filing and an EIA-860 vintage exist. It is backcast-only. |
| 24 | It is a registered field, with a matrix row and a cell in every shard (rule 28(c)). |
| 25 | SOCO's own census. |

## 2. Census (zero LP, fleet rebuilds on the keeper recipe)

Each of the seven years was rebuilt twice with `run_year(fleet_only=True)`: once armed and once not.

- **2019, 2020, 2021, 2022, 2024, 2025:** every LP-visible fleet column is **byte-identical**, and so is class
  availability.
- **2023:** only `availability` moves, only on the four Barry CC tranches (`CC_REGULAR_SOCO_AL_p3_*`). CC_REGULAR
  gains **+2.8162 TWh**, and Barry CC goes 4.38 → **7.20 TWh**, against its EIA-923 net of **7.34**.
  - The armed result is identical to a manual clip of unit 8 to 2023-11-01, with max |Δ| of 0.0.
- **Extract rows touched:**
  - Barry 3/8 clipped to 2023-11-01.
  - Lowman 56/CC1 dropped for Jan–Aug 2023, and its Aug 28 window clipped to Sep 1.
  - Lowman 56/NET0-923 dropped for 2021 and 2022.
  - The Lowman rows are inert in the fleet. The COD ramp is already 0, or the plant is absent from that vintage.
- **G-DRIFT** (FINDING §0): all INERT. The committed keeper bundle is the control, and no control solve is spent.

## 3. Recipe

Each shard runs one year, `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document.

```
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. python3 scripts/data/curate_demand_profile.py
python3 scripts/replay_keeper.py results/calibration/rsocob2_boundary_span --years <Y> \
  --out-dir results/calibration/soco67_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --note "soco-67 <Y>: R-SOCO-B2 keeper recipe + unit_outage_precod_clip (Barry unit 8 pre-COD window clipped to its EIA-860 COD month; rule 19)"
```

**Hard stops. A shard that sees otherwise stops and does not push.**

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` shows the six `--set` fields true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log contains `container preflight:` and `memory peak:`.
- 2023 only: the log contains `unit-outage pre-COD clip:`.

## 4. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

These are measured against the keeper's committed legs.

- **E1 (2019–2022, 2024, 2025).** |Δ class TWh| ≤ 0.01 on every class, and identical unserved MWh. The fleet is
  byte-identical, and rule 36's warm-start and basis knobs are off. A larger move falsifies §2 and is reported as a
  finding.
- **E2 (2023, direction and size).** These are anchored on the FINDING §4 greedy estimate. Solved Barry CC energy
  is ≤ its armed availability of 7.20 TWh.

  | class | expected Δ, TWh |
  |---|---|
  | CC_REGULAR | +1.2 to +2.8 |
  | CT_PEAKER | −0.6 to −2.0 |
  | ST_GAS | 0 to −1.0 |
  | every other class | ≤ 0.5 in magnitude |

- **E3 (2023 C1).** The CT_PEAKER row moves from +7.22 TWh / +3.0 pp to between +5.2 and +6.6 TWh, which is
  +2.2 to +2.8 pp. **Predicted PASS**, and a narrow one. No other 2023 C1 row changes status. 2023 unserved stays 0.
- **E4.** C2, C4, C6 and C8 PASS in every year. C3a/b/c stay UNSCORABLE, because SOCO has no price reference.
- **E5.** `gen_soco60b` B1/B2 are unchanged. They are benchmark-side, and the benchmark does not move.

## 5. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all three of these hold:

- All seven legs solve cleanly with the §3 hard stops met.
- E1 holds, or its deviation is fully explained by an identified code path.
- The 2023 change is confined to the Barry CC availability channel. That means no fleet column other than Barry
  CC `availability` moves (§2), and solved Barry CC energy is ≤ its armed availability.

This holds **whatever C1–C8 do**. The mechanism removes a double count that rules 19 and 14 require removed. The
owner decides (rule 31).

If the owner promotes, rule 35 prunes `2026-09-25-r-soco-b2-boundary`. The incoming run covers the full union
{2019, …, 2025}.

## 6. Retrievability (rule 34(e))

- **Legs.** Each shard pushes `results/calibration/soco67_<Y>/` (full bundle, including `dispatch/`) to
  `claude/soco67-<Y>`.
- **Composite.** The parent composes `soco67_span` and lands it on `main` via the lane PR. The per-year dirs are
  gitignored in the parent.
- **Cost.** Any leg not landed is costed as a re-solve, ~10–15 min per year.
