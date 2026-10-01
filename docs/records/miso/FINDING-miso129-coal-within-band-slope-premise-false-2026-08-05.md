# FINDING — miso-129: MISO's coal offer band ALREADY has a within-band incremental cost slope — miso-128's named object does not exist, and the real defect is the ladder's GRANULARITY

**Date:** 2026-08-05 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry and exit:** **`2026-08-04-miso-127-onlinepmin` — UNCHANGED**
(`results/calibration/miso127_onlinepmin_B`), determination **NOT-YET**, sole
FAIL **C7 `COAL_PRB` — 2025 only** (cv_ratio 0.347 vs the 0.5 gate), ledgered
caveats 2/3 {C3a, C3c}, `audit_keepers --iso MISO` 0/0.

**NO LP SOLVED. NO DERIVE RUN. NO ARM BUILT. NO MECHANISM ARMED. NO
`ScenarioConfig` FIELD ADDED. NO KEEPER MOVED. NO RUN REGISTERED** — the
pre-registration's §3 **P1 premise check fired its declared kill on the very
first statistic**, before the derive it would have licensed. Rule 15
`[R-DASHBOARD]` is satisfied by this statement: **this was a no-LP phase and it
produced no run.**

**Pre-registration:**
`results/calibration/PREREG-miso129-coal-within-band-incremental-slope-2026-08-05.md`,
committed and pushed at `ec5323a4` **before any adjudicating statistic, any
derive output and any arm**, with §1 disclosing in full every structural fact
read first — including that `data/raw/reference/miso_campd_marginal_hr_summary.csv`
was **not opened**.
**Probe:** `scripts/probes/_miso129_coal_within_band_slope.py`.
**Record:** `results/calibration/_miso129_coal_within_band_slope.json`.

Rule 22 `[R-HOLDOUT]`: 2023–2025 only — MISO holds no `calibration-complete`
marker, so no out-of-training year was solved, scored **or read**.

**Off-queue by necessity (rule 28(a)), and it says so.** `docs/mechanism-testing-matrix.md`
§5.4's miso-128 QUEUE STAMP records that MISO has **no named, un-adjudicated,
non-data-blocked queue item**. This lane took the one object miso-128 **NAMED BUT
DID NOT CHARTER** (§6.4). It did not survive its own premise.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **P1** | does MISO's coal offer band lack a within-band incremental cost slope? | **48 / 48 coal plants, 38,144.8 MW — cap share bidding ONE econ price 0.0000; cap share LADDERED 1.0000.** Every plant's econ band is **6 distinct rising prices** | **PREMISE FALSE — LANE DIES** |
| **P0** | does this session reproduce D-1's actual-side amplitude-vs-loading fit? | slope **+0.0558** (bar +0.0558 ± 0.005), wR² **0.429** (bar 0.429 ± 0.05), n = 92 | **PASS — construction valid** |
| P2 / P2b / P3 / P4 | the identification screens | **NOT RUN** — P1's falsifier kills the lane before the derive | *not reached, by design* |
| **OBS** | is the ladder's granularity commensurate with the amplitude D-1 gates? | cap-wtd econ step **72.6 MW** vs cap-wtd measured amplitude **90.4 MW**; cap-wtd **median** plant ratio **1.175**; **41.4 %** of coal capacity has its whole measured diurnal swing **inside one step** | **NAMED, NOT CHARTERED** |

---

## §1 — P1: the premise is false, at both grains

miso-128 §6.4 named the object as:

> "the model's coal offer band has no **within-band incremental cost slope**. Each
> CAMPD bin bids **one price**, so a plant is bang-bang in whichever band is
> marginal and **saturates flat** once loading clears a step."

**It bids nine prices, not one.**

**Grain 1 — config resolution (no LP, no fleet).** Under the keeper's own
committed config:

| field | value |
|---|---|
| `offer_curve_smoothing_n` | **6** (and this is the field's own `scenarios.py` **default**) |
| `offer_curve_smoothing_exp` | **1.0** — a straight linear ramp |
| `offer_curve_smoothing_mid` | `None` |
| `offer_curve_by_group["COAL_PRB"]` | `{committed 1.0, econ_low 1.0, econ_high 1.19, peak 1.48, econ_low_share 0.556}` |
| `econ_split_by_group` | `{}` (empty — the `offer is not None` limb is the one taken) |

`market_sim.data.offer_curves._econ_curve_steps` — reached from
`fleet/assembly.py::bins_to_fleet` — slices the econ ramp into `n_curve` equal-capacity
sub-tranches whose heat-rate multiplier rises `econ_low → econ_high` along
`mult(t) = lo + (pk − lo)·t^exp`. **Its own docstring says `exp == 1` is "a
straight (linear) ramp matching a thermal unit's gently-rising incremental heat
rate", and the enclosing comment says the plant then loads "gradually as hourly
price crosses MC, rather than snapping between two wide flat blocks".** The
mechanism miso-128 named as missing is not merely present — it is the documented
purpose of code that has been armed on this keeper all along.

**Grain 2 — the assembled fleet (the miso-126(a) duty, measured not asserted).**
The real MISO **2025** dispatch fleet built at HEAD under the keeper's committed
config, through the **CAMPD limb** (`fleet_to_bins` → `build_base_fleet` →
`build_dispatch_fleet`); `split_coal_tranches` is inert by wiring at MISO
(miso-128 §4) and is evidence of nothing here:

| statistic | value |
|---|---|
| coal plants assembled | **48** |
| total coal LP capacity | **38,144.8 MW** |
| capacity share with **one** econ price | **0.0000** |
| capacity share **laddered** (> 1 econ price) | **1.0000** |
| distinct econ marginal costs per plant | **6 for all 48 plants** (no exceptions) |
| distinct whole-plant marginal costs | 7 (3 plants) / **8 (36 plants)** / 9 (9 plants) |
| LP tranches per plant | 7 (3) / 8 (1) / **9 (44)** |
| cap-wtd econ HR max/min | **1.1341** (min 1.0073, max 1.1559) |
| `COAL_PRB` — the gated class | **34 plants / 27,973.1 MW, all laddered, econ HR ratio 1.1559 uniform** |

A representative plant (1733, 3,066 MW, PRB — one of the ten miso-128 measured
going *newly flat at higher loading* in 2025) assembles as
`mustrun, committed, econc00…econc05, peak`: **nine tranches, eight distinct
prices, spanning heat rate 10.74 → 15.90 (1.48×).**

**Pre-registered adjudication.** P1's falsifier: "if the econ band already
resolves to `n > 1` rising sub-tranches for ≥ 50 % of MISO coal capacity → the
premise is FALSE, the lane dies here with zero derive output and zero solves."
The measured share is **100.0 %**. **The lane dies. The derive was never run and
no `ScenarioConfig` field was added.**

**P0 — the construction is valid.** Before any comparison, this session
reproduced miso-128's own actual-side fit from the committed bench on the same
construction: `std_frac = +0.0558 × cf_off + 0.0289`, wR² **0.429**, n **92** —
**identical to three decimals** on slope and wR². Whatever else this session
says, it is not saying it on a different construction.

---

## §2 — what was actually wrong with the named object, and it is a distinction that matters

miso-128's §6.4 reasoning was: *the newly-flat set sits at HIGHER loading than
the varying set, which is a saturation signature, so the band must have no slope.*
**The inference from the signature to the cause does not hold, and this is the
generalisable lesson.** A saturation signature is produced by a step of *any*
width. It says a plant is parked between prices; it does **not** say there is only
one price. Reading "flat at higher loading" as "no slope" skipped the
construction check that would have distinguished a **missing** ladder from a
**coarse** one — and the two have completely different successors.

The phenomenon miso-128 measured is **real and unchanged**: 10 plants / 11,958 MW
newly flat in 2025, nine of ten while model loading rises; 59.4 % of 2025 PRB
nameplate flat against reality's 12.3 %; `R_dfrac` 0.354. Nothing here retires
any of that. **What is retired is the stated cause.**

---

## §3 — OBS: the ladder exists, and its step is the same size as the swing being gated

Reported as an **observation only**. PREREG KILL-5 forbids manufacturing a
successor and rule 19 `[R-ONE-MECH]` forbids stacking one, so this is written
down for the next session **exactly as miso-128 §6.4 wrote down this lane's
object — NAMED, NOT CHARTERED.**

Both quantities in **MW**, denominator-free: the measured amplitude is normalised
by bench nameplate while the LP step is a share of assembled LP capacity, and
those denominators are not the same number.

| statistic | value |
|---|---|
| cap-wtd econ **step width** | **72.6 MW** |
| cap-wtd **measured** off-peak diurnal amplitude | **90.4 MW** |
| ratio of the cap-wtd aggregates | 1.245 |
| cap-wtd **median** per-plant ratio | **1.175** |
| cap-wtd **mean** per-plant ratio | 2.228 |
| **capacity share whose amplitude is smaller than ONE step** | **0.4138** |

**Reality's entire off-peak diurnal swing is about the size of one model econ
step, and for 41.4 % of MISO's coal capacity it is smaller than one step.** A
plant parked mid-step is flat to every price move narrower than a step — which
reproduces miso-128's saturation signature without requiring a missing slope.

**The mean and the median are both reported and neither may be quoted alone**
(miso-127's gross/net duty applied to a ratio): the cap-wtd **mean** of per-plant
ratios is 2.228 but the cap-wtd **median** is 1.175, because plants with small
econ bands Jensen-inflate the mean. The median and the sub-one-step capacity
share are the honest statistics.

**Three things a successor would have to establish, none of them established
here:** (a) that the granularity, not something else, is what carries `R_dfrac`;
(b) an identification for `offer_curve_smoothing_n` that is **not** the C7
residual — it is presently an unidentified discretization count sitting on the
gated mechanism, which is a **rule 21 `[R-DOF]` question in its own right**, and
sweeping it against C7 is the forbidden fitted path (rules 1 / 24); (c) that a
finer ladder does not simply re-spend `R_tot`, which is already at **0.952** and
has no room (miso-128's binding consequence, and it binds this observation too).

---

## §4 — a rule-28(c) gap, filed and closed in this session

**`offer_curve_smoothing_n` had ZERO mentions anywhere in
`docs/codebase-site/data/mechanism-matrix.js`** — a solve-affecting
`ScenarioConfig` field, armed at 6 on the MISO keeper, **construction-proven to
shape 100 % of MISO's coal offer band**.

**And it is a sharper instance than a plain absence, because its own two
modifiers ARE registered.** The `offer_curve_by_group` row's `def` already
carries `offer_curve_smoothing_mid :8876` and `offer_curve_smoothing_exp :8867`
— the anchor and the exponent that *shape* the ramp — while the field that
decides whether the ramp **exists at all** (`n = 0` ⇒ two flat blocks;
`n > 0` ⇒ an `n`-step ladder) is absent. A reader of that row sees the smoothing
family named twice and reasonably concludes it is covered. **This is the
caiso-161 §2 / nyiso-121 defect in a new variant: not a stale anchor and not a
wrong-row mention, but a registered *modifier set* standing in for an
unregistered *switch*.**

It is a **shared-stem** field (not `miso_*`), so it belongs to the cross-ISO
shared-stem backlog nyiso-121 named as the only remaining rule-28(c) debt — and
it is load-bearing on the class carrying MISO's sole failing criterion.

**The field is registered literally on the existing `offer_curve_by_group` row in
this session** (rule 28(b): the session that tests a mechanism stamps its cell),
as a sub-scalar of that family rather than a new row — the same convention
`coal_mustrun_online_pmin` follows on `coal_mustrun_per_plant`, and the one
nyiso-121 demanded ("register these fields on rows, not enumerate them in
prose"). **No cell moves:** the row is already `KKKKKK` and this session
confirms MISO's `K` at the construction grain rather than changing it. Per
rule 28(d) nothing is inferred for another ISO — the field's default of 6 means
it is very likely armed on every keeper, but that is an inference, not a
measurement, and only MISO's was taken.

---

## §5 — what this changes for the next session

1. **`coal_within_band_incremental_slope` must never be chartered at MISO.** The
   mechanism exists, is armed, and shapes 100 % of the coal band. Adding one
   would be a rule 19 `[R-ONE-MECH]` duplicate of `offer_curve_smoothing_n`.
2. **Do not re-open miso-128 §6.4's object.** It is adjudicated PREMISE-FALSE at
   two grains on 100 % of capacity. Its *phenomenon* stays real; its *stated
   cause* is dead.
3. **The refined object is GRANULARITY, and it is NAMED, NOT CHARTERED** (§3),
   with its three prerequisites stated so a successor is pre-registered against
   them rather than discovering them. It is **not** licensed by this finding.
4. **A structural lesson worth carrying beyond MISO:** a *signature* is not a
   *cause*. miso-128 inferred "no slope" from "flat at high loading" without a
   construction check; the construction check costs one fleet assembly and no LP,
   and it inverted the conclusion. **Check the construction before naming the
   defect** — the miso-126(a) two-grain duty applied to a *premise*, not just to
   a lever.
5. **The two bounded non-solve steps in §5.4 are unchanged** and neither is
   touched here: item 1's Form 580 tonnage count (a sourcing pass) and carrying
   miso-127 §1.3's headroom numbers into that ask.

**Carried DO-NOT-MISREADs, applied and not quietly dropped.** *miso-128:*
`R_tot` is already 0.952 — §3 explicitly states that a finer ladder must not be
proposed as an amplitude buy. *miso-128:* no absolute-amplitude figure is quoted
as a C7 result; §0 and §3 report absolute MW and the ratio together, and §1
quotes `R_dfrac` where the gate is concerned. *miso-127:* every aggregate is
decomposed before any claim — the OBS ratio is reported as mean **and** median
**and** capacity share, and the P1 census is per-plant (48 rows) before any
capacity share is taken. *miso-126(a):* the premise is proven at two grains, and
the CAMPD limb — not `split_coal_tranches` — is what was instrumented.
*miso-121:* this finding measures **construction and dispatch shape**, never
marginality or price; no number here is quoted as a price result. *miso-122:* no
`max_abs_class_hour_mw`-style statistic is used as a magnitude.

## §6 — reproduce

```
uv run python scripts/probes/_miso129_coal_within_band_slope.py
```

No LP, no bundle, no network; reads the committed bench and keeper sidecar plus
one HEAD fleet assembly for P1 grain 2. Writes
`results/calibration/_miso129_coal_within_band_slope.json`.
