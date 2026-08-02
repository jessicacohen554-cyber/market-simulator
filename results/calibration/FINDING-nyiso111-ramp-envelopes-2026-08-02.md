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

## §4 — `ramp_envelopes`: the pjm-140 transfer, pre-registered, solved, PROMOTED KEEPER

**The lever.** `ScenarioConfig.ramp_limits = True` — the plant-group hourly
ramp-envelope rows. Matrix row `ramp_envelopes`, NYISO cell `U`; PJM keeper
since pjm-140, never tested at NYISO. **Zero new DOF, no code change, no new
field, no PJM parameter imported** (rule 25): the artifact is derived from
NYISO's own CAMPD conduct in this session — `derive_campd_ramp_envelopes.py
--iso NYISO`, **77 rows / 48 well-observed plants**, measured max 1-hour
up-move fractions **CC median 0.49 × pmax (p90 0.82), ST 0.42 (p90 0.47),
CT 0.92 (p90 0.94)**. The bound is the **MAX** observed move, never a quantile,
so it can only remove transitions the real fleet never performed.

**The structural claim, which is the case for the arm.** With the flag off the
NYISO LP asserts that every thermal plant can move from any output to any other
in one hour — and the model acted on it.

**The pre-check honoured pjm-140's all-ISO lesson instead of rediscovering it.**
The class-aggregate test is reported **uninformative** (it fires in 1 hour of
26,280); the bound-against-the-bound test is the one quoted, measured on the
keeper's own per-plant dispatch with groups and envelopes taken from the live
loader:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| enveloped groups / capacity | 62 / 21,809 MW | 62 / 21,815 MW | 62 / 21,815 MW |
| transitions crossing the envelope | **5,226 (0.96 %)** | **6,819 (1.26 %)** | **4,057 (0.75 %)** |
| infeasible ramping | **225,117 MWh** | **291,437 MWh** | **274,134 MWh** |

PJM's superseded keeper crossed in 0.393 / 0.463 / 0.319 % carrying 555,882 /
587,079 / 536,940 MWh/yr — so NYISO's crossing **rate is 2.1–3.0× PJM's**, and
~6× PJM's relative to each fleet's own energy.

## §5 — A/B result: every pre-registered gate passes

Control `2026-08-02-nyiso111-control-zerodelta` / arm
`2026-08-02-nyiso111-ramp-envelopes`, both `[2023, 2024, 2025]` in one bundle
(rule 16). Scorer: `scripts/probes/_nyiso111_ramp_envelopes_ab.py` →
`results/calibration/_nyiso111_ramp_envelopes_ab.json`.

**Construction (K1–K6), all PASS:**

- **K1** exactly one config delta: `ramp_limits` `false → true`.
- **K2 control integrity on the STRICT BYTE basis — 0.0 MW** max class-hour
  delta against the committed nyiso-109 keeper in **all three years**. The A/B
  is unconfounded, and the solve-path commits that landed on main since that
  keeper (pjm-146's RGGI adder, caiso-155/156/157, ercot-150, and the
  `pipeline/year.py` + `input_completeness` changes) are **measured** NYISO-inert
  rather than assumed so.
- **K3** liveness: 62 enveloped groups, 21,809–21,815 MW, every year.
- **K4** artifact provenance: the frozen derive's own output at this HEAD.
- **K5** span `[2023, 2024, 2025]` both arms; the holdout spend freeze is ACTIVE
  and untouched (rule 22).
- **K6 effectiveness:** infeasible ramping **225,117 → 3,888 (−98.27 %)**,
  **291,437 → 4,717 (−98.38 %)**, **274,134 → 7,062 (−97.42 %)** — against a
  pre-registered floor of 70 %, and better than pjm-140's −90.8 / −89.1 /
  −84.6 %. The residual is **by design**: the availability-edge widening is the
  row's only slack.

**Kills (P1–P5), none fires:**

| gate | control | arm |
|---|---|---|
| **P1** C3a (±10 % band) | +7.508 / −0.547 / −9.640 % | **+7.501 / −0.599 / −9.657 %** — in band all years, ≤ 0.06 pp of movement |
| **P2** C1 | 14/14 all-class, 10/10 free-class | **14/14, 10/10** |
| **P3** C3c (>$300 h) | 3 / 0 / 7 | **3 / 0 / 7 — bit-unchanged** (actual 10 / 12 / 42) |
| **P4** C7 / C8 | PASS | **PASS / PASS** |
| **P5** slack, dump | 0.0 / 0.0 | **0.0 / 0.0** every zone-hour |

**Determination: CALIBRATED-WITH-CAVEATS**, identical to the superseded keeper —
C1/C2/C3a/C3b/C4/C6/C7/C8 all PASS, C3c the sole ledgered caveat.

**The price effect is NEAR-INERT, exactly as §3 of the pre-registration
declared.** That is not a disappointment to be explained away; it is pjm-140's
all-ISO finding reproduced on NYISO's own fleet — **a MAX-based envelope is a
correctness bound, not a price lever** — and the pre-registration committed to
it in advance so the null could not be re-narrated afterwards. No part of the
promotion rests on gate movement.

**PROMOTED KEEPER** under the standing structural-integrity standard (rule 1
`[R-STRUCT]` / rule 14 `[R-ACCURATE]`), the same ground pjm-140 was promoted on,
and per the pre-registration's own §7 promotion rule (all K pass, no P fires,
infeasible ramping ≥ 70 % down). NYISO is the **second ISO** to carry
`ramp_limits=True` and the **first transfer** of the mechanism. DOF ledger 27 →
28 entries with `n_residual` **unchanged at 6**.

## §6 — governance record and DO-NOT-REDO

Rule 28 `[R-MECH-MATRIX]` duties discharged in this session: `ramp_envelopes`
NYISO `U → K` with the full measurement in the note and the header keeper stamp
refreshed; `temp_dependent_derate` NYISO `U → G`; `hydro_ror_split` NYISO
`U → G`; and a **new row created** for `nysdec_peaker_rule_availability`, which
had none at all — a rule 28(c) hygiene gap on a solve-affecting field.

**DO-NOT-REDO:**

1. **The ramp envelope may not be tuned** (PREREG §6, carried from pjm-140 §5):
   no quantile swap, no tightening, no scaling, no per-class override, no
   re-derivation against a residual. There is no second version of this lever —
   a *binding* ramp representation would be a different mechanism with its own
   charter.
2. **`temp_dependent_derate` is closed at NYISO on identification**, not on
   fit. Re-opening needs a genuinely new capability instrument (unit DMNC test
   results, or a plant pinned at capability), not a re-run of the CEMS cogen
   estimator.
3. **`hydro_ror_split` is closed at NYISO on falsification.** The successor is
   a *bounded* within-day shaping constraint (a Lewiston-class reservoir-energy
   bound) under its own charter — never this transfer, and not rescued by the
   Niagara treaty schedule.
4. The **C3c frontier declaration (nyiso-104b) is untouched**: C3c is
   bit-unchanged across this A/B, so no C3c evidence moved and no caveat slot is
   spent. `diurnal_price_amplitude` NYISO stays `G` (nyiso-110); this arm makes
   no amplitude claim.
