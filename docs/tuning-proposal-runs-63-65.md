# ERCOT tuning proposal — Runs 63–65 (from Run-61 baseline)

**Date:** 2026-06-09. **Baseline:** `results/calibration/Run-61` (2023/2024/2025,
P1, no commitment pass, historic outages, PRB sigmoid OFF, flat passthrough 1.0,
n=6 linear smoothing). All proposed changes stay inside the tranche-pricing +
n=6 smoothing framework; no gas-keyed sigmoid is reintroduced.

Diagnostics below were computed directly from the Run-61 (and Run-60/62)
bundles: dispatch parquets vs CAMPD hourly and EIA-923 annual, plus
`system.parquet` prices vs `inputs/calibration/actual_lmp.json`.

---

## 1. What Run-61 actually shows

### 1.1 The 2025 LMP blowup is load shed, not offer-curve pricing

| year | model LMP mean | model median | actual RT mean | hrs > $1,000 | unserved |
|------|---------------|--------------|----------------|--------------|----------|
| 2023 | $32.86 | $23.92 | $48.36 | ~9 | 7 GWh |
| 2024 | $29.53 | $21.01 | $26.83 | ~14 | 17 GWh |
| 2025 | **$213.06** | $33.16 | **$32.49** | **309** | **798 GWh** |

The 2025 median is fine; the mean is destroyed by 309 hours clearing at
$4,300–5,000, of which **209 have real unserved energy (up to 12.9 GW)**,
concentrated at hours 17–21 across Mar–Nov. Root cause: the backcast storage
fleet comes from `inputs/raw-data/eia-860/eia860_energy_storage_operable.parquet`,
whose max Operating Year is **2024** — so 2025 solves with **8.05 GW / 11.5 GWh**
of batteries while actual ERCOT 2025 ran ~12–17 GW. The missing ~5+ GW of
evening discharge is almost exactly the shed depth. CT peakers running flat-out
in those hours are a *symptom*: ~2.2 TWh of the 2025 CT overrun sits inside the
scarcity hours.

(2023 is the opposite, known issue: model $32.9 vs actual $48.4 because the
energy-only LP has no ORDC adders — Aug-2023 actual averaged $192/MWh RT.)

### 1.2 CC_CHP — the dispatch is capacity-truncated at the top, and econ-band
pricing is a dead lever

Class totals vs EIA-923 are essentially perfect (+0.1% / +0.2% / +1.7%), but the
*shape* is wrong, exactly as observed on the dashboard:

- Aggregate hours-at-CF (10 CAMPD-matched plants, 7.3 GW): model mode sits in
  the 50–70% bands with **zero hours above ~78%**; CAMPD spends 2,200–2,800
  hours in the 70–90%+ bands. Dispatch-only max CF: model 49% (2023) / 53%
  (2025) vs CAMPD 90% / 94%.
- Monthly deficit vs CAMPD ≈ −0.8 to −1.0 TWh in Jan/Feb and May–Sep (high-load
  months), shrinking to −0.3/−0.4 in shoulders — the 2–3 TWh/yr gap after the
  flat BTM add-back.
- **Run-62's experiment proves the econ band is inert:** widening the CC_CHP
  ramp from 1.01→1.07 to 0.90→1.25 changed *nothing* (total 53.05 TWh and
  hourly r identical to 3 decimals). At HR ≈ 5.4–7.3 the entire econ band costs
  $14–25/MWh and is always in merit.

The two binding constraints are structural:
1. **The peak cliff.** `pct_peaking = 8` (% of nameplate) is the entire top
   13–20% of grid-facing capacity, priced at 2.25× ≈ $44+/MWh (2025 gas). It
   only clears in near-scarcity hours, so the fleet's top is amputated in
   normal summer/winter peaks — precisely the months that under-run.
2. **The BTM pull-out.** `chp_btm_pct` removes 40% (merchant) / 60%
   (industrial+commercial) of nameplate from the LP; the report adds it back
   *flat*. With ~45–55% of fleet capacity removed, the dispatched portion
   cannot reproduce the observed 80–95% CF excursions no matter how it is
   priced.

Issue 1 is an offer-curve knob (this proposal). Issue 2 is a tranche-*sizing*
assumption — held back as optional Run 66 so it doesn't contaminate the
curve-shape isolation.

### 1.3 CT_PEAKER — Run-61's committed cut caused the blowup

vs EIA-923: Run-60 (committed 1.48) **+10.2%** (2023) → Run-61 (committed
−0.25 → 1.23) **+29.5%** → Run-62 (−0.30 → 1.18) **+47.1%**. The committed
band at 1.23 × HR ~11 clears ~$33–36 (2023 gas) and hoovers up mid-price hours.
2025's +73% is that same overrun plus the fake scarcity of §1.1.

Shape note: actual CT fleet spends ~2× more hours at 10–30% aggregate CF
(single-unit starts, RUC, reserve deployments) and **never exceeded ~55%
aggregate CF in 2025**; the model is hotter-but-rarer. Raising the committed
hurdle back is the in-framework fix; the residual low-CF texture is a known
energy-only-LP limitation (no AS co-optimization).

### 1.4 Coal PRB / lignite — the ramp is so cheap (and so flat) it never exits
merit, so 2025 dispatch is a flat line

Average intraday CF range (matched plants):

| | 2023 model | 2023 CAMPD | 2025 model | 2025 CAMPD |
|---|---|---|---|---|
| COAL_PRB | 20.7 pts | 32.2 pts | **3.7 pts** | **26.1 pts** |
| COAL_LIGNITE | 13.1 pts | 20.3 pts | 3.6 pts | 15.8 pts |

2025 actual PRB shows a clear duck-curve: overnight ~47–49%, **midday dip to
41–44%** (solar depressing prices), evening peak 59%. The model holds 50–53
all 24 hours. Cause: PRB econ ramp tops out at 0.90 × HR × fuel ≈ $19–24/MWh —
below the 2025 price trough, so every slice is in merit every hour. The same
logic at 2023 gas leaves partial range. The fix that needs no sigmoid: **steepen
the ramp** — drop econ_low (bottom slices stay baseload) and raise econ_high to
~1.25 so the top slices price ~$30–34 and swing out at troughs/midday.

**Oak Grove decoded.** From Aug 1 to mid-Oct 2023 the plant ran nightly
turndowns: 00–07 CF ≈ 47–55% (median 47%), back to ~87% by 09:00 — i.e. down
to almost exactly its modeled floor (must-run 35% + committed 15% = 50% of
nameplate; one unit's worth ≈ 51%). The model holds 84% overnight. The
structure to capture it already exists — the failure is that the lignite econ
band (1.14→1.15, effectively one flat block at ~$20–23) never exits merit
overnight. A steepened lignite ramp (1.00→1.45) prices the upper slices
$26–30 so they shed in low-price nights, reproducing both the Aug–Oct nightly
two-shift and the milder rest-of-year turndown (actual rest-of-year overnight
≈ 74% vs model ~84%).

### 1.5 CC_REGULAR — under, not over (the CAMPD view misleads)

vs EIA-923 (with BTM): **−4.9% (2023), +1.9% (2024), −5.1% (2025)** — about
−7 TWh in 2023/2025. (vs CAMPD it *looks* over because of gross-vs-net and
coverage gaps.) Run-60's econ_high 1.46 sat at −2.1%; Run-61's 1.54 deepened
it. Lowering econ_high (and reverting the CT committed cut, which steals CC
hours) is correct — confirming the operator's instinct.

### 1.6 Doc discrepancy (flag for /sync-docs)

`docs/offer-curve-methodology.md` §2 still says CC/COAL fold the peak into the
ramp (`_CURVE_FOLD_PEAK`). The current code (`fleet.py` ~2771) folds nothing:
every group's ramp spans econ_low→econ_high and the peak is always a separate
flat tranche sized by `pct_peaking`. The stale doc materially misleads tuning
(it implies CC_CHP's ramp already reaches 2.25×).

---

## 2. Proposed runs

Deltas are cumulative vs the run57 baseline curve in
`run_calibration.py` (the same convention Run-60/61/62 used), passed via
`--offer-curve-delta-json`. Reuse the Run-61 invocation:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
  --no-prb-passthrough-sigmoid --storage-daily-cycling \
  --out-dir results/calibration/Run-6X --note "<note>" \
  --offer-curve-delta-json '<json below>'
```

### Run 63 — 2025 structural fix (storage fleet), zero curve changes

**Change:** refresh the EIA-860 operable energy-storage parquet so 2025-online
batteries exist (EIA-860M monthly / 2025 early release; the current file stops
at Operating Year 2024). Target ~12–14 GW operational-weighted for the 2025
backcast year. **No offer-curve deltas beyond Run-61's** — this isolates the
2025 scarcity variable.

**Expect:** unserved 798 → <50 GWh; LMP mean $213 → ~$40–55; hrs >$1,000
309 → <30; CT_PEAKER 2025 +73% → roughly its 2023-like +30%; CC_REGULAR 2025
recovers some volume in evening hours. 2023/2024 essentially unchanged
(regression guard).

**Accept if** 2025 LMP mean lands within ~2× actual ($32.49) with 2023/2024
volumes within ±0.5 TWh of Run-61. Anything left of the 2025 CT overrun after
this run is genuinely offer-curve, and Run 65 sizes it.

### Run 64 — CC_CHP shape isolation (only CC_CHP touched)

Replace the 1.07→2.25 cliff with a continuous gradient and shrink the
expensive top band: resolved curve `committed 0.92, econ_low 0.96,
econ_high 1.35, peak 1.55, pct_peaking 4`.

```json
{"CC_REGULAR": {"econ_low": -0.05, "econ_high": 0.13},
 "CC_CHP": {"econ_low": 0.0, "econ_high": 0.23, "peak": -0.70, "pct_peaking": -4.0},
 "COAL_PRB": {"committed": -0.20, "econ_low": -0.11, "econ_high": -0.04, "peak": -0.025},
 "CT_PEAKER": {"committed": -0.25, "econ_high": 0.10},
 "ST_GAS": {"committed": -0.175, "econ_low": 0.025, "econ_high": 0.195}}
```

(Every non-CHP class restates Run-61 exactly.) For a typical HR-6.0 plant at
2025 gas: slices now span $20→29, peak band ≈ $33–37 — engages on summer days
and winter mornings, idles overnight; at 2023 gas: slices $15→21, peak ≈ $26.
That is the "smoother econ-high→peak transition than CC_REGULAR" hypothesis,
implemented (CC_REGULAR keeps its 1.54→2.25 step; CHP's becomes 1.35→1.55).

**Expect:** the hours-at-CF mode shifts right by roughly a decile; the
Jan/Feb + May–Sep monthly deficits shrink by ~0.3–0.6 TWh/mo at dispatch
level; CC_CHP annual total drifts up to ~+2–3% vs 923 (was +0.1/+1.7) — the
freed hours come out of CT_PEAKER/CC_REGULAR/PRB overruns. Hourly r vs CAMPD
(dispatch) should rise from 0.83/0.79.

**Accept if** class total stays ≤ +3–4% vs 923 while plant-capture/r improve.
**If the top decile (80%+) is still empty**, that confirms the BTM ceiling →
Run 66.

### Run 65 — cross-class rebalance (CT revert, CC_REG, coal intraday)

Carry the Run-64 CC_CHP winner, then:

```json
{"CC_REGULAR": {"econ_low": -0.05, "econ_high": 0.05},
 "CC_CHP": {"econ_low": 0.0, "econ_high": 0.23, "peak": -0.70, "pct_peaking": -4.0},
 "CT_PEAKER": {"econ_high": 0.10},
 "ST_GAS": {"committed": -0.10, "econ_low": 0.025, "econ_high": 0.195},
 "COAL_PRB": {"committed": -0.20, "econ_low": -0.20, "econ_high": 0.30, "peak": -0.025},
 "COAL_LIGNITE": {"econ_low": -0.14, "econ_high": 0.30}}
```

Resolved: CT committed back to **1.48** (Run-60 proved 1.23→1.48 is worth
~−19 pp of CT overrun); CC_REGULAR econ_high **1.46** (Run-60's −2.1% level);
PRB ramp **0.50→1.24** (bottom slices unconditionally baseload, top slices
$30–34 so they shed at 2025 middays/overnights and 2023 troughs); lignite ramp
**1.00→1.45** (upper slices $26–30 exit overnight → Oak Grove two-shift);
ST_GAS committed 0.81 (Run-61's 0.735 ran +9.1% in 2025).

**Expect:** CT 2023 +29.5 → ~+10%, 2025 (post-Run-63) → +10–20%; CC_REGULAR
2023/2025 → ~−2%; PRB intraday range 3.7 → 15–25 pts in 2025 with annual
+8.3% → ~+2–4%; lignite range 3.6 → ~10–15 pts; Oak Grove Aug–Oct overnight CF
drops toward its 50% floor.

**Known tension (accepted, no sigmoid):** raising the PRB top will deepen 2024
PRB (−3.2% → maybe −6 to −8%) because 2024's cheap gas prices PRB out — this is
the gas-year effect the sigmoid bought. Decision rule: if 2024 PRB lands below
~−10%, prefer improving per-plant monthly EIA-923 PRB delivered-cost grounding
(physical data, not a fitted curve) over reintroducing the sigmoid.

### Run 66 (optional, only if Run 64's top decile stays empty)

Trim the CHP BTM pull-out (`CHP_BTM_PCT_BY_SECTOR`: industrial/commercial
60 → 50, merchant 40 → 35). This is a tranche-sizing (physical host-self-supply
share) change, not a price fit: it raises the dispatchable ceiling so the fleet
can reach the observed 85–95% CF excursions, while the flat report add-back
shrinks correspondingly (level roughly conserved, shape moves into the LP).
Run it alone — it shifts both level and shape for all three CHP classes.

---

## 3. Order and isolation logic

1. **Run 63 first** — it's the only change that touches the 2025 price
   formation, and every other class's 2025 error is contaminated by the fake
   scarcity. Cheap to validate.
2. **Run 64 second** — single-class isolation of the CC_CHP shape hypothesis;
   its volume spillover (CT/CC_REG/PRB give back overrun) is read directly in
   the signed-error table.
3. **Run 65 third** — rebalance with the CT/CC_REG/coal levers whose directions
   Run-60/61/62 already bracketed, sized on top of 63+64 outcomes.

Primary success metric stays dispatch integrity (class volumes vs 923 within
tolerance, hourly r / NRMSE / capture improving, intraday coal range), with
2025 LMP mean falling out of the structural fix rather than being chased with
price knobs.
