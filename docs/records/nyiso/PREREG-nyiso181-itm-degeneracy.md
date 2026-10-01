# PREREG — nyiso-181: is the un-dispatched in-the-money `ST_GAS` signature LP degeneracy?

**Session:** nyiso-181, NYISO backcast-calibration track, 2026-09-03.
**Keeper:** `2026-09-02-nyiso-177-vintage-matched` (`results/calibration/nyiso177_vintage_B1p`),
determination NOT-YET, target grade 5, fails 3 {C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}.

**Object, as re-posed by nyiso-180 §7 and handed forward at §12.3:** not *"why doesn't
in-the-money capacity run"* — under a reduced-cost optimality condition that is not an anomaly —
but **"what carries a sustained LEVEL gap in the in-the-money-unrun `ST_GAS` statistic"**. Two
named carriers survive; **LP degeneracy at a price plateau is the stronger and is taken first**,
as directed.

**This document is written and committed, together with its probe, BEFORE any quantitative
measurement of a reduced cost, of a degenerate share, or of any Ω.** §0 discloses in full
everything read at the time of writing.

---

## 0. DISCLOSURE — everything read before these gates existed

Nine reads were performed before this file was written. **All nine are code, artifact-schema, or
git-history facts. None is a quantitative measurement of the object.** No reduced cost, no Ω, no
degenerate share and no corrected `R` has been computed or read. The gates below are blind to
their own outcomes.

| # | what was read | result |
|---|---|---|
| E1 | `docs/FINDING-nyiso180-st-gas-undispatch-2026-09-03.md` §§7–12 | The premise correction, the seven-of-eleven sign/scope table, the four closed candidates, the two surviving carriers. |
| E2 | `results/calibration/PREREG-nyiso180-st-gas-undispatch.md` §§0–2 | The disclosure discipline and the one-sided-in-advance construction of G2. |
| E3 | `results/calibration/PREREG-nyiso180-per-generator-dispatch.md`, in full | The **parallel** lane's pre-registered predictions P-a / P-b / P-c / P-d, its §2.4 identity-closure STOP, and its §3 attribution limit. |
| E4 | `scripts/probes/nyiso180_unit_dispatch_adjudication.py`, in full (340 lines) | A complete, pre-registered adjudication instrument reading `hourly/unit_hourly_<year>.parquet`'s `mc` / `red_cost`. |
| E5 | `.gitignore:541,543` | `results/calibration/*/hourly/unit_hourly_*.parquet` is **gitignored**. |
| E6 | `ls results/calibration/nyiso177_vintage_B1p/hourly/` | `class_band_hourly`, `class_hourly`, `reserve_family`, `storage`, `system` — **no `unit_hourly`, any year**. |
| E7 | `git log --all --diff-filter=A` over `results/calibration/_nyiso180*` and `git ls-tree -r origin/main` | The only committed nyiso-180 outputs are `_nyiso180_st_gas_undispatch.json` and `_nyiso180_ramp_report.json`. **No `_nyiso180_unit_dispatch.json` exists in any commit on any branch.** The only `unit_hourly_*.parquet` tracked anywhere is NEISO's `neiso86_2022_corrected`. |
| E8 | `scripts/run_calibration_full.py::_unit_hourly_frame` docstring + call site `:5686` | `mc` and `red_cost` **are** written at HEAD, unconditionally, from `DispatchResult.gen_mc` / `gen_reduced_cost`. |
| E9 | `scripts/run_calibration_full.py::run_replay_bundle:8593` | A committed bundle's `meta.json` is the authoritative recipe; `--replay-bundle` re-solves it end-to-end. |

### 0.1 THE RECONCILIATION, and it is a result

The brief directs this session to reconcile with the parallel nyiso-180 lane (PR #4650) before
proposing anything. **E5–E7 settle what that lane delivered: the instrument and a complete
pre-registered probe, but NOT the adjudication.** Its per-unit sidecar columns are gitignored, so
they exist in no committed bundle; its probe hard-exits on a bundle that predates them; and its
output artifact was never produced. **Every prediction in `PREREG-nyiso180-per-generator-dispatch.md`
§2 — P-a, P-b, P-c, P-d, the §2.4 STOP — stands UNMEASURED**, which is exactly its own §5 S2 stop
condition ("the adjudication is handed forward **unmade**") having fired silently.

This session therefore does two things, and the order matters:

1. **Regenerate the instrument and execute the parallel lane's pre-registration verbatim.** A
   pre-registration fixed before the data existed, run by a session that did not write it, is the
   strongest evidential form available here. Its gates are **not restated or re-tuned** below:
   `nyiso180_unit_dispatch_adjudication.py` is run unmodified and its verdicts are reported at
   full magnitude whichever way they land.
2. **Add the gates that lane does NOT carry** — the degeneracy adjudication proper (§2). Its
   `degeneracy_control` block measures a **price margin** (`mc` within \$1 of `price`) and is
   explicitly a side-report, not a gated verdict. The reduced-cost test below is a different and
   stricter object, and it is this session's own.

**No bar from either lane is moved.** Where a tolerance is inherited it is named as inherited.

### 0.2 One correction to the object's own statement, made before measuring

The brief and the matrix describe *"a sustained ~1,000 MW LEVEL gap in 59–90 % of hours"*.
Against nyiso-179's own published annual figures (3.84 / 9.09 / 3.99 TWh) the implied mean is
**438 / 1,038 / 456 MW**. The **~1,000 MW characterisation is the 2024 figure**; 2023 and 2025 are
each under half of it. This is arithmetic on already-published numbers, not a new measurement, and
it is stated here so that no gate below is graded against an inflated object.

---

## 1. The instrument, and why it needs a replay

`red_cost[g,t]` is the LP's own optimality residual for a generation column:

    red_cost[g,t] = mc[g,t] − price[zone(g),t] + Σ_r a(r,g) · y_r
    Ω[g,t]        ≡ red_cost[g,t] − (mc[g,t] − price[zone(g),t])

`Ω` is exactly the net rent every **non-energy** row charges that unit-hour, with zero free
parameters. `sign(red_cost)` says which bound the column sits at: `> 0` lower, `< 0` upper,
`≈ 0` interior or **degenerate**.

Both columns exist at HEAD (E8) but in no committed bundle (E5–E6), so the instrument is produced
by a **bit-identical control replay of the keeper's own recipe** — `--replay-bundle` on
`nyiso177_vintage_B1p`, all three years, one invocation, years sequential (rules 12, 16). Per the
nyiso-180 precedent this is **an instrument, not a run: it is NOT registered on the dashboard**
(rule 15). Its `unit_hourly` output is gitignored and stays uncommitted; the probe's JSON is the
committed artifact.

---

## 2. Gates

### G-D — is the ITM-unrun MW DEGENERATE? **CAN FAIL, BOTH WAYS.**

Population: `ST_GAS` unit-hours with `mc ≤ price` — nyiso-179's own in-the-money definition,
**inherited, not chosen here**. Weight: `unrun[g,t] = max(cap_mw − mw, 0)` on that population;
`U = Σ unrun`.

A column at its lower bound with `red_cost ≈ 0` is **dual-degenerate**: the LP is indifferent to
dispatching it, an alternative optimal basis does dispatch it, and the objective is unchanged.
That is the precise LP meaning of "degeneracy at a price plateau", and it is measurable only from
the reduced cost.

Statistic: `Dshare(ε) = Σ_{|red_cost| ≤ ε} unrun / U`, reported over the ladder
ε ∈ {0.01, 0.10, 1.00, 5.00} \$/MWh, **in all three years**.

**Only the ε = \$1.00 rung decides.** The rung is fixed here, before measurement, and it is
**inherited**: \$1.00/MWh is `ITM_EPS_STRICT` in the parallel lane's already-committed probe. The
rest of the ladder is reported for sensitivity and **may not be substituted for the deciding
rung** — this is stated so that no rung can be chosen after seeing the answer.

**Verdict:**
* **`DEGENERACY-CARRIES`** iff `Dshare(1.00) ≥ 0.50` in **all three** years. An outright majority
  of the object is MW the LP is provably indifferent about.
* **`DEGENERACY-PARTIAL`** iff `Dshare(1.00) ≥ 0.50` in some years but not all.
* **`DEGENERACY-REFUTED`** iff `Dshare(1.00) < 0.50` in **all three** years. Then the stronger of
  the two surviving carriers is dead and the object is materially real MW held off by something.

**Pre-declared consequence of `DEGENERACY-CARRIES`, so that it cannot be re-read as a defect after
the fact:** the signature is then an **artifact of the ITM statistic**, not a dispatch defect, and
**the honest deliverable is retiring the statistic — NOT opening a lever.** This is registered in
advance as a legitimate result, per the brief.

### G-P — PRICE PLATEAU or a CHARGED ROW? **CAN FAIL.**

Degeneracy has two mechanically distinct sources and `Dshare` alone cannot tell them apart:
`red_cost ≈ 0` obtains either because `mc ≈ price` with nothing else charging, **or** because a
non-energy row charges `Ω` that exactly offsets a real margin. Only the first is a *price
plateau*; the second means a row is the carrier and merely happens to bind to indifference.

Within the deciding-rung degenerate MW (`|red_cost| ≤ \$1.00`), split on `Ω`:

* **plateau** MW: `|Ω| ≤ \$1.00` — no non-energy row charging.
* **charged** MW: `|Ω| > \$1.00` — a row is charging.

Statistic: `Pshare = plateau MW / degenerate MW`, per year.

**Verdict:**
* **`PLATEAU`** iff `Pshare ≥ 0.50` in **all three** years — the carrier is the flatness of the
  offer stack against the clearing price, and G-D's pre-declared consequence stands.
* **`CHARGED`** iff `Pshare < 0.50` in **any** year — a non-energy row carries it. **`Ω` is a SUM
  over rows and this session does NOT decompose it** (the parallel lane's §3 limit, inherited): a
  `CHARGED` reading names the magnitude of what to look for and hands the attribution forward
  **unmade**, never assigning it to a candidate by elimination.

### G-S — the SUCCESSOR statistic. **REPORT, CANNOT FAIL.**

If degeneracy is removed from the numerator, what is left is the MW genuinely held off its bound
by a row: `U_strict = Σ unrun over {mc ≤ price} ∧ {red_cost > \$1.00}`, in TWh/yr, against
nyiso-179's published 3.84 / 9.09 / 3.99. This re-sizes the object and is the concrete content of
"retiring the statistic". Descriptive; it adjudicates nothing.

### G-L — the LEVEL. **REPORT, CANNOT FAIL.**

Mean per-hour `ST_GAS` capacity within \$1/MWh of its zone's price, against the mean per-hour
ITM-unrun MW, per year. Checks §0.2's arithmetic against the LP's own offer and makes the *level*
claim in the object statement falsifiable by a reader. Descriptive.

### G-R — carrier 2, the reserve rows. **ONE-SIDED BY CONSTRUCTION. CAN ONLY IMPLICATE.**

Declared one-sided **in advance**, in the nyiso-180 G2 discipline, and this is a limitation of the
instrument rather than a softened bar: `Ω` is a sum over rows, the reserve rows' own duals are not
persisted, and `reserve_family`'s held MW is a per-family aggregate. A correlation between held
reserve and the un-run MW can **implicate** the shared-headroom row; it can **never exonerate** it.

Delivered by the parallel lane's own `reserve_overlay` (mean held MW, mean un-run MW, their ratio,
Pearson r), run unmodified.

* **`RESERVE-IMPLICATED`** iff mean held MW ≥ 0.50 × mean ITM-unrun MW **and** Pearson r ≥ 0.50 in
  any year.
* **`INCONCLUSIVE`** otherwise. **NOT an exoneration**, and must not be reported as one.

### G-I — INSTRUMENT CHECKS. **CAN FAIL, AND A FAILURE VOIDS EVERY GATE ABOVE.**

* **I1 — the replay is the keeper.** Hourly zonal prices in the replay must differ from the
  committed keeper's `system_<year>.parquet` in **0 of 52,560** cells, and `class_hourly` in 0 of
  122,640, in all three years — the figures nyiso-180 §8 published for this exact replay at this
  exact HEAD. Any non-zero count means the replay is not the keeper and **nothing below is
  measured on the keeper**: STOP.
* **I2 — the identity closes.** The parallel lane's §2.4 STOP population (strictly in the money,
  strictly inside its bounds, interior, and `|Ω| ≤ \$0.01`) must be **< 0.1 %** of class
  unit-hours. Larger means the sidecar is measuring something other than the LP that priced: STOP,
  no candidate adjudicated.
* **I3 — `price` is the dual.** The parallel lane's P-b: over interior `ST_GAS` unit-hours the
  median of `mc − price` is 0 to within \$0.01 and `|mean| ≤ \$0.05`. A displaced residual is a
  post-solve transform or an injection-side delivery factor of some origin: STOP.

I2 and I3 are **not this session's bars** — they are the parallel lane's, committed before its
data existed, and executed here for the first time.

---

## 3. What this session will NOT deliver — declared in advance

* **No decomposition of `Ω` into per-row terms.** The parallel lane's §3 limit is inherited
  verbatim. Any unattributed remainder is reported at full magnitude as unattributed.
* **No lever, in any branch.** `DEGENERACY-CARRIES` ⇒ retire the statistic. `DEGENERACY-REFUTED` or
  `CHARGED` ⇒ name the object and hand it forward. Neither is a mechanism.
* **Nothing that moves C1-2023, C3a-2025 or C3c.** The lane wall stands: nyiso-179 §7 puts 62.4 %
  of the 2025 top-decile `ST_GAS` deficit downstream of C3a-2025, which is owner-court
  (`DECISION-CARD-nyiso148-2025-level-remainder` Q1). **No `ST_GAS` offer lever is opened**, and
  if this work bottoms out against that wall it stops there and says so.
* **No re-opening of any DO-NOT-REDO cell**: the loss surface, the post-solve transform, the
  capacity/label-basis mismatch, `ramp_envelopes` as the dominant carrier, the
  measured-availability family, the merit guard, an `ST_GAS` duty curve, `gas_st_startup_cost`,
  `gas_st_committed_hr_mult`.

## 4. Stop conditions

* **S1** — any of I1 / I2 / I3 fails: the instrument is reported as failed, **no gate above is
  adjudicated**, and the finding says so.
* **S2** — the 3-year replay does not complete in this session's budget: the adjudication is
  handed forward **unmade**; nothing is inferred from a partial year and no single-year bundle is
  registered (rule 16).
* **S3** — **zero free parameters, zero swept bands, zero new mechanisms, zero `ScenarioConfig`
  fields.** This is an instrument-and-adjudication lane. If the result points at a lever, the
  lever is **named and handed forward**, never armed here.
* **S4** — the replay is a control and is **not registered** on the dashboard (rule 15, the
  nyiso-180 precedent). If no non-control solve is run, rule 15 registers nothing, and that is the
  correct outcome rather than a gap.

## 5. Governance

* **Rule 1 `[R-STRUCT]`** — no residual is consulted in choosing what to measure; no mechanism is
  adopted or rejected on whether it moves a fit.
* **Rule 13 `[R-MEASURED]`** — nothing is pinned to actuals. The replay is the keeper's own recipe
  and every quantity gated is a model-internal LP output.
* **Rule 14 `[R-ACCURATE]`** — no accurate input traded for an estimate; no input touched at all.
* **Rule 15** — the control replay is an instrument, not a run (§4 S4).
* **Rule 16 `[R-ALLYEARS]`** — one invocation, `--year 2023 2024 2025`, years sequential (rule 12).
* **Rule 19 `[R-ONE-MECH]`** — nothing added, so nothing to reconcile; nyiso-180 §7's sign/scope
  enumeration is inherited rather than re-derived.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched.** Nothing swept,
  nothing re-derived.
* **Rule 22 `[R-HOLDOUT]`** — every year is 2023 / 2024 / 2025. NYISO is absent from both
  `complete` and `final`; **no marker is requested**; the holdout spend freeze is untouched.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable**, no env-var knob, no gate flag.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only; only the NYISO matrix shard is edited.
* **Rule 27 `[R-PUSH]`** — no existing source file ≥ 300 lines is rewritten. The probe added here
  is a new file; the parallel lane's probe is run **unmodified**.
* **Rule 28 `[R-MECH-MATRIX]`** — the cells this session tests are annotated in the NYISO shard in
  this session, whichever way the gates land.
