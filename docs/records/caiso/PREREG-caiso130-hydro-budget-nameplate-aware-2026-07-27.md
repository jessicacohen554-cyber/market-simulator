# PRE-REGISTRATION — caiso-130 `hydro_budget_nameplate_aware` (single delta)

**Written and committed BEFORE arm B was solved.** No B-arm result existed when
this document was frozen. Gates below are final — a gate this document does not
contain cannot be quoted as a pass. Format follows
`PREREG-caiso126-ror-split-2026-07-27.md`.

Owner grant: caiso-127 ask §Status item 3 —
*"`hydro_budget_nameplate_aware` is to be armed in its OWN single-delta A/B —
never bundled with S1, which would confound both. Its cross-ISO blast radius is
checked before it enters any keeper."* S1 was executed and killed at the derive
gates (caiso-129), so this is the last unspent grant item. **Promotion is NOT
pre-granted** and remains a separate owner act after rule-22 LOYO.

---

## §0 — cross-ISO blast radius (the grant's own precondition), ANSWERED FIRST

Instrument: `scripts/probes/_caiso130_nameplate_blast_radius.py` (committed, no
LP anywhere in it). Each ISO probed under **its own keeper's** hydro settings,
read from the committed keeper bundles.

**The flag is NOT CAISO-scoped by construction — and that had to be measured,
not assumed.** It lives in the shared `data.hydro.load_hydro_budget` level-pinning
path, inside the `if monthly_target_mwh is not None` branch, so its reach is
exactly "the ISOs whose run pins a monthly hydro level".

| ISO (keeper) | pins a monthly level? | 2023 | 2024 | 2025 | forecast 2026 |
|---|---|---|---|---|---|
| **CAISO** `caiso126_rorsplit_B` | yes (`hydro_eia930_monthly`) | 130.2 GWh (0.53 %) | 340.6 GWh (1.50 %) | 26.3 GWh (0.12 %) | 158.4 GWh (0.79 %) |
| **PJM** `pjm121_ccbelt` | yes | **851.5 GWh (5.51 %)** | **573.4 GWh (3.62 %)** | **1 042.3 GWh (6.72 %)** | 656.2 GWh (4.13 %) |
| **MISO** `miso88_egrid_hr` | yes | 129.7 GWh (1.30 %) | 227.1 GWh (2.12 %) | 85.7 GWh (0.87 %) | 112.5 GWh (1.10 %) |
| **NEISO** `neiso61_netrev_margin` | yes | 71.2 GWh (0.81 %) | 66.9 GWh (0.91 %) | 14.4 GWh (0.28 %) | 19.3 GWh (0.28 %) |
| **ERCOT** `ercot115_coal_floor_only` | **no** | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL (no overflow) |
| **NYISO** `nyiso87_cmeas_minrun` | **no** | IDENTICAL | IDENTICAL | IDENTICAL | 3.2 GWh (0.01 %) |

(% is of that ISO-year's own in-LP conventional-hydro budget. "IDENTICAL" =
the `(n_hydro, 12)` budget array is bit-equal with the flag off and on, i.e.
`max |Δ| < 1e-6` MWh — the strict-no-op claim VERIFIED, not asserted.)

Three findings, all of which the disposition below respects:

1. **No non-CAISO keeper changes by arming this in the CAISO A/B.** The flag is
   a per-run `ScenarioConfig` field defaulting `False`, read via `getattr` in
   `data/fleet/assembly.py:1489`; every other ISO's keeper `run_config.json`
   records it `false`/absent. Arming it here is scoped to this run by
   construction — there is no shared derived artifact, no on-disk regeneration,
   no cross-ISO cache key involved (the flag changes only the in-memory budget
   array). **Rule 25 `[R-ISO-SCOPE]` is satisfied without scoping work**: the
   mechanism carries no ISO-fitted constant at all (the bound is the plant's own
   EIA-860 nameplate × the calendar).
2. **The defect it fixes is materially LARGER on PJM than on CAISO** — 3.6–6.7 %
   of PJM's in-LP hydro budget is undeliverable under the uniform scale, an
   order of magnitude above CAISO's 0.12–1.50 %. **Reported, not acted on**
   (the DO-NOT-REDO forbids bundling anything with this delta): PJM/MISO/NEISO
   arming is a separate per-ISO A/B and a separate owner act.
3. **The forward path is exposed on every hydro ISO**, including the two whose
   backcast is a strict no-op: `forecast_budget=True` pins the
   normal-water-year climatology through the same branch, so NYISO changes by
   0.01 % on a 2026 forecast where its backcast does not change at all. (ERCOT
   is 0 on both paths — its 12-plant hydro fleet never exceeds nameplate-hours.)
   Recorded so a later forecast-lane session does not rediscover it.

**Disclosed, NOT claimed as fixed:** NYISO's 2023/24 backcast carries
20.0/25.1 GWh of budget above nameplate-hours over 34 plant-months *in the raw
EIA-923 rows themselves*. With no level pin there is no target to re-allocate
against, so this flag cannot touch it (verified: `moved_mwh = 0`, undeliverable
unchanged). That is a separate defect in a separate lane.

## §1 — the delta (ONE switch, one mechanism, zero new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
scripts/replay_keeper.py results/calibration/caiso126_rorsplit_B \
    --out-dir results/calibration/caiso130_nameplate_B \
    --set hydro_budget_nameplate_aware=true \
    --note "caiso-130 nameplate-aware hydro budget target (single delta)"
```

- **Arm A** `results/calibration/caiso130_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `capacity-deliverability` and
  `hydro-plant-modes` partitions (both curated before either solve). NOT
  registered as a keeper candidate; registered as the run explorer's control
  arm per rule 15.
- Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  sequential within each run, arms sequential to each other (rule 12 — CAISO is
  single-solve-only on this 15 GB box).

**What the flag does** (`data/hydro.py::_nameplate_aware_scale`): the monthly
hydro LEVEL target (measured EIA-930 `NG: WAT` on this backcast) is applied by
water-filling under each plant-month's own `nameplate × hours-in-month` ceiling
and re-allocating the overflow pro-rata to the plant-months that still have
headroom, instead of a UNIFORM fleet-wide monthly scale factor. The month total
is met exactly wherever it is physically attainable; where it is not, every
plant sits at its bound and the shortfall is LOGGED.

- **DRIVER (rule 14 `[R-ACCURATE]`)**: the nameplate is the accurate datum.
  The uniform scale silently pushed small plant-months above a physical
  ceiling the LP then clipped (`P[g,t] <= pmax × availability`), so the fleet
  under-delivered its own measured level target. This is the
  FINDING-caiso126 K4 root cause, filed there as needing its own lane.
- **DOF added: zero** (rule 24). No threshold, no percentile, no tuned
  constant: the bound is EIA-860 nameplate × the calendar.
- **Rule 13 `[R-MEASURED]`**: no outcome is pinned. The construction
  regenerates identically for a forward year (the forecast path pins the same
  way — §0 row "forecast 2026") and responds to changed conditions through the
  level and the fleet.
- **Rule 19 `[R-ONE-MECH]`**: it is not a new mechanism on the residual — it is
  the *correct application* of the level target the keeper already pins. It
  adds no floor and no bound; it moves budget between plant-months inside a
  preserved monthly total.
- **Byte-identical below the bound** (unit-tested, `tests/unit/data/test_hydro.py`):
  when no plant-month overflows, the water-fill's first pass IS the uniform
  expression.

## §2 — measured baseline, frozen BEFORE arm B (arm A expectation)

Instrument: `scripts/probes/_caiso130_nameplate_precheck.py` (committed, no LP).
Read from the **keeper's own committed `hourly/` sidecars**, never a replay.

Keeper hydro window gap (model − measured EIA-930 `NG: WAT`), MW:

| window | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight (hod 0-6) | +159.7 | +91.7 | +211.1 |
| belly (hod 9-15) | −91.8 | −57.8 | −83.3 |
| **evening (hod 17-21)** | **−250.7** | **−375.5** | **−263.9** |
| annual mean (model / measured) | 2 763 / 2 794 | 2 506 / 2 596 | 2 413 / 2 436 |

(Reproduces the −251/−376/−264 that FINDING-caiso126 §2 and the caiso-127 ask
quote, from the keeper's own hourlies.)

Delta energy budget, split by DESTINATION class (the flag's re-allocated MWh):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| re-allocated | 130.2 GWh | 340.6 GWh | 26.3 GWh |
| … to reservoir (shapeable) | 115.1 | 308.1 | 23.4 |
| … to RoR (flat, month-constant) | 15.1 | 32.6 | 2.9 |
| undeliverable under the uniform scale | 130.2 GWh / 67 plant-months | 340.6 / 42 | 26.3 / 26 |
| undeliverable with the flag ON | **0.0 / 0** | **0.0 / 0** | **0.0 / 0** |
| month-total drift | < 1e-9 MWh | < 1e-9 | < 1e-9 |

## §3 — the NO-FEEDBACK CEILING, and the charter expectation it REFUTES ex ante

Every re-allocated MWh that lands on a **reservoir** plant is shapeable and can
in principle be placed in the evening; every MWh that lands on a **RoR** plant
raises a MONTH-CONSTANT flat level, so only 5/24 of it reaches the evening
window. That gives a hard fixed-λ ceiling on the evening movement:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **evening ceiling (no feedback)** | **+64.8 MW** | **+172.5 MW** | **+13.2 MW** |
| keeper evening gap | −250.7 | −375.5 | −263.9 |

**Stated before the solve, so it cannot be spun afterwards: this delta CANNOT
deliver the caiso-127 charter's "evening heals to within ±150 MW".** The
arithmetic ceiling is 64.8 / 172.5 / 13.2 MW against gaps of 251 / 376 / 264 MW
— unreachable in 2023 and 2025 by a factor of ~4 and ~20. The charter framed
that heal as the test of a mechanism that would *re-time* the whole evening;
this flag *adds deliverable water*, which is a different and much smaller
quantity. The PRIMARY below is therefore registered as a **direction + size**
test against this ceiling, and the charter's ±150 target is recorded here as
**not applicable to this delta**, not as a gate this run failed.

The ceiling is a *no-feedback* prediction, not a cap: caiso-126 measured the
water-value feedback channel to be real and 1.2–3× the fixed-λ proxy. A B−A
movement **above** the ceiling is therefore reported as a feedback ratio, not
scored as a failure — but it must be attributed (§5 A3).

## §4 — PRIMARY and SECONDARY gates (pass/fail, pre-registered)

**P1 — PRIMARY. The evening hydro gap moves toward zero in ALL THREE years.**
Owner mandate for this session. Two limbs, both required:
- **direction**: `evening_gap(B) > evening_gap(A)` (less negative) in 2023,
  2024 AND 2025. A single year moving the wrong way FAILS P1.
- **size**: the movement is at least **25 % of that year's no-feedback ceiling**
  — ≥ +16.2 / +43.1 / +3.3 MW. Below that the delta is not reaching the window
  its energy argument says it should, i.e. the re-allocated water is going
  somewhere else and the mechanism story is unsupported.

**P2 — the annual hydro energy deficit narrows in all three years.** The flag's
whole claim is that the fleet can now DELIVER its own level target. Delivering
the full re-allocation raises the annual mean by +14.8 / +38.9 / +3.0 MW.
Gate: annual-mean hydro (model) rises by **≥ 60 %** of that in every year
(≥ +8.9 / +23.3 / +1.8 MW). This is the mechanism's own identity check and is
close to deterministic — the keeper already uses 98–100 % of its deliverable
budget, so freed water is taken.

**P3 — mechanism accounting stays clean.** In arm B: D-4 off-window share is
`0.0000` for BOTH `hydro_ror_flat` and `hydro_min_flow` in all three years
(unchanged from arm A), and the D-2 forced share of the hydro class moves by
**≤ 2 pp** per mechanism per year. The delta must not re-arm or re-window an
existing floor.

**P4 — the undeliverable-energy defect is closed.** Arm B's solve log reports
the nameplate-aware rescale, and the pre-solve check (§2) shows 0 MWh / 0
plant-months above the bound in all three years. Verified pre-solve; recorded
here so the claim is auditable.

## §5 — KILLS (pre-registered; any one fires ⇒ the delta is rejected as armed)

**K1 — the C3a guard (owner-mandated).** The CA demand-weighted mean λ must not
move AWAY from actual in any year: the absolute % error `|model/actual − 1|`
may not increase by more than **0.25 pp** in any of 2023/24/25. C3a-2025
already reads **+10.9 %** and is the caiso-123 attributed extract basis — under
the neiso-66 freeze it is **never a tuning target**, only a guard.

**K2 — overnight.** The overnight gap (+159.7 / +91.7 / +211.1 MW, the
known-worst window) may not worsen by more than **+50 MW** in any year. Freed
water landing overnight instead of in the evening is the failure mode this
catches.

**K3 — belly.** `|belly gap|` may not exceed **150 MW** in any year (the
caiso-126 P2 bound, carried forward unchanged).

**K4 — rubric non-regression.** No rubric criterion that is PASS in arm A may
read FAIL in arm B (arm A expectation: C1/C2/C3b/C4/C7/C8 PASS; C3a/C3c/C5a
FAIL; C6 UNATTESTED).

**K5 — no silent structural change.** Arm B's in-LP hydro plant COUNT and
annual budget TOTAL must equal arm A's (the flag moves budget between
plant-months inside a preserved month total; it must not add, drop or re-zone a
plant). Pre-verified in §2 (`month-total drift < 1e-9 MWh`, identical plant
sets); re-checked from the solved bundles.

## §6 — rule-22 LOYO

**Zero fitted parameters** (the bound is EIA-860 nameplate × the calendar; no
threshold, no percentile, nothing derived from a residual), so LOYO reduces to
per-year gate consistency, exactly as in FINDING-caiso126 §5: each of P1/P2 and
each kill is evaluated **independently in each of 2023, 2024, 2025**, and the
verdict must be same-signed across all three. A gate that passes only in the
aggregate, or a movement confined to one year, is scored as a single-year
artifact and blocks promotion talk. There is nothing to re-tune and no
re-tuning occurred.

## §7 — scoring instrument and reporting

Scorer: `scripts/probes/_caiso130_nameplate_ab.py` (committed with this
prereg; reuses the caiso-125/126 loaders so the windows and the measured series
are identical across sessions). It reads only the two solved bundles plus raw
EIA-930 — no solve, and no gate that is not in this document.

Both arms are registered on the backcast dashboard in-session (rule 15),
whatever the verdict. Promotion is not granted here and is not requested by
this document.
