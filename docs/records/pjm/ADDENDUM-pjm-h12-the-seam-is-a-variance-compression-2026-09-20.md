# ADDENDUM — pjm-h12 card D-2: the export seam gap is ONE defect (price-variance compression), and the chartered successor's HOURLY claim is UNREACHABLE IN THE DATA (2026-09-20)

**Session:** pjm-h12 · **Branch:** `claude/pjm-h12-midcurve-seam-ar8wcb` · **HEAD:** `2c42c926a338ba916969badfcc1d4beb20e11107`
**ZERO LP MINUTES, ZERO SHARDS.** Every number here comes from committed artifacts: the PJM keeper
pair's `hourly/system_<year>.parquet` sidecars (rule 15 `[R-DASHBOARD]` commits them so a diagnostic
need not replay a solve), `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`, and
`data/raw/eia-930-interchange/`. Probe: `scripts/probes/pjm_h12_seam_qq_phase0.py`.
**Companion:** `docs/FINDING-pjm-h12-the-midcurve-rebuild-is-a-clean-rederivation-2026-09-20.md` (card D-1).

---

## 1. Headline

1. **Both limbs of C-2 have ONE cause.** The model's price distribution is **variance-compressed**
   against measured DA — systematically **too high in the low tail** (p10 ratio 1.18–1.40) and
   **too low in the high tail** (p99 ratio 0.63–0.89) — while the **median is right** (p50 ratio
   0.998–1.187, which is why C3a passes). The seam ladder's rungs are **quantiles of the measured
   DA price**, so clearing them against a compressed distribution under-clears both ends at once.
2. **That derives the sign of the export shortfall from first principles.** PJM exports when its
   price is *low*; the model's low tail is too high; so fewer deep export blocks clear and the model
   exports less. No fitting, no residual — the direction falls out of the Q-Q geometry.
3. **The import limb is not "under-modelled", it is UNREACHABLE.** Import rungs at never-exceeded
   depths price at `quantile(da, 1.0)` — the **year's measured maximum**. The model's hourly price
   reaches that ceiling in **7 hours out of 52,560 (0.013 %)**, and in **four of six years, never
   once**. That mechanically explains pjm-h11's C-2 reading (model gross import 0.000–0.048 TWh vs
   measured 0.000–0.603) with no further data.
4. **The re-anchoring repair is REAL and LARGE on volume.** Offline, a rank-preserving re-anchoring
   takes the span volume error from **+37.368 TWh to +0.060 TWh** and the duration RMSE from
   **358.1 to 118.6** — i.e. to the derivation's own P9 ceiling of 121.1.
5. **AND THE CHARTERED SUCCESSOR IS DEAD ANYWAY, killed at zero LP.** The charter required that "a
   successor must demonstrate the hourly claim." It cannot. Fed the **exact price it was derived
   from**, the ladder's own hourly *r* is **0.052**. The ceiling is already zero, so no
   re-anchoring of it can clear an hourly bar. §4.
6. **The reason is deeper than the model.** In the **measured data itself**, PJM's hourly seam flow
   is barely a function of PJM's own hourly DA price: |r| ≈ 0.00–0.33 with **signs that flip between
   years and between seams**. The hourly signal is not in the input. §5.
7. **Consequence for governance (owner-facing):** the hourly bar should be **withdrawn as a
   promotion gate on this mechanism family**, because it tests a device for something its input
   cannot carry. The re-anchoring should be judged on volume/duration, where it is decisive. §6.

---

## 2. The Q-Q, measured

Model = load-weighted system P1 price from the keeper pair's committed sidecars. Measured = PJM DA
hub. `ratio` = model ÷ measured at the same quantile.

| year | p1 | p5 | p10 | p25 | **p50** | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| 2020 | 1.634 | 1.478 | 1.402 | 1.264 | **1.187** | 1.134 | 1.038 | 0.964 | 0.886 | 29.756\* |
| 2021 | 1.339 | 1.273 | 1.202 | 1.115 | **1.062** | 0.953 | 0.864 | 0.865 | 0.879 | 1.060 |
| 2022 | 1.406 | 1.213 | 1.181 | 1.116 | **1.020** | 0.942 | 0.827 | 0.754 | 0.649 | 0.461 |
| 2023 | 1.547 | 1.404 | 1.297 | 1.175 | **1.039** | 0.934 | 0.833 | 0.788 | 0.641 | 0.358 |
| 2024 | 1.716 | 1.506 | 1.348 | 1.179 | **1.031** | 0.916 | 0.800 | 0.731 | 0.758 | 0.547 |
| 2025 | 1.570 | 1.341 | 1.237 | 1.120 | **0.998** | 0.886 | 0.790 | 0.738 | 0.627 | 0.869 |

\* 2020's model maximum is 1,991.95 $/MWh — a single scarcity hour. It is why 2020's *Pearson*
price correlation reads 0.197 against a *Spearman* of 0.871; an outlier artifact, not a ranking
defect. It does not affect any quantile at or below p99.

**The pattern is monotone and present in all six years**: the ratio falls steadily from ~1.5 at p1
to ~0.7 at p99, crossing 1.0 near the median. That is textbook variance compression, and it is the
whole of the seam story.

### The censor bounds, and whether the model can reach them

`qq_import` = `quantile(da, 1 − exceed)`, so a depth the measured flow never exceeded prices at the
year's **measured maximum**; `qq_export` = `quantile(da, depth)`, so a never-reached export depth
prices at the year's **measured minimum**. Both are single per-year scalars shared across seams.

| year | import ceiling | export floor | model p50 | model max | **hrs ≥ ceiling** | hrs ≤ floor |
|---|---|---|---|---|---|---|
| 2020 | 66.94 | 5.31 | 22.29 | 1991.95 | 3 (0.034 %) | 0 |
| 2021 | 169.76 | 14.72 | 33.61 | 180.03 | 4 (0.046 %) | 0 |
| 2022 | 431.93 | 13.01 | 59.79 | 199.05 | **0** | 0 |
| 2023 | 308.05 | 7.68 | 28.21 | 110.35 | **0** | 0 |
| 2024 | 276.93 | 7.75 | 26.60 | 151.59 | **0** | 0 |
| 2025 | 502.65 | 11.62 | 36.51 | 436.90 | **0** | 0 |

**7 hours in six years.** The saturated import rungs are not merely expensive in the model — they are
outside its price support entirely.

---

## 3. The offline reconstruction

`scripts/data/derive_pjm_seam_ladders.offline_score` already implements the clearing law
`sim = Σ step·1[price > import_k] − Σ step·1[price < export_k]`. The probe drives that identical law
with three price series against the same measured flows:

- **P9** — measured DA. The derivation's own check, and the mechanism's ceiling.
- **ASIS** — the model's own price. What the LP does today.
- **ARM** — the model's price mapped, hour by hour, to the measured-DA price at its **own within-year
  quantile**. A strictly monotone transform, so **hourly ordering is untouched by construction** and
  the arm cannot manufacture hourly correlation; only the marginal distribution moves.

| year | driver | sim TWh | act TWh | vol err | hourly *r* | dur RMSE |
|---|---|---|---|---|---|---|
| 2020 | P9 | −41.603 | −41.629 | +0.025 | 0.0277 | 121.6 |
| 2020 | **ASIS** | −25.919 | −41.629 | **+15.709** | 0.0545 | 449.5 |
| 2020 | **ARM** | −41.613 | −41.629 | **+0.016** | 0.0644 | 117.5 |
| 2021 | P9 | −37.805 | −37.816 | +0.011 | −0.0497 | 121.9 |
| 2021 | ASIS | −32.209 | −37.816 | +5.608 | −0.0862 | 328.5 |
| 2021 | ARM | −37.813 | −37.816 | +0.004 | −0.0618 | 118.7 |
| 2022 | P9 | −31.732 | −31.777 | +0.046 | −0.0413 | 121.0 |
| 2022 | ASIS | −28.280 | −31.777 | +3.497 | −0.0729 | 293.9 |
| 2022 | ARM | −31.739 | −31.777 | +0.038 | −0.0663 | 118.5 |
| 2023 | P9 | −39.961 | −39.978 | +0.017 | 0.0948 | 121.4 |
| 2023 | ASIS | −35.245 | −39.978 | +4.733 | 0.1775 | 366.9 |
| 2023 | ARM | −39.974 | −39.978 | +0.004 | 0.1786 | 118.6 |
| 2024 | P9 | −32.866 | −32.830 | −0.035 | 0.1295 | 120.8 |
| 2024 | ASIS | −27.742 | −32.830 | +5.088 | 0.0525 | 370.3 |
| 2024 | ARM | −32.874 | −32.830 | −0.043 | 0.0791 | 118.4 |
| 2025 | P9 | −32.891 | −32.928 | +0.037 | 0.1520 | 119.9 |
| 2025 | ASIS | −30.195 | −32.928 | +2.733 | 0.1014 | 339.5 |
| 2025 | ARM | −32.887 | −32.928 | +0.041 | 0.1342 | 119.9 |

| span totals | vol err TWh | mean hourly *r* | mean dur RMSE |
|---|---|---|---|
| P9 | **+0.100** | 0.0522 | 121.1 |
| **ASIS** | **+37.368** | 0.0378 | 358.1 |
| **ARM** | **+0.060** | 0.0547 | 118.6 |

This reproduces pjm-174's recorded numbers (2021 −37.805, 2022 −31.732, both to the milli-TWh) and
extends them to all six years.

**Honest scope limit, stated rather than buried:** this is the *derivation's* offline law. The live
LP additionally applies the measured per-border deliverability envelopes and its own internal price
feedback, so **+37.368 TWh is indicative of direction and rough scale, not the LP's own seam error**
(pjm-h11 measured the live shortfall at 9.0–12.3 TWh/yr, against ~6.2 TWh/yr here). The *ratio*
between drivers is the robust reading; the absolute is not.

---

## 4. The hourly claim, killed at zero LP

The charter's bar for a card D-2 successor was explicit: *"A successor must demonstrate the hourly
claim."* It cannot, and the reason is not the model.

**Fed the exact price it was derived from, the ladder's own hourly *r* is 0.052** (span mean; per
seam: MISO 0.3113, LGEE −0.0033, NYISO −0.0081, TVA 0.0007, Carolinas −0.0397). That is the
mechanism's ceiling, and it is already at zero.

| seam | P9 (ceiling) | ASIS | ARM | Δ |
|---|---|---|---|---|
| Carolinas | −0.0397 | 0.0098 | 0.0273 | +0.0175 |
| LGEE | −0.0033 | 0.0717 | 0.0922 | +0.0205 |
| MISO | 0.3113 | 0.2439 | 0.2630 | +0.0192 |
| NYISO | −0.0081 | −0.1069 | −0.1127 | −0.0058 |
| TVA | 0.0007 | −0.0294 | 0.0035 | +0.0329 |

The ARM does improve hourly *r* in 4 of 5 seams and its span mean (0.0547) even **exceeds** P9's
(0.0522). **That is not a result, it is noise at an absolute level of 0.05**, and reporting it as a
win would be exactly the kind of number this program exists not to quote.

**Why this is a structural property, not a tuning shortfall.** `qq_import`/`qq_export` match
*exceedance frequencies*. A step ladder calibrated on duration statistics is a **duration-curve
device**: it pins the *distribution* of flow by construction and says nothing whatever about which
hour receives which block. Hourly *r* ≈ 0 is what the mechanism is built to deliver. **This is also
the retrospective explanation for the previous arm's failure** — `seam_neighbour_hourly_ladder`'s
hourly claim was contradicted by its solve because it was never achievable, not because that arm was
built wrong.

---

## 5. The signal is not in the input

The deeper check, and the one that retires the whole line of attack. Correlation of **measured**
hourly seam flow against **measured** hourly PJM DA price:

| seam | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| MISO | 0.2436 | 0.0260 | 0.2920 | 0.3100 | 0.2980 | 0.1530 |
| NYISO | **−0.3663** | −0.1159 | **+0.2213** | 0.0676 | 0.1750 | 0.0695 |
| Carolinas | 0.0141 | 0.0324 | **−0.3321** | −0.0793 | −0.0735 | −0.0369 |
| TVA | −0.0567 | −0.1589 | −0.2197 | 0.0563 | −0.1623 | −0.0550 |
| LGEE | 0.1972 | −0.1258 | −0.2541 | −0.0132 | −0.1170 | −0.0028 |

**PJM's hourly interchange is not, in reality, a function of PJM's own hourly price.** The
magnitudes are small and **the signs flip between years and between seams** (NYISO −0.37 → +0.22;
Carolinas +0.03 → −0.33). Real hourly interchange is driven by the *neighbour's* price, by bilateral
schedules and by transmission outages — none of which a PJM-price-indexed device can see.

**No re-anchoring, no hourly ladder and no quantile map can recover a signal the input does not
carry.** MISO is the one partial exception (|r| 0.15–0.31, sign-stable), which is consistent with it
being the largest and most economically-coupled seam.

---

## 6. What this means, and what this lane did NOT do

**The mechanism-matrix cell `seam_neighbour_hourly_ladder` stays `O` and was NOT re-tested** — the
charter bars re-running that arm and this lane did not. What changed is the *reading* of why it
failed, and that reading is now measured rather than inferred. **No matrix cell is edited**, because
no mechanism was tested: this is a diagnostic on committed artifacts, and nothing here is wired into
a solve (rule 28 duty (b) triggers on testing a mechanism, which this is not).

**No successor was built and no shards were launched.** Phase 0 did its job in the direction phase 0
is *for* — it killed an arm before an LP was spent on it. Under rule 29 `[R-SCREEN]` clause (0),
surviving as practice, that is the whole point.

### The two questions this leaves for the owner

- **Q5 (new) — withdraw the hourly bar from this mechanism family?** §4 and §5 show the bar tests a
  duration-curve device for hourly skill its input cannot carry. Keeping it guarantees that every
  future seam successor fails for a reason unrelated to its merit. The proposal is to judge seam
  anchoring on **volume + duration RMSE**, where §3 shows a decisive, structurally-grounded repair
  (+37.4 → +0.06 TWh offline; duration RMSE 358 → 119), and to route hourly interchange to a
  **different input** (neighbour price / scheduled bilaterals) as its own card. This is a governance
  call about what a gate means, so it is **not** a session decision.
- **Q6 (new) — is a quantile-indexed ladder worth building?** The ARM series in §3 is a *diagnostic*
  reconstruction and is **not** itself admissible as a mechanism: mapping onto the measured DA
  marginal at runtime has no forward analogue, so it fails rule 13 `[R-MEASURED]`. The admissible
  form stores each rung's **quantile** rather than its measured price and evaluates it against the
  **model's own** within-year distribution — carrying no measured price level, regenerating for any
  forecast year from forward drivers, and removing the §2 censoring automatically. That is a real
  new `ScenarioConfig` mechanism (rule 28 duty (c): a matrix row in the same PR) and a
  PRECOMMIT-plus-six-shards task. **Not started here**, because Q5 decides what it would be gated on
  and building it first would repeat the previous arm's mistake in a new costume.

**Nothing is at risk with this container.** No LP ran, so there are no bundles on ephemeral disk and
rule 31 `[R-RETAIN]`'s promotion question has no subject. The probe and both docs are committed.
