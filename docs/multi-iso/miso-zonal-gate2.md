# MISO Zonal Refinement — Gate 2 Scoring vs Actual Hub LMPs

**Date:** 2026-07-02. **Run scored:** `2026-07-02-miso-38-zonal-reserves`
(current MISO keeper: 6-zone phase 1 + phase 2 zonal reserve co-opt),
reproduced from its recorded flags at `origin/main` because the hourly
bundle parquets are gitignored (provenance appendix below; repro zone-mean
LMPs 28.62/26.04/34.73 vs the keeper's registered 28.65/26.06/34.74 —
faithful to $0.03).

**Actuals:** `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
(scope decision D6, landed 2026-07-02): the eight named trading hubs,
RT-final and DA-ex-post, on the model's chronological fixed-CST calendar
(re-indexed by the 2026-07-15 all-ISO scoring-clock fix; the gate numbers
recorded in this doc were computed against the original Central-prevailing
indexing, which paired CST-month hours one real hour off). Hub→zone:
Minn→West, Ill→Illinois, Ind→Indiana, Mich→East, Ark/La/Tx/MS→South
(member-hub mean); **Plains = MINN+ILLINOIS hub mean** (documented proxy —
no LRZ 3/5 hub exists, so Plains' pairwise orderings vs West and Illinois
carry no independent information).

**Verdict summary (details per check below):**

| Check | Verdict |
|---|---|
| 1. Zone-mean levels & spread signs | **PARTIAL** — the South-below-Midwest sign (the miso-35 open question) is REAL and the model has it right; magnitude understated ~2–15× and trending the wrong way; intra-Midwest mean order entirely absent (all five Midwest zones equal to the cent) |
| 2. Spread-duration & which pairs separate | **FAIL** — model 661–2,536 h >$1 vs actual 8,421–8,748 h; model >$20 ≈ 0 h vs actual RT 1,732–2,853 h (DA 1,083–2,509); model separation is ~97% the South leg only; the wind-hour West discount and the Indiana/East premium do not exist in the model |
| 3. Congestion timing | **PARTIAL** — the RDT S→N binding hours line up with actual South-cheapest hours with real skill (lift 1.5–2.4×, precision up to 92%); every other interface is silent or degenerate (binds with $0 shadow price) |

No fix is implemented in this session: the root cause (below) is diagnosed
but the faithful fix needs new published data (sub-regional flowgate
limits) and a scope decision (D1), not an offer/cap retune — per CLAUDE.md
#1/#11 nothing was tuned to this residual. `miso-38` remains the keeper.

## Representation caveats (read before the numbers)

1. Hub LMPs carry a **marginal-loss component**; model zone prices are
   lossless energy-balance duals (`td_loss_factor = 0`). A $1–2 persistent
   piece of every actual spread is losses, not congestion.
2. The model LP is deterministic perfect-foresight → closer in nature to
   **DA** than RT. Both are scored; DA is the fairer duration comparison
   (actual RT max spreads reach $523–842; DA $109–195).
3. Model spreads are exactly $0 in any hour with no binding constraint,
   so the >$1 duration tier is structurally hard for a lossless zonal
   model; >$5 and >$20 are the meaningful tiers.

## Check 1 — Mean LMP by zone and inter-zone mean spreads

### The miso-35 open question: is the model's South-below-Midwest sign real?

**Yes — sign confirmed.** Actual South mean LMP sits BELOW the Midwest
mean in all three years, in both markets. The model's sign is right; the
magnitude is understated and, worse, **trends opposite to reality** (the
model's gap shrinks over the years while the actual gap grows):

| year | actual RT S−Midwest | actual DA S−Midwest | model S−Midwest |
|---|---|---|---|
| 2023 | −2.39 | −1.94 | −1.09 |
| 2024 | −3.20 | −3.25 | −0.55 |
| 2025 | −4.96 | −5.56 | −0.32 |

Zone means, actual RT vs model ($/MWh; bold = priciest, italic = cheapest):

| year | series | West | Plains* | Illinois | Indiana | East | South |
|---|---|---|---|---|---|---|---|
| 2023 | actual RT | 28.75 | 28.48 | 28.20 | **31.79** | 29.96 | *27.04* |
| 2023 | model | 28.80 | 28.79 | 28.80 | 28.80 | 28.80 | *27.71* |
| 2024 | actual RT | 27.43 | 26.98 | 26.53 | **30.80** | 29.83 | *25.12* |
| 2024 | model | 26.14 | 26.14 | 26.14 | 26.14 | 26.14 | *25.58* |
| 2025 | actual RT | 40.20 | 38.77 | 37.35 | 42.85 | **42.88** | *35.45* |
| 2025 | model | 34.79 | 34.79 | 34.79 | 34.79 | 34.79 | *34.47* |

Actual mean order (RT): **Indiana > East > West > Plains > Illinois >
South** (2023/2024; 2025 East≈Indiana on top). Pairwise mean-order sign
agreement, model vs actual: **10/15 (2023), 5/15 (2024), 5/15 (2025)** —
and the 5 pairs the model gets right in 2024–25 are exactly the five
South-vs-Midwest pairs. All ten intra-Midwest orderings are wrong in
2024–25 because the model's five Midwest zone means are **identical to
the cent** (ties broken by sub-cent noise).

**Decomposition — the error is a Midwest error, not a South error.** The
model's South *level* is nearly right (27.71/25.58/34.47 vs actual RT
27.04/25.12/35.45). What's missing is the Midwest side: model Midwest
mean 28.80/26.14/34.79 vs actual RT 29.44/28.32/40.41 (−0.6/−2.2/−5.6).
The understated S−Midwest gap and the model's known system price-level
underprediction are the same residual, concentrated in the Midwest zones
— i.e. the missing Indiana/East premium and the missing scarcity tail,
not a mis-modelled South.

Conditional depth of the South leg (RT): actual separates < −$1 in
38/47/50% of hours at a conditional mean of −$10.7/−11.7/−16.5; the model
separates in 28/16/7% of hours at −$3.8/−3.2/−4.5 — right mechanism,
about a third of the depth, firing progressively less often when reality
fires more.

## Check 2 — Spread-duration curves and which pairs separate

| year | series | >$1 h | >$5 h | >$20 h | max $ | mean $ |
|---|---|---|---|---|---|---|
| 2023 | actual RT | 8,421 | 5,099 | 1,732 | 523 | 14.77 |
| 2023 | actual DA | 8,670 | 6,410 | 1,083 | 109 | 11.02 |
| 2023 | **model** | **2,536** | **650** | **1** | **21** | **1.12** |
| 2024 | actual RT | 8,552 | 5,821 | 1,816 | 657 | 16.47 |
| 2024 | actual DA | 8,705 | 6,521 | 1,166 | 154 | 11.84 |
| 2024 | **model** | **1,463** | **234** | **5** | **28** | **0.57** |
| 2025 | actual RT | 8,684 | 6,553 | 2,853 | 842 | 22.20 |
| 2025 | actual DA | 8,748 | 7,364 | 2,509 | 195 | 17.40 |
| 2025 | **model** | **661** | **209** | **0** | **16** | **0.34** |

The model is one to two orders of magnitude under on every tier — even
against DA — and its separation *declines* over the years while the
actual separation *rises*.

**Which pairs separate.** In the model, ~97% of all >$1-spread hours are
the South leg (South < −$1 vs the Midwest median in 2,460/1,428/619 h);
the only intra-Midwest price events in three years are East > +$1 in 46 h
and Plains < −$1 in 48 h (both 2023). In the actuals (RT, >$5-spread
hours): cheapest zone is **West** (40/37/27%) or **South** (28/35/36%)
with Illinois third; priciest is **Indiana** (39/37/25%), **West itself**
(24/23/35% — wind-drought hours), and East (20/22/25%). East and Indiana
are essentially never the floor.

**Wind-conditioning** (EIA-930 measured MISO wind, top/bottom quartile, RT):

| year | regime | actual W−E | actual W−Ind | actual cheapest | model W−E |
|---|---|---|---|---|---|
| 2023 | high-wind | −5.15 | −8.14 | W 50%, Ill 35% | −0.04 |
| 2023 | low-wind | +5.45 | +4.38 | S 46%, W 25% | 0.00 |
| 2024 | high-wind | −5.40 | −6.58 | Ill 42%, W 40% | 0.00 |
| 2024 | low-wind | +2.32 | +1.36 | S 61%, W 22% | 0.00 |
| 2025 | high-wind | −7.31 | −7.48 | Ill 51%, W 41% | 0.00 |
| 2025 | low-wind | +3.57 | +3.51 | S 66%, W 4% | 0.00 |

So in the actuals **West IS the discount zone in high-wind hours** — and
flips to the premium zone in wind droughts (priciest zone in 56% of 2025
low-wind hours); **South is the discount anchor in low-wind hours**; the
persistent premium is **Indiana** (East joins it in 2025), not East
alone. The model reproduces none of this: its West−East spread is zero
in both wind regimes because West never exports at a binding limit
(median model West net flow is an *import* of 1.3–2.0 GW; exports peak at
1.4 GW against a 3.3–3.8 GW CEL — the West CEL binds **0 hours in all
three years**).

## Check 3 — Congestion timing

Model binding-hour inventory (net flow within 1 MW of cap):

| year | RDT N→S | RDT S→N | West CIL | East CIL | Illinois CEL | Plains CEL |
|---|---|---|---|---|---|---|
| 2023 | 91 | 3,066 | 1,152 | 92 | 154 | 87 |
| 2024 | 323 | 2,022 | 238 | 0 | 567 | 0 |
| 2025 | 1,053 | 825 | 661 | 0 | 970 | 0 |

- **The RDT leg has real timing skill.** Model RDT S→N binding hours
  coincide with actual South-cheapest hours well above chance: RT lift
  1.5/1.8/2.4× (precision 43/64/87% vs base 28/35/36%), DA lift
  1.5/1.7/2.1× (precision up to 92% in 2025). The one constraint that
  fires with a price effect fires at approximately the right times.
- **"Any interface binds" has no skill against overall large-spread
  hours** (lift 0.9–1.2×) — actual >$5 spreads are so common (58–84% of
  hours) that a ~3,000-hour binding set cannot discriminate, and most of
  the model's non-RDT "binding" carries no price anyway (next bullet).
- **The CIL/CEL groups mostly bind degenerately.** West CIL sits at its
  cap 1,152/238/661 h, yet West's price deviates from the Midwest median
  by **$0.00 in every one of those hours** — the flow parks at the cap
  because inter-Midwest flows are cost-indifferent (identical marginal
  stacks, generous bilateral TTCs), so the constraint's dual is $0. Cap-
  touching without a shadow price is not congestion. The only shadow-
  priced non-RDT events in three years are the 46 h East-CIL and 48 h
  Plains-CEL episodes of 2023.

## Root cause (structural, per rule #1 — no tuning to the residual)

1. **The LOLE CIL/CEL island envelopes are the wrong physical object for
   hourly energy-market congestion.** They are simultaneous-import/export
   *adequacy* limits (5–17 GW, sized for LOLE transfer at peak), an order
   of magnitude above the level at which real Midwest congestion prices —
   actual congestion binds on specific flowgates (MWEX/NDEX wind-export
   paths, IN→MI, the WUMS interfaces) long before a zone's entire
   simultaneous envelope is exhausted. The phase-1 design knowingly took
   the only published, reproducible limits available (scope §2, D4) and
   they were the right choice for *adequacy-scale* structure (the RDT
   works; the 2023 East/Plains episodes are real events) — but they
   cannot produce the observed $3–6 persistent intra-Midwest means or the
   ±$5–7 wind-regime West swing. The deliberately generous bilateral TTCs
   (placeholders per §2.2) leave the interior copperplate-by-construction.
2. **No marginal-loss component in zone prices** (`td_loss_factor = 0`).
   A persistent $1–2 of the actual mean spreads (West negative, load-east
   positive) is losses; the model's duals cannot show it by design.
3. **Deterministic perfect-foresight LP vs RT volatility.** Actual RT max
   spreads ($523–842) and roughly a third of the >$20 RT tail are
   transient re-dispatch events; even perfect zonal structure would score
   nearer the DA row. This bounds attainable duration-curve agreement but
   explains neither the flat means nor the missing DA-scale separation.
4. **The Indiana/East premium is (at least partly) seam pull.** Indiana
   hub is the priciest actual zone while hosting MISO's PJM seam; the
   model prices the seam at the border node but nothing inside the
   Midwest lets Indiana separate from Illinois when exports pull east.

**Next levers, in structural-faithfulness order** (all need new inputs or
scope decisions — none is a cap/offer retune):

- **Published sub-regional flowgate/IROL limits** for the recurring
  Midwest constraints (MISO daily market reports publish the binding
  constraints and shadow prices; MTEP/planning studies publish select
  flowgate ratings). A D6-style fetch would give measured, forward-
  reproducible per-path limits to replace the generous placeholders on
  L1–L6 — the direct fix for the degenerate-binding interior.
- **D1: split Michigan (Z7) from Wisconsin (Z2)** so the strongest real
  import pocket can price separately (blocked on a Z2/Z7 load split).
- **Marginal-loss factors on links** (real physics, forward-reproducible)
  to recover the persistent $1–2 loss component of zonal spreads.

## Keeper standing

`2026-07-02-miso-38-zonal-reserves` **remains the keeper** — it is still
the most structurally faithful MISO run; this scoring changes its
*documentation*, not its standing. Its registry definition is updated to
record the gate-2 measured outcome (South sign confirmed real; RDT timing
skill real; intra-Midwest separation absent; duration curves 1–2 orders
under). The phase-1 "prices separate" gate claim should be read with this
scoring's caveat: the miso-35/38 spread counts are ~97% the South leg,
and most non-RDT interface "binding hours" carry a $0 shadow price.

## Reproduction provenance (appendix)

The keeper's `system.parquet`/`flows.parquet` are gitignored, so the run
was re-solved from its recorded configuration at `origin/main` (4443bad):

```bash
MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1 PYTHONPATH=.:src \
  .venv/bin/python scripts/run_calibration_full.py --iso MISO \
  --year 2023 2024 2025 --out-dir results/calibration/_diag_miso38_gate2 \
  --coal-bit-sigmoid --ct-intermediate-split --cc-intermediate-split \
  --st-gas-intermediate --miso-zonal-gas-basis --cc-nameplate-summer-derate \
  --priced-interchange --reference-price-interface --miso-firm-imports \
  --miso-seam-flow-limit --miso-seam-export-limit --miso-pjm-border-anchor \
  --energy-reserve-coopt --miso-zonal-reserves
```

(All other keeper `meta.json` flags are argparse defaults; verified by
diffing `meta.json` against the parser. 12 GB swapfile +
`MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1` required, per
`docs/multi-iso/miso-reserve-coopt.md`.)

**Fresh-clone hazard found and handled — two silent clean-layer
fallbacks.** The gitignored `data/clean/` layer must be regenerated
before any MISO zonal solve, or the run silently degrades:

- `zonal-shares` absent → static annual load shares (no hourly zonal
  shape). Regenerate: `scripts/data/curate_zonal_shares.py --iso MISO --year
  2023 2024 2025`.
- `capacity-deliverability` absent → static PY2025-26 summer CIL/CEL
  fallback instead of the per-season measured vectors (WARNING in log).
  Regenerate: `scripts/data/curate_capacity_deliverability.py --iso MISO`.

A first repro attempt ran with the static-cap fallback; after curation
the correct seasonal run produced zone means identical to $0.02 — at
current binding levels the seasonal caps barely move system results,
consistent with the degenerate-binding finding above.

Fidelity vs the registered keeper: zone-mean LMP 28.62/26.04/34.73 vs
28.65/26.06/34.74; duration-curve max 54.5/65.9/70.4 vs 54.5/62.0/70.4
(2024 max is a fragile tail statistic; means match to $0.03). Binding
inventories differ modestly from the miso-35 gate-1 report (e.g. Illinois
CEL 154 vs 1,199 h in 2023) — expected drift from the co-opt dispatch and
main-branch movement since the keeper's dirty-tree sha; the price-side
conclusions are insensitive to it.

Scoring scripts: `scripts/report_miso_zonal_gates.py --bundle
results/calibration/_diag_miso38_gate2` (standard gates) plus the
session's extended analysis (spread-duration tiers, wind conditioning on
EIA-930 `NG: WND` quartiles, binding-vs-actual timing lift, conditional
South depth); actuals from the D6 parquet as described above.
