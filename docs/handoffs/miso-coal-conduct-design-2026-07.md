# MISO lane 1 — regulated-coal conduct complement: design + probe evidence (Phase A)

**Date:** 2026-07-14. **Session:** `claude/miso-lane1-coal-conduct-apkicm`
(Phase A — diagnosis/design; Phase B executes from this document).
**Lane:** lane 1 of the miso-64/65 sequencing — the conduct gap the miso-65
availability truth exposed (rule 15): **C1-2024 FAILs {COAL_PRB −10.41 TWh,
CT_PEAKER +8.30 TWh}** on the `2026-07-14-miso-65-outage-regen` keeper. At
$2.19 gas the LP fills missing coal with CT where the real market
self-committed coal. Nothing in this document is fit to a residual; every
scale is a committed measured input (SOM Table 7, EIA-860 Regulatory Status,
EIA-923 Schedule-5, CAMPD tranches).

## 1. The residual, restated two-sided

miso-65 C1 (scored, rubric v2.5; 2025 rows prelim-923 SKIPPED but shown):

| year | COAL_PRB | COAL_BIT | COAL_LIG | CT_PEAKER | verdict |
|---|---|---|---|---|---|
| 2023 | −7.26 (PASS, 0.74 from band) | −4.80 PASS | −1.19 PASS | +3.59 PASS | — |
| 2024 | **−10.41 FAIL** | −2.06 PASS | −2.54 PASS | **+8.30 FAIL** | the target |
| 2025 | +5.12 (ungated) | +3.09 (ungated) | −0.59 | +2.33 (ungated) | the guard |

Any fix must move 2024 PRB **up** ≥2.4 TWh and CT **down** ≥0.3 TWh (band
edges) — ideally mid-band — while adding ≈nothing in 2025 (PRB headroom to
the +8.0 band edge is ~2.9 TWh; C3a-2025 is −12.9% so cheaper troughs hurt;
C3b-2025 just flipped PASS) and not pushing 2023 BIT (−4.80) through −8.0.

## 2. Measured anchors (all in-repo)

- **SOM Table 7** (`data/raw/som-competitive-conduct/som_competitive_conduct.csv`,
  freeze-tested): regulated-utility coal starts 2023/2024: **56%/53%
  must-run (self-commit)** — 42/38pp profitable + 14/15pp "ran regardless of
  the price" — vs 44%/47% offered economically. Merchant coal: **93%/74%
  offered economically** (39–42 starts/yr total — the merchant fleet is small).
  The IMM's words: *"MISO's regulated utilities often continue to operate
  their units as 'must-run', running them regardless of the price."*
- **Revealed merit 2024** (diagnosis §6, F923+EIA-923, no model): 83% of PRB
  capacity sat above the CC fleet's $21 cap-weighted SRMC yet ran CF 0.43.
  Real regulated PRB does not follow full-SRMC offers.
- **The 2024 CT over-run is ~94% economic** (D-2) — a merit-order crossing,
  not a floor artifact. Its energy is the displaced side of the PRB deficit.
- **EIA-860 `Regulatory Status`** (`data/raw/eia-860/eia860_plant.parquet`,
  previously unread by code): RE/NR per plant, zero nulls on MISO coal —
  39 RE / 21 NR plants. The measured regulated-vs-merchant split Table 7
  conditions on.
- **Take-or-pay contract shares** (`coal_takeorpay_MISO.csv`, EIA-923
  Schedule-5): MISO coal ~100% contracted; 98% of RE coal plants in the map,
  mean share 0.94.

## 3. Rule-19 enumeration (what already floors/prices MISO coal)

| mechanism | state in miso-65 | phenomenon |
|---|---|---|
| `_mustrun` fuel-free band (per-plant CAMPD `mustrun_pct`, `coal_mustrun_per_plant`) | ON | the never-off self-commit floor (≈ Pmin × always-on share) |
| `coal_bit_committed_takeorpay` | ON (BIT only) | sunk-contract committed-band bid — **scoped by coal rank, not by the conduct driver** |
| `coal_econ_srmc_bound` | ON | econ/peak tranches ≥ full delivered SRMC (SOM mark-up ~0) |
| `coal_warm_committed` | ON | committed band exempt from startup markup (warm boiler) |
| `commitment_screen_coal` (P0 screen) | ON | commitment scaffolding |
| `coal_plant_monthly_pricing` + `class_aware_fuel_price_fallback` | ON | measured F923 fuel input |
| unit-outage overlays (std + short) | ON | physical availability |
| `coal_committed_takeorpay_all` | OFF — **blanket form settled as overshoot** (miso-60-era probe: PRB +15.7 swing, total coal +6.3 over) | — |
| PRB/BIT/LIG passthrough sigmoids | OFF for MISO (miso-53 SOM adjudication) | (premise refuted — offers near cost) |

The self-commitment phenomenon is carried **once** below the observed floor
(`_mustrun`) and **once** in the committed band's pricing (take-or-pay
discount). What is wrong today is the committed-band discount's **scope**:
it gates on coal rank (BIT) when the measured conduct split is
**regulatory status** (Table 7's own row structure). PRB/LIG regulated
committed bands bid full cost (get priced out at $2.19 gas — the 2024
deficit), while NR-BIT merchants (Prairie State, Warrick, ADM Decatur,
Filer City) get a discount the SOM says merchants don't exercise.

## 4. The design (frozen for Phase B)

**Mechanism: `coal_committed_takeorpay_regulated`** (ScenarioConfig, tier 3,
default **off** — every existing keeper byte-identical).

> The `_committed` tranche of a coal plant whose EIA-860 `Regulatory Status`
> is `RE` passes `1 − contract_share` of its fuel (the plant's own measured
> EIA-923 Schedule-5 take-or-pay share — the identical sunk-contract rule
> `_mustrun` and the BIT flag already use), bounded below by any supply
> passthrough in force. NR (merchant/IPP) committed bands bid full delivered
> cost. Union scope with the older flags; in the miso-66 recipe it
> **replaces** `coal_bit_committed_takeorpay` (rule 19 reconcile: RE-BIT
> plants are covered identically; NR-BIT reverts to the economic bidding the
> SOM measures for merchants).

Implementation (built and wired this session, probe-grade; Phase B hardens):

- `ScenarioConfig.coal_committed_takeorpay_regulated: bool = False`
  (+ tier-3 registry entry) — `src/market_sim/config/scenarios.py`.
- `fleet.eia860_regulated_plants()` — lru-cached `frozenset[int]` of RE plant
  codes from `eia860_plant.parquet` (`Regulatory Status`; null/absent ⇒ NR,
  conservatively no discount).
- `fleet.campd_tranche_fuel_frac(..., committed_takeorpay_regulated,
  regulated_plants)` — scope extension
  `_scope = all | (bit & _bit) | (regulated & plant ∈ RE)`; call-site threads
  the set only when the gate is on.
- No-LP wiring check `scripts/probes/_miso_coalconduct_wiring.py` (2024):
  **31/3022 units move, all `_committed` coal tranches**: RE prb 9,403 MW
  $28.09 → $5.07/MWh; RE lignite 442 MW $30.42 → $4.50; NR bituminous
  1,054 MW $4.53 → **$34.25** (the merchant reversion); RE BIT unchanged
  (covered under both flags); unmoved max |Δ| = 0.0.

### Why this framing (the charter's three candidates adjudicated)

- **(b) SOM-scoped committed take-or-pay — CHOSEN, with the scope carried by
  the measured regulated/merchant split rather than a 0.56 multiplier.** The
  SOM 56% is a share of **starts**; the miso-53 adjudication already ruled a
  start-share cannot size a capacity tranche ("smearing one fleet-level
  share over 44 per-plant measured floors loses granularity and manufactures
  a level no unit operates at"). The dimension-honest carrier of "how much
  of this plant stays online regardless" is the plant's **own CAMPD
  committed band** — an always-on self-committer carries a large
  mustrun+committed share, an economically-offered cycler a small one. The
  SOM statistic's information content is the **regulated-vs-merchant
  conduct split** (its own table structure), which is exactly what the
  EIA-860 flag scopes. Zero fitted scalars; LOYO at estimation is by
  construction (a boolean arming three measured inputs — the accepted
  miso-59..64 argument).
- **(a) ownership-scoped committed-share re-derivation — REJECTED**: the
  tranche shares are CAMPD-measured per plant and frozen against residuals
  (rule 23); re-deriving them from a starts split is both the dimension
  error above and a rule-23 violation (no source-data update triggers it).
- **(c) CT-side start-limit counterpart — DEFERRED (not built)**: the CT
  over-run is ~94% economic displacement; the coal-side fix returns that
  energy automatically through the LP energy balance. A second CT-side
  mechanism would stack on the same phenomenon (rule 19) with no measured
  driver in hand. Re-open only if the probe leaves CT_PEAKER-2024 out of
  band after the coal fix.

### Admissibility (rules 13/14/17/18/19/23/25)

- **Rule 13 test** ("regenerates forward, responds to changed conditions"):
  Regulatory Status is a standing institutional attribute (updates with each
  EIA-860 vintage); contract shares regenerate from each EIA-923 Schedule-5
  vintage; the discounted bid is `(1−share)×fuel` so it moves with the
  forward fuel trajectory; a deregulated/retired plant exits the set. No
  measured *outcome* is fed back (no CEMS generation pinning, no residual
  scalar).
- **Rule 17/18**: not a floor (no min-gen row; the LP remains free to leave
  the band idle when demand is absent) — it is a bid, so no window/driver
  floor contract is triggered; scoping is an institutional attribute, not a
  class-name tuple, and it *removes* a rank-scoped special case.
- **Rule 19**: replaces the BIT flag in the recipe (union semantics kept for
  backward replay of miso-62/63/64/65 bundles, which arm the BIT flag alone).
- **Rule 23**: no derive script touched; consumes frozen artifacts. Re-derive
  triggers: new EIA-860 vintage (RE set), new EIA-923 Schedule-5 vintage
  (shares), new SOM publication (conduct citation refresh).
- **Rule 25**: the flag is ISO-generic but default-off everywhere; the
  arming evidence is MISO's own SOM. No tuned curve crosses an ISO boundary
  (the RE set and Schedule-5 shares are national measured data, not fits).
- **C8/D-2**: a pricing input — forces no energy; stays **ARMED in the
  zero-forcing twin** (the miso-62 precedent for pricing inputs). No new
  D-2 floor id; coal forced share stays the mustrun-band attribution.
- **DOF ledger**: +1 measured-physical entry (SOM Table 7 + EIA-860
  RegStatus + Schedule-5 shares), zero fitted scalars → miso-66 expected
  **19 measured / 2 legacy**.

### The one classification caveat (decided by probe, fallback pre-defined)

EIA `Regulatory Status` classifies the **operator**. Conduct-regulated
public-power-owned IPPs read NR — materially **Prairie State** (1,630 MW BIT,
~95% muni/coop-owned per EIA-860 Schedule 4: AMP-Ohio 23.3%, IMEA 15.2%,
IMPA 12.6%, MJMEUC 12.3%, Prairie Power 8.2%, SIPC 7.9%, KMPA 7.8%, NIMPA
7.6%, Wabash Valley 5.1%; take-or-pay offtake, runs baseload). Baldwin and
Newton (Vistra, 100% operator-owned) are genuinely merchant. Under this
design Prairie State's committed band loses its (BIT-flag) discount — ~2.9
TWh/yr at risk against the 2023 BIT margin (−4.80, band ±8.0).

**Fallback V1b (only if the probe breaks a BIT band):** extend the scope to
"regulated-like" = RE ∪ {plants whose EIA-860 Schedule-4 ownership is
majority public-power/cost-of-service (owner Entity Type M/C/P/S/F or an RE
utility)}. Still fully measured and forward-reproducible; pulls Prairie
State (~95%) back in; leaves Plum Point (43%) and Big Cajun 2 (42%) out at
the majority threshold. Do NOT reach for it unless a band actually breaks —
the simpler classifier is preferred while it scores clean (rule 1: structure
first, and the simplest measured scope that carries the conduct).

**V1b ENGAGED (2026-07-14, this session).** The RE-only (V1a) 2023 probe
broke the COAL_BIT band exactly on the pre-identified reversion (−4.80 →
−8.59, 0.59 past the ±8.0 edge; per-plant: Prairie State probe 8.99 vs
actual 12.48, Warrick 2.24 vs 4.14 — both offtake/host-obligated
self-committers, not price-responsive merchants). Because the fallback and
its trigger were declared in this document (committed at `8bc5b67`) BEFORE
the probe was read, engaging it is the pre-registered estimation path
(caiso-81 discipline), not residual tuning. Implementation:
`fleet.eia860_selfcommit_scope_plants()` = `eia860_regulated_plants()` (RE)
∪ `eia860_costofservice_majority_plants()` — per plant, the summed
Schedule-4 `Percent Owned` of owners whose EIA-860 utility `Entity Type` ∈
{I, M, C, P, S, F} (cost-of-service entities), > 0.5; plants absent from
Schedule 4 use the operator's entity type (ownership.py's sparse-schedule
rule). Scope resolution on the decision plants (all measured, zero hand
exceptions):

| plant | RE | COS-majority | in scope | note |
|---|---|---|---|---|
| Prairie State | ✗ | ✓ (~95% muni/co-op JAAs) | ✓ | the band-breaker recovers |
| Warrick | ✗ | ✓ (operator = Alcoa's 'I'-typed generating utility) | ✓ | host-obligated self-committer; EIA's own typing |
| Baldwin / Newton (Vistra) | ✗ | ✗ (operator 'Q') | ✗ | the SOM's true merchants |
| Plum Point | ✗ | ✗ (43% < 0.5) | ✗ | below majority |
| Big Cajun 2 | ✗ | ✗ (42% Entergy < 0.5) | ✗ | below majority |
| ADM / Filer City CHPs | ✗ | ✗ (IND / Q) | ✗ | probe shows exclusion is honest (ADM over-runs actual even unfloored) |

## 5. Probe evidence (rule 16 — throwaway, never registered)

Probe driver: `scripts/probes/_miso_coalconduct_probe.py` (miso-65 recipe
replay = miso-62 `meta.json` strict RENAME/SKIP + `miso_rpe_pricing` +
`unit_outage_short_windows` + `class_aware_fuel_price_fallback`, on the
regenerated outage extract; `reg` mode swaps
`coal_bit_committed_takeorpay=False` /
`coal_committed_takeorpay_regulated=True`). Readout:
`scripts/probes/_miso_coalconduct_readout.py` (probe dispatch/system
parquets vs the registered miso-65 payload + measured actuals). A
same-machine `base` 2024 replica anchors environment drift.

### 2024 (the two-sided target) — BOTH C1 FAILS FLIP TO PASS

Class TWh, probe vs the registered miso-65 payload vs actual (C1 band ±8.0):

| class | probe | miso-65 | Δ | actual | Δ-to-actual: miso-65 → probe |
|---|---|---|---|---|---|
| COAL_PRB | 121.80 | 106.05 | **+15.76** | 116.46 | **−10.41 FAIL → +5.34 PASS** |
| COAL_BIT | 46.02 | 51.27 | −5.25 | 53.33 | −2.06 → −7.31 PASS (0.69 from edge — the NR reversion, see 2023) |
| COAL_LIGNITE | 5.36 | 3.98 | +1.37 | 6.52 | −2.54 → −1.16 PASS |
| CT_PEAKER | 23.79 | 27.53 | −3.74 | 19.23 | **+8.30 FAIL → +4.57 PASS** |
| CC_REGULAR | 143.64 | 147.43* | −3.79 | 143.47 | scored ≈ +2.6 → ≈−1.2 |
| ST_GAS | 15.37 | 16.88* | **−1.51** | 17.57 | scored ≈ −7.83 → **≈−9.3 (RISK: flips FAIL — was 0.17 from the edge)** |
| total coal | 173.18 | 161.31 | +11.87 | 176.32 | −15.0 → −3.1 |

\* CC_REGULAR/ST_GAS baselines are the same-machine `base` 2024 replica, NOT
the payload gmModel — the payload applies the OTHER_FOSSIL raw-klass relabel
(the miso-62 handoff's documented artifact), which the replica exposed: every
coal/CT class reproduces the payload to ±0.01 TWh, while raw-klass ST_GAS
reads +7.14 and CC_REGULAR +1.37 above their relabelled payload values. An
earlier draft of this table showed ST_GAS "+5.63 improvement" — that was the
relabel offset, not a real rise; the true A/B is **ST_GAS −1.51**.

The displaced CT energy returns to coal through the energy balance exactly as
designed — no CT-side mechanism needed (charter candidate (c) stays closed).
The displacement also shaves CC (−3.8) and ST_GAS (−1.5); ST_GAS-2024 was
already scored at −7.83 vs a ±8.0 band, so the shave likely flips it FAIL —
the known secondary risk Phase B's exact scoring adjudicates (the ST_GAS
deficit itself is the VLR-floor lane's open item, not this lane's).

Price side (Indiana DA-monthly proxy; scored C3a is RT-basis, deltas
transfer): C3a-2024 proxy −0.6% → −5.6% (scored −2.9% → ≈−7.9%, stays inside
the ±10% band); C3b-2024 proxy NRMSE 0.147 → 0.154 (scored 0.099 → ≈0.107,
PASS); hours > $200 unchanged (4); P10 $21.61. The cheaper troughs are the
honest price of holding sunk-fuel committed coal — the residual 2024 mean gap
sits in the missing tail (C3c 4h vs 24h actual), not in this lane.

### 2024 under V1b (`regb` — the Phase B configuration)

True A/B vs the same-box base replica; scored estimates apply the A/B delta
to the keeper's scored value:

| class | regb | base | A/B | scored est. to-actual (m65 → regb) |
|---|---|---|---|---|
| COAL_PRB | 120.92 | 106.05 | **+14.87** | −10.41 FAIL → **+4.46 PASS** |
| COAL_BIT | 50.77 | 51.27 | −0.50 | −2.06 → −2.56 PASS (PSGC/Warrick kept) |
| COAL_LIGNITE | 5.33 | 3.98 | +1.35 | −2.54 → −1.19 PASS |
| CT_PEAKER | 22.48 | 27.54 | **−5.06** | +8.30 FAIL → **+3.25 PASS** |
| CC_REGULAR | 142.41 | 147.43 | −5.03 | +2.60 → ≈−2.4 PASS |
| ST_GAS | 14.94 | 16.88 | −1.94 | −7.83 → **≈−9.8 (likely NEW FAIL — see below)** |
| total coal | 177.02 | 161.31 | +15.71 | −15.0 → **+0.70 (essentially exact)** |

Prices (scored basis, mechanism-only = regb minus same-box base): C3a-2024
−4.0% → −8.3% (Δ −4.3pp → scored ≈ −7.2%, inside ±10); C3b-2024 0.105 →
0.129 (Δ +0.024 → scored ≈ 0.123, PASS); tail unchanged (4 h).

**The ST_GAS-2024 exposure is the same rule-15 pattern by which miso-65
exposed this lane:** cheap held coal displaces the marginal slice of a class
whose own economics are the VLR-drag lane's documented open miss (ST_GAS was
scored −7.83, 0.17 inside the band, BEFORE this mechanism). The displacement
is real physics given the conduct; the deficit it deepens belongs to the
ST_GAS lane. Expected C1: 2023 all rows in band (V1b table below), 2024
15/16-to-16/16 depending on the exact relabel split of the −1.94.

### 2025 (the guard year) — fuel-mix improves broadly, PRB and the price
### level pay; C3b-2025 lands ON the 0.20 gate

Class TWh (2025 C1 rows are prelim-923 SKIPPED — shown for direction; the
scored 2025 guards are C2/C3a/C3b/C3c):

| class | probe | miso-65 | Δ | actual (prelim) | to-actual: miso-65 → probe |
|---|---|---|---|---|---|
| COAL_PRB | 148.61 | 144.38 | **+4.23** | 139.26 | +5.12 → +9.35 (ungated) |
| COAL_BIT | 59.09 | 60.54 | −1.45 | 57.45 | +3.09 → +1.64 (better) |
| CT_PEAKER | 20.13 | 20.74 | −0.62 | 18.42 | +2.33 → +1.71 (better) |
| ST_GAS | (raw 11.87 — payload basis carries the OTHER_FOSSIL relabel; see the 2024 note) | | ≈−1 to −2 true A/B | 14.86 | ungated 2025 |
| total coal | 213.25 | 210.17 | +3.08 | 202.55 | +7.62 → +10.70 |

V1b (`regb`) 2025 is near-identical — PSGC/Warrick sit in-merit at 2025 gas,
so restoring their discount barely moves the year: PRB +3.98, BIT −0.35,
CT −0.70, total coal +3.91 (over-read +7.62 → +11.5 on the prelim-923
basis, confounded by the G-23 import starvation −5.8 TWh); scored-basis
C3a −14.4% / C3b 0.201, matching V1a within solver noise.

Scored-basis prices (demand-weighted zonal monthly vs bench `rt_lw_mon` —
method validated by reproducing the keeper's scored 0.082/0.099/0.183
exactly from its payload):

**Mechanism-only price deltas (probe minus same-box base replica — the
drift-clean numbers; scored estimate = keeper scored + delta):**

| metric | keeper scored | same-box base | probe | mechanism-only Δ | scored miso-66 est. | gate |
|---|---|---|---|---|---|---|
| C3a-2024 | −2.9% | −4.0% | −8.3% | −4.3pp | **≈−7.2%** | ±10% PASS |
| C3b-2024 | 0.099 | 0.105 | 0.129 | +0.024 | **≈0.123** | ≤0.20 PASS |
| C3a-2025 | −12.9% | −13.5% | −14.4% | **−0.9pp** | **≈−13.8%** | FAIL (was FAIL; modest) |
| C3b-2025 | 0.183 | 0.196 | 0.201 | **+0.005** | **≈0.188** | ≤0.20 **PASS — guard holds** |
| C3c both | 4h/0h > $200 | — | unchanged | 0 | unchanged | — |

The naive probe-vs-registered 2025 comparison (0.183 → 0.201) was ~70%
solver-box drift — the base-2025 replica reads the UNCHANGED keeper config
at 0.196 on this box. The mechanism's own 2025 footprint is +0.005 C3b /
−0.9pp C3a: the committed bands are in-merit at 2025 gas, so the discount
is largely inframarginal there (2025 ST_GAS A/B −0.12, CC −1.95). The 2025
level gap stays owned by the OTHER open lanes (lane-2 max-gen event registry
≈ $6 of July alone; C3c scarcity depth; the G-23 import starvation −5.8 TWh,
which also confounds the 2025 coal-over reading). C5a direction: 2024 CO₂
−5.7% under → coal-up moves it toward actual; 2025 +0.9% → small further
rise, stays inside ±7%.

### 2023 — V1a broke COAL_BIT on the reversion; V1b clears every row

V1a (RE-only): PRB −7.26 → +3.65, CT +3.59 → +1.95, C3a +1.8% → −1.6%, C3b
0.082 → 0.085 — but **COAL_BIT −4.80 → −8.59 (FAIL by 0.59)**, decomposed
per-plant to Prairie State (probe 8.99 vs actual 12.48) and Warrick (2.24 vs
4.14). The pre-declared V1b scope (RE ∪ cost-of-service majority) engaged —
`regb` probes:

| class | regb-2023 | miso-65 | Δ | actual | to-actual: m65 → regb |
|---|---|---|---|---|---|
| COAL_PRB | 124.68 | 114.41 | +10.27 | 121.67 | −7.26 → **+3.01 PASS** |
| COAL_BIT | 51.76 | 52.27 | −0.51 | 57.07 | −4.80 → **−5.31 PASS** |
| COAL_LIGNITE | 6.27 | 5.86 | +0.42 | 7.05 | −1.19 → −0.78 |
| CT_PEAKER | 18.46 | 20.63 | −2.17 | 17.04 | +3.59 → +1.42 |
| total coal | 182.72 | 172.53 | +10.18 | 185.79 | −13.3 → −3.1 |

Prairie State recovers 8.99 → 11.23 TWh, Warrick 2.24 → 3.38 — both toward
actual: the ownership-refined set is empirically the conduct set. Prices:
C3a +1.8% → −2.2% (magnitude ~unchanged), C3b 0.082 → 0.087 PASS. Watch row:
CC_REGULAR-2023 shaves ~−4 (relabel-adjusted estimate ≈ −7.5 vs the −8.0
edge) — Phase B's exact scoring adjudicates.

### Same-machine base-2024 replica (environment control)

Every coal/CT class reproduces the registered payload to ±0.01 TWh —
probe-vs-payload deltas for those classes are clean A/B evidence. Raw-klass
ST_GAS/CC_REGULAR sit +7.14/+1.37 above their payload values (the
OTHER_FOSSIL relabel); their A/B baselines are the replica, not the payload.
Scored-basis price reproduction: C3a −4.0% / C3b 0.105 vs the keeper's
scored −2.9%/0.099 — solver-path noise of ~1pp/0.006 NRMSE on this box;
read all probe price deltas with that tolerance.

## 6. Expected scored deltas for miso-66 (to verify in Phase B)

All estimates below are the V1b (`regb`) configuration — the Phase B build:

- **C1 (fuelmix): both 2024 FAILs flip PASS** (PRB +4.46 / CT +3.25); 2023
  all eight rows in band (PRB +3.01, BIT −5.31); COAL_BIT-2024 −2.56. The
  one at-risk row is **ST_GAS-2024** (−7.83 → ≈−9.8 on the −1.94
  displacement shave; the exact scored value depends on the OTHER_FOSSIL
  relabel split). Best case 16/16 all / 12/12 free (the first MISO C1 clean
  sweep); expected case 15/16 with the fail composition changed from
  {PRB-2024, CT-2024} to {ST_GAS-2024} — a single row owned by the VLR-drag
  lane's documented deficit.
- **C3a: PASS/PASS/FAIL** — 2023 ≈−2%, 2024 ≈−7.2% (in-band), 2025 ≈−13.8%
  (FAIL before and after; mechanism-only −0.9pp).
- **C3b: PASS all three — ≈0.087 / ≈0.123 / ≈0.188.** The 2025 guard holds
  (mechanism-only +0.005; the 0.201 raw probe reading was solver-box drift
  on a box that reads the unchanged keeper at 0.196).
- **C3c: unchanged FAIL** (this lane adds no tail hours; scarcity-depth lane).
- **C5a: 2024 improves (−5.7% → ≈−3%), 2025 small rise (stays PASS).**
- **C2: watch** — 2025 grid-basis coal-family over-read rises ~+1.5-2pp
  (confounded by the import-starvation residual).
- **C8: unchanged** (pricing input, no forced energy; twin keeps it armed).
- **DOF: 18 measured / 2 legacy → 19 / 2** (one new measured-physical entry,
  zero fitted scalars).
- **Fail set: {fuelmix, price_mean, price_tail} → {price_mean, price_tail}
  best case (fail set sheds one), or unchanged-count with fuelmix's
  composition reduced to the single ST_GAS-2024 row.** Either outcome is
  structurally strictly better: the 2024 coal/CT conduct block is closed
  with total-2024 coal landing +0.70 TWh of actual.

## 7. Estimation-stage governance (rules 16/22/23)

- All probes are rule-16 throwaways (never registered); solved years
  2023/2024/2025 only. Probe bundles are gitignored; the solve logs and this
  document are the committed record.
- **LOYO at estimation: by construction** — the mechanism is a boolean
  arming three measured inputs (EIA-860 Regulatory Status + Schedule-4
  ownership × Entity Type, EIA-923 Schedule-5 shares, CAMPD tranche
  structure) with ZERO fitted scalars (the miso-59..64 accepted lineage
  argument); additionally all three years were probed A/B, which exceeds
  the LOYO-estimation minimum. The single scope decision made against probe
  evidence (V1a → V1b) followed a fallback pre-declared in this document
  (committed `8bc5b67`) before the deciding probe was read.
- No derive script touched (rule 23). Re-derive triggers recorded in §4.

## 8. Phase B execution checklist

The full copy-paste Phase B prompt lives in the session handoff (chat).
Summary: verify this branch's mechanism (already built, 23 tests green,
wiring-checked), build `scripts/probes/_miso66_coalconduct.py` on the
`_miso65_outage_regen.py` pattern (miso-62 meta + miso_rpe_pricing +
unit_outage_short_windows + class_aware_fuel_price_fallback +
`coal_bit_committed_takeorpay=False` + `coal_committed_takeorpay_regulated=
True`), full `--year 2023 2024 2025` bundle + zero-forcing twin (mechanism
stays ARMED in the twin — pricing input, miso-62 precedent; main and twin
NEVER concurrent), register as miso-66 with the standard artifact chain
(DOF ledger 19/2 → attestation with the C5b/C5c storage entries →
legitimacy_diagnostics → dashboard_add_run BEFORE calibration_verdict
--write-metrics → sidecar market_story/ablation links after payload refresh
→ attestation patched from scored metrics → parity check → never commit
deploy-owned manifest.js/benchmark.js/completeness.js → calibration-log
entry → push). Registration with a recommendation; keepers.json swap ONLY
on owner sign-off.
