# FINDING — ercot-163 Phase 0: the "~8 GW cheap CC offline block" DOES NOT EXIST. ERCOT's CC fleet was 96.4 % committed and 98.0 % loaded at the gap hours; the block was a 60-Day-DAM *day-ahead status* artifact, 99.2 % of which was telemetered ONLINE and generating in real time. NO commitment-state mechanism is chartered.

**Session ercot-163, 2026-08-04. NO LP, no solve, no mechanism armed, no
`ScenarioConfig` field added, no matrix cell verdict minted, keeper UNCHANGED
(`2026-08-03-ercot158-pool-arm`; NOT-YET, open gates C3a 2023-only, C3b
2023-only, C3c, C7 2023-lignite cv-leg).** The ERCOT-162 successor, Phase 0: the
storage OFFER-PRICE lane closed `R` because *"the model's crossing never runs
deep into the tranches — the cheap CC OFFLINE block absorbs the load and caps
the price"*, so the chartered object (DIAGNOSIS-ercot151 §3 / ERCOT-152,
upheld at ERCOT-158) was the **commitment state of that block**. This session
measured it on the delivery-2023 SCED corpus and found the block is not there.

Probes (both no-LP, both on committed data):

- `scripts/probes/ercot163_cc_commitment_state_census.py` →
  `results/calibration/_ercot163_cc_commitment.json` — the RT capability-state
  census of the CC and CT fleets over the delivery-2023 SCED corpus (315
  shards) at four hour sets, against the keeper's own reconstructed CC
  availability / dispatch / bid ladder (`reconstruct_bundle_fleet`, the
  ERCOT-161 machinery, fidelity flags asserted).
- `scripts/probes/ercot163_dam_config_collapse.py` →
  `results/calibration/_ercot163_dam_config_collapse.json` — the 60-Day DAM
  block ERCOT-151 measured, re-cut at train grain and **joined train-by-train
  to the RT telemetry at the same hours**.

## 0. Verdict

1. **The chartered premise is refuted, at Phase 0, without a solve.** At the
   committed top-100 gap hours the whole ERCOT CC fleet held **0.020 GW** of
   offline-startable (OFFQS/OFFNS) registered capability — 20 MW, against the
   ~8–10 GW the lane was chartered on — and its above-LSL SCED2 offer was
   **2.6 MW at $77.5–85.5**, with **zero MW above $100**.
2. **ERCOT's CC fleet was not "offline and cheap"; it was committed and
   flat out.** Committed share of registered capability **96.4 %**, online
   loading **98.0 %** (Base Point 29.46 GW against 30.07 GW of telemetered
   online HSL), leaving **0.32 GW** of online spare of which only 0.028 GW
   offered ≥ $500.
3. **The ERCOT-151 §0.2/§0.4 number is a DAM *status* artifact, twice over,
   and the second half is the fatal one.** (a) At resource-name grain the OFF
   block reads **48.9 GW** because a CC train submits one DAM row per
   configuration (**4.3 configurations/train**); train-collapsed it is
   **14.1 GW**. (b) Of the 13.42 GW that survives as wholly-offline *in the
   day-ahead disclosure*, **98.6 % (12.95 GW) was telemetered ONLINE in real
   time and 12.47 GW of it was generating** at those very hours. Genuinely
   idle in RT: **0.087 GW**. At the ERCOT-163 gap hours the same join gives
   **99.2 % online, 13.53 GW dispatched, 0.035 GW idle**. The DAM
   `Resource Status` is a *day-ahead commitment* status; ERCOT's merchant CC
   fleet self-commits into real time, so it says nothing about RT availability
   at an RT tail hour.
4. **The charter condition is therefore NOT met and no mechanism is
   chartered.** The prompt's condition was *"IF a real commitment-state gap is
   measured"*. There is none on the CC fleet. A mechanism that gated "cheap CC
   offline capacity out of the merit order where reality had it
   committed/unavailable" would, on this measurement, remove capacity ERCOT had
   **online and running** — a haircut with no measured referent, forbidden by
   rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]`.
5. **The instrument is not blind — it finds the pool where the pool is.** The
   same census run on the CT fleet at the same hours returns a real
   offline-startable population: **0.89 GW registered / 0.76 GW HSL**, offering
   **67 MW above LSL at p50 $891.5** with 36 MW ≥ $500. That is the ERCOT-88
   fast-start pool, already armed and already measured inert at the tail
   (ERCOT-158). CC has no analogue; ERCOT-152's "CC OFFQS/OFFNS is ~0 MW"
   reading on four sample-day extracts is **confirmed on the full-year
   corpus** and can be closed.
6. **What is left is real but is a different object, an order of magnitude
   smaller, and NOT commitment.** The model's CC *dispatch* matches reality to
   **+0.30 GW** (30.04 vs 29.73 GW, ONTEST and startup ramps included). What differs is *headroom*:
   the model leaves **3.07 GW** of CC undispatched (0.72 GW of it bid ≤ $200,
   2.04 GW ≤ $500) where the market had **0.35 GW** of non-dispatched CC
   capability in total. It is named in §4 and handed forward **unchartered**,
   because it is an availability/fleet-scope quantity that this session's two
   probes cannot attribute — and the lesson of §3 is precisely that an
   unattributed aggregate must not be handed forward as a mechanism premise.

## 1. The measurement — reality's CC capability state at the gap hours

Hour set: the committed top-100 2023 gap hours
(`results/calibration/_ercot161_wall_phase0.json`; 98.3 % of the load-weighted
residual, model $441.27 vs actual $1,487.84, λ $1,470.16; 83 of 100 in Aug/Sep,
all in h12–19). 400 SCED intervals. Every ERCOT CC resource
(`CCGT90`/`CCLE90`) is given a fixed capability reference `cap_ref` = its p98
telemetered HSL over delivery-2023 **at train grain** (configuration aliases
collapsed on the trailing `_<config>` segment — see §3), so the accounting has a
fixed denominator and a resource that stops telemetering lands in an explicit
`ABSENT` state rather than being silently dropped.

| CC capability state | registered GW (`cap_ref`) | telemetered HSL GW | Base Point GW |
|---|---|---|---|
| ONLINE (ON/ONREG/ONOS/ONRUC/ONHOLD/…) | **33.998** | **30.065** | **29.460** |
| ONTEST | 0.355 | 0.296 | 0.264 |
| **OFFLINE_STARTABLE (OFFQS/OFFNS)** | **0.020** | **0.018** | 0.000 |
| OFFLINE_OTHER (plain OFF) | 0.034 | 0.017 | 0.000 |
| OUT | 0.791 | 0.366 | 0.000 |
| TRANSITION (STARTUP/SHUTDOWN) | 0.034 | 0.017 | 0.010 |
| OTHER | 0.023 | 0.016 | 0.000 |
| ABSENT (registered, not telemetering) | 0.005 | — | — |
| **fleet** | **35.260** | **30.805** | **29.734** |

- **committed share of registered capability 96.4 %**; 70 trains present.
- **online loading 98.0 %** (Base Point / online HSL); online spare
  (HASL − Base Point) **0.321 GW**, ladder p50 **$32.5**, p90 $417.5 — 0.269 GW
  of it below $100 and only **0.028 GW ≥ $500**.
- **the offline-startable increment**: 2.6 MW of above-LSL, HASL-capped SCED2
  offer, p10–p99 **$77.5–85.5**, entirely inside the $0–100 band.

**The CT control, same hours, same construction.** Committed share **85.2 %**;
OFFLINE_STARTABLE **0.891 GW** registered / 0.761 GW HSL; above-LSL offer
**67.3 MW**, p50 **$891.5**, p90 $1,153.5, 36 MW ≥ $500. The census resolves an
offline startable pool at scarcity prices where one exists. It is CT-only.

**Ordinary-hour controls (the ERCOT-159 re-pointed question, measured on the
same instrument).** CC committed share runs 97.4 % at the top net-load bin's
non-gap hours, 94.0 % over Jun–Sep h13–19 non-gap, and 72.7 % over the whole
year — so ERCOT *does* cycle CC off, and when it does the capacity goes to
plain **OFF**, not OFFQS/OFFNS (all-hours: OFFLINE_OTHER 4.08 GW registered vs
OFFLINE_STARTABLE 0.14 GW). ERCOT's CC fleet is essentially never
intra-hour-startable, which is what its own physics says (min-down 4–12 h). The
offline-startable CC ladder never leaves the $0–100 band in any hour set.

## 2. The model at the same hours

Reconstructed from the keeper bundle `ercot158_poolarm_B` (fleet/offer arrays
only, no LP; P1 bids composed exactly as `run_calibration` composes them), with
dispatch read from the keeper's committed `class_hourly_2023.parquet`. The
undispatched block is taken cheapest-first inside the class.

| CC (CC_REGULAR + CC_CHP) | gap | bin6 non-gap | summer aft. non-gap | all |
|---|---|---|---|---|
| available GW | 33.109 | 33.748 | 32.568 | 29.330 |
| dispatched GW | 30.038 | 30.014 | 27.340 | 19.238 |
| **undispatched GW** | **3.072** | 3.735 | 5.228 | 10.092 |
| utilisation | 0.906 | 0.889 | 0.839 | 0.654 |
| undispatched ≤ $200 GW | 0.723 | 1.246 | 3.374 | 9.118 |
| undispatched ≤ $500 GW | 2.040 | 2.653 | 4.405 | 9.472 |
| marginal CC bid p50 | $134.33 | $83.80 | $48.11 | $25.00 |

Side by side at the gap hours:

| | model | reality |
|---|---|---|
| CC dispatch | 30.04 GW | 29.73 GW |
| CC capacity not dispatched | **3.07 GW** | **0.35 GW** (0.32 online spare + 0.035 offline) |
| of that, priced ≤ $200 | 0.72 GW | 0.0026 GW (the entire offline-startable offer, at $77–86) |
| of that, priced ≤ $500 | 2.04 GW | ≈ 0.30 GW (online spare below $500) |

The model's CC **output** is right to +0.30 GW. Its **depth** is ~9× the
market's. That is the whole of the CC-side residual, and it is 2.7 GW — not the
8–10 GW the lane carried forward.

*(Caveat, disclosed: the cheapest-first fill ignores min-gen forcing of
individual expensive rows, so the ≤ $200 / ≤ $500 splits carry a small
attribution error; the totals do not.)*

## 3. Where the "~8 GW" came from — the ERCOT-151 correction

`scripts/probes/ercot151_offline_phase0.py` + `…_phase0b.py` summed the 60-Day
**DAM** Gen Resource rows at the 91 missed 2023 >$300 hours with
`Resource Status ∈ {OFF, OFFQS, OFFNS}`. `ercot163_dam_config_collapse.py`
re-reads those same rows at those same hour keys:

| CC, ERCOT-151's 91 missed hours | GW |
|---|---|
| resource-name grain, OFF-status HSL (its raw leg) | **48.876** |
| train grain (configs collapsed; 4.3 configs/train) | **14.102** |
| — of which config-uprate headroom of a running train | 0.679 |
| — of which wholly-offline trains | **13.423** |
| **of the 13.423 GW: RT-telemetered ONLINE** | **13.229 (98.6 %)** |
| — RT Base Point of that block | **12.682** |
| **RT genuinely idle (OFFQS/OFFNS/OFF/absent)** | **0.087** |

At the ERCOT-163 top-100 gap hours the same join reads 14.032 GW → **99.2 %
RT-online, 13.531 GW dispatched, 0.035 GW idle**. The DAM/RT cross-tab is
2,151 train-hours of `DAM_OFF × RT_ONLINE` against 42 of
`DAM_OFF × RT_OFFLINE_STARTABLE`.

Two independent defects, both now measured:

1. **Configuration inflation (3.5×).** A combined-cycle train submits one DAM
   row per configuration and only one can be the operating point, so every
   other configuration of a *running* train carries `Resource Status = OFF`
   with its own full HSL. ERCOT-151's `_site()` collapse mitigated but did not
   fix this: it collapses across *trains at a site* and takes the **max** HSL
   among ON rows rather than the sum, which understates ON at any multi-train
   site and inflates the OFF increment. This is direct, quantified evidence for
   **open owner ruling #9** (the deriver `_site()` cross-train collapse).
2. **Basis (the fatal one).** Even correctly collapsed, a DAM status is a
   *day-ahead* commitment, and ERCOT's merchant CC fleet self-commits into real
   time. Using it as evidence of the RT commitment state at an RT scarcity hour
   inverts the answer: the capacity the DAM shows as OFF is the capacity that
   is, in real time, ON.

**ERCOT-152 was right and its finding should have closed the lane.** Its
committed-data census already read "CC OFFQS/OFFNS ≈ 0 MW in all four
extracts"; the narrative kept the "~8 GW cheap CC offline block" alive from the
DAM leg alongside it. The full-year corpus now says the same thing at 500×
better coverage.

## 4. What is left — NAMED, NOT CHARTERED

The residual CC object is **~2.7 GW of merit-order headroom the market did not
have**, and its provenance is *capability*, not commitment. The fleet-grain
arithmetic:

| | model | ERCOT SCED CC universe |
|---|---|---|
| registered capability | 38.83 GW nameplate (CC_REGULAR 33.12 + CC_CHP 5.71) | **35.26 GW** (train-grain p98 HSL) |
| available / telemetered at the gap hours | 33.11 GW | 30.81 GW (all states) |

The model's CC classes carry ~10 % more registered capability than ERCOT's SCED
CC universe holds, at a comparable derate. The obvious candidate is
cogeneration behind private-use networks — capacity that is physically real,
generates, and is in CAMPD/EIA-923, but never offers its capability into SCED
and therefore is not merit-order depth. **That is a hypothesis, not a result**:
the accepted DAM-site → EIA-plant crosswalk covers only **12 CC plants /
6.6 GW** of the fleet, so neither probe here can attribute the 3.6 GW to
specific units.

The successor's **first step is therefore identification, not a mechanism**:
extend the reviewed SCED-train ↔ model-unit crosswalk over the CC fleet and
measure, per unit, how much model CC capability has no SCED counterpart. Only
if that lands does a mechanism question arise, and it would be a **rule-14
`[R-ACCURATE]` fleet-scope correction to the existing availability channel**
(`ercot_thermal_dam_availability_*`, which already owns "how much CC capability
the model credits" under rule 19 `[R-ONE-MECH]`) — **not** a new commitment
gate, and **not** an aggregate cap (`energy_online_capability_cap` is `R`,
ERCOT-159, and its over-fire diagnosis stands).

Explicitly **not** proposed, and **not** to be re-derived from this finding:

- Any per-hour cap of CC availability at its RT-telemetered HSL. That is the
  rule-13 `[R-MEASURED]`-forbidden form ERCOT-159's Phase 0 already named
  (its raw-telemetry leg bound 3,838 hours, 3,615 of them at actual < $150).
- Any re-pricing of CC. ERCOT-152 measured it a no-op; ERCOT-158 upheld it.
- The storage offer-price lane (`ercot_storage_rt_offer_surface` `R`,
  ERCOT-162), the ercot41/43/106/108 envelope family,
  `ercot_shoulder_online_span`, the West/Panhandle topology split,
  `ercot_ordc_only_scarcity`, the offer LEVEL program (gas walls EXONERATED).

## 5. Governance

- **No mechanism tested ⇒ no matrix cell verdict minted** (rule 28(b)). The
  §5.1 queue and the two ERCOT cell notes that carried the refuted premise
  (`ercot_faststart_pool_offer`, `ercot_storage_rt_offer_surface`) are
  corrected in this session; `docs/DIAGNOSIS-ercot151-offline-increment-phase0-2026-08-02.md`
  carries a correction banner over its §0.2/§0.4.
- **No run produced ⇒ no dashboard registration** (rule 15; the
  ERCOT-147/152/161 no-LP pattern). Keeper UNCHANGED.
- **Rule 22**: delivery-2023 only — training span, no holdout year touched.
- **Rule 25**: ERCOT-scoped throughout; no other ISO's cell or artifact read
  or written.
- **Scope fence honoured** as listed in §4.
- The probes add no `ScenarioConfig` field and no solve-affecting code
  (rule 28(c) not engaged).

**Next shorthand: ercot-164.**
