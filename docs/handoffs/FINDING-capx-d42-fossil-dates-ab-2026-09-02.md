# FINDING — capx D42: the fossil announced-date posture A/B (D32 R1) — honoring the owner's filed EIA-860 retirement date as an exogenous step-1 input takes MISO's T1-H recall from 5/19 to 16/19, opens every non-coal exit class the floor held at zero, retires nothing the screen would have (zero economic exits in every year), and leaves the residual exactly where the data says it is: the undated cohort and the December-dated 2026 roll; the deferral class is countered per unit by published re-filings, every EIA-860 one of them on file before its vintage date's effective year

**Lane:** capx D42 — owner ruling Q29 on D32's R1
(`FINDING-capx-d32-floor-retention-2026-09-02.md` §7). A MEASUREMENT lane:
the gate `ScenarioConfig.fossil_announced_exits_enabled` ships DEFAULT-OFF,
every leg is registered SUFFIXED, the bare `miso-t1h` verdict key is
untouched, no keeper / board / marker moves. **Nothing arms. THE OWNER ARMS
OR DECLINES; this lane did neither.**
**Pre-declaration:** `PREDECL-capx-d42-fossil-dates-ab-2026-09-02.md`, pushed
before any arm leg solved; graded at full magnitude in §6.
**Legs** (all MISO T1-H 2021–2025, vintage 2020, realized fuel; years
sequential within a leg; ONE leg at a time on this 15 GB box — a MISO year
solve holds ~8 GB, so rule 12's ~2-concurrent cap is a memory ceiling here):

| leg | run id | cache key | posture |
|---|---|---|---|
| control | `miso-2021-2025-realized-t1h-d42-control` | `b0f54861d57685c5` | shipped posture at HEAD, replayed |
| **dates (verified)** | `miso-2021-2025-realized-t1h-d42-dates` | `85000b5179ddff0f` | gate on; verified posture; fuel-scoped derate |
| dates (ex-ante) | `miso-2021-2025-realized-t1h-d42-dates-exante` | see §5 | gate on; `--no-verified-announced-exits`; fuel-scoped derate |
| dates (plant-wide, superseded) | `miso-2021-2025-realized-t1h-d42-dates-plantwide` | `85000b5179ddff0f` | gate on; verified; the first solve, on step 0's plant-wide derate — registered as the measurement of §4.3 |

Both verified solves share one config hash because the derate scope is
code, not config (the shared-key census test moved 15 → 16, annotated).
The legs solved on the pre-rebase branch (control and plant-wide at the
mechanism commit; the two scoped-derate legs at the derate-patch commit);
the branch was then rebased onto `origin/main` (D37/D43/nyiso-176 landed
mid-session — §8), none of whose changes touch a MISO solve.

---

## 0. Verdict (one paragraph)

**The owner's filed date is the exit model MISO's forecast was missing, and
the shipped posture that no-ops it is the −74 % residual.** With the date
honored as an exogenous step-1 input (verified posture, fuel-scoped derate):
`retire.unit_recall_gt300` **5/19 → 16/19 (0.842, PASS)**, plant-grain
0.737; `retire.total_gw` **4.469 → 9.799 GW (−74.3 % → −43.6 %**, band still
FAIL); the four fuels the shipped posture holds at exactly 0.0 all open
(gas_st 0.849, oil 0.154, gas_ct 0.132, gas_cc 0.002 GW); `false_retire`
stays PASS at **0.0 GW**; plant-grain precision of the released MW **13.4 %
→ 98.5 %**; T-R10 a/b PASS; LOYO recall holds in **2 of 3** folds; and —
the rule-19 point of the charter — **the economic screen decides nothing in
any year**: every exit in the arm is the owner's filed exit, and the
reliability floor, which decided 100 % of the control's composition, decides
none of it. What remains of the −43.6 % is (i) the UNDATED cohort — Rush
Island 1.24 GW, Big Cajun 2 0.66, South Oak Creek 0.60, LaO 0.46, Waterford 1
0.45, Teche 0.35, Grand Tower 0.34 — which no date channel can reach ex
ante, (ii) the majority-of-year roll of December-dated rows into 2026 (3.42
GW of verified-live MW sits at effective 2026), and (iii) the dated units
that really were deferred (Columbia, Schahfer 17/18, Lake Catherine,
Waterford 2 — 3.5 GW). The deferral class the charter worried about — the
six deferred/sold coal plants, ≈6.5 GW — is countered in every case by a
published per-unit record (a later EIA-860 Schedule-3 filing, or DOE
§202(c) for Campbell), never by a filter, and every EIA-860 re-filing was on
file in the 2021 vintage, i.e. knowable before the vintage date's effective
year; the ex-ante leg (§5) carries all of it at full magnitude. The price of
the exits is the adequacy response the shipped model has no other channel
for: reserve margin −1.0 % / −1.5 % in 2023/2024 (I7 FAIL, I12 WARN) before
the backstop fires 2,415 MW of gas_ct in 2025 and flips `add.by_tech.gas_ct`
PASS → FAIL — reported, not hidden, and routed (§7).

---

## 1. What was built (the mechanism, gated off)

`fossil_announced_exits_enabled` (default False; cache-neutral off — the
default key `cedadc285f8603b9` is unchanged at HEAD and the registration
guard is clean; an armed run hashes `4c6b03ae098b6e3e`). Armed, in forecast
mode:

* **Loader** (`data/announced_retirements.py`): every OPERABLE (`OP`) fossil
  unit of the ISO (BA → ISO, fuel by the fleet's own `_map_fuel_type`) with a
  Schedule-3 planned retirement year/month in the run's ACTIVE EIA-860
  vintage, nameplate MW. **Rule 13 `[R-MEASURED]` — the vintage gate:** the
  rows are the vintage snapshot's own filings, so a date is admissible in
  year Y only because it was on file at the run's information cutoff — the
  same gate step 0 applies to a confirmed row's `instrument_date` — and the
  identical construction regenerates for a forecast year from the
  then-current 860 (the planned-additions pipeline already reads the same
  form's proposed-generator schedule as a forward input). The filed date is
  an ex-ante owner PLAN that responds to conditions (it moved for Baldwin,
  Sherco 1, Schahfer), not a measured outcome.
* **Verified posture** (rides `hindcast_verified_announced_exits`, the
  2026-08-22 ex-ante-purity-vs-verified-fleet trade the harness already
  arms by default and records per leg): each vintage row is checked against
  the later in-repo vintages (2021–2024 + the canonical 2025 snapshot). A
  LATER re-filed date is a filed deferral and is honored as the later
  vintage's information; a dropped date is a withdrawn plan (a sale with
  continued operation); an absent unit exited, so its vintage date stands;
  an EARLIER re-filing is recorded but the vintage date stands. It may defer
  or cancel a vintage exit, **never inject or advance one** — the same
  "suppress a never-executed exit, never inject one" discipline the flag's
  reversal leg carries. Reversal-registry plants (J H Campbell under DOE
  §202(c)) are dropped. Zero parameters, applied uniformly, no fitted filter
  (rule 21 `[R-DOF]`); every disposition and the FIRST later vintage in
  which the filing changed are persisted on the first ledger year
  (`announced_fossil_schedule`, 112 rows).
* **Step 1b** (`evolve_fleet`, a LIMB of the step-1 announced channel, never
  a new step): the rows ride step 0's `apply_confirmed_exits` — a unit-grain
  row drops the unit (ledger `retirements`, reason `announced`), a
  plant-binned row derates the plant's tranches (ledger `announced_derates`,
  the twin of `confirmed_derates`; the I4 checker and the scorer both read
  it), first-half months carry a completion leg, and the first simulated
  year takes the pre-start backlog in `build_base_fleet` (894 MW here).
  **Fuel-scoped derate (§4.3):** a row that carries a fuel derates only the
  plant's binned generators of that fuel when it has any; fuel-less rows
  (the confirmed registry) keep the plant-wide derate, byte-identical.
* **Rule-19 `[R-ONE-MECH]` reconciliation** (designed with the gate, tested
  in `TestFossilAnnouncedExits`): (a) a plant carrying a pending admissible
  date is EXOGENOUS to the economic screen (`dated_plant_unit_ids` →
  `exempt_unit_ids`; unit-grain by generator ID, plant-binned by plant) —
  the filed plan IS the owner's exit decision, so the screen decides only
  undated plants and no unit's exit is decided twice; when a plant's last
  row has completed, its survivors re-enter the screen as an undated
  residual plant. (b) The R-NEW admission cap's counterfactual fleet nets
  every dated exit due by the cap horizon (`exogenous_exits`, applied year
  by year to `cap_year`), so the floor's retention pool sees the dated units
  as scheduled exogenous exits: it can neither retain them (never in
  `eligible`) nor over-admit undated candidates against capacity that is
  leaving anyway. (c) The realized-year floor tests the post-step-1 fleet; a
  unit dropped at step 1 is pruned from the pipeline state, so no `executed`
  row can follow it. Contrast the confirmed-exit precedent, where the screen
  may pre-empt a LEGAL latest-exit ceiling: an owner's own filed plan is not
  a ceiling on the owner's decision, it is the decision. Open item declared,
  not closed: the counterfactual nets DATED rows only, not the confirmed
  registry's future rows (a pre-existing grain of the cap; negligible in
  MISO's window).
* **Harness / scorer / checker:** `--fossil-announced-exits` (FromConfig
  record, FFR-3R); `score_capacity_hindcast` reads `announced_derates` and
  treats the D-24 economic-evidence exclusion as not applicable under the
  gate (the announced route is live for fossil — fail-closed, as the
  `forecast_fossil_retirement_economic=False` posture already is);
  `check_forecast_invariants` I4 subtracts `announced_derates` (found by the
  arm's first sidecar reading 1,873 MW of coal as unexplained — the FR-1
  leak class, fixed the same way).
* **Tests:** loader on synthetic vintages + the committed MISO 2020
  magnitudes; step-1 channel (unit drop, binned derate, backlog gating);
  reconciliation (a) and (b); gate-off byte identity; fuel-scoped derate;
  the I4 ledger identity with dated rows. **Matrix (rule 28):** base row
  `fossil_announced_exits` + a cell in all six shards (MISO `.`/fc `O`, the
  other five `U`).

## 2. The data census (loader on the committed vintage_2020 — data, no solve)

| set | rows | coal | gas_st | gas_ct | oil | gas_cc | total GW |
|---|---:|---:|---:|---:|---:|---:|---:|
| ex-ante, planned year ≤ 2025 | 83 | 18.451 | 2.355 | 0.577 | 0.443 | 0.022 | 21.849 |
| verified, planned year ≤ 2025 | 57 | 10.756 | 1.059 | 0.194 | 0.285 | 0.022 | 12.317 |
| ex-ante, **effective** year ≤ 2025 (majority-of-year rule) | — | 16.272 | 2.355 | 0.143 | 0.390 | 0.022 | 19.183 |
| verified, **effective** year ≤ 2025 | — | 9.359 | 1.059 | 0.000 | 0.232 | 0.022 | 10.673 |

Dispositions of the 112 dated fossil rows: deferred 54, exited 22, advanced
22 (vintage date stands), cancelled 10, reversed 3 (Campbell), kept 1. The
effective-year rule moves every December-dated row one year out, which is
why the in-window channel is 10.7 GW rather than the 12.3 GW D32 counted by
planned year: 3.42 GW of verified-live MW sits at effective 2026 (Sherco 1
765 MW at 2025/12; Schahfer 17/18, Culley 2, Sabine deferred to 2026; …).
Under the verified posture the channel carries **no gas_ct at all** in the
window — every 2020-vintage CT date was deferred or withdrawn — which is the
control against which §4.3's artifact was recognisable.

## 3. Control — the shipped posture at HEAD (P0 HIT)

Value-identical to D33 on every score row and every per-year ledger event:
`retire.total_gw` 4.469 (−74.3 %), coal 3.684, recall 5/19 (0.263),
`false_retire` 0.0, the 23-tranche 2022 coal decision executing 2024,
`entry_capped` 96,315 / 92,753 / 117,499 MW in 2022/2023/2024, reserve
margins 0.104 / 0.046 / 0.024 / 0.076 and peaks identical. Cache key
`b0f54861d57685c5` ≠ D33's `40173304213d39cd`, exactly as pre-declared (the
default key moved at HEAD on merges that do not touch a MISO solve). LOYO
recall folds 6/16, 0/15, 6/18 — holds in 0 of 3. Plant-grain precision of
the released MW 13.4 % (D32's 13.5 %, reproduced by the committed probe).

## 4. The arm

### 4.1 Score rows, control → verified arm

| row | control | **verified arm** | actual | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 4.469 (−74.3 %) | **9.799 (−43.6 %)** | 17.369 | FAIL → FAIL (±10 %) |
| coal | 3.684 | **7.877** | 12.434 | |
| gas_st | 0.000 | **0.849** | 2.127 | |
| oil | 0.000 | **0.154** | 0.543 | |
| gas_ct | 0.000 | **0.132** | 0.399 | |
| gas_cc | 0.000 | **0.002** | 0.858 | |
| nuclear (non-fossil channel, unchanged) | 0.768 | 0.768 | 0.812 | |
| `retire.unit_recall_gt300` | 5/19 (0.263) FAIL | **16/19 (0.842) PASS** | — | FAIL → **PASS** |
| `plant_recall_frac` (reported) | 0.211 | **0.737** (14/19 at plant+fuel grain) | — | |
| `false_retire` (per-fuel excess) | 0.0 PASS | **0.0 PASS** | — | PASS |
| plant-grain precision of released MW (probe) | 13.4 % | **98.5 %** (148 MW at 2 plants: Blue Lake's oil-dated CTs carried as gas_ct; French Island biomass) | — | reported |
| T-R10a / b | PASS / PASS | PASS / PASS (vacuous — no economic exits) | | |
| LOYO recall folds (−2023 / −2024 / −2025) | 6/16 F, 0/15 F, 6/18 F → 0/3 | **8/16 F, 14/15 P, 15/18 P → holds 2/3** | | |
| economic `decided` / `executed` MW | 3,684 / 3,684 | **0 / 0** | | |
| admission cap `entry_capped` MW, 2022 / 2023 / 2024 | 96,315 / 92,753 / 117,499 | 76,751 / 74,223 / **0** | | |
| BLK-10 backstop fired | 0 | **2,415 MW gas_ct, 2025** | | |
| `add.by_tech.gas_ct` | 1.472 PASS | **4.415 FAIL** | 1.355 | PASS → FAIL |
| `add.shares.gas_ct` | 0.057 FAIL | 0.173 FAIL | 0.042 | |
| reserve margin 2023 / 2024 / 2025 | 0.046 / 0.024 / 0.076 | **−0.010 / −0.015 / 0.052** | | I7 FAIL, I12 WARN |
| FC-3 band-FAIL list | 8 rows | 8 rows (`retire.unit_recall_gt300` out, `add.by_tech.gas_ct` in) | | HOLD both |

Wind / solar / gas_cc / storage additions are identical between the legs
(8.0 / 4.946 / 4.146 / 4.0 GW): the D33 growth-ladder ceiling on solar is
untouched by this lane, as pre-declared.

### 4.2 Per-year mechanism (the committed ledgers)

| year | announced drops (MW) | announced derates (MW) | screen: candidates capped | decided | executed | reserve margin |
|---|---:|---:|---:|---:|---:|---:|
| 2021 (seed; 894 MW pre-start backlog in the base fleet) | — | — | — | — | — | 0.098 |
| 2022 (bridge) | 2,877 | 1,896 | 76,751 | 0 | 0 | — |
| 2023 | 2,178 | 1,602 | 74,223 | 0 | 0 | −0.010 |
| 2024 | 752 | 207 | 0 (no failing candidate) | 0 | 0 | −0.015 |
| 2025 | 153 | 132 | 0 | 0 | 0 | 0.052 |

The screen's release (3,684 MW in the control) goes to zero by
construction of reconciliation (b): with ~10 GW of scheduled exogenous exits
netted in the admission counterfactual, the floor cannot admit a single
undated candidate in 2022/2023 (it still binds — 76.8 / 74.2 GW of
candidates capped — but it is no longer SELECTING a composition, because
every exit that happens is the owner's), and by 2024 the thinned stack
clears every remaining unit's bar. D32's "the floor is the exit model"
finding is therefore not repaired by re-ranking the floor; it is dissolved
by giving the exit decision to the driver that identifies it.

### 4.3 The plant-wide derate artifact (measured, repaired, both registered)

The first verified solve reused step 0's derate as-is. That derate is
PLANT-WIDE: every binned generator of the plant scales by one factor,
whatever its fuel group. At MISO's mixed-fuel plants a dated COAL unit's MW
therefore bled onto the plant's gas bins — Karn 1–2 (coal, 2023) derated
Karn's ST_GAS bins by 360 MW; Schahfer 14/15 its CT bins by 96 MW; A B
Brown, St Clair, Heskett likewise; Blue Lake's oil date its CT bins. The
probe read it directly on the plant-wide leg: gas_ct 479 MW released
against 399 MW real at 9.4 % plant-grain precision, 8 false-positive plants
/ 809 MW, and coal correspondingly under-landed (7.345 vs 7.877 GW). §2's
census — the verified channel carries NO gas_ct in the window — is what made
the artifact unmistakable. This is a cross-fuel COMPOSITION error, not the
second-order heat-rate shift the step-0 docstring accepts, so it was
repaired in-lane: a row that carries a fuel now derates only the plant's
bins of that fuel (fuel-less confirmed rows keep the plant-wide derate,
byte-identical, tested). Plant-wide → scoped: total 9.972 → 9.799 GW,
recall 15/19 → 16/19, false-positive plants 8 → 2, precision 91.9 → 98.5 %,
gas_ct 0.479 → 0.132, gas_st 1.209 → 0.849, coal 7.345 → 7.877. The
plant-wide leg stays registered (`miso-t1h-d42-dates-plantwide`) as the
artifact's measurement.

### 4.4 The deferral class — at full honesty

Vintage dates effective ≤ 2025 that the verified posture moved out of the
window or withdrew (from the persisted `announced_fossil_schedule`; *first
change* = the first later vintage whose filing differed; *knowable* = that
vintage + 1 ≤ the vintage date's effective year, i.e. a rolling-vintage
ex-ante run would have seen the re-filing in time):

| plant | unit(s) | fuel | MW | vintage date → effective | verified | first change | knowable in time |
|---|---|---|---:|---|---|---|---|
| Coal Creek (6030) | 1, 2 | coal | 1,209.6 | 2022/10 → 2023 | withdrawn (sold to Rainbow Energy) | v2021 | yes |
| Columbia (8023) | 1, 2 | coal | 1,112.0 | 2023/12, 2024/12 → 2024, 2025 | → 2029 | v2021 | yes |
| Merom (6213) | 1, 2 | coal | 1,080.0 | 2023/5 → 2023 | withdrawn (sold to Hallador) | v2021 | yes |
| Schahfer (6085) | 17, 18 | coal | 847.0 | 2023/6 → 2023 | → 2026 | v2021 | yes |
| R D Green (6639) | 1, 2 | coal | 586.0 | 2022/3 → 2022 | withdrawn | v2021 | yes |
| Lake Catherine (170) | 4 | gas_st | 552.5 | 2025/6 → 2025 | → 2027 | v2021 | yes |
| Waterford (8056) | 2 | gas_st | 445.5 | 2024/6 → 2024 | → 2028 | v2021 | yes |
| Edgewater (4050) | 5 | coal | 413.7 | 2022/12 → 2023 | withdrawn | v2021 | yes |
| Sabine (3459) | 1 | gas_st | 239.4 | 2023/6 → 2023 | → 2026 | v2021 | yes |
| French Island (4005) | 3, 4 | oil | 157.6 | 2022/12 → 2023 | → 2030 | v2021 | yes |
| Culley (1012) | 2 | coal | 103.7 | 2023/12 → 2024 | → 2026 | v2021 | yes |
| Geismar (56787) | GTG | gas_ct | 83.9 | 2024/1 → 2024 | → 2030 | v2021 | yes |
| Sterlington (1404); Moselle (2070) | 7A; 3 | gas_ct; gas_st | 118.3 | 2022/6, 2025/1 | withdrawn | v2021 | yes |
| **J H Campbell (1710)** | 1, 2, 3 | coal | 1,560.8 | 2025/5 → 2025 | **reversed — DOE FPA §202(c), May 2025** (registry) | — | **no** (the order postdates every vintage ≤ 2024) |

**8,510 MW** in all — the ex-ante − verified in-window gap (19.18 − 10.67
GW). Every counter is a published per-unit record: a later EIA-860
Schedule-3 filing (6,949 MW), or a federal order (Campbell, 1,561 MW). Every
EIA-860 re-filing was on file in the **2021** vintage — knowable for solve
year 2022 onward, before the vintage date's effective year in every case —
so a rolling-vintage forecast would have carried none of them as false
positives. Only Campbell is unknowable ex ante, and it is the one countered
by the registry, not by a re-filing. No filter was fitted to any of it; the
ex-ante leg (§5) carries all 8.5 GW.

Reported against interest: Waterford 1 & 2 (8056) is a real 445.5 MW
gas_st exit in 2024 that the verified posture DEFERS (the 2020 vintage dated
unit 2 for 2024/6; the later vintages moved it to 2028 while unit 1 left the
operable file) — a true positive lost to the verification, and one of the
three ≥300 MW misses. The verification is a uniform rule and takes this
loss with the eleven gains.

## 5. The ex-ante leg (pure 2020-vintage dates, no verification)

TBD — solving; filled below when registered.

## 6. Grading the pre-declaration (full magnitude)

| # | declared | measured (verified arm) | grade |
|---|---|---|---|
| P0 | control = D33 value-identical; key ≠ D33's | identical on every row and ledger event; `b0f54861d57685c5` | HIT |
| P1 | channel opens gas_st +1.1 / oil +0.3 / gas_ct +0.2 / coal +9.7; every 0.0 fuel > 0 | gas_st 0.849 (low), oil 0.154 (low), gas_ct 0.132 (low), coal 7.877 (low — the effective-year 2026 roll and the deferrals); every fuel > 0 | direction HIT, magnitudes LOW on all four |
| P2 | recall 5/19 → ≥ 13/19 | 16/19 | HIT |
| P3 | `err_frac` in [−35 %, +5 %] | −43.6 % | **MISS** — the undated cohort (§0) is larger than the declaration allowed for |
| P4 | `false_retire` PASS; plant-grain FPs reported | 0.0 PASS; 148 MW at 2 plants | HIT |
| P5 | economic release ≤ 3,684 MW, never a dated plant | 0 MW | HIT |
| P6 | T-R10 a/b PASS | PASS / PASS (vacuous) | HIT |
| P7 | LOYO recall holds ≥ 2/3; control 0/3 | 2/3; 0/3 | HIT |
| P8 | additions: direction unknown, declared not predicted | the adequacy backstop fires 2,415 MW gas_ct (2025); `add.by_tech.gas_ct` PASS → FAIL; wind/solar/gas_cc/storage unchanged | declared, reported |
| P9 | HOLD on FC-3 every leg; no `miso-t1h` edit; suffixed keys only | HOLD ×3 (ex-ante pending); board edits insert-only | HIT |

Not pre-declared, found: the §4.3 derate artifact (repaired in-lane) and
the I4 checker gap (repaired). Both are reported with their measurements.

## 7. Posture recommendation (for the owner — this lane neither arms nor declines)

The evidence on every measured axis points the same way, and the decision
is a POSTURE, not a fit:

1. **Admissibility.** An owner's filed Schedule-3 date passes the rule-13
   forward test by the same reading the additions pipeline already passes
   (the same form's proposed-generator schedule is a forecast input today).
   The shipped default's rationale — "an announcement is not a certainty" —
   is a statement about precision, and the measured precision at plant
   grain is 98.5 % under verification and (§5) under the pure vintage.
2. **The channel identifies the cohort the screen cannot.** Recall 16/19,
   the non-coal classes open, the floor's composition monopoly dissolved by
   construction — with zero free parameters and zero economic exits, so
   nothing here was tuned to the residual (rule 21).
3. **What it does NOT close, stated plainly:** the undated cohort (≈3.7 GW
   of large real exits with no 2020-vintage date), the December-to-2026
   roll (a timing grain, not a posture), and the real deferrals. A rolling
   vintage (refreshing the dated set from each year's newest 860) is the
   forward-regenerable construction that would consume the re-filings in
   time; it is a design choice for the owner, not a lever.
4. **The adequacy response is now the object.** Exogenous exits at this
   scale push MISO below its requirement in 2023/2024 (I7 FAIL) before the
   backstop responds in 2025; the additions side (the D33 ladder ceiling,
   the entry screen's timing) is what a live channel exposes next. The
   backstop's 2.4 GW gas_ct is the model saying "something must replace
   this" — which is the additions lane's question (D33 §4.1, D39), not a
   reason to hold the exits back.
5. **Recommended posture, if the owner arms:** `fossil_announced_exits_
   enabled=True` for MISO via `default_scenario_overrides` (rule 25 — a
   MISO verdict; the other five ISOs enter as `U` and measure their own
   cohorts), verified posture in hindcasts as today, and the sector gate
   (D32 R3) as the structural companion for the undated cohort. **If the
   owner declines**, the finding stands as the measurement that the −74 %
   residual is a posture, and D32 R2/R6 (the retention-key repair, age)
   cannot reach it.

## 8. Governance attestation

* **Rule 12:** every leg ran its years sequentially; legs ran one at a time
  (memory ceiling), never two MISO solves concurrently.
* **Rule 13 / 14 / 21:** the channel's content is the vintage's own
  filings (a forward driver, not an outcome); the verification consults
  later published filings uniformly and never injects or advances; no
  parameter, threshold or filter was identified against any residual; the
  D32 pre-declared numbers were restated verbatim and graded at full
  magnitude, the one MISS (P3) included.
* **Rule 15 / forecast-dashboard duty:** every completed run is registered
  on the forecast namespace via the single `register_forecast_run.py` path
  — four sidecars, four suffixed verdict keys (insert-only board edits), the
  bare `miso-t1h` untouched, `program-status.json` untouched, no backcast
  file touched.
* **Rule 19:** the reconciliation is designed, documented in the field
  docstring and the module docstrings, and tested; one ledger row per exit.
* **Rule 22:** solve years 2021/2023/2024/2025 (2022 bridged), scored
  2023–2025, LOYO within 2023–2025; no out-of-training year touched; the
  verification reads the 2021–2025 EIA-860 vintages (the working span's own
  filings, no H1-2026 actuals).
* **Rule 27:** every ≥300-line file was edited locally and pushed as
  on-disk bytes; after every push the remote blob of each such file was
  compared to the local hash (all OK, 13/13 after the rebase push).
* **Rule 28:** base row + six cells landed in the mechanism commit; the MISO
  cell carries the measured evidence; anchors repaired with `--fix-anchors`
  (twice: after the field's docstring shifted lines, and after the rebase).
* **Collision / rebase:** D37 (NEISO) and D43 (CAISO) landed on main
  mid-session; the rebase conflicted only on the cache-key tuple tail
  (kept both), the matrix anchor digits (took main's, re-inserted the row,
  re-fixed anchors) and `.gitignore` (kept both blocks). The shared-key
  census test moved 15 → 16 for the two same-config verified solves
  (annotated in the test). `test_entry_vre_zone_selection`'s default-key
  pin was already red on main before this lane and was fixed on main
  mid-session; it passes after the rebase.
* **Probes:** `scripts/probes/_capxd42_plant_grain.py` (committed; reads
  committed ledgers + the actuals target only) reproduces D32's 13.5 % on
  D33 and every plant-grain number above.
