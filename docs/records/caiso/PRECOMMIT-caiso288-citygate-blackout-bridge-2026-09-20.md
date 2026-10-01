# PRECOMMIT caiso-288 — the 2022 C3a miss is an EIA PUBLICATION BLACKOUT in the measured citygate series, and the repair is chosen on withheld gas days before any LP is spent

**Lane:** CAISO calibration · **Date:** 2026-09-20 · **Keeper UNCHANGED**
`2026-09-19-caiso-287-mer-keeper` (bundle `caiso287_mer_span`, 2023–2025) with
`2026-09-19-caiso-287-mer-2022` (bundle `caiso287_instr_2022`) folded to it under rule 30
`[R-TOUCHPOINT-FOLD]` (a). **LP spent so far: ZERO.** Predecessor:
`docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md`, whose §8 named the 2022 C3a
object "on its own terms" as the honest successor. This document fixes **the object, the
mechanism, the identification, the gates, the predicted numbers and every outcome word
before a single shard is launched.** Nothing below was computed after seeing a solve,
because no solve exists.

---

## 0. The answer phase 0 already has, in one paragraph

**240 hours carry 45.9 % of the 2022 C3a failure, and they are exactly the hours for which
no gas price was ever measured.** EIA publishes no *Natural Gas Weekly Update* in
Thanksgiving week or in the two weeks spanning Christmas/New Year — every year — so the
committed CA Composite daily citygate series has an 8–19 day hole in November and December
of **every** year in the record. `_flow_date_staircase` constant-extends the last print
across that hole. In December 2022 the last print is **$53.59/MMBtu, the single highest
print of the year**, and it is held flat across **10 of December's 31 days** while the
measured record says the western gas crisis was collapsing through precisely those days.
The model's error over Dec 22–31 is **+$187.8/MWh**; over Dec 1–21, the days that *do* have
prints, it is **−$13.8/MWh**. The repair is not a lever and not a tuning channel: it is
rule 14 `[R-ACCURATE]` applied to an extrapolation that is standing in for a measurement,
and the construction that replaces it is selected by **reconstruction skill against 33,216
withheld measured gas days, with no reference whatever to the CAISO price residual.**

---

## 1. PHASE 0 — the decomposition, at zero LP, from committed artifacts only

Every number in this section is arithmetic over `frontend/data/backcast/runs/<id>.js`,
`frontend/data/backcast/bench/CAISO/<year>.json.gz` and the keeper's own committed
`hourly/` sidecars. No solve, no `fleet_only` rebuild, no LP.

### 1.1 The 2022 C3a gap by month — December is the plurality, but nothing is innocent

Reproducing `calibration_verdict.score_price_mean` exactly (load-weighted across zones,
`rt_lw` basis per §7 of the handoff): **model 94.0739 vs actual 84.4900, +11.34 %**, band
±10 %.

| month | model | actual | Δ$ | err % | load wgt | contrib $/MWh | share of gap |
|---|--:|--:|--:|--:|--:|--:|--:|
| Jan | 55.23 | 43.52 | +11.71 | +26.9 | 7.78 % | +0.911 | 9.5 % |
| Feb | 50.66 | 38.96 | +11.70 | +30.0 | 7.01 % | +0.820 | 8.6 % |
| Mar | 47.68 | 43.56 | +4.12 | +9.5 | 7.54 % | +0.311 | 3.2 % |
| Apr | 59.20 | 49.76 | +9.44 | +19.0 | 7.27 % | +0.687 | 7.2 % |
| May | 66.41 | 58.76 | +7.65 | +13.0 | 7.90 % | +0.604 | 6.3 % |
| Jun | 75.13 | 70.77 | +4.36 | +6.2 | 8.94 % | +0.389 | 4.1 % |
| Jul | 79.55 | 71.80 | +7.75 | +10.8 | 9.68 % | +0.750 | 7.8 % |
| Aug | 103.20 | 96.77 | +6.43 | +6.6 | 10.43 % | +0.670 | 7.0 % |
| Sep | 125.17 | 123.41 | +1.76 | +1.4 | 9.74 % | +0.171 | 1.8 % |
| Oct | 69.85 | 64.33 | +5.52 | +8.6 | 8.19 % | +0.452 | 4.7 % |
| Nov | 86.22 | 82.92 | +3.30 | +4.0 | 7.46 % | +0.246 | 2.6 % |
| **Dec** | **291.72** | **242.20** | **+49.52** | **+20.5** | 8.08 % | **+4.001** | **41.7 %** |

**Reported against the thesis, first:** every month is positive. 58 % of the gap lives
outside December, and the broad shoulder over-price (Apr +19 %, May +13 %) is visible in
2023/2024/2025 too (2024 May **+85.6 %**). **This PRECOMMIT does not claim to explain
that**, and §6.2 states what it means for the verdict.

### 1.2 December 2022 is a *plateau*, not a spike — and the plateau is the marginal fuel

Daily load-weighted model price rises from ~$130–180 on Dec 1–8 to **$358–448 on Dec 22–31**,
with 367 of 744 hours above $300, a p75 of $411 and a p90 of $431.7 — a tight cluster, not a
tail. **Zero slack, zero dump MWh in the entire month**, so no scarcity is involved.

The marginal *technology* never changes: implied heat rate from the committed
`marginal_emission_rate` is **7.82–7.87 all year** (gas CC), with 216 of 225 Dec 23–31 hours
gas-marginal. What moves is the implied fuel: **$6.67/MMBtu median in January, $9.00 in
July, $9.69 in November — and $32.72 in December.**

### 1.3 The model's own December 2022 gas input, reconstructed with production code

`_flow_date_staircase` on the committed `caiso_citygate_daily.csv` (the keeper runs
`caiso_citygate_spot_level = True`, `caiso_citygate_flow_date = True`,
`caiso_citygate_spot_coverage = True`, so these absolute $/MMBtu *are* the month's level):

```
Dec 01–22   measured prints, flow-dated          $14.90 – $53.59
Dec 23–31   $53.59  $53.59  $53.59  $53.59  $53.59  $53.59  $53.59  $53.59  $53.59
            ^^^^^^ ten calendar days, one print, zero measurements
Dec month mean $36.78/MMBtu   (days 1–22 alone: $29.91)
```

The last measured trade is **2022-12-21 at $53.59/MMBtu**, the year's maximum. It flows on
Dec 22 and is then held for nine more days. 7.82 × $53.59 ≈ $419, plus VOM/transport/carbon
≈ the observed **$430–441 plateau**, to the dollar.

### 1.4 The decisive measurement: the model's error is *created* on the unmeasured days

From the committed `lmpDeltaHr` (model − actual RT, load-weighted, hourly — the payload's
own field, already used by `score_diurnal_amplitude`), December 2022 daily:

```
Dec 01..21   -14.8 -11.3 -24.1  -1.2  +1.5 +25.8  -6.8 -15.3 -38.7 +39.5 +41.7
             +25.7 -33.9 -25.1 -37.1  +4.7  +1.5 -17.4 -39.1 -74.5 -53.6      mean  -12.0
Dec 22       -44.5                                                    (crisis peak still real)
Dec 23..31  +108.2 +137.2 +162.5 +159.0 +240.2 +229.4 +262.7 +304.2 +315.4    mean +187.4
```

**The divergence begins the day the measurements stop and grows monotonically**, exactly as
a frozen price must against a collapsing one. Load-weighted, over the full year:

| window | load share | mean model−actual | contribution | share of the +$10.32 gap |
|---|--:|--:|--:|--:|
| **Dec 22–31 (the blackout)** | **2.52 %** | **+187.82** | **+4.731** | **45.9 %** |
| Dec 1–21 (measured days) | 5.56 % | **−13.77** | −0.766 | −7.4 % |
| Jan + Feb | 14.79 % | +11.71 | +1.731 | 16.8 % |
| Mar – Nov | 77.14 % | +5.99 | +4.621 | 44.8 % |

### 1.5 The blackout is structural, annual, and in the source — not in our scrape

Probed live: `archivenew_ngwu/2022/12_22/` → **HTTP 200**; `2022/12_29/` → **404**;
`2023/01_05/` → **404**; `2023/01_12/` → **200**. The EIA archive index carries **1,463**
weekly pages and is missing the Thanksgiving-week and Christmas/New-Year pages in *every*
year. **The fetcher is not at fault and re-fetching cannot close this**, so rule 14's "go
get the accurate data" has no route through this source and the misalignment exception
applies: prefer a *reconciled* version of the real data over the guess.

Per-year: 2022 blackouts at Nov 18 (11 d) and **Dec 23 (9 d)**; 2023 Nov 17 (11 d), Dec 22
(10 d); 2024 Dec 20 (12 d), Nov 22 (11 d); 2025 Dec 19 (13 d), Nov 21 (11 d). **The hole is
in every year; only 2022's opens on a spike**, which is why only 2022 is disfigured by it.

---

## 2. THE MECHANISM — one flag, one seam, zero free parameters

`ScenarioConfig.caiso_citygate_blackout_bridge` (bool, **default False**, CAISO-only).
When armed, `_caiso_hub_daily_gas_prices` passes the full multi-year dated citygate map and
the measured Henry Hub daily series into `_flow_date_staircase`, where a gap of
`>= _GAS_BLACKOUT_MIN_GAP_DAYS` calendar days between consecutive measured prints is rebuilt
by `_basis_bridge_blackouts`:

```
citygate[d] = HH_staircase[d] + basis_L + w(d) × (basis_R − basis_L)
basis_X = citygate[X] − HH_staircase[X]   at the two bracketing MEASURED prints
```

Every gap shorter than the threshold is untouched and still staircases. A **December**
blackout is bracketed against the **next January's** first print, which is the one anchor
the existing within-year construction cannot reach — hence the multi-year map.

**Rule 19 `[R-ONE-MECH]`:** it **replaces** the constant extension on those days; it does
not stack a second thing on top of it, and it touches no other day.
**Rule 25 `[R-ISO-SCOPE]`:** CAISO-only. The identical blackout exists in the MISO / NEISO /
NYISO daily series (the NGWU skip is nationwide) and those cells enter the matrix as `U`
for their own lanes to test on their own evidence. No number crosses an ISO boundary.
**Rule 13 `[R-MEASURED]`:** every input is measured (both bracketing citygate prints; the HH
daily series inside the gap), and the identical construction regenerates for a forward year
from forward curves. Nothing is pinned to any outcome.
**Rule 24 `[R-REGISTRY]`:** the field is in `ScenarioConfig`, in `_CACHE_KEY_OPTIONAL_FIELDS`
and in the default ledger **in the same commit** (the nyiso-119 discipline), so it appears in
`run_config.json` and an armed run hashes distinctly while every existing key is preserved.

### 2.1 THE THRESHOLD IS IDENTIFIED BY AN EMPTY REGION OF THE DATA, NOT CHOSEN

Trade-gap histogram of the committed series, 2018–2026, 1,805 gaps:

```
  1 d: 1401    2 d:    2    3 d:  312    4 d:   52     <- the market's TRADING PACKAGES
  5 d:    3                                            <- holiday weeks, short table
  8 d:   17    9 d:    1   12 d:    9   15 d:    7   19 d: 1   <- PUBLICATION BLACKOUTS
```

Gaps of 1–4 days *are* the packages the index is quoted in (consecutive weekdays; the Friday
trade that covers Sat–Mon; its holiday-extended Sat–Tue form) — a real trade priced those
flow days and the staircase is **correct** for them. Gaps of ≥ 8 days are weeks with no
publication at all: **no trade priced those days.**

**The histogram is EMPTY at 6 and at 7.** Any threshold in `[6, 7]` selects the identical 35
gaps and produces byte-identical output, so the value **cannot have been chosen against any
result**. 6 is taken as the lower edge. The three 5-day gaps stay on the staircase — the
conservative side of the split. Pinned by
`tests/iso/caiso/test_caiso288_blackout_bridge.py::test_threshold_sits_in_an_empty_region_of_the_gap_histogram`.

### 2.2 THE CONSTRUCTION IS SELECTED ON WITHHELD GAS, NEVER ON THE PRICE RESIDUAL

**This is the load-bearing pre-registration of this document (rule 1 `[R-STRUCT]`).** The
three candidate fills were scored by **synthetic holdout on the measured citygate series
itself**: every fully-measured window of 8 / 12 / 15 / 19 days in the committed record has
its interior withheld, each construction reconstructs it from the bracketing prints, and the
error is measured against the withheld truth.
`scripts/probes/caiso288_blackout_census.py`, **33,216 withheld measured days**:

| construction | MAE | bias | RMSE | p95 abs err |
|---|--:|--:|--:|--:|
| (a) hold last — **what the code does today** | 0.716 | +0.039 | 2.376 | 1.950 |
| (b) linear interpolation | 0.519 | +0.033 | 1.873 | 1.335 |
| **(c) HH-basis interpolation — ARMED** | **0.481** | **+0.017** | **1.787** | 1.342 |

(c) wins on MAE at **every** gap length (8 d 0.406 / 12 d 0.474 / 15 d 0.504 / 19 d 0.500)
and on bias at every gap length. Restricted to the case that actually matters — a blackout
opening on a top-decile print — hold-last carries a **systematic +0.879 $/MMBtu HIGH bias**
(MAE 2.923) against (c)'s +0.170 (MAE 1.681). The current behaviour is therefore not merely
noisy: it is **one-sidedly too expensive exactly when the last print is extreme.**

**No CAISO price, no C3a residual and no gate was consulted in this selection**, and the
ranking is monotone, so no tie had to be broken by anything else.

### 2.3 What is NOT claimed

* **The sibling series are not touched.** `_trade_date_staircase` (Henry Hub daily shape,
  dual-fuel) and MISO's `_flow_date_staircase` consumer are byte-identical: the bridge is
  reached only through `_caiso_hub_daily_gas_prices` behind the flag.
* **The Jan/Feb and shoulder over-price is NOT addressed** (§1.1). It stays open.
* **This is not the belly object.** caiso-285's belly deficit and the reversed seam
  direction are untouched, and caiso-287 §8's open `startup_aware` admissibility question is
  **not** re-opened here — it remains an owner rules-1/13 question and this lane proposes no
  value on it, arms nothing and disarms nothing.

---

## 3. BYTE-IDENTITY OFF — proved, not asserted

Measured before this document was pushed:

1. `_caiso_hub_daily_gas_prices` for 2022 with the field **absent** (default) and with it
   explicitly `False` returns arrays that are **`np.array_equal` identical**.
2. `_flow_date_staircase(dated, year)` and `_flow_date_staircase(dated, year, None, None)`
   are `np.array_equal` identical for 2022 / 2023 / 2024 / 2025
   (`test_staircase_off_is_byte_identical`).
3. `cache_key()` is **unchanged** between the field-absent and `False` configs, and
   **differs** when armed.
4. The full `tests/unit/data` + `tests/iso/caiso` run (2,576 passed) carries **exactly the
   six failures clean `main` carries**, verified by `git stash` on an *uncommitted* tree —
   the handoff §6 trap, avoided. `test_persisted_identity::...[NYISO]` fails identically
   (`bd2b4657f9b5df7e`) before and after; **CAISO's solve-surface fingerprint does not move.**

**Guards:** `tests/iso/caiso/test_caiso288_blackout_bridge.py`, 5 cases — packages untouched;
the bridge lands exactly on HH + interpolated basis and reproduces both measured endpoints;
off is byte-identical; the threshold sits in the empty histogram region; and the mechanism is
**not one-directional** on the committed series.

---

## 4. THE PREDICTION, FIXED BEFORE ANY LP IS SPENT

Computed from the production loader, zero LP:

| year | hours moved | annual mean Δ gas | max abs Δ | December month mean |
|---|--:|--:|--:|---|
| **2022** | 720 / 8760 | **−0.250** | 23.602 | **$36.78 → $33.05** |
| 2023 | 624 / 8760 | +0.108 | 11.213 | $3.68 → $3.96 |
| 2024 | 1080 / 8760 | −0.027 | 0.980 | $3.21 → $3.15 |
| 2025 | 984 / 8760 | +0.007 | 0.991 | $3.29 → $3.28 |

Dec 22–31 2022: **$53.59 flat → a $53.59 → $29.99 decay, mean $42.03 (Δ −$11.57/MMBtu)**.
**November 2022 RISES +$0.84/MMBtu** and January 2023 rises +$1.11 — the mechanism moves gas
in both directions, which is what a construction does and a fit does not.

**PRE-REGISTERED POINT PREDICTION for 2022** (Δgas −11.57 × measured marginal HR 7.82 =
**−$90.5/MWh** on a 2.52 % load share = **−$2.28/MWh** annual):

> **model 94.07 → ≈ 91.8 $/MWh, C3a +11.34 % → ≈ +8.6 %, i.e. a PASS with ≈1.4 pp of margin.**

2023/2024/2025 are predicted **near-inert** (annual gas Δ ≤ 0.11 $/MMBtu).

---

## 5. PRE-REGISTERED GATES — all fixed here, none computed yet

**G-FILL — already PASSED, above.** The construction ranking on withheld measured gas days
(§2.2). Had (c) not strictly beaten (a) on both MAE and bias, **the arm would not have been
built.** It is recorded as spent, on data alone.

**G-FOOT — FOOTPRINT.** The armed-minus-control hourly gas delta must be **exactly zero
outside the 35 identified blackout gaps**, in every year. A single moved hour on a
package-gap day is a **defect** and stops the session.

**G-PRED — the point prediction, stated as a gate.** 2022's armed C3a must land within
**±1.5 pp** of the pre-registered ≈ +8.6 %. A miss is **not** a failure of the mechanism —
it is a failure of my linear sizing — and is reported as such, at full magnitude, rather
than re-explained after the fact.

**G-INERT — the untouched years.** 2024 and 2025 armed-minus-control load-weighted price
must move by **< 1.0 %** each. A larger move means the mechanism reaches further than §4
says and the footprint claim is wrong.

**G-CTRL — form 1, a SOLVED per-year control.** Form 4 (difference against the committed
keeper) is **NOT AVAILABLE here and this is stated rather than assumed**, for two independent
reasons, either sufficient:
  1. **Rule 36 `[R-YEAR-ISOLATION]` (owner, 2026-09-19).** `caiso287_mer_span` is a
     **three-year span solve**, so its 2024 and 2025 numbers carry the cross-year basis
     contamination rule 36 was written out of, and its `git_sha` `92b8e4db` predates the flip
     of `MARKET_SIM_WARMSTART_XYEAR` / `MARKET_SIM_P1_BASIS_SEED` to **off**. A per-year
     isolated re-solve therefore differs from it for reasons that have nothing to do with
     this arm.
  2. **G-DRIFT finds LIVE hunks.** `git diff 92b8e4db HEAD` over the solve path is **2,062
     insertions across 18 files**, including `pipeline/commitment.py` (+169),
     `model/interchange/spec.py` (+75), `data/outages.py` (+108),
     `data/fleet/campd_bins.py` (+99) and `runner.py` (+22). These are not all classifiable
     as INERT for a CAISO backcast without an audit this session has not done, and rule 29
     `[R-SCREEN]` (b) says a LIVE hunk is **exactly** what earns a control solve.
**So eight shards, not four: `{control, arm} × {2022, 2023, 2024, 2025}`, every one a
single-year isolated solve at ONE pinned SHA.** Attribution is then `arm − control` within
each year, in one regime, with nothing inherited.

---

## 6. EVERY OUTCOME, NAMED BEFORE THE ANSWER EXISTS (rule 1 `[R-STRUCT]`)

**6.1 A verdict is not a promotion.** This session registers what it solves (rule 15
`[R-DASHBOARD]`) and **asks** the promotion question (rule 31 `[R-RETAIN]`); it does not
pre-empt it in either direction.

**6.2 IF 2022 C3a PASSES.** The 2022 rung's last load-bearing failure closes and CAISO's
registered set reads clean. **This does NOT change the ISO's determination**, which is the
2023–2025 verdict and was already `CALIBRATED` (rule 30 `[R-TOUCHPOINT-FOLD]` (c): a
held-out year never certifies and never decertifies). The correct report is "a data-
completeness defect that disfigured one year is repaired", **not** "CAISO got better". And
§1.1's finding stands regardless: **every month of 2022 is over**, the shoulder over-price is
present in all four years, and the blackout bridge explains none of it. That remains the
open object and this document says so in advance.

**6.3 IF 2022 C3a STILL FAILS.** The mechanism is still correct — it is rule 14, decided on
G-FILL, and rule 1 forbids reverting a structurally-grounded measured-input repair because
the residual did not move far enough. It is reported as a partial close with the remaining
gap named, and the successor is §1.1's broad over-price.

**6.4 IF G-FOOT OR G-INERT FAILS.** The implementation reaches further than the design says.
That is a **defect in my code**, the session stops, and nothing is promoted.

**6.5 IF THE ARM MAKES A YEAR WORSE.** Reported at full magnitude and **not** reverted on
that ground. 2023's January rises $1.11/MMBtu and November 2022 rises $0.84 — the arm is
expected to cost something somewhere, and a measured-input repair that costs residual is
still the right input (rule 14, in terms).

**6.6 WHAT THIS SESSION REFUSES, named so it can be checked.**
* **No sweep.** `_GAS_BLACKOUT_MIN_GAP_DAYS` is not varied against any gate; §2.1 makes
  [6, 7] observationally identical and nothing outside it will be tried.
* **No second construction tried after seeing a price.** (b) and (a) were scored on gas
  alone, before any LP, and the ranking is recorded above. If (c) disappoints, (b) is **not**
  then run as a fallback — that would be selection against the residual.
* **No offer-curve multiplier**, no adder, no haircut, no proxy. There is **no
  `authorized_price_tuning` block** and the DOF ledger gains **no entry**: the mechanism has
  zero free parameters.
* **caiso-287's closed list stays closed** (the decommit screen, the gap-fusing question,
  the CC start cost, flat-vs-downtime-keyed start cost, CAISO public bids, the CAMPD
  start-fuel derive) — nothing here is new evidence against any of them.
* **The `startup_aware` drop-rate admissibility question is not touched** (§2.3).
* **Nothing is deleted** (rule 31 `[R-RETAIN]`), and the promotion question is surfaced in
  the RESULT rather than answered by this session's own judgement.

---

## 7. THE SHARDS — eight, one per (arm, year), all pinned to ONE immutable SHA

**THE PARENT NEVER SOLVES** (rule 32 `[R-SHARD]` (a)). **One year per shard** (rule 36
`[R-YEAR-ISOLATION]` (a); the parent composes the per-year legs afterwards as a zero-LP file
operation). **Every shard pushes its whole bundle** to its own branch by `.gitignore`
NEGATION plus a **plain** `git add`, never `git add -f` (rule 34 `[R-SHARD-PROMOTABLE]` (a)
and its 2026-09-12 correction), including `dispatch/<year>_P1.parquet`, which registration
requires.

| # | arm | year | source bundle | out-dir | branch |
|---|---|--:|---|---|---|
| 1 | control | 2022 | `caiso287_instr_2022` | `caiso288_ctl_2022` | `claude/caiso-288-ctl-2022` |
| 2 | arm | 2022 | `caiso287_instr_2022` | `caiso288_arm_2022` | `claude/caiso-288-arm-2022` |
| 3 | control | 2023 | `caiso287_mer_span` | `caiso288_ctl_2023` | `claude/caiso-288-ctl-2023` |
| 4 | arm | 2023 | `caiso287_mer_span` | `caiso288_arm_2023` | `claude/caiso-288-arm-2023` |
| 5 | control | 2024 | `caiso287_mer_span` | `caiso288_ctl_2024` | `claude/caiso-288-ctl-2024` |
| 6 | arm | 2024 | `caiso287_mer_span` | `caiso288_arm_2024` | `claude/caiso-288-arm-2024` |
| 7 | control | 2025 | `caiso287_mer_span` | `caiso288_ctl_2025` | `claude/caiso-288-ctl-2025` |
| 8 | arm | 2025 | `caiso287_mer_span` | `caiso288_arm_2025` | `claude/caiso-288-arm-2025` |

Arm shards add exactly `--set caiso_citygate_blackout_bridge=true`; control shards add
nothing. **That single token is the entire difference between the two legs.**

Rule 34 `[R-SHARD-PROMOTABLE]` (c): the ISO's registered year set is
**{2022, 2023, 2024, 2025}**, enumerated from `frontend/data/backcast/registry/*.json`
**before** anything is pruned (rule 35 `[R-PROMOTE]` (b)), and all four are solved.

**Hard stops each shard is given, self-checkable:** the pinned 40-character SHA
(`git rev-parse HEAD` must equal it; never rebase, never pull, never "sync"); the config
signature its leg must show (`caiso_citygate_blackout_bridge` **true** on an arm shard,
**false** on a control, `caiso_citygate_flow_date`/`spot_level`/`spot_coverage` all true in
both); its own out-dir and branch and **nothing outside them** in `git status --short`.
**Explicitly forbidden by name:** `git add -A`, `git add .`, `git add -f`;
`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `prune_iso_runs.py` and
anything under `frontend/data/backcast/**`; any edit under `src/` or `scripts/`; opening a
PR; deleting any result. **A shard that stops with a clear report is a SUCCESS; a shard that
repairs infrastructure is a FAILURE.**

Memory (rule 32 (c)(8)): run the runner unmodified, never pass `--no-container-preflight`,
and report the `container preflight:` and `memory peak:` lines. CAISO 2024 instrumented at
caiso-287 took 23.0 min / 8.28 GiB peak, inside the 13.34 GiB nested-cgroup ceiling.

---

## 8. COST, stated before it is spent

Eight single-year CAISO solves, ~15–25 min each, in eight containers, launched together.
**The parent spends ZERO LP**: phase 0, the G-FILL selection, the footprint check, the
differencing, the composition, the scoring and the registration are all arithmetic over
committed artifacts and returned bundles.

Rule 33 `[R-SHARD-ARCHIVE]`: each shard is archived the moment the parent has fetched,
checked out and **verified** its bundle (config signature + `git ls-tree` showing a non-empty
bundle path, rule 34 (d)), and the recovery line in the RESULT carries a **full SHA**, never
a branch name.

**Nothing is deleted** (rule 31 `[R-RETAIN]`). The bundles live on local disk, the container
is ephemeral, and the promotion question is asked explicitly in the RESULT before this
session ends.
