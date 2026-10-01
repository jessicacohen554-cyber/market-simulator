# MISO Manitoba two-way seam — replacing the import-only firm block with a measured two-way priced seam: frozen diagnosis + charter (miso-74)

**Date:** 2026-07-18. **Lane:** B of the post-miso-73 menu — the MHEB
two-way seam (the dominant remaining visible net-interchange residual, and the
last import-representation error on the MISO seam family). **Baseline keeper:**
`2026-07-18-miso-72-winter` (bundle `results/calibration/miso72_winter_citygate`).
**Phase A status: FROZEN (derive-first, NO LP — every number below is measured
data, keeper-bundle arithmetic, or an offline replay of the frozen Q-Q
construction).** Run number: miso-74. Zero fitted parameters anywhere in this
charter (rules 1/11/13/23).

**Lane chosen by owner (2026-07-18)** over the recommended lane A, on this
session's derive-first finding that lane A (coal trough offer level) is refuted
by its own source data — see §0.

## 0. Why lane B and not lane A (the C3a-2025 root-cause finding)

Lane A was recommended as "the C3a-2025/C3b trough-level root cause (coal-offer
level in dear-gas years)." This session's derive-first diagnosis **refutes that
premise**; recorded here because it re-frames what "done" means for MISO and it
is the reason lane B is the honest next structural step.

The C3a-2025 gap decomposed on its own load-weighted basis (actual RT hourly
`actual_lmp_hourly_MISO.parquet` × measured hourly demand
`miso_subba_demand_2023-2025.csv`):

| component | value |
|---|---|
| Actual LW mean | 44.2 (bench `rt_lw` 45.39) |
| Model LW mean (miso-72) | 39.17 |
| **Broad level (≤ $100): model vs actual** | **39.17 vs 39.36 → −$0.19 (essentially exact)** |
| **Tail (> $100) the model misses** | **$4.83 of the $6.22 gap = 78 %** |

June's *entire* miss is the tail: broad@100 = $40.8, model June = $40.91. The
model's **non-scarcity 2025 price level is correct**; ~78 % of C3a-2025 is the
scarcity tail (model 1 h vs 88 h > $200). That tail is already worked to its
legitimate extent — the keeper runs `maxgen_emergency_tier_pricing` (miso-70) +
the miso-71 engagement family, and miso-71's own adjudication is that 2023's 30
RT tail hours are all isolated 1-hour transients and ~95 % of 2024's are
sub-hourly/forecast-error (out-of-representation, ledgered not to force-close).

The **2025 SOM** (`data/raw/MISO/2025-MISO-SOM_Report.pdf`, published Jun 2026 —
the rule-23 re-derive trigger the miso-53 redesign queued) closes the door on
lane A directly: system price-cost mark-up **−1.07 %** (Table §VIII.B, PDF
p.118 — offers still at/below cost), **no offer-distribution / offer-curve
exhibit exists in the report** (full-text confirmed), and in the high-gas year
(Henry Hub +58 %) coal set the SMP *less* often (33 %→26 %) while **gas set
price 72 % of hours** (Table 1, PDF p.31). There is no measured basis to raise
the coal trough, and the trough is already correct; raising it would be a
compensating error (rules 11/14) that breaks the correct broad level and C3b.
**C3a-2025 is a largely irreducible scarcity-tail residual, not a trough root
cause.** #1347 is re-scored, not re-fit.

Lane B is the honest next structural step: it corrects a *known-wrong seam
representation*, and its C3a-2025 effect (a small upward nudge from removing the
firm block's 2025 over-import) is a disclosed side effect, never the objective.

## 1. The FROZEN diagnosis

### 1a. The MHEB residual and the firm block that causes it

The keeper serves Manitoba (MHEB) with an **import-only, annual-flat firm
block** — a fuel-free `Manitoba_firmhydro` generator in MISO-West, floor-frac
1.0 (must-flow), sized `MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR` = **726 / 531 /
224 MW** (2023/24/25) = **6.36 / 4.65 / 1.96 TWh** import. The measured MHEB net
interchange (EIA-930 BA-to-BA, `MISO interchange hourly.parquet`, import-positive
= −mw) is **+5.39 / +3.00 / −0.99 TWh**. So the firm block **over-imports
+0.97 / +1.65 / +2.95 TWh** (miso-73 §1a arithmetic, reproduced this session),
and in 2025 it imports +1.96 TWh where the measured seam **net-exports −0.99
TWh** — the firm block has no export path at all.

### 1b. The measured two-way anatomy (verified this session)

MHEB is a genuinely two-way seasonal hydro seam (freshet/summer import, winter
export to winter-peaking Manitoba; drought-2025 flips to net export):

| year | net TWh | mean MW | export-hours | flow min / max MW |
|---|---|---|---|---|
| 2023 | +5.39 | +615 | 25 % | −1326 / +2827 |
| 2024 | +3.00 | +343 | 39 % | −1417 / +2341 |
| 2025 | −0.99 | −113 | 58 % | −1405 / +2433 |

Monthly mean import MW (import-positive; miso-73 §8, reproduced): a summer
import peak (May-23 +1723, Aug-25 −430) and a winter export tail (Nov/Dec both
years negative), price-decorrelated (r ≈ 0.09–0.31 — the same scheduled-seam
signature the Q-Q ladder construction was built for). The import-only flat firm
block reproduces none of this: it carries a single annual import number and
cannot export.

### 1c. Why the firm block was the right stopgap and is now the residual

The firm block was the accepted representation while the three *priced* seams
(PJM/SPP/South) were being built (miso-46 root-cause doc §4d records the
limitation verbatim: "Manitoba-2025's measured net EXPORT (−0.99 TWh) is
outside the firm block's representation … a ~2-3 TWh known gap on that seam, out
of scope here"). With the seam ladder machinery now mature and merit-cap-aware
(miso-73), extending the **identical frozen Q-Q construction** to MHEB is the
correctness fix that retires that ledgered gap. This is the dominant remaining
*visible* net-interchange component: after the miso-73 merit-cap fix restores
the priced seams, the residual net-interchange wedge is approximately the firm
block's over-import (miso-73 §4, "the MHEB wedge REMAINS by construction").

## 2. What this lane IS and IS NOT

- **IS:** a correctness fix restoring the two-way seam physics MHEB actually
  has, by applying the **already-accepted, already-frozen** measured Q-Q ladder
  + deliverability-envelope construction (the same two mechanisms on
  PJM/SPP/South) to a fourth seam. Zero new mechanism *class*, zero new data
  *type*, zero fitted parameters.
- **IS NOT** an import floor or an export floor: nothing is forced. Every band
  clears economically against the LP's own hourly internal price; at low
  internal prices even the base import band backs off (and the seam exports),
  at high prices it imports deeper. The rejected `miso_firm_import_floor` stays
  rejected.
- **IS NOT** a C3a-2025 fix: the C3a-2025 miss is the irreducible tail (§0).
  The reduced 2025 net supply nudges C3a-2025 *up* as a disclosed side effect;
  no seam value moves in response to any price residual (rules 1/13).
- **IS NOT** a net-interchange-volume fix: it makes the *visible* net residual
  worse by exposing the priced-seam under-import the firm over-import was
  masking (§4, B3 — the rule-14 compensating-error signature). The volume
  residual belongs to the merit-cap lane (miso-73), the pre-declared
  composition partner (§3d).

## 3. The mechanism (FROZEN): `miso_manitoba_seam`

One new `ScenarioConfig` bool (default **False** — byte-identical replay for
every existing bundle), armed in the probe via `prb_overrides` and recorded in
`run_config.json` (rule 24). When True it performs one atomic swap:

1. **Suppresses the firm block** — the `Manitoba_firmhydro` generator is not
   built (supersedes `miso_firm_imports` for the MHEB leg).
2. **Adds MHEB as a fourth priced seam** — `MISO_SEAM_DIBA["Manitoba"] =
   ("MHEB",)` and a `NeighborInterface(name="Manitoba", ba_code="MHEB", …)` in
   `INTERFACE_NEIGHBORS["MISO"]`, so the existing seam machinery gives it, for
   free and with no new code path:
   - the reference-price node's 8 import + 8 export bands
     (`transmission.build_reference_price_node`);
   - the measured (month × hour-of-day) **two-way deliverability envelope**
     (`eia_loader.measured_seam_import_envelope`, both directions — auto-covers
     MHEB the moment it is in `MISO_SEAM_DIBA`; the loader today explicitly
     drops MHEB "in no seam", line 1696);
   - the merit-cap composition (`inject_miso_seam_flow_limit` under
     `miso_seam_envelope_merit_cap`) — **same code path, no fork** (§3d).

### 3a. The seam spec (physically-pinned constants, zero fitted)

- `border_zones=("MISO-West",)` — the Manitoba ↔ US ±500 kV HVDC / AC ties land
  in Minnesota (LRZ 1) = MISO-West, identical to the firm block's zone.
- `interface_limit_mw = 2900` — the physical MHEB→MISO transfer capability,
  pinned to the measured import extreme (+2,827 MW; §1b). The Q-Q fit is
  **insensitive** to this in [2400, 3000] (§3c reproduces net TWh to ±0.02 at
  every value); 2900 covers the observed import range while the export bands
  self-limit at the measured ~1,400 MW export capability via the export
  envelope. Phase B confirms against any published MHEB-MISO TTC; a material
  difference just re-runs the frozen derive (the ladder auto-adjusts).
- `import_emission_factor = 0.0` — Manitoba Hydro is ~hydro (physically pinned;
  CO2-pricing-inert for MISO, which has no border-carbon program — the EF is a
  CARB-only adder, `transmission.py` L1916 — but set explicitly to keep the
  clean-import accounting identical to the fuel-free firm block it replaces).
- `hurdle`, `gas_basis`, `marginal_heat_rate`, `hr_by_year` — the ladder prices
  the seam directly (displaces the reference-price formula on the rows it
  covers, exactly as PJM/SPP/South), so these carry the seam-family conventions
  and are inert under `miso_seam_measured_ladder=True` (keeper-on). No
  `firm_import_floor_by_year` (unlike PJM) — a firm import floor would force
  imports in the winter export hours the measured seam exports over.

### 3b. The ladder (frozen Q-Q construction, `derive_miso_seam_ladders.py`)

The derive script extends verbatim — MHEB joins `MISO_SEAM_DIBA` /
`INTERFACE_NEIGHBORS["MISO"]` and the existing loop derives its ladder with the
same formula (module docstring, unchanged):

    import band k:  pi_k    = Quantile_DA(1 − P[flow >  L_k])
    export band k:  sigma_k = Quantile_DA(    P[flow < −L_k])
    L_k = (k − 0.5) × interface_limit / 8

against the measured MHEB import-positive flow and the measured MISO **DA** hub
LMP, with the same same-seam no-wash clamp. The pooled 2023-2025 forward ladder
is the persistent revealed two-way seam structure. Candidate **pooled** ladder
(interface_limit 2800, this session's offline run — byte-exact values are Phase
B's frozen-derive output at the pinned 2900):

    "Manitoba": {
        "import": (31.18, 34.76, 39.89, 46.11, 57.51, 100.0, 184.22, 290.82),
        "export": (26.78, 23.58, 19.49, 14.01, 8.43, 8.43, 8.43, 8.43),
    }

The cheap base import rungs ($31–46, flowing most hours) are the persistent
firm hydro base; the deep rungs ($100–291) are the summer-freshet increment;
the four live export rungs ($14–27) are the winter export to winter-peaking
Manitoba (rungs 5-8 sit at the sample floor $8.43 — beyond the ~1,400 MW
measured export capability, effectively never-clearing).

### 3c. Offline P9 validation (this session — the derivation sanity check)

Simulating band clearing on the **measured DA** price (the derive script's own
`offline_score`), the Manitoba ladder reproduces the measured net flow — the
first time the two-way structure is captured:

| year | sim net TWh | measured | dur RMSE | import-hours sim / act |
|---|---|---|---|---|
| 2023 | +5.38 | +5.39 | 101 MW | 66 % / 75 % |
| 2024 | +2.99 | +3.01 | 98 MW | 51 % / 61 % |
| 2025 | **−1.00** | **−0.99** | 101 MW | 32 % / 42 % |
| pooled | +7.37 | +7.41 | 100 MW | 50 % / 59 % |

Duration RMSE ~100 MW (in family with PJM/SPP/South's 130–290 MW); hourly
placement is carried by the (month × hod) envelope + the model's internal price,
not the ladder (the flow is price-decorrelated by construction — the honest
reproducible structure is the duration curve, miso-46 §3). The import-hour
share is the expected duration-vs-placement bound (the ladder reproduces the
duration curve; the envelope places it).

### 3d. Composition with the merit cap (decided up front, per the lane brief)

Manitoba shares the seam family with the miso-73 `miso_seam_envelope_merit_cap`
(default off). Two things are handled **now**, not forked:

1. **Both envelope semantics.** Manitoba's deliverability envelope flows through
   the *same* `inject_miso_seam_flow_limit`, so with the merit cap OFF it is a
   uniform per-band derate (keeper default) and with it ON it is the waterfall
   ceiling — no Manitoba-specific branch. The primary probe (§7) runs merit-cap
   OFF (the keeper's setting).
2. **The composition hypothesis, pre-registered.** The merit cap was R1-vetoed
   because restoring the priced-seam imports flattened C3b-2025 0.183 → 0.200
   (added mid-price supply). Manitoba moves the *opposite* way in 2025 — it
   *removes* ~2.95 TWh of net supply (firm +1.96 → seam −0.99). The pre-declared
   hypothesis: **Manitoba's supply removal partly offsets the merit cap's C3b
   flattening**, so the composition {Manitoba + merit-cap} may restore the
   priced-seam volume *and* keep C3b ≤ 0.20. This is scored as the §7 A/B arm,
   NOT tuned — both are frozen structural mechanisms; whatever C3b does is
   reported (rules 1/14).

### 3e. DOF

**Zero new scalars.** The ladder is Q-Q-derived (measured flow × measured DA at
a fixed depth grid; re-derives only on a source-data extension — rule 23), the
interface_limit is physically pinned (§3a), the emission factor is 0.0 (hydro),
and the flag is a composition/representation gate, not a tunable. The firm
block's three scalars (726/531/224 MW) are **retired** from the DOF ledger.
Net DOF change: **−3 scalars** (a firm-import quantity per year → a measured
revealed supply curve).

## 4. Pre-registered expectations and bands

Deterministic swap arithmetic (firm − seam, measured): model net interchange
falls **0.97 / 1.65 / 2.95 TWh** when the firm block is replaced by the
measured seam net. The LP realizes the seam economically at its own (2025
~13.7 % low) internal price, so the realized Manitoba import will run modestly
*below* the measured (more export-leaning) in 2025.

- **B1 (primary gate — the deliverable):** the Manitoba seam's realized annual
  net lands within **±1.5 TWh** of measured (+5.4 / +3.0 / −1.0) every year,
  **and 2025 realizes net export (< 0)** — the two-way structure the firm block
  cannot represent. Scored by the extended per-seam validation (§6).
- **B2 (per-seam shape):** Manitoba monthly net-flow fidelity and flow-duration
  RMSE improve on the firm block (flat, export-blind) in every year (a low bar
  the firm block fails by construction — zero monthly variation, zero export).
- **B3 (net interchange, rule-14 honest):** total net-interchange |model −
  actual| moves **more negative by ≈ 0.97 / 1.65 / 2.95 TWh** (keeper gap
  −2.31 / −4.58 / −5.12 → ≈ −3.3 / −6.2 / −8.1). Pre-declared as the
  compensating-error signature — the firm over-import was masking the
  priced-seam under-import (the merit-cap lane). **NOT a rejection reason, NOT
  to be offset by any seam-side tuning** (rules 11/14). The composition arm
  (§7) is where the volume closes.
- **B4 (C3a-2025, disclosed side effect):** C3a-2025 moves **up (less
  negative)** by a modest amount (~+0.5 to +2 pp) from the reduced 2025 net
  supply; 2023/2024 ≈ unchanged. Disclosed, **not gated, not the objective, not
  quoted as validation** (rule R6). If it moved *down* the lane still stays
  (rule 14).
- **B5 (hard veto):** C3b ≤ 0.20 absolute, all years (standing shape veto;
  2025 keeper 0.183). Manitoba *removes* supply → expected to **un-flatten**
  (help) C3b, so this is low-risk for the primary probe; it is the live gate
  for the composition arm (§3d).
- **B6 (C5a watch):** CO2 may tick up slightly in 2025 from the new winter
  export leg (MISO generates more internally to serve the MISO→Manitoba
  export); expected within the C5a band (keeper +0.6 / −3.3 / +4.3 %). Disclosed.
- **B7 (no new floors, D-2):** the seam carries **no floor id** (bands clear
  economically; the export envelope only *caps* export, never forces it); D-2
  mechanism rows byte-comparable to the keeper's minus the firm block; C6/C7/C8
  PASS with the same ST_GAS grounded notes.

## 5. R-criteria (pre-declared refutations — the ONLY fallbacks)

- **R1 — inertness:** if main − base moves the 2025 *Manitoba-leg* net by
  < 1.0 TWh vs the firm block, the seam is not clearing — STOP, re-diagnose from
  the solved band flows/duals; tune nothing.
- **R2 — no two-way:** if the 2025 Manitoba seam does **not** realize net export
  (stays a net importer), the two-way structure failed — an implementation
  defect (envelope/ladder/sign), stop-the-line, fix, re-solve.
- **R3 — over-import overshoot:** if realized Manitoba net exceeds measured by
  > 1.5 TWh import in any year (imports like the old firm block), the export
  envelope / ladder is not binding — defect, stop-the-line.
- **R4 — C3b veto:** if C3b > 0.20 in any year on the **primary** probe, the run
  is registered (rule 15, both arms) but NOT recommended as keeper and the flag
  stays default-off; re-attribute, no percentile/ladder edit in response
  (rules 13/23/26). (Expected slack, not risk — Manitoba un-flattens.)
- **R5 — no fabricated structure:** no new scarcity prints attributable to the
  export leg (no chase of the out-of-representation SETEX $1,070 print;
  Jan-2024 stays not-a-reserve-event); miso-72's per-zone Heather-window
  fidelity must not regress materially (watch, disclose).
- **R6 — honesty:** the deliverable is the interchange structure (§6), NOT the
  price criteria; no C3a/C3b/C5a movement is quoted as validation of this
  mechanism.

## 6. Deliverable + validation (pre-named)

Extend `scripts/miso73_perseam_validate.py` to the Manitoba seam (its loop
already iterates `MISO_SEAM_DIBA`; Manitoba appears automatically once mapped) —
from the solved bundle's dispatch parquet, sum the `_refimp_`/`_refexp_` band
rows for the Manitoba seam and score, per year, against the measured EIA-930
MHEB flow:

1. annual net TWh + the sign of 2025 (B1),
2. monthly net-flow fidelity (mean |model − measured| monthly GWh) vs the firm
   block (B2),
3. flow-duration RMSE vs the firm block (B2).

Hourly correlation is NOT a target (price-decorrelated seam; the duration curve
is the honest reproducible structure — miso-46 §3).

## 7. Phase B build/probe/register plan (ordered)

1. `ScenarioConfig.miso_manitoba_seam` (default False, docstring citing this
   charter); the atomic swap in the seam builders (suppress firm block, inject
   Manitoba into the working seam set + envelope + ladder); `NeighborInterface`
   spec (§3a) + `MISO_SEAM_DIBA["Manitoba"]`. Extend
   `derive_miso_seam_ladders.py` (MHEB in the seam map) and paste its frozen
   pooled + per-year output into `MISO_SEAM_LADDER_BY_YEAR` at the pinned
   interface_limit. **No new mechanism code** beyond the flag wiring + the
   spec/ladder data.
2. Unit tests (trivial-case-first): one seam, 8 bands, constant cap — two-way
   band bounds, export-envelope cap, flag-off byte-identity (firm block intact,
   no Manitoba seam), merit-cap-on waterfall composition on the Manitoba seam,
   MHEB-in-`MISO_SEAM_DIBA` envelope auto-cover. Run the existing seam test
   files + the new tests.
3. Probe driver `scripts/run_miso74_manitoba_probe.py` (replays the
   `miso72_winter_citygate` bundle via `replay_keeper.build_kwargs`;
   `--manitoba-seam` arms the flag via `prb_overrides`; base = byte-faithful
   keeper replay) + chain `scripts/probes/_miso74_chain.sh` (clone
   `_miso73_chain.sh`: idempotent per-year + `--reuse-solved`,
   `MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1`, base then main, years
   SEQUENTIAL, rule 12; MISO per-plant co-opt peaks ~14-16 GB/yr).
4. **Commit ALL code before solving** (a dirty tree under src/scripts/data
   disables reuse and OOMs — rule 12 ops).
5. Solve base, then main (~25 min each on the 15.8 GB box). Never on CI.
6. **Composition A/B arm** (pre-registered §3d): a third run
   {Manitoba + `miso_seam_envelope_merit_cap`} on the same base box, to test
   whether Manitoba's supply removal keeps C3b ≤ 0.20 while restoring the
   priced-seam volume. Registered with the primary bundle.
7. `report_run` scoring + §6 per-seam validation + R-criteria reads.
8. Rule 15/16 registration — every run (base + main + composition arm), all
   three years 2023+2024+2025 in one bundle each: `dashboard_add_run` (labels
   ≤ 4 non-stopword words, distinct slugs) → `gen_miso74_attestation.py`
   (clone `gen_miso73_attestation.py`; DOF branch for the flag — retires the
   three firm-block scalars, §3e) → `build_dof_ledger.py` →
   `legitimacy_diagnostics.py --json-out` → `calibration_verdict.py
   --write-metrics` → `check_registry_payload_parity.py` → `build_manifest.py`
   → hand-write sidecars (house style) → calibration-log entry. MISO registry
   is AT 15: adding runs prunes the oldest (miso-66 pair next; sidecar +
   `runs/<id>.js` pairs only, bundle dirs stay). Push via the session git
   gateway, blob-verify every file ≥ 300 lines (rule 27).
9. Keeper recommendation per rules 1/11 (most structurally faithful — the
   correct two-way seam physics replacing a known-wrong import-only stopgap);
   swap is OWNER-ONLY.

## 8. Out-of-scope ledger (recorded so the next charters start measured)

- **The merit-cap volume lane (miso-73):** the priced-seam under-import
  exposed by B3 is the merit cap's job; the composition arm (§7 step 6) is the
  first joint test. If the composition keeps C3b ≤ 0.20, {merit-cap + Manitoba}
  is the candidate keeper recipe for a follow-up (owner call).
- **C3a-2025 is largely irreducible** (§0) — tail-dominated, out-of-
  representation, the maxgen/engagement scarcity already at its legitimate
  extent. Not a lane; re-scored, never re-fit (#1347 records the miss).
- **IESO seam split** off the pooled PJM seam (needs an HOEP intake) —
  unchanged (miso-46 §4a).
- **PJM-ISO's `inject_pjm_seam_flow_limit`** carries the identical uniform-derate
  defect (miso-73 §8) — its own all-ISO lane, will not move MISO.
- **The all-ISO `gas_daily_shape_factors` interp-mislocation fix** (miso-72
  design §3.7) — the only residual broad-level 2025 miss is July ~−$3.3 (§0
  by-month); this is the candidate cause, a separate correctness lane, not
  folded in.
- **North/Central zonal topology split** (lane C) — unchanged by this lane.
- **No sweeps:** `miso_seam_flow_percentile` stays default (p90); the interface
  limit is pinned not swept; no ladder value edits beyond the frozen derive; no
  new congestion mechanism.
