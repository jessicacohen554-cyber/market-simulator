# RESULT — SPP-36: `unit_outage_short_windows` armed across 2023–2025. SPP's TENTH KEEPER, promoted on the owner's ruling.

**DETERMINATION `CALIBRATED`** (rubric v3.7) · grade 7 of 8 · **0 FAILS** · 1 ledgered C3c caveat ·
0 protective · free-class C1 **16/16 all · 12/12 free** — the same shape as keeper 9 on every scored
criterion, **re-verified by the parent from committed artifacts with no solve**.

Run `2026-09-12-spp-36-shortwindow-span`, bundle `results/calibration/spp36_span`.
Control `2026-09-10-spp-27-commitment-grain` (keeper 9), differenced and **never re-solved**
(rule 29(b) form 4). Parent LP: **zero**.

## 1. THE RULING

> *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but
> gates regress that may still be a keeper."* — owner, in session, 2026-09-12.

`keepers/SPP.json` was untouched until the ruling (rule 31 `[R-RETAIN]`).

## 2. THE ARM — one field, zero code, one new measured input

SPP's LP ignored **every** sub-5-day unit outage in its own CAMPD record. The extract
(`data/raw/campd-unit-outages-short-SPP.csv`, 620 windows / 24 plants / 39 units, **620 of 620 rows
`plant_group == COAL`**) had sat committed and unarmed since it was derived, and the matrix cell was
**`U`** — a first test, not a re-test (rule 28(a)); PJM's and MISO's `K` and NEISO's `R` fill no SPP
cell (rule 28(d)). The extract was **not** re-derived (rule 23 `[R-FROZEN-DERIVE]`).
`unit_outage_short_windows_gas` stays **`False`** — cell `R`, killed by SPP-32.
`offer_curve_by_group` byte-identical in both legs, whole-mapping SHA-256
`090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`.

## 3. MEASURED, span vs span

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| plant-tranches derated (vs the ≥5-day overlay's) | 80 / 302 | 73 / 298 | 94 / 303 |
| coal TWh, control → arm | 72.8124 → 70.7851 | 67.1699 → 64.7963 | 87.2130 → 84.0355 |
| gas TWh, control → arm | 70.6275 → 72.6558 | 76.1721 → 78.5485 | 64.4307 → 67.6115 |
| **slack MWh, control → arm** | **0.0000 → 0.0000** | **370.1017 → 370.1017** | **0.0000 → 0.0000** |
| dump MWh | 0.0000 → 0.0000 | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| LW mean price | 25.3716 → 25.7428 | 25.4676 → 26.0214 | 28.7893 → 29.5377 |
| hours > \$200 (actual 42 / 59 / 68) | 0 → 0 | 5 → 7 | 0 → 0 |

Energy conserved to ≤ 0.0032 TWh. **The arm adds no unserved energy in any year** — 2024's slack is
the keeper's own pre-existing 2-hour SPP-South event, unmoved to the digit.

**Reported as the cost, not dressed up:** C3a **+2.44 / +3.54 / +5.15 %** (keeper 9: +0.96 / +0.07 /
+0.66) and C3b **0.1760 / 0.1658 / 0.1878** (keeper 9: 0.1728 / 0.1682 / 0.1638). Both degrade on two
years, 2024's C3b **improves**, and all six stay inside their bands. C5a CO2 −2.7 / −2.5 / +1.4 %.

## 4. THE PARENT'S OWN ERROR, AND THE FALSE FINDING IT PRODUCED

The span was first fanned into **three per-year shards**. They solved correctly, but their slim
pushed outputs **cannot compose into a registrable run**: `build_payload` needs the bundle-root
`system.parquet` and D-1/D-2/D-4 need `dispatch/<year>_<pass>.parquet`, both gitignored, and
`--reuse-solved` gates on the same two. The composite's D-1/D-2/D-4 returned **zero rows and passed
vacuously** — **D-4 flipped `False → True`** against the control's 71 rows / 12 failures, which reads
as a structural win and is nothing of the kind. It was caught by checking row counts, not verdicts.

Worse, the fan-out **produced a false result that was reported to the owner**: differencing
single-year arm solves against a **span-solved** control, the legs showed the arm adding
**1,295.6995 MWh** (2024) and **240.5966 MWh** (2025) of slack. The span-vs-span A/B above — arm and
control both 3-year invocations — shows slack **unchanged in every year**. The construction mismatch
was mine.

This is now banned: **rule 32 `[R-SHARD]` (b)**, amended by owner instruction the same day
(*"Ok ban slim shards this is dumb I should only have to wait for one solve wtf"*);
`docs/governance/rule-history.md` §19.

**OPEN AND ROUTED, NOT CLOSED.** 2023 — first year in both constructions — reproduces to 4 dp; 2024
and 2025 do not. Whether SPP's solve carries **process-order sensitivity** is unresolved, and it is
not idle speculation: SPP-27 already recorded `reconstruct_bundle_fleet` as order-dependent across
years within a process for SPP. **The registered A/B is unaffected either way**, because both legs
are 3-year invocations sharing construction. A lane should settle it; this one did not.

## 5. RULES

- **Rule 21 `[R-DOF]`** — the arm adds **one** entry, `unit_outage_short_windows`, identified
  **measured-physical**, not residual. Ledger **5 / 3**. The like-for-like baseline is the
  **control's own config rebuilt at HEAD**, which gives **4 / 3** — keeper 9's committed **3 / 2** is
  **stale** (the builder at HEAD adds `st_gas_mustrun_per_plant` and reclassifies
  `offer_curve_smoothing` as residual). **`n_residual` is unchanged by this arm.** The PRECOMMIT's
  prediction of "stays 3/2" was wrong about the baseline, not about the arm.
- **Rule 19 `[R-ONE-MECH]`** — disjoint from the ≥5-day overlay by DURATION and from every gas scope
  by plant group. It widens a discard; it stacks on nothing.
- **Rule 29(b) / G-DRIFT** — all twelve changed solve-path files INERT. The one needing proof:
  SPP-30's out-of-training intake moved `actual_lmp_hourly_SPP.parquet` 2023-2025 → 2019-2025, so the
  keeper's own `basis_sha` blob was read back and compared row-for-row — **2023/2024/2025 identical**,
  additive years only, tail rows unchanged at 42 / 59 / 68.
- **Rule 16 / 32** — one shard, one `--years 2023 2024 2025` invocation, 377 s, years sequential.
- **Diagnostics, with row counts checked**: D-1 PASS (25) · D-2 PASS (15) · **D-4 FAIL (71 rows,
  12 failures)** · D-5 PASS (8) · D-9 PASS (5) · D-10 PASS (6). No vacuous pass.

## 6. WHAT THIS KEEPER STILL CARRIES

- **D-4 off-window binding still FAILS**, 12 rows of 71, every one `st_gas_mustrun_per_plant × ST_GAS`
  on plants 1230 / 1235 / 1271 / 3008 / 6193 — **identical to keeper 9** and unrelated to this
  COAL-scoped overlay. Card **R-be**'s day-selection half is open and no forecast-admissible signal
  reaches it.
- **C3c** remains the accepted model-class limitation SPP-29 *measured* rather than asserted.
- The live queue is unchanged: **R-bc** (price-forming curtailment), **R-ba** (merit inversion).
- **SPP holds no `complete` entry and this promotion deliberately does not create one** — a separate
  owner act. Forecast gate (a) still reads `fail` on the marker alone.
- `[R-HOLDOUT]` was removed 2026-09-09: **`CALIBRATED` is a rubric determination, not a certified
  out-of-sample skill claim.**
