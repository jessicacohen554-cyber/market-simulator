# FINDING nyiso-140 — the always-on Long_Island ST_GAS floor has the right WINDOW and the wrong MEMBERSHIP: one economically laid-up plant (Port Jefferson) absorbs **72.6 %** of everything the floor forces, on **7.2 %** of the fleet's output

**Session nyiso-140, 2026-08-16.** Settles question 1 of
`FINDING-nyiso139b-zone-k-joint-lever-rescoped-2026-08-16.md` §6, and proposes the
K6 successor that question 2 asks for. **No solve spent, no mechanism written, no
`ScenarioConfig` field added.** Measured entirely from the floor's OWN source data
— the same CAMPD unit-level extract, guard-corrected outage extract and archived
zone TMAX that `scripts/data/derive_nyiso_st_reliability_floor.py` reads. No price
or volume residual, no metrics file and no solve output was consulted at any point
(rule 23 `[R-FROZEN-DERIVE]`; rule 1 `[R-STRUCT]`).

Reproducible: `.venv/bin/python scripts/probes/_nyiso140_li_st_floor_membership.py`.

---

## 1. THE OBJECT

The one live `Long_Island × ST_GAS` row of
`data/raw/reference/reliability_floor_coeffs_NYISO.csv`:

```
driver=tmax  threshold=-50.0 C  floor_pct=0.262  distribution=pro_rata
start_hour/end_hour: (none)     ramp_group: (none)
basis: "persistent 24h base: base_24h (when-available cool-day CF p25)"
```

A −50 °C `tmax` threshold is never not met, so the limb binds in **all 8,760
hours**; `pro_rata` floors **every unit** of the class in the zone at
`0.262 × pmax × availability[t]` (`model/interchange/core.py::_apply_frac`). The
two other LI ST_GAS limbs (the `LI_ST_ev` evening ramp knots) are disabled on the
keeper via `NYISO_PEAK_WINDOW_FLOORS_OFF`, and the `tmin` cold limb ships
`enabled=False` — so this row is the **sole** live floor on the class.

**Step 0 — the probe reproduces the frozen coefficients exactly**, so every gap
below is a basis difference, not a pipeline difference:

| coefficient | probe | CSV |
|---|---:|---:|
| `base_24h` (cool-day **daily-mean** fleet CF p25) | 0.2623 | 0.262 |
| `base_ev` (cool-day evening fleet CF p25) | 0.3502 | 0.35 |

## 2. THE WINDOW IS RIGHT — do not narrow it

Two of the three plants run a genuine persistent 24-hour baseline. Cool-day
(`tmax < 25 °C`) median when-available CF by hour block:

| plant | MW | h00-05 | h06-13 | h14-21 | h22-23 | P(CF=0) |
|---|---:|---:|---:|---:|---:|---:|
| E F Barrett | 372 | **0.254** | 0.409 | 0.541 | 0.330 | 0.051 |
| Northport | 1592 | **0.313** | 0.367 | 0.580 | 0.386 | 0.042 |
| Port Jefferson | 385 | **0.000** | 0.000 | 0.000 | 0.000 | **0.731** |

Barrett and Northport never approach zero in any block, overnight included, and
are at zero in only 4–5 % of cool hours. **The cable-islanded in-city steam
baseline is real and it is all-hours.** Rule 17 `[R-FLOOR-WINDOW]`'s window test
is satisfied for them: the driver (a physical must-run minimum on a committed
boiler serving a cable-islanded pocket) applies in every hour, and the measured
conduct confirms it. The floor forces them only **0.23 / 0.47 TWh over three
years** — 5.8 % and 4.4 % of their own observed output.

**Question 1 is therefore closed on its own terms: the always-on window is
correct, and no re-scoping to a peak window is warranted.** Narrowing it would be
rule 1 `[R-STRUCT]` backwards — removing a mechanism the evidence supports.

## 3. THE MEMBERSHIP IS WRONG — and it is where all the forcing lives

Port Jefferson (facility 2517, 385 MW) has **median CF exactly 0.000 in every
hour block of every year** and is at zero in 73 % of cool hours. Its model
availability is nonetheless ~100 % (0.945 / 1.000 / 1.000 across 2023–25),
because the 2026-07-26 guard fix (`6a8f285`) deliberately **un-booked economic
lay-up from the outage extract** — correctly, since lay-up is not a forced
outage. The `pro_rata` floor consequently holds a laid-up plant at 26.2 % of full
nameplate in all 8,760 hours:

| plant | observed TWh | floored TWh | **added TWh** | ×own output |
|---|---:|---:|---:|---:|
| E F Barrett | 4.018 | 2.219 | 0.234 | 0.55 |
| Northport | 10.785 | 5.994 | 0.471 | 0.56 |
| **Port Jefferson** | **1.151** | **2.604** | **1.867** | **2.26** |
| FLEET | 15.955 | | 2.573 | |

**Port Jefferson is 72.6 % of all the energy this floor adds above measured
conduct, while being 7.2 % of the fleet's observed output.** The floor manufactures
2.26× the plant's own annual generation, every year.

This is rule 17 `[R-FLOOR-WINDOW]` verbatim — *"a floor binding in hours its own
driver evidence says the class is offline is a bug by definition, whatever it does
to the residual."* The floor's stated basis is a **persistent 24 h baseline**;
Port Jefferson's own source evidence says it has none.

### 3.1 What Port Jefferson actually is: a temperature-conditional reserve unit

It is not dead — it is **U-shaped in temperature**, running on hot days and on
cold snaps and idling in mild weather:

| TMAX band °C | hours | P(on) | mean MW |
|---|---:|---:|---:|
| < 0 | 456 | 0.728 | 88.0 |
| 0–10 | 5,760 | 0.243 | 17.1 |
| 10–20 | 8,520 | 0.240 | 22.3 |
| 20–25 | 4,272 | 0.306 | 26.7 |
| 25–30 | 5,712 | 0.619 | 78.1 |
| ≥ 30 | 1,584 | **0.932** | **166.2** |

That hot-limb-plus-cold-limb response is precisely the driver the **ramp limbs**
(`LI_ST_ev`) and the `tmin` cold limb represent — **not** a persistent 24-hour
base. The unit is in the wrong limb, not merely over-floored.

### 3.2 The correction is membership-only and costs ~zero degrees of freedom

Re-deriving on the basis the floor is actually **applied** on (hourly, not
daily-mean) with the laid-up plant excluded lands almost exactly on the frozen
coefficient:

| basis | 3 plants (as frozen) | 2 plants (excl. 2517) |
|---|---:|---:|
| **hourly** all-24h p25 — *matches how the floor is applied* | 0.2011 | **0.2666** |
| daily-mean p25 — *the frozen basis* | 0.2623 | 0.3484 |

frozen `floor_pct` = **0.2620**.

Two basis errors were cancelling: the coefficient is a **daily-mean** statistic
used as an **hourly** floor (which inflates it), computed on a **fleet aggregate**
that includes a plant at zero (which deflates it). Fix both and the number barely
moves — **0.2666 vs 0.2620**. The correction is therefore a *membership* change
with the coefficient effectively unchanged, adding **no new free parameter** to
the DOF ledger (rule 21 `[R-DOF]`).

## 4. WHY THE GOVERNANCE DIAGNOSTICS DID NOT CATCH THIS

Both live checks pass, and both are structurally blind to it:

* **D-4 off-window binding is tautological for an always-on floor.** The keeper's
  row declares `window = h0-23`, so `offwindow_twh = 0.0` and
  `offwindow_share = 0.0` **by construction**, in all three years. A floor that
  declares "my window is every hour" can never fail an off-window test. Rule 17's
  substance — *does the driver evidence support binding in these hours?* — is not
  what D-4 measures.
* **D-2 is class-aggregate.** The rows read `class: ST_GAS` pooled ISO-wide
  (2.789 / 2.803 / 2.387 TWh forced, 20.5 / 22.1 / 15.6 % of class). A single
  plant carrying 73 % of the forcing is invisible at that grain, and C8's 30 % cap
  is not approached, so C8 PASSes.

Neither is wrong as written; both are measuring a coarser object than the defect.

## 5. PROPOSED K6 SUCCESSOR (question 2 — owner decision)

**The bias is real.** K6 kills an arm when *"any D-2 mechanism's forced share
rises"*. Forced share is `forced_twh / class_total_twh`, and an import-relief
lever moves **both** terms the wrong way by construction: relieving a transfer
bound displaces in-zone units out of merit (so more of them sit **at** their floor
rather than above it, raising `forced_twh`) while imports displace in-zone energy
(lowering `class_total_twh`). The share rises even when the class generates the
same or less. K6 cannot adjudicate any import-relief lever, which is what
nyiso-130 actually demonstrated.

**Proposal — mirror rule 20 `[R-FORCED-BUDGET]`'s own amended logic rather than
invent a new statistic.** Rule 20 already faced this question for C8 and resolved
it: a material class over its forced-share cap is *not* an automatic fail; it
escalates to a conditional pass on **provenance + shape**. Apply the same shape to
K6:

> **K6′** — a rise in a D-2 mechanism's forced share is **not itself a kill**. It
> escalates to provenance + shape, and fails only on a miss:
> **(a) provenance** — every binding mechanism still binds only inside its
> driver-justified window (D-4), and
> **(b) shape** — the class's D-1 diurnal profile still clears `profile_r` /
> `cv_ratio`.
> The forced-TWh change is reported at full magnitude either way, alongside the
> **energy-normalised** diagnostic
> `Δforced = forced_arm − forced_ctrl × (class_energy_arm / class_energy_ctrl)`,
> which strips the mechanical part of the move and is reported, not gated.

This reuses an adjudication pattern the owner has already approved, is scored
entirely from the committed `legitimacy_diagnostics.json` (scorer-only, no
re-solve, existing runs re-score in place), and requires **no zero-forcing twin** —
which rule 21's 2026-07-14 amendment retired and which must not return by the back
door.

**Rider, forced by §4 — K6′ leans on D-4 for provenance, and D-4 is vacuous for
`h0-23` floors.** Adopting K6′ without strengthening D-4 would rest the whole gate
on a check that cannot fail. Proposed minimal strengthening: for a floor whose
declared window is all hours, add a **per-unit conduct** row — a floored unit whose
own measured CF is ≈ 0 across the declared window fails provenance regardless of
the class aggregate. That is exactly the test that would have caught Port
Jefferson, and it generalises to every ISO's always-on limbs.

## 6. DISPOSITION — both questions answered by the owner, 2026-08-16

1. **Question 1 — CLOSED.** The always-on window is correct and stays. The
   defect is membership: an economically laid-up, temperature-conditional plant is
   inside a persistent-baseline floor. The fix is to exclude it (the
   `EXCLUDE_PLANTS` / `NYISO_ST_FLOOR_EXCLUDE_PLANTS` channel already exists in
   the derive script as an empty `frozenset`, but the engine's `_apply_frac` has
   no per-plant exclusion — so this is a `src/market_sim/` change, Opus/Fable only
   under rule 27 `[R-PUSH]`). The keeper runs `plant_level_fleet=True` +
   `use_campd_bins=True`, so Port Jefferson is its own LP rows and the exclusion
   is expressible.
2. **OWNER DECISION (Q1 sequencing) — STANDALONE ARM FIRST, then Zone-K.** The
   membership exclusion lands as its own control/arm pair on the keeper before the
   transfer lever is written. Rationale, per nyiso-139b §4: the transfer bound and
   this floor are **not one phenomenon**, so folding them into one bundle would
   confound a rule-17 bug fix with an untested lever. The Zone-K lever is then
   adjudicated against a **corrected** control.
3. **OWNER DECISION (Q2) — K6′ with the D-4 per-unit rider**, as proposed in §5
   including the rider. A forced-share rise escalates to provenance + shape rather
   than killing the arm; D-4 gains a per-unit conduct check so it is no longer
   vacuous for `h0-23` floors.
4. **The joint Zone-K arm is unblocked but deliberately deferred** behind the
   standalone membership arm, per decision (2).

**This finding does not license a residual-driven change.** The membership
correction is justified by the floor's own source evidence alone; if removing
1.87 TWh of manufactured LI steam energy opens a residual, that is a discovered
bug to root-cause under rule 14 `[R-ACCURATE]`, not a reason to keep the plant
floored.

## 7. THE A/B RESULT — all six kill gates clean, and the fit gets slightly WORSE

Solved in-session, `--year 2023 2024 2025` in one bundle each (rule 16), both
registered (rule 15):

* control `2026-08-16-nyiso-140-control` — the keeper recipe replayed at HEAD;
* arm `2026-08-16-nyiso-140-layup-exclusion` — the same recipe + the exclusion.

| gate | result |
|---|---|
| **K1** config isolation | **PASS** — exactly one differing field, `reliability_floor_plant_exclusions: False → True` |
| **K2** feasibility | **PASS** — slack and dump identically 0.0, both arms, all three years |
| **K3** liveness | **PASS** — the floor sheds **0.602 / 0.560 / 0.625 TWh** |
| **K4** scope | **PASS** — only the LI ST_GAS limb loses a row |
| **K5** gated-criterion regression | **PASS** — nothing goes PASS → FAIL |
| **K6′** provenance + shape | **does not fire** — both legs pass |

**K3 is the identification's own confirmation.** §3 predicted, from CAMPD conduct
alone and before any solve, that Port Jefferson's manufactured energy was
~0.62 TWh/yr. The LP shed 0.602 / 0.560 / 0.625. The object was sized correctly
from measured conduct, not fitted.

**C1/C2/C3a/C3b/C4/C8 all PASS on both sides; C3c is the same lone failure on
both.** Both runs read `NOT-YET` **only** because a fresh probe bundle carries no
`calibration_attestation.json`, so C6 is `UNATTESTED` — symmetric across the
comparison, and rule 22's C3c standing rule correctly refuses to reclassify
without a passing governance gate (guard (b)).

**The arm does not improve the fit, exactly as pre-registered.** §3's ex-ante
table said ST_GAS volume would improve in 2023 and worsen in 2024–25:

| year | actual | control | arm | control err | arm err |
|---|---:|---:|---:|---:|---:|
| 2023 | 8.704 | 11.383 | 10.967 | **+2.679** | **+2.263** |
| 2024 | 11.071 | 10.476 | 10.155 | −0.595 | −0.916 |
| 2025 | 16.003 | 12.625 | 12.266 | −3.379 | −3.737 |

Summed |error| 6.653 → 6.916 TWh. Mean system LMP firms slightly
(+0.21 / +0.18 / +0.40 $/MWh) as forced must-run energy is withdrawn.

**This is the rule 1 `[R-STRUCT]` case in its pure form, and the reason the run
is registered rather than buried.** The floor was holding a laid-up plant at
26.2 % of nameplate in all 8,760 hours; that is wrong whatever it does to the
residual. Under rule 14 `[R-ACCURATE]` the degradation is a **discovered bug**,
not a verdict on the correction: the manufactured 1.87 TWh was masking a real
downstate under-production (2025 ST_GAS was already −21 % *before* the fix). The
successor is that root cause — **not** re-flooring the laid-up plant.

**K6′'s first application, and it earned its keep.** The surviving
`nyiso_gas_commitment_bridge` share ROSE (+0.0045 / +0.0118 / +0.0051) while the
mechanism did strictly less work in absolute terms in the years its own energy
fell. Bare K6 — "any D-2 mechanism's forced share rises" — would have killed this
arm. K6′ correctly escalated to provenance + shape and cleared it.

**Standing caveat, stated because it weakens my own result.** K6′ leg (a) leans
on D-4, and §4 shows D-4 is *tautological* for an `h0-23` floor: both arms report
`offwindow_share = 0.000` **by construction**. So the provenance leg is currently
carried by a check that cannot fail, and the owner-adopted **D-4 per-unit conduct
rider is not yet implemented**. Until it is, K6′'s provenance leg should be read
as unproven rather than passed.

## 8. WHAT IS UNCHANGED

Keeper `2026-08-08-nyiso-133-cod-arm` is untouched and remains
`CALIBRATED-WITH-CAVEATS` with C3c the lone ledgered caveat. NYISO holds
`complete` (validation only), is absent from `final`, its frontier stays CLEARED,
and the holdout spend freeze is ACTIVE and untouched — this session solved
nothing and scored nothing. The NYISO RT interval convention (nyiso-139) is not
re-opened.
