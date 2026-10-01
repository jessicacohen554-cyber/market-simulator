# PRE-REGISTRATION — nyiso-115: the NYC locational RCPF demand-curve SHAPE

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16 —
one bundle per arm) · **Keeper at session start:**
`2026-08-02-nyiso-113-li-locational` (CALIBRATED-WITH-CAVEATS, C3c the sole
ledgered caveat) · **Committed and pushed BEFORE either solve.**

---

## §1 — what is being tested, and why it is a rule-14 question

nyiso-114's per-family reserve-dual sidecar
(`hourly/reserve_family_<year>.parquet`) made NYISO's binding reserve constraint
observable for the first time: it is overwhelmingly the **NYC locational pair**
(`nyc_10min_total` priced in 17/6/29 hours of 2023/24/25, `nyc_30min_total` in
8/6/10), and those hours carry **large shortfalls at small duals** — up to
307/358/317 MW against a 500 MW requirement, clearing at $15.63/$18.75.

That juxtaposition is a question about a **measured input**, not about a
residual: does `NYISO_RCPF_LOCATIONAL` reproduce the published NYC Reserve
Capacity Penalty Factors? Rule 14 `[R-ACCURATE]` governs, and the question is
answerable **without a solve**, so it was screened ex ante first.

## §2 — the ex-ante screen, ALREADY RUN (`scripts/probes/_nyiso115_nyc_rcpf_curve_screen.py`)

**Instrument.** NYISO's own posted **zonal** Day-Ahead ancillary-service
clearing prices, `data/raw/NYISO-AS/NYISO_as_da_<year>.csv` — per zone, per
product. The locational regions **nest** (NYCA ⊃ East ⊃ SENY ⊃ NYC), so
differencing zone J (`N.Y.C.`) against a zone sharing every region **except**
NYC isolates the NYC-only locational shadow price.

**The isolation is checked, not assumed.** All three qualifying references
(`DUNWOD`/`MILLWD`/`HUD VL` — all SENY, none NYC) agree **exactly**: max
$25.00, the same 45/141 hours at exactly $25.00, and **zero** hours above
$25.01. The two non-SENY controls (`CAPITL`/`WEST`) do **not** agree — they
reach $35.17/$65.00, because they additionally carry the SENY component.

**LEVEL — CONFIRMED. The model's $25/MW is right.** The isolated NYC adder never
exceeds $25.00 in any of 26,301 hours across the three years, and the 10-minute
product stacks to exactly **$50.00** in precisely the hours the 30-minute one
sits at $25.00 (**5/5, 16/16, 98/98**) — a 10-minute reserve also satisfies the
30-minute requirement, so its price carries both duals. Independently, the
`CAPITL`/`WEST` control's $65.00 ceiling decomposes as $25 (NYC) + $40 (SENY
increment), corroborating the ASM values from a second direction.

**SHAPE — REFUTED.** The measured distribution is a smooth opportunity-cost
continuum below the ceiling **plus one atom exactly AT it** (17/45/141 hours),
with essentially **no mass at the interior rungs** of the model's 8-step ramp
(**0 / 1 / 2** hours out of 103/167/428 material hours). A linear ramp places
atoms at every rung; a single step at the RCPF places exactly this. The model's
own NYC duals land on those rungs ($3.125 … $18.75) and **never reach the
published $25.00 in any of 26,280 hours, in either family, in any year.**

| family | model mean dual when binding (23/24/25) | published RCPF | under-price |
|---|---|--:|---|
| `nyc_10min_total` | $11.39 / $16.15 / $10.47 | $25.00 | **2.20× / 1.55× / 2.39×** |
| `nyc_30min_total` | $3.52 / $6.77 / $4.69 | $25.00 | **7.11× / 3.69× / 5.33×** |

The 30-minute family is worse **purely because its requirement is larger**
(1,000 MW vs 500), which makes the same ramp shallower — an artifact of the
construction with no market basis.

**A potential omission, checked and CLOSED.** ASM §6.8 item 2 prices "…New York
City… Spinning Reserves" at $40/MW, so a NYC locational *spin* family the model
omits would be a second rule-14 gap. Isolating it (`spin_10 − nonsync_10`, NYC
minus upstate) gives a 1,668–3,257-hour continuum with max $20.91–29.72 and
**zero hours at $40** — opportunity cost, not an enforced RCPF. **The model is
correct to omit it.** No action.

## §3 — the mechanism, and why the scope is the measurement's own boundary

`nyiso_nyc_rcpf_step_curve` (default **off**, NYISO-only, requires
`--energy-reserve-coopt`), scoped to
`NYISO_RCPF_STEP_CURVE_FAMILIES = ("nyc_10min_total", "nyc_30min_total")`.

**No new number is introduced (rule 5 `[R-NO-MAGIC]`).** Setting
`critical == requirement` collapses the ramp region to zero width, leaving the
single band at the **same published $25 RCPF** that
`nyiso_rcpf_product_shortfall_steps` already emits for that input. Total step
width is conserved, so the reserve balance row stays feasible at zero reserve.

**Scope is measured, not chosen.** NYC is the **only** locational region whose
published RCPF the measured market ever reaches:

| region | model max penalty | measured isolated adder, max (23/24/25) | verdict |
|---|--:|--:|---|
| NYC | $25 | **$25.00 / $25.00 / $25.00** | ceiling reached — shape identified |
| East | $775 | $27.00 / $36.05 / $46.22 | never approached — shape unidentified |
| SENY | $500 | $23.92 / $30.37 / **$40.00** | caps at the $40 #1344 increment |
| LI | $25 | no material hours in any year | never binds — shape unidentified |

East and LI keep the ramp. **SENY is deliberately NOT touched**: its $40 ceiling
is the issue-#1344 dynamic-requirement increment, which belongs to
`nyiso_ordc_measured_step_span` and its own pre-registration (rule 19
`[R-ONE-MECH]`). This is recorded as a finding, not acted on.

## §4 — HONEST LIMIT, stated ex ante so it cannot be claimed afterwards

**This changes the LEVEL, not the FREQUENCY.** A step and a ramp are *both* $0
at or above the requirement, so the family binds in the **same hours** either
way. This therefore **cannot** close nyiso-110's everyday-reserve-formation gap
(model 17/6/34 reserve-priced hours vs a measured NYISO DA spin price > $1 in
**100 %** of peak-window hours), and **must not be reported as closing it**.
Indeed a steeper curve makes shortfall more expensive to incur, so binding hours
may **fall**. Any outcome on the tail count is reported as measured, in either
direction.

## §5 — DO-NOT-REDO check (rule 28a), stated rather than assumed

* No NYISO cell marked `R`/`I`/`G` covers the curve **shape**. The two adjacent
  rows are `nyiso_rcpf_family` (**K** — which families exist and who may supply
  them; its "reserve-formation family is EXHAUSTED" verdict is about *supply*
  and *frequency*, which §4 explicitly does not contest) and
  `nyiso_ordc_measured_step_span` (**U** — width translation under a *dynamic*
  requirement, a different mechanism on different families).
* **The June-2026 `nyiso 25 rcpf-steep` probe is not a bar.** It transferred the
  **NYCA-30min** curve's `critical = 0.75 × requirement` anchor to the
  locational products — a different parameterization derived from a different
  family — carried **no matrix row**, and was rejected on the **C3c tail
  count**, i.e. on fit, which rule 1 `[R-STRUCT]` forbids as grounds for
  rejecting a structurally-correct mechanism. The present value is measured from
  NYISO's own locational prices.

## §6 — arms

Both solved from the nyiso-113 keeper recipe over **2023, 2024, 2025** in one
bundle each (rule 16), launched concurrently (rule 12, 2-way cap):

| arm | bundle | delta |
|---|---|---|
| **CONTROL** | `results/calibration/nyiso115_control` | zero-delta replay at THIS session's HEAD |
| **TREATMENT** | `results/calibration/nyiso115_nyc_stepcurve` | `nyiso_nyc_rcpf_step_curve=true` |

A **same-HEAD control is mandatory**, not optional: FINDING-nyiso114 §2 measured
that a keeper arming a P0-run-pattern bridge does **not** re-solve to
byte-identity once main moves (max |Δprice| $9.0–10.6 attributable entirely to
main's drift). Every attribution below is treatment-vs-control at one HEAD, never
treatment-vs-keeper.

## §7 — GATES (pre-registered), each on an instrument that can observe its claim

Reserve gates read `hourly/reserve_family_<year>.parquet` — **never**
`system.parquet`'s `reserve_price`, which is the cross-family SUM broadcast
identically to every zone and is inert by construction (the nyiso-113 K3/K4
error).

| id | gate | pass condition |
|---|---|---|
| **G1** | the curve is actually armed | `nyc_10min_total` / `nyc_30min_total` duals take the value **$25.00** in ≥ 1 hour, and take **no** interior-rung value ($3.125…$21.875) in **any** hour, all three years |
| **G2** | scope respected | `east_*`, `seny_*`, `li_*`, `nyca_*` families byte-identical to control in `dual`, `requirement_mw`, `held_mw`, `shortfall_mw` |
| **G3** | LP row identity holds | `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices (the nyiso-114 G3 check, re-run on this bundle) |
| **G4** | no feasibility damage | zero unserved-energy slack and zero dump in both arms, all three years |
| **G5** | span | 2023–2025 in one bundle; **no** year outside 2023–2025 touched (rule 22 — the holdout freeze is ACTIVE) |
| **G6** | scoring | `legitimacy_diagnostics.py` + `calibration_verdict.py` run per bundle; C1/C2/C3a/C3b/C3c/C4/C6/C7/C8 reported for BOTH arms against each other |

## §8 — KILLS (pre-registered), each discharged BY MEASUREMENT, never by reading the diff

nyiso-114's K-A lesson is binding: a kill is discharged by re-measuring, not by
asserting that the diff looks inert.

| id | kill | discharge |
|---|---|---|
| **K-A** | the effect is main's drift, not the mechanism | Compare TREATMENT to the **same-HEAD CONTROL** (§6), never to the keeper. If control-vs-keeper divergence exceeds treatment-vs-control on the NYC families' duals, the arm reports nothing and says so. |
| **K-B** | the flag is inert (nothing to report) | If G1 finds **zero** hours at $25.00, the mechanism did not arm; report **INERT** with the cell set `I`, and do **not** narrate a price delta. |
| **K-C** | the scope leaked | If G2 finds **any** non-NYC family changed, the arm is **VOID** — that is a construction bug, not a result. Fix and re-solve, or withdraw. |
| **K-D** | forced-energy / feasibility damage | If G4 finds slack or dump appearing where control had none, the arm is **NOT** promotable regardless of price movement. |

## §9 — NO-TUNING CLAUSE (binding)

* **The $25/MW RCPF is not a free parameter and will not be moved**, in either
  direction, for any reason, in this session or by this mechanism. It is the
  published ASM §6.8 value, already confirmed against measurement in §2. The
  only thing this arm changes is the **depth at which that published penalty
  applies**.
* **`n_ramp` will not be tuned.** The step curve has no ramp; the flag-off arm
  keeps `n_ramp=8` untouched.
* **No family's requirement MW is touched.** Not NYC's 500/1,000, not SENY's,
  not LI's, not East's.
* **SENY's $500 → measured-$40 discrepancy is REPORTED, NOT ACTED ON** in this
  session (rule 19 — it is `nyiso_ordc_measured_step_span`'s mechanism and needs
  its own pre-registration).
* Carried forward unchanged from prior sessions: the ramp envelope, the 227-3
  compliance file, the LI reserve levels / $25 value / On-Peak calendar, and the
  `nyiso_gas_bridge_*` measured min-load / min-run parameters (rule 23
  `[R-FROZEN-DERIVE]` — re-derive only on a SOURCE DATA change, never on a
  residual).
* **Promotion is decided on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`, not on
  the residual.** A structurally-correct published curve stays in even if the
  fit degrades; if it degrades, that is a discovered root-cause issue and is
  reported as one.

## §10 — governance

* **Rule 16** — all three training years in one bundle per arm.
* **Rule 22** — the holdout spend freeze is **ACTIVE**. No year outside
  2023–2025 is solved, scored or read; no marker spent or requested.
* **Rule 28(b)/(c)** — the matrix row `nyiso_nyc_rcpf_step_curve` is added in
  the **same PR** as the `ScenarioConfig` field, seeded `O`, and updated to its
  verdict in **this** session.
* **Rule 15** — both arms are registered on the dashboard in this session,
  keeper or not.
* **Rule 27** — every push touching a file ≥ 300 lines is blob-verified.
