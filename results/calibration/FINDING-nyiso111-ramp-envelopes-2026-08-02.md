# FINDING — nyiso-111: the cross-ISO transfer sweep — `temp_dependent_derate` and `hydro_ror_split` REFUSED ex-ante on NYISO's own data, `ramp_envelopes` pre-registered and solved

**Date:** 2026-08-02 · **Scope:** NYISO, 2023–2025 · **Keeper under test:**
`2026-08-01-nyiso109-zonal-margin-anchor` (bundle
`results/calibration/nyiso109_zonalanchor_B`) · **Pre-registration:**
`PREREG-nyiso111-ramp-envelopes-2026-08-02.md` (committed and pushed before any
arm solved).

---

## §1 — where NYISO stood, and why this session went to the transfer candidates

nyiso-110 closed the peak half's dominant component: the missing everyday
reserve-price formation is not formable in an hourly LP at NYISO under current
rules, the flag-only spin-online arm solved INERT by its own K3 rule, and
`diurnal_price_amplitude` NYISO moved **O → G**. That left the §5.5 lever queue
with **no admissible peak-half lever** and only three named re-open routes: the
owner amplitude-criterion call, an owner-funded reserve-offer/sub-hourly intake,
and item 8 (the `hydro_ror_split` Robert Moses classifier review).

So this session did what rule 28 `[R-MECH-MATRIX]` §4 is for: it went to the
**cross-ISO transfer candidates** — the matrix cells where NYISO reads `U` and
another ISO reads `K` — and adjudicated the three that are live at NYISO. Two
die before a solve is spent. Both die on **NYISO's own measurement**, never on
analogy (rule 25 `[R-ISO-SCOPE]`), which is the only way a transfer refusal is
worth recording.

| candidate | elsewhere | NYISO before | NYISO after | spent |
|---|---|---|---|---|
| `temp_dependent_derate` | CAISO / MISO / NEISO `K`, PJM `R` | `U` | **`G`** | no solve |
| `hydro_ror_split` (queue item 8) | CAISO `K` | `U` | **`G`** | no solve |
| `ramp_envelopes` (`ramp_limits`) | PJM `K` (pjm-140) | `U` | see §4 | pre-registered A/B |

## §2 — `temp_dependent_derate`: NYISO's own conduct does not identify the slope

The mechanism is a keeper in three ISOs, and MISO's own route (miso-101) is the
one this had to follow: **derive the slope from the target ISO's fleet**, because
pjm-95 refuted the committed literature values on PJM's CAMPD and MISO's own
measurement landed ~5× below them. `derive_campd_temp_derate_params.py --iso
NYISO` over NY CAMPD 2023–2025 was run, and it **fails on four independent
grounds, any one decisive**:

| # | check | MISO (the ISO that promoted it) | NYISO |
|---|---|---|---|
| a | identifiable plants | 6 CEMS-identifiable cogens | **2 of 15 candidates** (East River NYC, Nissequogue LI) |
| b | class parameter | +0.00141/°C (a loss) | **−0.00745/°C — capability RISING with temperature** |
| c | pinned-plant premise | cogens pinned at capability | East River loading ratio **0.5995** (dispatch freedom); the near-pinned plant (Nissequogue, 0.8025) measures **−0.000086 at r = 0.006** — no response at all |
| d | phase validation | best lag **0 h** (confirms the anchors) | best lag **−5 h** (r = +0.289 vs +0.088 at lag 0) |

The onset scan reproduces (b) rather than rescuing it — the within-day slope is
mildly positive (a loss) below 15 °C and turns **negative** above it
(−0.0048 / −0.0110 / −0.0107 per °C in the 15–20 / 20–25 / 25–40 °C bins, with
*positive* r). A gas turbine cannot gain output as ambient temperature rises;
what the estimator is reading is NYC's air-conditioning **dispatch** shape, and
(d) is the tell — a physical ambient response is contemporaneous, a 5-hour lead
is a load shape. Functional-form sensitivity is 3.6× (cosine −0.00348 vs
triangular −0.01243), which on its own would bar a level claim.

**Verdict: REFUSED on identification (cell `U → G`), not rejected on fit.** No
NYISO instrument identifies the response; rule 25 forbids importing the
literature slopes; rule 21 forbids picking one by hand. Artifacts:
`data/raw/_processed-legacy/campd_temp_derate_params_NYISO{,_onset,_phase}.csv`.

*Reported, not acted on:* the same measurement says nothing about whether NY's
gas fleet has an ambient response — only that **CEMS cogen conduct cannot
measure it here**. A future intake with an actual capability instrument (unit
DMNC test results, or a plant pinned at capability) would be a new
identification and could re-open the cell.

## §3 — `hydro_ror_split` (queue item 8): the classifier review, answered and falsified

Item 8 has been blocked since nyiso-92 on one question — what the EHA hybrid
label `Run-of-river/Peaking` means for **Robert Moses Niagara**. The answer does
not need the treaty schedule, because NY hydro's own metered output settles it.

**The partition.** The committed `curate_hydro_plant_modes` rule 1 (Peaking /
Intermediate Peaking → shapeable; every other label, hybrids included → flat)
applied to EHA FY2024 restricted to NYISO's own BA:

| EHA `Mode` | plants | MW | share | committed rule |
|---|--:|--:|--:|---|
| Run-of-river/Peaking | 9 | 2,471.4 | 52.8 % | flat-pinned |
| Peaking | 24 | 1,180.6 | 25.2 % | shapeable |
| Run-of-river | 70 | 477.7 | 10.2 % | flat-pinned |
| Run-of-river/Upstream Peaking | 11 | 151.4 | 3.2 % | flat-pinned |
| Intermediate Peaking | 3 | 81.0 | 1.7 % | shapeable |
| Reregulating | 3 | 17.0 | 0.4 % | flat-pinned |
| Canal/Conduit | 3 | 15.1 | 0.3 % | flat-pinned |
| **total** | **167** | **4,682.0** | | **73.1 % flat-pinned** |

Robert Moses Niagara alone is 2,429.1 MW = **51.9 %** of the fleet.

**The falsification.** Under the arm a flat-pinned plant is held at its own
measured monthly water (`min_gen == availability cap == budget[g,m]/hours[m]`),
so it contributes **exactly zero** to the fleet's diurnal swing. The model's
achievable hydro swing is therefore bounded above by the shapeable subset's
nameplate, **1,261.6 MW** — and NY hydro's own measured swing exceeds that bound
in every year:

| year | measured hod mean-profile swing | ÷ bound | measured median-DAY range | ÷ bound |
|---|--:|--:|--:|--:|
| 2023 | 1,291.9 MW | **1.02×** | 1,496 MW | **1.19×** |
| 2024 | 1,396.8 MW | **1.11×** | 1,495 MW | **1.19×** |
| 2025 | 1,792.2 MW | **1.42×** | 1,929 MW | **1.53×** |

(EIA-930 `NYIS` `NG: WAT`, local time, zero-dropout screened. `NG: WAT` is
conventional-only for this BA — nyiso-107 re-verified NYISO's absence from
`EIA930_PS_FOLDED_INTO_WAT` — so Lewiston's 240 MW and Blenheim-Gilboa's
1,000 MW of pumped storage are **not** in the series and cannot be the source of
the swing.)

**The label was never the problem; the reading of it was.** EHA itself records
the Niagara project's peaking machinery as a **separate plant** — Lewiston, EIA
2692, `Mode = Peaking`, `PS_MW` 240, `Water = Niagara River` — alongside Robert
Moses Niagara (EIA 2693, `Run-of-river/Peaking`, `CH_MW` 2,429.1). The hybrid
label therefore describes the **powerhouse's hydraulics**, not the project's
shapeability, and rule 1's gloss — *"a reregulating/RoR powerhouse cannot chase
price whatever its upstream neighbours do"* — is a CAISO-reviewed reading that
NY's own metered hydro falsifies. The treaty scenic-flow schedule the queue
entry asked for would bound *seasonal daytime diversion*; it cannot restore the
1.3–1.9 GW of within-day swing the flat pin deletes, so it cannot rescue the
transfer.

**Direction is wrong too, and the real defect is an order of magnitude
smaller.** nyiso-110's E3 over-peak-shave is confirmed here by an independent
construction — but it is modest:

| year | model hod swing | measured | model peak h17–19 | measured | excess |
|---|--:|--:|--:|--:|--:|
| 2023 | 1,507 MW | 1,195 MW | 3,868.4 | 3,575.6 | **+292.8 MW** |
| 2024 | 1,541 | 1,292 | 3,909.0 | 3,667.1 | **+241.9** |
| 2025 | 1,721 | 1,593 | 3,740.2 | 3,536.1 | **+204.1** |

Phase is correct (model peak h18/h19/h19 against measured h19) and annual
volumes are pinned to 4 dp. Removing 3.4 GW of shaping capability to correct
~250 MW of over-peaking is not a repair — it is a 13× overshoot on top of a
falsified premise.

**Verdict: REFUSED ex-ante (cell `U → G`), queue item 8 CLOSED.** The successor
is a **bounded** within-day shaping constraint — a Lewiston-class
reservoir-energy bound — which is a new mechanism with its own charter and its
own identification, never this transfer. Probe:
`scripts/probes/_nyiso111_hydro_ror_split_screen.py` →
`results/calibration/_nyiso111_hydro_ror_split_screen.json`.

## §4 — `ramp_envelopes`: the pjm-140 transfer, pre-registered and solved

*(filled in below once the A/B completed — see §5.)*

## §5 — A/B result

*(pending)*

## §6 — governance record and DO-NOT-REDO

*(pending)*
