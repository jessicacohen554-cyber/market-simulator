# ERCOT-70 — the supply-mix decomposition: the over-dispatched class NAMED

**Status:** DIAGNOSTIC COMPLETE (no build, no keeper change). The
moderate-tightness under-priced hours' phantom cheap supply is **+1.2–1.7 GW
of CC_REGULAR, concentrated in four CAMPD-invisible plants** (an availability
blind spot, Hidalgo's real Apr–May-2024 outage the headline case), with
storage and West/Panhandle gas both REFUTED as owners by direct measurement.
A second, coupled finding: the model's offer stack is FLAT between econ_high
and the peak rungs, so the supply-mix fix can only form the target prices in
COMPOSITION with the (already-built, default-off) ERCOT-69 midcurve belt —
which was probe-inert precisely *because* this phantom keeps clearing shares
below the belt. Keeper UNCHANGED (`2026-07-15-ercot66-storage-rebasis`).

Probe artifact: `scripts/probes/_ercot70_mix_decomp.py` (scorer-only, reads a
keeper-reconstruction bundle; regenerates every table below). The rule-16
single-year bundle (`ercot70_keeper_2024`) is a throwaway, deleted at session
end; regenerate with
`python scripts/probes/_ercot68_ladder_probe.py keeper --years 2024 --out-name ercot70_keeper_2024`.

---

## 1. The ERCOT-70 calibration-log entry (verbatim — merged into `docs/calibration-log.md`)

### 2026-07-16 — ERCOT-70: the supply-mix decomposition on the moderate-tightness under-priced hours — the over-dispatched class NAMED (+1.2–1.7 GW phantom CC_REGULAR in four CAMPD-invisible plants; storage and West gas REFUTED by measurement); the flat mid-stack makes it a composition lane with the ERCOT-69 midcurve belt; keeper UNCHANGED

**Task (owner-issued charter, the ERCOT-69 hand-off).** Convert the ERCOT-69
supply-mix adjudication into "THIS GW of THIS class in THESE hours": decompose
model dispatch-by-class vs measured generation on the moderate-tightness
under-priced hour sets (May-2024 shoulder-day daytimes, Nov-2024, Apr-2024),
rank the three prime suspects (storage over-discharge, West/Panhandle gas,
perfect-foresight ceiling), name the owner mechanism, adjudicate an admissible
fix.

**Leg 0 (keeper reproduction, 2024).** `2026-07-15-ercot66-storage-rebasis`
reconstructed byte-for-byte: C3a −14.2% (26.38 vs 30.74), C3b 0.212, C3c 20h
vs 68; May −12.5, Nov −5.8, Apr −4.1; shoulder family May-9/10/12/13/21/27/
29/30 = −30.8/−15.7/−20.4/−22.3/−26.7/−27.0/−15.9/−18.5. All controls verified.

**The decomposition** (`scripts/probes/_ercot70_mix_decomp.py`, scorer-only —
model dispatch-by-class vs CAMPD on-line gross (chp-export basis) + EIA-930
fuel-type net + EIA-923 monthly, all on the model's non-leap fixed-CST clock).
Mean MW, model − actual, after the coverage corrections below; positive =
model over-serves:

| window | h | model $ | actual $ | CC_REG | CT_PEAK | COAL | ST_GAS | storage net (mod vs meas) | West gas Δ |
|---|---|---|---|---|---|---|---|---|---|
| May shoulders h10–20 | 88 | 27.4 | 67.3 | **+1,469** | −1,183 | −589 | −784 | +242 vs ~+300 | +10 |
| May shoulders, δ<−5 | 62 | 29.5 | 87.7 | **+1,678** | −1,357 | −694 | −652 | +347 vs ~+380 | −53 |
| Nov, δ<−5 | 138 | 31.3 | 80.6 | **+425** | −1,234 | −851 | −766 | +748 vs +734 (930 BAT) | +294 |
| Apr, δ<−5 | 105 | 36.9 | 100.4 | **+913** | −477 | −2,418 | −243 | +568 vs n/a | −173 |

Demand matches EIA-930 within ±0.4% on every window; total thermal within
±0.9 GW. The residual is a pure **composition** shift: the model serves the
same load with cheap CC tranches where reality ran CT peakers (2.2–2.8 GW),
more coal, and Braunig-class steamers — the units that priced $57–100.

**The coverage-correction finding (a measurement artifact that was hiding the
owner).** The raw CAMPD class table showed CC_REGULAR +2,203 on the May
window; ~55% of that was the ACTUAL side being under-counted, not model
excess: (a) **four ERCOT CC plants have ZERO TX-CAMPD rows** — Kiamichi 55501
(OK-sited switchable, outside the TX state extract), Hidalgo 55545, Arthur Von
Rosenberg 7512, EG178 56233, ~2.65 GW — their real output (EIA-923) was being
scored as zero; (b) **V H Braunig (3612)** carries registry `plant_group`
OTHER, so `derive_ercot_rtolcap_forward._fleet_class_maps` drops it from every
class (its ~0.8 GW of real May steamer output vanished); (c) **W A Parish
gas-steam** (synthetic model id 34702) books its CAMPD gross entirely under
COAL 3470. Corrected, the true CC excess is +1,469/+1,678 (May), +425 (Nov),
+913 (Apr) — and the **non-CAMPD four alone carry +1,226/+1,381 (May) and
+1,443 (Apr)**. The headline case: **Hidalgo generated 0.0 MWh in all of
Apr+May 2024 (EIA-923) — a real two-month outage — while the model dispatches
it 434–499 MW on every target window**: the CAMPD-derived unit-outage overlay
is structurally blind to non-CEMS plants (no rows → no windows → flat
statistical availability), and Kiamichi's SPP-side hours are equally
invisible.

**Suspects adjudicated.**
* *Storage over-discharge (the strongest prior): REFUTED by measurement.* On
  May shoulders the model's batteries net +242 MW vs ~+300 MW measured RT
  battery output (EIA-930 pre-breakout OTH-proxy; ERCO folds batteries into
  OTH until Nov-2024); on the Nov under-priced subset model +748 vs measured
  BAT +734 — nearly exact; on Nov overall the model UNDER-discharges (−54 vs
  +411). The keeper's measured-AS stack already contains the fleet (awards
  2.9 GW on the May windows; measured DA energy award of the PWRSTR fleet on
  those afternoons: 18 MW). Not the owner, in any window.
* *West/Panhandle gas: REFUTED.* West-zone gas diff +10/−53/+294/−173 MW
  across the windows — order-of-magnitude below the CC term, no systematic
  sign. (The CC excess sits in North: +1.7 GW on May shoulders, of which
  Kiamichi ~1.0.)
* *Perfect-foresight ceiling: not the owner HERE.* The mix does not match, so
  the residual on these windows is not the structural-premium family (that
  stays the ledgered C3c winter-morning caveat, untouched).

**The marginal cross-check (the formation statement).** Model marginal on the
target hours = CC econ_high ($24–29 at 11.26× on $2.19 gas), at a CC dispatch
share of the MEASURED 60-Day-disclosure live HSL of **0.906 (88h) / 0.958
(62h subset)** — i.e. at reality's availability the model's CC demand nearly
exhausts the real live pool, whose measured offers price the 0.95–0.99 belt
at 18–22× ($39–48) and the top at 33.5× ($73): reality's $57–97 clearings sit
exactly there and in the CTs it actually ran (measured live CT 9.2 GW, real
dispatch 2.2–2.8 GW, model 1.0–1.8). The model never gets there for two
reasons in series: (1) the phantom +1.2–1.7 GW effective CC keeps its own
clearing share below the belt; (2) its offer stack is FLAT between econ_high
and the peak rungs — the empirical climb test (May daytimes, 341 h) shows the
model pricing $22–35 across 310/341 hours, $25.22 at exactly reality's gas
dispatch level (26 matched hours; actual there $41.98), and no May-daytime
hour at all in the $60–100 band. **Therefore the supply-mix fix ALONE cannot
form $67 — it must compose with the measured midcurve belt
(`ercot_offer_surface_midcurve_conditional`, built default-off in ERCOT-69),
which was probe-inert on the phantom base precisely because the phantom keeps
within-plant shares below its floors.** This closes the ERCOT-67 coupling
clause quantitatively: availability honesty and the offer belt are two halves
of one mechanism.

**Disposition (rules 1/13/14/24/26).** The owner is NAMED: the availability /
commitment basis of the CAMPD-invisible CC fleet (+1.2–1.7 GW effective on
the target windows), with covered-CC intensive creep second-order (+0.2–0.5)
and the coal/CT deficits endogenous to the too-low clearing. An admissible
measured fix EXISTS: the 60-Day DAM disclosure carries per-resource
`Resource Status` + HSL for EVERY ERCOT resource including the four blind
plants and the switchable Kiamichi — an ex-ante physical/market availability
declaration (same source family as the ERCOT-67 class-day series, finer
grain), passing the rule-13 test (forward year regenerates from the
statistical stack — the same G4 mode-aware seam as the CAMPD overlay);
EIA-923 monthly-zero months (Hidalgo Apr–May) equally ground discrete outage
windows. NOT admissible: any class haircut or monthly-level pin tuned to the
residual (rules 14/24). Successor lane chartered (ERCOT-71, §2 of the
handoff): per-plant measured availability for the blind plants (or the
disclosure-grain variant of `ercot_thermal_dam_availability`), composed with
the midcurve belt, adjudicated leg-wise on May/Nov/Apr + the ERCOT-67 summer
trade, full-span 2023–2025 + LOYO (rule 22) before any promotion. Two
derive-side coverage defects FILED (rule 23 — fixing them is a data-coverage
change, citable): (a) `_fleet_class_maps` drops OTHER-group plants (Braunig)
from every envelope/share derive, so the ERCOT-58/68 measured envelopes
under-count ST_GAS; (b) non-CAMPD ERCOT plants are absent from
`campd-unit-outages` and the envelope by construction. **Keeper UNCHANGED**
(`2026-07-15-ercot66-storage-rebasis`); nothing registered (single-year leg-0
reproduction is a rule-16 throwaway, deleted; no mechanism built, DOF ledger
untouched — zero new parameters).

**Ops.** One in-session solve (keeper leg 0 2024, ~8.7 min). The known
`prb_overrides`/`ercot_wtx` recorder warning surfaced as documented — not
chased. The ERCOT-69 calibration-log entry (413-blocked last session) merged
into `docs/calibration-log.md` from the handoff per its instruction.

---

## 2. ERCOT-71 charter sketch (the successor build lane)

**Thesis to build:** honest per-plant availability for the CAMPD-invisible
fleet + the measured midcurve offer belt, moving TOGETHER (leg-wise), form
the May/Nov/Apr moderate-tightness prices the keeper misses.

1. **Leg A — the availability blind spot (measured, per-plant).** Two
   admissible identifications, either or both:
   * Extend the 60-Day DAM disclosure availability derive
     (`ercot-thermal-dam-availability.csv`'s source) to per-plant grain for
     the non-CAMPD plants (Kiamichi, Hidalgo, AVR, EG178 + the non-CAMPD
     cogens): live HSL / `Resource Status` per resource-day. This also
     measures Kiamichi's switchable ERCOT-share directly (OFF in ERCOT COP
     when serving SPP).
   * EIA-923 monthly-zero months → discrete outage windows for non-CEMS
     plants (Hidalgo Apr–May 2024), same window semantics as
     `campd-unit-outages.csv`. Do NOT pin monthly LEVELS (outcome pin,
     rule 14) — zero-months are availability events; partial months are not
     windows.
   Both are backcast overlays behind the existing mode-aware seam
   (statistical stack is the forward analogue). Expect ~−1.2–1.5 GW effective
   CC on the target windows; ALONE this should move May only ~$2–5 (flat
   stack) — that is the expected leg-A result, not a failure.
2. **Leg B — composition with the midcurve belt.** Leg A +
   `ercot_offer_surface_midcurve_conditional=true` (ERCOT-69 build; re-derive
   unchanged). The phantom's removal pushes within-plant committed shares
   into the measured 0.95–0.99 belt on the shoulder afternoons; adjudicate
   whether May forms toward $57–97 without the Jan/Sep over-lifts ERCOT-69
   measured on the phantom base (the over-lift may itself shrink once the
   winter/high-net-load bins see honest availability).
3. **Watch the ERCOT-67 summer trade:** wholesale class-day availability
   adoption traded May for August. The per-plant/blind-spot-scoped leg A is
   surgical (does not touch the covered fleet's summer availability), which
   is the design reason to prefer it over flipping
   `ercot_thermal_dam_availability` wholesale; verify August windows hold
   (`_ercot66_summer_windows.py`).
4. **Gates:** full-span 2023–2025 one bundle (rule 16), LOYO for the
   composition (rule 22), D-2/D-4 attribution for any new floor-like
   mechanism (none expected — availability is not a floor), DOF ledger
   entries zero-DOF measured. Keeper promotion is the owner's.
5. **Also fix (citable data-coverage changes, rule 23):**
   `_fleet_class_maps` OTHER-group drop (Braunig) and the envelope's
   non-CAMPD hole — then re-derive the envelope/share tables and re-check the
   ERCOT-68 v3 realized-room identification on the corrected basis.

## 3. Reproduction

```
# leg 0 (rule-16 throwaway)
python scripts/probes/_ercot68_ladder_probe.py keeper --years 2024 --out-name ercot70_keeper_2024
python scripts/probes/_ercot63_c3_proxy.py ercot70_keeper_2024 --year 2024
python scripts/probes/_ercot68_anatomy.py ercot70_keeper_2024 --year 2024
# the decomposition (all tables in §1)
python scripts/probes/_ercot70_mix_decomp.py --bundle ercot70_keeper_2024 --year 2024
```

Sources: `data/raw/eia-930-hourly/ERCO hourly.parquet` (fuel-type net;
BAT breaks out Oct-2024, batteries live in OTH before), CAMPD TX extracts via
`market_sim.data.campd`, `data/raw/_processed-legacy/eia923_monthly_generation.parquet`,
`data/raw/ercot-thermal-dam-availability.csv` (measured class-day live HSL),
`60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2024_*.parquet` (PWRSTR DA
awards), `actual_lmp_hourly_ERCOT.parquet` (rt). All series indexed on the
model's non-leap fixed-CST 8760 clock (Feb-29 dropped).
