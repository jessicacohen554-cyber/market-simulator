# DESIGN — SPP-105: gas-family outage allocation (zero LP, 2026-09-30)

Lane: SPP-105, chartered by the owner card "Continue: gas-family design" (SPP-104).
Keeper: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (2019–2025).
Probe: `scripts/probes/_spp105_gas_outage_hourly_phase0.py` (+ `_spp105_carriers.py`).
Numbers: `results/phase0/spp/_spp105_gas_outage_phase0.json`.
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched.**

## 0. Headline

1. **The keeper already tracks SPP's hourly gas outage closely.** On the outage-type basis, the
   hourly correlation between the keeper's gas unavailability and SPP's published Natural Gas outage
   is **0.91 / 0.75 / 0.65 / 0.72 / 0.89 / 0.81 / 0.87** (2019–25). Most of the keeper's gas outage,
   **6.0–8.1 GW**, is the measured CAMPD event layer. The statistical terms (WEFOR + CT POF) add only
   1.2–1.5 GW.
2. **The scarce-hour gap in the train years does not have one sign.** In upper-tercile RT hours,
   keeper minus SPP is **−0.70 / −1.85 / +0.36 GW** (2023 / 24 / 25). 2024 is short, 2025 is over.
   That is year-specific event variance, not a rate error. No rate-based (structural) carrier can make
   2024 short and 2025 over at the same time.
3. **No admissible SPP-own CT / ST / CC split exists** (§3). The only numeric SPP-own class figure is
   the MMU's 2022 text: combined cycle is ~31 % of gas outaged capacity. The keeper's own split is
   **29–32 %** in every year, so the keeper's class split is not contradicted. There is no evidence the
   gap sits in one class.
4. **The only carrier that closes the gap is SPP's hourly total itself.** A "CROW residual" carrier
   (§4, carrier B) replaces the gas statistical terms with `max(0, SPP gas − CAMPD events)`. It is
   binding in **41–94 %** of hours, so in those hours it sets the model's gas outage equal to the
   published total. That is the pin the charter's DO-NOT list forbids (rule 13). Its zero-LP
   prediction mainly moves 2024: **+1.16 $/MWh all hours, +2.67 upper tercile**. In 2023 and 2025 it
   moves only +0.12 / +0.07.
5. **The rule-19 repair on its own points the wrong way.** Removing the statistical WEFOR from the
   CAMPD-covered classes (CC, ST) moves the keeper **further** from SPP's measured gas outage in 5 of 7
   years (mean |gap| 0.93 → 1.11 GW). It also lowers train-year prices by 0.17–0.31 $/MWh. So the
   WEFOR on ST and CC is not a pure double count. It stands in for the sub-5-day outages and derates
   that the ≥5-day CAMPD windows miss (SPP's gas short-window family is R, SPP-32).
6. **Recommendation: build nothing. Record this as a model-class limit.** The 2023+ scarce-hour
   shortfall is real in 2023 and 2024. But what carries it is year-specific CROW event data at fuel
   grain. The model cannot take that in without pinning to the published total, and SPP publishes no
   class split to allocate it by.

## 1. What the keeper carries for gas (code, SPP recipe)

`outage_source historic`, `coal_drop_pof true`, `wefor_residual None`, `wefor_multiplier 0.7`,
`unit_outage_short_windows_gas false`. In `data/fleet/arrays.py::_availability_matrix`:

| class | statistical WEFOR (×0.7, 30 % summer share) | POF | CAMPD event windows (≥ 5 d) |
|---|---|---|---|
| CC_REGULAR / CC_CHP | yes (full; `wefor_residual` None) | dropped (`_POF_DROP_GROUPS`) | yes |
| ST_GAS / ST_CHP | yes (full) | dropped | yes |
| CT_PEAKER / CT_CHP | yes | shoulder 0.03 | none (SPP-104) |

## 2. Phase 0: hourly decomposition vs SPP published (outage-type basis, GW)

Three `fleet_only` rebuilds per year, used as decomposition instruments and never as configs. Each has
the flat GADS derate and the summer class derate zeroed, as in SPP-104. `full` is everything; `nowefor`
also zeroes WEFOR; `event` zeroes every statistical term. **Upper** = RT ≥ p67 and < p99, February
excluded (SPP-84's cut). COD / retirement edges ≥ 30 d are excluded. SPP published data: portal
`capacity-of-generation-on-outage`. It covers ≥ 99.9 % of hours in every year. 2025 is assembled from
the 365 daily CSVs.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SPP gas, all hours | 10.19 | 8.13 | 8.03 | 7.23 | 7.93 | 9.66 | 8.99 |
| SPP gas, upper | 10.18 | 8.01 | 7.04 | 6.13 | 7.37 | 9.23 | 8.32 |
| keeper gas, all | 9.16 | 7.82 | 8.83 | 9.20 | 7.47 | 8.37 | 9.59 |
| keeper gas, upper | 8.88 | 7.45 | 8.41 | 7.45 | 6.67 | 7.39 | 8.68 |
| **keeper − SPP, all** | −1.03 | −0.31 | +0.80 | +1.98 | −0.46 | −1.29 | +0.61 |
| **keeper − SPP, upper** | −1.30 | −0.55 | +1.37 | +1.31 | **−0.70** | **−1.85** | **+0.36** |
| keeper − SPP, top 1 % | −1.48 | −1.08 | +0.69 | +1.79 | −1.14 | −3.21 | +0.77 |
| (upper − body) gap | −0.42 | −0.42 | +0.40 | −0.94 | −0.30 | −0.75 | −0.33 |
| hourly r / daily r | 0.91 / 0.92 | 0.75 / 0.76 | 0.65 / 0.65 | 0.72 / 0.73 | 0.89 / 0.89 | 0.81 / 0.81 | 0.87 / 0.87 |
| component: CAMPD events | 7.85 | 6.47 | 7.59 | 7.88 | 6.02 | 6.87 | 8.09 |
| component: WEFOR | 1.18 | 1.22 | 1.11 | 1.19 | 1.31 | 1.36 | 1.36 |
| component: POF (CT only) | 0.13 | 0.13 | 0.13 | 0.13 | 0.14 | 0.14 | 0.14 |

By class (all hours; 2023 / 2024 / 2025):
- **CC_REGULAR:** 2.28 / 2.55 / 2.91. Mostly CAMPD events, plus WEFOR 0.23–0.26.
- **ST_GAS:** 4.50 / 5.11 / 5.74. CAMPD events 4.0–5.2 plus WEFOR 0.52–0.59.
- **CT_PEAKER:** 0.65 / 0.65 / 0.91. Statistical only; in 2025 the `event` variant also carries 0.23 GW
  of COD-ramp masking that the 30-day edge filter does not remove, since CTs have no CAMPD windows.
- **CHP:** < 0.06 each.

Reading:
- **Level.** The gap's sign changes from year to year: short in 2019, 2020, 2023 and 2024; over in
  2021, 2022 and 2025.
- **Where the gap sits in time.** The monthly profile (JSON `spp_monthly_gw` / `keeper_monthly_gw`)
  puts the 2024 shortfall in Apr and Oct–Nov (−3.0 / −4.2 / −4.2 GW) and in summer (−1.3 to −1.7). The
  2025 surplus is in Jul–Sep (+1.2 to +2.2).
- **Shape.** In 6 of 7 years the keeper's gas outage drops more in scarce hours than SPP's does
  (upper − body = −0.30 to −0.94 GW). This is the one persistent feature. It is small: 0.3–0.9 GW,
  against a 1.2–1.5 GW statistical layer.
- **Is that shape the summer WEFOR share?** Probably not.
  - SPP's own MMU (ASOM 2025 §3, concurrent forced outage) puts gas forced outage **higher in winter
    (median 10 %) than summer (4 %)**.
  - So the heuristic's low summer share (`SUMMER_WEFOR_SHARE` 0.30) has SPP's measured sign, unlike
    MISO (miso-160).
  - `summer_wefor_share_override` is therefore not a carrier for the summer scarce hours. Its
    Jun–Sep / annual ratio is also not identifiable from SPP data: the MMU publishes winter and summer
    medians only, and the portal series is untyped.

## 3. Source search for a CT / ST / CC split (rule 13 forward test, rule 14 alignment)

| candidate | what it splits | grain | verdict |
|---|---|---|---|
| Portal `capacity-of-generation-on-outage` | fuel only (Natural Gas MW) | hourly, 2016→; 2025 from daily CSVs | no class split |
| MMU ASOM "Resource outages and derates" 2021–23 reports | coal / gas combined-cycle / gas simple-cycle / … | annual GWh, stacked-bar **charts only** (transcriptions carry axis ticks, no values) | see below |
| MMU ASOM 2024 and 2025 reports | **fuel only** ("categorized by fuel type"; gas 55 % / 49 % of outaged capacity) | annual | no split for 2024 or 2025 |
| MMU "Unavailable Generation Capacity" (Dec 2025) | ST vs **CT/CC/IC pooled** (Fig 11: gas ST 8,248 MW; gas CT/CC/IC 26,879 MW) | study period 2020–24; ambient derates, commitment status, offer parameters | no outage series by class; confirms ambient derates are unreported (185–422 MW/day) |
| SPP LOLE study EFOR | fuel × size, service-hour basis | biennial | already rejected as a CT vehicle (SPP-104, R) |
| CROW unit-level outage records | unit | — | not public |
| FERC filings / SPP RC outage postings | event narratives (Uri, Elliott) | episodic | not a series |

Why the MMU ASOM charts are not a usable split:
- **Digitization is not reproducible to the needed precision.** The source PDFs are not in the repo,
  and the committed transcriptions contain only axis labels. Pixel-reading a 0–100,000 GWh stacked bar
  resolves about ±1,000 GWh ≈ ±0.11 GW per segment. The design would need ~0.1 GW class-level accuracy.
- **It is not rule-14-reconcilable with the portal series:**
  - "simple-cycle" includes gas steam (22.7 GW nameplate ≈ keeper CT + ST_GAS), so it cannot separate
    CT from ST;
  - it excludes economic / excess-capacity outages, which the portal series includes;
  - it is annual GWh with no hourly or seasonal grain;
  - it stops at 2023. The two train years that carry the scarce-hour gap (2024, 2025) are fuel-only.

**The one numeric datum is a cross-check, not an input.** ASOM 2022 text: CC ~15 % and simple-cycle
~34 % of outaged capacity, so CC ≈ 31 % of gas outage. The keeper's outage-type CC share is
**0.298 / 0.298 / 0.324 / 0.292 / 0.309 / 0.309 / 0.306** (2019–25), and 0.292 in 2022. The keeper's
class allocation agrees with SPP's only class figure to within ~2 points.

## 4. Candidate carriers and zero-LP predictions (SPP-84 re-clear instrument, gas only)

Both carriers are deterministic functions of fixed inputs with no tunable
(`scripts/probes/_spp105_carriers.py`). The instrument merit-clears the keeper's own stack at its own
non-VER P1 generation, system-wide, with no ramps. Only deltas are used. The base clear sits
0.3–2.7 $/MWh below the keeper's P1.

- **A — `stat_off_covered` (rule-19 repair only).** Remove the statistical WEFOR from CC / ST, which
  already carry CAMPD windows. CT is untouched.
- **B — `crow_residual` (gas-family replacement).** Remove every gas row's statistical WEFOR and POF.
  Replace them with `R(t) = max(0, SPP_gas(t) − E(t))`, where E is the keeper's own CAMPD event MW.
  R is allocated pro rata to each row's annual statistical outage MW, so the class key is the
  incumbent's own and the shape comes from SPP. Allocation is capped at each row's available MW.

| $/MWh (Δ gas unavailable, GW) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| RT mean / keeper P1 | 20.85 / 22.89 | 16.52 / 20.60 | 37.36 / 37.47 | 44.09 / 38.58 | 23.47 / 22.49 | 23.31 / 22.12 | 27.11 / 26.08 |
| A, all hours | −0.17 (−0.67) | −0.16 (−0.71) | −0.47 (−0.61) | −0.24 (−0.67) | −0.17 (−0.79) | −0.31 (−0.84) | −0.31 (−0.81) |
| A, upper | −0.29 | −0.25 | −0.36 | −0.50 | −0.30 | −0.56 | −0.58 |
| A: keeper − SPP after (all) | −1.70 | −1.01 | +0.19 | +1.31 | −1.25 | −2.13 | −0.21 |
| B, all hours | +0.25 (+0.85) | +0.12 (+0.40) | +2.46 (+0.02) | −0.10 (−0.66) | +0.12 (+0.36) | **+1.16 (+1.25)** | +0.07 (−0.09) |
| B, upper | +0.56 | +0.30 | −0.06 | −0.09 | +0.29 | **+2.67** | +0.24 |
| B: share of hours binding (pinned) | 94 % | 78 % | 54 % | 41 % | 84 % | 82 % | 60 % |
| B: residual / replaced statistical / unplaceable | 2.38 / 1.31 / 0.22 | 1.90 / 1.35 / 0.16 | 1.41 / 1.24 / 0.15 | 0.71 / 1.32 / 0.05 | 2.01 / 1.44 / 0.21 | 3.12 / 1.50 / 0.37 | 1.64 / 1.50 / 0.23 |

Keeper C3a for reference: +11.5 / +27.5 / +6.5 / −5.8 / −6.7 / −8.6 / −5.4 %.

Reading:
- **Carrier A.** It moves every year's price down, including the three under-priced train years (2024
  would go from −8.6 % toward the −10 % band edge), and it moves the keeper away from SPP's data in 5
  of 7 years. The repair is structurally motivated, but SPP's own measurement contradicts it (rule 14).
  **Not proposed.**
- **Carrier B.** It moves 2024 materially, by about the same amount SPP-104's LP measured (+2.55 LP;
  instrument +1.16 all hours). It barely moves 2023 or 2025, which are also under-priced. It raises the
  over-priced 2019 and 2020. 2021's +2.46 is Uri and non-linear, as in SPP-84.
  - **It is a pin in 41–94 % of hours.** It also has a 0.05–0.37 GW unplaceable remainder, because the
    incumbent key cannot place all of R.
  - **Forward story (rule 13).** A forecast year has no CROW data, so the statistical stack stays. That
    is the same backcast-only posture as the CAMPD windows. The step that breaks rule 13 is not being
    backcast-only; it is matching the published total by construction.

## 5. The design that would be built (carrier B), and why it is not recommended

- **Form (rule 19).** A replacement inside `_availability_matrix`, not a layer: under
  `outage_source historic`, gas rows' statistical WEFOR / POF become the CROW residual. CAMPD windows
  are untouched. Forecast mode keeps the statistical stack.
- **Driver / window / forward story (rule 17).** Not a floor. Its driver is SPP's measured outage.
  In a forecast year it regenerates as the incumbent statistical stack.
- **Parameters (rule 21).** Zero fitted. The allocation key is the incumbent class rates, and one
  cross-check holds (MMU 2022 CC share).
- **Why it fails.**
  - **Rule 13 / charter:** its level is the published total whenever that total exceeds CAMPD. The
    charter names this pin explicitly.
  - **Rule 14:** there is no class split to allocate by, and the unplaceable remainder shows the
    allocation is not a physical statement.
  - **Rule 1:** its only material effect is on one year (2024), in the direction the residual wants.
    Choosing it for that would be the fitted-mechanism route SPP-104's rejection already named.
- **Failure modes if built anyway:**
  - it double-counts CAMPD events that SPP files under a different timing;
  - it restores nothing where SPP < CAMPD, so it is one-sided by design;
  - Uri 2021 non-linearity;
  - a 2024-only benefit.
- **Owner-accepted cost profile:** not applicable, since nothing is recommended. For reference, the
  instrument's damage to 2019 and 2020 is small (+0.25 / +0.12 $/MWh ≈ +1 pt C3a).

## 6. Recommendation

- **Record as a model-class limit.** The keeper's gas outage is CAMPD events plus the national GADS
  statistical stack. The class split it implies matches SPP's only class figure. What remains of the
  gap is year-specific event variance at fuel grain (2024 short, 2025 over). The model cannot carry
  that without pinning to SPP's published total.
- **Close the SPP-104 successor.** "A gas-family allocation matched to SPP's hourly total with a
  CT / ST split from SPP's own data" has no admissible split: none exists in any public SPP product
  for 2024 or 2025. The "matched to the total" half is the forbidden pin.
- **Where the train-tier price shortfall should be looked for instead.** Not in outage availability
  for 2023 or 2025: the keeper's upper-tercile gas outage there is within −0.7 / +0.4 GW of SPP's
  data. The MMU Dec 2025 report's other unavailability classes are offer-side:
  - reliability commitment status, 4 % of conventional capacity;
  - emergency-max shortfall, 1.5–3 %;
  - unreported ambient derates.

  These are outside this charter (commitment posture and offer parameters) and are named only as the
  open question.
- **Matrix (rule 28(b)):** no verdict moves. Evidence appended to SPP's `dam_availability_rebasis`
  (stays O), `wefor_statistical_stack` (U), `wefor_residual` (U; carrier A measured, not armed) and
  `summer_wefor_share_override` (U; SPP's MMU sign noted).
- **Rules:**
  - 1: nothing selected on a residual.
  - 13: the pin is identified and refused.
  - 14: the MMU 2022 cross-check holds, and carrier A fails reconciliation.
  - 19: both carriers are replacements.
  - 21: zero parameters.
  - 25: SPP data only.
  - 29(b) / 31–36: no solve, shard, bundle or registration.

## 7. Owner ruling and the built form (2026-09-30)

**Owner card: "Build carrier a and b"**, over §6's recommendation. Both are built, default off, and solved
as two separate arms against the keeper.

- **Carrier A uses EXISTING fields, with no new code** (rule 19 / 26: no second mechanism for one
  phenomenon). It is `wefor_residual = 0.0` with
  `wefor_residual_groups = {CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}`. That is the historic-backcast WEFOR cap
  the field already implements, set to zero on the CAMPD-covered gas classes.
- **Carrier B is the new field `spp_gas_crow_residual_outage`** (SPP-only; exclusive with
  `spp_ct_lole_efor`; inert outside an SPP backcast on `outage_source historic`).
  - **Replacement.** `_availability_matrix` zeroes every gas row's statistical WEFOR / POF and records
    its annual rate as the key (`crow_rate_out`).
  - **Allocation.** After `_apply_outage_overlays`, `data.spp_gas_outage.allocate_crow_residual`
    removes `max(0, SPP gas − CAMPD events)`. It uses a capped proportional split (water-filling, so
    nothing is left unplaced), counts events at rated capacity, and excludes COD / retirement edges
    (≥ 30 d, SPP-84's rule) and COD-ramp months.
  - **Data.** `data/raw/spp-gen-outage/` (61,358 market hours, sha `c2baf1c2…`); re-fetch with
    `scripts/data/fetch_spp_capacity_gen_outage.py`.
  - **Matrix.** A row plus a cell in every shard. The SPP cell is O, and SPP's `wefor_residual` cell
    moves U → O for carrier A.
- **Tests.** `tests/iso/spp/test_spp_gas_crow_residual.py` covers the allocator, the seam, the config
  and the data.

**Zero-LP census of the BUILT code path.** Keeper rebuilt `fleet_only` with each arm; the re-clear
instrument is as in §4 (JSON `reclear.<y>.A_built / B_built`). Reach was verified through the real
`--set` → `prb_overrides` channel. For 2024, rated gas unavailability is 10.549 (keeper), 9.717 (A) and
12.183 (B) GW; the census path gives the same numbers.

| $/MWh (Δ gas unavailable, GW) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A, all hours | −0.17 (−0.67) | −0.16 (−0.71) | −0.47 (−0.61) | −0.24 (−0.67) | −0.17 (−0.79) | −0.30 (−0.83) | −0.31 (−0.81) |
| A, upper | −0.28 | −0.24 | −0.35 | −0.49 | −0.30 | −0.56 | −0.58 |
| B, all hours | +0.28 (+1.08) | +0.12 (+0.56) | +4.09 (+0.20) | −0.13 (−0.60) | +0.13 (+0.58) | +1.30 (+1.64) | +0.18 (+0.29) |
| B, upper | +0.60 | +0.32 | −0.05 | −0.14 | +0.31 | **+3.20** | +0.48 |
| B, instrument short hours (keeper 0) | 0 | 0 | 0 | 0 | 0 | **17** | 0 |
| B, events / residual placed (GW) | 7.85 / 2.38 | 6.47 / 1.90 | 7.56 / 1.43 | 7.88 / 0.71 | 6.02 / 2.01 | 6.87 / 3.12 | 7.86 / 1.80 |
| B, binding share | 94 % | 78 % | 55 % | 41 % | 84 % | 82 % | 63 % |

Notes on the census:
- **2021, carrier B.** The +4.09 is Uri, as in SPP-84's instrument: non-linear and February-only
  (upper −0.05).
- **2024, carrier B.** The 17 short hours are a pre-registered risk to unserved energy (E3).

The solve is pre-registered in `docs/records/spp/PRECOMMIT-spp-105-gas-family-outage-2026-09-30.md`.
