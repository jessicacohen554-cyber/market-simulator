# PREREG — nyiso-178: is the NYISO `ST_GAS` over-booking an OFFER-side object, and if so what shape?

**Session:** nyiso-178, NYISO backcast-calibration track, 2026-09-02.
**Keeper (control):** `2026-09-02-nyiso-177-vintage-matched`, bundle
`results/calibration/nyiso177_vintage_B1p`. Determination **NOT-YET**, target
grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}. It reproduces
BIT-IDENTICALLY at HEAD (nyiso-177 §10.3 G-CONTROL: 0 of 52,560 hourly zonal
prices differ in all three years), so **no control leg is solved.**

**Committed BEFORE any measurement this session performs**, together with the
probe that runs the gates. Nothing below is written after seeing its own result.

---

## 0. The object, and the brief's claim this session is testing rather than assuming

nyiso-177 §7.1 sized, for the first time, an object it did not repair: the NYISO
`ST_GAS` outage overlay books **0.534 / 0.560 / 0.501** of the bin-capacity-year
as mechanical outage **in the keeper**, against a documented EFOR+planned norm of
**0.10–0.15** — 3.5–5×. It handed the object forward with a **stated type**:

> *"The overlay is carrying economic idling the offer curves should be
> producing. That is the NYISO steam lane's next object, and it is an
> **offer-side question, not an availability-side one**."*

**This session does not inherit that type. It tests it**, because the type is
the whole disposition: an availability-side object and an offer-side object have
disjoint lever sets, and arming the wrong one is a rule-1 `[R-STRUCT]` error that
the residual would happily reward.

## 0.1 DISCLOSURE — everything measured before this file was written

Honesty about the pre-registration boundary. Before writing this file I read
committed bytes only, and computed exactly one quantity that is not already
published in an artifact: **the model-vs-actual `ST_GAS` energy by year**, from
the keeper's own `hourly/class_hourly_<year>.parquet` (P1) against
`frontend/data/backcast/bench/NYISO/<year>.json.gz` `classFull`. It is the
reason this session's gates are shaped around a **year signature** rather than a
level:

| year | model TWh | actual TWh | delta |
|---|---|---|---|
| 2023 | 11.999 | 8.141 | **+3.858** |
| 2024 | 9.799 | 9.913 | −0.115 |
| 2025 | 10.014 | 13.712 | **−3.698** |

**The model's `ST_GAS` is FLAT (12.0 → 9.8 → 10.0) while the market's CLIMBS
(8.1 → 9.9 → 13.7).** The C1 failure is the 2023 end of a **response** defect,
not a standalone level error. Also read, and named here so no gate below can be
accused of having been reverse-engineered from them: the keeper's
`run_config.json` (offer bands, tranche flags, floor flags), its
`legitimacy_diagnostics.json` D-2 rows (`reliability_floor` 2.360 / 2.638 / 2.291
TWh, `nyiso_gas_commitment_bridge` 0.114 / 0.162 / 0.166 TWh), the committed
`thermal_tranches-perunitmerit-NYISO.csv` `ST_GAS` rows (10 plants, 8,857.4 MW
nameplate, `committed_pct` 6.5–65.1, `peaking_pct` NaN ⇒ class default 15),
`_DEFAULT_TRANCHE_PCT_BY_GROUP["ST_GAS"] = (0.0, 30.0, 15.0)`, and the NYISO
mechanism-matrix shard. **No quantity in any gate below has been computed.**

---

## 1. Gates

All four are decided by `scripts/probes/nyiso178_offer_side_idling.py`, committed
with this file, **zero solves**, from committed artifacts plus the keeper's own
sidecars. Every gate states both outcomes.

### G1 — IS THE AVAILABILITY ENVELOPE BINDING? (the type test)

The nyiso-173 S3 instrument, re-used on `ST_GAS`. Rebuild the keeper's own hourly
`ST_GAS` availability envelope — Σ over `ST_GAS` bins of `capacity_mw ×
unit_outage_derate_factors` under the keeper's exact config — and compare it hour
by hour to the keeper's `ST_GAS` P1 dispatch.

* **G1 ⇒ OFFER-SIDE** iff the model sits at its own `ST_GAS` envelope (within
  1 % of it) in **< 1 %** of hours in **every** year.
* **G1 ⇒ AVAILABILITY-SIDE** iff it does so in **≥ 5 %** of hours in **any**
  year.
* **G1 ⇒ MIXED** in between; both halves are then reported at full strength and
  neither is suppressed.

**If G1 ⇒ AVAILABILITY-SIDE the brief's stated type is CONTRADICTED**, and this
session reports the contradiction rather than the type it was handed (stop
condition S2). Reported alongside, ungated: the headroom distribution, and the
year in which the envelope binds hardest.

### G2 — WHY DOES THE ARMED MERIT-ORDER GUARD REMOVE ALMOST NO NYISO STEAM?

`campd_outage_merit_order_guard` is **keeper-armed** and exists precisely to take
economically-idle windows out of the mechanical-outage envelope, yet
`booked_share` moves **0.536 → 0.534 / 0.560 → 0.560 / 0.501 → 0.501**. Something
exempts NYISO steam from a guard built for exactly this. Attribute the
`ST_GAS` window-hours the guard **KEPT** across the three fail-safe exits its own
code defines (`MeritOrderPanel.is_economic_layup`, `outage_detect.py:754`):
(i) the unit is **unidentified** in the panel (no measured heat rate, cogen
`steamLoad`, or dropped fuel); (ii) the span is **unpriceable** (no hour with
both a finite unit SRMC and a finite RCC); (iii) the span IS priced and its
`out_of_merit_share` falls **below `MERIT_OOM_FRAC`**.

* **G2 DISCHARGES** iff **≥ 80 %** of the kept `ST_GAS` window-hours attribute to
  a **single** one of (i)/(ii)/(iii).
* **G2 FAILS** otherwise, and the exemption is reported as **diffuse** — which
  is itself the finding, and forecloses a single-cause repair.

No detector constant is touched either way (S1). `MERIT_OOM_FRAC` /
`MERIT_RCC_PCTL` are **read, never swept**.

### G3 — IS THE DEFECT THE OFFER'S SHAPE, OR ITS LEVEL?

The nyiso-169b instrument, re-used on `ST_GAS`. Rank the year's hours by the
keeper's own load-weighted zonal price and compare the model's `ST_GAS` output
against the measured fleet's CAMPD gross, **within price bands**, per year.

* **G3 ⇒ SHAPE** iff, in **every** year, the model's share of its own `ST_GAS`
  energy falling in the **bottom half** of the price distribution exceeds the
  measured fleet's by **≥ 2×**, **and** the model's **top-decile** share is at or
  below the measured fleet's. That is a class running as baseload where the
  market runs it as a peaker: a **duty-role** defect, repairable by an offer
  SHAPE identified from measured conduct.
* **G3 ⇒ LEVEL** iff the model's excess is concentrated in the **top** of the
  price distribution, or is **uniform** across bands (no band's model/measured
  ratio departs from the annual ratio by more than 25 %).
* **G3 ⇒ NEITHER** if it satisfies no branch; reported as such.

**G3 ⇒ LEVEL forecloses this session's arm** (S3): an offer-level change with no
measured level behind it is a value tuned to a residual — rule 21 `[R-DOF]` — and
nyiso-172 already refused the one class-scoped level scalar
(`gas_st_startup_cost`) on this class two independent ways.

### G4 — RULE 19 `[R-ONE-MECH]` ENUMERATION (a reporting duty with a bar)

Enumerate **every armed mechanism** that can put an `ST_GAS` MW on the bar in the
keeper — floors (`reliability_floor`, `nyiso_gas_commitment_bridge`), the tranche
split (`committed_pct` / class `pct_peaking` / econ residual), and the offer
levels that price each band — and attribute the keeper's `ST_GAS` energy across
them, per year.

* **G4 DISCHARGES** iff the enumeration accounts for **≥ 95 %** of the class
  energy with **no** unattributed remainder above 5 %.
* **G4 FAILS** otherwise, and the unattributed remainder is named as an open
  channel — which would itself block any new mechanism under rule 19.

---

## 2. Stop conditions — binding, and each one can stop this session

* **S1 — no fitted values.** No parameter is identified against any residual. If
  an instrument is built, every scalar in it is measured from CAMPD / LBMP and
  regenerates for a forward vintage (rules 13 `[R-MEASURED]`, 21 `[R-DOF]`,
  23 `[R-FROZEN-DERIVE]`). No detector constant, offer band or hr-mult is swept.
* **S2 — G1 ⇒ AVAILABILITY-SIDE stops the offer lane.** No offer-side arm is
  built or solved this session; the object is re-typed against the brief and
  handed forward.
* **S3 — G3 ⇒ LEVEL (or NEITHER) stops the arm.** Phase 0 is the deliverable and
  the successor is specified, not built.
* **S4 — G4 FAILS stops the arm.** A new mechanism cannot be stacked on an
  unexplained remainder of an old one (rule 19).
* **S5 — closed lines stay closed.** `gas_st_startup_cost` is NOT armed
  (nyiso-172 DO-NOT-REDO). `campd_per_unit_attribution` and
  `campd_outage_merit_order_guard` are NOT re-tested and NOT reverted (rule 14).
  The unguarded availability basis and `--no-fullstop-override` are NOT re-derived
  as instruments. **No C3c lever is opened** (brief). **C3a-2025 is not opened** —
  it is owner-court (`DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending),
  and any C3a movement this session produces is reported with its own magnitude,
  sign and named mechanism, never banked (the standing R6/K5 clause, carried
  verbatim from nyiso-175b → -176 → -177).
* **S6 — loosening availability is refused ex ante.** The brief's own guardrail:
  the two errors OFFSET, so relaxing the envelope alone makes `ST_GAS` volume
  WORSE. No availability-loosening arm is proposed regardless of what G1 says.
* **S7 — holdout.** Every year read, solved, scored or registered is
  **2023 / 2024 / 2025**. NYISO is absent from both `complete` and `final`; **no
  marker is requested**; the holdout spend freeze is untouched (rule 22).
* **S8 — scope.** NYISO artifacts only. Every other ISO's tranche and outage CSVs
  stay byte-untouched and only the NYISO matrix shard is edited (rule 25).
* **S9 — rule 15/16.** Any solve is ONE invocation, `--year 2023 2024 2025`, one
  bundle, years sequential, and is registered on the backcast dashboard **whatever
  it scores**, in this session.

---

## 3. THE ARM — pre-specified, and it runs ONLY if G1 ⇒ OFFER-SIDE **and** G3 ⇒ SHAPE **and** G4 DISCHARGES

`st_gas_duty_curve` — the `ST_GAS` sibling of the **adjudicated keeper**
`chp_layup_duty_curve` (nyiso-149), **disjoint from it by class scope** so the two
can never both price one bin (rule 19). Specified here in full so no degree of
freedom can be chosen after seeing a score:

* **Membership:** every `ST_GAS` bin the panel can identify. No cohort threshold,
  no separator, no hand list — the whole class, so there is no membership DOF.
* **Shape:** the measured **price-conditional on-share × loading-when-on × HSL**,
  by own-model-zone RT LBMP quantile band, measured **conditional on
  envelope-live hours** from the same frozen `-perunitmerit-` extract the keeper
  reads, so the availability envelope and the offer never double-count one
  mothball spell (the nyiso-149 §phase-0 guarantee, carried verbatim).
* **Level:** the class curve's **EXISTING** band multipliers. **Zero new price
  constants.** The remainder is WITHHELD from energy and reserves.
* **Wiring:** the load-bearing override is `assembly.py::bins_to_fleet`, not
  `fleet_to_bins` — **seam lesson #4 of this class**, paid twice by nyiso-146b and
  nyiso-148 and caught pre-scoring by nyiso-149. A MW contract, not a pct one.
* **Gate:** `ScenarioConfig.st_gas_duty_curve`, GATED **default off**, registered
  in `_CACHE_KEY_OPTIONAL_FIELDS` and the default-string registry in the same
  commit so it reaches `run_config.json` (rule 24), with its matrix row and a
  cell line in every shard in the same PR (rule 28c).

**Arm gates, fixed here:**

* **A1 — single delta.** The arm's config differs from the keeper's by exactly
  one field, verified by diff, nothing riding along.
* **A2 — ANTI-INERT.** LP-entry `ST_GAS` composition must change by **> 0.01 MW**
  against the control. A byte-identical arm is a **plumbing failure**, disclosed
  and registered as such before any corrected solve (nyiso-146b / -148 / -149
  precedent).
* **A3 — GRADED conduct.** The class must track the metered climb: model
  `ST_GAS` must move **toward** actual in **2023 and 2025 both** (|delta| falls in
  each), i.e. the arm must not buy 2023 by deepening 2025. **This is the gate the
  arm is most likely to fail**, and it is stated in that direction deliberately.
* **A4 — no new forcing.** Zero new D-4 rows; C8 does not regress.
* **A5 — no load-bearing degrade.** No C1/C2/C3a/C3b/C4 cell moves PASS → FAIL.

**A rejected arm is registered and its cell recorded `R`, exactly as nyiso-146b,
-148, -150 and -177's own probe leg were.** The arm is not promoted by this
session on its own authority if it is strictly worse than the keeper; that
disposition is the owner's (the nyiso-155 / -157 / -159 / -177 standing formula).

---

## 4. Explicitly NOT scoped, and why

* **The missing rung** (nyiso-177 §7.2: a guard-alone-on-incumbent-routing leg,
  which would satisfy promotion-bar leg (a) for the already-promoted keeper).
  Cheap and real, but it is **ladder bookkeeping for a settled disposition**,
  not this session's chartered object; taking it would spend the session's one
  solve budget on a question whose answer changes no keeper. Re-handed forward,
  unchanged, with the resolver note (`campd_attribution_selectors` forces
  `merit_guard` False without `per_unit` by design — the rung needs that gate
  relaxed, which is an API change, not a flag).
* **`mustrun_layup_window_mask`** (NYISO `U`; its matched
  `campd-unit-outages-layup-perunitmerit-NYISO.csv` companion exists but
  `outages.unit_layup_csv_for_iso` resolves only the unsuffixed name). G2 reads
  that companion as **evidence**; whether the mask is worth arming is a separate
  question this session does not answer, and no resolver is extended for it here.
* **C3a-2025** (owner-court, S5) and **C3c** (brief).

---

# 5. AMENDMENT — committed with the original, BEFORE the probe is run and before ANY gate quantity exists

**Status at amendment: nothing has been measured.** No probe has executed; no
G1/G2/G3/G4 number exists in any form. This amendment is driven purely by
re-reading §1 against the code, and it changes a gate's **CONSTRUCTION** because
that construction is defective on its face — never a threshold in response to a
result. (The nyiso-177 §6 precedent, applied one step earlier in the session.)

## 5.1 G4's bar is VACUOUS as written, and is replaced by G4′

**The defect, disclosed before it could be exploited.** G4 asks that the
enumeration "account for ≥ 95 % of the class energy". The only attribution the
committed artifacts support is `{reliability_floor-forced, bridge-forced,
economic residual}` — and *economic residual* is defined as the remainder, so the
three sum to **100 % by construction, for any model, always**. The bar cannot
fail. It measures arithmetic, not enumeration. Worse, per-band economic energy is
**not measurable at all** from the committed sidecars: `class_hourly` carries a
class aggregate, and per-unit/per-tranche model dispatch is not in any keeper
artifact (the standing nyiso-172 §2.5 / nyiso-173 instrument limit).

**G4′ REPLACES G4, and asks the question rule 19 `[R-ONE-MECH]` actually poses:**
is there an armed mechanism that can put an `ST_GAS` MW on the bar which is
**NOT** accounted for in the keeper's own committed D-2 attribution?

* Enumerate, from the keeper's `run_config.json`, every armed
  mechanism in a **fixed, pre-declared candidate list** of `ST_GAS`-capable
  forcing/shaping channels (below), and cross it against the `ST_GAS` rows of the
  keeper's committed `legitimacy_diagnostics.json` D-2.
* **G4′ DISCHARGES** iff **every** armed candidate either (a) carries an
  `ST_GAS` D-2 row, or (b) is shown inert for `ST_GAS` from committed bytes
  (wrong class scope, wrong ISO, or a null/absent artifact).
* **G4′ FAILS** iff any armed candidate can force `ST_GAS` and appears in
  neither — an **unattributed forcing channel**, which under rule 19 blocks a new
  mechanism until it is reconciled.

**The candidate list, fixed here before the cross-check runs** (a channel armed
but absent from this list is itself reported as a miss of this list, not
silently dropped): `reliability_floor`, `reliability_floor_plant_exclusions`,
`nyiso_gas_commitment_bridge` (+ its `st_min_load_frac` / `st_min_run_hours` /
`min_run` / `state_floor_min_run` / `online_hours` / `startup` legs),
`st_gas_mustrun_per_plant`, `st_gas_mustrun_p25_level`,
`st_gas_mustrun_p25_measured_level`, `st_gas_mustrun_oom_level`,
`st_gas_intermediate_split`, `mustrun_online_frac_per_year`,
`mustrun_plant_exclusions`, `mustrun_layup_window_mask`,
`nyiso_incity_commitment_obligation`, `chp_steam_following`,
`chp_layup_duty_curve`, `must_run_cf`, `commitment_enabled` / legacy P2,
`gas_st_netload_drag`, `historic_outage_overlay`,
`_DEFAULT_TRANCHE_PCT_BY_GROUP["ST_GAS"]` must-run share.

**The forced/economic split is still REPORTED** (it is the useful part of G4),
explicitly as a **report line, not a gate**.

## 5.2 G1's envelope reconstruction, and the bound it is gated on

Stated before measurement so the choice cannot be made to suit a verdict. The
`ST_GAS` envelope is rebuilt with the engine's own loader
(`outages.unit_outage_derate_factors` at the keeper's exact basis —
`per_unit_crosswalk=True, merit_order_guard=True`) against
`outages._iso_plant_capacity`, the **nyiso-173b instrument, unchanged**. Two
bounds are computed and **both are reported**:

* `env_raw = Σ cap × derate` — omits the statistical WEFOR, so it is an **UPPER**
  bound on the LP's true ceiling;
* `env_net = Σ cap × max(derate − WEFOR_BY_GROUP["ST_GAS"], 0)` — the additive
  form the availability builder actually uses (`fleet/arrays.py:742`,
  `availability = 1 − wefor − derate`), with the flat 0.12 class WEFOR.

**G1 is gated on `env_net`, the TIGHTER bound**, because that is the branch that
makes the brief's preferred answer (OFFER-SIDE) *harder* to reach: a tighter
envelope binds more often. If the two bounds disagree on the verdict, **G1 is
recorded as MIXED** and both are reported. Seasonal-WEFOR and any temperature
derate are **not** reconstructed; the armed availability config is enumerated and
reported so the omission is visible rather than assumed away.

## 5.3 §5.2's envelope reconstruction is WRONG ON THE CODE, and is replaced — still before any measurement

**Found by reading `fleet/arrays.py`, not by running anything.** No probe has
executed; §5.2 was written from `arrays.py:742` (`availability = 1 − wefor −
derate`) alone, and that line is only the FIRST of two layers. The unit-outage
overlay is applied at `arrays.py:1085–1098`, whose own comment is explicit:

> *"Multiplies the statistical availability already set above."*

So the LP's `ST_GAS` availability is **`(1 − WEFOR(age) − DERATE(age) − maint) ×
ufac`** — a PRODUCT, not a difference. §5.2's additive `env_net` would have
overstated the envelope by roughly the statistical layer, and would have made the
OFFER-SIDE branch of G1 far easier to reach than it should be. **The error would
have biased G1 toward the brief's preferred answer**, which is exactly why it is
corrected before the probe runs rather than after its number was seen.

**G1 is gated on `env_stat` and reports three bounds:**

* `env_overlay = Σ cap × ufac` — the overlay layer alone (§5.2's `env_raw`;
  the loosest bound, kept only so the two amendments are comparable);
* `env_stat  = Σ cap × (1 − WEFOR(age) − DERATE(age)) × ufac` — **THE GATED
  BOUND**, the composed envelope the LP actually carries, with
  `THERMAL_AVAILABILITY["ST_GAS"] = (0.06, 0.21, 0.003, 30, 0.04, 0.002, 30)`
  evaluated at each bin's own EIA-860 `online_year` age, exactly as
  `_thermal_outage` does;
* `env_stat_summer` — the same with the summer/shoulder WEFOR redistribution
  (`SUMMER_WEFOR_SHARE = 0.30`) applied, reported so the seasonal omission is
  visible.

**If `env_overlay` and `env_stat` disagree on the verdict, G1 is MIXED** and both
are reported — the §5.2 rule, carried over unchanged.

## 5.4 G5 — a NEW REPORTING DUTY the code reading forces, and it can fail

Rule 19 `[R-ONE-MECH]` is a gate on **mechanisms per phenomenon**, and §5.3 shows
`ST_GAS` unavailability is derived by **two stacked mechanisms** — an
age-escalated statistical NERC-GADS `WEFOR`+`DERATE`, and the measured CAMPD
window overlay — **multiplied**. Both model the same physical phenomenon (a unit
being unable to run). This session did not set out to test that and does not
propose a repair to it, but it cannot honestly measure an envelope and not report
its composition.

* **G5 REPORTS** the composed `ST_GAS` envelope decomposed into its statistical
  and measured layers, per year, with each bin's age, `WEFOR(age)`,
  `DERATE(age)` and mean `ufac`, and states whether the statistical layer is
  RELIEVED anywhere the measured overlay covers (`wefor_residual`,
  `gas_st_wefor_base_override`, `wefor_residual_groups`).
* **G5 FLAGS A RULE-19 STACK** iff both layers are armed for `ST_GAS` and
  **neither** relief field is set — i.e. the two are composed with no
  reconciliation.
* **G5 IS CLEAN** otherwise.

**G5 is a REPORT, not a lever.** Stop condition **S6 is unchanged and still
binds**: no availability-loosening arm is proposed this session, whatever G5
says, and the finding will state the direction honestly (relieving the stack
raises `ST_GAS`, which helps 2025 and hurts 2023). Two further guardrails, fixed
here: **`THERMAL_AVAILABILITY` is READ, never edited or swept** (rule 23), and
**`gas_st_wefor_base_override` is NOT set** — nyiso-173 already recorded this
stack as live for CC and declined to pull it, and a value chosen here would be a
value chosen against a known residual (rule 21).
