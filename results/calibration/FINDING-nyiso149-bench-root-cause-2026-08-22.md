# FINDING nyiso-149 — the NYISO benchmark root cause: the drift is the measured-BTM subtrahend re-arming the ±3% family reconcile, and the REGENERATED reconciliation is CORRECT

Session nyiso-149, 2026-08-22. Owner-chartered per
`FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md` §11 item 1,
BLOCKING any NYISO re-calibration. Evidence record:
`_nyiso149_bench_reconcile_closure.json` (probe
`scripts/probes/_nyiso149_bench_reconcile_closure.py`). **No LP was solved; no
determination, keeper, marker or bench part byte changed in this Part.** The
one code change is the benchmark-basis pin (§7), which reproduces the committed
authoritative parts byte-for-value and exists so they can never silently flip
back.

---

## 0. THE ANSWER, in the charter's own terms

1. **The commit is `01db36d`** (nyiso-147, 2026-08-20: *"wire
   nyiso_chp_btm_measured through the three BTM-share legs"*) — the very commit
   the charter carried as *ruled out*. The ruling-out inherited nyiso-148 §2's
   flag-flip measurement, which was structurally blind to the flag's real
   channel (§4). The change SURFACED at `f9145cf` (nyiso-148's registration,
   2026-08-21) because that was the first **flag-ON** registration whose
   re-rendered bench parts were **committed**; nyiso-147's own registration
   (`d1a298d`, 2026-08-20) re-rendered the same flipped parts on its container
   and committed none of them (§5).
2. **The EIA-923 vintage-reconciliation / CAMPD-backfill layer never moved.**
   The benchmark EIA-923 frame rebuilt at HEAD from today's raw data hashes to
   **`920c8b8bc1b1`** — the identical content-addressed shared-input name that
   every registered NYISO bundle meta declares, nyiso-142 (which wrote the old
   part) and nyiso-148 (which wrote the new one) alike. Same hash ⇒ same rows:
   `_benchmark_eia923_frame` / `_backfill_eia923_with_campd` produced the same
   output in both eras. nyiso-148 §3's "the delta lives in the
   vintage-reconciliation layer" was a **residual attribution** (declared
   classFull minus the plants-table sum), not a measurement of that layer.
3. **The regenerated (HEAD) reconciliation is CORRECT, on evidence** (§6). The
   owner's 2026-08-21 "regenerated is authoritative" ruling is hereby grounded
   in mechanism, not just recency: the old part's extra +3.98 TWh of
   CC_REGULAR-2024 "actual" traces to no meter — it is the ±3% EIA-930 family
   reconcile pro-rata re-inflating a gas family that the refuted 35% sector
   carve had over-shrunk. The keeper's C1-2024 `CC_REGULAR` failure (+5.18 TWh)
   is a TRUE model defect that the old benchmark's compensation masked.

## 1. HOW classFull IS ACTUALLY ASSEMBLED (the piece nyiso-148 could not see)

The bench part's per-class actual is not the e923 frame alone. At render time
(`render_calibration_html.build_payload`):

```
classFull[k] = Σ e923_frame[k] / 1e6  −  btm_cls[k]          # grid-delivered
reconcile_vintage_classes(classFull, e930, iso)              # THEN, in place:
    family = Σ over gas+coal classes
    target = e930.gas + e930.coal (foldin-deflated)
    if not (0.97·target ≤ family ≤ target/0.97):
        scale EVERY fossil class by target/family              # pro-rata
```

Two of the three inputs are **bundle-borne**: the e923 frame (shared-store
parquet — proven identical, §0.2) and **`btm_cls` from the bundle's
`btm.parquet`** — which `01db36d` made flag-dependent: sector shares
(`CHP_BTM_PCT_BY_SECTOR`, merchant 35%) with the flag off, the measured
Gold-Book/EIA-923 per-plant shares with it on. The shared per-(ISO, year) bench
part therefore inherited the **registering run's config**.

## 2. THE TWO CHANNELS, QUANTIFIED (2024 shown; record has all years)

| | flag OFF (sector 35%) | flag ON (measured) |
|---|---|---|
| btm_cls CC_CHP / CT_CHP / ST_CHP (TWh) | 6.71 / 0.25 / 0.56 | 1.76 / 0.14 / 0.39 |
| gas-family classFull pre-reconcile | **60.71** | **65.95** |
| EIA-930 gas+coal target | 67.80 | 67.80 |
| shortfall vs target | −10.5 % → **fires** | −2.7 % → **in deadband** |
| reconcile scale applied | **×1.11683** | ×1.0 |

- **Channel A (CHP classes):** the subtrahend itself — measured shares remove
  ~4.9 TWh less BTM than the 35% carve.
- **Channel B (every gas class, CC_REGULAR included):** the reconcile. With the
  sector carve, the family sits 6.5 % / 10.5 % / 15.9 % (2023/24/25) below the
  independent EIA-930 grid total, so the reconcile scaled **every** gas class
  ×1.06921 / ×1.11683 / ×1.18857. With the measured subtrahend the family lands
  within 1.1 % (2023) and 2.7 % (2024) of EIA-930 — no scale — and 2025 (a
  genuinely preliminary EIA-923 vintage) still scales, ×1.10131, which is the
  reconcile doing its designed job of vintage repair rather than carve
  compensation.

CC_REGULAR-2024's −3.9791 TWh is **exactly** its old ×1.11683: carries no BTM,
so its entire move is Channel B. The "implied backfill +8.00 → +4.02" of
nyiso-148 §3 decomposes as: real (unchanged) CAMPD backfill and non-modeled
plant rows ≈ +4.02, plus the reconcile's smear +3.98 that existed only on the
old part.

## 3. THE CLOSURE — every class, every year, EXACT

`_nyiso149_bench_reconcile_closure.json`: rebuilding classFull from the ONE
shared e923 frame with the **sector** subtrahend reproduces the OLD part
(92d8eee) **EXACTLY (≤0.0005 TWh) on every gas/coal class in 2023, 2024 and
2025**; with the **measured** subtrahend it reproduces the NEW part exactly.
Nothing else differs: the two parts' `e930` dicts are equal, the per-plant
rows differ only by the two measured-BTM display fields nyiso-148 already
found, and the e923 frame is hash-identical. There is no residual left for any
other cause.

## 4. WHY nyiso-148's TEST EXONERATED THE FLAG (the blind spot, stated plainly)

nyiso-148 §2 rebuilt the part twice from "a scratch copy of the same bundle
with the meta flag flipped" and got byte-identical classFull — concluding "none
of it is the flag". The test was sound arithmetic on an unsound premise:
`rebuild_benchmark` rebuilds the e923/e930/campd parquets **but not
`btm.parquet`**, which is written at solve time. Both scratch rebuilds
therefore shared the armD bundle's flag-ON btm.parquet, and the meta flip
changed nothing that feeds classFull. The flag's channel *is* btm.parquet; the
test held it fixed. Likewise the staleness sweep's `01db36d` annotation
("cannot … touch the classFull reconciliation layer") was wrong at one remove:
the commit never touches the reconcile's code — it moves the reconcile's
*input* across its deadband.

## 5. WHY IT SURFACED ONLY AT nyiso-148

`dashboard_add_run.py` re-renders the bench parts on **every** registration
from the registering bundle. 2026-08-17→08-19 registrations (nyiso-143…146c)
were flag-OFF bundles → re-rendered parts byte-identical to the committed ones
→ nothing to commit. nyiso-147's registration (`d1a298d`) rendered from the
flag-ON armA bundle → the parts flipped on its container — and the commit
carries sidecars, payloads, logs and matrix shard but **zero bench parts**:
the flip was left unstaged (the registration protocol's "commit any changed
bench parts" was missed; nothing in the tooling flagged it). nyiso-148's
registration produced the same flip and committed it. So the "2026-08-17 →
HEAD drift" was never a gradual drift: it is one binary flip that happened
(silently) on 08-20 and landed (visibly) on 08-21.

## 6. THE RULING — the regenerated reconciliation is CORRECT

**The benchmark's BTM subtrahend must be the measured shares, and therefore
the regenerated parts (and every verdict scored on them, the keeper's NOT-YET
included) stand.** Grounds:

1. **The subtrahend is a measured physical quantity, and the measurement
   refutes the estimate.** The 35% merchant carve is residual-identified — its
   own citation reads *"no independent source yet"* — while the measured
   shares are each plant's two published meters (Gold Book net energy vs
   EIA-923 net generation, pooled CY2022-2024, rule-13-admissible, rule-23
   frozen). nyiso-147 proved the carve wrong plant-by-plant: Sithe
   Independence delivers 100.3 % of its EIA-923 net to the market three years
   running (BTM ≈ 0, not 35 %); Brooklyn Navy Yard's carved capacity implies
   CF 1.07. Rule 14 `[R-ACCURATE]` does not permit keeping the estimate
   because its removal worsens a fit — and here it isn't even the model's fit
   at stake but the *benchmark's own accounting*.
2. **Two independent measurement systems agree only under the measured
   subtrahend.** EIA-923+CAMPD minus measured-BTM lands within 1.1–2.7 % of
   the EIA-930 grid total for the complete vintages — inside the reconcile's
   own "well-measured" deadband — while the sector-carve version missed by
   6.5–10.5 % and had to be force-scaled to the 930 cell every year. A
   benchmark that needs a ×1.12 annual correction to agree with the grid
   telemetry is not measuring grid delivery; one that agrees unscaled is.
3. **The old part's extra mass traces to no meter.** The +3.98 TWh of
   CC_REGULAR-2024 the old part carried above the new one is reconcile smear:
   pro-rata re-inflation of *every* gas class to cover energy the carve had
   deleted from the *CHP* classes. No EIA-923 row, no CAMPD series, no 930
   fuel cell attributes those 3.98 TWh to CC_REGULAR plants. An "actual" that
   is not traceable to measurement fails the same test rule 13 applies to
   inputs.
4. **The exposed C1 failure is independently corroborated as a real model
   defect.** On the correct benchmark the keeper over-dispatches CC_REGULAR
   2024 by +5.18 TWh while the CHP classes' capability is under-carried — the
   exact structure nyiso-147/148 diagnosed from the other side (the carve's
   phantom absence re-served by CC_REGULAR/ST_GAS at almost the same offer).
   The old benchmark cancelled a real error with a fabricated one; rule 1
   `[R-STRUCT]` reads that as two defects, not a fit.

**Standing consequences.** The keeper `2026-08-19-nyiso-146c-state-scoped`
remains NYISO's designated keeper and remains **NOT-YET**, now with the cause
fully understood: its C1-2024 miss is real, of one piece with the frontier's
CHP capacity+conduct object, and the re-calibration lane this finding was
blocking may open. The `marker_reexamination_open` question (§11 item 4 of the
nyiso-148 finding) stays with the owner, unchanged by this ruling.

## 7. THE PIN — the ruling made durable (shipped in this session)

Without a mechanism change, the ruling would last exactly until the next
flag-OFF NYISO registration re-rendered the parts back to the sector-carve
basis. Shipped, verified, and byte-stable:

* **`_btm_frame` now emits `btm_bench_twh`** beside `btm_twh`: the
  benchmark-basis class totals, sized from the measured shares **whenever the
  measured artifact exists** (`measured_chp_btm_pct_nyiso`), independent of
  the run's `nyiso_chp_btm_measured` flag. `btm_twh` still follows the flag —
  it states what *this run's* LP actually held out, which is what the model's
  add-back must use. For every ISO without a measured artifact the columns are
  byte-equal duplicates.
* **The render's bench-part writers consume the bench basis** — `classFull`'s
  subtrahend, the CEMS-anchor `_coal_grid`, `co2.btmClass`, the per-plant
  `plants[].btm` fields and the `gas_cogen_grid` anchor (via artifact-gated
  `_btm_measured`) — while the run payload's `gmModel` add-back stays on the
  run basis. Old bundles without the column fall back to `btm_twh` unchanged.
* **Verified**: the closure probe re-renders the committed authoritative parts
  **EXACTLY, with the flag OFF and ON alike**, in all three years
  (`pin: flag_off_render_now_reproduces_new_part: EXACT`), while the run basis
  stays flag-dependent. Unit-pinned in
  `tests/regression/test_btm_bench_basis_pin.py` (hermetic, no corpus).

## 8. WHAT THIS SESSION DELIBERATELY DID NOT DO

* **Not implemented: `rebuild_benchmark` rebuilding `btm.parquet`.** Its
  docstring's "the benchmark frames are pure functions of (year, iso)" is now
  true again only because of the pin; adding the btm frame to the rebuild
  would close the §4 blind spot at the tool level too. Recommended follow-up,
  small, no solve required.
* **No cross-ISO assertions** (rule 25): the pin is inert outside NYISO by
  construction (no measured artifact ⇒ identical columns), and the five other
  ISOs' bench regenerations remain their own lanes.
* **No determination, keeper, marker or shard edit**: nothing tested here is a
  solve-affecting mechanism (the pin changes only what the *benchmark* states,
  proven byte-stable for the committed parts), and the keeper's recorded
  NOT-YET already reflects the authoritative parts.
* **The nyiso-148 finding is answered by addendum, not rewritten** — its §2/§9
  inferences are corrected in place with a pointer here, preserving the
  escalation record.

## 9. REPRODUCTION

```
cd scripts && ../.venv/bin/python probes/_nyiso149_bench_reconcile_closure.py
# → results/calibration/_nyiso149_bench_reconcile_closure.json (all EXACT)
../.venv/bin/python -m pytest tests/regression/test_btm_bench_basis_pin.py -q
git show 92d8eee:frontend/data/backcast/bench/NYISO/2024.json.gz | zcat | jq .bench.classFull.CC_REGULAR   # 38.0395
zcat frontend/data/backcast/bench/NYISO/2024.json.gz | jq .bench.classFull.CC_REGULAR                      # 34.0604
```
