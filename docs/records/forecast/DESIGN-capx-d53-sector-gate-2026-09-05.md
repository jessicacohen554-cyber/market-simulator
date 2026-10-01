# DESIGN + PRE-DECLARATION — capx D53: the retirement-screen SECTOR GATE (D32 C5 / R3) — which owners face the merchant screen at all

**Lane:** capx D53 — the structural companion to the fossil-dates channel (D32 C3 → owner
ruling Q30 → capx D44). D32 §4.3 measured on MISO's 2021–2025 record that **88–92 % of the
coal / gas_st / oil MW that actually exited belonged to REGULATED UTILITIES** (EIA-860
Sector 1) — IRP and rate-case decisions filed as EIA-860 Schedule-3 dates — while the model
applies a merchant net-revenue screen to the WHOLE fleet, so the screen fails 77–92 % of a
fleet 97 % of which stayed and the reliability floor masks 96 % of it (D32 §4.4). D49 half 2
then measured that with the dates channel ON the undated cohort STILL fails 73–77 GW at $0
capacity, every MW `entry_capped`. This lane designs, builds default-off and A/Bs the
partition: **which owners face the screen.**
**Branch:** `claude/capx-d53-sector-gate-redt3y` (harness-assigned; the dispatch named
`claude/capx-d53-sector-gate`), FRESH off `origin/main` `d9f034f`.
**Date:** 2026-09-05. **Pushed BEFORE any mechanism code and before any solve.** Graded at
full magnitude in `FINDING-capx-d53-2026-09-05.md`, misses included.
**Model:** Fable (a structural mechanism with arming consequences, rule 27).

**NOTHING ARMS.** One `ScenarioConfig` field lands DEFAULT-OFF (`retirement_sector_gate`,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False` — the bare `miso-t1h` recipe key stays
`eff2c890746ec966`, verified after the field was added, §3); the A/B registers SUFFIXED
(`miso-t1h-d53-sectorgate`); the bare `miso-t1h` verdict key, every keeper / shard verdict /
marker, and the backcast namespace are untouched. The owner arms or declines on the condition
in §6. Rules 1, 5, 6, 12, 13, 14, 19, 21, 22, 24, 25, 27, 28 hold (§8).

---

## 0. Disclosure — what was computed before this text was written (zero solves)

Everything below was read from COMMITTED artifacts only — the D46 bare `miso-t1h` ledgers
(`results/hindcast/miso-2021-2025-realized-t1h-d46/MISO/eff2c890746ec966/evolution_*.json`),
the committed scoring target `data/raw/_validation-source/capacity_actuals_miso.csv`, and the
EIA-860 `vintage_2020` plant table (`data/raw/eia-860/vintage_2020/eia860_plant.parquet`,
columns `Sector` / `Sector Name` / `Regulatory Status`). No LP, no screen, no evolution was
run; the fleet loader was not called. The probe scripts are described in §9.

### 0.1 The attribute

EIA-860 assigns every plant ONE `Sector` (Form EIA-860 Schedule 2, "Sector"): 1 Electric
Utility · 2 IPP Non-CHP · 3 IPP CHP · 4 Commercial Non-CHP · 5 Commercial CHP · 6 Industrial
Non-CHP · 7 Industrial CHP. At the 2020 vintage, the two-value `Regulatory Status` flag
(`RE` regulated / `NR` non-regulated) is a near-perfect partition of the same set: **3,587 /
3,587 sector-1 plants are `RE`; 0 sector-1 plants are `NR`**; the only `RE` plants outside
sector 1 are 16 commercial / industrial self-generators (sectors 4/5/7). The two attributes
carry the same information on the population this lane partitions, so the gate consults ONE
(§1.4).

### 0.2 The MISO fleet by sector (EIA-860 2020 vintage, BA = MISO, operable, nameplate MW)

| fuel | sector 1 | 2 | 3 | 4 | 5 | 6 | 7 | sector-1 share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| coal | 52,022 | 6,284 | 893 | 0 | 4 | 0 | 952 | **0.865** |
| gas_cc | 23,628 | 3,187 | 3,608 | 0 | 43 | 0 | 4,122 | 0.683 |
| gas_ct | 22,116 | 3,416 | 573 | 3 | 158 | 48 | 2,349 | 0.772 |
| gas_st | 14,033 | 853 | 30 | 0 | 321 | 6 | 707 | **0.880** |
| nuclear | 9,845 | 3,236 | 0 | 0 | 0 | 0 | 0 | 0.753 |
| oil | 3,928 | 28 | 1 | 2 | 10 | 7 | 82 | **0.968** |
| **total** | **125,552** | 17,004 | 5,105 | 5 | 536 | 61 | 8,212 | **0.802** |

Sector 1 is **80 % of MISO's operable thermal nameplate**. The merchant IPP fleet (sector 2)
is 11 %; the three CHP sectors together 9 %.

### 0.3 What the bare recipe's screen fails, by sector (D46, key `eff2c890746ec966`)

Every failing unit in D46 is `entry_capped` (the admission floor admits ZERO in every screen
year — D44 §0: "zero economic exits in every year"); dated plants are already exempt (D42
reconciliation (a)), so these rows ARE the undated failing pool D49 §2.3 counted.

| screen year | failing units / GW | sector 1 | 2 | 3 | 4 | 5 | 6 | 7 | no sector (planned-addition ids) | sector-1 share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 (bridge) | 1,497 / **76.75** | **58.94** | 6.66 | 4.32 | 0.005 | 0.49 | 0.06 | 5.91 | 0.37 (8 units) | **76.8 %** |
| 2023 | 948 / **74.22** | **56.87** | 6.64 | 4.32 | 0.003 | 0.48 | 0.05 | 5.87 | 0 | 76.6 % |
| 2024 / 2025 | 0 / 0 | — | | | | | | | | (the capacity term clears every unit, D49 §2.3) |

By fuel at the 2022 bridge (MW): coal 18,972 sector-1 / 1,161 other · gas_cc 16,265 / 9,052 ·
gas_ct 16,741 / 5,479 (+374 unknown) · gas_st 3,895 / 1,628 · oil 3,067 / 116. The screen fails
the fleet's sectors in the fleet's own proportions (77 % vs 80 % of nameplate): it is blind to
who owns the unit, which is exactly D32's finding. The non-utility residual is **17.4 GW**
(2022) / 17.4 GW (2023): IPP non-CHP 6.7, IPP CHP 4.3, industrial CHP 5.9, commercial CHP 0.5,
commercial / industrial non-CHP 0.06.

### 0.4 The real cohort by sector (committed target, thermal, 2021–2025)

| fuel | exited MW | sector-1 share | D32 §4.3 read |
|---|---:|---:|---:|
| coal | 12,434 | **0.88** | 0.88 |
| gas_cc | 858 | 0.07 | 0.09 |
| gas_ct | 399 | 0.87 | 0.46 (a different join; 0.4 GW either way, immaterial) |
| gas_st | 2,127 | **0.90** | 0.90 |
| oil | 543 | **0.92** | 0.92 |
| nuclear | 812 | 0.00 (Palisades, sector 2) | — |
| biomass | 196 | 0.02 | 0.02 |

**The undated cohort** (real exits at plants with NO live row in the 48-plant
`announced_fossil_schedule` the D46 run carried — D49 §2.4's 3.465 GW fossil + 0.812 nuclear
+ 0.196 biomass = 4.473 GW): fossil **sector 1 = 1.576 GW (45 %)**, sector 2 = 1.030, sector 3
= 0.170, sector 7 = 0.632, sectors 4/5/6 = 0.057. Of D49's **2.785 GW reachable at plant+fuel
grain**, the sector-1 half is South Oak Creek (598.4, WEC), Teche (348.5, Cleco Power), Weston
(157.9, WPS), Houma (78.9, Entergy LA) ≈ **1.18 GW**; the non-utility half is Big Cajun 2
(657.9, Cleco Cajun — an unregulated affiliate, sector 2), LaO Energy Systems (464.5, sector
7), Grand Tower (336.8, sector 2), Warrick (166.6, sector 3), Indiana Harbor West (57.0,
sector 7) ≈ **1.68 GW**. Taconite Harbor (168.0, sector 1) is absent from the model fleet.

### 0.5 The cache keys (resolved through `run_capacity_hindcast.build_config` → `apply_iso_scenario_defaults` → `cache_key()` with the field added locally; name and default fixed by this text)

| config | key | check |
|---|---|---|
| bare `miso-t1h` recipe (gate OFF) | **`eff2c890746ec966`** | = D46 — the known-answer check on the registration |
| bare + `retirement_sector_gate=True` (the A/B arm) | **`c306ddc6d28c60c2`** | no collision under `results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/` |
| bare + `adequacy_accounting_ratio_dated_net=True` | `b538d37b36a88247` | = D51 — second known-answer check |
| bare + both gates (the §5 rider) | **`6ea92547eaa62559`** | no collision |
| `ScenarioConfig()` / bare backcast | `4c6b03ae098b6e3e` / `8211c72bb1960adc` | unmoved (the field drops at its declared `False`; coerced to default in a backcast) |

---

## 1. The design — the partition, and every interaction D32 R3 names

### 1.1 What the screen models, and for whom that is the decision

Step 3 (`apply_economic_retirements`, spec §5.2) asks one question of every thermal unit:
*does the attainable merchant margin — energy + reserve + capacity + attribute revenue on the
screen's own price signal — cover going-forward FOM?* That is the decision a **merchant
owner** faces: no rate base, no IRP, exit when the market stops paying. A **regulated
utility** (sector 1: IOU, muni, co-op, federal) faces a different decision — the unit's FOM is
recovered in rates whether or not the energy market pays it, and its exit is an integrated
resource plan / rate-case / securitization outcome that reaches the public record as an
EIA-860 Schedule-3 planned date (D32 §4.1, §4.3). The model already carries that channel
(step 1b, `fossil_announced_exits_enabled`, default ON since Q30/D44). What it does NOT yet do
is stop applying the merchant question to the 80 % of the fleet whose owners never ask it.

### 1.2 The partition (one published boolean)

| EIA-860 `Sector` of the unit's PLANT | who decides the exit | exit channels under the gate | why |
|---|---|---|---|
| **1 Electric Utility** | the owner's IRP / regulator | **step 0** (instrument-bound confirmed exits: RTO deactivation acceptance, consent decree, statute, regulatory order, RMR end) and **step 1 / 1b** (the owner-filed EIA-860 date, vintage-gated, reversal registry armed; non-fossil dates via the horizon gate). **Never the economic screen.** | The filed date IS the decision (D32 §4.3: 69 % recall / 87 % within ±1 yr of dated MW); a merchant-margin test on a rate-based unit models a decision the owner does not face. |
| **2 IPP Non-CHP** | the merchant owner | the economic screen, as today (plus steps 0/1 where a row exists — the D42 reconciliation) | The screen's own object. Utility-owned MERCHANT AFFILIATES are filed under the affiliate's own utility ID and sectored 2 — Cleco Cajun's Big Cajun 2, Entergy's ex-EWC merchant units, Vistra's ex-Dynegy Illinois fleet — so the gate already routes them to the screen (§1.4). |
| **3 IPP CHP** | the merchant cogen owner (steam co-product) | the economic screen, as today | An independent power producer whose primary business is selling power (Midland Cogeneration Venture, Carville, Whiting Clean Energy, Dearborn, LSP-Whitewater); steam revenue is a co-product the screen does not price — see §1.5. |
| **4 / 6 Commercial / Industrial Non-CHP** | the host | the economic screen, as today | 66 MW of the MISO fleet; self-generation with a grid-sales margin. Immaterial; kept in the screen so the partition stays ONE boolean. |
| **5 / 7 Commercial / Industrial CHP** | the host's process | the economic screen, as today (§1.5 decides and names the successor) | |
| plant absent from the vintage plant table (a `planned_*` addition's new plant code, a synthesized unit, `plant_code == 0`) | unknown | **fails OPEN to the screen** (today's behaviour), counted in the ledger as `unknown_sector` | A gate that cannot read the attribute must not invent one; the 8 such units at the 2022 bridge are 374 MW of planned gas_ct. |

**The rule is `Sector == 1` → exempt from the screen; everything else → the screen.** No
weight, no threshold, no share, no fitted value (rule 21 `[R-DOF]`): a partition on one
published per-plant attribute.

### 1.3 Rule 13 `[R-MEASURED]` — the forward test

*Could this quantity be produced for a forward year from forward drivers, and would it respond
to changed conditions?* `Sector` is published for every plant in every EIA-860 vintage
(annual), read at the run's ACTIVE vintage (`config.paths.active_eia860_dir` — the 2020
snapshot in a T1-H hindcast, the canonical 2025ER in a forecast), and it moves when ownership
moves: a sale from a utility to an IPP re-sectors the plant in the next vintage (Coal Creek →
Rainbow Energy, 2022; Merom → Hallador, 2022 — both sector 1 → 2 in later vintages). It is an
OWNER ATTRIBUTE, never an outcome: nothing about whether the plant exited enters it. The
information gate is the vintage's: in a 2020-vintage hindcast Coal Creek stays sector 1
through the window because the sale is post-vintage — the same construction step 0 applies to
`instrument_date` and step 1b to the filed date.

### 1.4 `Regulatory Status` (RE / NR) and utility-owned merchant affiliates — the rule stated

The gate keys on `Sector` ALONE and does NOT consult `Regulatory Status`. Reason (rule 19
`[R-ONE-MECH]`): on the population the gate partitions the two attributes are the same
information (§0.1: 3,587 / 3,587 sector-1 plants are `RE`, 0 are `NR`), so a second key would
be a second mechanism for one phenomenon with nothing to add; and `Sector` is the attribute
that carries the CHP distinction the successor in §1.5 needs, while `Regulatory Status` is not.
A utility-owned merchant affiliate is, in the EIA-860 filing, a separate utility ID with its
own sector: Cleco Cajun LLC (Big Cajun 2) is sector 2 / `NR` although its parent Cleco Power is
sector 1 / `RE`; the gate therefore screens Big Cajun 2 and exempts Teche — which is the right
reading of both plants' actual decision processes (Big Cajun 2's 2025 exit was Cleco Cajun's
merchant decision; Teche's was Cleco Power's IRP). The 16 `RE` plants in sectors 4/5/7 (rate-
regulated self-generators) stay IN the screen because their sector says self-generator; the
finding reports whether any of them fails, so the disagreement is measured rather than
assumed away. The vintage's `Sector` × `Regulatory Status` crosstab for the ISO's fleet is
logged once per run by the loader so a future vintage that breaks the equivalence is visible.

### 1.5 CHP sectors (3 / 5 / 7) — decided: they STAY in the screen this lane; the host screen is the named successor

Structurally, a CHP unit's exit is its steam host's process decision (plant closure, boiler
replacement), and its grid-sales margin is not the whole decision either. Three reasons the
gate nonetheless leaves sectors 3/5/7 in the screen:

1. **One partition, one boolean.** The charter's object (D32 C5, ledger D53) is the
   utility / merchant split; folding a second partition (CHP host vs merchant) into the same
   field would give one gate two rationales and two evidence bases, which is what rule 19
   forbids.
2. **The model already represents the host on the DISPATCH side** — CHP tranches carry
   steam-following floors (`must_run_pct`, `chp_grid_pmin_mw`, the measured
   `CHP_BTM_PCT_BY_SECTOR` shares), so their screen margin is an artefact of a unit that is
   dispatched by its host, not by price. The right fix for that margin is a going-forward
   representation of the host's steam economics (a revenue-side term or a host-exit input), a
   different mechanism from an ownership partition.
3. **The evidence points the other way for CHP.** CHP-sector plants DO exit in the window
   WITHOUT a filed date — LaO (464.5), Warrick (166.6), Indiana Harbor West (57.0): **0.69 GW,
   25 % of D49's reachable undated cohort**. Exempting them would move a quarter of the
   screen's only reachable real exits into "unreachable without a date"; exempting sector 1
   moves 1.18 GW whose real channel (the filed date) already exists and merely lacks a
   2020-vintage row.

Named, not built: **the CHP-host screen** — sectors 3/5/7 partitioned on host status, with
the exit input the host's own published closure record — is a successor lane with its own
census (the 10.7 GW of CHP-sector MW that fails the merchant bar today, §0.3: Midland Cogen
1,479, Plaquemine 793, Taft 739, Carville 521, Whiting 513, Sabine River Works 502 … — 61 % of
the post-gate failing pool).

### 1.6 Confirmed exits (step 0) — unchanged

Instrument-bound rows apply to any sector, before the screen, bypassing the floor, exactly as
today. A sector-1 plant with a confirmed row exits on its instrument; a sector-2 plant with a
confirmed row exits on its instrument AND is never screened while a row is pending (the
existing D42 exemption). The gate adds nothing to step 0 and removes nothing.

### 1.7 RPS-credited and clean units

The screen's candidate set is the `_THERMAL_FOM` fuels — coal, gas_cc, gas_ct, gas_st,
gas_cc_ccs, oil, **nuclear**. Wind, solar, hydro, biomass and geothermal are never screened
(no FOM entry), so the RPS dual / EAC credit they earn is untouched by the gate. Nuclear IS
screened, and the gate applies to it by the same rule: utility nuclear (sector 1 — Callaway,
Arkansas Nuclear One, Grand Gulf via System Energy Resources, Prairie Island, Monticello …)
leaves the screen and exits only on a filed date (the non-fossil step-1 horizon gate,
unchanged); MERCHANT nuclear (sector 2 — Palisades, and in PJM / NYISO the Constellation /
Vistra fleets) stays screened, with the EAC / ZEC / §45U revenue terms applying there. That is
where those programs exist in reality (Illinois, New York, New Jersey ZECs are merchant-
nuclear instruments), so the partition puts the attribute revenue on the units whose exit it
was designed to prevent. A `gas_cc_ccs` retrofit carries its host's sector.

### 1.8 The dates channel — the rule-19 reconciliation, stated not stacked

Two declarations now say "exogenous to the screen": the dated-plant exemption (D42 (a),
`dated_plant_unit_ids`) and the sector-1 exemption (this lane, `sector_gated_unit_ids`).
Both enter the screen through the SAME seam, `exempt_unit_ids`, as a set UNION. Neither
declaration produces an exit — exits come only from steps 0 / 1 / 1b or from the screen — so
nothing is decided twice:

| unit | dated? | sector | screen? | exit route |
|---|---|---|---|---|
| a | yes | 1 | no (both declarations) | the filed date, step 1b |
| b | yes | 2 | no (D42) | the filed date, step 1b |
| c | no | 1 | **no (D53)** | none until a later vintage files a date (`hindcast_verified_announced_exits`) or an instrument appears (step 0) — **the stated, accepted consequence**: 1.18 GW of D49's reachable cohort becomes unreachable by the screen (§0.4), because its owners' real channel exists and lacks a 2020-vintage row; that is a limit of the information set, not of the mechanism |
| d | no | 2–7 | **yes** | the screen (decided → lag → executed, floor-capped as today) |

A gated unit is never in `margins`, so it is never `decided`, `entry_capped`, `re_confirmed`,
`reversed` or pipelined, and the pipeline state cannot hold one (the state starts empty and is
only ever fed from `margins`) — asserted by test. The R-NEW admission cap's counterfactual
(D42 (b)) nets the DATED rows exactly as today; a gated undated unit is simply part of the
fleet the cap counts. The realized-year execution floor (D42 (c)) tests the post-step-1 fleet
unchanged. The reserve-margin backstop (BLK-10) and the CCS retrofit screen (step 2) are
untouched.

> **CROSS-REFERENCE, 2026-09-06 (capx D58 → owner ruling Q53 → capx D78) — the "same seam, set
> union" construction above was CORRECT FOR MISO AND WRONG IN GENERAL, and it is no longer how
> the gate enters the screen.** `FINDING-capx-d58-2026-09-06.md` §3 proved at the line that on
> an ISO with the D57 capacity-supply clearing armed (PJM alone at that date) the
> `exempt_unit_ids` union did a second job this section never claimed: a gated unit never
> entered `margins`, so it never entered the sell-offer stack, so its accredited MW fell into
> the $0 price-taking block — 34,172.4 MW moved, `n_offers` 1,370 → 1,000, PJM's 2022 clearing
> price 67.76 → 61.21 $/MW-day (−9.67 %), and 41 merchant rows / 2,910.2 MW failed that the
> control passed, inverting this design's own §3 P5 sign line (economic exits ROSE). The owner
> ruled (Q53, reading 1) that a sector-1 unit MUST STILL OFFER at its cost-based net-ACR price
> — PJM's must-offer requirement (Manual 18 Rev 62 §1.2 / §5.4.1 / §5.4.7) keys on
> existing-and-in-footprint, never on ownership — and that only its exit is exempt. Since capx
> D78 (`DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` §3) the gated set enters
> `apply_economic_retirements` on its OWN parameter, `exit_exempt_unit_ids`: evaluated,
> offered and settled like any screened unit, then partitioned out of `margins` after the
> clearing and before either decision rule. **The table above and the sentence "a gated unit
> is never in `margins`" describe the exit decision only**: a gated unit is now in `margins`
> for evaluation and offering and leaves it before anything that decides an exit reads it, so
> every EXIT-side claim here (never decided / capped / re-confirmed / reversed / pipelined; the
> cap, the floor, the backstop untouched) is unchanged and re-asserted by test, and on MISO —
> where the clearing is off — the two constructions are byte-identical. The dated-plant
> exemption (row a/b) keeps its D54 §4.2 price-taker reading and is routed, not moved (D78
> design §4). This note corrects the record by reference; the text above is preserved as the
> design D53 measured on MISO.

### 1.9 The additions-screen mirror — NAMED, not built

Utility builds are IRP-driven too: a regulated utility adds a CC or a solar farm because its
plan says so, not because the merchant new-entry screen's `expected_revenue > LCOE` clears —
and the model already carries that channel's data half (`load_planned_additions`, the
EIA-860 proposed-generator pipeline, step 4). D31 §7's additions under-build (the D39 object)
probably has the same asymmetry in it: the economic-entry screen (step 5) evaluates merchant
economics for a market whose builders are 80 % utilities. The mirror — the step-5 screen
sized to the merchant share of the build market, with the utility share carried by the
step-4 pipeline at its filed vintage — is a separate design with its own census and its own
A/B, and it is the lane this design points the director at once D53 lands. Not one line of it
is built here.

### 1.10 Where the sector enters (rule 6 `[R-SOA]`, never a hardcoded dict)

The per-unit sector is resolved from the run's active EIA-860 plant table
(`data/fleet/eia860.py::eia860_plant_sectors`, a directory-keyed cached reader beside
`eia860_plant_states` — the existing `_eia860_plant_sector` reader is `lru_cache(maxsize=1)`
with no directory key, so it would serve the first-loaded vintage across a switch; it is left
untouched for its own consumer, `data/coal.py`) keyed on the `plant_code` every `Generator`
already carries from the fleet assembly (both the CAMPD-bin and the legacy per-unit paths),
and joined at the evolve seam by `retirements.sector_gated_unit_ids(fleet, sectors)` — the
twin of `dated_plant_unit_ids`. No plant → sector dict lives in the model; no `Generator`
field is added (the sector is a PLANT attribute, and `plant_code` is already the key the
dated-exemption seam uses — one join, one grain). The LP never sees it (rule 6 is about the
matrix builder; step 3 is the object layer before it).

### 1.11 What the ledger records

Per evolution year under the gate, `evolution_<year>.json` gains one small block,
`sector_gated`: `{units, mw, mw_by_fuel, mw_by_sector, unknown_sector_units,
unknown_sector_mw}` — the whole gated set (every sector-1 thermal unit in the year's fleet,
failing or not), so the D-2 mechanism attribution can read what left the screen without the
per-unit rows (derivable from the fleet + the vintage table). OFF the gate the block is absent
and every ledger is byte-identical.

---

## 2. Expected consequence from the census (zero solves) — the mechanism argued, then the numbers

### 2.1 Why the gate cannot move an EXIT on the bare recipe

The admission cap (`_apply_pipeline_retirements` → `_apply_reliability_floor` on the cap-
horizon counterfactual) retains candidates cheapest-firm-first until the post-pipeline
accredited fleet clears the requirement, and admits whatever is left. Its ceiling — the whole
cap-horizon fleet with NOTHING removed — is the same in both arms: a gated unit is not a
candidate, so it is in the fleet the cap counts either way. D46 admitted ZERO at every screen
(2022, 2023: 1,497 / 948 rows, all `entry_capped`; 2024, 2025: no unit fails), i.e. the ceiling
itself is below the horizon requirement (the pending dated exits netted, the peak grown to
the coal-lag horizon). A smaller candidate pool under the same short ceiling admits the same
zero. **Therefore on the bare recipe the retirement rows are byte-identical between the
arms, by construction** — and that is the honest first result, not a disappointment: the
gate's measurable effect on this recipe is on the CENSUS of what the screen fails and the
floor masks, and its composition effect is observable only where headroom exists, which is
what the §5 rider measures.

### 2.2 The numbers

| quantity | bare (D46) | gate ON, expected |
|---|---:|---:|
| 2022 bridge: failing units / GW (`pipeline_events`, all `entry_capped`) | 1,497 / 76.75 | **~400 / 17.4–18.5** (the non-utility 17.4 + up to 0.37 unknown-sector fail-open) |
| 2023: failing units / GW | 948 / 74.22 | **~350 / 17.0–18.0** |
| 2024 / 2025 failing | 0 / 0 | 0 / 0 |
| share of the model's thermal fleet the screen FAILS at the 2022 bridge | 77 % (76.75 / ~143.4 GW) | **~12 %** |
| floor masking share OF THE SCREEN'S POOL (`entry_capped` ÷ failing) | 100 % | 100 % — the headroom is zero either way; what changes is the pool it masks, ÷ 4.3 |
| `sector_gated` 2022: units / GW | — | ~1,100 / **105–120** (the fleet's sector-1 thermal MW; 125.6 GW at the spine scaled by the model's 92 % fleet coverage) — of which the failing subset **58.9 (57–61)**, by fuel coal 18.97 / gas_cc 16.27 / gas_ct 16.74 / gas_st 3.90 / oil 3.07 |
| economic exits, every year | 0 | **0** |
| `retirements` per year (all `announced`) | 2.877 / 2.178 / 0.752 / 0.153 GW | **identical to the decimal** |
| `capacity_reserve_position` 2023 / 24 / 25 | 1.032186 / 0.976427 / 0.948813 | **identical** |
| BLK-10 backstop 2025 | 2,414.8 MW gas_ct | **identical** |
| real-exit share of the failing pool (D49's reachable cohort's model MW at real-exit plants ÷ failing MW) | 3,371 / 76,751 = 4.4 % | **~1,790 / 17,800 ≈ 10 %** (Big Cajun 2 799, LaO 384, Warrick 343, Grand Tower 264) |
| of D49's reachable 2.785 GW: reachable by the screen at all | 2.785 | **1.60** (sector 1's 1.18 GW leaves — §1.8 row c) |

---

## 3. The pre-declaration (primary A/B: bare `miso-t1h` + `retirement_sector_gate=True` → `miso-t1h-d53-sectorgate`, key `c306ddc6d28c60c2`)

**P1 — exits byte-identical.** Every `retirements` row, every `pipeline_events` `decided` /
`executed` / `re_confirmed` / `reversed` row (there are none in D46), `floor_retained` (0),
`announced_derates`, and every FC-3 retirement row: `retire.total_gw` **9.799 (−43.6 %,
FAIL)**, coal 7.877, gas_st 0.849 / oil 0.154 / gas_ct 0.132 / gas_cc 0.002 / nuclear 0.768 /
biomass 0.016, `retire.unit_recall_gt300` **16/19 PASS**, `false_retire` **0.0 PASS**, LOYO
recall 8/16 / 14/15 / 15/18 — **identical to the decimal.** Falsifier: any economic exit, any
`decided` row, or any retirement row moving by ≥ 0.001 GW.

**P2 — the census moves exactly as the partition says.** 2022 `pipeline_events` MW **17.0–
18.5 GW** (1,497 rows → 350–450), 2023 **17.0–18.0 GW**; the gated block's failing subset
**57–61 GW** in 2022 with coal 18–20 / gas_cc 15.5–17 / gas_ct 16–17.5 / gas_st 3.5–4.3 / oil
2.9–3.2 GW. Zero `pipeline_events` rows at a sector-1 plant. Falsifier: any sector-1 unit
carrying a pipeline row; the failing pool outside 15–20 GW.

**P3 — everything outside the screen's candidate set is byte-identical**: the three ledger
positions and requirements, every `add.*` FC-3 row (gas_ct 4.415 / gas_cc 4.146 / wind 8.0 /
solar 4.946 / storage 4.0; the shares), the BLK-10 backstop (2,414.8 MW gas_ct, 2025), the
CCS-retrofit and entry-screen diagnostics, both `screen_signal_diag_*.npz` (the same LP, so
the same duals), `fleet_by_fuel_before/after` every year. Determination **HOLD** both, FC-7
CAVEAT both. Falsifier: any of these moving — that would be a SECOND seam the gate touches,
and §6 says HOLD-and-route on it.

**P4 — cost.** 20–30 min wall, ≤ 10.5 GB, solve years {2021, 2023, 2024, 2025}, 2022 bridged,
`SOLVE-YEAR PARITY` held; run solo (rule 12, a ~10 GB MISO year).

**P5 — the rule-14 sign line, stated before the solve.** On this recipe `retire.total_gw` does
not move in either direction, so no band reading can be quoted for or against the gate. If it
DID move it could only move DOWN (fewer candidates, same headroom) — and a worse
`retire.total_gw` under the gate would be the expected signature of a screen that had been
retiring utility units for a reason their owners never faced, not evidence against the
partition. Composition and `false_retire` are where the gate can improve; the bare recipe
cannot show that, the rider can.

## 4. What the primary A/B can and cannot adjudicate — said now

It CAN adjudicate: whether the field is a pure candidate-set partition (P1 + P3), whether the
partition the code applies is the one the vintage table says (P2), and what the floor is
actually masking once the fiction is removed (the failing pool's size and its real-exit
share). It CANNOT adjudicate composition, precision or recall, because the floor's headroom on
this recipe is zero. A lane that only ran the primary and then argued the gate "does nothing"
would be reading a zero-headroom regime as a verdict on a partition — the same mistake D32
§4.4 named for the retention key. Hence the rider.

## 5. The rider — the composition-observability leg (gate ON + D51's ratio ON → `miso-t1h-d53-sectorgate-d51ratio`, key `6ea92547eaa62559`, comparator `miso-t1h-d51-ratio`, `b538d37b36a88247`)

D51 measured the ONE configuration in the committed record where the admission cap has
headroom: with the accounting ratio re-identified net of the dated exits, the 2022 bridge
admits **477.4 MW of coal** — the last-retained tranches in the float-noise order (D32 §3.2,
D55's object), at **1.1 % plant-grain precision** (D51 §0). Under the gate, the coal that can
fill that headroom is the NON-UTILITY coal pool: Big Cajun 2 (799 model MW, sector 2, real
exit 657.9 MW in 2025), Warrick (343, sector 3, real exit 166.6 MW in 2025), and ~19 MW of
sector-3/7 residue — 1,161 MW in all, of which 1,142 MW (98 %) sits at plants that really
exited. The rider is a MEASUREMENT of the gate in a headroom regime, run on D51's default-off
field (not armed; neither field arms; the rider registers suffixed and moves no gate row).

**P6 — the admitted MW comes from the non-utility pool, at plant-grain precision that D51's
did not have.** 2022 admits **0.3–0.7 GW nameplate of coal** (the headroom is the position's,
not the pool's, so within ±0.25 GW of D51's 477.4 — the exact figure moves with the admitted
units' EFORd-accredited firm value), **every admitted / decided / executed unit at a non-
sector-1 plant**, drawn from {Big Cajun 2, Warrick} in the retention order; plant-grain
precision of the NEWLY admitted MW **≥ 90 %** (D51: 1.1 %); precision of ALL released MW
**≥ 97 %** (D51: fell from 98.5 %). Executed 2024 (coal lag 3 from loss year 2021 — one year
early against both plants' real 2025 exits, the D42 timing grain). Falsifier: any sector-1
unit in a `decided` / `entry_capped` / `executed` row; admitted 0 (the headroom closed by a
seam the gate should not touch); admitted > 1.2 GW (more than the pool's whole non-utility
coal).

**P7 — the totals.** `retire.total_gw` **10.0–10.5** (D51 10.276; the same headroom filled
from a different pool); `false_retire` **0.0**; `retire.unit_recall_gt300` **16/19 or 17/19**
(17 if Big Cajun 2 — 657.9 MW real, > 300 — is admitted and the ±1-yr timing window admits
its 2024 execution against a 2025 exit; Warrick is < 300 MW and cannot move the count); LOYO
recall ≥ 2/3 in every fold; the D51 positions **1.0777 / 1.0194 / 0.9875** within ±0.003
(the 2025 position moves with which coal executed in 2024); `add.*` rows identical to D51's
(`add.by_tech.gas_ct` 1.472, backstop 0). Falsifier: `retire.total_gw` outside 9.8–10.8; any
non-coal economic exit; recall < 16/19.

**P8 — cost.** 20–30 min, solved AFTER the primary, never concurrently (rule 12).

## 6. Arming recommendation — the pre-stated condition (a P9-style flip condition)

Recommend **ARM** (`retirement_sector_gate=True` as the ScenarioConfig default — the gate is
ISO-agnostic by construction and carries no ISO's numbers, the same posture class as Q30;
alternatively MISO-only via `default_scenario_overrides` if the owner prefers to wait for the
PJM leg) iff ALL of:

- **(a) purity** — P1 and P3 hold: on the bare recipe every retirement row and every non-
  screen row is identical to the decimal (the field is a candidate-set partition and touches
  no second seam);
- **(b) fidelity of the partition** — P2 holds: the gated failing MW at the 2022 bridge is
  within ±5 % of the census's 58.9 GW and NO sector-1 unit carries a pipeline row;
- **(c) composition where it can be seen** — on the rider, every economic decision is at a
  non-sector-1 plant AND the plant-grain precision of the newly admitted MW is ≥ D51's 1.1 %
  (the gate must not make the floor's pick WORSE than random; the pre-declared expectation is
  ≥ 90 %);
- **(d) LOYO** — `retire.unit_recall_gt300` LOYO holds ≥ 2/3 on both legs.

**`retire.total_gw`'s band reading is explicitly NOT a condition in either direction**
(rule 14 — §3 P5). Recommend **HOLD-and-route** if (a) fails (a second seam moved: the gate is
not what this design says it is). Recommend **DECLINE** if (b) fails (the code's partition is
not the vintage's) or (c) fails (the partition worsens composition). The recommendation is
STRUCTURAL (rule 1 `[R-STRUCT]`): the bare recipe's FC-3 cannot distinguish the arms, and the
lane will not pretend otherwise; what arming buys is that the screen stops failing 59 GW of
rate-based capacity it has no standing to screen, so that the moment headroom exists (D51
showed it opening; the additions lane will open it further) the floor's release is drawn from
the merchant pool that actually faces the decision, at ~10 % real-exit density instead of
~4 %. NOTHING ARMS HERE — the default is the owner's.

## 7. Successors named

1. **PJM leg** (once D48 lands, DATA PROFILE widened to pjm): D45 L1 measured PJM's 2022
   screen failing **111.7 GW of fossil candidates** — the same shape. PJM's EIA-860 sector mix
   is the inverse of MISO's (merchant-heavy: the ex-Exelon / Vistra / Talen / LS Power
   fleets are sector 2), so the PJM census is the discriminating test of the partition — a
   gate that removes a MINORITY of PJM's failing pool while removing 77 % of MISO's is
   behaving as an ownership attribute should. Run as `pjm-t1h-d53-sectorgate` against the
   bare `pjm-t1h` on D48's basis, its own census pre-declared, its own cell (rule 25).
2. **The additions-screen mirror** (§1.9) — the step-5 merchant-entry screen sized to the
   merchant share of the build market, the utility share carried by the step-4 filed
   pipeline. Own design doc.
3. **The CHP-host screen** (§1.5) — sectors 3/5/7 on the host's own closure record.
4. **D55's float-noise fix** re-orders WITHIN the post-gate coal pool; the two lanes compose
   (D55 edits `_floor_retention_merit`, this lane edits only the candidate set — disjoint
   seams in the same file, rebased before every push).

## 8. Governance attestation (as pre-declared; re-attested in the finding)

- **Rule 1:** the partition is a market-structure fact (who faces a merchant exit decision),
  argued from the owner's decision process (§1.1) and measured on the cohort (§0.4) — not
  from the residual; the bare A/B is pre-declared to leave the residual UNMOVED.
- **Rule 5 / 24:** one gated field, in `ScenarioConfig` and `run_config.json`, harness flag
  `--retirement-sector-gate`, `TIER_TAGS` 1; no literal, no env knob, no per-plant dict.
- **Rule 6 / 13:** the attribute enters through the EIA-860 plant table at the active vintage
  (§1.3, §1.10); forward-regenerating, owner-side, never an outcome.
- **Rule 12:** MISO solo; the rider solved after the primary, never concurrently; no PJM solve.
- **Rule 14:** the sign line is stated (§3 P5) before the solve; a worse band under the gate is
  the expected signature, not a reason to revert.
- **Rule 19:** one exit decision per unit — the gate and the dates channel union at the same
  `exempt_unit_ids` seam and neither produces an exit (§1.8); no floor, no stacked mechanism.
- **Rule 21:** a partition, no weight — no value was, or can be, identified against a residual.
- **Rule 22:** solve years {2021, 2023, 2024, 2025}, 2022 bridged and never scored, scoring
  and LOYO bounded to 2023–2025, the holdout freeze untouched, nothing against H1-2026.
- **Rule 25:** the field carries no ISO's numbers; MISO alone gets a measured verdict; the
  other five shards receive `U` (a transfer candidate, untested), never a letter from MISO.
- **Rule 27:** every ≥300-line file edited locally (`scenarios.py`, `retirements.py`,
  `evolve.py`, `eia860.py`, `run_capacity_hindcast.py`, `register_forecast_run.py`, the
  matrix base and shards, `ff-verdicts.json`, `.gitignore`) and blob-verified after each push.
- **Rule 28:** matrix base row `retirement_sector_gate` + a cell in ALL SIX shards in the
  build commit; MISO's `economic_retirement_screen` cell gains the D53 evidence in the finding
  commit; CI's `check_mechanism_matrix.py --base` gate run locally before the push.
- **No keeper, no shard verdict letter beyond the new row's own cells, no marker, no backcast
  file, no default flip, no parameter value.**
- **Collision:** D51 landed (its constant and field are consumed by the rider, unchanged);
  D55 edits `_floor_retention_merit`; this lane adds `sector_gated_unit_ids` beside
  `dated_plant_unit_ids` and touches nothing else in `retirements.py`; D48 owns PJM.

## 9. Kills

- K-a: any cache-key collision, or a realized key ≠ its §0.5 value unexplained from the
  resolved config → STOP for that leg.
- K-b: P1 fails on the bare recipe (an economic exit appears or vanishes) → the A/B is still
  registered and graded, but the recommendation is HOLD-and-route by §6(a), whatever the
  band reads.
- K-c: any sector-1 unit in a pipeline row on either leg → DECLINE by §6(b), and the
  loader's join is the first suspect, reported.
- K-d: rules 13/14/21 — no operand of the gate is a model outcome or a residual; the cohort
  (§0.4) is used to MEASURE the partition's consequence, never to identify anything.
- K-e: the preserved baselines (`miso-t1h` / D46, `miso-t1h-d51-ratio`, every `*-pre-*` and
  `*-d42-*`) are never written; both legs take fresh out-dirs.

## 10. Reproduction of §0 (scratch probes, not committed)

- **Sector census of the failing pool:** `evolution_{2022,2023}.json` `pipeline_events` →
  plant code from `_p<id>_` (binned tranches) or the `<plant>_<gen>` prefix (legacy ids;
  `planned_*` ids carry none) → `vintage_2020/eia860_plant.parquet` `Sector` /
  `Regulatory Status` → MW by sector × fuel.
- **Fleet by sector:** `vintage_2020/eia860_generators.parquet`, `balancing_authority_code ==
  "MISO"`, `status == "OP"`, fuel by `data.fleet.eia860._map_fuel_type`, joined to the plant
  table's `Sector`.
- **Cohort by sector:** `capacity_actuals_miso.csv` `kind == "retirement"` thermal rows
  joined on `plant_id`; "dated" = plant in the D46 `evolution_2021.json`
  `announced_fossil_schedule` with `disposition ∉ {cancelled, reversed}` (48 plants).
- **Keys:** `run_capacity_hindcast.build_config(iso="MISO", start_year=2021, end_year=2025,
  variant="realized", vintage=2020, entry_screen_diagnostics=True)` →
  `iso_configs.apply_iso_scenario_defaults(·, "MISO")` → set the gate(s) → `cache_key()`.
