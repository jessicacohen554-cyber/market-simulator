# CHARTER — CAMPD economic-layup discrimination (merit-order guard)

**Opened** 2026-07-25 by owner instruction, out of `neiso-63`
(`results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md`).
**Status:** **CLOSED WITH CAUSE (owner ruling 2026-08-26, §10)** — guard
ADOPTED-AS-IMPROVEMENT (owner verdict 2026-07-26, §8); freeze LIFTED for the
VALIDATION tier only, locked test stays frozen. The detector question remains
OPEN and is carried explicitly (§10).
**Scope:** all six ISOs.
**Model assignment:** Opus or Fable (writes `scripts/lib/outage_detect.py`, a
core-infrastructure path — CLAUDE.md rule 27).

## 1. The defect

`scripts/lib/outage_detect.py::filter_revealed_outages` keeps a detected down
span when EITHER (a) the unit was down through ≥ `MIN_INMERIT_HOURS` (24) local
high-net-load hours, OR (b) it is a ≥ `FULL_STOP_OVERRIDE_DAYS` (5) full stop
below `FULL_STOP_OVERRIDE_CF` (0.02). The override's docstring states the
premise:

> *economic idling backs down but does not fully stop for weeks*

That premise fails for a gas CC priced out of merit for weeks — which is the
normal New England winter state and, per the cross-ISO screen, common
everywhere. A sustained economic layup satisfies **both** surviving branches, so
it is booked as a mechanical outage and its capacity is deleted from the
availability envelope.

Measured consequence: every ISO books **23–46 % of its CC capacity-year** as
outage against a real EFOR + planned-maintenance norm of ~10–15 %.

## 2. What the audit already settled (do not re-litigate)

- **The contamination is window-level, not unit-level.** Keeping only units with
  ≤3 windows/unit-year fixes the seasonal shape (monthly r +0.53→+0.84,
  +0.47→+0.75, +0.70→+0.96 for NEISO 2023/24/25) but collapses the level
  (410 vs 4,575 MW). Real outages live inside high-frequency units' records too.
  **Any fix must classify each window, not each unit.**
- **Common-mode / class-simultaneity discrimination is ruled out.** At every
  τ ∈ [0.30, 0.50] the seasonal correlation is *worse than applying no filter*,
  because genuine shoulder maintenance is itself strongly clustered.
- **The detector is not broadly broken.** It reproduces ISO-NE's published
  series in autumn (0.86–1.06×), when real maintenance dominates. The defect is
  specific to periods when units are out of merit.

## 3. The candidate mechanism

A **merit-order guard**: a window is not credited as an outage when the unit was
plausibly *out of merit* across it. The phenomenon is fuel-economic, so the
discriminator should be too.

Inputs available and admissible (rule 13 — delivered fuel prices are an
explicitly allowed physical input; the detector already carries class economic
guards `ST_GAS_CF_PEAK` and `SHORT_BASELOAD_CF`):

- delivered fuel price on the unit's own basis (the ISO's hub/citygate series
  the model already loads),
- the unit's heat rate (CAMPD marginal-HR artifacts exist per ISO),
- measured net load / the existing `high_load_mask`.

**Design questions the charter must settle before any build:**

1. What is the out-of-merit test — the unit's own SRMC against a fuel-only
   proxy for the marginal price, or against a class-relative rank? It must not
   use LMP, cleared price, or any MWh residual (rules 11/13/26).
2. Does the guard *drop* a window, *shorten* it to its genuinely-down core, or
   *reclassify* it into a separate non-outage column the fleet builder treats
   differently?
3. Per-class parameters or one ISO-agnostic rule? Rule 24 forbids a scalar
   fitted on one ISO's residual leaking into another's.
4. What happens where fuel-price data is thin (pre-2020, non-gas classes)?

## 3a. FROZEN DESIGN (neiso-64, 2026-07-25) — owner sign-off 2026-07-25

Answers to all four questions, with the no-solve evidence each rests on. Probes
read committed artifacts only (`campd-unit-outages-<ISO>.csv`,
`campd-unit-level/<ST>_<YYYY>.parquet`, `gas_basis_by_iso_month.csv`,
`gas-prices/henry_hub_{daily,monthly}.csv`,
`_processed-legacy/eia923_monthly_fuel_costs.parquet`, and each ISO's published
outage instrument). No LP solve was run and no keeper was touched.

### D1 — the out-of-merit test: SRMC vs the *revealed marginal cost* (Q1 option 1)

Per unit `u`, hour `t`:

* **Measured heat rate** `HR_u = Σ heatInput / Σ grossLoad` over the unit's
  running hours (`CF ≥ REAL_RUN_CF`), pooled over the years of the derive
  invocation. CAMPD-measured; clipped to `[4, 20]` MMBtu/MWh against meter noise.
  A unit with fewer than `MIN_REAL_RUN_HOURS` (24) running hours has no
  identified heat rate and is excluded (see D4).
* **Delivered fuel price** `px(u, t)`, by the unit's own fuel:
  * *gas* — the ISO's delivered hub: measured Henry Hub **daily** re-centred on
    the measured Henry Hub **month**, plus the ISO's measured monthly basis
    (`gas_basis_by_iso_month.csv`; all six ISOs, 2015–2026). Mean-preserving at
    the monthly hub level, so only the within-month shape is added.
  * *coal* — F923 delivered, plant-month → state-month (volume-weighted) →
    ISO-month (volume-weighted).
  * *anything else* (oil, other) — no series; unit excluded (D4).
* `SRMC_u(t) = HR_u × px(u, t)`. **No VOM adder**: a per-class additive would be
  a free parameter (rule 20) with no discriminating power, since every unit is
  ranked through the identical construction.
* **`RCC(t)` — the revealed clearing cost** — the capacity-weighted
  `RCC_PCTL = 0.90` quantile of `SRMC` over the units **measured running** at
  `t` (`CF ≥ REAL_RUN_CF`), **excluding cogeneration** (measured non-zero CAMPD
  `steamLoad` — heat-driven, not economically dispatched, so it carries no merit
  information; keyed on the measured quantity, not a class name, per rule 17).
  p90 rather than the max so a single reliability-committed unit cannot set the
  band.
* A window's **out-of-merit share** = the fraction of its hours with
  `SRMC_u(t) > RCC(t)`.
* **A window is ECONOMIC LAYUP iff its out-of-merit share ≥ `OOM_FRAC = 0.90`**
  — "for essentially the whole window, cheaper capacity than this unit was
  setting the revealed margin."

Every input is measured CEMS operation or a delivered fuel price. There is no
LMP, no cleared price, no cleared quantity and no residual anywhere in the
construction (rules 11/13/26).

**Why this and not the alternatives.** The self-referential variant (compare the
window's fuel price to a percentile of the unit's *own* running-hour price
distribution) was probed first and is **rejected**: the unit's heat rate cancels
out of a within-unit percentile comparison, so it can only see the
*fuel-cost-blowout* half of out-of-merit. It fixed NEISO DJF but left JJA
untouched (1.93× → 1.93×) and, in the mild 2024 winter, its NEISO gain sat
**inside the placebo band** (r +0.55 vs placebo p95 +0.56). Cross-unit ranking
against `RCC` is what puts the heat rate back in, and it is the only variant
that moves all four seasons.

**Evidence — NEISO 2023/24/25, detector ÷ published ISO-NE Section 3 line C:**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / monthly r | 1.52× / +0.53 | 1.57× / +0.47 | 1.22× / +0.70 |
| guard on, level / monthly r | **1.36× / +0.71** | **1.29× / +0.61** | **0.92× / +0.78** |
| placebo p95 (same GW-days dropped at random, 30 draws) | +0.63 | +0.55 | +0.78 |

Level and shape improve **together** — unlike unit-frequency filtering (shape
+0.84 but level collapsed to 410 MW) and unlike common-mode (shape worse than no
filter). The guard beats the placebo p95 in 2023 and 2024 and sits exactly at it
in 2025 (the year whose baseline shape was already good), so the gain is
discrimination, not the mere removal of MW.

**Positive control — the two populations land in the two buckets ISO-NE itself
publishes.** ISO-NE's Morning Report Section 3 reports mechanically unavailable
capacity (`gen_outages_reductions_mw`) *separately* from available-but-not-
committed capacity (`uncommitted_available_gen_nonfast_mw`) — i.e. the published
instrument measures the layup population directly. Monthly correlation, 2023 /
2024 / 2025:

| window set | vs published OUTAGES | vs published UNCOMMITTED |
|---|---|---|
| baseline (all windows) | +0.53 / +0.47 / +0.70 | +0.34 / +0.45 / +0.48 |
| **KEPT** (guard: mechanical) | **+0.71 / +0.61 / +0.78** | +0.08 / +0.28 / +0.31 |
| **VETOED** (guard: layup) | −0.26 / +0.01 / +0.24 | **+0.77 / +0.71 / +0.67** |

The vetoed windows are anti-correlated (or uncorrelated) with published outages
and strongly correlated with published uncommitted-available capacity. That is
the charter's identification requirement met against a published instrument, not
a residual.

### D2 — RECLASSIFY, not drop and not shorten

The vetoed windows are a real, separately-measured population (D1 positive
control), so the information is preserved rather than discarded:

* the mechanical extract `campd-unit-outages-<ISO>.csv` keeps only the
  non-vetoed windows — an economically laid-up unit **is available**, and the LP
  must decide not to run it on its own economics;
* the vetoed windows are written to a labelled companion
  `campd-unit-outages-layup-<ISO>.csv`, same schema plus the measured
  `out_of_merit_share` that carried the call, which **no loader reads by
  default** — an audit artifact and the validation series, following the
  existing `-e923-` / `-maxgen-` / `-short-` companion convention.

**Not shortened.** There is no evidence of a "genuinely-down core" inside a
layup window; a sub-window classifier would be a fitted answer key with nothing
to identify it against. **No new LP mechanism** (rule 18): mechanical
unavailability stays in the outage overlay, and economic non-commitment stays
where it already lives — the dispatch economics.

### D3 — one ISO-agnostic, class-agnostic rule

Both knobs (`RCC_PCTL`, `OOM_FRAC`) are structural percentiles over per-ISO
self-referential distributions; **no scalar fitted on one ISO's residual is
carried into another** (rule 24). Class enters only through two *physical*
facts, not tuning: cogeneration is excluded from the `RCC` panel (measured
`steamLoad`), and the unit's fuel selects its price series. The knobs are
identified **jointly across the ISOs with published instruments**, never per
ISO, and only against those published outage series — rule 14 reconciliation of
an input to its own measurement, never rule 13 fitting to a dispatch outcome.
They re-derive only on a source-data change (rule 23). The window-grain
out-of-merit share is close to binary (NEISO: p25 = 0.00, p75 = 1.00), so
`OOM_FRAC` is not load-bearing — 0.70 → 1.00 moves the NEISO veto count only
560 → 412.

### D4 — thin fuel data: INERT, fail-safe, no fabricated basis

The guard can only ever **remove** windows, so every gap degrades to
current behaviour:

* no measured heat rate (< `MIN_REAL_RUN_HOURS` running hours) → unit excluded
  from the `RCC` panel **and** from the guard; its windows are kept.
* no delivered price for the unit's fuel (oil, "other", a coal plant outside
  every F923 ladder rung, a year outside the basis table) → same exclusion.
* an ISO-year with no `RCC` hours at all → extract byte-identical.
* **Henry Hub is never substituted for a missing ISO basis.** For NEISO the
  basis *is* the signal; a Henry-Hub fallback would silently switch the test off
  while appearing to run.

### Gate

`MERIT_ORDER_GUARD_ENABLED = False` in `scripts/lib/outage_detect.py`, surfaced
as `--merit-order-guard` on `scripts/data/derive_campd_unit_outages.py`.
Byte-inert when off, **proven at full extract scale**: a full 2018–2026
re-derive without the flag reproduces every committed extract blob exactly
(NEISO `a95c0928`, CAISO `3dc01fae`, NYISO `181fefb9`, ERCOT `b4b48f5a`).

## 4. Validation protocol — binding

- **Anchor: the published instrument, never the price residual.** The four
  DAM-first gates wired 2026-07-24 (`caiso_dam_outages`,
  `miso_native_outage_source`, `neiso_operable_capacity_availability`,
  `pjm_dam_availability`) give CAISO / MISO / NEISO / PJM a published
  outage/availability series. The corrected extract is scored against **that**,
  on both level and seasonal shape, at **no solve cost**. ERCOT and NYISO have
  no native gate and need a separately-identified cross-check before their
  extracts can be declared fixed.
  **Amended 2026-07-25 (owner):** ERCOT *does* carry a published anchor —
  `data/raw/ercot-thermal-dam-availability.csv` (60-day DAM disclosure, daily
  class `rating_mw − live_mw`), already consumed by the ERCOT overlay. It is
  adopted as ERCOT's validation series **with the caveat** that DAM
  offered-capacity conflates mechanical unavailability with a unit that simply
  did not offer, so it carries some layup itself. **NYISO alone remains
  unverified.**
- **Explicitly inadmissible:** trimming, scaling, or thresholding the extract
  until model *prices* match actuals. Rule 14 permits reconciling an input to
  its own published measurement; rule 13 forbids reconciling it to a dispatch
  outcome. The published outage MW is the target, the LMP residual is not.
- **Rule 22:** structural mechanism change ⇒ leave-one-year-out within
  2023–2025 before any keeper promotion.
- **Rule 15:** both arms registered whatever the verdict.
- **Rule 23:** any re-derived constant cites the source-data change, not a
  residual.

**Scope caveat on level ratios (2026-07-25).** The CAMPD extract covers only the
CEMS-reporting fossil fleet (coal / CC / gas-steam); several published series
are whole-fleet (MISO, PJM, CAISO). A level *ratio* is therefore only
interpretable where the thermal-only extract **exceeds** a whole-fleet published
total — an unambiguous over-count, as in NEISO. The robust cross-ISO axis is the
**monthly correlation** against the published series, plus the placebo test.

## 5. Blast radius — every keeper is implicated

The NEISO keeper's offer curves are demonstrably co-dependent on the
over-count: relieving it moved mean LMP −7 to −9 % and halved h>$200 (70→26 in
2023, 102→42 in 2025). That is the ERCOT-79 / nyiso-63 condition (rule 11 — the
estimate was silently compensating). Expect the same class of dependency
wherever a keeper was calibrated against the inflated envelope, and expect some
keepers to need re-tuning rather than a fix-in-place.

Sequencing note: the `neiso-62` operable-capacity denominator band
**[0.737, 0.849]** is **secondary to this charter**. Reconciling that overlay
matters only if it is load-bearing; the correct order is to fix the detector
first and let the fleet-grain published series serve as the *validation
instrument* it is suited to be, since a fleet aggregate cannot carry per-unit
availability.

## 6. Governance state while this charter is open

**Holdout spending is FROZEN across all ISOs**
(`frontend/data/backcast/holdout-freeze.json`, declared 2026-07-25, enforced in
`run_calibration_full.py::enforce_holdout_year_gate`). No validation or
locked-test year may be solved, scored, or registered until this charter reaches
a decision. Data intake is unaffected.

**[SUPERSEDED 2026-08-26 by the closure ruling (§10).** The charter has reached
its decision and the freeze is now TIER-SCOPED rather than total: the
VALIDATION tier (2020–2022) is lifted — governed by the `complete` marker +
`--holdout-authorized` alone — while the LOCKED TEST (2019, H1-2026) stays
frozen for every ISO, `final` marker or not. The paragraph above is retained
verbatim as the record of the governance state while the charter was open.]

No marker or frontier has been withdrawn on this finding. Unlike nyiso-63 the
NEISO determination held and the fit improved, so the evidence does not yet meet
the withdrawal bar — but the NEISO frontier (2026-07-11) and calibration-complete
marker (2026-07-07) are **open questions** pending this charter.

## 7. Definition of done

Either:

- **Adopted** — corrected detector merged, each ISO's extract re-derived and
  scored against its published instrument, affected keepers re-audited on the
  corrected envelope (fix-in-place or re-tune, per ISO), freeze lifted by the
  owner; or
- **Closed with cause** — the merit-order guard is shown not to separate the
  populations (as common-mode was), the extract is confirmed fit for purpose on
  evidence, and the freeze is lifted.

A charter that stalls without either outcome leaves the freeze in place. That is
the intended failure mode, not an accident.

## 8. VERDICT — ADOPTED-AS-IMPROVEMENT, freeze HELD (owner, 2026-07-26)

The owner adopted the merit-order guard as a **genuine measured improvement,
not a closure of the neiso-63 finding**, choosing adopt-and-hold over
adopt-and-lift and over close-with-cause:

- **Adopted.** The guard patches merge (still default-off,
  `MERIT_ORDER_GUARD_ENABLED = False`); each ISO's committed extract is
  re-derived guard-on and committed together with its
  `campd-unit-outages-layup-<ISO>.csv` companion — the availability envelope
  every keeper reads now excludes the reclassified economic-layup windows.
- **Freeze HELD.** `frontend/data/backcast/holdout-freeze.json` stays
  `active=true`. The residual over-count survives the guard — NEISO 2023–24
  still runs 1.29–1.36× a whole-fleet published total on a thermal-only
  extract — so out-of-training years remain preserved until that residual is
  either explained (scope) or fixed. Only the owner lifts the freeze; §6's
  clause that no session lifts it by inference stands.
- **Keeper re-audits proceed** (§5 blast radius): NEISO is done
  (fix-in-place, `2026-07-25-neiso-64-meritguard-a1`); ERCOT / PJM / MISO /
  CAISO / NYISO replay their keepers in-sample (2023–2025, one bundle,
  rule 16) on the corrected envelope, both arms registered (rule 15).
- **Definition-of-done status:** the §7 "Adopted" leg is satisfied except its
  final clause ("freeze lifted by the owner"), which is deliberately deferred
  to the residual-over-count investigation. The charter stays open on that
  single item plus the outstanding re-audits.

**Amendment to the CAISO re-audit cell (2026-07-26, caiso-123).** The CAISO
"RE-TUNE REQUIRED" verdict (`2026-07-26-caiso120-meritguard-a1`, C3a-2025
+10.0 → +11.1 %) was measured against a confounded A0: the CAISO extract was
derived-not-committed until 07-24, the keeper's committed bytes carry a
session-local PARTIAL derivation, and the 07-24 backfill (#2842/#2844)
committed a heavier FULL derivation independent of — and two days before —
the guard. Same-HEAD isolation puts the guard's own effect at **−0.18 %
(favourable)** and the extract-content change at **+1.24 % λ / CC_REGULAR
−0.49 TWh / import +0.42 TWh**. The re-tune trigger is accordingly
**withdrawn as stated and re-derived**: the keeper's C3a-2025 PASS was
calibrated against a non-reproducible partial envelope (rule-11 class), and
on any honest full derivation C3a-2025 fails by ~+1.1 pp. Sequencing of the
CAISO re-tune against the §8 residual-over-count investigation (the
extract's absolute level, freeze lift condition) is an owner call. Full
record: `results/calibration/FINDING-caiso123-c3a-drift-attribution-2026-07-26.md`.

**MISO re-audit cell RESOLVED (2026-07-26, miso-93): RE-TUNE REQUIRED.** Arm
`2026-07-26-miso-93-meritguard-a1` (2023/2024/2025, one bundle) takes the
`2026-07-25-miso-88-egrid-hr` keeper from `CALIBRATED-WITH-CAVEATS` to
**`NOT-YET`** on one newly-failing gate: **C3a-2024 −8.7 % → −10.1 %**, past the
±10 % veto by 0.1 pp. C1/C2/C4/C5a/C6/C7/C8 hold; C3b/C3c stay ledgered
(C3b-2025 0.208 → 0.214). Unlike the CAISO cell this verdict is **not**
confounded: the MISO extract blob is byte-identical across the keeper's own
`git_sha`, changes exactly once (at `6a8f285`) and not since, and a same-HEAD
isolation probe on the failing year puts the post-keeper **code** drift at
**exactly $0.000** — A0′ reproduces the keeper's committed sidecar to three
decimals — so the guard/extract accounts for **100 %** of the −$0.445
(−1.38 pp) move. Direction and mechanism are as this charter predicted: the
guard removes **11,614 GW-days and adds zero**, **73.5 % of it ST_GAS**, and the
added supply lowers the clearing price (C8 ST_GAS forced share rises in step,
still grounded). A rule-11 discovered-bug signal — the keeper's offer curves
were compensating for the inflated envelope, as at NEISO but milder (−1.4 pp vs
−7…−9 %). **No tuning applied; MISO's ledger is 3/3 saturated, so the re-tune
must close by structure.** Keeper designation unchanged (owner call). Evidence:
`results/calibration/FINDING-miso93-keeper-reaudit-meritguard-2026-07.md`;
charter `docs/handoffs/miso-93-keeper-reaudit-charter-2026-07.md`. Remaining
open re-audit cells: **ERCOT, NYISO** (PJM targets `pjm121_ccbelt` per §3e).

**PJM re-audit cell RESOLVED (2026-07-26, pjm-129): RE-TUNE REQUIRED.** Arm
`2026-07-26-pjm-129-meritguard-a1` (2023/2024/2025, one bundle) takes the
`2026-07-25-pjm-121-cc-belt` keeper from `CALIBRATED` — PJM's first all-pass,
10/10 — to **`NOT-YET` (7/10)** on **three** newly-failing gates: **C3a-2025
−9.3 % → −10.6 %** (past the ±10 % veto by 0.6 pp), and **C3c tail 2024
0.50× → 0.39×** and **2025 0.66× → 0.47×** (band ≥0.5×), plus **C1-2023
CC_REGULAR −7.87 → −8.10 TWh**, crossing an 8 TWh volume band by 0.10 TWh.
C2/C3a-2023,24/C3b/C4/C5a/C6/C7/C8 hold, and C3a-2023 (+5.6 → +4.0 %),
C3b-2023 and C5a-2023/24 **improve**. Like MISO and unlike CAISO this verdict is
an **isolation, not an attribution**: the extract blob changes exactly once after
the keeper's own `git_sha` (at the guard commit `6a8f285`) with the on-disk file
byte-identical to HEAD, and a same-HEAD 2025 probe with the extract reverted
reproduces the keeper's committed `system_2025` and `class_hourly_2025` sidecars
at **`max|diff| = 0` on every column** — post-keeper **code** drift is exactly
**$0.000**, so the guard/extract owns **100 %** of the −$0.518 (−1.3 pp) move.
Mechanism as this charter predicted: **903 windows / 4,624 GW-days removed, zero
added** (11.7 % of envelope), **54.7 % of it ST_GAS**, and the returned supply
lowers the clearing price and *removes scarcity hours* — the C3c leg is the
consequence the pjm-129 charter itself failed to pre-register, and it deepens the
already-open G-20b/G-22 reserve-tightness root cause rather than creating a new
one. A rule-11 discovered-bug signal, −1.3 pp against MISO's −1.4 pp. **No tuning
applied; keeper designation unchanged (owner call).** Evidence:
`results/calibration/FINDING-pjm129-keeper-reaudit-meritguard-2026-07.md`;
charter `docs/handoffs/pjm-129-keeper-reaudit-charter-2026-07.md`.

**And the RAM block on this cell is closed, not deferred.** Both prior attempts
(§3e, then its re-attempt) concluded the PJM replay "needs a ≥24 GB environment"
after being SIGKILLed at 15.9 GB building 2024. Measured per solve-year here:
`resident` after release **1.06 / 1.19 / 1.26 GB** (a fully-attributed floor, not
a leak — the year loop's `del` + `gc.collect()` + `malloc_trim` block works) and
single-year `peak` **14.87 / 14.94 / 15.06 GB**. `peak(N+1) + floor(N)` = **15.93
GB at year 2** reproduces the reported kill to 0.03 GB, at the year both attempts
reported it. **The single-year LP peak is the ceiling; ≥24 GB was never
required** — one fresh process per solve-year (the staged `--reuse-solved` chain
miso-92/93 established, and which `pjm121_ccbelt`'s own attestation records it
was itself solved with at "peak ~14.8 GB") fits every PJM year in a 15.7 GB box.

**Re-audit ledger after this cell.** All six ISOs now carry a registered arm:
NEISO fix-in-place, ERCOT fix-in-place (insensitive), CAISO / NYISO / MISO / PJM
re-tune-required (§3, plus the CAISO amendment above, miso-93 and this entry).
The "ERCOT, NYISO" wording carried above from miso-93 is left as written; per §3
both already have registered arms, so what remains under those names is
**re-tune** work in their own keeper lanes, not an unrun re-audit. Sequencing
every re-tune against §8/§9's still-open residual / freeze-lift item is an owner
call. **The freeze stays ACTIVE; nothing here lifts it.**

## 9. Residual-over-count investigation — CLOSED on evidence; the freeze-lift decision is now the owner's

The single item §8 deferred the freeze to. Three ordered steps were set by
`results/calibration/FINDING-neiso66-overcount-rootcause-2026-07-26.md` §6; all
of the *measurement* is now done, and no LP solve was run for any of it.

| step | status | evidence |
|---|---|---|
| 1 — re-measure NEISO on a sound published-side build | **DONE, PASSED** | neiso-66 §5b — the residual tracks ISO-NE's published `uncommitted_available_gen_nonfast_mw` at +0.70 to +0.85 and is **anti**-correlated with published outages (−0.85 to −0.86) |
| 2 — test the commitment-economics mechanism directly | **DONE, NEGATIVE** | `FINDING-neiso67-commitment-test-2026-07-26.md` — per-unit AUC 0.47–0.57 across 18 configuration-years, **below** the marginal test in every one; on the seam population the sign inverts (AUC 0.39–0.41, and 89–93 % of seam days already repay the published start cost); the commitment band identifies nothing against the published series (−0.51 / +0.26 / +0.05) |
| 3 — disposition | **OWNER DECISION, recommendation below** | — |

**What is now settled.** The residual over-count is a **definitional seam**
(CNOG/ISO-NE publish *unavailability*; the CEMS detector measures
*non-operation*), confirmed against a published instrument — and it is **not
recoverable by any discriminator the admissible inputs support**. Both of the
re-audit's original candidate directions were refuted by measurement
(neiso-66 §3, §4); the marginal test has no power on this population (§4); and
the commitment test now has none either, with its only novel band
(`0 ≤ R < 1`) carrying no signal and rule 19 `[R-ONE-MECH]` forbidding it
stacking on the guard that already owns the `R < 0` half.

**Recommendation to the owner — carry the seam explicitly, then lift.**

- Take **disposition (b)**: leave the availability envelope alone. Option (a),
  a commitment-aware second discriminator in the detector, is not buildable on
  the evidence (neiso-67 §6) and would be a mechanism with no measured
  discriminating power — what rule 1 `[R-STRUCT]` forbids reaching for.
- The §7 **"Closed with cause"** leg is the one that now fits the residual: the
  over-count is explained, quantified, bounded to a definitional scope
  difference, and shown not to be closable by a detector change. That is a
  cause, not a stall.
- **The freeze-lift is still the owner's act and no session takes it by
  inference** (§6, and `holdout-freeze.json` `lifts_when`). What has changed is
  that its stated condition — "the residual is explained or fixed" — is now met
  on the *explained* branch, with the measurement committed and re-runnable.

**The LP-side lane is now also measured, and closed on a negative
(2026-07-26, neiso-68).** The remaining open question — whether the seam
should be closed on the LP side, with the units restored to the envelope as
*available* and the LP declining them on its own commitment economics
(neiso-66 §5b) — was answered against the keeper's own solved clearing prices
(`neiso64_meritguard_a1` committed hourly sidecars; no LP solve): the seam
population is in merit on essentially every seam day at every offer level up
to the keeper's committed multiplier (median in-merit share 100 %, 87.7–97.6 %
of seam days repay the start at LP prices), seam days are indistinguishable
from the same units' running days (AUC 0.48–0.52), the LP's strict decline
predictor fails the D1 placebo in all three years, and restoring the envelope
would inject a first-order 15–38 TWh of phantom dispatch against seam-day
spreads (+$15–21/MWh) no plausible price feedback (≈ −$3–4/MWh measured) can
close. The envelope deletion is definitionally impure but **operationally
load-bearing** — the only mechanism in the system producing the observed
non-operation. An LP-side closure would be a NEW *decline* mechanism (the
existing bridges are min-gen floors that force capacity ON) with no
identifiable driver on any instrument this program admits — which rules
1/12/19 forbid building. Record:
`results/calibration/FINDING-neiso68-lp-seam-screen-2026-07-26.md` (its §6
states the falsification bar any future LP-side proposal must meet). This
closes the last open lane of the residual-over-count investigation; the §7
"Closed with cause" leg fits, and the freeze-lift decision — unchanged — is
the owner's alone.

**LANE B is also closed, on a negative (2026-07-26, cross-ISO).** neiso-67 §6
item 2 flagged the day-grain best-block `R < 0` cut as a possible
**replacement** for the guard's window-grain out-of-merit cut, in its existing
marginal lane (rule 19 `[R-ONE-MECH]` — never an addition). It is now validated
on every ISO with a published anchor — CAISO (CNOG revision-aware build only),
MISO, PJM, ERCOT, NEISO; **NYISO excluded, it has no anchor and none was
improvised** — across `--rcc-pctl {0.50, 0.75, 0.90, 0.99} × --horizon
{24, 48, 72}` × 2023–2025, **180 cells**, each carrying the full D1 standard
(vetoed-by-cut capacity vs the published series, kept-vs-vetoed separation,
proportion-matched placebo p95, no-split reference, monthly-`r`-is-the-robust-axis
caveat). Probe: `scripts/probes/_campd_daygrain_crossiso.py` (no LP solve; the
re-implemented incumbent reproduces each ISO's committed kept/layup split on
99.1–99.8 % of windows, and the ported machinery reproduces neiso-67's own
published band numbers). **Result: the candidate beats the incumbent in 82 of
180 cells — a coin flip — at a median gain of −0.0003, with |Δ| < 0.02 in
159/180; it is sign-stable across all three years in only 9 of 60
configurations, and it clears the placebo in 101/180 cells against the
incumbent's 105/180 (the 14 disagreements favour the incumbent 9–5).** Two
things explain it. First, the flagged observation's headline gap
(`+0.63…+0.79` vs `+0.08…+0.31`) compared the **two opposite sides of the
guard's own split** — an identified-layup series against the guard's KEPT
/ mechanical series; against the correct comparator, the guard's own VETOED
series, D1 already stood at +0.77 / +0.71 / +0.67 and the candidate measures
+0.70 / +0.74 / +0.53. Second, the two cuts **select the same windows**
(Jaccard 0.77–0.97, median 0.92): over 15,782 scored windows the day-grain cut
vetoes 127 the incumbent does not and the incumbent vetoes 144 the day-grain
cut does not, and on NEISO and CAISO the candidate's veto set is a strict
**subset** of the incumbent's in every year. **No guard change is proposed, so
no blast radius is reopened and no rule-22 leave-one-year-out obligation
arises**; the guard stands exactly as §8 adopted it. Record:
`results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md` (its §5
states what would falsify the null: a block-integral construction whose veto
set is *materially disjoint* from the window-grain cut's, which then clears D1
on the disjoint part).

## 10. CLOSED WITH CAUSE — owner ruling 2026-08-26; the cause stated, not implied

**The ruling (owner, program-director sitting 2026-08-26, card 6 — the O4/O5
decision card `docs/audit/AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4, option (A)
taken as recommended), verbatim:**

> Close the layup charter with cause; lift the freeze for the VALIDATION tier
> (2020-2022) for ISOs holding a `complete` marker. `final` stays empty and the
> locked test stays frozen. Restores the diagnostic touchpoint loop.

**What the cause is.** This closure takes §7's "Closed with cause" leg on §9's
*explained* branch — and one clause of §7's wording is met only in a weaker
form, which is recorded here rather than papered over. §7 asked for "the
extract is confirmed fit for purpose on evidence". What the four investigation
lanes actually established (§9) is that the extract is the best **buildable**
representation: the residual over-count is a definitional seam (published
series measure *unavailability*; the CEMS detector measures *non-operation*),
confirmed against a published instrument, and **not recoverable by any
discriminator the admissible inputs support** — the published-side re-measure
PASSED, the commitment-economics discriminator was NEGATIVE, the LP-side
closure was NEGATIVE, and the cross-ISO day-grain replacement was NEGATIVE.
"Best buildable" is a cause for closing a charter whose every further lane is
measured shut; it is not a finding that the input is unimpeachable.

**The detector question therefore REMAINS OPEN, and what that costs is stated
plainly:** the post-guard `CC_REGULAR` capacity-weighted outage share is
**14.2–36.7 %**, with **17 of 18 ISO-years above the ~10–15 % EFOR+planned
norm ceiling** (audit row O4 re-measurement, 2026-08-18,
`results/calibration/_audit_followup_o4_cc_envelope.json`). **Every keeper's
availability envelope inherits that seam.** It is carried explicitly — in the
freeze file's 2026-08-26 `history` entry, in audit row O4's resolution, and
here — as a documented definitional scope difference, so any future reader
sees the measured number and the four negative lanes together rather than a
silently accepted input. The lift is a decision to **proceed with a known-open
input question**, on the asymmetry the owner relied on in both prior narrow
lifts: validation years are iterable, re-spendable, model-selection-only
evidence, so spending one against an imperfect envelope costs nothing
irreversible and re-opens the diagnostic touchpoint loop (rule 22) that has
already surfaced two real input defects (neiso-85/86); locked-test years are
touch-once, and they stay frozen.

**Execution (2026-08-26 holdout-governance records lane; no LP, no solve, no
year spent):**

- `frontend/data/backcast/holdout-freeze.json` re-scoped — `active: true`,
  `scope.tiers = ["locked_test"]`, history appended (never rewritten), the
  original 2026-07-25 `reason` preserved verbatim.
- The scope is enforced by the single fail-closed reader
  `scripts/lib/holdout_policy.frozen_tiers` (an active freeze with no
  parseable scope covers every tier), consumed by
  `run_calibration_full.enforce_holdout_year_gate` — the choke point every
  solve path routes through.
- Verified behaviourally across all three rule-22 enforcement paths (the CLI
  year gate, `legitimacy_diagnostics.run_d6_quarantine`,
  `scripts/audit_keepers.py` H1), 55/55 invocations as required — including
  the one that matters: **2019 and H1-2026 refused for every one of the six
  ISOs, with and without `--holdout-authorized`**. Record:
  `docs/FINDING-holdout-governance-2026-08-26.md`.
- `calibration-complete.json`'s `final` block is untouched and still empty; no
  ISO's marker changed.

**What this closure does NOT do.** It does not resolve the detector question
(nothing further is buildable on the evidence — §9); it does not grant any
locked test (`final` stays empty; per the same sitting's card 7, any future
`final` grant is additionally preconditioned on the ISO's 2020–2022
touchpoints having been run and the loop having stopped surfacing repairs);
and it does not close the §5 blast-radius re-tune lanes, which continue in
their own ISO lanes on the corrected envelope.
