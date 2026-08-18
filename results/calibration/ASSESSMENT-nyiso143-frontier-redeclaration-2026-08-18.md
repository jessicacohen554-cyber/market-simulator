# ASSESSMENT — nyiso-143: can NYISO's frontier be RE-DECLARED?

**Session:** nyiso-143, 2026-08-18 · **Branch:** `claude/nyiso-frontier-redeclaration-191c6i`
**Keeper:** `2026-08-17-nyiso-142-stackdup`, determination **`CALIBRATED`** (rubric v3.3)
**Markers:** `complete` HELD · `final` **EMPTY** · **holdout spend freeze ACTIVE**
**Years touched:** 2023 / 2024 / 2025 only. No out-of-training year was solved, scored or registered.

---

## 0. THE ANSWER

> ### NOT YET FRONTIER. Two of the five open objects are CLOSED this session; three remain OPEN, and one of them was open in a way nobody knew.

Frontier is the owner's declaration that *"we have tested everything we could
have"*. It cannot stand while a named, admissible, untested object is open.
After this session:

| # | object | status after nyiso-143 |
|---|---|---|
| 1 | chartered Zone-K reconciliation | **PRE-REGISTERED, SOLVED, REGISTERED — and ESCALATED.** All six gates PASS, including the K6′ that replaced the K6 which killed it; the arm is still not promotable, on a **discovery** rather than a fit result (§1) |
| 2 | D-4 per-unit conduct rider | **CLOSED — BUILT, VALIDATED, SHIPPED.** And it immediately found a live defect on the keeper (§2) |
| 3 | `nyiso_incity_commitment_obligation` | **OPEN — and newly BLOCKED** on an unidentified coefficient (§3) |
| 4 | `nyiso_synchronised_reserve` | **OPEN. The ground for closing it is FALSIFIED** (§3) — this is the object nobody knew was open |
| 5 | `nyiso_iroquois_winter_spread` | **OPEN** (owner question, unchanged) **+ governance defect CONFIRMED and FILED** (§4) |
| — | *new*: the nyiso-140 membership repair is **INCOMPLETE** — the gas commitment bridge still floors Port Jefferson (34.6 % of its 2024 ST_GAS forcing) | **NEW OPEN OBJECT**, surfaced by object 2 (§2.3) |
| — | *new*: the model's **entire** downstate scarcity formation is the Zone-K import bound | **NEW OPEN OBJECT**, surfaced by object 1 (§1.4) |

The honest summary is that the queue did not shrink by three. It shrank by
two and **grew by three**, because the two instruments this session was asked to
build — the conduct rider and the Zone-K A/B — are what found them. That is the
gates working, not the lane regressing.

---

## 1. OBJECT 1 — the chartered Zone-K reconciliation

### 1.1 The "joint" mechanism does not exist any more, and that is an owner decision, not a session judgement

The charter (D1 **GRANTED** 2026-08-16) asked for the mainland→Zone-K transfer
bound and the downstate ST_GAS `min_gen` floor reconciled as **one** mechanism
under rule 19 `[R-ONE-MECH]`. Three subsequent owner-level facts collapsed it:

1. The floor limb the card paired with the bound (`Long_Island:ST_GAS:tmax:LI_ST_ev`,
   HB14-21) **was already disabled** on the keeper by `NYISO_PEAK_WINDOW_FLOORS_OFF`
   — the card's literal arm is a floor-side no-op (nyiso-139b §2).
2. The live limb's **window is correct**; its **membership** was the defect
   (owner, nyiso-140 §6.1).
3. The owner then **ordered the two apart** — *"STANDALONE ARM FIRST, then
   Zone-K … the transfer bound and this floor are **not one phenomenon**"*
   (nyiso-140 §6.2).

So the "re-scoped 24-hour base" half of the writable arm **already landed**, as
`2026-08-16-nyiso-140-layup-exclusion`, and it is inside the control. What
remained to adjudicate was the transfer bound alone.

### 1.2 Why that is not the forbidden re-test

`nyiso_li_tsl_n11_security` is `R`, killed on K6 at nyiso-130, and rule 28(a)
forbids re-testing an `R` cell **without new evidence**. Three things are new,
each independently sufficient:

* **the control changed** — post-nyiso-140 membership repair (which removed the
  plant absorbing 72.6 % of the very floor K6 fired on) and post-nyiso-142
  benchmark correction;
* **the gate changed** — K6 → **K6′**, owner-adopted at nyiso-140 §6.3
  *precisely because* K6 "cannot adjudicate any import-relief lever";
* **K6′ leg (a) became non-vacuous** — this session's D-4 conduct rider.

Pre-registration: `results/calibration/PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md`,
written and committed **before** either solve was launched.

### 1.2b THE RESULT — all six gates pass, and the arm is still not promotable

Full record: `results/calibration/RESULT-nyiso143-zone-k-transfer-bound-ab-2026-08-18.md`.
Both arms solved 2023/2024/2025 in one bundle and **both registered** (rule 15):
`2026-08-18-nyiso-143-control` and `2026-08-18-nyiso-143-n11tsl-arm`.

**K1-K5 silent, and K6′ SILENT — the gate that killed nyiso-130 clears it.**
The forced shares rose exactly as pre-registered (downstate
`reliability_floor × ST_GAS` 0.169→0.185, 0.190→0.222, 0.123→0.138); bare K6
fires on any rise, K6′ escalated and cleared both legs — **zero new D-4
failures** in the arm (it *removes* three) and **zero new D-1 misses**.

| year | C3c model → (actual, band) | C3a | at-bound share in-window | LI AC import TWh |
|---|---|---|---|---|
| 2023 | **21 → 2 h** (10, [5, 20]) | +9.6 % → **+9.0 %** | 0.845 → **0.248** | 3.392 → 4.563 |
| 2024 | **3 → 0 h** (13, [6, 26]) | +1.6 % → +1.9 % | 0.876 → **0.213** | 3.383 → 4.791 |
| 2025 | **24 → 5 h** (42, [21, 84]) | −2.5 % → −2.3 % | 0.711 → **0.068** | 2.599 → 3.321 |

C1 / C2 / C3a / C3b / C4 / C8 PASS in both; mean LMP moves ≤ $0.26/MWh and 2023
C3a *improves*. **C3c is the whole story and it goes the wrong way:** the
control misses two years and **passes 2025**; the arm misses all three and
takes 2025 PASS → FAIL.

The control is itself a validation: replaying the keeper's own recipe at this
HEAD reproduces **C3c 21 / 3 / 24 bit-identically**.

### 1.4 THE DISCOVERY — the model's entire downstate scarcity IS this bound

**100 % of the model's C3c tail hours are Long_Island, in both arms and every
year.** NYISO's modelled scarcity pricing is the Zone-K import bound binding in
84.5 / 87.6 / 71.1 % of its design-condition hours; swap in the published
number and occupancy falls to 24.8 / 21.3 / 6.8 % and the scarcity goes with
it. **The model has no other downstate scarcity mechanism** — the rule 14
`[R-ACCURATE]` "the estimate was silently compensating" signature, and the same
object nyiso-110 named from the reserve side and nyiso-124 located as a
downstate price-formation gap.

**So the arm is NOT rejected on fit — rule 1 `[R-STRUCT]` forbids that**, and
the identification is published with zero DOF. It is a **rule 22 D-5(b)
escalation** with two defensible readings: (A) rule 14 literal — arm the
accurate number now and open the scarcity mechanism as the discovered root
cause, at the cost of a 3-of-3 C3c miss and NOT-YET; or (B) sequencing — build
the scarcity mechanism first so the accurate input does not land on a
representation left emptier than it started. **Session recommendation: B, as a
recommendation and not a verdict.** The A/B is DONE and must not be re-solved;
what is open is the ruling. Cell `nyiso_li_tsl_n11_security`: **`R` → `O`**.

### 1.3 One thing the pre-registration had to decide, and flags for the owner

K6′ leg (a) requires that every binding mechanism *"**still** binds only inside
its driver-justified window"*. **"Still" is ambiguous between absolute and
arm-vs-control**, and this session is what makes the ambiguity bite: before the
conduct rider, leg (a) could never fire at all. The pre-registration declares
the **delta** reading (a mechanism failing in *both* arms is pre-existing and
does not kill the arm) and says so in advance, because under the absolute
reading leg (a) would kill **every** NYISO arm until the separate Danskammer
defect (§2.3) is repaired — plainly not what was adopted. **If the owner
overturns that reading, the A/B result must be discarded, not re-interpreted.**

---

## 2. OBJECT 2 — the D-4 per-unit conduct rider: BUILT, VALIDATED, CLOSED

### 2.1 What was wrong

D-4 measures floored MWh falling outside a mechanism's declared window. For a
mechanism whose declared window is **all 24 hours**, `offwindow_share` is
`0.0` **by construction** — it cannot fail. **Every one of NYISO's six D-4 rows
declares `h0-23`**, so D-4 had *zero* discriminating power on this ISO, while
K6′ leg (a) and rule 20 `[R-FORCED-BUDGET]`'s grounded-above-budget escalation
both rest on it. A gate that cannot fail is not a gate, and frontier cannot be
claimed while the lane relies on one.

### 2.2 What was built (owner-adopted at nyiso-140 §5/§6.3, implemented here)

`scripts/legitimacy_diagnostics.py::run_d4` now emits, for all-hours windows
only, a **per-unit conduct row** per floored plant: the plant fails provenance
when **its own measured (CAMPD bench) median hourly output over the hours the
floor actually binds for it is exactly zero** — the meter says it is offline in
at least half the hours the floor asserts it must be online.

* **Threshold-free.** "Median exactly zero" carries no fitted constant (rule 5
  `[R-NO-MAGIC]`, rule 21 `[R-DOF]`); materiality reuses the module's existing
  `D2_FLOOR_MIN_MW`.
* **Measured on the plant's BINDING hours, not the whole window.** An earlier
  window-wide draft produced three false positives on NYISO's own fleet
  (Bowline Point 2625, Roseton 8006 and Danskammer 2480 all sit under the
  `Capital_Hudson × ST_GAS` **tmax 31.1 °C** limb, which lives inside an
  `h0-23` *declared* window but binds only on design-cooling hours). Scoring
  binding hours cleared 2625 and 8006 — median 372-472 MW in their 220-250
  binding hours — and is both the faithful reading of the adopted wording and
  the only one that cannot manufacture a false positive out of a driver-gated
  limb. This is recorded because the first draft was wrong, not because it was
  right.
* **Never fails for a missing meter.** Hydro / nuclear / renewables /
  interchange pseudo-units carry no measured series; they are skipped and
  disclosed by count (125 / 123 / 4 rows).
* **Bounded blast radius, verified in code.** `calibration_verdict._d4_provenance`
  is called from exactly **one** site — the C8 above-cap escalation branch. A
  conduct failure therefore changes a *scored determination* only for a class
  already **above** its forced-share cap. No committed bundle is re-scored
  until its own lane regenerates; NYISO's C8 is under cap in every year, so
  **no determination moves.**
* **Forward-compatible for every consumer.** Both checks share the `rows` list
  and the mechanism's own `floor` label — which is what lets
  `_d4_provenance` pick conduct failures up with **no change to its matching
  rule** — and are discriminated by a new `check` field
  (`"window"` / `"unit-conduct"`). A pre-rider artifact has no `check` key and
  is read as `"window"`, so **every committed bundle re-scores exactly as
  before**. Surveyed the other seven readers of `D4.rows` (six per-run probes
  plus the cross-ISO `_xiso3_forced_share_d4_census.py`): all read committed
  artifacts, none sums `floored_twh` across rows, and the census's
  window-consistency check passes conduct rows unchanged because they carry the
  same window string. A consumer that ever *does* want energy totals should
  filter `check == "window"`.
* 8 new unit tests (`tests/scoring/test_legitimacy_diagnostics.py::TestD4PerUnitConductRider`);
  full `tests/scoring/` = 1,030 passed, and the 5 pre-existing failures
  (`test_ff_readiness_battery`, `test_crossover_harness` — forecast lane) were
  confirmed present on a stashed tree, i.e. not caused here.

### 2.3 It works in both directions — and it found something

Both bundles reconstructed identically at this HEAD:

| bundle | plant | year | floored | binding h | measured median | of them at zero | verdict |
|---|---|---|---:|---:|---:|---:|---|
| `nyiso140_control` (**pre**-repair) | **2517 Port Jefferson** | 2023 | 0.5530 TWh (19.8 %) | 7,401 | **0.000 MW** | 70.5 % | **FAIL** |
| | | 2024 | 0.5269 TWh (18.5 %) | 6,500 | **0.000 MW** | 71.4 % | **FAIL** |
| | | 2025 | 0.5637 TWh (24.0 %) | 7,080 | **0.000 MW** | 64.5 % | **FAIL** |
| **keeper** `…nyiso-142-stackdup` (**post**-repair) | 2517 | — | *absent from every row* | | | | **cleared** |

So the rider **independently reproduces nyiso-140's finding through the new
gate** — it would have caught Port Jefferson — and **clears** on the repair.
That is the validation in both directions.

**One more guard the full-dispatch run forced, recorded because the first
version was wrong.** Plants carrying the benchmark's own **CT-only CEMS flag**
(`ct_only`: EIA-923 net > 1.1× CAMPD gross, so the *benchmark* scores them on
EIA-923 **monthly** because the hourly CAMPD series is incomplete) are excluded
— a zero median in a series the benchmark itself declines to trust is a
metering artifact, not conduct (rule 14 `[R-ACCURATE]`). Without it the rider
convicted five such plants. Rows whose dispatch is **substituted** by their own
floor (pjm-149 / caiso-155) are excluded for the same reason: their at-floor
set is the whole floor-positive set by construction, so a verdict on them would
be "indeterminate on a fail".

**NEW OPEN OBJECT — the nyiso-140 membership repair is INCOMPLETE, and in a
bigger way than a single small plant.** Run on the full-dispatch bundles rather
than the payload, the rider shows `reliability_floor_plant_exclusions` fixed
**one mechanism, not the plant**:

| year | mechanism | plant | floored | share of mechanism | binding h | measured median | at zero |
|---|---|---|---:|---:|---:|---:|---:|
| 2024 | `nyiso_gas_commitment_bridge × ST_GAS` | **2517 Port Jefferson** | 0.1495 TWh | **34.6 %** | 4,623 | **0.000 MW** | 71.2 % |
| 2025 | `nyiso_gas_commitment_bridge × ST_GAS` | **2517 Port Jefferson** | 0.0529 TWh | 11.9 % | 1,568 | **0.000 MW** | 50.3 % |
| 2025 | `nyiso_gas_commitment_bridge × CC_REGULAR` | 7314 | 0.0819 TWh | 11.4 % | 2,360 | **0.000 MW** | 80.3 % |
| 2023–25 | bridge × ST_GAS **and** `reliability_floor × ST_GAS` | **2480 Danskammer** | 0.0010–0.0140 TWh | 0.0–4.4 % | 24–1,641 | **0.000 MW** | 90.7–100 % |
| 2025 (arm) | `nyiso_gas_commitment_bridge × ST_GAS` | 8006 Roseton | 0.1881 TWh | 44.9 % | 1,714 | **0.000 MW** | 60.9 % |

**The exclusion channel exists only on the reliability floor.** The gas
commitment bridge has no membership exclusion, so the very plant nyiso-140
identified as economically laid up is still floored — by the *other* mechanism,
for a THIRD of everything that bridge leg forces in 2024. This is rule 19
`[R-ONE-MECH]`'s "enumerate what already floors the same class" working exactly
as intended, one mechanism later. It is a named successor with its own
identification and its own A/B; **not repaired here**, present identically in
both Zone-K arms, and declared in the Zone-K pre-registration §5 so it cannot be
misread as that arm's doing.

*(The pre-registration and this section's first draft named only 2480
Danskammer, from a payload-based run that covered 100 plants and substituted
127. The full-dispatch numbers above supersede that figure; the Danskammer row
survives, it is simply the smallest of the set.)*

---

## 3. OBJECTS 3 AND 4 — the reserve family: the closing argument is FALSIFIED

Full record: `results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md`.
No solve spent.

The handoff expected `nyiso_synchronised_reserve` to be closable on the
matrix's standing argument that it is *"a construction of exactly the class-2
online-gate family nyiso-110 measured EXHAUSTED … an AGGREGATE rho\*output row
that reserve-eligible hydro's own 2-5 GW keeps slack in every hour"*.

**The class-2 headroom row is PER-ZONE, not aggregate** (`model/lp/reserve_rows.py`:
`R[c,z] - rho * sum_{elig g in z} P[g] <= 0`). nyiso-110's inert arm gated the
**published NYCA/East** families, whose zone masks let upstate hydro in. This
flag adds `nyc_spin_online`, masked to **NYC alone** — and NYISO has **no NYC
hydro**. The verdict was read across two structurally different zone masks.

Measured on the keeper's own committed dispatch, against the 250 MW static
requirement (`0.5 × nyc_10min_total`):

| year | NYC quick-start min | `rho*` for inertness | binding hours at the ACTUAL `rho` | worst deficit |
|---|---:|---:|---:|---:|
| 2023 | 79.1 MW | 3.1588 | **7,911 (90.3 %)** | 170.9 MW |
| 2024 | 86.3 MW | 2.8981 | **7,159 (81.7 %)** | 163.7 MW |
| 2025 | 82.9 MW | 3.0152 | **4,669 (53.3 %)** | 167.1 MW |

**And the actual `rho` is not measured at all.** Its declared identification —
the fleet's own cap-weighted `(pmax−pmin)/pmin`, *"a fleet property … not a
tuned coefficient"* — is guarded by `valid = (pmin > 0) & (pmax > pmin)`, and on
the keeper's fleet **only 4 of 851 / 849 / 705 LP rows carry `pmin > 0` at all**
(the nuclear block), **none of them quick-start eligible**. Under
`plant_level_fleet` + `use_campd_bins`, must-run rides `min_gen`, not `pmin`.
So the identification is **dead code for this ISO** and the value that decides
the mechanism is the literal `1.0` in the `else:` branch — in every year, in
**both** the path-A branch and the rule-19 sibling's obligation branch
(451 / 443 / 299 rows, 0 valid).

**A mechanism that is provably inert at `rho ≥ 3.16` and binds in 90 % of hours
at `rho = 1.0`, on a coefficient that is never measured, has a free parameter
in disguise** (rule 21 `[R-DOF]`, rule 5 `[R-NO-MAGIC]`). Both flags stay `U`.
This is a root-cause finding, not a rejection: the downstate 10-minute
requirement genuinely *is* an online-gated obligation. What is missing is a
measured 10-minute-headroom-per-MW-online statistic, derived under rule 23
`[R-FROZEN-DERIVE]` from source data. One identification unblocks the pair, and
the hard `ValueError` means only one of them may ever be armed.

`nyiso_spin_reserve_online` keeps its `I` — untouched, and explained rather
than contradicted. Nothing here re-opens `diurnal_price_amplitude` (`G`).

---

## 4. OBJECT 5 — `nyiso_iroquois_winter_spread`: the taxonomy gap is REAL, CONFIRMED, and FILED

Two separate things, deliberately kept apart:

**(a) The arming decision is an OWNER question and stays one.** Arming it would
improve a measured input (the flat annual allocation mis-states the winter
physics of a Connecticut trading point inside the New England complex, rule 14
`[R-ACCURATE]`) while **degrading C3a-2025** — a rule 22 D-5(b) escalation, not
a session decision. Untouched here.

**(b) The governance defect is confirmed by measurement.** It is a
solve-affecting `ScenarioConfig` field (`scenarios.py:4640`, cache-key
registered at `:13264`, with its own CLI flag `--nyiso-iroquois-winter-spread`)
that has **0 cells in all six ISO shards** and appears **only** in prose — 3
mentions in `mechanism-matrix.js`, of which the load-bearing one is inside the
`def:` head of the *sibling* row `gas_hub_basis_overlay`.

The consequences are exactly the class ercot-177 filed:

* `scripts/check_mechanism_matrix.py` **passes** (mention-anywhere: registration, not taxonomy);
* `scripts/mechanism_matrix_gap_sweep.py --iso NYISO` reports **0 prose-only**,
  because `coverage()` returns `own_row` for any field named in a row's `def`
  head — so the census cannot see it either;
* NYISO's cell on that row reads **`K`**, which asserts a verdict about the
  *overlay* (armed, keeper) while the winter-spread scalar is **OFF and OPEN**.
  One character cannot carry two booleans with different statuses.

**Remediation, specified but NOT executed here.** The ercot-177 precedent is
**two rows**: give `nyiso_iroquois_winter_spread` its own base row plus one
cell line in **every** shard (NYISO `O`; the other five `.` — the field is
NYISO-gated and unreachable elsewhere). That is a base-file + all-six-shards
edit, the one deliberately non-parallel edit rule 28(c) describes, and it is
**out of a single-ISO lane's scope** — this session edits only NYISO's shard.
Filed for a governance round, with a second item worth folding in: a
`check_mechanism_matrix.py` leg asserting that every solve-affecting field
resolves to a row **whose cell it owns**, not merely to a row that *mentions*
it. That leg would have caught both this and ercot-177's case.

---

## 5. `complete` / `final` — RE-VERIFIED AT HEAD, and one leg of the record is CORRECTED

`complete` is held and needs nothing. **No `final` grant is proposed.**
nyiso-142 job 2's NOT-READY verdict **STANDS**, re-verified here on its three
load-bearing legs:

| leg | nyiso-142 claim | re-verified at HEAD |
|---|---|---|
| 2019 fleet not representable | Indian Point 2/3 absent from every `eia860_generator*.parquet` | **STANDS** — 0 matching rows across all vintages (2022/2023/2024, operable + proposed + retired) |
| 2019 cannot discriminate on C3c | 1 actual RT hour > $300, max $372.38 | **STANDS, bit-identical** — mean $24.96, max $372.38, **1 h**; the least discriminating year in the record (2022: 101 h; 2025: 42 h; H1-2026: 85 h) |
| H1-2026 unsolvable | *"`load_demand` raises: no EIA-930 rows for 2026"* | **THIS HALF IS FALSIFIED AT HEAD.** `data/raw/eia-930/EIA930_BALANCE_2026_Jan_Jun.parquet` carries **4,343 NYIS rows**, 2026-01-01 01:00 → 2026-07-01 00:00 — exactly the covered span the assessment itself quotes for C3c |

**The conclusion is unchanged and the correction does not soften it.**
H1-2026 remains unsolvable on the frozen keeper config for the *other* reason
that assessment gave: the keeper arms `nyiso_dynamic_reserve_requirements`,
whose loader **raises rather than falling back**, and
`data/raw/NYISO-AS/requirements/` carries `NYISO_reserve_requirements_{2022,
2023,2024,2025}.csv` — **four files, re-counted this session** — against a
published LRR schedule with a genuine gap (v2021 ends 2026-02-14, v2026 starts
2026-07-10). Closing that needs an adjudicated mid-year splice: a methodology
decision about the frozen config's inputs, taken *after* the config was
selected, which is precisely what a touch-once test cannot absorb.

One reinforcing fact this session adds: **`data/raw/lmp-data/NYISO/` holds no
2019 file at all**, so 2019 could not be zonally scored even if it could be
solved.

And independently: the **holdout spend freeze is `active: true`**, which
outranks both marker blocks, so a `final` grant would be unspendable today
regardless.

---

## 6. WHAT WOULD CLOSE THE REMAINING QUEUE

1. **The Zone-K ruling** (§1.4) — reading A or reading B, under rule 22 D-5(b).
   The A/B is done, registered and must not be re-solved; what is open is the
   ruling. Plus an owner ruling on K6′ leg (a)'s absolute-vs-delta reading,
   which the pre-registration declared in advance and this run is scored on.
2. **The downstate scarcity mechanism** — the root cause §1.4 uncovers, and the
   thing reading B says must exist before the accurate bound is armed. Same
   object nyiso-110 named from the reserve side and nyiso-124 located as a
   downstate price-formation gap.
3. **`rho` identification** for the online-gated reserve class — a measured
   10-minute headroom per MW online, from CAMPD ramp conduct or NYISO's
   published capability data, under rule 23. Unblocks objects 3 **and** 4 (only
   one may be armed).
4. **A membership-exclusion channel on `nyiso_gas_commitment_bridge`** (§2.3) —
   it still floors Port Jefferson for a third of its 2024 ST_GAS forcing, plus
   7314, 8006 and Danskammer. Its own identification and A/B.
5. **`nyiso_iroquois_winter_spread`** — the owner's D-5(b) call, plus the
   two-row matrix remediation in a governance round.

**Not on this list, and not to be re-opened** (cite, do not re-litigate):
BLOCKER-A's topology split, **CLOSED AT G0 WITH CAUSE** at nyiso-124 — so
C3c's standing re-open condition is **falsified as written**, not pending;
BLOCKER-B, closed on **content** not access (nyiso-97, the MyNYISO wall);
BLOCKER-C, closed on **measurement** — the measured interface limits are
**looser** than the model's estimates; the cross-ISO queue, closed since
nyiso-122; queue items 1b / 2 / 3 / 5-12, adjudicated; the class-2 reserve
family's *measured* exhaustion (nyiso-110) — sound for the published NYCA/East
families, see §3; the commissioning curve (nyiso-133) and the fleet-CF
composition object (nyiso-136), both refuted ex ante.

**Out of lane:** the price-distribution compression (nyiso-109) is measured
**SYSTEMIC at all six ISOs** by xiso-1. It is not a NYISO queue item and is not
entered as one.
