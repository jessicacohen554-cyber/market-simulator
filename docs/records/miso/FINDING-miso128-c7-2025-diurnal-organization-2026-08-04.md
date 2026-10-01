# FINDING — miso-128: MISO's 2025-only C7 failure is one dimension, not one year — and the last named lever is inert by wiring

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry and exit:** **`2026-08-04-miso-127-onlinepmin` — UNCHANGED**
(`results/calibration/miso127_onlinepmin_B`), determination **NOT-YET**, sole
FAIL **C7 `COAL_PRB` — 2025 only**, ledgered caveats 2/3 {C3a, C3c}.

**NO LP SOLVED. NO ARM BUILT. NO MECHANISM ARMED. NO KEEPER MOVED. NO RUN
REGISTERED** — the pre-registration's §3 P10 successor screen fired its declared
default (rule 15 is satisfied by this statement, not by a registration).

**Pre-registration:**
`results/calibration/PREREG-miso128-c7-2025-diurnal-organization-2026-08-04.md`,
committed and pushed at `010e22ba` **before** any adjudicating statistic, with
§0 disclosing in full every number already measured in exploration.
**Probe:** `scripts/probes/_miso128_c7_diurnal_organization.py`.
**Record:** `results/calibration/_miso128_c7_diurnal_organization.json`.

Rule 22 `[R-HOLDOUT]`: 2023–2025 only — MISO holds no `calibration-complete`
marker, so no out-of-training year was solved, scored **or read**.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **P1** | does the construction reproduce the gated statistic? | cv_ratio 0.512/0.525/0.345 vs the committed 0.514/0.529/0.347; max err **0.004** vs a 0.02 bar | **PASS** |
| **P2** | does the uint8 payload grain agree with the unquantized parquet? | profile r **0.99999/0.99999/1.00000**; CV rel-diff 3.2/2.4/2.1 % vs a 10 % bar | **PASS** |
| **P3** | is the flat-plant census above the quantization floor? | noise **0.000151** of nameplate = **1.5 %** of the 1 % threshold, bar 5 % | **PASS** |
| **P4** | does `R_tot × R_dfrac × R_level` equal cv_ratio? | max rel err **< 1e-6** | **PASS** |
| **P5** | is 2025's failure a single-factor move? | `R_tot` **0.877→0.952** (up), `R_level` 1.091→1.025 (down), `R_dfrac` **0.549→0.354** (0.64×, bar 0.80×) | **PASS — one factor** |
| **P6** | is the absolute amplitude deficit non-increasing? | MW **1145→858→800**; ÷level **0.0812→0.0629→0.0488**; ΔCV **0.0755→0.0576→0.0482** | **PASS — R′ holds 3/3** |
| **P7** | is the defect specific to the diurnal dimension? | non-diurnal ratio **0.825/0.808/0.829** (drift 0.021) vs diurnal **0.473/0.483/0.315** (drop 0.168) | **PASS** |
| **P8** | do the control coal classes collapse too? | `COAL_BIT` R_dfrac 0.506→**1.111** (*rises*); `COAL_LIGNITE` 0.920→0.424 | **mixed — NOT fleet-wide** |
| **P9** | is `coal_tranche_1/2/3_frac` reachable on MISO's path? | 2,923 generators, **max \|Δpmax\| = 0.0 MW, max \|Δfuel_frac\| = 0.0, 0 elements changed** under a 0.30/0.25/0.45 → 0.10/0.15/0.75 perturbation | **INERT BY WIRING at MISO** |
| **P10** | does any candidate clear the four-part successor screen? | none — every candidate fails ≥1 of {closed-family, residual-free identification, proven wiring, targets `R_dfrac`} | **NO ARM SOLVED** |

---

## §1 — the decomposition: C7 is one dimension, and 2025 is its projection

D-1's gated statistic is the ratio of two off-peak CVs taken on the **hour-of-day
mean profile** over h0–h14 (`legitimacy_diagnostics.d1_shape_metrics`). Because
`cv = prof_std / mean` and `prof_std = tot_std × dfrac`, where
`dfrac` is the share of a series' off-peak dispersion that is diurnally
organised, the gate factors **exactly**:

> `cv_ratio = R_tot × R_dfrac × R_level`

| year | `R_tot` total dispersion | `R_dfrac` diurnal organisation | `R_level` | **cv_ratio** | gate 0.5 |
|---|---|---|---|---|---|
| 2023 | 0.907 | 0.524 | 1.077 | 0.512 | pass |
| 2024 | 0.877 | 0.549 | 1.091 | 0.525 | pass |
| 2025 | **0.952** | **0.354** | **1.025** | **0.345** | **FAIL** |

**Two of the three factors improve into 2025 and one collapses.** The model's
total off-peak dispersion reaches **95 % of reality's — its best year of the
three** — and its level error nearly closes (`R_level` 1.091 → 1.025, i.e. the
model was 1,140 MW light on the 2024 off-peak mean and only 399 MW light in
2025). The entire failure is `R_dfrac`: the model carries **as much off-peak
variability as reality does and organises almost none of it by hour of day**.

**This is not a defect of dispatch variability.** Any successor that adds
variability without organising it hour-of-day cannot move the gate — the room
for that is already spent.

---

## §2 — the defect is year-invariant; only the denominator moved (R′)

**P6, three independent normalisations, all monotone the same way.** The model's
absolute amplitude deficit on the class off-peak profile:

| measure | 2023 | 2024 | 2025 |
|---|---|---|---|
| `std_a − std_m` (MW) | 1,145.2 | 858.4 | **800.3** |
| that ÷ the actual off-peak mean | 0.0812 | 0.0629 | **0.0488** |
| `cv_a − cv_m` | 0.0755 | 0.0576 | **0.0482** |

On every absolute measure **2025 is the model's best year**, and on the ratio
form it is its worst. That is not a contradiction — it is what a ratio does when
its denominator falls faster than its numerator's shortfall. Actual off-peak CV
fell 0.155 → 0.121 → 0.074; the model's absolute gap to it closed the whole time.

**P7 isolates the dimension, with outages removed from both sides.** Restricting
to fully-online days (every off-peak hour above 5 % of nameplate, per plant, per
side), model ÷ actual:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **non-diurnal** (day-to-day) dispersion | 0.825 | 0.808 | **0.829** |
| **diurnal** amplitude | 0.473 | 0.483 | **0.315** |
| level | 1.015 | 0.941 | 0.972 |

The non-diurnal ratio is flat to **±0.021** across three years while the diurnal
ratio drops **0.168**. On the same plants, on the same days, at the same level,
the model reproduces **83 %** of reality's day-to-day coal variation in every
year and its hour-of-day amplitude alone degrades.

**P8 says it is not a coal-fleet-wide effect.** `COAL_BIT`'s `R_dfrac` moves the
**other** way in 2025 (0.506 → **1.111** — the model becomes *more* diurnally
organised than reality); `COAL_LIGNITE` collapses (0.920 → 0.424) but is
immaterial (0.9–1.1 % of ISO load, under the 2 % gating floor). The object is
`COAL_PRB`-specific, which matches every prior MISO coal finding.

---

## §3 — what 2025 actually is: a driver the model reproduces, and over-responds to

The brief asked for the driver of the *measured* collapse before any theorising.
It is the gas price, and it is in the keeper's own committed flags:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| MISO gas, `calibration_flags.gas_prices` ($/MMBtu) | 2.54 | 2.19 | **3.52** (**+61 %**) |
| matched-`COAL_PRB` off-peak mean, **actual** (MW) | 14,108 | 13,654 | **16,392** (**+20.1 %**) |
| same, **model** (MW) | 13,094 | 12,514 | **15,993** (**+27.8 %**) |

Coal loaded up on both sides because gas got expensive; a more inframarginal
fleet cycles less, which is why **reality's** off-peak CV is lowest in 2025 too.
**The model reproduces the driver in direction and roughly in size** — it
over-responds by about a third (+27.8 % vs +20.1 %), which is what closes its
standing level shortfall.

So the answer to "does the model's 2025 CV fall for a different reason than
reality's?" is **partly — and the difference is measurable**. Both fall for the
same driver. Reality's fall is mostly the level rise with its amplitude
comparatively protected; the model's is the level rise **plus** a diurnal-
organisation collapse reality does not have.

**Why the model's amplitude is not protected**, measured across all 92 plant-years,
capacity-weighted least squares of per-plant off-peak amplitude on per-plant
off-peak loading:

| side | fit | weighted R² |
|---|---|---|
| **actual** | `std_frac = +0.0558 × cf_off + 0.0289` | **0.429** |
| **model** | `std_frac = −0.0028 × cf_off + 0.0250` | **0.003** |

Reality's coal plants swing **more** in absolute terms when they are loaded
harder; the model's per-plant amplitude is a near-constant ~2.5 % of nameplate
that does not respond to loading at all. In a year when loading rises 20–28 %,
reality's amplitude is partly carried by that positive slope and the model's is
not. **That is the mechanism-level statement of the 2025 residual.**

**The flat-plant census makes it concrete.** Plants whose off-peak profile
amplitude is under 1 % of nameplate (P3 puts the quantization floor 66× below
that threshold):

| year | actual | model |
|---|---|---|
| 2023 | 0 / 31 plants, **0.0 %** of class nameplate | 10 / 31, 26.0 % |
| 2024 | 3 / 31, 7.5 % | 11 / 31, 27.4 % |
| 2025 | 4 / 30, **12.3 %** | **17 / 30, 59.4 %** |

**Ten plants / 11,958 MW go newly flat in the model in 2025, and nine of the ten
do so while their model loading RISES** (e.g. 1733: `cf_off` 0.421 → 0.616,
amplitude 0.0232 → 0.0095; 6664: 0.468 → 0.721, 0.0489 → 0.0042). The model's
2025 flat set sits at **higher** loading than its varying set (cap-weighted
`cf_off` 0.534 vs 0.440) — the saturation signature. Their **measured**
counterparts are not distinguishable: the flat set's *actual* amplitude is
0.0410 of nameplate against the varying set's 0.0401. **Reality does not go flat
where the model does.**

---

## §4 — P9: the last named lever is inert by wiring at MISO

The session brief named one open lever, and miso-127 §4 recorded it as the
standing DOF debt on this mechanism: `coal_tranche_1/2/3_frac` (0.30/0.25/0.45),
declared in `scenarios.py` as "calibrated to EIA-930 2023–2024 hourly **ERCOT**
coal dispatch", flagged residual-identified with open issue **#1336** — an
apparent live rule-25 `[R-ISO-SCOPE]` breach sitting directly on the C7
mechanism.

**It is not a MISO tuning channel at all.** Proven at two grains before any
solve (the miso-126(a) duty), with no LP built:

* **Grain 1 — construction, measured not asserted.** MISO's own fleet synthesis
  under the keeper's committed config produces a **non-empty** `campd_bins`
  frame (**423 rows**, from `thermal_tranches_MISO.csv` via `fleet_to_bins`).
  `fleet/assembly.py::build_dispatch_fleet` branches on
  `if campd_bins is not None:`, and `split_coal_tranches` — the **sole** consumer
  of the fractions outside probe scripts (`data/offer_curves.py:70-72`) — exists
  only in the `else` limb. MISO takes the CAMPD limb, whose per-bin fuel
  fractions come from `campd_tranche_fuel_frac`.
* **Grain 2 — measurement.** The real MISO 2025 dispatch fleet assembled twice
  at HEAD under the keeper's own config, once committed and once with the
  fractions perturbed to **0.10 / 0.15 / 0.75** — a materially different split of
  the same total, chosen so a null cannot be a degenerate perturbation.
  **2,923 generators; `max |Δpmax_mw| = 0.0`, `max |Δfuel_fracs| = 0.0`, 0
  elements changed on either vector.**

> **`coal_tranche_1/2/3_frac` is INERT BY WIRING at MISO.** Issue **#1336 is a
> split-fleet-ISO debt, not a MISO one**, and there is no rule-25 breach at MISO
> to repair: MISO's coal tranche split comes from `thermal_tranches_MISO.csv` —
> **MISO's own measured CAMPD conduct** — which is exactly what miso-127 promoted
> a selector between two columns of.

This is a zero-solve kill on a pre-registered property, the miso-127 Lane A
pattern. **DO NOT charter a `coal_tranche_*_frac` re-derive as a MISO lane.**
The #1336 debt remains open and real for the ISOs that take the `else` limb, and
belongs to one of their sessions (rule 25 `[R-ISO-SCOPE]`).

---

## §5 — P10: no arm was solved, and that was the pre-registered default

The pre-registration required a candidate to clear **all four** screens before
any arm: (1) not in a closed family, (2) identification that is not the C7
residual, (3) proven wired into MISO's solve path at two grains, (4) targets
`R_dfrac` specifically. Against the record:

* the take-or-pay **period-budget** family — **closed by proof** (miso-127 §1.2:
  volume neutrality and non-inertness are mutually exclusive);
* take-or-pay **removal** — **R twice**, structurally (miso-102);
* the **regulated-self-commitment forcing** family — **closed** (miso-111 R /
  112 R / 113 I, confirmed 114), and rule 19 `[R-ONE-MECH]` forbids a fourth;
* **receipts-derived tonnage** in any variant — **refuted** (miso-103);
* `coal_mustrun_online_pmin` — the freshly-promoted keeper mechanism, **out of
  scope by pre-registration** (P11) and by the brief; it has zero free
  parameters and re-sizing it against one year is the forbidden fitted path
  (rules 1 / 24);
* `coal_tranche_*_frac` — **fails screen 3**, §4.

`docs/mechanism-testing-matrix.md` §5.4 independently records that MISO has no
named, un-adjudicated, non-data-blocked queue item. **Nothing cleared the screen,
so nothing was solved** — and no successor was manufactured, because rule 19
forbids it and PREREG KILL-4 forbids sizing anything on any Δ measured here.

---

## §6 — what this changes for the next session

1. **Retire "2025 is different" as a lane.** There is no 2025-specific dispatch
   driver to hunt. §1 and §2 establish a **year-invariant, single-dimension**
   defect — the hour-of-day organisation of `COAL_PRB`'s off-peak output —
   projected onto a denominator that fell for a driver (gas +61 %) the model
   reproduces. A session that goes looking for what broke in 2025 will find
   nothing, because nothing did.
2. **The gate is still the gate, and the defect is still real.** C7 FAILS on
   2025 and the determination stays **NOT-YET**. R′ says the ratio form is
   scale-sensitive; it does **not** say C7 is "really" passing. The underlying
   deficit — the model carries **under half** of reality's diurnal coal
   amplitude in **every** year, and 59.4 % of its 2025 PRB nameplate is flat
   against reality's 12.3 % — is unfixed and is what a successor must attack.
3. **The target statistic for any successor is now stated and measured**, so it
   can be pre-registered against rather than discovered: reality's per-plant
   off-peak amplitude rises with loading at **+0.0558 per unit CF (wR² 0.43)**;
   the model's slope is **−0.0028 (wR² 0.003)**. A mechanism that does not put a
   **positive** slope there cannot move `R_dfrac`, and `R_tot` is already at
   0.95 so there is no room to buy the gate with more variability.
4. **The one structural reading this leaves open, NAMED and NOT CHARTERED**
   (rule 19 `[R-ONE-MECH]`; it is not a successor until someone identifies it
   from data): the model's coal offer band has no **within-band incremental cost
   slope**, so a plant's dispatch is bang-bang in whichever band is marginal and
   saturates flat once loading clears a step — which is precisely what §3's
   newly-flat-at-higher-loading set shows. Its identification source would have
   to be MISO's **own** measured unit-level incremental heat rate versus load,
   and it would need its own pre-registration, its own derive, its own two-grain
   wiring proof and a leave-one-year-out before any promotion. It is written down
   here so it is not re-derived from scratch; it is **not** licensed by this
   finding.
5. **The two bounded non-solve steps in §5.4 are unchanged** and neither is
   touched here: item 1's Form 580 tonnage count (a sourcing pass) and the
   headroom numbers miso-127 §1.3 asked to be carried into that ask.

**Carried DO-NOT-MISREADs, applied and not quietly dropped.** miso-121: this
finding measures **dispatch shape**, never marginality or price, and no number
here is quoted as a price result. miso-122: no `max_abs_class_hour_mw`-style
statistic is used as a magnitude. miso-127: every aggregate in §3 is decomposed
to plant grain before any inertness or materiality claim — the flat census and
the 10-plant newly-flat set are the gross view behind the class net.

## §7 — reproduce

```
python scripts/probes/_miso128_c7_diurnal_organization.py
```

No LP, no bundle, no network; reads only committed artifacts plus a HEAD fleet
assembly for P9 grain 2 (`--skip-grain2` runs the dispatch half alone). Writes
`results/calibration/_miso128_c7_diurnal_organization.json`.
