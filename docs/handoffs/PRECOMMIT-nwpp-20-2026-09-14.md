# PRECOMMIT — lane NWPP-20: register NWPP (the pin flip)

**Lane** NWPP-20 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-14 ·
**Branch** `claude/nwpp-20-register-hlgraw` · **Base sha** `d083b0b14b5c5bfb3aed8877859d309f7ddca4d1`
(= `origin/main` at session start; the desk refresh `089341f2` is an ancestor) ·
**DATA PROFILE** `shared` (this lane creates the `nwpp` profile) · **Zero LP** (rule 32 `[R-SHARD]`:
this lane runs no solve; rule 31's promotion question does not fire).

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §2.3 (the checklist), §0, §3 (the ruled
cards), §7 gates G1–G3, G5–G12, G18; the r#4 issuance notice. Written **before any file under
`src/`, `scripts/`, `configs/` or `tests/` was edited**; every number below was measured off the
committed tree at the base sha with pandas only.

---

## 1. Preconditions — re-verified at `d083b0b1`, none regressed

| Precondition | Verified how | State |
|---|---|---|
| Cards N1, N3 ruled (sitting #1); N4, N5, N7, N8 ruled (sitting #4); N6 resolved by measurement | plan §3 rows read at this sha; rulings quoted in §2 below | MET |
| NWPP-10/11/12/13 merged; NWPP-21 landed the ninth shard | `docs/handoffs/FINDING-nwpp-1{0,1,2,3}-2026-09-13.md` and `FINDING-nwpp-21` present on the base tree; `docs/codebase-site/data/mechanism-matrix/NWPP.js` present | MET |
| Gate G12 (LTLF edition + vintage) | `data/raw/load-forecast/nwpp/nwpp.csv`: 83 rows, publishers PacifiCorp (20) / Idaho Power (61) / PSE (2) | MET — spec strings taken verbatim from the notice |
| NWPP-22 / rubric v3.8 PRICE-UNSCORED class on `main` | `scripts/calibration_verdict.py` carries the class (SOCO-22 `1b6ce1fd`); `actual_lmp.json` has no NWPP block | MET — this lane touches nothing in the scorer |

**Re-measured counts at this sha (plan §0):** `SUPPORTED_ISOS` = **7** (`ERCOT CAISO MISO PJM
NYISO NEISO SPP`); `SURFACE_ISOS` = **7** (same set); `BA_CODE_TO_ISO` = **7** entries;
`mech_matrix.ISO_ORDER` = **9** (`… SPP SOCO NWPP`), `ISO_EV_KEY["NWPP"] = "W"`; matrix base
`isos` = **9**; nine shard files on disk. A nine-shard matrix over a seven-region registry is the
supported intermediate state the notice describes. SOCO is **not** registered (`_ISO_BUILDERS`
has no SOCO); NWPP registers as the **eighth** builder.

## 2. The rulings this lane implements (plan §3, verbatim excerpts)

- **N1** — *"RULED 2026-09-13 (sitting #1): ALL 17 BAs … Footprint = BPAT PACE PACW PGE PSEI AVA
  IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP; key `NWPP`; NEVP in; Canada out; AVRN and
  GRID supply-side members, not zone candidates."*
- **N3** — *"BUILD CASCADE COUPLING FIRST — AGAINST the desk's recommendation."* (lane NWPP-36;
  this lane adds **no** `ScenarioConfig` field — gate G8.)
- **N4** — *"SERVED MEASURED INTERCHANGE, PRICED LINKS DEFAULT-OFF … `_SCALAR_INTERCHANGE_ISOS +=
  NWPP` … `NeighborInterface`s registered but default-OFF … Binding caveat measured by NWPP-10
  §3.1: BPAT's balance identity FAILS structurally … The derive must handle that, never assume
  `Demand = NetGen − TotalInterchange`."*
- **N5** — *"FIVE ZONES, AS SCOPED … TTC tiers … EAST↔SNV Path 35 TOT 2C 600/580 — Tier-1
  candidate; INLAND↔SNV Path 16 Idaho–Sierra 500/360 — Tier-1 candidate; NW↔INLAND Tier-2 (Paths
  8/6/14, aggregation documented); INLAND↔EAST Tier-2 (Path 20 "Path C" 1,600/1,250); NW↔OR
  Tier-3, documented absence … Paths 4/5/71/86/87/88 are east–west cuts, NOT BA interfaces."*
- **N6** — *"RESOLVED BY MEASUREMENT, NOT RULED … 14 Pacific / 3 Mountain (NWMT, PACE, WAUW) …
  IPCO files Pacific … UTC is the canonical hour and the only admissible join key; local time is
  provenance only."*
- **N7** — *"ONE SCALAR NOW, DECLARED; PER-ZONE SEASONAL AS A FORECAST LEVER … the two-regime
  mismatch DECLARED on the determination basis at full magnitude … WRAP is a FORECAST-SIDE OBJECT
  ONLY … first binding season Winter 2027–28."*
- **N8** — *"LEGACY HEAT-RATE BINS FOR THE FIRST KEEPER; CAMPD PER-PLANT AS A LEVER … so
  `use_campd_bins=False`."*

Standing defaults (plan §3, no card): `_MULTI_YEAR_ISOS` gains NWPP; no import node (G7);
offer-curve bands 1.0 (G5); `ISO_EV_KEY["NWPP"] = "W"` (landed by NWPP-21).

## 3. Design decisions fixed before the code was written

### 3.1 `ISO_TO_BA_CODE` (the R-e blocker)
`data/fleet/models.py` gains `ISO_TO_BA_CODES: dict[str, tuple[str, ...]]` (grouped from
`BA_CODE_TO_ISO`, insertion order) and `ba_codes(iso)`; the scalar `ISO_TO_BA_CODE` keeps an
entry **only** for 1:1 regions, so `ISO_TO_BA_CODE.get("NWPP")` is `None` rather than an arbitrary
BA. Every consumer moves to membership (`isin`): `data/hydro.py` ×3, `data/fleet/eia860.py` ×3,
`data/fleet/campd_bins.py`, `data/zone_assignment.py` ×3 (+ its own `_ISO_TO_BA_CODES`),
`scripts/data/curate_fleet.py`, `curate_hydro_plant_modes.py`, `derive_egrid_family_heat_rates.py`.
For a 1:1 region `isin((code,))` and `== code` select identical rows, which is the byte-identity
claim gate G8 tests (§5).

### 3.2 Footprint admission predicate
`BA ∈ NWPP_BAS AND NERC Region == "WECC"`, encoded as `ISO_NERC_REGION_ADMISSION = {"NWPP":
"WECC"}` in `models.py` and applied in the producer (`process_eia860.py`) and in the EIA-860 plant
reads of `zone_assignment.py`. No per-plant exclusion. A Western-Interconnection bounding test is
**not** added: Desert Bloom (69290, Maricopa AZ) is inside the WI, so such a test cannot catch it;
it is inert (proposed only) and named in the FINDING as a re-vintage review item.

### 3.3 Demand
Per-BA `Demand (MW) (Adjusted)`, `_screen_demand_dropouts` **per member BA before summing**
(NEVP 2025: 17 exact-zero hours — a footprint sum would never read zero), **no**
`_screen_demand_spikes` (NWPP-10 §1.3). Members are joined on **UTC** onto the Pacific local year
(`BPAT` clock, 81.6 % of load); the three Mountain BAs are re-indexed by UTC, their local columns
unused. AVRN and GRID demand is null in every hour and enters as 0.0.

### 3.4 Served interchange — the construction, and why (measured 2024, TWh, export +)
| BA | NG−D | TI | DIBA internal | DIBA external | NG−D−TI |
|---|---:|---:|---:|---:|---:|
| BPAT | +21.47 | +57.51 | +40.06 | +17.47 | **−36.04** |
| every other BA (15) | = TI | | | | 0.00 (NEVP +0.25, GCPD −0.04) |
| GRID | +18.62 | +18.62 | +8.84 (→BPAT) | +9.79 (→PNM/SRP/WALC) | 0.00 |

BPAT's `Total interchange` **dropped by ~4,000 MW in 2025-06** (monthly means: TI 4,345 → 2,206
while NG 7,864 → 8,774, D 6,287 → 6,616, `NG: WAT` continuous), and the identity closes to 0 from
that month. So the defective series is TI, not NG or D. GRID's balancing area is two physically
separate resource sets: legs to BPAT only (Hermiston Power, 55328, in the fleet) and legs to
PNM/SRP/WALC only (Desert-Southwest resources EIA-860 files under other BAs — Harquahala is BA
`HGMA`). **Construction fixed:** `served(t) = Σ₁₇ (NG_adj − D_adj)(t) − Σ GRID→{PNM,SRP,WALC}(t)`.
Annual (Σ₁₇ NG−D before the GRID term): −6.63 / −3.12 / +5.43 TWh; GRID DSW legs +7.12 / +9.77 /
+10.13. The alternative (external-DIBA sum, +12.45 / +16.98 / +21.24 TWh) inherits BPAT's per-leg
over-report and is reported, not used. The residual adjudication is routed (FINDING §5).

### 3.5 VOLL — interim, declared
No participant IRP states a $/MWh unserved-energy cost (transcriptions searched: PacifiCorp Vol. 1
has "unserved energy costs … total cost of $0" and no rate; Avista/NVE/PGE none). Audit §7.1
route (b) (LBNL ICE on the footprint customer mix) is a derivation lane, not a registration.
Registered: **$2,000/MWh — the WEIM hard offer cap (CAISO Tariff §39.6.1 / FERC Order 831) that
11 of the 17 balancing areas' resources bid under in 2023–2025 (NWPP-13 §0: WEIM clears 5.5–6.2 %
of footprint energy net)**, declared INTERIM in the config docstring and ledgered as a free
parameter (rule 21); the audit's objection (a cap of an imbalance market is not a customer damage
function) is quoted in place and route (b) pre-declared as the successor.

### 3.6 TTC tiers (WECC 2024 Path Rating Catalog, `data/raw/nwpp-planning/README.md` §1)
Asymmetric published ratings are expressed as **paired one-way links** (the ERCOT Northeast↔North
precedent): EAST→SNV 600 / SNV→EAST 580 (Path 35, p. 36); INLAND→SNV 500 / SNV→INLAND 360 (Path
16, p. 19); INLAND→EAST 1,600 / EAST→INLAND 1,250 (Path 20, p. 23); INLAND→NW 8,877 = Path 8
2,200 + Path 6 4,277 + Path 14 2,400 (E→W) and NW→INLAND 2,550 = Path 8 1,350 + Path 14 1,200
(lower end of 1,200–1,340; Path 6 W→E "Not defined" contributes 0 — a stated gap); NW↔OR
symmetric **Tier-3 non-binding placeholder = NWPP-NW zone nameplate 43,619.1 → 43,600 MW** (the
SPP-20 construction: the sending zone's capability, an upper bound that cannot bind; OR is a leaf
whose peak load ≈ 9.9 GW).

### 3.7 Registry values (source → value)
Zonal load shares = pooled 2023–2025 `Demand (MW) (Adjusted)` energy, UTC-joined: **NW 0.3769 · OR
0.1509 · INLAND 0.1533 · EAST 0.1808 · SNV 0.1381** (per year NW 0.3778/0.3740/0.3788; audit
§9.2 2024 cross-check 37.41/15.09/15.29/18.11/14.10). Coincident peaks reproduce **49,290 /
52,564 / 50,953 MW** exactly. PRM 0.144 (PacifiCorp 2025 IRP Vol. 1 p. 131, July, "adopted from
WRAP"). Fleet 939 / 1,930 / 98,238.1 MW; wind 14,460.3, solar PV **9,751.3** (post-adjudication —
the audit's 10,051.3 included Pine Forest's 300 MW), batteries 2,321.0 OP + 2,147.0 proposed
U/V/TS. Queue CODs 2015–2025 (GW/yr peak): wind 1.484 (2020), solar 1.953 (2024), storage 0.919
(2025), gas_ct 0.456 (2024), gas_cc 0.500 (2016; 0 in 2019–25), geothermal 0.127 (2018), all-tech
4.491 (2024). EIA-930 pool energy 2024: wind 34.82 TWh, solar 17.18 TWh; nameplate ≤2023/≤2024:
wind 12,489.8/13,422.3, solar 6,312.6/8,265.8. Delivered coal 2024 quantity-weighted 2.855 $/MMBtu
(8 plants; Colstrip/Centralia/TS Power/Hardin carry no rows). Sumas 2024 mean 2.002 vs Henry Hub
2.192 → basis −0.19. Nuclear CF: `scripts/data/derive_nuclear_monthly_cf.py --isos NWPP`, run
once after the fleet loads (Columbia, plant 371). Seam envelopes (hourly, 2023–25): CAISO legs
max export 3,884–4,316 / import 1,424–1,737 MW; WECC_CAN 2,690–2,743 / 2,312–2,362; WECC_SW
(residual WECC + the WAUW↔SWPP tie) 4,014–6,049 / 3,667–4,361 (2023 carries a 60,037 MW artifact
hour). Data-profile trap re-measured: bare `ava` (13 hits), `grid` (16), `pge` (4), `wpp` (22)
and **`scl` (66 — ERCOT SCED files)** are refused; `nwpp` and the other twelve BA codes are clean;
the refused four are claimed by the delimiter-bounded `"<code> hourly"` / `"<code> interchange"`
forms.

## 4. What this lane will NOT do
No `ScenarioConfig` field, no default flip, no `results/cache.py` edit (G8); no `TAIL_THRESHOLD`
(G6, NWPP-13 read NO); no import node (G7); no `MARKET_DESIGN` / `_CURVE_ISOS` / `_CAPACITY_ISOS`
entry (N7); no zonal-share parser in `scripts/data/curate_zonal_shares.py` (NWPP-32's region — the
per-BA regroup is routed); no touch of `frontend/data/forecast/**`, any keeper/log/matrix shard,
`scripts/calibration_verdict.py`, the plan or the ledger.

## 5. Gate G8 proof plan
`python scripts/solve_surface_register.py --diff <base> HEAD` → zero moved rows for the seven;
NWPP rows new and undeclared (the D79 ledger has no new-ISO limb — FINDING-spp-20 R-1, still
open). Then `cache_key()` for two committed keepers re-derived on this branch and on the base tree.
