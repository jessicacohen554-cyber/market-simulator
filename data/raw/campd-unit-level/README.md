# CAMPD hourly unit-level extracts

`<ST>_<YEAR>.parquet` — one row per `(facility, unit, hour)` of EPA Clean Air
Markets Program Data (CEMS): `stateCode, facilityName, facilityId, unitId, date,
hour, opTime, grossLoad, steamLoad, so2Mass, co2Mass, noxMass, heatInput,
primaryFuelInfo, unitType, programCodeInfo`. Masses are in EPA source units
(SO2/NOx pounds, CO2 short tons); the model converts to kg on load
(`src/market_sim/data/campd.py`). Raw data is **immutable** — never edited in
place.

## Fetching

Reproducible via `scripts/fetch_campd_unit_level.py` (completed-year per-state
bulk files; set `EPA_API_KEY` to avoid the DEMO_KEY hourly rate limit):

```
python scripts/fetch_campd_unit_level.py --year 2019 --states TX IL OH …
```

The fetcher **refuses** the quarantined holdout years 2022 and H1-2026 unless
`--holdout-intake <ISO>` names an ISO with a `calibration-complete` marker
(CLAUDE.md rule 22).

## Layout / coverage

35 states (the ISO footprints in `campd.ISO_STATES`): AR CA CT DC DE IA IL IN KS
KY LA MA MD ME MI MN MO MS MT NC ND NH NJ **NV** NY OH PA RI SD TN TX VA VT WI
WV. NV added 2026-08-16 (caiso-197): Desert Star Energy Center (EIA 55077,
370.1 MW CAISO CC_REGULAR, Clark County NV) files CEMS under Nevada, so the
CA-only list left it unobservable — the FINDING-caiso193 §2 state-scope gap;
`ISO_STATES["CAISO"]` is now `("CA", "NV")` on the NYISO NY+NJ fleet-filtered
template. NV spans 2018–2026 (2026 = H1 quarters via `--quarters 1 2`).

**39 states since 2026-09-06 (SPP-11): + NE NM OK WY**, the SPP footprint's
CEMS states, landed for **2023–2026** (`docs/handoffs/FINDING-spp-11-2026-09-06.md`;
`docs/multi-iso/spp-addition-plan-2026-09.md` §6 row 1). SPP is not a
registered ISO yet, so these four states are absent from `campd.ISO_STATES`
until SPP-20 registers it; the parquets are the critical-path input for
SPP-30's outage windows and thermal tranches. Their 2026 vintage is Q1,
matching every other `<ST>_2026.parquet` in the corpus.

**41 states since 2026-09-13 (SOCO-11): + AL GA**, the Southern Company
(`SOCO`) footprint's two large CEMS states, landed for **2023–2026**
(`docs/handoffs/FINDING-soco-11-2026-09-13.md`;
`docs/multi-iso/soco-addition-plan-2026-09.md` §6 row 1). AL and GA carry
65.8 GW of SOCO's 70.7 GW, so these eight files are the SOCO program's
critical-path input (outage windows and thermal tranches, SOCO-30). **MS was
already present** 2019–2026 from the MISO footprint and is not re-fetched —
`data/raw` is immutable. SOCO is not a registered ISO yet, so AL/GA are absent
from `campd.ISO_STATES` until SOCO-20 registers it. Their 2026 vintage is Q1,
matching every other `<ST>_2026.parquet` in the corpus.

    python scripts/data/fetch_campd_unit_level.py --year <2023|2024|2025> \
        --states AL GA
    python scripts/data/fetch_campd_unit_level.py --year 2026 --quarters 1 \
        --states AL GA --holdout-intake SOCO

All eight were verified **schema-equal to `MS_2024.parquet`** (re-checked
against that exact sibling after the fact; the fetcher's own assertion
compares against the same state's newest file, which for the first AL and GA
files was `WY_2026.parquet`) and confined to their own year. Coverage is
stable across the window — `AL` 23 facilities / 88 units, `GA` 32 / 131 in
every year:

| file | rows | facilities | units | span |
|---|---:|---:|---:|---|
| `AL_2023.parquet` | 740,328 | 23 | 88 | 2023-01-01 .. 2023-12-31 |
| `AL_2024.parquet` | 772,992 | 23 | 88 | 2024-01-01 .. 2024-12-31 |
| `AL_2025.parquet` | 770,880 | 23 | 88 | 2025-01-01 .. 2025-12-31 |
| `AL_2026.parquet` | 190,080 | 23 | 88 | 2026-01-01 .. 2026-03-31 |
| `GA_2023.parquet` | 1,147,560 | 32 | 131 | 2023-01-01 .. 2023-12-31 |
| `GA_2024.parquet` | 1,150,704 | 32 | 131 | 2024-01-01 .. 2024-12-31 |
| `GA_2025.parquet` | 1,147,560 | 32 | 131 | 2025-01-01 .. 2025-12-31 |
| `GA_2026.parquet` | 282,960 | 32 | 131 | 2026-01-01 .. 2026-03-31 |

**`AL_2023` is the one file that is not a clean units × hours rectangle** and
the shortfall is EPA's, carried unmodified: five units stop reporting
mid-year — Barry unit 8, Colbert `CCT9`/`CCT10`/`CCT11` (2,208 h each, Q1
only) and Charles R Lowman `CC1` (4,416 h, H1) — for 30,552 rows against the
88 × 8,760 rectangle. Every other seven file is exact. Note that Colbert is
TVA's and Lowman is PowerSouth's: a *state* extract is not a *BA* extract, and
the SOCO fleet crosswalk still has to filter these files to the SOCO BA.

**No `SHA256SUMS.txt` rows are added for these eight.** That file's scope is
the 35 gitignored `<ST>_2018.parquet` extracts only (see its own header); the
2019–2026 files are tracked, so git's own blob hashes are their integrity
record.

**45 states since 2026-09-13 (NWPP-11): + ID OR UT WA**, the four NWPP-footprint
CEMS states absent from the corpus, landed for **2023–2026**
(`docs/handoffs/FINDING-nwpp-11-2026-09-13.md`;
`docs/multi-iso/nwpp-addition-plan-2026-09.md` §6 row 1, card N8). NWPP is not a
registered ISO yet, so these four states are absent from `campd.ISO_STATES`
until NWPP-20 registers it. **MT, NV, CA and WY were already present** from the
MISO/CAISO/SPP footprints and are not re-fetched — `data/raw` is immutable.
Their 2026 vintage is Q1, matching every other `<ST>_2026.parquet` in the corpus.

    python scripts/data/fetch_campd_unit_level.py --year <2023|2024|2025> \
        --states ID OR UT WA
    python scripts/data/fetch_campd_unit_level.py --year 2026 --quarters 1 \
        --states ID OR UT WA --holdout-intake NWPP

All sixteen were verified schema-equal to a sibling by the fetcher's own
assertion (`_verify_against_sibling`, which compares against the same state's
newest file — `WY_2026.parquet` for the first ID file, then each state's own
prior year) and confined to their own year. Coverage is stable across the
window except for one real commissioning event (below):

| file | rows | facilities | units | span |
|---|---:|---:|---:|---|
| `ID_2023.parquet` | 70,080 | 5 | 8 | 2023-01-01 .. 2023-12-31 |
| `ID_2024.parquet` | 70,272 | 5 | 8 | 2024-01-01 .. 2024-12-31 |
| `ID_2025.parquet` | 70,080 | 5 | 8 | 2025-01-01 .. 2025-12-31 |
| `ID_2026.parquet` | 17,280 | 5 | 8 | 2026-01-01 .. 2026-03-31 |
| `OR_2023.parquet` | 122,640 | 7 | 14 | 2023-01-01 .. 2023-12-31 |
| `OR_2024.parquet` | 122,976 | 7 | 14 | 2024-01-01 .. 2024-12-31 |
| `OR_2025.parquet` | 122,640 | 7 | 14 | 2025-01-01 .. 2025-12-31 |
| `OR_2026.parquet` | 30,240 | 7 | 14 | 2026-01-01 .. 2026-03-31 |
| `UT_2023.parquet` | 254,040 | 11 | 29 | 2023-01-01 .. 2023-12-31 |
| `UT_2024.parquet` | 254,736 | 11 | 29 | 2024-01-01 .. 2024-12-31 |
| `UT_2025.parquet` | 260,664 | 11 | 31 | 2025-01-01 .. 2025-12-31 |
| `UT_2026.parquet` | 66,960 | 11 | 31 | 2026-01-01 .. 2026-03-31 |
| `WA_2023.parquet` | 148,920 | 11 | 17 | 2023-01-01 .. 2023-12-31 |
| `WA_2024.parquet` | 149,328 | 11 | 17 | 2024-01-01 .. 2024-12-31 |
| `WA_2025.parquet` | 148,920 | 11 | 17 | 2025-01-01 .. 2025-12-31 |
| `WA_2026.parquet` | 36,720 | 11 | 17 | 2026-01-01 .. 2026-03-31 |

**`UT_2025` is the one file that is not a clean units × hours rectangle**, and
the shortfall is a real commissioning event carried unmodified: Intermountain
(EIA 6481) units `3SGA` (4,416 h, H2 only) and `4SGA` (2,208 h, Q4 only) enter
the extract mid-year — the IPP Renewed repowering — for 260,664 rows against
the 31 × 8,760 rectangle. The unit count therefore steps 29 → 31 between 2024
and 2025 and holds at 31 into 2026. Every other fifteen file is exact.

**CO is deliberately NOT fetched.** Colorado is inside PacifiCorp's *balancing*
reach only through a single 7.5 MW solar row in PACE (plan §6 row 1, card N8);
there is no CO combustion unit in the NWPP footprint for CEMS to observe, so a
CO extract would land ~1 MB of rows this program can never use. The skip is a
scoping decision, not a block — no CO URL was requested and none returned an
error.

**Scope note, stated at the gate (plan card N8):** CEMS observes *combustion*
units only. The NWPP fleet is 36.3 % hydro + 24.9 % wind/solar + 1.2 % nuclear
by nameplate, so **CAMPD reaches at most ~32 % of it** — materially less than in
ERCOT or SPP. The per-plant binning path (`use_campd_bins`) and the outage /
tranche artifacts it feeds therefore cover correspondingly less of this ISO.
That is a scoping fact for NWPP-30, not a reason to skip the fetch.

**No `SHA256SUMS.txt` rows are added for these sixteen**, on the SOCO-11
precedent directly above: that file's scope is the 35 gitignored
`<ST>_2018.parquet` extracts only (see its own header), and the 2019–2026 files
are tracked, so git's own blob hashes are their integrity record.

**Back years 2019–2022 landed 2026-09-06 (SPP-15) for OK, NE and NM only** —
twelve files (`docs/handoffs/FINDING-spp-15-2026-09-06.md`; charter
`docs/multi-iso/spp-addition-plan-2026-09.md` §8 SPP-15, r#4 am.1; §6 row 15):

    python scripts/data/fetch_campd_unit_level.py --year <2019|2020|2021|2022> \
        --states OK NE NM --holdout-intake SPP

**WY is deliberately NOT back-filled**: it is not in the SPP footprint
(`docs/multi-iso/spp-data-audit.md` §2.4), so its 2023–2026 files stay the
whole of its coverage here. All twelve back-year files were verified
schema-equal to `KS_2024.parquet` (the fetcher's own sibling assertion checks
against the same state's newest file; the KS check was re-run after the fact)
and confined to their own year. Unit counts move with real fleet turnover —
`NM` runs 32 units in 2019/2020, 31 in 2021/2022 and 29 from 2023; `OK` 94
throughout 2019–2022, 92 by 2025. **2018 is not landed for these three
states** and is not planned: 2018 is outside the program's working span and
its vintage is untracked at tip (below).

Rule 22 `[R-HOLDOUT]`: **this is DATA PREP, not a spend.** What is held out is
the score, never the data. 2022 is a quarantined year, so `--holdout-intake
SPP` records the owner's dispatch of the SPP-15 charter as the authorization
the fetcher requires; nothing was solved, scored or registered, and SPP holds
no tier marker (none is claimed). 2019–2021 need no such record.

| Years | Status |
|---|---|
| 2023–2025 | complete (35 states each; **39 incl. NE NM OK WY since 2026-09-06**, **41 incl. AL GA since 2026-09-13**, **45 incl. ID OR UT WA since 2026-09-13**) — the calibration window |
| 2018–2021 | **complete** (34 states 2026-07-05 + NV 2026-08-16; **+ NE NM OK for 2019–2021 since 2026-09-06**, SPP-15 — 2018 not landed for those three) — the forward CO2-rate history (`docs/handoffs/emissions-co2-rate-plan-2026-07.md` §4); all files committed in per-batch pushes |
| 2022, H1-2026 | **INTAKE-ANYTIME under explicit owner authorization** (rule 22 as amended 2026-07-06, Option 2 — the fetcher records it via `--holdout-intake <ISO>`); the SPEND (solve/score/register) stays gated by the tier markers. NV 2022/H1-2026 intaken 2026-08-16 under `--holdout-intake CAISO` (caiso-197 owner brief), matching the 34-state corpus's existing 2022/2026 coverage. NE/NM/OK/WY H1-2026 (Q1) intaken 2026-09-06 under `--holdout-intake SPP` (SPP-11 charter). **NE/NM/OK 2022 intaken 2026-09-06 under the same flag (SPP-15 charter, plan §8 SPP-15 / r#4 am.1); WY 2022 is deliberately not landed — WY is outside the SPP footprint.** ID/OR/UT/WA H1-2026 (Q1) intaken 2026-09-13 under `--holdout-intake NWPP` (NWPP-11 charter); their 2022 is not landed and is not planned by that charter. |

**RESOLVED 2026-07-08 — EIA-923 2018–2021 (parasitic net conversion) source gap
closed, re-derive still open.** The v2 rate artifact converts CAMPD gross → net
with per-plant parasitic factors (`scripts/derive_parasitic_load.py`, EIA-923
net ÷ CAMPD gross). The committed
`data/raw/_processed-legacy/eia923_monthly_generation.parquet` now covers
**2018–2026** (data-register intake landed the four missing `f923_2018.zip …
f923_2021.zip` releases — see `docs/data-register-2026-07.md`). The 2018–2021
v2 rows still inherit each plant's **pooled** measured parasitic factor (a
slowly-varying station-service fraction) — `derive_plant_emissions_v2.py`'s
documented fallback, physically the right prior — because the re-derive
itself has not been run yet. To refine: `derive_parasitic_load.py --years
2018 2019 2020 2021` then re-derive v2 (a separate, owner-visible operation
per rule #15 — cite this data landing as the trigger).

**Note on the 2018–2021 push:** these 136 files are large binary parquets, so
they were committed and pushed in small per-batch `git push` commits (each pack
tens of MB, base = latest main) — a single pack of the full ~0.5 GB 413s on this
remote and `mcp__github__push_files` is text-only (CLAUDE.md Git section). All
batches are on main; any missing file regenerates from the committed fetcher.

## The 2018 vintage is UNTRACKED at tip (BLOAT-S2, 2026-08-17)

The 35 `<ST>_2018.parquet` files are **gitignored** since the Stage-2
(a)-only untrack (O2 grant,
`docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`; evidence pass
`docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §3). 2018 is outside
the program's working span (owner decision 2026-08-06; fail-closed
locked-test tier, unsolvable), so no solve reads it — its consumers are
derive/curation-time only (the forward CO2-rate history recipe
`derive_fossil_co2_rates.py --years 2018..2021`, the 2018–2026
`derive_campd_unit_outages.py` extract recipe and its caiso-198/199 gate
probes, `derive_correlated_outage_curve.py`, the `curate_emissions*` glob
defaults). **2019–2026 stay tracked**: they are solve-time inputs
(`campd.load_campd_hourly` / `outages._campd_availability_envelope`, keyed on
the solve year) for the training and holdout tiers, with silent-degrade
absence semantics — never untrack them.

**Recovery is re-fetch ONLY** (story (a); no pin/history route). Measured
2026-08-17: the EPA CAM-API bulk-files service served
`emissions-hourly-2018-tx.csv` (HTTP 206, `x-api-key: DEMO_KEY`) — stable
federal archive, full history. Re-fetch BEFORE running any 2018-spanning
derive:

    python scripts/data/fetch_campd_unit_level.py --year 2018 --states <ST ...>

(no holdout quarantine applies to 2018). `SHA256SUMS.txt` records the exact
removed bytes; the fetcher's sibling-schema verification keeps a re-fetched
file schema-identical, though parquet serialization may differ byte-wise.

**42 states since 2026-09-22 (NWPP-47): + AZ**, landed for **2023–2025** as
evidence for the NWPP plant-level EIA-930 attribution intake
(`docs/handoffs/FINDING-nwpp-47-2026-09-22.md` §2): GRID's SRP / WALC export
legs are regressed hourly on Desert-Southwest CEMS gas plants to establish they
are resources the NWPP fleet does not own. AZ is not an NWPP footprint state
and is absent from `campd.ISO_STATES`; no loader reads it.

    python scripts/data/fetch_campd_unit_level.py --year <2023|2024|2025> \
        --states AZ

| file | rows | facilities | units | span |
|---|---:|---:|---:|---|
| `AZ_2023.parquet` | 788,400 | 25 | 90 | 2023-01-01 .. 2023-12-31 |
| `AZ_2024.parquet` | 803,760 | 26 | 92 | 2024-01-01 .. 2024-12-31 |
| `AZ_2025.parquet` | 819,168 | 26 | 96 | 2025-01-01 .. 2025-12-31 |
