# FINDING — ercot-241 (2026-08-30): the off-core conduct screen MEASURED — all three kills CLEAR and the PHASE-1 GATE IS OPEN (12/12 reach, CC 4 / CT 3 contrast bins, occupancy ×35–670 over floor) — but the dependence the surface captures is POSITION/PARTICIPATION-carried, not within-resource repricing (paired position-fixed Δ ≈ +$0.2–0.5 at 0.9×HSL), and priors P1a/P2 MISSED: the shoulder hours carry more real gas high-price mass than the ercot-161 base rates implied

**Session ercot-241 (pickup), 2026-08-30, designated branch
`claude/ercot-241-backcast-8horad`. ZERO-SOLVE** — every number below is a
read of the tracked delivery-2023 SCED corpus (`data/raw/ercot/SCED/`, 306
of 323 shards carrying 2023 rows), the committed k33 carve-out sidecar,
the measured ORDC reserves parquet, EIA-930 and the committed ercot-239
JSON. Precommit
`docs/PRECOMMIT-ercot241-offcore-conduct-phase0-2026-08-30.md` pushed +
blob-verified (merged as PR #4349) BEFORE any measurement; **no
amendments** — every §2 construction ran as declared (three
within-convention notes in §1 below). Probe:
`scripts/probes/ercot241_offcore_conduct_phase0.py` →
`results/calibration/ercot241_offcore_conduct_phase0.json` (committed).
Charter: FINDING-ercot239 §6 **OBJECT 1** only; the wind pair (h6399/h7145)
stays queued and untouched; the two-config keeper is untouched. Reads ⊂
{2023}.

## 0. Verdict in six lines

1. **No kill fires.** K-1 (scope): wall-scope share of λ-band dispatched
   mass < 1/3 in **7 of 12** hours — one short of the ≥ 8 kill line. K-2
   (no-dependence): its (b) leg fails spectacularly — the tight/loose p90
   contrast is huge (§0.3). K-3 (identifiability): pooled tight × bins 2–6
   occupancy is 35,138 CC / 67,130 CT resource-intervals over 157 days —
   ×351/×671 the 100-interval floor.
2. **The PHASE-1 GATE IS OPEN, all four legs:** (ii) the tight-room M-4
   cell prices p90 ≥ $500 at the hour's declared bin in **12 of 12** hours
   (CT everywhere $898–4,952; CC $566–770 in bins 3–6); (iii) the
   tight/loose contrast exceeds 1.25× at p90 in **4 of 5** bins for CC
   (2.26–7.13×, bins 2–5) and **3 of 5** for CT (6.53–22.5×, bins 4–6);
   (iv) every cell the mechanism would arm holds ≥ 3,986 resource-intervals
   and ≥ 36 days. Phase-1 (separate pushed precommit; ONE 2023 probe solve
   on the k33 carve-out; full gates; rule-15 registration; keeper
   consequence ESCALATED, never self-adopted) is now **authorized to open**.
3. **What the dependence actually is — the honest core of this round.** The
   pooled surface contrast is real and large, but the precommit's own
   composition-free, position-free conduct measure (M-3, within-resource
   paired repricing at fixed 0.5/0.9×HSL positions) reads **≈ nil**: pooled
   median Δ at 0.9×HSL = **+$0.20 (CC, n=612 pairs)** / **+$0.52 (CT,
   n=1,094)**, ~$0 at 0.5×HSL. Resources do NOT rewrite their curves when
   room tightens. The tight-room elevation is carried by **position** (Base
   Points ride deep into the curve, leaving only the steep tail as spare)
   and **participation** (which units are on). A room axis would therefore
   parameterize the measured *tail state* of the online spare under
   tightness — defensible as a measured surface (it is exactly what the
   armed net-load wall already does, conditioned finer), but it is NOT
   evidence of tightness-triggered repricing conduct.
4. **P1a/P2 MISSED — the composition priors were too strong.** Wall-scope
   λ-band share < 1/3 in 7/12 (declared ≥ 8): the July/Sep core hours are
   storage-carried as expected (5 hours at share 0.00, PWRSTR largest in
   9/12 — P1b confirmed), but the shoulder hours are NOT (h2971 share 0.97,
   h7001 1.00, h5484 0.62). CC+CT offered-≥$500 mass ≤ 0.15 GW in only
   8/12 (declared ≥ 10; h5777 0.30 GW, h4623 0.19 GW). Real merchant-gas
   high-price mass exists at the object hours beyond the ercot-161 top-100
   base rates — those were measured inside net-load bin 6; this family
   lives in bins 2–6 at tighter room.
5. **P3 REFUTED on its ratio leg** (tight/loose p90 ≫ 1.25 in bins 2–5
   CC / 4–6 CT), **P4 CONFIRMED** (h2058 coal+ST_GAS λ-band share 0.397 vs
   0.000 median elsewhere — the March outage-season composition is a
   different animal, and h2058 is also the one UNMATCHED hour: 5 controls
   even after month ±1 widening), **P5 CONFIRMED** (occupancy ×35+ over
   floor everywhere).
6. **The surface is NON-MONOTONE in room in exactly the way a
   participation story predicts:** CT tight/loose ratio INVERTS below bin 4
   (0.26–0.29 — loose-room CT spare at low net load prices near cap: units
   posting $4,952 p90 while never expecting dispatch) and CC inverts in
   bin 6 (0.876). Any Phase-1 artifact must carry the whole measured table,
   inversions included — zero fitted scalars means no cherry-picking the
   cells that go the "right" way.

## 1. Gates and constructions (all as declared; three notes, no amendments)

* **V-0 PASS:** the recomputed {h : model < $200 ∧ actual ≥ $500}
  population is byte-identically the committed 14-hour family
  (`ercot239_missedevents_phase0._series` imported, not copied).
* **Corpus:** 323 shards selected by `_sced_source_files(2023)`, 306 with
  delivery-2023 rows after the delivery-year filter; status filter
  startswith("ON") ∧ ≠ "ONTEST"; scan 440 s. The corpus grain is **4 SCED
  snapshots per hour** (the NP3-965 15-minute disclosure grain) — interval
  means are over 4, not 12; all interval-mean quantities scale correctly.
* **Note 1 (declared-bin vs rank-bin, both per the precommit):**
  object-hour bin references use the §1 DECLARED mapping (committed
  ercot-239 `net_load_pctl_year` on the armed edges); the full-year M-4
  surface and control matching use `_netload_pct` (rank), §2's declared
  conditioning variable. The two differ at 5 of 12 hours (2971, 5369,
  5484, 7001, 7480 land one bin lower on rank). Both are recorded per
  hour in the JSON.
* **Note 2 (units, fixed before measurement):** ratio contrasts (K-2b,
  gate iii, P3b) graded on HR-mult (the armed wall's own convention), $
  reported alongside — the $ ratios agree in every graded cell (no
  unit-sensitivity anywhere near a threshold); explicit $ thresholds
  (K-2a $10, P3a $25, gate-ii $500) graded in $.
* **Note 3 (M-2 pooling):** the pooled control ladder concatenates each
  matched object hour's own control pool (a control hour serving k object
  hours contributes k times).
* **Controls:** 11 of 12 matched (8–36 controls; h7480 via the declared
  month ±1 widening). **h2058 UNMATCHED** (5 controls after widening —
  March high-net-load loose-room peers at hod 17–19 barely exist) and
  excluded from paired aggregates as declared, never padded. It remains in
  M-1/M-4/gate-(ii), which need no controls.

## 2. The central tables

**M-1 — who carries the λ-band, and the gap-band mass (interval-mean GW):**

| h | bin | λ | model | wall λ-band share | largest type | gap-band offered (all / wall / PWRSTR) |
|------|---|-------|--------|------|--------|---------------------|
| 2058 | 2 | 703 | 75.9 | 0.19 | PWRSTR | 0.28 / 0.06 / 0.22 |
| 2971 | 3 | 510 | 35.4 | **0.97** | CCGT90 | 0.47 / 0.03 / 0.04 |
| 4578 | 6 | 2008 | 175.4 | 0.00 | PWRSTR | 0.55 / 0.30 / 0.20 |
| 4623 | 5 | 632 | 49.9 | 0.00 | PWRSTR | 0.10 / 0.03 / 0.07 |
| 4626 | 5 | 652 | 58.1 | 0.00 | PWRSTR | 0.24 / 0.14 / 0.10 |
| 5369 | 6 | 666 | 78.4 | 0.43 | PWRSTR | 0.32 / 0.27 / 0.05 |
| 5484 | 6 | 558 | 166.8 | **0.62** | CCGT90 | 0.27 / 0.11 / 0.08 |
| 5777 | 5 | 536 | 91.5 | 0.26 | PWRSTR | 0.05 / 0.03 / 0.02 |
| 5943 | 5 | 584 | 64.8 | 0.00 | PWRSTR | 0.13 / 0.07 / 0.04 |
| 5945 | 6 | 961 | 125.3 | 0.00 | PWRSTR | 0.59 / 0.33 / 0.24 |
| 7001 | 4 | 757 | 44.1 | **1.00** | SCLE90 | 0.16 / 0.13 / 0.02 |
| 7480 | 3 | 601 | 43.4 | 0.35 | PWRSTR | 0.16 / 0.07 / 0.09 |

Reading: the family is NOT one population. The July/Sep core (4578, 4623,
4626, 5943, 5945 + mostly 5369/5777) is storage-carried, consistent with
ercot-161's census. The shoulder/edge hours (2971, 5484, 7001, partially
7480/5369) have merchant gas IN the price-setting band — the K-1 kill was
one hour short, and legitimately so.

**M-2 vs M-3 — the two conduct measures disagree, which is the finding:**

| class | M-2 spare p90, events pooled | M-2 p90, controls pooled | M-3 paired Δ @0.9×HSL (median, n) |
|-------|------------------------------|--------------------------|------------------------------------|
| CC | $698 (mult 335) | $99 (mult 49) | **+$0.20** (612) |
| CT | $5,000 (mult 2,370) | $76 (mult 38) | **+$0.52** (1,094) |
| ST_GAS (report-only) | $952 | $200 | $0.00 (285) |
| COAL (report-only) | $110 | $103 | $0.00 (252) |

The event-hour spare ladder is 7–65× the control ladder at p90 — yet the
same resources, compared at the same fixed curve positions against their
own matched-control selves, moved +$0.20–0.52. The elevation is where the
spare WINDOW sits (Base Point → HASL rides up the curve) and who
participates, not repriced curves. (The precommit anticipated exactly this
split: "the spare window moves with Base Point; M-3 does not".)

**M-4 — the candidate surface's graded cells (tight = room ≤ 0.10 pooled,
loose = 0.30–0.70; p90, $ / HR-mult ratio):**

| bin | CC tight p90 $ | CC ratio | CT tight p90 $ | CT ratio |
|-----|----------------|----------|----------------|----------|
| nl2 | 344 | 4.11 | 898 | 0.29 (inverted) |
| nl3 | 566 | 7.13 | 951 | 0.26 (inverted) |
| nl4 | 713 | 3.22 | 951 | 6.53 |
| nl5 | 770 | 2.26 | 4,952 | 22.5 |
| nl6 | 623 | 0.88 (inverted) | 4,952 | 11.9 |

Occupancy (tight, per bin 2–6): CC 3,986–13,479 resource-intervals /
36–77 days; CT 8,000–21,974 / 36–77. Nothing is thin.

## 3. Prior grading (declared ex ante, graded as declared)

* **P1 PARTIAL — leg (a) MISSED:** wall share < 1/3 in 7/12 (declared
  ≥ 8); leg (b) CONFIRMED: PWRSTR largest in 9/12 (declared ≥ 8).
* **P2 MISSED:** CC+CT offered-≥$500 ≤ 0.15 GW in 8/12 (declared ≥ 10);
  h5777 0.30 GW, h4623 0.19 GW, h2971 0.16 GW, h4578 0.16 GW.
* **P3 REFUTED (on its ratio leg):** paired Δ leg holds trivially
  (+$0.20/+$0.52 ≪ $25) but the tight/loose p90 ratio exceeds 1.25 in
  bins 2–5 (CC) and 4–6 (CT) — the conjunction fails. There IS measured
  room dependence at the surface level; §0.3 says what kind.
* **P4 CONFIRMED:** h2058 coal+ST_GAS λ-band share 0.397 vs 0.000 median
  elsewhere (≥ 2× trivially).
* **P5 CONFIRMED:** every tight × bin 2–6 cell ≥ 3,986 CC / 8,000 CT
  resource-intervals, ≥ 36 days (declared 100 / 10).

## 4. Kills and the Phase-1 gate (direction-blind, as declared)

* **K-1 clear** (7 < 8): recorded at full magnitude — one more
  storage-carried hour and this round would have died on scope. The
  shoulder hours saved it.
* **K-2 clear:** (a) holds (+$0.20/+$0.52 < $10) but (b) fails everywhere
  it could (ratios up to 22.5× ≫ 1.15) — the kill needs both.
* **K-3 clear:** occupancy ×351/×671 over the floor.
* **Gate (ii) 12/12** (declared ≥ 6): every hour's (declared-bin, tight)
  cell prices p90 ≥ $500 for CT, and for CC too in bins 3–6.
* **Gate (iii) PASS:** CC 4 bins, CT 3 bins > 1.25× (declared ≥ 3, either
  class).
* **Gate (iv) PASS both classes.**
* **⇒ PHASE-1 OPENS** under the precommit's own terms: a separate pushed
  precommit; ONE 2023 probe solve on the k33 carve-out config; full gates;
  rule-15 registration as probe/candidate; verdict unrewritten; any keeper
  consequence escalated to the owner, never self-adopted.

## 5. What Phase-1 must honestly carry (design constraints from this measurement)

1. **The mechanism is a room-axis EXTENSION of the armed RT wall** (M-5
   reconciliation; rule 19 `[R-ONE-MECH]`) — the same measured-spare-ladder
   surface, conditioned (class × net-load bin × room bin) instead of
   (class × net-load bin). Never a stacked adder/floor. The k33 config's
   armed path (`ercot_offer_surface_cleared_share_rt` mode=replace,
   position_tail, swcap_clip k_peak=33, faststart pool) is the base it
   extends.
2. **Zero fitted scalars means the whole M-4 table, inversions included.**
   The CT bins 2–3 inversion (loose-room near-cap posting) and CC bin 6
   inversion ride along; both bin grids are fixed ex ante (armed net-load
   edges; §2 room edges).
3. **The forward-driver question is the Phase-1 precommit's to declare:**
   the backcast conditioning variable is measured rtolcap percentile; a
   forecast year needs the model's own reserve-room state as the analogue
   (rule 13's regenerability test). This is the same forward-native
   pattern as the net-load axis (which regenerates from the year's own
   load+VRE), but it must be declared, not assumed.
4. **What a solve can and cannot show:** M-3 says resources do not
   reprice; the surface prices the tail STATE. In the LP, position is
   endogenous (dispatch rides up the same ladder), so a room-conditioned
   ladder risks double-counting the position effect M-2 measured — the
   probe solve's gates (C-family + D-diagnostics + the year's non-event
   hours) are exactly the test of whether the extension prices the 12
   hours without breaking the 8,748 others. A gate miss is the verdict.
5. **h2058 is likely out of reach** of any CC/CT room axis (coal+ST_GAS
   carried, March outage season, UNMATCHED controls) — Phase-1 should
   declare its expected reach as the 11-hour conduct core, with h2058
   graded but not load-bearing.

## 6. Disposition

Phase-0 complete: zero solves, zero input changes, nothing armed, no
matrix stamp (no mechanism TESTED yet — the ercot-239 "nothing tested ⇒ no
stamp" precedent; the Phase-1 session that actually arms the room axis
stamps its cell then), keeper untouched, years ⊂ {2023}, no marker, freeze
respected, ERCOT surfaces only. Deliverables: the merged precommit + this
probe + JSON + this FINDING + the calibration-log entry, pushed on the
designated branch. **The chartered question is answered: a measured,
occupancy-adequate, zero-fitted-scalar room-conditioned surface EXISTS and
REACHES the object family (gate open) — and the same measurement shows the
dependence is position/participation-carried, not repricing conduct, which
is the central fact the Phase-1 precommit must be written around.**
