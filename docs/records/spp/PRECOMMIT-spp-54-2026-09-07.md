# PRECOMMIT — SPP-54: the SPS / Texas-Panhandle pocket as a third zone (P1's second lever; SPP-57b R-17)

**Lane** SPP-54 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-54-sps-pocket-kx4jvd` (stem `claude/spp-54-sps-pocket-v2kq`) ·
**Data profile** `spp` · **Charter** plan §8 W5 SPP-54 (issued r#9, `docs/multi-iso/spp-addition-plan-2026-09.md`) ·
**Predecessors** FINDING-spp-57b (R-17: the residual bubble is a composition defect no link rating reaches; R-18:
the per-zone wind reconciliation owed before any three-zone solve; R-20: do NOT rate an SPS link on the SPP-57b ψ
table), FINDING-spp-57 (§2 the CSWS split, §3.1 the R-13 spread table, `f5926636` the three-zone scaffolding),
FINDING-spp-14 §5 (the `sps_tie` footprint), FINDING-spp-32 §2 (SPS is its own EIA-930 sub-BA), FINDING-spp-43 +
Addendum A (keeper-3, the control), PRECOMMIT-spp-53 §2.1 (the FCITC construction).

**Pushed before any limit, ψ, price or flow of this lane is derived, read or solved.** Everything below is a
membership rule, a construction rule, a direction convention, a tolerance, a gate with its thresholds, or a
number already on the committed record (cited where it is). Nothing here is revised after a result; a miss of any
declared condition is reported at full magnitude in the FINDING.

---

## 0. THE PIN, the control, the preconditions

```
9708d69e   origin/main at PRECOMMIT time (branch cut from it)
623184f3   keeper-3 git.sha (results/calibration/spp43_screened_B/run_config.json)
f5926636   SPP-57's three-zone design commit (SPP-Oklahoma); 7bfe047d SPP-57b's (same files, two ratings)
```

| precondition | check | result |
|---|---|---|
| SPP-43 LANDED — keeper-3 is the control | `frontend/data/backcast/keepers/SPP.json` → `2026-09-07-spp-3-screened-input`; bundle `spp43_screened_B` + `hourly/` (system / class_hourly / class_band_hourly / storage × 2023–2025); keeper-1 / keeper-2 pruned | **yes** |
| SPP-58 (ψ₂) | `git ls-remote --heads origin` → no `claude/spp-58*` head; no `FINDING-spp-58*` in `docs/handoffs/` | **NOT LANDED** — the rating (§3.3) and the solve wait; design (A)/(C)/(D) and the census run now |
| SPP-57's instruments and sidecars in tree at the pin | `spp57/tstar_ok_s.csv` (L_f per `sps_tie` constituent + SPP-57's ψ), `spp57/spread_identification.csv` (R-13), `_validation-source/actual_lmp_hourly_area_SPP.parquet` (`SPS_SPS`), `spp-binding-constraints/rtbm_bc_oklahoma_limits_2026.parquet`, `eia-861/` | **yes** |
| `data/raw` hydrated for `spp` (full clone, 185 subtrees) | `zone-specific-demand/SPP`, `spp-wind-shape/`, `eia-860/`, `eia-930/`, `_validation-source`, `spp-binding-constraints/` present | **yes** |
| NASA POWER reachable (the wind-shape rebuild) | `HTTP 200` on a one-point WS50M probe | **yes** |
| rule 12 concurrency | no `run_calibration*` process in this container; SPP-58 is zero-LP; SPP-51 / SPP-55 / SPP-60 may solve in their own containers — the desk is told before any solve here (the lane runs autonomously) | one per-plant solve at a time here |

**The control (rule 29(b), form 4) = keeper-3**, `2026-09-07-spp-3-screened-input`, bundle `spp43_screened_B`, its
committed `hourly/` sidecars and FINDING-spp-42 §2.2 / FINDING-spp-43 §2 numbers. Its recipe: the spp-1 recipe +
`--hydro-backfill-year 2024 --hydro-eia930-monthly` + the coal supply-class crosswalk CSV (LP-inert) + the SPP-41
screened EIA-930 wind input (in tree). **Every solve of this lane runs on exactly that recipe plus the topology.**

### 0.1 G-DRIFT audit (rule 29(b)) — keeper-3 `623184f3` → `9708d69e`

```
git diff --stat 623184f3 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

13 files, +538 / −1; two commits: `19e1c867` (SPP-44, `spp_gas_commitment_bridge`) and `7f8dcbc6` (ercot-255,
`ercot_zonal_spread_ep_referenced`). `scripts/lib`, `data/raw/_validation-source`, `data/raw/reference` untouched.

| # | file(s) | hunk | verdict for an SPP 2023–2025 backcast on keeper-3's recipe | reason |
|---|---|---|---|---|
| 1 | `config/scenarios.py`, `run_calibration*.py`, `pipeline/commitment.py`, `pipeline/year.py`, `runner.py`, `pipeline/__init__.py`, `data/floor_mechanisms.py`, `config/constants.py` (SPP half) | SPP-44: the `spp_gas_commitment_bridge` field (default `False`, drop value `"False"` declared), its CLI flag, `build_spp_gas_bridge_p1_prep` (returns `None` for every gate-off run), the two measured constants, the D-2 mechanism id | **INERT** | default-off and absent from keeper-3's recipe (`run_config.json` carries no such key; `--spp-gas-commitment-bridge` is not passed); the prep hook is `None` when off; the cache key drops the field at its frozen value |
| 2 | `config/scenarios.py`, `data/fuel/basis/ercot.py`, `data/fuel/__init__.py`, `data/fuel/basis/__init__.py`, `config/constants.py` (ERCOT half) | ercot-255: `ercot_zonal_spread_ep_referenced` (default off) + `ercot_zonal_gas_basis_source_group` | **INERT** | ERCOT-only branch (`apply_ercot_zonal_gas_basis`), never entered by an SPP run |
| 3 | `config/solve_surface_declared.py` | two declarations `SPP_GAS_BRIDGE_MIN_LOAD_FRAC` / `SPP_GAS_BRIDGE_MIN_RUN_HOURS` | **INERT** | `solve_surface_register.py --diff 623184f3 HEAD`: **297 → 299 names; 0 value(s) moved, 2 added — "NO VALUE MOVED — no ISO's key is reached"** |

**All hunks INERT ⇒ form 4 is valid: keeper-3's committed numbers are the control and no control solve is
spent**, for the screen and for the full span alike (unlike SPP-57b, no year carries a LIVE hunk against this
control — the SPP-41 seam is already IN keeper-3).

---

## 1. The object — what SPP-57b measured and this lane splits

SPP-57b §3.3 / §7 R-17: the `sps_tie` set identifies ONLY OK→S-loaded constituents (the ties bind on imports INTO the
Panhandle; the residual South reads DEARER than the Oklahoma hub on every annual mean), while the model's residual
bubble — SPS's 4.65 GW of wind + SWEPCO's AR/LA/east-Texas thermal against a 5–11 GW load — EXPORTS into Oklahoma in
every hour above the median. Two physically disjoint pockets joined by a copperplate: SPS wind serves Louisiana load
at zero cost and the composite reads as a surplus zone the market never sees. **No link rating on the three SPP-57b
bubbles can reach that**, so the object here is the composition: carve the SPS pocket out of the P1 South on its own
sub-BA and its own transmission footprint, leave Oklahoma + AR/LA/east-Texas as the residual South, and give the
pocket ONE link to that residual.

What this lane does NOT do: re-open the Oklahoma pocket (SPP-57/57b's object; the residual South here is
deliberately OK + SWEPCO whole, so the N↔S 3,400 link keeps SPP-53's identification and value untouched — rule 14,
SPP-58 owns any question about it); add a `ScenarioConfig` field (topology, G8); touch an offer band (1.0); touch
`keepers/SPP.json` (P15 is the desk's).

**Rule 1 `[R-STRUCT]` framing, stated once:** the SPS pocket is a real market structure — its own BA-area token
(`SPS`), its own ITP interface names (`SPPSPSTIES`), Lubbock as a 2024 Frequently Constrained Area — and it enters
regardless of what it does to any residual. The screen's gate below asks only whether the mechanism does what its
own arithmetic says; it never reads C3a / C3b.

---

## 2. Design (A) — THE POCKET, the rule and the census

### 2.1 The membership rule (fleet side) — fixed before the fleet is built

`SPP-SPS` = the transmission footprint of Southwestern Public Service Co (Xcel), which is the EIA-930 sub-BA `SPS`
on the load side and, on the plant side, **every SWPP plant in New Mexico (FIPS 35, whole) plus every SWPP plant in a
Texas county of the SPS service territory**, declared as a county-FIPS set in `zone_assignment.py`:

- the 26 Texas Panhandle counties (Armstrong, Briscoe, Carson, Castro, Childress, Collingsworth, Dallam, Deaf Smith,
  Donley, Gray, Hall, Hansford, Hartley, Hemphill, Hutchinson, Lipscomb, Moore, Ochiltree, Oldham, Parmer, Potter,
  Randall, Roberts, Sherman, Swisher, Wheeler);
- the 15 South Plains counties (Bailey, Cochran, Crosby, Dickens, Floyd, Garza, Hale, Hockley, King, Lamb, Lubbock,
  Lynn, Motley, Terry, Yoakum);
- Gaines (the Permian-edge county SPS serves that hosts a SWPP plant).

The residual `SPP-South` = OK (whole) + AR + LA + every other Texas county (the SWEPCO / PSO east-Texas and
north-central-Texas footprint: Harrison, Titus, Marion, Morris, Gregg, Cass, Upshur, Baylor, …). `SPP-North` is
untouched (byte-identical state map).

**Why a county set and not a T/D-owner field.** `zone_assignment` places a plant by `(lat, lon, fips_state,
fips_county)` — the same instrument CAISO / NYISO / PJM use — so a county rule regenerates for any future plant with
no per-plant table (rule 13's forward test). The EIA-860 `Transmission or Distribution System Owner` field was read
as the **corroboration**, not the rule: of the 76 SWPP plants in the set, 10,156 of 12,167 MW report owner 17718
(SPS) and the rest report the co-ops that ride SPS's transmission (Golden Spread / NextEra-served 7279, Lea County EC
10817, Southwestern EC-NM 17715, South Plains EC 17561, Farmers EC-NM 6198) or OG&E 14063 (Palo Duro Wind,
Ochiltree — physically in the Panhandle, offtaken by OG&E; the county rule keeps it in the pocket, and this is the
one plant where the two instruments disagree, stated here). Conversely International Paper Texarkana (Cass) reports
owner 17718 and is in the residual South by county — a field quirk the geographic rule is right to ignore.

**Coordinate fallback (a plant with no FIPS):** inside the South tier (lat < 37.0 N), TX/NM longitude west of
−100.0° (the 100th meridian, the OK-Panhandle line) → `SPP-SPS`. Measured on the EIA-860 SWPP fleet: the pocket's
easternmost plant sits at −100.84° W (Celanese, Gray) and the residual South's westernmost Texas plant at −99.02° W
(Diversion Wind, Baylor), so the meridian separates the two sets with 1.8° of clearance.

**Stated, not patched:** (i) WFEC's Lea County / Roosevelt County NM assets fall to `SPP-SPS` by this rule while
WFEC's LOAD is a whole sub-BA in the residual South (the same sub-BA-vs-state seam SPP-57 stated); (ii) the City of
Lubbock's three gas stations still carry BA `SWPP` in the active EIA-860 vintage although LP&L's load migrated to
ERCOT in stages 2021–2023 — the measured `SPS` sub-BA demand series already carries whatever load remained, so the
two sides are consistent by measurement, not by adjustment; (iii) `CSWS` stays in the residual South WHOLE — no
sub-allocation is needed for this pocket (FINDING-spp-32 §2: SPS is its own token), and the SPP-57 CSWS split is not
reused here because there is no Oklahoma zone to split it into.

### 2.2 The membership rule (load side)

`curate_zonal_shares._SPP_SUBBA_ZONE_GROUPS`: `SPS → SPP-SPS`; the other 16 tokens unchanged (12 North; `CSWS`,
`GRDA`, `OKGE`, `WFEC` → `SPP-South`). No split, no new accessor. The hourly redistribution identity
(`max|Σ_z share − 1|`, every hour, all three years) is reported and must hold to 1e-9 (it is 2.2e-16 for the
two-zone table, FINDING-spp-32 §2.2, and the grouping is a partition, so nothing can move it).

### 2.3 The census (zero-LP), what is already on record, and the static shares

Already read at PRECOMMIT time (a load census, not a limit, ψ, price or flow): the EIA-930 `SPS` sub-BA energy share
of the 17-token SWPP total is **0.1251 (2023) / 0.1266 (2024) / 0.1260 (2025), pooled 0.1259**; 35.5 / 36.7 / 37.7
TWh; hourly 3.0–6.3 GW (mean 4.06 / 4.18 / 4.31 GW). Static `load_share`s therefore: SPP-North **0.5125** (unchanged,
the pocket is carved from the South alone), SPP-SPS **0.1259**, SPP-South **0.3616** (residual, sum 1.0000) —
confirmed to four decimals by the census before they are written.

To be produced by `docs/handoffs/spp54/census.py` (an on-recipe `run_year(fleet_only=True)` on keeper-3's meta via
`replay_keeper.run_year_kwargs`, the SPP-57b instrument re-pointed) for 2023–2025: per zone the plants, LP units,
thermal + hydro MW by class, wind / solar MW and potential TWh, demand TWh and min–max MW. Pre-census expectation
from EIA-860 nameplate under the rule (reported so it can be wrong): SPS pocket 76 plants / 12,167 MW — wind 4,654
(TX 3,518 + NM 1,136), coal 1,136 (Tolk), gas ≈ 6,100 (TX ≈ 4,680 / NM ≈ 1,410), solar 284; the residual South wind
13,146 (OK's 12,944 + Diversion 201), coal 5,856, gas ≈ 18,000, hydro 523. **The pocket is thermally
self-sufficient at its own peak** (≈ 7.2 GW of thermal against a 6.3 GW maximum hourly load) and a wind exporter
overnight (4.65 GW of wind against a ≈ 3.0 GW minimum load) — the two facts §3.2 reasons from.

Residual-blind bounds for §3.4 (computed in the census, the SPP-53/57 construction: zone capability minus minimum
hourly load): `B_plaus(SPS)`, `B_plaus(South)`, `B_hard` for both — written into the FINDING before the rating is
read.

---

## 3. Design (B) — THE LINK: one link, its direction, its rating rule

### 3.1 Topology

`SPP-North ↔ SPP-South` (3,400 MW, SPP-53, **unchanged in value, identification and citation**) **plus** ONE new
symmetric `TransferLink(from_zone="SPP-South", to_zone="SPP-SPS")`. No North↔SPS link: no SWPP element crosses from
the North tier into the Panhandle without transiting the residual South's network (the SPS ties land at Woodward /
Tuco / Potter on the Oklahoma-side system), and SPP-53's corridor set has no Panhandle constituent. Direction
convention (fixed): **positive flow = South→SPS = INTO the Panhandle.**

### 3.2 Direction, declared ex ante from two independent readings

**(a) From the ties' own binding direction (SPP-57b §0 / §2.2, the committed record):** the `sps_tie` constituents
that identify do so with ψ > 0 on (p_S − p_OK) — 4 of 7, 6,177 pooled hours, ZERO reverse-identified — i.e. when a
tie binds the Panhandle side is dearer, so the binding flow is INTO the Panhandle. Under this topology that is
**South→SPS**, the positive direction. The named direction for leg (i) is therefore **South→SPS**, fixed now, and
it does not depend on the number SPP-58 hands over.

**(b) From the SPS bubble's own balance (§2.3):** 4.65 GW of wind against a 3.0–6.3 GW load and ≈ 7.2 GW of
thermal. Overnight in wind, the pocket exports — at most ≈ 4.65 − 3.0 ≈ 1.7 GW plus whatever thermal the LP keeps
on, i.e. **an SPS→South flow of order 2 GW, below any rating the record names (3,602–11,409 MW), so the link is
expected NEVER to bind SPS→South**. In low-wind high-load hours the pocket imports whenever the residual has cheaper
energy — up to load minus the pocket's own dispatched thermal, bounded by the 6.3 GW peak — so a South→SPS bound is
**reachable only at a rating below ≈ 5–6 GW** and is expected to bind, if at all, in the direction the ties name.

**Do the two readings conflict? No — and that is the difference from SPP-57b.** There, the identified direction was
"into the Panhandle" but the bubble was the Panhandle PLUS SWEPCO, a net exporter into Oklahoma. Here the bubble is
the Panhandle alone, whose scarce hours are import hours. What the two readings jointly say, written so it can be
wrong: **liveness is a question of the rating's magnitude, not its sign** — at the ITP-interface constituents' own
T* (`SPPSPSTIES` 3,602 / Potter `TMP555` 3,850, on SPP-57's ψ) the link would be live South→SPS; at the
Potter-`TEMP50` reading (10,705) or `SPSNMTIES` (11,409) it would be inert both ways, exactly as SPP-57b's second
link was. **The gate adjudicates; the lane does not pick.**

**(c) The measured price sign (SPP-57 §3.1, R-13 — the committed table, not P1's "persistently negative" prose):**
SPS load zone minus the Oklahoma hub, annual signed mean **−1.30 (2023) / +4.74 (2024) / +12.07 (2025)**, mean |·|
13.70 / 31.25 / 24.92, a two-sided hourly distribution. For the screen year 2024 the measured sign is **positive**
(SPS dearer). Ex ante the model's spread (p_SPS − p_South) is positive in import-bound hours and negative in
export-bound hours; with (b) saying the link binds only on imports, the modelled annual mean is expected
**positive if the link is live at all, and exactly 0.00 if it is not** (identical duals) — the latter is graded as a
sign mismatch, as SPP-57/57b graded it.

### 3.3 The rating rule — declared now, the number filled in when SPP-58 lands

**Construction:** SPP-53's FCITC reading, verbatim — `T*_f = L_f / |ψ₂_f|` per identified constituent, aggregated as
the **binding-hours-weighted (2023–2025 pooled) median over the identified constituents of the link's membership
set, rounded to the nearest 100 MW** (the SPP-53 median rule).

| leg | source | fixed now |
|---|---|---|
| membership set | the `sps_tie` group as `docs/handoffs/spp14/groups.py` assigns it, ≥ 263 pooled binding hours — the 7 constituents of `spp57/tstar_ok_s.csv` (`TEMP50_23126`, `TMP555_29231`, `TMP200_25341`, `TMP775_29068` — Potter County 345/230 kV; `SPSNMTIES`, `SPPSPSTIES`; `TMP703_28546` FPL Switch–Woodward) | **yes** — the charter's set; `oklahoma_internal` and the CSWS-only rows are EXCLUDED (an intra-Oklahoma / intra-CSWS object is not a pocket boundary) |
| L_f | SPP-57's committed limit-at-bind per constituent (`tstar_ok_s.csv` column `L_f`: Potter 505.9 / 508.7 / 503.1 / 508.7; the two ITP interfaces 1,018.0; FPL–Woodward 119.2 — 2026 archive, SPP-53's join order) | **yes** — reused, never re-read |
| weights | SPP-57's pooled binding hours per constituent (same file) | **yes** |
| **ψ₂** | **SPP-58's second, independent identification** — whatever `FINDING-spp-58` hands over for these constituents under its own identification rule (which constituents identify, in which direction, with what ψ₂). **SPP-57's ψ column is NOT used** (SPP-57b R-20) | **waits** |
| identification / direction | SPP-58's rule for its ψ₂; the named direction is data-named (the direction whose identified set carries more pooled hours), expected South→SPS per §3.2(a); the reverse reading reported beside it or "none" if R1 fails there | **yes** |
| what if SPP-58 hands a T* or a TTC directly | its one-line "what SPP-54 may use" is taken as written; if it hands a disagreement band rather than a number, the lane STOPs at the design and reports — it does not pick inside a band | **yes** |

**Disclosed rather than discovered:** the record already prints, on SPP-57's ψ, `SPPSPSTIES` 3,602 / `TMP555`
3,850 / `TEMP50` 10,705 / `SPSNMTIES` 11,409 (weighted median 10,700; LOYO 8,395 / 10,490 / 14,796). That table is
NOT this lane's rating input (R-20) and is cited only so no later reader thinks the number was unread.

**One membership doubt, stated before any number:** `SPSNMTIES` ("SPS NM ties") may be SPP's ITP interface INTO
SPS's eastern-New-Mexico load area — an intra-pocket (TX→NM) object under this topology — rather than an
SPS↔SPP-East tie. The charter's set includes it and the set decides; the FINDING reports the reading with
`SPSNMTIES` excluded BESIDE the primary as a sensitivity, never as the rating. If SPP-58's identification itself
separates the two interfaces, its reading governs.

### 3.4 Rejection conditions — PRECOMMIT-spp-57 §3.3 R1–R4, applied to the one link

| id | condition | consequence |
|---|---|---|
| R1 | fewer than **3** identified constituents carry an L_f in the link's NAMED direction | the construction FAILS; no rating; the lane routes to SPP-DESK |
| R2 | TTC ≥ max(`B_plaus(SPS)`, `B_plaus(South)`) from the census (§2.3) | rejected as a non-binding placeholder |
| R3 | TTC ≥ the same max of `B_hard` | rejected a fortiori |
| R4 | weighted p75 / p25 of the identified T* > **10×** | no single transfer level; FAILS |

R2 is expected to be the tightest (the residual South's own bound is the binding one; SPP-57 measured the OK+SWEPCO
composite's `B_plaus` at ≈ 11,085). It is applied as written.

---

## 4. Design (C) — THE WIND RECONCILIATION (SPP-57b R-18), a STOP before any solve

`scripts/data/build_spp_wind_shape.py --years 2023 2024 2025 --reconcile` on the three-zone map: the builder's
per-zone site set is the six largest EIA-860 operable wind plants per zone under `build_zone_lookup("SPP")`, so the
SPS pocket gets its own Panhandle / eastern-NM sample and the residual South its own (Oklahoma-dominated) sample; the
North's six sites are the same six as the two-zone build (its map is unchanged). Then `spp54/wind_reconcile.py`
builds the LP's wind bound through the real path (`renewables.load_renewable_profiles`, keeper-3's config, the
three-zone `ISOConfig`) and grades, hourly, all three years:

| leg | test | STOP if |
|---|---|---|
| (C-1) the redistribution identity | `Σ_z cap_z · cf_z(t)` vs `M(t)` = the EIA-930 SWPP delivered wind × the SPP-32 year-invariant gross-up 1.106808 (the flat-path aggregate); relative error per hour | any hour > **1e-9** |
| (C-2) capacity feasibility | every `cf_z(t) ≤ 1`; water-filling overflow that cannot be placed (the only way the split can LOSE energy) | any hour with lost overflow |
| (C-3) the Dec-21-2025 window, itemised | for h8496–h8520 (2025-12-21 00:00 → 12-22 00:00 local; h8505–h8508 are the keeper-2/keeper-3 unserved hours), per zone: wind potential (two-zone build vs three-zone build), solar, thermal + hydro capability net of outages, demand; and the regional feasibility `own capability + wind + solar + 3,400 ≥ demand` for the South + SPS region | any window hour that the three-zone INPUTS make arithmetically infeasible while the two-zone inputs left it feasible — the pocket must not manufacture unserved energy by inputs alone |
| (C-4) attribution of the North's change (reported, never gated) | ΔW_North(t) three-zone minus two-zone, annual and in the window, decomposed into the part explained by replacing the SPS capacity's borrowed Oklahoma shape with its own | — |

Also reported: each zone's night/afternoon ratio (the arming-proof statistic), the GenMix reconciliation `r`, and the
Dec-21 window's `Demand` stuck-run status (FINDING-spp-42 §2 R-9: the SWPP `Demand` series is flat at 37,455 MW for
155 h from 2025-12-15 14:00; the zonal demands inherit it through the sub-BA shares — a P9-class routed item, NOT
repaired here).

**Tolerance rationale:** C-1/C-2 are construction identities (2.2e-16 on the two-zone table, FINDING-spp-32 §3.3), so
1e-9 is a defect detector, not a band. C-3 is the honest pre-solve form of the charter's "the pocket must not
manufacture unserved energy": R-18's 89 → 444 MWh was a regional-generation change under identical demand and
pipe, and the arithmetic above is what would have caught it before the LP. There is no measured per-zone wind series
(EIA-930 sub-BAs report demand only; GenMix is system-wide), so C-3/C-4 are stated as accounting, not as a fit.

---

## 5. Design (D) — every registry gains `SPP-SPS`; the proofs

| file | change |
|---|---|
| `src/market_sim/config/iso_configs.py` `_spp_config` | third `Zone` (static shares §2.3), the South↔SPS `TransferLink` beside the N↔S 3,400 link (which keeps its citation comment byte-for-byte), docstring; the rating's citation comment written at fill-in time |
| `src/market_sim/data/zone_assignment.py` | `_SPP_STATE_ZONES[35] = "SPP-SPS"`; `_SPP_SPS_TX_COUNTIES` (FIPS set, §2.1); `_spp_zone(lat, lon, fips_state, fips_county)` with the county limb and the meridian fallback; `_LARGEST_ZONE["SPP"]` stays `SPP-North` |
| `scripts/data/curate_zonal_shares.py` | `"SPS": "SPP-SPS"` |
| `src/market_sim/data/renewables.py` `RENEWABLE_ZONE_ALLOCATION["SPP"]` | fallback-only entry by the "zone holding the largest share" rule (wind: North 17,664 > South ≈ 13,146 > SPS 4,654; solar: North 601 > South ≈ 557 > SPS 284 → both `SPP-North`); never read on the primary path |
| `src/market_sim/data/fuel/basis/meanzero.py` + `data/raw/spp_zonal_gas_hub.csv` / `.SOURCES.md` | `SPP-SPS` rows on the **TX proxy** (EIA `N3045TX3`, Waha / Permian-Panhandle): the pocket's gas fleet is TX ≈ 77 % / NM ≈ 23 % by nameplate, and EIA publishes no NM delivered-to-electric-power series usable here — the `f5926636` TX rows (2022 −0.081 / 2023 +0.096 / 2024 −0.010, derived by SPP-57 from the same instrument SPP-32 used) re-keyed from its `SPP-South` to `SPP-SPS`; the residual South keeps the OK proxy (OK is now ≈ 60 % of the residual's gas). **No applier is armed** — the table is LP-inert for every SPP keeper (SPP-32's posture, unchanged) |
| `src/market_sim/model/interchange/spec.py` | **unchanged**: both ERCOT DC ties (Oklaunion → the Lawton/PSO side; Monticello → Titus County) land in the residual South, so `border_zones=("SPP-South",)` is still right, and the block is default-off |
| `data/raw/_validation-source/calibration_reference.json` SPP block + `SPP_{2023,2024,2025}_renewable_capacity.csv` | regenerated by `build_calibration_reference.py --isos SPP` for the zone-keyed `renewables` block ONLY; the `demand` / `generation_twh` blocks are diffed against HEAD and any move is REVERTED (G9 merge-never-replace — `f5926636` carried an unrelated `demand.peak_mw` move that this lane will not repeat) |
| `docs/codebase-site/data/iso-topologies.json` SPP entry | three zones, two links (also correcting the stale 48,700 the SPP-53 landing left there) |
| `data/raw/spp-wind-shape/spp_{2023,2024,2025}_wind_zone_shape.parquet` + README | the three-zone rebuild (§4) |
| tests | `test_iso_config.py` (three zones, two links, shares), `test_zone_assignment.py` (state + county + fallback + named plants: Tolk 6194 / Cunningham 2454 → `SPP-SPS`; Sooner / Muskogee / Flint Creek / Pirkey → `SPP-South`; every plant resolves), `test_curate_zonal_shares_spp.py`, `test_spp_renewable_inputs.py` (three columns), `test_spp_zonal_gas_hub.py` |

Zero-LP proofs owed before any solve: `validate_topology()`; `solve_surface_register.py --diff origin/main HEAD` →
**0 moved** for the six keepers (rule 25); `tests/regression/test_persisted_identity.py` green; the SPP test files
green; ruff clean; the `fleet_only` three-zone census (§2.3); the wind reconciliation (§4).

**Landing posture:** the three-zone solve path lives on this branch. If the screen KILLS, the solve path is restored
to `origin/main`'s bytes (`git checkout origin/main -- <files>`, never rewritten — the SPP-57/57b rule: a killed
arm's topology must not silently change every later SPP lane's zones while the keeper has two) and the design
commit is cited for a re-issue. If the screen clears and the span runs, the topology lands with the candidate and
the desk serves P15.

---

## 6. The SCREEN (rule 29(a)) — year, gate, thresholds

**Screen year = 2024** — the year of the largest `sps_tie` footprint (FINDING-spp-14 §5.2: 3,000 binding hours,
share **0.342**, $69.6 mean |shadow|; 2023 0.258 / $52.4; 2025 0.282 / $58.5) — the mechanism's own measured
footprint, NOT the residual (2023 is keeper-3's worst C3a year, +14.1 %, which is exactly why the choice is stated on
the footprint). One `--year 2024` invocation on keeper-3's recipe plus the topology, after the rating is filled in
and the desk is told (rule 12):

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2024 \
    --out-dir results/calibration/_spp54_screen --hydro-backfill-year 2024 --hydro-eia930-monthly
```

The bundle is TEMPORARY: gitignored the moment it is written (rules 29(c) / 31 — kept on local disk until the
owner rules, never committed); every number cited from it lives in the FINDING and
`docs/handoffs/spp54/grade_screen_2024.log`.

**STOP gate — structural, kill-only, ex-ante thresholds (E-6). It never reads C3a / C3b.** Graded by
`spp54/grade_screen.py` (SPP-57b's instrument re-pointed: one link, the named direction South→SPS, the census
from `spp54/`, control keeper-3).

| leg | condition | STOP if |
|---|---|---|
| (i) liveness + direction | hours at bound (\|flow\| ≥ TTC − 1 MW) / 8,760 on the South↔SPS link; share of at-bound hours in the named direction **South→SPS** | at bound < **5 %** OR named-direction share < **55 %** |
| (ii) sign | sign of the annual mean of the modelled `p_SPS − p_South` (from `system_2024.parquet`) vs the measured 2024 SPS-load-zone-minus-OK-hub mean **+4.74** (R-13) | sign disagrees (a never-binding link yields exactly 0.00, graded as a mismatch) |
| (iii) the pocket traps something | wind re-curtailment = 1 − delivered / potential (`class_hourly_2024.parquet` vs the census potential) | re-curtailment = **0.0 %** exactly (magnitude REPORTED, never gated) |
| (iv) no new unserved energy | hours with slack > 0 | **any** hour — keeper-3's 2024 has **0 MWh** unserved (`system_2024.parquet`: 0 slack hours), so the control set is empty |
| (v) fuel families within an order of magnitude | each family's TWh vs `calibration_reference.json` 2024 (coal 65.09 / gas_cc 46.25 / gas_ct 15.28 / gas_st 19.85 / hydro 8.70 / nuclear 15.30 / solar 1.65 / wind 108.49) | any family outside [0.1×, 10×]. Hydro reads against keeper-3's own EIA-930 2024 level (8.97 TWh dispatched vs 8.70), not a vintage defect this year — stated, and expected in band |

Control numbers (keeper-3, 2024, form 4 — computed from its committed `hourly/` sidecars, and FINDING-spp-42
§4's table for the link): load-weighted **$26.36** (zone means N 25.59 / S 25.80; mean |S−N| 0.99; measured RT
C3a 2024 PASS); negative-price hours **7**; hours > $200 **3** (max 247.84); unserved **0**; re-curtailment 0.0 %
(wind 120.99 TWh = 109.317 × 1.106808); by class COAL_PRB 55.16 / COAL_LIGNITE 5.87 / CC_REGULAR 37.66 / CC_CHP
1.81 / CT_PEAKER 25.97 / CT_CHP 1.21 / ST_GAS 14.99 / ST_CHP 0.38 / hydro 8.97 / nuclear 15.02 / solar 1.20 / wind
120.99 TWh; demand 290.89 TWh; N↔S link at bound **877 N→S / 895 S→N** (the year-specific tie FINDING-spp-40 §7.2 /
FINDING-spp-42 §4 record — keeper-3's own 2024 `flows.parquet` is gitignored and its P1 landed on a different
vertex, so the split is quoted from the record, not re-read).

Reported beside the legs, never gated: load-weighted price, zone means, negative-price hours (measured ~1,170 in
2024), hours > $200, the by-class TWh, the N↔S link's own at-bound count and split (does carving the pocket move
the corridor?), and — as SPP-57 §5.3 / 57b §3.3 did — the hours at/over bound the South↔SPS link would show at
other ratings, from the screen's own flows (a report on the construction question, never a re-cut).

### 6.1 Ex-ante expectations, written so they can be wrong (not gates)

| item | expectation | basis |
|---|---|---|
| South↔SPS at a rating ≤ ~4,000 | live, South→SPS-dominant, binding in low-wind / high-load hours (summer afternoons, winter mornings) | §3.2(b): the pocket's scarce hours are import hours; its export never reaches 3,400 |
| South↔SPS at a rating ≥ ~6,000 | **inert**, leg (ii) then fails by construction | the pocket's 6.3 GW peak cannot pull 6 GW across the link while any of its 7.2 GW of thermal runs |
| N↔S 3,400 | still live, near the control's ~20 % (the pocket is carved from the South, so the North's export path is unchanged) | control 877 / 895 |
| re-curtailment | > 0 only if the SPS link binds SPS→South overnight, which §3.2(b) says it will not; so **likely 0.00 % — a STOP on (iii)** even with a live import link | 4.65 GW of wind against 3.0 GW of minimum load exports ≈ 2 GW, below any rating on record |
| unserved | 0 — the pocket is thermally self-sufficient; C-3 is the pre-solve check | §2.3 |

The (iii) expectation is worth stating plainly: the gate's "traps something" leg was written for a pocket that
exports wind behind a bound tie (SPP-57's Oklahoma), and this pocket's physics is the opposite — it imports at the
bound. A STOP on (iii) alone would therefore be the gate measuring the wrong sign of the same object, and the FINDING
will say so at full magnitude **without changing the gate**: a screen that kills on (iii) is reported as a kill, and
the observation is routed to the desk as a gate-design question, never re-cut in-lane.

**A kill is this session's result; the full span is then not spent. A pass promotes nothing.**

---

## 7. If the screen clears (every leg): the full span

One `--year 2023 2024 2025` invocation, years sequential (rule 12; the `spp` memory class at three zones is ≈ 5 GB),
`--out-dir results/calibration/spp54_sps_B`; registered as a **CANDIDATE** (rule 15); LOYO (rule 22) — every year's
criterion table beside keeper-3's at full magnitude; the control is keeper-3 for every year (§0.1: no LIVE hunk);
`keepers/SPP.json` untouched; the SPP shard cell `measured_interface_limits` (or the topology row the desk names)
stamped in this session (rule 28(b)). **DOF ledger expected:** the county set is a geographic rule, the load shares
are measured, L_f and the weights are measured, ψ₂ is SPP-58's measured identification — **zero tuned scalars**; the
inherited `wefor_multiplier` 0.7 residual entry carries over unchanged.

## 8. Deliverables and files

| file | change |
|---|---|
| the solve-path files of §5 + the three wind-shape parquets + README | the topology (on the branch; landing posture per §5) |
| `docs/handoffs/spp54/` | `census.py` (+ `census.csv`, log), `wind_reconcile.py` (+ log, `dec21_window_2025.csv`), `rate_link.py` (+ log, `tstar_s_sps.csv`) once SPP-58 lands, `grade_screen.py` / `flows_at_ratings.py` (+ logs) if the screen runs |
| `docs/handoffs/FINDING-spp-54-2026-09-07.md` | the census, the wind reconciliation, the rating (ψ₂ cited), the STOP-gate table beside SPP-57b's, LOYO if the span ran, DOF, the P15 recommendation |
| `docs/calibration-log/spp.md`; plan §5 row; ledger row; matrix shard `SPP.js` | the record |

Not touched: any other ISO's config, maps, rows or shard; `ScenarioConfig` (no field, G8); offer bands (1.0);
`keepers/SPP.json`; the N↔S 3,400 value; `calibration-complete.json`; `docs/handoffs/spp57*/` (read only);
`frontend/data/forecast/`.

## 9. What is not a rejection condition

Any comparison of a modelled price or flow with the measured one except the sign test in (ii). No band moves, no
rating is re-cut after a solve, no set changes after a number is seen, no county is moved after a solve, and no gate
reads a criterion of the rubric.
