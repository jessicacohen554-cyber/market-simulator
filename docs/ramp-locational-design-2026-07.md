# Ramp-Rate + Locational (LCR) Structure — Design (2026-07)

**Status: DESIGN — awaiting owner sign-off. No implementation in this doc's commit.**

**Thread:** closes the structural gap disclosed by
`results/calibration/FINDING-caiso-evening-merit-2026-07-04.md`: evening CT dispatch in
reality is driven by ramp-rate limits and load-pocket locational need, neither representable
in the current energy-only, ramp-free zonal LP. The caiso-51 CT floor (`ct_netload_drag`) was
compensating for exactly this absence; after the caiso-52 scrub it is the **sole surviving CT
commitment mechanism** in the CAISO keeper. This build must replace its rationale (rule 18 —
one mechanism per phenomenon), not stack on it.

Two ISO-agnostic mechanisms, each owning one phenomenon, both living in the shared LP builder
(`model/dispatch.py:build_constraints`) used by `runner.py` and `scripts/run_calibration.py`
alike:

| Mechanism | Phenomenon owned | Flag (ScenarioConfig, GATED default off) |
|---|---|---|
| Plant-level hourly ramp envelope rows | slow-fleet trajectory friction → fast-start units clear the evening ramp on merit | `ramp_limits` |
| Local-capacity (LCR-area) minimum-generation rows | load-pocket commitment the zonal topology cannot see | `local_capacity_constraints` |

Zero new fitted degrees of freedom: the ramp envelopes are CAMPD-measured physical
capabilities (rule 13 admissible), the LCR parameters are CAISO-published study values
already in `data/raw/capacity-deliverability/caiso/caiso.csv`. The DOF ledger entry for both
is "measured/published input, no free parameter"; the ablation twin is the flag off.

---

## 1. Q1 — Ramp-rate constraints in P1

### 1.1 Why naive class ramp rates would NOT work — and what does

Engineering ramp rates (NREL/WWSIS cycling params: CC ≈ 5 %/min, coal ≈ 1–2 %/min) are
per-minute figures; at hourly LP resolution a CC's nameplate hourly ramp (≈ 300 %/h of pmax)
exceeds pmax, so a class-typical ramp row **never binds**. The binding physics at hourly
resolution is the start-to-dispatchable trajectory (a warm CC start takes 2–4 h to full
load) plus operational practice — a *commitment* envelope, not a MW/min rate.

The measured plant-level hourly delta captures exactly that envelope, because every start,
warm-up, and shutdown the plant ever performed is in its CEMS trace. Probe on the CAMPD CA
unit-level extracts (2023–2025 pooled, plant-hour gross load summed across CC units,
gap-hours excluded from diffs; 43 CC plants ≥ 50 MW, 19.5 GW observed pmax):

| statistic | value |
|---|---|
| p99.5 1-h up-ramp / observed pmax, capacity-weighted mean | **0.32** |
| plants with p99.5 up-ramp < 0.6 × pmax | 41 of 43 (93 % of capacity) |
| p99.5 1-h down-ramp / pmax, mean | 0.37 |
| CC **fleet-aggregate** max observed 1-h up-ramp | 3.7 GW (p99.5 = 2.4 GW) |

So a measured envelope binds hard at hourly resolution: the model currently swings
CC_REGULAR from 5.5 GW (midday) to 8.5 GW (evening) freely; reality's fleet has never moved
more than ~3.7 GW in any hour. With the envelope in place, the LP must either pre-position
CC before the ramp (real: CAISO RUC does this) or clear fast resources — CT, storage,
imports — at the ramp margin (real: fast-start dispatch). Either way, in ramp-bound evening
hours the **marginal unit becomes the fast resource, so the LMP rises to CT SRMC and CT
clears on merit** — the exact mechanism the finding identified as missing.

### 1.2 Formulation

One two-sided row per ramp-constrained *plant* per hour transition (t = 1…T−1, no cyclic
wrap — the Dec-31→Jan-1 seam carries no physics worth a coupling row):

```
-RD_eff[p,t] ≤ Σ_{tranches g∈p} P[g,t] − Σ_{g∈p} P[g,t−1] ≤ RU_eff[p,t]
```

- **Plant level, not tranche level.** Tranches dispatch bang-bang within a plant; the
  trajectory is a plant property. Same aggregation precedent as the per-gen reserve
  `pergen_col` grouping (`dispatch.py:_build_reserve_rows_pergen`).
- **Availability-edge widening (feasibility guard).** An outage onset forces
  ΔP = −P[t−1] regardless of any envelope; a return/COD restores capacity in one hour.
  With `cap[p,t] = Σ_g pmax[g]·availability[g,t]`:
  `RU_eff[p,t] = RU[p] + max(0, cap[p,t] − cap[p,t−1])`,
  `RD_eff[p,t] = RD[p] + max(0, cap[p,t−1] − cap[p,t])`. Pure vector arithmetic on the
  existing availability arrays; keeps the row hard everywhere except at capacity
  discontinuities the model itself imposes.
- **Pruning.** A plant with `RU ≥ cap_max` and `RD ≥ cap_max` gets no row (it can never
  bind). This automatically excludes CTs (bang-bang: observed max delta ≈ pmax), hydro and
  storage (not in scope), and import pseudo-generators. No class-name gate anywhere —
  eligibility is by measured parameter, per rule 18's commitment-physics-by-parameters.

**Vectorization** (rule 2): the block is a single `coo_matrix` exactly like the SOC-dynamics
block — rows `r = p·(T−1) + (t−1)`, +1 coefficients on each member tranche's P column at
hour t, −1 at hour t−1; RHS vectors from the availability-delta arithmetic above. No Python
loop over hours.

**Row placement:** appended after the interface-group rows, before hydro/oil/RPS/reserve —
the front-anchored energy-balance duals and end-anchored RPS/reserve duals keep their
positions (same convention as every optional family in `build_constraints`).

### 1.3 Data: `derive_campd_ramp_envelopes.py` (new, mirrors `derive_campd_ct_run_lengths.py`)

Per ISO, per plant in the model fleet with CAMPD coverage, pooled over the available vintages
(2023–2025 today):

- `ramp_up_mw` = **max observed** 1-h increase in plant gross load. Max, not a quantile: the
  envelope must never make the backcast fleet unable to do something it actually did — the
  bound removes only moves *never observed*. Max includes every start trajectory.
- `ramp_dn_mw` = max observed 1-h decrease **excluding trip-to-offline deltas** (deltas whose
  endpoint is < 5 % of pmax — a trip is an availability event, already modelled by the
  outage overlay/availability, not a dispatch choice; leaving trips in would inflate the
  down-envelope to ≈ pmax and disarm it).
- Guards: gap-hours excluded from diffs; plants with < ~4,000 observed hours fall back to
  the ISO-class row (capacity-weighted median envelope fraction × pmax), like the run-length
  class fallback.
- Output `data/raw/_processed-legacy/campd_ramp_envelopes_<ISO>.csv`; loaded by a new
  `fleet.py` helper that maps plants → LP tranche groups and returns
  `(ramp_group_col, ramp_up_mw, ramp_dn_mw)` for `build_constraints`.

**Admissibility (rule 13):** a physical-capability envelope in the same class as the CAMPD
min-stable loads, committed shares, and measured run lengths (rules 12/23 precedents): it
regenerates from the CAMPD pipeline for any vintage, responds to fleet change (new plant →
class fallback; retrofit → new trace), and never reads a price/volume residual. Forward
story: forecast years use the same per-plant envelope (a physical constant of the machine)
and class fractions for new entrants. **Freeze rule 23 applies:** re-derive only on source
data updates, never because a residual moved.

### 1.4 Expected effect and honest limits

- Targets **who serves the evening ramp increment** — CT vs CC on merit. Ramp duals make
  prices non-separable across hours (real: CAISO's ramp scarcity / FRP exists because of
  exactly this coupling).
- Does **not** fix the all-hours CC over-supply (+3.2 GW overnight has no ramp excuse) —
  that is Lever A (CC SRMC floor, landed `1ada584`) / Lever B (firm import sizing) territory
  per the finding. A/B scoring must not blame the ramp rows for that residual.
- Down-ramp rows will hold CC *higher* through the midday solar belly than a free LP would.
  That is the real physics (reality's midday CC of 3.1 GW was achieved *with* these
  envelopes, which are measured from that same trajectory), so a worse midday fit is a
  rule-12 signal about the offer level, not about the envelope.

### 1.5 LP size / runtime

CAISO: ~60 ramp-constrained plants (43 CC + ~10–15 ST/cogen survivors of pruning) →
~60 × 8,759 ≈ **0.53 M rows**, nnz ≈ 2 × ~4 tranches × 0.53 M ≈ **4 M** (~+30 % on the
~12 M-nnz LP; roughly doubles the row count, which today is SOC-dominated at ~0.4 M).
These are SOC-like inter-temporal coupling rows — the LP is already inter-temporal through
storage, so the structure is not new to the basis. Estimate: **1.5–2.5× solve time**
(CAISO year today: P0 cold ~120–160 s, P1 warm ~15–30 s, P2 ~100–160 s → expect ~6–12 min/yr,
~30–40 min for the 3-year A/B arm). Memory: +4 M nnz ≈ tens of MB in A plus solver fill —
within the 15 GB single-run budget; keep the ≤ 2-concurrent-run cap. **Abort criterion:**
if the single-year probe exceeds 3× baseline solve time, revisit (options: prune to plants
with envelope < 0.8 × pmax; drop down-ramp rows first — the up-envelope carries the merit
mechanism).

PJM/MISO per-plant fleets are ~4–6× CAISO's plant count → ~2–3 M ramp rows. Acceptable in
principle (same order as their per-gen reserve builds), but phase 1 is CAISO-only; measure
before extending.

---

## 2. Q2 — Min-up/min-down in P1: **defer (stay in P2)**

Recommendation: **do not** add min-up/min-down to P1 in this build.

1. **The measured envelope already carries it at hourly resolution.** A plant's observed
   max hourly delta embeds its start trajectory; the envelope forces multi-hour climbs and
   descents, which is the dispatch-visible consequence of min-up/down + start friction. A
   separate P1 min-up mechanism would be a second mechanism on the same phenomenon
   (trajectory friction) — rule 18 forbids stacking it on the unexplained residual of the
   first.
2. **A pure-LP min-up/down needs commitment variables.** The standard tight formulation
   requires `u[g,t] ∈ [0,1]` columns (+8,760 columns per slow unit, roughly doubling the
   slow-fleet block) and its LP relaxation is weak — fractional `u` dissolves exactly the
   lumpiness min-up/down is meant to impose. High cost, low signal.
3. **The three-solve architecture already owns the phenomenon elsewhere.** P2's screen
   enforces min-run/min-down for the opt-in diagnostic path; the P1 startup-amortization
   markup (v3 measured-run basis) prices cycling into offers. Interaction with this build:
   ramp rows lengthen P0 runs → the endogenous markup shrinks — correct direction, no
   double-count (offers price start *cost*; rows enforce trajectory *feasibility* —
   different phenomena).

Revisit only if the A/B shows evening CT still short **and** D-2 attribution localizes the
residual to start-cycling the envelope cannot express; that would be a phase-3 candidate
(relaxed-commitment LP), opened as its own root-cause issue.

---

## 3. Q3 — Sub-zonal locational need: options ranked

**(b) Local-capacity constraint row — RECOMMENDED for phase 1.**

- Grounded in CAISO's published Local Capacity Requirements study — already in the repo
  (`data/raw/capacity-deliverability/caiso/caiso.csv`: LA Basin requirement 7,529 / 4,413 /
  4,123 MW for 2023/24/25, San Diego–IV 3,332 / 2,834 / …, per-year primary-source
  citations). Market-design-real: local RA must-offer + minimum-online-commitment is how
  CAISO actually procures this.
- Formulation, one row per (LCR area a, hour t):

  ```
  Σ_{g ∈ area a} P[g,t] ≥ max(0, local_load_a[t] − import_cap_a)
  ```

  with `import_cap_a = published_area_peak_load − published_requirement` (both from the
  same LCR report table — requires adding the `peak_load` metric rows to `caiso.csv`, same
  source PDFs already cited) and `local_load_a[t] = area_share × zone_load[t]`
  (`area_share = area_peak / zone_peak`, documented rule-14 reconciliation of the study's
  substation boundary onto our zonal load shape). RHS is a plain vector; the row is a
  `coo` block identical in shape to the interface rows (kron over hours). ~2 areas ×
  8,760 ≈ 17.5 k rows — negligible.
- **This is the exact LP relaxation of the deferred zone split**: the sub-zone's energy
  balance with its boundary flow at the import cap, minus the LMP separation. It binds only
  in hours where local load exceeds import capability — evenings/peaks — giving the
  rule-17 triple natively: *driver* = local load (forward-regenerating), *window* = emerges
  from the driver (never binds overnight), *forward story* = each year's published LCR
  study / load growth.
- **Dual semantics (feature, not bug):** the row's dual subsidizes in-area units' reduced
  costs without entering the zonal energy-balance dual — i.e. out-of-market commitment,
  uplift-like, exactly how real local commitments are paid (bid-cost recovery / RMR), and
  consistent with the SP15 hub price remaining the scoring benchmark. In-area CTs dispatch
  up on local need; SP15 LMP is not artificially lifted.
- Membership crosswalk: plant → LCR area by county (EIA-860 plant table carries
  County/lat-lon; LA Basin ≈ LA + Orange counties within the CAISO fleet — LADWP is a
  separate BA and never enters our fleet). New file
  `data/raw/reference/lcr_area_membership_CAISO.csv`, cited; unmapped pockets
  (Stockton/Kern, per the capacity-deliverability crosswalk notes) stay unmapped rather than
  guessed. Registry `LOCAL_CAPACITY_AREAS` in `config/iso_configs.py` (ISO-agnostic; NYISO
  in-zone pockets / PJM EMAAC sub-areas can populate it later without code changes).
- D-2 accounting: LCR-bound energy is attributed as its own mechanism ID (like
  `min_gen_mechanism`), counted in the forced-energy budget (rule 19) — the CT budget
  (≤ 10 %) still applies to the sum of all binding-floor + LCR-forced energy.

**(a) Full LA-basin zone split — DEFER (phase 3+, only if evidence demands).** Highest
fidelity (locational LMP separation) but: needs sub-zonal load disaggregation, fleet and
renewable/storage re-assignment, an intra-SP15 interface rating (the published number *is*
the LCR import capability — same input as (b)), and it **changes the scoring boundary**
(bench actuals are SP15 hub prices; a split zone needs a re-aggregation convention before
any keeper can be scored). CAISO-specific topology surgery with keeper-breaking risk — do it
only if the LCR row demonstrably under-represents the pocket.

**(c) Ramp only, defer locational — REJECTED as the plan of record.** The finding names
both mechanisms; LA-basin units are the bulk of the CAISO CT fleet, and shipping ramp alone
would leave a known structural absence for the drag to keep compensating — exactly the
rule-18 stacking this build exists to end. (The A/B still measures a ramp-only arm for
attribution.)

---

## 4. Q4 — Forecast parity from day one

Both rows live in `build_constraints` (`model/dispatch.py`) — the byte-shared matrix builder
both entry points already call. Threading follows the `energy_reserve_coopt` /
`capacity_deliverability_limits` pattern verbatim:

1. `ScenarioConfig.ramp_limits: bool = False`, `local_capacity_constraints: bool = False`
   (# GATED comments) + cache-key registry entries (`scenarios.py:3284` map).
2. Shared input builders in `src/market_sim/` (`fleet.py` ramp-envelope loader;
   a `local_capacity.py` or `transmission.py` helper for LCR RHS/membership) — **no
   calibration-script-only wiring**.
3. `runner.py` and `run_calibration.py` each add the same `dispatch_kwargs`
   (`ramp_group_col`, `ramp_up_mw`, `ramp_dn_mw`, `lcr_gen_idx`, `lcr_rhs`) under the flag —
   the mirrored-hook pattern (`runner.py:200-220` vs `run_calibration.py:2896-2920`).
4. Flags off → zero rows → byte-identical LP (regression-tested, like every optional
   family).

Forecast-year inputs regenerate: envelopes are plant constants (class fractions for new
entrants), LCR RHS from the latest published study scaled by forecast zonal load.

---

## 5. Q5 — Rule-18 ledger: what this replaces

Current CT-commitment mechanism inventory (post-caiso-52 scrub) and disposition:

| Mechanism | Phenomenon it stood in for | Disposition |
|---|---|---|
| `ct_netload_drag` (CAISO: slope 0.00901/GW, int −0.1124, cap 0.36, window h15–22 — **ON in keeper, sole CT mechanism**) | evening ramp + local commitment the LP couldn't see | **Retire from CAISO wiring when ramp+LCR pass the decision rule below.** Its DwC rationale (audit §7 D-8) was "reliability commitment the LP can't see"; once the LP sees it, the drag has no phenomenon left to own. Never re-enabled on top of a ramp+LCR residual (rule 18). |
| `apply_gas_st_netload_drag_floor` (ST sibling) | same, steam units | Same decision rule, same A/B. |
| Reliability-floor CT limbs (CAISO CSV) | same | Already `enabled=False` (caiso-52). Stay retired; provenance rows kept. |
| RA startup bridge CT eligibility | overnight restart economics | Already physics-gated out (min-down ≥ 4 h). Unchanged. |
| `caiso_ra_mustoffer` CC min-load bridge | CC RA commitment across short gaps | **Keep** — different phenomenon (stay-online economics, not trajectory). Re-audit overlap in the A/B's D-2 attribution. |
| Reliability-floor `SP15,CC_REGULAR,tmax` limb | temperature-driven CC commitment | **Keep** — different driver (temperature); re-check attribution after ramp lands. |
| NYISO downstate CT temperature floor; PJM CT-drag probe | their evening/local CT commitment | **Unchanged until phase 2 validates ramp+LCR on those ISOs** (rule 25 — a CAISO result never retires another ISO's mechanism). Same decision rule applies there when their A/B runs: NYISO's floor rationale ("cable-constrained downstate load pockets") is precisely an LCR-registry entry; PJM's drag rationale ("AS/RUC deployment energy") is precisely the ramp envelope. |

**Retirement decision rule (stated ex-ante, scored on the 3-year A/B):** with
`ramp_limits + local_capacity_constraints` on and `ct_netload_drag` off, the arm must show
(i) CAISO CT evening (h15–21) energy at or above the drag arm's, or closer to CAMPD actual;
(ii) C7 diurnal shape clean (overnight CT ≈ 0, D-4 off-window binding = 0); (iii) D-2 CT
forced share (now = LCR-attributed only) below the drag arm's and within the rule-19 10 %
peaker budget. Pass → `ct_netload_drag` and the ST drag are removed from the CAISO keeper
wiring (`run_calibration.py:1351-1370`) in the same PR that promotes the run. Fail → the
new mechanisms stay (they are structural, rule 1), the drag stays retired from the arm, and
the residual is opened as a root-cause issue — **not** closed by re-arming the drag.

---

## 6. Phased build plan

**Phase 0 — data + derive (no LP change):**
`scripts/data/derive_campd_ramp_envelopes.py` (+ CAISO CSV artifact, governance header per the
run-lengths precedent); `peak_load` metric rows added to
`data/raw/capacity-deliverability/caiso/caiso.csv` from the already-cited LCR reports;
`lcr_area_membership_CAISO.csv` county crosswalk; `LOCAL_CAPACITY_AREAS` registry. Unit
tests on the derive logic (gap handling, trip exclusion, class fallback).

**Phase 1a — ramp rows:** `_build_ramp_rows` in `dispatch.py` + bounds arithmetic +
threading (§4) + tests (§7, T1–T3, T6) + a single-year CAISO 2024 throwaway timing probe
(never registered, rule 15).

**Phase 1b — LCR rows:** `_build_local_capacity_rows` + RHS builder + threading + tests
(T4–T5) + mechanism-ID attribution in the D-2 diagnostics.

**Phase 1c — CAISO 3-year A/B** on the current main recipe (caiso-51 flags + scrub +
Lever A, plus Lever B if landed), `--year 2023 2024 2025`, arms:
(W) baseline, drag ON (status quo);
(X) `ramp_limits` only, drags OFF;
(Y) `ramp_limits + local_capacity_constraints`, drags OFF — the candidate;
(Z) `local_capacity_constraints` only, drags OFF (attribution).
Run `legitimacy_diagnostics --keepers` + `audit_keepers`; register every arm on the
dashboard (rule 14; payloads via `mcp__github__push_files`); apply the §5 decision rule.
Keeper promotion by structural fidelity, not MAE (rule 1).

**Phase 2 — second ISO:** NYISO (downstate pockets already zonal — LCR registry may be
small; ramp envelopes from CAMPD NY extracts) or PJM per owner priority; same A/B + ledger
discipline against their CT mechanisms.

**Phase 3 — only on evidence:** relaxed-commitment P1 layer (§2) and/or LA-basin zone
split (§3a).

## 7. Test plan (Testing Pattern: trivial first)

- **T1 (1 gen, 1 zone, 24 h):** slow gen (pmax 100, RU=RD=20) + fast peaker; demand step
  50→150. Assert slow-gen |ΔP| ≤ 20 every hour, peaker fills the step, step-hour LMP =
  peaker MC (the merit mechanism itself), no slack; flag off → row count and solution
  byte-identical to today.
- **T2 (availability edge):** outage zeroing the slow gen mid-day → LP stays feasible,
  widened RHS consumed, no slack beyond the energy shortfall itself.
- **T3 (plant grouping):** one plant, two tranches — envelope binds the *sum* (tranche
  switching inside the plant stays free).
- **T4 (LCR, 2 gens, 1 zone, 24 h):** in-area dear unit + out-area cheap unit; local load >
  import cap in 4 evening hours. Assert in-area dispatch ≥ RHS exactly in those hours,
  zonal LMP still set by the cheap unit (uplift-not-price semantics), zero rows/identical
  solution with the flag off.
- **T5 (LCR RHS):** `max(0, ·)` clipping, area-share scaling, per-year requirement
  selection.
- **T6 (vectorization/scale):** no `for t in range(` in the new builders; 8,760-hour
  construction time for the ramp block < a few seconds (matches the ~2 s full-matrix build
  budget).

## 8. Success criteria (from the task, measured on arm Y)

CT evening dispatch rises toward the CAMPD actual (h15–21 mean 770 MW vs model 598)
**through merit** — CT energy clearing at LMP ≥ its SRMC band, no floors; C7 diurnal shape
stays clean (overnight ≈ 0); D-2 forced share falls versus the drag baseline. Explicitly
*not* success criteria: total CC energy (Lever A/B territory) and backcast MAE in isolation
(rule 1).
