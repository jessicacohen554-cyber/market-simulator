# PREREG miso-181 — the D-2 coincident-peak seam-RESPONSE envelope: form, identification, no-LP pre-checks with the rank-displacement predictor, the conditional combination arm, and the gated A/B — every rule fixed BEFORE any measurement

**Session miso-181, 2026-08-24.** Keeper `2026-08-22-miso-177-rho-measured`
(bundle `results/calibration/miso177_rho_B`; NOT-YET on C3a-2025 alone
(−11.747 %; 2023 +1.279 / 2024 −4.064; band ±10 % ⇒ +1.75 pp needed), C3b
PASS, C3c the single ledgered caveat, C6 attested, C8 PASS all years, zero
D-4 conduct failures).

**Charter (owner grant, in the session prompt, 2026-08-24).** By issuing the
prompt the owner RULES ON 5(i) and GRANTS **D-2**: a seam-import RESPONSE
envelope conditioned on the NEIGHBOUR'S OWN coincident load is **ADMISSIBLE
IN KIND** — the neighbour's load is a forward driver (regenerates from its
own demand trajectory, responds to changed conditions, rule 13), and the
binding physics is measured, not fitted (miso-176: MISO over its own
firm-flow entitlement on 67/82/80 % of scarce binding rows; JOA congestion
management binding 4–6× harder at stress). The known correlation with MISO's
own scarcity (coincident summer peaks) is **DISCLOSED** and is not, by
itself, residual-fitting — but **every parameter must be identified from
seam/neighbour-side measurement, never from a MISO price residual**; a
residual-swept envelope is the rule-1 fitted-adder KILL. A separate FFE-MW
cap stays `G` (miso-176 K-2: no published seam-grain entitlement aggregate —
nothing here re-opens it). **D-3 (South under-export evidence) stays OPEN —
not built here.** The lever is the top named object in the matrix §5.4 MISO
queue (duty 26(a): on-queue).

**Order of operations, auditable in the commit history** (the
miso-176/177/179/180 discipline): **THIS DOCUMENT, committed and pushed** →
the pre-check probe (§4: driver/envelope construction, then K-a → K-b → K-c
and the combination-arm condition) → IF AND ONLY IF the session-level kills
are all clear: the gated implementation (§3, OFF path proven inert before
any solve) → control solve → arm solve(s) → gates (§5) → verdict mapping
(§6). No hour-set-conditioned quantity of this session exists before this
document's commit; every measured number cited below is a COMMITTED prior
artifact (the miso-174/176/178/180 records and findings).

---

## 1. The object (committed evidence only; nothing new measured yet)

The 2025 residual is a supply-side object at the binding hours, not an
offer-surface object at any grain (miso-179 level `R`, miso-180 spread `I`):
the LP meets the 88-hour actual RT>$200 tail with **+2.07 GW phantom net
import and −5.3 GW gas** vs measured (miso-178 §5; miso-174: +1.41 GW on the
47-h scarce set, of which the PJM seam is the only all-years import-side
component, +0.87/+0.72/+0.94 GW). The named, evidenced structure:

* **The real PJM seam moves AWAY from MISO at coincident stress; the
  model's moves toward it** (miso-174 §3b): measured scarce-hour response
  vs own summer mean **−0.77/−0.54/−1.03 GW**; model **+0.89/+0.48/+1.34
  GW** — sign-opposite in all three years. The measured seam is essentially
  uncorrelated with the hourly price spread (r ≈ +0.06/+0.05/−0.06): the
  real seam does not arbitrage the spread; the model's priced seam is a
  spread-arbitraging supply curve bounded only by an unconditional p90
  envelope.
* **The physics is measured and named for about half the hours** (miso-176):
  seam-class M2M binding CO-MOVES with MISO's scarce hours (3/3 years,
  shadow-basis 3.8–5.7×), is restriction-consistent (2/3), and on the
  binding rows MISO sits OVER its firm-flow entitlement 67/82/80 % — the
  JOA's congestion-management obligation in exactly those hours is to push
  MISO back toward its entitlement. The non-binding half still pulls back
  (miso-176 §4) — TLR-class events, deeper PJM-internal congestion,
  scheduling conservatism: coincident-stress conduct, partly unnamed.
* **Manitoba is the control**: the one seam carried by a firm contract
  block is the one seam the model reproduces (miso-174 §3b).

**AGAINST-INTEREST NUMBERS, carried honestly (charter order):** miso-174 §6
measured the envelope's reach at the CURRENT stack slope as near-inert alone
(+3.3/+7.7/+3.9 $/MWh in scarce hours ≈ 1–2.5 % of the miss), and the mean
rank displacement of 2.1 GW over the ~60 GW affected stack is only ~+0.035.
The live channel is the ALREADY-EXPOSED tail hours (the miso-180 K-c
59-hour set, whose clearing rank already reaches ≥ 0.875), where a
pull-back pushes the rank INTO the now-existing grafted steepening (the
built, default-off, adjudicated-`I` `miso_offer_spread_anchored`). **That
coupling is a HYPOTHESIS the pre-check must measure per-hour, never a
promise.** Ceilings: model@DA +1.96 %; deterministic-reachable space
−13.71 pp (miso-178 §3–4).

**Falsifiable cross-zone prediction, unchanged (rule 1):** the 2025 zonal
miss is a dipole (Midwest −4.3…−15.2 % under vs MISO-South **+17.0 %
OVER**; South +18.8/+21.0 in 2023/24). Less phantom import at Midwest
stress hours raises Midwest prices and lowers southward export pressure;
the South over-price must move TOWARD ZERO with **no South-specific
mechanism**. An arm that improves C3a-2025 while leaving the dipole intact
has NOT captured the real object.

**The distinction from `import_shape_lever` (MISO `G`), stated as the
charter requires:** that refusal concerns the seam's **hour-of-day price
shape** — miso-123 exonerated the envelope family of the diurnal defect at
r = +0.81…+0.996, and no hour-of-day lever may be re-opened. The chartered
object here conditions on the **neighbour's own load STATE** — the seam's
response to coincident regional stress, a dimension miso-174 §3 explicitly
named as covered by neither the shape cell nor `measured_interface_limits`.
Nothing in this mechanism keys on hour-of-day beyond what the existing
armed envelope already carries.

## 2. The mechanism (proposed form, frozen) — a CONDITIONING of the armed envelope, not a second cap

One new gated `ScenarioConfig` field, **`miso_seam_coincident_envelope:
bool = False`** (registered, cache-key drop-at-default per the nyiso-119
discipline; armed key hashes distinctly; run_config-recorded; rule 24;
CLI `--miso-seam-coincident-envelope`; `replay_keeper --set`-able).

**Rule-19 reconciliation (design duty i).** The keeper's seam-envelope
family is `miso_seam_flow_limit` / `miso_seam_export_limit` with
`miso_seam_envelope_merit_cap` and `miso_seam_envelope_hour_ending_key`
armed — one measured deliverability envelope per seam × direction, applied
as the per-hour ceiling the LP clears below
(`measured_seam_import_envelope` → `inject_miso_seam_flow_limit`). The new
flag **conditions that same envelope's PJM-seam import ceiling on the
neighbour-load state inside the same construction and the same injection
path** — same percentile constant, same hour-ending key, same merit-cap
waterfall, same seam rows. No new cap object, no new LP rows, no second
mechanism on the same MW: with the flag off, the returned cap arrays are
byte-identical.

**Construction (armed, MISO only, PJM seam only, import direction only):**

1. **Driver series.** PJM's own measured hourly demand: the EIA-930
   BALANCE `D` series (`data/raw/PJM_region.parquet`, `type == "D"`,
   committed; UTC `period` mapped to the model's CST hour key by −6 h, Feb
   29 dropped, the `_miso174` `e930_balance` convention). Per hour *t*, the
   **neighbour-load percentile** `b(t)` = the percentile rank of PJM demand
   at *t* within the SAME YEAR's finite demand values (pandas
   `rank(pct=True)`, average ties, × 100). Hours with missing driver value
   carry no conditioning (**fail-open** to the existing envelope).
2. **Bin grid (declared convention, not a fitted parameter).** Edges
   **[0, 50, 75, 90, 95, 97.5, 99, 100]** — seven bins of the
   neighbour-load percentile axis, declared here ex ante exactly as the
   199-point GRID and the (month × hod) buckets are declared conventions.
   No edge is ever moved in response to any result of this session.
3. **Conditional envelope level (measured; the same percentile constant).**
   For each bin *b*: `cond_cap(b)` = the `MISO_SEAM_FLOW_PERCENTILE` (=
   90.0, the existing armed constant — no new number) percentile of the
   MEASURED PJM-seam net import over the same year's hours falling in bin
   *b* (the EIA-930 DIBA product pooled by `MISO_SEAM_DIBA["PJM"]`, read at
   the keeper's armed −1 h hour-ending key — the miso-174-solved,
   miso-175-armed convention), clipped ≥ 0. Hours with missing seam
   measurement drop from the bin population.
4. **Composition.** The PJM seam's import cap becomes, per hour,

   > `cap′(t) = min( cap_p90(month(t), hod(t)) , cond_cap(b(t)) )`

   — the joint (bucket × state) envelope represented by the min of its two
   measured marginals (the joint grain is unmeasurable at p90 without
   sparse cells; the min never loosens the armed cap and never forces a
   flow — a capability/response ceiling, exactly the existing envelope's
   semantics). SPP / South / Manitoba seams, the export direction, and
   every other ISO: **byte-untouched**.

**Parameters and their identification (design duty ii).** The percentile
(existing constant), the bin edges (declared convention), the conditional
caps (measured EIA-930 seam flows), the driver percentiles (measured
EIA-930 PJM demand). **The identification path contains NO MISO LMP, no
model output, and no residual anywhere.** The M2M/CMP FFE record is the
physics EVIDENCE for the mechanism's reality (miso-176 A-2/A-3/A-4); **zero
parameters derive from it** (K-2 stays `G`; no apportionment is invented).
DOF ledger: measured entries only; `n_residual` UNCHANGED at 2. Re-derives
only when the source data updates (rule 23). Zero fitted scalars: **there
is nothing in this mechanism a residual sweep could tune** — that is the
form the 5(i) ruling's discipline demands.

**Window / driver / forward story (design duty iii, rule 17 in spirit).**
*Driver:* JOA/M2M congestion management plus the neighbour's own
native-load obligation at coincident regional stress — measured (miso-176:
co-moves 3/3, restriction-consistent 2/3, MISO over-FFE 67–82 %;
miso-174 §3b: the measured seam withdraws −0.77/−0.54/−1.03 GW at MISO's
scarce hours). *Window:* none imposed — the binding hours are wherever the
neighbour's own load state and the measured conditional distribution put
them; K-c VERIFIES (never assumes) that the binding concentrates at
neighbour peaks. *Forward story:* in a forecast year the conditioning
regenerates from the neighbour's own forward load trajectory (each hour's
percentile within its own year) with the conditional response identified
from multi-year measured history — it responds to changed conditions
(hotter years, load growth, peak-timing shifts move the binding hours with
them). The same-year measured substrate in backcast mode is exactly the
existing envelope family's convention (a rule-13-admissible measured
physical/market input, not an outcome pin: no MISO price or dispatch
outcome is consumed).

**Telemetry (consumed by G-1):** when armed, the run records per year the
bin caps, the count of hours where `cap′ < cap_p90` (conditioned hours),
and the mean tightening MW over those hours.

## 3. The combination arm (design duty iv) — the `miso_offer_spread_anchored` re-open clause, exercised only through its own gate

`miso_offer_spread_anchored` is adjudicated **`I`** with a stamped re-open
clause: new evidence = "a model whose clearing rank reaches the top decile
… when the same graft would bind" (FINDING-miso180 §5). The charter
authorizes re-arming it **inside this session's combination arm ONLY**, and
only if the pre-check shows the predicted rank displacement reaches the
0.875 anchor in a material hour set. Frozen build condition — **arm C
(envelope + `miso_offer_spread_anchored=true`) is built if and only if ALL
of:**

* (C-1) every session-level kill in §4 is clear (the envelope arm B is
  proceeding);
* (C-2) the grafted-stack K-b leg clears: predicted C3a-2023 with the
  mechanism ceiling `R_hi` on the GRAFTED stack stays inside ±10 %;
* (C-3) **materiality of the coupling**: in 2025, under the intersected
  mechanism estimate `R_lo` (§4), the count of hours with `R_lo(t) > 0`
  whose displaced clearing rank `r′(t) ≥ 0.875` is **≥ 20**;
* (C-4) the incremental predicted 2025 reach (grafted-stack minus
  ungrafted-stack prediction, both at `R_lo`) is **≥ +0.10 pp**.

If any of C-2/C-3/C-4 fails, arm C is NOT built, the envelope arm B
proceeds alone, and the `miso_offer_spread_anchored` cell is untouched
(stays `I`, its re-open clause unspent — the pre-check result is recorded
as evidence either way). The `R_hi` analogues of C-3/C-4 are reported
beside the adjudicating `R_lo` values, adjudicating nothing.

## 4. The no-LP pre-checks — kills fixed NOW, before any of them is computed

Probe `scripts/probes/_miso181_seam_response_precheck.py` (descends from
the `_miso180_anchored_spread_precheck.py` machinery: the `_miso178`
wrapper repoints `_miso156` to `miso177_rho_B`; `carry_price_demand`, the
frozen affected mask, `weighted_quantiles`, the committed dispersion vector
+ `MISO_OFFER_SPREAD_ANCHOR_RANK` = 0.875; and from the `_miso174`
measured-side machinery: `diba_wide` at the solved −1 h key,
`e930_balance`, the non-leap 8760 fold) →
`results/calibration/_miso181_seam_response_precheck.json`.

**Validity gates (all hard-ABORT if failed):** V1 reproduces C3a
+1.2813 / −4.0643 / −11.7421 % to ±0.5 pp per year as each year loads; V4
n_gen 2929/2923/2923, carry zones 6; the dispersion artifact's sha256
equals the pinned `b4e72312…de28` and its grid equals the frozen
`QUANTILE_GRID`; the anchor consumed equals `MISO_OFFER_SPREAD_ANCHOR_RANK`
= 0.875 = the committed miso-180 identification; the DIBA hour key
re-verified (the −1 h shift correlates DIBA-sum net import against BALANCE
−TI at r ≥ 0.999 in 2023 AND 2025 — the miso-174/175 solution; 2024's
published internal inconsistency r ≈ 0.83 is disclosed, not gating);
PJM driver coverage ≥ 8,600 finite hours per year.

**The removal series (per year; PJM seam, import direction):**

* `R_bound(t) = max(0, model_net(t) − meas_net(t))` — the charter's K-a
  bound ON THE KEEPER'S COMMITTED HOURLIES: `model_net` = the keeper's P1
  `import`-class net interchange (the only interchange grain the committed
  keeper carries — the per-seam `unit_hourly` bundle `miso169_gated_A` was
  pruned at miso-180 registration, disclosed here ex ante); `meas_net` =
  −TI (EIA-930 BALANCE, CST key). Hours with missing TI ⇒ `R_bound = 0`.
  DISCLOSED GENEROSITY, both directions stated: the aggregate excess
  includes non-PJM components a PJM-seam mechanism cannot reach (South
  under-export inflates it; Manitoba under-import deflates it) and no
  substitution channel exists in the predictor — `R_bound` is the honest
  CEILING of the mechanism class, proper for a STOP decision and never
  quoted as the mechanism's own reach.
* `R_hi(t) = max(0, cap_p90_PJM(t) − cond_cap(b(t)))` on driver-covered
  hours, 0 elsewhere — the mechanism's own ceiling (assumes the model sits
  at the armed cap wherever the conditioning tightens; overstates,
  declared), where `cap_p90_PJM` is the PRODUCTION armed envelope
  (`measured_seam_import_envelope("MISO", y, 8760, None, "import",
  hour_ending_key=True)`) and `cond_cap(b)` is §2's construction computed
  by the probe exactly as the arm would.
* `R_lo(t) = min(R_hi(t), R_bound(t))` — the intersected mechanism
  estimate (each factor overstates; the min is still an estimate, not a
  bound, declared).

**The rank-displacement predictor** (per year × removal series × stack
variant; the K-PRE-c machinery extended one step): `r*(t)` = the
availcap-weighted share of affected mass with `mc_base ≤ P_mod(t) + $0.01`
(verbatim); `W(t)` = the affected stack's total available capacity;
`δr(t) = R(t)/W(t)`; `r′(t) = min(r*(t) + δr(t), 1.0)`. Per-hour stack
curves, the same estimator semantics as `weighted_quantiles`:

* **Ungrafted:** `ΔP(t) = max(0, Q_t(r′(t)) − Q_t(r*(t)))` with `Q_t` the
  affected stack's own availcap-weighted quantile step function of hour-t
  `mc_base`.
* **Grafted:** `Q^g_t(r) = max(Q_t(r), A_m(t) + (Q̂(r) − Q̂(0.875)) ×
  G_ref(month(t)))` for `r > 0.875`, else `Q_t(r)` — `A_m`, `Q̂`, `G_ref`
  the miso-180 §3 constructions verbatim; `ΔP_g(t) = max(0, Q^g_t(r′(t)) −
  Q_t(r*(t)))`.

`P′(t) = P_mod(t) + ΔP(t)`; predicted C3a = `Σ w·P′ / Σ w / bench_rt_lw −
1` (the committed statistic, carry-demand weights). **Declared biases:**
no substitution (miso-180 measured the static predictor's overstatement at
4.5× — a pass is weak evidence FOR, a kill against the bound is strong
evidence AGAINST); the aggregate-vs-seam generosity above; the maxgen
ceiling not enforced in the adjudicating numbers (the count of hours with
`P′ > $500` and a $500-capped variant of every reach number are REPORTED
beside them, adjudicating nothing).

**The kills, adjudicated in the frozen order a → b → c** (all quantities
computed and reported in full even when an earlier kill fires):

* **K-a — reach (STOP ⇒ mint `I`-on-arrival).** Predicted C3a-2025 shift
  under `R_bound`, on BOTH stack variants. **STOP: shift < +0.5 pp on
  BOTH.** (If removing the FULL measured aggregate excess, priced with no
  substitution on the steeper grafted stack, cannot reach half a point
  toward the +1.75 pp need, no admissible envelope in this class can — the
  object is inert here; no LP.)
* **K-b — the against-interest year (KILL ⇒ mint `R`,
  REFUSED-BY-PREREG).** Predicted C3a-2023 under `R_hi` on the UNGRAFTED
  stack (the envelope arm as it would be armed; the predictor's every
  declared bias overstates the 2023 push, the precautionary direction).
  **KILL: outside ±10 %.** The grafted-stack 2023 prediction is C-2's
  gate (§3): it kills only the combination arm, never the session.
* **K-c — conditioning sanity (STOP ⇒ mint `R`, uniform-binding
  refusal).** By the envelope's OWN driver, model-free: with weights
  `R_hi(t)` (the tightening MW), in EACH of 2023/2024/2025:
  **(i) ≥ 50 % of `Σ_t R_hi(t)` must lie in hours with neighbour-load
  percentile ≥ 90** (a ≥ 5× concentration into 10 % of hours), and
  **(ii) ≤ 10 % of `Σ_t R_hi(t)` may lie in hours with percentile < 50.**
  Any year failing either ⇒ the envelope is a level lever in costume —
  STOP. Reported beside, adjudicating nothing: the monthly distribution of
  the tightening, the per-bin caps and populations, and the conditioned
  hour counts.

**A fired session-level kill ends the session with NO LP:** the pre-check
FINDING is written; the matrix base row `miso_seam_coincident_envelope` +
all six shard cells are minted with the MISO cell `I` (K-a) or `R`
(K-b / K-c) and the five others `·`; the §5.4 stamp + calibration-log
entries land in-session; and the lane falls back to the OPEN owner items —
**D-3 (the South under-export evidence session)** becomes the queue head,
with its handoff sketch recorded in the FINDING. Nothing is built, no
field is created (the miso-179 pattern).

## 5. The A/B (only if every session-level kill clears)

Implementation lands first, gated OFF by default, with the OFF path proven
inert BEFORE any solve: default cache key unmoved (pin tests + the
registered-key check), armed key distinct, the envelope arrays byte-
identical with the flag off, non-MISO inertness (the seam-DIBA gate
already scopes the loader to MISO; asserted in tests), unit tests on the
construction (min-composition never loosens; PJM-seam/import-only scope;
fail-open on missing driver; bin-population and clip semantics; telemetry
recorded; zero-conditioned-hours hard-error while armed).

Control and arm(s) are `replay_keeper.py` replays of the committed keeper
at HEAD, run SEQUENTIALLY and ALONE (rule 12; MISO plant-level), each the
FULL span 2023 2024 2025 in ONE invocation (rule 16), under the miso-169
15 GB recipe (pinned stack `highspy==1.14.0 pandas==3.0.3 pyarrow==24.0.0
numpy==2.4.6 scipy==1.17.1 pydantic==2.13.4` + openpyxl, python 3.11 per
the bundle's recorded environment; `MARKET_SIM_HIGHS_THREADS=4`; 8 GB
swapfile; abandon-before-solve if available RAM < 13 GB):

```
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso181_seam_A \
  --note "miso-181 CONTROL: byte-faithful keeper replay at HEAD (miso_seam_coincident_envelope at default off)"
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso181_seam_B \
  --set miso_seam_coincident_envelope=true \
  --note "miso-181 ARM B: neighbour-load-conditioned PJM-seam response envelope (single delta)"
# ONLY if §3's C-1..C-4 all fired:
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso181_seam_C \
  --set miso_seam_coincident_envelope=true miso_offer_spread_anchored=true \
  --note "miso-181 ARM C: envelope + the re-opened anchored spread graft (the coupling arm; PREREG §3)"
```

Registration ids `2026-08-24-miso-181-control` /
`2026-08-24-miso-181-seamresp` / (if built)
`2026-08-24-miso-181-seamresp-spread` — **ALL solved runs registered
whatever the outcome** (rule 15), full 3-year bundles with hourly sidecars
incl. `reserve_family` (rule 16 / the KEEPER sidecar clause). Arm
attestations generated from the keeper's per the `gen_miso180_attestation`
pattern; controls stay UNATTESTED by convention.

Gates, fixed now — the PREREG-miso179/180 §5 set VERBATIM with the
mechanism name swapped; arm B is the adjudicated arm, and arm C (if built)
is scored against the SAME gates with its own G-1/G-2 lines:

* **G-0 CONTROL BIT-IDENTITY (ABANDON).** All 12 scored sidecars
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical (numeric max|diff| = 0, identical row sets) to the
  committed keeper's. Anything else ⇒ HEAD drift or a non-inert default —
  STOP, report, no arm conclusion.
* **G-1 ARM VALIDITY (KILL).** The arm's `run_config.json` records the
  flag true and the control's false/absent; the telemetry records
  conditioned hours > 0 in every year; the probe-computed and arm-consumed
  bin caps agree to 1e-6 (same construction, same data); for arm C
  additionally the artifact sha256 equals the pinned digest and the anchor
  consumed is 0.875.
* **G-2 C3a-2025 DIRECTION.** Δ = arm − control C3a-2025 in pp.
  **Δ ≤ −0.25 pp ⇒ KILL** (regression). |Δ| < 0.25 ⇒ the mechanism is
  measured INERT here (verdict `I`, §6). Δ ≥ +0.25 ⇒ the improvement leg
  is satisfied.
* **G-3 AGAINST-INTEREST BAND (KILL).** C3a-2023 AND C3a-2024 each inside
  ±10 % on the arm.
* **G-4 C3b (KILL).** The C3b criterion PASSES all three years on the arm.
* **G-5 CONDUCT (KILL).** C8 PASS in all three years on the arm (grounded
  form allowed), AND zero NEW D-4 conduct failures vs the regenerated
  control's `legitimacy_diagnostics.json`.
* **G-6 DOF (KILL).** The arm bundle's ledger: `n_residual` unchanged (2);
  the new entries' identification is `measured` with zero fitted scalars.
* **G-7 RECORD FLIPS (KILL).** Zero PASS → non-PASS flips across the
  verdict scorer's records, arm vs the committed keeper.

Reported in full, gated by nothing (the charter's ungated list): **the
South-dipole prediction** (the `_miso180_structural_reports` zonal stage on
ALL bundles; ex-ante expectation: MISO-South 2025 own-error +17.0 % moves
toward zero); **the Δ-channel re-run** (the miso-156 instrument on the
arm(s): Δ₁ must collapse for the object to be real — its movement is
reported at full magnitude either way); **the miso-178 tail/body bucket
decomposition** on the arm(s); **seam-flow realized-vs-envelope** (the
arm's PJM-seam import against `cap′`: binding shares and conditioned-hour
utilisation, computed from locally-written unit-level output where the
replay writer supports it, else from the `import`-class aggregate + the cap
arrays; unit-level parquets are NOT committed — the summary lands in the
A/B record); **maxgen $500/$1,000 ceiling encounters** control vs arm(s);
**the rank-displacement predictor's audit** (predicted vs realized, all
three years, all removal variants); load-weighted price deltas annual /
JJA / DA-foreseen vs RT-only; C3c tail-hour counts at full magnitude.

## 6. Verdict mapping and the promotion decision rule, fixed now

* **A §4 session-level kill fires** → NO LP; §4's closure path (FINDING,
  cell `I` on K-a / `R` on K-b or K-c, stamps, D-3 becomes the queue
  head).
* **G-0 fires** → ABANDONED-AT-CONTROL; escalate the drift; no arm
  conclusion; nothing registered as arm evidence.
* **Any of G-1/G-3/G-4/G-5/G-6/G-7 fires on arm B, or its G-2 kills** →
  arm B **REJECTED-AS-ARMED** with the firing gate named; all solved runs
  registered; MISO cell `R` with evidence; keeper unchanged. (Arm C, if
  built and also failing, records its own firing gate;
  `miso_offer_spread_anchored` stays `I` — a failed coupling arm is not
  new evidence FOR the graft.)
* **All kills silent + arm B G-2 inert** → verdict **`I`**; all
  registered; keeper unchanged; the FINDING records where the removed
  import went instead (the substitution channels the predictor declared
  absent) — that is itself the structural datum. If arm C was built and
  ITS G-2 shows ≥ +0.25 while B is inert, the coupling is the live object:
  ESCALATE with both records (no self-promotion on a C-only improvement;
  the graft cell's re-open evidence is recorded either way).
* **All kills silent + G-2 improvement on the candidate arm + BOTH
  structural legs confirm** — (a) MISO-South's 2025 own-error strictly
  smaller in magnitude on the candidate arm, and (b) Δ₁ (2025 annual)
  strictly smaller in magnitude by ≥ $0.50/MWh of its control +10.45 —
  → **the candidate arm is the KEEPER-CANDIDATE and MAY BE PROMOTED THIS
  SESSION on this prereg's own rule.** The candidate is the arm with the
  largest C3a-2025 improvement among the built arms passing every gate;
  ties → arm B (fewer armed mechanisms). Promotion executes: keeper shard
  edit + `calibration-keeper-auditor` run + matrix re-stamp (both cells if
  C promotes) + calibration-log, all in-session. MISO holds no
  `calibration-complete` marker, so no re-key is owed (rule 22 D-5(b)
  vacuous).
* **MIXED — kills silent, C3a-2025 improves, but a structural leg fails**
  (dipole intact/worse, or Δ₁ not collapsing), or any structurally
  conflicted reading → **ESCALATE to the owner with all records, no
  self-promotion.** The owner's standing structural standard applies and
  is quoted verbatim: *"If structural integrity improves but gates regress
  that may still be a keeper."* Per §1, an arm that closes the number
  without moving the dipole and the price-setter identity has not captured
  the real object, and claiming it would be the rule-1 second-half
  violation.
* **An outcome none of these anticipate** is recorded as an unanticipated
  branch (the miso-151 precedent) — reported, never retrofitted into a
  listed branch.

## 7. Governance

* **Rule 22 [R-HOLDOUT]:** 2023/2024/2025 ONLY, one invocation per run;
  MISO holds neither marker; the holdout spend freeze is untouched.
  Leave-one-year-out at promotion: the identification consumes no
  target-year OUTCOME anywhere — driver percentiles and conditional caps
  are neighbour/seam-side measured inputs, the bin grid and percentile are
  declared constants — so LOO is vacuous by the miso-172/175/177/179/180
  precedent (frozen identification, committed measurements, zero fitted
  parameters), recorded, not re-derived per-year.
* **Rule 13 [R-MEASURED]:** the envelope is a measured physical/market
  RESPONSE input (deliverability under coincident stress), admissible in
  kind under the owner's 5(i) ruling; it regenerates for a forward year
  from the neighbour's own forward load trajectory + the measured
  multi-year conditional response, and responds to changed conditions. No
  MISO outcome is pinned; no parameter touches a residual.
* **Rules 23/24/25/26:** parameters are cited constants + committed
  measured series (re-derive only on data change, cited); the field is
  registry-visible and run_config-recorded; no env-var knobs; MISO-only
  action (rule 25 — the construction gates on the MISO seam map);
  matrix duties: the new mechanism's ROW + a cell line in EVERY ISO shard
  land in the same PR as the ScenarioConfig field (26(c)); the MISO cell
  verdict + §5.4 stamp + calibration-log land in-session whatever the
  outcome (26(b); a no-LP kill mints the row + cells without the field,
  the miso-179 pattern). `miso_offer_spread_anchored`'s cell is edited
  ONLY per §3/§6's frozen branches.
* **Rule 12 [R-PARALLEL]:** MISO plant-level solves run ALONE, years
  sequential within each invocation.
* **Rule 27 [R-PUSH]:** small commits, exact on-disk bytes, blob
  verification after any push touching a ≥300-line file; run payloads over
  `git push`; HTTP/1.1 fallback on 408/500 before any pack-size
  conclusion.
* No new `.github/workflows`. The owner merges; no PR unless asked.
* Disclosed data caveats, carried on every consuming number: the 2024
  EIA-930 DIBA↔BALANCE internal inconsistency (r = 0.8286 at the solved
  key vs 1.0000 in 2023/2025, miso-174 §5); the PJM demand series' small
  NaN counts (24/22/0 hours — fail-open); the pruned `unit_hourly` bundle
  (no per-seam model series exists at the current keeper — §4's R_bound
  grain disclosure).
