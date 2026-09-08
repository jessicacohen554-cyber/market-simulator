# FINDING — ERCOT 2021's C3a/C3b is a MISSING-DATA defect: no HSL parquet

**Session** ercot-256b · **ISO** ERCOT · 2026-09-08 · **Zero LP**
**Keeper measured** `2026-09-08-ercot256-drag-layup-mask`
(`results/calibration/ercot256_five_year_keeper`)

---

## 1. HEADLINE

ERCOT 2021's `C3a +26.2 %` / `C3b 0.333` is **not a level miscalibration and not an
offer-curve problem**. It is the model being unable to form **low and negative prices**,
because ERCOT's uncurtailed-renewable-potential (HSL) dataset **exists for 2023/2024/2025
and does not exist for 2021/2022**. Without it the LP is handed wind and solar
*already net of curtailment*, so it has no surplus to curtail, wind is never marginal, and
the price can never reach the −$26/MWh wind offer the config already carries.

**This is a data intake, not a lever.** Rule 14 `[R-ACCURATE]`.

---

## 2. THE MEASUREMENT — the error is entirely in the bottom of the stack

2021, HB_HUBAVG settle vs the keeper's North-zone hourly price:

| pct | actual | model | ratio |
|---|---|---|---|
| min | **−31.65** | **+17.57** | — |
| p1 | **−4.60** | **+21.12** | — |
| p5 | 8.15 | 43.07 | **5.29×** |
| p10 | 13.44 | 49.81 | 3.71× |
| p25 | 18.00 | 57.35 | **3.19×** |
| p50 | 24.84 | 65.33 | 2.63× |
| p75 | 37.10 | 79.77 | 2.15× |
| p90 | 56.18 | 103.96 | 1.85× |
| p95 | 81.01 | 126.96 | 1.57× |
| p99 | 8,866.15 | 6,303.38 | **0.71×** |
| max | 9,024.06 | 10,771.42 | 1.19× |

**The tail is roughly right; the bottom three quartiles are 2.1–5.3× too expensive.** The
model has a hard floor at **+$17.57** and **zero hours at or below $0**, against an actual
whose bottom ~2 % is negative.

The monthly split shows the same thing and explains why the *annual* number looks mild:

| | model | actual | bias |
|---|---|---|---|
| **Feb (Uri)** | 1,302 | 1,522 | **−14 %** |
| every other month | 57–130 | 19–47 | **+79 % … +196 %** |

February's ~$1,522/MWh dominates the load-weighted annual mean, so a −14 % miss there very
nearly cancels a **+138 % average miss across the other eleven months**. The headline
+26.2 % is two large errors offsetting — which is also why C3b (shape) fails alongside C3a.

---

## 3. THE CAUSE — stated by the loader itself

`src/market_sim/data/renewables.py`, module docstring, verbatim:

> "Because the EIA generation series reflect *delivered* output, they already embed
> real-world curtailment (roughly 5 % for wind and solar in ERCOT and CAISO), so for most
> ISO-years the derived CF profiles inherit that curtailment and **the dispatch does not
> separately re-curtail**.
>
> The exceptions are the backcasts with an hourly uncurtailed-potential (HSL) dataset, where
> the CF profile is built from that instead … so the dispatch is handed the *uncurtailed*
> potential and **re-curtails** wind and solar under the modeled transmission limits …
>
> * **ERCOT 2023/2024/2025** — all three buildable backcast years now carry a built HSL
>   parquet"

`data/raw/ercot-hsl/` holds `ercot_2023/2024/2025_hsl_hourly.parquet` and nothing else;
`data/raw/ercot-hsl/np6/` holds `2023/ 2024/ 2025/` source archives and nothing else. The
2021 solve says so at run time:

```
[3e] Renewable curtailment — 2021: no ERCOT HSL parquet; build with
     scripts/build_ercot_hsl.py
```

The wind offer is **not** the missing piece — it is configured in every year
(`ira_ptc_wind = 26.0`, `policy/ira.py:240` `wind_mc = -config.ira_ptc_wind`). It simply
never sets the price in 2021, because nothing is ever curtailed.

---

## 4. THE PATTERN IS EXACT ACROSS ALL FIVE YEARS

Measured on the keeper `2026-09-08-ercot256-drag-layup-mask`:

| year | HSL parquet | model min | model hrs ≤ $0 | model p25 / actual p25 |
|---|---|---|---|---|
| **2021** | **NO** | **+17.57** | **0** | **3.19×** |
| **2022** | **NO** | **+9.42** | **0** | 1.37× |
| 2023 | YES | **−26.00** | 73 | 1.34× |
| 2024 | YES | **−26.00** | 104 | 1.44× |
| 2025 | YES | 0.00 | 161 | 1.27× |

**Every year with an HSL parquet forms negative prices; neither year without one does.** The
−$26.00 floor in 2023/2024 is exactly `−ira_ptc_wind`, i.e. the wind offer setting the price
in surplus hours — the mechanism 2021 cannot reach.

---

## 5. WHAT THIS DOES **NOT** ESTABLISH

- **It is necessary, not proven sufficient.** 2022 also lacks HSL yet scores 1.37× on p25,
  close to the HSL years. So the HSL gap alone does not account for 2021's *magnitude*
  (3.19×); a second factor is likely and is not identified here. One plausible contributor,
  untested: 2021 and 2022 both run the 2023 ECRS carve-out's `k_peak 33.0` offer scaling
  (CC_REGULAR peak band `151.008` against the forward config's `4.576`).
- **No solve was run.** Whether building the 2021 HSL parquet closes C3a/C3b is untested and
  cannot be tested until the data exists.
- 2021 is **validation tier**, so under rule 30(c) none of this moves ERCOT's headline —
  it stays `CALIBRATED` on the train tier either way.

---

## 6. THE FIX, AND WHY IT NEEDS THE OWNER

Build `ercot_2021_hsl_hourly.parquet` (and 2022) with the existing
`scripts/data/build_ercot_hsl.py`, from ERCOT's NP4-732-CD (wind) / NP4-737-CD (solar)
"Hourly Averaged Actual and Forecasted Values", or the by-region variants NP4-742-CD /
NP4-745-CD that 2023 used.

`data/raw/ercot-hsl/README.md` records the 2023 archives as an **owner upload** (2026-07-22),
so the source is not self-serve from this session. **The ask: drop 2021/2022 NP6 archives
into `data/raw/ercot-hsl/np6/2021/` and `…/2022/`.** The builder and the loader path already
exist and need no code change — this is intake only, zero free parameters, and it applies
identically to every year (rule 22: inputs are collected once and applied across the whole
span, never held out).

---

## 7. SIX OTHER 2021-SCOPED INPUT GAPS, FOUND IN THE SAME PASS

Reported for the record; none is quantified here and none is claimed to be the cause.

| gap | run-time message |
|---|---|
| GTC limits | `no gtc-limits clean partition for 2021 — static TTC kept` |
| West neg-day frequency | `collapse_freq 0.420 (default; measured neg-day n/a)` |
| Coal peak offer year level | `solve year 2021 is NOT in the table [2023] — static level kept` |
| Cleared-share RT basis | `year 2021 absent from the RT artifact — DAM basis retained` |
| Fast-start pool | `year 2021 absent from the pool artifact` |
| AS requirements | `no published AS Plan for this year — using the MEASURED CLEARED DAM quantity` (the log notes this **understates** the requirement and biases price and tail **low**) |

---

*Generated by [Claude Code](https://claude.ai/code)*
