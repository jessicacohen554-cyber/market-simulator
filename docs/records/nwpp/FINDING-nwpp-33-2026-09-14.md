# FINDING — lane NWPP-33 (zonal shares · per-zone VRE shape · per-zone gas basis)

Lane **NWPP-33**, `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-33.
Model: Opus `claude-opus-5`. Branch `claude/nwpp-33-zonal-shares-q7x4`.
DATA PROFILE `nwpp`. Preconditions checked and MET: NWPP-20 has landed — the five
zones are registered in `iso_configs._nwpp_config` and `_NWPP_BA_ZONES` is keyed on
`Balancing Authority Code`.

---

## 1. The two things the charter asks for FIRST

### 1.1 THE 54 CHPD HOURS SURVIVED — measured, not asserted

**All 54 survive, untouched, in every artifact this lane produced.** Re-measured
this session on the committed data rather than taken from NWPP-10:

| Check | Measured |
|---|---|
| CHPD 2024 hours above 2.5 × its own median (206.0 MW) | **54** |
| …of which fall in 12–16 January 2024 | **54 — all of them** |
| `Demand (MW) (Adjusted)` byte-identical to raw on those hours | **True** |
| CHPD 2024 annual peak | **583.0 MW at 2024-01-13 16:00 UTC** |
| CHPD 2024 peak / median | **2.83** |
| **NWPP-NW 2024 annual peak, after this lane's regroup** | **21,560.0 MW at 2024-01-13 19:00 UTC** |
| CHPD's contribution in that peak hour | **564.0 MW** |

The NWPP-NW peak reproduces the charter's own figure **to the MW**, and it sits
inside the cold-snap block — so the zone's annual peak is *carried by* the hours the
spike screen would have deleted. `_screen_demand_spikes` is **not applied**;
`_screen_demand_dropouts` **is** (it repaired the 17 exactly-zero NEVP hours of
2025, logged each time). Nothing is padded, interpolated or rescaled beyond those
two repairs (rule 13 `[R-MEASURED]`).

**Gate G20 held.** The footprint coincident peak comes back at **49,290 / 52,564 /
50,953 MW** for 2023 / 2024 / 2025 — the cleaned values, to the MW, not the 835,464
MW an unscreened series produces. The 30 artifact hours never enter, because the
Adjusted column already repairs them.

The guard is now a test, not a convention: `tests/curation/
test_curate_zonal_shares_nwpp.py::test_a_cold_snap_spike_is_not_screened` fails if
anyone reintroduces spike screening on this path.

### 1.2 THE FIVE ZONAL SHARES, summing to 1.0

Pooled 2023–2025 energy shares of `Demand (MW) (Adjusted)`, UTC-joined onto the
Pacific local year:

| Zone | Pooled 2023–2025 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| **NWPP-NW** | **0.376815** | 0.377755 | 0.373973 | 0.378719 |
| **NWPP-EAST** | **0.180797** | 0.178532 | 0.181140 | 0.182650 |
| **NWPP-INLAND** | **0.153271** | 0.155302 | 0.152879 | 0.151694 |
| **NWPP-OR** | **0.150934** | 0.152877 | 0.150928 | 0.149059 |
| **NWPP-SNV** | **0.138182** | 0.135535 | 0.141081 | 0.137877 |
| **Sum** | **1.0 exactly** | 1.000000000000 | 1.000000000000 | 1.000000000000 |

These are the *energy* shares. The committed artifact is the **hourly** matrix —
`(5, 8760)` per year, every hour summing to 1.0 — so each zone carries its own
diurnal and seasonal shape rather than a flat fraction.

**They reproduce NWPP-20's registered static `load_share` to the fourth decimal**
(0.3769 / 0.1509 / 0.1533 / 0.1808 / 0.1381), which is an independent confirmation
of that lane's registration from the same bytes by a different code path.

---

## 2. Why the shares are EXACT and not approximate — the one property only a pool has

Every other ISO's zonal-share parser divides one published per-zone series by a
**differently-sourced** system total, so the two sides reconcile to within a
tolerance (SPP's own parser documents "annual sums within 0.03 %"). NWPP does not
have to: it is a **pool of seventeen balancing authorities**, its system demand is
already the UTC-joined sum of seventeen per-BA extracts, and owner ruling N5 makes
every zone a whole-BA group. So the zonal shares are that same sum **taken in five
parts instead of one** — one pass over one set of arrays.

Measured consequence, all three years:

```
max | Σ_zones demand_z(t) − pool frame's own Demand(t) |  =  0.0 MW        (exact)
max | Σ_zones share_z(t) − 1 |                            =  2.22e-16      (float eps)
max | Σ_zones share_z(t)·Demand(t) − Demand(t) |          =  7.28e-12 MW
```

`parse_nwpp_shares` therefore **re-uses** `eia930.frames._pool_member_frames` and the
pool builder's own screening rather than re-implementing them, so the convention
cannot drift between the system total and its parts (rule 19 `[R-ONE-MECH]`).

**Gate G18 held.** The shares come from the committed per-BA EIA-930 series
(NWPP-11's 17 extracts), **not** sub-BA — none exists for any of the 17 — and **not**
state-keyed. No zone splits a BA; the crosswalk is `_NWPP_BA_ZONES` itself, pinned
by test against owner ruling N5's exact partition.

**Gate G19 held.** `_pool_member_frames` re-indexes every member onto the
`_POOL_CLOCK_BA` (BPAT) **Pacific** local year by a pure UTC join, so the three
Mountain members (NWMT, PACE, WAUW) land on the Pacific hour that is the same
physical hour. Every artifact this lane writes states its clock in its own module
docstring or README: **UTC is the canonical key; local time is provenance only.**

AVRN and GRID carry null demand in all 26,304 hours and enter their zones as
exactly 0.0, so they move no share — pinned by a test that also rejects an
implementation treating "no demand" and "zero demand" differently. Their
**generation** still lands in NWPP-NW / NWPP-OR, and §3 shows how much that is.

---

## 3. The VRE shape summary — and this footprint gets a MEASURED one

MISO, SPP and ERCOT buy their per-zone wind shape from MERRA-2 reanalysis wind
speed run through a turbine power curve, because EIA-930 publishes their wind as
**one** BA-wide series that cannot be taken apart. **NWPP's can be**: EIA-930
publishes `NG: WND` and `NG: SUN` for each of the seventeen members, and each zone
is a whole-BA group. Under rule 14 `[R-ACCURATE]` the builder therefore **reads
rather than simulates**, and it carries none of the reanalysis path's physics
constants — no shear exponent, no power curve, no hub height. **Zero free
parameters** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

Numerator and denominator are attributed on **one key**: generation groups on
`_NWPP_BA_ZONES`, and the EIA-860 December capacity it is divided by reaches zones
through `build_zone_lookup("NWPP")`, which is that same BA map. The implied
capacity factor is therefore internally consistent, and it lands in physical
ranges (wind 0.22–0.40, solar 0.07–0.29) rather than at a normalisation artifact.

### 3.1 Wind — a 2.3× diurnal spread, stable in sign and rank across three years

| Zone | night(00-06)/afternoon(12-18), 2023 / 2024 / 2025 | Dec cap 2024 (MW) | 2024 TWh | 2024 CF |
|---|---|---:|---:|---:|
| **NWPP-OR** | **1.26 / 1.26 / 1.32** — nocturnal | 1,206.4 | 4.053 | 0.384 |
| NWPP-INLAND | 1.07 / 1.10 / 1.08 | 1,899.7 | 6.691 | 0.402 |
| NWPP-NW | 0.89 / 0.82 / 0.82 | 6,181.4 | 13.435 | 0.248 |
| NWPP-EAST | 0.82 / 0.86 / 0.85 | 3,981.6 | 10.325 | 0.296 |
| **NWPP-SNV** | **0.55 / 0.59 / 0.57** — afternoon | 150.0 | 0.317 | 0.241 |

**For scale: the contrast that justified SPP's own per-zone wind shape was 1.04 vs
0.97 — a 7 % difference. NWPP's is 2.3×.** One footprint-wide profile applied to
all five zones holds wind in the wrong zone at the wrong hour by a far larger
margin than either ISO that already arms this mechanism.

**AVRN and GRID are load-empty but supply-heavy, and it matters here:** AVRN
contributes **5.285 TWh of wind in 2024 — a third of NWPP-NW's total** — and GRID
**2.171 TWh, over half of NWPP-OR's**. The zone map places them, and the placement
is doing real work on the supply side even though it does nothing on the load side.

### 3.2 Solar — a one-hour west-to-east progression, in the geographic order

Energy-weighted mean hour-of-day of solar output on the pool's Pacific clock:

| Zone | 2023 | 2024 | 2025 | Dec cap 2024 (MW) | 2024 CF |
|---|---:|---:|---:|---:|---:|
| NWPP-NW | 11.81 | 11.88 | 11.74 | 561.2 | 0.073 |
| NWPP-OR | 11.30 | 11.35 | 11.36 | 667.9 | 0.233 |
| NWPP-SNV | 11.21 | 11.17 | 11.13 | 4,181.9 | 0.225 |
| NWPP-INLAND | 11.05 | 11.05 | 11.06 | 859.1 | 0.210 |
| NWPP-EAST | 10.81 | 10.83 | 10.87 | 2,196.4 | 0.293 |

Monotonic west → east, reproducing to **±0.07 h across three independent years**.
That is what a footprint spanning ~11° of longitude and two timezones must produce,
and it is the cleanest available check that these series are the real thing rather
than noise: `NWPP-EAST` (Utah / Wyoming, filed on Mountain time) peaks a full hour
earlier on the Pacific clock than `NWPP-NW`.

**Declared, not buried:** `NWPP-NW`'s solar CF of 0.073–0.083 is genuinely the
worst solar resource in the footprint (the BPAT + PSEI fleet), not a defect. BPAT's
`NG: SUN` also carries the most negative hours of any member — station-service
netting — and clipping them to zero costs **0.56 %** of that zone-year's positive
energy, the largest clip in either fuel and still under 1 %. Every other cell is
≤ 0.17 % (wind ≤ 0.02 %). `renewables` clips identically at read time, so the
committed artifact and the applied shape are the same object.

---

## 4. The gas-basis assignment table, with citations

`data/raw/nwpp_zonal_gas_hub.csv`, on the sibling five-column schema. Full
provenance: `data/raw/nwpp_zonal_gas_hub.SOURCES.md`.

| Zone | Hub | Evidence for the hub | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|
| **NWPP-NW** | Sumas / Northwest Pipeline | Northwest Pipeline GP **2,036.8 MW** named (audit §7.2); its Canadian-border receipt point **is** Sumas, which EIA calls *"the main pricing point for natural gas in the Pacific Northwest"* | 2.682 | 0.847 | −0.282 |
| **NWPP-OR** | Stanfield / GTN | GTN **1,490.2 MW** + "Pacific Gas" 1,319.3 MW; GTN's interconnect with Northwest Pipeline is **Stanfield**, inside this zone | 2.454 | −0.240 | −1.301 |
| **NWPP-INLAND** | **MIXED** — Opal/NWP (IPCO) + Stanfield/GTN and NorthWestern LDC (NWMT) | NWP 762.2 vs GTN 554.3 + NorthWestern LDC 261.6 MW. **See §4.1 — this is not a tie broken silently** | 2.143 | 0.223 | −0.952 |
| **NWPP-EAST** | Opal / Rockies (Williams, Questar-Enbridge) | **1,328.7 of 1,695.3 named MW (78.4 %)** on the Rockies complex once the `Pipeline Notes` are read — **§4.2, which closes the audit's provisional flag** | 5.272 | 0.774 | −0.173 |
| **NWPP-SNV** | Kern River | Kern River **4,747.1 MW** directly, plus Southwest Gas 3,419.1 MW as the LDC downstream of Kern River / El Paso. Unambiguous | 4.654 | 0.734 | −0.091 |

Values are `basis_vs_hh_usd_mmbtu` — the zone's own plants' delivered price minus
Henry Hub, month-balanced. **The hub name is documentation; the number beside it is
never a quote from that hub.** It could not be: NWPP-12 established that Stanfield,
Opal and Kern River have **no free public series reachable from this repo**, and
synthesising one from a neighbour is what gate **G17** and rule 13 forbid. Instead
every row is the **measured EIA-923 Schedule 2 delivered price the zone's own
plants actually paid** — the accurate input a hub proxy would have been standing
in for (rule 14), at complete 12-month × 5-zone × 3-year coverage with no gap and
no fallback rule. The MMBtu totals reproduce NWPP-12 §1 exactly, an independent
re-derivation.

The **level never reaches a solve** (the mean-zero applier re-centres to a
gas-capacity-weighted zero); what moves dispatch is the spread, which is **3.129 /
1.087 / 1.210 $/MMBtu** across 2023 / 2024 / 2025.

### 4.1 `NWPP-INLAND` is genuinely mixed, and is labelled mixed

| Member | $/MMBtu 2023–2025 | MMBtu | Pipeline |
|---|---:|---:|---|
| NWMT | **1.815** | 20,214,617 | GTN + NorthWestern's own LDC |
| IPCO | **3.903** | 63,684,507 | Northwest Pipeline (Williams / Rockies) |

**2.15×, inside one zone — the zone's average of 3.400 describes neither member.**
The charter said to say so rather than pick the larger half silently, so the `hub`
column reads `MIXED: …` and names both halves. Splitting the zone is a **zoning**
change — owner-ruled territory (card N5), and gate G18 bars any zone finer than a
whole-BA group regardless — so this is declared, not fixed. It is the same class of
limitation `SPP-North` carries on its 30 % Kansas proxy, and it is larger.

### 4.2 `NWPP-EAST` is no longer provisional — the audit's open item is CLOSED

`nwpp-data-audit.md` §7.2 flagged 1,174.1 MW of PACE gas filed as *"Other — please
explain in pipeline notes below"* and asked a follow-up to read the notes. Read,
off the committed `eia860_plant.parquet`:

| Plant | MW | `Pipeline Notes`, verbatim |
|---|---:|---|
| Jim Bridger | 1,164.1 | *"Jim Bridger Units 1 and 2 recieve their gas supply from Williams Gas Supply. The units are owned by PacifiCorp and Idaho Power."* |
| Hurricane City Power | 10.0 | *"Enbridge (formerly Dominion Energy)"* — Questar's successor |

Williams and Questar-Enbridge are both the Rockies complex. With Questar's own
152.4 MW and Colorado Interstate's 2.2 MW that is **1,328.7 of 1,695.3 named MW
(78.4 %)**, against Kern River 217.0 and Northwest Pipeline 144.0. **Opal / Rockies
confirmed.**

Still open and **not** this lane's to close: **5,518.0 MW (23.7 %) of footprint gas
names no pipeline at all** in EIA-860. That is a gap in the *hub label*, not in the
*prices* — every committed row is a delivered price actually paid.

### 4.3 STATED LIMITATION — the 2023 row is a one-month-dominated annual mean

The western winter 2022-23 gas event puts January 2023 at **$39.66 (EAST) / $34.61
(SNV) / $21.38 (OR) / $18.30 (NW) / $15.41 (INLAND)** per MMBtu against a **$3.27**
Henry Hub, and it dominates every zone's 2023 row. **The month is real and it is not
removed** — dropping a month because it is inconvenient is the residual-driven
selection rules 1 `[R-STRUCT]` and 13 forbid. The January-excluded basis (2.443 /
2.229 / 1.031 / 1.559 / 1.234) is carried **in each 2023 row's own `source` string**
and in SOURCES §5, so the distortion is visible rather than buried; it is not an
alternative value and must not be substituted for one.

Worth flagging because it is the reason this is a caveat and not a footnote: the
event **re-ranks part of the spread**, it does not merely scale it. EAST and SNV
stay dearest in the same order either way, but `NWPP-OR` and `NWPP-INLAND` swap for
cheapest zone (full-year: INLAND 2.143 < OR 2.454; January-excluded: OR 1.031 <
INLAND 1.234).

---

## 5. ROUTED TO NWPP-DESK — nothing this lane landed is armed, by design

Every artifact is **data with a registered filename**. No `ScenarioConfig` field
was added, nothing under `src/` was touched, no `cache_key()` moves and no existing
keeper is affected (plan §7 gate **G8**) — the posture SPP-32 landed its own tables
in. Three arming decisions are the desk's, not this lane's:

| # | What | Cost | Why routed |
|---|---|---|---|
| **R-1** | **Arm the per-zone WIND shape.** `paths.WIND_SHAPE_DIRS["NWPP"] = RAW_DATA_DIR / "nwpp-wind-shape"` and `renewables._WIND_ZONE_SHAPE_ISOS` gains `"NWPP"` | **two lines, no new code** — the files already carry the exact schema and filename the loader composes | Both live under `src/`, outside this lane's boundary. NWPP has no keeper, so this is a membership on SPP's own precedent, not a gated flip; `_redistribute_preserving_total` preserves the footprint aggregate exactly, so it can only change WHICH ZONE holds the wind |
| **R-2** | **Decide what to do with the measured SOLAR shape.** | a design question, not a registry entry | The per-zone solar path (`_SOLAR_ZONE_SHAPE_ISOS`) builds a **clear-sky shape from EIA-860 tracking geometry and reads no file at all**. NWPP is the first region with a *measured* per-zone solar series, and whether a measured series should displace or reconcile against the geometry construction is a mechanism choice — rule 19 `[R-ONE-MECH]` says it must replace or reconcile, never stack |
| **R-3** | **Register `meanzero.NWPP_ZONAL_GAS_HUB_PATH`** (and, separately, decide on an applier) | one constant; the applier is a mechanism | `src/`. Note the 2023 caveat (§4.3) and the MIXED INLAND row (§4.1) are properties an applier inherits — they should be read before arming, exactly as SPP-32 said of its own 2025 hole |

**Not a mechanism-matrix touch (rule 28).** This lane adds no `ScenarioConfig`
field, no calibration CLI flag and no run registration, and tests no mechanism —
so there is no cell to move. A lane that executes R-1, R-2 or R-3 **does** owe the
NWPP shard a cell.

---

## 6. Files

| File | Change |
|---|---|
| `scripts/data/curate_zonal_shares.py` | **+`parse_nwpp_shares`** and its `_PARSE_FUNCS` entry. NWPP-only; no other ISO's parser touched |
| `scripts/data/build_nwpp_vre_shape.py` | **new** — the measured per-zone wind/solar shape builder |
| `scripts/data/derive_nwpp_zonal_gas_hub.py` | **new** — the per-zone gas basis derive |
| `data/raw/nwpp-wind-shape/` | **new** — 3 parquets (2023-2025) + README |
| `data/raw/nwpp-solar-shape/` | **new** — 3 parquets (2023-2025) + README |
| `data/raw/nwpp_zonal_gas_hub.csv` + `.SOURCES.md` | **new** — 15 rows, 5 zones × 3 years |
| `tests/curation/test_curate_zonal_shares_nwpp.py` | **new** — 16 tests, synthetic fixtures only (no `data/raw` read, so it runs under CI's sparse checkout) |
| `data/dictionary/schema/zonal-shares.schema.yaml` | source note: NWPP is the one regroup-not-upload source |

The zonal shares themselves land in `data/clean/zonal-shares/NWPP/` — **derived and
gitignored**, as every ISO's are. They are regenerated by
`python scripts/data/curate_zonal_shares.py --iso NWPP --year 2023 2024 2025`, and
`eia930.zonal_shares._zonal_shares_from_raw` serves the identical matrix with no
clean tree at all (verified byte-identical, all three years).

**Nothing under `src/` was modified, no ScenarioConfig field added, no other
region's rows touched, and the zone map itself (NWPP-20's) is read-only here.**

## 7. Verification run in this session

| Check | Result |
|---|---|
| `tests/curation/test_curate_zonal_shares_nwpp.py` | **16 passed** (synthetic fixtures only — no `data/raw` read, so it runs under CI's sparse checkout) |
| `tests/curation` full suite, this branch | **899 passed, 2 failed** |
| `tests/curation` full suite, base `d54cd9c5` | **883 passed, 2 failed** — the **same two** |
| `ruff check` / `ruff format --check` on every file touched | clean |
| `scripts/check_mechanism_matrix.py --base d54cd9c5` | **exit 0** — integrity OK, all four ratchets OK. No cell to move (§5) |
| Clean-parquet path vs raw-fallback path, all three years | **byte-identical** (`np.array_equal`) |

**The two failures are PRE-EXISTING and not this lane's.** Both are the same
`coal-stocks` schema drift — a `coal-stocks.schema.yaml` ships without a matching
`DATATYPE_ORDER` / `DATATYPES` entry (`test_clean_io.py::
TestRegenerateEntrypoint::test_datatype_list_matches_schemas` and
`test_data_dictionary_sync.py::DataDictionarySyncTest::test_every_schema_has_a_section`).
They reproduce identically on the base tree with this branch stashed, they name no
NWPP object, and they belong to whichever lane shipped that schema. **Routed to
NWPP-DESK to forward**, alongside the red gates NWPP-10 §3.2 and NWPP-12 §6
already routed. Stated because an honest report says which reds it left standing:
this lane did not fix them and does not claim a fully green suite.

*(An earlier run of the suite in this session also showed
`test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`
red. It is order-/`data/clean`-state dependent, not a regression: it passes in
isolation, passes with the whole zonal-share and phase3d selection, and passes in
the clean full-suite run recorded above. Recorded rather than dropped.)*

## 8. Log entry

## 2026-09-14 — NWPP-33: zonal shares, measured per-zone VRE shape, per-zone gas basis

Five zonal shares derived from the committed per-BA EIA-930 series and summing to
1.0 exactly: NW 0.376815 · EAST 0.180797 · INLAND 0.153271 · OR 0.150934 ·
SNV 0.138182 (pooled 2023-2025), reproducing NWPP-20's registered static
`load_share` to four decimals from a different code path. Because NWPP is a pool
and every zone is a whole-BA group, the regroup is an **identity**: Σ zones equals
the pool frame's own `Demand` column to **0.0 MW** in every hour of all three
years. **The 54 CHPD hours of 12-16 January 2024 survived** — the spike screen is
not applied, the dropout screen is, NWPP-NW's 2024 peak comes back at 21,560 MW in
that block, and the guard is now a test. Gates G18 / G19 / G20 held.

Per-zone VRE shape is **measured, not modelled** — the first in the repo: EIA-930
publishes wind and solar per balancing authority, so no reanalysis and **zero free
parameters**. Wind night/afternoon spread is **2.3×** (OR 1.26-1.32 nocturnal vs
SNV 0.55-0.59 afternoon) against the **7 %** contrast that justified SPP's own
per-zone shape; solar's energy-weighted peak hour runs 11.81 → 10.81 west to east,
reproducing to ±0.07 h over three years.

Per-zone gas basis from the committed per-plant EIA-923 delivered price (complete
12-month × 5-zone × 3-year coverage), minus Henry Hub, month-balanced — not a hub
proxy, because NWPP-12 established three of the four hubs have no reachable public
series. `NWPP-INLAND` is labelled **MIXED** rather than resolved to its larger half
(NWMT 1.815 vs IPCO 3.903 $/MMBtu, 2.15× inside one zone); `NWPP-EAST`'s Opal
attribution is **no longer provisional** — the audit's 1,174.1 MW of "Other" is Jim
Bridger 1-2 on Williams Gas Supply plus Hurricane City on Questar-Enbridge,
78.4 % of the zone's named gas on the Rockies. The 2023 rows are declared as
one-month-dominated by the western winter 2022-23 event, with the January-excluded
value carried on each row.

Nothing is armed: no `ScenarioConfig` field, no `src/` edit, no `cache_key`
movement. Three arming decisions routed to the desk (§5).
