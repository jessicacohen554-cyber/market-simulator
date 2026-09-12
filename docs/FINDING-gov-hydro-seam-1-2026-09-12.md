# FINDING (gov-hydro-seam-1): both pjm-h1 escalations LANDED — and decision 2 turned out
# to be a PRECONDITION for decision 1, not an independent nicety

**Session** `gov-hydro-seam-1` · **Scope** CROSS-ISO GOVERNANCE · **Date** 2026-09-12
**Base** `origin/main` @ `fb73c4f6` (the handoff cites `5327e60d`; main moved before this
session opened, and every measurement below is against what is actually at HEAD).
**ZERO LP.** The parent never solved (rule 32 `[R-SHARD]` (a)) and no shard was launched.
**All seven keepers UNCHANGED at CALIBRATED**, re-scored before and after.
**No keeper promoted, demoted or re-keyed.** Pre-registration:
`docs/PRECOMMIT-gov-hydro-seam-1-2026-09-12.md` + `docs/ADDENDUM-gov-hydro-seam-1-vintage-fallthrough-2026-09-12.md`.

---

## 1. RESULT

> **BOTH DECISIONS TAKEN. pjm-h1 §7 option (a), unconditionally, and the §5 `classify_plant`
> repair — and the second is a PRECONDITION for the first, which the escalating session did
> not state.**
>
> pjm-h1 §7 says of the two: *"It is not needed for (a), and (a) is not needed for it."* That
> is true only in the sense that each compiles alone. **As a correctness claim it is false.**
> Under (a) ALONE, a folded ISO-year's hydro actual becomes the EIA-923 `hydro` **bucket** —
> which today carries pumped-storage **net**, i.e. a negative number. PJM 2023 would land on
> **6.4513 TWh** where the conventional `HY` population is **8.9763**: (a) alone trades a
> **+72.5 %** error for a **−28.1 %** one and lands on a third population that is neither side
> of the comparison. **(a) is a repair only if the bucket it falls back to is
> conventional-only, and decision 2 is what delivers that.**
>
> **THE PRE-REGISTERED FALL-THROUGH WAS ALSO WRONG, AND THE MEASUREMENT CAUGHT IT (§4).** The
> PRECOMMIT routed an early-release vintage to the existing nyiso-106 carry-forward. Measured,
> that carry **never fires** where it is needed: its trigger, `_vintage_completeness`, is an
> **ISO-total** ratio reading **0.9233 / 0.9230** for PJM / MISO in 2025 while those ISOs file
> **10 of 72** and **14 of 160** hydro plants. Left as written the repair would have scored PJM
> 2025 against **2.2898 TWh** — a −74 % error replacing a +74 % one, exactly the "worse defect
> than the one you are fixing" the handoff named. Repaired on structure by ANDing the
> already-adjudicated hydro-census gate (`complete_923_hydro_years`), so the swap is refused
> only where a right-population measurement exists to refuse it in favour of.
>
> **NOT SOLVE-AFFECTING, AND THE VERDICT IS MEASURED RATHER THAN INHERITED (§3).** The handoff
> offered a read of the `classify_plant` call-site blast radius and asked that it be verified,
> not inherited. It is correct, and the measurement is stronger than the argument: the repair
> moves **exactly 366 EIA-923 rows** 2019-2026, every one `WAT`/`PS`, none of any other kind;
> **zero** dominant-class flips reach a gas class, so the ERCOT bin override and
> `mixed_fossil_plants` are byte-identical; and the injected `OTHER` must-run — a **solve
> input** — moves **0.000000 MWh in all 42 scored ISO-years**.
>
> **GATE-NEUTRAL ACROSS THE WHOLE REGISTRY, not just the keepers.** All seven keepers hold
> **CALIBRATED**, and **all 47 registered runs score byte-identically** control vs arm — every
> criterion, every caveat, every determination. Zero cache keys move; zero solve-surface rows
> move.
>
> **WHAT IS NOT DONE, AND IT IS THE HANDOFF'S EXPECTED "BULK" (§5).** The committed bench parts
> are **not regenerated**, because they cannot be without a re-solve: the committed bundles are
> **slim** — `dispatch/` is gitignored and absent from every one of them — so the render the
> handoff assumed is cheap is not available. Regenerating all 34 parts would cost ~40
> shard-years of LP for a display number already measured to flip nothing. Each ISO's next
> registration refreshes its own parts automatically, and §5 publishes the exact number each
> will land on.
>
> **ESCALATED, NOT ABSORBED (§6):** `check_bench_freshness` **cannot see this change at all** —
> `run_calibration_full.py` is not in `bench_stamp.PAYLOAD_SOURCES` — so it reports
> `0 STALE` and *"bench part reproduces at HEAD"* for parts whose hydro row demonstrably does
> not. That is a **false green** on a reproducibility gate, and the obvious fix is a regression
> in the same shape the Y-17 finding already repaired. Owner's call, §6.

---

## 2. THE DECISIONS, ON STRUCTURE

The full structural argument is the PRECOMMIT §0 and is not repeated. In one line each:

* **Decision 1.** The LP's hydro units are EIA-923 prime mover `HY` **by construction** —
  `data.hydro._load_hydro_generation` filters `prime_mover == "HY"` **directly**, never through
  `classify_plant` — and a PS-folded BA's `NG: WAT` is conventional hydro **plus** pumped-storage
  gross discharge. Scoring one against the other is a unit mismatch. The predicate that says so,
  `eia930_wat_level_folded`, is already owner-adjudicated three times (miso-109, miso-110,
  neiso-72) and is reused rather than duplicated (rule 19 `[R-ONE-MECH]`). This is the BENCHMARK
  end of the repair pjm-143 landed on the MODEL end. Rule 14 `[R-ACCURATE]`.
* **Decision 2.** `classify_plant` contradicted its own comment. Rule 26 `[R-DELETE]`: fix it,
  do not flag it both ways.
* **UNCONDITIONAL, no `ScenarioConfig` field.** A flag makes the wrong construction re-armable
  (rule 26); the model side landed unconditionally; and a scenario knob over a *benchmark*
  construction has no scenario meaning while costing rules 24 and 28(c) duties for no gain.

**Zero new parameters, zero new registry entries, zero new constants, zero new
`ScenarioConfig` fields, zero new solve-surface names.**

---

## 3. DECISION 2's BLAST RADIUS — MEASURED, and the verdict on "solve-affecting"

**VERDICT: NOT solve-affecting. Benchmark-only.**

### 3.1 What actually moves

Over the whole EIA-923 record 2019-2026, **126,342 rows**:

| | |
|---|---|
| rows that change class | **366** |
| transitions observed | `hydro -> OTHER` : 366, and **nothing else** |
| prime movers among them | `PS`, and only `PS` |
| fuel codes among them | `WAT`, and only `WAT` |
| non-`PS` rows that move | **0** |
| `PS` rows that do NOT move | **0** |

So the repair is total and exactly scoped: every PS row moves, nothing else does.

### 3.2 Every call site, verified not assumed

The handoff listed six; grep finds more, including derive/curate scripts it did not name. All
are enumerated here. The question at each is the same: **does it distinguish `hydro` from
`OTHER`, and does it consume either?**

| # | call site | verdict | why — verified |
|---|---|---|---|
| 1 | `data/coal.py:312` | **INERT** | `WAT` is in `campd._NON_COMBUSTION_FUELS`, so WAT rows are dropped **before** the classifier is called; the frame is then further filtered to `_COAL_EIA_FUELS`, which excludes `WAT`. Inert twice over. |
| 2 | `data/chp.py:391` (`chp_class_netgen_mwh`) | **INERT** | Keyed `(plant_id, klass)` and read at `assembly.py:910` as `.get((plant_code, group))` inside the **gas-CHP** branch. A PS plant is loaded as LP storage (`load_eia860_pumped_storage`) and carries no thermal generator, so it never reaches the lookup; and moving a key from `(pid,'hydro')` to `(pid,'OTHER')` cannot create a hit on a gas-CHP `group`. |
| 3 | `data/fleet/eia860.py:1352` | **INERT** | **The handoff's read, confirmed.** It sits inside `elif fuel_type in ("gas_cc","gas_cc_ccs","gas_ct","gas_st")`, and `_map_fuel_type` returns **`None`** for `WAT` (hydro falls through to its final `return None`). A WAT plant never enters the branch. |
| 4 | `data/fleet/eia860.py:1613` | **INERT** | Guarded by `if source != "NG" or not switch.startswith("Y"): continue`. `WAT` never reaches the call. |
| 5 | `data/fleet/eia860.py:3218` (`_eia923_plant_class_totals`) | **LIVE, and the only one that matters** | Classifies every row. Its two consumers are measured in §3.3. |
| 6 | `data/fleet/eia860.py:3357` (`ct_mustrun_floor_mwh_by_plant`) | **INERT** | Filters `== "CT_PEAKER"`. A WAT/PS row is neither before nor after. |
| 7 | `scripts/run_calibration_full.py:281` (`_classify_f923`) | **LIVE — the benchmark**, which is the point of the change | |
| 8 | `scripts/data/curate_fleet.py:139` | derive-time | Produces a committed `data/clean/` artifact; not re-run here. See §3.4. |
| 9 | `scripts/data/derive_thermal_tranches.py:310` | derive-time | idem |
| 10 | `scripts/data/curate_chp_btm_share.py:118` | derive-time | idem |
| 11 | `scripts/data/derive_reliability_coeffs.py` | derive-time | idem |
| 12 | `scripts/data/derive_caiso_ct_reliability_floor.py:135` | derive-time | reads `eia923_dominant_class_by_plant`; §3.3 covers it |
| 13 | `scripts/data/derive_caiso_local_commitment.py:143` | derive-time | idem |

### 3.3 The one live model-side consumer, measured over 2019-2026

`_eia923_plant_class_totals` feeds exactly two things:

* **`eia923_dominant_class_by_plant` → `campd_bins._override_bin_class_from_eia923`** — this
  **is** on the solve path (the ERCOT per-plant bin class). Its guards are
  `curated in _GAS_BIN_GROUPS` and `derived in _GAS_BIN_GROUPS`.
* **`mixed_fossil_plants` → `apply_other_fossil_scoring`** — scoring only, and its guard is
  that the top TWO classes are both in `_GAS_THERMAL_SCORING_CLASSES`.

| year | plants | dominant-class flips | **flips touching a GAS class** | **`mixed_fossil_plants` delta** |
|---|---:|---:|---:|---:|
| 2019 | 9,981 | 30 | **0** | **0** |
| 2020 | 10,468 | 30 | **0** | **0** |
| 2021 | 11,091 | 30 | **0** | **0** |
| 2022 | 11,744 | 28 | **0** | **0** |
| 2023 | 12,308 | 29 | **0** | **0** |
| 2024 | 13,210 | 29 | **0** | **0** |
| 2025 | 3,427 | 28 | **0** | **0** |
| 2026 | 3,528 | 28 | **0** | **0** |
| **total** | | **232** | **0** | **0** |

Every one of the 232 flips is `hydro -> OTHER` on a pure pumped-storage plant. **None reaches a
gas class**, so `_override_bin_class_from_eia923` and `mixed_fossil_plants` are byte-identical.

### 3.4 The injected `OTHER` must-run — the one genuine SOLVE INPUT at risk (gate G2)

`_must_run_profiles` injects `OTHER` as must-run MW. Routing PS into `OTHER` would double-count
it against the LP's storage units — which is precisely what `_pumped_storage_plant_ids()` was
written to prevent, and which it has never actually done, because PS never reached `OTHER`.
**This repair makes that guard live for the first time.** The guard filters by **plant id**, not
by row, so it could in principle drop a non-PS `OTHER` unit co-located with a PS generator.

Measured:

* **over-filter rows — non-PS rows already in `OTHER` at a PS plant id: `0`**, in the entire
  EIA-923 record 2019-2026. The guard removes exactly the PS rows and nothing else.
* **injected `OTHER` class energy, before vs after, all 7 ISOs × 2020-2025 (42 cells):
  worst |delta| = `0.000000 MWh`.**

**G2 PASS.** The `OTHER` must-run injection, and therefore the LP, is unchanged.

### 3.5 Cache keys and the solve surface (gate G3)

`plant_taxonomy` **is** a member of `solve_surface.SURFACE_MODULES`, so this was checked rather
than assumed. The fingerprint hashes module-level **values** matching `^[A-Z][A-Z0-9_]*$`; a
function has no canonical image and is out of scope by construction (design §3). **No new
module-level name was added** — deliberately, so no `solve_surface_declared` entry is needed and
no CI check 5 duty arises. Measured:

* `check_cache_key_registration.py --base origin/main` → **clean** ("no new ScenarioConfig
  fields … 305 solve-surface names across 7 module(s), all declared").
* `moved_rows(iso)` is **byte-identical at `origin/main` and at the arm for all seven ISOs**.
  The two rows that do appear — `NUCLEAR_MONTHLY_CF_BY_YEAR` (ERCOT, CAISO) and
  `STATE_CARBON_PRICE_BY_ISO` (CAISO) — are **pre-existing and another lane's**.

**Nothing re-keyed. Every keeper's dispatch is byte-identical.**

### 3.6 The derive/curate scripts — stated, not hidden

Call sites 8-13 produce **committed, frozen** artifacts (rule 23 `[R-FROZEN-DERIVE]`). They are
not re-run here, so nothing they produced changes. What changes is that a **future** re-run of
them would bucket PS differently. Every one of them filters to fossil/gas/coal or to a dominant
gas class, so the §3.3 result ("no flip reaches a gas class") covers them by the same
measurement — but it is recorded here as a known property rather than left to be rediscovered.

---

## 4. THE EARLY-RELEASE VINTAGE — the design decision, and the cost it leaves

Full reasoning: the ADDENDUM. In brief: the PRECOMMIT's carry-forward fall-through **does not
fire**, because `_vintage_completeness` is ISO-wide (PJM 2025 **0.9233**, MISO **0.9230**, both
above the 0.90 threshold) while the hydro class itself is 26 % / 11 % filed. **All three
available scalars are measurably wrong for this class** — the ISO vintage ratio by construction;
the plant-census fraction in the other direction (PJM `2.2898 / 0.139 = 16.5 TWh` against a modal
~8.9); and an unscaled prior-year carry is not a scalar at all but a **climatology standing in
for a scored actual**, which tells a reader nothing about the year being scored.

**So the swap is refused only where a right-population measurement exists**: folded **AND** the
year's own EIA-923 `HY` census complete, using the already-adjudicated
`complete_923_hydro_years` (miso-109's "2025 trap", miso-110). Measured, it returns the right
verdict with no tuning — **complete 2020-2024 in all seven ISOs, incomplete 2025 in all seven**
(PJM files 10 of 72 hydro plants in 2025, MISO 14 of 160, NEISO 5 of 166, CAISO 26 of 160,
NYISO 3 of 147, SPP 1 of 22, ERCOT 1 of 12).

**THE COST, NOT ABSORBED: PJM 2025 and MISO 2025 keep the pumped-storage-contaminated actual.**
They are the only two cells in the matrix where the seam is diagnosed and left unrepaired (NEISO
2025 is past its `EIA930_PS_SPLIT_COMPLETE_FROM` year and is not folded; no other ISO is folded).
It is **self-healing**: when the final 2025 EIA-923 vintage lands the census fills, the predicate
flips, and the repair reaches both cells **with no code change and no re-adjudication**.

---

## 5. THE EFFECT — every ISO-year at full magnitude, regressions included

**The control is exact.** Re-deriving the benchmark at `origin/main` reproduces **every one of
the 34 committed `classFull.hydro` values to 4 dp**, so the hydro row carries **zero** pre-existing
drift and every delta below is attributable to this change alone.

| ISO | yr | committed | repaired | Δ TWh | what moved it |
|---|---:|---:|---:|---:|---|
| **PJM** | 2020 | 15.8943 | **9.9324** | **−5.9619** | swap refused → 923 `HY` |
| | 2021 | 16.6400 | **10.2909** | **−6.3491** | " |
| | 2022 | 15.9967 | **8.8854** | **−7.1113** | " |
| | 2023 | 15.4676 | **8.9763** | **−6.4913** | " |
| | 2024 | 15.8562 | **8.8612** | **−6.9950** | " |
| | 2025 | 15.5065 | 15.5065 | 0.0000 | **UNREPAIRED** — census 10/72 (§4) |
| **MISO** | 2020 | 11.6531 | **11.2658** | **−0.3873** | swap refused → 923 `HY` |
| | 2021 | 9.4564 | **10.1739** | **+0.7175** | swap never fired here; **pure PS-net removal** |
| | 2022 | 10.5977 | **9.2410** | **−1.3567** | swap refused → 923 `HY` |
| | 2023 | 9.9790 | **8.7887** | **−1.1903** | " |
| | 2024 | 10.7386 | **9.0414** | **−1.6972** | " |
| | 2025 | 9.8768 | 9.8768 | 0.0000 | **UNREPAIRED** — census 14/160 (§4) |
| **NEISO** | 2020 | 7.0566 | **6.6409** | **−0.4157** | swap refused → 923 `HY` |
| | 2021 | 6.6442 | **6.2031** | **−0.4411** | " |
| | 2022 | 7.1437 | **6.5427** | **−0.6010** | " |
| | 2023 | 8.1720 | **8.5469** | **+0.3749** | swap never fired; **pure PS-net removal** |
| | 2024 | 7.3942 | **6.7136** | **−0.6806** | swap refused → 923 `HY` |
| | 2025 | 5.1207 | 5.1207 | 0.0000 | post-split, **not folded** — correctly untouched |
| **NYISO** | 2022 | 26.9760 | **27.4267** | **+0.4507** | not folded; **decision 2 alone** |
| | 2023 | 28.0312 | **28.4033** | **+0.3721** | " |
| | 2024 | 27.4654 | **27.8750** | **+0.4096** | " |
| | 2025 | 24.1039 | 24.1039 | 0.0000 | swap fires (not folded) |
| **CAISO** | 2022 | 14.8359 | **13.4575** | **−1.3784** | **SOURCE FLIP — see below** |
| | 2023 | 23.3713 | **23.9003** | **+0.5290** | not folded; decision 2 alone |
| | 2024 | 21.3447 | **21.4837** | **+0.1390** | " |
| | 2025 | 21.3492 | 21.3492 | 0.0000 | swap fires |
| **SPP** | 2023 | 8.3472 | **8.4002** | **+0.0530** | not folded; decision 2 alone |
| | 2024 | 8.6543 | **8.7018** | **+0.0475** | " |
| | 2025 | 8.8299 | 8.8299 | 0.0000 | swap fires |
| **ERCOT** | 2021-2025 | — | — | **0.0000** | no PS fleet, never folded — neither half reaches ERCOT |

**THE ONE DEBATABLE CELL, FLAGGED FOR CAISO'S LANE RATHER THAN BURIED. CAISO 2022 is a SOURCE
flip, not a level change, and it is a side effect of decision 2 rather than an intended
outcome.** CAISO is not PS-folded, so my gate never fires there. What happens is that removing
the PS-net deflation lifts the 923 hydro total from **13.1631 to 13.4575**, and the **existing**
0.90× completeness threshold sits at `0.90 × 14.8359 = 13.3523`. The corrected total crosses it,
so the 930 swap stops firing and the year keeps its own 923 `HY`. That is the pre-existing
completeness rule acting on a corrected input — arguably right (923 is now genuinely ≥ 90 %
complete) but it moves that one year **off the grid-side authority this function prefers by
default**, on a 0.8 % margin. **CAISO's lane should look at it; I have not tuned the threshold
and will not.**

**Net direction, stated plainly:** PJM/MISO/NEISO move **down** onto the conventional-only
population their LP units are (the intended repair); NYISO/CAISO/SPP and the two
swap-never-fired cells (MISO 2021, NEISO 2023) move **up** by removing a PS-net deflation (the
same repair, opposite sign). Both directions are the same construction.

### 5.1 Gate G4 — every keeper, and then the whole registry

Re-scored from committed artifacts against bench parts carrying the repaired hydro actual.
`hydro` lives in exactly one place in a bench part (`bench.classFull.hydro`; it is absent from
`bench.e930`), and `reconcile_vintage_classes` scales **fossil** classes only — so this
reproduces exactly what a regenerated part would carry.

| ISO | keeper | before | after |
|---|---|---|---|
| CAISO | `2026-09-10-caiso-271-egrid-family` | **CALIBRATED** | **CALIBRATED** |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | **CALIBRATED** | **CALIBRATED** |
| MISO | `2026-09-09-miso-250-ep-gas` | **CALIBRATED** | **CALIBRATED** |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | **CALIBRATED** | **CALIBRATED** |
| NYISO | `2026-09-09-nyiso-221-fuelvintage-span` | **CALIBRATED** | **CALIBRATED** |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | **CALIBRATED** | **CALIBRATED** |
| SPP | `2026-09-10-spp-27-commitment-grain` | **CALIBRATED** | **CALIBRATED** |

The verdict objects diff **byte-identically** — every criterion, every caveat, every basis.

**And the nyiso-148 flipset check, over ALL 47 registered runs, not just the keepers:**
**0 differences.** `{CALIBRATED: 19, NOT-YET: 27, CALIBRATED-WITH-CAVEATS: 1}` before and after.

This confirms pjm-h1 §4 and extends it: `hydro` is not a C1 row, the 8 TWh cap binds either way,
and **the repair cannot be a residual fit because it moves no gate anywhere.**

---

## 6. WHAT IS **NOT** DONE, AND WHAT IS ESCALATED

### 6.1 The committed bench parts are NOT regenerated — and the reason is new information

The handoff budgeted this as "the deliverable's bulk", on the reasonable assumption that a bench
part is a render. **It is not, for these bundles.** `render_calibration_html.build_payload` reads
`<bundle>/dispatch/<year>_P1.parquet`, and **every committed bundle is slim**: `dispatch/` and
`system.parquet` are gitignored (`.gitignore:1918` and siblings) and absent from a fresh
checkout. `--rebuild-benchmark` itself works and is genuinely zero-LP (28 s on SPP; it
refreshes the EIA-923/930/CAMPD inputs and explicitly "no re-solve"), but the **render** that
writes the part cannot run without dispatch.

So regenerating all 34 parts means **re-solving 12 bundles ≈ 40 shard-years of LP**. Against a
change measured to move **no gate in any of 47 registered runs**, that was refused as a
disproportionate spend, and this is a governance session rather than a solve program.

**What happens instead, and why it is safe:** bench parts are shared per (ISO, year), and **every
new registration refreshes its own ISO-years automatically**. The registry shows each lane
registering runs every few days. §5 publishes the exact value each part will land on, and §5.1
has already scored it — **so when a lane's next registration moves its hydro actual by up to
7.1 TWh, that is this change, it is expected, and it flips nothing.** Handing that number over in
advance is the whole point of measuring it here; the alternative is a lane discovering an
unexplained 7 TWh move and reaching for the wrong root cause.

The `hydro_level_923_hy` cell in **all seven** mechanism-matrix shards carries this stamp
(rule 28 duty (b); a cross-ISO session is the exception the per-ISO rule exists to permit). **No
cell verdict moves** — no mechanism was tested.

### 6.2 ESCALATED: `check_bench_freshness` has a FALSE GREEN, and the obvious fix is a regression

`bench_stamp.PAYLOAD_SOURCES` is `(render_calibration_html.py, render_backcast.py,
backcast_artifacts.py)`. **`run_calibration_full.py` is not in it** — yet `classFull` is built
from `_benchmark_eia923_frame`, which lives there. So a benchmark-**construction** change does
not move the stamp at all. Measured at the arm:

```
bench freshness: 34 part(s) checked, 0 STALE, 0 on a superseded stamp …, 34 with engine drift
::warning …/bench/PJM/2023.json.gz::bench part reproduces at HEAD but 16 engine commit(s) …
```

The gate says PJM/2023 **"reproduces at HEAD"**. At HEAD its hydro is **8.9763**; the part says
**15.4676**. **That is a false green on the gate whose entire job is answering "would the builder
at HEAD produce the same numbers?"**

**I have not fixed it, and the reason is that the obvious fix is wrong.** Adding the whole
14,117-line `run_calibration_full.py` to `PAYLOAD_SOURCES` would re-stamp every part on every
edit to a file that lanes touch constantly — **exactly the degeneracy the Y-17 finding removed**
when it took `bench_stamp.py` out of the payload set ("unable to return *equal* for any part
built before such an edit even when its payload sources were byte-identical"). The right shape is
narrower — fingerprint the benchmark-construction functions rather than the file — and that is a
design change to a shared CI gate, with a cost every lane pays. **Owner's call. It is not
blocking anything today.**

### 6.3 Pre-existing gate REDs — reported, untouched

* **`check_registry_payload_parity`: 4 REDs, all pre-existing and all committed on
  `origin/main`** (verified with `git ls-tree`): `nyiso227_rebasis_span` (the known one, NYISO's
  lane) **plus three new ones the CAISO lane landed today**, `caiso275_B_gascoupling_{2023,2024,2025}`
  — per-year shard dirs left committed, the exact rule 32(d) / rule 29(c) Class-E case. **Not
  mine; not touched** (and rule 31 `[R-RETAIN]` forbids me reaching for `rm` on another lane's
  solved bundles).
* **`audit_keepers --iso CAISO`: FAIL (1 failure, 1 warning)** and **`build_status --iso CAISO
  --check`: exit 1**. Both reproduce **identically at `origin/main`** with my two files reverted
   — pre-existing, CAISO's lane's. The other six ISOs PASS. *(Note: the handoff expected CAISO's
  failure at `check_gate_a_provenance`; that gate now **passes**, "7 row(s) checked". CAISO's
  failure has moved to these two.)*
* **`check_mechanism_matrix --base origin/main`: exit 0** (warnings are pre-existing anchor
  drift). **`check_gate_a_provenance`: OK.**
* **`pytest tests/scoring`: 15 failures at the arm and 15 at `origin/main`, and the failure sets
  diff IDENTICALLY. Zero new failures.** The handoff's quoted baseline of 16 is stale; it is 15
  at `fb73c4f6`.

---

## 7. DECISION 3 — the rule 31 text-vs-code discrepancy: **RECOMMEND fixing the GATE, not the rule**

Rule 31 `[R-RETAIN]` states the parity gate *"only ever sees committed dirs, so an ignored bundle
can sit on local disk indefinitely without turning anything red."* At HEAD that is **false**:
`check_registry_payload_parity.py:437` sweeps `calib_root.iterdir()` — the working tree.
Confirmed again this session.

**RECOMMENDATION: option (a) — teach the sweep to skip gitignored dirs (`git check-ignore`).
Not option (b).** Four reasons:

1. **It makes the gate say what it means.** The gate's real question is *"is there a COMMITTED
   bundle dir with no retained sidecar?"* A gitignored dir is by construction not that, so
   skipping it removes a **false positive**, never a true one.
2. **It removes the incentive that caused the ercot-255 incident.** Rule 31 exists because a lane
   read a red gate and reached for `rm -rf`, destroying four solved bundles the owner then wanted
   promoted. Amending the prose leaves the red on the lane's screen and asks them to ignore it.
   **A rule that depends on every lane correctly ignoring a red gate will be broken again.**
3. **It makes local and CI behaviour identical**, which is the one property a gate must have. CI
   already skips these dirs (they are simply absent from the checkout). Option (b) *codifies* a
   local/CI divergence instead of removing it.
4. **It is small and fail-safe**: one batched `git check-ignore --stdin`, with a fallback to
   today's behaviour if git is unavailable — so it can only ever narrow the sweep, never widen it.

**NOT LANDED.** The handoff asked for a recommendation, and this changes a shared gate's
behaviour for every lane. It is a ~20-line change I can land on a word.

---

## 8. RULES

* **Rules 1 / 13 / 14** — decided on construction (two populations), never on a residual. The
  direction is fixed by `_load_hydro_generation`'s `HY` filter, which no result can select. The
  measured gate-neutrality across all 47 registered runs is what makes that checkable rather than
  merely asserted.
* **Rule 19 `[R-ONE-MECH]`** — one predicate at both ends of the comparison
  (`eia930_wat_level_folded`), and the vintage guard reuses the second already-adjudicated
  predicate (`complete_923_hydro_years`) rather than inventing a third.
* **Rule 21 / 24** — zero free parameters, zero registry entries, zero constants, zero
  `ScenarioConfig` fields, zero off-registry knobs.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the commit cites the construction repair and
  `EIA930_PS_FOLDED_INTO_WAT` / `EIA930_PS_SPLIT_COMPLETE_FROM`. No residual is cited and none
  was consulted in choosing the construction.
* **Rule 25 `[R-ISO-SCOPE]`** — one shared predicate applied identically; no ISO's number reaches
  another. This session is the cross-ISO exception the per-ISO lane convention exists to permit.
* **Rule 26 `[R-DELETE]`** — the classifier is fixed, not flagged both ways; and the dead
  `_pumped_storage_plant_ids` guard is made **live** with a docstring that now states when it
  became true, rather than left asserting behaviour the code lacked.
* **Rule 27 `[R-PUSH]`** — both edited files are ≥ 300 lines (14,117 and 348). Edited locally with
  the Edit tool; exact on-disk bytes pushed; blob verified after push (§9 of the session log).
* **Rule 28 `[R-MECH-MATRIX]`** — the `hydro_*` cells were read before anything was proposed; no
  verdict moves because no mechanism was tested; duty (b) discharged by stamping
  `hydro_level_923_hy` in all seven shards in this session.
* **Rule 30(c)** — no held-out-year result downgrades any ISO; no determination moved at all.
* **Rule 31 `[R-RETAIN]`** — **nothing was solved, so nothing is at risk of deletion**, and no
  other lane's bundles were removed (three CAISO parity REDs left in place deliberately, §6.3).
* **Rule 32 `[R-SHARD]`** — the parent never solved and launched no shard. `--rebuild-benchmark`
  is zero-LP by construction and was exercised once (SPP, 28 s) purely to establish §6.1's
  finding; its bundle mutation was reverted.
