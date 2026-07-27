# NYISO CT_PEAKER: the class does not need a new reason to run — it needs its measured heat rate

**Session:** nyiso-88 (peaker commitment charter) · **Date:** 2026-07-27 ·
**Mode:** no-LP, scoring-side characterisation (rule 14 [R-ACCURATE])
**Premise:** `docs/FINDING-nyiso87-commitment-drag-2026-07-27.md` §4.3/§4b/§6,
`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §7, and the keeper
`2026-07-27-nyiso-87-cmeas-measured` open item (1).

---

## 0. Summary

nyiso-87 removed the owner-adjudicated-inaccurate h14-21 boxcar. CT_PEAKER's
diurnal **shape** became good (D-1 `profile_r` 0.88/0.93/0.95, `cv_ratio`
1.38/1.07/1.15) while its **level** collapsed to 0.46 TWh against a ~2.3 TWh
actual. The charter framed this as a **missing mechanism** — "with no floor,
nothing in the model gives a downstate GT a reason to start" — and offered three
directions: (a) an offline-quick-start non-spin product, (b) start-cost recovery
in the offer, (c) C3c price formation, with (c) to be tested first.

**All three are the wrong frame. The finding is a measured-input error.**

1. **(c) is refuted.** A maximally-generous peak-price uplift — the model's own
   diurnal swing stretched to the measured NYISO DA swing, for free, with no
   offsetting cost — recovers only **12.6 / 12.2 / 16.9 %** of the gap (§2).
2. **The real fleet is NOT running uneconomically.** Priced on the keeper's own
   delivered-gas seam, the real downstate peaker fleet earns an energy-weighted
   margin of **−$1.39 / +$5.82 / +$3.49 per MWh** over its own SRMC — an
   at-the-money marginal fleet, which is exactly what a peaker fleet should be
   (§3). There is no large non-energy obligation to discover, so direction (a)
   has nothing to explain and direction (b) points the wrong way (start-cost
   recovery *raises* an offer).
3. **The model overcharges that fleet by more than its entire margin.** The
   model prices NYISO downstate peakers at an **eGRID plant-average annual**
   heat rate of 11.05–11.23 MMBtu/MWh against a CAMPD unit-level **loaded** rate
   of 9.66–10.11 — a **9.3–15.7 %** overstatement worth **+$6.48 / +$6.70 /
   +$7.34 per MWh** at the keeper's own delivered gas (§4).

**The cost error exceeds the margin the fleet actually earns, in every year.**
An at-the-money fleet priced $6.5–7.3/MWh above its true SRMC never clears. That
is a rule-14 [R-ACCURATE] input defect with a measured replacement already on
disk, not a missing market mechanism — and it must be fixed before any new
mechanism is built on top of it (rule 1 [R-STRUCT]).

A **second, independent** measurement defect was found in the scoring benchmark
itself (§5): 6 NYISO gas plants that span more than one model class are
collapsed to a single class by an arbitrary alphabetical tiebreak, and the
payload silently drops the model dispatch of every non-winning class. It is
worth ~0.24 TWh on CT_PEAKER's actual but ±2.1–2.5 TWh on ST_GAS / ST_CHP /
CC_*, and it is cross-ISO.

Reproduce: `scripts/probes/nyiso88_peaker_price_coupling.py` (§2) and
`scripts/probes/nyiso88_peaker_economics.py` (§3–§4). No LP is solved; every
input is a committed artifact or a measured source.

---

## 1. A correction recorded up front

The first pass of §3 computed peaker SRMC from
`fuel.nyiso_downstate_ct_gas_premium` — the **superseded** monthly statewide EIA
N3050NY3 *firm* city-gate stand-in. The keeper does not price that: it sets
`nyiso_downstate_ct_gas_daily=True` / `nyiso_downstate_ct_gas_basis=False`, so a
downstate CT takes the curated per-zone daily index (Transco Z6 NY daily spot +
the measured LDC **non-firm transportation** rate, KEDNY SC-22 / KEDLI SC-19 —
nyiso-55, gap G-13).

The stand-in runs ~$1.5–2.3/MMBtu dearer, and dearest in exactly the summer
months peakers run. On it the fleet appeared to produce **66–92 %** of its
energy below SRMC at a margin of **−$24.16/MWh** — a spurious "the fleet runs
uneconomically" result that would have sent this session to build the non-spin
mechanism of direction (a). On the seam the keeper actually runs, the margin is
**−$1.39/+$5.82/+$3.49**. The probe now reads the keeper's seam directly and
documents why (`downstate_ct_gas_hourly`).

---

## 2. Direction (c) is refuted on the model's own offer surface

`nyiso88_peaker_price_coupling.py` reads the keeper's own P1 CT_PEAKER dispatch
against its own load-weighted internal price to recover the class's **revealed
offer curve** (running-max of dispatch by price bin — the LP's merit order read
off its solution, so it already embeds availability, min-gen and binding
commitment structure). That curve is then re-evaluated against a counterfactual
price series whose hour-of-day profile is stretched about its load-weighted mean
until the diurnal swing equals the measured NYISO DA swing.

The counterfactual is deliberately the most generous rendering of (c): perfect
peak/off-peak price formation, granted free, with no offsetting cost anywhere.
It is therefore an **upper bound** on what fixing price formation could buy.

| year | model TWh | actual TWh | gap | model swing | target swing | recovery | share of gap |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 0.46 | 2.52 | 2.06 | $9.16 | $22.5 | 0.26 | **12.6 %** |
| 2024 | 0.31 | 2.37 | 2.05 | $10.28 | $25.1 | 0.25 | **12.2 %** |
| 2025 | 1.28 | 3.08 | 1.79 | $19.06 | $43.3 | 0.30 | **16.9 %** |

The gap is not where a peak uplift can reach it: by the model's own price
distribution only **0.14–0.42 TWh** of it sits above the 90th price percentile,
while **1.05–1.22 TWh** sits in the p50–p90 belly.

C3c's own tail bounds this independently. The >$300 tail is 3/0/9 model hours
against 10/12/42 actual; even the full 2,634 MW fleet running every one of the
42 worst hours of 2025 is 0.11 TWh — under 7 % of that year's gap. **C3c cannot
be the peaker lane's mechanism**, and closing C3c will not close this.

---

## 3. The real fleet is a marginal, at-the-money fleet

`nyiso88_peaker_economics.py` restricts to **pure-CT plants** — every model unit
at the plant is `CT_PEAKER`, so no mixed steam/CC facility contaminates the
series — and prices them on the keeper's own per-zone delivered gas at their
CAMPD unit-level loaded heat rate, plus the fleet's own VOM.

| year | plants | capacity | actual TWh | DA when running | own SRMC | margin | % of energy below SRMC |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 18 | 2,739 MW | 1.88 | $43.41 | $44.80 | **−$1.39** | 68.1 % |
| 2024 | 18 | 2,739 MW | 1.76 | $53.96 | $48.13 | **+$5.82** | 52.2 % |
| 2025 | 17 | 2,722 MW | 2.22 | $85.73 | $82.24 | **+$3.49** | 49.6 % |

Roughly half the energy above its SRMC and half below, at a margin inside
±$6/MWh, in all three years. **That is the signature of a fleet dispatched on
energy economics at the margin** — not of a fleet held online by an obligation.

*Locational robustness.* The DA series is the 11-zone hub while the fleet sits
in NYC and Long Island. Measured directly from the raw 5-minute zonal RTD files
on disk (June and December 2023 — a summer and a winter sample), the premium
over the 11-zone mean is **+$1.23 (Zone J)** and **+$7.42 (Zone K)**. It moves
the margin in the fleet's favour and does not change the character of the
result.

*Consequence for the charter.* Direction (a) supposed the fleet runs for a
non-energy reason. It does not. Direction (b) supposed its offer must recover a
start over a short run — that makes the offer **higher**, moving the model
further from the actual. Both are answers to a question the measurement does not
pose. This also converges with nyiso-83, which built and tested the in-city
commitment obligation and measured **+0.11 TWh** on CT_PEAKER: the published
reserve ladder is not this class's driver.

---

## 4. The model overcharges the fleet by more than its whole margin

The model's non-ERCOT fleet carries an **eGRID plant-average annual** heat rate,
identical across every generator of a plant (E F Barrett's GT units and its
188 MW steam boilers share one 11.076 figure). Two things are wrong with that
for a peaker: an annual plant average is not the **loaded** rate that sets an
offer, and at a mixed facility it is not even the right technology's rate.

CAMPD unit-level gives the measured alternative directly — per unit, heat input
over gross load in hours at or above 80 % of that unit's p95 load:

| year | plants | model HR | measured loaded HR | ratio | delivered gas | **SRMC bias** | fleet margin |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 15 | 11.23 | 9.71 | 1.157 | $4.25 | **+$6.48** | −$1.39 |
| 2024 | 15 | 11.11 | 9.66 | 1.150 | $4.62 | **+$6.70** | +$5.82 |
| 2025 | 15 | 11.05 | 10.11 | 1.093 | $7.80 | **+$7.34** | +$3.49 |

**The bias exceeds the margin in every year.** A fleet that clears on ±$6/MWh,
charged $6.5–7.3/MWh too much, does not clear at all — which is the observed
collapse, without positing any missing mechanism.

The per-plant errors are not a uniform bias but **source noise**, in both
directions, which is why no single multiplier could stand in for the
measurement:

| plant | measured loaded HR | model HR | model / measured |
|---|--:|--:|--:|
| Bayswater Peaking Facility (55699) | 10.58 | 21.68 | **2.05×** |
| Port Jefferson (2517) | 9.46 | 12.01 | 1.27× |
| E F Barrett (2511) | 15.05 | 11.08 | **0.74×** |
| Bayonne Energy Center (56964) | 9.28 | 9.77 | 1.05× |

Bayswater at 21.68 MMBtu/MWh is not a physical simple-cycle heat rate at all.
Barrett at 0.74× is the mixed-facility blend pulling the GTs *down* toward the
steam average while pushing the steam *up*.

**Admissibility (rules 13/14).** A unit's loaded heat rate is a physical
characteristic measured from the same CAMPD unit-level source the repo already
uses for the nyiso-87 bridge's min-load fractions
(`derive_campd_gas_commitment_params.py`). It regenerates for a forward year and
responds to changed conditions (retrofits, new units carry design rates), so it
is rule-13 admissible as an input, and rule 14 requires preferring it to the
eGRID estimate it replaces. Nothing here is fitted to a residual.

**Do not expect this to close the gap by itself.** Scored against the *actual*
price, correcting the heat rate lifts the fleet's in-merit hour-share from
5.1 → 6.8 % (2023), 8.1 → 11.2 % (2024) and 12.6 → 15.4 % (2025) — a 25–33 %
relative gain, not 5×. The real fleet runs several times more hours than any
hourly SRMC screen implies, which is the ordinary signature of **day-ahead
commitment in multi-hour blocks** (measured NYISO CT run lengths: median 4 h,
mean 6.5–7.6 h, p90 14 h — `campd_ct_run_lengths_NYISO.csv`). The correct order
of work is rule 1's: fix the measured input first, re-measure, and only then ask
what commitment structure the *remaining* residual needs.

---

## 5. Second defect: the bench collapses multi-class plants by an alphabetical tiebreak

Independent of the above, and cross-ISO.

`render_calibration_html.py` builds the benchmark payload with

```python
for (code, klass), g in dm.groupby(["plant_code", "klass"], observed=True):
    mw_p[int(code)] = arr          # keyed by code alone — overwritten per class
    grp_p[int(code)] = str(klass)
```

Both dicts are keyed by `plant_code` while the loop iterates `(plant_code,
klass)` pairs, so for a plant spanning two model classes the **last** class in
groupby order wins — deterministic, but alphabetical. The plant's *entire* CEMS
actual is then attributed to that one class, while only that class's slice of
model dispatch survives in the payload.

Six NYISO gas plants (9.13 TWh of benched CEMS energy, 13.9 % of the ISO's
benched fossil) span more than one model class, and the bench group is the
alphabetically-last model class for **6 of 6**:

| plant | model classes (MW) | bench group | actual |
|---|---|---|--:|
| Ravenswood (2500) | ST_GAS 1,725 · CC_REGULAR 222 | ST_GAS | 2.850 TWh |
| East River (2493) | CT_CHP 306 · ST_CHP 310 | ST_CHP | 2.134 TWh |
| E F Barrett (2511) | CT_PEAKER 281 · ST_GAS 372 | ST_GAS | 1.526 TWh |
| Bethpage (50292) | CC_REGULAR 129 · CT_PEAKER 44 | **CT_PEAKER** | 0.631 TWh |
| Port Jefferson (2517) | ST_GAS 385 · CT_PEAKER 83 | ST_GAS | 0.400 TWh |
| S A Carlson (2682) | ST_GAS 45 · CT_PEAKER 42 | ST_GAS | 0.042 TWh |

CT_PEAKER is the class alphabetical order hurts most: it loses every CT/ST mix
and wins the one CC/CT mix — exactly backwards. Bethpage is a **combined cycle**
(EIA-923 dominant class CC_REGULAR at 74 %; CAMPD unit types: GT1/GT2/GT4
"Combined cycle", GT3 "Combustion turbine"), and 0.459 TWh of its output is
combined-cycle energy scored as peaker energy.

Splitting both sides at CAMPD `unitType` granularity gives the honest actual:

| class | committed bench | unit-level split | delta |
|---|--:|--:|--:|
| CC_CHP | 17.591 | 19.724 | +2.134 |
| CC_REGULAR | 31.002 | 33.469 | +2.468 |
| CT_PEAKER | 2.520 | **2.278** | −0.242 |
| ST_CHP | 2.134 | 0.000 | −2.134 |
| ST_GAS | 11.912 | 9.686 | −2.226 |

**Stated plainly so it is not overclaimed: this is only −0.24 TWh on CT_PEAKER
and does not explain that class's gap.** Its weight is on ST_GAS / ST_CHP /
CC_* (±2.1–2.5 TWh), where ST_GAS carries its own open item.

Exposure is cross-ISO — energy on multi-class plants as a share of benched
fossil: **NYISO 13.9 %, MISO 9.2 %, ERCOT 8.8 %, PJM 2.6 %, CAISO/NEISO 0.1 %**.
Bench parts are per-(ISO, year) files rewritten only when that ISO registers a
run, so a fix lands per lane rather than re-baselining every dashboard at once.
This is filed as a finding, not fixed here: it is a scorer change affecting every
ISO's D-1/C-class basis and belongs to its own lane with owner scoping.

---

## 6. What this session did **not** do, and why

* **No LP arm was registered.** A zero-delta keeper replay was started to
  regenerate the dispatch needed for both the control and any arm; it solved
  2023, then was **OOM-killed during 2024's persist** on this 15 GB container
  (rule 12's memory ceiling, reached here even at a single invocation). No
  bundle exists, so nothing is registered — reporting a run that did not
  complete would be worse than reporting none. Every number above is from
  committed artifacts and needs no solve.
* **No floor was re-armed.** The charter's hard constraint is honoured: nothing
  here proposes a windowed floor, a temperature boxcar, or a CT-scoped
  `reliability_floor` row.
* **No closed route was re-opened.** The NYCA/East spin gate and the J/K ladders
  stay closed and default-off; §3 removes the reason to revisit them for this
  class.

## 7. Recommended next step

1. **Build `scripts/data/derive_campd_ct_heat_rates.py`** — per-plant measured
   loaded heat rates for NYISO `CT_PEAKER` from CAMPD unit-level, frozen against
   residuals per rule 24 [R-FROZEN-DERIVE] (re-derives only when CAMPD updates),
   and wire it into the fleet build ahead of the eGRID plant-average. Register a
   single arm against a same-HEAD zero-delta control, all three years, one
   bundle (rules 16 + 12). Re-score C1 **and** C5a — the C1 margin is thin
   (−2.78 TWh against ±2.94) and 2025 CO2 is already +7.6 % against a +10 % band,
   and this arm adds gas volume.
2. **Re-measure the residual** after (1) before proposing any commitment
   mechanism, and judge it against the measured CT run-length distribution
   rather than against the volume gap.
3. **Scope the §5 bench fix** as its own cross-ISO lane.

Rule 1 applies throughout: the heat-rate correction is the accurate input and
stays whatever it does to the residual; if C3c or C1 degrade, that is a
discovered root cause elsewhere, not a reason to revert (rule 14).
