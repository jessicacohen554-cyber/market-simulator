# RESULT — pjm-h3: the `pjm_reserve_pergen_sync` SCREEN, PJM 2022

**Session** `pjm-h3` · **ISO** PJM · **Date** 2026-09-13 · **Base** `origin/main` @ `7404ef12`
**Pre-registration** `docs/PRECOMMIT-pjm-h3-reserve-sync-2026-09-13.md`, pushed at
`ed6bb0996d2685884d1f05eb105c3bef4dea138c` **before any solve**. Its §5 gates are read here
exactly as fixed and are not re-specified.
**Owner ruling** re-opening the pjm-142 price-formation frontier: `docs/calibration-log/governance.md`
"## 2026-09-13 — OWNER RULING".

**PJM keeper `2026-09-11-pjm-d4-4-gasoutage` — re-scored BEFORE this session:
CALIBRATED, grade 8/8, zero caveats, zero fails, determination basis "all criteria pass,
governance attested."** (Rule 30(c): held-out years never downgrade PJM.)

> ## STATUS AT THIS COMMIT: **SCREEN IN FLIGHT — NO VERDICT YET.**
> This document is committed mid-session, deliberately and while the solve is still running, so
> that §5's gate READINGS and §7's phase-0 census are on the record with a timestamp that
> **precedes any arm number** (the pjm-169 §9.2 / pjm-170 §1.1 error is exactly the reverse of
> that, and it is forbidden). Everything below §1-§8 is measured from **committed artifacts and
> zero-LP reconstruction only**. The S1-S5 adjudication, the verdict, the keeper's AFTER re-score
> and the matrix stamp are appended in a later commit. **Do not read this revision as a result.**

---

## 1. WHAT I INHERITED, AND THE FIRST SHARD'S FAILURE

The shard this session was handed — `session_01SKY3Qo2snPS9N6UbrdWbaN`, branch
`claude/pjm-h3-syncarm-2022`, bundle `results/calibration/pjmh3_syncarm_2022` — **FAILED and
produced nothing.**

| check | result |
|---|---|
| session status | `SESSION_STATUS_ARCHIVED`, `status_bucket: SESSION_STATUS_BUCKET_FAILED` |
| its own last summary | *"pinned SHA verified; hydrating PJM data, launching solve"* |
| lifetime | 05:04:17Z → 05:14:35Z (~10 min — far short of a ~24 min PJM year) |
| branch on the remote | **absent** (`git ls-remote` finds no `claude/pjm-h3-syncarm-2022`) |
| rule 34(d) retrievability (`git ls-tree -r <sha> -- <bundle>`) | **not applicable — there is no sha; zero bytes ever existed** |

So there was nothing to recover, nothing to verify and nothing to archive (the session had already
archived itself). No FINDING doc existed on any branch to rescue under rule 33(f)(1). The
**probable cause**, stated because it changed how I wrote the retry prompt: a PJM year is ~24 min
of wall clock and the Bash tool ceiling is 10 min, so a foreground solve cannot complete — the
retry prompt therefore *requires* a background job with polling, and states a 45-minute budget
under rule 32(b)'s "longer single shard with the budget stated".

**The screen was therefore re-launched, not re-adjudicated from stale numbers.**

## 2. PHASE 0 — WHAT WAS ESTABLISHED AT ZERO LP BEFORE THE SOLVE

**(a) The arm is a STRICT ONE-FIELD DELTA.** Both declared prerequisites are already `True` in the
control's own recipe and every mutually-exclusive field is already `False`, read from
`results/calibration/pjm_d4_4_TP/meta.json`:

| field | control |
|---|---|
| `energy_reserve_coopt` | **True** (prerequisite, already armed) |
| `pjm_reserve_pergen` | **True** (prerequisite, already armed) |
| `pjm_reserve_supply_cap` | True |
| `pjm_reserve_pergen_sync` | **False** ← the arm |
| `pjm_reserve_online_gated` / `pjm_reserve_commitment_scoped` / `pjm_commitment_posture` / `pjm_reserve_pergen_size_split` | False (the rule-19 exclusions) |

So the admissible S1 delta set is exactly `{pjm_reserve_pergen_sync}` — no prerequisite needed
setting, and `replay_keeper.py --set pjm_reserve_pergen_sync=true` makes S1 satisfiable by
construction rather than by inspection.

**(b) The measured SYNC requirement EXISTS in every year — the arm is reachable at the input
layer.** `load_pjm_measured_sync_reserve_requirement` / `…_mad_…` (`results/scarcity.py:3160/3185`),
8,760 h, zero gaps, so neither family falls back to the Manual 11 §4.3 largest-single-contingency
rule:

| year | RTO `sr_req` mean / min / max MW | MAD `mad_sr_req` mean / min / max MW |
|---|---|---|
| 2020 | 1,710.3 / 1,480.6 / 2,728.0 | 1,690.2 / 1,480.6 / 2,728.0 |
| 2021 | 1,696.5 / 1,461.7 / 2,728.0 | 1,695.9 / 1,461.7 / 2,728.0 |
| **2022** | **1,712.2 / 1,481.4 / 2,753.0** | **1,711.6 / 1,473.9 / 2,753.0** |

The families the arm builds are named `pjm_sync` (RTO) and `pjm_sync_mad` (nested MAD)
(`reserves/spec.py:2689/2719`) — **the SYNC requirement (~1.71 GW) is SMALLER than the Primary
requirement it sits beside (~2.66 GW)**, which is the quantity S2 is really asking about: the
product only prices if ONLINE 10-min ramp falls to ~1.71 GW, and `FINDING-pjm-eas-screen-2026-09-07`
measured PJM's *deliverable* ramp at ~51 GW against a 2.64 GW Primary requirement (~19×).

**(c) The CONTROL's reserve market, measured on its committed sidecar** (`pass == P1`, 8,760 h):

| family | hours dual > 0 | % of 8,760 | mean $/MW | max $/MW | requirement mean MW |
|---|---:|---:|---:|---:|---:|
| `pjm_primary` | **0** | 0.0000 % | 0.000000 | 0.000000 | 2,663.3 |
| `pjm_primary_mad` | **2** | **0.0228 %** | 0.002703 | 12.259206 | 2,662.4 |
| *(any SYNC family)* | — | **n/a — the control has no SYNC product at all** | — | — | — |

This reproduces the PRECOMMIT §2 control figure (0.02 % of hours, mean ≈ $0.003) exactly.

**(d) CONVENTIONS, fixed before the arm landed** so no number could choose them:
`hod = hour % 24`; `h16-18 = {16,17,18}`; `h01-04 = {1,2,3,4}`. **Validated**: the control's own
load-weighted price on this convention peaks at **hod 16** and troughs at **hod 02**, which is
exactly what the rubric's committed D-A row reports for PJM ("peak h16 vs h17, trough h02 vs h02").
"The SYNC dual" is the **SUM** over the sync families present in an hour — the model's own
cross-family convention (CLAUDE.md rule 15: `system.reserve_price` is the cross-family SUM);
per-family values are reported alongside. "The energy dual" is the load-weighted mean zonal price
per hour (weights = that hour's zonal demand).

**(e) THE SCORING HARNESS WAS VALIDATED AGAINST THE CONTROL BEFORE ANY ARM NUMBER EXISTED.**
Following the documented pjm-d4-4 shard method (a `replay_keeper` bundle carries no `metrics.json`
and the committed control's carries no per-year numerics), each side is scored by substituting into
the registered payload (i) its own class TWh as a delta on `gmModel` and (ii) its own `lmp` block
rebuilt from `hourly/system_2022.parquet`. **Reconstruction is exact**: every one of the 9 zones'
`p` reproduces the committed payload **to the cent** and every `d` to 4 dp (AEP_Ohio 65.33,
ATSI 65.78, Central_PA 65.00, ComEd 63.39, Dominion 67.60, EMAAC 67.77, SWMAAC 69.07,
West_APS 65.45, external 56.93), `ordc.hoursGt200.model` reproduces at **3**, and the re-scored
control reproduces its committed verdict criterion-for-criterion.

**(f) The S5 CONTROL baseline, 2022, scored from committed artifacts:**

| criterion | tier | control status on 2022 |
|---|---|---|
| **C2** system volume | load-bearing | **PASS** ← protected |
| **C4** dispatch correlation | supporting | **PASS** ← protected |
| **C6** governance | protective | **PASS** ← protected |
| **C8** forced share (D-2) | protective | **PASS** ← protected |
| C1 fuel-mix | load-bearing | FAIL (CC_REGULAR +22.56 TWh, share +1.6 pp) — **target, excluded** |
| C3a mean LMP | load-bearing | FAIL (−10.7 %) — **target, excluded** |
| C3b price shape | load-bearing | FAIL (NRMSE 0.246) — **target, excluded** |
| C3c price tail | supporting | CAVEAT (ledgered; model 3 h vs RT actual 92 h) — not gated |

**A note on C6 that is NOT a mechanism finding.** A `replay_keeper` probe writes no
`calibration_attestation.json`, so C6 on the arm reads **`UNATTESTED`**, not `FAIL` — measured
directly by scoring a de-attested copy of the control. That is a property of the throwaway-probe
path (the same one the pjm-d4-4 shard flagged), not of the arm, and it is reported rather than
counted either way.

## 3. G-CTRL / G-DRIFT — FORM 4, NO CONTROL SOLVE SPENT

Rule 29(b): the incumbent keeper's committed bundle **is** the control. PJM's form-4 baseline is
already established and is not re-derived — the keeper's 833-field `cache_key()` is identical at its
`git_sha` and at HEAD, and since capx D79 that key carries the solve-surface fingerprint, so no
registry table, solve-surface row or config default the keeper touches has moved. Corroborated at
HEAD this session: `check_cache_key_registration --base origin/main` reads
*"844 ScenarioConfig fields, 299 registered … all resolve; 299 declared defaults all match HEAD;
305 solve-surface names across 7 module(s), all declared"*. **No control LP was spent or
authorized.**

## 4. GATE BASELINES AT `origin/main` @ `7404ef12`, TAKEN BEFORE I TOUCHED ANYTHING

| gate | baseline |
|---|---|
| `check_registry_payload_parity` | **1 RED — `results/calibration/caiso279_ablate_dswcouple_span`** |
| `audit_keepers --iso PJM` | PASS, 0 failures, 1 pre-existing E3 warning (keeper `meta.json` years `[2023,2024,2025]` vs `calibration_flags` years `[2020..2025]`) |
| `build_status --iso PJM --check` | in sync (1 keeper: PJM) |
| `check_mechanism_matrix --base origin/main` | warnings only, every one self-labelled *"pre-existing, not this PR"* |
| `check_cache_key_registration --base origin/main` | ok, no new fields |
| `check_gate_a_provenance` | **FAILS — NYISO only**, citing superseded keeper `2026-09-09-nyiso-221-fuelvintage-span` against the live `2026-09-12-nyiso229-hourgrain-span`. Not PJM, not mine. |
| `pytest tests/scoring` | **15 failed**, 1,474 passed — exactly the stated baseline |
| `check_bench_freshness` | 34 parts checked, **0 STALE**, 34 carrying engine drift |

**CORRECTION TO MY OWN BRIEF, reported rather than absorbed.** The handoff named **five**
pre-existing parity REDs — `nyiso227_rebasis_span`, `caiso275_B_gascoupling_{2023,2024,2025}`,
`spp36_2025`. **All five are gone from `main`** (`git ls-tree -r origin/main` returns 0 files for
each); they were pruned before this session started. The one RED that exists is a **different
bundle from a different lane** — `caiso279_ablate_dswcouple_span`, 34 files committed on
`origin/main` at `e24c0d90` (the caiso-279 session, merged after this brief was written). It is
pre-existing, it is CAISO's, it is not mine, and I did not `rm` it.

## 5. THE GATE READINGS, FIXED IN WRITING BEFORE ANY ARM NUMBER EXISTED

PRECOMMIT §5 fixes the *bars*. Three of them need a stated *reading* to be machine-checkable, and
**those readings are recorded here before the solve returned** — precisely so they cannot be chosen
once a number is on the table (the pjm-169 §9.2 / pjm-170 §1.1 error, which is forbidden). The
harness implementing them (`gates.py`, `adjudicate.py`) was written and **self-tested on the
null case** (control-vs-control) while the solve was still running.

* **S2 "the SYNC family's dual"** — measured on the SUM over the sync families present
  (`pjm_sync` + `pjm_sync_mad`) per hour, i.e. the union of hours in which the SYNC product prices
  at all. This is the reading most favourable to the arm, so a KILL here is unambiguous. Per-family
  counts are reported too.
* **S3 ratio when the trough mean is exactly zero** — a credit that is strictly zero at h01-04 and
  positive at h16-18 reads `+∞` and **PASSES**: it is maximally shape-like, which is what pjm-138 §7
  lead 1 demands. Both means zero reads 0 and KILLs (but S2 would already have killed).
* **S4** — both limbs must hold (`r ≥ +0.30` **AND** zero-hour mean |Δ| < 25 % of positive-hour
  mean |Δ|); its PRECOMMIT verdict word is **STOP**, not KILL. If S2 kills, `r` is undefined and S4
  is reported as **moot**, not as a pass.

**Gate-order discipline:** S1 first (a disallowed config delta ⇒ STOP, do not push). Then S2/S3 as
STOP-only structural gates. **S5 is scored over the PROTECTED set {C2, C4, C6, C8} ONLY.**
**C1, C3a, C3b, C3c, the annual price level and the D-A amplitude are TARGETS: reported at full
magnitude, gating NOTHING in either direction** (rule 1 `[R-STRUCT]` — an arm is never promoted by
its target improving and never killed by it either).

## 6. WHAT THIS SESSION DOES NOT CLAIM, STATED AT THE GATE

**The OVERNIGHT half of PJM's amplitude deficit is not this arm's claim and is not a gate here.**
PJM's overnight reserve price is small and the model's is zero, so the
**+$6.82 / +$5.78 / +$3.40** overnight over-pricing (2020/2021/2022) is untouched by anything
below. pjm-142's measured stack slope (2.88 / 3.37 / 2.57 GW per $1/MWh) says closing it needs
**9–20 GW** of stack movement, which no queued lever supplies. **A clean screen must not be read as
closing it**, and it is not read that way here.

The owner's re-opening licenses **structural** mechanisms only. Neither of the two things it
explicitly does not license was reached for: **no MIP** (the Stack mandate is untouched; this arm is
pure LP) and **no adder** (`ordc_scarcity_overlay` stays `G`).

## 7. PHASE-0 RAMP CENSUS — THE QUANTITY S2 TURNS ON, MEASURED AT ZERO LP

Rule 32(a) puts a phase-0 census in the parent (it is not a solve). The PJM 2022 keeper fleet was
rebuilt through `run_calibration.run_year` with **no LP** (`scripts/lib/bundle_fleet`), and its
`FleetArrays.ramp10` — the 10-minute deliverable ramp the reserve columns draw on — censused per
plant group. *(The DA-virtual layer was forced off for the census only: those units are virtual
demand/supply bids, carry no `plant_group` and no `ramp10`, so they cannot enter a thermal
reserve-ramp census. Nothing else was changed.)*

| plant group | units | pmax GW | ramp10 GW (nameplate) | **ramp10 GW (availability-weighted)** |
|---|---:|---:|---:|---:|
| CC_REGULAR | 583 | 60.54 | 21.67 | **15.76** |
| CT_PEAKER | 860 | 26.35 | 18.30 | **14.75** |
| COAL | 553 | 49.37 | 7.17 | 3.36 |
| *(ungrouped)* | 1,291 | 56.93 | 3.39 | 2.49 |
| ST_GAS | 69 | 11.53 | 2.30 | 1.23 |
| CC_CHP / CT_CHP / ST_CHP | 217 | 2.04 | 0.79 | 0.65 |
| hydro | 75 | 3.31 | 0.00 | 0.00 |
| **TOTAL** | | | **53.61** | **38.24** |

| | GW |
|---|---:|
| fleet 10-min ramp, availability-weighted | **38.24** |
| measured **SYNC** requirement (RTO), annual mean | **1.71** |
| measured Primary requirement, annual mean | 2.66 |
| **ratio, fleet ramp ÷ SYNC requirement** | **22.3×** |

**What this says, and what it does not.** It corroborates and sharpens
`FINDING-pjm-eas-screen-2026-09-07`'s ~19× supply margin (measured there against the *Primary*
requirement): against the *Synchronized* requirement the margin is **wider still, 22.3×**, because
the SYNC requirement is the smaller of the two. The arm's own claim is that the margin should
collapse once the SYNC column is restricted to **ONLINE** capacity sharing a joint P+R headroom row
— and the census says where that has to come from: **CT_PEAKER's 14.75 GW is the second-largest
block and is mostly OFFLINE in the model** (17.0 TWh/yr ≈ 1.94 GW mean against 26.35 GW installed),
so online scoping moves it to the NON-SYNC column and leaves **CC_REGULAR's 15.76 GW** as the
dominant SYNC-eligible source — against a 1.71 GW requirement.

**This is a PRIOR, not a gate.** It decides nothing, it is not one of S1-S5, and the screen is what
adjudicates. It is recorded because it explains the outcome in *either* direction: a KILL at S2 is
this margin surviving online scoping, and a PASS at S2 would mean online scoping collapsed a 22×
margin — which would be the genuinely surprising and interesting result.

**Container cost fact, reported because it is not free.** A PJM solve container cannot replay this
keeper without re-fetching `data/raw/pjm-da-virtuals/` — the payload is **deliberately untracked**
(PJM DataMiner2 carries a non-member redistribution restriction; `docs/data-licensing.md` §4), only
its `README.md` is committed, and `virtual_bids.py` raises rather than silently no-op. That is a
licensing decision, not a defect, but it is a mandatory re-fetch step on every fresh PJM solve
container and it is what blocked this census until the layer was switched off.

## 8. THE THREE OPEN ITEMS I WAS ASKED TO REPORT EITHER WAY

### 8.1 The pending bench move on PJM 2021/2022 C1 — EXPECTED, NOT THE ARM, corroborated here

`FINDING-pjm-h2-holdout-basis-2026-09-12.md` §3 measured that the merged `gov-hydro-seam-1`
PS→`OTHER` repair shrinks the `gas_foldin_deflation` fold-in, which raises the reconcile target,
which pushes **PJM 2021 and 2022 — and no other ISO-year anywhere — out of the 0.97 deadband**, so
`reconcile_vintage_classes` NEWLY FIRES at PJM's next registration (×1.03343 / ×1.03281):
CC_REGULAR **+26.31 → +16.98** and **+22.56 → +12.81** TWh, COAL_BIT 2021 **+1.33 → −3.71** (sign
flip), **2020 UNMOVED**, **zero determination flips** over all 8 registered PJM runs.

**Independent corroboration this session, at zero cost.** `check_bench_freshness` reads
**34 parts checked, 0 STALE** — so the committed PJM parts still reproduce under the builder — **but
every PJM part carries an engine-drift warning naming exactly the path in question**: *"5 engine
commit(s) under `src/market_sim/data/`, `src/market_sim/config/` have landed since it was committed
(2026-09-12T02:17:41Z). Those can move the **plant->class map**, the CHP shares or the **EIA-923
reconciliation**."* The gate's own warning is the mechanism pjm-h2 measured. **This is expected, it
is NOT the arm, and it must not be root-caused in the model.** Blast radius: exactly two ISO-years,
both PJM. Nothing in this session's adjudication is scored on a 2021 number.

### 8.2 ESCALATED, owner's call — is PS-net-inclusive `OTHER` the right `gas_foldin_deflation` operand?

Not settled in-lane, exactly as pjm-h2 left it. EIA-930's "Other Fuel Sources" carries no pumped
storage (PJM folds PS into `NG: WAT`), so subtracting a *negative* PS net from the 923 side compares
two different populations. Both readings are defensible ((a) HEAD is right and the reconcile was
being suppressed by a `classify_plant` defect; (b) the fold-in wants *generation by other fuels* and
should exclude PS). `gas_foldin_deflation` and `classify_plant` are **shared ISO-agnostic code** and
a PJM lane does not make that call (rule 25 `[R-ISO-SCOPE]`; the pjm-h1 precedent). Worth
**9.3–9.8 TWh** of PJM's held-out C1 residual and **zero determinations anywhere**.

### 8.3 The corrupt EIA-930 PJM 2021 `net_gen` — CONFIRMED, and NARROWED to three cells with a named cause

pjm-h2 verified the effect is inert (the scorer never reads `net_gen`; the benchmark builder does,
but both consumers are blocked by their `est > annual` guard) while the *kind* is a latent trap. I
reproduce the headline **exactly — 4,939.01 TWh** — and then localize it, which pjm-h2 did not:

| | |
|---|---|
| file | `data/raw/eia-930/EIA930_BALANCE_2021_Jul_Dec.parquet` (Jan–Jun is clean at 404.83 TWh) |
| PJM rows | 4,343 + 4,417 = **8,760 — the hour count is correct, so this is value corruption, not duplication** |
| **corrupt cells** | **exactly 3**, at local hour-ending `10/18/2021 23:00`, `10/19/2021 00:00`, `10/19/2021 01:00` |
| values MW | 1.52733 × 10⁹ · **2.14748 × 10⁹** · 4.30497 × 10⁸ (median PJM hour: 93,752 MW) |
| **named cause** | **2,147,480,000 ≈ 2³¹ = 2,147,483,648** — a signed 32-bit integer overflow / sentinel, not a plausible reading |
| year total with the 3 cells dropped | 404.83 + 428.87 = **833.70 TWh**, i.e. the true ~830 |

So the repair is **three cells in one committed extract**, with a diagnosable cause — not a
re-fetch of the year. Still a **shared committed-extract repair, not this lane's** to make, but it
is now specified rather than merely flagged.

---

## 9. ATTEMPT 2 — THE ARM INSTALLED, AND THEN P0 WAS OOM-KILLED

**Shard** `session_01EzNPfc9AUhb1Lv1ptTDF2J`, branch `claude/pjm-h3-syncarm-2022`, recovery SHA
**`ad589bd32c0af82b9b91d7456024a326d64c3262`** (rule 33(d): the full 40-char sha, never a branch
name). Its parent commit is `ed6bb0996d2685884d1f05eb105c3bef4dea138c` — **the exact pin; it never
pulled, rebased or synced**. It changed **exactly one file**, its own FINDING doc: no `src/`, no
`scripts/`, no `frontend/`. Its unique record was rescued onto this branch as
`docs/handoffs/FINDING-pjm-h3-syncarm-2022-blocked-2026-09-13.md` (rule 33(f)(1)) **before** the
shard was archived (rule 33(a)).

**Rule 34(d) retrievability: `git ls-tree -r ad589bd3 -- results/calibration/pjmh3_syncarm_2022`
returns ZERO files.** There is no bundle. The bundle dir on its container held only an empty
`dispatch/` directory. **Nothing was pushed, and that is correct** — rule 27 `[R-PUSH]` forbids
pushing a half-written bundle, so rule 34's push duty had no object.

### 9.1 The four hard stops all PASSED, and THE ARM ARMED

Quoted verbatim from the shard's solve log:

```
INFO: PJM PER-GEN reserve co-opt ON: 78 R columns / 2682 member units (eligible, ramp10>0;
deliverable ramp mean 38.2 GW), 4 balance families (pjm_primary, pjm_primary_mad, pjm_sync,
pjm_sync_mad), req means [2663, 2662, 1902, 1901] MW — SYNC product split ON
(pjm_reserve_pergen_sync: online-scoped sync caps recomputed at the P0->P1 seam)
```

**Four balance families against the control's two; `pjm_sync` and `pjm_sync_mad` both present; 78 R
columns. The mechanism installed exactly as designed.** Two independent cross-checks of my own
phase-0 work land on it:

* the solve's **`deliverable ramp mean 38.2 GW`** reproduces §7's parent-side zero-LP census
  (**38.24 GW**) — two different code paths, same number;
* the SYNC family requirement means **1,902 / 1,901 MW** are §2(b)'s measured `sr_req`
  (1,712.2 / 1,711.6 MW) **plus the published ORDC offset** (`sr_req + sr_offset`, ≈ 190 MW),
  which is the construction `reserves/spec.py:2689` specifies.

### 9.2 Where it died, and why

| | |
|---|---|
| phase | **P0** — no P0 completion marker, no P1 marker, no `memory peak:` line ever printed |
| exit | **137** (SIGKILL), `oom-kill:constraint=CONSTRAINT_MEMCG` |
| anon-RSS at kill | **13,927,636 kB = 13.28 GiB** |
| cgroup ceiling | **13.34 GiB** — pinned exactly at it |
| `memory.failcnt` | **1,562,256** |
| swap in use at kill | **3.4 MB** of a 4.0 GiB swapfile — i.e. essentially none |
| armed-run wall clock | 411 s (6 min 51 s) before the kill |

**The container was DEGRADED, and that is the diagnosis — not that the arm is infeasible.** The
preflight said so itself, in advance:

```
WARNING: container preflight: swap: /swapfile-marketsim is already active (4.0 GiB) but
  ceiling+swap is still 6.7 GiB short of the 24 GiB target; leaving it as it is
WARNING: container preflight: ceiling+swap 17.3 GiB is below the 24 GiB target; a per-plant
  ISO-year LP (MISO, PJM) may be OOM-killed here
```

`scripts/lib/solve_container.py` targets **24 GiB** of ceiling + swap (`DEFAULT_TARGET_GIB = 24`)
but **keeps an already-active `/swapfile-marketsim` and never re-creates it** (`_swapfile_active`).
That shard inherited a stale 4 GiB swapfile from an earlier tenant, so the preflight could not
provision the ~10.7 GiB it wanted, warned, and was proved right.

**Measured in THIS parent container, which is the same environment**, and which is why one retry is
warranted rather than a conclusion:

| | |
|---|---|
| cgroup | **v1** (`/sys/fs/cgroup/memory` present) |
| `memory.limit_in_bytes` | 14,327,676,928 B = **13.34 GiB** |
| `memory.memsw.limit_in_bytes` | **unlimited** |
| `vm.swappiness` | **60** |
| active swap | **NONE** |

With `memsw` unlimited and swappiness 60, **swap genuinely can extend the effective ceiling here** —
the shard's own conclusion that "adding swap under a v1 limit does not substitute" is too strong as
a general statement, and is corrected: what actually happened is that *almost no swap was
provisioned*, because a stale swapfile blocked the preflight. A container that starts with no swap
lets the preflight reach its own target.

**One further correction to the shard's report, because it changes the reading.** It infers "the
control itself would very likely not fit either" from the control peaking at 13.94 GB against a
13.34 GiB ceiling. Those are different units: **13.94 GB = 12.98 GiB**, which is *below* the
13.34 GiB ceiling. The control fits with ≈ 0.36 GiB of headroom; the SYNC split's extra structure
(2 → 4 balance families, 78 R columns) consumes it. The arm needs *modestly* more than the ceiling,
not a fundamentally different class of machine.

### 9.3 What attempt 2 also established, and what it corrects in my own record

Three environment blockers must be cleared before a PJM LP is reached in a fresh container, each
fatal because the mechanism refuses to silently no-op: `transfer-interface-limits` (no clean
partition), `ramp-capability` (no clean partition for PJM), and `pjm_da_virtual_bids`
(`data/raw/pjm-da-virtuals/` is a README-only, licence-restricted corpus; **`--years 2022` must be
requested explicitly — the fetcher defaults to 2023-2025**). I hit the identical three in the parent.

**This corrects my own hypothesis about attempt 1.** I attributed that failure to a foreground
solve exceeding the 10-minute Bash ceiling. Attempt 2's evidence says the first shard was almost
certainly killed by blocker 1 or 2 — it died ~10 min in, which is where blocker 1 lands, and it
never reached an LP at all. The background-job requirement was still the right instruction, but it
was not the fix for attempt 1.

### 9.4 STATUS AFTER ATTEMPT 2 — THE SCREEN HAS NOT RUN

**S1 is satisfied on identity** (hard stop 3 verified the control signature; the arm installed as
the declared single-field delta with exactly the declared structure). **S2, S3, S4 and S5 are
UNMEASURED — not KILL, not PASS.** No `reserve_family_2022.parquet` and no `system_2022.parquet`
were ever written, so there is no evidence about the mechanism's behaviour, and **no verdict about
the mechanism may be drawn from an OOM.**

**Attempt 3 launched** — `session_01HBTXoSZmnAD9KZoNWAhi6B`, branch
`claude/pjm-h3-syncarm2-2022`, same pin `ed6bb099…`, on a **fresh container** so the preflight can
provision its full swap target, with the three blockers pre-cleared in the prompt (~17 min saved)
and a stated 60-minute budget (rule 32(b)). It is instructed to report `swapon --show` *before* the
solve, and that **a second OOM is a reportable result to stop on, never a thing to engineer
around**.
