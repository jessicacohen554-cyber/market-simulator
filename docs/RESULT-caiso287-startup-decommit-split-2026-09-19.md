# RESULT caiso-287 — the split is unanimous: the DECOMMIT screen is exonerated, the `startup_aware` screen removes the coverage, and the real object is its 42–60 % DROP RATE

**Lane:** CAISO calibration · **Date:** 2026-09-19 · **Keeper UNCHANGED at the time of
writing** `2026-09-12-caiso-275-gascoupling` (the owner-ruled MER promotion is §7).
Pre-registration: `docs/PRECOMMIT-caiso287-startup-decommit-split-2026-09-19.md`, pushed at
`92b8e4dbf6017a8571026c3f58fb20914e590875` **before** any shard was launched. Every metric, gate,
cut and verdict word below was fixed there.

---

## 0. The answer in one paragraph

caiso-286 re-opened the CAISO belly with 270.3 mean-belly-MW that pass the RA bridge's restart
inequality and are floored by nothing, and named two screens that could be removing them. **It is
the `startup_aware` run screen, in all four years, by a factor of 40 to 370.** The surplus decommit
screen removes **1.157 to 2.591 mean-belly-MW on its own** — between 0.2 % and 2.2 % of the joint
removal — so caiso-285's exoneration of it survives, now established on the per-gap P0-dual basis
that caiso-285 could not compute and caiso-286 showed its own arithmetic did not reach. But the
pre-registered §6.2 limb then dissolves the mechanism this session was sent to find: **the
gap-fusing is not a defect** — it follows from the screen's own premise — and the coverage is lost
through the **24-hour DA exclusion**, not through the restart economics. What is left standing is
one number the screen produces without anyone having looked at it: it **drops 42–60 % of every
detected run**, on an anchor test priced off the model's own P0 duals — **the exact circularity
this repository already adjudicated as disqualifying when it refused to expose the same screen for
ERCOT.**

---

## 1. What made the split possible, and what it cost

The two screens both read the **P0 dispatch in MW** and the **P0 duals**, and **no committed
artifact carried either** — verified by tree read over the caiso-285 bundle (17 files; the only
dispatch payloads are `2024_P1.parquet` and `2024_P1_fleet.parquet`; there is no `_P0`). That is
why caiso-285 had to invert the inequality analytically and why caiso-286's 270.279 MW is an
upper bound.

**`--persist-p0-dispatch`** (`scripts/` only, opt-in, default-off, write-only) closes it, writing
`hourly/p0_dispatch_<year>.parquet` (float64, packed per generator) and
`hourly/p0_prices_<year>.parquet` (the duals, carrying their zone **names**). Byte-identity was
proved on four legs, the strongest empirical: caiso-285 was solved **with** the sibling flag
`--persist-p0-commitment`, and that string appears nowhere in its committed `meta.json`, so
persistence flags never reach meta at all — an armed run differs from an unarmed one by exactly
**two added files**.

**A second, unstated defect in caiso-286 is corrected here.** Its probe priced every gap at the
**P1** dual (`df["pass"] == "P1"`), because the committed sidecars carry P1 only. The screens are
fed the **P0** duals (`build_caiso_ra_p1_prep` passes `r0.prices`). So 270.279 MW was a bound on a
price array the screens never saw.

**Cost:** 8 shards (2 arms × 4 years), 2 arms because the MER control arm rode along. The parent
spent **zero LP** (rule 32 `[R-SHARD]` (a)). 2024 instrumented: 23.0 min, 8.28 GiB peak.

## 2. THE SPLIT — unanimous across all four years

The production `caiso_ra_mustoffer_min_gen`, unmodified, in four configurations per year, with the
keeper's own arguments. Metric: mean over the belly of the total RA floor on `CC_REGULAR` rows.

| year | `M_both` (keeper) | `M_sa` | `M_dc` | `M_none` | **R_SA** | **R_DC** | R_total | bar@70 % | verdict |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 2022 | 986.835 | 1017.623 | 1103.944 | 1106.535 | **88.911** | **2.591** | 119.699 | 83.790 | **(A)** |
| 2023 | 785.472 | 872.817 | 1180.992 | 1183.277 | **310.460** | **2.285** | 397.805 | 278.464 | **(A)** |
| 2024 | 670.470 | 788.185 | 1217.472 | 1218.628 | **430.444** | **1.157** | 548.158 | 383.710 | **(A)** |
| 2025 | 773.710 | 907.217 | 1490.339 | 1492.621 | **585.404** | **2.283** | 718.911 | 503.238 | **(A)** |

**(A) GAP-MERGING DOMINANT** in every year, on the cut fixed before any shard ran.

**The surplus decommit screen is exonerated, definitively.** `R_DC` never exceeds 2.6 mean-belly-MW.
caiso-285 exonerated it on an arithmetic caiso-286 then showed did not hold; this exonerates it on
the basis the code actually computes, with both screens armed and the real P0 duals, and the answer
is the same. **caiso-286 §9's re-opening of it is CLOSED** (rule 28 `[R-MECH-MATRIX]` (a)).

## 3. The gates

**G-R1 PASS** in all four years — belly reproduced, unit-id alignment asserted across the rebuilt
fleet, `p0_dispatch` and `floors`, and a zone map asserted one-to-one and dense from the fleet's own
`zone` attribute (the caiso-286 §4 defect).

**G-R2 PASS at artifact precision** in all four years: `float32(detector) == stored` **exactly**, 0
mismatching RA gen-hours of 39,785 (2024) and 42,409 (2023). **But it FAILED as I wrote it**, and
that is reported rather than quietly restated: the PRECOMMIT specified a float64 equality against
`floors/<year>_P1.npz`, which stores `min_gen` as **float32**, so the literal form cannot pass even
on a bit-exact reproduction (max |Δ| 7.46e-06 MW; float64-vs-store relative difference 5.79e-08,
strictly below float32 eps 1.19e-07). The defect was in the gate wording. Both forms are in every
committed record.

**That 2023 and 2025 reproduce the committed floors exactly is the strongest evidence in this
document** — those are years the probe was not built against, so the reproduction is not a fit.

**G-R3** reproduces caiso-286's published 670.470 belly RA mean on 2024 (670.4704). Off 2024 there
is no published expectation, so the figure is REPORTED, not gated.

## 4. §6.2's limb — THE FUSING IS NOT A DEFECT

The pre-registered question was whether a **dropped** run should still delimit gaps. The census:

| year | runs dropped | belly MW on FUSED gaps | on gaps OVER the 24 h horizon |
|---|---|--:|--:|
| 2022 | 3506 / 8288 (42.3 %) | 44.5 % | 26.2 % |
| 2023 | 3405 / 6989 (48.7 %) | 55.9 % | 51.5 % |
| 2024 | 5070 / 8384 (60.5 %) | 64.4 % | 63.5 % |
| 2025 | 4760 / 8221 (57.9 %) | 64.0 % | 62.8 % |

**The question answers itself.** The screen's premise is that a dropped run is one a real
unit-commitment would never have started. If the unit was never started it was **idle across the
whole span**, so the fused gap IS the true idle period and pricing the hold over all of it follows
from the premise rather than from the rebinding. A dropped run is precisely a run the unit did not
physically have. **There is no repair to make here, and this lane proposes none.**

**And the coverage is lost through the DA exclusion, not the restart economics.** In 2023/24/25 the
over-DA share tracks the fused share almost exactly (51.5 vs 55.9 · 63.5 vs 64.4 · 62.8 vs 64.0).
The dominant path is: drop ~half the runs → gaps fuse → the fused gap exceeds 24 h → excluded
outright at `commitment.py:1221`, never repriced. That is also internally consistent: a >24 h idle
is a next-day decommit, not an intra-day min-load hold.

## 5. WHAT IS LEFT STANDING — the drop rate, and a circularity this repo has already ruled on

The screen drops **42–60 % of every detected run**. Its anchor test scores a run on the **model's
own P0 duals**:

```python
margin_per_mw = Σ_t (p1_prices[zone, t] − base_mc[g, t]) × p0_dispatch[g, t] / pmax   # :1067
if margin_per_mw >= startup_per_mw: keep
```

**This repository has already adjudicated that circularity as disqualifying — in another ISO.**
`src/market_sim/config/scenarios.py:12824`, verbatim:

> *NOTE (ERCOT-63 startup-aware adjudication): the CAISO `caiso_ra_bridge_startup_aware` run screen
> is deliberately NOT exposed for the ERCOT bridge. Its anchor test prices a run's margin off the
> model's own P0 duals; ERCOT's modelled troughs are the +$5-7-overpriced, spread-flattened quantity
> under repair (diagnosis §2), so run margins are circularly thin and the screen refuses every
> anchor … Re-deriving a lower margin threshold "for ERCOT economics" would be a scalar tuned until
> anchors survive — a residual-fitted knob (rules 13/20). Dropped with cause.*

**The same argument reaches CAISO, where the screen is armed.** CAISO's belly price is likewise the
quantity under repair — caiso-285 measured the belly clearing at **−$6.71** and the deficit *is* the
object. A run scored against a belly price that is itself wrong produces a margin that is
circularly thin, and the measured consequence here is a 42–60 % drop rate.

**Stated as what it is, and not more.** This does **not** show the drop rate is wrong, and it is
**not** a proposal to disarm `startup_aware`. Rule 1 `[R-STRUCT]` forbids removing a
structurally-motivated mechanism because it costs coverage, and PRECOMMIT §6.2 pre-registered that
refusal in advance precisely so an (A) verdict could not be turned into one. What is shown is that
the screen's **identification** is circular on exactly the quantity CAISO is trying to repair, that
the repo already refused it elsewhere for that reason, and that the consequence is measurable.
**Whether that identification is admissible is a rules-1/13 question for the owner.**

## 6. The MER control arm — and two findings about the keeper

**Marginal carbon, produced for every CAISO year** (the append's purpose):

| year | load-weighted MER (tCO₂/MWh) | p10 / median / p90 | exact-zero: CAISO zones | WECC_DSW | WECC_PNW |
|---|--:|---|--:|--:|--:|
| 2022 | 0.2945 | −0.0 / 0.3628 / 0.4912 | 31–35 % | 78.0 % | 63.1 % |
| 2023 | 0.3050 | −0.0 / 0.3639 / 0.4448 | 24–26 % | 66.6 % | 60.7 % |
| 2024 | 0.2927 | −0.0 / 0.3674 / 0.4462 | 26–31 % | 58.4 % | 44.1 % |

The zero share is concentrated at the import nodes in every year, exactly the predicted signature.

**FINDING 1 — G-DRIFT form 4 is NOT bit-confirmed, and the reason is dual degeneracy, not drift.**

| year | primal (slack/dump/demand) | scored load-weighted mean | WECC_PNW max abs Δ | every other zone |
|---|---|--:|--:|--:|
| 2022 | **identical (0.0)** | 94.068804 → 94.074407 (+0.0060 %) | 472.18 | ~19–21 |
| 2023 | **identical (0.0)** | 55.891457 → 55.893744 (+0.0041 %) | 88.35 | ~4.75 |
| 2024 | **identical (0.0)** | 37.547014 → 37.547070 (+0.0001 %) | 171.28 | **~0.28** |

The primal solution is unchanged in every year; the scored quantity moves by at most 0.006 %; and
the magnitude is confined to WECC_PNW by up to **600×**. That is the degenerate import-node dual
caiso-285 G1 already measured, not a behaviour change. Solver and numerics stack are identical
(highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, python 3.11.15); only the kernel differs.

**FINDING 2 — the CAISO keeper's provenance SHA does not resolve.** Both keeper bundles record
`git_sha b8ddf8bc`, and that object is not in this repository: not fetchable from origin, absent
from `docs/governance/citation-commit-map.txt`, and `--disambiguate` finds no object with the
prefix. **So rule 29 `[R-SCREEN]` (b)'s G-DRIFT code audit cannot be performed against the current
CAISO keeper by any session**, and the drift above cannot be attributed on code evidence. The
primal/scored/per-zone split is what carries the conclusion instead. **The §7 promotion repairs
this** — the incoming bundles record `4583e70b`, which resolves.

**A correction on the record.** An earlier reading in this session reported "0 commits on the solve
path" between the keeper SHA and the control SHA. That was **false**: `git log` errored on the
unresolvable revision, the error went to a discarded stderr, and `wc -l` counted the empty output as
zero. A clean zero that should have been disbelieved. Nothing downstream rests on it.

## 7. The promotion, and the governance ledger

**OWNER RULING 2026-09-19, verbatim: "Mer should be promoted either way."** Executed as a rule 35
`[R-PROMOTE]` promotion: compose 2023/24/25 into one span bundle, keep 2022 stamped to it (rule 30
`[R-TOUCHPOINT-FOLD]` (a)), register, re-score, verify with `audit_keepers` E1, **then** prune the
outgoing keeper (35(e): promote → verify → delete). The year union **{2022, 2023, 2024, 2025}** was
enumerated and recorded **before** any prune (35(b)), since the delete destroys the evidence.

What promotion changes, reported rather than buried: the scored numbers move by the §6 amounts
(+0.0001 % to +0.0060 %), and Finding 2 is repaired.

* **Zero LP in the parent** (rule 32 (a)). Every number here is arithmetic over committed sidecars
  and a `fleet_only` rebuild.
* **No `ScenarioConfig` field added**, no constant changed, no derive re-run, no offer-curve
  multiplier touched, **no mechanism armed or disarmed**.
* **`src/` untouched.** The only code is `scripts/` (the opt-in flag) and four probe scripts.
* **Nothing deleted** (rule 31 `[R-RETAIN]`).
* **Matrix (rule 28 (b)):** the `gas_commitment_bridge` cell's evidence line is extended with §2,
  §4 and §5; no cell verdict moves, because no mechanism was armed or rejected.

## 8. What this closes, and what it opens

**CLOSED (rule 28 (a) — do not re-test without new evidence):**

1. **The surplus decommit screen as the belly's remaining mechanism** — `R_DC` ≤ 2.6 mean-belly-MW
   in all four years, measured on the code's own basis with both screens armed.
2. **"Does a dropped run belong in the gap arithmetic?"** — §4. It does; the fusing follows from the
   screen's premise. No repair exists to make.
3. **The gap-fusing as a repairable side effect** — same.

**OPEN, and named:** the `startup_aware` **drop rate** (42–60 % of runs) and the admissibility of an
anchor test priced off the model's own belly duals — the circularity `scenarios.py:12824` already
refused for ERCOT. **This is an owner admissibility question under rules 1/13, not a residual to
tune**, and this lane proposes no value, arms nothing and disarms nothing.

**If the owner rules the identification admissible**, the CAISO belly has no remaining identified
mechanism in the RA bridge, and PRECOMMIT §6.3's outcome stands: the 270.3 MW should not be held,
the keeper stays `CALIBRATED` with its single ledgered C3c, and the honest successor is the 2022
C3a object on its own terms (rule 30 (c): a held-out year never downgrades the ISO).
