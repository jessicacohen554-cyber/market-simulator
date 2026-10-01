# PRE-REGISTRATION — caiso-153: re-identify the CAISO offer surface's gas-coupling classifier

Committed and pushed **before any classifier value on this session's corpus
exists**. House rule; caiso-139/146/147/148/151/152 precedent.

Lever: **mechanism-matrix §5.2 item 9** — NEW at caiso-152, BLOCKING, unowned.
It is a prerequisite, not a price lever.
Instrument: `scripts/probes/_caiso153_offer_classifier_reid.py`
(`curate` / `diagnose` / `derive`).
Keeper at entry: `2026-07-31-caiso-151-firm-selfsched`, CALIBRATED-WITH-CAVEATS,
0 FAILs, C1 12/12 · free 8/8, 2 of 3 non-protective ledger slots spent,
protective 0/1. CAISO holds **no** rule-22 calibration-complete marker
(re-verified this session): solve years are **2023 2024 2025 only**, and **no
marker is written**.

---

## §1 — the problem, as caiso-152 left it

`caiso_offer_curve_measured.json` and `caiso_offer_surface_condbinned.json` are
a LIVE keeper input. caiso-152 fixed the `dam-public-bids` RLE parse defect —
the parser carried only 47.9 % of real GENERATOR EN curve-hours and charged
18.0 % of them to the wrong net-load bin — and measured the correction's effect
as **MATERIAL and CT_PEAKER-only** (`econ_high` 1.055 → 0.912; ladder bin means
+0.311/+0.277/+0.276/+0.304 against a ~0.146 tolerance).

The correction **cannot ship**, for a reason that is not the parse:

* the derive fails its **own G1** on BOTH arms — CT bucket ratio 0.235 (old
  parse) / 0.280 (new) against a `[0.50, 1.60]` bound — and correctly withholds
  the consumed JSONs;
* the OLD arm **is** the committed code path on the deriver's own default
  corpus, and does not reproduce the committed artifact: **25 CT units vs 102**,
  CT bucket 1,786 MW vs 10,785, CC `econ_low` 1.544 vs 1.051, G1 FAILING where
  the artifact records it PASSING at 1.416.

Gas is byte-identical inside 2023–25 and fleet geometry round-trips exactly.
The artifact is **not reproducible as a matter of record**.

## §2 — the hypothesis under test

The classifier reads a per-resource regression **slope** of the daily body bid
on the daily citygate price as that resource's marginal heat rate, then gates
on `slope ∈ [4, 18]`, `r ≥ 0.6`, `≥ 120 resource-days` and splits classes at
`hr_cut = 8.5`.

**H1 — the slope distribution is systematically ATTENUATED**, i.e. the
estimated slope is biased toward zero relative to the true marginal heat rate.
Two independent observations point the same way:

* caiso-152's lead: 71 resources / 16,329 MW clear `r ≥ 0.6` yet land at
  **slope < 4 MMBtu/MWh**. High correlation with an impossibly low slope is the
  signature of attenuation, not of a non-gas resource.
* the population moves as attenuation predicts: 102 CC / 25 CT against the
  committed 55 CC / 102 CT. CT-heat-rate units sliding below the 8.5 cut into
  CC, and the tail sliding out of the `[4, 18]` gate, is one shift of one
  distribution — not two unrelated defects.

Two mechanisms could produce H1 and are tested **together**, because either
alone suffices and the caiso-152 lead names only the first:

* **A — the body-price probe.** `_price_at_frac` reads a SINGLE step at 35 % of
  a p98-estimated capacity. If that step is the min-load / self-commitment
  block rather than the SRMC body, the sampled price tracks gas only partially.
* **B — the estimator.** The regressor's variance is dominated by an extreme
  tail: the CA-composite citygate reaches **$24.29/MMBtu** in January 2023
  against a 2023–25 median near $3–4. A pooled OLS slope is therefore levered
  on a few days of one month of one year, and any resource that did not track
  that spike proportionally — a different CA hub, a monthly index, a
  cost-verified default energy bid on a lagged index — is attenuated with its
  correlation intact.

Registered ex ante: **a partial refutation of A is not a refutation of H1.** A
throwaway raw-CSV measurement made before this pre-registration (12 trade days,
no classifier, no multiplier) found the probe falls back to the first step on
only 8.5 % of curve-hours, with those curves near-flat. That is evidence
against the *Pmin-fallback* form of A and is reported as such; it says nothing
about B, and B is why the grid below has two axes.

## §3 — corpus (frozen)

The **full contiguous 2023–2025 span** — 1,095 trade days, what
`scripts/data/fetch_caiso_public_bids.py` produces with no arguments, with the
documented 2023-06-01 OASIS archive hole. This is `FINDING-caiso152` §D's
measured corpus requirement: this derive is a per-resource daily regression and
a seasonally balanced sample starves it (both parse arms fail G1 there for
reasons unrelated to the parse). **The caiso-151 balanced sample is not used.**

Parser: the corrected (HEAD, post-caiso-152) RLE-expanding parser, on every
arm. This session runs **no old-parse arm** — the parse question is settled.

## §4 — the estimator grid (frozen ex ante)

3 body probes × 3 slope estimators. The incumbent is `P035_OLS`.

| axis | id | definition |
|---|---|---|
| body | `P035` | price of the step at 0.35 × cap (incumbent `BODY_FRAC`) |
| body | `BAND` | capacity-weighted mean step price over [0.35, 0.85] × cap — the INTEGRATED body, insensitive to where any single breakpoint sits |
| body | `P060` | price of the step at 0.60 × cap — mid dispatchable range, above a typical CC min-load block |
| slope | `OLS` | least squares on every gas day (incumbent) |
| slope | `TS` | Theil–Sen median of pairwise slopes — resistant to extreme regressor days and to outlying bid days |
| slope | `TRIM` | OLS restricted to days at or below the resource's own p95 gas price |

Everything else in the derive is **untouched**: the gas staircase and its
trade+1 flow-day placement, `MIN_CAP_MW = 20`, `GAS_SLOPE_RANGE = [4, 18]`,
`GAS_MIN_R = 0.6`, `GAS_MIN_DAYS = 120`, the storage exclusion `min_mw ≥ −1`,
the band windows, the ladder construction, the carbon basis, and
**`hr_cut = 8.5`**. The probe swaps how a marginal heat rate is MEASURED, not
what is done with it.

## §5 — selection rule (frozen ex ante; blind to G1 and to the committed artifact)

Neither criterion may read a derive gate or a committed multiplier. That is the
point: a rule that could see G1 would be a gate fit, and a rule that could see
the committed values would be the answer key `FINDING-caiso152` §H forbids
chasing.

**5.1 Admissibility, applied FIRST — the physical level identity.** A cost-based
gas bid satisfies `body ≈ HR × gas + VOM + CO2_FACTOR × HR × P_carbon`, so the
implied non-fuel adder

    L = median over the resource's days of [ body − slope × (gas + 0.057 × P_carbon) ]

must sit near VOM ($2.0 CC / $3.5 CT). An estimator is **ADMISSIBLE** iff its
capacity-weighted median `|L|` over gas-gate-passing resources is **≤ $20/MWh**.
Rationale for the bar, fixed before any value: VOM is $2.0–3.5; $20 leaves a 5×
margin for start amortization and conduct adders, while still excluding the
~$50 non-fuel adder that an attenuated slope must invent to reproduce the
observed bid level.

**5.2 Ranking — out-of-sample slope stability.** Each resource's gas days are
split by **alternating gas rank** (sort by gas price; even index → half A, odd
→ half B) so both halves span the same regressor range and the test measures
the estimator rather than the split. Metric: capacity-weighted median
`|slope_A − slope_B|` in MMBtu/MWh, over resources passing the gas gate with a
finite slope in both halves. **Lowest wins.**

5.1 precedes 5.2 deliberately: an estimator that shrank every slope toward zero
would win 5.2 outright, and 5.1 is what makes that impossible.

**5.3 Reported, never a selection input:** classified bucket capacities, the
count/MW below the `slope < 4` gate, and slope quantiles. These are printed by
`diagnose` and prefixed `_context_` in its JSON.

## §6 — outcomes and REJECT conditions

Exactly three, decided in this order.

**(a) NOT RE-IDENTIFIED — no estimator is admissible under §5.1.** FILE AND
STOP. No solve, no registration, no artifact written, keeper unchanged. This is
a **first-class result**, and the one this pre-registration expects to be
reportable as such: it would mean an armed keeper input is permanently
unreproducible, so the surface needs retirement or replacement — an **owner
decision**, not a lever. Matrix cell updated regardless.

**(b) RE-IDENTIFIED but the frozen derive gates still FAIL.** The winning
estimator is run through the unmodified deriver; if any of G1–G4 fails, the
consumed JSONs are correctly withheld and **the lane stops at the derive**. No
solve. The finding reports the winning estimator, its gate results, and what
still does not reconcile. **No gate is relaxed, re-centred or re-scoped**
(rule 23 `[R-FROZEN-DERIVE]`; `FINDING-caiso152` §H).

**(c) RE-IDENTIFIED and all four gates PASS on their own.** Only then is an
artifact written and an LP A/B run — see §7.

**REJECT conditions, binding on every branch:**

1. No threshold in G1–G4 moves. No change to `hr_cut`, `GAS_SLOPE_RANGE`,
   `GAS_MIN_R`, `GAS_MIN_DAYS` or `MIN_CAP_MW`.
2. No hand-edited JSON, no OLD/NEW blend, no CC-only cherry-pick, no arming the
   ladder off a summary CSV (`FINDING-caiso152` §H, PREREG-caiso152 §6(e)).
3. No estimator is preferred because it moves a bucket toward the committed
   values, and no band level is re-derived against a price residual. The
   committed CT numbers are not a target.
4. If the corrected input makes the backcast WORSE, that is a **discovered
   bug**, not a reason to revert (rule 1 `[R-STRUCT]`, rule 14
   `[R-ACCURATE]`). The input stays; the root cause is opened.
5. Any mid-session change to a registered input (corpus, grid member,
   threshold, population) is registered in a **dated addendum before any value
   under it exists** (the caiso-152 precedent).

## §7 — the A/B, if and only if branch (c)

Two arms, same HEAD, solved **sequentially** because the delta is FILE CONTENT
at `data/raw/_validation-source/` and the static half has no path-override
field (only the ladder has `caiso_offer_surface_binned_path`):

* **control A** — `scripts/replay_keeper.py results/calibration/caiso151_clip_B`
  with the committed artifacts in place: a same-HEAD **zero-delta control**.
  The committed keeper bytes are **not** the control (caiso-152 §"the committed
  artifact is NOT the control").
* **arm B** — identical, with the re-derived artifacts swapped in.

Both files are **hashed per arm**. `legitimacy_diagnostics.json` is generated
for BOTH arms (`replay_keeper.py` does not emit it, and C7/C8 score SKIPPED
without it). Arms are compared **UNATTESTED, criterion by criterion**; a
control with no `calibration_attestation.json` correctly reads NOT-YET /
2 FAILs / UNATTESTED, which is a repo-wide convention, not a regression.

**Direction expected:** the CT_PEAKER ladder rises ~+19–21 % relative to the
committed surface under the parse correction alone; the re-identification's own
direction is **not predicted and none is registered**. No sign is claimed for λ.

**Protective checks (any failure ⇒ the arm is not promotable):**
* no new FAIL on any C1–C8 criterion relative to control A;
* C7 diurnal-shape gates hold for the **absorbing gated classes** —
  `CC_REGULAR` and `CT_PEAKER` (the levered classes), plus `ST_GAS` / `COAL`;
* C8 forced-share: `CT_PEAKER` stays under the 0.15 peaker cap;
* Nuclear, `CC_CHP`, `CT_CHP`, `ST_CHP` are exempt from **both** C7 and C8 by
  explicit class list — no exempt class's D-1/D-2 number is quoted as a passed
  gate;
* `ST_GAS` 2024/2025 raw D-1 rows read FAIL on **both** arms and have since
  before caiso-148 — pre-existing, below the 2 % materiality floor, **not**
  attributable to this lever.

**C3a materiality trigger:** if arm B moves the C3a-2025 statistic by more than
the criterion's own reporting tolerance in EITHER direction, it is reported
explicitly against the caiso-145 ledgered caveat. It is **not** grounds to
retune anything: C3a-2025 is DIAGNOSED-UNCLOSED with an empty in-model lever
queue (caiso-141 A2 data wall), and re-litigating it needs new evidence against
a named caiso-140/141/142/143/144 cell.

## §8 — deliverables

* Rule 15: if a solve happens, **both arms** are registered on the backcast
  dashboard (bundle slim files + registry sidecar + `runs/<id>.js` payload +
  changed `bench/`), pushed in this session. If no solve happens, **nothing is
  registered** (caiso-136/143/144/149/150/152 pattern).
* Rule 28b: the `measured_offer_surface` CAISO cell + evidence citation is
  updated in `docs/codebase-site/data/mechanism-matrix.js` **in this session**,
  including on outcome (a) or (b).
* `docs/calibration-log/caiso.md` gains a caiso-153 entry with its own
  DO-NOT-REDO section.
* A `FINDING-caiso153-*.md` is written on every branch.
* **No rule-22 calibration-complete marker is written for CAISO.**
