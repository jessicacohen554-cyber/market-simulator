# FINDING — CAMPD economic-layup charter, LANE B: the day-grain best-block `R < 0` cut is **NOT** a viable replacement for the merit-order guard's window-grain cut. Validated on all five ISOs with a published anchor, 180 configuration-cells: at the grain the guard actually operates on it beats the incumbent in **82 of 180 cells** — a coin flip — with a median gain of **−0.0003** and |Δ| < 0.02 in 159 of 180. The flagged neiso-67 observation does not survive restatement: its headline gap compared the **two opposite sides of the guard's own split**, and against the correct comparator the incumbent already matches or beats it. Mechanically the two cuts select **the same windows** (Jaccard 0.77–0.97, median 0.92; the day cut finds 127 windows the incumbent misses out of 15,782 scored). **Documented negative; nothing is proposed** (2026-07-26)

**Freeze status: STILL ACTIVE, and this finding does not lift it.** Lane B was a
measurement lane over a flagged observation, not a freeze condition. **Only the
owner lifts the freeze** (`frontend/data/backcast/holdout-freeze.json`).

Probe (committed, re-runnable, **no LP solve**):
`scripts/probes/_campd_daygrain_crossiso.py`.

Context: `FINDING-neiso67-commitment-test-2026-07-26.md` §6 item 2 flagged — and
deliberately did not act on — an observation:

> The day-grain best-block `R < 0` cut tracks published UNCOMMITTED at +0.63 to
> +0.79, where the guard's own window-grain out-of-merit share reaches +0.08 to
> +0.31 (D1 table, KEPT windows). That is a **marginal**-test refinement, in the
> guard's existing lane — a possible *replacement* for its window-grain cut,
> never an addition. It is out of scope for this charter, it has not been
> validated cross-ISO, and it must not be adopted on this finding alone.

It is now validated cross-ISO. **It does not replace anything.**

Nothing here changes a keeper, an extract, a default, or the guard. No LP solve
was run. No out-of-training year was touched. No dashboard registration
(findings-only session; rule 15 covers runs, not probes).

---

## §1 — what was measured, and the two controls that make it readable

Both cuts are applied to the **same window population** — each ISO's committed
guard-on extract UNION its committed layup companion, i.e. the guard-off
baseline reconstructed from committed bytes (no re-derive was run) — against the
**same merit panel**, with the **same structural threshold** `MERIT_OOM_FRAC =
0.90`. Only the grain of the out-of-merit test changes:

* **window-grain (incumbent).** A window's out-of-merit share is the fraction of
  its HOURS with `SRMC_u(t) > RCC(t)`; veto at `≥ MERIT_OOM_FRAC`.
* **day-grain (candidate).** A window's out-of-merit share is the fraction of its
  DAYS whose best feasible commitment block is out of merit — the maximum-sum
  contiguous block of at least the unit's published `min_run_hours` inside a
  forward horizon of `max(--horizon, min_run_hours)` from the day start has
  NEGATIVE energy margin. Veto at the same `≥ MERIT_OOM_FRAC`.

Note what the candidate is **not**: `R = margin / start_cost` with start cost
strictly positive, so `R < 0` is exactly `margin < 0` and the published
start-cost table drops out of the cut entirely. The cut carries **no start-cost
parameter** — it is a pure marginal condition evaluated over a physically
bounded block, which is why it is a candidate in the guard's existing lane
rather than a second mechanism stacked on it (rule 19 `[R-ONE-MECH]`).
`min_run_hours` (measured CAMPD `unitType` × measured heat rate → the published
NREL/SR-5500-55433 row) is the only new physical input and carries no free
parameter.

**Reference price.** The full-panel `RCC`, not neiso-67's leave-one-out — and on
this population that is an *identity*, not a simplification: LOO removes unit
`j`'s weight from hour `t`'s quantile only where the unit is measured RUNNING and
priced, and every hour scored here is an hour the extract books the unit as
DOWN. With zero weight to remove, `rcc_loo[j] == rcc` exactly. This is also what
the guard itself uses, so the head-to-head is clean.

**Control 1 — the re-implementation is the guard.** The re-applied window-grain
cut reproduces each ISO's **committed** kept/layup split on **99.1–99.8 %** of
windows (NEISO 468/471, 466/470, 480/484; CAISO 529/530, 531/533, 626/628;
ERCOT 1,088/1,091, 1,173/1,181, 1,068/1,070; MISO 1,445/1,451, 1,502/1,509,
1,448/1,454; PJM 1,676/1,684, 1,624/1,635, 1,583/1,591). The residual disagreement
is the window span reconstructed from the extract's calendar dates versus the
detector's own hour indices.

**Control 2 — the ported machinery lands on neiso-67's published numbers.** The
neiso-67 §2/§5 idle-capacity `R < 0` band, recomputed here: **812 MW / +0.70**
(2023), **1,104 MW / +0.80** (2024), **1,071 MW / +0.64** (2025), against
neiso-67's 812 / +0.70, 1,114 / +0.79, 1,074 / +0.63. The charter D1 anchors also
reproduce: NEISO 2023 baseline **1.52× / +0.53**, guard-on **1.37× / +0.69**
(D1: 1.36× / +0.71), placebo p95 **+0.59** (D1: +0.63), vetoed-vs-UNCOMMITTED
**+0.77** (D1: +0.77). **So everything below is a property of the cut, not of a
broken port.**

Scope, per the charter §4: **CAISO** (CNOG on the reviewed resource→plant
crosswalk, **revision-aware build only** — `tail(1)` and raw-sum are both wrong,
neiso-66 §1), **MISO** (native outage source), **PJM** (Data Miner 2 DAM
availability), **ERCOT** (60-day DAM disclosure, with its stated
offered-vs-available caveat), **NEISO** (ISO-NE Morning Report Section 3, the
only ISO that also publishes the uncommitted column). **NYISO has no published
anchor and is excluded — none was improvised for it.**

Sweep: `--rcc-pctl {0.50, 0.75, 0.90, 0.99} × --horizon {24, 48, 72}` × 3 years ×
5 ISOs = **180 cells**, each carrying the full D1 standard (vetoed-by-cut
capacity vs the published series, kept-vs-vetoed separation, proportion-matched
placebo p95 over 30 draws, and the no-split reference).

**Level/shape caveat, binding on every number here (charter §4).** The extract is
CEMS-thermal while several published series are whole-fleet, so a level *ratio*
is interpretable only where the thermal-only extract EXCEEDS a whole-fleet
published total. **The robust axis is the monthly correlation**, plus the placebo.

## §2 — the flagged observation compared the two opposite sides of the same split

The neiso-67 headline set `+0.63…+0.79` against `+0.08…+0.31`. Those are not two
cuts. The first is the **identified-layup** side (capacity the day-grain test
picks out); the second is the guard's **KEPT / mechanical** side — the half that
is *supposed* to be uncorrelated with the uncommitted column. The correct
comparator for a layup identifier is the guard's own **VETOED** side, which the
charter D1 positive control already measured at **+0.77 / +0.71 / +0.67**.

Re-measured here on one instrument, NEISO at the default p90 / h24, vs published
`uncommitted_available_gen_nonfast_mw`:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| window-grain **VETOED** (incumbent's layup side) | **+0.77** | +0.73 | **+0.66** |
| day-grain **VETOED** (candidate's layup side) | +0.70 | **+0.74** | +0.53 |
| day-grain idle-capacity `R < 0` band (neiso-67's object) | +0.70 | +0.80 | +0.64 |
| window-grain KEPT (the observation's comparator) | +0.11 | +0.27 | +0.31 |
| day-grain KEPT | +0.19 | +0.26 | +0.37 |

At the grain the guard operates on, the incumbent's vetoed side **beats** the
candidate's in 2023 and 2025 and loses by 0.01 in 2024. The `+0.63…+0.79` was
never a gap over the incumbent; it was a gap over the incumbent's *other half*.

Two further reasons the observation does not transfer, both structural rather
than statistical: the band is measured on **idle unit-days** (all non-operating
capacity, whether or not the detector booked a window) while the guard classifies
**detected windows** — different populations; and the KEPT series is *also* the
one that must track published OUTAGES, which is the property the D1 standard
actually gates on.

## §3 — head-to-head at the guard's own grain: a coin flip

The operative comparison is the **KEPT** extract — the series the fleet builder
reads — against each ISO's published outage anchor, at the default
`RCC` p90 / horizon 24 h:

| ISO | year | no-split baseline | WINDOW kept level / r | DAY kept level / r | Δ (day − window) |
|---|---|---|---|---|---|
| NEISO | 2023 | 1.52× / +0.53 | 1.37× / **+0.69** | 1.39× / +0.65 | **−0.038** |
| NEISO | 2024 | 1.57× / +0.47 | 1.29× / **+0.61** | 1.31× / +0.61 | −0.007 |
| NEISO | 2025 | 1.22× / +0.70 | 0.92× / **+0.78** | 0.95× / +0.73 | **−0.047** |
| CAISO | 2023 | 1.64× / +0.78 | 1.34× / +0.78 | 1.39× / +0.78 | −0.001 |
| CAISO | 2024 | 1.84× / +0.79 | 1.69× / +0.77 | 1.71× / +0.77 | +0.003 |
| CAISO | 2025 | 2.05× / +0.83 | 1.91× / +0.85 | 1.93× / +0.85 | +0.005 |
| ERCOT | 2023 | 1.05× / +0.64 | 0.72× / **+0.79** | 0.71× / +0.78 | −0.010 |
| ERCOT | 2024 | 0.97× / +0.68 | 0.75× / **+0.82** | 0.76× / +0.81 | −0.004 |
| ERCOT | 2025 | 0.90× / +0.84 | 0.71× / **+0.92** | 0.71× / +0.91 | −0.012 |
| MISO | 2023 | 0.89× / +0.82 | 0.79× / +0.87 | 0.79× / +0.88 | +0.002 |
| MISO | 2024 | 0.91× / +0.79 | 0.82× / +0.80 | 0.81× / +0.81 | +0.005 |
| MISO | 2025 | 0.76× / +0.88 | 0.68× / +0.95 | 0.67× / +0.95 | +0.003 |
| PJM | 2023 | 1.28× / +0.90 | 1.11× / +0.90 | 1.11× / +0.90 | +0.001 |
| PJM | 2024 | 1.07× / +0.90 | 0.98× / +0.91 | 0.97× / +0.90 | −0.006 |
| PJM | 2025 | 0.96× / +0.93 | 0.84× / +0.95 | 0.83× / +0.95 | +0.002 |

Over the **whole 180-cell sweep**: the day-grain cut is better in **82/180**
cells, median Δ **−0.0003**, mean Δ **−0.004**, and **|Δ| < 0.02 in 159/180**.
Per ISO, median Δ: NEISO **−0.006**, ERCOT **−0.004**, CAISO **+0.000**, PJM
**+0.000**, MISO **+0.001**.

**The placebo verdict is the same for both cuts almost everywhere.** Window-grain
clears its proportion-matched placebo p95 in 105/180 cells, day-grain in 101/180;
the two disagree in 14 cells, and **9 of those 14 favour the incumbent**. Against
the no-split reference: window 138/180, day 134/180. Neither cut acquires a
capability the other lacks.

**Sign stability, the adoption bar's own criterion.** Of the 60 (ISO × pctl ×
horizon) configurations, only **9** have the day-grain cut winning in all three
years, and in every one of those the median gain is **+0.002 to +0.017** —
inside the noise band the placebo defines. No configuration wins on all five
ISOs. The *largest* deltas in the sweep run the other way and cluster on NEISO,
the ISO the observation came from: −0.09 to −0.14 at p50/p90 with the longer
horizons.

**No horizon rescues it.** Mean kept-`r` at p90 by horizon, window vs day:
NEISO +0.693 vs +0.662 (h24) → +0.616 (h48) → +0.604 (h72); CAISO +0.798 vs
+0.801 / +0.803 / +0.799; ERCOT +0.843 vs +0.835 / +0.835 / +0.836; MISO +0.875 vs
+0.879 / +0.879 / +0.872; PJM +0.918 vs +0.917 / +0.916 / +0.917. Lengthening the
commitment horizon — the lever that most directly expresses the candidate's
"block" idea — makes it monotonically **worse** on NEISO and moves nothing
anywhere else.

## §4 — the mechanism: the two cuts select the same windows

The null is not a mystery. Measured at the default p90 / h24, veto-set overlap
per ISO-year:

| ISO | Jaccard (2023 / 2024 / 2025) | window-only vetoes | day-only vetoes |
|---|---|---|---|
| NEISO | 0.92 / 0.97 / 0.94 | 8 / 4 / 12 | **0 / 0 / 0** |
| CAISO | 0.77 / 0.91 / 0.86 | 18 / 9 / 9 | **0 / 0 / 0** |
| ERCOT | 0.97 / 0.95 / 0.97 | 7 / 15 / 9 | 7 / 6 / 2 |
| MISO | 0.93 / 0.89 / 0.94 | 7 / 15 / 6 | 11 / 13 / 11 |
| PJM | 0.88 / 0.88 / 0.92 | 10 / 8 / 7 | 29 / 26 / 22 |

Across all 15 ISO-years and **15,782 scored windows**, the day-grain cut vetoes
**127** windows the incumbent does not (0.8 %), and the incumbent vetoes **144**
the day-grain cut does not (0.9 %). On NEISO and CAISO the day-grain veto set is
a strict **subset** of the incumbent's in every year — it cannot identify
anything the incumbent misses, by construction of what it selected.

That is the finding in one line: **the day-grain best-block condition is not a
different discriminator, it is a slightly smaller version of the same one.** The
window-grain share is near-binary (IQR [0.00, 1.00] on NEISO/ERCOT), and so is
the day-grain share — a unit that is out of merit for essentially every hour of a
multi-day window is also a unit whose best feasible block is negative on
essentially every day of it. The integral over a `min_run`-length block that the
commitment framing was supposed to add changes the verdict on ~1 window in 60.

## §5 — verdict

**NEGATIVE, on the bar stated before measurement.** Adoption evidence required
the day-grain cut to be sign-stable, above placebo, **and beating the
window-grain cut in (nearly) every cell across ISOs**. It is: not sign-stable
(9/60 configurations), no better than the incumbent against placebo (101 vs 105
of 180, with the disagreements favouring the incumbent 9–5), and it beats the
incumbent in 82 of 180 cells at a median gain of −0.0003. **It fails all three
legs.**

Consequences, stated carefully:

* **No guard change is proposed, so there is no blast radius and no rule-22
  leave-one-year-out obligation.** The charter §5 blast radius stays closed and
  no keeper is implicated by this session. The guard remains exactly as the
  charter §8 verdict adopted it: window-grain, `MERIT_RCC_PCTL = 0.90`,
  `MERIT_OOM_FRAC = 0.90`, `MERIT_ORDER_GUARD_ENABLED = False` with the committed
  extracts derived guard-on.
* **The neiso-67 §6 item-2 observation is CLOSED, not merely unadopted.** Its
  headline gap was a comparison across the two sides of one split; restated
  against the correct comparator (§2), the incumbent already matches or beats
  the candidate on the very instrument the observation invoked. This is the
  charter's own identification standard applied to itself.
* **Rule 19 `[R-ONE-MECH]` was never in tension.** The candidate was screened
  strictly as a *replacement* in the guard's existing marginal lane. It is not
  adopted, so nothing stacks. Had it been adopted it would have replaced the
  window-grain share outright.
* **Rule 23 `[R-FROZEN-DERIVE]` is respected.** No knob was re-derived and none
  is recommended. `MERIT_OOM_FRAC` was held at 0.90 for both cuts throughout —
  re-tuning it to flatter one cut would have been fitting to a residual, and
  neiso-66 §4 already measured that lever as reaching at most 3–5 % of the
  excess.

**What would falsify this finding.** A day-grain (or any block-integral)
construction whose veto set is **materially disjoint** from the window-grain
cut's — Jaccard well below the 0.77–0.97 measured here — *and* which then clears
the D1 standard on the disjoint part. The null measured here is specifically that
the two select the same windows; a construction that genuinely selects different
ones has not been tested and is not refuted by this. What is refuted is the
`R < 0` best-block cut as specified in neiso-67 §6 item 2, on every ISO with a
published anchor, across every reference-price level and horizon in the sweep.

**NYISO remains unverified**, as it has been throughout this charter: it carries
no published outage or availability instrument, and none was improvised. Any
future cut proposed for the guard inherits that gap.
