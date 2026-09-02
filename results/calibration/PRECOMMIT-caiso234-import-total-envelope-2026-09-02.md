# PRECOMMIT — caiso-234: the TOTAL import-envelope estimator for CAISO's four ungrounded SPOT depths

**Registered 2026-09-02, session caiso-234. Branch
`claude/caiso-import-total-envelope-dnvmx0`, cut fresh from `origin/main`
(`a2e80dbf`).**

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`**, determination
**NOT-YET**, **C3a the SOLE load-bearing FAIL** (+4.1 / +12.5 / +15.6 %); C3c the
single ledgered caveat; C6 attested; C8 PASS. CAISO holds **no `complete` and no
`final` marker**; the holdout spend freeze is **ACTIVE**. Every read in this
session stays inside **2023–2025**.

---

## §0 — ESTIMATOR ORDER AND THE FORKING-PATH DISCLOSURE

**This document is registered BEFORE the derivation is executed, not merely
before the solve.** That is a deliberate tightening on caiso-233, whose §3 could
honestly say only that its thresholds were fixed in the script before the script
ran. Here the whole estimator — gated object, thresholds, placement convention,
and stop condition — is committed and pushed first, because this is a **second
estimator on data a first estimator has already been run against**, and that is
the exact condition under which pre-registration stops being a formality.

**§0.1 — caiso-233 ran first, and FAILED.** On 2026-09-01 the straight NEISO port
(per-corridor p98 with the MIC firm block carved out of each corridor, scarcity as
p99.9-minus-summed-rungs) failed **both** of its pre-registered gates: per-rung
year-stability at `PNW_midC` CV **0.253** and `WECC_scarcity` CV **0.550** against
a 0.20 bar, and LOYO at **40.1 % / 491.7 % / 57.9 %** against a 25 % bar. Its stop
condition fired; no LP was built. That estimator is **DO-NOT-REDO**
(FINDING-caiso233 §F4) and is not re-run here.

**§0.2 — THIS estimator was pre-specified in caiso-233 §F, before any of its own
numbers existed.** The committed text, verbatim (§F item 3):

> **Gate the quantity that is actually identifiable.** The measured record
> identifies the **total** envelope (CV 0.056) far better than any per-rung split;
> an estimator whose gated object is the total, with rungs placed by a fixed
> zero-DOF convention inside it, is the NYISO precedent and is the obvious next
> candidate — **pre-registered before it is run**, not selected after seeing which
> estimator passes.

with §F1 ("do not carve the firm block out of the measured depth") and §F2 ("do
not define scarcity as a residue … size it directly … e.g. the p99.9−p98
*interval*") fixing the two construction changes. This session executes that
specification; it does not choose it.

**§0.3 — WHAT IS ALREADY SEEN. Stated against interest, because it materially
weakens one of the two gates.** caiso-233 committed the per-year total-corridor
percentiles in `results/calibration/_caiso233_import_depth_decomp.json`:
p98(TOTAL) = 7,872.52 / 7,804.84 / 8,844.88 and p99.9(TOTAL) = 9,630.02 /
9,111.67 / 10,434.92 MW. Consequently:

* **CV(routine_total) = 0.0581 and CV(p99.9 total) = 0.0560 are ALREADY PUBLISHED
  in that JSON and already known to clear the 0.20 bar.**
* The scarcity **interval** CV is a hand calculation on those same six committed
  numbers, and I did it before writing this document: intervals 1,757.50 /
  1,306.83 / 1,590.04 MW, **CV ≈ 0.12**, also clearing 0.20.

**So G-STABILITY is foreseen, carries little evidential weight here, and is NOT
claimed as an unseen test.** It is retained because dropping a gate after seeing
it pass would be its own forking path, but no part of this session's argument may
rest on it.

**§0.4 — WHAT IS GENUINELY UNSEEN.** A percentile of a pooled multi-year sample is
**not** a function of the per-year percentiles, so nothing in the committed record
determines: any pooled percentile; the entire **G-LOYO** leg (which is computed on
pooled two-year samples); the pooled corridor weights; or any delivered rung value.
**G-LOYO is the load-bearing gate.** It is the gate that killed the price limb
(30.5 % at caiso-86b) and the caiso-233 port (491.7 %), and it is unseen here.

**§0.5 — THE GATED OBJECT CHANGED, and that is the honest objection to this
session.** caiso-233 gated the four per-rung capacities; this gates the **total**.
That is a **weaker test**, and moving the gated object after a failure is the
classic shape of gate-shopping. Two things answer it, and neither is a claim that
the objection is void:

1. The change was **specified in advance by the failed session itself**, in
   committed bytes (§0.2), on stated structural grounds (§F1/§F2/§F3) rather than
   on which object passes.
2. **§5 reports the stricter test anyway.** The per-rung stability and per-rung
   LOYO under the new placement are computed and published at full magnitude in
   the FINDING whatever they say, so a reader who rejects §0.5(1) can apply
   caiso-233's own bar to this ladder and reach their own verdict from the
   committed artifacts.

**§0.6 — BUDGET: TWO ESTIMATORS. THERE IS NO THIRD.** If the gates below fail,
this session files the FINDING, does not solve, and **escalates the DOF to the
owner as a standing item** with FINDING-caiso233 §E's measured over-depth bound as
the record. A third estimator on the same three years would be estimator-shopping
and the FINDING must say so in those words.

## §1 — THE OBJECT

Unchanged from FINDING-caiso233 §A — the four `IMPORT_TRANCHES["CAISO"]` SPOT
capacities (`src/market_sim/model/interchange/spec.py:349`), which
`scripts/probes/_caiso186os_dof_repair.py` labels **`RESIDUAL (static, no cited
primary source)`** and which caiso-191 desk-adjudicated:

| rung | MW | limb |
|---|--:|---|
| `PNW_midC` | 1,800 | SPOT — **ungrounded** |
| `DSW_CCGT` | 1,800 | SPOT — **ungrounded** |
| `DSW_CT` | 2,200 | SPOT — **ungrounded** |
| `WECC_scarcity` | 3,000 | SPOT — **ungrounded** |
| | **8,800** | |

`PNW_hydro_base` (1,072 / 1,558 / 1,566) and `DSW_solar_PV` (1,251 / 1,813 /
1,805) are the MIC-measured, per-year FIRM pair and are **held FIXED throughout**
— re-opening a grounded rung to move a residual is rule 1 `[R-STRUCT]`.

## §2 — THE GATED OBJECT (pre-registered)

Two components, both **direct statistics of the TOTAL corridor net-import
distribution** (`WECC_PNW + WECC_DSW`, EIA-930 CISO interchange on the model
clock via `corridor_net_import` / `CAISO_CORRIDOR_DIBA`, imported from
`scripts/data/derive_caiso_import_tranches.py`, not re-implemented):

    routine_total     = p98  ( TOTAL net import )
    scarcity_interval = p99.9( TOTAL ) - p98( TOTAL )
    ladder_total      = routine_total + scarcity_interval  =  p99.9( TOTAL )

* **No firm carve-out enters the gated object** (§F1). The firm block sits
  *inside* the derived total; the CV-0.16 DMM/MIC measurement never touches the
  gated statistic.
* **Scarcity is an INTERVAL, never a residue** (§F2). The residue form was a
  2.0–10.3 % remainder of a ~9 GW minuend with 9.8× CV amplification that also
  double-counted the 0.5–1.1 GW simultaneity gap.
* Percentile constants `CAP_PCTL = 98.0` / `SCARCITY_PCTL = 99.9` are carried
  **unchanged** from `derive_caiso_import_depths.py`, which took them from the
  NEISO precedent. **Not settable by this session.**

## §3 — PRE-REGISTERED HONESTY GATES

The same constants the price limb was held to and failed
(`derive_caiso_import_tranches.py` `CV_MAX` / `LOYO_MAX`, already on `main`):

* **G-STABILITY** — CV across 2023 / 2024 / 2025 of **each** of `routine_total`
  and `scarcity_interval` ≤ **0.20**. *(Foreseen — see §0.3.)*
* **G-LOYO** — derive both components on the pooled other two years, predict the
  held-out year's own values; worst held-out relative error ≤ **0.25**.
  *(Unseen — the load-bearing gate, see §0.4.)*

Both must pass. Neither is softenable.

## §4 — PLACEMENT CONVENTION (ZERO DOF; fixed HERE, before execution; NOT gated)

The rungs are placed inside the gated total by a convention with **no free
parameter**. Every step is mechanical:

**(a) Corridor weights.** `w_c = p98_pooled(c) / Σ_c p98_pooled(c)`. This is the
pro-rata reconciliation of the two marginal corridor depths to the coherent
total, and it is the direct implementation of §F2's objection: summing marginal
p98s over imperfectly correlated seams (pooled hourly r = **+0.484**) over-provisions
routine depth by the measured **969 / 1,126 / 514 MW** simultaneity gap. Scaling
the marginals to the p98 of the total removes exactly that gap. Zero parameters.

**(b) Corridor routine depth.** `routine_c = routine_total × w_c`, then
`spot_routine_c = max(0, routine_c − firm_c)`, where `firm_c` is the mean over the
pooled years of the committed per-year measured MIC firm block
(`IMPORT_TRANCHES_BY_YEAR`). *(The subtraction is unavoidable — the firm rungs are
fixed and must sit inside the total — but it is now a **placement** step, not the
gated statistic. §5 publishes what it does to the per-rung numbers.)*

**(c) Within-corridor split.** Equal MW among that corridor's spot rungs —
`WECC_PNW` → (`PNW_midC`); `WECC_DSW` → (`DSW_CCGT`, `DSW_CT`). The NYISO/NEISO
equal-MW rung convention (`derive_nyiso_import_tranches.py`,
`NYISO_CT_base`/`_peak`). The split point is **fixed by the convention, never
chosen**.

**(d) Scarcity.** `WECC_scarcity = scarcity_interval`, on its **incumbent node**
(PALOVRDE / `WECC_DSW`). Placement unchanged; only the depth is derived.

**(e) Rounding** to 5 MW (`_round_cap`, NEISO convention).

**(f) PRICES ARE UNCHANGED.** This is a capacity-limb derivation only. The price
Q-Q route is **DO-NOT-REDO** — `derive_caiso_import_tranches.py` failed LOYO at
30.5 % (caiso-86b).

**(g) POOLED 2023–2025 → ONE STATIC ladder**, the same convention the incumbent
entry already uses ("this static entry is the POOLED derivation … backcast years
use `IMPORT_TRANCHES_BY_YEAR`"). The FIRM rows of every by-year entry stay at
their measured per-year values.

## §5 — REPORTED AT FULL MAGNITUDE, NOT GATED

The FINDING will publish, whatever they say, and without re-scoping anything on
the strength of them:

1. per-year implied rung capacities under the §4 placement, and their CV;
2. per-rung LOYO under the same placement — i.e. **caiso-233's own bar applied to
   this ladder**;
3. the per-year corridor weights `w_c`;
4. delivered vs incumbent, per rung and in total.

Committing in advance to publishing (2) removes the option of not looking.

## §6 — STOP CONDITION (pre-registered)

If **either** gate in §3 fails: **file the FINDING and do NOT solve.** Do not
soften a threshold. Do not re-scope the gated object to whichever component
passes — caiso-233 §D refused a passing `DSW_CCGT`/`DSW_CT` pair on exactly this
ground, its CV 0.026 being an arithmetic cancellation rather than stability. Do
not fall back to a residual-tuned depth. **Do not try a third estimator** (§0.6):
escalate the DOF to the owner as a standing item.

## §7 — PRE-REGISTERED SOLVE DESIGN (reached ONLY on a gate PASS)

* **A0 control** — `--replay-bundle results/calibration/caiso231_b1_ungrounded` at
  this HEAD, isolating the delta from HEAD drift.
* **B1 treatment** — the same, plus the derived depths as the **ONLY** delta,
  armed by a new **default-off** `ScenarioConfig` gate
  **`caiso_import_depth_measured`** so both arms run at ONE HEAD and the incumbent
  literals stay untouched for every other lane. Rule 28(c): its base
  mechanism-matrix row plus a cell line in **every** ISO shard land in the same
  PR; the CAISO cell verdict (rule 28(b)) is this session's to move.
* `--year 2023 2024 2025` in **ONE invocation, years sequential** (rules 12/16);
  the two invocations launched concurrently (rule 12's cap of 2 for CAISO's
  per-plant multi-zone LP). Scored on **P1**. **Both arms registered** (rule 15).

## §8 — PRE-REGISTERED C3a DIRECTION AND MAGNITUDE

Baseline (committed artifacts, `2026-09-01-caiso-231-b1-ungrounded`):
**2023 +4.1 % (pass) / 2024 +12.5 % FAIL / 2025 +15.6 % FAIL.**

* **DIRECTION (the falsifiable claim): NEGATIVE in all three years.** The derived
  ladder is *shallower* than the incumbent (FINDING-caiso233 §E: the incumbent
  stack is **1,493 / 3,059 / 1,736 MW deeper** than the measured p99.9 total
  envelope), so B1 removes above-market import depth; FINDING-caiso232 §D measures
  corr(monthly residual, model import volume) = **+0.419**, so less import volume
  must move λ **down**.
* **MAGNITUDE: |ΔC3a| ≤ 3 pp per year.** FINDING-caiso202 §C attributes **< 5 %**
  of the C3a positive gap directly to the import legs on the per-hub-priced
  keeper. **A depth change cannot close C3a and is not meant to.**
* **CHANNEL CHECK (pre-registered, so a null is not re-interpreted after the
  fact).** The keeper runs `caiso_corridor_flow_limit=True`, so each corridor's
  import is already clipped hour-by-hour at its measured (month × hour-of-day)
  p95 deliverability envelope, and both corridors sit far inside their physical
  link TTCs (COI ≈ 4,800 MW; Path-46/WOR ≈ 10,623 MW). **A near-zero ΔC3a with
  substantially unchanged model import volume is therefore an ADMISSIBLE and
  ANTICIPATED outcome** — it means the measured envelope binds before the rung
  depth does, and the derivation is a structural regrounding with no residual
  signature. That is **keeper-eligible, not a failure**. A move **larger** than
  3 pp means the mechanism is acting through an undeclared channel: **diagnose it,
  do not bank it.**
* **This is a DOF-closure lane, not a residual lane.** Per rule 1 `[R-STRUCT]` the
  derivation is **never** weighed against the price residual: a C3a regression does
  not veto a grounded depth, and a C3a improvement does not license an ungrounded
  one. The owner's standing standard applies verbatim — *"If structural integrity
  improves but gates regress that may still be a keeper."*

## §9 — OUTCOME (recorded 2026-09-02, same session)

**THE STOP CONDITION FIRED.** G-STABILITY passed and G-LOYO **FAILED**:

* **G-STABILITY ok** — `routine_total` CV **0.058**, `scarcity_interval` CV
  **0.120**, both inside the 0.20 bar. **This is the foreseen leg** (§0.3
  pre-disclosed the hand calculation "CV ≈ 0.12"; the script returned 0.120), so
  nothing rests on it.
* **G-LOYO FAIL** — worst held-out error **34.2 %** against the 25 % bar, on
  `scarcity_interval` with 2024 held out (folds: 7.0 % / **34.2 %** / 11.5 %).
  **This was the load-bearing, genuinely unseen leg (§0.4), and it failed.**

**No LP was built and no solver was called.** §7's arms were never run, so there
is nothing to register. The bar was not moved, the gated object was not re-scoped
to the passing component — and `routine_total` *did* pass both gates cleanly
(CV 0.058, LOYO ≤ 11.5 %), so that refusal was a live one, made under §6 and
recorded in the FINDING §C against interest.

**The two-estimator budget is SPENT (§0.6). No third estimator was attempted.**
The DOF ledger entry `spot_capacity` stays **OPEN** and is escalated to the owner
as a standing item.

**One correction to this document, against interest.** §0.5 anticipated the
gate-shopping objection and answered it. Execution surfaced a **stronger** form of
that objection, unknown when this was written: the caiso-233 and caiso-234
estimators are **algebraically constrained to deliver the same total**
(both reduce to `p99.9(TOTAL) − Σ firm` = 7,062 MW), so gating the total gated
their common ground and left ungated exactly the split caiso-233 failed on. It is
moot in outcome — the estimator failed anyway — but it is recorded at full
strength in FINDING §E rather than left to the reader to notice.

Full result, the failure decomposition, the §5 diagnostics published as promised,
and the owner escalation:
`FINDING-caiso234-import-total-envelope-2026-09-02.md`.
