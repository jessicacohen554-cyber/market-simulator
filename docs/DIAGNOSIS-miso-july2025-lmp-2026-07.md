# MISO July-2025 LMP miss — capacity-data audit, import answer, and decomposition

**Date:** 2026-07-13. **Session:** `claude/miso-coal-deficit-analysis-1v41i7`.
**Trigger:** owner directive on the miso-62 keeper's July-2025 gap — "is it an
outage or capacity-availability issue where we're assuming more capacity is
available than actually is … was there an import shortage?"
**Scope:** measured-data audit only (no LP re-solve in this doc); the sizing
probe is `scripts/probes/_miso_shortout_probe.py`. All numbers below are from
committed measured sources (CAMPD unit-level CEMS, EIA-930 hourly, the D6 hub
LMP record, the pbc transfer-constraint-binding record) or the registered
miso-62 keeper payload/bundle — nothing is fit to a residual.

## 1. The miss, quantified (scored basis)

Model (miso-62 keeper, demand-weighted zonal) vs actual monthly LMP, 2025.
The C3a benchmark series is Indiana Hub (verified hour-identical in
`scripts/build_miso_lmp_reference.py`), so the scored gap carries the full
North premium:

| month | model | DA actual | Δ |
|---|---|---|---|
| Jan | 40.50 | 50.26 | −9.8 |
| Jun | 38.74 | 45.56 | −6.8 |
| **Jul** | **39.48** | **58.79** | **−19.3** |
| Aug | 35.65 | 41.57 | −5.9 |
| Dec | 41.69 | 48.29 | −6.6 |
| annual | 37.89 | 43.73 | −5.8 |

July decomposes on the measured hub record
(`data/raw/lmp-data/MISO/miso_hub_lmp_2025_da.csv.gz`) into three stacked,
separately-owned components:

1. **North–South separation (~$11 of Indiana's July gap).** July hub means:
   MINN 60.2 / INDIANA 58.8 / MICHIGAN 58.6 / ILLINOIS 55.8 vs ARKANSAS 34.8 /
   TEXAS 37.7 / LOUISIANA 38.6 / MS 36.2. The North–South hub-mean spread is
   **$21.5/MWh on average, positive in 82% of ALL July hours** (median $15.4),
   ramping diurnally $3 (h02) → $50 (h18). The model prices all six zones
   within $0.2 of each other (~$39.5) — i.e. the model's uniform price tracks
   the SOUTH's actual level and misses the entire North premium. The
   RDT-proper record (`transfer-constraint-binding`, DA `S_to_N`) binds
   **185 h in July 2025 — the most of any month** (mean |shadow| $13.1;
   binding-hour spread $27.7 vs non-binding $19.5), but the separation is
   BROAD, not confined to binding hours: it is the whole S→N corridor
   (RDT + RPE + internal flowgates + losses) that the 6-zone model collapses
   into links that never bind because the model's North never needs to pull.
2. **Broad footprint-level tightness (~$5 of the hub-average gap).** Hub-avg
   July actual 47.59 vs model 39.48; capping actual hours at $60 still leaves
   41.56 — the $60–100 shoulder band contributes ~$3.3 and the base level ~$2.
3. **Scarcity tail (~$2.7 hub-avg; larger on Indiana RT).** 27 h > $100 and
   9 h > $200 DA (RT: 88 h > $200 across 2025, actual peak days Jul 24 /
   28–29 at DA $205–344). The keeper prints **0 h > $200 in all of 2025**
   (payload `ordc.hoursGt200` model 0 vs actual 88).

## 2. Was there an import shortage? — No.

- Actual July 2025 net imports were 2.50 TWh (~3.4 GW avg). During the
  Jul 28–29 event MISO imported **5.0–9.6 GW at the peak blocks** (11.0 GW
  peak on Jul 24) — imports were strong, not short (EIA-930 hourly).
- The model, if anything, **under-imports 2025**: 13.2 TWh vs 19.0 actual
  (−5.8; the G-23 "2025 import starvation" residual, still open under the
  measured seam ladder). 2023: 36.3 vs 37.9; 2024: 20.3 vs 23.0.
- Under-importing raises model prices, so imports cannot explain the July
  undershoot; the domestic stack is too cheap/too available in spite of it.

## 3. Capacity-data audit (the owner's "double check")

- **Demand:** pinned exactly (model monthly = EIA-930 monthly to <0.1 TWh).
- **Wind/solar:** pinned exactly (model July wind potential 4.76 TWh = actual
  4.76; event-block wind potential mean 2.65 GW / min 1.10 GW matches the
  measured 1.1–3.8 GW collapse; solar ~12 GW at the peak blocks, correct).
- **Full-outage overlay (`campd-unit-outages-MISO.csv`):** covers all of 2025
  (windows through Dec-31). July-2025 average 11.8 GW out vs 10.8/11.2 in
  July 2023/24; 10.1 GW out during the Jul 28–29 event. No coverage gap.
- **Flat summer derates:** CC/CT carry the EIA-860 net-summer treatment;
  COAL/ST_GAS have none (by design).
- **Temperature-slope derates:** `temp_dependent_derate` is REFUTED on MISO's
  own fleet (rule-24 own-fleet check,
  `scripts/probes/_miso_temp_capability_envelope.py`; "never re-enable for
  MISO"). NOT re-opened here. Note the envelope conditions on ONLINE plants
  (`r > 0.30`), so it measures smooth capability vs temperature and is blind
  to discrete trips — compatible with §4.
- **Partial-outage channel:** ERCOT-only by explicit scoping
  (`fleet.py` "other ISOs carry no such file"); MISO has NO partial/short
  channel. Both detectors carry a 5-day duration floor.

## 4. The finding: event-coincident short outages are invisible (≈ the owner's "assuming more capacity than actually available")

Measured from per-unit CAMPD (July 2025, MISO fleet =
`bin_assignments_MISO.csv` plants):

- At the Jul 28–29 13:00–19:00 peak blocks, **11.9 GW** of capability that ran
  elsewhere in July was absent or reduced; the outage overlay sees only
  **3.6 GW** of it. The **invisible 8.4 GW** splits COAL 2.85 / CT_PEAKER 2.84
  / CC_REGULAR 1.26 / ST_GAS 0.66 / CHP classes ~0.8; ~2.4 GW of it is
  explainable as reserve holdback. Zonally it is **6.5 GW North vs 1.9 South —
  3.1 GW in MISO-Indiana alone** (the benchmark hub's zone), 2.78 GW of it
  Northern coal.
- The model's own reconstructed availability at the event block
  (`run_year(fleet_only=True)` on the keeper meta): **COAL 37.7 GW available
  vs 32.1 GW actual coal peak output**; total thermal 118.9 GW such that at
  the actual peak residual load the marginal MODEL offer is **$45–54 with
  14–20 GW of stack headroom** — while reality printed $200–433. Removing
  ~5–6 GW of phantom North capacity at those hours moves the margin into the
  $114–949 stack tail; that is the C3c/tail leg and part of leg-2.
- Same signature at the Jun 23–24 2025 event (12.9 GW missing, 6.1 invisible)
  and the Aug 2023 max-gen event (12.1 / 8.4). (A no-event July-2024 control
  reads 9.9 GW "invisible missing" — on a slack day most of that is economic
  partial-loading, so these event-day figures are upper bounds, not clean
  outage counts; the identification lives in the derive-script guards below.)
- Root cause of the invisibility: `derive_campd_unit_outages.py` carries
  `--min-outage-days 5` — **any forced outage shorter than 5 days does not
  exist for the model**, and short forced outages concentrate exactly in
  stressed periods. The measured record (miso-62 handoff) shows coal's real
  off-blocks < 48 h are rare (~800–1,150 unit-hours/yr) — small energy,
  decisive at events.

**Mechanism built (gated, default off):** `ScenarioConfig.
unit_outage_short_windows` + `scripts/derive_campd_unit_outages.py
--short-windows` → `campd-unit-outages-short-{ISO}.csv` →
`outages.unit_outage_short_derate_factors` (applied in
`fleet.generators_to_fleet_arrays` next to the parent overlay). Identification
guards (all measured, no price/residual input): coal-only detector; unit
annual CF ≥ 0.55 (the partial-outage detector's baseload guard — a cycling
unit's brief stop can be economics, a baseload unit's 1–5-day full stop with
10+ h starts and take-or-pay fuel cannot); the revealed-availability in-merit
filter always binding (6 h high-net-load overlap ≈ the parent gate's 20%
fraction; the ≥5-day full-stop override can never engage below the cap).
Windows capped strictly below the 5-day floor → the two extracts are disjoint
by construction. CT/CC event unavailability (2.8 + 1.3 GW) remains an open,
UNMODELED gap — no identification exists without a declared max-gen-event
registry (future intake: MISO capacity advisories / max-gen declarations).

## 5. Does the miso-62 coal fix help July 2025? — No (slightly worsens).

`coal_bit_committed_takeorpay` adds cheap contracted BIT committed capacity;
2025 COAL_BIT goes +6.3 TWh OVER actual (total coal +9.9) and C3a-2025 moved
−15.8% → −16.5% on the keeper. The July-2025 layers are the three in §1 —
availability truth at events (§4, built), the S→N separation (lane 3), and
scarcity depth (RDC/ELMP lane) — all orthogonal to the 2023/24 coal-deficit
lane.

## 6. Interaction with the total-coal-deficit lane (lane 1)

Scored class accounting (keeper payload vs bench classFull, TWh):

| year | total coal Δ | driver classes | gas side | imports Δ |
|---|---|---|---|---|
| 2023 | −12.2 | PRB −8.4, BIT −2.6, LIG −1.2 | ST_GAS −5.0, ST_CHP −3.9, CT_CHP −3.0 | −1.6 |
| 2024 | −15.8 | PRB −13.4, LIG −2.5 (BIT fixed) | CC +5.3, CT +7.1 vs ST_GAS −6.4, ST_CHP −4.0 | −2.7 |
| 2025 | **+9.9** | BIT +6.3, PRB +4.1 | ST_GAS −7.7, CC_CHP +4.3 | **−5.8** |

The 2025 July story and the 2025 coal-over are the same phenomenon seen from
two sides: the model's North coal is too available/too cheap in the high-gas
year, so the North never pulls on the South (S→N binds 236 h model vs 919 h
measured), prices stay uniform at the Northern coal/CC margin, and coal
over-generates while imports and Southern gas under-run. Note also the
persistent CHP/steam under-generation cluster (ST_GAS + ST_CHP + CT_CHP ≈
−11 to −13 TWh every year) and the classFull-vs-model total basis gap
(24/20/6 TWh in 2023/24/25) — both confound a naive "coal deficit" reading
and belong in lane-1's root-cause ledger before any all-coal pricing lever is
re-tested.

Three further lane-1 anchors measured this session:

- **The 2024 CT_PEAKER over-run is ~94% ECONOMIC** (D-2: only 1.16 of
  19.5 TWh forced, reliability floor) — at $2.19 gas the model's CT SRMC
  genuinely crosses below its full-cost PRB offer. The deficit's counterpart
  is a merit-order crossing, not a floor artifact.
- **The measured PRB conduct anchor exists in-repo**
  (`data/raw/som-competitive-conduct/som_competitive_conduct.csv`, 2023 SOM
  Table 7): 56% of MISO regulated-coal starts are must-run/self-commit (42%
  profitable + 14% ran-regardless), 44% offered economically. A PRB
  take-or-pay discount scoped by the measured self-commit share — rather than
  the blanket `coal_committed_takeorpay_all` (which overshoots PRB +7.8) — is
  the natural grounded scale-down to test once the availability channel and
  lane-3 are settled. The 2024 revealed-merit measurement (F923 + EIA-923,
  no model): PRB cap-wtd SRMC $27.9 ran at CF 0.458 while CC at SRMC $21.0
  ran 0.591 — **83% of PRB capacity sat above the CC fleet's SRMC and still
  ran at CF 0.43**. Real PRB dispatch does not follow full-SRMC offers.
- **The CT fuel-price gap-fill donor is class-blind and measurably cheap.**
  Measured 2024 delivered gas (F923, cap-weighted): CT filers $4.13/MMBtu vs
  CC $2.57 — a +$1.56 small-volume/retail-transport premium. Only 67% of
  MISO CT_PEAKER capacity files its own F923 price; the other 33% gap-fills
  from the `_NearbyFuelPrices` state/zone mean, which is **fuel-group-wide
  and quantity-weighted** (`fuel.py`), i.e. dominated by cheap CC burn
  (~$2.6-2.8). Those CTs are priced ~$16-20/MWh below their measured class
  cost — feeding BOTH the 2024 CT_PEAKER +7.1 economic over-run (at PRB's
  expense: the lane-1 "gas undercutting coal" candidate, now with a measured
  mechanism) AND July-2025's too-cheap North margin. Candidate fix (rule 14,
  gated default-off so every keeper replay stays byte-identical): a
  class-aware donor — same-class state/zone mean first, fuel-group mean as
  the fallback. Untested; needs its own A/B across all three years.

## 7. Recommended sequence

1. Size the §4 channel with the 2025-only throwaway probe
   (`_miso_shortout_probe.py`; rule 16 — never register). Read out: July/June
   monthly LMP, N-S zonal separation, hours > $200, coal TWh (should barely
   move annually — the windows are ~0.2–0.3 TWh/yr).
2. If material: full 2023–2025 keeper-candidate run (rule 16) with the
   channel armed, composed with miso-62 (and owner's call on composing
   miso-61 RPE per handoff lane 2), zero-forcing twin, DOF ledger unchanged
   (zero fitted parameters — the windows are each unit's own CEMS record).
3. The S→N separation (leg 1, the largest scored piece) stays lane 3's
   root-cause item — the RDT limits are published and already priced; the
   question is the model's missing North pull (coal cost/availability, §6).
4. Scarcity depth (RDC/ELMP engagement once headroom is honest) remains the
   C3c lane; re-read after step 1 — the §4 channel may let the existing
   pergen/zonal reserve machinery engage on its own.
