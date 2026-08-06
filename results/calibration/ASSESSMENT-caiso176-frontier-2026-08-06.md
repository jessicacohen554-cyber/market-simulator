# ASSESSMENT — caiso-176: the CAISO frontier, re-run on the caiso-175 keeper

**Keeper:** `2026-08-06-caiso-175-tac-intake` · CALIBRATED-WITH-CAVEATS · 0 FAILs · 9/9 scored ·
DOF `n_entries` 11 / `n_residual` 8.
**NO LP, NO SOLVE, NO year outside 2023–2025.** Every number below is read from committed
artifacts, or from a **live** re-run of a walled-route survey. `holdout-freeze.json` and
`calibration-complete.json` are UNTOUCHED.
Pre-registration: `PRECHECK-caiso176-frontier-dof-2026-08-06.md`.

---

## 0. Headline

**The frontier holds, and it is now measured on a keeper two promotions newer than the last
assessment.** Every caiso-173 check re-runs clean, the one demand-input gap it left open is
CLOSED on data, and CAISO's ISO-specific DOF count has fallen 4 → 3.

**The `final` recommendation is NO — and it does not rest on a judgement about model quality.**
CAISO's locked-test tier is **not executable**: the ISO has **no 2019 price bench, no 2019
calibration reference and no 2019 renewable-capacity input** (source-walled, not un-fetched),
and H1-2026 has a price bench but **no 2026 calibration reference at all**, so the volume and
fuel-mix criteria could not be scored on either year. Granting `final` today would authorize a
touch-once one-shot that **cannot be run**, and the realistic failure mode is worse than
useless: it would be spent on a partial score.

---

## 1. What re-ran, and what it returned

| check | result |
|---|---|
| `caiso173_frontier_recheck.py` (committed artifacts, live registry resolution) | ran clean on the new keeper |
| G0 FFR-4D epoch gate | **KEEPER IS POST-EPOCH** — `storage_measured_base_fleet` present in its `run_config.json` |
| `mechanism_matrix_gap_sweep.py --iso CAISO` | **0 / 0 / 0 / 0 / 0** over 63 family fields |
| CAISO matrix column census | **61 K · 23 U · 14 I · 6 R · 5 G · 5 O** (was 60/20/13/6/5/**6**) |
| §5.2 evidence documents (probe F5) | **19 of 19 resolved, 0 missing** |
| `audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings |
| `calibration_verdict.py --run-id 2026-08-06-caiso-175-tac-intake` | CALIBRATED-WITH-CAVEATS, 0 FAILs, C3a + C3c ledgered, C7 **PASS**, C8 **PASS** |
| `check_mechanism_matrix.py --base origin/main` | gap ratchet **OK**, shared ratchet **OK** (anchor warnings pre-existing, other lanes) |
| `check_registry_payload_parity.py` | **OK** — 76 runs, 0 unsynced |
| `check_cache_key_registration.py` | **ok** — 693 fields, 139 registered, all resolve |
| **Wall 1** (C3a, non-public hourly pumped storage) — `_caiso141_water_source_survey.py`, **LIVE network** | **5/5 `unchanged`** |
| **Wall 3** (C3c, the SoCalGas OFO declaration record) — `data/raw` census | **HOLDS** |

**The `O` count fell 6 → 5** because `storage_measured_base_fleet` moved off `O` at caiso-174 —
the item caiso-173 named as "different in kind" from the other five.

### 1a. The walls are re-verified, not assumed

**Wall 1 re-ran live and returned `unchanged` on all five routes.** S1: the EIA-930 API carries a
`PS` fuel category but **CISO publishes 0 PS rows**. S2: CAISO Outlook per-day hydro against
EIA-930 `WAT`, n=72, **corr 0.950**, mean abs diff 287 MW — the same PS-net feed, not a separate
one. S3: Outlook `storage.csv` is battery-only (`Total / Stand-alone / Hybrid batteries`).
S4: CDEC hourly sensors at **CTG 0 / WSN 0 / SHV 0** — Courtright, Wishon and Shaver, i.e. Helms
(1,053 MW) and Eastwood (199.8 MW), **60.3 % of the fleet, uninstrumented**. S5: the sub-BA route
is demand-only.

**Wall 3 holds on disk.** The only SoCalGas artifact anywhere under `data/raw` is
`gas-prices/pge_socal_citygate_weekly.csv`, a **price** series. Nothing carries OFO event windows.

Neither wall was re-opened, and neither may be closed with an adder, haircut or overlay
(rules 1 / 13; caiso-142 §H; caiso-144 §D).

### 1b. caiso-173's one open demand-input gap is CLOSED on data

caiso-173 §C carried MWD-TAC as a named open defect worth 0.24–0.30 % of ISO load. Measured on
the current committed series by the same probe leg:

| year | TAC areas | MWD present | ISO total | modelled | **unmodelled** |
|---|---:|---|---:|---:|---:|
| 2023 | 6 | yes | 25,023.6 MW | 25,023.6 MW | **+0.0 MW (+0.00 %)** |
| 2024 | 6 | yes | 25,598.8 MW | 25,598.8 MW | **+0.0 MW (+0.00 %)** |
| 2025 | 6 | yes | 25,664.4 MW | 25,664.4 MW | **+0.0 MW (+0.00 %)** |

`CAISO_TAC_ZONE_WEIGHTS` now carries an `MWD-TAC` row. The gap is closed, not narrowed.

### 1c. DOF — CAISO's ISO-specific residual count fell 4 → 3

Bundles resolved **live** from each ISO's `keepers/<ISO>.json` → registry, never pinned:

| ISO | entries | residual | core | **ISO-specific** | marker | the ISO-specific entries |
|---|---:|---:|---:|---:|---|---|
| **CAISO** | 11 | 8 | 5 | **3** | yes | `battery_dispatch_adder`, `WECC_import_simultaneous.cap_mw`, `IMPORT/EXPORT_TRANCHES[CAISO]` |
| PJM | 19 | 6 | 5 | 1 | yes | `wefor_residual` |
| NYISO | 34 | 6 | 4 | 2 | yes | `NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']`, `IMPORT/EXPORT_TRANCHES[NYISO]` |
| NEISO | 14 | 5 | 5 | 0 | yes | — |
| MISO | 29 | 2 | 2 | 0 | NO | — |

CAISO remains the highest ISO-specific count, but it is **3, not caiso-173's 4** — the
`CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` entry became **measured** at caiso-172. Of the three that
remain, `WECC_import_simultaneous.cap_mw` is **not in the keeper's binding path** (the published
MIC sum is, binding 0/0/0 h) and `IMPORT/EXPORT_TRANCHES` is the class NYISO carries *while
holding its own marker*. **`battery_dispatch_adder` is the live one**, and §2 of the companion
FINDING is this session's work on it.

### 1d. KNOWN-OPEN 1, re-measured on the current keeper

| year | measured `NP15−ZP26` | congestion share | model | model / measured |
|---|---:|---:|---:|---:|
| 2023 | +5.947 | 80.2 % | +0.307 | **5.2 %** |
| 2024 | +8.576 | 87.2 % | +0.203 | **2.4 %** |
| 2025 | +5.727 | 81.7 % | +0.166 | **2.9 %** |

Unchanged in substance and **named, not buried**. No N–S topology lever is chartered off it
(caiso-164 §0/§6 stands).

### 1e. Reported against interest — a stale line in the re-check instrument

`caiso173_frontier_recheck.py` prints its "battery fleet the keeper did NOT see (measured minus
the flat 8,000 MW scalar)" block **unconditionally**, including when its own G0 gate has just
returned `PRE-EPOCH: False`. On this keeper those numbers (−507.6 / +3,131.3 / +7,448.4 MW)
describe a counterfactual that no longer applies. The gate verdict is correct; the block beneath
it is stale framing inherited from caiso-173, when the answer was the other way. Flagged, not
edited — it belongs to that probe's own lane.

---

## 2. THE DECLARATION QUESTION — does the evidence support recommending `final`?

**Recommendation: NO.** Three of the four pre-registered conditions fail, and the first fails on
plain arithmetic rather than judgement.

### F-a — IS THE TIER EXECUTABLE? **NO. This alone is dispositive.**

`final` authorizes a touch-once score of **2019** and **H1-2026**. CAISO's committed benches:

| input | file | CAISO years present |
|---|---|---|
| LMP bench (hourly) | `actual_lmp_hourly_CAISO.parquet` | **2023, 2024, 2025, 2026** |
| LMP bench (annual) | `actual_lmp.json` | **2023, 2024, 2025, 2026** |
| calibration reference | `calibration_reference.json` | **2021–2025** |
| renewable capacity | `CAISO_<y>_renewable_capacity.csv` | **2021–2025** |
| scored bench payloads | `frontend/data/backcast/bench/CAISO/` | **2023, 2024, 2025** |

* **2019 — NOTHING.** No price bench, no calibration reference, no renewable-capacity input.
  Not one scored criterion could be evaluated. And this is a **source wall, not an un-run
  fetch**: the 2026-07-31 CAISO intake binary-searched OASIS's retention boundary and found the
  **earliest DAM trade date served is 2023-04-19**, with 2018 / 2020 / 2022 all returning
  `ERR_CODE 1000` for DAM and RTM alike. Only hand-downloaded GRP bulk zips could close it.
* **H1-2026 — HALF.** The price bench exists (4,343 dense hours, DA \$20.22 / RT \$19.59) but
  there is **no 2026 calibration-reference block and no 2026 renewable-capacity input**, so
  C1 (fuel mix), C2 (system volume) and C4 (dispatch correlation) have no reference at all.

A one-shot that cannot be scored is not a test. Worse, the concrete risk of granting it is that
the tier gets **spent on the half that happens to resolve** — and rule 22 makes that
unrecoverable: *"scored EXACTLY ONCE per ISO … no calibration change may respond to a
locked-test result."*

### F-b — IS THE TIER ORDER RESPECTED? **NO.**

**CAISO has never spent its validation tier.** Its `complete` marker was granted 2026-08-05 and
the freeze has meant 2022 was never solved. The ladder is ordered by design: validation is the
**iterable** model-SELECTION step that exists to catch problems *before* the unrepeatable test
is burned. PJM and NEISO — the two ISOs the owner has actually let spend — both did 2022 first,
and NEISO has since re-spent it after an input repair, which is exactly the iteration the tier is
for. Recommending `final` for an ISO with **zero out-of-training evidence of any kind** inverts
that.

### F-c — IS THE INPUT ENVELOPE SETTLED? **NOT BY THE OWNER'S OWN STANDING CHOICE.**

The freeze is **ACTIVE**, re-armed 2026-08-06 after a narrow NEISO-2022-only lift. Its stated
basis — the CAMPD economic-layup over-count — has moved: the fix charter's §9 now records the
residual investigation **CLOSED ON EVIDENCE** across four lanes, with a recommendation to close
with cause and lift **fully**. **The owner deliberately did not take that step**, so the freeze
stands on its original basis and every out-of-training year for every ISO stays preserved.

Two things follow, and they point the same way. First, the freeze outranks any marker, so
`final` would grant nothing spendable today regardless. Second — and this is the CAISO-specific
part — **CAISO's own 2023–2025 outage windows were regenerated on the current detector** in the
2026-07-24 intake (2023 439→640, 2024 405→622, 2025 509→733 windows), which that intake_log
entry itself flagged for "a CAISO re-audit/re-solve … NOT solved or scored here." That re-audit
is still outstanding, and both caiso-173 §5 item 5 and the `complete` grant name it as a
precondition for spending **2022**. It is *a fortiori* a precondition for the locked tier.

### F-d — IS THE MODEL AT ITS FRONTIER? **YES** — necessary, not sufficient.

§1 establishes it: in-model lever queue empty, both ledgered caveats walled on live-re-verified
evidence, gap sweep 0/0/0/0/0, 19/19 evidence documents resolving, 9/9 criteria scored with
0 FAILs, and CAISO's last free parameter now carrying a measured bound (companion FINDING). This
is the `complete` criterion and CAISO clears it. It is not a `final` criterion.

### What would change the answer, in order

1. **Close F-a or accept a scoped tier.** Either land a CAISO 2019 bench (hand-downloaded OASIS
   GRP bulk zips — the only route the retention wall leaves) plus the 2019 calibration reference
   and renewable-capacity inputs; or the owner explicitly grants a **scoped** `final` naming
   H1-2026 alone, on the price criteria alone, with the 2019 half recorded as never-grantable
   until its bench exists. The second is a real option, but it must be written that way — an
   unqualified grant risks the tier being half-spent by accident.
2. **Spend 2022 first** (F-b), once the owner lifts the freeze for it.
3. **Re-audit the keeper on the corrected availability envelope** (F-c), which is owed before
   2022 regardless.
4. Only then is `final` a live question.

**This session writes no marker.** `calibration-complete.json` is untouched; `final` remains
empty; no locked-test year was solved, scored, read or registered.

---

## 3. Carried forward, unchanged

1. **KNOWN-OPEN 1** — the N–S congestion majority (§1d). Named, no lever chartered; an N–S
   topology lever stays FORBIDDEN.
2. **KNOWN-OPEN 2** — the caiso-170 within-day storage placement pointer. Untouched.
3. **The `run_d1` / `score_shape` gating inconsistency** — `run_d1`'s `gated` column screens on
   the class list alone while the rubric's `score_shape` screens on class list **and** load
   share, so `legitimacy_diagnostics.json` reads `Overall: FAIL` on CAISO `ST_GAS` where C7
   correctly reads PASS (0.6 / 0.4 / 0.1 % of load, under rule 21's 2 % floor). Still a clean
   scorer-only fix, still deliberately **not made here** — this session's frontier verdict would
   depend on the answer, which is the wrong session to change it in.
4. **CAISO `ST_GAS` diurnal shape is genuinely poor** (r 0.114 / −0.021). Below rule 21's
   materiality floor; recorded so the next material-class review does not rediscover it as new.
5. **Other ISOs' zonal load series have never been audited** for the coverage defect caiso-175
   found in CAISO's 2023 TAC series. Worth one no-LP sweep; not CAISO's lane.
