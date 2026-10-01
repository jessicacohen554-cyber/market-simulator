# FINDING — nyiso-118: the SENY ORDC span fix, armed and promoted on structure

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 · **Keeper at
session start:** `2026-08-03-nyiso-117-nyc-rcpf` · **Keeper at session end:**
`2026-08-03-nyiso-118-seny-span`
**Pre-registration:** `results/calibration/PREREG-nyiso118-seny-span-2026-08-03.md`
(committed and pushed **before** either solve).

---

## §1 — headline

`nyiso_ordc_measured_step_span` — matrix cell **`U`**, implemented but never
armed — was **armed, solved against a mandatory same-HEAD zero-delta control,
and PROMOTED**. Determination **CALIBRATED-WITH-CAVEATS**, C3c the sole ledgered
caveat, **unchanged**. **All 18 scored numeric fields are EQUAL to the control's.**
DOF ledger **31 → 32** entries with **n_residual UNCHANGED at 6**.

**The promotion rests on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`, and the
residual deliberately did not move.** Rule 1 is explicit that a
structurally-correct mechanism is never rejected or reverted because the residual
didn't move. The static 1,300 MW span was an **estimate leaking into a curve
whose balance row is measured** — exactly what rule 14 forbids keeping once the
accurate input is in hand.

| arm | run id | bundle |
|---|---|---|
| CONTROL | `2026-08-03-nyiso-118-control-zerodelta` | `nyiso118_control` |
| TREATMENT | `2026-08-03-nyiso-118-seny-span` | `nyiso118_seny_span` |

## §2 — what the mechanism is (a construction fix, not a lever)

`nyiso_dynamic_reserve_requirements` — already armed on the incumbent keeper —
puts the **measured** hourly reserve requirement on the balance row. But the ORDC
demand curve priced *against* that row was still built off the **static
published** MW. The flag scales each dynamic family's width vector by
`requirement[t] / requirement_static`, restoring the identity **total step width
== the hour's requirement**.

**It introduces no new number** (rule 5 `[R-NO-MAGIC]`): the scale factor is the
ratio of two already-committed measured inputs, and the published RCPF penalties
are requirement-**independent** — measured unchanged by the flag. That is why the
ledger gains an entry but **no free parameter**.

The defect is measured, not inferred. SENY's total step width differed from its
own requirement in **6,239 / 6,249 / 6,231** hours of 2023/24/25 in the control
and **0 / 0 / 0** in the treatment.

## §3 — the scope question was settled EX ANTE, on CONSTRUCTION

`scripts/probes/_nyiso118_span_construction_probe.py` builds the NYISO
`ReserveDesign` **twice at one HEAD** on the keeper's reserve flags and diffs
every family's `requirement`, `ordc_penalties` and `ordc_step_widths` — **no LP,
no dual**. That is deliberate: `dual` and `held_mw` are **solved co-optimization
outputs**, and gating byte-identity on them can only pass when the mechanism does
nothing (the nyiso-115 G2 error).

| family | widths | requirement | penalties | reachable price |
|---|---|---|---|---|
| `li_30min_total` | **IDENTICAL** | IDENTICAL | IDENTICAL | IDENTICAL |
| `nyc_10min_total`, `nyc_30min_total` | changed (185/227/120 h) | IDENTICAL | IDENTICAL | **IDENTICAL ($0.000)** |
| `seny_30min_total` | changed (6,239/6,249/6,231 h) | IDENTICAL | IDENTICAL | **CHANGED (max $437.50/$437.50/$375.00)** |
| `east_10min_total`, `li_10min_total`, `nyca_10min_spin`, `nyca_10min_total`, `nyca_30min_total` | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL |

### §3.1 — the one live coupling did NOT occur

The LI locational ladder (`nyiso_li_locational_reserve`, **armed on the keeper**)
already applies this **same** span translation family-scoped and unconditionally
to `li_30min_total`, deliberately without flipping the global flag — so arming it
globally could have **double-applied**.

**`li_30min_total` is byte-identical between arms in all three vectors, all three
years. K-A did not fire.** The guard's `or` in
`if name in dynamic_req and (measured_step_span or name in span_scaled)` is
**boolean, not additive**, and LI's family-scoped entry has already normalized
its widths, so the global flag finds nothing left to scale.

### §3.2 — two corrections to the record, both MEASURED

1. **The blast radius is THREE families, not one.** `_nyiso_design`'s docstring
   claimed the flag is a "No-op wherever measured == static (NYCA, East, NYC)".
   **That is false for NYC**: NYC's measured requirement dips *below* its static
   base in **185/227/120** hours (mean 490.8 vs 500 MW). The docstring was
   corrected against the probe in this session.
2. **But NYC is re-REPRESENTED, not re-PRICED — the rule-23 freeze holds.**
   Shortfall is bounded above by the hour's requirement (`held ≥ 0`), so band
   width beyond `requirement[t]` is **unreachable padding**; and under the frozen
   `nyiso_nyc_rcpf_step_curve` that family is a **single flat band** at the
   published $25 RCPF. Trimming padding off a flat band cannot move a price. The
   reachable price function is **pointwise identical ($0.000, 0 hours, all three
   years)**, so **K-B did not fire**.

That three-way split — SENY re-priced, NYC re-represented, LI untouched — is also
what demonstrates the construction instrument **has discriminating power**. It is
not a gate that can only pass by doing nothing.

## §4 — gates: all six PASS, no kill fires

| id | gate | result |
|---|---|---|
| G1 | span live, construction identity restored | **PASS** — 6,239/6,249/6,231 → 0/0/0 |
| G2a | scope: every family's `requirement_mw` float32-EXACT | **PASS** |
| G2b | LI no-double-apply (widths + requirement + penalties) | **PASS** |
| G2c | ORDC step count unchanged, from the solve log | **PASS** — 59/59/59 in **both** arms |
| G3 | LP row identity (`held + shortfall ≥ requirement`) | **PASS** |
| G4 | no feasibility damage | **PASS** — zero slack, zero dump, both arms |
| G5 | span / holdout | **PASS** — 2023–2025 only; freeze ACTIVE, untouched |
| G6 | scoring both arms | **PASS** — determinations identical |

**K-A … K-E all silent.**

G2c is worth naming: the step count is **unchanged**, exactly as pre-registered,
because the flag re-spans widths and adds or removes **no** steps. It is an
instrument that never touches the parquet, committed as each bundle's
`ordc_steps.log`.

## §5 — the PARTIAL was pre-registered and it HELD

**This does NOT close the S-OVER finding and is not reported as doing so.**

The flag re-spans **widths only**. SENY's penalty vector is measured **unchanged**
and its **first rung is still $62.50** — already above the **entire** measured
envelope ($23.92 / $30.37 / $40.00 in 2023/24/25, with 52 hours of 2025 at
exactly the published ASM items-2/12 $40 increment and **zero** hours above it in
any year). **Arming this flag alone cannot bring SENY inside the measured
envelope**, and PREREG §4 said so before the solve.

The remaining defect — the published curve is a **$500 base PLUS a $40
increment** while the model carries only the base as a `critical_mw = 0` ramp —
is a **SECOND mechanism** requiring its own pre-registration and its own arm
(rule 19 `[R-ONE-MECH]`). **Nothing was introduced, changed or fitted for it
here.**

## §6 — measured effect, stated precisely

* **2023 and 2024 are BIT-IDENTICAL between arms.**
* **Only 2025 moves, and it moves DOWNWARD** — SENY's max dual **125.00 →
  87.07**, the shallower ramp and the **pre-registered direction**.
* The NYC pair gains one binding hour each in 2025 **with its own curve provably
  unchanged**. That is co-optimization **general equilibrium** propagating
  through held reserve — which is precisely why the scope kill was written on
  **construction** and the duals were **reported (G2d), not gated**.

**Why the effect is small, and what it is NOT.** It is small because **SENY binds
in almost no hours** (2/0/8 in the control) — **not** because the curve barely
changed. The curve's reachable price differs in roughly **6,100 hours per year**;
a demand curve can only price where there is a shortfall.

**Direction, with its exception, as pre-registered.** The re-span prices lower
where measured > static (69 % of hours) and *higher* where measured < static:
265,399 / 264,039 / 267,874 construction probe points price lower against
2,101 / 1,889 / 1,188 higher. Predominantly but **not monotonically** downward.

## §7 — C3c: the pre-registered null held

**C3c is UNCHANGED.** The null was pre-registered (PREREG §5), not discovered
afterwards. C3c is closed as a lever lane with an exhausted queue, and its
re-open condition remains a `Capital_Hudson` → Zone-F/Zone-G **topology split**
under its own owner charter — never a mechanism-flag lever. This does **not**
reach nyiso-110's everyday-reserve-formation gap and is **not** reported as
closing it.

## §8 — TASK 2: the cross-ISO queue

NYISO's transfer queue is **empty** and its matrix column is **closed**;
re-confirmed and nothing else touched. `mechanism_matrix_gap_sweep.py --iso
NYISO`: **40 family fields, 0 absent, 0 prose-only, 0 armed-no-cell, 0
shared-gap**, the single "live-but-invisible" row being the declared
`weather_year` exclusion.

The MISO (17), PJM (18), ERCOT (14) and CAISO (5) shared-field backlogs are
**their lanes' work** (rule 25 / 28(d) — a census can mint a `U` and nothing
more) and were **not** adjudicated here.

## §9 — governance

* **Rule 15** — both arms registered on the dashboard in this session.
* **Rule 16** — 2023, 2024, 2025 in ONE bundle per arm.
* **Rule 19** — the SENY level/step-structure question was NOT folded in.
* **Rule 22** — holdout freeze **ACTIVE** and untouched; no year outside
  2023–2025 solved, scored or read. NYISO's `complete` entry re-keyed with the
  determination **re-verified from committed artifacts, no solve** (D-5(b)):
  nothing worse, so the promotion proceeded.
* **Rule 21 `[R-DOF]`** — ledger 31 → 32, n_residual unchanged at 6.
* **Rule 23** — the SENY $500 penalty, `critical_mw = 0`, `n_ramp = 8`, the NYC
  $25/MW RCPF and its scope, and the LI levels/calendar were **not** re-derived.
* **Rule 27** — every push touching a file ≥ 300 lines blob-verified.
* **Rule 28(b)** — `nyiso_ordc_measured_step_span` `U` → `K` in this session.

## §10 — what a later session should NOT redo

* **Do not re-screen SENY.** The measurement is done twice over
  (`nyiso117_seny_rcpf_curve_screen.json` for the posted prices,
  `nyiso118_span_construction_probe.json` for the construction).
* **Do not re-open the NYC curve.** Level and scope are frozen and now
  *additionally* shown invariant under this flag ($0.000 reachable price delta).
* **Do not re-test the span flag.** It is armed, solved, gated and keeper.
* **The OPEN successor is the SENY LEVEL/STEP mechanism** — the published $500
  base **plus** $40 increment against the model's base-only `critical_mw = 0`
  ramp. It needs its own pre-registration and its own arm. It is the reason this
  session's result is a **partial**, and it is the named next lever in NYISO's
  queue.
* **Do not gate a reserve scope question on a dual.** `dual`/`held_mw` are solved
  co-optimization outputs; this session's NYC result is the live demonstration —
  the NYC *curve* is provably unchanged while its *dual* moves through general
  equilibrium.
