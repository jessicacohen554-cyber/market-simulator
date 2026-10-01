# FINDING miso-103 — the coal minimum-take constraint is DATA-BLOCKED: the only forward-regenerable tonnage (lagged / trailing-mean receipts) FAILS the pin-strength test, reproducing 90–96 % of actual annual coal energy and overshooting actual burn outright in 2024 — NO LP BUILT, keeper UNCHANGED

**Determination: NO-BUILD (Stage-1 admissibility failure, adjudicated ex ante
per the charter — no arm solved, no bundle produced). KEEPER UNCHANGED —
`2026-07-28-miso-101b-tempgrain`.**

Charter: the miso-103 handoff (MISO lever queue item 1, the ONLY C7 route
miso-102 left open). Stage 1 gates everything: *"If (b) fails, write the
no-build FINDING, update the matrix cell, log as miso-103, and stop. Do NOT
reach for a substitute mechanism to hit C7."* It fails.

Reproduction: `scripts/probes/miso103_mintake_pin_strength.py` (committed
artifacts only, ~2 min, no solve).

---

## 0. Summary

1. **Stage 1(a) — the data is on disk, with a caveat that matters.** The
   Schedule-5 receipts series exists at monthly plant grain for 2018–2025
   (`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`), but only
   for **39 of 49** MISO take-or-pay coal plants — the cost-reporting subset,
   which is **exactly the regulated set** (EIA withholds merchant fuel costs,
   and the parquet drops cost-less receipt rows upstream). The raw
   `f923_*.zip` releases are not in the repo (immutable downloads, by design).
2. **Stage 1(b) — the pin-strength test FAILS, on every measure and every
   window.** `MinTake[p,Y] = contract_share[p] × trailing-mean receipts` is
   statistically the same quantity as year-Y actual burn: log-space
   cross-section R² **0.87–0.94** (lag-3; lag-1 and lag-5 give 0.87–0.94
   too — the lag adds *no* independence). The floor lands at **0.96 / 1.14 /
   0.98×** same-year actual tonnage in aggregate and, energy-weighted, dictates
   **90.3 / 95.9 / 90.9 %** of the target plants' actual CAMPD coal energy.
3. **The floor would BIND, so the pin is real, not hypothetical.** Against the
   discount-free miso-102 arm B (`2026-07-29-miso-102b-sunkfixed` — the exact
   control this constraint would replace the discount on), the floor binds at
   **22 / 33 / 20 of 38** plants, forcing **32 / 44 / 20 TWh** above
   unconstrained economics. The constraint — not dispatch economics — would set
   annual coal energy, and it would set it to ≈ the same year's measured
   outcome. That is precisely the rule 13 `[R-MEASURED]` pin miso-96 §7 warned
   of (its same-year construction pinned "≈85 % of actual"; this one pins
   90–96 %).
4. **2024 is an independent killer.** Coal burn fell faster than the trailing
   window: the floor sits at **1.136×** actual tonnage (≥100 % of actual burn
   at 77 % of plants). A hard `≥` constraint would force **more** coal than
   reality burned — C1 breaks in the opposite direction — and softening it
   needs a fitted penalty price (rule 24 `[R-DOF]`).
5. **Stage 1(c) — forward-regenerability fails as "the same quantity."**
   Beyond the data edge a forecast year has no measured trailing receipts; the
   generator must switch to model-simulated prior-year burn. The backcast would
   then validate a *different mechanism* than the forecast runs — rule 13's
   admissibility test ("could this same quantity be produced for a forward
   year?") is not met by a construction whose forward analogue is a different
   variable.
6. **The lane is DATA-BLOCKED and the C7 COAL_PRB failure remains standing on
   the keeper**, now with its last identified route closed pending genuinely
   contractual data (see §4). No substitute mechanism was reached for (charter
   prohibition; rules 1/13).

## 1. Stage 1(a): what is actually on disk

| item | status |
|---|---|
| raw `f923_*.zip` releases | **absent** (immutable EIA downloads, never committed — `derive_coal_takeorpay.py` docstring) |
| `eia923_monthly_fuel_costs.parquet` | **present**, monthly × plant × fuel-group, 2018–2026 (2026 partial) |
| MISO take-or-pay plants covered | **39 / 49** every year 2018–2025 (all 39 regulated; the 10 absentees are the cost-withheld reporters) |
| `coal_takeorpay_MISO.csv` contract shares | present; tons-weighted mean **0.969**, `share == 1.00` at **34 / 49** plants |

Two consequences. First, the constraint's target set (regulated take-or-pay
plants) is fully covered — the series is usable *in principle*. Second,
because `contract_share ≈ 1`, `MinTake` is effectively the trailing-mean
receipts themselves: the share contributes no attenuation, so the pin-strength
question reduces to "are trailing receipts the same number as this year's
burn?" §2 answers yes.

## 2. Stage 1(b): the pin-strength test — FAIL

`MinTake[p,Y] = contract_share[p] × mean(tons[p, Y−3..Y−1])`, tested against
year-Y actual receipts (tons, receipts-as-burn at plant grain) and CAMPD
actual generation (energy):

| year | log R² lag3 (lag1 / lag5) | MinTake/actual tons p50 | aggregate | ≥90 % of plants | ≥100 % | energy-weighted floor as % of actual CAMPD coal energy |
|---|---|--:|--:|--:|--:|--:|
| 2023 | **0.923** (0.883 / 0.902) | 0.914 | **0.964** | 56 % | 31 % | **90.3 %** |
| 2024 | **0.874** (0.916 / 0.873) | 1.112 | **1.136** | 85 % | 77 % | **95.9 %** |
| 2025 | **0.935** (0.936 / 0.915) | 0.950 | **0.978** | 67 % | 46 % | **90.9 %** |

The charter's criterion — *"if R² is high enough that the min-take floor
effectively reproduces actual annual coal energy, the construction FAILS rule
13"* — is met with room to spare. Three readings, each sufficient alone:

* **Level identity.** The floor is within 4 % of actual aggregate tonnage in
  2023/2025 and dictates ≥ 90 % of the target plants' actual annual energy in
  every year. An LP carrying this constraint has its annual coal energy
  written in by a measured outcome series, not chosen by dispatch economics.
* **The lag buys nothing.** Lag-1, lag-3 and lag-5 all sit at R² 0.87–0.94.
  Receipts are so autocorrelated (multi-year contracts *are* the persistence)
  that lagging is a cosmetic de-identification of the same answer key. The
  same-year construction was already adjudicated forbidden (miso-96 §7,
  verified miso-102 §6); this is statistically the same construction.
* **It carries the level without the physics.** The within-plant delta test —
  does the trailing mean predict *year-to-year change* in burn? — gives R²
  **0.172**. So the construction transmits the *answer* (the level of actual
  burn) while failing to transmit the *driver* (the year's conditions). That
  is the exact inversion of what rule 13 admits: a formulaic input that
  responds to changed conditions but does not encode the outcome.

## 3. The binding-margin check: the pin is operative

A floor only pins what it binds. Against the discount-free arm B per-plant
dispatch (the configuration this constraint would be armed on, with
`coal_committed_takeorpay_sunk_fixed=true` replacing the discount):

| year | arm-B energy at matched plants | implied floor | binds at | forced above economics |
|---|--:|--:|--:|--:|
| 2023 | 130.3 TWh | 149.7 TWh | 22 / 38 | **32.0 TWh** |
| 2024 | 122.5 TWh | 163.9 TWh | 33 / 38 | **44.0 TWh** |
| 2025 | 168.2 TWh | 171.5 TWh | 20 / 38 | **19.6 TWh** |

20–44 TWh of the target plants' energy would be set by the constraint rather
than by prices — and set to a number that §2 shows is ≈ the measured outcome.
(Method note: floor energy uses the receipts-as-burn tons ratio applied to
each plant's CAMPD energy, capped at 1.5×; arm-B energy from the registered
run payload `2026-07-29-miso-102b-sunkfixed`, 38 of the 39 plants matched.)

## 4. What would unblock the lane, and what does NOT

**Unblocks:** a *genuinely contractual* tonnage series — contract minimums /
nominations from FERC Form 580, utility fuel-adjustment-clause filings, or
state IRP fuel-budget exhibits. Those are terms fixed *before* the delivery
year (ex-ante by construction, not statistically de-identified deliveries),
they regenerate forward (contracts have stated terms and durations), and they
respond to changed conditions exactly the way reality does (renegotiation,
buyouts, force-majeure). That is a data-intake project, not a modelling
session; it belongs beside the standing outage-grain ask as the second MISO
data ask.

**Does NOT unblock (adjudicated here or upstream, do not redo):**

* any receipts-derived tonnage, whatever the lag/window/smoothing — §2's
  autocorrelation makes every variant the same answer key;
* softening the floor with a penalty price — the price is a fitted knob tuned
  to the residual (rule 24), and rule 17's window would come from the tuning,
  not a driver;
* shrinking the floor by a scalar (e.g. `0.7 × lagged mean`) — the scalar
  would be identified off the C1/C7 residuals, i.e. fitting (rules 13/24);
* every substitute-mechanism route to C7 that miso-102 closed: offer
  steepening, price formation, blunt `sunk_fixed`, PRB-scoped discounts,
  floors/min-gen (D-2: nothing to bite on), and the miso-89 outage-grain gap
  (separately data-blocked).

**C7 status after this session:** failing 3/3 on the keeper, with **no open
admissible lever**. The lane's continuation is a data ask, not a solve.
MISO's caveat budget stays 3/3 saturated — C7 is not ledgered (charter;
miso-96 §7).

## 5. Governance

* **Rule 13 `[R-MEASURED]`** — applied as chartered; the construction fails
  the admissibility test and is not built. No diagnostic-probe arming either:
  nothing was solved.
* **Rule 22 `[R-HOLDOUT]`** — no solve, no scoring, no out-of-training touch.
  The receipts inputs for 2018–2022 windows are already-on-disk authorized
  intake (`docs/out-of-sample-results-2026-07.md` §1); they were read here
  only as *inputs* to a no-LP statistical test of training-year constructions.
* **Rule 26 `[R-MECH-MATRIX]` duty (b)** — `coal_takeorpay_committed` MISO
  cell updated this session with the miso-103 adjudication (the min-take
  successor lane is now `G`-flavoured: governance-refused pending contractual
  data). No new `ScenarioConfig` field was added (nothing built), so duty (c)
  is not triggered.
* **Rule 15 `[R-DASHBOARD]`** — no run was produced; there is nothing to
  register. This finding + probe are the deliverable (ERCOT-127/-130
  ex-ante-refusal precedent).
* **Keeper unchanged**; no shard edit, no attestation.
