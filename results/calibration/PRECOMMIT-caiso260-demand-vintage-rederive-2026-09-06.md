# PRECOMMIT — caiso-260: the keeper's demand input was derived on a bench vintage its scoring bench no longer has. **The arm is the committed producer run unchanged on the current bench — zero new parameters, zero threshold changes, one measured input brought back onto the vintage the run is scored against.** Registered before the estimator is re-run, before phase 0, and before any LP.

**Session caiso-260, 2026-09-06.** Branch
`claude/caiso-258-backcast-calibration-b1nal9` (continuation). Keeper
**`2026-09-06-caiso-257-b1-ctonly`** (bundle `caiso257_ctonly`),
DETERMINATION **CALIBRATED** (rubric v3.6), C3c-2024 the single ledgered
caveat; C4-2025 gas NRMSE **0.300 against ≤ 0.30, zero margin**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze ACTIVE.
**There is no rubric failure to tune.**

---

## §0 — THE OBJECT, AND WHAT HAS ALREADY BEEN SEEN

`ASSESSMENT-caiso259 §8`: a `--help` probe ran
`derive_caiso_supply_consistent_demand.py` (it takes no arguments) and the
regenerated 2023–2025 artifacts differed from the committed ones — max
|Δdemand| **1,452 / 863 / 583 MW** in an hour, annual **+69 / −33 / −753
GWh**, the moved column `cems_gas_grid_mw`. The files were restored
byte-exactly. **Those six numbers are the only values of this object anyone
has seen, and they are this document's G-REPRO target, not a result.**

**Cause, from the provenance sidecar:** the committed artifact carries CEMS
anchors `gas_cems_grid` **60.344 / 53.428 TWh** (2023/24) and cogen **8.399**
TWh, while the bench parts C1/C4 score against today carry **62.209 / 54.588 /
44.429** and cogen **6.604 / 6.416 / 6.416** — the CEMS plant map the
caiso-196 (El Segundo remap) and caiso-199/200 (Desert Star, member panel)
landings widened after the artifact's 2026-07-13 vintage. Note what that
means for the shape: in 2023 the annual level barely moves (+69 GWh) because
~1.8 TWh moved *from the flat cogen block into the hourly CEMS block*; **the
arm is a shape change at the hours those plants ran, not a level change.**

### §0.1 — Admissibility

* **Rule 14 `[R-ACCURATE]`:** the re-derived series is the more faithful
  input by construction — it is the caiso-80 Option A basis (owner-signed,
  `FINDING-caiso80 §6`: *"the model's demand basis becomes identical to the
  honest basis it is scored against"*) evaluated on the bench the run is
  actually scored against. Keeping the stale artifact keeps a demand basis
  that is *not* identical to the scoring basis, which is the defect caiso-80
  was written to remove.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the derive is not edited, no threshold or
  window moves (`_ANNUAL_GUARD`, `_ANCHOR_TOL` untouched), and it re-runs
  **because its source data updated** — the bench parts' CEMS plant map
  (caiso-196 `5f3e35c5`, caiso-199 `da33e509`, caiso-200 `cf156483`), cited
  here as the source-data change. Not because a residual moved: no residual
  is named as the reason and none may be.
* **Rule 13 `[R-MEASURED]`:** every term is a measured input (930 cells, CEMS
  hourly, 923 blocks, measured TI); nothing is an outcome pinned back.
* **Rules 21/24:** zero new parameters, zero `ScenarioConfig` fields; the DOF
  ledger is expected byte-identical at 9 entries / 6 residual.

### §0.2 — The C3a pattern, declared before anything is solved

caiso-257 was the **eighth consecutive** CAISO promotion whose C3a moved
favourably while excluded from its basis. If this arm is promoted and C3a
moves favourably again it will be the ninth, and that streak is the shape
selection bias takes. **C3a is EXCLUDED from every gate and from the promotion
basis in both directions**; its direction is reported once and quoted nowhere.
The arm's own first-order C3a direction is not knowable before phase 0 (it
depends on the sign of Δdemand in the hours that set the load-weighted mean).

### §0.3 — The C4-2025 constraint (handoff item B)

The pre-solve check is a **direction statement, computed in phase 0 and
recorded in the ADDENDUM before the screen**, never a solve: from the
caiso-252 anatomy the CC error is positive at night/evening and negative
mid-day, so **demand rising where the gas error is already positive worsens
C4-2025, demand rising where it is negative improves it**. The registered
statistic is `S = Σ_t e_t · Δd_t` over 2025 with `e_t` the keeper's CEMS-basis
gas error (the caiso-258 instrument): `S > 0` ⇒ expected worse, `S < 0` ⇒
expected better, magnitude reported as a first-order bound (`|ΔMSE| ≤ 2|S|/T
+ Σ Δd²/T`, since at most all of Δd is served by gas). A C4-2025 flip over
0.30 is **supporting-tier, does not block, and is the first line of the
FINDING** if it happens (handoff promotion basis).

---

## §1 — THE ESTIMATOR AND G-REPRO (stop gate)

Run the committed derive **unchanged** at HEAD; diff the regenerated three
CSVs against the committed bytes column by column.

| # | registered | tolerance | if it fails |
|---|---|---|---|
| **R-1** | the derive's own guards pass (`_ANCHOR_TOL` 0.1 TWh; `_ANNUAL_GUARD` windows) with no edit | exact | STOP — the producer no longer runs on its own inputs |
| **R-2** | max \|Δdemand\| = **1,452 / 863 / 583 MW** and annual Δ = **+69 / −33 / −753 GWh** (2023/24/25) | ±1 MW, ±1 GWh | STOP — the artifact or the bench moved since caiso-259 |
| **R-3** | the ONLY moved input column is `cems_gas_grid_mw`; `netgen_mw`, `ng_cell_mw`, `ti_mw` byte-identical; `Δdemand_t ≡ Δcems_t + Δflat` with `Δflat` a constant per year | exact / < 0.01 MW | STOP — a term other than the coverage change moved |

## §2 — PHASE 0 (ZERO LP): what the arm changes, before it is solved

Computed on the regenerated files against the committed ones, recorded in
the ADDENDUM:

1. **Δdemand by hour-of-day and by month**, per year; the constant `Δflat`
   split out so the hourly-CEMS term is read on its own.
2. **Sign and size at hod 22–23 and in the belly (hod 10–15)**, the two
   blocks caiso-252/258 name.
3. **Attribution of Δcems to plants**: which bench plants' hourly series
   entered (expected: El Segundo 57901, Desert Star 55077) — read from the
   bench part's plant map, no solve.
4. **The footprint `F(y) = Σ_t |Δdemand_t|` (gross MWh moved)**, per year,
   with the net beside it. **The screen year is `argmax_y F(y)`**, fixed
   by this rule before F is computed. The handoff expects 2025 on the net
   −753 GWh; **the gross rule governs** and P-2 below says what I expect.
5. **The C4-2025 statistic `S`** (§0.3) and its bound.
6. **G-DRIFT by measurement**: `_caiso255_gdrift_identity.py --keeper-sha
   <caiso257 meta.json git_sha>`, launched with the artifact in its
   COMMITTED state. **It rebuilds both shas on one data tree and therefore
   cannot see the artifact change**; the demand matrix is differenced
   separately in this probe (committed vs regenerated) and that difference
   is the arm. Any LIVE code hunk on the CAISO backcast path ⇒ G-CTRL form
   4 is void and the session stops to report (no control solve is spent to
   find out — rule 29(b)).

## §3 — THE SCREEN (ONE year, rule 29; STOP-only, may never promote)

Replay the keeper recipe on the screen year with the regenerated artifact on
disk (`scripts/replay_keeper.py results/calibration/caiso257_ctonly
--out-dir results/calibration/caiso260_screen<year> --years <year>`,
`MARKET_SIM_P1_BASIS_SEED=0`), preconditions per `ADDENDUM-caiso257 §7`
(seam cap `mic_partition`, hydro partition present, outage/tranche sha256
identical, **"P1 route: COLD REBUILD"**).

| gate | registered | verdict rule |
|---|---|---|
| **G-IDENT** | Σ CAISO-zone `demand` in the arm's `system_<year>.parquet` equals the regenerated artifact's `demand_mw` to **< 1 MW every hour** (and differs from the keeper's by exactly Δdemand) | FAIL ⇒ the arm did not run the artifact; STOP |
| **G-FOOT** | nuclear / wind / solar each move **< 0.5 %** of keeper annual energy (they have no demand coupling beyond curtailment); hydro, storage, import and every gas class REPORTED | FAIL ⇒ STOP and escalate |
| **S-3 (C1 stop)** | no class PASS → FAIL against the keeper `_verdict.json` C1 records' actual ± tolerance | flip ⇒ STOP and escalate |
| **S-3b (C3b stop)** | C3b NRMSE stays ≤ 0.20 in the screen year | flip ⇒ STOP and escalate |
| **S-4 (C4)** | gas r / NRMSE by the caiso-252 construction — **REPORTED, EXCLUDED** (handoff: a 2025 flip over 0.30 does not block; it leads the FINDING) | — |
| C3a | **EXCLUDED both ways**; reported once | — |
| `co2` | never differenced | — |

**The screen may kill; it may never promote.** It clears ⇒ ONE
`--years 2023 2024 2025` invocation into `results/calibration/caiso260_demand_vintage`
(rule 16), registered the same session (rule 15), the screen bundle deleted
before merge (rule 29(c)).

## §4 — PROMOTION BASIS (the owner's ruling in the handoff, verbatim in substance)

*"Structural integrity improving while gates regress MAY still be a keeper."*
The re-derived demand is the more faithful input by construction (rule 14).
Promote iff **(a)** G-IDENT holds on the full span, **(b)** governance holds
(C6 attested, C8 PASS), **(c)** every load-bearing criterion that regresses
to a NEW FAIL in any year is reported at full magnitude and put to the owner
in the FINDING **before** the keeper shard is edited. C3a and C4 enter
neither (a)–(c). A load-bearing new FAIL therefore does not by itself refuse
promotion under this ruling — it stops the session at the FINDING for the
owner's word, and the keeper shard is not touched until it is given.

## §5 — PREDICTIONS, WRITTEN TO BIND

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| P-1 | R-1/R-2/R-3 all hold | the object is not what caiso-259 measured; stop |
| P-2 | the gross footprint names **2025** as the screen year (net −753 GWh dominates) | 2023's larger hourly swings (1,452 MW) make it the gross maximum; the rule picks 2023 and the handoff's expectation was wrong |
| P-3 | Δcems is carried by **El Segundo and Desert Star**; no other plant contributes > 10 % of Σ\|Δcems\| | the coverage change is broader than the caiso-196/199/200 landings and needs its own attribution before the arm is solved |
| P-4 | Δdemand at hod 22–23 in 2025 is **negative** (the −753 GWh is night/evening-weighted, where the 2025 CEMS block shrank) | it is positive there, adding load exactly where the CC over-run lives |
| P-5 | `S < 0` in 2025 (expected C4-2025 direction: better) | `S > 0`: the arm is expected to push the zero-margin cell over 0.30, and the FINDING leads with that |
| P-6 | on the screen year, the class response is confined to gas + import + storage; nuclear/wind/solar < 0.5 % | a renewable move means the artifact changed curtailment economics, which is a second mechanism |
| P-7 | no load-bearing criterion flips PASS → FAIL on the full span | a flip goes to the owner under §4(c) |
| P-8 | DOF ledger byte-identical, 9 / 6 | the arm added a row, which it cannot |

**No prediction about C3a's direction is made**, on purpose.

## §6 — STOP RULE

1. G-REPRO (R-1/R-2/R-3) fails ⇒ STOP before phase 0 is quoted.
2. G-DRIFT finds a LIVE hunk ⇒ STOP and report; no control solve.
3. Any STOP gate of §3 fails on the screen ⇒ the arm dies; the artifacts
   are restored to their committed bytes with `git checkout`; 2024/2025 are
   never spent.
4. No gate is relaxed, re-run to a pass or redefined after its result; the
   derive's guards are never edited.
5. No `ScenarioConfig` field; no `complete` marker (owner act — raised in
   caiso-259 §7, not granted); `program-status.json` untouched.
6. The derive is run **only** inside §1's estimator (and, if promoted, once
   more to land the files); never casually.

## §7 — SEQUENCE

1. This document — **pushed first**. 2. G-DRIFT probe launched with the
artifact committed. 3. Estimator (§1) → phase 0 (§2) → **ADDENDUM** with the
measured screen year, `S`, the predictions scored, and the G-DRIFT verdict —
**pushed before the screen**. 4. Screen (§3). 5. Full span; register;
attestation (`gen_caiso260_attestation.py` from the caiso-257 pattern,
re-pointed); `calibration_verdict.py --run-id`; FINDING; then, iff §4
holds, `keepers/CAISO.json`, `build_status.py --iso CAISO`,
`audit_keepers.py --iso CAISO`, the keeper-auditor agent, rule-15 prune of
the superseded keeper, matrix shard stamps, calibration-log entry. 6. Screen
bundle deleted before merge.
