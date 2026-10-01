# FINDING (caiso-109, P0 ECONOMIC-VS-PHYSICAL): the gas under-dispatch is ECONOMIC, not physical — but the chartered lever (firm $28/$48 rung) is REFUTED on two counts (pinned AND not the volume culprit). The over-import is the BELLY/daytime clean-import DEPTH (+2.5 GW), a defect caiso-106/107 already localized and whose CA-observable derivation caiso-107 already refuted. No mechanism armed; keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.

**Session 2026-07-21 (CAISO-109 — P0 diagnosis, NO SOLVE: model & actual gas
hourly reconstructed from committed artifacts only). This is the P0 the charter
required BEFORE any P1 import build. P1 is CONDITIONAL on an owner ask + grant on
a specific form (rule 1 / derive-first); the charter's proposed form (firm-rung
reprice/derate) is refuted here, so P1 as chartered is not executed — an
owner-ask on the refined lever is raised instead.**

Keeper reproduces: `.venv/bin/python scripts/calibration_verdict.py --run-id
2026-07-19-caiso-102-hourfix` → NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}.

## 0. What P0 was asked to settle

caiso-108 attributed the three failing gates (C3c scarcity tail, C4 gas hourly,
C5a CO2-LOAD) to ONE root: the model over-imports ~6–10 TWh/yr and
under-dispatches gas, a net-import VOLUME substitution. caiso-109 P0: decide
**economic or physical** — does the LP *choose* imports over CA gas (economic),
or *can't* dispatch more gas (physical, gas at its availability ceiling)? Then
**adjudicate the pin state** before any price form, because
`caiso_firm_import_selfschedule=True` is live in the keeper.

All measurements below are from **committed artifacts only** — the keeper's own
per-plant model dispatch (`plants[].m`, b64 CF%), the CAISO CEMS bench
(`plants[].campd`), and the near-identical keeper-proxy bundle `caiso104_m1_B`
(gas within 0.25 % of the keeper: 60.73/54.52/46.35 vs 60.57/54.43/46.20 TWh) for
the hourly LMP + total-import series the keeper payload does not carry. No solve.
Instrument: `scripts/probes/_caiso109_econ_vs_physical.py`.

## 1. VERDICT — ECONOMIC. Physical is ruled out on the bytes.

Gas fleet dispatch vs ceiling, in the hours where model gas < actual (CEMS) gas:

| year | under-disp hrs | model gas peak / nameplate | under-hrs model gas mean | under-hrs at >90 % of peak (pinned) | reality (CEMS) ran gas | under-hrs LMP < cheapest CCGT MC |
|---|---|---|---|---|---|---|
| 2023 | 5738 (66 %) | 19.4 / 26.2 GW (26 % headroom) | 6.1 GW | **0.4 %** | **1.31×** the model | 59 % |
| 2024 | 6130 (70 %) | 18.9 / 26.2 GW (28 % headroom) | 5.7 GW | **0.2 %** | **1.27×** the model | 37 % |
| 2025 | 5834 (67 %) | 18.1 / 26.1 GW (31 % headroom) | 4.8 GW | **0.0 %** | **1.30×** the model | 41 % |

- **Gas is never at its ceiling.** Model gas peaks at 18–19 GW against 26 GW of
  CEMS-covered nameplate (26–31 % headroom even at the *annual* peak), and in the
  under-dispatched hours it is at >90 % of its own peak in **0.0–0.4 %** of them.
- **Reality proves the capacity was there.** In those same hours CEMS ran the gas
  fleet **1.27–1.31× higher** than the model — the physical availability existed;
  the model declined it.
- **The clearing price sits below the gas offer.** In 37–66 % of the
  under-dispatched hours the model LMP is below the *cheapest* CA CCGT marginal
  cost, so gas is priced out at the margin — economic, not capacity-bound. The
  under-dispatch is uniform across ~66–70 % of hours (not peak-clipping), matching
  the caiso-108 C4 signature (r 0.84–0.91 good, NRMSE level low).

**Physical branch is closed. The LP CHOSE imports over available CA gas.**

## 2. The substitution is ~1:1 gas↔import ON THE CEMS BASIS (the caiso-108 −13.66 TWh was the corrupted 930 NG cell)

Reconstructing the gas actual on the CEMS grid basis (`gas_cems_grid +
gas_cogen_grid`, the same basis C4/C5a score on) instead of the corrupted
EIA-930 NG cell:

| year | gas model | gas actual (CEMS) | gas gap | net-import over | solar model/actual |
|---|---|---|---|---|---|
| 2023 | 60.57 | 68.74 | **−8.2** | **+8.28** | 39.6 / 37.2 |
| 2024 | 54.43 | 61.04 | **−6.6** | **+9.65** | 47.2 / 44.6 |
| 2025 | 46.20 | 51.60 | **−5.4** | **+6.35** | 52.7 / 49.7 |

The gas under-dispatch (−8.2/−6.6/−5.4) ≈ the net-import over-dispatch
(+8.3/+9.7/+6.4) — **~1:1**. (caiso-108 quoted gas −13.66 in 2023 by differencing
against the 930 NG actual 74.23; on the honest CEMS actual 68.74 the gap is −8.2,
which matches the import over almost exactly.) Wind and nuclear are ≈flat; solar
is model-*over* by 2.5–3 TWh — so the excess import displaces **gas, not solar**
(the belly imports are not curtailing solar; the model runs *more* solar than
reality). Closing the ~8 TWh over-import recovers the ~8 TWh of gas → closes C5a
(the caiso-108 CO2 arithmetic).

## 3. PIN STATE — the firm rung is PINNED (offer-price byte-inert) AND is NOT the volume culprit

`caiso_firm_import_selfschedule=True` is live: `inject_caiso_firm_import_self
schedule` floors both firm tranches' `min_gen` at their full shaped
`pmax × availability`. At `min_gen == pmax × availability` the block can never be
marginal — its $28/$48 ladder price is inert bookkeeping. **An offer-price change
on the firm rung is byte-inert** (the charter's KILL condition, confirmed).

But the firm rung is not the over-import source either. Decomposing model import
into the pinned firm floor (`shape × firm_total × (1−eford)`, eford 0.02) and the
economic layer above it:

| year | firm floor (pinned) | model import | actual import | firm floor / actual | over-import |
|---|---|---|---|---|---|
| 2023 | 19.9 TWh (2.28 GW) | 37.1 | 28.9 | 69 % | +8.2 |
| 2024 | 28.9 TWh (3.30 GW) | 42.1 | 32.4 | 89 % | +9.7 |
| 2025 | 28.9 TWh (3.30 GW) | 42.5 | 36.2 | 80 % | +6.3 |

The firm floor is only **69–89 % of actual imports**, correctly shaped (it backs
off midday — the caiso-73 measured shape), and **does not over-import**. A
firm-floor *derate* (the charter's fallback availability lever) would deepen the
evening/overnight under-import while leaving the belly over-import untouched — the
**wrong** lever. Both the firm-rung price form and the firm-floor availability form
are dead.

## 4. WHERE the over-import lives — the BELLY/daytime economic clean-import DEPTH

Over-import by hour-of-day window (model − actual, GW), and the economic layer
(import above the pinned firm floor):

| year | overnight (22–6) | belly (10–15) | evening (16–21) | belly gas gap (model<actual) |
|---|---|---|---|---|
| 2023 | +0.45 | **+2.20** | −0.06 | model −1.2 GW midday |
| 2024 | +0.59 | **+2.52** | −0.03 | model −1.2 GW midday |
| 2025 | +0.14 | **+2.10** | −0.33 | model −1.0 GW midday |

- The over-import is **belly/daytime-concentrated** (+2.1 to +2.5 GW at h8–15),
  ≈0 overnight, and slightly **negative (under-import) in the evening**.
- It sits **above the pinned firm floor** (which is low midday): the economic
  import layer runs +2.4 to +2.7 GW in the belly vs actual ≈0.5 GW.
- The armed belly supply is the **clean-depth tranches** — daytime-clean
  (caiso-94, capability **4994/5563/5770 MW**), surplus-clean (caiso-87),
  overnight-clean (caiso-93) — priced at the **raw measured hub with EF 0 (zero
  carbon)**. Midday, when the hub is low, a zero-carbon import undercuts CA gas
  (which additionally pays the $28–35/ton CARB adder), so the depth floods in and
  de-commits ~1.0–1.2 GW of midday gas (belly gas gap) plus displaces gas across
  the annual energy balance.

## 5. This is caiso-106/107's belly defect — and its CA-observable derivation is ALREADY refuted

caiso-106 localized a +2.6 GW belly over-import; caiso-107 LANE-2 then tried to
re-derive the belly depth on CA **price** observables (net-load p50 CV 0.33–0.37,
PaloVerde hub LEVEL CV 0.49–1.62, hub−CA basis CV 0.71–0.89) — **every one fails
year-stability**. caiso-107 §2's root cause: the CA belly transfer depends on the
**full west-wide balance (WECC solar + hydro + load)**, which no single CA
observable summarizes; the hub LEVEL prices the neighbor's *marginal energy*, not
the *surplus QUANTITY* that sets how much CA can import. **caiso-107 tested price
observables and refuted them; it did not test a west-wide surplus QUANTITY
observable** — that is the one un-refuted lever class.

## 6. Verdict + what P1 can and cannot be

**P0 verdict:** ECONOMIC (physical closed). The ~8 TWh/yr over-import ≈ the
~8 TWh/yr gas under-dispatch (CEMS basis) and drives C5a/C4/C3c. The
over-import is the **belly/daytime clean-import depth**, not the firm rung.

**Refuted / DO-NOT-REDO lever forms (carried forward):**
- Firm-rung **offer-price** reprice — byte-inert (rung pinned, §3). KILL.
- Firm-floor **availability derate** — firm floor is 69–89 % of actual and
  backs off midday; derating deepens the evening/overnight under-import and
  misses the belly (§3). Wrong lever.
- Belly-depth re-derivation on a CA **price** observable (net-load / hub level /
  hub−CA basis) — caiso-107 L2, every scalar fails year-stability. DO-NOT-REDO.
- Any residual-fitted throttle/haircut/adder on the depth (rule 1/23/25).

**Un-refuted honest lever classes (the owner-ask, §7):**
- **(A) West-wide surplus QUANTITY constraint** on the daytime/surplus
  clean-import capability — the depth shrinks when a measured WECC-side surplus
  quantity (neighbor-BA solar penetration / net-export headroom, EIA-930) says
  the whole West is correlated-saturated. Structural (rule 1), forward-
  regenerable (WECC solar is a forward driver), and it is precisely the
  observable class caiso-107 flagged as untested. Scope: a new mechanism +
  likely a WECC-neighbor EIA-930 generation intake.
- **(B) Midday gas commitment / min-load** — the complementary gas-side view:
  reality keeps ~1.0–1.2 GW more CA gas online midday (CHP must-run + CCGT
  min-load bridging the evening ramp) than the model; committing it structurally
  (rule 12) leaves less belly room for imports. Risk: C8 forced-energy budget;
  overlaps the existing `caiso_ra_mustoffer`.

## 7. Owner-ask (raised in-session; no mechanism armed pending grant)

The chartered firm-rung lever family is refuted. Which direction for P1 —
(A) build the west-wide surplus-quantity depth constraint, (B) the midday
gas-commitment floor, or (C) file P0 and re-charter the west-wide-surplus
representation as its own structural charter (caiso-110)? Per derive-first, no
form is armed without a grant on a specific LP construction. If granted, P1 is a
single-delta A/B vs a fresh same-machine `caiso102_repro_A`, all three years one
bundle, gated on C5a CO2 → 0 / C4 NRMSE < 0.30 / C3c up, with C3a+C3b held PASS
and rule-22 leave-one-year-out before any promotion.

## 8. Session artifacts

- No solve, no bundle, no mechanism, nothing registered. Keeper
  `2026-07-19-caiso-102-hourfix` UNCHANGED.
- Reproduces from committed artifacts only:
  `scripts/probes/_caiso109_econ_vs_physical.py` (§1/§2/§4 — payload+bench+proxy)
  and `scripts/calibration_verdict.py --run-id 2026-07-19-caiso-102-hourfix`
  (the fail set). No new probe solve needed — the model's own hourly per-plant
  dispatch is in the keeper payload; the CEMS actual is in the committed bench.
