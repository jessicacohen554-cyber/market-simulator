# FINDING miso-111 — COAL_PRB committed-band dispatchability (C7 amplitude lane)

Session miso-111, 2026-07-31, branch `claude/miso-111-coal-amplitude-p1l29u`.
Pre-registration (kill rules committed BEFORE the Phase-2 measurement, design
refinement committed BEFORE any solve):
`results/calibration/PREREG-miso111-prb-committed-flex-2026-07-31.md`.

## 0. Dependency check + status-report note

`origin/main` already reads keeper `2026-07-31-miso-109b-hy-level` (miso-110
merged), so this branch is off latest main. The prompt's concern that the
calibration status page still reported miso-101b was checked and is
RESOLVED AT HEAD: `frontend/data/backcast/status/MISO.js` at HEAD carries the
109b keeper id and 109b's own numbers (C3a −1.2/−6.4/−14.2 %), and a fresh
`build_status.py --iso MISO` reproduces it byte-identically except the
`generated` timestamp. Any 101b text still visible on the LIVE page is deploy
lag, not repo state; the next Pages deploy clears it.

## 1. Phase 1 (no-LP): the 2025 CV collapse is merit saturation, not census

All from committed artifacts (keeper sidecars, run payload, CAMPD bench,
`run_config.json`) — no solve. Full numbers in the PREREG §2; the four
load-bearing results:

1. **Per-plant, not mix.** Counterfactual class off-peak CV over the 30
   common plants: 2023 shapes hold 0.0725→0.0815 under 2025 weights (mix
   effect is *positive*); 2025 shapes give 0.0193 even under 2023 weights.
2. **Merit saturation on the 2025 fuel path.** Gas $2.19→$3.52/MMBtu lifted
   the model's off-peak LMP p10 to $29.71 — above the entire PRB SRMC band
   ($22-29) — so the econ tranches that supplied ALL the model's within-day
   variability in 2023/24 never back out in 2025. Near-flat plants: 9
   (60.2 TWh, 51 % of class energy) → 13 (89.3 TWh, 62 %). One of the five
   newly-flat plants is MERCHANT (56456, cv 0.122→0.011) whose committed
   band already bids full SRMC — pure price-driven saturation.
3. **Excluded:** take-or-pay share (year-static by construction), census
   (one 1-MW plant), `unit_outage_short_windows` (multi-day grain, no
   hour-of-day signal).
4. **The flexibility inversion persists in 109b** (energy-weighted per-plant
   off-peak CV): model regulated 0.062/0.056/0.018 vs merchant
   0.330/0.184/0.143; actual regulated 0.160/0.126/0.083 vs merchant
   0.171/0.130/0.059.

**The actual-price cross-check that reframes the lane.** MISO's own RT hub
record (MINN/ILLINOIS/INDIANA, `data/raw/lmp-data/MISO/`) shows off-peak
prices routinely INSIDE and BELOW the PRB band in every year — p10
$14.60/$12.30/$17.95, share of off-peak hub-hours < $25 = 56/68/36 % — while
the model's off-peak floor never gets there (p10 $25.34/$21.32/$29.71). And
the conduct is price-responsive (§2): reality's 2025 coal cycling is largely
ECONOMIC, riding real overnight price dips the model does not produce. The
model misses those dips for two separable reasons: (a) ~62 % of class energy
bids ~VOM and cannot participate in price formation (THIS session's lane);
(b) the model's overnight price distribution lacks depth from congestion/
sub-hourly RT dispersion (the miso-89/90 spread-compression defect and the
miso-78/79 data-blocked congestion lane — NOT this session's lane, and NOT
reopened).

## 2. Phase 2: the CAMPD conduct measurement (kill rules did not fire)

Probe `scripts/probes/_miso111_prb_conduct.py` →
`results/calibration/miso111_prb_conduct.csv` (30 plants, 90 plant-years,
plant basis, WP-3 loading-when-on construction; protocol PREREG §4):

| leg | year | online-hours off-peak CV | amplitude (of HSL) | trough→peak |
|---|---|---|---|---|
| REG (26 plants, 29.1 GW) | 2023 | 0.159 | 0.251 | h2→h18 |
| REG | 2024 | 0.126 | 0.224 | h2→h18 |
| REG | 2025 | 0.076 | 0.181 | h2→h18 |
| MER (4 plants, 3.8 GW) | 2023 | 0.193 | 0.318 | h2→h17 |
| MER | 2024 | 0.147 | 0.292 | h2→h18 |
| MER | 2025 | 0.065 | 0.196 | h2→h18 |

- **K1 (flat committed band): NOT fired** — regulated units cycle within-run
  in every year; the online-conditioned profile carries essentially the whole
  class signal (0.159/0.126/0.076 vs unconditional class actual
  0.155/0.121/0.074), so the observed CV is within-run load-following, not
  start/stop edges.
- **K2 (no headroom): NOT fired** — plant-basis `lsl_frac` cap-weighted p50 =
  0.182 (REG; range 0.107-0.731). MER 0.218.
- **K3 (merchant artifact): NOT fired** — merchant amplitude is 1.1-1.6×
  regulated, not ≥2×.
- **Discriminating conduct test:** regulated-PRB overnight de-load vs day max
  = 0.488/0.452 on cheap nights (hub overnight min < $22) vs 0.189/0.221 on
  dear nights (> $28), 2023/2025 — the within-day cycling is
  PRICE-RESPONSIVE. Only the COMMITMENT is self-determined.

**Design consequence (PREREG §8, committed before the solve):** the floor
half of the original hypothesis is already represented — the per-plant CAMPD
`_mustrun` bands (30-52 % of nameplate at the large regulated plants) sit far
ABOVE the measured LSL p50 0.182 and are always-on at sunk-contract fuel, so
a new bridge floor would be provably inert. The arm is the headroom half
only: `coal_prb_committed_dispatchable` (ScenarioConfig, default off) —
PRB/subbituminous plants excluded from the committed-band take-or-pay
discount; BIT/lignite keep it; `_mustrun` untouched.

## 3. Phase 3: the A/B

Arms (each 2023+2024+2025 in ONE bundle, rule 16; years chained sequentially
per rule 12 via `scripts/probes/_miso111_chain.sh`):

- **A (control)** `results/calibration/miso111_control_A` — the
  109b keeper recipe replayed at miso-111 HEAD, no delta.
- **B (arm)** `results/calibration/miso111_prbdispatch_B` — A +
  `coal_prb_committed_dispatchable=true`.

Guards G1-G6 pre-registered in PREREG §6; predictions P-A..P-E in §8.

### 3.1 Results

**Control integrity.** Arm A reproduces the committed 109b keeper at
L1 0.00000 % in 2023 and 2024 (max class-hour |diff| 0.000 MW). 2025 carries
0.030 % L1 HEAD drift (wind/CC/solar hour-level re-ties from the commits
main took between the keeper solve, sha e1b7335, and this session's HEAD)
with every gate statistic identical (COAL_PRB off-peak CV 0.0226 both arms,
cv_ratio 0.314). Every arm-B movement is therefore attributable to the
single flag. First arm-B chain attempt was OOM-killed by this session's own
concurrent benchmark rebuild (recorded for rule-12 hygiene: nothing heavy
runs beside a MISO year-solve on a 15 GB box); relaunched clean.

**D-1 COAL_PRB (the C7 gate), A → B:**

| year | profile_r | model off-peak CV | actual | cv_ratio | verdict |
|---|---|---|---|---|---|
| 2023 | 0.988 → 0.990 | 0.072 → 0.128 | 0.155 | **0.466 → 0.828** | FAIL → **PASS** |
| 2024 | 0.978 → 0.988 | 0.058 → 0.125 | 0.121 | **0.475 → 1.028** | FAIL → **PASS** |
| 2025 | 0.971 → 0.967 | 0.023 → 0.030 | 0.074 | **0.314 → 0.411** | FAIL → FAIL |

**C-series, arm B:** C1 **14/16 (free 10/12)** — the two flips are both
COAL_PRB volume: **−8.77 TWh (2023)** and **−14.97 TWh (2024)** against a
±8 TWh tolerance (control: +2.02/+1.86). The displaced energy lands on
CC_REGULAR (+3.4/+4.2), imports (+2.8/+4.1), CT_PEAKER (+1.8/+4.4), CC_CHP
and ST_GAS — all of which stay in band. C2 PASS; C3a improves in the caveat
year (2025 −14.2 → −13.5 %) and 2023/24 stay in tolerance; C3b PASS; C3c
unchanged (the ledgered tail); C4 PASS; C8 PASS with COAL_PRB carrying zero
forced rows in both arms; COAL_BIT is untouched (off-peak CV
0.036/0.029/0.032 vs control 0.036/0.026/0.033 — no overshoot).

## 4. Adjudication — REJECTED on pre-registered guards G1 + G2

- **G1 (C7 all three years): FAIL.** 2025 lands at 0.411 — the improvement
  direction is real (+0.10 over control) but the pre-registered P-B risk
  materialized: the model's overnight price floor keeps most of the PRB
  band inframarginal at night in 2025, and interleaving with gas-CC econ
  tranches buys only part of the gap. The PREREG said in advance that a
  2023/2024-only improvement reproduces miso-102 and fails; it did.
- **G2 (C1 16/16): FAIL — and prediction P-C is FALSIFIED, stated plainly.**
  The scoped repricing shed far more volume than the miso-102-scaled
  estimate: the committed-band discount is carrying **~9-15 TWh/yr of real
  stay-online self-commitment energy** that the `_mustrun` band alone does
  not carry. Removing the discount deletes it — the miso-102 objection
  reproduced at PRB scale, now precisely sized per year.
- G3 (COAL_BIT): PASS by construction. G4 (prices): PASS — C3a improved,
  nothing regressed. G5: no floors added, D-2 clean. G6: both arms
  registered, matrix cell stamped R.

**Keeper decision: NOT promoted; `2026-07-31-miso-109b-hy-level` stays.**
The owner's standing grant (2026-07-31, in-session: structural-integrity
improvement may promote even with gate regression) was weighed and does NOT
apply: arm B trades one structural infidelity (a byte-flat committed band)
for another (a fleet that decommits 15 TWh of coal reality kept burning —
the very conduct SOM Table 7 documents and rule 1 protects). It is not the
most faithful run producible; it is half of one.

**What the A/B establishes (the lane's sharpest statement yet):** reality's
regulated PRB night level within committed runs is **0.62 × HSL** — BETWEEN
the model's mustrun band (~0.46) and its full committed stack (~0.92). A
single committed band at a single price cannot hold that level: discounted,
it pins at 0.92 (the C7 flatness); at SRMC, it drops to 0.46 on every cheap
night (the C1 volume hole). The committed band needs a **measured split**:
a hold-through slice (the fraction of the band reality keeps loaded through
cheap nights — keeps the contract discount) and a cycling slice (bids full
SRMC). Both slice sizes are measurable from the same CAMPD within-run
loading construction this session already built (night p50 vs day p50 of
loading-when-on, per plant) — a source-data derivation, not a residual fit.
That is the named successor lane (miso-112). The 2025 residual (0.411 vs
0.5) additionally needs the overnight price-formation defect (model
off-peak p10 $29.71 vs actual hub p10 $17.95; night HE0-3 model $27.8-35.3
vs actual $19.4-26.9 in BOTH miso-102 arms) — a separate, data-blocked lane
(miso-78/79 congestion; sub-hourly RT dispersion), not reopened here.

## 5. Rule-26 duties discharged

- Matrix cell `coal_prb_committed_dispatchable` MISO added (O at build time,
  finalized with the verdict in this session); `coal_takeorpay_committed`
  cell note NOT altered (its miso-102/103/104 adjudications stand).
- `docs/mechanism-testing-matrix.md` §5.4 header refreshed: the stale "C3b
  spread compression" target retired (C3b passes on the live scorer); the
  outage-grain ask relabelled defect-motivated.
- Both arms registered on the backcast dashboard in this session (rule 15).
