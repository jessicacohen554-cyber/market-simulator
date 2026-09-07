# PRECOMMIT — SPP-57: the Oklahoma pocket as a third zone (P1's first lever)

**Lane** SPP-57 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-57-oklahoma-pocket-yedapf` (stem `claude/spp-57-oklahoma-pocket-m4rt`) ·
**Data profile** `spp` · **Charter** plan §8 W5 SPP-57 (issued r#7; P1 ranking applied r#5) ·
**Predecessors** FINDING-spp-14 §5 / §8.2, FINDING-spp-40 §3 / §7.2, PRECOMMIT-/FINDING-spp-53,
FINDING-spp-32 §2–§3, FINDING-spp-20 §3.

**Pushed before any limit or price is parsed.** Everything below is a topology design, a
construction rule, a membership rule, a direction convention, a gate with its thresholds, or
arithmetic on numbers already committed by earlier lanes (sub-BA loads, EIA-860 capability, the
SPP-53 psi table). Two byte pulls were started in the background *before* this document was
pushed and are disclosed here so nothing is hidden: the 2026 daily RTBM binding-constraint files
(the SPP-53 producer, `spp53/pull_daily.py`, to the session scratchpad) and the EIA-861 zips. **No
value in either was parsed, printed or looked at before the push** — the pulls are minutes long
and were overlapped with the writing; the construction below does not depend on anything in them.
Nothing here is revised after the data is read; a miss of any declared condition is reported at
full magnitude in the FINDING.

---

## 0. THE PIN, the control, and the preconditions

```
40b54ce7   origin/main at PRECOMMIT time (branch cut from it)
```

| precondition | check | result |
|---|---|---|
| SPP-40 landed — keeper-1 exists | `frontend/data/backcast/keepers/SPP.json` → `2026-09-07-spp-1-baseline`; bundle `results/calibration/spp40_baseline_B/` + `hourly/` | **yes** |
| SPP-53 landed (the FCITC construction and the corridor sidecar) | `rtbm_bc_corridor_limits_2026.parquet`, `docs/handoffs/spp53/psi_all.csv` (134 regressors), `_spp_config` link 3,400 MW | **yes** |
| SPP-14 landed (four-group rules, per-hub parquet, `SL_to_Pnode_to_Zone_with_Area.csv`) | `spp14/groups.py`; `actual_lmp_hourly_zonal_SPP.parquet` 52,560 rows; SL map 296,791 rows | **yes** |
| SPP-32 landed (`_SPP_SUBBA_ZONE_GROUPS`, wind shape, gas-hub rows) | in tree | **yes** |
| **SPP-42** (repaired-input re-baseline) | `git ls-remote --heads origin` → no `claude/spp-42*`, `spp-41*` or `spp-36*` head; `git log origin/main --grep=SPP-42` empty | **NOT LANDED, NOT LAUNCHED** at the pin |
| portal serves the 2026 daily BC files anonymously | `fetch_spp_alt_portal.py --list rtbm-binding-constraints /2026/09/By_Day` → `20260901..20260905` | reachable |
| portal serves the monthly RT LMP-by-SL files | `/2023/2023.zip`, `/2024/2024.zip` central directories list 12 `RTBM-LMP-MONTHLY-SL` members each (84 / 86 MB); `/2025/MM/RTBM-LMP-MONTHLY-SL-2025MM.csv` live (27 MB) | reachable |
| EIA-861 `Sales_Ult_Cust` 2023 / 2024 | `archive/zip/f8612023.zip`, `zip/f8612024.zip` answer `206` to a range request | reachable |

**The control (rule 29(b), form 4)** is the keeper CURRENT at this PRECOMMIT: `2026-09-07-spp-1-baseline`,
`git.sha = 4639a309` (`run_config.json`), bundle `spp40_baseline_B`. The charter's instruction —
solve only after SPP-42 lands, because a control whose inputs are about to be repaired makes the
differencing unreadable — is honoured as written: **every zero-LP step of this lane runs now; the
screen solve waits for SPP-42 (or the desk saying it stopped).** If the keeper moves between this
document and the solve, the pin and the G-DRIFT audit below are re-done as an addendum before the
screen runs.

### 0.1 G-DRIFT audit (rule 29(b)) — keeper `4639a309` → `40b54ce7`

```
git diff --stat 4639a309 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

| # | file | hunk | verdict for SPP | reason |
|---|---|---|---|---|
| 1 | `data/raw/_validation-source/caiso-supply-consistent-demand/*` | new CAISO 2022 demand csv + provenance | **INERT** | CAISO-only artifact; no SPP loader path reads it |
| 2 | `scripts/lib/transmission_expansion/spp.py` | docstring only (SPP-35's prose update to the SPP-53 position) | **INERT** | prose; the spec's `IsoSpec` and the empty frame are unchanged |
| 3 | `src/market_sim/config/constants.py` | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` added | **INERT** | CAISO key; SPP's dict entry untouched |
| 4 | `src/market_sim/config/fuel_trajectories.py` | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` + comments | **INERT** | CAISO key; SPP has no carbon program (`CAP_AND_TRADE_PROGRAMS` exclusion, FINDING-spp-20 §4) |
| 5 | `src/market_sim/model/interchange/spec.py` | three CAISO DSW depth dicts + `IMPORT_TRANCHES_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO keys; SPP's `INTERFACE_NEIGHBORS` block byte-identical; SPP has no import node |

**All five hunks INERT ⇒ form 4 is valid: the keeper's committed bundle is the control, and no
control solve is spent.** (If SPP-42 lands, the new keeper becomes the control and this table is
re-run against its sha.)

---

## 1. The object — what the two bubbles cannot hold, and what the third zone is for

FINDING-spp-40 §3 read one object three ways: a 22-hour N↔S direction tie against a 1.7 : 1
N→S-dominant market, a 17× under-separation ($0.99 modelled vs $17.23 measured mean |S−N|), and
7–9 negative-price hours against ~1,000–1,170 with 0.0 % wind re-curtailment. FINDING-spp-14 §5
had already ranked the cause: `oklahoma_internal` is the market's most-binding flowgate group in
every year — 4,713 / 4,698 / 5,822 binding hours (0.538 / 0.536 / 0.665 of 8,760) at $261.55 /
$263.58 / $311.80 mean |shadow| — above the corridor itself (0.555 / 0.516 / 0.631 at $140–227)
and far above the SPS tie. The published South hub (`SPPSOUTH_HUB`, 460 nodes: OKGE 265 + WFEC
105 + CSWS 90, entirely Oklahoma — FINDING-spp-14 §5.1) sits *inside* that group's footprint.

**Two things must be said about the third zone before it is built, so they are not discovered in a
residual.**

1. **A sub-BA-defined Oklahoma zone is the whole state, not the OKC/Tulsa load pocket.** The
   `oklahoma_internal` flowgates are, by SPP-14's own membership rule, constraints whose
   contingency areas are the Oklahoma utilities — and much of what they price is *intra*-Oklahoma:
   western / south-western Oklahoma wind (Anadarko, Gracemont, Woodward, Cimarron) delivered east
   into the OKC / Tulsa load. A bubble that holds OKGE + GRDA + WFEC + PSO holds the wind and the
   load on the same side of those elements, so it cannot trap western-Oklahoma wind *behind*
   Osage–Webber Tap or Gracemont–Anadarko any more than the two-zone model could. What it CAN do
   is the thing the lever is for: bound the **Oklahoma bubble's own exchange** with Nebraska /
   Kansas on one side and with the Panhandle / Arkansas–Louisiana on the other, so that ~13 GW
   of Oklahoma wind plus SPS's exports into Oklahoma meet a ~6–7 GW Oklahoma load with a finite
   pipe out in each direction. The intra-Oklahoma west→east pocket is stated here as the residual
   the three-zone model still cannot hold, and the FINDING reports the share of the group's binding
   hours that identify on *either* zonal spread (the ψ screen, §3) — the measured size of that
   residual, not a number to absorb.
2. **The residual "SPP-South" is two physically disjoint pockets joined by a copperplate.** With
   Oklahoma removed, what remains of the P1 South is SPS (Texas Panhandle + eastern New Mexico,
   west of Oklahoma) and SWEPCO / AECC / ETEC (Arkansas, Louisiana, east Texas, east of Oklahoma),
   which share no transmission except *through* Oklahoma. One residual bubble therefore lets SPS
   wind serve Louisiana load at zero cost. That is the charter's design and it is executed as
   chartered; the misalignment is stated on the OK↔S link (§3.3) and the split of the residual is
   exactly lever **SPP-54**'s object (the SPS pocket, queued behind this lane by the r#5 ranking).
   This lane does not pre-empt it and does not build a fourth zone.

---

## 2. Design (A) — THE POCKET

### 2.1 Zones

| zone | sub-BAs (load) | states (fleet, `_SPP_STATE_ZONES`) |
|---|---|---|
| `SPP-North` | EDE, INDN, KACY, KCPL, LES, MPS, NPPD, OPPD, SECI, SPRM, WAUE, WR (unchanged) | ND SD NE MN MT IA KS MO CO (unchanged) |
| **`SPP-Oklahoma`** (NEW) | OKGE, GRDA, WFEC + **w_OK · CSWS** | **OK** |
| `SPP-South` (residual) | SPS + **(1 − w_OK) · CSWS** | TX NM AR LA |

The plant-side partition is exact at the state line: every PSO plant is in Oklahoma and every
SWEPCO plant in AR / LA / TX (EIA-860 2025 ER, BA `SWPP`, `OP`). WFEC's New Mexico assets fall to
the residual South by the state rule while WFEC's load is counted Oklahoma — a stated
misalignment of the sub-BA-vs-state seam (WFEC's NM share is small; the FINDING prints it from
the census). The coordinate fallback (`_spp_zone`, no FIPS) gains an Oklahoma limb: South tier
below 37.0 N as before; inside it, Oklahoma when the point lies in the Oklahoma state box
(−103.0 ≤ lon < −94.43, lat > 33.62; the Panhandle strip 36.5–37.0 N is inside that box). FIPS
state is the primary key and carries every SWPP plant, so the fallback decides nothing in the
census.

### 2.2 The CSWS sub-allocation — a rule-14 misalignment, closed with a measured value

EIA-930 reports AEP West (`CSWS`) as ONE sub-BA spanning Oklahoma (PSO) and Arkansas / Louisiana /
east Texas (SWEPCO); SPP's own hourly-load files carry the same single `CSWS` column, and SPP's
settlement-location registry does not tag CSWS load SLs by utility (measured: the 7 distinct CSWS
`LOAD` settlement locations are `AEPM_CSWS`, `AECC_CSWS`, `CSWS_ETEC_LOAD`, `GATEWAY_LOAD`,
`GSEC_GL_CSWS`, `OMPA_SPP`, `WFEC_WFEC` — an AEP-West aggregate plus non-AEP members, none of
them PSO-vs-SWEPCO). No published hourly series splits it. The split is therefore a **reconciled
measured value** under rule 14's misalignment clause, declared here before the source is read:

> **w_OK(year) = PSO retail sales / (PSO retail sales + SWEPCO retail sales)**, from EIA-861
> `Sales_Ult_Cust_<year>` — utility 15474 *Public Service Co of Oklahoma* (OK only) and utility
> 17698 *Southwestern Electric Power Co* (AR + LA + TX), `Total` MWh, all `Part`/`Service Type`
> rows summed per utility — for 2023 and 2024. **2025 = hold-last (the 2024 value)**: EIA-861
> 2025 is unpublished at the pin, and the hold-last rule is declared now rather than chosen later.

Applied as an hourly identity: the CSWS MW row is split w_OK : (1 − w_OK) into the two zones in
every hour, then the 17-token normalisation runs unchanged, so Σ_z share = 1.0 every hour and the
redistribution identity (`Σ_z cap_z · cf_z(t) = M(t)`) is unaffected. The static `load_share`
fallback in `_spp_config` is the same weight applied to the same 2023–2025 sub-BA energies
(FINDING-spp-20 §3 basis). **Stated misalignment**: the CSWS sub-BA also carries non-AEP load
(AECC / ETEC → residual South, OMPA → Oklahoma, GSEC ambiguous) whose MW are not separately
published, so the AEP retail split is applied to the whole sub-BA; the direction of that bias is
unknown and is not adjusted. Zero-LP arithmetic already in the tree, for scale (sub-BA hourly
means, 2023 / 2024 / 2025, MW): OKGE + GRDA + WFEC 6,067 / 6,397 / 6,739; CSWS 5,466 / 5,504 /
5,706; SPS 4,011 / 4,178 / 4,308; North 16,495 / 16,930 / 17,432.

### 2.3 Every other registry (design (D), the SPP-20 list) — what each gains and how

| registry | change |
|---|---|
| `iso_configs._spp_config` | three `Zone`s (static shares from §2.2), two `TransferLink`s (§3), the N↔S link **RETIRED** (§3.1) |
| `zone_assignment._SPP_STATE_ZONES`, `_spp_zone`, `_SPP_SEAM_LAT` | OK → `SPP-Oklahoma`; Oklahoma-box limb in the coordinate fallback; `_LARGEST_ZONE["SPP"]` stays `SPP-North` |
| `curate_zonal_shares._SPP_SUBBA_ZONE_GROUPS` + a NEW `_SPP_CSWS_OKLAHOMA_SHARE_BY_YEAR` (hold-last rule in the accessor) | OKGE / GRDA / WFEC → Oklahoma; SPS → South; CSWS split per §2.2; clean `zonal-shares` rows regenerated for 2023–2025 |
| `renewables.RENEWABLE_ZONE_ALLOCATION["SPP"]` | fallback-only: wind → `SPP-Oklahoma` (OK 12,944 MW is the largest state), solar → `SPP-North` (601 MW vs OK 423 / residual 415) — the primary path distributes by plant coordinates |
| `build_spp_wind_shape.py` → `data/raw/spp-wind-shape/spp_<yr>_wind_zone_shape.parquet` | rebuilt for three zones (the site set follows `build_zone_lookup("SPP")`; NASA POWER reachable, `200` at the pin); the redistribution identity re-proved |
| `data/raw/spp_zonal_gas_hub.csv` (+ `meanzero.py` comment) | `SPP-Oklahoma` = the OK proxy rows (N3045OK3, the former South rows, 2022–2024); `SPP-South` residual = **TX proxy** (N3045TX3, the residual's gas-fleet plurality: TX 6,547 of 8,986 MW gas), 2022–2024 only (the intersection rule SPP-32 declared). **Still no applier armed** (no `ScenarioConfig` field, G8) |
| `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` | stays 2026 (the limit vintage of both new links) |
| `interchange/spec.INTERFACE_NEIGHBORS["SPP"]` (default-off blocks) | `border_zones`: MISO → (`SPP-North`, `SPP-South`) unchanged (the MISO seam is Iowa/Minnesota in the North and Arkansas/Louisiana in the residual South — Oklahoma has no MISO border); AECI → `SPP-North` unchanged; ERCOT DC ties → **(`SPP-Oklahoma`, `SPP-South`)**: the DC-North tie (Oklaunion, 220 MW) lands on the Lawton, OK side and the DC-East tie (Monticello, 600 MW) on the SWEPCO east-Texas side, so P3's "border SPP-South" splits across the two bubbles the old South became; the block is default-off and dispatch-inert for the keeper |
| `_validation-source/calibration_reference.json` SPP block | regenerated `build_calibration_reference.py --isos SPP` (its `renewables.*.monthly_capacity_mw` is keyed by zone name); the G9 merge leaves every other ISO's block byte-identical |
| `docs/codebase-site/data/iso-topologies.json` SPP block | three zones / two links (it still carries SPP-20's 48,700 MW; corrected to the live config) |
| `derive_actual_lmp.py` / `actual_lmp.json` zone comment | unchanged — the SPP zonal benchmark is keyed by TRADING HUB, not model zone (SPP-14 §3), and stays so; the scorer's zonal rows are not renamed |
| tests | `test_iso_config.py` SPP cases re-pinned (three zones, two links, shares); `test_zone_assignment.py` (OKC / Panhandle → Oklahoma); `test_curate_zonal_shares_spp.py` (three-zone partition, CSWS split identity); `test_spp_renewable_inputs.py` (three-zone fixtures); `test_spp_zonal_gas_hub.py` (zone set) |

**Zero-LP proofs owed before any solve (design (D) exit):** `get_iso_config("SPP").validate_topology()`;
`solve_surface_register.py --diff origin/main HEAD` → 0 moved for the six keepers (no
`SURFACE_MODULES` file is touched; rule 25); `tests/regression/test_persisted_identity.py` 23/23;
an on-recipe `run_year(fleet_only=True)` census per zone (plants, MW by class, wind / solar MW,
demand TWh) for 2023–2025, printed in the FINDING before the screen.

---

## 3. Design (B) — THE LINKS, and their construction (declared before any limit is read)

### 3.1 Topology: a chain. The N↔S link is RETIRED, not re-rated

`SPP-North ↔ SPP-Oklahoma ↔ SPP-South`, two symmetric `TransferLink`s, no direct North↔South
link. Why retired rather than re-rated:

1. **SPP-53's 3,400 MW was identified on the Nebraska-hub → central-Oklahoma-hub pair** — the
   `SPPSOUTH_HUB` is entirely Oklahoma (SPP-14 §5.1), so the figure IS the North↔Oklahoma
   capability by its own construction. Keeping it as a North↔residual-South link would re-purpose
   a number identified on a different pair.
2. **The only registered element crossing North to the residual South is the SPS tie
   (`SPPSPSTIES`, SECI→SPS)** — PRECOMMIT-spp-53 §1.2's census found no other SWPP element with one
   terminal in a North area and the other in a South area. That interface is lever SPP-54's
   object; its rating is NDA/CEII (FINDING-spp-13 §4). The Missouri/Arkansas 161 kV ties
   (EDE↔SWEPCO) appear in no flowgate. A direct N↔S link would therefore have no measured
   constituent set this lane may claim.
3. **Cost, stated at the gate:** a North→SPS or North→SWEPCO transfer must transit the Oklahoma
   node and consume both links' capacity. Physically the North→SPS path is the Kansas→Panhandle
   tie (Liberal–Sooner), not Oklahoma. This is the price of the residual bubble (§1 item 2) and
   is routed to SPP-54, not absorbed.

Direction convention (fixed): link 1 `SPP-North → SPP-Oklahoma`, positive flow = **N→OK**;
link 2 `SPP-Oklahoma → SPP-South`, positive flow = **OK→S**.

### 3.2 The construction — SPP-53's FCITC reading, on a three-point spread

Each link's TTC is the transfer at which the link's limiting flowgate reaches its own effective
limit: **T*_f = L_f / ψ_f**, aggregated as the **binding-hours-weighted (2023–2025 pooled) median
of T*_f over the identified constituents, rounded to the nearest 100 MW** — SPP-53 §2.1 verbatim
(median not minimum, weighted by hours, for the reasons stated there and not re-argued).

**Leg 1 — L_f** (unchanged from SPP-53): per constituent, the median `Real Time Effective Limit`
over its BINDING ∪ BREACHED intervals in the 2026 daily archive (2026-03-17, part of 03-25, and
04-01 → latest — the 14-column days, FINDING-spp-53 §3.1); a constituent with < 100 such
intervals takes its registry rating (`Temp_Flowgate.csv` `NormLimit`, else the mean of the four
seasonal `Normal` ratings in `Flowgates.csv`), joined on `Constraint Name` first, then on the
`Monitored Facility` string; none ⇒ drops out, reported. **The corridor constituents keep SPP-53's
committed L_f exactly** (`spp53/tstar_table.csv`; rule 23 — no re-derivation without a source
change); the new groups' L_f come from the NEW reduced sidecar (§5).

**Leg 2 — ψ_f**, one regression per link, SPP-53 §2.1's specification unchanged in every
particular (sample = every hour of 2023–2025 with the two prices present; regressors = the hourly
mean |shadow price| of EVERY `Constraint Name` with ≥ 263 pooled binding hours, all four groups, +
intercept; OLS, HC1; identified iff ψ_f > 0, t ≥ 2.0, ψ_f ≤ 1). What differs is only the
dependent:

| link | dependent (hourly RT, $/MWh) | ψ_f > 0 means the constituent is loaded by | leg 2 status |
|---|---|---|---|
| N↔OK | `SPPSOUTH_HUB − SPPNORTH_HUB` (= p_OK − p_N) | N→OK transfer | **ALREADY ON THE TREE**: it is SPP-53's own regression (`spp53/psi_all.csv`, all 134 regressors incl. the 37 `oklahoma_internal` constituents ≥ 263 h). Reused verbatim; not re-fitted |
| OK↔S | `p_S − p_OK`, p_S the residual-South price (§3.4) | OK→S transfer | NEW regression, same spec, run once after this push |

**Constituent membership per link** (the flowgate-membership rule, fixed now; groups are
`spp14/groups.py`'s, unchanged):

- **N↔OK**: every constituent with ≥ 263 pooled binding hours in **`n_s_corridor` ∪
  `oklahoma_internal`** that identifies on the (p_OK − p_N) spread. The two groups measure the same
  transfer on the same axis (the Kansas corridor and the Oklahoma-entry elements are the one
  North→Oklahoma path; the area-token grouping is not a physical series/parallel decomposition,
  which no network model in this repo could make), so they pool. Reported beside the pooled
  figure: the corridor-only value (= 3,400 by construction) and the `oklahoma_internal`-only
  value, so the reader sees how the union moves it.
- **OK↔S**: every constituent with ≥ 263 pooled binding hours in **`oklahoma_internal` ∪
  `sps_tie` ∪ {`other` rows whose reason is `"other areas: CSWS"`}** that identifies on the
  (p_S − p_OK) spread. Why wider than the charter's literal "`oklahoma_internal` rows": in the chain
  the residual bubble's ONLY interface is this link, and its physical constituents are the SPS ties
  (`sps_tie` — SPP's own named ITP interface `SPPSPSTIES` / `SPSNMTIES` and the Potter County
  interchange) on the west and the PSO↔SWEPCO ties on the east (a CSWS-only contingency, which
  SPP-14's rule sends to `other`, reported as a sensitivity there); rating the link on
  Oklahoma-internal elements alone would omit the interface the market itself names. The ψ screen
  is what separates the interface elements from SPS-internal or Tulsa-internal ones, exactly as it
  separated the corridor from Kansas-internal delivery constraints in SPP-53. Reported by group.
  SPS-internal constraints (contingency token = `{SPS}` alone → `other`) are NOT admitted: they sit
  inside the residual bubble.

**The direction each link stands for — the "flowgate-named direction"** (E-6, fixed now): for
each link, the identified set with ψ > 0 (loaded by the positive direction) and the set with
ψ < 0, t ≤ −2 (loaded by the reverse) are both formed; **the link's named direction is the one
whose identified set carries more pooled binding hours**, its TTC is that set's weighted median,
and the reverse set's weighted median is reported beside it (the symmetric link, SPP-20 / SPP-53
posture; the asymmetric pair stays SPP-58's). The named direction is thus data-named, not this
lane's guess; §4 states the guess separately as a falsifiable expectation.

### 3.3 Declared rejection conditions per link (a miss kills the construction; nothing is adjusted)

Residual-blind bounds, from the sub-BA loads and the EIA-860 2025 ER fleet (`OP`, BA `SWPP`), with
w_OK unknown at the pin and therefore bracketed over [0, 1]:

| bound | Oklahoma | residual South | North (SPP-53) |
|---|---:|---:|---:|
| total capability, MW | 30,215 | 17,750 | 48,328 (48,711.8 audit) |
| non-gas capability (wind + coal + nuclear + hydro), MW | 16,917 | 8,112 | 34,617 |
| minimum hourly load 2023, MW | 4,053 + w·3,411 | 2,999 + (1−w)·3,411 | 11,299 |
| **B_plaus** (non-gas − min load): the most the zone can push out | 9,450 – 12,860 | 1,700 – 5,110 | 23,300 |
| **B_hard** (total − min load) | 22,750 – 26,160 | 11,340 – 14,750 | 37,400 |

| id | condition | consequence |
|---|---|---|
| R1 | fewer than **3** identified constituents carry an L_f (per link, in its named direction) | that link's construction FAILS |
| R2 | link TTC ≥ max over its two directions of B_plaus (evaluated at the measured w_OK) — N↔OK: max(23,300, B_plaus(OK)); OK↔S: max(B_plaus(OK), B_plaus(S)) | rejected as a non-binding placeholder |
| R3 | link TTC ≥ the same max of B_hard | rejected a fortiori |
| R4 | identified T*_f span > **10×** between the hours-weighted p25 and p75 | no single transfer level; FAILS |
| R5 | the daily archive cannot be pulled for ≥ 90 % of the days 2026-03-17 → latest, or the RT monthly SL files for ≥ 33 of 36 months | STOP (data) |
| R6 | the residual-South price (§3.4) cannot be formed for ≥ 95 % of hours in any year | STOP (data) — the OK↔S identification would rest on a gap |

On FAIL of either link the topology is **not** landed in that state: the FINDING says so with the
measured cause and the lane routes to SPP-DESK; no set, threshold or dependent is re-specified.

### 3.4 The residual-South price (the third point of the spread), declared

No SPP hub sits in the residual South (`Hub_Definitions.csv`: `SPPNORTH_HUB`, `SPPSOUTH_HUB`,
participant hubs). The residual price is built from settlement-location RT LMPs (`RTBM-LMP-MONTHLY-SL`,
the same files SPP-14's per-hub build reads, parsed on the same `_dense_from_daily` calendar):

> **p_S(h) = w_SPS · P_SPS(h) + w_SW · P_SW(h)**, with
> **P_SPS** = the RT LMP of SPP's SPS load-zone settlement location **`SPS_SPS`** (fallback where
> absent: the simple mean of the SPS-area `LOAD` SLs `GSEC_SPS`, `SPS_WTMN_SPS`, `WFEC_ENMC`);
> **P_SW** = the simple mean of the SWEPCO-side settlement locations, fixed now by name from the
> SL registry: the load SL **`AECC_CSWS`** plus the SWEPCO / AECC generation SLs in AR / LA / TX —
> `CSWARSENALHILL5`, `CSWETTURK`, `CSWMSTURK`, `CSWSWTURK`, `CSWFLINTCREEK1`, `CSWJLSTALL`,
> `CSWKNOXLEE5`, `CSWLIEBERMAN3`, `CSWLIEBERMAN4`, `CSWMATTISON1`–`4`, `CSWNARROWS1`, `CSWWELSH1`,
> `CSWWELSH3`, `CSWWILKES1`–`3`, `CSWSEASTMAN`, `AECC_ELKINS`, `AECC_FITZHUGH`, `AECC_FLTCREEK`,
> `AECC_FULTON`, `AECC_HYDRO13`, `AECC_JWTURK`, `CSWS.OMPA.TURK`, `CSWS.AECC.FITZHUGH34`
> (a name absent from a month is skipped for that month; the count used is printed);
> weights **w_SPS : w_SW = E_SPS : (1 − w_OK) · E_CSWS**, the residual zone's own measured
> 2023–2025 sub-BA energy composition.

Stated misalignment (rule 14): P_SW is a generator/hub-node mean, not a load-weighted zonal
price; P_SPS is a load-zone SL, which is the closer analogue of an LP zonal dual. Both halves are
also reported against `SPPSOUTH_HUB` separately, so the blend's construction is visible.

---

## 4. Design (C) — THE IDENTIFICATION, and the ex-ante expectations

From the per-hub parquet and the SL series, by year and by market (RT primary, DA reported):
**mean and p90 of |p_OK − p_N|** (already computed for 2023–2025 by SPP-14 §3.2: RT mean $12.13 /
$17.23 / $15.18, p90 $28.49 / $41.36 / $36.25, signed +$1.95 / +$8.42 / +$0.15 — restated, not
re-read), **mean and p90 of |p_S − p_OK|** and its signed mean, plus |p_S − p_N| for completeness,
and the same by month.

Ex-ante expectations, written so they can be wrong:

| link | expected sign of the annual-mean spread | expected named direction | expected season of binding | basis (published, not this lane's data) |
|---|---|---|---|---|
| N↔OK | p_OK > p_N (Oklahoma dearer) | **N→OK** | Sep–Oct and Dec–Jan (the widest measured months, FINDING-spp-40 §2 leg A table) | SPP-14 §3.2 signed means; MMU ASOM hub spread |
| OK↔S | **p_S < p_OK** (residual South cheaper) | **S→OK** (trapped Panhandle wind exporting into Oklahoma) | spring and overnight (wind-driven), with a summer OK→S reversal into the SPS / SWEPCO load | plan §3 P1 ("persistent negative SPS prices, largest curtailment share"); the SWEPCO half has no published statement and may pull the blend toward zero |

If the OK↔S named direction comes out OK→S (the SWEPCO half dominating the blend), that is
reported as the expectation being wrong, and the gate below runs on the data-named direction.

---

## 5. Deliverables and files (the sidecar spec)

| file | change |
|---|---|
| `data/raw/spp-binding-constraints/rtbm_bc_oklahoma_limits_2026.parquet` | NEW reduced sidecar: every `State ∈ {BINDING, BREACHED, ACTIVATED}` row of the 14-column 2026 daily files whose constraint is `oklahoma_internal`, `sps_tie`, or `other/"other areas: CSWS"` under `groups.py`'s rules — the OK↔S and Oklahoma-entry candidate set — columns as the corridor sidecar (`Constraint Name`, `Monitored Facility`, `Contingent Facility`, `State`, `Shadow Price`, `Source Limit`, `Real Time Effective Limit`, `Initial Effective Limit`, `Interconnect`, `GMTIntervalEnd`) + `group` |
| `data/raw/spp-binding-constraints/README.md`, `SOURCES.md`, `SHA256SUMS.txt` | one status section + one source row + one checksum; the four-group spec untouched |
| `data/raw/_validation-source/actual_lmp_hourly_area_SPP.parquet` (+ README row) | NEW: hourly RT `SPS_SPS`, the P_SW mean (with its per-month SL count) and p_S, 2023–2025, on the model calendar — the third point of the spread, so the identification is reproducible without the 500 MB pull |
| `data/raw/eia-861/` (NEW dir: reduced csv of the PSO / SWEPCO `Sales_Ult_Cust` rows 2023–2024 + README / SOURCES / SHA256SUMS) | the w_OK source |
| the registries of §2.3, their tests, the three rebuilt wind-shape parquets, the regenerated clean `zonal-shares` rows, the regenerated SPP block of `calibration_reference.json` | design (D) |
| `docs/handoffs/spp57/` | the instruments (pull, parse, regression, aggregation, area-price build) beside their outputs, the `spp53/` convention |
| `docs/handoffs/FINDING-spp-57-2026-09-07.md` | design (A)–(D) as executed, the identification tables, the two T* tables, the STOP-gate table, the LOYO table, the DOF ledger, the P15 recommendation |
| matrix shard `docs/codebase-site/data/mechanism-matrix/SPP.js` | the cell for the topology / interface mechanism moved by this lane (`measured_interface_limits` O → the screen's verdict), in this session (rule 28(b)) |

Not touched: any other ISO's config, maps, rows or shard; `ScenarioConfig` (no field, G8);
`results/cache.py`; offer bands (1.0, rule 25); `keepers/SPP.json` (P15 is the desk's);
`calibration-complete.json`; `frontend/data/forecast/`.

---

## 6. The SCREEN (rule 29(a)) — year, gate, thresholds

**Screen year = 2025**, named here: the year of the largest `oklahoma_internal` footprint (5,822 h,
0.665, $311.80) — the mechanism's own measured footprint, NOT the year with the largest residual
(2025 is also the keeper's worst C3a year, +21.7 %, which is exactly why the choice is stated on
the footprint and not on the residual). One `--year 2025` invocation, `--out-dir
results/calibration/_spp57_screen`, the keeper's recipe unchanged except the topology (every band
1.0; served interchange; no floors / bridges / adders; `authorized_price_tuning` NONE). Deleted
before the PR merges (rule 29(c)); every number cited from it lives in the FINDING.

**STOP gate — structural, kill-only, ex-ante thresholds (E-6). It never reads C3a / C3b.**

| leg | condition | STOP if |
|---|---|---|
| (i) liveness + direction, per link | hours at bound (|flow| ≥ TTC − 1 MW) as a share of 8,760; share of at-bound hours in the link's flowgate-named direction (§3.2) | at bound < **5 %** of hours, OR named-direction share < **55 %** of at-bound hours — for EITHER link |
| (ii) sign, per spread | sign of the annual mean of the modelled zonal spread (p_OK − p_N from `system_2025.parquet`; p_S − p_OK likewise) vs the sign of the measured annual mean (RT, §4) | either sign disagrees |
| (iii) the pocket traps something | wind re-curtailment (delivered / potential, from `class_hourly_2025.parquet` against the uncurtailed input) | re-curtailment = **0.0 %** exactly (magnitude REPORTED, never gated) |
| (iv) no new unserved energy | hours with slack > 0 | any hour outside the set SPP-40 §7.3 / SPP-42's FINDING already names (2025-07-24 14:00, 07-30 13:00–14:00, 12-21 10:00–12:00, or SPP-42's repaired set) |
| (v) fuel classes within an order of magnitude | each fuel family's TWh vs EIA-923 2025 (the keeper's leg C table) | any family outside [0.1×, 10×] |

Control = the keeper's committed 2025 numbers (form 4, §0.1): link 3,400 at bound 1,245 N→S / 373
S→N h; |S−N| zonal spread ~$1; re-curtailment 0.0 %; 2,007 MWh unserved in 6 h; the leg C fuel
table. The arm's numbers are printed beside them. **A kill is this session's result; the full span
is then not spent.** A pass promotes nothing.

**Full span** only if every leg clears: one `--year 2023 2024 2025` invocation, years sequential
(rule 12; the `spp` memory class is 5.3 GB, no other per-plant solve concurrent), registered as a
**CANDIDATE** under rule 15 with LOYO (rule 22) reported — every year's criterion table beside
the keeper's at full magnitude. **DOF ledger expected**: the CSWS split is a MEASURED value
(EIA-861, §2.2), both TTCs are measured constructions (two legs each, no free scalar), and
**zero tuned scalars**; the inherited `wefor_multiplier` 0.7 residual entry carries over from the
keeper's ledger unchanged.

## 7. What is not a rejection condition

Any comparison of a modelled price or flow with the measured one except the sign test in (ii).
No band moves, no TTC is re-cut after a solve, and no gate reads a criterion of the rubric.

---

## ADDENDUM A (before the screen) — the keeper moved: control re-pinned to keeper-2, G-DRIFT re-run

Between this document's push (`910fd5b1`, base `40b54ce7`) and the screen, **SPP-42 landed**
(PR #5471, `origin/main` `91b5d6fb`) and promoted `2026-09-07-spp-2-crosswalk-hydro`
(`results/calibration/spp42_crosswalk_B`, `git.sha = 33034499`) over spp-1. §0's clause fires:

- **Control = keeper-2** (rule 29(b) form 4), its committed `hourly/` sidecars and FINDING-spp-42
  §2.2 / §3.2 numbers. Its recipe = the spp-1 recipe + `--hydro-backfill-year 2024
  --hydro-eia930-monthly` + the coal supply-class crosswalk CSV (LP-inert, scoring-side only).
  **The screen and the full span run on exactly that recipe plus the topology.**
- **G-DRIFT, keeper-2 `33034499` → `91b5d6fb`** (the rebased base of this branch):

| # | file | hunk | verdict for SPP | reason |
|---|---|---|---|---|
| 1 | `data/raw/_validation-source/caiso-supply-consistent-demand/*` | CAISO 2022 demand csv | **INERT** | CAISO-only |
| 2 | `config/constants.py` | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO key |
| 3 | `config/fuel_trajectories.py` | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` | **INERT** | CAISO key; SPP has no carbon program |
| 4 | `model/interchange/spec.py` | CAISO DSW depths + `IMPORT_TRANCHES_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO keys; SPP's block byte-identical |
| 5 | `pipeline/backcast_config.py` | `_SPP_OFFER_CURVE` extended to the five coal keys (identity bands, `econ_low_share` 0.55) | **INERT as drift** | this IS keeper-2's own recorded dirty change (`run_config.json` `changed_files` / `diffstat` +29/−5): the keeper solved WITH it, so the base carries the keeper's recipe, not a drift from it |

  All hunks INERT ⇒ form 4 stays valid; no control solve.
- **Gate (iv) set, restated for keeper-2:** the control's 2025 unserved energy is **89.3 MWh in ONE
  hour, h8507 = 2025-12-21 11:00, SPP-South** (FINDING-spp-42 §2.2 / §3.2; the six spp-1 hours are
  gone with the hydro repair). The arm's unserved hours must lie inside {h8507} — in the three-zone
  topology the zone may be `SPP-Oklahoma` or `SPP-South` (the former South split) — or the leg STOPs.
- **Control numbers for the other legs (2025, keeper-2):** link 3,400 at bound 1,573 N→S / 228 S→N h;
  mean |S−N| zonal spread $1.35; negative-price hours 6; wind re-curtailment 0.0 % (wind 122.25 TWh
  delivered); fuel TWh coal 83.20 / CC_REGULAR 32.57 / CT_PEAKER 22.35 / ST_GAS 9.83 / hydro 8.82 /
  nuclear 15.78 / wind 122.25; load-weighted price $29.97; hours > $200 1.
- **Owner direction received in-session (2026-09-07), verbatim:** *"Is this a recommended keeper
  candidate? If so plz promote. If structural integrity improves but gates regress that may still be a
  keeper."* Read as P14's standing rule applied to this lane; the charter's "solve after SPP-42" is
  now satisfied on its own terms (SPP-42 landed), so the screen proceeds. Promotion itself is handled
  per the charter's P15 line and this direction — reported at the end, not assumed.

Nothing in §2–§6 is changed by this addendum: the constructions, sets, thresholds and the screen year
stand as written. The design's identification (§3–§4) was completed BEFORE this addendum and is
unchanged by the keeper move (it reads no keeper output).
