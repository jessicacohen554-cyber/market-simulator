# ERCOT reserve-supply scarcity — Session 1 deliverables + Session 2 handoff (2026-06-22)

**Branch:** `claude/ercot-reserve-supply-scarcity-i3320n` (fresh off `main`).
**Keeper:** run143 (`results/calibration/ercot_dam_2023as_netload`).
**Reads first:** `docs/ercot-run131-lmp-decomposition-2026-06.md` (the monthly-shape
diagnosis + published-ORDC step-1) and
`docs/ercot-outage-sensitivity-middle-ground-2026-06.md` (the local-30 outage band).

This session (1) acquired the **measured exogenous reserve series** the
reserve-supply lever needs as a target, and (2) **re-baselined** the keeper and
the published-ORDC probe on the *current* local-30 outages (run143 and the
published-ORDC numbers in the run131 doc were solved on the stale annual-band
outages — `CC outage GW-days 2906 -> 5997`).

---

## TASK A — measured RTOLCAP / RTORPA acquired (committed)

`scripts/data/fetch_ercot_ordc_reserves.py` (style of `scripts/data/fetch_eia930_hourly.py`)
pulls ERCOT MIS **NP6-905-CD "Historical Real-Time Price Adders by SCED Interval"**
(`reportTypeId=13231`) annual archives `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_<year>` —
**public, no API key** — and curates the reserve / scarcity-adder subset onto the
fleet's non-leap 8760-hour ERCOT-local clock:

`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet` columns:
`rtolcap` (online responsive reserve capability, MW), `rtoffcap`, `rtorpa` (ORDC
on-line price adder, $/MWh), `rtoffpa`, `rtordpa` (reliability-deployment adder),
`rtolhsl`, `prc` (physical responsive capability), `system_lambda`.

These are **exogenous measured series — never fit to LMP.** Validated:

| year | coverage | RTOLCAP mean / p5 / p95 (MW) | RTORPA>$1 h | notes |
|---|---|---|---|---|
| 2023 | 8760/8760 | 13485 / 7427 / 21961 | 294 (Apr/May/Aug) | matches 2023 scarcity |
| 2024 | 8760/8760 | 16679 / 9298 / 25743 | 78 | fleet growth |
| 2025 | 8112/8760 | 19124 / 10975 / 29831 | 15 | Dec tail NaN (see below) |

- **2025 coverage stops in early December**: the ORDC/RTORPA regime ended at the
  **RTC+B go-live (2025-12-05)**, so the 2025 archive's last ~648 hours are
  preserved as **NaN, not fabricated** (matches the run131 doc's "ORDC/RTORPA in
  force to 2025-12-04"). DST spring-forward is the only interpolated hour/yr.
- **PRC quirk (non-blocking):** the 2024 `prc` column has a left-skewed
  distribution (mean 2700 < p5 6494) — a chunk of low/zero intervals in the
  source. RTOLCAP/RTORPA (the targets) are clean; `prc` is context only.

### The measured reserve-supply TARGET (the point of Task A)

The run131 doc localized the residual to the **P90–P99 "moderately scarce" band**
(2024 model P95 27.9 vs actual 61.4) and pointed the next lever at the
reserve-**supply** definition (`ercot_reserve_eligible` counts ~all dispatchable
thermal headroom as reserve, vs ERCOT's ORDC reserve = online responsive
capability **RTOLCAP**). The measured series quantifies that band directly —
join measured RTOLCAP/RTORPA to the actual RTSPP price percentiles:

| year | RTOLCAP median, all hrs | **RTOLCAP median, P90–P99 band** | RTOLCAP median, RTORPA>$1 |
|---|---|---|---|
| 2023 | 12745 MW | **8386 MW** | 6488 MW |
| 2024 | 16197 MW | **9872 MW** | 7235 MW |
| 2025 | 18551 MW | **11986 MW** | 7671 MW |

**Reading:** real moderate-scarcity pricing (P90–P99) happens when online reserve
tightens to **~8–12 GW, ~60–65% of the typical level**, and the ORDC adder only
fires at RTOLCAP ~6.5–8 GW. The model is hollow in that band because its
reserve-**supply** over-count keeps modeled reserves abundant — modeled reserve
never tightens into the ~8–12 GW range where ERCOT's (already-published, step-1)
curve prices the P90–P99 hours. This is the exogenous physical target for
Session 2: re-scope `ercot_reserve_eligible` (online vs offline/slow-start) so the
modeled reserve supply tracks measured RTOLCAP, **not a fit to the price**.

### TASK A part 2 — the two long-missing files: NOT publicly reachable

Both the **60-Day DAM Load Resource AWARDS** (verifying the 884 MW load credit)
and the **Oct-2023 (10-02..11-01) Gen Resource Data disclosure** live in the
60-Day DAM/SCED Disclosure reports (`reportTypeId=13051`/`13052`). Their **public
MIS rolling archive only retains back to 2024-03-24** — neither 2023 file is
reachable without ERCOT's **authenticated API archive** (`api.ercot.com`, requires
an Ocp-Apim subscription key, not provisioned in this environment). This matches
the task's "if reachable" qualifier. The 884 MW load credit was already
cross-derived in run139 (from the in-repo Gen Resource Data + ASPLANNP433), so
this is a lost cross-check, not a blocker.

---

## TASK B — re-baseline on the current local-30 outages

Both solves re-run the run143 keeper recipe byte-faithfully (via
`scripts/probes/_keeper_2023as_run.py`), changing only the named lever; the
outage CSVs on disk are now the local-30 band. Co-opt LP ~3–4 min/yr, run
SEQUENTIALLY (OOM at 4 cores/16 GB if parallel).

### run143_redo — the corrected keeper baseline (registered, PROBE)

`results/calibration/run143_redo`, registered
`2026-06-22-run143-redo-rebaseline-local30`. Demand-wtd avg / hourly-MAE / h>200 /
h>500 vs actual RTSPP:

| year | run143_redo | stale run143 (run131 doc) | actual |
|---|---|---|---|
| 2023 | 35.2 / 27.9 / 89 / 51 | 36.5 / – / 104 / 56 | 48.4 / 181 / 104 |
| 2024 | 25.4 / 15.0 / 33 / 23 | 23.2 / – / 22 / 16 | 26.8 / 53 / 16 |
| 2025 | 32.5 / 11.6 / 1 / 0 | 31.4 / – / 1 / 0 | 32.5 / 31 / 3 |

P90–P99 band still hollow (2024 P95 29.6 vs 61.4; 2025 49.7 vs 76.7). The
local-30 outages nudge 2024's **deep tail to a mild over-fire** (h>500 23 vs
actual 16).

### ordc_pub2 — published-ORDC curve, re-baselined (registered, PROBE)

`results/calibration/ordc_pub2`, registered `2026-06-22-ordc-pub2-published-ordc`.
run143_redo + ONE change: the co-opt ORDC reserve-demand curve uses ERCOT's
published NP6-576-ER seasonal µ/σ (`KEEPER_ORDC_TABLE`) instead of the neutral
µ=0 fallback. Demand-wtd avg / h>200 / h>500 vs actual:

| year | ordc_pub2 | run143_redo | actual |
|---|---|---|---|
| 2023 | **42.9** / 135 / 78 | 35.2 / 89 / 51 | 48.4 / 181 / 104 |
| 2024 | 28.0 / 44 / **31** | 25.4 / 33 / 23 | 26.8 / 53 / **16** |
| 2025 | 32.6 / 3 / 1 | 32.5 / 1 / 0 | 32.5 / 31 / 3 |

The published curve lifts **all three years** toward actual (closing most of
2023's undershoot) — the structural non-fit test. But it **over-fires the 2024
deep tail** (h>500 31 vs actual 16) and the **P90–P99 band stays hollow** (2024
P95 unchanged 29.6 vs actual 61.4) — confirming the moderate band is a
reserve-*supply* problem the demand curve cannot reach.

### Keeper-readiness call (the task's deliverable)

**Published-ORDC is keeper-ready on VOLUMES, NOT yet on PRICE SHAPE.**

- **Volume re-gate: CLEAN.** `calibration_verdict.py` gives C1 fuel-mix and C2
  family FAILs **byte-identical** between run143_redo and ordc_pub2 (2024
  CC_REGULAR +10.0%, ST_GAS −6.72 TWh, CT_PEAKER −3.17, coal −2.7%), and these
  same C1 classes FAIL in the registered run143 keeper too. The curve is
  **price-only** (`DAM−BASE ≈ 0`); it introduces **no new volume regressions**.
  The operating-shape / ST_GAS / CT_PEAKER FAILs are **pre-existing, not new** —
  confirmed.
- **Price shape: not yet.** On the re-baselined numbers the curve over-fires the
  2024 deep tail and leaves the P90–P99 band hollow. So **do not adopt it
  standalone**; adopt it **paired with the reserve-supply lever** (Session 2),
  which reshapes *where* the curve bites — lifting the moderate band and taming
  the deep-tail over-fire.

### Why 2024 is "off" for CC_REGULAR (asked) — a merit-order swap, not the curve

2024 grid-delivered TWh: **CC_REGULAR model 157.8 vs actual 145.4 (+9.9%)**,
**ST_GAS 11.4 vs 18.1 (−37%)**, **CT_PEAKER 4.2 vs 8.2 (−39%)**. The CC over-run
(~+12 TWh) almost exactly *replaces* the ST_GAS+CT_PEAKER under-run (~−11 TWh) —
a **within-gas merit-order substitution**, worst in the shoulder (Apr +24pp, May
+22pp, Oct +19pp). The energy-only LP runs cheap combined-cycle when ERCOT
actually ran steam-gas + peakers — because (a) CC offers sit too cheap relative
to ST_GAS/CT_PEAKER (offer-curve calibration) and (b) the energy-only dispatch
can't see the **local-reliability / AS commitments** that keep real ST_GAS and
peakers online at part-load. It is an **operating-shape / offer-curve MODEL MISS**,
independent of the reserve curve (unchanged by the price-only published-ORDC
lever) and the same ST_GAS/CT_PEAKER under-dispatch seen in all 3 years. It is
**not** a reserve-supply-lever target — flag it as a separate offer-curve /
energy-only-limitation track (the rubric's documented CT_PEAKER limitation class).


### Pre-existing gate FAILs (the VOLUME re-gate)

`scripts/calibration_verdict.py` on run143_redo **and** on the registered run143
keeper FAIL the **same C1 fuel-mix classes** — these are PRE-EXISTING, not
introduced by the outage re-baseline or the reserve curve:

| criterion | run143_redo | registered run143 keeper |
|---|---|---|
| C1 ST_GAS | −4 to −7 TWh (all yrs) | −6 to −9 TWh (all yrs) |
| C1 CT_PEAKER | −2 to −3 TWh (all yrs) | −3 to −4 TWh (all yrs) |
| C1 CC_REGULAR | +5 to +10% (2024/25) | +6 to +12% (2024/25) |
| C2 volume | 2024 coal −2.7% | 2023 gas −3.1%, coal +5.4% |

The local-30 re-baseline **cleared 2023's C2** (gas/coal volume) that the keeper
failed. The ST_GAS/CT_PEAKER under-dispatch + CC_REGULAR over-dispatch is the
long-standing ERCOT operating-shape miss (offer-curve/merit-order), independent
of the reserve curve.

---

## Session 2 — the reserve-supply lever (next, GROUNDED, GATED)

1. **The target is measured (Task A):** modeled reserve supply should track
   RTOLCAP — mean ~13.5/16.7/19.1 GW, tightening to ~8–12 GW in the P90–P99 band.
   Re-scope `ercot_reserve_eligible` (`results/scarcity.py`) to **online
   responsive** capability (exclude offline/slow-start headroom), an exogenous
   physical/rule distinction, **not a price fit**.
2. **Pair with the published-ORDC curve** (step-1, `--ordc-lolp-params-path` /
   `KEEPER_ORDC_TABLE`), which is the grounded reserve-*demand* curve. The
   supply re-scope makes modeled reserve actually reach the band the published
   curve prices.
3. **Gate** on the DURATION CURVE + scarcity-hour frequency + sensitivity across
   all 3 years (NOT monthly-shape RMSE), and **re-confirm the volume gate**: the
   reserve curve is price-only (`DAM−BASE ≈ 0`), so C1/C2 must stay the
   pre-existing run143_redo FAILs above (ST_GAS/CT_PEAKER/CC_REGULAR), not regress
   further. Reproduce the measured-target join with the snippet in the commit /
   `scripts/data/fetch_ercot_ordc_reserves.py` validation output.
### The 2023 undershoot — newly PARTLY unblocked by the measured adder series

2024/25 land; **2023 is the lone year that materially undershoots** (ordc_pub2
42.9 vs actual 48.4). Decomposing it against the measured series (no fit):

- The 2023 gap is **87% concentrated in the 181 actual>$200 hours** (2% of the
  year). The body and shoulder are fine. So 2023 is a **deep-tail** problem, the
  market-design signature.
- In those 181 hours: actual RTSPP mean **$1101** = implied energy **$1016** +
  measured ORDC/RDP adder **$85**. The model makes **$878**. So the model is
  ~$223/h short, split: **~$85 the measured adder it under-fires** + **~$138 the
  energy-scarcity base** (its fleet isn't tight enough — the reserve-supply
  over-count again).
- 2023's differing market design *is* the cause: **ECRS launched 2023-06-10**
  (~2 GW new product) and ERCOT ran **conservative real-time reliability
  deployments** through H2-2023 (the IMM's ~$12B out-of-market estimate). That
  conservatism shows up as the **measured RTORDPA** (reliability-deployment price
  adder) — demand-wtd only ~$1/yr but **~$85/h in the tail**.

**The unblock:** the run131 doc parked a regime-gated 2023 out-of-market adder
because it "needs a defensible *measured* MW/$-withheld source (IMM withholding,
egress-blocked)." **That source is now in-repo** — `rtordpa` (and `rtorpa`,
`rtoffpa`) in `data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet` is ERCOT's
*published*, hour-resolved reliability-deployment adder: exogenous, not a fit. A
**regime-gated 2023 overlay of the measured RTORDPA onto the model energy price**
(stripping the model's own ORDC adder to avoid double-count) is now a grounded
lever. Caveat from the decomposition: it closes only **~$85 of the ~$223 tail
gap** — the larger ~$138 is the energy-scarcity base, i.e. the **same
reserve-supply lever**. So the 2023 plan is: reserve-supply lever first (lifts the
energy base in 2023's tail *and* the P90–P99 band in all years), then the measured
RTORDPA overlay closes the residual administrative slice — both measured, neither
a fit. This **shrinks** the "un-sourceable ~42–47% out-of-market" residual the
run131 doc described.

### Out of scope / still blocked

The 2024-Jan winter-storm tail (model $22/3 h vs actual $44/19 h) remains
un-modelable by an ORDC/LOLP availability curve; the global storage-AS credit
stays rejected (run131 doc). The 2023 administrative slice is now *partly*
sourceable via measured RTORDPA (above) rather than fully blocked.
