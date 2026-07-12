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

## 9. LANE 1 EXECUTED (2026-07-11 — miso-55 ct-faststart): the static CT hurdle
hypothesis REFUTED on MISO's own fleet; the commitment cost priced by ELMP
fast-start amortization instead

**The measurement came first (rule 23), and it overturned the §8 lane-1 framing.**
`derive_campd_marginal_hr.py --iso MISO` (2023-2025 pooled, n=249 CT units,
cap-weighted; provenance `data/raw/reference/miso_campd_marginal_hr_summary.csv`)
measures the MISO CT min-load block's average-HR premium at **1.025** [p25 0.94,
p75 1.14] over class base — NOT a 1.55-style hurdle — and the CT marginal
(incremental) HR **flat-to-FALLING** with load (0.697/0.687/0.691
committed/lo/hi), the same result NEISO measured on its fleet (2026-07-06 entry)
and NYISO's run-28 saw (CT marg 0.66-0.85x). Heat-rate physics supplies ~+2.5%
at min load and no rising econ ramp: re-arming a large static committed
multiplier would have been residual-fitting with a measurement veneer (rules
1/13). What the de-leaked 1.55 was actually proxying is the **commitment-cost
component** of a real CT offer — start + no-load recovery — which is not a
heat-rate multiplier at all. MISO's own price formation (ELMP, FERC Order 825
fast-start pricing) folds exactly that component into the LMP.

**miso-55 = miso-54 meta.json replay + two deliberate changes** (probe driver
`scripts/probes/_miso55_ct_faststart.py`, strict replay — errors on unmapped
keys):

1. `_MISO_OFFER_CURVE["CT_PEAKER"]` at HEAD: committed 1.0 → **1.025**
   (measured), econ bands **measurement-affirmed neutral 1.0**.
2. `tranche_startup_amortization=True` + `tranche_startup_measured_runs=True`:
   the existing Order-825 lever (NEISO keeper carries v2; NYISO probes validated
   v3) on a new rule-23 artifact `campd_ct_run_lengths_MISO.csv`
   (`derive_campd_ct_run_lengths.py --iso MISO`: 95 plants, median start-to-stop
   runs 3-17 h, class fallback 10 h over 61,322 measured runs). NREL
   CT_STARTUP_PARAMS start costs over measured horizons ⇒ engaged CT econ/peak
   markup ≈ **$1.9/MWh cap-weighted median** (p75 $2.7, max $9.5). Zero fitted
   scalars.

**RESULT (registered `2026-07-11-miso-55-ct-faststart` + zero-forcing twin
`...-ablation`).** NOT-YET (rubric v2.4) but strictly dominates miso-54 on both
structure and score, with zero new fitted scalars (DOF residual count 3→2):

- **C3b price-duration shape flips FAIL→PASS all years** (the miso-54 2025
  0.200 NRMSE FAIL clears — the fast-start markup restores the mid-curve).
- **C1: 6 → 4 class-year FAILs.** CT_PEAKER-2024 +15.29 → **+8.51 TWh**;
  CT-2023 lands **+0.3 TWh** (near-exact vs actual 25.4); COAL_PRB-2024
  −10.50 → −8.0 (back in band); ST_GAS-2024 −6.1 → +1.9. Remaining:
  COAL_BIT −15.3/−14.4 and CC_REGULAR +9.0/+9.1 — the pre-flagged CC/coal
  mid-merit split (CC flat measured econ body + import under-run), now THE
  C1 residual, no longer masked by the CT over-run.
- **C3a-2025 −14.7 % → −13.3 %** (2023 +0.1 %, 2024 −3.3 % DA-diagnostic);
  C3c unchanged (0 h >$200 vs DA 1/24/38 h) — the RDC/ELMP Lane-2 item.
  C2-2025 gas −11.0 %/coal +8.8 % (was −9.9/+7.7): the 2025
  coal-over/gas-under regime absorbs part of what the CTs shed — Lane-2's
  scarcity/AS price formation is what the 2025 merit inversion is waiting on.
- **C5a CO₂ ≈ unchanged** (−11.0/−10.2 % vs −11.1/−10.3): the CT→coal/steam
  reallocation is roughly carbon-neutral; C5a belongs to the COAL_BIT/CC
  split, as predicted in the probe's pre-commitment.
- **August artifact stays cleared** (Aug 2023/24 deltas +0.4/+0.4 $/MWh;
  0 modelled hours >$200 in 2023/24). C4 dispatch-corr PASS retained; C7/C8
  PASS (D-1 CT diurnal r 0.99/0.99/0.92; D-2 CT forced share 3.7–8.1 %,
  cap 15 %). Twin near-identical (CT_PEAKER +0.6/+0.27/+0.47 TWh, all else
  <0.3): the fit is carried economically.

**Recommendation to owner:** promote miso-55 over miso-54 (rule 1: same
structure plus a measured mechanism MISO's real market actually has — ELMP
fast-start pricing — and the measured CT part-load premium; every score
movement is a by-product, none was tuned). Leave-one-year-out evidence: no
parameter in the change was fit to any year (published NREL costs + pooled
2023-25 CAMPD measurements), and the per-year movements are 2023 ✓ / 2024 ✓ /
2025 mixed-but-improved on price. Lane 2 (RDC/ELMP scarcity depth + evening
timing) is next and now carries the 2025 C2/C3a/C3c residual cleanly.

## 10. LANE 2 EXECUTED (2026-07-11 — miso-56 measured-scarcity): the measured
data adjudicates the lane — DA reserve scarcity is ~nonexistent, the flat/static
requirement estimates were wrong both ways, and the 2025 residual's drivers are
measured to live in RDT congestion / RT-only constructs

**The measurement came first (rules 1/23), and it re-scoped the lane.** Three
measured adjudications, all from series already on disk or the IMM's own
publications:

1. **The DA reserve MCPs never price the RDC steps.** `asm_damcp_zonal`
   (MISO Wide, GEN*MCP): 2023 max $25 spin / $20 supp, 2024 max $27/$25, 2025
   one hour at $132 (2025-07-28 HE19). Real day-ahead reserve scarcity is
   ~nonexistent in the train window — so the model's 0 binding RDC hours is
   structurally CORRECT on the C3c DA-expressible basis, and any mechanism
   that forces the in-LP families to bind in DA would fabricate scarcity the
   measured market does not have. Reserve-scarcity pricing lives in the RT
   tail (supp/spin RT MCP ≥ $190: ~3-4 h 2023, 8-11 h 2024, 17-19 h 2025 —
   e.g. Aug 12/20 2023 evenings at $230-486), which the DA-anchored score
   deliberately does not chase (the miso-53 RT-companion note).
2. **The DA >$200 LMP anatomy is not reserve-driven.** 2023: 1 h (Aug, $205).
   2024: all 24 h are Winter Storm Heather (Jan 14-17, HE6-8 + HE17-19, max
   $285). 2025: 38 h = July (15) + June (11) + Jan (8) + Feb/Sep/Oct, evenings
   HE15-19 and winter mornings, max $433. These cleared on the energy-offer
   tail (fuel spikes + commitment-cost recovery + emergency constructs), with
   DA reserve MCPs ≤ $27 through all of 2023-24.
3. **The IMM's Summer-2025 quarterly names the 2025 drivers**: RDT S→N
   congestion ($9.31/MWh Midwest-South separation, $41M RDT+RPE congestion —
   the transmission lane, not this one); June 23-24 ELMP *ex-post* emergency
   repricing (2.5× ex ante — an RT-only construct; "MISO did not experience
   operating reserve shortages during these events"); the hour-18 net-load
   ramp (evening ramp demand 1,000 MW 2023 → ~6,000 MW 2025; 26 RT OR-shortage
   intervals, majority HE18 — RT forecast-error events, incl. the July 28
   40-minute shortage). None of these is a DA in-LP reserve-depth phenomenon.

**What Lane 2 honestly supports — miso-56 = miso-55 meta replay + two measured
changes** (probe driver `scripts/probes/_miso56_measured_scarcity.py`):

1. **Measured hourly OR requirements** (`miso_measured_reserve_requirements`,
   new intake `data/miso_reserve_requirements.py` ←
   `asm_rt_cleared_mw_<year>.parquet`). Market-wide RBDC: flat fleet-MSSC+400
   (~3,438 MW) → measured hourly cleared reg+spin+supp (mean 2,447/2,557/2,642,
   max 3,069/3,124/3,295 MW — the event-evening requirement raises MISO
   actually posts, e.g. Aug 12 2023 HE17-20 2,410→2,830 MW, now in the LP at
   the right hours). South zonal: within-zone-MSSC static (~2,196 MW) →
   measured South reservation (mean 321/366/477 MW) — the static basis
   over-withheld South by ~1.8 GW, capacity the real market never held back.
   Rule-13 (measured AS power reservation) + rule-14 (mandatory swap).
   Documented caveats: RT cleared (no DA hourly series exists), cleared <
   requirement in the rare true-shortage intervals; STR excluded (separate
   30-min product).
2. **Condition-keyed fast-start amortization** (`tranche_startup_conditional_runs`,
   v4 of the Order-825/ELMP lever): CAMPD measures MISO CT runs STARTED in
   p97.5+ net-load hours at 6 h median vs 10 h pooled (ratios
   0.9/1.1/1.1/0.8/0.6 across [0-.5/.5-.75/.75-.9/.9-.975/.975+], stable each
   year; `derive_campd_ct_run_lengths.py --condition-bands`, 61,322 runs) —
   the v3 ceiling scales per hour by the band ratio of the hour's within-year
   net-load percentile, so a tight-evening engagement amortizes its NREL
   start cost over the SHORT commitment block it really is (the ELMP
   evening-timing element the monthly grain could not express). P1-only,
   forward-native trigger.

**Pre-committed expectations (recorded before the solve):** correctly-timed
evening CT markup lift (band-4 ≈ +$1-2/MWh — NREL CT starts are $12-25/MW, so
this is timing, not level); South withholding release (direction on South
LMPs down / S→N exports up); market-wide requirement drops ~1 GW in normal
hours (slight softening — accepted per rule 14). July-2025's −18 $/MWh
monthly gap is NOT expected to close: its measured drivers (RDT congestion,
RT-only constructs, hour-18 ramp forecast-error scarcity) are outside this
lane. C3c likely stays ~0 on the DA basis — which the measurement above says
is correct, not missing.

**Deferred with documentation (zero-effect for this window):** MISO's
shortage-pricing redesign effective 2025-09-30 (FERC-approved: Pricing VOLL
$10,000, System VOLL $35,000 scaling a LOLP-based ORDC capped at $6,000 —
Updated Shortage Pricing White Paper, Nov 2024) post-dates every 2025 DA
scarcity cluster (June/July/Jan) and Q4-2025 DA reserve MCPs stayed ≤ $55, so
a year/hour-gated curve re-anchor provably changes nothing in the 2023-2025
backcast. It becomes REQUIRED the moment H1-2026 crossover scoring or a 2026+
forecast leans on the reserve curves; wire it then (ERCOT ECRS-reform date-
gate pattern).

**Next-lane pointers (from the measured adjudication, NOT tuned lanes):**

1. **RDT S→N congestion depth (transmission/seam lane) — QUANTIFIED as the
   largest single measured lead on the 2025 residual.** The miso-55
   payload's 2025 Midwest−South monthly LMP separation (mean of
   Illinois/Indiana/West/Plains minus South) is **$0.19/MWh over Jun-Aug vs
   the IMM's measured $9.31/MWh** (Summer-2025 quarterly) — the RDT
   congestion is essentially ABSENT from the model. With the Midwest
   carrying most of MISO load, the missing ~$9 separation is plausibly
   ~$5-8/MWh of the July-2025 −18.0 monthly delta on its own. Check the
   RDT/RPE contract-path representation (limit level, and whether the S→N
   direction ever binds under 2025's low-wind/low-import summer pattern).
2. The COAL_BIT/CC mid-merit split with the import under-run (the standing
   open root cause).
3. Winter delivered-gas fidelity for Heather-window CTs (Jan 2024's −11.5
   $/MWh monthly delta is the entire 2024 miss).

### §10 RESULT (appended after the solve, same session)

**Registered `2026-07-11-miso-56-measured-scarcity` + zero-forcing twin
`…-ablation` (rubric v2.4: NOT-YET, FAIL set {fuelmix, sysvol, price_mean,
price_tail, co2} — identical to miso-55, every delta flat-to-better):**

- C1: CT_PEAKER-2024 +8.51 → **+8.27 TWh**; CC_REGULAR/COAL_BIT within
  0.04 TWh of miso-55 (the standing mid-merit split, untouched as promised).
- C3a-2025 −13.3 % flat (July-2025 monthly −18.8 vs −18.9 — confirms the
  July gap lives in the RDT/emergency lanes, exactly as adjudicated ex-ante).
- C3c 0 h >$200 all years — the pre-committed, measurement-correct outcome
  on the DA basis. August 2023/24 stays clean (+0.5/+0.2 $/MWh monthly).
- C3b/C4/C6/C7/C8 PASS (D-2 CT forced 3.7–5.9 % vs 15 % cap); C5b the
  ledgered benchmark-basis CAVEAT (+1154.7 % this run).
- Mechanism verification (not score): South LMPs fell −0.1..−1.4 $/MWh (the
  fabricated withholding released); market-wide requirement now carries the
  measured event-evening raises; the v4 markup varies hourly with the
  measured band ratios. Twin near-identical (class-year deltas ≤ 0.3 TWh;
  the twin even sheds the CT_PEAKER-2024 C1 FAIL by dropping the ~1.0 TWh
  evening reliability deployment) — the fit is carried economically.
- DOF ledger: 11 entries, residual count unchanged at 2 (the offer-curve
  legacies); both new mechanisms enter as measured-physical rows.

**Disposition:** miso-56 strictly dominates miso-55 on structural grounding
(two wrong estimates replaced by measured series; the evening-timing element
now exists) at an identical-to-marginally-better score. It is the natural
successor to the miso-55 recommendation — same owner decision pending;
keepers.json untouched. Retention: miso-41-ct-evening (+ twin) displaced
(16th main, oldest first).

## 11. TRANSMISSION LANE EXECUTED (2026-07-11 — miso-57 rdt-congestion): the
RDT now binds at measured frequencies in 2023-24; the 2025 gap is a quantified
UPSTREAM direction-reversal, not a transmission-limit issue

**The sanity chain came first (rules 1/14).** A 2025-only throwaway diagnostic
(miso-56 replay, `scripts/probes/_miso57_rdt_diag.py`, never registered) measured
WHY the model carried ~$0 Midwest–South separation against the IMM's $9.31: the
shared `MISO_external` bus links to all five border zones, so the LP wheeled South
energy South→external→Midwest through the bus's energy balance without touching
any priced band — a fabricated, cost-free 3,000 MW bypass around the RDT contract
path. Measured bypass: **1,255 MW summer-2025 mean** (1,563 of 2,208 summer hours;
7.7 TWh/yr) while the RDT S→N link carried 54 MW mean and saturated **13 h/yr**.

**miso-57 = miso-56 meta replay + two structural changes, zero fitted scalars**
(probe driver `scripts/probes/_miso57_rdt_congestion.py`):

1. `miso_south_seam_split` — the South seam's reference-price bands re-home onto
   their own external zone (`transmission.split_miso_south_external_node`; the
   southern neighbors SOCO/TVA/AECI are electrically south of the RDT). Severs the
   wheel outright.
2. `miso_rdt_tcdc` — the static JOA contract pair (3,000 N→S / 2,500 S→N) becomes
   the published operating representation: 92% default derate ("MISO derates the
   RDT limit to 92 percent of the contract limit by default", 2024 SOM §III.B) as
   the free tier, then the two-step TCDC ($40/MWh at the modeled limit, $500/MWh
   from 102%, hard bound at contract) as priced one-way tiers
   (`TransferLink.flow_cost`, one-way-only validated). Deliberately conservative:
   the 92% DEFAULT derate, not the deeper measured-when-binding 84% (no published
   hourly derate series; rule 13 forbids the haircut), and the RPE ($200, additive
   in real violations) is NOT modeled — both gaps point the same way
   (under-separation).

**RESULT — the mechanism reproduces the measured RDT behaviour in 2023-24:**

| anchor | measured (SOM / facts note) | miso-57 |
|---|---|---|
| 2023 S→N mean flow | 917 MW (§IV.E p.39) | 1,139 MW |
| 2024 S→N mean flow | 1,108 MW (§II.E) | 1,035 MW |
| 2024 binding frequency | >25% of RT intervals (§III.B) | 25% (2,183 h; 2023: 27%) |
| 2024 separation when binding | ~$3/MWh (§III.B) | $2.89 (2023: $2.77) |

Score: 2025 annual C3a **−13.3% → −11.7%** (model +$0.71/MWh; June −6.4, Aug −5.2
both improved), July-2025 **−18.8 unchanged** — exactly as pre-adjudicated in §10
(its drivers are ELMP ex-post/emergency constructs + deeper operator derates +
RPE, none of which this lane fabricates). August 2023/24 hold clean (+0.5/+0.5
monthly). D-2 CT forced 5.8/3.7/8.1% vs 15% cap. DOF ledger 13 entries, residual
count unchanged at 2 (offer-curve legacies); both mechanisms enter as
measured-physical zero-scalar rows.

**The 2025 finding — direction reversal, upstream of the RDT:** in 2025 the model
runs the RDT predominantly N→S (mean 1,350 MW, binding N→S 2,559 h ≈ 29%) with
S→N at only 322 MW mean / 371 binding h (4%) — while the real 2025 market ran
predominantly S→N ($9.31 summer separation, RDT+RPE congestion $41M, +121% YoY).
The model's Midwest is too cheap / South relatively too dear in exactly the hours
reality pulled 2,100+ MW north: this is the standing mid-merit split root cause
(COAL_BIT −15 TWh under-run / CC_REGULAR +9 TWh over-run, import under-run
co-driving) now quantified as a ~1,000+ MW RDT direction reversal. No admissible
transmission-side change can close it (S→N never saturates even the derated
limit in 2025), and rule 1 forbids tightening the limit against the residual.
The $9.31 separation will emerge when the mid-merit lane fixes the upstream
misallocation — the constraint that will price it is now in place and validated
on 2023-24.

**Disposition:** miso-57 supersedes miso-56 (the promoted keeper) on structural
grounding — it removes a fabricated free transfer path and adds the published
RDT market design, reproducing three measured anchors in-window — at a
strictly-better score (2025 +1.6 pts, everything else flat-to-better). Keeper
swap is the owner's call; recommended. Deferred (documented in the attestation):
RPE constraint family; hourly measured RDT limit/flow series intake (MISO posts
RT limit data — a future rule-14 upgrade replacing the 92% static default);
Midwest–South separation as a scored metric.

## 12. MID-MERIT LANE FORENSICS (2026-07-12, pre-miso-59): the scorer-basis
check reframed the lane, and the model-side wedge is a fabricated cold-start
premium on self-committed coal

**Scorer basis first (the miso-58 handoff's mandated first step — G-21b,
calibration-log 2026-07-12).** The C2 preliminary-vintage fallback gated raw
EIA-930 per-fuel cells; the G-21 cross-ISO probe re-run shows MISO 930 books
coal −16.9/−18.0/−20.9 TWh below CEMS (2023/24/25) with the mirror in NG:NG.
Consequences:

- miso-58's C2-2025 FAIL pair (gas −10.1%/coal +7.6%) was substantially that
  swap: CEMS-corrected, 2025 reads coal −2.9% / gas ~−3.3%. **"The model
  over-coals 2025" is FALSE.** (Scorer fixed → sysvol FAIL → commercial
  CAVEAT; keeper re-scored in place.)
- The REAL 2023/24 miss is ~2× the handoff's number: coal family −34/−42 TWh
  vs CEMS (classFull: COAL_BIT −18.2/−17.1, COAL_PRB −9.2/−13.8), mirrored by
  CT_PEAKER +8.8/+16.0 and CC_REGULAR +2.9/+9.4. The handoff's "CC_REGULAR
  +9.0/+9.1" was the pre-G-21 scorer basis; on the corrected basis the
  compensation spreads across CT_PEAKER (larger) and CC.

**Model-side forensics (replayed miso-58 2023 solve, on/off LMP crossing
points — an LP price-taker runs iff LMP ≥ mc):**

| band | crossing | static measured-fuel SRMC | wedge |
|---|---|---|---|
| CC_REGULAR committed+econ | always-on (< $20.6 LMP floor) | ~$17-24 | — |
| COAL_PRB committed (11.0 GW) | $34.6 | ~$26 (F923 $2.2-2.3/MMBtu) | **+$8** |
| COAL_BIT committed (3.8 GW) | $43.8 | ~$29-31 | **+$13** |
| COAL_PRB econ | $32.0 | ramp top ~$30 | ~0 |
| COAL_BIT econ | $36.4 | ramp top ~$34 | ~0 |

The wedge is `compute_monthly_markup`'s $100/MW cold-start amortization
(committed band only, raw P0 run lengths, no measured ceiling; a no-run month
amortizes over 1 hour) — applied while the SAME plants' fuel-free mustrun
bands hold their boilers ONLINE 84-98% of hours in the same solve. A hot
boiler's committed band is an output ramp, not a cold start. And the IMM's
measured conduct (miso-53 SOM adjudication) prices MISO offers AT cost
(system markup +3.0%/−2.5%) — the fabricated premium contradicts the
measured market; self-committed units recover start costs outside the
energy offer.

**Fix = miso-59 (`coal_warm_committed=True`, existing gated exemption, zero
new parameters).** The ERCOT 98a/98b rejection of the same flag was
ERCOT-shaped (their 2023 coal already calibrated; their CT/ST under-running
were stolen from) and does not cross the ISO boundary — MISO's measured
residual is its exact mirror in both years and both directions.

**RDT-2025 linkage (§11 continuity).** With the 2025 family miss reframed as
benchmark artifact, the ~1,000+ MW direction reversal is now expected to be
REGIONAL (South ST_GAS/CT starved while Plains coal/CC over-runs, import
under-run −4 TWh) rather than an ISO-wide family swap; the warm-committed fix
is watched against the 2023-24 RDT anchors and the 2025 direction, not
claimed to close it.

## 13. SOUTHERN-GAS LANE EXECUTED (2026-07-12 — miso-60 stgas-vlr): the 2025
starvation is the Entergy steam fleet's measured VLR self-commitment, invisible
to the model; the South-basis "suspect" was a real data bug but counter-directional

**Input adjudication first (rules 14/15, the handoff's suspects in order).**

1. *South delivered-gas basis*: the committed MISO-South 2025 row (+0.095)
   does NOT reproduce from the file's own methodology — it subtracted the
   full-year Henry Hub mean (3.529) from the 6-reported-month LA mean (3.560),
   while every other cell is like-for-like per-month diffs. The correct value
   is +0.343 (months Feb/May/Jun/Jul/Sep/Oct; EIA API re-pull this session).
   FIXED in miso_zonal_gas_hub.csv — and counter-directional: the bug
   FLATTERED South by $0.25/MMBtu (~$2.6/MWh at HR 10.4), so with South at
   its relatively cheapest basis in three years the model STILL starved it.
   Basis is not the driver; the honest correction stays (rule 15).
2. *Seam import ladders*: measured/frozen-formula (rule 23), validated at
   intake; the −4.2 TWh import gap is outcome-level. No input defect.
3. *ST_GAS representation*: ROOT CAUSE — CEMS unit-grain forensics:

| plant | online % of ALL hours 2023-25 | plant P5-all-hours | artifact mustrun_pct |
|---|---|---|---|
| Nine Mile Point | 98.2% | 414 MW (28% of nameplate) | 0.0 |
| Sabine | 85.6% | 0 (unit rotation; P5-online 122 MW) | 0.0 |
| Lewis Creek | 87.8% | 0 (P5-online 55 MW) | 0.0 |
| Little Gypsy | 50.8% | 0 | 0.0 |
| Gerald Andrus / Lake Catherine / Waterford | 13.9 / 14.6 / 19.4% | 0 | 0.0 |

The thermal-tranche derive computes the same P5-all-hours floor that grounds
the coal mustrun tranche, then class-gates it to COAL ("recorded as zero even
when its high capacity factor would make the all-hours floor look high").
With no floor, a 1.32× part-load HR on the committed band, and startup
amortization, the LP leaves the Entergy steamers dark: model South ST_GAS ~6
vs 16.4 TWh measured (2025); classFull −4.2/−5.1/−9.2 all years. The South's
load is then served by Plains coal/CC over an N→S RDT flow — the §11
direction reversal, quantified at its source.

**miso-60 = miso-59 strict meta replay + `st_gas_mustrun_per_plant=True`,
zero new scalars** (+ the rule-15 basis fix riding as data). The mechanism is
the EXISTING cc_mustrun_per_plant architecture's ST_GAS leg: each plant's
measured committed tranche (CEMS P5-when-online) forced on in its measured
top-online_frac system-load window; offers untouched (rule 19); self-targeting
by measurement (rule 18 — Gerald Andrus is floored only in its top-load 13.9%);
own mechanism id + D4_WINDOWS all-24h row (same evidence shape as the ST_GAS
drag/reliability rows). Driver: MISO SOM-documented out-of-market VLR/
self-commitment in the South region (Amite South / DSG / WOTAB). Forward
story: committed share + online fraction re-derive from multi-year CAMPD
(rule 13). The CT G-20 rejection does not transfer (opposite evidence
signature). Floors: Nine Mile 467 MW, Sabine 303, Lewis Creek 106, Little
Gypsy 100 (+ measured Midwest legs, e.g. plant 990 at 97.4% online). LOYO by
construction (zero-scalar boolean over 2023-25-pooled per-plant measurements).

**RESULT (scored, rubric v2.4):**

| anchor / metric | miso-59 (keeper) | miso-60 main | miso-60 twin (floor off) |
|---|---|---|---|
| 2023 S→N mean-flowing / sep-when-binding | 1551 MW / $2.48 | 1600 MW / $2.61 | — |
| 2024 S→N mean-flowing / sep-when-binding | 1523 MW / $2.43 | 1549 MW / $2.48 | — |
| 2025 S→N mean-flowing | 322 MW (4% binding) | 1083 MW (7.9% flowing) | — |
| 2025 N→S binding share of hours | 29% | 11.9% | — |
| 2025 summer Midwest−South separation | ~$0 | −$0.15 (vs IMM $9.31) | — |
| C1 all / free | 12/16 · 8/12 | **13/16 · 9/12** (CC-2024 clears) | 12/16 (CC-2024 +8.27 stays) |
| sysvol-2025 gas | −6.9% FAIL | **−5.5% FAIL** (0.5pp out) | −6.6% FAIL |
| C3a-2025 | −14.7% | −15.8% (regression) | −14.7% |
| C3b-2025 duration shape | PASS | FAIL (NRMSE 0.206, regression) | PASS |
| interchange-2025 (actual −19.0) | −14.0 | −11.6 (regression) | — |
| ST_GAS TWh 23/24/25 | under-run all years | 16.7 / 19.6 / 12.1 | — |
| C8 ST_GAS-2025 | n/a | 36.6% forced → **grounded PASS** (D-4 0 off-window, D-1 r 0.98 / cv 2.18) | — |
| FAIL set | 5 | 6 (+price_shape) | 5 (same as miso-59) |

*(2025 RDT baseline caveat: the 322 MW / 29% row is §11's miso-57/58
construction — miso-59 recorded "2025 direction unchanged" and its parquets
are gone, so the exact same-script comparison is unavailable; the miso-60
column is scripts/probes/_miso59_rdt_anchors.py on this bundle. The 2023/24
anchor rows ARE same-script comparisons vs the miso-59 disclosure.)*

The twin isolates the trade exactly: the floor buys the CC_REGULAR-2024 C1
clear, +1.1pp of sysvol-2025 gas, and the RDT direction movement, at the cost
of −1.1pp C3a-2025 and the C3b-2025 flip — forced supply depresses a 2025 LMP
that is already too low for reasons this lane does not own (the July-2025
−18.8% was pre-adjudicated in §10 to ELMP ex-post/emergency constructs +
deeper operator derates + RPE, none modeled). The price regressions are the
flip side of a real supply mechanism landing BEFORE the price mechanisms
exist; the named build-out that would reprice it is unchanged: RPE ($200
post-contingency, additive in violations), hourly measured RDT limit intake
(rule-14 upgrade over the 92% static derate), the 2025-09-30 shortage-pricing
redesign, and the commitment-posture window rows (COAL_BIT −15.7 both years,
CT_PEAKER-2024 +11.2 — untouched by this lane, as expected).

**Disposition:** registered 2026-07-12-miso-60-stgas-vlr (+ zero-forcing twin);
**PROMOTED to MISO keeper (owner decision, same session — supersedes
miso-59-coal-warm)** on the recommendation below. Scoring-basis note (owner
question answered): miso-60's totals are on the G-21/G-21b basis — C1 class
totals and complete-vintage C2 score per-class on the 923/CAMPD classFull
(combined reconcile preserves the CEMS-validated 923 split); the 2025 gas
family (preliminary vintage) scores on the EIA-930 combined-fossil LEVEL with
the CEMS-anchored split — already the all-ISO unconditional default. The
original recommendation: miso-60 is strictly more structurally
faithful (a measured, SOM-documented commitment the model previously
contradicted; D-1 shape r=0.98; grounded C8) and improves the volume/mix
interior, at a one-FAIL price-side regression owned by named deferred
mechanisms. Owner directive (this session): MISO dashboard pruned to the
keeper + post-keeper runs (25 pre-keeper registrations removed; bundles kept).

## 14. PRICE-SIDE LANE 1 EXECUTED (2026-07-12 — miso-61 rpe-pricing): the RPE
$200 additive violation pricing built as market design; the measured RDT
binding record intaken as the lane's validation series; C5c-2025 adjudicated
basis-broken

**The adjudication came first (rules 1/13/14), and it sharpened both lanes.**

1. **RPE pinned to primary sources** (2024 SOM body pp.9/51-52, §II.E/§III.B):
   RPE = Reserve Procurement Enhancement — "MISO enforces STR requirements in
   its two subregions by enforcing reserve procurement enhancement (RPE)
   constraints over the RDT"; "the RPE binds when headroom on the RDT plus
   the available STR in the importing subregion is limited"; it "limits flows
   between subregions after a supply-side contingency and has a single demand
   value of $200 per MWh". In the 2023-2025 design the RDT TCDC and RPE
   demand values "apply additively" in real violations — measured $700
   subregion-wide spreads ($500+$200), with even SMALL violations (the $40
   first step) overpriced "by $200 per MWh" (→ $240). The IMM's cap-at-$500
   recommendation was NOT implemented in-window, so additive-in-violation IS
   the honest historical representation (date-gate a re-anchor if adopted,
   rule 23).
2. **Lane 2 (hourly measured RDT limit intake) re-verified DATA-BLOCKED** for
   the limit series (RT Data Broker RDT endpoint deprecated without archive;
   Data Exchange key-gated; pbc reports carry no limit MW; no new public
   source as of 2026-07 — the quarterly's derate-behavior evidence, p.30, is
   chart-only). The admissible measured series is the pbc BINDING record —
   intaken this session as the `transfer-constraint-binding` clean datatype
   (MISO `{da,rt}_pbc`, market dates 2023-2025 only per rule 22, verbatim raw
   consolidation via `scripts/fetch_miso_pbc.py`; per-ISO registry
   `scripts/lib/transfer_constraint_binding/`). VALIDATION ONLY (rule 13:
   binding is a dispatch outcome).
3. **Measured basis discovery — the SOM's ">25% of RT intervals" is the
   RDT+RPE FAMILY, not the RDT proper.** The pbc RDT-proper record reads
   (hours-equivalent; RT rows are 5-min):

   | year | da S→N bind h | da mean\|shadow\| | da at-$40 h | rt S→N bind h-eq | rt N→S bind h-eq | rt violation h-eq (≥$40) |
   |---|---|---|---|---|---|---|
   | 2023 | 8 | $5.13 | 0 | 280 | 13 | 40 |
   | 2024 | 241 | $6.28 | 0 | 661 | 34 | 61 + 10 N→S |
   | 2025 | 919 | $9.88 | 18 | 264 | 8 | 50 |

   RT-2024 RDT-proper ≈ 7.5% of intervals vs the SOM family figure >25% —
   the gap is the RPE's own binding ("Tx Only"/"Both"/"RPE Only" split, IMM
   Summer-2025 quarterly p.29, with "RPE Only" large). Two consequences:
   (a) the model's single RDT constraint stands in for the whole family, so
   its binding frequency legitimately sits BETWEEN the two measured bases;
   (b) the earlier anchor readings that matched model "binding ≈25% of
   hours" to the SOM figure were family-vs-proper conflations — the new
   probe (`scripts/probes/_miso61_rdt_anchors.py`) scores both bases and
   fixes a second legacy-basis artifact (the old probe counted tier-ROWS,
   not hours, where the TCDC's parallel tiers exist; its cross-run deltas
   remain valid same-script comparisons).
   The DA S→N regime shift is measured directly: binding hours 8 → 241 →
   919 across 2023/24/25 — the 2025 S→N-dominant year the model has been
   missing, now as an hourly validation series.

**miso-61 = miso-60 strict meta replay + `miso_rpe_pricing=True`, zero new
scalars** (probe driver `scripts/probes/_miso61_rpe_pricing.py`): adds
`constants.MISO_RPE_DEMAND_VALUE` ($200, published) to both VIOLATION tiers'
flow_cost on each one-way RDT link (free tier untouched — the adder engages
only in the constraint's own driver window, rule 12). Conservative documented
gap, same direction as miso-57's: the "RPE Only" STR-scarcity channel is
unrepresented (no STR product in the LP) → separation UNDER-states measured.
Expected direction (ex-ante): violation hours reprice $40→$240 / $500→$700;
the LP redispatches up to $240 before violating; 2023/24 anchors HOLD or move
toward measured ~$3 separation-when-binding; 2025 moves only where the
model's S→N flow reaches the violation region (July-2025's gap pre-owned by
ELMP ex-post/emergency + deeper derates + upstream mid-merit, §10).

**C5c-2025 storage shape (handoff lane 5) adjudicated in parallel:
basis-broken → ledgered exception, no mechanism.** The 2025 battery-only
actual's monthly "shape" is the fleet's COD ramp (r=0.934 vs cumulative
in-service MW, EIA-860 198→804 MW in-year); per in-service MW the residual
shape is degenerate by the scorer's own CV floor (0.175 < 0.25) and
uncorrelated with the model (r≈0.02). Full write-up:
`results/calibration/FINDING-miso-c5c-storage-shape-basis-2026-07.md`;
(storage_shape, 2025) enters the miso-61 exceptions ledger alongside the
carried C5b entry (2 of 3 budgeted). Scorer-side BAT-vs-BAT + per-MW fix
flagged to the rubric-infrastructure lane.

**RESULT — to be appended after the solve + scoring (same session).**
