# DESIGN — SPP-104: "CT_PEAKER carries no outage" is a measurement artifact; no admissible CT-specific source exists (zero LP, 2026-09-29)

Lane: SPP-104 (availability lane), chartered by the owner card "Record + CT outage lane" (SPP-103).
Keeper: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (2019–2025).
Base: `origin/main` `6b1e7593`. Probe: `scripts/probes/_spp104_ct_availability_phase0.py`.
Numbers: `results/phase0/spp/_spp104_ct_availability_phase0.json`.
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched.**

## 0. Headline

1. **The premise is false in code.** CT_PEAKER is not outage-free. Outside the must-run-floor plants, every CT row takes
   the statistical NERC-GADS stack in `data/fleet/arrays.py::_availability_matrix` (`THERMAL_AVAILABILITY["CT_PEAKER"]`
   = POF 0.03, WEFOR 0.07, derate 0.05, age escalation past 20 yr), with `wefor_multiplier 0.7` from the keeper recipe,
   plus the 12.5 % summer class derate. CTs have no **event-based** (CAMPD window) layer, and that is the only thing they
   lack.
2. **SPP-84's gas gap was measured on a metric that cannot see flat unavailability.** It took each row's *maximum
   available MW over the year* as its capacity (`_spp84_published_outage_rebasis.py:140`). A flat WEFOR or derate is
   then invisible. For CTs this hides ~1.0 GW of the 1.5–1.9 GW the keeper actually removes.
3. **On a like-for-like basis the gap has no consistent sign** (§2). Keeping only outage-type terms (WEFOR, POF, CAMPD
   windows), which is what SPP's CROW report can contain, the keeper's gas outage minus SPP's published is:
   **−1.04 / −0.31 / +0.80 / +1.97 / −0.46 / −1.29 / +0.60 GW (2019–2025)**. SPP-84 reported −2.35 / −1.39 / −0.38 /
   +1.04 / −1.26 / −2.19 and left 2025 unmeasured.
4. **No SPP-own, CT-specific, forward-reproducible source exists** (§3). SPP's portal splits outage by fuel only. The MMU
   splits combined-cycle from "simple-cycle", but its simple-cycle class includes gas steam and is published only as
   charts. The LOLE study publishes GADS EFOR by fuel × size, not by technology, and on a service-hour basis. CAMPD cannot
   detect outages for a unit whose normal state is off.
5. **Recommendation: build nothing. Record it as a model-class limit and close the premise.** A CT outage layer would
   stack on the statistical stack CTs already carry (rule 19). It has no admissible identification (rules 14/21), and
   the measured gap it would fill is not there on a consistent basis.

## 1. How the keeper represents CT_PEAKER availability (code)

| component | CT_PEAKER value in the keeper | applies | in SPP's CROW outage? |
|---|---|---|---|
| WEFOR (forced) | 0.07 × `wefor_multiplier` 0.7 = **0.049** (+0.003/yr past age 20) | all year; 30 % share in Jun–Sep, the rest pushed into shoulder months | yes |
| POF (planned) | **0.03** | shoulder months only (CTs keep POF; `_POF_DROP_GROUPS` excludes them) | yes |
| GADS weather/performance derate | **0.05** (+0.002/yr past age 20) | flat all year | partly (derates ≥ 10 MW are reportable) |
| summer class derate | **12.5 %** (`SUMMER_CLASS_DERATE`) | Jun–Sep | no: MMU Dec-2025 §3.3.1.2 says ambient derates go unreported |
| CAMPD event windows | **none** | — | — |
| CT must-run floor plants | WEFOR and POF removed (`ct_floor_plants`) | none on SPP (`ct_mustrun_per_plant` False) | — |

Why CAMPD skips CTs: the zero-operation window detector treats a unit's normal idle state as "on outage", and that
normal state for a peaker is off. The extracts are derived for coal / CC / ST only (SPP-32 derived gas CC/ST/CHP;
CT_PEAKER was never in scope).

## 2. Phase-0 measurement (keeper rebuilt `fleet_only`, no LP)

Two bases. **Rated:** `pmax − pmax × availability`, all components. **Outage-type:** the same, with the flat GADS derate
and the summer class derate zeroed in the rebuild (a decomposition instrument only, never a config). COD / retirement
edges ≥ 30 days are excluded, as in SPP-84.

| GW, annual mean | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CT_PEAKER pmax | 10.23 | 10.26 | 10.11 | 10.40 | 10.49 | 10.59 | 11.85 |
| CT unavailable, rated | 1.54 | 1.55 | 1.55 | 1.56 | 1.58 | 1.60 | 1.91 |
| CT unavailable, outage-type | 0.63 | 0.63 | 0.65 | 0.64 | 0.65 | 0.65 | 0.91 |
| CT unavailable, SPP-84 metric | 0.53 | 0.53 | 0.55 | 0.54 | 0.54 | 0.55 | 0.79 |
| gas unavailable, rated | 10.67 | 9.35 | 10.31 | 10.75 | 9.07 | 9.96 | 11.24 |
| gas unavailable, outage-type | 9.16 | 7.82 | 8.83 | 9.20 | 7.47 | 8.37 | 9.59 |
| **SPP published gas outage** | 10.19 | 8.13 | 8.03 | 7.23 | 7.93 | 9.66 | **8.99** |
| **keeper − SPP, outage-type** | **−1.04** | **−0.31** | **+0.80** | **+1.97** | **−0.46** | **−1.29** | **+0.60** |
| keeper − SPP, rated | +0.48 | +1.22 | +2.28 | +3.52 | +1.14 | +0.30 | +2.25 |
| keeper − SPP, SPP-84 metric (for reference) | −2.35 | −1.39 | −0.38 | +1.04 | −1.26 | −2.19 | — |

- **2025 is measured here for the first time.** The year zip is 0 bytes, but the 365 daily CSVs download
  (`/2025/<MM>/Capacity-Gen-Outage-<YYYYMMDD>.csv`). Using the last snapshot per market hour over 8,750 hours, gas averages
  **8.99 GW** and coal 4.98 GW.
- **The seasonal shape agrees.** The keeper's CT outage-type MW run ~0.50 GW in winter, ~1.09 GW in the shoulders and
  ~0.15 GW in summer. SPP's published gas outage also peaks in spring and fall and bottoms out in Jul–Aug (2025:
  2.7 GW Jul–Aug, 16.0 GW Apr).
- **The class the gap lives in is not identifiable.** Of the keeper's outage-type gas MW, CC is 2.3–2.9 GW and ST_GAS
  4.5–5.9 GW (statistical ST WEFOR 0.21 × 0.7 **plus** CAMPD windows, since `wefor_residual` is None on SPP). Where the
  keeper is short (2019, 2024), no public series says whether the missing MW are CT, ST or CC.

## 3. Source search (rule 13 forward test, rule 14 alignment)

| candidate | SPP-own? | CT-specific? | forward-reproducible? | verdict |
|---|---|---|---|---|
| Portal `capacity-of-generation-on-outage` (hourly, by fuel) | yes | **no** (Natural Gas MW only) | yes | fuel-level only; the aggregate rebase is SPP-84's DO-NOT-REDO |
| MMU ASOM "Resource outages and derates" (2022 Fig 3–36/37; 2024 Fig 3–17) | yes | **no**: "gas, simple-cycle" includes gas steam (22.7 GW nameplate ≈ keeper CT + ST_GAS) | annual | chart-only (no tables); excludes economic outages. 2022 text: simple-cycle ~34 % of outaged capacity, CC ~15 % |
| MMU "Unavailable Generation Capacity" (Dec 2025) | yes | no (CT/CC/IC pooled) | one-off | confirms ambient derates are unreported; no class outage series |
| SPP LOLE study (2021 report, Tables 10/11) | yes (GADS 2016–20, SPP fleet) | **no** (fuel × size bins) | biennial | EFOR is per service hour, not per calendar hour, which overstates a peaker's calendar-hour unavailability; Natural Gas 13–29 % |
| EIA-860M monthly status | national, unit-level | yes | yes | closed by SPP-84 (0.05–0.45 GW non-OP, all gas) |
| CAMPD hourly for CTs | national, unit-level | yes | yes | outage is unidentifiable from zero output for a unit whose normal state is off |
| NERC GADS by unit type (national) | no | yes | yes | **already the incumbent** (`THERMAL_AVAILABILITY`); swapping one national rate for another fails rule 14 |

**What a forward year would use:** the incumbent statistical stack. Nothing better is admissible. A forecast has no
CAMPD windows either, so CTs are already on the forward construction in both modes.

## 4. The design that would be built, and why it is not recommended

**Form (hypothetical).** Replace the CT_PEAKER WEFOR/POF base with SPP's own LOLE seasonal gas EFOR by size bin. This is a
rule-19 **replacement** inside `_availability_matrix`, not a new layer.
- **Driver / window / forward story (rule 17).** Seasonal (Jun–Sep vs the rest), rebuilt from each biennial LOLE study.
  It is not a floor, so rule 17's window test is trivially met.
- **Parameters (rule 21).** Zero fitted, but it needs one **unidentified mapping** from EFOR (service-hour basis) to a
  calendar-hour derate. SPP publishes neither the service hours nor the EFORd a peaker needs. That mapping would be a
  free parameter chosen by the lane, which is what rule 21 forbids.
- **Rule 14 reconciliation fails.**
  - At face value (13–29 %) CT outage would rise ~0.7–2.3 GW, overshooting SPP's published gas outage in 2021 / 22 / 25,
    where the keeper already runs +0.6 to +2.0 GW over.
  - Its size bins mix CT and gas-steam units, so it cannot be scoped to the CT class.
- **Failure modes.**
  - A stack-on-stack double count with WEFOR if armed additively.
  - Size-bin leakage onto ST_GAS.
  - Selecting a year-varying scaling to fit the published total. That is SPP-84's forbidden pin in another form (rule 13).

**Zero-LP price prediction if something were built anyway.** This linearly scales SPP-84's gas-only re-clear sensitivity
($/MWh per GW of added gas outage) by the outage-type gap. It is an instrument, not a solve.
- **2019:** +1.04 GW → **~+0.4 $/MWh**.
- **2020:** +0.31 GW → **~+0.25**.
- **2023:** +0.46 GW → **~+0.2**.
- **2024:** +1.29 GW → **~+2.0**.
- **2021 / 2022 / 2025:** the keeper is already over SPP's published outage, so a gap-driven CT add has no support. Any
  add would push these years further away.

The charter pre-accepted ~5 pts of C3a damage in 2019/20. The issue is not the damage: the structural basis is absent.

## 5. Recommendation and what changes

- **Record as a model-class limit.** The CT outage basis is the national GADS statistical stack. SPP publishes nothing
  finer that is admissible.
- **Close the premise.** "CT_PEAKER carries no outage" should read "CT_PEAKER carries a statistical (GADS × 0.7) outage
  and no event layer". SPP-84's gas-gap numbers are restated in §2.
- **Side observations (routed, not acted on; outside this charter):**
  - (a) `wefor_multiplier 0.7` scales every class's WEFOR and is a Tier-3 calibration value. Its ledger status on SPP
    is worth an audit.
  - (b) ST_GAS carries full statistical WEFOR **and** CAMPD windows (`wefor_residual` None). This is the double count
    the field's own comment names. On the outage-type basis it is the largest gas term.
  - (c) The rated-minus-outage-type difference is 1.5–1.6 GW of flat derates. The MMU measures unreported ambient
    derates at only 0.19–0.42 GW (all thermal). Whether CT pmax is nameplate or net-summer decides whether the 12.5 %
    summer derate double counts.
- **Matrix (rule 28(b)):** no cell verdict moves; nothing was armed or solved. SPP-104 evidence was appended to
  `SPP.js` `wefor_statistical_stack` (stays U) and `dam_availability_rebasis` (stays O), and a §5.7 note was added.
- **Rules:**
  - 1: nothing selected on a residual.
  - 13: no pin, no rebase.
  - 14: the one candidate SPP source fails reconciliation.
  - 19: no stacking proposed.
  - 21: the only design needs an unidentified mapping.
  - 25: SPP data only.
  - 29(b) / 31–36: no solve, shard, bundle or registration.

## 6. Owner ruling and the zero-LP arm census (2026-09-30)

**Owner card: "Build LOLE-EFOR CT swap"**, over §5's recommendation. Built, default off:
- **Field** `spp_ct_lole_efor`. It is SPP-only and raises for any other ISO.
- **Table** `constants.SPP_LOLE_GAS_EFOR_BY_SIZE`: 2023 SPP LOLE Report Tables 9/10, GADS 2015–2022.
- **Helper** `data/fleet/ct_lole_efor.py`: a per-plant, capacity-weighted mean over the per-unit EIA-860 roster.
- **Branch** in `arrays._availability_matrix`: `1 − EFOR(season) − derate − POF(shoulder)`, then the unchanged summer
  class derate. `wefor_multiplier`, `SUMMER_WEFOR_SHARE` and WEFOR age escalation no longer reach a CT row.
- **Tests** `tests/iso/spp/test_spp_ct_lole_efor.py`, plus the matrix row and a cell in every shard.

**The §4 "unidentified mapping" is resolved without a free parameter.** Each LOLE report's Appendix A defines SERVM's
unit process as `ttf = ttr·(1−EFOR)/EFOR`, running in every hour. Its steady-state outage probability is EFOR itself. So
SPP's own model already applies the published EFOR as an all-hours rate, and this field copies that construction; it
does not choose one.

**Vintage, declared ex ante.** One table for every year (rule 1(b) spirit): the 2023 report. Its GADS window 2015–2022
covers the 2019–22 backcast years. The 2025 report (April 2026) publishes only projected 2030/2032-fleet columns, which
fit a forecast year, not a 2019–25 fleet. For a forward year, the latest biennial report regenerates the table (rule 13).
The 2017 report used EFORd, a different statistic, and is not mixed in.

**Zero-LP arm census** (keeper rebuilt `fleet_only` with the field armed; `_spp104_ct_availability_phase0.json`,
`arm_*` blocks). All CT plants resolve in the roster in every year; 0 fall back.

| GW, annual mean | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CT unavailable, rated: keeper → arm | 1.54 → 3.22 | 1.55 → 3.23 | 1.55 → 3.20 | 1.56 → 3.27 | 1.58 → 3.31 | 1.60 → 3.33 | 1.91 → 3.70 |
| CT outage-type: keeper → arm | 0.63 → 2.38 | 0.63 → 2.39 | 0.65 → 2.38 | 0.64 → 2.42 | 0.65 → 2.44 | 0.65 → 2.47 | 0.91 → 2.78 |
| gas outage-type − SPP published: keeper | −1.04 | −0.31 | +0.80 | +1.97 | −0.46 | −1.29 | +0.60 |
| gas outage-type − SPP published: **arm** | **+0.71** | **+1.45** | **+2.53** | **+3.75** | **+1.33** | **+0.52** | **+2.47** |

**Reading.**
- The arm overshoots SPP's own measured gas outage in **every** year, not only in the three years §4 predicted.
- Its summer is the sharpest cross-check. The CT class alone is out ~1.85–2.2 GW in Jun–Sep, against SPP's published
  **all-gas** outage of ~2.7 GW in Jul–Aug 2025 (5.1 GW Aug 2019). That puts ~70 % of SPP's total gas outage on CTs.
- This is the rule-14 signature of the service-hour-basis EFOR overstating a peaker's calendar-hour unavailability.
- **Price prediction**, from SPP-84's gas-only re-clear sensitivity scaled to +1.7 GW: roughly
  **+0.7 / +1.4 / large / ≈0 / +0.6 / +2.6 $/MWh** (2019 / 20 / 21 / 22 / 23 / 24).
  - 2021 is Uri-dominated and non-linear in SPP-84's instrument (+7.06 on only +0.38 GW), so a large rise is expected
    there.
  - 2022 took +0.03 on +1.04 GW.
  - Every sign is **up**, which is the wrong direction for the already over-priced 2019–21 C3a years.
