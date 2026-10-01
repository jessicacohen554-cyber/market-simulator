# Accreditation-basis adjudication memo — ICAP / UCAP / FPR (#1532) — 2026-07-12

**Session.** P-2B of `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
(§3.4.2). Memo only — **no code changed**. Adjudicates the open #1532 flag
(gap register, 2026-07-06 post-#1503–#1532 addendum) using the P-2A validation
numbers (`docs/handoffs/capacity-price-validation-2026-07-12.md`), the stage-5
§6 ICAP/UCAP pairing audit
(`docs/handoffs/fom-scarcity-joint-protocol-2026-07-06-stage5-energy-only-floor.md`),
and the live code (`model/capacity.py` accreditation/requirement paths,
`config/constants.py` `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO` /
`MARKET_DESIGN`, P-0B raw data under `data/raw/capacity-market/`).

**Decision put to the owner (box in §6): adopt Option A — per-ISO
published-basis consistency.** For each capacity-market ISO, the requirement,
the supply ledger, the CR-1 curve position, the curve's dollar anchor, and the
per-unit payment all sit on **that ISO's own published accreditation basis** —
for PJM that is the FPR / ELCC-class-rating basis end-to-end; for MISO the
existing EFORd-flavored pairing is already ~consistent and stays; NYISO and
NEISO get their own pairing audits before they are curve-eligible. The
migration is a published-parameter re-derivation plus one supply-side basis
extension; it re-opens the items listed in §4.3 and **nothing on the backcast
dashboard** (capacity evolution is forecast-mode only).

---

## 1. Why this exists (one paragraph)

Stage-5 §6 (PR #1513/#1532 lane) correctly found that testing an ICAP-stated
requirement (PJM IRM, MISO ICAP-PRM) against a UCAP-counted supply ledger
double-counts forced-outage risk, and fixed the **requirement** side by
adopting each ISO's own published conversion
(`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`: PJM FPR/(1+IRM) =
0.9170/1.191 = **0.7699**; MISO (1+PRM_UCAP)/(1+PRM_ICAP) = **0.9326**). The
#1532 flag is that PJM's conversion is **not an EFORd number**: since the
2025/26 CIFP accreditation reform, PJM's FPR embeds the **pool-wide
average-ELCC accreditation ratio ≈ 0.77–0.78** (every resource class,
thermal included, accredited at ELCC-based class ratings), while the model's
supply ledger still counts thermal at **(1 − EFORd) ≈ 0.92–0.97** and pays
capacity on the same (1 − EFORd). Correcting one side of a two-sided
comparison onto a *different* basis than the other side replaced one basis
error with another — and P-2A measured both halves of the damage.

## 2. (a) The three bases in play, and where each enters

| Basis | What it is | Where it enters TODAY (code anchor) |
|---|---|---|
| **B1 — Published FPR / ELCC-class basis** (PJM post-2025/26 reform) | Requirement stated in accredited UCAP: `peak × FPR`, FPR = (1+IRM) × pool-avg ELCC ratio (≈0.77). Supply accredited at published **ELCC class ratings** (2025/26–2026/27 BRA finals: nuclear ~95 %, coal ~84 %, gas-CC ~79 %, gas-CT ~62 %, 4-h storage 50 %, tracking solar 11 %, onshore wind 41 %). Prices ($/MW-day) quoted per **UCAP-MW**: net-CONE 212.14 $/MW-day = 77.43 $/kW-yr; cap 329.17 $/MW-day. | **Requirement only** — via the 0.7699 ratio inside `resolve_adequacy_requirement_mw` (`capacity.py:788`). Nowhere on the supply or payment side. |
| **B2 — Model hybrid UCAP basis** | Thermal at `pmax × (1 − EFORd)` (`EFORD`, `constants.py:760` — factors 0.92–0.97), VRE at flat generic credits (wind 0.16 / solar 0.18), storage at duration-ELCC × dilution. | **Supply ledger** `accredited_firm_capacity_mw` (`capacity.py:2240`) → reliability floor, build backstop, and the CR-1 position `capacity_reserve_position` (`capacity.py:2279`). **Payment** `capacity_revenue_per_mw_yr` (`capacity.py:602`) multiplies the clearing price by (1 − EFORd). |
| **B3 — ICAP-basis PRM with ratio correction** | The stage-5 construction: `peak × (1 + PRM_ICAP) × icap_to_ucap_ratio`. Arithmetically equals B1's requirement for PJM/MISO (that was the point), except a **vintage mix**: PJM PRM 0.178 is the 2025/26 IRM while the 0.7699 ratio is 2026/27 → composite 1.178 × 0.7699 = **0.907** vs the published 2026/27 FPR **0.9170** (−1.1 %). | **Requirement** `resolve_adequacy_requirement_mw` — shared by floor, backstop, and CR-1 position (one requirement, rule 19). |
| *(anchor sub-issue)* | PJM publishes net-CONE **both ways** in the same Table 3: 60,396 $/MW-yr (ICAP-annual) and 212.14 $/MW-day (UCAP) — ratio 60,396 / 77,431 = **0.780**. The price cap likewise: 256.75 $/MW-day-ICAP vs 329.17 UCAP = 0.780. (On disk: `data/raw/capacity-market/demand-curve/pjm/pjm.csv`.) | CR-1's PJM anchor `net_cone_curve_per_kw_yr = 60.396` (`constants.py:2580`) is the **ICAP-annual** figure, but the curve it scales is compared against **UCAP-$** clearing prices. |

So today the pipeline is **B1 requirement → B2 supply/position → B2 payment on
an ICAP-$ anchor**: three seams, three bases. Note the two published PJM
conversions are close but not identical (FPR/(1+IRM) = 0.7699 vs the price
tables' 0.780) — each is PJM's own number for its own lane (quantity vs price)
and they must never be blended into one hand-derived factor.

## 3. (b) The sign-flip risk, quantified on the P-2A numbers

### 3.1 The position-side flip — realized, not hypothetical

P-2A Pass 2 (PJM hindcast fleet): accredited reserve position **1.292 / 1.363
/ 1.349 / 1.296** (2021/23/24/25) against a curve whose entire priced region
spans **0.99–1.045**. The curve pays **$0 in every year**, including 2025/26,
which actually cleared 98.5 $/kW-yr near the cap — a −100 % payment error with
the *opposite sign* of the market's signal. System scale: the real 2025/26 BRA
paid 135,684 MW × 269.92 $/MW-day ≈ **$13.4 bn/yr**; the model's screens see
$0 of it.

Decomposing the 2025 row with the model's own ledger
(`results/hindcast/pjm-2021-2025-realized/…/evolution_2025.json`, thermal
nameplate 182.8 GW: coal 46.4, gas-CC 63.5, gas-CT 27.8, gas-ST 10.4, nuclear
28.6, oil 4.2, biomass 2.0):

- On the model's B2 factors the thermal block accredits **172.1 GW** → fleet
  average **0.941**.
- Restated at PJM's published ELCC class ratings (indicative values above —
  the thermal rows of PJM's final class-ratings doc are **not yet intaken**,
  see §4.3-R3) it accredits ≈ **145.2 GW** → average **0.794**. The supply
  block alone is overstated **×1.185** relative to the basis the FPR
  requirement presumes.
- Restating supply: firm 188.7 → ≈161.8 GW → position **≈1.11**, vs the
  measured **1.296** and the auction's actual **1.007**.

So of the 2025 position excess (+0.29 over reality), **≈0.185 (≈2/3) is the
basis mismatch and ≈0.10 (≈1/3) is real fleet error** (the −63 %
retirement-miss owned by the retirement-calibration lane). A ~18 % position
bias on a curve whose priced region is 5.5 points wide is ~3× the width of the
entire curve — this is why P-2A's "decisive blocker" exists, and the majority
of it is adjudicable here without touching the fleet.

This is the #1513/#1532 sign flip in its realized form: **in exactly the
high-scarcity scenario the flag named (a genuinely short market), the
mismatched pipeline reads "long, pay $0" while the real market pays near-cap
— so the entry screen sees no reason to build and the retirement screen
retires *into* the shortage.** A new CT at the true 2025/26 position (1.007)
earns ≈ 1.177 × 77.43 × 0.62 ≈ **56 $/kW-yr** installed in the real design;
the model pays **$0** — a payoff sign flip on any entrant or incumbent whose
going-forward cost sits between.

### 3.2 The anchor-side flip — the uniform −22 %

P-2A Pass 1B: PJM residual is a uniform **−22 to −28 %**. That is the ICAP-$
anchor: the model scales its (exactly-correct-shape) curve by 60.396 $/kW-yr
while the auction clears against the 77.43 UCAP-$ reference — ratio 0.780,
confirmed independently by the published cap pair (256.75/329.17). Every model
price lands ≈22 % low even at the *published* position, before any fleet or
supply-basis error.

### 3.3 The trap this memo must close — error cancellation

Dividing the ratio back out of the Pass-2 positions (i.e., reverting stage-5's
requirement fix) gives 1.292→**0.995**, 1.363→**1.049**, 1.349→**1.039**,
1.296→**0.998** — three of four years land inside the priced region and the
curve starts "reproducing" prices. That is two compounding errors cancelling
(ICAP-overstated requirement vs B2-overstated supply), the precise thing rules
1/13 forbid: reaching the right number through a mechanism that isn't real.
**Reverting the ratio is not an option**, however good it makes Pass 2 look;
the stage-5 test (`test_icap_ucap_ratio_reverses_naive_pjm_vs_ercot_comparison`)
and its filing citations stand.

### 3.4 Per-unit payment errors (secondary but real)

At an identical position, the two current errors partially cancel for
high-ELCC thermal and diverge for peakers: model pays `price(60.4-anchored) ×
(1 − EFORd)`; the market pays `price(77.4-anchored) × class-ELCC`. For gas-CC
(0.95 vs 0.79 accreditation) the model is ≈ −6 %; for gas-CT (0.94 vs 0.62) ≈
**+20 %** — a class-differential distortion that tilts the entry mix toward
CTs even when the level is roughly right. The position error of §3.1
dominates, but this term is why the payment seam must migrate with the ledger
(one accreditation resolver for both, rule 19), not be patched separately.

## 4. (c) The recommended basis, migration path, and triggered re-derivations

### 4.1 The single basis

**Per-ISO published-basis consistency:** each capacity-market ISO's
requirement, supply ledger, CR-1 curve position, curve dollar anchor, and
per-unit payment all on **that ISO's own published accreditation basis** —
the same principle the ERCOT accreditation audit already established for the
CDR seasonal-rating basis (`THERMAL_ACCREDITATION_BASIS_BY_ISO`), extended to
the ELCC-reform ISOs. Concretely:

| ISO | Requirement | Supply & payment accreditation | Curve $ anchor | Verdict |
|---|---|---|---|---|
| **PJM** | `peak × FPR` (published, per delivery-year vintage — devintages today's 1.178×0.7699 mix) | Published **ELCC class ratings** for ALL classes (thermal + storage + VRE), from the extended P-0B elcc datatype | 77.43 $/kW-yr (212.14 $/MW-day UCAP × 365/1000) | **Migrate** (this memo's main object) |
| **MISO** | Keep `(1+PRM_ICAP) × 0.9326` — MISO's conversion IS EFORd-flavored (UCAP = ICAP × (1−XEFORd)), so B2 supply (avg 0.93) is already ~consistent (implied pool factor 0.9326) | Keep (1 − EFORd) thermal; VRE → CR-3.1 MISO ELCC curves (on disk) | 79.8 $/kW-yr (already the published Net CONE) | **Keep, verify in CR-3** |
| **NYISO** | IRM 24.4 % is ICAP-stated, **no ratio in the registry** → today's pairing (ICAP req vs UCAP supply) is the same error class in the **opposite direction** (position understated ~5–7 %, over-pays) | (1 − EFORd) matches NYISO's own UCAP construction — the requirement is the broken half | 50.55 (published ARV) | **Pairing audit required** before curve eligibility (stage-5 already flagged; P-2A blocks NYISO on curve vintage anyway) |
| **NEISO** | Net ICR basis vs qualified capacity (≈ seasonal claimed capability, no EFORd derate — outage risk lives in Pay-for-Performance) → B2 supply likely **under**-counts vs ISO-NE's own ledger | audit with the FCA qualified-capacity definition | 108.94 (published FCA18) | **Pairing audit required** (same bar) |
| **CAISO / ERCOT** | CAISO fixed proxy (no curve, gate is a no-op); ERCOT already fixed on the CDR seasonal-rating basis by the accreditation audit | — | — | **No change** |

**Why not one global convention:** the ISOs genuinely differ — PJM reformed
onto ELCC-for-everything, MISO/NYISO stayed EFORd-flavored, ISO-NE counts
undischarged capability and prices performance separately, ERCOT's CDR carries
outage risk in the target margin. A single global basis would misstate at
least three of them; the rule that generalizes is *pairing consistency within
each ISO*, enforced per-ISO by the existing registries.

### 4.2 Migration path (ordered; each step independently testable, no LP)

1. **Anchor re-derivation (data already on disk, pure constants change):**
   `MARKET_DESIGN["PJM"].net_cone_curve_per_kw_yr` 60.396 → **77.431**, cited
   to the 212.14 $/MW-day UCAP row of the on-disk 2026/27 planning-parameters
   CSV; update `tests/test_capacity_demand_curve.py` reconciliation. Removes
   the uniform −22 % of §3.2 regardless of everything else.
2. **Requirement devintage:** resolve PJM's requirement from the published
   **FPR of the matching delivery year** (new `FORECAST_POOL_REQUIREMENT`
   rows in the P-0B demand-curve datatype; `resolve_adequacy_requirement_mw`
   prefers a published FPR where one exists, falls back to
   `(1+PRM) × ratio` otherwise). Fixes the −1.1 % vintage mix (0.907 vs
   0.9170) and makes the requirement construction literally the ISO's own.
3. **Supply-basis extension (the substantive step):**
   `THERMAL_ACCREDITATION_BASIS_BY_ISO` grows an `"elcc_class_rating"` basis
   (PJM), resolved per fuel class from the extended elcc datatype;
   `_thermal_firm_mw` reads it exactly as it reads `"seasonal_rating"` today.
   Storage: reconcile `STORAGE_ELCC_BY_DURATION` with PJM's published storage
   class ratings (4-h = 50 % on disk) for PJM only — one mechanism, no
   double-derate (rule 19; same enumeration discipline as the CR-3.1 charter).
   VRE: CR-3.1 curves (P-2C) — under this basis PJM wind moves 0.16 → ~0.41
   class-average (the model currently *under*-credits PJM wind 2.5×) and
   solar 0.18 → ~0.08–0.11.
4. **Payment seam:** `capacity_revenue_per_mw_yr` multiplies by the unit's
   basis-resolved accreditation (the same resolver the ledger uses), replacing
   the hardcoded `(1 − EFORd)`. Ledger and payment can then never diverge
   again by construction.
5. **Re-validate (no LP):** re-run `scripts/validate_capacity_prices.py`
   Pass 2. Expected: PJM positions ≈1.11–1.19 (still long — the residual is
   the retirement miss, owned by the retirement-calibration lane + G-31), and
   Pass-1B residual collapses from −22/−28 % to the frozen-vintage ±10 %.
   The default flip remains gated on P-2A's §7 prerequisites — this memo
   clears prerequisite 1, not 2–4.

### 4.3 Published-parameter re-derivations / intakes this triggers

- **R1** `MARKET_DESIGN["PJM"].net_cone_curve_per_kw_yr` (step 1) + the
  reconciliation test.
- **R2** PJM requirement vintage: FPR-per-delivery-year intake rows (step 2);
  `PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]` 0.178 gets superseded on the
  requirement path for PJM (kept for ISOs without a published FPR).
- **R3** **P-0B elcc datatype extension (intake session):** the on-disk PJM
  file has NO thermal class-rating rows (only intermittent/storage/DR — 135
  rows checked this session). The thermal ratings are in the same
  already-cited PJM final-ratings documents; the §3.1 decomposition used
  indicative values and must be re-stated from the intaken rows before step 3
  lands.
- **R4** PJM fixed-mode anchor `net_cone_per_kw_yr = 100.0`: neither the ICAP
  (60.4) nor UCAP (77.4) published figure. P-1B kept it for default
  byte-identity, earmarking reconciliation for "the P-2A default flip"; under
  Option A re-derive it to the published UCAP-basis figure **in the flip
  commit** (until then it stays, explicitly labeled legacy).
- **R5** NYISO + NEISO pairing audits (new gap-register rows): each needs its
  own filing check (NYISO's published IRM→UCAP translation; ISO-NE's
  qualified-capacity definition) — the stage-5 bar, no touching without the
  citation.
- **R6** Methodology-spec §5.8/§5.9 + `docs/parameter-citations.md` sync
  (`/sync-docs` at the implementing session's end).

## 5. (d) How CR-3.1 marginal-ELCC curves change the answer

They **support but cannot substitute for** the adjudication:

1. **CR-3.1 alone closes only a sliver of the PJM gap.** As chartered
   (wind/solar only), it re-bases ≈10–17 GW of a ≈189 GW firm ledger; the
   wind correction (0.16→0.41) *raises* and the solar correction
   (0.18→0.08–0.11) *lowers* accredited MW — net a ±2–4-point position move.
   The 18-point basis bias of §3.1 lives in the **thermal** block (0.94 vs
   0.79 average), which CR-3.1 as written never touches. Adjudicating "wait
   for CR-3.1" (Option C below) leaves the sign flip live.
2. **CR-3.1 makes Option A cheaper and the alternatives worse.** It lands the
   ELCC datatype plumbing, the penetration-indexed resolver, and the
   per-ISO-override pattern Option A's step 3 reuses; conversely, once VRE is
   on published ELCC, a supply ledger that mixes published-ELCC VRE with
   (1 − EFORd) thermal against an FPR requirement is *less* internally
   coherent than today's.
3. **The forward story (rule 13) only exists under Option A.** PJM's
   preliminary ER24-99 marginal-ELCC trajectories (on disk: onshore wind 35 %
   → 19 % across 2026/27–2032/33) give the FPR basis a forward-regenerable
   driver — accreditation that responds to modeled penetration in forecast
   years. The (1 − EFORd) basis has no forward analogue of the accreditation
   dynamics the reformed market actually applies to entrants and incumbents.
4. **Sequencing stands as planned:** P-2C consumes this memo's adopted basis
   (the plan's Wave-2 ordering); its scope should be confirmed to include the
   R3 thermal-class intake or a sibling item opened for it.

## 6. Owner-decision box

| | Option | What it is | What it re-opens | Verdict |
|---|---|---|---|---|
| **A** | **Per-ISO published-basis consistency** (§4.1–4.3) | PJM → FPR requirement + ELCC-class supply & payment + UCAP-$ anchor; MISO keeps its (consistent) ratio; NYISO/NEISO pairing audits; ERCOT/CAISO untouched | R1–R6 (§4.3); P-2C scope confirmation; P-2A Pass-2 re-run (script only); PJM forecast floor/backstop volumes shift (supply accredits ~15 % lower → floor retains more, backstop builds more — measured in the Pass-2 re-run + P-3D hindcast rescore, NOT tuned); **no backcast keeper or dashboard artifact** (forecast-only machinery) | **RECOMMENDED** |
| B | Revert the ICAP→UCAP ratio (back to ICAP requirement vs B2 supply) | Makes Pass-2 positions land in the priced region (0.995–1.049) | Re-opens the stage-5 phantom-margin double-count its own filing citations killed; the "fit" is two errors cancelling (§3.3) | **REJECT — rules 1/13** |
| C | Status quo + wait for CR-3.1 | Keep B1-requirement/B2-supply mismatch; let P-2C fix VRE only | Leaves ~18 % thermal-driven position bias and the §3.1 sign flip live; P-2A §7 flip prerequisites unmeetable; every capacity-market forecast keeps a $0-paying curve mode | **REJECT** |
| D | Normalize the model's supply by a model-derived pool factor (divide firm by fleet-avg accreditation ratio) | One scalar patch instead of per-class basis | A self-referential, fleet-dependent conversion — exactly what stage-5's "not a model-derived pool EFORd" clause was written to prevent; drifts as the model's own mix drifts | **REJECT — rule 24 spirit** |

**Recommendation: Option A.** It is the only option in which every number in
the requirement→position→price→payment chain is a published market-design
parameter on the basis its ISO publishes it (rule 13), it is the stated
prerequisite 1 of P-2A §7 for any future `capacity_market_clearing` flip, and
it converts the #1532 flag from an open incompatibility into two bounded work
items (R3 intake + step-3/4 implementation) plus two audits (R5). What it does
**not** claim: it does not make the curve payable on the current hindcast
fleet (position ≈1.11 is still past the zero-cross) — the remaining third of
the excess is the retirement miss, which stays with its own lane and must not
be laundered through accreditation.

*Produced 2026-07-12 (P-2B). Verified against the working tree at
`origin/main` merge-base 673e987; no code, data, test, or dashboard file was
modified. Follow-ups on owner sign-off: R1–R6 (§4.3) as an implementation
session; NYISO/NEISO audit rows for the gap register; P-2C scope
confirmation.*
