# PRECOMMIT — nyiso-244: the `measured_offer_surface` NYISO design pass, and the five gates it must clear before a shard is spent

**Session** nyiso-244 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `95825f63`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025}. **UNCHANGED
at the time of writing.**
**Predecessor** `docs/RESULT-nyiso243-the-tail-is-not-an-availability-object-2026-09-20.md` §6,
which re-opened `measured_offer_surface` NYISO `G` → `U` and named the two blockers this
document gates.

**THIS FILE IS COMMITTED BEFORE ANY NUMBER BELOW IS COMPUTED.** Every threshold, every
pass/fail bar and every scope rule is fixed here, so no gate can be written to fit a result
(rule 1 `[R-STRUCT]`). The only measurements that precede it are a **descriptive** column
census of the P-27 corpus (which columns exist, and which are populated) and a read of the
keeper's own committed `run_config.json` — neither of which touches a gated statistic.

---

## 1. THE OBJECT, AND WHY IT IS NOT AN AVAILABILITY OBJECT

nyiso-242 and nyiso-243 between them closed the availability route on two independent
instruments (CAMPD operation; P-27 declared availability). What survives is an **offer-level**
object, measured:

| | 2022 winter, 70 missed hours | ordinary winter hours |
|---|---:|---:|
| measured MW offered above $300 (DAM) | **4,986** | 1,953 |
| model MW idle **below** the $300 gate | **4,715.7** | — |

and the measured quantity rises monotonically with a **day-ahead-observable** driver
(3,833 → 4,561 → 9,328 → 10,183 MW across DA > $100/150/200/300). That conditioning is what
makes an offer surface rule-13 `[R-MEASURED]` admissible rather than a fitted level.

**The reachability logic that decides everything below** (nyiso-242 phase 0D): the energy
dual is the marginal tranche's offer, so a price above $300 requires that **every tranche
offering below $300 is already fully dispatched**. It follows that a mechanism can only reach
this object if it raises the offers **of the idle sub-gate capacity itself**. Raising a
tranche that is already above the margin changes no dual. §3 G3 is that test, and it is the
gate most likely to refuse.

---

## 2. WHAT IS BEING DESIGNED

The repo already carries a shared conditional-offer-surface kernel —
`data/fleet/offer_surfaces.py::_conditional_surface_markup`, wired per ISO through
`_CONDITIONAL_SURFACE_SPECS` (ERCOT, NEISO, PJM, CAISO). It is a **P1-only additive markup**
that reprices a class's **peak-rung** rows from the height the fleet built them at
(`offer_curve_by_group[cls]["peak"]`) to a **measured** heat-rate multiplier read out of a
frozen condition-binned JSON, keyed on the hour's within-year **net-load percentile** bin. A
loose bin never lowers an offer (ratio clamped ≥ 1), and the repriced offer is capped below
VOLL.

A NYISO member of that family would be `nyiso_offer_surface_conditional` +
`nyiso_offer_surface_binned_path` / `_netload_pcts` / `_min_bin` / `_price_cap_frac`, with a
`scripts/data/derive_nyiso_offer_surface.py` producing the frozen JSON from **NYISO MIS P-27**
(`data/raw/nyiso-bid-data`, intaken by nyiso-243).

**Nothing in this design is transferred from another ISO (rule 25 `[R-ISO-SCOPE]`).** What is
reused is the *method* — a shared kernel and the NEISO derive's published-physics cohort
selector — never a parameter. Every number the NYISO surface carries is measured on NYISO's
own bid corpus against NYISO's own fleet.

---

## 3. THE FIVE GATES. ALL FIVE BIND, AND ANY FAILURE REFUSES THE MECHANISM BEFORE A SHARD.

### G1 — rule 19 `[R-ONE-MECH]`: enumerate and reconcile, BEFORE building

The owed enumeration is of every **armed** mechanism that writes a NYISO peak-rung offer.
`gas_offer_net_revenue_margin` is `K` and armed in the keeper, and it is already a measured
markup over marginal cost.

**G1 PASSES** iff, for every class the surface would price, all three hold:

* **(a)** the enumeration is complete — every armed mechanism touching that class's peak rung
  is named, from the keeper's own `run_config.json`, not from memory;
* **(b)** the surface's increment is shown to be **disjoint** from each enumerated
  mechanism's. The claim to be tested numerically on the keeper's own arrays is that
  `gas_offer_net_revenue_margin` prices the **registered** markup `(m − phys)` at the
  fuel-invariant anchor while the surface prices the **measured scarcity increment**
  `(M − m)` at the hour's fuel — two disjoint increments of one curve, no MW priced twice.
  The test is a decomposition with **max |overlap| = 0** by construction, reported with the
  realised $/MWh of each increment;
* **(c)** no other armed mechanism writes the same rung. `tranche_startup_amortization`,
  `nyiso_ct_peaker_committed_measured`, the reliability floors and the gas commitment bridge
  are each checked against the peak rung explicitly.

**G1 FAILS** if any enumerated mechanism prices the same increment. The remedy is then a
**replacement** form (the surface sets the rung's height outright) or refusal — never a
stack.

*Recorded in advance so it cannot be claimed afterwards as a discovery: the repo's own ERCOT
keeper (`ercot248_two_config_keeper`) arms `gas_offer_net_revenue_margin` AND
`ercot_offer_surface_conditional` together. That is a precedent, not an argument; G1 is
decided on the NYISO decomposition above, and a precedent cannot pass it.*

### G2 — the masking blocker: what does the surface key on?

P-27 is **masked** — no class, no fuel, no zone, no unit. The surface kernel needs a
**per-class** ladder, so a cohort attribution is required, and per
`RESULT-nyiso243` §6 that attribution **is itself a modelling choice that must be validated
before use, never assumed.**

**The selector is fixed here and is a PUBLISHED NYISO PRODUCT DEFINITION, not a fitted
signature.** A resource that submits a **10-Minute Non-Synchronized Reserve** offer is, by
NYISO's own product definition, able to go from **offline to full output within 10 minutes**.
That is the quick-start population the model's `CT_PEAKER` class represents, and it is the
same *kind* of identification `derive_neiso_offer_surface.py` uses on ISO-NE's equally-masked
corpus (`Claim 30 ≥ 0.9 × EcoMax` — "the fast-start segment is selected by PHYSICS, not fuel
labels"). **Selector: a masked gen whose rows carry a 10-Min Non-Synch reserve offer in ≥ 50 %
of its DAM offered hours.** The 50 % is a presence-not-accident bar fixed here, never swept.

**G2 PASSES** iff the selected cohort reproduces the model's own fleet census on **all three**
pre-registered statistics. The model side is the keeper's own fleet arrays, internal rows
only (`NYISO_external_*` and `NYISO_DR_*` excluded — the nyiso-243 §3 scope trap):

* **V1 — scope.** `|Σ P-27 max UOL − model internal installed| / model internal ≤ 0.15`.
  Establishes that the two corpora describe the same fleet before any cut is taken.
* **V2 — cohort size.** Cohort `Σ max UOL` within **±25 %** of the model's CT-family
  (`CT_PEAKER + CT_INTERMEDIATE + CT_CHP`) nameplate, **and** cohort unit count within
  **±30 %** of the model's CT-family plant count.
* **V3 — fingerprint.** Sort both capacity vectors descending, truncate to the shorter, and
  require the **median relative gap ≤ 0.25**. This is the discriminating test: a cohort
  contaminated by combined-cycle units (300–1,000 MW) cannot match a CT fleet's size
  distribution however well its total happens to land.

**G2 FAILS** if any of V1/V2/V3 misses. **A fleet-wide, class-free surface is NOT substituted
on a G2 failure** — posting one level across every gas rung is the collapsed-heterogeneity
failure mode the flat `ercot_ct_offer_surface` was rejected for (calibration-log 2026-07-06),
and rule 1 `[R-STRUCT]` refuses a structurally worse mechanism whatever it does to the
residual.

### G3 — REACH. The gate most likely to refuse, and it is measured against the object.

Per §1, only the offers of the **idle sub-gate capacity** can move the dual. The kernel
prices **peak rungs only**.

**G3 PASSES** iff, in the 2022 winter missed cluster (70 hours, 4,715.7 MW idle below $300),
the capacity the surface could actually reprice — **peak rungs of the G2-validated classes,
idle, offered below $300** — is **≥ 50 %** of that 4,715.7 MW.

**G3 FAILS** below 50 %. The precedent for refusing on reach is nyiso-242 §1.3, which refused
`cc_winter_capability_basis` at 263.6 MW against the same 4,716 MW object (5.6 %). A failure
is reported with its full decomposition — idle MW by class and by rung family — because that
decomposition tells a successor whether the defect is the *scope* (peak-only) or the
*class*, and those have different successors.

### G4 — rule 13 `[R-MEASURED]` admissibility, re-measured on EVERY year the keeper carries

nyiso-243 measured the conditioning driver on **2022 and 2025 only**. A surface armed across
{2022, 2023, 2024, 2025} owes the same evidence on all four.

**G4 PASSES** iff the measured DAM MW offered above $300 rises **monotonically** across the
DA ladder $100 → $150 → $200 → $300 in **at least 3 of the 4 years**. A driver that only
conditions in the year holding the events is a coincidence, not a forward-reproducible
construction.

### G5 — rule 1 `[R-STRUCT]` / rule 21 `[R-DOF]`: nothing is selected on a residual

Fixed here, before any derive is run, and **never swept**:

* bin edges = **0.80 / 0.90 / 0.97** — the repo's standing precedent, identical for ERCOT,
  NEISO, PJM and CAISO. Not chosen for NYISO, and not varied.
* rungs = **5**, equal-capacity quantiles — the NEISO precedent.
* `min_bin` = **0**, `price_cap_frac` = **0.95** — the shared defaults.
* the ladder is the **measured distribution**; no level, offset, haircut or multiplier is
  chosen, tuned or swept against any gate or criterion.
* derive window = **every year the keeper carries** (2022–2025), one surface, not a per-year
  vintage.

**G5 FAILS** the moment any of the above is varied to move a result. Under rule 21
`[R-DOF]` the surface contributes **zero free parameters** if it clears: every number in the
frozen JSON is a measured quantile of NYISO's own submitted curves, and the wiring constants
are the shared precedent values above.

---

## 4. WHAT HAPPENS ON EACH OUTCOME

* **All five PASS** → build `scripts/data/derive_nyiso_offer_surface.py`, wire
  `nyiso_offer_surface_conditional` into `_CONDITIONAL_SURFACE_SPECS` with its own frozen
  JSON and its own default-off flag, add the matrix row cells (rule 28 `[R-MECH-MATRIX]`
  duty c), commit, pin the SHA, and launch **four single-year shards** (2022, 2023, 2024,
  2025 — rule 36 `[R-YEAR-ISOLATION]` (a); rule 35 `[R-PROMOTE]` (c): the incoming keeper
  must cover the ISO's whole year union, which is {2022, 2023, 2024, 2025}). Each shard
  pushes its FULL bundle including `dispatch/<year>_P1.parquet` (rule 34
  `[R-SHARD-PROMOTABLE]` (a)). The parent composes, scores and registers.
* **Any FAILS** → **no shard is launched** (rule 34 `[R-SHARD-PROMOTABLE]`: a solve that
  cannot back a promotion is not spent). The cell records the refusal with its citation and
  its re-open condition, and the RESULT doc carries every number, including the ones that
  favoured the mechanism, at full magnitude.

**The keeper is not touched by this document.** NYISO reads **CALIBRATED** on its ISO tier
(2023–2025, rule 30 `[R-TOUCHPOINT-FOLD]` (c)) with C3c the lone ledgered caveat, and nothing
here proposes reverting it to recover the full-span headline (rule 1).

---

## 5. GOVERNANCE

* **Rule 32 `[R-SHARD]` (a)** — zero LP in this container. The only model-side call is a
  `fleet_only` rebuild of the keeper's own recipe, which enters no LP.
* **Rule 28 `[R-MECH-MATRIX]`** — the target cell is `measured_offer_surface` NYISO, `U` since
  nyiso-243. Duty (a) discharged: the DO-NOT-REDO set was read, and the availability family
  (`temp_dependent_derate` `G`, `cc_winter_capability_basis` `G`, `unit_outage_short_windows`
  `I`, the ST_GAS blanket) is **not** re-opened by this session. Duty (b) is discharged in the
  RESULT whichever way the gates fall; duty (c) applies only if a new `ScenarioConfig` field
  lands.
* **Rule 25 `[R-ISO-SCOPE]`** — no ISO's parameter is carried. The kernel and the
  cohort-selection *method* are shared code; every NYISO value is measured on NYISO's corpus.
* **Rules 21 / 24** — §3 G5 fixes the wiring constants at the shared precedent values and
  forbids sweeping them; the ladder carries no free parameter.
* **Rule 31 `[R-RETAIN]`** — nothing is deleted. If shards are launched, their bundles are
  pushed (rule 34 (a)) and the promotion question is put to the owner explicitly before this
  session ends.
* **Rule 27 `[R-PUSH]`** — any edit to a ≥300-line source file is a local `Edit` and the
  pushed blob is verified.

**One correction owed to the record, and it is recorded here rather than buried.**
`nyiso243_offered_availability.py` Leg 3 reports "explicit AS offers" from the columns
`10 Min Non-Synch MW`, `10 Min Spin MW`, `30 Min Non-Synch MW`, `30 Min Spin MW`,
`Regulation MW`. Measured on the January 2022 archive, **the four reserve MW columns are
100 % null** in both DAM and HAM — only `Regulation MW` is populated (8.7 % of DAM rows), so
Leg 3's 866 / 794 MW are **regulation only**, not the whole reserve holding. Leg 3 was
explicitly a diagnostic and never a gate, so no nyiso-243 verdict moves; the caveat it already
carried ("headroom above dispatch is reserve-capable without a separate AS offer, so this
column understates reserve holding") is simply larger than stated. The reserve **Cost**
columns *are* populated (15–22 % of DAM rows), which is what G2's selector reads — presence of
an offer, not its MW.
