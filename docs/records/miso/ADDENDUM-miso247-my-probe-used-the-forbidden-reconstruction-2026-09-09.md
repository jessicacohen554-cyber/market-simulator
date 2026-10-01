# ADDENDUM miso-247 (first) — **MY OWN PROBE USED THE RECONSTRUCTION `replay_keeper` EXPLICITLY FORBIDS.** It produced NO numbers — it crashed — and the repair is declared here BEFORE any repaired number exists. **No bar moves; no gate is touched**

**Governs:** `scripts/probes/_miso247_p19_posture_phase0.py`'s `build()` only. **Every gate in
`PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md` — `D-1`…`D-5`, `P-1`…`P-3`, the §4
screen-year selection rule and `G-1`…`G-4` — is UNTOUCHED**, and none of their numbers existed when
this was written.

---

## 1. THE FAILURE, AT FULL MAGNITUDE

The probe as pushed (`_miso247_p19_posture_phase0.py`, first commit) built its `run_year` call from
**`replay_keeper.build_kwargs(meta)`** splatted directly. It **crashed on its first call**:

```
TypeError: run_year() got an unexpected keyword argument 'commitment'
```

**It emitted no measurement of any kind** — no `D-1`, no footprint, no screen year. There are
therefore **no pre-repair values to launder**, and I state that plainly rather than presenting the
absence as cleanliness: **the reason there is nothing to correct is that the probe never ran, not
that it ran correctly.**

## 2. WHY IT IS WORSE THAN A TYPO, STATED AGAINST INTEREST

`replay_keeper.run_year_kwargs`'s own docstring names this exact construction as the defect it was
written to forbid — *"THE ONLY SANCTIONED FLEET-ONLY RECONSTRUCTION (caiso-243 §7.3 / caiso-244) …
from caiso-202 to caiso-243 the CAISO lane's probes rebuilt the recipe as a filter by parameter NAME
… A probe on that reconstruction measured a lookalike recipe, not the keeper."* I read that
docstring **after** writing the probe, not before, and the lane's own instrument had the answer the
whole time.

**I got lucky in a way that must be said out loud:** `build_kwargs` carries `commitment`, which
`run_year` does not accept, so the mistake surfaced as a **loud crash**. Had the keeper's meta
happened to carry only name-matching keys, the probe would have run and silently measured a
**recipe that is not this keeper** — dropping `coal_prb_sigmoid_overrides` → `prb_overrides`, the bag
that carries dozens of structural flags. **The failure mode was noisy by accident, not by design.**

## 3. THE REPAIR — STRICTER, and it moves no bar

`build()` now reconstructs through **`run_year_kwargs(meta)` + `derived_run_year_inputs(KEEPER,
year)`**, the sanctioned pair, which hard-errors on any unmapped key and applies `RUN_YEAR_REMAP`.
Two checks are **added**, so the repair is strictly stronger than the original:

1. **`run_year_unreachable(meta)`** is evaluated on this keeper: it returns **`{}`** — the
   fleet-only rebuild carries the whole recorded recipe, with nothing silently dropped.
2. **Posture A is ASSERTED on the RESOLVED config.** The screen has no named `run_year` kwarg, so it
   rides `prb_overrides` → `config.with_overrides`; `build()` now asserts
   `state["config"].f923_gas_price_plausibility_screen == requested` and **raises** otherwise, rather
   than trusting the argument that its consumer runs after that channel applies. (`__post_init__`
   coerces the field to its frozen `False` wherever the seam is unreachable; MISO's keeper is
   `mode="backcast"` with `gas_plant_monthly_fuel_pricing=True`, so the seam is reachable — but the
   assertion measures that rather than reasoning to it.)

**No bar is moved, no gate is re-scoped, and no threshold is relaxed.** The repair changes only *how
the keeper's recipe is reconstructed*, in the direction the lane's own instrument requires.

## 4. Non-claims

1. **No number in this session existed when this was written.** The repair cannot have been shaped to
   a result.
2. **`D-1`…`D-5`, `P-1`…`P-3`, §4's selection rule and `G-1`…`G-4` are unchanged**, verbatim.
3. **Zero LP**; keeper unchanged; DOF **41/2**; no `ScenarioConfig` field created or changed.
4. **No marker is sought or implied** and no out-of-training year is touched.
