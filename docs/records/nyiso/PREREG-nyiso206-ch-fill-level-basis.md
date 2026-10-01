# PREREG — nyiso-206: does `cheapest_first` deliver the physics that `floor_pct = commit_frac × min_stable_pct` asserts?

**Session:** nyiso-206, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-ruj0qb`, off `main` `4fa2a714`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — unchanged by this
session. **ZERO LP is budgeted and none is expected to be earned.**

Written **before any number of this session's object is read.** Numbers land in the FINDING and
in the decision card, not here.

---

## 1. The statements the charter requires this PREREG to carry

- **THERE ARE STILL NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0** on the keeper
  (grade 7/8); **C3c is the lone ledgered caveat**, is non-downgrading under rubric v3.3 / v3.6,
  and **is not an objective of this session**. No criterion is hunted. Nothing below is selected
  because a residual moved (rule 1 `[R-STRUCT]`). No metrics file, price series or volume
  residual is opened at any point.
- **THE OFFER-CURVE CHANNEL IS OWNER COURT AND IS NOT TAKEN.** The `offer_curve_by_group` band
  multipliers are the authorized price-tuning channel under rule 1's 2026-09-05 carve-out, whose
  condition (c) reserves them to the owner, set ex ante and never swept. This session does not
  touch them.
- **MARKERS ARE NOT MINE.** `complete` is WITHDRAWN (Q5, nyiso-192); `frontier` is withdrawn on
  the determination limb. Re-entry to either is an explicit **owner** act. Neither is edited,
  prepared, or treated as earned. Card **C-19 / Q51 stays PARKED**. Rule 22 `[R-HOLDOUT]`:
  **2023–2025 is the entire world of this session.**
- **`DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` §5/§5.1 stays UNRULED.** This session
  does not rule it and does not rely on a ruling of it.
- **DO-NOT-REDO is respected in full.** Not re-tested: the Capital_Hudson **membership** arm in
  either form (2480+8006, nyiso-204; 2480 alone, nyiso-204b); the **fill-order operator**
  question (`cheapest_first` vs `pro_rata`, nyiso-205 — `cheapest_first` CONFIRMED, `pro_rata`
  REFUTED on 9-of-9 g/a evidence plus a decisive rule-17 leg); the NYC limb's window, membership
  or operator (nyiso-203 §§3–5); Astoria 8906 membership; the whole-year lay-up census as a
  membership test for a seasonal limb; the duct-tranche lever; `nyiso_ct_peaker_bands_measured`;
  `cc_duct_peaking_row_scoped`. **No matrix cell marked `R`/`I`/`G` is re-tested.**
- **No third fill operator, and no hybrid, is sought.** nyiso-205 was chartered not to and did
  not; neither does this session. The object below is **not** a choice between operators.

## 2. The object — a construction question no session has asked, on the instrument the charter names

The charter names the **target level** (`floor_pct = 0.0973`) as the only instrument nyiso-204b
identified that remains unexamined, and rules that **taking** it unilaterally is not a lane's to
do: lowering it is a rule-23 `[R-FROZEN-DERIVE]` re-derivation with no source-data trigger, on a
coefficient identified over n = 65 observations of the whole class, whose only visible motive
would be the D-4 rows it removes. **This session does not take it, does not re-derive it, and
does not propose a value for it.**

What it does instead is ask the **prior** question, which is a construction audit rather than a
level choice, and which nobody has asked on this limb:

> **Does the delivery mechanism preserve the coefficient's own meaning?**

The coefficient's meaning is documented in the derive script that produced it
(`scripts/data/derive_reliability_coeffs.py`, module docstring), and it is a **per-unit physics
statement with a commitment count on top**:

- `min_stable_pct` (ST_GAS **0.12**, `constants.MIN_STABLE_PCT_PHYSICAL`, NREL WWSIS-2 Table 7)
  is *"the class's physical min-stable level (Pmin/Pmax) of a **committed unit**… the temperature
  gate reliability-commits a merchant unit on an extreme day; **once committed it sits at this
  physical Pmin**"*.
- `commit_frac` (**0.8105**) is *"the share of the class's nameplate that is online
  (grossLoad > 0) on temperature-flagged days — **a commitment count**"*.

So `floor_pct = 0.0973` asserts: *on a design cooling day, ~81 % of Capital_Hudson `ST_GAS`
nameplate is committed, and **each committed unit sits at 12 % of its own capacity**.*

The delivery mechanism is `model/interchange/core.py::_distribute_group_floor`, read here as
code before any measurement:

```python
target = frac * avail_cap.sum(axis=0)          # a ZONAL aggregate
for r in order:                                 # rows sorted by heat rate
    cap_r = pmax[r] * availability[r, :]
    take = np.minimum(remaining, cap_r)         # fill to FULL available capacity
    np.maximum(min_gen[r, :], take, out=...)
    remaining = remaining - take
```

The per-row cap in the fill is **`cap_r` — the row's full available capacity — not
`min_stable_pct × cap_r`.** `pro_rata`'s branch, by contrast, floors each row at
`frac × cap_r = 0.0973 × cap_r`, which is below `min_stable_pct = 0.12` for every row and so
never asserts more than the physics does.

**Therefore the two operators are NOT symmetric with respect to the coefficient's construction,
and that asymmetry is a separate fact from the one nyiso-205 adjudicated.** nyiso-205 asked
*which units carry the floor* and answered it on the meters (concentration on the cheapest,
confirmed 9-of-9). This session asks *at what level, relative to each row's own physical minimum
stable point, the floor is placed* — a question about the units the fill **reaches**, not about
which ones it reaches. **`cheapest_first` remains CONFIRMED and is not re-litigated;** a row-level
mismatch, if one is measured, would be a defect in the fill's per-row cap, not a reason to
revisit the ordering that nyiso-205 established. That distinction is stated here, before
measuring, so it cannot be blurred afterwards.

### 2.1 Why this is not a residual hunt, stated plainly

The audit's warrant is the derive script's own words against the kernel's own code — two
committed artifacts that can be compared with no reference to any output of the model. It is the
same class of audit nyiso-203 ran on the NYC limb (identified on daily means, applied hourly,
−0.0087, reported and not taken) and it is reported the same way: **at full magnitude, in both
directions, and not taken.** If the measurement comes back clean, that is a **clean negative and
a full result**, exactly as the charter says, and the session stops.

### 2.2 Why any repair is OWNER COURT and this lane may not take it (rule 25 `[R-ISO-SCOPE]`)

`_distribute_group_floor` is the **shared kernel for every ISO's `cheapest_first` limbs.**
nyiso-205's committed provenance census counted `cheapest_first` as the operator of **37 of 50**
live floor limbs program-wide (ERCOT 5/5, MISO 12/12, NEISO 6/6, PJM 14/14, all by dataclass
default). Capping the fill at a row's min-stable level would therefore move **five other ISOs'
protective mechanism at once** — precisely the situation `DECISION-CARD-nyiso193` describes for
`legitimacy_diagnostics.py` (*"one file scored for all six ISOs"*), and precisely what rule 25
forbids a single-ISO lane from doing. **This session writes the card and does not write the
patch.**

## 3. DOF status — declared before measuring

**Zero.** No `ScenarioConfig` field, no coefficient, no re-derivation, no CSV edit, no
`src/market_sim/` change. `floor_pct = 0.0973`, `commit_frac = 0.8105`, `min_stable_pct = 0.12`
and the `distribution` column are all read and none is written.

Declared for the card rather than for this session: **were the owner to rule that the fill's
per-row cap should be a row's min-stable level, that would add ZERO free parameters** — 0.12 is
already in the CSV, already a published WWSIS-2 physical constant, and already one of the two
factors of the very coefficient being delivered. That is a statement about the *shape* of a
possible ruling, not a recommendation, and the card will size its consequences in both
directions before it says anything else.

## 4. Phase 0 — the measurement, pre-registered (rule 29 `[R-SCREEN]` step 0, ZERO LP)

Taken on the limb's own binding window, reconstructed from the engine's own code path
(`iso_zone_tmax` → `tmax > 31.1 °C` → `_bridge_flagged_runs(min_event_hours = 48)`), which
`_nyiso204b_ch_exclusion_variants.py` and `_nyiso205_ch_fill_operator.py` both already reproduce
at **504 / 432 / 600 h** for 2023 / 2024 / 2025 — the count is re-verified before anything else
is computed, and a mismatch aborts the probe. Availability comes from the keeper bundle's own
`fleet_only` reconstruction (`reconstruct_bundle_fleet`, the path every nyiso-19x/20x phase 0
uses). The floor is produced by calling the **shipped** `_distribute_group_floor` kernel, never
re-implemented here.

For each year, over the limb's binding hours, on the LP rows of Capital_Hudson `ST_GAS`:

1. **The row-level intensity distribution.** For every (row, hour) cell the fill raises above
   `pmin`, the ratio **`i = floor / cap_r`** — the delivered floor as a share of that row's own
   available capacity. Reported as the share of raised cells at `i ≥ 0.999` (pinned at full
   availability), in `[0.12, 0.999)` (above min-stable but not pinned), and `< 0.12` (below
   min-stable), plus the cell-count-weighted and MW-weighted means.
2. **The same three bands measured in ENERGY**, not just in cells: forced MWh
   (`Σ max(0, floor − pmin)`) attributed to each band, so a rare-but-large band cannot hide
   behind a cell count and a frequent-but-tiny one cannot be inflated by it.
3. **Per plant and per row**, so the answer says *which* rows are pinned, not only how many.
4. **The `pro_rata` counterfactual on the SAME statistic** — reported for calibration of the
   scale only. It is arithmetically forced (`i ≡ 0.0973 < 0.12` for every raised row), so it is
   **not evidence**, and the FINDING will say so rather than presenting it as a result.
5. **The aggregate identity re-verified**: Σ delivered floor = `0.0973 × Σ cap_r` in every
   binding hour, to six decimals. If the aggregate does not hold, every intensity number is
   meaningless and the probe reports that instead.

**Robustness, pre-registered so it cannot be chosen after the fact.** Every band statistic is
reported over the same **three** hour sets nyiso-205 pre-registered — the bridged binding window
(the limb's own, and the one the verdict is read off), the unbridged `tmax > 31.1` flagged hours,
and the binding window narrowed to **h14–21**. A conclusion that survives only one cut is
reported as not surviving. All three years are reported separately; no year is pooled away.

## 5. The decision rule, fixed in advance

- **If the raised cells sit at or below `min_stable_pct`** — i.e. the fill never pins a row much
  above 0.12 of its own availability — then **`cheapest_first` delivers the coefficient's physics
  and the construction is SOUND AS BUILT.** That is a **CLEAN NEGATIVE and a FULL RESULT**: it is
  reported, no card is written on this leg, the session stops, and the target-level question is
  handed to the owner as the charter frames it, with the added fact that the delivery mechanism
  is not the confound.
- **If a material share of the forced ENERGY is delivered at `i ≥ 0.999`** — rows pinned at full
  available capacity — then the mechanism is asserting a must-run-at-full-output where the
  coefficient asserts a minimum-stable commitment, and **that is a construction gap of the
  nyiso-203 §6 class.** It is then **sized at full magnitude and written up as an OWNER DECISION
  CARD**, together with the target-level question the charter names, because the two are the same
  ruling seen from two sides: *what the number is* and *what the mechanism does with it*. **No
  arm is proposed, no patch is written, and no screen is run** (§2.2, rule 25).
- **In between** — raised above 0.12 but not pinned — the magnitude decides how much of the card
  is warranted, and the honest reading is stated as measured rather than rounded to either pole.
- **Phase 0 GATES the solve, and this session expects it to gate it to zero.** No screen year is
  pre-registered here, because no solve is earned: the only outcomes on the table are a clean
  negative and a card, and **neither is an arm.** Should that judgement prove wrong, a screen
  year would be pre-registered in an addendum **before** the screen runs, chosen by **the
  mechanism's own measured footprint** — never by residual size — and any screen bundle would be
  **never registered** and **deleted before merge** (rule 29(c)).

## 6. Rule 29(b) — G-DRIFT, and why no control solve is spent

The keeper's **committed bundle is the control** (G-CTRL form 4), and form 4's validity is
established **empirically, not by reading hunks**, exactly as the charter requires: re-running
`scripts/probes/nyiso198_rebuild_checks.py --year 2024` at this HEAD must leave `git diff`
**clean** — the committed `_nyiso198_rebuild_checks_2024.json` regenerating byte-identically off
the same `reconstruct_bundle_fleet` path every number in §4 comes from. The result is recorded in
the FINDING. *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198
duct-peaking gate for `cc_duct_peaking_row_scoped`, an `R` cell. It is part of the committed
record, is **not** a drift signal, and nothing here re-opens it.)*

In any case this session differences nothing against a solve, so no control solve could be owed.

## 7. What this session will not do

- Not take, re-derive, or propose a value for `floor_pct` (rule 23 — no source-data trigger).
- Not edit `_distribute_group_floor`, or any shared kernel, or any `src/market_sim/` file
  (rule 25 — five other ISOs ride it; §2.2).
- Not re-open the operator choice, the membership, or the NYC limb's window/membership/operator.
- Not touch `offer_curve_by_group`, any marker, any other ISO, or any other ISO's matrix shard.
- Not register anything on the dashboard — nothing will be solved, so there is no run (rule 15;
  git history and the FINDING are the record).
- Not fix the pre-existing HEAD test failures; they are measured and reported for the capx /
  FF-readiness / SCN-WS5A-LOAD lanes that own them (rule 25).

---

## Addendum §A — one counterfactual ADDED, before any number was read

§4 pre-registered two floors to compare: the shipped `cheapest_first` (the object) and
`pro_rata` (declared there as *not evidence*, because its intensity is arithmetically forced to
`0.0973 < 0.12` for every raised row). Writing the probe made clear that neither of them can
answer the question the card will have to put to the owner, which is not *"is the delivery
wrong"* but *"what would the coefficient's own construction have delivered instead, and at what
cost."*

A **third** floor is therefore added: the **min-stable-capped cheapest-first fill** — the same
merit-ordered fill with each row capped at `min_stable_pct × cap_r` instead of `cap_r`. This is
the fill the derive script's own words describe: *commit units in merit order, each at its
physical minimum stable level, until the zonal target is met.*

**It is declared here for three reasons and one of them is against interest.**

1. It is **always feasible** on this limb, and provably so before measuring: the target is
   `0.0973 × Σ cap`, the per-row caps sum to `0.12 × Σ cap`, and `0.0973 < 0.12`. So the
   counterfactual cannot fail for an arithmetic reason and cannot be reported as "infeasible"
   after the fact.
2. Its committed-capacity share is `floor_pct / min_stable_pct` **by construction** — which is
   `commit_frac = 0.8105`, the coefficient's own commitment count. That makes it a **closed-form
   prediction**, not a fitted alternative: the probe measures the realised share and the number
   it must land on was fixed here, before the run. A miss would be a defect in this reasoning,
   and would be reported as one.
3. **Against interest:** because it is a closed-form construction with zero free parameters and a
   pre-stated answer, it will look attractive, and the temptation to promote it from *sizing* to
   *proposal* is exactly what this addendum exists to foreclose. **It is NOT proposed, NOT
   screened, and NOT patched.** `_distribute_group_floor` is the shared kernel behind 37 of 50
   live limbs across five other ISOs (§2.2), so changing it is owner court under rule 25
   `[R-ISO-SCOPE]`, and its consequences for those ISOs are **unmeasured and will not be measured
   from this lane.** The card will say so at the top, not in a footnote.

**Timestamp discipline:** this addendum and the probe that computes the counterfactual are
committed in the same commit, **before the probe is executed for the first time.** No measurement
of this session's object existed when it was written.

---

## Addendum §B — a POST-HOC check added AFTER the primary measurement, and it can only hurt

**Declared as post-hoc, because it is.** §4 and addendum §A were fixed before the probe ran. This
one was not: it was added after reading the primary result, and the record says so rather than
presenting it as pre-registered.

**Why it is added.** The primary measurement came back showing the shipped fill delivers the
floor far above the coefficient's min-stable level, which makes the §A counterfactual look good.
That is exactly the moment to run the test that could destroy it. nyiso-205's **decisive** leg
against `pro_rata` was rule 17 `[R-FLOOR-WINDOW]`: `pro_rata` would have floored Danskammer 2480
in **100 % of binding hours** against a metered P(on) of 0.125 / 0.255 / 0.370, multiplying the
very D-4 off-window exposure the inquiry began from. **The §A counterfactual spreads the same
aggregate over more rows, so it is exposed to the identical objection**, and a card that sized it
without running that test would be advocacy, not measurement.

**What is added**, per plant, per year, on the limb's binding window, for **both** the shipped
`cheapest_first` fill and the §A min-stable-capped fill, from CAMPD unit-level hourly `grossLoad`
at plant grain — the same meter and the same statistic nyiso-205 used:

1. the count of binding hours in which the plant is floored at all, and its share of the window;
2. the plant's metered **P(on)** over the hours that fill floors it;
3. the **manufactured energy** `Σ max(0, floor − metered)` — nyiso-205's do-no-harm statistic.

**The decision rule for it, fixed before it is run.** If the min-stable-capped fill floors 2480
(or 8006) in a materially larger share of binding hours at a metered P(on) that says the unit is
off, then it **inherits `pro_rata`'s refutation** on rule 17, and **the card must lead with that**
— reporting it as a cost that may well be disqualifying, not as a footnote. A counterfactual that
fixes one construction defect by manufacturing a larger off-window one is not an improvement, and
this session will say so plainly if that is what the meters return.
