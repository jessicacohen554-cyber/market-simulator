# FINDING — CAISO seam-clock forensics: the 07-07 seam-diurnal attribution was a timezone artifact; the corridor envelope was mis-phased in the LP; the C3a body reattributes to belly gas commitment (2026-07-07, W3a lane)

**Supersedes:** `FINDING-caiso-seam-diurnal-2026-07-07.md` **§2 (the flow-shape attribution),
§5 (the pre-registered fix prediction)**, and every register sentence derived from them
(G-15 "re-attributed to the WECC seam diurnal shape", G-20d "root cause relocated", G-61
"the seam's midday under-import starves the release signals"). The earlier FINDING's §1
(hod-λ overshoot table), §3's reserve-scarcity/offer-band adjudications, and §4's
observation that the DSW_solar_PV firm block runs at night all survive (frame-consistent).
**Basis:** exact-reproduction forensics on `data/raw/CISO_region.parquet`,
`data/raw/CISO_fueltype.parquet`, `data/raw/eia-930-interchange/CISO interchange
hourly.parquet`, `data/raw/eia-930-hourly/CISO hourly.parquet`, the OASIS SLD_FCST
January-2023 pull, and two byte-faithful HEAD replays of the caiso-60 keeper recipe
(`caiso61_replay_seamw3a` base arm; `caiso65_seam_envelope_clock` fix arm). Every offset
below is measured (lag-scan correlations quoted), not inferred.

## 1. Layer 1 — the 07-07 FINDING's "measured actual" table was UTC-bucketed

The 07-07 FINDING §2 "actual" column reproduces **to the MW** as the hour-of-day mean of
net import (−TI) bucketed on the **UTC hour** of the EIA-930 `period` timestamp
(2023: UTC-hod h0/h12/h19/h21 = 948/5,131/669/200 vs the FINDING's 955/5,131/669/200;
2024 and 2025 reproduce identically). The model column in the same table is on the model's
local clock (the LP has no UTC — the base replay reproduces it exactly), so §2 compared
frames 7–8 hours apart. The "evening collapse to 0.2–1.9 GW" was the Pacific **midday**
collapse wearing a UTC label; the "+2–3.2 GW evening over-import" and "−1 to −1.8 GW
midday under-import" were artifacts of that comparison, and §5's fix prediction (price out
evening imports, feed midday) points the wrong way in both segments. Annual-TWh
cross-checks could not catch this (annual sums are timezone-invariant).

## 2. Layer 2 — which clock is true, and which files are off it

Absolute anchors, convention-free:

- **Solar astronomy:** January CISO solar must be strictly inside wall [07:15, 17:10).
  The model's hourly frame (the `eia-930-hourly/CISO hourly.parquet` extract row clock,
  which feeds demand, the wind/solar HSL profiles, `caiso_solar_fraction`, and the C1
  benchmarks) has January solar nonzero exactly on hods {7..16} — **wall-true**.
- **The 2024-04-08 partial eclipse** (max over CA ≈ 11:12 PDT): the extract frame's
  deepest solar hour lands exactly on hod 11 — **wall-true in PDT too**.
- **Lag scans** (best-lag correlation, 2023–2025): the per-DIBA interchange parquet's
  `local_time` stamps lag the model clock by **1 h in standard time** (best lag −1, corr
  0.972 vs 0.930 runner-up) and **2 h in daylight time** (best lag −2, corr 0.961 vs
  0.919). `CISO_region.parquet` / `CISO_fueltype.parquet` `period` timestamps share the
  same late frame (per-DIBA ≡ region TI at lag 0, corr 0.9957, MAD 13 MW). Consistent
  with prevailing-local hour-ending stamps whose DST offset was applied twice at fetch
  time (both files predate `scripts/fetch_eia930_interchange.py`).

Consequences inside the repo:

- **The keeper's corridor deliverability envelope was mis-phased in the LP.**
  `measured_corridor_flow_envelope` bucketed (month × hod) on the per-DIBA stamps
  directly, so every cap arrived 1–2 h late against the model's wall-true clock: the
  midday-collapse cap reached the LP at model hours ~13–17 instead of the true belly,
  and the overnight-loose cap bled into the morning. **Fixed this session** at the read
  seam (`eia_loader._caiso_interchange_model_clock`, constants
  `_CAISO_INTERCHANGE_LAG_STD_H = 1` / `_CAISO_INTERCHANGE_LAG_DST_H = 2`), guarded by
  `scripts/validate_caiso_seam_hod_frame.py`, which re-measures the lag from source and
  fails if it ever stops matching the pinned constants (so a re-fetched parquet with
  honest stamps cannot be silently double-shifted). A/B: §5.
- `scripts/derive_caiso_export_cap.py` consumes the same stamps but its committed output
  is a max over (month × hod) buckets — phase-insensitive, no action.
- The MISO per-DIBA file shares the CISO file's manual provenance (README) and its
  consumers should be lag-checked by the MISO lane; the ISNE file was fetched by the
  script (different provenance). The measured-ladder derivations (MISO/NEISO) are
  duration-curve-based — phase-insensitive.
- One residual ±1 h question is **open**: the extract's `Demand` column sits +1 h from
  the OASIS SLD actual-load frame (corr 0.9953 at lag −1 vs 0.885 at 0, Jan-2023) while
  the same extract's generation columns are astronomy-exact. Whether EIA-930 demand and
  generation ride different sub-conventions upstream, or the OASIS SLD label differs, is
  a data-provider question — filed, not resolved here; the model is internally consistent
  either way (demand and renewables ride one clock).

## 3. The true measured seam shape (model clock; guard-script canonical table)

CISO net import, hod means (MW):

| hod | 2023 | 2024 | 2025 |
|---|---|---|---|
| 0 | 5,320 | 5,543 | 6,251 |
| 3 | 5,122 | 5,228 | 5,934 |
| 6 | 3,909 | 4,149 | 4,727 |
| 9 | 1,091 | 1,754 | 2,217 |
| 12 | 228 | 847 | 1,301 |
| 15 | 979 | 1,396 | 1,663 |
| 18 | 4,305 | 4,281 | 4,737 |
| 19 | 4,687 | 4,599 | 4,991 |
| 21 | 5,430 | 5,377 | 5,908 |

The seam mirrors **CAISO's own duck**: a 5.3–6.3 GW overnight base, collapse through the
morning to a ~0.2–1.7 GW belly trough (spring/summer middays go net-EXPORT, PNW corridor
reversing to −0.7 to −1.3 GW), and recovery to ~4.3–5.9 GW through the evening ramp. It is
**not** a neighbor-evening-scarcity pattern: corridor-neighbor net load (EIA-930 BA
demand − solar − wind over the corridor DIBAs) peaks h18–19, exactly while CAISO's
measured draw is *rising*. Price frame (all measured, model calendar): midday PALOVRDE
sits $2–9 *below* CAISO RT (margin ≈ wheel; flows thin because CAISO is long, not because
delivery is impossible); evening h18–20 both hubs sit $3–31 *above* CAISO RT while
3.4–5.0 GW still flows — the evening/overnight base is contracted/self-scheduled
(RA imports, owned shares, EIM transfers), not spot-spread arbitrage; overnight spreads
are ±$2 while 5.3–6.3 GW flows.

## 4. The true model residual (base arm `caiso61_replay_seamw3a`, both sides on the model clock)

Corridor net import, model − actual (GW):

| hod | 2023 | 2024 | 2025 |
|---|---|---|---|
| 0 | −0.6 | −1.8 | −1.8 |
| 6 | −0.2 | −1.0 | −1.1 |
| 9 | **+3.0** | **+2.5** | **+2.9** |
| 12 | **+3.3** | **+2.7** | **+2.9** |
| 15 | +1.8 | +1.0 | +1.7 |
| 18 | −0.5 | −1.6 | −1.9 |
| 19 | −0.8 | −1.7 | −1.4 |
| 21 | −1.3 | −2.3 | −2.1 |

with the per-corridor mix also wrong: the model pins **PNW at its (mis-phased) p95 cap**
in 55–91 % of belly hours and 62–77 % of nights (model +0.4 to +2.1 GW vs a corridor that
actually *exports* midday and imports only 0.6–1.2 GW overnight), while **DSW runs 1.7–3.2
GW short** of its real overnight/evening base with its envelope slack (0–14 % binding).
Three structural facts follow:

1. **Midday +2.5–3.3 GW OVER-import, envelope-capped.** The model's belly λ ($37–59,
   gas-CC-marginal) towers over delivered import cost, so the LP imports to whatever the
   envelope allows (DSW belly binding 56–66 %, PNW 55–91 %). Reality clears 0.2–1.7 GW at
   λ $13–33 — an interior solution. The model's midday import excess is a *symptom* of an
   inflated internal belly price, not a seam capability error.
2. **Overnight/evening −0.6 to −2.3 GW UNDER-import, price-gated (not envelope-gated).**
   The model's non-firm rungs pay the CAISO-side border LMP + wheel + CARB adder
   (2023 wedges over hub: DSW_CCGT ≈ +$16.2, DSW_CT ≈ +$22.2, scarcity ≈ +$20.1/MWh at
   the measured $33.03 CARB allowance). In the evening the measured border LMP *alone*
   exceeds the model's own λ (real evening congestion premium), so the spot ladder
   structurally deletes the 3.4–5.9 GW contracted/self-scheduled base reality delivers —
   the same signature as MISO's G-23 import starvation ("firm/scheduled base which
   spread-gated arbitrage structurally deletes"), here gated by the self-referential
   border price instead of a hurdle. The firm blocks (2.3–3.4 GW, DMM-grounded) are the
   only price-taking depth and are undersized relative to that base.
3. **The C3a body does NOT belong to the seam.** With both sides on the model clock, the
   component table shows model solar ≈ measured solar (the earlier "evening solar cliff"
   was a frame misread of the fueltype file — the model's HSL profiles are
   eclipse-verified wall-true), but **actual CAISO runs 3.1–5.2 GW MORE gas through the
   belly than the model** (h9–15: actual 8.4–10.9 GW vs model 5.3–6.4 GW; nights ≈ equal)
   while printing $13–33. Reality's belly is a committed-gas *surplus* (min-load CC/cogen
   /local-reliability/AS-holding units riding through, pushing the margin to
   curtailment/import prices); the model's belly is an exact-fit dispatch whose marginal
   unit is an economic gas tranche at $37–59. The midday λ overshoot (+$18–35, C3a's worst
   bucket) is therefore a **belly commitment posture** gap — G-61's lane, with its sign
   inverted (the RA bridge is directionally *right* and, if anything, thin; note
   `caiso-63`'s startup-aware bridge REMOVES belly min-load energy and moved λ *up*
   +$0.30–0.46 — away from actual — exactly as this reattribution predicts).

## 5. A/B — the envelope clock fix (`caiso65_seam_envelope_clock`, single-delta at HEAD)

Same recipe, same code except the envelope clock; both sides scored on the model clock.
Corridor-flow error (model − actual, MW at hod; **mean |Δ| over all 24 hods**):

| year | mean \|Δ\| base → fix | h9 Δ base → fix | h12 Δ | h15 Δ | h18 Δ |
|---|---|---|---|---|---|
| 2023 | 1,402 → **1,362** | +3,014 → +2,506 | +3,262 → +2,974 | +1,842 → +2,252 | −524 → −20 |
| 2024 | 1,803 → **1,692** | +2,534 → +1,914 | +2,688 → +2,519 | +1,019 → +1,301 | −1,553 → −1,260 |
| 2025 | 1,979 → **1,816** | +2,902 → +2,232 | +2,879 → +2,547 | +1,657 → +1,934 | −1,876 → −1,730 |

The improvement concentrates exactly at the phase edges a 1–2 h correction should move:
the morning-shoulder over-import (h9: −508/−620/−670 MW of phantom import) and the
early-evening under-import (h18: +504/+293/+146 toward the real base) shrink in all three
years; h15 gives back a little (the corrected envelope is honestly looser there — the
mis-phased cap had been lending h15 the true-h13/h14 collapse values). λ moves ±$0.0–0.8
by hod (2023 SP15 hod-mean λΔ +25.2→+25.2 at h0, +34.5→+34.8 at h12, +20.6→+20.4 at h18)
— the pre-registered expectation: the envelope was rarely the *price*-setting object, and
the body inflation is internal (§4.3). Verdict-tier metrics (C-gates, D-2 forced shares)
are computed at registration in CI and recorded on the run's dashboard entry; the fix is
kept on correctness regardless (rule 14) — the measured envelope now caps the same
physical hour the LP dispatches.

## 6. What this means for the open gaps

- **G-15 (drag retirement):** the "seam fix reopens the evening premium → the drag's
  scarcity-pricing half retires" story is withdrawn. The evening premium is missing
  because the **body** is inflated; the body's worst bucket is the belly commitment
  posture (§4.3). Admissible next steps, in leverage order: (a) ground the real belly
  gas commitment (cogen/OTC/local-RMR/AS-holding — measured drivers exist: CEMS belly
  min-load patterns, CAISO must-offer/exceptional-dispatch records), (b) the seam's
  contracted evening/overnight base (§4.2 — measured objects: DMM RA-import capacity
  [already the firm blocks' basis, undersized vs the revealed 4.3–5.9 GW base], EIM
  transfer volumes, CARB specified-source imports), (c) only then re-examine what the
  drag still carries.
- **G-61:** the coupling claim reverses. The model already over-imports midday and still
  never curtails; path (c)'s curtailed-VRE release is starved by the *internal* belly
  balance (and by the belly gas DEFICIT vs reality), not by seam under-delivery. Path
  (b) startup-aware (`caiso-63`) reduces belly commitment — the measured comparison says
  that direction is wrong for CAISO's belly; its adoption decision should weigh §4.3.
- **G-20d:** "root cause relocated to the seam" is withdrawn; the reserve-channel
  inertness findings (caiso-59/61/62) stand untouched.
- **Rule-13 postscript:** the mission this session was commissioned to build — an
  evening neighbor-scarcity export-withdrawal envelope — would have tuned the model
  toward the UTC artifact (real evening flows RISE into the neighbors' peak). It was
  correctly not built. The corrected fix directions above are all measured-first.

## Files
- Base arm: the registered `2026-07-07-caiso-61-lolp-tail` recipe, re-solved at HEAD as
  `caiso61_replay_seamw3a` for hourly instrumentation (local-only bundle; its corridor
  hods reproduce the 07-07 FINDING's model column exactly, confirming recipe fidelity —
  the registered caiso-61 is the base arm's dashboard identity).
- `results/calibration/caiso65_seam_envelope_clock/` — envelope-clock fix arm
  (registered).
- `scripts/validate_caiso_seam_hod_frame.py` — the frame guard (lag constants + duck
  orientation).
- `src/market_sim/data/eia_loader.py` — `_caiso_interchange_model_clock` + constants.
- `FINDING-caiso-seam-diurnal-2026-07-07.md` — superseded in §2/§5 (banner added).
- `docs/gap-register-2026-07.md` G-15 / G-20 / G-61 — corrected rows;
  `docs/calibration-log.md` — W3a correction entry.
