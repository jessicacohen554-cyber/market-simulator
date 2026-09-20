# PRECOMMIT xiso-8 — the year-start left-edge object

**Lane:** xiso-8 (cross-ISO: CAISO + MISO) · **Date:** 2026-09-20 · **Phase 0 = ZERO LP**
**Opened by:** owner ruling 2026-09-20, `docs/FINDING-caiso289-the-bridge-flag-carries-two-mechanisms-2026-09-20.md`
§7(1) — *"the left-edge repair → open it as its own cross-ISO object"*, and, the same day,
*"do a single lane."*

---

## 0. THE CROSS-ISO SCOPE DEPARTURE, DECLARED

This lane edits **two ISOs' shards** — `mechanism-matrix/{CAISO,MISO}.js` and
`frontend/data/backcast/keepers/{CAISO,MISO}.json` — which is a **deliberate departure** from the
per-ISO discipline in rule 28 `[R-MECH-MATRIX]` (d) and `frontend/data/backcast/keepers/README.md`
(*"a lane edits ONLY its own ISO's shard"*). It is authorized by the owner instruction of
**2026-09-20** cited above, which made the defect one cross-ISO object and assigned it to a single
lane. **No third ISO's shard is touched** beyond the rule 28 duty (c) obligation to add a cell line
for a new shared `ScenarioConfig` field in every shard — which is the one deliberately
non-parallel edit that duty already requires.

Recorded here, and in both keeper shards' notes, so a later auditor does not read a
CAISO-and-MISO edit as a lane that overstepped.

---

## 1. THE DEFECT

`_flow_date_staircase` (`src/market_sim/data/fuel/hubs.py`) places each trade-day citygate print on
its gas **flow** day (trade + 1; Friday's trade covers the holiday-extended weekend package),
forward-fills the non-trading gaps, and then `.bfill()`s whatever is left. The only days `.bfill()`
can reach are the **year's opening flow days** — those before the first January trade's flow day.

On the function's own documented convention those days were priced by the **previous December's
last trade**. The back-fill instead hands them the year's **first January trade** — a trade that
had not happened yet, and that prices a *later* flow day.

**The basis is rule 14 `[R-ACCURATE]`, on the source convention, and nothing else.** CAISO's 2023
C3a residual is +3.796 % (model high) and this repair pushes early-2023 gas *down*, i.e. the
helpful way. **That is an OUTCOME, not the reason** (rule 1 `[R-STRUCT]`: the direction of a
residual is evidence for nothing). The band in §5 is registered before the solve and is not a
target.

---

## 2. PHASE 0 (a) — MISO'S EXPOSURE, AND THE TRAP IT EXPOSED

Harness: `scripts/probes/xiso8_left_edge_census.py` → `results/calibration/_xiso8_left_edge_census.json`.
Zero LP; arithmetic over the committed dated maps.

### 2.1 The trap: not every year-boundary gap is a package

The convention argument licenses forward-fill **across a trading package**. It does not license
constant-extending the last print across an **EIA publication blackout** — that is precisely the
artifact `caiso_citygate_blackout_bridge` (caiso-288/289) exists to remove, and it is a different
mechanism with a different owner. A naive "always ffill from prior December" repair would have
handed **MISO 2023-01-01..04 the 2022-12-21 Winter Storm Elliott print of $17.69/MMBtu**, across a
**15-day** gap, when the next measured print is $3.38. That is a *worse* construction than the
back-fill it replaces.

**So the repair is scoped to PACKAGE gaps only** — a year-boundary trade gap of
`< _GAS_BLACKOUT_MIN_GAP_DAYS` (6). Where the boundary sits inside a blackout, this object does
nothing and the day remains the bridge's territory. The two mechanisms are **disjoint by
construction** (rule 19 `[R-ONE-MECH]`): the bridge fills only gaps ≥ 6 days, this fills only
gaps < 6.

### 2.2 G-LE-CENSUS — CAISO (SoCal citygate), LEVEL channel

The CAISO keeper arms `caiso_citygate_spot_level=True`, so the staircase supplies the **absolute
daily $/MMBtu**. A left-edge error is a direct level error on those days.

| year | edge days | gap | class | prior Dec last trade | used (first Jan) | Δ $/MMBtu | Δ CC mc $/MWh |
|---|--:|--:|---|---|---|--:|--:|
| 2022 | 3 | 4 | package | 2021-12-30 = 7.09 | 2022-01-03 = 5.66 | **+1.430** | **+10.64** |
| 2023 | 3 | 4 | package | 2022-12-30 = 15.31 | 2023-01-03 = 23.66 | **−8.350** | **−62.12** |
| 2024 | 2 | 4 | package | 2023-12-29 = 2.98 | 2024-01-02 = 3.45 | **−0.470** | **−3.50** |
| 2025 | 2 | 2 | package | 2024-12-31 = 2.90 | 2025-01-02 = 3.12 | **−0.220** | **−1.64** |

2019 and 2020 are blackouts (15-day gaps) and out of scope; both are outside every scored CAISO
year anyway. **All four scored years are in scope.**

*Cross-check: this table reproduces caiso-289 §4's independently-measured figures exactly, on all
four years, from a different harness.*

### 2.3 G-LE-CENSUS + G-MISO-SHAPE — MISO (Chicago citygate), SHAPE channel only

The MISO keeper `2026-09-20-miso-264-anchor-vintage` arms **`miso_winter_citygate_daily=True`**
and **`miso_gas_marginal_commodity_pricing=False`**. So of MISO's two call sites, the live one is
`basis/miso.py:160` `miso_chicago_daily_shape_factors`, whose factors are renormalized to mean
**exactly 1.0 within every month**. A left-edge change therefore **cannot move January's gas
level at all** — it only redistributes price *within* January. The level channel
(`basis/miso.py:501`) is inert in the keeper.

Only **two** MISO years are in scope at all; the other four registered years' boundaries sit inside
15–19 day publication blackouts.

| year | edge days | class | Δ $/MMBtu | edge Δ mc $/MWh | full-pass-through on the annual mean |
|---|--:|---|--:|--:|--:|
| 2021 | 4 | package | −0.180 | −1.183 | **−0.0293 %** |
| 2022 | 3 | package | +0.200 | +1.363 | **+0.0180 %** |
| 2023 | 5 | **BLACKOUT** | — | — | out of scope |
| 2024 | 4 | **BLACKOUT** | — | — | out of scope |
| 2025 | 2 | **BLACKOUT** | — | — | out of scope |
| 2020 | 2 | **BLACKOUT** | — | — | out of scope |

**MISO's worst-year exposure to this object is 0.0293 % of the annual mean price** — ~30× smaller
than CAISO's 2023 limb, and below the resolution of every gate in the rubric.

---

## 3. THE SCOPE CUT — SIX SHARDS ARE NOT SPENT

**The object is cut to CAISO's four shards.** This is §3.1(a) of the lane instruction taken at its
word: *"If MISO's exposure is trivial, say so and cut the object to CAISO's four shards — that is
a legitimate and valuable outcome, not a failure."* It is trivial, measured, above.

What that does and does not mean:

* The **shared code path is repaired for MISO too**, with the gate default-off. MISO's keeper keeps
  its cache key and is byte-identical. A MISO lane can arm it on its own cadence with no
  re-derivation and no new measurement — the census above is committed.
* This is **not** rule 25 `[R-ISO-SCOPE]` trouble: nothing fitted on one ISO's residual crosses to
  another. It is one shared convention repair with **zero free parameters**, armed where it is
  material and left available where it is not.
* It is **not** fitted-mechanism selection under rule 1 `[R-STRUCT]`. The cut is made on
  **exposure magnitude measured before any solve**, not on whether a gate moves. The MISO cells
  are recorded in the matrix as measured-and-not-armed with this doc as the citation, so the
  decision is auditable rather than silent.
* **Stated as a cost:** MISO's keeper continues to carry the defect on 2021 and 2022, at the sizes
  above. That is a known, quantified, ledgered residual, not an oversight.

---

## 4. THE DESIGN

`ScenarioConfig.gas_flow_date_year_start_package` — **bool, default `False`**, shared field.

* **Registered** in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (rule 24
  `[R-REGISTRY]`), so `cache_key()` drops it at its default and **every existing config in every
  ISO keeps its key**; an armed run earns a distinct one.
* **Registered** in `_BACKCAST_ONLY_OVERLAY_FIELDS` beside its direct sibling
  `caiso_citygate_flow_date` ("flow-date placement of that measured series"), and at tier 3.
* **Zero free parameters, zero new thresholds.** The scope limit reuses the existing
  `_GAS_BLACKOUT_MIN_GAP_DAYS = 6`, whose identification (a histogram empty at 6 and 7, so 6/7/8
  select the identical gaps) is caiso-289 §2 and is not re-derived here.
* **Mechanism:** `_flow_date_staircase` gains a `prior_year_dated` parameter — the *prior* year's
  month→day map, which every call site already has. The function takes that year's **last trade**,
  places it on its flow day, and seeds the series with it when the gap to this year's first own
  flow day is `< _GAS_BLACKOUT_MIN_GAP_DAYS`. The existing `.ffill()` then carries it across the
  edge and `.bfill()` has nothing left to reach.
* **Not smuggled through the bridge flag.** caiso-289 spent a session separating those channels
  (rule 19); `test_the_flag_moves_blackout_interiors_and_nothing_else` stays green.
* **Rule 23 `[R-FROZEN-DERIVE]`:** `scripts/data/derive_miso_gas_variable_transport.py:139` calls
  the same function. It is left at the default (off), so the frozen derive does **not** silently
  re-derive. That is a second, independent reason the default is off.

**G-DRIFT (rule 29 `[R-SCREEN]` (b), form 4)** — audited against both keepers' `git_sha`
(CAISO `35adf93c`, MISO `23b5d44e`). Every changed hunk on the backcast path classifies **INERT**:
`REGIONAL_RENEWABLE_CF` / `PPA_COST_RECOVERY_YR` are read only by `scripts/build_mac_sidecar.py`
(a reporting surface, never the solve path); `new_entry.py`'s `cf_override` / `life_override` are
`None`-defaulted, byte-identical at `None`, and sit on the forecast-only capacity-evolution path a
`mode="backcast"` run never enters; `hubs.py`'s `_basis_bridge_blackouts` and the separated branch
are reachable only under `caiso_citygate_blackout_bridge`, which is default-off and absent from
both keepers' recipes; the `constants.py` NWPP rows are another ISO's branch. **All INERT ⇒ form 4
is valid and both committed keepers are the control. No control solve is spent.**

---

## 5. THE BAND, PRE-REGISTERED EX ANTE

Construction is caiso-288's: **[no movement, full pass-through]**, where the upper limb prices
every edge hour's move at the CAISO CC_REGULAR cap-weighted heat rate 7.44 MMBtu/MWh and weights it
by that hour's share of annual load, both read from the keeper's **committed** hourlies. Computed
before any solve; harness `results/calibration/_xiso8_band.json`.

| year | edge days | Δ gas $/MMBtu | keeper load-wtd mean $/MWh | edge-hour load share | **BAND on the annual mean** |
|---|--:|--:|--:|--:|---|
| 2022 | 3 | +1.430 | 90.279 | 0.742 % | **[0.000 %, +0.087 %]** |
| 2023 | 3 | −8.350 | 56.226 | 0.796 % | **[0.000 %, −0.879 %]** |
| 2024 | 2 | −0.470 | 37.201 | 0.479 % | **[0.000 %, −0.045 %]** |
| 2025 | 2 | −0.220 | 36.975 | 0.501 % | **[0.000 %, −0.022 %]** |

**The honest size of this object, stated up front: it is a correctness repair with a small price
footprint.** Only 2023 is above a tenth of a percent. Nothing here is a lever, and the arm is
**not** judged by whether a gate moves (rule 1 `[R-STRUCT]`) — a landing anywhere inside the band
is the predicted behaviour of a correct construction, and a landing outside it is a finding to
root-cause.

---

## 6. THE SHARD PLAN

Rule 36 `[R-YEAR-ISOLATION]`: **one year per shard, one container each**, one
`--years <single year>`; both cross-year knobs stay at their new OFF defaults. Rule 34
`[R-SHARD-PROMOTABLE]` (a): every shard pushes its **whole** bundle including
`dispatch/<year>_P1.parquet`, via a `.gitignore` negation plus a **plain** `git add`. Rule 34 (c):
**all four** registered CAISO years, which is the full union from §7.

| shard | year | out-dir | branch |
|---|--:|---|---|
| xiso8-caiso-2022 | 2022 | `results/calibration/xiso8_leftedge_2022` | `claude/xiso8-caiso-2022` |
| xiso8-caiso-2023 | 2023 | `results/calibration/xiso8_leftedge_2023` | `claude/xiso8-caiso-2023` |
| xiso8-caiso-2024 | 2024 | `results/calibration/xiso8_leftedge_2024` | `claude/xiso8-caiso-2024` |
| xiso8-caiso-2025 | 2025 | `results/calibration/xiso8_leftedge_2025` | `claude/xiso8-caiso-2025` |

The parent never solves (rule 32 `[R-SHARD]` (a)). Phase 0, composition, scoring, registration and
the promotion question stay here.

---

## 7. THE YEAR UNION, ENUMERATED BEFORE ANY PRUNE (rule 35 `[R-PROMOTE]` (b))

Read from every sidecar in `frontend/data/backcast/registry/` for each ISO, **before** anything is
deleted — the prune destroys this evidence.

* **CAISO — union `{2022, 2023, 2024, 2025}`**, from two registered runs:
  `2026-09-20-caiso-288-citygate-recovery` (bundle `caiso288_gasfix_span`, years 2023–2025) and
  `2026-09-20-caiso-288-citygate-2022` (bundle `caiso288_gasfix_2022`, year 2022, stamped
  `holdout.keeper` → the recovery run).
* **MISO — union `{2020, 2021, 2022, 2023, 2024, 2025}`**, from one registered run:
  `2026-09-20-miso-264-anchor-vintage` (bundle `miso264_anchor_span`).

**The incoming CAISO keeper must cover all four years** (rule 35 (c)) — it does, by construction of
§6 — and the 2022 rung folds to it via `stamp_touchpoint_holdout.py` (rule 30 `[R-TOUCHPOINT-FOLD]`
(a); a dangling `holdout.keeper` reads as unstamped and would silently drop 2022 off the report).
**MISO is not promoted and nothing of MISO's is pruned**, per §3.

*(Correction to the lane instruction §1: it names MISO's keeper as
`2026-09-19-miso-263-coal-ceiling` / `miso263_coalcap_span`. That was superseded earlier the same
day by `2026-09-20-miso-264-anchor-vintage` / `miso264_anchor_span`, which is what is registered at
this lane's base commit and what §2.3's measurements are taken against.)*

---

## 8. WHAT WOULD MAKE THIS NOT A KEEPER

Stated before the solve so it cannot be written to fit the result:

* any year landing **outside** its §5 band — the construction then does something the arithmetic
  did not predict, and that is a root-cause question, not a tuning one;
* any **load-bearing** criterion (C1/C2/C3a/C3b) flipping PASS → FAIL in any year;
* the governance gate failing, or a second ledgered caveat appearing beside the standing C3c;
* `test_the_flag_moves_blackout_interiors_and_nothing_else` failing — the channels have re-merged.

A gate that *fails to improve* is **not** on this list. The repair's warrant is rule 14, and
caiso-288's own ruling stands: structural integrity may improve while gates regress and the run can
still be a keeper.
