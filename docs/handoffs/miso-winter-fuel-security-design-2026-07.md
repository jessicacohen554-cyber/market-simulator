# miso-72 — Winter Fuel Security (leg c): design freeze

**Status:** Phase-A frozen 2026-07-17 (this session). Diagnosis frozen (below);
mechanism spec, cited parameters, pre-registered bands and R-criteria frozen
BEFORE the Phase-B build. Base recipe = the promoted MISO keeper
`2026-07-17-miso-71-midwest` (compose ONE new mechanism on it).

**Lane:** MISO backcast-calibration, charter "fuel-security / gas_daily_shape /
seam family". Owns the **Jan-14-17-2024 Winter Storm Heather** tail.

**Model per rule 27:** Opus/Fable (this session intakes data AND writes core
`src/market_sim/data/fuel.py`; never Sonnet).

---

## 1. The FROZEN diagnosis (2024 MISO SOM pp.10-12 + 5-agent forensic sweep — DO NOT relitigate)

Jan-14-17-2024 = Winter Storm Heather (polar vortex, MLK weekend). Attribution,
ranked:

1. **DELIVERED GAS-PRICE / citygate basis spike — the PRIMARY documented driver.**
   SOM p.10: *"Gas prices were volatile and required the IMM to actively update
   generator reference levels"*; *"multiple pipelines signaled the likelihood of
   restrictions"*. Henry Hub daily spiked $13.20 on 2024-01-12 (4.16× the Jan mean).
2. **HIGH LOAD** — record South winter peak 32.6 GW (SOM p.10); already in the
   model (weather-driven), not a new mechanism.
3. **LOCAL SETEX congestion** — the ONLY true extreme (TEXAS.HUB $1070.3, Jan-16
   HE08). SOM p.11: *"high load, a transmission outage, and inadequate generation"*
   in the SE-Texas load pocket, resolved only when a dually-connected unit switched
   ERCOT→MISO. This is a transmission/load-pocket phenomenon, **OUT OF
   REPRESENTATION** in a 6-zone reduced network (the ERCOT sub-zonal-congestion
   ledger precedent). miso-72 MUST NOT try to reproduce it; pinning any adder to
   the $1070 print is rule-13-forbidden (a measured local outcome with no forward
   analogue).

**REFUTED ROUTES — pre-adjudicated, DO NOT BUILD:**
- **RESERVE scarcity: REFUTED.** miso-71 measured RT reserve MCP ~$3 in the window;
  SOM p.12 event RSG only $5M (vs $90M Uri, $15M Elliott); STR raised precautionarily
  but did not price. No reserve/ORDC/RCPF path for Heather (would contradict the
  measured ~$3, rule 19).
- **AVAILABILITY DERATE (the NEISO `neiso_gas_coldsnap_derate` template): REFUTED.**
  SOM p.10: generators *"seemed better prepared for the cold temperatures, so forced
  outages were LOWER"* than Uri/Elliott. CAMPD confirms net gas-fired offline
  overlapping Jan-14-17 (15.1 GW) is LOWER than surrounding 4-day windows — no net
  capacity-loss event above baseline. An Elliott-anchored derate would FABRICATE
  unavailability the SOM says did not happen (rules 1/13). Do not build a MISO
  cold-snap derate.

**The ONE admissible mechanism:** a measured **daily MISO citygate delivered-gas
overlay**. The keeper misses the tail (`gas_daily_shape=true` already ON) because
it is mean-preserving per month AND — via an even-spread `np.interp` — **mislocates**
the Jan-12 national Henry-Hub spike to Jan-13, so the actual tail days Jan-15/16/17
get factors 0.88–0.96 (BELOW average), model gas ~$4/MMBtu there vs the ~$8-13/MMBtu
a marginal MISO gas unit needs for the observed ~$90/MWh tail. National HH also
misses the regional Chicago citygate basis blowout entirely. The monthly Chicago
basis (`gas_basis_by_iso_month.csv`, MISO Jan-2024 ≈ +$1.82/MMBtu) is present but
too small/flat to form a 4-day tail. The irreducible missing signal is the DAILY
regional citygate — landed in Phase 0 (below).

---

## 2. Phase 0 — the data that landed (2026-07-17, this session)

`data/raw/gas-prices/miso_citygate_daily.csv` — **680 daily Chicago Citygate
delivered-gas prints, 2023-01-05 … 2025-12-17** (per-year 232 / 224 / 224 weekday
trading days), columns `date, chicago_citygate_usd_mmbtu, henry_hub_usd_mmbtu,
source`. Scraped by `scripts/data/fetch_miso_citygate_daily.py` from the **"Chicago"**
row of the EIA Natural Gas Weekly Update compact "Spot Prices ($/MMBtu)" table
(`archivenew_ngwu/YYYY/MM_DD/`) — the same free EIA-displayed NGI Daily GPI table
the CAISO ("Cal. Comp. Avg") and NYISO ("New York") daily scripts already read.
`SOURCES_miso_citygate.md` + `README.md` + `docs/multi-iso/miso-data-audit.md`
Item 4 updated.

**The measured winter signal (the whole point):** the Winter Storm Heather week
(EIA page `2024/01_18`, column dates 11/12/15/16/17-Jan) shows Chicago Citygate
**$3.00 → $25.82 (Jan-12 Fri) → N/A (MLK) → $3.76 → $2.89**, against Henry Hub
$3.13 → $13.08 → N/A → $4.15 → $2.87. On the Friday that priced storm-weekend
delivery, **Chicago Citygate = $25.82/MMBtu (+$12.74 over Henry Hub)** — the exact
regional blowout the diagnosis names, and completely missed by both national HH
`gas_daily_shape` and the flat monthly Chicago basis (+$1.82). The narrative-only
method would have reported "unchanged at $2.89" (Wed-to-Wed) and missed it entirely
— the structured table is decisively superior.

**Sub-source limits (rule-11 reconciliation, documented, not hidden):**
- **MichCon is NOT free.** The EIA compact table carries no MichCon/Michigan row and
  the narrative never quotes a MichCon daily print (verified). Lower-Michigan's
  citygate daily stays the paywalled ICE manual-download item (`miso-data-audit.md`
  Item 4 remains partially open). **Chicago Citygate is the representative MISO
  North/Central winter gas hub** for the mechanism; the daily series is Chicago-only.
- **Weekly-broadcast granularity** is NOT a factor here — the structured table gives
  genuine weekday-daily prints (not the algonquin "last_wednesday" broadcast), so
  the single-Friday cold-snap print lands on its true calendar day.
- **Licensing:** the Chicago spot is NGI's Daily GPI displayed by EIA — the same
  proprietary-index provenance flagged for the sibling AGT/CA/NY daily files
  (`README.md`, `docs/data-licensing.md` §5). Carried forward, not resolved here.

Per-year winter shape (flow-date, mean-preserving; §3): **2023 near-inert** (peak
1.13–1.22×, 0 days >1.5×, no MISO winter event); **2024 Jan 4.67×, 4 days** (Heather,
Jan-13–16); **2025 Jan 2.23× + Feb 1.92×, 6 days** (Jan-17 $9.92, Feb-18/19 $6.98/$7.82).

---

## 3. Phase A — the mechanism (FROZEN)

### 3.1 What it is

`miso_winter_citygate_daily` (ScenarioConfig **tier 3, default OFF**, MISO-scoped) —
a **zone-aware, shape-only, mean-preserving winter daily gas overlay**. In the
**winter months {Dec, Jan, Feb}** only, for the MISO gas units in the **Chicago-hub
zones only** (MISO-Illinois, MISO-Indiana, MISO-East — the zones the published
`miso_zonal_gas_hub.csv` assigns to "Chicago Citygate (IL)"), it **replaces the
national-Henry-Hub `gas_daily_shape` within-month daily shape with the measured
Chicago Citygate daily shape**, placed on **gas FLOW days** (trade + 1, weekend/
holiday packages forward-filled — `_flow_date_staircase`) and **renormalized to
mean 1.0 within each month** so the monthly gas level (and hence the already-correct
monthly LMP) is UNCHANGED.

Concretely, inserted in `resolve_fuel_prices` **immediately before
`apply_miso_zonal_gas_basis`** (so it operates on rows still equal to
`level × national_shape`, before the additive zonal spread):

```
for each Chicago-hub MISO gas row g, for each winter-month hour t:
    fuel_prices[g, t] *= chicago_shape[t] / national_shape[t]
    #  = level × national × (chicago/national) = level × chicago
```

where `national_shape = gas_daily_shape_factors(year, T)` (the exact factor line
3564 applied; all-ones if `gas_daily_shape` is off) and `chicago_shape` is the
flow-date, mean-preserving Chicago daily shape. Non-winter months, non-Chicago
zones, and the off-state are byte-identical.

### 3.2 Why shape-only, zone-aware, flow-date (the data-informed refinements)

The Phase-0 data sharpened the handoff's pre-data sketch on three points, each a
rule-1/rule-13 requirement, NOT a free choice:

1. **Shape-only (not the level-replacing `apply_hub_basis_overlay`).** The keeper's
   MISO January LMP is already correct (model Illinois-hub Jan $35.0 vs actual $33.0;
   handoff). The hub-basis-overlay REPLACE path would swap the monthly LEVEL from the
   keeper's measured EIA-923 ISO-month construction to `HH + Chicago-basis`, moving
   that already-correct monthly — forbidden (rule 11: never move a correct level to
   chase a residual). So the overlay is **mean-preserving within month** — it only
   redistributes the within-month shape. This is the handoff's rule-19 option (b),
   "a pure winter-daily shape layered on the zonal-split base," made explicit.
2. **Zone-aware (Chicago-hub zones only).** MISO-North/Central prices off Chicago
   Citygate; **MISO-South prices off Gulf/Henry Hub** and MISO-West/Plains off MidCon.
   The Chicago blowout ($25.82) is ~2× the Henry-Hub spike ($13.08); applying the
   Chicago shape to the Gulf-priced South would over-amplify the South's daily gas
   swing and risk spuriously lifting South LMP toward the out-of-representation
   SETEX print (R2). So the Chicago shape hits only the zones the published
   `miso_zonal_gas_hub.csv` maps to Chicago; West/Plains/South keep their existing
   national-HH shape (HH is a conservative under-proxy for MidCon/Gulf — rule 14,
   never over-reach). The zone selector is READ FROM the same published file
   `apply_miso_zonal_gas_basis` uses — no new magic mapping (rule 5).
3. **Flow-date placement (trade + 1, weekend/holiday forward-fill).** The daily
   citygate is a next-day-delivery index; Friday's trade prices the whole
   Sat-through-Monday (holiday-extended) weekend package. The Jan-12 $25.82 Friday
   print is the physical delivered cost of gas FLOWING Jan-13/14/15/**16** (MLK Mon
   is a no-trade holiday; the record-peak Tuesday Jan-16 burned gas bought Friday).
   The even-spread `np.interp` in `gas_daily_shape_factors` mislocates it to Jan-13
   and drops the true tail days to 0.88–0.96×; the flow-date staircase
   (`_flow_date_staircase`, the caiso-90 precedent) places it correctly on
   Jan-13–16 = 4.67×. Verified: monthly-mean factor = 1.000 (mean-preserving).

### 3.3 Rule-19 reconciliation (REPLACE/COORDINATE, never STACK)

- **vs `gas_daily_shape` (national HH, ON):** SUPERSEDED for Chicago-zone winter
  cells via the `chicago/national` correction — the national shape is divided out
  and the Chicago shape multiplied in (replace, not add). The nyiso_downstate_ct_gas
  precedent ("force the national sibling off when the regional daily is on"), applied
  at cell granularity (Chicago zones × winter months). Non-winter / non-Chicago cells
  keep national unchanged.
- **vs `miso_zonal_gas_basis` (annual mean-zero N/S spread, additive, ON):** NO
  double-book. The winter overlay is a multiplicative, mean-preserving-within-month
  TEMPORAL shape on the level; the zonal basis is an additive, annual, mean-zero
  SPATIAL spread read statically from `miso_zonal_gas_hub.csv`. The overlay runs
  BEFORE `apply_miso_zonal_gas_basis` and preserves every zone's annual mean, so the
  zonal basis's capacity-weighted mean-zero anchor is unperturbed and its per-zone
  additive spread lands un-shaped. Orthogonal components; the "Chicago spread" the
  zonal basis books (annual level) is never re-booked by the overlay (mean-1 shape).
- **Dual-fuel oil-parity min runs AFTER** (`apply_dual_fuel_pricing`, rule 14
  ceiling) so the winter spike cannot exceed oil parity where oil-capable units exist
  (MISO keeper: dual_fuel off, so no cap fires — the shape is bounded by the measured
  spot regardless: base×4.67 ≈ $21 < measured $25.82).

### 3.4 Cited parameters + DOF

**Zero fitted scalars.** The DOF ledger entry (main = base + 1) is the **measured
daily Chicago Citygate series** (`miso_citygate_daily.csv`, EIA-sourced). Everything
else is structural / data-sourced:
- Chicago-hub zone set {Illinois, Indiana, East} — READ from `miso_zonal_gas_hub.csv`
  `hub == "Chicago Citygate (IL)"` (the existing published assignment; identification
  source = the same file `apply_miso_zonal_gas_basis` reads).
- Winter months {12, 1, 2} — the pipeline-scarcity heating season (structural scope,
  the meteorological-winter convention; every measured MISO winter event 2023-2025
  falls inside it). Not a fitted knob.
- Flow-date convention (trade + 1, weekend/holiday forward-fill) — the NG gas-day
  market structure (`_flow_date_staircase`, caiso-90 precedent).

**Forward story (rule 13 admissible):** a forecast year takes the forward gas curve's
regional Chicago basis and its own daily/weekly shape — forward-native, responds to
changed conditions (a warmer forecast winter → smaller shape; more Chicago demand →
larger). The mechanism regenerates from forward drivers, so it is a legitimate input
even though it is exercised here in backcast.

### 3.5 Pre-registered bands (HONEST — per the rule-1 scoring nuance)

The C3c scoring hub is **Indiana**, where the whole Jan-14-17-2024 event is ~1 tail
hour ($227.68) and only 2 of 37 annual 2024 tail hours are in January. A CORRECT
winter mechanism moves scored C3c by ~1-2 hours AT MOST. Its correctness is validated
**per-zone** (South/West/Plains hourly LMP vs the TEXAS/MINN/ARKANSAS/LOUISIANA hub
actuals in `data/raw/lmp-data/MISO/miso_hub_lmp_2024_rt.csv.gz` Jan-14-17), NEVER by
the C3c residual. Do not reject the mechanism because C3c barely moves (rule 1); do
not tune anything to move it (rules 1/13).

| Metric | Band | Rationale |
|---|---|---|
| **C3c-2024 (Indiana, scored)** | **[7, 9]** hours | ≈ keeper (7); the event is off the scoring hub. +1-2 at most, R2-clean. |
| **C3c-2023 / C3c-2025 (scored)** | [0, 2] / [0, 2] from keeper | 2023 near-inert; 2025 modest lifts off the Indiana hub. |
| **C3b (all years, ABSOLUTE)** | **≤ 0.20** (standing veto); 2025 headroom 0.016 | Wrong-shape veto. |
| **C3b mechanism-only Δ** | **≤ +0.005** all years | A winter-only shape must not broaden non-event months. |
| **C3a-2024** | watch, **≤ ±0.5%** | Winter is a handful of hours; annual bias barely moves. |
| **C1 CC_REGULAR-2023 / C3a-2025 / C2 / C4 / C5a / C6 / C7 / C8** | = keeper (no regression) | Not this lane's levers; mean-preserving ⇒ neutral. |
| **PER-ZONE fidelity (South/West/Plains, Jan-14-17)** | **IMPROVES** | The real deliverable. |
| **DOF main** | base **+1** (measured daily Chicago series) | Zero fitted scalars. |

### 3.6 R-criteria (pre-declared — refutes the mechanism if hit)

- **R1 — C3b breach.** C3b any year > 0.20 → **REFUTED** (wrong-shaped / too-broad
  gas surface). Standing shape veto.
- **R2 — SETEX fabrication.** The overlay must NOT reproduce the $1070 SETEX print
  (out of representation). Any hour a Chicago-zone LMP the overlay lifts reaches the
  $1000+ range is a **red flag, not credit** — investigate, do not bank. (Gas at
  ~$21/MMBtu tops a 10-HR unit at ~$210/MWh; anything near $1070 is a bug.)
- **R3 — no double-count.** Off-state LP byte identity vs the keeper; covered-month
  supersession of `miso_zonal_gas_basis` and `gas_daily_shape` verified (the winter
  overlay adds no annual mean; the zonal spread and monthly level are unchanged).
- **R4 — inertness.** If the daily series does not materially lift the Jan-14-17 tail
  days (Chicago-zone gas < ~1.5× base on the flow days), close honestly and ledger
  (data granularity insufficient) — do NOT reach for a fitted amplifier (rule 13).
  [Pre-read: 2024 flow-day factor 4.67× → NOT inert. 2023 inert by construction —
  no event; that is honest, not a failure.]
- **R5 — honesty.** A C3c-Indiana gain must be attributable to Jan-14-17 hours, not
  spurious; the per-zone read (South/West/Plains vs actuals) is the validation, not
  C3c. A run whose C3c improves for a non-Heather reason is refuted.

### 3.7 Separate, worth-doing-regardless bug (flag; do NOT fold into the miso-72 verdict)

`gas_daily_shape_factors` (`fuel.py:1354`) uses an even-spread `np.interp` that
mislocates a convex single-day HH spike bracketed by a trading-holiday gap (Jan-12
spike → modeled Jan-13). Fix precedent: NYISO's `_transco_z6_daily_dated`
(true-date placement) + the flow-date staircase. This is an ALL-ISO correctness fix
(national HH shape), tracked separately; it will NOT close the MISO tail alone
(mean-preserving keeps the tail-day level ~$4 nationally), so it stays OUT of the
miso-72 keeper case. Filed as a follow-up.

---

## 4. Phase B — build / probe / register plan

- **Build:** `apply_miso_winter_citygate_daily` + a `miso_chicago_daily_shape_factors`
  helper in `fuel.py`; `ScenarioConfig.miso_winter_citygate_daily` (tier 3, default
  off) + tier map + CLI flag; wire the call before `apply_miso_zonal_gas_basis`.
  Tests: trivial 1-gen/1-zone/24-h (a covered-month covered-zone overlay lifts a
  cold-snap flow day without moving the monthly mean; off-state byte identity;
  rule-19 supersession of national shape + non-perturbation of the zonal spread;
  non-Chicago zones untouched; non-winter months untouched). `fuel.py` ≥ 300 lines →
  rule-27 push-integrity (edit locally, push exact bytes, verify blob after push).
- **Probe:** on the `2026-07-17-miso-71-midwest` keeper recipe (strict meta replay
  via `replay_keeper.build_kwargs`; the new flag via `prb_overrides`; base = keeper
  structure). MISO 2023+2024+2025 one bundle each, per-year + `--reuse-solved`, years
  ALWAYS sequential (rule 12), main/base back to back; COMMIT code before solving
  (dirty tree disables reuse → OOM at the ~16 GB box). `MALLOC_ARENA_MAX=1
  MARKET_SIM_HIGHS_THREADS=1`. NEVER offload a solve to CI.
- **Validate PER-ZONE** (South/West/Plains hourly LMP vs TEXAS/MINN/ARKANSAS/LOUISIANA
  actuals Jan-14-17), not C3c.
- **Register BOTH** runs whatever the verdict (rule 15): bundle → legitimacy_diagnostics
  → attestation/DOF → dashboard_add_run (labels ≤4 non-stopword words) →
  calibration_verdict --write-metrics → check_registry_payload_parity → build_manifest
  → calibration-log (LEAD with the dashboard result + the per-zone validation, NOT
  C3c). MISO registry AT 15 → honour top-15-per-ISO retention. Keeper recommendation
  per R-criteria; **keepers.json swap is OWNER-ONLY**.

**Guardrails (inherited):** rule 22 (MISO no calibration-complete marker — solve
2023/2024/2025 ONLY, one bundle); rules 1/11/13/14/19 (right structure first; measured
inputs only; never tune to a residual; a worse/unchanged fit from accurate data is a
discovered constraint, not a revert trigger); no reserve/derate path; no SETEX chase;
no monthly-to-actuals pin; no RBDC/zonal-ORDC/VOLL edit; C3b ≤ 0.20 absolute standing
veto.
