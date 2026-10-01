# PRECOMMIT — SPP-27: place the per-plant must-run window at the WHOLE-OPERATING-DAY commitment grain. NOTHING IS SOLVED YET.

**Lane** SPP-27 · **Base** `bc0cbe0784f2be7e9ce41b84dd3e55ba0089f2dc` · **Keeper / control**
`2026-09-10-spp-64-stgas-selfcommit`, bundle `results/calibration/spp64_span` (committed WITH
`hourly/` sidecars — **differenced, NEVER re-solved**) · **Object** card **R-be**, the named,
unfixed rule-17 `[R-FLOOR-WINDOW]` defect the keeper carries · **Predecessors**
`docs/RESULT-spp64-span.md` §4(i), `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`,
`docs/handoffs/FINDING-spp-64-2026-09-10.md`, `docs/calibration-log/spp.md` (spp-25/spp-26).

**THIS DOCUMENT IS PUSHED BEFORE ANY LP.** Every number below is re-derived in this session from
the committed artifacts and three zero-LP `run_year(fleet_only=True)` rebuilds of the keeper's own
recipe — never from another lane's prose. Rule 32 `[R-SHARD]`: the parent runs **no LP**; the
solves are shards. SPP holds **no `complete` marker and no `frontier` declaration**, and this lane
neither adds, requests nor implies either.

---

## 0. WHAT THE PHASE-0 CENSUS ACTUALLY FOUND, INCLUDING WHAT IT KILLED

The keeper's note and the handoff both diagnose R-be as *"their operating hours are simply not
top-system-load correlated"*. **That reading is only partly right, and this lane says so before
proposing anything.** Measured this session:

- The three persistent failures ARE load-correlated, just not tightly enough — 1230's floor window
  is **3.5×** enriched in its own online hours over the plant's base rate (1271 **4.2×**, 1235
  **3.3×**). A pure "not correlated" story is falsified.
- Their windows are also **over-sized in the individual year** by the pooled `online_frac`
  construction (1230: k = 1,428 h against 839 metered online hours in 2023, and 2,186 in 2024).
  **That is NOT a defect** — a pooled multi-year duty statistic is exactly what rule 13
  `[R-MEASURED]` requires for forward regeneration, and it necessarily mis-sizes any one year. The
  per-year alternative (`mustrun_online_frac_per_year`, miso-172) is registered **BACKCAST-ONLY**
  for precisely that reason. **This lane refuses it**: trading a rule-13-admissible input for one
  with no forward analogue, to move a diagnostic, is the wrong direction.
- **What IS a defect, and is repairable, is the GRAIN.** §1.

**Two candidate signals were measured and are DELIBERATELY NOT TAKEN, declared here so the choice
cannot be read as hidden.** Ranking days by their **peak** rather than mean load, and ranking on
**net** load (load − wind − solar) instead of gross, both score marginally better on the
conduct-overlap statistic of §4 (day-peak-net 0.8368 against day-mean-gross 0.8238 over 65
plant-years). Neither is taken: each bundles a **second, independently-unmotivated change** into
the same arm, and net-vs-gross is a **wash at the hour grain** (0.8168 against 0.8168), so SPP's
own data does not establish that net load is the better commitment signal here. The arm is the
**minimal** lift of the incumbent's own construction, and nothing was swept against any gate in §6.

## 1. THE OBJECT — a floor that asserts a COMMITMENT but is placed like ENERGY

`st_gas_mustrun_per_plant` claims a **commitment**: a day-ahead, whole-operating-day decision by a
vertically-integrated utility. The engine places it by ranking **individual hours** by system load
and taking the top `k = round(online_frac × 8760)`. So the floor inherits the **diurnal shape of
load**, not the diurnal shape of **commitment** — it binds at the daily peak and is absent
overnight **on the very same committed day**. Rule 17 `[R-FLOOR-WINDOW]` in both directions.

### 1.1 The driver measurement — the plants' own CAMPD record, zero LP, no residual in the statistic

Peak-to-mean of each plant's **online** hour-of-day profile (1.000 = committed for whole days;
≫ 1 = daily cycling), 3-year mean, from the committed `frontend/data/backcast/bench/SPP/<y>.json.gz`:

| plant | p2m | plant | p2m | plant | p2m |
|---|---|---|---|---|---|
| 2446 Maddox | **1.007** | 2952 Muskogee | 1.031 | 7013 East 12th St | 1.086 |
| 1416 Arsenal Hill | **1.007** | 2965 Tulsa | 1.033 | 1230 Cimarron River | 1.090 |
| 3484 Nichols | 1.008 | 3476 Knox Lee | 1.034 | 4940 Riverside | 1.118 |
| 3478 Wilkes | 1.012 | 1417 Lieberman | 1.046 | 1271 Coffeyville | 1.146 |
| 6193 Harrington | 1.013 | 1233 Fort Dodge | 1.049 | 2951 Horseshoe Lake | 1.231 |
| 2956 Seminole | 1.017 | 2964 Southwestern | 1.060 | **3008 Mooreland** | **1.609** |
| 3485 Plant X | 1.025 | 2226 Canaday | 1.073 | | |
| 3482 Jones | 1.027 | 1235 Great Bend | 1.073 | | |

**21 of 22 plants sit in 1.007–1.231.** When these units are synchronized they run through the
overnight trough. Corroborated by the night/afternoon share (h0-5 ÷ h12-17 of the plant's own
online hours): 19 of 22 in **0.78–1.09**. **Only Mooreland 3008 genuinely two-shifts** (0.25–0.38),
with Horseshoe Lake 2951 partly so (0.49–0.79).

The incumbent window's own peak-to-mean over the same plant-years is **1.03–2.86** (the four
D-4-failing plants 1.82–2.38), and at the mechanism level, floored-MWh-weighted, **1.235** (SPP
2023, from the engine's own arrays).

### 1.2 The physics statement — rule 18 `[R-PHYSICS]`, and it is not close

Contiguous binding blocks the window **implies**, i.e. the starts the floor asserts, against the
runs the meter records, summed over the ST_GAS fleet:

| year | measured runs | **incumbent hour grain implies** | ratio | **day grain implies** | ratio |
|---|---|---|---|---|---|
| 2023 | 647 | **2,843** | **4.39×** | 288 | 0.45× |
| 2024 | 746 | **2,740** | **3.67×** | 320 | 0.43× |
| 2025 | 778 | **2,335** | **3.00×** | 284 | 0.37× |
| **span** | **2,171** | **7,918** | **3.65×** | **892** | **0.41×** |

Per plant the incumbent asserts 202 starts on 989 MW Muskogee in 2024 (measured 27), 307 on Plant X
in 2023 (measured 45), 179 on 883 MW Wilkes (measured 11), 166–169 on Maddox (measured 6–16). **A
gas-steam unit cannot start 200 times in a year.** The day grain asserts **fewer** starts than the
meter records in every year — a floor that is a conservative commitment scaffold, which is what a
floor is for.

## 2. RULE 17 `[R-FLOOR-WINDOW]` — the triple

**(a) DRIVER.** SPP's gas-steam fleet is **100.0 % EIA-860 Sector 1 "Electric Utility"** (9,515 of
9,515 MW; keeper 8's own census, inherited not re-derived), and a vertically-integrated utility
commits **day-ahead for the operating day**, not hour by hour. The plants' own meter agrees on both
counts: §1.1's flat online diurnal profile and §1.2's 2,171 measured runs across three years —
multi-day blocks, not daily cycles.

**(b) WINDOW.** `round(k/24)` whole operating days, ranked by that day's **mean system load** — the
mechanical lift of the incumbent's own hourly ranking to the commitment period. **Same signal, same
ordering statistic, one grain coarser.** SIZE (`online_frac`), LEVEL (`committed_pct`, the
P5-of-online LSL) and MEMBERSHIP are untouched.

**(c) FORWARD STORY.** The ranking is the model's **own load shape**, computed exactly as the hour
ranking is. **Nothing measured enters the placement**, so a forecast year regenerates it from
forward drivers and it responds to changed conditions. The field is therefore deliberately **NOT**
in `_BACKCAST_ONLY_OVERLAY_FIELDS` — unlike `mustrun_online_frac_per_year`, which is.

## 3. THE SEAM, AND THE PROOF IT IS SURGICAL (zero LP, measured)

One boolean, `ScenarioConfig.mustrun_window_commitment_grain` (default **False**), consumed by two
new pure helpers in `data/fleet/arrays.py` (`_commitment_day_order`, `_mustrun_window_hours`) at
**both** per-plant must-run window sites inside `_compose_min_gen_floors` — the committed-tranche
block (`cc_mustrun_per_plant` / `st_gas_mustrun_per_plant`) and the `st_gas_mustrun_p25_level`
block — so the mechanism id's window stays single-valued.

Two `run_year(fleet_only=True)` rebuilds of the keeper's **2023** recipe, control and arm, in one
process with `clear_fleet_caches()` between:

| mechanism | CONTROL floored TWh | p2m | ARM floored TWh | p2m |
|---|---|---|---|---|
| 1 `nuclear_mustrun` | 16.926975 | 1.000 | **16.926975** | 1.000 |
| 2 `chp_steam` | 1.245162 | 1.000 | **1.245162** | 1.000 |
| **16 `st_gas_mustrun_per_plant`** | **3.870051** | **1.235** | **4.070490** | **1.000** |

`max |Δ min_gen|` over every cell **neither** run tags as ST_GAS-mustrun: **0.000000**. The control
column reproduces the keeper's committed 3.8701 TWh, so the reconstruction is faithful.

## 4. WHAT THE ARM DOES **NOT** DO — declared before the solve, at full magnitude

**It does not close R-be, and this lane will not pretend otherwise.** The same phase-0 census, using
the D-4 rider's own statistic (the share of a plant's effective binding hours in which its meter
reads > 0), over 65 plant-years:

| | incumbent hour grain | **arm, day grain** |
|---|---|---|
| fleet mean overlap | 0.8168 | **0.8238** |
| rows better / worse | — | **25 / 26** |
| plant-years below 0.50 (the rider's proxy) | **10** | **11** |

The count moves the **wrong way by one**, and the mechanism is exactly why: **Mooreland 3008 is the
one measured two-shifter in the fleet** (p2m 1.609), so a uniform whole-day window is wrong for it
and its 2023 and 2025 rows cross below 0.50 (0.552 → 0.488, 0.527 → 0.474), while 1230's 2024 row
crosses above (0.476 → 0.615). **The lane does not special-case Mooreland**: a per-plant grain
predicate needs a threshold, which is a free parameter (rule 21 `[R-DOF]`), and choosing it against
this statistic is the fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids. A plant-level
exclusion is refused for the reason miso-170 already gave — it *"would bury that error inside a
membership list"*.

**The rest of the R-be residual is day SELECTION, and no forecast-admissible signal reaches it.**
For 1230/1235/1271 the day-selection lift over chance is only ~2×: their commitment responds to
their own utility's conditions, not to SPP-wide load. That is stated as an open limit, not repaired.

**The arm also costs floored energy** (§5): whole days land in more available hours, so the
mechanism forces **+3.2 % to +5.2 %** more. Against rule 20 `[R-FORCED-BUDGET]`, the keeper's
measured ST_GAS forced share is 0.1962 / 0.1849 / 0.1744 against a 0.30 cap; a proportional rise
lands ≈ 0.206 / 0.191 / 0.181, still under. **If it goes over, the rule's conditional-pass limb
opens and this lane reports the outcome whatever it is.**

**So the warrant is rule 1 `[R-STRUCT]`, and only that**: *"never judge a structurally-correct
mechanism by whether it improves the backcast fit, and never reject/revert it because the residual
didn't move."* §1.1 and §1.2 are measured statements about what the floor asserts, independent of
any residual and of D-4. If the owner's read is that a structural repair which leaves the named
diagnostic open is not worth a keeper churn, that is a defensible ruling and §9 puts it explicitly.

## 5. SCREEN YEAR — 2023, NAMED ON THE MECHANISM'S OWN MEASURED FOOTPRINT

Footprint = floor **MWh that MOVES** (symmetric difference of the incumbent and proposed windows at
the same level and the same `pmax × availability` clip). Model-vs-model; no actual, no residual:

| year | incumbent TWh | arm TWh | Δ | **MOVED MWh** | **moved %** | keeper C1 ST_GAS residual |
|---|---|---|---|---|---|---|
| **2023** | 3.8699 | 4.0704 | **+5.18 %** | **858,999.2** | **22.20 % ← LARGEST** | −6.034 TWh |
| 2024 | 4.1137 | 4.2453 | +3.20 % | 806,653.2 | 19.61 % | **−7.423 ← largest residual** |
| 2025 | 3.4778 | 3.6157 | +3.97 % | 669,504.3 | 19.25 % | *(C1 skipped — preliminary EIA-923)* |

**The footprint choice and the residual choice DISAGREE and the lane takes the footprint** — 2024
carries the larger C1 miss and the smaller footprint. 2023 is screened.

## 6. THE STOP GATES — STRUCTURAL, PRE-REGISTERED, AND **NONE READS D-4**

Rule 29 `[R-SCREEN]`: a screen **may kill an arm; it may never promote one.** The target of this
lane is the **D-4 per-unit conduct rider**, so **no gate below reads D-4, the conduct overlap of
§4, or any per-plant conduct statistic, in either direction.** Every gate asks what the *placement
rule* does.

| gate | asks | STOP bar |
|---|---|---|
| **G-1** config identity & liveness | `mustrun_window_commitment_grain: true`; `st_gas_mustrun_per_plant` true; `st_gas_mustrun_p25_level`, `mustrun_online_frac_per_year`, `mustrun_layup_window_mask`, `mustrun_plant_exclusions`, `cc_mustrun_per_plant` all **false**; ten fossil classes still 0.93 × 4 bands; `offer_curve_by_group` byte-identical | any mismatch |
| **G-2** the window's own SHAPE (the thing being repaired) | mechanism-16 floored-MWh-weighted diurnal peak-to-mean, from the solved bundle's own `min_gen`/`min_gen_mechanism` | **not 1.000 ± 0.005** (pre-solve arithmetic says exactly 1.000) |
| **G-3** the PHYSICS the shape implies (rule 18) | implied starts (contiguous mech-16 binding blocks) summed over the fleet, against the meter's 647 runs | **> 647**, i.e. the floor may never assert more starts than the plants performed |
| **G-4** SIZE preservation — *this is the "not a shrinkage repair" gate* | mechanism-16 floored energy, all-on basis | **outside [3.95, 4.20] TWh** (control 3.8699; pre-solve arm 4.0704; band = control +2 % to +8.5 %). A repair that fixes the shape by making the floor stop binding is refused here. |
| **G-5** reach — no new forcing beyond the declared mechanism | no class other than ST_GAS acquires `min_gen`; every other mechanism id byte-identical to §3's control column; `dump` = 0; slack ≤ **370.102 MWh** (the keeper's own 2024 value; 2023 is 0.000) | any breach |
| **G-6** no non-target load-bearing regression | C3a within ±10 %, C3b ≤ 0.20, C2 family volumes in band — scored by `scripts/lib/spp63_g5.py`, **re-validated on the keeper this session** (C3a 25.38 / 25.47 / 28.8, C3b 0.173 / 0.171 / 0.163, reproducing the committed numbers exactly); and **C1 must not go PASS → FAIL** | any **PASS → FAIL** |

**How G-2 / G-3 / G-4 are measured, stated now.** All three are properties of the **fleet arrays**,
which the config alone determines, so the **parent** verifies them at **zero LP** by rebuilding the
shard's own returned bundle through `run_year(fleet_only=True)` (`scripts/lib/bundle_fleet.py`) and
reading `min_gen` / `min_gen_mechanism` — the identical instrument §3 used on the control. That is
deliberate: it confirms the shard solved the configuration it claims, and it keeps every LP in a
shard (rule 32(a)). G-5's `dump`/`slack` and G-6 come from the bundle's committed `hourly/`
sidecars. The slack bar is the **span-wide** envelope applied to any year (the keeper's 2023 and
2025 are both 0.000 MWh; 370.102 is its 2024).

**G-6's C1 leg is one-sided and is the prompt's own condition** — "a repair that fixes D-4 by
SHRINKING the floor until it stops binding is not a repair; it must keep the structural gain." It
can only kill the arm; a C1 improvement earns the arm nothing and is not read.

**G-4's band is arithmetic, not a sweep.** It was written from the §3/§5 pre-solve delta before any
solve, and no variant was tried against it.

## 7. G-DRIFT — the code-level audit, so no control solve is spent (rule 29(b) form 4)

The keeper's recorded `basis_sha` `7de0b789a4f709b19baccd10de85cbb108ba5d66` **resolves** at this
base (it post-dates the 2026-08-16 history rewrite), and the commit that ADDED
`results/calibration/spp64_span/meta.json` is `d0e137f4`. Both audits:

```
git diff --stat 7de0b789a4f709b19baccd10de85cbb108ba5d66 HEAD -- src/market_sim \
  scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib \
  data/raw/_validation-source data/raw/reference
git diff --stat d0e137f4 HEAD -- <the same paths>
```

**Both return EMPTY — zero solve-path files changed.** There is nothing to classify: form 4 is
valid, **keeper 8's committed bundle IS the control, and NO control solve is spent.** (The audit is
of PRE-EXISTING drift; this lane's own solve-path change is the arm, declared in §3 and gated by
G-1.) Corroborated by §3's control rebuild reproducing the keeper's committed floored energy.

## 8. DOF — rule 21 `[R-DOF]`

Ledger goes **3 entries / 2 residual → 3 entries / 2 residual. ZERO free parameters are added.**
`mustrun_window_commitment_grain` is a boolean gate. There is **no threshold, no share, no
multiplier and no length**: the grain is the **operating day**, which is the period a unit
commitment is made for, and `round(k/24)` is arithmetic on the existing `online_frac`. The
`offer_curve_by_group` uniform 0.93 is inherited unchanged — this arm does not touch the authorized
price-tuning channel, and `authorized_price_tuning` is declared unchanged in the attestation.

**Rule 19 `[R-ONE-MECH]`, enumerated.** The floor has four orthogonal properties. Membership
(`mustrun_plant_exclusions`, off), window SIZE (`mustrun_online_frac_per_year`, off), LEVEL
(`st_gas_mustrun_p25_level` / `_measured_level` / `_oom_level`, all off), hour-eligibility
(`mustrun_layup_window_mask`, off). **This arm moves window PLACEMENT alone**, and none of the other
four is armed on SPP's keeper. The window is **replaced, never stacked**. The COAL synchronization
floor (`coal_sync_online_frac`, armed on SPP via `coal_mustrun_per_plant`) and the CT_PEAKER floors
deliberately **keep the hour grain** — separate mechanism ids whose own conduct evidence this lane
does not carry, and rule 25 `[R-ISO-SCOPE]` says SPP's ST_GAS census cannot speak for them. The
coal half is the parallel `claude/spp-64-price-formation-rbb` lane's object and is left to it.

**Rule 25 `[R-ISO-SCOPE]`.** The field's dataclass default stays `False` and it is registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at that declared default, so **every pre-existing cache key of all
seven ISOs is byte-stable and no other ISO moves.** No `iso_configs` default override is added. The
matrix cell is `O` in SPP's shard only; every other shard gets `U`.

## 9. THE SOLVES — rule 32 `[R-SHARD]`. The parent runs NO LP.

Measured basis: the keeper's own span took **12 min 5 s** wall for three years (`RESULT-spp64-span`
§1), so one span invocation fits inside rule 32(b)'s 20-minute unit and is solved as ONE shard —
which is also what rule 16 `[R-ALLYEARS]` wants (one `--year 2023 2024 2025` invocation, one
bundle, years sequential per rule 12).

```
SCREEN  claude/spp27-screen-2023   results/calibration/spp27_screen_2023   ~3 min
  python3 scripts/replay_keeper.py results/calibration/spp64_span \
    --years 2023 --out-dir results/calibration/spp27_screen_2023 \
    --set mustrun_window_commitment_grain=true

SPAN    claude/spp27-span          results/calibration/spp27_span          ~13 min
  python3 scripts/replay_keeper.py results/calibration/spp64_span \
    --years 2023 2024 2025 --out-dir results/calibration/spp27_span \
    --set mustrun_window_commitment_grain=true
```

**The SPAN is the only registerable bundle.** The screen is a throwaway probe — never registered,
never a keeper, never quoted as a keeper number — and its year is re-solved inside the span. **The
span runs only if the screen clears every gate in §6.** Both bundle families are **gitignored**
(`results/calibration/spp27_*/`), which is what discharges rule 29(c); rule 31 `[R-RETAIN]`:
**nothing will be `rm`'d and nothing is deleted before the owner rules on promotion.**

**KNOWN TRAP, pre-declared:** `replay_keeper.py --out-dir` does not propagate
`calibration_attestation.json`, so the bundle scores **C6 UNATTESTED** unless the parent authors it
(`scripts/gen_spp64_attestation.py` re-pointed at this lane).

## 10. WHAT THIS LANE PRE-COMMITS TO REPORTING, WHATEVER THE RESULT

- **Every gate in §6 at full magnitude**, pass or fail.
- **The D-4 rider outcome in full**, including the Mooreland rows §4 predicts will cross below
  0.50, and including any row that does not move. It is the lane's object and it is reported even
  though no gate reads it.
- The rule-20 `[R-FORCED-BUDGET]` forced share and **D-1** whatever they say.
- **Registration under rule 15 `[R-DASHBOARD]` whatever the span says** — keeper or rejection — in
  the session that produces it, plus the rule-28 matrix cell in **SPP's shard only**.
- **The promotion question put explicitly in-session** (rule 31), with the statement that the
  bundles live on gitignored local disk and do **not** survive this container.
- `[R-HOLDOUT]` was removed 2026-09-09, so **no year is protected from being iterated against**.
  Every number here and in the result is model-**SELECTION** evidence, never a certified
  out-of-sample skill claim, and any determination is a **rubric determination** only.
