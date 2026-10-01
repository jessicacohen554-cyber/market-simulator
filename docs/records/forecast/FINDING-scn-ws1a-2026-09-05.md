# FINDING — SCN-WS1a: federal carbon-price semantics (G-C1, gated on owner card D-1) + the two seam defects (G-C2, G-C3) + the pre-declared CAP-STATE-TIGHT case

**Lane:** SCN-WS1a (desk ledger r#1, `docs/handoffs/scenario-desk-ledger-2026-09.md` §1/§5),
plan §3 WS-1 items 1–3 + §7 "WS-1a". Model Fable. Branch `claude/scn-ws1a-carbon-d1-eupbi5`
(the harness assigned this stem in place of the ledger's nominal `claude/scn-ws1a-p4qd`; the
file paths are what matter). Branched off `origin/main` at `5cc1e7ce` (= desk pin `d01ab8b0`
+ the desk's own r#1 amendment PR #4853); every plan §2 anchor re-verified with `git log` at
the branch point (§0.2).

**DATA PROFILE: caiso** (this container is a full clone; `data/clean` was absent and is
regenerated in full for the one CAISO T0 pair — §3).

**Card gate, read first (charter):** desk ledger §2 at my start reads **D-1 PRESENTED r#1, no
recorded ruling**. The gate therefore reads OPEN, so this lane delivers **items 2–4, the Phase-0
trajectory table, and the D-1 evidence memo (§6), and STOPS**. `cap_and_trade.py`'s forecast
branch (`:289-291`) is **NOT changed** on this lane's judgment; item 1 (floor semantics, the
D34-guard extension, the `test_cap_and_trade.py:135` flip, the NEISO-tight strict-increase
test, the cache-epoch entry) is **NOT executed** and is written up in §6 as the implementation
the FLOOR ruling would authorize.

---

## 0. Phase 0 — the PRECOMMIT (zero-solve; pushed before any code and before the T0)

### 0.1 The resolved carbon trajectory per ISO per horizon year per `policy_bundle`, at HEAD

Instrument: `docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.py` (its full
25-year output is the `.json` beside it; the `.txt` is the console table). It evaluates the
LIVE resolver — `resolve_policy_bundle` → `apply_iso_scenario_defaults` →
`policy.carbon.resolve_carbon_price(config, year)` — so every number below is exactly what
every model consumer (dispatch `mc`, the capacity-evolution driver, the CARB border adder)
receives. Values in $/tCO2.

| ISO | bundle | resolved path | state pricing | 2026 | 2027 | 2028 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ERCOT | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| ERCOT | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CAISO | current | zero | True | 30.02 | 32.13 | 34.37 | 39.36 | 55.20 | 77.42 | 108.58 | 152.29 |
| CAISO | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| CAISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| PJM | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| PJM | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| PJM | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MISO | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MISO | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| MISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| NYISO | current | zero | True | 23.64 | 25.29 | 27.06 | 30.98 | 43.45 | 60.95 | 85.48 | 119.89 |
| NYISO | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| NYISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| NEISO | current | zero | True | 26.05 | 27.88 | 29.83 | 34.15 | 47.90 | 67.18 | 94.23 | 132.16 |
| NEISO | tight | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| NEISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

(`current` on a program ISO = the projected program trajectory: the last measured auction
average — CAISO CARB 2025 $28.06, NYISO RGGI 2025 $22.09 short-ton-as-published, NEISO RGGI
2025 $24.35 metric-converted — escalated at the program's 7 %/yr containment-band rate,
`cap_and_trade.py::projected_price`. `tight` = RFF mid, linear between the knots 0/15/35/50 at
2026/2030/2040/2050. `rollback` = zero path + `state_carbon_pricing=False`.)

**G-C1 is PROVEN at HEAD: `policy_bundle="tight"` is a carbon-price CUT on all three program
ISOs in every one of the 25 horizon years.** `tight − current`, $/t, over 2026–2050:

| ISO | smallest cut | largest cut | years with a cut |
|---|---|---|---|
| CAISO | −24.36 (2030) | −102.29 (2050) | 25 / 25 |
| NYISO | −15.98 (2030) | −69.89 (2050) | 25 / 25 |
| NEISO | −19.15 (2030) | −82.16 (2050) | 25 / 25 |

The mechanism is `cap_and_trade.py:289-291`: an explicit non-`"zero"` `carbon_price_path`
sets `price = None`, the resolver falls through to the RFF path alone, and the projected
program trajectory is suppressed. The D34 guard (`carbon.py::carbon_price_below_base_warning`)
does not fire because it reads `carbon_price`, not the path. `rollback` is a cut too, by
declared design (PB-1 §1.2: "state programs frozen off"), and is not a defect.

**The number that matters for D-1 beyond "cut".** Under the recommended FLOOR semantics
(`effective = max(RFF path, program trajectory)`), `tight` would be an **exact no-op on all
three program ISOs in every year**: the RFF mid path never exceeds the escalated program
trajectory (largest gap program − mid: CAISO $24.36, NYISO $15.98, NEISO $19.15, all in 2030).
The same holds for RFF low. RFF high crosses the program trajectory only mid-horizon on the two
RGGI ISOs — NYISO 2031–2047 (max +$9.05), NEISO 2033–2042 (max +$3.32) — and never on CAISO
(max gap −$5.06). So a floor makes the `tight` bundle's carbon leg bite ONLY on ERCOT / PJM /
MISO, and a "federal carbon price" scenario on a program ISO written as an RFF path becomes an
increase only with the `high` path and only in those windows. §6 carries this as the central
evidence for the owner. (Instrument: `docs/handoffs/scn-ws1a/gc2-import-offers-2026-09-05.py`,
second block.)

### 0.2 Anchor re-verification at the branch point (`5cc1e7ce`)

| anchor (plan §2.1 / §8, taken at `4d4dc6ce`) | last commit touching the file | verified at HEAD |
|---|---|---|
| `policy/cap_and_trade.py:289-291` (`price = None` on an explicit path) | `54f50b0c` 2026-09-04 | line 289 `if getattr(config, "carbon_price_path", "zero") not in ("zero", None): price = None` — as cited |
| `model/interchange/spec.py:1931` (`wecc_border_carbon_adder(getattr(config, "carbon_price", 0.0))`) | `3eaf7918` 2026-09-05 | line 1931 — as cited |
| `runner.py:2561-2575` (`carbon_price = resolve_carbon_price(config, year)` → `mc_cost = assemble_mc(...)`) | `9f1c8797` 2026-09-05 | lines 2561–2575 — as cited; `mc_cost` becomes the dispatch `mc_base` at `:2628` |
| `scripts/run_calibration.py:4022-4052` (the membership-weighted column) | `826c6bee` 2026-09-05 | lines 4010–4053 — as cited (the block begins at `:4010` with the comment; the gate + loop are `:4026-4052`) |
| `config/scenarios.py:15572` (the D34 guard in `__post_init__`) | `13f711bc` 2026-09-05 | lines 15572–15577 — as cited |
| WS-2a's `runner.py` regions `:1195-1229`, `:2851-2864` | — | `_rps_region_grain_active` at 1195; the RPS/clean row block at 2849–2864 — disjoint from `:2561-2575` |

### 0.3 G-C2 zero-LP census — what the seam resolves to, and what the offer path prices

Instrument: `docs/handoffs/scn-ws1a/gc2-seam-census-2026-09-05.py` (output `.txt` beside it).
CAISO, `mode="forecast"`, 2026, ISO defaults applied, base vs `carbon_price_delta=25`:

| arm | `resolve_carbon_price(config, 2026)` | expected border adder 0.428 × price | `spec.corridors[*].carbon_adder` (spec.py:1931, per-hub posture) | runner-path border (`runner.py:1321`, `wecc_border_carbon_adder(resolve_carbon_price(...))`) |
|---|---|---|---|---|
| base | 30.0242 $/t | 12.8504 $/MWh | **0.0** on WECC_PNW and WECC_DSW | 12.8504 |
| delta=25 | 55.0242 $/t | 23.5504 $/MWh | **0.0** on WECC_PNW and WECC_DSW | 23.5504 |

**Reproduced:** the seam's value is $0 under the program-resolved posture where its own
arithmetic says $12.85, exactly as G-C2 states.

**A finding the plan does not carry, established at zero LP and load-bearing for the T0
design:** `Corridor.carbon_adder` has **no reader anywhere in the tree**. `grep -rn
"\.carbon_adder\|\.corridors\b"` over `src/`, `scripts/`, `tests/` finds only the field's
definition (`spec.py:1738`), its docstring (`:1728`) and its assignment (`:1943`); the
`InterchangeSpec.corridors` list is consumed by nobody (`runner.py:1394` reads
`use_corridors`, the boolean, not the list). The import tranches that actually reach the LP
are built by `build_interchange_fleet(spec, border_carbon_per_mwh)` with the border computed at
`runner.py:1321` from the resolver, and re-priced per year by `apply_interchange_injections(...,
carbon_price=resolve_carbon_price(config, year))` (`runner.py:2740`). So the offer path is
already resolver-correct; the seam is a dead informational field that reports the wrong number.
The plan's §2.1 sentence "under the default program-resolved posture that seam's adder is $0"
is true of the FIELD and false of the OFFER. The consequence for the T0 is stated in §0.4.

The offers themselves, built exactly as the runner builds them (instrument
`gc2-import-offers-2026-09-05.py`, first block; `vom` $/MWh, the static-ladder placeholder the
per-year injector re-prices):

| import unit | vom @ base (carbon 30.02) | vom @ delta=25 (55.02) | Δvom | Δvom / 10.70 |
|---|---|---|---|---|
| WECC_import_PNW_hydro_base | 28.00 | 28.00 | 0 | 0 (EF 0) |
| WECC_import_PNW_midC | 36.00 | 36.00 | 0 | 0 (EF 0) |
| WECC_import_DSW_solar_PV | 48.00 | 48.00 | 0 | 0 (EF 0) |
| WECC_import_DSW_CCGT | 79.109 | 88.359 | **+9.25** | 0.864 (EF 0.37 / 0.428) |
| WECC_import_DSW_CT | 126.513 | 140.263 | **+13.75** | 1.285 (EF 0.55 / 0.428) |
| WECC_import_WECC_scarcity (the unspecified block) | 192.850 | 203.550 | **+10.70** | **1.000 = 0.428 × 25** |
| export sinks (solar / curtail) | 8.00 / 0.00 | unchanged | 0 | exports carry no CA compliance cost |

### 0.4 The PRECOMMIT for the CAISO T0 (rule 29 `[R-SCREEN]`; the gate is structural and STOP-only)

- **Screen year:** 2026 — the single year of the T0, named before the solve. The mechanism's
  measured footprint (the import-offer delta above) is year-invariant under a flat Δ, so the
  charter's year is the screen year; nothing else solves.
- **Arms:** `base` and `carbon_plus25` (`carbon_price_delta=25.0`), each ONE solve-year,
  built by the committed FC-6 construction `scripts/run_driver_battery.py --iso CAISO
  --start-year 2026 --end-year 2026 --paired-arm <arm>` (= `run_full_horizon.reference_config
  (…, cmc=False, golden_posture=True)` + exactly one override, `solve_and_summarize`). The
  incumbent-control rule (rule 29 clause b) has no CAISO forecast control to difference
  against at 2026 on the D60 key (`results/ff-t1f-d46/caiso` is a 2026–2030 T1-F on a pre-D60
  key), so the base arm IS the control here — one T0 pair, two solve-years, as chartered.
- **Expected sign and magnitude, stated before the solve:** the resolver's Δ is exactly
  +25.00 $/t (premise row `P1.premise` of `check_forecast_invariants.py --paired --pair-kind
  carbon` PASSES); the CARB border adder moves 12.8504 → 23.5504 $/MWh, i.e. **+10.70 = 0.428 ×
  25 on the WECC unspecified block**, +9.25 on DSW_CCGT, +13.75 on DSW_CT, 0 on every EF-0
  tranche and both export sinks; every in-state fossil row's `mc` rises by `emission_rate ×
  25`. Dispatch response: carbon-bearing WECC import energy does not rise, CAISO CO2 does not
  rise, the load-weighted price does not fall.
- **Footprint claimed:** the three carbon-bearing WECC import tranches + in-state fossil rows.
  Zero-carbon rows (hydro/solar/midC imports, VRE, nuclear, storage) carry an unchanged offer.
- **What the T0 can and cannot show, said now:** because the spec.py field is dead (§0.3), the
  T0 pair exercises the OFFER path (`runner.py:1321` + `:2740`), which G-C2 said was $0 and is
  not. It cannot observe `spec.py:1931` at all. The seam fix itself is verified at the unit
  level (Corridor.carbon_adder = 0.428 × resolved price after the change), and a second,
  post-fix T0 pair is **not** spent: the fix writes a field that enters no LP array, so the
  post-fix solve is byte-identical by construction, proven at zero LP by diffing every array
  `build_interchange_fleet` + `get_interchange_spec` emit before and after the change
  (§3). Spending an LP to re-prove that would be exactly the "files changed, therefore solve"
  heuristic rule 29 forbids.
- **Gate (STOP only):** the arm is KILLED if the premise row fails, if a zero-EF tranche's
  offer moves, or if the import dispatch responds with the wrong sign to a +10.70 $/MWh
  unspecified-block offer move. Nothing in the gate reads a residual; the T0 promotes nothing.

### 0.5 Byte-identity posture of everything this lane lands

No `ScenarioConfig` field is added, moved or re-defaulted, so **no cache key moves anywhere**
(the pinned default `e5ecd4105ada3e58` and every keeper / forecast key stand). The two code
changes are behaviour-inert for every committed bundle: the spec.py fix writes a dead field
(§0.3), and the G-C3 column reduces to the incumbent scalar for every ISO whose program
membership is uniform or whose resolved adder is $0 — which at HEAD is all six (PJM's forecast
adder is $0, `projected_price` has no PJM anchor). The complete key list is §5.

---

## 1. Item 1 — floor semantics (G-C1): NOT EXECUTED, gated on D-1 (see §6)

`cap_and_trade.py:289-291`, `carbon.py`, the D34 guard, `test_cap_and_trade.py:135`, the
NEISO-tight strict-increase test and the cache-epoch entry are all untouched on this branch.
`git diff origin/main -- src/market_sim/policy/cap_and_trade.py` shows one ADDITION only (the
G-C3 helper `carbon_mc_column`, §2) and no change to `resolve_carbon_program`. §6.4 carries
the implementation the FLOOR ruling would authorize, so the executing lane needs no design work.

## 2. Item 3 — G-C3: the membership-weighted carbon column at `runner.py`'s `assemble_mc` seam — LANDED

**What was wrong.** The forecast orchestrator passed the resolved ISO-wide scalar straight to
`assemble_mc` (`runner.py:2561-2575`, and that `mc_cost` becomes the dispatch `mc_base` at
`:2628`), while the backcast orchestrator (`scripts/run_calibration.py:4010-4053`) replaced the
scalar with the per-generator membership-weighted column `m[g] × p_allowance` whenever the
ISO's program maps membership per zone (PJM's RGGI footprint). Inert today — PJM's forecast
adder is $0 — and wrong the day a forecast carbon price on PJM turns non-zero.

**What landed.** `policy/cap_and_trade.py::carbon_mc_column(config, iso, year, carbon_price,
fleet_arrays, zone_names)` — the backcast block lifted VERBATIM as a function (same gate in
the same order: falsy scalar → scalar; no program or `zone_share is None` → scalar; resolution
adder falsy → scalar; else `per_generator_membership(...) × price_adder`). `runner.py`'s call
site (my region, `:2561-2575` → now `:2564-2598`) calls it and passes the result to
`assemble_mc`; the call site is the ONLY runner edit besides the import line. The scalar path
returns the **identical object** (`is`), so `assemble_mc` receives byte-for-byte the argument
it received before — pinned by `TestCarbonMcColumn` (`tests/unit/policy/test_cap_and_trade.py`):
- identity on the scalar path for ERCOT / CAISO / MISO / NYISO / NEISO, both modes, at a
  forced non-zero price (so the identity is on the value, not on "carbon was zero");
- the zero-price short-circuit touches no fleet;
- PJM forecast resolves $0 today (G-C3 inert at HEAD, asserted);
- PJM's one live path (gated backcast RGGI adder, synthetic rows) builds the
  `PJM_RGGI_ZONE_SHARE × 22.83` column;
- `assemble_mc(scalar)` and `assemble_mc(column-on-scalar-path)` are `tobytes()`-equal on a
  NEISO fleet.

`scripts/run_calibration.py` is NOT touched (not this lane's file): its inline block stays, and
the helper is its verbatim twin. Folding the backcast call onto the helper is a one-line,
byte-identical follow-up for whichever lane next owns that file (rule 19, noted, not done).

**Not decided here.** The column is built from the resolution's `price_adder` (the program
adder alone), exactly as the backcast does, not from the full resolved scalar (which may carry
`carbon_price_delta` or a scalar override). Whether a FEDERAL component stacks membership-free
on top of a partial-footprint state adder is the D-1 question in PJM clothing (§6.3); the
helper's docstring says so and the seam does not pre-empt it.

## 3. Item 2 — G-C2: `spec.py` corridor border adder off the resolver — LANDED; T0 in §3.2

### 3.1 The fix and its zero-LP proofs

`model/interchange/spec.py:1931` → `wecc_border_carbon_adder(resolve_carbon_price(config,
year))`, with `year` = the spec's own year when the caller passes one, else `config.start_year`,
else `START_YEAR` — the runner calls `get_interchange_spec(config, iso)` without a year and
builds the fleet at `start_year`, so the two agree. Lazy import (policy → config → model
layering). Tests `TestBorderSeamResolvesCarbon` (same test file): the corridor adder equals
`0.428 × resolve_carbon_price` under the program-resolved posture (`carbon_price == 0.0`), moves
by exactly `0.428 × 25` under `carbon_price_delta=25`, and equals the border the runner prices
the import fleet with.

**Pre/post identity of everything the LP consumes** (`docs/handoffs/scn-ws1a/` census re-run
against the pre-fix snapshot, four postures: base / delta=25 × single-node / per-hub):

| posture | import `Generator` list pre == post | `Corridor.carbon_adder` pre → post |
|---|---|---|
| base, single-node | identical | (no corridors) |
| base, per-hub | identical | 0.0 → 12.8504 (WECC_PNW, WECC_DSW) |
| delta=25, single-node | identical | (no corridors) |
| delta=25, per-hub | identical | 0.0 → 23.5504 |

So the fix is offer-inert by construction: it corrects a reported number that nothing consumed.
Suites run green after the change: `tests/unit/policy` (61 + 12), `tests/unit/config/
test_interchange_config.py`, `tests/unit/data/test_capacity_deliverability_wiring.py`,
`tests/iso/caiso/test_caiso_per_hub_intertie.py`, `test_caiso_intertie_forward.py`,
`tests/unit/pipeline/test_runner.py` (62 passed).

### 3.2 The CAISO T0 pair (precommit §0.4) — every gate row PASSES; arm not killed

Solved on this branch's code (post-fix tree) after a full `data/clean` regeneration (55
datatypes, green): `run_driver_battery.py --iso CAISO --start-year 2026 --end-year 2026
--paired-arm {base,carbon_plus25}` — the FC-6 construction, `golden_posture=True`, `cmc=False`.
Records: `docs/handoffs/scn-ws1a/t0/` (both `full_horizon_summary.json` + `run_config.json`,
the scoring instrument and its JSON, the launch script, the pair log).

| arm | cache key | wall | peak RSS | resolved carbon 2026 | CO2 Mt | load-weighted price $/MWh | max hourly $/MWh |
|---|---|---|---|---|---|---|---|
| base | `706eec14f63096e8` | 7.1 min | 4.88 GB | 30.0242 | 30.5116 | 55.32 | 70.7 |
| carbon_plus25 | `f129fd3720e3e874` | 7.3 min | 4.55 GB | 55.0242 | 29.6034 | 65.141 | 83.3 |
| **Δ** | | | | **+25.00** | **−0.908 (−3.0 %)** | **+9.82 (+17.8 %)** | +12.6 |

**Precommit gate rows (§0.4), all structural:**
- Premise `P1.premise` PASS — Δ = +25.00 $/t exactly, the resolver both arms see.
- Zero-EF tranches' offers unchanged → their dispatch is byte-identical: PNW_hydro_base 13,375
  GWh and PNW_midC 15,453 GWh in both arms (Δ 0.0).
- Carbon-bearing WECC import energy does not rise: DSW_CCGT, DSW_CT and the unspecified
  `WECC_scarcity` block dispatch **0 GWh in BOTH arms** — they are out of merit at $79 / $127 /
  $193/MWh against a $55 load-weighted price, so the +9.25 / +13.75 / +10.70 $/MWh offer moves
  (§0.3) act on blocks the LP never clears in 2026. The offer-level claim ("the unspecified
  block's offer moves by 0.428 × price") is therefore established on the runner's own fleet
  construction (§0.3, the `vom` table), not on a dispatch change; the dispatch-level gate row
  holds trivially (0 → 0).
- CO2 does not rise (falls 0.91 Mt); price does not fall (+$9.82, ≈ Δcarbon × the marginal
  gas-CC rate 0.37–0.40 t/MWh = $9.3–10.0, i.e. gas-CC is marginal in most hours and the
  carbon adder passes through at the marginal unit's rate).
- `P1` (CO2 monotone vs carbon) PASS: 30.51 → 29.60 Mt.

**Footprint (by-fuel generation, GWh, base → arm):** gas_cc 77,579 → 75,351 (**−2,229**);
import 42,072 → 44,300 (**+2,228**, entirely the zero-carbon DSW_solar_PV tranche: +2,228);
gas_ct 978 → 1,068 (+90); coal 359 → 351 (−9); gas_st 1 → 3; nuclear / hydro / wind / solar /
biomass **unchanged to the MWh**. So the response is in-state gas-CC displaced by uncarbonized
solar import plus a small CC→CT re-ordering — confined to the fossil rows and the import
substitution the higher in-state carbon cost buys, exactly the claimed footprint. Nothing
outside it moved.

**G-CTRL, reported not buried.** The base arm reproduces the committed `results/ff-t1f-d46/
caiso` 2026 row **exactly** — by-fuel generation dict equal, CO2 30.5116 = 30.5116, price
55.32 = 55.32 — even though the d46 bundle sits on a pre-D60 cache key (`772b1e5abc7fc80c`).
Under rule 29 clause (b) that committed row was a valid form-4 control for 2026, and the base
solve-year (7.1 min) was redundant; I spent it because the key difference read as a possible
drift and I had not run the G-DRIFT audit on the d46 → HEAD delta first. The audit answer,
now measured rather than argued: every solve-path change between the d46 commit and HEAD is
INERT for CAISO 2026 (identical output). One solve-year was spent that the rule says to skip.

**What the T0 does not show, as pre-declared:** nothing about `spec.py:1931` — the corridor
field is dead (§0.3) and the corridor branch is not even entered under CAISO's shipped
forecast posture (`caiso_per_hub_intertie` / `caiso_reference_price_seam` both off). The
seam fix is proven at the unit level (§3.1) and is offer-inert by the zero-LP identity.

**Registration.** The pair is a throwaway rule-29 screen (one year, one arm) — NOT registered
on the forecast dashboard and not quoted as a keeper number. WS-1b's six-ISO paired probe
(REF vs `carbon_price_path="mid"` post-repair) is the registrable CAISO carbon evidence.

## 4. Item 4 — the CAP-STATE-TIGHT case, pre-declared (NOT run)

### 4.1 What the mass-cap row can express at HEAD (zero-LP census)

`mass_cap_enabled=True` arms `policy/cap_and_trade.py::_power_sector_cap`: an explicit
`mass_cap_tons` wins, else the program's PUBLISHED budget for the year
(`_published_power_sector_budget`), else the row is inert and the adder path stays active.
Published coverage over the horizon, metric Mt, from `constants.py`'s landed schedules:

| ISO | 2025 (per-state, member set) | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032+ |
|---|---|---|---|---|---|---|---|---|
| CAISO (CARB, whole-economy) | 267.4 | none | 240.6 | 227.3 | 213.9 | 200.5 | 193.8 | none |
| NYISO (RGGI) | 23.164 (NY) | none | 57.334 ¹ | 55.701 ¹ | 54.068 ¹ | 52.526 ¹ | none | none |
| NEISO (RGGI) | 20.670 (six states) | none | 57.334 ¹ | 55.701 ¹ | 54.068 ¹ | 52.526 ¹ | none | none |

¹ `RGGI_MEMBER_STATES_BY_YEAR` stops at 2025, so 2027–2030 fall back to the REGIONAL
`RGGI_STATE_CO2_BUDGET["RGGI"]` total — the docstring's "looser over-bound", i.e. the whole
11-state RGGI budget applied to one ISO. Against the committed T1-F REF trajectories (CO2 Mt:
CAISO 30.5 → 25.8, NYISO 23.7 → 21.0, NEISO 16.3 → 14.7 over 2026–2030) the published path is
therefore **slack everywhere except NYISO on its own 2025 per-state budget** (23.16 vs 23.74
modelled — the one place the row would bind), inert in 2026 and after 2031, and by 2027 wildly
slack on the RGGI ISOs. "Published schedule alone" is NOT a tight case.

**A declining schedule cannot be written as one case at HEAD:** `mass_cap_tons` is a scalar
`float | None` (`scenarios.py:2765`) — one number for every year. Expressing `CAP-STATE-TIGHT`
needs either (a) a `{year: tons}` schedule field (a NEW `ScenarioConfig` field → its own matrix
row in the same PR, rule 28 c; the natural name is `mass_cap_tons_by_year`, read by
`_power_sector_cap` before the scalar), or (b) per-year single-year cases, which the campaign
harness does not chain. **(a) is the build**, and it belongs to the lane that runs the case
(WS-1b, wave 2), not to this lane's file list.

### 4.2 The pre-declared case (levels illustrative until owner card D-2)

```yaml
# configs/scenario_campaign_matrix.yaml  (WS-0 owns the file; this is the declaration)
CAP-STATE-TIGHT:
  mass_cap_enabled: true
  mass_cap_program: co2
  state_carbon_pricing: true          # the row REPLACES the adder on a program ISO
  carbon_price_path: zero             # no federal price in the cap case
  mass_cap_tons_by_year:              # NEEDS the schedule field (§4.1 a); metric tonnes
    # anchor = the 2025 published per-state budget (the last year with a member-set
    # breakdown), then a linear decline to 20 % of the anchor by 2050 — RGGI's own
    # post-2030 trajectory is not landed in the repo, and CARB publishes no
    # power-sector budget at all, so the slope is an OWNER level (D-2).
    NYISO: {2026: 23.16e6, 2030: 20.2e6, 2040: 12.8e6, 2050: 4.6e6}
    NEISO: {2026: 20.67e6, 2030: 18.0e6, 2040: 11.4e6, 2050: 4.1e6}
    CAISO: {2026: 30.5e6,  2030: 26.5e6, 2040: 16.5e6, 2050: 6.1e6}   # REF-2026 anchored:
    #   CARB's whole-economy cap (267 Mt) is meaningless as a power-sector row; the
    #   anchor is the model's own REF 2026 CO2, declining on the same 80 % slope.
```

Applies to CAISO / NYISO / NEISO only (`CAP_AND_TRADE_PROGRAMS` gates the row; ERCOT / MISO
have no program; PJM's partial footprint is a separate declaration). Read-out: the row dual is
the endogenous power-sector allowance price `DispatchResult.co2_cap_price` ($/t, one per active
cap), to be compared against the adder path's exogenous escalator in the same year — the
price-vs-quantity instrument comparison the case exists for.

### 4.3 Is the cap row's slack / dual in the exported summary? **NO — routed to WS-0 (G-E4 rider)**

`DispatchResult.co2_cap_price` (`model/lp/model.py:1235`, the negated row dual) has **no reader
under `src/market_sim/results/`**: `results/export.py::summarize_year` (`:198-210`) emits
`emissions_mt`, prices, generation, capacity, curtailment, storage cycles, clean share — no cap
price, no slack, no binding flag — and the `full_horizon_summary.json` trajectory row
(`co2_mt`, `lw_price`, `rps_dual`, …) carries `rps_dual` but nothing for the cap. The ONLY
consumer in the tree is `scripts/run_driver_battery.py:905` (the T1.2 adder/cap duality rung,
in-memory). No slack diagnostic exists at any layer (the LP returns the dual only; slack =
`cap_tons − Σ coeff·P` is not computed). `results/export.py` is SCN-WS0's file, so this lane
does not add it: **WS-0 should add `co2_cap_price` (per active cap) and `co2_cap_slack_t` to
`summarize_year` and to the trajectory row, alongside its by-fuel / by-zone CO2 grain** —
without it the CAP-STATE-TIGHT case has no exported read-out and cannot be scored.

## 5. Byte-identity key list

No `ScenarioConfig` field is added, moved or re-defaulted by this lane; `cache_key()` is
untouched, so **no key moves** (pinned default `e5ecd4105ada3e58` stands). The two code changes
are behaviour-inert for every committed bundle (§2, §3.1). Every bundle below carries
`carbon_price_path="zero"`; none carries a non-`"zero"` path on any ISO, so the FLOOR ruling
would create **zero** stale bundles (the fact the item-1 cache-epoch entry would record).

**Keepers** (`frontend/data/backcast/keepers/<ISO>.json` → bundle `run_config.json`; all
`mode=backcast`, `carbon_price=0.0`, `carbon_price_path="zero"`, `state_carbon_pricing=True`,
`policy_bundle="current"`; keeper bundles record no `cache_key` field — the identity claim is
that no key-bearing field changed): CAISO `2026-09-05-caiso-251-b1-nomargin`
(`caiso251_arm_nomargin`), ERCOT `2026-09-05-ercot248-two-config-keeper`
(`ercot248_two_config_keeper`), MISO `2026-09-05-miso-217-intermphys` (`miso217_intermphys_B`),
NEISO `2026-08-17-neiso-99-joint-p1` (`neiso99_joint_B`), NYISO
`2026-09-05-nyiso-192-astoria-panel` (`nyiso192_astoria_panel`), PJM
`2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`).

**Committed forecast bundles** (`results/**/run_config.json`, `scenario_config.carbon_price /
carbon_price_path / carbon_price_delta`):

| bundle | ISO | cache key | carbon posture |
|---|---|---|---|
| ff-t1f-d45r/miso · nyiso · pjm | MISO/NYISO/PJM | `8d8bc63a0d4378a9` · `cc7d1050a8090c76` · `321f04e9060787f0` | 0 / zero / 0 |
| ff-t1f-d46/caiso · ercot · neiso | CAISO/ERCOT/NEISO | `772b1e5abc7fc80c` · `873d8c0e6cab52ae` · `6690e4d6d66bc819` | 0 / zero / 0 |
| ff-t1f-d50/ercot · neiso · pjm | ERCOT/NEISO/PJM | `0c3e9cd5b5993bdf` · `18515067bf4d2fbe` · `167e65187f32056b` | 0 / zero / 0 |
| ff-t1f-d60/miso · nyiso | MISO/NYISO | `b1a73a087064ffd8` · `19a9690bb12c8459` | 0 / zero / 0 |
| ff-t1f-s123/verify; s4hydro/neiso(+control); s6-pjm/ledger | MISO; NEISO; PJM | `587dc5b32ba71ceb`; `9a7f68fc7dcac931`; `31a19d815fa319a7` | 0 / zero / – |
| ff-t3-neiso-golden/bau, bau/fc6/{base,gaspm5,gasup150} | NEISO | `706e7ba8e6582d42`, `2d017ed9675aa386`, `65662ca117959ee5` | 0 / zero / 0 |
| ff-t3-neiso-golden/bau/fc6/carbon_plus25 | NEISO | `f7cced798488ddac` | 0 / zero / **25** (delta) |
| ff-t3-neiso-golden/bau-d46, bau-d46/fc6/{base,gaspm5,gasup150} | NEISO | `67678e58b2d0526c`, `e84079053b581a9e`, `96984c538320d6d6` | 0 / zero / 0 |
| ff-t3-neiso-golden/bau-d46/fc6/carbon_plus25 | NEISO | `56019f3b0850e9f9` | 0 / zero / **25** (delta) |
| ff-t3-neiso-golden/bau-prera-2026-08-31 (+ fc6 base/gaspm5/gasup150) | NEISO | `a4b11ef4aaa1be35` (`0365174ab16cc318`, `1de43201e2040f7f`, `13f9357712250600`) | 0 / zero / – |
| ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/carbon25 | NEISO | `7924eccc695c0168` | **25 (scalar, the D21 inversion)** / zero / – |
| ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/carbon_plus25 | NEISO | `7784d408fc955785` | 0 / zero / **25** (delta) |
| hindcast/caiso-…-t1h-d46 | CAISO | `2c8cc7d19ccaed4c` | 0 / zero / 0 |
| hindcast/ercot-…-t1h-d46 · d4m | ERCOT | `67d5dcc1ada2e2df` · `f061b2646bfaac8b` | 0 / zero / – |
| hindcast/miso-…-t1h-d27 · d31 · d33 · d46 · d53-sectorgate · d53-…-d51ratio · d33-probe-entrydiag | MISO | `501b5f64b8adf8d4` · `3649264ca98a1fb4` · `40173304213d39cd` · `eff2c890746ec966` · `c306ddc6d28c60c2` · `6ea92547eaa62559` · `1b0f1a5e75719b92` | 0 / zero / – |
| hindcast/neiso-…-t1h-d37-armed · d45r · d46; neiso-2023-2027-crossover-capxd14 · -rcrepair | NEISO | `313ba0612435b963` · `d6c0137e37bf3200` · `da19b85495178949`; `07e416f3f8072e7c` (both) | 0 / zero / – |
| hindcast/nyiso-…-t1h-d45r · d45r-curveon · d52-devintage; nyiso-2023-2027-crossover-capxd10 | NYISO | `91686abe7a744a88` · `cad77112c804881d` · `911371a8cf23d5c3`; `7323dc2ddabc95c7` | 0 / zero / – |
| hindcast/pjm-…-t1h-d45 · d45r · d45r-fixed · d57-clearing | PJM | `ea767a6254b8e4af` · `c6091bd5b62bbc3f` · `896da48960560a29` · `f0e050e820c1159a` | 0 / zero / – |
| ff2b-after/{caiso,neiso,nyiso}; ffr1c/{before,after}-{caiso,miso,nyiso} | — | `4acf6ad23f51314a` `fe4d5bd213dd8607` `7a475a3d06eeddd6`; `d2e04c6d74f01db2` `755fd1fba560e0e3` `cfde2bf55b3a06d9` | pre-`run_config.json` era; summary only |

## 6. D-1 evidence memo — written for the owner alone

### 6.1 The question, in one paragraph

Three fields set a carbon price in a forecast. `carbon_price` is a flat $/t that **replaces**
whatever the ISO would otherwise pay (your ruling Q26 kept that, with a warning when it is a
cut). `carbon_price_path` names an RFF federal trajectory (`low/mid/high`; `zero` = none).
`state_carbon_pricing` charges the ISO's own state program — California's cap-and-trade for
CAISO, RGGI for NYISO and NEISO — at the last auction price escalated 7 %/yr. **D-1 asks what
a unit in a program state should pay when a federal path is ALSO named.** Today the code
answers "the federal path INSTEAD of the state program" (`replace`). The alternatives are
"the higher of the two" (`floor`) and "both, added together" (`additive`).

### 6.2 What the evidence says

1. **Today's answer is a carbon-price cut on every program ISO in every year** (§0.1). Naming
   the RFF mid path — which is what `policy_bundle="tight"` does — takes CAISO from $30→$152/t
   down to $0→$50/t, NYISO from $24→$120 down to the same $0→$50, NEISO from $26→$132 down to
   the same. The RFF federal paths were written as a federal price on top of nothing; the state
   escalators were added later (EM-6, 2026-08) and the two were never reconciled. So "tight"
   is loose on the three ISOs where carbon already bites, and a campaign row labelled
   "federal carbon price" would report LOWER carbon on them. That is the D23 inversion again
   through a second field, and the Q26 guard does not see it (it watches `carbon_price` only).
2. **Under `floor`, `tight` becomes an exact no-op on the three program ISOs** — the mid path
   never exceeds the state escalator in any year, nor does `low`. Only `high` ever does, and
   only mid-horizon on the RGGI ISOs (NYISO 2031–2047, at most +$9/t; NEISO 2033–2042, at most
   +$3/t); never on CAISO. So `floor` fixes the sign but does NOT make a federal-path scenario
   "do something" on CAISO/NYISO/NEISO — its carbon leg bites only on ERCOT / PJM / MISO. That
   is the honest reading of a federal price that a state program already exceeds, but you
   should know it before choosing, because it decides what the campaign's CARB-LO/MID/HI rows
   can show on half the ISOs.
3. **Under `additive`, a program-state unit pays the federal path PLUS the state escalator**
   ($30 + $0 in 2026 rising to $152 + $50 = $202/t on CAISO in 2050 under mid). Legally that is
   what concurrent instruments do (a federal fee does not cancel a state allowance obligation).
   But the state allowance price is not a fixed escalator in that world: a federal price that
   does the abatement work collapses demand for state allowances toward the program's auction
   reserve/floor, so the state term would fall, not keep rising 7 %/yr. The model has no
   endogenous state price (it is an exogenous escalator, `projected_price`), so `additive`
   double-charges relative to reality by roughly the state escalator minus its floor. It is
   also duplicative in the code: `carbon_price_delta` (your D26 instrument) is ALREADY the
   additive channel on the resolved signal, so an additive `carbon_price_path` would be a
   second mechanism for one phenomenon (rule 19).
4. **`floor` is what a BINDING instrument means to a unit.** The unit's marginal compliance
   cost is set by whichever instrument is tighter; a state cap's allowance price cannot sit
   below a federal price that every emitter in the state also faces (the state price would
   fall to its floor and the federal price would be the binding one), and where the state
   escalator is the higher of the two the federal price is not the binding constraint. `max`
   is the exogenous-price approximation of that, at zero new parameters, and it is monotone:
   a higher federal path never lowers anyone's carbon price.
5. **Cost of changing it: nothing stale.** No committed bundle carries a non-`zero` path on any
   ISO (§5), every keeper is a backcast (the branch is forecast-only), and no cache key moves.
   The change is one branch of one function, one test flip, one new test, one ledger entry.

### 6.3 Recommendation and the two things to decide with it

**Rule FLOOR.** It restores the sign (1), is the faithful exogenous reading of concurrent
instruments (4), keeps Q26's `carbon_price` replace-plus-guard untouched, and creates no stale
evidence (5). Two consequences to rule on in the same sitting, so the executing lane is not
guessing:

- **D-1(b) — what should `policy_bundle="tight"` mean on a program ISO once it is a no-op
  there?** Options: leave it (tight = federal mid floor, which is honest: a federal mid price
  changes nothing where the state already prices higher); or redefine the bundle's carbon leg
  as an INCREMENT (`carbon_price_delta`) so "tight" bites everywhere. The first keeps the
  bundle a federal-policy statement; the second turns it into a "more carbon everywhere"
  statement. This is a D-2 level question and I recommend the first, with the campaign's
  CARB-LO/MID/HI rows written as RFF floors exactly as plan §3.5 has them, and a separate
  delta-based row if you want a program-ISO carbon response.
- **D-1(c) — PJM's partial footprint under a federal floor.** With `floor` on a partial-
  footprint ISO the natural reading is per generator: a RGGI-state unit pays
  `max(federal, RGGI)`, a non-RGGI unit pays `federal`. The G-C3 seam landed here (§2) prices
  the state term per generator but is built from the program adder alone, exactly as the
  backcast does; the floor lane should build the per-generator `max` there. Inert today (PJM's
  forecast adder is $0), stated so it is not discovered later.

### 6.4 What the FLOOR implementation is (for the executing lane; not done here)

- `cap_and_trade.py::resolve_carbon_program` forecast branch (`:289-291`): stop nulling the
  program price on an explicit path — always return the projected (or named-path) program
  adder; the combination happens one level up.
- `carbon.py::resolved_base_trajectory_price`: compute both the program adder and the RFF
  path value and return `max(program, path)` on a program ISO (path alone elsewhere; program
  alone at path `zero`). `carbon_price` (scalar) and `carbon_price_delta` untouched.
- D34 guard: extend `carbon_price_below_base_warning` to fire when an explicit path's
  resolved value would sit below the program trajectory — under `floor` that cannot happen,
  so the guard becomes an assertion of the invariant rather than a warning.
- Tests: `test_cap_and_trade.py::test_explicit_rff_path_wins_in_forecast` (`:135`) → asserts
  the floor; add `NEISO tight ≥ current in every year 2026–2050` (strict increase is FALSE
  under floor at mid — it is equality; the mirror test should assert `>=` with equality at
  mid and strict `>` only in the `high` crossing years, or the test will fail on the very
  arithmetic in §0.1).
- `results/cache.py` epoch-ledger entry: same-key invalidation, scope "forecast bundles with a
  non-`zero` `carbon_price_path` on CAISO/NYISO/NEISO" — an empty set at this commit (§5).
- Matrix: `carbon_price_path` cells on the three program ISOs move from the semantics stamped
  at this lane (§7) to "floor"; `policy_bundle` likewise.

## 7. Records

- Instruments and outputs: `docs/handoffs/scn-ws1a/` (Phase-0 trajectory `.py/.json/.txt`,
  G-C2 seam census, import-offer table); `docs/handoffs/scn-ws1a/t0/` (the CAISO T0 pair:
  summaries, run configs, scoring instrument + JSON, launch script, pair log).
- Code: `src/market_sim/policy/cap_and_trade.py` (+`carbon_mc_column`), `src/market_sim/
  runner.py` (the `assemble_mc` call site + one import), `src/market_sim/model/interchange/
  spec.py` (the one corridor line), `tests/unit/policy/test_cap_and_trade.py` (+2 classes).
- Not touched: `cap_and_trade.py::resolve_carbon_program`, `carbon.py`, `scenario_resolvers.py`,
  `config/scenarios.py`, `results/cache.py`, `test_carbon_price_below_base_guard.py` (all
  item-1, gated), `scripts/run_calibration.py`, `results/export.py` (WS-0), the WS-2a regions.
- Matrix: base rows `carbon_price_path` + `policy_bundle` minted (they did not exist) and a
  cell line in every shard — last commit.
- Plan §5.1 Carbon column and ledger §3 copy updated in this PR.
