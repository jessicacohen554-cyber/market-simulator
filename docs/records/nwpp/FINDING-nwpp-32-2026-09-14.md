# FINDING — lane NWPP-32: the hydro energy budget (288 plants), and NWPP-36's specification

**Lane:** NWPP-32 (desk r#5 charter, 2026-09-14) · **Model:** Fable (`claude-fable-5-1`) ·
**Base:** `d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c` (= `origin/main` at session start) ·
**Branch:** `claude/happy-newton-rdab8x` (harness-designated; the charter's stem could not be used —
PRECOMMIT header) · **PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwpp-32-2026-09-14.md` ·
**DATA PROFILE:** `nwpp` · **Zero LP** (rule 32; no promotion question fires, rule 31).

## 0. REPORT FIRST

**Reconciliation: PASS, every plant, every year, at 0.000 MWh.** All 290 (2023) / 286 (2024) / 25
(2025) EIA-923 conventional-hydro reporters in the 17 BAs reconcile their twelve monthly budgets to
EIA-923's own annual column with a maximum absolute delta of **0.000 MWh** against the pre-registered
1.0 MWh tolerance (PRECOMMIT §2; predictions P1–P3 held). Nothing was filled: the **263 plants absent
from the 2025 early release read `NO_923_SERIES`** and stay absent. The loader
(`load_hydro_budget("NWPP", y)`) reproduces the clipped artifact to **0.00e+00 MWh** and the same
nameplate for every plant it keeps. Pumped storage (one plant, 314.0 MW, BPAT) is out by design.

**§2.7 (a), the chain, read from a published inventory and not chosen:** the ORNL EHA FY2024 `Water`
field places **eleven plants on the U.S. Columbia mainstem — Grand Coulee → Chief Joseph → Wells →
Rocky Reach → Rock Island → Wanapum → Priest Rapids → McNary → John Day → The Dalles → Bonneville —
20,098.8 MW = 56.14 % of the 35,799.5 MW of conventional hydro and 58.84 % / 57.96 % of its 2023 /
2024 energy.** The hydrological fact is in BPA's own published discharges: average annual flow rises
monotonically down the chain, 107,700 cfs at Grand Coulee → 108,000 at Chief Joseph → 169,800 at
McNary (after the Snake) → 172,400 → 177,900 → 183,300 cfs at Bonneville. Four more federal
run-of-river plants form the **lower Snake chain** (3,033.0 MW) that enters the mainstem at the McNary
pool, fed by Idaho Power's three-plant **Hells Canyon chain** (1,276.1 MW) and by Dworshak storage.
**One correction to the desk's list:** of its "eight ≥ 1 GW plants = 17,821.8 MW", **seven are
mainstem (16,662.1 MW); Boundary (1,159.7 MW) is on the Pend Oreille**, which reaches the Columbia
only through Canada — it is coupled to nothing else in this footprint.

**`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` is EMPTY (prediction P4 held).** Eight instruments were
read or attempted (§4); none states an energy-conservation period for a named plant, and the one
coordinating instrument that does define an accounting period — the 1997 Pacific Northwest
Coordination Agreement — defines **"Period means a calendar month"**, i.e. the model's existing
default. Every mainstem plant is NWPP-36's object under rule 19 in any case.

**Not in the charter, found on the way, and decisive for the 2025 posture (§3.2):** the pooled EIA-930
`NG: WAT` series is **not the same population** as these plants (−2.52 % in both complete years, a
BA-assignment artefact that decomposes exactly), and it carries the known-defective hours —
**+1,166 GWh = 14.1 % of October 2025 from one AVA hour at 810,113 MW**. An `eia930_monthly` repin of
2025 is therefore **refused** on rule-14 grounds; the recommended posture is `backfill_year=2024`
alone, with the measured like-for-like wetness declared.

## 1. Preconditions and what was touched

Preconditions verified at `d54cd9c5` (PRECOMMIT §1): NWPP-20 landed (eight regions; `ba_codes("NWPP")`
is the 17-tuple; `data/hydro.py` reads it); NWPP-11's extract present; the EIA-930 pool frame
registered, so **no loader branch was needed** and none was written. Files: five new artifacts under
`data/raw/nwpp-hydro/` + README rows; one new script `scripts/data/build_nwpp_hydro_budget.py`;
this FINDING and its PRECOMMIT. No `src/` edit, no `ScenarioConfig` field, no other region's rows, no
shared record (collision rule 1), no solve.

## 2. Gate A — the budget reconciles to EIA-923 annual, by plant

| year | EIA-923 `HY` reporters | EIA-860 `HY` plants | union | `RECONCILED` (Δ ≤ 1 MWh) | `MISMATCH` | max Δ | `ALL_ZERO` / `NON_POSITIVE` | `NO_923_SERIES` | no EIA-860 nameplate | loader keeps | loader clip of negative months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2023 | 290 | 288 | 295 | **290 / 290** | 0 | 0.000 MWh | 7 / 3 | 5 (80.0 MW) | 7 | 280 | 6,856 MWh over 38 plants |
| 2024 | 286 | 288 | 294 | **286 / 286** | 0 | 0.000 MWh | 3 / 3 | 8 (92.0 MW) | 6 | 280 | 56,868 MWh over 27 plants |
| 2025 | 25 | 288 | 288 | **25 / 25** | 0 | 0.000 MWh | 0 / 0 | **263** | 0 | 25 | 86 MWh over 1 plant |

Annual energy: 106.9281 / 107.9002 / 74.9364 TWh (extract = EIA-923 annual column, to the MWh); the
loader stamps 106.9353 / 107.9575 / 74.9365 TWh after its documented clip of negative months. The
`ALL_ZERO` / `NON_POSITIVE` plants (Electron 22.8 MW at zero in both years; Prospect 3, Prospect 4,
Weber, Hydro III negative in every month) reconcile exactly and are dropped by the loader as
degenerate units — reported here, not hidden (NWPP-11 §5.3 flagged the same rows).

**The population edges, named:**

* **`NO_923_SERIES` (in EIA-860, no EIA-923 series):** Pilot Butte 1.6 MW, Swift 2 72.0 MW,
  Drop 2 2.5, Drop 3 1.6, Newhalem 2.3 (both years); plus Rock Creek II 1.9, El Dorado Elk Creek 2.6
  and James W. Broderick 7.5 in 2024 only. **Not filled.** Swift 2 is the one material absentee
  (Cowlitz PUD's canal plant on the Lewis River; its energy may be filed under another plant id —
  routed to the desk as a question, §7).
* **No EIA-860 nameplate (EIA-923 reporters):** **Copco 1, Copco 2, Iron Gate and John C. Boyle are
  the Klamath dams removed in 2023–2024** — 387,400 MWh of real 2023 energy (71,412 + 42,481 + 81,505
  + 192,002) and 8,761 MWh in 2024, carried by the loader at its peak-monthly-average fallback
  (17.0 / 18.3 / 18.6 / 63.9 MW in 2023). That is the correct treatment: the energy was generated;
  the plants no longer exist in the operable file. Quincy Chute (9.4 MW, canal) and PEC Headworks
  (Potholes East Canal, GCPD) are Reclamation canal drops with no 860 hydro row; Port Townsend Paper
  carries a 923 hydro row at zero.
* **The `cf_over_1` envelope inconsistency (NWPP-11 flag):** 31 plant-years in each complete year where
  a month's energy exceeds nameplate-hours — worst Nooksack (1.5 MW, max monthly CF 1.78), Wanship
  (1.9 MW, 1.29), Ryan (55.2 MW, 1.26), Arrowrock (15.0 MW, 1.24), Long Lake (70.0 MW, 1.20). Carried
  as `cf_over_1_months` / `cf_max_month` in the artifact; **surfaced, not clipped** (rule 14) — the
  loader's `P ≤ pmax` bound will under-deliver those plant-months and the largest is 70 MW.

## 3. Gate B — the envelope, and the 2025 posture

### 3.1 Envelope

`max_mw` = EIA-860 nameplate for 288 plants (35,799.5 MW; loader stamps 35,808.2 MW in 2023 and
35,694.6 in 2024 after the fallbacks and drops above); `min_mw = 0` everywhere. **No floor is stamped
by this lane** — a floor needs a driver, a window and a forward story (rule 17), and the measured
Q95 sustained level that would identify one is reported in §5(c) as evidence for NWPP-40's posture
decision on the default-off `hydro_min_flow_floor`, never armed here.

### 3.2 The 2025 early release — backfill, and the repin is REFUSED on measured grounds

The PRECOMMIT (§3) pre-registered: recommend `eia930_monthly` on top of `backfill_year=2024` iff the
pooled 930/923 annual ratio is stable across the complete years (|Δ| ≤ 0.01) and monthly r ≥ 0.95.
Both conditions are met on their face (0.9748 / 0.9748; r 0.997 / 0.993). **The rule's premise —
"the same physical series on a stable basis" — is nevertheless false, and the honest outcome is to
say so rather than apply it.** Two measured reasons:

**(i) The −2.52 % gap is a population mismatch, not a basis offset.** By BA, EIA-930 `NG: WAT` minus
EIA-923 `HY` (TWh, 2023 / 2024): BPAT **−3.995 / −4.291**, GCPD **+3.873 / +3.835** (Priest Rapids —
EIA-860 assigns it to BPAT, EIA-930 generates it inside GCPD; the pair nets to ≈ 0), **WAUW −2.644 /
−2.811** (3.2 TWh of EIA-923 hydro assigned to WAUW — Yellowtail, Canyon Ferry-class Reclamation
plants — against 0.5 TWh of WAUW `NG: WAT`: their EIA-930 generation is filed by another BA and is
NOT in the pool), **PACW −0.722 / −0.718**, NWMT +0.28 / +0.38, PACE +0.26 / +0.50, NEVP +0.27 / +0.28.
The stability of the total ratio is two large offsetting gaps, not one series on one basis. A pin to
the pool level would scale 288 plants to a level that is missing ~2.7 TWh of their own energy.

**(ii) The pool carries the known-defective hours (NWPP-10 §4.4, gate G20) in `NG: WAT` too.** Pool
hours above 26,000 MW: 2024 — two (NWMT 65,891 MW on 2024-08-27 20:00 UTC, 65,880 on 10-07 20:00:
+76 / +73 GWh = 0.9 % / 1.1 % of August / October); **2025 — five (AVA 810,113 MW on 2025-10-12
10:00, 190,346 the next hour; NWMT 99,225 / 32,416 on 10-14; NWMT 29,149 on 12-02): +1,166 GWh =
14.1 % of October 2025, +40 GWh in December.** `measured_monthly_hydro` sums them in. A 2025 repin
would put a phantom 1.17 TWh into October.

**Recommended 2025 posture for NWPP-40 (a flag choice, no code):** `backfill_year=2024`, **no
`eia930_monthly`**. Measured cost, declared at full magnitude: the backfilled 2025 budget is
**113.156 TWh over 280 plants (35,694.6 MW)**, of which **66.2 % is measured 2025 energy** (the 25
large reporters, all eight ≥ 1 GW plants) and 33.8 % is 2024 water carried forward; on the 25-plant
panel 2025 ran **+6.1 % / +7.5 %** against 2023 / 2024 (NWPP-11 §5.2), so the carried third is, on
that evidence, biased low by roughly that much (~2–3 % of the fleet total). The pool level, after the
basis ratio and before its defective hours, implies 114.32 TWh — within 1.0 % of the backfill — and a
monthly pattern that differs from the backfill by −8 % to +16 % (the +16 % is the October artefact;
December's +10 % is the measured 2025 flood month the backfill cannot know). **Both defects are routed
(§7); if the eia930 layer repairs its `NG: WAT` hours and the pool's population is reconciled, the repin
becomes the more accurate posture and NWPP-40 should revisit.** The choice is made on rule 14, not on
any residual — there is no NWPP residual and none was consulted.

## 4. The instrument table, and why the period-entry set is EMPTY

Admissibility (PRECOMMIT §4): an entry needs (i) a published instrument read in-session, (ii) a period
stated in words or convertible from published numbers alone, and (iii) a plant outside NWPP-36's chain
(rule 19). Every candidate, with retrieval status:

| Instrument | Issuer / date | What it actually constrains | Plants | Period stated? | Retrieved |
|---|---|---|---|---|---|
| **Columbia River Treaty** (1961/1964) + Agreement-in-Principle 2024-07-11 + interim measures 2024-11-25 | US / Canada; CRS R43287 (2024-12-03) | 15.5 MAF Canadian storage (Duncan, Keenleyside/Arrow, Mica) operated to an **Assured Operating Plan set six years ahead** and **Detailed Operating Plans**; 1.0 MAF/yr fisheries flows since 1995 (+0.5 MAF in dry years under the AIP); 3.6 MAF preplanned flood storage at Keenleyside; the **Canadian Entitlement 1,141 MW / 454 aMW (2024 baseline) → 660 MW / 305 aMW (2025–29)**, −37 % from 2024-08-01; Libby is a Treaty project | Grand Coulee and everything below it (inflow), Libby | **No** — annual plans and seasonal flood/fish operations; no plant-level energy period | ✅ PDF, 19 pp (`congress.gov`; the BPA treaty page was 404) |
| **Pacific Northwest Coordination Agreement** (1997) | BPA, Corps, Reclamation + regional utilities | System-wide storage accounting: Operating Year Aug 1–Jul 31; Critical Period, Energy Content Curves, Critical Rule Curves, Firm Energy Load Carrying Capability — **"Period means a calendar month"** (§2 definitions). **Terminated 2024-09-15** (§1(a)), i.e. inside the scored window; the 2026 White Book says owners still supply BPA plant data and constraints, no successor text found | every coordinated reservoir | **Yes — and it is the calendar month**, the model's existing default | ✅ PDF, 117 pp (`grantpud.org`) |
| **CRSO Record of Decision** (2020-09-28; DOE/EIS-0529, 85 FR 63262) | Corps, Reclamation, BPA | 14 federal projects (Libby, Hungry Horse, Albeni Falls, Grand Coulee, Chief Joseph, Dworshak, the four lower Snake, McNary, John Day, The Dalles, Bonneville); juvenile fish passage spill **up to 125 % TDG for 16 h/day then reduced for up to 8 h, from the beginning of April through the third week of June** at six of eight lower river projects; **−330 aMW firm (critical water), −210 aMW average CRS, −230 aMW regional** vs No Action; MOP drawdowns are described for the MO4 alternative (the Selected Alternative's MOP terms were not extracted here) | the 14 | **No** — a flow/spill rate schedule and elevation limits, not an energy period | ✅ PDF, 135 pp (public-inspection copy; `federalregister.gov` HTML 302s to an unblock page, `nwd.usace.army.mil/CRSO` 403) |
| **Hanford Reach Fall Chinook Protection Program Agreement** (2004-04-05) | Grant PUD, BPA, Chelan, Douglas, WDFW, tribes | Rearing period **Priest Rapids weekday outflow delta (24 h max−min) ≤ 20 / 30 / 40 / 60 kcfs** for previous-day Wanapum inflow 36–80 / 80–110 / 110–140 / 140–170 kcfs, ≥ 150 kcfs above 170; the same caps over each 48-h weekend; spawning-period outflow held 55–70 kcfs for ≥ 12 h/day; pre-hatch drops to 36 kcfs for up to 8 h; protection flows at Vernita Bar (50 kcfs elevation); delivered "through use of the Mid-Columbia Hourly Coordination" | Priest Rapids outflow; binds the seven-project operation | **No** — a daily ramp band on outflow, not an energy budget; and Priest Rapids is in NWPP-36's chain (condition iii) | ✅ PDF, 24 pp (`grantpud.org`) |
| **Vernita Bar Agreement** (1988) | Grant PUD, BPA, others | Fall spawning flows lower, winter incubation flows higher over Vernita Bar | Priest Rapids | No | described in BPA *Inside Story* pp. 41–43; text not retrieved |
| **Mid-Columbia Hourly Coordination Agreement** (effective 1997-07-01 to 2017-06-30 "as amended, extended, or replaced") | BPA + Chelan, Douglas, Grant PUDs | Single-system hourly operation of **Grand Coulee, Chief Joseph, Wells, Rocky Reach, Rock Island, Wanapum, Priest Rapids** (HRFCPPA definition); **expired ~late 2019** ("nearly six months before May 2020") — coordination "gave way to cooperation" | the seven | No | ❌ text not retrieved; definition via HRFCPPA; expiry via search snippet of `newsdata.com` (fetch 429) |
| **FERC licence P-2144, Boundary** (2013-03-20, 42 yr) | FERC / Seattle City Light | Load-following with forebay elevation restrictions (summer); tributary deltas "experience the full range of water level fluctuations associated with load-following" | Boundary 1,159.7 MW | Elevation band only; **no pondage volume retrieved**, so no conversion (condition ii fails) | search-level only |
| **Flood-control rule curves** | Corps / Reclamation | Variable drawdown Jan–Apr from runoff forecasts, refill Apr–Jul (target 31 July), fixed drawdown Sep–Dec; "runoff is usually adequate to refill reservoirs about three out of every four years" | Grand Coulee (5.19 MAF), Libby (4.98), Hungry Horse (3.16), Dworshak (2.02), Albeni Falls (1.16), John Day | No — seasonal elevation guidance | ✅ BPA *Inside Story* pp. 28–38 (80 pp PDF) |
| **Resilient Columbia Basin Agreement** (2023-12-14) | US Government + OR, WA, four tribes | Increased spill at the eight lower Columbia/Snake dams; litigation stay granted 2024-02-08 through 2028; BPA rate impact est. 0.5 % (2026) → 0.9 % (2035); **terminated by the federal government June 2025**; a 2026 court order on emergency spill is reported | the eight | No | search-level only (`nwcouncil.org`, `idahoconservation.org`) |

**Decision:** no entry. The mainstem and lower-Snake instruments state flow, spill, elevation and
ramp conditions — not conservation periods — and their plants are NWPP-36's; the coordinating
instrument's own period is the month; the independent tributary projects' operating bands live in
FERC licence articles that were not retrieved (Boundary's elevation band, the Skagit, Lewis, Cowlitz,
Deschutes, Pend Oreille and Clark Fork licences) — **rule 14: do not invent an instrument we have not
read.** An empty set is the complete outcome; "the Columbia is complicated" was not consulted as one.

## 5. The four §2.7 constraints, measured on this footprint — NWPP-36's specification

### 5(a) Hydraulic coupling down the mainstem

**The chain (EHA `Water` ∈ {Columbia River, Columbia And Snake Rivers, Snake And Columbia Rivers};
order by the published dam sequence, cross-checked on EHA lat/lon):**

| # | plant | id | BA | MW (860) | 2023 GWh | 2024 GWh | published type | storage MAF | avg discharge cfs | EHA Mode |
|---|---|---:|---|---:|---:|---:|---|---:|---:|---|
| 1 | Grand Coulee | 6163 | BPAT | 6,495.0 | 15,585 | 15,442 | storage (BPA) | 5.19 | 107,700 | Intermediate Peaking |
| 2 | Chief Joseph | 3921 | BPAT | 2,456.2 | 9,391 | 9,228 | run-of-river (BPA) | — | 108,000 | NaN (Corps dam) |
| 3 | Wells | 3886 | DOPD | 866.8 | 3,498 | 3,502 | mid-C PUD project | — | — | Peaking |
| 4 | Rocky Reach | 3883 | CHPD | 1,349.2 | 5,001 | 4,901 | mid-C PUD project | — | — | Run-of-river/Upstream Peaking |
| 5 | Rock Island | 6200 | CHPD | 629.4 | 2,033 | 2,025 | mid-C PUD project | — | — | Run-of-river |
| 6 | Wanapum | 3888 | GCPD | 1,220.0 | 4,086 | 4,053 | mid-C PUD project | — | — | Peaking |
| 7 | Priest Rapids | 3887 | BPAT* | 950.0 | 3,842 | 3,838 | mid-C PUD project | — | — | Peaking |
| — | *lower Snake enters at the McNary pool* | | | | | | | | | |
| 8 | McNary | 3084 | BPAT | 990.5 | 3,646 | 3,668 | run-of-river (BPA) | — | 169,800 | Run-of-river |
| 9 | John Day | 3082 | BPAT | 2,160.0 | 6,793 | 6,956 | run-of-river, flood control (BPA) | — | 172,400 | Run-of-river |
| 10 | The Dalles | 3895 | BPAT | 1,819.7 | 5,407 | 5,431 | run-of-river (BPA) | — | 177,900 | Run-of-river |
| 11 | Bonneville | 3075 | BPAT | 1,162.0 | 3,631 | 3,493 | run-of-river (BPA) | — | 183,300 | Run-of-river |
| | **mainstem** | | | **20,098.8 = 56.14 %** | **62,913 = 58.84 %** | **62,536 = 57.96 %** | | | | |

\* EIA-860 files Priest Rapids under BPAT; EIA-930 generates it inside GCPD (§3.2).

Feeding it: **lower Snake** — Lower Granite 810 → Little Goose 810 → Lower Monumental 810 → Ice Harbor
603 MW, all federal run-of-river, 3,033.0 MW, average discharge 47–50 kcfs; **Hells Canyon** —
Brownlee 675 → Oxbow 190 → Hells Canyon 411.1 MW (Idaho Power, all EHA Peaking), 1,276.1 MW;
**Dworshak** (465 MW, 2.02 MAF) into the lower Snake at Lower Granite. Upstream of Grand Coulee only
through Canada: **Libby** (525 MW, 4.98 MAF, Kootenai → Kootenay Lake → Columbia), the **Pend Oreille /
Clark Fork / Flathead** chain (Hungry Horse 428 MW 3.16 MAF → Séliš Ksanka Qlispé 227.8 → Noxon Rapids
487.8 → Cabinet Gorge 265.2 → Albeni Falls 42 (1.16 MAF) → Box Canyon 90 → **Boundary 1,159.7**), and
the Spokane chain (seven Avista plants, 207.7 MW) into Lake Roosevelt. **Sum of the coupled chains in
this footprint: 24,408 MW = 68.2 % of hydro** (mainstem + lower Snake + Hells Canyon). The Pend
Oreille chain (2,700 MW) is coupled internally but reaches the mainstem only via Canadian storage.
Everything else — Skagit (840), Cowlitz (532), Lewis (510), Deschutes (513), Willamette, Baker,
Nisqually — is an independent tributary system.

**What the monthly budget does to the chain today:** eleven independent monthly rows. The budget's
granted freedom is nameplate-hours ÷ budget = 1/CF: **Grand Coulee 3.98×, Bonneville 3.38×, The
Dalles 3.15×, John Day 2.90×, Rock Island 2.82×, Wanapum 2.80×, McNary 2.56×, Rocky Reach 2.54×,
Chief Joseph 2.48×, Wells 2.30×, Priest Rapids 2.26×** (2023 annual). A run-of-river plant whose
published pondage is "three to five feet" (BPA *Inside Story* p. 15: run-of-river projects "pass
water at the dam at nearly the same rate it enters the reservoir") cannot use any of that freedom
independently of the plant above it.

**What a mechanism must express (NWPP-36 inherits this; it may not re-derive it):**

1. The identity per link (u → d): `release_u(t) + side_inflow_d(t) − spill_d(t) − release_d(t) =
   Δstorage_d(t)`, with `release_d` bounded by the plant's `P/η·head` and `Δstorage_d` bounded by the
   published pondage band — for the nine run-of-river links, a band of a few hours of flow; for Grand
   Coulee (5.19 MAF) and Brownlee, a seasonal reservoir whose monthly budget stays the measured EIA-923
   one. In energy terms the coupling is `E_d(t) ≈ k_d · E_u(t − τ_ud) + E_side,d(t)` with `k_d` the
   head ratio; the artifact's plant-level `budget_annual_mwh` and the published discharges give
   `k_d` directly (e.g. Chief Joseph / Grand Coulee energy ratio 0.60 at discharge ratio 1.003).
2. **The lag τ is NOT published at mechanism precision** — searched, not found (§8 sources) — and it
   is NWPP-36's to **measure**, not assume: the USACE/CROHMS hourly project-outflow feed
   (`public.crohms.org`, the same source the HRFCPPA cites for its compliance data) gives every
   federal and mid-C project's hourly discharge, so cross-correlating adjacent projects' outflow
   yields τ per link at hourly resolution. Distances for the sanity check: Chief Joseph is at river
   mile 545, McNary at 292, Bonneville at 146.
3. **No instrument couples the seven mid-Columbia projects as one plant in the scored years** — the
   Hourly Coordination Agreement expired ~2019 — so NWPP-36 must couple them **hydraulically only**,
   never as a coordinated single unit; and the PNCA's monthly accounting expired mid-2024.
4. Row count: T × (links) additional equality rows with two or three non-zeros each; with T = 8760 and
   ~14 links that is ~123 k rows — vectorised (rule 2), gated default-off, on
   `_CACHE_KEY_OPTIONAL_FIELDS` (gate G8 as amended).
5. **The HRFCPPA ramp band is an inherited outlet condition:** during the rearing period Priest
   Rapids' daily outflow range is capped at 20–60 kcfs by inflow band, ≈ 0.12–0.36 of a 170 kcfs
   inflow; in energy terms a cap on the within-day swing of the seven-project outlet.

### 5(b) Within-month shaping the monthly budget cannot see

Off the pooled EIA-930 `NG: WAT` (artifact `nwpp_hydro_within_month_930.csv`; 2023–24 means; p95 is
used where the defective hours contaminate the maximum):

| series | nameplate MW | mean / np | p5 / np | p95 / np | (p95−p5) / np | diurnal amplitude (daily max−min) / mean | daily-energy CV within month |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NWPP pool** | 35,799.5 | 0.334 | 0.243 | 0.440 | **0.196** | **0.54** | **0.086** |
| BPAT | 21,686.2 | 0.299 | 0.208 | 0.404 | 0.196 | 0.55 | 0.102 |
| CHPD | 2,037.8 | 0.406 | 0.182 | 0.621 | 0.438 | 1.00 | 0.158 |
| DOPD | 866.8 | 0.460 | 0.233 | 0.689 | 0.455 | 0.91 | 0.156 |
| GCPD | 1,220.0 | 0.745 | 0.434 | 1.074 | 0.640 | 0.71 | 0.159 |
| IPCO | 2,056.7 | 0.422 | 0.279 | 0.579 | 0.300 | 0.62 | 0.115 |
| AVA | 1,174.1 | 0.398 | 0.216 | 0.628 | 0.412 | 0.97 | 0.181 |
| SCL | 2,048.5 | 0.255 | 0.124 | 0.395 | 0.271 | 0.98 | 0.162 |
| PGE | 694.2 | 0.314 | 0.169 | 0.448 | 0.279 | 0.76 | 0.123 |
| TPWR | 724.8 | 0.332 | 0.171 | 0.527 | 0.356 | 0.84 | 0.181 |

(GCPD's p95 > nameplate is Priest Rapids, §3.2; WAUW/PACE/NEVP are the population-mismatch BAs.)

Three magnitudes NWPP-36 and NWPP-40 need:

* **The diurnal swing is half the monthly mean at pool level (0.54) and about one full mean at the
  mid-C PUDs (0.9–1.0)** — the measured within-day shaping the budget LP is free to do, and does. May
  2023 (the freshet) is the exception: pool diurnal amplitude **0.19**, p5 = 14,938 MW against a
  monthly mean of 19,372 — the river ran flat out and there was nothing to shape.
* **The day-to-day signal within a month is small at pool level (CV 0.086) but not zero**, and it is
  a *trend*, not noise: first-week ÷ last-week daily energy runs 0.79–0.80 in November–December 2023
  and 1.16–1.27 in June–July, i.e. the freshet's rise and recession inside a month. A flat monthly
  budget cannot see a 20–27 % within-month ramp, which is the same order as the diurnal swing at BPAT.
* **The measured fleet never approaches zero**: pool Q5 is 0.73 of the monthly mean on average (9,327 MW
  in January 2023 against a 12,931 MW mean), the lower half of the envelope the existing
  `hydro_min_flow_floor` machinery would stamp — 6,031–14,938 MW by month in 2023 — whereas the pure
  budget LP can park 35.8 GW of hydro at 0 MW.

### 5(c) Non-power constraints (fish / flow / spill), the instrument that sets each, and their size here

* **Juvenile fish-passage spill — CRSO ROD 2020**: up to 125 % TDG, 16 h high spill / 8 h reduced,
  beginning of April through the third week of June at six of the eight lower Columbia / Snake
  projects (fish operations start **April 3** on the lower Snake, **April 10** on the Columbia; the
  Priest Rapids spring flow objective of **135 kcfs** runs to June 30 — BPA *Inside Story* p. 40 on the
  BiOp). Published size: **−330 aMW firm under critical water, −210 aMW average across all water
  years for the CRS, −230 aMW regionally**, with the loss concentrated in April–June and generation
  *higher* in late August and winter. **Measured signature on this footprint** (EIA-923 monthly CF
  against nameplate): **Bonneville 0.50 / 0.50 / 0.42 in Jan–Mar 2023 → 0.20 / 0.14 / 0.21 in
  Jun–Aug**; 2024 0.47 / 0.49 / 0.49 → 0.23 / 0.18 / 0.25; the four lower Snake plants 0.29–0.45 in
  Feb–Mar 2024 → **0.09–0.28 across April–August**; McNary 0.58 (Jan 2023) → 0.27 (Jun). Water that is
  there (Grand Coulee and Chief Joseph run 0.50–0.70 in the same months) is routed past the turbines.
  **What the budget LP does with it:** it sees Bonneville's July 2023 budget of 0.14 CF and grants
  **7.1× freedom** — 1,162 MW for 3.4 hours a day, on a run-of-river plant with 3–5 ft of pondage in a
  spill month. There is no spill object; NWPP-36's coupling rows give one for free (spill is the slack
  between upstream release and downstream turbine flow).
* **Flow-fluctuation bands — HRFCPPA 2004** (table in §4): a ramp cap on Priest Rapids outflow during
  spawning, incubation, emergence and rearing, delivered by the seven-project operation.
* **Treaty flows — CRT DOPs**: 1.0 MAF/yr of Canadian storage released for fisheries flows since 1995
  (+0.5 MAF in dry years under the 2024 AIP) — an inflow to Grand Coulee, measured already inside the
  EIA-923 budgets.
* **Flood-control rule curves** (BPA *Inside Story*): variable drawdown Jan–Apr, refill Apr–Jul to
  31 July, fixed Sep–Dec at Grand Coulee, Libby, Hungry Horse, Dworshak, Albeni Falls, John Day — the
  seasonal shape already inside the measured monthly budgets, and the reason a *forecast* year's
  budget must come from the climatology path rather than any rule curve.
* **Minimum sustained release** (licence/BiOp minimum flows): the measured pool Q5 of §5(b) — in a
  forecast the existing `hydro_min_flow_floor` regenerates it from climatology; in a backcast it is
  the same-year measured level, the same admissibility class as outage windows.
* **Instrument timeline inside the scored window, so a later lane does not treat 2023–2025 as one
  regime:** ROD 2020 spill regime through 2023 → **RCBA 2023-12-14** (litigation stay from 2024-02-08,
  increased spill at the eight dams) → **PNCA terminated 2024-09-15** → Canadian Entitlement −37 % from
  2024-08-01 → **RCBA terminated June 2025** → a 2026 court order on spill (reported, post-window).

### 5(d) Storage vs run-of-river — how much of 35,799.5 MW is genuinely dispatchable

EHA `Mode` over the 288 EIA-860 plants, completed for Mode-NaN by the documented
`curate_hydro_plant_modes.py` rule (Corps dam → release-taker; GRanD/HydroLAKES reservoir linkage →
shapeable) **but not curated** — the `hydro_ror_split` arm is a W4/W5 posture:

| class | plants | MW | share of hydro | 2023 TWh |
|---|---:|---:|---:|---:|
| SHAPEABLE — EHA Peaking / Intermediate Peaking | 66 | 17,554.4 | **49.0 %** | 50.62 |
| SHAPEABLE — Mode NaN, reservoir-linked (Ross, Diablo, Séliš Ksanka Qlispé, Carmen Smith, Lucky Peak, American Falls, …) | 32 | 1,479.5 | 4.1 % | 3.33 |
| HYBRID — EHA Run-of-river/Upstream Peaking (Rocky Reach, …) | 10 | 1,735.9 | 4.8 % | 6.64 |
| NOT SHAPEABLE — EHA Run-of-river / Canal-Conduit / Reregulating | 135 | 12,141.9 | **33.9 %** | 35.33 |
| NOT SHAPEABLE — Mode NaN, Corps dam (Chief Joseph) | 1 | 2,456.2 | 6.9 % | 9.39 |
| UNCLASSIFIED — Mode NaN, no linkage | 44 | 431.6 | 1.2 % | 1.19 |

So on the published inventory **~53 % of nameplate (19.0 GW) is classed shapeable and ~41 % (14.6 GW)
run-of-river**, with the mainstem itself split 9,531.8 MW peaking (Grand Coulee, Wells, Wanapum,
Priest Rapids) / 6,778.1 run-of-river (Rock Island, McNary, John Day, The Dalles, Bonneville) /
2,456.2 Corps run-of-river (Chief Joseph) / 1,349.2 hybrid (Rocky Reach). **But "Peaking" on the
mid-Columbia means hours of pondage, not seasonal storage** — the published seasonal storage in this
footprint is Grand Coulee 5.19, Libby 4.98, Hungry Horse 3.16, Dworshak 2.02, Albeni Falls 1.16 MAF
(BPA *Inside Story*), plus Brownlee and the Skagit/Ross reservoirs whose volumes were not transcribed.
**The empirical answer is smaller than the classification:** the pool's shaped band (p95 − p5) is
**19.6 % of nameplate (7.0 GW)**, with the mean at 33.4 %; the mid-C PUDs shape 44–64 % of their
nameplate and BPAT 20 %. What a mechanism needs from this: a per-plant pondage bound (hours of flow
at nameplate) for the coupled chain — the published "three to five feet" needs each pool's area to
convert, which HILARRI's GRanD / NID ids point to but which is **not on disk** — and it is NWPP-36's
to source (NID has surface area and storage per dam), with the EHA class as the fallback partition.

## 6. What NWPP-36 inherits, stated as a specification

1. **Chain membership and order** — §5(a) table and `nwpp_hydro_chain.csv`; the mainstem is eleven
   plants, the lower Snake four, Hells Canyon three; Boundary is not coupled to the mainstem.
2. **Per-plant energy ratios and the published discharges** for `k_d`; measured monthly budgets per
   plant stay the EIA-923 artifact — the coupling redistributes *when*, never *how much* per month
   (the budget row is untouched; rule 19: one mechanism per phenomenon, and the coupling is a second
   phenomenon, not a second floor).
3. **Lag τ per link: MEASURE from CROHMS hourly outflows** (§5(a) item 2); not published at precision.
4. **Pondage bound per run-of-river link: SOURCE from NID** (§5(d)); "3–5 ft" is the published order.
5. **No single-unit coordination of the seven mid-C projects in 2023–2025** (HCA expired).
6. **The outlet ramp band** (HRFCPPA) and the **spill season** (ROD: Apr 3 / Apr 10 → third week of
   June at 125 % TDG 16 h/8 h) as the two published non-power operating conditions on the chain, with
   their measured signatures (§5(c)).
7. **The magnitudes the first keeper's C1 / C4 will be testing**: 56 % of hydro nameplate and 58–59 %
   of hydro energy is in one chain; within-month shaping is a 0.54 diurnal and a 20–27 % intra-month
   trend at pool level; spill collapses Bonneville and the lower Snake to 0.13–0.25 CF for five months.
8. The default-off field, `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in one
   commit, byte-identical keys for every keeper (gate G8 as amended) — NWPP-36's exit, not this
   lane's.

## 7. Routed to NWPP-DESK (not fixed here — outside FILES YOU OWN)

1. **`data/eia930`: the NWPP pool `NG: WAT` carries the G20 defective hours** (AVA 810,113 MW at
   2025-10-12 10:00 UTC and four more; NWMT 65,891 / 65,880 in 2024). NWPP-10's repair is demand-side;
   `measured_monthly_hydro` / `measured_hydro_min_flow_level` / the envelope read the unrepaired column.
   Until repaired, `eia930_monthly` and the 930-derived hydro floors/envelopes are unsafe for NWPP 2024–25.
2. **930 vs 923 population mismatch (−2.7 TWh, stable)** — WAUW (−2.6/−2.8 TWh) and PACW (−0.7) file
   their EIA-923 hydro plants' generation under other EIA-930 BAs; Priest Rapids sits in BPAT (860) and
   GCPD (930). Any level pin between the two series needs a reconciliation the loader does not have.
3. **Swift 2 (72 MW, PACW)** has no EIA-923 series in either complete year — an id question.
4. **`curate_hydro_plant_modes.py`** registers CAISO only; an NWPP curation is a W4/W5 lever
   (`hydro_ror_split`), and §5(d) is the evidence it would start from.
5. **PNCA terminated 2024-09-15** with no successor text found — the coordinating instrument changes
   inside the scored window; NWPP-40's PRECOMMIT should state it.

## 8. Sources — URL and status (no value from memory)

| source | URL | status |
|---|---|---|
| CRS R43287, *Columbia River Treaty*, 2024-12-03 | `https://www.congress.gov/crs_external_products/R/PDF/R43287/R43287.30.pdf` | 200, 19 pp, text extracted locally (pypdf) |
| BPA, *The Columbia River System Inside Story* | `https://www.bpa.gov/-/media/Aep/power/hydropower-data-studies/columbia_river_inside_story.pdf` | 200, 80 pp, extracted |
| CRSO Record of Decision, 2020-09-28 (public-inspection copy) | `https://public-inspection.federalregister.gov/2020-22147.pdf` | 200, 135 pp, extracted; `federalregister.gov` HTML 302 → unblock page; `nwd.usace.army.mil/CRSO/` 403 |
| 1997 Pacific Northwest Coordination Agreement | `https://www.grantpud.org/templates/galaxy/images/1997PNCAAgreement.pdf` | 200, 117 pp, extracted |
| Hanford Reach Fall Chinook Protection Program Agreement, 2004-04-05 | `https://www.grantpud.org/templates/galaxy/images/hanfordReachFallChinookProtectionProgramAgreement040504.pdf` | 200, 24 pp, extracted |
| CRS R48089 (lower Snake) | `https://www.everycrsreport.com/reports/R48089.html` | 200 (HTML summary) |
| ODOE, *Columbia Basin Hydropower Developments*, Jan 2025 | `https://www.oregon.gov/energy/energy-oregon/Documents/ODOE-Columbia-Basin-Hydro.pdf` | 200; no generation figures |
| newsdata.com, *Coordination gives way to cooperation on Mid-Columbia* (2020-05) | `https://www.newsdata.com/water_power_west/hydro_news/coordination-gives-way-to-cooperation-on-mid-columbia/article_53900cb6-9a1e-11ea-a042-03a051911225.html` | **429**; expiry taken from the search snippet only |
| BPA treaty page | `https://www.bpa.gov/energy-and-services/power/columbia-river-treaty` | **404** |
| B.C. AIP page; NWCouncil RCBA note (2025-01-24); Idaho Conservation League RCBA note; hydroreform.org Boundary P-2144; Seattle City Light licence notices | search-level | not fetched |
| ORNL EHA FY2024; HILARRI v4; EIA-923 / EIA-860 | committed under `data/raw/` | on disk |

## 9. Rules

1 `[R-STRUCT]` — no residual exists and none was consulted; every decision here (the empty entry
set, the refused repin) rests on instruments and rule 14. 13 `[R-MEASURED]` — nothing filled, nothing
rescaled; the artifact is the source, reconciled. 14 `[R-ACCURATE]` — the Klamath dams' real 2023
energy is kept at the loader's fallback; the pool level is refused because it is *less* accurate for
this population, stated with the decomposition. 23 `[R-FROZEN-DERIVE]` — the artifact regenerates
only when EIA-923 / EIA-860 / EHA / HILARRI update. 27 `[R-PUSH]` — new files only; no existing
source file rewritten. 28 `[R-MECH-MATRIX]` — no mechanism tested, no field added; NWPP-36 adds the
row. Collision rules — no shared record touched; the `## Log entry` below is for the desk.

## 10. Deliverables and retrievability

All on this branch: `data/raw/nwpp-hydro/{nwpp_hydro_budget.parquet, nwpp_hydro_reconciliation.csv,
nwpp_hydro_chain_published.csv, nwpp_hydro_chain.csv, nwpp_hydro_within_month_930.csv}` + README rows;
`scripts/data/build_nwpp_hydro_budget.py` (regenerates all five in ~2 min); PRECOMMIT + this FINDING.
Zero LP; nothing is on ephemeral disk that a promotion would need.

## Log entry

`docs/calibration-log/nwpp.md` is a shared record this lane may not create; the desk appends this:

> **nwpp-32 — 2026-09-14.** Hydro budget + envelope built for the 288 EIA-860 conventional-hydro
> plants (35,799.5 MW; PS 314.0 MW excluded) from NWPP-11's EIA-923 extract: **every plant-year
> reconciles to EIA-923 annual at 0.000 MWh** (290 / 286 / 25 reporters); 263 plants have no 2025
> series and are flagged, not filled; loader reproduces the artifact to 0.00e+00. Envelope = 860
> nameplate, no floor. `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` **empty** — eight instruments
> read, none states a plant period; the PNCA's own "Period means a calendar month". **§2.7 (a) chain
> read from ORNL EHA + BPA published discharges: eleven mainstem plants Grand Coulee → Bonneville,
> 20,098.8 MW = 56.1 % of hydro / 58–59 % of energy; lower Snake 3,033 MW; Hells Canyon 1,276 MW;
> Boundary is Pend Oreille, not mainstem** (desk's list corrected). (b) pool diurnal 0.54, intra-month
> trend 20–27 %, Q5 = 0.73 of mean; (c) ROD 2020 spill 125 % TDG 16 h/8 h Apr→3rd wk June, −210 aMW
> CRS / −230 aMW regional, Bonneville CF 0.50 → 0.14; HRFCPPA ramp band 20–60 kcfs; (d) 53 % shapeable /
> 41 % RoR by EHA, empirical shaped band 19.6 % of nameplate. **2025 posture: `backfill_year=2024`
> only; `eia930_monthly` REFUSED** — the pool `NG: WAT` is a different population (−2.52 %, WAUW/PACW/
> Priest Rapids BA assignment) and carries the G20 defective hours (+1,166 GWh = 14.1 % of Oct 2025).
> Routed: eia930 NG:WAT defect repair; 930/923 population reconciliation; Swift 2 id. No solve.
> FINDING: `docs/handoffs/FINDING-nwpp-32-2026-09-14.md`.
