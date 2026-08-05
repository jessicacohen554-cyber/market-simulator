# FINDING — caiso-174: the FFR-4D epoch re-solve, and `storage_measured_base_fleet` is a MEASURED NULL

**Date:** 2026-08-05 · **Session:** caiso-174 · **Pre-registration:**
`PRECHECK-caiso174-epoch-resolve-2026-08-05.md` (committed before the first arm finished)

**Keeper PROMOTED:** `2026-08-04-caiso-172-measured-path15` → **`2026-08-05-caiso-174-measured-fleet`**
**Determination:** CALIBRATED-WITH-CAVEATS, **0 FAIL**, same 2 ledgered caveats, D-10 12/12 · free 8/8
**Matrix:** `storage_measured_base_fleet` CAISO **`O` → `I`**
**Recommendation on `complete`: YES** (per the rule pre-registered in PRECHECK §2)

---

## 0. The headline

`ASSESSMENT-caiso173` recommended **NOT YET** on `complete` for exactly one reason: FFR-4D's
cache epoch `2026-08-04c` had landed and the designated keeper predated it, so its metrics
described a model that no longer existed. This session is the re-solve FFR-4D §7 D-2 stated
as owed. **It is now done, and the result is a measured null:**

> **`ScenarioConfig.storage_measured_base_fleet` is PROVABLY INERT on the CAISO keeper's
> recipe.** Against its own same-head control the treated arm is **bit-identical** —
> `max |Δprice| = 0.000000` over **all** P1 zone-hours of **all three** years, **0 hours
> differ**, battery peak discharge and charge equal to the decimal, every displaced-class
> energy **+0.000 TWh**.

So the epoch invalidated the **cache**, not the **answer**. The keeper's metrics were never
actually wrong — but that could only be established by solving, not by arguing, which is why
caiso-173 correctly refused to declare on them. **The keeper is now post-epoch** (G0 flips to
`KEEPER IS PRE-EPOCH: False`), and the staleness question is closed by measurement.

**The substantive finding is a refutation.** FFR-4D §5 filed an explicitly-not-claimed
hypothesis: that the C3a-2025 caveat (mean LMP **+14.4 %** hot) was partly this fleet defect,
since *"7.4 GW of missing evening-peak battery leaves that load to thermal."* **C3a moves
−0.01 $/MWh.** The missing battery never had that load to leave.

---

## 1. Why it is inert — a composition fact, measured not argued

The keeper arms `caiso_storage_shape_anchor`, whose `caiso_storage_shape_caps` envelope is a
**per-year measured capability** (EIA-930 `NG:OTH` ÷ EIA-860 monthly fleet). That envelope
caps battery discharge **strictly below both fleets in every year**:

| year | Arm A fleet (flat) | Arm B fleet (measured) | **peak discharge** | peak charge | envelope binds below both? |
|---|---:|---:|---:|---:|:--:|
| 2023 | 15,450.0 | 7,492.4 | **4,256.5** | 3,442.0 | **YES** |
| 2024 | 15,450.0 | 11,131.3 | **6,914.6** | 6,162.3 | **YES** |
| 2025 | 15,450.0 | 15,448.4 | **9,550.3** | 8,133.6 | **YES** |

**The base-fleet scalar was never the operative constraint on battery dispatch**, so moving
it moves nothing. This restates caiso-168's finding that the LP **rides the anchor** — the
envelope, not the fleet, is the binding object.

**INERT BY COMPOSITION, NOT BY CONSTRUCTION.** Disarm `caiso_storage_shape_anchor` and the
base fleet *would* bind. The verdict is scoped to this recipe and must not be read as "the
field does nothing."

**The field stays armed and default-ON.** It corrects a real vintage/as-of misalignment —
`STORAGE_BASE_FLEET_MW` is a *forecast* object whose own docstring calls it "the base year
(2026)", yet `runner.py` fed it to every backcast year. Rule 14 `[R-ACCURATE]` makes the
measured EIA-860 fleet the right input, and rule 1 `[R-STRUCT]` forbids reverting a
structurally-correct measured input because it failed to move a residual. **A null result is
not a reason to remove it.**

---

## 2. The A/B — three states, and why the control earned its keep

PRECHECK §4a established that this is a **three-state** comparison, because FFR-4D made two
changes: it re-vintaged the constant `STORAGE_BASE_FLEET_MW["CAISO"]` **8,000 → 15,450 MW**
(no flag gates it) **and** added the field.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| keeper (pre-epoch) | 8,000.0 | 8,000.0 | 8,000.0 |
| **Arm A** control (new constant, flat) | 15,450.0 | 15,450.0 | 15,450.0 |
| **Arm B** treated (measured, vintaged) | 7,492.4 | 11,131.3 | 15,448.4 |

**B − A = 0 exactly.** **B − keeper is tiny but nonzero** — and the control is what proves
that residue is *incidental code drift* between head `789e28b8` and this one (FFR-4C, ercot-165,
miso-127/129, nyiso-127, neiso-83), **not** the epoch:

| year | C3a keeper | A | B | **B − keeper** | **B − A** |
|---|---:|---:|---:|---:|---:|
| 2023 | 56.18 | 56.16 | 56.16 | −0.02 | **+0.00** |
| 2024 | 38.59 | 38.59 | 38.59 | −0.00 | **+0.00** |
| 2025 | 39.36 | 39.35 | 39.35 | −0.01 | **+0.00** |

Every displaced class tells the same story — `CC_REGULAR`, `CT_PEAKER`, `ST_GAS` and
`import` all move ≤ 0.011 TWh vs the keeper and **exactly +0.000 TWh** vs the control.
**Without Arm A, that ≤0.011 TWh residue would have been misattributed to the epoch.**

---

## 3. The verdict rule fired as written

PRECHECK §2 fixed, **before any number was read**:

> CALIBRATED-WITH-CAVEATS with no NEW FAIL and no new caveat slot → **PROMOTE**, recommend
> **YES**. Determination degrades → **do not promote**, **escalate to the owner**.

**The first branch fired.** Both arms score CALIBRATED-WITH-CAVEATS, **0 FAIL**, the same two
ledgered caveats (C3a mean LMP, C3c price tail — the owner's act of 2026-07-30 at caiso-145),
D-10 free-class C1 **12/12 · free 8/8**. **No new caveat slot is spent and no criterion flips
in any year.**

**Rule 22 leave-one-year-out:** this session fits nothing and moves no free parameter, so LOYO
reduces to the no-held-out-degradation check — all three years are **bit-identical** to the
control, so no single year can carry the result.

**Rule 20 `[R-DOF]`:** `n_entries` **11** and `n_residual` **8**, both **UNCHANGED**. The
field carries **zero free parameters**. `gen_caiso174_attestation.py` **fails closed** on
exactly that invariant, and on two others: that the arms differ on **exactly one** config key,
and that the arm **re-resolves** the measured fleet from the shipped storage path rather than
from a hand-typed number.

---

## 4. The quantity gate caught a wrong pre-registration

The caiso-162 lesson is that a `run_config` recording a mechanism as armed is not evidence the
LP saw it. `scripts/probes/_caiso174_fleet_gate.py` ran **before any price was read** — and
its first run **failed**, correctly, on my own §4:

§4 had pre-registered the control at a flat **8,000 MW**. Wrong: FFR-4D's constant re-vintage
means a control at this head runs **15,450 MW**, and the pre-epoch 8,000 is **not reproducible
by any flag**. Recorded as **PRECHECK §4a**, not silently corrected. Two consequences fell out
of it, both pre-registered before the solve:

- the re-vintaged constant **is** the 2025 measured fleet rounded (15,450 vs 15,448.4), so the
  arms **coincide in 2025 by construction** and the field's per-year reach is 2023/2024 —
  where it turned out to be inert as well;
- **Arm A is not a reconstruction of the keeper's baseline** and never claimed to be.

A second correction inside the gate: the 2-D vintage ramp is produced by
`storage_cap_profiles`, **not** `storage_units_to_arrays`. The first draft checked the latter
and would have reported a **false failure** — the caiso-162 failure mode in a new place.

**Side effect confirmed live:** `storage_vintage_ramp`, armed on this recipe but a **dead flag
for batteries** while the fleet was a scalar (it reached pumped storage only), is live for
batteries for the first time — a **2-D `(6, 8760)`** power-cap profile that **varies within the
year** in all three years. That dead flag is now closed.

---

## 5. What this means for `complete` — **YES**

`ASSESSMENT-caiso173` found **every frontier limb intact** and withheld its YES on the epoch
alone. That blocker is now discharged:

| caiso-173 finding | status after this session |
|---|---|
| Lever queue empty, walls hold, evidence 19/19, census 0/0/0/0/0 | **unchanged — still intact** |
| ISO-specific residual DOF = 3, still sole highest | **unchanged** (re-measured, 11/8) |
| **Keeper is PRE-EPOCH** | **CLOSED — G0 now reads `PRE-EPOCH: False`** |
| `storage_measured_base_fleet` = CAISO `O`, backcast-scoped, default-ON | **CLOSED — adjudicated `I`** |

Per PRECHECK §2 and caiso-173 §6: **the recommendation on `complete` is YES.**

**The marker remains the owner's act and this session did not write it.**
`calibration-complete.json` and `holdout-freeze.json` are **UNTOUCHED**. CAISO holds no
`complete` marker, so rule 22 D-5(b) re-keying does not apply and every out-of-training year
(2022, 2019, ≤2021, H1-2026) stays fully quarantined; the **holdout spend freeze is ACTIVE**
and outranks any marker. Solved **2023/2024/2025 only** (rule 16).

---

## 6. Carried forward, unchanged

- **KNOWN-OPEN 1** — re-measured on the new keeper: model reproduces **5.5 / 2.5 / 3.0 %** of
  the measured `NP15−ZP26` basis (+5.947/+8.576/+5.727, congestion share 80–87 %). **Wide
  open.** No N–S topology lever is chartered (caiso-164 §0/§6 stands).
- **KNOWN-OPEN 2** — caiso-173 flagged that the caiso-170 storage-placement pointer was
  measured on a pre-epoch fleet and should be re-read. **It now needs no re-reading:** the
  fleet change is bit-identical in dispatch, so the pointer's statistics are unaffected. That
  is a *resolution* of caiso-173's concern, not a deferral.
- **C3a two-year widening** (+11.5 % 2024 / +14.4 % 2025) — unchanged, and now known **not**
  to be a fleet-vintage artifact (§0). Its root cause remains the caiso-141 A2 pumped-storage
  data wall.
- **MWD-TAC** — still a recorded open demand-input item (caiso-173 §2 C: a misapportionment
  worth 0.24–0.30 % of ISO load, **not** missing load). Deliberately kept **out** of this
  re-solve so the one delta stayed attributable.
- **`battery_dispatch_adder`** — CAISO's one genuinely open DOF lane, with a named
  forward-valid replacement.

---

## 7. Files

- This finding; pre-registration `PRECHECK-caiso174-epoch-resolve-2026-08-05.md`.
- Quantity gate `scripts/probes/_caiso174_fleet_gate.py` → `_caiso174_fleet_gate.json`.
- A/B scorer `scripts/probes/_caiso174_ab_compare.py` → `_caiso174_ab_compare.json`.
- Attestation generator `scripts/gen_caiso174_attestation.py` (three fail-closed checks).
- Closing check `scripts/probes/caiso173_frontier_recheck.py` → `_caiso174_frontier_recheck_post.json`.
- Bundles `results/calibration/caiso174_{control_flatfleet,measured_fleet}/`.
- Runs `2026-08-05-caiso-174-{control-flatfleet,measured-fleet}` (both registered, rule 15).
- Matrix cell `storage_measured_base_fleet` CAISO `O` → `I`; §5.2 header re-stamped.
