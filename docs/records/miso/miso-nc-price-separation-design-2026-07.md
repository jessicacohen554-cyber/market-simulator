# miso-76 — Midwest (North/Central) zonal price-separation lane: Phase-A diagnosis + frozen design charter

**Date:** 2026-07-19 (Phase A, derive-only — NO LP was solved for this
document). **Lane:** post-miso-75, owner-selected 2026-07-19 (the owner
DECLINED the determination-path ledger conversion — see
`docs/handoffs/miso-76-determination-proposal-2026-07.md`, which remains on
record un-applied — and chose lane B, this charter). **Design discipline:**
this charter is committed BEFORE any build; the bands (§5) and refutation
criteria (§6) are pre-registered and may not be revised after the first LP
solve (miso-72/73/74/75 precedent). **Model per rule 27: Fable/Opus.**

**Probe evidence (derive-only, committed, reproducible):**
- `scripts/probes/_miso76_separation_anatomy.py` — measured hub separation vs
  the flat model pool (§1a, §1b).
- `scripts/probes/_miso76_component_decomposition.py` — congestion-vs-loss
  decomposition of the hub spreads (§1c).
- `scripts/probes/_miso76_bc_boundary_rank.py` — where measured DA congestion
  sits, by model-zone boundary (§2b, the M1 refutation).

---

## 0. The problem this lane owns (and what it does NOT touch)

The six-zone MISO build's five Midwest zones are **price-uniform in the
model** — the internal bilateral links L1–L6 carry deliberately non-binding
40 GW placeholder TTCs, and the per-zone LOLE CIL/CEL envelopes bind only
degenerately (Gate-2 finding: cap-touching with $0 duals). Two standing
consequences:

1. The measured **persistent intra-Midwest separation** (Indiana $3–5/MWh
   above Illinois in annual mean, every year, both markets) does not exist in
   the model — all ten intra-Midwest mean orderings were wrong at Gate-2, and
   the miso-75 keeper's Midwest annual-mean span is **$0.14/$0.38/$0.38**
   (2023/24/25) vs measured **$3.6/$4.3/$5.5** (Indiana−Illinois RT).
2. The miso-72 winter Chicago-citygate overlay smears its repricing across
   the whole uniform pool — the disclosed **~+$2 full-January MAE broadening
   in Indiana/East/West** (miso-72 log entry) — because nothing lets the
   Chicago-hub zones carry their own winter marginal price.

**Out of scope (untouched, own lanes):** the irreducible C3a-2025/C3c
scarcity tail (ledgered Phase-A finding, miso-71/74 — nothing here chases
it); the PJM uniform-derate merit-cap twin; the all-ISO `gas_daily_shape`
interp fix; the D1 Michigan(Z7)/Wisconsin(Z2) split (blocked on a load
split; the East≈Indiana spread is the smallest pair at $1.7–2.9).

## 1. Phase-A diagnosis (derive-only)

### 1a. The separation is real, persistent — and DA-visible (in representation)

From the committed D6 hub actuals (probe 1). Annual means, RT:

| year | MINN | ILLINOIS | INDIANA | MICHIGAN |
|---|---|---|---|---|
| 2023 | 28.75 | 28.20 | **31.79** | 29.96 |
| 2024 | 27.43 | 26.53 | **30.80** | 29.83 |
| 2025 | 40.19 | 37.35 | 42.85 | **42.88** |

The DA annual means carry the SAME structure (Indiana−Illinois DA: $3.97 /
$3.78 / $5.01). This is the decisive admissibility fact: **the day-ahead
market — an hourly, commitment-aware, full-network optimization, the closest
real-world analogue of our LP — prices this separation persistently.** Unlike
the C3c scarcity tail (RT-only 5-minute formations, out of representation),
intra-Midwest separation is exactly the kind of structure an hourly zonal LP
is supposed to produce. Hourly spread stats vs INDIANA.HUB (RT):

| pair | year | mean | MAE | p95 | \|Δ\|>$10 |
|---|---|---|---|---|---|
| MINN−IND | 2023/24/25 | −3.0/−3.4/−2.7 | 9.7/9.3/11.7 | 37/33/41 | 25/26/34 % |
| ILL−IND | 2023/24/25 | −3.6/−4.3/−5.5 | 4.4/5.0/6.0 | 19/19/24 | 11/13/18 % |
| MICH−IND | 2023/24/25 | −1.8/−1.0/+0.0 | 2.7/2.7/2.4 | 11/10/9 | 6/5/4 % |

Monthly texture (probe 1): Jan-2024 (Heather) MINN 43.5 vs ILLINOIS 33.0
while Indiana sits at 40.5; Apr-2025 Indiana−Illinois +$11.7; Minnesota flips
sign seasonally (deep discount in wind-flush months, premium in Jan-2024 /
Aug-2023). The Minnesota leg is the wind-belt congestion signature (highest
MAE and tail); the Illinois leg is the persistent load-east premium.

### 1b. The model is a flat pool

miso-75 keeper payload per-zone annual means: Midwest span $0.14/$0.38/$0.38.
The C3a/C3b criteria are load-weighted across zones, so the flat pool also
mis-weights the load-heavy expensive east (East+Indiana = 37.6 % of load) vs
the cheap west — part of the broad price-level story, disclosed as a B3 watch
(never the objective).

### 1c. Decomposition: congestion ~62–105 %, marginal losses $0.2–2.9

MISO publishes per-node LMP components (MCC congestion / MLC loss) in its
daily ex-post reports. Sampled decomposition (probe 2; 15th of each month,
36 days/yr, DA):

| pair | year | dLMP | dMCC (congestion) | dMLC (loss) |
|---|---|---|---|---|
| MINN−IND | 2023/24/25 | −6.2/−7.6/−6.7 | −4.8/−4.7/−5.0 | −1.4/−2.9/−1.8 |
| ILL−IND | 2023/24/25 | −3.9/−4.9/−8.1 | −2.6/−3.0/−5.8 | −1.2/−1.9/−2.3 |
| MICH−IND | 2023/24/25 | −1.7/−2.9/−1.8 | −1.5/−2.6/−1.9 | −0.2/−0.2/+0.1 |

Both components are real: congestion dominates (62–105 %), and the loss
component is a persistent $1–3 on the West and Illinois legs — consistent
with Gate-2's prediction that $1–2 of every spread is marginal losses the
`td_loss_factor = 0` model cannot show by design.

## 2. Measured-data survey (what exists, what does not)

### 2a. Exists (public, train-window, forward-regenerating)

| data | where | use |
|---|---|---|
| Hub RT/DA hourly LMPs | committed D6 parquet | anatomy + validation bands (have) |
| Per-node LMP components (LMP/MCC/MLC) | `docs.misoenergy.org/marketreports/YYYYMMDD_{da_expost,rt}_lmp*.csv` daily | the loss-surface derive source + decomposition validation (Phase-A2 intake, new `lmp-components` datatype) |
| Binding-constraints history (constraint, hour, shadow price, TCDC curve) | `YYYY_{da,rt}_bc_HIST.csv` annual consolidations | congestion location/timing VALIDATION only — shadow prices are the answer class (rule 13), never inputs |
| Constraint→control-area registry (From/To CA per binding branch) | daily `*_bcsf.xls` supplemental + the CA field embedded in bc_HIST branch names | measured constraint→zone-boundary crosswalk |
| RDT binding record | `data/raw/transfer-constraint-binding/MISO` (in repo) | already modeled (L7 pair + TCDC pricing) |
| SOM top-congestion tables | `data/raw/MISO/*SOM*.pdf` (in repo) | cross-check of the recurring-constraint ranking |

### 2b. Does NOT exist publicly: flowgate MW limits

The bc/bcsf record carries **no MW limit and no flow** — only events, shadow
prices, and the TCDC demand-curve caps ($400–2,000). MTEP publishes select
ratings only; OASIS AFC feasibility is unknown (contingent investigation,
§3 M4). And the measured congestion *location* (probe 3, Σ|shadow-price| by
zone boundary, DA): **West-internal 20–26 %, external/seam 20–32 %,
Plains-internal 10–15 %, Indiana-internal 7–11 % — clean between-model-zone
corridor pairs barely register** (West|Plains peaks at 0.8 %). Real Midwest
congestion is distributed branch-level congestion WITHIN zones plus seam
loop-flow, whose zonal price effect operates through network shift factors a
6-zone reduced network does not carry.

## 3. Mechanism adjudication (pre-registered)

- **M1 — corridor MW caps on L1–L6 derived from the binding record:
  REFUTED at the data layer.** No published MW limits exist (§2b), and the
  measured congestion does not sit on the model's corridors — any per-link
  cap would be an invented apportionment, exactly what scope decision D4
  refused, and any cap *derived to reproduce the observed spreads* would be
  residual-fitting (rules 13/26). Not built.
- **M2 — measured "hurdle rates" set from the observed MCC spreads:
  REFUTED.** The MCC spread is a component of the scored price itself;
  feeding it back as an inter-zonal friction is pinning the backcast answer
  (C6 assertions 2/3). Not built, in any form.
- **M3 — marginal-loss physics in the LP (THE LANE'S BUILD, §4).**
  Admissible: marginal losses are network physics; the derive target is the
  **dimensionless marginal delivery-factor surface** (MLC/LMP), a stable
  physical network property that regenerates for a forward year and responds
  to changed conditions (its $/MWh expression scales with the price level).
  It enters the LP as physics (transported energy costs MWh), so prices stay
  duals (rule 4) — never as a price adder. Closes the measured dMLC
  component ($1–3 on the West/Illinois legs, ~20–38 % of the persistent
  spread) and gives the interior its first distance metric, letting the PJM
  seam pull and the Chicago-zone winter gas express locationally (report-only
  hypotheses B2/B4 — never gated, never tuned toward).
- **M4 — OASIS AFC / flowgate-rating intake: CONTINGENT.** If a measured
  per-flowgate MW-limit series proves publicly fetchable, the congestion
  component becomes representable and gets its OWN charter. Until then the
  congestion component beyond existing structure (CIL/CEL + RDT + seams) is a
  **documented data-blocked limitation** — recorded, not faked.

## 4. M3 design (build gated on this frozen charter)

- **Flag:** `ScenarioConfig.miso_zonal_loss_surface` (tier 3, default OFF,
  byte-identical off — MISO-scoped per rule 24; the surface is derived from
  MISO's own published components).
- **Derive script (frozen, rule 23):** `scripts/data/derive_miso_loss_surface.py`
  reads the Phase-A2 `lmp-components` clean parquet (2023–2025 hub
  LMP/MCC/MLC) and emits a per-zone (month) marginal delivery-factor
  deviation surface (dimensionless; hub→zone per the D6 crosswalk; Plains,
  hub-less, carries the geographic interpolation of its neighbors,
  documented). Re-derives ONLY on source-data updates.
- **LP implementation (build-time choice, pre-registered acceptance test):**
  per-link loss fractions or per-zone delivery factors in the energy
  balance — whichever implementation is chosen must pass the OFFLINE
  acceptance test before any full solve: at the keeper's typical flow
  pattern, the implied zonal dual ratios reproduce the measured mean dMLC
  per hub-pair within the B1 band. No fitted scalars: the surface is the
  measured object; DOF +1 measured-physical, `n_scalars 0`.
- **Unit tests:** off-state byte-identity; toy 2-zone LP separates by the
  loss factor; derive-script determinism.

## 5. Pre-registered bands (scored on the mechanism-only A/B: main − same-box base)

- **B1 (THE deliverable):** with M3 on, each benchmarked Midwest hub-pair's
  model annual-mean separation lands within **[0.5×, 1.5×] of the measured
  mean dMLC** for that pair-year (pairs vs Indiana: West, Illinois, East).
  The loss surface must reproduce the LOSS component — claiming the whole
  spread would be fabrication.
- **B2 (report-only):** total pair separation including knock-on effects
  (seam pull, winter gas localization) — reported against the measured total,
  never gated, never tuned toward.
- **B3 (rule-14 disclosure):** C3a may move either way as the load-weighted
  mean re-weights; watch band **|ΔC3a| ≤ 1.5 pp per year**, disclosed. Any
  C3a improvement is a side effect, NOT validation (R5).
- **B4 (report-only):** miso-72's January per-zone MAE in Indiana/East/West —
  hypothesis: partial reduction as Chicago-hub winter gas prices
  differentially. Reported, not gated.

## 6. Pre-registered refutation criteria

- **R1 (the veto, pre-named riskiest gate):** C3b ≤ 0.20 every year. The
  keeper sits at 0.198 in 2025 — **0.002 headroom**. If the loss physics
  trips the veto, the run is a REJECTED PROBE (registered as such per rule
  15) and the interaction is diagnosed; nothing is re-tuned to un-trip it.
- **R2 (no fabricated separation):** no pair-year's model annual-mean
  separation may exceed **1.0× its measured RT total mean** separation.
- **R3 (inertness):** if every benchmarked pair-year moves < $0.30, the
  mechanism is inert → rejected (wiring defect or immaterial surface).
- **R4 (no criterion regression):** C1/C2/C4/C5a/C6/C7/C8 hold on the A/B;
  NO new floors (loss physics carries no floor-mechanism id; D-2/D-4 regen
  adds no row).
- **R5 (honesty):** no price criterion movement is quoted as validation; the
  lane's success claim is B1 and only B1.

## 7. Phase plan

1. **A (this document + probes 1–3): DONE** — committed before any build.
2. **A2 — data intake** (data-intake skill, schema-first, train-window
   guard): (i) new `lmp-components` datatype — daily
   `*_da_expost_lmp.csv` / `*_rt_lmp_final.csv` → per-hub hourly
   LMP/MCC/MLC parquet, 2023–2025; (ii) extend `transfer-constraint-binding`
   with the annual `YYYY_{da,rt}_bc_HIST.csv` source mirrors (validation
   layer only).
3. **A3 — derive + offline acceptance:** `derive_miso_loss_surface.py` +
   the §4 acceptance test (no LP).
4. **B — LP build** (core infra, rule 27 model assignment; commit ALL code
   before solving, rule 12).
5. **C — solve & register:** main + same-box base, full span 2023+2024+2025,
   per-year + `--reuse-solved`, years sequential, both arms registered
   (rules 12/15/16); owner adjudicates any keeper swap (rule 27).

## 8. Out-of-scope ledger (restated)

C3a-2025/C3c irreducible tail (untouched — B3 movement is disclosure, not
closure); M4 OASIS AFC feasibility (contingent, own charter); D1 Z2/Z7
split; PJM merit-cap twin; all-ISO `gas_daily_shape` interp fix; the
congestion component of intra-Midwest separation beyond existing structure
(data-blocked, §2b/§3 M4 — documented, not faked).
