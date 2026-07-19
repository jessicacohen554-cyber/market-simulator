# FINDING (caiso-102): the inelastic-charge channels MEASURED (the DAM allocates 76-84 % of realized battery charge; the FMM covers 94-97 %; RT additions are reg-down-deployment-shaped; the non-belly charge clears $6-9 ABOVE the belly floor — obligation conduct, not arbitrage) — and the evening merit-stack diagnosis found a +1h FRAME DEFECT: `_eia_hourly_frame_filled` anchors on the hour-ending `Local time` stamp, so every gap-bridged BA-year (CISO-2025, PJM-2023, MISO-2025) solved one hour LATE; fixed at the root, 2025 artifacts re-derived, single-delta B-leg pre-registered here BEFORE adjudication

**Session 2026-07-19 (CAISO-102 — the caiso-101 handoff's chartered successor:
priority 1 = the inelastic-conduct derive, priority 2 = the evening merit-stack
diagnosis). Derive-first: the only LPs run are (i) the same-machine repro of
the PROMOTED caiso-101 keeper recipe (`scripts/probes/_caiso102_repro_A.py` →
gitignored `caiso102_repro_A`, un-registered per the FINDING-caiso92b
protocol; reproduces the keeper ladder DIGIT-FOR-DIGIT — belly
+6.0/+6.6/+5.0, evening −5.8/−4.9/−3.0, overnight +0.8/−0.0/+1.6) and (ii)
the single-delta `caiso102_hourfix_B` DEFECT-FIX leg pre-registered in §6
below (a rule-14 measured-input correction, not a mechanism — no conduct
mechanism was built or solved; the conduct channels go to the §7 owner ask).
Instruments (committed): `scripts/probes/_caiso102_charge_channels.py` (the
CAISO Daily Energy Storage Report market_output layers: IFM/RUC/RTPD/RTD EN +
SOC + RU/RD/SR/NR, LESR basis), `scripts/probes/_caiso102_evening_merit.py`
(hour-paired evening composition, resid-quartile conditioned). Data: the
committed `data/raw/storage-as-awards/CAISO/storage-report-*.xlsx` (12
quarterly files, 2023-2025), EIA-930 CISO hourly, CAMPD facility CEMS,
`actual_lmp_hourly_CAISO.parquet`.**

## 1. Channel (a) — the DA award allocates the charge; the RT margin re-times a minority

LESR (standalone + co-located batteries — the NG:OTH/EIA-860 basis of
caiso-98/99/100; HYBD excluded, combined-resource EN mixes PV). Per year:
realized (RTD) charge vs the day-ahead (IFM) schedule and the 15-min FMM
(RTPD) commitment; "DA-share" = Σ_h min(chg_IFM, chg_RTD) / Σ_h chg_RTD:

| year | RTD chg TWh | IFM chg TWh | DA-share of realized | FMM(RTPD) chg | FMM-share | EIA-930 chg (basis xcheck) |
|---|---|---|---|---|---|---|
| 2023 | 3.99 | 4.19 | **0.840** | 4.10 | 0.940 | 4.07 |
| 2024 | 8.02 | 7.14 | **0.799** | 8.11 | 0.950 | 8.73 |
| 2025 | 12.22 | 9.82 | **0.760** | 12.54 | 0.970 | 13.02 |

Belly (hod 10-14) DA-share is higher still: **0.905 / 0.885 / 0.820**. The
charge decision is made in the DAM against DA prices — the RT margin the LP
prices re-times only 16-24 % of the volume, and even that is committed at the
15-minute FMM (94-97 % coverage), not the 5-minute margin. Daily IFM charge
volume is fleet-size-driven (p10-p90 only ±30 % around the median) and only
modestly spread-modulated within-month (corr with DA TB4, month-detrended:
0.26/0.47/0.47; raw 0.04/0.02/−0.25) — the caiso-101 inelasticity finding,
now measured at the allocation layer itself.

## 2. Channel (b) — the RT-added charge is AS-deployment-shaped and grows with the reg-down book

IFM AS awards (avg MW) and the RT re-dispatch delta (hour-mean RTD EN − IFM
EN; negative = extra RT charge) conditioned on the fleet's own reg-down award:

| year | RU | RD | SR | NR | corr(ΔEN, RD) | slope MW/MW-RD | extra-RT-chg share in top-RD-quartile hours |
|---|---|---|---|---|---|---|---|
| 2023 | 349 | 571 | 71 | 19 | +0.12 | +0.16 | 0.28 |
| 2024 | 458 | 743 | 192 | 92 | −0.21 | −0.39 | 0.44 |
| 2025 | 441 | 810 | 243 | 158 | **−0.46** | **−1.34** | **0.58** |

RD awards peak in the morning/belly (2025 hod-profile 510/997/1169/1026/635/654
across the six windows) — the battery book carries ~1 GW of reg-down through
exactly the hours the RT charge additions land. By 2025 more than half the
extra-RT charge sits in the top-RD-quartile hours and each MW of RD award is
associated with −1.3 MW of RT re-dispatch: the RT-added volume is
deployment/positioning conduct, not price-responsive marginal charging.

## 3. Channel (c) — the non-belly charge pays ABOVE the belly floor (obligation-rational, arbitrage-irrational), and the LP's miss is concentrated overnight + 2025-morning

Realized charge by window (TWh), its charge-weighted actual RT λ, and the
same-machine keeper repro's model charge (`caiso102_repro_A`):

| 2025 window | meas RTD | DA-shr | λ_rt | RT-added λ | model |
|---|---|---|---|---|---|
| overnight(0-5) | 0.357 | 0.669 | 39.9 | 37.9 | **0.036** |
| morning(6-9) | 2.838 | 0.609 | 20.0 | 15.2 | **1.353** |
| belly(10-14) | 8.256 | 0.820 | 14.9 | 10.8 | 9.317 |
| pm-shldr(15-16) | 0.725 | 0.746 | 11.1 | 19.1 | 1.430 |
| evening(17-21) | 0.038 | 0.268 | 32.4 | 34.0 | 0.055 |
| late(22-23) | 0.009 | 0.116 | 37.8 | 38.9 | 0.000 |

(2024: model overnight 0.110 vs measured 0.360, morning 1.927 vs 1.948, belly
6.035 vs 5.345; 2023: model belly 3.186 vs 2.604, overnight 0.099 vs 0.334.)
The non-belly totals: measured 1.38/2.68/3.97 TWh at charge-weighted λ
36.0/20.1/20.3 — **$6-9/MWh ABOVE the same-year belly charge-weighted floor**
(27.1/12.3/14.9). Pure arbitrage would move that energy into the belly;
the fleet pays the premium because the charge is positioning: the measured
RTD net profile runs a real SECOND DAILY CYCLE (overnight charge hod 2-3
~170-260 MW avg → morning discharge peak hod 5-6, 450-935/671-1207/899-1690
MW avg 2023/24/25) plus SOC restoration under the AS book (RTD SOC hod-mean
troughs at hod 6 and rebuilds to a hod-15 peak of 14.8/24.9/34.3 GWh). The
LP's annual under-charge outside the belly (the −4/−8 % of
FINDING-caiso100 §5) decomposes into: overnight −0.24/−0.25/−0.32 TWh (the
second cycle at $38-58 λ the arbitrage-only objective refuses) and a
2025-only morning gap −1.49 TWh (partly the §5 frame defect: the +1h-late
solar profile starved the model's mornings of ~4 GW of solar and priced its
morning charge out — re-measured on the §6 B-leg).

## 4. Priority 2 — WHO SERVES THE EVENING (hour-paired, resid-quartile conditioned)

`_caiso102_evening_merit.py` on `caiso102_repro_A`, evening = model hod 17-21
(intervals 17:00-22:00). **Clock note:** EIA-930 rows are HOUR-ENDING labeled
(Hour 1..25, `Local time` 01:00 = interval 00:00-01:00, verified uniform
across the per-BA extracts); this probe indexes measured rows positionally
(interval-beginning), the model/LMP clock. The `_caiso_who_serves_night/day.py`
loaders instead take hod from the hour-ending stamp, so their EIA-930 windows
sit one hour EARLY vs the model's — caiso-95 §4's "evening" compared model
17-22 against measured 16-21, and its "+1.9/2.1/2.2 TWh excess evening
import" does not survive alignment:

| evening TWh (model / meas) | 2023 | 2024 | 2025 |
|---|---|---|---|
| net imports | 7.26 / 8.19 | 7.60 / 8.12 | 7.70 / 9.11 |
| gas TOTAL (930 NG:NG) | 18.58 / 22.51 | 16.66 / 20.11 | 12.48 / 16.29 |
| CC_REGULAR (CEMS) | 15.05 / 14.00 | 13.83 / 12.45 | 10.29 / 10.04 |
| CT_PEAKER (CEMS) | 0.91 / 1.76 | 0.49 / 1.57 | 0.16 / 0.60 |
| CT_CHP+CC_CHP (CEMS) | 2.40 / 1.82 | 2.09 / 1.49 | 2.00 / 1.47 |
| hydro (+PS dis) | 8.30 / 7.29 | 7.47 / 6.60 | 6.56 / 6.27 |
| solar | 1.08 / 0.98 | 3.90 / 3.76 | **8.41 / 4.20** |
| battery net | 3.20 / 2.98 | 5.82 / 5.70 | 6.70 / 7.96 |
| demand | 49.03 / 51.62 | 52.77 / 52.64 | 51.98 / 51.49 |

On the aligned window the model **UNDER-imports** the evening
(−0.5/−0.3/−1.4 TWh) — the caiso-97 trim already took the excess out — and
the composition defect is the one caiso-95 named, now cleanly measured: vs
CEMS the model's CC OVER-serves (+581/+757/+137 avg MW, and CHP cogens +317/
+332/+289 — the caiso-101 promotion's known displacement) while **CT_PEAKER
under-serves in every year** (−469/−588/−238 avg MW). The under-price
concentrates where the CT rung should set the price: in the deepest
resid-quartile (Q1, mean resid −36.6/−25.6/−20.2 $/MWh) measured CT runs
1.33/1.19/0.51 GW vs model 0.58/0.31/0.12, model gas sits ~3 GW below the
measured stack, and model imports are AT or ABOVE measured (d_imp
+664/+398/−392 MW) — the model substitutes hub-priced import + committed-CC
MW for reality's expensive-rung CT MW exactly in the tight hours; in Q4 (the
over-priced quartile) the pattern inverts (d_imp −1.5/−0.9/−1.3 GW). The
worst cells are hod 17-18 (2023 hod-18 −13.3; 2025 hod-17 −10.1) and
scarcity months (Jul −23.0/−19.2 in 2023/24; spring 2025 −10 to −11).
Battery timing: 2023/24 evening net ≈ measured (+116/+65 MW); 2025 the
envelope-capped fleet arrives LATE (hod 17-19 d_batnet −1562/−1973/−1108 MW,
hod 20-21 positive) and under-discharges the window (6.70 vs 7.96 TWh).

## 5. THE +1h FRAME DEFECT (found chasing 2025's phantom evening solar)

The 2025 composition row that does not belong: model evening solar **8.41 vs
measured 4.20 TWh** (hod-17 delta +2.3 GW) while 2023/2024 match. The model's
2025 solar hod profile is the measured profile SHIFTED ONE HOUR LATE (model
hod-18 7,832 ≈ measured hod-17 7,770; cross-correlation peaks at lag −1 with
r=0.9997 vs r=0.9525 at lag 0; 2023/2024 peak at lag 0). Root cause:

- `eia_loader._eia_hourly_frame_filled` — the gap-bridging variant used
  whenever a BA-year is short of a clean 8760 — anchors its reconstructed
  UTC clock with `utc_start = utc[0] − (loc[0] − Jan 1)`, treating the
  `Local time` stamp as interval-BEGINNING. The stamps are HOUR-ENDING
  (verified uniform across every per-BA extract: the year's first interval
  is stamped 01:00 / Hour 1), so every reconstructed row lands one position
  late: the whole BA-year is rotated +1h. The strict full-8760 path indexes
  positionally and is correct — which is why only gap-bridged years shift.
- **Blast radius (train years):** CISO 2025 (8751 rows), PJM 2023 (8759),
  MISO 2025 (8753). All other ISO-train-years are strict. For CISO 2025 the
  shift entered the keeper through every filled-frame consumer: the solar %
  wind profiles (via `data/raw/caiso-hsl/caiso_2025_hsl_hourly.parquet`,
  whose delivered component is built from `load_eia_hourly_renewable_gen`),
  the caiso-80 supply-consistent demand artifact
  (`caiso_supply_consistent_demand_2025.csv`), and runtime
  interchange/renewable fallbacks — i.e. the model's entire exogenous 2025
  hourly world ran one hour late against the unrotated LMP actuals it is
  scored on. (The hod-grain import-shape artifacts — caiso-73 firm shape,
  caiso-87/97 corridor windows — ride the separately tz-audited
  `eia-930-interchange` clock mapper and are NOT affected.)
- Second-order contamination (enumerated, not rebuilt this session): the
  caiso-92 measured-offer-surface conditional binning pairs DAM bids with
  filled-frame net-load percentiles (2025 slice mispaired by 1h; pooled
  artifact — a rebuild moves 2023/24 bytes too, so it is its own rule-23
  follow-up), `derive_caiso_solar_shape_band` (scalar percentile thresholds,
  insensitive at that grain), MISO wind shape / PJM DA-virtual + offer
  surfaces (their lanes' follow-ups). GitHub issue filed with the record-
  correction list (PJM-2023 / MISO-2025 keeper legs solved on the rotated
  frame).

**The fix (rule 14 — fix the root cause, never bury it):**
`_eia_hourly_frame_filled` now shifts the hour-ending stamps back one hour
before anchoring (src/market_sim/data/eia_loader.py, comment cites this
FINDING). Verified: CISO-2025 filled frame aligns at lag 0 (r=1.0), CISO-2024
filled ≡ strict byte-identical, PJM-2023 bridges to 8760 with the first hour
intact. Re-derived through the fixed loader (rule 23, citing this defect —
never a residual): `caiso_2025_hsl_hourly.parquet` (now matches the measured
positional profile exactly) and `caiso_supply_consistent_demand_2025.csv`.
The 2023/2024 artifacts of both families are BYTE-IDENTICAL after rebuild
(md5-checked) — the fix touches only what was broken.

## 6. Pre-registered single-delta B-leg (`caiso102_hourfix_B`) — gates committed BEFORE adjudication

`scripts/probes/_caiso102_hourfix_B.py`: the caiso-101 keeper recipe
verbatim (no flag delta, no mechanism); the A/B delta is the §5 fix set only
(loader + the two re-derived 2025 artifacts). 2023-2025 one bundle (rule 16),
sequential, scored `_caiso92_report.py <A> <B>` + `_caiso102_evening_merit.py
<B>` + `_caiso102_charge_channels.py <A> <B>`.

HARD GATES (all must clear):

- **2023 and 2024 solve outputs byte-identical to `caiso102_repro_A`**
  (per-year md5 on the persisted parquet slices) — the fix must not move a
  strict-path year.
- **2025 model solar hod profile aligns with measured at lag 0** (lag-0
  cross-correlation ≥ every ±1-2h lag) — the defect is actually gone in the
  dispatched world.
- **C1 holds 12/12; C7/C8 PASS.**

REPORTED, NOT GATED (two-sided honesty: the rotation realigns demand AND
supply simultaneously, so no directional λ prediction is honest —
pre-registering one would be a guess dressed as a gate): the 2025 ladder
(belly +5.0, evening −3.0, overnight +1.6, hod-17 −10.1), C3a/C3c/C4/C5a,
the 2025 morning/belly charge windows (§3), and the evening composition
(§4). Registered on the dashboard whatever the result (rule 15); promotion
is the owner's call (§7) on no-status-regression + most-structurally-faithful
(rule 1). DOF ledger delta: ZERO parameters (a defect fix; no tunable moved).

## 7. Disposition + owner asks

1. **No conduct mechanism is proposed this session.** The inelastic-charge
   channels are now measured (§1-§3): the volume is allocated day-ahead,
   FMM-committed, AS-positioned — a marginal-cost bid CANNOT carry it
   (caiso-100/101 stands, mechanically explained). Any mechanism must fix
   the ALLOCATION (hold volume, re-price the margin) — but its design should
   start from the post-hourfix residual surface, not the contaminated one:
   the 2025 morning/belly charge geometry changes with the frame fix. The
   re-charter therefore WAITS for the B-leg numbers; the ask is to ratify
   that sequencing.
2. **Keeper swap on the B-leg** if every §6 hard gate clears and no scored
   status regresses: the fix is a pure measured-input integrity correction
   (rule 14) — the A-leg's 2025 solved a world rotated one hour. Owner call.
3. **Cross-ISO record corrections** (the §5 issue): PJM-2023 and MISO-2025
   keeper legs solved on the rotated frame; their registry sidecars need
   ERCOT-65-style correction notes and their lanes a re-solve when next
   touched. The caiso-92 offer-surface 2025 slice re-derive is a named
   rule-23 follow-up (pooled artifact, own gates).
4. Issue #2546 (the $5 fallback literal + pre-caiso-99 record corrections)
   remains OPEN — no owner ruling appeared this session; carried unchanged.

## 8. Do NOT redo

Everything in the caiso-101 handoff's list (battery adder family
volume-refuted; day-threshold CLOSED; WP-3 steam level frozen; caiso-99
envelope not tightened; caiso_storage_as_reservation stays off;
caiso-94/96/97/99/101 mechanisms frozen; no caiso-87 widening; no CC
commitment forcing; no CT_PEAKER floor; no CC offer cuts; no year outside
2023-2025). Plus, new: do not "fix" the caiso-95 §4 import comparison by
re-tuning any import tranche — the offset is a measurement artifact of the
night/day probes' hour-ending hod, and the aligned measurement (§4) shows no
evening import excess to remove; do not derive conduct mechanisms from the
pre-hourfix 2025 charge geometry.

## 9. B-LEG ADJUDICATION (same session, post-pre-registration) — every hard gate CLEARS; PROMOTED to CAISO keeper on the owner's in-session ruling

`caiso102_hourfix_B` solved 2023-2025 one bundle (sequential) on the §5 fix
set. Against the §6 pre-registered gates:

- **2023/2024 byte-identity: PASS.** Per-year dispatch/system/storage/flows
  frames are IDENTICAL to `caiso102_repro_A` (dataframe equality, all four
  families) — the fix moved only the defective year.
- **2025 solar lag-0 alignment: PASS.** Dispatched 2025 solar hod profile vs
  measured: lag 0 r=0.99987, every ±1-2h lag ≤0.947 (was lag −1 r=0.9997).
- **C1 12/12 (free 8/8): PASS. C7 shape: PASS. C8 forced-share: PASS.**

Scored result (vs the caiso-101 keeper = the A-leg): the criteria grid is
IDENTICAL — zero status regression, fail set stays {C3c, C4, C5a} — while
every 2025 ladder block improves: **belly +5.0 → +4.3, evening −3.0 → −1.1,
overnight +1.6 → +1.4** (2023/2024 ladders unchanged by construction);
2025 C1 misses essentially unchanged (CC_REGULAR −4.07→−4.03, CT_PEAKER
−1.96→−2.01 TWh); C3c model tail 19/0/0 unchanged; annual C3a mean ≈
unchanged (+1.76→+1.74 dw) — the gain is intra-day shape, exactly what a
clock rotation predicts. Post-fix 2025 evening composition (§4 re-run):
solar 4.37 vs 4.20 TWh (phantom gone), battery net 8.03 vs 7.96 (the
envelope's evening discharge lands on the measured clock), hod-17 resid
−10.1 → −4.5, Q1 depth −20.2 → −15.4; the surviving evening structure is
the SAME CT-rung composition defect as 2023/2024 (Q1: measured CT 567 MW vs
model 189, model gas −2.1 GW, imports ≈ measured) — the merit-stack lane's
next target, now measured on a clean clock.

**Registered `2026-07-19-caiso-102-hourfix`; PROMOTED to CAISO keeper**
(owner in-session ruling 2026-07-19: "if it's a keeper in your opinion,
promote" — judgment: zero status regression + strictly more structurally
faithful, a rule-14 measured-input integrity fix with zero DOF delta;
supersedes `2026-07-19-caiso-101-chp-steam`, whose sidecar carries the
ERCOT-65-style record-correction note; registry 15/15, no prune).
Determination stays **NOT-YET**, fail set {C3c, C4, C5a(2024 CAVEAT)}.

Post-fix 2025 charge windows (§3 re-measured on the B-leg): morning model
charge 1.35 → 2.57 TWh (measured 2.84), non-belly total 2.87 → 3.64
(measured 3.97), belly 9.32 → 9.37 (measured 8.26), pm-shoulder 1.43 → 1.01
(measured 0.73) — the 2025-only morning gap was mostly the frame defect, and
the surviving all-years inelastic gap is the overnight second cycle (model
0.05 vs measured 0.36 TWh) plus the belly/shoulder over-charge geometry the
§7 allocation re-charter now measures from a clean surface.
