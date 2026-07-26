# FINDING — caiso-121 SURPLUS-REGIME MARGINAL-UNIT ATTRIBUTION: the belly λ is set by the **EF-0 `DSW_surplus_clean` import tranche** (interior in 53/62/84 % of surplus hours), and **59–101 % of the λ−min-hub wedge is DSW→CA corridor congestion rent, not the tranche's price**; the border-carbon candidate is REFUTED (the marginal rung pays no border carbon), the committed-gas candidate is REFUTED (CC_REGULAR interior 1.3–4.9 %); the delta family selected is **corridor/export-path in surplus**, NOT clean-tranche depth and NOT committed-state (2026-07-26)

**Derive-first: NO mechanism armed, nothing promoted.** Keeper
`2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. Attribution runs on a
same-HEAD control replay (`caiso121_repro_A`, gitignored, NOT registered —
FINDING-caiso92b protocol), because the caiso-119 operational note holds:
HEAD drift is not inert for CAISO (quantified in §0 below).

Instruments (committed): `scripts/probes/_caiso121_surplus_marginal.py`
(the caiso-105 pin-aware method re-pointed at the caiso-120 regime split).

---

## §0 — arm A does NOT reproduce the keeper byte-for-byte (HEAD drift, quantified)

The replay is recipe-identical and the numerics stack matches the keeper's
recorded environment exactly (python 3.11.15, numpy 2.4.6, scipy 1.17.1,
pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4; only the kernel *build label*
differs). It still drifts:

| year | CA λ mean | hourly r | CC_REGULAR | import | other |
|---|---|---|---|---|---|
| 2023 | +0.47 % | 0.99879 | +0.04 % | **+0.55 %** | CC_CHP −2.7 %, CT_PEAKER +1.1 % |
| 2024 | +0.88 % | 0.99733 | **−0.61 %** | +0.31 % | ST_GAS +7.7 % (0.6 TWh class) |
| 2025 | **+1.35 %** | 0.99614 | **−1.24 %** | **+0.93 %** | — |

Direction is uniform and worth recording: **current HEAD makes the C5a defect
slightly worse than the committed keeper snapshot** — gas down, imports up,
λ up, monotonically increasing with year. This confirms the caiso-119 note as
a standing rule, and it is why every number below is read off arm A rather
than the keeper's committed bytes.

The **verdict** is nonetheless preserved: C3a's band is ±10 % mean and the
largest λ drift is 1.35 %; C4's ceiling is 0.30 NRMSE against a keeper at
0.263–0.292 with a 0.996+ inter-arm hourly correlation. Neither can flip on a
drift this size. (Arm A is not scored directly — a repro arm is never
registered.)

## §1 — the marginal rung, named (Inv 4 answered)

Belly = hod 10–15; surplus = measured RT ≤ $20. Interiority is against the LP's
OWN bounds: `min_gen` from `floors/<y>_P1.npz`, caps from the
`run_year(fleet_only=True)` reconstruction. A pinned or at-bound unit cannot set
λ; a strictly interior unit's offer EQUALS its zone's λ at the optimum.

**Per-tranche interiority in surplus-regime belly hours:**

| tranche | EF | 2023 | 2024 | 2025 | interior MW (23/24/25) | its offer |
|---|---|---|---|---|---|---|
| **`DSW_surplus_clean`** | **0** | **52.8 %** | **61.6 %** | **84.1 %** | **1154 / 2121 / 2122** | $8.98 / −$1.92 / $4.48 |
| `WECC_scarcity` | 0.428 | 14.0 % | 0.0 % | 0.0 % | 273 / 40 / — | $41.05 |
| `PNW_midC` | 0 | 12.0 % | 12.5 % | 12.4 % | 70 / 164 / 63 | $12.51 / $18.49 / $10.54 |
| `DSW_daytime_clean` | 0 | 0.5 % | 9.1 % | 0.6 % | 23 / 182 / 12 | $28.42 / $23.40 / $36.78 |
| `DSW_CCGT` | 0.37 | 2.3 % | 6.3 % | 0.9 % | 265 / 88 / 0 | $32.59 / $20.15 / $25.24 |
| `PNW_hydro_base` (firm) | 0 | **0.0 %** | **0.0 %** | **0.0 %** | — | pinned (at-cap 47/49/65 %) |
| `DSW_solar_PV` (firm) | 0 | **0.0 %** | **0.0 %** | **0.0 %** | — | pinned (at-cap 47/49/65 %) |

**The answer is `DSW_surplus_clean`** — the caiso-87 WEIM clean surplus-depth
tranche, priced at the measured Palo Verde hub + Path-46 wheel, **EF 0**.

### The two named candidates this REFUTES

1. **Border-carbon import rung — REFUTED.** The winning rung carries
   `IMPORT_TRANCHE_EF = 0` and therefore pays **no border carbon at all**. The
   carbon-paying tranches are marginal in a small minority of hours
   (`DSW_CCGT` 0.9–6.3 %, `DSW_CT` 0.0 %). The apparent match between the CARB
   unspecified adder (0.428 × allowance = $14.14 / $15.08 / $12.01) and the
   observed wedge ($4.4 / $13.5 / $8.0) is a **numerical coincidence**: it does
   not even track sign across years (2023's adder is the largest and its wedge
   the smallest). Independently fatal: the cheapest *carbon-paying* rung offers
   $78–81/MWh, ~10× the surplus λ.
2. **Domestic gas at a floor/min-load block — REFUTED as the price-setter.**
   CC_REGULAR is interior in **4.9 / 4.8 / 1.3 %** of surplus hours carrying
   **3 / 4 / 1 MW**, at an offer ($35–41) 3–6× λ. It is **62–72 % PINNED** —
   which is exactly the point: a floored unit is a *volume* mechanism and
   cannot set λ by LP optimality. (Same for the 100 %-pinned CC_CHP / CT_CHP /
   nuclear — the DO-NOT-REDO note about the ~99 % floor-binding rate stands.)
3. **Hydro shadow value — co-marginal, not the driver.** Interior in 21–29 % of
   surplus hours but carrying only **14–22 MW**; at-cap 55–74 % (the p95
   envelope). Real, small.

## §2 — the load-bearing decomposition: the wedge is CONGESTION, not the rung's price

Every term below is a mean over the SAME mask (surplus belly hours with a
defined measured hub), so the two components sum exactly to the wedge:

| yr | n | act RT | min-hub | model **WECC_DSW** λ | model **CA** λ | **wedge** | = node−hub | + **congestion** (CA−DSW) | congestion share |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 659 | $3.08 | $5.26 | $5.20 | $9.65 | **+$4.39** | −$0.06 | **+$4.45** | **101 %** |
| 2024 | 1116 | −$5.21 | −$6.65 | −$1.52 | $6.88 | **+$13.53** | +$5.13 | **+$8.40** | **62 %** |
| 2025 | 1077 | −$0.11 | −$0.80 | $2.51 | $7.20 | **+$8.00** | +$3.31 | **+$4.68** | **59 %** |

Reading:

1. **The model's own southern node is priced approximately RIGHT.** WECC_DSW λ
   sits −$0.06 / +$5.13 / +$3.31 from the measured min-hub, and the marginal
   tranche's offer goes negative in 2024 (−$1.92) exactly as the hub does. The
   clean-tranche pricing mechanism is doing its job.
2. **59–101 % of the belly over-price is DSW→CA corridor congestion rent.** CA
   cannot reach its own correctly-priced import node. In 2023 the congestion is
   the ENTIRE wedge.
3. **The northern node is stranded and drowning.** WECC_PNW λ means −$2.22 /
   −$3.12 / −$7.80, negative in **31 / 52 / 59 %** of surplus hours, with a 2025
   median of **−$20.00** (the floor). Its firm block `PNW_hydro_base` is
   self-scheduled must-flow (`MECH_FIRM_IMPORT`) at-cap 47–65 % of the time —
   forced into a node whose only outlet is a bound corridor.
4. **The export sinks NEVER fire.** `WECC_DSW_export_PALOVRDE` and
   `WECC_PNW_export_MALIN` dispatch **exactly 0.00 MW in every one of the 26,280
   hours of 2023–2025** (annual mean 0.00, max 0.00, hours>0 = 0). Reality
   net-exports in 40–57 % of these hours (caiso-120 Table 2). This is not a
   clamp so much as a *consequence*: an export sink absorbs only when CA's own
   marginal cost is below the neighbours' willingness-to-pay, and CA's λ is
   $7–14 *above* the hub. The model imports because it is priced short, and it
   is priced short because it is importing.

## §3 — the physical stack that produces it (corroboration)

Surplus-regime belly means, model − actual (MW). Gas actual on the CEMS basis
(the 930 CISO NG cell is condemned — caiso-121 §Step 2); other fuels raw
EIA-930; model storage from arm A's `storage.parquet`:

| resource | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas | −859 | −784 | −636 |
| hydro | **−1114** | **−948** | **−856** |
| solar | **+1596** | **+1233** | **+1563** |
| wind | +96 | +139 | +125 |
| nuclear | −14 | −10 | −26 |
| **net import** | **+2578** | **+3461** | **+2606** |
| **storage net (charging +)** | **+1967** | **+2049** | **+2244** |

The model **imports 2.6–3.5 GW too much, curtails 1.2–1.6 GW too little solar,
parks ~2.0–2.2 GW of the excess in storage, and displaces 0.9–1.1 GW of hydro
and 0.6–0.9 GW of gas.** Solar curtailment in surplus hours runs 11 / 43 / 41 %
of hours (152 / 560 / 480 MW) — and where it *does* bind, the price collapses
correctly (SDGE λ $1.46 in 2024, $0.93 in 2025, vs $7.2–7.7 in the congested
zones). The mechanism for a right-priced surplus belly is present and working;
it is reached in only one zone.

**Open basis item (not a finding, flagged honestly):** the model's CA-zone
demand in these hours runs 1,426 / 2,567 MW BELOW the EIA-930 CISO Demand cell.
The two are on different bases (`caiso_supply_consistent_demand` reconstructs
from the generation frame), so the rows above do not sum to zero and no
conclusion here rests on the demand row. Note the difference works *against*
the model's behaviour — a shorter demand should make it export MORE, not less.

## §4 — which joint belly-delta family this SELECTS

Against the three candidate families the caiso-120 handoff put up:

- **SELECTED — export-path / corridor in surplus.** It owns 59–101 % of the
  wedge (§2), it is the only family that also explains the missing net-export
  sign, and it is the only one consistent with a correctly-priced import node
  (§2.1). Two structurally distinct sub-levers, both already in the tree and
  both default-off in this keeper: the corridor's **export-direction
  deliverability envelope** (a measured p95 net-export ceiling whose median
  collapses to ~0 GW on the DSW leg — derived from *evening* net-import
  behaviour, then applied to midday hours where reality exports), and
  `caiso_wecc_export_floor` (caiso-112, rejected in the caiso-113 L1a′ form
  because it priced exports at a FIXED hub in ALL hours — the regime split now
  says the export conduct is a *surplus-regime* behaviour, which is precisely
  the caiso-120 Inv 3 argument).
- **NOT SELECTED (second-order) — clean-tranche depth/EF.** The tranche is
  priced near-correctly (node−hub −$0.06/+$5.13/+$3.31) and hits its cap in only
  0.7 / 20.8 / 3.5 % of surplus hours. Its EF is already 0. Adding depth moves
  the volume the wrong way; the 2024 20.8 % at-cap share is the only part worth
  revisiting, and only jointly.
- **NOT SELECTED — committed-state.** Refuted at 1.3–4.9 % interior share
  (§1.2). The committed-gas lever is real for the *firm-regime* ~2 GW volume
  defect (caiso-118b/119) but has no purchase on the surplus-regime price.

**Pre-registered gates for that later delta remain the REGIME-CONDITIONAL ones**
(FINDING-caiso120 §Gate implication), never aggregate import volume: (i) surplus
— signed interchange goes long (net-export hours appear toward the measured
40–57 %), λ − min-hub → ~0, and specifically **CA λ − WECC_DSW λ → ~0** (the
term this finding isolates as the majority of the error); (ii) firm — import →
measured 0.9–2.4 GW with gas filling; (iii) C3a stays PASS by each regime being
individually right.

**No mechanism is armed by this finding.** Arming either corridor sub-lever is a
separate owner ask, and would be scored leave-one-year-out within 2023–2025
before promotion (rule 22).

---

Reproduction:
`python scripts/probes/_caiso121_surplus_marginal.py results/calibration/caiso121_repro_A --recipe-from results/calibration/caiso_netrev_margin`
(arm A is gitignored; re-create it with
`python scripts/replay_keeper.py results/calibration/caiso_netrev_margin --years 2023 2024 2025 --out-dir results/calibration/caiso121_repro_A`).
