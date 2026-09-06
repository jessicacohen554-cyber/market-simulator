# FINDING — nyiso-205: `cheapest_first` is CONFIRMED for the Capital_Hudson `ST_GAS` hot step. A **clean negative** — the meters refute `pro_rata` in every year and every cut, and swapping the operator would make the rule-17 exposure **worse**

**Session:** nyiso-205, NYISO backcast calibration. **Branch:**
`claude/nyiso-capital-hudson-operator-chqu85`, rebased onto `main` `b22b91c3`. **Date:**
2026-09-06. **DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` —
**UNCHANGED**. Nothing promoted, nothing registered, no `ScenarioConfig` field, no CSV edit.

**ZERO LP WAS SPENT.** Rule 29 `[R-SCREEN]` step 0 did what it exists to do: the arm was killed
before it reached a solve. No screen year was pre-registered, because no solve was earned.

**PREREG:** `results/calibration/PREREG-nyiso205-ch-fill-operator.md` — committed and pushed
**before any number was read** (`375b3d9a`, since merged to `main`), including its addendum §A.
**Instrument:** `scripts/probes/_nyiso205_ch_fill_operator.py` →
`results/calibration/_nyiso205_ch_fill_operator.json`.

---

## 0. Verdict in one paragraph

The pre-registered question was whether `cheapest_first` — which the Capital_Hudson `ST_GAS`
`tmax 31.1` step runs only because its CSV `distribution` column is empty and it falls through to
the dataclass default — is the operator this limb's own market conduct supports. **It is.**
Measured on the limb's own binding window, the **cheapest** plant (Bowline 2625, HR 10.70) carries
a generation share **above** its available-capacity share in **9 of 9** year × cut cells
(g/a **1.19–2.01**), while **both** dearer plants carry **less** than their availability share in
**9 of 9** cells (Roseton 8006, HR 11.50: **0.51–0.85**; Danskammer 2480, HR 11.85:
**0.15–0.99**). `pro_rata`'s assertion is precisely *g/a ≡ 1 for every plant*, and **not one of the
eighteen measurements is at 1**. The concentration is real, it is ordered by heat rate, and it is
the direction `cheapest_first` encodes. **This is the mirror image of nyiso-203 §5's NYC result,
with the opposite sign — and it is a CLEAN NEGATIVE, which the charter names a full result.** Two
independent legs confirm it. **(1) Do-no-harm:** `pro_rata` manufactures **1.64×** more energy over
the three years (0.0382 vs 0.0233 TWh). **(2) Rule 17 `[R-FLOOR-WINDOW]`, and this is decisive:**
`pro_rata` would floor Danskammer 2480 in **100 % of binding hours — 504 / 432 / 600 h — against a
metered P(on) of 0.125 / 0.255 / 0.370**, versus the **192 / 24 / 0 h** `cheapest_first` actually
produces. **The swap would multiply the very D-4 off-window exposure that motivated the inquiry.**
The D-4 rows on 2480 are what nyiso-204b said they might be: **the honest bottom of a correctly
ordered stack.** Rule 20 `[R-FORCED-BUDGET]` leg (a) stays **OPEN**, now with its two cheapest
instruments both closed. **No third option was sought**, per the charter.

**Not a keeper candidate. There is nothing to promote.** No arm was proposed, so the owner's
standing "structural integrity improves but gates regress" formula is not reached — no structure
improves here; the measurement *refuses* the change.

---

## 1. The object, and why the operator rather than the membership

The live limb: `Capital_Hudson` / `ST_GAS` / `tmax` / `31.1 °C`, `floor_pct = 0.0973`
(`commit_frac 0.8105 × min_stable_pct 0.12`, n = 65, frozen), `min_event_hours = 48`,
`exclude_plant_codes` **empty**, `distribution` **empty → `cheapest_first`** by dataclass default.

nyiso-204 refused the membership arm (2480 + 8006) and nyiso-204b refused its narrowed form
(2480 alone); **DO-NOT-REDO covers both and neither was re-tested.** 204b §3 named the instrument
the evidence actually points at: 2480's D-4 conviction is that its meter reads zero in 100 % of the
hours *the cheapest-first fill reaches it* — a fact about **which hours a zonal target selects at
the bottom of the stack**, not about who belongs in the class. The candidates were therefore the
**fill order** or the **target level**. This session took the fill order. The target level is
**not** taken (§5).

**Why this object is cleaner than the one nyiso-204 refused.** Both operators size the same hourly
quantity — `frac × Σ available capacity` over the selected rows — so **the delivered aggregate is
identical and they differ only in which units carry it**. The membership edit, by contrast, shrank
the target's own base by ~60 %: a level change by the back door (rules 21 / 23). **Verified, not
assumed** — the aggregate identity holds to six decimal places in all three years:

| year | `cheapest_first` forced | `pro_rata` forced | target |
|---|---:|---:|---:|
| 2023 | 0.038636 TWh | 0.038636 TWh | 0.038636 TWh |
| 2024 | 0.075831 | 0.075831 | 0.075831 |
| 2025 | 0.090432 | 0.090432 | 0.090432 |

So every number below is **allocation-only**, with no level confound.

## 2. The measurement — nyiso-203 §5's test, verbatim

Hour sets built on the engine's own code path (`iso_zone_tmax` → `tmax > 31.1 °C` →
`_bridge_flagged_runs(48)`), which **reproduces the engine's binding-hour counts exactly —
504 / 432 / 600** — verified independently before the fleet was ever reconstructed. Availability
from the keeper bundle's own `fleet_only` reconstruction; generation from CAMPD unit-level hourly
`grossLoad` at plant grain. `cheapest_first`'s allocation is produced by calling the **shipped**
`_distribute_group_floor` kernel on the reconstructed arrays, not by arithmetic here.

**g/a = (metered generation share) ÷ (available-capacity share). `pro_rata` asserts g/a ≡ 1.**

| year | cut | **2625 Bowline** (HR 10.70) | **8006 Roseton** (11.50) | **2480 Danskammer** (11.85) |
|---|---|---:|---:|---:|
| 2023 | binding (504 h) | **2.01** | 0.54 | 0.15 |
| 2023 | flagged unbridged (384 h) | **1.94** | 0.59 | 0.18 |
| 2023 | binding h14–21 (168 h) | **1.84** | 0.66 | 0.16 |
| 2024 | binding (432 h) | **1.27** | 0.75 | 0.37 |
| 2024 | flagged unbridged (408 h) | **1.24** | 0.77 | 0.40 |
| 2024 | binding h14–21 (144 h) | **1.19** | 0.85 | 0.35 |
| 2025 | binding (600 h) | **1.86** | 0.51 | 0.89 |
| 2025 | flagged unbridged (504 h) | **1.86** | 0.52 | 0.94 |
| 2025 | binding h14–21 (200 h) | **1.65** | 0.62 | 0.99 |

**The signature is unanimous and it survives every pre-registered cut**: the cheapest plant above
1 in 9 of 9, both dearer plants below 1 in 9 of 9. Contrast nyiso-203's NYC limb, where the same
statistic returned **1.22 / 1.25 / 0.57** — a *shared* baseline, no ordering by cost — and
`pro_rata` was ruled supported. **Capital_Hudson is the opposite market.**

### 2.1 Stated against interest — three things this measurement does NOT establish

1. **It does not validate `cheapest_first`'s DEGREE, only its direction.** `cheapest_first`
   allocates **92.2 / 99.8 / 98.5 %** of the floor to 2625; the meters give 2625
   **70.7 / 67.9 / 65.0 %**. It over-concentrates. `pro_rata` under-concentrates
   (35.2 / 53.5 / 35.0 %). **Neither operator reproduces the metered split**; the finding is that
   one asserts the right direction and the other the wrong one.
2. **The derived L1 distance is SPLIT, and it is reported rather than buried.** Summing
   |allocation share − metered share| over the three plants: 2023 **cheapest_first** closer
   (0.477 vs 0.710); 2024 **pro_rata** closer (0.287 vs 0.637); 2025 **pro_rata** closer
   (0.600 vs 0.670). That statistic was **not** pre-registered, it is dominated by the level of
   2625's share rather than by the ordering, and it does not overturn a 9-of-9 unanimous g/a
   signature — **but it is the one cut that does not point the same way, and it is on the record.**
3. **g/a is a whole-dispatch statistic, not a bottom-slice one.** A cheap plant being
   over-dispatched overall is merit order working; strictly, that refutes `pro_rata`'s
   proportionality claim rather than proving a *commitment floor* belongs on the cheapest unit.
   The same logic is what nyiso-203 used, in reverse, and it is why the verdict rests jointly on
   §3 rather than on §2 alone.

## 3. The two legs that decide it

### 3.1 Do-no-harm: `pro_rata` manufactures 1.64× more energy

`Σ max(0, floor − metered)` over binding hours:

| year | `cheapest_first` | `pro_rata` | ratio |
|---|---:|---:|---:|
| 2023 | 0.00401 TWh | 0.00787 TWh | **1.96×** |
| 2024 | 0.01585 | 0.01545 | 0.97× |
| 2025 | 0.00346 | 0.01489 | **4.30×** |
| **total** | **0.02332** | **0.03822** | **1.64×** |

2024 is the one year they are level (0.97×), and it is stated plainly rather than averaged away.

### 3.2 Rule 17 `[R-FLOOR-WINDOW]` — the decisive leg: the swap would make the exposure WORSE

Binding hours the floor would place on each plant, against that plant's own metered P(on):

| year | plant | `cheapest_first` h | `pro_rata` h | metered P(on) on binding hours |
|---|---|---:|---:|---:|
| 2023 | **2480 Danskammer** | 192 | **504 (100 %)** | **0.125** |
| 2024 | **2480** | 24 | **432 (100 %)** | **0.255** |
| 2025 | **2480** | 0 | **600 (100 %)** | **0.370** |
| 2023 | 8006 Roseton | 24 | 240 | 0.544 |
| 2024 | 8006 | 0 | 288 | 0.669 |
| 2025 | 8006 | 24 | 576 | 0.728 |

Rule 17 asks whether a floor binds *"in hours its own driver evidence says the class is offline"*.
Under `pro_rata` the Capital_Hudson step would floor Danskammer in **every** binding hour of
**every** year while its meter reads zero in **63–88 %** of them. **That is a new and much larger
rule-17 violation than the one the session set out to relieve** — the arm would have moved the
defect and enlarged it, which is the same shape of error nyiso-204 caught in the membership arm.

## 4. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 step 0 killed the arm pre-solve; no screen year needed pre-registering |
| **Rule 29(b) G-DRIFT** | **re-validated EMPIRICALLY at this HEAD, not by reading hunks**, as the charter requires: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git diff` **CLEAN** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically. G-CTRL **form 4** is valid and **no control solve was spent**. *(That probe prints its own `"VERDICT": "STOP"` — the nyiso-198 duct-peaking gate for `cc_duct_peaking_row_scoped`, an already-adjudicated `R` cell. Part of the committed record, **not** a drift signal; nothing here re-opens it.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **UNCHANGED**. Not a keeper candidate; no promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Markers** | untouched. `complete` (WITHDRAWN, Q5) and `frontier` re-entry are **owner** acts. Card C-19 / Q51 stays **PARKED** |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual. NYISO reads **fails 0**; C3c is the ledgered non-downgrading caveat and was **not** an objective. The `offer_curve_by_group` channel is owner court under carve-out condition (c) and was **not touched** |
| **Rule 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** | zero fields, zero DOF entries, zero re-derivations. The PREREG §3 declared **before measuring** that an operator swap would have been **one binary free parameter**, not the zero-DOF a membership edit claimed — that declaration cost nothing, because the arm is refused |
| **Rule 22 `[R-HOLDOUT]`** | 2023–2025 only. No out-of-training year solved, scored or registered |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only. The PREREG addendum's cross-ISO operator census is **descriptive context only**; nothing is proposed, transferred or concluded for any other ISO |
| **Rule 26 / 28** | NYISO matrix shard `reliability_floor` cell updated **in this session** with this negative outcome, per duty (b) |
| **Rule 15** | nothing registered — no run finished. Git history + this finding are the record |
| **Files added** | 1 probe, 1 JSON output, 1 PREREG, this finding. No `src/market_sim/` change, no CSV edit |

### 4.1 Reported, not fixed — pre-existing failures at HEAD, other lanes' work

Measured at this session's HEAD across the charter's named files: **32 failed / 62 passed** —
27 in `tests/unit/model/test_d62_published_going_forward_bar.py` +
`test_d74_no_default_cap_convention.py` (capx lane), 4 in `tests/scoring/test_ff_readiness_battery.py`,
1 in `tests/scoring/test_collate_scenario_campaign_common_set.py` (SCN-WS5A-LOAD lane) — plus
`tests/regression/test_constants_facade.py::test_moved_surface_is_complete` and
`tests/unit/data/test_caiso_st_gas_peak_measured.py::…::test_registry_value_matches_the_committed_artifact`
(1.154 vs 1.166). **Not fixed from this lane** (rule 25): none is NYISO's file or NYISO's number,
and silently re-baselining another lane's regression constant is how a real regression gets buried.

### 4.2 An environment note worth recording for the next lane

`data/clean/` was **empty** at session start — it is gitignored, derived and disposable — so **no
phase-0 reconstruction can run in a fresh session until it is rebuilt** from `data/raw`
(`scripts/regenerate_clean.py`, or the targeted `scripts/data/curate_<datatype>.py`). The NYISO
reconstruction path additionally needs `capacity-deliverability` and `nyiso-interface-flows`, both
of which hard-fail with a named remedy rather than silently no-opping. Budget for it: the full tree
is tens of minutes; the two targeted curations are ~2 minutes.

## 5. What this closes, what stays open, and what is deliberately NOT taken

**Closed (negative).** The `pro_rata` operator for the Capital_Hudson `ST_GAS` `tmax 31.1` limb is
**REFUTED** on its own market's meters. `cheapest_first` is **CONFIRMED** as the better-supported
of the two operators the engine offers. **DO-NOT-REDO**: do not re-test this cell without new
measured NYISO conduct data. Combined with nyiso-204 / 204b, **both cheap instruments aimed at the
Capital_Hudson D-4 rows are now closed** — the membership column (twice) and the fill order.

**Open.** Rule 20 `[R-FORCED-BUDGET]` leg (a), and the unit-grain C8 exposure it rests on
(`ST_GAS` 0.351 / 0.343 / 0.268 against the 0.30 cap, 2 of 3 years). Unchanged by this session.
`DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` remains **UNRULED**; nothing here rules it.

**Deliberately NOT taken, and named so the next lane does not read silence as absence.**

- **The TARGET LEVEL** — the other instrument 204b §3 named. Lowering `floor_pct` on this limb is a
  **re-derivation with no source-data trigger** (rule 23), it would move a coefficient identified
  on n = 65 observations of the whole class, and its only visible motive would be the D-4 rows it
  removes. That is owner court, not a lane's. **Not proposed here.**
- **A third operator**, or any hybrid. The charter is explicit: a clean negative is a full result,
  and no third option is to be sought. None was.
- **Re-litigating the membership**, in either refused form.
- **The NYC persistent-base limb's daily-mean-identified / hourly-applied construction gap** —
  reported by nyiso-203, still awaiting an owner ruling, still not taken.
