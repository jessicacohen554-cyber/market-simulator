# PREREG miso-132(b) — CC committed-band MEASURED RE-GROUNDING at MISO (the fallback lane)

Session miso-132, 2026-08-05, branch `claude/miso-132-backcast-calibration-d8gen8`,
off `origin/main` at `b4581c49`. Keeper at entry **`2026-08-04-miso-127-onlinepmin`**
(NOT-YET, sole FAIL C7 `COAL_PRB` 2025 `cv_ratio` 0.347 vs 0.50, ledgered caveats
2/3 {C3a, C3c}). Rule 22 `[R-HOLDOUT]`: MISO holds NO marker — **2023–2025 only**;
2022 / 2019 / 2026 are neither solved, scored nor read.

**Pushed BEFORE any adjudicating statistic of this lane.** The primary lane
(synchronized-reserve online-gating, `PREREG-miso132-synchronized-reserve-online-gating-2026-08-05.md`,
pushed `9a0033bb`) was **KILLED on its own pre-registered S-2 bar with zero solves**
(record `results/calibration/_miso132_online_gating_sizing.json`; the finding is
written in the same session). This document opens the **successor-2** lane —
miso-130 stamp (c) / miso-131 §3(b) — the only remaining named, un-adjudicated,
non-data-blocked item on §5.4.

**Fallback-trigger disclosure (rule 28(a) honesty).** The inbound handoff scoped
the fallback to "*if step-1 identification fails*". Step-1 identification did **not**
fail — it succeeded (the published reg+spin split is definitional and its MW measured
1,316/1,550/1,519 at July night, exactly the charter's claim). The lane died one step
later, on the ex-ante sizing screen. The fallback is invoked on that **KILL** rather
than on an identification failure, and it is invoked because successor 2 is the queue's
only remaining item — going off-queue would be worse. Stated, not slipped in.

---

## §0 Contamination disclosure

Everything read before writing this file: CLAUDE.md; §5.4 stamps miso-131/130/129;
the miso-130 and miso-131 findings; this session's own online-gating screen record;
`pipeline/backcast_config.py` (the `_MISO_OFFER_CURVE` and `CC_INTERMEDIATE` block
comments), `data/offer_curves.py::_markup_multiplier`, and
`data/raw/reference/miso_campd_marginal_hr_summary.csv`.

Numbers in hand, none of which size this lane: the C7 series 0.529/0.514/0.347 and
its ×1.447 reach; `R_tot` 0.952 / `R_dfrac` 0.354 (2025); the July night `COAL_PRB`
surplus +2,276/+2,204/+3,454 MW; the +$7.0–8.7 July-night price bias; miso-130 §3's
freeze statistic (55.4 % of the 2025 PRB econ ladder priced below the model's own July
night floor) and §4's note that ~0.3 GW of CC_REGULAR-routed committed prices within
$1 of the 2025 July night p50. **KILL-4 stands: nothing below is sized on any of them.**

---

## §1 IDENTIFICATION — one measurand, two ungrounded registered values

The measurand is the **min-load block's average burn relative to the plant's own base
heat rate**, measured on MISO's own CAMPD CEMS unit conduct by the repo's rule-23
derive (`scripts/data/derive_campd_marginal_hr.py --iso MISO`; provenance artifact
`data/raw/reference/miso_campd_marginal_hr_summary.csv`, 2023–2025 pooled,
cap-weighted):

| class | `base_hr` | `n_units` | `avg_committed_p50` | p25 | p75 |
|---|---:|---:|---:|---:|---:|
| **CC_REGULAR** | 7.436 | **103** | **1.005** | 0.951 | 1.057 |

The registered committed multipliers for the two cohorts the MISO CC fleet routes to
are **neither** that value:

* `_MISO_OFFER_CURVE["CC_REGULAR"]["committed"] = **1.20**`, resting on a generic
  "a CC's part-load $/MWh is ~30–40 % above its full-load SRMC" claim that **predates**
  this measured artifact. The same dict already carries `phys_committed: 1.005` — the
  measured value is *in the file*, used only as the `gas_offer_margin` markup basis
  (markup `max(0, 1.20 − 1.005) = 0.195`, ≈ $4.4/MWh at the ISO anchor), never as the
  band itself.
* `CC_INTERMEDIATE["committed"] = **0.92**` — the generic default carried by the
  cohort `cc_intermediate_split` routes MISO's baseload CCs to. `backcast_config.py`'s
  own comment calls the 0.92 block "**an unphysical, artificially-cheap min-load
  block**".

Both are the **same physical quantity on the same 103 measured CC units** — the split
is a *duty-cycle routing*, not a different measurand. `CT_PEAKER`'s committed band is
already grounded on its own measured value (1.025 = registered = `phys`, markup 0);
CC's is not.

**The action is a rule-14 `[R-ACCURATE]` proxy-for-measurand swap with ZERO free
parameters: both committed bands → the measured 1.005.** No value is chosen, swept,
or fitted; 1.005 is read off a committed artifact that re-derives only on source-data
updates (rule 23 `[R-FROZEN-DERIVE]`).

**Both keys move together, and that is deliberate.** Moving only `CC_REGULAR`
(cheaper) or only `CC_INTERMEDIATE` (dearer) would be choosing the direction — the
forbidden path. One measurand, one mechanism, both cohorts (rule 19 `[R-ONE-MECH]`).

---

## §2 PRE-CHECK — descriptive, ONE inertness bar

Probe `scripts/probes/_miso132b_cc_committed_precheck.py`, record
`results/calibration/_miso132b_cc_committed_precheck.json`. No LP; the fleet is
assembled at HEAD under the keeper's committed config and each cohort's committed
tranches are priced at their July basis, then compared with the keeper's own solved
July night prices.

Reported (descriptive, **no bar**, so they can never be read as adjudicating):

* capacity in each cohort's committed band, per year;
* each cohort's committed offer $/MWh before and after the swap, against the keeper's
  own July night p10 / p50;
* the resulting **net** capacity re-priced up vs down.

**The one gating bar — INERTNESS (`P-0`).** If the combined committed capacity of the
two cohorts is **< 200 MW** in every year, the swap cannot move a price and two arms
of solve are not spent: the lane is recorded INERT and stops. This is a
worth-the-compute bar, not a lever screen — **it cannot pass/fail the mechanism**,
whose admissibility is settled by rule 14 alone.

**Two-sided prior, declared now.** The honest prior is that the swap's **net** effect
on the July night clearing is **UP**, not down: `cc_intermediate_split` is armed and
MISO's CC fleet is described in-code as entirely baseload, so the **bulk** of CC
capacity sits in the `CC_INTERMEDIATE` cohort moving **0.92 → 1.005 (dearer)**, while
only the smaller `CC_REGULAR`-routed cohort moves **1.20 → 1.005 (cheaper)**. A higher
overnight floor would move C7 the **wrong** way (miso-130 §3: a higher floor freezes
*more* of the cheap PRB ladder out of the diurnal wave). **That outcome is
pre-accepted**: under rules 1 and 14 the accurate input stays in and the worsened fit
is a *discovered bug* pointing at the real root cause — it is **not** grounds to
revert to 0.92/1.20, and the reverse (a C7 gain) is **not** by itself grounds to
promote.

---

## §3 THE ARM

Produced through the **registered override channel**, never a bare code edit (the
miso-122 reproducibility seam): `replay_keeper.py --offer-curve-json`, which
deep-merges onto the calibrated curve so only the named band changes and the resolved
curve is recorded verbatim in the bundle's `run_config.json`
(`scenario_config.offer_curve_by_group`) — rule 26 `[R-REGISTRY]` satisfied.

```
{"CC_REGULAR": {"committed": 1.005}, "CC_INTERMEDIATE": {"committed": 1.005}}
```

`phys_committed` is untouched (1.005 on `CC_REGULAR`; absent on `CC_INTERMEDIATE`,
which the `_markup_multiplier` identity default makes markup-neutral), so under the
keeper's armed `gas_offer_margin` **both** bands land at markup 0 — the measured
block-average burn with no adder. No new `ScenarioConfig` field is created, so rule
28(c) adds no row; rule 28(b) still requires this session to stamp the
`offer_curve_by_group` cell and §5.4.

**A/B protocol.** Same-HEAD **zero-delta control arm A first** (miso-124: never against
the committed keeper), then arm B. Both:
`scripts/replay_keeper.py results/calibration/miso127_onlinepmin_B --years 2023 2024 2025`
in **ONE invocation per arm** (a per-year chain records only the last year in
`meta.json`). Arms **sequential** (rule 12). Arm A is bit-for-bit HEAD-identical to
arm B because arm B carries **no code change at all** — only the override JSON.

### KILLS — pre-registered, in order

| id | gate | KILL condition |
|---|---|---|
| **K0** | control integrity | arm A must reproduce the incumbent keeper's scorecard **and** its committed hourly sidecars (caiso-146: a zero-delta control has diverged before). A diverging control invalidates every Δ. |
| **K1** | flag fidelity / single delta | arm A records the keeper's `offer_curve_by_group`; arm B differs in **exactly** the two `committed` entries and nothing else. |
| **K2** | year span | both bundles `[2023, 2024, 2025]` (rules 16 / 22). |
| **K3** | liveness (grain 2) | per-class **ENERGY** deltas are the magnitude of record (miso-122: `max_abs_class_hour_mw` is not a mechanism magnitude at MISO). Bar: `abs(Δ CC class energy) > 0.05 TWh` in ≥ 1 year. A null here is a **wiring defect to find**, not an `I` verdict — the pre-check will already have shown the bands exist. |
| **K4** | **C1 16/16** | C1 must stay 16/16. |
| **K5** | **`COAL_BIT` no-overshoot** (miso-102 signature) | KILL if `COAL_BIT` off-peak `cv_ratio` exceeds **1.60** in any year, or its C7 status regresses PASS→FAIL. |
| **K6** | **full-balance identity** (miso-126(b)) | `d_class + d_discharge − d_charge + d_slack − d_dump − d_demand == 0`, every year, across the full sidecar set. |
| **K7** | **`R_tot` floor 0.90** (miso-131 P3 convention) | `COAL_PRB` `R_tot` ≥ 0.90 in all three years. A `cv_ratio` move bought by inflating raw off-peak dispersion is not an organisation gain. |
| **K8** | **LOYO within 2023–2025** | scored leave-one-year-out; a verdict carried by one year, or a PASS→FAIL flip in a currently-passing year, is overfitting. |
| **K9** | no forced energy | the arm changes a PRICE, not a floor: KILL if D-2 shows a new forcing id or any class's forced share rises. |

### TARGET and REPORTING

**C7 `COAL_PRB` `cv_ratio` via `R_dfrac`** (quote `R_dfrac`, never raw variance), with
the July-night price bias and the miso-130 freeze share reported alongside as the
mechanism's own channel. `R_dfrac` and the price channel are reported **whatever their
sign**.

### KEEPER DECISION RULE, declared before the numbers

Promotion is on **structural fidelity, never score** (rules 1/14; owner guidance
2026-08-05). Arm B replaces two ungrounded multipliers with the fleet's own measured
value, so it is the more faithful configuration by construction. Therefore:

* if K0–K2, K6 and K9 hold, arm B **may be promoted even if a scored gate regresses** —
  including C3a, whose annual mean is expected to move as the overnight level moves,
  the rule-14 compensating-error signature against the C3c-ledgered missing peak;
* a `cv_ratio` gain achieved with a **failed** K4/K5/K7 is **refused** — the right
  number by a wrong route is not a keeper;
* a regression is **reported**, and is **not** grounds to revert to 0.92/1.20 (rule 14
  forbids burying the error back in the proxy). If arm B is not promoted, the keeper's
  ungrounded committed band is recorded as an **open root-cause issue**, not a settled
  parameter.

### KILL-4

Nothing is sized on any Δ measured in this session. If arm B underperforms, the
response is a finding — **not** a sweep of the committed multiplier, not a
cohort-selective application, not a window narrowed onto the residual.

## §4 DO-NOT-REDO honoured

Unchanged and untouched: granularity / `offer_curve_smoothing_n` (miso-131, inert at
class grain); the take-or-pay family; regulated self-commitment forcing;
`coal_tranche_*_frac`; within-band slope (premise false); the seam price/ceiling/floor
classes; trough-marginal-unit **volume** (miso-115 — this lane changes a committed
band's **price**, not the trough's marginal-unit sizing); the coal night floor;
`gas_commitment_bridge` (cell stays `U`). No fitted trough adder. No 2025-specific
lane — the swap is armed identically in all three years.

Next number after this session: **miso-133**.
