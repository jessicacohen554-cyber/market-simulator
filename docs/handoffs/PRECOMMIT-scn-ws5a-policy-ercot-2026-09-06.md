# PRECOMMIT — SCN-WS5A-POLICY-ERCOT: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-ERCOT · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-ws5a-policy-21mq1y` · **Data profile** `ercot`
(full clone — `hydrate_data.py --profile ercot` reports every blob already local) ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Charter** SCN-DESK ledger §5 policy charter **v5** (r#16) · **Predecessors**
`PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (THE PIN, the inherited G-DRIFT) and
`FINDING-scn-ws5a-load-ercot-2026-09-06.md` (the REF this lane differences against).

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed artifact, or arithmetic on the two. Nothing here is
revised after a solve; §6's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` §0 (precondition P1). Verified here:
`git merge-base --is-ancestor bdfb3095 origin/main` → **yes**; `origin/main` is **88 commits**
past it at PRECOMMIT time. **THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything on `main`
after it is recorded as post-pin, never retro-fitted and never used to re-read a result. My
keys are therefore **pre-fingerprint keys** (capx D79 entered `cache_key()` after the pin);
the pin records them and §2 lists them.

## 0.1 Bottom line before any LP

1. **Ten of twelve chartered cases survive phase 0; two are killed on a proven identity.**
   `VOL-MID` is **slack in all five years** (§3) and `CAP-STATE-TIGHT` resolves to **no carbon
   program at all** on ERCOT in every year (§4). Neither is solved.
2. **The carbon axis is byte-identical to REF in 2026 in every arm** — the RFF 2026 knot is
   $0 in `low`/`mid`/`high` alike — and live 2027–2030. That is not a kill (the case is live in
   4 of 5 years); it is a free per-year identity check, pre-registered as gate **G1a**.
3. **ERCOT's REF is in deep shortage, so this lane's price side is disclosure-only from 2028**
   and its *levels* are not quotable at any year (`FINDING-scn-ws5a-load-ercot` §7: unserved
   0.38 → 127.2 TWh, `lw_price` $91 → $4,438, `hours_ge_500` 7,962 of 8,760). Gate **G2** is
   the REF-side precondition that asserts this rather than discovering it (desk standing
   change #2).
4. **The inherited G-DRIFT makes the committed REF a valid control without a control solve.**
   ERCOT carries **no `gas_cc_ccs` row in any year of any leg** — re-measured here from the
   committed summary, not inherited — so capx D77 and D65-B re-key ERCOT without moving an
   answer, and rule 29(b) form 4 holds (§5).
5. **One charter literal is corrected before it can mislead a gate.** The charter's G7 names
   the WTP ceiling as `$4.5/MWh`; that is the **mid** level. Every voluntary leg that survives
   phase 0 runs `high`, whose ceiling is **$7.0/MWh** (§3.3). G7 is bounded per arm.

---

## 1. Preconditions — verified, with one charter/actual discrepancy recorded

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE's PRECOMMIT names the pin; ERCOT clean by G-DRIFT | **MET** | `1b95d430` (#5214) §0 names `bdfb3095`; its §2 measures ERCOT `gas_cc_ccs` = 0.00 TWh in every year of all three legs. Re-measured independently here (§5.1). |
| **P2** | ERCOT's REF leg at the pin registered on main | **MET, at a different path than the charter states** | ERCOT's REF is the standing SCN-WS5A-LOAD leg, `results/scn-campaign-load-2026-09-06/ERCOT/REF/`, key `6e40769352a572ba`, sidecar `frontend/data/hindcast/ercot-2026-2030-scn-campaign-load-2026-09-06-ref.json`, `provenance.scored_at_sha = 73c109cb4098`, 5/5 years solved. **Discrepancy:** the charter says RESOLVE "re-solved IN PLACE"; it did **not** — legs 1–6 *renamed* the re-solved trees to `results/scn-campaign-load-2026-09-06-**r2**/<ISO>/<CASE>/` (`R083`/`R097` in `61b9cce5`). Immaterial to ERCOT (not re-solved) but it is the path a PJM/CAISO/MISO/NEISO/NYISO policy lane must read. Routed §8. |
| **P3** | the carbon form is the committed RFF path ladder | **MET at the pin** | `configs/scenario_campaign_matrix.yaml` at `bdfb3095`: `CARB-LO/MID/HI` → `carbon_price_path: low/mid/high`; `ALL-CLEAN` → `carbon_price_path: mid`. Resolved values measured in §4. |
| **P4** | rule 12 concurrency | **NOT MET — first solve HELD** | SCN-WS5A-RESOLVE is at leg 6/13 (`9ef06cf8`, PJM REF) and its remaining legs are **CAISO ×3 and MISO ×3**, both per-plant. The charter's own clause: while RESOLVE is on a per-plant ISO, this lane does phase 0 + PRECOMMIT and **holds**. See §7. |
| **P5** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` exist | **MET, and out of scope for ERCOT** | Both live at the pin. ERCOT carries no program → §4.2 kills the case; it was never in ERCOT's chartered set. |

## 1.1 The constant families this lane consumes (desk standing change #1)

All read at **THE PIN** `bdfb3095`, verbatim:

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `policy/carbon.py` | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | keys `CAISO`, `NYISO`, `NEISO` — **ERCOT absent** |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NYISO`, `NEISO`, `PJM` — **ERCOT absent** |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; mid {2023: 0.08}; high {2023: 0.08} |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; **mid {2026: 0.5}**; high {2026: 1.0} |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5**; **high 7.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built; ERCOT has only wind + solar |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["ERCOT"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = 1.0 |
| `DATACENTER_ADDITIONS_MW["ERCOT"]` | `config/constants.py` | mid {2025: 3,516; 2030: 38,182; 2035: 41,675} MW; high {2025: 9,281; 2030: **88,603**; 2035: 95,151; 2040: 97,920} MW |
| `DEMAND_GROWTH_RATES["ERCOT"]` | `config/constants.py` | mid {near 0.134813, long 0.016258}; high {near 0.206157, long 0.004561} |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}; ACP $50/MWh |

**A stale comment, named so it is not read as a level.** The campaign YAML's ERCOT
tail-regime block still narrates "DC high 122 GW by 2030"; the pin's constant is
**88,603 MW**. The 122 GW anchor was retired by SCN-LOAD's re-derivation, which is why the
load lane's prediction P-1 (no tail regime) was a HIT. The YAML's arithmetic block is stale
prose; the constant above is what this lane resolves against. Not edited (not this lane's
region) — routed §8.

---

## 2. The case set at THE PIN — resolved fields and cache keys

Resolved exactly as `runner.run_scenario_iso` does: `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults`,
then `config.cache_key()`. Base: `configs/scenarios/ercot_scenario_base_2026_2030.yaml`.

**Chain validation — the same three ERCOT rows RESOLVE published, reproduced independently:**
`REF` `de9c68e19316910e`, `LOAD-HI` `ec2ea8193e2e45a1`, `LOAD-HI-ORGANIC` `0c87f2f2467e95b3`
— identical to `PRECOMMIT-scn-ws5a-resolve` §3's ERCOT line. The resolve chain used below is
therefore the one the solve will use, not a naive `cache_key()`.

| case | key at THE PIN | override vs REF | verdict |
|---|---|---|---|
| *REF (control, not solved)* | `de9c68e19316910e` | — | **reused** (key `6e40769352a572ba` as solved at `1cc45bb2`; see §5) |
| `CARB-LO` | `c1e09985c3e4fa56` | `carbon_price_path: low` | **SOLVE** |
| `CARB-MID` | `ab8d79646b49abbd` | `carbon_price_path: mid` | **SOLVE** |
| `CARB-HI` | `73dadcb65d74acce` | `carbon_price_path: high` | **SOLVE** |
| `CES-P10` | `17e0b252e13a484a` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `5a89c34af859160c` | premium 20.0 | **SOLVE** |
| `CES-P30` | `8588e1b0d055e772` | premium 30.0 | **SOLVE** |
| `CES-T80` | `e6638b058ce4d5fb` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CARB-MID+LOAD-HI` | `b99311bb1f3032e0` | carbon mid + growth high + DC high | **SOLVE** |
| `VOL-MID` | `8878ca20b4cf2f0d` | `voluntary_clean_demand_path: mid` | **KILLED — §3.2** |
| `VOL-HI` | `76ef5a80df6a9277` | `voluntary_clean_demand_path: high` | **SOLVE** |
| `CES-P20+VOL-HI` | `5b7774c817ee425b` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `619cfffde44422b2` | carbon mid + growth high + DC high + CES target + ACP 50 + voluntary high | **SOLVE** |
| *`CAP-STATE-TIGHT`* | `a5362929b2690f31` | cap fields | **KILLED — §4.2** (never in ERCOT's chartered set) |

**Every case keys distinctly**, so no leg can collide with another or with a pre-fix bundle.
`LOAD-HI` is the pairing base for `CARB-MID+LOAD-HI` and is **not re-solved** — it is the
committed leg at `1cc45bb2` (key `31cf71afda5c610d`), valid as a control under §5.

**10 legs to solve, 50 solve-years.**

---

## 3. Phase 0 — the voluntary row, per year, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed —
`load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`, the runner's own
chain — not by re-deriving the memo's arithmetic. Zone list: the 7 ERCOT zones, no import node.

### 3.1 The resolved volumes (TWh)

| case | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| REF / all non-VOL | `E_total` | 595.73 | 676.04 | 767.18 | 870.60 | 987.97 |
| | `E_DC` | 77.80 | 129.43 | 181.05 | 232.68 | 284.30 |
| `VOL-MID` | **V** | 80.34 | 108.44 | 137.42 | 167.37 | 198.45 |
| `VOL-HI`, `CES-P20+VOL-HI` | **V** | 119.24 | 173.16 | 227.94 | 283.71 | 340.60 |
| `ALL-CLEAN` (DC high) | `E_total` | 672.99 | 811.73 | 979.07 | 1,180.91 | 1,424.37 |
| | `E_DC` | 187.23 | 305.36 | 423.49 | 541.61 | 659.74 |
| | **V** | 226.09 | 345.87 | 467.93 | 592.76 | 720.91 |

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — and the kill

Eligible generation `G` = wind + solar **as dispatched in the paired baseline** (ERCOT has no
offshore wind or geothermal; the fuel keys present in every committed leg are exactly
`coal, gas_cc, gas_ct, gas_st, hydro, nuclear, solar, wind`). `G_REF` from
`results/scn-campaign-load-2026-09-06/ERCOT/REF/`; `G_LOAD-HI` from that leg, the nearest
committed baseline for `ALL-CLEAN`'s DC-high / growth-high posture.

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` | 197.26 | 198.49 | 198.49 | 219.79 | 234.86 |
| `G_LOAD-HI` | 197.26 | 198.49 | 198.49 | 215.61 | 233.17 |

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | 80.3 < 197.3 (**+116.9**) | 108.4 < 198.5 (**+90.1**) | 137.4 < 198.5 (**+61.1**) | 167.4 < 219.8 (**+52.4**) | 198.5 < 234.9 (**+36.4**) | **(i) SLACK, all five years** |
| **`VOL-HI`** vs `G_REF` | 119.2 < 197.3 (+78.0) | 173.2 < 198.5 (+25.3) | **227.9 > 198.5 (−29.5)** | **283.7 > 219.8 (−63.9)** | **340.6 > 234.9 (−105.7)** | slack 2026–27, **binds 2028–30** |
| **`CES-P20+VOL-HI`** | identical V to `VOL-HI` | | | | | slack 2026–27, **binds 2028–30** |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | **226.1 > 197.3 (−28.8)** | **345.9 > 198.5 (−147.4)** | **467.9 > 198.5 (−269.4)** | **592.8 > 215.6 (−377.2)** | **720.9 > 233.2 (−487.7)** | **binds all five years** |

**`VOL-MID` IS KILLED — the identity, stated as an argument and not an assertion.** The
voluntary row adds one constraint plus one escape column of strictly positive cost. When
`V ≤ G` at REF's own optimum, REF's solution is feasible for `VOL-MID` with `ESC = 0` and
carries the same objective value; `VOL-MID`'s feasible set is REF's intersected with the new
row, and REF's optimum lies inside it — so REF's optimum **is** `VOL-MID`'s optimum, the dual
is 0, and the deployment half (the dual through the screens' `max()` seam) is unarmed. The arm
is byte-identical to REF in all five years and is **not solved**. This EXTENDS WS-3b §6, which
measured the slack at ERCOT 2026 only (on the smaller `scn-ws4-probe` REF: V 76.2 / 115.1 vs
G 197.3), across the whole T1-F window on the campaign REF. The thinnest margin is 2030's
**+36.4 TWh**, 15.5 % of `G_REF` — slack, not marginal.

**`VOL-HI` is NOT killed**: the same test binds from 2028, so rule 29's inert-year clause
applies to the arm's first two years, not to the arm.

### 3.3 The WTP ceiling — a charter literal corrected before it binds a gate

`voluntary_wtp_ceiling_usd_per_mwh` ships `None`, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. The charter's G7 names **$4.5/MWh** — the **mid**
level (ruling S9's cell). **Every voluntary leg that survives phase 0 runs `high`**, whose
ceiling is **$7.0/MWh** (WS-3b §4(b): *"VOL-MID carries this cell; VOL-HI runs the cited $7
endpoint"*). G7 is therefore bounded at **$7.0/MWh** for `VOL-HI`, `CES-P20+VOL-HI` and
`ALL-CLEAN`. The $4.5 cell would have been the bound for `VOL-MID` alone, which is killed. No
level moved; the charter's parenthetical was the wrong one of two committed cells.

---

## 4. Phase 0 — the carbon axis and the cap row

### 4.1 Resolved carbon $/tCO2 per year (`policy.carbon.resolve_carbon_price`)

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `REF` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `CARB-LO` | **0.0000** | 2.0000 | 4.0000 | 6.0000 | 8.0000 |
| `CARB-MID` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| `CARB-HI` | **0.0000** | 7.5000 | 15.0000 | 22.5000 | 30.0000 |
| `CARB-MID+LOAD-HI` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| `ALL-CLEAN` | **0.0000** | 3.7500 | 7.5000 | 11.2500 | 15.0000 |
| every CES-only / VOL-only case, and `CAP-STATE-TIGHT` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

**Reproduces the campaign YAML's declared ERCOT table to the cent** — that is gate **G1** on
the carbon axis, passed before any LP. The 2026 knot is $0 in every path, so **2026 is
byte-identical to REF in all five carbon-bearing arms** (gate **G1a**).

### 4.2 `CAP-STATE-TIGHT` is proven LP-identical to REF on ERCOT

`resolve_carbon_program(config, year)` returns **`None`** in every year 2026–2030 for BOTH
`REF` and `CAP-STATE-TIGHT`, and `scheduled_power_sector_budget` returns **`None`** in every
year. The mechanism is the first two lines of `policy/cap_and_trade.py::resolve_carbon_program`:
`CAP_AND_TRADE_PROGRAMS.get("ERCOT")` is `None` → early return, before `mass_cap_enabled` is
ever consulted. So `mass_cap_enabled: true` and the whole `mass_cap_tons_by_year` schedule
(which names NYISO/NEISO/CAISO only) reach no LP input. The cache key moves
(`a5362929b2690f31` ≠ `de9c68e19316910e`) because the fields are set; **no LP input differs**.
Killed at phase 0 — the same "key moves, answer cannot" class as ERCOT's own REF across the
pin. This confirms the charter's ERCOT/MISO clause with a measurement rather than by citation.

---

## 5. G-DRIFT (rule 29(b)) — the control is the committed REF, and no control solve is earned

### 5.1 `1cc45bb2 .. bdfb3095` — inherited, and its ERCOT premise re-measured here

RESOLVE's §1 classified 34 non-merge solve-path commits: **4 LIVE** (capx D77, D65-B ISO-wide;
D67-ARM, D81 **PJM only**) and 30 INERT with a stated reason. For **ERCOT** all four are inert:

- **D77 / D65-B** are inert because ERCOT's retrofit ledger is empty. **Re-measured here, not
  inherited:** `generation_by_fuel_mwh` in `results/scn-campaign-load-2026-09-06/ERCOT/{REF,
  LOAD-HI,LOAD-HI-ORGANIC}/full_horizon_summary.json` carries **no `gas_cc_ccs` key at all** in
  any of the 15 leg-years — the fuel does not appear, which is stronger than a 0.00 reading.
  A repair to a converted unit's emission rate and a change to the capture VOM adder cannot
  move a fleet that converts nothing.
- **D67-ARM / D81** are PJM-scoped: `capacity_adequacy_requirement_published_by_iso` and
  `capacity_market_supply_clearing_by_iso` both resolve **`None`** on ERCOT (RESOLVE §3's
  per-ISO table; reproduced in this lane's own resolve, §2).

⇒ **Form 4 is VALID for ERCOT.** The committed `REF` (key `6e40769352a572ba`, solved at
`1cc45bb2`) and `LOAD-HI` (key `31cf71afda5c610d`) **are** the control. Their keys differ from
the pin keys `de9c68e19316910e` / `ec2ea8193e2e45a1` — that is D65-B re-keying a field ERCOT
never reads, and it is exactly the case rule 29(b) says a code audit answers better than a
control solve. **No control solve is spent, and REF is never re-solved** (charter P2).

### 5.2 `bdfb3095 .. HEAD` — for the record; I solve at THE PIN regardless

`git diff bdfb3095 origin/main` over the same window: **13 files, +1,467 / −52, across 4
non-merge commits.** All four INERT for an ERCOT forecast leg:

| commit | what | INERT because |
|---|---|---|
| `cd96fa26` | pjm-167 F2 — published transfer limit enforced only if its own flows respect it | New field `pjm_interface_feed_admissibility_gate: bool = **False**`; PJM-scoped and backcast-facing. Absent from ERCOT's `default_scenario_overrides` and from every campaign case. |
| `beb74f0f` | pjm-167 F1 — backcast EIA-860 vintage tracks the solved year | New field `eia860_vintage_tracks_solve_year: bool = **False**`; and the vintage branch it gates is `config.mode == "backcast" or config.hindcast`, neither true on a forecast leg. |
| `16210868` | capx D79 phase 1 — the solve-surface fingerprint enters `cache_key()` | **Key-only, and it moved zero keys at landing** (`capxd79-solve-surface-no-op-record.json`: every name declared at its live hash). It carries no LP input. My pin is pre-D79, so my keys are the pre-fingerprint keys §2 lists. |
| `bf97317f` | capx D78-R2 step 0 — delete the producer-less `exempt_unit_ids`; restate T3 as a negative test | D78's seam needs `retirement_sector_gate` **and** a clearing-armed ISO; ERCOT has neither (`retirement_sector_gate` False, clearing `None`). |

**No LIVE hunk ⇒ no control solve is earned under clause (b), on either window.**

---

## 6. What each surviving leg is expected to do — pre-registered, from measured responses

Sources, all measured before this lane and none of them a residual: **WS-1b §3.1** (the ERCOT
2027 carbon pair), **WS-2b §3** (the ERCOT CES premium ladder at HEAD), **WS-3b §6** (the
voluntary row's arithmetic), and the committed ERCOT REF itself.

### 6.1 The sharpest prediction — a cross-lane identity, not a band

**P-1.** `CARB-MID` **2027 reproduces WS-1b §3.1's CARB arm exactly**: `emissions_mt`
**255.0452 Mt**, `lw_price` **984.247 $/MWh**, `unserved_mwh` unchanged from REF at
4,621,769.86, `clean_share` unchanged at 0.3519, `import_co2_mt_reported` 0.0000.
*Why this is an identity and not an analogy:* WS-1b's T0 pair
(`ercot-2026-2027-scn-ws1-probe-{ref,carb}`) ran on **the same base config**
(`configs/scenarios/ercot_scenario_base_2026_2030.yaml`) with the same resolved override
(+$3.7500/t at 2027), and its REF 2027 — 255.9732 Mt / 982.313 $/MWh — is **my campaign REF's
2027 to displayed precision** (255.97 / 982.31). Under one-pass capacity evolution 2027 depends
only on 2026, so a 2026–2027 run and a 2026–2030 run must agree at 2027. **Scored as a hit only
on an exact match to 4 dp**; any drift is a real finding about pin-inertness and is reported at
full magnitude, not explained away.

**P-2.** The three carbon arms' **2026 is bit-identical to REF** — `co2_mt` 214.3926,
`lw_price` 91.037 — as WS-1b measured for its own pair. (Gate G1a.)

### 6.2 Carbon — sign, ordering, magnitude

**P-3.** CO2 falls and price rises monotonically REF → LO → MID → HI in each year 2027–2030;
2026 flat. **P-4.** The mechanism is a coal→gas-CC merit-order substitution at ~1:1 energy,
with **every zero-carbon class moving exactly 0.0000 TWh** (WS-1b's footprint claim held
without qualification; that is gate G3). **P-5.** ΔCO2 at `CARB-MID` 2027 = **−0.928 Mt**
(−0.36 %); at `CARB-LO` 2027 (half the price, $2.00) I expect **−0.3 to −0.7 Mt** —
sub-linear, because the cheapest coal→gas swaps go first; at `CARB-HI` 2027 ($7.50, 2×)
**−1.4 to −2.0 Mt**, likewise sub-linear rather than 2×. **P-6.** By 2029–2030 the arms'
ΔCO2 **shrinks toward zero in absolute terms despite a rising carbon price**, because REF is
shedding 127 TWh at VOLL and the coal that carbon would displace is already inframarginal
against scarcity — the same saturation the load lane measured (its §2: ΔCO2 falls +41.6 →
+13.4 Mt while Δunserved rises). *This one carries the most reasoning and is the most likely
to miss.*

**P-7.** **No `gas_cc_ccs` appears in any carbon arm in any year.** `ccs_retrofit_available_year`
is 2028 and `CARB-HI` reaches only $15/t there; WS-2b measured ERCOT's screen listing CCS
`unprofitable` / `per_tech_cap_zero` at carbon 0, and capx D50's closure (owner Q42) is the
same asymmetry. If one appears, the D77 seam becomes live for ERCOT and §5.1's control
argument needs re-stating — which is why it is pre-registered.

### 6.3 CES — the ladder is expected to SATURATE

**P-8.** **`CES-P20` and `CES-P30` land within 1 % of each other on `clean_share`, commissioned
VRE and `emissions_mt`.** WS-2b §3 measured exactly this at HEAD: CES-20 and CES-40 commission
*identical* builds (14.0 GW solar, 10.0 GW wind), clean shares 0.4751 vs 0.4756, CO2 257.680 vs
257.637 Mt — because the binding cap in every premium year is **`iso_budget_exhausted`**, the
12 GW/yr ISO queue budget, not the price. Above ~$20/MWh the ERCOT premium buys nothing more.
**P-9.** `CES-P10` separates from `CES-P20` (below the saturation point). **P-10.** Direction,
in all three arms: `clean_share` ↑, commissioned wind and solar ↑, `avg_price` ↓,
`negative_price_hours` 0 → >0, curtailment ↑ (WS-2b measured it roughly doubling, 4.91 → 9.97
TWh). **Caveat carried at the number:** WS-2b's ladder ran on `ercot_ces_poc_2026_2030.yaml`
with a BAU 2030 shedding 17.7 TWh, while my REF sheds 127.2 TWh — so the *directions* and the
saturation *mechanism* transfer, the *levels* do not, and I predict no level from it.

**P-11.** `CES-T80`: the 2026 target is 0.55 and **my REF's own clean share never reaches it**
— measured from the committed REF's `generation_by_fuel_mwh` (wind + solar + nuclear + hydro
over `total_gen_mwh`): **0.3953 / 0.3519 / 0.3257 / 0.3246 / 0.3172** across 2026–2030, i.e.
*falling*, because load outgrows clean entry. (The 2027 value **0.3519** is WS-1b §3.1's
reported `clean_share` for the same year to 4 dp — a third independent confirmation that its
pair sits on this REF.) The gap to the 0.55 target therefore *widens*, so the row is in the
**escape regime in every year**:
dual = ACP **$50.00/MWh exactly**, escape MWh = the shortfall `target(y)·D − credited`. That is
gate G4, and it is the same regime WS-2a measured on its NEISO T0 pair (credited 0.345 < 0.55,
dual = ACP exactly).

### 6.4 Voluntary — the dual, the escape, and the ordering

**P-12.** `VOL-HI` and `CES-P20+VOL-HI`: dual **0.0 in 2026–2027** (slack), and in **2028–2030
the escape fires** — dual = **$7.0/MWh exactly**, escape MWh = `V − Σ eligible`, i.e. roughly
29.5 / 63.9 / 105.7 TWh before any dispatch response. The shortfall is far too large for
ERCOT's eligible fleet to close, so I expect the escape regime rather than an interior dual.
**P-13.** `ALL-CLEAN`: escape regime in **all five years**, dual $7.0/MWh exactly.
**P-14 (gate G8).** Where the row first binds, **curtailment of eligible resources falls before
any thermal row moves** — the first MWh a REC buyer pays for is one that was being dumped.
Measured as: Δcurtailment < 0 and |Δcurtailment| ≥ |Δfossil generation| in the first binding
year. **P-15.** Because the escape absorbs the shortfall at a $7/MWh ceiling that is ~0.2 % of
a $4,000/MWh scarcity price, the voluntary arms' **CO2 and price deltas are small** —
|ΔCO2| < 2 Mt in every year. The voluntary axis's ERCOT content is the **dual and the
curtailment ordering**, not an emissions response.

### 6.5 The combined legs — both nettings (ruling S11)

**P-16.** `CES-P20+VOL-HI` carries the CES **premium** (a price, no row), so D-6 has **no
dispatch content** there: the two attribute buyers compose through the screens' existing
`max()` and one certificate is sold to the higher bidder — the premium ($20) exceeds the
voluntary ceiling ($7) in every year, so I expect the **voluntary dual to be irrelevant to
deployment** in this arm while remaining the row's own escape price. **P-17.** `ALL-CLEAN` is
the one arm where D-6 has content (a CES **target** row and the voluntary row both count a
clean MWh). Both nettings are reported side by side per §7's duty, with the CES dual under
each; **counts-toward is the headline** (as built), **additional** beside it — computed at the
report layer as `federal_credited − V ≥ target(y)·D`, with its implied escape
`max(0, target·D + V − federal_credited)` priced at the ACP. Neither is asserted as the answer;
D-6 is open.

---

## 7. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1 carbon table = the YAML's declared ERCOT table; §3.1 volumes from the runner's own demand chain. **Already PASS, pre-solve.** |
| **G1a** | every carbon-bearing arm's **2026** is bit-identical to REF | `co2_mt` 214.3926, `lw_price` 91.037, and the full `generation_by_fuel_mwh` to 1e-6 |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries the adequacy state WS-5A measured: unserved 0.38 → 127.2 TWh, reserve margin +0.033 → −0.253, FAIL set exactly `{I3, I12}`, `hours_ge_500` 74 → 7,962. **Consequence, declared now:** every leg's **price, captured price and deployment level is DISCLOSURE-ONLY from 2028**, and all five years' *levels* are unquotable; only **deltas at 2026–2027**, the **dispatch/footprint orderings**, and the **duals** are campaign-grade. A broken REF fails the premise, never passes the delta. |
| **G3** | **footprint confinement** | *carbon* arms move fossil rows only, every zero-carbon class Δ = 0.0000 TWh, import line 0.0000 (no node); *CES* arms move eligible/ineligible shares + the CES dual; *voluntary* arms move eligible-class rows, thermal rows and the escape column only |
| **G4** | **`CES-T80` dual identity** | dual = ACP $50.0000 **exactly** in every year the target is unmet; a strictly interior dual only where it is met. Escape MWh = `target(y)·D − credited` |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's `{I3, I12}` FAIL / `{I13, I14}` WARN. A new FAIL outside the target mechanism kills the arm |
| **G6** | no unserved energy appears where REF has none | REF already sheds from 2026, so this binds as: `unserved_mwh` must not rise in an arm whose mechanism cannot raise demand (`CARB-*`, `CES-*`, `VOL-*`). It does **not** bind on `CARB-MID+LOAD-HI` / `ALL-CLEAN`, which raise load by construction |
| **G7** | voluntary dual bounded | where the row binds: dual > 0 and **≤ $7.0/MWh** (the `high` ceiling — §3.3, correcting the charter's $4.5 mid literal); where it escapes: dual = **$7.0/MWh exactly** and escape MWh = the shortfall |
| **G8** | **curtailment before thermal** | in the first binding year: Δcurtailment of eligible resources < 0, and \|Δcurtailment\| ≥ \|Δ fossil generation\| |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as headline, additional beside it, CES dual under each — never one alone (ruling S11) |
| **G10–G12** | `CAP-STATE-TIGHT` | **N/A for ERCOT** — the case is killed at phase 0 on a proven identity (§4.2) and was never in this lane's chartered set |

A gate **may kill an arm; it may never promote one**, and no gate reads a target residual.

---

## 8. Execution plan, and the first solve is HELD

**Driver** — `run_ces_leg.py`, the driver the load and resolve lanes both used (0 lines changed
between `1cc45bb2` and the pin), at THE PIN, one leg per invocation, years sequential:

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/ercot_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/ERCOT/<CASE>
```

Rebase **between** legs, never during one. Logs to the session scratchpad, never the results
tree. **Cache isolation:** all ten keys (§2) are new — no ERCOT bundle has ever occupied them —
and `results/ERCOT/` is gitignored and empty in this container, so no stale bundle is
reachable. Registration: kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, one run id
per (ISO, case), with **every invariant FAIL declared in
`frontend/data/hindcast/invariant-failures.json` in the same commit** (the Y-24 ratchet at the
registration seam; the audit is green on SCN today and stays so).

**Budget.** 10 legs × 5 solve-years. ERCOT measured 0.41–2.84 min/solve-year on the load legs
and 77–80 s/yr on WS-2b's CES legs ⇒ **~6.5–7 min/leg, ~65–70 min of LP total**, peak RSS
~4.2 GB. Well inside §2.4.

**THE FIRST SOLVE IS HELD ON RULE 12 (precondition P4).** SCN-WS5A-RESOLVE is at leg 6/13 and
its remaining seven legs are **CAISO ×3 and MISO ×3** (per-plant, 4.87 GB and 9.65 GB peak on a
15 GB box) plus NEISO/PJM tails; the charter's own clause holds this lane to phase 0 + PRECOMMIT
while any of MISO/PJM/CAISO is solving in any lane, and **the owner sequences the slot**. ERCOT
is cheap and light (4.2 GB), so it can take the slot the moment one opens. **Nothing is solved
until then.**

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **Charter P2 names the wrong path.** RESOLVE re-solved into
   `results/scn-campaign-load-2026-09-06-**r2**/<ISO>/<CASE>/`, not in place. The five
   non-ERCOT policy lanes read their REF there; the v5 charter text should be corrected before
   they launch, or a lane will look for a REF that main's tree does not carry.
2. **The charter's G7 ceiling literal is the mid cell ($4.5).** Every surviving voluntary leg
   is `high` ($7.0). Corrected in this lane's §3.3; the other five charters carry the same
   sentence.
3. **The campaign YAML's ERCOT tail-regime block is stale** — it narrates a 122 GW 2030 DC
   anchor against the pin's 88,603 MW. Prose only, no level depends on it, and the load lane's
   P-1 already recorded the consequence; but it reads as a level and is not this lane's region.
4. **`VOL-MID` is inert on ERCOT across the whole T1-F window**, not just at the 2026 T0 that
   WS-3b measured. If the desk wants a live mid-voluntary reading anywhere, ERCOT is not the
   ISO for it, and D-3c's crediting leg (new-builds-only) is what would change that.

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no solve yet.** DOF
  ledger: **zero** free parameters. No `authorized_price_tuning` (a backcast offer-curve
  channel; untouched).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the ERCOT base YAML,
  everything under `src/`, `scripts/run_ces_leg.py`, every committed bundle and sidecar.
  `program-status.json`, `ff-verdicts.json` and the whole **backcast** namespace: untouched
  (§7.5 — this lane registers into the forecast namespace only).
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms, and the control is a committed one.
- **Backcast byte-identity:** untouched by construction (forecast-mode only, `mode="forecast"`
  on every leg).
