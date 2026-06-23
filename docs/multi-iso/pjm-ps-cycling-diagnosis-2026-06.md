# PJM pumped-storage cycling — root-cause diagnosis (2026-06)

**Question.** The C5b storage-throughput metric was reported to show PJM
mis-cycling its pumped-storage (PS) fleet against the EIA-930 actual. Audit the
PS cycling, validate the actual first (CLAUDE.md #11), and fix the *real*
mechanism — not a knob tuned to the number.

**TL;DR.**
1. **PJM has no clean PS actual to score against.** The EIA-930 PJM extract
   carries **no `NG: PS` or `NG: BAT` breakout at all** (cols: COL/NG/NUC/WAT/
   SUN/WND/OIL/OTH). PJM's own ISO gen-by-fuel folds PS *discharge* into
   **"Hydro"** (positive-only, inseparable from ~3.3 GW conventional hydro) and
   reports "Storage" (batteries) ≈ 0. So `_actual_storage_twh` returns `None`
   and **C5b is — and stays — `SKIPPED` for every PJM year** (the verdict
   confirms: "no storage-throughput series in committed artifacts"). The task's
   premise (cycling "against the EIA-930 actual") rests on a series that does
   not exist for PJM. This is more severe than NEISO, which at least had a
   complete 2025 PS observation.
2. **The $10 PJM PS dispatch adder is the bug — it is a fit to a *mis-measured*
   actual (CLAUDE.md #12).** The adder was set 2026-06-10 ("pjm 3 ps-adder") to
   pull model PS discharge from ~9–10 TWh down to a target read as "~3.5–4 TWh/yr
   of **EIA-923 gross generation**". That target is a **measurement error**: the
   EIA-923 PS series for PJM is **net** generation (**−2.6 TWh/yr** — generation
   minus pumping load, i.e. the round-trip **loss**), not gross discharge.
3. **The true discharge throughput is ~6.5–10 TWh, triangulated two ways**, and
   the model's *original* ~9–10 TWh was approximately right. The $10 adder
   suppressed legitimate arbitrage down to the round-trip-loss figure.
4. **Fix: retire the fitted adder** (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`
   PJM `$10 → {}`; resolves to 0.0). With the adder gone, PS arbitrages on its
   physical RTE and lands at **6.3–6.7 TWh (CF ~14–15%)** — on the reconciled
   actual, **not runaway** — with only a mild, physically-correct price-spread
   compression (mean LMP −0.5%, troughs +$0.8, peaks −$0.7). C5b remains
   `SKIPPED` (no clean actual); the reconciled-actual agreement is supporting
   evidence, ledgered as an accepted measured-input limitation, never a scored
   pass.

---

## Step 1 — validate the actual first (CLAUDE.md #11)

### There is no separable PS/battery series for PJM

| Source | Storage breakout? | Detail |
|---|---|---|
| `data/raw/eia-930-hourly/PJM hourly.parquet` | **No** | cols COL/NG/NUC/WAT/SUN/WND/OIL/OTH — `NG: PS` and `NG: BAT` absent. `load_eia_hourly_benchmark` yields no `battery`/`pumped_storage` series. |
| `data/raw/PJM_fueltype.parquet` (EIA-930 derived) | **No** | fueltypes COL/NG/NUC/OIL/OTH/SUN/WND/WAT — no PS/BAT. |
| `data/raw/ISO-specific-gen-data/PJM_<y>_gen_by_fuel.csv` (PJM's own) | **Partial / folded** | "Storage" = batteries only, ≈0 (max 20 MW; 0.003/0.022/0.021 TWh for 23/24/25). "Hydro" = PS discharge **+** conventional hydro, positive-only (~15.5/16.0/15.5 TWh; max ~6.4–6.7 GW). PS *charging* appears as load, never as negative hydro. |

Consequence: `scripts/render_calibration_html.py:_actual_storage_twh` finds no
`pumped_storage`/`battery` series → `None` → **C5b `SKIPPED`** for 2023/24/25
(verified by `scripts/calibration_verdict.py results/calibration/pjm_46`).

### A reconciled PS *discharge* actual (the EIA-923 PS series is NET, not gross)

EIA-923 (`_processed-legacy/eia923_monthly_generation.parquet`), PJM prime-mover
`PS`, **net** annual generation: **−2.52 / −2.67 / −2.66 TWh** (2023/24/25). This
is *net* = discharge − pumping = −(round-trip loss). It is **not** discharge.

Two independent reconstructions of PS **discharge** throughput:

- **Method A — EIA-923 PS net × RTE.** `D = |net| · RTE/(1−RTE)`. At the model's
  own `PUMPED_STORAGE_RTE = 0.80`: **10.1 / 10.7 / 10.6 TWh**. At a more
  conservative real-fleet RTE 0.75: 7.6 / 8.0 / 8.0. At 0.72: 6.5 / 6.9 / 6.8.
- **Method B — PJM gen-by-fuel "Hydro" minus EIA-923 conventional HY.**
  `15.46 − 8.98 = 6.48` (2023); `15.96 − 8.86 = 7.10` (2024); 2025's conventional
  HY is a preliminary-vintage undercount (13 plants, 2.29 TWh) so Method B is
  unreliable for 2025 — use Method A there.

**Convergence: PS discharge ≈ 6.5–10 TWh/yr**, central ~7–8. Capacity check:
5046 MW PS (22 EIA-860 `PS` units; Bath County ~3 GW, Muddy Run, Yards Creek,
Seneca, Smith Mountain) at 7 TWh = **CF 15.8%**, at 10 TWh = 22.6% — squarely in
the real-PSH duty-cycle band. The "~3.5–4 TWh" that motivated the adder (CF
~7–9%) is the **net-loss magnitude (~2.6 TWh) misread as discharge**. Per
CLAUDE.md #11/#12 this reconciled figure is forward-valid: it is `net × RTE`,
a physical relationship that regenerates for any forward year. It is used here
as **evidence**, not injected into the scorer as a synthetic actual.

---

## Step 2 — diagnose the model (computed, in order)

### (a) Adder over-suppression — **CONFIRMED root cause**

Model PS discharge under the keeper's $10 adder (pjm_46 re-solve,
`storage.parquet` P1):

| Year | Model PS @ $10 | CF | Reconciled actual |
|---|---|---|---|
| 2023 | **1.58 TWh** | 3.6% | 6.48 (B) / 7.6–10.1 (A) |
| 2025 | **2.90 TWh** | 6.6% | ~8–10.6 (A) |

The model is **under-cycling by ~60–80%**. Why: with the $10 adder the arbitrage
breakeven is `P_high > P_low/RTE + adder` (RTE 0.80 → `P_high > 1.25·P_low + 10`).
On the 2025 model hub price (load-weighted):

| | days clearing breakeven (of 365) |
|---|---|
| adder **$10** | **125 (34%)** |
| adder **$0** | **340 (93%)** |

Median daily max/min ratio = **1.473** — well above the 1.25 RTE breakeven — so
the bread-and-butter intraday spread *is* profitable; the $10 adder kills it on
**215 days/yr**. The adder is suppressing legitimate arbitrage, exactly the
CLAUDE.md #12 failure mode (a knob tuned to a mis-measured residual).

### (b) Price-spread / scarcity tail — present, but **not the binding cause here**

The energy-only LP does compress PJM's tail (C3c, scored on pjm_47: model **0
hours > $200** vs actual **6 / 18 / 59 hours** for 2023/24/25) — the same
compression the coal/scarcity workstream already carries. **But unlike NEISO,
this is not what idles PS:** the
ordinary intraday spread already clears the RTE breakeven on 93% of days at
adder 0. Tail recovery would add *more* arbitrage on top, but PS under-cycling is
driven by the **adder**, not the tail. The tail piece is handed to the scarcity
workstream as an *additive* lever, not the root cause of PS cycling.

### (c) Energy / power cap — non-binding

5046 MW × 10 h = 50.5 GWh. At the fixed 6.3 TWh that is ~125 cycles/yr (≈ once
per 2.9 days) — the cap is a soft regulator, never the binding constraint. At
$10 the model is nowhere near it.

### (d) RTE / SOC — correct

`PUMPED_STORAGE_RTE = 0.80`; the re-solve's charge/discharge ratio is 0.80 to
three figures; cyclic SOC standard. No defect.

---

## The fix

**Retire the fitted PJM PS dispatch adder** (`constants.py`:
`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO = {"PJM": 10.0}` → `{}`, resolves to 0.0).
It was demonstrably fitted to a mis-measured EIA-923 PS *net* figure read as
gross discharge (CLAUDE.md #12 — no forward analogue), so it is removed, not
recalibrated to a different number. PJM PS now arbitrages on its physical RTE
like every other storage resource.

**Result of the retirement (pjm_47 re-solve, all years):**

| Year | Model PS @ $10 (before) | Model PS @ $0 (after) | CF after | Reconciled actual |
|---|---|---|---|---|
| 2023 | 1.58 | **6.34** | 14.3% | 6.48 (B) / 7.6–10.1 (A) |
| 2024 | — | **6.69** | 15.1% | 7.10 (B) / 8.0–10.7 (A) |
| 2025 | 2.90 | **7.04** | 15.9% | ~6.8–10.6 (A) |

The fix lands PS on the **lower-reconciled (Method B) actual within ~6%** — it is
**not runaway** (the energy cap + spread economics self-regulate it to ~14–15%
CF). Price effect (2023, load-weighted hub): mean **29.00 → 28.84** (−0.5%),
trough p5 +$0.8 (PS charging), peak p95 −$0.7 (PS discharge) — the textbook,
physically-correct spread compression of storage arbitrage. C3a/C3b are
preserved.

**Forward-valid replacement, if ever needed.** PJM PS units genuinely commit
capacity to synchronized reserve / regulation, a real opportunity cost. The
*concept* of a reserve-duty adder is legitimate; the **$10 magnitude was not** (it
was fitted, not measured). Should PS later over-cycle against a real ceiling, the
forward-valid lever is a **measured PJM synchronized-reserve power reservation**
— the analogue of ERCOT's `reserve_storage_as_power` (which reserves measured
hourly up-AS MW from the dispatch power cap) — handed to the reserve workstream.
That is a measured reserve *quantity* that responds to forward conditions, not a
throughput tune.

## C5b classification / ledger

- **2023 / 2024 / 2025 → `SKIPPED`** (no separable EIA-930 PS/BAT series for PJM;
  PS folded into "Hydro"). Ledgered as **ACCEPTED MEASURED-INPUT LIMITATION** —
  the *actual* is unobservable in committed artifacts, not a model defect.
- The fixed model's 6.3–6.7 TWh agrees with the reconciled ~6.5–7 TWh (Method B)
  to within ~6% (inside the C5b ±30% band, were it scoreable). This is recorded
  as supporting evidence, **not** a scored pass — no synthetic actual is injected
  into the scorer (mirrors the NEISO precedent).

## What the fix does *not* claim

The PJM keeper's dominant residual is the **coal/gas family volume** (C1/C2
FAILs: 2024 COAL_BIT −10.8 TWh, 2025 gas +11.4%) owned by the coal-operations /
price-formation workstream — unchanged by this PS fix. Retiring the adder fixes
the **PS mechanism** and removes a fitted knob; the determination stays `NOT-YET`
on the coal/gas residuals. That is the honest, rubric-correct outcome.
