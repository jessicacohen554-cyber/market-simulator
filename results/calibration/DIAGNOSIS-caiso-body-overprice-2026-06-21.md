# CAISO 2024 body overprice (+$6) — localization and root cause (2026-06-21)

Branch: `claude/caiso-lmp-lever-ab-m56edy`. Goal: close the keeper's
load-weighted body from model mean 42.0 toward actual DA 35.8 **without**
breaking the negative tail (neg precision 92%) or the peaks (p95). Diagnosis
first; ground every change in measured data (EIA-930 interchange/renewables).

Validation convention (`scripts/caiso_lmp_validate.py`): model hourly price =
load-weighted `price` across zones from `system.parquet`, `pass=='P2'`, grouped
by hour; actual = `da` column of
`data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`, 2024, 8760-hr
overlap.

## TL;DR

The +$6.15 mean residual is **not uniform** and **not a volume miss**. It is a
**diurnal-shape error in the priced import node**: the static node imports a
near-flat **~4 GW every hour**, but real CAISO net imports follow a strong duck
curve — **5.2–5.6 GW overnight, 1.0–1.6 GW midday**. The flat node therefore

1. **over-imports midday** (model ~3.9 GW vs measured ~1 GW) → CAISO is modeled
   *short* midday, so a positive import block ($28 firm hydro) sets the floor,
   whereas reality is *long* (exports the solar glut) and prices ~$14; and
2. **under-imports overnight** (model ~4 GW vs measured ~5.5 GW) → more gas runs
   → gas-CC sets ~$48–50 vs the real ~$42.

These two halves are **60% and 44% of the $·h gap**; the under-priced evening
ramp (-21%, model too flat) partly offsets. The mean is `+6.15`; `p50 +10.26`;
`p95 -3.59` (peaks already slightly under).

## Refuted hypotheses (grounded)

| hypothesis | check | verdict |
|---|---|---|
| renewable volume understated → too much gas | model solar 47.7 vs EIA-930 44.6 TWh (**over every month**); wind 20.3 vs 20.1 (spot on) | **refuted** |
| imports too scarce (annual) | model net imports 35.1 vs EIA-930 32.4 TWh (**+2.7 over**) | **refuted (annual)** — but mis-*shaped*: see below |
| midday floor is a volume miss | solar is over, not under, in every month incl. winter | **refuted** — it is a *pricing* miss |

## Where the $6 lives

Residual by hour-of-day block (share of the +53,871 $·h gap):

| block | mean resid | share | setter |
|---|---|---|---|
| midday h08–14 | +12.6 | **+60%** | over-imports → $28 import floor (reality long → ~$14) |
| overnight h22–05 | +8.1 | **+44%** | under-imports → gas-CC $48–50 (reality $42) |
| morning h06–07 | +6.9 | +9% | ramp |
| shoulder h15–17 | +3.6 | +7% | — |
| evening h18–21 | −7.6 | **−21%** | model too flat ($50), misses the $66 ramp peak |

By season the over-price is spring-heavy (MAMJ +52%) and winter shoulder (Feb
+17.8, Nov +10.3, Dec +17.5); summer (JASO) is well-calibrated (+15%); **January
is *under* (−20)** (cold, high-load, gas-set, no belly).

### The diurnal import smoking gun (model vs EIA-930 net import, MW)

| | overnight h22–05 | midday h10–14 |
|---|---|---|
| model | ~4.0 GW (flat) | ~3.9 GW (flat) |
| EIA-930 | **5.2–5.6 GW** | **1.0–1.6 GW** |
| error | **−1.2…−1.6** | **+2.3…+2.9** |

Net imports are also mis-shaped by month (Dec −1.4 TWh **under**, Jan +1.5
**over**), and the monthly import error correlates with the price residual
(under-import months over-price). Both the diurnal and the monthly miss are the
same cause: a single flat price/availability vector on the static node.

## Levers tried this session

| run | lever | mean | p50 | neg (prec) | verdict |
|---|---|---|---|---|---|
| caiso 15 | keeper repro (baseline) | 42.0 | 46.8 | 407 (92%) | baseline |
| (probe) | `--interchange-shaping-export-only` | 42.0 | 46.8 | 407 | **byte-identical no-op** — model is short midday, no surplus to export |
| caiso 16 | `--interchange-shaping` (full) | 51.3 | 53.8 | 88 (100%) | **regression** — see below |

**Why full interchange-shaping regresses:** `inject_interchange_shape` caps each
import tranche's availability by `import_cap / import_total`, where
`import_total` is the **full 11.4 GW tranche capacity**. Even overnight — where
the measured envelope is high (5.5 GW) — that fraction is < 1, so the cheap
baseload imports are starved and gas substitutes in *every* hour (+15 across the
board, mean 42→51). An availability cap-of-total is the wrong instrument; it
cannot raise the diurnal contrast without also starving the overnight baseload.

## Root cause and the grounded next lever

The cause is structural and measured: **the priced import node has no diurnal
shape.** The fix must be a *measured diurnal* lever that

* keeps (or deepens) the cheap **overnight** imports (so gas backs off → the
  +44% overnight body falls toward $42), and
* backs the spurious **midday** imports off / reprices them down (so CAISO is
  modeled long midday → the +60% midday floor falls toward $14),

without flattening into the export sink everywhere (which would over-shoot the
summer/winter midday, where reality is a *positive* ~$24–30, not negative). The
existing `--caiso-import-solar-shape` already does the deep-spring-belly half
(collapse the marginal blocks to −$20); the missing piece is the **broad-midday
/ overnight diurnal price shape** for the months/hours the annual net-load gate
does not reach. This is the candidate for the next run; an availability cap is
not (caiso 16).

Note the evening ramp (−21%) is *under*-priced and helping the mean — a diurnal
reshape must avoid lifting it, or the mean gap widens.
