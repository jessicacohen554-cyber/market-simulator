# PRE-REGISTRATION — miso-134: the `CT_PEAKER` July-night ORDER screen

**Session:** miso-134, 2026-08-05, branch `claude/miso-134-calibration-ys5txh`,
off `origin/main` at `57120845`.

**Keeper at entry:** `2026-08-05-miso-132b-cc-committed` (bundle
`results/calibration/miso132_ccmin_B`), **NOT-YET**, sole FAIL C7 `COAL_PRB`
2025 `cv_ratio` 0.338 vs the 0.50 gate, ledgered caveats 2/3 {C3a, C3c}.

**Charter lane:** (a) — the NEW-EVIDENCE ORDER-DIMENSION LEVER SCREEN on the
`CT_PEAKER` overnight row of `FINDING-miso133-overnight-identity-basis-2026-08-05.md`
§4 (model − measured **−854 / −691 / −666 MW** at July night h0–5, grid-delivered
both sides). The row is brand-new: it was invisible until miso-133 lifted the
miso-127-parallel §7a class-grain-gas blocker, and it is un-adjudicated.

**Rule 22 `[R-HOLDOUT]`:** 2023–2025 ONLY. MISO holds no marker; no 2022 / 2019 /
H1-2026 year is solved, scored or read at any point in this session.

**This document is pushed BEFORE any adjudicating statistic is computed.**

---

## §0. FULL DISCLOSURE — every number already in hand before this PREREG

Per the miso-131 §0 duty, everything measured or read before pre-registration,
so no result below can be back-fitted to a number already seen. All of it comes
from committed artifacts (the keeper's own `run_config.json`, the keeper's
`calibration_attestation.json`, a frozen rule-23 reference CSV, the matrix and
the calibration log) — **nothing here is a measurement of the object.**

1. Keeper `offer_curve_by_group["CT_PEAKER"]` =
   `{committed 1.025, econ_low 1.0, econ_high 1.0, peak 4.0, econ_low_share 0.526,
   pct_peaking 7.0, phys_committed 1.025, phys_econ_low 0.687, phys_econ_high 0.691,
   phys_peak 1.0}`.
   Keeper `offer_curve_by_group["CT_INTERMEDIATE"]` =
   `{committed 1.0, econ_low 1.0, econ_high 1.2, peak 3.0, econ_low_share 0.5,
   pct_peaking 5.0}` — **no `phys_*` keys**, i.e. rule-24-neutral under the margin form.
2. `data/raw/reference/miso_campd_marginal_hr_summary.csv`, `CT_PEAKER` row:
   `base_hr` 12.372, `n_units` **249**, `avg_committed_p50` 1.025,
   `marg_econ_low_p50` **0.687** (p25 0.640, p75 0.779),
   `marg_econ_high_p50` **0.691** (p25 0.645, p75 0.784).
   The keeper's `phys_econ_low`/`phys_econ_high` are exactly these two values.
3. Keeper `gas_offer_net_revenue_margin = true`, `gas_offer_margin_anchor = 3.0492`
   $/MMBtu; `gas_offer_margin_zonal_anchor = false`. Resolved gas prices
   2.54 / 2.19 / 3.52 $/MMBtu (2023/24/25).
4. Arithmetic on (1)–(3), class-cap-weighted, stated in advance so it cannot be
   presented later as a finding: the `CT_PEAKER` econ band carries a residual
   above-physical markup of `(1.0 − 0.687) × HR_base` heat-rate units, i.e.
   ≈ **$11.8/MWh** at `base_hr` 12.372 and ≈ **$11.5/MWh** at the
   `measured_ct_heat_rates` plant-grain 12.0351, fuel-invariant by the margin
   form's construction. **This is an input arithmetic, not the object** — the
   object is what that markup does to the July-night merit ORDER, which is
   unmeasured.
5. Keeper DOF ledger (`calibration_attestation.json`): `offer_curve_by_group`
   identification = **`residual`**, lineage `>=39 solves`; `n_entries` 29,
   **`n_residual` 2** (the other is `offer_curve_smoothing`).
6. Keeper arms, simultaneously: `tranche_startup_amortization = true`,
   `tranche_startup_measured_runs = true` (v3 CAMPD horizon,
   `campd_ct_run_lengths_MISO.csv`), `tranche_startup_conditional_runs = true`
   (v4 band ratios, `campd_ct_run_bands_MISO.csv`) — both ledgered
   **measured-physical**; and `measured_ct_heat_rates = true` (K at MISO,
   miso-117b, plant grain 12.3720 → 12.0351).
7. Keeper D-2, `CT_PEAKER × reliability_floor`: forced 1.7344 / 1.6876 / 1.6618 TWh
   of class totals 12.5666 / 17.1183 / 15.5073 TWh ⇒ share **0.138 / 0.099 / 0.107**,
   under the 0.15 peaker cap; the limb is the h14-21 peak window, **not** overnight.
8. miso-133 §6 (this session's own charter constraint): July-night keeper dispatch
   is **6.1 %** of assembled `CT_PEAKER` (2025 headroom 20,932 MW, idle share
   0.939) and 16.9 % of `ST_GAS`; ~41 GW idle non-coal gas against a 3.2 GW
   shortfall. miso-133 §4 shortfalls as above; transform-consistent `CT_PEAKER`
   bench coverage 0.846 / 0.867 / 0.813.
9. miso-130 §(a): keeper July-night price floor p10 = **26.11 / 20.67 / 31.42**
   $/MWh; July-night price sits +$7.0–8.7 above actual in all three years.
10. Matrix cells read (rule 28(a) DO-NOT-REDO check): `offer_curve_by_group`
    **KKKKKK**, `gas_offer_net_revenue_margin` **KKKKKK**,
    `tranche_startup_amortization` **GGKKKK** (MISO **K**),
    `measured_ct_heat_rates` **IKKKKK** (MISO **K**),
    `gas_offer_margin_zonal_anchor` **K.IIK.** (MISO **I**).
    **No cell adjudicates the `CT_PEAKER` econ-band LEVEL at MISO.**
    `backcast_config.py`'s MISO block calls the CT econ bands
    "measurement-AFFIRMED neutral" — an assertion about the band's **RAMP**
    (flat, which the measured 0.687 → 0.691 confirms), **not** about its LEVEL.
11. Cross-ISO precedent, cited and **NOT transferred** (rule 25): CAISO refused
    `tranche_startup_amortization` U → G partly on rule 19, having measured that
    its `CT_PEAKER` net-revenue margin ($8.42–22.69/MWh) is 2.19–7.86× the
    $3.85/MWh start recovery measured on `campd_ct_run_lengths_CAISO.csv`. MISO's
    own numbers are unmeasured and this PREREG does not assume CAISO's.

## §1. The object

**What prices MISO's peakers out of the July night.** The `CT_PEAKER` econ band
is offered at a **residual-identified** multiplier of 1.0 × base heat rate while
the class's own measured incremental burn is 0.687–0.691 × base heat rate
(n = 249 units, IQR 0.640–0.779). Under the armed `gas_offer_net_revenue_margin`
form the gap is a fuel-invariant $/MWh net-revenue margin added to the **base**
marginal cost, so it prices the class in **both** P0 and P1.

It is an ORDER object by construction and therefore admissible under the
miso-133 §6 DO-NOT: it changes **the price at which existing CT capability enters
the merit order** and adds no capability, no availability, no must-offer, no
commitment bridge, no reserve gating and no RA-style floor. The capability is
already assembled and 93.9 % idle; only its price is in question.

It is the last residual-identified band level in MISO's overnight gas merit
order — the same class of object miso-132(b) closed for the CC committed band
(1.20/0.92 → measured 1.005) and miso-117b closed for the CT base heat rate.

## §2. Two-sided prior (declared before measurement)

Genuinely two-sided in **both** dimensions, and the session commits to reporting
whichever fires:

* **Size.** ≈$11.5/MWh is large against a $20–31/MWh July-night floor, which
  argues the swap unlocks far MORE than the 666–854 MW shortfall — an over-run
  that would break C1 and refuse the arm. It is equally possible the cheapest
  idle CT sits more than $11.5 above the night price (the class base HR is
  12.0–12.4 against CC's 7.4, a ~1.6× fuel-cost handicap), in which case the
  full swap is **INERT** and the lane dies here, the miso-131 outcome.
* **Direction on C7.** Newly-in-merit CT displaces coal only if it prices BELOW
  the marginal `COAL_PRB` block at those hours. If it instead lands above PRB
  and below the CC block, it displaces `CC_REGULAR` — which miso-133 §4 shows is
  **also** short overnight (−1,367/−779/−1,357 MW) — and C7 `COAL_PRB` does not
  move at all. Both are live and the screen tests it explicitly (S-6).

The session's expectation, stated so it can be falsified: **KILL is at least as
likely as PASS.** Three MISO lanes in a row (miso-131, miso-132(a), miso-133)
have died at a pre-registered pre-check, and this screen is built the same way.

## §3. Statistics

All computed at HEAD from the **keeper's own `run_config.json`** (the miso-116 §7
discipline — the probe builds its fleet from the keeper's config, never a default
`ScenarioConfig`), against the keeper's own committed sidecars
`results/calibration/miso132_ccmin_B/hourly/{system,class_hourly}_<year>.parquet`,
pass **P1**. **NO LP IS SOLVED.** July night = **month 7, hours-of-day 0–5**,
the miso-130/133 window verbatim.

**S-0 — construction validity (GATING).**
 (a) assembled `CT_PEAKER`-class capacity (both offer-curve cohorts) reproduces
     the keeper's published assembled basis (miso-133 §6: 2025 headroom
     20,932 MW at idle share 0.939 ⇒ ≈22,292 MW) to **±2 %**;
 (b) cap-weighted plant-grain base heat rate reproduces the published
     **12.0351** (miso-117b, `measured_ct_heat_rates` armed) to **3 decimals**.
 FAIL on either ⇒ **NO VERDICT** — the probe is not keeper-matched and nothing
 below may be quoted.

**S-1 — the markup census.** Per assembled CT tranche, decompose the July-night
offer into: physical burn `phys × HR_base × fuel(t)`; residual net-revenue margin
`(mult − phys) × HR_base × anchor`; VOM; and — reported **separately**, since it
is a P1 bid adder and not part of the base offer — the startup amortization.
Report cap-weighted $/MWh of each and the MW share of CT capacity carrying a
positive markup, per year, at both grains of S-5.

**S-2 — THE SLACK / REACHABILITY MEASUREMENT (the pre-registered bar).** This is
the miso-132(a)/133 duty discharged before anything is built: measure the
constraint's slack on the incumbent's own dispatch.
Define, per year, over the July-night hours and each tranche's own zone price
from `system_<year>.parquet`:

    R(Δ)  =  mean over July-night hours of
             Σ_tranches  cap_MW · 1[ offer_$/MWh − Δ  ≤  zone_price(t) ]
             −  the same quantity at Δ = 0

i.e. the MW of CT capacity that comes into merit when Δ $/MWh is removed from its
offer. Report R(Δ) on a grid Δ ∈ {0, 1, 2, …, Δ_max} where **Δ_max is the FULL
residual markup** of the measured swap (econ 1.0 → 0.687/0.691) — not a chosen
value.

**BAR:**
* **PASS (lane licensed)** iff `R(Δ_max) ≥ shortfall` in **≥ 2 of 3** years,
  shortfall = **854 / 691 / 666 MW** (miso-133 §4, matched-set; the class-wide
  figure is larger, so this bar is conservative against the lane).
* **KILL (INERT — lane closed, no arm)** iff `R(Δ_max) < shortfall` in ≥ 2 of 3 years.

R(Δ) is a **price-taking** bound: real entering supply pushes the clearing price
DOWN, so the LP would clear strictly less than R. The bound therefore
**overstates** the lever, and a KILL on it is conservative in the direction that
matters — the identical construction discipline as miso-131's n→∞ bound.

**S-3 — the C1 counter-risk (annual reachability).** The same `R(Δ_max)`
evaluated over **all 8760 hours**, converted to TWh/yr of newly-in-merit CT
energy at price-taking, against the keeper's own C1 `CT_PEAKER` model-vs-actual
headroom. **Pre-registered refusal:** if the annual price-taking upper bound
would carry `CT_PEAKER` past its C1 band in ≥ 2 of 3 years, the arm is
**REFUSED even on an S-2 PASS** (rule 1 — a mechanism must be right in every
hour, not only in the hours it was recruited for).

**S-4 — the identification comparison (DECLARED UNGATED, descriptive).** The S-1
residual margin against MISO's OWN measured start recovery on the same tranches,
`startup_cost / fast_start_run_hours` from `campd_ct_run_lengths_MISO.csv`,
cap-weighted. Reports whether a residual-identified margin duplicates a
separately-armed **measured** mechanism, and by what multiple. **No verdict is
taken from it** (the miso-133 S-4 discipline: descriptive statistics do not move
cells and nothing is sized on it).

**S-5 — two grains (the miso-126 duty).** S-1/S-2 computed at (1) **tranche/plant
grain** — each tranche against its own zone's hourly price, the grain the LP
actually dispatches at — and (2) **class grain** — the cap-weighted class ladder
against the load-weighted ISO price. Both reported. On disagreement the **plant
grain governs** and the disagreement is reported, not buried.

**S-6 — the displacement target (gates the C7 CLAIM, not the arm).** For the CT
capacity that enters at Δ_max, compare its offer against the assembled `COAL_PRB`
econ ladder at the same hours. If the entering CT prices ABOVE the marginal PRB
block, the lever cannot displace coal and **the C7 `COAL_PRB` claim fails** even
on an S-2 PASS. The arm may still be licensed on rule-14 grounds alone (an
accurate input is armed for its own sake, never for its residual) — but this
PREREG forbids claiming C7 relief that S-6 does not support.

## §4. Decision rule

1. S-0 FAIL ⇒ NO VERDICT; session reports the construction failure and stops.
2. S-2 KILL ⇒ the `CT_PEAKER` order lane is **INERT**, closed with cause; the
   matrix cell note and the §5.4 queue stamp record it; **no arm, no field, no
   solve, keeper unchanged.**
3. S-2 PASS **and** S-3 refusal ⇒ arm **REFUSED**; recorded with the same finality.
4. S-2 PASS **and** S-3 clear ⇒ the arm of §5 is **LICENSED**, and only then.
5. The C7 claim is admissible only with S-6 support, independent of 1–4.

## §5. The arm, if licensed — fixed in advance

The **only** admissible arm: `offer_curve_by_group` `econ_low` / `econ_high` for
**both** CT cohorts set to the class's own measured
`marg_econ_low_p50` / `marg_econ_high_p50` = **0.687 / 0.691**, with matching
`phys_econ_low` / `phys_econ_high` so the markup goes to exactly zero on that
band. Armed via `replay_keeper --set offer_curve_by_group` with the JSON
generated from the control's own `run_config.json` (the miso-132(b) §5 route —
`--offer-curve-json` cannot carry `CT_INTERMEDIATE`, a routing key outside
`fossil_classes`). No other band, no other class, no other field.

Solve posture (rules 12/16): same-HEAD **zero-delta control first**, then one
`replay_keeper --set` invocation for the arm; `--years 2023 2024 2025` in a
single invocation each; arms sequential.

Arm-stage gates, all pre-registered here:
* **A1** control reproduces the incumbent to **0.0 MW** at class-hour grain.
* **A2** **C1 16/16.**
* **A3** `COAL_BIT` **no overshoot.**
* **A4** **D-4 off-window binding 0.000** on every limb.
* **A5** **LOYO within 2023–2025** — the verdict may not rest on a single year.
* **A6** determination may not regress; the C7 `COAL_PRB` `cv_ratio` direction is
  reported **whatever it is** and the accurate input is **NOT reverted** if it
  worsens (rules 1/14, the miso-117b and miso-132(b) precedent).

## §6. Kills

* **K1** Nothing is sized on any Δ from a solve. No `ScenarioConfig` field is
  created, and no arm built, before S-2 returns PASS.
* **K2** S-0 failure ⇒ NO VERDICT (§4.1).
* **K3** S-2 KILL ⇒ lane closed (§4.2). Declared as the at-least-as-likely branch.
* **K4** S-3 refusal ⇒ arm refused (§4.3).
* **K5** **NO TUNED Δ.** The full measured swap is the only admissible arm. Any
  intermediate Δ chosen because it lands on the shortfall is the forbidden fitted
  path (rules 1/24) and is refused in advance, whatever S-2 returns.
* **K6** **BOTH CT COHORTS MOVE TOGETHER** (`CT_PEAKER` and the
  `ct_intermediate_split`-routed `CT_INTERMEDIATE`) — the miso-132(b) rule-19
  discipline: moving only the cheaper or dearer half would choose the direction.
  If they cannot both be moved on one measurand, the arm is refused.
* **K7** **NO RE-DERIVE** of `miso_campd_marginal_hr_summary.csv` or any
  reference artifact (rule 23 `[R-FROZEN-DERIVE]`) — consumed exactly as committed.
* **K8** **No adjudicated cell is re-opened** (rule 28(a)): this touches neither
  `offer_curve_smoothing_n` (INERT, miso-131), nor reserve online-gating
  (miso-132(a)), nor the seam classes (SPENT, miso-114/123), nor take-or-pay
  (miso-127b), nor the within-band slope (miso-129), nor trough marginal-unit
  **VOLUME** (REFUSED, miso-115 — this object is miso-115 §4's surviving
  `CT_PEAKER` **PRICING** item, which stands), nor `gas_offer_margin_zonal_anchor`
  (MISO **I** — this arm does **not** touch the anchor, only the band multiplier).
* **K9** Rule 22: 2023–2025 only, in every statistic and every solve.
* **K10** The `CT_CHP`/`ST_CHP` S-2 residuals of miso-133 §3b are **out of scope**
  (charter lane (c), chartered only if (a) and (b) are both refused).

## §7. Duties this session discharges regardless of outcome

Rule 15 (register every run produced — none if no LP is solved, the
miso-131/132(a)/133 precedent), rule 28(b) (stamp the tested cell + the §5.4
queue stamp in the same session, rejection included), rule 22, rules 19/21/24/25
throughout, rule 27 blob verification on every push.
