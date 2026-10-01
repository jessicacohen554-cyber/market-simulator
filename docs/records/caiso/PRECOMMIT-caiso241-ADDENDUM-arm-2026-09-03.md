# PRECOMMIT ADDENDUM — caiso-241: the arm, its pre-solve G-STRUCT proof, and its TWO-SIDED envelope

**Pushed BEFORE any solve**, per the caiso-240 two-file pattern. The ruling,
design, predictions and gates are fixed in
`PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md`, pushed to `origin` as
`cf05a372` **before any fleet was rebuilt or any number below was measured**.
Nothing here revises that file; this addendum only carries what it deferred —
the evaluated bound — plus the pre-solve gate legs and one corroboration found
**after** the push, labelled as such.

**ZERO SOLVES so far.** Everything below is a fleet rebuild
(`run_year(fleet_only=True)`) or a read of the keeper's committed hourly
sidecars. CAISO holds no `complete` / `final` marker; the holdout freeze is
ACTIVE; every read is inside 2023–2025.

---

## §A1 — THE ARM, BUILT

`ScenarioConfig.caiso_ct_peaker_committed_measured` — gated, default off,
CAISO-gated, `--caiso-ct-peaker-committed-measured`, threaded onto
`--replay-bundle`. Applied on the **resolved band dict** in
`pipeline.backcast_config` (CT_PEAKER resolves a class curve, unlike the
caiso-239/240 bypass siblings, so there is no consumer-side limb):

```python
offer["committed"] := offer["phys_committed"]     # 1.350 -> 0.991
```

Not in `_BACKCAST_ONLY_OVERLAY_FIELDS` — `avg_committed_p50` is a physical
ratio that regenerates forward from CAMPD conduct (rule 13 `[R-MEASURED]`),
like its caiso-239 sibling and unlike caiso-240's.

Six unit contracts pinned in
`tests/unit/pipeline/test_caiso_ct_peaker_committed_measured.py` (**6 passed,
5 subtests passed**): byte-identical off; the band takes its own
`phys_committed` on; exactly one band on exactly one group moves;
band-disjoint from `caiso_offer_surface_measured*` (rule 19 `[R-ONE-MECH]`);
a non-CAISO ISO is a hard error (rule 25); a CAISO `CT_PEAKER` band with no
`phys_committed` is a hard error, never a silent fallback.

---

## §A2 — G-STRUCT, PRE-SOLVE: **PASS**

`scripts/probes/_caiso241_gstruct_presolve.py` →
`results/calibration/_caiso241_gstruct_presolve.json`. The keeper's own
`meta.json` rebuilt flag-off and flag-on at HEAD, all three years, every fleet
row diffed. **No LP.**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| fleet rows | 1,801 | 1,795 | 1,800 |
| rows moved | **44** | **44** | **44** |
| groups moved | `CT_PEAKER` | `CT_PEAKER` | `CT_PEAKER` |
| bands moved | committed | committed | committed |
| capacity moved | 829.8 MW | 829.8 MW | 829.8 MW |
| CT_PEAKER class capacity | 7,528.5 MW | 7,535.0 MW | 7,538.7 MW |
| **moved share of class** | **11.02 %** | **11.01 %** | **11.01 %** |
| ratio exact at 0.991/1.350 = **0.734074074074** | ✔ | ✔ | ✔ |
| `offer_markup_hr` → exactly 0.0 on every moved row | ✔ | ✔ | ✔ |
| rows moved in any other band / group / ISO | **0** | **0** | **0** |

**G-STRUCT PASSES**, and with it the registered substitute for the
dispatch-level control this arm cannot have (§0.6(2) — it is expected live in
all three years, so caiso-240's dispatch-identity form of G-CTRL has no inert
year to bind on). **What it does NOT prove, restated:** that nothing else
drifted between the keeper's `git_sha` and HEAD. Owner ask 2 stands.

**P-3 CONFIRMED, pre-solve** (registered: *"< 25 % of CT_PEAKER grid
capacity"*) — measured **11.0 %**.
**P-5 CONFIRMED, pre-solve** (the exact ratio, the zeroed markup, nothing else
moving) — every leg measured.

---

## §A3 — THE MEASURED DECOMPOSITION: THE QUANTITY REMOVED IS **EXACTLY** THE FUEL-INVARIANT COMMITMENT MARGIN

This is the sharpest confirmation of ruling limb 3 available without a solve,
and it was not guaranteed in advance.

Under `gas_offer_net_revenue_margin` the reformed cost is
`mc = phys·base_hr·fuel + (mult − phys)⁺·base_hr·anchor`. Grounding
`mult := phys` therefore leaves the **fuel-scaled physical cost untouched** and
removes **only** the fuel-invariant margin. Measured on the moved rows:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| capacity-weighted Δ mc | **−18.6197** | **−18.6197** | **−18.6197** $/MWh |

**Identical to four decimals in all three years, across gas at 2.54 / 2.19 /
3.52 $/MMBtu.** Per-row range −15.04 to −29.39 $/MWh (median −18.63);
`offer_markup_hr` 3.136 – 6.128 MMBtu/MWh (median 3.884) → 0.0.

The precommit's route arithmetic predicted **≈ $18.7/MWh** from the class base
heat rate; measured **$18.62**. So the entire effect of the fitted 1.35 is a
**fixed $/MWh commitment adder** — the margin mechanism has already isolated it
into exactly the form that makes it a start-cost adder — and it sits on top of
P1's identified amortized startup markup on the **same tranche**. Rule 19
`[R-ONE-MECH]` is not an interpretation here; it is arithmetic.

---

## §A4 — CORROBORATION FOUND **AFTER** THE PRECOMMIT PUSH, LABELLED AS SUCH: **MISO HAS ALREADY MADE THIS REPAIR, AND SAID WHY IN LIMB 3's WORDS**

Not pre-registered. Found while measuring the cross-ISO cells rule 28(c)
requires, and recorded here rather than folded silently into the ruling.

A config-only census (zero solves) of every ISO's resolved `CT_PEAKER` band:

| ISO | `committed` | `phys_committed` | ratio | `peak` | inverted? |
|---|--:|--:|--:|--:|---|
| ERCOT | 1.480 | 1.022 | 1.45 | 13.15 | no |
| **CAISO** | **1.350** | **0.991** | **1.36** | **1.166** *(keeper)* | **YES** |
| PJM | 1.250 | 1.049 | 1.19 | 4.00 | no |
| **MISO** | **1.025** | **1.025** | **1.00** | 4.00 | no |
| NYISO | 1.350 | 0.843 | 1.60 | 4.00 | no |
| NEISO | 1.350 | 0.985 | 1.37 | 4.00 | no |

**Five of the six ISOs price the CT min-load band above their own measured
basis. MISO is the one that has already grounded it — exactly on
`phys_committed`, to the third decimal — and `_MISO_OFFER_CURVE` states limb
3's argument verbatim:**

> *"The commitment-cost component of the real MISO CT offer (start + no-load
> recovery) is **NOT a static heat-rate multiplier**: MISO's ELMP (FERC Order
> 825 fast-start pricing) folds fast-start startup/no-load offer costs into the
> LMP, **represented by the P1 startup amortization** … **not by a band
> multiplier here**."*

So the repair is **precedent-following, not novel in kind**: the codebase
already contains this exact design principle, applied in one ISO and not in
CAISO. Two consequences:

1. **It strengthens the ruling and weakens nothing.** Limb 3 is not this
   session's invention; it is the model's own stated design rule, unevenly
   applied.
2. **It sharpens limb 4 and is, if anything, stronger for CAISO than for
   MISO.** MISO routes commitment cost to the P1 amortization on its CT
   **econ/peak** tranches (`tranche_startup_amortization = True` there). CAISO
   has that flag **off**, so on CAISO the P1 amortization lands on the
   `_committed` tranche itself — precisely the band carrying the second
   mechanism.

**Rule 25 `[R-ISO-SCOPE]` disposition is UNCHANGED and nothing transfers.**
ERCOT / PJM / NYISO / NEISO cells stay `U`: each lane grounds its own band on
its own measured `avg_committed_p50` — 1.022 / 1.049 / 0.843 / 0.985 — or the
cell stays `U`. **MISO's value is not imported and CAISO's is not exported.**

---

## §A5 — THE TWO-SIDED ENVELOPE (§H′), EVALUATED

`scripts/probes/_caiso241_cell_bound.py` →
`results/calibration/_caiso241_cell_bound.json`. Per precommit §3, the
caiso-230 §H form is **not** used as a ceiling — caiso-240 falsified that
description, and this arm sits squarely in the regime where §H under-predicts
(it lowers a band on a class that is 66–90 % absent, so its dominant channel is
energy attracted *into* a class that is not running). The estimator is the
crossing envelope of §3.2, which prices that channel directly.

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| repriced tranches | 44 | 44 | 44 |
| crossing zone-hours | 5,102 / 43,800 | 2,822 / 43,800 | 2,102 / 43,800 |
| crossing share | 11.65 % | 6.44 % | 4.80 % |
| mean fall **in** crossing hours | −7.55 | −5.90 | −4.12 $/MWh |
| **envelope B** | **0.8798** | **0.3804** | **0.1979** $/MWh |
| **REGISTERED INTERVAL** | **[−0.8798, +0.05]** | **[−0.3804, +0.05]** | **[−0.1979, +0.05]** |
| **volume envelope** | **0.432** | **0.247** | **0.120** TWh |
| §H matched-marginal zone-hours *(diagnostic only)* | 576 | 90 | 11 |

**No year is degenerate** (every year has crossing zone-hours), so the §0.6(2)
degeneracy clause does not fire; it stands unspent for whoever needs it.

**Falsifiers, as registered:** a measured annual mean price move **below −B**
falsifies the envelope (the channel delivered more than its maximum ⇒ estimator
or mechanism defect); a move **above +0.05** falsifies the sign. **A bound
violation is disclosed as a defect and NEVER re-fitted.**

**Two conservatisms, both stated in the probe's own docstring:** the costs are
`mc_base` (P0), so the true P1 bid is *higher* on these rows and fewer hours
cross — the envelope over-states the crossing; and B assumes the repriced
tranche sets price in **every** hour it newly clears.

---

## §A6 — WHAT THE ENVELOPE SETTLES BEFORE THE SOLVE, AND IT IS UNCOMFORTABLE

**THE ARM CANNOT CLOSE THE CT_PEAKER DEFECT, AND CANNOT MOVE C3a TO PASS. BOTH
ARE NOW MEASURED CEILINGS, NOT EXPECTATIONS.**

* **Volume.** The maximum energy the repriced tranches can attract is
  **0.432 / 0.247 / 0.120 TWh** against a measured miss of
  **2.71 / 3.84 / 2.11 TWh** — i.e. **at most 16 % / 6 % / 6 %** of the gap.
  **P-2 and P-6 are all but settled in the direction they were written**, and
  they were written before this was measured. The CT_PEAKER object of
  caiso-240 **survives this repair**; its dominant cause is elsewhere — the
  econ/peak bands, availability, or a structural absence — and is a separate,
  larger, unfunded object.
* **Price.** The deepest possible fall is **0.880 / 0.380 / 0.198 $/MWh**
  against a required move of **0.00 / −0.848 / −1.893**. Even at its absolute
  maximum the arm **cannot** flip C3a in any year: 2023 needs no move, 2024's
  ceiling is 45 % of what it would take, 2025's is 10 %.

**This is the strongest possible form of the rule-1 `[R-STRUCT]` posture the
precommit §0.7 committed to.** The direction is favourable, and the arm is
nonetheless **incapable of being a C3a lever** — measured, in advance, from its
own maximum. It is a structural-integrity repair, argued and gated as one.

---

## §A7 — UNCHANGED

Hard stops, DO-NOT-REDO, the no-control-arms deviation, the promotion rule
(§5.9 — structural basis; C3a excluded from the basis), and **the funding gate
(§0.8): no LP runs under this precommit until the owner funds it.** The four
owner asks stand, with ask 4 now measured rather than predicted.
