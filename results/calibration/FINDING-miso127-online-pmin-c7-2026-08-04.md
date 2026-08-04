# FINDING — miso-127: C7 `COAL_PRB` moves for the first time, and the last take-or-pay budget lane closes by proof

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-04-miso-126-steampart-b` ·
**Keeper at exit:** **`2026-08-04-miso-127-onlinepmin`**
(`results/calibration/miso127_onlinepmin_B`), determination **NOT-YET**,
sole FAIL **C7 `COAL_PRB` — now 2025 only**, ledgered caveats 2/3 {C3a, C3c}.
`audit_keepers --iso MISO` **0 failures / 0 warnings**.

**Prereg (pushed BEFORE any arm solved and before any adjudicating statistic):**
`results/calibration/PREREG-miso127-takeorpay-period-budget-2026-08-04.md`
(merged to `main` as `318d9d0d` / `49cf0877`-adjacent).
**Runs registered (rule 15):** `2026-08-04-miso-127-onlinepmin-control` (arm A,
same-HEAD zero-delta control) and `2026-08-04-miso-127-onlinepmin` (arm B, the
keeper).
**Probes:** `scripts/probes/_miso127_budget_reshape_precheck.py` (no LP),
`scripts/probes/_miso127_online_pmin_ab.py` (no LP).
**Records:** `_miso127_budget_reshape_precheck.json`, `_miso127_online_pmin_ab.json`.

> **Label collision, recorded for the archive.** A **parallel session also carried
> the `miso-127` label** (commit `49cf0877`, "pre-register the overnight gas
> composition measurement"), on a different lane: no LP, no mechanism armed, no
> run registered. There is no mechanism-cell or bundle overlap with this session,
> and the run ids are distinct.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **A1** | does the model carry a per-plant PERIOD sunk volume? | the sole loader reads **only** `plant_code` + `contract_share`; `total_tons` never reaches the LP | **FALSIFIED → Lane A dies** |
| **A2** | is there headroom above the measured overnight minimum? | actual **0.039–0.074** of nameplate vs model **0.236–0.268** | **HOLDS** |
| **A3** | can a budget be built with no new tonnage level? | receipts = miso-103's refuted series; no contractual grain (miso-104); model-derived = **provably inert** | **FALSIFIED** |
| **A4** | is the direction feasible (plateau can rise)? | class not capacity-bound midday (mean peak 15.3 GW vs realized max 27.9 GW) | **feasible, moot** |
| **B1** | does `coal_mustrun_online_pmin` fire at two grains? | grain 1 **42 coal bins**; grain 2 COAL_PRB **−1.72/−2.07/−0.43 TWh** vs a 0.05 TWh bar | **LIVE** |
| **B2** | is the control zero-delta? | class-hour **0.000000 MW**, D-1 identical, scorecard identical | **PASS** |
| **B3** | does the full energy balance close? | **−0.023 / −0.056 / −0.018 GWh**, `Δdemand` exactly 0 | **PASS** |
| **B4** | does C7 move? | cv_ratio **0.465→0.514, 0.474→0.529, 0.314→0.347** | **2/3 cross; C7 still FAILS on 2025** |
| **B5** | does anything regress? | C1 **16/16** held, no criterion status change; COAL_BIT C1 +0.69 TWh worse; immaterial COAL_LIGNITE 2025 D-1 flips | **CHANGED, reported** |
| — | the outcome | summed C1 |error| **35.46 → 30.48 TWh**; C3a, C3b, C4 all improve | **promoted** |

---

## §1 — Lane A: the period-budget re-shaping, closed ex ante by proof

The chartered question was whether the take-or-pay sunk band — today a per-hour
constant discount pinning ~55 % of each regulated plant at VOM in all 8,760 h —
could be re-expressed as a **period energy budget the LP allocates across hours**,
priced by its dual, at the **same annual volume the model already carries**. The
charter's own distinction from the blocked miso-103 lane was that a
**budget-neutral re-shaping needs no new level**.

### §1.1 — the model carries no period volume at all

`market_sim.data.coal._derived_coal_takeorpay()` is the sole loader of
`data/raw/_processed-legacy/coal_takeorpay_MISO.csv`. Of its seven columns it
reads **exactly two**: `plant_code` and `contract_share`. `spot_share`,
**`total_tons`**, `n_receipts`, `source` and `breakdown` are **never read by any
model code**. The take-or-pay representation is a pure per-hour fuel-cost
fraction (`fuel_frac = 1 − contract_share`) applied to a capacity band.

So a budget construction must **introduce** a level. Three sources exist and all
three fail:

1. **`contract_share × total_tons`** — the only committed tonnage, and it is
   EIA-923 Schedule-5 **same-year delivered receipts**: precisely the series
   miso-103 refuted (log-space cross-section R² 0.87–0.94 against same-year burn;
   aggregate floor 0.96/1.14/0.98× actual; 2024 overshoots at 1.136×). This is the
   least disguised member of the DO-NOT-REDO family.
2. **Genuinely contractual ex-ante tonnage** — does not exist at plant grain across
   the 39-plant / 26-owner / 12-state target set (miso-104's sourcing pass; the
   standing ask).
3. **A level derived from the model's own realized volume** — the only candidate
   that introduces no *data*. It dies by proof.

### §1.2 — the volume-neutrality ⇒ inertness theorem

Let the control LP be `min c'x s.t. Ax = b, x ≥ 0` with optimum `x*`, and let
`g'x` be the sunk-fuel volume of the discounted band. Volume neutrality *without
new data* means setting the budget to the volume the model already carries,
`B := g'x*`. Add the budget row in any form — cap `g'x ≤ B`, minimum-take
`g'x ≥ B`, or two-tranche (first `B` units cheap, remainder full cost). In every
form `x*` satisfies the new row **with equality**, so `x*` stays **feasible**;
and every point feasible for the constrained problem was already feasible for the
unconstrained one, over which `x*` was optimal. Therefore `c'x ≥ c'x*` for all
such `x` and **`x*` remains optimal**. The solution is unchanged.

> **A volume-neutral budget is provably INERT.** To bind, the budget must sit
> strictly away from the model's own volume, and the size of that departure is a
> free parameter with no identification source (rules 21 `[R-DOF]` /
> 24 `[R-REGISTRY]`).

Setting `B` at the band's capacity ceiling is slack, hence inert for the same
reason. Sourcing `B` from **P0** to apply in **P1** does not escape it either: the
two solutions differ only by the amortized startup markup, so the budget's
binding-ness would be an artifact of that markup rather than of any contract.

**Consequence — this is the useful generalisation.** miso-103's blocker is not
incidental to one construction: **volume neutrality and non-inertness are mutually
exclusive**, so *any* budget re-shaping needs **external** tonnage by
construction. The Form 580 ask is not one route among several; it is the only one.
**No LP was built and no arm was solved for Lane A.**

### §1.3 — what Lane A did produce: the headroom measurement

Regulated (EIA-860 `Regulatory Status = RE`) MISO `COAL_PRB` plants in the
keeper's own committed CAMPD bench, overnight (h0–h05) load as a fraction of
nameplate, on **online days only** (a full-outage day is maintenance, not a
dispatch choice), capacity-weighted:

| year | n | nameplate | **actual** min / p05 / p50 | **model** min / p05 / p50 |
|---|---|---|---|---|
| 2023 | 27 | 28,373 MW | **0.058** / 0.203 / 0.435 | 0.251 / 0.286 / 0.516 |
| 2024 | 27 | 28,373 MW | **0.039** / 0.192 / 0.440 | 0.236 / 0.264 / 0.469 |
| 2025 | 26 | 28,372 MW | **0.074** / 0.255 / 0.518 | 0.268 / 0.367 / 0.567 |

The **p50s are close** — on a typical night the model is only modestly high. What
it lacks **entirely** is the **low tail**: reality reaches 4–7 % of nameplate,
the model never goes below ~24 %. This is miso-113's "the overnight distribution
is too NARROW" seen at plant grain, and it **quantifies the amplitude a
correctly-sized budget would have to recover**. It sharpens the ask rather than
merely closing a door.

---

## §2 — Lane B: the "probably inert" secondary item was the session's result

### §2.1 — the expected-INERT prior was refuted before any solve

`ScenarioConfig.coal_mustrun_online_pmin` sizes the coal must-run (cheap,
fuel-sunk) tranche from the measured **online** minimum stable load
(`thermal_tranches_MISO.csv` `mustrun_online_pct`) instead of the all-hours
available-CF P5 (`mustrun_pct`). That tranche has `Pmin = 0`, so it changes the
**size of the cheap bid band**, not a forced floor.

The field's docstring predicts the all-hours figure "reads ~2× high". **That was
measured on ERCOT and is false at MISO** — and the brief's expected-INERT prior
rested on it. Measured on the committed MISO artifact (44 coal plants,
41,770.8 MW):

| statistic | value |
|---|---|
| cap-weighted `mustrun_pct` → `mustrun_online_pct` | 28.886 % → **27.609 %** (ratio **0.9558**) |
| p50 (moves the **other** way) | 25.20 → **28.00** |
| **net** MW moved | **−533.1** |
| **gross \|MW\| moved** | **+7,528.1** |
| plants grow / shrink / flat | **20 / 19 / 5** |
| per-plant Δ (pp of nameplate) | min **−43.2**, p50 +0.1, max **+60.0** |

> **The net is a cancelling aggregate.** −533 MW is 1.3 % of the coal fleet;
> **7,528 MW gross is 18 %**. Declaring `I` on the net would have been exactly the
> boundary/denominator error the miso-119 / 122 / 125 DO-NOT-MISREADs warn
> against. **The pre-registration recorded the prior as wrong** and chartered the
> A/B rather than proceeding as if the zero-solve kill were available.

### §2.2 — firing proven at two grains

miso-126's first arm returned exactly inert because a fleet-sourcing flag was not
forwarded at the backcast's own inlined bin synthesis. That defect class was
checked **in source and then measured**, not assumed away:
`coal_mustrun_online_pmin` is **config-borne** — `run_calibration.py` sets it via
`config.with_overrides` (and `prb_overrides` at `:1429`), `fleet_to_bins(..., iso,
config)` receives the config, and `campd_bins.py:1645` reads it — so it never
crosses the `load_fleet_from_csv` keyword seam.

* **Grain 1 (pre-arm).** Calling `fleet_to_bins` directly, flag off vs on, over
  the MISO 2023 fleet: `pct_mr` changes on **42 coal bins** (gross 867.8 pp),
  `pct_econ` on **39** (gross 733.0 pp).
* **Grain 2 (post-arm).** `COAL_PRB` **−1.72 / −2.07 / −0.43 TWh** against a
  pre-registered 0.05 TWh bar, displaced by `CC_REGULAR`, imports and
  `COAL_LIGNITE`.

### §2.3 — the control is exactly zero-delta

Measured, not assumed (caiso-146 found an outgoing keeper's sidecars diverging by
3.2 GW on a class-hour at HEAD): arm A reproduces the keeper's class-hour dispatch
to **0.000000 MW** in all three years, its D-1 rows exactly (C7 FAIL included),
and its determination, all nine criterion statuses and ledgered caveats.
**Every delta below is therefore attributable solely to the flag.**

### §2.4 — what it does

Against the same-HEAD zero-delta control, never against the committed predecessor:

**C7 `COAL_PRB` — the target, and MISO's sole failing criterion:**

| year | control | arm B | |
|---|---|---|---|
| 2023 | 0.465 **FAIL** | **0.514 pass** | ✓ |
| 2024 | 0.474 **FAIL** | **0.529 pass** | ✓ |
| 2025 | 0.314 **FAIL** | 0.347 **FAIL** | short of 0.5 |

`profile_r` is **preserved** (0.988/0.978/0.971 → 0.987/0.974/0.972), so the gain
is **amplitude**, not a phase trade — which is exactly what the gate measures
(the h0–h14 window is a morning-ramp amplitude statistic). **C7 as a criterion
still FAILS, on 2025 alone, so the determination remains `NOT-YET`.**

**miso-102's two failure modes are both absent** — checked, not assumed:

* **C1 holds 16/16** (that arm collapsed it to 11/16).
* **`COAL_BIT` does not overshoot**: 0.704/0.596/1.114 → 0.667/0.565/**1.211**,
  against the 2.6–2.8× signature that condemned it.

**Everything else improves:**

| statistic | control → arm |
|---|---|
| summed C1 \|error\|, 16 scored rows | **35.46 → 30.48 TWh** (+4.98, ~14 %) |
| C1 `COAL_PRB` | 3.81 → **0.57 TWh** |
| C1 `COAL_LIGNITE` / `CT_PEAKER` / `CC_CHP` | 2.05 → 0.84 / 3.88 → 3.25 / 0.99 → 0.63 |
| C1 `COAL_BIT` (the one regression) | 7.96 → **8.65 TWh** |
| C3a mean LMP 2023 / 2024 | −1.4 % → **−1.0 %** / −6.6 % → **−6.3 %** |
| C3b NRMSE 2023 / 2024 | 0.075 → 0.074 / 0.116 → **0.112** |
| C4 coal r | 0.895/0.873/0.888 → **0.898/0.880/0.892** (NRMSE down every year) |
| C2 2025 coal / gas | +4.0 → +3.9 % / −10.7 → −10.6 % |
| max zonal \|ΔLMP\| | 3.165 / 8.375 / 2.886 $/MWh |
| system demand-wtd Δλ | +0.1387 / +0.1104 / −0.0029 $/MWh |

For scale: this is a **4.98 TWh** C1 improvement against the **1.74 TWh** that
promoted the incumbent keeper at miso-126.

**Diagnostic verdict changes are exactly three:** D-1 2023 and 2024 `COAL_PRB`
FAIL → pass (the target), and D-1 2025 `COAL_LIGNITE` pass → FAIL.
`COAL_LIGNITE` is **immaterial** (0.9–1.1 % of ISO load, under the 2 % gating
floor), so it is reported and **not gated** — and its 2023 row **improves
markedly**, 2.344 → 1.516, toward the measured 1.0.

### §2.5 — the boundary lesson, vindicated a second time

Prereg **B3** was written on the **full** balance identity precisely because
miso-126 §6 had been caught by the class-only form. It was right to be: the
**class-only** net delta is **−11.0 / −19.4 / −26.3 GWh**, which a naive
class-sidecar statistic would have failed outright. On the full identity
`Δclass + Δdischarge − Δcharge + Δslack − Δdump − Δdemand` the residual is
**−0.023 / −0.056 / −0.018 GWh** with `Δdemand` exactly 0. The lever legitimately
moves storage cycling and scarcity slack; the class sidecar is not the whole
balance.

---

## §3 — why this is a keeper

**Promoted on structural fidelity (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`), not
on a score.** `mustrun_online_pct` **measures** the online minimum stable load;
`mustrun_pct` is a **biased proxy** for that same quantity, inflated for an
always-online unit because its all-hours P5 sits inside its normal operating band
and the outage-derate denominator lifts the available CF. Replacing a proxy with
its measurand is the rule-14 move, and rule 14 would have kept it **even if the
fit had worsened**. That it also moves the target criterion in all three years is
corroboration, not the justification.

**Zero free parameters.** The flag is a boolean **selector** between two columns
that already exist in a committed artifact. No coefficient, threshold or
percentile is introduced by this session; the 95 % online-time percentile lives in
the frozen derive and is the incumbent's own convention. **Rule 23
`[R-FROZEN-DERIVE]` is not engaged** — no re-derive was performed, because the
MISO artifact already carried the column and only the solve was missing.
`n_residual` unchanged at 2.

**Rule 19 `[R-ONE-MECH]`:** nothing is stacked on the take-or-pay discount's
residual. This **re-sizes the band the discount applies to**; no floor is added
and the discount itself is untouched.

**Rule 25 `[R-ISO-SCOPE]`:** the flag is `K` on the PJM keeper and that verdict
**transfers nothing**. It entered MISO as `U` (rule 28(d)) and MISO's band is
derived from MISO's own CAMPD conduct via its own `thermal_tranches_MISO.csv`.

**Leave-one-year-out (rule 22):** the mechanism has **zero fitted parameters and
nothing year-specific** — the band is read per plant from CAMPD conduct, never
from any year's residual — so LOO reduces to per-year consistency, and the effect
is independently present and same-signed in **all three years** (C7 up 3/3, C1
error down 3/3). No single year carries the result.

**Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. MISO holds no `calibration-complete`
marker, so no out-of-training year was solved, scored **or read**, and the D-5(b)
re-key duty does not apply.

**The honest debit column,** since a promotion is not a clean sweep: `COAL_BIT`'s
C1 error worsens by 0.69 TWh and its 2023/2024 off-peak CV ratios drift down
(0.704→0.667, 0.596→0.565, still passing); the immaterial `COAL_LIGNITE` 2025
D-1 row flips to FAIL; and the system demand-weighted λ **rises** ~$0.11–0.14 in
2023/2024 (which happens to narrow MISO's ledgered C3a under-pricing, but is a
consequence, not a target). None of these is reverted, because reverting a
measured input to buy back a residual is precisely what rule 14 forbids.

---

## §4 — `coal_tranche_1/2/3_frac`: recorded, not swept

`coal_tranche_1/2/3_frac` (0.30/0.25/0.45) and their passthroughs are, per their
own declaration in `scenarios.py`, "calibrated to EIA-930 2023–2024 hourly
**ERCOT** coal dispatch" — a MISO-applied parameter fitted on ERCOT's residual,
flagged residual-identified in the DOF ledger with standing open **issue #1336**.
That is a live rule-25 `[R-ISO-SCOPE]` / rule-21 `[R-DOF]` debt sitting directly
on the C7 mechanism.

**It was not swept against the C7 residual** — that is the forbidden fitted path
(rules 1, 24). Re-grounding it on MISO's own measured contract-share data would be
a rule-14 re-derive needing **its own** pre-registration and citing a **source-data**
change (rule 23). It is recorded here as the named open DOF item.

---

## §5 — for the next session

1. **C7 `COAL_PRB` is now a 2025-only failure** (0.347 against the 0.5 gate) and
   is the named successor. 2025 is the year with the **lowest actual** off-peak CV
   (0.074) *and* the lowest model CV (0.026) — a level-of-variability question in
   the year the fleet cycled least. It is **not** a sizing knob on this mechanism:
   do not re-sweep `coal_mustrun_online_pmin` (rules 1 / 24).
2. **The take-or-pay budget family is closed by proof** (§1.2). Do not re-charter
   any budget / minimum-take / two-tranche form until a source clears
   `docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §4. The bounded
   next step there remains a **sourcing** pass (ask §8: count 1:1 contract-plant
   Form 580 coal contracts covering 2023 for the 26 target owners), not a solve.
3. **The headroom numbers in §1.3 belong in that ask.** They convert it from "we
   would like tonnage" to "here is the measured low tail — 4–7 % of nameplate
   against a model floor of ~24 % — that a correctly-sized budget must recover."
4. **`coal_tranche_1/2/3_frac` (#1336)** is the standing DOF debt on this
   mechanism, and re-grounding it is a legitimate lane with its own prereg.
5. **Method note.** The session's whole result came from refusing a
   pre-declared zero-solve kill: the brief's expected-INERT prior was correct on
   the aggregate it named and wrong on the fleet, and the difference was a
   **cancelling aggregate** (net −533 MW vs gross 7,528 MW). Reporting the prior
   as refuted, rather than honouring it, is what turned a phantom queue item into
   MISO's first movement on C7.
