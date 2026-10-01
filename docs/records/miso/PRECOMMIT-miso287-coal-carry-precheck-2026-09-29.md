# PRECOMMIT — miso-287: zero-LP pre-check of a pooled coal stock-carry, written before it is measured

```
LANE    : miso-287 (owner ruling "P1 vs P0 residual (Recommended)", miso-286 §6)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds + keeper committed P1 hourly sidecars
PROBE   : scripts/probes/_miso287_carry_precheck.py (written after this file is committed)
STATUS  : pre-registration. No number below §4 exists yet.
```

## 1. What phase 0 found (already measured, recorded in the FINDING)

1. **The miso-285 stack clear used the wrong quantity.** It cleared the P0 offer stack at the
   keeper's non-VRE generation, which includes **biomass + OTHER**: must-run residual classes that
   `run_calibration_full` injects from EIA-923 and nets out of LP demand
   (`_INJECTED_MUSTRUN_CLASSES`). They are not LP rows. At the corrected quantity the base stack sits
   **$0.8–1.5 below P1 in every year**, not "±$0.3 in 5 of 7".
2. **The P1 startup markup is +$0.3–0.7 in every year.** It is not the 2022/2025 driver.
3. **Congestion is not the driver.** The Midwest is one price at night in every year; the 2022 gap
   is *larger* in hours where MISO-South is not separated.
4. **The driver is the pooled coal fuel-inventory row (`coal_fuel_inventory`, miso-259, K).**
   On 2022 summer nights P1 runs coal **16.6 GW below** the base-cost merit clear at the same
   quantity and backfills with CC_REGULAR (+13.4 GW), at a $65 night median against coal offers
   near $32. 2025: −2.2 GW; 2023: ~0. The keeper's monthly coal energy is **flat at 20.2–20.9 TWh
   from May to September 2022** (CAMPD: 24.3 Jul, 23.2 Aug) and over-runs CAMPD in the shoulder
   months: the flat `annual/12` cap binding in peak months.

That flat grain is the row's **stated limitation** (module docstring; matrix cell text, miso-259:
"THE NAMED SUCCESSOR is an SOC-style stock-carry row family, built BESIDE this field"). It was never
built.

## 2. The candidate

**Pooled cumulative carry.** Replace the twelve independent pooled rows

    sum_{t in m} HR·P  <=  B/12                        (m = 1..12)

with twelve cumulative month-end rows of the same identity

    sum_{t <= end of m} HR·P  <=  S_dec·hc + (m/12)·R·hc      (m = 1..12)

where `B = (S_dec + R)·hc` is the existing annual budget, `S_dec` the Dec(Y-1) opening stock and `R`
the prior-years delivery rate. At `m = 12` it is the annual row exactly. **Zero new parameters**
(rule 21): every term is one the flat rows already read. Receipts stay flat ratable, so no year-Y
timing enters (rule 13). Minimum stock stays zero, as in the incumbent. It **replaces** the flat
rows rather than stacking on them (rule 19). The per-yard annual rows (`_plant_grain`, K) are
untouched.

Physically: the opening pile can be drawn in any month, and deliveries arrive ratably. The flat form
instead forbids drawing more than 1/12 of the opening pile in any month.

## 3. The pre-check (zero LP)

Per year 2019–2025, on the fleet-only rebuild of the keeper recipe:

- **Emulator.** A binding energy row on a fuel acts, in the LP, as a uniform adder `λ` ($/MMBtu × HR)
  on every coal row over the row's hours. Emulate it by clearing the base-cost stack + startup
  markup (the `_miso287_p1_residual` bid stack) at the keeper's P1 thermal quantity, with coal offers
  raised by `λ·HR`, and bisecting `λ ≥ 0` so the coal MMBtu over the row's hours meets the row.
  - **FLAT** (the incumbent): one `λ_m` per month against `B/12`.
  - **CARRY** (the candidate): cumulative rows. Solved as the LP would: find the smallest-`λ`
    sequence such that every cumulative constraint holds. Implementation: one `λ` per contiguous
    binding block, found by forward pass (if the unconstrained cumulative path breaches at month `m`,
    the months up to `m` share one `λ` sized to meet `C_m` exactly; repeat from `m+1`).
- **Validation (gate V).** The FLAT emulation must reproduce the keeper's **P1 2022 night median
  within ±$1.5** (P1 = $48.05). If it fails, the emulator does not describe the LP and the pre-check
  is void. The lane then stops and reports, and no shard is launched.
- **Prediction.** Night (h0–5) median under CARRY minus under FLAT, per year.
- **Also reported, not gating:** annual and Jul/Aug coal TWh under each form against CAMPD, and C3a
  direction (mean price move vs the hub).

The per-yard annual rows are not emulated. The emulator therefore omits a constraint the LP carries,
which makes the CARRY prediction an **upper bound** on relief. Gate V is what shows whether the
omission matters.

## 4. Kill rule (fixed now)

The lane launches **no shards** unless **all** hold:

1. Gate V passes.
2. CARRY moves the **2022 night median down by ≥ $2.0** against FLAT.
3. CARRY moves no year's night median **up** by more than $0.5. A cumulative row can move burn
   earlier as well as later, so this sign test is not vacuous.

If 1–3 hold, the next step is a build (default off) plus a PRECOMMIT for the seven per-year shards
(miso-280 template §7/§8), launched only on the owner's card. If any fails, the result goes into the
FINDING and the owner gets a card. **No threshold above moves after the probe runs.**

## 5. What this does not claim

- It does not claim the carry fixes C3a 2022. C3a is a mean-price criterion over all hours. This
  pre-check sizes night medians only, and C3a is reported beside it.
- It does not tune anything. There is no free value in the candidate to tune.
