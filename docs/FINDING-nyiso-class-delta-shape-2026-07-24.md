# FINDING — NYISO per-class model−actual delta shapes (2026-07-24)

**Instrument:** the new Charts-tab hot/cold delta heatmap + non-fossil/imports
hourly panels (`nonfossilHr`), read on keeper
`2026-07-23-nyiso-72-netrev-margin`, 2023–2025 (rule 22 in-sample window only —
NYISO's other years were neither rendered nor scored).

**No solve, no scorer change, no rubric criterion, no keeper change.** This is a
read of an instrument. Everything below is a *named hypothesis with evidence*,
not an applied fix (rules 1 / 11 / 21 / 23–25). No probe number consumed —
`nyiso-74` stays free for the next SOLVE.

> ### ⚠ CORRECTION 2026-07-25 — the nuclear row (rank 4 / §2 / action 3) is WITHDRAWN
>
> This document was written against a **defective EIA-930 nuclear benchmark**.
> NYIS `NG: NUC` coded its filing gaps as an exact `0.0`: 1,275 h of 2023,
> including one contiguous **1,179-hour Mar–Apr block** that this document's
> derate detector read as an "actual Mar 13 + 50 d refuel outage". It never
> happened. A parallel session diagnosed it the same afternoon and landed the fix
> (`_ZERO_CODED_GAP_SERIES`, commit `d13a3f2`, ~27 min before this doc was
> committed and therefore not reflected in it) — see
> `docs/FINDING-nyiso-import-hour-assignment-and-nuclear-benchmark-2026-07-24.md`
> §4, which reaches the opposite conclusion against NYISO's own hourly fuel-mix
> posting.
>
> Regenerating this instrument's payload on 2026-07-25 against the repaired
> benchmark gives, for nuclear:
>
> | year | model TWh | actual TWh (repaired) | net Δ | actual TWh (as published here) |
> |---|---|---|---|---|
> | 2023 | 27.489 | **27.457** | **+0.03** | 23.998 |
> | 2024 | 26.958 | **26.955** | **+0.00** | 25.83 |
> | 2025 | 28.381 | **28.273** | **+0.11** | 27.90 |
>
> The 3-year net over-run is **+0.14 TWh, not +5.02 TWh**. **NYISO nuclear is not
> a refuel-calendar defect and action 3 below is closed** — the outage structure
> is present in the model (§4 of the sibling finding measures 6–8 discrete MW
> levels and a 74 % minimum). The residual hourly r (0.715) is what is left after
> interpolation bridges a 1,179-hour block: it recovers the *energy* but not the
> *shape*, so the map's nuclear signature is an artifact of the repair, not a
> model error. Curating the NYISO fuel-mix posting into the clean seam would fix
> the shape; that is a data-intake task needing owner authorization.
>
> **Everything else in this document reproduces exactly** against the repaired
> benchmark and is unaffected — hydro r 0.638/0.582/0.428 (mean 0.55), imports
> 0.474/0.488/0.395 (mean 0.45), other −0.622/0.189/−0.003 (mean −0.15), oil
> 0.073/−0.012/0.084 (mean 0.05), and the solar flat-block defect of §3. The
> ranked actions of §7 stand with nuclear struck. The canary that caught this is
> `tests/test_nonfossil_hourly.py::test_known_nyiso_signatures`, whose pins were
> repaired in the same commit as this correction.

Dashboard: `docs/codebase-site/backcast-runs.html#iso=NYISO&run=2026-07-23-nyiso-72-netrev-margin`
→ **Charts** tab → CLASS selector → *Non-fossil & imports (EIA-930)*.

---

## 1. What the maps show

Δ = model − actual, MW, per hour. Signature classified by a variance
decomposition of the Δ field (share of Δ variance carried by the hour-of-day
mean profile vs the day-of-year mean profile vs the monthly mean), so the
labels below are measured, not eyeballed.

| rank | class | Σ\|Δ\| 3 yr (TWh) | net 3 yr (TWh) | r (mean) | Δ variance: h-o-d / d-o-y / monthly | signature | implicates | cat |
|---|---|---|---|---|---|---|---|---|
| 1 | **hydro** | **25.97** | −0.43 | 0.55 | 9 % / 50 % / **0.7 %** | **bang-bang day blocks** (not seasonal) | no hourly modulation band / energy budget on conventional hydro | **(b)** |
| 2 | **imports** | **21.53** | +1.19 | 0.45 | **12 %** / 36 % / 0.0 % | **stable diurnal dipole** (over overnight, under at evening peak) | import ladder has no time-of-day schedule or evening ramp | **(b)** |
| 3 | other (biomass+geo) | 7.74 | −2.66 | **−0.15** | 5 % / 87 % / 39 % | seasonal blocks, **anti-correlated** | must-run block vs a seasonally-dispatched real fleet | (b) |
| 4 | ~~nuclear~~ **WITHDRAWN** | ~~7.46~~ | ~~+5.02~~ → **+0.14** | ~~0.61~~ → 0.70 | ~~0.4 % / 95 % / 36 %~~ | ~~multi-week vertical blocks~~ — a **zero-coded benchmark filing gap** | **nothing — the benchmark was wrong** (see the correction above) | — |
| 5 | oil | 4.16 | −0.98 | 0.05 | 0.1 % / 95 % / 19 % | event blocks, uncorrelated | oil peakers dispatch on the wrong days | (b) |
| 6 | solar | — | — | — | — | **no hourly actual; model is a FLAT block** | flat fallback CF (see §3) | **(c)+(a)** |
| 7 | wind | 0.06 | −0.00 | **1.000** | — | **none — pinned** | nothing (see §6) | — |

Category: **(a)** fixable model input · **(b)** missing structural mechanism ·
**(c)** data-intake blocker.

The C1 annual-volume gate passes on most of these. The error is **shape**, and
until this session nothing on the dashboard could display it.

---

## 2. Rank 4 — nuclear: ~~the refuel outages are in the wrong place~~ **WITHDRAWN 2026-07-25**

> **This entire section is withdrawn.** Its "actual" column is a zero-coded
> EIA-930 filing gap, not an outage — see the correction box at the top. The
> 2023 "actual Mar 13 + 50 d" window does not exist in the repaired benchmark
> (which shows exactly one sustained derate that year, Sep 02 + 6 d — the row
> below that *was* real), and 2025's "model NONE" was never an error: the
> repaired 2025 net Δ is +0.11 TWh. The section is kept unedited below as the
> record of what the instrument showed on the defective input.


The clearest single result, and it confirms the predicted signature exactly:
h-o-d share **0.4 %** (no diurnal structure at all), d-o-y share **95 %**
(multi-week blocks). Sustained derate windows, ≥5 days below 80 % of that
series' own p95 daily output:

| year | actual | model |
|---|---|---|
| 2023 | **Mar 13 + 50 d**, Sep 02 + 6 d | Apr 01 + 30 d |
| 2024 | Mar 04 + 24 d, Sep 04 + 15 d, Sep 23 + 6 d, Sep 30 + 17 d | Mar 01 + 31 d, Sep 01 + 30 d |
| 2025 | Mar 19 + 14 d | **NONE** |

Capacity is right — model p95 daily 3,326 MW vs actual 3,321 / 3,339 / 3,384 MW.
So this is **not** a fleet or derate-level problem; it is the outage *calendar*.
2023's outage starts 19 days late and is 20 days short (the solid orange
Mar–Apr block on the map), and **2025 models no refuel outage at all** — which
is the whole of that year's +0.43 TWh over-run and most of the +5.02 TWh 3-year
nuclear over-run.

Mechanism: NYISO nuclear is outside CAMPD (CEMS meters combustion units), so the
outage overlay that supplies fossil availability has nothing to say about
Ginna / Nine Mile / FitzPatrick. **Category (a)** — a per-unit nuclear refuel
schedule is a reproducible physical availability input in exactly the rule-13
sense (it regenerates forward from published refuelling cycles and responds to
changed conditions), so it is admissible in both modes. Worth confirming whether
the model's Mar/Sep blocks are a hard-coded generic assumption; if so, replacing
them with the measured per-unit windows is the fix.

## 3. Rank 6 — solar: the model's NYISO solar is a flat block (a definite defect)

Found only because the panel exists. NYISO model solar dispatch, 2023:

```
hour-of-day mean (MW):  222 222 222 222 222 ... 222 222 222   ← every hour, incl. 03:00
distinct values in 8760 hours: 12          midday/night ratio: 1.00
```

Twelve distinct values = twelve monthly levels. **The model's NYISO solar
generates the same power at 3 a.m. as at noon.** 2024 and 2025 are the same
(303 MW flat, 406 MW flat).

Root cause chain, traced and confirmed:

1. EIA-930 NYIS reports **no solar at all** — `NG: SUN` sums to 0.0 TWh, and
   `data/raw/NYIS_fueltype.parquet` `SUN` is all zeros (1 distinct value across
   19,685 rows). The gap is total, at every granularity.
2. `renewables._eia_hourly_cf_profile` therefore returns `None` — its own
   docstring names this case ("*e.g. EIA-930 NYIS does not separately report
   solar*") and falls back to the distribution-based profile.
3. The fallback `_eia930_cf("solar")` reads
   `data/raw/eia-930/eia_generation_profiles.parquet`, whose NYISO 2023 solar
   series is **also flat — 1 distinct value across 8760 hours**. Wind on the
   same path has 428 distinct values and a real diurnal ratio (0.90), so the
   loader is fine; the *solar row* is degenerate.
4. Flat CF × the 12-step EIA-860 monthly capacity ramp = the 12-value block.

Invisible to every existing gate: C1 can't score a class whose 930 actual is
absent, and 1.9–3.6 TWh/yr looks plausible annually.

**Category (c) at root** (no NYISO hourly solar meter exists in the intaken
930) **but with an (a) fix that needs no new intake**: shape the fallback
physically — solar geometry / clear-sky, or a neighbouring BA's normalized
diurnal solar shape — preserving the monthly energy. A flat 24-hour solar CF is
physically impossible, so *any* shaped fallback is strictly more faithful
(rule 1). Note this is a **fallback-path** defect: it will affect any ISO-fuel
whose 930 series is missing, not just NYISO solar. Worth an all-ISO sweep.

## 4. Rank 1 — hydro: bang-bang dispatch, and it is NOT a seasonal-shape problem

The predicted signature was a *seasonal band* (freshet/reservoir). **The data
says otherwise** — the monthly share of Δ variance is **0.7 %**. The seasonal
*level* is essentially right; the *hourly modulation* is missing:

| year | series | max MW | hours > 95 % of max | hours < 5 % | IQR/median |
|---|---|---|---|---|---|
| 2023 | model | 4,593 | **29.6 %** | 4.7 % | 0.57 |
| 2023 | actual | 5,231 | 0.1 % | 0.0 % | 0.27 |
| 2024 | model | 4,579 | **25.5 %** | 5.7 % | 0.59 |
| 2024 | actual | 5,141 | 0.1 % | 0.0 % | 0.32 |
| 2025 | model | 3,343 | **58.2 %** | 12.6 % | 0.70 |
| 2025 | actual | 4,957 | 0.2 % | 0.0 % | 0.39 |

The real NYISO hydro fleet is essentially *never* at its rail (0.1 % of hours)
and never off; the model sits pinned at max a quarter to over half the year and
hard-off ~5–13 %. It is being dispatched as a price-taking on/off resource. 2025
is the worst case and also where the model's hydro max collapses to 3,343 MW
against a 4,957 MW actual — the −3.06 TWh 2025 hydro under-run.

**Category (b)** — a missing structural mechanism: conventional hydro needs an
hourly modulation band (an energy budget over a day/week with min/max release
bounds), not a flat 0–max dispatchable bound. This is the biggest single error
source on the ISO by Σ|Δ| (25.97 TWh over three years) and should be worked
first. Note `nyiso69_hydro_reserve` / `nyiso70` already touched hydro *reserve
eligibility* — a different lever; the modulation band is untouched.

## 5. Rank 2 — imports: a stable diurnal dipole (right on volume, wrong every hour)

Annual volume lands within ~2 % every year (the C1-passing case the prompt
flagged) while r is 0.40–0.49. The hour-of-day Δ profile is the same shape in
all three years:

```
hour:        0    1    2    3    4  ...   15   16   17   18   19  ...  22   23
2023 Δ MW: +435 +672 +751 +675 +421     -296 -500 -641 -547 -397     +289 +422
2024 Δ MW: +240 +491 +637 +540 +193     -405 -611 -624 -525 -310     +395 +289
2025 Δ MW: +113 +226 +190  +10 -343     -197 -436 -412 -357 -201     +604 +168
```

The model **over-imports overnight** (+200…+750 MW, hours 0–4) and
**under-imports through the evening peak** (−200…−640 MW, hours 15–19). Repeating
across three independent years makes this structural, not noise. Monthly share
of Δ variance ≈ 0.0 %: it is purely a time-of-day error.

**Category (b)** — the priced import node's tranche ladder carries no
time-of-day schedule, so it fills the cheapest (overnight) hours to its cap and
has no headroom or ramp left for the evening peak the real seams deliver. If
NYISO/neighbour published hourly transfer schedules or hourly TTC exist, part of
this is **(a)** instead — worth checking before designing a mechanism (rule 12:
prefer the measured input).

## 6. wind: r = 1.000 is not skill — it is a pinned profile

Model wind = 4.601 / 6.010 / 7.047 TWh against actual 4.601 / 6.012 / 7.049 TWh,
Σ|Δ| = 0.06 TWh over three years, r = 1.000. The model's wind bound *is* the
EIA-930 delivered series, so the panel is comparing the input to itself. **This
row carries no validation information and must never be quoted as fit** — its
value is precisely that the map makes the tautology visible (a flat white delta
map with a ±4 MW cap). Contrast ERCOT, where wind r = 0.992 with real structure.

## 7. Ranked next actions (biggest first)

*(Renumbered 2026-07-25: nuclear struck, see the correction box.)*

1. **Hydro modulation band** — 25.97 TWh Σ|Δ|. Design an hourly energy-budget /
   release-bound mechanism for conventional hydro. Structural (b); own charter.
   Corroborated independently against NYISO's own fuel-mix posting (+1.20 / +0.96
   / **−3.20** TWh, r 0.62 / 0.58 / 0.41) — both benchmarks agree it is real.
2. **Import hour assignment** — 21.53 TWh. **Now specified**: the sibling
   finding's §3 traces it to `derive_nyiso_import_tranches.py`'s Q-Q construction
   `pi_k = Quantile_DA(1 − P[net_import > L_k])`, which imposes rank-1 coupling
   between import depth and internal price where the measured joint correlation
   is only +0.16 / +0.38 / +0.43, and which carries **no hour assignment at all**.
   Measured hourly seam schedules DO exist in-repo
   (`data/raw/NYISO/interface-flows/`, four "SCH -" external seams). Note the
   sign: the model imports MORE overnight than the real system, so adding cheap
   overnight depth moves the wrong way (that sub-lane is refuted). Rule 21: the
   re-derivation commit cites method incorrectness, never the residual. Rule 1
   warning: correcting it will make C3a 2023 *worse* and must not be reverted for
   that. Also read that finding's §1 first — `interchange_shaping` is adjudicated
   **rule-13 FORBIDDEN** as a keeper mechanism, so it is not the shortcut here.
3. ~~**Nuclear refuel calendar**~~ — **CLOSED, not a defect.** The apparent
   +5.02 TWh was a zero-coded benchmark filing gap, fixed in `d13a3f2`; the
   repaired 3-year net Δ is +0.14 TWh.
4. **Solar flat-CF fallback** — small TWh, but a *definite physical impossibility*
   and cheap to fix; likely affects other ISO-fuels with absent 930 series.
5. **`other` anti-correlation (r = −0.15)** — 7.74 TWh; biomass/geothermal
   modelled as a flat must-run against a seasonally-dispatched real fleet.
6. **Oil day-placement** — 4.16 TWh, r ≈ 0.05; lowest priority of the six.

**Owed, unrelated to the ranking:** the keeper's committed `metrics.json`
predates `d13a3f2`, so its NYISO C1/C4 nuclear numbers are scored against the
defective benchmark. A **re-score from the existing bundle** (no re-solve) is
owed — flagged in the sibling finding's §6 and still not done.

## 8. Cross-ISO note (not NYISO)

ERCOT's `_eia930_frame` dedicated loader path emits no `hydro` or `oil` series
(the generic per-BA loader would supply both from `NG: WAT` / `NG: OIL`), so
those two ERCOT panels show "no hourly actual" even though the underlying 930
data exists. That is a renderer-input gap, not a model error, and fixing it
changes an ERCOT bundle extract — deliberately **not** touched here.

---

*Evidence is reproducible from committed artifacts only: the keeper's
`hourly/class_hourly_<year>.parquet` + `hourly/system_<year>.parquet` sidecars
and `data/raw/eia-930-hourly/NYIS hourly.parquet`, via
`scripts/backfill_nonfossil_hourly.py --run 2026-07-23-nyiso-72-netrev-margin
--dry-run`. Clock alignment verified before any panel was emitted: model-vs-930
demand cross-correlation peaks at lag 0 with r = 1.0000 in all three years
(±1 h: 0.971–0.978), so no DST re-pairing is involved — cf.
`docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md`.*
