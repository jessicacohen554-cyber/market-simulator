# PRECOMMIT — capx D75-R-ARM: arming the PJM VRE ELCC delivery-year vintage (owner ruling Q55)

**Lane:** capx D75-R-ARM, executing **owner ruling Q55** (capx ledger §3, r#51: *"ARM for PJM"*) on
the measured D75-R A/B. **Branch:** `claude/capx-d75r-pjm-vre-arm-gdomci`, fresh off `origin/main`
**`0f7a4842`**. **Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.

**Pushed before any code change and before any solve.** Every key, count and classification below was
measured at `0f7a4842` with **zero LP**, through the shipped harness path, and is recorded here so it
cannot be written to fit a result.

**Charter:** pack §D75-R-ARM + `FINDING-capx-d75r-2026-09-06.md` (§0 the answer; §1 what was built and
why a second key was unavoidable; §5 the full window and its two fired STOPs; §6 what the lane routes;
§8 the recommendation and the arming posture it names) + the **D57/Q44 → D67-ARM arming precedent**
(`FINDING-capx-d67arm-2026-09-06.md`, this document's template).

**Instrument:** `scripts/probes/capxd75rarm_iso_override_no_op_check.py` — one script, run
`--simulate-arm` here for the ex-ante expectation and again with the flag omitted after the edit, so
the expectation and the measurement come off the same code.

---

## 0. THE DISPATCH PRECONDITION IS **UNMET**, and this lane is scoped around it

The charter's STOP: do not start until D65-B-R's board-write PR — the one registering `pjm-t1f` /
`neiso-t1f` / `nyiso-t1f` / `miso-t1f` / `neiso-t3` on `frontend/data/forecast/program-status.json` —
has merged. **It has not.** Checked at `0f7a4842`:

| check | result |
|---|---|
| `git log origin/main --grep="D65-B-R"` | 12 commits — PRECOMMIT, Addenda D/E/F, **legs 1–6** (`e1926620` … `46cb32c3`) |
| any of those touching `program-status.json` | **none** — every leg commit is `FINDING` + its own `results/forecast/…` bundle |
| `"D65-B-R"` in `origin/main:program-status.json` | **0 occurrences**; PJM's `b_t1f_verdict` is still the 2026-09-04 capx-D45R re-measure |
| `ff-verdicts.json` `pjm-t1f` provenance | `session=capx-D60-R3`, `run_id=pjm-2026-2030-d60-arm` — **not** leg 5's `542eeedadab83ee1` |
| open PRs / `d65*` branches on origin | **zero / zero** |

The board itself still says so in its own words: the PJM and NEISO `-pre-d60` rows read *"form-4
differencing is VOID for this row until D65-B re-solves every bare key at one HEAD."*

**Scope taken, on owner direction (2026-09-06, in-session): charter steps 0–2 only.** The PRECOMMIT,
the arm, the test edit and the byte-identity probe **touch no board file and none of the five rows**.
Charter **steps 3–4 are HELD** — the `pjm-t1h` re-solve, its registration, and the FINDING that would
quote a board row — exactly the posture `PRECOMMIT-capx-d67arm-2026-09-06.md` §7 took when it hit the
same collision (*"the board registration is HELD until D65-B-R merges"*). This lane does not become a
second writer of `program-status.json` or `ff-verdicts.json` while the batch's write is pending.

---

## 1. The act

`config/iso_configs.py::_pjm_config` `default_scenario_overrides` gains one key:

```python
"pjm_vre_accreditation_vintage": True,
```

The D57/Q44 → D67-ARM pattern exactly, and **nothing else**:

- the shared `ScenarioConfig` dataclass default stays **`False`** — an **ISO override, not a declared
  default flip**, so no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry, no other ISO's key moves, and
  every backcast key is byte-identical;
- the explicit `--no-pjm-vre-accreditation-vintage` path reaches the pre-arm posture and keeps its key
  (the (b′-1) inverse test) — the flag already exists, `argparse.BooleanOptionalAction` with
  `default=None` (`scripts/run_capacity_hindcast.py:1710`), so **no CLI surface is added**;
- **rule 19 `[R-ONE-MECH]` is satisfied by composition, not by proximity.** The predicate
  `retirements.vre_accreditation_vintage_armed` requires THREE conditions — this field, D48's own
  `pjm_accreditation_design_vintage`, and a registry entry for the ISO — so the VRE half can never be
  vintaged while the thermal half is not. It is a **sub-gate inside the D48 family**, which is why it
  is armed beside the D48 / D57 / D67 entries rather than as a fourth mechanism (D75-R §1);
- **rule 21 `[R-DOF]`: zero free parameters** beyond the ONE cross-vintage reconciliation ruling R1
  authorised and D75-R §1 declares at the seam — PJM's own published Table-5 installed-MW mix
  `1189/(1189+8713)` = 12.01 % fixed, re-derived from the committed rows by test. Every rating is a
  published PJM class rating reconciled byte-for-byte to
  `data/raw/capacity-market/elcc/pjm/pjm.csv`. **The ruling is the identification**; the decision to
  arm is Q55, and it is a rule 14 `[R-ACCURATE]` decision (the ISO's own published accreditation for
  the delivery year each auction actually cleared on), not a residual decision;
- **rule 25 `[R-ISO-SCOPE]`: a PJM posture.** No other ISO's cell, key or shard is touched. The five
  non-PJM shards keep their `·` cells — each is `ISO-exclusive`/`n/a by market design` on its own
  evidence, and none inherits PJM's verdict.

**Also in the PR** (test + docs, no solve-path behaviour): the D67-ARM-style override pin
`tests/unit/model/test_capacity.py::test_pjm_iso_override_arms_forecast_only` re-pinned to the new key
set; the `--pjm-vre-accreditation-vintage` help string, whose *"OMIT to inherit the shipped default
(off, unlike the two D48 gates PJM's ISOConfig arms)"* clause becomes false the moment the arm lands;
the CLAUDE.md Capacity Evolution sentence; the PJM matrix shard cell. **Docs follow code** — no doc
claim is written that the code does not already carry.

---

## 2. THE RE-KEY — declared before the edit, measured through the harness at `0f7a4842`

Harness path, the same one the override pin uses: `build_config(iso, 2021, 2025, "realized",
vintage=2020, entry_screen_diagnostics=True)` → `apply_iso_scenario_defaults` → `cache_key()`.

| recipe | key at `0f7a4842` | **after the arm** | |
|---|---|---|---|
| **bare `pjm-t1h`** | `a9c66d8ea25acb9d` | **`b518f5fe7d02f961`** | **moves** |
| explicit `--no-pjm-vre-accreditation-vintage` | `a9c66d8ea25acb9d` | `a9c66d8ea25acb9d` | **unmoved** |
| D57 off3 (`--no-` ×3), D67 on | `61dfbc5c48af076b` | **`1785cb6086cd2b15`** | **moves** |
| off3 + `--no-capacity-adequacy-requirement-published` | `c5ec052057905966` | **`d2fe4e2b32aef073`** | **moves** |
| D57 arm B (`--no-` ×2), D67 on | `2d5bebd2bceed991` | **`ab0237198cff24ad`** | **moves** |
| off2 + `--no-capacity-adequacy-requirement-published` | `6ba67a81ed4d2ed6` | **`05cdf4af2b9adef8`** | **moves** |
| MISO / NYISO / NEISO / CAISO / ERCOT bare | `1f92943f84f42fd0` · `ee6a3e764324f28f` · `5b292e24dd752ea4` · `8f1c3766703a90c4` · `46d013cbf1f35d27` | all **unmoved** | |
| PJM plain backcast | `3a566deac3a85682` | `3a566deac3a85682` | **unmoved**, field coerced `False` |

### 2.1 The four control legs MOVE, and that is declared here rather than discovered later

`FINDING-capx-d67arm` §2.1 recorded exactly one miss: its PRECOMMIT called the D57 all-off control
leg "unmoved" and **it moved**, because a leg that turns off three named fields and says nothing about
a fourth carries the fourth armed after the arm. **The same thing happens here, to all four legs**, and
it is pre-declared with its measured literals above rather than reported as a surprise. The reason is
structural: `pjm_vre_accreditation_vintage` is a `_CACHE_KEY_OPTIONAL_FIELDS` member registered at
`False`, so it is *dropped* from the hash while unarmed and *enters* it once armed — on every PJM
forecast leg, whatever the other flags say. (The mechanism is *inert* on the three legs that turn
D48's thermal half off, since the predicate needs it — but inertness is a solve property, not a hash
property, and the key move is real.)

**The arm is fully invertible, which is the property that actually matters** — measured, not asserted.
Adding `pjm_vre_accreditation_vintage=False` to each post-arm leg restores its pre-arm literal exactly:

| leg | post-arm | + `--no-pjm-vre-accreditation-vintage` | |
|---|---|---|---|
| bare | `b518f5fe7d02f961` | **`a9c66d8ea25acb9d`** | ✔ |
| off3 (D57 control, D67 on) | `1785cb6086cd2b15` | **`61dfbc5c48af076b`** | ✔ |
| off3 + `--no-req-pub` | `d2fe4e2b32aef073` | **`c5ec052057905966`** | ✔ (D45-R's bare key) |
| off2 (D57 arm B, D67 on) | `ab0237198cff24ad` | **`2d5bebd2bceed991`** | ✔ |
| off2 + `--no-req-pub` | `05cdf4af2b9adef8` | **`6ba67a81ed4d2ed6`** | ✔ (arm B) |

Every pre-arm bundle's recipe therefore stays both **reachable** and **identified**. All four moved
legs are re-pinned in `test_capacity.py` with their inverses beside them, so a later lane cannot
mistake a post-arm leg for the posture it names.

### 2.2 The post-arm key is **D75-R's own measured arm**, which makes this a re-declaration, not a new number

D75-R's full window was solved control `a9c66d8ea25acb9d` / arm `b518f5fe7d02f961`
(`PRECOMMIT-capx-d75r…` Addendum A.1, at base `d333d01b`). **Both literals reproduce at `0f7a4842`
to the digit** — the bare recipe here *is* that control, and the arm resolves to that arm. So the
solve surface the cache key covers has not moved since D75-R measured, and §5's predictions below are
D75-R's own bundle numbers rather than fresh guesses.

**Cache-epoch ledger** (`src/market_sim/results/cache.py`): this is a **KEY ADVANCE, not a same-key
invalidation** — the bare recipe moves `a9c66d8ea25acb9d` → `b518f5fe7d02f961`, so no committed
bundle is silently re-interpreted and the D67-ARM-era bundle keeps its own key under its own id.
**No registration re-key is written in this PR**: the `register_forecast_run.py` `VERDICT_MAP` move
(`pjm-2021-2025-realized-t1h-d67arm` → `pjm-t1h-pre-d75r`, and the re-solve → `pjm-t1h`) belongs to
the HELD step 3 and is not landed while the board is another lane's.

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — **every hunk INERT**

Window: **`d333d01b`** — D75-R's own full-window solve base, the honest base for numbers solved there
— **→ `0f7a4842`**. 175 commits; on the solve path
(`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/run_capacity_hindcast.py scripts/lib data/raw/_validation-source data/raw/reference`) it is
**20 files, +2,210/−65**, and it decomposes into exactly **six source commits**. A matched cache key
is NOT offered as a drift verdict; every classification below is structural.

**`constants.py` first, as the charter asks.** Over the whole window `config/constants.py` changes by
**exactly one line**:

```
+    RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO,
```

— D75-R's own re-export of the registry being armed. **Zero constants drift from any other lane** in
175 commits.

| commit | what | classification |
|---|---|---|
| **`f3d0396e`** | capx **D75-R's own build** — the ELCC vintage registry (`capacity_market.py` +131), the resolver and predicate (`retirements.py`), the field (`scenarios.py`), the CLI flag (`run_capacity_hindcast.py`), the constants re-export | **THE OBJECT, not drift.** Present identically in D75-R's control *and* arm; it is what Q55 arms |
| **`bf97317f`** | capx D78-R2 STEP 0 — deletes the producer-less `exempt_unit_ids` parameter from `apply_economic_retirements` and its skip | **INERT, provably.** At `d333d01b` the single call site (`evolve.py:754`) passed `exempt_unit_ids=frozenset()`, so `if g.unit_id in exempt_unit_ids:` could never fire. Removing a branch whose guard is always False is exactly value-preserving. At HEAD `grep` over `src/` finds no code reference left — only comments |
| **`16210868`** | capx D79 phase 1 — the solve-surface fingerprint enters `cache_key()` (`solve_surface.py` +406, `solve_surface_declared.py` +577, `cache.py`, `export.py`, `persist.py`, `forecast_provenance.py`) | **INERT, measured.** Landed in FROZEN-HASH form: `moved_rows()` is `[]` for all six ISOs and `SOLVE_EPOCHS` is empty, so neither `__solve_surface__` nor `__solve_epochs__` ever reaches a payload. Its own merge gate re-run at `0f7a4842`: **0 of 153 committed run configs moved**, 296 surface names, 296 declared, 0 undeclared |
| **`beb74f0f`** | pjm-167 F1 — backcast EIA-860 vintage tracks the solved year (`scenarios.py`, `paths.py`, `runner.py`, `run_calibration.py`) | **INERT, doubly.** GATED `eia860_vintage_tracks_solve_year` default **False**, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at False. And backcast-only by construction: on the forecast/hindcast leg `runner.py` calls `resolve_backcast_eia860_vintage(config.eia860_vintage_year, None, False)`, which returns `int(explicit)` or `None` — **the identical expression the line computed before** |
| **`cd96fa26`** | pjm-167 F2 — the PJM interface-feed admissibility gate (`transfer_interface_limits.py` +168, `scenarios.py`, `run_calibration.py`) | **INERT, doubly.** GATED `pjm_interface_feed_admissibility_gate` default **False**, registered at False; both new parameters default `False` so every existing caller is byte-preserved. And **off-path**: the only callers of `pjm_eastern_interface_hourly` / `pjm_apsouth_interface_hourly` / `pjm_interface_ttc_hourly` anywhere in `src/` or `scripts/` are in `scripts/run_calibration.py`, the **backcast** runner, which a `mode="forecast"` hindcast never enters |
| **`cbe15b6f`** | ercot-251 — the curtailment gates test the renewable bound's provenance rather than HSL-file existence (`run_calibration.py`) | **INERT.** Backcast runner, off-path as above; ERCOT-scoped besides |

**Recipe posture, resolved at `0f7a4842` (measured, not asserted):** `pjm_accreditation_design_vintage`
**True** · `pjm_demand_response_supply` **True** · `capacity_market_supply_clearing_by_iso`
**`{"PJM": True}`** · `capacity_adequacy_requirement_published_by_iso` **`{"PJM": True}`** ·
`pjm_vre_accreditation_vintage` **False** (the field this lane arms) ·
`eia860_vintage_tracks_solve_year` **False** · `pjm_interface_feed_admissibility_gate` **False** ·
`retirement_sector_gate` **False** · `ccs_retrofit_available_year` **2028** ·
`fossil_announced_exits_enabled` **True**.

**ALL HUNKS INERT ⇒ G-CTRL form 4 is VALID and the committed `pjm-t1h` bundle IS the control.** No
control solve is earned and none will be spent (rule 29(b)). Note this is *stronger* than the D67-ARM
window, which carried one LIVE hunk (D81): here there is none.

---

## 4. Rule 29(a) — why there is no screen solve

**29(a) does not apply.** The screen exists to *select* an arm before spending a full span. There is
nothing to select: D75-R already spent both the DY 2023/24 screen (PASS on all four legs) and the full
2021–2025 A/B on one base, and the **owner has ruled** (Q55). This lane executes a ruled arming. Under
the scope of §0 it spends **no LP at all**.

---

## 5. Pre-declared expectations — graded at full magnitude, whatever they read

**P-1 (the byte-identity gate, the only one this lane's scope actually settles).** The no-op probe,
run `--simulate-arm` at `0f7a4842` **before** `iso_configs.py` was touched, over all **153** committed
run configs:

| bucket | configs | moved |
|---|---:|---:|
| every non-PJM ISO (CAISO/ERCOT/MISO/NEISO/NYISO), forecast **and** backcast | 130 | **0** |
| PJM **backcast** | 2 | **0** |
| **PJM forecast** | 21 | **21** |

Zero off-target moves. Re-running the same probe **after** the edit, with `--simulate-arm` omitted,
must reproduce this table exactly. **Any non-PJM or backcast move is a STOP**, not a number to record:
it would mean the arm had been landed as a shared-default flip, the variant that orphans all six
backcast keepers and was never licensed.

**P-2.** `--no-pjm-vre-accreditation-vintage` reaches the control and keeps key `a9c66d8ea25acb9d`;
all four other control legs are invertible to their pre-arm literals (§2.1 table).

**P-3.** `tests/regression/test_persisted_identity.py` green; `check_cache_key_registration.py --base
origin/main` green; `check_mechanism_matrix.py --base origin/main` integrity OK; `ruff` clean;
`tests/unit/data/test_renewable_elcc_curves.py` + `tests/curation/test_curate_capacity_market_elcc.py`
green (the byte-for-byte reconciliation of every vintage rating and the rule-25 inertness lock across
the other five ISOs).

### 5.1 What the HELD step 3 would be graded against — recorded now so it cannot be written later

**The bar is D67-ARM's: all 14 invariants PASS on the bare `pjm-t1h` row.** Verified live in the
committed sidecar `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d67arm.json` — I1 energy balance ·
I2 no NaN/inf · I3 unserved/dump · I4 capacity accounting · I5 no retire-and-reenter · I6
econ-retirement sanity · I7 reliability floor · I8 planned-additions gating · I9 storage integrity ·
I10 RPS dual sign+stability · I11 one-pass · I12 reserve-margin band · I13 cobweb detector · I14 price
sanity, **14 PASS, 0 FAIL, 0 WARN**. D75-R measured *all 26 scored bands byte-identical* between its
control and arm, so **the re-solve is expected to hold all 14**. Anything less is a fired STOP.

**FC-3, reported at full magnitude and gated on nothing.** The control column is **not** quoted from
D75-R's prose — it is read row-by-row out of that committed sidecar, which confirms D75-R's control
*is* the shipped posture:

| FC-3 row | control (committed `pjm-t1h`, verified) | arm (D75-R §5.2, predicted) | band |
|---|---:|---:|---|
| `retirements.total_gw.model` (actual 15.062) | **18.058** | **17.294** | FAIL → FAIL |
| `retirements.total_gw.err_frac` | **0.199** | **0.148** | — |
| `false_retire.false_gw` | **8.065** | **7.596** | FAIL → FAIL |
| `false_retire.frac_of_model` | **0.447** | — | FAIL → FAIL |
| `plant_release_precision.window.all` | **0.421** | **0.439** | reported-only |
| `plant_release_precision` 2023, all channels | **0.689** | **0.965** | reported-only |
| `plant_release_precision.window.economic` | **0.122** | **0.129** | reported-only |
| `unit_recall_gt300.recall` | **0.65** (13/20) | **0.65 unchanged** | FAIL → FAIL |
| CO2, all three years | — | ±0.01 %, unmoved | — |

**Two bands stay FAIL and one metric does not move at all.** That is stated here, ex ante, as the
honest reading of a supply-side accreditation repair: it removes *false* exits, it does not find
missing *true* ones. Position is two-sided (Σ|gap| 2.587 → 2.074 pt frame B, 1.579 → 1.067 frame A),
and **D75-R's own STOP 4 fired** — DY 2025/26's residual narrowed where its PRECOMMIT predicted
widening, and the 2024/25 and 2025/26 census moved **UP** despite less VRE credit, through fleet
propagation. Nothing was re-tuned in response then and nothing is now (rule 1 `[R-STRUCT]`).

---

## 6. Execution order, and the HEAD guard

1. **This PRECOMMIT + the probe**, pushed **before** the override. ← the edit does not begin until this is on the branch
2. The override + the re-pinned test + the CLI help string + the CLAUDE.md sentence + the PJM matrix
   shard cell + the cache-epoch entry — one PR.
3. The **post-edit** probe run (flag omitted), which must reproduce §5's P-1 table exactly.
4. **HELD** — the `pjm-t1h` re-solve (2021–2025, sequential, `H0=$(git rev-parse HEAD); <solve>;
   [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`), its registration, and the FINDING. Released only
   when D65-B-R's board write has merged, or on explicit owner direction.

**Rebase discipline:** between steps, never during. No commit is made while any solve is running (the
error `FINDING-capx-d75r` §7 item 1 records).

---

## 7. Collisions

- **D65-B-R is the SOLE writer** of `frontend/data/forecast/{ff-verdicts,program-status}.json` until
  its batch registers. §0 is the whole scope decision. Steps 1–3 touch neither file.
- **D67-ARM** is the immediately prior writer of `_pjm_config`; its key `a9c66d8ea25acb9d` is this
  lane's control and is re-pinned, not replaced. Its own board registration is likewise held.
- **D78-R2 / D79 / pjm-167 / ercot-251** are the four other lanes in the G-DRIFT window; all INERT
  (§3), none in `_pjm_config`. **`_pjm_config` is this lane's window.**
- The D75-R lane's own branch is another desk's and is closed; this lane is fresh off `origin/main`.

---

## 8. What this lane does NOT claim

It moves **no** `ScenarioConfig` default, no registry value, no R1 reconciliation, no other ISO, no
backcast keeper, no marker or freeze file, and no calibration determination. It re-opens no
adjudicated matrix cell. It adds **no CLI surface** — `--no-pjm-vre-accreditation-vintage` already
exists. It does not re-litigate D75-R's open items, which stay routed and untouched: the missing
`evolution_2022.json` adequacy block, the EIA-860 `Fixed Tilt?`/`Single-Axis Tracking?` derivation
(ruling R1 made it its own card, and it is the route that would retire the cross-vintage
reconciliation), the 2025/26 BRA-vs-3IA vintage question, and PJM's 2025/26 3IA **thermal** ratings
differing from the wired 2026/27 set (D48's half, not this card's).

**And it does not claim the arm closes what D75-R said it does not**: the model still over-retires
(17.294 GW against 15.062 actual), `unit_recall_gt300` is unchanged at 0.65, and the 2024/25 and
2025/26 census stay **below** the published cleared position with this mechanism moving them the wrong
way there through fleet propagation. That residual is D66 card B's remaining half and is **not**
closed here.
