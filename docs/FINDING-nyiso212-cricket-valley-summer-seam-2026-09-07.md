# FINDING nyiso-212 — the Cricket Valley over-ceiling months are **not an outage-window defect**: the two CAMPD downloads agree to the MWh, the extract is faithful to its source, and the whole excess is a **summer-capability seam between `cc_capacity_reconcile` and `cc_nameplate_summer_derate`**

**Session:** nyiso-212, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-c7tc79`, off `main` `abdd30c9`. **Date:** 2026-09-07.
**Keeper: `2026-09-06-nyiso-202-startup-aware` — UNCHANGED.** No `ScenarioConfig` field, no
coefficient, no offer curve, no derive script, no scorer, no marker, no keeper, no gate moved.

**ZERO LP SPENT.** Rule 29 `[R-SCREEN]` step 0 in full: three on-recipe `fleet_only` rebuilds of
the keeper's `meta.json` (no solve, no dispatch, no prices), CSV and parquet reads. No screen, no
arm, no bundle, no registration — 29(c) has nothing to delete, rule 15 nothing to register.

**Pre-registration:**
`results/calibration/PREREG-nyiso212-cricket-valley-outage-window-construction.md`, committed and
pushed at `b9bfacf4` **before any plant-grain number was read**, and not edited since.
**Machine records:** `results/calibration/_nyiso212_overceiling_decomposition.json` (pre-registered
instrument) and `_nyiso212_summer_seam_census.json` (post-hoc characterisation, labelled as such).
**Reproduce:** `uv run python scripts/probes/nyiso212_overceiling_decomposition.py` then
`uv run python scripts/probes/nyiso212_summer_seam_census.py` (the second reads the first's
rebuild cache under `.cache/nyiso212/`).

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads **CALIBRATED, grade 7 of 8,
fails 0**, C3c the lone ledgered non-downgrading caveat. Nothing below was selected because a
residual moved (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`); the object is a physical
contradiction between measured inputs that C1 currently passes over.

**Rule 22 `[R-HOLDOUT]`.** Every year read here is **in-sample (2023, 2024, 2025)**. 2022 was not
read. 2020, 2021 and the locked test are untouched; no marker byte moved. The CAMPD unit-level
parquets carry 2019–2026; only the 2023–2025 files were opened, and only for plant 57185.

**Owner's standing formula, carried verbatim** (this session's opening message): *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper.."* **No candidate exists.** This session produced no solve; the formula
attaches only to an arm that clears a separately pre-registered screen and the full span (§7).

---

## 0. The result in one paragraph

nyiso-211 handed forward one object to start with: six plant-months of 2024/2025 (Jul/Aug/Sep 2024,
Jun/Jul/Aug 2025, plus Jul 2023 on both bases) in which the keeper's LP ceiling at Cricket Valley
57185 sits **below the plant's own CAMPD meter**, framed as an *outage-window construction defect*
with "cross-unit window sums exceeding the plant" as the likely mechanism. **That framing is
falsified, cleanly and at zero LP.** Under a pre-registered exact identity the excess in every one of
the seven months decomposes into four terms that name four different objects, and three of them are
zero or negative: the facility-level and unit-level CAMPD downloads agree **to the MWh** in every
month of 2023–2025 (`T_bench ≡ 0`); the committed extract windows are faithful to their own source
(`T_in ≤ 0.34 GWh` in every scored month, and re-running the deriver's rule on the current
unit-level file reproduces **every** committed 2024/2025 window); and the running blocks sit
*below* their LP share (`T_cap < 0`). **The whole excess — and more than the whole excess — is
`T_stat`, the statistical overlay riding on top of the windows**, and inside it the carrier is the
**summer** leg: the plant's statistical availability factor reads **0.965 off-summer and 0.747075
in Jun–Sep**, and `0.747075 = 0.965 × 0.774171 = (1 − WEFOR) × net_summer / nameplate` to six
decimals. That ratio, `1,016.1 / 1,312.5`, is `cc_nameplate_summer_derate`'s per-plant summer
multiplier — premised on the plant being carried at *nameplate* — applied to a capacity that
`cc_capacity_reconcile` (mode `cap`) has **already** moved off nameplate to the CAMPD p99.9 of
**1,086.9 MW**. Constructed summer capability: **841.4 MW**, against a design intent of 1,016.1 and a
measured summer p99.9 of 1,078 gross. The plant's own meter exceeds that constructed ceiling in
**1,906 summer hours (261.7 GWh)** over 2023–2025. Class-wide the same seam removes **470.2 MW** of
Jun–Sep capability from NYISO's 12 `cap`-row CC_REGULAR plants (Athens 126.4, CPV Valley 63.2,
Saranac 28.4, …) and adds capability at the three `raise`-row plants. Both mechanisms are measured
inputs and **stay** (rule 14 `[R-ACCURATE]`); what is wrong is that one phenomenon — a CC plant's
summer capability — is stated twice, by two constructions that no longer agree (rule 19
`[R-ONE-MECH]`). The preferred pre-registered prediction did not fire; the one that did is reported
with the object inside it corrected.

## 1. Pre-registered identity checks and predictions, exactly as declared

| id | declared bar | measured | verdict |
|---|---|---|---|
| **I1** instrument (rebuild reproduces nyiso-211's arm-basis 57185 monthlies) | ≤ 0.5 GWh / month; `mean_avail` to 4 dp | worst **0.046 GWh**; **4.6e-5** | **PASS** |
| **I2** windows (CSV reconstruction = loader factor hour for hour; statistical factor tranche-flat) | max abs diff ≤ 1e-9; spread ≤ 1e-9 | **0.3333** on 3 boundary days; spread **0.0**; availability 0 where ufac 0 | **FAIL** (see §1.1) |
| **I3** basis (`Σ c_mon = c_ann` ± 0.01 GWh; `c_ann` = facility gross × 1.0 within 0.1 %) | both legs | rounding leg **0.02 GWh** (2023, 2025); basis leg **3e-6 / 2e-6 / 1e-6** | **FAIL on the rounding leg**, basis leg holds (§1.2) |
| **I4** deriver (committed 2024/2025 windows reproduce from the current unit-level file) | every window | **every window reproduced**, zero missing, zero extra | **PASS** |
| **P1** — *preferred*: `T_bench` dominates in ≥ 4 of 6 repair-created months | ≥ 50 % of X, largest | `T_bench` = **0.00** in all 36 months | **FALSIFIED** |
| **P2** — *declared to hurt P1*: `T_in` dominates, I4 fails | ≥ 50 % of X in ≥ 4/6 **and** I4 fails | `T_in` ≤ 0.34 GWh (≤ 1.6 % of X); I4 passes | **FALSIFIED** |
| **P3** — third, disjoint: `T_cap + T_stat` dominate, `T_bench`, `T_in` each < 25 % | ≥ 50 % in ≥ 4/6 | `T_stat + T_cap = X` to 0.00 in every month; `T_bench` = 0, `T_in` < 2 % | **FIRES** (6 of 6, and Jul 2023) |
| **P4** — reported: `T_stat` a co-carrier | ≥ 25 % of X in ≥ 3 of 7 | `T_stat` ≥ **100 %** of X in **7 of 7** | fires |
| **P5** — timing: `T_bench` ≤ 2 % of M in Jan–Jun 2024 | — | 0.00 in every month | bar met; **inference vacuous** (`T_bench ≡ 0` everywhere, so it distinguishes nothing) |

**The pre-registered verdict is P3.** Its declared outcome family named the object as "a per-block
CAPACITY BASIS (plant-level p99.9 cap ÷ 3 vs a block's 374–380 MW peak)". **That guess inside P3 is
wrong and is corrected here rather than quietly reworded**: `T_cap` is *negative* in every scored
month (the running blocks average below their 362.3 MW share), so the per-block share is not the
carrier; `T_stat` is, and §3 names which leg of it.

### 1.1 I2 failed as declared, by a known artifact, and its consequence is honoured

The reconstruction differs from the loader by **exactly 1/3 for exactly 24 hours** three times —
2023-11-22, 2024-02-04, 2025-02-21 — because my reconstruction **unioned** each unit's rows while
the loader **sums** them: U002's `10-25→11-22` and `11-22→12-01` share Nov 22, U002's `01-28→02-04`
and `02-04→03-19` share Feb 4, U001's `01-01→02-21` and `02-21→02-26` share Feb 21. This is the
same-unit boundary-day double count `unit_outage_per_unit_clip` exists for (nyiso-211 §6 sized it
at 8.39 GWh/yr at this plant; 3 × 24 h × 362.3 MW ≈ 26 GWh over three years agrees). **None of the
three days is in a scored month.** The PREREG's consequence binds as written: **the `T_in` / `T_cap`
split is reported as UNVERIFIED by its declared bar**, and the load-bearing statements below rest on
`X`, `T_bench` (both independent of the reconstruction) and `T_stat = C1 − C2`, which is built from
the **loader's** factor and the rebuild's availability array and never touches the reconstruction.
A post-hoc **sum-form** reconstruction reproduces the loader at **0.0** in all three years
(`_nyiso212_summer_seam_census.json` → `post_hoc_I2_sum_form`); it is disclosed as a post-hoc
instrument repair and is **not** a pass of I2 as declared.

### 1.2 I3 failed its rounding leg and passed its basis leg

`Σ c_mon − c_ann` = +0.02 / −0.01 / +0.02 GWh against a ±0.01 bar — the bench stores `c_mon` at two
decimals, so twelve roundings can sum to 0.06; the bar was mis-sized, and that is reported rather
than the bar moved. The leg the consequence was about — *is the meter facility-level gross × 1.0?* —
holds at **3e-6** relative in every year (`c_ann` 5,321.4 / 4,240.9 / 4,861.8 GWh vs facility
gross 5,321.416 / 4,240.907 / 4,861.803), and the unit-level file sums to the **identical** figure.

## 2. The decomposition (pre-registered instrument), GWh, gross basis on both sides

`X = M − C2 = T_stat + T_bench + T_in + T_cap` (identity residual 0.00 in every month).

| year | month | **M** meter | **C2** LP ceiling | **X** | **T_stat** | **T_bench** | **T_in** | **T_cap** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | Jul (control) | 608.52 | 604.13 | **4.39** | **204.53** | 0.00 | 0.00 | −200.13 |
| 2024 | Jul | 430.44 | 409.25 | **21.19** | **138.55** | 0.00 | 7.19 | −124.55 |
| 2024 | Aug | 277.01 | 227.36 | **49.65** | **76.97** | 0.00 | 5.66 | −32.98 |
| 2024 | Sep | 445.52 | 389.76 | **55.76** | **131.95** | 0.00 | 0.00 | −76.19 |
| 2025 | Jun | 415.44 | 389.76 | **25.68** | **131.95** | 0.00 | 0.00 | −106.28 |
| 2025 | Jul | 476.82 | 402.75 | **74.07** | **136.35** | 0.00 | 0.00 | −62.28 |
| 2025 | Aug | 580.05 | 506.69 | **73.36** | **171.54** | 0.00 | 0.75 | −98.92 |

Three statements, in order of load-bearing:

1. **The two CAMPD downloads agree exactly.** `M` (bench, facility-level) = facility-file monthly sum
   = unit-file monthly sum in all 36 months; the unit-level file carries exactly U001–U003. The
   handoff's candidate mechanism — a unit re-id, a partial pull, a late-posted unit — does not exist
   at this plant. **P1 is dead.**
2. **The extract is faithful to its source.** Re-running `_unit_year_grid` +
   `detect_outages_eventbased(174.2 MW, 120 h, cf 0.02)` on the committed `NY_2024` / `NY_2025`
   unit-level files reproduces every committed 57185 window (I4), and the units the extract marks
   OUT reported ≤ 0.34 GWh inside their windows in any scored month. The 13-month U003 dark span
   (2024-07-15 → 2025-08-13) is real in the CEMS record. **P2 is dead**, and the nyiso-211
   handoff's "cross-unit window sums exceeding the plant" question is answered: only ONE overlay
   file carries 57185 (zero rows in the layup, e923, short and partial files — no cross-file
   stacking), and the only cross-row artifact is the three boundary days of §1.1.
3. **`T_stat` is the excess, and it is a Jun–Sep phenomenon.** Off-summer `T_stat` runs 9–28 GWh a
   month (a 3.5 % WEFOR residual on the ceiling); in Jun–Sep it runs **77–205 GWh** — and every
   scored month is a Jun–Sep month. `T_cap` is negative throughout: the blocks that ran averaged
   below 362.3 MW, so nothing here is a per-block share story.

## 3. POST-HOC: the summer leg, named to six decimals

**Not pre-registered. Decides no declared verdict.** Reads the keeper rebuild's own availability
array divided by the loader's unit-outage factor — a window-free quantity — by month:

| basis | Jan–May, Oct–Dec | Jun–Sep | identity |
|---|---:|---:|---|
| statistical factor at 57185, all three years | **0.965000** | **0.747075** | `0.747075 − 0.965 × (1016.1 / 1312.5)` = **0.000000** |

So the summer level is exactly `(1 − WEFOR) × net_summer / nameplate` with EIA-860's 1,016.1 /
1,312.5 for Cricket Valley — `cc_summer_derate_ratio` (`campd_bins.py` L2007) applied by
`arrays.py` ~L831–836 under `cc_nameplate_summer_derate=True`. The construction, in order:

1. **`fleet_to_bins` rescales every CC plant to NAMEPLATE** — `cap = cap / ratio`
   (`campd_bins.py` ~L2298–2323: *"the availability builder reapplies the per-plant summer derate
   seasonally"*). Cricket Valley: 1,016.8 (fleet net-summer) → 1,312.5.
2. **`_reconcile_cc_capacity` CAPS it to the CAMPD p99.9** — `campd_bins.py` ~L2462, whose own
   comment says *"applied after the summer-derate nameplate rescale above, so a demonstrated-peak
   CAP row … bounds the final LP capacity"*. Table row: `current_mw 1312.5, campd_p999_mw 1086.9,
   reconciled_mw 1086.9, mode cap`. Capacity is now 1,086.9 in every hour.
3. **The availability leg still multiplies Jun–Sep by `net_summer / nameplate`** — 0.774171 — a
   ratio whose denominator (nameplate) is no longer the capacity it multiplies. Summer capability:
   `1,086.9 × 0.774171 = 841.4 MW`, where the design intent of step 1 was **1,016.1** (net summer)
   and the plant's measured summer p99.9 over 2023–2025 is **1,078 MW gross**.

The caiso-186 `cc_winter_capability_basis` note in the same block states the invariant this breaks:
*"the two ratios are read from ONE helper so this rescale and the availability legs can never
drift apart"*. A `cap` row makes them drift apart by construction — by `ratio × (nameplate −
reconciled)` = 0.774 × 225.6 = **174.7 MW** here.

**Sign-definite, price-free consequence at 57185** (`cricket_valley_ceiling_counterfactual`): the
meter exceeds the LP's summer ceiling in **1,346 / 2,123 / 2,225** summer hours of 2023 / 2024 /
2025 (220.8 / 222.0 / 292.3 GWh). Holding every window and the WEFOR fixed and replacing only the
summer multiplier by `min(1, net_summer / capacity_actually_carried)` = 0.934861, those fall to
**804 / 1,370 / 1,638 hours (33.8 / 32.4 / 38.1 GWh)**, and the over-ceiling *months* fall from
seven to **one (Aug 2024)**. The residual — a plant whose measured summer p99.9 (1,078) exceeds its
EIA net-summer rating (1,016) by 6 %, under a further 3.5 % WEFOR on a capacity that is already the
demonstrated peak — is a rule-14 question about what "summer capability" should be measured *as*,
and is named in §7, not pursued.

## 4. Class census — the same seam at every reconciled NYISO CC_REGULAR plant

`_nyiso212_summer_seam_census.json`, 2023–2025, bench net basis (facility gross × the pooled
parasitic factor; 1.0 at every plant listed). *Constructed* = `pmax_LP × net_summer / nameplate`;
*design* = `min(net_summer, pmax_LP)`; meter columns are shown only for single-bin facilities
(2500, 50292, 50744, 54808 carry other bins and their facility meter is not comparable).

| plant | mode | pmax LP | nameplate | net summer | constructed summer | design summer | **lost to seam (MW)** | meter summer p99.9 | summer h meter > constructed | > design |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **57185 Cricket Valley** | cap | 1,086.9 | 1,312.5 | 1,016.1 | 841.4 | 1,016.1 | **174.7** | 1,078 | 1,906 | 503 |
| **55405 Athens** | cap | 1,064.7 | 1,221.6 | 984.4 | 858.0 | 984.4 | **126.4** | 1,064 | 2,351 | 1,635 |
| **56940 CPV Valley** | cap | 696.1 | 770.5 | 654.2 | 591.0 | 654.2 | **63.2** | 678 | **8,096** | 1,369 |
| 54574 Saranac | cap | 251.5 | 285.6 | 237.8 | 209.4 | 237.8 | 28.4 | 250 | 304 | 176 |
| 7314 Flynn | cap | 108.2 | 170.0 | 139.5 | 88.8 | 108.2 | 19.4 | 102 | 2,139 | 0 |
| 50978 Carr Street | raise | 80.0 | 122.6 | 93.0 | 60.7 | 80.0 | 19.3 | 70 | 1,960 | 1 |
| 54593 Batavia | cap | 42.9 | 66.2 | 48.8 | 31.6 | 42.9 | 11.3 | 37 | 287 | 0 |
| 54592 Massena | cap | 53.6 | 102.1 | 81.0 | 42.5 | 53.6 | 11.1 | 53 | 512 | 4 |
| 54034 Rensselaer | cap | 78.0 | 88.2 | 79.4 | 70.2 | 78.0 | 7.8 | 77 | 508 | 0 |
| 50744 Sterling† | cap | 43.9 | 64.2 | 54.8 | 37.5 | 43.9 | 6.4 | — | — | — |
| 10620 Carthage | cap | 53.6 | 62.9 | 61.1 | 52.1 | 53.6 | 1.5 | 55 | 34 | 16 |
| 10190 Castleton | cap | 71.2 | 72.0 | 67.0 | 66.3 | 67.0 | 0.7 | 69 | 30 | 27 |
| 56234 Caithness | raise | 361.7 | 348.9 | 317.3 | 328.9 | 317.3 | −11.6 | 348 | 1,772 | 3,151 |
| 55375 Astoria Energy | raise | 610.4 | 595.0 | 558.0 | 572.4 | 558.0 | −14.4 | 1,243‡ | — | — |
| 56196 Zeltmann | cap | 560.0 | 528.0 | 474.0 | 502.7 | 474.0 | −28.7 | 700‡ | — | — |

† multi-bin facility. ‡ facility meter roughly 2× the bin — the nyiso-211 §2 I1 object at Astoria
(and the same signature at Zeltmann); not comparable, reported not used.

**Totals:** 23 CC_REGULAR plants, 12 `cap` rows, 3 `raise` rows, **470.2 MW of Jun–Sep capability
removed by the seam** at the cap plants; the meter exceeds the *constructed* summer ceiling at
**17 of 19** single-bin plants and the *design* ceiling at 14 (the WEFOR-on-demonstrated-peak
residual of §3). The 8 unreconciled plants read constructed = design to 0.1 MW — for them the
fleet's net-summer sum equals EIA-860's, so the seam is **exactly** the reconciled set, which is
the footprint any repair would carry. Under `raise` the sign reverses: the summer multiplier is
applied to a capacity *above* nameplate, so Astoria / Caithness / Zeltmann carry summer capability
**above** their published net-summer rating.

## 5. What this corrects in the standing record

* **nyiso-211 §5's object (A) is re-attributed.** The six 2024/2025 over-ceiling months are not the
  extract-basis repair's construction and not any outage-window's. `unit_outage_extract_basis_share`
  made the contradiction *visible* — by removing the 48.6 %-available phantom at a dark plant, it
  let the summer seam show through in the months when one or two blocks ran hard — but the seam
  is present with the flag off too (Jul 2023 and Aug 2025 read > 1 on the pre-196 basis, and
  the statistical *factor* — 0.965 / 0.747075 — is identical on both bases because neither flag
  touches it; only the hours it multiplies differ).
* **"Cross-unit window sums exceeding the plant" is closed as a mechanism at 57185**: one overlay
  file, three boundary days, 8.4 GWh/yr, none in a scored month — nyiso-211 §6's clip census
  stands and is confirmed from the other direction.
* **CPV Valley 56940**, which nyiso-211 §4.1 separated from Cricket Valley as "old, stable, and
  upstream of every flag this lineage carries", carries the **same seam** (63.2 MW; its meter is
  above the constructed summer ceiling in 8,096 of 8,784 summer hours — i.e. in essentially every
  summer hour it ran). The two plants remain two *dispatch* objects; they share one *construction*
  defect.
* **The reconcile table's own comment** ("bounds the final LP capacity") is true of the capacity
  leg and false of the availability leg; the docstrings of both mechanisms describe the pre-seam
  world.
* **This seam was named before, at CAISO, and NYISO armed the composition anyway — on its own
  evidence, without addressing it.** The `cc_capacity_reconcile` base row (matrix, caiso-185,
  2026-08-09) refused the flag at CAISO *ex ante* on exactly this construction: *"the demonstrated
  peak is a REALIZED OUTPUT and therefore sits on the availability-INCLUSIVE side of pmax ×
  availability, while capacity_mw is the availability-EXCLUSIVE slot the hook writes it into …
  every multiplier between the two — the cc_nameplate_summer_derate seasonal ratio, WEFOR/POF …
  — is applied a SECOND time"*, measured there as 0.76–0.98 of each capped plant's own summer
  output, and it flagged PJM's `reconcile + summer derate` composition as *"a live unmeasured
  exposure"*. NYISO's cell records the flag's promotion by nyiso-188 (2026-09-04, U → K: *"bounds
  the FINAL LP capacity_mw at the CAMPD p99.9 … −740 MW over 12 capped plants … NOT-YET (grade 5,
  fails 3) → CALIBRATED (grade 7, fails 0)"*) with no mention of the summer-ratio stacking, and the
  nyiso-190/191/192 entries adjudicate scope, not this composition. Rule 28(d) is respected in both
  directions: CAISO's `R` transferred nothing to NYISO, and this session's measurement is NYISO's
  own — but the record now shows the same construction measured inadmissible at two ISOs, and
  the NYISO keeper's current determination was reached **with the seam armed**. That is a fact
  about provenance, stated here so it cannot be read as a fit argument later (rule 1: the seam is
  wrong whatever the repair does to any gate).

## 6. Rule 14 / rule 19 reading, stated plainly

Both mechanisms are measured inputs with stated derivations and zero free parameters, and **both
stay**: the demonstrated-peak cap (CAMPD p99.9) and the published net-summer rating (EIA-860) are
each the accurate statement of what they measure. The defect is that the plant's summer capability
is **stated twice** — once as `net_summer` (via a ratio to nameplate) and once, implicitly, as
`reconciled × net_summer / nameplate` — and a `cap` row makes the two statements disagree. Rule 19
`[R-ONE-MECH]` says a phenomenon is stated once; rule 14 says the accurate input stays and the
worse fit is a discovered bug. **The bug is in the seam, not in either input.**

**No offer curve, band multiplier, floor, or adder can reach this**: in 1,906 summer hours the LP
was forbidden by its own bounds from producing what the plant's meter recorded. That is the
structural claim the nyiso-211 handoff asked this session to establish or refute for object (A),
and it is established — with the mechanism corrected from "outage window" to "summer capability
seam".

## 7. What this hands forward

* **The named successor: a construction repair, gated and default-off, that divides the summer
  multiplier by the capacity it actually multiplies** — `min(1, summer_capability / pmax_LP)`
  where `summer_capability` is the plant's net-summer capability before any reconcile (the
  quantity step 1 of §3 rescales *from*). Byte-identical for every unreconciled plant (the ratio is
  then unchanged), 0.9349 instead of 0.7742 at Cricket Valley, deeper at the three `raise` plants.
  Zero free parameters. **BUILT IN THIS SESSION, GATED AND DEFAULT-OFF:**
  `ScenarioConfig.cc_summer_derate_reconciled_basis` (registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` at `False`, so every existing key is byte-stable),
  `fleet/arrays.py::_reconciled_summer_ratios` feeding both `cc_summer_derate_ratio` read sites
  in `_availability_matrix` (the summer leg and the temperature-curve anchor, so the two can never
  disagree), the replay override `--cc-summer-derate-reconciled-basis` on the same recorded bag
  as `--caiso-dsw-daytime-evening-trim` (so a rule-29 arm is provably the keeper recipe plus one
  value), the matrix row + a `U` cell in all seven shards (rule 28(c)), and
  `tests/unit/data/test_cc_summer_derate_reconciled_basis.py` (listed-plant summer ratio moves by
  exactly nameplate / carried; unlisted plant byte-identical; inert without the reconcile; default
  off and cache-key registered). It acts only where BOTH `cc_nameplate_summer_derate` and
  `cc_capacity_reconcile` are armed and only at the plants the table lists. Its **rule-29 screen is
  pre-registered separately** (`PREREG-nyiso212-summer-seam-screen.md`), the screen year chosen by
  the mechanism's own measured footprint (§4's table; the seam is a constant MW, so the footprint
  is the summer over-ceiling energy: 2025 at 57185, 292 GWh) — and only an arm that clears that
  screen and the full 2023–2025 span becomes a candidate to which the owner's formula and D-5(b)
  apply. **Nothing is armed on the keeper here.**
* **A rule-14 question, named and not pursued:** what a CC plant's *summer capability* should be
  measured as, once a demonstrated-peak cap exists. EIA net summer (1,016) sits 6 % below the
  measured summer p99.9 (1,078), and a 3.5 % WEFOR residual sits on top of a capacity that is
  already the demonstrated peak; together they leave 503 / 1,370 / 1,638 summer hours above the
  *design* ceiling (§3). A measured summer p99.9 would be a new derive-script table (rule 23) —
  a different, later object.
* **The three `raise` plants' summer over-statement** (§4) is the seam's other sign and belongs to
  the same repair.
* **Object (B)** — the merit / offer-position deficit outside the summer months — is **untouched**,
  as the handoff instructed: it is not to be levered until (A) is separated, and (A) is now
  separated and named.
* **No owner card is opened.** Nothing here needs a ruling: the seam is a code construction with
  a zero-DOF repair, and the five pending rulings are not touched.

## 8. Reported at full magnitude — measured, not the finding

* **Off-summer `T_stat`** is 9–28 GWh a month at 57185 (a flat 3.5 % WEFOR on a capacity that is
  already the CAMPD p99.9); the meter exceeds the off-summer LP ceiling in **1,058 / 919 / 998
  hours**. Small, named, not pursued (it is the §7 rule-14 question's other half).
* **I2 and I3 both failed their declared bars** (§1.1, §1.2); neither failure touches the
  load-bearing terms, and neither bar was moved.
* **P3's declared object was wrong** (per-block share); the correction is in §1, in the open.
* **Aug 2024 remains an over-ceiling month even under the design summer multiplier** (§3): with
  U003 dark all month and U001 out Aug 1–27, the meter's 277 GWh sits just above what two
  blocks at net-summer rating could make. This is the one month where the handoff's original
  "window" framing keeps a small residual; it is ~3 GWh against the seam's 50 GWh there.

## 9. Environment and pre-existing state (rule 25 `[R-ISO-SCOPE]`: re-measured, not repaired)

* **G-DRIFT:** `scripts/probes/nyiso196_rebuild_checks.py --year 2024` reproduces its committed
  record at this HEAD (`git status --porcelain -uno` empty afterwards). I1 adds that the nyiso-211
  arm-basis monthlies reproduce to 0.046 GWh — the same instrument, three years.
* **Pre-existing failures at this HEAD, re-measured:** the six charter test files plus
  `tests/scoring/test_gate_a_provenance.py` read **37 failed / 93 passed** (nyiso-211 read 37 / 80
  over the six alone; the +13 passes are the provenance file's other tests).
  `test_gate_a_provenance::test_live_board_passes` still fails on **MISO's** stale gate-(a) stamp.
  **Neither is this lane's to fix.**
* `main` moved 21 commits between the handoff's `39e7f30b` and this branch's base `abdd30c9`;
  none touches a NYISO file or any file this session read (only `calibration-complete.json`
  re-serialised, NYISO entry unchanged: `complete` on `2026-09-06-nyiso-202-startup-aware`,
  `final` absent).

## 10. Governance

| item | state |
|---|---|
| **Rule 1 `[R-STRUCT]`** | a structural mis-specification named and measured; no residual optimized, no mechanism armed or disarmed |
| **Rule 14 `[R-ACCURATE]`** | both measured inputs **stay**; the worse fit is a discovered construction bug, routed to a zero-DOF repair |
| **Rule 19 `[R-ONE-MECH]`** | the defect *is* a rule-19 violation — one phenomenon stated twice — and is named as such |
| **Rule 22 `[R-HOLDOUT]`** | in-sample years only; 2022 not read; no marker byte moved |
| **Rule 29 `[R-SCREEN]`** | step 0 only; footprint measured (§4); the screen is pre-registered separately, its year by footprint; no bundle, so (c) has nothing to delete |
| **Rule 15 `[R-DASHBOARD]`** | no run produced, nothing to register |
| **Rule 28 `[R-MECH-MATRIX]`** | NYISO shard stamped in this session; **no cell verdict letter moves** — `cc_nameplate_summer_derate`, `cc_capacity_reconcile`, `unit_outage_extract_basis_share` stay `K` with the seam recorded; key set verified identical to `main` (306 cells) |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only; MISO's gate-(a) failure reported, not touched |
| **Rule 27 `[R-PUSH]`** | files ≥ 300 lines pushed are blob-verified after push |
| **Markers / keeper / gates** | untouched; D-5(b) does not attach (no candidate) |
| **Owner rulings** | all five stay UNRULED; none prejudged |

---

*(nyiso-212, 2026-09-07. The preferred answer and the answer declared to hurt it were both
falsified by the same table; the third outcome fired and its object was corrected in the open. A
clean negative on the outage-window framing, and a two-mechanism seam measured to six decimals
that no offer curve can reach.)*
