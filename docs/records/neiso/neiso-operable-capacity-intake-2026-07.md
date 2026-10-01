# NEISO operable-capacity / generation-outage intake (ISO-NE Morning Report)

**Date:** 2026-07-19 · **ISO:** NEISO · **Scope:** data intake + gated
consumption seam (no LP solve, no scoring, no keeper change).

## What & why

The NEISO backcast's measured outage/availability signal has been the
CAMPD-derived unit-outage fallback (`campd-unit-outages-NEISO.csv`) — outages
*inferred* from zero-gross-load CEMS hours. This session intakes the ISO-NE
**published** equivalent of what ERCOT uses (`ercot-thermal-dam-availability.csv`,
the 60-Day DAM measured class-day availability): the ISO-NE **Morning Report**,
**Section 3 "Operable Capacity Analysis"**, which publishes each day's
**Generation Outages and Reductions (Planned + Forced)** MW and **Total Available
Capacity** MW — the direct measured "outages and capacity availability" series a
NEISO backcast can use *instead of* the CAMPD fallback.

## Source & coverage

- **Report:** ISO-NE ISO Express → Operations → Morning Report, Section 3.
  Landing: <https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/morning-report>
- **Public CSV endpoint:** `https://www.iso-ne.com/transform/csv/morningreport?start=YYYYMMDD`
  (isox_token bootstrap, same as the sibling `fetch_neiso_reserve_requirements.py`).
- **Coverage:** **2018-07-01 → present** (2026-07-19 at intake). 2018 H1 returns
  an empty placeholder (archive start). The planned/forced *split* columns are
  published only from the mid-2025 format change; null before.
- **~2,940 daily reports.** Byte-verified parse: the published accounting
  identity `H = A + B − C − D + E − F − G` reconciles to **0 MW on every row**.

## Deliverables

**Committed directly (via the API):**

| Path | Role |
|---|---|
| `scripts/data/fetch_neiso_morning_report.py` | downloader → `data/raw/neiso-operable-capacity/daily/*.csv` (gitignored, regenerable) |
| `scripts/data/build_neiso_operable_capacity.py` | label-keyed parser → the committed CSV (`--parquet` for a local columnar copy) |
| `data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv` | **committed deliverable**, per-year (2018–2026), one faithful row/day (nullable-int MW) |
| `data/raw/neiso-operable-capacity/README.md` | source citation + full column contract |
| `src/market_sim/data/neiso_operable_capacity.py` | loader + `neiso_thermal_availability_series(year, hours)` — the consumption API |
| `tests/test_build_neiso_operable_capacity.py` | parser + loader-math test (no network, no LP) |

**Ships as a patch** (`docs/handoffs/patches/neiso-operable-capacity-wiring.patch`,
the oversized-core-file transport — `scenarios.py`/`fleet.py` are ~0.5 MB each,
too large for the API push, `git push` is forbidden). Purely additive; applies
cleanly onto pristine `origin/main`; verified end-to-end this session:

| Edit | Role |
|---|---|
| `ScenarioConfig.neiso_operable_capacity_availability` (+26) | gate, **default OFF** |
| `data.fleet.generators_to_fleet_arrays` block (+79) | applies the measured fleet availability, superseding the CAMPD derate for covered thermal classes |

Regenerate: `python scripts/data/fetch_neiso_morning_report.py && python scripts/data/build_neiso_operable_capacity.py`.
Apply the wiring after merge: `git apply docs/handoffs/patches/neiso-operable-capacity-wiring.patch`.

## Design (mirrors the ERCOT DAM-availability precedent)

Like `ercot-thermal-dam-availability.csv`, this is a **raw-direct committed
artifact** read by a loader — not a `data/clean` datatype — because the user
asked for the ERCOT-equivalent and ERCOT's measured-availability overlays read
raw directly. **Format: committed CSV** (nullable-int MW, git-diffable), not
parquet — the repo's API-only push path (CLAUDE.md "Git & Pushing") commits file
content as text and cannot round-trip binary (verified this session: both
`push_files` and `create_or_update_file` store base64 content literally). This
matches the ERCOT precedent, itself a committed CSV. `build_...py --parquet
<path>` emits a columnar parquet locally for anyone who wants one. The committed table stores **published MW only** (rule 13 faithful
transcription); the consumed availability *fraction* is derived in the loader:

```
avail(day) = 1 − outages / (CSO + EcoMax-above-CSO)      # 1 − C/(A+B)
```

The fleet builder imposes it with the **same bidirectional cap-1.0 water-fill**
the ERCOT class-day block uses (RESTORE toward the ceiling where measured >
model, REMOVE toward zero where measured < model), setting the covered
dispatchable-thermal classes' cap-weighted day-mean availability to the measured
level and preserving each unit's intra-day shape below it.

**Grain caveat.** ISO-NE publishes availability only at **fleet** grain here (no
public per-unit / per-fuel outage series — only masked-asset DA offers, already
intaken under `data/raw/NEISO-AS/da-energy-offers/`). So this is one pooled fleet
fraction across the thermal classes, not ERCOT's per-class construction. Refining
*which* classes it covers, or whether to pair it with a residual, is a NEISO
calibration-lane decision — this session delivers the data + opt-in wiring, not a
keeper.

## Admissibility (CLAUDE.md rules 13/14)

Every stored figure is an ISO-NE-published **MW** quantity — a physical
generation-outage / operable-capacity measurement (planned maintenance + forced
outages) that regenerates for a forward year from forward maintenance/forced-
outage drivers and responds to changed conditions (the rule-13 test). The
consumed fraction is a transparent ratio of published figures, **never a price**
and **never rescaled onto a price/volume residual**. Backcast-only; forecast
keeps the statistical WEFOR/POF stack (the mode-aware seam). This is the ERCOT
DAM-availability admissibility argument, applied at fleet grain.

## Holdout authorization (rule 22)

The intake spans out-of-training years (2018–2022, 2019/H1-2026 locked). It was
executed under the **owner's explicit request** ("get as much as you can between
2018 and 2026"), the session-logged authorization rule 22 requires (registry
entry: `docs/out-of-sample-results-2026-07.md §1.2`). Discipline honored:

- **No LP solve, no scoring, no calibration-complete marker set.** Validation is
  no-LP only: byte-parse (identity = 0) + loader dry-run.
- The gate is **default OFF**, so every existing NEISO run is byte-identical;
  turning it on, and any *solve* of an out-of-training year, remains separately
  quarantined (needs NEISO's calibration-complete marker + `--holdout-authorized`
  per rule 22 / the CI `quarantine-gates` job).

## Verification done this session

- Parser: identity `H = A+B−C−D+E−F−G` = 0 MW on all parsed rows; blank
  planned/forced split → NaN (not 0).
- Loader: `neiso_thermal_availability_series(2024)` returns the exact
  `1 − C/(A+B)` fraction as a flat 24-h block on the covered date, NaN elsewhere.
- End-to-end: driving `generators_to_fleet_arrays` on a 2-unit thermal fleet with
  the flag **on** lands the covered-day cap-weighted thermal availability on the
  measured 0.891; uncovered days keep the statistical model; flag **off** is
  fully inert.
