# FINDING — capx D42: the fossil announced-date posture A/B (D32 R1) — honoring the owner's filed EIA-860 retirement date as an exogenous step-1 input takes MISO's T1-H recall from 5/19 to TBD/19, opens every non-coal exit class the floor held at zero, retires nothing the screen would have (zero economic exits), and leaves the residual where the data says it is: the undated cohort and the December-dated 2026 roll; the deferral class is countered per unit by published re-filings, every one of them knowable before its vintage date

**Lane:** capx D42 — owner ruling Q29 on D32's R1
(`FINDING-capx-d32-floor-retention-2026-09-02.md` §7). A MEASUREMENT lane:
the gate `ScenarioConfig.fossil_announced_exits_enabled` ships DEFAULT-OFF,
every leg registered SUFFIXED, the bare `miso-t1h` key untouched. **Nothing
arms. THE OWNER ARMS OR DECLINES; this lane did neither.**
**Pre-declaration:** `PREDECL-capx-d42-fossil-dates-ab-2026-09-02.md`, pushed
before any arm leg solved; graded at full magnitude in §6.
**Legs (all MISO T1-H 2021–2025, vintage 2020, realized fuel, years
sequential, one leg at a time on this 15 GB box):**

| leg | run id | cache key | posture |
|---|---|---|---|
| control | `miso-2021-2025-realized-t1h-d42-control` | `b0f54861d57685c5` | shipped posture at HEAD, replayed |
| dates (verified) | `miso-2021-2025-realized-t1h-d42-dates` | TBD | gate on; verified posture; fuel-scoped derate |
| dates (ex-ante) | `miso-2021-2025-realized-t1h-d42-dates-exante` | TBD | gate on; `--no-verified-announced-exits`; fuel-scoped derate |
| dates (plant-wide, superseded) | `miso-2021-2025-realized-t1h-d42-dates-plantwide` | `85000b5179ddff0f` | gate on; verified; the first solve, on step 0's plant-wide derate — kept as the measurement of §4.3 |

Solved at branch commit `c5feec13` (the fuel-scoped derate), the control and
plant-wide legs one commit earlier at `4fe0e8d`-class HEAD (pre-derate-patch;
the patch is byte-inert for fuel-less rows, so the control is unaffected —
§4.3). The branch was rebased onto `origin/main` after the last leg launched
(§8).

---

## 0. Verdict (one paragraph)

TBD after the final verified arm — the plant-wide leg already establishes the
direction and most of the magnitude: **the channel is the exit model MISO was
missing.** With the owner's filed date honored, `retire.unit_recall_gt300`
goes 5/19 → 15/19 (PASS at 0.789, plant-grain 0.737), `retire.total_gw` 4.469
→ 9.972 GW (−74.3 % → −42.6 %; band still FAIL), the four fuels the shipped
posture holds at exactly 0.0 (gas_st, oil, gas_ct, gas_cc) all read > 0, the
per-fuel `false_retire` stays PASS (0.08 GW), plant-grain precision of the
released MW goes 13.5 % → 91.9 %, the T-R10 guards pass, LOYO recall holds in
2 of 3 folds, and — the rule-19 point — **the economic screen decides nothing
at all in any year**: every exit in the arm is the owner's filed exit. What
remains of the −42.6 % is (i) the undated cohort (Rush Island 1.24 GW, Big
Cajun 2 0.66, Teche 0.35, South Oak Creek 0.60, LaO 0.46, Grand Tower 0.34 —
no 2020-vintage date, so no channel can reach them ex ante), (ii) the
majority-of-year roll of December-dated 2025 rows into 2026 (3.4 GW live,
outside the window), and (iii) the verified deferrals that really were
deferred (Columbia, Schahfer 17/18, Lake Catherine, Waterford 2 — 3.5 GW,
every one knowable before its vintage date). The deferral class the charter
worried about is countered by a published per-unit re-filing in every case,
never by a filter; the ex-ante leg carries it at full magnitude.

---

## 1. What was built (the mechanism, gated off)

`fossil_announced_exits_enabled` (default False; cache-neutral off — the
default key `cedadc285f8603b9` is unchanged and the registration guard is
clean). Armed, in forecast mode:

* **Loader** (`data/announced_retirements.py`): every OPERABLE (`OP`) fossil
  unit of the ISO (BA → ISO, fuel by the fleet's own `_map_fuel_type`) with a
  Schedule-3 planned retirement year/month in the run's ACTIVE EIA-860
  vintage, nameplate MW. **Rule 13 vintage gate:** the rows are the vintage
  snapshot's own filings, so a date is admissible only because it was on file
  at the cutoff — the same information gate step 0 applies to
  `instrument_date` — and the identical construction regenerates for a
  forecast year from the then-current 860. The filed date is an ex-ante owner
  PLAN, not a measured outcome.
* **Verified posture** (rides `hindcast_verified_announced_exits`, the
  2026-08-22 ex-ante-purity-vs-verified-fleet trade the harness already
  records per leg): each row is checked against the later in-repo vintages
  (2021–2024 + the canonical 2025). A LATER re-filed date is a filed deferral
  and is honored as the later vintage's information; a dropped date is a
  withdrawn plan (a sale with continued operation); an absent unit exited and
  its vintage date stands; an EARLIER re-filing is recorded but the vintage
  date stands. It may defer or cancel, **never inject or advance**. Reversal-
  registry plants (J H Campbell under DOE §202(c)) are dropped. Zero
  parameters, applied uniformly; every disposition + the first vintage in
  which it changed is persisted on the first ledger year
  (`announced_fossil_schedule`).
* **Step 1b** (`evolve_fleet`): the rows ride step 0's `apply_confirmed_exits`
  — unit-grain rows drop the unit (ledger `announced`), plant-binned rows
  derate the plant's tranches (ledger `announced_derates`, the twin of
  `confirmed_derates`), first-half months carry a completion leg, the first
  simulated year takes the pre-start backlog in `build_base_fleet` (894 MW
  here). **Fuel-scoped derate (§4.3):** a row that carries a fuel derates only
  the plant's binned generators of that fuel when it has any; fuel-less rows
  (the confirmed registry) keep the plant-wide derate, byte-identical.
* **Rule-19 reconciliation** (designed with the gate, tested):
  (a) a plant with a pending admissible date is EXOGENOUS to the economic
  screen (`dated_plant_unit_ids` → `exempt_unit_ids`; unit-grain by generator
  ID, plant-binned by plant) — the filed plan IS the owner's exit decision, so
  the screen decides only undated plants and no exit is decided twice;
  (b) the R-NEW admission cap's counterfactual fleet nets every dated exit due
  by the cap horizon (`exogenous_exits`), so the floor's retention pool sees
  the dated units as scheduled exogenous exits — it can neither retain them
  nor over-admit undated candidates against capacity that is leaving;
  (c) the realized-year floor tests the post-step-1 fleet; a unit dropped at
  step 1 is pruned from the pipeline state, so no `executed` row can follow.
  Open item declared, not closed: the counterfactual nets DATED rows only, not
  the confirmed registry's future rows (a pre-existing grain of the cap).
* **Harness / scorer:** `--fossil-announced-exits` (FromConfig record);
  `score_capacity_hindcast` reads `announced_derates` and treats the D-24
  economic-evidence exclusion as not applicable under the gate.
* **Tests:** loader (synthetic vintages + the committed MISO 2020 magnitudes),
  step-1 channel, reconciliation (a)/(b), gate-off byte identity, fuel-scoped
  derate. Matrix: base row `fossil_announced_exits` + a cell in all six shards.

## 2. The data census (loader on the committed vintage_2020, no solve)

| set | rows | coal | gas_st | gas_ct | oil | gas_cc | total GW |
|---|---:|---:|---:|---:|---:|---:|---:|
| ex-ante, exit year ≤ 2025 | 83 | 18.451 | 2.355 | 0.577 | 0.443 | 0.022 | 21.849 |
| verified, exit year ≤ 2025 | 57 | 10.756 | 1.059 | 0.194 | 0.285 | 0.022 | 12.317 |
| ex-ante, EFFECTIVE year ≤ 2025 (majority-of-year rule) | — | 16.272 | 2.355 | 0.143 | 0.390 | 0.022 | 19.183 |
| verified, EFFECTIVE year ≤ 2025 | — | 9.359 | 1.059 | 0.000 | 0.232 | 0.022 | 10.673 |

Dispositions of the 112 dated fossil rows: deferred 54, exited 22, advanced
22 (date stands), cancelled 10, reversed 3 (Campbell), kept 1. The
effective-year rule moves every December-dated row one year out, which is
why the in-window channel is 10.7 GW, not 12.3: 3.42 GW of verified-live MW
sits at effective 2026 (Sherco 1 765, Campbell reversed anyway, Schahfer
17/18 → 2026, Culley 2, Sabine, …).

## 3. Control — the shipped posture at HEAD (P0 HIT)

Value-identical to D33 on every score row and every per-year ledger event:
`retire.total_gw` 4.469 (−74.3 %), coal 3.684, recall 5/19 (0.263),
`false_retire` 0.0, the 23-tranche 2022 coal decision executing 2024, reserve
margins 0.104 / 0.046 / 0.024 / 0.076 and peaks identical. Cache key
`b0f54861d57685c5` ≠ D33's `40173304213d39cd`, exactly as pre-declared (the
default key moved at HEAD on merges that do not touch a MISO solve). LOYO
recall: 6/16, 0/15, 6/18 — 0 of 3 folds.

## 4. The arm

### 4.1 Score rows, control → verified arm (TBD: final; plant-wide leg in brackets)

| row | control | verified arm | actual | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 4.469 (−74.3 %) | TBD [9.972, −42.6 %] | 17.369 | FAIL → FAIL |
| coal | 3.684 | TBD [7.345] | 12.434 | |
| gas_st | 0.000 | TBD [1.209] | 2.127 | |
| oil | 0.000 | TBD [0.154] | 0.543 | |
| gas_ct | 0.000 | TBD [0.479] | 0.399 | |
| gas_cc | 0.000 | TBD [0.001] | 0.858 | |
| nuclear (non-fossil channel, unchanged) | 0.768 | 0.768 | 0.812 | |
| `retire.unit_recall_gt300` | 5/19 (0.263) FAIL | TBD [15/19 (0.789) PASS] | — | FAIL → PASS |
| `plant_recall_frac` | 0.211 | TBD [0.737] | — | reported |
| `false_retire` (per-fuel excess) | 0.0 PASS | TBD [0.08 PASS] | — | PASS |
| plant-grain precision of released MW (probe) | 13.4 % | TBD [91.9 %] | — | reported |
| T-R10a / b | PASS / PASS | PASS / PASS (vacuous — no economic exits) | | |
| LOYO recall folds (−2023 / −2024 / −2025) | 6/16 F, 0/15 F, 6/18 F | TBD [7/16 F, 14/15 P, 16/18 P] → holds 2/3 | | |
| economic `decided` / `executed` MW | 3,684 / 3,684 | TBD [0 / 0] | | |
| BLK-10 backstop fired | 0 | TBD [2,415 MW gas_ct, 2025] | | |
| `add.by_tech.gas_ct` | 1.472 PASS | TBD [4.415 FAIL] | 1.355 | |
| reserve margin 2023 / 2024 / 2025 | 0.046 / 0.024 / 0.076 | TBD [−0.011 / −0.016 / 0.050] | | |

### 4.2 Per-year mechanism (the ledgers)

TBD (final arm). Plant-wide leg: 2022 announced 2,792 MW drops + 2,011 MW
derates, admission cap capped 76,709 MW of candidates and admitted none;
2023 1,737 + 2,146, capped 73,808, admitted none; 2024 262 + 738, NO failing
candidate; 2025 153 + 132, none. The screen's release (3,684 MW in the
control) goes to zero: with ~10 GW of scheduled exogenous exits netted in the
admission counterfactual (reconciliation (b)), the floor cannot admit a
single undated candidate in 2022/2023, and by 2024 the tightened stack clears
every unit's bar. **The floor still binds on the admission side — it is no
longer selecting the composition**, because there is nothing left for it to
select: the composition is the owner's.

### 4.3 The plant-wide derate artifact (measured, then repaired)

The first verified solve reused step 0's derate as-is. That derate is
PLANT-WIDE: every binned generator of the plant scales by the same factor,
whatever its fuel group. At MISO's mixed-fuel plants a dated COAL unit's MW
therefore bled onto the plant's gas bins — Karn 1–2 (coal, 2023) derated
Karn's ST_GAS bins by 360 MW; Schahfer 14/15/17/18 derated its CT bins by
96 MW; A B Brown, St Clair, Heskett, Blue Lake (oil → CT) likewise. The
probe read it directly: gas_ct 479 MW released against 399 MW real at
9.4 % plant-grain precision, 8 false-positive plants / 809 MW, and coal
correspondingly under-landed. This is a composition error, not the
second-order heat-rate shift the step-0 docstring accepts, so it was
repaired in-lane: a row that carries a fuel now derates only the plant's
bins of that fuel (fuel-less confirmed rows keep the plant-wide derate,
byte-identical, tested). The plant-wide leg stays registered as the
artifact's measurement; the verified and ex-ante arms below solve on the
scoped derate.

### 4.4 The deferral class — at full honesty

Vintage dates effective ≤ 2025 that the verified posture moved out of the
window or withdrew (from the persisted schedule; `first change` = the first
later vintage whose filing differed; `knowable` = that vintage + 1 ≤ the
vintage date's effective year, i.e. a rolling-vintage ex-ante run would have
seen the re-filing in time):

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
| Sterlington (1404), Moselle (2070) | 7A; 3 | gas_ct; gas_st | 118.3 | 2022, 2025 | withdrawn | v2021 | yes |
| **J H Campbell (1710)** | 1, 2, 3 | coal | 1,560.8 | 2025/5 → 2025 | **reversed — DOE §202(c), May 2025** (registry) | — | **no** (the order postdates every vintage ≤ 2024) |

**8,510 MW** in total, the difference between the ex-ante and verified
in-window channels (19.18 − 10.67 GW). Every counter is a published per-unit
record — a later EIA-860 Schedule-3 filing or a federal order — and every one
of the EIA-860 re-filings was on file in the 2021 vintage, i.e. knowable for
solve year 2022 onward, before the vintage date's effective year in every
case. **Only Campbell is unknowable ex ante**, and it is the one countered by
the registry, not by a re-filing. The ex-ante leg (§5) carries all 8.5 GW as
false positives at full magnitude; no filter was fitted to any of it.

## 5. The ex-ante leg (pure 2020-vintage dates)

TBD.

## 6. Grading the pre-declaration (full magnitude)

TBD after the final arm. On the plant-wide leg: P0 HIT; P1 direction HIT on
every fuel (gas_st 1.209 vs +1.1 ✓, oil 0.154 vs +0.3 low, gas_ct 0.479 vs
+0.2 high — the §4.3 artifact, coal 7.345 vs +9.7 low — the 2026 roll and the
over-subscribed plants); P2 HIT (15/19 ≥ 13/19); P3 MISS (−42.6 % is outside
the declared [−35 %, +5 %]); P4 HIT (false_retire PASS; plant-grain FPs
reported: 809 MW, all the §4.3 artifact); P5 HIT (economic release 0 ≤
3,684); P6 HIT; P7 HIT (2/3 folds); P8 declared-not-predicted: additions did
move — the adequacy backstop fired 2,415 MW of gas_ct in 2025 (the exits
thinned the stack below the floor: reserve margin −1.1 % / −1.6 % in
2023/2024) and `add.by_tech.gas_ct` flips PASS → FAIL; P9 HIT (HOLD on FC-3,
no `miso-t1h` edit).

## 7. Posture recommendation (for the owner — this lane neither arms nor declines)

TBD after the final arm; the direction on every measured axis is the same:
the filed date is the identified exit driver, the screen is not, and the
reconciliation removes the floor's composition monopoly by construction.
What the owner is deciding is a POSTURE, not a fit: (i) whether an owner's
filed plan is an admissible forward driver (this lane's answer: yes, by the
same test the additions pipeline already passes); (ii) which verification
posture a hindcast may carry (the same trade the 2026-08-22 flag already
records; the ex-ante leg shows the price of not carrying it); (iii) the two
named residuals that no date channel can reach — the undated cohort and the
adequacy response to the exits (the backstop firing, the additions ceiling).

## 8. Governance attestation

TBD (rules 12/13/14/15/21/22/27/28; collision; rebase; the pre-existing
cache-key pin test on main).
