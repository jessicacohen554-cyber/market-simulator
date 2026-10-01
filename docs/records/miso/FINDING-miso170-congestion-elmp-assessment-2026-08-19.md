# FINDING miso-170 — the congestion and ELMP hypotheses for the 2025 miss, measured against the committed record

**Session miso-170, 2026-08-19. NO LP SPENT for this assessment; every number
below is computed from committed artifacts** (the keeper's hourly sidecars, the
staged hub LMP/MCC/MLC components, the zone-resolved actuals) **or quoted from
the adjudicated record with citation. No cell verdict is minted — no mechanism
was tested.** The companion lay-up membership A/B chartered in
`PREREG-miso170-stgas-floor-membership-2026-08-19.md` is a separate object.

## 0. The two owner hypotheses under examination (2026-08-19, verbatim intent)

1. *"In 2025, real-time transmission congestion costs inside MISO spiked 23 %
   to $2.2 billion. MISO frequently bumped against regional flowgates,
   triggering transmission penalty factors that aggressively elevate local
   LMPs."* — is missing flowgate/penalty-factor congestion a cause of the
   C3a-2025 −12.4 % miss?
2. *"MISO settles its real-time market using an Ex-Post pricing mechanism
   (ELMP) … allows fast-ramping, inflexible, or online emergency resources
   (which would normally have a binary constraint preventing them from being
   mathematically 'marginal') to retroactively set the LMP."* — is a missing
   ELMP premium a cause?

## 1. Hypothesis 1 (congestion) — REFUTED AS A C3a EXPLANATION on the scored target's own components; the real phenomenon is dispersion the target deliberately excludes

**1a. What the C3a target actually is.** MISO's system scoring reference
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet` is the
**INDIANA.HUB** series (the standing composition choice,
`scripts/data/derive_miso_hub_lmp.py::SYSTEM_HUB`), load-weighted over time by
system load (`rt_lw`, calibration_verdict.py:83).

**1b. The target's own congestion component did not move in 2025.** From the
committed hub component staging (`data/raw/lmp-data/MISO/miso_hub_lmp_*_rt.csv.gz`,
LMP/MCC/MLC rows verbatim from MISO's daily market reports), annual simple
means, $/MWh:

| year | INDIANA.HUB LMP | its MCC | its MLC |
|---|---|---|---|
| 2023 | 31.79 | **+1.75** | +0.71 |
| 2024 | 30.79 | **+1.55** | +0.77 |
| 2025 | 42.85 | **+1.56** | +0.88 |

The scored hub's LMP rose **+$11.06** from 2023 to 2025 while its congestion
component moved **−$0.19**. The 2025 rise at the C3a target is, to the dollar,
an ENERGY-component event. A congestion mechanism of any fidelity — flowgates,
penalty factors, nodal granularity — cannot close a gap whose target carries no
congestion growth.

**1c. Where the $2.2 B actually shows up: dispersion, mostly on the generator
side, and below the model's grain.** The same staging shows the 8-hub mean MCC
falling −0.82 → −1.40 → **−2.01** $/MWh (2023→2025), driven by the South/wind
hubs (ARKANSAS −6.50, MS −6.32, TEXAS −4.28 in 2025) while Indiana/Michigan
hold ≈+1.6. The 2025 congestion spike widened hub-to-hub SPREADS (miso-156 T-21:
cross-zone spread >$1/MWh in 21.1/24.4/**54.2 %** of hours) — it did not lift
the benchmark hub. This is consistent with the adjudicated anatomy of MISO
congestion in this repo (`docs/multi-iso/miso-zonal-gate2.md`): binding
flowgates discount the export-constrained wind belt against the load centers.

**1d. The load-weighting premium the model misses is TEMPORAL, not spatial.**
Measured this session: actual `rt_lw − rt` = 1.06 / 1.50 / **2.61** $/MWh
(2023/24/25) vs model 0.61 / 0.90 / 0.99 — the model misses $1.62/MWh of the
2025 premium. Splitting it: since the target is ONE hourly series, the premium
is by construction the price-load covariance over TIME — the miso-167 summer
scarcity-slope object (4.32× too-flat stack), not congestion. The within-hour
cross-zone (spatial) premium, computed on the zone-resolved actuals under the
model's own demand weights, is **+0.12 $/MWh actual vs +0.54 model in 2025**
(−0.05/+0.07 vs +0.07/+0.20 in 2023/24): at the model's zonal grain the model
already produces MORE load-weighted spatial premium than the hub actuals carry.

**1e. The penalty factors the hypothesis names are already in the model where
they are representable.** MISO's Transmission Constraint Demand Curves ARE the
model's RDT representation (cell `rdt_tcdc` = **K**, keeper-armed): the $40 /
$500 TCDC steps plus the $200 RPE adder as priced parallel tiers on the
JOA-cited 3,000/2,500 MW corridor at the published 0.92 derate
(`constants.py:4159-4213`, `model/interchange/miso.py::apply_miso_rdt_tcdc`).
Below zone grain, the flowgate object is ADJUDICATED CLOSED AS FUNDAMENTAL, not
merely missing: miso-78 (five representation candidates refuted, the missing
object being the shift-factor set nothing publishes), confirmed by miso-79's
LBA-grain measurement that **88–99.7 % of MISO's measured internal congestion
mass is intra-LBA** — an optimally-split ~12-zone model would capture only
~1.9–3.8 % of it. `internal_congestion_split` is cell **G** ("NO-BUILD is
fundamental. Do not re-open without new sub-zonal data intake"), and nothing in
the 2025 SOM changes the reason: the coefficients are still unpublished.

**1f. What survives of the hypothesis — two named, bounded leads (not
chartered here):**
- `measured_interface_limits` is **U** — genuinely untested at MISO, the
  natural home of miso-78 RO-1's "boundary-aligned interface limits" branch
  (published flowgate limits mapped to the six zone boundaries). Bounded by
  1c–1d: at the scored target it can move ≈nothing annual; its honest prize is
  zonal-basis fidelity (the gate-2 spread-duration FAIL), not C3a.
- The RPE **STR-scarcity channel** (binding *without* an RDT violation) is a
  documented representation gap (`scenarios.py` miso_rpe_pricing note: the
  measured Summer-2025 Midwest–South spread $9.31/MWh is under-stated) — a
  South-DISCOUNT object; widening separation prices the 27 % South load share
  DOWN, so it cuts against the level miss, not toward it.
- The one congestion-family lead pointing the right way in the scarce hours is
  miso-167 §2(d): the model **over-imports +1.33 GW precisely in the 47
  scarcity hours** (disclosed, unlevered — the seam envelope class; rule 23
  bounds any availability-ceiling re-derive).

**Bottom line 1:** the congestion story is real in MISO's settlement data and
in the model's zonal-basis weaknesses, but it is **not the C3a-2025 miss**: the
scored benchmark hub carries flat congestion content through the failing year,
the missing load-weight premium is temporal, and the sub-zonal object is
data-blocked at representation by adjudication that still holds. If the owner
wants the model judged on congestion-inclusive load pricing, that is a
BENCHMARK-COMPOSITION decision (a load-zone composite target instead of
INDIANA.HUB — MISO publishes load-zone ex-post LMPs the staging does not carry),
not a mechanism the current target can reward.

## 2. Hypothesis 2 (ELMP / ex-post premium) — the representable half is ALREADY IN; the residue is the adjudicated RT-only model-class limit, now measured at its exact size

**2a. What ELMP is, on the record:** a pricing-only convex-hull-approximation
relaxation (binaries → [0,1]) on single-interval dispatch that lets fast-start
(and, in scarcity, offline fast-start) units set price
(`docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md` §2).

**2b. The model's dispatch LP is already the relaxation ELMP approximates.**
There are no binary constraints anywhere (pure LP, P1 scored): a fast-start or
inflexible unit that is marginal in the LP DOES set the dual — the very thing
the hypothesis says a "standard deterministic LP" forbids. The specific ELMP
ingredients are each represented and adjudicated:
- **Amortized commitment costs in price:** the P1 bid-cost pass +
  `tranche_startup_amortization` (cell K, MISO-55) — registered in
  `_MISO_OFFER_CURVE`'s own comment as "the representation of MISO's ELMP
  fast-start pricing," worth a measured **$4.15–4.74/MWh at the top-200
  hours** (PREREG-miso155 §8).
- **Emergency/max-gen resources price-setting:** `maxgen_emergency_tier_pricing`
  = **K** (miso-70).
- **Reserve scarcity co-pricing on the synchronised product:**
  `miso_reserve_online_gated` = **K** as of miso-169, with the measured cleared
  requirement and the published Schedule-28 $65/$98 demand curve.
- **Residual markup room:** none — Potomac's measured MISO price-cost mark-up
  is **+3.0 % (2023) / −2.5 % (2024)** with a de-minimis withholding output
  gap: the real market clears essentially at cost (miso-155; the miso-151
  measured-offer-surface rejection measured real units bidding nearly FLAT
  within their own range, sign-reversed ~25× against the offer-surface prior).

**2c. What an ex-post premium could add is the RT tail — and that is the
measured RT-only residue the lane closed as model-class, at exactly this
size.** miso-167 §5, the 47 summer-2025 scarcity hours split on DA>$150:
- **DA-foreseen half** (20 h, mean load 109.1 GW): MISO's own deterministic,
  foresighted DA engine priced $254 where ours priced $103 → REACHABLE, and
  the miso-169 mechanism landed **+$10.12 in exactly these hours** ($0.00 in
  the RT-only half; K-5 "textbook"). The open owner lever here is the RHO_CLIP
  question (re-solve at the CAMPD-measured ρ = 0.1764 instead of the 0.5
  floor — one `replay_keeper --set`; binds strictly tighter).
- **RT-only half** (27 h, mean load 98.7 GW, DA $80.55 → RT $428.09): MISO's
  own DA market — same model class as ours, with full UC and network — did not
  see these hours either. In the 88 actual 2025 RT>$200 hours the keeper holds
  ≥11 GW of deliverable reserve against a ~4.4 GW requirement with zero load
  shed; the tail is priced by MISO's Monte-Carlo-LOLP-derived RCPF/ORDC over
  10–30-minute risk a perfect-foresight hourly LP does not contain
  (external-validation §1–§2; 23/23 surveyed PCMs share the limitation, §3).
  ELMP does not manufacture that risk — ELMP is the *pricing rule*, and the
  spikes come from the *uncertainty*. Reproducing them would mean fabricating
  the uncertainty or fitting the residual (rules 1/13), which is the standing
  `ordc_scarcity_overlay` **G** (re-affirmed miso-163; data NOT the blocker —
  `data/raw/MISO-AS/asm_rtmcp_zonal_*` is already staged).

**Bottom line 2:** the ELMP hypothesis is right about MISO's pricing design and
already embodied in the model's structure (LP relaxation + startup
amortization + emergency tiers + reserve co-optimization, each a K cell); what
it cannot buy is the RT-only ex-post tail, which is the honestly-reported
model-class limit — bounded by miso-167 at ~34.8 % of the summer gap, with the
reachable DA-foreseen ~34.1 % already under attack by the keeper's own
mechanism and the pending rho ruling.

## 3. Ames (1122) — the third owner-named plant, diagnosed: a FLOOR-LEVEL defect, not lay-up, and a measured basis-mismatch lead

Ames is in no D-4 FAIL row and is NOT laid up (P(on)=0.909; it is a hard-running
municipal plant). Its defect is the opposite pole of the same floor family:
- Keeper model: **586/593/591 GWh** (2023/24/25), mean 67 MW, on in ~91 % of
  hours — of which **0.546/0.576/0.534 TWh is forced** by
  `st_gas_mustrun_per_plant` (7,343–7,863 binding h/yr; D-4 conduct PASSES
  because the meter median in floored hours is 33–48 MW > 0).
- Meter (CAMPD, units summed): **356/336/306 GWh**, mean 40.6/38.2/35.0 MW,
  p95 58–63 MW. The model runs the plant at **+65 %/+77 %/+93 %** of its
  measured gross energy — near its p95 flat-out, while the real plant
  load-follows at half load.
- **The measured basis mismatch:** the artifact carries `p25_cf = 0.674`
  against a measured p25-of-online of **33 MW = 0.304 of nameplate** (stable
  across all three years). 0.674 × the plant's ~49 MW available-capacity basis
  ≈ 33 MW exactly — i.e. the p25_cf appears to be measured against an
  availability-derated base and reconstructed in `arrays.py` against
  NAMEPLATE, over-flooring any plant with a deep availability derate. This is
  a **named successor** in the same family as the landed PREREG §2a successor
  (1402's pooled-vintage online_frac): the per-plant must-run PARAMETERS
  (level basis, window vintage) need their own identification and A/B. It is
  deliberately not bundled into the membership A/B (rule 19), and Ames is
  deliberately NOT added to any exclusion list — its floor is legitimate in
  kind, wrong in LEVEL (rule 14: fix the measurement, never delete the plant).
- Materiality: ~0.25–0.29 TWh/yr of excess forced energy on this plant alone —
  sub-materiality for every gated criterion, dashboard-visible, and the same
  defect plausibly reaches other deep-derate ST_GAS plants.

## 4. What this session executes vs. names

- **Executed:** the lay-up membership A/B per the landed
  `PREREG-miso170-stgas-floor-membership-2026-08-19.md` (K-0 control + arm,
  this session's solves; results in `RESULT-miso170` / dashboard).
- **Named, not chartered (each needs its own identification + prereg):**
  (i) per-year `online_frac` for the must-run window (1402, the landed
  PREREG's successor); (ii) the p25-level reconstruction basis (Ames, §3);
  (iii) `measured_interface_limits` as a zonal-basis (not C3a) lever;
  (iv) the scarce-hour over-import (+1.33 GW, miso-167 §2d);
  (v) the benchmark-composition question (INDIANA.HUB vs load-zone composite)
  — an OWNER decision about what C3a should mean, logged §1f/§1 bottom line.
