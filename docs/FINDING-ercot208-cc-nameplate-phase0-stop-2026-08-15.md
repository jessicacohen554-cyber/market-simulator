# FINDING — ercot-208: `cc_nameplate_summer_derate` at ERCOT **STOPS AT PHASE 0** on condition (c). The measured object is real; the ARM as built is not admissible, because no flag separates it from a second, ERCOT-adverse, unidentified mechanism

**Session ercot-208 (re-keyed from ercot-205, §10), 2026-08-15, branch `claude/ercot-scar-next-lever-ba5pso`,
rebased onto `origin/main` `714ad11`.** Charter: pick the next ERCOT lever from
the §5.1 queue + ERCOT shard `U` cells, run Phase 0 (read-only, committed
artifacts, no LP) on conditions (a)–(d), and **stop and report if any of them
fails** — the ercot-195 / ercot-201 precedent, where a correct stop is the
deliverable.

**NO LP WAS BUILT. NO YEAR WAS SOLVED. NO RUN WAS REGISTERED. NO PRECOMMIT WAS
PUSHED. THE KEEPER IS UNTOUCHED. NO LEVER WAS SUBSTITUTED.** Phase 0 failed at
condition (c) and the session stopped there.

Everything below is reproducible from committed artifacts by
`scripts/probes/ercot208_cc_nameplate_phase0.py` (output:
`results/calibration/ercot208_cc_nameplate_phase0.json`). Rule 13
`[R-MEASURED]`: every measured series is read for audit/attribution only — none
enters a model input. Rule 22 `[R-HOLDOUT]`: only {2023, 2024, 2025} artifacts
were read; nothing solved or scored in any year; no marker granted or spent.

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `cc_nameplate_summer_derate` — the **CC leg** (`CC_REGULAR` + `CC_CHP`), ERCOT shard cell `U` |
| **Keeper** | `2026-08-15-ercot204-rule26-delete` (bundle `results/calibration/ercot204_rule26_delete`), NOT-YET, fail set {C3a-2023, C3b-2023} — **UNCHANGED**. Promoted mid-session by another lane; every figure here is re-measured against it and is byte-identical to the superseded keeper (§2.1) |
| **(a) armed state** | **PASS** — genuinely unarmed on the keeper through all three channels (resolved `run_config.json`, `meta.json`, `prb_overrides`) |
| **(b) measured object** | **PASS** — sized at full magnitude below: net **−413.03 MW** (CC_CHP) and **+334.50 MW** (CC_REGULAR) of Jun–Sep capability, with per-plant moves up to ±168 MW |
| **(c) rule-13 identification** | **FAIL — DISPOSITIVE.** The arm is two mechanisms behind one boolean. Leg (i), the measured rating swap, is admissible. Leg (ii), the statistical POF + age-derate drop, has **no ERCOT identification**, its own in-code premise is **measurably false on this keeper**, and **no flag separates the two** |
| **(d) DO-NOT-REDO** | **PASS** — the cell is genuinely `U`; ercot-177 refused a *different* row (`temp_dependent_derate`, `R`) and deliberately left this row's cells unchanged |
| **Second, independent ground** | Rule 19 `[R-ONE-MECH]`: **76 % of the object by MW (CC_REGULAR, 33,349 MW) is DAM-covered** and is erased by the armed water-fill (ercot-177 §3). The one surviving class, CC_CHP, is **44.94 % force-dispatched by `chp_steam`** and is a **PINNED class excluded from the free-class score** |
| **Matrix** | cell stays **`U`** — no mechanism was tested (the ercot-202 rule: a viability check that cancels the test is not a test). Evidence citation extended |

---

## 1. Why this lever, and what was checked before it

Rule 28(a) `[R-MECH-MATRIX]` DO-NOT-REDO, run **before** any measurement. The
candidate board and its disposition:

| candidate | ERCOT cell | Phase-0 disposition, measured |
|---|---|---|
| `historic_outage_overlay` | `U` | **DISQUALIFIED at (a)** — resolved **`True`** on the keeper. The cell is stale, exactly the ercot-202 case; not opened |
| `cc_nameplate_summer_derate` | `U` | **SELECTED** — unarmed, ERCOT-own instrument, sibling coal leg already `K` on the same keeper |
| `gas_hub_basis_overlay` | `U` | Deferred: ERCOT *does* carry 36 basis rows for 2023–25 in `data/raw/gas_basis_by_iso_month.csv`, but they are an **EIA N3050TX3 citygate proxy** (an LDC delivered price, +2.93 $/MMBtu over Henry Hub in Jan-2023), not a plant-gate spot — and the keeper already arms `ercot_zonal_gas_basis` plus an annual level pin, a rule-19 collision |
| `winter_citygate_daily` | `U` | **NO ERCOT FIELD EXISTS** (`miso_winter_citygate_daily` is MISO-scoped) and **no Waha/HSC/Katy daily series is on disk** — ercot-160 screened both free paths and returned MANUAL/BLOCKED (owner licensing) |
| `gas_coldsnap_derate` | `U` | **NO ERCOT FIELD EXISTS** — `neiso_gas_coldsnap_derate` is NEISO-scoped; a rule-25 transfer needing its own build |
| `winter_fuelsec_posture` | `U` | **NO IMPLEMENTATION AT ALL** — a matrix row with no `ScenarioConfig` field in any ISO |
| `dual_fuel_switching` | `U` | Deferred: the field's own docstring scopes it to the winter-switching cluster "so ERCOT (no dual-fuel fleet behaviour) … [is] unchanged"; ERCOT delivered gas ran 2.19–3.52 $/MMBtu across the span, nowhere near distillate parity, so `min(gas, oil)` cannot bind |
| `maxgen_emergency_tier_pricing` | `U` | Deferred: the mechanism is **MISO-vocabulary throughout** — `MODEL_TZ_BY_ISO` carries MISO only, the tier floors are `MISO_EMERGENCY_TIER1/2_OFFER_FLOOR`, the level set is MISO's pre-2026 ladder, and `data/raw/maxgen-events/` holds **`miso/miso.csv` and nothing else**. An ERCOT arm is a data intake + a new ladder, not an arm |
| `diurnal_price_amplitude` | `U` | **NOT TOUCHED** — cross-ISO audit row, PRECOMMIT-ercot193 §0(b) refusal |

Also checked and **not** re-opened: ercot-195 (L-SCAR L-1, V0 FAIL, DO-NOT-REDO),
ercot-200 (regime conditioning, WAIT-FOR-DATA to the 2026 SOM), ercot-201 (L-2
E1 dispersion, identification barred), ercot-202 (T-1 `gas_hh_monthly_shape`,
already armed). The ruling-closed fail set {C3a-2023, C3b-2023} (Q-B final, R-A)
is untouched: this lever was chartered as **shape-quality / forecast-readiness**
work only, and no C3a-2023 or C3b-2023 round was contemplated.

## 2. (a) THE ercot-202 CHECK — PASS

Read from the **keeper's own resolved config**, never from `scenarios.py`
(`FINDING-ercot202-t1-nonviable-2026-08-14.md` §1: a class default is not the
keeper's value; five sessions carried the stale claim before it was caught).

| flag | resolved `run_config.json` | `meta.json` kwarg | `prb_overrides` |
|---|---|---|---|
| **`cc_nameplate_summer_derate`** | **`False`** | **`False`** | absent |
| `cc_winter_capability_basis` | `False` | absent | absent |
| `coal_nameplate_summer_derate` | **`True`** | `True` | absent |
| `summer_derate_basis_aware` | `False` | absent | absent |
| `use_campd_bins` / `plant_level_fleet` | `True` / `False` | — | — |
| `mode` / `outage_source` | `backcast` / `historic` | — | `historic` |
| `wefor_residual` | `0.02` | absent | `0.02` |
| `wefor_residual_groups` | **`["ST_CHP", "ST_GAS"]`** | absent | `["ST_CHP","ST_GAS"]` |

The keeper id was re-read from `frontend/data/backcast/keepers/ERCOT.json` at
HEAD and matches. **The flag is genuinely unarmed, and its coal sibling is
genuinely armed** — the asymmetry the matrix's two-row split records.

### 2.1 The promotion that landed mid-session, and why it moves nothing here

While this branch was open the owner promoted
`2026-08-14-ercot202-arm-plantphysics` → **`2026-08-15-ercot204-rule26-delete`**
(the ercot-204 rule-26 discharge). **This Phase 0 was re-pointed at the new
keeper and re-run in full — nothing was inherited and nothing was carried over
from the pre-promotion measurement.** The promoting lane's byte-identity claim
was re-verified here rather than trusted:

* **All 6 sidecars this probe reads are sha256-identical** across the promotion
  (`class_hourly_{2023,2024,2025}` and `system_{2023,2024,2025}`), e.g.
  `system_2023.parquet` = `c8b095cf1bbe5336…` on both bundles.
* **All 18 flags this Phase 0 turns on are identical** on both resolved configs
  — `cc_nameplate_summer_derate False`, `coal_nameplate_summer_derate True`,
  `summer_derate_basis_aware False`, `wefor_residual_groups ["ST_CHP","ST_GAS"]`,
  `ercot_thermal_dam_availability_plant True`, and the rest.

Every MW, hour and $/MWh below is therefore **numerically unchanged** by the
promotion, and `keeper_id_matches` is `True` against `keepers/ERCOT.json` at
HEAD. Block `phase0_f_keeper_promotion_invariance` in the artifact carries the
hashes.

## 3. (b) THE MEASURED OBJECT, AT FULL MAGNITUDE — PASS

**What arming changes on the ERCOT path.** ERCOT is the CAMPD-bin path
(`use_campd_bins=True`, `plant_level_fleet=False`), so `fleet_to_bins` — the
*non-ERCOT* analogue that rescales CC capacity to nameplate — **is not on this
path at all**, and no capacity is raised. What the flag reaches on ERCOT is the
availability builder, `data/fleet/arrays.py`, in exactly two places:

* **Leg (i), `arrays.py:823-829`** — the flat class summer haircut
  `_SUMMER_CLASS_DERATE` (CC 0.10, an **UNCITED FLAT APPROXIMATION** by its own
  registry comment) is replaced in Jun–Sep by each plant's **measured**
  `net_summer / nameplate` from EIA-860.
* **Leg (ii), `arrays.py:712`** — in a historic backcast, CC availability is
  set to `1 - wefor`, **dropping the statistical POF (0.05) and the age /
  performance derate** year-round.

**Leg (i), per class** (bins-sheet nameplate; measured ratio from the committed
EIA-860 Generator_Y Operable sheet, transcribed from
`campd_bins.cc_summer_capacity` with the same technology filter, per-plant
grouping and double-file clamp):

| class | plants | matched in 860 | nameplate MW | cap-wtd measured summer ratio | keeper flat multiplier | **Jun–Sep ΔMW** | DAM-covered |
|---|---|---|---|---|---|---|---|
| **CC_REGULAR** | 41 | 41 | 33,349.4 | **0.91003** | 0.90 | **+334.50** | **yes** |
| **CC_CHP** | 19 | 18 | 10,642.6 | **0.858125** | 0.90 | **−413.03** | **no** |

The class nets conceal much larger per-plant moves — which is the whole content
of the instrument, since a flat 0.10 can express none of it:

| CC_CHP plant | MW | measured ratio | ΔMW |
|---|---|---|---|
| Green Power 2 (55470) | 611.0 | 0.7247 | **−107.08** |
| Odyssey Energy Altura Cogen (50815) | 643.6 | 0.7551 | −93.24 |
| Houston Chemical Complex Battleground (50043) | 380.7 | 0.6908 | −79.63 |
| Channel Energy Center (55299) | 923.8 | 0.8227 | −71.42 |
| … | | | |
| Texas City Power Plant (52088) | 450.0 | 0.9289 | +13.00 |
| **C R Wing Cogen Plant (52176)** | 230.0 | **absent from EIA-860 CC sheet** | **+23.00** |
| **Deer Park Energy Center (55464)** | 1,176.0 | **1.0** | **+117.60** |

(CC_REGULAR spans the same way: Rio Nogales 0.7216 → −167.76 MW against Temple
0.9836 → +134.24 MW.)

**A behaviour of the arm that must not be discovered at the seam.** For a plant
with **no EIA-860 CC row**, `arrays.py:824-829` applies the measured ratio only
when it exists and **never falls back to the flat class value** — so arming
**removes the summer derate entirely** for C R Wing (230 MW), and equally for
Deer Park (1,176 MW, whose published ratio is 1.0). **1,406 MW of CC_CHP loses
its summer haircut outright**, inside a class whose net move is −413 MW.

**Leg (ii), sized on the committed constants** (`THERMAL_AVAILABILITY`) and each
plant's cap-weighted EIA-860 operating year, at the keeper's own `wefor` settings:

| class | cap-wtd online year | keeper base availability | arm base (`1 − wefor`) | Δ (age-derate leg) | MW at stake | POF also dropped |
|---|---|---|---|---|---|---|
| CC_REGULAR | 2002.6 | 0.938587 | 0.960059 | **+2.147 pp** | 716.1 | 0.05 |
| CC_CHP | 1998.9 | 0.941512 | 0.964401 | **+2.289 pp** | 238.3 | 0.05 |

**Months, hours and $/MWh** (keeper's own committed `class_hourly_*` and
`system_*` sidecars, P1, load-weighted ISO price). The reach figure is an
**UPPER BOUND**, stated as such: the class sidecar records dispatched MW, not
the availability ceiling, so the hours within ΔMW of the class's **own** observed
summer maximum are the largest set a capability cut could bind in, and the
committed artifacts cannot narrow it further without a solve.

| year | class | summer hours | ΔMW | reach ≤ hours | months | mean price in those hours | summer mean price |
|---|---|---|---|---|---|---|---|
| 2023 | **CC_CHP** | 2,928 | 413.03 | **324** (11.07 %) | **Jul, Aug, Sep** | **$246.37/MWh** | $60.86 |
| 2023 | CC_REGULAR | 2,928 | 334.50 | 9 (0.31 %) | Aug, Sep | $2,336.00 | $60.86 |
| 2024 | **CC_CHP** | 2,928 | 413.03 | **119** (4.06 %) | **Jun, Aug** | **$72.01/MWh** | $30.27 |
| 2024 | CC_REGULAR | 2,928 | 334.50 | 2 (0.07 %) | Aug | $75.44 | $30.27 |
| 2025 | **CC_CHP** | 2,928 | 413.03 | **76** (2.60 %) | **Jun, Jul, Aug, Sep** | **$81.95/MWh** | $33.58 |
| 2025 | CC_REGULAR | 2,928 | 334.50 | 10 (0.34 %) | Jul, Aug | $96.51 | $33.58 |

So the object is real and it is not trivial: a **−413 MW** Jun–Sep capability
correction on CC_CHP, upper-bounded to **324 / 119 / 76** hours (Jul-Sep / Jun+Aug / Jun-Sep) whose mean price
is **$246.37 / $72.01 / $81.95 per MWh** — squarely in the near-tail window.
**Condition (b) passes.**

## 4. (c) IDENTIFICATION — **FAIL**, and this is what stops the session

**Leg (i) is admissible, and would have been a good arm.** The instrument is
ERCOT's own fleet in the EIA-860 Generator_Y Operable sheet: the published
per-generator **Nameplate Capacity (MW)** and **Summer Capacity (MW)** of the 59
matched ERCOT CC plants, summed per plant, clamped at nameplate. Rule 13
`[R-MEASURED]`: it is a published physical rating, not an outcome — it
regenerates for any forward year from the next 860 vintage and responds to
changed conditions (fleet turnover, uprates/derates, retirements) with **zero
fitted scalars** and no residual content. Rule 14 `[R-ACCURATE]`: it replaces a
constant whose own registry comment calls it an *"UNCITED FLAT APPROXIMATION"*.
Rule 25 `[R-ISO-SCOPE]`: nothing is transferred — every ratio is an ERCOT plant's
own filing. And the **identical instrument on the identical sheet is already
armed on this very keeper for coal** (`coal_nameplate_summer_derate = True`),
which is the strongest in-ISO precedent available.

**Leg (ii) is not admissible, and no flag separates it from leg (i).**
`cc_nameplate_summer_derate` is a single boolean that also fires `arrays.py:712`.
Three measured objections, in order of severity:

1. **Its in-code premise is FALSE on this keeper.** The comment at
   `arrays.py:717-721` justifies dropping POF and the age derate on the ground
   that *"wefor is already capped to `wefor_residual` above for this
   overlay-covered class"*. The keeper's resolved `wefor_residual_groups` is
   **`["ST_CHP", "ST_GAS"]`** — **CC is not in it**, so the cap never applies and
   the premise does not hold. This is the ercot-202 failure mode one level
   deeper: not a stale doc, a **stale in-code precondition**.
2. **The keeper's own registered comment calls the same relief harmful here.**
   The `wefor_residual_groups` narrowing exists because *"the relief is only
   warranted where the class was actually availability-capped (ST_GAS 2024) and
   is **harmful where the class is already over (CC)**"*. Leg (ii) is that same
   relief, applied to CC, in a larger form (it drops POF and the age derate
   outright rather than capping WEFOR) — i.e. **+2.15/+2.29 pp of availability
   plus a 0.05 POF, ~954 MW across the two classes, on a class the keeper's own
   record says is already over.**
3. **It has no ERCOT identification at all.** Leg (i) is EIA-860. Leg (ii) is an
   assumption about CAMPD outage coverage inherited from the per-plant
   (`plant_level_fleet`) path this ERCOT keeper does not use, and it was never
   measured on the ERCOT fleet. Under rule 13 that is not an input; under rule 19
   `[R-ONE-MECH]` it is a second mechanism stacked on the first.

**Condition (c) therefore fails for the arm as built.** The object is
identifiable; the *flag* is not admissible, because arming the measured rating
necessarily arms an unidentified, ERCOT-adverse availability increase alongside
it, and the pre-registered discipline forbids discovering that at the seam.

## 5. Second, independent ground — rule 19 against two ARMED keeper mechanisms

Stated separately because it stands even if leg (ii) were split out tomorrow.

**(5a) 76 % of the object by MW is erased by the armed DAM family.** The keeper
arms `ercot_thermal_dam_availability` + `_hourly` + `_plant`, all `True`. The
measured extract `data/raw/ercot-thermal-dam-availability-hourly.csv` covers
**`CC_REGULAR`, `COAL`, `CT_PEAKER`, `ST_GAS`**. `FINDING-ercot177` §3 proved —
and this probe re-reads the same lines, `arrays.py:1616-1633` — that the
class-HOUR water-fill drives the cap-weighted class-hour mean availability to the
measured target `_t` **independent of `_cur`**, so any **pre-overlay**
availability edit on a covered class is erased at the class-hour mean; with
`_plant` armed each crosswalked plant is additionally pinned to its own measured
site-hour fraction. Leg (i) is applied at `arrays.py:823-829`, i.e. **pre-overlay**.

| class | Jun–Sep ΔMW | fate |
|---|---|---|
| CC_REGULAR (33,349.4 MW) | +334.50 | **ERASED** — inert-or-double-counting by construction |
| CC_CHP (10,642.6 MW) | −413.03 | survives (DAM-excluded) |

**(5b) The one surviving class is a forced, pinned class.** CC_CHP on this
keeper is:

* **44.94 % / 44.53 % / 36.73 %** force-dispatched by `chp_steam` (D-2 rows,
  2023/2024/2025: 11.8679 of 26.4056 TWh, 12.7122 of 28.5453, 10.1759 of 27.7011);
* a **pinned class** in C1 scoring and **excluded from the free-class score**
  (`metrics.json` → `free_class_score.pinned_classes` / `excluded_from_free`);
* and `min_gen` is clipped to availability at `arrays.py:2798`
  (`np.minimum(min_gen, pmax[:, None] * availability, out=min_gen)`).

So a −413 MW summer availability cut on CC_CHP is clipped **straight through to
the `chp_steam` must-run floor** that carries ~45 % of the class's energy: the
arm's surviving scope lands first on a **forced** leg, not on the economic merit
order, and it does so on the one class whose dispatch the rubric has already
declared not-free evidence. That is a rule-19 reconciliation against `chp_steam`
which no part of the current charter performs.

## 6. (d) DO-NOT-REDO — PASS, and the cell is genuinely `U`

Every cell checked, with what each says:

| shard cell (`docs/codebase-site/data/mechanism-matrix/ERCOT.js`) | verdict | bearing |
|---|---|---|
| `cc_nameplate_summer_derate` (:84) | `U`, ev ercot-177 §5 | **the lever — genuinely untested** |
| `coal_nameplate_summer_derate` (:86) | `K` | sibling leg, armed; the split ercot-177 §5 decided |
| `temp_dependent_derate` | `R` | **a different row**: an ambient dry-bulb *slope*, closed 2026-07-09 REJECTED WITH CAUSE; ercot-177 §5 explicitly left this row's cells `UUUUKU` unchanged |
| `summer_derate_basis_aware` (:85) | `.` | n/a at ERCOT (nameplate-basis fleet) |
| `cc_winter_capability_basis` (:89) | `U` | the caiso-186 sibling; inert with the parent off |
| `historic_outage_overlay` (:80) | `U` | **STALE — resolved `True` on the keeper**; §7 |
| `wefor_residual` (:88) | `K`, "registration only … no ERCOT evidence, no verdict" | leg (ii)'s neighbour |
| `gas_hub_basis_overlay` (:129), `winter_citygate_daily` (:130), `dual_fuel_switching` (:131), `gas_coldsnap_derate` (:146), `winter_fuelsec_posture` (:93), `maxgen_emergency_tier_pricing` (:43) | all `U` | the rest of the candidate board, §1 |
| `diurnal_price_amplitude` (:39) | `U` | **not touched** (PRECOMMIT-ercot193 §0(b)) |

§5.1 queue items checked: 0/0b (CC committed offer shape — a *price* lever, not
capability), 1 (CLOSED, ERCOT-137), 2 (C6 — now PASSing), 3 (CLOSED at
ERCOT-143, do not re-open), 4 (EXECUTED at ERCOT-145b), items 10–26 (all
EXECUTED/CLOSED; 11 is Q-B final, 13 re-adjudicated at ercot-192, 20 is the
ercot-177 temp-derate refusal, 25/26 are the ercot-186/188 lineage this keeper
carries). **No adjudicated `R`/`I`/`G` cell was re-tested.**

## 7. TWO RECORD DEFECTS FOUND ON THE WAY, REPORTED NOT FIXED

1. **`historic_outage_overlay` reads `U` in the ERCOT shard while the keeper's
   resolved config carries it `True`.** This is the ercot-202 pattern exactly —
   a cell that would send the next session to charter an A/B with zero delta.
   Not corrected here because this session tested no mechanism and edits no cell
   verdict (§8); flagged for the owner as a one-line hygiene fix.
2. **`data/fuel/hubs.py`'s `WINTER_GAS_BASIS_PATH` comment says "other ISOs
   remain header-only"** for `gas_basis_by_iso_month.csv`, but ERCOT carries
   **134 rows including a complete 2023-2025 span**. Whether those rows are
   *usable* is a separate question — they are an EIA N3050TX3 **citygate**
   proxy, i.e. an LDC delivered price (+2.93 $/MMBtu over Henry Hub in Jan-2023),
   not the marginal gas unit's plant-gate opportunity cost, and the ERCOT keeper
   already arms `ercot_zonal_gas_basis`. Reported so the next session does not
   read "header-only" and skip the check, nor read "rows exist" and arm them.

## 8. WHAT THE OWNER IS ASKED TO DECIDE (nothing is decided here)

1. **Is leg (i) worth a split?** The clean successor is a **new, separately-gated
   field** carrying leg (i) only — the measured per-plant Jun–Sep rating — with
   leg (ii) left where it is. That is a `ScenarioConfig` addition plus a matrix
   row (rule 28(c)), i.e. a build, and it needs its own charter. This session did
   **not** build it.
2. **If it is built, what is its scope?** Rule 19 admits it only on
   DAM-**un**covered classes, which at ERCOT is CC_CHP alone — and §5b says
   even there it must first reconcile against `chp_steam`. The honest reading is
   that the ERCOT-reachable object is **CC_CHP × Jun–Sep × ~324/119/76 hours**,
   and the reconciliation is the real work, not the arm.
3. **The unmatched-plant fallback.** Whatever is built, `arrays.py:824-829`'s
   silent "no EIA-860 row ⇒ no derate at all" behaviour (1,406 MW of CC_CHP,
   §3) should be a declared choice, not an accident of control flow.
4. **The two record defects in §7** — in particular whether
   `historic_outage_overlay`'s stale `U` cell is corrected now, given it is
   precisely the trap that cost five sessions at ercot-202.

## 9. GOVERNANCE — WHAT THIS SESSION DID NOT TOUCH

**No solve, no score, no registration.** No LP was built; no year was solved; no
run was produced, so rule 15 `[R-DASHBOARD]` has nothing to register and rule 16
`[R-ALLYEARS]` nothing to span. **No precommit was pushed** — Phase 0 failed, so
there is no A/B to pre-register, and pushing one would have mis-stated the
session's own state. No DOF ledger entry — no field was added, `n_residual`
stays 6.

**Rule 22 `[R-HOLDOUT]`:** ERCOT holds no `complete` and no `final` marker. Only
{2023, 2024, 2025} artifacts were read; nothing solved or scored; no
`--holdout-authorized` anywhere; no marker granted or spent.

**Standing rulings honoured, none re-litigated:** **Q-B** (no ERCOT C3a-2023
spend, FINAL) — 2023 appears here only as a training-span year of the keeper's
own sidecars; **R-A** (NOT-YET stands; no C3b-2023 round) — no C3b object was
formed. C3c stays the single ledgered CAVEAT (ACCEPTED MODEL-CLASS LIMITATION).
ercot-195 (L-1 non-identifiability), ercot-200 (WAIT-FOR-DATA), ercot-201 (L-2
identification barred), ercot-202 (T-1 withdrawn-on-premise) — none re-opened.
D2 composition freeze — untouched. `diurnal_price_amplitude` stays `U` and was
not read as a lever. The ercot-188/E2 named permanent limitation (offer-surface
P0 bit-identity FORFEITED) is inherited unexpired and unaffected.

**Rule 28 `[R-MECH-MATRIX]`:** the base matrix and the ERCOT shard were read
before any step. **No cell verdict was edited in any shard** — no mechanism was
tested, and rule 28(b) attaches to a mechanism test; per the ercot-202 ruling, *a
viability check that cancels the test is not one*. **No row was added** — no
`ScenarioConfig` field was created, so rule 28(c) is not engaged. The only shard
edit is an **evidence-citation extension** on the already-`U`
`cc_nameplate_summer_derate` cell, pointing at this finding.
`scripts/check_mechanism_matrix.py` exits 0.

**Rule 25 `[R-ISO-SCOPE]`:** nothing crossed an ISO boundary; no other ISO's
shard, keeper, bench or registry was touched. The MISO/NEISO-scoped candidates
(`winter_citygate_daily`, `gas_coldsnap_derate`, `maxgen_emergency_tier_pricing`)
were *read* to establish that they carry no ERCOT field — never transferred.

**Rule 27 `[R-PUSH]`:** all edits are local (Edit tool), pushed as exact on-disk
bytes; no core file was rewritten. **P2 stays archived** — no P2 flag, no
`--enable-legacy-p2`. **No new GitHub Actions workflow** — this is a private repo
and every runner-minute is billed; all work ran in-session. **No PR was opened
and nothing was merged** (cycle-8 convention).

## 10. THE SHORTHAND RE-KEY, ercot-205 → ercot-208 (twice)

This session opened as **ercot-205** on the then-current ledger
(`docs/calibration-log/ercot.md` at `915e9ed`: *"Next shorthand: ercot-205"*).
While it was open, **four** lanes landed on `main` ahead of it: **205** (the
owner-instructed keeper promotion), **206** (the ERCOT-FRONTIER-1 assessment),
and — during this branch's own first rebase — **207** (the `audit_keepers` E10
attestation-stamp hygiene fix). Main's log now ends *"Next shorthand:
ercot-208"*.

**This session therefore re-keys itself to ercot-208** — the finding, the probe,
the artifact and the log entry all carry 208. It re-keyed twice (205 → 207 → 208)
because the ledger moved under it mid-rebase; only this branch's own unmerged
artifacts were renamed either time. That departs from the
`ercot-203`/`ercot-202` precedent of *"noted, nothing renamed — it is an owner
call"*, and deliberately: those collisions were discovered **after** both sides
had landed, where renaming would rewrite filed history. This one was caught
**before merge**, where the re-key is free — and leaving it would have written a
**third** duplicate heading into a log this session's own §7 criticises for
carrying duplicated headings. No already-landed record is renamed by this
session; only its own not-yet-merged artifacts.

**Session consumed the ercot-208 shorthand.**

**Artifacts produced:** this finding;
`scripts/probes/ercot208_cc_nameplate_phase0.py`;
`results/calibration/ercot208_cc_nameplate_phase0.json`; the
`docs/calibration-log/ercot.md` entry; the ERCOT-shard evidence
extension. Nothing else.
