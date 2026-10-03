# RESULT closeout-SOCO-3 — the take-or-pay coal pile on SOCO, 2019–2025 (owner ruling R-49)

Lane closeout-SOCO-3, 2026-10-03. Everything below was scored against the rules fixed in
`PRECOMMIT-solve-closeout-soco-3-2026-10-03.md`, which was pushed at `f613f353` before any shard launched.

**Run.** `2026-10-03-closeout-soco-3-coalpile`, bundle `results/calibration/closeout_soco_3_span`, years 2019–2025.
It is registered as a probe (rule 15) and is **not promoted**. The registration (sidecar, payload) and the slim bundle are held on
`claude/closeout-soco-3-reg` @ `22230331` and land on main only with the promotion: audit invariant E13 (rule 35) refuses an
unpromoted SOCO run on main.

**Recipe.** The keeper `2026-10-03-closeout-soco-2-nuclear` (`closeout_soco_2_span`), replayed with exactly four
flags set:

- `coal_fuel_inventory_plant_grain`
- `coal_fuel_inventory_take_floor`
- `coal_fuel_inventory_monthly_pile`
- `coal_monthly_pile_measured_receipts`

**Pin.** `0629d7955843948313beaa5c5f1d7a48e52ef4ef` on main. It carries the 2015–17 coal-stocks intake (#7134) and the
SOCO gate lift (#7137).

**G-DRIFT.** Between the keeper legs (`826333c4`) and the pin, 0 hunks are LIVE and 62 are INERT
(`GDRIFT-closeout-soco-3-keeper-to-pin-2026-10-03.md`).

## 1. What was solved

Seven year-isolated shards (rule 36), all at the pin, all in env `env_016R8xUY4maDbppZ6TEns5V8`.

**Legs.** Each leg pushed 18 files including `dispatch/<Y>_P1.parquet`. Before archiving, each was fetched, the bytes
were held locally, and the leg was verified (rule 33).

| Year | Shard branch @ commit (transport) | Coal yards floored | LP P1 |
|---|---|---|---|
| 2019 | `claude/closeout-soco-3-2019` @ `715b4ad83eb8a04f4882ff49919818f7a4d79c4c` | 8 of 11 (37.6 TWh-eq) | 84.6 s |
| 2020 | `claude/closeout-soco-3-2020` @ `a2a0ff68e8bf8f24ab9b2a237e1d51ee8d040963` | — | not recorded here |
| 2021 | `claude/closeout-soco-3-2021` @ `046f1a9cb395d4f19c5064044fc979d5bb65c714` | — | not recorded here |
| 2022 | `claude/closeout-soco-3-2022` @ `580829decc569a87361772fc40fe52605d515680` | — | not recorded here |
| 2023 | `claude/closeout-soco-3-2023` @ `50ea637566df2d18c7b7394c3a980a472a37d09a` | — | 210 s whole run |
| 2024 | `claude/closeout-soco-3-2024` @ `a4fba6a24b00d9a7620142d9a4bd6f0866e12b87` | — | not recorded here |
| 2025 | `claude/closeout-soco-3-2025` @ `ac18a3063a180258bb95b5fc4cad6de9f45de398` | 5 of 6 (29.4 TWh-eq) | 106.2 s |

**The arm was live.** The shards' own log lines show:

- `coal take floor (SOCO Y): soft, shortfall priced per yard …`
- `coal measured receipts (SOCO 2019): 9 yard rows measured, 2 ratable; contract 548.67 TBtu`
- the cumulative `coal monthly pile` month-end floors.

**Guards.**

- G-1 held in every leg: `hydro_plant_modes` reads 45 classified / 28 shapeable plants.
- G-2 held: `uv sync` completed, so the calamine reader was installed.
- Memory peaked at about 3.2–3.3 GiB.

**Compose.** `scripts/probes/_closeout_soco3_compose.py` is the W0 composer plus the four arm fields as required
`True`. Its recipe check passes: every leg equals the keeper plus W0 plus exactly the arm. All legs share one
solve-surface fingerprint, `fc42826310524d24`, and one SHA. `legitimacy_diagnostics.json` was regenerated over the
composite.

## 2. Kills (structural only, fixed ex ante)

| # | Kill | Reading | Verdict |
|---|---|---|---|
| 1 | Unserved energy > 0 in any year | 0 MWh slack and 0 dump in every year 2019–2025 | clear |
| 2 | C6 governance FAIL | UNATTESTED: no attestation in the bundle yet, because `promote_keeper.py` writes it. This is a registration artifact, not a model finding; the keeper reads PASS | clear (pending attestation) |
| 3 | C8 legitimacy FAIL | `forced_share` PASS in every year. ST_GAS sits above the 30 % cap but is GROUNDED (D-4 clean; profile r ≥ 0.96), exactly as the keeper is. Coal classes carry 0 % forced | clear |
| 4 | Recipe diff beyond the arm | the composer's field-by-field check passes | clear |
| 5 | C4 coal 2020 NRMSE > 0.30 | **0.224** (keeper 0.271) | clear |

**No kill fires.** Under the PRECOMMIT recommendation rule, the lane therefore **recommends promotion on structure**
(rule 1).

## 3. Reported at what the solve gave (rule 1, nothing tuned)

### C1 CC_REGULAR 2019, the row this lane was chartered for

**+3.97 TWh, share +3.2 pp: still FAIL** (keeper +4.43 TWh, +3.4 pp).

The zero-LP upper bound read +2.39 to +2.91 pp, with a 0.09 pp margin at f = 0.5. The LP delivers less than that.
Its added coal does not mainly come out of CC. Class deltas against the keeper, in TWh:

| Year | COAL_BIT | COAL_PRB | CT_PEAKER | ST_GAS | CC_REGULAR |
|---|---|---|---|---|---|
| 2019 | +3.45 | −1.40 | −1.25 | −0.34 | **−0.47** |
| 2020 | +2.72 | +0.14 | −1.47 | −0.33 | −1.07 |
| 2021 | +1.53 | −0.23 | −0.36 | −0.06 | −0.89 |
| 2022 | −0.74 | −3.39 | +0.29 | +0.08 | +3.79 |
| 2023 | +1.91 | +0.41 | −1.65 | −0.41 | −0.26 |
| 2024 | +0.42 | +1.62 | −0.75 | −0.06 | −1.21 |

The soft floor's shortfall is priced at the delivered fuel cost, so the floor is met. Every plant-year's December
burn reaches its floor; there is **no shortfall in any year** (`solve_floor_vs_burn.csv`). But the perfect-foresight
LP places the obligated coal in the hours where it displaces the dearest unit: CT and PRB coal. It does not place it
in the night hours where the real Southern backed CC down.

So the floor fixes **how much coal** Barry and Crist burn, but not **when**. The night-time CC conduct described in
closeout-SOCO-2 §b survives the arm. This is NWPP-NEXT-9's displacement mode, appearing on C1 rather than C4.

### Every other row, against the keeper (`solve_score.csv`)

**C1 coal**

- COAL_BIT 2019: −11.27 TWh / −4.3 pp → **−7.82 TWh / −2.8 pp**.
  - The share leg now passes.
  - The volume leg misses its ±7.64 TWh band by 0.18 TWh, so the row stays the ledgered COAL_BIT 2019 caveat.
- COAL_BIT moves closer to actual in every scored year: 2020 −6.26 → −3.54; 2021 −5.12 → −3.59; 2023 −5.07 → −3.16;
  2024 −3.94 → −3.51 TWh.
- At plant level:
  - Barry 2019: 69 → 2,069 GWh (actual 4,175).
  - Crist 2019: 690 → 2,460 GWh (actual 2,565).
  - Barry 2020: 120 → 2,583 GWh (actual 2,626).
- COAL_PRB 2022: +6.04 → +2.64 TWh, because the pile ceiling binds.

**C1 CC_REGULAR, other years**

- 2020: +1.03 → −0.04 TWh.
- 2021: +4.24 → +3.35 TWh; share 2.7 → 2.4 pp.
- 2023: +5.30 → +5.04 TWh.
- 2024: +3.92 → +2.71 TWh.

**C1 status changes:** no row goes PASS → FAIL.

**C3a (mean price vs Southern's λ)**

- 2019: +10.9 % CAVEAT → **+8.7 % PASS**.
- 2020: +11.0 % CAVEAT → **+8.4 % PASS**.
- These two ledgered caveats clear.
- 2021: −5.8 → −6.7 %. 2023: +1.0 → −0.4 %. 2024: −4.8 → −6.0 %. All still PASS.
- 2022: −14.8 → −13.7 %. This is the ledgered row; it prints FAIL only because the run is unattested.

**C3b (NRMSE)**

- 2019: 0.137 → 0.112.
- 2020: 0.140 → 0.113.
- 2023: 0.087 → 0.091.
- 2024: 0.175 → 0.184.
- 2022: 0.281 → 0.282 (the ledgered row).

**C4 coal NRMSE**

- It improves in 6 of 7 years: 2019 0.235 → 0.203; 2020 0.271 → 0.224; 2023 0.261 → 0.197; 2024 0.266 → 0.218.
- Coal r falls in 2022, 0.788 → 0.753, and still passes.
- Every C4 row passes.

**C2 sysvol:** unchanged, PASS in every year.

**D-1 diurnal shape (composite, reported only):** the failing rows drop from 3 (keeper: 2022 COAL_BIT, 2022 COAL_PRB,
2023 COAL_BIT) to 1 (2022 COAL_PRB). D-1 still reads FAIL overall, as it does for the keeper.

## 4. Determination on promotion (expected)

**SOCO stays NOT-YET on C1 CC_REGULAR 2019 (+3.2 pp).**

The ledger carried forward changes as follows:

- **Drop with recorded reasons:** the C3a 2019 and C3a 2020 caveats (now PASS).
- **Stay:** COAL_BIT 2019 (narrower), C3a 2022, C3b 2022.

The promotion command handles the carry-forward (rule 35).

## 5. Matrix

The SOCO cell `coal_monthly_pile_measured_receipts` moves U → **O** (solved, registered, owner ruling pending), with
this evidence.

- `coal_fuel_inventory_take_floor` stays G. It is armed here only in the R-49 measured form, which the gate lift
  enforces in code.
- `coal_takeorpay_committed` stays G.

## 6. Retrievability and promotion cost

- **Composed bundle.** Slim (53 files, 18 MB, `unit_marginal_<Y>` for every year), with the registration, on
  `claude/closeout-soco-3-reg` @ `22230331`. It reaches main in the promoting PR (E13 forbids an unpromoted run on main).
- **Per-year legs.** Their `dispatch/` and `unit_hourly` files live only on the seven shard branches above. Those
  branches are transport, cut when the lane PR merges; they are listed here as provenance.
- **Promotion cost.** One `promote_keeper.py --iso SOCO` run, zero LP. It writes the attestation, carries the ledger
  forward and prunes `closeout_soco_2_span`. No re-solve is needed.
- **Rule 31.** Nothing has been deleted. The bundles will not survive this container, and the composed bundle is pushed on
  `claude/closeout-soco-3-reg`.
