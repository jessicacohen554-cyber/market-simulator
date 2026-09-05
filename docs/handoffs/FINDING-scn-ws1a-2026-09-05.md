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

## 2. Item 3 — G-C3 (pending; this section is filled by the commit that lands it)

## 3. Item 2 — G-C2 (pending; filled by the commit that lands it, with the T0 result)

## 4. Item 4 — CAP-STATE-TIGHT pre-declaration (pending)

## 5. Byte-identity key list (pending)

## 6. D-1 evidence memo (pending)

## 7. Records
