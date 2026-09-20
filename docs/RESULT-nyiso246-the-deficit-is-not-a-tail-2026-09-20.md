# RESULT — nyiso-246: the anchored spread-only form is REFUSED on two independent pre-registered stops, the DISPERSION OBJECT IS CONFIRMED AND LARGE, and the cause is an ARMED mechanism pricing scarcity OUT

**Session** nyiso-246 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container, and
zero LP anywhere: no shard was launched**).
**Date** 2026-09-20. **Base** `origin/main` at `83543f3c`.
**PRECOMMIT** `docs/PRECOMMIT-nyiso246-conditional-level-dispersion-2026-09-20.md`, committed and
pushed at **`947de8cd`** before any gated number was computed.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025} — **UNCHANGED.
Nothing armed, promoted or registered. No `ScenarioConfig` field was ever written, so rule 26
`[R-DELETE]` has nothing to revert: the gates fired before any code was added.** NYISO still reads
**CALIBRATED** on its ISO tier (2023–2025), C3c the lone ledgered caveat.
**Predecessor** `docs/RESULT-nyiso245-the-object-is-level-dispersion-not-shape-2026-09-20.md` §5.

> ## HEADLINE
> 1. **THE FORM IS REFUSED ON TWO INDEPENDENT PRE-REGISTERED STOPS, BOTH AT ZERO LP.**
>    **G0 (support)**: the TIGHT window carries **45 / 18 / 68 / 129** hours in 2022/23/24/25 —
>    **1 of 4** years clears the 100-hour bar, against a bar of 3 of 4.
>    **Anchor guard (g3)**: `r_anchor = 0.145`, a **single clean crossing**, against a floor of 0.50.
> 2. **AND THE OBJECT IS CONFIRMED, LARGE AND STATIONARY.** G3a — the book's own cross-unit
>    conditional dispersion — measures **25.845 MMBtu/MWh** (`Δ̂(0.90) − Δ̂(0.50)`, all gens) and
>    **23.513** with every price taker excluded, against a 2.0 bar, and clears in **4 of 4** years.
>    **The FORM is refused; the OBJECT is not.** nyiso-245 named it correctly.
> 3. **THE DEFICIT IS NOT A TAIL — IT IS THE WHOLE DISTRIBUTION ABOVE p15.** The model sits above
>    the book only in the bottom **14.5 %** of ranks and below it at every rank above:
>    `Q_mod − Q_book` = **+8.05** at p10, then **−2.80 / −2.88 / −11.38 / −25.07 / −84.87** at
>    p20 / p50 / p75 / p90 / p99. **92.1 % of the gap sits above p50.** An anchored spread-only
>    graft exists to protect a body the model over-prices; **on NYISO's input-side conditioning
>    there is no such body to protect.**
> 4. **AND THE CAUSE IS AN ARMED MECHANISM, MEASURED.** **88.9 % of the affected stack's MW**
>    (14,923.6 of 16,797.3) carry `offer_markup_hr > 0`. On those rows the armed
>    `gas_offer_net_revenue_margin` term `markup_hr × (anchor − fuel)` is negative in
>    **100.0 % of TIGHT row-hours in every year**, capacity-weighted mean **−$27.07/MWh (2022)**
>    and **−$12.55 (2023)**, p5 **−$161.76** and **−$69.57**. Its per-zone anchor is that year's
>    own gas level — 2022's anchors {5.5865, 6.8765, **8.6565**} against a year mean of
>    **8.6565** — so the term is **antisymmetric about the annual mean by construction**: it adds
>    below the mean and subtracts above it. In the ORDINARY window it is **+$0.58** cap-weighted
>    mean, 56.4 % of row-hours negative — balanced, exactly as designed.
> 5. **SO THE ONE-SENTENCE FINDING: the market prices scarcity INTO its implied offer heat rate
>    and the model prices it OUT.** Book `bottom/G` moves **+2.04 / +11.93 / +27.88 / +96.71**
>    MMBtu/MWh at p50 / p75 / p90 / p99; the model's moves **−0.85 / +0.55 / +2.81 / +11.84**.
> 6. **THE SUCCESSOR IS NAMED AND ITS RE-OPEN CONDITION IS SATISFIED VERBATIM** (§6).
>    **A DECISION IS OWED (§7)** — it re-opens a `K`-verdict keeper mechanism.

---

## 1. WHAT WAS FIXED BEFORE ANY NUMBER EXISTED

The PRECOMMIT (`947de8cd`) fixed the mechanism, both state definitions, the anchor rule with three
STOP-IDENTIFICATION guards and an anti-sweep clause, every gate and every bar, the rule-19
argument, the promotion criteria and the G-DRIFT audit. **Nothing below was computed before that
commit, and no geometry, bar or anchor variant was tried after it.**

The mechanism under design: `ScenarioConfig.nyiso_offer_level_dispersion_anchored`, a NYISO member
of the `miso_offer_spread_anchored` family at **conditional** grain — graft only the measured
above-anchor rise of the book's cross-unit conditional-response vector onto the model's own
affected stack, pinned to the model's own level. **Rule 25 `[R-ISO-SCOPE]`: the method, population
rules, estimator and frozen 199-point grid crossed; `MISO_OFFER_SPREAD_ANCHOR_RANK = 0.875` was
never read.**

---

## 2. G0 — THE SUPPORT STOP, AND WHY THE CONJUNCTION IS NARROW BY STRUCTURE

**Bar (PRECOMMIT §3):** ≥ 100 TIGHT hours in ≥ 3 of 4 years, **and** ≥ 150 gens in BOTH windows.

| year | TIGHT hours | ORDINARY hours | gens in BOTH | TIGHT winter share |
|---|---:|---:|---:|---:|
| 2022 | **45** | 5,578 | 312 | **1.000** |
| 2023 | **18** | 5,174 | 282 | **1.000** |
| 2024 | **68** | 5,181 | 292 | **1.000** |
| 2025 | **129** | 5,460 | 298 | **1.000** |

**Leg 1 FAILS — 1 of 4 years clears 100 hours. Leg 2 PASSES comfortably** (282–312 gens against a
150 bar). So the object is *estimable* on the gens; it is the **hour** support that stops it, and
the gate is honored as written.

**Why the conjunction is narrow, and it is structural rather than incidental.** TIGHT requires the
delivered-gas series **and** net load both at or above their own year's 90th percentile. In NYISO
those are **different seasons**:

| year | gas ≥ p90 hours | winter share of them | net load ≥ p90 hours | summer share of them | overlap | overlap if independent |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 1,488 | 1.000 | 876 | 0.874 | **45** | 148.8 |
| 2023 | 1,416 | 1.000 | 876 | 0.800 | **18** | 141.6 |
| 2024 | 1,488 | 0.984 | 876 | 0.897 | **68** | 148.8 |
| 2025 | 1,488 | 1.000 | 876 | 0.833 | **129** | 148.8 |

**The observed overlap is BELOW the independence expectation in all four years** — the two
coordinates are *negatively* associated. NYISO's high-gas hours are winter; its high-net-load hours
are summer.

> **A REUSABLE FINDING, and the most portable thing in this session: in NYISO a net-load
> percentile is a SUMMER coordinate and does not select the gas-scarcity hours where C3a/C3b
> fail.** The registered cross-ISO `[0.80, 0.90, 0.97]` net-load geometry — carried by five ISOs'
> surface fields and adopted here unchanged precisely to avoid inventing one — is the wrong
> conditioner for a NYISO winter object. Any successor keyed on net-load tightness inherits this.

---

## 3. THE ANCHOR — IDENTIFIED BY THE FROZEN RULE, AND GUARD (g3) FIRES

`r_anchor = max{p ∈ GRID : Q_mod(p) ≥ Q_book(p)}`, both curves built by the identical
construction, pooled 2022–2025.

| population | `r_anchor` | ranks with model ≥ book | sign changes | g1 | g2 | **g3** |
|---|---:|---:|---:|---|---|---|
| all gens | **0.145** | 29 / 199 | **1** | no | no | **FIRES** |
| multi-block only | **0.150** | 30 / 199 | **1** | no | no | **FIRES** |

**`r_anchor ≤ 0.50` ⇒ STOP-IDENTIFICATION** (PRECOMMIT §2). The crossing is **single and clean**
(one sign change, not estimator noise), and it sits in the bottom sixth of the distribution. The
refusal survives excluding every price taker.

`D(p) = Q_mod(p) − Q_book(p)`, MMBtu/MWh, all gens:

| p | 10 | 20 | 25 | 50 | 75 | 90 | 95 | 99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Q_mod` | −8.43 | −4.34 | −3.23 | −0.85 | +0.55 | +2.81 | +4.24 | +11.84 |
| `Q_book` | −16.47 | −1.55 | −0.69 | **+2.04** | **+11.93** | **+27.88** | **+39.71** | **+96.71** |
| **D** | **+8.05** | −2.80 | −2.54 | −2.88 | −11.38 | −25.07 | −35.47 | **−84.87** |

**92.1 % of the (book − model) gap sits above p50; only 73.8 % above p75.** The anchored form is
built for a deficit confined to a tail above an interior anchor — MISO's, where the model was
**+$15 OVER** the eligible book at the median and under only in the top decile. **NYISO's deficit
is the whole distribution above p15**, so the frozen rule correctly returns an anchor at 0.145 —
which is not a spread graft at all but a wholesale replacement of the model's conditional response,
i.e. the LEVEL-replacement form miso-179 already REFUTED in its own ISO and which this PRECOMMIT's
entire design refuses. **The rule did its job: it refused the form rather than letting it be
re-shaped to fit.**

---

## 4. G3 — THE CORPUS. THE OBJECT IS REAL, LARGE AND STATIONARY

The refusal above is of the **form**. The corpus gates say the **object** is not in doubt.

**G3a — `Δ̂(0.90) − Δ̂(0.50)`, bar 2.0 MMBtu/MWh, required on BOTH populations:**

| population | n gen-windows | p50 | p75 | p90 | p95 | p99 | **G3a** |
|---|---:|---:|---:|---:|---:|---:|---:|
| all gens | 1,184 | +2.035 | +11.928 | +27.880 | +39.714 | +96.710 | **25.845 PASS** |
| multi-block only | 762 | +1.595 | +10.804 | +25.108 | +35.112 | +121.024 | **23.513 PASS** |

**G3b — stationarity, bar ≥ 2.0 in ≥ 3 of 4 years: PASS 4 of 4** — 9.443 (2022) / 30.027 (2023) /
20.158 (2024) / 9.392 (2025); multi-block 9.477 / 27.175 / 20.393 / 8.779. *(Per-year vectors are
a check and are never consumed.)*

**G3c — contamination, reported at full magnitude, gating nothing, price takers KEPT** (the
family's own population rules keep them; their weight can only pull δ toward zero):

| year | single-block gen share | single-block capacity share |
|---|---:|---:|
| 2022 | 0.391 | 0.1535 |
| 2023 | 0.369 | 0.1231 |
| 2024 | 0.343 | 0.1015 |
| 2025 | 0.322 | 0.0940 |

Consistent with nyiso-245's independent census (34–43 % of unit-hours, 9.1–12.7 % of capacity), and
the multi-block column above shows every verdict survives excluding them.

**D1 — rank variation: PASS**, spread 0.9999 in all four years.
**G1 / G2 / G4 / G5 / D2 / D3 were NOT evaluated**: G1, D2 and D3 are defined *relative to the
anchor*, and the anchor guard fired, so there is no anchor to define them against. Measuring a
refused mechanism's remaining gates would be looking for a reason to revive it.

---

## 5. THE CAUSE — AN ARMED MECHANISM, AND IT IS ANTISYMMETRIC BY CONSTRUCTION

`gas_offer_net_revenue_margin` (`data/offer_curves.py::apply_gas_offer_margin`) adds
`offer_markup_hr[g] × (anchor − fuel_price[g, t])` — algebraically
`phys × HR_base × fuel(t) + markup_hr × anchor`, the markup held fuel-invariant at an anchor
identified on the training window. **At `fuel == anchor` it is exactly zero; above the anchor it is
negative.**

**It reaches 88.9 % of the affected stack** (327 of 369 tranches, 14,923.6 of 16,797.3 MW), and the
anchors are *that year's own gas level*:

| year | per-zone anchors ($/MMBtu) | TIGHT mean gas | ORDINARY mean gas |
|---|---|---:|---:|
| 2022 | 5.5865 · 6.8765 · **8.6565** | **12.6704** | 7.6395 |
| 2023 | 1.8770 · 1.9970 · **3.3370** | **4.9517** | 3.0207 |

*(2022's top anchor 8.6565 is that year's delivered-gas MEAN to four decimals.)*

The term's distribution over the tagged rows, capacity-weighted, $/MWh:

| year | window | share of row-hours negative | cap-wtd mean | p5 | p25 | p50 | p75 | p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 | **TIGHT** | **1.0000** | **−27.069** | −161.761 | −13.783 | −7.655 | −4.514 | −1.579 |
| 2022 | ORDINARY | 0.5643 | +0.577 | −9.244 | −1.318 | +0.202 | +1.786 | +13.298 |
| 2023 | **TIGHT** | **1.0000** | **−12.553** | −69.566 | −6.550 | −3.292 | −2.113 | −0.709 |
| 2023 | ORDINARY | 0.6874 | −1.941 | −8.975 | −1.922 | −0.414 | +0.504 | — |

So the armed mechanism's **conditional** (TIGHT − ORDINARY) contribution is **−$27.6/MWh in 2022**
and **−$10.6/MWh in 2023**, on 88.9 % of the affected stack. This is not a defect of
implementation: it is exactly what a fuel-invariant margin *means*, and the ORDINARY row shows it
balanced about the mean as designed. **What the new corpus adds is that the measured conduct has
the opposite sign in precisely those hours.**

### 5.1 WHAT THIS DOES *NOT* CLAIM

nyiso-245 measured the model's conditional curve-bottom move at **+$40/MWh** against the market's
+$19/+$26.66, on the **missed-hours** window (residual-selected) in **$/MWh**. This session measures
`Q_mod` on the **input-side TIGHT** window in **MMBtu/MWh**. **These are different statistics on
different windows and neither contradicts the other.** The reconciliation is the normalization: the
model's offers are proportional to delivered gas, so `mc/G` is flat by construction and its dollar
response (~`HR × ΔG` ≈ $40) disappears in implied-heat-rate space, leaving only the non-proportional
parts — of which the armed margin term is the large one, and it is negative. What this session
establishes is narrower and is exactly what guard (g3) tests: **on the mechanism's own input-side
conditioning the anchored form's premise does not hold.**

**Stated limits.** The TIGHT window is thin — 45 / 18 / 68 / 129 hours, and **2023's 18 hours is
genuinely marginal**, which is what G0 exists to catch and why it stopped the mechanism rather than
being argued around. The per-unit medians behind δ rest on 282–312 gens and thousands of unit-hours,
so the gen-side support is not the weak leg.

---

## 6. THE SUCCESSOR — NAMED, WITH ITS RE-OPEN CONDITION SATISFIED VERBATIM

`gas_offer_net_revenue_margin` is NYISO cell **`K`**, and **nyiso-167 declined to re-open it with an
explicit condition**: *"…a per-year re-anchor would be a derivation-vs-dispatch basis mismatch with
the residual as its only motive (rule 1). **DO-NOT-REDO absent new measured NYISO offer data.**"*

**The NYISO MIS P-27 genbids corpus is that data** — landed by nyiso-245, extended here to a
conditional grain — and it satisfies the condition on its own terms. Three things distinguish this
from what nyiso-167 adjudicated:

1. **It is a different question.** nyiso-167 refused a **per-year RE-ANCHOR**. This is the
   **WITHIN-year conditional antisymmetry** of the existing anchor — the mechanism subtracting in
   above-mean-gas hours — which that session did not test.
2. **The motive is measured conduct, not a residual.** The book's `bottom/G` RISES in tight hours
   (+2.04 at p50, +27.88 at p90) where the armed term is negative in 100 % of row-hours. Rule 1's
   prohibition is on selecting a mechanism because the residual moved; this is a sign disagreement
   with a measured offer book, and no price error enters the identification path.
3. **"Remove it" is already refuted and is NOT the successor.** nyiso-195 KILLED removing the
   CC_REGULAR econ markup on the loading-shape gate (80–90 % share 33.0 → 33.5 against CAMPD 16.5;
   C1-2024 CC_REGULAR +3.68 → +4.34 TWh). The live question is the **fuel-invariance limb**, not
   the margin form.

**Not designed here, deliberately.** It re-opens a `K`-verdict keeper mechanism at the core of the
offer path, and a form chosen in the same session that found the evidence — with no PRECOMMIT and
no owner ruling — is exactly the selection discipline this lane exists to prevent. It needs its own
PRECOMMIT, its own identification and its own gates.

**A second successor, also named and also not folded in** (PRECOMMIT §0.2): the keeper's delivered
gas is `annual price × monthly seasonal shape` — smooth, 2022 running $6.239 → $12.745 — where the
real winter citygate is spiky at daily grain. That is the NYISO analogue of
`caiso_citygate_spot_coverage` / `miso_winter_citygate_daily`. It cannot produce the measured
object on its own (a common series moves every unit together, and the book says three quarters of
capacity moves little while a quarter moves enormously), but it compounds with the object above.

**2025 SUMMER and the G2 HYDRO LOSS remain separate open objects and were not touched.**

---

## 7. THE DECISION OWED — AND WHAT THIS SESSION DID NOT SPEND

**Zero LP was spent. No shard was launched, so rule 33 `[R-SHARD-ARCHIVE]` has nothing to sweep and
rule 34 `[R-SHARD-PROMOTABLE]` nothing to retrieve.** Rule 15 `[R-DASHBOARD]`: **no run completed,
so there is nothing to register** — the keeper's dashboard entry is untouched and correct. Rule 31
`[R-RETAIN]`: **nothing was deleted**; the derived artifact and both probe records are committed, so
a successor re-derives nothing. Rule 26 `[R-DELETE]`: **no `ScenarioConfig` field or applier was
ever written** — the gates fired first — so there is no default-off knob left behind.

**The question for the owner:** re-opening `gas_offer_net_revenue_margin`'s fuel-invariance limb
means re-examining an armed mechanism on the current keeper, whose cell is `K` and which three
prior sessions (nyiso-167, -182, -195) each declined to move. The measured case for doing it is
§5; the case against is that its margin form is separately validated and that removing it is
already refuted. **A lane should not take that decision on its own evidence alone, so it is put
here rather than acted on.**

## 8. ARTIFACTS

| path | what |
|---|---|
| `docs/PRECOMMIT-nyiso246-conditional-level-dispersion-2026-09-20.md` | the pre-registration, at `947de8cd` |
| `scripts/data/derive_nyiso_offer_level_dispersion.py` | the derive (self-test: T-1 recovery, T-2 level invariance, T-3 price taker) |
| `data/raw/_validation-source/nyiso_offer_level_dispersion.json` | the measured vector, sha256 `1ad26b2f21e3654c5cb1f25f66c0715ebeff601299624b4dd85de05d95e2f1db` |
| `scripts/probes/nyiso246_dispersion_phase0.py` → `results/calibration/_nyiso246_dispersion_phase0.json` | G0 anatomy, `Q_mod`, D1 |
| `scripts/probes/nyiso246_margin_sign_phase0.py` → `results/calibration/_nyiso246_margin_sign_phase0.json` | the armed margin's conditional contribution |
| `scripts/probes/_nyiso245_fleet_cache.py` | repaired: now writes the `gas_<year>.npy` pass the committed derive names |
