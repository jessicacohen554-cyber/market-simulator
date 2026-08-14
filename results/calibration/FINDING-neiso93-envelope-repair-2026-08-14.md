# FINDING — neiso-93 envelope repair: closing the four 2021-readiness data gaps

**Session:** neiso-93 (verified free against `docs/calibration-log/neiso.md`, whose neiso-92
entry names `neiso-93` as the next shorthand, and against the run registry).
**Date:** 2026-08-14 · **Branch:** `claude/neiso-envelope-repair-8k0ptq`
**Spec:** `results/calibration/ASSESSMENT-neiso92-2021-readiness-2026-08-13.md` §5.
**Scope:** data prep across 2019–2025 + an IN-SAMPLE (2023–2025) keeper re-solve.

---

## Gate state, verified at HEAD (not inferred)

| Gate | State |
|---|---|
| Holdout spend **freeze** (`frontend/data/backcast/holdout-freeze.json`) | **ACTIVE** — `active: true`, declared 2026-07-25, re-armed 2026-08-06. **Untouched by this session.** |
| Years solved / scored / registered | **2023, 2024, 2025 only** — in-sample, always permitted, no lift and no marker needed. |
| 2019 / 2020 / 2021 / 2022 / H1-2026 | **NOT solved, NOT scored, NOT registered.** Data was prepared for them; nothing was run. |
| `calibration-complete.json` `final` block, locked-test artifacts | **Untouched.** |

No lift was requested and none was needed: rule 22 as amended 2026-08-06 — *"what is held out is
the SCORE, never the DATA … Data intake needs NO per-ISO/per-window authorization and no marker."*

**Rule 23 [R-FROZEN-DERIVE] citation for all four re-derivations:** each is triggered by a
**SOURCE-COVERAGE change** — years the extract never covered — never by a residual. **Nothing in
this session was tuned to any year's fit, and no parameter was identified against 2019–2022 at
any point.**

---

## 1. Summary — all four gaps CLOSED

| # | Gap | Reproduce-check on the years it already owned | Outcome |
|---|---|---|---|
| 1 | Nuclear availability (anchor **and** NRC overlay) | **PASS** ×2 — anchor `--check` "committed table matches"; overlay `--check` "reproduces **byte-for-byte**" | **CLOSED** 2019–2025 |
| 2 | Interchange seam tranches | **PASS** ×3 — route, extract, and deriver (one disclosed 1-cent item) | **CLOSED** 2019–2025 |
| 3 | EIA-860 CHP by vintage | **PASS** — 2023/2024 reproduce plant-for-plant and flag-for-flag | **CLOSED** 2018–2025 |
| 4 | Parasitic load factors | **N/A — the file held no NEISO rows to reproduce** (see §5) | **CLOSED** 2019–2025 |

Two blockers the spec expected to stop gap 2 were both cleared, and one spec premise was
corrected (§5). Nothing was papered over.

---

## 2. Gap 1 — nuclear availability (the blocker)

**Reproduce, then extend.** Both producers were re-run over their committed span first:

- `derive_nuclear_monthly_cf.py --isos NEISO --years 2023 2024 2025 --check`
  → `# --check: committed table matches the EIA-923 derivation`
- `derive_nuclear_availability.py --iso NEISO --check`
  → `OK: nuclear-availability-NEISO.csv reproduces byte-for-byte`

Only then were new years minted.

**What changed.** The anchor `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` gains 2019–2022 (LEVEL, EIA-923);
the NRC daily per-reactor overlay `data/raw/nuclear-availability-NEISO.csv` goes **3,288 → 7,670
rows** (TIMING — 365/366 days × 3 reactors per year), every month reconciling to the anchor. The
committed 2023–2025 rows were verified **byte-identical after the rewrite** (the old 3,289-line file
diffs clean against the new file's 2023–2025 span).

**Derived anchor:**

| year | Jan–Dec monthly CF | mean |
|---|---|---|
| 2019 | 1.00 1.00 0.99 0.69 0.79 0.99 0.99 0.99 0.99 0.99 0.99 0.90 | 0.943 |
| 2020 | 0.99 1.00 0.99 **0.43** 0.71 0.87 0.99 0.98 0.99 **0.64** 0.84 0.98 | 0.868 |
| 2021 | 0.93 1.00 1.00 1.00 1.00 0.89 0.99 0.98 0.99 **0.43** 0.86 1.00 | 0.922 |
| 2022 | 0.94 1.00 0.99 **0.70** **0.63** 0.95 0.99 0.99 0.99 1.00 1.00 1.00 | 0.932 |

Against the static climatology it replaces (mean 0.982), this is the phantom nuclear the neiso-92
assessment sized: **+0.96 TWh in 2021** (+1.25 TWh in October alone), **+0.61 TWh in 2022**,
**+2.51 TWh in 2020**.

### EIA-930 cross-validation (the check the prompt required)

`scripts/probes/_neiso93_nuclear_crossval.py` reconstructs monthly nuclear CF from **EIA-930 ISNE
`NUC` hourly telemetry** — a collection independent of the EIA-923 the anchor is built from — over
the same model fleet pmax (3,355.4 MW; Millstone 566 = 2,108.4 MW + Seabrook 6115 = 1,247.0 MW).

| year | \|mean CF diff\| 923 vs 930 |
|---|---|
| **2020** | **0.002** |
| **2021** | **0.003** |
| **2022** | **0.001** |
| 2023 (committed) | 0.001 |
| 2024 (committed) | 0.004 |
| 2025 (committed) | 0.007 |

**The new years corroborate at least as tightly as the committed ones.** All three expected
refuelling windows appear, each traced to a single reactor going to ~0 in the per-plant series:

- **2021 Oct 0.43** (EIA-930: **0.426**) — **Seabrook**, plant CF 0.03. Visible in the daily
  extract as full power Oct 1 → **0.0 from Oct 7 through Oct 31** → 0.48 on Nov 6 → full by Nov 12.
  A five-week refuelling outage the static climatology was covering at CF ≈ 0.92.
- **2020 Apr 0.43** (930: 0.430) — Seabrook, plant CF 0.06.
- **2022 Apr/May 0.70 / 0.63** (930: 0.705 / 0.631) — a Millstone unit, 0.53 / 0.41.

**Consumer verified.** `outages.nuclear_unit_availability_series` now returns 3 real reactor series
× 8760 h for 2019–2022 (it returned `{}` before, and `data/fleet/arrays.py` fell through to the
climatology **silently**). Fleet-mean availability tracks the anchor: 2019 0.9442, 2020 0.8675,
2021 0.9201, 2022 0.9360.

### Two corrections to the committed comment block

1. **Pilgrim's EIA plant code was wrong.** `constants.py` cited **6098**; that is *Big Stone*, a
   South Dakota coal plant which generates in every year 2018–2025. Pilgrim Nuclear Power Station
   is **EIA 1590** (EIA-923 `plant_name`, last generation year 2019). Comment-only — no computation
   depended on it.
2. **2019 carries a fleet-vintage caveat, now measured rather than asserted.** Pilgrim ran
   **Jan–May 2019 for 2.177 TWh** before retiring 31 May 2019 and is absent from the EIA-860
   operable snapshot the model fleet is built from. The EIA-930 cross-check exposes this directly:
   Jan–May 2019 telemetry implies a **fleet CF of 1.18–1.20** — impossible for 3,355 MW — and the
   923-vs-930 gap collapses to 0.003–0.005 from **June onward, exactly when Pilgrim stops**. **A
   2019 solve is short ~2.18 TWh of nuclear regardless of this overlay.** 2020–2022 are unaffected.
   This is the direct analogue of the NYISO block's Indian Point caveat.

---

## 3. Gap 2 — interchange seam tranches (both blockers cleared)

The spec flagged one blocking fetch; there were **two**, and the second was not in the assessment
(hence deliverable 6, the one-line patch to it):

| input | committed span | blocker found |
|---|---|---|
| EIA-930 ISNE interchange | 2023–2025 | documented fetch route needs an `EIA_API_KEY` **this environment does not have** |
| NYISO proxy-bus DA LBMP | 2023–2025 | its producer's source zips (`*damlbmp_zone_csv.zip`) **are not in the repo at all** |
| ISO-NE DA hub LMP | 2018–2025 | none |

**Both were cleared without inventing anything.**

**(a) NYISO proxy.** `data/raw/lmp-data/README.md` line 14 documents those zips as *"gitignored —
regenerable"*, fetched from NYISO MIS by curl. `mis.nyiso.com` is reachable here, so **84/84 monthly
archives (2019–2025) were fetched, 0 failures**, the zips left untracked per that README, and only
the derived parquet committed. **Reproduce-check: rebuilding 2023–2025 reproduced the committed
parquet EXACTLY** (52,560 rows, exact frame equality, dtypes matched) before any widening. Now
122,640 rows = 7 × 8760 × 2 hubs, every year dense at 8760/8760 per hub, 0 nulls, and the extended
file's 2023–2025 slice re-verified identical.

**(b) EIA-930 interchange — the keyless route.** `api.eia.gov` *is* reachable (its 403 is a genuine
`API_KEY_INVALID` response, not a proxy block), but no key exists in this environment: `.env` is
untracked and absent, and registering one would mean creating an account on the owner's behalf.
Rather than stop, this session added a **second, keyless source** to `fetch_eia930_interchange.py`
(`--source bulk`): EIA's *Hourly Electric Grid Monitor* six-month bulk CSVs, **the same archive
family `fetch_eia930_bulk_long.py` already uses** for the BALANCE product. Rows are filtered to the
BA while streaming, so the 100 MB+ CSVs never land on disk.

**Reproduce-check at all three levels:**

1. **Route** — bulk vs the committed API-sourced extract over 2023–2025: **78,927 rows compared,
   mean interchange identical to full float32 precision (−425.92047119140625 both sides)**. The only
   18 non-identical rows are the DST fall-back hour, where the two ambiguous repeated rows appear in
   opposite **order** with identical values as a set — the artifact the script's own `--merge`
   docstring already anticipates. The routes are equivalent.
2. **Extract** — widened via `--merge`, which keeps every committed `(local_time, diba)` row.
   Verified after the fact: **all 78,912 pre-existing rows compare exactly equal**; file goes
   78,912 → **184,104 rows**, 2019-01-01…2026-01-01, 0 nulls.
3. **Deriver** — re-run over its committed span, reproducing the 2023–2025 ladders rung-for-rung.

**The year texture the pooled curve was erasing is large and physical.** Mean measured HQT import:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| HQT mean MW (neg = ISNE importing) | −1,576 | −1,559 | −1,532 | −1,541 | −1,204 | −694 | −315 |
| NYISO_HQ anchor $/MWh | 19.07 | 14.22 | 25.72 | 49.20 | 24.57 | 33.10 | 55.99 |

HQ delivered roughly **five times** as much in 2019 as in 2025 while its measured opportunity cost
roughly tripled. Accordingly the early years' `HQ_PhaseII` rungs price **below** their anchor
(−$3.2 / −$1.0 / −$5.5 / −$8.6) where 2025's prices **+$51.9 above** it. Pooling 2023–25 onto 2021
would have mispriced the single largest seam on the system. 2019–2022 carry no `import_scarcity`
rung and no `export_HQ` sink — both omitted by the deriver's own depth tests, not by hand.

**One 1-cent correction, disclosed.** 2025 `NYISO_CT_base` was committed as **44.48** on 2026-07-06;
the deriver emits **44.47** and always has — confirmed by re-running it against the **pre-session**
committed inputs, which also give 44.47. It is a hand-transcription slip in the original paste-in,
**not** an effect of this widening. Set to the producer's own output so the whole block re-derives
exactly. 195 interchange/tranche tests pass.

---

## 4. Gap 3 — EIA-860 CHP by vintage

`build_eia860_chp_by_year.py` reads the EIA-860 release **zips**, and **this clone carries no zips at
all** — so the builder could not run and the committed file could not even be reproduce-checked.
Added a vintage-dir source: `data/raw/eia-860/vintage_<year>/eia860_generator_operable.parquet` is
the *same* Operable generator sheet already extracted, carrying the same
`Associated with Combined Heat and Power System` column, so the identical per-plant "any unit flagged
CHP" rule applies. Zip years win where both exist.

**Reproduce-check: the vintage route reproduces every committed year EXACTLY** — 2023 at 12,477 rows
and 2024 at 13,371, plant-for-plant and flag-for-flag. The 2025 row comes from an early release no
clone carries, so `build()` now **preserves** any committed year it has no source for rather than
silently dropping it (verified still identical at 14,189 rows). File: 40,037 → 92,633 rows,
2018–2025.

**Measured materiality for NEISO:** exactly **one** NEISO fleet plant is classified differently by
the 2019/2020/2021/2022 vintage than by the 2025 vintage (of 177/183/188/195 carrying rows), and
zero for 2023/2024. Low — as the assessment predicted — but now measured, and the anachronism is
gone.

2018 is produced as a byproduct of the vintage dirs on disk. It is **out of** the 2019–2025 working
span and **grants nothing** (2018 stays unsolvable, locked-test tier); it is kept rather than
hand-pruned so the builder's output stays a deterministic function of its sources.

---

## 5. Gap 4 — parasitic load factors — **the spec was wrong, and the gap is bigger**

The assessment recorded this as *"NEISO carries 2022–2025 rows but no 2021"*, citing NEISO rows
`{0: 463, 2022: 564, 2023: 428, 2024: 453, 2025: 205}`.

**Those are the file's TOTAL rows by year, not NEISO's** — they sum to exactly its 2,113 rows.
Measured this session by plant-id intersection against each ISO's CAMPD plant set:

| ISO | CAMPD plants (2023) | overlap with the committed file |
|---|---|---|
| ERCOT | 130 | **130** |
| PJM | 411 | **410** |
| MISO | 485 | **280** |
| NYISO | 106 | **27** |
| **NEISO** | **71** | **0** |
| CAISO | 110 | 0 |

**NEISO had ZERO rows in ANY year — the tuned years 2023–2025 included.** Every NEISO plant was
falling back to the class default, always. So there was nothing to reproduce-check, and fixing only
2019–2021 would have left NEISO *inconsistent across the span* — precisely the disease this session
exists to cure. Per rule 22's consistency clause and rule 14 [R-ACCURATE], the derive covers
**2019–2025 in one pass**.

NEISO now carries 71 plants × 2019–2023, 67 in 2024, 66 in 2025, plus the pooled year-0 fallback;
**41.9 %** of its rows are `measured` (the rest `class_default` where EIA-923 net is unavailable).

**This moves the TUNED years for NEISO**, so Phase B's in-sample re-solve measures it. That is the
intended sequencing (rule 22's touchpoint loop, step 3), not a side effect.

**A destructive-write hazard found and fixed.** `derive_parasitic_load.py` rewrites the whole output
with only the requested states/years, and that output is **shared across ISOs** — so a scoped NEISO
back-fill would have **silently deleted every ERCOT/PJM/MISO/NYISO row** (rule 25). Added `--merge`:
every committed `(plant_id, year)` row is kept, only absent plant-years are added, and the freshly
computed pooled `year == 0` row is kept **only** for plants the file does not already carry one for
— so no already-committed default moves on the strength of a narrower year set. **Verified: all
2,113 previously-committed rows present and byte-identical across every column** (2,113 → 2,712).

---

## 6. What this session did NOT do

- **No out-of-training year was solved, scored or registered** — not 2019, 2020, 2021, 2022 or
  H1-2026. Data was prepared for them; the spend was not made.
- **The freeze was not lifted, modified, or requested to be lifted.** It remains ACTIVE as found.
- **`calibration-complete.json`'s `final` block and every locked-test artifact are untouched.**
- **No parameter was tuned and nothing was fitted to any year's residual.**
- **No mechanism was tested**, so no mechanism-matrix cell verdict was minted (rule 28d) —
  extending a data extract is not a mechanism test. Only the `nuclear_unit_availability` coverage
  caveat was refreshed.

---

## 7. Artifacts

| Path | What |
|---|---|
| `src/market_sim/config/constants.py` | `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` 2019–2022 + corrected Pilgrim code + measured 2019 fleet-vintage caveat |
| `data/raw/nuclear-availability-NEISO.csv` | NRC per-reactor daily overlay, 3,288 → 7,670 rows |
| `src/market_sim/model/interchange/spec.py` | `IMPORT_/EXPORT_TRANCHES_BY_YEAR['NEISO']` 2019–2025 |
| `scripts/data/fetch_eia930_interchange.py` | new keyless `--source bulk` route |
| `data/raw/eia-930-interchange/ISNE interchange hourly.parquet` | 78,912 → 184,104 rows |
| `data/raw/_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet` | 52,560 → 122,640 rows |
| `scripts/data/build_eia860_chp_by_year.py` | vintage-dir source + committed-year preservation |
| `data/raw/_processed-legacy/eia860_chp_by_year.parquet` | 40,037 → 92,633 rows |
| `scripts/data/derive_parasitic_load.py` | new `--merge` back-fill (prevents cross-ISO wipe) |
| `data/raw/_processed-legacy/parasitic_load_factors.{parquet,csv}` | 2,113 → 2,712 rows; NEISO added |
| `scripts/probes/_neiso93_nuclear_crossval.py` + `results/calibration/_neiso93_nuclear_crossval.json` | EIA-930 cross-validation |

**Prior art:** `ASSESSMENT-neiso92-2021-readiness-2026-08-13.md` (the spec),
`FINDING-neiso85-2022-seasonal-inversion-2026-08-05.md` (the precedent this gate prevents
repeating), `FINDING-neiso86-gas-basis-intake-2026-08-06.md`.

---

## 8. Phase B — in-sample re-solve on the corrected envelope

See §9 below (appended when the solve completed). Phase B replays the designated keeper recipe
`2026-08-06-neiso-87-control` (bundle `results/calibration/neiso87_control_A`) with **zero scenario
deltas**, via `scripts/replay_keeper.py` — which reads the keeper's own `meta.json` kwargs snapshot,
so the recipe is reproduced from the committed artifact rather than retyped. The only things that
differ are the corrected measured inputs above, plus the keeper's **disclosed defect (i)**: it was
solved on the stale `NEISO,2025,8` gas-basis row (+0.04) while HEAD carries the measured −0.38.

---

## 9. Phase B — result

**Run `2026-08-14-neiso-93-envelope`**, bundle `results/calibration/neiso93_envelope_A`, years
**2023 2024 2025 in ONE invocation**, sequential (rules 12 / 16 [R-ALLYEARS]). Registered on the
backcast dashboard with its hourly sidecars incl. `reserve_family_<year>.parquet` (rule 15).

### Determination: **CALIBRATED-WITH-CAVEATS — criterion for criterion IDENTICAL to the incumbent**

| criterion | tier | incumbent | neiso-93 |
|---|---|---|---|
| C1 fuel-mix by class | load-bearing | PASS | **PASS** |
| C2 system volume | load-bearing | PASS | **PASS** |
| C3a mean LMP | load-bearing | PASS | **PASS** |
| C3b price duration/shape | load-bearing | PASS | **PASS** |
| C3c price tail / scarcity | supporting | CAVEAT (ledgered) | **CAVEAT (ledgered)** |
| C4 fleet hourly dispatch corr | supporting | PASS | **PASS** |
| C6 governance gate | protective | PASS | **PASS** |
| C8 forced-energy share | protective | PASS | **PASS** |

**0 FAILs. D-10: C1 all 12/12 · free 8/8.** C3c remains the **sole** ledgered caveat, carried
forward unchanged in substance. The rule 22 D-5(b) worse-determination stop **does not fire**.

### Price effect — the incumbent's disclosed defect (i) is closed

| year | incumbent mean λ | neiso-93 | Δ |
|---|---|---|---|
| 2023 | 38.4613 | 38.4502 | −0.011 |
| 2024 | 43.7026 | 43.7025 | ~0 (essentially bit-identical) |
| **2025** | **69.7337** | **69.4178** | **−0.316** |

The 2025 move is the Aug-2025 gas-basis repair (stale `+0.04` interpolation → HEAD's measured
`−0.38`), the direction and magnitude the prompt predicted. **That 2024 barely moves and 2023 moves
a cent is the expected signature and worth stating explicitly:** the nuclear *anchor* is unchanged in
the tuned years — only the per-reactor **timing** overlay and gaps 3/4 can move them there — so the
in-sample sensitivity to this session's work is genuinely small, while the out-of-training years
(which were falling through to a climatology worth up to **+2.51 TWh** of phantom nuclear) are where
the repair actually bites. **Gap 4 is the one change that materially touches the tuned years**, since
NEISO had no parasitic-load rows in any year.

### Two things that needed doing and are disclosed rather than buried

1. **C6 needed an attestation the replay path does not emit.** The first scoring run returned
   `NOT-YET — governance gate UNATTESTED: no governance attestation in bundle`, i.e. a **missing
   artifact, not a substantive regression**. `build_dof_ledger.py` wrote `free_parameters` (7
   entries) and the `governance` / `disclosures` / `exceptions` sections were written for this run —
   the governance flags attested to this session's actual conduct, the C3c exception carried forward
   from the incumbent, and the disclosures recording every item in this document that cuts against
   the result.
2. **The raw D-1/D-2 diagnostics report gate FAILs on COAL_BIT / ST_GAS / CT_PEAKER.** These are
   **below the rule 20 [R-FORCED-BUDGET] 2 %-of-load materiality floor** in every year (COAL
   0.2–0.3 %, ST_GAS 0.1–0.3 %, CT_PEAKER 0.5–1.5 %) and the scorer skips them as immaterial, which
   is why C8 passes. Reported here so the raw FAIL in the bundle's own artifact is not mistaken for
   a gated failure.

### Promotion

Promoted to NEISO keeper. `frontend/data/backcast/keepers/NEISO.json` edited (NEISO only, rule 25),
status rebuilt via `build_status.py --iso NEISO`, and `calibration-complete.json`'s NEISO entry
**re-keyed with a determination RE-VERIFICATION on committed artifacts only** (rule 22 D-5(b), no
solve). `keeper_at_declaration` preserved; **tier authorization unchanged (validation only)** — this
grants, spends and re-arms nothing. `audit_keepers.py --iso NEISO`: **0 failures, 0 warnings**.

### What this does NOT do

**2021 is still not solved, and that is correct.** This session made it solvable. Spending it needs
its own owner lift. And **2019 is now further from ready than the anchor extension alone suggests** —
see §2's Pilgrim caveat, which is a fleet-vintage limitation this session did not fix.
