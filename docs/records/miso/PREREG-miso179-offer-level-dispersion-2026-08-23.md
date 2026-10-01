# PREREG miso-179 — the ACROSS-UNIT offer-level dispersion object: no-LP pre-checks with kills, then a gated A/B — every threshold fixed BEFORE any hour-set-conditioned quantity is computed

**Session miso-179, 2026-08-23.** Keeper `2026-08-22-miso-177-rho-measured`
(bundle `results/calibration/miso177_rho_B`; NOT-YET on C3a-2025 alone
(−11.747 %; 2023 +1.279 / 2024 −4.064; band ±10 % ⇒ +1.75 pp needed), C3b
PASS, C3c the single ledgered caveat, C6 PASS, C8 PASS all years — 2025
ST_GAS grounded-above-budget at 32.3 % with profile r 0.982, ZERO D-4
conduct failures).

**Charter (owner grant, in the session prompt, 2026-08-23).** FINDING-miso178
§10 **D-1 is GRANTED**: the across-unit dispersion object is CHARTERED, the
conduct-distribution admissibility FORM is approved in kind (measured ex-ante
offer declarations entering as a rank-mapped markup DISTRIBUTION — the
ercot-223 armed-conduct precedent; award columns are outcome-class and are
never read), and the ~430 MB JJA 2023–2025 `miso-energy-offers` refetch is
authorized. **D-2 (the 5(i) seam-response envelope ruling) and D-3 (the South
under-export evidence charter) stay OPEN — neither is built here.**

**Order of operations, auditable in the commit history** (the miso-176/177
discipline): corpus refetch + manifest sha256 verification (552/552 OK,
429.6 MB) + curation (`data/clean/energy-offers/MISO/{DA,RT}/`, outcome
columns dropped and asserted absent) → **THIS DOCUMENT, committed and
pushed** → the identification derive (§3) → the pre-check probe (§4) → IF
AND ONLY IF every pre-check clears: the gated implementation (§2, OFF-path
proven inert before any solve) → control solve → arm solve → gates (§5) →
verdict mapping (§6). No hour-set-conditioned statistic exists before this
document's commit; the only measured numbers cited below are COMMITTED prior
artifacts (miso-151 G-5, miso-178 anatomy).

---

## 1. The object (committed evidence only; nothing new measured yet)

MISO's real offer book is nearly flat WITHIN each unit ($3.76/MWh
cap-weighted median top-of-own-curve rise; the within-unit family is CLOSED —
`measured_offer_surface` R, miso-151) but disperses ACROSS units by
**$47.84/MWh p90−p10** (base-level quantiles p10/p50/p90/p95/p99 =
0.17/19.58/48.01/91.44/298.03, Jul-2025 DA book, cap-weighted — miso-151
G-5). The model compresses that across-unit spread into class-tranche band
multipliers (`_MISO_OFFER_CURVE`, mostly 1.0 for MISO), which is exactly: a
4.06×-too-flat 2025 summer stack, marginal-unit identity Δ₁ = +10.50 $/MWh
(197 % of the 2025 gap), 5.3 GW of real gas idle in the 88-hour tail while
imports over-serve by 2.1 GW, and a body that over-prices the trough
(+1.45 pp remainder even in 2025). The deterministic-reachable space is
−13.71 pp (model vs MISO's own DA surface); the need is +1.75 pp. Reach
ceilings (computed, miso-178 §4): tail@actual-RT → −2.13 %; model@DA →
+1.96 %. The one move the measurement forbids is a uniform level lift (2023's
body is +5.34 pp over; miso-145 measured the book $8–15/MWh CHEAPER than the
model at matched own-curve position — LEVEL transfer moves C3a the wrong
way). The admissible action is rank-preserving DISPERSION: leave the low
stack, raise the high-rank offers.

**Falsifiable structural prediction, stated before any build (rule 1):** the
2025 zonal miss is a DIPOLE (Midwest −4.3…−15.2 % under vs MISO-South
+17.0 % OVER; South over-priced +18.8/+21.0 % in 2023/24 too). If the Midwest
stack steepens to measurement, southward export pressure falls, the RDT N→S
premium unwinds, and **MISO-South's over-price falls toward zero with no
South-specific mechanism**. A dispersion arm that closes C3a-2025 while
leaving the South dipole intact has NOT captured the real object.

## 2. The mechanism (proposed form, frozen)

One new gated `ScenarioConfig` field, **`miso_offer_level_dispersion: bool =
False`** (registered, cache-key drop-at-default per the nyiso-119 discipline;
armed key hashes distinctly; run_config-recorded; rule 24). Armed, at fleet
build time, for **MISO only** (rule 25):

- **Scope.** The **econ_low / econ_high / peak tranches of the offer-curve
  classes** (CC_*, CT_*, ST_GAS*, COAL_* — the classes priced by
  `_MISO_OFFER_CURVE` band multipliers). The committed and `_mustrun`/`_sync`
  bands are UNTOUCHED (they are the model's analogue of the book's
  self-scheduled/must-run mass, which the identification population excludes
  — the correspondence is population-consistent by construction). Nuclear,
  hydro, renewables, storage, import tranches: untouched. Tranche MW
  structure (shares, pct_peaking): untouched — the mechanism REPRICES, never
  resizes. The P1 startup-amortization markup stays armed as-is on top: the
  measured levels are ENERGY offers, and MISO clears startup/no-load as
  separate offer components (ELMP fast-start pricing), which the P1 markup
  proxies — no double count, one mechanism per phenomenon (rule 19).
- **Graft rule.** Within each calendar month, rank the affected tranches by
  their base marginal cost (capacity-weighted rank r ∈ (0,1], weights =
  pmax, stable sort). Each tranche's energy offer becomes
  `Q(r) × G_ref(month)`, where Q is the measured markup quantile function
  (§3) and G_ref the delivered-gas monthly reference (§3). Q is monotone, so
  the graft is **rank-preserving inside the affected stack** — no
  merit-order inversion vs the base construction; order against unaffected
  units may change (physical). Values are applied as-is, negative offers
  included; the LP's existing maxgen slack ceiling ($500/$1,000 in declared
  windows) is EXPECTED to cap what the grafted tail can clear at — that is
  the market's own cap, reported in the A/B, not touched.
- **Parameters.** The measured quantile vector + identification metadata,
  from the committed derive artifact (§3). **Zero fitted scalars, zero
  LMP/residual anywhere in the identification path.** The DOF ledger gains
  one MEASURED entry; `n_residual` UNCHANGED at 2. Re-derives only on corpus
  update, and such a commit cites the data change (rule 23). Hard-error if
  the artifact is absent while armed.

## 3. Identification (frozen before the derive runs)

Derive `scripts/data/derive_miso_offer_level_dispersion.py` →
`data/raw/_validation-source/miso_offer_level_dispersion.json` (the
miso-151/ercot-223 artifact pattern).

- **Corpus:** `data/clean/energy-offers/MISO/DA/energy-offers_{2023,2024,
  2025}.parquet` — the JJA DA book, curated this session from the
  manifest-verified refetch (552/552 sha256 OK). DA, not RT: the DA market is
  the deterministic existence proof the reach argument rests on (miso-178
  §3); RT is reported nowhere in the identification.
- **Population (BOOK-ELIG, the price-setting-eligible mass):** unit-hours
  with `unit_available_flag AND economic_flag AND NOT must_run_flag`, weight
  `max(0, ecomax_mw − self_scheduled_mw)`. Emergency-limited mass excludes
  itself (a unit-hour with ecomax ≤ 0 carries zero weight). Rationale: a
  self-scheduled or must-run unit's energy is price-taking — its offer level
  can never set the LMP — so the conduct distribution the model consumes is
  identified on the mass that CAN.
- **Base offer level:** the unit-hour's step-1 price
  (`step_idx == 1`, `step_price_usd_per_mwh`) — the cleared-agnostic
  declaration at the unit's own operating point, exactly G-5's object. The
  within-unit rise above step 1 is NOT transferred (closed family).
- **Normalization (markup-over-reference):** `m = base_level /
  G_ref(month)`, where **G_ref = Henry Hub monthly + the measured MISO hub
  basis row** — the `measured_gas_monthly` construction of the
  pre-registered miso-156 instrument (PRIMARY basis; committed inputs
  `data/raw/gas-prices/henry_hub_monthly.csv` +
  `data/raw/gas_basis_by_iso_month.csv`). m is an implied-offer-heat-rate in
  MMBtu/MWh: it regenerates for a forward year from a forward gas trajectory
  and responds to changed conditions (rule 13 admissibility test).
  Disclosed mis-specification, accepted with the granted FORM: non-gas
  units' offers do not truly scale with gas, so ratio-pooling across years
  mixes them; the error is second-order for the mechanism's target (the top
  of the stack is gas-priced) and the A/B adjudicates. Application uses the
  SAME G_ref construction (using a different reference at apply time than at
  identification would smuggle in a level adder).
- **Pooling:** all three JJA years pooled into ONE vector (never per-year —
  the same-year-outcome-pin shape PREREG-miso146 §9 forbids as methodology;
  the ercot-223 stationary-conduct pattern). Per-year sub-vectors are
  computed and REPORTED as a stationarity check, never consumed.
- **The vector:** capacity-weighted quantiles of m on the frozen grid
  **p = 0.5 %, 1.0 %, …, 99.5 % (199 points)**, applied by monotone
  interpolation in rank. The artifact records: the grid, Q, per-year
  sub-vectors, population masks and counts, weight totals, the G_ref values
  consumed, the corpus manifest's sha256 inventory, and the curation row
  counts — so the derive is reproducible byte-for-byte from the raw mirror.
- **Timezone:** the corpus is fixed EST (UTC−5) year-round;
  `interval_start_local` maps directly onto the model's hour index
  (h = hours since Jan-1 00:00 local standard). No DST logic anywhere.

## 4. The no-LP pre-checks — kills fixed NOW, before any of them is computed

Probe `scripts/probes/_miso179_dispersion_precheck.py` →
`results/calibration/_miso179_dispersion_precheck.json`. Model side: the
`_miso156.model_year` path via the `_miso178_c3a_decomposition.py` wrapper
pattern (bundle repointed to `miso177_rho_B`, import shim included), with its
own V1/V4 validity gates required to PASS before anything else is read (V1:
reproduce C3a +1.2813/−4.0643/−11.7421 % to ±0.5 pp; V4: n_gen
2929/2923/2923, carry zones 6). All three pre-checks are computed and
reported IN FULL even if an earlier one fires; adjudication happens after
measurement, in the frozen order a → b → c.

**Frozen common constructions.**

- **H\* (the hour set):** the **221** JJA-2025 hours with the highest
  six-carry-zone total demand (the keeper's own committed
  `system_2025.parquet`, P1 rows) — the top decile of the 2,208 JJA hours.
- **Model offer basis:** `mc_base[g, t]` — the base marginal cost the
  committed-instrument lineage (miso-156/161/178) defines as the model's
  offer surface. DISCLOSED UNDERSTATEMENT: the P1 startup-amortization
  markup (not reconstructable without a P0 solve) adds dispersion on
  committed-unit econ/peak rows, so the model side is a LOWER bound; since
  K-PRE-a kills when the model's dispersion is LARGE, the bias runs toward
  PROCEEDING, and the A/B — not the pre-check — is the adjudicator that
  sees the true P1 surface. The magnitude is reported qualitatively from
  the keeper's markup telemetry if present; never estimated numerically.
- **Model affected stack:** econ/peak tranches of the offer-curve classes
  (§2 scope), availability-masked (`availcap[g,h] > 0`), weights
  `availcap[g,h]`.
- **Model clearing price** `P_mod(h)`: the committed P1 demand-weighted
  six-carry-zone price at h. The congested-hour share (cross-zone spread >
  $1/MWh, the miso-156 T-21 statistic) is reported beside every pooled
  number as the copper-plate caveat.
- **Book populations on H\***: BOOK-ALL = available unit-hours, weight
  `max(0, ecomax_mw)`; BOOK-ELIG = §3's identification population. DA book,
  mapped to model hours by `interval_start_local`.
- **Quantiles:** capacity-weighted, pooled over unit-hours (model:
  tranche-hours) in H\*; spread **S = p90 − p10**. p50/p90/p95/p99 all
  reported both sides.

**K-PRE-a — is the object already in the model?** S_mod (model affected
stack) vs S_book (BOOK-ELIG). **KILL: S_mod ≥ 0.5 × S_book.** (If the model
already carries at least half the measured across-unit dispersion at the
margin, the object is smaller than Δ₁ claims and the mechanism cannot move
what the anatomy attributes — STOP, no LP.) Reported alongside, never
adjudicating: BOOK-ALL quantiles; the model's across-PLANT base-level cut
(per `plant_code`: min affected-tranche mc with headroom, weight = plant
availcap) — the exact G-5 grain; per-hour median spreads.

**K-PRE-b — does the dispersion live ABOVE the margin, in price-setting
hands?** Two legs, both frozen:

- (b-1) Pooled over H\*: of the BOOK-ALL mass with base level >
  `P_mod(h)`, the share that is price-setting-eligible (the BOOK-ELIG
  definition applied to those unit-hours). **KILL: share < 1/3.** (The
  dispersed mass the model's margin is missing is predominantly
  self-scheduled / must-run / emergency-limited — dispersion without
  price-setting power.)
- (b-2) **KILL: S_book(BOOK-ELIG) < 0.5 × S_book(BOOK-ALL)** on H\*. (The
  eligibility mask itself strips the across-unit spread — the object is
  mostly non-price-setting conduct, and the vector §3 would identify is not
  the wall miso-151 measured.)

Also reported (not gated): the share of BOOK-ELIG mass above `P_mod(h)` —
how much eligible book mass the model's clearing point sits below.

**K-PRE-c — the against-interest year, predicted before any solve.** 2023 is
+1.279 % (in-band) and its Jun+Jul Δ₁ runs the OTHER way (−6.5 $/MWh: the
model's summer marginal unit is already too EXPENSIVE there) — the graft's
upside risk is 2023 exiting the band's TOP. Static repricing predictor, no
re-dispatch: for every 2023 hour, r\*(t) = the capacity-weighted rank of
`P_mod(t)` in the model's month-t affected stack (share of available
affected mass with offer ≤ P_mod(t) + $0.01); predicted price
`P′(t) = Q(r\*(t)) × G_ref(month)`; predicted C3a-2023 =
Σ_t w_t·P′(t) / Σ_t w_t / bench_rt_lw − 1, w_t = carry demand. This
predictor has NO substitution channel, so it OVERSTATES movement in both
directions — a pass is strong evidence, a fire is precautionary. **KILL:
predicted C3a-2023 outside ±10 %.** The same predictor for 2024 and 2025 is
computed and REPORTED (the ex-ante magnitude record the A/B is read
against), not gated — the LP gates 2024/2025 itself (§5).

**A fired kill ends the session with NO LP:** the pre-check FINDING is
written, the matrix cell `miso_offer_level_dispersion` (new row) is minted
**R** (K-PRE-a / K-PRE-b: identification refuted — the object is absent or
not price-setting) or the FINDING records the c-fire as
**REFUSED-BY-PREREG** with the cell minted R citing the against-interest
bound, the §5.4 stamp + calibration-log entries land in-session, and the
lane falls back to the OPEN owner decision points D-2/D-3/D-4 — which stay
the owner's, nothing built.

## 5. The A/B (only if every pre-check clears)

Implementation lands first, gated OFF by default, with the OFF path proven
inert BEFORE any solve: default cache key unmoved, armed key distinct, the
five non-ERCOT-ISO seam proof pattern of ercot-188 applied to MISO's
neighbours (every other ISO byte-identical with the flag armed), unit tests
on the graft (monotonicity, MW conservation, scope exclusion, artifact-hash
consumption).

Control and arm are `replay_keeper.py` replays of the committed keeper at
HEAD, run SEQUENTIALLY and ALONE (rule 12; the miso-151 OOM disclosure),
each the FULL span 2023 2024 2025 in ONE invocation (rule 16), under the
miso-169 15 GB recipe (pinned stack `highspy==1.14.0 pandas==3.0.3
pyarrow==24.0.0 numpy==2.4.6 scipy==1.17.1` + openpyxl, matching the
bundle's recorded environment; `MARKET_SIM_HIGHS_THREADS=4`; 8 GB swapfile;
abandon-before-solve if available RAM < 13 GB or the artifact sha256
mismatches the derive record):

```
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso179_disp_A \
  --note "miso-179 CONTROL: byte-faithful keeper replay at HEAD (miso_offer_level_dispersion at default off)"
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso179_disp_B \
  --set miso_offer_level_dispersion=true \
  --note "miso-179 ARM: measured across-unit offer-level dispersion, rank-mapped markup distribution (single delta)"
```

Registration ids `2026-08-23-miso-179-control` /
`2026-08-23-miso-179-dispersion` — **BOTH registered whatever the outcome**
(rule 15), full 3-year bundles with hourly sidecars incl. `reserve_family`
(rule 16 / rule 15 KEEPER sidecar clause).

Gates, fixed now:

* **G-0 CONTROL BIT-IDENTITY (ABANDON).** All 12 scored sidecars
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical (numeric max|diff| = 0, identical row sets) to the
  committed keeper's. Anything else ⇒ HEAD drift or a non-inert default —
  STOP, report, no arm conclusion.
* **G-1 ARM VALIDITY (KILL).** The arm's `run_config.json` records the flag
  true and the control's false/absent; the consumed artifact sha256 equals
  the derive's committed digest; the graft telemetry records the affected
  tranche count > 0 in every year.
* **G-2 C3a-2025 DIRECTION.** Δ = arm − control C3a-2025 in pp.
  **Δ ≤ −0.25 pp ⇒ KILL** (regression). |Δ| < 0.25 ⇒ the mechanism is
  measured INERT here (verdict `I`, §6). Δ ≥ +0.25 ⇒ the improvement leg is
  satisfied.
* **G-3 AGAINST-INTEREST BAND (KILL).** C3a-2023 AND C3a-2024 each inside
  ±10 % on the arm.
* **G-4 C3b (KILL).** The C3b price-duration/shape criterion PASSES all
  three years on the arm (scorer's own gate).
* **G-5 CONDUCT (KILL).** C8 PASS in all three years on the arm (grounded
  form allowed), AND zero NEW D-4 conduct failures vs the regenerated
  control's `legitimacy_diagnostics.json`.
* **G-6 DOF (KILL).** The arm bundle's ledger: `n_residual` unchanged (2);
  the new entry's identification is `measured` with zero fitted scalars.
* **G-7 RECORD FLIPS (KILL).** Zero PASS → non-PASS flips across the
  verdict scorer's records, arm vs the committed keeper (the miso-177 R-5
  form).

Reported in full, gated by nothing: **the South-dipole prediction** — the
miso-178 zonal stage re-run on BOTH bundles (per-zone demand-weighted
own-error, all three years); the ex-ante expectation from §1 is that
MISO-South's 2025 own-error (+17.0 % at control) moves TOWARD ZERO;
**the Δ-channel re-run** (miso-156 instrument on the arm: Δ₁ should collapse
toward 0; Δ₂ must not grow materially more negative — identity fixed, not a
level stacked); **the miso-178 bucket decomposition** on the arm (tail /
top-decile / remainder pp); the maxgen slack-ceiling encounter count (hours
where the arm's price reaches the $500/$1,000 ceiling — expected, not
touched); K-PRE-c's static prediction vs the LP's realized move (the
predictor's own audit); load-weighted price deltas annual / JJA /
DA-foreseen vs RT-only; C3c tail-hour counts both arms at full magnitude.

## 6. Verdict mapping and the promotion decision rule, fixed now

* **Any §4 kill fires** → NO LP; §4's closure path (FINDING, cell `R`,
  stamp, fallback to D-2/D-3/D-4).
* **G-0 fires** → ABANDONED-AT-CONTROL; escalate the drift; no arm
  conclusion; nothing registered as arm evidence.
* **Any of G-1/G-3/G-4/G-5/G-6/G-7 fires, or G-2 kills** → arm
  **REJECTED-AS-ARMED** with the firing gate named; both runs registered;
  cell `R` with evidence; keeper unchanged.
* **All kills silent + G-2 inert** → verdict **`I`**; both registered;
  keeper unchanged; the FINDING records why a measured $47.84 spread grafted
  at the margin failed to move the annual statistic (that itself is a
  structural datum).
* **All kills silent + G-2 improvement + the South-dipole moves toward
  zero** (|South 2025 own-error| strictly smaller on the arm) → **the arm is
  the KEEPER-CANDIDATE and MAY BE PROMOTED THIS SESSION on this prereg's own
  rule** (zero regression + target improvement + the structural prediction
  confirmed): keeper shard edit + `calibration-keeper-auditor` run + matrix
  re-stamp + calibration-log, all in-session. MISO holds no
  `calibration-complete` marker, so no re-key is owed (rule 22 D-5(b)
  vacuous here).
* **MIXED — kills silent, C3a-2025 improves, but the South dipole is intact
  or worse** (or any structurally conflicted reading) → **ESCALATE to the
  owner with both records, no self-promotion.** The owner's standing
  structural standard applies and is quoted verbatim: *"If structural
  integrity improves but gates regress that may still be a keeper."* The
  session presents the C3a movement AND the failed structural prediction
  side by side; per §1, an arm that closes the number without unwinding the
  dipole has not captured the real object, and claiming it would be the
  rule-1 second-half violation.
* **An outcome none of these anticipate** is recorded as an unanticipated
  branch (the miso-151 BRANCH-GATE-BREACH-INVERSE precedent) — reported,
  never retrofitted into a listed branch.

## 7. Governance

* **Rule 22 [R-HOLDOUT]:** 2023/2024/2025 ONLY, one invocation per run; MISO
  holds neither marker; the holdout spend freeze is untouched. The corpus
  span is training-years-only (the fetcher's own gate enforced it).
  Leave-one-year-out within 2023–2025 applies AT PROMOTION per rule 22's
  mechanism-change clause: the identification consumes no target-year
  outcome (zero LMP in the path) and the vector is pooled-measured with
  zero fitted parameters, so LOO is vacuous by the miso-172/173/175/177
  precedent (a selector plus a committed pooled measurement) — recorded,
  not re-derived per-year.
* **Rule 13 [R-MEASURED]:** offer columns are ex-ante declarations
  (admissible in kind, granted); award columns were dropped at curation and
  asserted absent; the identification path contains NO LMP and NO residual;
  the vector regenerates for a forward year from a forward gas trajectory
  and each future year's published book (90-day lag).
* **Rules 23/24/25/26:** frozen derive (re-derives only on corpus change);
  the field + artifact are registry-visible and run_config-recorded; no
  env-var knobs; MISO-only gating (verdicts never transfer); nothing
  deleted — at flag-off the band-multiplier path is byte-identical.
* **Rule 26(b)/(c) matrix duties:** the new mechanism's ROW +
  a cell line in EVERY ISO shard land in the same PR as the ScenarioConfig
  field; the MISO cell verdict + §5.4 stamp + calibration-log land
  in-session whatever the outcome.
* **Rule 12 [R-PARALLEL]:** MISO plant-level solves run ALONE, years
  sequential within each invocation.
* **Rule 27 [R-PUSH]:** small commits, exact on-disk bytes, blob
  verification after any push touching a ≥300-line file; run payloads over
  `git push`; HTTP/1.1 fallback on 408/500 before any pack-size conclusion.
* No new `.github/workflows`. The owner merges; no PR unless asked.
