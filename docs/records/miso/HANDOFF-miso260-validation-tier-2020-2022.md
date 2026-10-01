# HANDOFF — miso-260: close the 2020–2022 validation-tier misses

Successor to miso-259, which promoted MISO's keeper to
`2026-09-16-miso-259-coal-fuel` (the coal fuel-inventory ceiling). The train
tier 2023–2025 reads **CALIBRATED** and is not this session's object. **Your
object is the three remaining validation-tier criteria.**

## THE MISSES, SCORED LIVE ON THE NEW KEEPER — do not re-derive

`calibration_verdict.py results/calibration/miso259_coalinv_span --years 2020 2021 2022`
→ **NOT-YET**. C2, C4, C6, C8 all PASS. What fails:

| criterion | year | miss |
|---|---|---|
| **C1** fuel-mix | 2021 | CC_REGULAR **−9.46 TWh** (share −0.7 pp) |
| **C1** | 2021 | COAL_BIT **−8.36 TWh** (share −0.7 pp) |
| **C1** | 2022 | CC_REGULAR **−9.47 TWh** (share −1.2 pp) |
| **C3a** mean LMP | 2020 | **+22.9 %** |
| **C3a** | 2022 | **−14.6 %** |
| **C3b** price shape | 2020 | NRMSE **0.246** |
| **C3b** | 2021 | NRMSE **0.285** |
| C3c tail | 2022 | CAVEAT, ledgered, non-downgrading — **not yours** |

**The coal-inventory promotion already moved most of this**, so do not re-attack
what it fixed. Against the superseded `2026-09-12-miso-255-sil-measured` record:

| | old keeper | **new keeper** |
|---|---|---|
| C1 2022 CC_REGULAR | −28.52 | **−9.47** |
| C1 2022 COAL_PRB | +32.04 | **PASS** |
| C1 2022 COAL_BIT | +10.39 | **PASS** |
| C1 2021 CC_REGULAR | −15.94 | **−9.46** |
| C3a 2022 | −23.4 % | **−14.6 %** |
| C3b | 2020, 2021, 2022 fail | **2020, 2021** (2022 now passes) |
| C4 2022 gas r | 0.838 FAIL | **PASS** |

## THE STANDING DIAGNOSIS — read before proposing anything

`docs/FINDING-miso256-2022-passthrough-inversion-2026-09-13.md` §0 measured the
object and it is **still the live one**: MISO's gas passthrough slope is
**4.63 $/MWh per $/MMBtu against the market's 8.41 — 55 %** — carried by a fixed
intercept of 21.17 against 8.95, with `corr(gas price, model error %) = −0.841`.
The model under-responds to gas, so it **over**-prices cheap-gas years and
**under**-prices dear ones. That single slope explains the C3a pair directly:
2020 is the cheapest gas year in the span ($2.27/MMBtu) and reads **+22.9 %**;
2022 is the dearest ($6.45) and reads **−14.6 %**. They are one defect, not two,
and **a lever that fixes one by moving the intercept will break the other.**

The coal-inventory mechanism attacked the same slope from the coal side (a flat,
gas-insensitive coal cost sitting on the margin flattens the slope) and closed
about a third of the 2022 half. The residual is the **gas** side.

## THE OPEN LEVERS — in the order I would take them

### 1. THE MONTHLY NO-CARRY GRAIN (highest value, already identified)
The promoted mechanism uses **twelve independent monthly rows with no stock
carry**, and measured on the span that limitation does real damage in exactly
the years you are targeting:

| yr | Σ\|class err\| move under the arm |
|---|---:|
| 2020 | +0.13 |
| **2021** | **−1.40** |
| 2022 | −52.14 |
| 2023 | +0.23 |
| 2024 | +0.19 |
| **2025** | **+8.34** |

2021 and 2025 **bind where the ANNUAL fuel constraint says they should not**:
annual headroom is +65.6 and +50.6 TWh respectively, yet peak months still
breach a flat 1/12 cap. The successor is a **stock-carry (SOC-style) row
family** — `SOC[m] = SOC[m-1] + receipts[m] − burn[m]`, cyclic or with a
declared opening — so an under-burning spring funds a hot July.

**This is the single lever most likely to help 2021's C1 and cost nothing in
2022**, because 2022's constraint binds on the annual budget too. Build it as a
NEW `ScenarioConfig` field beside `coal_fuel_inventory`, not as a mutation of
it, so the promoted keeper stays reproducible.

### 2. THE 2020–2022 SEAM-PRICE PROXY (a rule 14 `[R-ACCURATE]` miss, open)
All three MISO seam `hr_by_year` tables cover **only 2023–2025**, so every
pre-2023 year falls through `neighbor_heat_rate` resolution order 1 onto the
**forward gas-elastic** path fitted on the training window. Sized against PJM's
realized RT LMP: **2020 +$8.08 (+40 %), 2021 +$24.25 (+65 %), 2022 +$5.76
(+8 %)**. This is a genuine defect and it sits squarely on your two C3b years.
**It was REFUTED as the 2022 *coal* object on ordering** (2021 carries the
largest proxy error and had no coal error) — that refutation does not touch its
standing as a **price-shape** object, which is what you are working.

### 3. C1 2021/2022 CC_REGULAR (−9.46 / −9.47 TWh, remarkably stable)
Both years now miss by almost exactly the same amount, which argues for a
**level** defect in the CC_REGULAR offer or availability basis rather than a
year-specific event. Check whether the miss is present in 2023–2025 at a smaller
magnitude before treating it as a validation-tier-only object.

## HARD CONSTRAINTS

* **DO NOT touch the train tier.** 2023–2025 reads CALIBRATED with zero fails.
  G-NOFLIP on any arm: no train-tier criterion may go PASS → FAIL. A validation
  win bought with a train-tier loss is a loss (rule 30(c) — the ISO headline IS
  the train tier).
* **The C3a pair is ONE defect.** Any lever must be scored on **2020 and 2022
  together**. Moving the intercept trades one for the other and is not progress.
* **No fitted adder, offset or haircut** (rule 1 `[R-STRUCT]`). The one
  authorized price-tuning channel is the registered `offer_curve_by_group` band
  multipliers, ONE config across every scored year, declared ex ante in the
  PRECOMMIT, **never swept against the gates**.
* **C3c 2022 is ledgered and non-downgrading.** Do not spend a session on it;
  `docs/multi-iso/miso-scarcity-tail-diagnosis.md` records it as a frontier
  needing a new admissible measured identification.

## MECHANICS

`DATA PROFILE: miso`. MODEL: **Opus or Fable, never Sonnet** (rule 27).
BASE: `origin/main`. Do not open a PR unless asked.

* **Keeper**: `2026-09-16-miso-259-coal-fuel`, bundle
  `results/calibration/miso259_coalinv_span`, span 2020–2025, committed SLIM.
* **Control**: the keeper's committed bundle (rule 29(b) form 4). **Do the
  G-DRIFT audit and expect it to be blocked the same way I was** — the previous
  keeper's recorded `git_sha` was unreachable because its shard branch had been
  deleted. If it is, say so and spend one control rather than asserting form 4.
  The cheap mechanical check that DID work: compare
  `solve_surface.surface_stamp("MISO", ScenarioConfig())["fingerprint"]` at HEAD
  against the bundle's own `run_config.json` → `solve_surface.fingerprint`
  (`9f0845000dc8af6e` at promotion).
* **Sharding (rule 32/34)**: ONE year per shard, each pushing its **WHOLE**
  bundle — ~17 files including `dispatch/<y>_P1.parquet`, `system.parquet`,
  `btm.parquet`, `floors/`. Use a `.gitignore` NEGATION plus a **plain
  `git add`**; `git add -f` is refused by the auto-mode classifier. Five years in
  parallel took ~20 min. **Do not run a sequential span** — I did, and discarded
  ~45 minutes for nothing.
* **Composition**: `scripts/probes/_miso259_compose_span.py` is the worked
  pattern. Per-year files copy; the bundle-root `system`/`btm`/`flows`/`storage`
  parquets **concatenate**. Two traps I hit, both costly:
  1. **`legitimacy_diagnostics.json` must be MERGED across years**, not copied
     from one. Its `D1/D2/D4` `rows`/`summary`/`failures` are year-stamped lists
     that concatenate. Copy one year's and **C8 silently goes SKIPPED**, which
     downgrades the determination on an *unscored protective criterion* —
     looking exactly like a model regression when it is a composition bug.
  2. The **shared input store** (`results/calibration/_shared/<ISO>/`) lives
     OUTSIDE the bundle dir, so shards do not push it and registration fails on
     `bundle_input_path(..., "eia923") -> None`. Fix with
     `run_calibration_full.py --rebuild-benchmark <bundle>` — **no re-solve**.
* **Before committing any registration**: diff the bench parts against HEAD and
  confirm **zero movement**. The actual side must not move (the miso-257 lesson,
  where a broken bench part moved C1 by 19 TWh and read as a model result). Mine
  was 0.000 TWh in all six years.

## GATES BEFORE PUSH

`check_registry_payload_parity` (**2 pre-existing REDs on main**,
`caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — never `rm` either; any
gitignored local bundle dir of your own will also show and is invisible to CI) ·
`audit_keepers --iso MISO` (**E3 `meta.json`-vs-`calibration_flags` years
warning is pre-existing**) · `build_status --iso MISO --check` ·
`check_mechanism_matrix --base origin/main` · `check_cache_key_registration
--base origin/main` · `check_gate_a_provenance` (**NYISO and SPP fail, not
yours**) · `check_bench_freshness --iso MISO` · `pytest tests/scoring` — report
only NEW against the **18-failure** baseline on `origin/main`.

Ruff: `uv run ruff check --fix --force-exclude -- <files>` then
`uv run ruff format --force-exclude -- <files>` (`scripts/probes/` is excluded).

## DO-NOT-REDO

* **The coal-inventory mechanism is BUILT and PROMOTED.** `coal_fuel_inventory`,
  default off, MISO-gated, backcast-only. Do not rebuild it; extend it.
* **The coal stock/receipts data is LANDED**: `coal-stocks` and `coal-receipts`,
  free and keyless from EIA-923's bulk workbook. The legacy
  `_processed-legacy/eia923_monthly_fuel_costs.parquet` is **incomplete for coal
  tonnage** (55 of 67 MISO plants, MISO 2020 99.10 Mt against the true 120.42)
  and must not be used for it.
* **The 2022 coal block is CLOSED** as the passthrough object — coal error
  +42.61 → +7.98 TWh. The residual is the **gas** side of the slope.
* **C1-2023 CC_CHP / COAL_PRB**: closed as a bench defect (miso-257).
* **The CHP BTM boundary**: refuted at phase 0 (miso-192).
* **The measured-SIL import envelope**: `R` (miso-255).
* Reserve-scarcity levers: retired in PJM's lanes; no MISO opening without a
  supply-margin census first.

## RECORDS

`docs/RESULT-miso259-coal-inventory-screen-2026-09-16.md` ·
`docs/PRECOMMIT-miso259-coal-fuel-inventory-2026-09-16.md` ·
`docs/FINDING-miso258-coal-stock-falsification-2026-09-14.md` ·
`docs/FINDING-miso256-2022-passthrough-inversion-2026-09-13.md` ·
`docs/codebase-site/data/mechanism-matrix/MISO.js`
