# PRE-REGISTRATION — pjm-133 `hydro_budget_nameplate_aware` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-caiso130-hydro-budget-nameplate-aware-2026-07-27.md`, **mirrored, not
copied**: PJM gets its own baseline, its own no-feedback ceiling and its own
PRIMARY, and §3 records exactly why the caiso-130 PRIMARY is *not* portable
here.

Owner ask: the caiso-130 cross-ISO hand-off (FINDING-caiso130 §5 item 4) —
*"3.6–6.7 % of PJM's hydro budget is undeliverable, ~10× CAISO's, and PJM's
keeper carries none of CAISO's evening-λ pin. Filed as an ask, not built."*
**Promotion is NOT pre-granted** and remains a separate owner act after
rule-22 LOYO.

Keeper under test: **`2026-07-25-pjm-121-cc-belt`** (bundle
`results/calibration/pjm121_ccbelt`, years 2023/24/25, `hydro_eia930_monthly=True`,
`hydro_backfill_year=2024`, `hydro_ror_split` and `hydro_min_flow_floor` **both
OFF**). Determination on the registered payload: **CALIBRATED, 10/10**.

Instrument for everything below: `scripts/probes/_pjm133_nameplate_precheck.py`
(committed with this prereg, **no LP anywhere in it**), reading the keeper's own
committed `hourly/*.parquet` sidecars — never a replay — plus the committed
`bench/PJM/<year>.json.gz` benchmark parts and raw EIA-860/923/930. Machine
output: `results/probes/pjm133_precheck.json`.

**Not re-measured here (FINDING-caiso130 §7, binding):** the cross-ISO blast
radius and the per-ISO undeliverable shares. §1's PJM row is quoted from
caiso-130 §1 and independently reproduced by this session's own precheck to the
0.1 GWh — it is not a re-derivation of the cross-ISO table.

---

## §1 — the delta (ONE switch, one mechanism, zero new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
scripts/replay_keeper.py results/calibration/pjm121_ccbelt \
    --out-dir results/calibration/pjm133_nameplate_B \
    --set hydro_budget_nameplate_aware=true \
    --note "pjm-133 nameplate-aware hydro budget target (single delta)"
```

- **Arm A** `results/calibration/pjm133_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `capacity-deliverability`
  partition (curated before either solve). NOT a keeper candidate; registered
  as the run explorer's control arm per rule 15.
- Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  **sequential** within each run (rule 12).
- Nothing else is bundled with this delta (FINDING-caiso130 §7).

**What the flag does** (`data/hydro.py::_nameplate_aware_scale`): the monthly
hydro LEVEL target is applied by water-filling under each plant-month's own
`nameplate × hours-in-month` ceiling and re-allocating the overflow pro-rata to
the plant-months that still have headroom, instead of a UNIFORM fleet-wide
monthly scale factor. The month total is met exactly wherever physically
attainable; where it is not, every plant sits at its bound and the shortfall is
LOGGED.

- **DRIVER (rule 14 `[R-ACCURATE]`)**: the nameplate is the accurate datum. The
  uniform scale silently pushed plant-months above a physical ceiling the LP
  then clipped (`P[g,t] <= pmax × availability`).
- **DOF added: zero** (rule 24). The bound is EIA-860 nameplate × the calendar.
- **Rule 13 `[R-MEASURED]`**: no outcome is pinned; the construction regenerates
  identically for a forward year and responds to changed conditions.
- **Rule 19 `[R-ONE-MECH]`**: not a new mechanism on a residual — the correct
  application of the level target the keeper already pins. It adds no floor and
  no bound; it moves budget between plant-months inside a preserved month total.
- **Rule 25 `[R-ISO-SCOPE]`**: the mechanism carries no ISO-fitted constant at
  all. Arming it on PJM changes no other ISO (per-run `ScenarioConfig` field,
  `getattr`-read at `data/fleet/assembly.py:1489`, no shared derived artifact).

**PJM differs from CAISO in one structural way that matters to every gate
below:** `hydro_ror_split` and `hydro_min_flow_floor` are **both OFF** on this
keeper, so there is no flat run-of-river class and **the entire re-allocation
lands on shapeable plants**. Per GWh, PJM's shaping ceiling is therefore
structurally larger than CAISO's — and the GWh are 1.7–40× larger.

## §2 — measured baseline, frozen BEFORE either arm (arm A expectation)

Read from the keeper's own committed `hourly/` sidecars.

**Hydro by hour-of-day window** (model − measured EIA-930 `NG: WAT`), MW:

| window | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight (hod 0-6) | +52.0 | +161.3 | +324.3 |
| belly (hod 9-15) | −181.7 | −138.1 | +229.7 |
| evening (hod 17-21) | −247.2 | −388.1 | −1273.3 |
| late (hod 22-23) | +414.2 | +555.2 | +491.9 |
| annual mean (model / measured) | 1667 / 1769 | 1740 / 1811 | 1651 / 1770 |

**C1 hydro volume** (model vs the committed `classFull.hydro` benchmark), TWh:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model | 14.599 | 15.245 | 14.464 |
| benchmark | 15.468 | 15.855 | 15.507 |
| **gap** | **−0.869** | **−0.610** | **−1.043** |

**Gated rubric levels** (`calibration_verdict.py --run-id 2026-07-25-pjm-121-cc-belt`):

| | 2023 | 2024 | 2025 | band |
|---|---|---|---|---|
| C3a mean LMP (model / actual RT-lw) | 31.19 / 29.55 = **+5.6 %** | 30.53 / 31.31 = **−2.5 %** | 41.53 / 45.80 = **−9.3 %** | ±10 % |
| C5a CO2 (model / eGRID, Mt) | 258.9 / 264.1 = **−2.0 %** | 264.7 / 273.3 = **−3.1 %** | 299.6 / 292.5 = **+2.4 %** | ±7 % |
| determination | CALIBRATED (10/10) | | | |

**Two rubric facts that shape §5–§6 and are recorded now so no gate below can
pass vacuously:**

1. **C1 scores the eight FOSSIL classes only** (CC_REGULAR, CC_CHP, CT_PEAKER,
   ST_GAS, ST_CHP, COAL_PRB, COAL_BIT, COAL_WC — 16/16 = 8 × two gated years).
   **Hydro is not a C1 criterion.** P1 is therefore a *benchmark-magnitude*
   gate against the committed `classFull.hydro` series (the same measured
   number the dashboard renders), not a rubric status flip. Stated so the
   result is never mis-sold as "closing a criterion".
2. **All of C1 and C2 are SKIPPED in 2025** (preliminary EIA-923 vintage —
   8 classes skipped for incomplete plant data, and C2's gas/coal families with
   them). Any C1/C2 gate scored only over *gated* records would pass 2025
   vacuously. K2 below is therefore defined over the **reported** model/actual
   pairs in all three years, with the status-flip limb restricted to gated
   records. C2 in the gated years is derivative of C1 ("all classes in band
   (C1)"), so it carries no separate kill.

**Delta energy budget** (no-LP `build_hydro_fleet` diff, flag off vs on):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| re-allocated | **851.5 GWh** | **573.4 GWh** | **1 042.3 GWh** |
| … as a share of the in-LP budget | 5.51 % | 3.62 % | 6.72 % |
| … as an annual mean | **+97.2 MW** | **+65.5 MW** | **+119.0 MW** |
| destination: shapeable (reservoir) | **100 %** | **100 %** | **100 %** |
| destination: flat RoR | 0 % (class not built — `ror_split` off) | 0 % | 0 % |
| clipped plant-months (flag off) | 127 | 150 | 150 |
| recipient plant-months | 711 | 607 | 678 |
| undeliverable, flag OFF | 851.5 GWh | 573.4 GWh | 1 042.3 GWh |
| undeliverable, flag ON | **0.0** | **0.0** | **0.0** |
| month-total drift | 3.6e-10 MWh | 3.8e-10 | 2.6e-10 |
| plant count A / B | 73 / 73 | 72 / 72 | 72 / 72 |
| donor implied CF *before* | 129.8 % | 120.2 % | 135.6 % |
| recipient implied CF *after* | 64.0 % | 65.6 % | 64.2 % |

Two readings of the last two rows, both registered now so neither can be
invented later. Donor CF > 100 % **is** the defect, stated in the units the
bound is written in. Recipient CF ≈ 64–66 % after the re-allocation means the
recipients retain ~35 % of their nameplate-hours as headroom — so unlike
caiso-130, **the freed water is not being handed to plants that are already
near-baseload**; the LP has room to shape it if its own λ surface rewards that.

## §3 — the caiso-130 PRIMARY is NOT portable to PJM, and this is why

caiso-130's PRIMARY was the **evening hydro window gap against measured
EIA-930 `NG: WAT`**. Registering that gate on PJM would be measuring a
confounded quantity, and the confound is measured, not suspected:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| EIA-930 `NG: WAT` annual (the pinned target) | 15.45 TWh | 15.82 TWh | 15.51 TWh |
| EIA-923 prime-mover-`HY` budget (unpinned) | 8.98 TWh | 8.86 TWh | 8.47 TWh |
| **pin uplift** | **+6.47 TWh** | **+6.95 TWh** | **+7.04 TWh** |
| implied CF of the 3 334 MW `HY` fleet at the target | 52.9 % | 54.2 % | 53.1 % |

**PJM files no `NG: PS` column** (ISNE does; verified against the raw extracts),
so PJM's `NG: WAT` carries pumped-storage generation. The model's budget-hydro
fleet is prime-mover `HY` only (3 334 MW, 72–73 plants) and PJM's **5 046 MW of
`PS` is built separately as storage** (`model/storage.py::load_eia860_pumped_storage`);
the keeper's own net-storage trace confirms it is dispatching that fleet
(−1 360 to −1 783 MW overnight charge, +793 to +1 297 MW evening discharge).
The pinned level therefore asks a 3.3 GW conventional fleet to deliver ~6.5–7.0
TWh/yr of energy that another part of the same model is already generating.

Consequences, all registered ex ante:

1. **The measured hour-of-day comparator is contaminated exactly where
   caiso-130's PRIMARY looked.** Pumped storage generates in the evening and
   not overnight, and its pumping appears in EIA-930 as *demand*, never as
   negative `WAT`. So the keeper's −247/−388/−1273 MW "evening deficit" and its
   overnight/late surplus are in substantial part a PS booking artifact, not a
   conventional-hydro shape defect. **No gate in this document scores a hydro
   window against measured `WAT`.** The window movement is REPORTED (P4) so the
   two sessions stay comparable, and is explicitly **not** a pass/fail.
2. **This delta must not be allowed to launder the pin.** The flag's own datum
   (nameplate × calendar) is accurate and the defect it closes is real; the
   contaminated *target* it serves is a **separate, pre-existing keeper defect**
   that this session neither fixes nor bundles (single delta). It is filed as
   its own ask in the finding.
3. **Rule 14 predicts what §5's kills are watching for.** The silent nameplate
   clip was, in the units rule 14 is written in, an inaccurate input quietly
   compensating for the PS-inflated pin: it was deleting 0.57–1.04 TWh/yr of
   phantom hydro before the LP ever saw it. Removing the clip **exposes** the
   pin rather than causing it. If the gates below regress, that is the
   discovered defect, not evidence against the nameplate bound.

## §4 — the NO-FEEDBACK CEILING, and what this delta CANNOT reach

**What it CAN reach — C1 hydro volume, exactly and no more.** The month total
is preserved, so the volume ceiling is precisely the re-allocated energy:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| C1 hydro gap now | −0.869 TWh | −0.610 TWh | −1.043 TWh |
| ceiling (full delivery) | **+0.851** | **+0.573** | **+1.042** |
| gap after full delivery | −0.017 | −0.037 | −0.001 |
| **share of the deficit the clip explains** | **98.0 %** | **94.0 %** | **99.9 %** |

That is the load-bearing pre-solve number: **PJM's entire C1 hydro volume
deficit is the nameplate clip**, to within 0.4–6 %. Stated before the solve.

**What it CANNOT reach — the price level.** The demand-weighted λ movement
under three allocations of the freed energy, from the keeper's own empirical
λ-vs-thermal-dispatch slope (50 quantile bins, no feedback):

| allocation | 2023 | 2024 | 2025 |
|---|---|---|---|
| flat over 8760 h | −0.031 | −0.033 | −0.071 |
| ∝ keeper hydro shape | −0.032 | −0.035 | −0.094 |
| concentrated in the top-10 % λ hours (worst case) | −0.037 | −0.057 | **−0.233** |
| C3a mean λ for scale | 31.19 | 30.53 | 41.53 |

**Stated before the solve, so it cannot be spun afterwards.** The 2025 C3a band
edge is `0.90 × 45.80 = 41.22 $/MWh`, i.e. **$0.31/MWh of headroom**. The
central (hydro-shape) estimate leaves $0.22 of that headroom and the
peak-concentrated worst case leaves $0.08. So on a no-feedback basis C3a-2025
**stays in band** — but caiso-126 measured the water-value feedback channel at
1.2–3× the fixed-λ proxy, and **1.4× the peak-concentrated estimate breaches
the band**. K1 below is therefore a live kill, not a formality, and this is
registered as a genuine risk rather than discovered afterwards.

**What it CANNOT reach — the hour-of-day shape.** Even granting the confounded
comparator its face value, +97/+65/+119 MW of annual-mean energy is 39 %/17 %/
9 % of the evening gap. This delta *adds deliverable water*; it does not
*re-time* the fleet. Any evening heal target is **not applicable to this
delta**, exactly as in caiso-130 §3.

**What it CANNOT reach — the pin.** The PS uplift is +6.5 to +7.0 TWh (§3). The
delta is 8–15 % of it and moves in the *same* direction. Nothing in this
document may be read as evidence about the pin.

## §5 — PRIMARY and SECONDARY gates (pass/fail, pre-registered)

**P1 — PRIMARY. The undeliverable-energy defect closes and the LP takes the
freed water, in ALL THREE years.** Two limbs, both required:
- **direction**: `hydro_TWh(B) > hydro_TWh(A)` and `|hydro − benchmark|`
  strictly smaller in B, in 2023, 2024 **AND** 2025. A single year moving the
  wrong way FAILS P1.
- **size**: the rise is at least **60 % of that year's re-allocated energy** —
  ≥ **+0.511 / +0.344 / +0.625 TWh**. Below that the LP is declining freed
  water that its own budget rows now permit, and the mechanism story is
  unsupported.

This is a *benchmark-magnitude* gate, not a rubric status flip — hydro is not a
C1 criterion (§2). Registered as magnitude on purpose, and it must not be
reported as a criterion closing.

**P2 — the mechanism identity check** (the caiso-130 P2 analogue, adapted).
In arm B: the solve log reports the nameplate-aware rescale; **0 MWh and 0
plant-months** above `nameplate × hours-in-month`; per-month budget totals equal
arm A's to `< 1e-6 MWh`; hydro plant COUNT equal to arm A's. Pre-verified in §2;
re-checked from the solved bundles.

**P3 — mechanism accounting stays clean.** In arm B the hydro class's D-2
forced share stays **0.0 %** (it is 0.0 % in all three years in arm A — PJM
arms no hydro floor), no other class's D-2 forced share moves by more than
**2 pp** per year, and no D-4 off-window share increases. The delta must not
re-arm or re-window an existing floor.
`legitimacy_diagnostics.json` is generated for **BOTH** arms before scoring.

**P4 — destination attribution, REPORTED not gated.** Where the freed water
lands by hour-of-day window (B − A hydro, mean MW and share of the annual
rise), and its feedback ratio against the §4 no-feedback ceiling. Not a gate:
§3 shows the measured comparator is PS-confounded. Reported so pjm-133 and
caiso-130 stay directly comparable.

## §6 — KILLS (pre-registered; any one fires ⇒ the delta is REJECTED as armed)

**K1 — the C3a guard (the ask's own required PJM guard).** The demand-weighted
mean-LMP error `|model/actual − 1|` may not increase by more than **0.75 pp** in
any of 2023/24/25. Baselines: **+5.6 % / −2.5 % / −9.3 %**, band ±10 %. The
bound is set at ~1.5× the §4 peak-concentrated no-feedback ceiling (0.51 pp in
2025) — inside caiso-126's measured 1.2–3× feedback range, so the gate can
actually fire. Direction is pre-stated: the delta lowers λ, which moves 2023
**toward** actual and 2024/2025 **away**.

**K2 — volume collateral (defined so it cannot pass vacuously).** Two limbs:
- **status limb**: no *gated* C1 class may move PASS → FAIL (2023/2024 only;
  2025's C1 is entirely SKIPPED, §2).
- **magnitude limb, all three years**: the sum of `|model − actual|` over the
  **eight C1 fossil classes PLUS hydro** may not increase by more than
  **0.5 TWh** in any year, using the verdict's reported model/actual pairs
  whether or not that record is gated.

Hydro is deliberately inside the sum. C1 scores fossil only, so a fossil-only
sum would be worsened by up to the full displacement *by arithmetic* — the
model sits below actual on nearly every fossil class in 2023/24, so moving
0.85/0.57 TWh out of thermal deepens those deficits one-for-one. A gate that
fires on an arithmetic certainty tests nothing. With hydro in the sum the two
legs net, and K2 measures the thing actually in question: **whether the
displacement lands on classes where it helps or where it hurts.**

Direction pre-stated: 2023/2024 the model is *below* actual on both hydro and
nearly all fossil, so a one-for-one displacement nets to **≈ 0** — the ex-ante
prediction is **neutral**, and a breach means the LP shed *more* thermal than
the hydro it gained (a commitment response, not a swap). 2025's model sits
*above* actual on COAL_BIT (+3.97 TWh) and CT_PEAKER (+7.90 TWh), so the
ex-ante prediction there is a **net improvement**.

**K3 — C5a CO2.** The CO2 error may not increase by more than **1.0 pp** in any
year and must stay inside the ±7 % target band. Baselines −2.0 / −3.1 / +2.4 %.
Ex-ante ceiling from the same displacement, bracketed by the measured
CC_REGULAR and COAL_BIT intensities: **−0.32 to −0.85 Mt (2023), −0.22 to −0.57
(2024), −0.39 to −1.03 (2025)** = 0.08–0.35 pp. So the 1.0 pp bound is ~3× the
ceiling. Direction pre-stated: worsens 2023/2024, **improves** 2025.

**K4 — rubric non-regression.** No rubric criterion that is PASS in arm A may
read FAIL in arm B. Arm A expectation: **all 10 PASS, determination CALIBRATED**
(C1/C2/C3a/C3b/C3c/C4/C5a/C6/C7/C8).

**K5 — no silent structural change.** Arm B's in-LP hydro plant COUNT and annual
budget TOTAL must equal arm A's, and the hydro class's D-2 forced share must
stay 0.0 %. The flag moves budget between plant-months inside a preserved month
total; it must not add, drop or re-zone a plant, nor create a floor.

**Basis check (not a kill, a precondition).** Arm A must reproduce the committed
keeper **digit-for-digit** on the hydro class and on every class, all three
years (max hourly |Δ| < 1e-6 MW). If it does not, the A/B is reported with an
explicit basis caveat and the HEAD window is bisected before any verdict is
quoted. caiso-130 cleared this and that is what removed its basis caveat.

## §7 — rule-22 LOYO

**Zero fitted parameters** — the bound is EIA-860 nameplate × the calendar; no
threshold, no percentile, nothing derived from a residual — so LOYO reduces to
per-year gate consistency, exactly as in FINDING-caiso126 §5 and
FINDING-caiso130 §6. Each of P1/P2/P3 and each kill is evaluated
**independently in each of 2023, 2024, 2025**, and the verdict must be
same-signed across all three. A gate that passes only in the aggregate, or a
movement confined to one year, is scored as a single-year artifact and blocks
promotion talk. There is nothing to re-tune and no re-tuning will occur.

Note the years are **not** interchangeable in size here: 2025 carries 1.8× the
re-allocation of 2024 and 1.2× that of 2023, and is simultaneously the year with
0.7 pp of C3a headroom. A kill that fires only in 2025 must be reported as a
**size-scaled systematic property**, not a single-year artifact — the same
reading FINDING-caiso130 §6 gave its own 2024-only K2 breach.

## §8 — scoring instrument and reporting

Scorer: `scripts/probes/_pjm133_nameplate_ab.py` (committed with this prereg).
It reads only the two solved bundles, their `legitimacy_diagnostics.json`, the
committed `bench/PJM/*` parts and raw EIA-930 — no solve, and no gate that is
not in this document.

Both arms are registered on the backcast dashboard **in-session** (rule 15),
whatever the verdict. Promotion is not granted here and is not requested by
this document (rule 1). If the gates regress while structural integrity
improves, the rubric-vs-control comparison is presented to the owner and the
call is theirs — this session does not self-promote.
