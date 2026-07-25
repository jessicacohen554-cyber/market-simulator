# FINDING — PJM's C3a-2025 residual is unmodelled nested-ORDC shortage depth, not a summer shoulder-hour level miss (pjm-120, 2026-07-25)

> **STATUS — IN PROGRESS (2026-07-25).** §1–§5 are complete and measured. §6's
> A/B arm (`pjm_reserve_pergen_sync`) is **solving**; its prediction is
> pre-registered below and has NOT been read. No keeper change is proposed and
> no lever is promoted in this document.

**Charter:** close PJM's last open gate — C3a mean LMP 2025, `−10.7 %` against a
`±10 %` band, the single NOT-YET criterion on keeper
`2026-07-24-pjm-119-overlay-restore` (9/10 scored PASS).

**Verdict — a clean split, both halves measured:**

1. The handoff's strongest named lead — *"2025 gas is above the anchor, so the
   fixed margin compresses offers in exactly the year that fails"* — is
   **REFUTED**. In the months that actually miss, delivered gas is *below* the
   anchor, so `gas_offer_net_revenue_margin` **raises** those offers. It
   compresses only in the months that already score well.
2. The gate does **not** turn on a shoulder-hour level miss. What separates
   2025 from the passing years is **14 hours** of genuine PJM reserve-shortage
   ORDC pricing the model structurally cannot reach. That unreachable mass is
   **3.3× the margin to the band edge in 2025 and ~zero in both passing
   years** (it is 22 % of the total 2025 residual — §3 is explicit about the
   distinction).
3. But product coverage is probably **not** the operative cause: the keeper
   carries ~10× slack on its reserve balance, so no ORDC family can bind at
   all (§6, pre-registered).

---

## 1. The gap is small and the arithmetic is unforgiving

C3a gates on the load-weighted RT actual (`rt_lw`, `calibration_verdict.py`
:1112) — 2025 `rt_lw = $45.80/MWh`. At `−10.7 %` the model is `≈ $40.90`; the
band edge (`−10.0 %`) is `$41.22`. **The whole gate is $0.32/MWh of annual
load-weighted price.**

That matters because it sets the bar for what counts as an explanation: any
mechanism worth more than ~$0.3/MWh annually is a candidate, and any mechanism
that also moves 2023/2024 by that much breaks a passing year.

## 2. The anchor/margin lead is refuted by the delivered-gas series

The handoff proposed that 2025 fails because gas ($3.52 HH) sits above the
`gas_offer_margin_anchor` ($3.3483), compressing offers via
`apply_gas_offer_margin`: `mc += markup_hr × (anchor − fuel)`.

The sign of that adjustment is set by the **delivered** series
(`data.fuel.trajectories._gas_series`, the keeper's own
`--gas-monthly-actuals` + daily-shape overlay), not by the annual Henry Hub
scalar. Measured, PJM 2025 monthly delivered $/MMBtu:

| Jan | Feb | Mar | Apr | May | **Jun** | **Jul** | Aug | **Sep** | **Oct** | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.79 | 4.99 | 4.07 | 4.03 | 3.41 | **2.99** | **3.26** | 2.89 | **2.66** | **3.12** | 3.94 | 5.09 |

Anchor = **3.3483**. Every month of the failing summer/autumn block
(Jun −20.1, Jul −9.0, Aug −4.6, Sep −8.5, Oct −6.7 $/MWh model−actual) is
**below** the anchor, so `anchor − fuel > 0` and the mechanism **lifts** those
offers. The months where it genuinely compresses — Jan 6.79, Feb 4.99,
Dec 5.09 — are the months that score best (Jan −0.9, Feb −2.0).

**The mechanism's sign is opposite to the residual it was proposed to explain.**
Lowering the anchor (e.g. to a pooled p50, $2.9449) would *reduce* the summer
lift and make 2025 worse. This lead is closed; `gas_offer_net_revenue_margin`
and its anchor are exonerated as the C3a-2025 driver, independently of the
owner's 2026-07-24 decision to keep the mechanism.

## 3. Where the residual actually lives — a discrete truncation, not a level

June 2025's mean is not a level; it is an event. On the equal-weighted June
hub series (mean $51.97, median **$31.30**) the top 5 hours alone contribute
**$8.91/MWh** of the monthly mean and the top 24 contribute **$16.27**. The
June 22–25 heat wave printed $1,722 / $1,319 / $1,286 / $1,285.

The actual 2025 price mass is extraordinarily concentrated at the top —
**14 hours (0.2 % of load) carry $1.99/MWh, 4.3 % of the whole $46.04
load-weighted mean**:

| actual stratum | hours | load share | contributes |
|---|---|---|---|
| 0–50 | 6,767 | 74.0 % | $23.34 |
| 50–100 | 1,655 | 21.3 % | $14.04 |
| 100–200 | 274 | 3.8 % | $4.97 |
| 200–376 | 45 | 0.7 % | $1.70 |
| **> 376** | **14** | **0.2 %** | **$1.99** |

The keeper's realized 2025 maximum is **$376**. Pricing the actual series
against that ceiling isolates the part of the mean the model cannot reach at
all:

| year | actual max | h > $376 | unreachable mass (equal-wt) | **unreachable mass (load-wt)** | C3a |
|---|---|---|---|---|---|
| 2023 | $631 | 2 | +$0.033/MWh | **+$0.039/MWh** | +4.7 % PASS |
| 2024 | $439 | 1 | +$0.007/MWh | **+$0.000/MWh** | −3.8 % PASS |
| 2025 | **$1,722** | **14** | +$0.693/MWh | **+$1.074/MWh** | **−10.7 % FAIL** |

**Be precise about what this does and does not claim.** The total 2025 C3a
residual is **−$4.90/MWh** (model $40.90 vs `rt_lw` $45.80); the truncation is
**$1.07** of it, about 22 %. The remaining ~$3.8 is a broad lightness which is
*not* the thing that distinguishes 2025 — 2023 runs **over** (+4.7 %), so the
bulk of the curve is not uniformly light across the window.

What the truncation *is* the explanation for is **the gate**. It is
**3.3× the $0.32/MWh margin to the band edge**, and it is ~zero in both
passing years. Removing it alone would move the three years to roughly
+4.8 % / −3.8 % / **−8.4 %** — i.e. it is the single component that explains
why 2025 fails while 2023 and 2024 pass, and it is worth fixing on structural
grounds independently of that (§5).

## 4. Those hours are a real, published pricing mechanism — measured

They are not statistical noise. PJM's own RT reserve settlement
(`data/raw/PJM-AS/reserve_market_results_2025.parquet`) shows a deep
simultaneous shortage across **all three** nested products at 2025-06-24
18:50 EPT:

| product | requirement (MW) | cleared (MW) | shortfall | clearing price |
|---|---|---|---|---|
| Synchronized (SR) | 2,515 | 1,619 | **−896** | **$2,550** = 3 × $850 |
| Primary (PR) | 3,678 | 1,621 | **−2,057** | **$1,700** = 2 × $850 |
| 30-Minute (Secondary) | 3,678 | 1,831 | **−1,847** | **$850** = 1 × $850 |
| Regulation | 1,000 | 993 | −7 | $4,206 |

This is exactly the cascade documented in
`docs/multi-iso/pjm-reserve-curve-source.md`
(`SRMCP = SP_SR + SP_PR + SP_30`, Manual 11 sec 4.4.1), with all three
demand curves pinned at their Step-1 **$850** penalty factor. The $1,722
energy LMP is that reserve scarcity rent arriving in energy through
co-optimization — PJM's post-2022 Reserve Price Formation design working as
filed.

Shortage is rare and tightly bounded, which is why it cannot be mistaken for a
level effect — PJM 2025 hours with a positive hourly-mean RTO shortfall:
**SR 12 h, PR 29 h, 30-Min 4 h**.

## 5. Why the model cannot reach it — one of three nested products

The ceiling chain is not a cap that needs raising; every parameter in it is
already correct and cited:

| element | value | site |
|---|---|---|
| Hard LP ceiling (load-shed slack at ISO VOLL) | **$2,000** | `config/iso_configs.py:763`, `model/lp/costs.py:124` |
| ORDC step-1 / step-2 penalty | **$850 / $300 (+190 MW)** | `data/raw/_validation-source/pjm_ordc_curve.csv`, Manual 11 §4.3.3 |
| Reserve families built in the LP | **Primary RTO + Primary MAD only** | `model/reserves/spec.py:1680-1729` |
| Top gas offer at June-2025 gas (CT_PEAKER peak ×4.0) | **≈ $144** | `pjm_campd_marginal_hr_summary.csv`, `assembly.py:506` |
| Post-solve scarcity adder | **none for PJM** (correctly skipped under co-opt) | `runner.py:1846-1852` |

So the model's *structural* June-2025 ceiling is `$144 + $850 = $994` in an
RTO-only zone and `$144 + $1,700 = $1,844` in a MAD zone — i.e. **the
published mechanism, if it bound, could reach the observed $1,722.** Nothing
here needs a bigger number.

What is missing is **product coverage**. PJM clears three nested reserve
products; the keeper's LP carries one:

* **Primary** (RTO + MAD) — live (`pjm_reserve_pergen=true`).
* **Synchronized** (RTO + MAD) — implemented but **default-off**
  (`pjm_reserve_pergen_sync=false`).
* **30-Minute / Secondary** — **not implemented in the LP at all**
  (`PJM_RESERVE_CASCADE` / `pjm_reserve_cascade_mcp` in `results/scarcity.py`
  exist only on the validation/overlay side).

In a shortage where reality stacks 3 × $850, the keeper can inherit at most
one layer. The count of scarcity hours is therefore reproducible (C3c passes:
39 of 59 hours > $200) while their **depth** is not — and C3c counts hours, so
it never registers the miss that lands squarely in C3a.

## 6. The supply side — why no reserve family can bind (pre-registered)

§5 establishes that the keeper prices one of three nested products. That is a
real structural gap. It is **not**, on this evidence, the operative cause — and
the keeper's own solve log says why:

```
PJM PER-GEN reserve co-opt ON: 39 R columns / 2405 member units
(eligible, ramp10>0; deliverable ramp mean 38.1 GW),
2 balance families (pjm_primary, pjm_primary_mad)
```

Two facts in one line. The families are **Primary RTO + Primary MAD only**
(§5 confirmed from the run itself, not inferred). And the model carries a
**mean deliverable 10-minute ramp of 38.1 GW** against a Primary requirement
of ~3.7 GW and a Synchronized requirement of ~2.5 GW — roughly **10× slack on
the reserve balance**.

Reality at the same moment is the opposite: at 2025-06-24 18:50 PJM *cleared*
only 1,619 MW of Synchronized reserve against a 2,515 MW requirement (§4). The
model's reserve supply exceeds PJM's realised cleared reserve by more than an
order of magnitude.

A demand curve only prices when the balance binds. With ~10× headroom, no
ORDC family — Primary, Synchronized, or a future Secondary — can reach its
Step-1 penalty. **Adding products cannot fix a supply-side surplus.**

> **Pre-registered prediction, fixed before the arm was read.** The A/B arm
> `results/probes/pjm120_syncarm_2025` (keeper recipe + `--set
> pjm_reserve_pergen_sync=true`, adding the measured Synchronized RTO+MAD
> families) will be **≈ inert on C3a-2025 (|Δ| < 0.2 pp)** and will not
> materially raise the 14 hours above $376. If instead C3a moves ≥ 0.5 pp, the
> product-coverage reading of §5 is the operative cause and this section is
> wrong.

If the prediction holds, the conclusion is that PJM's C3a-2025 gate **cannot be
closed by reserve-product coverage**, and the operative root cause is the
reserve *supply* side — the perfect-foresight, all-online dispatch leaving far
more deliverable ramp than PJM actually carries. That is the same LP-tightness
class the owner identified as G-20b (and ERCOT G-22), and it **independently
re-derives the owner's 2026-07-11 hold on `pjm_reserve_pergen_sync`** from a
different criterion (C3a rather than C3c) — strengthening, not re-opening, that
decision.

## 7. Guardrail review

* **Rule 1** — this relocates the residual onto a market-structure gap
  (missing published reserve products), not onto a level knob. No mechanism is
  judged by whether it improves the fit.
* **Rule 11** — the anchor refutation *keeps* the accurate measured input and
  declines the estimate-shaped "retune the anchor" move; the anchor's basis
  question is answered by measurement, not by the residual.
* **Rule 13** — every quantity used here is a measured market input or a
  published tariff parameter with a forward analogue (reserve requirements
  regenerate from Manual 11's LSC rule; penalty factors are filed constants).
  No outcome is pinned.
* **Rule 16** — the 2025-only replay in §3/§5 is an explicitly diagnostic
  probe, never registerable as a keeper.
* **Rule 22** — 2023–2025 only; no holdout year touched.

## Pointers

* Superseded framing: the pjm-119 handoff's "summer SHOULDER-hour price LEVEL
  miss" and its `gas_offer_margin_anchor` lead (§2 refutes both).
* Prior adjudication of `pjm_reserve_pergen_sync`: owner hold 2026-07-11
  (`docs/calibration-log.md`), scoped to **C3c's $75–200 afternoon band** —
  a different question from C3a's extreme-tail depth. See §6.
* Mechanism provenance: `docs/multi-iso/pjm-reserve-curve-source.md`.
