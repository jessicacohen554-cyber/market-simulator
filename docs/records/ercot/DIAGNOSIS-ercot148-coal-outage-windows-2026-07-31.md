# DIAGNOSIS — ERCOT-148: the coal outage WINDOWS are correct and current; the over-run is the DAM COP pin RESTORING availability over them — a measured-vs-measured precedence defect, fixed by capping the restore at the event-window ceiling

**Date** 2026-07-31 · **ISO** ERCOT · **Lane** ercot148-coal-outage-audit
(owner directive 2026-07-31) · **Keeper under audit**
`2026-07-31-ercot145-gas-daily-shape` (bundle `ercot145_gas_daily_arm`) ·
**Method** Phase 0/1 no-LP reconciliation through
`scripts/probes/ercot148_coal_outage_phase0.py` (committed record
`results/calibration/ercot148_coal_outage_phase0.json`), the raw 60-Day DAM
disclosure rows, one frozen-derive re-run to scratch, and one byte-identical
keeper replay of 2023 used as dispatch ground truth (65.64 TWh coal
reproduced exactly; kept out of the dashboard — it is the keeper, not a new
run). Phase 2 (the single-delta arm) is chartered by
`docs/PRECOMMIT-ercot148-dam-coal-event-cap-2026-07-31.md`.

**Preconditions.** `audit_keepers.py` PASS 0/0. The directive's
`cache_key 603c2498bf71d21d` no longer reproduces — post-ERCOT-147 merges
added default-off fields (`coal_prb_committed_dispatchable`, miso-111); the
current default is `8161b094a391de90` and the drift is name-only (field
default off, keeper bytes unchanged — the miso-111 commit states every
existing keeper is byte-identical). Recorded, not a blocker.

---

## 0. The charge, and what the audit actually found

The directive's evidence: Coleto Creek +31.4 %/2023, +32.4 %/2024
(model 3.50 vs CAMPD 2.66/2.64 TWh), Limestone +40.3 %/2024 (7.53 vs 5.36),
with months-long CAMPD zero-op blocks the model runs through, and Sandy
Creek (−1.2 %/−0.7 %) as the captured control. All three numbers reproduce
exactly from the keeper's own payload (`m_ann` per plant) and bench
(`c_ann`).

The presumed defect — missing/clipped windows in
`campd-unit-outages.csv` — is **NOT what the audit found**. Three findings,
in order of size:

1. **The windows CSV is current and essentially complete** (§2). Every
   months-long zero-op block at every one of the 10 coal plants is in the
   committed extract, including Coleto's 2023 mothball (Jan 1–24 +
   Feb 12–May 1), Limestone LIM2's 141-day Feb–Jun 2024 block, and Sandy
   Creek's 306-day 2025 outage.
2. **The DAM COP plant pin ERASES the windows it disagrees with** (§3). The
   keeper arms `ercot_thermal_dam_availability` + `_coal` + `_hourly` +
   `_plant`: every coal plant is pinned, per hour, to its own COP
   live-HSL/rating fraction through the accepted crosswalk — and the
   water-fill is **bidirectional by design**, so wherever the COP says the
   resource was startable, the pin RESTORES the capacity the window had
   removed. The model then dispatches **4.36 / 4.98 / 5.01 TWh** (2023/24/25)
   of coal **above the measured-window ceiling**.
3. Two genuinely-absent micro-windows and one already-handled destroyed unit
   (§5): immaterial (≤0.15 TWh) and no-action respectively.

## 1. Layer inventory at the seam (the keeper's armed stack)

`generators_to_fleet_arrays` applies, in order: statistical availability
(coal POF dropped, `coal_drop_pof`) → **≥ 5-day CAMPD unit windows**
(`unit_outage_derate_factors`; short/unit-partial/maxgen gates OFF in this
keeper) → ERCOT plant-grain partial plateaus
(`partial_outage_derate_factors`) → CAMPD-blind gas caps (gas-only) → **the
DAM COP rescale** (class-hour water-fill, coal included via ERCOT-110;
plant-grain pin via ERCOT-97 for every crosswalked plant — all 26 coal
sites → all 10 plants), ceilinged only by `BIN_FORCED_DERATE_BY_YEAR`
(ERCOT-137). The DAM layer is applied **last**, so on any conflicted hour it
wins.

## 2. Phase 0 reconciliation — the windows are not the problem

Per unit × year, CAMPD zero-op spells (gross == 0 on the zero-filled hourly
grid, ≥ 5 days — the derive's own clock convention) vs the committed
extract's day-granular `[start, end+1d)` masks
(`ercot148_coal_outage_phase0.json` `spells`):

- **59 of 62 spell-rows ≥ 5 days are 100 % window-covered** across the 10
  plants × 2023–2025.
- The three exceptions: Martin Lake 1's full-2025 silence (§5.1), J K Spruce
  **2 2025-01-25..31 (5.5 d), Major Oak U2 2025-03-01..07 (6.3 d) (§5.2).
- Staleness is REFUTED: a frozen-derive re-run for 2025 on today's source
  reproduces the committed extract exactly once the committed layup
  companion is added back (655 standard + 415 layup = 1,070 = the no-guard
  re-run's row count) — the committed extract is the current script's own
  output (merit-order guard armed), not an old vintage. No coal-bin window
  sits in the layup file (its COAL-labelled rows are all W A Parish WAP1–4,
  the gas-steam units the overlay routes to split code 34702).

## 3. The root cause: OFF-at-full-HSL COP filings override certified dead stops

The site-hour series the plant pin consumes counts an `OUT` resource as 0
and an `OFF` (uncommitted-but-startable) resource **at its reported HSL** —
"commitment state is not an availability event"
(`derive_ercot_thermal_dam_availability.py`). That convention is correct
for load-following gas. On the coal fleet's long dead stops it collides
with the window layer's own frozen identification (`outage_detect`
FULL_STOP_OVERRIDE: *"economic idling backs down but rarely fully STOPS
for weeks — a sustained, weeks-long CF≈0 dead stop is the
mechanical-outage signature"*), and the raw disclosure rows show the
collision is plant-specific COP filing behaviour, exactly matching the
directive's control observation:

| resource, dead-stop window | COP rows during the CAMPD zero-op block |
|---|---|
| COLETO_COLETOG1 2023-01-01..24 | 514 h `OFF` @ 655 MW, 62 h `OUT` |
| COLETO_COLETOG1 2024-02-14..04-16 | 1,067 h `OFF` @ 649, 444 h `OUT` |
| LEG_LEG_G1 (LIM1) 2023-02-07..28 | 504 h `OFF` @ 793, 24 h `ON`, 0 h `OUT` |
| WAP_WAP_G5 2024-01-23..04-06 (74 d) | 1,677 h `OFF` @ 657, 72 h `OUT` |
| LEG_LEG_G2 (LIM2) 2024-02-02..06-22 | 2,855 h `OUT`, 552 h `OFF` (mostly honest) |
| SCES_UNIT1_J01 (Sandy) 2025-04-24..12-31 | 5,953 h `OUT` — **honest; the control** |

**Dispatch-level proof** (byte-identical 2023 keeper replay): Coleto
dispatches 0.216 TWh at a 591 MW peak inside its windowed Jan block and
runs at **full 622 MW nameplate** inside the windowed Feb–Apr mothball;
Limestone peaks at **1,653 MW** during LIM1's Feb dead stop against a
windowed ceiling of 957 MW; Sandy Creek's one COP-dishonest spell
(Jan 2023, `OFF` @ 0.968) leaks the same way (0.187 TWh @ 562 MW peak) —
its other spells are COP-`OUT` and stay dark. The failure tracks the QSE's
COP filing, not the plant, the crosswalk, or the derive.

**Quantification** (keeper payload hourly `m` series, decode verified 1.0000
correlation against the replay dispatch): coal dispatch **above the
measured-window ceiling** (≥ 5-day unit windows × plant-grain partials) =
**4.36 / 4.98 / 5.01 TWh** (2023/24/25), concentrated: Limestone
1.11/1.12/1.49, W A Parish 1.06/1.28/1.12, J K Spruce 1.14/0.45/0.96, Oak
Grove 0.07/0.84/0.76, Coleto 0.40/0.41/0.19, Martin Lake 0.20/0.50/0.25,
Sandy Creek 0.27/0.32/0.06 (per-plant-year table:
`ercot148_coal_outage_phase0.json` `phantom_twh_by_plant_year`).

## 4. Phase 1 adjudication (per window class)

**4.1 The pin-restore collision is a wiring/precedence DEFECT between two
incumbent measured layers — fix it (Phase 2).** Admissibility: the ≥ 5-day
windows are the canonical rule-13 measured input (the
backcast-measured-data audit's own "canonical allowed case"), and their
identification is frozen (rule 23). The COP `OFF`@HSL rows are a QSE's
*declaration* of startable capability; the CEMS record plus the frozen
full-stop doctrine certify the capacity was physically not delivering for
weeks. Rule 14's misalignment clause governs: when two measured
instruments conflict, prefer the physical record and document the
misalignment — never let a paper declaration resurrect a certified dead
stop. Rule 19: the fix is a **reconciliation of the two incumbents** (a
`min()` precedence at the seam), not a new mechanism, no new floor, no new
cap layer. The DAM overlay keeps its designed job — replacing the
statistical stack — everywhere the window family is silent (factors are 1.0
outside windows), and its **remove** direction is untouched everywhere.
Zero fitted parameters; nothing is tuned to any residual. Forward story:
both layers are backcast-only overlays; forecast years keep the
statistical stack (the G4 mode-aware seam), unchanged.

The fix is **coal-scoped** because the coal detector's averaged-rule
identification is what certifies dead stops as mechanical; for
load-following gas, `OFF`-is-available is genuinely correct and the
symmetric question (a CC with a committed event-based dead-stop window AND
a COP `OFF`@HSL) is left **explicitly open** — it needs its own
measurement before any arm (see §6).

This is NOT CEMS pinning: the cap is an availability ceiling from the
already-admissible window overlay; dispatch below it stays fully free (no
unit is floored to observed generation, no output is rescaled to actuals).
The phantom it removes is capacity the plant's own CEMS proves was not
there — rule 14's "estimate silently compensating" pattern, unwound.

**4.2 Purely economic shutdowns are NOT being stamped "outage".** The
extract was derived with the merit-order guard armed: windows the unit
spent ≥ MERIT_OOM_FRAC out of merit are already reclassified to the layup
companion (which no loader reads), and zero coal-bin windows sit there.
The two micro-spells the standard extract excludes (§5.2) are excluded by
the frozen identification chain itself (in-merit/override specifics) on
current source data — recorded, not re-tuned (rule 23; no threshold moves,
`UNIT_OUTAGE_MIN_DAYS` untouched).

**4.3 Coleto Creek's seasonal operation.** The 2023 (Jan–Apr) and 2024
(Feb–Apr) blocks match Coleto's publicly announced seasonal-operation
posture ahead of its announced retirement; whatever the instrument's exact
form, the *identification here does not rest on it* — the frozen full-stop
doctrine certifies the blocks from the CEMS record alone, and the windows
already sit in the committed extract. The instrument citation strengthens,
never carries, the ruling.

## 5. Side findings (no action this lane)

**5.1 Martin Lake unit 1, 2025** — CEMS-silent all 8,760 h AND COP `OUT`
all 8,760 h @ 815 MW. The window derive cannot see a whole-vintage-absent
unit (no run/stop transition) and the DAM deriver's **same-year p98 rating
basis** yields no rating for an all-year-OUT site → fraction NaN → pin
inert. Already carried by `BIN_FORCED_DERATE_BY_YEAR["N_COAL4"]={2025:
0.67}` (ercot132-checked, explicitly retained; the DAM ceiling honours
it). The rating-basis gap is recorded here as the reason the COP pin
cannot yet retire that registry entry (its own TO-RETIRE note).

**5.2 Two micro-spells** — J K Spruce **2 2025-01-25..31 (5.5 d, 0.12 TWh)
and Major Oak U2 2025-03-01..07 (6.3 d, 0.03 TWh) are absent from the
standard extract AND the layup file, and a current-source frozen re-run
reproduces their absence — the exclusion is the frozen identification's
own outcome, not staleness. Immaterial at 0.4 % of the phantom;
recorded, not forced.

## 6. Explicitly open (successor questions, NOT armed here)

1. **The gas-side symmetric collision** — committed CC/ST dead-stop windows
   vs COP `OFF`@HSL: size unmeasured; needs its own audit before any arm
   (this lane is coal availability only).
2. **The DAM deriver's rating basis for all-year-OUT sites** (§5.1) — a
   multi-year rating fallback would let the pin carry destroyed units and
   retire the `N_COAL4` registry entry; rule-23 derive change, own lane.
3. The remaining per-plant residual **outside** the windows (Coleto's
   +41 %/2025 is mostly loading conduct, ERCOT-126's 90–93 % LOADING
   finding) — the C1/C7-adjacent dispatch-shape object, distinct from
   availability and already part-attributed by ERCOT-126/142/143.

## 7. Decision

Phase 2 is LICENSED: arm `ercot_dam_availability_coal_event_cap`
(default-off ScenarioConfig gate + matrix row, rule 26c) as a single delta
off `ercot145_gas_daily_arm`, full span 2023–2025, precommit pushed before
the solve. Zero fitted parameters (a precedence rule between two measured
instruments) ⇒ structurally LOYO-exempt, with the per-year guard table
standing in (the ERCOT-145b precedent). Ex-ante predictions and guards:
the precommit.
