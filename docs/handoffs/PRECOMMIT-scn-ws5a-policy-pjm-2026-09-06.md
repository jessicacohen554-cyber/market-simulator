# PRECOMMIT — SCN-WS5A-POLICY-PJM: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-PJM · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-ws5a-policy-pjm-o50o88` · **Data profile** `pjm`
(full clone — `hydrate_data.py --profile pjm` reports every blob already local) ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Charter** SCN-DESK ledger §5 policy charter **v6** (r#17) · **Predecessors**
`PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (THE PIN, the inherited G-DRIFT),
`9ef06cf8` (RESOLVE leg 6/13 — the PJM REF this lane differences against),
`FINDING-scn-ws5a-load-pjm-2026-09-06.md` (the pre-fix PJM reading and its caveats) and
`PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md` (the first policy lane's phase 0, this
lane's template).

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed artifact, or arithmetic on the two. Nothing here is
revised after a solve; §6's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` §0 (precondition P1). Verified here:
`git merge-base --is-ancestor bdfb3095 origin/main` → **yes**; `origin/main` is **170 commits**
past it at PRECOMMIT time. **THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything on `main`
after it is recorded as post-pin, never retro-fitted and never used to re-read a result. My
keys are therefore **pre-fingerprint keys** (capx D79 entered `cache_key()` after the pin);
the pin records them and §2 lists them.

## 0.1 Bottom line before any LP

1. **THIRTEEN OF THIRTEEN CHARTERED CASES SURVIVE PHASE 0. NOTHING IS KILLED.** That is the
   exact inverse of the ERCOT lane, which killed two, and both inversions are measured rather
   than assumed: `VOL-MID` is in the **escape regime in all five years** on PJM (§3), and
   `CAP-STATE-TIGHT` resolves to a **real RGGI cap row in 2027–2030** whose budget my REF's
   estimated covered emissions **exceed at 2030** (§4.2). The charter expected `SLACK (kill)`
   for the cap case; **it does not reproduce, and the case is solved.**
2. **THE STRUCTURAL RESULT OF THIS PHASE 0 IS AN ATTRIBUTE-PRICE CEILING, AND IT RE-WRITES
   WHAT THREE OF MY CASES CAN POSSIBLY DO.** PJM's RPS row sits at its **$45.00/MWh ACP
   ceiling in every REF year** (`rps_dual` 45.0, 2026–2030; `STATE_RPS_ACP["PJM"] = 45.0`).
   The entry and retirement screens read `max(EAC, RPS dual, clean dual)` — never a sum
   (`new_entry.py:1205`). So on PJM:
   - the CES **premium** ladder {10, 20, 30} is **strictly dominated** for wind/solar and
     cannot move VRE entry at all; its only deployment channel is **nuclear** (never RPS
     eligible, CES credit 1.0) and **gas_cc_ccs** (0.95);
   - **the voluntary row's deployment channel is provably inert on PJM** — ruling S10's
     eligible set is renewable-only, every one of those fuels already earns $45, and both
     ceilings ($4.5 / $7.0) are 6–10× below it. `VOL-*` can act **only through dispatch**;
   - **`CES-T80` is the one case that raises VRE entry economics**, and by exactly
     **+$5.00/MWh**: its dual is the ACP **$50.00** in the escape regime (§6.3), against the
     RPS's $45.
   None of this is a residual reading; it is three committed tables and one `max()`.
3. **PJM's REF is adequacy-short but NOT energy-short**, which is what makes this lane
   campaign-grade where ERCOT's is not: **no unserved energy in any year** (I3 PASS), against
   I7 + I12 FAIL in all five. Gate **G2** asserts that state rather than discovering it, and
   declares the two consequences: price *levels* from 2028 are scarcity-inflected (the
   $2,000 cap is reached in 21 / 8 / 139 hours) and the **deployment response is attenuated
   by construction**, because leg 6 measured the rate-capped backstop at its cap in every year.
4. **The inherited G-DRIFT holds and no control solve is earned** (§5). The one hunk that is
   LIVE for a PJM forecast leg — capx **D75-R-ARM** — landed **after** THE PIN, so arm and
   control are both pre-arm and the confound cannot enter a delta.
5. **`CARB-MID+LOAD-HI` HAS NO PAIRING BASE AT THE PIN, AND I SAY SO BEFORE I SOLVE IT.**
   RESOLVE stopped at leg 6/13; **PJM's `LOAD-HI` was never re-solved** (§1 P2a). Its
   committed bundle is the pre-fix one, and D77+D65-B are the opposite of inert on PJM
   (CCS 3.50 → 14.81 TWh at 2030). The case is still solved — but it is differenced against
   **REF and `CARB-MID`, both at the pin**, never against the pre-fix `LOAD-HI`.
6. **The first solve is HELD on rule 12** (P4): two other SCN policy lanes are running and I
   would be the third. §8.

---

## 1. Preconditions — verified, with one unmet and one charter correction confirmed

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE's re-solved PJM REF on main with G1 PASS | **MET** | `9ef06cf8` (leg 6/13) — **all five gates PASS**; G1 on 1/6/6 converted units to 1e-9; 2026/2027 reproduce the pre-fix bundle to the digit on CO2 (373.1949, 393.6752) and price (41.711, 42.193). Desk r#17 records PJM policy as UNBLOCKED. |
| **P2** | the REF leg is at the `-r2` path | **MET — and the v6 correction is confirmed against the tree** | `results/scn-campaign-load-2026-09-06-r2/PJM/REF/`, key **`67a786980ac38749`**, sidecar `frontend/data/hindcast/pjm-2026-2030-scn-campaign-load-2026-09-06-ref.json`, 5/5 years, `total_wall_s` 2,597.5. The un-suffixed `…/PJM/REF/` still holds the **pre-fix** bundle at the pin (leg 6 deletes it in a post-pin commit) — exactly the hazard v6's P2 names. **REF is never re-solved.** |
| **P2a** | *(not a charter clause — recorded because the charter assumes it)* PJM `LOAD-HI` at the pin | **NOT MET** | RESOLVE is 6/13; legs 7+ (PJM LOAD-HI, CAISO ×3, MISO ×3) have not run. The committed `LOAD-HI` is pre-fix, key `94061c158317a8a5`; the pin key would be `d1da885b4fdc4e6b`. Consequence handled in §0.1(5) and §6.5; routed §9. |
| **P3** | the carbon form is the committed RFF path ladder | **MET at the pin** | `configs/scenario_campaign_matrix.yaml` at `bdfb3095`: `CARB-LO/MID/HI` → `carbon_price_path: low/mid/high`; `ALL-CLEAN` → `mid`. Resolved values measured in §4.1 and reproduce the YAML's declared PJM table to the cent. |
| **P4** | rule 12 concurrency (ruling S14: ~2 concurrent) | **NOT MET — first solve HELD** | The session listing shows **SCN-WS5A policy NYISO** and **SCN-WS5A policy NEISO** both RUNNING alongside this lane. I would be the **third** SCN-track lane, and PJM is the campaign's heaviest non-per-plant ISO (**8,878.7 MB peak RSS**, 2,597.5 s for five years on the REF alone). The desk's own launch order puts PJM fourth. §8. |
| **P5** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` exist | **MET, and IN scope for PJM** | Both live at the pin. PJM **is** in `CAP_AND_TRADE_PROGRAMS` (partial RGGI), so the case is not byte-identical to REF — §4.2 measures the fallthrough and the binding test. |

## 1.1 The constant families this lane consumes (desk standing change #1)

All read at **THE PIN** `bdfb3095`, verbatim:

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `policy/carbon.py` | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | keys `CAISO`, `NYISO`, `NEISO` — **PJM absent** (so PJM carries no state carbon *price*, only the RGGI *program*) |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NYISO`, `NEISO`, **`PJM`** (RGGI, fractional `zone_share`) |
| `RGGI_MEMBER_STATES_BY_YEAR` | `policy/cap_and_trade.py` | keyed {2021, 2023, 2024, 2025}; 2025 onward = {CT, DE, MA, MD, ME, NH, NJ, NY, RI, VT} — **VA left after 2024**. ∩ PJM = **{DE, MD, NJ}** |
| `STATE_RPS_ACP["PJM"]` | `config/capacity_market.py` | **45.0 $/MWh** — the ceiling §0.1(2) turns on |
| `RPS_ELIGIBLE_FUELS_BY_ISO["PJM"]` | `config/capacity_market.py` | **`None`** → the universal wind+solar convention; **nuclear is never RPS-eligible** (CX-6a) |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; **mid {2023: 0.08}; high {2023: 0.08}** |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; **mid {2026: 0.5}**; **high {2026: 1.0}** |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5**; **high 7.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built; **PJM dispatches only wind + solar** |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["PJM"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = 1.0 |
| `DATACENTER_ADDITIONS_MW["PJM"]` | `config/constants.py` | mid **and** high identical at every anchor: {2026: 11,479; 2030: 38,815; 2035: 68,977; 2046: 87,194} MW |
| `DEMAND_GROWTH_RATES["PJM"]` | `config/constants.py` | mid {near 0.064645, long 0.023830}; high {near 0.107742, long 0.039717} |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}; ACP $50/MWh |
| federal CES row credits | `policy/federal_ces.py` | nuclear/wind/solar/hydro/geothermal/offshore_wind/hydrogen = 1.0; **`gas_cc_ccs` = 0.95** |

**The DC axis is degenerate on PJM.** `high` equals `mid` at *every* anchor, so
`LOAD-HI` ≡ `LOAD-HI-ORGANIC` and `CARB-MID+LOAD-HI`'s load half is the **growth** axis alone
(§3.1 measures the two demand paths and confirms it). This is the reason PJM's ORGANIC arm was
never spent in Stage A-LOAD, and it means no DC attribution is readable from this lane.

---

## 2. The case set at THE PIN — resolved fields and cache keys

Resolved exactly as `runner.run_scenario_iso` does: `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults`,
then `config.cache_key()`. Base: `configs/scenarios/pjm_scenario_base_2026_2030.yaml`.

**Chain validation.** The resolved `REF` key is **`67a786980ac38749`** — *identical to the
`cache_key` the committed r2 REF bundle records*, and to RESOLVE §3's declared PJM PIN key.
The chain used below is therefore the one the solve will use, not a naive `cache_key()`.

| case | key at THE PIN | override vs REF | verdict |
|---|---|---|---|
| *REF (control, not solved)* | `67a786980ac38749` | — | **reused** (§5) |
| `CARB-LO` | `69a2199c1d2bffd6` | `carbon_price_path: low` | **SOLVE** |
| `CARB-MID` | `055ad9fc2202d385` | `carbon_price_path: mid` | **SOLVE** |
| `CARB-HI` | `0a63b91706bac093` | `carbon_price_path: high` | **SOLVE** |
| `CES-P10` | `dccf5c2aa49ded42` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `ba6202d729de037d` | premium 20.0 | **SOLVE** |
| `CES-P30` | `f4aa44cf47216299` | premium 30.0 | **SOLVE** |
| `CES-T80` | `6afe42c8d8bef012` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CARB-MID+LOAD-HI` | `664bf9cf053e7c6f` | carbon mid + growth high (+ DC high, degenerate) | **SOLVE** |
| `VOL-MID` | `c0b963f080625cb0` | `voluntary_clean_demand_path: mid` | **SOLVE — §3.2** |
| `VOL-HI` | `cbdafe9626b105a1` | `voluntary_clean_demand_path: high` | **SOLVE** |
| `CES-P20+VOL-HI` | `3259a892ac876177` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `a116292f8cdb8695` | carbon mid + growth/DC high + CES target + ACP 50 + voluntary high | **SOLVE** |
| `CAP-STATE-TIGHT` | `50da3e27a4298ba2` | `mass_cap_enabled`, `mass_cap_program: co2`, `state_carbon_pricing`, `carbon_price_path: zero`, the schedule | **SOLVE — §4.2** |
| *(`LOAD-HI`, not in this lane's set)* | `d1da885b4fdc4e6b` | growth/DC high | pairing base, **UNSOLVED at the pin** (P2a) |

**Every case keys distinctly**, so no leg can collide with another or with a pre-fix bundle.

**13 legs to solve, 65 solve-years.**

---

## 3. Phase 0 — the voluntary row, per year, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed —
`load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`, the runner's own
chain — not by re-deriving the memo's arithmetic. Zone list: the 8 PJM zones, no import node.

### 3.1 The resolved volumes (TWh)

| case | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| REF / all non-VOL mid-growth | `E_total` | 921.217 | 980.769 | 1,044.171 | 1,111.672 | 1,183.536 |
| | `E_DC` | 85.473 | 136.359 | 187.245 | 238.131 | 289.016 |
| `VOL-MID` | **V** | 109.596 | 135.732 | 162.176 | 188.949 | 216.070 |
| `VOL-HI`, `CES-P20+VOL-HI` | **V** | 152.332 | 203.911 | 255.799 | 308.014 | 360.578 |
| `LOAD-HI` / `CARB-MID+LOAD-HI` / `ALL-CLEAN` | `E_total` | 997.309 | 1,104.761 | 1,223.790 | 1,355.644 | 1,501.704 |
| | `E_DC` | **85.473** | **136.359** | **187.245** | **238.131** | **289.016** |
| `ALL-CLEAN` | **V** | 158.420 | 213.831 | 270.168 | 327.532 | 386.031 |

`E_DC` is **identical** between the mid and high demand paths in every year — the degeneracy
of §1.1 measured on the runner's own demand rather than argued from the constants table.

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — every arm binds, nothing is killed

Eligible generation `G` = wind + solar as dispatched in the paired baseline (PJM's committed
fuel keys are `biomass, coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro, import, nuclear, oil,
solar, wind` — no offshore wind, no geothermal). `G_REF` from the r2 REF; `G_LOAD-HI` from the
committed `LOAD-HI` (pre-fix — its VRE rows are unaffected by the CCS repair, and 2026–2028 are
identical to REF's anyway).

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` | 53.060 | 53.060 | 53.060 | 64.609 | 67.106 |
| `G_LOAD-HI` | 53.060 | 53.060 | 53.060 | 63.206 | 67.106 |

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | 109.6 > 53.1 (**−56.5**) | 135.7 > 53.1 (**−82.7**) | 162.2 > 53.1 (**−109.1**) | 188.9 > 64.6 (**−124.3**) | 216.1 > 67.1 (**−149.0**) | **ESCAPE, all five years** |
| **`VOL-HI`** / **`CES-P20+VOL-HI`** vs `G_REF` | 152.3 > 53.1 (−99.3) | 203.9 > 53.1 (−150.9) | 255.8 > 53.1 (−202.7) | 308.0 > 64.6 (−243.4) | 360.6 > 67.1 (−293.5) | **ESCAPE, all five years** |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | 158.4 > 53.1 (−105.4) | 213.8 > 53.1 (−160.8) | 270.2 > 53.1 (−217.1) | 327.5 > 63.2 (−264.3) | 386.0 > 67.1 (−318.9) | **ESCAPE, all five years** |

**NOTHING IS KILLED, AND THE MARGIN IS NOT CLOSE.** Even `VOL-MID`'s thinnest year demands
**2.07×** the eligible fleet's entire output. PJM's eligible fleet is 5.8 % of its energy
(53.1 TWh of 921.2) where ERCOT's is 33 %, which is the whole reason ERCOT's `VOL-MID` was
slack in all five years and PJM's escapes in all five. **The inversion is a fleet fact, not a
level change** — the volumes come from the same two committed cells (S9) in both lanes.

### 3.3 The WTP ceiling — bounded per arm (charter v6's G7, applied)

`voluntary_wtp_ceiling_usd_per_mwh` ships `None`, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. Measured on the resolved configs: **`VOL-MID`
→ $4.50/MWh**; **`VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN` → $7.00/MWh**. Unlike the ERCOT lane,
**both committed cells are live here**, because `VOL-MID` survives — so G7 is genuinely
per-arm on PJM rather than uniformly $7.

### 3.4 The consequence the ceiling has for deployment — provable before any LP

The row's dual reaches entry and retirement through
`max(effective_eac_price_for_tech, rps_credit_for_zone, clean_credit_for_zone)`
(`model/capacity_evolution/new_entry.py:1205`; `retirements.py:3530`) — **a max, never a sum**
(one certificate, FFR-6B §6.4). Ruling S10's eligible set is `(wind, solar, offshore_wind,
geothermal)`, of which PJM dispatches wind and solar; **both already earn the RPS dual of
$45.00/MWh in every REF year**. $7.00 < $45.00 and $4.50 < $45.00.

⇒ **The voluntary axis has NO deployment channel on PJM, in any year, in any of its four
arms.** Its only channel is dispatch: recovering curtailed eligible MWh where the recovery
costs less than the ceiling. This is pre-registered as prediction **P-12** and gate **G8**.

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

**Reproduces the campaign YAML's declared ERCOT/PJM/MISO table to the cent** — gate **G1** on
the carbon axis, passed before any LP. The 2026 knot is $0 in every path, so **2026 is
byte-identical to REF in all five carbon-bearing arms** (gate **G1a**). PJM's RGGI program
resolves a `price_adder` of **0.0** in every REF year, so the S2 floor binds on the *path* side
here and the ladder's sign is unambiguous — PJM is one of the three ISOs where the carbon axis
is live at all.

### 4.2 `CAP-STATE-TIGHT` on PJM — the fallthrough measured, and the case is NOT killed

**(a) The fallthrough is real, and it is the published REGIONAL budget.** `resolve_carbon_program`
returns a `MassCapSpec` for **2027–2030** and `None` for 2026; `scheduled_power_sector_budget`
returns `None` in every year, because the S12 schedule names NYISO / NEISO / CAISO only and PJM
falls through to `_published_power_sector_budget`. Measured cap, metric tonnes:

| year | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `cap_tons` | **none (no row)** | 57,334,075.568 | 55,701,143.036 | 54,068,210.504 | 52,525,996.446 |

So **2026 is byte-identical to REF** in this arm (no row is built) and 2027–2030 carry a real
RGGI cap. This confirms SCN-CAP §5 item 1 by measurement.

**(b) The cap covers only the RGGI-member fraction of PJM.** `_membership` returns
`[0, 0, 0, 0, 0, 0, 0.7221, 0.9976]` over
`[ComEd, AEP_Ohio, ATSI, West_APS, Central_PA, Dominion, EMAAC, SWMAAC]` — Dominion's 0.9881
share is a **2023** entry and VA's exit drops it to 0.0 from 2024. PJM runs `use_campd_bins`,
so `per_generator_membership` overrides that zone fallback per plant against
`{DE, MD, NJ}`.

**(c) The binding test — and why it does not kill the case.** Covered emissions are not in the
slim artifacts, so I estimate them from the covered share of PJM's EIA-860 summer fossil
capacity in `{DE, MD, NJ}` combined with the REF's own per-fuel generation:

| fuel | covered MW | other MW | covered share |
|---|---|---|---|
| coal | 1,284.6 | 34,390.7 | **0.036008** |
| gas_cc | 11,562.7 | 47,993.8 | **0.194147** |
| gas_ct | 4,184.8 | 22,583.4 | **0.156335** |
| gas_st | 1,916.9 | 7,600.3 | **0.201414** |
| oil | 1,746.7 | 3,533.0 | **0.330827** |

Per-fuel rates are recovered from the REF trajectory itself (bounded least squares on the five
years' `co2_mt` against `generation_by_fuel_mwh`; max reconstruction error **1.77 Mt**, 0.4 %):
coal 0.999, gas_cc 0.402, gas_ct 0.518, gas_st 0.750, oil 0.950 t/MWh — all inside the
independently measured 2030 rates the PJM load FINDING §4 published (coal 1.0301, gas_cc
0.3885, gas_ct 0.5421).

| year | REF CO2 Mt | **est. covered Mt** | covered share | budget Mt | budget − covered |
|---|---|---|---|---|---|
| 2027 | 393.675 | **40.2** | 10.2 % | 57.334 | **+17.1 (slack)** |
| 2028 | 417.380 | **45.4** | 10.9 % | 55.701 | **+10.3 (slack)** |
| 2029 | 429.951 | **49.0** | 11.4 % | 54.068 | **+5.1 (slack)** |
| 2030 | 463.039 | **54.0** | 11.7 % | 52.526 | **−1.4 (BINDS)** |

Three independent estimators (a hand calculation on the load FINDING's published rates, an
unconstrained NNLS fit, and the bounded fit above) put 2030's covered emissions **1.4 to 3.6 Mt
ABOVE the budget**, i.e. 2.7–6.9 % over, while agreeing that 2027–2029 are comfortably slack.
The gap closes monotonically — +17.1 → +10.3 → +5.1 → −1.4 — because PJM's covered zones are
gas-heavy and gas grows while the budget declines.

**The case therefore survives phase 0.** Rule 29 clause 0 kills only on a **proven** identity,
and the identity is not merely unproven here: the best available estimate says the row **binds
at 2030**. The estimator's one assumption is that each fuel's capacity factor is uniform across
zones; for 2030 to be slack after all, covered gas-CC would have to run about **10 % below** the
ISO-average gas-CC capacity factor. That is possible and it is not provable from a committed
artifact — which is exactly why the year is solved rather than argued.

**This contradicts the charter's stated expectation** (*"the PJM lane runs the phase-0 binding
test and expects SLACK (kill)"*). Recorded as a phase-0 finding, not a deviation: the charter
asked for the test, and the test says solve.

---

## 5. G-DRIFT (rule 29(b)) — the control is the committed REF, and no control solve is earned

### 5.1 `1cc45bb2 .. bdfb3095` — inherited, and PJM's LIVE set re-verified here

RESOLVE §1 classified 34 non-merge solve-path commits: **4 LIVE** (capx D77, D65-B ISO-wide;
D67-ARM, D81 **PJM only**) and 30 INERT with a stated reason. For PJM all four are live in
principle — and **leg 6 measured the two PJM-only ones INERT on the REF pair** (every capacity
row identical in all five years, because the rate-capped backstop is clamped at a −16 % reserve
margin whichever requirement operand it tests). I do **not** inherit that as a general finding:
the charter's own instruction is to re-measure it on any case that moves the margin, and
`CARB-MID+LOAD-HI` and `ALL-CLEAN` move it hard (peak +14.3 → +59.9 GW). That re-measurement is
pre-registered as **P-18**.

**Form 4 is VALID for PJM.** The control is the **r2 REF, solved at THE PIN itself** — not a
pre-pin bundle — so D77, D65-B, D67-ARM and D81 are on *both* sides of every delta this lane
reports and cannot enter one. This is a stronger position than ERCOT's, which had to argue an
empty retrofit ledger. **No control solve is spent, and REF is never re-solved** (P2).

The one exception is `CARB-MID+LOAD-HI`'s load half: its natural control, `LOAD-HI` at the pin,
does not exist (P2a). **It is differenced against REF and against `CARB-MID`, both at the pin**
— which gives the joint (carbon × load) response and the load-under-carbon response cleanly, and
leaves only carbon-under-high-load unmeasurable until RESOLVE leg 7 lands. Stated, not absorbed.

### 5.2 `bdfb3095 .. origin/main` — for the record; I solve at THE PIN regardless

`git diff bdfb3095 origin/main` over the rule-29 window: **18 files, +1,812 / −59, across 8
non-merge commits.**

| commit | what | verdict for a PJM forecast leg |
|---|---|---|
| `6164231e` | capx **D75-R-ARM** — `pjm_vre_accreditation_vintage` armed for PJM via `_pjm_config.default_scenario_overrides` (owner Q55) | **LIVE at HEAD — INERT at THE PIN.** Measured at the pin: `pjm_vre_accreditation_vintage = False`. It is post-pin, so arm and control are both pre-arm. **My results are the pre-D75-R-ARM posture and must be read as such.** |
| `486c115f` | constants facade re-export of two D75-R names | INERT — names only, no behaviour. |
| `7ff10b64` | `ruff format` on the miso-231 files | INERT — AST-identical, verified at landing. |
| `14ae4d76` | miso-231 hourly neighbour-anchored MISO↔PJM seam ladder | INERT — new field default off, and MISO-scoped (`_inject_seam_ladder` is byte-identical unarmed). |
| `cd96fa26` | pjm-167 F2 interface-feed admissibility gate | INERT — the field **does not exist at the pin**; at HEAD it is default `False` and backcast-facing. |
| `beb74f0f` | pjm-167 F1 EIA-860 vintage tracks the solved year | INERT — **absent at the pin**; at HEAD default `False` and its branch is `mode=="backcast" or hindcast`, neither true here. |
| `16210868` | capx D79 phase 1 — the solve-surface fingerprint enters `cache_key()` | **Key-only, zero key moves at landing.** My pin is pre-D79, so §2's keys are the pre-fingerprint keys. |
| `bf97317f` | capx D78-R2 step 0 — delete `exempt_unit_ids`, restate T3 | INERT — D78's seam needs `retirement_sector_gate` **and** a clearing-armed ISO. Measured at the pin: PJM has the clearing (`{'PJM': True}`) but `retirement_sector_gate = False`. |

**One LIVE hunk on the HEAD window, and it is post-pin — so it changes nothing about this
lane's internal consistency and earns no control solve under clause (b).**

---

## 6. What each leg is expected to do — pre-registered, from measured responses

Sources, all measured before this lane and none of them a residual: **WS-1b §3.4** (the PJM
2027 carbon pair), **WS-2b §3** (the CES premium ladder, on ERCOT — mechanism only, never a
level), **WS-3b §6** (the voluntary row's arithmetic), **the PJM load FINDING** and the
committed r2 REF itself.

### 6.1 The REF-side facts every prediction rests on

`clean_share` (wind+solar+nuclear+hydro over total generation) **0.3682 / 0.3458 / 0.3246 /
0.3153 / 0.2980** — *falling*, because load outgrows clean entry. `rps_dual` **45.0 in every
year** (the ACP ceiling — the RPS row is itself in escape). CO2 **373.195 / 393.675 / 417.380 /
429.951 / 463.039 Mt**. `unserved_mwh` **0 in every year**.

### 6.2 Carbon — sign, ordering, magnitude

**P-1 (the cross-lane anchor, and it is deliberately NOT claimed as an identity).** WS-1b §3.4
measured PJM 2027 on a *different* base (`scn-ws1-probe`, 2026–2027): REF 393.6225 Mt / $42.385,
CARB(+$3.75) 380.1844 Mt / $44.534, **ΔCO2 −13.4381 Mt (−3.41 %)**, Δprice **+$2.149**,
Δimport CO2 **+0.4336 Mt**. My campaign REF's 2027 is **393.6752 Mt / $42.193** — 0.053 Mt and
$0.19 apart, *close but not identical*, so unlike the ERCOT lane I claim a **band, not a
digit**: `CARB-MID` 2027 ΔCO2 in **[−11.0, −16.0] Mt** and Δ`lw_price` in **[+1.8, +2.5]**.
Scoring the ERCOT lane's identity claim on a non-identical base would have been a false hit.

**P-2.** All three carbon arms' **2026 is bit-identical to REF** — `co2_mt` 373.1949,
`lw_price` 41.711, every fuel row to 1e-6. (Gate G1a.)

**P-3.** CO2 falls and price rises monotonically REF → LO → MID → HI in each year 2027–2030;
2026 flat.

**P-4.** The mechanism is coal→gas-CC, with **every zero-carbon class moving exactly 0.0000
TWh** — WS-1b measured hydro/nuclear/solar/wind at exactly 0.0000 on this ISO. Gate G3.

**P-5 (PJM's elasticity is the campaign's largest, and I do not repeat WS-1b's mistake).**
WS-1b's own band was 2.3× too small because it assumed low elasticity; the measured mechanism is
a **narrow spread** ($3.98/MWh on coal vs $1.54 on gas-CC at $3.75/t ⇒ a ~$2.44/MWh relative
shift) sitting inside a dense mass of PJM coal. Scaling that: `CARB-LO` 2027 ($2.00/t, a
~$1.30/MWh relative shift) **−5 to −10 Mt**; `CARB-HI` 2027 ($7.50/t, ~$4.88/MWh)
**−22 to −34 Mt** — **sub-linear in both directions** as the cheap swaps are exhausted.

**P-6.** ΔCO2 **grows** in absolute terms 2027 → 2030 in every carbon arm (unlike ERCOT, where
scarcity saturates it), because PJM sheds no load and the carbon price quadruples. At
`CARB-HI` 2030 ($30/t) I expect **−60 to −110 Mt**, the campaign's largest single policy
response.

**P-7.** `gas_cc_ccs` **rises** in the carbon arms from 2028 — PJM already carries 2,248.7 MW /
14.805 TWh at REF 2030 on §45Q alone, and a carbon price adds to the retrofit's screened uplift.
At `CARB-HI` 2030 I expect **> 2,248.7 MW**, and I expect the 3 GW/yr per-ISO cap to be the
binding constraint rather than the economics.

**P-8 (the leakage duty, WS-0 §4).** `import_co2_mt_reported` **rises** in every carbon arm —
PJM's import tranches pay no border carbon, so they get relatively cheaper. WS-1b measured
**+0.4336 Mt** at 2027 on $3.75/t (3.2 % of ΔCO2). REF's import generation grows 0.279 → 13.707
TWh, so I expect the leakage line to reach **+1.5 to +4.0 Mt** at `CARB-HI` 2030 — still a
single-digit percentage of ΔCO2, and reported beside every CO2 number, never netted into it.

### 6.3 CES — the ladder is expected to be NEARLY INERT, and the target is not

**P-9 (the sharpest structural call in this PRECOMMIT).** **`CES-P10`, `CES-P20` and `CES-P30`
commission essentially identical wind and solar, and essentially identical to REF's.** The
premium enters `max(EAC, RPS dual, clean dual)` and PJM's RPS dual is **$45.00** in every year;
10, 20 and 30 are all strictly below it. Measured as: `builds_renew_mw` within **±5 %** of REF's
(0 / 0 / 0 / 6,000 / 1,500 MW) in all three arms and all five years. **This is the opposite of
WS-2b's ERCOT ladder** (14.0 GW solar + 10.0 GW wind commissioned), and the reason is one number
ERCOT does not have.

**P-10.** The premium's response therefore appears **only** on RPS-ineligible eligible fuels —
**nuclear** (credit 1.0, `RPS_ELIGIBLE_FUELS_BY_ISO["PJM"] = None` ⇒ wind+solar only, and
nuclear is refused by name) and **gas_cc_ccs** (0.95). Concretely: `retire_mw` of nuclear stays
0 (it already is), and I expect any separation between P10/P20/P30 to show up as **`gas_cc_ccs`
capacity rising with the premium** from 2028 and/or nuclear entry. If P10 → P30 moves *nothing*
anywhere, that is a clean null and it is reported as one.

**P-11 (`CES-T80`, gate G4).** The target ramps **0.5500 / 0.5778 / 0.6056 / 0.6333 / 0.6611**
(linear 2026:0.55 → 2035:0.80). REF's **credited** share — nuclear + wind + solar + hydro +
0.95 × `gas_cc_ccs`, over the LP's own demand — is **0.3686 / 0.3462 / 0.3270 / 0.3263 /
0.3106**, i.e. *falling while the target rises*. The row is in the **escape regime in every
year**: dual = ACP **$50.00/MWh exactly**, escape MWh = `target(y)·D − credited` ≈
**167.1 / 227.1 / 290.9 / 341.3 / 414.8 TWh**. Same regime WS-2a measured on its NEISO T0 pair.

**P-12.** Because $50.00 **exceeds** the $45.00 RPS ceiling, `CES-T80` is the **one** case in
this lane that raises VRE entry economics — by exactly **+$5.00/MWh**, an 11 % uplift. I predict
it commissions **more** renewables than REF and than any premium arm, and that this is the
lane's only positive VRE-entry reading. Magnitude not predicted (the queue caps may bind).

### 6.4 Voluntary — a dispatch-only axis, pre-registered as such

**P-13 (gate G7).** In **every year of all four voluntary arms** the row escapes: dual =
**$4.50/MWh exactly** on `VOL-MID` and **$7.00/MWh exactly** on `VOL-HI`, `CES-P20+VOL-HI` and
`ALL-CLEAN`; escape MWh = the §3.2 shortfall, less whatever dispatch recovers.

**P-14 (the deployment null, from §3.4).** `retire_mw`, `builds_renew_mw`, `builds_thermal_mw`,
`builds_storage_mw` and `capacity_by_fuel_mw` are **identical to REF to 0.1 MW in all five
years** in `VOL-MID` and `VOL-HI`. This is a **provable** consequence of the `max()` seam, not
an expectation, and if it fails the seam has a defect this lane must report rather than explain.

**P-15 (gate G8).** The only dispatch channel is recovering curtailed eligible MWh at ≤ the
ceiling. REF's implied CFs (wind 29.764 TWh on 11,000 MW = 0.309; solar 23.296 on 14,000 =
0.190) and `neg_price_hour_frac = 0.0` say there is very little curtailment to recover, so I
predict **|Δwind + Δsolar| < 0.5 TWh** and **|ΔCO2| < 1.0 Mt** in every year of `VOL-MID` and
`VOL-HI` — an axis that is *nearly* inert on PJM without being byte-identical. The escape
column carries the cost instead: ≈ **$0.67 B/yr** at `VOL-MID` 2030 and **$2.05 B/yr** at
`VOL-HI` 2030, which is the arm's real content.

### 6.5 The combined legs — both nettings (ruling S11), and one honest gap

**P-16.** `CES-P20+VOL-HI` composes two dominated prices ($20 and $7) under a $45 ceiling, so
D-6 has **no dispatch content and no deployment content** on PJM. I expect it to be
indistinguishable from `VOL-HI` on every capacity row and within P-15's band on dispatch. Both
nettings are still reported (G9) — the point is that the composition is *observably* empty here,
which is itself evidence for D-6.

**P-17.** `ALL-CLEAN` is the one arm where D-6 has content: a CES **target** row (dual $50) and
the voluntary row (dual $7) both count a clean MWh. Both nettings reported side by side, CES dual
under each; **counts-toward is the headline** (as built), **additional** beside it, computed at
the report layer as `federal_credited − V ≥ target(y)·D` with implied escape
`max(0, target·D + V − federal_credited)` at the ACP. Neither asserted as the answer.

**P-18 (the D67-ARM/D81 re-measurement the charter requires).** Leg 6 measured that confound
INERT on the REF pair *because the backstop was clamped*. `CARB-MID+LOAD-HI` and `ALL-CLEAN`
drive the reserve margin from −16 % toward −34 %, i.e. **further into the clamp**, so I predict
it stays inert there too — every capacity row moving for load reasons, none for a requirement
reason. If instead a capacity row moves in a direction load cannot explain, the confound is live
and I report it rather than attributing the delta to policy.

**P-19 (`CAP-STATE-TIGHT`, gates G10–G12).** 2026 byte-identical to REF; 2027–2029 slack with
`co2_cap_price` = **0 exactly**; **2030 binding** with covered emissions equal to
**52.525996 Mt** to 1e-6 and a **positive** dual. Because only ~11.7 % of PJM's emissions are
covered, I expect the binding year's dual to be **modest** ($5–40/t) — a 1.4 Mt bite out of a
54 Mt covered pool — and the whole-ISO CO2 to fall by **less than 2 Mt**. The comparison the
case exists for is reported explicitly: that dual against `CARB-*`'s exogenous $15.00 / $30.00
in the same year. *This is the prediction I most expect to be wrong*, because it rests on the
§4.2(c) estimate rather than on a measured covered total.

---

## 7. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1 carbon table = the YAML's declared PJM table to the cent; §3.1 volumes from the runner's own demand chain; REF key `67a786980ac38749` = the committed bundle's. **Already PASS, pre-solve.** |
| **G1a** | every carbon-bearing arm's **2026** is bit-identical to REF | `co2_mt` 373.1949, `lw_price` 41.711, full `generation_by_fuel_mwh` to 1e-6. Also asserted for `CAP-STATE-TIGHT` 2026 (no row is built). |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries the adequacy state leg 6 measured: **`unserved_mwh` = 0 in every year**, reserve margin −0.0947 → −0.1635, FAIL set exactly `{I7, I12}`, `hours_ge_500` 0 → 139, `max_hourly_price` at the $2,000 cap from 2028. **Consequences, declared now:** (a) CO2 and dispatch **deltas are campaign-grade in all five years** — this is not ERCOT; (b) **price levels from 2028 are scarcity-inflected and disclosure-only**, deltas readable, levels not; (c) **deployment responses are attenuated by construction** — the rate-capped backstop is at its cap in every year, so every capacity response is a **lower bound**; (d) PJM's CO2 **levels** are not quotable against the board key (+18.0 % energy divergence, load FINDING §6). |
| **G3** | **footprint confinement** | *carbon* arms move fossil rows only, every zero-carbon class Δ = 0.0000 TWh; *CES* arms move eligible/ineligible shares + the CES dual; *voluntary* arms move eligible-class rows, thermal rows and the escape column only. The **import line moves in the carbon arms by design** (no border carbon) and is reported, never counted as a confinement failure. |
| **G4** | **`CES-T80` dual identity** | dual = ACP **$50.0000 exactly** in every year the target is unmet; a strictly interior dual only where it is met. Escape MWh = `target(y)·D − credited`. §6.3 says all five years are unmet. |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's `{I7, I12}` FAIL. A new FAIL outside the target mechanism kills the arm. |
| **G6** | **no unserved energy appears where REF has none** | REF has **zero** unserved in all five years, so this binds strictly on `CARB-*`, `CES-*`, `VOL-*` and `CAP-STATE-TIGHT`: any `unserved_mwh > 0` kills the arm. It does **not** bind on `CARB-MID+LOAD-HI` / `ALL-CLEAN`, which raise load by construction (the pre-fix `LOAD-HI` gained I3 from 2027). |
| **G7** | voluntary dual bounded, **per arm** | where the row binds: dual > 0 and ≤ **that arm's own** ceiling — **$4.50** on `VOL-MID`, **$7.00** on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`; where it escapes: dual = that ceiling **exactly** and escape MWh = the shortfall. |
| **G8** | **curtailment before thermal** | in the first binding year: Δcurtailment of eligible resources < 0 and \|Δcurtailment\| ≥ \|Δ fossil generation\|. On PJM every year is a binding year, so this is asserted at **2026**. |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as headline, additional beside it, CES dual under each — never one alone (ruling S11). |
| **G10** | **`CAP-STATE-TIGHT` cap identity** | in every binding year covered emissions equal the budget to **1e-6** and `co2_cap_price` > 0; in a slack year the dual is **0 exactly**. 2026 has no row and must be byte-identical to REF. |
| **G11** | **one instrument at a time** | `carbon_price_path: zero` resolves to the STATE program only (never a federal price) and the mass-cap ROW **replaces** the adder where `state_carbon_pricing: true`. Verified pre-solve: `resolve_carbon_program` returns `price_adder=None` with a `cap_spec` in 2027–2030, and `price_adder=0.0` with `cap_spec=None` at REF. A leg carrying both is a STOP. |
| **G12** | **cap footprint + the price-vs-quantity read-out** | footprint as a carbon case (G3), and `co2_cap_price` reported **beside** `CARB-MID`'s and `CARB-HI`'s exogenous $/t in the same year — the comparison the case exists for. |

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
    --config configs/scenarios/pjm_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/PJM/<CASE>
```

Rebase **between** legs, never during one. Logs to the session scratchpad, never the results
tree. **Cache isolation:** all thirteen keys (§2) are new — no PJM bundle has ever occupied them
— and `results/PJM/` is gitignored and empty in this container, so no stale bundle is reachable.
Registration: kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, one run id per
(ISO, case), with **every invariant FAIL declared in
`frontend/data/hindcast/invariant-failures.json` in the same commit** (the Y-24 ratchet at the
registration seam; the audit is green on SCN today and stays so).

**Budget — and it is the campaign's largest, stated plainly.** 13 legs × 5 solve-years = **65
solve-years**. The r2 REF measured **2,597.5 s** for five years (397 / 132 / 246 / 948 / 874 s —
strongly super-linear, exactly as the load FINDING §1 warned) at **8,878.7 MB peak RSS**. The
high-load arms are heavier still. ⇒ **≈ 45–75 min per leg, roughly 10–15 hours of LP**, one leg
at a time. If the desk wants a smaller spend, the honest place to cut is the CES premium ladder:
§6.3's P-9 predicts P10/P20/P30 are near-identical on PJM, so two of the three could be dropped
to a single P20 — **but that is the desk's call, not mine, and I do not narrow a chartered set
on my own** (I solve all thirteen unless told otherwise).

**THE FIRST SOLVE IS HELD ON RULE 12 (precondition P4).** Two SCN policy lanes — **NYISO** and
**NEISO** — are running now; I would be the third against ruling S14's ~2-concurrent cap, and
PJM is the heavy half of any pair (8.9 GB). The desk's own launch order puts PJM fourth, behind
ERCOT/NEISO and NYISO. **Nothing is solved until the owner opens the slot.** The moment one
opens, all thirteen legs run back to back from this PRECOMMIT with no further preparation.

---

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **PJM's `LOAD-HI` is not re-solved at the pin** (P2a). RESOLVE stopped at leg 6/13, so
   `CARB-MID+LOAD-HI` has no same-pin pairing base and the *carbon-under-high-load* difference
   is unmeasurable in this lane. It is **not** a reason to hold the case (REF and `CARB-MID` are
   both at the pin), but the charter's clause *"LOAD-HI is WS-5A's committed leg at the pin —
   reuse it as the pairing base"* is **false for PJM today**, and the same sentence sits in the
   CAISO and MISO charters, where RESOLVE has run **zero** legs. Those two lanes have no
   re-solved REF at all and are blocked on P1, so the sentence bites hardest there.
2. **The charter's `CAP-STATE-TIGHT` expectation does not reproduce on PJM.** v6 says the PJM
   lane *"expects SLACK (kill)"*; §4.2 measures 2027–2029 slack but **2030 binding** on three
   independent estimators. The case is solved. If the desk wants the binding test settled
   exactly rather than estimated, what is needed is a covered-emissions read-out on the REF
   bundle (per-zone or per-membership CO2), which no committed artifact carries today — a cheap
   reporting addition to `report_scenario_deltas.py`, and not this lane's region.
3. **The desk's own budget arithmetic understates PJM by ~2×.** The load FINDING §9 item 3 said
   so and it is confirmed at the pin: 65 solve-years at 45–75 min/leg is 10–15 h, against the
   campaign's 3.92 min/solve-year average. Any Stage-B sizing that treats PJM at the campaign
   mean will be wrong by a factor of two.
4. **A structural result the desk may want in the plan, not just in my FINDING:** PJM's RPS row
   sits at its $45 ACP ceiling in every forecast year, which **dominates the entire committed CES
   premium ladder and both voluntary ceilings** at the screens' `max()` seam. Two chartered
   axes are therefore near-inert on PJM *by construction*, and the campaign will read that as a
   null unless the reason is carried with it. It also means PJM cannot produce a
   premium-ladder response for the cross-ISO §5.1 rows — ERCOT and MISO can.

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no new case, no solve yet,
  never a year past 2030.** DOF ledger: **zero** free parameters. No `authorized_price_tuning`
  (rule 1's carve-out is a backcast offer-curve channel; untouched by a forecast lane).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the PJM base YAML,
  everything under `src/`, `scripts/run_ces_leg.py`, `scripts/report_scenario_deltas.py`, every
  committed bundle and sidecar, and every other ISO's files. `program-status.json`,
  `ff-verdicts.json` and the whole **backcast** namespace: untouched (§7.5 — this lane registers
  into the forecast namespace only).
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms and the control is a committed one.
- **Backcast byte-identity:** untouched by construction (forecast-mode only, `mode="forecast"`
  on every leg).
- **Rule 28(b):** the PJM shard's `federal_ces_target`, CES-premium, `carbon_price_path`,
  `voluntary_clean_demand` and mass-cap cells are stamped as the **last** commit, after rebase.
