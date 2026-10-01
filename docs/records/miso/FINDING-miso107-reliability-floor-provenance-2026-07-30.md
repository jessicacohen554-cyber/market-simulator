# FINDING — miso-107: the h14-21 CT_PEAKER reliability floor did NOT absorb a mispriced fleet

**Outcome: the Option-A hypothesis is REFUTED ex ante on the floor's own
derivation provenance. NO LP was spent. Keeper UNCHANGED.**

miso-106 surfaced a real and striking signal: arming `measured_ct_heat_rates`
made the h15-21 `CT_PEAKER` `reliability_floor` force **1.188 → 1.743 TWh
(+47 %)**, D-2 share **11.77 → 14.21 %** against a 15 % peaker cap. Its §8
recorded the open question: *was the floor's **level** implicitly absorbing a
mispriced fleet?*

The question is answerable from the coefficient artifact and its deriver alone,
and the answer is **no — by construction**. Spending six year-solves on it would
have tested a premise the source code already falsifies.

## 1. The floor's level has no model-dependent input

`data/raw/reference/reliability_floor_coeffs_MISO.csv` is built by
`scripts/data/derive_reliability_coeffs.py`, whose identity is:

```
floor_pct = commit_frac × min_stable_pct
```

| term | what it is | source | model-dependent? |
|---|---|---|---|
| `commit_frac` | share of class nameplate **online** (`grossLoad > 0`) on flagged days | CAMPD unit-level gross load, MISO's own | **no** |
| `min_stable_pct` | 0.38 for `CT_PEAKER` | `constants.MIN_STABLE_PCT_PHYSICAL`, NREL WWSIS-2 Table 7 ("simple-cycle CT — WWSIS-2 38 %") | **no** |
| `threshold` | 78.52 GW = **p70** of MISO daily-peak net load (demand − VRE) | MISO's own 2023–2025 EIA-930 distribution | **no** |
| `enabled` | `rho ≥ RHO_MIN` ∧ `n ≥ N_MIN` ∧ `commit_frac > baseline_commit` | all measured | **no** |

No price, no dispatch, no residual, and no model output enters any of them. The
deriver says so in its own docstring — *"The floor is **structural**, never tuned
to a price/volume residual"* and *`commit_frac` is *"a commitment count, **NOT a
measured-CF ceiling**"*. It is a rule-23 `[R-FROZEN-DERIVE]` measured-behaviour
parameter, re-derivable only on a source-data change.

A level that never touched the model's economics cannot have been compensating
for the model's economics. **The hypothesis fails on provenance, not on a gate.**

## 2. What the +47 % actually is: the floor became load-bearing, not wrong

The floor is a **floor**, not a fixed schedule — it binds only when economics put
the class beneath it.

* **Before.** 1,068 MW of MISO CTs carried **combined-cycle** heat rates
  (miso-106 §1; one plant at a physically impossible 26.544 MMBtu/MWh). Too
  cheap, the LP dispatched them *economically* above their commitment floor
  through much of the window, so the floor rarely bound.
* **After.** Correctly priced, the cheap end of the CT curve rises
  (**+1.280 MMBtu/MWh** capacity-weighted on the bottom-12, miso-106 §3) and
  those units clear less on merit. The **same unchanged floor** now binds.

So the mispricing had been quietly discharging a commitment obligation that the
floor is there to represent. Correcting the input did not break the floor; it
stopped hiding it. This is the opposite of the "propping up capacity the
corrected economics would shut off" reading — the floor is not creating
commitment, it is *revealing* commitment that the meter says is real and that
underpriced CTs were previously supplying for free.

## 3. It is not over-forcing — a proportionality bound from committed numbers

The floor is armed only on flagged days (net load > p70) inside h15-21:

* flagged days: **n = 329** over the 2023–2025 derivation window = 30.0 % of
  1,096 days ⇒ **≈ 110 days/yr**
* window: h15-21 inclusive = **7 h/day** ⇒ **≈ 767 h/yr = 8.76 % of 8,760**

Against that, arm B forces **1.743 TWh** on a **measured** 2023 `CT_PEAKER`
actual of **19.199 TWh** (the C1 benchmark actual) = **9.08 % of the class's own
metered annual energy**.

**9.08 % of measured energy inside 8.76 % of the year's hours.** The floor is
holding min-stable output on the tightest ~30 % of afternoons and is essentially
proportionate to what MISO's CTs actually did. It is not inflating the class.

## 4. Rule 17 `[R-FLOOR-WINDOW]` triple, for the record

* **(a) External driver** — MISO system daily-peak **net load** (demand − VRE)
  ≥ 78.52 GW, the p70 of MISO's own distribution. A tightness signal, not a
  calendar.
* **(b) Hours it may bind** — h15-21 on flagged days only, the observed CT
  mobilisation window. **D-4 off-window binding measures exactly 0.000 in both
  miso-106 arms**, so the limb binds nowhere its driver says the class is idle.
  This is the specific pathology rule 17 exists to catch, and the floor is clean
  on it.
* **(c) Forward regeneration** — net load is a forward model quantity; the p70
  threshold recomputes from the forecast net-load distribution; `commit_frac`
  re-derives from CAMPD when source data updates; `min_stable_pct` is a
  published constant. Every term regenerates for a forecast year and responds to
  changed conditions — rule 13 `[R-MEASURED]`'s admissibility test, passed.

## 5. Rule 19 `[R-ONE-MECH]` — nothing stacked

D-2 on the keeper enumerates exactly one mechanism forcing `CT_PEAKER`:
`reliability_floor` (h15-21). `nuclear_mustrun`, `chp_steam`,
`st_gas_mustrun_per_plant` and the `reliability_floor × ST_GAS` limb touch other
classes. There is nothing to reconcile or replace.

## 6. What is actually open — and what must not be done about it

1. **The real open item is C1 `CT_PEAKER` volume**, which miso-106 §5.1 records
   as degrading in all three years. It must **not** be closed by relaxing this
   floor: that is the compensating-error pattern rules 1 `[R-STRUCT]` and 14
   `[R-ACCURATE]` forbid, and the miso-106 keeper note bars it explicitly.
2. **A genuinely different question remains** — whether `min_stable_pct = 0.38`
   (a class-physical NREL value shared across ISOs) is right for **MISO's own**
   CT fleet composition. Under rule 25 `[R-ISO-SCOPE]` MISO would have to derive
   its own from its own units, and under rule 23 `[R-FROZEN-DERIVE]` that may
   only be triggered by a **source-data change — never because a residual
   moved.** No such trigger exists today, so this is recorded, not actioned.
3. **Queue items 5 and 6 are untouched** (`dual_fuel_switching`;
   `hydro_budget_nameplate_aware` + the `NG: PS` pin audit).

## 7. Governance

* **Rule 15** — no run produced; nothing to register. No solve was spent because
  the premise was falsified before the LP stage, the same discipline as
  miso-103/104/105.
* **Rule 22** — no year solved, scored or registered; no holdout touched. MISO
  carries no calibration-complete marker.
* **Rule 1** — no mechanism was added, relaxed or re-scoped to move a number.
* **Contamination declared.** This session's handoff quoted miso-106's arm-B
  outcomes (1.743 TWh, 14.21 %, "C3a improved in all three years", "C3c
  bit-identical") before any artifact was read, so this session was **not blind**
  to them. That is immaterial here — nothing was pre-registered or predicted;
  the finding rests on the deriver's source code and published coefficients, both
  of which predate and are independent of either arm.
* **Dependency** — miso-106's artifacts live in **PR #3140**, open and unmerged
  at the time of writing. Its MISO governance is green
  (`[✓] MISO 2026-07-30-miso-106b-ct-heatrate — all checks passed`); it is held
  up by three failures that reproduce on a clean `main` and that it did not
  cause: 20 Ruff `F811` redefinitions in `src/market_sim/data/fleet/__init__.py`
  (a partial extraction to `fleet/models.py` that left the originals in place), a
  dangling `scripts/data/derive_parasitic_factors.py` reference from
  `campd_bins.py`, and a stale `frontend/data/backcast/status/NEISO.js`.
