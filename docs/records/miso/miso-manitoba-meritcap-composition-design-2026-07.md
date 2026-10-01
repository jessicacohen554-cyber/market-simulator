# MISO {Manitoba two-way seam + seam-envelope merit-cap} composition — closing the net-interchange volume without breaking the C3b veto: frozen diagnosis + charter (miso-75)

**Date:** 2026-07-18. **Lane:** the pre-registered composition partner of the
miso-73 merit-cap and the miso-74 Manitoba seam (miso-74 charter §3d/§8, miso-73
charter §5 R1). **Baseline keeper:** `2026-07-18-miso-74-manitoba-seam` (bundle
`results/calibration/miso74_manitoba_seam`). **Phase A status: FROZEN
(derive-first, NO LP — every number below is measured data, keeper-bundle
arithmetic, or an offline replay of already-registered series; both mechanisms
are already BUILT + unit-tested and merged).** Run number: miso-75. Zero fitted
parameters anywhere in this charter (rules 1/11/13/23).

This is a **composition probe of two frozen structural mechanisms**, not a new
mechanism. No new code, no new data, no new parameter — the deliverable is the
verdict of turning **both** already-merged flags on together.

## 0. The composition in one line

`miso_manitoba_seam` (keeper-on) **+** `miso_seam_envelope_merit_cap` (miso-73,
default-off, R1-vetoed as a standalone) — both frozen, both flowing through the
**same** `inject_miso_seam_flow_limit` path (no fork, §2) — to test whether the
Manitoba seam's 2025 supply *removal* opens enough C3b headroom for the merit
cap to restore the priced-seam import volume **without** tripping the C3b ≤ 0.20
veto that killed it standalone.

## 1. The FROZEN diagnosis

### 1a. The residual this lane targets — the net-interchange volume

The miso-74 keeper is the most structurally faithful MISO run to date (four
measured seams, zero fitted scalars) and PASSes C3b, but it carries a
**net-interchange volume miss** as a pre-registered rule-14 exposure. The
keeper's total net interchange vs the measured EIA-930 total (import-positive
TWh), reproduced from the registered payloads:

| year | keeper model | actual | gap (model − actual) TWh |
|---|---|---|---|
| 2023 | ~+32.4 | +37.9 | **−5.46** |
| 2024 | ~+15.7 | +23.1 | **−7.38** |
| 2025 | ~+11.7 | +19.0 | **−7.27** |

miso-74 pre-registered (§B3) that replacing the firm block with the measured
two-way seam would make this *visible* gap worse (−2.31/−4.58/−5.12 →
−5.46/−7.38/−7.27) precisely because the firm block's over-import
(+0.97/+1.65/+2.95 TWh) had been **masking the priced-seam under-import**. That
under-import is the miso-73 merit-cap defect: the uniform per-band derate on the
PJM/SPP/South seams suppresses PJM imports −5.6/−8.3/−8.9 TWh and South exports
+2.8/+2.6/+3.1 TWh (2023/24/25; miso-73 §1c), which partially cancel in the net
but leave the total short. The Manitoba seam removed the mask; the merit cap is
the mechanism that closes the volume.

### 1b. Why the merit cap was R1-vetoed as a standalone — and why the veto may lift now

The miso-73 merit-cap fix (waterfall ceiling replacing the uniform derate,
restoring the Q-Q ladder's price-to-depth pairing) was **registered but
R1-vetoed as a standalone** on the miso-72 base: restoring ~5–8 TWh/yr of
mid-price priced-seam import flattened **C3b-2025 0.183 → 0.200** (added
mid-merit supply into the price-duration curve), landing exactly on the 0.20
shape veto. Everything else improved; only the C3b headroom killed it (miso-73
§5 R1, this session's registered miso-73 arms).

The miso-74 Manitoba seam changes the base the merit cap composes onto. Manitoba
**removes ~2.95 TWh of 2025 net supply** (firm block +1.96 TWh import → measured
seam −0.99 TWh net export) and, as a side effect, **un-flattened C3b-2025 0.183
→ 0.181** — opening **0.019 pp of headroom** below the 0.20 veto. The
pre-declared composition hypothesis (miso-74 §3d.2): Manitoba's supply removal
*offsets* the merit cap's C3b flattening, so {both on} may restore the
priced-seam volume **and** keep C3b ≤ 0.20.

### 1c. The base C3b ledger (the risk surface, frozen from the miso-74 keeper)

| year | keeper C3b | headroom to 0.20 |
|---|---|---|
| 2023 | 0.080 | 0.120 |
| 2024 | 0.124 | 0.076 |
| 2025 | **0.181** | **0.019 — the riskiest gate** |

2025 is the only year at material risk. The standalone merit cap added ~+0.017
to C3b-2025 on the miso-72 base; whether Manitoba's export-leg supply removal
absorbs that on the miso-74 base is exactly what the probe measures — it is
**not** predictable from arithmetic (the price-duration curve's response to the
combined supply shift is an equilibrium effect). Pre-registered R1 gates it.

## 2. The mechanism (FROZEN): both flags, one shared path, no fork

Both mechanisms are already merged, default-off, and compose with **zero new
code**:

1. `miso_manitoba_seam=True` (the miso-74 keeper's setting, carried in the
   keeper bundle's `prb_overrides`) appends the Manitoba (MHEB) seam's 8 import
   + 8 export bands via `build_reference_price_node(extra_neighbors=
   [MISO_MANITOBA_SEAM_SPEC])` and suppresses the firm block. `MISO_SEAM_DIBA
   ["Manitoba"]=("MHEB",)` and `MISO_SEAM_LADDER_BY_YEAR["Manitoba"]` are present
   unconditionally, so the measured (month × hod) MHEB deliverability envelope
   auto-covers the seam.
2. `miso_seam_envelope_merit_cap=True` (miso-73, the delta this probe adds)
   selects the **waterfall** composition semantics inside
   `inject_miso_seam_flow_limit`: `ub_k = clip(cap − (k−1)·step, 0, step)` on the
   import bands, the export mirror on `min_gen`, `Σ_k ub_k = min(cap, limit)`
   exactly. Cheap base rungs keep full width; the envelope's residual falls on
   the expensive rungs.

**No fork.** `inject_miso_seam_flow_limit` iterates **every** seam in the
measured envelope dict (`for name, cap in env.items()`) with the single
`merit_cap` flag threaded from `getattr(config, "miso_seam_envelope_merit_cap")`
at both the import and export call sites (`scripts/run_calibration.py`
L2310–2312, L2336–2343). When Manitoba's bands exist (flag 1 on), the merit-cap
waterfall (flag 2 on) applies to the Manitoba seam **and** the PJM/SPP/South
seams through the identical arithmetic. Verified this session in
`model/transmission.py` L3568–3644.

### 2a. DOF

**Zero new scalars, zero new measured entries.** Both flags are
composition-semantics gates over already-ledgered inputs (the Q-Q ladders and
the deliverability envelopes are in the miso-46 ledger; Manitoba's ladder is in
the miso-74 ledger). Net DOF change vs the keeper: **0** (the merit cap adds no
parameter; it is a semantics selection). The keeper's DOF ledger (27 free / 2
identified) carries unchanged.

## 3. The A/B (pre-registered, same-box)

- **base** = the miso-74 keeper {Manitoba only} recipe, re-solved same-box at
  HEAD (`miso_seam_envelope_merit_cap=False`, keeper default). This is the drift
  control; `main − base` isolates the merit-cap semantics on the Manitoba base.
- **main** = {Manitoba + merit-cap} (`miso_seam_envelope_merit_cap=True` added
  via `prb_overrides`).

Both replay the **miso-74 keeper bundle** (`results/calibration/
miso74_manitoba_seam`) via `replay_keeper.build_kwargs`, so the full keeper
structure (including `miso_manitoba_seam`) rides through `prb_overrides` and the
only delta between the arms is the merit-cap flag. All three years
2023/2024/2025 in one bundle each (rule 16). MISO has no calibration-complete
marker — 2023–2025 only (rule 22).

## 4. Pre-registered expectations and bands

Offline fixed-price bound (merit-cap restore ≈ PJM +5.6/+8.3/+8.9 imports −
South +2.8/+2.6/+3.1 exports = **net +2.8/+5.7/+5.8 TWh** toward measured; an
UPPER bound since equilibrium feedback lowers prices as imports rise and backs
marginal rungs off): the composition net-interchange gap should move from base
−5.46/−7.38/−7.27 toward **≈ −2.7 / −1.7 / −1.5 TWh**. The solve should land
between the base and this bound.

- **B1 (primary gate — the deliverable):** net interchange |model − actual|
  **strictly improves in EVERY year** vs the base (5.46/7.38/7.27 TWh); expected
  landing ≤ 3.0 TWh/year. This is the volume the composition exists to close.
- **B2 (per-seam, the structural deliverable):** each priced seam's annual net
  moves **toward** measured in every year — PJM import up, South export up (more
  negative), SPP ≈flat — scored by `scripts/miso73_perseam_validate.py` (already
  covers all four seams incl. Manitoba). Monthly net-flow fidelity and
  flow-duration RMSE on PJM and South improve vs base.
- **B3 (rule-14 honest):** C3a moves **DOWN** (net supply up ~+2.8/+5.7/+5.8
  TWh) — watch band ≤ ~2.5 pp deeper per year; 2025 base −13.3% → toward ~−15%.
  Pre-adjudicated as the compensating-error signature (the suppressed seam was
  masking the domestic price-level miss, which re-attributes to the irreducible
  scarcity-tail ledger, miso-74 §0). **NOT a rejection reason, NOT to be offset
  by any tuning in this lane** (rules 11/14).
- **B4 (HARD VETO = R1):** **C3b ≤ 0.20 absolute, ALL years** (standing shape
  veto). Base 0.080/0.124/**0.181**; 2025 headroom 0.019 is the whole risk. See
  R1 — this gate decides the verdict.
- **B5 (watch):** C3c disclosed as-is (base 0/6/1 vs RT 30/37/88); this lane
  claims NO tail closure. Restored mid-price imports may shave rare model tail
  hours; any movement is disclosed, not gated.
- **B6 (C5a watch):** CO2 may tick from the restored import mix; expected within
  the C5a band; disclosed.
- **B7 (no new floors, D-2):** neither flag carries a floor id (export caps only
  *reduce* export; import bands clear economically); D-2 mechanism rows
  byte-comparable to the keeper's; C6/C7/C8 expected PASS with the same ST_GAS
  grounded notes.

## 5. R-criteria (pre-declared refutations — the ONLY fallbacks)

- **R1 — C3b veto (the decisive gate):** if **C3b > 0.20 in ANY year**, the
  composition is a **REJECTED probe**. Register both arms (rule 15), the
  `miso_seam_envelope_merit_cap` flag **stays default-off**, and the finding
  re-attributes to the seam-volume-vs-shape tension as an open item. **No
  percentile sweep, no ladder edit, no envelope re-derivation, no offsetting
  mechanism may be added in response** (rules 13/23/26). The Manitoba-only
  keeper stands unchanged.
- **R2 — inertness:** if `main − base` moves 2025 net interchange by
  **< +1.0 TWh**, the §1a attribution missed a binding structure — STOP and
  re-diagnose from the solved band flows/duals; tune nothing.
- **R3 — overshoot:** if any year's net interchange lands ABOVE the offline
  fixed-price bound (≈ base + 2.8/5.7/5.8, i.e. net ≈ +35.2/+21.4/+17.5) by
  **> 1.0 TWh**, the ceiling is not binding as designed — an implementation
  defect, stop-the-line, fix, re-solve.
- **R4 — no fabricated structure:** no new scarcity prints attributable to the
  restored import/export (no chase of the out-of-representation SETEX $1,070
  print; Jan-2024 stays not-a-reserve-event); the miso-72 per-zone Heather-window
  fidelity and the miso-74 per-seam Manitoba fidelity must not regress materially
  (watch, disclose).
- **R5 — honesty:** the deliverable is the interchange **volume + per-seam
  structure** (§B1/B2), NOT the price criteria; no C3a/C3b/C3c/C5a movement is
  quoted as validation of this composition.

## 6. Deliverable + validation (pre-named)

`scripts/miso73_perseam_validate.py` (already iterates `MISO_SEAM_DIBA`, covers
all four seams) on both bundles: per seam and year, annual net TWh, monthly
net-flow fidelity (mean |model − measured| monthly GWh), flow-duration RMSE —
PJM and South must improve on the base in every year (B2). Plus the total
net-interchange gap (B1) and the C3b read (B4/R1) from `report_run` scoring.
Hourly correlation is NOT a target (price-decorrelated seams; the duration curve
is the honest reproducible structure — miso-46 §3).

## 7. Phase B build/probe/register plan (ordered)

1. **No mechanism code.** Both flags are merged. The only new artifacts are the
   probe driver `scripts/run_miso75_composition_probe.py` (clone
   `run_miso74_manitoba_probe.py`; replays the **miso-74 keeper** bundle;
   `--merit-cap` arms `miso_seam_envelope_merit_cap=True` via `prb_overrides`;
   base = byte-faithful keeper replay, merit-cap OFF) and the chain
   `scripts/probes/_miso75_chain.sh` (clone `_miso74_chain.sh`: idempotent
   per-year + `--reuse-solved`, `MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1
   MARKET_SIM_HIGHS_THREADS=1`, base then main, years SEQUENTIAL, rule 12; MISO
   per-plant co-opt peaks ~14–16 GB/yr).
2. **Commit ALL code before solving** (a dirty tree under src/scripts/data
   disables reuse and OOMs — rule 12 ops).
3. Solve base, then main (~25 min each on the box). Never on CI.
4. `report_run` scoring + §6 per-seam validation + R-criteria reads (R1 first).
5. Rule 15/16 registration — **both** runs, all three years in one bundle each:
   `dashboard_add_run` (labels ≤ 4 non-stopword words, distinct slugs) →
   `gen_miso75_attestation.py` (clone `gen_miso74_attestation.py`; DOF branch:
   the merit-cap flag adds **zero** scalars — a semantics gate) →
   `build_dof_ledger.py` → `legitimacy_diagnostics.py --json-out` →
   `calibration_verdict.py --write-metrics` → `check_registry_payload_parity.py`
   → `build_manifest.py` → hand-write both sidecars (house style; keeper leads
   with the determination if promoted) → calibration-log entry. MISO registry is
   AT 15: adding 2 runs prunes the 2 oldest
   (`2026-07-16-miso-67-stgas-p25` single, then the miso-68 pair; sidecar +
   `runs/<id>.js` pairs only, bundle dirs stay). Push via the session git
   gateway, blob-verify every file ≥ 300 lines (rule 27).
6. **Keeper recommendation (OWNER-ONLY).** If the composition **holds the C3b
   veto (R1) AND closes the net-interchange volume (B1)**, it is a clean keeper
   upgrade over the Manitoba-only keeper (most structurally faithful — the
   correct merit-order seam semantics composed on the correct two-way seam) —
   propose the swap, do NOT self-promote. If R1 trips, the Manitoba-only keeper
   stands and the merit-cap flag stays default-off.

## 8. Out-of-scope ledger (recorded so the next charters start measured)

- **C3a-2025 / C3c remain the irreducible scarcity tail** (miso-74 §0 finding,
  miso-71 adjudication): out-of-representation, the maxgen/engagement scarcity
  already at its legitimate extent. This lane claims no tail closure; it moves
  C3a the *wrong* way (B3) by construction and is honest about it. The honest
  MISO endgame once the structure is maximally faithful is the
  determination/exceptions-ledger path (owner call), not more mechanism.
- **PJM-ISO's `inject_pjm_seam_flow_limit` carries the identical uniform-derate
  defect** (miso-73 §8) — its own all-ISO correctness lane, will not move MISO.
- **The all-ISO `gas_daily_shape_factors` interp-mislocation fix** (miso-72
  design §3.7; only residual broad-level 2025 miss is July ~−$3.3) — separate
  correctness lane, not folded in.
- **North/Central zonal topology split** — unchanged by this lane.
- **No sweeps:** `miso_seam_flow_percentile` stays default (p90); no envelope
  re-derivation; no ladder value edits; no new congestion mechanism. If R1
  trips, none of these are the fallback (rule 13/23/26).
