# FINDING — nyiso-109: the 2023 C3a breach was an identification-GRAIN error in the gas-offer margin anchor, and closing it restores NYISO to CALIBRATED-WITH-CAVEATS

**Session:** nyiso-109. **Frozen HEAD:** `1aad56a` + this session's mechanism
commit. **Outgoing keeper:** `2026-07-31-nyiso108-hydro-input-repair` (NOT-YET,
1 FAIL). **NEW KEEPER:** `2026-08-01-nyiso109-zonal-margin-anchor`
(bundle `results/calibration/nyiso109_zonalanchor_B`),
**CALIBRATED-WITH-CAVEATS**, 8 target-grade / 1 ledgered / **0 FAILs**.
**Pre-registration:** `results/calibration/PREREG-nyiso109-zonal-margin-anchor-2026-08-01.md`,
committed **and pushed** (PR branch `claude/nyiso-109-fossil-pricing-io7nhu`)
before either arm was scored.
**Solves: 2** — one same-HEAD zero-delta control, one single-delta arm, three
years each.

**This promotion is the pre-registration's OWN verdict.** Every construction
gate (K1–K6) and every kill gate (P1–P5) passes. No owner override was needed
or used — which is the material difference from nyiso-108.

---

## §0 — Headline

The nyiso-108 successor charter named *"the NYISO 2023 fossil over-pricing — an
offer-stack / fuel-basis root cause"*. It **was** an offer-stack root cause, and
it is now closed. But the charter's other premise — that the defect is
**2023-specific** — is **falsified by measurement**, and this finding records
that correction rather than following the instruction.

The defect is an **identification-grain error** in a mechanism armed on all six
keepers. `apply_gas_offer_margin` adds `markup_hr × (anchor − fuel)` and states
its own identity: *at `fuel == anchor` the reformed offer reduces EXACTLY to the
registered band multiplier.* That is a statement about **a unit's own delivered
fuel**. The anchor, however, is derived from `data.fuel.trajectories._gas_series`
— an **ISO-level** series that carries the hub overlay but **not** the per-zone
basis the solve applies afterwards on the `(n_gen, T)` array. On NYISO the zonal
basis leaves the **reference** zone (Capital_Hudson, Iroquois Z2) unchanged and
shifts every other zone strictly **down** to its own measured pipeline hub. Two
of five zones — **67.6 % of NYISO load** — were therefore pricing their markup at
a fuel level they never pay.

Resolving the anchor per zone (zero free parameters — the same measurement at
the grain the mechanism's own definition requires) moves **C3a 2023 from
+10.21 % to +7.51 %**, inside the ±10 % band. C3a passes in all three years, and
NYISO returns **NOT-YET → CALIBRATED-WITH-CAVEATS** with C3c the sole ledgered
caveat.

---

## §1 — The diagnosis, and the two handoff premises it corrects

Every measurement in this section is on committed artifacts with **no LP**
(`scripts/probes/_nyiso109_trough_offer_stack.py` →
`results/calibration/_nyiso109_trough_offer_stack.json`): the keeper's own
`hourly/` sidecars, the committed clean `lmp/NYISO/RTM` hourly actual (partial
coverage, disclosed), the committed bench payload, and the measured NYISO MIS
P-32 interface flows.

### 1.1 The residual is a COMPRESSED distribution, not a level error

Model-minus-actual system price by **actual-price decile**, on the covered hours
(2023: Jun + Dec; 2024: Feb–Jun + Sep; 2025: Aug):

| | trough (d1) | d5 | peak (d10) |
|---|---|---|---|
| 2023 | **+10.85** | +7.24 | **−11.56** |
| 2024 | **+11.18** | +6.17 | **−21.30** |
| 2025 | **+9.28** | +8.55 | **−25.04** |

By **load** decile the same shape (bottom **+8.81 / +4.92 / +8.31**, top
**+0.14 / −2.02 / −13.68**), and the model's within-load-decile price dispersion
is 1.9–5.0 against the actual's 3.4–16.1.

### 1.2 Premise 1 CORRECTED: the defect is ALL-YEARS, not 2023-specific

Trough (h01–h05) → evening-peak (h17–h19) amplitude:

| | model swing | actual swing | reproduced | trough err | peak err |
|---|---|---|---|---|---|
| 2023 | 9.37 | 13.62 | **69 %** | **+7.26** | **+3.01** |
| 2024 | 9.41 | 19.17 | **49 %** | **+5.50** | −4.26 |
| 2025 | 14.80 | 33.21 | **45 %** | **+8.65** | −9.75 |

The trough is over-priced in **all three years**. What is 2023-specific is only
that 2023 is the mild year whose **peak error is also positive**, so nothing
cancels the trough excess and the annual mean crosses the band. A lever scoped to
2023 would have been the wrong lever. This is the same defect PJM diagnosed at
pjm-141 (31/33/32 % of amplitude, sign-symmetric) — measured here independently
on NYISO's own data; PJM's verdicts transfer nothing (rule 25).

### 1.3 Premise 2 CORRECTED, and a REFUSAL: the interface route is not it

The congestion lead was real and was checked before the offer-side lead.
Measured on NYISO's own MIS P-32 postings:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| REAL `CENTRAL EAST - VC` within 50 MW of its posted limit | **0.8 %** | **0.1 %** | **0.2 %** |
| REAL `TOTAL EAST` / `UPNY CONED` / `SPR/DUN-SOUTH` | 0.0 % | 0.0 % | 0.0 % |
| MODEL link at its own monthly TTC | 16.1 % | 1.7 % | 1.4 % |
| MODEL mean separation when at TTC | $2.20 | $12.00 | $1.22 |
| REAL Upstate↔Capital separation (covered hours) | 60.3 % | 54.8 % | 38.2 % |

The model's monthly TTC envelope already tracks the measured monthly mean limit
(2023 model 1950…2725 vs measured 1918…2699 MW). **The real interface is
essentially never at its posted limit, so the posted limit is not what produces
the real separation** — that is marginal losses (zone LMP loss components
−$0.72…+$2.00/MWh) plus sub-interface nodal constraints, neither representable at
five-zone grain. Tightening the model's link to manufacture the spread would be a
**fitted** constraint (rules 5 / 14's named misalignment clause).
**`measured_interface_limits` NYISO → `G`, refused ex ante, no solve spent.**

**A correction to this session's own pre-registration, stated plainly:** §1.3 of
the prereg says the model's link "separates in 0.0 % of hours in all three
years". That is true only on the covered-actual-hours subsample at a $1
threshold; over the **full** year the model's link binds and separates in
12.0 / 1.3 / 1.1 % of hours. The refusal does not depend on it — it rests on the
real-world flow-vs-limit statistic, which is unchanged — but the prereg's
sentence was wrong as written and is corrected here rather than quietly dropped.

### 1.4 What the trough residual pointed at

Regressing the monthly Capital_Hudson trough (p10) on the month's measured
delivered gas (Henry Hub monthly + the committed NYISO hub basis): the model's
bottom-of-stack offer is **slope 3.74 MMBtu/MWh, intercept $16.95/MWh**; the
actual's is **slope 2.24, intercept $13.19**. A materially larger
**fuel-invariant adder** — the signature of `gas_offer_net_revenue_margin`'s
fixed $/MWh margin, whose implied per-band margins on NYISO's registered curve
are `CC_REGULAR` econ_low **$5.03**, `ST_GAS` econ_low **$10.36** / econ_high
**$12.52**, `CT_PEAKER` committed **$23.65**.

### 1.5 The marginal-rung census confirms it, and names the term

The pjm-141 §1 marginal-set test, re-derived on NYISO's own fleet (a unit is
marginal when its own hourly offer equals its own zone's dual to within
EPS = $1; fleet rebuilt from the control bundle's `meta.json` through
`run_year(fleet_only=True)`, **no LP**; detection 99.1–100 %):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| trough marginal tranche = **`econ`** | **80.5 %** | **81.1 %** | **80.8 %** |
| dominant pair `CC_REGULAR:econ` | 54.0 % | 50.9 % | 42.2 % |
| **peak control**, `econ` | 84.5 % | 83.5 % | 85.2 % |

The trough and peak windows are set by the **same rung family** — ordinary
economic loading, no floor rung and no part-load artifact at the margin, exactly
pjm-141's result. And the marginal trough rung's own offer decomposes as:

| | offer | = physical burn | + VOM | + **residual markup** | at fuel |
|---|---|---|---|---|---|
| 2023 | 29.69 | 20.56 | 2.30 | **6.84** | 2.755 |
| 2024 | 28.98 | 16.67 | 2.18 | **10.13** | 2.089 |
| 2025 | 45.36 | 33.73 | 2.39 | **9.24** | 4.072 |

**The markup is largest exactly where the fuel is furthest below the ISO
anchor** — 2024, at $2.089/MMBtu against an anchor of 3.9046 — which is
`markup_hr × (anchor − fuel)` read straight off the marginal rung. That is the
term §2 corrects, measured on the rung that actually sets the trough price.

Two further census results, both reported rather than acted on:

* **Within-day offer variation is EXACTLY zero.** No thermal LP row's offer
  moves between the trough hour and the peak hour of the same calendar day
  (σ = $0.000000, cap-weighted offer at trough = peak to the cent: $77.10 /
  $79.68 / $92.08). All of the model's diurnal amplitude must therefore come
  from merit-order traversal — NYISO reproduces pjm-141's T6 finding on its own
  fleet. This is the structural statement behind §1.2.
* **The model does not lack a cheap offer; it lacks depth.** Its cheapest
  thermal offer is **$1.40**, far below NYISO's own measured trough p05
  ($14.60 / $14.23 / $19.96), but only **8.0 / 7.7 / 8.2 GW** of 25.0–25.6 GW
  available sits below that target.

---

## §2 — The lever: the mechanism's own identification point, at the right grain

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO["NYISO"] = 3.9046` is derived from `_gas_series`,
which is ISO-level. `apply_nyiso_zonal_gas_basis` runs **afterwards** (before
`apply_dual_fuel_pricing`, therefore before the margin) and is anchored so the
reference zone is unchanged. Measured offsets from the committed SOM Figure A-6
table:

| zone | hub | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Capital_Hudson / Lower_Hudson / Long_Island | Iroquois Z2 | 0.00 | 0.00 | 0.00 |
| NYC | Transco Z6 NY | −1.34 | −0.71 | −1.38 |
| Upstate_West | Tenn Z4 200L | −1.46 | −1.07 | −3.08 |

`derive_gas_offer_margin_anchor.py --iso NYISO --by-zone` (new; applies the
**runtime** transform to the same series over the same 2023–2025 window, so the
values are by construction the levels the solve prices those zones at):

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 3.9046 |
|---|---|---|---|---|---|
| Capital_Hudson / Lower_Hudson / Long_Island | 3.3566 | 2.7969 | 5.5602 | **3.9046** | **0.0000** |
| NYC | 2.0166 | 2.0869 | 4.1802 | **2.7612** | −1.1433 |
| Upstate_West | 1.8966 | 1.7269 | 2.4802 | **2.0346** | −1.8700 |

**Zero fitted parameters** (+1 DOF entry, +0 residual-identified; 26 → 27
entries, `n_residual` 6 → 6). No new mechanism, no new identification constant,
no second channel: a band-scoped rebasis anchor (ERCOT-118/119 `margin_anchor_*`)
keeps precedence (rule 19). Rule 23 re-derives the table only on a source-data
change. Rule 25: the registry carries **NYISO only** and hard-fails elsewhere.

In the solve: **234 of 404** marked-up tranches move onto a zone anchor and the
median fixed margin falls **$6.04 → $5.39/MWh**.

---

## §3 — Every construction gate PASSES

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — arm `true` + the resolved map equal to the registry; control `false` / `null`; the mechanism it anchors armed at 3.9046 in **both** |
| **K2** control integrity | **PASS on the STRICT BYTE basis** — control − committed keeper = **exactly 0.0 MW** on every class-hour in all three years |
| **K3** liveness | **PASS** — system λ moves **−0.871 / −0.609 / −0.602 $/MWh**; class-hour Δ live in every year |
| **K4** single delta | **PASS** — the recorded scenario blocks differ in exactly the two zonal-anchor keys |
| **K5** year span | **PASS** — both bundles `[2023, 2024, 2025]`; the holdout spend freeze is ACTIVE and untouched |
| **K6** direction integrity | **PASS** — **no zone's λ rises anywhere**, as the construction requires (every zone anchor ≤ the ISO anchor, every markup ≥ 0) |

**K2 is again the load-bearing one, and it is a stronger result than nyiso-108's.**
Four solve-path commits landed on main since the keeper's HEAD
(`data/hydro.py`, `data/fleet/arrays.py`, `model/reserves/spec.py`). The prereg
recorded the expectation that they are NYISO-inert (NYISO is in neither
`EIA930_PS_FOLDED_INTO_WAT` nor `EIA930_PS_SPLIT_COMPLETE_FROM`) **as something
the control could falsify**. It did not: the control reproduces the committed
keeper bit-for-bit, so the A/B is unconfounded.

---

## §4 — Every kill gate PASSES, and the result

| kill | result |
|---|---|
| **P1** C1 free-class | **PASS** — 10/10 free and 14/14 all-class in both arms |
| **P2** no new load-bearing FAIL | **PASS** — the arm's FAIL set is **empty**, a strict subset of the control's `{C3a}` |
| **P3** protective gates | **PASS** — C6 / C7 / C8 all PASS |
| **P4** slack and dump | **PASS** — exactly 0.0 in every year of both arms |
| **P5** no fitted follow-up | **PASS** — the anchors are the derive script's own output; nothing was swept |

**C3a mean LMP, vs the load-weighted RT actual:**

| year | control | arm | band |
|---|---|---|---|
| 2023 | **+10.21 % (FAIL)** | **+7.51 % (PASS)** | ±10 % |
| 2024 | +1.05 % | −0.55 % | ±10 % |
| 2025 | −8.73 % | **−9.64 %** | ±10 % |

(DA diagnostic, non-gated: 2023 +7.9 % → +5.3 %.)

**Determination: NOT-YET → CALIBRATED-WITH-CAVEATS** (7 target-grade / 1 FAIL →
**8 target-grade / 0 FAILs**, 1 ledgered caveat).

**What does NOT move.** C1 stays **14/14 all-class, 10/10 free-class** in both
arms. C2 / C3b / C4 / C6 / C7 / C8 PASS in both. **C3c is unchanged** — model
3 / 0 / 7 h vs actual 10 / 12 / 42 h above $300 in both arms.

---

## §5 — The cost, reported and not hidden

**C3a 2025 moves −8.73 % → −9.64 %**, nearer the band edge. That is the honest
signature of §1.1–1.2: the residual is a compressed distribution, and this lever
corrects only its **trough** half. The peak half — under-priced by $4.3 (2024)
and $9.8 (2025) — is untouched and stays open. Any successor must be judged on
the **amplitude**, never on the annual mean, because a level that passes by
cancellation is not a correct level.

**The expected direction was pre-registered as grounds for extra scrutiny.**
Every zone anchor is ≤ the ISO anchor and every markup ≥ 0, so offers can only
fall — the direction the failing C3a wanted. The prereg fixed that in advance
(rule 1 `[R-STRUCT]`, both directions; the nyiso-101 posture): the lever is
defended on the arithmetic of the mechanism's own stated identity and would have
been the correct change had C3a not moved at all.

---

## §6 — The frontier: the C3c declaration STANDS and its PREMISE is RESTORED

nyiso-108 recorded that the nyiso-104b premise — *C3c is the sole blocker and
every other criterion passes* — had lapsed. It holds again: C3a passes in all
three years and C3c is once more the sole miss, carried as **one** ledgered
caveat. C3c itself is bit-unchanged across this A/B, so no C3c evidence moved,
the exhausted-queue finding is untouched, **no new caveat slot is spent**, and
the re-open condition is unchanged (a Capital_Hudson → Zone-F/Zone-G topology
split under its own owner charter).

**What is explicitly NOT restored is the "options exhausted" reading.** §1.1–1.2
measured a second, non-C3c, structurally real and still-open defect that passes
every current gate. It is not a blocker; it is an open item with no lever
chartered.

Holdout unaffected: NYISO keeps `complete`, stays **absent** from `final`, and
the ACTIVE spend freeze independently blocks every out-of-training solve. No
out-of-training year was solved, scored or probed.

---

## §7 — Cross-ISO exposure: measured, REPORTED, not acted on

**ERCOT, PJM and MISO also arm a zonal gas basis on their keepers**
(`ercot_zonal_gas_basis`, `pjm_zonal_gas_basis`, `miso_zonal_gas_basis` all
`true`), so the same grain mismatch exists in their lanes; CAISO and NEISO arm
none, so the row is n/a there. Their matrix cells enter as **`U`** — each needs
its own derived table and its own A/B in its own lane (rule 25). ERCOT partially
self-corrects already: `_gas_series` adds a flat EP-basis level term for ERCOT,
which the code's own comment describes as deliberately omitting the per-zone
spread. **Nothing outside NYISO is touched here and no other keeper moves.**

---

## §8 — Named successor and what is NOT claimed

**nyiso-110: the PEAK half of the compressed distribution** — the model
reproduces 45–69 % of the measured trough→peak amplitude and under-prices the
peak by $4.3 / $9.8 in 2024 / 2025. It is the same defect family pjm-141 named
(hour-varying offer conduct), where PJM found every in-model route already
adjudicated; NYISO's `measured_offer_surface` cell is still `U`, but NYISO
publishes no submitted-offer curve (the blocker nyiso-94 established for its DA
analogue), so a successor should expect to have to identify a different
instrument rather than transfer that one.

**Not claimed:** no C3c improvement (bit-unchanged); no amplitude claim beyond
the trough half; no hydro claim — the nyiso-108 input repair is neither
re-litigated nor re-tuned; the hydro **volume** statistic stays declared plumbing
and is not quoted; the barred statistics (2025 `solar`, 2025 `OTHER`, 2025
`ST_CHP`, `hydro` in every year) stay barred; no forecast-lane result; no
out-of-training year touched.

**Recorded honestly rather than dropped:** the pre-registration's §1.3 sentence
about the model's link separating in 0.0 % of hours is wrong as written (§1.3
above), and the `flows.parquet` measurement that corrects it only became
available once this session's own arms were solved.

---

## §9 — Test baseline measured at this HEAD

`tests/{curation,scoring,unit}` after a full `regenerate_clean`:
**14 failed / 4419 passed / 14 skipped / 1 xfailed / 254 subtests passed** in
11m56s. Composition: `test_measured_chp_heat_rates.py` **7** (the standing
deriver cluster), three cache-key byte-stability tests
(`test_cc_committed_offer_margin.py`, `test_ramp_envelope_basis.py`,
`test_forecast_xyear_warmstart_flag.py`), `test_consume_lmp.py` 1,
`test_ff_readiness_battery.py` 1, `test_outages.py` 1, and
`test_clean_io.py::test_datatype_list_matches_schemas` 1.

**None is attributable to this session.** Thirteen are nyiso-108's measured
baseline verbatim; the fourteenth (`test_datatype_list_matches_schemas` — the
`regenerate_clean` datatype list carries `ira-credit-parameters` with no schema
file) is a datatype/schema registry mismatch on main, and this branch touches no
`clean_io`, schema or `regenerate_clean` file.

**The three cache-key failures deserve their own check, because this session
added two `ScenarioConfig` fields.** Verified directly rather than assumed: the
default `ScenarioConfig().cache_key()` is **`0e9fce2fb55b889f` on `origin/main`
and `0e9fce2fb55b889f` at this HEAD** — byte-identical. The new fields are
correctly registered in the cache-key exclusion list at their defaults, and the
three tests fail against a stale pinned literal (`603c2498bf71d21d`) that was
already stale on main. Re-measure rather than inherit — the set moves several
PRs per session.

**11 new tests** land with the mechanism
(`tests/unit/data/test_gas_offer_margin_zonal_anchor.py`), all passing: the gate
is byte-identical off, hard-fails when half-armed, resolves each zone to its own
anchor, keeps a band-scoped rebasis anchor's precedence, and reproduces the
mechanism's identity (offer == the registered multiplier at the zone's own
anchor) in every zone.
