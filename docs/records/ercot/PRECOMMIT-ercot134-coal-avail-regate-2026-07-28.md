# PRE-COMMIT ADJUDICATION — ERCOT-134 Phase 2: the ERCOT-116 re-solve A/B on the CURRENT keeper

**Written 2026-07-28, BEFORE any year of either bundle was solved.** Rule 1:
criteria fixed here so no verdict can be reverse-engineered from a residual.
Companion synthesis (Phase 1, no-LP, pushed with this document):
`docs/DIAGNOSIS-ercot134-coal-availability-pin-2026-07-28.md` + the
reproduction probe `scripts/probes/ercot134_coal_availability_pin.py`.

## What this A/B is FOR — and what it is not

**The point of the run is to size the un-pinning and expose the coal-vs-gas
merit bias on the current keeper — NOT to produce a keeper.** ERCOT-116
already measured both effects, but its numbers are stale twice over: it ran
against the ercot115 keeper (two promotions ago — ercot128/129 added the coal
min-config floor), and the merged Sandy Creek availability repair (ERCOT-132
D2/D3) has since changed 2025 coal availability, so the committed
`ercot129_conditional` bundle is no longer byte-reproducible from the tree.
A fresh BASE is therefore mandatory; the ARM is **never** diffed against the
committed ercot129 bundle.

**The ARM is EXPECTED to fail on level (C1/C3a). That is the measurement,
not the verdict.** ERCOT-116 adoption remains an owner ruling this lane does
not make; there is no promotion path from this lane.

## The two bundles (recipe fixed now; current HEAD, `d38e28f` or later)

```
python scripts/replay_keeper.py results/calibration/ercot129_conditional \
  --out-dir results/calibration/ercot116_regate_base \
  --years 2023 2024 2025 \
  --note "ERCOT-116 re-gate BASE — ercot129 recipe on current HEAD"

python scripts/replay_keeper.py results/calibration/ercot129_conditional \
  --set ercot_thermal_dam_availability_coal=true \
  --out-dir results/calibration/ercot116_regate_arm \
  --years 2023 2024 2025 \
  --note "ERCOT-116 re-gate ARM — measured coal DAM availability, single delta"
```

Run sequentially (one per-plant ERCOT LP at a time on this box), years
sequential within each (rules 12/16). Full span in one bundle each; no
holdout year touched (rule 22).

## Scorers (named now, all committed before the solve)

* **Pin / declaration-ratio / impossible-hours** —
  `scripts/probes/ercot134_coal_availability_pin.py --bundle <dir>` (reads the
  bundle's own `hourly/unit_hourly_<year>.parquet`; `cap_mw` IS the LP's
  availability bound, so the ARM's redistribution is scored exactly as
  solved; pin tolerance 0.5 MW on exact LP dispatch).
* **G1 fleet-aggregate loading-vs-price** —
  `scripts/probes/ercot128_coal_unit_grain.py --arm-bundle <X>
  --keeper-bundle <Y>` (section H, the standing G1 authority; 21 bands =
  7 price bands × 3 years, tolerance 0.05).
* **C1–C8 rubric** — `scripts/calibration_verdict.py <run-id>` after both
  bundles are registered (rule 15; registration happens whatever the runs
  show).

## Measurements and gates

**G0 — validity (hard gate; failure voids the A/B).**
BASE: solve log shows the DAM plant-grain redistribution for gas classes
ONLY (no COAL line) in all 3 years; `run_config.json` carries
`ercot_thermal_dam_availability_coal=false`; the coal min-config floor arms
(10 plants / 2,164 MW) as in the keeper.
ARM: log shows `COAL plant-grain redistribution` in all 3 years;
`run_config.json` carries the flag `true`; coal TWh differs from BASE by
> 0.5 TWh in at least one year.

**B1 — BASE currency (reported, not gated).** BASE's rubric profile is
expected IDENTICAL to the keeper's (C1/C2/C4/C8 PASS; C3a/C3b/C3c/C7 FAIL;
C6 UNATTESTED) and its G1 expected to reproduce ~19/21. Sandy Creek 2025 now
carries availability (0.137 mean fraction), so BASE 2025 coal shifts vs the
committed keeper — reported as the Sandy-Creek repair's solve-through cost,
with Sandy Creek's own 2025 TWh stated (CAMPD ran 0.697 TWh net).

**M1 — does it actually un-pin?** Fleet ceiling-pin share, BASE vs ARM.

**M2 — declaration alignment.** Model-avail / COP-declared ratio (2025, the
§2 six plants), BASE vs ARM.

**M3 — impossible hours.** Fleet impossible-hours count, BASE vs ARM.

**M4 — the over-run (the merit-bias exposure).** Coal TWh per year, BASE vs
ARM vs actual; C1 and C3a/C3c movement.

**M5 — G1 signature.** Full 21-band table for both arms; BASE count; ARM
count and WHERE the ARM moves (which bands flip which way).

## Predictions registered now (my own words, so the verdict is auditable)

1. **G0 passes** — both bundles arm as configured; the ARM bites (coal moves
   by several TWh, not <0.5).
2. **B1**: BASE reproduces the keeper's rubric profile and G1 19/21
   (permitting ±1 band from the Sandy Creek repair's 2025 ripple); BASE 2025
   coal lands ABOVE the committed keeper's 61.05 TWh by roughly +0.3 to
   +1.5 TWh, most of it Sandy Creek dispatching again (model over-ran Sandy
   Creek ~1.4–1.5× in 2023/24, so I expect ~0.9–1.1 TWh there against
   CAMPD's 0.697).
3. **M1**: BASE fleet pin ≈ 32 / 33 / 45 % (the keeper's §3 numbers,
   2025 a little lower via Sandy Creek); **ARM falls below 25 % in every
   year** (ERCOT-116 measured 20/16/17 % on the ercot115 base).
4. **M2**: ARM 2025 ratios move from 0.77–0.99 into 0.95–1.05 for the six
   §2 plants (the redistribution pins the class-hour mean to the measured
   fraction).
5. **M3**: ARM fleet impossible-hours fall by ≥ 50 % vs BASE in every year.
6. **M4**: ARM coal OVER-RUNS actual in every year, monotone worse
   2023→2025, in the +4 to +13 TWh range (old base: +5.7/+8.9/+11.0); C1
   coal goes out of band in 2025 at minimum (C1 16/16 → 15/16 or worse);
   C3a DEGRADES ≥ 3 pp in every year; C3c falls or holds (price
   suppression, the ERCOT-116 G3 signature).
7. **M5**: ARM's bottom bands (<$15, 2023/2025) RISE toward actual
   (improve), its mid bands ($15–25) go OVER (the arm-B +9–29 pp
   signature), and ≥$50 2024 worsens; net ARM G1 count ≤ BASE's, landing
   14–19/21.
8. **Overall: the ARM FAILS on level and is registered as a rejected
   probe.** A refutation that confirms this prediction is a SUCCESS — the
   lane's deliverable is the sized measurement, not a pass.

## Decision rule (fixed now)

* **G0 fails** → report mis-armed/inert; the A/B is void; nothing else is
  interpreted; both bundles still registered (rule 15) with the void stated.
* **G0 passes** → report M1–M5 in full, register BOTH bundles (hand-written
  sidecar `definition`s — `dashboard_add_run.py` copies `run_config`'s
  `model_changes_note`, which is wrong-run boilerplate on this lineage),
  update the mechanism-matrix cell for the coal availability lever with the
  re-gate verdict (rule 26 duty b), and score the full C1–C8 rubric on both.
* **No promotion in any branch.** If the ARM SURPRISES and looks promotable
  (no rubric regression vs BASE, G1 not below BASE, C1 in band) — **STOP and
  surface to the owner**; ERCOT-116 adoption is an un-ruled owner decision
  and `frontend/data/backcast/keepers/ERCOT.json` is not touched.
* **No tuning in any branch.** Nothing is adjusted to close the expected
  over-run — a residual-tuned offer/haircut is rule 13 inadmissible and
  rule 19 stacking. The over-run routes to the chartered successor
  (DIAGNOSIS §10), which does not start here.

## Declared in advance: what would NOT count

* Price MAE, either direction (rule 1).
* The ARM's annual level regression — it is the EXPECTED measurement (the
  merit bias becoming visible, rule 14), not grounds to un-measure the
  input, and equally NOT grounds to adopt it (that is the owner's ruling).
* Any comparison of the ARM against the COMMITTED ercot129 bundle — stale
  basis; the fresh BASE is the only comparator.
* The ≥$300 scarcity tail set (C3c reported under M4, not read as a tail
  claim).

## Known at write time

Known: everything in `DIAGNOSIS-ercot134` (keeper pin/ratio/impossible
tables on current-HEAD availability; the audit); ERCOT-116's old-base
results in full (coal +6.8/+9.2/+12.9 TWh vs ercot115, C3a −7.6/−7.0/−5.6
pp, pin halved 43/41/50→20/16/17 %); the keeper's G1 19/21 and rubric
profile; the arming-line grep patterns.

**Not known:** any solved result of either regate bundle. No year of
`ercot116_regate_base` or `ercot116_regate_arm` had been solved when this
document was written and pushed. The genuinely open quantities: how the
min-config floor (absent from every prior ERCOT-116 solve) interacts with
the measured coal availability; and what the Sandy-Creek-repaired 2025
does under either config.

---

## Verdict recorded after the fact

**G0 PASS · measurement delivered · ARM rejected on level as predicted · BASE
promoted keeper (owner sign-off this session).** Full write-up:
`results/calibration/FINDING-ercot134-regate-2026-07-28.md`. Runs
`2026-07-28-ercot116-regate-base` (keeper) / `2026-07-28-ercot116-regate-arm`
(rejected probe). Predictions: 6 of 8 confirmed; misses — ARM plant-hour pin
share fell only to 28.1/27.9/38.6 % (the <25 % prediction anchored to
ERCOT-116's energy-on-flat-top statistic, a different basis), and ARM G1
landed 1/21 against the predicted 14–19/21 (the merit bias is uniform across
every price band, larger than predicted — that is the finding). Impossible
plant-hours −83/−86/−91 %; over-run +6.5/+9.6/+11.4 TWh; C3a
−35.3/−14.7/−13.2 %. No tuning; no ERCOT-116 adoption (owner ruling still
open); successor: the coal-vs-gas merit-order lane on the un-pinned fleet.
