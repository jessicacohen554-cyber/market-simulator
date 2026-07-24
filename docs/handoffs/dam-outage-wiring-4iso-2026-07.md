# DAM-first outage-overlay wiring — 4 ISOs (CAISO / MISO / NEISO / PJM)

**Session 2026-07-24, branch `claude/dam-outage-wiring-4iso-nqecbh` (infra, NOT a
keeper).** Wires each ISO's published availability instrument as the PRIMARY
outage source, DAM-first with the CAMPD-unit derate as the fallback, matching the
ERCOT precedent. All four gates ship **backcast-only + default-off**; when off the
solve is byte-identical to today's keeper.

## Status

| Piece | State |
|---|---|
| PJM data fetched + derived (2018-2026) | on disk, loader-resolvable; intake logged in `frontend/data/backcast/calibration-complete.json` |
| `src/market_sim/data/fleet/arrays.py` (the DAM-first application) | **PUSHED + blob-verified** (2373 ln, sha `94b2840d…`) |
| `tests/test_dam_outage_wiring.py` | **PUSHED + verified** (5 tests green) |
| `data/raw/pjm-outages/.gitignore` (un-ignore by-year CSVs) | **PUSHED + verified** |
| `src/market_sim/config/scenarios.py` (the 4 gate fields + cache-key registration) | **PATCH ONLY** — see below |
| PJM by-year CSVs | **regenerate locally** — see below |

## Why scenarios.py ships as a patch (not applied on the branch)

`scenarios.py` is **8242 lines ≈ 237,000 tokens** of content. The API-only push
path (`mcp__github__push_files`) requires emitting the *entire* file content in a
single tool call, which exceeds the model's output-token limit by a wide margin —
a **hard physical limit**, not a budget-tuning issue (arrays.py at ~68k tokens
fit and pushed; scenarios.py at ~237k cannot). `git push` is disallowed
(CLAUDE.md Git & Pushing) and api.github.com is blocked by org egress policy.
This is the same wall the original CAISO/MISO/NEISO/PJM intake sessions hit
(their loaders + data landed; the `scenarios.py` + `fleet.py` edits shipped as
unapplied patches). The change is a clean **129-line, 3-hunk, purely-additive**
patch that applies cleanly onto the branch's `scenarios.py`.

**To apply (one command, local git):**

```bash
git checkout claude/dam-outage-wiring-4iso-nqecbh
git apply docs/handoffs/patches/dam-outage-wiring-4iso-scenarios.patch
# verify: ScenarioConfig().cache_key() must stay "edbc1b103207170a" (pinned)
python -m pytest tests/test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned tests/test_dam_outage_wiring.py -q
git commit -am "dam-wiring: add 4 DAM-outage gate fields to ScenarioConfig (default off)"
git push
```

The patch adds four default-`False` gate fields with cited docstrings —
`caiso_dam_outages`, `miso_native_outage_source`,
`neiso_operable_capacity_availability`, `pjm_dam_availability` — and registers all
four in `_CACHE_KEY_OPTIONAL_FIELDS` so the pinned default `cache_key`
(`edbc1b103207170a`) and every existing keeper key stay byte-stable. Until it is
applied, `arrays.py`'s `getattr(config, "…", False)` guards make the wiring an
inert no-op (safe), but the gates cannot be armed and `tests/test_dam_outage_wiring.py`
fails on the unknown kwargs.

## PJM by-year CSVs — regenerate locally

The 9 `data/raw/pjm-outages/by-year/gen_outages_by_type_<YEAR>.csv` (2018-2026,
current-day actuals) are dense numeric data that cannot be faithfully hand-emitted
through the text-only push path. They regenerate **deterministically** from the
two committed scripts (the un-gitignore is already pushed, so they'll be tracked):

```bash
python scripts/data/fetch_pjm_outages.py --start 2018-01-01 --end 2026-07-19
python scripts/data/derive_pjm_dam_availability.py
git add data/raw/pjm-outages/by-year/ && git commit -m "dam-wiring: land PJM by-year outage CSVs"
```

(`data/raw/pjm-dam-availability.parquet` is the gitignored local fast-path; the
by-year CSVs are the committed portable source of truth. Both regenerate from the
raw pull.) Rule-22 intake authorization for 2018-2026 is logged in
`calibration-complete.json` (`intake_log` 2026-07-24, verbatim task authorization).

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

## Verification done this session

- **Config byte-inertness:** `ScenarioConfig().cache_key()` stays the pinned
  `edbc1b103207170a`; each gate ON forks a distinct key (proven).
- **Fleet byte-inertness + mechanism-fires:** synthetic-fleet no-LP builds
  (`tests/test_dam_outage_wiring.py`, 5 green): each gate fires on its covered
  scope at the native grain and is byte-identical off / on the uncovered scope
  (containment — no leakage, no double-count).
- **No ERCOT regression:** the ERCOT DAM fleet-application tests and the fleet
  golden pass unchanged (arrays.py ERCOT block untouched).

## NOT done this session (per task scope)

- **In-sample 2023-2025 A/B** (CAMPD-off vs DAM-on rubric deltas, criterion 5):
  8 multi-year LP solves, deferred — run after scenarios.py is applied. This is a
  STRUCTURAL mechanism change (rule 1): keep the DAM-first source even if the fit
  worsens; a keeper promotion additionally requires leave-one-year-out scoring
  within 2023-2025 (rule 22). **No gate defaulted ON, no keeper promoted, no
  out-of-training year solved.**
