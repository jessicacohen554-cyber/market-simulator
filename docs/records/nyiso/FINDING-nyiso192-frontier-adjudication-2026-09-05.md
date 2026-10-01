# FINDING — nyiso-192 (`backcast-calibration` lane, frontier adjudication): the two nyiso-191 hand-forwards decomposed with NO LP — the top-of-queue Sithe object was three-quarters a DASHBOARD-PAYLOAD ARTIFACT (repaired, keeper payload re-rendered), the `ST_GAS` zonal pattern resolves to two owner-court identifications and cell G, the Astoria merit-panel defect turns out to move the WHOLE steam fleet's availability and was A/B-solved, and the keeper's C8 PASS is shown to be instrument-dependent

**Session:** nyiso-192, `backcast-calibration` lane
(`claude/nyiso-192-frontier-adjudication-mo2nrq`), 2026-09-05. **Solves run: TWO**
— the keeper replayed IN PLACE as the control (bit-identical; it mints no run)
and ONE arm (`results/calibration/nyiso192_astoria_panel`, registered
`2026-09-05-nyiso-192-astoria-panel`; verdict in §4).
**Keeper at entry AND at exit: `2026-09-05-nyiso-189-steam-identity`** —
CALIBRATED, grade 7, fails 0, C3c ledgered — re-verified artifact-only after its
payload was re-rendered. **Markers:** `complete.NYISO` held and keyed to the
keeper (D56-R); `final` empty; freeze active; **nothing re-keyed, no marker
requested, no out-of-training year touched.** Frontier stays WITHDRAWN; the
assessment for card C-10 / Q39 is
`results/calibration/ASSESSMENT-nyiso192-frontier-2026-09-05.md` and the owner's
one-card decision `docs/DECISION-CARD-nyiso192-frontier-2026-09-05.md`.
**Pre-registration:** `results/calibration/PREREG-nyiso192-frontier-adjudication.md`
(§0–§6 pushed before the control replay and before any payload re-render; §7
Amendment 1 pushed before the arm was solved); every bar below is executed
verbatim.
**Machine records:** `_nyiso192_payload_addback_audit.json`,
`_nyiso192_sithe_duty_phase0.json`, `_nyiso192_stgas_zonal_decomp.json`,
`_nyiso192_plant_grain_rerendered_{keeper,arm}.json`,
`_nyiso192_c8_unit_grain_{keeper,arm}.json`; probes under
`scripts/probes/nyiso192_*.py` (+ `_nyiso192_common.py`);
`scripts/gen_nyiso192_attestation.py`; the arm bundle carries the repaired
extract and both availability tables.

---

## 1. The instrument defect — the CHP add-back in the dashboard payload

**What.** `scripts/render_calibration_html.py` adds a cogen's behind-the-meter
host supply back onto its **model** series so the plant heatmap compares the
full plant to the full CAMPD plant. The bench side has passed the nyiso-147
MEASURED per-plant shares since nyiso-149 (`measured=_btm_measured`). **The
model-payload site (the `mplants[key]["m"]` / `m_ann` writer) and the `volErr`
actual-side `_grid_frac` did not** — both fell through to `chp_btm_pct(sector)`,
the 35 % "merchant" default. Under `nyiso_chp_btm_measured` the keeper's LP holds
out the MEASURED share (`fleet/assembly.py`: 0 % at Sithe Independence 54547,
22.2 % at Linden 50006), so every NYISO cogen's series carried `e_ann × 35 %` of
**flat energy the LP never dispatched** — and the `m_ann` field nyiso-190 §3 and
nyiso-191 §6 built their plant-grain objects on carried it too.

**Measured on the committed keeper payload before the repair**
(`nyiso192_payload_addback_audit.py`):

| year | payload Σ `CC_CHP` | LP `class_hourly` `CC_CHP` | flat offset | Sithe payload / LP / CAMPD (TWh) | Sithe over-run, published → LP |
|---|---|---|---|---|---|
| 2023 | 21.29 TWh | 15.50 | 643–674 MW | 5.65 / 4.24 / 4.06 | +1.59 → **+0.18** |
| 2024 | 25.42 | 18.84 | 735–763 MW | 9.47 / 7.32 / 6.29 | +3.19 → **+1.04** |
| 2025 | 25.89 | 20.05 | 655–682 MW | 9.81 / 7.64 / 6.32 | +3.48 → **+1.31** |

The payload's hourly minimum at Sithe is exactly the flat add-back
(243 MW ≈ 6.158 TWh × 0.35 / 8760), and subtracting the sector add-back from
every CHP plant closes the class identity to the committed `class_hourly`
totals within byte-quantisation. The "model peak 1,366 MW against a CAMPD peak
of 1,193" quoted at nyiso-190 §3 is the add-back on top of an LP capacity of
1,157.8 MW × availability ≤ 0.972 = 1,125 MW — **there is no phantom winter
capacity at Sithe.**

**The repair.** The model-payload site now passes the run's own hold-out map
(`_btm_run_measured` = the measured map iff the run's `nyiso_chp_btm_measured`
is on, else `None` → the sector default), so the add-back mirrors what THAT
run's LP held out; the `volErr` actual side passes the measured map whenever the
artifact exists (the bench convention — a physical fact). Pinned by
`tests/scoring/test_render_chp_addback_measured.py`, which reads the source and
fails on any bare `_btm_share(` call.

**The keeper's payload re-rendered on the repaired instrument** (V1 / V2 / P1,
PREREG §3): the keeper replayed in place — **every committed hourly sidecar,
`metrics.json` and `calibration_attestation.json` byte-identical**; the three
stamp-only files (`meta.json` / `run_config.json` / `legitimacy_diagnostics.json`:
timestamp, git sha, the replay's default note, a newly-serialised default field
and `load_share` values) restored to the committed bytes before registration.
`dashboard_add_run.py --no-prune` under the same label re-rendered
`runs/2026-09-05-nyiso-189-steam-identity.js`: the sidecar byte-identical; the
bench parts changed ONLY in `meta.builderFingerprint`; **86 of 86 non-CHP plants
byte-identical in `m` and `m_ann` in every year**; the CHP class identity
(Σ `m_ann` − Σ measured add-back − unbenched LP = `class_hourly`) closes to
**≤ 0.0001 TWh**; Sithe reads **4.228 / 7.322 / 7.637 TWh** (predicted 4.24 /
7.32 / 7.64), i.e. over-runs of **+0.17 / +1.04 / +1.31** (predicted +0.18 /
+1.04 / +1.31); the plant-grain offsetting misallocation reads **8.41 / 6.98 /
6.92 TWh** (predicted 8.4 / 7.0 / 6.9). **P1 HELD.** Determination re-verified:
CALIBRATED, 1 ledgered caveat.

**What it corrects in the record** (`_nyiso192_plant_grain_rerendered_keeper.json`):

| | nyiso-190 §3 (published) | corrected |
|---|---|---|
| gross over 2023 / 2024 / 2025 (TWh) | +11.86 / +11.25 / +11.22 | **+8.41 / +6.98 / +6.92** |
| gross under | −7.38 / −8.18 / −9.29 | −9.35 / −9.99 / −10.51 |
| offsetting misallocation | 7.4 / 8.2 / 9.3 | **8.4 / 7.0 / 6.9** |
| largest over-runner | Sithe (2024 / 2025) | **Ravenswood `ST_GAS`** +3.13 / +1.74 (2023 / 2024); Sithe +1.31 (2025) |
| Linden 50006 | −0.18 / −0.43 / −0.55 | **−0.90 / −1.15 / −1.28** (UNDER) |
| Brooklyn Navy Yard | +1.35 / +0.86 / +1.19 | +0.70 / +0.35 / +0.57 |

Non-CHP rows are untouched. **Fourteen other registered NYISO payloads still
carry the defect** — their slim bundles hold no dispatch parquet to re-render
from — and are flagged here, not rewritten (PREREG S5); the class-level record
and every determination they carry are unaffected.

---

## 2. Object 1 — Sithe Independence 54547 (phase 0, no LP, no lever)

1. **The census rule is right.** Sithe's row in the frozen
   `chp_layup_census_NYISO_population.csv` reads `cells_zero 0 of 18`, pooled
   median 752 MW, HSL 1,187 MW, online share 0.844, verdict `operating`. The
   rule is a LAY-UP test (median gross = 0 in every 4-hour block of every year);
   Sithe ran 6.3 TWh. A rule that admitted it would be a low-CF test — the form
   nyiso-148 rejected by name — and a price-conditional duty curve for a live
   merchant CC would pin observed conduct (rule 13 `[R-MEASURED]`). It is not
   proposed.
2. **The corrected residual is level-when-on, not hours-on** (LP series = payload
   − flat add-back; `_nyiso192_sithe_duty_phase0.json`): 2024 +1.03 TWh = +0.81
   both-on level + 0.32 measured-off / LP-on − 0.10 LP-off / measured-on; 2025
   +1.32 = +1.20 level. CAMPD has all four trains on for 72 % of on-hours at a
   mean 949 MW (80 % of HSL, 3,620 of 5,755 four-on hours below 85 %); the LP
   holds the plant at 0.88 / 0.94 of its available capacity against 0.76 / 0.78
   measured.
3. **Offer position.** On the model's own SRMC (Tenn Z4 200L + $2 VOM + RGGI),
   Sithe's last econ tranche ($23.96 / $25.23 / $32.03) is in merit **95.8 %** of
   2024 hours at the model's Upstate_West price but **76.8 %** at the actual
   Zone-C RT LBMP: the model prices Upstate_West below $20 in 0.7 % of 2024
   hours against 15.3 % actual (p05 $23.4 vs $16.7). **0.52 of the 1.03 TWh 2024
   residual sits in those trough-flip hours** — the compression object
   (nyiso-109 corrected the trough half; nyiso-167/168: a year-invariant 0.70
   price-response gain, its one new mechanism provably LP-inert; the remainder
   owner-court, DECISION-CARD-nyiso148 Q1). In 2023 the trough matches (28.8 %
   vs 29.6 %) and the residual is +0.18; in 2025 it is 2.4 % vs 4.1 % and the
   +1.32 TWh is NOT price-explained: in 74 % (2024) / 66 % (2025) of the hours
   the plant part-loaded, the actual Zone-C price was ABOVE its full-load SRMC.
4. **What remains is unidentifiable in-repo.** Sithe files no EIA-923 Schedule-5
   delivered-gas cost (0 rows; only 2493 / 2511 / 2516 / 2517 / 56196 do in NY),
   so whether its true delivered basis sits above the SOM Zone A–B hub the model
   assigns cannot be measured; and four trains at 80 % while in merit is the
   signature of a regulation / reserve reservation, a product the representation
   does not carry (the NYCA reserve families are hydro-saturated at zero dual in
   every hour — nyiso-152).

**Disposition: INADMISSIBLE / IDENTIFICATION-BLOCKED at the current
representation; magnitude corrected 3×.** The intake that would unblock it:
Sithe's delivered-gas basis (a plant-specific receipt or the Empire / Iroquois
Waddington index the plant actually buys on) and a regulation product. Neither
is a lane lever.

---

## 3. Object 2 — the `ST_GAS` zonal placement, decomposed (phase 0, no LP)

`_nyiso192_stgas_zonal_decomp.json`, on the keeper's reconstructed offers, its
hourly zonal prices and the MIS RT zonal LBMP (2024 shown; 2023 / 2025 agree):

| plant | zone | committed mc | S0 in-merit (model offer vs model price) | S1 (vs ACTUAL price) | S2 (NYC on the Iroquois basis) | measured on-share | model / CAMPD TWh |
|---|---|---|---|---|---|---|---|
| Ravenswood | NYC | 39.6 | 0.469 | 0.382 | **0.102** | 0.490 | 2.44 / 0.68 |
| Arthur Kill | NYC | 40.4 | 0.397 | 0.353 | **0.101** | 0.784 | 2.13 / 1.35 |
| Astoria | NYC | 42.2 | 0.311 | 0.308 | 0.077 | 0.690 | 0.66 / 0.92 |
| Northport | LI | 47.1 | 0.140 | 0.226 | 0.138 | **0.999** | 2.14 / 3.92 |
| E F Barrett | LI | 46.5 | 0.163 | 0.234 | 0.163 | 0.898 | 0.79 / 1.14 |
| Bowline Point | CH | 44.8 | 0.132 | 0.188 | 0.132 | 0.266 | 0.44 / 1.35 |
| Roseton | CH | 47.7 | 0.091 | 0.149 | 0.091 | 0.083 | 0.12 / 0.26 |

* **The NYC over-run is carried by the zonal delivered-gas basis, not by price
  formation and no longer by the heat rate.** NYC steam buys at the Transco Z6
  NY hub (1.97 / 2.07 / 3.86 $/MMBtu) against LI / CH at Iroquois Z2 (3.28 /
  2.77 / 5.06) — a gap the repo's own monthly Transco / Iroquois series
  reproduces to ±$0.1. Put NYC on the reference basis (S2) and its in-merit
  share falls to LI / CH's level. The model's NYC price is at or BELOW actual
  (−$0.7 / −$7.0 in 2024 / 2025), so price formation cannot carry it.
  Ravenswood's heat-rate basis is CLOSED on the keeper (`egrid_family_heat_rates`
  K, committed HR 12.906 — now the highest of the NYC steam plants). The
  plant-specific delivered basis for Ravenswood / Arthur Kill / Astoria is
  UNFILED (no F923 receipts), so which basis is right is an **identification
  intake** (Con Edison / KEDNY electric-generation transport service and rate;
  Ravenswood and Astoria are Con Ed, Arthur Kill is KEDNY).
* **The one in-repo alternative is refused ex ante, with the computation.** The
  LDC-delivered daily index the `CT_PEAKER` leg uses (`nyiso_downstate_ct_gas_daily`:
  Transco Z6 NY daily + KEDNY SC-22; 4.53 / 4.90 / 7.66 $/MMBtu in NYC) would
  shift NYC steam's committed tranches by **+$34 / +$37 / +$53 per MWh** to an
  in-merit share of **0.4–1.3 %** in every year on the keeper's own prices,
  leaving the class only what the NYC persistent-base floor holds (2.85 / 2.31 /
  1.67 TWh) — ~100 % floor-forced, so **rule 20 / C8 fails by construction**.
  That is the nyiso-187 result restated from the offer side: the market's NYC
  steam dispatch is out-of-market commitment, **cell G**. nyiso-145 already
  refused the same extension for the LI CC / ST fleet on F923 grounds.
* **The LI / CH under-run is out-of-market commitment plus the compressed
  downstate premium.** S1 lifts LI / CH in-merit shares by only 0.05–0.09; the
  model prices LI $2.9 / $9.7 below actual (spreads LI−CH 5.6 vs model 1.8;
  NYC−CH 2.9 vs 1.2); Northport is ON 99.9 % of measured hours at CF 0.28 and
  Bowline ON 27 % against a 13 % in-merit share on its own SRMC — nyiso-187's
  `b ≥ 0.50` in every downstate cell. Owner: cell G + C3a-2025 (Q1).

**Disposition:** NYC over → identification intake (OWNER-HELD) + BLOCKED (G);
LI / CH under → BLOCKED (G) + OWNER-HELD (Q1). No lane lever. The one measured
input inside this pattern that a lane COULD repair is the merit-panel defect of
§4, which sets these plants' availability.

---

## 4. The one live lever — the Astoria merit-panel stack-duplicate repair, A/B-solved

**Why it was built.** Enumerating the record for the assessment found this
object carried unbuilt through nyiso-185…191 ("sized, not repaired; needs its
own A/B on that lane"). Under the pre-registered frontier rule a live admissible
lever forces NO, so it was adjudicated (PREREG §7 Amendment 1, pushed before the
arm; the control replay was already running on the committed extract).

**The repair.** `scripts/lib/outage_detect.build_merit_order_panel` read the
CAMPD parquets bare and never applied the stack-duplicate helpers
`campd._normalize_campd` applies; Astoria 8906's `31RH`/`32SH` and `51RH`/`52SH`
pairs entered the guard as two units each carrying the SAME generator MW with
half the heat — SRMC at half its physical value in the test that decides
mechanical outage vs economic lay-up (nyiso-184 §4.1: panel HR 5.55 vs merged
11.01). The loader now drops the duplicate's `grossLoad` copy and re-labels it
onto its primary; `tests/curation/test_merit_panel_stack_duplicate.py` pins it
(10.33 on the fixture, 5.33 before). The registered stack-pair set is `{8906}`
(NY only), so every other ISO's panel is byte-identical by construction.

**Phase 0 — the re-derived extract** (`--iso NYISO --years 2019…2026
--per-unit-crosswalk --merit-order-guard`, the committed `.meta.json` flags; to
a scratch path, then bundle-local as
`nyiso192_astoria_panel/campd-unit-outages-perunitmerit-NYISO_repaired_panel.csv`,
sha256 `58799099…` against the committed `45714bb9…`): 3,668 → 3,717 rows;
**106 windows leave — all Astoria** (`31RH` 226 / 189 → 89 / 0 window-days in
2023 / 2024; `51RH` 241 / 219 → 0 / 0) — and **155 windows ENTER at fifteen
other plants** (Ravenswood +41, Arthur Kill +25, Port Jefferson +21, Northport
+12, Riverbay +12, Roseton +10, Sterling +10, Bowline +7, …), because the
guard's revealed clearing cost is the capacity-weighted p90 SRMC of the RUNNING
units and Astoria's rows are in it: priced at their physical SRMC they lift the
RCC in the hours they run, every other unit reads in merit more often, and
fewer of their dead spans clear `MERIT_OOM_FRAC`. **My "Astoria-only"
assumption was wrong and is recorded as such.** Availability, the engine's own
builder on each extract (`_availability_{keeper,repaired}_extract.json`):

| plant | keeper extract 2023 / 2024 / 2025 | repaired extract |
|---|---|---|
| 8906 Astoria `ST_GAS` | 0.177 / 0.240 / 0.330 | **0.367 / 0.509 / 0.462** |
| 2500 Ravenswood `ST_GAS` | 0.786 / 0.478 / 0.309 | 0.786 / **0.260 / 0.121** |
| 2490 Arthur Kill | 0.855 / 0.907 / 0.527 | 0.829 / **0.453** / 0.527 |
| 2516 Northport | 0.527 / 0.526 / 0.552 | **0.368** / 0.521 / 0.526 |
| 2625 Bowline · 8006 Roseton · 2480 Danskammer · 2517 Port Jefferson | 0.148 / 0.224 / 0.397 · 0.057 / 0.067 / 0.755 · 0.222 / 0.223 / 0.215 · 0.925 / 1.000 / 1.000 | 0.104 / 0.224 / 0.288 · 0.057 / 0.067 / **0.357** · 0.222 / 0.223 / 0.079 · 0.916 / 0.989 / 0.830 |

This re-opens Ravenswood's *availability* under DO-NOT-REDO's own exception —
new evidence: nyiso-183 refuted a mis-booking by the guard on a panel whose
INPUT was defective; the guard's rule and thresholds are untouched.

**The A/B** (`2026-09-05-nyiso-192-astoria-panel`; control = the keeper
replayed in place on the committed extract, bit-identical; the repaired extract
swapped in at the committed path for the arm's solve and the committed file
restored byte-for-byte afterwards, hash-verified; computed attestation
`gen_nyiso192_attestation.py` — G-CONTROL bit-identical, **G-DELTA `[]`** with
three newly-serialised defaults reported as non-deltas, G-INPUTS both pins
match, G-DOF 13 / 6 verbatim, G-ENGAGE the envelope moved as predicted):

| bar | result |
|---|---|
| **B1** engagement | Astoria's mean LP capacity up in every year; Ravenswood's down in 2024 / 2025 — **ENGAGED** |
| **B2** predictions | (a) Astoria `ST_GAS` 0.617 → 0.976 / 0.661 → 1.207 / 1.161 → 1.481 TWh — HELD; (b) Ravenswood 2.419 → 1.726 / 1.911 → 1.060, 2023 +0.018 — HELD; (c) Roseton 2025 0.431 → 0.361 — HELD |
| **B3** rejection rule | C2 PASS; **C3a +4.9 / +1.7 / −8.3 → +4.8 / +3.2 / −7.3 %** PASS; **C3b 0.119 / 0.166 / 0.177 → 0.118 / 0.172 / 0.167** PASS; **C8 `ST_GAS` 19.7 / 23.6 / 18.3 → 17.1 / 23.8 / 18.6 %** PASS (unit grain 0.393 / 0.414 / 0.305 → 0.369 / 0.403 / 0.287) — **NO FLIP, not rejected** |
| **C1** | **2024 `CC_REGULAR` +3.33 → +3.68 TWh, +2.8 → +3.0 pp — FLIPS PASS → FAIL** (share out of band); 2023 `ST_GAS` +1.92 → +1.77, 2024 `ST_GAS` −0.62 → −1.43, `CC_CHP` 2024 +1.82 → +2.10, all in band. Determination **NOT-YET** (grade 6, fails 2: C1 and C3c — C3c no longer lone) |
| **B4** structural integrity | plant-grain offsetting misallocation **8.41 → 8.67 (2023, worse) / 6.98 → 6.24 / 6.92 → 6.41 (better)**; `ST_GAS` Σ|plant error| 7.71 → 8.22 / 6.43 → 4.87 / 5.38 → 4.46; NYC steam over-run +4.26 → +4.60 / +2.24 → +1.31 / +0.41 → −0.07; Arthur Kill 2024 +0.78 → −0.01, Ravenswood 2025 +0.84 → −0.01; Northport 2023 −0.63 → −1.11 (its lowered envelope); load-weighted price +0.7 $/MWh in 2024 / 2025 |

**Where the 2024 `ST_GAS` energy went:** −0.81 TWh `ST_GAS` → +0.35 `CC_REGULAR`,
+0.28 `CC_CHP`, +0.09 `CT_CHP`, +0.05 import, +0.03 `CT_PEAKER`. The C1 flip is
the within-family fill onto the class nearest its band — the nyiso-187 /
nyiso-190 mechanism: the market ran NYC / LI steam out of market (cell G), the
model cannot, and whatever is taken off steam by a more accurate input lands
on combined cycles.

**Disposition — ADJUDICATED, the call is the owner's** (PREREG §7.3 "C1 flip
only → owner call", executed verbatim). Rule 14 `[R-ACCURATE]`: the repaired
panel is the accurate input and the C1 regression is a discovered root-cause
issue with a named root cause (G). What the owner should weigh, stated plainly:
promoting the arm under the standing formula puts a NOT-YET keeper under the
`complete` marker, which the uniform Q5-W rule forbids — the marker would fall
again; holding the keeper leaves it on a pre-repair extract that the repaired
derive no longer reproduces (the keeper stays reproducible from its COMMITTED
bytes — the file, not the derive, is its pinned input — and the repaired
extract is preserved bundle-local for whichever keeper next carries it). The
keeper is **unchanged**; the arm is registered NOT-YET with this disposition in
its sidecar; the code repair ships.

---

## 5. The keeper's C8 PASS is instrument-dependent (measured, not acted on)

nyiso-181 §6 escalated the D-2 plant-grain under-count on the superseded
nyiso-177 keeper. Measured on the current keeper's own `unit_hourly` dispatch and
`floors` (both written by every solve), with D-2's own `at_floor_mask` and
tolerances (`nyiso192_c8_unit_grain.py`, `_nyiso192_c8_unit_grain_keeper.json`):

| class | unit-grain forced share 2023 / 2024 / 2025 | committed plant-grain C8 | cap |
|---|---|---|---|
| **`ST_GAS`** | **0.393 / 0.414 / 0.305** | 0.197 / 0.236 / 0.183 | 0.30 |
| `CC_REGULAR` | 0.123 / 0.119 / 0.113 | 0.027 / 0.009 / 0.012 | 0.30 |
| `CC_CHP` | 0.270 / 0.218 / 0.202 | (D-2-exempt) | — |

Every `ST_GAS` year is above the cap at unit grain. This is a scorer-instrument
fact, code-generic across six ISOs, and NOT this lane's to re-base (rule 25); a
re-based breach would escalate to rule 20's provenance + shape path, not fail
automatically. It is reported at full magnitude because a frontier declaration's
"CALIBRATED" limb otherwise rests on a number the owner has not seen.

---

## 6. Handed forward

1. **Card C-10 / Q39** — the frontier question, put to the owner with the
   disposition table on its face (`DECISION-CARD-nyiso192-frontier-2026-09-05.md`).
2. **The D-2 / C8 grain** (§5) — scorer lane, cross-ISO; the NYISO number is now
   measured on the current keeper.
3. **The NYC steam delivered-gas identification** (§3) — owner-court intake
   (Con Ed / KEDNY transport service and rate for Ravenswood / Astoria / Arthur
   Kill); whatever basis is adopted, the dispatch it leaves is cell G's.
4. **Sithe's delivered basis and a regulation product** (§2) — owner-court
   intakes; the census rule stands.
5. **Fourteen historical NYISO payloads** carry the add-back defect (§1) — a
   records item; the formula to correct any `m_ann` is `m_ann − e_ann × (0.35 −
   measured share)` for a `nyiso_chp_btm_measured` run.
6. **Cross-ISO: the merit-panel repair is byte-identical for every other ISO**
   (the stack-pair registry is `{8906}`), so no other extract moves; if the
   registry ever gains a non-NY facility, that ISO's extract re-derives under
   rule 23.
7. Unchanged: C3a-2025 (Q1); cell G; `chp_layup_duty_curve` K; the `CC_CHP`
   widening R; the pooled CT-only test (cross-ISO derive lane); the Bethlehem
   headroom note; eGRID 2025 not landed.

## 7. Governance

Rule 1 `[R-STRUCT]`: bars, dispositions and the arm's rejection rule were fixed
and pushed before the control replay, before the payload re-render and before
the arm; nothing was adopted or refused on a residual; the ex-ante refusal of
§3's LDC extension rests on a floor-forcing collision (rule 20), never on a fit.
Rules 5 / 21 / 24: zero new constants, zero retuned constants, zero new
`ScenarioConfig` fields, zero new DOF entries — two call-site data-handling
repairs (payload add-back; merit panel stack pairs). Rule 11 / 14: both defects
repaired at their root. Rule 13: every measured series diagnoses; the
demonstrated-conduct statistics pin nothing. Rule 15: the arm registered with
its verdict in its sidecar; the keeper's payload re-rendered under its own id.
Rule 16 / 12: 2023–2025 in one bundle each; the two invocations never
overlapped on the extract. Rule 19: the panel repair replaces nothing and stacks
nothing — it corrects the input of an armed K mechanism. Rule 22: training years
only; markers untouched. Rule 23: the extract re-derived ONLY because its source
handling changed, cited. Rule 25 / 28: NYISO shard only; the cells touched are
`campd_outage_merit_order_guard`, `offer_curve_by_group`, `cc_capacity_reconcile`,
`chp_layup_duty_curve`, `nyiso_downstate_ct_gas_basis`, `scuc_load_pocket_commitment`.
Rule 27: on-disk bytes pushed; every ≥300-line blob verified after each push
(`render_calibration_html.py`, `outage_detect.py`, the NYISO shard,
`mechanism-testing-matrix.md`).

*(nyiso-192, 2026-09-05. Two solves. Keeper unchanged. Frontier not declared.)*
