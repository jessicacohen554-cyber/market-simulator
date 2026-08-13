# PREREG — miso-156: decompose MISO's C3a-2025 mean-LMP miss into **IDENTITY / COST-LEVEL / ABOVE-COST**, on an exactly additive identity, with the floors READ

**Session** miso-156 · **ISO** MISO · **Date** 2026-08-13 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED at
pre-registration** · **Model** `claude-opus-5` (rule 27 `[R-PUSH]`: this scope
may write `src/market_sim/`, so Opus/Fable only).

**This document is pushed and blob-verified against the FETCHED remote ref
BEFORE any adjudicating statistic is computed** (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 ONLY. MISO holds **NEITHER**
`complete` NOR `final`. No holdout year is read, solved, scored or registered
anywhere in this session. Any run produced covers all three train years in ONE
bundle (rule 16 `[R-ALLYEARS]`).

---

## 0. The object, and why the lane can now ask this question honestly

The target (matrix §5.4, owner directive 2026-08-06) is MISO's 2024/2025
**mean-LMP LEVEL miss**: C3a-2025 **−15.6 %**, C3b-2025 NRMSE **0.212**, the
keeper's two load-bearing FAILs.

Three prior sessions narrowed it and one closed the instrument:

* **miso-152** localized it: 2025's miss is **JUNE and JULY** (−27.9 % / −30.9 %),
  17 % of hours carrying **46 %** of the annual gap, and the model's summer p99
  and max sit **BELOW its own rest-of-year** p99 and max. **The model forms no
  summer peak at all.**
* **miso-153** identified the peak price-setter: **`CT_PEAKER`**, in
  40.0 / 42.6 / **66.0 %** of top-200 zone-hours.
* **miso-155** closed the volume instrument: with the exact P0 read and the
  reliability floors read, CT volumes measure to **−0.89 / −0.26 / −0.52 %**.
  **There is no unexplained CT volume residual left to attribute to the offer
  level.**

And the market's own referee says MISO clears essentially **at cost**: the
Potomac Economics MISO IMM measures the system price-cost mark-up at
**+3.0 % (2023)** and **−2.5 % (2024)** with a de-minimis output gap
(`data/raw/som-competitive-conduct/som_competitive_conduct.csv`, rows 12–13 /
24–25).

Put together: **a −15.6 % level miss on a market that clears at cost, with the
right volumes, cannot be an offer-markup deficiency.** It is a statement about
either *which unit is marginal* or *what that unit costs* — or about hours whose
price no unit's cost explains. **This document decomposes exactly that, and
takes no lever.**

### 0.1 What I inspected BEFORE writing this document (disclosure)

Plumbing, published numbers, and mechanism definitions — **no gas price series,
no measured LMP series, no model price statistic beyond the already-published
C3a**:

* `scripts/calibration_verdict.py::score_price_mean` (C3a's construction: system
  **load-weighted** mean LMP vs the `rt_lw` bench, ±10 % target).
* `scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
  (committed artifacts only, **no solve**), which reproduces the published
  determination: **NOT-YET**, fail set {C3a, C3b}, C3a-2025 **−15.6 %**,
  C3b-2025 **0.212**, C3c ledgered 1/1, C6 PASS, C8 PASS.
* `frontend/data/backcast/bench/MISO/<year>.json.gz` → `bench.avgLMP` **keys and
  structure**, and the `rt_lw` annual values **32.85 / 32.30 / 45.46 $/MWh**
  (the scorer's own denominators; the C3a percentages already imply them).
* `hourly/system_<year>.parquet`, `class_hourly_*`, `reserve_family_*` schemas.
* `scripts/probes/_miso134_ct_night_order_screen.py::build_year` (returns
  `fuel_prices` **(n_gen, T)** and `mc_base`), `_miso155_p0_exact_instrument.py`
  (`read_solve_floor`, `reconstruct_p1_floorsfirst`), and
  `results/calibration/_miso155_p0_exact_instrument.json` `FLOOR_source` block.
* `scripts/run_calibration.py:3307-3372` — the production reliability-floor
  application, and `market_sim.model.transmission.inject_reliability_floor`.
* The keeper's `run_config.json` armed-field census, and the **definitions**
  (docstrings/comments, not data) of `miso_zonal_gas_basis`,
  `miso_winter_citygate_daily`, `gas_hub_basis_overlay`
  (`data/fuel/hubs.py::apply_hub_basis_overlay`).
* `data/raw/gas_basis_by_iso_month.csv` — **column names and per-ISO row counts
  only** (MISO 135 rows). **I did not read a single MISO basis value.**

**Not inspected:** any gas price value, any measured LMP series, any model
implied heat rate, any decomposition share. The §5 priors are reasoned from the
published localization and the mechanism, not read off an answer.

---

## 1. What is established and is NOT re-derived

* miso-152's monthly localization and the summer-distribution result (§0).
* miso-153's D-3 peak-setter share and D-1 cushion; its **CLOSED** across-unit
  dispersion object (three grounds) — **NOT re-opened**.
* miso-155's CT volume result, the exact-P0 markup, and **the instrument defect**:
  `_miso134.build_year` **stops before the reliability-floor registry**, so any
  probe scoring a floored class must obtain the floors elsewhere.
* **DO-NOT-REDO (rule 28(a)), none re-tested here:** the within-unit offer-shape
  family (`measured_offer_surface` **R**), the across-unit dispersion object
  (CLOSED), the base-band inversion (IMMATERIAL), the D-4 all-hours window flag
  (WITHDRAWN), CT min-run/min-down (ABSENT, 733/733 at 0.0),
  `cc_nameplate_summer_derate` (wrong direction), `gas_commitment_bridge`
  (cannot bind), C7 `COAL_PRB` (owner-DEPRIORITIZED).
* **The CT offer-LEVEL lever is NOT re-opened on volume grounds** (miso-155 §8).

---

## 2. A constraint this session discovered and must declare up front

**`results/calibration/*/floors/` is GITIGNORED** (`.gitignore:443`). No
committed bundle — keeper or control — carries `floors/<year>_P1.npz`. miso-155's
mandated instrument correction ("read the floors from the bundle") is therefore
**not reproducible from the repository** in a fresh checkout.

This session does **not** re-solve to recover them. It closes the gap the
durable way: **call the production floor engine**
(`model.transmission.inject_reliability_floor`, driven by
`RELIABILITY_FLOOR_REGISTRY` + `apply_reliability_floor_overrides` +
`drop_drag_owned_reliability_specs` + `drop_obligation_owned_reliability_specs`,
exactly as `run_calibration.py:3307-3372` composes them) on the probe's own
assembled arrays — the same repair, sourced from committed inputs instead of a
gitignored artifact.

**It is gated, not assumed** — validity gate **V2** (§7) requires the rebuilt
floors to reproduce miso-155's committed `FLOOR_source` figures. If they do not,
**S-FLOORBLIND** fires and no adjudicating statistic is quoted.

---

## 3. The decomposition — an EXACTLY ADDITIVE identity, fixed here before measurement

For each carry zone `z` (the 6 carry zones; `MISO_external*` import nodes
excluded) and hour `h`:

Let `P_mod` be the model's P1 LMP (`hourly/system_<year>.parquet`), `P_act` the
measured RT hub LMP on the scorer's own basis, `G_mod` the model's own delivered
gas price at its marginal tranche, `G_act` the measured MISO delivered gas price,
and `V` a fixed gas VOM reference (the model's capacity-weighted gas VOM,
computed from its own arrays — a constant, not a free parameter).

Define implied heat rates `IHR ≡ (P − V) / G`, and let `HRmax` be the **maximum
heat rate among the model's own available gas tranches in that hour** — the
fleet's physical cost ceiling.

**Channel (iii) — ABOVE-COST.** The part of the actual price no MISO gas unit
could charge at cost:

    Δ₃ = max(0, P_act − (HRmax · G_act + V))

**Channel (ii) — COST LEVEL (fuel).** Revalue the model's *own* marginal heat
rate at the measured fuel price:

    Δ₂ = IHR_mod · (G_act − G_mod)

**Channel (i) — MARGINAL-UNIT IDENTITY.** At the measured fuel price, how much
of the remaining gap is the market being on a *different (worse) unit* than the
model's marginal one:

    Δ₁ = G_act · (IHR*_act − IHR_mod),   IHR*_act ≡ (P_act − Δ₃ − V) / G_act

**These sum exactly:** `Δ₁ + Δ₂ + Δ₃ ≡ P_act − P_mod`, identically, hour by hour.
The identity is asserted elementwise to 1e-9 as gate **V3**; it is arithmetic,
not an approximation, so a failure is a coding error.

**Reported at three grains, all three years:** annual (the C3a grain — this is
the adjudicating one), June+July (miso-152's concentration), and the top-200
model-demand hours (miso-153's window, for continuity).

### 3.1 Interpreting Δ₁ — a second, independent measurement

Δ₁ says the market's marginal unit is more expensive than the model's. It does
**not** say whether such a unit exists. So Δ₁ is qualified by a census fixed here:

* the **percentile** of `IHR*_act` within the model's own available gas
  heat-rate distribution in that hour, and
* the **class** (`CT_PEAKER` / `CC_REGULAR` / `ST_GAS` / …) of the model tranche
  at that heat rate, against the model's actual marginal class.

If `IHR*_act` lands **inside** the model's own distribution, Δ₁ is a
**misidentification** the model's own fleet could fix. If it lands **above**
the distribution but below `HRmax` only because `HRmax` is one outlier tranche,
that is disclosed as such.

### 3.2 Two measured `G_act`, and the primary is declared now

* **PRIMARY — hub-month spot:** `henry_hub_monthly.csv` + the MISO rows of
  `gas_basis_by_iso_month.csv`. This is the *marginal opportunity cost* of gas,
  the quantity a cost-based offer is built from.
* **COUNTER-MEASUREMENT — F923 receipts:** the model's own per-plant delivered
  series (i.e. `G_mod` itself, which is F923-based). Reported alongside so the
  reader sees how much of Δ₂ is "spot vs receipts" rather than "wrong level".

**Both are reported at full magnitude in every branch.** Declaring the primary
now is what stops a post-hoc basis choice.

---

## 4. Rule 19 `[R-ONE-MECH]` — what already owns each channel, enumerated before any lever

**Channel (ii), delivered gas:**

1. `miso_zonal_gas_basis` (**ARMED**) — the measured per-zone EIA delivered
   basis vs Henry Hub, added as a **mean-zero, capacity-weighted spread**. It
   owns the **north/south gradient** and by construction **cannot move the
   ISO-wide level**.
2. `miso_winter_citygate_daily` (**ARMED**) — replaces the national within-month
   daily shape with the measured Chicago Citygate daily shape, **Dec/Jan/Feb
   only**, **mean-preserving within month**. Owns the *winter daily shape*; it
   cannot move a June/July level.
3. `gas_offer_margin_anchor = 3.0492` with `gas_offer_net_revenue_margin`
   (**ARMED**) — the fixed $/MMBtu margin at the ISO anchor.
4. `coal_tranche_{1,2,3}_fuel_passthrough` + `coal_prb_contract_passthrough`
   — the coal side of the same delivered-fuel question.

**So MISO's ISO-wide gas LEVEL is owned by nothing but the F923/EIA-923 series
itself.** `gas_hub_basis_overlay` (matrix **U**) is the queue candidate for it.

**A rule 14 `[R-ACCURATE]` hazard in that candidate, stated ex ante so a
favourable Δ₂ cannot launder it.** `apply_hub_basis_overlay` **REPLACES** every
gas generator's fuel price with one ISO-wide hub-month series, *"superseding
both the ISO-month EIA-923 series and the per-plant F923 overwrite"*
(`hubs.py:1268-1272`). That is right for NEISO — two plants report Schedule-5
receipts — but for MISO it would **destroy a per-plant measured input the model
demonstrably reproduces faithfully**: miso-153 Ground 3 measured across-plant
delivered-gas dispersion at **5.321 → 3.593 → 3.413 $/MMBtu** against an F923
source of **5.657 → 3.748 → 3.679**. Arming it as written would trade a faithful
measurement for a flat one. **If Δ₂ dominates, the admissible lever is a level
reconciliation that PRESERVES per-plant dispersion — not this overlay as
constructed** — and that is a separate charter, not this session's.

**Channel (i), marginal-unit identity at the peak:** `measured_ramp_capability`
and `ramp_envelopes` are both **U**. Nothing in the keeper constrains
inter-hour ramp. `miso_measured_reserve_requirements` /
`miso_midwest_subregional_reserves` / `miso_reserve_pergen` / `miso_zonal_reserves`
are ARMED and own the **reserve** requirement — and miso-153's D-4 measured them
**INERT at the summer peak** (zero binding hours, zero shortfall, dual $0.00,
all three families × all three years × 1,464 Jun+Jul hours).

**Channel (iii):** owned by the **C3c ledger** and its 2026-07-20 frontier
designation. **This session does not touch the C3c ledger, proposes no tail
mechanism, and never tunes to the tail.** Δ₃ is measured only to size what the
other two channels cannot reach.

---

## 5. Priors — two-sided, numeric, committed before measurement

Shares of the **2025 annual, load-weighted** gap `mean(P_act) − mean(P_mod)`,
which is the C3a grain. They sum to 100 % by construction, so the bands overlap
deliberately.

| channel | prior band | centre |
|---|---|---|
| **(i) IDENTITY** | **45 – 80 %** | **60 %** |
| **(ii) COST LEVEL (fuel)** | **5 – 35 %** | **20 %** |
| **(iii) ABOVE-COST** | **5 – 25 %** | **15 %** |

**Reasoning, from the published localization rather than from any gas datum.**
miso-152 established that the miss is **June/July** and that the model's summer
distribution sits at winter levels — its summer p99 **below** its own winter
p99. A delivered-fuel level error is a roughly month-uniform multiplier on the
whole year, and MISO's gas basis is a **winter** phenomenon (which is why the
two armed gas mechanisms are a mean-zero spread and a **Dec/Jan/Feb** daily
shape). A month-uniform cause cannot own a miss that is 46 % concentrated in
17 % of hours in the two months where basis is least active. What *is*
load-shaped is which unit is marginal: miso-153 found 16.2 GW idle at the 2025
peak, **55.8 % of CT's own availability**, with **6.31 GW within $20/MWh** of the
clearing price — a nearly flat top-of-stack the price walks along instead of
climbing. That is channel (i).

**Two-sided against my own branch.** The IMM's at-cost finding cuts *both* ways:
it argues Δ₃ should be small, but it also means any Δ₁ I find must be a real
cost difference between real units, not a markup — and if `IHR*_act` lands
**outside** the model's own heat-rate distribution, channel (i) is not a
misidentification the fleet can fix and my 60 % centre is wrong. Equally, a
summer gas basis blowout is a real phenomenon I have deliberately not looked at;
`gas_basis_by_iso_month` is **month-varying**, so channel (ii) is genuinely
capable of being month-concentrated and my 20 % centre could be badly low.
**I record now that Δ₂ ≥ 50 % would refute my reading of this lane**, and that I
would report it as such.

**PRIOR P-4 (year ordering, load-bearing).** Whatever channel dominates 2025
must be **materially smaller in 2023**, since 2023 passes C3a at ≈ −0.5 %. A
decomposition that assigns 2023 a large channel-(i) gap while 2023's total gap
is ~0 would mean the channels are cancelling — I pre-register that as a
**disclosure-triggering** outcome, not a quiet one.

---

## 6. Branches — fixed here, with their consequences

| branch | condition (2025 annual) | consequence |
|---|---|---|
| **B-IDENT** | Δ₁ ≥ 50 % **and** `IHR*_act` lands inside the model's own gas heat-rate distribution in ≥ 60 % of Jun+Jul hours | The miss is a **marginal-unit identity** failure at high load. Phase 1 proceeds to the identity queue (`measured_ramp_capability` / `ramp_envelopes`), under §7's against-interest bound, **or** names it and stops if no admissible identification exists in-session. |
| **B-COST** | Δ₂ ≥ 50 % | The miss is a **delivered-fuel level** failure. **S-FUEL has fired and my prior is refuted** — reported in those words. The lever is a level reconciliation that preserves per-plant dispersion (§4); `gas_hub_basis_overlay` **as constructed** is NOT armed on a favourable Δ₂ alone. |
| **B-ABOVE** | Δ₃ ≥ 40 % | The miss is largely **unreachable by cost-based identity**. **NO LEVER, and the session STOPS at Phase 0** — the remaining object is C3c-adjacent and its ledger/frontier designation governs it. Reported at full magnitude. |
| **B-SPLIT** | no channel ≥ 50 % and Δ₃ < 40 % | **NO LEVER.** A split residual means rule 19 `[R-ONE-MECH]` cannot name one owner, and the split itself is the finding. |

**In every branch the full decomposition is reported at all three grains and all
three years.** No branch permits arming a mechanism whose channel did not win,
and none permits quoting a grain other than **annual** as the adjudicating one
(C3a is an annual mean).

### 6.1 Pre-committed surprise triggers

| trigger | fires when | what I do |
|---|---|---|
| **S-FLOORBLIND** | rebuilt floors miss miso-155's committed `FLOOR_source` by > 0.5 % on CT TWh, or the floored-row count differs | The instrument is not the one that cleared. **Stop, debug, disclose before any conclusion.** No adjudicating statistic is quoted. |
| **S-FUEL** | Δ₂ ≥ 50 % of the 2025 annual gap | **My §5 prior is REFUTED.** Reported as a refutation, at full magnitude, and branch **B-COST** is taken. |
| **S-SIGN** | any channel carries the **wrong sign** at annual grain (e.g. `G_mod > G_act`, so the model's fuel is *too expensive*) | The lane's framing of a uniform level *deficit* is wrong in that channel. Report the sign and magnitude explicitly; do not net it away inside a total. |
| **S-2023** | the 2023 decomposition shows a channel ≥ 50 % of a gap that is itself ≈ 0 | Channels are cancelling in the passing year. Disclose; treat any 2025 attribution as **provisional** and say so. |
| **S-CEIL** | `HRmax` is set by a single tranche carrying < 0.5 % of gas capacity | Δ₃ is then an artifact of one outlier. Re-report Δ₃ on a capacity-weighted p99 heat rate as a **declared, labelled** sensitivity, alongside the primary. |

---

## 7. Validity gates — reproduce published numbers BEFORE any adjudicating statistic

Run first, in this order. The miso-154 void-run precedent is binding.

* **V1 — the scored C3a is reproduced from committed artifacts.** The probe's
  own load-weighted model mean over the 6 carry zones must reproduce the
  registered C3a of **−1.98 / −8.03 / −15.58 %** against `bench.avgLMP.rt_lw`
  to **±0.5 pp** in all three years.
* **V2 — the rebuilt floors reproduce miso-155's committed record.** Against
  `_miso155_p0_exact_instrument.json` `FLOOR_source`: CT floor
  **2.8457 / 2.8773 / 2.8677 TWh**, floored CT rows **158 / 150 / 153**, CT max
  **144.605 MW**, fleet floor **117.44 / 120.70 / 121.86 TWh** — tolerance
  **0.5 %** on the TWh figures and **exact** on the row counts. A miss fires
  **S-FLOORBLIND**.
* **V3 — the decomposition identity holds elementwise.** `Δ₁+Δ₂+Δ₃ = P_act−P_mod`
  to **1e-9** on every zone-hour of every year. Asserted, not spot-checked.
* **V4 — the reconstruction is the keeper's own fleet.** `n_gen` reproduces
  miso-155's **2929 / 2923 / 2923**, carry-zone count **== 6**.

**Environment integrity, already executed and recorded here:**
`git status --short | grep -c '^ D'` = **0**; the container shipped **no
`.venv`** (one was built from `requirements.txt`); `data/clean` was **empty** and
`curate_capacity_deliverability.py` wrote **776 MISO rows** (the expected count).

**AGAINST-INTEREST BOUND (binding, inherited from miso-154/miso-155 PREREG §7).**
2023 passes C3a at ≈ −0.5 %. **A lever that lifts 2023's mean by more than +3 %
is a REGRESSION even if 2025 improves.** No lever is applied in Phase 0. If
Phase 1 arms one, its **expected 2023 effect is stated in a SECOND
pre-registration, before any solve**.

**Contingency, pre-registered.** If Phase 1 charters a lever but the rule-12
per-year solve chain cannot complete all three years in this session, **no
solve-based statistic is quoted**: the session reports Phase 0 complete, the
lever named-but-not-armed, and registers **nothing**. A partial-year solve is
**never** registered (rule 16 `[R-ALLYEARS]`).

---

## 8. Traps, each with its counter-measurement

T-1…T-8 are inherited and re-run unchanged; T-18…T-23 are new to this
decomposition.

| # | Trap | Counter-measurement |
|---|---|---|
| **T-1** | `_miso134` is HARD-WIRED to another bundle | Repoint to `miso148_basis_B` and **assert** at import |
| **T-2** | 3-arg `getattr` on the offer path encodes a wrong field name | **Zero** 3-argument `getattr(` added on the offer path; `grep` count reported; `ruff` clean |
| **T-3** | **Disbelieve clean zeros** — the trap that produced miso-155's finding | Every exact `0.0` in a reported aggregate gets a **second, different derivation** or is reported unverified |
| **T-4** | `SimpleNamespace` fixtures encode the same wrong name as the code | Production types only; assert no `SimpleNamespace` |
| **T-5** | `MISO_external*` are IMPORT NODES | Assert carry-zone count **== 6**; import nodes excluded from every aggregate (V4) |
| **T-6** | `build_year` keys the CAMPD derate on `config.weather_year`, not the solve year | `dataclasses.replace(cfg, weather_year=y)` **per solve year**; V1/V4 are its control |
| **T-7** | An inert instrument "clears" nothing and looks like a fix | Report each channel's **$/MWh magnitude**, not only its share |
| **T-8** | A re-implemented production function reproduces my expectation, not the model's | **Assert** `inject_reliability_floor.__module__ == "market_sim.model.transmission"` and `assemble_mc.__module__`; the floor specs come from `RELIABILITY_FLOOR_REGISTRY` through the production override/drop chain |
| **T-18** | **The floors are gitignored** (§2), so "read the bundle" is unreproducible | Rebuild via the production engine and **gate on V2** against miso-155's committed record |
| **T-19** | A floored tranche is dispatched at `min_gen` and is **not** marginal, yet would be counted as the price-setter | The marginal-tranche search **excludes** rows whose entire availability is floored, and reports how many hours that exclusion changes |
| **T-20** | `IHR = (P − V)/G` explodes when `G` is small or `P < V` | Report the hours where `P_act < V` or `G ≤ 0.5 $/MMBtu`; they are counted, magnitude-reported and **excluded from shares** rather than silently clipped |
| **T-21** | Congestion makes a zone's LMP differ from any unit's mc, so the "marginal unit" is a fiction in that zone-hour | Measure the cross-zone price spread; report the share of hours with a spread > $1/MWh, and run the whole decomposition **both** per-zone and on the load-weighted ISO mean, reporting both |
| **T-22** | `P_act` is a **hub** series while `P_mod` is a **zonal** series — a basis mismatch masquerading as a channel | Use the scorer's own `rt_lw` basis for the adjudicating annual number, so V1 ties the decomposition to the registered C3a; the hourly hub series is used only for **within-year shape** and its annual mean is reconciled to `rt_lw` and the reconciliation reported |
| **T-23** | Δ₃ is defined off `HRmax`, a max over an unbounded tail | **S-CEIL** (§6.1): report `HRmax`'s owning tranche and its capacity share; if < 0.5 %, re-report on a capacity-weighted p99 as a labelled sensitivity |

---

## 9. Rules engaged

* **Rule 1 `[R-STRUCT]`** — this is a *diagnosis*, judged on whether it
  decomposes the model's own price formation faithfully, never on whether a
  channel flatters a lever. No branch reaches a number through a mechanism that
  isn't real.
* **Rule 13 `[R-MEASURED]`** — nothing is pinned to a measured outcome. The
  actual LMP enters only as the *target being decomposed*; no model input is
  rescaled so an output lands on it.
* **Rule 14 `[R-ACCURATE]`** — §2 prefers the production floor engine over a
  gitignored artifact; §4 refuses in advance to trade MISO's faithful per-plant
  F923 dispersion for a flat hub series.
* **Rule 19 `[R-ONE-MECH]`** — §4 enumerates the current owner of each channel
  **before** any lever is named.
* **Rule 20 `[R-DOF]`** — Phase 0 introduces **zero** free parameters. `V`,
  `HRmax` and the branch thresholds gate a *report*, not a solve.
* **Rule 24 `[R-REGISTRY]` / 28(c)** — Phase 0 adds **no `ScenarioConfig`
  field**, so no matrix mechanism row is created. The MISO shard is stamped with
  this session's outcome under rule 28(b) regardless.
* **Rule 25 `[R-ISO-SCOPE]`** — every parameter is derived from MISO data; no
  verdict is transferred from another ISO.
* **Rules 12 / 15 / 16 / 22** — years sequential, register any completed run in
  this session, all three train years in one bundle, no holdout year touched.
* **Rule 27 `[R-PUSH]`** — Opus; local edits pushed as exact on-disk bytes;
  every push touching a ≥300-line file blob-verified immediately.
* **Rule 28(a)/(b) `[R-MECH-MATRIX]`** — no `R`/`I`/`G` cell is re-tested; the
  MISO shard is updated this session, rejection or not.

---

## 10. Disclosure standard

Any statistic computed in this session that is **not** specified in §3–§8 is
labelled **NOT PRE-REGISTERED** where it is reported, with its
counter-measurement and its **full magnitude** — in the favourable and the
unfavourable branch alike. Scope extensions are disclosed, never silently folded
in.
