# FINDING — ercot-164 Phase 0/1: the WP-B nodal layer's identification LANDS, but it refutes the layer *as specified*. The station-to-station corridor tail is OVERNIGHT-shaped (2025 gap-shape corr −0.79) — the missing mid-afternoon mode lives in PNHNDL interface binding (gap-shape corr **+0.96**) and a stable afternoon-heavy nodal minority (**+0.80**), both diluted or mis-owned by the armed pooled share. A redirected charter is NAMED (not built): unpool the share by diurnal family + give the Panhandle interface ONE correctly-timed owner.

**Session ercot-164, 2026-08-04. NO LP, no solve, no mechanism armed, no
`ScenarioConfig` field added, no matrix cell verdict minted, keeper UNCHANGED
(`2026-08-03-ercot158-pool-arm`; NOT-YET, open gates C3a 2023-only, C3b
2023-only, C3c, C7 2023-lignite cv-leg).** §5.1 item 7 (the WP-B nodal
curtailment layer, unblocked on data at ERCOT-160): build the layer's
IDENTIFICATION from the station-to-station NP6-86 binding rows that
`curate_gtc_limits._gtc_only` drops, resolved through the NP4-160-SG spine
(`data/raw/ercot-network-model/`, published 2026-07-29 — the only vintage that
exists), on the same net-load × hour × season axis
`ercot_wtx_curtailment_driver` uses, and answer whether that measured pressure
reproduces the ERCOT-121 §4 shape (2025 actual wind curtailment mid-afternoon
h15–16 vs model overnight h22–23, hod corr −0.079).

Probe (no-LP, committed data only):
`scripts/probes/ercot164_wpb_nodal_identification.py` →
`results/calibration/ercot164_wpb_nodal_identification.json`. Inputs: NP6-86
2023–2025 parquets, the NP4-160-SG spine, HIFLD TX substations
(validation-grade), `ercot-hsl` hourly + zonal (shape target),
`data/raw/reference/ercot_wtx_curtailment_share.csv` (the armed pooled share),
and the keeper's committed hourly sidecars (model dispatch + zone prices).
Rule 22: 2023–2025 only; the 2020–2022 NP6-86 archives were not read.

## 0. Verdict

1. **Phase-0 vintage gate: PASS, measured on this session's own population.**
   The 2026-07-29 spine resolves **91.3 / 90.3 / 90.1 %** of the distinct
   stations appearing in 2023/2024/2025 binding station-rows, **92.5 / 94.4 /
   93.0 %** of binding-row endpoint weight, and **100.0 / 99.9 / 99.8 %** of
   binding rows resolve at least one endpoint (ERCOT-160's 186/191 and 50/50
   were a different population and were not inherited). The vintage risk did
   not materialize for the corridor question.
2. **The layer as specified — aggregate the dropped station-to-station
   corridor rows into ONE curtailment-pressure frequency — is REFUTED by its
   own identification data.** The LZ_WEST 138/345 kV nodal tail is
   overnight-shaped in all three years (hod peak h21–23; afternoon h13–17
   share 0.146–0.159 vs overnight h21–02 share 0.317–0.344) and its 2025
   hod profile is **anti-correlated with the under-curtailment gap:
   corr −0.793**. Feeding it into the driver would deepen the ceiling in the
   overnight troughs — exactly where the keeper already over-weights
   curtailment (model overnight share 0.357 vs actual 0.266 in 2025).
3. **The mid-afternoon mode the model misses EXISTS in the same data, one
   resolution level finer.** The 2025 wind gap (actual − model, positive
   part; 3.22 TWh, peak h11, daytime h9–17 share 0.567) is reproduced by:
   - **PNHNDL interface binding frequency** — 2025 hod peak h10, afternoon
     share 0.262 vs overnight 0.171, **gap-shape corr +0.961**, hod corr vs
     actual wind curtailment +0.628 and vs solar +0.684;
   - **an afternoon-heavy nodal minority** (10–16 elements/yr, 15.5–19.4 %
     of nodal binding weight; core membership stable all three years:
     PALOUS_WOLFCA1_1, TREADW_YELWJC1_1, plus a rotating Maddux/San-Angelo
     family) — hod peak h14–15, hod corr vs actual solar curtailment
     **+0.948–0.967 in every year**, 2025 wind-gap-shape corr **+0.802**.
   The dominant overnight tail matches the locus the model already produces;
   the 2025 inversion is the *growth of the daytime mode*, which no armed
   mechanism carries with the right timing.
4. **The rule-19 stack ERCOT-121 flagged as opaque is now attributed, and it
   is a TIMING miss, not a depth miss.** The keeper's endogenous
   Panhandle→North tie reproduces ERCOT-121's separation COUNTS almost
   exactly (this probe: 2,666 / 3,214 / 4,066 h vs ERCOT-121's 2,708 /
   3,221 / 4,074) but at the wrong time of day: model separation peaks h22
   with hod corr vs measured PNHNDL binding **−0.162 (2024) / −0.170
   (2025)**. Measured PNHNDL enforcement itself moved into the solar-flood
   hours by 2025 (active-set hod peak h13, afternoon share 0.269; binding
   peak h10), while the tie's non-active-hour stand-in at the static rating
   manufactures overnight binding the real 2025 corridor did not have
   (PNHNDL was in SCED's active set only 2,039 h in 2025). The armed pooled
   share reinforces the same overnight timing (peak h22–23, daytime share
   0.27–0.32) because the overnight nodal tail dominates its union. **Two
   mechanisms own the Panhandle phenomenon and both put it at night.**
5. **The HIFLD geographic sub-split of the corridor is NOT viable from
   committed data** — deterministic name tiers cover only 2.5–6.6 % of
   corridor endpoint weight and the prefix tier produces detectable false
   positives (§5). The element-level diurnal clustering (verdict 3) does the
   job the geography split was for — separating the daytime family from the
   overnight family — without coordinates. `panhandle_geo_nodal` measured
   empty; the Panhandle daytime signal enters through PNHNDL, not through
   HIFLD-resolvable nodal endpoints.
6. **A redirected charter is NAMED (not built), pending owner authorization**
   (the ercot-159/162 structural-arm precedent): **WP-B v2 — diurnal-family
   unpooled curtailment-pressure shares + Panhandle interface timing
   reconciliation** (§6). It is a QUANTITY object bounding the wind/solar
   variables: a ceiling-clipped variable is never marginal, so it is NOT a
   C3a/C3b/C3c price lever and "the residual didn't move" is not a verdict
   on it (rule 1). It is judged on curtailment volume AND shape ([3e] /
   D-1 / the C2-adjacent gas displacement).

## 1. Match rate — the vintage duty, measured on this session's population

Per year, over binding (ShadowPrice > 0) station-to-station rows only:

| year | binding station rows | distinct stations | stations resolved | endpoint weight | rows ≥1 endpoint | rows both |
|---|---|---|---|---|---|---|
| 2023 | 216,138 | 693 | 633 (91.3 %) | 92.5 % | 100.0 % | 85.1 % |
| 2024 | 260,271 | 713 | 644 (90.3 %) | 94.4 % | 99.9 % | 88.8 % |
| 2025 | 353,416 | 765 | 689 (90.1 %) | 93.0 % | 99.8 % | 86.2 % |

The corridor mask needs *either* endpoint in LZ_WEST, so the operative rate is
the ≥1-endpoint row rate (99.8–100 %). The ~10 % unresolved stations are
predominantly low-weight (endpoint-weight rate ≥ 92.5 %) and consistent with
nodes commissioned/retired across the 2023→2026-07 network drift the ERCOT-160
README warns about. This is a Phase-0 PASS: the identification below is not
match-rate-limited.

## 2. D-2 attribution — what curtails each corridor zone in the keeper (rule 19 prerequisite)

Enumerated from the keeper's `run_config.json` + `ERCOT_GTC_LINK_MAP` +
`market_sim.data.gtc` before proposing anything:

| zone | mechanism | armed by | timing measured this session |
|---|---|---|---|
| West | LP economics (surplus curtailment) | always | overnight troughs (model wind curt peak h23) |
| West | West→North + West→South_Central ties at measured WESTEX limits | `ercot_gtc_limits_measured=True` | inert: 2/17/4 separation hours (>|$1|) 2023/24/25 |
| West | wtx driver ceiling (pooled share × depth 0.1004/0.1637) | `ercot_wtx_curtailment_driver=True` | share peaks h22–23; daytime share 0.27–0.32 |
| Panhandle | LP economics | always | overnight |
| Panhandle | Panhandle→North tie at measured PNHNDL limits (static 2,680 MW stand-in on non-active hours) | `ercot_gtc_limits_measured=True` | binds 2,666/3,214/4,066 h, peak h22 — hod corr vs measured PNHNDL binding −0.162/−0.170 (2024/25) |
| Panhandle | wtx driver ceiling (same pooled share broadcast) | `ercot_wtx_curtailment_driver=True` | same overnight shape, active ~8,750 h/yr (ERCOT-121 §4) |

The ERCOT-121 stack is the last two Panhandle rows; §4 of this finding times
it. The West interface rows are effectively inert (the reduced West zone's
aggregate export almost never reaches the measured WESTEX limit), which is the
documented reduced-form role of the driver there (sole mechanism, clean).

## 3. The shape test — where each measured signal puts its pressure

Sanity anchor first: the probe reproduces ERCOT-121 §4 from committed
sidecars — model wind curtailment hod corr vs actual +0.645 / +0.462 /
**−0.077** (2023/24/25; documented 0.610 / 0.459 / −0.079), model peak h23 in
all years, actual peak h0 / h1 / **h15**. Actual 2025 is bimodal (afternoon
0.222, overnight 0.266); the model is unimodal overnight (0.159 / 0.357); the
gap is the daytime mode (2025 gap daytime h9–17 share **0.567**, peak h11;
2023/24 gap daytime 0.381 / 0.404 — the mode predates 2025, 2025 made it
dominant).

Signals on the driver's own axis, 2025 (full three-year tables in the probe
JSON; `aft` = h13–17 share of the hod profile, `ovn` = h21–02, `day` = h9–17;
`gapHod` = Pearson corr of the signal's 24-point hod profile vs the wind gap's):

| signal | mean | peak | aft | ovn | day | gapHod(w) | hodCorr vs act wind | vs act solar |
|---|---|---|---|---|---|---|---|---|
| iface_pnhndl | 0.098 | h10 | 0.262 | 0.171 | 0.541 | **+0.961** | +0.628 | +0.684 |
| iface_westex | 0.069 | h23 | 0.221 | 0.317 | — | −0.067 | +0.241 | +0.162 |
| iface_gtc (both) | 0.157 | h10 | 0.242 | 0.230 | — | +0.854 | +0.678 | +0.688 |
| corridor_nodal (the "layer" as specified) | 0.592 | h23 | 0.146 | 0.339 | 0.271 | **−0.793** | −0.068 | −0.839 |
| nodal_afternoon_cluster | 0.116 | h15 | 0.368 | 0.151 | 0.629 | **+0.802** | +0.393 | **+0.948** |
| armed_pooled_share (as armed) | 0.557 | h23 | 0.175 | 0.306 | 0.323 | −0.670 | +0.098 | −0.755 |
| corridor_nodal_intensity | 1.011 | h22 | 0.172 | 0.340 | — | −0.778 | −0.055 | −0.647 |

Three structural facts:

- **The pooled share is overnight because the nodal tail dominates its
  union** (nodal mean 0.37→0.59 vs interface 0.13–0.19 across years): the
  ≥1-constraint OR is near-saturated (0.64 mean in 2025) and inherits the
  majority family's shape. The driver therefore cuts deepest at night — the
  hod-shape it applies is anti-correlated with the very gap it exists to
  close (gapHod −0.30 / −0.40 / −0.67 across years, worsening as the daytime
  mode grows).
- **The afternoon nodal family is real, small, and stable**: aft>0.30
  elements carry 19.4 / 15.5 / 16.7 % of nodal binding weight;
  PALOUS_WOLFCA1_1 (aft share 0.60/0.54/0.57, overnight share 0.000 in 2023
  and 2025) and TREADW_YELWJC1_1 (0.36/0.36/0.32) persist all three years;
  its hod corr vs actual **solar** curtailment is +0.948–0.967 every year —
  it is the solar-flood/daytime-export congestion family, and it also carries
  the 2025 wind gap shape (+0.802) because 2025's missing wind curtailment is
  solar-coincident (ERCOT-121 §4's own reading).
- **Season structure agrees**: 2025 actual wind curtailment peaks h15/h16 in
  DJF/MAM and h9 in JJA (daytime in every solar-strong season, overnight only
  in SON); measured iface binding follows (2025 MAM peak h10 aft 0.274, JJA
  peak h13 aft 0.338) while the nodal tail stays h21–23 in every season of
  every year.

## 4. The stack, timed — why the armed pair under-curtails despite 4 kh of binding

The keeper's Panhandle tie does bind — the model separation counts match
ERCOT-121 to within ~1 % (this probe recomputes them from the committed
`system_<year>.parquet` zone prices: 2,666 / 3,214 / 4,066 h at |Δ|>$1). But:

- model separation hod: peak h22, afternoon 0.206, overnight 0.279 (2025);
- measured PNHNDL binding hod: peak h10, afternoon 0.262, overnight 0.171;
- corr between the two profiles: **−0.170** (2025), −0.162 (2024), +0.364
  (2023 — the year before the daytime regime took over, when the real
  corridor still congested at night).

Mechanism: `data.gtc` stands the tie's cap at the measured `limit_mean` only
in hours the GTC was in SCED's *active set* (1,312 / 2,692 / 2,039 h) and at
the static 2,680 MW rating everywhere else. Overnight, real 2025 PNHNDL was
mostly *not enforced* (more headroom than the static rating implies) while
the model's static cap + high overnight wind saturates the tie — manufactured
overnight congestion. Mid-afternoon, real PNHNDL was enforced (limit ≈ 3,018
MW active-afternoon mean vs 2,827 overnight — the level barely moves; the
*enforcement incidence* moved) and binding at h10-peaked incidence the model
does not reproduce because its afternoon Panhandle flow (wind dip + solar
rise, zonally aggregated) sits below the cap. On top of this, the driver
broadcasts its overnight-shaped pooled ceiling to the same zone in ~8,750
h/yr. Net effect: separation-hour COUNT right, curtailment volume and timing
both wrong — the precise anatomy of ERCOT-121 §4's "level calibrated,
attribution opaque".

## 5. The geographic sub-split negative (reported, per the charter's honesty duty)

Deterministic HIFLD matching (exact normalized + unique-prefix ≥6 chars, the
fuzzy tier deliberately excluded after the WP-B build's LMESA→El-Paso false
positive) covers only **2.5 / 5.6 / 6.6 %** of corridor nodal endpoint weight
(top binder codes — MDSSW, MGSES, VEALMOOR, KNAPP, SCRCV, YELWJCKT … — are
abbreviations HIFLD does not carry verbatim), and its B2 cross-check
(HIFLD-boxed "Panhandle" stations showing LZ_SOUTH/LZ_HOUSTON zones) shows the
prefix tier still admits false positives. `panhandle_geo_nodal` is empty at
this coverage. **Conclusion: within-LZ_WEST geographic resolution is not
achievable from committed data**, and — per §3 — not needed: the element's own
binding-hod placement separates the families the geography split was after.
(`Resource_Node_to_Unit`-based unit-name joins to EIA plants remain the
"judgement step" the ERCOT-160 README declined; nothing here changes that.)

## 6. The redirected charter — NAMED, NOT BUILT (owner authorization required before any LP)

**Name: WP-B v2 — diurnal-family unpooled curtailment-pressure shares +
Panhandle interface timing reconciliation.** One coherent reconciliation, not
a bolt-on, because the armed depths were LOYO-identified WITH the current tie
and pooled share live — changing either de-calibrates both.

Components (design detail is the build session's job; this names the object
and its constraints):

1. **Unpool the share.** Replace the single pooled `congestion_share` with
   per-family shares on the same (net-load decile × hod × season) axis,
   derived from the same NP6-86 + NP4-160-SG sources: family-D (daytime /
   solar-flood: the afternoon-heavy nodal elements; membership derived per
   year from each element's own binding-hod placement — a source-data derive,
   rule 23) and family-N (overnight / wind-export: the dominant nodal tail).
   Whether WESTEX joins family-N or stays interface-only is a build-session
   A/B (its 2025 shape went overnight; its West links are inert either way).
2. **One owner for the Panhandle interface, correctly timed (rule 19).** The
   build session must pick, via pre-registered A/B, between: (a) the tie owns
   it — PNHNDL leaves the driver's share entirely AND the tie's non-active-
   hour stand-in is re-examined against the measured enforcement-incidence
   structure (§4; the static-rating stand-in over-constrains overnight — a
   rule-14 misalignment reconciliation on measured data, not a fit); or
   (b) a Panhandle-scoped share owns the sub-limit pressure and the tie keeps
   only its measured active-hour caps. Never both on the same hours.
3. **Depths re-identified under LOYO** (rule 23 / the anti-residual gate):
   the two per-tech scalars re-centre on the measured curtailment MW quantity
   with the unpooled shares live. **Any DOF beyond the existing two depths
   (e.g. per-family weights) needs its own identification source declared to
   the owner before the build** — the default design keeps two.
4. **Forward story (rule 13).** Shares remain functions of the model's OWN
   net-load (decile re-ranks each forecast year; more West solar → deeper
   daytime deciles → more family-D pressure — the self-scaling the driver
   already demonstrates), hod/season are calendar, and family membership
   re-derives whenever a new NP6-86 year lands (frozen-topology assumption #2
   of the WP-B handoff carries over unchanged, owner-accepted). Nothing reads
   the reported curtailment volume except the depth level scalars, exactly as
   today.
5. **Judged on** [3e] curtailment volume AND hod/season shape (the §4
   inversion), the C2-adjacent gas displacement, and D-1 wind/solar shape —
   NOT on C3a/C3b/C3c (quantity object; a ceiling-clipped variable is never
   marginal). LOYO within 2023–2025 before any promotion (rule 22).

Expected leverage, stated honestly: the 2025 wind gap is 3.22 TWh with 0.567
of it daytime; the signals that carry that shape are measured and stable; but
the depth conversion stays a level scalar, so whether volume closes without
shape distortion is an empirical build-session question. The alternative of
doing nothing leaves the driver applying a share whose gap-shape correlation
is −0.67 and worsening as solar grows.

## 7. Governance attestation

- **No LP, no solve, no registration** — keeper untouched; no dashboard entry
  (rule 15 applies to runs; none was produced — the ercot-147/152/161/163
  no-LP pattern).
- **Rule 22**: only 2023–2025 read; 2020–2022 NP6-86 archives untouched;
  no holdout year scored.
- **Rule 19**: D-2 enumeration done BEFORE proposing (§2); the charter's core
  is the reconciliation, not a third mechanism on the stack.
- **Rule 13/14**: every signal here is measured SCED binding incidence /
  enforcement structure; the gap (actual − model) was used as a DIAGNOSTIC
  target only (the ERCOT-121 reconciliation pattern) — the charter forbids
  fitting any share to it; depths remain the sole outcome-anchored scalars,
  owner-accepted at the WP-B build.
- **Rule 28b/c**: no mechanism tested → no matrix cell verdict minted; no
  `ScenarioConfig` field added → no matrix row due. §5.1 item 7's queue entry
  is updated in-session with this outcome.
- **Scope fence honored**: item 8 not re-opened; no envelope/availability-cap
  family touched; the West/Panhandle TOPOLOGY SPLIT stays CLOSED — nothing
  here is a zone split; the finding's families are share-table resolution,
  sub-zonal by construction (DIAGNOSIS-ercot-trough §§7–10 unchallenged).
- **Vintage duty**: match rates measured on this session's own per-year
  populations (§1); ERCOT-160's rates never inherited.
