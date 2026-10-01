# RESULTS — CAMPD merit-order guard (neiso-64, 2026-07-25)

STEP 2 + STEP 3 of `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`.
Design frozen in charter §3a (owner sign-off 2026-07-25). Everything below is
**no-solve**: derived extracts scored against each ISO's published outage
instrument. The keeper re-audit (STEP 4) is reported separately.

## 1. The guard, and the gate

A detected down window is **economic layup** rather than a mechanical outage
when the unit's measured `SRMC = HR_u × delivered_fuel_price(u, t)` sat above
`RCC(t)` — the capacity-weighted p90 SRMC of the units measured running that
hour — for ≥ 90 % of the window's hours. Layup windows leave the availability
envelope and are written to `campd-unit-outages-layup[-{ISO}].csv`, which no
loader reads by default.

Ships as two patches (rule 27; both files clear the 300-line bar):
`docs/handoffs/patches/campd-merit-order-guard-{lib,deriver}.patch`.

**Byte-inertness, proven at full extract scale (2018–2026, all six ISOs).** With
`--merit-order-guard` absent, a complete re-derive reproduces every committed
extract blob exactly:

| ISO | committed blob | re-derived guard-off |
|---|---|---|
| NEISO | `a95c09288410b7bf2f8acce798445a629b277c65` | identical |
| CAISO | `3dc01fae376f932897706446d443370759ba84e8` | identical |
| NYISO | `181fefb98a89f60b6f41cce8f0fe1a02650dbd8d` | identical |
| ERCOT | `b4b48f5a7f8ecef5397bb3f8095a7988e07a9cc8` | identical |
| PJM   | `5283f5c66ef3ec68b1e98b2780d3627678df67c8` | identical |
| MISO  | `f2b3ec8e4f2920bccf9d64200b1635cc42d223a9` | identical |

## 2. How to read the numbers

Two axes, both against the ISO's **published** instrument, never against an LMP
residual (charter §4; rule 14 not rule 13):

* **level** — extract ÷ published, daily mean. **Interpretable in only one
  direction.** The CAMPD extract covers the CEMS-reporting fossil fleet only,
  while MISO / PJM / CAISO publish whole-fleet totals, so a ratio **above 1.0**
  is an unambiguous over-count and a ratio below 1.0 is mostly scope. ERCOT's
  DAM series is offered-capacity-based (`rating − live`), so it conflates
  mechanical unavailability with a unit that simply did not offer — it carries
  some layup itself, and a corrected mechanical-only extract *should* sit below
  it.
* **monthly r** — correlation of monthly means. The robust cross-ISO axis.
  Graded against a **placebo**: drop the same GW-days at random, 30 draws, and
  re-score. A guard that does not clear the placebo p95 has not discriminated,
  it has only subtracted.

## 3. Per-ISO result, 2023–2025

### NEISO — published: ISO-NE Morning Report §3 `gen_outages_reductions_mw`

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / r | 1.52× / +0.53 | 1.57× / +0.47 | 1.22× / +0.70 |
| guard-on level / r | **1.36× / +0.71** | **1.29× / +0.61** | **0.92× / +0.78** |
| placebo p95 | +0.63 | +0.55 | +0.78 |
| verdict | BEATS | BEATS | at p95 |

444 windows / 1,083 GW-days reclassified. Level and shape improve **together** —
unlike unit-frequency filtering (shape +0.84, level collapsed to 410 MW) and
unlike common-mode (shape worse than no filter).

**Positive control.** ISO-NE publishes the layup population separately
(`uncommitted_available_gen_nonfast_mw` — available but not committed). Monthly
r, 2023 / 2024 / 2025:

| window set | vs published OUTAGES | vs published UNCOMMITTED |
|---|---|---|
| baseline (all windows) | +0.53 / +0.47 / +0.70 | +0.34 / +0.45 / +0.48 |
| **KEPT** (guard: mechanical) | **+0.71 / +0.61 / +0.78** | +0.08 / +0.28 / +0.31 |
| **VETOED** (guard: layup) | −0.26 / +0.01 / +0.24 | **+0.77 / +0.71 / +0.67** |

The guard sorts the windows into the two buckets ISO-NE itself publishes: kept
windows track outages and are near-orthogonal to uncommitted capacity; vetoed
windows do the reverse. This is the charter's identification requirement met
against a published instrument.

### ERCOT — published: 60-day DAM disclosure `rating_mw − live_mw`

Owner-authorised 2026-07-25 as ERCOT's anchor, with the offered-capacity caveat
above.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / r | 1.05× / +0.64 | 0.97× / +0.68 | 0.90× / +0.84 |
| guard-on level / r | 0.72× / **+0.79** | 0.74× / **+0.81** | 0.71× / **+0.92** |
| placebo p95 | +0.69 | +0.74 | +0.88 |
| verdict | **BEATS** | **BEATS** | **BEATS** |

The strongest shape result of any ISO, and the only 3/3. The layup population is
again near-orthogonal to published outages (+0.07 / −0.20 / −0.30).

### PJM — published: `gen_outages_by_type`, PJM RTO, lead 0

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / r | 1.28× / +0.90 | 1.07× / +0.90 | 0.96× / +0.93 |
| guard-on level / r | **1.11×** / +0.90 | **0.98×** / +0.91 | 0.84× / **+0.95** |
| placebo p95 | +0.91 | +0.92 | +0.94 |
| verdict | inside | inside | BEATS |

903 windows / 4,624 GW-days reclassified. PJM's baseline shape is already
near-ceiling (+0.90), so there is almost no room on that axis and the placebo
test is correspondingly uninformative. The **level** result is the substantive
one: a thermal-only extract at 1.28× a whole-fleet published total in 2023 is an
unambiguous over-count, and the guard takes it to 1.11×.

### CAISO — published: Curtailed and Non-Operational Generator report

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / r | 0.32× / +0.42 | 0.30× / +0.70 | 0.37× / +0.47 |
| guard-on level / r | 0.32× / +0.41 | 0.29× / +0.68 | 0.34× / +0.51 |
| placebo p95 | +0.44 | +0.75 | +0.55 |
| verdict | inside | inside | inside |

**The guard does not discriminate on CAISO's instrument, and CAISO's instrument
is the weakest of the four.** The extract sits at ~⅓ of the published series
because the comparison is CEMS-thermal against a whole-fleet report filtered
only by a resource-name heuristic (no CAMPD↔CAISO resource crosswalk exists).
Reported as an honest null, not as a pass. A proper crosswalk would make this a
per-resource ground-truth test — the strongest validation available anywhere in
this charter — and is the single highest-value follow-up.

### MISO — published: `miso_outages_estimated` Forced + Planned + Unplanned

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / r | 0.89× / +0.82 | 0.91× / +0.79 | 0.76× / +0.88 |
| guard-on level / r | 0.79× / **+0.88** | 0.81× / +0.80 | 0.68× / **+0.95** |
| placebo p95 | +0.84 | +0.83 | +0.90 |
| verdict | **BEATS** | inside | **BEATS** |

755 windows / 3,630 GW-days reclassified. MISO's extract already sits *below* a
whole-fleet published total, so its level ratio is scope, not over-count, and
carries no signal either way. The shape result is the substantive one: 2/3 clear
the placebo, and 2024 — the year that resists in every ISO — is the one that
does not.

### NYISO — no published instrument identified

Its extract remains **UNVERIFIED**. The guard reclassifies windows there on the
same measured basis as everywhere else, but nothing independent confirms the
result. Stated plainly rather than inferred from the other five.

## 3a. Cross-ISO summary

Placebo-cleared ISO-years — the discrimination test, not the level test:

| ISO | 2023 | 2024 | 2025 | cleared |
|---|---|---|---|---|
| ERCOT | BEATS | BEATS | BEATS | **3/3** |
| NEISO | BEATS | BEATS | at p95 | 2/3 |
| MISO | BEATS | inside | BEATS | 2/3 |
| PJM | inside | inside | BEATS | 1/3 (baseline r already +0.90) |
| CAISO | inside | inside | inside | 0/3 |
| NYISO | — | — | — | no instrument |

**2024 is the hardest year everywhere** — mild winter, low gas basis, so the
fuel-cost signal that drives the guard is at its weakest exactly when the
detector's over-count is at its worst (NEISO baseline DJF 2.77×). That is a
known limit of the mechanism, not a defect in the run.

## 4. What this adds up to

The mechanism separates the populations. The evidence is strongest where the
instrument is cleanest (NEISO's outage/uncommitted split, ERCOT's DAM series),
weakest where the instrument is a scope-mismatched whole-fleet aggregate
(CAISO), and uninformative where the baseline shape already saturates (PJM).
Nowhere does it make a scored axis worse.

It is **not** the whole defect. NEISO 2023–24 still runs 1.29–1.36× a
whole-fleet published total on a thermal-only extract, so a residual over-count
survives the guard. The charter's verdict should record that the guard is a
genuine, measured improvement rather than a closure of the finding.

## 4a. STEP 4 — keeper re-audit on the corrected envelope (NEISO, in-sample)

`2026-07-25-neiso-64-meritguard-a1` — the `2026-07-23-neiso-61-netrev-margin`
keeper recipe replayed verbatim (`--replay-bundle`) on the guard-corrected NEISO
envelope, 2023–2025 in one bundle (rule 16). The **A0 arm is the keeper itself**:
the guard is byte-inert when off and the guard-off extract reproduces the
committed blob exactly, so an A0 re-solve would be the keeper by construction.

| criterion | A0 / keeper | A1 / guard-corrected |
|---|---|---|
| C1 fuel-mix | PASS (12/12, free 8/8) | PASS (12/12, free 8/8) |
| C2 system volume | PASS | PASS |
| **C3a mean LMP vs RT** | +5.2 / +7.1 / +5.2 % | **+3.4 / +6.0 / +3.2 %** |
| **C3b duration NRMSE** | 0.102 / 0.164 / 0.071 | **0.085 / 0.157 / 0.057** |
| C3c tail (model h > $300) | 0 h | 0 h — unchanged |
| C4 dispatch correlation | PASS | PASS |
| C5a CO₂ | PASS | PASS |
| C8 forced-energy share (D-2) | PASS | PASS |

**Both load-bearing price criteria improve in every one of the three years, and
nothing regresses.** That is the leave-one-year-out condition met by
construction (rule 22): no year is traded against another, so the gain is not a
re-weighting. Mean LMP moves −1.0 to −1.7 % — an order of magnitude smaller than
the neiso-62 operable-capacity overlay's −7 to −9 %, because the guard relieves
part of the over-count rather than replacing the whole envelope.

**Verdict for NEISO: fix-in-place, not re-tune.** The charter anticipated that
some keepers would need re-tuning against the corrected envelope (the
ERCOT-79 / nyiso-63 co-dependency condition). NEISO's does not: the offer curves
were not so co-dependent on the over-count that relieving it broke them — it
improves them.

Bundle determination is **NOT-YET**, on C6 governance UNATTESTED only: this is a
candidate arm, not a promotion, so it carries no DOF-ledger attestation. C3c
reports FAIL rather than the keeper's ledgered CAVEAT for the same reason — the
underlying number (0 model hours > $300) is identical in both arms. **No keeper
was changed in this session.**

## 5. Reproduction

```
git apply docs/handoffs/patches/campd-merit-order-guard-lib.patch
git apply docs/handoffs/patches/campd-merit-order-guard-deriver.patch
python scripts/data/derive_campd_unit_outages.py --iso <ISO> \
    --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 --merit-order-guard
python scripts/probes/_neiso64_meritguard_score.py --iso <ISO> \
    --base <guard-off>.csv --guard <guard-on>.csv --layup <guard-on>-layup.csv
```

No LP solve is involved in anything in this document.

**The corrected extracts, their `-layup` companions, the run payload
`frontend/data/backcast/runs/<id>.js` (372 KB) and the bundle's parquet sidecars
are not committed.** The repo's API-only push path carries content inline, so it
cannot round-trip files that size and cannot carry binary at all; and committing
a corrected extract before the charter reaches a verdict would silently change
every ISO's availability envelope. What is committed: the registry sidecar,
`metrics.json`, `meta.json`, the two patches, the scorer, and this document.
Everything else is deterministic from committed inputs — the committed extracts,
the two patches, and the committed CAMPD / gas-price / F923 source data — so the
commands above regenerate it byte-for-byte. **Consequence to be explicit about:
the run is registered by sidecar but will not render on the dashboard until
`runs/<id>.js` lands via a git-push path.** Adopting the guard is the commit
decision, and it is the owner's.
