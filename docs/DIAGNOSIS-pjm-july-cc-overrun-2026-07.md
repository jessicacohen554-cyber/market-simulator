# DIAGNOSIS — PJM July gas "over-dispatch": temperature, gross-vs-net, and where the +3 TWh actually lives (2026-07-14)

**Charter:** confirm the mechanism behind the pjm-107 keeper's apparent July gas
over-generation (+3.1 / +3.8 / +2.9 TWh vs actual, 2023/24/25) before touching
`temp_dependent_derate` / `gt_ambient_derate` / a seasonal parasitic-load
correction. Owner framing: (1) were the over-run days HOT at the plants,
(2) is the parasitic-load (gross→net) haircut seasonal, (3) redo the
model-vs-actual comparison net-basis. No solve, no config flip — this session
is diagnostic only (rules 1/11/13/22 reviewed at the end).

**Verdict in one line:** the July "over-run" is NOT a missing-derate problem and
NOT a parasitic-load problem — it is (a) predominantly an **actuals-basis
artifact** (EIA-930 vs EIA-923 vs CAMPD-gross disagree by 1–3 TWh on PJM July
gas, and by 7–20 TWh annually), (b) a real but ~5× smaller **within-fleet
misallocation** (model over-runs mid-cost cyclers in AEP-Ohio / Central-PA /
ComEd and under-runs the Dominion belt, nights and mild days — a
cycling/congestion shape signature that nets to ≈ 0), and (c) in the one year
the C3c tail lives (2025), a real **+1.9 TWh July COAL over-dispatch** that is
the surviving over-supply lead for the missing summer tail. Temperature derate
stays refuted (third refutation, now July-specific and per-unit); the parasitic
haircut is measured flat (no seasonality); the reframing and next charters are
in §6–§7.

Probes (committed, no-LP): `scripts/probes/_pjm_july_cc_overrun_temp.py`,
`scripts/probes/_pjm_cc_netgross_bases.py`. Model side decoded from the
committed pjm-107 dashboard payload
(`frontend/data/backcast/runs/2026-07-14-pjm-107-gas-daily.js`, per-plant
hourly LP dispatch) — the container's dispatch parquets did not survive the
session boundary; the payload is byte-derived from them at render time.

---

## 0. Plumbing (the crosswalk the charter asked for)

There is no fuzzy name matching anywhere below. The repo's convention is
**EIA plant id == ORISPL** (`constants.py`: "EIA plant IDs are the EIA-860/923
ORIS codes used throughout the model"); `data/campd.py` joins CAMPD
`facilityId` → model `plant_id` directly, with the split-plant exceptions
registered in that module, and `data/raw/reference/master-plant-registry.csv`
is the loose index table. The 12 named plants resolve as:

| plant | EIA id / ORIS | model zone | EIA-860 nameplate MW |
|---|---|---|---|
| Guernsey | 62949 | AEP_Ohio | 2,055 |
| Greensville County | 59913 | Dominion | 1,773 |
| York Energy Center | 55524 | Central_PA | 1,449 |
| Hanging Rock | 55736 | AEP_Ohio | 1,430 |
| South Field | 60356 | AEP_Ohio | 1,210 |
| Brunswick County | 58260 | Dominion | 1,472 |
| Warren County | 55939 | Dominion | 1,472 |
| Lawrenceburg | 55502 | AEP_Ohio | 1,232 |
| New Covert | 55297 | AEP_Ohio | 1,176 |
| Jackson Generation | 62926 | ComEd | 1,289 |
| CPV Three Rivers | 63931 | ComEd | 1,300 |
| Hummel Station | 60368 | Central_PA | 1,194 |

Zone/group assignments are the model's own (`fleet.load_fleet_from_csv("PJM")`,
the pjm-95 probe pattern); temperatures are the model's own derate input series
(`eia_loader.iso_zone_tmax`, `data/raw/pjm-weather/pjm_zone_temp_daily.csv`).

## 1. Q1 — Were the over-run days hot? **No.**

Exact per-plant hourly model dispatch (payload) minus CAMPD hourly gross,
July, per day, crossed against the plant's own zone TMAX — the exact series
`temp_dependent_derate` would consume:

| July | corr(TMAX, daily over-run) | over-run share on ≥33 °C days | on ≥35 °C days | modal TMAX bin |
|---|---|---|---|---|
| 2023 | **−0.14** | 7.4 % | 1.2 % | 28–31 °C (50.8 %) |
| 2024 | **−0.09** | 20.4 % | 5.1 % | 28–31 °C (35.3 %) |
| 2025 | **−0.09** | 16.2 % | 0.3 % | 28–31 °C (38.1 %) |

The correlation is **negative** every year: the model over-runs *more* on
mild days. 30–50 % of each plant's July over-run MWh accrues **overnight
(hours 0–6)** — hours a hot-afternoon capability derate cannot touch by
construction. And on the ≥33 °C hours themselves, the same units demonstrate
0.96–1.06× their net-summer rating in CAMPD (max observed output; the pjm-95
rule-24 lower-bound test reproduced on exactly these plants) — the fleet
*delivers its rating on the hours the derate would cut it*, a third
confirmation of the pjm-95 refutation (ERCOT 2026-07-09, PJM fleet-wide
2026-07-10, PJM July-unit-specific here).

Two arithmetic facts make the temperature levers inert for this residual even
before the data:

* `temp_dependent_derate` for CC is **rescaled to be capacity-neutral on the
  Jun–Sep mean** (scenarios.py docstring) — it reshapes summer availability by
  temperature; it cannot remove July TWh. Flipping it cannot close a volume gap.
* `gt_ambient_derate` bites only on hours above its 35 °C reference. PJM zones
  log ~11–31 such day-maxima per July; at the physical CC slope (0.4 %/°C,
  1–3 °C excursions) the July energy effect is ~0.01–0.03 TWh — two orders of
  magnitude below the headline.

**Do not flip either flag for this residual.** (They remain available where
their physics is the point — hot-hour scarcity depth — but that case was
already refuted on PJM's own fleet capability envelope, and the C3c-2025 tail
hours the model does form are Jun/Jul *load* hours it already reaches.)

## 2. Q2 — Is the parasitic-load haircut seasonal? **No.**

Plant-month EIA-923 net ÷ CAMPD gross, all 65 model CC_REGULAR plants
(complete-CEMS reporters; capacity-weighted), 2023–2025 pooled:

* Monthly ratio band: **0.969–0.975 in every calendar month.**
* Jan 0.9727 vs Jul 0.9731 → summer extra haircut **−0.05 pp** (i.e. none);
  per-year Jan–Jul deltas −0.37 / +0.34 / −0.15 pp — noise around zero.
* DJF 0.9723 vs JJA 0.9720.

PJM CC parasitic load is ~2.7 % of gross, flat year-round, at every month's
sample of 156–173 plant-months. The static `parasitic_load_pct` treatment is
**correct**; there is no aux-cooling seasonality to model and no admissible
seasonal correction to build. (Hypothesis refuted cleanly — CC station load is
dominated by boiler-feed/condensate pumps and the cooling system's base draw,
not by an ambient-following increment visible at plant-month resolution.)

## 3. Q3 — The net-basis re-comparison, and what it exposed instead

Correcting CAMPD gross → net makes the per-plant gaps *bigger* (net actual is
~2.7 % lower), so gross-vs-net does **not** explain the York-type +15 pt CF
gaps. What the apples-to-apples exercise exposed instead is that the per-plant
*benchmark* was corrupted at six of the biggest apparent over-runners, in two
distinct ways:

**(a) CT-only CEMS reporting — benchmark understated ~⅓.** Ironwood (55337),
Hunterstown (55976), Allegheny 3-4-5 (55710): EIA-923 **net** = 1.45–1.59×
their CAMPD **gross** — physically impossible unless their CEMS submissions
carry only the combustion-turbine share of the block (steam-turbine MWh
missing; net/gross ≈ 1.5 is exactly the 2×1 signature). Against CAMPD these
three "over-run" ~630 GWh every July; against EIA-923 net the real deltas are
~+91 / +35 / +28 GWh (2025). **~0.5–0.6 TWh/July of the apparent over-run
evaporates.** Any per-plant capture/Δ-vs-CEMS diagnostic at these plants is
structurally unfair to the model until the bench flags them.

**(b) EIA-860 summer-capacity corruption — six plants, +972 MW phantom.**
New Covert (55297: generator-level "Summer Capacity" rows sum to **1,586 MW vs
1,176 MW nameplate** — block totals double-filed at component rows, +410 MW),
Keys (60302: plant total 766 MW filed on one unit plus NaN components the
loader nameplate-fills → fleet pmax 1,237 vs 830.6 nameplate, +406 MW), Camden
(10751: +50 MW), plus three smaller instances (56807 +69, 7153 +30, 55710 +7 —
probe block 3). Fleet-loaded pmax > plant nameplate is impossible; the
raw-basis fleet build carries **+972 MW of phantom CC**.
**Keeper-inert:** under the keeper's `cc_nameplate_summer_derate=True` the LP
capacity basis flips to nameplate and the corrupt ratio clamps at 1.0 (payload
confirms Covert dispatches ≤ 1,176 MW). But every flag-off configuration —
the **default**, other-ISO fleets through the same ISO-agnostic loader, and
any forecast run without the flag — carries the phantom MW. Latent data bug;
fix in §6.

**The honest named-plant table** (July, GWh net; model = LP grid dispatch from
the payload, actual = EIA-923 net; CF on nameplate):

| plant | 2023 Δ | 2024 Δ | 2025 Δ | 2025 CF m→a |
|---|---|---|---|---|
| York Energy | +134 | +142 | **+183** | 0.94 → 0.77 |
| Lawrenceburg | +74 | +104 | +132 | 0.95 → 0.80 |
| Hanging Rock | +90 | +90 | +101 | 0.94 → 0.84 |
| South Field | +111 | +55 | +94 | 0.99 → 0.88 |
| New Covert | +57 | +274 | +88 | 0.99 → 0.89 |
| CPV Three Rivers | +83 | +150 | +82 | 0.89 → 0.80 |
| Hummel | +93 | +140 | +79 | 0.90 → 0.81 |
| Jackson Gen | +20 | +73 | +4 | 0.90 → 0.89 |
| Guernsey | −18 | −19 | −86 | 0.75 → 0.80 |
| Greensville | **−204** | −117 | −58 | 0.86 → 0.90 |
| Brunswick Co | **−194** | −119 | −71 | 0.86 → 0.93 |
| Warren Co | −86 | −135 | −61 | 0.86 → 0.91 |
| **named-12 total** | **+159** | **+639** | **+487** | |

The "12 worst over-runners" net to +0.16 / +0.64 / +0.49 TWh — with the
over-runs (AEP-Ohio/Central-PA/ComEd mid-cost cyclers, flat where reality
two-shifts) largely offset by **under-runs at the Dominion belt** (Greensville
/ Brunswick / Warren run 0.90+ CF in reality; the model holds them at
0.86 and imports/redispatches elsewhere). That is a **merit/congestion
allocation** signature, not a capacity or ambient-physics one. Fleet-level D-1
passes (profile_r 0.95–0.98) precisely because these per-plant shape errors
net out in the class aggregate.

## 4. The basis reconciliation — where "+3 TWh every July" actually lives

July PJM gas, TWh, all bases measured this session:

| July | model (payload, all gas classes) | EIA-923 matched-grid (volErr `a`) | EIA-923 all-PJM-BA plants | EIA-930 NG | model −923 (matched `m`−`a`) | model −930 |
|---|---|---|---|---|---|---|
| 2023 | 41.36 | 40.59 | 41.63 | 39.63 | **+0.76** | +1.7 |
| 2024 | 42.52 | 41.17 | 42.33 | 39.37 | **+0.57** | +3.2 |
| 2025 | 42.37 | 42.08 | (38.87 — legacy 2025 vintage incomplete) | 40.66 | **+0.16** | +1.7 |

On the **plant-survey (EIA-923) basis the model's July gas is within
+0.2–0.8 TWh of actual** — and on fleet totals 2023/24 within ±0.3. The
+3 TWh-class headline is the model measured against **EIA-930**, which runs
1.0–3.0 TWh *below* EIA-923 on PJM July gas and 7–17 TWh below annually. The
two federal actuals sources **invert the sign** of the annual mix error: 2025
gas is −6.8 TWh (model UNDER) vs 923-matched but +13.4 (OVER) vs 930; 2025
coal is +7.7 OVER vs 923 but −1.7 UNDER vs 930. (The prior July aggregation's
exact numbers — `july_final.json` — did not survive the session container, but
they sit on the 930/CAMPD-gross side of this table; the payload/923/930
numbers here are reproducible from committed files.)

This is a known-pathology class the repo has precedent for (the PJM
interchange three-way meter disagreement boundary note, calibration-log
2026-07-10; `EIA930_NG_CELL_CORRUPT` for CAISO): 930 is the real-time BA
telemetry submission with its own fuel bucketing; 923 is the revised plant
census the model's plant-level scoring (volErr, class gates) already uses.
**Which series C1 should anchor to is an owner-level scoring question, not a
dispatch bug** — flagged in §7, not adjudicated here.

What survives as *real* July over-supply, on the consistent 923 basis:

| July | CC_REGULAR | CT_PEAKER | ST_GAS | gas total | COAL (BIT+PRB+WC) |
|---|---|---|---|---|---|
| 2023 | +1.03 | −0.69 | +0.30 | **+0.76** | −0.19 |
| 2024 | +1.67 | −0.41 | −0.73 | **+0.57** | +0.42 |
| 2025 | +0.15 | +0.13 | −0.23 | **+0.16** | **+1.90** |

* CC zonal decomposition (m−a, TWh): 2024 EMAAC **+1.05**, AEP_Ohio +0.50,
  Central_PA +0.32, ComEd +0.27 vs Dominion −0.53, SWMAAC −0.16; 2025
  Central_PA +0.41, AEP_Ohio +0.42, ComEd +0.21 vs SWMAAC **−0.64**, EMAAC
  −0.26, Dominion −0.12.
* **2025 — the C3c year — the real July over-supply is COAL, not gas**:
  +1.90 TWh (COAL_BIT +1.63: West_APS +0.85, AEP_Ohio +0.66, SWMAAC +0.36 vs
  Dominion −0.24), i.e. ~**2.5 GW of average phantom mid-merit supply in the
  scarcity month**. Part of the model-wide 2025 coal-vs-gas split error
  (annual coal +7.7 / gas −6.8 vs 923). That cushion, not a 3-TWh gas
  phantom, is the volume-side suspect for the missing summer half of the
  C3c-2025 tail (model 6 h vs actual 51 h).

## 5. Guardrail review (rules 1/11/13/22)

* **No solve, no config flip** — none run; everything above is measured from
  committed payloads + raw survey data (no-LP probes).
* **Temp derate (rule 13/24):** stays OUT. Third refutation; the July-specific
  evidence (negative TMAX correlation, overnight over-run, rating demonstrated
  at ≥33 °C) closes the owner's question #1 in the negative. Flipping it to
  chase this residual would be deleting capability the fleet measurably has
  (rule 1: right number, unreal mechanism).
* **Seasonal parasitic correction (rule 13):** would have been an admissible
  measurement fix, but the measurement says there is nothing to fix — the
  haircut is flat. Static `parasitic_load_pct` stands.
* **Rule 22:** 2023–2025 data only, throughout.

## 6. pjm-110 — the one mechanical fix this session confirms (Opus execution spec)

Small, admissible, and none of it tunes a residual. One solve cycle, all three
years, one bundle (rule 16). Label `pjm 110 bench-hygiene`.

**Leg A — EIA-860 CC summer-capacity consistency guard (fleet build, code).**
In the CC summer-capacity path (`fleet.cc_summer_capacity` and the
generator-level `net_summer_capacity_mw` pmax sum): where a plant's summed
summer capacity **exceeds** its summed nameplate, treat the summer figure as
corrupt component/total double-filing and reconcile to
`min(summer_sum, nameplate_sum)`, with a loader warning naming the plant.
Rule-15/14 basis: EIA-860's own schema defines summer capability ≤ nameplate;
the reconciled figure regenerates for any forward vintage and responds to
re-rates. The guard must act on the **fleet-loaded plant pmax sum** (the
Keys/Camden pattern hides behind NaN component rows the loader
nameplate-fills — raw 860 sums miss it). ISO-agnostic (the corruption is in
the shared loader's source); PJM instances (probe block 3): 55297 +410 MW,
60302 +406 MW, 56807 +69, 10751 +50, 7153 +30, 55710 +7 — **+972 MW**.
*Expected dispatch effect on the pjm-107 recipe: ≈ none* (the keeper's
`cc_nameplate_summer_derate=True` already clamps these three to nameplate) —
the fix protects the **default/flag-off path and forecast mode**. Gate A:
pjm-110 solve is within noise of pjm-107 on every scored metric (this is a
no-regression hygiene leg, not a fit-mover); a probe diff of the flag-OFF
fleet shows exactly −972 MW PJM CC and nothing else.

**Leg B — CT-only CEMS bench flag (scorer-side, no solve).** In the benchmark
builder (`render_calibration_html.py` bench assembly), detect plants whose
EIA-923 annual net > 1.1× CAMPD annual gross (a physical impossibility for a
complete CEMS record) and (a) exclude them from CAMPD-basis per-plant
capture/Δ heatmap gates, scoring them on their EIA-923 monthly row instead,
(b) print them in the bench provenance note. PJM instances: 55337, 55976,
55710. Gate B: pjm-107's committed scores re-render byte-identical except the
flagged plants' per-plant rows; no class gate flips by construction (volErr
already uses 923).

**Owner sign-offs requested with the bundle:** none beyond the standard keeper
swap decision — but see §7 first; the two follow-on charters are where the
C3c-relevant volume lives.

## 7. Chartered follow-ups (each needs its own session; NOT pjm-110)

1. **July-2025 coal conduct (+1.9 TWh in the scarcity month; annual 2025 coal
   +7.7 / gas −6.8 vs 923).** Why does the model's 2025 coal-gas split break
   toward coal — delivered-coal price vintage? Coal supply/stockpile conduct
   the take-or-pay + PRB sigmoid doesn't carry in 2025 conditions? This is the
   surviving volume-side C3c-summer lead: ~2.5 GW of phantom July mid-merit
   supply. (Complement, not alternative, to the owner-closed reserve
   opportunity-cost boundary from the pjm-107 cycle.)
2. **CC zonal misallocation / Dominion under-run.** The model persistently
   holds the Dominion CC belt 5–13 CF-points below reality in July while
   over-running AEP-Ohio/Central-PA/ComEd cyclers, with 2024-EMAAC (+1.05) the
   largest single cell; interchange remains r = −0.16 vs the tie-line record
   with the measured seam ladder already on. Trace whether the binding
   constraint is seam pricing, the zonal congestion surface, or Dominion-zone
   fuel cost, on the volErr zone-month cells.
3. **Per-plant diurnal cycling depth.** The over-runners are flat overnight
   where reality two-shifts (30–50 % of over-run in h0–6); the under-runners
   are the opposite. Class D-1 hides this by netting. A per-plant
   overnight-turndown shape metric (D-1p) would make the residual visible and
   gateable before any commitment-posture work is attempted (the ERCOT
   gas-commitment-bridge pattern is the eventual shape lever if PJM offer-floor
   evidence — the offer-corpus intake — supports it).
4. **C1 actuals-basis boundary note (owner).** Document the PJM 930-vs-923
   gas/coal divergence (this doc §4) alongside the interchange three-way note;
   decide whether C1's gas/coal rows should stay 930-anchored or move to the
   923 basis volErr already uses. Until then, cross-basis deltas (model-vs-930)
   should not seed volume charters without a 923 cross-check — this session is
   the case study.

## Pointers

* Keeper: `2026-07-14-pjm-107-gas-daily` (owner-adopted; run_config confirms
  `temp_dependent_derate=False`, `gt_ambient_derate=False`,
  `cc_nameplate_summer_derate=True`, `pjm_seam_measured_ladder=True`).
* Temp-derate refutation lineage: calibration-log 2026-07-10 (pjm-95 demotion,
  `scripts/probes/_pjm_temp_capability_envelope.py`); ERCOT closure 2026-07-09.
* C3c winter half: `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` Part C.
* Probes for this doc: `scripts/probes/_pjm_july_cc_overrun_temp.py`,
  `scripts/probes/_pjm_cc_netgross_bases.py`.
