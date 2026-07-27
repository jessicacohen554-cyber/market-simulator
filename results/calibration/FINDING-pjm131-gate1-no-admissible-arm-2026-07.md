# FINDING — pjm-131: gate 1 has no admissible arm — its CC_CHP half is an economic merit miss (the same stratum as gate 2), its ST_GAS half is grounded, and the measured host-share artifact that would have armed it is globally degenerate

**Lane:** the PJM re-tune opened by pjm-129's `NOT-YET`, continued from pjm-130.
Charter (pre-registered, committed as `e454b87` **before** the probe was run):
`docs/handoffs/pjm-131-gate1-arm-charter-2026-07.md`.
**No LP was solved.** Every verdict below comes from a rule committed before the
measurement that decides it.

---

## §0 — verdict

| item | status after this session |
|---|---|
| **Priority 1 — re-conditioning memo** | **STILL UNDECIDED.** Verified: last commit `f1070d4`, live banner "awaits the owner's decision", no authorization anywhere in the tree. Not nudged, not re-derived, no proxy (rule 23). Gate 2 stays blocked. |
| **Gate 1 — CC_CHP half** | **REFUTED as an arm, and re-classified.** κ = **0.023** ⇒ the class is economically dispatched, not capacity-bound, so the host-share lever cannot reduce the overshoot. The +2.54 TWh is a **merit-order** miss at 72.7 % mean utilization — pjm-122's marginal-ownership question, i.e. **gate 2's stratum**. |
| **Gate 1 — ST_GAS half** | **GROUNDED, ledgered.** `st_netload_drag` carries a cited `D4_WINDOWS` declaration and D-4 scores it **pass, 0.000 off-window**; D-1 shape passes every year. Not a floor-window artifact ⇒ not mechanised (rules 1 / 19). |
| **`chp-btm-share` artifact** | **GLOBALLY DEGENERATE — new defect, localized.** `btm_share ≡ 1.0` on **62/62 rows across 5 ISOs**. Root-caused upstream. Latent forecast-path exposure. |

**Net:** gate 1 is **not independently armable**. Both of its halves resolve onto
things this session may not touch — the CC_CHP half onto the owner-blocked memo,
the ST_GAS half onto a mechanism that is already grounded. This session did not
invent a mechanism (charter §5, rules 1 / 19 / 23).

This **sharpens** pjm-130 §8.2. That session called gates 1 and 2 "one stratum"
by analogy; κ turns it into a **measured dependency** — the CC_CHP overshoot is
economic clearing, so it is closed by whatever re-owns the $40–150 merit region,
which is exactly gate 2's blocked route.

## §1 — gate 1's CC_CHP half: κ = 0.023, so the capacity lever is inert

The candidate was the only structural lever pointing at CC_CHP: for the gas CHP
classes the behind-the-meter host share is a **grid-capacity pull-out**, not a
floor (`offer_curves.plant_cf_bands` / `fleet/assembly.py`: `pct_mr =
chp_btm_pct(...)`, then `mustrun_cap = 0`, `grid_cap = nameplate × (1 −
pct_mr/100)`), and the same share is the bench subtrahend
(`run_calibration_full._btm_frame`, "the identical share the LP hold-out uses").

`scripts/probes/pjm131_chp_btm_precheck.py`, on the `pjm129_meritguard_a1`
fleet reconstructed with no LP via `scripts/lib/bundle_fleet.py`:

| quantity | 2023 |
|---|---|
| model CC_CHP | **8.653 TWh** |
| bench actual (`classFull`) | **6.1148 TWh** |
| overshoot | **+2.538 TWh** |
| mean class utilization | **72.7 %** |
| **κ** (energy share at ≥99 % of hour-varying available grid capacity) | **0.0226** |

The model/actual/overshoot triple reproduces pjm-130 §2's 8.65 / 6.11 / +2.54
exactly, so the reconstruction is faithful.

**Pre-registered Q3 rule** (charter §4): `κ ≤ 0.20` ⇒ economically dispatched ⇒
the model barely responds to a capacity cut while the bench actual falls in
full ⇒ the overshoot **worsens** ⇒ **REFUTED as a gate-1 arm.** κ = 0.023 fires
it with room to spare: only 2.3 % of CC_CHP's energy is produced against its
capacity ceiling. **The class is not capacity-constrained; it is clearing on
price.** That is a merit-ownership finding, not a capacity one.

**Stated limitation, not glossed:** κ is a *local* elasticity. It says a marginal
capacity change is absorbed; a large enough cut would eventually bind (mean
utilization is 72.7 %, so cuts beyond ~27 % start biting). That branch is
unevaluable here because §3 shows no valid measured share exists to size such a
cut, and inventing one would be fitting a mechanism to a residual (rule 1).

## §2 — gate 1's ST_GAS half: the drag is window-declared and window-clean

Pre-registered Q5 asked whether ST_GAS's +1.72 TWh (+19 %) is a floor artifact.
From the A1 bundle's **committed** `legitimacy_diagnostics.json` — no solve:

* **D-2:** `st_netload_drag` forces **5.05 of 9.25 TWh = 54.6 %** of ST_GAS in
  2023 (52.9 % / 43.6 % in 2024 / 2025) — over the 30 % merchant cap.
* **D-4:** the mechanism carries a **cited `D4_WINDOWS` entry**
  (`(MECH_ST_NETLOAD_DRAG, None): (0, 24)`), grounded on measured CAMPD evidence
  that the gas-steam fleet is "committed every day and every night, never fully
  off" with overnight CF rising 0.03→0.36 against net load (Spearman ρ 0.82,
  year-stable). D-4 verdict **pass, off-window share 0.000**, all three years.
* **D-1:** ST_GAS passes every year (`profile_r` 0.97 / 0.92 / 0.90).

That is precisely rule 18's over-budget escalation path satisfied: declared
window + clean off-window binding + passing diurnal shape ⇒ a **grounded pass**,
which rule 18 says is "a clean PASS surfaced as a report note, never a caveat".

**Pre-registered Q5 rule:** clean and in-window ⇒ **ledger it, do not mechanise
it.** Applied. ST_GAS's overshoot is not a floor-window bug, so there is no
rule-17 defect to fix and no new mechanism is licensed (rules 1 / 19).

One observation recorded for the ledger, deliberately **not** acted on: D-1's
`cv_ratio` for ST_GAS is 1.9 / 2.8 / 2.2 — the model's off-peak ST_GAS is *more*
variable than the measured fleet, which is flatter. The gate is a **minimum**
(0.5) so this passes, but the direction says the net-load hinge introduces
variability the real fleet does not have. That is a shape observation, not a
licensed arm.

## §3 — the new defect: `chp-btm-share` is degenerate in every ISO

Pre-registered Q1/Q2 needed the measured per-plant host share. It does not exist
in usable form. `scripts/probes/pjm131_chp_btm_artifact_audit.py` (a follow-on
**diagnostic**, explicitly not a pre-registered test — it decides nothing):

| ISO | rows | `campd_net_mwh == 0` | `btm_share == 1.0` |
|---|---|---|---|
| PJM | 35 | 35 | **35** |
| MISO | 19 | 19 | **19** |
| NYISO | 6 | 6 | **6** |
| ERCOT | 1 | 1 | **1** |
| NEISO | 1 | 1 | **1** |
| CAISO | — | — | curates **no rows at all** |

**62 of 62 rows read `btm_share = 1.000`.** A share of 1.0 asserts that *no part*
of the plant's EIA-923 generation reaches the grid — the signature of a
CEMS-electrically-invisible plant, not a measured host share.

**Root cause, upstream in `plant_emission_rates_v2`.** The curation's cogen
signature is `steam_load_klbh_sum > 0`, and it sums `net_mwh` over exactly those
rows. But at CEMS the steam load and the electrical output are reported on
**different units**: of **2,915** steam-reporting unit-years, **2,914 carry
`gross_mwh = net_mwh = 0`**. The filter that identifies the cogen removes the
rows that carry its electricity, so the CAMPD term is zero by construction and
`btm_share = (e923 − 0)/e923 = 1`.

**A plant-level repair is not sufficient.** Lifting the cogen test to plant level
and summing `net_mwh` over all the plant's units recovers a non-zero CAMPD term
for only **24 of 134** cogen plants; **110 still read zero**. Repairing to that
subset would base a fleet-wide capacity pull-out on the CEMS-*visible* cogens
only — a biased sample, and worse than the uniform sector estimate it replaces.
So no repair is shipped here: this is rule 14 `[R-ACCURATE]`'s own exception
(the data is "genuinely misaligned to our representation" — it measures CEMS
visibility, not host share), and the sector-keyed estimate correctly stands,
now **documented** rather than merely inherited.

**Latent forecast exposure, flagged.** `runner.py` resolves this artifact for
**forecast** years only. Any forecast whose ISO has a curated partition would
pull every covered CHP plant **100 % behind the meter** and give it zero grid
capacity. It is latent rather than live because `data/clean/` is derived and
gitignored, so it fires the moment the datatype is curated. **Not fixed here** —
the repair is a data-intake project (finding the electrical-output channel for
cogens), not a hygiene edit, and it is out of this session's scope.

## §4 — corrections disclosed

Two slips in the pre-registration, both corrected in the probe with the
correction commented at the site, neither changing a verdict:

1. **Sign of the Q4 propagation.** The charter and docstring wrote
   `model_new = model_old × (1 − κ·delta_cap)`, but `delta_cap` is defined as
   the *signed* relative capacity change, so the propagation is `(1 + κ·delta_cap)`.
   Corrected rather than left to print a wrong number. Q4 is moot regardless —
   with no valid measured share it evaluates on `s_meas = 1.0` and reports the
   overshoot going 2.54 → 8.46 TWh (the actual collapses to zero), which is the
   degeneracy of §3 restated, not a result.
2. **A mis-named verdict key.** `Q2_direction_reduces_capacity` read the sign
   backwards and is renamed `Q2_measured_gives_more_grid_capacity`. The
   underlying test is unchanged.

## §5 — the pre-existing test failure: NOT reproducible at main

pjm-130 §6 reported
`test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
failing on a clean `origin/main` (expected `edbc1b103207170a`, got
`30065460cdc3042c`). **At `origin/main` = `8e5053e` it passes.**

* `ScenarioConfig().cache_key()` returns **`edbc1b103207170a`** — the pinned value.
* The pin literal is unchanged (`git log` on the file shows only the
  `tests/regression/` move, `89ed875`); it was **not** edited to silence anything.
* It is **not** data-dependent: re-run with `data/clean/` moved aside, still passes.
* `scenarios.py` carries **no live env-var knobs** — all five `getenv`/`environ`
  hits are historical comments about channels already removed (rule 24 clean).

So the failure did not survive into this container and has no identified code
cause. It is **not** silenced and **not** dismissed — recorded as unreproduced,
with the pin intact. **`--reuse-solved` is unaffected**: the default cache key
matches the pinned literal, so no on-disk cache is orphaned.

## §6 — rule compliance

* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. Freeze untouched, NOT lifted; PJM
  still carries no calibration-complete marker. The `chp-btm-share` curation
  excludes 2022/2026 by construction.
* **Rule 15 `[R-DASHBOARD]`:** no solve completed ⇒ no bundle to register.
  Nothing was solved and dropped (pjm-124/125/126/127/128/130 precedent).
* **Rule 16 `[R-ALLYEARS]`:** no bundle produced; no single-year artifact exists.
* **Rules 1 / 19 / 20 / 23 / 24 / 26:** nothing tuned — no offer band, sigmoid,
  floor, ORDC value, derive output or surface JSON touched, and no mechanism
  invented for either half of gate 1.
* **Rule 27 `[R-PUSH]`:** no existing file ≥300 lines was modified; the only new
  code is two probes. Nothing regenerated from response content.
* **Keeper** `2026-07-25-pjm-121-cc-belt` untouched; `keepers.json` not edited.

## §7 — what PJM needs next

1. **Gate 1 is not independently armable — it is now *provably* gate 2's
   problem.** κ = 0.023 says CC_CHP clears on price, so the arm that closes it is
   the measured re-ownership of the $40–150 region (pjm-122), whose surface is
   inadmissible until the memo is decided. Do not open a separate CC_CHP lane.
2. **The memo decision is the gating item for the whole PJM lane** — now for
   gates 1 *and* 2, not gate 2 alone. Frontier remains NOT ready.
3. **`chp-btm-share` needs a data-intake project or retirement.** It cannot
   supply a host share for any ISO today, and it is wired into the forecast path.
   Either find the cogens' electrical-output channel, or gate the artifact off
   until it has one. Tracked here; not fixed in-session.
4. **Carried forward:** pjm-130's bench fix still has **not** landed on the
   dashboard — the renderer writes `bench/` at registration and this session
   registered nothing. The corrected `bench/PJM/2025.json.gz`
   `classFull.CT_CHP ≈ +1.4653` lands on the next PJM registration.

## Reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/regenerate_clean.py \
    transfer-interface-limits ramp-capability lmp
PYTHONPATH=. .venv/bin/python scripts/data/curate_chp_btm_share.py
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_da_virtuals.py \
    --years 2023 2024 2025 --feeds hrl_da_incs_decs        # all 36 months
PYTHONPATH=. .venv/bin/python scripts/probes/pjm131_chp_btm_precheck.py \
    --bundle results/calibration/pjm129_meritguard_a1 --year 2023 \
    --json-out results/calibration/pjm131_chp_btm_precheck_2023.json
PYTHONPATH=. .venv/bin/python scripts/probes/pjm131_chp_btm_artifact_audit.py \
    --json-out results/calibration/pjm131_chp_btm_artifact_audit.json
```

Fidelity anchor re-verified this session (no solve): `pjm120_c3a_stratum_readout.py
results/calibration/pjm121_ccbelt --year 2025` → model_lw **41.53** / actual
**46.07** / gap **−4.54**.
