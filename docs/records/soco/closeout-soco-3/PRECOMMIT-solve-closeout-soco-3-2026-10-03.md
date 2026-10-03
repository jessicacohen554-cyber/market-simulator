# PRECOMMIT-solve — closeout-SOCO-3: the take-or-pay pile on SOCO, 2019–2025 (R-49 step 3)

Lane closeout-SOCO-3, 2026-10-03. This is pushed **before** any shard launches.

- **Owner ruling:** R-49, plan §5.0 (main @ `18b525cb`).
- **Desk rulings:** #7134 MERGE; step-3 GO with the CC rule below.
- **Zero-LP record:** `FINDING-closeout-soco-3-phase0-2026-10-03.md` and `RESULT-phase1-closeout-soco-3-2026-10-03.md`.
  All three phase-1 bars cleared.

## Recipe

**Pin:** `0629d7955843948313beaa5c5f1d7a48e52ef4ef` (main). It carries:
- #7134 @ `9f2fe6df`, the EIA-923 Page 2 coal stocks 2015–17;
- #7137, the SOCO gate lift (`COAL_PLANT_GRAIN_ISOS`, `COAL_TAKE_FLOOR_ISOS`, `COAL_TAKE_FLOOR_MEASURED_ONLY_ISOS`).

**Solve:** one shard per year, 2019–2025 (rule 36), each running

```
python3 scripts/replay_keeper.py results/calibration/closeout_soco_2_span --years Y --out-dir results/calibration/closeout_soco_3_Y \
  --set coal_fuel_inventory_plant_grain=true --set coal_fuel_inventory_take_floor=true \
  --set coal_fuel_inventory_monthly_pile=true --set coal_monthly_pile_measured_receipts=true
```

The control is the keeper `2026-10-03-closeout-soco-2-nuclear` (`closeout_soco_2_span`, legs @ `826333c4`), per rule 29(b).

## G-DRIFT (keeper legs `826333c4` → pin)

- **Audit:** `GDRIFT-closeout-soco-3-keeper-to-pin-2026-10-03.md`, covering `826333c4` → `18b525cb`, 201 commits.
- **Result:** 62 hunks INERT, 0 LIVE.
  - 26 of the INERT rows are output-identical refactors. `kron_hours` was tested against `sp.kron` on 300 random
    blocks with 0 mismatches; `_soco_gas_st_campaign_floor` was checked by hand (same rows, same order).
  - The SolveEpoch rename `2026-10-03a` → `03c` is key-only.
- **`18b525cb` → pin:** only the two LIVE-by-design changes, the stocks data and the gate lift. They are the arm.
- **Guards, checked in every shard as hard stops:**
  - G-1: `resolved_inputs.hydro_plant_modes` reads 45 classified / 28 shapeable. It is now built by
    `--solve-profile SOCO`; at the keeper's SHA it was curated by hand.
  - G-2: `uv sync` installs `python-calamine` (eGRID read). A missing package fails loudly and cannot shift the LP.

## Kills (structural only; any one fired ⇒ no promotion recommendation, reported at full magnitude)

1. **Unserved energy.** The keeper has 0 MWh every year; any year with unserved energy above 0 fires this kill.
2. **C6 governance FAIL** on the composed bundle.
3. **C8 legitimacy FAIL** on the composed bundle (`legitimacy_diagnostics.json`, rule 20 forced budget included).
4. **Recipe diff.** It must equal the keeper recipe plus exactly the four flags above, field by field, and nothing
   else. The composer's recipe check enforces this.
5. **C4 coal NRMSE 2020 > 0.30.** The keeper reads 0.285.

## Not kills (reported at whatever the solve gives; rule 1, no tuning)

- **CC_REGULAR 2019.** The zero-LP upper bound is +2.39 to +2.91 pp: PASS with a 0.09 pp margin at f = 0.5. A miss is
  a finding. It is never a reason to move f, the floor, the yard history or any band.
- **COAL_BIT 2019.** Expected about −3.0 pp (FAIL; it is the ledgered row).
- **Every other criterion-year:** C1, C2, C3a/b/c, C4, compared against the keeper.
- **Shortfall MMBtu per yard-month:** how much of the soft floor was paid rather than burned.

## Recommendation rule (fixed now)

- **If no kill fires:** recommend promoting on structure (rule 1), whatever CC 2019 lands at. On promotion, the
  `coal_monthly_pile_measured_receipts` SOCO cell moves U → O, then to K if promoted, with this evidence.
- **If any kill fires:** RESULT only. The cell stays U, plus a card.

## Shards

- Environment `env_016R8xUY4maDbppZ6TEns5V8`, at most 6 alive at once.
- Prompt from `scripts/shard_prompt.py`, plus:
  - step 0: fetch and check out the pin;
  - `eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"`;
  - `uv sync`;
  - the G-1 and G-2 hard stops.
- Run once; stop on first failure. Budget 20 min per leg (closeout-SOCO-2 legs: LP about 80 s, about 13.4 GiB).
- **Compose:** `scripts/probes/_w0_compose_span.py`, then score, then RESULT.
