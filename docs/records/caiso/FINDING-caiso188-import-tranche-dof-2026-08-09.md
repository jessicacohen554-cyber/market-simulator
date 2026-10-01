# FINDING — caiso-188: the `IMPORT_TRANCHES[CAISO]` census settles the row at **6 live fitted scalars, not 7**, and it clears the 8,800 MW spot ladder of the role it was charged with — because the census found the **real** binding fitted scalar next door: the **7,500 MW `WECC_import_simultaneous` cap, which the ledger and `_caiso186os` both certify as SUPERSEDED, has silently governed every CAISO run since caiso-175** and pins total import in **764 / 477 / 809 hours** of the current keeper

**Keeper `2026-08-09-caiso-184-c1-lpbasis` UNCHANGED. No promotion is proposed.**
CAISO's `complete` marker is withdrawn and the owner sitting is prepared and
pending; nothing here pre-empts it, and `calibration-complete.json` /
`holdout-freeze.json` are untouched. 2023–2025 only (rule 22).

Instruments (committed, no network):

* `scripts/probes/_caiso188_import_tranche_census.py` — §1–§3. Static limb
  census, then the keeper's **built fleet** per year
  (`run_calibration.run_year(fleet_only=True)`, the caiso-131/134/140/150/151
  machinery — a fleet build, never a solve) for liveness, and the per-corridor
  ceiling stack. Record `_caiso188_import_tranche_census.json`.
* `scripts/probes/_caiso188_seam_cap_forensics.py` — §4. Committed bytes only.
  Record `_caiso188_seam_cap_forensics.json`.
* `results/calibration/PRECHECK-caiso188-mic-seam-2026-08-09.md` — the A/B gates,
  pre-registered before any solve.

No scored criterion was read to select or reject anything below. **C3a is a live
FAIL on this ISO and is reported, never targeted** (rule 1 `[R-STRUCT]`, rule 13
`[R-MEASURED]`).

---

## §1 — the limb census, at HEAD

`IMPORT_TRANCHES["CAISO"]` / `IMPORT_TRANCHES_BY_YEAR["CAISO"]` split into four
limbs. Two are closed; two are live — the split `_caiso186os_dof_repair` read
off the source text, now **measured on the built fleet** (§2) rather than read:

| limb | tranches | identification | verdict |
|---|---|---|---|
| **firm capacity** | `PNW_hydro_base`, `DSW_solar_PV` | MEASURED, per year (1,072/1,558/1,566 and 1,251/1,813/1,805 MW) | **CLOSED** — DMM annual RA-import capacity × published branch-group MIC north/south split, two cited primary sources |
| **firm price** | same two | RESIDUAL — $28.00 / $48.00, identical in all three years, `STATIC-FITTED-PENDING-MEASURED` in the source itself | **LIVE ON THE BINDING PATH** (§2 measures both `mc` rows as CONSTANT) |
| **spot capacity** | `PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity` | RESIDUAL — 1,800 / 1,800 / 2,200 / 3,000 = **8,800 MW**, no primary source anywhere, identical in all three years | **LIVE, but NOT as a ceiling** (§3) |
| **spot price** | same four | SUPERSEDED — the per-hub injector overwrites each `mc` row with its own measured hub series | **CLOSED on the backcast binding path** (§2 measures all four as hourly) |

**The count is 6, not 7.** Four spot capacities + two firm prices. The
`docs/mechanism-testing-matrix.md` §5.2 block and the caiso-186 owner-sitting
memo both print "7 live fitted scalars" over the same enumeration; that is an
arithmetic slip, corrected here and in the matrix. Nothing else about the split
changes.

`EXTERNAL`-side note, same ledger row: **`EXPORT_TRANCHES["CAISO"]` is not on
the keeper's binding path at all.** `build_caiso_per_hub_intertie` builds one
export leg per corridor bounded by `_caiso_corridor_export_cap_mw`, which reads
the corridor's **published** link rating (COI 4,800 / Path-46 10,623 MW) from the
topology; the static export sink is only reachable through the superseded
`build_export_sinks` path. The ledger row names both dicts and should say so.

## §2 — liveness, measured on the keeper's own built fleet

Per import row, 2025 (2023/2024 in the record; the pattern is identical):

| row | pmax MW | capability mean MW | floor mean MW | mc mean | mc |
|---|---|---|---|---|---|
| `WECC_PNW::PNW_hydro_base` | 3,234.5 | 1,426.2 | **1,140.6** | **28.00** | **CONSTANT** |
| `WECC_PNW::PNW_midC` | 1,800.0 | 1,764.0 | 0.0 | 43.00 | hourly |
| `WECC_DSW::DSW_solar_PV` | 3,728.2 | 1,768.9 | **1,427.2** | **48.00** | **CONSTANT** |
| `WECC_DSW::DSW_CCGT` | 1,800.0 | 1,764.0 | 0.0 | 46.85 | hourly |
| `WECC_DSW::DSW_CT` | 2,200.0 | 2,156.0 | 0.0 | 51.90 | hourly |
| `WECC_DSW::WECC_scarcity` | 3,000.0 | 2,940.0 | 0.0 | 50.48 | hourly |
| `WECC_DSW::DSW_surplus_clean` | 5,472.0 | 1,526.6 | 0.0 | 36.47 | hourly |
| `WECC_DSW::DSW_overnight_clean` | 6,487.0 | 952.3 | 0.0 | 32.47 | hourly |
| `WECC_DSW::DSW_daytime_clean` | 5,770.0 | 699.7 | 0.0 | 32.47 | hourly |

Three readings:

1. **The two firm prices are live and static, exactly as `_caiso186os` said** —
   their `mc` rows are flat at $28.00 / $48.00 in all three years while every
   other rung varies hour to hour. Above the clipped must-flow floor
   (1,140.6 / 1,427.2 MW mean in 2025) the blocks are offered to the LP as
   economic capability *at those two fitted prices*; that is the caiso-151
   `caiso_firm_import_selfsched_clip` re-arm, and the caiso-77 retirement
   argument ("pmin = pmax, so it can never set the margin") does not cover it.
2. **The four spot prices are closed**, measured hub series hour by hour.
3. **The spot rungs are price-differentiated only by the CARB EF ladder.** Since
   the injector writes `hub + wheel + border × (EF / EF_unspecified)`, the four
   DSW rungs sit at the *same* hub with different EFs. The keeper carries
   `carbon_price = 0.0` with `state_carbon_pricing = True`, and the built rows
   invert to a border adder of **$12.01/MWh** (allowance ≈ $28.06/t): `DSW_CT −
   DSW_CCGT = 12.01 × (0.55−0.37)/0.428 = $5.05`, and `WECC_scarcity` lands
   between them at `+$2 wheel + 12.01 × (1−0.865)`. So the live content of the
   spot-capacity limb is **where the carbon-EF breakpoints sit**, not how deep
   the ladder is.

## §3 — the ceiling stack: the 8,800 MW is **not** the operative corridor ceiling

Per corridor per hour, the ladder's own capability (Σ pmax × availability)
against the two other bounds on the same physical quantity — the measured p95
deliverability envelope (`caiso_corridor_flow_limit`, ARMED) and the published
WECC path rating:

| year | corridor | ladder mean | envelope mean | path rating | **hours the ladder is the tightest** |
|---|---|---|---|---|---|
| 2023 | WECC_DSW | 10,630 | 4,739 | 10,623 | **0 / 8,760** |
| 2023 | WECC_PNW | 2,691 | 1,341 | 4,800 | **62 / 8,760 (0.7 %)** |
| 2024 | WECC_DSW | 11,563 | 4,725 | 10,623 | **0 / 8,760** |
| 2024 | WECC_PNW | 3,096 | 1,589 | 4,800 | **152 / 8,760 (1.7 %)** |
| 2025 | WECC_DSW | 11,807 | 4,885 | 10,623 | **0 / 8,760** |
| 2025 | WECC_PNW | 3,190 | 1,714 | 4,800 | **0 / 8,760** |

**The measured envelope is the tightest per-corridor bound in 25,866 of 26,280
corridor-hours.** The fitted spot depth is the operative ceiling in **214**, all
on the north corridor, all in 2023–2024. It is *not* inert, though: strip the
four spot rungs and the remaining firm + measured-clean capability would fall
below the measured envelope in **3,177–5,991 hours** per corridor-year — the
spot depth is the supply that lets the model reach a measured ceiling.

So the limb's two live roles are **(a)** filling the band between the firm +
measured-clean depth and the measured envelope, and **(b)** placing the CARB-EF
breakpoints of §2.3. Neither is the role
`FINDING-caiso140` §C's "2.7–3.0 GW import plateau" was attributed to in the
`_caiso186os` verdict: that plateau is a **price**-parity plateau (CA λ equal to
the WECC_DSW node λ exactly), and at the keeper's own depths the corridor is
bounded by the measured envelope, not by the ladder, in every DSW hour of all
three years. The attribution "that plateau IS this depth ladder" is **corrected**
to: the plateau's *length* is set by the ladder, its *level* by the measured hub.

### §3.1 — the published object, and where it does and does not map (rule 14)

The three candidate published objects the charter names, laid against the ladder:

| year | corridor | ladder total | published path rating | branch-group MIC |
|---|---|---|---|---|
| 2023 | WECC_PNW | 2,872 | 4,800 | 7,389 (north) |
| 2023 | WECC_DSW | 8,251 | 10,623 | 8,666 (south) |
| 2024 | WECC_PNW | 3,358 | 4,800 | 7,581 |
| 2024 | WECC_DSW | 8,813 | 10,623 | 8,871 |
| 2025 | WECC_PNW | 3,366 | 4,800 | 7,478 |
| 2025 | WECC_DSW | 8,805 | 10,623 | 8,670 |

* **MIC does not map, and using it here would double-count.** Maximum Import
  Capability is an **annual RA-showing allocation**, not an hourly transfer
  limit; and the model already spends that same object twice over — once as the
  firm block's north/south split, once as the aggregate seam limit under
  `capacity_deliverability_limits`. Sizing an hourly spot rung on it a third
  time is a rule 19 `[R-ONE-MECH]` violation on top of a category error. *(The
  DSW ladder total lands within 0.7–4.8 % of the south MIC in all three years.
  That is close enough to be suggestive of how the number was first chosen and
  **not** close enough to be a derivation; it is recorded, not adopted.)*
* **The path ratings DO map, but only to the ceiling role** — which §3 has just
  measured as owned by the measured envelope in 25,866 of 26,280 corridor-hours.
  Re-grounding the ladder totals on them is therefore inert in ≥98.3 % of hours
  and would *loosen* the ceiling in the 214 hours where the fitted depth binds.
* **Nothing published maps to the live role**, the EF breakpoint placement. The
  measured object for that is a Q-Q revealed supply curve — and the CAPACITY
  side of that estimator is the **inverse of the same monotone duration coupling
  whose PRICE side failed its pre-registered LOYO gate at 30.5 % against a 25 %
  bar** (`derive_caiso_import_tranches.py`, caiso-83/86/86b; DO-NOT-REDO). It is
  the same data, the same estimator and the same instability with the axes
  swapped, so it cannot be assumed to pass; it would have to be derived and
  gated on its own before anything could be armed.

**Disposition of the 8,800 MW: it stays, and it stays declared.** No published
object maps onto the limb's live role; the object that maps onto its dormant
role is already superseded by a measured mechanism. Under rule 20 `[R-DOF]` that
makes it an **open root-cause issue, not a parameter to re-fit** — and this
session guessed nothing. What changed is the ledger's description of it (§6).

## §4 — what the census actually caught: the **7,500 MW seam cap is live and binding**

Chasing the ceiling stack of §3 to the aggregate turned up the row next door.

**F1/F2 — the pin, and its date.** The keeper's own committed
`hourly/class_hourly_<year>.parquet` puts total net import at **exactly
7,500.0 MW in 764 / 477 / 809 hours** (8.7 / 5.4 / 9.2 %) and never above it.
7,500 appears nowhere in the CAISO import path except
`WECC_import_simultaneous`. Across the committed bundle lineage the regime
change is exactly dated:

| bundles | import max (2023/24/25) | hours at 7,500 |
|---|---|---|
| caiso-124 … caiso-174 (8 bundles) | 9,497 / 9,169–11,625 / 10,451–10,777 | **0** |
| **caiso-175 … caiso-184 (8 bundles, the keeper included)** | **7,500.0 / 7,500.0 / 7,500.0** | **456–905** |

Every CAISO run from **caiso-175 (2026-08-06)** onward has solved against the
fitted scalar, including `caiso184_c0_control` / `c1_lpbasis` — the designated
keeper and its control.

**Why.** `capacity_deliverability_limits` Part A resolves the published MIC
through `data/clean/capacity-deliverability/`, a **gitignored, disposable
partition that no solve auto-builds**. Absent, `import_limit_by_area` returns
nothing, `_seam_mw` is falsy, `apply_deliverability_seam_limit` is never called —
and the run proceeds with a single WARNING while **`run_config.json` still
records `capacity_deliverability_limits: true`**. The flag is recorded as armed
in the committed artifact and was inert in the LP. With the partition
materialised, the same code at HEAD installs 16,055 / 16,452 / 16,148 MW
correctly (verified this session), so this is an **environment-conditional
silent no-op, not a code defect** — which is worse for provenance, because
nothing committed records which of the two caps a bundle solved against.

**F3 — why the standing proof does not cover it.** `FINDING-caiso133` §3 proved
the seam row unreachable and §4 measured its dual as exactly 0.000 in all 26,280
hours. Both are correct **given the cap they assumed** — the MIC. Re-run against
the value that actually bound:

| year | Σ corridor envelope caps (max) | h ≥ MIC | h ≥ 7,500 |
|---|---|---|---|
| 2023 | 9,631 | **0** | **2,608** |
| 2024 | 9,557 | **0** | **2,982** |
| 2025 | 10,777 | **0** | **3,802** |

The seam row is unreachable at 16 GW and thoroughly reachable at 7.5 GW. And
every one of the keeper's 764 / 477 / 809 pinned hours is a reachable one
(envelope sum ≥ 7,511 MW in the tightest). caiso-133's §4 zero duals were
measured on the caiso-130-era keeper, whose import level had not yet reached the
cap; nothing there is wrong, and nothing there covers today's keeper. This is
new evidence, not a DO-NOT-REDO breach (rule 28).

**F4 — the fitted cap is falsified as a physical bound (rule 14 `[R-ACCURATE]`).**
From the same EIA-930 bytes the corridor envelopes are built from, the **real**
CAISO system carried:

| year | measured total net import: mean / p95 / max | h > 7,500 | h > MIC |
|---|---|---|---|
| 2023 | 3,292 / 7,125 / **13,136 MW** | **271** | 0 |
| 2024 | 3,579 / 7,215 / **13,312 MW** | **293** | 0 |
| 2025 | 4,102 / 8,037 / **15,080 MW** | **681** | 0 |

The real market exceeds 7,500 MW in 1,245 hours and reaches 1.8× it; the
published MIC envelopes every measured hour. This is the
`retire_misattributed_sil` / nyiso-100 pattern exactly: a scalar installed as an
external bound that measurement falsifies as one.

**F5 — the honest cost, stated before the A/B.** In those same pinned hours the
model is **already carrying +1,488 / +1,604 / +763 MW more import than actually
flowed**. So the fitted cap has been **silently compensating** for the standing
CAISO over-import (caiso-121's surplus-belly +2.6 GW, caiso-135's gas
ride-through loading defect, caiso-140 §B). Rule 14 names this case exactly —
the compensating estimate goes, the defect it was hiding becomes the named root
cause — and rule 1 forbids reinstating it because the residual moved.

## §5 — the A/B: every pre-registered gate answered

Arms `caiso188_d0_control` (`2026-08-09-caiso-188-d0-control`) and
`caiso188_d1_micseam` (`2026-08-09-caiso-188-d1-micseam`), both registered on
the dashboard (rule 15), full span 2023–2025 in one bundle each (rule 16), one
delta, years sequential (rule 12).

**G-CTRL — PASSES, and it is the strongest single result here.** Arm A
reproduces the committed keeper **EXACTLY: max |Δ| = 0.00 MW, every class,
every hour, all three years**, and its rubric is identical (C3a +3.7/+10.5/
+13.1 %, C3c FAIL, NOT-YET). That holds *despite* 22 changed `src/` files since
the keeper's `03914d8` and a different solver build (highspy 1.14.0 vs the
bundle's 1.15.1). Two things follow, neither of them inferences any more:

1. **The keeper solved with `capacity_deliverability_limits` INERT.** Arm A has
   the flag explicitly OFF. A run with the published MIC seam in force could not
   reproduce a 7,500-pinned run to 0.00 MW.
2. **`hydro_ror_split: true` never ran either.** Arm A's environment has no
   `hydro-plant-modes` partition, and it still reproduces the keeper exactly.
   Two of the keeper's armed mechanisms are advertised in its `meta.json` and
   absent from its LP.

**G-SEAM — PASSES.** Arm B logs `seam import cap set to 16055 / 16452 / 16148 MW`
for the three years; arm A logs nothing (flag off) and its import maxes at
exactly 7,500.0. The dual settles the attribution with no inference left —
the seam interface group `grp:+WECC_PNW>NP15+WECC_DSW>SP15_rest`, read off each
arm's own `hourly/network_<year>.parquet`:

| year | arm A limit | binding h | mean dual | congestion rent | arm B limit | binding h | mean dual | rent |
|---|---|---|---|---|---|---|---|---|
| 2023 | **7,500** | **764** | **−2.903** | **−$190.7 M** | 16,055 | **0** | **0.000** | **$0.0 M** |
| 2024 | **7,500** | **477** | **−0.223** | **−$14.7 M** | 16,452 | **0** | **0.000** | **$0.0 M** |
| 2025 | **7,500** | **807** | **−0.368** | **−$24.2 M** | 16,148 | **0** | **0.000** | **$0.0 M** |

Arm B's seam dual is **exactly 0.000 in every hour of every year** — i.e. it
reproduces `FINDING-caiso133` §4 precisely, which is what caiso-133 measured on
a keeper whose Part A *had* resolved. And **caiso-157's own numbers reproduce**
on today's keeper to within rounding: it measured 757/472/857 h and
−$187.2 M/−$15.1 M/−$26.9 M; this is 764/477/807 h and
−$190.7 M/−$14.7 M/−$24.2 M. **The same defect, at the same magnitude, seven
sessions later.**

Import maxima return to the pre-caiso-175 lineage values, to the decimal —
**9,497.0 / 9,169.0 / 10,451.5 MW**, the exact maxima of `caiso162` /
`caiso164`. Zero hours pinned at 7,500 in any year of arm B.

**G-IMPORT — REPORTED, and it is a cost.** Mean net import rises only
**+52.3 / +18.4 / +38.4 MW** annually: the effect is entirely inside the
previously-pinned hours, where arm B takes **+586 / +333 / +422 MW** more than
arm A. Against the measured EIA-930 total in those same hours the model's
over-import widens from **+1,488 / +1,604 / +763 MW** (arm A) to
**+2,075 / +1,937 / +1,184 MW** (arm B). This was pre-registered as a disclosed
cost and it is published as one. It does **not** reverse the repair: the fitted
cap is falsified as a physical bound (§4/F4), the per-corridor **measured**
envelopes stay in force and take up the slack (their 2023 duals go
−6.64 → −9.24 DSW and −14.74 → −17.44 PNW — the constraint moves from the
fitted seam to the measured corridors, which is the structurally right place for
it), and rule 14 is explicit that a compensating estimate goes and the defect it
was hiding becomes the named root cause. That root cause is the standing CAISO
over-import (caiso-121 §, caiso-135's gas ride-through loading, caiso-140 §B),
already open and not touched here.

**G-RUBRIC — REPORTED, NEVER A TARGET.** Every criterion holds its status;
**zero gate flips in either direction**. C3a moves **+10.5 → +10.4 %** (2024)
and **+13.1 → +12.9 %** (2025); 2023 stays a PASS. Both arms read **NOT-YET**
on the same basis (C6 UNATTESTED in the bundle, C3a FAIL, C3c FAIL). The
improvement is a rounding-scale by-product of a correctness repair and is
**not** why the repair is kept — nor would a degradation have been a reason to
revert it (rule 1 `[R-STRUCT]`).

**G-LOYO — not triggered.** No determination differs between the arms in any
year, so there is no mechanism-change verdict flip to score leave-one-year-out.

**Solve-environment disclosure.** Arm B was solved with the newly-wired
`check_clean_partitions` guard temporarily un-wired, so its config matches the
control in **every** field except the single delta. The guard had fired on the
relaunch — on `hydro_ror_split`, correctly — and honouring it would have forced
a *second* mechanism change into the same A/B. The bypass was local and
temporary; the committed tree carries the guard wired (`git diff` clean against
the commit). Arm B's first attempt was OOM-killed in the 2025 solve while two
per-plant CAISO LPs ran concurrently — rule 12's own warning, observed; it was
re-solved alone.

## §6 — the DOF-ledger repair, and the wiring fix

Repaired **at the source** (`scripts/build_dof_ledger.py`), so every future
bundle carries the corrected text, and re-generated into the keeper's committed
attestation (`audit_keepers --check --iso CAISO` PASS 0/0 afterwards). Rule 25
`[R-ISO-SCOPE]`: no other ISO's row text changes — the generic
`IMPORT_TRANCHES/EXPORT_TRANCHES[iso]` row is untouched for NYISO/MISO/PJM and
CAISO branches to its own census.

1. **`IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`** now carries the four-limb census
   of §1–§3 and, for the first time, **`n_scalars: 6`** — the count the row
   always owed. Its `root_cause` records why no published object closes it and
   why the Q-Q capacity route inherits the failed price LOYO.
2. **`WECC_import_simultaneous.cap_mw`** stops asserting supersession it cannot
   verify. The old text — *"Not in the keeper binding path; governs the forecast
   / non-deliverability path only"* — is replaced by the measurement: the
   supersession is **conditional** on Part A resolving, the condition **failed**
   for every CAISO bundle from caiso-175 onward, and the scalar is therefore
   **live on the keeper's backcast binding path**.

**The wiring fix, and why the defect recurred at all.** caiso-157 found this
exact failure at caiso-146/147/148/151/153 (757/472/857 binding hours) and
installed a fail-fast guard, `market_sim.data.input_completeness.
check_clean_partitions`, to stop it happening again. **That guard has never once
run in a solve.** Its only call site is `pipeline/year.py::run_year_solve` — a
function with **no production caller**; the backcast orchestrator reaches the LP
through `run_energy_solve` directly. Its unit tests call it directly, so it
passes CI while being dead on the solve path. Two changes:

* `scripts/run_calibration.py` now calls `check_clean_partitions(config, iso)`
  on the solve path, after the `fleet_only` exit so fleet-reconstruction probes
  keep working. **It fires immediately on the CAISO keeper recipe** — measured
  this session, on `hydro_ror_split`, when arm B was relaunched.
* `apply_interchange_topology`'s unresolved-Part-A branch now WARNs and names
  the baked fallback the LP will actually solve against, instead of passing
  silently. Pinned by
  `tests/unit/data/test_capacity_deliverability_wiring.py::TestSeamOverrideUnresolvedWarns`.

**A second silently-advertised mechanism, measured not suspected.** G-CTRL (§5)
reproduces the committed keeper **exactly** from an arm whose environment has
**no** `hydro-plant-modes` partition — so the keeper's `hydro_ror_split: true`
also never ran. Two of the keeper's armed mechanisms are advertised in its
`meta.json` and absent from its LP. **This session fixes neither by arming it**:
materialising either partition changes the LP and is its own A/B with its own
pre-registration. Filed, not absorbed (rule 19 `[R-ONE-MECH]`, one mechanism per
probe).

**What is still owed, and is NOT done here.** (a) The forecast orchestrator
(`src/market_sim/runner.py`) has no guard call — the same silent-degradation
surface exists there and is filed. (b) Nothing **committed** yet records which
seam cap a bundle solved against; the durable fix is to persist the resolved
value into `run_config.json`, which is why the ledger's `root_cause` names it.
(c) The hydro RoR question above.

## §7 — DO-NOT-REDO (new, binding)

1. **Do not re-attribute the caiso-140 §C belly plateau to the spot-capacity
   ladder.** §3 measures the DSW ladder as the tightest corridor ceiling in
   **0 of 26,280** corridor-hours. The plateau's *length* is the ladder's; its
   *level* is the measured hub. `_caiso186os_dof_repair`'s spot-capacity verdict
   is corrected on this point, not repeated.
2. **Do not size the CAISO spot rungs on MIC.** It is an annual RA-showing
   allocation, already spent on the firm split and the seam limit; a third use
   is a rule 19 double-count on a category error (§3.1). The near-match of the
   DSW ladder total to the south MIC (0.7–4.8 %) is recorded as suggestive of
   provenance, and is **not** a derivation.
3. **Do not re-run the Q-Q ladder derivation on the CAPACITY axis expecting the
   caiso-83 lane to be "still open".** It is the same monotone duration coupling
   whose PRICE axis failed LOYO at 30.5 % vs a 25 % bar; it must be derived and
   gated on its own before anything is armed (§3.1).
4. **Do not quote `FINDING-caiso133` §3/§4 as proof that the seam row is
   unreachable.** Both are exact **given the MIC cap they assumed**. Against the
   7,500 MW value that actually bound, the two corridors' measured envelopes
   exceed the cap in 2,608/2,982/3,802 hours (§4/F3).
5. **Do not treat "the run_config records the flag as armed" as evidence the
   mechanism ran.** caiso-161's lesson (check the gate) and caiso-162's (check
   a call site exists on the lane being solved) now gain a third: **check the
   DATA the gate resolves through**. All three failure modes have now been
   measured on this one ISO.

---

## §8 — ADDENDUM (2026-08-11, caiso-189): the keeper WAS promoted, and its attestation was written post-hoc

*Appended by caiso-189. **Nothing in §§1–§7 above is altered** — this section records
what happened after the body was written, in the same way caiso-183's finding carries its
own promotion addendum.*

### 8.1 The promotion

The body opens "**Keeper `2026-08-09-caiso-184-c1-lpbasis` UNCHANGED; no promotion is
proposed**". That was true when it was written and is **SUPERSEDED**: the **owner promoted
`2026-08-09-caiso-188-d1-micseam` in the SAME session**, superseding
`2026-08-09-caiso-184-c1-lpbasis`. The promotion record is
`docs/handoffs/caiso-186-owner-sitting-2026-08-09.md` — "**KEEPER PROMOTED,
OWNER-DIRECTED IN THE SAME SESSION**" — and it is reflected in
`frontend/data/backcast/keepers/CAISO.json` and the mechanism matrix §5.2 header.

The finding's other governance statements survive the promotion intact:
`calibration-complete.json` / `holdout-freeze.json` **were** correctly left untouched,
because CAISO holds no `complete` marker and rule 22 D-5(b) re-keying therefore does not
fire. The A/B, the census, the seam forensics and every gate stand exactly as measured.

### 8.2 What the promotion shipped without, and what caiso-189 did about it

Every CAISO promotion ships a bespoke `scripts/gen_caisoNNN_attestation.py` that writes
the bundle's `schema` / `governance` / `exceptions` blocks. **The series stops at
caiso-184**: because this promotion was owner-directed after the body was written, no
generator was written for it, and `caiso188_d1_micseam/calibration_attestation.json`
carried **only** the `free_parameters` DOF ledger `scripts/build_dof_ledger.py` writes.

One missing block, two rubric consequences — both mechanical, neither a model defect:

* `calibration_verdict.score_governance` read **C6 UNATTESTED** ("a bundle whose
  attestation carries no governance block is exactly as unattested as one with no file"),
  which **alone** forces `NOT-YET`;
* the incumbent's C3c exceptions never carried forward, so `ledger_entries` was `[]` and
  the two failing C3c years read as **undocumented** FAILs. The owner's C3c standing rule
  could not cover them either — it requires a passing governance gate **and** a lone
  failure, and C3a fails here.

`scripts/audit_keepers.py` check **E8** validates only `free_parameters`, so it reported
"0/0" — green — on an attestation nobody had signed. That is why the gap survived every
audit.

caiso-189 (2026-08-11) wrote `scripts/gen_caiso189_attestation.py` on the pjm-153
precedent (`gen_pjm153_collapse_attestation.py`, for the `pjm152_collapse_A` bundle, which
likewise shipped without its attestation). It computes rather than types every premise —
**G-DELTA** (the arms differ on exactly `capacity_deliverability_limits`, False → True),
**G-SEAM** (Part A actually resolved: control at the fitted 7,500.0 MW limit binding
764/477/807 h vs this bundle at the published MIC 16,055/16,452/16,148 MW with its dual
**exactly 0.0** in every hour of every year), **G-MACHINE** (the machine half of C6, using
the scorer's own constants), **G-DOF** (the `free_parameters` block carried
**byte-identical**, 11 / 8, `n_scalars` 6) and **G-EXC**.

**The verdict delta is bookkeeping only, on committed artifacts, with no solve:**
C6 `UNATTESTED → PASS`; C3c `FAIL → ledgered CAVEAT`; failing criteria `2 → 1`; scored
criteria `7 → 8`. **C3a mean LMP remains the sole load-bearing FAIL** at
+3.4 / +10.4 / +12.9 % against a ±10 % band, and **the determination remains `NOT-YET`.**

### 8.3 Two magnitudes were stale and were refreshed

The four exceptions are the incumbent caiso-184's, carried with `classification` and
`reason` **byte-identical**; this session created no caveat and spent no ledger slot. Their
`magnitude` fields were re-measured on **this** bundle, because a carried magnitude
measured on a superseded bundle is its own governance defect. Two had moved:

| entry | carried magnitude | measured on `caiso188_d1_micseam` |
|---|---|---|
| C3c 2023 | model 0 h > $200 (on `caiso163_asym_path_ratings`) | model 0 h vs RT 47 h — **unchanged** |
| C3c 2024 | model 0 h > $200 (on `caiso163_asym_path_ratings`) | **model 1 h** vs RT 35 h — **refreshed** |
| C3a 2025 | λ 39.3543 $/MWh (on `caiso166_measured_loss_zones`) | **38.87** vs RT 34.42 (+12.9 %) — **refreshed** |
| C3a 2024 | λ 38.5678 $/MWh, +11.5 % (on `caiso166_measured_loss_zones`) | **38.27** vs RT 34.65 (+10.4 %) — **refreshed** |

Each refreshed field quotes the carried text verbatim alongside the new measurement, so
nothing is overwritten. Note that C3c **2025 PASSES** on this bundle (model 0 h vs RT 8 h,
small-count |Δ| ≤ 10 h) and caiso-184's ledger carries no 2025 C3c entry, so none was
invented. Under rubric v3.1 `LEDGERABLE_CRITERIA` is `price_tail` alone, so the two C3a
entries **reclassify nothing** — they are carried as the historical record and C3a's FAIL
stands at full magnitude.

Record: `results/calibration/FINDING-caiso189-c6-attestation-2026-08-11.md`,
`scripts/gen_caiso189_attestation.py`, `scripts/audit_keepers.py` (new check **E10**,
which closes the E8 blind spot), `tests/scoring/test_audit_keepers_attestation_shape.py`.
