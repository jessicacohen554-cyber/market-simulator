# PRE-REGISTRATION — nyiso-175b: the fleet-wide tranche-attribution repair

**Session:** nyiso-175 (second charter; the first is discharged and merged —
`docs/FINDING-nyiso175-ct-deficit-two-objects-2026-09-02.md`).
**Keeper:** `2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}.
**Written and committed BEFORE the probe or any solve was run.** Six consecutive
sessions have honoured this; this is the seventh.

---

## 1. The object, as its predecessor handed it forward

nyiso-175 §4.4 / handed-forward item 1, and nyiso-174 §6 item 1 — **the same
defect family in two artifacts**: a per-plant aggregate assigned to one of a
mixed plant's classes by a *proxy* instead of by the units' own meters.

**(A) The tranche deriver.** `derive_thermal_tranches._fleet_nameplate_and_group`
attributes a plant's **facility-summed** CAMPD net to the group holding the most
**nameplate**. Measured wrong at three NYISO plants, **15.233 TWh** of measured
conduct over 2023–2025:

| plant | primary (nameplate) | actual carrier | margin | CAMPD TWh/yr |
|---|---|---|---|---|
| 2500 Ravenswood | `ST_GAS` 1,724.8 MW | `CC_REGULAR` 222.2 MW | 1,502.6 MW | 2.850 / 2.665 / 2.994 |
| 2493 East River | `ST_CHP` 309.5 MW | `CT_CHP` 306.0 MW | **3.5 MW (1.1 %)** | 2.134 / 2.259 / 2.189 |
| 2682 S A Carlson | `ST_GAS` 45.0 MW | `CT_PEAKER` 42.0 MW | 3.0 MW | 0.042 / 0.029 / 0.071 |

**(B) The outage extract.** `_resolve_unit_group`'s `fac_group` short-circuit
(last-writer-wins over the fleet iteration) writes East River's two EIA-860 `GT`
units into `campd-unit-outages-NYISO.csv` as `ST_CHP`. Two windows, both 2023.

**Zero DOF in both.** A crosswalk repair, not a re-derivation against a
residual, so rule 23 `[R-FROZEN-DERIVE]` is satisfied by citing the attribution
defect rather than a data change. The corrected per-unit construction already
exists and is tested: `scripts/lib/campd_measured_classes.corrected_unit_class`.

**Honest expected value, stated before measuring (nyiso-175 §4.5): the C3a
expectation is ~ZERO.** Both East River bins carry the same heat rate (7.4205)
and the same delivered gas, so moving energy between them changes no unit's
marginal cost and no marginal price. This is proposed on rule 1 `[R-STRUCT]`
grounds as a **C1 / representation repair**. It must never be sold as a C3a
lever, and a large favourable C3a move would be evidence of a *defect*, not of
success — see kill K5.

---

## 2. Rule 19 `[R-ONE-MECH]` — what already exists, checked before adding

`mixed_gas_routing` (miso-200, `ScenarioConfig`-gated, default **False**) already
skips the `fac_group` short-circuit at a facility carrying ≥2 gas bins. **Gate
K3 tests whether it already covers East River.** Reading the code it does not —
`_GAS_BIN_GROUPS` is `{CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}` and **excludes both
CT classes**, so East River's `{CT_CHP, ST_CHP}` intersects it at size 1 and
`_is_multi_gas_facility` returns False — but that is a *reading*, and K3 makes it
a *measurement*. If K3 shows the existing gate does reach the plant, this lane
stops and arms that gate instead of writing new logic.

---

## 3. PRE-SOLVE gates. Any FAIL stops the lane before an LP runs.

**K1 — the object must be the size its predecessor measured.** The corrected
per-unit attribution must move **≥ 4.0 TWh** of NYISO CAMPD energy over
2023–2025 onto a different `(plant_code, plant_group)` tranche row than the
nameplate rule assigns. *(Bar set at ~1/4 of the 15.233 TWh measured, so
ordinary construction differences cannot clear it.)* **FAIL ⇒ STOP:** the object
is smaller than §4.4 measured and does not justify a three-year re-solve.

**K2 — it must be a STRICT crosswalk repair.** At every NYISO plant carrying
exactly **one** thermal group, the corrected construction must reproduce the
current one **exactly** (zero changed rows, zero changed statistics). **FAIL ⇒
STOP and re-derive:** a repair that moves single-group plants is not a crosswalk
repair, it is a reclassification, and its blast radius is not what is claimed.

**K3 — the existing mechanism must provably not already cover it.** With
`mixed_gas_routing=True`, East River's units 1/2 must still resolve to a bin
other than `CT_CHP`. **FAIL ⇒ STOP the new-logic lane** and arm the existing
gate instead (rule 19).

**K4 — the repair must give the turbine bin a row it currently lacks.** East
River must gain a `CT_CHP` tranche row (it has none today) and Ravenswood's
`CC_REGULAR` must gain one. **FAIL ⇒ STOP:** the construction did not do the
thing the object is about.

---

## 4. POST-SOLVE kills, if and only if §3 passes and a solve is run

Scored on all three years in one bundle (rule 16), years sequential (rule 12).

**K5 — C3a-2025 must stay ~flat, and a BIG move in EITHER direction is a
FAIL.** Pre-registered expectation **|ΔC3a-2025| ≤ 1.0 pp**. A favourable move
larger than that is *not* a win: it would mean the repair changed price
formation, which the physics says it cannot (identical heat rate, identical
gas), and it must be diagnosed before any promotion. **This gate exists
specifically to stop this repair being retro-sold as a C3a lever.**

**K6 — the C1 signs must be right in all three years.** `CT_CHP` volume must
move **toward** its benchmark (+) and `ST_CHP` **toward** its benchmark (−).
Pre-registered sizes from nyiso-175 §4.5, single-basis: `CT_CHP`
**+0.378 / +0.965 / +0.402 TWh**, `ST_CHP` **−0.064 / −0.343 / −0.713 TWh**.
Tolerance ±50 % on magnitude; **sign is not negotiable**. A wrong sign in any
year ⇒ the construction is wrong: diagnose, do not promote.

**K7 — leave-one-year-out within 2023–2025 before any promotion.** In-sample
gain with held-out degradation is overfitting, not skill.

**K8 — rule 20 `[R-FORCED-BUDGET]` must not regress.** No merchant class ≥2 % of
ISO load may cross its forced-energy cap as a result of the repair.

### What this lane will NOT do, whatever the numbers say

* **Rule 1 `[R-STRUCT]`: a correct mechanism STAYS IN even if C3a does not
  move.** The repair is justified by the primary record, not by the residual.
* **Rule 14 `[R-ACCURATE]`: a WORSE backcast after an accurate input is a
  discovered bug elsewhere, never a reason to revert.** If C1 or C3a degrades,
  the finding records the degradation and opens the root-cause question; the
  accurate input stays.
* **No floor, no offer re-level, no markup, no haircut.** nyiso-170 §5 refused
  the offer-band re-level and nyiso-171 §2.5 showed the sign forbids a floor on
  the CHP side. If the result points at either, that is evidence the mechanism
  has not been found — not a licence to arm one.
* **No C3c lever.** C3c is supporting-tier and auto-ledgers under rubric v3.3.
* **2023–2025 only.** NYISO's `complete` marker was withdrawn 2026-08-30 and
  NYISO is absent from `final`; no marker is requested.

### Scope limit, declared in advance

The code repair is **ISO-agnostic**, but only **NYISO's** derived artifacts are
regenerated and re-solved in this session. Every other ISO's committed tranche
and outage CSVs are left byte-untouched; their lanes re-derive on their own
schedule. This keeps rule 25 `[R-ISO-SCOPE]` clean and keeps the blast radius
of a single session bounded.
