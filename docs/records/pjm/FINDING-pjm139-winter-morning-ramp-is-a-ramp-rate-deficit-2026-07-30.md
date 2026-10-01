# FINDING — pjm-139: **the chartered lever was already armed, and the winter morning ramp is a RAMP-RATE deficit, not a fuel-price one.** `gas_daily_shape` is `K` on PJM, not `U`: it has been in the keeper since **pjm-107** (2026-07-14), and `pjm137_ctheatrate_B` carries `scenario_config.gas_daily_shape = True`. It also could not have reached this defect even if it were off — its factors are one per CALENDAR DAY, repeated across 24 hours, so their within-day σ is **≤ 4.4e-16** and their hour-of-day profile is **flat to 0.000**, while the defect is an intra-day differential swinging **$10–25/MWh across hours of the same winter days**. What the model actually misses is the ramp itself: PJM's own winter system energy price rises **+$15.28 / +$21.63 / +$35.45** from h04 to h07 and the model's rises **+$3.93 / +$4.55 / +$6.51** — **26 / 21 / 18 %** of it. The keeper runs `ramp_limits = False`, so it meets the winter morning ramp by sliding cheap STEAM up the merit order at **1.8× / 2.4× / 2.6×** the rate the real fleet demonstrably achieves instead of starting the CTs the real fleet starts.

**No LP was solved.** Every measurement runs on the committed keeper
`pjm137_ctheatrate_B` (`hourly/` sidecars, `run_config.json`), PJM's committed
`PJM-AS` day-ahead reserve results, the committed benchmark payload
`frontend/data/backcast/bench/PJM/<year>.json.gz`,
`data/raw/gas-prices/henry_hub_daily.csv`, and the `data/raw/pjm-zonal-lmp/` DA
component intake. Probe: `scripts/probes/_pjm139_winter_ramp.py`. Machine output:
`results/probes/pjm139_winter_ramp.json`.

**No delta is chartered here and nothing is registered on the dashboard** (no run
was solved — same disposition as pjm-138). One successor lever is **named,
measured and pre-checked**, and its pre-registration is committed alongside this
document so a successor can solve it without re-deriving the case:
`PREREG-pjm140-ramp-envelopes-2026-07-30.md`.

---

## §0 — the verdict in one table

| test | question | result | verdict |
|---|---|---|---|
| **W0** is the chartered lever available? | the handoff and matrix §5.3 item 9 both say `gas_daily_shape` is matrix `U`, never probed on PJM, keeper `False` | **NO. All three are false.** `pjm137_ctheatrate_B/run_config.json::scenario_config.gas_daily_shape = True`, carried on the `prb_overrides` channel (`calibration_flags.coal_prb_sigmoid_overrides.gas_daily_shape = True`). The matrix cell string is `"UKKKKK"` over `isos: ["ERCOT","CAISO","PJM","MISO","NYISO","NEISO"]` — **PJM = `K`**. It was probed at **pjm-107** (2026-07-14, leg A), passed every gate and became the `2026-07-14-pjm-107-gas-daily` keeper | **charter VOID — rule 28 forbids re-testing a `K` cell as if it were `U`** |
| **W1** could it have reached the defect anyway? | resolution check on the mechanism itself | **NO, on grounds independent of W0.** `gas_daily_shape_factors` builds one factor per calendar day and repeats it 24× (`hubs.py`, `np.repeat(day_factor, 24)`): max within-day σ **1.1e-16 / 4.4e-16 / 2.2e-16**, hour-of-day mean profile range **0.000000**, corr with hour-of-day **~1e-18**. It is not inert — it carries a real cold-snap swing (January peak day factor **1.151 / 3.287 / 2.143**, 0 / 4 / 4 DJF days above 2×) — it simply has **zero intra-day resolution** | **a DAY-scale lever cannot move an INTRA-DAY differential** |
| **W2** the handoff's own M1, run as asked | is the gap concentrated on high-gas days? | **NO — and in 2024 it is inverted.** corr(day gas factor, system-energy gap) = **−0.039 / −0.249 / +0.050** all hours, **−0.030 / −0.359 / +0.078** in DJF. The mean gas factor is **1.000 in every DJF hour-of-day window** (overnight, ramp, midday, evening peak) to three decimals — a direct numeric statement that the mechanism carries no information the defect varies on | the commodity-swing story is dead on its own test |
| **W3** how big is the winter cell, and how much is reachable? | pjm-138's identity + reserve credit, re-pointed at DJF × hour-of-day | **DJF h06–h07 CT-weighted the deficit is $23.99 / $85.33 / $114.43**, splitting into basis **$13.86 / $37.55 / $43.84** (the pjm-137-closed intra-zonal lane), reserve **$6.19 / $17.30 / $30.48** (the pjm-138-closed lane) and a **reachable residual of $3.93 / $30.48 / $40.11**. Load-weighted the DJF ramp residual after full reserve credit is **−$0.37 / +$5.55 / +$13.44** | the cell is real, and 2024–25 leave real headroom |
| **W4** what sets the model's overnight price? | `FINDING-pjm138` §7 lead 2, never measured | **a bottom-of-distribution level miss, NOT a floor-pinning artifact.** The model prints **872 / 825 / 951** distinct overnight price levels at a **0.7–0.9 %** modal share — fully dispersed. But its **p05 is $21.22 / $20.15 / $26.35 against PJM's $13.32 / $11.44 / $17.02**, and PJM's MEC is below the model's in **97.6 / 93.9 / 84.3 %** of overnight hours. The overnight stack is `CC_REGULAR` **68.9 / — / 65.7 %** and `COAL_BIT` **22.5 / — / 25.6 %** | the model has no offer cheap enough to reach PJM's overnight floor |
| **W4b** is queue item 8 the owner? | `st_gas_mustrun_p25_level`, promoted by pjm-138 on the overnight gap | **NO — wrong size and wrong mechanism.** `ST_GAS` carries **0.9 / — / 1.9 %** of overnight thermal energy (0.44 / 1.04 GW) at a night/peak ratio of **0.22 / 0.35** and cv **1.18 / 1.00** — a small peak-following class, not an overnight-floored one. Its actual keeper forcing mechanism is **`st_netload_drag`** (D-2: 54.7 / 51.3 / 42.5 % of class), not the "six overnight floor limbs" the item describes (that is the MISO form) | **the overnight motivation is WITHDRAWN** |
| **W5** what IS the defect, stated as one number? | the ramp rate each side produces | **the model's winter price profile is TOO FLAT.** DJF h04 → h07 the measured MEC rises **+$15.28 / +$21.63 / +$35.45**; the model rises **+$3.93 / +$4.55 / +$6.51** — **26 / 21 / 18 %**. Whole-day trough-to-peak: measured **$16.56 / $23.24 / $40.33**, model **$5.23 / $6.22 / $8.34** — **32 / 27 / 21 %** | a SHAPE deficit, sized without reference to any level |
| **W7** the no-LP pre-check for the successor lever | does the model out-ramp the real fleet? | **YES, in every family and every year.** At the p99 1-h up-move as a fraction of each side's own fleet peak, model ÷ actual = **CC 1.42 / 1.72 / 1.53**, **CT 1.38 / 1.70 / 1.52**, **ST 1.61 / 1.62 / 1.50**. Because the aggregate is the sum of the parts, aggregate excess **proves** per-plant envelope rows would bind | **`ramp_envelopes` (PJM `U`) FIRES the pre-check** |

---

## §1 — W0: the charter was void before it was written, and the record says so three ways

The session prompt, `DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3/§B.4 and
`docs/mechanism-testing-matrix.md` §5.3 item 9 all describe `gas_daily_shape` as
an untested PJM lever running `False` in the keeper. The committed record
contradicts each of them:

| claim | committed evidence | verdict |
|---|---|---|
| "the keeper runs … `gas_daily_shape=False`" | `results/calibration/pjm137_ctheatrate_B/run_config.json` → `scenario_config.gas_daily_shape = True`, and `calibration_flags.coal_prb_sigmoid_overrides.gas_daily_shape = True` (the `prb_overrides` channel `_pjm107_gas_daily_probe.py` itself used) | **false** |
| "matrix `U`" | `docs/codebase-site/data/mechanism-matrix.js`: `cells: "UKKKKK"` against `isos: ["ERCOT","CAISO","PJM","MISO","NYISO","NEISO"]` → position 3 = PJM = **`K`**. Only ERCOT is `U` | **false** |
| "never probed on PJM" | `scripts/probes/_pjm107_gas_daily_probe.py` exists and is the driver; `docs/calibration-log.md` (2026-07-14) records leg A at 16/16 C1 PASS, all gates PASS, registered as `2026-07-14-pjm-107-gas-daily` and adopted as the keeper | **false** |

**And pjm-107 had already inverted the hypothesis that motivates the charter.**
`DIAGNOSIS` §B.4 predicted that arming the mechanism would ADD the January
cold-snap tail. On the mean-preserving builder it did the opposite — the 2025
model tail went **17 h → 6 h** — because the flat-monthly baseline had been
over-pricing *every* January day at the elevated monthly mean. The
calibration-log entry states this in terms: *"The fix INVERTED the diagnosis's
central winter hypothesis."* The `DIAGNOSIS` text was never updated, and that
stale text is what the handoff read.

Under rule 28 `[R-MECH-MATRIX]` a `K` cell is not re-tested as though it were
untested, and there is no A/B to run: arm B would be the keeper. **The chartered
delta does not exist.** The stale sources are corrected in place by this session
(§7).

## §2 — W1: the mechanism has the wrong resolution for this defect, armed or not

This is the part that would hold even if W0 had gone the other way, and it is
worth stating precisely because it generalises beyond PJM.

`gas_daily_shape_factors` (`data/fuel/hubs.py`) builds a true-trade-date
staircase, divides each month by its own calendar-day mean, and then:

```python
day_factor = seg / mean            # one value per CALENDAR DAY
shaped = np.repeat(day_factor, 24) # ... repeated across that day's 24 hours
```

Measured on the committed `henry_hub_daily.csv`, all three years:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| max within-day standard deviation | **1.11e-16** | **4.44e-16** | **2.22e-16** |
| hour-of-day mean profile, range over 24 h | **0.000000** | **0.000000** | **0.000000** |
| corr(factor, hour-of-day) | −2.4e-18 | −1.0e-18 | +1.8e-19 |
| factor range | [0.735, 1.276] | **[0.535, 3.287]** | **[0.637, 2.143]** |
| January peak calendar-day factor | 1.151 | **3.287** | **2.143** |
| DJF days above 2× | 0 | 4 | 4 |

The mechanism is **not inert** — the bottom two rows show it carrying a genuine
2.1–3.3× cold-snap commodity spike, which is exactly why it is a keeper. It is
simply **constant within each day to machine precision**, so it moves all 24
hours of a winter day by the same multiple.

The defect it was chartered against is the opposite kind of object. DJF
load-weighted, the system-energy gap by hour-of-day window:

| DJF window | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight h01–h04 | **−7.71** | **−2.63** | +3.18 |
| **morning ramp h06–h07** | **+2.25** | **+11.96** | **+26.94** |
| midday h11–h14 | −5.55 | −2.66 | +1.69 |
| evening peak h16–h18 | −0.83 | +4.38 | +15.21 |
| **intra-day swing** | **$9.96** | **$14.62** | **$25.25** |

A mechanism with 0.000 intra-day variation cannot move a $10–25/MWh intra-day
swing. And its **sign is wrong on half the cell**: lifting cold-snap days
uniformly would raise the overnight hours the model is *already too dear in* by
the same multiple as the ramp hours it is too cheap in. That is the
"monthly-average argument about a daily mechanism" error class the handoff
warned about, in its intra-day form.

**This is an all-ISO scope bound, not a PJM one**, and it is recorded on the
matrix row as such: `gas_daily_shape` — and any daily citygate series, including
the still-`U` PJM `winter_citygate_daily` (TETCO M3) — is a **day-scale** lever
and may never be chartered against a diurnal defect in any ISO.

## §3 — W2: the handoff's own M1, and it refutes the charter on its own terms

M1 as specified: join the measured daily HH deviation to the system-energy gap
and report the gap conditional on the day's gas deviation. Diffuse ⇒ inert;
concentrated on high-gas days ⇒ it fires.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| corr(day gas factor, system-energy gap), all hours | −0.039 | **−0.249** | +0.050 |
| same, DJF only | −0.030 | **−0.359** | +0.078 |

Not merely diffuse — in 2024 **materially negative**: the gap is *smaller* on
high-gas days, the opposite of the charter's prediction. (Mechanically this is
the pjm-107 inversion again: on a high-factor day the model's whole stack is
already repriced upward, so it is *less* short of PJM's price, not more.)

The cleanest single line is the window table. The mean gas factor in each DJF
hour-of-day window:

| | overnight h01–04 | ramp h06–07 | ramp h05–09 | midday h11–14 | evening h16–18 |
|---|---|---|---|---|---|
| 2023 / 2024 / 2025 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

Identical to three decimals in every window, in every year — because it must be.

## §4 — W3/W5: what the winter cell actually is

### §4.1 — the decomposition, on pjm-138's identity

CT-energy-weighted, `$`/MWh, using `FINDING-pjm138` §1's exact identity
(`total = system-energy + basis`) and §3's reserve credit:

| DJF cell | | total gap | system energy | basis (closed, pjm-137) | measured Sync MCP (closed, pjm-138) | **reachable residual** |
|---|---|---|---|---|---|---|
| all DJF hours | 2023 / 24 / 25 | 5.97 / 30.21 / 71.51 | −0.19 / 14.94 / 46.10 | 6.16 / 15.26 / 25.41 | 1.99 / 4.90 / 13.61 | −2.18 / 10.04 / 32.49 |
| overnight h01–h04 | | 0.08 / 21.38 / 83.13 | −5.90 / 4.25 / 45.59 | 5.98 / 17.13 / 37.55 | 0.04 / 0.05 / 6.05 | −5.94 / 4.20 / 39.54 |
| **morning ramp h06–h07** | | **23.99 / 85.33 / 114.43** | **10.12 / 47.79 / 70.59** | 13.86 / 37.55 / 43.84 | 6.19 / 17.30 / 30.48 | **3.93 / 30.48 / 40.11** |
| midday h11–h14 | | −4.09 / 1.78 / 33.06 | −6.11 / −0.12 / 21.99 | 2.02 / 1.90 / 11.07 | 0.23 / 0.32 / 2.93 | −6.34 / −0.44 / 19.06 |
| evening peak h16–h18 | | 3.22 / 18.03 / 64.15 | −0.60 / 9.32 / 45.68 | 3.82 / 8.71 / 18.47 | 1.84 / 4.55 / 13.71 | −2.44 / 4.77 / 31.97 |
| JJA all hours | | 18.85 / 30.50 / 59.08 | 11.52 / 16.64 / 26.10 | 7.33 / 13.87 / 32.98 | 7.06 / 6.04 / 18.56 | 4.45 / 10.66 / 11.19 |

Load-weighted, the DJF morning-ramp residual after the full reserve credit is
**−$0.37 / +$5.55 / +$13.44** — 2023 is fully explained by the two closed lanes;
2024 and 2025 are not.

### §4.2 — and stated as a ramp rate, which needs no level at all

PJM's own DJF system energy price against the model's, hour by hour (2025):

| h | 02 | 04 | 05 | **06** | **07** | 08 | 09 | 12 | 17 | 18 |
|---|---|---|---|---|---|---|---|---|---|---|
| measured MEC | 46.73 | 48.87 | 53.52 | **69.09** | **84.32** | 64.15 | 54.12 | 47.14 | 70.18 | 69.70 |
| model system price | 45.58 | 46.68 | 50.68 | **53.92** | **53.19** | 51.18 | 49.44 | 45.91 | 51.98 | 52.06 |
| measured Sync MCP | 1.10 | 1.18 | 1.84 | 7.07 | **16.93** | 5.21 | 2.46 | 0.98 | 5.50 | 8.26 |

PJM's price climbs $35 in three hours and gives it back in two. The model climbs
$6.51 and does not even peak at h07 — its DJF maximum is h06. The summary
statistics:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **DJF h04 → h07 rise, measured MEC** | **+15.28** | **+21.63** | **+35.45** |
| DJF h04 → h07 rise, model | +3.93 | +4.55 | +6.51 |
| **model as % of measured** | **26 %** | **21 %** | **18 %** |
| DJF whole-day trough-to-peak, measured | 16.56 | 23.24 | 40.33 |
| DJF whole-day trough-to-peak, model | 5.23 | 6.22 | 8.34 |
| **model as % of measured** | **32 %** | **27 %** | **21 %** |

In 2023 the model is too *dear* in every DJF hour except h07, h17 and h18. That
is the signature exactly: **the winter price profile is too flat — trough too
dear, peak too cheap** — which is why the annual load-weighted level looks right
(`FINDING-pjm138` §1: +$0.47 / +$2.62 / +$8.48) while the intra-day shape does
not.

## §5 — W7: the successor lever, named and pre-checked without a solve

`pjm137_ctheatrate_B` runs **`ramp_limits = False`**. The LP therefore carries
**no intertemporal coupling on the thermal fleet at all**: every hour is an
independent economic dispatch and the morning ramp is a free slide up the merit
order. There is no ramp scarcity to price, so the marginal unit at h07 is
whatever is next-cheapest — not whatever can physically get there.

### §5.1 — the pre-check fires

Aggregate 1-h up-move as a fraction of each side's own fleet peak (model class
hourlies against the committed bench per-plant CAMPD record, same CC/CT/ST
families the envelope derive keys on):

| family | statistic | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **CC** | p99 1-h up, model ÷ actual | **1.42** | **1.72** | **1.53** |
| **CT** | p99 1-h up, model ÷ actual | **1.38** | **1.70** | **1.52** |
| **ST** | p99 1-h up, model ÷ actual | **1.61** | **1.62** | **1.50** |

The model moves its thermal fleet **~1.4–1.7× harder per hour** than the real
PJM fleet ever demonstrably did. **The test is one-sided and is reported as
such**: because the aggregate is the sum of the parts, aggregate excess *proves*
that per-plant envelope rows would bind; the converse does not hold, so this
measurement can establish that the mechanism FIRES but could never establish
that it is inert.

### §5.2 — and the mechanism of the flat price is visible in the composition

DJF h01–h04 → h06–h07 mean rise, GW, model against the benchmark's own measured
per-plant record:

| family | 2023 model / actual | 2024 model / actual | 2025 model / actual |
|---|---|---|---|
| **ST** (coal + gas steam) | **+2.42 / +1.33** | **+2.73 / +1.13** | **+2.57 / +0.97** |
| **CT** (peakers) | **+0.66 / +1.14** | **+1.36 / +1.79** | **+2.08 / +2.50** |
| CC | +5.48 / +4.15 | +5.27 / +3.70 | +4.73 / +3.32 |

The model ramps **steam 1.8× / 2.4× / 2.6× harder** than the real fleet and
**CTs only 58 % / 76 % / 83 %** as hard. Per family the DJF h04→h07 rise ratio is
**ST 1.29 / 1.49 / 1.63** against **CT 0.44 / 0.52 / 0.72**.

That is the whole story in one line: **on winter mornings the model meets the
ramp with the cheapest thing on the stack — coal and steam it cannot physically
move that fast — instead of the dearest thing the real fleet actually starts.**
A cheap marginal unit prints a flat price. It also predicts the keeper's own
standing C1 note, where ISO-wide `CT_PEAKER` runs **2.11 / 3.57 / 3.32 TWh**
short while `COAL_BIT` and `CC_REGULAR` improve.

`ramp_envelopes` (`ScenarioConfig.ramp_limits` + `data.fleet.build_ramp_groups`
+ the frozen `derive_campd_ramp_envelopes.py`) is the CAMPD-measured,
**zero-fitted-DOF** mechanism for precisely this, its PJM matrix cell is **`U`**,
and it is armed in no keeper in any ISO. Its charter, expected direction,
no-feedback ceiling, pre-registered kills and the two known risks (the ERCOT
"envelopes are loose" precedent; the LP memory cost of the extra rows on a
15 GB box) are written up in
`results/calibration/PREREG-pjm140-ramp-envelopes-2026-07-30.md`, committed
before any arm solves. **It is not armed here and no arm was solved.**

## §6 — DO-NOT-REDO (binding on successors)

- **Do not charter `gas_daily_shape` on PJM.** It is `K`, armed since pjm-107,
  live in `pjm137_ctheatrate_B` (`run_config.json`). There is no A/B: arm B is
  the keeper.
- **Do not charter `gas_daily_shape`, `winter_citygate_daily`, or any daily gas
  series against a DIURNAL defect in ANY ISO.** §2: the factors are constant
  within a calendar day to ≤ 4.4e-16, so the hour-of-day profile is flat to
  0.000. This is a property of the construction, not of PJM. A daily series is
  chartered against a winter **level** or a **day**-scale tail, or not at all.
- **Do not quote `DIAGNOSIS-pjm-dof-scarcity-tail` §B.3/§B.4 on `gas_daily_shape`
  or on the `CC_LIKE` leg B without reading their correction stamps.** Both rows
  described mechanisms as "proposed" that are live in the keeper
  (`gas_daily_shape=True`; `pjm_offer_midcurve_segments = ["LONG_RUN","CC_LIKE"]`).
  The stale text is what produced this session's void charter; it is corrected in
  place, and the amendment is the record.
- **Do not read the overnight over-pricing as a floor-pinning artifact, and do
  not route it to `st_gas_mustrun_p25_level`.** §W4: the model prints 825–951
  distinct overnight price levels at a 0.7–0.9 % modal share; the miss is at the
  bottom of the distribution (p05 $21.22/$20.15/$26.35 against PJM's
  $13.32/$11.44/$17.02). `ST_GAS` is **0.9–1.9 %** of overnight thermal energy
  against `CC_REGULAR`'s 66–69 %, and its keeper forcing mechanism is
  `st_netload_drag`, not an overnight floor. The lever may still be defensible as
  a rule-23 re-derivation on its own source data; it is **not** an
  overnight-price lever, and pjm-138's promotion of it on that basis is withdrawn.
- **Do not size the winter cell from `FINDING-pjm138`'s all-hours residual.** The
  reachable residual is *concentrated*: $1.46 / $6.12 / $11.97 all-CT-hours
  becomes **$3.93 / $30.48 / $40.11** in DJF h06–h07 CT-weighted, and
  −$0.37 / +$5.55 / +$13.44 load-weighted after the reserve credit. 2023 is
  fully explained by the two closed lanes; 2024–25 are not.
- **Do not treat W7's aggregate pre-check as a two-sided test.** Aggregate excess
  proves per-plant binding; aggregate slack would prove nothing.
- Carried forward unchanged and still binding **in full**: `FINDING-pjm138` §6
  (the reserve/scarcity closure, the pjm-122 ownership closure, the G-20b
  sizing caveat, the EPT/EST hour-key rule, the measured-offer-surface `R`),
  `FINDING-pjm137` §5 (the zonal-congestion closure, the
  `3.066 / 4.048 / 5.218 TWh` benchmark actual, the frozen CT heat-rate
  artifact), `FINDING-pjm136` §5, `FINDING-pjm135` §7, `FINDING-pjm134` §5/§8.

## §7 — the record corrections this session made

Rule 28 duty (b) plus the "code is the source of truth" clause. No solve is
affected by any of these — they are all prose:

- `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3 — the `gas_daily_shape`
  and `CC_LIKE` rows restated from "proposed leg A/B" to LIVE, with the keeper's
  own `run_config` values cited.
- Same doc §B.4 item 1 — struck and replaced with the three-way closure (armed
  at pjm-107; the prediction was inverted; and the resolution objection that
  holds either way). §B.4's closing paragraph gains an OUTCOME stamp recording
  that both legs are adjudicated.
- `docs/mechanism-testing-matrix.md` §5.3 item 9 — struck, with the reason
  recorded rather than deleted so the error is not re-made; item 10
  (`winter_citygate_daily`) gains the same resolution bound; item 8
  (`st_gas_mustrun_p25_level`) has its overnight motivation withdrawn on the W4
  size measurement.
- `docs/codebase-site/data/mechanism-matrix.js` — header re-stamped for pjm-139;
  the `gas_daily_shape` and `winter_citygate_daily` notes carry the PJM-`K`
  confirmation and the all-ISO day-scale resolution bound. **No cell verdict
  moves** (no mechanism was armed and no run solved). `check_mechanism_matrix.py`
  passes.

## §8 — handover leads, stated but NOT built here

1. **`ramp_envelopes` is the pre-checked successor** — §5,
   `PREREG-pjm140-ramp-envelopes-2026-07-30.md`. It needs the PJM artifact built
   first (`derive_campd_ramp_envelopes.py --iso PJM`, the pjm-137 pattern of
   running a frozen derive for PJM for the first time), and it carries an
   unquantified LP memory cost that must be measured on one year before a
   three-year arm is launched.
2. **The overnight bottom-of-distribution miss is a separate, unexplained
   defect** (§W4) and the reserve credit does not touch it. What is now known:
   it is not pinning, it is not `ST_GAS`, and the model's overnight marginal
   supply is `CC_REGULAR` (66–69 %) plus `COAL_BIT` (23–26 %). What is not known
   is which *tranche* of those two sets the clearing point — the
   `_pjm138_marginal_ownership` census re-pointed at h01–h04 answers it with no
   LP (this probe carries it as `--with-fleet`/W6, unrun here because the
   container's `data/clean/` regeneration had not completed).
3. **Two owner-lane items remain pending from pjm-138** and are re-stated
   unchanged, since `keepers/PJM.json` is still unedited: (a) retire root cause
   (6) — coal no longer owns the $40–150 band; (b) restate root cause (3)'s
   deficit on the corrected hour key ($17.97 / $26.44 / $54.06, of which only
   8.1 / 23.1 / 22.1 % is reachable). pjm-139 adds a third: (c) root cause (3)'s
   reachable share is **concentrated in the winter morning ramp**, not spread
   across CT hours.
4. Carried from pjm-137, still open and still blocked: a `PJM_Dominion`
   NoVA/Loudoun split needs a measured sub-zonal load basis.

## §9 — what this session did NOT do, and why

**No arm was solved, no bundle was produced and nothing was registered on the
dashboard.** The chartered lever turned out to be armed in the keeper (§1), so
there was no A/B to run — arm B would have reproduced arm A. The successor lever
the measurement fired at (`ramp_envelopes`) is a *different* mechanism from the
one this session was chartered for: it needs an artifact that does not yet exist
for PJM, and under the protocol its pre-registration must be committed before any
arm solves. That pre-registration is committed here; the solve is the next
session's.

**The keeper's standing kills are unchanged because nothing was solved.** C3c
still passes by ~1 h (2024: 10 h model vs 18 h RT, 0.56×) and ~2.5 h (2025: 32 h
vs 59 h, 0.54×) against a 0.5× floor — still the thinnest margin in the keeper,
and note that a lever which forces CTs on at the winter morning ramp is expected
to *add* tail hours, so the PREREG watches its upper bound too. C8 `CT_PEAKER`
forced share stays 16.3 / 16.9 / 17.1 %, all GROUNDED. C1 stays 16/16 with free
12/12; ISO-wide `CT_PEAKER` |err| stays 2.11 / 3.57 / 3.32 TWh — which §5.2 now
attributes to the same root cause as the flat winter morning price.
