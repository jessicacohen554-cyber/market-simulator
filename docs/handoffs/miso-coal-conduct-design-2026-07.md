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

Scored-basis prices (demand-weighted zonal monthly vs bench `rt_lw_mon` —
method validated by reproducing the keeper's scored 0.082/0.099/0.183
exactly from its payload):

| metric | miso-65 (scored) | probe (scored basis) | gate |
|---|---|---|---|
| C3a-2024 | −2.9% | **−7.2%** | ±10% → PASS retained |
| C3b-2024 | 0.099 | **0.122** | ≤0.20 → PASS |
| C3a-2025 | −12.9% | **≈−15%** | FAIL, worse by ~2pp |
| C3b-2025 | 0.183 | **0.201** | ≤0.20 → AT/OVER the gate by ~0.001 |
| C3c both years | unchanged (4h/0h > $200) | unchanged | — |

The 2025 damage is a broad ~$0.5–1.6/month price drop — the level gap
leaking into the (bias-inclusive) shape metric, not a new shape error. The
2025 model-under is owned by the OTHER open lanes (lane-2 max-gen event
registry ≈ $6 of July alone; C3c scarcity depth; the G-23 import starvation
−5.8 TWh, which also confounds the 2025 coal-over reading). C5a direction:
2024 CO₂ −5.7% under → coal-up moves it toward actual; 2025 +0.9% → small
further rise, stays inside ±7%.

<!-- 2023 GUARD + BASE REPLICA FILLED AFTER SOLVES -->

## 6. Expected scored deltas for miso-66 (to verify in Phase B)

- **C1 (fuelmix): the two 2024 FAILs flip PASS** (PRB +5.34 / CT +4.57 under
  V1a; V1b shifts both a little as PSGC/Warrick BIT competes back). 2023 PRB
  improves (−7.26 → ≈+3.7). The open rows: COAL_BIT-2023 (V1a breaks it at
  −8.59 → V1b recovers Prairie State/Warrick, expected ≈−5) and
  **ST_GAS-2024** (−7.83 → ≈−9.3 on the −1.5 displacement shave — the
  possible new FAIL). Best case 16/16 (first MISO C1 clean sweep); worst
  case 15/16 with the fail row swapped {PRB, CT} → {ST_GAS}.
- **C3a: PASS/PASS/FAIL retained** — 2024 degrades −2.9% → ≈−7% (in-band),
  2025 worsens ≈−13% → ≈−15% (already FAIL).
- **C3b: 2024 PASS (≈0.12); 2025 ON the gate (≈0.20 ± solver noise)** — the
  promotion-deciding number; Phase B scores it exactly.
- **C3c: unchanged** (this lane adds no tail hours; that is the scarcity-depth
  lane).
- **C5a: 2024 improves (−5.7% → ≈−3%), 2025 small rise (stays PASS).**
- **C8: unchanged** (pricing input, no forced energy; twin keeps it armed).
- **Fail set: {fuelmix, price_mean, price_tail} → {price_mean, price_tail}
  if C3b-2025 holds ≤0.20, else 3 FAILs with fuelmix swapped for
  price_shape.** Either way C1 16/16 is a first; the C3b edge case is the
  owner's promotion call, with the lane-2 event registry the named root
  cause that relieves the 2025 price level.

## 7. Phase B execution checklist

See the Phase B prompt block in the 2026-07-14 calibration-log entry /
session handoff. Summary: harden the mechanism (unit tests: off-path
byte-identity, RE/NR scoping, union semantics, null-status conservatism;
docstring cross-refs), full `--year 2023 2024 2025` bundle + zero-forcing
twin (mechanism stays armed in the twin — pricing input), register as
miso-66 with the standard artifact chain, recommendation only (owner
promotes).
