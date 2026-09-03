# PRE-DECLARATION — capx D46: the BATCHED RE-MEASURE (Stage 1), a baseline refresh of every stale forecast-family key at HEAD

**Lane:** capx D46 — the batched re-measure the director queued at r#30/r#31 and
the owner scoped at r#32 (ruling Q32: STAGED — the cheap set now, the t1f tail
later). Branch `claude/capx-d46-remeasure-batch-oe1h77`, FRESH off `origin/main`
`32e07427`. **Pushed BEFORE any solve started.** Predictions below are graded at
full magnitude in the finding, misses included, and nothing here may be
re-narrated after a result is read.

**What this lane is.** A **BASELINE REFRESH, not an A/B.** Every registered
forecast bundle is stale on up to three independent axes that were each measured
on their own lanes already:

- **(i) Q30 / D44** — `fossil_announced_exits_enabled` flipped default-ON at
  `57088c33`. Every bundle solved before that commit carries `False`.
- **(ii) D41** — the CCS-retrofit fixed-cost constants re-identified onto ATB
  2024: `ccs_retrofit_capex_kw` 900.0 → **1521.4** $/kW and
  `fixed_om_gas_cc_ccs` 25.0 → **65.0** $/kW-yr.
- **(iii) keeper vintage** — CAISO (231→239→240), MISO (198→200→201→202),
  NYISO (159→177) all superseded since their forecast bundles solved.

**No attribution is performed and nothing is armed.** There are no per-ISO
controls in this lane: the axes were measured on D42 / D41 / the owner's backcast
lanes, and re-measuring them here would be re-testing adjudicated cells. What
this lane produces is a board that is TRUE at HEAD, plus a full-magnitude report
of every gate-leg flip that the refresh produced.

**Governing discipline (rule 14, inherited from D27/D28/D31/D37/D42/D45):**
faithful inputs move exits TOWARD recall and G3 may read WORSE — that is the
expected signature, not a regression. Nothing is sized to any residual and
nothing is re-tuned to a band. **NOTHING ARMS.** No `ScenarioConfig` field is
added or moved, no parameter value changes, no keeper / shard / marker moves,
and the backcast namespace is untouched (rules 12, 13, 22, 25, 27, 28).

---

## 1. Two scope corrections, stated before the first solve

**(a) The T1-F window is 2026–2030, not 2026–2050.** The dispatch prices the
Stage-1 t1f legs as "full-horizon 2026–2050". The t1f TIER as it is actually
registered is a **5-solve-year 2026–2030 gate run** — `neiso-t1f`'s live record
is `neiso-2026-2030-s4b-ara` (cache epoch `9a7f68fc7dcac931`), every committed
t1f sidecar spans 2026–2030, and `VERDICT_MAP` keys the bare t1f keys off
`<iso>-2026-2030-ff-t1-gate`. A 25-year window is additionally REFUSED by
`assert_schedulable` without `--full-solve-authorized`, and **this lane holds no
full-solve authorization for ERCOT or CAISO** (the §2.1b campaign authorization
covers NEISO's golden alone, Q13). Running 2026–2050 for ERCOT/CAISO would be
both an unregistrable tier mismatch and an unauthorized full-horizon campaign.
**Resolution: the three t1f legs run 2026–2030**, matching the keys they
overwrite. GOLDEN-2 keeps its own 2026–2050 window under its own authorization.

**(b) The NEISO T1-H leg reproduces the bare key's flag set, so it keeps
`--neiso-net-icr-requirement`.** The dispatch's posture rule has two halves that
diverge at exactly one leg: *"each leg is the ISO's LIVE default posture at
HEAD"* and *"read the last committed bare-key bundle's `run_config.json` for the
flag set … and change NOTHING except what HEAD's defaults changed."* The bare
`neiso-t1h` key is held by `neiso-2021-2025-realized-t1h-d37-armed`, whose ONLY
non-default flag is `neiso_net_icr_requirement=True` (D37, owner ruling Q28 —
"this measurement only"; the shipped default stays `False` and D37's own P9 flip
condition failed). Dropping the lever would introduce a FOURTH axis into a lane
whose whole discipline is that it attributes nothing: every flip I report at
NEISO would then be confounded by the lever rather than by (i)/(ii)/(iii). **The
second half governs: the flag set is reproduced, only HEAD's defaults move.** The
consequence is stated rather than fixed — the bare `neiso-t1h` key continues to
advertise a posture that is not NEISO's shipped default. That is D37's standing
decision, not this lane's to re-litigate; it is **routed to the director** as an
observation, and `neiso-t1h-d37-control` remains the unarmed-posture record.

**(c) D41's axis (ii) is INERT in all four T1-H legs, and that is checkable.**
`ccs_retrofit_available_year=2028` and `ccs_available_year=2030` at HEAD, and the
T1-H window solves {2021, 2023, 2024, 2025}. **No CCS retrofit decision can be
taken in any Stage-1 hindcast.** Axis (ii) therefore touches GOLDEN-2 and the
three t1f legs ONLY. This is asserted here so the finding can VERIFY it from the
per-year `evolution_<year>.json` ledgers rather than assume it — and it is the
same verification the rule-28 bounded exception (§6) depends on.

---

## 2. The legs, with cache keys and postures pre-declared

Every key below was computed at HEAD `32e07427` through the harness's own
resolution path (`build_config` / `reference_config` → `apply_iso_scenario_defaults`
→ `ScenarioConfig.cache_key()`), and **checked against all 88 cache keys committed
under `results/` — none collides with any of them, nor with any other leg here.**
Every leg gets a fresh out-dir and the harness redirects `CACHE_ROOT` into it, so
no pre-existing bundle can be served.

### 2.1 Stage 1a — T1-H hindcasts, `--start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics`

| # | leg | run id | bare key | expected cache key | keeper at HEAD | posture beyond HEAD defaults |
|---|---|---|---|---|---|---|
| H1 | NEISO | `neiso-2021-2025-realized-t1h-d46` | `neiso-t1h` (overwrite) | **`da19b85495178949`** | `2026-08-17-neiso-99-joint-p1` | `--neiso-net-icr-requirement` (§1(b)) |
| H2 | CAISO | `caiso-2021-2025-realized-t1h-d46` | `caiso-t1h` (**MINT**) | **`2c8cc7d19ccaed4c`** | `2026-09-03-caiso-240-b1-stgas` | none |
| H3 | ERCOT | `ercot-2021-2025-realized-t1h-d46` | `ercot-t1h` (**MINT**) | **`67d5dcc1ada2e2df`** | `2026-08-25-234-eastex-identity` | none |
| H4 | MISO | `miso-2021-2025-realized-t1h-d46` | `miso-t1h` (overwrite) | **`eff2c890746ec966`** | `2026-09-03-miso-202-unitclip` | none |

`fossil_announced_exits_enabled=True` on **every** leg (verified in the resolved
config, not assumed).

**Comparator provenance, stated per leg, because two of the four have no
like-for-like predecessor:**

- **H1** supersedes `neiso-2021-2025-realized-t1h-d37-armed` (key
  `313ba0612435b963`, sha `11735c1f`). Resolved-config delta vs this leg:
  **`fossil_announced_exits_enabled` only**, plus six fields that did not exist
  then and all default `False`. A clean single-axis comparison.
- **H4** supersedes `miso-2021-2025-realized-t1h-d33` (key `40173304213d39cd`,
  sha `80327d08`). Delta: the fossil flip, the two D41 CCS constants (**inert**
  per §1(c)), `entry_screen_diagnostics` `False`→`True` (**output-only**, fleet
  outcome byte-identical per D37, but cache-keyed at every value), plus
  since-added `False` defaults.
- **H2** MINTS `caiso-t1h`. Its indicative predecessor is
  `caiso-2021-2025-realized-t1h-d43-control` (key `3f924a5e9c5d57c3`, sha
  `d1905a18`), which differs on the fossil flip alone plus since-added defaults —
  so the comparison is nearly like-for-like even though the key is new.
- **H3** MINTS `ercot-t1h`. **There is no comparable predecessor.** The newest
  committed ERCOT T1-H legs (`…-d12c-armed` / `…-d12c-control`, sha `bf5e08f`)
  are an old vintage differing on 21–23 resolved fields, including four defaults
  that have since flipped ON (`storage_entry_availability_gate`,
  `storage_entry_cost_normalized_rank`, and in the control arm
  `entry_margin_exhaustion`, `entry_forward_reserve_leg`). Any H3-vs-d12c delta
  is **indicative only** and is reported as such, never as a dates-flip effect.

Existing long-id ERCOT/CAISO records are left **untouched**: the D43 pair stays
the dispersion baseline and the ERCOT c1joint / d12c legs stay where they are.

### 2.2 Stage 1b — GOLDEN-2 re-solve

| leg | run id | bare key | expected cache key | window |
|---|---|---|---|---|
| G | NEISO golden | `neiso-2026-2050-t3-golden3-bau` | `neiso-t3` (overwrite) | **`67678e58b2d0526c`** | 2026–2050 |

Recipe verbatim from `FINDING-capx-t3-golden2-2026-09-01.md` §3:
`run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050
--golden-posture --full-solve-authorized`, under
`MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`, years
sequential. Resolved-config delta vs GOLDEN-2's own bundle (key
`706e7ba8e6582d42`, sha `f0a13bf5`) is **exactly the three axes**: the fossil
flip and the two D41 CCS constants, plus since-added `False` defaults. This is
the cleanest three-axis leg in the batch.

Prior record preserved at **`neiso-t3-pre-d46`**; the existing preserved chain
(`-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`, `-pre-p2scope`, `-prera-2026-08-31`)
is untouched.

**Honest cost restatement.** The dispatch prices this leg at "~35 min, ~3.5 GB".
That is the **campaign solve alone**. Full rubric scoring as GOLDEN-2 did it
includes the FC-6 paired battery — four sequential ~30–35 min arms (`base`,
`carbon_plus25`, `gasup150`, `gaspm5`), measured at **2.30 h** in GOLDEN-2 §7.1 —
so the true leg cost is **≈3 h**, not 35 min. Stage 1 as a whole therefore prices
at ≈9–10 h against the dispatch's ≈8 h, before the ~40 min one-time `data/clean`
build this container needed. Legs are executed in the dispatch's order; whatever
does not land is reported as PENDING, never silently dropped.

### 2.3 Stage 1c — T1-F, `--golden-posture`, 2026–2030 (§1(a))

| # | leg | run id | bare key | expected cache key | pairing |
|---|---|---|---|---|---|
| F1 | NEISO | `neiso-2026-2030-t1f-d46` | `neiso-t1f` (overwrite) | **`6690e4d6d66bc819`** | paired with F2 |
| F2 | ERCOT | `ercot-2026-2030-t1f-d46` | `ercot-t1f` (overwrite) | **`873d8c0e6cab52ae`** | paired with F1 |
| F3 | CAISO | `caiso-2026-2030-t1f-d46` | `caiso-t1f` (overwrite) | **`772b1e5abc7fc80c`** | solo |

Scored `forecast_verdict.py --tier t1f`, registered
`register_forecast_run.py --summary … --kind t1f --label d46-remeasure`. Priors
preserved at `neiso-t1f-pre-d46` / `ercot-t1f-pre-d46` / `caiso-t1f-pre-d46`.

Rule 12: years sequential inside every invocation; at most two invocations
concurrent; **MISO and PJM never paired with anything** (neither is in Stage 1's
t1f set).

---

## 3. THE PREDICTIONS — graded at full magnitude in the finding

**Sign discipline (rule 14).** The dates channel is an *exogenous, vintage-gated,
reliability-floor-bypassing* step-1 input. It can only ADD exits. So every
prediction below says exits move UP; where the ISO's actual exits are small, UP
means the G3 error reads **WORSE**, and that is the predicted signature, not a
defect. Nothing here is a target and nothing is re-tuned to a band.

### 3.1 T1-H retirement rows — before-values and predicted direction

| leg | quantity | committed before | predicted direction | confidence |
|---|---|---|---|---|
| **H3 ERCOT** | `retire.total_gw` model | **0.000** GW (actual 2.294; err −1.000) | **UP off exactly zero** | HIGH |
| | `per_fuel` coal / gas_st model | 0.000 / 0.000 (actual 1.008 / 0.888) | **both UP off zero** | HIGH |
| | `retire.total_gw` err_frac | −1.000 | **toward 0** (may overshoot positive) | HIGH |
| | `retire.false_retire` | 0.000 GW, band PASS | **UP off zero; band may flip PASS→FAIL** | MEDIUM |
| | `retire.unit_recall_gt300` | n/a (`n_excluded_unreachable` 2/2) | **becomes scorable** — the dates channel is an admissible channel, so the reachable set is no longer empty | MEDIUM |
| **H4 MISO** | `retire.unit_recall_gt300` | **5/19 = 0.263**, FAIL | **UP to ≈16/19 ≈ 0.842 ⇒ band FAIL→PASS** | HIGH (D42 measured this exact leg) |
| | `retire.total_gw` model | 4.469 GW (actual 17.369; err −0.743) | **UP substantially**; err_frac toward 0 | HIGH |
| | `per_fuel` gas_cc / gas_ct / gas_st / oil model | all **0.000** | **all UP off zero** | HIGH |
| | `retire.false_retire` | 0.000 GW, PASS | **stays at/near 0.0, band PASS holds** | MEDIUM (D42: `false_retire` 0.0 on the armed leg) |
| **H1 NEISO** | `retire.total_gw` model | 3.645 GW (actual 4.997; err −0.271) | **UP; err_frac from −0.271 toward 0, possibly positive** | MEDIUM |
| | `per_fuel` oil / gas_ct model | 0.000 / 0.000 (actual 1.208 / 0.319) | **both UP off zero** | MEDIUM |
| | `retire.unit_recall_gt300` | 4/6 = 0.667, FAIL (bar 0.70) | **UP; band FAIL→PASS is a live possibility** | MEDIUM |
| | `retire.false_retire` | 0.959 GW / 26.3 %, FAIL | **frac falls** (gas_st's +199.9 % excess persists; denominator grows) — **band stays FAIL** | MEDIUM |
| **H2 CAISO** | `retire.total_gw` model | 2.240 GW (actual 0.293; err **+6.642**, already OVER) | **UP further ⇒ err_frac reads WORSE** | MEDIUM |
| | `per_fuel` gas_st / gas_ct model | 0.000 / 0.000 | **UP off zero** (the OTC-driven filed dates) | MEDIUM |
| | `false_retire` | 2.240 GW / 100 % — the entire model exit is **nuclear** | **`false_gw` UP in absolute terms; `frac_of_model` FALLS below 1.0** as genuine dated fossil exits enter the numerator's denominator | MEDIUM |
| | the 2.240 GW nuclear false-retire | present | **may or may not persist** — the keeper vintage (231→240) moves the price surface underneath it. **No prediction; it is read, not predicted.** | — |

**Cross-leg prediction:** `retire.total_gw` band is **FAIL on all four legs
before**; I predict it remains **FAIL on at least three of the four after** — the
dates channel closes the *recall* half of the retirement problem, not the
*magnitude* half, which D27/D31/D37 located on the margin side. A leg that flips
`retire.total_gw` to PASS would falsify that.

### 3.2 The three axes' predicted reach

- **Axis (i), the dates flip:** fires on **all seven** legs. Largest effect at
  ERCOT (exits move off literally zero) and MISO (D42-measured).
- **Axis (ii), the CCS constants:** **INERT on all four T1-H legs** (§1(c),
  verified from the evolution ledgers, not assumed). On GOLDEN-2 — NEISO, under
  RGGI, where D41 §4.4 says retrofits still clear but the bar rises from a
  28–35 % capacity factor to **56–85 %** — I predict **FEWER `gas_cc_ccs`
  conversions and the 3 GW/yr/ISO cap STOPS binding in at least one year it bound
  in GOLDEN-2.** This is the measurement D41 §7 explicitly routed as *"not
  determinable from committed artifacts"*; whatever it reads is the answer, and a
  cap that still binds every year falsifies my prediction. On the t1f legs: ERCOT
  is carbon-zero, so I predict **zero CCS conversions** there (D41's PJM/MISO
  result transferring on the same arithmetic, not on a transferred verdict);
  CAISO carries state carbon pricing and was **not dispositioned by D41** — I
  make **no prediction** for it and will report what it does.
- **Axis (iii), keeper vintage:** reaches CAISO (H2, F3) and MISO (H4) only among
  Stage-1 legs. It moves the calibrated offer/price surface underneath the entry
  and retirement screens. **Direction not predicted** — a keeper promotion is not
  signed to move a forecast quantity in any particular direction, and guessing
  one would be exactly the residual-reasoning rule 14 forbids.

### 3.3 What would make me stop

- Any solve failing, or any expected cache key not matching its realized key →
  **STOP and route**; the finding records the mismatch and nothing is registered
  at a key I did not declare.
- A `-pre-d46` key already existing in `ff-verdicts.json` → **STOP**; a preserved
  baseline is never overwritten.
- A leg needing a `ScenarioConfig` field, a parameter value, or an owner
  authorization I do not hold → **STOP and route.**

---

## 4. Registration plan (preserve-then-overwrite, the `-pre-d45` mechanism)

| bare key | prior record preserved at | new record | action |
|---|---|---|---|
| `neiso-t1h` | `neiso-t1h-pre-d46` | `neiso-2021-2025-realized-t1h-d46` | overwrite |
| `miso-t1h` | `miso-t1h-pre-d46` | `miso-2021-2025-realized-t1h-d46` | overwrite |
| `caiso-t1h` | — (**new key**) | `caiso-2021-2025-realized-t1h-d46` | mint |
| `ercot-t1h` | — (**new key**) | `ercot-2021-2025-realized-t1h-d46` | mint |
| `neiso-t3` | `neiso-t3-pre-d46` | `neiso-2026-2050-t3-golden3-bau` | overwrite |
| `neiso-t1f` | `neiso-t1f-pre-d46` | `neiso-2026-2030-t1f-d46` | overwrite |
| `ercot-t1f` | `ercot-t1f-pre-d46` | `ercot-2026-2030-t1f-d46` | overwrite |
| `caiso-t1f` | `caiso-t1f-pre-d46` | `caiso-2026-2030-t1f-d46` | overwrite |

`VERDICT_MAP` gains one row per new run id; where a superseded run id currently
points at a bare key it is re-pointed at that key's `-pre-d46` preservation, on
the `miso-t1h-pre-d31` / `-pre-d33` precedent — **a run must never render a
verdict its own score contradicts.** No unrelated row is touched.
`register_forecast_run.py` is a ≥300-line file, so every push touching it is
blob-verified against the local bytes (rule 27).

## 5. Board refresh

FC legs and gate (b)/(c) rows are re-derived for the four Stage-1 ISOs **only
where a record actually moved**; byte-identity is asserted for every untouched
row; **gate (a) is never moved by this lane.**
`scripts/check_gate_a_provenance.py` and `scripts/check_forecast_staleness.py`
are run before the records commit. (Both are expected to be **already failing on
CAISO / MISO / NYISO gate-(a) stamps** at the start — the r#32 §0ac finding, whose
repair belongs to the promoting lanes; this lane records the state it inherited
and the state it leaves, and repairs neither.)

## 6. Matrix (rule 28)

**No mechanism is tested here, so no cell verdict moves** — with the one bounded
exception the dispatch grants: where an ISO's `-pre-d46` baseline differs from
its new leg on the **fossil-dates axis ALONE** (same keeper, and **no CCS
decision in either leg — verified from the evolution ledgers per §1(c), never
assumed**), that ISO's `fossil_announced_exits_enabled` cell MAY be stamped with
its own measured verdict and citation (rule 25: own data). **On the pre-solve
reading, exactly one leg qualifies: H1 NEISO** (single-axis delta; keeper
unmoved; CCS unreachable in-window). H4 MISO carries the diagnostics flip as a
second delta and MISO's cell is already `K` from D42; H2/H3 mint new keys with
no `-pre-d46` baseline to difference; H4 and H2 also move on keeper vintage.
Every other cell stays as D44 left it, with this lane's evidence citation
appended.

---

*Pre-declaration authored and committed 2026-09-03 at HEAD `32e07427`, before any
D46 solve began.*
