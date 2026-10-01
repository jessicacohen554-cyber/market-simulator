# PRECHECK — caiso-187: THE WEFOR-vs-OVERLAY RECONCILIATION (`wefor_residual` / `wefor_multiplier`)

**Pre-registration. Written and pushed BEFORE the residual value is computed, before any LP
is solved, and before any scored metric of this session's object is read.** Every bar,
formula and stop rule below is fixed here and is fail-closed.

* **Session:** caiso-187. **ISO: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d).
* **Branch:** `claude/caiso-186-seasonal-capability-nmgjkb` (the session's designated branch).
* **Authorisation:** owner decision, this session — route **(c)** of FINDING-caiso186 §10,
  the successor that finding filed and did not build.
* **Incumbent keeper:** `2026-08-09-caiso-184-c1-lpbasis` — **NOT-YET**, C3a the SOLE
  load-bearing FAIL (2023 **+3.7 %** PASS, 2024 **+10.5 %** FAIL, 2025 **+13.1 %** FAIL).
  **DOF ledger 11 / 8.**
* **Holdout:** CAISO holds **no `complete` marker**, spend freeze **ACTIVE**. **2023 + 2024 +
  2025 ONLY**, one bundle per arm (rule 16), years sequential, arms sequential (rule 12).
  `calibration-complete.json` and `holdout-freeze.json` are **OWNER ACTS — neither is written
  by this session.**
* **C3a is REPORTED, never TARGETED, and is NEVER the promotion basis.**

---

## 0. P0-1 — DO-NOT-REDO audit (rule 28 duty a)

* **NOT caiso-186** (`cc_winter_capability_basis`, CAISO = `R`). That flag is **not armed**
  here, and this charter does **not** re-test the published seasonal capability basis. It
  tests the *other* half of the composition caiso-186 §6a identified. **If the outcome of
  this session makes that basis admissible, re-testing it is a SEPARATE, LATER charter** —
  not a second arm here.
* **NOT `unit_outage_short_windows` / `unit_partial_outage_windows`** (caiso-136/180,
  CLOSED). Those are **window overlays** with a **coal-only detector**, and CAMPD's CAISO
  population has **zero coal** — the committed `campd-unit-outages-short-CAISO.csv` has
  **0 rows**. They are **not armed** here and the coal-only detector is **not re-run on gas**.
  This charter changes a **statistical rate**, not a window set.
* **NOT caiso-184 / caiso-183 / caiso-181** — no outage window, grain, depth, denominator or
  extract is touched. The extract is **read only**.
* **NOT any struck lever** (`battery_dispatch_adder`, the offer-surface coverage extension,
  the AS-power-reservation family, N–S topology, the seam/intertie family,
  `caiso_ps_charge_shape_anchor`). None re-opened.
* **The cell is genuinely open at CAISO.** `wefor_residual` is armed on the **ERCOT** keeper
  (0.02) and the **PJM** keeper (0.015); `wefor_residual_groups` on ERCOT
  (`{ST_GAS, ST_CHP}`). **No verdict transfers** (rule 25 / 28 duty d) — this session derives
  CAISO's value from CAISO's own extract and adopts neither number. A repo search finds no
  prior CAISO adjudication of either field.
* **Rule 28(c) debt to close.** `wefor_residual` and `wefor_residual_groups` are
  solve-affecting fields registered **only as literals inside `wefor_statistical_stack`'s
  `def`** — the "passes the mention-anywhere CI gate yet can never carry a verdict in any
  ISO" class ercot-177 / nyiso-115 / caiso-185 name. **A verdict-bearing row is split out in
  this PR.**

---

## 1. THE OBJECT — a live double count, and the fitted knob that has been hiding it

`data/fleet/arrays.py` states the defect in its own comment:

> "the CAMPD overlay + unit-level derate already carry every ≥ 5-day outage for the covered
> classes … so their full statistical WEFOR would double-count those events. Cap it at the
> short-outage residual … `wefor_residual`"

**On the CAISO keeper `wefor_residual` is `None`, so that cap is never applied.** In a
historic backcast a covered CC unit's availability is set to `1 − WEFOR` and the CAMPD
outage overlay multiplies on top. The model therefore removes, per covered unit,
approximately

```
statistical WEFOR   +   overlay-measured outage    (two mechanisms, one phenomenon)
```

where the second term is a **measured record of the same events the first term is a
statistical expectation of**. Rule 19 `[R-ONE-MECH]`.

### 1a. What makes this charter different from a normal lever

**`wefor_multiplier = 0.7` on the CAISO keeper, and it is DOF ledger entry #5 with
`identification: "residual"`** (`calibration_attestation.json`, `>= 52 solves`). The class
WEFOR base for `CC_REGULAR` is `0.05`, so the model's effective CC forced-outage rate is
`0.05 × 0.7 = 0.035` — exactly the `0.965` peak availability caiso-186 measured on every
violated plant-season.

So the double count **is already being compensated — by a residual-fitted scalar rather than
by the measured repair the code's own comment prescribes.** That is simultaneously:

* **rule 19** — `wefor_multiplier` and `wefor_residual` are two mechanisms for one
  phenomenon, and the fitted one is armed while the measured one is not;
* **rule 21 `[R-DOF]`** — "a residual that can only be closed by a tuned value is an open
  root-cause issue, not a parameter". This is that root cause, still open.

**The prize is therefore not a better fit — it is a SMALLER LEDGER.** The target end state is
`wefor_multiplier` back at its neutral `1.0` and `wefor_residual` carrying a **measured**
value, i.e. **DOF 11 / 8 → 11 / 7** (one entry moves from `residual` to `measured`), or
10 / 7 if the multiplier leaves the ledger entirely. **A DOF increase is an automatic fail;
no decrease at all is a failure of the charter's own thesis and must be reported as one.**

---

## 2. THE IDENTIFICATION — the formula is FIXED HERE, before the value is computed

**This is the load-bearing section of this pre-registration.** The value must be *derived*,
never *chosen*, and it must be computed and committed **before any price is read**.

For each covered class `c` (the CAMPD-covered set `_POF_DROP_GROUPS` =
`{CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}` plus coal by fuel type; CAISO has **zero coal**):

```
W_c  =  the model's OWN published statistical forced-outage rate for class c
        — constants.THERMAL_AVAILABILITY[c] WEFOR base + its age escalation,
          capacity-weighted over the CAISO fleet's units of that class,
          evaluated with wefor_multiplier = 1.0   (the UNFITTED rate)

X_c  =  the CAMPD overlay's OWN measured removal for class c
        — Σ over committed campd-unit-outages-CAISO.csv rows of class c
          (unit-outage-hours x unit_pct_of_plant) ÷ (class capacity x hours),
          pooled over 2023-2025, computed through the SHIPPED loader
          (outages.unit_outage_derate_factors) so it is the overlay the LP
          actually applies, not a re-implementation

residual_c  =  max(0, W_c - X_c)
```

and the single scalar the field takes:

```
wefor_residual  =  the CAPACITY-WEIGHTED mean of residual_c over the covered classes
                   PRESENT IN THE CAISO FLEET, rounded to 4 decimals
wefor_residual_groups  =  the covered classes present in the CAISO fleet
```

**Why this is zero-DOF.** `W_c` is already in the model (`constants.THERMAL_AVAILABILITY`,
unchanged, not re-derived — rule 23). `X_c` is a **count over a committed artifact**, read
through the shipped loader. `max(0, ·)` is a physical bound, not a tuning choice. **No term
is fitted, no term is free, and no term can respond to a price.**

**What this asserts.** After the repair the *total* expected unavailability of a covered
class equals `W_c` — the model's own published statistical rate — instead of
`0.7·W_c + X_c`. The overlay supplies the sustained (≥ 5-day) part it measured; the residual
supplies the rest.

### 2a. Fixed in advance, so it cannot be chosen later

1. **The rounding is 4 decimals, stated now.** No other rounding will be used.
2. **`max(0, ·)`**: if `X_c ≥ W_c` for a class, that class's residual is **0** — the overlay
   alone already exceeds the statistical rate. **That is a reportable finding, not a licence
   to raise `W_c`.**
3. **`W_c` is NOT re-derived.** Rule 23 `[R-FROZEN-DERIVE]`: `THERMAL_AVAILABILITY` re-derives
   only on a source-data change, and none is cited. If `W_c` looks wrong, that is a separate
   charter.
4. **The value is computed ONCE, written to `_caiso187_residual_identification.json`, and
   COMMITTED AND PUSHED BEFORE THE FIRST SOLVE.** It is frozen from that commit onward.
   **Recomputing it after seeing any price is forbidden and would void this session.**
5. **No sweep.** No second value, no sensitivity arm, no "±0.005 to check". One value, from
   the formula.

---

## 3. THE INSTRUMENT

**No new `ScenarioConfig` field.** Both fields already exist and are already registered.
The arm is:

| field | keeper | **ARM A** |
|---|---|---|
| `wefor_multiplier` | **0.7** *(DOF #5, `residual`)* | **1.0** *(neutral — the fitted knob retired)* |
| `wefor_residual` | `None` | **the §2 measured value** |
| `wefor_residual_groups` | `None` | the covered classes present in the CAISO fleet |

**This is ONE mechanism change, not three.** It replaces a fitted compensation with the
measured repair the code prescribes; splitting it would produce an arm
(`wefor_multiplier = 1.0`, `wefor_residual = None`) that is the **full uncompensated double
count** — a configuration known-wrong in advance, which rule 1 says we do not spend LP on.
A **diagnostic-only** decomposition may be reported from the fleet arrays **without an LP**.

---

## 4. GATES — pre-registered, fail-closed

| gate | bar |
|---|---|
| **G-DOF** | The ledger **MUST NOT INCREASE**. Target **11 / 7** (`wefor_multiplier` moves `residual` → `measured`, or leaves). **An increase is an automatic FAIL. No decrease is a FAILURE OF THE THESIS and is reported as one.** |
| **G-NOFIT** | **ZERO fitted scalars.** Every term in §2 is published-in-model or counted from a committed artifact. **No value tuned to a residual, no sweep, no post-hoc adjustment.** |
| **G-FROZEN** | The residual value is **computed, committed and pushed BEFORE the first solve**, and never recomputed afterwards. Violation voids the session. |
| **G-NODOUBLE** | The repair must be shown to remove a **real** double count, not to invent headroom: `X_c > 0` for every class credited, measured through the **shipped loader**, and the post-repair total unavailability must equal `W_c` to within the rounding. A class with `X_c = 0` gets **no relief** (its residual is `W_c`, i.e. unchanged). |
| **G-SCOPE** | Only classes with actual CAMPD overlay coverage in the CAISO extract are relieved. **CT classes are NEVER relieved** (`_POF_DROP_GROUPS` excludes them; CTs have no overlay coverage), even though the CAISO extract carries 527 `CT_CHP` outage rows — that mismatch is **REPORTED as an open observation, not acted on**. |
| **G-SIXISO** | The other five ISOs **byte-unchanged**. Both fields are per-run config, so the proof is that no other ISO's committed keeper config or default is edited, and **neither ERCOT's 0.02 nor PJM's 0.015 is adopted or referenced as evidence** (rule 25). |
| **G-C1** | C1 free-class fuelmix PASS on every free class, all three years. |
| **G-PROT** | C6 and C8 PASS; C8 stays **SCORED** (`legitimacy_diagnostics.json` registered). |
| **G-LOYO** | Any verdict flip scored **leave-one-year-out within 2023-2025 BEFORE promotion**. |
| **CONTROL** | **MANDATORY if any arm solves.** Reproduce the keeper via `--replay-bundle results/calibration/caiso184_c1_lpbasis` (**never** a remembered CLI string); re-measure the same-head identity at **FULL precision** and **quote the noise floor BEFORE reading any treated delta**. caiso-184 measured it BIT-ZERO (0 of 61,320 zone-hours); if it is no longer bit-zero, **that is a finding about the head** and is reported as one. |

---

## 5. P0-4 — DIRECTION, and why this session carries the HIGHEST motivated-reasoning risk of the lane

**Removing a double count ADDS capability, which LOWERS price.** The model is **+10.5 %
(2024) / +13.1 % (2025) OVER** on C3a. **So this lever's expected direction is the one that
flatters the residual** — the exact opposite of caiso-186, whose expected direction was
unfavourable and which was therefore safe by construction.

**This is the hazard, and it is pre-registered as the primary one:**

1. **The value comes from the §2 formula and nothing else.** It is frozen and pushed before
   the first solve (G-FROZEN). **If the formula's value moves C3a the wrong way, or too far
   the right way, the value STANDS.**
2. **A FAVOURABLE C3a MOVE IS NOT CORROBORATION.** It is the expected sign of *any*
   capability addition, correct or not, and will be reported as such — never quoted as
   evidence that the residual value is right.
3. **OVERSHOOT IS A REAL FAILURE MODE AND IS PRE-DECLARED.** If C3a crosses from `+13.1 %`
   to a materially NEGATIVE error, that is **not** a success: it says the repair released
   more capability than the double count justified, and the finding must say so and
   investigate rather than celebrate. **Neither outcome licenses re-tuning the value.**
4. **The promotion basis, if any, is the LEDGER and the MECHANISM** — a residual-fitted DOF
   replaced by a measured input, the double count removed — **never C3a**. A keeper promotion
   on this arm requires G-DOF to show a genuine decrease; a C3a improvement with the ledger
   unchanged is **not** a promotion case.
5. **No compensating adjustment**, no partial scope chosen for its direction, no second value.

---

## 6. ARMS

Sequential (rule 12), each one invocation covering **2023 + 2024 + 2025** (rule 16):

1. **CONTROL** — `--replay-bundle results/calibration/caiso184_c1_lpbasis`, out-dir
   `results/calibration/caiso187_ctl`. Read FIRST; the noise floor is quoted before any
   treated number.
2. **ARM A** — keeper recipe + `wefor_multiplier=1.0` + the §2 measured
   `wefor_residual` / `wefor_residual_groups`, out-dir `results/calibration/caiso187_wefor_A`.

**No third arm. No sweep. No variant chosen after a result.**

---

## 7. BRANCHES, fixed now

* **BRANCH A — the formula yields a MATERIAL residual and G-NODOUBLE passes.** → Solve
  CONTROL then ARM A, register ARM A on the dashboard (rule 15) **whatever C3a does**, update
  the matrix cell from this session's own evidence, and report the ledger movement first and
  C3a second.
* **BRANCH B — the formula yields `residual ≈ W_c` for every class** (i.e. `X_c ≈ 0`: the
  overlay removes almost nothing, so there is no double count to remove). → **No LP.** The
  charter's premise is refuted by measurement; report it, score the cell `I`, and the
  `wefor_multiplier = 0.7` DOF stays open with a *different* explanation owed.
* **BRANCH C — the formula yields `residual = 0` for every class** (`X_c ≥ W_c`: the overlay
  alone already exceeds the published statistical rate). → **No LP without escalation.** That
  would mean the overlay is removing more than the statistical model says exists, which is a
  finding about the **overlay**, not a licence to zero the statistical term. Report and
  escalate.
* **BRANCH D — G-NODOUBLE or G-DOF fails.** → **Kill before solve**, nothing registered,
  keeper unchanged, cell scored from this session's evidence.

**In every branch the matrix is updated in THIS session** (rule 28 duty b) and the new
verdict-bearing `wefor_residual` row is added in the same PR (duty c), with every other ISO's
cell carrying **no transferred verdict** — except that an ISO whose **own** committed keeper
arms the field is recorded as armed (registration, not adjudication; the caiso-185 §8
precedent). **ERCOT's 0.02 and PJM's 0.015 are recorded as their own lanes' values and are
never adopted, averaged, or used as a sanity check on CAISO's.**

---

## 8. THE STANDING DATA BLOCKER — unchanged, not a session lever

C3a's first named contributor remains the **walled hourly pumped-storage water state**
(FINDING-caiso140 §B / caiso-141 A2) — owner-funded intake. This session attempts **no**
proxy, **no** split heuristic and **no** PS mechanism tuned to the level residual.

---

## 9. Governance

Rule 1 `[R-STRUCT]` — structure first; the promotion basis is the ledger and the mechanism,
never C3a, and the favourable expected direction is pre-declared as a hazard rather than a
hope (§5). Rule 11 — the fitted `wefor_multiplier` is treated as the open root cause it is,
not left buried. Rule 13 `[R-MEASURED]` — the residual is counted from a committed measured
artifact and regenerates for any year from the same extract; no measured *outcome*, price
residual or benchmark enters any input or any bar. Rule 14 `[R-ACCURATE]` — a measured input
replaces a fitted scalar; if the fit worsens, the measured input **stays** and the root cause
is pursued. Rule 15 / 16 — if an arm solves, the full 2023-2025 bundle is registered in this
session; no single-year keeper. Rule 19 `[R-ONE-MECH]` — the object: two mechanisms for one
phenomenon, resolved by **replacing** one, never by stacking. Rule 21 `[R-DOF]` — the charter's
thesis and its hardest gate. Rule 22 `[R-HOLDOUT]` — 2023-2025 only, freeze respected, both
markers untouched (owner acts). Rule 23 `[R-FROZEN-DERIVE]` — `THERMAL_AVAILABILITY` is **not**
re-derived and no data byte is written; the extract is read only. Rule 24 `[R-REGISTRY]` — no
new field; both are in `ScenarioConfig` and `run_config.json`; no env knob, no hardcoded dict.
Rule 25 `[R-ISO-SCOPE]` — CAISO only; ERCOT's and PJM's values are neither adopted nor used as
evidence. Rule 27 `[R-PUSH]` — this pre-registration is pushed and blob-verified before the
value is computed and before any LP; every push verified by commit-SHA round trip. Rule 28
`[R-MECH-MATRIX]` — duty (a) in §0, duties (b) and (c) in §7.
