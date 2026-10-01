# PRECOMMIT — SCN-RESOLVE-G1-RECHECK + ERCOT-POLICY-ADDENDUM-B

**Lane** SCN-RESOLVE-G1-RECHECK (Task 1) + ERCOT-POLICY-ADDENDUM-B (Task 2) · **Model** Opus
(`claude-opus-5`) · **Date** 2026-09-07 · **Branch** `claude/scn-resolve-g1-recheck-t13bm6` ·
**DATA PROFILE** `code` · **LP budget** ZERO.

**Trigger** `FINDING-scn-ws5a-resolve-ercot-2026-09-07.md` §1.5 and §4 items 1–4.

Pushed **before any measurement**. Every gate and every prediction below is written without having
computed a single delta or duplicate count. Misses are reported at full magnitude.

---

## 0. What this lane is and is not

Two zero-LP tasks, both reading **committed artifacts only**:

1. **Task 1** — re-check the ruling-S5 **G1 identity** in the five sibling RESOLVE lanes (CAISO,
   MISO, NEISO, NYISO, PJM) with **fuel-type-qualified** resolution, because all five keyed it on
   `unit_id` and `unit_id` is **not a key** in an evolved fleet.
2. **Task 2** — the policy FINDING's owed **ADDENDUM B**: re-difference the eleven committed ERCOT
   policy legs against the **NEW** REF (`results/scn-campaign-load-2026-09-06-r2/ERCOT/REF`, key
   `de9c68e19316910e`, THE PIN `bdfb3095`), not the deleted pre-fix one.

**Not in scope, explicitly:** no LP of any kind; no `src/` or `config/` edit; no default move; no CI
workflow; no year past 2030; no other lane's regions; no PR. **This is the FORECAST track** — no
keeper, no rubric criterion, no `frontend/data/backcast/keepers/` touch.

---

## 1. Task 1 — the gates

All structural and **kill-only** (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`). A PASS promotes nothing.

| id | gate | predicate | STOP condition |
|---|---|---|---|
| **T1-G0** | **cache availability** | for each of CAISO/MISO/NEISO/NYISO/PJM, does `results/<ISO>/<leg cache_key>/` exist in this container with a readable `FleetContext` **and** `evolution_<year>.json`? | If ABSENT, the corrected per-unit G1 re-measurement is **NOT COMPUTABLE** here. The lane then **says so and states the replay cost** (T1-G4) — it does **not** estimate, interpolate or infer a deviation number. |
| **T1-G1** | **collision mechanism, at source** | Is the ERCOT duplicate a *general* mechanism or an ERCOT accident? Predicate: `data/fleet/legacy_bins.aggregate_fleet` re-mints `{fuel_type}_{efficiency_bin}_{zone}` for every aggregatable fuel at the end of **every** evolution year (`capacity_evolution/evolve.py`), while a retrofitted unit — `fuel_type = "gas_cc_ccs"`, which is **not** in `_AGGREGATABLE_FUELS` — passes through carrying the id minted under its **pre-retrofit** `fuel_type`. | PASS = confirmed in source and ISO-agnostic. FAIL = the mechanism is ERCOT-specific, and Task 1 reports the false-PASS risk as not generalisable. |
| **T1-G2** | **direction of the defect** | Which twin does `{u: i for i, u in enumerate(unit_ids)}` (last-occurrence-wins) resolve to? Decided from source: the order `aggregate_fleet` returns (`passthrough + representatives`), and whether the SoA → `FleetContext.unit_ids` persist path preserves list order. | Reported in whichever direction the source says. This gate **can overturn the routing premise** and is written to be able to. |
| **T1-G3** | **per-ISO exposure** | For each sibling ISO, is its retrofit cohort composed of **legacy bin representatives** (`{fuel}_{bin}_{zone}` — exposed) or **CAMPD per-plant tranches** (`is_campd_bin`, which `aggregate_fleet` passes through un-aggregated and which carry a `plant_code` — not exposed)? Evidence: the per-unit cohort rows each sibling lane published in its own FINDING. | An ISO whose cohort ids are **not published per-unit** is reported **UNKNOWN**, never assumed clean. |
| **T1-G4** | **replay cost, stated not guessed** | Per ISO: solve-years × the committed `total_wall_s` / `per_year_perf` in that ISO's own r2 legs, **plus** the `data/clean` regeneration precondition the ERCOT lane measured (~39 min, 56 datatypes / 1.5 GB). | Cost is quoted from committed artifacts; no extrapolated rate is presented as measured. |

### 1.1 Task 1 predictions, pre-registered

- **P-1 (direction) — the routing premise is WRONG and the defect is one-directional.** I predict the
  converted twin is **always at the LOWER index**: `aggregate_fleet` returns `passthrough +
  representatives`, a `gas_cc_ccs` unit is always in `passthrough` and the colliding unabated
  `gas_cc` bin representative is always in `representatives`, and the persist path
  (`unit_ids=list(fleet.unit_ids)`) preserves that order. Therefore last-occurrence-wins **always**
  grades the **unabated** twin, and this mechanism can produce a **false FAIL only** — the false
  **PASS** the ERCOT lane routed **cannot arise through it**. If the source says otherwise, that is
  a full-magnitude miss and the routing stands as written.
- **P-2 (cohort composition).** CAISO's and MISO's published cohort rows are CAMPD per-plant tranche
  ids (`CC_REGULAR_<zone>_p<plant_code>_{econ,committed}`), so I predict **both are structurally
  unexposed**. NEISO / NYISO / PJM cohort ids are **not published per-unit** in
  `FINDING-scn-ws5a-resolve-2026-09-06.md`, so I predict those three come back **UNKNOWN** and are
  reported as UNKNOWN.
- **P-3 (caches).** All five ABSENT (`results/<ISO>/` is gitignored; fresh container).
- **P-4 (the published counts cannot detect this).** Every sibling lane reported *units checked* ==
  *cohort size* in every year. I predict that is **not a detector**: the masking is a cohort
  member's id resolving to a **non-cohort** row, the lookup dict still holds exactly one entry per
  id, and the count is unchanged. So no published table can settle Task 1 either way.
- **P-5 (ERCOT reproduction, as a consistency check).** The ERCOT collision should be reproducible
  from the record alone: REF builds **3,000 MW gas_cc in 2030** (resolve FINDING §1.3 / policy §4)
  and new gas-CC is stamped `efficiency_bin = "h_class"` (`new_entry.py`), which re-aggregates into
  `gas_cc_h_class_North` — the very id the retrofitted 2030 unit already holds.

---

## 2. Task 2 — the gates

| id | gate | predicate | STOP condition |
|---|---|---|---|
| **T2-G1** | **base validity** | All eleven policy legs carry `git.sha == bdfb3095`, `git.dirty == false`; the new REF carries key `de9c68e19316910e` at the same pin. | Any leg off-pin is **excluded and named**; it is not re-differenced. |
| **T2-G2** | **read-back identity** | For every leg × year × quantity, the **old** delta recomputed from the committed `*_headline_deltas.csv` `arm − *_bau` columns reproduces the number the policy FINDING §2 quotes, to 1e-3. | A mismatch **STOPS** that quantity's addendum row — it means I am not reading the column the FINDING quoted, and the re-difference would be uninterpretable. |
| **T2-G3** | **2026–2027 invariance** | The FINDING labelled 2026–2027 **VALID** on the claim that the pin's seam is inert before `ccs_retrofit_available_year` 2028. Predicate: new REF's 2026/2027 absolutes are identical to old REF's on every headline quantity. | If any 2026–2027 REF absolute moves, the "valid" label was wrong and every 2026–2027 delta in §2 must be restated too. |
| **T2-G4** | **claim (a) — "the CCS retrofit row is a NULL for the policy reading"** | Re-scored per year from committed cumulative `gas_cc_ccs` capacity: new REF 0 / 2,763.8 / 5,763.8 MW at 2028 / 2029 / 2030 vs each arm's own. | Reported in both directions, per year. |
| **T2-G5** | **claim (b) — the +2.28 / +2.89 TWh unserved attribution** | Re-difference `unserved_mwh` for every arm against the **new** REF. | Reported at full magnitude whichever way it lands. |

### 2.1 Task 2 predictions, pre-registered

- **P-A (claim (a)) — the prompt's split is right and I expect to confirm it.** FALSE at 2028 (new
  REF converts 0 while the carbon and CES-premium arms convert 2,932–2,996 MW), TRUE at 2029–2030
  (new REF converts on its own). **Sharpened, and this is the part that can miss:** I predict the
  2028 conversion is **not** a property of "policy" in general but of the **carbon-priced and
  CES-premium** arms specifically — `VOL-HI` and `CES-T80` convert **0 MW at 2028** (policy FINDING
  §4), i.e. **`VOL-HI` reproduces the new REF's schedule 0 / 2,764 / 3,000 to the tenth of a MW**.
  So the correct statement is narrower than "the 2028 conversion is a policy response": it is a
  response to a **carbon or clean-attribute price**, and the two rows that carry neither reproduce
  the control exactly.
- **P-B (claim (b)) — I predict the prompt's expectation MISSES, and this is the lane's most
  falsifiable call.** The prompt says the +2.28 / +2.89 TWh "should largely close against this
  control". I predict it **does NOT close, and does not move at all**: the ERCOT resolve FINDING
  §2.1 measures REF's `unserved` as **byte-identical pre-fix → post-fix in every year**
  (127.2204 → 127.2204 TWh at 2030), so re-differencing against the new REF leaves every arm's
  Δunserved **unchanged to the reported precision**. The *attribution* is still wrong — the capture
  derate moves unserved by exactly zero — but the *number* survives intact and needs a different
  cause. **My candidate cause, stated in advance so it cannot be fitted afterwards:** the carbon
  arms' own **entry** difference — policy FINDING §4 records the carbon and CES-P10 arms building
  **+500 MW solar and gas_ct 500 → 0 in 2029** versus REF, i.e. 500 MW *less* firm capacity on an
  ISO already shedding 76 TWh. If the re-difference shows Δunserved moving materially, P-B is a
  full-magnitude miss and the prompt's expectation is confirmed instead.
- **P-C (2026–2027).** Every 2026–2027 policy delta in §2 is **unchanged to the digit**. A miss here
  would falsify the FINDING's own "VALID" labelling of those years.
- **P-D (direction of the 2028–2030 CO2 re-difference).** The new REF's CO2 is **lower** than the
  old REF's at 2029 (−7.95 Mt) and 2030 (−16.01 Mt) and **unchanged** at 2028. So every arm's
  ΔCO2 vs REF must move **toward zero (less negative) by exactly those amounts** at 2029/2030 and
  **not at all** at 2028. This is arithmetic, not a forecast, and it is registered as a gate on my
  own reading: if any arm's 2029/2030 ΔCO2 does not move by exactly +7.9521 / +16.0087 Mt, I have
  mis-joined the tables and T2-G2 has failed.
- **E-1 (magnitude, offered as a directional read, not scored).** Under P-D the carbon arms' 2030
  ΔCO2 goes from ≈ −26.6 Mt to ≈ −10.6 Mt — i.e. **roughly 60 % of the headline abatement the
  policy FINDING attributes to ERCOT carbon pricing at 2030 was the pin's own retrofit screen**.
  Offered as the reading that follows if P-D holds; the numbers themselves are the deliverable.

---

## 3. Deliverables

1. `docs/handoffs/FINDING-scn-resolve-g1-recheck-2026-09-07.md` — Task 1.
2. `docs/handoffs/ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md` — Task 2, with a pointer added
   from `FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §7 item 1.
3. A **card** opened on the desk ledger for the code question (fleet builder emitting unique ids vs
   every consumer qualifying by fuel type) — **proposed, not implemented**, per the charter.

Every number either lane cites lives in these documents (rule 29(c) discipline): the artifacts are
committed already, and nothing in this lane produces a bundle.
