# PREREG miso-216 — THE GAS-OFFER MARGIN ANCHOR'S BASIS/CLASS GRAIN: phase 0 (zero-solve) prices every admissible identification point, measures what each does to the FIVE ALREADY-ARMED MISO gas classes, counts the cross-ISO blast radius, and delivers an OWNER PACKET. **ARMS NOTHING.** (2026-09-05)

**Pushed BLIND** — before any adjudicating statistic of this session and before any arm is
designed. Keeper at open `2026-09-05-miso-213-layering` (bundle
`results/calibration/miso213_layering_B`), **NOT-YET on C3a-2025 alone (−11.747 %)**, C3c
ledgered 3/3, C6 attested 41/2. Branch `claude/miso-216-anchor-basis-grain` from
`origin/main` **`a0014864`**, which contains the miso-215 work (its FINDING, PREREG, probe,
JSON record and the `constants.py` MISO-anchor comment correction, merged as PR #4770).
Rule 22 `[R-HOLDOUT]`: **2023–2025 only** — MISO holds no marker; the probe hard-asserts it.
Rule 25 `[R-ISO-SCOPE]`: MISO's shard only. **No `ScenarioConfig` field, no registry entry,
no matrix row — so rule 28(c) is not engaged and no other shard is touched.**

---

## 1. The object, carried in from miso-215 as STATED FACT (not re-measured here)

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"] = 3.0492` reproduces **exactly** as annual Henry Hub
plus the flat `GAS_BASIS_DIFFERENTIAL["MISO"] = 0.30` — measured series-minus-HH
**+0.2992 / +0.2993 / +0.2990**, a constant in every year — because
`scripts/data/derive_gas_offer_margin_anchor.py` reads
`data.fuel.trajectories._gas_series` under
`GAS_SERIES_FLAGS["MISO"] = {gas_seasonality, gas_daily_shape, miso_zonal_gas_basis}`, which
is ISO-level. The keeper prices the fleet by the per-plant EIA-923 print
(`gas_plant_monthly_fuel_pricing=True`, `gas_monthly_actuals=False`,
`gas_hub_basis_overlay=False`), applied on the `(n_gen, T)` array **after** that series and
invisible to the derive.

Because `apply_gas_offer_margin`'s economic content is a fixed margin `markup_hr × anchor`,
that difference sizes what the KEEPER already installs (miso-215 §4c):

| armed class | `markup_hr` | fixed margin @ anchor | @ its own MEAN fuel 23/24/25 |
|---|---:|---:|---|
| `CT_PEAKER` | 3.9059 | **$11.91/MWh** | 24.76 / 18.25 / 21.95 |
| `ST_GAS` | 2.0475 | **$6.24/MWh** | 8.29 / 9.86 / 11.02 |
| `CC_REGULAR` | 0.4862 | **$1.48/MWh** | 1.41 / 1.33 / 1.92 |

**This is the BASIS/CLASS grain. It is NOT the ZONAL grain** (`gas_offer_margin_zonal_anchor`,
adjudicated `I` at miso-119/120 and made doubly moot in a MISO backcast by miso-213's
`miso_zonal_gas_basis_skip_923_priced`) — that cell is **not re-tested and not re-opened**.

**Four miso-215 results are carried in as FACTS and will not be rediscovered:**

* **(F-1) The coverage-gap arm is READY and is NOT this lane's lever.** K-a passes (one
  MISO-gated boolean at `data/offer_curves._offer_curve_for_group`, zero free parameters);
  K-b passes 9 of 9 cohort-years (each cohort's own measured marginal-HR multiplier within
  0.0344 / 0.0388 / 0.0149 of the borrowed parent midpoint against ±0.06, on 94–100 % of
  capacity). **Held behind this question. Not re-measured, not armed.**
* **(F-2) A HIGHER, BETTER-PLACED ANCHOR IS ADVERSE, NOT FAVOURABLE.** Re-anchoring on each
  cohort-year's own delivered mean DEEPENS the arm (CT_INTERMEDIATE 2023 −1.475 → −4.218 TWh;
  2024 −5.285 → −7.043), because a fixed $/MWh margin prices UP exactly the low-fuel hours
  the class is marginal in (cap-w mean offer shift −6.35 / −2.03 / −5.02 $/MWh at a raised
  share of only 0.395 / 0.565 / 0.160). **Any prediction that a raised anchor helps C3a or C1
  is already refuted and this PREREG makes none.**
* **(F-3) THE MEAN-VS-MEDIAN SPLIT IS THE WHOLE QUESTION.** On the MEDIAN there is arguably
  nothing to fix (max |gap| 0.82 over all six cohorts × three years); on the capacity-hour
  MEAN the CT and ST classes are 0.9–3.3 off. **Both are reported side by side and neither is
  privileged.** The miso-215 instrument asymmetry — cohort means capacity-hour weighted while
  percentiles were unweighted — is a real defect and is **repaired first** (M-0 below).
* **(F-4) THE OIL CONFOUND IS CLOSED.** A second fleet build with `dual_fuel_switching=False`
  puts the oil-parity step at **0.000** of the econ capacity-hours of all six cohorts in all
  three years, the two series agreeing to ≤ $0.024 on the intermediate cohorts. The CT/ST
  premium is a GAS PRINT. **Not re-opened; the two-build technique IS reused.**

## 2. Why this is OWNER-COURT and what this session may therefore do

Re-identifying the anchor is a change to a mechanism's **identification**, not a
re-derivation on new source data, so rule 23 `[R-FROZEN-DERIVE]` does not reach it; it moves
**five already-armed MISO gas classes at once**; and PJM, CAISO, NYISO and NEISO carry the
identical construction, so an ISO-local answer would be a rule-25 `[R-ISO-SCOPE]` boundary
crossing. **This session's job is the EVIDENCE PACKET, not the ruling.** No field, no
registry entry, no matrix row, no solve. If the owner does not rule in-session (see §6), the
packet is the deliverable and the lane hands off to the alternative queue head.

## 3. Instrument, and what it can and cannot see

* **Zero solve.** Every number from committed artifacts and the HEAD fleet chain.
* **The `_miso212` import trap, closed the same way twice already** (miso-214 §9, miso-215
  §1): `_miso212_south_gas_cost_basis` transitively imports `_miso211_rdt_binding_state`,
  which re-points `_miso134.BUNDLE` to `miso210_clock_B` **at module scope**. The T-1
  re-pointing block sits AFTER the last import and carries a hard assert on
  `miso_zonal_gas_basis_skip_923_priced`, a keeper-only field.
* **Footing check, pre-registered:** the probe must reproduce miso-215's published cohort
  numbers exactly — cohort capacities 9,333.2 / 24,877.0 / 4,290.8 MW, `CT_PEAKER` remainder
  `markup_hr` 3.9059 and its $11.91/MWh margin at the anchor. Disagreement means the T-1
  re-point missed and the run is void.
* **Plant-grain model merit is the miso-215 PRICE-TAKING STATIC SCREEN**, not the LP: the
  keeper ships no `unit_hourly/` or `dispatch/`. miso-214 §1 measured it at **1.41–1.43×**
  the LP's own CT class energy, and **it holds price fixed, so cross-class backfill is
  invisible to it.** Every A-2 reach number is a BOUND and the K-1 exposure is an
  **un-instrumented risk**, never a measurement. Stated here, before the numbers.
* **The anchor is ONE scalar over the whole 2023–2025 window**, while a fleet or class
  statistic is naturally per-year. A-1 therefore reports **both** the per-year statistic and
  the window statistic that is the apples-to-apples replacement for 3.0492, so the "grain"
  question is never confounded with the "window mean" question.
* **What this instrument CANNOT do:** it cannot tell you which grain is *right*. It prices
  each candidate and reports the consequences. The choice is a judgement about what the
  mechanism's identity means, and that judgement is the owner's.

## 4. What will be measured (M-0, A-1 … A-4)

Probe `scripts/probes/_miso216_anchor_basis_grain_phase0.py` → record
`results/calibration/_miso216_anchor_basis_grain.json`. Reuses the miso-215 readers
(`build_year`, `keeper_config`, the static screen, the margin-sizing block, the two-build
dual-fuel separation).

* **M-0 THE F-3 INSTRUMENT REPAIR, FIRST.** Every distributional statistic below is
  **capacity-hour weighted on both legs** — weighted mean AND weighted quantiles (an explicit
  weighted-percentile implementation, not `np.percentile`). The miso-215 unweighted
  percentiles are re-reported beside the repaired ones so the size of that defect is visible
  rather than quietly corrected.
* **A-1 THE CANDIDATE GRAINS, ENUMERATED AND PRICED.** For each admissible identification
  point, the MISO anchor it implies (per year and over the window) and the fixed margin
  `markup_hr × anchor` it installs on all six cohorts:
  **(a)** status quo — the ISO `_gas_series` window mean, 3.0492;
  **(b)** the gas fleet's own capacity-hour MEAN resolved delivered price;
  **(c)** its capacity-hour MEDIAN;
  **(d)** per-CLASS means and medians — a class-grain registry, the natural sibling of the
  existing per-ZONE `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`;
  **(e)** an ENERGY-weighted variant (weighted by each tranche's own screen dispatch) rather
  than capacity-hour weighted.
  Every one reported with its weighting named. **A reporting exercise: nothing minted.**
* **A-2 WHAT EACH GRAIN DOES TO THE ARMED CLASSES.** The static reach of moving **only** the
  anchor, per grain, on `CT_PEAKER` / `CC_REGULAR` / `ST_GAS` / `CC_CHP` / `CT_CHP` — the
  three uncovered cohorts are untouched (F-1). **The two protective faces are pre-registered
  here, before measurement:** C1 `CC_REGULAR`-2024 at **+7.419** of a **±8.00** band
  (0.58 TWh of headroom); C8 `CT_PEAKER`-2023 at **0.2044** against the **0.15** peaker
  budget, passing only on rule 20's conditional provenance+shape route.
* **A-3 THE IDENTITY THE MECHANISM CLAIMS, TESTED DIRECTLY.** `apply_gas_offer_margin`'s own
  contract is *at `fuel == anchor` the reformed offer reduces EXACTLY to the registered band
  multiplier*. Per class per year and per grain: the capacity-hour distribution of
  `|F(t) − anchor|`, and the **cap-weighted absolute offer distortion in $/MWh**,
  `E[|markup_hr × (anchor − F(t))|]`, against the registered multiplier form. **That number
  — not the anchor's distance from any single statistic — is what the owner is choosing
  between**, and it is the packet's primary axis.
* **A-4 CROSS-ISO EXPOSURE, COUNTED NOT TESTED.** For each of the other five ISOs, from
  **committed artifacts only** (`GAS_SERIES_FLAGS`, `GAS_BASIS_DIFFERENTIAL`, each keeper's
  own `run_config.json` gas flags, `SOLVE_FUEL_ARRAY_ISOS`, the by-zone registry): is its
  anchor derived on an ISO-level series while its keeper prices the fleet on a different
  basis? **No other ISO's fleet is built, no other ISO's delivered price is measured, and no
  other ISO's matrix cell is filled** (rule 25). A count of who is exposed, so the owner
  knows the blast radius.

## 5. My prior, stated before the measurement (scored in the finding, against interest)

* **P-1 (A-1 spread).** Over the 2023–2025 window the gas fleet's capacity-hour MEAN resolved
  delivered price exceeds 3.0492 by **+0.35 to +0.85 $/MMBtu**, and its capacity-hour MEDIAN
  sits **within ±0.30** of it. Rationale: CC is ~90 % of MISO gas capacity and miso-215
  measured the CC cohorts near the anchor, with the CT/ST tail pulling only the mean.
* **P-2 (A-3, THE DECISION AXIS).** Under the status quo the cap-weighted absolute offer
  distortion is **largest on `CT_PEAKER`** (its `markup_hr` 3.9059 is the biggest armed) and
  exceeds **$8/MWh in ≥ 2 of 3 years**. Moving to grain **(b)** reduces the `CT_PEAKER`
  distortion by **< 25 %**, because CT's own fuel sits far above even the fleet mean; only the
  per-CLASS grain **(d)** reduces it by **≥ 50 %**. *If (b) reduces CT by ≥ 25 % this
  prediction is wrong and the fleet-grain answer is stronger than I think.*
* **P-3 (A-2 protective faces).** Any grain that RAISES the anchor reduces `CT_PEAKER` screen
  energy in **≥ 2 of 3 years** (F-2's mechanism applied to the armed class) and therefore
  raises the C8 `CT_PEAKER`-2023 forced share above 0.2044. `CC_REGULAR` is nearly
  unaffected — **|screen reach| < 0.5 TWh in every year under every grain** — because its
  `markup_hr` 0.4862 is ~8× smaller than CT's.
* **P-4 (A-4 exposure).** **ERCOT is the LEAST exposed and is arguably NOT exposed at all**:
  `backcast_config` sets `gas_plant_monthly_fuel_pricing=(iso != "ERCOT")`, so ERCOT's fleet
  and its anchor share one basis. **The other four ARE exposed in kind** — 4 of 5.
* **P-5 (which grain the packet favours).** I expect the evidence to favour **(d) per-CLASS**,
  on the ground that the mechanism's identity is a per-tranche statement and the class is the
  grain at which `markup_hr` itself is registered. **The strongest argument against it, which
  the packet must carry:** a per-class anchor multiplied by a per-class `markup_hr` makes the
  fixed margin a product of two class-fitted quantities, which is a rule-21 `[R-DOF]` concern
  even when both are measured.
* **P-6 (process).** **P(the owner rules in-session) ≈ 0** — no owner is present in this
  session. I pre-commit that the fallback is the packet plus a hand-off to the alternative
  queue head, **never an unauthorized arm**, and that I will not treat my own §5 favourite as
  a ruling.

## 6. Kill criteria — what would mean there is nothing to route

* **K-1 — FLEET GRAIN IS FINE.** If BOTH the window capacity-hour mean and median sit within
  **±0.35 $/MMBtu** of 3.0492, the ISO-grain anchor is sound at fleet level and only the CLASS
  grain is at issue ⇒ **narrow the packet to (d) alone** and say so.
* **K-2 — IMMATERIAL.** If the A-3 cap-weighted absolute distortion under the status quo is
  **< $2/MWh on EVERY armed class in every year**, the question does not matter ⇒ **route
  nothing**, record it, and hand the lane to the alternative head.
* **K-3 — NO DOMINANT GRAIN.** If moving to a grain increases the A-3 distortion on more
  class-years than it decreases, that grain is not an improvement; if **no** grain dominates
  the status quo, the packet reports *"no grain dominates"* rather than naming a favourite,
  and P-5 is scored WRONG.
* **K-4 — PROTECTIVE.** If a grain the packet would otherwise favour pushes C1
  `CC_REGULAR`-2024 past ±8.00 or raises C8 `CT_PEAKER`-2023 materially, that consequence is
  reported **on the packet's face**, not in a footnote — the owner rules with the cost in
  view.

## 7. IF the owner rules in-session (and ONLY then)

* **Field:** one MISO-gated `ScenarioConfig` boolean, default **False**, resolving the anchor
  at the ruled grain.
* **Seam, pre-registered:** it resolves where `gas_offer_margin_zonal_anchor` already
  resolves — `data/fleet/assembly.py::bins_to_fleet`, which stamps
  `Generator.offer_margin_anchor` per plant and which `apply_gas_offer_margin` reads via its
  per-tranche `anchors` array. That makes the two **disjoint by construction** (rule 19
  `[R-ONE-MECH]`: they resolve the SAME mechanism's identification point and must never
  stack), and it is **fleet-assembly time**, so a `replay_keeper --set` — which rides the
  generic `prb_overrides` channel applied AFTER `backcast_config` merges the per-ISO curves —
  actually fires. A config-BUILD-time resolution would NOT.
* **Guards:** armed without `gas_offer_net_revenue_margin` is a hard error; armed without its
  resolved map is a hard error (never a silent fallback to the ISO anchor) — mirroring the
  zonal gate's own two guards verbatim.
* **Tests:** flag-off byte identity of the resolved anchors and of `mc`, and the algebraic
  identity at `fuel == anchor`.
* **Matrix:** base row + a cell line in **every** shard (rule 28c);
  `scripts/check_mechanism_matrix.py` must pass.
* **Solve:** `scripts/replay_keeper.py results/calibration/miso213_layering_B --set
  <field>=true --out-dir results/calibration/miso216_<name>_B`, years **2023 2024 2025
  sequential in ONE invocation** (rules 12, 16). **CONTROL is the keeper bundle itself**
  (S-0 inherited, not re-solved).
* **Scorer** on the `_miso213_ab_gates.py` pattern, **committed BEFORE the solve**: S-0
  inherited, S-1 over the RECORDED configs, S-2 liveness (the per-tranche anchors actually
  differ from the ISO scalar, and byte identity at flag-off), K-1…K-6, plus the §4 A-2
  protective faces.
* **Promotion** only if structurally faithful AND no protective gate regresses. **C3a is
  reported, never argued** (rule 1 `[R-STRUCT]`).

## 8. Standing constraints this lane must not violate

* **The miso-214 standing result stands.** 62–70 % of the CT energy the model misses was
  produced by the real market **below the plant's own delivered cost, at the market's own
  price** (41–49 % on the strictest single substitution; 44–60 % paying the better of DA and
  RT) — **not reachable by any offer or price mechanism**. No anchor movement may be
  presented as closing the CT class's gap.
* **DO-NOT-REDO:** `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
  `miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
  `miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (**I — the ZONAL
  grain; A-1's BASIS/CLASS grain is a different question**), `zonal_gas_basis` (K, scoped by
  miso-213), `measured_offer_surface` (R — the within-unit offer-shape family is CLOSED).
* **CLOSED BY MEASUREMENT at miso-214:** a CT commitment bridge or min-load AS floor keyed on
  CAMPD. **CLOSED BY MEASUREMENT at miso-215:** the intermediate-cohort `phys_*` borrowing
  (VALID 9 of 9) and the dual-fuel oil confound.
* **OWNER-COURT, not armed:** the average-vs-marginal delivered-cost convention (miso-212
  §8) — **adjacent to but DISTINCT from** this lane's question, which is where a fixed margin
  is IDENTIFIED, not which cost basis an offer uses; and the D-2 5(i) seam-response object.
* **STILL OPEN, the alternative head:** the South PRICE separation (miso-213 O-4 / the
  miso-211 D-3 object, +$0.16 model vs +$58 measured), independent of the anchor.
* **Rule 25:** PJM, CAISO, NYISO and NEISO share this construction in kind. A-4 **counts**
  their exposure from committed artifacts and fills **no** cell of theirs.

## 9. What ends the session

The OWNER PACKET in `FINDING-miso216-…md` — the question in one paragraph, grains (a)–(e)
side by side on the A-3 distortion axis with their A-2 protective consequences, the grain the
evidence favours **and the strongest argument against it**, and what this lane does under each
possible ruling — plus the probe, its JSON record, the `docs/calibration-log/miso.md` entry,
the §5.4 queue stamp, the MISO shard cell updates and the miso-217 handoff. **Nothing armed,
nothing minted, no solve.**

Next shorthand: **miso-216**.
