# PRECOMMIT — SCN-WS5A-POLICY-CAISO: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-CAISO (COORDINATOR, ruling **S16**) · **Model** Opus
(`claude-opus-5`, rule 27 `[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-caiso-szt2qw` · **Data profile** `caiso` (full clone; `data/raw`
6.1 GB already local) · **Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`,
`reference_case: REF` · **Charter** SCN-DESK ledger §5.4 (r#18, charter **v6**) + the **S15**
bracketing addendum + **r#18 am.1** charter **v7** (the coordinator/shard split, ruling S16) ·
**Predecessors** `PRECOMMIT-/FINDING-scn-ws5a-resolve-caiso-2026-09-06.md` (THE PIN, the
inherited G-DRIFT, the re-solved REF) and `FINDING-scn-ws5a-load-caiso-2026-09-06.md`.

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
config resolved at THE PIN through the runner's own chain, a committed artifact, or arithmetic
on the two. Nothing here is revised after a solve; §6's predictions are scored as written and
misses are reported at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-caiso-2026-09-06.md` §0 (precondition P1). Re-verified
here: `git merge-base --is-ancestor bdfb3095 origin/main` → **yes**; `origin/main` is **28
non-merge solve-path commits** past it at PRECOMMIT time (§5.2). **THE PIN IS NOT MOVED AFTER
THE FIRST SOLVE.** Anything on `main` after it is recorded as post-pin, never retro-fitted and
never used to re-read a result. My keys are therefore **pre-fingerprint keys** — capx **D79**
(`16210868`) put the solve-surface fingerprint into `cache_key()` *after* the pin — and §2 is
the record of them.

## 0.1 Bottom line before any LP

1. **Six of fourteen cases are KILLED on a proven identity; eight survive.** The three
   `CARB-*` arms and `CARB-MID+LOAD-HI` resolve carbon **identically to REF/LOAD-HI in every
   year** under ruling S2's floor (§4.1), and `VOL-MID` / `VOL-HI` are **slack in all five
   years** (§3.2). None is solved.
2. **The whole voluntary axis is inert on CAISO — a stronger result than any sibling lane's.**
   ERCOT killed `VOL-MID` and kept `VOL-HI`; here **both** die, and `ALL-CLEAN`'s voluntary leg
   is slack too, by **33.7–47.1 TWh** at its own DC-high posture (§3.2). CAISO's data-centre
   block is the campaign's smallest (1,622 MW mid / 4,240 MW high at 2030) while its eligible
   wind+solar fleet is 73–86 TWh, so `V` never approaches `G`.
3. **The S15 mask BINDS on CAISO in all five years, and it binds at an exact tie.** REF's
   `rps_dual` is **50.0 in every year** — the CAISO RPS row sits at its `STATE_RPS_ACP` escape
   — so the committed premium ladder {10, 20, 30} and `CES-T80`'s ACP $50 add **nothing** to
   the ENTRY fold. `CES-P60` is added, and **G-B1 is already computed and CLEARS** (60.0 > 50.0
   strictly, wind/solar/geothermal, every zone, every year — §A).
4. **The mask is an ENTRY-screen mask only, and CAISO's CES legs are far from inert.** The
   premium reaches DISPATCH directly through `policy.eac.apply_eac_to_mc` /
   `compute_eac_dispatch_credits`, which is not a `max()` fold against the RPS dual at all:
   `gas_cc_ccs` marginal cost falls by **0.95 × premium** on a fleet that carries **22.7 → 65.0
   TWh** in REF's 2028–2030. That, not entry, is where CAISO's CES response will live (§6.3).
5. **`CAP-STATE-TIGHT` is LIVE and the SCN-CAP binding test must be restated post-D77.** Its
   budget is 30.5 → 26.5 Mt; the re-solved REF is 31.31 / 34.51 / 30.12 / 21.97 / 19.96 Mt, so
   the naive REF comparison now reads *slack* in 2029–2030 where SCN-CAP read binding in all
   five. **That comparison is the wrong test** and §4.2 replaces it with a one-directional one:
   the arm **replaces** the $30.02–$39.36/t CARB adder with the row, so its own emissions are
   **≥** REF's, and REF's 2029–2030 lows are *produced by* that adder.
6. **CAISO's REF is in an adequacy shortfall (I7 + I12, 2026–2028) and in RPS escape in every
   year.** Gate **G2** asserts this rather than discovering it, and §7 names which readings are
   disclosure-only.

---

## 1. Preconditions — verified

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE-CAISO re-solved the three legs at THE PIN, all gates PASS | **MET** | `FINDING-scn-ws5a-resolve-caiso-2026-09-06.md` §4: G1–G5 PASS on REF / LOAD-HI / LOAD-HI-ORGANIC. Both its magnitude bands MISS (P-A −11.2021 Mt against a 3–8 Mt band; P-B −0.9799 Mt against 1–3 Mt) — read, and carried into §6 as a sizing lesson, not as a defect. |
| **P2** | the re-solved REF is at `…-r2/CAISO/REF/`, not the pre-fix path | **MET** | `results/scn-campaign-load-2026-09-06-r2/CAISO/{REF,LOAD-HI,LOAD-HI-ORGANIC}/` exist on `main`; `results/scn-campaign-load-2026-09-06/CAISO/` **does not exist** (deleted by RESOLVE under rule 26). REF `cache_key` **`2d16a246bb372e4a`**, `git.sha` **`c538ecfb`**, `git.dirty` **false**, `solved_years` 5/5. `c538ecfb` is a PIN descendant and `git diff bdfb3095 c538ecfb -- src/market_sim scripts configs data/raw/_validation-source data/raw/reference` is **EMPTY** (verified here, not inherited) — the one file it changes is RESOLVE's own PRECOMMIT. **REF is never re-solved.** |
| **P3** | `CARB-*` read `carbon_price_path` low/mid/high; `ALL-CLEAN`'s carbon component mid | **MET at the pin** | `configs/scenario_campaign_matrix.yaml` at `bdfb3095`: `CARB-LO/MID/HI → low/mid/high`; `CARB-MID+LOAD-HI → mid`; `ALL-CLEAN → mid`; `CAP-STATE-TIGHT → zero`. Resolved $/t in §4.1. |
| **P4** | rule 12 concurrency | **MET by construction** | This lane solves nothing. Each of the four shards is its own container with one solve at a time and years strictly sequential (§8); the ≤2 per-plant cap is a per-container memory constraint and does not compose across containers (r#18 am.1). |
| **P5** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` exist; SCN-CAP's binding test re-run on the POST-D77 REF | **MET, and the test is REPLACED** | Both live at the pin; the CAISO schedule resolves to 30.5 / 29.5 / 28.5 / 27.5 / 26.5 Mt (§4.2). SCN-CAP measured the budget binding in all five years on the PRE-D77 REF. Post-D77 the naive comparison flips in **2029 and 2030**, not in 2026 as the charter anticipated — 2026 is byte-unmoved by D77 (31.3061 both). §4.2 states why the naive comparison is not the binding test and gives the one-directional replacement. |

### 1.1 The constant families this lane consumes — read at THE PIN `bdfb3095`

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `config/fuel_trajectories.py` | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | keys `CAISO`, `NYISO`, `NEISO` — **CAISO present** (CARB) |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NYISO`, `NEISO`, `PJM` — **CAISO present** |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; **mid {2023: 0.08}**; **high {2023: 0.08}** (high coincides with mid — WS-3b §4(c)) |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; **mid {2026: 0.5}** (ILLUSTRATIVE, ruling S9); high {2026: 1.0} |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5** (ILLUSTRATIVE, S9); **high 7.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built. **CAISO's modelled fleet carries neither offshore wind nor geothermal**, so the eligible set here is exactly wind + solar. |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["CAISO"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = **1.0** |
| `DATACENTER_ADDITIONS_MW["CAISO"]` | `config/constants.py` | mid {2025: 98; 2030: **1,622**; 2035: 4,123; 2040: 4,382} MW; high {2025: 125; 2030: **4,240**; 2035: 6,531; 2040: 6,658} MW (the CEC Form 1.1c *Local Reliability Scenario* intake — the S4/D-4 data that made `high ≠ mid`, WS-5A-LOAD §0.1) |
| `DEMAND_GROWTH_RATES["CAISO"]` | `config/constants.py` | mid {near 0.032425, long 0.016710}; high {near 0.048638, long 0.023394} |
| `STATE_RPS_ACP["CAISO"]` | `config/capacity_market.py` | **50.0** $/MWh |
| `STATE_RPS_FLOORS["CAISO"]` | `config/capacity_market.py` | {2021: 0.33, 2024: 0.44, 2026: 0.50, 2030: 0.60, 2040: 0.60, 2045: 0.60} |
| `_RPS_ELIGIBLE_FUELS` | `model/capacity_evolution/retirements.py:144` | `frozenset({"wind", "solar"})` — the fuel gate that makes the CES legs non-inert (S15) |
| `eac_price_*` (every one) | `ScenarioConfig` defaults, resolved on REF | **0.0** — so the federal CES premium is the SOLE EAC in every arm that carries it |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}; ACP $50/MWh |
| `mass_cap_tons_by_year["CAISO"]` | the campaign YAML (ruling S12) | {2026: 30.5e6, 2030: 26.5e6, 2040: 16.5e6, 2050: 6.1e6} — the **disclosed, non-published** REF-2026 anchor |

---

## 2. The case set at THE PIN — resolved keys, kills and solves

Resolved exactly as `runner.run_scenario_iso` does (`runner.py:1384-1423`): `matrix_configs`
→ `resolve_policy_bundle` → `set_caiso_fsno_partition(iso=="CAISO" and
config.caiso_fsno_subzonal_topology)` → `apply_iso_scenario_defaults` → `.cache_key()`. Base:
`configs/scenarios/caiso_scenario_base_2026_2030.yaml`. Script + machine-readable output:
`docs/handoffs/scn-ws5a-policy-caiso/phase0-caiso-2026-09-07.{py,json}`.

**Chain validation — RESOLVE's own two CAISO rows reproduce independently:** `REF`
**`2d16a246bb372e4a`** and `LOAD-HI` **`86bfde6ed2896b99`**, identical to
`PRECOMMIT-scn-ws5a-resolve-caiso` §2. The chain below is therefore the one the solve uses,
not a naive `cache_key()`.

| case | key at THE PIN | override vs REF | verdict |
|---|---|---|---|
| *REF (control, never solved)* | `2d16a246bb372e4a` | — | **reused** — the committed re-solved leg |
| *LOAD-HI (pairing base, never solved)* | `86bfde6ed2896b99` | growth high + DC high | **reused** — the committed re-solved leg |
| `CARB-LO` | `7dc545a5e5abbe8b` | `carbon_price_path: low` | **KILLED — §4.1** |
| `CARB-MID` | `e43c47c8f49e4dd1` | `carbon_price_path: mid` | **KILLED — §4.1** |
| `CARB-HI` | `2d1950d20e4ce38a` | `carbon_price_path: high` | **KILLED — §4.1** |
| `CARB-MID+LOAD-HI` | `2eaf1143794bada5` | carbon mid + growth high + DC high | **KILLED — §4.1** (identical to `LOAD-HI`) |
| `VOL-MID` | `ff4ddde42fbffe97` | `voluntary_clean_demand_path: mid` | **KILLED — §3.2** |
| `VOL-HI` | `810c744cda2cacfc` | `voluntary_clean_demand_path: high` | **KILLED — §3.2** |
| `CES-P10` | `f672e9134d51a475` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `46f5eb984e5a4614` | premium 20.0 | **SOLVE** |
| `CES-P30` | `cedae86096ba6c3e` | premium 30.0 | **SOLVE** |
| **`CES-P60`** (S15) | `cb35acef1879e80e` | premium 60.0 | **SOLVE — §A** |
| `CES-T80` | `2ad09fb1eac689a9` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CES-P20+VOL-HI` | `130a2410b012cf93` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `e2820065dbdcb708` | carbon mid + growth high + DC high + CES target + ACP 50 + voluntary high | **SOLVE** |
| `CAP-STATE-TIGHT` | `2c5abed281bcee82` | `mass_cap_enabled`, `mass_cap_program: co2`, `state_carbon_pricing`, `carbon_price_path: zero`, the schedule | **SOLVE — §4.2** |

**16 distinct keys**, so no leg can collide with another or with a committed bundle.
`results/CAISO/` **does not exist** on this container (recorded pre-solve), so none of the
eight SOLVE keys is occupied by any bundle at any point.

**8 legs to solve, 40 solve-years.**

### 2.1 Every kill is a ONE-FIELD identity, measured

The resolved `ScenarioConfig`s were diffed field-by-field (`asdict`, all ~800 fields). Each
kill pair differs in **exactly one field**, and that field's own resolved value is measured
identical across every year:

| pair | the single differing field | why the LP cannot see it |
|---|---|---|
| `CARB-LO` / `CARB-MID` / `CARB-HI` vs **REF** | `carbon_price_path` (`low`/`mid`/`high` vs `zero`) | §4.1: resolved $/t identical in all five years, and §4.3 audits that the field reaches the LP through exactly one seam |
| `CARB-MID+LOAD-HI` vs **LOAD-HI** | `carbon_price_path` (`mid` vs `zero`) | idem — and `LOAD-HI` differs from REF only in `demand_growth_path` + `datacenter_load_path`, which this case sets to the same values |
| `VOL-MID` / `VOL-HI` vs **REF** | `voluntary_clean_demand_path` (`mid`/`high` vs `off`) | §3.2: the row is slack at REF's own optimum in every year |

---

## 3. Phase 0 — the voluntary row, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed
(`load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`), never by
re-deriving the memo's arithmetic. Zones: the 3 CAISO zones + the WECC import node.

### 3.1 The resolved volumes (TWh)

| posture | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| REF / every DC-mid case | `E_total` | 238.198 | 245.921 | 253.895 | 262.128 | 270.627 |
| | `E_DC` | 2.999 | 5.269 | 7.538 | 9.808 | 12.077 |
| `VOL-MID` | **V** | **20.316** | **21.887** | **23.478** | **25.090** | **26.723** |
| `VOL-HI`, `CES-P20+VOL-HI` | **V** | **21.815** | **24.521** | **27.247** | **29.993** | **32.761** |
| `ALL-CLEAN` / `LOAD-HI` posture (growth high, DC high) | `E_total` | 245.738 | 257.690 | 270.223 | 283.367 | 297.149 |
| | `E_DC` | 7.059 | 13.187 | 19.315 | 25.443 | 31.571 |
| `ALL-CLEAN` | **V** | **26.153** | **32.747** | **39.388** | **46.077** | **52.817** |

`s_base` 0.08, `w_ISO` 1.0, `f_commit` 0.5 (mid) / 1.0 (high) in every year.

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — and the double kill

Eligible generation `G` = wind + solar **as dispatched in the paired committed baseline**
(CAISO's modelled fleet has no offshore wind and no geothermal; the fuel keys present in every
committed leg are exactly `biomass, coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro, import,
nuclear, oil, solar, wind`). `G_REF` from `…-r2/CAISO/REF/`; `G_LOAD-HI` from `…/LOAD-HI/`.

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` | 73.266 | 73.266 | 73.266 | 84.643 | 86.487 |
| `G_LOAD-HI` | 73.266 | 73.266 | 73.266 | 84.643 | 86.487 |

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | 20.3 ≪ 73.3 (**+52.950**) | 21.9 ≪ 73.3 (**+51.379**) | 23.5 ≪ 73.3 (**+49.788**) | 25.1 ≪ 84.6 (**+59.553**) | 26.7 ≪ 86.5 (**+59.764**) | **(i) SLACK ×5** |
| **`VOL-HI`** vs `G_REF` | 21.8 ≪ 73.3 (**+51.451**) | 24.5 ≪ 73.3 (**+48.745**) | 27.2 ≪ 73.3 (**+46.019**) | 30.0 ≪ 84.6 (**+54.650**) | 32.8 ≪ 86.5 (**+53.726**) | **(i) SLACK ×5** |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | 26.2 ≪ 73.3 (+47.113) | 32.7 ≪ 73.3 (+40.519) | 39.4 ≪ 73.3 (+33.878) | 46.1 ≪ 84.6 (+38.566) | 52.8 ≪ 86.5 (**+33.670**) | **(i) SLACK ×5** |
| **`CES-P20+VOL-HI`** | identical `V` to `VOL-HI` (same demand posture) | | | | | **(i) SLACK ×5 at the REF baseline** |

**`VOL-MID` AND `VOL-HI` ARE BOTH KILLED — the identity, stated as an argument.** The
voluntary row adds one constraint plus one escape column of strictly positive cost. When
`V ≤ G` at REF's own optimum, REF's solution is feasible for the arm with `ESC = 0` and carries
the same objective value; the arm's feasible set is REF's intersected with the new row, and
REF's optimum lies inside it — so REF's optimum **is** the arm's optimum, the dual is 0, and
the deployment half (the dual through the screens' `max()` seam) is unarmed. Both arms are
byte-identical to REF in all five years and are **not solved**. The thinnest margin over both
arms is 2028's **+46.019 TWh**, **63 %** of `G_REF` — slack, not marginal.

**`CES-P20+VOL-HI` and `ALL-CLEAN` are NOT killed, and the distinction is deliberate.** Their
voluntary row is provably slack against the **REF** baseline, but their own LP baselines are
`CES-P20`'s and (`CES-T80` + `LOAD-HI`)'s, which do not exist until they are solved. Rule 29
clause 0 kills on a **resolved-input** identity; a predicted identity to an arm I have not
solved is a prediction, and it is registered as one (§6.5 P-13/P-14) rather than spent as a
kill. It is also the chartered surface for gate **G9** (ruling S11's two nettings) and for the
D-6 question, and it is the only empirical test available of whether the voluntary machinery
has a footprint I cannot see from the REF baseline.

**This EXTENDS every prior voluntary reading rather than repeating one.** WS-3b §6 measured
slack at ERCOT 2026 only; the ERCOT policy lane extended that to `VOL-MID` across the T1-F
window and kept `VOL-HI` live from 2028. On CAISO **both** arms are slack across the whole
window and so is the DC-high corner — because CAISO pairs the campaign's **smallest** DC block
with a large existing renewable fleet. Under ruling S10's "credit all eligible units" set that
is decisive; under D-3c's alternative (new-builds-only crediting) it would not be, and CAISO is
the sharpest case for that card the campaign has produced.

### 3.3 The WTP ceiling per arm

`voluntary_wtp_ceiling_usd_per_mwh` ships `None`, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. The charter's G7 names **$4.5/MWh**, which is the
**mid** cell (ruling S9) and bounds only the killed `VOL-MID`. Every voluntary leg that
survives phase 0 runs `high`, ceiling **$7.0/MWh**: `CES-P20+VOL-HI` and `ALL-CLEAN`. G7 is
bounded at **$7.0/MWh** on both. No level moved (the same correction the ERCOT lane recorded
in its §3.3).

---

## 4. Phase 0 — the carbon axis and the cap row

### 4.1 Resolved carbon $/tCO2 per year (`policy.carbon.resolve_carbon_price`) — the S2 floor

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `REF` | 30.0242 | 32.1259 | 34.3747 | 36.7809 | 39.3556 |
| `CARB-LO` | **30.0242** | **32.1259** | **34.3747** | **36.7809** | **39.3556** |
| `CARB-MID` | **30.0242** | **32.1259** | **34.3747** | **36.7809** | **39.3556** |
| `CARB-HI` | **30.0242** | **32.1259** | **34.3747** | **36.7809** | **39.3556** |
| `LOAD-HI` | 30.0242 | 32.1259 | 34.3747 | 36.7809 | 39.3556 |
| `CARB-MID+LOAD-HI` | **30.0242** | **32.1259** | **34.3747** | **36.7809** | **39.3556** |
| every CES-only / VOL-only case | 30.0242 | 32.1259 | 34.3747 | 36.7809 | 39.3556 |
| `CAP-STATE-TIGHT` | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |

`resolve_carbon_program` returns the same object too: `price_adder` 30.0242 / 32.125894 /
34.37470658 / 36.780936040600004 / 39.35560156344201, `cap_spec` `None`, in **REF and in all
four carbon arms alike**, to the last recorded digit.

**All four carbon arms are byte-identical to their pairing base in every year, and are
KILLED.** The RFF `high` path reaches only $30/t at **2050** while CARB is already $30.02/t at
2026, so under ruling S2's floor `max(program, path)` returns the program in every year of the
T1-F window on every arm. This is the inertness WS-1b measured on CAISO exactly
(`Δ = 0.000000` on every metric, its §3.8) and SCN-FIX2's YAML block declares — reproduced
here on this lane's own resolved configs at this lane's pin, not cited. **This is a T1-F fact,
not a horizon fact:** SCN-FIX2 records that CAISO stays inert in all 25 years of the
2026–2050 base while NYISO and NEISO see `high` cross above their program in mid-horizon
years, so a full-horizon `CARB-HI` must not be killed by transferring this argument.

`CARB-MID+LOAD-HI` therefore has no carbon content on CAISO: it is `LOAD-HI` with a carbon
label, and `LOAD-HI`'s committed re-solved bundle (`86bfde6ed2896b99`) **is** its answer. Its
key moves because the field is set; **no LP input differs** — the same "key moves, answer
cannot" class as the three `CARB-*` arms.

### 4.2 `CAP-STATE-TIGHT` — LIVE, and the binding test SCN-CAP used is replaced

The resolved schedule, from `scheduled_power_sector_budget` (linear between the S12 knots):

| year | budget (Mt) | re-solved REF CO2 (Mt) | naive REF comparison |
|---|---|---|---|
| 2026 | **30.5000** | 31.3061 | REF **over** by 0.806 |
| 2027 | **29.5000** | 34.5149 | REF **over** by 5.015 |
| 2028 | **28.5000** | 30.1194 | REF **over** by 1.619 |
| 2029 | **27.5000** | 21.9693 | REF **under** by 5.531 |
| 2030 | **26.5000** | 19.9574 | REF **under** by 6.543 |

**SCN-CAP §3 measured this budget binding in all five years on the PRE-D77 REF** (31.31 /
34.51 / 33.32 / 31.36 / 31.16 Mt — every year above the budget). The charter's precondition P5
anticipated that the thin margin at risk was CAISO-**2026**; it is not. 2026 is **byte-unmoved
by D77** (31.3061 pre and post), and what moved are **2029 and 2030**, which D77 cut by 9.39
and 11.20 Mt and which the naive comparison now reads as slack.

**The naive comparison is the wrong test, and it is not the one I gate on.** `CAP-STATE-TIGHT`
sets `state_carbon_pricing: true` with `mass_cap_enabled: true`, so the ROW **REPLACES** the
adder (the resolver invariant, one instrument at a time) — measured in §4.1: the arm's resolved
carbon price is **$0.0000 in every year** and its program object carries `cap_spec` with
`price_adder: null`, against REF's `price_adder` $30.02–$39.36 and `cap_spec: null`. The arm
therefore faces **no carbon price at all** except the row's own endogenous dual. Its emissions
before the cap acts are consequently **≥ REF's in every year**, which gives a one-directional
test:

- **REF over budget ⇒ the cap binds, certainly.** 2026, 2027, 2028 — **binding**.
- **REF under budget ⇒ INDETERMINATE, never "slack".** 2029 and 2030 REF lows are *produced by*
  the very adder this arm removes: at 2030 the adder is worth
  `(0.3806 − 0.0375) × 39.356 ≈ $13.50/MWh` to `gas_cc_ccs` against unabated `gas_cc`, and it is
  what lifted the CCS fleet to 65.0 TWh at an 83.5 % capacity factor (RESOLVE §3.2). Remove it
  and the CCS fleet loses its merit-order position, unabated `gas_cc` returns, and emissions
  move back toward the ~31 Mt level REF carried in 2026–2028 — **above** the 27.5 / 26.5 Mt
  budget.

So the case is LIVE in every year, and gate **G10** is written to test the row's **identity**
(binding ⇒ emissions = budget to 1e-6 and `co2_cap_price` > 0; slack ⇒ dual exactly 0), never a
pre-chosen regime. My own prediction is stated in §6.4 and scored as written.

### 4.3 `carbon_price_path` reaches the LP through exactly ONE seam — audited, not assumed

Every occurrence in `src/` classified:

| site | kind |
|---|---|
| `policy/carbon.py:187` — `return max(program, rff_path_price(config.carbon_price_path, year))` | **the only LP-input consumer**, inside `resolve_carbon_price`; its per-year output is measured identical (§4.1) |
| `policy/carbon.py:381` — `carbon_path_below_program_warning` | a diagnostic tripwire that returns `None` while the floor holds; no LP input |
| `config/scenarios.py:16721` | `__post_init__` gate that only calls the tripwire above; `warnings.warn`, no mutation |
| `config/scenarios.py:18450` | the cache-key field weight — key only |
| `config/scenario_resolvers.py:277/291/301` | the `policy_bundle` resolver **sets** the field; my cases run the neutral bundle, and the §2.1 field diff proves nothing else moved |
| `policy/cap_and_trade.py:227/237/304`, `results/cache.py:272-288`, `config/fuel_trajectories.py:1226`, `policy/voluntary_demand.py:5`, `policy/carbon.py:63/152/208/335/339` | **comments and docstrings only** — no live read |

That, plus the one-field diff of §2.1 and the identical resolved $/t of §4.1, is what makes the
four carbon kills a proven identity rather than an inference.

---

## 5. G-DRIFT (rule 29(b)) — form 4 holds, and no control solve is earned

### 5.1 The control question is settled by the pin itself

My arms solve at **THE PIN**; my control (the committed REF, `2d16a246bb372e4a`) solved at
`c538ecfb`, a PIN descendant whose solve-path diff against the pin is **EMPTY** (§1, P2,
verified here). Control and arms therefore sit on **the same solve surface**, which is the
strongest form of form 4 there is. The inherited `1cc45bb2..bdfb3095` audit (RESOLVE's §1,
which established CAISO's LIVE set as exactly `{D77, D65-B}`) is **not re-audited**; it is not
load-bearing here, because both sides of every comparison are post-D77.

### 5.2 `bdfb3095 .. origin/main` — for the record; I solve at THE PIN regardless

**28 non-merge solve-path commits** (`src/market_sim`, `scripts/run_full_horizon.py`,
`scripts/run_ces_leg.py`, `scripts/lib`, `configs`, `data/raw/_validation-source`,
`data/raw/reference`). Every hunk is **unreachable by construction** — a leg pinned to
`bdfb3095` cannot read a later commit — so this is a record, not a gate. Classified:

| group | commits | INERT for a CAISO forecast leg because |
|---|---|---|
| **SPP registration** (`9ee67e3c`, `24aeed4e`, `62681e22`, `18507f13`, `de0166b9`, `5486b46f`, `b429b631`, `3b676963`, `67dca44f`, `7cdd7497`, `ed44a18c`, `05fcbf3c`) | 12 | a seventh ISO's topology, registries, artifacts and data profiles. The only CAISO-touching lines in the whole window's `src/` diff are D79 solve-surface **declared hashes** (key-only), registry key additions and comments — **no CAISO value moves** (measured by grepping every added/removed `src/` line for `CAISO`) |
| **PJM/MISO gated builds** (`cd96fa26`, `beb74f0f`, `14ae4d76`, `7ff10b64`, `20611146`, `caa2936e`, `15fc14ac`) | 7 | four new `ScenarioConfig` fields — `gas_offer_margin_anchor_vintage`, `pjm_interface_feed_admissibility_gate`, `miso_seam_neighbour_hourly_ladder`, `miso_seam_neighbour_hourly_spp` — **all `= False`**, all absent from every campaign case and from CAISO's `default_scenario_overrides`; `beb74f0f`'s vintage branch additionally requires `mode == "backcast" or hindcast`, neither true here |
| **capx PJM arms** (`24311a95`, `fd2a0d18`, `6164231e`, `486c115f`, `bf97317f`) | 5 | armed through `_pjm_config.default_scenario_overrides`; CAISO resolves `capacity_market_supply_clearing_by_iso` `None`, `retirement_sector_gate` `False`, `pjm_vre_accreditation_vintage` `False` (RESOLVE §1, re-measured on this lane's own resolved configs in the phase-0 JSON) |
| **capx D79** (`16210868`) | 1 | key-only; it moved zero keys at landing. My pin is pre-D79, so §2's keys are the pre-fingerprint keys |
| **ERCOT backcast inputs** (`09c812aa`, `71d1217b`, `b8e0c537`) | 3 | ERCOT-scoped backcast measured inputs and scarcity accounting |
| **caiso-260 demand re-derive** (`caaa3e05`) | 1 | `data/raw/_validation-source/caiso-supply-consistent-demand/*` only — a CAISO **backcast** calibration input; a `mode="forecast"` leg reads the EIA-930 demand path, not this artifact |

**No LIVE hunk on either window ⇒ no control solve is earned under clause (b).**

---

## 6. What each surviving leg is expected to do — pre-registered, scored as written

Sources, all measured before this lane and none of them a residual: **WS-1b §3.8/§4** (CAISO's
carbon inertness and its zero import-CO2 leakage), **WS-2b §3** (the ERCOT CES premium ladder's
saturation *mechanism*, levels explicitly not transferred), **WS-3b §6** (the voluntary row's
arithmetic), the **committed re-solved REF/LOAD-HI**, and the code paths audited in §4.3 / §6.3.

### 6.1 The REF this lane differences against (committed, key `2d16a246bb372e4a`)

| year | CO2 Mt | lw $/MWh | max $/MWh | h≥500 | reserve margin | `rps_dual` | backstop MW | renew builds MW | retire MW | `gas_cc_ccs` TWh |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 31.3061 | 55.708 | 71.8 | 0 | 0.0916 | **50.0** | 0.0 | 0.0 | 0.0 | — |
| 2027 | 34.5149 | 55.946 | 71.7 | 0 | 0.0599 | **50.0** | 1,396.4 | 0.0 | 1,527.3 | — |
| 2028 | 30.1194 | 58.205 | 74.4 | 0 | 0.0804 | **50.0** | 2,792.8 | 0.0 | 0.8 | 22.740 |
| 2029 | 21.9693 | 58.852 | 967.4 | 11 | 0.1659 | **50.0** | 3,795.8 | 4,702.2 | 0.0 | 42.305 |
| 2030 | 19.9574 | 71.554 | 973.9 | 37 | 0.1524 | **50.0** | 2,176.6 | 702.2 | 1,127.2 | 64.988 |

FAIL set `{I7, I12}`; **I3 PASSES** (REF sheds nothing). `import_co2_mt_reported` **0.0000** in
every year — CAISO's import node **pays** the CARB border adjustment, so only the zero-EF
tranches clear (WS-1b §4).

### 6.2 The two structural facts every prediction below rests on

**(a) The ENTRY fold is masked below $50, at an exact tie.** `attr = max(effective_eac_price_for_tech, rps_credit_for_zone, _clean_credit_for_tech)`
(`new_entry.py:1131-1143`), the RPS leg carries no fuel gate, and REF's `rps_dual` is **50.0 in
all five years** (CAISO's RPS floor rises 0.50 → 0.60 while its RPS-eligible output is ~31 % of
load, so the row sits at its `STATE_RPS_ACP` escape). Measured `eac_leg` at 2027: REF 0.00;
`CES-P10/P20/P30` 10/20/30; `CES-P60` **60**; `CES-T80` 0.00 (its credit is the row dual, which
in escape is the ACP **$50 — an exact tie**). `federal_ces_replaces_state_rps` is **False** in
every arm, so no CES leg suppresses the state row.

**(b) The DISPATCH channel is NOT masked, and it is where CAISO's CES response lives.**
`policy.eac.apply_eac_to_mc` subtracts `max(legacy eac_price_*, premium × credit fraction)`
from per-generator `mc` for nuclear, `gas_cc_ccs`, geothermal, offshore wind and hydro, and
`compute_eac_dispatch_credits` does the same for the wind/solar zone adders. Every
`eac_price_*` default is **0.0** on CAISO, so the premium is the whole credit. Credit
fractions measured at the pin: wind / solar / nuclear / hydro / geothermal / offshore wind
**1.00**; **`gas_cc_ccs` 0.95**; biomass, battery, `gas_cc`, `gas_ct`, `gas_st`, coal, oil
**0.00**. This is a `max()` against a *legacy scalar*, not against the RPS dual — the RPS row's
dual never enters `mc` — so it is unmasked at every premium level.

### 6.3 The CES premium ladder — the response is dispatch, not entry

**P-1 (the mechanism, and the sharpest claim here).** The dominant channel is `gas_cc_ccs`
marginal cost falling by **0.95 × premium** = **$9.50 / $19.00 / $28.50 / $57.00** per MWh at
P10 / P20 / P30 / P60, on a fleet carrying **22.740 / 42.305 / 64.988 TWh** in REF's
2028–2030. So in **2028–2030** `gas_cc_ccs` generation **rises** and unabated `gas_cc`
**falls** roughly one-for-one, and **CO2 falls monotonically** REF → P10 → P20 → P30 → P60 in
each of those years.

**P-2 (2026–2027 is a much smaller effect, and I say why).** `ccs_retrofit_available_year` is
**2028**, so there is **no `gas_cc_ccs` fleet at all** in 2026–2027 and the only dispatch
channel is the wind/solar offer adder (−premium on resources that are already MC = 0 and
largely dispatched). I predict **|ΔCO2| < 0.5 Mt** in 2026 and 2027 in every premium arm, and
**Δ`generation_by_fuel_mwh` = 0.000 for nuclear and hydro in every year** (nuclear is baseload
at its bound; hydro is monthly-budget constrained and its lower bid is dispatch-inert by
construction, plan §5.3).

**P-3 (price).** `lw_price` **falls** monotonically with the premium in 2028–2030, because
RESOLVE §3.2 measured the corrected CCS cohort setting price in many more hours and this
channel cuts exactly that cohort's offer. I predict the 2030 `lw_price` falls from REF's
**71.554** by **$3–15/MWh at P30**; direction is the claim, the band is the guess most likely
to miss.

**P-4 (entry is masked, and this is a testable identity, not a band).** The entry attribute
term is **50.0000 in REF and in `CES-P10` / `CES-P20` / `CES-P30` alike**, so any difference in
`builds_renew_mw` among those four arms comes through the **price** channel, never the
attribute channel. REF builds **0.0 MW** of renewables in 2026–2028 and 4,702.2 / 702.2 MW in
2029–2030. I predict `builds_renew_mw` stays **0.0 in 2026–2028** in all three premium arms.

**P-5 (retirement — and the one channel that is unmasked but cannot fire).** The retirement
screen's RPS leg is fuel-gated to `_RPS_ELIGIBLE_FUELS = {wind, solar}`, so nuclear, hydro and
`gas_cc_ccs` earn `rps_for_unit = 0.0` and the premium reaches them **unmasked**. The obvious
candidate is CAISO's nuclear, which drops 18.197 → 9.082 TWh with `retire_mw` 1,127.2 at 2030.
**It cannot be deferred by any premium:** Diablo Canyon 1–2 (EIA plant 6099) are **confirmed
exits** under SB 846 (2029-10-31 / 2030-10-31) in `data/raw/confirmed-retirements/caiso.csv`,
i.e. step 0, instrument-bound, and step 0 bypasses the economic screen entirely. **I predict
`retire_mw` and the nuclear capacity path are IDENTICAL to REF in every CES arm.** If they move,
the confirmed-exit channel is not doing what its own documentation says, and that is a finding.

**P-6 (the CCS retrofit screen).** The retrofit screen values `eac_price_gas_cc_ccs`, whose
effective value becomes 0.95 × premium, so the screened uplift **improves** and I predict the
`gas_cc_ccs` **capacity** at 2030 is **≥** REF's 8,885.7 MW in every premium arm, weakly
monotone in the premium. This is the prediction I am least confident in: the 3 GW/yr/ISO
retrofit cap and the ≥15 yr remaining-life screen may bind first, in which case capacity is
flat and the whole response is utilization — exactly the axis RESOLVE's P-E declined to
predict on and then found to be the interesting one (CF 59.3 % → 83.5 %).

**P-7 (saturation — mechanism transferred, levels not).** WS-2b measured the ERCOT ladder
saturating above ~$20/MWh on `iso_budget_exhausted`, the 12 GW/yr queue cap. That is an
**entry** saturation and CAISO's entry is masked anyway, so **I predict CAISO does NOT
saturate between P20 and P30** on CO2 or on `gas_cc_ccs` generation: the dispatch channel is
linear in the premium until the CCS fleet is fully utilized, and at REF's 2030 CF of 83.5 %
there is headroom left. `CES-P20` and `CES-P30` should differ by **more than 1 %** on 2030 CO2.

### 6.4 `CES-T80`, the cap, and the combined legs

**P-8 (`CES-T80` — regime measured, not assumed; gate G4).** `target_for_year` interpolates
linearly between the S12/S3 knots: **0.5500 / 0.5778 / 0.6056 / 0.6333 / 0.6611**. The row's
obligation is `target × Σ zone annual demand`; the credited side is
`Σ_g fuel_credit(g) × gen(g)` with the measured map {nuclear, wind, solar, hydro, geothermal,
offshore wind, hydrogen 1.0; **`gas_cc_ccs` 0.95**; everything else 0}. At **REF's own
generation**:

| year | target | obligation TWh | credited TWh | gap |
|---|---|---|---|---|
| 2026 | 0.5500 | 131.009 | 110.267 | **−20.742** |
| 2027 | 0.5778 | 142.088 | 110.267 | **−31.821** |
| 2028 | 0.6056 | 153.748 | 131.870 | **−21.878** |
| 2029 | 0.6333 | 166.014 | 161.834 | **−4.180** |
| 2030 | 0.6611 | 178.915 | 176.111 | **−2.804** |

So I predict the **escape regime in 2026–2028** (dual = ACP **$50.0000 exactly**, escape MWh =
the shortfall), and I **pre-declare 2029 and 2030 as OPEN**: the REF-baseline gaps are 2.5 %
and 1.6 % of the obligation, well within reach of the arm's own $50/MWh push on the CCS fleet,
so either regime is admissible there. **G4 gates the identity, not my guess** — dual = ACP
exactly ⟺ ESC > 0; dual ∈ (0, ACP) ⟺ ESC = 0 and the row binds; dual = 0 ⟺ slack. My own bet,
scored as written: **2029 and 2030 flip to interior** (the row is met), which would make CAISO
the first ISO in the campaign to *meet* the federal target in any year.

**P-9 (`ALL-CLEAN`'s target row).** At the DC-high posture the same arithmetic gives gaps of
−24.889 / −38.621 / −31.724 / **−15.221** / **−16.867** TWh — 5.4× and 6.0× the `CES-T80` gaps
at 2029/2030. I predict `ALL-CLEAN` is in the **escape regime in all five years**, dual =
**$50.0000 exactly**, i.e. the load case *undoes* the flip P-8 predicts.

**P-10 (`CAP-STATE-TIGHT` binds in ALL FIVE years).** 2026–2028 by the certain leg of §4.2.
For 2029–2030 I predict the cap binds too, because the arm removes a $36.78/$39.36 per tonne
adder worth ~$13.50/MWh to the CCS fleet's merit position; uncapped emissions should return
toward the ~30–31 Mt of 2026–2028, above the 27.5 / 26.5 Mt budget. **This is the prediction
most likely to miss**, and the direction of a miss is informative either way: if 2029–2030 come
back slack, the CCS fleet is retained by something other than the carbon price.
**P-11.** In every binding year `emissions_mt` equals the budget to 1e-6 and `co2_cap_price`
> 0. I predict the dual is **larger** than REF's exogenous adder in the same year (the quantity
instrument must price above the price instrument to force a strictly tighter outcome), and the
two are reported side by side — the price-vs-quantity comparison the case exists for (WS-1a
§4.2). **P-12.** `gas_cc_ccs` at 2030 is **lower** than REF's 64.988 TWh under the cap despite
the tighter constraint, because a mass cap prices *emissions* rather than subsidising *capture*
— if instead CCS rises, the cap's dual is doing the adder's work and that is the finding.

**P-13 (`CES-P20+VOL-HI`, gate G9).** The voluntary row is slack at the REF baseline by
46–55 TWh and the CES premium can only *raise* eligible generation, so I predict this leg is
**byte-identical to `CES-P20`** in all five years — CO2, price, clean share and every by-fuel
row to displayed precision — with the voluntary dual **0.0 in every year** and escape MWh
**0.0**. On D-6 this leg therefore has **no dispatch content** on CAISO, exactly as the memo
§4.3 says of a premium (a price, not a row): both nettings are reported and they **coincide**.
**P-14 (`ALL-CLEAN`).** Its voluntary row is likewise slack (dual 0.0, escape 0.0), so the
D-6 question that *does* have content — a CES **target** row and the voluntary row both
counting a clean MWh — is **not exercised on CAISO**. Both nettings are still reported under
G9 with the CES dual under each, and they coincide because `V` never binds. That null is the
deliverable, not a gap.

**P-15 (leakage, every leg).** `import_co2_mt_reported` stays **0.0000** in every leg and every
year. CAISO is the one ISO whose imports pay carbon (the CARB border adjustment charges
`0.428 × resolved price` on the import tranche VOM), so only the zero-EF tranches (PNW hydro,
midC, DSW solar) clear and the three carbon-bearing ones stay out of merit (WS-1b §4). The one
arm that could break this is **`CAP-STATE-TIGHT`, and I flag it before the solve**: it removes
the border charge along with the adder, so DSW_CCGT (0.37), DSW_CT (0.55) and WECC_scarcity
(0.428) become relatively cheaper and **imports are the one plausible leakage channel in the
campaign**. I predict `import_co2_mt_reported` **> 0** in at least one year of
`CAP-STATE-TIGHT` and 0.0000 everywhere else. Every CO2 number in the FINDING carries this
line beside it.

### 6.5 What I am NOT predicting, and why

Following RESOLVE's own lesson — its two magnitude bands missed in opposite directions because
they were sized from accounting and treated the priced dispatch response as a modifier — I make
**no level prediction** for CAISO's absolute CO2, price or deployment in any arm, and no band
at all for the `gas_cc_ccs` capacity response (P-6 is a sign, not a size). Where I give a band
(P-3) it is labelled as the guess most likely to miss.

---

## 7. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

A gate PASS means only *"the mechanism did what its own arithmetic says"*; it promotes nothing
and contributes to no determination (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1's carbon table, §4.2's budget, §3.1's volumes, §2's sixteen keys — all from the runner's own chain. **Already PASS, pre-solve**; each shard re-asserts its own two keys before solving |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries the adequacy state WS-5A measured: **I7 FAIL** (accredited firm short 2,941 / 4,669 / 3,710 MW in 2026–2028) and **I12 FAIL** (reserve margin 9.2 / 6.0 / 8.0 % against a [15 %, 30 %] band), backstop ladder 0 → 3,795.8 MW, **I3 PASS** (REF sheds nothing), and `rps_dual` at its $50 escape in all five years. **Consequence, declared now:** every leg's **deployment and capacity-mix LEVELS are disclosure-only in 2026–2028**, where the fleet is held together by a backstop ladder that is itself the artefact of an unmet requirement; and the **price levels in 2029–2030 are disclosure-only**, where scarcity hours appear (11 and 37 h ≥ $500, max $967–974). What stays campaign-grade in every year: **deltas vs REF**, the **dispatch/footprint orderings**, and the **duals**. A broken REF fails the premise; it never passes the delta |
| **G3** | **footprint confinement** | *CES* arms move the eligible/ineligible shares, the CES dual, and the classes the audited channels reach — `gas_cc_ccs`, `gas_cc`, wind, solar — with **nuclear and hydro generation Δ = 0.000 TWh** (§6.3 P-2, P-5) and `retire_mw` unchanged; *voluntary* arms move eligible-class rows, thermal rows and the escape column only; *cap* arms move fossil rows and imports only |
| **G4** | **`CES-T80` / `ALL-CLEAN` dual identity** | dual = ACP **$50.0000 exactly** ⟺ escape MWh > 0, and escape MWh = `target(y)·D − credited` to LP tolerance; dual ∈ (0, 50) ⟺ escape = 0 and the row binds; dual = 0 ⟺ slack. **The regime is NOT pre-chosen for 2029–2030** (§6.4 P-8) |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's FAIL `{I7, I12}` / WARN `{}`. A new FAIL outside the target mechanism kills the arm. **Not a STOP, pre-declared:** `I3` appearing in `ALL-CLEAN` (a load case — LOAD-HI already carries I3) and `I7`/`I12` moving with a changed retrofit or backstop set |
| **G6** | no unserved energy appears where REF has none | **REF sheds nothing (I3 PASS), so this binds hard here.** `unserved_mwh` must stay 0 in `CES-P10/P20/P30/P60`, `CES-T80`, `CES-P20+VOL-HI` and `CAP-STATE-TIGHT`, whose mechanisms cannot raise demand. It does **not** bind on `ALL-CLEAN`, which raises load by construction |
| **G7** | voluntary dual bounded | where the row binds: dual > 0 and **≤ $7.0/MWh** (the `high` ceiling — §3.3, correcting the charter's $4.5 mid literal); where it escapes: dual = **$7.0/MWh exactly** and escape MWh = the shortfall. On CAISO both surviving voluntary legs are predicted **slack** (dual 0.0), which the gate reads as the third admissible state |
| **G8** | **curtailment before thermal** | in the first binding year of a voluntary row: Δcurtailment of eligible resources < 0 and \|Δcurtailment\| ≥ \|Δ fossil generation\|. **Vacuous on CAISO if P-13/P-14 hold** (no binding year exists); reported as vacuous, never as passed |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as the headline, additional beside it, the CES dual under each — never one alone (ruling S11). The "additional" reading is `federal_credited − V ≥ target(y)·D` with implied escape `max(0, target·D + V − federal_credited)` priced at the ACP, computed at the report layer |
| **G10** | **`CAP-STATE-TIGHT` row identity** | in every binding year `emissions_mt` equals the resolved budget to **1e-6** and `co2_cap_price` > 0; in a slack year the dual is **0 exactly**. Any residual between `emissions_mt` and the capped set is named rather than absorbed |
| **G11** | **one instrument at a time** | `carbon_price_path: zero` resolves to the STATE adder alone under S2's floor, and with `state_carbon_pricing` true the ROW **replaces** that adder. **Already PASS, pre-solve** (§4.1): the arm's resolved carbon price is 0.0000 in all five years with `price_adder: null` and a `cap_spec`, against REF's `price_adder` 30.0242–39.3556 with `cap_spec: null` |
| **G12** | **`CAP-STATE-TIGHT` footprint as a carbon case** | fossil rows and imports only; the row's dual reported **beside** the adder path's exogenous price in the same year (§6.4 P-11) |
| **G-B1** | **the S15 mask is actually cleared at $60** | the entry fold's `attr` strictly exceeds REF's for at least one eligible tech-zone-year. **Already PASS, pre-solve** — §A |
| **G-B2** | **`CES-P60` footprint as a CES case** | as G3, plus: the entry attribute term is 60.0 where REF's is 50.0 |
| **G-B3** | no non-target load-bearing invariant flips PASS → FAIL vs REF on `CES-P60` | as G5 |

A gate **may kill an arm; it may never promote one**, and no gate reads a target residual.

---

## 8. Execution — this lane launches SHARDS and solves nothing itself (ruling S16)

**Shard width is derived, not chosen** (r#18 am.1): CAISO measures **4.33 min/solve-year** in
the Stage A-LOAD synthesis §8 and **5.60 min/solve-year** in RESOLVE's own post-D77 re-solve
(84.0 min / 15 solve-years) — at 5 solve-years per leg that is **21.7–28.0 min/leg**, so **2
legs per shard** against the 60-minute LP budget. **8 legs ⇒ 4 shards**, each ~43–56 min of LP.

| shard | cases | keys |
|---|---|---|
| **G1** | `CES-P10`, `CES-P20` | `f672e9134d51a475`, `46f5eb984e5a4614` |
| **G2** | `CES-P30`, `CES-T80` | `cedae86096ba6c3e`, `2ad09fb1eac689a9` |
| **G3** | `CES-P20+VOL-HI`, `ALL-CLEAN` | `130a2410b012cf93`, `e2820065dbdcb708` |
| **G4** | `CAP-STATE-TIGHT`, **`CES-P60`** | `2c5abed281bcee82`, `cb35acef1879e80e` |

`CES-P60` is confined to **one** shard because it is the only leg with a non-standard
invocation (§A.3). Driver, per leg, one at a time, years sequential, HEAD-guarded:

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/caiso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/CAISO/<CASE>
```

**Fixed setup cost, measured and passed on:** `data/clean` is derived and gitignored, so a
fresh container has none and `run_scenario_iso` hard-fails on `confirmed-retirements` before
any LP starts. `scripts/regenerate_clean.py` takes **~50 min** (RESOLVE §6). Each shard starts
it at session open and does its pre-solve checks while it runs — that is wall, not LP, and it
is why a shard's wall clock is ~1 h 45 against ~50 min of LP.

**Registration:** kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, one run id per
case, with **every invariant FAIL declared in `frontend/data/hindcast/invariant-failures.json`
in the same commit**. `scripts/check_forecast_invariants.py --sidecar-dir
frontend/data/hindcast` is EXIT 0 on `main` today and must stay so.

| case | label | run id |
|---|---|---|
| `CES-P10` | `scn-campaign-policy-2026-09-06-ces-p10` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p10` |
| `CES-P20` | `scn-campaign-policy-2026-09-06-ces-p20` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p20` |
| `CES-P30` | `scn-campaign-policy-2026-09-06-ces-p30` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p30` |
| `CES-P60` | `scn-campaign-policy-2026-09-06-ces-p60` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p60` |
| `CES-T80` | `scn-campaign-policy-2026-09-06-ces-t80` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-t80` |
| `CES-P20+VOL-HI` | `scn-campaign-policy-2026-09-06-ces-p20-vol-hi` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p20-vol-hi` |
| `ALL-CLEAN` | `scn-campaign-policy-2026-09-06-all-clean` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-all-clean` |
| `CAP-STATE-TIGHT` | `scn-campaign-policy-2026-09-06-cap-state-tight` | `caiso-2026-2030-scn-campaign-policy-2026-09-06-cap-state-tight` |

---

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **The campaign matrix carries no `CES-P60` case.** Ruling S15 orders the leg; the only
   region that could express it as a case is `configs/scenario_campaign_matrix.yaml`, which
   this lane may not edit and which is shared by all seven ISO lanes. The leg is therefore run
   through the **registered** `--set` channel (§A.3) and its summary's `case` field will read
   **`CES-P30`** with `set_overrides {"federal_ces_premium_usd_per_mwh": 60.0}`. **Declared
   here so no reader mistakes the provenance.** If the desk wants a clean `case` label across
   the six ISOs that will run this leg, one shared matrix row is the fix, and it belongs to
   whoever owns that file.
2. **`VOL-MID` *and* `VOL-HI` are inert on CAISO across the whole T1-F window, and so is the
   DC-high corner.** Under ruling S10's "credit all eligible units" set the voluntary axis has
   **no dispatch footprint anywhere on CAISO**. Card **D-3c**'s alternative leg
   (new-builds-only crediting) is what would change that, and CAISO — smallest DC block, large
   incumbent renewable fleet — is the sharpest case for that card the campaign has produced.
   Routed to D-3c beside the ERCOT lane's §9 item 4.
3. **Card D-6 is not exercised on CAISO.** Both nettings coincide because `V` never binds
   (§6.4 P-14). The campaign will need an ISO where `V > G` to give D-6 dispatch content; on
   present evidence that is ERCOT's `ALL-CLEAN` and nothing here.
4. **SCN-CAP §3's binding table is stale for CAISO post-D77** and, more importantly, was built
   on the wrong comparison (REF's CO2 rather than the arm's own uncontrolled emissions — §4.2).
   The same restatement plausibly applies to NYISO and NEISO, whose lanes read the same table.
5. **The charter's G7 ceiling literal is the mid cell ($4.5).** Corrected to $7.0 per arm in
   §3.3 — the same correction the ERCOT lane routed as its §9 item 2, still carried by the
   other charters.

---

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no new case beyond
  S15's, no solve outside §2's eight, never a year past 2030.** **DOF ledger: ZERO free
  parameters.** No `authorized_price_tuning` (rule 1's carve-out is a backcast offer-curve
  channel, untouched by a forecast lane).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the CAISO base YAML,
  everything under `src/`, `scripts/`, every committed bundle and sidecar, and every other
  ISO's files. `program-status.json`, `ff-verdicts.json` and the whole **backcast** namespace:
  untouched (§7.5 — this lane registers into the forecast namespace only).
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms and its control is a committed one.
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; any push touching one
  is fetch-back verified.
- **Rule 28(b) `[R-MECH-MATRIX]`:** CAISO's `federal_ces_target`, CES-premium,
  `carbon_price_path`, `voluntary_clean_demand` and mass-cap cells are stamped as the **LAST**
  commit after rebase — one appended line each, in CAISO's shard only.
- **Backcast byte-identity:** untouched by construction (forecast-mode only, `mode="forecast"`
  on every leg).
- **No CI workflow is created.** Every solve runs in a Claude session.

---

# ADDENDUM A — ruling S15, the bracketing leg (2026-09-07, pushed before the first solve)

## A.1 STEP 1 — the mask, measured per year from the committed REF

| year | REF `rps_dual` | the CES dual each ladder leg carries | mask binds? |
|---|---|---|---|
| 2026 | **50.0** | P10 → 10.0 · P20 → 20.0 · P30 → 30.0 · T80 → 50.0 (ACP, escape) | **YES** — 50.0 ≥ every one; T80 **ties exactly** |
| 2027 | **50.0** | idem | **YES** |
| 2028 | **50.0** | idem | **YES** |
| 2029 | **50.0** | idem | **YES** |
| 2030 | **50.0** | idem | **YES** |

The dual is `STATE_RPS_ACP["CAISO"]` exactly, in every year: CAISO's RPS floor rises 0.50 →
0.60 across the window while its RPS-eligible (wind + solar) output is ~31 % of load, so the
row is in its **escape** regime throughout. **The mask binds in 5 of 5 years, and CES-T80 is
the exact-tie case the addendum names.** STEP 2 fires.

## A.2 G-B1 — computed BEFORE the solve, and it CLEARS

`attr = max(effective_eac_price_for_tech(config, tech, year), rps_credit_for_zone(rps_dual,
zone), _clean_credit_for_tech(...))`, measured through the real functions at the pin:

| arm | `eac_leg` (wind / solar / geothermal) | RPS leg | **resulting `attr`** | vs REF |
|---|---|---|---|---|
| REF | 0.00 | 50.0 | **50.00** | — |
| `CES-P10` | 10.00 | 50.0 | **50.00** | tie — masked |
| `CES-P20` | 20.00 | 50.0 | **50.00** | tie — masked |
| `CES-P30` | 30.00 | 50.0 | **50.00** | tie — masked |
| `CES-T80` | 0.00 (its credit is the row dual = ACP 50 in escape) | 50.0 | **50.00** | tie — masked |
| **`CES-P60`** | **60.00** | 50.0 | **60.00** | **+10.00, STRICTLY GREATER** |

`tech_credit_fraction` is **1.00** for wind, solar, geothermal, offshore wind, nuclear and
hydro, so the premium passes through undiminished. **G-B1 PASSES for wind, solar and geothermal
in every zone and every one of the five years**, since the RPS dual is a flat 50.0 throughout.
The leg is not pointless and is solved.

**$60/MWh is the ONE COMMON LEVEL for every ISO** (r#18 §5.4), above the footprint's highest
published ACP ($50, CAISO and NEISO), identified from the published ACPs and **never** from a
residual. It is deliberately not per-ISO: a level chosen to clear CAISO's own $50 would be the
per-ISO fitting rule 25 `[R-ISO-SCOPE]` forbids. It is not re-levelled, not swept, and no second
bracketing leg is added.

## A.3 The leg — key, and its declared provenance deviation

**Key at THE PIN: `cb35acef1879e80e`.** There is no `CES-P60` case in
`configs/scenario_campaign_matrix.yaml` at the pin, and that file is outside this lane's
regions (§9 item 1). The leg is therefore expressed through the **registered** `--set` channel
(rule 24 `[R-REGISTRY]`; capx **D60-R4** repaired `apply_set_overrides` to use
`with_overrides`, so the override is recorded in the summary and in `run_config.json` and beats
an ISO default):

```
--case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0
```

Verified end-to-end through the driver's own `parse_set_overrides` → `apply_set_overrides` →
`resolve_policy_bundle` → `apply_iso_scenario_defaults` chain: resolved premium **60.0**, key
**`cb35acef1879e80e`**, and the resolved config differs from `CES-P30`'s in **exactly one
field**. **Declared, not hidden:** the leg's summary will record `case: "CES-P30"` with
`set_overrides {"federal_ces_premium_usd_per_mwh": 60.0}`; it is registered under the run id
`caiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p60` and written to
`results/scn-campaign-policy-2026-09-06/CAISO/CES-P60/`.

## A.4 What the leg is expected to do — pre-registered

**P-B1.** `CES-P60` is the **only** arm whose entry attribute term exceeds REF's, so it is the
only one in which a *renewable entry* response is attributable to the CES at all. I predict
`builds_renew_mw` **> REF's** in at least one year — most plausibly 2027 or 2028, where REF
builds **0.0 MW** and the backstop ladder is carrying the requirement gap instead.
**P-B2.** A leg that clears G-B1 and still shows **no** entry response is a **REPORTABLE
FINDING at full magnitude, not a gate failure** — it would distinguish "correctly masked" from
"the CES row does not reach entry at all", and only one of those is a model that works. I name
the two candidate explanations in advance so neither is invented afterwards: the ISO queue
budget / per-tech build-share cap binding first, or the entry screen's revenue estimate being
dominated by the energy term at CAISO's $56–72/MWh prices.
**P-B3.** Its dispatch response is `CES-P30`'s doubled: `gas_cc_ccs` mc falls **$57.00/MWh**,
so `CES-P60` carries the campaign's largest CCS-for-`gas_cc` substitution and the lowest CO2 of
any CAISO leg in 2028–2030.
