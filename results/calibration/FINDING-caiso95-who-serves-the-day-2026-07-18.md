# FINDING (caiso-95): WHO SERVES THE DAY — the C5a gas under-production decomposed against the metered fleet; the CC half is a LATE AFTERNOON RE-COMMITMENT (the model starts its evening CCs ~3 h after reality, an under-commitment concentrated in hod 13–17, NOT the belly), the CT_PEAKER half is the EVENING SUPPLY-STACK COMPOSITION (the model over-imports the evening by ~2 TWh/yr and its λ never reaches the CT rung — no floor is admissible, caiso-91b stands), CT_CHP is a LEVEL defect of the existing steam floor, and ST_GAS is a 2023-only final-year-OTC residual — four components, four different owners; charter asks at the end, NO new mechanism built or solved

**Session 2026-07-18 (CAISO-95 — the caiso-94 promotion's chartered successor
lane: C5a CC-underproduction root cause). Derive-first: the ONLY LP run was the
same-machine repro of the PROMOTED caiso-94 keeper recipe
(`scripts/probes/_caiso95_repro_A.py` → gitignored `caiso95_repro_A`,
un-registered per the FINDING-caiso92b same-machine protocol; recipe-identical,
no new mechanism, reproduces the keeper to ≤0.02 TWh/class — CC_REGULAR
48.88/44.58/36.19 vs the keeper's 48.86/44.57/36.19). NO new-mechanism solve;
keeper unchanged (caiso-94); nothing registered. Script:
`scripts/probes/_caiso_who_serves_day.py` (the hod 6–21 mirror of the frozen
`_caiso_who_serves_night.py`, plus a commitment-vs-dispatch decomposition, run
detector threshold 5 % — the RA-bridge's own `run_threshold_frac`). Data:
committed loaders only — CAMPD facility CEMS `CA_{2023,2024,2025}.parquet`
(grossLoad, co2Mass; LA-Basin ORISPL crosswalk), EIA-930 CISO hourly, the
committed bench artifacts (`frontend/data/backcast/bench/CAISO/{y}.json.gz`,
classFull/eGRID/intensities).**

## 1. The lane's question

The caiso-94 promotion accepted C5a CO2 deepening CAVEAT→FAIL
(−13.3/−11.2/−16.5 % vs eGRID) because the EF-0 daytime clean import displaces
in-state CC gas — a surfaced root cause (rule 11), never a reason to throttle a
measured structure (rule 1). The lane asks: is the model's gas under-production
**UNDER-COMMITMENT** (fewer CC/CT online than the metered fleet — fix at
availability/commitment) or **UNDER-DISPATCH** (units online but out-competed —
fix at the stack), per class, and what already floors each class (rule 19)?

## 2. The C5a bridge — where the missing tons actually are (full-plant classFull basis)

Class energy gaps (model − measured EIA-923 classFull, TWh) × bench eGRID
intensities (t/MWh), vs the scored C5a miss:

| component (Mt CO2) | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR (−2.96/−1.41/−4.40 TWh × 0.399) | −1.18 | −0.56 | −1.76 |
| CT_PEAKER (−3.18/−3.70/−2.15 TWh × 0.52–0.55) | −1.74 | −1.99 | −1.13 |
| CT_CHP (−1.84/−1.76/−1.08 TWh × 0.32–0.33) | −0.60 | −0.57 | −0.34 |
| ST_GAS (−1.13/+0.17/−0.05 TWh × 0.59–0.60) | −0.68 | +0.10 | −0.03 |
| CC_CHP (+0.71/+0.16/−0.66 TWh × 0.34) | +0.24 | +0.06 | −0.23 |
| **sum** | **−3.96** | **−2.96** | **−3.49** |
| **scored C5a gap** (−13.3/−11.2/−16.5 % of 30.386/26.982/23.645) | −4.04 | −3.02 | −3.90 |

The class-energy gaps explain the C5a miss essentially in full (residual ≤0.4 Mt
= COAL/OTHER_FOSSIL/rounding) — **C5a is a dispatch-energy problem, not an
emission-rate problem.** And the composition overturns the lane's framing:
**CT_PEAKER is the largest single component in 2023 (44 %) and 2024 (66 %);
CC_REGULAR leads only in 2025 (45 %).** The "separate CT lane" is in fact the
bigger half of C5a across the span. (The caiso-94 import itself added
≈ −0.9/−1.4/−1.3 Mt via the CC displacement — the pre-existing gap was already
−10.1/−5.2/−10.4 %.)

## 3. CC_REGULAR — mixed, and the commitment half is the AFTERNOON, not the belly

Day-window (hod 6–21) decomposition, CEMS-visible plants, common capacity basis
(E = online-cap-hours × loading; ΔE = ΔOH × L_cems + OH_model × ΔL):

| year | ΔE day (TWh) | commitment part | dispatch part | ΔE night |
|---|---|---|---|---|
| 2023 | −2.09 | −1.50 | −0.59 | −0.59 |
| 2024 | −1.26 | −0.49 | −0.77 | −0.25 |
| 2025 | −2.21 | −1.26 | −0.96 | +0.30 |

Where the commitment deficit lives (online-capacity hod profile, GW):

- **Belly core (hod 10–14): NO deficit.** Model online CC ≈ CEMS (2025:
  4.7 vs 4.4–4.5 GW; 2023 model is HIGHER, 7.2–7.3 vs 6.5–6.8). The RA
  must-offer bridge is doing its job through the trough — model min-load share
  of on-hours (<40 % load) exceeds measured (0.44 vs 0.31 in 2023).
- **Afternoon re-commitment (hod 13–17): the whole gap.** The metered fleet
  brings capacity back online through the early afternoon — 2025 CEMS online
  4.9 → 5.7 → 6.9 → 7.7 → 8.0 GW across hod 13–17 while the model sits at
  4.7 → 4.7 → 4.5 → 4.6 GW and jumps to 8.0 only at hod 18. 2023 same shape
  (CEMS 7.7/9.0/10.5/11.0 vs model 7.3/7.5/7.9/9.2 over 13–16).
- **The start-time histogram is decisive.** Measured CC run-starts peak at
  hod 13–15 (1.2–1.8 starts/day); the model's peak at hod 17–18 (2.3–3.5/day)
  — **the model starts its evening units ~3 hours after reality**, and does
  ~2× the total daily starts (16 vs 8.6/day in 2023 — the classic
  no-startup-decision LP over-cycling, incl. phantom morning starts at hod 4–6
  reality doesn't do).
- The night side is flat-to-over (+0.30 TWh 2025) and the model's evening MW
  runs ABOVE measured (hod 18–21, e.g. 2023: 8,405–8,441 vs 7,758–7,889 avg
  MW) — the late-started units then over-serve the peak.

**Verdict (lane question a, CC): ~55–60 % under-commitment, and it is
specifically the afternoon startup-positioning window (hod 13–17), not the
belly; ~40 % under-dispatch (loading-when-on 0.58 vs 0.59–0.61), owned by
import-volume competition (§5).** Physical driver of the missing structure: a
real CC started for the evening peak fires hours early (hot-start-to-load
trajectory + DAM operating-day positioning); the continuous-variable LP pays no
startup and materializes capacity exactly at the ramp hour.

**Lane question (b) — the belly interplay resolves cleanly:** the commitment
fix window (13–17) is disjoint from the belly core (10–14), and added min-load
energy in hours where hub-priced imports are marginal displaces import VOLUME
at an unchanged hub-set λ — it adds gas (CO2 ↑) without re-pricing the belly
down. Where the model over-prices the tight afternoon 15–17 (the caiso-94
autumn diagnosis), a mild λ reduction HELPS C3a. This is exactly the charter's
predicted shape: an availability/commitment lever, not an offer-cost cut.

## 4. CT_PEAKER — a pure online-hours gap that must NOT become a floor

The decomposition is unambiguous: day ΔE = −1.94/−2.04/−0.97 TWh with the
commitment part −2.03/−2.01/−0.98 and the dispatch part ≈ 0 (loading-when-on
comparable, 0.50–0.59 both sides). The measured class is online around the
clock (0.2–0.5 GW overnight, 1.5–2.2 GW evening peak 2023; output 60–250 MW in
every hour) while the model's CT fleet is dark outside a thin evening sliver.

But **caiso-91b stands**: the class's measured conduct is DAILY MERIT BLOCKS
(Panoche: 1,107 starts / median run 7 h / fully off 58 % of hours), not
commitment — there is no committed window to declare, so a commitment/floor
mechanism remains refuted (and D-2 confirms nothing floors the class today:
`ra_mustoffer_bridge` forces 0.003/0.001/0.000 TWh; `ct_mustrun_per_plant`
quarantined off; `ct_netload_drag` off — rule 19 enumeration clean). The
caiso-92 measured DAM offer surface (in the keeper) already re-priced the CT
econ/peak rungs to the measured bids — the class STILL never clears, so the
defect is not the CT offer either. **The defect is on the other side of the
merit order: the model's evening clearing never reaches the CT rung because
something cheaper serves those hours that reality does not have:**

- **The model over-imports the evening.** Net imports hod 17–21:
  model 7.83/8.24/9.22 TWh vs measured (EIA-930) 5.95/6.14/7.04 —
  **+1.9/+2.1/+2.2 TWh/yr of excess evening import**, at hub-priced rungs
  below the CT offer. (The belly is over-imported too: model 5.9/7.0/7.3 vs
  measured 1.3/2.5/3.4 TWh — absorbed by model storage charging; context for
  §3's dispatch half.)
- Simultaneously the model's evening λ is UNDER-priced (−6.6/−5.0/−2.4 pp,
  deepened by caiso-94's unconditional hod 6–21 window) and its evening CC
  over-serves (§3). Real evenings have MORE supply (the CT fleet) at HIGHER
  prices — the model substitutes cheap import/CC MW for reality's
  expensive-rung CT MW, which under-prices λ AND under-produces gas AND
  under-emits, one defect, three symptoms.
- A CT floor would push evening λ further DOWN — the wrong direction on
  C3a-evening — while faking the CO2. Rule-1 forbidden shape.

**Verdict (lane question c, CT_PEAKER): route to the evening supply-stack
composition, not to a CT mechanism.** The named sub-levers are both
already-flagged owner territory: (i) the caiso-94 evening sub-window — its own
FINDING §4/§7 pre-registered "drop the evening peak 18–21" as the principled
hod-restriction IF the overshoot materialized; the promotion put it on watch
("only if it degrades further"). This session's evidence upgrades the watch
from a price residual to a **volume + CO2 wedge** (the +2 TWh/yr excess import
is CT_PEAKER's −1.1 to −2.0 Mt). Whether that constitutes "degrades further" is
the owner's call, not this session's. (ii) evening storage timing (model
evening net discharge 4.3/6.5/5.9 TWh) — the separate storage charter named in
FINDING-caiso94 §5.

## 5. CT_CHP — the existing steam floor's LEVEL is wrong, not its mechanism

The model's class is 81–90 % floor-carried (D-2, `chp_steam` — the caiso-89
p25 available-CF level) at a flat ~28 MW and ~40 % loading. The metered conduct
is a steam-host BASELOAD at HIGH load: loading-when-on ≥70 % in **79/85/88 %**
of on-capacity-hours (model: 12–14 %), with a daytime hump (measured 32–70 MW
avg by hod). And the CEMS-visible slice is only ~0.4 TWh of the class — the
EIA-923 classFull gap is −1.84/−1.76/−1.08 TWh, i.e. **mostly CEMS-invisible
cogens whose grid delivery the p25 statistic misses**. One mechanism owns the
class (rule 19 clean); its level statistic under-measures the host's sustained
operating level. A re-derivation of the level source (p25 all-hours
available-CF → a statistic that matches the class's own measured conduct) is a
**rule-23 derive-script change: it must cite this source-data evidence, not a
residual, and is owner-gated.**

## 6. ST_GAS — 2023-only, small, named

−1.13 TWh (classFull) / −0.38 TWh (CEMS-visible) in 2023 — the final operating
year of the OTC steam fleet, which reality ran through the year's evening
ramps (CEMS 38–121 MW avg by hod, online 0.1–0.3 GW) and the model barely
touches. 2024/2025 are flat-to-over (+0.17/−0.05). Worth ~0.68 Mt of the 2023
C5a gap only; report-only, no charter (the class carries its own drag/startup
mechanisms and the 2023 fleet is retired forward — a fix has no forecast
surface).

## 7. Charter asks (owner authorization required BEFORE any LP solve — caiso-93/94 protocol)

Priority order by C5a mass and structural cleanliness:

1. **WP-1 — CC afternoon startup-trajectory re-commitment (the lane's core).**
   Extend the EXISTING P1-native RA must-offer bridge (rule 19: same mechanism,
   wider physics — never a new stacked floor) with a **startup lead**: for each
   detected evening run-start of a bridge-eligible CC, floor the L hours before
   the start at the ramp-in/min-load trajectory, L = the class's
   start-to-load duration — a measured physical parameter (CEMS multi-year
   median start-to-full-load per plant is rule-13 admissible: physics-grounded,
   regenerates forward, responds to changed run patterns) or the
   `CC_COMMITMENT_PARAMS` constants. Driver: hot-start + ramp physics and DAM
   operating-day positioning; window: the pre-start afternoon hours its own
   detector emits; forward story: regenerates from the model's own P0 run
   pattern. Expected effect: +1.0–1.5 TWh/yr CC in hod 13–17 displacing import
   volume at hub-set λ (belly clearing untouched, C3a-safe), ≈ +0.4–0.65 Mt/yr
   toward C5a. Also expected to cut the model's 2× start-churn.
2. **WP-2 — evening supply-stack composition (owns CT_PEAKER + the evening λ).**
   No build from this lane: present §4's volume evidence to the owner as the
   caiso-94 evening-window watch input and the storage-charter input. If the
   owner rules the watch tripped, the pre-registered principled fix is the
   caiso-94 FINDING's own hod-trim (18–21) — grounded in its measured
   per-cell admissibility table, not in this residual.
3. **WP-3 — CT_CHP steam-floor level re-derivation** (rule-23 change, cites
   §5's measured-conduct evidence; the p25 statistic vs the host's sustained
   level). Small (−0.3 to −0.6 Mt) but chronic and mechanically trivial.

**A clean composed outcome:** WP-1 + WP-3 recover ≈ 0.7–1.2 Mt/yr of the
2.96–4.04 Mt C5a gap structurally; the remaining mass is WP-2's (owner-gated)
and the 2023 ST_GAS residual. No component tunes to the residual; every lever
is a measured physical structure with a forward story.

## 8. Do NOT redo

The caiso-94 daytime mechanism or its derive-gate; widening/deepening any clean
tranche to chase CO2; throttling any measured clean import to protect a CO2
number (rule 1); a CT_PEAKER commitment floor or mustrun family (caiso-91b
conduct refutation stands); cutting CC offer costs to lower the belly (the
identified CC lever is availability-side, and the belly core shows NO
commitment deficit to fix); re-tuning the caiso-92 measured offer multipliers
(rule 23 — the CT rungs are measured and are not the defect).
