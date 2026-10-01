# G-41 decision memo — PJM hindcast invariant I7 ("floor doesn't force-build")

_2026-07-06 · owner decision requested · scope: define invariant I7, not fix the harness_

**One-line ask:** Decide whether forecast invariant **I7** asserts an **absolute**
planning-reserve-margin floor (model must force-build up to it) or a
**retirement-bounded** floor (model must only avoid over-retiring below it). This
memo frames the choice; it changes **no code** and touches **no gate register**.

Owner sign-off is a single yes/no at the bottom.

---

## 1. Problem statement

### What I7 asserts today
`scripts/check_forecast_invariants.py::check_i7_reliability_floor` (lines 399-419)
asserts, for every solved evolution year:

```
thermal_nameplate  ≥  (peak − firm_clean) × (1 + margin) − slack
```

with `margin = 0.15` (hardcoded `Thresholds.reliability_reserve_margin`),
`firm_clean = hydro nameplate only` (`FIRM_CLEAN_FUELS = {"hydro"}`), and
`thermal = {gas_cc, gas_ct, gas_st, gas_cc_ccs, coal, oil, nuclear}` counted at
**nameplate**. It is an **absolute** floor: the RHS depends only on peak load and
firm-clean capacity, never on what the fleet started at or what retired.

### The observed FAIL (PJM 2021→2025 realized hindcast)
Bundle `results/hindcast/pjm-2021-2025-realized/PJM/df18e9c13581a99f`, post the
2026-07-05 demand-defect repair (which cleared the old `2.47e9 MW` data-artifact
version of this FAIL):

```
[FAIL] I7  2021: thermal 170918 < floor 172028 MW   (gap ~1.1k MW)
           2025: thermal 180821 < floor 184644 MW   (gap ~3.8k MW)
```

A small, **real** ~1–4k MW shortfall — the model's post-evolution thermal fleet
sits just under the absolute floor in the first and last scored years.

### Why this is a definition question, not a harness bug
The checker is arithmetically correct and the input data is now clean (I1-I6,
I8-I14 all PASS). The FAIL reflects a genuine model behaviour, documented as
finding **F1** in `docs/forecast-invariant-findings.md`:

> The economic-retirement reliability floor (`capacity.apply_economic_retirements`
> → `_apply_reliability_floor`) only **prevents over-retiring** below
> `(peak − firm_clean) × (1 + PRM)`; it does **not force-build up to it**, and the
> force-building backstop (`reserve_margin_build_enabled`,
> `apply_reserve_margin_build`, step 6 of capacity evolution) is **off by default**
> (`config/scenarios.py:669`). So a forecast whose starting thermal fleet is
> already below the floor stays below it, and I7 (an absolute floor) FAILs.

Nothing is broken. The model does exactly what it is configured to do. The open
question is **what the invariant should mean** — and per rule #1 that must be
answered by which definition mirrors the real market mechanism, never by which
one turns the line green.

---

## 2. The two options

### Option A — Absolute floor (model force-builds to the requirement)
I7 keeps its absolute form; the **model** is made to satisfy it by enabling the
adequacy backstop that already exists in code.

- **Code delta.** `apply_reserve_margin_build` (`model/capacity.py:2143`) already
  force-builds the cheapest firm resource (`gas_ct`) to close
  `resolve_adequacy_requirement_mw − accredited_firm_capacity_mw`, capped at the
  ISO's interconnection-queue throughput. It is a pure no-op today because
  `config.reserve_margin_build_enabled` defaults `False` (`scenarios.py:669`).
  The change is flipping that default **on for the capacity-evolution path** —
  see §4 for why this must be **gated by market design**, not a global flip.
- **Effect on the ~1–4k MW gap.** Closed. Step 6 builds `gas_ct` firm MW to the
  adequacy requirement each year; thermal rises to meet the floor and I7 PASSes.
- **Does it PASS honestly?** Yes *if and only if* the backstop is enabled because
  it is the right structure, not to move the residual — and *if* the checker's
  floor accounting is first reconciled with the model's requirement (see the
  caveat below). Enabling a real adequacy mechanism is legitimate under rule #1.
- **Rule #1 / methodology consistency.** The backstop **is** the ReEDS/NEMS/CDR
  structural adequacy mechanism (its own docstring, `capacity.py:2151-2160`).
  Methodology §5.1 step 6 lists it as a real evolution step; it is default-OFF
  today only as a byte-identity safety valve, and its own config comment already
  says *"recommended on for forecasts"* (`scenarios.py:676`). Turning it on for
  the ISOs whose market design actually procures to an adequacy target is
  structurally faithful, not a fitted pass.
- **Caveat that makes-or-breaks the "honest" claim.** I7's floor uses a *different
  counting convention* than the model's requirement: I7 counts **nameplate**
  thermal, treats **only hydro** as firm-clean, ignores wind/solar/storage
  entirely, and hardcodes a **0.15** margin. The model's requirement
  (`resolve_adequacy_requirement_mw`) uses **UCAP/ELCC accreditation**
  (`accredited_firm_capacity_mw`, thermal derated by EFORd, wind/solar/storage at
  ELCC) against **peak × (1 + PJM IRM = 0.178)** on PJM's ICAP→UCAP basis. If the
  backstop is enabled without reconciling these, the model will build to satisfy
  **its own** requirement while the checker measures a **different** floor — the
  model could still FAIL I7, or PASS it only by coincidence. Building the model to
  satisfy a checker that measures a different quantity is precisely the
  goalpost-moving rule #1 forbids. **Option A is only legitimate once the checker's
  I7 floor is put on the same convention as the model's adequacy requirement**
  (share `resolve_adequacy_requirement_mw` / the accredited-capacity ledger rather
  than the crude nameplate proxy).

### Option B — Retirement-bounded floor (weaken the invariant)
I7 is redefined to assert only that evolution did not **over-retire** below the
floor — the model is responsible for backfilling what retirements removed, but a
fleet that *started* below the floor is tolerated:

```
thermal_after  ≥  min(floor, thermal_before) − slack
```

- **Code delta.** A **harness** change in `check_forecast_invariants.py` (not
  `capacity.py`): I7 compares against `min(absolute_floor, prior-year thermal)`.
  No backstop default flip; `capacity.py`/`scenarios.py` behaviour is unchanged.
  (The model-side analogue — making the retirement floor's *target* explicitly
  retirement-relative — would be the `capacity.py` version, but the retirement
  floor already **is** retirement-bounded by construction; the only thing that
  currently claims an absolute floor is I7 itself.)
- **Effect on the ~1–4k MW gap.** The gap is not closed — it is **reclassified as
  acceptable**. I7 PASSes because the PJM fleet started thermal-short and
  evolution did not push it further below.
- **Does it PASS honestly?** Only if the retirement-bounded floor is the
  *physically more correct* statement of what the model should guarantee. If it is
  chosen because it is "always satisfiable" (F1's own words) — i.e. because it can
  never FAIL — that is redefining the test to pass, which rule #1 forbids.
- **Rule #1 / methodology consistency.** Defensible *only* for a market design
  with no absolute adequacy floor. It is the **correct** invariant for energy-only
  **ERCOT**: the real ERCOT has no reliability floor — an under-remunerated unit
  exits (~0.5–2 GW/yr observed), reserves tighten, and ORDC prices the scarcity
  (this is exactly the rationale already encoded in `market_design_retirement_floor`,
  `scenarios.py:679-697`). It is **not** correct for PJM, whose RPM/BRA procures to
  an absolute Installed Reserve Margin.

---

## 3. Recommendation

**Adopt the absolute floor (Option A) for capacity-market ISOs, and the
retirement-bounded floor (Option B) for energy-only ISOs — i.e. make I7's
definition market-design-dependent, mirroring the mechanism that actually clears
capacity in each ISO.**

Rationale, grounded in the real mechanism (rule #1):

- **PJM's RPM is an absolute-IRM procurement.** PJM's Base Residual Auction clears
  capacity to a fixed Installed Reserve Margin (17.8% for 2025/26, already in
  `PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]`). The market *does* force capacity to an
  absolute floor — via capacity payments that retain the marginal survivor and pull
  new entry. The model's `apply_reserve_margin_build` gas_ct backstop is the LP
  analogue of that procurement. For PJM the **absolute** floor is the physically
  faithful invariant, and a model that sits ~1–4k MW under it is under-modelling
  RPM-driven retention/entry — a real gap to close, not a threshold to relax.
- **ERCOT is energy-only.** No RPM, no absolute floor; the retirement-bounded
  statement is the faithful one there. A global absolute floor (or a global
  backstop flip) would be structurally *wrong* for ERCOT — it would manufacture
  firm MW the real ERCOT market never procures. The codebase already draws exactly
  this line for the retirement floor via `market_design_retirement_floor` and
  `MARKET_DESIGN[iso].capacity_market`; I7 and the backstop default should follow
  the **same** gate.
- **Legitimacy test.** Changing an invariant's definition to make a test pass is
  illegitimate **unless the new definition is the more physically correct one.**
  Here the split passes that test: absolute-for-capacity-market and
  retirement-bounded-for-energy-only is *more* correct than today's one-size
  absolute floor, independent of what it does to any residual. Enabling the PJM
  backstop is justified by RPM's design, not by the ~1–4k MW number.

Two hard preconditions on the Option-A half (without these it becomes
goalpost-moving, not a fix):

1. **Reconcile the checker's I7 floor with the model's adequacy requirement**
   (UCAP/ELCC accreditation + per-ISO IRM, via `resolve_adequacy_requirement_mw`)
   before or with the backstop flip. Do not leave I7 measuring a nameplate/hydro-
   only/0.15 proxy while the model builds to a UCAP/17.8% target.
2. **Gate the backstop default by `MARKET_DESIGN[iso].capacity_market`**, not a
   blanket `reserve_margin_build_enabled = True`. ERCOT stays off.

### Owner decision requested (crisp yes/no)

> **Adopt market-design-dependent I7:** absolute floor + default-on adequacy
> backstop for capacity-market ISOs (PJM/MISO/NYISO/NEISO/CAISO); retirement-
> bounded floor + backstop-off for energy-only ERCOT — conditioned on first
> reconciling the checker's I7 floor accounting with the model's UCAP/ELCC + per-
> ISO IRM adequacy requirement.  **YES / NO**
>
> If NO, fallback preference: **B (retirement-bounded everywhere)** — cheaper, but
> under-models PJM RPM and should be logged as accepted debt, not a closed gap.

---

## 4. Implementation sketch (do NOT implement until signed off)

Owned by lane **L-7** (`model/capacity.py`, hindcast harness). Once decided:

- `config/scenarios.py` — do **not** flip the bare `reserve_margin_build_enabled`
  default. Instead resolve it per market design in the capacity-evolution path
  (`runner.py` step 6, `capacity.py:2793-2799`): default-on when
  `MARKET_DESIGN[iso].capacity_market` is truthy, off for energy-only ERCOT.
  Keep the explicit `ScenarioConfig` field as an override (rule 21 — every knob on
  the config), so a scenario can still force it either way and it lands in
  `run_config.json`.
- `model/capacity.py` — no change to `apply_reserve_margin_build` itself (it is
  ready); only the resolution of whether it fires. Confirm the queue-cap
  (`QUEUE_CAP_GW`) does not throttle the ~1–4k MW PJM fill below the requirement in
  a single year.
- `scripts/check_forecast_invariants.py` — (a) branch `check_i7_reliability_floor`
  on market design: absolute floor for capacity-market ISOs, `min(floor,
  thermal_before)` for energy-only; (b) replace the nameplate/hydro-only/0.15
  proxy floor with the model's `resolve_adequacy_requirement_mw` +
  `accredited_firm_capacity_mw` convention so checker and model measure the same
  quantity. Do **not** widen any threshold to green the line (rules 1/11/14).
- Re-run the PJM (and ERCOT) hindcast + `check_forecast_invariants.py`; expect I7
  PASS on PJM via force-build and on ERCOT via the retirement-bounded branch.
- Update F1/F2 in `docs/forecast-invariant-findings.md` and close G-41 on the gap
  register with the chosen definition recorded.

## 5. Holdout & scoring implications

- **No backcast keeper is touched.** I7, the retirement floor and the backstop all
  live in **capacity evolution**, which runs only in **forecast mode**. Backcasts
  perform no capacity evolution (the fleet is fixed to the vintage), so no backcast
  keeper, dashboard bundle, or MAE re-gate is triggered by this change. This is a
  forecast-side change end-to-end.
- **Re-run obligations are forecast-side only:** the PJM/ERCOT hindcast bundles,
  the `check_forecast_invariants.py` I7 line, and any forecast band / PB ensemble
  whose capacity path depends on step-6 builds must be regenerated. Those are
  forecast deliverables, not keeper re-scores.
- **No holdout is disturbed.** The PJM hindcast spans 2021→2025 with **2022 as a
  never-solved quarantine bridge** (rule 22) and 2023–2025 scored. Enabling the
  backstop changes the *evolved* (non-solved) 2022 fleet and the 2023–2025 solved
  path, but this is forecast-mode capacity evolution, **not** a backcast solve or a
  scoring of measured actuals — it does not touch the 2022 / H1-2026 solve
  quarantine and does not trip the `quarantine-gates` CI job (all solve years stay
  within 2021–2025, none of them a quarantined backcast). No new holdout is
  consumed.
- **Rule-1 discipline for the record:** the backstop flip is justified by PJM
  RPM's absolute-IRM procurement, **not** by the fact that it makes I7 green. If a
  future session ever finds the absolute floor makes the *forecast* look worse on
  some other axis, that is a root-cause signal to investigate — not license to
  revert to the retirement-bounded floor for PJM.

---

_Files that would change once decided (not changed here):_
`config/scenarios.py` (backstop default resolution), `model/capacity.py`
(step-6 gating only), `scripts/check_forecast_invariants.py` (I7 branch + floor
reconciliation), `docs/forecast-invariant-findings.md` (F1/F2), gap register
(G-41 close). This memo edits none of them.
