# pjm-h17 — the measured TOP of the offer curve is NOT PJM's slope defect; the CT_FAST shelf is

**Lane:** PJM — the offer-stack slope (C3c upstream, C3a cancellation)
**Date:** 2026-09-21, re-verified 2026-09-22 · **Keeper:** `2026-09-20-pjm-h15-coalwindow-span`
(+ folded touchpoint `…-touchpoint`)
**Cost:** ZERO LP. Three `fleet_only` builds (~15 s each) + committed sidecars. No shard launched.
**Rules:** 29 `[R-SCREEN]` clause 0 (zero-LP phase 0), 32 `[R-SHARD]` (a) (the parent never solves),
28 `[R-MECH-MATRIX]` (a) (never re-test an adjudicated cell without new evidence), 1 `[R-STRUCT]`.

> **Re-verified 2026-09-22 against the keeper promotion.** Every measurement below was first taken
> on `2026-09-20-pjm-h14-coalmustrun-span`, which the `pjm-h15-coalwindow` promotion superseded and
> pruned (rule 35 `[R-PROMOTE]`). Re-run against the incoming keeper, **all three grounds and the
> slope table reproduce to within ±2 MW / ±0.01** — the six-year ratio table is identical to the
> digit, CC_REGULAR's peak band is still 0.000 MW in all 26 280 hours, and (A) is unchanged because
> the promotion moved nothing this finding reads: `CC_REGULAR.peak = 5.0`, `CT_PEAKER.peak = 4.0`,
> `ST_GAS.peak = 3.024`, `pjm_offer_midcurve_segments = ('LONG_RUN','CC_LIKE')`,
> `pjm_offer_midcurve_peak_segments = None`, `pjm_ct_measured_max_reprice = False` in both recipes.
> The probes are repointed at the current keeper. **Lane renamed h15 → h17**: `pjm-h15` was taken by
> the coalwindow lane (`RESULT-pjm-h15-2026-09-21.md`) and `pjm-h16` is in flight.

---

## 0. Verdict

**The lane's proposed lever is refuted at phase 0, on three independent grounds, before any
solve.** Its premise — that PJM's corpus "carries the top segments that were never read" — is
half true and the half that is true points the other way: the derive *does* read the top belt
(it has since the G-22 lever-C extension, and the committed surface carries `s0.975`/`s0.995`
for all three segments over 2020–2025), and where the model does not read it, reading it would
**lower** the top of the stack, not lift it.

**The defect the lane's own evidence is pointing at is one class down: the CT_PEAKER econ
shelf.** 22.8 GW of it, 90–92 % of it priced *below* PJM's own published offers, and 7.4–13.6 GW
of it sitting idle in exactly the hours the lane measured the gap. A mechanism aimed precisely
at it already exists, is rule-19-constructed, and has **never been armed in any PJM bundle**.

---

## 1. The lane's evidence reproduces — on the current keeper, and across all six years

The prompt's ratios were computed on `2026-09-20-pjm-h13-meritalloc-span`, since superseded twice —
by `…-h14-coalmustrun-span`, then by the current `…-h15-coalwindow-span`. **Neither promotion moved
them**, and the table below is the current keeper's. Model/market price ratio by
percentile, load-weighted system dual vs PJM's hub RT series
(`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`):

| year | p50 | p90 | p95 | p99 | p99.9 | mean |
|---|---|---|---|---|---|---|
| 2020 | 1.24 | 1.03 | 0.87 | 0.62 | 0.55 | 1.18 |
| 2021 | 1.12 | 0.87 | 0.79 | 0.66 | 0.58 | 1.00 |
| 2022 | 1.10 | 0.83 | 0.75 | 0.63 | 0.08¹ | 0.93 |
| 2023 | 1.13 | 0.82 | 0.73 | 0.54 | 0.44 | 1.03 |
| 2024 | 1.10 | 0.78 | 0.68 | 0.69 | 0.56 | 0.99 |
| 2025 | 1.08 | 0.80 | 0.72 | 0.60 | 0.53 | 0.95 |

¹ 2022 p99.9 is Winter Storm Elliott: market $1 957.7 against model $157.7. A single-event
artifact, reported rather than smoothed.

The prompt's 2023/2024/2025 rows (1.13/0.82/0.54/0.44, 1.09/0.78/0.68/0.56, 1.08/0.80/0.60/0.53)
reproduce to ±0.01. **The defect survived both promotions and extends to every year PJM carries.** It is a genuine, stable, monotone slope deficit: the model is 8–24 % *high* at the
median and 31–56 % *low* at p99.

---

## 2. Ground (A) — the measured top belt sits BELOW the model's fitted peak band

Measured with the mechanism's **own** targeting code (`_pjm_midcurve_context` /
`_pjm_midcurve_row_target`), so the number is byte-for-byte what
`pjm_offer_midcurve_peak_segments` would apply. Implied gas heat rate (price ÷ delivered gas day),
capacity-weighted over each class's `peak*` rungs:

| year | class | MW | model fitted | PJM measured | measured/model |
|---|---|---|---|---|---|
| 2023 | CC_REGULAR | 3 945 | 34.52× | 11.04× | **0.32** |
| 2023 | CT_PEAKER | 2 414 | 38.50× | 31.95× | 0.83 |
| 2023 | ST_GAS | 1 729 | 17.88× | 10.61× | 0.59 |
| 2024 | CC_REGULAR | 3 945 | 37.50× | 13.58× | **0.36** |
| 2024 | CT_PEAKER | 2 415 | 42.67× | 35.52× | 0.83 |
| 2024 | ST_GAS | 1 731 | 19.62× | 10.76× | 0.55 |
| 2025 | CC_REGULAR | 3 945 | 30.34× | 11.73× | **0.39** |
| 2025 | CT_PEAKER | 2 415 | 34.01× | 32.53× | 0.96 |
| 2025 | ST_GAS | 1 731 | 17.33× | 8.20× | 0.47 |

`pjm_offer_midcurve_peak_segments` prices these rows in **LEVEL** form — the measured belt
*replaces* the fitted rung, by design, because a floor cannot pull a rung down onto measured.
Every ratio is < 1. **Arming it lowers the top of PJM's stack in every class and every year.**
That is the wrong sign for a tail that is already 31–56 % low, and the lane's own pre-registration
("a peak-only lift that breaks C3a is a fail") is moot: there is no lift available here.

Stated plainly, because it cuts the other way too: **the fitted CC peak band (`offer_curve_by_group
CC_REGULAR.peak = 5.0`, ≈ 30–38× gas) is 2.6–3.1× PJM's own published top-of-curve offer.** That
is a rule-14 `[R-ACCURATE]` observation about the incumbent band, and it is *not* resolved here —
see §6.

---

## 3. Ground (B) — the peak rungs barely clear, and one never clears at all

Whole-year P1 dispatch of every `peak*` band, from the keeper's committed
`hourly/class_band_hourly_<year>.parquet`:

| class | 2023 max / mean MW | 2024 | 2025 |
|---|---|---|---|
| **CC_REGULAR** | **0.0 / 0.0** | **0.0 / 0.0** | **0.0 / 0.0** |
| CT_PEAKER | 854.8 / 7.3 | 935.9 / 5.7 | 975.7 / 8.0 |
| ST_GAS | 995.2 / 27.6 | 977.3 / 46.4 | 993.3 / 59.7 |
| COAL_BIT | 535.6 / 47.0 | 589.6 / 69.5 | 562.8 / 183.3 |

**CC_REGULAR's peak band dispatches 0.000 MW in all 26 280 hours of all three years.** It is
~3.9 GW of capacity (8 % of CC per `pct_peaking`) offered at 5.0 × SRMC that the LP has never once
found economic. CT_PEAKER's peak band averages 5.7–8.0 MW against a 936 MW block.

A row that never sets the dual cannot move it. This is the **pjm-99 inertness result**
(`measured_offer_surface` cell = **R**, `FINDING-pjm-offer-surface-noop-2026-07.md`) re-measured on
the current keeper — and under rule 28(a) it is the reason this lane does not re-open that cell.

---

## 4. Ground (C) — the model is not at the top of its stack in those hours anyway

Availability-aware headroom (`pmax × availability[g,t]`, from the keeper's own `FleetArrays` —
never a max-over-year proxy), in the market's top-1 % hours (n = 88):

| year | available | dispatched | **idle** | market LMP | model LMP |
|---|---|---|---|---|---|
| 2023 | 104 481 MW | 77 088 | **27 393 (26 %)** | $123.1 | $39.2 |
| 2024 | 101 716 MW | 81 519 | **20 196 (20 %)** | $169.8 | $54.9 |
| 2025 | 110 860 MW | 94 444 | **16 416 (15 %)** | $317.6 | $112.6 |

And the composition of that idle block is the whole finding:

| class | 2023 used | 2024 used | 2025 used | idle MW (23/24/25) |
|---|---|---|---|---|
| CC_REGULAR | 93.6 % | 95.4 % | 95.6 % | 3 047 / 2 158 / 2 229 |
| COAL | 82.5 % | 90.6 % | 98.5 % | 3 962 / 2 058 / 401 |
| **CT_PEAKER** | **36.5 %** | **52.4 %** | **65.8 %** | **13 590 / 10 257 / 7 415** |
| ST_GAS | 62.9 % | 72.4 % | 67.2 % | 2 626 / 1 624 / 2 429 |
| oil | 0.0 % | 0.3 % | 5.9 % | 3 961 / 3 967 / 3 749 |

**CC and coal are fully loaded; the peakers are the idle block.** The clearing point sits in the
middle of the CT_PEAKER econ ladder with 7–14 GW of CT still above it. Repricing the top 5 % of a
curve the LP never reaches is inert by construction — which is exactly what pjm-99 found and what
the armed mid-curve mechanism's own docstring says it was built to route around.

*Join hazard, recorded because it nearly produced a wrong headline:* the fleet's `efficiency_bin`
vocabulary and the sidecar's `klass` are different alphabets. `efficiency_bin` carries one `COAL`
bin (521 rows, 49 371.7 MW) that the sidecar splits into COAL_BIT/PRB/WC, and a `default` bin
(691 rows, 58 106 MW) that is oil 507 + import 80 + hydro 72 + nuclear 32. Joined naively those two
read 0 % utilised and inflate "idle" by ~62 GW (83 GW / 59 % instead of 27 GW / 26 %). The probe
keys the fleet side on `Generator.fuel_type` instead.

---

## 5. Where the gap actually is — the CT_FAST shelf, measured

The same corpus, the same conditioning, the same within-plant capacity-share mapping — applied to
the rungs the keeper's scope **excludes**. `pjm_offer_midcurve_segments` is armed at
`('LONG_RUN','CC_LIKE')`; CT_FAST is out of scope by the pjm-103 rule-19 decision that
`tranche_startup_amortization` owns the CT stack.

Capacity-weighted over the CT econ/peak rows, in the market's top-1 % hours:

| year | CT rows | CT MW | model `mc_base` | **PJM's own offer** | upper-bound lift | % of CT MW-h where measured > `mc_base` |
|---|---|---|---|---|---|---|
| 2023 | 797 | 22 829 | $50.3 | **$78.9** | $33.2 | **90 %** |
| 2024 | 804 | 22 836 | $55.5 | **$91.1** | $39.6 | **91 %** |
| 2025 | 803 | 22 835 | $67.6 | **$119.7** | $56.5 | **92 %** |

The idle shelf of §4 and the under-priced shelf of §5 are **the same 22.8 GW**.

**Stated limit, not buried:** `$33–57` is an **upper bound**. It is computed against `mc_base`
(the P0 base cost); `pjm_ct_measured_max_reprice` applies `max(bid, target)` at the
`p1_bid_max_target` seam *after* `tranche_startup_amortization`, which already raises CT bids and
will absorb part of it. pjm-121 §3 put the model's full P1 marginal CT bid at $47–80 — overlapping
this `mc_base` range — so the absorption looks partial, but **this lane did not measure it** and
the number above must not be quoted as a predicted price effect.

The mechanism: **`ScenarioConfig.pjm_ct_measured_max_reprice`** (`scenarios.py:14400`, default
`False`). It is the rule-19 *reconciliation* rather than a second mechanism — pjm-101/102 armed the
same measured level as a floor against `mc_base` alone and it over-expressed (CT −12 TWh, C3a
+12 %) because the two markups **summed**; here whichever prices the row higher owns it. Per the
matrix base row it is **armed in ZERO PJM bundles** and has never been solved.

---

## 6. What is NOT claimed

* **No arm is proposed and no parameter is constructed.** Nothing was swept; every number is a
  committed artifact or the keeper's own fleet build read through the mechanism's own code.
* **The CT direction is not established as a fix.** It is established as *the measured surface the
  keeper does not read, sitting on the capacity that is idle in the hours that miss*. Whether
  arming it re-slopes the stack or merely re-levels it is a solve question, and the C3a-cancellation
  risk the lane pre-registered applies to it in full: p50 is already 1.08–1.13, so a lift that does
  not also let the middle fall will break C3a.
* **The CC peak band's 2.6–3.1× gap over measured (§2) is left open.** Closing it *downward* is
  what `peak_segments` does, and doing that alone would deepen the tail miss. It belongs in a joint
  re-slope charter with §5, not as a standalone arm.
* **`measured_offer_surface` stays R and is not re-opened.** §3 is fresh evidence *for* that
  verdict, not against it.

---

## 7. Governance — why this stops here

Arming `pjm_ct_measured_max_reprice` sits inside the **owner-declared-closed pjm-142 frontier**
(`keepers/PJM.json`: *"Further PJM price-formation work needs a NEW defect or a NEW measured
identification with its own charter"*). The matrix records the same gate for the sibling
`peak_segments` extension: *"sits inside the owner-declared-closed pjm-142 frontier, so it is an
OWNER RULING."*

§5 is arguably a **new measured identification** — a committed corpus surface the keeper provably
does not read, on capacity provably idle in the missing hours. It is not this session's call to
decide that it clears the frontier. **No shard was launched and no year was spent.**

Nothing is at risk from waiting: **no bundle was solved, so rule 31 `[R-RETAIN]` has nothing to
protect.** The cost of this phase 0 was ~45 s of LP-free fleet builds; the cost of the arm it
declined to launch would have been 6 shard containers × 6 years.

---

## 8. Artifacts

| artifact | what | LP |
|---|---|---|
| `scripts/probes/_pjm_h17_top_of_stack.py` | grounds (A) / (B) / (C) — §2, §3, §4 | zero |
| `results/calibration/_pjm_h17_top_of_stack.json` | its output | — |
| `scripts/probes/_pjm_h17_ct_shelf.py` | the CT_FAST shelf census — §5 | zero |
| `results/calibration/_pjm_h17_ct_shelf.json` | its output | — |

Both probes rebuild the keeper's own fleet with `fleet_only=True` (≈15 s per year) and read the
measured surface through the mechanisms' own `_pjm_midcurve_context` /
`_pjm_midcurve_row_target` / `build_pjm_ct_measured_max_target`. The CT probe flips
`pjm_ct_measured_max_reprice` on in a **local config copy only** to build the target array —
nothing is armed, and no bundle, recipe or registered run is touched.

Two `data/clean` partitions had to be regenerated for the fleet build to run in a fresh
container (`transfer-interface-limits`, `ramp-capability`); both are derived, gitignored and
reproduced by `scripts/regenerate_clean.py`.
