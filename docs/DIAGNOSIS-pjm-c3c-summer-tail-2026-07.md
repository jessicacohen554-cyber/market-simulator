# DIAGNOSIS — PJM C3c summer tail: the phantom scarcity-hour supply is measured unit-availability events the outage overlay structurally cannot see (2026-07-15)

**Charter:** `docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md` Part B (B.1–B.5) —
the SUMMER half of the pjm-111 keeper's single open miss, C3c `price_tail`
(2025: model 17 h vs DA-actual 51 h > $200). No-LP, design + measurement only;
no solve, no config flip (rule 1). The winter half is a separate lane
(`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` Part C); the reserve/ORDC
opportunity-cost SUPPLY lane is owner-closed and is not re-opened here.

**Verdict in one line:** the summer tail miss is a **measured availability
error, not an offer/conduct or fuel-price error** — in the 22 actual summer
DA-tail hours (the Jun 23–25 and Jul 28–29 heat events) the model dispatches
**+3.0 GW of coal the real fleet demonstrably could not produce**, because the
real fleet was in short (<5-day) full-unit outages and sustained partial
derates that the ≥5-day zero-run extract is blind to by construction; the
admissible lever is the existing measured unit-availability overlay family
completed at unit grain (arm `unit_outage_short_windows` for PJM with a
when-operable baseload guard + a unit-grain partial-plateau extract at the
partial deriver's frozen constants), with the gate pre-committed in §8.

Probe (committed, no-LP): `scripts/probes/_pjm_c3c_summer_tail_decomp.py`
(sections: tail / phantom / units / derivers / fuel / zonal / coalhod).
Model side decoded from the committed pjm-111 payload
(`frontend/data/backcast/runs/2026-07-15-pjm-111-cc-reconcile.js`); actuals
from the chronological `actual_lmp_hourly_PJM.parquet`, the 12-hub DA record,
bench CAMPD/923 series, raw CAMPD unit-hourly extracts, the committed
`campd-unit-outages-PJM.csv`, and the F923 delivered-cost parquet.

---

## 1. Tail anatomy — what the 51 hours are, and what the model misses

`actual_tail.json` PJM 2025: DA > $200 in **51 h** (RT 59). By month: **Jan 28,
Feb 1, Jun 13, Jul 9** — the tail is 29 h winter (out of scope here) + **22 h
summer**, and the summer half is exactly two heat events: **Jun 23–25** and
**Jul 28–29**.

Model (pjm-111, energy-only): 17 h any-zone / 7 h load-weighted, all Jun/Jul.
On the load-weighted reconstruction (actual RT + committed `lmpDeltaHr`):

* the model **catches the event peaks** (Jun 24 15–18h at $220–272, Jul 28 17h,
  Jul 29 16–17h at $239–240) — price formation works at the very top;
* it **misses the event shoulders**, hardest in the evening: Jun 24 19h actual
  $248 vs model $98; Jul 29 18h actual **$482 vs model $139**; Jul 29 19h $286
  vs $74.
* missed-hour gap-to-$200 (summer, 15 h load-weighted): **p25 $21 / p50 $52 /
  p75 $89**, max $126. The winter misses sit $121–133 away — a different lane.

Gate arithmetic (scorer `score_price_tail`, band [0.5×, 2×]): 2025 needs
**26–102 h** (currently 17); 2023 must stay ≤ 18 (currently 1, actual 8);
2024 ≤ 12 (currently 1, actual 2).

## 2. The phantom is in the scarcity hours themselves — and it is coal

Model − CAMPD, mean MW **in the 22 summer tail hours** (probe `phantom`):

| class | tail hours | Jun events | Jul events |
|---|---|---|---|
| COAL | **+3,034** | +2,401 | +3,948 |
| CC_REGULAR | +1,004 | +1,158 | +735 |
| CT | **−765** | −613 | −985 |
| ST_GAS | +314 | +365 | +240 |

In a $200+ hour every available coal MW runs, so model-minus-actual output in
those hours measures an **availability gap**, not conduct. The +3.0 GW coal
cushion (net of the CT −0.8 GW it crowds out of the price-setting margin) is
the "phantom mid-merit supply" of the charter, present in the exact hours the
tail lives. Per-plant (tail-hour mean): Conemaugh +450 (Jun-concentrated:
+744), Rockport +401 (Jul: +893), Pleasants +343, Clifty +290 (Jul: +688),
Amos +285 (Jun: +440), Kincaid +283, Mitchell-WV +262 (Jul: +604), Mt Storm
+192, Powerton +184, Brandon Shores +108.

## 3. Unit-level decomposition — what kind of availability events these are

Against each unit's **summer demonstrated capability** (CAMPD p99.5 of
Jun 1–Sep 15 gross), the coal shortfall in the 22 tail hours decomposes
(probe `units`):

| bucket | mean MW | what it is |
|---|---|---|
| full stop, **covered** by the ≥5-day extract | 2,137 | already applied by the overlay (model holds these at 0 — e.g. Rockport MB1's Jun 21–29 window caps the model at one unit through the June event ✓) |
| full stop, **uncovered** | **1,016** | short (1–4-day) event-coincident outages: Conemaugh-2 (Jun 23–24, ~907 MW), Clifty 1/2 (Jul 29–30), Pleasants-2 (Jul 29), Mt Storm-3 |
| **partial derate** (unit never zero → no zero-run window can exist) | **1,859** | Rockport MB2 at ~540/1,364 through Jul 28–30 (failing into its Aug 1 documented outage), Kincaid-1 at ~300/558 through BOTH events, Mitchell-1/2, Amos-1/2, Powerton ×4, Brandon Shores ×2, Fort Martin |

Uncovered short stops + partials ≈ **2.9 GW ≈ the measured +3.0 GW phantom** —
the decomposition closes. The extract itself is healthy (1,381 windows touching
2025, vintage through 2026-03) — the gap is **structural**: a ≥5-day zero-run
detector cannot represent 1–4-day stops or derates, and both concentrate
exactly in stressed periods (the MISO Jul-2025 precedent, verbatim:
`unit_outage_short_windows` was built for "~2.8 GW of coal capability offline
at the peak block invisibly to the standard overlay").

Honesty note, both directions: Amos-3's documented Jul 17–Aug 5 window has the
real unit briefly BACK on Jul 28 (~900 MW) — the binary window over-removes
there; the +3.0 GW phantom is already net of such over-carries.

## 4. Refuted alternatives (measured)

* **F923 price vintage (B.1's first question): refuted.** The 2025 delivered-
  coal vintage is complete (519 PJM-state rows, 11–12 months at the reporters)
  and moved only −5% vs 2024 (qw $2.77 → $2.64; Jun–Jul $2.79 → $2.61) while
  the model's gas moved **+61%** ($2.19 → $3.52). The 2025 coal-toward-merit
  shift is real commodity movement; no price-vintage artifact exists to fix.
* **Offer conduct as the TAIL driver: refuted by construction.** Sub-cost
  committed pricing (the #1302 sub-floor multipliers, COAL_BIT committed
  0.548×) shapes WHERE coal clears in mid-merit hours, but in a $200 hour every
  available MW runs whatever its bid — bids cannot create the 3 GW the fleet
  did not have. The pricing story remains the (non-gated) level/shape residual:
  July-2025 coal over-run is uniform around the clock (+2,969 MW overnight vs
  +2,821 MW day; 30% of over-run in h0–6 ≈ the 29% share of hours), with a
  flat-floor signature (July p10 CF: model 0.46 vs CAMPD 0.33) — owned by the
  DOF-ledger issue #1302, not by this lane.
* **Temperature derate: stays refuted** (third refutation, 2026-07-14
  diagnosis §1); nothing here re-opens it — the phantom is unit-event-shaped
  (June-only / July-only per unit), not ambient-shaped.

## 5. Lead 2 — the CC zonal misallocation trace (B.2): congestion surface, not fuel

* **Zonal congestion surface (the binding defect).** July mean DA premiums
  (hub − hub-mean) vs model zonal duals (zone − zone-mean), probe `zonal`:
  actual EASTERN HUB **+11.5 to +15.0**, WESTERN HUB +6.8/+7.7, DOMINION
  +0.9/+4.5, N ILLINOIS −1.7/−6.1 — the model's surface is nearly **flat**
  (−1.7 … +3.5). Cheap western/ComEd energy flows east essentially
  unconstrained, which is precisely why the model over-runs the AEP-Ohio/
  Central-PA/ComEd cyclers and holds the Dominion belt 5–13 CF-pts low.
* **Dominion-zone fuel cost: exonerated.** The Dominion belt reports its own
  F923 gas (Jun–Jul-2025 $3.07–3.23, ABOVE the cyclers' pool fills ~$2.9–3.0);
  the model prices it honestly. Reality base-loads the belt because the real
  east/Dominion congestion premium covers the higher fuel cost; the model has
  no such premium to pay it.
* **Seam pricing: secondary.** The measured seam ladder is on; the residual
  seam error is mean-level over-import (2025 model 25.0 vs actual 18.0 TWh) and
  hourly shape (r = −0.16; note the 2025 figure is contaminated by the known
  model-side 2025 phase defect filed 2026-07-15 — do not over-read it).
* **C3c relevance:** real summer scarcity is partly ZONAL (east premium spikes)
  while the model's flat surface needs system-wide shortage to clear $200 in
  any zone. The surface is therefore a disclosed contributor to the tail
  boundary — but fixing it is a topology/interface-limit charter of its own
  (the West/Panhandle-split class), NOT this lane's lever, and no admissible
  quick lever exists for it (an interface-limit haircut tuned to spreads would
  violate rules 1/13).

## 6. D-1p instrument (B.3) — built, run on pjm-111

`scripts/probes/_pjm_d1p_diurnal_cycling.py` (committed with the 2025
phase-audit) runs against any payload; on pjm-111 it flags the CC flat-
overnight offenders (2/5/1 plants ≥15-pt turndown gap in 2023/24/25; Newark,
Woodbridge, Fremont, West Deptford, Bergen — EMAAC/ATSI cyclers) with
`night_share` ~0.3–0.4 of |model−CAMPD| MWh accruing in h0–6. The coal
companion lives in this session's probe (`coalhod`). Proposed D-1p gate for
future commitment-posture work (NOT gated in this cycle — instrument only):
capacity-weighted mean turndown gap (turndown_c − turndown_m) over CC_REGULAR
≥500 MW complete-CEMS plants ≤ 0.10, and no single plant > 0.40. Both numbers
are reported by the probe so the gate can be armed scorer-side later without
re-solving.

## 7. The named mechanism — measured unit-availability completion (PJM)

**One phenomenon** (rule 19): measured unit-availability events absent from the
≥5-day zero-run extract. **Two window shapes, both from the same CEMS source,
both zero-fitted-scalar, all constants inherited frozen from the existing
derivers:**

* **Leg A — short full-unit stops (existing mechanism, arm it for PJM).**
  `ScenarioConfig.unit_outage_short_windows=True` +
  `campd-unit-outages-short-PJM.csv` derived by the frozen deriver
  (`scripts/derive_campd_unit_outages.py --short-windows --iso PJM`) with ONE
  identification-basis correction: `SHORT_BASELOAD_CF` (0.55, unchanged)
  evaluated on **when-operable** hours (excluding the unit's own ≥5-day
  standard windows) instead of raw annual hours. The raw-annual basis
  contradicts the guard's own stated intent ("units that normally run near
  their ceiling"): a unit with a documented 113-day outage is baseload when
  operable — measured when-operable CFs for the event units are 0.58–0.72
  (all pass) vs raw-annual 0.09–0.36 (9 of 11 spuriously fail). The in-merit
  revealed-availability filter (≥6 high-net-load hours, frozen) stays on and
  is what keeps economic stops out. Measured capture (upper bound, pre-filter):
  **~990 MW mean in the 51 actual 2025 tail hours**; annual footprints
  5.4/4.1/7.0 TWh (2023/24/25) BEFORE the in-merit filter prunes low-price
  economic stops. The raw-annual basis would capture only ~340 MW — the guard
  correction is what makes the mechanism reach the events.
* **Leg B — unit-grain partial-derate plateaus (new flag, frozen constants).**
  `ScenarioConfig.unit_partial_outage_windows` (tier-3, default off) + a
  per-ISO unit-grain partial extract emitted into the `campd-partial-outages`
  schema, using the partial deriver's frozen constants verbatim (≥5-day
  plateau, 7-day centered median, ceiling < 0.65× p90 reference, run-floor
  0.06) plus the same when-operable baseload guard. Measured capture at frozen
  constants: ~170 MW in the 2025 tail (Kincaid-class sustained derates; the
  3–4-day event derates are structurally invisible to the 7-day median — 
  disclosed, NOT chased with new constants). The existing **plant-level**
  partial detector is measured to over-fire **43 TWh/yr** on PJM's cycling
  fleet (economic part-load read as outage) and is REFUSED for PJM as-is; the
  ERCOT-only scope in `fleet.py` stays correct for the plant-grain file.

Rule-13 admissibility: unit outage/derate windows are physical availability
events (the explicitly admissible overlay class), detected from CEMS with
frozen identification rules + a market-revealed in-merit test, regenerate for
any vintage (rule 23: the PJM short/partial extracts are new-ISO intake of an
existing datatype), respond to changed conditions, and have the standard
forward analogue (WEFOR/derate rates). What is NOT done: no hourly
output-tracking cap (that would be pinning), no window hand-added for a
specific residual hour, no constant re-tuned (0.55 / 0.65 / 5d / 7d / 0.06 all
carried), no bid or price surface touched.

Expected-effect honesty: legs A+B recover ~**1.2 GW** of the 3.0 GW tail-hour
phantom; ~1.7 GW of event partial derates (Rockport-MB2-class, 3–4-day) stays
unidentifiable at frozen constants and is the quantified residual boundary if
the gate misses. The near-miss geometry is favourable — every 2025 model hour
within $90 of the threshold has ≥500 MW of A+B-recovered capacity in it (19/19;
within-$25: 5/5) and 2023 has zero near-misses within $90 (no small-count
risk) — but whether +1.2 GW moves the marginal rung $21–89 in ≥9 hours is an
LP question the pre-committed gate adjudicates, not this document.

## 8. Pre-committed gate (set BEFORE any solve — rule 1)

The pjm-112 solve (pjm-111 recipe verbatim + the two availability flags,
2023+2024+2025 in one bundle, rule 16) is adjudicated on, all together:

1. **C3c-2025**: model tail (payload `ordc.hoursGt200.model`, any-zone
   energy-only, same basis as pjm-111) **≥ 26 h and ≤ 102 h**.
2. **C3c-2023/2024 small-count caps hold**: 2023 ≤ 18 h, 2024 ≤ 12 h.
3. **No currently-PASS criterion flips in any year**: C1 16/16, C2, C3a, C3b,
   C4, C5a, C6, C7, C8 (rubric v2.5, `calibration_verdict.determine`).
4. **Provenance check (pre-solve, build-time)**: the derived PJM windows
   recover ≥ 800 MW mean across the 22 summer tail hours in the extract
   arithmetic itself (probe `derivers` reproduces this) — i.e. the mechanism
   demonstrably targets the measured phantom before the LP ever runs.
5. **LOYO within 2023–2025**: zero-fitted-scalar measured overlay (the
   miso-66 "by construction" precedent) — satisfied by per-year scoring of the
   one bundle; any year regressing on 1–3 is a fail.

Outcomes: all five hold → register + recommend keeper (owner promotes;
keepers.json owner-only). (1) misses but 2–5 hold → register as NOT-YET
candidate, update this diagnosis with the measured shortfall, and the summer
tail becomes a **quantified disclosed boundary** (the ~1.7 GW frozen-constant-
invisible partial-derate bucket + the flat congestion surface of §5) — no
constant may be revisited in that same session (rules 1/11/23/26). Anything
else regresses → reject, keeper stays pjm-111.

## 8.1 Measured result (pjm-112, 2026-07-15) — outcome (1) misses, 2–5 hold

Run `2026-07-15-pjm-112-unit-availability` (pjm-111 recipe + the two availability
flags, 2023+2024+2025 in one bundle). Both overlays fired (2023: short 206
plant-tranches, partial 134). Gate adjudication, all five together:

| gate | test | result |
|---|---|---|
| **1** | C3c-2025 model tail ∈ [26, 102] h | **MISS — 18 h** (pjm-111 was 17; +1 h) |
| 2 | 2023 ≤ 18 / 2024 ≤ 12 | HOLD (1 / 1) |
| 3 | no PASS criterion flips (C1 16/16, C2, C3a, C3b, C4, C5a, C6, C7, C8) | HOLD — every criterion PASS, matching pjm-111 |
| 4 | provenance ≥ 800 MW over the 22 summer tail hours | HOLD — **1502 MW** (short 1314 + partial 188) |
| 5 | LOYO within 2023–2025 (no year regressing on 1–3) | HOLD |

**This is outcome (1): gate #1 misses, gates 2–5 hold → NOT-YET candidate; the
summer tail is now a QUANTIFIED DISCLOSED BOUNDARY. Keeper stays pjm-111.**

The mechanism is measured and demonstrably on-target — the two extracts remove
**1502 MW** of the +3.0 GW coal phantom in the exact 22 Jun 23-25 / Jul 28-29
tail hours (gate #4, above the §7 estimate because the when-operable guard
correction reaches more short-window units than the raw-annual basis: the
short leg alone captures Conemaugh-2 Jun 22-25 and Clifty 1/2 Jul 28-31, the
partial leg Mitchell-WV-1 Jul 23-30). Yet removing that coal moves the marginal
price rung past $200 in only **1 additional hour** (17 → 18). The boundary is
therefore **two-part and larger than availability alone**:

1. **The frozen-constant-invisible partial-derate bucket (§7).** ~1.7 GW of the
   phantom is 3–4-day event derates (Rockport-MB2-class, Jul 28-30) that the
   7-day-median plateau detector cannot see; the derived partial extract carries
   Rockport MB2 only in 2024, not the 2025 event — as §7 disclosed. Chasing it
   would require moving `_SMOOTH_DAYS`/`_MIN_DAYS` (rule 23 forbids it here).
2. **The flat zonal congestion surface (§5) — the binding residual.** Even the
   1.5 GW we *did* remove barely moves the tail: cheap western/ComEd energy
   flows east essentially unconstrained and imports backfill, so the system
   still needs system-wide shortage to clear $200 in any zone. This is the
   dominant contributor and is a **topology/interface-limit charter of its own**
   (the West/Panhandle-split class), not this lane — no admissible quick lever
   exists for it (rules 1/13).

Per rules 1/11/23/26, no constant, window or threshold was revisited after the
result. The measured overlay stays in as the structurally-faithful availability
model (it is real, on-target, and zero-DOF); it simply does not, on its own,
close the C3c summer tail — which is now disclosed as congestion-surface-bound.

## 8.2 Nuclear (non-CAMPD) availability probe (pjm-nuc-1, 2026-07-16) — NULL result

Follow-on session pjm-nuc-1 tested the one candidate the §2/§3 decomposition is
blind to **by construction**: the phantom tables are model-minus-CAMPD, and PJM
nuclear (32 units, 33.5 GW; 32,689 MW active after the dormant Crane exclusion)
is not in CAMPD at all. The model runs nuclear on the fleet-month CF smear
(`NUCLEAR_MONTHLY_CF_BY_YEAR`, EIA-923-derived, flat must-run at
pmax × CF within each month), which cannot see a unit-specific refuel/trip
inside a scarcity hour — the exact defect ERCOT fixed with its per-reactor
daily overlay (`ercot_nuclear_unit_availability`). Diagnostic-first: probe
committed, stop threshold (~400 MW ≈ one small reactor, over the 22 tail
hours) pre-declared before measurement, no flag and no solve without a
material phantom.

Probe: `scripts/probes/_pjm_nuclear_phantom_decomp.py`. Model side is an
**exact** reconstruction (nuclear is flat must-run, so dispatch ==
pmax × monthly CF; validated per year against the committed pjm-113 payload's
own fuelRows annual nuclear to < 0.05 TWh — nuclear plants are absent from the
payload's per-plant dict, which is CAMPD fossil only). Actual side is EIA-930
PJM nuclear hourly via the canonical `load_eia_hourly_benchmark` clock (the
series the run's nuclear fuelRow is scored against; nuclear is a price-taker,
so realized ≈ available, and CEMS cannot see nuclear).

**Measured phantom (model − EIA-930 nuclear), the scarcity hours themselves:**

| window | hours | phantom mean MW |
|---|---|---|
| 2025 summer tail (the 22 Jun 23-25 / Jul 28-29 hours) | 22 | **+147** (clock cross-check on `PJM_fueltype.parquet` UTC→EPT: +119) |
| — Jun 23-25 event only | 13 | +241 |
| — Jul 28-29 event only | 9 | +12 |
| 2023 summer tail | 8 | +328 |
| 2024 summer tail | 1 | +320 |

Range over the 2025 tail hours: −36 … +407 MW; no single hour reaches 410 MW.
The real fleet was effectively fully up through both heat events (actual
32.0–32.1 GW vs model 32.0–32.4 GW). Whole-month phantom means are slightly
NEGATIVE (Jun −202, Jul −81 MW): the CF cap-at-1.0 convention makes the smear
under-credit the fleet on the month, not over-credit it. EIA-923 plant-month
attribution finds no event-coincident refuel — the only 2025 sub-0.90 event-
month plant is Susquehanna (Jun/Jul CF 0.87, a sustained partial state whose
monthly energy the smear already embeds).

**Verdict: NULL — the stop condition binds (147 < 400 MW).** A perfect
per-reactor overlay could at most recover the phantom itself, ~0.15 GW mean —
an order of magnitude below the +3.0 GW coal phantom (§2) and a tenth of the
1.5 GW whose removal moved the tail only +1 h in pjm-112/113. No overlay was
built, no flag added, no solve run, nothing registered (rules 1/11/13: the
measurement does not justify the mechanism). The `avg_ecomax`-for-nuclear open
question and the NRC daily-status intake are both moot for PJM and were not
pursued; the non-CEMS GAS availability extension remains a separate,
unchartered follow-on. The C3c summer boundary therefore stands **as §8.1
disclosed, now with the third candidate measured and excluded**: the flat
zonal congestion surface (§5, dominant) plus the ~1.7 GW frozen-constant-
invisible partial-derate bucket (§7).

### 8.2.1 Owner order (2026-07-16, pjm-nuc-1b): build the measured overlay anyway — gate pre-committed BEFORE any solve

The owner reviewed the §8.2 null and directed that the ~147 MW smear error be
fixed with the real mechanism regardless ("147 MW is still more than it needs
to be"). This proceeds under rule 1's structural-fidelity reading — a
per-reactor measured availability is strictly more faithful than the
fleet-month smear, and the ERCOT precedent is a live keeper input — NOT as a
fit-chase: the expected C3c movement is ≈ nil and is not the success
criterion. The mechanism carries **zero fitted scalars**; nothing may be
tuned to the residual.

**Source adjudication (charter order (a)→(b)→(c), measured head-on):**
DataMiner2 `energy_market_offers` returns identity-MASKED `unit_code`s
(base64-opaque, e.g. `AAAABg8LDwUG…`), so per-reactor attribution from
`avg_ecomax` is impossible whatever its null-ness — (a) is unusable for a
unit overlay and the charter's open question is answered "cannot be
established per-unit; feed is anonymized". (b) EIA-923 is monthly and cannot
see intra-month timing. **(c) NRC daily Power Reactor Status is selected**:
`ReportDt|Unit|Power` per reactor-day, all 31 active PJM reactors present
365/366 days for 2023–2025, a direct physical measurement with no
withholding confound. Raw NRC availability energy sits 0.7–1.6 %/yr below
the committed EIA-923 anchor (winter-uprate / thermal-vs-net basis wedge),
so the deriver mirrors the ERCOT reconciliation verbatim: **the 923 anchor
owns the LEVEL, NRC owns the TIMING** — event days (raw < `EVENT_RAW_MAX`
0.90, frozen) kept exactly as measured, pool days scaled by one per-month
fixed-point factor (per-day cap 1.0, scale clip 1.25, frozen) to reproduce
`NUCLEAR_MONTHLY_CF_BY_YEAR["PJM"]` monthly energy exactly.

**Pre-committed gate (set NOW, before the CSV is derived or any LP runs):**

1. **Build-time provenance:** the derived windows must recover
   **≥ 75 MW mean** over the 22 summer-2025 tail hours in extract arithmetic
   (Phase-1 measured phantom 147 MW minus a stated 72 MW margin for the
   level reconciliation) — probe section `windows`. Below that, the
   mechanism demonstrably does not reach the events: stop before solving,
   disclose here.
2. **Solve gate (identical to §8 gates 1–3/5):** C3c-2025 model tail
   ∈ [26, 102] h; 2023 ≤ 18 h, 2024 ≤ 12 h; NO currently-PASS criterion
   flips in any year (C1 16/16, C2, C3a, C3b, C4, C5a, C6, C7, C8); LOYO
   within 2023–2025 (zero-fitted-scalar measured overlay, per-year scoring
   of the one bundle).
3. **Outcomes:** all hold → register + recommend keeper. C3c misses but the
   rest hold → register NOT-YET candidate (same lineage as pjm-112/113);
   the realistic expectation given ≤ 0.15 GW recovered. Anything else
   regresses → reject, keeper stays pjm-113. No constant revisited after
   results (rules 1/11/23/26).

**Measured result (2026-07-16): gate #1 FAILS at the build step — no solve.**
The overlay was fully built (fetch `scripts/fetch_nrc_reactor_status.py` +
committed raw NRC annual files, deriver `scripts/derive_nuclear_availability.py`
→ `data/raw/nuclear-availability-PJM.csv`, 15,190 reactor-days / 31 reactors;
loader `outages.nuclear_unit_availability_series`; PJM-scoped fleet wiring
behind `ScenarioConfig.nuclear_unit_availability`, default off, byte-identical
when off; tests) and its extract arithmetic measured by the probe `windows`
section: net recovery over the 22 summer-2025 tail hours is **−72 MW**
(min −327 / max +400; 2023: −1 MW, 2024: −105 MW) — the overlay *adds* nuclear
in the tail hours. The mechanism is self-defeating for this target **by
construction**: conserving the 923 monthly anchor forces the pool scale to
redistribute event-day energy onto near-full days, and scarcity hours ARE
near-full days (the June-2025 anchor at 0.99 lifts Susquehanna's real
0.91–0.98 Jun-24/25 derates to 1.0). Equivalently: at daily grain with an
honest level anchor, the +147 MW tail-hour phantom has ≈ zero unit-availability
content — it is sub-daily net-vs-thermal basis wiggle (heat-day condenser
backpressure reduces NET capability below nameplate while NRC thermal power
reads 100 %) plus hourly output noise, below any daily overlay's grain.
Chasing it further would require either dropping the level anchor (posts a
winter-biased-low level, refused above) or pinning nuclear to its hourly
EIA-930 output — rule-13-forbidden. **Stopped per the pre-commitment: no
solve, no registration, keeper stays pjm-113.** The infrastructure stays
committed default-off (the repo's standard posture for probe-refuted flags;
usable by a future ISO charter with its own gate). The honest answer to the
owner's "fix the 147 MW": at the admissible frontier it is not fixable by
availability timing; the only physical mechanism below this grain is an
ambient nuclear net-capability derate (a new charter, ~0.1 GW stakes, and the
§4 temperature-derate refutation would need distinguishing for nuclear).

## 9. Guardrail review

* **Rules 1/11**: mechanism identified and gate pre-committed before any
  solve; no lever tuned to the 17→26 residual; refuted alternatives (§4)
  stay out however the gate lands.
* **Rule 13**: measured physical availability events; forecast-native
  analogue; no output pinning; the same admissibility clause that covers the
  existing outage overlay.
* **Rule 22**: 2023–2025 data only throughout (no 2022/2019/H1-2026 touch).
* **Rule 23**: deriver constants frozen; the PJM short/partial extracts are
  new-ISO intake; the when-operable guard basis is an identification
  correction argued in the guard's own terms and applies uniformly (any ISO's
  future re-derive), cited to this measurement, not to the price residual.
* **Rule 24**: every table above is PJM-only; no cross-ISO curve moved.
* **Rules 19/25/26**: one mechanism family for one phenomenon; the refused
  plant-level partial path is left ERCOT-scoped (not deleted — it is ERCOT's
  live keeper input), and no new tunable scalar is introduced.

## 10. pjm-cong-1 — the congestion-surface charter: the east cut measured, the lane is MATERIAL, gate pre-committed (2026-07-16)

**Charter:** the §5/§8.1 "flat zonal congestion surface" boundary — this
session measures whether MEASURED interface limits on a real boundary can
close it (the ERCOT West/Panhandle-split precedent class). Probe (committed,
no-LP, stop condition pre-declared in its header BEFORE the adjudicating
section ran): `scripts/probes/_pjm_c3c_congestion_surface_decomp.py`
(sections roster / events / zonalphantom / interfaces / eastcut, model side
from the pjm-113 keeper payload).

### 10.1 The scarcity-hour tranches are ZONAL — the east carries 3× the system tail

Hub-level DA > $200 tranches (roster): **2025 EASTERN HUB 152 h** vs system
51 h (DOMINION 109, WESTERN 79, NEW JERSEY 76, N ILLINOIS 39); **2024
EASTERN 46 h vs system 2 h** — the 2024 tail was almost entirely an
east-only zonal event; **2023 EASTERN 28 h vs system 8 h**. In the 22
summer-2025 tail hours the EASTERN HUB premium over the hub mean runs
**+55 to +178 $/MWh** (June event mean +135, July +71; 2023 events up to
+140; the single 2024 system hour +102) while the model's EMAAC monthly
dual premium is **+3.3** — the flat surface is ~40× short in the scarcity
hours themselves, and C3c's any-zone count has ~3× the system's hours
available to a model that can price the east.

### 10.2 The dispatch phantom is an east-west wheel, stable across years

Zone × class model−CAMPD in each year's tail hours (zonalphantom): the model
UNDER-generates inside the MAD zones (2025: Dominion −1,122 MW — CT −1,243;
SWMAAC −957; the peakers reality ran: Linden −835, Doswell −783, Chalk Point
−369) and over-generates west of them (ComEd +547…+2,143, AEP/West_APS
positive every year) — a net **~+3.0 to +3.6 GW excess west→east wheel in
scarcity hours in ALL THREE YEARS** (2023 +3,619, 2024 +2,950, 2025 +3,372
MW, fossil basis). This is the §5 signature at event grain: the model
imports the east's scarcity away.

### 10.3 Interface identity corrected from the primary source (PJM Manual 03 §3.8, Rev 71 eff. 2026-05-20)

The DataMiner2 `transfer_limits_and_flows` series are PJM's named REACTIVE
TRANSFER INTERFACES (defined line sets, 5-min TLC limits posted hourly), NOT
"regional envelope means" as the constants.py crosswalk comment reads:

* **Eastern** = 7 EHV circuits into the eastern Mid-Atlantic (Breinigsville–
  Alburtis ×2, Juniata–Alburtis, Lauschtown–Hosensack, Peach Bottom–Limerick,
  Rock Springs–Keeney, Lackawanna–Hopatcong) — i.e. the **EMAAC import cut**,
  spanning BOTH of our Central_PA→EMAAC and SWMAAC→EMAAC paths. The committed
  map applies it to Central_PA→EMAAC alone, leaving the 5,000 MW
  SWMAAC→EMAAC static as an un-monitored parallel path the real interface
  does not have.
* **5004/5005** = Keystone–Juniata + Conemaugh–Juniata 500 kV — a
  western-PA→central-PA corridor interface. The committed map applies its
  measured series (mean ~2.8–3.1 GW) to **ComEd→AEP_Ohio (Illinois!)** —
  a mis-attribution inherited from the original iso_configs naming; the real
  ComEd interface (CE-East) is not in the feed at all. The mis-mapped series
  has been silently halving ComEd's 6,000 MW eastward capability.
* BC/PEPCO (the SWMAAC import cut) and CE-East exist in Manual 03 but are
  not published in this feed; Western/Central are PA-corridor cuts whose
  "envelope" seeding of the AEP→West_APS / ATSI→Central_PA statics stays
  as documented (out of this lane's scope).

### 10.4 The measured adjudication — MATERIAL (pre-declared stop condition passed)

In the 22 tail hours **no published interface binds in reality** (Average
Eastern utilization 81 %, transfers 8,216 vs limit 10,134 MW mean; AP-South
78–79 %; the TLC limits RISE during the events) — the real east premium
forms below the interface aggregation, as it does for Dominion (phase-drift
diagnosis §3). But the MODEL's east flow is the phantom: reconstructing the
model's internal EMAAC-cut import requirement from committed artifacts
(metered zonal load on the model's own 20→8 grouping × EIA-930 demand scale,
minus payload fossil dispatch, the exact nuclear smear, 930-scaled
renewables/oil, and PS at FULL discharge — every non-exact term biased
against materiality; actual-side cross-validation vs the feed's measured
transfers closes to +1,020 MW, inside the stated <1.5 GW unmonitored-path
wedge):

* **the requirement exceeds the measured Eastern limit in 13/22 tail hours,
  median exceedance +485 MW** (central estimate, zero seam import — the 2025
  NYISO import rungs price at $502.65, above every model tail price); with
  the measured 1,650 MW NYISO firm-export floor the count is 22/22;
* the binding hours ARE the missed shoulder hours (Jun 24 19h +656, Jul 29
  18h +910, Jul 29 19h +1,003 MW — the §1 evening misses), while the
  already-CAUGHT peak hours sit at negative margins;
* the MAD super-cut (Eastern + AP-South + AEP/DOM + statics) is loose by
  −11…−17 GW — the binding boundary is specifically EMAAC;
* pre-declared stop condition (probe header, fixed before computation:
  ≥ 8/22 h AND median ≥ 300 MW): **PASSED → the lane is MATERIAL.**
* LOYO context: the same construction binds 74 h (2023) / 32 h (2024) /
  46 h (2025, central) across the whole year — enough to separate the east
  in the right hours, bounded enough not to obviously blow the 2023 ≤ 18 h /
  2024 ≤ 12 h caps (the LP adjudicates; that is what the gate is for).

### 10.5 The mechanism (zero fitted scalars, all measured)

1. **`ScenarioConfig.pjm_east_interface_cut`** (tier 3, default off, PJM
   backcast overlay, byte-identical off): one ONE-SIDED aggregate
   interface-group row per hour capping `Flow(Central_PA→EMAAC) +
   Flow(SWMAAC→EMAAC)` at the hour's measured **Average Eastern** limit
   (the same `transfer-interface-limits` clean partition the per-link
   overlay reads; the dispatch interface-group machinery already supports
   hourly `(T,)` caps — the CAISO measured-corridor precedent). Reverse
   (westward) flow keeps the per-link TTCs; the per-link statics stay as
   their own bounds. Forward story: the interface regenerates from the same
   feed every year; forecast mode keeps the static seeds (two-track, the
   pjm-97 pattern).
2. **Crosswalk correction (unconditional data-integrity fix, rule 14):**
   delete the `("PJM_ComEd","PJM_AEP_Ohio") → 50045005` entry from
   `constants.PJM_INTERFACE_LINK_MAP` (primary-source refuted, §10.3); the
   link reverts to its static 6,000 MW. No measured series replaces it
   (CE-East is unpublished). The 5004/5005 series stays in the datatype
   (its Manual-03 boundary is internal to Central_PA at our grain — mapping
   it anywhere would double-apply the corridor the Eastern/Central/Western
   interfaces already carry, rule 19).

Rule-13 admissibility: a published operating-security transfer limit on a
real boundary, entering as a formulaic hourly bound that regenerates for
any year and responds to changed grid conditions — the explicitly admissible
class (measured TTC/GTC/interface limits), reconciled to the reduced network
per rule 14 with the misalignment documented (§10.3). NOT done: no scalar on
the series, no haircut, no link value tuned to spreads (§5 prohibition), no
constraint hand-placed for a residual hour.

### 10.6 Pre-committed gate (set NOW, before any solve — rules 1/11)

The pjm-cong-1 solve (pjm-113 keeper recipe verbatim via replay + ONLY
`pjm_east_interface_cut=True`, on the corrected crosswalk, 2023+2024+2025
one bundle) is adjudicated on, all together:

1. **Provenance (pre-solve, extract arithmetic):** the joint cut binds in
   ≥ 8 of the 22 tail hours (measured: 13/22 central — §10.4) and the
   implied east premium is positive, toward the measured +11.5–15 July
   mean; post-solve the July-2025 EMAAC monthly dual premium must land in
   **(+3.3, +30]** — moved from the flat surface, never past 2× the
   measured July hub premium.
2. **C3c-2025:** model any-zone tail ∈ **[26, 102] h**.
3. **C3c small-count caps hold:** 2023 ≤ 18 h, 2024 ≤ 12 h.
4. **No currently-PASS criterion flips in any year** (C1 16/16, C2, C3a,
   C3b, C4, C5a, C6, C7, C8 — rubric v2.5; watch C5a/C4: a real east limit
   re-prices the Dominion belt and the seam).
5. **LOYO within 2023–2025:** zero-fitted-scalar measured overlay — per-year
   scoring of the one bundle; any year regressing on 2–4 is a fail.

Outcomes: all hold → register + RECOMMEND keeper (owner promotes;
keepers.json owner-only). (2) misses but 1, 3–5 hold → register NOT-YET
candidate, update §5/§8.1/§10 with the measured shortfall. Anything else
regresses → reject, keeper stays pjm-113. No constant, window, series or
threshold is revisited after results (rules 1/11/23/26).

### 10.7 Measured result (pjm-114, 2026-07-16) — ALL FIVE GATES HOLD; keeper promotion RECOMMENDED

Run `2026-07-16-pjm-114-east-interface` (bundle
`results/calibration/pjmcong1_east_cut`): the pjm-113 keeper recipe verbatim
via replay + ONLY `pjm_east_interface_cut=True` (recorded in run_config, both
channels — the ERCOT-65 stomp check passed), on the corrected crosswalk, all
three years in one bundle, sequential. Gate adjudication:

| gate | test | result |
|---|---|---|
| 1 | provenance: binds ≥ 8/22; July-2025 EMAAC dual premium ∈ (+3.3, +30] | HOLD — 13/22 pre-solve; post-solve July **+8.96** (June +6.50; keeper was +3.3 flat) |
| 2 | C3c-2025 ∈ [26, 102] h | **HOLD — 40 h** (0.78× the DA 51; scorer PASS; pjm-111/112/113 were 17/18/18) |
| 3 | 2023 ≤ 18 / 2024 ≤ 12 | HOLD — **7 / 9** (both small-count PASS; actual east tranche 28 h / 46 h) |
| 4 | no PASS criterion flips | HOLD — every scored criterion PASS; the ONLY status change is price_tail FAIL→PASS |
| 5 | LOYO within 2023–2025 | HOLD — per-year scoring of the one bundle, zero fitted scalars, each year on its own measured series |

**Determination: CALIBRATED-WITH-CAVEATS** (rubric v2.5) — the first
non-NOT-YET PJM determination; the remaining caveat is the pre-existing
unscored storage benchmark (C5b/C5c data-blocked), untouched by this lane.
The mechanism behaves exactly as designed: the east cut separates ONLY
EMAAC (annual dual premium +0.45/+0.69/+1.37 across 2023/24/25; every other
zone stays uniform), and the model's tail becomes zonally structured the way
reality's is (§10.1) — 2024's 9 model tail hours are east-only, mirroring
the real 46-hour EASTERN-HUB tranche that the 2-hour system count hid.
Keeper promotion RECOMMENDED to the owner (keepers.json untouched —
owner-only), alongside sign-off request (i): the transfer-limit feed's
"Average Eastern" as the adopted east-cut limit source with the §10.5
boundary reconciliation.

## Pointers

* Keeper: `2026-07-16-pjm-113-short-only` (leg-A-only, promoted 2026-07-16;
  NOT-YET on C3c only — was `2026-07-15-pjm-111-cc-reconcile` when §1–8
  were written).
* Charter: `docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md` Part B.
* Probes: `scripts/probes/_pjm_c3c_summer_tail_decomp.py` (this session),
  `scripts/probes/_pjm_d1p_diurnal_cycling.py` (D-1p instrument),
  `scripts/probes/_pjm_nuclear_phantom_decomp.py` (§8.2 null result),
  `scripts/probes/_pjm_c3c_congestion_surface_decomp.py` (§10 east-cut
  measurement + pre-declared adjudication, pjm-cong-1).
* Winter half: `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` Part C.
* MISO precedent for leg A: calibration-log 2026-07-14 (miso-65) and the
  `unit_outage_short_windows` docstrings in `src/market_sim/data/outages.py` /
  `src/market_sim/data/fleet.py`.
