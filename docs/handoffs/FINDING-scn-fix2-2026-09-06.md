# FINDING — SCN-FIX2: the carbon ladder is switched to the committed RFF path form (S3), and the voluntary levels are relabelled COMMITTED (S9 / S10)

**Lane:** SCN-FIX2 — SCN-FIX1's items 3 and 4, re-chartered whole after FIX1 landed on the r#10
text (desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#12, §4, §5 issuance).
**Model:** Opus `claude-opus-5`. **DATA PROFILE:** `code` (not hydrated — this lane reads no
`data/raw`). **Branch:** `claude/scn-fix2-carbon-form-relabel-lurf5k` (the harness assigned this
stem in place of the ledger's nominal `…-v8kq`; the mismatch every SCN lane has recorded).
**Base:** `origin/main` `47e306d3`. **Solves: ZERO** — no LP of any kind ran, so rule 29
`[R-SCREEN]` has no screen to gate and clause (c) DELETE-BEFORE-MERGE has no bundle to reach.
**Registrations: none.** No mechanism was added or tested, so rule 28 `[R-MECH-MATRIX]` duty (b)/(c)
is not triggered (`carbon_price_path` and `voluntary_clean_demand` already carry their rows and
cells; no shard is edited).

**Commits:** `725a0d85` (item 3, the YAML form switch + its test pin), `428549ac` (item 4, the
relabel), then this document.

---

## 0. Bottom line

**Both records edits are executed exactly as chartered, and the whole lane moves no model number.**

| | what | measured result |
|---|---|---|
| **item 3** | the four carbon rows + ALL-CLEAN's carbon component switch from the interim additive `carbon_price_delta` {15, 25, 50} to the committed RFF path ladder `carbon_price_path: low/mid/high` (ruling **S3**, unblocked by SCN-WS1c landing **S2**'s floor) | the resolved-carbon table, §1 — `mid` on ERCOT/PJM/MISO is **0 / 3.75 / 7.50 / 11.25 / 15.00** across 2026-2030, and every arm on CAISO/NYISO/NEISO is **identical to REF** in that window |
| **item 4** | `f_commit` mid 0.5 and the WTP ceiling $4.5/MWh stop being ILLUSTRATIVE and become **committed** (**S9**); the eligible-set default stops being a RECOMMENDATION and becomes the **ruled** default (**S10**) | **words only** — both files are line-for-line identical once trailing comments are stripped (§2); every `VOLUNTARY_*` key and value unchanged |
| **keys** | a case override never touches a base, keeper or pin key | **3/3 pins, 18/18 committed keeper `run_config.json`, 12/12 REF bases byte-identical**; exactly the **30** keys of the five re-formed cases move (5 × 6 ISOs), and **no committed bundle exists for any of them** (§3) |

**One measured result the charter did not predict, and it is the load-bearing one for the policy
lanes.** "Exactly inert on CAISO/NYISO/NEISO" is a **T1-F fact, not a horizon fact.** Over the
2026-2050 base the `high` path crosses **above** the state-program trajectory on **NYISO in
2031-2047** (peak **+$9.05/tCO2** at 2040) and on **NEISO in 2033-2042** (peak **+$3.32/tCO2** at
2038). CAISO stays inert in all 25 years, and `low` / `mid` stay inert in all 25 years on all three.
A full-horizon `CARB-HI` is therefore a **LIVE arm on NYISO and NEISO** and must not be killed by an
inertness argument carried over from the 2026-2030 window (§1.2). Every crossing delta is
**positive** — under S2's floor no path can cut any ISO's carbon signal in any year, which is the
property the interim additive form was bought to guarantee, now held by the committed form.

**Two things routed to SCN-DESK, neither touched here** (§5): the campaign YAML's *voluntary* and
*cap* comment blocks are stale after S9/S10/S12 but lie outside this lane's regions; and the live
forecast default pin at HEAD is **`547053bdfccd4264`**, not the charter's `e5ecd4105ada3e58` (which
is the pre-D65-B value — both are measured unchanged here, §3.1).

---

## 1. The resolved carbon signal, per case × ISO × year

Measured through the live chain a solve uses — `SweepDefinition.case_configs(base)` →
`apply_iso_scenario_defaults(cfg, iso)` → `policy.carbon.resolve_carbon_price(cfg, year)` — on the
committed `configs/scenarios/<iso>_scenario_base_2026_2030.yaml` REF bases, at commit `428549ac`.
$/tCO2, real 2026$.

| ISO | case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| ERCOT | `REF` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ERCOT | `CARB-LO` | 0.00 | 2.00 | 4.00 | 6.00 | 8.00 |
| ERCOT | `CARB-MID` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| ERCOT | `CARB-HI` | 0.00 | 7.50 | 15.00 | 22.50 | 30.00 |
| ERCOT | `CARB-MID+LOAD-HI` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| ERCOT | `ALL-CLEAN` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| PJM | `REF` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| PJM | `CARB-LO` | 0.00 | 2.00 | 4.00 | 6.00 | 8.00 |
| PJM | `CARB-MID` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| PJM | `CARB-HI` | 0.00 | 7.50 | 15.00 | 22.50 | 30.00 |
| PJM | `CARB-MID+LOAD-HI` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| PJM | `ALL-CLEAN` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| MISO | `REF` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MISO | `CARB-LO` | 0.00 | 2.00 | 4.00 | 6.00 | 8.00 |
| MISO | `CARB-MID` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| MISO | `CARB-HI` | 0.00 | 7.50 | 15.00 | 22.50 | 30.00 |
| MISO | `CARB-MID+LOAD-HI` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| MISO | `ALL-CLEAN` | 0.00 | 3.75 | 7.50 | 11.25 | 15.00 |
| CAISO | `REF` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| CAISO | `CARB-LO` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| CAISO | `CARB-MID` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| CAISO | `CARB-HI` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| CAISO | `CARB-MID+LOAD-HI` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| CAISO | `ALL-CLEAN` | 30.02 | 32.13 | 34.37 | 36.78 | 39.36 |
| NYISO | `REF` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NYISO | `CARB-LO` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NYISO | `CARB-MID` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NYISO | `CARB-HI` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NYISO | `CARB-MID+LOAD-HI` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NYISO | `ALL-CLEAN` | 23.64 | 25.29 | 27.06 | 28.96 | 30.98 |
| NEISO | `REF` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |
| NEISO | `CARB-LO` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |
| NEISO | `CARB-MID` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |
| NEISO | `CARB-HI` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |
| NEISO | `CARB-MID+LOAD-HI` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |
| NEISO | `ALL-CLEAN` | 26.05 | 27.88 | 29.83 | 31.92 | 34.15 |

Two readings, and both are the ruled ones:

* **The three no-program ISOs get the path alone.** The 2026 knot is `0` in every RFF path
  (`constants.CARBON_PRICE_PATHS`: `low` 0 / 8 / 18 / 25, `mid` 0 / 15 / 35 / 50, `high` 0 / 30 /
  70 / 110 at knot years 2026 / 2030 / 2040 / 2050, linearly interpolated), so **no arm separates
  from REF anywhere in 2026** — the axis is live from 2027. The `mid` column is exactly the ladder
  the charter names, to the cent.
* **The three program ISOs are identical to REF, every arm, every year of the T1-F window** —
  ruling S2's floor `max(path, program)` binding on the program side. This reproduces SCN-WS1b's
  measured inertness through the *committed* form rather than the interim one, which is the whole
  point of the switch: the same physical answer, now expressed as the level S3 committed.

### 1.1 Why the switch is a form change and not a level change

S3 committed the plan §3.5 table, and §3.5 writes `carbon_price_path: low/mid/high`. The delta
knots {15, 25, 50} were never a ruled level — plan §3.5 note (iii) calls them "a desk stand-in …
until SCN-WS1c lands S2's floor", and the YAML's own header said so. SCN-WS1c landed the floor on
2026-09-06 (`FINDING-scn-ws1c-2026-09-06.md`: 450/450 predicted cells to the cent, 0 cache keys
moved, `policy_bundle="tight"` an exact no-op on the three program ISOs), which killed **G-C1** at
the resolver — the defect under which an explicit path SUPPRESSED the program and so *cut* carbon
by $16-102/t on CAISO/NYISO/NEISO. With G-C1 dead the committed form is the safe form, and the
stand-in has no remaining job.

The commented-out path block in the YAML is **deleted**, not left dormant (rule 26 `[R-DELETE]`: a
commented-out live form is a re-armable answer). The FIELD `carbon_price_delta` is untouched and
still available for a labelled sensitivity; no campaign case uses it.

### 1.2 THE INERTNESS IS A WINDOW FACT — measured, and it corrects a reading in circulation

Repeating the measurement on the **2026-2050** bases and differencing each arm against its own REF,
year by year (all 25 years, same live chain):

| ISO | arm | years differing from REF | window | peak delta |
|---|---|---|---|---|
| CAISO | `low` / `mid` / `high` | **0 / 0 / 0** | — | — |
| NYISO | `low` / `mid` | 0 / 0 | — | — |
| NYISO | **`high`** | **17** | **2031-2047** | **+$9.05/t at 2040** (+0.85 at 2031, +0.13 at 2047) |
| NEISO | `low` / `mid` | 0 / 0 | — | — |
| NEISO | **`high`** | **10** | **2033-2042** | **+$3.32/t at 2038** (+0.16 at 2033, +1.08 at 2042) |

The program trajectories are convex in the late horizon and the RFF `high` path is steepest in the
2030s, so `high` overtakes NYISO's and NEISO's programs mid-horizon and is overtaken again before
2050. **What follows, stated for the lanes that will read it:**

* the **policy lanes' phase-0 kill of CARB-* on the program ISOs remains correct for Stage A**,
  which is T1-F 2026-2030 — the table in §1 is the evidence, and it is exact (identical to REF, not
  approximately so);
* **a full-horizon campaign must not carry that kill over.** On NYISO and NEISO a 2026-2050
  `CARB-HI` is a live arm with a genuine mid-horizon carbon increment. This does not contradict
  SCN-WS1b (whose measurement was the 2027 leg / T1-F window) — it bounds it;
* **the floor's sign guarantee holds everywhere**: of the 27 differing ISO-years, **all 27 deltas
  are positive**. No path lowers any ISO's carbon signal in any year, which is exactly the
  invariant `policy.carbon.carbon_path_below_program_warning` exists to trip on.

---

## 2. The relabel — every word changed, and nothing else

Rulings executed: **S9** (2026-09-06, card D-2(b), verbatim *"Take the placeholders as committed"*)
and **S10** (2026-09-06, card D-3c, verbatim *"Ratify the default as built"*).

**`src/market_sim/config/constants.py`, the `VOLUNTARY_*` region only:**

| where | before | after |
|---|---|---|
| region header (~:5065) | "Cells the memo's box 5 leaves OWNER-SET are labelled ILLUSTRATIVE below … so neither may be inferred from a ruling here" | "EVERY LEVEL IN THIS REGION IS NOW COMMITTED", naming S9 verbatim, the values already shipped, and that no number moved |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` block (~:5091) | "*** D-3c IS OPEN (ledger §2): this set is the memo's RECOMMENDATION, not a ruled default. ***" | "*** COMMITTED — owner ruling S10 … 'Ratify the default as built': this set is the ruled default … every eligible unit is credited; there is no additionality or vintage mask ***" |
| `VOLUNTARY_COMMITTED_DC_FRACTION` `mid` narrative (~:5181) | "*** ILLUSTRATIVE, OWNER-SET UNDER D-2 … 0.5 is a placeholder at the range midpoint … it is NOT a ruled level ***" | "*** COMMITTED (owner ruling S9) *** at the range midpoint, the value shipped under the former ILLUSTRATIVE label … a ruled what-if level (rule 1 `[R-STRUCT]`)" — and the memo's "weakest-anchored cell" caveat is **kept**, because the ruling does not change the anchor |
| its trailing comment | `# ILLUSTRATIVE — owner level (D-2), see above` | `# committed (owner ruling S9, 2026-09-06), see above` |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` `mid` narrative (~:5204) | "*** ILLUSTRATIVE, OWNER-SET UNDER D-2 (box 5: 'the ceiling itself is an owner level'…) ***" | "*** COMMITTED (owner ruling S9) *** — the range midpoint, the value shipped under the former ILLUSTRATIVE label … the label moved and the number did not" |
| its trailing comment | `# ILLUSTRATIVE — owner level (D-2), see above` | `# committed (owner ruling S9, 2026-09-06), see above` |

**`src/market_sim/config/scenarios.py`, the three `voluntary_*` field docstrings only:**

| field | before | after |
|---|---|---|
| `voluntary_clean_demand_path` | "TWO CELLS S3 DID NOT REACH stay LABELLED ILLUSTRATIVE (owner-set under D-2 …): f_commit MID (0.5 placeholder) and the WTP-ceiling MID level (4.5 placeholder)" | "THE TWO CELLS S3 DID NOT REACH ARE NOW COMMITTED TOO — owner ruling S9 … at the values already shipped under their former ILLUSTRATIVE label: f_commit MID (0.5) and the WTP-ceiling MID level (4.5). No number moved" |
| `voluntary_wtp_ceiling_usd_per_mwh` | "(low 2.0 / mid 4.5 ILLUSTRATIVE / high 7.0)" | "(low 2.0 / mid 4.5, COMMITTED by owner ruling S9 2026-09-06 / high 7.0)" |
| `voluntary_eligible_fuels` | "*** OWNER BOX D-3c IS OPEN: that default is the memo §4.1 RECOMMENDATION, not a ruled level ***" | "*** COMMITTED: owner ruling S10 … ratifies exactly that set, so it is no longer the memo §4.1 recommendation but the ruled default — every eligible unit credited, no additionality or vintage mask ***" |

**Nothing else in either file is touched** (rule 27 `[R-PUSH]`'s model-assignment half is satisfied
— this is an Opus session — and both files are edited in place with the Edit tool, never rewritten
from regenerated content).

### 2.1 Words-only, measured

* **Stripping trailing comments, both files are line-for-line identical to their pre-edit state:**
  `constants.py` 1,728 code lines before and after, `scenarios.py` 3,281 — no insertions, no
  deletions, no reordering.
* The only non-comment lines in either diff are **two trailing comments on unchanged dict entries**
  (`"mid": {2026: 0.5},` and `"mid": 4.5,` — the code before the `#` is byte-identical):

  ```
  -    "mid": {2026: 0.5},  # ILLUSTRATIVE — owner level (D-2), see above
  +    "mid": {2026: 0.5},  # committed (owner ruling S9, 2026-09-06), see above
  -    "mid": 4.5,  # ILLUSTRATIVE — owner level (D-2), see above
  +    "mid": 4.5,  # committed (owner ruling S9, 2026-09-06), see above
  ```
* **Every `VOLUNTARY_*` key and value is unchanged**, dumped after the edit:
  `ELIGIBLE_FUELS_DEFAULT` (wind, solar, offshore_wind, geothermal), `BASELINE_SHARE`
  (low 0.06 / mid 0.08 / high 0.08), `BASELINE_ISO_WEIGHT` (six `None`), `COMMITTED_DC_FRACTION`
  (0.0 / 0.5 / 1.0), `WTP_CEILING_USD_PER_MWH` (2.0 / 4.5 / 7.0), and the two NREL provenance
  series.
* No `ScenarioConfig` field, default, type or registration moved: the `scenarios.py` diff contains
  **zero non-comment lines at all**.

---

## 3. Key and test measurements

### 3.1 Cache keys — the census, before the first edit and after the last

One script, run at the pre-edit tree and again at `428549ac`, hashing: the two live pins plus the
charter's named pre-D65-B key; **every** `results/calibration/*/run_config.json` on disk (18 files,
reconstructed through `ScenarioConfig(**kept)` with the same legacy-field drop applied on both
sides); the twelve REF bases (6 ISOs × 2030/2050); and **every live campaign case on every ISO**
(90 keys).

| set | count | moved |
|---|---|---|
| pins (`547053bdfccd4264` forecast default, `f61891696e671969` bare backcast, `e5ecd4105ada3e58` pre-D65-B default) | 3 | **0** |
| committed keeper / touchpoint `run_config.json` | 18 | **0** |
| REF bases | 12 | **0** |
| live campaign cases | 90 | **30** — exactly `CARB-LO`, `CARB-MID`, `CARB-HI`, `CARB-MID+LOAD-HI`, `ALL-CLEAN` × 6 ISOs |
| cases added / removed | — | **0 / 0** |

**A case override never touches a base, keeper or pin key — measured, not asserted.** The 30 that
move are the five cases whose *own* override set changed form, which is the intended and necessary
consequence of expressing a different config: `{carbon_price_delta: 25.0}` and
`{carbon_price_path: "mid"}` are different configs and must hash differently, or an arm and its
control would collide on disk. **Nothing is orphaned by it:** all five cases are HELD under ruling
S5 and none has ever been solved — no `results/**` or `frontend/**` directory named `CARB-*` or
`ALL-CLEAN` exists, and the only committed artifacts carrying a nonzero `carbon_price_delta` are
earlier, differently-named probes (`results/scn-ws0-smoke/neiso/CARB`, the FF-T3 `carbon_plus25`
arms), which carry their own on-disk configs and are untouched.

**A note on a program-ISO subtlety worth stating once:** on CAISO/NYISO/NEISO the re-formed
`CARB-*` cases now resolve to *exactly REF's* carbon signal in the T1-F window (§1) while carrying a
*different cache key from REF* (the path field is set). That is correct — the key is a config hash,
not a dispatch hash — and it is why the policy lanes kill the case at phase 0 rather than solving it
and comparing.

**The charter's pin, reconciled.** The charter asks that the forecast default `e5ecd4105ada3e58` be
byte-identical. At this HEAD that key is **not** the live default: `capx D65-B` advanced the pin to
**`547053bdfccd4264`** on 2026-09-06 (`tests/regression/test_persisted_identity.py:203, :269`), and
`e5ecd4105ada3e58` is reachable only at the pre-flip construction
(`ccs_retrofit_fixed_cost_co2_scaling=False, ccs_retrofit_vom_adder=8.0`, the decomposition that
test records at :254). **Both were measured, and both are unchanged by this lane.** The stale
number is the charter's, written before D65-B landed; the in-repo comment block at
`scenarios.py:139` still names `e5ecd4105ada3e58` as "THE LIVE PIN" and is likewise stale — routed
in §5, not touched, because that block is outside this lane's regions.

### 3.2 Resolved-carbon identity for everything that is not a carbon case

The same census recomputed the resolved carbon trajectory for all six carbon-bearing case rows on
all six ISOs. The 30 that changed are the 30 re-formed cases; the six `REF` rows are unchanged.

### 3.3 Tests

* `tests/scoring/test_scenario_campaign_configs.py` — **18 passed**. The renamed pin
  `test_the_carbon_ladder_is_the_committed_rff_path_form` asserts the exact override dict of each of
  the three CARB-* rows **and** that `carbon_price_delta` is absent from the two composite cases, so
  the form is pinned in both directions and the stand-in cannot return silently.
  `test_voluntary_cases_are_live_on_the_one_field`'s ALL-CLEAN assertion follows the corner's carbon
  half onto `carbon_price_path: "mid"`.
* Wider slice `tests/unit/config tests/unit/policy tests/scoring`: **2,553 passed, 26 skipped, 98
  subtests passed, 5 failed** — and **all five are pre-existing on a clean tree under the `code`
  data profile**, verified by restoring the base-commit (`47e306d3`) copies of this lane's four
  files and re-running: four in `tests/scoring/test_ff_readiness_battery.py`
  (`test_walk_inputs_trivial_single_year`, `test_resolve_report_no_hard_fail_full_horizon`,
  `test_ercot_confirmed_horizon_is_reported_not_failed`,
  `test_build_registration_scorecard_no_iso_gate_open` — the same family SCN-LEVELS §3(c) recorded),
  plus
  `test_collate_scenario_campaign_common_set.py::test_the_repair_holds_over_the_whole_committed_tree`.
  The last was verified twice — with this lane's working-tree edits stashed, and again with the
  base-commit copies of `configs/scenario_campaign_matrix.yaml` and `tests/scoring/` restored — and
  fails identically both times (SCN-FIX1's regression pin expects 18.83 Mt; the committed results
  tree, which SCN-WS5A-LOAD is still filling, now yields 101.97 Mt). It is that lane's to re-pin,
  not this one's: `results/**` and `scripts/**` are outside this lane's regions.
* `ruff check` and `ruff format --check` **clean** on all four touched files. Two OTHER files are
  format-red on `main` and were deliberately **not** touched: `scripts/run_calibration.py` and
  `src/market_sim/data/fuel/basis/miso.py` (already routed onward by SCN-FIX1).

---

## 4. Files touched

| file | commit | what |
|---|---|---|
| `configs/scenario_campaign_matrix.yaml` | `725a0d85` | the four carbon rows + ALL-CLEAN's carbon component switched to `carbon_price_path`; the interim-form header block rewritten to the committed form citing S3 + WS-1c; header note 3 closed; the commented-out path block deleted; the §1.2 horizon finding recorded at the case |
| `tests/scoring/test_scenario_campaign_configs.py` | `725a0d85` | the carbon-form pin renamed and flipped to the committed form (both directions), ALL-CLEAN's carbon assertion followed |
| `src/market_sim/config/constants.py` | `428549ac` | the `VOLUNTARY_*` region, **words only** (§2) |
| `src/market_sim/config/scenarios.py` | `428549ac` | the three `voluntary_*` field docstrings, **words only** (§2) |
| `docs/handoffs/FINDING-scn-fix2-2026-09-06.md` | this commit | this document |

**Not touched, per the charter:** every other line of `scenarios.py` / `constants.py`;
`frontend/data/hindcast/**`; `results/**`; `scripts/**`; the mechanism-matrix shards; the plan's
§5.1; every non-carbon case in the campaign YAML. No solve, no registration, no CI workflow.

---

## 5. Routed to SCN-DESK — three staleness items this lane could not fix in its regions

1. **The campaign YAML's VOLUNTARY comment block still calls S9's committed cells illustrative.**
   The `VOL-MID` / `VOL-HI` block (and header note 2) reads "TWO CELLS stay **owner-set and LABELLED
   ILLUSTRATIVE** — `f_commit` MID (0.5 placeholder) and the WTP-ceiling MID level (4.5
   placeholder)" and "**D-3c** … is STILL OPEN: both cases run the memo §4.1 RECOMMENDATION". S9 and
   S10 make both statements false. The constants and the field docstrings — where a reader of the
   *levels* looks — are repaired here; the YAML's voluntary block is not this lane's region (the
   charter scopes it to "the four carbon rows + ALL-CLEAN's carbon component ONLY"), so it is routed
   rather than edited.
2. **The campaign YAML's header note 1 and `CAP-STATE-TIGHT` block are superseded by S12.** They
   still read "STILL OPEN under D-2" / "the slope is an OWNER level … must not be inferred"; ruling
   S12 (r#12 am.1) committed the 80 % slope and chartered SCN-CAP to build
   `mass_cap_tons_by_year`. SCN-CAP owns that case block and will land it; noted so the two lanes do
   not collide (they touch disjoint case blocks, as §4 of the ledger anticipates).
3. **`scenarios.py:139`'s pin comment names a superseded key.** It declares "THE LIVE PIN IS
   `e5ecd4105ada3e58`"; the live forecast default at HEAD is `547053bdfccd4264` (capx D65-B,
   2026-09-06), which `tests/regression/test_persisted_identity.py:269` already pins correctly. The
   comment block is capx's region and outside this lane's words-only scope, so it is measured and
   routed, not edited.

Nothing in §5 changes a number, a determination or a gate; all three are records drift of the kind
this lane exists to close, in regions another lane holds.
