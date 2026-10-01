# FINDING — caiso-154: the caiso-153 OLS-attenuation defect is NOT LIVE in PJM or NEISO — the estimator family is structurally absent from both derives; the counterfactual transplant is refuted on PJM's corpus and confirmed data-real on NEISO's; all three committed artifacts REPRODUCE; one new NEISO tail-sensitivity exposure is filed

Lane: the `FINDING-caiso153` §H cross-ISO lead (NEW, unowned at caiso-153) —
adjudicated. **No LP was run; nothing is registered on any dashboard; no derive
was modified; no consumed artifact was rewritten; every keeper is unchanged**
(the caiso-136/143/144/149/150/152 no-solve pattern).

Pre-registration: `PREREG-caiso154-xiso-ols-attenuation-2026-08-02.md`,
committed and pushed **before any estimator value on this session's corpus
existed**. No addendum was needed: no registered input changed mid-session.

Instrument: `scripts/probes/_caiso154_ols_attenuation_xiso.py`
(`m2` / `m34` / `compare`), which **imports** the caiso-153 harness core
(`_fit`, `_score_resources`) and the CAISO derive's family constants —
parameterized by ISO, not forked. Outputs:
`results/calibration/caiso154_grid_{PJM,NEISO}.json`,
`caiso154_slopes_{PJM,NEISO}.csv`, `caiso154_m34_report.json`,
`caiso154_arms/` (six redirected shipped-derive arms). All committed EXCEPT
`caiso154_slopes_PJM.csv` (gitignored, session-local): its per-unit
intercepts/level-adders are bid-level-adjacent, and PJM DataMiner2 prohibits
non-member republication (`docs/data-licensing.md` §4) — the repo convention
is aggregates/multipliers only. It regenerates in ~15 min via
`m2 --iso PJM` once the corpus is fetched; the committed grid JSON carries
every aggregate the finding quotes.

**This was NOT a re-test of any adjudicated mechanism cell.**
`measured_offer_surface` PJM stays `R` (pjm-126/127/132 dispersion family;
pjm-141 D-BIN resolution bound) and NEISO stays `I` (neiso-58 dormancy) —
what was audited is the **input's standing** (the caiso-152/153 class), and
the cells' verdict letters are untouched. Rule 25: every measurement was made
on the target ISO's own corpus and own fuel series; nothing transferred.

Keepers at entry and exit: CAISO `2026-07-31-caiso153-reid-b`, PJM
`2026-07-31-pjm-143b-hy-level`, NEISO `2026-07-31-neiso-72-hy-window`.
Rule-22 state re-verified and **corrected against the handoff prompt**: PJM
and NEISO each hold a `complete` (validation-tier) marker (2026-07-31 /
2026-07-07); CAISO holds none; no ISO holds `final`; the **holdout spend
freeze is ACTIVE** and outranks everything. No marker written, no
out-of-training year touched, no solve at all.

---

## §A — the corpora, exactly as registered

* **PJM**: the full 36/36-month 2023–2025 DataMiner2 `energy_market_offers`
  corpus, refetched this session by the committed fetcher (~26 M unit-hour
  rows; the raw dir is gitignored and dies with the container). All 36
  parquets read-validated.
* **NEISO**: 1,058 published `hbdayaheadenergyoffer` days — **353/352/353 per
  year, exactly the committed artifact's recorded coverage**. The 38 absent
  days re-error on retry (the documented endpoint gateway-timeout gaps,
  neiso-58); all 9 critical tail-event days present. ~6.7 M offer rows,
  334 assets ≥ 20 MW, 82 physics-fast-start.
* No seasonally balanced subsample anywhere (caiso-152 §D). Fuel regressors
  are byte-committed model series: HH daily + PJM basis $0.67; Algonquin
  Citygate daily, forward-filled.
* Data facts established for the record: PJM `mw1..mw20` breakpoints are
  CUMULATIVE (0 monotonicity violations in 479 k multi-step rows); NEISO
  segment MWs are INCREMENTAL block sizes (per-row sum/EcoMax p50 = 1.000;
  monotone in only ~15 % of multi-segment rows), so the cumulative curve is
  their cumsum; ~9.7 % of NEISO rows carry blocks summing past 1.5× EcoMax
  (reported, not filtered).

## §B — L1 is FALSE: the estimator family does not exist in either derive

Disclosed in PREREG §2 before any corpus value existed, from code inspection:
the caiso-153 defect requires a **per-resource daily regression of a bid
statistic on the fuel series whose pooled-OLS slope is consumed** (as a
marginal heat rate, into an r-gated classifier with an `hr_cut` bucket split).
`derive_caiso_offer_surface.py::_classify` is the **only** offer-surface
derive containing any regression estimator (precise grep:
`polyfit|linregress|lstsq|theilslopes|siegelslopes`). The three PJM/NEISO
artifacts are built by per-unit **median-of-daily-ratio** ladders
(`(price / fuel_day) / base_HR`) with **physics** segmentation
(`min_runtime` / ecomin-ratio for PJM; `Claim30 ≥ 0.9 × EcoMax` for NEISO) —
no regression, no slope, no r gate anywhere in their consumed path. And
neither top-of-curve surface is armed in its keeper in any case
(`pjm_offer_surface_conditional = False`, `neiso_offer_surface_conditional =
False`); the one live artifact among the three is the PJM **midcurve** belt.

**FINDING-caiso153 §H's premise ("the PJM/NEISO derives use the same family")
is therefore IMPRECISE**: the shared element is the daily-fuel normalization,
not the estimator. **The defect is NOT LIVE in either ISO, categorically.**

## §C — M1: the tail-leverage precondition IS present, differently, in both

| series (2023–25 daily, as the derives consume it) | median | max | max/med | top-1%-days share of variance |
|---|---|---|---|---|
| CAISO CA-composite citygate (caiso-153, reference) | ~$3–4 | $24.29 | ~6–8× | (not recomputed) |
| PJM HH + basis | $3.31 | $13.87 | 4.2× | **53.0 %** (Jan-2024 storm + Jan-2025) |
| NEISO Algonquin | $2.19 | $28.36 | **13.0×** | 26.0 % (Feb-2023 arctic week) |

PJM's leverage is *concentration* (11 days carry half the regressor
variance); NEISO's is *magnitude*. So the counterfactual (§D) is a genuine
test, not a formality.

## §D — M2: the counterfactual transplant — REFUTED on PJM, DATA-REAL on NEISO

The full caiso-153 grid (body probes P035/BAND/P060 + TOP, × OLS/TS/TRIM),
family constants frozen (`≥ 120 days`, `r ≥ 0.6`, `slope ∈ [4,18]`,
`cap ≥ 20 MW`, `hr_cut = 8.5`, admissibility `|L| ≤ $20`), basis = gas only
(RGGI caveat as registered). Descriptive only; nothing was derived from it.

**PJM — the attenuation signature does NOT reproduce.**

* Every OLS cell on the caiso-153 body probes is **ADMISSIBLE**: |L| $6.34–7.76
  vs TS $13.7–14.3 (CAISO: OLS $32.7–37.5 INADMISSIBLE vs TS $10.1–12.7 —
  the ordering is **reversed**).
* Slope p50 moves < 0.75 MMBtu/MWh between OLS and TS on every body probe
  (9.14→8.81 at P035) — no slope collapse (CAISO: 6.07→10.03).
* The impossible population (`r ≥ 0.6`, slope < 4) does **not** deflate under
  TS (P035: 29 res/13.3 GW OLS → 34/14.5 TS; CAISO collapsed 32/10.9 GW →
  13/2.7 GW). It is a feature of the P035 statistic on this corpus, not an
  OLS artifact; at TOP it is negligible under every estimator (≤ 9 res /
  ≤ 2.2 GW).
* What OLS *does* cost in PJM is **precision**: split-half instability
  1.91–2.77 vs 0.22–0.45 (TS) — the 53 % variance concentration degrades
  stability without biasing the level.
* The classifier half fails **under every estimator**: cap-weighted confusion
  vs the shipped physics segmentation misbuckets 6.0–11.3 GW of CC_LIKE into
  the ≥ 8.5 bucket and 5.7–6.8 GW of LONG_RUN below it, OLS and TS alike. An
  hr-cut slope classifier is the wrong identification for PJM regardless of
  estimator — the physics segmentation the shipped derive uses is not merely
  adequate, it is load-bearing.

**NEISO — the caiso-153 signature IS present in the counterfactual, in
miniature, and robust estimation removes it — but every OLS body-probe cell
stays admissible.**

* OLS attenuates the slope: p50 7.42–8.07 (OLS) → 9.43–10.22 (TS) → 10.27–11.15
  (TRIM) — the CAISO direction, ~2–3 MMBtu/MWh.
* OLS roughly doubles the implied non-fuel adder: |L| $15.2–15.7 vs TRIM
  $4.4–7.8 — the CAISO direction — **yet stays under the $20 bar** (CAISO OLS
  was $32.7+). PREREG §5's branch fires exactly: tail present, OLS adder
  admissible ⇒ NOT LIVE.
* The impossible set empties under robust estimation on the integrated
  probes: BAND 5 res/1,436 MW (OLS) → 1/262 (TS) → 0 (TRIM); P060 likewise
  → 0.
* The misbucketing mechanism reproduces: at P035 the physics-fast-start
  630 MW splits 303 CC / 327 CT under OLS while **TS puts all 630 MW at
  ≥ 8.5**; at TOP the below-8.5 bucket swings 2,724 MW (OLS) → 411 MW (TS) —
  the caiso-153 CT-bucket collapse, counterfactually reproduced on NEISO's
  own data.
* Context, per the prereg's expectation: only 24–30 assets / 3.7–5.7 GW pass
  the gas gate at all — the fast-start fleet is heavily oil/dual-fuel and the
  r-gate correctly rejects it; a CAISO-style classifier would also have been
  starved here.

**TOP-of-curve is inadmissible under EVERY estimator in BOTH ISOs**
(|L| $23.8–36.4, vs OLS-at-TOP $14.5 in PJM): the curve top carries real
conduct/start adders. That is a measurement of why the CAISO family reads the
BODY — and why transplanting a level-identity admissibility bar to a
top-of-curve statistic would misfire. Reported per REJECT condition 3: no M2
cell is quotable as measured PJM/NEISO conduct in absolute terms.

## §E — M4: all three committed artifacts REPRODUCE — the caiso-152 defect class is CLEAR here

Shipped `main()`s, outputs redirected, fleet basis injected from each
artifact's own provenance (the recorded `pjm98_cc_mustrun` bundle and
`neiso_fleet_binned.parquet` cache are absent in this container — that leg is
BLOCKED as declared; what is tested is corpus + parser + estimator + ladder):

| artifact | armed? | result vs committed |
|---|---|---|
| PJM midcurve (the LIVE keeper input) | **YES** | **IDENTICAL — 1,152/1,152 numeric leaves, byte-equal values** |
| PJM top-of-curve | no | max rel Δ 0.016 % (the declared rounded-basis injection noise); 0 leaves > 2 % |
| NEISO top-of-curve | no | max rel Δ 0.023 %, at IDENTICAL day coverage (353/352/353); 0 leaves > 2 % |

Where caiso-152 found CAISO's committed artifact unreproducible from its own
script and corpus, **PJM's and NEISO's reproduce** — the armed PJM midcurve
exactly. The reproducibility defect class does not extend to these lanes.

## §F — M3: shipped-estimator tail sensitivity — PJM ROBUST; NEISO TRIPS the bar; a NEW exposure is FILED

Tail-exclusion arms (top ceil(1 %) of 2023–25 fuel days, ties included,
masked to NaN so they drop at the derives' own `fuel > 0` filter):

* **PJM tail set = 11 days ≥ $6.29** (Jan-2024 storm, Jan-2025). Both PJM
  artifacts move ≤ **4.8 %** (top: CC bin-0 body-clamp rungs 2.851 → 2.987;
  midcurve: max 4.65 % on LONG_RUN-2025 tight-bin shares). **ROBUST** under
  the pre-registered 10 % bar.
* **NEISO tail set = 34 days ≥ $25.00** — the ties-included rule swept a
  plateau: the Feb-2023 arctic week ($25.00–28.36, genuine daily prints)
  PLUS 2025-12-03..30, where the Algonquin series is a **weekly-Wednesday
  anchor series with one $25.00 print on 2025-12-03 forward-filled 28 days**
  (next print 2025-12-31; the real 2025-12-08 DA > $300 event sits inside the
  window). 3.1 % of days, faithfully measured against the exact series the
  derive divides by — which is also the series the model solves on.
* **NEISO result: 4 of 42 consumed leaves move > 10 % (max 13.1 %)** — the
  q0.7/q0.9 rungs of net-load bins 1–3 — and the movement is **UPWARD**
  (e.g. bin-2 rung-4 10.706 → 12.110). On $25+ gas days a fixed-dollar
  (oil-parity / capped) top-of-curve offer divides to a LOW gas multiplier,
  dragging the within-bin per-asset medians down; excluding those days raises
  the rungs 5–13 %.

**Verdict, exactly as pre-registered: TAIL-SENSITIVE — a NEW named exposure
for the NEISO lane, NOT "caiso-153 live", FILE AND STOP.** No estimator
change, no derive edit, no re-derivation. Standing facts that bound its
weight:

1. The artifact is **not armed in any keeper** (neiso-58 adjudicated the
   mechanism dormant; `neiso_offer_surface_conditional = False` everywhere) —
   the exposure moves no keeper, no solve, no dashboard number.
2. It is a **regime-mixing** exposure, the ratio-estimator analogue of
   attenuation: the tight-bin top rungs fold oil-parity/capped-offer days
   into a gas-normalized ladder, biasing the measured "fast-start wall" LOW
   by ~10 % — same direction as caiso-153 (measured conduct understated),
   different mechanics (division, not regression leverage).
3. Whether that is a defect or the intended signal is a **charter question**:
   the Feb-2023 days are exactly the winter-scarcity events the surface
   exists to represent (the derive hard-requires them present), and NEISO's
   frontier note already demands a NEW measured identification
   (oil-parity / import / DA-bid formation) before further C3c work. This
   measurement hands that charter a quantified entry point; it does not
   license bypassing it.
4. Half the excluded mass is a **fuel-series granularity** phenomenon (the
   weekly-anchor ffill plateau), which any successor should weigh before
   treating the 13 % as pure conduct signal.

## §G — disposition

* **PJM: NOT LIVE** — L1 false; counterfactual transplant REFUTED on the
  ISO's own corpus (no attenuation signature under any body probe); shipped
  estimator tail-ROBUST (≤ 4.8 %); both artifacts reproduce, the armed
  midcurve byte-identically. The PJM derives are untouched, per the charter's
  own branch: the defect is not live there, and the deriver does not change.
* **NEISO: NOT LIVE** (L1 false; OLS adder admissible under the family's own
  bar even with the 13× tail) — with the §F tail-sensitivity exposure FILED
  for the NEISO lane as its own unowned item, actionable only through a NEW
  charter (frontier discipline, neiso-72 keeper note).
* **The FINDING-caiso153 §H flag is ADJUDICATED** and its premise corrected
  on the record: "the PJM/NEISO derives use the same family" → they share the
  fuel-normalization, not the estimator; the failure mode transfers as a DATA
  fact to NEISO (and would have fired had NEISO been identified the CAISO
  way) and does not transfer to PJM even counterfactually.
* No solve, no registration, no marker, no threshold moved, no derive
  modified, no artifact rewritten. Matrix cells stay `KKRUUI`; evidence and
  notes updated for the P and Q columns in this session (rule 28b).

## §H — DO-NOT-REDO (new, binding)

* **Do NOT quote any M2 cell as measured PJM/NEISO offer conduct in absolute
  terms** — only the OLS-vs-robust contrasts, gate populations, and
  physics-vs-slope confusions are results (REJECT condition 3; extends
  caiso-153 §G's "no OLS absolute levels" discipline).
* **Do NOT re-run the counterfactual grid to "pick" an estimator for PJM or
  NEISO.** Nothing consumes a slope in either ISO; there is nothing to
  select. A future session that wants a slope-based identification in either
  ISO is proposing a NEW mechanism and owes its own charter, prereg, and
  frozen selection rule — and it inherits §D's measured warning that the
  hr-cut classifier misbuckets PJM under EVERY estimator.
* **Do NOT treat the NEISO §F exposure as a license to re-derive the NEISO
  surface with tail days excluded, a different normalization, or a different
  estimator** — that is the charter question, owner-visible, in NEISO's lane
  (frontier discipline). The 10 % bar was a detection threshold fixed ex
  ante, not a correction target; and the artifact is unarmed, so there is no
  keeper pressure.
* **Do NOT read §E's reproductions as a standing guarantee** — they certify
  the current committed artifacts against the current corpus endpoints. A
  refetch that changes coverage re-opens the question (the NEISO endpoint's
  gap set is live).
* **Do NOT re-litigate the PJM `R` or NEISO `I` mechanism verdicts on the
  strength of anything here** — this session measured input standing, not
  mechanism merit; pjm-141's D-BIN bound and rule 23 still bar re-binning,
  and neiso-58's dormancy stands.
* Carried forward unchanged: ALL of `FINDING-caiso153` §G (BODY_FRAC stays
  0.35; no CAISO re-derivation against the +0.05 MAE; hr_cut stays 8.5),
  `FINDING-caiso152` §H, `FINDING-caiso151` §H, `FINDING-caiso150` §H,
  `FINDING-caiso149` §G, `FINDING-caiso148` §G, `FINDING-caiso147` §G,
  `FINDING-caiso146` §G, `FINDING-caiso144` §G, caiso-143 §H/§I, caiso-142
  §K, caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10; the pjm-141
  D-BIN re-binning bar.

## §I — carried open items and cross-ISO notes

* **NEW (this session, unowned): the NEISO offer-surface tail-sensitivity
  exposure** (§F) — 4/42 consumed leaves levered > 10 % by 34 fuel-tail
  days; unarmed artifact; belongs to the NEISO oil-parity/DA-bid charter
  class named in its frontier note.
* **Observed, unowned, weigh before any NEISO fuel work: the Algonquin
  series' weekly-anchor granularity** — a single Wednesday print can govern
  up to 4 ffilled weeks (2025-12-03's $25.00 held 28 days). Both the derive
  and the solve consume the same series, so the model is internally
  consistent; but any statistic that treats the ffilled dailies as
  independent observations overweights anchor prints.
* The PJM/NEISO raw offer corpora are gitignored and die with the container.
  Refetch ≈ 65 min (PJM, 3 concurrent year-scoped fetchers; monthly-file
  skip-existing makes year-parallelism safe) / ≈ 3.5 h (NEISO, per-day
  files; run one fetcher per year — a shared-years invocation races the
  year-scoped ones on the same files). Budget for it; background fetchers do
  not survive session idle.
* Unchanged carried items: the caiso-151 §F diagnostics-harness plant-set
  defect (ISO-generic); the shared CT heat-rate sub-6.0 meter bug (four
  ISOs); the latent CHP derive defect in PJM (caiso-147 §B);
  `compute_monthly_markup`'s unconditional committed-tranche start
  amortization (six ISOs); the caiso-148 Diablo basis mismatch; CT_CHP's
  thin CAISO coverage; `audit_keepers.py`'s missing E7 staleness check; the
  two pre-existing CI test failures (clean-origin reproduced at caiso-152).

Next number: caiso-155.
