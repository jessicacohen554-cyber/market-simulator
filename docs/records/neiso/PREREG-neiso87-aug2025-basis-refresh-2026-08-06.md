# PREREG — neiso-87: refresh the stale in-sample `NEISO,2025,8` gas-basis row

**Session:** neiso-87, 2026-08-06 · **Branch:** `claude/neiso-87-declaration-assessment-khmvod`
**Written and committed BEFORE any data byte was edited and before either arm was scored.**
**Incumbent keeper:** `2026-08-05-neiso-83-ca1-reclass` (CALIBRATED-WITH-CAVEATS, rubric v3.1
re-verified this session from committed artifacts, no solve).
**Type:** DATA CORRECTION (rule 14 `[R-ACCURATE]`). **Zero new DOF. No `ScenarioConfig` field.
No mechanism.** Rule 28(c) not engaged; rule 28(d) mints no cell verdict.

---

## 1. The object

`data/raw/gas_basis_by_iso_month.csv`, row `NEISO,2025,8`, is the **only one of NEISO's twelve
2025 rows that is not measured**. It is a committed **interpolation**:

```
NEISO,2025,8,Algonquin Citygate (interp Jul/Sep ISO-NE MA gas index),0.04,
  interpolated from Jul (+1.03) and Sep (-0.95) measured ISO-NE MA index; EIA N3050MA3
  proxy (+13.46) rejected - low-volume summer LDC citygate average overstates marginal
  AGT basis (actual Aug-2025 NEISO DA LMP $45.6 vs winter-level proxy implied $167)
```

It was written when no measured figure was available. **One now exists**, and it is already
committed in this repo, in the series every sibling row is drawn from
(`data/raw/gas-prices/isone_ma_gas_index_monthly.csv`):

```
2025,8,2.53,2.9129,-0.3829,https://isonewswire.com/2025/10/02/monthly-wholesale-electricity-prices-and-demand-in-new-england-august-2025/
```

ISO-NE's August-2025 recap (published **2025-10-02**, i.e. *after* the interpolated row was
written) states the Massachusetts natural gas index at **$2.53/MMBtu**. Against Henry Hub
$2.9129 the basis is **−0.3829 → −0.38**.

Discovered and declared, but deliberately not changed, by neiso-86
(`FINDING-neiso86-gas-basis-intake-2026-08-06.md` §5.4) because that session's own
pre-registered V2 gate froze all in-sample rows. This session carries the charter to close it.

## 2. The change — exactly one row, stated in full before it is made

| | hub label | basis | source |
|---|---|---|---|
| **before** | `Algonquin Citygate (interp Jul/Sep ISO-NE MA gas index)` | **+0.04** | interpolation note |
| **after** | `Algonquin Citygate (ISO-NE MA gas index)` | **−0.38** | the 2025-10-02 recap URL |

Δ = **−0.42 $/MMBtu** for the month of August 2025 only. After the edit all twelve NEISO 2025
rows carry the identical hub label and one cited recap URL each — the row joins its siblings'
provenance rather than introducing a new one.

**Why this is a correction and not a tuning act (rule 13/14).** The replacement value is not
chosen, fitted or compared against any residual: it is the same published series, same
boundary, same units, same monthly convention, same transformation (`MA index − Henry Hub`)
already used for the other 35 in-sample rows. The neiso-86 extractor independently reproduced
**33/36** committed in-sample rows exactly, and this row is the **one material disagreement**
it found — i.e. the pipeline that validates the other 35 rows is what flags this one.

## 3. Governance posture

- **2025 is IN-SAMPLE (training tier, 2023–2025).** No holdout year is solved, scored or
  registered. `holdout-freeze.json` is untouched and is not engaged by this work.
- **Rule 16 `[R-ALLYEARS]`:** both arms solve **2023, 2024, 2025 in ONE bundle**, one
  invocation, years sequential (rule 12).
- **Rule 22 as rewritten 2026-08-06:** an input is applied consistently across all years. This
  edit brings 2025 onto the same measured source the rest of the span already uses; it does not
  create a per-year provenance split, it **removes** the last one inside the training window.
- **Rule 23 `[R-FROZEN-DERIVE]`:** the commit cites the data change and its publication date
  only. No residual, MAE, gate score or criterion is named in the commit message or the row.
- **Rule 25 `[R-ISO-SCOPE]`:** no non-NEISO row is touched.

## 4. Arms

The keeper's own `git.sha` (`f8f803dd`) is **not resolvable in this clone** (shallow, 251
commits; the neiso-83 branch was squash-merged), so zero code drift since the keeper solved
**cannot be proven** and the committed keeper bundle is **not** admissible as the control.
Both arms are therefore solved at the same HEAD:

| arm | out-dir | data |
|---|---|---|
| **A — control** | `results/calibration/neiso87_control_A` | current committed basis (`+0.04`) |
| **B — corrected** | `results/calibration/neiso87_aug2025basis_B` | one row changed (`−0.38`) |

Both via `--replay-bundle results/calibration/neiso83_ca1reclass_B` so the recipe is the
keeper's by construction and is never re-expressed flag-by-flag.

## 5. Construction properties — all must hold or the run is INVALID, not "inert"

- **P1 — SCOPE FIDELITY (the free, decisive check).** The edited row is a **2025** row.
  Therefore **2023 and 2024 `class_hourly` and `system` must be BYTE-IDENTICAL between arms A
  and B.** Any 2023/2024 difference means something other than this row moved and the A/B is
  **INVALID** — reported as such, not interpreted.
- **P2 — FIRING AT THE ENERGY/PRICE GRAIN.** August-2025 gas marginal cost must fall (Δ basis
  is −0.42 $/MMBtu ⇒ ≈ −$3/MWh at a 7 MMBtu/MWh CC heat rate). If **2025 is byte-identical
  between the arms**, the input never reached the LP and the run is **INVALID** — a
  loader-level check does not substitute.
- **P3 — CONSERVATION.** Per-hour energy-balance identity over `class_hourly` + `storage` +
  `system` holds in both arms, relative tolerance `1e-6`.
- **P4 — SYSTEM INTEGRITY.** Total generation within ±0.05 %; `slack` and `dump` do not rise.

## 6. Stop-and-escalate triggers — fixed here, before any result is seen

- **N1 (rule 22 D-5(b)).** If arm B's re-verified determination is **worse** than the
  incumbent's `CALIBRATED-WITH-CAVEATS`, the promotion **STOPS** and escalates to the owner. It
  is never silently written.
- **N2.** If any criterion currently PASSING moves to **FAIL** in arm B — in particular C3a
  2025, which sits at `+0.2 % vs DA` today — STOP and escalate.
- **N3.** If P1 fails (2023/2024 not byte-identical), STOP: report INVALID, promote nothing.
- **N4.** If P2 fails (2025 byte-identical), report **INVALID**, promote nothing, and open the
  wiring question — do **not** report it as "the correction is inert".

## 7. Verdict ladder

- **V1 — INVALID.** P1 or P2 fails ⇒ nothing is promoted; the finding reports the construction
  failure.
- **V2 — ESCALATE.** N1 or N2 fires ⇒ arm B is registered as a **probe**, the keeper is
  unchanged, and the owner decides.
- **V3 — PROMOTE-ON-CORRECTNESS.** P1–P4 hold, no N-trigger fires, determination not worse.
  Arm B becomes the keeper **whatever the size of the residual move**, including a move that is
  numerically negligible or mildly adverse: this is a rule-14 measured-input correction with
  zero free parameters, and rule 1 `[R-STRUCT]` forbids judging it by the residual. The
  magnitude is **reported, never required** — the neiso-83 / caiso-159 precedent.

## 8. Expected direction (reported, NOT a gate)

August-2025 delivered gas falls by 0.42 $/MMBtu, so gas-marginal August hours should price
**lower**; 2025 annual mean λ should fall by a small amount (August is ~1/12 of the year and
only its gas-marginal hours move). C3c is expected to be **bit-unchanged** — the model's 2025
tail is 0 h and the change moves prices *down*, away from the $300 threshold. Recording this in
advance so that a result in the opposite direction is visible as a surprise rather than
rationalized after the fact.
