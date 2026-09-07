# PRECOMMIT — SCN-WS5A-POLICY-MISO: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-MISO (COORDINATOR under ruling **S16**) · **Model** Opus
(`claude-opus-5`, rule 27 `[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-miso-x4m3xp` · **Data profile** `miso` · **Campaign**
`scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` · **Charter**
SCN-DESK ledger §5.4 (charter **v6**) + the **S15** bracketing addendum + §5.5 am.1
(charter **v7**, the coordinator/shard split) · **Predecessors**
`PRECOMMIT-scn-ws5a-resolve-miso-2026-09-06.md` / `FINDING-scn-ws5a-resolve-miso-2026-09-06.md`
(THE PIN, the re-solved REF this lane differences against) and
`FINDING-scn-ws5a-load-miso-2026-09-06.md` (the REF's caveats).

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
config resolved at THE PIN through the runner's own chain, a committed artifact, or arithmetic
on the two. Nothing here is revised after a solve; §6's predictions are scored as written and a
miss is reported at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` §0 and met for MISO by
`FINDING-scn-ws5a-resolve-miso-2026-09-06.md` (3/3 legs, 5/5 gates each, zero STOPs). Verified
here: `git cat-file -t bdfb3095…` → `commit`; `origin/main` at PRECOMMIT time is `9bdd0709`,
**83 non-merge solve-path commits** past it (§5.2). **THE PIN IS NOT MOVED**, before or after
any solve. capx **D79**'s solve-surface fingerprint entered `cache_key()` *after* the pin
(`16210868`), so every key in §2 is a **pre-fingerprint key** and the pin records that.

## 0.1 Bottom line before any LP

1. **All twelve chartered cases SURVIVE phase 0 — MISO kills none of them**, and the S15
   addendum adds a thirteenth. `VOL-MID` — killed on ERCOT as slack in all five years — is
   **LIVE on MISO**, binding in 2029 (−0.70 TWh) and 2030 (−6.07 TWh). **13 legs, 65
   solve-years.**
2. **`CAP-STATE-TIGHT` is out of scope and proven LP-identical to REF** (precondition P5):
   `CAP_AND_TRADE_PROGRAMS.get("MISO")` is `None`, so `resolve_carbon_program` returns `None`
   in all five years for **both** REF and the cap case. It is not in this lane's chartered set
   and it is not solved (§4.2).
3. **The carbon axis is byte-identical to REF in 2026 in every carbon-bearing arm** — the RFF
   2026 knot is $0 in `low`/`mid`/`high` alike — and live 2027–2030. MISO has no state program,
   so under ruling **S2** the RFF path is the whole signal. Not a kill; a free per-year identity
   check, pre-registered as gate **G1a**.
4. **MISO is the thinnest mask in the footprint, and the mask still binds.** `rps_dual`
   = **30.0 in 5 of 5 years** in the committed REF, which is `STATE_RPS_ACP["MISO"]` exactly —
   the escape regime. `CES-P10`/`P20` sit **strictly below** it and `CES-P30` **ties it
   exactly**, so none of the three moves the entry attribute (§7). `CES-T80`'s ACP $50 clears
   it by $20 and `CES-P60` clears it by $30 — **G-B1 clears with a 2× margin** and the leg is
   added (§7.3).
5. **The voluntary axis on MISO is an ESCAPE-ONLY axis, and that is a pre-registered
   prediction, not a kill.** REF's `curtailment_twh` is **0.0000 in every year of every leg**,
   so a binding voluntary row has no curtailed eligible MWh to recover; and its dual, capped at
   $4.5/$7.0, is itself **below the $30 RPS dual** it must beat in the screens' `max()`, so it
   cannot reach deployment either. Predicted: dual = the arm's own ceiling exactly, escape MWh
   = `V − G`, and ~zero dispatch response (§6.4). Gate **G8** is therefore declared **vacuous
   on MISO** in advance rather than scored as a pass (§7).
6. **The control needs no control solve and no G-DRIFT argument.** This lane's arms solve at
   THE PIN and the REF it differences against was *itself solved at THE PIN* by
   SCN-WS5A-RESOLVE-MISO. Rule 29(b) form 4 is valid by construction — the control and the arms
   share a base commit, so the drift window between them is empty (§5.1).

---

## 1. Preconditions — verified

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE-MISO re-solved the three campaign legs at THE PIN, every gate PASS | **MET** | `FINDING-scn-ws5a-resolve-miso-2026-09-06.md` §4: G1–G5 PASS on REF / LOAD-HI / LOAD-HI-ORGANIC, zero STOPs; keys `f1b3caa22b3f14ff` / `9688b06c1b0a5a54` / `b87deb7735c242a0`. |
| **P2** | the re-solved REF is at `results/scn-campaign-load-2026-09-06-r2/MISO/REF/` | **MET** | The `-r2` tree holds `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC`; the un-suffixed `results/scn-campaign-load-2026-09-06/MISO/` holds **only** `bundle/` + `report/` — no `REF/` — i.e. the pre-fix bundles were deleted, exactly as RESOLVE-MISO §8 records. `run_config.json` reads `cache_key f1b3caa22b3f14ff`, `git.sha 95ad76d4`, `dirty false`; `95ad76d4` is RESOLVE-MISO's own PRECOMMIT commit, a descendant of THE PIN with a **zero solve-path diff** (that lane's G5(c) convention, §5.1 there). Sidecar `frontend/data/hindcast/miso-2026-2030-scn-campaign-load-2026-09-06-ref.json` unchanged. **REF IS NEVER RE-SOLVED.** |
| **P3** | `CARB-*` read `carbon_price_path` low/mid/high; `ALL-CLEAN`'s carbon component `mid` | **MET at the pin** | `git show bdfb3095:configs/scenario_campaign_matrix.yaml`: `CARB-LO: low` (l.131), `CARB-MID: mid` (l.133), `CARB-HI: high` (l.135), `CARB-MID+LOAD-HI: mid` (l.362), `ALL-CLEAN: mid` (l.402). Resolved $/t in §4.1. No regression. |
| **P4** | rule 12 concurrency | **MET by construction under S16** | ≤ 2 legs per shard, **one solve at a time inside a shard**, years always sequential. Shards are separate containers, so the per-container memory cap does not compose. MISO peaks at **9.98 GB on a 15 GB box** (RESOLVE-MISO §6) — **never two MISO solves in one container** (§8). |
| **P5** | `CAP-STATE-TIGHT` is out of scope for MISO | **MET, and proven** | `CAP_AND_TRADE_PROGRAMS` keys are `{CAISO, NEISO, NYISO, PJM}` — MISO absent; `STATE_CARBON_PRICE_BY_ISO` keys are `{CAISO, NEISO, NYISO}` — MISO absent. `resolve_carbon_program(cfg, y)` is `None` for **both** REF and `CAP-STATE-TIGHT` in all five years (§4.2). Not solved. |

## 1.1 The constant families this lane consumes

All read at **THE PIN** `bdfb3095`, verbatim, through the pin worktree:

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `config/fuel_trajectories.py` (re-exported `policy/carbon.py`) | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | `CAISO`, `NYISO`, `NEISO` — **MISO absent** |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NEISO`, `NYISO`, `PJM` — **MISO absent** |
| `STATE_RPS_ACP` | `config/capacity_market.py` | CAISO 50.0, NYISO 40.0, NEISO 50.0, PJM 45.0, **MISO 30.0** — the footprint's lowest |
| `STATE_RPS_FLOORS["MISO"]` | `config/capacity_market.py` | {2026: 0.11, 2030: 0.16, 2040: 0.20, 2045: 0.20} |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; mid {2023: 0.08}; high {2023: 0.08} |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; **mid {2026: 0.5}**; high {2026: 1.0} |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5**; **high 7.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built; **MISO carries only wind + solar** in every committed leg-year |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["MISO"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = **1.0** (measured, §3.1) |
| `DATACENTER_ADDITIONS_MW["MISO"]` | `config/constants.py` | mid {2026: 1,154; 2030: **20,000**; 2046: 33,154} MW; high {2026: 1,154; 2030: **27,067**; 2046: 45,154} MW |
| `DEMAND_GROWTH_RATES["MISO"]` | `config/constants.py` | mid {near 0.054816, long 0.014850}; high {near 0.082546, long 0.022363} |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}; ACP $50/MWh |
| S15 bracketing level | ledger §5.4 addendum | premium **60.0** $/MWh — one common level for every ISO, identified from the footprint's published ACPs, never from a residual |

**Zero DOF.** No free parameter is introduced by this lane; no default is moved; no
`ScenarioConfig` field is added. No `authorized_price_tuning` block — rule 1's carve-out is a
**backcast offer-curve** channel and this is a forecast campaign.

---

## 2. The case set at THE PIN — resolved fields and cache keys

Resolved exactly as `runner.run_scenario_iso` does (`runner.py:1384–1423`):
`matrix_configs(base, sweep)` → `resolve_policy_bundle` → `set_caiso_fsno_partition(False)` →
`apply_iso_scenario_defaults(cfg, "MISO")` → `config.cache_key()`. Base:
`configs/scenarios/miso_scenario_base_2026_2030.yaml` (byte-identical pin → HEAD, as are
`configs/scenario_campaign_matrix.yaml` and `scripts/run_ces_leg.py`).

**Chain validation — the three MISO rows RESOLVE-MISO published, reproduced independently
here:** `REF f1b3caa22b3f14ff`, `LOAD-HI 9688b06c1b0a5a54`, `LOAD-HI-ORGANIC b87deb7735c242a0`
— identical to that lane's §5 table, and identical to the `cache_key` written inside each
committed `run_config.json`. Both columns reproduce, so the resolve chain used below is the one
the solve will use.

| case | key at THE PIN | override vs REF | verdict |
|---|---|---|---|
| *REF (control, not solved)* | `f1b3caa22b3f14ff` | — | **REUSED** (committed at the pin; §5.1) |
| `CARB-LO` | `1c815555d55e5db2` | `carbon_price_path: low` | **SOLVE** |
| `CARB-MID` | `27fb6e72c0ad31ae` | `carbon_price_path: mid` | **SOLVE** |
| `CARB-HI` | `40bc61fac2b5271d` | `carbon_price_path: high` | **SOLVE** |
| `CES-P10` | `e4ba286178e0d499` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `472af7fd5ba90f99` | premium 20.0 | **SOLVE** |
| `CES-P30` | `3a4b528c75d7fd6d` | premium 30.0 | **SOLVE** |
| `CES-T80` | `82c916d847270ebf` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CARB-MID+LOAD-HI` | `e644893331d7708f` | carbon mid + growth high + DC high | **SOLVE** |
| `VOL-MID` | `dc8ca3580e277d72` | `voluntary_clean_demand_path: mid` | **SOLVE** — *not killed; binds 2029–30 (§3.2)* |
| `VOL-HI` | `7e1a2a2145711bab` | `voluntary_clean_demand_path: high` | **SOLVE** |
| `CES-P20+VOL-HI` | `ed42e5d7d1d95d3e` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `00edacf5f50c88fc` | carbon mid + CES target + ACP 50 + voluntary high + growth high + DC high | **SOLVE** |
| **`CES-P60`** (S15) | **`e5fb002f78c0c681`** | `--case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0` | **SOLVE** — §7.3 |
| *`LOAD-HI` (pairing base, not solved)* | `9688b06c1b0a5a54` | growth high + DC high | **REUSED** — the committed leg at the pin |
| *`CAP-STATE-TIGHT`* | `32584ac5c0133d89` | cap fields | **OUT OF SCOPE / KILLED — §4.2** |

**Every case keys distinctly.** No MISO bundle has ever occupied any of the thirteen SOLVE
keys — `results/MISO/` does not exist in any lane container at PRECOMMIT time — so a
pre-existing key directory in a shard is a cache hit and a **STOP**, never a shortcut.

**`CES-P60` carries no new YAML case, deliberately.** The pin's matrix has no `CES-P60` row and
the pin is not moved, so the leg is expressed through the **registered** `--set` channel
(`run_full_horizon.apply_set_overrides`, which routes through `with_overrides` and records the
override in `run_config.json` and the summary — rule 24 `[R-REGISTRY]`: a `--set` naming a real
`ScenarioConfig` field is a registered channel, an unknown name is a hard error). One
consequence is disclosed rather than papered over: the leg's summary records `case:
"CES-P30"` with `set_overrides {"federal_ces_premium_usd_per_mwh": 60.0}`, because
`_leg_meta` stamps the `--case` argument. Its shard therefore **skips** the group
`--assemble` / `report_scenario_deltas` step, whose `members[case] = key` map would collide
with the real `CES-P30` leg; the parent reads its absolutes from `full_horizon_summary.json`
and its duals from `duals.json` directly.

**13 legs to solve, 65 solve-years.**

---

## 3. Phase 0 — the voluntary row, per year, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed — the
runner's own chain `load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`
— never by re-deriving the memo's arithmetic. Zones: the six MISO zones
`[MISO-West, MISO-Plains, MISO-Illinois, MISO-Indiana, MISO-East, MISO-South]`; no import node.
Instrument: `docs/handoffs/scn-ws5a-policy-miso/phase0-miso-2026-09-07.py` →
`…-2026-09-07.json`, both committed with this document.

### 3.1 The resolved volumes (TWh)

Measured `s_base` = 0.08, `w_ISO` = **1.0**, `f_commit` = 0.5 (mid) / 1.0 (high) in every year.

| posture | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| **REF / all DC-mid cases** | `E_total` | 717.24 | 756.56 | 798.03 | 841.78 | 887.92 |
| | `E_DC` | 8.59 | 43.67 | 78.76 | 113.84 | 148.92 |
| | `E_nonDC` | 708.65 | 712.88 | 719.27 | 727.94 | 739.00 |
| | **V (`VOL-MID`)** | **60.99** | **78.87** | **96.92** | **115.15** | **133.58** |
| | **V (`VOL-HI`, `CES-P20+VOL-HI`)** | **65.28** | **100.71** | **136.30** | **172.07** | **208.04** |
| **`ALL-CLEAN` (growth high + DC high)** | `E_total` | 755.45 | 817.81 | 885.32 | 958.39 | 1,037.51 |
| | `E_DC` | 8.59 | 56.83 | 105.07 | 153.30 | 201.54 |
| | **V** | **68.34** | **117.71** | **167.49** | **217.71** | **268.42** |

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — and why nothing is killed

Eligible generation `G` = wind + solar **as dispatched in the paired committed baseline**
(MISO carries no offshore wind and no geothermal in any leg-year; the fuel keys present in
every committed leg are exactly `biomass, coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro,
nuclear, oil, solar, wind`). `G_REF` from `results/scn-campaign-load-2026-09-06-r2/MISO/REF/`;
`G_LOAD-HI` from that leg, the DC-high/growth-high baseline `ALL-CLEAN` is paired to.

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` | 103.5691 | 103.5691 | 103.5691 | 114.4560 | 127.5060 |
| `G_LOAD-HI` | 103.5691 | 103.5691 | 103.5691 | 114.4560 | 127.5060 |

*(The two are identical to 4 dp in every year — MISO's VRE fleet and its dispatch are
unchanged by the load axis, because REF curtails nothing and the load arms commission the same
VRE. That is a measured fact of the committed legs, not an assumption.)*

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | 61.0 < 103.6 (**+42.58**) | 78.9 < 103.6 (**+24.70**) | 96.9 < 103.6 (**+6.65**) | **115.2 > 114.5 (−0.70)** | **133.6 > 127.5 (−6.07)** | slack 2026–28, **binds 2029–30** |
| **`VOL-HI`** vs `G_REF` | 65.3 < 103.6 (+38.28) | 100.7 < 103.6 (+2.86) | **136.3 > 103.6 (−32.73)** | **172.1 > 114.5 (−57.62)** | **208.0 > 127.5 (−80.53)** | slack 2026–27, **binds 2028–30** |
| **`CES-P20+VOL-HI`** | identical `V` to `VOL-HI` | | | | | slack 2026–27, **binds 2028–30** |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | 68.3 < 103.6 (+35.23) | **117.7 > 103.6 (−14.14)** | **167.5 > 103.6 (−63.92)** | **217.7 > 114.5 (−103.26)** | **268.4 > 127.5 (−140.91)** | slack 2026, **binds 2027–30** |

**NOTHING IS KILLED, and the MISO/ERCOT divergence is the substance.** On ERCOT `VOL-MID` was
slack in all five years by ≥ 36 TWh and was killed on a proven identity
(`PRECOMMIT-scn-ws5a-policy-ercot` §3.2). On MISO the same arm **crosses**: its 2028 margin is
+6.65 TWh (6.4 % of `G`) and it goes negative in 2029 by **0.70 TWh** — 0.6 % of `G`, the
thinnest crossing anywhere in the campaign. The driver is arithmetic, not judgement: MISO's
eligible fleet is small relative to its load (`G/E_total` 14.4 % in 2026 falling to 14.4 % in
2030) where ERCOT's is 33 %, so a national 8 % baseline share plus half a data-centre block
outgrows it. `VOL-MID` is therefore **solved**, and 2026–2028 are its own pre-registered
byte-identity years (rule 29's inert-year clause applies to those years, not to the arm).

**What "binds" does and does not imply here — stated before the solve.** The row is
`Σ W + Σ S + Σ ESC ≥ V` with the escape priced at the arm's WTP ceiling. Where `V > G` the LP
has exactly three responses: (a) recover curtailed eligible MWh — **unavailable, REF's
`curtailment_twh` is 0.0000 in every year of every committed leg**; (b) build more eligible
capacity through the dual in the *next* year's entry screen — **unavailable, the dual is capped
at $4.5/$7.0 and the entry fold takes `max(EAC, RPS, clean)` against a $30 RPS dual (§7)**;
(c) buy the escape. So (c) is the only open channel, and §6.4 pre-registers the consequence.

### 3.3 The WTP ceiling — bounded per arm, not per lane

`voluntary_wtp_ceiling_usd_per_mwh` resolves `None` on every case, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. The charter's G7 literal names **$4.5/MWh**, which
is the **mid** cell (ruling S9). MISO runs **both**: `VOL-MID` is bounded at **$4.5**, and
`VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN` at **$7.0**. G7 is bounded **per arm, from that
arm's own resolved path** — the ERCOT lane's §3.3 correction applies here with the extra clause
that MISO, unlike ERCOT, actually exercises the $4.5 cell.

---

## 4. Phase 0 — the carbon axis and the cap row

### 4.1 Resolved carbon $/tCO2 per year (`policy.carbon.resolve_carbon_price`)

MISO has **no state carbon program**, so ruling S2's `max(RFF path, program trajectory)` reduces
to the path alone — MISO's `CARB-*` legs are LIVE, unlike CAISO/NYISO/NEISO's.

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `REF` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `CARB-LO` | **0.0000** | 2.0000 | 4.0000 | 6.0000 | 8.0000 |
| `CARB-MID` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| `CARB-HI` | **0.0000** | 7.5000 | 15.0000 | 22.5000 | 30.0000 |
| `CARB-MID+LOAD-HI` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| `ALL-CLEAN` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| every CES-only / VOL-only leg, and `CAP-STATE-TIGHT` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

**Reproduces the campaign YAML's declared ERCOT/PJM/MISO table to the cent** — gate **G1** on
the carbon axis, passed before any LP. The 2026 knot is $0 in every path, so **2026 is
byte-identical to REF in all five carbon-bearing arms** (gate **G1a**).

### 4.2 `CAP-STATE-TIGHT` is proven LP-identical to REF on MISO (P5)

`resolve_carbon_program(config, year)` returns **`None`** in every year 2026–2030 for BOTH
`REF` and `CAP-STATE-TIGHT`. The mechanism is the first statement of
`policy/cap_and_trade.py::resolve_carbon_program`: `CAP_AND_TRADE_PROGRAMS.get("MISO")` is
`None` → early return, before `mass_cap_enabled` is consulted. So `mass_cap_enabled: true` and
the whole `mass_cap_tons_by_year` schedule (which names NYISO/NEISO/CAISO only) reach no LP
input. The cache key moves (`32584ac5c0133d89` ≠ `f1b3caa22b3f14ff`) because the fields are
set; **no LP input differs**. Confirmed and **not solved** — the case was never in MISO's
chartered set.

---

## 5. The control (rule 29(b)) — form 4 is valid *by construction*

### 5.1 The control and the arms share THE PIN, so the drift window between them is empty

Rule 29(b) form 4 differences an arm against the incumbent's **committed** numbers, and the
question it can fail on is "did the solve path move between the control's `git_sha` and the
arm's?". **Here it cannot**: SCN-WS5A-RESOLVE-MISO re-solved REF *at THE PIN* (`git.sha
95ad76d4`, a descendant of `bdfb3095` whose `git diff … -- src/market_sim scripts configs
data/raw` is **EMPTY**, that lane's §5.1), and this lane's thirteen arms solve at THE PIN too.
No G-DRIFT argument is needed to license the control, and **no control solve is earned**. This
is stronger than ERCOT's position, whose control was solved at `1cc45bb2` and needed the
inherited audit to bridge one pin to another.

The inherited RESOLVE audit is nonetheless recorded, because it is what makes the REF's
*numbers* the post-repair ones: `1cc45bb2..bdfb3095` = 41 files, +5,362 / −433; of its four LIVE
mechanisms, **capx D77 and D65-B are LIVE for MISO** (they are the repair, and they moved the
2030 REF CO2 412.6343 → 410.2013 Mt), while **D67-ARM, D78 and D81 are INERT** — MISO's
`capacity_market_supply_clearing_by_iso` resolves `None`, which is the second arming condition
of all three (RESOLVE-MISO §1, asserted by `tests/unit/model/test_capacity.py:7250`).

### 5.2 `bdfb3095 .. origin/main` (`9bdd0709`) — for the record; I solve at THE PIN regardless

**83 non-merge commits, 126 files, +20,048 / −256** over `src/market_sim scripts configs`. The
window's whole content is other lanes' work — the SPP seventh-ISO registration (SPP-14/20/21/
31/32/33/53), backcast calibration lanes (miso-232/233/234/235, nyiso-208/209/210/211,
ercot-251/252/253, caiso-260/261, neiso-107), and the capx D75-R/D76/D78 arms. The audit that
matters for a MISO **forecast** leg is the field census, and it is exhaustive:

**Exactly four `ScenarioConfig` fields were added in the window, all `= False`:**
`gas_offer_margin_anchor_vintage`, `pjm_interface_feed_admissibility_gate`,
`miso_seam_neighbour_hourly_ladder`, `miso_seam_neighbour_hourly_spp`. The two MISO ones are
backcast seam fields, default-off, and named by **no** case in the campaign matrix and by
**no** entry in MISO's `default_scenario_overrides` — which the window does not touch for MISO
at all (`git diff … -- src/market_sim/config/iso_configs.py` changes MISO only in comments and
in the ISO-list prose that now says "SPP"). **No LIVE hunk for a MISO forecast leg ⇒ no control
solve is earned on this window either**, and it changes nothing about what is solved: **the pin
is not moved.**

---

## 6. What each surviving leg is expected to do — pre-registered

Sources, all measured before this lane and none of them a residual: **WS-1b-r2** (the MISO 2027
carbon pair, `docs/handoffs/scn-ws1b/score-MISO-2027.json`), **WS-2a** (the CES target row's
escape regime), **WS-3b §6** (the voluntary row's arithmetic), **WS-4c** (the MISO load
response), and the committed MISO REF itself.

### 6.1 The REF this lane differences against (the levels every prediction is relative to)

| year | `co2_mt` | `lw_price` | `clean_share` | `unserved_mwh` | `curtailment_twh` | `rps_dual` | `gas_cc_ccs` TWh |
|---|---|---|---|---|---|---|---|
| 2026 | 368.5353 | 44.599 | 0.2828 | 111,553.23 | 0.0 | 30.0 | — |
| 2027 | 371.1727 | 53.787 | 0.2679 | 228,902.15 | 0.0 | 30.0 | — |
| 2028 | 381.2997 | 91.967 | 0.2563 | 698,735.08 | 0.0 | 30.0 | 2.1476 |
| 2029 | 387.9419 | 90.727 | 0.2579 | 506,183.48 | 0.0 | 30.0 | 4.1227 |
| 2030 | 410.2013 | 206.363 | 0.2545 | 2,824,183.49 | 0.0 | 30.0 | 4.6908 |

`import_co2_mt_reported` = **0.0000** in every year (reported beside every CO2 number per
G-E3, never inside it). Invariant FAIL set **{I3, I7, I12}**, WARN **{I14}**.

### 6.2 Carbon — sign, ordering, magnitude

**P-1.** 2026 is **bit-identical to REF** in all five carbon-bearing arms — **`co2_mt`
368.5353, `lw_price` 44.599** — and the full `generation_by_fuel_mwh` matches to 1e-6
(gate G1a). *(`CARB-MID+LOAD-HI` and `ALL-CLEAN` are excepted: their load half moves
2026 too, so for them G1a asserts identity to `LOAD-HI`'s 2026, `co2_mt` 387.0428 /
`lw_price` 59.632, not to REF's.)*

**P-2.** CO2 falls and `lw_price` rises monotonically REF → LO → MID → HI in each year
2027–2030; 2026 flat.

**P-3 — the transferable magnitude, and why it is a band and not an identity.** WS-1b-r2
measured MISO's 2027 response to exactly `carbon_price_path: mid` (+$3.7500/t): **ΔCO2
−6.6414 Mt (−1.79 %)**, Δ`lw_price` **+2.411 $/MWh**, implied Δp/Δcarbon **0.6429 t/MWh**,
`unserved_mwh` unchanged, 8/8 gates PASS. **It is NOT an identity for this lane** — that
probe's REF 2027 is 370.4751 Mt against my campaign REF's 371.1727 Mt (a different key,
`1b9e15c5a85f6302`, at a pre-pin HEAD), so the *level* does not transfer even though the year
does. I therefore predict `CARB-MID` 2027 **ΔCO2 in [−8.0, −5.5] Mt** and Δ`lw_price` in
[+1.8, +3.3] $/MWh, centred on the measured response. This is the prediction most likely to
miss and it is stated with its own reason.

**P-4.** Sub-linearity across the ladder at 2027: `CARB-LO` (+$2.00, 0.53×) **ΔCO2 in
[−4.5, −2.5] Mt**; `CARB-HI` (+$7.50, 2×) **ΔCO2 in [−15, −10] Mt** — more than 2× MID's, not
less, because MISO's coal→gas-CC spread is narrow and a wide band of coal crosses between $3.75
and $7.50. *(This is the opposite curvature to ERCOT's P-5 and is asserted deliberately.)*

**P-5 (gate G3).** The mechanism is a coal→gas-CC merit-order substitution at ≈1:1 energy, with
**every zero-carbon class moving 0.0000 TWh** and `emissions_by_fuel_mt["import"]` 0.0000 —
WS-1b's G5/G6 held on MISO without qualification.

**P-6.** `gas_cc_ccs` **grows** with the carbon price from 2028: REF's screen already converts
618.1 MW by 2029 at carbon 0, and a positive carbon price raises the retrofit's incremental
uplift, so I expect `CARB-HI` 2030 `gas_cc_ccs` **strictly above** REF's 4.6908 TWh. MISO's
cohort is **two physical plants** (p7985 MISO-Plains, p1007 MISO-Indiana; RESOLVE-MISO §7 item
4), so this channel can move **discontinuously** — a step, not a curve, and a flat reading is
reported rather than explained away.

### 6.3 CES — the ladder is expected to be ENTRY-MASKED and RETIREMENT-LIVE

**P-7.** `CES-P10`/`P20`/`P30` show **no new VRE entry response** relative to REF: at entry the
fold is `max(effective_eac_price_for_tech, rps_credit_for_zone, clean_credit)` with **no fuel
gate on the RPS leg**, MISO's legacy EAC is **0.0 for every tech**, and both attribute rows
escape at $30 — so 10 and 20 are strictly dominated and 30 **ties exactly** (§7.1). Predicted
`builds_renew_mw` identical to REF's (0 / 0 / 0 / 5,650.2 / 4,349.8 MW) in all three arms.

**P-8.** They are **not** byte-identical to REF, and the channel is the **retirement** screen:
there `rps_for_unit` is fuel-gated to `{wind, solar}` and `clean_for_unit` is fuel- **and**
zone-resolved to MISO's two state clean regions (MN, MI — WS-2a §80), so a **nuclear or hydro
unit outside MN/MI, and every `gas_cc_ccs` unit, has zero attribute alternative** and the CES
premium reaches its going-forward margin unopposed at 10 / 20 / 28.5–30 $/MWh. Predicted: any
divergence from REF appears first in `retire_mw` and in the `gas_cc_ccs` cohort, not in
`builds_renew_mw`.

**P-9.** `CES-T80`: the target is 0.55 in 2026 and MISO's own credited share is far below it in
every year — REF's `clean_share` is **0.2828 / 0.2679 / 0.2563 / 0.2579 / 0.2545**, i.e.
*falling*, because load outgrows clean entry. The gap therefore **widens**, and the federal row
is in the **escape regime in every year**: dual = ACP **$50.0000/MWh exactly**, escape MWh =
`target(y)·D − credited`. That is gate **G4**, and it is the same regime WS-2a measured on its
NEISO T0 pair. Because $50 > $30 it is the **first CES case that is not entry-masked**, so
`CES-T80` — not the premium ladder — is where a MISO CES deployment response should appear.

### 6.4 Voluntary — escape-only, and stated as such in advance

**P-10 (gate G7).** `VOL-MID`: dual **0.0** in 2026–2028 (slack), then **$4.5000/MWh exactly**
in 2029 and 2030 with escape MWh ≈ **0.70 and 6.07 TWh**. `VOL-HI` and `CES-P20+VOL-HI`: dual
**0.0** in 2026–2027, then **$7.0000/MWh exactly** in 2028–2030 with escape ≈ **32.73 / 57.62 /
80.53 TWh**. `ALL-CLEAN`: dual 0.0 in 2026, then **$7.0000/MWh exactly** in 2027–2030 with
escape ≈ **14.14 / 63.92 / 103.26 / 140.91 TWh**.

**P-11.** **CO2 and `lw_price` in `VOL-MID` / `VOL-HI` / `CES-P20+VOL-HI` are unchanged from
REF to displayed precision in every year** — |ΔCO2| < 0.5 Mt, |Δ`lw_price`| < 0.5 $/MWh. The
argument, pre-registered: with zero curtailment there is no eligible MWh to recover, the escape
column absorbs the whole shortfall at a price that never reaches the screens' `max()` against a
$30 RPS dual, and the row's only other coupling to dispatch is through an objective term the
escape variable satisfies at its own bound. **If a voluntary arm moves CO2 materially, that is
a finding about the row's coupling and is reported at full magnitude, not smoothed.**

**P-12 (gate G8 — declared vacuous, in advance).** The G8 ordering "curtailment of eligible
resources falls before thermal dispatch changes" **cannot be exercised on MISO**: REF's
`curtailment_twh` is 0.0000 in every year, so Δcurtailment is bounded below by 0 and the
antecedent is empty. G8 is scored **N/A — vacuous, REF has no curtailment to recover**, and the
substantive test it stands for is carried instead by P-11 (no thermal response either).

**P-13.** `ALL-CLEAN` is the one arm where owner card **D-6** has dispatch content — a federal
CES **target** row and the voluntary row both count a clean MWh. Both nettings are reported
side by side (gate **G9**): **counts-toward as the headline** (as built: two independent rows,
FFR-6B §6.4), **additional** beside it, computed at the report layer as
`federal_credited − V ≥ target(y)·D` with implied escape `max(0, target·D + V − credited)`
priced at the ACP, with the CES dual under each. Neither is asserted as the answer; D-6 is OPEN.

### 6.5 The combined and load-paired legs

**P-14.** `CARB-MID+LOAD-HI` at 2030: `LOAD-HI`'s CO2 is 482.6176 Mt against REF's 410.2013
(ΔCO2 +72.4163). Adding carbon `mid` should *reduce* that, and I predict the arm lands in
**[476, 481] Mt** at 2030 — i.e. carbon at $15/t claws back **2–7 Mt** of a 72 Mt load
increase, so the honest headline is that **a mid carbon price does not hold MISO's CO2 flat
under data-centre growth**. `unserved_mwh` should not fall below `LOAD-HI`'s.

**P-15.** `CES-P20+VOL-HI`: the CES **premium** ($20) exceeds the voluntary ceiling ($7) in
every year, and *both* sit under the $30 RPS dual, so I expect the arm to be
**indistinguishable from `VOL-HI`** on dispatch and entry, with the CES premium's only content
on the retirement side (P-8). D-6 has no dispatch content under a premium.

---

## 7. S15 — the mask, measured, and the bracketing leg

### 7.1 STEP 1, zero LP: the two numbers per year

From the committed REF bundle at THE PIN (`full_horizon_summary.json` `trajectory[].rps_dual`):

| year | REF `rps_dual` ($/MWh) | `CES-P10` | `CES-P20` | `CES-P30` | mask binds? |
|---|---|---|---|---|---|
| 2026 | **30.0** | 10.0 | 20.0 | 30.0 | **YES** — 30 ≥ 10, 30 ≥ 20, 30 = 30 |
| 2027 | **30.0** | 10.0 | 20.0 | 30.0 | **YES** |
| 2028 | **30.0** | 10.0 | 20.0 | 30.0 | **YES** |
| 2029 | **30.0** | 10.0 | 20.0 | 30.0 | **YES** |
| 2030 | **30.0** | 10.0 | 20.0 | 30.0 | **YES** |

**The mask binds in 5 of 5 years, and 30.0 is not a coincidence — it is
`STATE_RPS_ACP["MISO"]` exactly**, i.e. at least one MISO compliance region is at its
alternative-compliance ceiling (the escape regime) in every year of the window. `CES-P10` and
`CES-P20` are strictly dominated; **`CES-P30` ties to the cent**, and a tie leaves `max()`
unmoved, so all three are entry-masked. MISO is the thinnest mask in the footprint ($30 vs
NYISO 40 / PJM 45 / CAISO 50 / NEISO 50) and it is still not thin enough for the committed
ladder to clear it.

**Two limits stated rather than glossed.** (a) The ledger scalar is the **MAX** region dual
under MISO's K-row grain (`runner.py:4919`: "under the K-row grain the ledger scalar is the MAX
region dual"), while the screens index `rps_credit_for_zone` **per zone**. The per-region
vector lives on `DispatchResult.rps_region_duals` and is **not** in the committed slim
artifacts, so whether a *lower*-dual MISO region exists — in which which case the premium would
be unmasked there — is not determinable at zero LP. It is exactly what the `CES-P*` solves will
reveal, and §6.3's P-7 is written so that either outcome is legible. (b) The clean-tier family
escapes at the **same** $30 (`policy/clean_tiers.py:139` reads `STATE_RPS_ACP["MISO"]`), so the
mask's ceiling is $30 on both attribute rows, not just the RPS one.

### 7.2 Why the CES legs are still solved and are not killable

Not a defect and no code changes: this is rule 19 `[R-ONE-MECH]`'s `max()` attribute doctrine
working as designed — attribute revenue is a max, never a sum. The **retirement** screen's RPS
leg *is* fuel-gated (`retirements.py:144` `_RPS_ELIGIBLE_FUELS = {"wind", "solar"}`, applied at
`:3509–3516`), and its clean leg is fuel- and zone-resolved, so the premium is **unmasked** for
nuclear and hydro outside MN/MI and for every `gas_cc_ccs` unit. The CES legs are therefore not
byte-identical to REF, are not killable at phase 0, and solve as chartered.

### 7.3 STEP 2 — `CES-P60`, and the G-B1 arithmetic done before the solve

`CES-P60` = `federal_ces_enabled: true`, `federal_ces_premium_usd_per_mwh: 60.0`, nothing else.
$60 is **one common level for every ISO**, above the footprint's highest published ACP ($50),
identified from published ACPs and **never from a residual**; it is deliberately not per-ISO —
a level picked to clear MISO's own $30 would be the per-ISO fitting rule 25 `[R-ISO-SCOPE]`
forbids and would make MISO incomparable to the other five. It is not re-levelled, not tuned,
and no second bracketing leg is added.

**Gate G-B1, computed at THE PIN before solving:**

| tech | `effective_eac_price_for_tech` at $60 | REF's attr upper bound | strictly exceeds? |
|---|---|---|---|
| wind / solar / nuclear / geothermal / offshore wind | **60.00** | ≤ 30.00 | **YES, by $30.00** |
| `gas_cc_ccs` (credit fraction 0.95) | **57.00** | ≤ 30.00 | **YES, by $27.00** |

The upper bound is exact, not assumed: MISO's legacy EAC is `0.0` for every tech
(`get_eac_price_for_new_entry`), the RPS row escapes at `STATE_RPS_ACP["MISO"] = 30.0`
(`policy/rps.py:123`) and the state clean-tier family escapes at the same 30.0
(`policy/clean_tiers.py:139`), so `attr_REF = max(0, ≤30, ≤30) ≤ 30.0` for **every** eligible
tech in **every** zone in **every** year. **G-B1 CLEARS with a 2× margin.** The leg is added.

Key `e5fb002f78c0c681`. **A leg that clears G-B1 and still shows no entry response is a
REPORTABLE FINDING, not a gate failure** — it is what distinguishes "correctly masked" from
"the CES row does not reach entry at all", and only one of those is a model that works.

---

## 8. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1's carbon table = the YAML's declared ERCOT/PJM/MISO table; §3.1's volumes from the runner's own demand chain; §2's keys reproduced against RESOLVE-MISO's three. **Already PASS, pre-solve.** |
| **G1a** | every carbon-bearing arm's **2026** is bit-identical to its own load baseline | `CARB-{LO,MID,HI}` vs REF (`co2_mt` 368.5353, `lw_price` 44.599); `CARB-MID+LOAD-HI` and `ALL-CLEAN` vs `LOAD-HI` (387.0428 / 59.632); full `generation_by_fuel_mwh` to 1e-6 |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries the adequacy state WS-5A measured: FAIL set exactly `{I3, I7, I12}`, WARN `{I14}`; `unserved_mwh` 0.112 → 2.824 TWh (0.02 % → 0.32 % of load), reserve margin −0.084 → −0.073 against a [0.7 %, 15.7 %] band, accredited firm short of requirement by 12.3 → 12.5 GW in every year, `lw_price` $44.60 → $206.36. **Consequence, declared now:** MISO's shortage is an order of magnitude milder than ERCOT's (0.32 % of load at 2030 vs 12.9 %), so **CO2, merit-order and dual results are campaign-grade in all five years**; the **2030 price level alone is DISCLOSURE-ONLY** (`lw_price` $206.36 with I14 WARN and 361 shortage hours is scarcity-set), and 2028–2029 price *levels* carry the I14 WARN beside them. Price **deltas** at 2026–2027 are campaign-grade. A broken REF fails the premise; it never passes the delta. |
| **G3** | **footprint confinement** | *carbon* arms move fossil rows only, every zero-carbon class Δ = 0.0000 TWh, `emissions_by_fuel_mt["import"]` = 0.0000; *CES* arms move eligible/ineligible shares + the CES dual; *voluntary* arms move eligible-class rows, thermal rows and the escape column only |
| **G4** | **`CES-T80` dual identity** | dual = ACP **$50.0000 exactly** in every year the target is unmet; a strictly interior dual only where it is met. Escape MWh = `target(y)·D − credited` |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's `{I3, I7, I12}` FAIL / `{I14}` WARN. A new FAIL outside the target mechanism kills the arm |
| **G6** | no unserved energy appears where REF has none | REF already sheds in every year, so this binds as: `unserved_mwh` must not **rise** in an arm whose mechanism cannot raise demand (`CARB-*`, `CES-*`, `VOL-*`). It does **not** bind on `CARB-MID+LOAD-HI` / `ALL-CLEAN`, which raise load by construction |
| **G7** | voluntary dual bounded, **per arm** | where the row binds: dual > 0 and ≤ **that arm's own** ceiling from `VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]` — **$4.5** on `VOL-MID`, **$7.0** on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`; where it escapes: dual = that ceiling **exactly** and escape MWh = the shortfall |
| **G8** | curtailment before thermal | **DECLARED VACUOUS ON MISO IN ADVANCE** (§6.4 P-12): REF's `curtailment_twh` is 0.0000 in every year, so there is no curtailed eligible MWh to recover and the antecedent is empty. Scored **N/A**, never as a PASS. Its substance is carried by P-11 (no thermal response either) |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as headline, additional beside it, the CES dual under each — never one alone (ruling S11) |
| **G-B1** | the S15 mask is actually cleared | **PASS, computed pre-solve** — §7.3: 60.00 (57.00 for CCS) vs an exact ≤ 30.00 upper bound on REF's attr, every eligible tech, zone and year |
| **G-B2** | `CES-P60` footprint as a CES case | eligible/ineligible shares and the CES dual move; every zero-carbon class row otherwise as G3 declares |
| **G-B3** | `CES-P60` collateral | no non-target load-bearing invariant flips PASS → FAIL vs REF |
| **G10–G12** | `CAP-STATE-TIGHT` | **N/A for MISO** — killed at phase 0 on a proven identity (§4.2), never in this lane's chartered set |

A gate **may kill an arm; it may never promote one**, and **no gate reads a target residual.**

---

## 9. Execution plan — the shard split (ruling S16)

**Driver** — `scripts/run_ces_leg.py` at THE PIN, one leg per invocation, years sequential:

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/miso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/MISO/<CASE>
```

**Shard width = 2 legs**, from the Stage A-LOAD synthesis §8's measured MISO rate
(5.23 min/solve-year ⇒ 26.2 min/leg ⇒ ~52 min LP per shard, inside the 60-minute budget).
RESOLVE-MISO measured 6.20 min/solve-year on a container also building `data/clean`, so a
shard may run ~62 min of LP; that is the disclosed upside, and it is why the width is 2 and not
3. **MISO peaks at 9.98 GB on a 15 GB box — never two MISO solves in one container.**

| shard | cases | keys |
|---|---|---|
| **G1** | `CARB-LO`, `CARB-MID` | `1c815555d55e5db2`, `27fb6e72c0ad31ae` |
| **G2** | `CARB-HI`, `CARB-MID+LOAD-HI` | `40bc61fac2b5271d`, `e644893331d7708f` |
| **G3** | `CES-P10`, `CES-P20` | `e4ba286178e0d499`, `472af7fd5ba90f99` |
| **G4** | `CES-P30`, `CES-T80` | `3a4b528c75d7fd6d`, `82c916d847270ebf` |
| **G5** | `VOL-MID`, `VOL-HI` | `dc8ca3580e277d72`, `7e1a2a2145711bab` |
| **G6** | `CES-P20+VOL-HI`, `ALL-CLEAN` | `ed42e5d7d1d95d3e`, `00edacf5f50c88fc` |
| **G7** | `CES-P60` (via `--set`) | `e5fb002f78c0c681` |

Protocol: `docs/handoffs/SUBLANE-scn-ws5a-policy-miso-solve-protocol-2026-09-07.md`.
**Cache isolation:** all thirteen keys are new; `results/MISO/` exists in no lane container, and
a pre-existing key directory in a shard is a **STOP**. Registration: kind `scenario`, campaign
`scn-campaign-policy-2026-09-06`, run id `miso-2026-2030-scn-campaign-policy-2026-09-06-<label>`,
with **every invariant FAIL declared in `frontend/data/hindcast/invariant-failures.json` in the
same commit**; `check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` must exit 0.

**Budget.** 13 legs × 5 solve-years = **65 solve-years**, ~340 min of LP fanned across 7
containers ⇒ ~52–62 min of LP per container plus ~35–45 min of fixed setup (hydrate + `uv sync`
+ `regenerate_clean`, the last of which measured ~40 min in this lane's own container).

---

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no case invented**
  beyond the S15 leg the charter mandates, **no solve yet**, **no year past 2030**. DOF ledger:
  **zero** free parameters. No `authorized_price_tuning` (a backcast offer-curve channel;
  untouched by a forecast lane).
- **Rule 22 `[R-HOLDOUT]` / R-AZ:** every leg is `mode="forecast"` over **2026–2030**, inside
  the forecast plan §2.1b five-solve-year window. No grant is needed and none is claimed; no
  backcast year is touched; no marker is read or written.
- **Rule 15 / forecast plan §7.5:** the **forecast** namespace only
  (`frontend/data/hindcast/<run id>.json` + `invariant-failures.json`). The backcast registry,
  `program-status.json` and `ff-verdicts.json` are untouched.
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms and its control is a committed one.
- **Backcast byte-identity:** untouched by construction (forecast mode on every leg).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the MISO base YAML,
  everything under `src/` and `scripts/`, every other ISO's files, every committed bundle and
  sidecar, the readiness plan and the desk ledger (their §5.1 / §3 rows are written **after**
  the FINDING, in this lane's own rows only).
- **Rule 27 `[R-PUSH]`:** no source file ≥ 300 lines is rewritten; any pushed file ≥ 300 lines
  is fetch-back verified (line count + blob hash).
- **No CI workflow is created.** Every solve runs in a Claude session.
- **This is NOT a keeper and cannot be one** — "keeper" is a backcast-calibration concept. This
  is a forecast scenario campaign registered `--kind scenario`; it has no keeper shard, no
  determination and nothing that can be promoted.

## 11. Routed to SCN-DESK — not executed, outside this lane's regions

1. **The charter's `VOL-MID` expectation does not generalise.** ERCOT killed it as slack in all
   five years; **MISO's binds in 2029–30**, and the 2029 crossing is **0.70 TWh — 0.6 % of
   `G`**. Any desk text that reads "VOL-MID is the inert arm" should be scoped to ERCOT.
2. **The S15 mask has a second ceiling nobody has named.** MISO's *clean-tier* family escapes
   at `STATE_RPS_ACP["MISO"]` too (`policy/clean_tiers.py:139`), so on MISO the mask is $30 on
   **both** attribute rows. The addendum's arithmetic is unaffected, but a lane reasoning only
   about the RPS row would understate the mask on any ISO with a clean tier.
3. **The voluntary dual is itself masked by the same seam.** Its ceiling ($4.5 / $7.0) is below
   every `STATE_RPS_ACP` in the footprint, so the voluntary row's *deployment* half —
   plan §5.1 criterion 2's "dual → the existing `max()` screen seam" — **cannot be exercised in
   any RPS ISO at the committed levels**. That is a campaign-wide readability limit on the
   voluntary axis, not a MISO fact, and it belongs beside card D-3c.
4. **`miso-2026-2030-d60-arm` remains stale as a description of HEAD** (+14.7 % energy; I3
   fails in REF where the board key has it passing) — RESOLVE-MISO §7 item 3, restated so it
   does not get lost, for the capx director.

---

## ADDENDUM A — 2026-09-07, the S15 mask is ZONAL, and half of MISO is unmasked

**Written and pushed BEFORE any shard produced a result** (the seven shards were launched at
03:34–03:36 UTC and each pays ~40 min of `regenerate_clean` before its first LP; nothing had
solved). This is **zero-LP registry arithmetic that belonged in §7.1 and was not done there** —
it sharpens a prediction rather than revising one against an answer, and §7.1's own stated limit
("whether a *lower*-dual MISO region exists … is not determinable at zero LP") is what it
closes. **No case, key, kill, level or gate moves.** Instrument:
`docs/handoffs/scn-ws5a-policy-miso/rps-region-census-2026-09-07.py` → `…json`.

### A(a) MISO's RPS row is FIVE regions with FIVE different eligible geographies

`MISO_RPS_COMPLIANCE_REGIONS` at THE PIN, with each region's obligation computed as
`obligated_load_share × floor(year) × (that zone's own annual demand on the runner's demand
chain)`, against the ISO-wide eligible pool `G` (= REF's dispatched wind + solar):

| region | obligated zone × share | eligible zones | floor 2026→2030 | obligation TWh 2026→2030 | vs `G` (103.6 → 127.5) |
|---|---|---|---|---|---|
| **MN** | MISO-West × 0.77 | **5** (all but MISO-South) | 0.26 → 0.40 | 20.87 → 40.06 | far under |
| **MI** | MISO-East × 0.57 | **MISO-East only** | 0.35 → 0.50 | 34.88 → **63.14** | one zone's VRE must cover it |
| **WI** | MISO-East × 0.43 | **5** | 0.10 | 7.52 → 9.53 | far under |
| **IL** | MISO-Illinois × 1.00 | **MISO-Illinois only** | 0.25 → 0.40 | 12.20 → **24.74** | one zone's VRE must cover it |
| **MO** | MISO-Plains × 0.43 | **5** | 0.15 | 6.36 → 8.00 | far under |

### A(b) The consequence: `rps_credit_for_zone` is structurally ZERO in two of six zones

`p[z] = max{dual_r : z ∈ eligible_zones(r)}` (`policy/rps.py:145–179`), so a zone admitted by no
region earns **0 by construction, whatever any dual does**:

| zone | admitting RPS regions | admitting clean-tier regions | 2030 demand TWh |
|---|---|---|---|
| MISO-West | MN, WI, MO | MN | 130.05 |
| MISO-Plains | MN, WI, MO | MN | 123.96 |
| MISO-Illinois | MN, WI, **IL**, MO | MN | 61.84 |
| MISO-Indiana | MN, WI, MO | MN | 122.48 |
| MISO-East | MN, **MI**, WI, MO | MN, **MI** | 221.54 |
| **MISO-South** | **none** | **none** | **228.04** |

**MISO-South is in no RPS region's and no clean-tier region's eligible geography — and it is
MISO's largest demand zone** (26 % of 2030 ISO demand). Its attribute alternative is identically
zero, so the federal CES premium is **never masked there**, at $10 or at any level.

### A(c) The refined S15 answer — P-7b, pre-registered beside P-7

§7.1's measurement stands unchanged: the ledger scalar `rps_dual` = 30.0 = `STATE_RPS_ACP["MISO"]`
in 5 of 5 years, and it is a **MAX over regions**. A(a) now says *which* regions can plausibly
be at that ceiling — the two **single-zone** ones, MI (63.1 TWh of obligation against MISO-East's
own VRE) and IL (24.7 TWh against MISO-Illinois's own) — while the three five-zone regions carry
obligations of 8–40 TWh against a 104–128 TWh pool and are very likely slack at a dual of 0.

**P-7b (pre-registered, falsified or confirmed by the shards' `rps_region_duals`):** the
predicted per-zone RPS credit is **30 in MISO-East and MISO-Illinois** and **0 in MISO-West,
MISO-Plains, MISO-Indiana and MISO-South**. If that holds, the S15 mask on MISO is **zonally
partial, not ISO-wide**, and `CES-P10`/`P20`/`P30` **DO** reach the entry screen in four of six
zones — including the two largest by demand. **P-7 as written in §6.3 (no new VRE entry
response) is then WRONG, and it is scored as written and at full magnitude**; P-7b is scored
beside it. This is the sharpest thing this lane can say before an LP runs, and it makes MISO's
answer to ruling S15 qualitatively different from an ISO whose RPS row is ISO-wide.

**What does NOT change:** the ledger measurement, the "mask binds" verdict in §7.1 (it binds —
in the two zones where a region escapes), the decision to add `CES-P60`, and **G-B1**, which is
*strengthened*: in the unmasked zones REF's attr is 0, so $60 clears by the full $60 rather than
by $30, and the ≤ $30 upper bound used in §7.3 remains a valid bound everywhere.

### A(d) One precision fix to P-8, recorded rather than quietly corrected

§6.3's P-8 says "every `gas_cc_ccs` unit has zero attribute alternative". That is too strong as
a general statement: `MISO_CLEAN_TIER_REGIONS["MI"]`'s `qualifying_fuels` **includes**
`gas_cc_ccs` (MN's does not). It is nonetheless true of **MISO's actual retrofit cohort**, which
is two plants — `p7985` in **MISO-Plains** and `p1007` in **MISO-Indiana**
(`FINDING-scn-ws5a-resolve-miso-2026-09-06.md` §2.1) — and MI's eligible geography is
**MISO-East only**, so neither host can earn the MI clean credit. P-8's prediction is unchanged;
its justification is narrowed from "every CCS unit" to "every CCS unit outside MISO-East, which
is both of MISO's".
