# ERCOT-90 (measure-first) — the ST_GAS shoulder-hour displacement lane: the §8.3 CAMPD check, executed

**Status: step-1 measurement EXECUTED 2026-07-20; step-2 design round
EXECUTED 2026-07-20 (ERCOT-91, §8): the band-hour seam
(`ercot_offer_surface_cleared_share_steam`) is REJECTED as armed
(zero-spurious/C3a trips in both current-design years, alone and composed);
the winter seam (`gas_st_drag_seasonal`, the rule-22 season-grain re-derive
of the drag curve) PASSES all pre-committed guards in all three years and is
OWNER-PROMOTED to ERCOT keeper same-session:
`2026-07-20-ercot91-seasonal-drag-fullspan` supersedes ercot86. Band-hour
frontier round EXECUTED 2026-07-20 (ERCOT-92, §9, measure-first): the
RT/SCED steam-basis corpus adjudication — the NP3-965 corpus DOES carry the
gas-steam restypes (the ERCOT-89 §8.3 note is overturned), and the
RT/SCED-basis ST ladder is DERIVED from committed data
(`ercot_sced_offer_wall_steam_condbinned.json`, 2024/2025, frozen); step-2
arming remains owner-gated, keeper unchanged.** Successor lane opened per
ERCOT-89's §9.5(2) frontier (`ercot-shoulder-online-envelope-2026-07.md`):
the span mechanism was rejected as armed with the ST_GAS displacement wedge
named as the binding blocker, and §8.3 named this exact measurement — a
CAMPD-based ST_GAS hourly check — as the follow-up.

## 0. One-line answer

The direct CEMS measurement **refutes the ERCOT-89 §8.3 inference in
magnitude and re-scopes the lane**: real non-CHP steam-gas ran a median
**4.2–4.8 GW** in the residual $150–500 band hours (not the inferred ~1–2
GW), so the model's ST_GAS over-dispatch there is **×1.27–1.29 (+1.3–1.7
GW)**, not ~3× (+4 GW); and that over-dispatch is **economic, not
floor-forced** — in 97–100 % of residual hours the model's ST_GAS dispatch
exceeds even an *upper-bound* reconstruction of the `gas_st_netload_drag`
floor, by ~2.8–3.0 GW median. The band-hour miss is a **commitment-state /
offer-surface miss** (the steam analogue of the ERCOT-89 online-envelope
wedge — the LP clears the whole DAM-available steam fleet at committed/econ
offers ~$24–36 in $48–62 model hours, where reality, facing actual $150–500,
had only ~47 % of the same base online), owned by the ST_GAS offer surface
(`ercot_offer_surface_cleared_share_steam`, default-off in the keeper) —
NOT by more drag. A secondary, separable finding: the season-blind drag
curve over-carries **winter** sub-$150 hours (model 1.6–1.9 GW vs measured
0.6–1.1 GW in DJF controls, largely floor-consistent), a drag season-shape
issue against its own source evidence.

## 1. Inheritance and scope

* Target regime: the ERCOT-86/87/88/89 moderate-tightness band ($150–500
  actual RT), residual hours = actual in band & model < $150. ERCOT-88/89
  closed the merchant offer- and quantity-side enumerations; ERCOT-89 §9.2's
  static screen found the residual hours re-clear on ~2.3–2.4 GW of CC
  mid-rungs **plus ST_GAS headroom**, and §9.5(2) made any span revisit
  conditional on the ST_GAS lane closing its shoulder-hour level.
* Rule-19 owners of the ST_GAS phenomenon (any fix lands in an existing
  owner's seam, never a new stacked channel): `gas_st_netload_drag`
  (+ `gas_st_drag_*` params, rule-23-frozen derive,
  `docs/ercot-st-gas-netload-drag-2026-06.md`), the ST_GAS committed offer
  levels (`offer_curve_by_group` / `gas_st_committed_hr_mult` = 1.32,
  `gas_st_econ_hr_mult` = 0.97 in the keeper), and
  `ercot_offer_surface_cleared_share_steam` (default OFF in the keeper).
  Keeper D-2: `st_netload_drag` is the ONLY floor mechanism on the class
  (27–32 % of class energy forced, 2025 above the 30 % cap but
  rubric-v2.2-grounded).

## 2. The measurement

Probe: `scripts/probes/ercot90_stgas_shoulder_measure.py` → artifact
`data/raw/_validation-source/ercot90_stgas_shoulder_measurement.json`.
MEASUREMENT ONLY — nothing feeds the model.

* **Measured side** — CAMPD/CEMS hourly gross load (unit-level TX extracts;
  unit grain is required because two model bins are unit subsets of mixed
  facilities: 34702 = W A Parish non-coal steamers, 49392 = Barney M Davis
  unit 1, routed by the model's own `data.outages` unit rules) for the
  model's own 17-plant ERCOT ST_GAS fleet (12,391 MW nameplate, the
  `custom-bin-assignments.csv` set — non-CHP by classing), CT/CC unit types
  dropped, summed per plant on the fixed local-standard non-leap clock and
  netted ×0.95 (`campd.DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]`, the sibling
  drag-derive convention).
* **Model side** — the committed keeper's hourly sidecars only
  (`results/calibration/ercot86_rtwall_fullspan/hourly/`): ST_GAS class P1
  MW, demand-weighted system price, demand, VRE dispatch. NO keeper replay.
* **Hour sets** — the ERCOT-89 conventions at full-8760 coverage (CAMPD
  covers every day, vs the NP3-965 sample-day corpus): residual n = 63/61
  (2024/2025), formed n = 5/4, bin-matched controls n = 6,471/6,506; the
  ERCOT-89 covered residual subsets (35/33 h) are re-scored as-is for
  §8.3 continuity. Conditioning: net-load percentile bin × meteorological
  season × 4-h block (the ERCOT-89 span-derive cells).
* **Floor reconstruction** — `floor_ub = clip(0.00906·NL_GW − 0.1376, 0,
  0.34) × 8,923 MW` (keeper-armed params × the non-peaker, non-peak-tranche
  base) with `NL_hat = keeper demand − VRE dispatch`. Dispatch ≤ potential,
  so NL_hat ≥ the runner's potential-convention net-load and floor_ub is an
  **upper bound** on the true applied floor (no availability cap taken
  either). Model MW above floor_ub is therefore *provably* economic; model
  MW at/below floor_ub is floor-*consistent*, not proven forced.

Caveats (disclosed in the artifact): hourly RT smooths intra-hour spikes;
the CF percentages use the drag-covered net base (8,923 MW) as a shared
denominator for measured and model; the overnight curve check rides the
NL_hat basis (biased high vs the derive's EIA-930 basis), so it is a grain
check, never a re-fit.

## 3. Results (artifact headline rows)

### 3.1 The §8.3 inference is refuted in magnitude — the wedge is ~⅓ the assumed size

| set (2024 / 2025) | n | measured net MW med | model MW med | model − meas | ratio |
|---|---|---|---|---|---|
| residual (full) | 63 / 61 | 4,247 / 4,233 | 5,445 / 5,672 | +1,329 / +1,336 | ×1.29 / ×1.27 |
| ERCOT-89 covered subset | 35 / 33 | 4,455 / 4,769 | 6,115 / 6,133 | +1,660 / +1,364 | ×1.37 / ×1.29 |
| control (bin-matched) | 6,471 / 6,506 | 2,055 / 1,527 | 2,363 / 2,048 | +540 / +496 | ×1.26 / ×1.30 |

The e89-subset model medians reproduce §8.3's "6.1 GW" exactly — the model
side is byte-consistent — but the measured side says reality ran **4.5/4.8
GW** in those same hours, not 1–2 GW. The §8.3 number was inferred (EIA-930
NG minus merchant Base Points minus a CHP estimate; the corpus lacks ST
restypes) and inherits its §8.4(a) merchant-scope offset; the direct CEMS
measurement supersedes it. Reality **surges steam into the band hours just
as the model does** (control → resid measured 2.1 → 4.2 GW; model 2.4 →
5.4 GW): the displacement wedge is real but is **+1.3–1.7 GW, not +4 GW**.

### 3.2 The residual-hour over-dispatch is economic, not floor-forced

Residual hours: model − floor_ub median **+2,993 / +2,822 MW** (2024/2025);
share of residual hours with model dispatch above even the upper-bound
floor **1.00 / 0.97**. Median model price there $48/$62 — with committed/
econ steam offers ≈ $24–36 (keeper multipliers × 2024–25 gas), the LP has
the whole DAM-available steam fleet in merit. Measured CF on the same base:
**47.6/47.4 %** vs model **61.0/63.6 %** (curve frac 31.4/31.7 %). Reality
faced actual prices of $150–500 in those hours — every *online* steam MW
was called — so the measured output IS the online capability: the model's
excess ~1.3–1.7 GW is capability reality did not have online. This is the
ERCOT-89 §2 wedge (class-day only-OUT-is-out availability, no hour-level
commitment state) expressed on ST_GAS, at ×1.3 rather than the merchant
8–10×.

### 3.3 Secondary: the season-blind drag over-carries winter sub-$150 hours

Season-resolved controls (model price med $23–37, below/near the committed
offer, so dispatch is floor-consistent or cheap-econ-tranche):

| DJF controls | n | meas med | model med | floor_ub med | share > floor_ub |
|---|---|---|---|---|---|
| 2024 | 1,307 | 611 | 1,585 | 1,674 | 0.40 |
| 2025 | 1,480 | 1,096 | 1,923 | 1,829 | 0.55 |

MAM is neutral (model − meas −70 / +50 MW); JJA/SON over by ~470–640 MW
with 54–75 % of hours above floor_ub (econ-tranche energy). The winter
over-run (+0.8–1.0 GW median) contradicts the drag doc's pooled-season
premise at this grain: at the same net-load, 2024–25 winter steam
commitment is far below the pooled curve. On its own overnight terms the
curve still tracks (Spearman NL↔CF 0.69/0.75; per-bin table in the
artifact), so this is a **season-axis grain limit of the same source
evidence**, not a level error — any fix is a season-resolved re-derive of
the same CAMPD source with citation (the rule-22 lane named in the task),
never a residual re-tune.

### 3.4 Availability-basis notes

Model max ST_GAS 10,408/8,706 MW vs measured max *concurrent* 8,739/7,396
MW; in the 5 formed 2024 hours the model runs 9,389 MW — above the year's
measured fleet maximum. CFB Power Plant (56708, 310 MW) never runs in CEMS
either year; V H Braunig zero in 2025 residual hours; Barney M Davis ST
zero in residual hours both years. Annually the model over-runs the same
17-plant CAMPD net basis by **+25 %/+24 %** (20.77/17.92 model vs
16.61/14.41 measured TWh) — concentrated in the winter + high-net-load
hours above, while D-1 diurnal shape passes (profile_r 0.966–0.996).

## 4. Adjudication (the three named axes)

* **Drag-shape miss?** NOT in the band hours — the residual-hour
  over-dispatch sits almost entirely above even the upper-bound floor; the
  drag level there (~2.8 GW) is *below* the measured real output (~4.2 GW).
  The drag IS implicated in the separable winter control-hour over-run
  (§3.3): a season-axis grain limit against its own source.
* **Committed-offer level / commitment-state miss?** YES — the binding
  band-hour seam. The model prices the full DAM-available steam fleet at
  committed/econ offers with no online/offline state; reality's online
  share in exactly those hours was ~47 % of the same base. The owning seam
  is the ST_GAS offer surface: `ercot_offer_surface_cleared_share_steam`
  (default-off, already built — the steam leg of the measured cleared-share
  conditional) or the committed offer levels — the same admissible shape as
  the ERCOT-88/89 re-pricing of the un-cleared increment, extended to
  steam. Never a new channel; never an LP cap (the ercot41/43 no-cap line).
* **Availability-basis miss?** Contributing, not primary: max-concurrent
  and never-running-plant evidence (§3.4) says the class-day only-OUT-is-out
  basis carries some MW reality never showed, but the band-hour wedge is
  dominated by the commitment-state/offer axis above.

## 5. Re-quantified coupling for ERCOT-89 §9.5(2)

The revisit clause stands but with reduced expected potency: closing
ST_GAS to measured levels frees at most **~1.3–1.7 GW** of the ~2.3–2.4 GW+
mid-rung re-clearing wedge the §9.2 static screen identified — ST_GAS is
roughly HALF the displacement, the rest is merchant CC mid-rung headroom
(the ERCOT-89 §9.1 partial-driver limit, unchanged). An ST_GAS fix alone is
therefore unlikely to form the band; it is a necessary-but-not-sufficient
leg, and the span re-probe (unchanged, per §9.5(2)) remains the test of the
combined effect.

## 6. Pre-committed step-2 guards (if the owner authorizes a build)

1. Default-off gate in the existing owner's seam only (§4): the
   cleared-share-steam conditional and/or a season-resolved drag re-derive
   from the same CAMPD source. No new channel, no LP row/cap/floor beyond
   the existing drag, D-2 enumeration re-derived before the seam is
   written.
2. Probe cadence: single-year 2024 rule-16 throwaway probe first
   (`scripts/replay_keeper.py results/calibration/ercot86_rtwall_fullspan
   --set key=json --years 2024`), then 2025, then full-span LOYO — bundles
   deleted after analysis, nothing registered unless a genuine keeper
   candidate.
3. Gates, pre-committed: C3a level guard + zero-spurious gate + no
   scarcity-tail/C3b/C3c degradation (both directions), the ERCOT-89
   inherited set. A winter fix additionally must not degrade the winter
   C1/C4 rows it touches. Degrading the current-design years is a
   rejection (rules 1/11 — no re-sweep of any frozen artifact against the
   residual).
4. Keeper stays ercot86 throughout (owner-only swap). After any ST_GAS fix
   lands, the ERCOT-89 span mechanism MAY be re-probed unchanged (its
   §9.5(2) clause) — same guards, no artifact re-sweep.

## 7. Rule ledger

* **Rule 13** — every measured quantity here is a telemetered/CEMS physical
  output used to adjudicate seam ownership; the per-hour series may only
  ever drive a mechanism through conditional structure (as the
  cleared-share/span artifacts already do), never a per-hour pin.
* **Rule 14** — the measured data contradicted the §8.3 estimate; the
  measured data wins and the estimate's error (merchant-scope offset in the
  930-residual arithmetic) is documented rather than kept.
* **Rule 19** — one owner per phenomenon: the verdict routes the band-hour
  fix to the offer-surface owner and the winter fix to the drag owner;
  the two are separable and must not be stacked on the same rows.
* **Rule 22** — the drag params were NOT re-derived or re-tuned; the curve
  was checked against its own source at a finer grain, and the winter
  finding is recorded as a grain limit with citation.
* **Rule 23** — the ERCOT-89 span artifact and the drag derive stay frozen;
  nothing here re-swept them.

**Deliverable of this charter:** this document + the §2 probe + artifact +
the calibration-log entry. Step 2 is chartered, not started, pending owner
go-ahead on the §4 verdict.

## 8. Step-2 build record (ERCOT-91, 2026-07-20 — the authorized design round)

One design round, two separable seams, probed independently per §6 and
adjudicated on the pre-committed guards. D-2 enumeration re-derived before
any seam was armed (calibration-log entry; `st_netload_drag` confirmed as
the class's only floor, the wall bid-axis-only within the existing
cleared-share owner — no stacking).

### 8.1 Band-hour seam (arm `ercot_offer_surface_cleared_share_steam`) — REJECTED as armed

The ERCOT-77-built steam extension ENGAGED as designed (516 walled rows vs
the CC/CT-only base; ST boundary/wall + measured ST state weight, DAM
basis). It moves the LEVEL toward measured everywhere — 2024: residual-hour
model 5,445 → 5,315 MW (measured 4,247), controls +540 → +158 MW over,
annual +25 % → +15 % over the CAMPD basis, freed energy → CC +0.82 /
CT +0.62 TWh (reality's surge pattern); 2025: residual 5,672 → 5,012
(~half the wedge), annual +24 % → +10 %. But it TRIPS the pre-committed
gates in BOTH current-design years:

* 2024: zero-spurious TRIPPED (7 → 15; all 8 new hours ONE Jan-14
  cold-snap cluster, hoy 330-336 + 349, actual $85-107 → probe $153;
  283 sub-$150 hours lifted > $5, median +$8.7); C3a −1.3 % → +1.9 %
  (held); band fill 5/68 → 5/68 (none).
* 2025: C3a +1.4 % → +3.5 % DEGRADED; spurious 2 → 3 TRIPPED; band
  4/65 → 4/65. Tail/NRMSE held both years (h>$200 toward actual, 13 → 18
  vs 53 in 2024).
* Composition with the winter seam (both armed, 2024) REFUTES the coupling
  hypothesis: the SAME 8 Jan hours trip (at $153-157) and C3a degrades
  further (+2.8 %) — the cluster is a genuine cold snap (high net-load;
  the DJF-resolved drag correctly still carries a floor there), and the
  walled above-DA steam increment sets the price regardless of the drag's
  state. The trip is intrinsic to the DAM-basis ST wall + state weight at
  the measured grain, not to the drag.

Disposition: the ercot41/43 rejected-probe pattern — machinery stays MERGED
default-OFF (as built in ERCOT-77), byte-identical off; probe bundles
deleted (rule 16); no retune, no artifact re-sweep (rule 23). Frontier for
any future band-hour round (a NEW charter, not this one): the ST analogue
of the ERCOT-86 RT/SCED basis correction — the RT artifact deliberately
carries no ST block, so the steam wall prices a DAM-basis ladder the
ERCOT-84/86 lane already proved measured-cheap/mis-based for CC/CT — plus
finer state conditioning; both are data-intake questions (the ERCOT-89
§9.5(1) shape). The §5 coupling ledger stands: no ST_GAS band-hour fix is
armed, so the ERCOT-89 span revisit clause remains parked on its ~1.3-1.7
GW necessary-but-not-sufficient leg.

### 8.2 Winter seam (season-resolved drag re-derive) — PASSES, full-span candidate

`scripts/data/derive_ercot_stgas_drag_seasonal.py` re-derives the SAME
curve from the SAME CAMPD source (drag-covered plants only, unit-routed;
EIA-930 ERCO net-load; overnight 23-05h; hinge estimator of the
NYISO/PJM standing family) per meteorological season →
`data/raw/_validation-source/ercot_stgas_drag_seasonal.json` (frozen rule
23): DJF 0.01354/−0.4257/0.270 (zero-crossing 31.4 GW), MAM
0.00731/−0.1073/0.241 (14.7), JJA 0.01149/−0.2800/0.359 (24.4), SON
0.00601/−0.0810/0.276 (13.5); pooled re-fit consistency check
0.00932/−0.1863/0.293 vs the armed 0.00906/−0.1376/0.34. The DJF
zero-crossing at ~31 GW vs the pooled 15.2 GW IS the §3.3 winter
over-carry, now measured at curve grain. LOYO 2-year re-fits: MAM/JJA/SON
stable; the DJF knee varies 24-38 GW with winter-event composition but
every subset sits far above the pooled crossing — grain fix robust,
magnitude carries honest winter variance.

Mechanism: `ScenarioConfig.gas_st_drag_seasonal` (default off) swaps the
three pooled scalars for the artifact's per-season coefficients inside
`fleet.apply_gas_st_netload_drag_floor` — same mechanism id, same rows,
same all-hours window (D-2/D-4 identity unchanged); ISO-guarded (rule 25);
flag-off byte-identical (test-enforced).

Probes (single-year throwaways, base = keeper): ALL GATES HELD both years,
C3a improved in 2024 (−1.3 % → −0.6 %; 2025 +1.4 % → +2.0 %, inside the
material threshold). 2024: DJF ST_GAS 3.51 → 2.26 TWh vs measured 1.74
(over-carry +1.77 → +0.52), annual 20.77 → 18.54 vs CAMPD 16.61
(+25 % → +12 %), DJF conservation → CC +0.92 TWh; 2025: DJF 4.21 → 3.05 vs
2.82 (+1.39 → +0.23), annual 17.92 → 15.83 vs 14.41. Winter C4 (gas-family
vs EIA-930 NG) flat-to-improved both years (2024 DJF NRMSE 0.1296 → 0.1291;
2025 0.1322 → 0.1317). Residual band hours barely move (economic, not
floor-forced — as pre-registered). Honest cost, disclosed: MAM/SON medians
shift further under measured (the shallower shoulder floors release MW the
econ layer does not re-add; that under-run belongs to the ST_GAS econ-offer
axis, not the floor — rule 14: the finer-grain measured curve stands).

Disposition: solved full-span 2023-2025 as
`ercot91_seasonal_drag_fullspan`, registered on the dashboard per rules
15/16 in the same session (see the calibration-log entry for the final
gate table), and **OWNER-PROMOTED to ERCOT keeper same-session**
(`2026-07-20-ercot91-seasonal-drag-fullspan`, superseding ercot86;
attestation + keeper shard + market_story + status rebuild +
keeper-auditor PASS — see the calibration-log promotion amendment).

## 9. ERCOT-92 (measure-first): the RT/SCED steam-basis corpus adjudication — derivable from COMMITTED data, and derived (2026-07-20)

The ERCOT-91 §8.1 frontier named two data questions for any future band-hour
round: an RT/SCED-basis ST ladder and finer state conditioning. This round
adjudicated the corpus (no apply, no mechanism, no solve — the ERCOT-90
pattern) and resolved the premise: **no new data intake is needed.**

### 9.1 Corpus adjudication (the three chartered axes)

* **(a) NP3-965 SCED corpus — CARRIES steam; the §8.3 note is overturned.**
  All four on-disk sample-day parquets carry the three gas-steam restypes
  (GSREH/GSNONR/GSSUP): 44 resources, ~45-55k interval-rows per file,
  SCED1/SCED2 curves 100 %-populated on every ON-family row (median 8
  steps), Base Point + HASL present, positive BP→HASL spare on ~half the ON
  rows. The ERCOT-89 §8.3 parenthetical "the corpus lacks ST restypes"
  described the DERIVED CC/CT artifact's restype scope
  (`CLASS_OF_RESTYPE` in `derive_ercot_sced_offer_wall.py` — rule 19 as
  then applied), not the raw corpus; §8.3 now carries a bracketed
  correction (rule 14: the measured fact wins and the error is documented).
* **(b) 60-Day DAM disclosure steam rows — NOT SCED-usable.** The DAM Gen
  Resource Data carries 45 steam resources at full-year coverage but only
  the QSE-submitted DAM energy offer curve (10 steps), DAM/AS awards, and
  an ex-ante `Resource Status` — no SCED1/SCED2 as-dispatched curves, no
  Base Point/HASL, no telemetered status. It cannot supply an RT surface;
  it IS the measured-cheap DAM basis the ERCOT-91 §8.1 trip refuted.
* **(c) Telemetered steam ON/OFF at hour grain — YES, same corpus.** The
  SCED corpus carries `Telemetered Resource Status` per interval for all 44
  steam resources (ON/OFF/OUT/ONOS/ONREG/…), hour-resolvable by
  within-hour aggregation (the ERCOT-87/89 convention). Coverage is the
  sample-day inventory only: 2024 = 25 tail + 22 control days, 2025 = 11
  tail + 24 control days. The state-conditioning half of the frontier is
  therefore ALSO committed-data-derivable if a step-2 round wants it.

**Verdict: an RT/SCED-basis ST ladder (the ERCOT-86 construction, steam
leg) is derivable from committed data for 2024/2025 — no intake, no owner
data authorization needed. 2023 stays DAM-basis unreachable (no 2023 sample
days on disk; regime bar).**

### 9.2 Fleet scope (the model's own 17 plants)

36 of the 44 corpus steam resources map by exact name onto 16 of the 17
model ST_GAS plants (`custom-bin-assignments.csv`); validated per-plant —
sum of max HSL tracks nameplate for all 16. CFB Power Plant never appears
in the corpus (consistent with its zero CEMS operation, §3.4). The other 8
resources are small industrial/municipal CHP steam (Dow ×4, Texas
Petrochemicals, GEUS Greenville ×3), all ≤ 49 MW HSL, ~0.2 % of gas-steam
ON-spare MW — excluded from the ladder and disclosed per year in the
artifact (`coverage.excluded_non_fleet`). An unmapped corpus name is a hard
error, so a source update forces a map review (rule 23 hygiene). The fleet
scope also removes the CHP self-scheduler noise: ONOS rows drop from 13 %
of raw steam ON-family rows to < 1 % of fleet rows.

### 9.3 The derived frozen artifact

`scripts/data/derive_ercot_sced_offer_wall_steam.py` →
`data/raw/_validation-source/ercot_sced_offer_wall_steam_condbinned.json`
(+ `tests/test_derive_ercot_sced_offer_wall_steam.py`, 9 tests). The
ERCOT-86 wall construction byte-shared (segment/geometry helpers imported
from the frozen CC/CT derive, which stays byte-identical and ST-free —
test-enforced): ON-family fleet steam rows, BP→HASL segments of the SCED2
curve, price/gas-day HR-multiplier normalization, MW-weighted quantile
ladders per shared net-load-percentile bin. Year-scoped 2024/2025, no
pooled fallback, zero fitted scalars, deterministic (byte-identical
re-runs), frozen rule 23. All 7 bins populated both years (168-505
intervals/bin). Headline:

| bin (2024) | RT q30 | RT p50 | RT q70 | RT q90 | DAM p50 | DAM q90 |
|---|---|---|---|---|---|---|
| b3 (p50-70) | 19.4 | 46.0 | 66.2 | 183.8 | 19.9 | 81.7 |
| b4 (p70-80) | 18.1 | 44.1 | 60.1 | 153.0 | 21.0 | 80.6 |
| b5 (p80-97) | 32.0 | 46.3 | 58.5 | 153.4 | 31.4 | 90.6 |

2025 is steeper still (b5 q90 438; b6 q70 301). From bin 1 upward the RT
steam surface's upper rungs stand far above the DAM ST ladder's (encoded as
a regression test on the mid-band bins, the CT-test convention) — the
ERCOT-84/86 measured-cheap-DAM-basis lesson, now MEASURED on steam.
Exceptions disclosed, not encoded: b0 both years and 2024-b6 (scarcity bin:
tail-day ON steam runs nearly fully loaded, so the residual spare is thin
and cheap while DAM carries cap-level rungs). Quantified basis gap for the
step-2 round: the keeper's steam offer stack (econ mult 10.8, committed
14.8 = 0.97/1.32 × the 11.18 cap-weighted fleet HR) prices at the measured
RT surface's ~q10-q30 in every mid/high bin — the §8.1 trip's root cause
(pricing the un-cleared steam increment off a surface whose whole mass
sits below the real one) now carries its measured replacement.

### 9.4 STOP — step-2 arming is a separate owner-gated round

Chartered, not started (the ERCOT-90/91 cadence). The arming round inherits
the ERCOT-91 §6 guards: C3a level + zero-spurious + no tail/C3b/C3c
degradation, both directions; 2024 rule-16 throwaway → 2025 → full-span vs
TRUE bases; bases come from the ercot91 keeper's committed hourly sidecars
(`results/calibration/ercot91_seasonal_drag_fullspan/hourly/`, ALL years —
no replays). Design questions for that round, named here so nothing hides:
(i) the wall's ladder-source swap to this artifact in the steam leg (the
ERCOT-86 replace/tier composition semantics, steam-scoped); (ii) whether
the state weight ALSO moves to the SCED-basis hour-grain conditional
(§9.1(c)) or stays DAM-based; (iii) the Jan-14-2024 cold-snap cluster that
tripped the DAM-basis arm is the first regression to check. Explicitly out
of scope, unchanged: any LP cap (ercot41/43), re-tuning any frozen
artifact (rule 23), the C3c tail lane, the ERCOT-89 span re-probe (§9.5(2)
condition still unmet).

### 9.5 Rule ledger

* **Rule 13** — the ladder is an ex-ante posted-offer measurement with a
  forward-native driver (year-own net-load percentile), zero fitted
  scalars, year-scoped with no pooled fallback; nothing per-hour ships.
* **Rule 14** — the measured corpus fact (steam restypes present) overturns
  the §8.3 working note; the note is corrected in place with citation, and
  the fleet-scope map prefers exact measured correspondence (validated vs
  nameplate) over the restype-only approximation.
* **Rule 19** — the steam ladder is the steam-owner seam's own basis in its
  own artifact; the CC/CT RT artifact is untouched (its ST-free invariant
  stays test-enforced).
* **Rules 22/23** — no existing artifact re-derived or re-tuned; the new
  artifact freezes against residuals (re-derive only on SCED source
  update, map reviewed on update via the unmapped-name hard error).
* **Rule 16** — no solve, no probe bundle, nothing registered; keeper
  unchanged (`2026-07-20-ercot91-seasonal-drag-fullspan`).
