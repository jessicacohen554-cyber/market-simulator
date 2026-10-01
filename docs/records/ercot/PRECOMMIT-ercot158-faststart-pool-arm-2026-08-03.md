# PRECOMMIT — ERCOT-158: `ercot_faststart_pool_offer` arming test (the ERCOT-88 CT pool, now with its 2023 year block) + honest-inputs control replay

**Date** 2026-08-03 · **ISO** ERCOT · pushed BEFORE any solve (rule-15/ercot145b
protocol; the ERCOT-148/149 template). **Owner authorization:** the session
prompt is the owner's authorization for the ERCOT-89 §7 step-2 design round
(ERCOT-151 §4 ask 2), the standing owner gate this arm has waited on since
2026-07-19. Basis keeper `2026-08-02-ercot150b-zonal-anchor` (bundle
`results/calibration/ercot150_zonalanchor_B`, determination NOT-YET, fail set
{C3a 2023-only, C3b 2023-only, C3c, C7 2023-lignite cv-leg}, C1 16/16 all-class
/ 12/12 free-class, C6 ATTESTED+PASS, n_entries 9 / n_residual 6). Chartered
design: `docs/DIAGNOSIS-ercot151-offline-increment-phase0-2026-08-02.md` §3–§4;
Phase-0 committed record `results/calibration/ercot151_offline_phase0.json`;
data landing `docs/calibration-log/ercot.md` "2026-08-03 — ERCOT-157".

## 0. Scope fence (DO-NOT-REDO, rule 28(a))

The arm is the **existing ERCOT-88 CT pool mechanism exactly as built** —
`ercot_faststart_pool_offer=true`, no code change, no new flag — now engaging
2023 because ERCOT-157 landed the pool artifact's 2023 CT year block
(`data/raw/_validation-source/ercot_faststart_pool_condbinned.json`, CT
2023/2024/2025; 2024/25 blocks verified byte-identical to the prior committed
artifact). **NO CC slow-start tier is built**: ERCOT-152 refused it ex ante on
measured conduct (CC OFFQS/OFFNS ≈ 0 MW — no measured object; plain-OFF CC
SCED2 curves are cheap, p50 $19.5–34.7, so re-pricing them is a measured
no-op). The ercot41/43/106/108 envelope/cap family stays closed (§3(ii): the
pool re-prices the offline increment, never caps it). `ercot_shoulder_online_span`
stays OFF (rejected as armed, ERCOT-89 §9.4–9.5) — this arm runs the **static
ERCOT-88 boundary** `1 − pool_frac(bin)`, not the span boundary. Solves need
only the committed condbinned JSONs — never the raw NP3-965 shards (rule 23).

## 1. The two runs (rule 16 full-span, rule 12 concurrent invocations)

Both are `scripts/replay_keeper.py` replays of the keeper bundle's meta.json
recipe, full span `--year 2023 2024 2025` (years sequential within each
invocation), the two invocations concurrent with separate `--out-dir`s
(rule 12, cap 2 for plant-level ERCOT):

* **Run A — honest-inputs control replay** (the ercot98 pattern):

  ```
  python scripts/replay_keeper.py results/calibration/ercot150_zonalanchor_B \
    --out-dir results/calibration/ercot158_honest_A \
    --note "ERCOT-158 Run A: honest-inputs replay of the ercot150b keeper config \
  (UNCHANGED) on the ERCOT-157-completed inputs; A/B control for the pool arm."
  ```

  Config **unchanged**. The only physical input delta vs the committed keeper
  bundle is the ERCOT-157 refresh of the armed RT wall's 2023 block
  (`ercot_sced_offer_wall_condbinned.json`: the committed block was the
  Jan–Oct post-purge slice, now completed full-year — moves confined to
  net-load bins 0–4; **scarcity-tail bins 5–6 byte-identical**, so 2023
  tail-pricing inputs did not move; 2024/2025 blocks byte-identical). Expect
  C3c ≈ unchanged; any movement concentrated in the 2023 low/mid band.
  Run A doubles as the **A/B base**: ercot150's K2 finding measured real
  same-HEAD regenerated-input drift vs the committed bundle (class-hour to
  ~GW scale, annual lw λ within ~0.07), so gates are scored Run A → Run B,
  where the shared drift cancels and the A/B is unconfounded (the
  ercot150a/miso-117 control-arm pattern; a redirected replay mints its own
  dated id, never the keeper's).

* **Run B — the pool arm, single delta on the same config:**

  ```
  python scripts/replay_keeper.py results/calibration/ercot150_zonalanchor_B \
    --out-dir results/calibration/ercot158_poolarm_B \
    --set ercot_faststart_pool_offer=true \
    --note "ERCOT-158 Run B: single delta off the ercot150b keeper config — \
  ercot_faststart_pool_offer=true (ERCOT-88 CT pool, first run with its 2023 \
  year block); A/B vs ercot158_honest_A."
  ```

  `--set` routes through the generic prb_overrides ScenarioConfig channel
  (merged into the keeper's recorded override dict; no
  `ercot_faststart_pool_offer` solve kwarg exists, so there is no
  kwarg-over-prb re-stomp exposure — the exact channel the ERCOT-89 probes
  used, mechanism verifiably ENGAGED there).

## 2. Mechanism statement (what `ercot_faststart_pool_offer=true` does)

`build_ercot_faststart_pool_markup` (src/market_sim/data/fleet/offer_surfaces.py)
offers the telemetered-offline startable CT pool to the LP at its measured
start-inclusive price:

* **Object**: merchant CT rows (the cleared-share wall's measured CT scope)
  whose within-plant cumulative-capacity midpoint lies above the hour's
  net-load-bin measured pool boundary `1 − pool_frac(bin)` — the top-of-curve
  capacity that in reality is telemetered OFFQS/OFFNS (offline-startable).
  Target price interpolates the pool's measured above-LSL SCED2 ladder
  (per net-load bin, × delivered-gas day normalizer); markup =
  `max(0, min(target, cap_frac×VOLL) − mc_base)` — the pool only ever RAISES
  a bid, and a row whose target sits below base cost bids cost.
* **REPLACE-BY-MASK (rule 19)**: the builder returns `(markup, own_mask)`;
  in pool-owned row-hours every other offer surface's markup (conditional
  peak surface, cleared-share DA wall, RT leg alike) is REPLACED — one owner
  per row-hour, enforced at the composition site. **Hard-errors unless
  `ercot_offer_surface_cleared_share` is armed** — the keeper config arms it
  (meta: `ercot_offer_surface_cleared_share=true`), so the precondition holds
  by construction.
* **An offer-availability, NEVER a floor**: no `min_gen` is touched — no
  forced energy exists to attribute, so **D-2/D-4 exposure is vacuous by
  construction** (charter §9.1) and the rule-17 hazard (a CT floor binding
  overnight) is structurally impossible.
* **Eligibility is unit physics** (rule 18): `min_down_hours ≤
  FASTSTART_POOL_MIN_DOWN_HOURS`; CC rows fail by physics (4–8 h min-down),
  ST_GAS by 8–12 h. Never a class tuple.
* **Year-scoped, zero fitted scalars** (rules 13/23): no pooled fallback; the
  2023 block (new, ERCOT-157: full 315-shard corpus, interval counts
  [8750, 8759, 7002, 3504, 3500, 2408, 809], pool_frac 0.035–0.095, p70 mult
  449.6–482.1 — 2023's post-Uri conservative-ops conduct, ~2/3 of 2024's
  ladder level) engages 2023 for the first time; 2024/2025 read blocks
  byte-identical to what ERCOT-88 built. The artifact is frozen against
  residuals.
* **Rule-19 reconciliation (enumerated per the diagnosis §3)**:
  `ercot_gas_commitment_bridge` owns the ON committed CC min-gen state
  (disjoint — the pool prices OFFLINE CT rows); P1 startup amortization owns
  started-run pricing (the pool REPLACES, never stacks, in its mask); the RT
  wall owns the ON fleet's ladder (disjoint by status). No third channel.
* **Forward story (rule 17/13)**: conditional conduct (net-load bin ×
  physics tier) regenerates for a forward year from forward net load exactly
  as the DAM/RT walls do, and responds to changed conditions.

## 3. Expectation management (stated before any number is seen — rule 1)

**Primary expectation: NOT SUFFICIENT to flip the 2023 missed tail.** The
target residual is the keeper's 91 missed 2023 >$300 hours (of 144 actual;
model mean $105.11 vs actual $859.92 — Phase 0). At those hours the
config-collapsed startable-OFF increment is CC 10.32 GW (8.24 ≤$200 on
submitted DAM curves) + CT 7.81 GW (5.22 ≤$200) against a ~0.5 GW cushion.
The pool re-prices ONLY the fast-start CT slice; the CC offline block stays
un-repriced (ERCOT-152: measured no-op — its curves are genuinely cheap; its
phantom depth is a COMMITMENT-STATE gap, cap-side expression closed). ~8 GW
of cheap non-CT offline depth therefore remains, and the LP is expected to
clear around the repriced CT slice — the recorded ERCOT-88 2024/2025
signature. **The arm's value either way is the measured 2023 anatomy**: with
the CT slice priced at conduct, how much cheap depth remains at the matched
hours, does any real tail hour flip, and where does the marginal unit land —
the quantified residual this lane's successor (the commitment-state gap)
inherits. Honest secondary risk: pool-owned CT row-hours becoming marginal in
LOW bins would lift sub-$150 hours $9–19 (the ERCOT-89 death-by-small-lifts
signature) — the net-load-bin scoping is the protection and the
zero-spurious gate is the kill.

Predicted directions, run B vs run A:

* **2023**: low/mid-band ≈ unchanged (pool prices high; low-bin boundary
  ~0.965–0.905 scopes it to top-of-curve CT). Tail: possible small formation
  at matched hours where the marginal cushion was thinner than the CT OFF
  share; C3a 2023 (≈ −33% on the keeper) may improve immaterially. No
  material movement is the base case.
* **2024/2025**: pool blocks byte-identical to ERCOT-88's; its solo probes
  measured near-tail-inertness (173/91 pool rows engaged). Expect ≈ Run A
  within LP-vertex noise; all four analyzer gates must HOLD.
* **Engagement (validity precondition, not a verdict)**: the pool must engage
  in 2023 (pool-owned row-hours > 0, reported per bin). Zero engagement =
  mis-wire → fix-or-abort, not a mechanism verdict.

## 4. Pre-declared gates (scored Run A → Run B, per year, no exceptions)

Analyzer: the standing `scripts/probes/_ercot89_span_check.py`
(`--base results/calibration/ercot158_honest_A --probe
results/calibration/ercot158_poolarm_B --years 2023 2024 2025`) — the exact
ERCOT-89 pre-committed gate semantics, unchanged:

| gate | definition (per year, each of 2023/2024/2025) | kill condition |
|---|---|---|
| **C3a level guard** | annual demand-weighted resid: \|resid_B\| ≤ \|resid_A\| + 1.0 pp | any year DEGRADED |
| **Zero-spurious** | Δ(hours model ∈ [$150,$500] & actual < $150) ≤ 0 | any year TRIPPED |
| **Tail-count** | \|h>$200_B − h>$200_actual\| ≤ \|h>$200_A − h>$200_actual\| | any year moves AWAY |
| **NRMSE (C3b proxy)** | NRMSE_B ≤ NRMSE_A + 0.005 | any year DEGRADED |

Plus, same standing:

* **C3c matched-hour anatomy (the ercot148/149 discipline)** — scored on the
  Phase-0 hour sets (2023: 144 actual >$300 hours; the keeper's 91
  missed / 53 hit split re-derived on Run A's own prices for exactness):
  report Run A → Run B model mean/median at the missed and hit sets, count of
  missed hours flipped (model ≥$300), and **every NEW 2023 model >$300 hour
  must lie inside the actual >$300 set — zero new spurious tail hours**. Tail
  formation on quiet days is a kill regardless of the aggregate gates.
* **Scorecard holds (vs Run A statuses)**: C1 16/16 (12/12 free), C2, C4, C8
  PASS held; C3b 2024/2025 PASS held; C7 2024/2025 lignite legs held (the
  2023 cv-leg is a standing keeper FAIL — must not worsen in kind). The
  standing 2023 fail set {C3a, C3b, C3c} may only improve or hold.
* **D-2/D-4 zero-forced-energy**: `legitimacy_diagnostics.json` for Run B
  must show NO new forcing mechanism id and forced-share rows unchanged
  (within noise) vs Run A — the pool is an offer-availability; any forced
  energy attributed to it is a structural bug and a kill.
* **DOF/C6**: n_residual MUST NOT rise (zero fitted parameters added; the
  pool ladder/boundary are measured, rule-23 frozen). C6 governance block
  copied and attested honestly BEFORE the verdict run.

**LOYO (rule 24):** zero fitted parameters ⇒ structurally LOYO-exempt per the
ercot145b/148/149/150 precedent, with the per-year guard table standing in:
all three years' gates must clear **independently** — a 2023 gain bought with
a 2024/2025 guard trip is overfitting-shaped and REJECTS the arm. No
parameter exists to re-fit; the frozen artifact is not re-swept against any
residual of this A/B (rules 1/11/23).

## 5. Decision rule and registration (pre-declared)

* **K (keeper candidate)**: matched-hour 2023 movement is real (missed-hour
  flips at actual-tail hours), all §4 gates hold all three years → promotion
  via the keeper lane (`keepers/ERCOT.json` + `build_status.py --iso ERCOT` +
  `calibration-keeper-auditor` + matrix header re-stamp; ERCOT holds no
  `complete` marker, so no re-key duty).
* **R (rejected)**: any §4 kill fires → mechanism stays merged default-off,
  matrix cell `R` with this doc + both bundles as evidence.
* **I (inert)**: gates hold but movement at the matched hours is not
  material (the base-case expectation) → matrix cell `I`; the measured
  anatomy is the deliverable the successor lane inherits; mechanism stays
  default-off.
* **Either way**: BOTH runs are registered on the backcast dashboard in this
  session (rule 15 — bundle + sidecar + run payload committed and pushed;
  Run A is a completed calibration run on honest inputs and is registered
  regardless of Run B's verdict), the `ercot_faststart_pool_offer` matrix
  cell is updated with the tested verdict + citation in the same session
  (rule 28(b)), and both runs are logged in `docs/calibration-log/ercot.md`
  as ercot-158. Whether Run A itself is a keeper candidate (honest-inputs
  re-solve of the keeper config) is scored on its own standing rubric
  numbers vs the committed keeper and surfaced to the owner; its verdict
  never gates Run B's A/B.

## 6. Open owner rulings carried (surfaced, not decided)

Unchanged from the ercot150b promotion note: (9) the DAM deriver `_site()`
cross-train collapse + gas crosswalk partial acceptance; (10) the pin
remove-direction over-removal; the standing (8) rating-basis gap; the CC
econ-band under-dispatch (ERCOT-138/139 object) — which this lane's Phase-0
measurement quantifies from the offline side and which the pool arm, by
design, does NOT touch (CC stays un-repriced per ERCOT-152).
