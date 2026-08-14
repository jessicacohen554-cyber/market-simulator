# FINDING — miso-157: the chartered share is **NOT ADJUDICATED** (its two measured comparators disagree), and the session instead root-caused a **DIFFERENT, LARGER DEFECT**: MISO's entire 108.7 GW thermal fleet is stamped **one vintage, 2010**, by an **ERCOT-only registry**

**Session** miso-157 · **ISO** MISO · **Date** 2026-08-14 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**PREREG** `results/calibration/PREREG-miso157-ct-summer-wefor-share-2026-08-14.md`,
pushed at **`09b7c87`**, blob **`84091bdf`**, **verified byte-identical against
the FETCHED remote ref** before any adjudicating statistic was computed
(rule 27 `[R-PUSH]`).

**NO SOLVE. NO RUN REGISTERED. NO `ScenarioConfig` FIELD ADDED. NO CELL VERDICT
MINTED. KEEPER UNCHANGED.** Rule 15 `[R-DASHBOARD]` is not engaged — no backcast
run was produced. No mechanism was armed or tested, so the miso-142/153
precedent applies and no matrix cell moves; the MISO shard's §5.4 queue stamp is
updated under rule 28(b).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds **neither**
`complete` nor `final`. No holdout year was read, solved, scored or registered.

**BRANCH TAKEN: B-DISAGREE** (PREREG §6) — and **B-ARM independently fails its
own condition**, so the no-lever outcome rests on two grounds, not one.

---

## 1. Headline

**The charter's object is not adjudicated, and I will not pretend otherwise.**
`SUMMER_WEFOR_SHARE = 0.30` removes 70 % of `CT_PEAKER`'s forced-outage rate
from Jun–Sep. Measured against MISO's own published outage record it looks
**wrong** (the record's unplanned buckets run *above* annual in summer);
measured against MISO's own CAMPD per-unit extract it looks **right** (0.62–0.75).
The two measured comparators differ by **0.487 / 0.346 / 0.362** against a
pre-registered 0.25 bar. That is the miso-87 Ground-1 signature, and the PREREG
turned it into a kill gate precisely so this session could not argue past it.

**What the session did establish, and it is bigger than the lever it was
looking for.** Chasing a clean constant (trap T-3) produced a root-caused,
measured input defect on the price-setting class:

| | model | measured (EIA-860, **100.0 %** coverage) |
|---|---|---|
| `CT_PEAKER` cap-wt online year | **2010** | **1998.7** |
| cap-wt age (2025) | 15 | **26.3** |
| capacity past the age-20 escalation onset | **0.000 GW (0.0 %)** | **18.86 GW (84.6 %)** |
| cap-wt WEFOR | **0.0700** | **0.0929** (**×1.33**) |
| cap-wt performance DERATE | **0.0500** | **0.0653** |

**Every plant-group-tagged thermal row in MISO's fleet — 108.70 GW across 7
classes and 527 plants — carries exactly one `online_year`, 2010.** The cause is
not a data gap. `_commission_year` (`data/fleet/assembly.py:280-285`) looks each
plant up in `master-plant-registry.csv` and falls through to a hardcoded
`return 2010` on a miss; that registry is **833 rows, `ba_code = 'ERCO'` for all
833**, so MISO's 527 plant codes intersect it at **zero** and the fall-through is
total. The consequence is that **the entire age-escalation limb of
`THERMAL_AVAILABILITY` is identically inert for MISO — 0.000 GW past onset in
every class, in every training year.**

Direction, stated plainly: the defect makes MISO's thermal fleet **younger,
more available, and cheaper to keep online than it is** — and it lands hardest
on `CT_PEAKER`, the class that sets MISO's summer peak price. It is not a fix
for C3a (§6 sizes it), but it is exactly the kind of input error rule 14
`[R-ACCURATE]` exists to catch.

---

## 2. Validity gates — all run BEFORE any adjudicating statistic, and one FIRED

| gate | result |
|---|---|
| **V1** — reproduce miso-153's published D-1/D-2 | **PASS 3/3, after S-V1 fired and was debugged** (§3). CT_PEAKER Jun+Jul cap-wt availability **0.9234 / 0.9261 / 0.9195** against the published 0.923 / 0.926 / 0.919 (Δ **0.0004 / 0.0001 / 0.0005** against a ±0.02 bar); top-200 available **93.28 / 92.41 / 89.09 GW** against the published 93.28 / 92.41 / 89.09 (**+0.005 %** every year) |
| **V2** — the keeper's own fleet | **PASS 3/3.** `n_gen` **2929 / 2923 / 2923**; carry zones **6** |
| **V3** — the measured record's own internal identity | **PASS 3/3.** `MISO_<cause>` = North+Central+South to **0.000 MW** on every day of every year; rows **365 / 366 / 365** |
| **V4** — `weather_year` pinned per solve year | **PASS 3/3** (`dataclasses.replace`; V1 is its control) |

---

## 3. S-V1 fired — the defect was **MINE**, and it is disclosed rather than quietly repaired

On its first run the V1 GW leg read **111.56 / 110.76 / 106.95 GW** against
miso-153's published 93.28 / 92.41 / 89.09 — **+19.60 / +19.86 / +20.04 %**. Per
the PREREG's instruction the session stopped, debugged and quoted no
adjudicating statistic until it was resolved.

**The uniformity of the offset is what identified it** — a defect that lands
within 0.45 pp of +20 % in three independent years is a scope difference, not
noise. It was: my aggregate summed `availcap` over the **whole** fleet, pulling
in the 872 blank-`plant_group` rows (nuclear/VRE, ~15.8 GW) and hydro (~2.4 GW).
miso-153's D-1 is scoped to the classes carrying a `THERMAL_AVAILABILITY` entry.
On the corrected scope the gate reproduces D-1 **exactly, 3/3, to +0.005 %**.

**Reported against interest: the reconstruction was right and my instrument was
wrong.** Three further cross-checks agree — CT availcap **20.509 / 20.519 /
20.161 GW** reproduces miso-153's published idle 14.18 / 12.90 / 11.25 GW at its
published 69.2 / 62.9 / 55.8 % shares. The mis-scoped figure is kept in the
committed record (`top200_avail_gw_ALL_FLEET_misscoped`) rather than deleted.

---

## 4. Leg 1 — the shape, at full magnitude, all three years and both windows

`R` ≡ Jun–Sep mean unavailability ÷ annual mean, on the model's own partition
(`_SUMMER_MONTHS = {6,7,8,9}`). The model's implied share is **0.30**.

| year | `R_mod` non-floor | `R_mod` floor | `R_meas^MISO` composite | `R_meas^MISO` **Derated-only** | `R_meas^CAMPD` covered |
|---|---|---|---|---|---|
| 2023 | **0.539** | 1.036 | **1.104** | **1.261** | **0.617** |
| 2024 | **0.545** | 1.036 | **0.967** | **1.237** | **0.622** |
| 2025 | **0.556** | 1.188 | **1.109** | **1.174** | **0.746** |

Jun+Jul (T-29, reported and never substituted for the adjudicating window):
`R_mod` 0.545 / 0.535 / 0.581 · `R_meas^MISO` 1.065 / 0.991 / 1.165 ·
Derated-only 1.261 / 1.227 / 1.207 · `R_meas^CAMPD` 0.576 / 0.575 / 0.715.

**The MISO record separates planned from unplanned exactly as physical
scheduling requires**, which is a strong internal validation of it — 2025 bucket
ratios: `Planned` **0.658** (work moved *out* of summer), against `Derated`
**1.174**, `Forced` **1.073**, `Unplanned` **1.083** (all *above* annual). The
model already puts POF in the shoulder only, matching the 0.658. What
`SUMMER_WEFOR_SHARE` additionally does is apply the **same planned-outage logic
to the FORCED rate**, and on this record the forced buckets do not behave that
way.

**But CAMPD says the opposite, and the PREREG forbids waiving it** (§5).

---

## 5. The branch — B-DISAGREE, and B-ARM fails independently

| year | \|`R_meas^MISO` − `R_meas^CAMPD`\| | B-DISAGREE (> 0.25) | B-ARM needs `R_CAMPD` ≥ 0.90 | ΔMW (B-INERT < 0.5 GW) |
|---|---|---|---|---|
| 2023 | **0.487** | **FIRES** | **FAILS** (0.617) | 1.241 GW — silent |
| 2024 | **0.346** | **FIRES** | **FAILS** (0.622) | 1.030 GW — silent |
| 2025 | **0.362** | **FIRES** | **FAILS** (0.746) | 1.248 GW — silent |

Under the pre-registered precedence (**B-DISAGREE > B-INERT > B-SUPPORTED >
B-ARM**) the session takes **B-DISAGREE: no lever, no solve, nothing armed.**
B-ARM additionally fails on its own stated condition in all three years, so the
outcome does not depend on the precedence rule.

**S-PHANTOM fired** in 2023 and 2024 (`R_CAMPD` 0.617 / 0.622 < 0.70) and was
silent in 2025 (0.746). Its pre-registered instruction is explicit that
B-DISAGREE is *"evaluated on that basis rather than waived"* — I wrote that
clause to stop exactly the move I would otherwise be tempted to make here, and
it binds.

**The evidence bearing on which comparator is biased is reported, and it is not
a resolution.** CAMPD's detector books economic idleness as mechanical outage
(`FINDING-ercot79-phantom-outage-2026-07.md`), and MISO's CC and coal are
economically idle in the **shoulder**, which depresses a summer ÷ annual ratio.
The per-class gradient is consistent with that pre-declared direction:
`CC_REGULAR` **0.267 / 0.434 / 0.558** (the most economically cycled class, the
lowest ratio) against `ST_GAS` **0.861 / 0.866 / 0.833** and `ST_CHP`
**0.887 / 0.783 / 0.939** (rarely cycled, close to 1). That is an *explanation*
of the disagreement, **not** a demonstration that the MISO record is right, and
this session does not treat it as one.

---

## 6. Leg 2 — the reach, and why the charter could not have closed C3a anyway

ΔMW is the `CT_PEAKER` summer capability the share moves, at the top-200
Jun–Sep demand hours (200 / 196 / 200 of the top-200 hours fall in Jun–Sep):

| year | ΔMW | vs D-1 cushion within $20/MWh | vs total CT idle | on the **true** WEFOR (§7) |
|---|---|---|---|---|
| 2023 | **+1.241 GW** | 16.0 % of 7.74 GW | 8.8 % of 14.18 GW | 1.560 GW |
| 2024 | **+1.030 GW** | 13.6 % of 7.56 GW | 8.0 % of 12.90 GW | 1.330 GW |
| 2025 | **+1.248 GW** | 19.8 % of 6.31 GW | 11.1 % of 11.25 GW | **1.657 GW** |

**T-27 PASSES** — the counterfactual is a pure seasonal reallocation, annual-mean
availability invariant to **3.2e−18 / 0.0 / 3.2e−18** against a 1e−6 bar. So the
mechanism is the one claimed, not a disguised level change.

**§5.4's pre-registered honesty holds up.** The PREREG registered, before
measuring, that this lever *"closes on the order of a tenth of the gap and
cannot close C3a"*. Measured: it reaches **19.8 %** of the 2025 cushion, i.e.
about a fifth of the CT block sitting within $20/MWh of the clearing price. That
would have been worth arming under rule 1 `[R-STRUCT]` — a parameter with no
source governing the price-setting class — and it would **not** have been a C3a
fix. The point is moot; the comparators disagree.

---

## 7. S-AGE fired, and it produced the session's durable result

**The trigger.** Cap-weighted `CT_PEAKER` WEFOR came back as **exactly 0.0700**
in all three years while the fleet aged 13 → 14 → 15. Under T-3 an exact
constant gets a second derivation rather than an explanation, and the second
derivation is what follows. **This is the third consecutive MISO session in
which "disbelieve clean zeros" has been the instrument that found the defect**
(miso-155's `min_gen` 733/733 at 0.0; miso-156's floors-OFF 27-cell zero).

**The measurement** (probe function `s_age_true_vintage`, EIA-860
`vintage_2024`, capacity-weighted per plant, **100.0 % coverage of CT capacity
in every year**):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| true cap-wt online year | 1998.7 | 1998.7 | 1998.7 |
| true cap-wt age vs model | **24.3 vs 13** | **25.3 vs 14** | **26.3 vs 15** |
| capacity past age-20 onset, true | **17.08 GW (76.7 %)** | **18.08 GW (81.1 %)** | **18.86 GW (84.6 %)** |
| capacity past onset, **model** | **0.000 GW** | **0.000 GW** | **0.000 GW** |
| cap-wt WEFOR true / model | 0.0880 / 0.0700 (**×1.257**) | 0.0904 / 0.0700 (**×1.292**) | 0.0929 / 0.0700 (**×1.327**) |
| cap-wt DERATE true / model | 0.0620 / 0.0500 | 0.0636 / 0.0500 | 0.0653 / 0.0500 |

**The blast radius inside MISO** (2025 census, committed in the record):

| class | rows | GW | distinct `online_year` |
|---|---|---|---|
| COAL | 446 | 42.79 | **1** (2010) |
| CC_REGULAR | 333 | 27.42 | **1** (2010) |
| CT_PEAKER | 733 | 22.28 | **1** (2010) |
| ST_GAS | 115 | 10.99 | **1** (2010) |
| CC_CHP | 64 | 3.62 | **1** (2010) |
| CT_CHP | 114 | 0.90 | **1** (2010) |
| ST_CHP | 86 | 0.70 | **1** (2010) |
| *(blank plant_group)* | 872 | 16.66 | 84 (1932–2024) |

**108.70 GW on one vintage.** The blank-`plant_group` rows carry a real
distribution because they reach `online_year` through the EIA-860 loader, not
through `_commission_year` — so the data exists in the repo and only the
plant-group/binned path misses it.

**Why it matters here and not only in the abstract.** The DERATE leg is **flat
year-round**, so unlike the chartered share this is *not* a seasonal
reallocation: correcting the vintage lowers CT availability in **every hour,
including the summer peak**. Sized on the model's own arrays, the vintage defect
alone overstates summer CT capability by **0.388 / 0.440 / 0.493 GW**, and it
scales the chartered share-lever's own reach by 1.26–1.33× (§6, last column).

**Rule 25 `[R-ISO-SCOPE]`, both ways.** The registry is ERCOT-only, so **every
non-ERCOT ISO on this code path is exposed** — but the magnitude is **measured
for MISO only** and **no verdict transfers**. Each lane must measure its own.
This is flagged to the owner in §9 as a cross-ISO governance item, not fixed
here: it is a different mechanism from the chartered one (rule 19
`[R-ONE-MECH]`) and it writes `src/market_sim/`, so it needs its own charter.

---

## 8. Priors and triggers, scored

| prior | registered | measured | verdict |
|---|---|---|---|
| **P-1** `R_mod` | 0.40 – 0.65, centre **0.55** | **0.539 / 0.545 / 0.556** | **CONFIRMED.** The PREREG's derived arithmetic (0.548) predicted 2025 to within **0.008** |
| **P-2** `R_meas^MISO` | 1.00 – 1.35, centre 1.15 | **1.104 / 0.967 / 1.109** | **2 of 3 inside; 2024 falls BELOW the band.** A miss, reported as one |
| **P-3** `R_meas^CAMPD` | 0.55 – 1.05, centre 0.80 | **0.617 / 0.622 / 0.746** | **CONFIRMED 3/3**, at the low end, in the direction pre-declared as hostile |
| **P-4** ΔMW 2025 | 1.0 – 3.0 GW, centre **1.9** | **1.248 GW** | Inside the band but at its **bottom**; the centre was **too high** |
| **P-5** floor-population share | 5 – 30 %, centre 15 % | **1.0 %** (0.23 of 22.28 GW) | **BELOW the band — a miss.** It cuts *for* the charter (the object owns 99 % of CT), which is why it is stated as a miss rather than a finding |

**Triggers: S-V1 FIRED** (§3, my own defect, disclosed). **S-AGE FIRED** (§7, the
session's main result). **S-PHANTOM FIRED** 2023/2024 and did **not** waive
B-DISAGREE (§5). **S-FLOORPOP silent** (1.0 % vs a 40 % bar). **S-DERATE-SPLIT
silent, narrowly** — the composite and `Derated`-only ratios differ by
0.157 / **0.270** / 0.065 against a 0.30 bar, so 2024 came within 0.03 of firing;
reported because it nearly did. **S-REACH not evaluated** (no solve).

---

## 9. Traps — every counter-measurement, at full magnitude

| # | Counter-measurement | Result |
|---|---|---|
| **T-1** | Bundle repointed and asserted | **PASS** — `_miso134.BUNDLE` → `miso148_basis_B`, asserted at import |
| **T-2** | Zero 3-argument `getattr(` | **PASS** — count **0**. The two candidates (`online_year`) were replaced by direct attribute access after confirming `Generator.online_year` is a required `int` (`fleet/__init__.py:172`) read the same way by the production branch (`arrays.py:676-677`), so a rename fails loudly. `ruff` clean |
| **T-3** | **Disbelieve clean zeros** | **PASS, AND IT PAID FOR THE THIRD SESSION RUNNING** — the exact 0.0700 was refused and its second derivation produced §7 |
| **T-4** | Production types only | **PASS** — every array from `generators_to_fleet_arrays`; no `SimpleNamespace` |
| **T-5** | `MISO_external*` are IMPORT NODES | **PASS** — carry zones asserted **== 6** |
| **T-6** | CAMPD derate keyed on `config.weather_year` | **PASS** — `dataclasses.replace(cfg, weather_year=y)` per solve year, asserted; V1's 3/3 is its control |
| **T-7** | An inert instrument looks like a fix | **PASS** — every channel reported in **GW**, not only as a ratio |
| **T-8** | Production functions, never re-implementations | **PASS** — `generators_to_fleet_arrays.__module__` asserted |
| **T-24** | `ct_floor_plants` take a different branch | **PASS** — populations split and reported separately: **719 non-floor / 14 floor**, floor = **1.0 %** of CT capacity, `R_mod` floor 1.036 / 1.036 / 1.188 vs non-floor 0.539 / 0.545 / 0.556 (visibly a different branch, as predicted) |
| **T-25** | The MISO record is whole-fleet | **COUNTER-MEASURED** — the `Derated`-only ratio (physically ambient/thermal) is reported beside the composite in every year; S-DERATE-SPLIT silent at 0.270 max |
| **T-26** | CT CAMPD coverage is a cited clean zero | **PASS, RE-DERIVED INDEPENDENTLY** — **0 CT_PEAKER windows** in `campd-unit-outages-MISO.csv`; classes present are `CC_CHP, CC_REGULAR, COAL, CT_CHP, ST_CHP, ST_GAS`. **A correction to miso-87 falls out:** it recorded CT_PEAKER **and CT_CHP** (25.0 GW) at 0.000, but `CT_CHP` **is** covered — 291 windows, 1,263 MW annual mean. The zero is CT_PEAKER's alone |
| **T-27** | A share change that also moves the level | **PASS** — annual-mean availability invariant to **3.2e−18 / 0.0 / 3.2e−18** |
| **T-28** | The 0.30 is a global constant | **PASS, VACUOUSLY** — nothing was armed and `SUMMER_WEFOR_SHARE` was not edited |
| **T-29** | Jun–Sep vs Jun+Jul window shopping | **PASS** — both reported for every ratio in every year; the model-partition figure adjudicates, as fixed in the PREREG |

---

## 10. Where this leaves the lane

**Established, and a successor should not re-derive it:**

1. **The chartered object is UNRESOLVED, not refuted and not confirmed.**
   `SUMMER_WEFOR_SHARE = 0.30` is contradicted by MISO's published record
   (unplanned buckets all > 1 in summer; `Derated`-only **1.17–1.26** in all
   three years) and supported by MISO's CAMPD extract (**0.62–0.75**). Resolving
   which comparator is admissible for a *forced-outage seasonal shape* is the
   successor question, and it is a **data-provenance** question, not a lever.
2. **`CT_PEAKER` has NO measured outage coverage in MISO at all** — 0 windows,
   re-derived independently of miso-87 (whose 25.0 GW figure is corrected: CT_CHP
   *is* covered; the hole is CT_PEAKER's 22.28 GW alone).
3. **MISO's whole plant-group-tagged thermal fleet carries one vintage, 2010**,
   from an ERCOT-only registry, and the age-escalation limb of
   `THERMAL_AVAILABILITY` is therefore **dead for MISO** (§7). Measured against
   EIA-860 at 100 % coverage.
4. The chartered lever's reach is **~20 % of the 2025 CT cushion** and could
   never have closed C3a — as the PREREG registered before measuring.

**Rule 20 `[R-DOF]` posture, unchanged and now sharper.** `SUMMER_WEFOR_SHARE`
remains in the keeper's DOF ledger under identification `residual`. This session
tried to retire it against measurement and **could not**, so it stays an open
root-cause issue — which is the correct ledger state, not a failure of the
attempt.

**Two items go to the owner (§11), neither taken here.**

---

## 11. For the owner — two decisions this session prepared and did not take

1. **The vintage defect (`_commission_year` → hardcoded 2010).** A rule-14
   `[R-ACCURATE]` / rule-5 `[R-NO-MAGIC]` input error with a measured
   replacement in hand (EIA-860, 100 % coverage) and **zero free parameters** —
   it *removes* a magic literal rather than adding a knob. But it writes
   `src/market_sim/data/fleet/assembly.py`, it is a **gated availability
   change**, it is a **different mechanism** from the chartered one (rule 19),
   and the registry being ERCOT-only means **five other ISOs are exposed with
   unmeasured magnitude** (rule 25 — no verdict transfers). It needs its own
   charter, its own pre-registration, and a cross-ISO impact decision. **Direction
   is against the current keeper's fit in the shoulder and for it at the peak,
   and it must not be adopted on that basis** (rule 1 `[R-STRUCT]`).
2. **Which measured record is admissible for a forced-outage seasonal shape**
   (§5). MISO's published record is ISO-official but whole-fleet; CAMPD is
   class-resolved but carries the documented phantom-outage bias. Until that is
   settled, no `SUMMER_WEFOR_SHARE` charter can clear its own kill gate — this
   session's B-DISAGREE is the proof.

*(miso-156's two open items are unchanged except that the owner **blessed the
gated production-engine floor rebuild** as canonical this session, closing its
item 2. Its item 1 — the P0 commitment sidecar — is untouched.)*

---

**Artifacts.** Probe `scripts/probes/_miso157_ct_summer_wefor.py` (`ruff` clean,
zero 3-arg `getattr`). Record
`results/calibration/_miso157_ct_summer_wefor.json`. PREREG `09b7c87`, blob
`84091bdf`. Keeper `2026-08-09-miso-148-basis-aware`, **unchanged**.
