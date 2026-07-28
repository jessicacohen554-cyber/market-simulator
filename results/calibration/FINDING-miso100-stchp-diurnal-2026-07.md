# FINDING miso-100 — the ST_CHP diurnal anti-correlation is a composition of two flat-by-construction representation choices plus a missing hour-grain temperature response; the measured wave is identified as ambient dry-bulb at r ≈ −0.96 with the repo's own committed ST condenser slope predicting its amplitude

**Lane:** characterization, no solve, no LP, no mechanism (rule 1 `[R-STRUCT]`
structural-fidelity lane; explicitly NOT gate-chasing — ST_CHP is D-1-ungated
and D-2-exempt, so no gate is at risk). **Keeper
`2026-07-27-miso-98b-sectormeasured` UNCHANGED.** Premise:
`docs/FINDING-bench-multiclass-collapse-2026-07-28.md` §0.5/§5/§6 — the
post-fix signal `profile_r` +0.45/+0.74/+0.58 → **−0.795/−0.751/−0.765**
(2023/24/25, committed `legitimacy_diagnostics.json` D-1 rows; reproduced
bit-exactly here from the corrected slice-keyed bench + the keeper payload).
No lever was tested; no mechanism-matrix cell changes (duty (b) not
triggered). Off-queue rationale: the §5.4 MISO queue targets C7 COAL_PRB /
C3b / C3a-2024 — this lane is the owner-scoped follow-up 1 of the collapse
FINDING §6, a shape-fidelity diagnosis, not a gate lever.

---

## 0. Summary

1. **The D-1 ST_CHP "class" statistic is effectively a one-refinery test.**
   Only 3 of the 9 CAMPD-benched ST_CHP entries carry CEMS hourly data
   (ExxonMobil Beaumont Refinery 50625, R S Nelson 1393 slice, New Ulm 2001);
   the other six — including Valley (WI) 275 MW and Spiritwood — are below
   the Part-75 reporting line (`nodata`). The paired actual is 0.93 / 0.88 /
   0.85 TWh, of which **Beaumont is 91 / 99 / 99 %**. The class's full
   EIA-923 actual is 5.2 / 5.5 / 3.9 TWh (~0.6–0.8 % of MISO load — under
   the rule-20 2 % materiality line in every year, which is *why* it is
   ungated).

2. **The measured actual has a small, persistent diurnal wave: peak
   h05–h08, trough h14–h16, amplitude 3–6.6 % of level, in winter AND
   summer** (Beaumont, all three years). It is not a large host-load-following
   swing — a continuous-process refinery host runs flat; the wave is the
   plant's *capability/output* breathing with ambient temperature.

3. **The model is flat by construction on every channel that carries the
   dominant plant, and its only remaining diurnal freedom is anti-phase.**
   Beaumont's grid slice is 100 % floor-pinned (flat `chp_steam_following`
   floor clipped to flat availability ⇒ byte-flat payload, per-plant
   `profile_r` = 0 by the constant-profile convention); its report-side BTM
   add-back is flat by design (correlation-invariant per plant). The *entire*
   class model hour-of-day signal is R S Nelson's ~2.5–10 GWh/yr of
   price-following economic dispatch (amp 1.6 / 3.7 / 6.3 MW, peaking
   h14–h18), which correlates with the class actual at **−0.795 / −0.751 /
   −0.740 by itself** — the class anti-correlation is this hump against
   Beaumont's temperature trough.

4. **The actual's wave is quantitatively identified as an ambient dry-bulb
   response.** Against a standard TMIN→TMAX diurnal interpolation (min h05,
   max h15) of the curated MISO-South daily weather, Beaumont's measured
   hour-of-day profile correlates at **r = −0.91 … −0.99 in every year and
   season**, and the repo's own committed condenser slope
   (`temp_derate_slope_st_gas` = 0.0054/°C, docs/parameter-citations) times
   the observed ~11 °C diurnal range predicts a ~6 % amplitude that brackets
   the observed 3–6.6 %. The wave persists in winter — the response has no
   hard 15 °C onset in the data.

5. **Why the model cannot show it today:** the temperature-derate machinery
   (`temp_dependent_derate`, OFF in the keeper; MISO matrix cell `U`) is fed
   by `iso_zone_tmax`, which **broadcasts daily TMAX flat within the day** —
   even armed, it reshapes day-to-day and seasonally but carries zero
   hour-of-day signal. No channel in the current representation can produce
   the measured wave.

6. **Proposed (NOT built): hour-grain diurnal temperature capability for the
   steam classes** — §7. Owner decides whether an arm lane opens.

## 1. What D-1's ST_CHP row actually measures

The corrected slice-keyed bench (`bench/MISO/<year>.json.gz`, keys via
`scripts/lib/bench_multiclass`) carries 9 ST_CHP entries; D-1 pairs the ones
with CEMS hourly (`campd`) against the keeper payload's per-plant model
series (`load_payload_plants`, flat CHP add-back included):

| entry | plant | npl MW | CAMPD hourly | actual TWh (2023/24/25) |
|---|---|--:|---|---|
| `50625:ST_CHP` | ExxonMobil Beaumont Refinery | 150 | yes | 0.846 / 0.869 / 0.840 |
| `1393:ST_CHP` | R S Nelson (slice) | 819 | yes (e923_monthly split) | 0.079 / 0.005 / 0.010 |
| `2001` | New Ulm | 78 | yes | ~0.000 / 0.000 / 0.002 |
| `1073:ST_CHP`, `4042`, `10328:ST_CHP`, `50240`, `55096:ST_CHP`, `56786` | Prairie Creek, Valley (WI), T B Simon, Purdue, Portside, Spiritwood | 19–275 | **no (`nodata`)** | 0.9–1.0 TWh combined (e923) |

The paired subset is ~17–24 % of the class's EIA-923 actual (5.2 / 5.5 /
3.9 TWh) and 91–99 % Beaumont. Every claim below about "the class actual
shape" is really a claim about one Gulf-coast refinery cogen — that is a
property of the benchmark's CEMS visibility, not a defect in the split fix
(the slice attribution behaved exactly as designed).

## 2. The two profiles

Committed D-1 rows (payload path, migrated diagnostics — reproduced exactly):

| year | profile_r | model offpeak CV | actual offpeak CV | cv_ratio |
|---|--:|--:|--:|--:|
| 2023 | −0.795 | 0.004 | 0.031 | 0.136 |
| 2024 | −0.751 | 0.010 | 0.010 | 1.070 |
| 2025 | −0.765 | 0.012 | 0.010 | 1.198 |

Hour-of-day means (2023, MW): actual rises overnight to a **h05–h08 peak
(~111)**, falls through the morning to a **h14–h16 trough (~100.5)**, recovers
in the evening. The model is **flat at ~110.6 with a hump to ~112.2 at
h14–h16** — the mirror image. 2024/25 identical in phase with the model hump
growing (peak h16–h18, +3.3 / +6.7 MW) as Nelson's economic dispatch grows.
Seasonal split of the actual (Beaumont): winter amp 2.9–4.8 MW, summer amp
4.0–6.4 MW, trough pinned at h15–h16 in both — larger in summer, present in
winter.

## 3. Attribution — which plants carry it

Per-plant, against the class actual profile (payload model side):

| plant | model diurnal amplitude (23/24/25, MW) | corr of its model profile vs class actual |
|---|---|---|
| Beaumont `50625:ST_CHP` | **0.00 / 0.00 / 0.00** (byte-flat) | 0 (constant) |
| R S Nelson `1393:ST_CHP` | 1.62 / 3.71 / 6.27 | **−0.795 / −0.751 / −0.740** |
| New Ulm `2001` | 0.00 / 0.00 / 0.45 | 0 / 0 / −0.903 |

* **Beaumont (the actual):** grid slice `ST_CHP_MISO-South_p50625_econ`
  41.6 MW pmax, `chp_pmin_cf` = 104.5 (p2 CAMPD gross CF > net nameplate),
  BTM 70 % (miso-98 sector-measured) ⇒ floor ≥ econ cap, `min_gen` avg
  36.2 MW = pmax × flat availability 0.87. **Zero dispatch freedom**; LP
  output = flat capability. Payload adds the 923 BTM hold-out back flat
  (~51 MW). Model = 87 MW dead flat vs a measured 97–106 MW series that
  breathes ±3 %.
* **Nelson (the model shape):** its ST_CHP grid tranche (42.5 MW, hr 12.65,
  BTM 90 %) carries **no floor** (`chp_pmin_cf` = None — the p2 statistic
  self-collapses on a cycler, correctly). The LP dispatches it a few GWh/yr
  in the afternoon price window; its payload `m_ann` (0.210 TWh, 2023) is
  ~99 % the flat BTM add-back (0.2075), i.e. the hump is ~2.5 GWh of energy.
  The *measured* Nelson slice (0.079 TWh, 2023) ran winter mornings (class
  actual winter amp 15 MW, peak h08), not summer afternoons — an aged Gulf
  steamer running on host/reliability events, not daily LMP chasing. The
  model's conduct is ordinary merchant logic on a trivial energy; it owns the
  class shape only because everything else is flat.

## 4. Root cause — the representation choices

The class model profile is the sum of three channels, each flat or
anti-phase by construction:

1. **Flat steam floor** (`chp_steam_following`, `MECH_CHP_STEAM`): level =
   annual/pooled statistic (`chp_pmin_cf` p2, × (1 − sector BTM share)),
   constant across all 8760 h; clipped to `pmax × availability`, which is
   also hour-flat (`gas_st_wefor_base_override` 0.1, seasonal outage
   overlays only — no diurnal component).
2. **Flat report-side BTM add-back** (`render_calibration_html`, deliberate
   and correlation-invariant per plant — but it flattens the *class*
   composite further by adding constant MW).
3. **Merchant residual freedom** (un-floored ST_CHP headroom) — follows
   afternoon LMP, i.e. anti-phase with a temperature-driven output trough.

And the one mechanism that *could* carry a diurnal capability signal cannot:
`temp_dependent_derate` (OFF here; `U` for MISO) consumes
`iso_zone_tmax` = **daily TMAX broadcast flat within-day**
(`data/eia930/weather.py`) — hour-of-day resolution does not exist anywhere
in the availability chain.

## 5. The temperature identification

Test: build the standard diurnal dry-bulb proxy (cosine bridge TMIN@h05 →
TMAX@h15) from the curated `data/clean/weather/MISO` daily series
(MISO-South), correlate hour-of-day profiles, and compare the amplitude
predicted by the committed slope (0.0054/°C) with the observed:

| year, window | corr(Beaumont profile, temp proxy) | diurnal range °C | predicted amp | observed amp |
|---|--:|--:|--:|--:|
| 2023 year / winter / summer | −0.964 / −0.966 / −0.912 | 11.3–11.5 | 6.1–6.2 % | 5.7 / 4.9 / 6.6 % |
| 2024 year / winter / summer | −0.963 / −0.945 / −0.958 | 10.7–11.1 | 5.8–6.0 % | 3.7 / 3.0 / 4.1 % |
| 2025 year / winter / summer | −0.984 / −0.975 / −0.987 | 10.5–11.3 | 5.7–6.1 % | 4.8 / 3.3 / 4.9 % |

Phase matches exactly (output trough at the temperature peak, h15); the
committed slope's predicted amplitude brackets/over-predicts modestly —
consistent with a condenser/steam-cycle response, and inconsistent with a
host-steam-demand story of any large amplitude (the wave survives winter,
tracks temperature, and a refinery host is continuous-process). A host
day-shift component cannot be excluded at the residual level, but the
temperature driver alone is quantitatively sufficient. Note the winter wave
means the *measured* response has no hard 15 °C onset — the current curve's
`max(0, T − 15)` hinge would zero it in winter; a MISO derivation must
measure its own onset (rule 24-style own-fleet duty, see §7).

## 6. Rule-19 enumeration — everything that already floors/fixes ST_CHP in the keeper

Floor-mechanism census on ST_CHP unit-hours (reconstructed keeper fleet, no
LP): **`{MECH_CHP_STEAM: 192,720}` — one mechanism, 22 floored tranches,
nothing else.** Specifically:

* `chp_steam_following=True` → the flat grid steam floor (class avg 77.8 MW,
  hour-flat). The only ST_CHP floor. D-2-exempt (`D2_EXEMPT_MECHS`);
  committed D-2 rows show `chp_steam` forced share 5.8 / 3.2 / 4.5 % of the
  class.
* Level-source variants OFF: `chp_export_floor_measured=False`,
  `chp_steam_floor_p25=False`.
* `st_gas_mustrun_p25_level=True` floors **ST_GAS only** (census confirms no
  second id on ST_CHP); reliability-floor limbs touch no ST_CHP unit-hour.
* Availability: `gas_st_wefor_base_override=0.1` (flat), seasonal/unit
  outage overlays (day-grain), `temp_dependent_derate=False`,
  `gt_ambient_derate=False`. No hour-of-day structure.
* Offers: ST_CHP band curve (mr 1.05 / mc 1.10 / econ 1.00 / peak 1.10),
  `gas_offer_margin=True` compression; heat rates per plant (Beaumont 5.68).
  **miso-99's `measured_chp_heat_rates` deliberately excludes ST_CHP**
  (back-pressure physics, FINDING-miso99 §1.3) — no interaction with the
  in-flight arms.
* BTM hold-out: miso-98 sector-measured `chp_btm_pct` (Beaumont 70, Nelson
  90, Valley/Spiritwood 35).

So a diurnal-shape fix is not a *new* floor and must not be one (rule 19
`[R-ONE-MECH]`): the existing floor already clips to
`pmax × availability`, so an availability-grain refinement propagates to
every floored cogen automatically, with no second mechanism.

## 7. Proposed fix (NOT built) — owner decides whether an arm lane opens

**Hour-grain diurnal temperature capability for the steam classes: feed the
existing temperature-derate curve an hourly dry-bulb series interpolated
from the already-curated daily TMIN/TMAX (the §5 proxy), instead of
TMAX-flat.** Concretely: a diurnal interpolation in
`iso_zone_tmax` (or a parallel hourly loader), consumed by the
`temp_dependent_derate` ST leg — scoped to the steam classes for the MISO
arm, with a MISO-measured slope and onset (the §5 winter evidence says the
onset is below 15 °C; the committed hinge would erase the winter wave).

* **Rule-13 forward story:** driver = zone ambient dry-bulb — a physical
  input exogenous to the market, already curated per zone-year, pinned by
  weather-year in forecast mode; the capability response regenerates for any
  forward year and responds to changed conditions. Zero conduct terms; the
  slope is a cited physical constant validated against (not fitted to) CEMS
  conduct.
* **Rule 19:** no new floor — the `MECH_CHP_STEAM` clip carries the shape to
  the pinned cogens; unfloored units just see an hour-varying pmax.
* **Rule 17:** window is driver-defined (hours above onset), amplitude
  bounded by slope × diurnal range.
* **Matrix discipline:** `temp_dependent_derate` MISO cell is **`U`** — not
  an adjudicated R/I/G retest. miso-90's inert verdict was the
  `gt_ambient_derate` GT increment (different mechanism, different classes).
  **Caution carried:** pjm-95 refuted the committed slopes on PJM's own
  CAMPD — a MISO arm must derive/validate slope and onset on MISO (or
  MISO-South) CAMPD conduct before arming, per rule 25 `[R-ISO-SCOPE]`, and
  its matrix cell updates in the arm session (duty (b)).
* **Honest expected effect, stated in advance:** the lever puts the correct
  wave on the floored slices (Beaumont grid slice ~1.8 MW amplitude), but
  the report add-back stays flat and Nelson's anti-phase hump (1.6–6.3 MW)
  persists, so **the scored class `profile_r` may stay negative in 2024–25
  even with the physics fixed** — the statistic composites a shape channel
  the lever does not own. That is not grounds to widen the lever (rule 1: a
  structurally-correct mechanism is not judged by the residual). If the
  owner wants the *statistic* moved as well, the second, separable question
  is Nelson's ST_CHP slice conduct (a start-economics/commitment question on
  a trivial 2–10 GWh energy, or a fleet-classification review of whether
  `1393`'s gas steamers belong in ST_CHP at all — the collapse FINDING §6.2
  fleet-classification lane), which should be its own decision, not a rider.
* **Materiality, stated plainly:** ST_CHP is ~0.6–0.8 % of MISO load and the
  D-1 pairing is one refinery. The case for the arm is structural fidelity
  (rule 1) plus the fact that the same missing hour-grain temperature input
  flattens **every** floored steam cogen in **every** ISO (CAISO's CC_CHP
  steam fleet is 0.65–0.76 GW); the case against is that no gate anywhere is
  at risk. This FINDING takes no position beyond recording both.

## 8. DO-NOT-REDO / verification

* The bench slice attribution is NOT the defect — reproduced the committed
  D-1 rows bit-exactly from the migrated artifacts (payload path); the
  anti-correlation is real model-vs-meter, not scorer plumbing.
* Do not re-derive the "actual swings with host demand" premise: measured,
  the wave is temperature-phase (r ≈ −0.96), small (3–6.6 %), and survives
  winter; there is no large host-following diurnal swing at the CEMS-visible
  MISO ST_CHP fleet.
* Do not arm `temp_dependent_derate` for MISO as-is: (a) its input is
  day-flat — it cannot produce the wave; (b) its 15 °C hinge contradicts the
  measured winter response; (c) pjm-95's own-fleet refutation makes the
  committed slopes non-transferable (rule 25).
* Do not stack a shape fix as a new floor mechanism on ST_CHP
  (`MECH_CHP_STEAM` is the only floor; rule 19).
* Nelson `1393` ST_CHP slice: `chp_pmin_cf`=None is correct conduct
  self-targeting (cycler ⇒ no floor), not a bug; its bench npl 819 vs fleet
  grid 42.5 MW reflects the 90 % sector BTM hold-out plus the slice-npl
  family proration — flagged to the fleet-classification follow-up, not
  changed here.
* Analysis scripts: session scratchpad (`stchp_char.py`, `stchp_shape2.py`,
  `stchp_fleet3/4.py`, `temp_test.py`); inputs were exclusively committed
  artifacts + the no-LP `reconstruct_bundle_fleet` path. Years 2023–2025
  only; quarantine untouched; no solve, no registration, no matrix cell
  change.
