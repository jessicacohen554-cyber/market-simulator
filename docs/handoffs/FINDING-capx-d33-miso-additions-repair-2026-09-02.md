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
**Owner-facing chart brief:** https://claude.ai/code/artifact/bcee1d9b-a5d7-49c3-9302-4f7a6559096f
**Rule 14 [R-ACCURATE] sign discipline (binding).** Nothing below was sized,
tuned, or sequenced by what it does to the exit residual or to any band. The
repair has **zero free parameters**, so there was nothing to size. Both legs
were identified from committed sources and the probe's committed artifacts
BEFORE the pre-declaration, which was pushed before the solve.

---

## 0. Verdict (one paragraph)

**The additions defect is a SITING defect, it is repaired, and repairing it does
exactly NOTHING to the exit residual — which is the lane's most important
result, because it amends D31 §7.** The entry screen sited 100 % of new MISO
solar in MISO-South, the one model zone eligible under **no** state compliance
region, screened it at a $0 REC credit against the run's own $30/MWh ACP, and
declined **every candidate in every screen year 2022/2023/2024**; 75.8 % of the
solar the market actually built was outside that bucket. Coverage was never the
alternative: at the run's vintage-2020 cutoff the known-additions channel can
reach **5.6 % of that solar** (1.036 of 18.649 GW), 85.9 % of it having never
been filed with EIA at the cutoff. With `entry_vre_zone_selection` armed for
MISO the screen fires in **every** year and every decided VRE row sites in
**MISO-East or MISO-Illinois** — the REC-eligible zones — never MISO-South:
`add.by_tech.wind` **4.000 → 8.000 GW** against 7.200 actual, band **FAIL →
PASS**; `add.by_tech.solar` **1.236 → 4.946 GW**, still FAIL at −73.5 %; the
FC-3 band-FAIL list goes **9 rows → 8**; all 14 invariants stay PASS. Solar's
remaining shortfall is not the siting repair's — it is the FFR-4A pending-stock
netting holding the ladder at its measured vintage-2020 seed cap of
1,236.4 MW/yr in every year, exactly as pre-declared. **And the exit side does
not move at all**: `retire.total_gw` stays **4.469 GW (−74.3 %)** and
`unit_recall_gt300` stays **5/19**, with the pipeline **event-for-event
identical to D31 in every year** — same 3,684.0 MW all-coal decided cohort, same
`entry_capped` sets to the MW. +7.7 GW of new VRE decisions, 5.236 GW of it
commissioned inside the window, released **exactly zero** additional exits,
because the first cohort commissions at step 4.5 of 2024 — *after* that year's
retirement screen — and the 2025 screen fails no unit in either run. **D31 §7's
chain "additions under-build → floor binds → exits throttled" is refuted at this
magnitude: on this evidence the additions residual and the exit residual are
independent objects.** Determination **HOLD, unchanged**, on FC-3 alone.

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

## 4. The measured consequence — the additions side

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d33
```

Bare HEAD recipe, every solve-affecting flag omitted — the arming reaches the
solve through MISO's own `default_scenario_overrides`, not the CLI, and
`run_config.json` records `entry_vre_zone_selection: true` (P0). Solved
`[2021, 2023, 2024, 2025]`, bridged `[2022]`, scored 2023–2025; ~20 min. Cache
key **`40173304213d39cd`** — neither D31's `3649264ca98a1fb4` nor the probe's
`1b0f1a5e75719b92`; the fresh out-dir was the fresh-solve guard. One environment
note, disclosed: the first launch of the *probe* died on the fresh checkout's
absent `data/clean/confirmed-retirements` partition (regenerated per the error's
own instruction; no solve had started) — the same note D31 carried.


The screen now fires in **every** year, and it fires in the REC-eligible zones.
Every decided VRE row, from the run's own committed `entry_pipeline` ledgers:

| decision year | tech | MW | **build zone** | COD |
|---|---|---:|---|---:|
| 2022 (bridge screen) | wind | 4,000.0 | **MISO-Illinois** | 2024 |
| 2022 (bridge screen) | solar | 1,236.4 | **MISO-East** | 2024 |
| 2023 | solar | 1,236.4 | **MISO-East** | 2025 |
| 2024 | wind | 4,000.0 | **MISO-Illinois** | 2026 |
| 2024 | solar | 1,236.4 | **MISO-Illinois** | 2026 |
| 2025 | solar | 1,236.4 | **MISO-East** | 2027 |
| 2025 | gas_cc / gas_ct | 3,000.0 / 1,471.6 | MISO-Illinois | 2027 |

**Not one row sites in MISO-South or MISO-West.** In D31 the only VRE rows in
the whole run were the 2025 pair, sited in MISO-South (solar) and MISO-West
(wind) — the two zones whose REC credit is 0.

The zonal pools grow for the first time: `solar_cap_mw` 2,048.0 → **3,284.4**
(2024) → **4,520.8** (2025), and wind takes +4,000 MW in 2024. In D31 the pools
sat at 2,048.0 for the entire 2021–2025 window.

**The score** (committed `score.json`; bands per the T1-H rubric):

| row | D31 | **D33** | actual | band |
|---|---:|---:|---:|---|
| `add.by_tech.wind` | 4.000 (−44.4 %) | **8.000 (+11.1 %)** | 7.200 | **FAIL → PASS** |
| `add.by_tech.solar` | 1.236 (−93.4 %) | **4.946 (−73.5 %)** | 18.649 | FAIL (both) |
| `add.by_tech.gas_cc` | 4.146 (+7.2 %) | 4.146 (+7.2 %) | 3.867 | PASS (both) |
| `add.by_tech.gas_ct` | 1.472 (+8.6 %) | 1.472 (+8.6 %) | 1.355 | PASS (both) |
| `add.by_tech.storage` | 4.000 (+437.7 %) | 4.000 (+437.7 %) | 0.744 | FAIL (both) |
| model total additions | 14.854 | **22.563** | 31.981 | — |
| `add.shares.wind` | +4.4 pp PASS | **+12.9 pp FAIL** | — | **PASS → FAIL** |
| `add.shares.gas_ct` | +5.7 pp FAIL | **+2.3 pp PASS** | — | **FAIL → PASS** |
| `retire.total_gw` | 4.469 (−74.3 %) | **4.469 (−74.3 %)** | 17.369 | FAIL (both) |
| `retire.unit_recall_gt300` | 5/19 (0.263) | **5/19 (0.263)** | — | FAIL (both) |

FC-3's band-FAIL list goes **9 rows → 8**: `add.by_tech.wind` and
`add.shares.gas_ct` out, `add.shares.wind` in. The share flip is honest and
worth naming: fixing wind's *volume* made wind's *share* wrong, because solar
did not keep up — the composition is still solar-short, which is the same object
under a different row.

**All 14 forecast invariants PASS** on the committed sidecar (I1 energy balance
7.3e-11 MW; I12 reserve-margin band "all in-band"; I7 "held"), matching D31's
clean record.

### 4.1 Why solar is still short — and it is not the siting repair

Solar decides **exactly 1,236.4 MW in every one of 2022 / 2023 / 2024 / 2025**.
That is `ENTRY_GROWTH_LIMIT_MULTIPLE × 0.6182 GW`, the measured EIA-860
vintage-2020 MISO seed — i.e. **the growth ladder's opening cap, in every year,
never ratcheted**. The ratchet is killed by the FFR-4A pending-stock netting:
with `entry_pipeline_aware_signal` OFF and a 2-year COD lag, the pending stock
(a MW quantity, no time denominator) is subtracted from an annual flow cap, so
`K − L + 1 = 1` and a tech building at its cap never raises it. 2023 is the
arithmetic in one line: prior-max rises to 1.2364 GW, the cap doubles to
2,472.8 MW, the 2022 row's 1,236.4 MW is still pending, room = 1,236.4.

Against a market that reached **7.145 GW of solar in 2025 alone**, a ladder
pinned at 1.24 GW/yr cannot close the band whatever the siting is. **This was
pre-declared as the ceiling on the repair (P3), and the measurement confirms the
mechanism, not just the number.** It is the `entry_rate_limits` /
`entry_pipeline_aware_signal` object, already adjudicated `O` in MISO's matrix
column with a measured armed series on the same cell — not this lane's to arm.

## 5. The measured consequence — the exit side is a NULL, and it amends D31 §7

**Every retirement row is identical to D31 to the decimal**, and so is the
pipeline that produced it:

| year | event | D31 | **D33** |
|---|---|---:|---:|
| 2022 (bridge screen) | `decided` | 3,684.0 MW coal | **3,684.0 MW coal** |
| 2022 | `entry_capped` | coal 27,247.4 / gas_cc 27,223.5 / gas_ct 24,385.0 / gas_st 13,942.2 / oil 3,516.9 | **identical, to the MW** |
| 2023 | `re_confirmed` / `entry_capped` | 3,684.0 / same five classes | **identical** |
| 2024 | `executed` / `entry_capped` | 3,684.0 coal / coal 51,880.5 + four classes | **identical** |
| 2025 | any screen event | none | **none** |
| — | `retire.total_gw` | 4.469 GW | **4.469 GW** |
| — | `unit_recall_gt300` | 5/19 | **5/19** |

The ONLY thing that moved on the exit side is the reserve margin:
**2024 0.015662 → 0.023699** (+0.80 pp) and **2025 0.064675 → 0.076359**
(+1.17 pp) — on the run's own requirement basis, ≈ **0.98 GW** and ≈ **1.40 GW**
of additional accredited firm capacity. Real headroom, and it released nothing.

**Why, read off the run's own ledgers rather than argued.** Two reasons compose:

1. **Sequencing.** The first VRE cohort (4,000 MW wind + 1,236.4 MW solar,
   decided 2022) commissions at **step 4.5 of 2024**, *after* that year's
   economic-retirement screen (step 3). The 2024 screen therefore sees the
   2023-evolved fleet, exactly as D31's did — which is why its `entry_capped`
   set reproduces D31's to the megawatt. The 2025 screen *does* see the cohort,
   and fails **no unit** in either run. So inside a 2021–2025 window the
   headroom never reaches an exit decision at all.
2. **Magnitude.** Even if it had, ≈1 GW of accredited capacity is not the right
   order. The gap between the model's 4.469 GW of exits and the market's
   17.369 GW is ~12.9 GW of nameplate sitting behind an admission cap that holds
   ~27 GW of coal and ~100 % of the entire gas_ct, gas_st and oil fleets
   (D27 §4). At the ≈19 % effective accreditation this cohort realizes, closing
   that would take **tens of GW** of VRE nameplate — more than the 26 GW the
   real market built over the whole window.

**The consequence for D31 §7, stated plainly.** D31 attributed the exit residual
**downstream** of the additions residual: "the floor holds the census at the
requirement precisely because nothing new arrives to create headroom … the
under-build is the only term left that can starve the release." That inference
was reasonable on D31's evidence and it is **refuted at this magnitude by
direct measurement**: something new now arrives, the census does gain headroom,
and the release is bit-for-bit unchanged. The two residuals are, on this
evidence, **independent objects**. The exit residual's owner is back where D27
put it — the admission cap and the retention key (**D32**), which this lane did
not touch.

## 6. The pre-declaration, graded at full magnitude

**P0 — the arming reaches the solve: HIT.** `run_config.json` records
`entry_vre_zone_selection: true`; cache key `40173304213d39cd`, neither D31's
`3649264ca98a1fb4` nor the probe's `1b0f1a5e75719b92`.

**P1 — the attribute leg turns on in a REC-eligible zone: HIT, exactly.** Every
decided VRE row sites in MISO-East or MISO-Illinois — the declared set — and
none in MISO-South or MISO-West. The falsifier (siting unchanged ⇒
identification refuted) did not fire.

**P2 — entry fires before 2025: HIT, and stronger than declared.** I declared
"at least two of 2022/2023/2024"; **all three** fired. The central expectation
("solar decides 1,236.4 MW in 2022") is exact. **Its trailing clause — "and the
ladder then ratchets" — is a MISS:** the ladder never ratcheted, held at
1,236.4 MW/yr in all four years by the pending-stock netting. I had that
mechanism right in P3's rationale and wrong in P2's sentence; the two clauses
contradicted each other in the pre-declaration and the measurement settled it
against P2.

**P3 — the addition bands: HIT on both, including the ceiling's mechanism.**
Solar 4.946 GW is inside the declared **2.0–5.5 GW** band and −73.5 % is inside
the declared −70 % to −89 %. Wind 8.000 GW is inside the declared **4.0–8.0 GW**
band (at its top edge) and the declared *possibility* — "may cross into PASS" —
materialized (+11.1 %, band 5.400–9.000). Storage unchanged at 4.000 GW as
declared. The falsifier (solar does not rise) did not fire. The declared
**reason** for the ceiling — the FFR-4A netting throttling the ratchet — is
confirmed by the per-year decision series, not merely consistent with it.

**P4 — the exit residual: MISS, on direction and on band.** I declared "more
exits than D31's 4.469 GW", band **4.5–12.0 GW**. Measured: **4.469 GW,
identical to D31** — below the band's floor, and no movement in the declared
direction. The falsifier ("falls below 4.469") did not fire, so the miss is a
null rather than a reversal. **This is the lane's most consequential miss and it
is the finding** (§5): I inherited D31 §7's downstream attribution and
pre-declared from it; the measurement refuted the attribution. The sequencing
reason (the cohort commissions after the screen) was available in the code
before the solve and I did not check it — that is the error, not the band width.

**P5 — invariants hold: HIT.** All 14 PASS.

**P6 — declared, not predicted.** The gas bands did **not** break in either
direction: `gas_cc` +7.2 % PASS and `gas_ct` +8.6 % PASS, byte-identical to
D31, because both are set by the known-additions channel plus the 2025 decision
and neither moved. What did move unpredicted is the **share** pair
(`add.shares.wind` PASS → FAIL, `add.shares.gas_ct` FAIL → PASS), reported at
full magnitude in §4.

**P7 — governance: HIT on every leg.** Determination HOLD on FC-3 alone; the
ff-verdicts edit is a pure two-key change (`miso-t1h` replaced,
`miso-t1h-pre-d33` inserted, 110 lines inserted and zero deleted); the
cross-lane STOP condition was checked against the diff and did not trigger.

**Scorecard: every structural and directional prediction about the REPAIR hit,
including the exact zone set and the ceiling's mechanism; the one prediction
inherited from another lane's attribution (P4) missed completely, and that miss
is the result worth having.**

### 6.1 A cross-lane discharge, with the opposite sign

capx **D39** §5.3, merged into main one day into this session, names exactly
this object as an open precondition: the committed MISO screen ledgers credit
solar `attribute_price 0.0` while the registered D27/D31 T1-H ledgers carry
`rps_dual = 30.0`, "a $57.8 k/MW-yr attribute credit the committed screen rows
never saw — enough on its own to flip the ledgers' solar margins positive. No
diagnostics-on ledger exists at the live MISO posture; this is a precondition
item, not a finding about the sign."

**This lane's probe IS that ledger, and it settles the sign the other way.** At
the live posture the attribute credit is **0.0 on every VRE row in every screen
year** — not because the dual is absent, but because the dual is a *per-zone
vector* and the candidate is sited in the one zone no row admits. D39's
inference from the scalar was the natural one and it was wrong for the same
reason the screen was: the scalar `rps_dual` in the ledger is
`np.max(vector)`, and the zonal grain is invisible in it. §5.3 is discharged.

## 7. Exit-residual direction, stated honestly (rule 14)

**Direction: none. Magnitude: zero. That is the measurement, and nothing in this
lane was arranged to produce it.**

The charter pre-authorized either sign. The repair moves the additions residual
toward the actual on both VRE rows and moves the exit residual **not at all** —
`retire.total_gw` identical to nine significant figures, the pipeline identical
event by event. There is no parameter in `entry_vre_zone_selection` that could
have been set to a different answer: the zone chooser has zero free values, and
the two things it reads (statutory eligibility masks, the model's own zonal CFs
and duals) were both fixed before the lane opened.

What the null establishes, and what it does not:

* **It establishes** that the additions and exit residuals are separable in
  MISO's T1-H window: a 55 % increase in modelled additions (14.854 → 22.563 GW)
  bought zero exits. Any future claim that fixing entry will fix the exit side
  now has a measured counterexample to clear.
* **It does not establish** that additions never matter to exits — only that
  they do not inside a 5-year window whose first VRE cohort commissions after
  the second-to-last screen. A longer horizon, or a repair that also moved the
  ladder, would test the proposition properly; this run cannot.
* **It does not reopen anything.** D31's ratio and RBDC curves are untouched;
  D32's `_floor_retention_merit` is neither read nor written here; non-coal
  fossil exits remain exactly 0.000 GW, as in D27 and D31.

## 8. What remains routed

1. **D32 — the floor-retention key's composition monopoly.** Untouched by
   charter, and this lane's null **strengthens** its priority: with additions
   demonstrably not the exit lever, the admission cap and the retention key are
   where the −74.3 % lives. Non-coal fossil exits are still exactly 0.000 GW.
2. **The solar ladder (`entry_rate_limits` / `entry_pipeline_aware_signal`).**
   §4.1 measures the remaining solar shortfall to the pending-stock netting,
   whose armed MISO series is already recorded on the matrix cell
   (1,236 → 2,472 → 4,944 → 6,000 MW/yr). Arming it is a separate decision on
   its own evidence and was refused here — it is the ceiling on this band, not
   part of this repair.
3. **The 2025 entry screen's capacity leg** (pre-declaration §3, disclosed
   before the solve and unchanged by it): the probe prices it at $304.4 k /
   $307.7 k / $125.5 k / $53.8 k per MW-yr for gas_ct / gas_cc / solar / wind,
   roughly 4× MISO's ~$79.8 k/MW-yr annual net-CONE anchor, and it is why every
   2025 candidate clears at its cap. That is the D31 RBDC seam read at the entry
   screen's own forward `reserve_position`; **D31's closed repairs may not be
   revisited because a residual moved** (rules 13/14/23). Routed to the
   capacity-price lane, named so it cannot be mistaken for something D33
   introduced.
4. **Arming `entry_vre_zone_selection` in any other ISO** — five `U` cells, each
   its own decision on its own evidence (rule 25). The identification that would
   open one is that ISO's own: whether its allocation bucket is materially
   unrepresentative of where its market builds, and whether its RPS/clean rows
   are zone-restricted enough for the bucket to change the attribute credit.
   MISO is the extreme case; an ISO with one footprint-wide REC product has no
   attribute leg to gain.
5. **Unchanged from D31 §8:** per-class SAC accreditation intake; the seasonal
   accreditation basis; the BTMG operating-mode split; the cross-ISO clearing
   D6; the director's 8-failure unit-test census.

## 9. Governance attestation

**Rule 12 [R-PARALLEL]:** years sequential within each invocation (the runner's
design); the diagnostic probe and the registered run were run **sequentially,
not concurrently** — this environment holds 15 GB and a single MISO T1-H solve
peaks near 8 GB, so a second concurrent invocation would have OOMed.
**Rule 13 [R-MEASURED] / 14 [R-ACCURATE]:** the repair has zero free parameters;
its inputs are statute (`MISO_RPS_COMPLIANCE_REGIONS`, each row cited to its
enabling act) and the model's own zonal CFs and duals; the §2.2 build-share
table is evidence that the bucket is unrepresentative and appears nowhere in the
code. Nothing was sized, tuned or sequenced by any residual, and the
pre-declaration was pushed (`dc0f4b84`) before the solve.
**Rule 19 [R-ONE-MECH]:** one construction of the VRE capacity payment, shared
by the zone chooser and the screen; the siting rule is *replaced*, never stacked.
**Rule 21 [R-DOF]:** no parameter added — nothing enters the DOF ledger.
**Rule 22 [R-HOLDOUT]:** solve years {2021, 2023, 2024, 2025}, 2022 bridged and
never scored, scoring bounded to 2023–2025; the holdout freeze is active,
honored, and asserted by the run's own governance banner; no marker touched;
nothing scored against measured H1-2026.
**Rule 25 [R-ISO-SCOPE]:** the ScenarioConfig default stays `False`; the arming
is MISO's alone through its own `default_scenario_overrides`; every other ISO is
byte-identical (`cache_key(ScenarioConfig())` unchanged at `603c2498bf71d21d`,
asserted as a regression test).
**Rule 27 [R-PUSH]:** every ≥300-line file was edited locally and pushed as
on-disk bytes, with post-push blob verification (git hash-object vs the remote
blob) on `new_entry.py`, `scenarios.py`, `iso_configs.py`,
`run_capacity_hindcast.py`, `mechanism-matrix.js`, `mechanism-matrix/MISO.js`
and the new test — all OK.
**Rule 28 [R-MECH-MATRIX]:** the new solve-affecting field carries its base row
in `mechanism-matrix.js` plus a cell in **all six** shards in this same
PR-chain (MISO `O`/fc `K` with the measured evidence; the other five `U` with
their own named identification source); `scripts/check_mechanism_matrix.py`
passes, and its 237 drifted line anchors were repaired by the shipped
`--fix-anchors`.
**Registration:** the bundle's slim set + evolution ledgers (one-bundle
`.gitignore` carve-out, the D27/D31 precedent), the canonical sidecar, the
hindcast report, `VERDICT_MAP`, the ff-verdicts preserve-then-overwrite and the
board block are committed in this chain; the generated forecast namespace is
left to the Pages deploy. **Verdict edit surface: exactly two keys**
(`miso-t1h`, `miso-t1h-pre-d33`) — the cross-lane STOP condition was checked
against the diff and did not fire; no keeper, no backcast surface, no other
ISO's rows.
**Environment notes disclosed:** the fresh checkout's absent
`data/clean/confirmed-retirements` partition (regenerated per the error's own
instruction, before any solve started — the same note D31 carried); the branch
was rebased on `origin/main` before every push and force-with-lease was used
once, on this lane's own branch, after its earlier commits merged to main.
