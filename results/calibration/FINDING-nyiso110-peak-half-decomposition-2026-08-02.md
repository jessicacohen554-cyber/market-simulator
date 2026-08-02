# FINDING — nyiso-110: the PEAK half decomposes into MISSING EVERYDAY RESERVE-PRICE FORMATION (dollar-for-dollar, slope ≈ 1) on top of an energy side that is ALREADY OVER-PRICED at both ends — the keeper's C3a PASS is a cancellation, and every in-model route to the missing component is closed on NYISO's own measurements

**Date:** 2026-08-02 · **Scope:** NYISO, 2023–2025, the nyiso-109 named successor
(the peak half of the compressed price distribution) · **NO LP was solved, no
keeper changed, no bundle produced, no dashboard registration** (the
nyiso-93/94/95/97/99/101/105/107 disposition — rule 15 governs completed runs;
there is none). **Probe:** `scripts/probes/_nyiso110_peak_half_decomposition.py`
(committed; sidecar measurements A–D re-run in seconds with `--no-fleet`, the
stack/dormancy measurements E rebuild one fleet per year with no LP).
**Machine output:** `results/calibration/_nyiso110_peak_half_decomposition.json`.

The handoff asked (a) for a no-LP decomposition of the peak-half miss on the
keeper's own sidecars — how much is reserve/scarcity formation vs offer-surface
level vs the systemic amplitude signature — and (b) for either ONE
pre-registered lever from the §5.5 queue or a declaration that the lane is
systemic-blocked pending the owner amplitude-criterion call. The decomposition
came back sharper than the question: at NYISO the "systemic amplitude
signature" is not a residual left after reserve formation and offer level are
accounted — **it is, to first order, the missing reserve formation itself**,
and the flat-stack energy side owns only the smaller DA-basis remainder.

---

## §0 — the verdict in one table

| # | question | result | verdict |
|---|---|---|---|
| **B** | how much of the missing trough→peak swing is reserve formation? | measured spin-reserve differential (peak − trough) covers **89 / 64 / 64 %** of the missing swing on the DA basis and **131 / 97 / 107 %** on the RT basis (upper bound); hour-level passthrough slope of the peak miss on the measured spin price ≈ **1** (DA +1.15 / +1.31 / +0.75; RT censored +0.77 / +1.02 / +1.09) | **the dominant component** |
| **B2** | what does the energy side look like once the measured reserve content is stripped? | the model **over-prices BOTH ends** (RT energy basis: trough +5.7 / +3.5 / +4.2, peak +7.3 / +3.2 / +5.3) and its energy-only swing is **117 / 97 / 107 %** of the reserve-stripped actual swing (RT; DA 92 / 79 / 68 %) | **C3a passes by CANCELLATION** |
| **B3** | is the model's own reserve pricing alive? | co-opt reserve dual > 0 in **17 / 6 / 34 hours** of 8,760 (peak-window mean $0.11 / $0.06 / $0.44) vs a measured DA spin price **> $1 in 100 %** of peak-window hours (LW mean $9.72 / $8.62 / $17.46) | **dead — the NYISO face of the cross-ISO co-opt dormancy** |
| **C** | is the peak miss events or every day? | DA miss > 0 in 51 / 63 / 81 % of peak hours; $200-censoring moves the mean by ≤ $2.2; top decile carries 48–67 % of the positive mass | **broad, everyday** (with a DJF surplus beyond reserve, §3) |
| **E1** | can the model's stack even reach the actual peak price? | actual DA peak exceeds the model's most expensive available thermal offer in **{E1_SHARE} %** of peak hours; where reachable, **{E1_BAND} GW** sits priced between the model's clearing price and the actual | **{E1_VERDICT}** |
| **E2** | who is marginal at the model's peak? | `econ` **{E2_ECON} %** of the peak marginal set (the same family as the trough — nyiso-109 §8's flat-stack signature reproduced on the keeper) | **traversal, not a missing tier** |
| **E3** | is the model standing lower on its stack (volume error)? | model thermal at peak = **{E3_RATIO}** × measured (EIA-930 gas+oil, zero-dropout-screened) | **{E3_VERDICT}** |
| **E4** | is the nyiso-84 "widened spin gate" route live? | hydro alone — armed reserve-eligible on the keeper, zero opportunity cost by construction (held reserve spends no water) — covers the 655 MW NYCA spin requirement in **{E4_SHARE} %** of all hours (conservative min(headroom, ρ·P) basis: **{E4_CONS} %**) | **{E4_VERDICT}** |
| **(b)** | lever or blocked? | see §6–§7 | **{FINAL_VERDICT}** |

## §1 — A: the target statistic, restated full-year on the committed hub actual

nyiso-109's 69/49/45 % was measured on the partially-covered RTM zonal clean;
the committed `actual_lmp_hourly_NYISO.parquet` hub DA/RT covers all 8,760
hours, and the xiso-1 hour-of-day amplitude construction reproduces exactly
(hod share 0.520 / 0.509 / 0.445 vs xiso-1's 52.0 / 50.9 / 44.5 %). Windows are
nyiso-109's verbatim: trough h01–h05, peak h17–h19.

| year · basis | model swing | actual swing | share | trough err | peak err |
|---|--:|--:|--:|--:|--:|
| 2023 DA | 10.82 | 17.99 | **60.1 %** | +4.79 | −2.39 |
| 2023 RT | 10.82 | 16.20 | 66.8 % | +5.49 | +0.11 |
| 2024 DA | 11.60 | 20.18 | **57.5 %** | +2.71 | −5.88 |
| 2024 RT | 11.60 | 20.37 | 56.9 % | +3.22 | −5.55 |
| 2025 DA | 16.44 | 36.12 | **45.5 %** | +2.45 | −17.23 |
| 2025 RT | 16.44 | 38.81 | 42.3 % | +2.48 | −19.90 |

The sign-symmetric compression nyiso-109 reported, on the full-year basis: the
trough is over-priced everywhere, the peak under-priced in 2024/2025, and 2023's
peak error is ~0 — which §2 shows is itself a cancellation, not a correct peak.

## §2 — B: the reserve-formation component, measured on NYISO's own published AS prices

**Rule 25 basis.** pjm-138 measured this construction on PJM's market; nothing
transfers. The measured side here is NYISO's own posted zonal AS clearing
prices — the committed `NYISO_as_{da,rt}_<year>.csv` (OASIS damasp/rtasp
intake), `spin_10` per settlement zone mapped onto model zones by the
repo's established cascade-tier representative-zone map
(`derive_nyiso_rcpf_overlay._MODEL_ZONE_TO_NYISO_AS`), load-weighted with the
keeper's own zonal demand. `spin_10` is the top of NYISO's posted cascade — a
spin provider's price internalizes the lower products — so it is the correct
single-product opportunity-cost proxy for a reserve-capable marginal unit, and
the conservative one (the repo's 3-product "stack" convention roughly doubles
it). The model side is the keeper's own `reserve_price` sidecar column — the
co-opt family duals, folded into the energy price by construction.

**The model's reserve pricing is dead; the market's is everywhere:**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model reserve dual > 0 (hours of 8,760) | **17** | **6** | **34** |
| model dual, peak-window mean | $0.11 | $0.06 | $0.44 |
| measured DA spin, peak-window LW mean | **$9.72** | **$8.62** | **$17.46** |
| — share of peak-window hours > $1 | **100 %** | **100 %** | **100 %** |
| — $200-censored | $9.72 | $8.62 | $16.28 |
| measured DA spin, trough-window LW mean | $3.36 | $3.09 | $4.88 |
| measured RT spin, peak-window LW mean | $7.29 | $8.77 | $25.67 |
| measured DA spin, all-hours mean | $5.70 | $5.28 | $9.09 |
| measured RT spin, all-hours mean | $2.46 | $2.38 | $7.59 |

The measured content is **not** event tail: censoring at $200 moves the DA
peak-window mean by ≤ $1.2 (spin > $200 in 0.0 / 0.0 / 0.5 % of peak hours).
It is the everyday co-optimization opportunity cost the LP never forms.

**The swing arithmetic.** The reserve differential (peak-window minus
trough-window measured spin) against the missing swing (actual minus model):

| basis | | 2023 | 2024 | 2025 |
|---|---|--:|--:|--:|
| DA | reserve differential | 6.37 | 5.53 | 12.58 |
| | missing swing | 7.18 | 8.59 | 19.68 |
| | **share owned by reserve** | **88.7 %** | **64.4 %** | **63.9 %** |
| RT | reserve differential | 7.04 | 8.47 | 23.94 |
| | missing swing | 5.38 | 8.77 | 22.38 |
| | **share owned by reserve** | **130.8 %** | **96.5 %** | **107.0 %** |

**Passthrough is dollar-for-dollar.** Regressing the hourly peak-window miss on
the hourly measured spin: DA slope **+1.15 / +1.31 / +0.75**, RT $200-censored
slope **+0.77 / +1.02 / +1.09**, hour-level correlation +0.53 / +0.62 / +0.66.
A slope of ~1 is the signature of a missing *additive* component, not a
mis-scaled one; the negative DA intercepts (−8.74 / −5.41 / +3.65) are the
energy side over-pricing that §2.1 isolates.

### §2.1 — B2: the energy-basis restatement — the C3a PASS is a cancellation

Subtract the measured spin content from the actual price and the model's own
(near-zero) folded dual from its price, and compare energy-only to energy-only.
This is a **bounding** construction — the spin price passes into the LMP only
where a reserve-capable unit is marginal, so it strips *at most* the true
content — and the RT event hours over-strip (RT spin spikes co-move with RT
LMP spikes), which is why the >100 % RT cells are quoted as upper bounds and
the censored slope ≈ 1 above is the load-bearing statement.

| year | RT energy trough err | RT energy peak err | RT energy swing share | DA energy swing share |
|---|--:|--:|--:|--:|
| 2023 | **+5.74** | **+7.29** | 116.9 % | 92.1 % |
| 2024 | **+3.52** | **+3.16** | 97.0 % | 78.7 % |
| 2025 | **+4.21** | **+5.33** | 107.5 % | 68.0 % |

Read it directly: **once the measured reserve content is accounted for, the
model's energy side over-prices BOTH ends of the day by $3–7/MWh, and its
energy-only diurnal swing is ~100 % of the reserve-stripped actual swing on the
RT basis** (68–92 % on DA — the flat-stack residual survives there, §5). The
keeper's C3a PASS is therefore a cancellation: an energy side ~$3–7 too dear,
netting against ~$2.4–7.6 of reserve content it never forms. nyiso-109's §8
marginal-rung census measured the same excess from the other side — the
residual markup on the price-setting rung ($6.84 / $10.13 / $9.24).

## §3 — C: the miss is broad and everyday, with a DJF surplus beyond reserve

DA-basis peak-window miss: mean +2.39 / +5.88 / +17.23, positive in 51 / 63 /
81 % of peak hours, p50 +0.19 / +2.07 / +9.13; $200-censoring moves the mean to
+2.08 / +5.78 / +15.07. Seasonally (DA): DJF **+8.08 / +11.27 / +32.00**, JJA
+0.60 / +4.61 / +21.84, shoulder +0.49 / +3.87 / +7.66 — against measured DJF
peak-window spin of only 9.43 / 9.79 / 18.72. The winter miss **exceeds** the
winter reserve content in 2023 and 2025: a second, smaller, winter-specific
non-reserve component sits on top (the `nyiso_iroquois_winter_spread` family's
territory — see §6's queue notes; its re-arm stays blocked on its own
adjudicated joint-lever condition).

## §4 — D: the day-level view — compression is the typical day, not an average artifact

Per-calendar-day model share of the actual trough→peak swing (days with actual
swing > $1): DA median **0.577 / 0.564 / 0.459**, model below half the actual
swing on 36 / 39 / 57 % of days, inverted days ≈ 0. The compression is the
shape of the ordinary day, consistent with xiso-1's finding that no single
scarcity event drives the amplitude statistic.

## §5 — E: the stack anatomy at peak, on the keeper's own offers

{SECTION_E}

## §6 — the lever space, adjudicated route by route

{SECTION_6}

## §7 — what this does and does not license, and the owner call (surfaced, not decided)

{SECTION_7}

## §8 — governance record and DO-NOT-REDO

{SECTION_8}

## §9 — reproduction

```
PYTHONPATH=.:src python scripts/probes/_nyiso110_peak_half_decomposition.py \
    --bundle results/calibration/nyiso109_zonalanchor_B \
    --out results/calibration/_nyiso110_peak_half_decomposition.json
```

Measurements A–D read only committed artifacts and run in seconds
(`--no-fleet`). Measurement E rebuilds the keeper's fleet per year via
`replay_keeper` → `run_year(fleet_only=True)` — one reconstruction per year,
no LP, run sequentially; a fresh container needs `pip install -e .`, the
pinned wheels, and a full `scripts/regenerate_clean.py` first (the nyiso-108
environment note).
