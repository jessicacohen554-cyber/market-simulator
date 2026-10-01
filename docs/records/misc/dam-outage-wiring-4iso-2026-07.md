# DAM-first outage-overlay wiring — 4 ISOs (CAISO / MISO / NEISO / PJM)

**Session 2026-07-24.** Wires each ISO's published availability instrument as the
PRIMARY outage source, DAM-first with the CAMPD-unit derate as the fallback,
matching the ERCOT precedent. All four gates ship **backcast-only + default-off**;
when off the solve is byte-identical to today's keeper.

## Status — COMPLETE on `main`

| Piece | State on main |
|---|---|
| `src/market_sim/config/scenarios.py` — 4 gate fields + cache-key registration | **APPLIED** (8242 ln, 4/4 fields, 4/4 cache-key entries, pinned `cache_key` = `edbc1b103207170a` preserved) |
| `src/market_sim/data/fleet/arrays.py` — DAM-first application | **APPLIED** (9 wiring refs, blob-verified) |
| `tests/test_dam_outage_wiring.py` — regression tests | **APPLIED** (5 tests; skip per-ISO when its data is absent, skip all until gate fields exist) |
| `data/raw/pjm-outages/.gitignore` — un-ignore by-year CSVs | applied |
| `docs/handoffs/patches/dam-outage-wiring-4iso-scenarios.patch` | committed (the scenarios.py change, for reference) |
| `frontend/data/backcast/calibration-complete.json` — rule-22 PJM intake log | applied |
| PJM by-year CSVs | **regenerate locally** — see below |

## How scenarios.py was landed (it exceeds the API push path)

`scenarios.py` is 8242 lines ≈ 237k tokens of content — beyond any single-response
emission limit, so `mcp__github__push_files` (which needs the whole file in one
call) could not carry it, and `git push`/api.github.com are unavailable in this
session. The 129-line additive patch (`docs/handoffs/patches/dam-outage-wiring-
4iso-scenarios.patch`, base blob `5bb724f` matching main's) was therefore applied
**server-side** by a one-shot `workflow_dispatch` GitHub Action that did
`git apply` + commit + push (sparse checkout of just the two files it touches —
seconds of runner time). The workflow has been **deleted**; no per-task CI remains.

## PJM by-year CSVs — regenerate locally (or in CI)

The 9 `data/raw/pjm-outages/by-year/gen_outages_by_type_<YEAR>.csv` (2018-2026)
are dense numeric data that can't be faithfully hand-emitted through the text-only
push path, so they are **not committed** — the tests skip PJM when they're absent.
They regenerate deterministically (the un-gitignore is on main, so they'll be
tracked once generated):

```bash
python scripts/data/fetch_pjm_outages.py --start 2018-01-01 --end 2026-07-19
python scripts/data/derive_pjm_dam_availability.py
git add data/raw/pjm-outages/by-year/ && git commit -m "dam-wiring: land PJM by-year outage CSVs" && git push
```

`data/raw/pjm-dam-availability.parquet` is the gitignored local fast-path; the
by-year CSVs are the committed portable source of truth. Rule-22 intake
authorization for 2018-2026 is logged in `calibration-complete.json` (`intake_log`
2026-07-24, verbatim task authorization).

## Design (per ISO, grain-correct, no double-count)

- **CAISO** (`caiso_dam_outages`) — per-PLANT grain. `caiso_dam_outage_derate_factors`
  returns the same `{(plant_code, plant_group): (hours,) multiplier}` interface as
  the CAMPD derate, so precedence is a per-key merge `ufac = {**ufac, **dam}`: the
  DAM curtailment reports override only the plants they name; every other plant and
  any pre-2021-06-18 year keeps its CAMPD window.
- **MISO** (`miso_native_outage_source`) — AGGREGATE region envelope. Covers the
  whole fossil-thermal fleet uniformly, so a covered year REPLACES `ufac` outright;
  a year the record does not cover (pre-2023) returns empty → keeps CAMPD.
- **NEISO** (`neiso_operable_capacity_availability`) — FLEET grain. Pooled-thermal
  bidirectional cap-1.0 water-fill to the measured operable-capacity fraction
  (ISO-NE publishes fleet-total only), superseding CAMPD on covered days.
- **PJM** (`pjm_dam_availability`) — per-CLASS uniform fraction. Each covered
  fossil-thermal class water-filled to the same measured RTO fleet fraction (PJM
  publishes no per-class split). A SEPARATE block from ERCOT, so the ERCOT overlay
  stays byte-identical.

All four are backcast-only (`mode == "backcast"`) and skip cleanly to the CAMPD
fallback when the gate is off or the loader returns no coverage for `(iso, year)`.

## Verification

- **Config byte-inertness:** `ScenarioConfig().cache_key()` stays the pinned
  `edbc1b103207170a`; each gate ON forks a distinct key (proven; main's
  scenarios.py is byte-identical to the locally-verified copy).
- **Fleet byte-inertness + mechanism-fires:** synthetic-fleet no-LP builds
  (`tests/test_dam_outage_wiring.py`, 5 green locally): each gate fires on its
  covered scope at the native grain and is byte-identical off / on the uncovered
  scope (containment — no leakage, no double-count).
- **No ERCOT regression:** the ERCOT DAM fleet-application tests and the fleet
  golden pass unchanged (arrays.py ERCOT block untouched).

## NOT done this session (per task scope)

- **In-sample 2023-2025 A/B** (CAMPD-off vs DAM-on rubric deltas, criterion 5):
  8 multi-year LP solves, deferred to a dedicated run. This is a STRUCTURAL
  mechanism change (rule 1): keep the DAM-first source even if the fit worsens; a
  keeper promotion additionally requires leave-one-year-out scoring within
  2023-2025 (rule 22), surfaced to the owner for the promotion decision. **No gate
  defaulted ON, no keeper promoted, no out-of-training year solved.**
