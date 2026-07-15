# MISO price-formation lane — Phase A diagnosis + design (Fable → Opus)

**Date:** 2026-07-15. **Session:** `claude/miso-price-formation-phase-a-0igp3n`
(Phase A — diagnosis/design only; Phase B executes from this document, the
same Fable→Opus split that produced miso-66 from
`miso-coal-conduct-design-2026-07.md` and the run-66 triage from
`miso-run66-triage-design-2026-07.md`). **Lane:** the two remaining MISO fail
criteria after the ST_GAS lane — **price_mean (C3a-2025)** and **price_tail
(C3c 2024/2025)**. Deliverable is the dashboard, not this doc (rule 15):
Phase B ends with registered runs on the backcast run explorer and a keeper
recommendation; keeper swaps are owner-only.

Every number below is live-scored (`calibration_verdict.py
2026-07-14-miso-66-coalconduct --json`, this session), recomputed from the
committed payload/bench/LMP/CAMPD files this session, or read from a primary
tariff/market document fetched this session. Nothing is fit to a residual; no
solve was run or registered (rule 16 — Phase A produces no keepers).

**Keeper verification (redo first in Phase B):** MISO keeper =
`2026-07-14-miso-66-coalconduct`, determination **NOT-YET**, fail set
**{fuelmix, price_mean, price_tail}**. C1 15/16 (sole gated FAIL ST_GAS-2024
−9.13; 2025 prelim-923). C3a −0.9% / −7.1% / **−13.7%** (2025 FAIL). C3b
PASS ×3: 0.081 / 0.118 / **0.187** (0.013 from the ≤0.20 veto). C3c PASS/
FAIL/FAIL: 0h vs 1h · 4h vs 24h · **0h vs 38h** DA >$200 (RT diagnostic
30/37/88). DOF 19/2. If the keeper moved, STOP and reconcile with
`docs/calibration-log.md` before executing anything here.

## miso-67 status finding (checked 2026-07-15, this session)

**miso-67 (`st_gas_mustrun_p25_level`) has NOT landed.** No ScenarioConfig
field, no probe script, no bundle (`results/calibration/miso67*` absent), no
registry sidecar, no calibration-log entry. It exists only as the frozen
Issue-2 design in `docs/handoffs/miso-run66-triage-design-2026-07.md`.
Consequence for this lane:

- The price lane **can be designed now** (this doc) but its deciding probes
  **must be sequenced after miso-67's probe verdict**, because (a) the July
  North-up separation channel is supplied by miso-67's honest South-steam
  commitment (the S→N pull), and (b) the C3b-2025 veto headroom (0.013) is
  shared — miso-67's mechanism-only footprint gets first claim on it.
- **Phase B therefore begins by executing miso-67 verbatim from the triage
  doc** (its Issue-2 checklist, including the pre-declared V2b fallback),
  then composes this lane's probe on whatever stack survives miso-67's own
  gates. Both branches are pre-declared in the sequencing memo below.
- The triage doc's Issue-1 display fix (the 22-TWh header wedge, no solve)
  was also not executed; it remains independent and ships first.

## Classification summary

| issue | classification | one-line root cause |
|---|---|---|
| C3a-2025 (−13.7%), Jun/Jul monthly | **(B) mechanism, two channels** | Jun/Jul is ~all missing **North-up separation** (model July zonal spread $0.55 vs measured N−S hub spread $21.5) — the S→N pull is miso-67's channel, already designed; the event-day residual is channel 2 below |
| C3c 2024+2025 (4h vs 24h, 0h vs 38h) | **(C) data intake + re-read, not a new curve** | every material tail cluster sits inside a *declared* MISO emergency window (Jan-2024 winter Max Gen Emergency = ALL 24 of 2024's tail hours; Jun-23/24-2025 Max Gen Event; Jul-24/28/29-2025 advisories/warnings; Aug-24-2023 event); the armed in-LP RDC machinery prints 0h because the stack carries phantom headroom at exactly those windows — fix = declared event-window registry + CAMPD revealed derates inside those windows, then RE-READ the existing RDC |
| Schedule 28 VOLL/RDC anchors | **verified — no backcast change** | primary docs confirm $3,500 VOLL + stepped ORDC were the in-force tariff until **2025-09-30** (ER25-579 reforms effective then); 37 of 38 scored 2025 tail hours precede the switch — the constants are correct for the scored window; the post-9/30 regime is a forecast-lane item |

## 1. price_mean (C3a-2025) — root cause, quantified two-sided

Recomputed this session from the keeper's committed payload
(`runs/2026-07-14-miso-66-coalconduct.js`) + bench (`bench/MISO/2025.json.gz`),
demand-weighted zonal model vs RT load-weighted actual:

| month (2025) | model | RT-lw actual | Δ |
|---|---|---|---|
| Jan | 42.07 | 51.23 | −9.2 |
| **Jun** | 40.78 | 57.37 | **−16.6** |
| **Jul** | 41.40 | 59.47 | **−18.1** |
| Sep | 37.72 | 46.37 | −8.7 |
| Dec | 42.78 | 47.25 | −4.5 |
| May | 37.97 | 33.94 | **+4.0** (two-sided: the model is HIGH in May) |
| annual | 39.18 | 45.39 | −13.7% (C3a FAIL) |

July-2025 model zonal prices span **$0.55** (Indiana 41.51, South 41.09,
Illinois 41.64 — uniform), recomputed from the payload `pMon`. The measured
July DA hub record (recomputed this session from
`data/raw/lmp-data/MISO/miso_hub_lmp_2025_da.csv.gz`): North hubs
MINN 60.15 / INDIANA 58.79 / MICHIGAN 58.62 / ILLINOIS 55.84 vs South hubs
LOUISIANA 38.61 / TEXAS 37.69 / MS 36.21 / ARKANSAS 34.84 — **North mean
58.35 / South 36.84, spread $21.51** (June: 45.19 / 34.27, spread $10.92).
The model's uniform ~$41.4 sits AT/ABOVE the actual South: the entire scored
July gap (Indiana-hub benchmark) is the missing North premium, per the lane-3
finding (93% congestion, one-sided, corridor exonerated — the North margin is
the defect). Unchanged from the triage; the numbers above re-verify it on the
current keeper.

**Channel ownership (rule 19 — nothing new to build for the separation):**

1. **The S→N pull = miso-67** (Issue 2 of the triage doc, frozen there). The
   honest South-steam commitment level reverses the model's N→S serving
   direction and lets the already-armed RDT/TCDC/RPE machinery earn the
   separation. How much of C3a-2025 it buys is **unknowable without its
   probe** — Phase B's FIRST deliverable is that read (July zonal spread,
   S→N binding hours vs the measured 919, C3a-2025 delta) from miso-67's own
   probe bundle before anything else in this lane is decided.
2. **The event-day residual + the tail = §2's registry channel** (~$6 of
   July per the diagnosis decomposition; Jan/Jun energy too, see §2).
3. **Jan/Sep/Dec (~$1.9 of the annual gap)**: Jan-2025 is partly §2's
   winter-event leg (8 tail hours Jan 20-22 + elevated non-tail event-window
   prices); Sep/Dec have no declared-window story and stay open residual —
   NOT force-closed in this lane (no mechanism without a driver, rule 12).
4. **NOT this lane: G-23 import starvation** (2025 model imports 13.2 vs
   19.0 TWh actual). Fixing it ADDS supply and LOWERS prices — it pulls
   C3a-2025 the wrong way. It stays in the measured-seam-ladder lane and is
   sequenced LAST so its C2 gain doesn't mask this lane's price reads.

## 2. price_tail (C3c) — the tail is declared-window-coincident

Recomputed this session from the DA hub record (Indiana hub, the scored C3c
basis), every DA hour > $200:

| year | tail hours | day clusters | declared MISO instrument (per public record) |
|---|---|---|---|
| 2023 | 1 | Aug 24 (1h, $204.68) | Maximum Generation Event, Aug 24 2023 |
| 2024 | **24 — ALL January** | Jan 14 (2h) / Jan 15 (7h) / Jan 16 (13h, $284.59) / Jan 17 (2h) | winter arctic-blast Maximum Generation Emergency (Winter Storm Heather window) |
| 2025 | 38 | Jan 20-22 (8h) · Feb 20-21 (2h) · Jun 23-24 (11h, $327) · Jul 24/28/29 (15h, $433) · Sep 29 (1h) · Oct 6 (1h) | Jan cold-snap advisories; **Jun 23-24 declared Max Gen Event** (the summer's only one); **Jul 28-29 ran under capacity advisories/warnings, NOT a declared event** (RTO Insider: "MISO Skirts Max Gen Emergency in July Heat") |

Two structural conclusions this table forces (both NEW vs the triage doc's
summer-only framing):

- **The 2024 C3c FAIL is a WINTER event.** All 24 hours are Jan 14-17. A
  summer-scoped registry would leave 2024 untouched. The registry and the
  derate channel MUST cover winter declarations (freeze-offs / fuel-supply
  derates are the same CAMPD-revealed construction).
- **The registry must record the full escalation ladder** — Capacity
  Advisory → Maximum Generation Alert → Warning → Event Steps (the pre-2026
  structure; MISO's 3-step simplification takes effect 2026-06-01, KA-01551)
  — because July 28-29 2025 (15 tail hours, the deepest prices) was
  advisory/warning-level, never a declared Event. Identification below works
  at any declared level.

### 2a. Event-window unavailability, recomputed on the CURRENT extracts

The diagnosis §4 numbers (11.9 GW absent / 3.6 covered / 8.4 invisible at the
Jul 28-29 peak) predate the miso-65 outage-extract regeneration and used a
different capability basis. Recomputed this session from CAMPD unit-level
(fleet = `bin_assignments_MISO.csv`) against the **current committed**
`campd-unit-outages-MISO.csv` (4,418 rows) + short companion, on a defined
basis: unit capability = max gross load in the event month; event output =
unit's **best hour** inside the event blocks (crediting any hour it reached);
"covered" = any std/short window overlapping the blocks:

| event (blocks) | reduced/absent | overlay-covered | invisible | invisible by class (GW) |
|---|---|---|---|---|
| Jul 28-29 2025 (h13-19) | 9.39 GW | 3.96 | **5.43** | COAL 1.74 / CT 1.56 / CC 1.26 / ST_GAS 0.21 / CHP 0.66 |
| Jun 23-24 2025 (h13-19) | 10.75 | 6.37 | **4.38** | CT 1.30 / CC 1.22 / COAL 1.06 / CHP 0.65 / ST_GAS 0.15 |
| Jan 15-17 2024 (h06-21, month-capability) | 13.69 | 4.62 | **9.07** | CT 6.18 / CC 1.22 / COAL 1.02 / ST_GAS 0.44 |

**The identification finding (the decisive one):** the same measure on hot
NON-event control days reads **higher**, not lower — Jul 14-15 2025: 7.91 GW
"invisible"; Jul 21-22: 10.23; mild Jan 8-10 2024: 19.61. On a slack day
most "missing capability" is economics (peakers not needed). **The raw gap
has NO identification; only inside a declared window — where the emergency
instrument plus deep in-merit prices guarantee an available unit runs — is
absence evidence of unavailability.** This is measured confirmation of the
diagnosis §4 conclusion and the reason the channel is a *registry-scoped*
overlay, never a general detector.

Control-screened event-specific unavailability (invisible at the event AND
running normally on both control days — the conservative floor for what the
channel removes):

- **Jul 28-29 2025: 3.89 GW** (North 2.54 / South 1.36; Indiana 0.50;
  COAL 1.37 / CC 1.07 / CT 0.65 / ST_GAS 0.21 / CHP 0.58). Largest units:
  Sherco-1 −287 MW, RS Cogen −201 (hard zero), F B Culley-3 −172,
  Labadie-2 −159, Gibson City CT −102 (hard zero).
- **Jan 15-17 2024: 2.64 GW** (CT 0.83 / CC 0.73 / COAL 0.51 / ST_GAS 0.44;
  North 1.55 / South 1.09) on month-capability. **Capability-basis
  sensitivity is large in winter** (full-year basis reads 14.45 GW invisible,
  10.45 of it CT — summer-only capability contaminates it): the deriver's
  capability window is identification-critical and is frozen in M-2 below.

Against the diagnosis's stack arithmetic ("removing ~5-6 GW of phantom North
capacity at the event hours moves the margin into the $114-949 stack tail"),
the honest current-stack channel size is **~3.9-5.4 GW at the July peak**
(screened → raw) — composed WITH miso-67's separation channel (which raises
the North margin the removal acts on), plausibly tail-engaging; the probe
decides. The old 8.4 GW figure should not be quoted forward: miso-65's regen
already absorbed part of it.

### 2b. Scarcity machinery — already in-LP, armed; re-read, don't build

Rule-19 enumeration of everything already pricing MISO (from the keeper's
own `run_config.json`, read this session):

| mechanism | state in miso-66 | phenomenon |
|---|---|---|
| `energy_reserve_coopt` + `miso_measured_reserve_requirements` | ON | market-wide RBDC ramping to VOLL $3,500 (`MISO_RESERVE_DEMAND_CURVE_MAX`) on measured hourly cleared reserves |
| `miso_zonal_reserves` (South family) | ON | zonal stepped ORDC $200/$1,100/$3,300 (BPM-002 §5.2.1.2 / Schedule 28-A, `MISO_ZONAL_ORDC_STEPS`) |
| `miso_reserve_pergen` | ON | reserve competes with energy per-generator (headroom-true withholding) |
| `miso_rdt_tcdc` | ON | RDT contract caps 3,000 N→S / 2,500 S→N, 92% derate, $40/$500 TCDC tiers |
| `miso_rpe_pricing` | ON | $200 RPE step |
| seam family (`miso_seam_export_limit/flow_limit/measured_ladder/south_seam_split`, `miso_firm_imports`) | ON | interchange physics |
| `miso_zonal_gas_basis` (+0.343 South committed) · F923 per-plant fuel · `gas_daily_shape` · `class_aware_fuel_price_fallback` · `nearby_fuel_price_fallback` | ON | measured delivered-fuel offer basis |
| coal conduct/pricing stack (`coal_committed_takeorpay_regulated`, `coal_mustrun_per_plant`, `coal_plant_monthly_pricing`, `coal_warm_committed`, tranche passthroughs) | ON | coal offer structure (CLOSED lane) |
| ST_GAS stack (`st_gas_mustrun_per_plant`, HR mults, startup, `gas_st_wefor_base_override`) | ON | VLR floor (miso-67's lane) |
| outage overlays (`outage_source=historic` std extract + `unit_outage_short_windows`) | ON | availability truth |
| post-solve scarcity overlays (`scarcity_price_overlay`, `scarcity_pricing_enabled`, ERCOT ORDC family) | **OFF (correct)** | MISO scarcity is in-LP only — no overlay may be added (one mechanism per phenomenon) |

The RDC prints 0h > $200 because the stack carries phantom headroom at the
event windows — a headroom-truth problem, not a missing-curve problem. **No
new scarcity mechanism is designed in this lane.** Sequence: miso-67 + M-2
(below) make the headroom honest; then C3c is RE-READ on that stack. Only if
it stays dark does a new scarcity question open — as its own charter, a
MISO-parameter update from MISO primary documents, never an ERCOT/NYISO
analogue import (rule 25).

### 2c. Schedule 28 anchors — VERIFIED against primary documents (this session)

- MISO's shortage-pricing reform (FERC docket **ER25-579**, approved April
  2025) raises VOLL $3,500 → **$10,000/MWh** and replaces the stepped ORDC
  with an LOLP-based curve (scaled by a $35,000 Operating Reserve Target
  Cost, $6,000/MWh ORDC upper limit adder), adds a fixed $3,500 EDR offer
  cap, a circuit-breaker (VOLL degrades toward $5,000 in long events), and
  raises DA price-sensitive/virtual bid caps to VOLL. MISO's own August-2025
  MSC deck (MSC-2019-1, fetched and text-extracted this session): "MISO is
  targeting an effective date of **9/30/2025**."
- Scored impact check (recomputed): **37 of the 38** 2025 DA Indiana tail
  hours precede 2025-09-30 (only Oct 6, $203.96, falls after); all 2023/2024
  tail hours are under the $3,500 regime. **The committed constants
  (`MISO_RESERVE_DEMAND_CURVE_MAX = 3500`, `MISO_ZONAL_ORDC_STEPS`
  $200/$1,100/$3,300) are the correct in-force tariff for effectively the
  entire scored window. No backcast constant change.** Memory of "the 2025
  filings changed VOLL" is true but does not touch the scored tail.
- The post-9/30 regime ($10,000 VOLL + LOLP ORDC) is REAL and belongs to the
  **forecast path** (2026+ runs currently inherit the $3,500 anchor — a
  measured tariff update with citation, its own small charter). It is
  deliberately NOT bundled into this lane's probes: a half-implementation
  (VOLL step without the LOLP curve) would be a wrong mechanism, and the
  scored-window payoff is ≤1 hour. Pre-declared: if Phase B's C3c re-read
  finds the Oct-6 hour verdict-material (it cannot be — 1 of 38), that still
  does not authorize an in-lane change; note it for the forecast charter.
  Add the ER25-579 citation + effective date to `docs/parameter-citations.md`
  and as a comment on the constants in Phase B (doc-only edit, no behavior).

## 3. The frozen design

### M-0 (prerequisite): execute miso-67 from the triage doc — by reference

`docs/handoffs/miso-run66-triage-design-2026-07.md` §Issue-2 is already the
frozen contract (mechanism `st_gas_mustrun_p25_level`, expected ST_GAS-2024
→ ≈ −3.5..−5.5 PASS, C1 → 16/16, fallback V2b pre-declared there). Execute
it verbatim FIRST, including its reads: ST_GAS/OTHER_FOSSIL C1, C2-2025 gas,
C3a/C3b mechanism-only, RDT anchors, D-1/D-2/D-4. **This lane consumes two
additional reads from that same probe bundle:** July-2025 model zonal spread
(vs $0.55 today) and S→N binding hours (vs 236 today / 919 measured) — the
quantified answer to "how much separation does honest South steam buy."

### M-1: `miso-maxgen-events` declared event-window registry (data intake)

New datatype via the `data-intake` skill (raw → schema → clean), rule-13
class: **declared physical/market availability events** — the same
admissibility family as CAMPD outage windows (backcast/calibration overlay
by construction, forecast years carry none).

- **Content:** one row per (declaration, region): `iso`, `region`
  (Midwest / South / footprint — as declared), `level` (capacity_advisory /
  maxgen_alert / maxgen_warning / maxgen_event_step<N> — as declared, pre-2026
  ladder), `start_utc`, `end_utc`, `source_url`, `source_doc`, `notes`.
  Coverage: 2023-01-01 .. 2025-12-31, all levels ≥ capacity advisory.
- **Sources (primary, durable — pre-declared ladder):**
  1. MISO OASIS `Capacity_Emergency_Historical_Information.pdf` ("Maximum
     Generation Emergency Declarations", hosted at
     `oasis.oati.com/woa/docs/MISO/MISOdocs/`) — the standing historical
     declaration record. Server was intermittently 503/TLS-blocked from this
     box on 2026-07-15; retry in Phase B, and verify the posted vintage
     covers through 2025 (the search-indexed vintage said "through June
     2024" — a newer vintage likely exists at the same URL).
  2. MISO monthly Operations Reports / Informational Forum decks
     (cdn.misoenergy.org) — advisories/warnings/events with dates + regions.
  3. Potomac SOM annual reports (2023/2024/2025) — emergency-event
     tabulations as cross-check (2025 SOM published ~June 2026).
  MISO's live notification feed deletes after 30 days — NOT a source. **If
  no primary document covers an event window, that window is NOT in the
  registry** — reconstructing windows from price spikes is residual-fitting
  and forbidden (pre-declared, absolute).
- Freeze test on the data-intake pattern (schema validation + byte identity);
  provenance per row.

### M-2: `unit_outage_maxgen_events` (ScenarioConfig bool, tier 3, default OFF)

CAMPD **revealed unit derates inside declared windows only**, on the
`unit_outage_short_windows` deriver pattern
(`derive_campd_unit_outages.py --maxgen-events` or a sibling deriver), emitting
`campd-unit-outages-maxgen-MISO.csv`; applied in
`fleet.generators_to_fleet_arrays` next to the std/short overlays. Frozen
identification guards (all measured; no model, price-residual, or tuning
input):

1. **Window scope:** derates exist only within registry windows (M-1),
   clipped to the declared start/end. Class-agnostic (this is the only
   channel that can carry the CT/CC leg — the std extract's 5-day floor and
   the short channel's coal-only CF≥0.55 guard exclude it by design).
2. **In-merit certificate (measured):** a window qualifies for a region only
   where the measured DA hub LMP (the committed hub record) for that
   region's hubs exceeds **$150/MWh** — far above any in-fleet thermal SRMC
   — for ≥2 window hours. Inside such a window, an available unit runs;
   absence/reduction is revealed unavailability. ($150 is a conservative
   in-merit certificate, not a tuned scalar: its only role is to certify
   "deep in-merit"; any value in [$120, $200] selects the same windows in
   2023-2025 — state this insensitivity check in the deriver docstring and
   verify it at derivation.)
3. **Capability basis (frozen):** unit capability = max CAMPD gross load in
   a **±45-day window** centered on the event (seasonal-honest; recomputed
   sensitivity this session: month-basis 9.07 vs year-basis 14.45 GW
   invisible for Jan-2024 — the ±45d basis pins winter CT capability to
   winter-adjacent evidence). Derate = capability − unit's best event-window
   hour, floored at 0 (crediting the best hour makes reserve holdback
   invisible to the measure — a unit that touched capability is not derated).
4. **Disjointness:** unit-hours already covered by the std or short extracts
   are excluded (the miso-65/short-windows precedent; assert 0 same-unit
   overlaps at derivation).
5. **No control-day screen in the deriver.** The §2a control screen is
   Phase-A identification evidence, not a derivation input — inside a
   declared, in-merit-certified window the absence IS the measurement, and a
   control screen would wrongly discard true peaker freeze-offs (a peaker
   idle on a mild control day is economics, not health). The deriver's
   guards are 1-4 only, so the channel carries the RAW invisible sizes
   (~5.4 GW Jul-2025, ~9.1 GW Jan-2024 at month-basis), with the screened
   figures (3.89 / 2.64) as the pre-registered lower bound on what matters.
6. Gated boolean, default **off** everywhere; MISO backcast arms it. Every
   existing keeper replays byte-identical with it off.

**Rule-12 triple:** *driver* = MISO's own declared emergency-procedure
instruments (max-gen events/warnings/alerts/capacity advisories — public,
per-event provenance) + each unit's own CAMPD trace inside them; *window* =
exactly the declared windows (D-4: binding outside a registry window is a
bug by definition — declare the window set in `D4_WINDOWS` when regenerating
`legitimacy_diagnostics.json`); *forward story* = availability-event overlay,
backcast/calibration only (identical to the CAMPD std/short outage windows'
rule-13 status; the registry + derates regenerate from each new
CAMPD/declaration vintage; a forecast year carries the class outage-rate
machinery instead — no forward window is fabricated).

**Admissibility (rules 13/15/17/18/19/22/23/25/26):** measured physical
inputs a forward year produces through its own outage machinery — the
established overlay family; no outcome pinning (dispatch inside windows
stays free above the derate; prices are never touched directly). Rule 15:
this is accurate measured data REPLACING an implicit "fully available"
estimate. Rule 19: it extends the availability phenomenon's existing
mechanism family (std + short + maxgen extracts, disjoint by construction) —
not a floor, not a price adder. Rule 23: new deriver limb, frozen guards
1-5, re-derives only on new source data. Rule 25: MISO-only extract; the
boolean is ISO-generic with no cross-ISO values. Rule 26: nothing deleted.
**DOF ledger:** +2 measured-physical entries (declared event registry;
event-window revealed derates; zero fitted scalars) → expected **22
measured / 2 residual** on the miso-67 stack (20/2), 21/2 if miso-67 fails.

### M-3: none — the deliberate non-mechanisms

Pre-declared as NOT designed, so Phase B does not invent them: no post-solve
MISO scarcity overlay (in-LP RDC is the mechanism); no VOLL/ORDC constant
change for the scored window (§2c verified correct); no new congestion
mechanism (corridor exonerated, miso-61 anchors); no Jan/Sep/Dec residual
mechanism without its own driver; no G-23 import work in this lane.

## 4. Expected scored deltas (directions + pre-registered bands; probes decide)

- **miso-67 first (from its own design):** ST_GAS-2024 → ≈ −3.5..−5.5 PASS,
  C1 → 16/16, fail set sheds `fuelmix`; C3a-2025 UP from −13.7% via the
  separation channel (magnitude = this lane's first read); RDT anchors
  (2023/24 S→N mean-flow ~1.55 GW, separation-when-binding ~$2.5-2.9,
  re-read from probe `flows.parquet` — the slim keeper bundle cannot supply
  them) must hold; C3b-2025 mechanism-only within the 0.20 veto.
- **M-2 composed on the miso-67 stack:** Jun/Jul-2025 monthly Δ −16.6/−18.1
  → target better than ≈ −10/−12 (separation + ~4-5.4 GW event-window
  removal); Jan-2025 −9.2 → ≈ −6..−8; annual C3a-2025 −13.7% → **−6..−9%
  (PASS band ±10)**. C3c-2025 model DA >$200: 0h → **into [19, 76]**
  (0.5×-2× of 38); C3c-2024: 4h → **into [12, 48]** via the Jan-2024 window
  (all 24 actual tail hours). C3b-2025 **mechanism-only ≤ +0.005** on the
  composed read (veto ≤0.20 absolute). C2/C5a watch: event windows remove
  little energy (windows are days, not months) — coal/gas class totals move
  ≤ ~0.5 TWh; C5a-2024 (−2.6%) and 2025 (+1.8%) must stay in ±7. C8: no new
  floors — forced shares unchanged from the miso-67 read.
- If C3a-2025 lands PASS but C3c-2025 stays 0h: register the composed run as
  the candidate anyway (it is structurally superior — rule 1) and open the
  scarcity-depth charter separately. Do NOT hold registration hostage to the
  tail.

## 5. Pre-declared fallback triggers (committed BEFORE any deciding probe is read)

- **F1 (miso-67 fails its own gates):** follow the triage doc's V2b; if the
  ST_GAS lane still ends without a promotable stack, run M-2 composed on the
  **miso-66 keeper stack instead** — the derate channel is independent of
  miso-67 — but the July-separation read is deferred and C3a-2025 is
  expected to stay FAIL; the run is then a REJECTED PROBE registered per
  rule 15, and the lane pauses for the owner.
- **F2 (C3b-2025 mechanism-only breach, > +0.013 composed):** stop; the
  registry windows stay (they are measured), the composition is re-read one
  mechanism at a time (miso-67-only vs M-2-only) to locate the breach; no
  guard/window/threshold retuning against the shape residual. Escalate to
  owner with both single-mechanism reads.
- **F3 (capability-basis instability):** if ±45d vs event-month capability
  changes any event's derate GW by >2×, freeze to the SMALLER and record the
  sensitivity in the deriver docstring + design-doc addendum. (Jul-2025 is
  insensitive — my recompute; Jan-2024 is the known-sensitive case.)
- **F4 (registry coverage gap):** if no primary document yields a 2025
  vintage covering Jun/Jul-2025 (or the Jan-2024 winter declarations), those
  windows are absent and the expected deltas shrink accordingly — the lane
  reports the gap; it never reconstructs windows from prices or from the
  residual.
- **F5 (C3c still 0h after miso-67 + M-2):** the phantom-headroom hypothesis
  is refuted at current depth; open the scarcity-depth charter (MISO
  primary-parameter work) as a NEW lane; nothing further is armed in this
  one.

## 6. Sequencing memo (Phase B order)

0. **Verify-first block** (keeper re-score; miso-67 absence re-check; RAM +
   push probes below).
1. **Triage Issue-1 display fix** (no solve, independent) if still unshipped.
2. **miso-67** per the triage doc: implement → probe (3 years, one bundle,
   same-box base replica) → read → register (candidate or rejected probe) →
   this lane's separation reads off the same bundle.
3. **M-1 intake** (registry; data-intake skill; freeze test; no solve).
4. **M-2 deriver + gated boolean** (+ unit tests: off-state byte identity,
   window clipping, disjointness assert, capability-basis function).
5. **Composed probe**: miso-67-stack + `unit_outage_maxgen_events=True`,
   **2023+2024+2025 in one bundle** (rule 16) + a same-box unchanged-recipe
   base replica (the drift-control lesson: mechanism-only = probe − base,
   never probe − registered).
6. **Reads** in §4's order; fallbacks F1-F5 as triggered.
7. **Registration chain** (per run, keeper or rejected probe — rule 15):
   `dashboard_add_run` BEFORE `calibration_verdict --write-metrics` → DOF
   ledger (`build_dof_ledger.py`) → attestation (`gen_misoNN_attestation.py`
   pattern) → `legitimacy_diagnostics.py` regen (new D4_WINDOWS entry for
   the maxgen mechanism id) → sidecar `market_story` → payload parity
   (`check_registry_payload_parity.py`) → `build_manifest.py` →
   calibration-log entry → push. **No ablation twin (rule 20 as amended
   2026-07-14).** Keeper swap is owner-only.
8. **G-23 imports**: untouched, sequenced after this lane lands (it pulls
   C3a-2025 down).

## 7. What NOT to re-litigate (inherited + this session)

Inherited: `coal_committed_takeorpay_all`; `temp_dependent_derate` (MISO —
refuted on own-fleet envelope); the coal/CT conduct lane (CLOSED, miso-66);
P2 (archived); CAISO startup-aware screen (dropped-with-cause for MISO); gas
committed take-or-pay discount (commodity-vs-transport physics); offer-side-
only ST_GAS fixes ($118-128 outlier arithmetic); re-deriving `committed_pct`;
Issue-1-class scorer changes (verdict basis sound).
New this session: **no VOLL/ORDC constant change for pre-9/30/2025 hours**
(verified in-force tariff — §2c); **no post-solve MISO scarcity overlay**
(in-LP RDC is the one mechanism); **no general short-outage detector beyond
the declared windows** (control days measure MORE raw "missing" than event
days — the identification exists only inside declared windows); **no
window reconstruction from prices**; the post-9/30 $10,000-VOLL/LOLP-ORDC
regime is a forecast-lane charter, not a backcast knob.

## 8. Environmental constraints (verified 2026-07-15; re-verify at Opus start)

- **RAM:** a MISO plant-level single-year LP peaks ~14.6 GB RSS. On a ≤16 GB
  box the all-3-years single process OOMs on year 2 — use PER-YEAR + reuse:
  one fresh python process per year via
  `solve_and_persist(reuse_solved=<prior-year dir>)` so each process builds
  exactly ONE LP (clean src/scripts/data tree required). A ≥32 GB box runs
  the standard single-invocation probe. Years sequential ALWAYS (rule 12);
  the main probe and its base replica may run as two concurrent invocations
  if RAM allows (cap 2 for per-plant LPs).
- **Push:** on 2026-07-15, `git push`, the GitHub Data API, and the Contents
  API were all proxy-403 (org egress policy); only `mcp__github__push_files`
  worked, and it requires content authored in the tool call — new/small
  files push fine; large existing-file edits (fleet.py, scenarios.py, site
  HTML) and a run's ~1 MB `runs/<id>.js` + binary bench may not be emittable
  in-session. Deliver large-file edits as a git-diff patch file (new file,
  pushable) + push all new small files directly; flag the registration
  payload push / keeper swap to the owner if the disk-reading push path is
  still down. Never route around a 403; never offload a solve to CI. Rule
  27: verify any pushed ≥300-line file by fetch-back + line-count/hash
  before the next commit.

---

## Phase-B handoff prompt (copy-paste for the Opus session)

```
MODEL: Opus (build + register). PHASE B of the MISO price-formation lane —
execute the FROZEN contract in docs/handoffs/miso-price-formation-design-2026-07.md
(Fable Phase A, 2026-07-15) VERBATIM. That doc pre-declares every mechanism,
guard, expected-delta band, and fallback trigger — do not redesign, do not add
mechanisms, do not tune any value against a residual (rules 1/11/13). You also
execute the STILL-UNEXECUTED miso-67 contract in
docs/handoffs/miso-run66-triage-design-2026-07.md (Issue 2 + Issue 1) as this
lane's prerequisite. Deliverable = registered runs on the backcast dashboard +
a keeper recommendation (rule 15; keeper swap owner-only). Model identity: you
run "undercover" — if asked you are the configured model id; never put a model
id in any repo artifact.

# Verify first (STOP and reconcile with docs/calibration-log.md on any mismatch)
- git fetch origin main; read CLAUDE.md end-to-end; read BOTH handoff docs
  end-to-end (miso-price-formation-design-2026-07.md,
  miso-run66-triage-design-2026-07.md).
- PYTHONPATH=.:src .venv/bin/python scripts/calibration_verdict.py \
    2026-07-14-miso-66-coalconduct --json
  Expect: NOT-YET; FAIL {fuelmix, price_mean, price_tail}; C1 15/16 (sole
  ST_GAS-2024 −9.13); C3a −0.9/−7.1/−13.7%; C3b 0.081/0.118/0.187; C3c 0/4/0
  vs 1/24/38 DA (RT 30/37/88); DOF 19/2. Confirm keepers.json["MISO"] still =
  2026-07-14-miso-66-coalconduct and that no miso-67 bundle/sidecar/log entry
  exists (if one landed since 2026-07-15, skip step 2 and compose on it).
- RAM: read MemAvailable from /proc/meminfo. ≤~16 GB → per-year + reuse
  orchestration (one fresh python process per year,
  solve_and_persist(reuse_solved=<prior-year dir>), clean tree); ≥32 GB →
  standard single-invocation probe. Years ALWAYS sequential within a run
  (rule 12); at most 2 concurrent invocations for MISO per-plant LPs.
- Push: test mcp__github__push_files with a trivial new file on your branch.
  git push / Data API / Contents API were proxy-403 on 2026-07-15 — if still
  403, push new/small files via push_files with in-call content, deliver
  large existing-file edits as a git-diff patch file, and flag the ~1 MB
  runs/<id>.js payload + binary bench push to the owner. Never route around
  a 403; never spin up CI for a solve (billed private repo). Rule 27:
  after any push touching a ≥300-line source file, fetch it back and verify
  line count + hash before the next commit.

# Guardrails (absolute)
- Rule 22: MISO has NO calibration-complete marker — nothing touches 2022,
  2019, ≤2021, or H1-2026, EVER. All probes 2023+2024+2025, one bundle
  (rule 16); no single-year keeper.
- C3b-2025 ≤ 0.20 is the standing VETO (0.187 now, 0.013 headroom). Read it
  MECHANISM-ONLY: every probe pairs main + a same-box unchanged-recipe base
  replica; mechanism footprint = probe − base, never probe − registered.
- Rule 20 (amended 2026-07-14): NO zero-forcing ablation twin. Legitimacy =
  DOF ledger + legitimacy_diagnostics.json (D-1/D-2/D-4).
- All fallback triggers are PRE-DECLARED in the design doc §5 (F1-F5) and the
  triage doc (V2b). Engage them only on their stated triggers; never invent
  a new fallback after reading a probe.
- Do NOT re-litigate the design doc §7 list. No post-solve MISO scarcity
  overlay; no VOLL/ORDC constant change for pre-9/30/2025 hours; no window
  reconstruction from prices; no G-23 import work in this lane.

# Ordered execution
1. Triage Issue-1 display fix (docs/codebase-site/backcast-runs.html header
   wedge annotation + CHP row unfold; no solve; verify by recomputing the
   triage §Issue-1 table from the committed payload/bench). Ship first.
2. miso-67 per the triage doc §Issue-2 checklist: implement
   st_gas_mustrun_p25_level (tier-3 bool, default off; fleet.py level swap +
   cheapest-first tranche distribution; unit tests incl. off-state byte
   identity) → probe scripts/probes/_miso67_stgas_vlr_level.py on the
   _miso66_coalconduct.py pattern (miso-66 meta strict RENAME/SKIP replay +
   the new flag via prb_overrides), 3 years one bundle + same-box base →
   read {ST_GAS/OTHER_FOSSIL C1, C2-2025 gas, C3a/C3b mechanism-only, RDT
   anchors from flows.parquet (S→N mean-flow ~1.55 GW 2023/24,
   separation-when-binding ~$2.5-2.9 must hold), D-1/D-2/D-4 regen} →
   fallback V2b only on its pre-declared trigger → register (candidate or
   rejected probe) with recommendation.
   ALSO read for this lane: July-2025 model zonal spread (vs $0.55) and S→N
   binding hours (vs 236 model / 919 measured) — how much separation the
   honest South steam buys.
3. M-1 intake via the data-intake skill: miso-maxgen-events registry
   (schema → raw → clean; fields + source ladder in design doc §3/M-1;
   2023-2025 incl. WINTER declarations — all 24 of 2024's tail hours are
   Jan 14-17). Primary source first: OASIS
   Capacity_Emergency_Historical_Information.pdf (verify vintage covers
   2025; it was 503 on 2026-07-15 — retry); then MISO operations-report
   decks; SOM tables as cross-check. A window with no primary document does
   NOT enter the registry (F4).
4. M-2: deriver limb (--maxgen-events → campd-unit-outages-maxgen-MISO.csv)
   with the FROZEN guards (design §3/M-2: declared-window scope; $150 DA
   in-merit certificate + [$120,$200] insensitivity check; ±45-day
   capability basis; best-event-hour credit; disjointness assert vs std +
   short; NO control-day screen) + ScenarioConfig bool
   unit_outage_maxgen_events (tier 3, default off) applied beside the
   existing overlays in fleet.generators_to_fleet_arrays. Unit tests:
   off-state byte identity, window clipping, disjointness, capability
   window.
5. Composed probe: the step-2 surviving stack + unit_outage_maxgen_events,
   3 years one bundle + same-box base replica. Read in this order:
   C3b-2025 mechanism-only (veto) → Jun/Jul/Jan monthly deltas → C3a-2025 →
   C3c-2024/2025 (model DA-basis hours >$200 vs bands [12,48] / [19,76]) →
   C2/C5a watches → RDT anchors → regenerated D-1/D-2/D-4 (new D4_WINDOWS
   entry for the maxgen mechanism id = the registry windows). Fallbacks
   F1-F5 exactly as pre-declared.
6. C3c/RDC re-read on the honest stack (design §2b): if C3c-2025 is still
   0h, do NOT arm anything new — record F5, register the run (rule 15), and
   open the scarcity-depth charter as a NEW lane for the owner.
7. Registration chain for EVERY registered run (keeper candidate or
   rejected probe): scripts/dashboard_add_run.py BEFORE
   scripts/calibration_verdict.py --write-metrics → scripts/build_dof_ledger.py
   (expect 22/2 composed on miso-67, 21/2 on F1) → attestation
   (gen_misoNN_attestation.py pattern) → scripts/legitimacy_diagnostics.py
   regen → sidecar market_story → scripts/check_registry_payload_parity.py →
   scripts/build_manifest.py → docs/calibration-log.md entry (lead with the
   dashboard result) → push via mcp__github__push_files (small commits; the
   payload/bench push may need the owner per the push constraint). Honour
   top-15-per-ISO retention. NO ablation twin. Keeper swap: owner-only —
   end with a recommendation, not a keepers.json edit.
8. Doc-only follow-ups: ER25-579 citation + 9/30/2025 effective date into
   docs/parameter-citations.md and a comment at
   reserve_config.MISO_RESERVE_DEMAND_CURVE_MAX / MISO_ZONAL_ORDC_STEPS
   (constants verified correct for the scored window; post-9/30 regime =
   forecast charter). /sync-docs at end of session.

# Expected scored deltas (pre-registered bands — the probe decides; a miss
# triggers the matching fallback, never a retune)
- miso-67: ST_GAS-2024 −9.13 → −3.5..−5.5 PASS; C1 16/16; sheds fuelmix.
- Composed: C3a-2025 −13.7% → −6..−9% (PASS ±10); Jun/Jul-2025 −16.6/−18.1
  → better than ≈ −10/−12; Jan-2025 −9.2 → −6..−8; C3c-2025 0h → [19,76];
  C3c-2024 4h → [12,48]; C3b-2025 mechanism-only ≤ +0.005 (veto ≤0.20
  absolute); C5a within ±7; class energy moves ≤ ~0.5 TWh; RDT anchors hold.
```
