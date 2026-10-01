# PRECHECK — caiso-184: THE CAPACITY-BASIS MISMATCH (`f_CEMS > 1`)

**Pre-registration. Written and pushed BEFORE any measurement of this session's object
is taken and before any scored metric exists.** Every bar, every stop rule, every
attribution rule and the direction prediction below are fixed here. Nothing in this
document was informed by a number produced by this session's instruments; the
hypotheses are derived **from source** (file + line cited for each), which is the same
discipline caiso-181 §2c used and stated.

**Session** caiso-184, 2026-08-08. **Branch** `claude/caiso-184-capacity-basis-4z804a`.
**ISO scope: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d). No other ISO's
extract, keeper shard, registry sidecar, status part or bench file is read for a
verdict or written.

**Keeper at session start** `2026-08-08-caiso-183-b1-hour` — **NOT-YET**, rubric v3.1,
8 criteria, **C3a the SOLE FAIL** (2023 **+3.9 %** PASS, 2024 **+10.9 %** FAIL, 2025
**+13.9 %** FAIL; RT, band ±10 %). **DOF ledger 11 / 8.** `complete` **NOT held**
(withdrawn by the owner 2026-08-06). **HOLDOUT SPEND FREEZE ACTIVE.**
**2023 + 2024 + 2025 ONLY**, one bundle per arm (rule 16), years sequential, arms
sequential (rule 12). `calibration-complete.json` and `holdout-freeze.json` are
**OWNER ACTS — neither is written by this session.**

---

## 0. P0-1 — DO-NOT-REDO audit (rule 28 duty a)

The CAISO **in-model lever queue is EMPTY**; all nine `docs/mechanism-testing-matrix.md`
§5.2 items are struck. This charter must therefore prove it is a **different object**
from every closed one, and stop if it is not.

**It is NOT the settled envelope-DEPTH question (caiso-181, SETTLED).** caiso-181 asked
whether the detector asserts unavailability its own CEMS record contradicts, and answered
**no, at exactly zero** across 599,736 interior in-window hours. That question is about
**which hours** are asserted unavailable. This charter touches **no window, no hour, no
detector constant and no detection threshold**. The `f_CEMS > 1` term caiso-181 isolated
in §2a is the residue it explicitly **could not** own: *"CEMS gross exceeding the bin's
entire EIA-860 nameplate, which no availability envelope can represent"* (§2a) and
*"belongs to the fleet-capacity lane. Reported, not acted on"* (§5 item 2). This charter
is that named, filed, un-owned item.

**It is NOT the grain seam (caiso-183, CLOSED and PROMOTED).** caiso-183 repaired the
day↔hour round-trip in the outage CSV, driving in-window CEMS contradiction to exactly
zero and cutting the envelope-excess term by 69 / 75 / 75 %. What it did **not** and
**could not** touch is the `f_CEMS > 1` term, which lives **above** the `f_CEMS = 1`
line where no availability multiplier — at any grain — can reach. Post-repair that term
is what **dominates** the remaining 2.00 / 2.22 / 1.38 % of depth (caiso-183 §4).
This charter adds **no grain**, re-derives **no extract**, and does not re-open BE-3.

**It is NOT any struck §5.2 lever.** `battery_dispatch_adder` (permanent declared-residual
DOF, three exits closed at caiso-176/178/179) is not re-opened or re-derived. The
measured-offer-surface **coverage** extension (caiso-182, both identification tests
failed) is not re-attempted. The AS-power-reservation family (caiso-74/127/129), every
N–S topology lever (caiso-164 §0/§6, **FORBIDDEN**), the seam/intertie family
(caiso-142/143/167, STRUCK), `caiso_ps_charge_shape_anchor` (`G`, input walled) and
`unit_outage_short_windows` / `unit_partial_outage_windows` (caiso-136/180, `I` —
coal-only detectors against a CAMPD CAISO population with **zero coal**) are all
untouched. `caiso_dam_outages` stays `U` and is **NOT armed here**.

**Adjacent-but-distinct, and named so it cannot be confused later.** `cc_capacity_reconcile`
(CAISO cell `U`) and the always-on merchant-CC summer guard
`fleet._reconcile_cc_pmax_to_nameplate` both live in the same lane and are **explicitly
OUT OF SCOPE** (§5). This charter neither arms the reconcile, nor re-derives its table,
nor changes the guard.

**Conclusion: distinct object, DO-NOT-REDO clear, proceed to P0-2.**

---

## 1. THE OBJECT, restated at source precision

caiso-181 §2a's **BASIS** term is `Σ_t (f_CEMS − 1)⁺ × pcap`, where

* the **numerator** is CAMPD **`grossLoad`**, summed over the bin's units
  (`scripts/probes/_caiso181_cems_confrontation.py::_year_grids`), and
* the **denominator** `pcap` is `outages._iso_plant_capacity(CAISO)` —
  `Σ pmax_mw` over `(plant_code, plant_group)` on the EIA-860 fleet
  (`src/market_sim/data/outages.py:436-479`).

`fleet/eia860.py:1007-1009` sets **`pmax = net_summer_capacity_mw`**, with nameplate only
as a fallback when the summer figure is missing or ≤ 0. So caiso-181's phrase *"the bin's
entire EIA-860 nameplate"* is **imprecise, and this charter corrects it**: for CAISO that
denominator is **NET SUMMER**.

Worse, for **CC bins it is not the LP's capacity at all.** The CAISO keeper runs
`cc_nameplate_summer_derate=True` (`pipeline/backcast_config.py:1744`, armed for PJM /
NYISO / NEISO / CAISO), under which `fleet_to_bins` divides the CC bin's summed capacity
by `cc_summer_derate_ratio = net_summer / nameplate` so **the LP carries full nameplate**
(`fleet/campd_bins.py:1684-1694`), and the seasonal derate is re-applied inside the
availability matrix in **summer months only** (`fleet/arrays.py:738-748`).

Three capacity quantities are therefore in play and **caiso-181 measured against the one
the LP does not hold**:

| id | quantity | basis | source |
|---|---|---|---|
| **D1** | `_iso_plant_capacity` — the outage-derate denominator, and caiso-181's `f_CEMS` denominator | **net summer** | `outages.py:436`, `eia860.py:1007` |
| **D2** | the binned fleet's actual LP `pmax` sum per `(plant, group)` | **nameplate** for CC (keeper config), net summer otherwise | `campd_bins.py:1691` |
| **D3(t)** | `Σ pmax × availability(t)` — the LP's hourly capability ceiling, every overlay live | as D2, seasonally derated | `arrays.py` |

---

## 2. HYPOTHESES — all four derived from source, NONE measured

### H-GROSS — numerator basis (diagnostic only)
CAMPD reports **gross**; every model capacity is **net**. The committed measured artifact
`data/raw/_processed-legacy/parasitic_load_factors.parquet`
(`scripts/data/derive_parasitic_factors.py` → `campd.compute_parasitic_factors`) supplies
per-plant net/gross; the class fallbacks are `campd.DEFAULT_PARASITIC_LOAD_PCT` —
**CC 2.5 %, ST_GAS 5.0 %, CT 1.0 %**. On its own this inflates `f_CEMS` by ≈ **+2.6 %**
at a CC bin, **+5.3 %** at ST_GAS. **Predicted: real, and entirely a property of the
DIAGNOSTIC, not of the model.**

### H-NPBASIS — denominator basis in the diagnostic (CC bins; diagnostic only)
`f_CEMS` divides by **D1** (net summer) while the LP holds **D2** (nameplate) for CC.
The inflation is exactly `1 / cc_summer_derate_ratio`. The committed CAISO evidence
records the gap as material: `campd_bins.py:1680` cites *"up to −27 % for Moss Landing"*,
and `cc_capacity_reconcile_CAISO.csv` carries Moss Landing at 1398.0 MW current against
1470.0 MW EIA-860 winter. **Predicted: the DOMINANT term, and the reason caiso-181 found
the excess "concentrated at the CC bins" — CC is precisely the class whose LP basis
differs from D1.**

### H-DENOM — a REAL model defect, if it survives (the only branch that can license an arm)
`fleet/arrays.py:929` calls `unit_outage_derate_factors(...)`, whose per-row derate share
is `removed_mw / plant_capacity_mw` (`outages.py:524-548`) with `plant_capacity_mw` = **D1
(net summer)**. But the extract's `removed_mw` is written by
`scripts/data/derive_campd_unit_outages.py::build_capacity_index`, whose `derate_mw` is
**EIA-860 NAMEPLATE** (CC-steam-augmented), and whose own docstring states the invariant
it believes it satisfies:

> *"so the plant's CT shares sum back to the full block (CT + steam) — **the same basis as
> the model bin denominator the derate divides into**"* (`derive_campd_unit_outages.py:244`)

**That invariant is VIOLATED on every non-ERCOT ISO**: numerator nameplate ÷ denominator
net summer. The removed **fraction** is inflated by `nameplate / net_summer`, so the model
removes **more MW than went out** at every multi-unit plant — the identical failure mode
`_iso_plant_capacity`'s own docstring documents for `cc_steam_part_reclass` (NEISO 6081
Stony Brook, *"46 % more than actually went out"*, `outages.py:445-455`), forwarded for
**that** flag and never for this basis. A **third** basis enters at the
`source == "observed_peak"` fallback rows, whose `derate_mw` is the unit's CAMPD peak
**gross** (`derive_campd_unit_outages.py:343`).
**Predicted sign: over-removal ⇒ CC availability under-stated ⇒ over-pricing.**
Single-unit plants are unaffected (their share clips at 1.0 either way).

### H-REMAP
Plants **62115 / 62116** (AES Alamitos / Huntington Beach) route through
`campd.CAMPD_UNIT_PLANT_REMAP`. The CEMS facility's unit population need not equal the
fleet's generator population at the remap target, so the bin denominator can cover fewer
machines than the numerator. **Predicted: small, plant-specific, and a coverage question,
not a basis question.**

---

## 3. P0-2 — THE CENSUS (design fixed here)

Instrument: `scripts/probes/_caiso184_capacity_basis_census.py`, **REUSING**
`_caiso181_cems_confrontation._year_grids` (NaN preserved — a missing hour is never a
contradiction), `campd.CAMPD_UNIT_PLANT_REMAP`, `outages._generic_unit_outage_target`,
`outages._iso_plant_capacity`, the shipped `fleet_to_bins` path for D2/D3, and the
committed `parasitic_load_factors` artifact. **No new intake. No fetch. No LP.**

Per `(plant_code, plant_group)` × year ∈ {2023, 2024, 2025}, over all 8760 h:

* **N1** = CAMPD gross on the model clock; **N2** = N1 × measured parasitic factor
  (pooled artifact; `DEFAULT_PARASITIC_LOAD_PCT` fallback by class).
* **D1 / D2 / D3(t)** as §1.

**Excess capacity-year** `X(N, D) = Σ_t (N_t − D_t)⁺ / 8760` MW-yr, reported for
`(N1,D1)` — *this is caiso-181's basis term* — and for `(N2,D1)`, `(N2,D2)`, `(N2,D3)`.

**Attribution rule, fixed now** (shares of `X(N1,D1)`):

* `H-GROSS  = [X(N1,D1) − X(N2,D1)] / X(N1,D1)`
* `H-NPBASIS = [X(N2,D1) − X(N2,D2)] / X(N1,D1)`
* `RESIDUAL  =  X(N2,D2) / X(N1,D1)`  ← the only part that can be a model defect
* `H-REMAP` is reported as the 62115/62116 share of RESIDUAL, not as a separate subtraction.

**H-DENOM is measured separately** (it is about the derate *share*, not about `f_CEMS`):
for every CAISO unit-outage row in each year, `removed_mw / D1` against `removed_mw / D2`,
converted to MW-h of **over-removal** against the year's committed envelope depth.

---

## 4. BARS AND STOP RULES — fail-closed, fixed before measurement

* **B-ATTRIB (charter P0-2, GATING).** `H-GROSS + H-NPBASIS + H-REMAP` must jointly
  attribute **> 50 %** of `X(N1,D1)` in **every** year. If they do not, the mechanism is
  **NOT IDENTIFIED**: say so, **STOP, spend no LP, register nothing**.
* **B-ARTIFACT (the null branch — a REAL, publishable outcome, not a fallback).** If
  `RESIDUAL` is **< 0.5 %** of that year's committed envelope depth **AND** **< 0.2 %** of
  CAISO's thermal capacity-year, then **the LP's capacity basis is NOT contradicted by its
  own CEMS record**: caiso-181's BASIS term is a **diagnostic-basis artifact** of comparing
  gross to net and net-summer to a nameplate-basis LP. In that branch this session
  **registers nothing, spends no LP**, corrects caiso-181 §2a's language, and escalates the
  PS intake. **This branch may NOT be converted into a lever.**
* **B-DENOM (the only branch that licenses an LP arm).** H-DENOM justifies an arm **only**
  if the measured over-removal is **≥ 2 %** of the year's committed envelope depth in at
  least two of the three years. Below that it is filed as measured-and-immaterial and **no
  arm is solved**.

**Decision tree (pre-registered, no discretion at read time):**

| branch | condition | action |
|---|---|---|
| **A** | B-ATTRIB fails | **STOP.** Not identified. No LP. File. |
| **B** | B-ATTRIB passes, B-DENOM < 2 % | **NO ARM.** File as artifact + immaterial defect. Correct the record. Escalate PS. |
| **C** | B-ATTRIB passes, B-DENOM ≥ 2 % | Build the §5 repair. **ONE control + ONE treated arm.** |

---

## 5. THE REPAIR, named in advance — and everything it is NOT

**If and only if branch C fires:** put the outage-derate **denominator on the same basis as
the extract's `removed_mw` numerator** — EIA-860 **nameplate** — restoring the invariant
`derive_campd_unit_outages.py:244` already declares, exactly as `_iso_plant_capacity`
already forwards `cc_steam_part_reclass` for the identical reason (`outages.py:445-455`).

* **ZERO DOF. ZERO new fitted scalars.** The nameplate is EIA-860's published
  `nameplate_capacity_mw`, already read by the deriver. No ratio is fitted, no threshold
  re-valued, no frozen identification constant touched (rule 23 `[R-FROZEN-DERIVE]`).
* **Gated by ONE new default-off `ScenarioConfig` field**, armed for CAISO only in this
  session, so PJM / NYISO / NEISO / MISO / ERCOT are **byte-unchanged** (rule 25, G-SIXISO).
  Its matrix row lands in the **same PR** (rule 28 duty c).
* **Monotone by construction**: nameplate ≥ net summer, so the repair can only ever
  **reduce** a removed fraction. A row whose removed MW **increases** is a stop-the-line
  event (**G-MONO**).

**NOT licensed by this charter, and not to be reached for if branch C's arm disappoints:**
arming `cc_capacity_reconcile` for CAISO; re-deriving `cc_capacity_reconcile_CAISO.csv`;
changing `_reconcile_cc_pmax_to_nameplate`; introducing a seasonal winter-capacity basis;
touching the detector, any window, any grain, or `caiso_dam_outages`.

---

## 6. P0-3 — BYTE-EQUIVALENCE (ercot-174 BE-1/BE-2/BE-3 discipline)

* **BE-1** — with the change present and the gate **absent**, `_iso_plant_capacity` returns
  a map **identical** to pre-change for **all six ISOs**, asserted against a snapshot taken
  **before** the change is written.
* **BE-2 / G-SIXISO** — the full `(ISO, year)` availability digest over the outage-derate
  consumer leg is **bit-identical** for the five non-CAISO ISOs with the gate armed for
  CAISO only.
* **BE-3** — **no data file is re-derived or rewritten by this session.** The extract stays
  at caiso-183's adopted hour-grain `25360e90…`. Asserted by sha256 ledger.
* A **test** lands with the change covering BE-1 and G-MONO (charter P0-3).

---

## 7. P0-4 — DIRECTION PRE-REGISTERED AS **UNKNOWN**

Raising a CC bin's effective capacity basis **raises available capability** and therefore
**likely LOWERS price** — into a model already **+10.9 % / +13.9 %** over in 2024/2025.
**That is a PREDICTION, not a TARGET.** It is recorded so that a move in that direction
cannot later be presented as corroboration it was not designed to be, and so that a move
in the **opposite** direction is reported as a falsification rather than explained away.

**C3a IS REPORTED, NEVER TARGETED, AND IS NEVER THE PROMOTION BASIS** (rule 1
`[R-STRUCT]` — it is a live FAIL; rule 13 `[R-MEASURED]` — nothing is tuned to it). The
only admissible promotion basis is that **the model's capacity basis stops being
contradicted by its own CEMS record**. **If the residual does not close, this session says
so plainly.**

---

## 8. GATES — pre-registered, fail-closed

**Deliberately NOT keyed to the caiso-180 regeneration leg.** caiso-183 proved that
construction malformed **twice** (G-DEPTH′, G-CAISO180) for one shared reason — it presumes
the repair is that leg's inverse — and both withdrawals are still with the owner. Every bar
below is sized on **this mechanism's own physics**.

| gate | bar |
|---|---|
| **G-DOF** | DOF ledger **EXACTLY 11 / 8**. Any increase is an **automatic FAIL**. |
| **G-NOFIT** | **ZERO** new fitted scalars. The basis is EIA-860-published or it does not enter. No value tuned to a residual. Frozen detector constants unmoved. |
| **G-SIXISO** | The other five ISOs' fleets and availability digests **byte-unchanged** (§6 BE-1/BE-2). |
| **G-BASIS** | The repaired basis reduces measured `f_CEMS > 1` capacity-year by **≥ 50 %** **without** pushing any bin's `f_CEMS` materially **BELOW** its measured demonstrated output. Over-correction fails exactly as under-correction does. |
| **G-MONO** | The repair may only **reduce** a removed fraction. Any row whose removed MW increases is **stop-the-line**. |
| **G-CONSIST** | Post-repair, every CAISO outage row's derate share is taken against the capacity the LP actually holds — asserted in code **and** in a test. |
| **G-C1** | C1 free-class fuelmix **PASS on every free class, all three years**. |
| **G-PROT** | C6 and C8 **PASS**; C8 stays **SCORED** (`legitimacy_diagnostics.json` registered with every bundle). |
| **G-LOYO** | Any verdict flip scored **leave-one-year-out within 2023–2025 BEFORE** promotion. |
| **CONTROL** | **MANDATORY if any arm solves.** Reproduced via `--replay-bundle results/calibration/caiso183_b1_hourgrain` (never a remembered CLI string). Measured at **FULL precision, hour by hour**; the noise floor is **quoted before any treated delta is read**. caiso-183's correction is inherited: same-head drift is **NOT bit-zero** (2023/2024 churn −0.0027 / −0.0024 $/MWh on the **zero-demand WECC import nodes**, LP alternate optima). Distinctness uses `scripts/probes/_caiso183_arm_identity.py::check_arms_distinct` (**hourly signature**); caiso-180's derate-census check is **INVALID** for an input-only delta. The solve cache is **purged between arms** (caiso-183 §6). |

---

## 9. STANDING DATA BLOCKER — declared, not a session lever

C3a's **first named contributor** remains the **WALLED hourly pumped-storage water state**
(`FINDING-caiso140` §B / caiso-141 A2). No public source exists; it is an **OWNER-FUNDED
INTAKE decision**. This session attempts **no proxy, no split heuristic, and no PS
mechanism of any kind**. If P0 concludes the basis mismatch cannot be identified from repo
data, the session **registers nothing, spends no LP, files that result, and escalates the
PS intake to the owner as the only remaining named route.**

## 10. Governance commitments

Rule 1 `[R-STRUCT]` — no mechanism judged by its effect on the fit; C3a reported only.
Rule 13 `[R-MEASURED]` — every input is EIA-860-published or CAMPD-measured and
forward-reproducible; **no measured outcome, no price residual, no benchmark enters any
input**. Rule 14 `[R-ACCURATE]` — a consistency repair that worsens the fit **stays** and
the root cause is opened, never buried back in an inaccurate input. Rule 15 / 16 — every
arm that solves is registered with `legitimacy_diagnostics.json`, all three years in ONE
bundle; if no arm solves, that absence is **stated explicitly** so it is not read as a
skipped registration. Rule 19 `[R-ONE-MECH]` — the repair replaces a basis, it does not
stack a second derate on the first. Rule 21 `[R-DOF]` — ledger stays 11 / 8. Rule 22
`[R-HOLDOUT]` — **2023–2025 only**; the spend freeze is respected; both markers untouched
(owner acts). Rule 23 — no derive re-run, no identification constant re-valued. Rule 24
`[R-REGISTRY]` — any tunable appears in `ScenarioConfig` and the run's `run_config.json`;
no env knob, no hardcoded per-plant dict. Rule 25 `[R-ISO-SCOPE]` — CAISO-scoped; no verdict
transfers. Rule 27 `[R-PUSH]` — this pre-registration is pushed and blob-verified **before
any measurement**; every push blob-verified; no existing ≥300-line source file rewritten
from regenerated content. Rule 28 `[R-MECH-MATRIX]` — the CAISO cell and §5.2 header are
stamped **in this session**, whatever the outcome, including a null one.
