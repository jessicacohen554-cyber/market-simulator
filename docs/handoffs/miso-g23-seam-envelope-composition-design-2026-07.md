# MISO G-23 imports — the seam-envelope composition defect (uniform per-band derate vs merit-order ceiling): frozen diagnosis + charter (miso-73)

**Date:** 2026-07-18. **Lane:** G-23 imports — the last pre-named MISO lane
(sequenced last by the miso-71/72 sessions). **Baseline keeper:**
`2026-07-18-miso-72-winter` (bundle `results/calibration/miso72_winter_citygate`).
**Phase A status: FROZEN (derive-first, NO LP — every number below is measured
data, keeper-bundle arithmetic, or an offline replay of already-registered
series).** Run number: miso-73. Zero fitted parameters anywhere in this charter
(rules 1/11/13/23).

## 1. The FROZEN diagnosis

### 1a. The residual and its exact decomposition

The miso-72 keeper's net interchange (registered payload, import-positive TWh)
vs the measured EIA-930 total:

| year | model | actual | gap | MHEB firm block (model − meas) | priced seams (model − meas) |
|---|---|---|---|---|---|
| 2023 | +35.60 | +37.91 | −2.31 | 6.36 − 5.39 = **+0.97** | 29.24 − 32.52 = **−3.28** |
| 2024 | +18.50 | +23.08 | −4.58 | 4.65 − 3.00 = **+1.65** | 13.85 − 20.08 = **−6.23** |
| 2025 | +13.84 | +18.96 | −5.12 | 1.96 − (−0.99) = **+2.95** | 11.88 − 19.95 = **−8.07** |

The MHEB column is deterministic arithmetic (the Manitoba firm block is a
floor-frac-1.0 must-flow at the measured per-year firm MW 726/531/224,
`interchange_config.MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`), so the priced-seam
column is exact without a solve.

### 1b. Candidate causes tested offline — two REFUTED, one CONFIRMED

The model's own hourly hub price was reconstructed from the registered
payload's `lmpDeltaHr` array (model − actual hourly delta) + the measured hub
RT series, so every replay below carries the keeper's actual price level AND
shape. Offline band-clearing replays of the registered
`MISO_SEAM_LADDER_BY_YEAR` ladders (priced-seam net TWh, 2023/2024/2025):

| replay | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| measured DA, uncapped (P9) | +32.37 | +20.05 | +20.09 | reproduces measured (+32.5/+20.1/+20.0) |
| model price, uncapped | +34.22 | +21.97 | +19.54 | **price level/shape REFUTED** (moves ≤ ±2) |
| model price, envelope as true ceiling | +33.21 | +19.90 | +18.89 | envelope-as-designed REFUTED (trims 1–2) |
| model price, SIL 8,700 MW | 0 h binding | 0 h | 0 h | SIL REFUTED |
| model price, **uniform per-band derate** | **+29.35** | **+13.91** | **+11.76** | **solve is +29.24/+13.85/+11.88 — match ±0.12 TWh, all three years** |

The C3a price level — the reason this lane was sequenced last ("adds supply,
pulls C3a-2025 the wrong way") — is NOT the driver of the import shortfall:
even the 2025 reconstruction (annual mean −14 to −19 % below actual) moves the
ladder clearing by under 1 TWh, because the Q-Q rungs are widely spaced and
mostly deep in/out of the money.

### 1c. The confirmed mechanism of the defect

`transmission.inject_miso_seam_flow_limit` applies the measured (month ×
hour-of-day) deliverability envelope as a **uniform per-band availability
derate**: `frac = cap_t / interface_limit; availability[band_k, t] *= frac`
(mirrored on export `min_gen`). Under that composition the seam can reach its
envelope cap **only when ALL eight rungs clear** — i.e. only when the internal
price exceeds the ladder's MOST EXPENSIVE rung — which contradicts both the
injector's own documented intent ("the LP still clears its merit order *below*
the ceiling", "A high percentile keeps headroom above the median, so the
modeled seam price — not the cap — sets the typical hour") and the miso-46
ladder design's adjudicated premise ("Band capacities … untouched; every band
clears economically", `docs/multi-iso/miso-import-starvation-rootcause-2026-07.md`
§3). Measured severity on the PJM seam: the envelope frac averages
0.84/0.69/0.64 (2023/24/25) so the derate is live in essentially every hour;
under correct ceiling semantics the envelope would bind in 16/27/16 % of
hours, but the price clears all eight rungs (letting the uniform derate reach
the cap) in only 1.4/0.2/0.1 % of hours. Both directions are distorted:

- PJM imports suppressed **−5.6 / −8.3 / −8.9 TWh** (vs ceiling semantics);
- South exports suppressed **+2.8 / +2.6 / +3.1 TWh** (pushed toward zero).

The two partially cancel in the net-interchange total — which is why the
headline gap (−3.3/−6.2/−8.1 priced-seam) understates the per-seam distortion.
The defect became load-bearing when the miso-46 measured ladder widened the
rung range (e.g. 2023 PJM $13.40→$46.55); under the older near-flat spread
pricing the derate's price-depth distortion was small.

### 1d. Why this was invisible until now

The offline P9 validation in the derive script scores the ladder **uncapped**
against measured DA (its documented scope: "The live LP additionally applies
the measured per-seam deliverability envelopes"), so the derivation sanity
check could not see the composition. The solve-side totals were attributed to
the price level (miso-46 log: "C3a mean LMP is NOT expected to close…"), which
§1b now quantitatively refutes as the volume driver.

## 2. What this lane IS and IS NOT

- **IS:** a correctness fix restoring the adjudicated semantics of TWO
  already-accepted measured mechanisms (the Q-Q ladder and the deliverability
  envelope). Zero new data, zero new parameters, zero re-derivations — the
  registered ladder rungs, envelope percentile (p90 default), band grid, and
  firm block are all byte-unchanged.
- **IS NOT** an import floor: nothing is forced; every band still clears
  economically against the LP's own hourly price, and at trough prices even
  the base band backs off. The rejected `miso_firm_import_floor` stays
  rejected.
- **IS NOT** price-level compensation: the C3a level ledger (#1347 coal-offer
  level, trough shape) is untouched and no seam-side value moves in response
  to it (rules 1/13). The expected C3a *worsening* from restored supply is
  pre-declared in §4 as the rule-14 compensating-error signature.

## 3. The mechanism (FROZEN): `miso_seam_envelope_merit_cap`

One new `ScenarioConfig` bool (default **False** — replay fidelity for every
existing bundle), armed in the probe via the `prb_overrides` channel and
recorded in `run_config.json` (rule 24). When set,
`inject_miso_seam_flow_limit` applies the SAME envelope with **merit-order
(waterfall) semantics** instead of the uniform derate — import bands (k
1-based, band order = depth order = rung order, monotone by the Q-Q
construction):

    ub_k(t) = clip(cap_t − (k−1)·step, 0, step)        # availability multiplier ub_k/step
    Σ_k ub_k(t) = min(cap_t, interface_limit)           # the exact ceiling

with the export mirror on `min_gen` (`lb_k(t) = −clip(cap_t − (k−1)·step, 0,
step)`, composed via `maximum` so the cap can only reduce export, never force
it — unchanged composition rule). Given monotone rungs this is exactly
equivalent to a shared per-seam-hour `Σ_k P[band_k,t] ≤ cap_t` constraint row,
implemented availability-only (no new LP rows, no hour loops — pure vectorized
bound arithmetic). Cheap base rungs keep full width; the envelope's residual
falls on the expensive rungs — restoring the price-to-depth pairing the Q-Q
derivation defines (`pi_k` was derived at depth `L_k` on the FULL-width grid).

DOF: **zero new scalars, zero new measured entries** (both inputs already in
the miso-46 ledger). The flag is a composition-semantics gate, not a tunable.

## 4. Pre-registered expectations and bands

Offline fixed-price bound (ceiling replay at the base's own solved prices —
an UPPER bound, since the LP's equilibrium feedback lowers prices as imports
rise and backs marginal rungs off): priced-seam +33.2/+19.9/+18.9; net totals
(+ firm block) **+39.6 / +24.6 / +20.9** vs actual +37.9/+23.1/+19.0. The
solve should land between the base and this bound.

- **B1 (primary gate):** net interchange |model − actual| strictly improves
  in EVERY year (base 2.31/4.58/5.12 TWh); expected landing ≤ 2.5 TWh/year.
- **B2 (per-seam, the deliverable):** each priced seam's annual net moves
  toward measured in every year (PJM up toward +40.9/+32.3/+28.0; South
  export up toward −9.4/−11.8/−8.9; SPP toward +1.0/−0.4/+1.0), scored by
  the new per-seam validation script (§6).
- **B3 (honest, rule 14):** C3a moves DOWN (net supply +4/+6/+7 TWh) — watch
  band ≤ 2.5 pp deeper per year (2023 +0.1 → ~−2; 2024 −7.3 → ~−9.5;
  2025 −13.7 → ~−16). Pre-adjudicated as the compensating-error signature:
  the suppressed seam was masking the domestic price-level miss, and the
  re-exposed residual re-attributes to the #1347 / trough-shape ledger. NOT
  a rejection reason, NOT to be offset by any tuning in this lane.
- **B4 (hard veto):** C3b ≤ 0.20 absolute, all years (standing shape veto;
  2025 base 0.183 — headroom 0.017, the riskiest gate; see R1).
- **B5 (watch):** C3c 1/7/1 disclosed as-is; the 2025 leg-(b) deep-tail
  lower bound stays honestly ledgered — this lane claims NO tail closure and
  will not chase one. Restored mid-price imports may shave rare model tail
  hours; any movement is disclosed, not gated here.
- **B6:** no new floors (the mechanism carries no floor id; export caps only
  reduce export); D-2 mechanism rows byte-comparable to the keeper's;
  C6/C7/C8 expected PASS with the same ST_GAS grounded notes.
- **The MHEB wedge REMAINS by construction** (+0.97/+1.65/+2.95 model-over,
  §1a): after the fix the visible net-interchange residual should be
  approximately the firm block's over-import — that is the NEXT charter
  (§8), not a miss of this one.

## 5. R-criteria (pre-declared refutations — the ONLY fallbacks)

- **R1 — C3b veto:** if C3b > 0.20 in any year, the run is registered
  (rule 15, both arms) but NOT recommended as keeper; the flag stays in code
  default-off, and the finding re-attributes to the trough/level shape ledger
  as an open root-cause. No percentile sweep, no ladder edit, no offsetting
  mechanism may be added in response (rules 13/23/26).
- **R2 — inertness:** if main − base moves 2025 net interchange by
  < +1.0 TWh, the §1c attribution missed a binding structure — STOP and
  re-diagnose from the solved band flows/duals; do not tune anything.
- **R3 — overshoot:** if any year's net interchange lands ABOVE the offline
  fixed-price bound (+39.6/+24.6/+20.9) by > 1.0 TWh, the ceiling is not
  binding as designed — an implementation defect, stop-the-line, fix,
  re-solve.
- **R4 — no fabricated structure:** no new scarcity prints attributable to
  the export restoration (no chase of the out-of-representation SETEX $1,070
  print; Jan-2024 stays not-a-reserve-event); the Heather-window per-zone
  fidelity (miso-72's deliverable) must not regress materially (watch,
  disclose).
- **R5 — honesty:** the deliverable is the interchange structure (§6), NOT
  the price criteria; no C3a/C3b/C3c movement is quoted as validation of this
  mechanism.

## 6. Deliverable + validation (pre-named)

`scripts/miso73_perseam_validate.py` (the `miso72_perzone_validate` pattern):
from the solved bundle's dispatch parquet, sum the `_refimp_`/`_refexp_` band
rows per seam (+ the firm block for MHEB) and score, per seam and year,
against the measured EIA-930 pooled seam flows:

1. annual net TWh (B2 bands above),
2. monthly net-flow fidelity (mean |model − measured| monthly GWh, must
   improve on PJM and South vs the base in every year),
3. flow-duration RMSE (must improve on PJM and South vs the base).

Hourly correlation is NOT a target (the measured flow is price-decorrelated,
r ≈ +0.06 — the duration curve is the honest reproducible structure; miso-46
root-cause doc §3).

## 7. Phase B build/probe/register plan (ordered)

1. `ScenarioConfig.miso_seam_envelope_merit_cap` (default False, docstring
   citing this charter) + the waterfall branch in
   `inject_miso_seam_flow_limit` (both directions) + unit tests
   (trivial-case-first: one seam, 8 bands, constant cap — per-band waterfall
   bounds, exact ceiling total, export mirror, flag-off byte-identity,
   cap ≥ limit no-op, cap = 0 zero).
2. Run the existing seam test files + the new tests.
3. Probe driver `scripts/run_miso73_seam_probe.py` (replays the
   `miso72_winter_citygate` bundle meta via `replay_keeper.build_kwargs`;
   `--merit-cap` arms the flag via `prb_overrides`; base = byte-faithful
   keeper replay) + chain `scripts/probes/_miso73_chain.sh` (the _miso72
   idempotent per-year + `--reuse-solved` pattern; `MALLOC_ARENA_MAX=1
   MARKET_SIM_HIGHS_THREADS=1`; base then main, years SEQUENTIAL, rule 12).
4. **Commit ALL code before solving** (a dirty tree under src/scripts/data
   disables reuse and OOMs).
5. Solve base, then main (~25 min each on the 15.8 GB box). Never on CI.
6. `report_run` scoring + §6 per-seam validation + R-criteria reads.
7. Rule 15/16 registration, both runs, all three years, one bundle each:
   `dashboard_add_run` → `gen_miso73_attestation.py` (seeded from the miso-72
   attestation + `build_dof_ledger.py`; new DOF branch for the flag — a
   composition gate, zero scalars) → `legitimacy_diagnostics.py --json-out` →
   `calibration_verdict.py --write-metrics` →
   `check_registry_payload_parity.py` → `build_manifest.py` → calibration-log
   entry. MISO registry is AT 15: adding 2 runs prunes the 2 oldest
   (sidecar + `runs/<id>.js` pairs). Push via `mcp__github__push_files`,
   blob-verify every file ≥ 300 lines (rule 27).
8. Keeper recommendation per rules 1/11 (most structurally faithful — the
   accurate composition of two measured structures); swap is OWNER-ONLY.

## 8. Out-of-scope ledger (recorded here so the next charters start measured)

- **MHEB two-way seam (the next import charter, NOT folded in — one mechanism
  per probe):** the firm block is import-only and annual-flat, but measured
  MHEB is a genuinely two-way seasonal hydro seam — monthly mean import MW
  (import-positive):

  | | J | F | M | A | M | J | J | A | S | O | N | D | exp-hours |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | 2023 | 922 | 672 | 632 | 1006 | 1723 | 1127 | 1132 | 790 | 368 | −254 | −551 | −193 | 25 % |
  | 2024 | −208 | −113 | −482 | −242 | 59 | 1011 | 1050 | 1175 | 1094 | 877 | 186 | −284 | 39 % |
  | 2025 | 54 | −99 | 206 | 502 | 677 | 265 | −405 | −430 | −401 | −300 | −582 | −839 | 58 % |

  (freshet/summer import peak, winter export to winter-peaking Manitoba,
  drought-2025 net-export flip to −0.99 TWh; flow extremes +2,827/−1,417 MW;
  price-decorrelated r ≈ 0.09–0.31 — the same scheduled-seam signature the
  Q-Q ladder construction was built for). Candidate: a fourth priced seam
  (`MISO_SEAM_DIBA["Manitoba"] = ("MHEB",)`) REPLACING the firm block.
- **IESO seam split** off the pooled PJM seam — needs an HOEP intake;
  recorded option (miso-46 doc §4a), untouched.
- **PJM-ISO's `inject_pjm_seam_flow_limit` carries the IDENTICAL uniform
  derate** ("The mechanism is identical to the MISO function") composed with
  `PJM_SEAM_LADDER` — the same defect class, all-ISO correctness follow-up in
  its own lane (will not move MISO; the PJM keeper's flags decide exposure
  there).
- C3a level ledger #1347 (coal-offer level in dear-gas years, trough shape);
  C3c-2025 leg-(b) honest lower bound; the North/Central zonal topology
  split; the all-ISO `gas_daily_shape_factors` interp fix — all separate,
  unchanged by this lane.
- **No sweeps:** `miso_seam_flow_percentile` stays default (p90); no
  envelope re-derivation; no ladder value edits; no new congestion
  mechanism.
