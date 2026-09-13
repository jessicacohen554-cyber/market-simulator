# FINDING — lane NWPP-10 (Phase-0 data audit + registry-values table + protocol correction)

Lane **NWPP-10** · 2026-09-13 · branch `claude/nwpp-10-audit-raq015` · base sha **`4d9c3251`**
· MODEL Opus `claude-opus-5` · DATA PROFILE `shared`.

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-10 / §8 prompt pack.
Deliverable: `docs/multi-iso/nwpp-data-audit.md` (NEW) + two corrections. **Zero solves, zero
mechanisms tested, zero matrix cells moved, nothing under `src/`, `scripts/`, `configs/`,
`tests/`, `frontend/` or `data/` touched.**

---

## 0. What this lane did and did not do

**Did:** measured the NWPP footprint off committed EIA-860 and EIA-930 artifacts; adjudicated
the TRE row and two the charter had not found; resolved the curated-fleet seam with an
unambiguous recommendation; established the demand-column and time conventions; measured
seasonal peaking per candidate zone; computed the CEMS coverage arithmetic; built the
registry-values table; recommended (did not decide) a zoning.

**Did not:** decide topology, set any parameter, derive anything (rule 23 `[R-FROZEN-DERIVE]`),
fetch any external document (that is NWPP-11/12/13's region — §8.0 collision rule 5), or write
to any shared record. The record is this FINDING plus the audit doc.

---

## 1. Result — the four the charter asked for FIRST

### 1.1 The census — headline CONFIRMED, three technology rows CORRECTED

| Measure | Charter | Measured | |
|---|---:|---:|---|
| Plant-table rows carrying a footprint BA | 1,082 | **1,082** | ✅ |
| Plants with ≥ 1 operable generator | 940 | **940** | ✅ |
| Operable generators | 1,932 | **1,932** | ✅ |
| Nameplate | 98,738.1 MW | **98,738.1 MW** | ✅ |
| Hydro / plants / ≥1 GW | 35,799.5 / 288 / 17,821.8 | **identical** | ✅ |
| Nuclear · coal (units) · Electric Utility MW | 1,200.0 · 8,910.2 (32) · 68,860.0 | **identical** | ✅ |
| Per-BA, per-state tables | — | **confirmed**, except **MT 6,939.6** (charter 6,940.4) | 1 correction |
| Gas ST · gas ICE · solar PV | 2,163.0 · 732.7 · 10,049.9 | **2,393.0 · 737.5 · 10,051.3** | **3 corrections** |

The three technology deltas sum to +236.2 MW and come out of the charter's elided "other"
residual (365.7 → a measured **129.5 MW** over four technologies); the **total is unchanged**.
New: summer 92,199.2 MW, winter 96,596.1 MW; the full EIA-860 planned-retirement table (the
charter quotes one row of it — there are seven cohorts, including 230.0 MW of gas ST dated 2028
and 593.3 MW of gas CC dated 2043); and the coal detail correcting *"five units < 60 MW"* to
**five plants / eleven units**.

### 1.2 The TRE adjudication — **REJECTED**, on a two-key interconnection test

Plant **68906 "Pine Forest Solar I"** · Hopkins County **TX** (33.100779 N, −95.392287 W) ·
NERC **TRE** · BA `DOPD` (*PUD No. 1 of Douglas County*) · `PFBA` 200.0 MW Batteries +
`PFPV` 300.0 MW Solar PV = **500.0 MW**, COD 2025 · T&D owner *4 Rivers Electric Cooperative*
(KS) · 345 kV.

**The rule applied:** a plant self-reporting a NWPP BA code is admitted only when **both**
(i) `NERC Region == "WECC"` **and** (ii) its coordinates fall inside the Western
Interconnection. Key (i) is **dispositive on physics**: ERCOT and the Western Interconnection
are **asynchronously separated** — no generator is inside both — so a Washington PUD cannot
balance a resource in ERCOT. Key (ii) corroborates: ~1,900 km, and every independent locator in
the same committed row agrees against the single BA-code field, which is a respondent-entered
free field. Cost of rejection: 500.0 MW (0.51 %) and 2 of 1,932 generators. Post-adjudication
footprint: **939 plants / 1,930 generators / 98,238.1 MW**.

**Two more rows the charter did not name**, both found by the same sweep:

- **Sand Creek Wind Farm (60595)**, McCone County MT, NERC **MRO**, BA `WAUW` — **NOT a
  defect.** WAPA Upper Great Plains West genuinely straddles the Eastern/Western seam through
  eastern Montana (Fort Peck, same county, is WECC). The row is **canceled** and holds zero
  operable generators, so it is inert — but it proves key (i) is doing real work for WAUW, not
  just catching a typo, and a future Eastern-side WAUW addition must not enter the LP.
- **Desert Bloom (69290)**, Maricopa County **AZ**, WECC, BA `DOPD` — **passes** the predicate
  and is caught only by geography. Proposed-only today (150.0 MW batteries, status `V`), so
  inert — **live the moment it enters service.** `DOPD`'s three plant rows are Wells (real),
  Pine Forest (defect) and Desert Bloom (AZ): two of three are suspect, which reads as a
  respondent-side problem at that utility rather than three unrelated slips.

**Recommendation to NWPP-20:** encode the predicate (`BA ∈ NWPP_BAS AND NERC == "WECC"`), not a
per-plant exclusion (which would be an off-registry dict, rule 24 `[R-REGISTRY]`), and consider
extending it with a Western-Interconnection bounding test for the Desert Bloom class.

### 1.3 The defect-screen convention — and a screen that would destroy a real annual peak

The charter's **30 artifact hours are confirmed exactly** (AVA 10, NWMT 11, NEVP 6, PACE 1,
SCL 2), including AVA **810,948 MW** at 2025-10-12 10:00 UTC and **−58,286 MW** at 2024-01-05
16:00. `Demand (MW) (Adjusted)` repairs all 30 and reproduces the charter's cleaned peaks
**49,290 / 52,564 / 50,953 MW to the MW**.

**But the same screen flags 84 hours, not 30, and the other 54 are real load.** They are all
CHPD, all 12–16 January 2024, and `Adjusted` leaves every one **byte-identical to raw** — EIA's
own verdict. The daily maxima trace a cold snap (408 → 524 → 583 → 573 → 572 → 560 → 487 → 433),
the block contains **CHPD's annual peak (583 MW) and the whole NWPP-NW zone's 2024 annual peak
(21,560 MW at 2024-01-13 19:00 UTC)**, and CHPD's peak/median ratio is **2.29 / 2.83 / 2.50**.
The `_screen_demand_spikes` docstring justifies its 2.5 factor on the claim that *"every
legitimate demand series has max/median ≤ 2.1"* — **falsified here by CHPD in all three years
and by NEVP (2.20–2.37) as well.** Applying it would delete a documented regional cold snap and
interpolate over it: a rule-14 `[R-ACCURATE]` violation by construction.

**THE CONVENTION established (audit §4.4):**
1. **`Demand (MW) (Adjusted)` is the series every downstream NWPP demand read uses.**
2. **Do NOT apply `_screen_demand_spikes` on top for NWPP.** If a belt-and-braces screen is
   wanted, the admissible form is the **fuel-series two-statistic test** (`> 2.5 × median`
   **AND** `> 2.5 × p99.9`, `data/eia930/actuals.py`), which passes all 54 CHPD hours and still
   catches all 30 artifacts. Recommended; NWPP-20 decides.
3. **`_screen_demand_dropouts` IS needed** — **17 exactly-zero NEVP demand hours in 2025**
   survive into the Adjusted column, and the charter did not find them.
4. **`Demand (MW) (Imputed)` is NOT a series** — 447,133 of 447,168 null.

Nothing was padded, interpolated or rescaled by this lane (rule 13 `[R-MEASURED]`).

### 1.4 Seasonal peak by candidate zone — **MEASURED, and the footprint is SPLIT**

| Zone | 2023 | 2024 | 2025 | summer/winter |
|---|---|---|---|---|
| **NWPP-NW** | **WINTER** | **WINTER** | **WINTER** | 0.86 / 0.80 / 0.82 |
| **NWPP-OR** | SUMMER | SUMMER | **WINTER** | 1.09 / 1.06 / **0.98** |
| **NWPP-INLAND** | SUMMER | SUMMER | SUMMER | 1.11 / 1.11 / 1.10 |
| **NWPP-EAST** | SUMMER | SUMMER | SUMMER | 1.24 / 1.34 / 1.30 |
| **NWPP-SNV** | SUMMER | SUMMER | SUMMER | **1.95 / 2.06 / 1.87** |

Per BA: **8 winter · 6 summer · 1 flipping (PACW)**. The footprint's own coincident peak is a
**summer** peak in all three years even though its largest zone peaks in winter.

**Consequence for card N7, stated because it is structural, not cosmetic:**
`PLANNING_RESERVE_MARGIN_BY_ISO` is `dict[str, float]` — **one scalar per ISO** — and the
reliability floor that reads it tests `accredited_firm_capacity_mw` against
`peak × (1 + PRM)`. A footprint where NWPP-NW peaks in January and NWPP-SNV peaks in July at
~2× its own winter load cannot be sized by one number against one peak. **NWPP-INLAND is worse
than a scalar**: it mixes winter-peaking AVA (0.92–0.95) and NWMT with summer-peaking IPCO
(1.34–1.41) and WAUW, so even a per-zone seasonal PRM averages two regimes inside one zone.

---

## 2. The other charter items

| Item | Result |
|---|---|
| **(3) Curated-fleet seam** | **EXTEND `eia860_generators.parquet`, through the existing producer.** It is the fleet loader's own source (`data/fleet/eia860.py`, `EIA_860_PARQUET_NAME`) and `data/hydro.py`, `model/storage.py` and `data/announced_retirements.py` read it too; a missing NWPP fleet raises `FileNotFoundError`. `scripts/data/process_eia860.py:203` filters on `BA_CODE_TO_ISO`, so adding the 17 codes there and re-running extends the file, its retired-window twin and the `iso` column together. **But see §3 — the blocker is `ISO_TO_BA_CODE`, not the file.** |
| **(4) Load spine** | All 17 BAs committed, confirmed. Window **447,168 rows = 17 × 26,304 UTC hours, zero gaps** once the 2022 half-file is read (the charter's 8,751-hour 2023 is a UTC-boundary artifact, not missing data). Energy on the Adjusted column: **284.208 / 291.343 / 293.390 TWh** — the charter's energy row is the **raw** column while its peak and load-factor rows are **Adjusted**. AVRN/GRID null demand in all 26,304 h **in all three variants**, confirmed; `Total Interchange (Adjusted) == Net Generation (Adjusted)` for both, to 0.0 MW. |
| **(6) Timezone** | Confirmed exactly: **14 Pacific / 3 Mountain (NWMT, PACE, WAUW)**, stable across all three years, **all 6 DST transitions present and correctly signed** (Mountain flips one UTC hour before Pacific, both directions), **IPCO files Pacific** (measured: at UTC 2023-07-28 08:00 IPCO stamps 01:00, PACE 02:00). **Every BA has 26,304 unique UTC hours and exactly 3 duplicated LOCAL timestamps.** **Convention: UTC is the canonical hour and the only admissible join key**; local is provenance only. `BA_TIMEZONE` gains 14 × `America/Los_Angeles` + 3 × `America/Denver`; **`IPCO` takes `America/Los_Angeles`**, not `America/Boise`. Gate **G19 closed on the data side**. |
| **(7) Registry-values table** | Audit §7, 16 rows. **Measured and NOT pending**: queue-cap basis (demonstrated peak annual COD 2019–2025: wind 1.484, solar 1.953, storage 0.919, gas_ct 0.456, gas_cc 0.000 GW/yr — the same identification ERCOT's own entry uses); Columbia Generating Station monthly CF (**0.802 / 0.948 / 0.737**, biennial refuelling visible); gas basis **attribution** per zone off `Natural Gas Pipeline Name 1`; eGRID vintage (2023, module scalar, no entry needed); `ISO_STATES["NWPP"]`; offer bands 1.0. **Pending NWPP-12**: PRM by season, VOLL (§2.1 below), TTCs, `TRANSMISSION_BASE_STATIC_VINTAGE`, LTLF, RPS schedules, coal basin labels. |
| **(8) CEMS arithmetic** | Charter's ~32 % confirmed as an **upper bound (32.63 %)**; measured **15.32 % today**, **30.98 % after NWPP-11**. On **energy** the same path reaches **41.8–43.6 %** of EIA-923 footprint net generation — materially better than the nameplate share implies. Proxy validated at **100 % precision / 94.9 % MW recall** against MT/NV/WY/CA. **CO needs none — its one footprint plant is 7.5 MW of HYDRO, not solar as the charter says** (the charter's conclusion is right, its reason is wrong, and the corrected reason is stronger). **CA is already on disk and is inert for NWPP** (zero footprint facilities in `CA_2024`). |
| **(9) Zone recommendation** | **Five zones, as scoped, with two items declared open.** `NWPP-SNV` is the cut to defend hardest (its correlation with NWPP-NW is **0.048**); `NWPP-INLAND` the least (within-group 0.682 vs vs-rest 0.631 — a residual grouping). NW↔OR correlate **0.916** and are the least-bad three-zone merge, at the cost of the one seasonal distinction the fleet turns on. **GCPD's placement is disputed by the load data** (0.90 with IPCO, 0.08–0.16 with the Puget BAs it is grouped with, and summer-peaking in a winter-peaking zone) — flagged, **not recommended for a move**, because load correlation is not a transmission constraint. Dispositive evidence is NWPP-12's WECC path ratings. |
| **(10) Manual manifest** | Audit §10 — 17 numbered rows with exact URLs, split by owning lane. |

### 2.1 VOLL — the one registry row where the *object* differs from every registered ISO

Every registered ISO's `voll` is a **market offer cap** (ERCOT $5,000, CAISO/SPP/ISO-NE $2,000).
**FERC Order 831 (157 FERC ¶ 61,115; 18 C.F.R. §35.28(g)(11)) applies by its own terms to RTOs
and ISOs**, and NWPP is neither — no pool-wide day-ahead market, no clearing engine, no
incremental offers to cap. Importing $2,000 would put a market-design artifact from a market
that does not exist here into the LP's scarcity ceiling: a rule-13 `[R-MEASURED]` failure (no
forward analogue in the region modelled) and a rule-25 `[R-ISO-SCOPE]` transfer.

This lane therefore proposes a **sourcing rule, not a number** (audit §7.1): (a) a loss-of-load
/ unserved-energy cost stated in a participant IRP; else (b) the **LBNL Interruption Cost
Estimate Calculator** (`icecalculator.com`, LBNL / US DOE) on the footprint's own customer mix;
else (c) a WECC or WRAP published planning VOLL. Whatever lands is a **ledgered free parameter**
(rule 21 `[R-DOF]`) and is never swept against a gate. Two mechanics for NWPP-20: `voll` is
`Field(gt=0.0)` so the config will not validate without one, and a VOLL below the most expensive
real unit's marginal cost makes shedding load cheaper than dispatching — so any interim value is
**declared as interim in the run's attestation**, not quietly adopted.

---

## 3. ROUTED TO THE DESK — the W2 blocker the charter located in the wrong module

**Plan §2.3 names `data/zone_assignment.py` as "the one genuinely novel code change in W2".
Measured, it is in at least five modules, and the object is `ISO_TO_BA_CODE`.**

`BA_CODE_TO_ISO` handles 17→1 correctly everywhere (`.map()`, `.isin()`, and the two
`{ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}` set comprehensions). **Its inverse does
not:**

```python
# src/market_sim/data/fleet/models.py:221
ISO_TO_BA_CODE: dict[str, str] = {iso: ba for ba, iso in BA_CODE_TO_ISO.items()}
```

With 17 NWPP entries, `ISO_TO_BA_CODE["NWPP"]` becomes **one arbitrary BA — whichever is
inserted last** — and every consumer compares with `==`. Nine live `src/` call sites plus
`zone_assignment`'s own 1:1 `_ISO_TO_BA_CODE` (four more) and four `scripts/`:

| Module | Line(s) | Silent effect for NWPP |
|---|---|---|
| `data/hydro.py` | 607, 639, **684** | the hydro nameplate/budget tables cover **1/17 of the fleet** — **card N3's own machinery** |
| `data/fleet/eia860.py` | 1653, 2574, 2748 | fleet-side BA filters wrong |
| `data/fleet/campd_bins.py` | 168 | oil-primary screen returns **empty**, indistinguishable from "none" |
| `data/zone_assignment.py` | 1092, 1120, 1325 (+795) | the plant→zone splitter sees one BA |
| `scripts/data/curate_fleet.py` (106), `curate_hydro_plant_modes.py` (218), `derive_egrid_family_heat_rates.py` (147), `scripts/lib/wind_shape.py` (178) | — | same |

**Every one fails silently** — an empty or 1/17 result, never an exception. **Recommended shape
(recommendation only):** make the ISO→BA direction a codes-tuple (`dict[str, tuple[str, ...]]`,
or a parallel `ISO_TO_BA_CODES` keeping the scalar for the seven 1:1 ISOs), move all 13 call
sites to membership, and pin it with a unit test asserting `len(ba_codes("NWPP")) == 17` **and**
that a loaded NWPP fleet reproduces **939 plants / 1,930 generators / 98,238.1 MW**.

**This is a scope correction to plan §2.3's "Zone assignment" row, and it belongs to
NWPP-20/NWPP-32/NWPP-36 jointly** — NWPP-32 and NWPP-36 both read `data/hydro.py`.

## 3.1 Also routed — two seam facts that will break a naive derive

- **BPAT's balance identity fails structurally.** `Demand = NetGen − TotalInterchange` holds to
  0.000 MW for PACW/PSEI/TPWR and near-exactly for ten more, but for **BPAT** the mean residual
  is **−3,206 MW** and **81.5 % of hours** miss by > 1 MW (BPA wheels energy it neither generates
  nor serves). Consequence: **summing per-BA `Total Interchange` over the 17 does NOT give the
  footprint's external position** — it is off by **+35.4 / +35.8 / +12.9 TWh** against
  `NetGen − Demand` (−6.618 / −3.157 / +5.418 TWh). Direct input to **card N4**, hard constraint
  on **NWPP-34**, and the reason the per-counterparty DIBA product (NWPP-11 item 3) is required
  rather than nice-to-have.
- **`GRID` is a hard source conflict, and it is ~6 % of footprint net generation.** EIA-930
  `GRID` net generation peaks at **3,208 MW = 4.65×** the **689.4 MW** EIA-860 assigns that BA,
  implied CF **2.93**, 16.79 / 18.62 / 17.72 TWh/yr against a 6.04 TWh/yr physical ceiling.
  Gridforce Energy Management provides BA *services* to third-party resources, so the two
  sources do not describe the same resources. **This must be adjudicated before card N5 places
  GRID's generation anywhere** — taking EIA-930's figure risks double-counting resources
  EIA-860 attributes elsewhere, possibly outside the footprint. **AVRN is clean** (0.89×
  nameplate, CF 0.34).
- **The EIA-930 fuel taxonomy changes at 2024-07**, and read literally footprint hydro goes
  104.2 → 55.4 → **0.0 TWh**. Union the old/new families and the mix reconciles to published net
  generation within **0.04 % / 0.00 % / 0.08 %**. One Adjusted column carries an EIA **spelling
  error** — `Solar witho Integrated Battery Storage (Adjusted)` — which breaks any programmatic
  `f"{base} (Adjusted)"`. **Pumped storage is unobservable** in EIA-930 for this footprint in
  every year, though EIA-860 carries 314.0 MW.
- **Colstrip has no committed delivered coal price.** `eia923_monthly_fuel_costs.parquet` covers
  8 coal plants; **Colstrip (1,647.4 MW, ~9–11 TWh/yr), Centralia, TS Power and Hardin —
  2,911.7 MW = 32.7 % of coal — carry zero rows** (mine-mouth / captive-mine). NWPP-12's coal
  item must supply a cited cost for Colstrip specifically or its marginal cost is undefined.
- **The 2025 EIA-923 vintage is preliminary** — 260 footprint plant-rows against 848 / 879 for
  2023 / 2024. NWPP-30/31/32 must verify coverage before relying on it (the SPP audit's own
  item-9 caveat, reproduced here).

---

## 4. Files changed

| File | Change |
|---|---|
| `docs/multi-iso/nwpp-data-audit.md` | **NEW** — the Phase-0 census (§0 headline, §1 status table, §2 fleet + adjudications, §3 curated-fleet seam, §4 load spine, §5 seasonal peak, §6 timezone, §7 registry values, §8 CEMS, §9 zoning, §10 manual manifest, §11 reproduction) |
| `docs/multi-iso/00-iso-addition-protocol.md` | §0 NWPP row added; the §0 "eighth region" paragraph and the **§3 registered-count sentence** rewritten to carry both chartered-not-registered regions. **The count was re-measured at this lane's own base sha: `_ISO_BUILDERS` carries SEVEN** (ERCOT, CAISO, MISO, PJM, NYISO, NEISO, SPP); SOCO and NWPP are charter-order eighth and ninth, neither registered |
| `docs/multi-iso/01-data-needs-and-upload-manifest.md` | NWPP rows in §2 (EIA-930), §3 (CAMPD), §4 (gas basis), §5 (zonal load), §7 (hydro). **NWPP rows only** |
| `docs/handoffs/FINDING-nwpp-10-2026-09-13.md` | this file |

No shared record was touched: not the plan, not the ledger, not `docs/calibration-log/`, not
`CHANGELOG.md`, not `docs/mechanism-testing-matrix.md`, not any matrix shard (rule 28 — this
lane tested no mechanism), not any `soco*` file.

---

## 5. Log entry

*(For the desk to append verbatim to `docs/calibration-log/nwpp.md` when NWPP-35 opens it.)*

```markdown
## 2026-09-13 — NWPP-10: Phase-0 data audit, registry-values table, protocol correction

Lane NWPP-10, branch `claude/nwpp-10-audit-raq015`, base sha `4d9c3251`. No solve, no
mechanism, no matrix cell. Deliverable `docs/multi-iso/nwpp-data-audit.md`.

**Census.** The charter's headline is confirmed exactly — 1,082 plant-table rows / 940 plants
with an operable generator / 1,932 generators / **98,738.1 MW**, hydro 35,799.5 over 288 plants
(eight ≥ 1 GW holding 17,821.8), nuclear 1,200.0, coal 8,910.2 over 32 units, Electric Utility
68,860.0 MW. Corrected: gas ST **2,393.0** (charter 2,163.0), gas ICE **737.5** (732.7), solar
PV **10,051.3** (10,049.9), MT **6,939.6** (6,940.4); the total is unchanged and the charter's
elided "other" residual falls 365.7 → 129.5 MW.

**The TRE row is REJECTED.** Plant 68906 *Pine Forest Solar I*, Hopkins County TX, NERC TRE,
BA `DOPD`, 500.0 MW. Rule applied: a **two-key interconnection test** — WECC NERC region AND
Western-Interconnection coordinates — key (i) dispositive because ERCOT and WECC are
asynchronously separated. Post-adjudication footprint **939 plants / 1,930 generators /
98,238.1 MW**. Two more rows named: `WAUW`'s Sand Creek Wind (MRO, eastern Montana — not a
defect; WAUW straddles the interconnection seam; canceled, inert) and `DOPD`'s Desert Bloom
(Maricopa County AZ, WECC, proposed-only — inert today, live on entry).

**Demand convention: `Demand (MW) (Adjusted)`, and do NOT screen on top of it.** It reproduces
the charter's cleaned peaks 49,290 / 52,564 / 50,953 MW to the MW and repairs all 30 artifact
hours (confirmed exactly: AVA 10, NWMT 11, NEVP 6, PACE 1, SCL 2). The same 2.5×-median screen
also flags **54 CHPD hours in 12–16 January 2024 which are REAL** — the cold snap containing
CHPD's and the whole NWPP-NW zone's 2024 annual peak; CHPD's peak/median is 2.29 / 2.83 / 2.50,
falsifying the screen's own stated ≤ 2.1 basis (NEVP 2.20–2.37 too). `_screen_demand_dropouts`
IS needed — 17 exactly-zero NEVP hours in 2025 survive into Adjusted. `(Imputed)` is a sparse
patch column, not a series. Energy on the Adjusted column: **284.208 / 291.343 / 293.390 TWh**
(the charter's energy row is raw, its peak and load-factor rows Adjusted). Window is
**447,168 rows = 17 × 26,304 UTC hours, zero gaps**, once the 2022 half-file is read.

**Seasonal peak is SPLIT, measured.** NWPP-NW winter ×3 · NWPP-OR summer/summer/**winter** ·
NWPP-INLAND summer ×3 · NWPP-EAST summer ×3 · NWPP-SNV summer ×3 (S/W 1.87–2.06). Per BA
8 winter / 6 summer / 1 flipping. One scalar `PLANNING_RESERVE_MARGIN_BY_ISO` cannot express
it, and NWPP-INLAND mixes both regimes inside one zone. Card N7.

**Timezone CLOSED.** 14 Pacific / 3 Mountain (NWMT, PACE, WAUW), stable across years, all six
DST transitions correct, IPCO files Pacific (recorded). 26,304 unique UTC hours vs 3 duplicated
local timestamps per BA → **UTC is the only admissible join key**; local is provenance. Gate
G19 closed on the data side.

**CEMS: ~31 % of nameplate, ~42–44 % of energy.** Charter's ~32 % confirmed as an upper bound
(32.63 %); 15.32 % reachable today, 30.98 % after NWPP-11 lands ID/OR/UT/WA (16 files). CO
needs none — its one footprint plant is 7.5 MW of **hydro**, not solar. CA is on disk and inert.

**Routed to the desk.** (a) The W2 novel change is **`ISO_TO_BA_CODE`**, not
`zone_assignment.py`: it is the inverse dict comprehension of `BA_CODE_TO_ISO`, so 17→1
collapses it to one arbitrary BA and 13 `==` call sites fail **silently**, including
`data/hydro.py:684` — card N3's own machinery. (b) **BPAT's balance identity fails
structurally** (mean −3,206 MW, 81.5 % of hours), so per-BA `Total Interchange` cannot be summed
to the footprint boundary (off by 35.4 / 35.8 / 12.9 TWh) — card N4, NWPP-34. (c) **`GRID` is a
source conflict** — EIA-930 net generation 4.65× the 689.4 MW EIA-860 gives that BA, ~6 % of
footprint energy — and must be adjudicated before card N5 places it. (d) The EIA-930 fuel
taxonomy changes at 2024-07 and one Adjusted column is misspelled `Solar witho …`. (e) Colstrip
(1,647.4 MW) has **no** committed delivered coal price, as do Centralia, TS Power and Hardin —
32.7 % of coal. (f) VOLL: FERC Order 831's $2,000 is the wrong object here (Order 831 binds RTOs
and ISOs; NWPP is neither) — a sourcing rule is proposed, not a number.
```

---

## 6. Gates

| Gate | State after this lane |
|---|---|
| **G19** (two-timezone footprint) | **CLOSED on the data side** — 14/3 split measured, stable, all 6 DST transitions verified, UTC join key established. Card N6's convention choice remains |
| **G20** (the 30 defective hours propagate) | **DISCHARGED and SHARPENED** — the 30 are confirmed and named, the convention is established, and the gate is **extended**: the live risk is now the *screen*, which would delete 54 real hours, plus 17 zero-demand hours no screen currently catches |
| **G3** (data-profile token trap) | untouched — NWPP-20 re-measures at its own base sha |
| **G12** (LTLF edition + vintage) | **still open, still a W2 precondition** — no citable footprint LTLF is committed |
| **G18** (a zone splits a BA) | **confirmed unavoidable as scoped** — no sub-BA product exists for any of the 17; BPAT alone is 20.3–20.8 % of load |
| Rules | 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 23 `[R-FROZEN-DERIVE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]` — all observed; every cell is measured, cited, or `pending` |
