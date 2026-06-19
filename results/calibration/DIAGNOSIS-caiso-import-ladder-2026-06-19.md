# CAISO price level — why it's ~$22 too high, and the grounded fix (2026-06-19)

Branch: `claude/caiso-modeling-accuracy-td82v4`. Goal: find why the CAISO
backcast LMP is so far from actuals and fix it **without curve-fitting or magic
numbers**. Supersedes the open question left by `AUDIT-caiso-structural.md` /
`RESULTS-caiso-ra-mustoffer-floor.md`: after the RA must-offer floor + negative
renewable offers collapsed the *midday floor*, why is the annual **mean** still
~$55 vs actual ~$33?

All numbers from fresh 2024 keeper-config runs (`--commitment
--priced-interchange`, RA floor 0.80 + negative offers ON, 2024 hydro repin),
load-weighted system price vs `actual_lmp_hourly_CAISO.parquet`.

## TL;DR

CAISO's body is **+$22/MWh too high almost uniformly** (every month +$12…+$35
except January). Four re-solves isolate the cause, and it is **not** the import
ladder alone (the prior working hypothesis) — it is **gas-cost-bound**:

1. The **median hour is gas-CC-set at ~$56**; the cheaper hours (~21%) are set by
   the `DSW_solar_PV` import tranche ($48). The static import ladder pins the
   *lower* part of the curve but **gas sets the median**.
2. **The gas offer markup is not the lever.** Flattening the CAISO gas offer to
   cost (econ bands → 1.0×) moved the mean only $55→$48 and did **not** break gas
   volume (68.5 TWh vs ref 67.7) — but gas-*at-cost* is still ~$46-50 (HR 7.28 ×
   ~$4-5 gas + $13-14 CARB), **above the real $34 median.**
3. **Cheap imports cannot rescue the body.** Pricing *all* import tranches at
   realistic Mid-C/Palo-Verde levels ($18-34) moved the mean only $55→$50 while
   import volume **over-shot to 44 TWh** (vs 30.8 target) and gas fell to 59 TWh.
   The cheap-import capacity (~6 GW) is small against 25-45 GW demand, so domestic
   gas still tops up and **sets the median at its cost** no matter how cheap the
   imports are. The body is **bounded below by CA gas marginal cost (~$46-50).**
4. **The real median ($34) is BELOW CA gas cost.** Reality clears its median below
   what an efficient CA CC costs in the model — because its marginal CC bids the
   gas **commodity spot** (SoCal Citygate ~$3.0-3.5) not the F923 **all-in
   delivered** cost (~$4.2, transport reservation amortized in) the model assigns,
   plus abundant cheap hydro/imports. The model over-states the marginal *fuel*
   cost and so cannot price the median below ~$46.
5. **The negative tail is missing** — model 14 hours ≤ $0 vs actual **868** —
   because the node imports in **96% of hours** (never long) *and* the static
   import prices never go negative.

**Two grounded levers (no curve-fitting), both needing measured data the remote
env blocks:**

- **(A) Measured-hub import prices** — price each tranche at the measured WECC
  neighbor-hub LMP it proxies (Mid-C/Malin, Palo Verde), paired with the measured
  EIA-930 interchange *availability* envelope (`--interchange-shaping`, in repo) so
  volume stays real. Fixes the import-set hours and — because hub prices go
  negative in the desert-SW solar glut — the **negative midday tail**. *Mechanism
  built + tested this session* (`caiso_import_hub_prices`); needs the intertie LMP
  fetch. This does **not**, on its own, fix the gas-set median (lever B does).
- **(B) Marginal gas at the commodity spot, not F923 all-in delivered** — bid the
  gas-set median on the SoCal/PG&E Citygate spot (the marginal commodity; the
  pipeline reservation is sunk), not the transport-loaded F923 delivered cost.
  This is the gas-cost-bound body (the larger half of the +$22). Grounded in the
  sunk-cost principle, but needs measured Citygate spot gas (also env-blocked).
  *Diagnosed, not built* — flagged for a decision, since it borders the gas-input
  methodology.

The gas offer **curve** is left untouched (the markup is not the cause); the gas
*cost inputs* (HR, carbon) are measured and correct and must not be lowered to fit.

## Evidence

### Annual & monthly — a near-uniform +$22 overprice

| | model | actual RT | resid |
|---|---|---|---|
| annual mean | **55.0** | 32.9 | **+22.2** |

Monthly resid (+ = model high): Jan **−9**, Feb +27, Mar +30, Apr +26, May +27,
Jun +23, Jul +17, Aug +26, Sep +25, Oct +13, Nov +18, Dec +35. January (cold,
gas-set) is the only month the model is *under* — everywhere else the supply
stack prices above reality.

### What sets the price, by band (keeper `dispatch/2024_P2.parquet`)

| model price band | hours | marginal resource | cheap-import headroom |
|---|---|---|---|
| < $20 | 234 | gas decommitting / renewables | imports OFF |
| **~$48** | 1,874 (21%) | **`DSW_solar_PV` import** | PNW/Mid-C maxed, DSW_solar partial |
| **~$56** | 1,895 (22%) | **gas CC** | DSW_solar now maxed, DSW_CCGT not yet on |
| > $60 | 2,812 (32%) | DSW_CCGT / upper gas | — |

The cheap PNW/Mid-C blocks (4.4 GW) are **inframarginal baseload** — always maxed,
never price-setting. The price is set by the `DSW_solar` import block ($48) in the
cheaper hours and **gas CC ($56) at the median**.

### Duration curve — body too high, both tails missing

| pct | model | actual RT |
|---|---|---|
| p5 | 30.6 | −14.0 |
| p25 | 48.0 | 22.2 |
| **p50** | **56.0** | **34.0** |
| p75 | 62.2 | 44.6 |
| p95–max | 81.0 | 64.7 … 896.7 |

Median +$22. No negative tail (model **14 hrs ≤ $0** vs actual **868**); no upper
tail (max $81 vs p99 $143). Net import: importing **96.4%** of hours, exporting
1.6% (real CAISO exports ~11% midday) — the node is never long.

### Four re-solves isolate the lever

| run | mean | p50 | p25 | p5 | ≤$0 hrs | gas TWh | import TWh |
|---|---|---|---|---|---|---|---|
| keeper baseline | 55.0 | 56.0 | 48.0 | 30.6 | 14 | 71.3 | 35 |
| imports −$15 (static ladder) | 52.8 | 56.1 | 45.3 | 21.0 | 14 | — | — |
| gas→cost **+** imports −$15 | 48.2 | 50.1 | 41.7 | 21.0 | 14 | 68.5 | 35.2 |
| imports at ~Mid-C/PV ($18–34) | 50.1 | 51.5 | 44.8 | 24.0 | 14 | 59.2 | **44.4** |
| **actual RT** | **32.9** | **34.0** | **22.2** | **−14.0** | **868** | (67.7) | (30.8) |

- Lowering the **static** ladder −$15 barely moves the median ($56→$56): the cheap
  blocks are inframarginal, so a lower price on them adds no cheap import *volume*.
- Flattening the **gas offer** to cost adds only −$4.6 and does **not** break gas
  volume — but the floor is gas-*cost* ~$46-50, still ≫ $34. The markup is not it.
- Pricing **all** imports at realistic hub levels ($18-34) over-imports (44 TWh,
  +13 over target) yet the median only falls to $51.5 — domestic gas still tops up
  the 25-45 GW load above the ~6 GW of cheap imports and sets the median at its
  cost. **The body is gas-cost-bound; no import re-price alone reaches $34.**

### Carbon, gas cost, must-run, AS — ruled out

- **Carbon is correct.** CARB 2024 $35.23/t → border $15/MWh on unspecified
  imports, ~$13 on gas CC; actual CAISO LMPs include it (the OASIS `MGHG`
  component). Not a spurious inflator.
- **Gas cost is right, not high.** CA delivered gas $4.24/MMBtu (qty-wtd 2024,
  EIA-923), HR 7.28 (cap-wtd, EIA-860) — both measured. Do not lower them; reality
  simply has gas marginal *less often*.
- **AS reserve-withholding** is a documented near-no-op on a gas-long system
  (`caiso-as-reserve-formula-findings.md`); the **RA floor** already collapsed the
  midday *floor*. Neither touches the body.

## The grounded fix — two levers

### (A) Measured-hub import prices — built this session

Price each import tranche at the **measured hourly WECC neighbor-hub LMP** it
proxies, paired with the measured interchange-availability envelope:

- **PNW_hydro_base / PNW_midC** → Mid-Columbia / Malin (COI, PDCI) intertie LMP —
  crashes in the spring runoff (the real reason CAISO Apr/May RT is ~$11-14).
- **DSW_solar_PV / DSW_CCGT / DSW_CT** → Palo Verde / Mead (Path 46) intertie LMP
  — cheap-to-negative midday (desert solar), gas-set otherwise.
- Pair with `--interchange-shaping` (EIA-930 month×hour envelope, already in repo)
  so cheap imports clear up to the *real deliverable volume* and don't over-import
  (the hub-ladder run over-imported to 44 TWh precisely because it had no
  availability cap — the two must go together).

This fixes the **import-set cheaper hours and the negative midday tail** (hub
prices go negative in the solar glut), passing the forecast/backcast admissibility
test (`claude.md` #11) — the delivered cost of the imported energy, reproducible
and responsive, not a residual haircut. It does **not** by itself fix the gas-set
median (lever B); the two are complementary.

**Mechanism (default-off, byte-identical off, tested):**
`config.caiso_import_hub_prices` overwrites each import tranche's mc row with the
measured hub LMP + per-tranche border carbon, via
`eia_loader.measured_import_hub_prices` + `transmission.
inject_caiso_import_hub_prices` (mirrors the existing `inject_reference_price_mc`
seam). Tests: `tests/test_caiso_import_hub_prices.py` (5).

**Measured data it needs:** the WECC intertie scheduling-point LMPs — *not* in the
repo (the recovered CAISO LMP is the internal hubs TH_NP15/SP15/ZP26, i.e. the
model's *output*, not the import price). From CAISO OASIS `PRC_LMP` (DAM, v12) at
the intertie APNodes (Malin, NOB, Palo Verde, Mead), energy component (`MCE`),
aggregated to the model's local 8760 calendar into
`data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet` (columns
`year, hour, hub ∈ {MALIN, PALOVRDE}, price`). The remote env blocks
oasis.caiso.com, so it is fetched on a GitHub runner (extend the existing
`fetch-caiso-oasis` workflow with the intertie nodes — same `PRC_LMP` query as the
hubs it already pulls; validate the APNode names on the first run).

### (B) Marginal gas at the commodity spot, not F923 all-in delivered — diagnosed

The **larger half of the +$22** is the gas-set median: the model bids gas at the
F923 *delivered* cost (~$4.2/MMBtu, transport reservation amortized in), but the
marginal commodity a dispatched CC actually pays is the **Citygate spot** (~$3.0-
3.5) — the reservation is a *sunk* fixed cost that does not enter the marginal
offer. At HR ~7 that is ~$5-8/MWh of the body, and it is what keeps the model's
median floored at ~$46-50 when reality clears ~$34. CAISO is the only ISO priced
on F923 monthly *delivered* rather than a Henry-Hub-spot-plus-basis path; aligning
the marginal gas bid to the spot commodity is grounded in the sunk-cost principle.
Needs measured SoCal/PG&E Citygate spot gas (also env-blocked). **Diagnosed, not
built** — flagged for a decision (it touches the gas-input methodology, not the
offer curve).

## Status

- Diagnosis: **done** (this doc) — the body is **gas-cost-bound**; the import
  ladder sets only the cheaper hours + (absent) negative tail. Carbon, the offer
  markup, import volume, and the gas HR are ruled out as the cause.
- Lever A (`caiso_import_hub_prices`): built, flag-gated, default-off, tested;
  needs the intertie-LMP fetch + `--interchange-shaping` pairing.
- Lever B (marginal gas = Citygate spot): diagnosed, needs measured spot gas +
  a methodology decision.
- Grounded keeper + dashboard: blocked on the env-blocked measured data. Do
  **not** ship a fitted ladder or a lowered gas/HR as a stopgap — those are the
  artifacts this diagnosis removes.
