# FINDING — nyiso-184 (`stgas-heat-rate-basis` lane): the 9.50 is a HAND NUMBER in a per-plant dict lifting a PLANT-GRAIN eGRID blend; Astoria is a MEASURED-SIDE artifact, not a model object; the zero-parameter family construction is built, gate-tested and **NOT PROPOSED** — it misses its own pre-registered consistency bar by 0.027 and the whole miss sits in one EIA-923 number

**Session:** nyiso-184, `stgas-heat-rate-basis` lane
(`claude/nyiso-184-stgas-heat-rate-90z3qr`), NYISO backcast-calibration track,
2026-09-04. **Solves run: ZERO.**
**Keeper at entry and exit: `2026-09-02-nyiso-177-vintage-matched`**
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**, target
grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.
**Unchanged.** No parameter touched, no band swept, no constant moved; **one
`ScenarioConfig` field added, DEFAULT-OFF and byte-identical off, with its
matrix row and a cell in every shard in the same PR (rule 28c) — NOT armed in
any run and NOT proposed as a keeper candidate.**
**Pre-registration:** `results/calibration/PREREG-nyiso184-stgas-heat-rate-basis.md`,
pushed to `origin` at `19d809d9` **before the first gate measurement**.
**Machine records:** `results/calibration/_nyiso184_heat_rate_basis.json`
(gates G0–G4 + a labelled post-hoc block) and
`_nyiso184_heat_rate_basis_prefix_g1unit.json` (the pre-repair run, preserved
unread-past-G1, §3.1); probe `scripts/probes/nyiso184_heat_rate_basis.py`;
derive `scripts/data/derive_egrid_family_heat_rates.py` → artifact
`data/raw/_processed-legacy/egrid_family_heat_rates_NYISO.csv` (+ `_vintages.csv`).
**PREREG §6 S2 FIRED — no solve was spent, R1 is not proposed, nothing is
registered.** Rule 15 has nothing to register (the nyiso-179 / -180 / -181 /
-183 zero-solve precedent).

---

## 1. The result in one paragraph

The brief handed this session one term — a 9.50 MMBtu/MWh `ST_GAS` base heat
rate at Ravenswood (2500) against a 10.71 meter — with the join named but not
adjudicated and a second, unexplained term (`CC_REGULAR` 8.80 vs `ST_GAS` 9.50
at the same plant). **Both terms are now traced to source and proved as
identities, not asserted.** The 8.80 is eGRID-2023 `PLNT23.PLHTRT` for ORISPL
2500 joined at PLANT grain to every generator row (G1: parquet == `PLHTRT`/1000
to 0.0, `PLHTIAN`/`PLNGENAN` == `PLHTRT` to 1.2e-8). The 9.50 is
**`fleet.models.MIXED_FACILITY_STEAM_HR[2500] = 9.5`** — a hardcoded per-plant
dict, always on, ungated, lifting only the `ST_GAS` rows of the same blend
(G0: committed tranche ÷ 1.05 = peak ÷ 4.20 = 9.50; CC committed ÷ 0.90 =
8.8004). Its 9.5 is **not a measurement**: its own comment derives it from
ASSUMED capacity factors that put two-thirds of the site's energy on the steam;
CAMPD 2023 puts one-third there. **Astoria (8906) is NOT the same object and
is NOT a model-side object at all**: its "measured" 5.39–5.55 is the known
CAMPD stack-duplicate double count (`31RH`/`32SH`, `51RH`/`52SH` each repeat
the boiler's full gross while splitting its heat); merged, its G4d ratio reads
**1.697 / 1.717 / 1.761** against peer clusters [1.636, 1.749] / [1.604, 1.745]
/ [1.596, 1.749] — inside in 2 of 3, G3 FIRES. **The one admissible repair —
eGRID at PRIME-MOVER-FAMILY grain, Σ`HTIAN`/Σ`GENNTAN` per family from the
same vintage the join reads, zero parameters — was built, tested,
gate-checked and NOT PROPOSED**: it puts Ravenswood's steam at **12.29** (in
window, above the meter's 10.71, G2a/G2b hold) but its like-for-like ratio to
the meter, **1.148**, sits **0.027 above** the eight peers' range [1.059,
1.121] (G2c fails). A post-hoc factorisation puts the entire excess in a single
number: EIA-923's net generation for the 1,000 MW unit 30 is **0.862** of its
CAMPD gross, where its sister units read 0.913 / 0.933 and every peer steam
plant 0.923–0.959 — idle-period house load at a 4 % capacity factor, on the
same convention every peer carries, amplified by the unit's size. **The bar is
not moved; the object stays open, now with its two terms named, its mirror
image closed, and its repair form sitting default-off with a stated gap.**

---

## 2. RULE 19 `[R-ONE-MECH]`, discharged from the code and then PROVED on data

PREREG §1 enumerated ten mechanisms that can set an NYISO `ST_GAS` base heat
rate on this keeper and answered from the code: **mechanism 1**
(`process_eia860._join_egrid_heat_rate`, plant-grain eGRID-2023 `PLHTRT`
written into the committed parquet) owns the 8.80 on all five Ravenswood rows,
and **mechanism 5** (`_correct_mixed_facility_steam_hr` over the
`MIXED_FACILITY_STEAM_HR` dict, always on, no `ScenarioConfig` field) owns the
9.50. Mechanisms 3 (boundary repair: `gas_cc`, `{55641}` only), 4
(`measured_ct_heat_rates`: `CT_PEAKER` only, 2500 absent), 6
(`measured_chp_heat_rates`: CHP only), 7 (`egrid_identity_heat_rates`: 7784
only) and 8 (the CHP hand factor) are class- or plant-disjoint; 9 and 10
multiply the base and never set it.

**G0 and G1 turned both into measured identities:**

| gate | statistic | measured | bar | verdict |
|---|---|---|---|---|
| G0 | no-LP reconstruction vs nyiso-183's committed G4d `model_hr`, every `ST_GAS` plant, 3 years | worst \|Δ\| **0.00037** | ≤ 0.005 | PASS |
| G0 | Ravenswood `ST_GAS` base from committed tranche ÷ 1.05 and peak ÷ 4.20 | **9.5000 / 9.5000** | 9.50 ± 0.01 | PASS |
| G0 | Ravenswood `CC_REGULAR` base from committed tranche ÷ 0.90 | **8.8004** | 8.80 ± 0.01 | PASS |
| G1 | parquet `heat_rate`(2500) vs eGRID-2023 `PLHTRT`/1000 | 8.800451481 vs 8.800451481, rel Δ **0.0** | ≤ 1e-5 | PASS |
| G1 | `PLHTIAN`/`PLNGENAN` vs `PLHTRT` | rel Δ **1.2e-8** | ≤ 1e-5 | PASS |

**So nyiso-183 §8's "second term" is closed: the CC/ST split is the dict.** A
pure plant-grain join produces one number per plant; the dict lifts one class
of one plant off it. The three properties PREREG §1 recorded stand on the
evidence: a rule-24 per-plant dict (the sibling of the `_FLEET_GROUP_OVERRIDE`
nyiso-177 removed from this plant); a rule-21 free value (assumed CFs — CC
0.6 / steam 0.15 on 222 MW / 1,725 MW puts 66 % of the energy on the steam;
CAMPD 2023 puts 31 %: 883 GWh steam against 1,966 GWh combined cycle); and no
vintage — the same 9.5 in 2019 and 2050, failing rule 13's forward test as
written.

### 2.1 Disclosed instrument repair (the §8 standard: record, repair, never move a bar)

**G1 read FAILED on the first run and the record is preserved**
(`_nyiso184_heat_rate_basis_prefix_g1unit.json`): the probe divided
`PLHTIAN`/`PLNGENAN` — already MMBtu/MWh — by 1,000 a second time and compared
0.0088 against 8.80. The bar (1e-5 relative) is untouched; the statistic was
computed in the wrong unit. The same run reported the CC base through the
`ST_GAS` committed multiplier (7.9204 ÷ 1.05 = 7.54); the CC multiplier is
0.90 (`_NYISO_OFFER_CURVE`), and 7.9204 ÷ 0.90 = 8.8004. Both were fixed
before any gate below G1 was read; the probe `return`s on a G1 failure, so
nothing downstream had been scored.

---

## 3. G2 — the family construction is grounded at the plant on two legs and MISSES the third

**R1 as pre-registered:** for a plant hosting ≥ 2 prime-mover families
(`ST` = {ST}; `CC` = {CT, CA, CS, CC}; `GT` = {GT, IC}) each with `HTIAN` > 0
and `GENNTAN` > 0 in the applied vintage, each family takes
Σ`UNT23.HTIAN` ÷ Σ`GEN23.GENNTAN` over its own codes — the same eGRID-2023
workbook, sheets and window the plant join reads. Zero free parameters.

| plant | family | 2023 family rate | plant `PLHTRT` | Δ |
|---|---|---|---|---|
| **2500 Ravenswood** | **ST** | **12.2918** | 8.8005 | **+3.49** (vs the dict's 9.5: **+2.79**) |
| 2500 Ravenswood | CC | 7.3499 | 8.8005 | −1.45 |

The heat side is **exact**: eGRID's steam-family `HTIAN` 9,736,334 MMBtu equals
CAMPD's 2023 heat input over units 10 / 20 / 30 to 2.5e-9 (the post-hoc
`factor_heat_boundary` = 1.0000). The construction differs from the meter only
on the DENOMINATOR (EIA-923 net vs CAMPD gross) and on the HOURS (annual vs
running).

| leg | statistic | measured | bar | verdict |
|---|---|---|---|---|
| G2a | inside the join's window | 12.29 | [3, 30] | HOLDS |
| G2b | ≥ CAMPD-2023 steam-only gross running-hour HR | 12.29 ≥ 10.707 | ≥ | HOLDS |
| **G2c** | `r` = eGRID rate the model carries ÷ CAMPD running-hour HR, Ravenswood inside the eight peers' `[min, max]` | **1.148** vs **[1.059, 1.121]** | inside | **FAILS by 0.027** |

The peers' range, computed and printed before Ravenswood's value:

| peer | eGRID plant rate | CAMPD running HR | `r` |
|---|---|---|---|
| 2625 Bowline Point | 10.186 | 9.618 | 1.059 |
| 2527 Greenidge | 10.486 | 9.829 | 1.067 |
| 2516 Northport | 10.887 | 10.101 | 1.078 |
| 2490 Arthur Kill | 11.268 | 10.429 | 1.081 |
| 2517 Port Jefferson | 12.015 | 10.910 | 1.101 |
| 8006 Roseton | 10.950 | 9.781 | 1.120 |
| 2480 Danskammer | 11.282 | 10.069 | 1.121 |
| 2511 E F Barrett | 11.076 | 9.883 | 1.121 |
| **2500 Ravenswood under R1** | **12.292** | **10.707** | **1.148** |
| *(2500 under the incumbent 9.5)* | *9.500* | *10.707* | *0.887* |

**G2 does not fire. PREREG §6 S2 fires: no solve is spent and R1 is not
proposed.** The bar is not moved, and the two asymmetries in the statistic
both cut in Ravenswood's FAVOUR, so the miss is robust rather than an artifact
of construction: the peers' `r` uses their plant rate, which their own peaking
GTs inflate above their steam family (Barrett's steam family reads 10.571
against a plant 11.076, so on a family basis its `r` would be 1.070, not 1.121,
and the band would be narrower); and the statistic's heat side is identical
between the two sources.

### 3.1 POST-HOC locator — WHERE the 0.027 lives (no bar, not scored, written after the gate was read)

`r` factorises exactly into three terms, each from committed bytes:

```
r = [CAMPD all-hours HR / CAMPD running-hour HR]   annual-vs-loaded
  × [eGRID HTIAN / CAMPD heat]                      heat boundary
  × [CAMPD gross MWh / eGRID GENNTAN]               gross-to-net
```

| plant | annual ÷ loaded | heat boundary | gross ÷ net | net ÷ gross |
|---|---|---|---|---|
| **2500 Ravenswood ST** | 1.029 | **1.0000** | **1.115** | **0.897** |
| 2500 Ravenswood CC | — | — | 1.029 | 0.971 |
| 2625 Bowline | 1.015 | 1.000 | 1.043 | 0.959 |
| 2527 Greenidge | 1.001 | 1.000 | 1.066 | 0.938 |
| 2516 Northport | 1.007 | 1.000 | 1.070 | 0.934 |
| 2490 Arthur Kill | 1.008 | 1.001 | 1.071 | 0.934 |
| 2480 Danskammer | 1.071 | 1.000 | 1.047 | 0.956 |
| 8006 Roseton | 1.034 | 1.000 | 1.083 | 0.923 |
| 2517 / 2511 | 1.019 / 1.002 | 1.18 / 1.15 *(plant heat includes the GTs)* | 0.91 / 0.97 *(plant net includes the GTs)* | — |

Ravenswood's annual-vs-loaded factor (1.029) is ordinary — Roseton and
Danskammer, the other low-CF plants, read 1.034 and 1.071. **The whole excess
is the gross-to-net leg**, and at generator grain it is ONE machine:

| eGRID generator ↔ CAMPD unit | MW | 2023 CAMPD gross GWh | EIA-923 net ÷ CAMPD gross |
|---|---|---|---|
| gen 1 ↔ unit 10 | 364.5 | 281.7 | 0.913 |
| gen 2 ↔ unit 20 | 375.2 | 226.2 | 0.933 |
| **gen 3 ↔ unit 30** | **985.1** | **375.5** | **0.862** |

At 0.862, unit 30 reports 13.8 % of its gross as station use, against 6.7–8.7 %
for its sisters and 4–8 % for every peer. Its 2023 capacity factor is 4.2 %
(1,218 running hours), so ~7,500 idle hours of a large unit's house load are
charged against 375 GWh of output — the same EIA-923 convention every peer
carries, amplified by this unit's size and idleness. **The per-vintage
companion record says the same thing without being asked**: the steam family
rate runs **11.47 (2018, 1,979 GWh net) → 11.84 → 12.06 → 12.57 (2021, 445 GWh)
→ 12.50 → 12.29 → 12.06**, i.e. it rises as the steam's generation falls,
which is what an idle-load-inflated annual rate does and what a loaded heat
rate does not.

**What this does and does not say.** It says the eGRID family rate is a
correct read of eGRID and that eGRID's steam denominator at Ravenswood carries
a low-CF house-load effect that the eight peers carry less of. It does NOT say
12.29 is the wrong number — that is the class's basis, and the C1-2023 object
would be dispatched against it exactly as every peer is. It does NOT license
this session to re-anchor the bar: the peers' band was a real, pre-declared,
like-for-like test; it was missed; and the reason found afterwards is data,
not a mis-attribution of the kind nyiso-183 §8 repaired. A successor that
wants to test the construction against a bar that separates the loaded rate
from the idle-load effect must pre-register that bar before reading these
numbers again — they are all in the JSON.

---

## 4. G3 — ASTORIA IS A MEASURED-SIDE ARTIFACT: two objects, decided ex ante and confirmed

PREREG §2 decided before measurement that Ravenswood and Astoria are not one
object: Ravenswood's meter is ordinary and its model is the artifact; Astoria's
model (eGRID 11.949) is ordinary and its "meter" is the known CAMPD
stack-duplicate double count (`campd.CAMPD_STACK_DUPLICATE_UNITS`, nyiso-141,
three independent channels). nyiso-183's `measured_hr` and `stgas_units` read
the raw parquet without `merge_stack_duplicate_units` / `stack_duplicate_mask`,
so each RH/SH half carried the boiler's FULL gross against HALF its heat; the
"heat-recovery halves" description in nyiso-183 §6.1 was a misreading — they
are boiler monitoring paths and they ARE the plant's `ST_GAS` units.

| year | model HR | measured, raw halves | **measured, merged** | ratio raw | **ratio merged** | peer cluster | inside |
|---|---|---|---|---|---|---|---|
| 2023 | 18.677 | 5.550 | **11.007** (20: 12.99, 31RH: 10.82, 51RH: 11.12) | 3.365 | **1.697** | [1.636, 1.749] | **yes** |
| 2024 | 18.677 | 5.464 | **10.881** (13.58 / 10.86 / 10.86) | 3.419 | **1.717** | [1.604, 1.745] | **yes** |
| 2025 | 18.677 | 5.393 | **10.604** (13.11 / 10.68 / 10.38) | 3.464 | **1.761** | [1.596, 1.749] | no (+0.012) |

**G3 FIRES (2 of 3; bar ≥ 2).** Merged, Astoria's boilers read 10.4–11.1 gross
— exactly the NYISO gas-steam band nyiso-141 §2 published (10.4–10.8) — and
its model-to-meter ratio sits in the middle of the class. **There is no
model-side Astoria heat-rate object, and Astoria is NOT a contributor to the
other-ten-plant deficit through its heat rate.** The 3.4× outlier nyiso-183
handed forward was an instrument population artifact and is CLOSED.

### 4.1 G3b — the SAME artifact inside the merit-order guard's evidence: SIZED, NOT REPAIRED (§5 F4)

`scripts/lib/outage_detect.build_merit_order_panel` reads the CAMPD parquets
with `pd.read_parquet` and never calls the stack-duplicate helpers (code read,
PREREG §0 B), so the guard prices Astoria's SRMC on the halved rate: panel HR
**5.55** against a merged **11.01** in 2023, i.e. its SRMC at roughly half its
physical value. Astoria is NOT absent from the keeper's extract — the earlier
id-column check in this session's brief was wrong — it carries **281 rows /
7,412.8 window-days** in `campd-unit-outages-perunitmerit-NYISO.csv` and **70
rows / 3,434.1 days** in the `-layup-` companion. A unit that looks half as
expensive as it is looks IN merit more often, so fewer of its dead spans clear
the guard's `MERIT_OOM_FRAC` bar and more remain booked as mechanical
outages. Direction: Astoria's keeper availability is BIASED LOW by the
artifact. Magnitude on the extract is not computed here — it needs the panel
re-run with the merge, which is the outage-derive lane's object (nyiso-183
closed the availability route; PREREG §5 F4 forbids repairing it here). **The
repair is one call site**: apply `merge_stack_duplicate_units` and
`stack_duplicate_mask` in `build_merit_order_panel`'s loader, as
`campd._normalize_campd` and `curate_emissions_unit_annual` already do — and
it is solve-affecting (it re-derives the keeper's outage extract), so it needs
its own A/B on that lane.

---

## 5. G4 — the footprint of the one generic rule, enumerated with no LP

Under the 2023 vintage the predicate covers **7 NYISO plants / 15 (plant,
family) rows, 14 applied** (Northport's 8-MWh GT family is out of window and
not applied). At generator grain, armed against the keeper's own flag set, the
flag moves **24 generator rows at 7 plants, 6,238 MW**, and the off path is
byte-identical (460 generators, every `heat_rate` equal before and after an
armed load; G0 passed on the modified code with the flag off):

| plant | family | rows moved | MW | incumbent → family rate | note |
|---|---|---|---|---|---|
| **2500 Ravenswood** | **ST** | 3 | 1,724.8 | **9.500 → 12.292** | the object |
| 2500 Ravenswood | CC | 2 | 222.2 | 8.800 → 7.350 | the other half of the same blend |
| 2511 E F Barrett | ST | 2 | 372.2 | 11.076 → 10.571 | the GTs' inefficiency leaves the steam |
| 2517 Port Jefferson | ST | 2 | 385.0 | 12.015 → 12.364 | |
| 2517 Port Jefferson | GT | 1 | 12.9 | 12.015 → 10.408 | a `GT1` row with no class (not `CT_PEAKER`), so `measured_ct_heat_rates` does not reach it |
| 2490 Arthur Kill | ST | 2 | 876.6 | 11.268 → 11.262 | |
| 2516 Northport | ST | 4 | 1,592.2 | 10.887 → 10.886 | |
| 8906 Astoria | ST | 3 | 923.2 | 11.949 → 11.944 | |
| 50292 Bethpage | CC | 5 | 129.0 | 9.818 → 9.559 | |
| 2511 / 2517 / 50292 | GT | 0 | — | — | `CT_PEAKER` rows keep `measured_ct_heat_rates` precedence, as pre-declared |

The applied set reaches (2500, ST), so S3 does not fire. Every other move is
≤ 0.5 MMBtu/MWh and is the honest consequence of one rule, not a target.

---

## 6. What was built, and its exact status

**Shipped, DEFAULT-OFF, byte-identical off, UNARMED, matrix cell `O`:**

* `ScenarioConfig.egrid_family_heat_rates: bool = False` (+ the two cache-key
  registries), CLI `--egrid-family-heat-rates` on `run_calibration.py` and
  `run_calibration_full.py`, composed onto `--replay-bundle` so a future arm is
  the keeper's recorded recipe plus exactly this field.
* `fleet/models.py::EGRID_PRIME_MOVER_FAMILIES` / `egrid_prime_mover_family`;
  `fleet/eia860.py::egrid_family_heat_rates_for` / `_apply_egrid_family_heat_rates`
  at the eGRID-input seam of `_rows_to_generators` (right after the boundary
  repair, so `measured_ct_heat_rates` / `measured_chp_heat_rates` /
  `egrid_identity_heat_rates` keep their precedence unchanged);
  `_correct_mixed_facility_steam_hr(generators, skip_plants)` skips covered
  plants (rule 19 — superseded, never stacked; empty while off).
* `process_eia860.EGRID_HR_WINDOW_BTU_KWH` — the join's inline 3,000–30,000
  window named once and shared with the derive (rule 5; behaviour identical).
* `scripts/data/derive_egrid_family_heat_rates.py` → the NYISO artifact and
  its per-vintage companion; `tests/unit/data/test_egrid_family_heat_rates.py`
  (family map, reader, frame apply, the rule-19 hand-off, artifact invariants).

**Why it is shipped although G2 did not fire, stated plainly:** the code
replaces a rule-24 per-plant dict and a rule-21 hand value with a measured
construction, is off by default with the off path proved identical, and is
the instrument the successor needs. It is the nyiso-175b class (repaired in
code, validated at artifact level, shipped default-off as a companion) with
one difference recorded on its cell: **a pre-registered grounding leg was
missed**, so it is `O`, not a candidate. CAISO's 315 / 335 dict entries are
untouched (§5 F7); their retirement under this construction is CAISO's lane.

---

## 7. Honest expected value — what is NOT delivered

* **No repair is proposed, no arm was solved, no run is registered, and the
  C1-2023 gate is not moved.** S2 fired on its own terms.
* **The bar that failed was mine, it was tight (eight plants, one vintage),
  and I do not know a priori that it was right** — but it was pre-declared,
  like-for-like, and its two asymmetries favour the plant that failed it. It
  stays failed.
* **G2c's miss decomposes to one EIA-923 number** (unit 30 net ÷ gross 0.862).
  Whether that is an attribution defect in the source or real idle-period
  house load is not decidable from the artifacts in this repository; the
  per-vintage record and the sister units say "real", but that is post-hoc.
* **G3b is sized, not repaired.** The guard's Astoria SRMC is halved; the
  consequence on the extract's 281 rows is not quantified here.
* **My first G1 read was a unit error** and my first G0 CC base used the
  wrong multiplier; both preserved and disclosed (§2.1); no bar touched.
* **My brief's "Astoria has zero extract rows" was wrong** (an id-column grep
  on a name-first CSV); corrected in §4.1.

---

## 8. Governance

* **Rule 1 `[R-STRUCT]`** — no residual consulted; the repair form was fixed
  before any measurement and was NOT proposed when its own consistency gate
  failed, whatever it would have done to C1-2023.
* **Rule 5 / 21 / 23** — zero parameters: every constant read at its
  committed value; the one new constant (`EGRID_HR_WINDOW_BTU_KWH`) is the
  join's own inline pair, named. The derive reads eGRID and EIA-860 only.
* **Rule 13 `[R-MEASURED]`** — the CAMPD meter DIAGNOSES (G2b, G2c, G3); the
  construction reads published eGRID fields, regenerates for any vintage,
  responds to changed conditions, and pins nothing.
* **Rule 14 `[R-ACCURATE]`** — §2 is this rule pointing at a hand value that
  was silently compensating; §3 is the accurate construction, held back only
  by its own pre-declared bar.
* **Rule 15** — zero solves; nothing to register.
* **Rule 16 / 12** — every measurement spans 2023–2025; no solve, no year loop.
* **Rule 19 `[R-ONE-MECH]`** — §2 from the code, then G0/G1 on data; the
  construction supersedes the dict at covered plants and never stacks.
* **Rule 22 `[R-HOLDOUT]`** — 2023 / 2024 / 2025 only; NYISO absent from
  `complete` and `final`; no marker requested; the freeze untouched.
* **Rule 24 `[R-REGISTRY]`** — one registered boolean; no env var; no
  per-plant dict added (the existing one is superseded where covered, not
  edited; §5 F1).
* **Rule 25 / 28** — NYISO shard edited for verdicts; the required `U` cell
  line added in every shard and the base row added (28c); `check_mechanism_matrix.py`
  clean (line anchors re-fixed mechanically after the field insertion).
* **Rule 27 `[R-PUSH]`** — every source file edited locally and pushed as
  its on-disk bytes; ≥300-line files blob-verified after push (§10).
* **Tests** — see §10.

## 9. Matrix (rule 28 duty b) and the §5.5 queue

NYISO shard: `egrid_family_heat_rates` → **`O`** (built default-off; G0/G1/G2a/
G2b/G3/G4 pass, G2c missed by 0.027, the miss localised to unit 30's net/gross);
`offer_curve_by_group` annotated (the open object's two terms named and
proved; Astoria closed; the incumbent dict identified); `campd_outage_merit_order_guard`
annotated (G3b: the panel prices Astoria on the halved rate; 281 / 70 rows;
handed to the outage-derive lane). Other shards: `U`. The §5.5 lever queue is
rewritten with the prior queue preserved beneath.

## 10. Verification

**Tests:** `tests/unit` + `tests/iso/nyiso` with the new field in place —
**4,492 passed, 28 skipped, 1 xfailed, 200 subtests passed, 0 failed**
(8 min 39 s). The 4 `test_export.py` environment failures nyiso-177 §9 /
nyiso-183 §10 recorded do not appear because the `confirmed-retirements`
clean partition was regenerated before the run, as before. Lint: `ruff check`
and `ruff format --check` clean on every edited file;
`scripts/check_mechanism_matrix.py --base origin/main` clean (integrity, gap
ratchet, shared ratchet). Off-path identity:
460 NYISO generators byte-equal before and after an armed load (§5). Pushed
blobs of every ≥300-line file compared to local by line count and hash.

**Side effect, disclosed:** `data/clean/` regenerated for
`capacity-deliverability`, `nyiso-interface-flows`, `confirmed-retirements`
(gitignored, derived). `frontend/data/parameters.json` +
`docs/parameter-citations.md` regenerated by `generate_parameter_registry.py`
for the new field.

## 11. Handed forward

1. **The 9.50 is `MIXED_FACILITY_STEAM_HR[2500]`, a hand number with assumed
   CFs, lifting eGRID-2023's plant-grain 8.80.** Both proved as identities.
   The C1-2023 object is this dict and this join; nothing else in the offer
   path sets the base.
2. **The family construction exists, default-off, and reads 12.29 for the
   steam.** Do not re-run G2c as written and expect a different answer; the
   numbers are in the JSON. A successor may pre-register a bar that separates
   the loaded rate from the idle-load denominator effect (e.g. `r` on the
   gross-to-net leg compared per UNIT against the class's per-unit
   distribution, or a CAMPD-heat / EIA-923-net-per-unit construction) — before
   reading them again.
3. **Astoria is CLOSED as a heat-rate object** (G3, 2 of 3). Its measured HR
   is 10.4–11.1 merged. Any instrument that reads NYISO CAMPD at unit grain
   must apply `merge_stack_duplicate_units` + `stack_duplicate_mask`;
   nyiso-183's G4c/G4d helpers did not.
4. **The merit-order guard's panel does not either (G3b)** — a one-call-site
   fix on the outage-derive lane, solve-affecting, own A/B; Astoria carries
   281 extract rows / 70 lay-up rows on the keeper.
5. **Expected consequence of arming R1, unchanged from PREREG §4 G5 and
   untested:** Ravenswood `ST_GAS` volume falls in every year; 2024 / 2025
   `ST_GAS` deepen (the other ten plants are −6.776 / −7.957 TWh short); its
   `CC_REGULAR` rises; no price claim.
6. **UNCHANGED and not opened:** C3a-2025 (owner-court); C3c; the D-2 / C8
   grain under-count (scorer lane); the availability route (DO-NOT-REDO);
   CAISO's 315 / 335 dict entries.
