# FINDING — pjm-129: the PJM keeper does NOT hold on the guard-corrected CAMPD envelope — **RE-TUNE REQUIRED**, three gates; and the RAM block that stopped two prior attempts was never a bigger box

**Lane:** the last PJM cell of `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`
§5/§8. Charter, pre-registered and committed **before any solve result was read**:
`docs/handoffs/pjm-129-keeper-reaudit-charter-2026-07.md`.

**Registered arm:** `2026-07-26-pjm-129-meritguard-a1` (PJM 2023/2024/2025, ONE
bundle, rule 16; rule 15 — registered whatever the verdict). **Nothing was
tuned.**

---

## §0 — verdict

**DETERMINATION `CALIBRATED` (10/10, PJM's first all-pass) → `NOT-YET` (7/10).
RE-TUNE REQUIRED**, on three newly-failing gates:

| gate | keeper | A1 | band | |
|---|---|---|---|---|
| **C3a mean LMP 2025** | −9.3 % (model $41.53 / actual $45.80) | **−10.6 %** ($40.93) | ±10 % | **FAIL** |
| **C3c tail 2024** | 9 h vs 18 h actual, 0.50× | **7 h, 0.39×** | ≥0.5× | **FAIL** |
| **C3c tail 2025** | 39 h vs 59 h actual, 0.66× | **28 h, 0.47×** | ≥0.5× | **FAIL** |
| **C1 2023 CC_REGULAR** | −7.87 TWh, −0.4 pp | **−8.10 TWh**, −0.5 pp | `min(2 % load, 8 TWh)` **and** 3 pp | **FAIL** (volume, by 0.10 TWh) |

C2, C3a-2023/24, C3b, C4, C5a, C6, C7, C8 all still PASS. **C3a-2023 and C3b-2023
and C5a-2023/24 improve.** Free-class C1 16/16 → 15/16 (free 12/12 → 11/12).

**The keeper designation was NOT changed.** miso-88's precedent applies:
promoting or demoting on a NOT-YET re-audit arm is an owner call, not a
session's. Nothing was tuned and nothing is licensed to be.

Per **rule 11 [R-ACCURATE]** this is a *discovered bug*, not a reason to revert
the guard: the keeper's offer curves were silently compensating for an inflated
outage envelope — the NEISO / ERCOT-79 / nyiso-63 / miso-93 condition. The
corrected extract stays in (rule 1 [R-STRUCT]).

**The verdict is an isolation, not an attribution (§5).** A same-HEAD probe with
the extract reverted to the keeper's blob reproduces the keeper's committed 2025
hourly sidecars with `max|diff| = 0` on every column, so the post-keeper code
surface is measured **PJM-inert** and the guard/extract owns **100 %** of the
−$0.518 (−1.3 pp) move.

**Pre-registration honesty.** The charter named **C3a-2025** as the single
exposure and got the gate, year, direction **and magnitude** right (predicted
"a MISO-sized −1.4 pp move lands it at ≈−10.7 %, outside the band"; it landed at
−10.6 %). It **missed C3c** entirely — it did not consider that adding supply
removes scarcity hours — and it explicitly predicted C1 would hold, which it did
at the family level (C2 PASS) but not at the CC_REGULAR *row* level, which was
already at 98 % of its volume band before the guard. Recorded as a miss rather
than narrated afterwards as foreseen.

## §1 — the RAM block: not a leak, and not a ≥24 GB requirement

Two prior sessions attempted this re-audit in this same 15 GB / 4-core container
(neiso-65 on the then-keeper `pjm119_overlay_restore`, then a re-attempt on
`pjm121_ccbelt`). Both completed 2023 running **alone** and were both SIGKILLed
at **15.9 GB** building 2024, and both concluded the replay "needs a ≥24 GB
environment". The second left a lead: *"2023 fits alone and 2024 does not, on
both attempts. That is consistent with the year loop retaining the prior year's
arrays rather than with any single year being too large — worth measuring before
assuming the LP itself is the ceiling."*

**Measured, PJM-specific, from the release-block telemetry of this session's own
solve-years** (`year %d memory after release: resident=… peak=…`, one fresh
process per solve-year):

| solve-year | `resident` after release (the floor it would hand on) | `peak` (single-year high-water) | declared accumulators |
|---|---|---|---|
| 2023 | **1.06 GB** | **14.87 GB** | 0.07 GB (campd 0.05) |
| 2024 | **1.19 GB** | **14.94 GB** | 0.13 GB (campd 0.09, flows 0.02, system 0.01) |
| 2025 | **1.26 GB** | **15.06 GB** | 0.19 GB (campd 0.14, flows 0.03, system 0.02) |

**The lead is refuted, and the arithmetic is exact.** The year loop is not
leaking: `run_calibration_full.py`'s year loop carries an explicit
`del` + `gc.collect()` + `malloc_trim(0)` release block, and it releases to a
**1.06–1.26 GB** floor that is itself fully attributed (0.07–0.19 GB of declared
cross-year accumulators plus ~0.1 GB retained payload and glibc interior
fragmentation — the attribution miso-92 established, and 35 % of which it
removed). What kills a *single-process* multi-year PJM run is

> **year N+1's single-year peak + year N's floor = 15.93–16.25 GB**
> (14.94 + 1.06 at year 2; 15.06 + 1.19 at year 3)

against the **15.9 GB** kill both attempts reported, **at year 2, which is where
both reported it**. Reproduced to within 0.03 GB by two numbers neither attempt
read. **The single-year LP peak is the ceiling; the prior year's floor is only
what tips it over.**

**Consequence: the ≥24 GB requirement was never real, and the keeper's own
attestation already said so.** `pjm121_ccbelt`'s attestation records it was
itself *"solved as the rule-12 per-year chain (2023, then 2024, then 2025; one
fresh process each, ~15 min/year, **peak ~14.8 GB**)"* — the recipe was in the
keeper's own provenance the whole time. One fresh process per solve-year removes
the floor and every PJM solve-year then fits this container with **0.6–0.8 GB**
spare. No CI job was spun up and no bigger box was requested (CLAUDE.md "never
offload work to CI" — private repo, billed minutes).

**A no-power measurement was deliberately not run.** The lead suggested
instrumenting a 1-zone/24-hour toy first. A toy of that size allocates ~0.01 GB,
so "the loop leaks" and "the loop is clean" render identically at two decimal
places — it cannot discriminate a 15 GB peak from a 1.1 GB floor, which is the
entire question. The instrument with power is the real solve-year's own release
telemetry, and it costs nothing (already in the code, one log line per year).
Reported rather than padded with a measurement that could not have answered it.

**Reproducibility.** The first stage-1 launch was discarded and re-run because it
solved from a tree carrying one untracked file (the charter itself), which
`--reuse-solved` correctly refuses as not commit-addressable. The two runs agree
to 0.01–0.03 GB (`resident` 1.05 vs 1.06, `peak` 14.84 vs 14.87), so the memory
figures are reproducible, not single-draw.

## §2 — prerequisites, and the A0-validity check

`data/clean/` is derived and disposable and did not exist in this container.
Regenerated **before** solving (both `curate_ramp_capability.py` and
`curate_capacity_deliverability.py` need `PYTHONPATH=.` or they abort into a
silently degraded solve): `transfer-interface-limits` (PJM, 3 × 87,600 rows),
`ramp-capability` (PJM, 749 rows), `capacity-deliverability` (PJM, 155 rows).
`data/raw/pjm-da-virtuals/` held only its README, so all **36 months** of
`hrl_da_incs_decs` (2023–2025, 22 MB) were re-fetched — `pjm_da_virtual_bids`
hard-fails on any missing month.

**Every solve log was audited before any number here was quoted.** The overlays
are live, not degraded: `transfer-interface-limits <year>` names all six measured
PJM interfaces plus the measured EAST cut; the DA layer builds *"64 DEC-form +
64 INC-form pseudo-units (8 rungs/side, measured hourly curves)"*; the per-gen
reserve co-opt reports *"deliverable ramp mean 38.7–38.9 GW"*, matching
pjm-124's independently reconstructed 38.9 GW — the measured ramp partition is
in. The only warnings are the known benign reconciliations the keeper itself
logged (eGRID plant 55641 heat rate, five CC pmax bounds, 14 of 1,922 generators
without an eGRID zone).

**A0 is the keeper itself** (`2026-07-25-pjm-121-cc-belt`,
`results/calibration/pjm121_ccbelt`, solved 2026-07-25 on the pre-adoption
envelope). The guard is byte-inert off, so no solve was burned re-deriving it.
**PJM does not carry the caiso-123 confounded-A0 defect**, verified before
solving:

* `data/raw/campd-unit-outages-PJM.csv` changes **exactly once** in
  `0069f8e..HEAD` (the keeper's own `git_sha` → HEAD) — at `6a8f285`, the
  guard-adoption commit — and that commit touches only the extract
  (−3,246 rows) and its new layup companion (+3,247). `campd-unit-outages-short-PJM.csv`
  and `campd-partial-outages-PJM.csv` are untouched, so the delta is exactly one
  file;
* the keeper's blob is `5283f5c6`, HEAD's is `65ff8371`, and the **on-disk file
  hashes to HEAD's blob exactly** — no derived-not-committed input.

**Same-bench control.** The keeper was **re-scored in this session on today's
`bench/`, after this arm's registration** (scorer-only, no solve) and still reads
`CALIBRATED` 10/10 with the identical set of SKIPPED 2025 rows. So the
before/after table above is measured against the same benchmark on both sides —
**the drift is not benchmark drift.**

**Side-effect observed and reported, not introduced here:
`bench/PJM/2025.json.gz` changed on registration.** Four cells moved, all CHP:
`classFull` CC_CHP 6.3383 → 6.2811 and **CT_CHP 0.5456 → −0.3726**, with the
mirrored `co2.btmClass` cells moving the opposite way. This is the documented
behind-the-meter treatment — `btm.parquet` is the *run's own* must-run-emissions
BTM allocation and the renderer subtracts it from `classFull` **on both sides**
(`run_calibration_full.py` ~L1874) — so the stored bench's CHP split belongs to
whichever run registered last. Two things follow, both checked: the subtraction
is symmetric, so no C1 CHP row is biased by it; and **the keeper re-scores
`CALIBRATED` 10/10, free 12/12, on the changed bench**, so nothing downstream
moves. The negative CT_CHP cell (A1's BTM estimate 2.10 TWh exceeds the metered
class total 1.72 TWh, so the subtraction over-subtracts) is a **pre-existing
property of that mechanism**, surfaced here rather than created here — flagged
for the PJM lane, not fixed in a re-audit that is forbidden from touching
anything.

## §3 — the guard's effect on the PJM envelope (no solve)

Measured from the two committed blobs. The guard **removes windows and adds
none**:

| | 2023 | 2024 | 2025 | 2023–25 |
|---|---|---|---|---|
| GW-days removed (layup companion) | 2,001 | 1,109 | 1,513 | **4,624** (903 windows) |
| kept envelope GW-days | 13,059 | 11,387 | 10,595 | 35,041 |
| **relief, % of envelope** | **15.3 %** | **9.7 %** | **14.3 %** | **11.7 %** |

Class mix of the removal, 2023–25: **ST_GAS 2,528 GW-days (54.7 %)**, COAL 984
(21.3 %), CC_REGULAR 841 (18.2 %), CC_CHP 191, CT_CHP 80. Exactly the signature
the charter predicted and MISO measured — gas *steam* priced out of merit for
weeks was being booked as mechanically unavailable. PJM's relief (11.7 % of
envelope) is close to MISO's (12.8 %).

## §4 — what the solve did with it

**Price falls in every year.** Load-weighted mean zonal price from the two
bundles' own committed `hourly/system_<year>.parquet` sidecars (the mechanism
read), and the scorer's C3a series (the gate, which additionally carries the
post-solve scarcity adder):

| year | sidecar LW keeper → A1 | Δ | C3a model keeper → A1 | C3a vs actual |
|---|---|---|---|---|
| 2023 | 30.719 → 30.273 | **−$0.447** (−1.45 %) | 31.19 → 30.72 | +5.6 % → **+4.0 %** (improves) |
| 2024 | 29.570 → 29.323 | **−$0.247** (−0.84 %) | 30.53 → 30.25 | −2.5 % → −3.4 % |
| 2025 | 40.070 → 39.552 | **−$0.518** (−1.29 %) | 41.53 → 40.93 | −9.3 % → **−10.6 % FAIL** |

2023's −$0.447 is within a cent of MISO's measured −$0.445/−$0.467. **2025 fails
not because its move is the largest but because it started closest to the veto**
(0.7 pp of margin) — the same structure as MISO's C3a-2024.

**Class volumes move exactly as the mechanism says they should** (2023 TWh,
keeper → A1): **ST_GAS 8.09 → 10.60 (+2.51)**, CC_CHP 8.01 → 8.65 (+0.64),
COAL_BIT 100.77 → 101.70 (+0.92), **CT_PEAKER 23.20 → 21.78 (−1.42)**,
CC_REGULAR 317.80 → 317.57 (−0.23). Returned gas-steam and coal capacity
displaces peaking. 2025 ST_GAS moves 12.72 → 16.56 TWh (+3.84). The gas family
stays in band (C2 PASS, 2025 gas +1.1 % → +1.7 %), which is why the *family*
gate holds while the CC_REGULAR *row* tips.

**C3c is the mechanically obvious consequence the charter missed.** Adding supply
removes scarcity: model hours >$200 fall 5 → 2 (2023), 9 → 7 (2024), 39 → 28
(2025) against unchanged actuals of 6 / 18 / 59. 2023 survives only because its
count is inside the small-count `|Δ| ≤ 10 h` band. This *deepens* an already-open
PJM root cause rather than creating a new one: the keeper's own note carries the
G-20b/G-22 reserve supply-side tightness class (38.1 GW deliverable 10-min ramp
against a ~3.7 GW requirement; reserve dual never crosses $300), and pjm-124/125
closed both framings of the scoping lever. Relieving the envelope adds still more
of the very supply that keeps the tail flat.

**Nothing degrades on shape or emissions.** C3b NRMSE 0.157 → 0.152 (2023),
0.122 → 0.125 (2024), 0.151 → 0.160 (2025) — all inside the ≤0.20 band. C5a CO₂
−2.0 → −1.3 % (2023), −3.1 → −2.8 % (2024), +2.6 → +3.1 % (2025). C4 hourly
dispatch correlation is flat to three decimals (r 0.92–0.95 both arms). C7 and C8
PASS; the three CT_PEAKER C8 rows stay *grounded above budget* (15.0/15.4/15.7 %,
D-4 clean, profile r 0.93–0.98).

## §5 — the isolation: is any of this the post-keeper code drift?

The charter flagged that `0069f8e..HEAD` is 28 files / +2,235 lines under
`src/market_sim/`, including **`offer_surfaces.py` +391** — the module that owns
the keeper's own `pjm_offer_midcurve_segments` mechanism, whose `CC_LIKE` scope
*is* what pjm-121 added. miso-93 proved that churn MISO-inert; that does not
transfer to PJM.

**One single-year throwaway probe closes it**, 2025 (the failing year) solved at
**this HEAD** with `data/raw/campd-unit-outages-PJM.csv` reverted to the keeper's
blob `5283f5c6` (verified by `git hash-object` before launching):

| arm | 2025 sidecar LW $/MWh | C3a | isolates |
|---|---|---|---|
| KEEPER (`0069f8e`, pre-guard extract) | **40.070** | −9.3 % | — |
| **A0′** (HEAD, pre-guard extract) | **40.070** | −9.3 % | code drift alone |
| **A1** (HEAD, guard-corrected extract) | **39.552** | **−10.6 %** | code + extract |

**Code drift with the extract held fixed: $+0.000 — exactly zero.** A0′ does not
merely agree to three decimals: its `hourly/system_2025.parquet` and
`hourly/class_hourly_2025.parquet` are **`max|diff| = 0` against the keeper's
committed sidecars on every column** — `price`, `slack`, `dump`, `demand`,
`reserve_price`, and per-class `mw` (78,840 and 166,440 rows). Corroborated
independently in the solve logs: A0′ reports the per-gen co-opt's *"deliverable
ramp mean **38.1 GW**"*, the exact figure carried in the keeper's own designation
note, against A1's 38.9 GW.

**So the post-keeper code surface is measured PJM-inert, and the
guard/extract accounts for 100 % of the −$0.518 (−1.3 pp) move.** PJM matches
MISO here and, like MISO, does **not** carry the caiso-123 confounded-A0 defect.
A1's C3a-2025 FAIL is the guard's own effect, not code drift, and the −$0.518 is
the number a re-tune has to close.

The probe bundle is a **single-year** solve and is therefore **deleted, never
registered** (rule 16 — a one-year bundle is a throwaway diagnostic only); its
numbers live here. The reverted extract was restored immediately after the solve
and re-verified by `git hash-object` against HEAD's blob (`65ff8371`).

The probe bundle is a **single-year** solve and is therefore **deleted, never
registered** (rule 16 — a one-year bundle is a throwaway diagnostic only); its
numbers live here.

## §6 — ops and rule compliance

* **Rule 16 [R-ALLYEARS]:** one bundle, 2023 + 2024 + 2025. The two staged
  intermediates (`pjm129_a1_y23`, `pjm129_a1_y2324` — solved and deleted under
  their pre-renumber names `pjm128_a1_*`, see the lane note below) are
  scaffolding, not runs:
  their `class_hourly_<year>` sidecars were lifted into the final bundle
  (`_copy_reused_year` does not carry `hourly/`) and verified against the final
  bundle's own `system_<year>` slices (`max|diff| = 0` on price / demand / slack /
  dump), then the directories were deleted. Together with the isolation probe,
  **no partial-year bundle exists anywhere.** Four solve-years spent total
  (2023, 2024, 2025, + the 2025 isolation probe).
* **Rule 15 [R-DASHBOARD]:** registered this session with its `hourly/`
  sidecars, verdict notwithstanding.
* **Rule 22 [R-HOLDOUT]:** 2023–2025 only. PJM has no calibration-complete
  marker and `holdout-freeze.json` is `active=true`; **the freeze is untouched
  and this finding does not lift it** — only the owner does.
* **Rule 12 [R-PARALLEL]:** solve-years strictly sequential, one process each.
  No concurrent invocation was launched: a single PJM year needs 14.9–15.1 GB of
  a 15.7 GB box, so two at once is not a rule-12 option here regardless of how
  the invocations are counted.
* **Rules 20/23/24:** nothing tuned. No offer-curve band, sigmoid, floor, ORDC
  parameter, derive value or surface JSON touched; no ledger entry widened or
  added; no measured-behaviour constant re-derived (this lane has no source-data
  change of that kind to cite). The arm's `calibration_attestation.json` carries
  the keeper's own DOF ledger **unchanged** — it is the same recipe.

## §7 — what PJM needs next

**A re-tune charter, scoped to three gates under a ~1.3 pp structural price
reduction**, and it cannot be closed by relaxing the envelope back (rule 1):

1. **C3a-2025** (−10.6 %, needs +0.6 pp). This is the *same* stratum pjm-121
   closed and pjm-120/122/123 diagnosed: of pjm-121's +$0.35/MWh 2025 gain,
   73 % was a level lift on cheap strata, and the monotone dispersion compression
   is untouched. The measured-ownership route (pjm-122's finding: fitted coal
   rungs own the $40–150 region the measured corpus assigns to the CC top belt
   and CT_FAST) is the standing candidate and is *level*-bearing, so it is the
   natural place to look.
2. **C3c-2024/2025** (0.39×, 0.47×; need ≥0.50×). Downstream of the open
   G-20b/G-22 reserve tightness root cause, now with more supply in it.
   pjm-124/125 closed both scoping framings of that lever, so this needs the
   root cause, not another scoping variant.
3. **C1-2023 CC_REGULAR** (−8.10 TWh against an 8 TWh band, share −0.5 pp against
   3 pp). The **cheapest** of the three by an order of magnitude — 0.10 TWh, 1.2 %
   of the band — and it is a *volume* miss on a class the guard barely moved
   (−0.23 TWh); the row was already at 98 % of band before the guard. Worth
   checking whether it is genuinely CC_REGULAR's or a displacement side-effect of
   the +2.51 TWh ST_GAS return.

Sequencing of a PJM re-tune against the parent charter's still-open residual /
freeze-lift item is an **owner call**, exactly as for MISO and CAISO.

---

**Lane-numbering note.** This session opened as **pjm-128** and pre-registered its
charter under that number, taken from `docs/calibration-log/pjm.md`'s then-current
tail. A concurrent session (the DA-award-feed scope census, PR #2965) landed on
`main` with the same number while this lane's solves were running, so everything
here was **renumbered 128 → 129** before registration: the bundle, the run id
(`2026-07-26-pjm-129-meritguard-a1`), the charter and this finding. The only
residue is that the deleted staged-chain scaffolding directories were created
under `pjm128_a1_*`, which the git history shows. Next free PJM number after this
entry: **pjm-130**.
