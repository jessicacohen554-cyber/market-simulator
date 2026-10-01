# RESULT — miso-264: MISO's gas-offer margin was identified at a FROZEN anchor and priced against it in every year. Armed, solved, registered — and the 2020 object is measured NOT to be an offer object at all

```
SESSION : miso-264        ISO: MISO        PARENT LP: ZERO (rule 32 [R-SHARD] (a)).
KEEPER  : 2026-09-19-miso-263-coal-ceiling (results/calibration/miso263_coalcap_span)
          — UNCHANGED. Train tier 2023-2025 CALIBRATED, C3c the lone ledgered caveat.
NEW RUN : 2026-09-20-miso-264-anchor-vintage (results/calibration/miso264_anchor_span),
          2020-2025, registered. NOT promoted — the promotion question is §8.
OBJECT  : the BULK price residual FINDING-miso262 §5 reported and did not fix.
LP      : 6 shard-years, one per shard (rule 36 [R-YEAR-ISOLATION]). No re-solves.
```

---

## 1. THE CHARTER'S QUESTION, ANSWERED AT ZERO LP

*"What sets the bulk price in 2020's internal zone-hours, class by class."*

Method: the keeper's own 2020 fleet/offer arrays rebuilt with no LP through the
sanctioned `scripts/lib/bundle_fleet.reconstruct_bundle_fleet`, then every
internal zone-hour's committed P1 dual matched against the available offer rows
at a tolerance **fixed at $0.05/MWh before the first number**. MISO 2020 has
zero slack, zero dump and a non-zero reserve dual in 0.01 % of hours, so the
energy dual is a clean marginal-offer read.

**The identification is essentially complete: 99.4 % of internal MWh match a
row**, and of the 0.6 % that do not, **0.00 % lie above or below the whole live
stack** — every unmatched hour's dual is interior, i.e. a congestion blend, not
a missing price-setter. Tolerance sensitivity (pooled matched share): 84.7 % at
$0.01, 99.4 % at $0.05, 99.97 % at $0.10, 100.0 % at $0.25.

MWh-weighted share of the price-setting role, 2020, pooled over internal zones:

| model price band | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| p00–p10 | **CC econ 53.7 %** | coal econ 9.2 % | CC committed 8.5 % | ST_CHP 7.8 % |
| p10–p50 | **CC econ 33.7 %** | coal econ 22.3 % | ST_CHP 8.6 % | ST_GAS econ 6.7 % |
| p50–p90 | **coal econ 53.8 %** | CC econ 9.5 % | CT econ 8.5 % | ST_GAS econ 7.7 % |
| p90–p100 | coal econ 34.8 % | CT econ 21.7 % | ST_GAS econ 9.3 % | CC econ 8.9 % |
| all | coal econ 36.3 % | CC econ 21.8 % | CT econ 8.1 % | ST_GAS econ 7.0 % |

**MISO's 2020 bulk is a two-class stack — gas CC econ owns the bottom half of
the price distribution, coal econ the top half — and the seam owns 7.7 % of the
cheapest decile and ~3 % overall**, which independently reproduces
`FINDING-miso262` §4's 12.6 % hour-count measurement of the same thing.

That matters because the miss is **worst at the bottom**: model p10 $20.34 vs
RT $14.58, model p50 $26.60 vs RT $19.86. The decile the model over-prices
hardest is the one a **gas** class sets 54 % of.

## 2. AND THE 2020 MISS IS IN NOBODY'S CURVE

The same census carrying each matched row's physical heat rate, delivered fuel
and markup, set beside the same hours' measured RT on the scale-free
implied-marginal-heat-rate basis (`_miso264_marginal_hr_2020.py`):

| family | share | mc | fuel leg | above fuel | phys HR | markup HR | Δ implied HR |
|---|---:|---:|---:|---:|---:|---:|---:|
| coal econ | 36.3 % | 28.17 | 23.71 | 4.45 | 12.482 | 0.000 | **+1.90** |
| CC econ | 21.8 % | 23.87 | 21.20 | 2.67 | 8.881 | 1.236 | **+1.66** |
| CT econ | 8.1 % | 29.43 | 22.60 | 6.83 | 10.556 | 3.770 | +1.49 |
| ST_GAS econ | 7.0 % | 28.24 | 22.45 | 5.78 | 10.521 | 2.014 | +1.66 |
| CT committed | 5.4 % | 27.46 | 23.50 | 3.96 | 11.256 | 0.826 | +1.77 |
| ST_CHP | 5.1 % | 24.49 | 20.89 | 3.60 | 7.962 | 0.000 | +1.49 |
| CC committed | 4.0 % | 24.25 | 22.42 | 1.83 | 9.364 | 0.107 | **+2.01** |
| coal committed | 3.1 % | 27.84 | 23.36 | 4.48 | 11.502 | 0.000 | +1.94 |
| coal peak | 1.7 % | 29.52 | 25.07 | 4.45 | 15.315 | 0.000 | +1.41 |

**The gap is +1.41 to +2.01 in EVERY family, gas and coal alike.** No class is
the carrier, so a lever repricing one class cannot be the repair — which
independently re-derives `FINDING-miso262` §6's refusal of the COAL_BIT band
lever, by a different instrument.

**Disclosed because it weakens the reading:** the uniformity is partly
arithmetic. `Δ imHR = (mc − RT)/fuel`, `mc ≈ λ` by construction of the census,
and delivered gas varies only over $1.64–$2.62 across families, so a roughly
uniform $/MWh gap over a roughly uniform fuel level must come back roughly
uniform. What the table adds beyond that is the **decomposition**: the non-fuel
wedge runs $1.83 (CC committed) to $6.83 (CT econ), a five-fold spread, while
the miss does not move. A defect invariant to that is not living in the wedge.

## 3. THE DEFECT THAT ANSWERING IT TURNED UP

`gas_offer_net_revenue_margin` (`K` since miso-83) adds
`mc[g,t] += offer_markup_hr[g] × (anchor − fuel[g,t])` to every gas tranche
with a positive markup, and its own documentation states the identity that
makes the anchor meaningful: **at `fuel == anchor` the reformed offer reduces
EXACTLY to the registered band multiplier — "the identification point, not a
tunable".** The term is a linear extrapolation with no saturation.

The keeper prices **all six years** at `3.0492 $/MMBtu`, the frozen mean over
the **2023-2025** window. The solve year's own mean, resolved by `run_year`'s
own production block:

| year | frozen | the year's OWN anchor | Δ | that year's Henry Hub |
|---|---:|---:|---:|---:|
| 2020 | 3.0492 | **2.3294** | **−0.7198** | 2.03 |
| 2021 | 3.0492 | **4.0189** | **+0.9697** | 3.72 |
| 2022 | 3.0492 | **6.5881** | **+3.5389** | 6.45 |
| 2023 | 3.0492 | 3.0187 | −0.0305 | 2.54 |
| 2024 | 3.0492 | 2.5580 | −0.4912 | 2.19 |
| 2025 | 3.0492 | 3.8190 | +0.7698 | 3.52 |

**In 2022 the model prices its entire gas offer surface off an identification
point $3.54/MMBtu — 54 % — below the fuel its units actually burn.**

`gas_offer_margin_anchor_vintage` (pjm-169, built, default-off, byte-identical
off, cache-key registered at its declared `False`) evaluates the same
measurement on the solve year. MISO's matrix cell read `U` with the evidence
*"it is this lane's to adjudicate on its own market's data (rule 25)"* — so the
arm is on-queue by the matrix's own words. **Zero new fields, zero free
parameters; the DOF ledger carries over verbatim at 43 / 2, 0 added.** Rule 1
`[R-STRUCT]`'s price-tuning carve-out is **not** invoked: the
`offer_curve_by_group` multipliers are byte-identical in every year, and this
restores the condition under which they mean what they were calibrated to mean.

## 4. THE PREDICTION WAS REGISTERED BEFORE THE SOLVE, AND IS SCORED AGAINST

`PRECOMMIT-miso264` §4 published a per-year first-order price move computed at
zero LP from §1's census and the exact armed-minus-control `mc_base` difference
(whose per-row shift is constant in `t` to 5.7e-14 — measured, not assumed).

| year | predicted Δ price | **realised** | ratio |
|---|---:|---:|---:|
| 2020 | −0.553 | **−0.403** | 0.73 |
| 2021 | +1.251 | **+0.753** | 0.60 |
| 2022 | +7.513 | **+3.446** | 0.46 |
| 2023 | −0.044 | **−0.031** | 0.69 |
| 2024 | −0.839 | **−0.570** | 0.68 |
| 2025 | +1.593 | **+1.047** | 0.66 |

Correct sign in all six, 46–73 % of first order, damped most where the offer
move is largest — the signature of LP re-dispatch. The resolved anchors
reproduce the pre-registered values to seven significant figures.

**ONE PREDICTION WAS WRONG, AND IS CORRECTED RATHER THAN DROPPED.** §4 item 2
predicted C1 2022 CC_REGULAR would **deepen** to ~−13 TWh through the
`FINDING-miso262` seam transducer. It **improved by +1.82 TWh** instead. The
reason is an intra-gas merit reshuffle the prediction did not model: the arm's
`mc` shift is ~4.5× larger on CT than on CC (2022 cap-weighted **+18.976** CT
econ / **+94.722** CT peak against **+4.214** CC econ), so CT_PEAKER cedes
−6.557 TWh to CC_REGULAR (+1.820), CC_CHP (+1.661) and imports (+3.382)
together. The seam took +3.382 TWh exactly as the transducer predicts; it was
simply not the only thing moving.

## 5. GATES, AS SCORED — SAME SCORER, SAME COMMITTED BENCH, SAME SESSION

| | incumbent `miso-263-coal-ceiling` | **this run** |
|---|---|---|
| **train tier 2023-2025** | **CALIBRATED** | **CALIBRATED** |
| full span | NOT-YET | NOT-YET |
| grade summary | scored 8 / target 4 / ledgered 1 / fails 3 | **identical** |
| C1 2020 COAL_BIT | −10.29 **FAIL** | **−10.92 FAIL** (deeper) |
| C1 2022 CC_REGULAR | −9.47 **FAIL** | **PASS** |
| C1 2022 COAL_PRB | +7.90 pass | **+8.13 FAIL** (new) |
| C3a 2020 | +16.3 % **FAIL** | **+14.6 % FAIL** |
| C3a 2022 | −14.6 % **FAIL** | **PASS** |
| C3b 2021 | 0.299 **FAIL** | **0.304 FAIL** |
| C3c | CAVEAT, ledgered | CAVEAT, ledgered |
| DOF added | 0 | **0** |

Failing criteria **3 → 3**; failing C1 cells **2 → 2** (one closed, one
opened); `price_mean` failures **2 → 1**.

| gate | verdict |
|---|---|
| `audit_keepers --iso MISO` | **E13 RED — EXPECTED AND CORRECT FOR AN UNDECIDED CANDIDATE.** Two registered runs, one not the keeper: that *is* the open promotion decision (§8). E3 warning pre-existing |
| `build_status --iso MISO --check` | **PASS** (in sync) |
| `check_mechanism_matrix --base origin/main` | **PASS** — 0 errors, keeper stamps and §5.x headers match |
| `check_gate_a_provenance --iso MISO` | **PASS** |
| `check_bench_freshness --iso MISO` | **PASS** — 6 parts, 0 STALE; 6 carry the engine-drift warning, and the parts **reproduce at HEAD**, which is the strong form |
| `_miso260_bench_parity` | **0.000000 TWh** — see §6 |
| `check_registry_payload_parity` | **as charted** — `caiso279_ablate_dswcouple_span` + 13 `spp51_*` (both pre-existing, neither MISO's) + this lane's 6 gitignored per-year dirs, each confirmed by `git check-ignore`. The local FILESYSTEM-sweep RED rule 31 documents; CI stays green |
| `check_cache_key_registration --base origin/main` | **RED AT BASELINE, NOT MINE.** `PPA_COST_RECOVERY_YR` / `REGIONAL_RENEWABLE_CF` undeclared in `solve_surface_declared`. Measured red in this container BEFORE any change. No new `ScenarioConfig` field here, zero key movement from this session |
| `pytest tests/scoring` | **22 failed / 1547 passed, both ways.** Failed NAME SETS compared, not counts: **zero new, zero fixed** |
| `node --check` | **PASS** on the edited matrix shard |
| ruff | check + format clean |

## 6. THE BENCH MOVES AT REGISTRATION — MEASURED, AND MY OWN PRECOMMIT WAS WRONG

Registering the bundle rewrites `frontend/data/backcast/bench/MISO/*.json.gz`
and moves the **actual** side by up to **2.651100 TWh** (2024 CC_REGULAR actual
143.4737 → 146.1248; an `oil` → `OTHER_FOSSIL` reclassification in every year,
e.g. 2025 oil 0.3530 → −0.0124 with OTHER_FOSSIL 8.5572 → 9.1738). That
**reproduces `RESULT-miso263` §5.1's magnitude EXACTLY.**

**`PRECOMMIT-miso264` §6 said the magnitude "does not reproduce". That was
wrong.** It rested on a hunk-by-hunk read of `e63f730a` (spp-49) showing every
new path gated on `benchmark_membership_vintage_union`, a field defaulting
`False` and byte-identical at `False` — which is a sound reason to doubt the
*attribution* and no reason at all to doubt the *magnitude*, which I had not
measured at the time. I have now, and it reproduces to six decimals. What stays
open is **which commit causes it**; that is routed to whoever owns spp-49, not
absorbed here.

Scoring a candidate against a moved actual is the miso-257 defect, so the parts
were restored to `origin/main` and **both runs were scored in one session
against the same committed bench**; parity then reads 0.000000.

## 7. WHAT THE SOLVE SAYS ABOUT 2020 — THE REAL FINDING

The arm improves 2020's price by −0.403 $/MWh **and deepens its coal deficit**
(COAL_BIT −10.29 → −10.92, COAL_PRB −3.33 → −4.76 on the gating basis), because
cheaper gas offers take more off coal: ST_GAS +1.23, CT_PEAKER +1.10,
CC_REGULAR +0.89 TWh against COAL_PRB −1.43, COAL_BIT −0.62, imports −0.66.

**So in 2020 the price residual and the coal-volume residual demand OPPOSITE
offer moves.** Price says the gas stack is too dear; volume says coal should be
running ~10 TWh more. Both can be true only if MISO's coal is held off the
system by something that is **not its offer** — an availability, commitment or
fuel-logistics constraint.

That is the same conclusion §2 reached from the other side, by a different
instrument, before any shard ran. **Two independent measurements, one
verdict: the 2020 object is a QUANTITY / COMMITMENT object, not an offer-level
one.** It is named and routed to the successor, not absorbed here, and no lever
in this session claims it.

## 8. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — THE OWNER'S CALL

**I do not have a confident recommendation, and saying so is the honest
report.** The arm is structurally right and gate-neutral:

**FOR.** The defect is real, measured and not about the residual: an
identification point defined as "the mean of the year's own delivered-gas
series" is being evaluated on a frozen window, and in 2022 that is 54 % wrong.
Rule 14 `[R-ACCURATE]` says keep the accurate input. Zero new fields, zero free
parameters, one pre-existing boolean. The train tier does not move. Two 2022
rungs close.

**AGAINST.** It trades one failing C1 cell for another (2022 CC_REGULAR closes;
2022 COAL_PRB fails by 0.13 TWh on a cell already at 99 % of its band), it
**deepens the charter's own named object** (2020 COAL_BIT −10.29 → −10.92), and
C3b 2021 slips 0.299 → 0.304. The grade summary is byte-identical, so nothing
in the rubric distinguishes the two runs.

Rule 14's own instruction, if the arm is promoted: the worse coal cells are a
**discovered bug to root-cause, not a reason to bury the accurate input** — and
§7 says where to look.

**RETRIEVABILITY (rule 34 (e)): a promotion costs ZERO re-solves.** The
registered composite is committed. Every per-year leg carries its FULL bundle
including `dispatch/<y>_P1.parquet` on its own branch at a full immutable SHA,
recorded in `.gitignore`:

```
2020  77b2e3b2f1bbb0a001fac53cdb9b15f0db9e283c
2021  96e389c953dd352ea2bc1b9840b396a2095e7c26
2022  85cf692355b4cc0acc4fea1ba1bcdd9aed448c3b
2023  c19a110345bf5007e8e81547de905afdbea381ac
2024  32c7d9fcd7fcea97092ebd3e4deb8bf9b57a93c3
2025  980c8287e15fff7509c5efa32ec834caa6b89c77
```

Nothing was deleted (rule 31). **If declined:** prune
`2026-09-20-miso-264-anchor-vintage` to clear E13; §3's defect still stands and
the keeper then knowingly prices 2022's gas surface 54 % off its own
identification point.

## 9. ROUTED, NOT ABSORBED

1. **The 2020 quantity/commitment object** (§7) — the successor's named object.
2. **The frozen derive is stale by 2.7 %.** The three in-window runtime anchors
   mean **3.1319** against the registered **3.0492**, because
   `derive_gas_offer_margin_anchor.GAS_SERIES_FLAGS["MISO"]` mirrors the
   **2026-07-23 miso-81** keeper's gas recipe, not today's. **No MISO test pins
   the two together** (NYISO's zonal variant carries such a pin; MISO's
   ISO-level one does not), so the gap is unguarded. Rule 23
   `[R-FROZEN-DERIVE]`; this arm does not fix it.
3. **The bench move's CAUSE** (§6) — magnitude settled, attribution open.
4. **`check_cache_key_registration` is red on `main`** for two undeclared
   solve-surface names that belong to no ISO lane.
5. **D-2 CT_PEAKER is over its 15 % cap in all six years on BOTH runs** (keeper
   50.6/45.7/27.1/26.6/19.0/16.1 %, arm 47.1/50.8/47.2/26.4/16.6/17.8 %) and
   2022 worsens most, for the same reason CT_PEAKER loses 6.6 TWh there.
