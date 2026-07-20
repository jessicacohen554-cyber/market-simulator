# FINDING (caiso-106): the state-conditioned intertie conduct is MEASURED — the EVENING exhaustion ceiling is year-stable and admissible (an owner ask is drafted), the BELLY surplus-collapse is real and directionally unanimous but NOT year-stable on any CAISO-observable state (needs a west-wide observable; held back)

**Session 2026-07-20 (CAISO-106 — executing the caiso-105 intertie-elasticity
re-charter, derive-first, measurement-only): keeper `2026-07-19-caiso-102-hourfix`
(NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}) UNCHANGED; no mechanism armed, no
calibration leg registered.** Instrument (committed):
`scripts/probes/_caiso106_intertie_elasticity.py` — the state-conditioned
intertie measurement, pure raw-data (EIA-930 CISO interchange + WECC hub DA
LMP + CA actual LMP + EIA-930 net-load), NO solve, NO clean-data dependency.

## 0. What caiso-105 handed to this session

FINDING-caiso105 landed BOTH open λ-ladder residuals on ONE locus — the
model's WECC intertie supply is hub-anchored and too ELASTIC in both
directions (belly imports too deep at hub prices, propping λ ABOVE the
surplus-collapsed RT; evening supplies the margin at hub-equalized prices,
holding λ BELOW the hub-separated RT). The re-charter: MEASURE the
state-conditioned intertie conduct (belly surplus depth/direction incl. the
export side; evening depth exhaustion vs the hubs) BEFORE proposing any LP
form — rule 1: the eventual input must be a measured depth conditioned on an
observable, forward-reproducible state, NEVER a fitted throttle/haircut.

## 1. Method

Per year, on the model clock (interval-beginning, non-leap 8760), all series
raw:
* corridor net import — EIA-930 CISO BA-to-BA interchange per corridor
  (`WECC_PNW`, `WECC_DSW`) and TOTAL (negative = export), via
  `derive_caiso_import_tranches.corridor_net_import` (the SAME series that
  grounds every caiso-82/87/93/94 clean-depth derivation).
* hub DA LMP — MALIN / PALOVRDE (`hub_prices`; NaN in the 2023 Jan-Feb OASIS
  gap, masked).
* CA RT / DA LMP — `actual_lmp_hourly_CAISO.parquet`.
* net-load — EIA-930 CISO demand − solar − wind (the observable surplus /
  tightness state the model computes internally).

Two conditionings: (i) year-relative net-load QUINTILES within each window,
(ii) FIXED net-load GW bands (absolute thresholds — the same physical system
state in every year and forward). Estimation-stage honesty gates: caiso-81/86/87
standard (CV ≤ 0.20 across years, LOYO mean-of-others ≤ 25 %; near a zero
crossing the belly gate uses an absolute ±750 MW spread — a ratio CV explodes
at the import↔export sign change).

## 2. EVENING (hod 17-21): the measured intertie EXHAUSTS — year-stable, admissible

Measured TOTAL net import saturates and even BACKS OFF as CAISO tightens; it is
NOT the elastic hub-priced backstop the model treats it as. Fixed-band p50/p95
(MW), all PASS:

| net-load band (GW) | p50 2023/24/25 | CV | p95 2023/24/25 | CV |
|---|---|---|---|---|
| [10,15) | 2290/3276/3774 | 0.20 | 4398/5583/6440 | 0.15 |
| [15,20) | 3244/4309/4510 | 0.14 | 6229/7008/6644 | 0.05 |
| [20,25) | 5124/5084/5437 | 0.03 | 7752/7580/8584 | 0.06 |
| [25,30) | 5130/5169/5338 | 0.02 | 7169/7586/8573 | 0.08 |
| [30,45) (tightest) | 4199/4558/4502 | 0.04 | 6883/6973/6644 | 0.02 |

The signature: net import climbs to a plateau of **~5.1-5.4 GW p50 / ~7.6-8.6
GW p95 around net-load 20-30 GW, then DECLINES to ~4.5 GW p50 / ~6.6-7.0 GW
p95 in the tightest band [30,45)** — the West is ramping/tight at CAISO's
sunset peak too, so the import margin is exhausted, not elastic. The
year-relative tightest-quintile p95 ceiling is 7,055/6,875/7,555 MW (CV 0.040,
LOYO ≤ 7.8 % — PASS). This is exactly the missing rung behind FINDING-caiso103
§1 ("model λ sits 8-40 $ BELOW the measured hubs; actual RT clears at/above the
hubs"): the import cannot grow to fill the evening margin, so reality's price
climbs to the domestic rung while the model's hub-equalized import holds λ
down. **Admissible — a measured, year-stable, forward-reproducible exhaustion
envelope. The owner ask below proposes it.**

## 3. BELLY (hod 10-14): the surplus-collapse/EXPORT reversal is real and unanimous but NOT year-stable on any CAISO-observable state — HELD BACK

Direction is decisive and consistent: as CAISO drops into deep midday surplus
the corridor REVERSES to net EXPORT. Deepest net-load quintile (B5) TOTAL net
import mean −2078/−2207/−1174 MW, export share 91/92/80 %; conditioned on
hub-negative (PALO < 0) TOTAL mean −1030/−1124/+168, export 73/70/45 %, with
measured RT < 0 in 66/78/65 % of those hours. The model instead imports
+3.3-4.2 GW at hub-linked prices in exactly its worst over-price hours
(FINDING-caiso105 §4) — the over-import props the belly λ ABOVE a
surplus-collapsed real market.

BUT the DEPTH is NOT year-stable on any CAISO-observable state tested:
* year-relative deepest-quintile p95 ceiling 844/182/1030 MW — **CV 0.531,
  LOYO 28-416 % (FAIL)**.
* FIXED-band p50 response: [10,15) GW → 1058/2206/2517 (CV 0.33); [20,25) GW →
  3613/2492/6082 (CV 0.37) — **FAIL**. Even the response FUNCTION at a fixed
  system state drifts year-to-year.

Root cause (structural, not noise): the belly corridor conduct depends on the
**west-wide** surplus state (WECC solar/hydro), which CAISO net-load does not
observe — the same CA net-load pairs with a flush West (CA exports) or a
tighter West (CA imports). Compounded by non-stationarity: 2025 belly net-load
reaches −7.2 GW (more solar / EDAM), so a static per-year depth is
inadmissible. The evening arm escapes this because at CAISO's sunset the West
is correlated-tight (system-wide ramp), so CAISO tightness DOES proxy the
neighbor state — which is why the evening envelope is stable and the belly one
is not.

**Verdict (rule 1 / derive-first):** the belly is NOT ready. No LP form is
proposed on an unstable measurement. The belly needs a west-wide observable
(the Palo Verde / Malin hub LEVEL is the natural candidate — it already prices
the neighbor state) before a depth-and-direction structure can be responsibly
built. Filed as a follow-on measurement lane, NOT in this ask.

## 4. The owner ask (drafted this session)

`docs/handoffs/caiso-106-evening-intertie-exhaustion-ask-2026-07-20.md` —
a MEASURED, net-load-conditioned EVENING import-exhaustion ceiling on the
CAISO import node (the class of the MISO/PJM/NEISO measured deliverability
envelopes and the caiso-87/93/94 measured depths), with pre-registered
estimation + solve gates (both windows, all 3 years, one bundle; LOYO
structural scoring before promotion). PENDING owner ruling — nothing built or
solved.

## 5. Model-side binding check (single-year 2024 diagnostic)

<!-- FILLED AFTER THE 2024 REPRO SOLVE — model evening/belly TOTAL import vs
the measured ceiling; the "does the ceiling bind" number. -->

## 6. Session artifacts

- Probe committed: `_caiso106_intertie_elasticity.py` (the measurement + gates).
- Single-year diagnostic solve driver `_caiso106_binding_2024.py` (keeper-recipe
  repro restricted to 2024, un-registered per the FINDING-caiso92b protocol —
  the owner-gate applies to NEW-mechanism solves, not to reproducing the keeper).
- DAM-outage intake completion (caiso-105 handoff §2): capacity-permitting;
  crosswalk `data/raw/reference/caiso-dam-resource-crosswalk.csv` is committed.
- #2546 ($5 battery_dispatch_adder fallback delete + re-gate): untouched,
  remains a dedicated-session item.
