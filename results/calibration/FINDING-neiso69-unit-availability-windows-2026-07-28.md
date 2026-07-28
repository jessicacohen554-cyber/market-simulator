# FINDING — neiso-69: the measured unit-availability window family is **REJECTED for NEISO on provenance**, not on fit. The frozen detector returns **one** short window and **zero** partial windows across 2023–25; that single window is **contradicted by the fleet's own hourly CEMS** (Merrimack produced in **72 of its 72 masked hours**, peaking at **441 MW**, including 8 of 2023's top-22 price hours), and arming it would zero NEISO's entire modelled coal bin across the **Feb 3–4 2023 Arctic outbreak**. The `when-operable CF ≥ 0.55` baseload guard is **degenerate in this ISO**: it judges Merrimack on **6–10 % of the year**, because the standard ≥5-day overlay has already removed ~90–97 % of it.

**Lane:** OFF-QUEUE input-accuracy lever (rule 28a). This is a rule-14
`[R-ACCURATE]` measured-availability input in the sense of `measured_ct_heat_rates`
(NEISO queue item 3) — **not** a member of NEISO's frontier-declared C3c scarcity
family, and it needed no new charter. Tail movement is reported below as a
downstream observation only; nothing here is framed or promoted as a C3c lever.

**Keeper `2026-07-23-neiso-61-netrev-margin` UNCHANGED.** Both flags stay
default-off. Matrix cell `unit_outage_short_windows` × NEISO: **U → R**.

Rule 25 note: this is a **NEISO-scoped** verdict. It carries no implication for
the PJM/MISO `K` cells, and §4 measures why those fleets are unaffected. The
ERCOT `I` adjudication (ERCOT-126) was **not** ported here — NEISO was entered
as `U` and tested on its own data.

---

## §1 — Step 1 coverage (the two extracts, frozen constants)

Both extracts derived with the detector exactly as committed — **no constant
loosened, no class scope widened, no gas-CC extension** (the layup confound is
untouched; rule 23 `[R-FROZEN-DERIVE]`).

```
scripts/data/derive_campd_unit_outages.py --iso NEISO --short-windows   --years 2023 2024 2025
scripts/data/derive_campd_unit_outages.py --iso NEISO --partial-windows --years 2023 2024 2025
```

| extract | file | windows | units | MW-days | class mix |
|---|---|---|---|---|---|
| short (1–5 d full stops) | `data/raw/campd-unit-outages-short-NEISO.csv` | **1** | 1 (Merrimack u2) | **691** | COAL ×1 |
| partial (sustained derates) | `data/raw/campd-partial-outages-NEISO.csv` | **0** | 0 | 0 | — |

Per year: 2023 → 1 window; 2024 → 0; 2025 → 0. The single row is
`Merrimack (2364) u2, 345.6 MW, 2023-02-01 → 2023-02-03, 2.0 d`.

**Why so few — this is a structural fact about NEISO, not a detector miss.**
NEISO's entire CEMS coal fleet in 2023–25 is **one plant**, Merrimack (2364),
units 1–2. Probe (instrumented copy of the derive script, scratchpad; the guard
line printed for every coal unit reaching it):

| year | unit | cap MW | raw annual CF | when-operable CF | guard |
|---|---|---|---|---|---|
| 2023 | u1 | 113.6 | 0.040 | 0.926 | PASS |
| 2023 | u2 | 345.6 | 0.046 | 0.611 | PASS |
| 2024 | u1 | 113.6 | 0.003 | 0.000 | FAIL |
| 2024 | u2 | 345.6 | 0.078 | 0.685 | PASS |
| 2025 | u2 | 345.6 | 0.086 | 0.772 | PASS |

Raw annual CF is **4–9 %**. Merrimack is a winter-reliability cycling unit, not
a baseload plant. The short extract is disjoint from the ≥5-day extract by
construction, and the standard extract already books Merrimack u2 **offline
~97 % of 2023** — so there is almost no running time in which a sub-5-day stop
could occur. **Materiality:** modelled `COAL_BIT` is **0.095 / 0.125 / 0.204 %**
of NEISO load in 2023/24/25, peaking at **102 MW** on a ~20–23 GW system — an
order of magnitude below rule 20's 2 % gating line, and far from the PJM case
that motivated the family (+3.0 GW of phantom coal in 22 summer tail hours).

## §2 — the branch point was **not** taken: the family is not inert

The prompt's stop-branch (adjudicate `I`) applies when the extracts cannot move
anything. The **partial half genuinely is** a provable no-op —
`unit_partial_outage_derate_factors` returns `{}` for all three years on the
empty file. **The short half is not.** Measured on the overlay itself:

* `unit_outage_short_derate_factors(2023, iso="NEISO")` →
  `{(2364, 'COAL'): …}`, **72 hours affected, h744–815**, multiplier **0.0000**.
* Merrimack's `COAL` bin in the NEISO fleet is **108.0 MW**; the row removes the
  unit's 345.6 MW share, which clips to **full derate** — the bin goes to zero.
* The standard ≥5-day overlay's multiplier over those same hours is **1.0000**,
  so the short window is genuinely **additive**, filling the Jan 25 → Feb 5 gap.
* `outage_end` is extended `+1 day` by the shared accumulator, so the mask runs
  **Feb 1 00:00 → Feb 3 23:00** — it covers the Feb 3 evening peak.

Those 72 hours contain **8 of 2023's top-22 NEISO prices**, including h811
(Feb 3 19:00, **$246.8**, the #4 hour of the year). Arming the family is
therefore a real, sharply-targeted change to the year's scarcity tail — it had
to be tested, not declared inert.

## §3 — the rejection: the window belongs to a unit **the model does not carry**, and is applied to one that **never stopped**

Merrimack's EIA-860 generators:

| gen | nameplate MW | net summer MW | status | in model fleet? |
|---|---|---|---|---|
| **1** | 113.6 | **108.0** | `OP` | **YES — it is the entire bin** |
| **2** | 345.6 | 330.5 | **`OS`** (out of service) | **NO** |
| GT1/GT2 | 18.6 ×2 | 16.8 ×2 | `OP` | (gas CTs, not COAL) |

The NEISO fleet's `(2364, 'COAL')` bin is **108.0 MW — exactly unit 1's net
summer capacity.** Unit 2 is excluded from the fleet by its `OS` status.

**The single detected window is unit 2's.** The overlay's accumulator keys on
the *plant* bin, not the unit, so it applies unit 2's outage at unit 2's
345.6 MW share against a 108.0 MW denominator — `345.6 / 108.0 = 3.2`, clipped
to full derate — and thereby zeroes **unit 1**.

Per-unit CEMS over the masked hours h744–815:

| unit | MWh | mean MW | max MW | hours > 0 | |
|---|---|---|---|---|---|
| **1** (the bin) | **7,444** | **103.4** | 123 | **72 / 72** | **never stopped** |
| 2 (window owner) | 4,161 | 57.8 | 320 | 24 / 72 | the unit that actually stopped |

Unit 1 — the only coal the model has — ran **every one of the 72 masked hours**
at a steady 103 MW. Across the top-price cluster it held a flat 121 MW while
unit 2 ramped 120 → 320 MW:

| hour | | unit 1 (in fleet) | unit 2 (not in fleet) | model bin |
|---|---|---|---|---|
| h808 Feb-03 16:00 | | 121 MW | 120 MW | 96 MW |
| h811 Feb-03 19:00 | | 121 MW | 315 MW | 96 MW |
| h812–815 Feb-03 20–23:00 | | **121 MW** | 319–320 MW | 96 MW |

**The keeper is already accurate here.** Its 95.7 MW mean sits within **≈7 %**
of unit 1's actual 103.4 MW. Arming the family does not correct a phantom — it
**deletes a unit that was measurably generating in all 72 hours**, across 8 of
2023's top-22 prices, during New England's Feb 3–4 Arctic outbreak. That is the
exact inverse of the PJM pathology the family was built for.

This is a **rule 14 `[R-ACCURATE]` rejection, not a fit rejection.** The accurate
measured input is the hourly per-unit CEMS series, and it refutes the derived
window's application. Rule 14 forbids reverting to an estimate because it fits
better; it does not oblige arming a derived artifact the underlying measurement
contradicts. Nothing was reverted, loosened, or tuned to a residual.

**Scope of the identity mismatch (context, NOT a verdict — rule 25).** Mapping a
unit's window onto its plant bin is generic overlay behaviour; its severity
scales with how much of a plant's CEMS-reporting capacity the fleet excludes. At
fleet level that share is small everywhere (non-`OP` coal net-summer ≈1.4 % PJM,
1.8 % MISO, 3.9 % NEISO), but the exposure is **plant-level and concentrated**:
here **75 %** of the plant's coal capacity is excluded, and that one plant *is*
NEISO's entire coal fleet. The PJM/MISO `K` cells are **not** adjudicated by this
session and no verdict transfers to them; whether any of their coal plants carry
a comparable per-plant exclusion is a cheap spot-check left to those lanes.

## §4 — why the window was emitted at all: the baseload guard is **degenerate in a fleet that is ~all outage**

`_when_operable_cf` measures CF over the hours **outside the unit's own ≥5-day
standard windows**. For a fleet already booked ~90–97 % offline, that clock is a
sliver of precisely the hours the unit was running — so the "baseload" test is
close to self-fulfilling:

| year | unit | operable hours (the guard's entire sample) |
|---|---|---|
| 2023 | u1 | 336 / 8760 (**3.8 %**) |
| 2023 | u2 | 528 / 8760 (**6.0 %**) |
| 2024 | u2 | 864 / 8760 (**9.9 %**) |
| 2025 | u2 | 816 / 8760 (**9.3 %**) |

Merrimack u2 clears the ≥0.55 guard at 0.611 on a **6 %** sample, while its true
annual CF is **0.046**. The guard's stated intent — "units that normally run near
their ceiling" — is not met: this unit does not normally run at all.

**This is NEISO-specific, and the PJM/MISO `K` cells are untouched by it.**
Operable-hour share for 2023 COAL units carrying ≥1 standard window:

| ISO | n | median | p10 | p90 | share < 0.15 |
|---|---|---|---|---|---|
| PJM | 97 | 0.62 | 0.16 | 0.90 | 7 % |
| MISO | 103 | 0.75 | 0.32 | 0.92 | 5 % |
| **NEISO** (Merrimack u2) | 1 | **0.06** | — | — | **100 %** |

In PJM and MISO the guard judges CF over most of the year and is well
conditioned. NEISO's sole coal unit sits **below both fleets' 10th percentile**.
The mechanism is sound where coal is baseload; NEISO's coal is not baseload, so
its identification basis collapses. No claim is made about any other ISO's cell.

## §5 — A/B arm (rule 15: registered either way)

Single arm, both flags set together — the two-arm split the prompt allows was
**unnecessary here and attribution is still unambiguous**, because the partial
extract is empty and its overlay is a measured `{}` no-op (§2). All movement is
the short half.

```
scripts/replay_keeper.py results/calibration/neiso61_netrev_margin \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --out-dir results/calibration/neiso69_shortpartial
```

Rule 16: all three years, sequential within the one invocation. Environment
pinned to the keeper's recorded package set (highspy 1.15.1 / pandas 3.0.5 /
pyarrow 25.0.0) so the delta is the mechanism, not solver drift.

<!-- A/B RESULTS -->

## §6 — DOF ledger

**Zero free parameters, zero residual solves.** Both entries are
measured-physical, mirroring the ercot129 / pjm-113 ledger treatment: the
window set is a pure function of CAMPD hourly gross under frozen detector
constants, and no value was fitted, swept, or chosen against a residual. The
rejection is likewise not a tuning act — the flags return to their default-off
state, so the keeper's DOF ledger is unchanged.

## §7 — observation filed, not chartered

NEISO's modelled coal fleet is **unit 1 only** (108 MW); Merrimack unit 2
(330.5 MW net summer, `OS` in EIA-860) carries no LP representation even though
it generated **~140–260 GWh/yr** of real NEISO energy across 2023–25 and ramped
to 320 MW in the Feb 3 2023 peak. Whether an `OS`-status unit that demonstrably
runs as a winter-reliability resource should enter the fleet is a genuine
representation question — but `COAL_BIT` is **0.1–0.2 % of NEISO load**, an
order of magnitude below rule 20's materiality line, so it cannot move a gate
and does not merit structural work. Filed as an observation; **no charter, no
mechanism, nothing armed.**

Corrected from this session's own first pass: an earlier cut compared the model
bin against **both** Merrimack units and read a "−41 % coal under-run". That
comparison was wrong — the fleet carries only unit 1, and against unit 1 the
keeper tracks actual to ≈7 % (§3). There is no in-window coal under-run to
explain.
