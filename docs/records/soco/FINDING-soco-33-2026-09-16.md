# FINDING — SOCO-33, the seam derive

Lane **SOCO-33**, Opus `claude-opus-5`, branch `claude/soco-33-seam-derive-mz1tng`,
base `edd40943`. `DATA PROFILE: soco`. Plan
`docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-33, §3 card **S4**.
**Zero LP. Derive only — this lane arms nothing.**

Preconditions held: SOCO-20 LANDED (the eight `INTERFACE_NEIGHBORS["SOCO"]`
blocks are registered default-off; `soco_net_interchange` is in
`_SCALAR_INTERCHANGE_ISOS`), SOCO-11 LANDED (the DIBA book).

---

## 0. Headline

**Card S4's served half is sound and verified; its priced half is not yet
armable, and the binding obstacle is the interface limits, not the heat
rates.**

1. **SANITY CHECK PASSES.** SOCO comes out a **net EXPORTER in every year** on
   both clocks — the served array the LP would consume reads **+10.156 /
   +10.807 / +13.032 TWh** (2023/24/25), the sum of the nine DIBA legs reads
   **+10.155 / +10.832 / +13.039 TWh**, and every residual between them is
   explained (leap day, DST, UTC re-binning) rather than padded. This
   reproduces the charter's +10.16 / +10.81 / +13.03 and SOCO-11 §4.1
   independently.
2. **Seven of SOCO's eight registered `interface_limit_mw` values are
   contradicted by SOCO's own meter.** Arming the priced seams at the values
   `spec.py` carries would **refuse 10.66 / 12.81 / 14.21 TWh** of measured
   flow — **35.6 / 39.0 / 41.7 %** of the gross throughput across those eight
   seams. `SOCO_SCEG`, SOCO's largest export seam, is over its 126 MW limit in
   **99.8 %** of 2025 hours and would lose **8.68 of its 9.78 TWh**. Only
   `SOCO_MISO` (2,374 MW) is never exceeded, in any hour of any year. This is
   the quantification of the rule-14 misalignment `spec.py` states
   qualitatively for all eight blocks; **the limits are a precondition for
   SOCO-56, ahead of any heat-rate work.**
3. **Exactly one of eight seams is anchorable at all.** `SOCO_MISO` derives to
   `hr_by_year` **{2023: 9.52, 2024: 10.09, 2025: 9.28}** (RT) off MISO-South's
   own zonal LMP. The other seven neighbours publish no LMP and get **no year
   table** — reported, never proxied. **Gate G17 was never approached**: no
   step of this lane needs or uses a SOCO price.
4. **Both committed producers fail on `--iso SOCO`, and one fails silently** —
   routed, not patched (§7 R-1/R-2).

---

## 1. What ran

```
python3 scripts/data/derive_neighbor_hr_by_year.py   --iso SOCO --years 2023 2024 2025
python3 scripts/data/derive_neighbor_hr_elasticity.py --iso SOCO --years 2023 2024 2025
```

| Producer | Exit | Output |
|---|---|---|
| `derive_neighbor_hr_by_year.py --iso SOCO` | **1** | `SOCO: no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS` |
| `derive_neighbor_hr_elasticity.py --iso SOCO` | **0** | header only — **zero rows**, no diagnostic |

Both are real and neither is repaired here (§7). The tables below are the two
producers' **own arithmetic**, unchanged, with only the anchor resolver
substituted — the SPP-33 precedent, whose complete listing lives in its
FINDING §A and whose counterpart for this lane is **§A** below.

### Files landed (all under `data/raw/reference/`, nothing else touched)

| file | rows | bytes | sha256[:16] |
|---|---:|---:|---|
| `soco_seam_served_schedule.csv` | 6 | 1,085 | `d857db09882926a9` |
| `soco_seam_hr_by_year.csv` | 27 | 4,179 | `b5991c920c14b9a0` |
| `soco_seam_hr_elasticity.csv` | 24 | 2,514 | `5b1a6c5acf3c3055` |
| `soco_seam_diba_duration.csv` | 27 | 5,089 | `907c7e45c69fc7dc` |
| `soco_seam_limit_binding.csv` | 24 | 2,370 | `754caf4ae99e50cc` |
| `soco_seam_SOURCES.md` | — | 9,249 | — |

`git status --short` shows **only** these six paths — no `src/`, no
`spec.py`, no `ScenarioConfig`, no neighbour's object, no `scripts/`, no
`tests/`, no `frontend/`, no matrix cell (rule 28 — this lane tests no
mechanism), no CI workflow, no solve. Gate **G9** (non-SOCO diff = ∅) holds by
construction.

---

## 2. The sign convention, stated explicitly — and verified (gate G19)

**`mw > 0` = SOCO EXPORTS to the counterparty; `mw < 0` = SOCO IMPORTS from
it.** The served scalar column uses the same convention (`> 0` = net export).

SOCO's footprint spans two timezones, so the convention is **verified, not
asserted**, on two axes at once:

| shift applied to the leg sum | hours joined | exactly equal to the BA book | r |
|---|---:|---:|---:|
| −2 h | 26,294 | 31 (0.1 %) | +0.8944 |
| −1 h | 26,294 | 54 (0.2 %) | +0.9551 |
| **0 h** | **26,294** | **24,100 (91.7 %)** | **+0.9985** |
| +1 h | 26,293 | 52 (0.2 %) | +0.9549 |
| +2 h | 26,292 | 31 (0.1 %) | +0.8945 |

Zero shift is the only alignment that works, so both the interchange product's
`local_time` and `SOCO hourly.parquet`'s `Local time` are on the **same**
clock — `America/Chicago`, the key SOCO-10 established and SOCO-20 registered.
The **mean of both series is +1,293 MW**, positive, which is the sign check
itself. (24,100/26,294 reproduces SOCO-11 §4.1 exactly, from an independent
join.)

## 3. The served schedule — card S4's actual first-keeper input

`soco_seam_served_schedule.csv`. Sign: `> 0` = SOCO net export.

| year | source | hours | net TWh | export TWh | import TWh | export-hour share | mean MW | min MW | max MW |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | `served_model_clock` | 8,760 | **+10.1562** | 10.2909 | −0.1347 | 94.37 % | 1,159.39 | −1,397 | 4,432 |
| 2023 | `sum_of_legs_local_clock` | 8,759 | +10.1550 | 21.0315 | −10.8765 | — | — | — | — |
| 2024 | `served_model_clock` | 8,760 | **+10.8067** | 10.8855 | −0.0788 | 96.47 % | 1,233.64 | −1,659 | 4,858 |
| 2024 | `sum_of_legs_local_clock` | 8,784 | +10.8315 | 23.1223 | −12.2908 | — | — | — | — |
| 2025 | `served_model_clock` | 8,760 | **+13.0321** | 13.0802 | −0.0482 | 97.34 % | 1,487.68 | −933 | 5,147 |
| 2025 | `sum_of_legs_local_clock` | 8,760 | +13.0385 | 24.7275 | −11.6890 | — | — | — | — |

**Every residual is accounted for, not absorbed:**

* **2024, 0.0248 TWh** — the model's non-leap 8,760 h clock drops **2024-02-29
  (24 h, 24.18 GWh = 0.0242 TWh)**; `10.8315 − 0.0242 = 10.8074` against the
  served `10.8067`, leaving **0.0007 TWh** of UTC→local re-binning.
* **2023, 0.0012 TWh**; **2025, 0.0064 TWh** — re-binning plus the seven
  UTC-bounded trailing hours of 2025 the loader bridges.

**One structural point the arming lane must carry.** The served scalar is the
**net** position: gross export 10.3–13.1 TWh against gross import 0.05–0.13
TWh, because offsetting legs cancel inside the hour. The nine directional legs
carry **21.0–24.7 TWh of gross export and 10.9–12.3 TWh of gross import** —
roughly **twice the throughput**. Replacing the served scalar with eight
priced seams is therefore not a re-parameterisation of the same quantity; it
doubles the energy crossing SOCO's border and gives that energy a direction
and a price. That is the whole of what SOCO-56 has to get right.

---

## 4. `hr_by_year` — one seam of eight, **for a later lane to arm**

`soco_seam_hr_by_year.csv`. `HR[y] = mean_anchor_LMP[y] / (delivered_gas[y] × K[y])`.

### 4.1 The one anchorable seam

| neighbour | year | run | anchor mean $/MWh | HH $/MMBtu | basis | delivered gas | `K` | **`hr_by_year`** | registered flat | flat constructs $/MWh | flat error |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `SOCO_MISO` | 2023 | **rt** | 27.0420 | 2.54 | 0.30 | 2.84 | 1.0 | **9.52** | 9.63 | 27.3492 | +1.14 % |
| `SOCO_MISO` | 2023 | da | 28.0903 | 2.54 | 0.30 | 2.84 | 1.0 | 9.89 | 9.63 | 27.3492 | −2.64 % |
| `SOCO_MISO` | 2024 | **rt** | 25.1159 | 2.19 | 0.30 | 2.49 | 1.0 | **10.09** | 9.63 | 23.9787 | −4.53 % |
| `SOCO_MISO` | 2024 | da | 25.4835 | 2.19 | 0.30 | 2.49 | 1.0 | 10.23 | 9.63 | 23.9787 | −5.90 % |
| `SOCO_MISO` | 2025 | **rt** | 35.4525 | 3.52 | 0.30 | 3.82 | 1.0 | **9.28** | 9.63 | 36.7866 | +3.76 % |
| `SOCO_MISO` | 2025 | da | 35.7947 | 3.52 | 0.30 | 3.82 | 1.0 | 9.37 | 9.63 | 36.7866 | +2.77 % |

Anchor: `actual_lmp_hourly_zonal_MISO.parquet`, rows `zone == "MISO-South"`
(35,040 / 35,040 / 35,036 rows; 0 / 0 / 4 NaN), per-zone mean — the anchor
SOCO-20's `spec.py` block documents. `K = 1.0` exactly, because every SOCO
block carries `load_shape_exponent = 1.0` (the mean-preserving, parameter-free
default), so the convexity term does no work on this ISO.

**ERROR AGAINST INTEREST — my RT numbers are not byte-equal to the registered
ones, and the difference is mine to explain rather than to round away.**
`spec.py` carries `hr_by_year={2023: 9.54, 2024: 10.08, 2025: 9.26}`; the
producer's arithmetic at HEAD gives **9.52 / 10.09 / 9.28** (Δ −0.02 / +0.01 /
+0.02 MMBtu/MWh, ≤ 0.24 %). The cause is the Henry Hub operand, not the
anchor: SOCO-20's block comment shows it divided by **2.836 / 2.492 / 3.829**
(unrounded HH 2.536 / 2.192 / 3.529 + 0.30), while `neighbor_gas_price` reads
`HENRY_HUB_TRAJECTORIES["mid"]`, which carries **2.54 / 2.19 / 3.52**. The
runtime uses the trajectory constants, so **9.52 / 10.09 / 9.28 is what the
registered formula would actually produce**; the registered triple is a
hand-computation on a more precise gas operand. Both means round to the same
registered flat 9.63. The block is default-off, so nothing is live and nothing
is fixed here — it is SOCO-56's to reconcile (§7 R-3).

### 4.2 The seven that cannot be anchored

`SOCO_TVA`, `SOCO_DUK`, `SOCO_SCEG`, `SOCO_SC`, `SOCO_FPL`, `SOCO_FPC`,
`SOCO_TAL` — every one a vertically-integrated, non-market BA that publishes
no LMP. Each is written into the CSV with `anchor_status = NO_ANCHOR …` and
**blank** `hr_by_year`, reported rather than silently dropped (the SPP-51
discipline). **No proxy is substituted.** PJM's flat 11.6 and its `(5.6, 14.2)`
Southeast affine fit are PJM's (rule 25 `[R-ISO-SCOPE]`) and are neither
re-keyed nor re-derived; the CSV reports only what the registered 11.6
placeholder would *construct* as a price level — **$29.46 / $25.40 / $40.83
per MWh** — with no error column, because there is nothing measured to compare
it to.

**MEASURED GAP, reported not papered over.** `FLA hourly.parquet` ends
**2025-01-31** (744 h of 2025), so the three Florida seams — registered
`proxy_ba="FLA"` — have **no 2025 load shape at all**; `neighbor_load_shape`
returns `None` and their 2025 rows carry a blank `K`. Nothing is substituted:
SOCO's own shape is not Florida's. This blocks **nothing** in the served
keeper and is a **precondition for SOCO-56** (§7 R-4).

## 5. The elasticity fit — one seam, and weakly identified

`soco_seam_hr_elasticity.csv`. OLS of `mean_anchor_LMP / K` on delivered gas.

`SOCO_MISO`: **`hr_gas_elastic = (7.95, 4.96)`**, `fit_r2 = 0.9935`,
`hr_phys_sign_ok = True`, `n_points = 3`.

| year | delivered gas | measured HR | flat 9.63 | elastic | \|flat − meas\| | \|elast − meas\| |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 2.84 | 9.52 | 9.63 | 9.70 | 0.11 | 0.17 |
| 2024 | 2.49 | 10.09 | 9.63 | 9.94 | 0.46 | 0.15 |
| 2025 | 3.82 | 9.28 | 9.63 | 9.25 | 0.35 | **0.03** |
| **mean** | | | | | **0.31** | **0.12** |

**Read it honestly, in both directions.** The elastic form beats the flat on
average (0.12 vs 0.31 MMBtu/MWh) and is much better in the dear-gas year, but
it is **worse in 2023** — and `r² = 0.9935` on **three points and two
parameters** (one residual degree of freedom) is close to mechanical, not
evidence of identification. What the fit is good for is a sign and an order of
magnitude: MISO-South's price formation is **strongly** gas-elastic
(`hr_phys` 7.95 of an effective ~9.6), unlike the coal/nuclear Southeast PJM
fits at 5.6. What it is *not* good for is a claim of forward skill on three
points.

**Materiality, stated so nobody over-invests here.** The registered flat 9.63
is already within **1.1–5.9 %** of the measured mean in every year; the
elastic form buys ~0.19 MMBtu/MWh of mean error, about **$0.7/MWh** at 2025
gas, on **one** of eight seams that carries 4.4–4.7 TWh of a 21–25 TWh gross
book. **SOCO's seam risk is not in the heat rate.** It is in §6's limits (the table above) and
in the seven neighbours that cannot be priced at all.

The seven unanchored neighbours get `n_points = 0` and blank coefficients. No
SPP or PJM fit is transferred to fill them (rule 25); note that SPP's own MISO
fit `(9.0, 3.22)` is a **different object** — it anchors MISO-West **and**
MISO-South, where SOCO's Mississippi seam anchors MISO-South alone.

---

## 6. The headline finding — the interface limits

`soco_seam_limit_binding.csv`. Each registered `interface_limit_mw` against
the measured DIBA series it governs.

| neighbour | limit MW | yr | h over limit | share | max \|MW\| | headroom | gross TWh | **TWh refused** | share refused |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `SOCO_SCEG` | 126 | 2023 | 8,693 | 99.2 % | 1,462 | 0.086 | 7.12 | **6.02** | 84.6 % |
| | | 2024 | 8,764 | 99.8 % | 1,537 | 0.082 | 8.85 | **7.74** | 87.5 % |
| | | 2025 | 8,743 | 99.8 % | 2,123 | 0.059 | 9.78 | **8.68** | 88.7 % |
| `SOCO_TAL` | 20 | 2023–25 | 7,968 / 7,987 / 7,325 | 91 / 91 / 84 % | 294 / 274 / 291 | 0.068–0.073 | 0.72 / 0.69 / 0.59 | 0.56 / 0.52 / 0.43 | 77 / 76 / 73 % |
| `SOCO_TVA` | 478 | 2023–25 | 5,131 / 5,248 / 4,770 | 59 / 60 / 54 % | 2,940 / 3,007 / 3,150 | 0.152–0.163 | 5.66 / 5.66 / 5.25 | 2.35 / 2.29 / 2.03 | 42 / 40 / 39 % |
| `SOCO_DUK` | 407 | 2023–25 | 4,064 / 4,648 / 5,003 | 46 / 53 / 57 % | 1,797 / 1,779 / 1,954 | 0.208–0.229 | 3.80 / 4.01 / 4.62 | 1.13 / 1.29 / 1.87 | 30 / 32 / 41 % |
| `SOCO_FPC` | 50 | 2023–25 | 3,182 / 3,354 / 4,917 | 36 / 38 / 56 % | 313 / 298 / 354 | 0.141–0.168 | 0.42 / 0.45 / 0.64 | 0.13 / 0.16 / 0.30 | 31 / 36 / 47 % |
| `SOCO_SC` | 533 | 2023–25 | 3,029 / 4,298 / 4,771 | 35 / 49 / 54 % | 984 / 1,242 / 1,241 | 0.429–0.542 | 4.06 / 4.59 / 4.83 | 0.34 / 0.70 / 0.86 | 8 / 15 / 18 % |
| `SOCO_FPL` | 1,317 | 2023–25 | 358 / 316 / 165 | 4.1 / 3.6 / 1.9 % | 2,622 / 2,843 / 1,969 | 0.463–0.669 | 3.60 / 4.01 / 3.42 | 0.13 / 0.10 / 0.03 | 3.6 / 2.5 / 1.0 % |
| **`SOCO_MISO`** | **2,374** | **2023–25** | **0 / 0 / 0** | **0 %** | 1,507 / 1,780 / 1,657 | **1.33–1.58** | 4.58 / 4.58 / 4.94 | **0.00** | **0 %** |

| all eight seams | gross TWh | TWh refused | share |
|---|---:|---:|---:|
| 2023 | 29.96 | **10.66** | 35.6 % |
| 2024 | 32.83 | **12.81** | 39.0 % |
| 2025 | 34.08 | **14.21** | 41.7 % |

**What this says, and what it does not.** `spec.py` already declares the
misalignment in prose — the values are the 2024 Reserve Margin Study's
**average import transfer capability into** Southern, an adequacy-study
quantity, not a tie rating — and notes the envelope exceeds them 3–25×. This
lane puts a number on the consequence: **arming the eight blocks at the
registered limits would refuse 36–42 % of the energy SOCO's own meter
recorded**, concentrated in the two seams (`SCEG`, `TAL`) where the limit is
an order of magnitude below the median flow. `SOCO_MISO` is the single seam
whose registered limit is consistent with its own measured flow in all three
years, and it is also the only one with a price anchor — a coincidence worth
noticing, not a result.

It does **not** say the published values are wrong. They are a correctly
transcribed, correctly cited adequacy-study quantity (SOCO-12,
`data/raw/soco-planning/README.md` §4c). It says they are **the wrong
quantity for a transfer limit**, which is precisely rule 14's misalignment
exception — and rule 14's instruction in that case is a *reconciled* version
of the real data, not a guess and not the estimate. Reconciling them is
SOCO-56's, on the SPP-51 ERCOT-tie precedent (§7 R-5).

### The duration curves

`soco_seam_diba_duration.csv` — nine DIBAs × three years, 11 percentiles each,
with `sign_convention` carried on every row. **Zero NaN hours and zero
impossible prints** anywhere in the book; the largest `|mw|` is 3,150 MW, so
the `> 20,000 MW` screen excludes nothing at any threshold above ~3,200.
Grain is 8,759 / 8,784 / 8,760 h, the 2023 shortfall being the DST
spring-forward 02:00 local. Every net TWh and percentile **matches SOCO-11
§4.3 to the digit**, from an independent computation.

Structure, largest first (net TWh 2023 / 2024 / 2025, `>0` = export):

| DIBA | seam | 2023 | 2024 | 2025 | character |
|---|---|---:|---:|---:|---|
| `SCEG` | `SOCO_SCEG` | +7.12 | +8.85 | +9.78 | near-unidirectional export, 99.7→100.0 % of hours |
| `MISO` | `SOCO_MISO` | +4.39 | +4.49 | +4.73 | export, 91–95 % of hours |
| `SC` | `SOCO_SC` | +4.05 | +4.59 | +4.83 | export, 96–100 % |
| `FPL` | `SOCO_FPL` | +2.90 | +2.77 | +2.91 | export, 77–85 % |
| `TAL` | `SOCO_TAL` | +0.71 | +0.67 | +0.56 | export, 89–95 %, small |
| `FPC` | `SOCO_FPC` | +0.08 | −0.02 | −0.42 | **drifting balanced → import** |
| `SEPA` | *(unregistered)* | −1.95 | −2.58 | −2.31 | federal hydro allocation, 0.1–2.8 % export |
| `TVA` | `SOCO_TVA` | −3.46 | −4.08 | −2.88 | **the one genuinely two-way seam**, 18–28 % export, ±3,150 MW |
| `DUK` | `SOCO_DUK` | −3.69 | −3.86 | −4.16 | near-unidirectional import, 6–12 % export |

`SEPA` is correctly left out of the priced blocks and inside the served
schedule (SOCO-20's stated reason: a federal hydro **marketer**'s contract
allocation is not a priced seam) — but note it is **−1.95 to −2.58 TWh/yr of
firm import** that the served scalar carries and any priced-seam
representation would have to carry some other way.

---

## 7. Routed to the desk — nothing acted on here

**R-1. `derive_neighbor_hr_elasticity.py` fails SILENTLY on any ISO whose
neighbours are not in its global name map.** It exits **0** with an empty
table. This is the same defect class SPP-51 repaired in
`derive_neighbor_hr_by_year.py` (which now fails **closed**, as it did for
SOCO here) and never repaired in this one. Worse for SOCO than for SPP,
because SOCO's neighbours are named `SOCO_<DIBA>` *by design* (so no
`_HR_GAS_ELASTIC` key can collide — rule 25, plan gate G10), so **no** SOCO
seam will ever resolve through a name-keyed map. The fix is the per-ISO
`NEIGHBOR_LMP_ANCHORS` shape SPP-51 already built. **Not made here** — a
shared producer this lane does not own.

**R-2. `NEIGHBOR_LMP_ANCHORS` has no `SOCO` key**, so producer A exits 1. The
entry SOCO-56 would add is one line and is written out in §A. **Not made
here**, same reason; registering an anchor map is part of arming.

**R-3. The registered `SOCO_MISO` `hr_by_year` and the producer's arithmetic
differ by ≤ 0.02 MMBtu/MWh** (§4.1), because the block was hand-computed on
unrounded Henry Hub while the runtime reads `HENRY_HUB_TRAJECTORIES`. Inert
today. SOCO-56 should adopt **9.52 / 10.09 / 9.28** (what the formula
produces) or state why not.

**R-4. `FLA hourly.parquet` ends 2025-01-31**, so the three Florida seams have
no 2025 load shape and cannot be priced that year. A data-lane fetch
(`fetch_eia930_hourly.py --ba FLA`), not a modelling decision. **Precondition
for SOCO-56**; blocks nothing in the served keeper.

**R-5. The interface limits are the lane-blocking item** (§6). Seven of eight
would refuse 36–42 % of measured flow. Rule 14's misalignment exception
applies and points to a *reconciled* real quantity — SERC/Southern posted
firm ATC/TTC, or the measured envelope itself with a stated basis — not to the
adequacy-study average and not to a guess. SPP-51's ERCOT-tie reconciliation
is the precedent `spec.py` already names.

**R-6. Gate G17 was never approached and should be recorded as such.** No step
of this lane needs a SOCO price: every anchor is the **neighbour's own**
realized price on the **neighbour's own** side of the seam, which is what a
`NeighborInterface` prices. No neighbouring hub, adjusted MISO-South series or
cost-stack construction stands in for a SOCO price anywhere in these files,
and none of them scores a SOCO run. Card S2 limb (b) / rubric v3.8 is
untouched.

**R-7. For the record, the served scalar and eight priced seams are not the
same quantity** (§3): gross throughput roughly doubles. Whatever SOCO-56
concludes about limits and anchors, that step change is the thing to screen
under rule 29 `[R-SCREEN]`, and its phase-0 is computable with no LP from
`soco_seam_diba_duration.csv`.

---

## §A. The complete producer listing

The two committed producers cannot reach SOCO (§7 R-1/R-2), so these files
regenerate from the listing below, which **substitutes only the anchor
resolver** and is otherwise the producers' own arithmetic. Run from the repo
root with `PYTHONPATH=src`. The one-line entry a repaired producer A would
carry instead is:

```python
# scripts/data/derive_neighbor_hr_by_year.py :: NEIGHBOR_LMP_ANCHORS
"SOCO": {
    # The ONLY anchorable SOCO seam: MISO-South's own zonal RT/DA LMP, the
    # anchor INTERFACE_NEIGHBORS["SOCO"]["SOCO_MISO"] documents. The other
    # seven neighbours publish no LMP and are reported unanchored. SOCO's own
    # price does not exist (SOCO-13 verdict NO) and is never required here.
    "SOCO_MISO": Anchor("zonal_MISO", ("MISO-South",)),
},
```

<details>
<summary><code>gen_soco_seam.py</code> — the full generator (401 lines)</summary>

```python
"""SOCO-33 seam derive - regenerate data/raw/reference/soco_seam_*.csv.

DERIVE ONLY. Nothing here arms anything: no spec.py edit, no ScenarioConfig
field, no neighbour's side of any seam touched (rule 25).
"""

from __future__ import annotations

import csv
import hashlib

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.eia930 import soco_net_interchange
from market_sim.data.neighbor_price import neighbor_gas_price, neighbor_load_shape

OUT = paths.RAW_DIR / "reference"
YEARS = [2023, 2024, 2025]
HOURS = 8760

# The anchor resolver, stated ex ante (gate G17). SOCO ITSELF HAS NO PRICE
# SERIES and this lane never asks for one; every anchor is the NEIGHBOUR's own
# realized price on the NEIGHBOUR's own side of the seam. Seven of eight
# neighbours publish no LMP: REPORTED as unanchored, never proxied (PJM's 11.6
# and its (5.6, 14.2) fit are PJM's - rule 25).
ANCHORS: dict[str, dict] = {
    "SOCO_MISO": {
        "product": "zonal_MISO",
        "zones": ("MISO-South",),
        "kind": "zonal; per-zone mean over the one bordering zone (MISO-South)",
        "proxy": False,
    },
}
NO_ANCHOR_REASON = "NO_ANCHOR — the neighbour BA publishes no organized-market LMP"


def _anchor_mean(spec: dict, year: int, run: str) -> tuple[float | None, int]:
    """Return (mean LMP $/MWh, n rows) for the anchor - the producer's rule."""
    path = paths.CALIBRATION_DIR / f"actual_lmp_hourly_{spec['product']}.parquet"
    if not path.is_file():
        return None, 0
    df = pd.read_parquet(path)
    rows = df[df["year"] == year]
    if rows.empty or run not in rows.columns:
        return None, 0
    if spec["zones"] is not None:
        rows = rows[rows["zone"].isin(spec["zones"])]
        if rows.empty:
            return None, 0
        return float(rows.groupby("zone")[run].mean().mean()), int(len(rows))
    return float(np.nanmean(rows[run].to_numpy(dtype=float))), int(len(rows))


def _henry_hub(year: int) -> float:
    return float(HENRY_HUB_TRAJECTORIES["mid"][year])


def hr_tables() -> tuple[list[dict], list[dict]]:
    """hr_by_year (producer A) and the elasticity fit (producer B)."""
    hr_rows: list[dict] = []
    el_rows: list[dict] = []
    for nb in INTERFACE_NEIGHBORS["SOCO"]:
        spec = ANCHORS.get(nb.name)
        for year in YEARS:
            shaped = neighbor_load_shape(nb, year, HOURS)
            gas = neighbor_gas_price(nb, year)
            if shaped is None:
                # MEASURED GAP, reported not papered over: the FLA EIA-930
                # extract ends 2025-01-31 (744 h of 2025), so the three Florida
                # seams have no load shape that year. Nothing is substituted -
                # SOCO's own shape is not the neighbour's.
                k, flat_level = None, None
                shape_ba = f"MISSING — no extract for ba={nb.ba_code} / proxy={nb.proxy_ba}"
            else:
                k = float(np.nanmean(shaped[0]))
                shape_ba = shaped[1]
                flat_level = nb.marginal_heat_rate * gas * k
            if spec is None:
                hr_rows.append({
                    "neighbor": nb.name, "year": year, "run": "n/a",
                    "anchor_status": NO_ANCHOR_REASON + ("; NO LOAD SHAPE" if k is None else ""),
                    "anchor_file": "", "anchor_kind": "", "anchor_rows": 0,
                    "shape_ba": shape_ba, "mean_lmp_usd_mwh": "",
                    "henry_hub_usd_mmbtu": round(_henry_hub(year), 4),
                    "gas_basis_usd_mmbtu": round(nb.gas_basis, 4),
                    "delivered_gas_usd_mmbtu": round(gas, 4),
                    "shape_convexity_k": "" if k is None else round(k, 6),
                    "hr_by_year_mmbtu_mwh": "",
                    "registered_marginal_heat_rate": nb.marginal_heat_rate,
                    "flat_hr_constructed_mean_usd_mwh": "" if flat_level is None else round(flat_level, 4),
                    "flat_hr_error_pct": "",
                })
                continue
            for run in ("rt", "da"):
                mean_lmp, n = _anchor_mean(spec, year, run)
                if mean_lmp is None:
                    raise SystemExit(f"{nb.name}/{year}/{run}: declared anchor absent")
                hr_rows.append({
                    "neighbor": nb.name, "year": year, "run": run,
                    "anchor_status": "DERIVED" + (" (DECLARED PROXY)" if spec["proxy"] else ""),
                    "anchor_file": f"actual_lmp_hourly_{spec['product']}.parquet",
                    "anchor_kind": spec["kind"], "anchor_rows": n, "shape_ba": shape_ba,
                    "mean_lmp_usd_mwh": round(mean_lmp, 4),
                    "henry_hub_usd_mmbtu": round(_henry_hub(year), 4),
                    "gas_basis_usd_mmbtu": round(nb.gas_basis, 4),
                    "delivered_gas_usd_mmbtu": round(gas, 4),
                    "shape_convexity_k": round(k, 6),
                    "hr_by_year_mmbtu_mwh": round(mean_lmp / (gas * k), 2),
                    "registered_marginal_heat_rate": nb.marginal_heat_rate,
                    "flat_hr_constructed_mean_usd_mwh": round(flat_level, 4),
                    "flat_hr_error_pct": round(100.0 * (flat_level - mean_lmp) / mean_lmp, 2),
                })
        if spec is None:
            for year in YEARS:
                el_rows.append({
                    "neighbor": nb.name, "year": year, "anchor_status": NO_ANCHOR_REASON,
                    "n_points": 0, "hr_phys_mmbtu_mwh": "", "hr_adder_usd_mwh": "",
                    "fit_r2": "", "hr_phys_sign_ok": "",
                    "delivered_gas_usd_mmbtu": round(neighbor_gas_price(nb, year), 4),
                    "measured_hr": "", "flat_hr": nb.marginal_heat_rate,
                    "elastic_hr": "", "abs_err_flat": "", "abs_err_elastic": "",
                })
            continue
        gas_pts, price_pts = [], []
        for year in YEARS:
            mean_lmp, _ = _anchor_mean(spec, year, "rt")
            k = float(np.nanmean(neighbor_load_shape(nb, year, HOURS)[0]))
            gas_pts.append(neighbor_gas_price(nb, year))
            price_pts.append(mean_lmp / k)
        gas_a, price_a = np.array(gas_pts), np.array(price_pts)
        hr_phys, hr_adder = np.polyfit(gas_a, price_a, 1)
        pred = hr_phys * gas_a + hr_adder
        ss_res = float(((price_a - pred) ** 2).sum())
        ss_tot = float(((price_a - price_a.mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        for i, year in enumerate(YEARS):
            meas_hr = price_a[i] / gas_a[i]
            elast_hr = hr_phys + hr_adder / gas_a[i]
            el_rows.append({
                "neighbor": nb.name, "year": year,
                "anchor_status": "DERIVED" + (" (DECLARED PROXY)" if spec["proxy"] else ""),
                "n_points": len(gas_pts),
                "hr_phys_mmbtu_mwh": round(float(hr_phys), 2),
                "hr_adder_usd_mwh": round(float(hr_adder), 2),
                "fit_r2": round(r2, 4), "hr_phys_sign_ok": bool(hr_phys > 0),
                "delivered_gas_usd_mmbtu": round(float(gas_a[i]), 4),
                "measured_hr": round(float(meas_hr), 2),
                "flat_hr": nb.marginal_heat_rate,
                "elastic_hr": round(float(elast_hr), 2),
                "abs_err_flat": round(abs(nb.marginal_heat_rate - meas_hr), 2),
                "abs_err_elastic": round(abs(elast_hr - meas_hr), 2),
            })
    return hr_rows, el_rows


SIGN = "mw>0 = SOCO exports to DIBA"
_PCTS = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]
# Plausibility screen. No SOCO DIBA carries an impossible print (the extremes
# are TVA -3,150 and FPL +2,843 MW), so nothing is excluded - the screen is RUN
# and REPORTED, not assumed away, and is insensitive above ~3,200.
_IMPOSSIBLE_ABS_MW = 20_000.0


def _diba_frame() -> pd.DataFrame:
    df = pd.read_parquet(paths.RAW_DIR / "eia-930-interchange" / "SOCO interchange hourly.parquet")
    df["year"] = df["local_time"].dt.year
    return df


def duration_and_limits() -> tuple[list[dict], list[dict]]:
    df = _diba_frame()
    reg = {nb.name.removeprefix("SOCO_"): nb for nb in INTERFACE_NEIGHBORS["SOCO"]}
    dur_rows, lim_rows = [], []
    for diba in sorted(df["diba"].astype(str).unique()):
        for year in YEARS:
            sub = df[(df["diba"].astype(str) == diba) & (df["year"] == year)]
            mw_all = sub["mw"].to_numpy(dtype=float)
            nan_h = int(np.isnan(mw_all).sum())
            vals = mw_all[~np.isnan(mw_all)]
            impossible = int((np.abs(vals) > _IMPOSSIBLE_ABS_MW).sum())
            vals = vals[np.abs(vals) <= _IMPOSSIBLE_ABS_MW]
            exp_h, imp_h = int((vals > 0).sum()), int((vals < 0).sum())
            row = {
                "diba": diba, "year": year,
                "registered_seam": f"SOCO_{diba}" if diba in reg else "",
                "sign_convention": SIGN, "hours_in_file": int(len(sub)),
                "hours_with_value": int(vals.size), "hours_nan": nan_h,
                "hours_excluded_impossible": impossible,
                "export_hours": exp_h, "import_hours": imp_h,
                "zero_hours": int((vals == 0).sum()),
                "export_hour_share": round(exp_h / vals.size, 4),
                "mean_mw": round(float(vals.mean()), 2),
                "net_twh": round(float(vals.sum()) / 1e6, 4),
                "export_twh": round(float(vals[vals > 0].sum()) / 1e6, 4),
                "import_twh": round(float(vals[vals < 0].sum()) / 1e6, 4),
            }
            for p in _PCTS:
                row[f"p{p:02d}_mw"] = round(float(np.percentile(vals, p)), 1)
            dur_rows.append(row)
            nb = reg.get(diba)
            if nb is not None:
                mx = float(np.abs(vals).max())
                over = int((np.abs(vals) > nb.interface_limit_mw).sum())
                gross = float(np.abs(vals).sum())
                clipped = float(np.clip(np.abs(vals) - nb.interface_limit_mw, 0.0, None).sum())
                lim_rows.append({
                    "neighbor": nb.name, "diba": diba, "year": year,
                    "registered_interface_limit_mw": nb.interface_limit_mw,
                    "hours_with_value": int(vals.size),
                    "hours_abs_flow_over_limit": over,
                    "share_over_limit": round(over / vals.size, 5),
                    "max_abs_mw": round(mx, 1),
                    "max_export_mw": round(float(vals.max()), 1),
                    "max_import_mw": round(float(vals.min()), 1),
                    "headroom_ratio_limit_over_max": round(nb.interface_limit_mw / mx, 3),
                    # What arming at the registered limit would REFUSE.
                    "gross_throughput_twh": round(gross / 1e6, 4),
                    "energy_clipped_by_limit_twh": round(clipped / 1e6, 4),
                    "clipped_share_of_gross": round(clipped / gross, 4),
                })
    return dur_rows, lim_rows


def served_rows() -> list[dict]:
    """Card S4's actual first-keeper input, on both clocks."""
    df = _diba_frame()
    out = []
    for year in YEARS:
        served = soco_net_interchange(year)
        if served is None:
            raise SystemExit(f"soco_net_interchange({year}) returned None")
        legs = df[df["year"] == year]["mw"].to_numpy(dtype=float)
        legs = legs[~np.isnan(legs)]
        n_legs_h = int(len(df[df["year"] == year]) / df["diba"].nunique())
        for label, arr, hours, note in (
            ("served_model_clock", served, int(served.size),
             "eia930.envelopes.soco_net_interchange(year) — the array the LP serves"),
            ("sum_of_legs_local_clock", legs, n_legs_h,
             "SOCO interchange hourly.parquet, all 9 DIBAs summed"),
        ):
            model = label == "served_model_clock"
            out.append({
                "year": year, "source": label,
                "sign_convention": "mw>0 = SOCO exports (net)", "hours": hours,
                "net_twh": round(float(arr.sum()) / 1e6, 4),
                "export_twh": round(float(arr[arr > 0].sum()) / 1e6, 4),
                "import_twh": round(float(arr[arr < 0].sum()) / 1e6, 4),
                "export_hour_share": round(float((arr > 0).mean()), 4) if model else "",
                "mean_mw": round(float(arr.mean()), 2) if model else "",
                "min_mw": round(float(arr.min()), 1) if model else "",
                "max_mw": round(float(arr.max()), 1) if model else "",
                "note": note,
            })
    return out


def _write(name: str, rows: list[dict]) -> None:
    path = OUT / name
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    print(f"  {name:38s} {len(rows):4d} rows  {path.stat().st_size:7d} B  sha {sha}")


def main() -> None:
    print("SOCO-33 seam derive — writing data/raw/reference/soco_seam_*.csv")
    hr_rows, el_rows = hr_tables()
    dur_rows, lim_rows = duration_and_limits()
    _write("soco_seam_hr_by_year.csv", hr_rows)
    _write("soco_seam_hr_elasticity.csv", el_rows)
    _write("soco_seam_diba_duration.csv", dur_rows)
    _write("soco_seam_limit_binding.csv", lim_rows)
    _write("soco_seam_served_schedule.csv", served_rows())


if __name__ == "__main__":
    main()
```

</details>

**Verified**: the listing above, extracted from this file and run with only `OUT` redirected to a scratch directory, reproduces all five committed CSVs **byte-for-byte** (`cmp` clean on each). Expected output (the committed state):

```
SOCO-33 seam derive — writing data/raw/reference/soco_seam_*.csv
  soco_seam_hr_by_year.csv                 27 rows     4179 B  sha b5991c920c14b9a0
  soco_seam_hr_elasticity.csv              24 rows     2514 B  sha 5b1a6c5acf3c3055
  soco_seam_diba_duration.csv              27 rows     5089 B  sha 907c7e45c69fc7dc
  soco_seam_limit_binding.csv              24 rows     2370 B  sha 754caf4ae99e50cc
  soco_seam_served_schedule.csv             6 rows     1085 B  sha d857db09882926a9
```

---

## 8. What the DESK owes — this lane touched no shared record

Plan §8.0 rule 1 is explicit: *"A lane touches NO shared record. Not this plan,
not the ledger, not `docs/calibration-log/soco.md` … The DESK writes every one
of those at its next refresh, from the lane's FINDING."* So although this
lane's charter lists "plan §5 row → LANDED" as an exit condition, **the plan is
not edited here** — the standing collision rule outranks it, and the same rule
is why the `## Log entry` below is written out for the desk to append verbatim
rather than filed by this lane. Three desk actions follow from this FINDING:

1. **Plan §5 → SOCO-33 LANDED.** The row is shared (`SOCO-30/31/32/33
   derivation`), so marking it needs the desk's judgement about the other three
   lanes; SOCO-33's own exit checks are met — gate G9 holds (non-SOCO diff = ∅)
   and the per-lane FINDING is this file.
2. **Plan §9 findings index** — a `SOCO-33` row citing this file.
3. **`docs/calibration-log/soco.md`** — append the `## Log entry` block below,
   verbatim, newest last.

Also for the desk, not acted on here: §7 R-1 … R-7.

---

## Log entry

```
## soco-33 — 2026-09-16 — seam derive (card S4, zero-LP)

Lane SOCO-33, Opus claude-opus-5, branch claude/soco-33-seam-derive-mz1tng,
base edd40943. Deliverable: data/raw/reference/soco_seam_{served_schedule,
hr_by_year,hr_elasticity,diba_duration,limit_binding}.csv + soco_seam_SOURCES.md.
DERIVE ONLY — FOR A LATER LANE TO ARM. No spec.py, no ScenarioConfig, no
neighbour's object, no producer script, no matrix cell, no solve; git status is
those six paths and nothing else (gate G9 holds).

SANITY CHECK PASSES. SOCO is a net EXPORTER in every year on both clocks: the
served array soco_net_interchange() reads +10.156 / +10.807 / +13.032 TWh, the
sum of the nine DIBA legs +10.155 / +10.832 / +13.039, reproducing the charter
and SOCO-11 §4.1 independently. Residuals explained, not padded: 2024's 0.0248
TWh is 0.0242 leap day (2024-02-29, 24 h, 24.18 GWh, dropped by the 8,760 clock)
+ 0.0007 UTC→local re-binning; 2023 0.0012, 2025 0.0064.

GATE G19 CLOSED ON THIS LANE'S SIDE. Sign convention stated on every row and
VERIFIED, not asserted: mw>0 = SOCO EXPORTS. Shift test over 26,294 joined
hours — sum-of-legs equals the BA book exactly in 24,100 h (91.7 %, r +0.9985)
at zero shift, collapsing to 54 / 52 h (0.2 %, r +0.955) at ∓1 h; both series
mean +1,293 MW, positive. Both products are America/Chicago; the served array
is UTC-built onto the model's non-leap 8,760 clock, and each CSV row names its
clock.

HEADLINE — THE INTERFACE LIMITS, NOT THE HEAT RATES. Arming the eight
registered blocks at their registered interface_limit_mw would REFUSE 10.66 /
12.81 / 14.21 TWh, 35.6 / 39.0 / 41.7 % of the eight seams' gross throughput.
SOCO_SCEG (limit 126 MW, SOCO's largest export seam) is over limit in 99.2 /
99.8 / 99.8 % of hours and loses 6.02 / 7.74 / 8.68 of 7.12 / 8.85 / 9.78 TWh;
SOCO_TAL (20 MW) 77/76/73 % refused; TVA (478) 42/40/39 %; DUK (407) 30/32/41 %;
FPC (50) 31/36/47 %; SC (533) 8/15/18 %; FPL (1,317) 3.6/2.5/1.0 %. SOCO_MISO
(2,374 MW) is the ONLY seam never exceeded in any hour of any year — and the
only one with a price anchor. The values are correctly transcribed adequacy-
study AVERAGE import transfer capability (SOCO-12 §4c), i.e. the wrong QUANTITY
for a transfer limit: rule 14's misalignment exception, whose instruction is a
reconciled real quantity, not the estimate and not a guess. Routed to SOCO-56
on the SPP-51 ERCOT-tie precedent.

hr_by_year — ONE of eight seams is anchorable. SOCO_MISO, off MISO-South's own
zonal LMP (actual_lmp_hourly_zonal_MISO, 35,040/35,040/35,036 rows): RT 9.52 /
10.09 / 9.28, DA 9.89 / 10.23 / 9.37; K = 1.0 exactly (every SOCO block is
load_shape_exponent 1.0). The registered flat 9.63 constructs within 1.1–5.9 %
of the measured mean in every year. ERROR AGAINST INTEREST: spec.py carries
9.54 / 10.08 / 9.26 and the producer's arithmetic gives 9.52 / 10.09 / 9.28
(Δ ≤ 0.02, ≤ 0.24 %) — SOCO-20 hand-computed on unrounded Henry Hub (2.536 /
2.192 / 3.529) where neighbor_gas_price reads HENRY_HUB_TRAJECTORIES (2.54 /
2.19 / 3.52). Inert (default-off); routed to SOCO-56, not fixed. The other
seven neighbours publish no LMP (TVA, DUK, SCEG, SC, FPL, FPC, TAL — all
vertically integrated) and are REPORTED unanchored with blank hr_by_year, never
proxied: PJM's 11.6 flat and its (5.6, 14.2) Southeast fit stay PJM's (rule 25),
and the CSV reports only what the 11.6 placeholder would CONSTRUCT ($29.46 /
$25.40 / $40.83) with no error column.

ELASTICITY. SOCO_MISO (7.95, 4.96), r² 0.9935, sign OK — but on THREE points
and two parameters, so r² is near-mechanical and this is a sign and an order of
magnitude, not a forward-skill claim. Mean |err| 0.12 elastic vs 0.31 flat, yet
WORSE than flat in 2023 (0.17 vs 0.11). Materiality stated so nobody
over-invests: the flat is already within 1.1–5.9 %, the elastic buys ~$0.7/MWh
at 2025 gas, on one seam carrying 4.4–4.7 of a 21–25 TWh gross book. Not SPP's
(9.0, 3.22) — that fit anchors MISO-West AND South; SOCO's anchors South alone.

DURATION CURVES. Nine DIBAs × three years, 11 percentiles, sign on every row;
every net TWh and percentile matches SOCO-11 §4.3 to the digit from an
independent computation. Zero NaN hours, zero impossible prints (max |mw| 3,150,
so the >20,000 screen is insensitive above ~3,200); grain 8,759 / 8,784 / 8,760,
the 2023 shortfall the DST spring-forward 02:00. SEPA (−1.95 / −2.58 / −2.31
TWh of firm federal-hydro import) is correctly outside the priced blocks and
inside the served schedule — but a priced representation must carry it somehow.

GATE G17 NEVER APPROACHED. No step needs a SOCO price; every anchor is the
NEIGHBOUR's own realized price on the NEIGHBOUR's own side of the seam. No
neighbouring hub, adjusted MISO-South series or cost-stack construction stands
in for a SOCO price anywhere, and none of these files scores a SOCO run. Card
S2 limb (b) / rubric v3.8 untouched.

ROUTED, NOT ACTED ON. (R-1) derive_neighbor_hr_elasticity.py --iso SOCO exits 0
with an EMPTY table — its _NEIGHBOR_LMP_ISO is still the pre-SPP-51 GLOBAL name
map, and SOCO's neighbours are named SOCO_<DIBA> by design (gate G10), so no
SOCO seam can ever resolve through it; the same silent-drop class SPP-51 fixed
in the other producer. (R-2) NEIGHBOR_LMP_ANCHORS has no SOCO key, so
derive_neighbor_hr_by_year.py --iso SOCO exits 1 (fail-closed, working as
designed); the one-line entry is written out in FINDING §A. (R-3) the
hr_by_year rounding gap above. (R-4) FLA hourly.parquet ENDS 2025-01-31 (744 h),
so SOCO_FPL / SOCO_FPC / SOCO_TAL have NO 2025 load shape and cannot be priced
that year — nothing substituted; a fetch, and a SOCO-56 precondition; blocks
nothing in the served keeper. (R-5) the limits, above. (R-7) the served scalar
and eight priced seams are NOT the same quantity: gross throughput roughly
DOUBLES (net 10–13 TWh vs 21–25 gross export / 11–12 gross import), which is
the step change SOCO-56 must screen under rule 29 — its phase 0 is computable
with no LP from soco_seam_diba_duration.csv.

docs/handoffs/FINDING-soco-33-2026-09-16.md.
```
