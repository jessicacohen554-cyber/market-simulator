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

(TO BE FILLED FROM THE SOLVES)

## 4. Adjudication

(TO BE FILLED)

## 5. Rule-26 duties discharged

- Matrix cell `coal_prb_committed_dispatchable` MISO added (O at build time,
  finalized with the verdict in this session); `coal_takeorpay_committed`
  cell note NOT altered (its miso-102/103/104 adjudications stand).
- `docs/mechanism-testing-matrix.md` §5.4 header refreshed: the stale "C3b
  spread compression" target retired (C3b passes on the live scorer); the
  outage-grain ask relabelled defect-motivated.
- Both arms registered on the backcast dashboard in this session (rule 15).
