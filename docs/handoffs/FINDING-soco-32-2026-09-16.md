# FINDING — SOCO-32: zonal load shares + per-zone solar shape + zonal gas hub

**Lane:** SOCO-32 · **Date:** 2026-09-16 · **Model:** Opus `claude-opus-5` ·
**Branch:** `claude/soco-32-zonal-solar-gas-t9lxas` (cut at pinned `edd40943`) ·
**Profile:** `soco` · **Charter:** `docs/multi-iso/soco-addition-plan-2026-09.md`
§5 row SOCO-32, §2.5, §3 card S3, §7 G8/G9/G17/G22 ·
**Premises:** FINDING-soco-11 §3 (the FERC-714 spine), FINDING-soco-14 (the BA
membership citations), FINDING-soco-12 §4 (gas), FINDING-soco-20 (registration).

This lane DERIVES. It arms no mechanism, adds no `ScenarioConfig` field, opens no
matrix cell, and runs no LP.

---

## 0. Result

| Deliverable | State | Headline |
|---|---|---|
| **Zonal load shares** | LANDED | Five cited FERC-714 respondents → 3 geographic zones. Annual-energy share **AL 0.3022 / GA 0.6382 / MS 0.0596** (2023), **0.2974 / 0.6450 / 0.0576** (2024), **0.2939 / 0.6493 / 0.0568** (2025). Residual vs the metered EIA-930 BA demand **3.03 / 2.92 / 1.18 %** — SOCO-11's five-respondent diagnostic, reproduced on the model clock. Southern Power (186) excluded and never re-tested |
| **Per-zone solar shape** | LANDED | New builder + three parquets from **measured all-sky irradiance at all 482 plant-years**. Reconciles to EIA-930 `NG: SUN` at **shift +0 h, r = 0.988 / 0.975 / 0.933**, energy-weighted mean hour-of-day **11.07 vs 11.05 measured**. Nothing pinned |
| **Zonal gas hub** | LANDED | 9 rows from the committed **per-plant EIA-923** series, 3 zones × 3 years, no publication hole. Mean-zero spread **0.789 / 0.467 / 0.537 $/MMBtu**. No applier armed |
| **G8** | HOLDS | `solve_surface_register.py --diff origin/main` → **0 values moved, 0 added, 0 removed**; 54 region × fuel × year renewable-shape cells hashed before/after, **3 moved and all 3 are `SOCO\|solar`** |
| **G9 / G17** | HOLD | No shared regenerated file touched; no neighbouring market's series used anywhere |
| **G22** | HONOURED | The five-respondent set is used exactly as re-ruled; the six-respondent set was not rebuilt, not evaluated and not tuned toward |

**Tests:** 51 new (19 curation + 23 solar + 9 gas), all passing. Full suites:
`tests/curation` **2 failed / 918 passed**, `tests/unit/config` + `tests/unit/data`
**6 failed / 3,183 passed**, `tests/regression/test_persisted_identity.py`
**1 failed / 23 passed** — and **every one of those 9 failures reproduces
identically with this lane's `src/` and `scripts/` changes stashed** (§5).

---

## 1. Zonal load shares — the FERC-714 spine on the model clock

### 1.1 What was built

`scripts/data/curate_zonal_shares.py` gains `_SOCO_RESPONDENT_ZONE_GROUPS`,
`_soco_utc_to_local_hoy`, `parse_soco_shares` and its `_PARSE_FUNCS` entry —
the same shape MISO's and SPP's branches have, so registering the parser once
serves **both** the clean-parquet path and the fresh-clone raw fallback
(`eia930.zonal_shares._zonal_shares_from_raw` imports `_PARSE_FUNCS` from this
script). Measured: the clean and raw paths return **byte-identical** arrays for
all three years (`np.array_equal` → True, max abs diff 0.0).

The respondent → zone map, and it is deliberately **not 1:1** (card S3 (ii)):

| FERC-714 respondent | eia_code | Zone | Basis |
|---|---:|---|---|
| 2 Alabama Power | 195 | `SOCO_AL` | operating company, Alabama |
| 183 Georgia Power | 7140 | `SOCO_GA` | operating company, Georgia |
| 184 Mississippi Power | 12686 | `SOCO_MS` | operating company, Mississippi |
| 107 Oglethorpe Power | 13994 | `SOCO_GA` | Georgia EMC G&T — SOCO-14 §1 |
| 210 MEAG Power | 13100 | `SOCO_GA` | Georgia joint-action agency — SOCO-14 §2 |
| ~~186 Southern Power~~ | 16687 | **excluded** | SOCO-14 §3, a documented NO |

### 1.2 The share table

Annual-energy share, and the residual of the five-respondent hourly sum against
the metered EIA-930 `SOCO` demand, both measured on the **model's local clock**
by the committed parser:

| Year | SOCO_AL | SOCO_GA | SOCO_MS | 714 five TWh | 930 BA TWh | residual |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0.3022 | 0.6382 | 0.0596 | 222.511 | 229.469 | **3.03 %** |
| 2024 | 0.2974 | 0.6450 | 0.0576 | 231.740 | 238.699 | **2.92 %** |
| 2025 | 0.2939 | 0.6493 | 0.0568 | 236.545 | 239.359 | **1.18 %** |

SOCO-11 §3.3 reports **3.03 / 2.92 / 1.26 %** for the same set on the source's
own UTC calendar window; the 2025 difference is the clock, not the data (the
model's local year ends 7 hours later than the UTC year — §1.4).

The shares are **hourly, not static**: each zone's share moves through the day
and the year (2023 ranges: AL 0.2554–0.3543, GA 0.5808–0.6904, MS 0.0440–0.0757).
Mississippi is the most overnight-weighted zone in every year
(night/afternoon share ratio 1.033 / 1.041 / 1.028 against Georgia's
0.996 / 0.996 / 0.999), which is the structure a static share cannot carry.

**These replace a capacity share, not another load share.** SOCO-20 registered
`load_share` = **0.3510 / 0.5842 / 0.0648**, and its own docstring says what that
is: the audit's §5 row-4 **fleet-MW share, "a fallback of last resort and NOT a
load share"**, with "SOCO-32 replaces it with the FERC-714 hourly shapes". It
does. The measured load share sits ~5 points from the capacity share on the
AL/GA pair — Georgia carries proportionally more load than fleet — which is a
real feature of the footprint, not a discrepancy to reconcile.

### 1.3 An independent cross-check the charter did not ask for

The share construction is new, so it is worth testing against a source that is
not FERC-714 at all. **EIA-861 2024 retail sales coded `BA = SOCO`**
(`Sales_Ult_Cust_2024.xlsx`, sheet *States*, `f8612024.zip`, fetched 2026-09-16),
mapped to zones by the same FIPS-state rule:

| Zone | EIA-861 2024 TWh | EIA-861 share | this lane's 714 share | gap |
|---|---:|---:|---:|---:|
| SOCO_AL | 65.814 | 0.2942 | 0.2974 | −0.32 pt |
| SOCO_GA | 146.143 | 0.6533 | 0.6450 | +0.83 pt |
| SOCO_MS | 11.743 | 0.0525 | 0.0576 | −0.51 pt |

**Max 0.83 points, from a different EIA survey on a different basis** (retail
sales vs planning-area demand; the latter adds losses and wholesale-requirements
service, which is why its total is higher). The same source also corroborates
the two contested zone assignments directly:

* **Oglethorpe → Georgia.** Georgia **cooperative** retail sales coded `BA=SOCO`
  are **41.463 TWh** in 2024 against respondent 107's **45.339 TWh** of
  planning-area demand — a +9.3 % gap, the size losses and own-use should be.
* **MEAG → Georgia.** Georgia **municipal** retail sales coded `BA=SOCO` are
  **13.389 TWh** against respondent 210's **13.902 TWh** — **+3.8 %**.

Neither entity has a service territory of its own in EIA-861 (G&T co-ops and
joint-action agencies do not), which is exactly why SOCO-11 could not attribute
their counties; this is the load-side arithmetic that closes the same question
from the other end.

### 1.4 The 7 uncovered hours of 2025, and why they are filled rather than refused

The committed 714 pull is bounded on **UTC** (ends 2025-12-31T23) while SOCO's
2025 **local** year ends at 2026-01-01T06 UTC, so the last **7 hour-ending
Central labels** of 2025 have no filing. This is not a second defect: it is the
*same* boundary the EIA-930 extract has, counted in
`docs/multi-iso/soco-data-audit.md` §3.2 — the identical 7 rows spill off the
front into local-date 2022-12-31.

Those 7 hours (**0.080 % of the year**) take the previous hour's **share**
through the shared `_hourly_shares_from_groups` back-fill, and the parser
**announces it** in the run log. A gap larger than the clock offset is refused
and the year degrades to `None`.

Audit §3.2 calls holding-forward WRONG, and it is right — **about the demand
series**. This is a different object: a share is an allocation fraction, and the
MW those hours dispatch come from the EIA-930 series and its own declared bridge,
not from here. The real alternative was never "7 measured hours" (no filing
exists on either side) but dispatching **the whole year** on the flat static
fallback — the miso-251 defect rule 14 `[R-ACCURATE]` exists to stop. The
durable fix is audit §3.2's own and is **routed** (§6, R-1): re-fetch both series
bounded on local time, after which the fill never fires.

2024 additionally carries one interior single-respondent gap (Oglethorpe, hour
1631), repaired by the per-respondent ffill every sibling parser already applies
— without it that hour would drop ~5 GW out of Georgia's total.

### 1.5 The gates

| Gate | Result |
|---|---|
| Shares sum to 1.0 every hour | max deviation **3.3e-16** (2023), 2.2e-16 (2024, 2025) |
| Redistribution identity | `Σ_z shares × system − system` max **< 1e-9** by test; measured 0.0 on the committed years |
| Bounded, finite | min share 0.0429, max 0.7064; no NaN |
| Clean == raw fallback | **byte-identical**, all three years |
| Live through `load_demand` | 3 zones × 8760 for all three years; system TWh 239.6 / 249.5 / 252.6 (demand + net export + losses) |

### 1.6 Card S3 was not re-litigated

The six-respondent set has the **smaller** residual (1.63 / 1.50 / **−0.03** %)
and was **not** built, not scored and not used. The code comment carries the
reason where the next reader will hit it, and
`test_southern_power_186_is_excluded` pins it with the reasoning in its
docstring: a cited basis beats a smaller residual (rules 1 `[R-STRUCT]` /
13 `[R-MEASURED]`), and the six-set's negative 2025 residual is the overshoot
SOCO-11's PowerSouth + Tallahassee falsifier was built to detect. No share, no
threshold and no parameter in this lane was chosen by looking at a residual.

---

## 2. Per-zone solar shape — measured irradiance, because the clear-sky path cannot

### 2.1 Why a new dataset rather than the existing solar path

The repo's per-zone SOLAR path (`renewables._solar_zone_clearsky_shapes`, armed
for CAISO) is keyed on **latitude** and its own docstring records that longitude
and the equation of time are *deliberately omitted* because "a constant timing
offset shared by all zones cancels". For a north–south stack that holds. SOCO's
zones are separated **east–west**:

| Zone | solar-fleet centroid lon | lat | single-axis | fixed | dual-axis |
|---|---:|---:|---:|---:|---:|
| SOCO_GA | −83.63 | 31.96 | 81.3 % | 14.3 % | 4.4 % |
| SOCO_AL | −86.35 | 31.28 | 69.7 % | 30.3 % | — |
| SOCO_MS | −89.16 | 31.45 | 84.2 % | 15.8 % | — |

**5.53° of longitude = 22.1 minutes of solar time**, against 0.68° of latitude.
One latitude-keyed shape puts all three zones' peak in the same model hour.

### 2.2 What was built

`scripts/data/build_soco_solar_shape.py` →
`data/raw/soco-solar-shape/soco_{2023,2024,2025}_solar_zone_shape.parquet`
(+ README/SOURCES). Per **generator**: NASA POWER hourly all-sky DNI and diffuse
at the plant's own coordinates, transposed onto the generator's **filed EIA-860
tilt and azimuth** by the same three tracking-class geometries
`_clearsky_poa_by_tech` uses, capacity-weighted into zones. 482 point-years
fetched (154 / 163 / 165 distinct coordinates), memoised under a gitignored
`data/clean/` cache.

**It costs fewer free parameters than the clear-sky path, not more** (rules 21
`[R-DOF]` / 24 `[R-REGISTRY]`): the measured DNI replaces the Meinel attenuation
pair (`_CLEARSKY_TRANSMITTANCE`, `_CLEARSKY_AM_EXPONENT`), the measured diffuse
replaces `_DIFFUSE_FRACTION`, and EIA's filed array angles replace the
tilt-at-latitude convention — **which EIA publishes for 100 % of fixed-tilt
nameplate MW in all three zones**, so the convention survives only as a fallback
that never fires on the committed fleet. Nothing new is introduced.

Omitted, with the measurement that makes each second-order: inverter clipping
(DC:AC 1.367 / 1.382 / 1.401 — a 2.5 % spread, near common-mode) and the
cell-temperature / ground-reflected terms (each would need a coefficient to
invent; both common-mode across three zones of one climate at ~20° of tilt).

### 2.3 Reconciliation — a check, never a channel

`--reconcile` correlates the capacity-weighted footprint shape against the
measured EIA-930 `NG: SUN` over −3…+3 h and prints the result. **No committed
value depends on it.**

| Year | best shift | r | r at −1 / +1 h | mean hour-of-day built vs measured |
|---|---:|---:|---:|---|
| 2023 | **+0 h** | 0.9878 | 0.9364 / 0.9313 | 11.07 vs **11.05** |
| 2024 | **+0 h** | 0.9753 | 0.9237 / 0.9182 | 11.08 vs **11.06** |
| 2025 | **+0 h** | 0.9331 | 0.8824 / 0.8763 | 11.07 vs **11.07** |

A sharp single peak at zero in every year: NASA POWER's hour-**beginning** UTC
stamp maps onto the model's hour-**ending** clock with the +1 h offset the
builder applies, and nothing further. The hour-of-day agreement to **≤ 0.02 h**
is an unpinned coincidence of two independent constructions.

**2025's r is the weakest and is reported, not repaired.** It is also the year
whose EIA-930 extract is 7 hours short and whose `NG: SUN` cell carries the most
reporting noise (audit §3.2–§3.3). Nothing was tuned toward it.

### 2.4 What the shape actually says

| Statistic | SOCO_GA | SOCO_AL | SOCO_MS |
|---|---:|---:|---:|
| energy-weighted mean hour-of-day (2023 / 24 / 25) | 11.026 / 11.033 / 11.024 | 11.246 / 11.283 / 11.268 | 11.392 / 11.382 / 11.368 |
| morning(07–10)/afternoon(13–16) | 1.256 / 1.233 / 1.233 | 1.136 / 1.100 / 1.105 | 1.071 / 1.072 / 1.079 |
| peak(11–13)/shoulder(08–10,14–16) | 1.296 / 1.271 / 1.264 | **1.333 / 1.331 / 1.312** | 1.319 / 1.265 / 1.271 |

Two independent signatures, both in the direction geography predicts and stable
across three years:

* **east→west timing.** The GA↔MS mean-hour gap is **0.366 / 0.349 / 0.344 h**
  against the **0.369 h** a 5.53° span predicts from solar geometry alone — the
  builder reproduces the pure-geometry prediction to ~0.02 h without being told
  it;
* **mounting.** Alabama is the peakiest zone in every year, carrying twice
  Georgia's fixed-tilt share.

Size: normalised zone shapes correlate **GA↔MS r = 0.90 / 0.90 / 0.91**, with
**3,508 / 3,488 / 3,402 hours a year** (≈ 40 %) more than 10 % apart.

### 2.5 What arming it does, measured end-to-end

Through `load_renewable_profiles`, armed vs the same call with the membership
removed:

| Year | system hourly max \|Δ\| | system TWh armed / flat | annual TWh moved (AL / GA / MS) | hourly max \|Δ\| by zone |
|---|---:|---|---|---|
| 2023 | **1.4e-12 MW** | 8.362168 / 8.362168 | −0.013 / +0.013 / −0.000 | 296 / 388 / 110 MW |
| 2024 | **1.8e-12 MW** | 10.126767 / 10.126767 | −0.029 / +0.044 / −0.015 | 259 / 372 / 152 MW |
| 2025 | **2.7e-12 MW** | 9.985204 / 9.985204 | −0.026 / +0.043 / −0.017 | 251 / 412 / 217 MW |

The system series is preserved at machine precision — six orders inside the 1e-9
gate — while up to **412 MW** moves between zones in an hour (48 % and 69 % of
the AL and MS zone capacities at the extreme). The mechanism is live and it
cannot touch ISO-wide solar energy.

Stated plainly, as card S3 (iii) requires: with the Tier-3 links non-binding
this changes no dispatch today. It is landed because it is the structurally
correct input (rule 1 `[R-STRUCT]`), and it becomes load-bearing the moment
SOCO-54 derives a binding TTC.

### 2.6 Solar, not wind — verified

SOCO's EIA-860 operable fleet carries **0 wind generators / 0.0 MW**, and the
EIA-930 `SOCO` extract reports `NG: WND` as **exactly 0.0 in all 26,257 hours it
publishes** for 2023–2025 (the column exists; it is zero, not null). There is no
series to shape.

---

## 3. Zonal gas hub

### 3.1 The committed table

`data/raw/soco_zonal_gas_hub.csv` (+ `.SOURCES.md`), derived by
`scripts/data/derive_soco_zonal_gas_hub.py` on the shared five-column schema, so
`meanzero._zonal_gas_basis_by_zone` reads it with no new parsing code.

| Zone | 2023 | 2024 | 2025 | Hub |
|---|---:|---:|---:|---|
| SOCO_AL | +0.955 | +0.860 | +0.757 | **MIXED**: SNG / Transco Z4 (AL) + FL-panhandle delivered |
| SOCO_GA | +0.539 | +0.706 | +0.871 | SNG / Transco Z4 (GA, Dalton lateral) |
| SOCO_MS | +0.166 | +0.393 | +0.334 | SNG / Transco Z4 (MS) |

Equal-weight mean-zero spread — what an armed applier would actually see —
**0.789 / 0.467 / 0.537 $/MMBtu**.

### 3.2 Why EIA-923 per-plant and not SOCO-12's state series

SOCO-12 committed the `N3045{AL,GA,MS}3` state series and left the zone mapping
explicitly to this lane. Rule 14 `[R-ACCURATE]` decided it, on two measured
grounds and no residual:

1. **The state boundary is not the zone boundary for `SOCO_AL`.** Card S3 puts
   the six SERC Florida-panhandle plants in `SOCO_AL`. The two that burn gas —
   Gulf Clean Energy Center (641) and Lansing Smith (643), **54.3 TBtu/yr,
   20–25 % of the zone's burn** — pay **+1.768 / +1.767 / +1.629** $/MMBtu
   against the Alabama plants' **+0.700 / +0.603 / +0.556**: a persistent
   **~$1.10/MMBtu premium** on a delivered market an Alabama state series cannot
   see. This is rule 14's own "defined on a different boundary than our zones".
2. **The state series stops before the backcast does.** EIA publishes nothing for
   **GA or MS after 2024-12**, so a state-series table would end in 2024 and
   hand 2025 either no basis or — worse — an AL-only row letting two zones
   default to `0.0` and fabricating a ~$0.75/MMBtu spread out of a publication
   gap. That is the trap SPP-32 refused for SPP-South.

**The cross-check that validates the route** (`--cross-check`): where the zone
boundary *is* the state line the two routes agree to **≤ 0.044 $/MMBtu**
(GA 2023 −0.044, 2024 +0.034; MS −0.028, −0.028) once the state series' `$/Mcf`
is converted at 1.037 MMBtu/Mcf. AL diverges by 0.52 / 0.34 / 0.20, decomposed
rather than asserted: the FL panhandle explains **0.26 / 0.26 / 0.20** of it, and
a residual **0.23 / 0.05 / −0.02** remains in which EIA's two products simply
disagree for Alabama, almost entirely in 2023 — reported, not resolved (§6, R-3).

### 3.3 Wiring, and what it is not

`SOCO_ZONAL_GAS_HUB_PATH` is registered in
`src/market_sim/data/fuel/basis/meanzero.py` beside its six siblings and
re-exported from `data/fuel/__init__.py`. **No applier is armed** — no
`ScenarioConfig` field, nothing reads the table in a solve, no cache key moves.

There is **no traded Southeast index** to use instead, and that is measured, not
assumed: SOCO-12 §4 swept both free EIA routes (no Southeast row in the Weekly
Update spot table; no Southeast region on the daily map) and returned a
documented NO. The `hub` column names the transport system — Southern Natural
Gas (50 % Southern Company Gas, 10-K FY2025 Item 1) and Transco into northwest
Georgia via the jointly-owned Dalton lateral (10-K Item 2 note (e)) — and the
value beside it is the measured delivered price, never a quote. Gate **G17** is
untouched: no neighbouring market's series appears anywhere in this lane.

**A charter-name divergence, declared.** The charter names
`src/market_sim/data/fuel/hubs.py` for this wiring. The zonal-hub path constants
have lived in `data/fuel/basis/meanzero.py` since the W-D3 split, and that is
where SPP-32's own table landed, so this lane followed the code. `hubs.py` needs
**no** SOCO entry: it is data-keyed on `gas_basis_by_iso_month.csv`, an absent
region falls through, and SOCO has no row there because SOCO-12 established that
no free daily source exists behind a winter overlay. Adding a SOCO branch there
would be inventing a mechanism, not wiring one.

---

## 4. G-DRIFT — every hunk, and the measurement behind the classification

13 hunks across 5 files. **Classification is not asserted**: 54 region × fuel ×
year cells of `_zone_renewable_shapes` were hashed on this tree and on the same
tree with `src/` and `scripts/data/curate_zonal_shares.py` stashed.

> **54 cells compared · 3 moved · all 3 `SOCO|solar`.** Every one of the eight
> incumbent regions is hash-identical on both fuels in 2023, 2024 and 2025.

And on the registry surface that reaches cache keys:

> `scripts/solve_surface_register.py --diff origin/main` →
> **305 → 305 names; 0 values moved, 0 added, 0 removed.**
> "NO VALUE MOVED — no ISO's key is reached by a registry change."

| # | File | Hunk | INERT for ERCOT / CAISO / MISO / PJM / NYISO / NEISO / SPP / NWPP because |
|---|---|---|---|
| H1 | `renewables.py` | `solar_shape_dir` import | An import binds a name; no call site changes. Byte-identical module behaviour until H3 is reached |
| H2 | `renewables.py` | `_SOLAR_ZONE_REANALYSIS_ISOS = frozenset({"SOCO"})` + comment | A **membership set of one**. The only reader is H3, whose first two guards are `fuel != "solar"` and `iso not in` this set. Pinned by `test_no_other_region_is_registered` |
| H3 | `renewables.py` | `_solar_zone_reanalysis_shapes()` (new function) | New symbol, one caller (H4). Returns `None` for every non-member region before touching the filesystem. Measured: `None` for all 8 regions × 3 years |
| H4 | `renewables.py` | `_zone_renewable_shapes` solar branch + docstring | Adds a **pre-step** that returns `None` for all 8, then falls through to the unchanged `_solar_zone_clearsky_shapes` call. CAISO still returns its clear-sky `(6, 8760)`; the other 7 still return `None` — hash-identical |
| H5 | `paths.py` | `SOCO_SOLAR_SHAPE_DIR`, `SOLAR_SHAPE_DIRS`, `solar_shape_dir()` | New constants and a new accessor; **nothing else reads them**. `paths.py` is not in `solve_surface.SURFACE_MODULES`, so it cannot reach any cache key. NWPP's committed `nwpp-solar-shape` is deliberately **not** registered — arming it is NWPP-DESK's call (rule 25) |
| H6 | `fuel/basis/meanzero.py` | `SOCO_ZONAL_GAS_HUB_PATH` + comment | A path constant beside six siblings. No applier reads it; no existing constant, loader or applier is touched. Sibling test file passes unchanged |
| H7 | `fuel/__init__.py` | re-export + `__all__` entry | Namespace only |
| H8–H13 | `curate_zonal_shares.py` | SOCO crosswalk, `_SOCO_FERC714_FILE`, `_SOCO_DEMAND_COLUMN`, `_SOCO_MAX_UNCOVERED_HOURS`, `_soco_utc_to_local_hoy`, `parse_soco_shares`, `_PARSE_FUNCS["SOCO"]`, module docstring | Every symbol is SOCO-keyed and new. The dispatch table gains one key; the eight existing keys and their parsers are untouched, and the full `tests/curation` suite passes identically |

`tests/regression/test_persisted_identity.py`: **23 passed**, 1 pre-existing
failure (§5).

---

## 5. Every test failure carries a same-tree control

Run on this tree, then re-run with `src/market_sim` and
`scripts/data/curate_zonal_shares.py` stashed (main's code, this lane's data and
tests in place):

| Failure | This tree | Control | Attributable to SOCO-32? |
|---|---|---|---|
| `test_persisted_identity::test_solve_surface_fingerprint_is_pinned[NYISO]` | FAIL | **FAIL** | No |
| `test_clean_io::test_datatype_list_matches_schemas` | FAIL | **FAIL** | No |
| `test_data_dictionary_sync::test_every_schema_has_a_section` | FAIL | **FAIL** | No |
| `test_mechanism_matrix_keeper_stamp` ×2 (NYISO) | FAIL | **FAIL** | No |
| `test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact` | FAIL | **FAIL** | No |
| `test_fleet::test_neiso_includes_mystic_cc` | FAIL | **FAIL** | No |
| `test_gas_offer_zonal_anchor_vintage` ×2 (NYISO) | FAIL | **FAIL** | No |
| `test_consume_phase3d::test_zone_lookup_matches_raw` | FAIL **once**, then passes | passes | No — cold-start (`data/clean` being written by this session's first curation run); plan §7 gate **G18** names exactly this. Passes standalone and on a second full run |

**HEAD == `origin/main` == `edd40943`**, so these are main's failures, not a
stale base. The NYISO solve-surface one is worth naming precisely because it is a
live guard that is currently disarmed: main's surface reads
`bd2b4657f9b5df7e` (210 rows) against the pinned `1eefed492204fab7` (209) — the
nyiso-235 promotion added a registry row without advancing the pin's dated cause
block, which is the ledger entry that test exists to demand. Routed, not fixed
(NYISO's lane owns it; rule 25 and §8.0 rule 1).

---

## 6. Routed to SOCO-DESK

| # | Item | Why it is not this lane's |
|---|---|---|
| **R-1** | **Re-fetch the FERC-714 parquet and the EIA-930 `SOCO` extract bounded on LOCAL time** (or extend both by 7 UTC hours). Both files end at 2025-12-31T23 UTC, 7 hours short of the model's 2025 local year; audit §3.2 names this and prefers the re-fetch. Doing it retires `_SOCO_MAX_UNCOVERED_HOURS` entirely | `data/raw/zone-specific-demand/SOCO/` and `eia-930-hourly/` are SOCO-11's files, not this lane's |
| **R-2** | **The static `load_share` in `_soco_config` is still the fleet-MW fallback** (0.3510 / 0.5842 / 0.0648). The measured load shares now exist (0.2978 / 0.6442 / 0.0580, three-year mean) and the hourly path uses them; the fallback only fires if the clean parquet AND the raw file are both absent. Re-keying it is a one-line `iso_configs.py` edit with a real basis | `iso_configs.py` is SOCO-20's file; a static-share edit is a topology-adjacent change, and the docstring explicitly reserves it |
| **R-3** | **EIA-923 and the EIA state delivered series disagree for Alabama 2023 by 0.23 $/MMBtu** (0.05 in 2024, −0.02 in 2025) even over all of Alabama, with the FL-panhandle effect already removed. Both are EIA products; neither is obviously right | A level question about EIA's own aggregation, with no bearing on this lane's zone-attribution argument and no consequence under a mean-zero applier |
| **R-4** | **The sibling hub tables carry a ~3.5 % unit bias.** MISO / PJM / SPP subtract a `$/MMBtu` Henry Hub from a `$/Mcf` state series. Measured here: the heat-content-**converted** series is the one that reconciles with EIA-923 (≤0.044 $/MMBtu), the raw one is 0.10–0.13 off. SOCO's table needs no conversion (EIA-923 is natively `$/MMBtu`) and is unaffected | Rule 25 `[R-ISO-SCOPE]`: those are other regions' tables |
| **R-5** | **`test_persisted_identity` is red on main** for NYISO's solve-surface pin (§5) | NYISO's lane owns the pin and the cause block it must carry |
| **R-6** | **NWPP's committed `nwpp-solar-shape` parquets now have a consumer** — this lane's reader would serve them the moment NWPP joins `_SOLAR_ZONE_REANALYSIS_ISOS` and `SOLAR_SHAPE_DIRS`. NWPP-33 routed arming to NWPP-DESK; worth telling them the path exists | Another region's arming decision (rule 25) |

---

## 7. Files

**New:** `scripts/data/build_soco_solar_shape.py` ·
`scripts/data/derive_soco_zonal_gas_hub.py` ·
`data/raw/soco-solar-shape/{README.md, SOURCES.md, soco_{2023,2024,2025}_solar_zone_shape.parquet}` ·
`data/raw/soco_zonal_gas_hub.csv` · `data/raw/soco_zonal_gas_hub.SOURCES.md` ·
`tests/curation/test_curate_zonal_shares_soco.py` ·
`tests/unit/data/test_soco_solar_shape.py` ·
`tests/unit/data/test_soco_zonal_gas_hub.py` · this FINDING.

**Modified:** `scripts/data/curate_zonal_shares.py` ·
`src/market_sim/config/paths.py` · `src/market_sim/data/renewables.py` ·
`src/market_sim/data/fuel/basis/meanzero.py` ·
`src/market_sim/data/fuel/__init__.py`.

**Derived, gitignored:** `data/clean/zonal-shares/SOCO/zonal-shares_{2023,2024,2025}.parquet`
(regenerate: `python scripts/data/curate_zonal_shares.py --iso SOCO --year 2023 2024 2025`) ·
`data/clean/solar-shape-irradiance/` (the NASA POWER memo, 482 point-years).

**Not touched:** `ScenarioConfig` · `results/cache.py` · any other region's rows,
branches, keeper shard, log or matrix shard · `frontend/data/**` · the mechanism
matrix (this lane arms nothing; shape membership is an INPUT, not a lever —
rule 28).

---

## Log entry

```
### soco-32 — 2026-09-16 — zonal load shares + per-zone solar shape + zonal gas hub

Three W3 derives landed; nothing armed, no ScenarioConfig field, no LP.

ZONAL SHARES. scripts/data/curate_zonal_shares.py gains the SOCO branch on the
FIVE cited FERC-714 respondents (AP 2, GP 183, MP 184, Oglethorpe 107, MEAG 210;
Southern Power 186 EXCLUDED per card S3 as re-ruled r#5). Annual-energy share
AL 0.3022 / GA 0.6382 / MS 0.0596 (2023), 0.2974/0.6450/0.0576 (2024),
0.2939/0.6493/0.0568 (2025); residual vs metered EIA-930 BA demand 3.03/2.92/
1.18% on the model clock (SOCO-11 reports 3.03/2.92/1.26% on the source's UTC
window -- the 2025 difference is the clock). Shares sum to 1.0 at 3.3e-16, clean
== raw fallback byte-identical, redistribution identity < 1e-9. The map is
deliberately NOT 1:1: both Georgia wholesale respondents join Georgia Power in
SOCO_GA, and that assignment is cross-checked from a different survey -- EIA-861
2024 retail sales coded BA=SOCO give zone shares 0.2942/0.6533/0.0525 (max 0.83
pt from the 714 shares), GA cooperative retail 41.463 TWh vs Oglethorpe's 45.339
TWh of planning-area demand (+9.3%, the size losses should be), GA municipal
13.389 vs MEAG's 13.902 (+3.8%). The six-respondent set was NOT built, scored or
tuned toward; a test pins the exclusion with the reasoning.
2025's last 7 hours have no filing on EITHER side (both fetches were bounded on
UTC; audit §3.2 counts the identical 7 rows spilling off the front into 2022):
their SHARES carry from the previous hour, announced in the log, and a gap larger
than the clock offset refuses the year. The MW come from the 930 series, not from
here. Re-fetching both bounded on local time is routed (R-1).

SOLAR SHAPE. NEW scripts/data/build_soco_solar_shape.py -> data/raw/
soco-solar-shape/soco_{2023,2024,2025}_solar_zone_shape.parquet + README/SOURCES.
Measured NASA POWER all-sky DNI+diffuse at every operable solar plant (482
point-years), transposed onto each generator's FILED EIA-860 tilt/azimuth (EIA
publishes one for 100% of fixed-tilt MW in all three zones) by the same three
tracking-class geometries _clearsky_poa_by_tech uses. It costs FEWER free
parameters than the clear-sky path: measured DNI replaces the Meinel pair,
measured diffuse replaces _DIFFUSE_FRACTION, filed angles replace
tilt-at-latitude. The clear-sky path cannot serve SOCO because it omits
longitude by design and SOCO's zones are separated EAST-WEST (centroids -83.63
GA / -86.35 AL / -89.16 MS = 22.1 minutes of solar time).
Reconciliation (a check, never a channel): best shift +0 h in all three years,
r = 0.9878 / 0.9753 / 0.9331, energy-weighted mean hour-of-day built 11.07/11.08/
11.07 vs measured 11.05/11.06/11.07. Per-zone mean hour GA 11.02 < AL 11.27 <
MS 11.37 every year, and the GA-MS gap (0.366/0.349/0.344 h) reproduces the
0.369 h pure-geometry prediction to ~0.02 h. AL is the peakiest zone (2x
Georgia's fixed-tilt share). Armed end to end: system series preserved at
1.4e-12 MW while up to 412 MW moves between zones in an hour. 2025's weaker r is
reported, not repaired. No wind shape: SOCO has 0 wind generators and NG: WND is
exactly 0.0 in all 26,257 published hours.

GAS HUB. data/raw/soco_zonal_gas_hub.csv (9 rows) + .SOURCES.md, derived by NEW
scripts/data/derive_soco_zonal_gas_hub.py from the COMMITTED per-plant EIA-923
Schedule 2 series (the NWPP-33 construction), NOT SOCO-12's state series -- two
measured reasons, no residual: (a) card S3 puts the FL-panhandle plants in
SOCO_AL and the two that burn gas are 20-25% of the zone's burn at +1.77/+1.77/
+1.63 vs the Alabama plants' +0.70/+0.60/+0.56 $/MMBtu, a market an AL state
series cannot see; (b) EIA publishes no GA or MS series after 2024-12, so a
state-series table would end mid-backcast or fabricate a spread out of a
publication gap. Where the zone boundary IS the state line the routes agree to
<=0.044 $/MMBtu. Basis AL 0.955/0.860/0.757, GA 0.539/0.706/0.871, MS 0.166/
0.393/0.334; mean-zero spread 0.789/0.467/0.537 $/MMBtu. SOCO_ZONAL_GAS_HUB_PATH
registered in fuel/basis/meanzero.py (the charter said hubs.py; the constant
family moved there at the W-D3 split, which is also where SPP-32's landed).
NO APPLIER ARMED.

G8 / G-DRIFT. 54 region x fuel x year renewable-shape cells hashed with and
without this lane's src changes: 3 moved, all 3 SOCO|solar; all eight incumbent
regions hash-identical. solve_surface_register.py --diff origin/main: 305 -> 305
names, 0 values moved. paths.py, renewables.py and meanzero.py are not in
SURFACE_MODULES, so no cache key is reachable.

TESTS. 51 new (19 curation + 23 solar + 9 gas), all passing. tests/curation 2
failed/918 passed; tests/unit/config + tests/unit/data 6 failed/3,183 passed;
test_persisted_identity 1 failed/23 passed -- and all 9 reproduce identically
with this lane's src/ stashed (same-tree control, HEAD == origin/main ==
edd40943). Named: the NYISO solve-surface pin is red ON MAIN (live
bd2b4657f9b5df7e / 210 rows vs pinned 1eefed492204fab7 / 209) because the
nyiso-235 promotion did not advance the pin's cause block -- routed, not fixed.

ROUTED: R-1 re-fetch both SOCO series bounded on local time (retires the 7-hour
fill); R-2 re-key _soco_config's static load_share from the fleet-MW fallback to
the measured 714 shares (0.2978/0.6442/0.0580 three-year mean); R-3 EIA-923 vs
the EIA state series disagree for Alabama 2023 by 0.23 $/MMBtu, both EIA;
R-4 the MISO/PJM/SPP hub tables carry a ~3.5% $/Mcf-vs-$/MMBtu unit bias (SOCO's
does not); R-5 test_persisted_identity red on main (NYISO); R-6 NWPP's committed
solar parquets now have a consumer if NWPP-DESK wants to arm them.
```
