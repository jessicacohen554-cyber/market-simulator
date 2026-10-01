# PRE-REGISTRATION — miso-127: the take-or-pay PERIOD-BUDGET re-shaping lane, and the `coal_mustrun_online_pmin` disposal

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only; MISO
holds NO `complete` marker, so no holdout year is solved, scored **or read**) ·
**Keeper at entry:** `2026-08-04-miso-126-steampart-b`
(`results/calibration/miso126_steampart_B`), determination **NOT-YET**, sole FAIL
**C7 `COAL_PRB` ×3y**, ledgered caveats 2/3 {C3a, C3c}.

**Target:** C7 `COAL_PRB` diurnal shape — MISO's sole failing criterion and its
determination blocker.

This document is pushed **before any arm solves** and before any adjudicating
statistic on either lane. Every number quoted in §1–§3 is an **ex-ante
measurement on committed artifacts** (no LP), produced by
`scripts/probes/_miso127_budget_reshape_precheck.py`.

---

## §0 — what C7 actually is (measured, not assumed)

The keeper's committed `legitimacy_diagnostics.json` D-1 rows, reproduced
verbatim by the probe:

| year | `profile_r` | model off-peak CV | actual off-peak CV | `cv_ratio` | verdict |
|---|---|---|---|---|---|
| 2023 | 0.988 | 0.072 | 0.155 | **0.465** | FAIL |
| 2024 | 0.978 | 0.057 | 0.121 | **0.474** | FAIL |
| 2025 | 0.971 | 0.023 | 0.074 | **0.314** | FAIL |

Gates: `profile_r ≥ 0.8` (passing comfortably), `cv_ratio ≥ 0.5` (failing).

Three properties of the statistic bind this session's construction and are
restated so no successor re-derives them wrongly:

* **The "off-peak" window is h0–h14 inclusive** (`D1_OFFPEAK_LAST_HOUR = 14`) —
  midnight to 3 pm. The gate measures **morning-ramp amplitude**, not midnight
  volatility. A "night floor" lever does not address it.
* **The statistic is the CV of the MEAN hour-of-day profile**
  (`model_mw.reshape(-1,24).mean(axis=0)`), not of the raw hourly series.
* **Phase is already right; only amplitude misses** (`profile_r` 0.97–0.99).

**Root cause is already CONFIRMED and is not re-diagnosed here** (miso-102, by
A/B, with five alternatives refuted on committed artifacts): the coal
take-or-pay committed-band discount (`coal_committed_takeorpay_regulated`, armed
on the keeper) prices ~55 % of each regulated plant at VOM in all 8,760 hours.

---

## §1 — LANE A (primary): the period-energy-budget re-shaping

### The chartered question

A take-or-pay contract's sunk volume is a **period** quantity, not an hourly
one. The model represents it as an hourly-constant cheap block. A real regulated
plant with the same annual sunk tonnage still chooses **when** to burn it. So:
can the sunk-fuel band be re-expressed as a **period energy budget the LP
allocates across hours** (a budget row priced by its dual), at the **same annual
volume the model already carries**, instead of a per-hour constant discount?

**The distinction from the blocked miso-103 lane, stated explicitly as
required.** miso-103 was blocked because sizing a minimum-take floor needed a
tonnage **level** from an ex-ante source that does not exist at plant grain. A
**budget-neutral re-shaping** was chartered on the premise that it needs **no new
level** — that it reuses a volume already carried by the model.

### The load-bearing properties, each with its falsifier

> **Property A1 — VOLUME NEUTRALITY IS ACHIEVABLE.** The model must already
> carry a per-plant **period** (annual or monthly) sunk volume.
> **Falsifier:** if the only quantity the model consumes is a per-hour
> *fraction*, a budget re-shaping cannot be built without introducing a level,
> which is miso-103's blocker.

> **Property A2 — HEADROOM EXISTS.** The pinned band must sit **above** the
> regulated PRB fleet's measured overnight minimum.
> **Falsifier:** if the real fleet's overnight floor is at or above the pinned
> band, there is no amplitude to recover.

> **Property A3 — NO NEW TONNAGE LEVEL IS INTRODUCED.** The construction must
> introduce no period level absent from the model today.
> **Falsifier:** any construction requiring a tonnage number — from receipts,
> from a fitted shrink factor, or from any other source — is in miso-103's
> blocked lane and must stop.

> **Property A4 — DIRECTION.** The re-shaping must **deepen** the overnight
> trough and **raise** the midday plateau at constant annual volume.
> **Pre-declared:** a re-shaping that *raises* the trough is a construction
> error, not a result.

> **Property A5 — IT MUST NOT RECREATE THE miso-102 FAILURE.** Annual coal
> energy per plant must be unchanged **by construction**, asserted not assumed.
> (miso-102's discount-deleting arm broke C1 16/16 → 11/16 and overshot
> `COAL_BIT` to 2.6–2.8× measured off-peak variability.)

### Ex-ante measurements (no LP)

**A1 — what the model actually consumes.** `data/raw/_processed-legacy/coal_takeorpay_MISO.csv`
carries 7 columns over 49 plants:
`plant_code, contract_share, spot_share, total_tons, n_receipts, source, breakdown`.

`market_sim.data.coal._derived_coal_takeorpay()` — the sole loader — reads
**exactly two**: `plant_code` and `contract_share`. The columns
**never read by any model code** are `spot_share`, **`total_tons`**,
`n_receipts`, `source`, `breakdown`.

> **The model carries NO period volume. The take-or-pay representation is a pure
> per-hour fuel-cost fraction** (`fuel_frac = 1 − contract_share`, applied to a
> capacity band). `total_tons` exists in the artifact as provenance and is inert
> to the LP.

**A2 — headroom.** Regulated (`EIA-860 Regulatory Status = RE`) MISO `COAL_PRB`
plants in the keeper's own committed CAMPD bench, overnight (h0–h05) load as a
fraction of nameplate, measured on **online days only** (a full-outage day is
maintenance, not a dispatch choice), capacity-weighted:

| year | n | nameplate | **actual** min / p05 / p50 | **model** min / p05 / p50 |
|---|---|---|---|---|
| 2023 | 27 | 28,373 MW | **0.058** / 0.203 / 0.435 | 0.251 / 0.286 / 0.516 |
| 2024 | 27 | 28,373 MW | **0.039** / 0.192 / 0.440 | 0.236 / 0.264 / 0.469 |
| 2025 | 26 | 28,372 MW | **0.074** / 0.255 / 0.518 | 0.268 / 0.367 / 0.567 |

**A4 — direction feasibility.** The model's `COAL_PRB` mean hour-of-day profile
against its own realized maximum:

| year | h0 | h14 | daily peak | max hourly |
|---|---|---|---|---|
| 2023 | 12.78 GW | 14.94 GW | 15.30 GW (h17) | 27.91 GW |
| 2024 | 12.42 GW | 14.22 GW | 14.77 GW (h17) | 25.03 GW |
| 2025 | 16.10 GW | 16.97 GW | 17.82 GW (h18) | 25.73 GW |

### Adjudication

**A2 HOLDS, and is the most useful thing this lane produces.** The measured
overnight *minimum* is 0.039–0.074 of nameplate while the model's is
0.236–0.268 — the model never goes low. The p50s are close (0.435 vs 0.516,
0.440 vs 0.469, 0.518 vs 0.567), so on a typical night the model is only
modestly high; what it lacks entirely is the **low tail** of overnight
operation. This is miso-113's "the overnight distribution is too NARROW" seen at
plant grain, and it **quantifies the amplitude a correctly-sized budget would
have to recover**. **A4 is feasible** — the class is not capacity-bound at
midday (mean daily peak 15.3 GW against a realized maximum of 27.9 GW), so the
plateau *can* rise.

**A1 IS FALSIFIED, and A3 with it.** The model carries no period volume, so any
budget construction must introduce a level. Every available source fails:

1. **`contract_share × total_tons`** — the only committed tonnage. This is
   EIA-923 Schedule-5 **same-year delivered receipts**, i.e. *precisely* the
   series miso-103 refuted (log-space cross-section R² 0.87–0.94 against
   same-year burn; aggregate floor 0.96/1.14/0.98× actual tonnage; 2024
   overshoots outright at 1.136×). The DO-NOT-REDO on receipts-derived tonnage
   variants is explicit and this is the least disguised of them.
2. **Genuinely contractual ex-ante tonnage** — does not exist at plant grain
   across the 39-plant / 26-owner / 12-state target set (miso-104's sourcing
   pass; the standing ask `docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`).
3. **A level derived from the model's own realized volume** — the one candidate
   that introduces no *data*. It is disposed of by proof, below.

### The volume-neutrality ⇒ inertness theorem (the general result)

Let the control LP be `min c'x  s.t.  Ax = b, x ≥ 0`, with optimum `x*`. Let
`g'x` be the sunk-fuel volume of the discounted band, and set the budget to the
volume the model **already carries**, i.e. `B := g'x*` — the definition of
volume neutrality without new data.

Add the budget row in any of its forms:

* cap form `g'x ≤ B` (the cheap-fuel entitlement),
* minimum-take form `g'x ≥ B`,
* two-tranche form (first `B` units cheap, remainder at full cost).

In every form `x*` satisfies the new row **with equality**, so `x*` remains
**feasible**. Every point feasible for the constrained problem was already
feasible for the unconstrained one, over which `x*` was optimal; hence
`c'x ≥ c'x*` for all such `x`, and **`x*` remains optimal**. The solution is
unchanged.

> **A volume-neutral budget is provably INERT.** To bind, the budget must be
> set **strictly away from** the model's realized volume — and the size of that
> departure is a free parameter with no identification source
> (rule 21 `[R-DOF]`, rule 24 `[R-REGISTRY]`).

Setting `B` at the band's *capacity ceiling* (`contract_share × band MW × 8760`)
is slack and therefore inert for the same reason. Sourcing `B` from the **P0**
pass and applying it in **P1** does not escape the result either: the two
solutions differ only by the amortized startup markup, so the budget's
binding-ness would be an artifact of that markup rather than of any contract.

**Conclusion for Lane A: volume neutrality and non-inertness are mutually
exclusive.** The reason a budget re-shaping needs external tonnage is not
incidental to miso-103 — it is **structural**, and it is the same blocker
arriving by a different route. **LANE A IS CLOSED EX ANTE. NO LP IS BUILT AND
NO ARM IS SOLVED FOR IT.** C7 `COAL_PRB` stands **fully data-blocked**, pending
the standing Form 580 tonnage ask (ask §8: pull the 2024 Form 580 filings for
the 26 target owners and count 1:1 contract-plant coal contracts covering 2023 —
a **sourcing** pass, not a solve; the constraint may not be chartered until a
source clears ask §4).

---

## §2 — LANE B: `coal_mustrun_online_pmin` at MISO

`ScenarioConfig.coal_mustrun_online_pmin` (default **off**; `False` on the
keeper's `meta.json`) sizes the coal must-run (cheap, fuel-sunk) tranche from
the measured **online** minimum stable load (`thermal_tranches_MISO.csv`
`mustrun_online_pct`) instead of the all-hours available-CF P5 (`mustrun_pct`).
In the energy-only LP that tranche has `Pmin = 0`, so this changes the **SIZE of
the cheap bid band**, not a forced floor. It is `K` on the PJM keeper; under
rule 28(d) it enters MISO as **`U`** and MISO derives its own parameters from
its own market's data — which its artifact already carries.

### The expected-INERT prior is REFUTED ex ante

The field's docstring predicts the all-hours figure "reads ~2× high". **That was
measured on ERCOT and is false at MISO.** Measured on the committed MISO
artifact (44 coal plants, 41,770.8 MW nameplate):

| statistic | value |
|---|---|
| cap-weighted `mustrun_pct` | **28.886 %** |
| cap-weighted `mustrun_online_pct` | **27.609 %** |
| ratio | **0.9558** |
| p50 (moves the **other** way) | 25.20 → **28.00** |
| **net** MW moved | **−533.1 MW** |
| **gross \|MW\| moved** | **+7,528.1 MW** |
| plants: band grows / shrinks / flat (±0.5 pp) | **20 / 19 / 5** |
| per-plant Δ (pp of nameplate) | min **−43.2**, p50 +0.1, max **+60.0** |

> **The net is a cancelling aggregate.** −533 MW is 1.3 % of the coal fleet;
> **7,528 MW gross is 18 %**. A zero-solve inert declaration built on the net
> would be exactly the boundary/denominator error the miso-119 / miso-122 /
> miso-125 DO-NOT-MISREADs warn against. **The pre-declared band that would have
> killed this item with zero solves is therefore NOT available, and this
> pre-registration records that the prior was wrong rather than proceeding as if
> it held.** The item requires an A/B.

Direction is **genuinely ambiguous ex ante** and that is why it is worth a
solve: shrinking a plant's cheap band moves capacity into full-delivered-cost
tranches so it price-follows (**more** overnight amplitude — what C7 needs),
while growing it flattens that plant. MISO's fleet does both, on 39 of 44
plants, in opposite directions.

### Firing proven at grain 1 (pre-arm), per the miso-126 rule

miso-126's first arm returned exactly inert because a fleet-sourcing flag was
not forwarded at the backcast's own copy of the bin synthesis
(`scripts/run_calibration.py`, which inlines `fleet_to_bins(load_fleet_from_csv(...))`).
`coal_mustrun_online_pmin` is **config-borne**, not a `load_fleet_from_csv`
keyword: `scripts/run_calibration.py:833` sets it via `config.with_overrides`,
`fleet_to_bins(..., iso, config)` receives the config, and
`campd_bins.py:1645` reads it. **This was proven, not assumed** — calling
`fleet_to_bins` directly with the flag off vs on over the MISO 2023 fleet:

| bins column | rows changed | gross \|Δ\| (pp) | net Δ (pp) |
|---|---|---|---|
| `pct_mr` | **42** | 867.8 | +297.8 |
| `pct_mc` | 10 | 134.8 | −4.4 |
| `pct_econ` | **39** | 733.0 | −293.4 |

Capacity moves between the cheap must-run band and the full-cost econ band on 42
of the coal bins. **Grain 1 PASSES.**

### The pre-registered gates

> **Property B1 — FIRING AT TWO GRAINS.** Grain 1 (pre-arm, bins): ≥ 20 coal
> bins change `pct_mr`. **Measured 42 — PASS, recorded above.** Grain 2
> (post-arm, energy): `|Δ COAL class energy|` vs the same-HEAD control must
> exceed **0.05 TWh in at least one year**.
> **Falsifier / kill:** if grain 2 is ~0 while grain 1 fired, the arm did **not**
> reach the LP — that is a wiring defect to be found and fixed, **not** an
> `I` verdict. A null is not trusted until both grains are read.

> **Property B2 — CONTROL INTEGRITY.** Arm A is a same-HEAD **zero-delta**
> replay of `miso126_steampart_B`. Every delta in this session is quoted against
> arm A, never against the committed keeper (miso-124: price response is not
> stable across keepers). Arm A must reproduce the keeper's class energy to
> < 0.01 TWh/yr.
> **Falsifier:** a non-zero arm A invalidates every A/B statistic in the session.

> **Property B3 — CONSERVATION.** The scored identity is the **full** balance,
> not the class sidecar (miso-126 §6):
> `Δclass + Δdischarge − Δcharge + Δslack − Δdump − Δdemand`, tolerance
> **0.5 GWh**, with `Δdemand` exactly 0.
> **Falsifier:** a magnitude violating this is a boundary defect in the
> statistic before it is a result about the mechanism.

> **Property B4 — THE C7 VERDICT.** `cv_ratio` for `COAL_PRB` in all three
> years, against arm A. The gate is 0.5.

> **Property B5 — NO REGRESSION.** C1 must not go PASS → FAIL, and `COAL_BIT`
> must not overshoot measured off-peak variability (the two ways miso-102's arm
> failed). Every criterion status and the ledgered-caveat budget {C3a, C3c} are
> reported against arm A.

> **Property B6 — RULE 14 GOVERNS THE OUTCOME.** `mustrun_online_pct` is a
> **measured** quantity and `mustrun_pct` is a biased proxy for it. If the arm
> makes the fit *worse*, rule 14 `[R-ACCURATE]` forbids reverting the accurate
> input to bury the error — the worse fit is a discovered root-cause item.
> Conversely rule 1 `[R-STRUCT]` forbids promoting a mechanism because a
> residual moved. **Both directions are reported honestly and neither the
> promotion nor the rejection is decided by `cv_ratio` alone.**

**Registered as a NON-KEEPER-BY-DEFAULT.** Arm B is a candidate, not a
presumptive keeper. **A candidate that moves C7 to PASS while breaking C1 is NOT
automatically a keeper, and one that improves structure while C7 stays FAIL
still MAY be** (rule 1: the keeper is the most structurally faithful run, not
the lowest-residual one). If a promotion is proposed, it is scored
leave-one-year-out within 2023–2025 first.

**Rule 19 `[R-ONE-MECH]`:** this does not stack a new forcing mechanism on the
take-or-pay discount's residual. It **re-sizes**, from a measured artifact, the
band the discount is applied to — it replaces a proxy with the quantity the
proxy estimates, and adds no floor. **Rule 24 `[R-REGISTRY]`:** no new field,
no fitted value; the flag is already registered and the value is read from a
committed artifact. **Rule 23 `[R-FROZEN-DERIVE]`:** no re-derive is performed —
the MISO artifact already carries `mustrun_online_pct`.

---

## §3 — `coal_tranche_1/2/3_frac`: recorded as a named open DOF item, not swept

`coal_tranche_1/2/3_frac` (0.30/0.25/0.45) and their passthroughs are, per their
own declaration in `scenarios.py`, "calibrated to EIA-930 2023–2024 hourly
**ERCOT** coal dispatch" — a MISO-applied parameter fitted on ERCOT's residual.
That is a rule-25 `[R-ISO-SCOPE]` and rule-21 `[R-DOF]` debt sitting directly on
the C7 mechanism, already flagged residual-identified in the DOF ledger with
standing open issue **#1336** (re-ground on EIA-923 fuel-cost-dispersion /
contract-share data).

**It is NOT swept against the C7 residual in this session** — that is precisely
the forbidden fitted path (rules 1, 24). Re-grounding it on MISO's own measured
contract-share data would be a rule-14 re-derive requiring **its own**
pre-registration and citing a **source-data** change (rule 23). **This session
records it as the named open DOF item and moves on.**

---

## §4 — what this session will and will not produce

* **Lane A:** no LP, no arm, no run registered. The cell is stamped with the
  ex-ante adjudication and its theorem.
* **Lane B:** two arms in **one** invocation each, `--years 2023 2024 2025`
  (rule 16), via `scripts/replay_keeper.py` on `miso126_steampart_B` at the same
  HEAD. Arm A (zero-delta control) runs **first**. Both are registered on the
  dashboard whatever the verdict (rule 15), and the matrix cell is stamped in
  this session either way (rule 28b).
* **Holdout:** `--year` strictly {2023, 2024, 2025}. MISO holds no
  `calibration-complete` marker, so no holdout year is solved, scored or read
  (rule 22).
