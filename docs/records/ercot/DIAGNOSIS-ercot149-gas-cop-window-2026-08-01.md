# DIAGNOSIS — ERCOT-149: the gas-side COP-vs-window collision is MATERIAL (4.27 / 5.93 / 4.14 TWh above the measured-window ceiling) and a DEFECT of the ERCOT-148 class — carried as much by the pin's own site-series misalignments as by OFF-at-HSL filings; fixed by widening the incumbent event cap to the DAM-covered gas classes

**Date** 2026-08-01 · **ISO** ERCOT · **Lane** ercot149-gas-cop-window (the
ERCOT-148 named successor, diagnosis §6.1; open owner ruling #7) · **Keeper
under audit** `2026-07-31-ercot148-dam-event-cap` (bundle
`ercot148_dam_event_cap_arm`) · **Method** Phase 0/1 no-LP reconciliation
through `scripts/probes/ercot149_gas_outage_phase0.py` (committed record
`results/calibration/ercot149_gas_outage_phase0.json`), the raw 60-Day DAM
disclosure rows, the merit-order guard's own panel
(`scripts/lib/outage_detect.build_merit_order_panel`), and the keeper's
committed dashboard payload as dispatch ground truth. **No LP was built and no
year was solved in Phase 0/1.** Phase 2 (the single-delta arm) is chartered by
`docs/PRECOMMIT-ercot149-dam-gas-event-cap-2026-08-01.md`.

**Preconditions.** `audit_keepers.py --iso ERCOT` PASS 0/0 at session start.
The default `ScenarioConfig().cache_key()` has drifted name-only again
(handoff `8161b094a391de90` → `0e9fce2fb55b889f`, post-merge default-off
fields, neiso-74 et al.); the armed-key MECHANISM verified instead of a pinned
hash: the keeper bundle's `run_config.json` `scenario_config` rebuilds into a
`ScenarioConfig` with every stored key still a live field,
`ercot_dam_availability_coal_event_cap=True` on, and toggling it moves the
cache key. Payload decode calibration: the probe's decode + ceiling machinery,
run in coal mode on the superseded `2026-07-31-ercot145-gas-daily-shape`
payload, reproduces the ERCOT-148 committed coal quantification —
4.37/4.99/5.01 vs the committed 4.36/4.98/5.01 TWh, per-plant table matching
to 0.01 TWh (Limestone 1.12/1.12/1.49, Parish 1.06/1.28/1.12, J K Spruce
1.14/0.45/0.96, …).

---

## 0. The charge, and what the audit actually found

ERCOT-148 fixed the coal side of the DAM-COP-restore-vs-measured-window
collision and left the gas side **explicitly unmeasured**, with the standing
caution that the coal ruling does NOT transfer: gas is load-following, the
deriver's `OFF`-is-available convention is genuinely correct there, and the
CC/ST windows passed a different (event-based) detector. This audit measured
the gas side on its own conduct. Findings, in order of size:

1. **The collision is material** (§1): the keeper dispatches
   **4.27 / 5.93 / 4.14 TWh** (2023/24/25) of CC_REGULAR + ST_GAS above the
   measured event-window availability ceiling — the same order as the coal
   phantom ERCOT-148 removed (4.36/4.98/5.01). Roughly half rides the
   plant-grain pin at crosswalked plants, half the class-hour/residual
   water-fill at unmapped plants.
2. **The mapped-channel restore is carried by three MEASURED mechanisms**
   (§3), and the largest is not an `OFF`@HSL filing at all: the DAM deriver's
   config-collapse **aliases two physical CC trains into one site** whose live
   capability is the max across trains — a single-train outage is invisible to
   the pin **even when the dead train's configs file `OUT` honestly**
   (Guadalupe, Oct–Dec 2024). The second is **partial site acceptance** (the
   crosswalk accepts a subset of the plant's DAM sites — Jack County's train 2
   is the unaccepted site `JCKCNTY2`). Only the third is the coal-symmetric
   conduct: **true `OFF`-at-HSL through certified dead stops** at
   fully-covered sites (Bastrop, Nueces Bay).
3. **The windows themselves are identification-strong on gas** (§2): they are
   dead spans (every hour < 2 % CF, one firing hour breaks the window) that
   survived the armed merit-order guard, and **81.6 % of their GW-days sit at
   exactly 0.0 out-of-merit share** on the guard's own panel — in merit for
   weeks while producing nothing. "Startable but unneeded" is untenable at
   that scale; the dead stops are mechanical (or contractual/mothball-grade —
   either way, not available capacity).

## 1. Phase 0 quantification (keeper payload, no LP)

Ceiling = the loader's own product exactly as the incumbent cap composes it
(≥ 5-day unit windows `unit_outage_derate_factors` × plant-grain partial
plateaus `partial_outage_derate_factors`, on the bins-sheet plant capacity).
Both layers are **armed incumbents on gas in the keeper**: with
`outage_source="historic"` the unit windows apply to every plant group
(`arrays.py:1026`) and the partial plateaus per plant code (`arrays.py:1226`);
the DAM overlay is applied after both and is the only availability-raising
layer above them. Model dispatch decoded from the keeper payload's per-plant
hourly series (`m` = base64 uint8 of 100 × MW / nameplate, rescaled so the
annual sum equals the payload's own `m_ann` — self-normalizing; calibration in
Preconditions).

Per class × year, TWh above the windowed ceiling (keeper payload / prior
`ercot145` payload — gas availability is byte-identical between the two, so
the near-identical phantom shows this is not an ERCOT-148 artifact):

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | 4.116 / 3.807 | 5.195 / 5.018 | 3.870 / 3.584 |
| ST_GAS | 0.158 / 0.131 | 0.735 / 0.635 | 0.272 / 0.241 |
| **DAM classes total** | **4.274** | **5.930** | **4.143** |
| CC_CHP (no-overlay control) | 0.070 | 0.170 | 0.236 |

Channel split (keeper): mapped pin 1.42 / 3.42 / 2.22 TWh, unmapped
water-fill 2.86 / 2.51 / 1.92 TWh. Top plants (2024): Jack County 1.10,
Guadalupe 0.92, V H Braunig 0.64, Bastrop 0.30, Nueces Bay 0.28, Midlothian
0.27 (unmapped), Tenaska Gateway 0.22 (unmapped). As a share of class energy
the phantom is far smaller than coal's (CC_REGULAR ≈ 2.7–3.5 % of a ~145 TWh
class vs coal's 7–8 %), but in absolute TWh it is the same defect size.

**Controls.** CC_CHP / CT_CHP carry windows but are excluded from the DAM
overlay by the deriver's class scope — nothing restores them — and their true
dispatch respects the ceiling exactly: their apparent 0.07–0.24 TWh "phantom"
is a flat in-window offset equal to the dashboard render's CHP-only BTM adder
(Pasadena 2024: 39.1 MW mean phantom = the flat adder; in deep windows the
decoded series sits at ceiling + adder). The CC/ST payload series carry no BTM
adder, so their phantom is real dispatch. CT_PEAKER has no windows by the
detector's own design (peakers dispatch economically) — no collision is
possible there.

## 2. The gas windows are identification-strong (the layup reading fails)

The committed gas rows passed a stricter chain than the coal rows:

- **Event-based detection** (`detect_outages_eventbased`): a window exists
  only if **every** hour of the span has CF < `ST_GAS_CF_PEAK` (0.02) — a
  single firing hour breaks it. Economic idling with occasional starts cannot
  enter the extract.
- **Revealed-availability filter** with the full-stop override (shared, armed).
- **Merit-order guard armed** at derive time: spans the unit was
  ≥ 90 % out-of-merit (measured CAMPD SRMC vs the revealed marginal cost of
  running capacity) were routed to the layup companion, which no loader reads
  — the provable economic layups are already out of the availability envelope.
- **Out-of-merit shares of what remains** (this audit, the guard's own panel
  re-run per window): over all 1,764 committed gas unit-window rows 2023–2025
  (8,912 GW-days), **81.6 % of GW-days at OOM share = 0.000 exactly**, 86.4 %
  ≤ 0.1, 91.4 % ≤ 0.5. Every headline window (Jack County Oct–Nov 2024,
  Guadalupe Oct–Dec 2024, Nueces Bay Aug–Oct 2024, V H Braunig Jan–Mar and
  Jun–Aug 2024, every Bastrop 2024 row) measures **0.000**.

A merchant unit that is IN MERIT — its measured SRMC below what the market
was paying running capacity — for weeks on end and never produces a single
hour above 2 % CF is not "startable but unneeded". The windows are measured
unavailability; the deriver's own docstring draws exactly this line ("a
genuine dead period" vs "an economically-idle-but-occasionally-firing unit").
The load-following caution protects the HOURLY `OFF` convention outside
windows — it does not license erasing a committed multi-week dead span.

## 3. The mapped-channel anatomy: three measured mechanisms

The pin (`_ercot_dam_plant_hourly_apply`) is bidirectional by design; whether
it erases a window at a crosswalked plant depends on why its site series stays
high through the window. Raw Gen_Resource rows (2024-10-15..25 pull +
full-2024 resource inventory; reproduce with the commands in the probe
docstring):

**3.1 Config-collapse train-aliasing (GUADG, KMCHI).** The deriver's
`_site()` truncates a CC resource name at its config tag, so `GUADG_CC1_*`
and `GUADG_CC2_*` — two **physical trains**, four configurations each —
collapse to ONE site `GUADG` whose live capability is `max()` across all
eight configs. The collapse is correct within one train (alternates never run
together) and wrong across two: with either train at full output the site
reads ≈ its p98 rating, so **a single-train outage is arithmetically
invisible**. During Guadalupe's Oct–Dec 2024 block the dead train's configs
file **`OUT` honestly** (`GUADG_CC1_1..4`: OUT, 264/264 rows in the pull)
while CC2 runs — site frac ≈ 0.97, plant pinned near-full, window erased
**despite honest COP conduct**. Crosswalk `p98_rating/plant_nameplate` shows
the halved grain directly: GUADG 0.51, KMCHI 0.47. Phantom at aliased plants:
0.372 / 0.919 / 0.736 TWh.

**3.2 Partial site acceptance (JACKCNTY, BRAUNIG_VHB3, GIDEONG3, OLING_3,
SANDHSYD, DANSBYG1).** The crosswalk accepts a subset of the plant's DAM
sites and the pin applies that subset's fraction to the whole model plant
bin. Jack County's second train is a **separate site `JCKCNTY2`** (present in
the disclosure, absent from the accepted rows): during train 2's committed
windows train 1 runs at ≈ rating → the whole 1,280 MW plant is held ≈ fully
available. V H Braunig: only `BRAUNIG_VHB3` (400 MW of an 1,138 MW plant) is
accepted; through VHB1/VHB2's committed dead windows the two file
**`OFF`@111–200 / `OFF`@75–160 MW** (startable-on-paper, the coal conduct)
but it is VHB3's own series that pins the plant. Ratios 0.33–0.52. Phantom at
partial-acceptance plants: 0.519 / 1.802 / 0.862 TWh.

**3.3 True `OFF`-at-HSL through certified dead stops (BASTEN, NUECES_B, and
the VHB1/2 filings above).** At fully-covered single-train sites the pin's
series IS the plant's own COP, and the phantom there is the exact
Coleto/Limestone signature on gas: Bastrop's committed windows carry
`dam_frac` 0.52–0.57 (a 1×1 config `OFF` at ~half rating through the dead
stop), Nueces Bay mixes `OFF`@HSL with honest `OUT` spells (frac 0.57–0.63).
Phantom at covered sites: 0.524 / 0.696 / 0.622 TWh.

**Controls reproduce the coal pattern.** Where the COP honestly reads `OUT`,
pin and window agree and the phantom vanishes: Victoria (covered,
`dam_frac` 0.019–0.29) carries 0.004–0.100 TWh; Rio Nogales 2024 (0.187) →
0.036. The within-plant control is decisive: **V H Braunig 2024** (site frac
0.70 through its windows) carries **0.643 TWh** of phantom; **V H Braunig
2025** (VHB3 itself down — frac 0.075) carries **0.059** on 360 windowed
days. Same plant, same windows CSV, opposite pin conduct, opposite phantom.
The failure tracks the fidelity of the pin's site series, not the plant.

## 4. The unmapped channel: the water-fill restore

Unmapped gas plants (2.9 / 2.5 / 1.9 TWh) are restored by the class-hour
water-fill / residual redistribution: the restore direction lifts every unit
toward its ceiling **proportionally to headroom**, and a windowed-out unit has
the most headroom, so it absorbs a disproportionate share of any class-level
restore (the ERCOT-82-fix design — reviving phantom-derated units is its
designed job everywhere else). Ennis 2023 is the clean example: whole-plant
windows (ceiling 0.000 TWh over 98 windowed days), model dispatches
0.246 TWh inside them. Same collision, same fix: the cap bounds the
per-generator result of the whole DAM block, whichever sub-mechanism restored
it.

## 5. Phase 1 adjudication

**Material: yes** — 4.1–5.9 TWh/yr, the size of the coal defect ERCOT-148
removed. **Defect: yes — the ERCOT-148 class**, argued from the gas fleet's
own conduct as the charter required:

1. **Two incumbent measured layers conflict at the seam.** The windows are
   applied to gas in the keeper today; the DAM overlay is applied after them
   and erases exactly the ones its site series disagrees with. This is an
   internal-consistency defect of the armed stack, not a question of whether
   gas windows *should* exist — they are already the committed rule-13 input.
2. **The layup defense fails on the guard's own instrument** (§2): 81.6 % of
   window GW-days in merit at share 0.000 while producing nothing. The
   deriver's `OFF`-is-available convention remains correct — and untouched —
   as the hourly commitment-state reading outside windows.
3. **The restore is not even carried by honest declarations where it is
   largest** (§3.1): Guadalupe's window is erased over the dead train's own
   `OUT` filings. Rule 14's misalignment clause applies directly — the pin's
   gas site series is measurably misaligned to our plant representation at 8
   of 16 accepted gas plants (ratios 0.33–0.52), and a misaligned accurate
   instrument must be reconciled, not applied literally.
4. **The honest-OUT and no-overlay controls** (§1, §3) show the stack behaves
   correctly wherever the instruments agree — the phantom is confined to
   conflicted window-hours, which is precisely where the incumbent cap's
   `min()` precedence operates.

**The fix is the incumbent cap, class scope widened** — one new default-off
ScenarioConfig gate (`ercot_dam_availability_gas_event_cap`) extending the
SAME `min()` block to the DAM-covered gas classes (CC_REGULAR / ST_GAS /
CT_PEAKER; CT provably inert — no windows by design). Never a second cap
layer (rule 19). Zero fitted parameters — a precedence rule between two
already-armed measured instruments (rule 14: the physical CEMS record
outranks the restored paper capability on conflicted hours; misalignment
documented on the ScenarioConfig field). The DAM overlay keeps its designed
job everywhere else: the remove direction and every non-window hour are
untouched (window factors are 1.0 there), and the coal-only arm stays
byte-identical (the widened loop's `(plant_code, plant_group)` key is the
former `(plant_code, "COAL")` literal for coal generators). NOT CEMS
pinning: an availability ceiling from the already-admissible overlay;
dispatch below it stays fully free. Forward story unchanged — both layers are
backcast-only overlays; forecast years keep the statistical stack (the G4
mode-aware seam).

## 6. Explicitly open (successor questions, NOT armed here)

1. **The deriver's `_site()` cross-train collapse** (§3.1) — the correct
   site-hour live capability for a multi-train family is the SUM of per-train
   maxes, not the max across trains. A rule-23 derive-identification fix,
   cited to this measurement; it would re-derive all three grains (class-day,
   class-hour, site-hour) and move every armed DAM keeper, so it is its own
   lane with its own re-gate — and the cap stays correct after it (windows
   still outrank restored paper capability on conflicted hours).
2. **The gas crosswalk's partial site acceptance** (§3.2) — completing the
   accepted site set per plant (JCKCNTY2, VHB1/2, GIDEONG1/2, …) is the
   companion fix on the crosswalk side; same lane as (1).
3. **The pin's remove-direction over-removal at partial-coverage plants** —
   V H Braunig 2025: VHB3 down pins the whole plant to ~0.075 while
   VHB1/2's status is unmeasured by the accepted subset. Out of this lane's
   restore-direction scope by charter; recorded, sized small on the keeper
   (VHB model 0.31 vs CAMPD 4.23 TWh in 2025 — but most of that gap is
   offer-economics under-dispatch, not the pin).
4. **The DAM deriver's rating basis for all-year-OUT sites** — already open
   owner ruling #8 (ERCOT-148 §6.2), unchanged by this lane.

## 7. Decision

Phase 2 is LICENSED: arm `ercot_dam_availability_gas_event_cap` (default-off
ScenarioConfig gate + matrix row in the same PR, rule 26c) as a single delta
off `ercot148_dam_event_cap_arm`, full span 2023–2025, precommit pushed
before the solve. Zero fitted parameters (a precedence rule between two
measured instruments) ⇒ structurally LOYO-exempt, per-year guard table
standing in (the ERCOT-145b/148 precedent). Ex-ante predictions and guards:
`docs/PRECOMMIT-ercot149-dam-gas-event-cap-2026-08-01.md`.
