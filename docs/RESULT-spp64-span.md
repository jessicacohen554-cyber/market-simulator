# RESULT — SPP-64 SPAN shard. `st_gas_mustrun_per_plant` on SPP's ST_GAS fleet, 2023–2025.

**Lane** SPP-64 SPAN · **Branch** `claude/spp64-span` · **Pin**
`c7b42eca7a689aac80fded16fc306745cb460c4e` (verified at session start; no `fetch`/`pull`/`rebase`
before the final push) · **Charter** `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`
· **Screen** `docs/handoffs/RESULT-spp64-screen-2023.md` (six of six §6 STOP gates PASS) ·
**Registered run** `2026-09-10-spp-64-stgas-selfcommit` · **Control**
`2026-09-10-spp-62-vintage-census` / `results/calibration/spp62_span`, **differenced, never
re-solved** (rule 29(b) form 4).

**SCORER'S DETERMINATION: `CALIBRATED`** — grade 7 of 8, **0 fails**, 1 ledgered caveat (C3c).
SPP's first CALIBRATED determination.

**THIS LANE'S PROMOTION RECOMMENDATION: RECOMMEND PROMOTION — with a named, unresolved rule-17
defect that the promotion does NOT fix and that this lane refuses to absorb.** §4 is the whole of
the case against, stated before the case for. **Promotion is the OWNER's call (rule 31
`[R-RETAIN]`); this lane recommends and has not acted** — `frontend/data/backcast/keepers/SPP.json`
is UNTOUCHED and no `complete` marker or `frontier` declaration was added.

---

## 1. The solve

ONE invocation, three years, sequential in one process (rules 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]`):

```
python3 scripts/replay_keeper.py results/calibration/spp62_span \
  --years 2023 2024 2025 --out-dir results/calibration/spp64_span \
  --set st_gas_mustrun_per_plant=true
```

Exit 0, **12 min 5 s** wall (16:44:44 → 16:56:49 UTC) — longer than the charter's ~440 s estimate,
which was extrapolated from the screen's single warm year. `results/calibration/spp64_*/` is
gitignored (`.gitignore:1914`), which is what discharges rule 29(c). **Nothing was deleted**
(rule 31 `[R-RETAIN]`). The parent ran the solve as the shard it is; no LP ran outside it.

**Config identity — exactly ONE live field moves.** 838 `scenario_config` keys compared against the
keeper's committed `run_config.json`; **4 differ**:

| field | keeper | ARM | reading |
|---|---|---|---|
| **`st_gas_mustrun_per_plant`** | **False** | **True** | the arm |
| `nyiso_total_east_cutset_ttc` | *absent* | False | added since the keeper solved; declared default |
| `spp_curtailment_ceiling` | *absent* | False | added since; declared default, gate OFF |
| `spp_curtail_depth_wind` | *absent* | 0.288137 | read only under the above, which is False |

`st_gas_mustrun_p25_level` is **False** in both, and `offer_curve_by_group` is **byte-identical** —
the authorized price-tuning channel was not touched, re-cut or swept (rule 1 `[R-STRUCT]` (c)).
These are the same three non-target fields the screen's G-1 found, at their declared defaults, i.e.
PRECOMMIT §7's G-DRIFT INERT hunks materializing.

## 2. THE SCORER — every criterion, every year, at full magnitude

| criterion | tier | keeper | **ARM** |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | **FAIL** | **PASS** |
| C2 system volume (gas/coal) | LOAD | PASS | PASS |
| C3a mean LMP | LOAD | PASS | PASS |
| C3b price duration/shape | LOAD | PASS | PASS |
| C3c price tail / scarcity | SUPP | **FAIL** | **CAVEAT** *(ledgered, rule 22 `[R-C3C]`)* |
| C4 fleet hourly dispatch corr | SUPP | PASS | PASS |
| C6 governance gate | PROT | PASS | PASS |
| C8 forced-energy share (D-2) | PROT | PASS | PASS |
| **determination** | | **NOT-YET** | **CALIBRATED** |
| grade / fails / ledgered | | 6 of 8 · 2 fails · 0 | **7 of 8 · 0 fails · 1** |
| D-10 free-class C1 | | all 14/16 · free 10/12 | **all 16/16 · free 12/12** |

### C1 — every scored row (band ±8.00 TWh & ±3 pp)

| yr | class | actual | keeper | Δ | | **ARM** | **Δ** | | k pp | a pp |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | **ST_GAS** | 15.020 | 6.640 | **−8.380** | FAIL | **8.986** | **−6.034** | **PASS** | −2.94 | **−2.12** |
| 2023 | CC_REGULAR | 45.694 | 42.125 | −3.569 | PASS | 41.567 | −4.127 | PASS | −1.25 | −1.45 |
| 2023 | COAL_PRB | 65.279 | 66.877 | +1.598 | PASS | 65.805 | **+0.526** | PASS | +0.56 | +0.18 |
| 2023 | CT_PEAKER | 13.214 | 15.621 | +2.407 | PASS | 15.095 | **+1.881** | PASS | +0.85 | +0.66 |
| 2023 | COAL_LIGNITE | 9.396 | 7.293 | −2.103 | PASS | 7.193 | −2.203 | PASS | −0.74 | −0.77 |
| 2023 | CC_CHP | 1.737 | 1.853 | +0.116 | PASS | 1.848 | +0.111 | PASS | +0.04 | +0.04 |
| 2023 | ST_CHP | 0.533 | 0.303 | −0.230 | PASS | 0.293 | −0.240 | PASS | −0.08 | −0.08 |
| 2023 | COAL_BIT | 0.035 | 0.000 | −0.035 | PASS | 0.000 | −0.035 | PASS | −0.01 | −0.01 |
| 2024 | **ST_GAS** | 20.098 | 10.386 | **−9.712** | FAIL | **12.675** | **−7.423** | **PASS** | −3.34 | **−2.55** |
| 2024 | CC_REGULAR | 45.894 | 41.908 | −3.986 | PASS | 41.365 | −4.529 | PASS | −1.38 | −1.57 |
| 2024 | COAL_PRB | 59.953 | 61.718 | +1.765 | PASS | 60.715 | **+0.762** | PASS | +0.59 | +0.25 |
| 2024 | CT_PEAKER | 15.908 | 18.633 | +2.725 | PASS | 17.999 | **+2.091** | PASS | +0.93 | +0.72 |
| 2024 | COAL_LIGNITE | 8.669 | 6.638 | −2.031 | PASS | 6.567 | −2.102 | PASS | −0.70 | −0.72 |
| 2024 | CC_CHP | 1.869 | 1.888 | +0.019 | PASS | 1.885 | +0.016 | PASS | +0.01 | +0.00 |
| 2024 | ST_CHP | 0.525 | 0.175 | −0.350 | PASS | 0.172 | −0.353 | PASS | −0.12 | −0.12 |
| 2024 | COAL_BIT | 0.035 | 0.000 | −0.035 | PASS | 0.000 | −0.035 | PASS | −0.01 | −0.01 |

**2025 C1 is SKIPPED for every class** on both runs — preliminary EIA-923 vintage (ST_GAS
16/36 prior plants missing, 56 % reporting) — exactly as on the keeper. Not a change and not a claim.

**Both failing rows close, and they close on the volume AND the share leg.** The bar the PRECOMMIT
§10 pre-stated was **+0.38 TWh (2023)** and **+1.71 TWh volume plus +0.3 pp share (2024)**; realised
**+2.346** and **+2.289 TWh**, and share_pp **−2.94 → −2.12** and **−3.34 → −2.55**. Two neighbours
also move *toward* their actuals rather than away — COAL_PRB +1.598 → +0.526 (2023) and
+1.765 → +0.762 (2024), CT_PEAKER +2.407 → +1.881 and +2.725 → +2.091 — so the displacement
§6's G-6 was watching for landed on the two classes that were carrying surplus, which is where the
pre-solve arithmetic said the energy had to come from.

### C2 / C3a / C3b / C3c / C4 / C8

| | 2023 keeper → ARM | 2024 keeper → ARM | 2025 keeper → ARM |
|---|---|---|---|
| **C2 gas** | `C1 flags: ST_GAS` → **all classes in band** | `C1 flags: ST_GAS` → **all in band** | SKIPPED −21.7 % → −20.5 % |
| **C2 coal** | all in band → all in band | all in band → all in band | SKIPPED +7.7 % → +6.5 % |
| **C3a** (bar ±10 %) | +2.1 % → **+1.0 %** | +1.3 % → **+0.1 %** | +2.2 % → **+0.7 %** |
| **C3b** NRMSE (bar ≤0.20) | 0.172 → 0.173 | 0.172 → **0.171** | 0.167 → **0.163** |
| **C3c** >$200 h | 0 vs 42 → **0 vs 42** | 5 vs 59 → **5 vs 59** | 0 vs 68 → **0 vs 68** |
| **C4 gas** | r 0.960/0.192 → 0.959/**0.188** | 0.951/0.201 → 0.951/**0.197** | 0.949/0.253 → 0.950/**0.243** |
| **C4 coal** | r 0.949/0.161 → **0.951**/0.162 | 0.917/0.209 → **0.919**/0.209 | 0.912/0.177 → **0.914**/**0.174** |
| **C8 ST_GAS** | 0.0 % → **19.6 %** | 0.0 % → **18.5 %** | 0.0 % → **17.4 %** |
| **C5a** CO2 (reported-only) | −1.7 % → −1.8 % | −1.2 % → −1.4 % | +2.9 % → +2.8 % |

**C3a improves in all three years and C3b in two of three.** Reported because it is true, and
explicitly **not** claimed as evidence for the mechanism: no gate in the charter read the price
level, and rule 1 `[R-STRUCT]` forbids judging a structural mechanism by whether the residual moved.

**C3c is UNCHANGED at full magnitude — 0 / 5 / 0 model hours above $200 against 42 / 59 / 68
actual.** Not one hour moved. Its status changed only because `_apply_c3c_standing_rule`
reclassified it once C1 closed and it became the **lone** failure. The determination flip is
therefore **entirely** C1's doing; C3c's own miss is exactly as large as it was on the keeper, and it
remains `FINDING-spp-64`'s R-bd (an absent tail that is congestion rent, not reserve scarcity).
The system price max is byte-identical in all three years (59.313 / 2000.000 / 73.773), which is the
mechanical reason no tail hour could have moved.

**Slack and dump are byte-identical to the keeper**: dump 0.000 MWh in every year; slack 0.000 /
**370.102** / 0.000 MWh — the 2024 value matching the keeper's own two zone-hours at VOLL to three
decimals. Energy conservation across the class table: **+0.0009 / −0.0013 / −0.0008 TWh**.

## 3. THE GROSS CLASS DELTAS (`hourly/class_hourly_<y>.parquet`, P1, TWh)

| class | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---|---|---|
| **ST_GAS** | **+2.3314** | **+2.2886** | **+2.5736** |
| COAL_PRB | −1.0717 | −1.0027 | −0.8208 |
| CC_REGULAR | −0.5633 | −0.5456 | −0.8665 |
| CT_PEAKER | −0.5560 | −0.6394 | −0.7044 |
| COAL_LIGNITE | −0.1009 | −0.0704 | −0.1489 |
| ST_CHP | −0.0101 | −0.0108 | −0.0073 |
| CC_CHP / CT_CHP | −0.0058 / −0.0075 | −0.0037 / −0.0064 | −0.0131 / −0.0054 |
| **wind** | **−0.0150** | **−0.0106** | **−0.0071** |
| solar | −0.0001 | −0.0003 | −0.0008 |
| nuclear / hydro / biomass / OTHER / oil | 0.0000 | 0.0000 | 0.0000 |
| **TOTAL** | **+0.0009** | **−0.0013** | **−0.0008** |

The increment is paid by coal and the two other gas classes, **not** by curtailing renewables — wind
moves 0.013 % / 0.009 % / 0.006 %. The 2023 column reproduces the screen shard's §3(a) table
class-for-class to four decimals, which independently confirms the span solved the same
configuration rather than a drifted one.

## 4. THE THREE ADJUDICATIONS THE CHARTER ROUTED HERE

### (i) D-4 UNIT-CONDUCT RIDER — **IT RECURS, IN ALL THREE YEARS.** This is the adverse finding.

| year | conduct rows | pass | **FAIL** | failed TWh | mechanism forced TWh | **% of forced energy** |
|---|---|---|---|---|---|---|
| 2023 | 19 | 15 | **4** | 0.0595 | 2.3238 | **2.56 %** |
| 2024 | 20 | 15 | **5** | 0.0763 | 2.3398 | **3.26 %** |
| 2025 | 20 | 17 | **3** | 0.0216 | 2.5291 | **0.85 %** |

**The keeper carried ZERO conduct FAILs in every year** (2 rows/yr, both `chp_steam`, both pass).
`D4.passed` goes **True → False**, and the run prints "legitimacy diagnostics gate FAIL".

| year | failing plants |
|---|---|
| 2023 | 1230, 1235, 1271, 3008 |
| 2024 | 1230, 1235, 1271, 3008, **6193** |
| 2025 | 1230, 1235, 1271 |

**Plants 1230, 1235 and 1271 fail in ALL THREE YEARS.** Their measured median output over the hours
the floor actually binds for them is **0.000 MW**, with 59–83 % of those hours metered at exactly
zero (worst: 1271 in 2024 at 77.3 %, 1235 in 2025 at 82.6 %). Rule 17 `[R-FLOOR-WINDOW]`: *"A floor
binding in hours its own driver evidence says the class is offline is a bug by definition, whatever
it does to the residual."* This is that signature, at the per-unit grain, and it is **persistent
rather than a single-year artifact**.

**What it is, mechanically.** It is a **window** defect, not a level or membership accident: the
mechanism's hypothesis is *"a self-committing utility steam plant runs in the system's top-load
hours"*, and the meter verifies that for 15/19, 15/20 and 17/20 plants and **falsifies it** for
these three-to-five. Their own `online_frac` is real, but their operating hours are not top-load
correlated, so placing their floor by system-load rank puts it in hours they are dark.

**Three things stated so the finding is neither inflated nor buried.** (a) The **class-level** D-4
window leg PASSES — `offwindow_share` **0.0000** in all three years, self-windowing at h0-23 exactly
as the PRECOMMIT predicted; it is only the per-unit rider that fires. (b) The magnitude is
**0.85–3.26 %** of the mechanism's forced energy — the mechanism is overwhelmingly clean, and
0.0216–0.0763 TWh is not what moved C1 by 2.3 TWh. (c) **It never reached the determination**, and
that is the uncomfortable part, not a defence: `_score_forced_share` consults `_d4_provenance` ONLY
for a class ABOVE its cap, ST_GAS came in under (§ii), so **C8 passed on the share alone and the
scorer never looked at the rider.** The `CALIBRATED` headline in §2 was produced by a code path that
did not examine this defect. Anyone quoting the determination should know that.

### (ii) RULE 20 `[R-FORCED-BUDGET]` — **UNDER budget in all three years**

| year | ST_GAS forced | class total | **forced share** | cap | verdict |
|---|---|---|---|---|---|
| 2023 | 2.3238 | 11.8466 | **0.1962** | 0.30 | under |
| 2024 | 2.3398 | 12.6553 | **0.1849** | 0.30 | under |
| 2025 | 2.5291 | 14.4998 | **0.1744** | 0.30 | under |

ST_GAS is **not** in `d2_exempt_classes`, so this is a real test and not an exemption. The share
*falls* across the span as the class total grows. **C8 PASSES**, and the PRECOMMIT §6's pre-declared
"KNOWN OPEN RISK" — that ST_GAS would carry roughly a third of its energy at a binding floor — **did
not materialise in any year**; the charter's projection was ~0.33 and the measured values are
0.17–0.20. Consequently the rule's conditional-pass limb (provenance + shape) is never reached, and
the question the charter flagged — whether a 100 %-regulated class is a "merchant" class within the
rule's own words — **does not need deciding on this run**. It is left open rather than answered by a
lane that did not need to answer it.

Every other class is unchanged at **0.0 % forced** (CC_REGULAR, COAL, CT_PEAKER, hydro), so the arm
added forcing to exactly one class — rule 19 `[R-ONE-MECH]` holds on the solved artifact, not just
on the pre-solve census.

### (iii) D-1 DIURNAL SHAPE — **passes in all three years, and the shape gets BETTER**

| year | keeper `profile_r` | **ARM** | keeper `cv_ratio` | **ARM** | bars |
|---|---|---|---|---|---|
| 2023 | 0.996 | **0.997** | 2.161 | **2.117** | r ≥ 0.80, cv ≥ 0.50 |
| 2024 | 0.999 | **0.999** | 2.060 | **1.844** | |
| 2025 | 0.992 | **0.997** | 2.244 | **1.717** | |

`D1.passed = True`. The PRECOMMIT called D-1 "the genuinely uncertain leg"; it is not close to its
bars. Worth noting against the gate's one-sidedness: `cv_ratio` moves **toward 1.0** in all three
years (2.244 → 1.717 in 2025), i.e. the model's off-peak ST_GAS variability moves toward the
measured — the gate only requires ≥ 0.50, so this improvement earns the arm nothing, but it is
evidence the floor is reproducing observed conduct rather than flattening it.

## 5. WHAT THIS LANE DID **NOT** DO

No gate or bar was re-cut (§6's six screen gates were the screen's and are not re-read here). The
control was **not** re-solved. `st_gas_mustrun_p25_level` was not armed, `offer_curve_by_group` was
not touched, and **no parameter was added** — the DOF ledger is inherited at **n_entries 3 /
n_residual 2** (`offer_curve_by_group`, `offer_curve_smoothing`, `wefor_multiplier`), verified from
the written attestation. No other ISO's files were written. No `complete` marker, no `frontier`
declaration, no edit to `frontend/data/backcast/keepers/SPP.json`.

Registration used `--no-prune`: SPP has 2 registered runs against a cap of 15, so the sweep is a
no-op either way, and rule 31 `[R-RETAIN]` says nothing is removed while the promotion question is
open — which is precisely the question of *which* of those two runs is the keeper.

## 6. PROMOTION — **RECOMMEND**, and here is the case against it first

**THE CASE AGAINST.** The arm carries a **recurring rule-17 `[R-FLOOR-WINDOW]` defect** on three
plants in every year of the span, and rule 17's own words call that "a bug by definition, whatever
it does to the residual". The `CALIBRATED` determination was reached without the scorer ever
consulting the test that catches it. A lane that wanted this arm promoted could point at 0 fails and
a clean C8 and never mention §4(i) — so the honest reading has to put it first. A defensible owner
decision here is: **refuse promotion, repair the window for the falsified plants, and re-solve**
(~12 min of LP), so that SPP's first CALIBRATED keeper is clean rather than clean-except-for-a-known-bug.

**THE CASE FOR, which is why this lane nonetheless recommends it.** Rule 1 `[R-STRUCT]` says a run
is a keeper because it is **the most structurally faithful**, not because it has the best numbers.
On that test the arm wins and the incumbent does not:

- The incumbent keeper gives SPP's gas-steam fleet **no commitment structure at all** — machine-verified,
  ST_GAS forced 0.0 % and absent from D-2 entirely — for a fleet measured **100.0 % EIA-860 Sector 1
  regulated utility** (9,515 of 9,515 MW). A vertically-integrated utility self-commits its steam;
  modelling it as a merchant that starts and stops against the LMP is a structural error, and it is
  the object `FINDING-spp-46` §0.2 named and left open.
- The arm gets that structure right for **15/19, 15/20 and 17/20** plants and wrong for the rest. The
  comparison is not "clean vs buggy" but **"right on ~80 % of the fleet vs right on none of it"**.
  Reverting to the incumbent to avoid the rider FAILs would trade a 2.3 TWh structural repair for a
  0.02–0.08 TWh defect, and would restore a *larger* rule-17-adjacent error (a class the model runs
  near-dark against a driver that says it is committed).
- It adds **zero free parameters**, arms **one** mechanism on a class that had **none**, takes the
  **smallest** of the three available floor levels (`committed_pct`, the LSL — 9.09 TWh all-on,
  against 14.43 and 23.32 for the alternatives), and leaves the authorized price channel
  byte-identical. There is no fitted quantity anywhere in it.
- Nothing else regressed. C3a improves in all three years, C3b in two of three, C4 in five of six
  rows, slack and dump are byte-identical, and C5a moves ≤ 0.2 pp.

**The recommendation is therefore: promote, and open the window defect as the immediate successor
card — do not absorb it.** The successor is specific: **re-derive the placement rule for plants whose
measured operation is not top-system-load correlated** (1230, 1235, 1271 persistently; 3008 and 6193
in single years). It is explicitly **NOT** a `mustrun_plant_exclusions` job as a first reach —
miso-170's own note warns that excluding a plant that fails a conduct test "would bury that error
inside a membership list", and these plants look like genuine cyclers whose *window construction* is
wrong, which is the error rule 17 exists to surface.

**If the owner prefers the clean-first route, this lane's estimate is ~12 min of LP for a repaired
re-solve of the full span**, and the artifacts to difference against already exist.

## 7. RETENTION — THE BUNDLE DOES NOT SURVIVE THIS CONTAINER (rule 31 `[R-RETAIN]`)

`results/calibration/spp64_span/` is **gitignored and lives only on this container's local disk**,
which is ephemeral and is reclaimed when the session ends. **Nothing was deleted.** What IS committed
and therefore permanent: the bundle's slim files, its `hourly/` sidecars, the registry sidecar,
`runs/2026-09-10-spp-64-stgas-selfcommit.js` and the changed `bench/SPP/` parts — i.e. everything a
later lane needs to difference against this run without re-solving it, exactly as this lane
differenced the keeper.

**The promotion question is put explicitly and is unanswered as this shard reports.** No owner ruling
on promotion had been received at any point in this session.

## 8. Honest limits

- `[R-HOLDOUT]` was removed 2026-09-09, so **no year is protected from having been iterated
  against**. 2023–2025 are all model-**SELECTION** evidence. **`CALIBRATED` here is a determination
  under the rubric, not a certified out-of-sample skill claim**, and nothing in this document should
  be quoted as one.
- **2025 C1 is SKIPPED for every class** (preliminary EIA-923), so the span's C1 verdict rests on
  2023 and 2024. The 2025 ST_GAS number is real dispatch but is scored against nothing.
- The determination flip is **C1's alone**. C3c did not improve by a single hour; it was reclassified
  by a standing rule once it became the lone failure. SPP's absent price tail is exactly as absent as
  it was on the keeper.
- The C3a/C3b/C4 improvements are **reported, not evidence**: no gate read them, and rule 1 forbids
  treating a residual move as a mechanism's warrant.
- **Both runs were scored by the SAME scorer at HEAD, rubric v3.7.** The keeper's *committed*
  `metrics.json` is stale at v3.6 (and records C6 UNATTESTED), so every keeper number quoted above is
  from a **live re-score at v3.7 in this session**, not from that sidecar — otherwise the comparison
  would not be apples-to-apples. v3.7's only change is the **holdout-year** C3c limb, which cannot
  apply here: all three years are in-training, and v3.7 explicitly leaves the in-training
  lone-failure guard untouched. **The `CALIBRATED` is therefore not an artifact of a recent rubric
  loosening** — it is the v3.2/v3.3 in-training path, reached because C1 closed.
- **Noted, not fixed, and not this lane's**: the committed `frontend/data/backcast/rubric-consts.js`
  still declares `rubricVersion: 3.6` against a scorer at 3.7. `build_manifest.py` regenerates it
  (42 runs, SPP present), but the refresh is unrelated drift from another lane's scorer change, so it
  was reverted rather than swept into this shard's commit. The Pages deploy regenerates it anyway.
  `check_registry_payload_parity.py` is **green** after this registration: 42 runs checked, 74 bundle
  dirs swept, 0 known-unsynced tolerated.
