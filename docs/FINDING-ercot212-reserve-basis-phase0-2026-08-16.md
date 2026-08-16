# FINDING — ercot-212 (RESERVE-BASIS-1, card X item X-3): the ORDC zero-reading is fully attributed — curve-top saturation, a growing credit wedge, and a reporting seam; the pre-registered viability rule PASSES on a zero-fitted-scalar consistency candidate

**Session ercot-212, 2026-08-16, branch `claude/ercot-reserve-basis-x3-gjpsh9`.
Dispatch RESERVE-BASIS-1 (X-3 signed by dispatch; signature appended to
ASSESSMENT-ercot209 "RESOLUTIONS — CARD X" this session).** Phase-0 is
READ-ONLY: no LP, no year solved or scored in Phase-0, keeper
**`2026-08-15-ercot204-rule26-delete`** untouched. Precommit (pushed before the
probe ran): `docs/PRECOMMIT-ercot212-reserve-basis-phase0-2026-08-16.md`.
Probe: `scripts/probes/ercot212_reserve_basis_phase0.py` →
`results/calibration/ercot212_reserve_basis_phase0.json`.

## 0. VERDICT

The ercot-204 §A open object — why the armed ORDC counterpart reads ≈ zero
across the 560/253 published-fired hours of 2024/2025 while the model "holds
less reserve than the real system," and why 2023 is healthy — is **fully
attributed, construction-exact** (A0: the family dual reproduces the LP step
curve at `held + credits` to ≤ 2.4e-5 $/MWh in every shortfall hour of all
three years; the requirement identity `req = max(10,700 − lr − sas, 3,000)`
holds to 5e-4 MW). Three stacked causes, each measured at full magnitude, plus
one inversion of the ercot-204 premise:

1. **Curve-top saturation (requirement basis).** In **1,501/1,705 (2023),
   520/560 (2024), 249/253 (2025)** published-fired hours the model's marginal
   reserve level `held + credits` sits AT the static curve top (10,700 MW),
   where the price is **zero by construction** — the LP demands nothing beyond
   the 40-band span, and ample model headroom fills the whole credited span.
2. **The credit wedge (held-quantity + supply-cap basis).** The measured
   LR RRS-UFR and storage AS-award series are netted off the demand side
   (requirement) but **ride untouched on the supply side**: the reserve-supply
   caps are raw RTOLCAP / RTOLCAP+RTOFFCAP, telemetry that (by the code's own
   documented reading) already **contains** the online ESR and Load-Resource
   MW being credited. The model's marginal evaluation point can therefore
   reach `cap + credits`: in the fired hours it sits **+1,715 MW (2024) /
   +1,037 (2025) / +2,408 (2023) ABOVE published RTOLCAP** on average.
3. **The reporting seam (the ercot-198/204 "≈ zero" series).** The sidecar
   `ordc_adder` is the **additive uninternalized dual**, written **only in
   hours where the measured supply cap is the binding reserve constraint** —
   verified exactly: its nonzero hours are **identically** the cap-binding
   hours, 42/2/1 in 2023/2024/2025. In the other shortfall hours the physical
   shared headroom binds and the family dual — up to **$760/h in 2024** (11
   fired hours > $1: h2538-40, h2826-28, h3065-68, h5562) — is **already
   inside the energy LMP** (the co-opt transmission; the scored price carries
   it). ercot-198 §0's "the endogenous stand-in measures ≈ zero (2 non-zero
   hours in 2024)" is a true statement about the COLUMN and the additive
   channel, not about the mechanism: the broad-shallow published-fired region
   is genuinely missing (cause 1-2), but the deep-scarcity reserve content of
   2024's tightest hours is priced, endogenously, inside `price`.

**The ercot-204 premise inverts on the honest basis (the dispatch's
crosswalk-first demand).** `held_mw` (6,955 vs RTOLCAP 8,854 in 2024) is a
**demand-limited procurement quantity** — held ≈ the credited requirement in
nearly every fired hour — not a capability measure, so "the model holds less
reserve than the real system" was a basis artifact. On the reconciled common
basis the model's marginal level is pinned at 10,700 and sits **above** the
real system's reserve, and is **uncorrelated** with it (corr(B_model, RTOLCAP)
= 0.18 / 0.10 / 0.05 in 2023/2024/2025 live hours). §2 below states why the
two constructions cannot be component-reconciled further.

**Why 2023 is healthy: the cap-contact channel, which the growing credit is
closing.** The model's ONLY transmission from the real system's reserve dips
is the measured supply cap, and it binds only when `RTOLCAP+RTOFFCAP` falls
below the credited requirement (10,700 − credits). Fired-hours credits grew
**2,394 → 3,615 → 4,053 MW** (2023 → 2024 → 2025; storage AS awards 1,516 →
2,739 → 3,339 of it), pushing the requirement DOWN from 8,306 → 7,085 → 6,647
while the real cap's fired-hours p05 is 7,558 / 7,968 / 9,114 — so cap contact
collapses **42 → 2 → 1 hours**. 2023's 42 sidecar-adder hours (up to $1,920/h,
42/42 inside the published-fired set) ARE its 42 cap-binding hours. The year
gradient is the credit growth, not a curve change and not model comfort.

## 1. THE ATTRIBUTION TABLE (full magnitude, published-fired hours)

| quantity | 2023 | 2024 | 2025 |
|---|---|---|---|
| published-fired hours (rtorpa > 0, live) | 1,705 | 560 | 253 (252 settled) |
| … at model curve top (level = 10,700, price ≡ 0) | 1,501 | 520 | 249 |
| … with model shortfall > 0 | 204 | 40 | 4 |
| … of those, measured-cap-binding (= sidecar `ordc_adder` ≠ 0) | 42 | 2 | 1 |
| family dual > $1 (headroom- or cap-bound) | 52 | 11 | 0 |
| sidecar `ordc_adder` > $1 | 3 | 0 | 0 |
| model `held_mw` mean | 8,122 | 6,955 | 6,638 |
| credited requirement mean | 8,306 | 7,085 | 6,647 |
| credits mean (LR + storage awards) | 2,394 (878+1,516) | 3,615 (876+2,739) | 4,053 (714+3,339) |
| marginal level `held+credits` mean | 10,517 | 10,570 | 10,691 |
| published RTOLCAP mean | 8,108 | 8,854 | 9,654 |
| marginal level − RTOLCAP mean | **+2,408** | **+1,715** | **+1,037** |
| published RTORPA h>$1 / h>$100 (settled) | 294 / 17 | 78 / 4 | 14 / 0 |

**Term: demand-curve placement — NOT the 2024/2025 zero's driver.** At the
model's own marginal levels the armed flat curve (μ=0/σ=1,400, shift 0.5)
and the published NP6-576-ER table collapsed to the annual-mean scalars the
LP builder would actually use (μ 924/σ 1,348, shift 0 → span 10,664 vs
10,700) price **the same hours**: 11 vs 11 h>$1 in 2024, 52 vs 50 in 2023, 0
vs 0 in 2025 (A4). Two real placement wedges are measured and named, both
subordinate to the basis terms: (a) the LP evaluates **both** half-hour LOLP
terms at ONE total level, where the published form prices the half-hour term
at RTOLCAP (online) and keys the floor to it — the published two-basis form on
the same telemetry yields 48 vs the single-level 45 h>$1 (2024); (b) the
`spec.py` annual-mean collapse (`mu_s = float(np.mean(mu))`) makes any
seasonal table nearly inert **in-LP** — the B0 table-vs-fallback differences
live in the per-hour post-solve form only, so arming the table in the LP as
built would change almost nothing (consistent with B0's year-keyed verdict,
which this session does not touch).

**Term: floor date-gating — non-explanatory for the 2024/2025 zero.** The
undated in-LP OBDRR048 floor is active in both fired windows anyway; the
model's marginal level reaches the floor region (≤ 7,000) in only 6 (2024) / 0
(2025) fired hours vs published RTOLCAP ≤ 7,000 in 26 / 0 — the basis terms,
not the floor's gating, keep the floor silent. Converse 2023 exposure
(measured, carried): the LP floor exists Jan–Oct-2023 where the real floor did
not (effective 2023-11-01); the model's level enters ≤ 7,000 in **16** pre-Nov
hours, all inside genuine scarcity (dual > $1 in 52 pre-Nov hours, published
fired 1,555 pre-Nov). Small, real, named — an over-pricing risk in 2023's
favor, inherited from the armed construction, not introduced here.

## 2. THE CROSSWALK (dispatch: built FIRST, "reconciliation or show it cannot be one")

It cannot be a component reconciliation, for a measured reason on each side:

* **`held_mw` is not a capability series.** It is the LP's cleared reserve,
  demand-limited at the credited requirement (held = requirement in 96 % of
  2024's fired hours) and supply-capped at raw RTOLCAP/RTOLCAP+RTOFFCAP. Its
  level says what the LP was ASKED to hold, not what the fleet COULD hold.
* **RTOLCAP is not a procurement series.** It is telemetered on-line
  capability of everything synchronized — thermal headroom + online ESRs +
  Load Resources — with no demand-side cap.
* The honest common basis is `B_model = held + lr + sas` vs RTOLCAP (both
  "total online reserve counting load-side and storage MW"). On it: B_model
  is pinned at min(10,700, ·) (p50 = 10,700 in every year's fired hours),
  sits above RTOLCAP (table §1), and is uncorrelated with it (r ≤ 0.18). The
  residual components that keep even B_model from a like-for-like identity
  are named: the model credits AWARDS (cleared AS) where RTOLCAP carries
  CAPABILITY (online ESR headroom ≥ awards; enrolled LR ≥ cleared LR), and
  the model's held tops out at the curve span where RTOLCAP is uncapped.

## 3. THE PRE-REGISTERED VIABILITY RULE: **PASS** — Phase-1 is entered

Against `PRECOMMIT-ercot212-reserve-basis-phase0` §4, candidate class C-A
(basis consistency of the armed family, zero fitted scalars):

* **V1 PASS** — the candidate uses only the already-armed measured series
  (RTOLCAP/RTOFFCAP caps; LR + storage-AS credits) and the armed curve. No
  scalar is chosen anywhere.
* **V2 PASS** — it repairs the armed family's arithmetic; no second channel.
* **V3 PASS** — nothing R/I/G re-armed: no published-RTORPA overlay, no
  envelope, no capability cap, no LOLP-table arming (the table appears above
  as a comparison curve only), no conduct, no E1.
* **V4 PASS** — out-of-LP implied 2024 incidence on the armed flat curve:
  **minimal form 45 h>$1, full two-basis form 48**, vs the settled published
  78 → 0.58×/0.62×, inside the pre-registered [0.25×, 4×].
* **V5 PASS** — implied 2023 deep tail h>$100: **minimal form 37, two-basis
  form 20**, vs settled published 17 → 2.18×/1.18×, inside [0.25×, 4×].

**The candidate, named: `ercot_reserve_supply_cap_net_credits`** — net the
armed LR + storage-AS credit series off the measured reserve-supply caps
(`cap' = max(cap − lr − sas, 0)`, both tiers), exactly when the corresponding
requirement credit is armed, scoped to the measured-cap (backcast) branch.
The same MW must not be credited on the demand side and simultaneously ride
the supply cap whose telemetry already contains it — a consistency repair of
the armed construction (rule 19: one mechanism; rules 13/20/23: zero new
scalars, no new series). With it, the marginal level at cap contact becomes
`RTOLCAP+RTOFFCAP` (the telemetry basis) instead of `cap + credits`, and cap
contact expands from 42/2/1 hours toward the real dip set (upper bound
571/190/67 hours with cap_all < 10,700; implied ≥$1 incidence 175/45/5 vs
published 294/78/14). The **full published two-basis form** (half-hour term
priced at the online tier, floor keyed to it; implied 48 h>$1 in 2024) is
measured, viable, and **NOT built here** — it is a larger family-splitting
construction, named for the owner as the next increment beyond the single
delta. The forward branch is untouched: the WS-A forward cap composes storage
explicitly and carries no LR term, so the double-count is specific to the
measured branch; the forward composition's own basis audit is a forecast-lane
item, named not opened.

Phase-1 (the armed A/B) proceeds under its own pushed precommit:
`docs/PRECOMMIT-ercot212-netcredits-phase1-2026-08-16.md`. Any 2023 movement
is side-effect-reported at full magnitude under Q-B/R-A phrasing, never a
basis (X-3). §5 of this finding records the Phase-1 outcome.

## 4. WHAT THIS CORRECTS IN THE STANDING RECORD (stated, not silently)

* ercot-204 §A.3's "the model holds materially LESS reserve than the real
  system and still does not price" — the held-vs-RTOLCAP comparison it itself
  caveated as non-identity — **inverts at the margin** (§0, §2). The
  falsification it powered ("the simplest explanation is falsified") stands
  for a different reason: the model's system is indeed not comfortable in the
  40 shortfall hours; it is silent because of the basis terms above.
* ercot-198 §0 / ercot-204 §A.2's "endogenous `ordc_adder` ≈ 0 (2 non-zero
  hours in 2024)" is the additive column only. The reserve-scarcity content
  of 2024's deepest hours (up to $760/h) is in the scored `price` via the
  co-opt; the missing content vs published RTORPA is the broad-shallow
  region, sized by ercot-198 at +0.237 $/MWh dw (2024). No re-scoring is
  performed and no criterion moves in this Phase (read-only).

## 5. PHASE-1 RECORD — **REJECTED-AS-ARMED** (G-SPUR kill + a diagnosed structural mis-anchoring); the IDENTIFICATION IS VALIDATED and the successor is named

**A/B executed under `PRECOMMIT-ercot212-netcredits-phase1-2026-08-16.md`
including its Amendment 1** (the keeper is not byte-reproducible at HEAD —
upstream drift, measured on both environments; G-REPRO re-based to
control-vs-armed BEFORE the armed solve). Both members solved full-span
2023+2024+2025 sequentially at the same tree (main `00abb60fd` + the ercot-212
commits, since merged as PR #4016) on the keeper's true solve environment
(highspy 1.15.1 / pandas 3.0.5 / pyarrow 25.0.1). Registered
**`2026-08-16-ercot212-ctl-headbase`** / **`2026-08-16-ercot212-arm-netcredits`**,
then PRUNED in the same session per the dispatch roster duty (adjudication
rejected-wholesale; this finding + the matrix cell + the log entry are the
durable record). Probes: `results/calibration/ercot212_ab.json`,
`ercot212_coal148.json`.

**The HEAD drift is score-inert** (control vs keeper): price dw Δ ≤ ±0.07
$/MWh, tails 58/22/1 → 57*/22/1 identical on the scorer, shed 4/1/0
identical hour lists, `ordc_adder` incidence 42/2/1 identical with identical
maxima; the official scorer reproduces the keeper's determination on the
control exactly (C3a-2023 −33.2 %, C3b-2023 0.604, C3c 58/22/1). (*57 on the
probe's dw basis, 58 on the scorer's max-zonal basis — the standing two-basis
note.)

**Gate table (control → armed), against §3 as amended:**

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| G-SHED (no increase) | 4 → **0** (h5490/5682/5802/5994 all clear) | 1 → 1 (h3067) | 0 → 0 | **PASS** (reductions reported) |
| G-C3c (not away from actual) | 57 → **123** (181) | 22 → **33** (53) | 1 → **3** (31) | **PASS** — toward actual in every year |
| **G-SPUR** (≤ +5) | 9 → **16 (+7)** | 11 → 13 (+2) | 0 → 0 | **KILL** |
| G-SPAN (≤ 2.0 %) | max 0.077 % (CT_PEAKER) | 0.0 % | 0.0 % | PASS |
| G-COAL148 (rise ≤ 0.5 TWh) | 0.0 | 0.0 | 0.0 | PASS |
| G-OWNER | — | C3a-2024 PASS, C3b-2024 PASS | C3a-2025 PASS | PASS |
| G-DOF | zero fitted scalars; boolean only | | | PASS |
| G-D2 | no new D-4 row | | | PASS |

**Verdict under the pre-registered direction-blind rule (§6): one kill ⇒
REJECTED-AS-ARMED.** The verdict is mechanical and stands unrewritten.

**Side-effect report at full magnitude (Q-B/R-A phrasing — reported, never a
basis, never spent):** on the official scorer the armed member reads
**C3a-2023 +13.3 %** (from −33.2 % — the magnitude falls 20 pp and the sign
flips to OVER), **C3b-2023 NRMSE 0.299** (from 0.604 — halved, bar 0.20),
**C3c-2023 123/181 and C3c-2024 33/53 now PASS their bands** (the keeper
carries both as ledgered caveats at 58/181, 22/53); C3c-2025 still fails
(3/31). DA diagnostics on the armed member: 2023 −2.2 % vs DA, 2024 +0.1 %,
2025 −9.6 %. Armed determination NOT-YET, fail set {C3a-2023, C3b-2023,
C3c-2025} (+ C6 unattested on both A/B members — no attestation generated
for a pruned pair).

**The identification is VALIDATED and the failure is DIAGNOSED, both from the
committed record:**

* Incidence landed almost exactly on the §2 predictions: `ordc_adder` ≥ $1 in
  **184/38/7** hours (predicted 175/45/5); nonzero in 564/178/67 (upper bound
  571/190/67); every price-tail count moved toward actual in every year; the
  2023 shed vanished as predicted (freed reserve serves load).
* The LEVEL overshoots for a structural reason the arm itself exposes: in the
  cap-additive regime the writer adds the **VOLL-anchored** curve price (the
  co-optimization-correct form, whose λ is supposed to cancel through the
  shared-headroom internalization) **without the λ subtraction the published
  additive formula carries** (`adder = (VOLL − λ) × LOLP`), and it sums **both
  headroom tiers'** cap duals — the armed maximum adder is **$10,000/h = 2 ×
  VOLL**, a price the published design's own protocol cap (λ + adders ≤ VOLL,
  enforced by the post-solve `ordc_adder()` via `min(adder, VOLL − λ)` and by
  ERCOT's settlement) **cannot produce**. With the gross caps this regime was
  nearly unreachable (42/2/1 hours); the netting makes it dominant, so the
  mis-anchoring converts a correct incidence repair into a 2023 level
  overshoot (+13.3 %) and the G-SPUR mid-band spill.

**Promotion: DECLINED — this is NOT a recommended keeper candidate**, and the
owner's standing structural standard ("structural integrity outranks gate
regression") is judged NOT to apply: the arm is structurally RIGHT about the
basis (validated above) and structurally WRONG about the additive-regime
price formula (super-VOLL prices violate the market design being modeled —
rule 1). Promoting would enshrine the wrong half to keep the right half.

**THE NAMED SUCCESSOR (zero fitted scalars, needs its own precommit — the
next ERCOT lever):** keep the credit netting, and make the cap-additive
regime price on the published formula: (a) anchor the additive component at
**(VOLL − λ)** (or equivalently route it through the post-solve
`ordc_adder()` construction on the LP's realized netted reserve state, which
already carries the protocol cap and the floor's date gate); (b) **single
counterpart, not a two-tier sum** — the ORDC total family's uninternalized
component alone; (c) the published **two-basis form** (half-hour term at the
online tier, floor keyed to online) as the second increment. Expected
landing zone from this session's out-of-LP construction: 2023 tail ~20–37
h > $100 (vs 17 published settled), 2024 45–48 h > $1 (vs 78) — between the
control's silence and the arm's overshoot.

**Roster:** both members registered (rule 15) and pruned in-session
(`scripts/prune_iso_runs.py --iso ERCOT`) per the dispatch roster duty;
keeper `2026-08-15-ercot204-rule26-delete` unchanged and protected
throughout.

## 6. GOVERNANCE

Q-B FINAL and R-A cited, never re-litigated: no C3a/C3b/C3c value was computed
in Phase-0 — every number above is a committed-artifact or telemetry read.
2023 appears as measurement context and in the pre-registered V5 band only.
ercot-206 B0 honoured: the NP6-576-ER table entered as a comparison curve
only, never armed; no blanket-table candidate was considered (V3). ercot-211 /
Door A honoured: no conduct object touched. V0/ercot-201 DO-NOT-REDO
honoured: no tightness-conditioned identification, no E1 term; RTOLCAP
entered as read telemetry (FFR-8B §4 evaluation role) against the ALREADY
armed supply-cap construction. Rule 22: {2023, 2024, 2025} only, no marker
sought. Rule 25: ERCOT only. Rule 27: files edited locally, exact bytes
pushed, ≥300-line pushed files blob-verified. Rule 28: the 28a sweep is cited
in §3 V3 (cells checked: `ordc_scarcity_overlay` R, `ercot_rtordpa_overlay`
K, `energy_reserve_coopt` K, `ercot_multiproduct_as` K,
`online_capacity_envelope` R, `energy_online_capability_cap` R,
`measured_ramp_capability` I, `dynamic_reserve_requirements` U,
`reserve_family_dual_sidecar`/`reserve_family_sidecar` I,
`storage_measured_anchors` K); the 28b/28c matrix duties land with Phase-1.
Environment: the container's `uv.lock` resolves highspy 1.14.0 / pandas 3.0.3
/ pyarrow 24.0.0 — **byte-equal to the keeper `run_config.json`'s recorded
versions**, so the dispatch's pin instruction is satisfied by verification
(recorded; no pin action was needed). No PR (push-and-stop; the owner
merges).
