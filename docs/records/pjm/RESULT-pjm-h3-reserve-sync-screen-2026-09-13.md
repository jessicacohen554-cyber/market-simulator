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

## 10. ATTEMPT 3 — SAME OOM, AND IT REFUTES MY OWN ATTEMPT-2 DIAGNOSIS

**Shard** `session_01HBTXoSZmnAD9KZoNWAhi6B`, branch `claude/pjm-h3-syncarm2-2022`, recovery SHA
**`96da85894876c67ee0a44dc1fc14521afaef381f`**, parent = the pin. Again exactly one file changed
(its own FINDING, rescued here as
`docs/handoffs/FINDING-pjm-h3-syncarm2-2022-blocked-2026-09-13.md`), no `src/`, no `scripts/`.
**Rule 34(d): `git ls-tree` returns ZERO files** — no bundle, nothing pushed but the doc, which is
correct.

**The arm armed again, byte-for-byte the same signature** (4 balance families, 78 R columns, req
means `[2663, 2662, 1902, 1901]` MW, `SYNC product split ON`). The mechanism reaches the LP
reliably; it is not what is blocked.

### 10.1 MY ATTEMPT-2 DIAGNOSIS WAS WRONG, and the correction is the useful part

I concluded that a **stale 4 GiB swapfile** blocked the preflight, and that a fresh container would
therefore let it reach its 24 GiB target. **Attempt 3 falsifies that directly.** Its container
started with **zero swap** (`swapon --show` empty), so the preflight took its *create* path — and
still produced **exactly 4 GiB**, landing on the identical 17.3 GiB and emitting the identical
warning.

**The 4 GiB is DISK-BOUND, not stale.** `ensure_solve_container` sizes the swapfile as

```
add_gib = int(min(deficit_gib, max(0.0, free_gib − DISK_RESERVE_GIB)))
```

with a 24 GiB target, so on a 13.34 GiB ceiling the deficit is ~10.7 GiB — against a
PJM-hydrated container's **6.4 GiB free**, less a ~2 GiB output reserve. It writes what fits (4 GiB),
warns, and proceeds. **A fresh container does not fix this; the disk allowance does.**

### 10.2 The load-bearing number, and why it raises the bar

| quantity | attempt 2 | attempt 3 |
|---|---:|---:|
| anon-RSS at kill | 13.28 GiB | **13.28 GiB** (identical) |
| `memory.limit_in_bytes` | 13.34 GiB | 13.34 GiB |
| `memory.max_usage_in_bytes` | at the ceiling | **at the ceiling** |
| **`memory.memsw.max_usage_in_bytes`** | not reported | **17.33 GiB = 13.34 + 4.00 exactly** |
| `memory.failcnt` | 1,562,256 | 1,144,459 |
| swap in use | 3.4 MB | **fully consumed** |
| phase | P0 | P0 |

**`memsw.max_usage` = ceiling + swap, exactly.** The solve consumed **100 % of RAM and 100 % of
swap** and was still killed — so the requirement is **strictly greater than 17.3 GiB**, and this is
not a marginal miss a slightly bigger swapfile clears. Attempt 3's own reading is right and I adopt
it: the 24 GiB target is the real requirement, not a safety margin.

This also **retires attempt 2's** conclusion that "adding swap under a v1 limit does not
substitute" — attempt 3 shows swap *was* fully used once it existed. Both shards' individual
inferences were wrong in opposite directions; the composite measurement is what stands.

### 10.3 Attempt 4 — the one lever left, and it is the parent's to pull

Attempt 3 correctly refused to choose between its three options and routed the decision up. Of them:

* **A larger container is not available** — `list_environments` offers exactly two, both
  `anthropic_cloud`, and this parent measures the same 13.34 GiB ceiling.
* **Subdividing** is permitted for never-registered diagnostic work (rule 32(b)), but P0 is a single
  system LP and there is no subdivision of it that preserves what the screen measures.
* **Freeing disk is real, measured, and mine to do** — and it is not a rule 31 `[R-RETAIN]` question
  at all, because nothing unique is destroyed.

Measured in this parent container:

| action | `data/raw` | free disk |
|---|---:|---:|
| before | 6.4 GiB | 17 GiB |
| **`hydrate_data.py --profile pjm --force`** | **2.3 GiB** | **21 GiB** |

**+4.1 GiB**, using the repo's own documented tooling (`docs/fast-clone.md`,
`configs/data-profiles.yaml`) — it drops working-tree copies of blobs that stay in `.git`, and is
reversible with `--profile all --force`. Removing the other ISOs' *committed* bundle checkouts adds
**~0.6 GiB** more, guarded by a `git ls-tree` test so only paths committed at the pin are removed
and `pjm_d4_4_TP` is explicitly excluded.

On the shard's 6.4 GiB that is ~**11 GiB free** → `add_gib = int(min(10.66, 11 − 2)) = 9` →
**ceiling + swap ≈ 22.3 GiB**, against a requirement measured to exceed 17.33 GiB.

**Attempt 4 launched** — `session_012kj4shTS4xNWaedcWiSUqa`, branch
`claude/pjm-h3-syncarm3-2022`, same pin, same solve, **nothing about the mechanism, config, runner
or solve settings changed**. It carries an **early gate**: if the preflight still provisions under
6 GiB of swap, it kills the job and stops rather than spend ten minutes proving a known-doomed
configuration a third time. **It is told there will be no fifth attempt.**

**Stated honestly: this may still fail.** 22.3 GiB is ~29 % above the floor we have measured, but
the true requirement is unknown — all we know is that it exceeds 17.33 GiB. If attempt 4 OOMs, the
screen is environment-blocked on a triply-measured, fully reproducible constraint, and the ask
becomes the owner's: a solve container with a memory ceiling above ~13.34 GiB, or a disk allowance
that lets the existing preflight reach its own 24 GiB target.

---

# 11. THE VERDICT — THE SCREEN RAN, AND IT KILLS THE ARM AT S2

**Attempt 4 completed.** Shard `session_012kj4shTS4xNWaedcWiSUqa`, branch
`claude/pjm-h3-syncarm3-2022`, recovery SHA **`786affd47cf95334aa1fc7579135c230492f1296`**
(rule 33(d)). **Rule 34(d): `git ls-tree` returns 17 files including
`dispatch/2022_P1.parquet`** — the bundle is pushed and a promotion would cost zero re-solves
(rule 34 `[R-SHARD-PROMOTABLE]` (a)). The disk fix worked exactly as predicted: the shard freed
4 GiB, the preflight reached ~23 GiB of ceiling+swap, and the solve completed.

## 11.1 THE GATES, AS PRECOMMIT §5 FIXES THEM — NOT RE-READ, NOT SOFTENED

| # | gate | bar | **measured** | verdict |
|---|---|---|---|:--|
| **S1** | arm identity | delta = `pjm_reserve_pergen_sync` + declared prereqs ONLY | exactly one config delta: `pjm_reserve_pergen_sync` false→true (both prereqs already True; all four rule-19 exclusions False; `gas_prices.2022` identical at 6.45) | **PASS** |
| **S2** | the mechanism is LIVE | SYNC dual ≠ 0 in **≥ 20 %** of 8,760 h | **1.2215 % — 107 hours** (`pjm_sync` 0, `pjm_sync_mad` 107). PJM published 2022: **61.3 %** | **KILL** |
| **S3** | shape, not level | mean h16-18 **≥ 2×** mean h01-04 | **$0.13327 vs $0.00000 → +∞** | **PASS** |
| **S4** | confinement | r ≥ **+0.30** AND zero-hour mean abs delta < **25 %** of positive-hour | **r = +0.7380**; **0.17 %** | **PASS** |
| **S5** | no collateral damage | no PROTECTED criterion (C2/C4/C6/C8) PASS→FAIL | C2 PASS · C4 PASS · C8 PASS · C6 `UNATTESTED` (probe artifact, §2(f)) | **PASS** |

> ## **S2 IS A STOP GATE AND IT FIRED. THE ARM IS KILLED. THE 2020 AND 2021 YEARS ARE NOT SPENT**
> (rule 29 `[R-SCREEN]` clause 2 / PRECOMMIT §7).

## 11.2 THE CHARACTER OF THE KILL — STRUCTURALLY CORRECT, QUANTITATIVELY INERT

This is not a mechanism that misbehaves. It is a mechanism that behaves **perfectly** and **does
almost nothing**, and both halves are measured.

**What it gets right.** S3 and S4 are as clean as this lane has ever measured. The credit is
**strictly peak-confined — exactly zero in every overnight hour** — which is precisely what
pjm-138 §7 lead 1 said a successor must be. The energy-price response is confined to the hours the
reserve prices: `r = +0.738`, and movement in SYNC-zero hours is **0.17 %** of movement in
SYNC-positive hours. It also **moves the reserve rent to the correct product**: the control priced
2 hours in `pjm_primary_mad` — a *synchronized* requirement being met by *offline* capacity, the
pjm-87 misrepresentation this arm exists to fix — and the arm prices **0 there and 107 in
`pjm_sync_mad`**, at mean **$6.23**, median **$1.85**, max **$65.27**, with **zero shortfall
hours** (binding-at-requirement rent, never an ORDC shortfall).

**What it fails to do.** It is inert on every quantity the model is scored on:

| | control | arm | delta |
|---|---:|---:|---:|
| C1 CC_REGULAR | +22.56 TWh | **+22.55 TWh** | −0.01 |
| C3a mean LMP | −10.7 % | **−10.7 %** | 0.0 pp |
| C3b NRMSE | 0.246 | **0.246** | 0.000 |
| C3c model tail hours > $200 | 3 h | **3 h** | 0 |
| annual load-weighted price | 64.074 | **64.092** $/MWh | +0.017 |
| largest class movement (CC_REGULAR) | 319.6918 | **319.6819** TWh | **−0.0100** |

Every one of these is a **target** and gates nothing in either direction (rule 1 `[R-STRUCT]`), and
they are reported at full magnitude exactly as the PRECOMMIT requires.

**Two honest notes rather than quiet omissions.** (i) The arm's C3c reads `FAIL` in my re-score
where the control's reads `CAVEAT`. That is **not a mechanism effect**: the C3c standing rule's
guard (b) requires governance to PASS, and a `replay_keeper` probe writes no attestation, so C6
reads `UNATTESTED` and the reclassification is correctly blocked. The magnitude is **unchanged at
3 h vs 92 h**. (ii) The 107 binding hours cluster at **hod 11-16** (Jun 43 / Jul 21 / Aug 28 /
Sep 15), i.e. *midday-to-afternoon*, a little earlier than PJM's own h16-18 peak. S3 passes because
the nights are exactly zero, but the intraday placement is not a perfect match and is said so here.

## 11.3 WHY IT IS INERT — THE PHASE-0 CENSUS PREDICTED THIS, AND THE SOLVE CONFIRMED IT

§7's zero-LP census put the PJM fleet 10-minute ramp at **38.24 GW** availability-weighted against
a measured SYNC requirement of **1.71 GW** — a **22.3×** margin, *wider* than the ~19×
`FINDING-pjm-eas-screen-2026-09-07` measured on the Primary requirement, because the SYNC
requirement is the smaller of the two. **The solve's own log independently reports
`deliverable ramp mean 38.2 GW`.** Online-only scoping does what it claims — CT_PEAKER's 14.75 GW
of ramp is mostly offline and moves to the NON-SYNC column — but that leaves **CC_REGULAR's
15.76 GW** as the SYNC source, still ~9× the requirement. The published ORDC knee therefore fires
only in 107 summer midday hours.

**The consequence reaches past this cell.** The **tightest defensible reserve-product definition
the design space offers** — online-only, 10-minute deliverable ramp, sharing the pool's joint P+R
headroom row, on the measured requirement and the published curve — **still cannot make PJM
reserve scarcity bind at this fleet size.** That extends `FINDING-pjm-eas-screen-2026-09-07`'s
retirement of the PJM-levers-routed-through-reserve-scarcity family **from the forecast lane to the
backcast lane**. The binding object is the **supply margin**, not the product definition.

## 11.4 THE PJM KEEPER IS UNCHANGED

| | determination | grade | caveats | basis |
|---|---|---|---|---|
| **BEFORE** | **CALIBRATED** | 8/8 | 0 | all criteria pass, governance attested |
| **AFTER** | **CALIBRATED** | 8/8 | 0 | all criteria pass, governance attested |

Re-scored on `origin/main` before this session and again after it, across a 47-commit refresh of
`main` in between. Nothing armed: `pjm_reserve_pergen_sync` stays default-off. Rule 30(c) holds —
no held-out year touches PJM's determination.

## 11.5 THE PROMOTION QUESTION — PUT EXPLICITLY (rule 31 `[R-RETAIN]`)

**MY RECOMMENDATION: DO NOT PROMOTE.** Stated with the case against my own recommendation, because
the owner routinely promotes what a session declines and that is what a promotion decision *is*.

**The case FOR promoting it, stated fairly and not strawmanned.** It is a real PJM market structure
(Manual 11 §4.2/§4.3.3) the model does not otherwise have. It carries **zero parameters fitted to
the price residual** — a measured requirement, the published ORDC curve, and physics ramp and
commitment gates. It **corrects a named misrepresentation**: the control lets a *synchronized*
requirement be satisfied by *offline* capacity (pjm-87), and the arm stops that, moving the rent
into the product that actually bears it. **Nothing regresses** — S5's protected set is clean and
every target is unchanged to the reported precision. Rule 1 `[R-STRUCT]`'s "a real market behaviour
stays in even if it makes the fit worse" applies *a fortiori* when it does not make the fit worse
at all.

**The case AGAINST, which is why I do not recommend it.**

1. **My own pre-registered gate killed it.** S2 was fixed in the PRECOMMIT before the solve
   precisely so it could not be re-read once a number was on the table. 1.22 % against a 20 % bar
   is not a near miss — it is a factor of **16**, and against PJM's own 61.3 % a factor of **50**.
   A gate I might think mis-specified is reported as such and **the verdict still stands**.
2. **It is inert, so there is nothing to buy.** The owner's standard — *"if structural integrity
   improves but gates regress that may still be a keeper"* — describes accepting a **fit cost** to
   gain **real structure**. Here there is no fit cost *and* no fit gain: the largest class moves
   **0.010 TWh out of 319.69** and the annual price moves **$0.017/MWh**. The trade the standard
   contemplates is not on offer.
3. **It carries a real, measured operational cost.** It doubles the R-column count and
   **OOM-killed P0 on three successive standard containers**; it completed only after 4.1 GiB of
   disk was freed so the preflight could reach ~23 GiB of ceiling+swap. Promoting it puts that cost
   on **every future PJM solve**, for a mechanism that is provably active in 1.2 % of hours.
4. **Promotion is not free to obtain.** Rule 16 `[R-ALLYEARS]` requires the full **2020-2022** span
   in one bundle; the screen year would be re-solved inside it. That is **~3 PJM years at ~25-40 min
   each on a disk-freed container (~90-120 min)**, plus registration — and rule 29 `[R-SCREEN]`
   clause 2 spends the span only if the screen **clears** its gate, which it did not.

**What I would need to change my recommendation:** an owner ruling that the structural correction
(reserve rent booked to the synchronized product rather than to a requirement offline capacity
should never have satisfied) is worth carrying at its memory cost *despite* being inert. That is a
legitimate call and it is the owner's, not mine.

**WHERE THE BUNDLE IS, AND WHAT A PROMOTION WOULD COST FROM HERE** (rule 34 `[R-SHARD-PROMOTABLE]`
(e)). The 2022 screen bundle is **retrievable with zero re-solves** — 17 files including
`dispatch/2022_P1.parquet`, pushed to the shard branch and recoverable by immutable sha:

```
git checkout 786affd47cf95334aa1fc7579135c230492f1296 -- results/calibration/pjmh3_syncarm_2022
```

It is also on this container's local disk (196 MB), gitignored so it cannot reach `main`
(rule 29(c) discharged by `.gitignore`, **not** by `rm` — rule 31, the ercot-255 incident).
**This container is ephemeral and the local copy does not survive the session; the shard-branch
copy does.** A promotion from here costs the 2020 and 2021 legs only — the 2022 leg exists.

## 12. SHARDS LAUNCHED, AND THEIR DISPOSAL (rule 33 `[R-SHARD-ARCHIVE]`)

| attempt | session | branch | recovery SHA | outcome | archived |
|---|---|---|---|---|:--:|
| 1 (inherited) | `session_01SKY3Qo2snPS9N6UbrdWbaN` | `claude/pjm-h3-syncarm-2022` | — (never pushed) | FAILED, zero bytes | already self-archived |
| 2 | `session_01EzNPfc9AUhb1Lv1ptTDF2J` | `claude/pjm-h3-syncarm-2022` | `ad589bd32c0af82b9b91d7456024a326d64c3262` | STOP: P0 OOM | **yes** |
| 3 | `session_01HBTXoSZmnAD9KZoNWAhi6B` | `claude/pjm-h3-syncarm2-2022` | `96da85894876c67ee0a44dc1fc14521afaef381f` | STOP: P0 OOM, disk-bound | **yes** |
| 4 | `session_012kj4shTS4xNWaedcWiSUqa` | `claude/pjm-h3-syncarm3-2022` | **`786affd47cf95334aa1fc7579135c230492f1296`** | **SOLVED, bundle pushed** | **yes** |

Each was archived only **after** the parent had fetched its branch, checked out its content and
verified it (rule 33(a)), and each unique FINDING doc was rescued onto this branch first
(rule 33(f)(1)). **No shard was left running.**

**Branch deletion (rule 33(f)) is REFUSED in this environment and I did not report otherwise.**
`git push origin --delete` returns **HTTP 403** — visible only on HTTP/1.1; on HTTP/2 it presents
as `send-pack: unexpected disconnect` followed by a misleading `Everything up-to-date`. This is
exactly what rule 33(f)(5) documents: the session credential can create and update refs but not
delete them. The branches therefore **stay**, which is the better outcome anyway — every recovery
sha above still resolves (rule 33(f)(4)).

## 13. RULES APPLIED

Rule 1 `[R-STRUCT]` (no lever selected on a residual; the targets gate nothing) · rule 14
`[R-ACCURATE]` (measured requirement + published curve) · rule 16 `[R-ALLYEARS]` (the span is NOT
spent — the screen killed the arm) · rule 19 `[R-ONE-MECH]` (all four exclusive fields verified
False) · rule 28 `[R-MECH-MATRIX]` (b) (the `reserve_pergen` cell stamped **in this session**, a
rejection with full citation quality) · rule 29 `[R-SCREEN]` (zero-LP phase 0 first; one screen
year named on footprint in the PRECOMMIT; G-CTRL form 4, **no control solve spent**; clause (c)
discharged by `.gitignore`) · rule 30(c) (no held-out year touches PJM's determination) · rule 31
`[R-RETAIN]` (**nothing deleted**; the promotion question put explicitly above) · rule 32
`[R-SHARD]` (a) (**the parent ran no LP** — every solve was a shard; phase 0, scoring and
composition stayed here) · rule 33 `[R-SHARD-ARCHIVE]` (all four shards swept; recovery by
immutable sha) · rule 34 `[R-SHARD-PROMOTABLE]` (a)/(d)/(e) (the bundle is pushed and verified
retrievable, and its retrievability is stated).

## 14. CORRECTION — §10.2's "the requirement strictly exceeds 17.3 GiB" IS FALSIFIED BY ATTEMPT 4

I wrote, from attempt 3's kill, that because `memsw.max_usage` equalled ceiling + swap **exactly**
(17.33 GiB), the solve's requirement must **strictly exceed 17.3 GiB**. Attempt 4 measures
otherwise and the correction matters for every future PJM shard prompt:

| | attempt 3 | **attempt 4** |
|---|---|---|
| swap available | 4 GiB | **8 GiB** |
| swap actually used at peak | **4.0 GiB (all of it)** | **2.4 GiB** |
| effective peak | 17.33 GiB, then **OOM** | **≈ 15.7 GiB**, **completed** |
| wall clock | killed at 10 min 09 s | **17.6 min — faster than the control's 24 min baseline** |

So the true working set is **≈ 15.7 GiB**, not > 17.3 GiB. Attempt 3's 17.33 GiB was a
**thrashing artifact**: with too little swap the cgroup sat in continuous reclaim
(`failcnt` 1,144,459) and RSS inflated until the kernel killed it. Given adequate headroom the
solve settled well below the figure its own failure had implied, and ran *faster* than the
unswapped control.

**The operational lesson, corrected:** what a PJM per-plant year needs here is not a bigger memory
ceiling — it is **enough free disk for the preflight to build a swapfile with headroom**, because
`ensure_solve_container` sizes it `int(min(deficit, free − 2 GiB))`. Freeing 4.1 GiB with
`hydrate_data.py --profile pjm --force` was the whole fix. A shard prompt for a per-plant ISO should
do that **before** the solve rather than discover it through an OOM, and the three environment
blockers (§10.3) should be pre-cleared in the same step.

*(Also reported, not absorbed: the shard's `legitimacy_diagnostics.py` post-step exited non-zero on
a **D-10 wind/solar advisory**. It is not C8 — the scorer read the arm's own committed
`legitimacy_diagnostics.json` and **C8 PASSES** — and the D-10 advisory is present on this ISO
independent of the arm.)*
