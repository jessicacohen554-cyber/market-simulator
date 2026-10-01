# PREREG nyiso-144 — arm the gas commitment bridge's laid-up plant membership correction

**Written and committed BEFORE either arm is solved.** Session nyiso-144.
Keeper at HEAD: `2026-08-18-nyiso-143-n11tsl-arm`. Holdout spend freeze
**ACTIVE** — 2023, 2024, 2025 only, one bundle each arm (rules 16 / 22), years
sequential within a run (rule 12).

---

## 1. THE OBJECT

`reliability_floor_plant_exclusions` (nyiso-140, keeper) excludes economically
laid-up plants from the always-on Long_Island ST_GAS reliability floor. **It
does not reach `nyiso_gas_commitment_bridge`**, which floors the same class. So
nyiso-140 repaired one MECHANISM rather than the plant, and the bridge kept
holding laid-up stations at minimum stable load. Rule 19 `[R-ONE-MECH]`'s
"enumerate what already floors the same class and replace or reconcile", one
mechanism later.

This arms the bridge's own half: `nyiso_gas_bridge_plant_exclusions`
(`ScenarioConfig`, default off; CLI `--nyiso-gas-bridge-plant-exclusions`).

**ONE config field differs between the arms.** Nothing else changes.

## 2. THE IDENTIFICATION — and why it is not circular

A plant is in economic **lay-up** iff its median CAMPD plant gross load is
**zero in every (year, 4-hour block) cell** of the pooled 2023–2025 window —
the nyiso-140 criterion verbatim. Derivation:
`scripts/data/derive_campd_bridge_layup_exclusions.py`; artifact
`data/raw/_processed-legacy/campd_bridge_layup_exclusions_NYISO.csv` (+
`_population.csv` with the full 30-plant population and its cell counts).

**Why the per-cell quantifier, not a pooled median.** Measured on NYISO's own
bridge population, a pooled median of zero *also* catches ordinary CYCLERS —
Saranac `P(on) = 0.426`, Port Jefferson `P(on) = 0.375` — which are exactly the
population a commitment bridge exists to hold together. The per-cell test
separates them cleanly: the qualifying set stops at **18/18** zero cells and the
nearest non-qualifier sits at **16/18**.

**ZERO new free parameters** (rule 21 `[R-DOF]`): no scalar is introduced, the
bridge's measured min-load fractions and run horizons are untouched, and the
test reads only the meter. `n_residual` unchanged.

**The test is computed BLIND to the mechanism.** It never reads which plants the
bridge floors, nor any D-4 verdict. That independence is what makes the
agreement evidence: on the committed keeper diagnostics it selects **7 of the
bridge's 8 D-4 unit-conduct FAILURES** without being shown any of them.

**Qualifying set (12 plants):** 2480 Danskammer, 2625 Bowline, 2682 S A Carlson,
8006 Roseton, 10190 Castleton, 10620 Carthage, 10621 Syracuse, 50744 Sterling,
54034 Rensselaer Cogen, 54592 Massena, 54593 Batavia, 56188 Pinelawn.

**TWO PLANTS ARE DELIBERATELY NOT EXCLUDED, and both are pre-registered as such
so neither can be added after seeing a residual:**

* **7314** is the eighth D-4 FAIL (2025: 0.0774 TWh, 2,235 binding h, **77.1 %**
  of them metered at zero) and does **not** qualify — it is a cycler the model's
  own P0 over-runs. Its forcing is an offer/economics defect; excluding it here
  would bury that error inside a membership list instead of fixing it (rule 14
  `[R-ACCURATE]`, rule 1 `[R-STRUCT]`). It is a **named successor object**, not
  part of this arm.
* **2517 Port Jefferson** is excluded from the reliability FLOOR (whose
  always-on baseline it does not have) but stays in the BRIDGE population, which
  is keyed to detected runs it genuinely performs. Its committed D-4 verdict on
  this mechanism is `pass` in all three years.

## 3. CORRECTION TO THE RECORD, made before the solve

The nyiso-144 handoff (from `RESULT-nyiso143` §6 / `ASSESSMENT-nyiso143` §2.3)
states the bridge floors **2517 Port Jefferson** for **0.1495 TWh in 2024**,
34.6 % of that leg, **4,623 binding hours**, median **0.000 MW**, **71.2 %** at
zero. The keeper's own committed `legitimacy_diagnostics.json` says otherwise:

| year | plant | floored TWh | share | binding h | measured median | at zero | verdict |
|---|---|---:|---:|---:|---:|---:|---|
| 2024 | 2517 | **0.0616** | 19.5 % | **1,716** | **45.222 MW** | **44.7 %** | **pass** |
| 2025 | 8006 Roseton | 0.1881 | 44.9 % | 1,714 | 0.000 MW | 60.9 % | **FAIL** |
| 2025 | 7314 | 0.0774 | 11.3 % | 2,235 | 0.000 MW | 77.1 % | **FAIL** |

The Roseton row matches the handoff exactly; the 2517 and 7314 rows do not. The
committed artifact is the source of truth, and on it **Port Jefferson passes**.
The handoff's premise for this job — "it still floors 2517 Port Jefferson" — is
therefore not what the keeper's diagnostics say, and the arm is scoped to what
they do say. (Likely provenance: the assessment's own note that a first,
payload-based rider run covering 100 plants and substituting 127 was superseded
by the full-dispatch numbers.)

## 4. FALSIFIABLE EXPECTATION, from the committed artifacts BEFORE any solve

The bridge's D-4 unit-conduct rows attribute its floored energy per plant-year.
Removing exactly the qualifying set predicts the arm sheds:

| year | bridge floored (unit-conduct) | predicted shed | share | qualifying plants that bind |
|---|---:|---:|---:|---|
| 2023 | 1.5071 TWh | **0.1186 TWh** | 7.9 % | 2480, 2625, 8006, 10190, 54034, 56188 |
| 2024 | 1.0460 TWh | **0.1396 TWh** | 13.3 % | 2480, 2625, 8006, 10190, 54034, 56188 |
| 2025 | 1.1060 TWh | **0.3089 TWh** | 27.9 % | + 54592, 54593 |

This is a **lower bound on the floor removed**, not a prediction of the energy
delta: the LP re-dispatches, and other units pick up the freed load.

## 5. KILL GATES — pre-registered, falsifiable, evaluated on the committed bundles

**K1 — ARMED AND RECORDED.** The arm's `meta.json` carries
`nyiso_gas_bridge_plant_exclusions=True` and the control carries it absent/False;
exactly ONE `scenario_config` field differs. *Fails if not.*

**K2 — LIVENESS.** The arm's bridge floor volume falls, and the shed lands
within **±50 %** of the per-year prediction in §4 in all three years. *Fails if
the mechanism is inert (0 shed) or the shed misses the band* — an inert arm
reads as "the mechanism does nothing", the failure mode nyiso-89 §4a names as
the most dangerous.

**K3 — MEMBERSHIP IS EXACTLY THE DECLARED SET.** In the arm's D-4 rows, every
one of the 12 qualifying plants has zero bridge-floored energy, and **no
non-qualifying plant loses its floor**. *Fails if any other plant is dropped* —
that would mean the channel is scoping on something other than the artifact.

**K4 — NO NEW D-4 FAILURE, AND THE KNOWN ONES SHRINK.** The arm introduces zero
new D-4 unit-conduct failures on any mechanism, and the bridge's failing set
loses the seven qualifying members. *Fails if a new failure appears.*

**K5 — NO GATED-CRITERION REGRESSION.** C1, C2, C3a, C3b, C4, C6, C8 do not
regress against the control in any year. C3c is **not** a promote criterion (the
standing rule ledgers it), and is reported at full magnitude whatever it does.

**K6′ — FORCED-SHARE ESCALATION** (the owner-adopted successor form, first
applied at nyiso-140). If any surviving mechanism's forced share RISES, the arm
is not killed automatically; it escalates and passes only if (a) every binding
non-exempt mechanism still clears D-4 off-window binding and (b) no new D-1
shape miss appears. A share that rises while the mechanism does strictly less
work is expected here, exactly as at nyiso-140.

**PROMOTE CRITERION: K1–K6′ clean.** Not "the fit improves". Under rule 1
`[R-STRUCT]` and rule 14 `[R-ACCURATE]` a correct membership stays in even if
the residual worsens — and it may well worsen, because the removed energy was
manufactured above measured conduct. A worse fit is a **discovered bug** whose
root cause becomes the successor, never a reason to revert.

## 6. WHAT THIS ARM IS NOT

* Not a scarcity or price lever, and not aimed at C3c.
* Not a re-opening of the Zone-K transfer bound (nyiso-143, closed, DO NOT
  RE-SOLVE).
* Not a change to the bridge's window, its measured min-load fractions
  (CC 0.523 / ST_GAS 0.239), its run horizons, or its physics gate.
* Not transferable: rule 28(d) / rule 25 `[R-ISO-SCOPE]` — this verdict fills no
  other ISO's cell, and any other ISO must identify its own laid-up units from
  its OWN CAMPD conduct.

## 7. REPRODUCTION

```
# control — the keeper recipe replayed at HEAD
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso143_n11tsl_arm \
  --out-dir results/calibration/nyiso144_control

# arm — the same recipe + the one field
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso144_arm_recipe \
  --out-dir results/calibration/nyiso144_layup_arm
```

(the arm recipe is the keeper's `meta.json` with
`nyiso_gas_bridge_plant_exclusions: true` — the replay path takes the whole
config from the bundle, so the flag is set in the recipe rather than on the
command line.)

Derivation of the membership artifact:

```
python scripts/data/derive_campd_bridge_layup_exclusions.py --iso NYISO --detail
```
