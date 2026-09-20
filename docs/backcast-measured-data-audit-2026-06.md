# Backcast measured-data audit — compliance with the "no pinning to actuals" rule

**Date:** 2026-06-17
**Rule audited:** claude.md Non-Negotiable Rule — *"Measured data is allowed
only as a reproducible physical/market input, never as the answer — no pinning
the backcast to actuals."*
**Subject:** the current ERCOT keeper **run 124**
(`results/calibration/run124_storage_as_keeper`) and the full set of
measured-data overlays still present in the code path.
**Method:** code reads of `data/outages.py`, `data/renewables.py`,
`results/scarcity.py`, `config/scenarios.py`, the `derive_ct_deployment.py` /
`derive_reliability_deployment.py` overlays; plus the keeper's resolved
`run_config.json`. Builds on the prior whole-backcast review
`docs/ercot-backcast-audit-2026-06.md` (run 115b), re-checked against the
current keeper. Diagnosis only — no parameter changed.

---

## The admissibility test

A measured-data input is **allowed** (even in backcast mode) when it is grounded
in physics or market design **and** passes:

> *Could this same quantity be produced for a forward year from forward drivers,
> and would it respond to changed conditions?*

If yes, it is an **input** (like an outage, a fuel price, an emission rate, an AS
reservation). If instead it is a measured **outcome** fed back to drive the
residual to zero — observed generation, observed LMP, or an input rescaled so the
model's *output* lands on the actuals — it is **forbidden** in a keeper, because
it has no forward analogue: the dispatch being validated stops being the dispatch
being forecast.

---

## Headline: the current keeper is compliant

The three mechanisms the 2026-06-15 audit flagged as feeding the answer in are all
**OFF** in run 124 (verified in `run_config.json`):

| Mechanism | Test | run 124 |
|---|---|---|
| `ct_deployment_overlay` — floors each peaker to its **observed CEMS net output** in out-of-merit hours | **FAIL** (measured outcome, no forward analogue) | **OFF** ✓ |
| `reliability_deployment_overlay` — floors pocket CC/coal/ST to **observed CEMS net** in congestion hours | **FAIL** (same) | **OFF** ✓ |
| `ordc_reliability_deployment_mw` — flat non-physical MW offset **tuned to the 2023 price residual** | **FAIL** (residual-fitted adder) | **DELETED 2026-07-04** (rule 26 — the field no longer parses) ✓ |

These remain in the codebase as **default-off diagnostic probes**, gated to
backcast mode and no-op in forecast (no artifact ⇒ no-op). That placement is
exactly what the rule permits — *exist as labelled probes, never as keepers.* The
risk is governance, not a current violation: runs 115b/118/122/123 **did** enable
them, so the temptation to switch them back on for a headline number is live. They
must not be re-enabled in a keeper or quoted as forecast skill.

---

## Reliability-floor rebuild — measured-data status (2026-06-30)

The **temperature-driven reliability-floor rebuild** (Phase 3/4, merged
2026-06-30) replaced the five legacy per-ISO injectors and the old windowed
`ReliabilityFloorSpec` with a single CSV-seeded per-(zone, class, driver) engine.
The following measured-data probes and crutches are affected:

| Mechanism | Status after rebuild | Compliance |
|---|---|---|
| `ct_mustrun_per_plant` (EIA-923 per-plant must-run floor) | **Demoted to default-off diagnostic probe.** All six reliability-floor rebuild keepers have `ct_mustrun_per_plant=False`. | ✓ PASS — no forward analogue (measured per-plant commitment pinned to a specific year's EIA-923 filing) |
| `ct_deployment_overlay` (CEMS per-plant deployment floor) | **Demoted to default-off diagnostic probe.** All six rebuild keepers have `ct_deployment_overlay=False`. | ✓ PASS — measured outcome, same as above |
| p97-CF ceiling in old `ReliabilityFloorSpec` (`cap` field) | **Removed entirely.** The new `ReliabilityFloorSpec` has no `cap` field; `floor_pct = commit_frac × min_stable_pct` is a structural commitment share × physical min-stable level, not a measured-CF ceiling. | ✓ PASS — the ceiling was a measured outcome (p97 of CAMPD CF) with no forward analogue |

**Confirmation:** all six reliability-floor rebuild bundles (ERCOT, CAISO,
PJM, MISO, NYISO, NEISO) have `reliability_floor=True` and
`ct_mustrun_per_plant=False`. No keeper enables an outcome-pinned floor.
The reliability-floor coefficients (`reliability_floor_coeffs_<ISO>.csv`)
are derived from CAMPD CF-vs-temperature regressions with a ρ/n enable
gate — temperature→commitment coefficients that regenerate for a forward
year and respond to changed weather. They are **never** tuned to a
price/volume residual.

---

## Allowed inputs in run 124 (pass the test — keep)

| Input | Why it passes |
|---|---|
| `historic_outage_overlay=True`, `outage_source="historic"` | Unit outage = physical availability event; reproducible window-detection on any year's CAMPD; forward analogue is the statistical/historically-derived maintenance profile. The **canonical allowed** case (the user's own example). |
| `coal_drop_pof=True` | Bookkeeping to avoid double-counting the statistical POF against the historic overlay — not a fit device. |
| `coal_plant_monthly_pricing=True` (F923 delivered fuel) | A real **cost input**; forward analogue is the forecast gas/coal price path. Responds to conditions. |
| Per-plant CEMS emission **rates** (bundle `campd.parquet`) | A physical plant **parameter** (lb/MMBtu), not an outcome; forward analogue is the fuel-class default. |
| `storage_as_commitment=True` (measured up-AS power reservation) | A **market-design commitment** (AS-held power cannot also arbitrage energy); adopted "for accuracy not fit"; forward analogue is the AS co-optimization / reservation logic. Caps the *physical* peak, does not pin energy to actuals. |
| Per-plant CAMPD `Plant_Avg_HR`, CF-P5 min-stable-load floors | Physical plant parameters (heat rate, min load), not outcomes. |

`renewable_cf_adjustment=1.0` and no per-plant/per-year CF override are set — good
(a per-plant-year CF override pinned to realized utilization would **fail** the
test; none is in use).

---

## The HSL rescale — RESOLVED (2026-06-17)

**Was:** `data/renewables.py` `_HSL_RESCALE_TWH` was a module-level hardcode
`(ERCOT, 2023, wind)=110.0` / `(ERCOT, 2023, solar)=32.0`, applied
unconditionally whenever the 2023 ERCOT HSL profile was built. Its two parts had
different verdicts: raising the raw HSL up to *at least* the EIA-930 delivered
total was a legitimate physical-floor fix (the UMass-derived series sums *below*
delivered, which is impossible for a potential), **but** the targets were
deliberately set *above* delivered "to offset the dispatch's economic
re-curtailment, so the *delivered* output lands on the actuals" — tuning an
**input** so the model's **output** matched a measured actual, the exact
anti-pattern the rule forbids (no forward analogue; the `+offset` was sized to
*this model's* curtailment behaviour).

**Now:** the model-output target is gone. `hsl_potential_mw()` consumes each HSL
parquet as-is, with **one real-data coverage reconciliation**: when a source's
own delivered (its `GEN` column) materially undercounts the EIA-930 system
delivered total (a partial-footprint dataset), the series is scaled UP to the
EIA-930 level *preserving the dataset's own measured curtailment ratio*
(`delivered/HSL`). That reconciles two real datasets — the parquet's hourly shape
+ curtailment ratio, the EIA-930 level — and references nothing about model
output. The model then curtails endogenously and the modeled-vs-reported
curtailment gap is a **diagnostic**, not a fit target (Rule #11). For 2023 this
now yields wind **113.28 TWh** / solar **34.01 TWh** at the measured 4.67% / 6.29%
curtailment ratios, replacing the back-solved 110 / 32.

The reconciliation is a **no-op for full-footprint published data** (whose
delivered already matches EIA-930 within 2%). `build_ercot_hsl.py` now prefers the
authoritative ERCOT **NP4-732/737** published HSL for *any* year (drop the reports
into `np6/`), falling back to the UMass reconstruction for 2023 only when no
published upload exists. **Action for the user:** supplying the published
2023/2024/2025 NP6 HSL retires the reconciliation entirely — 2024/2025 currently
have *no* HSL parquet at all and fall back to EIA-930-delivered-as-CF (no
curtailment modelling), so the published uploads also turn on endogenous
curtailment for those years.

---

## Verdict

Run 124 **complies** with the new rule on the load-bearing items: the CEMS
deployment floors and the fitted ORDC scarcity offset — the mechanisms that
previously "fed the answer in" — are off, and the remaining measured inputs
(outages, F923 fuel, CEMS rates, the storage-AS reservation) all pass the
forward-analogue test. After the 2026-06-17 HSL fix, the remaining standing
exposure is **governance**: the CEMS deployment overlays still exist in code and
were keeper-enabled as recently as runs 118/122/123. Keep them default-off and
out of keepers; if used, label them probes and never quote their fit as skill.
(The HSL output-target rescale — previously the one live measured-outcome-driven
input — has been replaced with a real-data coverage reconciliation; see above.)

## ORDC scarcity pricing made formulaic — RESOLVED (2026-06-17)

The fitted scarcity offset (`ordc_reliability_deployment_mw`, ~2,500 MW tuned to
the 2023 LMP residual) is **DELETED outright (2026-07-04; it was first deprecated
out of the default reserve path, then re-swept after deprecation — rule 26)**,
replaced by a market-design-grounded **on-line/off-line reserve split**
(`results.scarcity.reserve_headroom` / `ordc_adder`): only responsive capacity
backs the ORDC curve — a cold slow-start unit the perfect-foresight LP left idle
is not real-time reserve, and the published RTOLCAP (online) / RTOFFCAP
(quick-start non-spin) two-tier LOLP structure is now evaluated honestly instead
of the RTOFFCAP = 0 shortcut.

Two candidate "formulaic" levers were tested and **rejected** on run 124:
- **AS-plan netting** (measured or a published-standard formula): overshoots
  catastrophically (2023 MAE 32 → 814, fires 3,300+ h vs 181 actual). ERCOT's
  RTOLCAP already counts online AS-held capacity as reserve, so netting it
  double-counts — confirming the prior `ordc_as_plan_mw` rejection.
- A forecast AS-requirement formula was built then removed (its only purpose was
  the rejected netting).

The split alone **reproduces scarcity incidence** (online reserve < the 6,500 MW
floor in 178 h ≈ 181 actual >$200 h) and improves 2023 monthly LMP MAE
**32.3 → 27.7** (2024/25 neutral) with **no fitted constant**. It does not fully
close the 2023 magnitude gap, and per Rule #1 that residual is **not** chased
with an offset: its honest cause is the bang-bang energy-only LP never
part-loading units to carry spinning reserve. The real next step is **AS/reserve
co-optimization in the LP** (the documented B5a structural gap), not a knob. See
`docs/ordc-overlay.md`.

The strongest single confirmation remains the still-unrun **statistical-mode
backcast** (every overlay off — `forecast-validation-plan.md` Phase 3): it would
convert "the keeper passes the rule" from a config inspection into a measured
overlay-vs-statistical gap.

## CHP grid-delivered benchmark de-circularized + measured export floor (2026-07-02)

Two paired changes (the C1 CC_REGULAR/CC_CHP caveat work):

1. **Bench-side BTM was circular — FIXED.** The grid-delivered CHP "actual"
   (`classFull` = EIA-923 class total − `btm.parquet`) previously sized the
   BTM as `(923 class total − the model's own grid dispatch).clip(0)`
   (`run_calibration_full._btm_frame` →
   `results.emissions.compute_must_run_emissions` data-driven mode). Whenever
   the model under-dispatched a CHP class, the "actual" collapsed onto the
   model — C1 could never fail for CHP classes (a vacuous pass, the reverse of
   the no-pinning rule: the *benchmark* was pinned to the model), and the
   attribution varied ~19 TWh between solves of identical code+data
   (unversioned solve-container state). The BTM hold-out is now measured-input
   only: per-(plant, class) EIA-923 net generation × the measured host share
   (`chp_btm_pct` sector shares / per-plant overrides — the identical share
   the LP hold-out removes). Two rebuilds are byte-identical from committed
   code + `data/raw`.

2. **`chp_export_floor_measured` — new backcast overlay (ADMISSIBLE).** The
   CHP steam-following grid floor (`pmin_cf × (1 − btm share)`) now rides at
   the plant's measured EIA-923 class CF for the solved year instead of the
   pooled CAMPD p2 minimum. Test: host steam demand is a physical input
   exogenous to the power market — a topping-cycle cogen's power train follows
   its host, not the LMP (measured ERCOT CC_CHP grid delivery ≈ 32 TWh/yr vs
   ~26 modeled under p2 floors). The same floor regenerates for a forward year
   from sector-level host demand × the EIA-860 CHP designation, and it
   responds to changed host conditions. The LP keeps upward freedom (scarcity
   dispatch above the floor) and outage windows still relax it (min_gen is
   clipped to pmax × availability). Boundary note: this floors the unit at its
   host-driven *operating level*, which is stronger than a never-below
   minimum — it is admissible only because a steam-following export is
   genuinely price-inelastic, and it must never be extended to merchant
   classes, where the same construction would be pinning dispatch to observed
   generation. Off by default; forecast mode always uses the persistent
   `chp_pmin_cf` floors.

---

## `ercot_gtc_limits_measured` — measured hourly GTC export limits (2026-07-02)

New backcast overlay (ADMISSIBLE, rule #14's explicit case): the export
capability of the transfer links that carry ERCOT's published Generic
Transmission Constraints follows the **measured hourly GTC limit series**
(NP6-86 "SCED Shadow Prices and Binding Transmission Constraints" →
`scripts/data/curate_gtc_limits.py` → `gtc-limits` clean datatype →
`market_sim.data.gtc.ercot_gtc_ttc_hourly`) instead of the single static
`ttc_mw`. Test: a GTC limit is ERCOT's published voltage/WSCR **stability
transfer limit** — a physical/market input that regenerates for any year
ERCOT publishes and responds to changed grid conditions (new synchronous
units or transmission raise it). West/Panhandle renewable curtailment then
emerges **endogenously** wherever the measured limits bottle the pockets;
the ISO-reported HSL curtailment totals (the [3e] validation target) are
never read by the overlay. Mechanism check: with the `gtc-limits` partition
absent (or the crosswalk emptied) the dispatch reverts byte-identically to
the static ratings.

Reconstruction formula (all measured): an hour where the constraint was in
SCED's active set takes the time-average of its per-interval limits, with
non-enforced intervals standing in at the constraint's measured year-max
envelope; hours never enforced ride the envelope. The import direction keeps
the static thermal rating (`ttc_import` — a GTC caps exports, not imports).

Crosswalk / reconciliation boundary (rule #14's misalignment exception,
documented in `constants.ERCOT_GTC_LINK_MAP`): the single aggregate WESTEX
GTC is one published boundary the reduced network splits across two links
(8:3, the static ratio); PNHNDL and NE_LOB map 1:1; **N_TO_H is deliberately
not applied** (one of several parallel 345 kV paths the reduction collapses —
using it literally would understate the interface); intra-zone GTCs (VALEXP,
EASTEX, TRDWEL, MCCAMY) are unrepresentable and ignored. Per-year gating:
the overlay applies only when the year has BOTH the `gtc-limits` partition
and measured HSL renewable potential — without real potential
(EIA-930-delivered-as-CF years) a binding export cap would double-curtail
wind below what actually flowed, so those years keep the static limits with
a logged warning.

Data status: the NP6-86 monthly archives (`*SCEDBTCNP686*.zip`,
2023–2025) are **not present in this environment** and cannot be fetched
anonymously (7-day MIS retention; the Data Portal requires a sign-in) — see
the `DATA NEEDED` note in `data/raw/iso-specific-transmission/README.md`.
The full pipeline is validated end-to-end on the live 7-day MIS window
(10 GTCs recovered, PNHNDL/WESTEX/NE_LOB limits consistent with the 2023-24
derived statics).
## CAISO storage-AS awards + demand-clock realignment — two new measured inputs (2026-07-11)

Two CAISO backcast inputs added by the caiso-74/75 probe session, both scored
against the admissibility test:

| input | flag | verdict |
|---|---|---|
| **Battery AS-award reservation** — the measured hourly CAISO battery (LESR) AS awards (`storage-as-awards` clean datatype from the CAISO Daily Energy Storage Report quarterly xlsx; DA means 1,010/1,484/1,652 MW 2023-25, ~1 % off the DMM-published anchors) reserved out of the battery power cap, with SOC floored at the tariff 30-min sustain of the spin/non-spin award (`CAISO_AS_SUSTAIN_DURATION_H`). | `caiso_storage_as_reservation` (default **off**) | **PASSES the test** (market-design commitment, regenerates forward via the endogenous co-opt path — the CAISO analogue of ERCOT's `storage_as_commitment` row above) but measured **ex-ante inert** on the zone-aggregate fleet (caiso-74: LP battery discharge peaks 3.7–6 GW below nameplate, the 0.7–2.8 GW derate never binds). Not in any keeper; kept available with the intake. |
| **2023 demand-clock realignment** — the EIA-930 CISO `Demand` column rides +1 h late vs the extract's own astronomy-verified generation frame for local dates before 2023-11-01 (best-lag −1 at r 0.984–0.997 vs the extract's balance identity; OASIS SLD corroborates at 0.9953); the window is pulled forward 1 h onto the wall-true frame. | `caiso_demand_clock_realign` (default **off**; ON in the caiso-75 line) | **PASSES** — a rule-14 reconciled-real-data *clock* correction derived only from the source series' internal identity: annual energy conserved to +0.1 MW, no level rescale, no residual in the derivation. Frozen against residuals (rule 23), guarded by `scripts/validate_caiso_demand_clock.py` (fails loudly if EIA restates the series, so it cannot silently double-shift). Forward story by construction: 2024+ needs no correction. |

Adjudication record: `results/calibration/FINDING-caiso75-demand-clock-2026-07-11.md`
(the demand BASIS stays EIA-930 `Demand` — corroborated at 0.9994 by the OASIS
SLD TAC actual; the "supply-implied load" alternative was REJECTED as a
zero-daily-mean 930 supply-side artifact, so no outcome series entered the
demand input). Inert-probe record:
`results/calibration/FINDING-caiso74-storage-as-reservation-2026-07-11.md`.

---

## `NYISO_INTERFACE_TTC_BY_MONTH` / `_BY_YEAR` — measured Central-East DAM transfer capability (2026-07-30)

**Declared backcast overlay** (nyiso-104). This entry closes a registry gap
rather than admitting a new input: the overlay has been live in every NYISO
backcast since the Central-East tables landed, but it carried **no D-5 row**,
so the parity gate was blind to it. It is now
`nyiso_central_east_measured_ttc` in
`scripts/legitimacy_diagnostics.py::D5_REGISTRY`, `declared=True`,
`mode="backcast_only"`, ISO-scoped to NYISO.

**What it is.** The month-mean of NYISO's posted MIS `ATC_TTC` `TTC (DAM)`
series for the `CENT EAST` interface (`scripts/data/derive_nyiso_central_east_ttc.py`),
applied to the `Upstate_West -> Capital_Hudson` link — per-hour by calendar
month (`_BY_MONTH`, via `pipeline/ttc.py::apply_iso_monthly_ttc`) over an
annual-mean scalar (`_BY_YEAR`, via `apply_iso_year_ttc`). Both helpers are
called only from `scripts/run_calibration.py`; `runner.py` never references
them.

**Why it is an overlay and not a forward mechanism.** The charter for this
session posed the fork explicitly — a measured series with no forward analogue
(declare it) versus a published seasonal rating that regenerates forward (wire
it into the forecast, as nyiso-102 did for the three downstate mechanisms).
It resolves to the former, on a falsifiable test of the source data rather
than by analogy:

| test | result | reading |
|---|---|---|
| Level-normalized monthly shape, correlated across the two years sharing the post-AC-Transmission topology (2024 vs 2025) | Pearson r = **+0.21**, Spearman ρ = +0.16, dihedral-null one-sided p = 0.25 | A rating recomputed the same way each year would repeat at r ≈ 0.9+ on an unchanged network. The true calendar alignment is no better than a rotated or reversed one. |
| Deepest-derate month, same two years | **Sep (2024) → Apr (2025)** | The derate is not anchored to a season. |
| The prior provenance comment's "recurring late-summer/shoulder derate" | Aug–Nov derate **+7.9 % (2024)** but **+0.0 % (2025)** | **Falsified**; the comment is corrected in `constants.py`. |
| Variance decomposition over all 36 monthly means | 82.0 % between-year (level/step); 6.8 % is the post-upgrade within-year shape (sd 162/199 MW on a 2,850 MW link) | The disputed component is both non-reproducible *and* small. |

The within-year signal is that year's own **approved transmission-outage
schedule** — a physical availability event on the network, the same
admissibility family as `historic_outage_overlay` on a unit, and admissible in
a backcast for the same reason. What it does not have is a forward analogue at
the *month* level, so pushing these numbers into a forecast year would import
one historical year's outage schedule into every forward year.

**The forecast loses nothing by this.** The *level* — the component that is
forward-reproducible — already has its forward channel: the
transmission-expansion registry (`data/raw/transmission-expansion/nyiso.csv`,
`in_service_year` + ΔTTC, wired into `runner.py`) over the static 2,850 MW in
`iso_configs._nyiso_config`, which is itself this series' measured
post-upgrade annual mean. The registry's own Smart Path Connect row already
records that reasoning ("the model's Central-East 2,850 MW static is the
measured 2024-25 DAM mean"). So the correct forward treatment of a
Central-East re-rate is a registry row with a published instrument and an
in-service date — not this table.

Adjudication record: `docs/FINDING-nyiso104-central-east-ttc-classification-2026-07-30.md`;
probe `scripts/probes/nyiso104_central_east_ttc_classification.py`.

**Data status:** `data/raw/NYISO/ATC_TTC.zip` is **not present in this
environment** (see the `DATA NEEDED` note in `data/raw/NYISO/README.md`); the
committed tables are the derived artifact. Re-fetch from NYISO's MIS before
re-running the derive script.

---

## `caiso_ra_mustoffer` — market design with a forecast **wiring gap**, declared (2026-09-20)

**Declared parity difference** (caiso-294). Like the `nyiso_central_east_measured_ttc`
entry above, this closes a **registry gap rather than admitting a new input** — but the
class is different and the distinction is the whole point of the entry: this is **not a
measured overlay at all**. It is a market-design commitment mechanism that is
**mode-independent by intent**, and the only reason D-5 sees a backcast/forecast
difference is that the forecast entry point never calls it.

**What D-5 was reporting.** `D5_REGISTRY`'s `caiso_ra_mustoffer` row declares
`mode="both"` with `caiso_ra_mustoffer_min_gen` required in both entry scripts. Measured
at this writing: the symbol appears **twice in `scripts/run_calibration.py` and zero times
in `src/market_sim/runner.py`**, so `active_b=True`, `active_f=False`, and with
`declared=False` the row read `FAIL` — the **single** D-5 failure on the CAISO keeper
`2026-09-20-caiso-290-leftedge`. The gate was reporting a true fact about the code and
scoring it as an undeclared overlay, which it is not.

**Why it is admissible in a backcast under rule 13 `[R-MEASURED]`.** The bridge floors a
gas CC/CT that the model's **own base-cost P0 run pattern** shows idling across a midday
gap shorter than its **physical** minimum-down time (or, under `caiso_ra_startup_bridge`,
uneconomic to cycle by the standard restart inequality priced at the model's **own** P0
dual). Both operands — the P0 pattern and `CC_COMMITMENT_PARAMS` min-down — are produced
by the model from forward drivers and respond to changed conditions. **No measured
outcome enters**: nothing is pinned to observed CEMS generation, no offset is tuned to a
residual, and the P1 LP dispatches freely above the floor. It passes the admissibility
test at the top of this document in both modes; it simply is not *reachable* in one of
them.

**What the declaration costs, stated rather than hidden.** While the gap stands, a CAISO
**forecast** year carries no RA must-offer commitment while every CAISO **backcast** year
does — so the two modes do not run the same mechanism set, and a CAISO forecast's belly
commitment is structurally thinner than the backcast that validated it. The declaration
records that difference and sanctions D-5's treatment of it; it does **not** claim the
difference is harmless. This is the same posture the `reliability_floor` row above already
carries ("a wiring gap in the forecast entry is reported but sanctioned by the
declaration").

**The named closure, not absorbed.** Wire `caiso_ra_mustoffer_min_gen` into `runner.py`'s
P0→P1 seam (`docs/audit-wiring-iso-gaps/prompt-pack/w2-caiso-ra-p2.md`; fix plan
`docs/audit-wiring-iso-gaps/fix-plan.md`). That is a **forecast-path model change** — it
arms an extra `min_gen` bridge in every CAISO forecast and hindcast year and moves every
CAISO forecast result — so it needs its own PRECOMMIT, its own gates and an owner ruling.
It is deliberately **not** bundled into this declaration, which is docs + one registry
boolean and changes no solve.

Registry row: `scripts/legitimacy_diagnostics.py::D5_REGISTRY`, `declared=True`,
`mode="both"`. Record: `docs/RESULT-caiso294-*.md`.
