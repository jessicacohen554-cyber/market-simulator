# FINDING — capx D33: the MISO additions under-build is a SITING defect. The entry screen put every new solar MW in the one MISO zone no compliance region admits, priced it at a $0 REC credit against the run's own $30/MWh ACP, and declined it in every screen year. Coverage was never the gap — at the vintage-2020 cutoff the known-additions channel can reach 5.6 % of the solar the market built

**Lane:** capx D33 — the ADDITIONS repair upstream of D31's FC-3 exit-residual
chain (`FINDING-capx-d31-miso-caprev-repair-2026-09-02.md` §7).
**Pre-declaration:** `PREDECL-capx-d33-miso-additions-repair-2026-09-02.md`,
pushed at `dc0f4b84` BEFORE the solve started; graded at full magnitude in §6,
misses included.
**Run:** `miso-2021-2025-realized-t1h-d33`, registered to the bare `miso-t1h`
key; the D31 record preserved at `miso-t1h-pre-d33` (D31's own preserved
`miso-t1h-pre-d31` and D27's `miso-t1h-pre-d27` untouched).
**Diagnostic probe:** `miso-d33-probe-entrydiag` (key `1b0f1a5e75719b92`) — the
D31 recipe plus the decision-neutral `--entry-screen-diagnostics` arm. Its 2025
decisions reproduce D31's to the MW, which is what licenses reading its screen
rows as D31's own.
**Rule 14 [R-ACCURATE] sign discipline (binding).** Nothing below was sized,
tuned, or sequenced by what it does to the exit residual or to any band. The
repair has **zero free parameters**, so there was nothing to size. Both legs
were identified from committed sources and the probe's committed artifacts
BEFORE the pre-declaration, which was pushed before the solve.

---

## 0. Verdict (one paragraph)

*(Lands with the measured run — §5.)*

## 1. Leg 1 — the planned-additions coverage audit (a MEASUREMENT, not a knob)

**The question the charter set:** does the missed ~20 GW sit *absent from the
vintage file*, *present-but-status-filtered*, or *present-but-slipped*?

**Method.** Every MISO generator that actually reached commercial operation in
2021–2025 — canonical EIA-860 release, thermal generator sheet plus the solar
and wind schedules, BA-mapped through the loaders' own `BA_CODE_TO_ISO`; **716
units, 31.151 GW** (solar 18.649 / wind 7.200 / gas_cc 3.867 / gas_ct 1.355 /
oil 0.053 / gas_st 0.024 / biomass 0.003 — the solar and wind totals reproduce
the T1-H scorer's `add.by_tech` actuals exactly) — traced back to each hindcast
vintage's `eia860_generator_proposed.parquet` by `(Plant Code, Generator ID)`
and bucketed by what the channel's own three gates do to it.

**The reconciliation table, at the run's vintage-2020 information cutoff (GW):**

| where the MW sits | biomass | gas_cc | gas_ct | gas_st | oil | **solar** | **wind** | TOTAL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **1 absent from the vintage file** | 0.003 | 1.238 | 0.708 | 0.008 | 0.046 | **16.021** | **3.977** | **22.001** |
| 2 status-filtered (not U/V/TS) | 0.000 | 0.156 | 0.150 | 0.000 | 0.000 | 1.264 | 0.675 | 2.245 |
| 3 vintage gate (`Effective Year` ≤ 2020) | 0.000 | 0.000 | 0.005 | 0.016 | 0.002 | 0.327 | 1.164 | 1.514 |
| **4 delivered by the channel** | 0.000 | **2.473** | 0.492 | 0.000 | 0.005 | **1.036** | **1.384** | **5.390** |

Status-filter detail (vintage 2020): solar L 0.480 / P 0.459 / T 0.325; wind
L 0.318 / P 0.302 / T 0.054; gas_cc L 0.156; gas_ct P 0.088 / T 0.062.

**The answer: ABSENT, overwhelmingly, and the absence is the information gate
working — not a defect.** Coverage of the whole 2021–2025 wave is **17.3 %**;
of solar **5.6 %** (1.036 of 18.649 GW) and of wind **19.2 %** (1.384 of
7.200). **85.9 % of the solar was never filed with EIA at the 2020 cutoff.**
Admitting *both* remaining buckets — the P/L/T statuses the channel excludes on
instrument grounds and the rows whose effective year precedes the vintage, a
rule-13 widening this lane does **not** propose — would raise the solar ceiling
only to **2.627 of 18.649 GW (14.1 %)**.

**And the ceiling is a property of the horizon, not of 2020.** Repeating the
audit at every vintage, scored against the CODs that vintage could still see:

| vintage | window | coverage, all techs | solar | wind |
|---|---|---:|---:|---:|
| 2020 | 2021–2025 | 5.390 / 31.151 = **17.3 %** | 1.036 / 18.649 = **5.6 %** | 1.384 / 7.200 = **19.2 %** |
| 2021 | 2022–2025 | 2.958 / 25.767 = 11.5 % | 1.055 / 17.457 = 6.0 % | 0.449 / 4.515 = 10.0 % |
| 2022 | 2023–2025 | 4.548 / 21.394 = 21.3 % | 2.242 / 16.126 = 13.9 % | 0.960 / 3.093 = 31.0 % |
| 2023 | 2024–2025 | 6.350 / 16.555 = 38.4 % | 4.830 / 13.368 = 36.1 % | 0.223 / 1.707 = 13.1 % |
| 2024 | 2025 only | 4.378 / 9.501 = 46.1 % | 2.462 / 7.145 = 34.5 % | 0.644 / 1.082 = 59.5 % |

Coverage rises monotonically as the horizon shortens and still tops out near
half at one year out. **A construction-committed pipeline read at a vintage
cutoff cannot carry a five-year VRE build wave, and no repair to that channel
can close a 17 GW solar gap.** Leg 1's deliverable is therefore a *negative*
result that redirects the lane: the residual belongs to step 5.

**Consequently nothing in leg 1 is armed.** The FFR-5E procurement channel
(`vre_procurement_additions_enabled`) stays default-OFF. Measured content at
vintage 2020 for MISO: 1,034.4 MW solar (583.4 in 2021, 451.0 in 2022) and
1,380.0 MW wind (2021) — **every row with a COD before the scored window**, so
arming it moves no addition band at all. That is the same fact behind FFR-5E-H's
DEFER verdict, now quantified from the source.

## 2. Leg 2 — the economic-entry screen: what the screen actually said

Measured on the probe's committed `entry_screen_diagnostics` rows (five
candidates per screen year; `$/MW-yr`):

| screen year | tech | energy rev | **attribute rev** | capacity rev | annual cost | margin | binding cap |
|---|---|---:|---:|---:|---:|---:|---|
| 2022 | wind | 99,704.3 | **0.0** | 0.0 | 103,623.2 | −3,918.9 | `unprofitable` |
| 2022 | solar | 69,369.3 | **0.0** | 0.0 | 94,204.4 | −24,835.1 | `unprofitable` |
| 2023 | wind | 99,704.3 | **0.0** | 0.0 | 101,584.5 | −1,880.3 | `unprofitable` |
| 2023 | solar | 69,369.3 | **0.0** | 0.0 | 90,439.6 | −21,070.2 | `unprofitable` |
| 2024 | wind | 78,938.1 | **0.0** | 0.0 | 99,757.2 | −20,819.1 | `unprofitable` |
| 2024 | solar | 52,773.6 | **0.0** | 0.0 | 87,371.7 | −34,598.1 | `unprofitable` |
| 2025 | wind | 76,723.2 | **0.0** | 53,758.9 | 98,104.1 | +32,377.9 | `per_tech_cap` (4,000.0) |
| 2025 | solar | 51,005.3 | **0.0** | 125,491.3 | 84,801.9 | +91,694.7 | `growth_ladder` (1,236.4) |

gas_cc and gas_ct are `unprofitable` in 2022/2023/2024 on the same rows and
clear only in 2025. **The 2022 and 2023 VRE energy-revenue figures are
byte-identical because 2022 is the bridge year and its screen reads 2021's
solved prices — checked, not assumed; 2024 moves.**

Three things follow, and only one of them is this lane's.

1. **The attribute leg is EXACTLY zero on every VRE row in every year**, while
   the same runs' ledgers record `rps_dual` = 30.0 (the field is
   `np.max(per-zone vector)`, `runner.py:4270`). The screen is leaving the
   ISO's entire REC price on the table.
2. **The whole screen is dead until 2025**, and what wakes it is the capacity
   leg D31 repaired — not anything about VRE.
3. **In 2025 solar is already profitable and clipped by its ladder** at
   1,236.4 MW = 2 × the measured vintage-2020 seed 0.6182 GW. So the additions
   band is not one binder but two in sequence: a dead screen, then a ladder that
   never ratcheted because the screen was dead.

### 2.1 Why the attribute leg is zero: it is zero BY CONSTRUCTION

`RENEWABLE_ZONE_ALLOCATION["MISO"]` sends **100 % of economically-entered solar
to MISO-South** and all wind to MISO-West. Resolving
`MISO_RPS_COMPLIANCE_REGIONS` onto the model's zone ordering through the
shipped `build_rps_region_arrays` gives each zone's REC-eligibility set —
`p[z] = max{dual_r : z ∈ eligible(r)}`:

| model zone | rows whose certificates it may generate |
|---|---|
| MISO-West | MN, WI, MO (the Midwest footprint) |
| MISO-Plains | MN, WI, MO |
| MISO-Illinois | MN, WI, MO, **IL** (IL is MISO-Illinois-only) |
| MISO-Indiana | MN, WI, MO |
| MISO-East | MN, WI, MO, **MI** (MI is MISO-East-only) |
| **MISO-South** | **NONE — eligible under no compliance region at all** |

`MISO_RPS_MIDWEST_FOOTPRINT_ZONES` omits MISO-South by construction
(AR/LA/MS/E-TX carry no standard and sit behind the RDT), and neither
zone-restricted row reaches it. **A solar candidate sited in MISO-South earns a
$0 REC credit in every year of every run, whatever the market is paying.**

And the $30 is real and reachable. From the committed artifacts alone:
`max_z p[z] = 30.0` (the ledger), `p[MISO-West] = −0.0` and
`p[MISO-South] = 0.0` (the probe's own screen rows). `p[MISO-West] = 0` forces
**MN = WI = MO = 0**, so every footprint-only zone is 0 — which leaves the
$30 in **MISO-East and/or MISO-Illinois**, the two zone-restricted rows.
**The screen sites new solar in the one zone that can never earn the credit,
while the credit sits at the $30/MWh ACP in zones it never considers.**

### 2.2 And the bucket is not where the market builds

MISO's actual 2021–2025 VRE by model zone (EIA-860 CODs on the model's own
state→zone map, GW):

| model zone | solar | wind |
|---|---:|---:|
| MISO-East | 4.061 (21.8 %) | 1.235 (17.2 %) |
| MISO-Illinois | 3.536 (19.0 %) | 1.486 (20.6 %) |
| MISO-South | 4.520 (24.2 %) | 0.328 (4.6 %) |
| MISO-Indiana | 3.687 (19.8 %) | 0.704 (9.8 %) |
| MISO-Plains | 1.957 (10.5 %) | 1.934 (26.9 %) |
| MISO-West | 0.887 (4.8 %) | 1.512 (21.0 %) |

**75.8 % of the solar and 79.0 % of the wind was built outside the bucket the
screen values it in.** The single-bucket table's own docstring calls it the
FALLBACK "used only when EIA-860 plant-location data is unavailable"; the
existing fleet is distributed from coordinates, and the FFR-5E procurement
channel sites each procured row from its plant coordinates precisely so it does
**not** land in that bucket (`eia860.py:2690`, citing FFR-3V §4.4). **The
economic screen was the last consumer still on the fallback.**

## 3. The repair

`ScenarioConfig.entry_vre_zone_selection` — GATED, **default False**
(`cache_key(ScenarioConfig())` unchanged at `603c2498bf71d21d`; armed it is
`e5311e5163fefbaf`), **armed for MISO only** through
`ISOConfig.default_scenario_overrides`, the D-2′/D-30 precedent. Rule 25
[R-ISO-SCOPE]: the mechanism is ISO-agnostic, the arming is MISO's alone, every
other ISO is byte-identical and arming one is its own decision on its own
evidence.

Armed, the screen values each VRE candidate **in every zone that carries the
resource** and sites it where its own margin is highest, over machinery the
screen already had:

* the zone's hourly CF profile and **that zone's** LP prices (the shape-aware
  revenue path, unchanged — only its zone argument moves);
* the K-row **zone-resolved** REC credit (`rps_credit_for_zone`) and clean-tier
  credit (`clean_credit_for_zone`), through the same one shared consumer helper;
* the zonal RA gate, through **one** construction of the capacity payment (a
  shared closure consumed by both the chooser and the screen), so a candidate
  can never be ranked on one payment and screened on another — rule 19
  [R-ONE-MECH].

Annualized cost is zone-invariant, so `argmax(revenue)` **is** `argmax(margin)`.

**Why it is admissible.** Rule 21 [R-DOF]: **no free parameter** — there is
nothing in the mechanism a residual could have set. Rule 13 [R-MEASURED]: no
measured outcome enters — the eligibility masks are statute
(`MISO_RPS_COMPLIANCE_REGIONS`, each row cited to its enabling act), the CF
profiles and prices are the model's own, and the whole construction regenerates
for any forward year and moves when conditions move. The §2.2 build-share table
is **evidence that the bucket is unrepresentative, never an input**: no share,
weight or target from it appears anywhere in the code.

**Tie discipline (the guard against a gate that relocates on no information).**
The allocation bucket is the incumbent and is displaced only by a **strictly**
better zone. A zone-blind scalar RPS dual, a flat price surface, absent zonal CF
or price inputs, or an exact tie all leave siting exactly where the gate-off
path puts it. Pinned by `tests/unit/model/test_entry_vre_zone_selection.py`
(10 tests + 3 subtests), which also pins the off-path bucket behaviour, the
off-path *insensitivity to where the REC price is* — the defect itself, made a
regression — the MISO-only arming, and the byte-stable default cache key.

**What the repair is NOT.** It does not touch the growth ladder, the queue caps,
the pending-stock netting, any FOM, threshold or execution lag, the reliability
floor, `_floor_retention_merit` (D32's object, untouched), the D31 accounting
ratio, or the published RBDC curves.

## 4. The measured consequence

*(Lands with the run — §5.)*

## 5. The T1-H run

*(Lands with the run.)*

## 6. The pre-declaration, graded at full magnitude

*(Lands with the run.)*

## 7. Exit-residual direction, stated honestly (rule 14)

*(Lands with the run.)*

## 8. What remains routed

*(Lands with the run.)*

## 9. Governance attestation

*(Lands with the run.)*
