# CHARTER — the backcast fleet-vintage retiree window (`RETIREMENT_WINDOW_START`)

**Opened:** 2026-08-15, session neiso-94 · **Scope:** ALL SIX ISOs · **Status:** TASK 2 EXECUTED 2026-09-09 (session xiso-fuelvintage-1, commit `7934e92c`); tasks 1, 3, 4 OPEN, routed per ISO by `docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md`
**Evidence:** `results/calibration/ASSESSMENT-neiso94-final-readiness-2026-08-15.md` §2 ·
`results/calibration/_neiso94_pilgrim_vintage_audit.json` ·
`scripts/probes/neiso94_pilgrim_vintage_audit.py`
**Not a NEISO lane item.** It was *surfaced* by NEISO (Pilgrim, 2019) but the defect, the fix and
the risk are ISO-agnostic, which is why it is chartered rather than patched (rule 25
`[R-ISO-SCOPE]`, rule 24 `[R-REGISTRY]`).

---

## 1. The defect, in one sentence

**The backcast fleet is a static `status == "OP"` EIA-860 snapshot, so every generator that
retired between a modelled year and the snapshot's vintage is silently absent from that year —
and the one mechanism built to fix this is hard-cut at 2023, four years inside the program's
2019–2025 working span.**

## 2. Why the existing machinery is right and only the window is wrong

Three components already ship, are correct, and need **no change**:

| component | file:line | what it does |
|---|---|---|
| the monthly online mask | `src/market_sim/data/cod_ramp.py:326-357` | `retirement_year == run_year` → online through `retirement_month`; `retirement_year < run_year` → all-`False`. Mid-year retirement is fully expressed. |
| the mask application | `src/market_sim/data/fleet/arrays.py:3091-3157` | `availability *= ramp`, `min_gen *= ramp`; `pmax` untouched. Backcast-only, `cod_ramp_enabled` default `True`. |
| the retiree injection path | `scripts/data/process_eia860.py:248+` → `eia860_generator_retired_within_window.parquet` → `data/fleet/eia860.py:1826-1891` → `runner.py:1208-1212` (backcast-only) | Re-admits whole-plant exits the current operable snapshot no longer carries, writing the actual retirement into `planned_retirement_*` so the single COD mechanism ages them out. Built for Mystic (plant 1588, ~1.4 GW CC, retired mid-2024) — the identical shape of problem. |

**The single blocker** — `scripts/data/process_eia860.py:74`:

```python
RETIREMENT_WINDOW_START: int = 2023
```

applied at line 323 (`df = df[df["planned_retirement_year"] >= cutoff_year]`). The shipped
artifact holds **477 rows / 141 plants / retirement years 2023–2024 only / zero nuclear**.

Its own comment states the intent correctly — *"First backcast year the within-window retiree
snapshot supports … Bump only if the supported window moves."* **The supported window has moved.**
Rule 22 as amended 2026-08-06 makes the program's working span **2019–2025 for all ISOs**. The
constant is stale relative to the policy; nothing else about the design is wrong.

## 2a. TASK 2 EXECUTION RECORD (2026-09-09, session xiso-fuelvintage-1)

`RETIREMENT_WINDOW_START: 2023 -> 2019` and the artifact rebuilt, commit `7934e92c`. **Two
things §3 did not anticipate**, both measured and both handled:

1. **The source zips are gone.** `build_within_window_retirees` read release zips;
   `data/raw/eia-860/` commits their *extracted parquet vintages* instead. The reader is now
   source-agnostic (`_read_retired_sheets`) and the per-vintage projection is factored out.
2. **A bare rebuild would have DROPPED 161 real units, not added any.** EIA prunes older
   retirements from each release, so the vintages that supplied the shipped 2023/2024 rows can
   no longer reproduce them: rebuilding from what is on disk gives **423** rows against the
   shipped **477** (-111 of 2023, -50 of 2024). The new `preserve` argument carries the shipped
   rows verbatim; `until_year` bounds newly-read rows from above so the widening touches only
   the years it widens *into*.

**Verified additive**: the 477 shipped rows are content-identical after the rebuild (sha256
`b1f1a953…`), pinned as a STOP condition by `tests/unit/data/test_retiree_window_extension.py`.
Artifact 477 -> 1,094 units / 436 plants / 52.8 GW. Capacity restored per solve year (net
summer MW): **2019 31,919 · 2020 20,735 · 2021 12,945 · 2022 7,685 · 2023-2025 exactly 0**.
Per ISO 2019-2022: PJM 13,294.9 · MISO 9,127.8 · NYISO 3,671.9 · NEISO 1,696.5 ·
CAISO 1,700.6 · SPP 1,277.9 · ERCOT 1,149.7.

**Task 3 (in-sample bit-identity) is NOT discharged by this session** — it needs an LP per ISO
and is carried in each ISO's handoff prompt. **Task 4** (retiring the two `constants.py`
caveats) likewise stays in NEISO's and NYISO's own lanes, per rule 25.

**Task 5 is superseded by events, not by this session**: the validation tier (2020-2022) was
lifted from the holdout freeze by the owner ruling of 2026-08-26 and is governed by the
`complete` marker + `--holdout-authorized`, which ERCOT, NEISO, PJM, CAISO and NYISO hold and
**MISO does not**. 2019 remains locked-test tier with `final` empty and the freeze ACTIVE.

## 3. What the change is

**One constant, one artifact rebuild.** `RETIREMENT_WINDOW_START: 2023 → 2019`, then re-run
`scripts/data/process_eia860.py` to regenerate `eia860_generator_retired_within_window.parquet`.

- **Zero new mechanisms. Zero new free parameters. No `ScenarioConfig` field** (so rule 28
  `[R-MECH-MATRIX]` duty (c) is not engaged — but see §7).
- **Rule 23 `[R-FROZEN-DERIVE]` basis: SOURCE COVERAGE, not a residual response.** The window
  moves because the supported backcast span moved by owner amendment. **The cutoff must never be
  chosen, or later adjusted, to improve any year's fit** — 2019 is the program's floor, so 2019 is
  the value. A future session that proposes a different cutoff must cite a span change, not a
  score.
- **Rule 14 `[R-ACCURATE]` basis:** real machines that really generated are currently represented
  by nothing. If closing the gap makes any backcast *worse*, that is a discovered bug elsewhere to
  be root-caused — **not** grounds to restore the cutoff.

## 4. Blast radius — measured, not estimated

Replicating `build_within_window_retirees`' own filters (BA-mapped to a modelled ISO; whole-plant
exits only, i.e. absent from the operable snapshot; latest vintage record per plant) at a 2019
cutoff:

| ISO | plants added | MW added | notable |
|---|---|---|---|
| PJM | 83 | 8,125.4 | |
| MISO | 83 | 6,682.6 | |
| **NYISO** | **15** | **3,417.6** | **Indian Point 2 (2497, 2020-04, 1,299 MW), Indian Point 3 (8907, 2021-04, 1,012 MW), 6082 (2020-03, 655 MW)** |
| CAISO | 49 | 1,361.7 | |
| ERCOT | 13 | 966.0 | |
| **NEISO** | **21** | **914.2** | **Pilgrim (1590, 2019-05, 670 MW) = 73 % of the ISO total; all 20 others ≤ 45 MW** |
| **TOTAL** | **264** | **21,467.5** | |

**Two standing model caveats are closed by this one change**, both currently written into
`src/market_sim/config/constants.py` as permanent limitations:

- `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` (`constants.py:2170-2180`) — *"A 2019 solve is short
  ~2.18 TWh of nuclear regardless of this overlay."*
- `NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']` (`constants.py:2111-2118`) — *"A 2018-2021 solve is short
  that capacity regardless of this overlay."*

Both say the same thing: the CF overlays are **intensive** (fractions applied to units already in
the fleet) and cannot restore missing capacity. Fleet membership is owned by the loader plus the
COD ramp, which is exactly what this charter fixes.

**Sizing the NEISO instance** (the only one measured so far — see §5, task 1): integrating the
committed per-reactor nuclear overlay against the model fleet's pmax and comparing to independent
EIA-930 telemetry gives a gap of **−2.123 TWh in 2019** against **±0.15 TWh in every year
2020–2025**, concentrated as a **−390 to −670 MW step in Jan–May that vanishes to ±15 MW from
June** — Pilgrim's retirement month. Against NEISO 2019's C1 fuel-mix volume band of ±2.366 TWh,
that single defect is **91 % of the whole error budget**.

## 5. Work plan

**Task 1 — quantify, per ISO, before changing anything.** Run the neiso-94 envelope self-test
(overlay- or capacity-implied generation vs EIA-930 telemetry) for each ISO across 2019–2025 to
size each ISO's own gap and identify which years are material. NEISO is done; the other five are
not. This is unrestricted data inspection (rule 22) and needs no marker and no freeze lift.

**Task 2 — the change.** Lower the constant, rebuild the artifact, commit both. Report the new
row/plant counts per ISO.

**Task 3 — THE GATE: prove in-sample bit-identity, all six ISOs, 2023–2025.** This is the
load-bearing verification and the reason this is a charter rather than a patch.

*The expectation:* every one of the 264 added plants retired **before 2023**, so
`monthly_online_mask` returns all-`False` for 2023, 2024 and 2025 and their availability is
identically zero. Dispatch **should** be bit-identical.

*Why it must be proven anyway:* the ramp deliberately does not touch `pmax`, so the added units
still enter `FleetArrays`. Everything downstream that reads capacity rather than availability can
move — fleet capacity totals, per-class denominators and shares, CAMPD per-plant binning and
tranche construction, `_join_egrid_heat_rate` (a long-retired plant may carry no eGRID rate), the
plant-group/outage crosswalks, and the LP column count. Any of these can perturb a solve even at
zero availability.

*The gate:* an A/B on **2023–2025 for every ISO**, control = HEAD, arm = the rebuilt artifact,
passing iff **max |class-hour delta| = 0.000000 MW in all three years for all six ISOs**. A
non-zero delta is not a small problem to be waved through — it means capacity-denominated code is
reading retired units, and it must be root-caused before the change lands. Follow rule 12
`[R-PARALLEL]`: separate per-ISO invocations concurrently (cap ~2 for per-plant multi-zone LPs),
years sequential within each.

**Task 4 — retire the two constants caveats** (§4) once tasks 2–3 pass, replacing them with a
pointer to this charter's outcome. **Each in its own ISO's lane** (rule 25): NEISO's edit belongs
to a NEISO session, NYISO's to a NYISO session.

**Task 5 — out-of-training years remain untouched.** Closing this gap changes the availability
envelope for 2019–2022, so any already-spent validation touchpoint measured on the *old* envelope
(NEISO's 2022, PJM's 2022) becomes re-spendable evidence under rule 22's touchpoint loop. **This
charter neither requests nor implies a freeze lift.** Lifting is an owner action; nothing here
solves, scores or registers an out-of-training year.

## 6. What this charter explicitly does not claim

- **It does not predict the sign of any residual change**, in any year, in any ISO. It is argued
  on rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` — structural fidelity — and per rule 1 it must
  not be judged by whether it improves a backcast fit.
- **It does not make 2019 grantable as a locked test.** The `final` recommendation is
  independently **DO NOT GRANT** on the C3c discrimination reason
  (ASSESSMENT-neiso94 §4), which no input repair can touch. Closing this gap removes one
  disqualifier, not the binding one.
- **It does not address the pre-2019 span.** 2018 and earlier are locked-test tier by
  fail-closed default (rule 22) and out of scope.

## 7. Rule notes for the implementing session

- **Rule 28 `[R-MECH-MATRIX]`:** no `ScenarioConfig` field is added, so duty (c) is not engaged.
  But the change alters the fleet every ISO dispatches, so the implementing session should record
  it against the relevant fleet/vintage row in **each ISO's own shard** — or, if no row fits, add
  one base row plus a cell line in every shard in the same PR.
- **Rule 27 `[R-PUSH]`:** `scripts/data/process_eia860.py` is a large existing file; edit locally
  and push exact on-disk bytes, then verify the pushed blob.
- **Rule 22 `[R-HOLDOUT]`:** tasks 1–4 are entirely in-sample plus data prep, and need no marker
  and no freeze lift. Do not let task 5 drift into a spend.
