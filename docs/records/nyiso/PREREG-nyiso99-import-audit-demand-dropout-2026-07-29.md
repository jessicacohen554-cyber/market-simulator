# PRE-REGISTRATION — nyiso-99: import-shape benchmark audit + the EIA-930 demand-dropout repair

**Written and pushed BEFORE any solve** (NYISO lane protocol, nyiso-89 §4a /
nyiso-98). Session scope: mechanism-matrix §5.5 **item 9, import hourly shape**.
Keeper at entry: `2026-07-29-nyiso-98-nucavail`
(`results/calibration/nyiso98_nucavail`), DETERMINATION NOT-YET, C3c sole
blocker.

This document fixes, in advance: (§1) what the mandated benchmark audit found,
(§2) the adjudication it forces on item 9, (§3) the one code change this session
arms, (§4) its gates, (§5) what is explicitly NOT claimed.

---

## 1. The audit came first, and it cleared the target

nyiso-98 established that the EIA-930 `NYIS` feed posts reporting gaps as
**exactly 0.0 MW in the source parquet** — values, not NaN, and not produced by
`_eia_hourly_frame_filled`'s gap-bridging (which emits NaN). In `NG: NUC` that
was 1,179 h (2023) / 380 h (2024) / 117 h (2025), and gap-masking **inverted**
the published r_day ordering, so item 7's stated defect did not exist as
described. The standing instruction is that the audit is open for every other
series. Item 9's target is one of them.

Instrument: `scripts/probes/nyiso99_import_benchmark_provenance.py`
(sections `census` / `falsify` / `baseline`), built on the nyiso-98 pattern.
Independent falsification instruments, both measured, both already intaken
under the 2026-07-10 owner authorization, neither the EIA-930 feed:

* **imports** — NYISO MIS **P-32** External Limits & Flows
  (`data/raw/NYISO/interface-flows`): the eleven `SCH -` external schedules,
  summed hourly, aligned on **UTC** (local-time alignment collapses the DST
  fall-back hour and yields an 8,759-row year).
* **hydro / oil** — NYISO MIS **P-63** Real-Time Fuel Mix
  (`data/raw/NYISO/fuel-mix`), NYCA-total by NYISO's own taxonomy.

### 1.1 Census — the artifact does NOT repeat on the import target

Suspect hours = exactly-0.0 values, plus bit-identical non-zero runs ≥ 4 h,
on the 8,760-h model clock:

| series | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`Total interchange`** (item 9's target) | **0** | **6** | **14** |
| `NG: WAT` | 0 | 1 | 1 |
| `NG: OIL` | 3,160 | 6,371 | 7,935 |
| `NG: NUC` (nyiso-98 reference) | 1,275 | 390 | 118 |

### 1.2 Falsification — every suspect import hour is an artifact, and there are almost none

P-32 validates itself on the clean hours first: hourly r **0.910 / 0.908 /
0.882** against EIA-930, mean bias −16 / +182 / +508 MW (scheduled-vs-actual
interchange drift, growing; it does not affect a zero test). On that footing
**6 of 6 (2024) and 14 of 14 (2025)** suspect hours are falsified — P-32 median
|flow| 1,247 / 4,138 MW where EIA-930 posts 0.0. 2023 has **no** suspect hour.
`NG: WAT`: 1 of 1 falsified in each of 2024/2025, none in 2023.

`NG: OIL` is a different animal and is **out of scope here**: its suspect hours
are overwhelmingly *genuine* zeros (P-63 confirms 3,074 / 6,285 / 7,343 of
them), and its instrument agreement is weak in 2023–24 (r 0.068 / 0.330 /
0.867) because NYISO books dual-fuel units under `Dual Fuel` regardless of
which fuel is burning. That is a basis mismatch, and it is item 10's territory
(`dual_fuel_oil_reattribution`), not item 9's.

### 1.3 Re-based baseline — the item-9 statistic is unmoved by gap-masking

On the keeper, `import` model-vs-target:

| year | r_hr raw | r_hr gap-masked | r_day raw | r_day masked | r_hr vs **P-32** |
|---|---|---|---|---|---|
| 2023 | 0.598 | 0.598 | 0.735 | 0.735 | 0.612 |
| 2024 | 0.624 | 0.624 | 0.786 | 0.787 | 0.611 |
| 2025 | 0.454 | 0.458 | 0.636 | 0.635 | 0.495 |

**Item 9's stated defect is REAL.** 20 artifact hours in 26,280 cannot move it,
and an entirely independent instrument reproduces it. The nyiso-98 failure mode
does not repeat. The audit clears the target rather than dissolving the item.

---

## 2. Item 9 is a downstream symptom of C3c — adjudication, no solve

With the benchmark cleared, the defect is attributed on the keeper's own
sidecars. Three measurements, all three years:

1. **The import node is not broken.** Its shape tracks the spread *it is
   shown* — `r(profile: model import, model seam spread)` = **+0.673 / +0.686 /
   +0.772**, where the spread is the model's own load-weighted internal price
   minus the seam price it is offered.
2. **The spread it is shown is phase-inverted.** `r(model spread profile, real
   spread profile)` = **−0.401 / −0.236 / −0.600**. Model spread peaks at
   h21 / h02 / h22; the measured NYISO-DA-minus-neighbor spread peaks at
   h17 / h16 / h17.
3. **The inversion is arithmetic, and its single term is the C3c deficit.** The
   seam side is measured and correct (neighbor DA LMP, hod swing 19.8 / 24.1 /
   32.1 $/MWh). NYISO's *internal* price swing is **12.95 / 13.17 / 19.75**
   against a real **22.45 / 25.13 / 43.27** — a ratio of **0.58 / 0.52 / 0.46**.
   Subtracting a correctly-peaked seam price from a too-flat internal price
   drives the spread to its minimum exactly at the peak: model spread at h17 is
   **−0.1 / −1.1 / +5.3** $/MWh, so the LP stops importing in the hour NY
   imports most, and buys its reconciled monthly quota overnight instead.

This confirms nyiso-86 §3's qualitative claim ("the interchange shape shares
C3c's root cause") quantitatively, on the current keeper, and adds the part
nyiso-86 could not: the seam mechanism itself is faithful.

**Consequence — item 9 has no admissible independent lever.** Any mechanism
that re-times imports toward the afternoon peak would have to be identified
from the measured net-interchange series, which is the scored outcome and is
forbidden as an input (rule 13 `[R-MEASURED]`, rule 21 `[R-FROZEN-DERIVE]`).
And nyiso-86 already recorded the sign: forcing peak imports **depresses peak
duals**, so it moves C3c the wrong way while flattering the import metric —
rule-14-backwards. Item 9 is therefore recorded **CLOSED, attributed to C3c**,
the same diagnosed-unclosed structural limitation of the five-zone
representation that nyiso-94/95/96/97 closed every other candidate against.
**No import-side mechanism is armed this session.**

### 2.1 Two by-products, reported not armed

* **The 4,350 MW `NYISO_simultaneous_import` cap is a hand-set estimate that
  measurement contradicts.** It hard-pins model import at exactly 4,350 MW in
  548 / 689 / 177 h/yr and the `import_scarcity` rung is never reached in any
  hour of any year, while measured net import exceeds it in 287 / 314 / 145 h
  (max 5,929 MW, nyiso-86) and the published P-32 external limits sum to a
  minimum of 5,805 / 6,090 / 6,680 MW. This is a live rule-14 `[R-ACCURATE]`
  reconcile item. It is **not** armed here: the P-32 sum (~10 GW mean) is not
  a simultaneous limit — it is the sum of parallel paths our five-zone network
  collapses, exactly rule 14's named misalignment case — so a *reconciled*
  identification is needed, and relaxing the cap alone would only let the model
  import more in its wrong-phase overnight hours. Separate charter.
* **The dropout artifact reaches the demand INPUT, not only the benchmark** —
  §3, which is what this session arms.

---

## 3. The single armed delta — `_screen_demand_dropouts`

Extending the audit to the `Demand` column of every modeled BA found that
EIA-930's exactly-0.0 dropout is **consumed by the LP as real load**. Across
all six BAs × 2023–2025 the only affected series is `NYIS` `Demand`:
**2024 h403, h6760, h6761 and 2025 h354, h355**, each bracketed by ~17–22 GW
readings — and each reproduced **1:1** in the keeper's solved
`system_<year>.parquet` (total served demand exactly 0.0 MW in those five
hours). The model serves no load at all in an hour New York drew 22 GW.

**Change** (`src/market_sim/data/eia930/demand.py`): `_screen_demand_dropouts`,
the low-side twin of the existing `_screen_demand_spikes`, wired into all six
per-BA demand loaders. An exactly-zero BA demand reading is an artifact by
construction — no threshold, no fitted parameter, **zero DOF**. Flagged hours
are dropped and linearly interpolated from their neighbours, the same repair
the spike screen and the missing-meter path already use.

Deliberately **scoped to demand only, never interchange**: a BA's net
interchange legitimately reads 0.0 MW on idle ties (ERCO posts 187 / 140 / 113
such hours on its ~1.2 GW DC ties), so the same screen on an interchange series
would delete real measurements — the rule-14 failure mode the repair exists to
avoid.

**Admissibility.** This is a data-quality repair of a known reporting artifact,
identified against the source's own physics, not against any residual — rule 21
`[R-FROZEN-DERIVE]` is satisfied because nothing here is a measured-behaviour
parameter, and rule 13 is satisfied because the repair regenerates identically
for a forward year. Rule 14 `[R-ACCURATE]` is the governing rule and points one
way: an EIA-930 zero-dropout is not accurate data.

**Blast radius, measured before solving:** byte-identical (Δ = 0.00000 TWh,
max |Δ| = 0.0 MW) on **16 of 18** ISO-years; NYISO 2024 **+0.0562 TWh**
(+0.037 %) and NYISO 2025 **+0.0435 TWh**. **2023 is untouched in every ISO.**

### 3.1 Run design — 2023 IS the zero-delta control

One invocation, `scripts/replay_keeper.py results/calibration/nyiso98_nucavail
--out-dir results/calibration/nyiso99_demandfix`, years 2023 2024 2025
sequentially in that one invocation (rules 15/16). The keeper's own `meta.json`
supplies the recipe, so the **only** delta against the keeper is the code fix.

The screen is a **proven no-op on 2023**, so the arm's 2023 year is a genuine
same-recipe zero-delta control carried inside the arm itself — a stronger
control than a separate run, and it also establishes that this fresh container
reproduces the keeper at all. No second invocation is needed.

---

## 4. Gates — declared before the solve

| id | gate | pass condition |
|---|---|---|
| **G1** | **Control identity.** Arm 2023 vs keeper 2023. | Per-class hourly MW and per-zone hourly prices agree to < 1e-6. **A miss voids everything below** — the container does not reproduce the keeper. |
| **G2** | **Repair landed.** | Zero hours with total served demand == 0.0 in all three years (keeper has 3 in 2024, 2 in 2025). |
| **G3** | **Level neutrality.** | Annual served energy rises by the repaired wedge only: +0.0562 TWh (2024), +0.0435 TWh (2025), each within ±1 %. 2023 unchanged. |
| **G4** | **C1 protection.** | 2023 CC_REGULAR is bit-unchanged by G1 (it is the ISO's tightest cell at −2.79 of ±2.94). 2024/2025 C1 cells stay in band; any walk is REPORTED, not patched (rule 14). |
| **G5** | **Protective gates hold.** | C7 and C8 verdicts unchanged. C8 2024 `ST_GAS` is grounded-above-budget at 30.5 % and fragile — a flip is reported as a regression. |
| **G6** | **C3c honesty.** | C3c reported whatever it does. It is *not* expected to move (5 hours), and no result on it is claimed as skill either way. |

**Promotion rule, fixed now:** the arm is proposed as keeper **only if G1–G3
pass and G4–G5 hold**. If G4 or G5 breaks, the finding is reported and the
keeper stays — a five-hour data repair does not justify walking a protective
gate, and the fix would then need its own root-cause session.

Because this is a correctness repair rather than a mechanism, rule 20's
leave-one-year-out requirement does not bite (there is no fitted value to
overfit); the 2023 no-op *is* the held-out year.

---

## 5. What this session does NOT claim

* **No import mechanism is tested, so no import cell earns a verdict from an
  arm.** Item 9 is closed on adjudication and attribution, in the
  nyiso-93/94/95/97 ex-ante shape — not on a solve.
* **The demand repair is not an item-9 fix.** It changes five hours; it will
  not move r_hr and is not offered as though it might.
* **C3c stays a diagnosed, unclosed structural limitation** with an empty lever
  queue. Nothing here re-opens it; this session adds one more attributed
  symptom to it.
* **P-32 flows are diagnosis only.** Per-interface measured flows sum to the
  scored outcome and are never an input. Only the *published limits* in that
  file would be admissible, and none is armed here.
* **CT_PEAKER is untouched** (owner-accepted misrepresentation), the h14-21
  windowed floors stay off, and item 8 stays blocked on its classifier review.
