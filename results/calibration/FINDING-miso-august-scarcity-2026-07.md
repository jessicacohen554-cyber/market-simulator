# FINDING — MISO August scarcity jump: temp-derate + a silent config regression (2026-07-10)

**Thread:** owner question — "somewhere around run 48-50 we started to get an August scarcity
price jump in MISO that has been there since, but is not reflected in actual price formation.
Fresh look at MISO calibration; major issues and a path to a calibrated keeper."

**Answer in one line:** the jump has TWO stacked causes, both now root-caused — (1) miso-49's
`temp_dependent_derate` deletes hot-hour capacity the MISO fleet measurably has (rule-24
own-fleet refutation, third fleet after ERCOT and PJM), and (2) miso-50 through miso-53 were
accidentally solved WITHOUT the entire miso-46..49 keeper structure (reserve co-opt, priced
seam, Manitoba firm imports, intermediate splits) because their drivers replayed the recipe
from `run_config.json`'s curated `calibration_flags` instead of the exhaustive `meta.json` —
MISO ran as an **island**. Fix run: `miso-54` (`_miso54_som_restored.py`).

## 1. The trace (dashboard payloads, load-weighted monthly means vs bench `da_mon`)

August model−actual delta ($/MWh) by run:

| run | Aug 2023 | Aug 2024 | Aug 2025 | note |
|---|---|---|---|---|
| miso-46 seam-ladder (keeper line) | −1.3 | −2.3 | −6.4 | clean |
| miso-47 steamgas-ct | −1.4 | −2.3 | −6.0 | clean |
| miso-48 stgas-srmc | −1.4 | −2.3 | −5.9 | clean |
| **miso-49 tempderate (KEEPER)** | −0.1 | **+12.3** | −5.2 | jump appears (2024) |
| **miso-50 coalsigmoid** | **+25.5** | **+27.8** | −2.7 | explodes (2023+2024) |
| miso-51 gasdaily-hydro | +25.3 | +27.6 | −4.3 | persists |
| miso-52 sigmoid-monthlykey | +25.3 | +27.5 | −4.3 | persists |
| miso-53 somcoal | **+28.6** | **+32.5** | −2.7 | worsens |

The owner's "around run 48-50" is exactly right: onset at 49, amplification at 50.

## 2. Hour-level forensics (payload `lmpDeltaHr` + measured RT hub-mean)

The whole monthly jump is a handful of near-$2,000 modelled hours (miso-50..53 spike hours are
byte-identical — the coal-offer changes never touched them):

- **Aug 24 2023 HE14-18** (the real MISO record-peak / maxgen day): model $1,965-2,002 vs
  actual RT $47-213. Plus Aug 3 + Aug 23 afternoons at $220-450 vs $45-143.
- **Aug 25 2024 HE13-19 + Aug 26 HE16** (the real late-Aug-2024 heat event, one day early):
  model $1,579-1,977 vs actual RT $10-148.
- 2025 never overshoots (model **undershoots**: 11-31 modelled RT-like hours >$200 vs 88
  actual; July 2025 mean −8 to −16 low across runs).

Depth is ~10x wrong and timing is midday (HE13-18) where the real spikes are early-evening
(HE17-20); the model simultaneously MISSES the real distributed evening spikes (Aug 12 HE17
$393, Aug 20 HE19 $569, Aug 28 HE19 $403 in 2023 — model $6-40 in those hours). So the fix
target is not "no August scarcity" — the events land on real heat days — it is correct
**depth** (available capacity + import support) and correct **evening timing**.

## 3. Cause 1 — `temp_dependent_derate` (entered at miso-49, in every run since)

Slopes (CC 0.76, CT 1.26, ST_GAS 0.54 %/degC above 15 C; COAL 0.40 %/degC above 25 C —
COAL/ST_GAS applied as RAW additive cuts, no net-summer reshape anchor) delete on the order of
10-15 GW from the MISO thermal fleet at an August-peak hour. In backcast mode the CAMPD
historic-outage overlay already carries the real heat-event outages/derates, so the curve
double-counts on exactly the tightest days.

**Rule-24 own-fleet check (`scripts/probes/_miso_temp_capability_envelope.py`, this session —
the follow-up flagged in the 2026-07-10 pjm-95 demotion entry): the MISO CAMPD fleet REFUTES
the slopes, the same verdict as ERCOT and PJM:**

- p98 capability envelope FLAT in every TMAX bin up to 36-40 C, all three years: CC_REGULAR
  0.990-1.008 (model curve predicts 0.908 at 36-40 C), CT_PEAKER 0.978-1.02 (model 0.837),
  ST_GAS 0.979-1.056 (model 0.936), COAL 0.998-1.041 (model 0.956). (2025 CT 36-40 C cell
  1.286 is a small-reference artifact, above 1.0 either way.)
- Lower bound: COAL — the class taking the raw additive cut, ~55 GW — demonstrates at/above
  its net-summer rating on TMAX>=34 C hours (median max-output/rating 1.040-1.063; 69-79 % of
  capacity proven >=1.00x). CC_REGULAR median 0.996-1.001 with 70-82 % proven >=0.95x.
- Max-incentive scarcity-hour slopes (RT>$200: 8,959 plant-hours; RT>$100: 32,353):
  CC −0.33 %/degC vs model −0.76; CT +0.00/−0.15 vs −1.26; COAL −0.00/+0.14 vs −0.40;
  ST_GAS −0.16 vs −0.54.

By the pjm-95 precedent ("if the fleet refutes the slopes the mechanism exits the keeper the
same way ERCOT's did") the mechanism exits MISO's keeper line. The miso-49 promotion basis
("a real, literature-cited physical mechanism") is invalidated for this fleet; its C3c gains
(0/6/3 h vs miso-48's 0/0/0) were bought with capacity the fleet demonstrably has — rule 1's
"right number, unreal mechanism".

## 4. Cause 2 — the miso-50..53 config regression (the amplifier)

`_miso51/52/53` probe drivers (and the miso-50 launcher) rebuilt "the miso-49 keeper recipe"
from `run_config.json` → `calibration_flags` — the **curated subset** that
`_miso_tempderate_ab.py`'s own docstring warns "is missing several MISO structural flags this
keeper turns on". `_miso_tempderate_ab.py` replays `meta.json` (the exhaustive record) with a
signature check precisely to avoid this trap; the -50..53 drivers did not. Silently dropped in
every run since miso-49 (verified in all three of `meta.json`, `run_config.json:scenario_config`,
and the solve logs — miso-53's log has ZERO seam/import/interchange lines vs miso-48's 34):

| dropped | what it is |
|---|---|
| `energy_reserve_coopt` + `miso_zonal_reserves` + `miso_reserve_pergen` | the whole MISO reserve co-optimization (keeper structure since miso-39), incl. the published zonal RDC steps ($200/$1100/$3300) |
| `reference_price_interface` + `miso_seam_measured_ladder` + `miso_seam_flow_limit` + `miso_seam_export_limit` + `miso_pjm_border_anchor` | the entire measured priced seam (the reason miso-46 was promoted) — MISO ran as an island |
| `miso_firm_imports` | Manitoba Hydro firm must-flow block (~10-15 TWh/yr into MISO-West) |
| `miso_zonal_gas_basis` | zonal delivered-gas basis |
| `ct/cc/st_gas` intermediate splits (+ bundled `gas_st_startup_cost`, NERC-GADS `gas_st_wefor_base_override=0.10`) | offer-curve/availability structure from the miso-45..48 line |
| `coal_econ_srmc_bound` | the miso-42 measured-SRMC bound |

Islanding a structural net importer forces the import energy onto domestic coal/CC and removes
the peak-day import buffer: August ignites in BOTH 2023 and 2024 and every miso-50..53
conclusion is drawn on a degraded surface. Specifically contaminated: miso-50's "grounding the
sigmoid worsens coal over-run" A/B (claimed "ONE change" vs miso-49 — actually 17), miso-52's
monthly-key null result, and miso-53's headline mean-LMP overshoot (+24.2 %/+13.4 %) and
C3a/C3b FAILs, which conflate the SOM offer redesign with the missing seam/co-opt. miso-53's
data-side findings stand: the SOM conduct evidence (offers at cost; self-commitment is a
commitment phenomenon) and the C4 coal dispatch-shape all-pass are premise-level results.

## 5. The fix — miso-54 (`scripts/probes/_miso54_som_restored.py`, this session)

miso-49 `meta.json` replay (same RENAME + signature-check machinery as
`_miso_tempderate_ab.py`) with exactly two deliberate changes vs the miso-49 keeper recipe,
plus the measured intake fixes:

1. `temp_dependent_derate=False` — rule-24 own-fleet refuted (§3).
2. Coal sigmoids OFF on the HEAD SOM-grounded `_MISO_OFFER_CURVE` bands — the miso-53
   redesign, now measured on the full structure.
3. `hydro_backfill_year=2024` + `hydro_eia930_monthly=True` (miso-51/53 measured hydro);
   `gas_daily_shape` is code-resolved ON for MISO at HEAD.

Zero-forcing ablation twin per rule 20. Results section to be appended on completion; the
run registers on the dashboard either way (rule 15).

## 6. Keeper-path recommendation (post-miso-54 lanes, in order)

1. **Demote/replace miso-49** — it carries a refuted mechanism. miso-54 is the natural
   candidate if its gates come back sane (expect: August spikes gone, C3a 2023/24 back near
   miso-49's −2.5/−1.0 %, C4 coal all-pass retained from the SOM redesign, C5a all-pass).
2. **CT_PEAKER hurdle lane (pre-existing, now the top residual):** CAMPD-grounded MISO CT
   committed hurdle + econ ramp (rule-23 derive from the CT heat-rate spread) — the de-leaked
   neutral-1.0 hurdle's predicted over-run (+17/+25 TWh at miso-53) will partially persist on
   the restored structure since it's an offer-curve property, not a seam artifact.
3. **C3c depth/timing (the real scarcity lane):** with the co-opt restored, scarcity prices
   through the measured RDC steps instead of the raw stack top. The remaining 2025 undershoot
   (88 actual RT>$200 h) is the documented RDC/ELMP representation gap (RT-vs-DA dual basis)
   — treat via the C3c DA-expressible scoring frame, not by re-adding capacity deletions.
4. **Governance guard:** recipe replays must source `meta.json`, never `calibration_flags`
   (this finding is the second bite of that trap — consider making
   `run_calibration_full.py --replay <bundle>` the only sanctioned path).

## 7. Files

- `scripts/probes/_miso_temp_capability_envelope.py` — rule-24 own-fleet check (COAL included).
- `scripts/probes/_miso54_som_restored.py` — the corrected keeper-candidate driver.
- `results/calibration/miso54_som_restored*/` — bundles (main + ablation twin).
- Forensics reproduced from committed dashboard payloads (`frontend/data/backcast/runs/*miso*.js`)
  + `bench/MISO/*.json.gz` + `data/raw/lmp-data/MISO/miso_hub_lmp_{2023,2024}_rt.csv.gz`.

## 8. RESULT (appended 2026-07-11 — miso-54 solved, registered)

Registered: **`2026-07-10-miso-54-som-restored`** (bundle
`results/calibration/miso54_som_restored`) + rule-20 zero-forcing twin
**`2026-07-11-miso-54-som-restored-ablation`**.

**The August artifact is GONE.** Aug 2023 delta −0.0 $/MWh (model $34.4 vs actual $34.4),
Aug 2024 −0.5 ($31.6 vs $32.1); 0 modelled hours > $200 and 0 slack hours in any year (vs
miso-53's +28.6/+32.5 monthly deltas on ~$1.9-2.0k midday spike plateaus).

**The miso-53 C3a 2023/24 overshoots were the islanding, not the band levels:** miso-54 reads
−1.6 % (2023) / −5.4 % (2024) DA-diagnostic vs miso-53's +24.2 %/+13.4 % — so the "legacy
≥1.0 band levels" lane loses its headline evidence and shrinks to the C1 mid-merit split
below. C4 dispatch-corr PASS retained (the SOM redesign's structural win), C3b 2023/24 PASS,
C1 CT_PEAKER-2023 back in band, C2-2025 improves to gas −9.9 %/coal +7.7 % (was −14.7/+16.3
at miso-49).

**Honest NOT-YET FAIL set (rubric v2.4), one shared root + one lane:**

- C1 (COAL_BIT −16.3/−15.4 TWh, CC_REGULAR +8.7/+8.8, CT_PEAKER 2024 +15.3), C5a CO₂
  2023/24 (−11.1 %/−10.3 %), C2-2025 — near-cost bituminous loses mid-merit to the
  unhurdled neutral-1.0 CT committed band: the pre-documented **CAMPD-grounded MISO CT
  hurdle lane**, now at clean magnitudes (the islanded run overstated it ~2×).
- C3a-2025 −14.7 %, C3b-2025 0.200, C3c 0 h all years (DA actual 1/24/38 h) — the honest
  scarcity-representation undershoot (**RDC/ELMP lane**), no longer maskable by deleted
  capacity. The co-opt's published RDC steps ($200/$1100/$3300) are in the LP; what's
  missing is engagement depth/timing (evening net-load peaks), not a capacity deletion.

**Zero-forcing twin:** near-identical (every class < 0.3 TWh except CT_PEAKER +0.53/+0.35
TWh 2023/2025 — the evening reliability-deployment window). Floors are commitment
scaffolding on this surface; the fit is carried economically.

**Recommendation to owner:** promote miso-54 over miso-49 (rule 1 — miso-49 carries a
mechanism its own fleet refutes; miso-54 is the same structure without it, plus the
SOM-grounded coal conduct). Then run the two lanes in order: (1) CAMPD-grounded CT
committed hurdle + econ ramp (rule-23 derive), (2) RDC/ELMP scarcity depth/timing. Prune
note: `2026-07-06-miso-41-v2rescore-probe` displaced (16th main; no-solve rescore duplicate
of miso-41).
