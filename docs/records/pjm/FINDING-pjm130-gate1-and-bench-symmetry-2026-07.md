# FINDING — pjm-130: gate 1 is displacement, its lever is real, and it sits on a benchmark cell the scored run writes itself — the one-sided BTM repair is fixed

**Lane:** the PJM re-tune opened by pjm-129's `NOT-YET`.
Charter (kill criteria + named exposure): `docs/handoffs/pjm-130-retune-charter-2026-07.md`.
**No LP was solved.** Every measurement below comes from a probe whose question,
method and decision rule were committed *before* it was run.

---

## §0 — verdict

| gate | status after this session |
|---|---|
| **C1-2023 CC_REGULAR** (−8.10 TWh vs 8.00 band) | **DIAGNOSED, not closed.** The marginal move is displacement (99.6 %, r = −0.369), and a real structural lever exists: the guard-returned classes now dispatch **past their metered annual energy**. Arming it was blocked by §2 and is now unblocked. |
| **C3a-2025** (−10.6 %, needs +0.6 pp) | **BLOCKED — owner decision.** Its only level-bearing admissible route needs the re-conditioning memo, still undecided. Not worked around. |
| **C3c 2024/2025** (0.39× / 0.47×) | **LEDGERED, root cause out of reach.** Both scoping framings closed; the shared floor is 5.0–5.6× the requirement and 17.5 GW of it is tariff-protected Non-Sync Primary reserve. A MIP would not close it either. |

**Shipped:** a benchmark-integrity defect — a **negative metered volume** in a
committed benchmark — reproduced, localized and **fixed** (`03e105f`), with a
regression test. It was gate 1's prerequisite, not a side item.

**Not shipped:** any A/B solve. Under the conditions above every arm available
would have been a mechanism fitted to a residual (rules 1 `[R-STRUCT]`, 23
`[R-FROZEN-DERIVE]`, 26 `[R-DELETE]`). This is the pjm-124/125/126/127/128
pattern — five candidates closed on no-LP pre-checks with no solve spent.

## §1 — gate 1: the marginal 0.23 TWh is displacement, and it is hour-for-hour

`scripts/probes/pjm130_c1_ccregular_displacement.py`, on the two arms' committed
`hourly/class_hourly_<year>.parquet` sidecars and the committed PJM bench.
Pre-registered rule: DISPLACEMENT iff ≥60 % of CC_REGULAR's gross hourly loss
falls in hours where the returned supply rose **and** r ≤ −0.30.

| year | Δ CC_REGULAR | Δ returned | loss share in returned-up hours | r | verdict |
|---|---|---|---|---|---|
| 2023 | −0.230 TWh | +3.865 | **99.6 %** | **−0.369** | **DISPLACEMENT-CONFIRMED** |
| 2024 | −0.795 | +2.720 | 98.4 % | −0.280 | AMBIGUOUS (r just inside) |
| 2025 | −0.388 | +3.829 | 97.9 % | **−0.433** | **DISPLACEMENT-CONFIRMED** |

2024 is reported as AMBIGUOUS on its own pre-registered rule rather than rounded
into the verdict. The failing year, 2023, is unambiguous: essentially **all** of
CC_REGULAR's hourly loss lands in hours the returned supply is up.

So C1-2023 CC_REGULAR is not a CC_REGULAR under-dispatch story. It is the
−7.87 TWh standing shortfall the keeper already carried (98 % of band), pushed
0.10 TWh over the line by supply the guard correctly returned.

## §2 — the lever is real: the returned classes overshoot the meter

The pre-registered kill criterion was that a lever exists **only if** some
returned class now exceeds its *metered* actual while CC_REGULAR is short.
2023 (TWh, model vs EIA-923-derived bench actual):

| class | actual | keeper | A1 | A1 − actual |
|---|---|---|---|---|
| **CC_REGULAR** | 325.67 | 317.80 | 317.57 | **−8.10 (FAIL, band 8.00)** |
| **CC_CHP** | 6.11 | 8.01 | **8.65** | **+2.54 (+41 % over meter)** |
| **ST_GAS** | 8.88 | 8.09 | **10.60** | **+1.72 (+19 % over meter)** |
| COAL_BIT | 103.03 | 100.77 | 101.69 | −1.33 |
| CT_PEAKER | 21.66 | 23.20 | 21.78 | +0.12 (was +1.54 — improves) |

The criterion is met, and the shape of the miss is now specific: **+4.26 TWh of
CHP and gas-steam energy above the meter against a −8.10 TWh CC_REGULAR
shortfall.** Note CT_PEAKER *improves* to near-exact — the guard's returned
supply displaced peaking correctly; what it did not do is route the freed energy
to the class the meter says served it.

That is a merit-order ownership question, and it is the **same** question
pjm-122 named for gate 2 (fitted rungs owning a region the measured corpus
assigns elsewhere). Gates 1 and 2 are one stratum, which is why gate 1 cannot be
closed independently while gate 2's measured route is owner-blocked.

## §3 — the prerequisite: a committed benchmark asserting negative metered energy

Gate 1's largest signal (CC_CHP, +2.54 TWh) is measured against a `classFull`
cell computed as

    classFull[k] = e923_bench[k] − btm[k]

where `btm` is the **scored run's own** `btm.parquet`. pjm-129 §6 reported the
symptom and was forbidden from touching it: registering A1 moved the committed
`bench/PJM/2025.json.gz` cell `classFull.CT_CHP` to **−0.3726 TWh**. A metered
grid volume cannot be negative — the subtrahend had escaped its minuend.

`scripts/probes/pjm130_chp_bench_attribution.py` reproduces and localizes it from
committed inputs only:

* Reconstructed with **no** backfill, the invariant `btm[k] ≤ e923_bench[k]`
  holds in all three years and 2025 CT_CHP is **+0.6385**, positive.
* Reconstructed with `--btm-backfill-year 2024` armed, the BTM cells come back
  **4.4251 / 2.0959 / 0.6801** — the committed bench's `btmClass` values **to
  4 dp, all three classes** — and the invariant breaks at **exactly** CT_CHP
  (2.0959 > 1.8162 ⇒ −0.2798). That identifies the path beyond doubt.

**The defect.** `--btm-backfill-year` carries a plant's donor-vintage class total
when the target year's EIA-923 release is a thin monthly survey (2025 reads ~73 %
complete). It was applied to the **BTM side only**. The benchmark's own repair,
`_backfill_eia923_with_campd`, fires on **non-CHP** plants by construction, so a
backfilled CHP plant's host share was subtracted from a class total that never
received that plant's energy. One-sided repair, negative cell.

**The fix** (`03e105f`) — `_backfill_chp_eia923_from_donor` mirrors the repair
onto the benchmark: same donor vintage, same `campd_active` gate, same
per-(plant, class) key, CHP classes only, and only where the target vintage
reports zero. Both sides then describe the same plant population, so
`btm[k] ≤ e923_bench[k]` holds **by construction** (the host share is ≤ 1).
Rule 14 `[R-ACCURATE]`: the plant genuinely generated and the gap is a reporting
artifact of the vintage, so the accurate treatment repairs both sides — never one.

Measured effect on PJM:

| year | vintage | effect |
|---|---|---|
| 2023 | complete | **byte no-op**, every cell |
| 2024 | complete | **byte no-op**, every cell |
| 2025 | thin | CT_CHP `classFull` **−0.2798 → +1.4653**; CC_CHP 6.3192 → 6.4827 |

**No C1 row changes verdict** (both classes stay far inside band on the corrected
actuals). The corrected bench lands on the next PJM registration — the renderer
writes `bench/` at registration time, so no solve is *required* to fix it, but no
solve in this session means it is not yet written. Wired at the solve call site
and in `rebuild_benchmark`, which recovers the flag from the bundle's
`run_config.json` when one recorded it.

Pinned by `tests/regression/test_btm_benchmark_symmetry.py` (6 tests): the
invariant, never-overwrite-measured, the `campd_active` gate, the non-CHP no-op
and the complete-vintage no-op.

**Consequence for gate 1.** 2023 is a complete vintage, so the fix is a no-op
there and **§2's numbers stand unchanged** — the +2.54 TWh CC_CHP overshoot is
real, not an artifact. What the fix removes is the risk of arming gate 1 against
a 2025 CHP cell the run had authored.

## §4 — gate 2: blocked, and deliberately not worked around

The only *level*-bearing admissible route to C3a-2025 is the measured
re-ownership of the $40–150 region (pjm-122: fitted coal rungs own a region the
measured corpus assigns to the CC top belt and CT_FAST). The surface that
carries it is inadmissible until the owner decides
`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md` (rule 23
`[R-FROZEN-DERIVE]`). **Verified undecided this session** — last commit `f1070d4`,
no decision has landed. Not nudged, not re-derived, no proxy taken.

Carried forward unchanged: pjm-121's honest-scope caveat — 73 % of its 2025 C3a
gain was a level lift and the monotone dispersion compression is untouched.

## §5 — gate 3: ledgered, root cause out of reach

C3c 2024/2025 (0.39× / 0.47×) is downstream of the open G-20b/G-22 reserve
supply-side tightness class, now with *more* supply in it — the guard's returned
capacity removes scarcity hours (model >$200 h fell 5→2 / 9→7 / 39→28 against
unchanged actuals 6 / 18 / 59). Both scoping framings are closed on record
(pjm-124 INERT, pjm-125 PARTIAL), and pjm-125 measured the floor they share at
**5.0–5.6× the requirement**, 17.5 GW of which is offline fast-start iron that
counts as Non-Synchronized **Primary** reserve under Manual 11 §4.2 and is
untouchable by any commitment mechanism — so a MIP would not close it either.

**This session did not reach the root cause and did not invent a mechanism for
it.** Ledgered as-is, per the charter.

## §6 — reported, not introduced

`tests/regression/test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
**fails on a clean checkout of `origin/main`** in this container (expected
`edbc1b103207170a`, got `30065460cdc3042c`). Verified pre-existing by stashing
this session's work and re-running. The test's own message says a changed default
"orphans every on-disk cache and breaks keeper reproducibility" and warns against
updating the literal to silence it — so it is **flagged, not touched**. It is
unrelated to this session's change (nothing here reaches `ScenarioConfig`).

## §7 — rule compliance

* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. The freeze is untouched and NOT
  lifted; PJM still has no calibration-complete marker.
* **Rule 15 `[R-DASHBOARD]`:** no solve completed, so there is no bundle to
  register. Nothing was solved and quietly dropped.
* **Rule 16 `[R-ALLYEARS]`:** no bundle produced; no single-year artifact exists.
* **Rules 20 / 23 / 24:** nothing tuned — no offer-curve band, sigmoid, floor,
  ORDC parameter, derive value or surface JSON touched.
* **Rule 27 `[R-PUSH]`:** `run_calibration_full.py` (10,422 lines) was edited in
  place with the Edit tool and blob-verified byte-identical against the remote
  after push. No regenerated full-file content was ever pushed.
* **Keeper designation** `2026-07-25-pjm-121-cc-belt` untouched; `keepers.json`
  not edited (miso-88 precedent).

## §8 — what PJM needs next

1. **Gate 1 is now armable.** The target is specific: reduce the CC_CHP
   (+2.54 TWh) and ST_GAS (+1.72 TWh) 2023 overshoot **against the meter**, not
   raise CC_REGULAR directly. The charter §5 pre-registers the kill criteria,
   including the refutation signature — an arm that lifts CC_REGULAR while
   leaving the returned classes above their metered energy is displacement-neutral
   and dies.
2. **Gates 1 and 2 are one stratum.** §2's ownership miss and pjm-122's are the
   same question. Sequencing them together is likely cheaper than either alone —
   but gate 2 stays blocked until the memo is decided.
3. **The memo decision is still the gating item for the whole lane**, exactly as
   pjm-127b left it. Frontier remains NOT ready and owner-declared only.

## Reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/regenerate_clean.py \
    transfer-interface-limits ramp-capability lmp
PYTHONPATH=. .venv/bin/python scripts/probes/pjm130_c1_ccregular_displacement.py \
    --json-out results/calibration/pjm130_c1_displacement.json
PYTHONPATH=. .venv/bin/python scripts/probes/pjm130_chp_bench_attribution.py \
    --iso PJM --years 2023 2024 2025 --backfill-from 2024 \
    --json-out results/calibration/pjm130_chp_bench_attribution.json
PYTHONPATH=. .venv/bin/python -m pytest tests/regression/test_btm_benchmark_symmetry.py -q
```

Fidelity anchor (no solve): `pjm120_c3a_stratum_readout.py
results/calibration/pjm121_ccbelt --year 2025` needs `data/clean/lmp/PJM/RTM/`
present — it is derived and absent in a fresh container.
