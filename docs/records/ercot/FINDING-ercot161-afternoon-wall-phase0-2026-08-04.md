# FINDING — ercot-161 Phase 0: the armed RT wall is exonerated on its own population; the ~100-hour price was formed on the STORAGE fleet, which has no offer instrument in the model

**Session ercot-161, 2026-08-04. NO LP, no solve, no mechanism armed, no
`ScenarioConfig` field added, keeper UNCHANGED (`2026-08-03-ercot158-pool-arm`).**
The FINDING-ercot-2023-summer-underrun-2026-08-04 §6 successor, Phase 0: *why
does the armed measured RT SCED offer wall
(`ercot_offer_surface_cleared_share` + `_rt`, `_rt_mode=replace`) not reproduce
ERCOT's own cleared SCED system lambda in the ~100 hours that carry 98.3 % of
the 2023 −30.5 % residual?* All four §6 candidate explanations are answered
below on committed artifacts + the ERCOT-157 delivery-2023 corpus. Probes (all
no-LP):

- `scripts/probes/ercot161_afternoon_wall_phase0.py` →
  `results/calibration/_ercot161_wall_phase0.json` (hour set verified to the
  cent against the FINDING; keeper fleet reconstructed via
  `reconstruct_bundle_fleet` with the prb-overrides channel asserted — 426
  conditional / 369 walled / 173 pool rows, the keeper's exact builder
  signature; wall-bin geometry; marginal-row attribution; stack census;
  rel-clamp census; gap-hour-conditioned corpus spare ladder).
- `scripts/probes/ercot161_dispatched_segment_census.py` →
  `_ercot161_dispatched_census.json` (the DISPATCHED (LSL→Base-Point] and full
  (LSL→HASL] SCED2 segment ladders at the gap hours vs the bin-6 rest).
- `scripts/probes/ercot161_price_setter_census.py` →
  `_ercot161_price_setter.json` (ALL resource types: whose dispatched segments
  sat in the λ-neighbourhood band [0.7, 1.3]×λ at the gap hours).
- `scripts/probes/ercot161_pwrstr_conduct_census.py` →
  `_ercot161_pwrstr_conduct.json` (the 2023 storage discharge-offer conduct,
  ONTEST excluded, absolute $ — the ERCOT-154 population discipline, on the
  full-year corpus that landed after ERCOT-154's probes ran).

## 1. The four Phase-0 questions, answered

**Q1 — Bin resolution: NOT the defect.** 86/100 gap hours land in the wall's
top net-load bin (bin 6, ≥p97) on the apply-time model geometry, 82/100 on the
derive-time EIA-930 geometry (93 % agreement); the rest sit in bin 5. The
ercot43-collapse hypothesis — the scarcity afternoons pooled into a bin whose
median washes out their conduct — is **refuted on the wall's own population**:
the gap-hour-conditioned online-spare ladder is statistically
indistinguishable from the rest of bin 6 (CC p90 multiplier **197 vs 194**;
p95 603 vs 629; p99 2,463 both). There is no finer bin that would recover a
hotter gas ladder, because the gas conduct does not differ at these hours. The
separability sweep confirms it from the driver side: within bin 6 the gap
hours are **not** separable by PRC (p50 5,661 vs 6,077 MW — PRC < 5,000
captures 12 % of gap hours and 4 % of the rest), by net-load depth (≥p99
captures 50 % vs 26 %), or by calendar — while λ differs **17×** ($1,337 vs
$76 p50). No admissible conditioning grain of THIS instrument can discriminate
these hours.

**Q2 — Row coverage: real, secondary.** At the model's own price (merit
crossing on the reconstructed P1 bid stack; median |bid − sidecar price|
$9.07, price-bracket cross-method median deviation $0.54): the wall's own
rows ARE marginal in **41/100** hours (CC 27, CT 14) at a walled level of
**$238 p50** — the wall is present at the margin and sets a price 4–6× under
λ. In **39/100** the margin is a row the wall never touches: CC peak rungs
r0–r2 left at their baked height by the conditional ladder ($85–102, 17 h),
CT `committed` tranches ($247, 9 h), ST_GAS rows (steam flag off, 4 h), COAL
econ ($80, 2 h), misc (7 h). In **20/100** it is a conditional-surface peak
rung (ST_GAS 16 at $103–209, CC_CHP 4). Median marginal bid **$161.69** vs
actual λ p50 **$1,029**.

**Q3 — Class coverage: the model's margin is CC/CT/ST_GAS; the REAL margin was
PWRSTR.** Model marginal class over the 100 hours: CC_REGULAR 46, CT_PEAKER
28, ST_GAS 19 (utilisation at those hours reproduces the parent FINDING:
COAL 98.9 %, CC 91.3 %, CT 71.4 %). But the real price-setter census
(all resource types, dispatched segments in [0.7, 1.3]×λ) attributes the
marginal segments to **PWRSTR — grid batteries**: 33 MW/interval in-band vs 9
for the largest gas type, and of ALL capacity offered ≥$500 at those hours
(1.10 GW incl. ONTEST), **0.91 GW is PWRSTR** (0.556 GW with ERCOT-154's
ONTEST exclusion) against ~0.19 GW for every thermal type combined. **The CT
branch — the ercot-160 item 8(b) licensing blocker — is NOT the binding
issue**: SCLE90 offered only 0.082 GW ≥$500 at these hours, so the successor
does not run through the blocked Texas-hub daily gas basis.

**Q4 — Ceiling/rungs: the wall's geometry has real defects, and repairing them
cannot close the gap.** The rel-clamp census: the wall interpolates
`rel = (share_mid − boundary)/(1 − boundary)` onto a p10..p90 quantile ladder
that `np.interp` clamps at p90 — and the within-plant share midpoints top out
at 0.90–0.92, so of **10,480 MW** of walled CC capacity **6 MW** reaches the
p90 rung (CT: 15 of 3,869 MW); the maximum wall price any row attains is
**$413 (CC) / $1,216 (CT)** at the gap-hour delivered gas ($2.04), with
MW-weighted mean multipliers of 34× ($69) and 102× ($209). The gap-hour bid
stack: 56.4 GW < $120, 2.5 GW at $120–300, 1.1 GW at $300–500, and only
**1.7 GW across $500–3,000** (mostly conditional-surface top peak rungs + the
fast-start pool tail). But the decisive measurement is §2: even a perfectly
re-derived gas ladder cannot carry these hours, because the measured gas
conduct at exactly these hours tops out near **$81/MWh at the dispatched p99
(CC)**.

## 2. The decisive measurement — ERCOT's λ was not formed on the gas fleet

Three independent censuses on the same corpus/clock:

1. **The online spare is exhausted residue at these hours** — CC 0.354 GW /
   CT 0.101 GW (vs 0.7 GW at ordinary bin-6 hours, 2.9 GW at bin 0) — and its
   price distribution is flat across the gap/rest split (Q1). Per-hour, the
   spare's p10 multiplier (8–12× gas ≈ $16–25) is **uncorrelated with λ/gas
   (r = −0.10)** while λ/gas ran 321–993× (p25–p75). The spare — the wall's
   measured population — does not carry the price signal.
2. **The dispatched portion was cheap too.** MW-weighted dispatched-segment
   ladders at the gap hours: CC p50 8.0× / p90 13.4× / **p99 39.8× ≈ $81**;
   CT p99 489× on tiny MW. Merchant gas dispatched ≥$500: **0.06 GW**;
   full-curve (LSL→HASL) ≥$500: **0.12 GW**. The premise that ERCOT had "GW
   offered across $500–3,000" **on the merchant gas fleet's SCED2 curves** is
   refuted — the parent FINDING §4's number described the whole market, and
   the whole market's high-priced GW sit on storage.
3. **PWRSTR carried the price.** The storage fleet's above-LSL,
   HASL-capped discharge offers at the gap hours (ONTEST excluded): p10 $74 /
   **p30 $1,500 / p50–p99 pinned at the $5,000 HCAP**, 0.711 GW offered,
   0.556 GW ≥$500, 0.488 GW ≥$2,000. And this conduct is **standing, not
   event-conditioned**: every one of the seven net-load bins shows p50 =
   $5,000 with 0.55–0.74 GW ≥$500 (year-round hockey stick). The
   discrimination between a $76 ordinary bin-6 hour and a $1,337 gap hour is
   NOT in the storage offer — it is in how deep the system's own crossing ran
   into it. That is exactly the discriminator the LP inherently has and the
   ERCOT-159 reserve-row cap inherently lacked: an offer prices capacity and
   binds only where dispatch actually reaches it.

**Synthesis.** The armed RT wall is *exonerated on its own population*: it
prices the merchant gas fleet at that fleet's measured conduct, and the
merchant gas fleet genuinely did not carry the $500–3,000 offers at these
hours. The model's residual exists because its marginal resource at these
hours is gas/steam priced $85–441, while reality's marginal resource was a
battery fleet offering ~0.6–0.9 GW at $1,500–5,000 — **a class the model
prices at a flat `battery_dispatch_adder` = $10 + LP opportunity cost, with no
offer instrument at all**. The model's storage discharges 653 MW mean at
the gap hours (max 1,530) — comparable in MW to the real fleet's whole online
energy-side capability (0.71 GW) — so the defect is its *price*, not its
volume.

## 3. Why this does not re-open ERCOT-154 (rule 28(a) compliance)

ERCOT-154 refused the storage discharge-offer arm — but on the **evening
h17–21 average object**, from the **2024/2025 sample-day extracts** (its
write-up records "2023 carries no measured surface by construction"; the
full-year delivery-2023 corpus landed at ERCOT-157, after its probes ran).
What is new, per ground:

- **(b) "the lever cannot produce the phenomenon" (evening slope 1.6 $/MWh/GW
  ⇒ withholding storage buys $1.38–3.05)** — measured on the 15–17 GW evening
  cushion framing that the owner-endorsed parent FINDING **superseded at
  these hours**: the top-100 hours run 6.63 GW headroom at 90.3 % utilisation,
  and the stack census above shows the crossing sitting at the bottom of a
  thin $120–500 band. The ground does not hold at the hours that carry the
  residual.
- **(c) "breaks a measured quantity already short"** — measured on 2025
  EIA-930 annual volume (no 2023 `NG: BAT` series exists) and on pooled
  evenings. At the gap hours the model's 653 MW mean discharge ≈ the real
  fleet's 0.71 GW measured online energy capability; a measured re-price
  binds only where the model's price is below the measured offer, and SOC
  re-optimisation moves the same energy toward the same scarce hours reality
  did. The annual-volume guard belongs in the successor's pre-registered
  gates, not as an ex-ante refusal.
- **(a) representation (one discharge column per storage unit; a single price
  collapses the measured rising ladder)** — **still true and still binding**:
  this is the reason the successor must be **multi-tranche** (below), which
  ERCOT-154 itself named as the required form ("the rungs a multi-tranche
  form needs are unidentified"). Those rungs are now identifiable: the
  full-year 2023 corpus provides dense coverage (400 gap-hour intervals;
  every bin populated), and at absolute-$ grain the upper rungs are
  *degenerate at HCAP by measurement* (p50–p99 = $5,000 in all seven bins) —
  a stable identification, not an unstable one. The p10–p30 toe is the part
  needing the year-pair stability test, exactly where ERCOT-154's own p30
  test PASSED (2025/2024 ratio 0.969, rel IQR 0.143).
- **The ERCOT-154 DO-NOT-REDO items are honoured**: the successor is not the
  single-price arm, not gas-multiple-based (absolute $ — ERCOT-154 refuted
  the gas basis for storage), and no rung is selected on the model's
  absorption.

The `battery_dispatch_adder` ERCOT cell stays `K` (the incumbent is
unchanged); no cell verdict is minted by this session. The successor enters
the matrix as a new row when its `ScenarioConfig` field is built
(rule 28(c), same-PR).

## 4. The chartered successor (NAMED AND CHARTERED — NOT armed, NOT built here)

**Mechanism: `ercot_storage_rt_offer_surface` (working name) — a measured
multi-tranche RT discharge-offer surface for ERCOT battery storage.** Split
each ERCOT battery storage unit's discharge variable into K tranches sharing
the unit's SOC pool and power cap (the thermal-tranche pattern on the storage
columns; SOC/charge untouched), with tranche prices set to the MW-weighted
absolute-$ quantile ladder of the measured PWRSTR above-LSL, HASL-capped
discharge offers, per net-load-percentile bin (the shared
`NETLOAD_PCT_EDGES` geometry), year-scoped with no pooled fallback (the RT
wall's rule-13 precedent). Population discipline per ERCOT-154: ONTEST
excluded; ONREG/ONFFRRRS included (they are online AS-carrying states whose
HASL cap already nets the AS award). Zero fitted scalars; frozen rule 23.

- **Rule-19 reconciliation**: the arm REPLACES the flat
  `battery_dispatch_adder` ($10) on ERCOT battery discharge pricing — one
  owner per row; the PS adder and other ISOs untouched (rule 25). The AS-side
  storage capability keeps its own owners (the co-opt reserve rows); this
  surface prices the ENERGY-side discharge only, which is exactly what the
  HASL cap measures.
- **Forward story (rule 13)**: bins regenerate from any year's own net
  load; the conduct is a standing property of the fleet (measured flat
  across bins), scales with the evolving storage fleet through the existing
  capacity-evolution storage stack, and would respond to changed conditions
  through the LP's own crossing depth. The admissibility test passes: the
  same quantity could be produced for a forward year from forward drivers.
- **Identification phase (before any solve)**: derive the 2023 block from the
  full-year corpus; 2024/2025 blocks from the committed sample-day extracts
  (the RT wall's own 2024/2025 basis); fix K and the quantile set a priori;
  report the year-pair stability of every rung (the p10–p30 toe is the live
  question; p50+ is HCAP-degenerate by measurement) and the ONTEST/ONREG
  population shares. Disclose every grain variant computed (the ercot-159
  precommit discipline).
- **Pre-registered gates (the ERCOT-158/159 pattern), to be carried by the
  successor's PRECOMMIT**: C3a grace +1.0 pp; **zero-spurious mid-band**; the
  33-fabricated-tail kill (new tail hours outside the actual tail); NRMSE
  +0.005; matched-hour C3c on the control's own prices; **the 2025 EIA-930
  storage-volume guard** (model discharge vs `NG: BAT`, the ERCOT-154 ground-
  (c) recurrence test — 2025 is the only year with a full series); D-2 vacuous
  by construction (an offer, never a floor); K/R/I decision rule and LOYO
  within 2023–2025 stated ex ante. Control = fresh same-HEAD `replay_keeper`
  run, both arms `--year 2023 2024 2025` sequential (rule 12; ~10 GB RSS
  each).
- **What would refute it, stated now**: if the model's crossing at the gap
  hours does not reach the storage tranches (the thermal stack absorbs the
  withdrawn ~0.65 GW below $500), the arm is INERT and the residual object
  moves to the quantity side (the AS/energy split of storage capability at
  scarcity); if it lifts the 163 ordinary bin-6 hours ERCOT cleared at $76
  p50, the standing-conduct premise mis-transfers into the LP and the arm is
  R on the zero-spurious gate.
- **Structural cost, named**: K extra discharge columns per battery unit in
  the LP layout (`Dis[s,k,t]` sharing SOC and power-cap rows) — a
  `model/` change gated ERCOT-only, plus the derive + its schema. This is a
  structural LP change: **owner authorization is required before it is
  built**, per this lane's convention for structural arms (the ercot-159
  item-9 precedent).

## 5. Corrections this finding makes to standing text

- The parent FINDING §4's "ERCOT has GW of capacity offered across
  $500–3,000" is **correct for the market and wrong for the merchant gas
  fleet**: at the top-100 hours the $500+ GW sit on PWRSTR (0.91 of 1.10 GW
  incl. ONTEST). Any successor text should say "on the storage fleet".
- ERCOT-155's census line "essentially no model capacity priced between ~$120
  and ~$2,800" (measured on the ercot150 keeper) is superseded in magnitude on
  the ercot158 keeper: the gap-hour stack carries ~3.6 GW at $120–500 and
  ~1.7 GW at $500–3,000 (conditional top rungs + pool + wall) — still ~an
  order of magnitude thinner than the real market's storage wall relative to
  the crossing, and concentrated in rows the crossing rarely reaches.
- ERCOT-159's rejection narrative gains its final clause: the energy cap
  forced price through the reserve channel; the ENERGY channel's real carrier
  at these hours was the storage fleet's offers — the population neither the
  gas walls nor any reserve row represents.

## 6. Governance

No LP, no solve, no registration owed (rule 15 — the
ERCOT-142/143/145/147/152/154/155/159-addendum no-LP pattern). No mechanism
tested ⇒ no matrix cell verdict (rule 28(b)); the `battery_dispatch_adder`
row's note gains a pointer to this finding (recorded adjudication transcription,
zero verdicts minted), and the §5.1 queue's successor entry is re-stamped to
this object. No `ScenarioConfig` field added ⇒ rule 28(c) does not fire.
Holdouts untouched: 2023 only, training span (rule 22). ERCOT-scoped
(rule 25). Scope fence honoured: the ERCOT-155 offer-dispersion refusal
(cold-capacity pricing) is not touched — the storage surface prices ONLINE
telemetered capability at its own submitted curve, the ERCOT-158 status
distinction; the ercot41/43/106/108 envelope family, shoulder-span,
West/Panhandle topology, item 6, items-5/6 reopen, and `ercot_ordc_only_scarcity`
remain closed; the offer LEVEL program is not re-derived (the gas walls are
exonerated, not re-tuned). The CT item-8(b) licensing blocker is documented
NOT binding on this successor (§1 Q3).
