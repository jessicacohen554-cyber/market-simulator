# ADDENDUM miso-245 (third) — **MY OWN SCREEN GATE `S-3(b)` FAILED, AND IT FAILED BECAUSE I WROTE IT AGAINST OBJECTS THAT CANNOT MATCH.** Published FIRST, at full magnitude; the repair is declared here BEFORE its numbers exist, MOVES NO BAR, and is the strictest **satisfiable** form of the same question

**Governs:** `ADDENDUM-miso245-the-four-screen-gates-2026-09-08.md` §1 `S-3(b)` only. **`S-1`, `S-2`,
`S-3(a)` and `S-4` are UNTOUCHED — no bar, no operand and no disposition of theirs moves.**

---

## 0. **THE FAILURE, FIRST AND AT FULL MAGNITUDE**

`S-3(b)` required *"the screen bundle's `run_config.json` `scenario_config` is **identical to the
keeper's on every field**."* **It FAILED on four fields**
(`results/calibration/_miso245_screen_gates.json`, `STOPPED_BY: ["S3_identity_and_clean_ab"]`):

| field | keeper | arm |
|---|---:|---:|
| `gas_price_override` | 2.54 | **2.19** |
| `weather_year` | 2023 | **2024** |
| `netload_drag_layup_window_mask` | *(absent)* | **false** |
| `pjm_thermal_accreditation_vintage` | *(absent)* | **false** |

**The gate stopped the arm, and I am not arguing that away.** What follows is a repair, declared
before its numbers exist, not a re-reading of a number I have already seen.

## 1. **WHY IT FAILED: I COMPARED A 3-YEAR BUNDLE'S RECORD AGAINST A 1-YEAR BUNDLE'S. THE GATE AS WRITTEN IS UNSATISFIABLE**

`run_config.json` carries **one** `scenario_config`, and `pipeline/backcast_config.py::backcast_config`
builds it **per year** — `gas_price_override` is that year's measured Henry Hub price and
`weather_year` is the solve year. The keeper is a `--year 2023 2024 2025` bundle, so its record is
**2023's**; the arm is a `--years 2024` replay, so its record is **2024's**. **Two of the four fields
therefore CANNOT match, for any arm, ever** — including an arm with no delta at all. A gate that no
correct run can pass is broken, not strict, and it is my error.

The other two are the **new ScenarioConfig fields** that landed between the keeper's solve sha and
HEAD, recorded at their dataclass default `False` — i.e. **the absent behaviour the keeper solved
with**, not a config change. Both were **MEASURED or classified INERT for MISO backcast by
miso-244's G-DRIFT** (`_resolve_drag_layup_shares(keeper_config, "MISO", y, 8760)` returns **len 0**
in all three years; `pjm_thermal_accreditation_vintage` is on the capacity-evolution path a
`mode="backcast"` run never enters), and they landed **before** `a667073f`, inside that all-INERT
audit — my own `a667073f..HEAD` audit is **empty**.

**STATED PLAINLY: `S-1`, `S-2` and `S-3(a)` compared the RIGHT objects and are unaffected.** They read
the two bundles' **year-2024 solve outputs** and the derive's own table — both bundles' 2024 outputs
were solved on 2024's weather and 2024's gas. Only `S-3(b)`'s operand was wrong.

## 2. **THE REPAIR — `S-3(b′)`, declared here before its numbers exist. NO BAR MOVES**

> **`S-3(b′)` PASS iff EVERY field on which the arm's `scenario_config` differs from the keeper's
> falls into one of exactly TWO closed classes, each MEASURED rather than asserted:**
>
> * **(P) PER-YEAR.** The field's arm value is what the keeper's **own** recipe produces for **2024**,
>   and the keeper's recorded value is what that same recipe produces for **2023**. Measured by
>   calling `backcast_config("MISO", 2023)` and `backcast_config("MISO", 2024)` and requiring **both**
>   to reproduce the two recorded values exactly. *(A field that differs and is NOT reproduced by the
>   keeper's own per-year construction is a real config change and STOPS the arm.)*
> * **(N) NEW-FIELD DEFAULT.** The field is **absent** from the keeper's `scenario_config`, the arm's
>   value equals the `ScenarioConfig` **dataclass default**, and the field is one miso-244's G-DRIFT
>   already measured or classified INERT for MISO backcast. *(A newly-present field at a NON-default
>   value STOPS the arm.)*
>
> **Any differing field in neither class STOPS the arm.** The count of differing fields is **not** a
> bar and is never widened; what is gated is that every one of them is accounted for by a closed,
> measured class.

**Why this is the strictest SATISFIABLE form and not a loosened one.** `S-3(b)`'s question was *"is
the only delta between control and arm the ladder constant?"* Its written form asked something no
correct run can satisfy. `S-3(b′)` asks the same question in the only form that can distinguish a
**dirty A/B** from a **cross-year record artifact**: it enumerates the admissible explanations in
advance, closes the enumeration, and **measures each one** rather than reasoning from a gate.

**A CONTROL SOLVE WAS AVAILABLE AND IS NOT BEING SPENT, AND I SAY SO RATHER THAN LEAVING IT UNSAID.**
Re-solving 2024 at HEAD with the *pre*-reconciliation ladder would settle this by measurement in ~13
minutes of LP. It is not spent because (a) rule 29(b) earns a control solve only on a **LIVE** hunk
and this session's G-DRIFT `a667073f..HEAD` is **empty**, (b) the two new fields are already
**measured** inert for MISO backcast rather than classified from their gate, and (c) `S-3(b′)` answers
the question at zero LP with a closed enumeration. **If `S-3(b′)` cannot close the enumeration, the
control solve is the next step and the arm stops until it is spent.**

## 3. **THE PRE-REPAIR NUMBERS, PUBLISHED HERE SO THE REPAIR CANNOT LAUNDER THEM**

`S-1` and `S-2` **already PASS** against the keeper's committed bundle, and their values are fixed on
the record before any repair:

| gate | bar | **measured** | |
|---|---|---:|---|
| **S-1** `Δ mean net import` | `0 ≤ Δ ≤ 40 MW` | **+0.039378 MW** (0.0107 × `Δq̂`) | **PASS** |
| **S-2** hours changed > 1 MW | ≤ 860 | **288** (3.29 % of the year) | **PASS** |
| **S-3(a)** derive reproduces the solved table | 192 entries at 0.00 | **0.0** | **PASS** |

Reported beside them and gated in neither direction: `max |Δ|` = **375.000 MW** — **exactly one South
band step** (`3000/8`), which is the correction's own quantum and nothing else — with **151 hours
positive / 137 negative** and a net **+344.951 MWh** over the year.

**AND THE PRE-SOLVE ARITHMETIC IS CONFIRMED IN THE DIRECTION THAT COST ME A PREDICTION:** the LP's
mean response is **+0.039 MW against a pre-solve `Δq̂` of +3.682 MW**, i.e. **1.1 %** of it. That is
the sign the arithmetic requires and **two orders of magnitude below its size** — exactly what
miso-244 §0e predicted post-hoc when it measured the moving band to be the marginal price-setter in
**82 of its 86 hours** (a marginal band that moves takes the price with it, so a footprint evaluated
at the frozen price overstates). **The screen's lower bound was set at `0`, not at `Δq̂`, for this
reason, and that looseness was declared in advance rather than discovered here.**

## 4. Non-claims

1. **No bar is moved, and `S-3(b)`'s failure is not withdrawn** — it is repaired, and the repaired
   gate is stated before its numbers exist.
2. **`S-1`, `S-2`, `S-3(a)`, `S-4` are untouched**, and their pre-repair values are published above so
   the repair cannot re-open them.
3. **The repair cannot promote anything.** Every gate remains STOP-only, and a cleared screen
   authorises the full span and nothing else.
4. **DOF stays 41/2**; no `ScenarioConfig` field is created or changed by this session.
5. **No out-of-training year is solved, scored or registered**, and no marker is sought.
