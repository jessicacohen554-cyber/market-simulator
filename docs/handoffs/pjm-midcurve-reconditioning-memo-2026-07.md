# OWNER MEMO — re-conditioning the PJM measured offer surfaces from within-year to within-season tightness (pjm-127b, 2026-07-26)

**Decision requested:** authorize (or decline) re-deriving the PJM measured
offer surfaces with a **within-season** net-load-percentile conditioning in
place of the current **within-year** conditioning. Rule 20 gates this: derive
scripts are frozen against residuals, and a re-derivation commit must cite a
data or conditioning-**definition** change. This memo is the definitional case
that gate consumes. **No re-derive has been performed.** The keeper
(`2026-07-25-pjm-121-cc-belt`, CALIBRATED 10/10) is untouched.

**Evidence base:** pjm-126 (2025, fidelity-exact to 8.5e-13) plus its
pjm-127a multi-year confirmation on 2023/2024 — the within-year
conditioning's tightest-bin inversion is a **conditioning artifact**: the
annual top-3% net-load bin is structurally a summer-only sample (87% summer
in 2025), winter's expensive offers are deposited into the middle bins, and
under within-season ranking the inversion reverses sign in the two segments
that carry it (2025: CT_FAST +10.00 → −0.85, CC_LIKE +0.35 → −0.20). The
three-year gap table lives in the pjm-127 finding. Findings:
`docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md`,
`docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`.

> **Status at first commit (pre-registration).** This memo is committed while
> the pjm-127a 2023/2024 probes are still running, so that §3 (the season
> definition) and §4 (the A/B expectations and refutation signature) are in
> git BEFORE any multi-year result is seen — the lane's standing
> pre-registration discipline. **The memo is conditional:** if either 2023 or
> 2024 contradicts the 2025 ARTIFACT verdict, the charter stops this lane at
> the finding and this memo is withdrawn, not acted on. A follow-up commit
> will replace this banner with the measured three-year confirmation (or the
> withdrawal). Nothing in §1–§6 changes in response to the probe numbers —
> that is the point of committing it now.

---

## 1. The definitional case — why within-season is the better definition of tightness state

The case below is argued from market structure only. No backcast residual, no
gate, no score enters it; the residual-facing consequences are quarantined in
the pre-registration section (§4), which is written *ahead* of any re-derived
surface precisely so they cannot leak backward into this section.

The surfaces' conditioning variable is meant to measure **tightness state** —
the scarcity state a unit's offer desk perceives when it prices the curve.
The within-year construction measures something else: distance from the
*annual* (i.e. summer) peak. Four structural facts about PJM say
season-relative rank is the better definition of the state the offers respond
to:

1. **PJM's own market design treats the year as two seasonal operating
   environments.** Capacity accreditation and ratings are seasonal (summer vs
   winter capability ratings and the seasonal capacity constructs of Manual
   18/RPM), the summer peak-load season (the 5CP window, Jun–Sep) and the
   winter season (Dec–Mar) carry their own emergency procedures (hot- vs
   cold-weather alerts), and both seasons carry Capacity Performance
   obligations. A unit's "how tight is the system" assessment is made against
   the seasonal envelope it is operating in — its own seasonal rating, the
   season's outage plan, the season's fuel arrangements — not against a
   January-vs-July comparison no operator makes.

2. **Winter and summer scarcity are different products, and PJM prices both.**
   PJM's severe scarcity events are bi-seasonal — Winter Storm Elliott
   (Dec 2022) and the Jan 2024/Jan 2025 cold snaps sit beside the summer
   heat events. But because PJM is summer-peaking in *absolute* net load, an
   annual percentile can never classify a winter emergency as tight: measured
   2025 composition puts only 34 winter hours in the annual top-3% bin
   against 229 summer hours, while the middle bins are winter-enriched
   (477/249). A tightness conditioner that structurally excludes one of the
   two scarcity seasons from its tight state is not measuring tightness; it
   is measuring summer-ness.

3. **The offer-relevant drivers of scarcity are season-specific, so rank must
   be taken within the season for the bins to hold the driver fixed.** Winter
   is when CT offers are dearest (oil parity, gas-basis blowouts, cold-snap
   commodity spikes); shoulder months are when planned outages thin the
   available fleet, so modest absolute net load can still be operationally
   tight (the maintenance-season risk PJM and NERC seasonal assessments flag
   explicitly). The within-year rank conflates two variables — season and
   tightness — in a single index. A conditioning variable should measure one
   thing; ranking within season removes the seasonal composition confound by
   construction (each bin's seasonal mix becomes uniform), leaving the bins
   measuring what they are named for.

4. **The within-year bins are not even measuring "summer scarcity" cleanly.**
   Because bin membership is annual, the middle bins mix winter peaks with
   summer shoulders-of-peak, and the tight bin's apparent cheapness imports
   summer's cheap gas ($4.03 bin3 vs $4.53 bin1 mean delivered, 2025) — the
   gas normalisation removes the price level but not the population
   difference. The measured surface as currently conditioned answers "how do
   offers look at each rank of *annual* net load", which is not a question
   any mechanism in the model wants answered.

**The honest counter-argument, stated.** Within-year rank does capture one
real thing season-relative rank does not: *absolute* scarcity. The marginal
opportunity cost that sets the very top of the price distribution lives
disproportionately in the summer peak, and a within-season bin3 dilutes that
sample with shoulder-season "tight" hours (top-3%-of-April is rarely scarce
in any absolute sense). We judge this cost real but second-order for these
surfaces: their job is mid-curve and top-of-curve *offer conditioning*, not
peak-event identification, and the shoulder tight hours it admits are
precisely the thin-margin maintenance-season hours whose offers do carry a
scarcity state (point 3). The alternative conditioners that would capture
absolute scarcity directly (net load against *available* capacity, i.e. a
reserve-margin conditioner) are named in §6 and rejected on forward-native
and identification grounds, not on results.

This case stands or falls as written above. If the owner judges it
insufficient *as a definition*, the re-derive is inadmissible regardless of
anything a re-conditioned surface might do downstream — that is rule 20
working as intended.

## 2. Scope — the decision covers BOTH frozen surfaces, explicitly

The mid-curve surface (`pjm_offer_midcurve_condbinned.json`,
`derive_pjm_offer_midcurve.py`) deliberately shares its bin edges
`[0.80, 0.90, 0.97]` and its tightness driver with the frozen pjm-99
top-of-curve surface (`pjm_offer_surface_condbinned.json`,
`derive_pjm_offer_surface.py`) — "the SAME edges … so the two mechanisms
share one tightness state definition" (the derive's own docstring).
Re-conditioning one and not the other silently breaks that invariant: two
committed PJM surfaces would carry contradictory definitions of the same
state, and a future session arming the currently-dormant top-of-curve
mechanism (`pjm_offer_surface_conditional`, **off in the keeper**) would
stack a within-year surface on top of a within-season one.

**Proposed scope: the tightness-state definition changes for the PJM
measured-offer-surface family as a unit.** Concretely, one definitional
vintage, one commit:

* **Both derives** re-run with within-season ranking (same edges, same
  shares, same segmentation, same gas normalisation — *only* the ranking
  scope changes), each JSON's provenance block gaining
  `conditioning: "within-season"` and the `season_of_month` map.
* **Both consumption seams** change coherently in the same commit. Solve-time
  binning today takes within-year quantiles of the LP-served net load
  (`_pjm_midcurve_context`: `np.quantile(net_load, edges)`;
  the top-of-curve path's `_netload_regime_mask` equivalent) — under the new
  definition each hour's bin comes from its own season's quantile
  thresholds. A **vintage guard** (the existing edges-mismatch-guard
  precedent, `offer_surfaces.py`) hard-fails any solve that pairs a
  within-season JSON with within-year binning code or vice versa, so a
  half-updated state cannot silently mismeasure.
* **All three mid-curve consumers** inherit the seam change automatically —
  the keeper's floor mechanism
  (`build_pjm_offer_midcurve_conditional_markup`), the default-off level
  form, and the default-off CT_FAST max()-seam reprice
  (`build_pjm_ct_measured_max_target`) all read
  `_pjm_midcurve_context`; the top-of-curve mechanism is the fourth
  consumer via its own loader.
* **No other ISO is touched.** ERCOT/NEISO/CAISO surfaces keep their own
  conditioning; whether the same artifact exists there is those ISOs'
  question, on their own evidence (rule 25 — and the segregation mechanism is
  ISO-specific: it follows from PJM's seasonal peak structure).
* The superseded within-year JSONs are retained under a `-withinyear-2026-07`
  suffix as the measurement record of the prior vintage (they are cited by
  pjm-99/104/108/121/123/126 findings); the live filenames carry the new
  vintage. Nothing is deleted (the findings stay reproducible), and nothing
  deprecated remains loadable by a live config default (rule 24 — the loaders
  point at the live filenames only).

The alternative scopes are rejected: *mid-curve only* breaks the shared
definition (above); *re-condition mid-curve and retire the top-of-curve
surface* deletes a measurement record no evidence impeaches — pjm-99's
finding (the top-of-curve surface is inert in PJM because the mid-curve caps
the dual) is about curve position, not conditioning, and survives either
vintage.

## 3. The season definition, fixed in advance

Exactly the definition pjm-126 pre-registered and committed before any result
was seen (`pjm126_midcurve_conditioning_precheck.SEASON_OF_MONTH`, commit
`9409f7f`):

| season | months |
|---|---|
| summer | Jun, Jul, Aug, Sep |
| winter | Dec, Jan, Feb, Mar |
| shoulder | Apr, May, Oct, Nov |

This memo proposes **no change** to those boundaries. They are PJM's own
operating convention — the summer peak-load season is the Jun–Sep 5CP window,
the winter season Dec–Mar — and the split is symmetric (4/4/4 months), so no
season's bins are structurally thinner than another's. Ranking is within
(year, season): a season that spans the calendar boundary (Dec with the
following Jan–Mar) is still ranked within the delivery year the hours fall
in, matching how the per-year surface tables are keyed. Any future proposal
to move these boundaries is a new definitional change and needs its own
memo *before* any result under the new boundaries is seen.

## 4. Pre-registered A/B expectation and the refutation signature — written before the re-derived surface exists

If authorized, the sequence is staged so the cheap gates come first, and every
criterion below is committed before the re-derive runs.

**Stage 1 — re-derive + no-LP pre-check (no solve).** Re-derive both surfaces
within-season. Then re-run the pjm-123 composite pre-check machinery and the
pjm-121 spread diagnostic against the NEW surface on the keeper fleet
(reconstructed via `scripts/lib/bundle_fleet.py`), pre-registered:

* **Expected ladder movement** (from pjm-126/127 arm B, so these are
  predictions about the derive output, checkable before any solve): armed-
  segment bin3 ladders RISE relative to the within-year vintage (CC_LIKE body
  ≈ +0.4–0.5 × gas in 2025), bins 1–2 FALL modestly (winter inflation
  removed, ≈ −0.1 × gas); LONG_RUN approximately unchanged (its inversion was
  ~1%). CT_FAST bin3 rises sharply (≈ +10 × gas) but CT_FAST is **not armed**
  in the keeper's floor scope (rule 19 — owned by the pjm-103 startup
  amortization).
* **Stage-1 kill (K1-gradient, the pjm-123 criterion):** the new surface's
  MW-weighted bid delta on the keeper fleet must be **larger in the tightest
  bin than in the slackest** (gradient bin3−bin0 > 0) for the armed floor
  scope, in at least 2 of 3 years. A surface whose re-conditioning still
  moves the slack bins as much as the tight bin is not a dispersion lever,
  and **no solve is spent**.
* **Stage-1 honesty bound:** the expected armed-segment effect is *modest*
  (the big CT_FAST flip lands on a segment the keeper deliberately does not
  floor). If the pre-check shows the armed tight-bin floor rising by less
  than ~$1/MWh MW-weighted, the expected solve-level effect is within noise —
  report that to the owner before spending the chain rather than after.

**Stage 2 — the A/B solve chain (only if Stage 1 survives).** Keeper recipe
vs keeper recipe + re-conditioned surface (+ the coherent seam change), via
`replay_keeper.py results/calibration/pjm121_ccbelt`, all of 2023 2024 2025,
years sequential (rules 12/16), full determination scoring, registered on the
dashboard win or lose (rule 14).

* **PASS signature (adopt):** the 2025 C3a gain, if any, is carried by the
  **tight strata** — on the pjm-120 stratum decomposition (baseline 2025:
  0–25 +2.015, 25–50 +2.249, 50–100 −3.662, 100–200 −2.487, 200–376 −1.126,
  >376 −1.534 $/MWh), the combined ≥$50 strata contribution must improve by
  more than the combined <$50 strata contribution moves (the same gradient
  logic, now on prices), AND model hourly price dispersion widens toward
  actual (p90−p10 up, weekly CV up), AND C1 stays 16/16 gated rows all years
  (the pjm-108 failure mode — CC displacement — is the known risk of raising
  the CC floor), AND every other closed gate stays closed, AND the verdict
  flip (if any) survives leave-one-year-out within 2023–2025 (rule 22).
* **REFUTATION signature (closes the lever for good):** the effect is a
  **level shift either way** — the stratified delta is near-uniform across
  strata (price-gradient ≤ 0), or C3a moves while the tight-strata gap does
  not close, or C1 breaks. That is pjm-121 §5 / pjm-123 K1 restated on the
  season-conditioned surface: the measured-offer-surface family will then
  have been tried as a dispersion lever under BOTH conditioning definitions,
  and the family closes on record — Lane 2 ends, and with Lane 1 already
  complete the frontier ledger is again whole.
* **Either outcome is registered** (keeper candidate or rejected probe, same
  session, rule 14). Promotion, as always, is flagged and owner-made
  (`keepers.json` is owner-only).

**What may NOT happen under this authorization:** no edge re-tuning, no
share-grid change, no segmentation change, no new free parameter — the
re-derive changes the ranking scope and nothing else. Any of those is a
different change needing its own case.

## 5. The bin-population consequence, and forward regeneration (rule 13)

Within-season ranking rebalances the tight bin from a summer-only sample to a
balanced one by construction — 2025: bin3 goes from 229 summer / 34 winter /
0 shoulder to 88/88/88. Three consequences, stated:

1. **The tight-bin ladder becomes a three-regime mixture** (a cap-weighted
   median over winter, summer and shoulder tight hours). It is no longer "the
   summer peak sample" — that is the intended semantics, and it also makes
   the ladder more stable across years (no single summer's weather dominates
   a 263-hour bin).
2. **Forward regeneration is exactly as forward-native as today** — the
   rule-13 admissibility test passes identically. At solve time the
   conditioner is built from the forecast year's own simulated net load
   (`np.quantile` per season instead of per year; the month→season map is
   calendar, fixed), no measured data enters, and the same quantity would be
   produced for a forward year from forward drivers and respond to changed
   conditions. The per-year tables stay keyed by delivery year with the
   pooled fallback for forward years, unchanged in structure.
3. **Forecast-side expression changes, by design.** With seasonal
   thresholds the tight state fires in every season of a forecast year
   (~3% of each season's hours), so the surfaces' tight-bin pricing will
   express in winter and shoulder forecast hours where the within-year
   construction confined it almost entirely to summer. A forecast's winter
   price formation therefore sees the measured tight-state offer level for
   the first time. This is the definitional change doing its work — flagged
   so the owner authorizes it knowingly.

## 6. Alternatives considered and set aside (definitionally, not on results)

* **Reserve-margin conditioning** (net load against *available* capacity):
  closer to true tightness, but it makes the conditioner depend on the outage
  state — at derive time that imports a measured overlay into a forecast-
  methodology input's definition, and at solve time the availability series
  is partly endogenous. A cleaner candidate in principle, materially harder
  to keep rule-13-clean; not proposed.
* **Within-month ranking (12-way):** no market-structure basis (nothing in
  PJM's design operates monthly) and it thins the tight bin to ~22 hours per
  month-year, destabilizing the medians. Rejected.
* **Absolute-MW thresholds:** not forward-native (a fixed GW threshold does
  not regenerate as load grows). Rejected.

## 7. What this memo does not do

It performs no re-derive, arms nothing, and changes no committed file's
meaning. The multi-year confirmation it rests on (pjm-127a) is a diagnostic
JSON, not a surface. If the owner declines, the within-year surfaces stand,
pjm-123's closure of the family stands *as narrowed by pjm-126* (i.e. the
lane remains open but untriable under rule 20), and that state — a named
admissible mechanism blocked on an owner decision — is itself a legitimate
ledger entry for the frontier question, though not a completion of it.

## Pointers

* The artifact evidence: `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md`,
  `docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`.
* The lane and its ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §3.
* The frozen derives: `scripts/data/derive_pjm_offer_midcurve.py`,
  `scripts/data/derive_pjm_offer_surface.py`.
* The consumption seams: `src/market_sim/data/fleet/offer_surfaces.py`
  (`_pjm_midcurve_context`, `build_pjm_offer_midcurve_conditional_markup`,
  `build_pjm_ct_measured_max_target`, and the top-of-curve conditional path).
* The dispersion caveat this aims at: `docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md` §2/§4.
* Rule 20's text and genealogy: `CLAUDE.md` rule 21 `[R-FROZEN-DERIVE]`;
  `docs/governance/rule-history.md`.
