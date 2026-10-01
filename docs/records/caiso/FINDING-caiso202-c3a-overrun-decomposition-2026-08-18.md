# FINDING — caiso-202: the C3a 2024/2025 mean-LMP overrun is **one year-invariant model behaviour read through three different scarcity regimes** — the model overprices every sub-$60 hour by +$10–14/h in ALL THREE YEARS (2023 included) and underprices the >$60 tail; C3a's year pattern (+4.1 / +12.8 / +15.7 %) is the **cancellation ordering**, not three defects. In 2024 the miss is **~85 % the RT−DA settlement basis** (vs the DA level the model is +1.6 %); the mid-band marginal price-setter is the **in-state CC econ rung carrying CAISO's own measured DAM bid multipliers** (interior in ~98 % of the overrun hours), so the level is right-by-construction against the DA and the residual is the adjudicated RT/supply-state model-class. **Every owner-named suspect is measured and ACQUITTED**: import tranches (<5 % of the gap, measured hubs), biomass (EIA-923 monthly must-run, month-flat, never marginal), coal (13 MW), the solar bound (measured HSL potential by design). NO LP, NO SOLVE — committed bytes only (2026-08-18)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered.**
This is the owner's 2026-08-18 re-opening of the caiso-201 rested lane executing
its own charter's fallback clause: *"if the honest answer after the diagnosis is
that the remaining overrun is a measured-input limitation, write that FINDING and
stop — do not manufacture a pass."* The kill-before-solve discipline
(caiso-129/140/150 pattern) fired on every candidate lever the decomposition
surfaced — each is either measured-already-correct, arithmetically insufficient,
or fails 2023 high.

Instruments (committed, no LP, no solver; the only reconstruction is the
caiso-105/131 `run_year(fleet_only=True)` offer/fleet assembly):

* `scripts/probes/_caiso202_c3a_decomp.py` — §A/§B: the month × hod-band residual
  map on the rubric's rt_lw weights, on BOTH settlement bases (RT and DA); the
  actual-price-bucket decomposition; the node-parity witness.
* `scripts/probes/_caiso202_marginal_rung.py` — §C: per-hour marginal-rung
  attribution of the positive gap against the keeper's own reconstructed offer
  stack (per-hub measured import legs incl. wheel + CARB border carbon, fleet
  rungs by class) with the biomass-drop correction (see §C.1).

Every number reproduces from the keeper's committed `hourly/` sidecars, the
committed actual-LMP reference (`actual_lmp_hourly_CAISO.parquet`, `rt` + `da`),
the committed bench (`frontend/data/backcast/bench/CAISO/<yr>.json.gz`), the
committed measured-hub parquet (`wecc_intertie_lmp_hourly_CAISO.parquet`) and the
committed measured offer-surface artifacts (`caiso_offer_curve_measured.json`).

---

## §A — Level vs basis: the same model, two settlement bases

rt_lw common weights (caiso-131 §2 convention); "model" is the CA
demand-weighted λ from the keeper's sidecars (the C3a construction, lw-weighted —
the rubric's own-model-weights print is ~1.5 pp higher; structure identical):

| year | model λ | actual RT (lw) | gap vs RT | actual DA (lw) | gap vs DA | DA−RT basis (lw) |
|---|---|---|---|---|---|---|
| 2023 | 55.60 | 54.17 | **+1.43 (+2.6 %)** | 61.68 | **−6.32 (−10.3 %)** | **+7.55** |
| 2024 | 38.57 | 34.65 | **+3.92 (+11.3 %)** | 37.97 | **+0.60 (+1.6 %)** | **+3.32** |
| 2025 | 39.02 | 34.42 | **+4.59 (+13.3 %)** | 35.40 | **+3.62 (+10.2 %)** | **+0.98** |

Readings:

1. **2024's C3a miss is ~85 % settlement basis.** Against the DA — the market the
   model's measured bid inputs (§C) actually clear in — the model is +1.6 %,
   deep inside the band. Reality's 2024 RT traded $3.32/MWh (lw) below its own
   DA; the rubric scores RT; the model has no RT (`caiso_da_rt_two_settlement`
   is **R**, not re-opened — this table is the evidence use the charter
   authorized, not a lever).
2. **2025 is a genuine level miss** — +10.2 % even vs the DA — carried Sep–Dec
   (58 % of the DA-basis gap) + the spring belly: the standing supply-state
   lane's window (caiso-121/135/140).
3. **2023 UNDERSHOOTS the DA by 10.3 %.** The 2023 "pass" is not model skill at
   the level; see §B.

Required moves (rubric basis, to the +10 % edge): 2024 **−$0.97**, 2025
**−$1.96**; 2023 tolerates ~−$7.4 before failing low.

## §B — The cancellation ordering: one behaviour, three scarcity regimes

Weighted gap contribution per ACTUAL-RT price bucket (probe §A output;
per-bucket `mod_mean − act_mean` in $/h):

| bucket | 2023 (h / overrun per h) | 2024 | 2025 |
|---|---|---|---|
| < $0 | 410 h / **+13.9** | 868 h / +15.4 | 605 h / +10.5 |
| 0–10 | 350 / +14.1 | 418 / +12.8 | 426 / +12.4 |
| 10–20 | 668 / +14.7 | 694 / +13.6 | 736 / +12.7 |
| 20–30 | 931 / +13.1 | 1,422 / +9.5 | 1,266 / +9.8 |
| 30–40 | 1,194 / +10.3 | 2,283 / +5.8 | 2,228 / +6.4 |
| 40–60 | 2,407 / +5.7 | 2,435 / +0.2 | 3,024 / +1.3 |
| 60–100 | 1,942 / **−8.6** | 509 / −12.8 | 455 / −15.0 |
| > 100 | 810 / **−31.6** | 131 / −79.2 | 20 / −136.7 |

**The model overprices every sub-$60 bucket by +$6–15/h in every year — 2023
included — and underprices the >$60 tail in every year.** What differs across
years is only how many tail hours exist to cancel with: 2,752 h > $60 in 2023
(sum of tail contributions −$5.02, cancelling +$6.45 of sub-$60 overrun to a net
+1.43) vs 640 h in 2024 and 475 h in 2025 (tail credit −$2.09 / −$1.19). C3a's
+4.1/+12.8/+15.7 % is this ordering. Consequences:

* The 2024/2025 "overrun" and the ledgered C3c tail deficit are **two faces of
  one compression**: the model's price distribution is squeezed toward its
  mid-band from both sides. C3b (duration NRMSE) passes because the compression
  is distributed, not because the surface is right.
* **Any level-down fix sized to 2024/2025 also moves 2023** — but 2023 has
  ~$7.4 of down-room, so a ~$2–3 broad level-down would land all three years in
  band *arithmetically*. No admissible instrument that size exists (§F).

## §C — Marginal-rung attribution: who actually sets the overrun-hour λ

`_caiso202_marginal_rung.py`, positive-contribution hours, nearest-rung within
$0.75 against (a) the per-hub import legs exactly as the keeper's injector
prices them — measured hourly MALIN/PALOVRDE hub + OATT wheel + CARB border
carbon at the year's allowance price — (b) the corridor export legs, (c) the
reconstructed fleet rungs:

| rung (2024 / 2025) | share of positive gap | model λ p50 | actual RT p50 |
|---|---|---|---|
| **fleet gas-CC econ rungs** | **50 % / 52 %** | 41.6 / 44.4 | 34.2 / 37.7 |
| unmatched (storage/hydro inter-temporal duals) | 22 % / 19 % | 29.8 / 25.9 | 12.8 / 16.4 |
| import legs, ALL tranches combined | ~5 % / ~5 % | — | — |
| coal rungs | ~8 % / ~12 % | see §C.2 | |
| gas-CT / gas-ST | ~3 % | 60–62 | 50–53 |

**CC is genuinely marginal, not an attribution coincidence**: in the
positive-gap hours with λ in the CC band ($32–52), the CC class dispatches
strictly interior to its available capacity (0.05–0.95 of cap) in **4,062 of
4,137 h (2024) and 4,622 of 4,652 h (2025)**; at-cap in only 25 / 12 h. The CC
economic segment's offer is the binding price.

**And that offer is measured, not fitted.** The keeper's CC/CT band multipliers
are the pooled 2023–2025 medians of **CAISO's own as-submitted DAM bids** (OASIS
`PUB_DAM_GRP`, `caiso_offer_curve_measured.json`, gates G1/G2 recorded in the
artifact; armed via `caiso_offer_surface_measured`), the `gas_offer_net_revenue_
margin` anchor 4.7964 $/MMBtu is CAISO's own delivered-citygate 2023–25 mean
(`derive_gas_offer_margin_anchor.py`: 6.9524/3.3721/4.0646), the fuel is the
measured monthly hub overlay, and the carbon is the CARB allowance
(33.03/35.23/28.06 $/t). The DOF ledger's `offer_curve_by_group`
"identification: residual" row **overstates the residual content for CAISO's
CC/CT bands** — those specific bands have been measured since 2026-08-02; the
ledger text was not updated then (reported, not fixed here — an attestation-text
item for the next promotion).

So the model clears its mid-band exactly where CAISO's real DAM bid stack says —
which is why it is +1.6 % against the 2024 DA — and the RT prints the rubric
scores against settle below those bids through mechanisms the model class
excludes (5-minute surplus dispatch, WEIM export release, curtailment pricing:
`caiso_p1_export_sink_seam` R, `caiso_corridor_export_path` R,
`caiso_da_rt_two_settlement` R).

### §C.1 — Corrections recorded against interest (attribution artifacts found and removed)

* **Biomass is acquitted, and the first-pass attribution that indicted it was
  wrong.** The full runner injects biomass as a measured EIA-923 monthly
  must-run profile and DROPS the raw LP units (`inject_biomass_mustrun`; the
  keeper's biomass is month-flat, within-month σ ≈ 0). The
  `run_year(fleet_only=True)` reconstruction does not replicate the drop, so
  184 phantom biomass rungs ($18.6–75.9) sat dense in exactly the model's
  low-hour clearing range and absorbed 25 % of the gap by proximity. Excluded,
  their share redistributes to gas-CC (+5 pp) and unmatched (+12 pp).
* **Coal is 13 MW.** The `fleet:coal` rows are a single 13 MW plant's 2 MW
  tranches; marginal-by-degeneracy for ~500 h/yr with ~zero λ leverage. Noise.
* **The import-parity witness needed the armed loss surface.** Only 26–41 h sit
  at exact node parity because `caiso_zonal_loss_surface` and the wheel/carbon
  adders separate CA λ from the node λ; the tranche-level attribution above is
  the correct test, and it acquits the import ladder: the caiso-140-era "8,800
  MW spot capacities pinning the belly λ" no longer describes this keeper —
  since caiso-188 (MIC seam, dual 0.000) and the per-hub measured pricing, the
  import legs carry <5 % of the positive gap directly.

### §C.2 — The unmatched 19–22 % is the mid-band level read back through storage

The unmatched hours (λ p50 $26–30 vs actual $13–16) match no static rung: they
are inter-temporal dual-priced (battery charge floor / hydro water value). The
model's 6.9–9.6 GW li-ion fleet charges the belly up to arbitrage parity with
the CC-priced evening (λ_belly ≈ λ_evening×η² − adders ≈ $22–27) — correct LP
conduct given the evening level. The belly floor therefore INHERITS the CC
mid-band level; it is not an independent defect and no storage-side lever
repairs it (`battery_dispatch_adder` re-derivation remains the ledger's open
item, but its C3a-mean effect is hour-shifting, ~level-neutral).

## §D — Lane 2 (the owner's lead hypothesis): renewable/hydro bounds — AUDITED, the bound basis is measured-correct, and the overrun runs AGAINST the price miss

* **Solar** (+2.14/+2.09/+2.74 TWh vs EIA-930 delivered): the LP bound is the
  **measured uncurtailed potential** (HSL parquet) with endogenous spill —
  `caiso_solar_endogenous_spill`, the deliberate rule-3 structure ("solar sets
  the midday dual when curtailed"). The delivered-cap variant exists in code as
  `caiso_solar_cap_at_delivered` and is **self-labelled a default-off rule-13
  diagnostic pin that "must never feed a keeper"**. The overrun is the model
  refusing curtailment reality performed (largely local-congestion curtailment a
  zonal network cannot see) — and it is **price-cushioning, not price-causing**:
  removing 0.45–0.94 GW of zero-MC belly supply raises the belly λ. The owner's
  offsetting hypothesis is answered: the renewable overrun offsets the CT/CC
  *volume* underrun in the energy balance, but it cannot cause a price overrun,
  and repairing it would move C3a AWAY from the band.
* **Wind** (+0.15/+0.23/+0.28 TWh): same structure, one order smaller. Not a
  lever.
* **Hydro**: monthly budgets are the measured EIA-923 targets
  (`hydro_budget_nameplate_aware` K, `hydro_vintage_input_repair` K; 2024 pinned
  22.678 TWh in the keeper's own log). The PS water-state hourly split remains
  the unfunded owner object (caiso-201 Q2(a) NOT FUNDED); `hydro_ror_split` R
  untouched.

## §E — Lane 3: the CT_PEAKER underrun is crowding plus the excluded RT/AS duty cycle

Model CT 0.5–1.9 TWh vs actual 2.3–4.3. In the LP's perfect-foresight
energy-only P1, a CT with measured bid multipliers is never cheaper than the
measured-hub import + CC stack that serves the same hours; reality ran CTs on
RT flexibility, AS awards and local commitments the model class excludes
(`energy_reserve_coopt` I at caiso-144, LOLP overlay refused on measurement).
The underrun's energy sits inside the same over-import wedge as the CC deficit
(net imports +8.7/+8.1/+6.3 TWh). No untested in-model cell reaches it:
`cc_committed_offer_margin` (U) targets the committed-block level — §C shows
CAISO's committed/econ bands are already measured from its own bids, so the
ERCOT-form re-identification has no CAISO gap to close (cell annotated, stays
U as an ERCOT-derived form never armed here); `dam_availability_rebasis` (U,
`caiso_dam_outages`) would stack a coarser availability source over the
fully-identified CAMPD outage instrument the caiso-199/200 arc just landed
(rule 19) and is refused as this lane's lever without its own charter;
`diurnal_price_amplitude` (U) is a scorer, not a lever — this finding IS its
CAISO evidence base.

## §F — Candidate levers surfaced by the decomposition, each killed by arithmetic before any solve

1. **Per-year measured band multipliers** (`per_year_band_mults`, committed in
   the artifact, pooled deliberately at derivation): 2024 econ_low 1.027 vs
   pooled 1.066 (−$0.6 on low-econ-marginal hours) but econ_high/committed/peak
   move UP; 2025 CC bands ALL move up (committed 1.071, econ 1.085/1.098, peak
   1.457) — **anti-helpful in the failing year**. Not a lever; recorded as
   honest evidence that the real 2025 bid conduct is not below the pooled form.
2. **Per-year margin anchor** (6.95/3.37/4.06 instead of pooled 4.7964): scales
   2024 markups ×0.70 (−$1–2.4) and 2025 ×0.85 (−$0.7–1.2) — but 2023 ×1.45
   (+$3–4) drives C3a-2023 from +4.1 % toward the +10 % edge. **Kill: fails
   2023 high**, and the pooled anchor is the derivation's deliberate
   identification (rule 23 — frozen against exactly this residual).
3. **Conduct sweep of residual static-priced rows** (the $28/$48 firm blocks'
   un-forced remainder hours, ~290 h / +0.44): caiso-150 measured the firm
   blocks as already OVER-forced must-flow (+4.6/+5.7 TWh/yr vs measured
   self-schedules); completing the O-cell `caiso_firm_selfsched_floor`
   reconciliation REMOVES forced overnight supply and RAISES λ. Structurally
   owed, C3a-adverse. Not this charter's lever.
4. **The wedge instruments** (committed-gas ride-through conduct floor, PS
   water-state, export seam): adjudicated at caiso-140 §D/§G, caiso-142/143,
   caiso-191 rulings 4/6, caiso-201 Q2 — unfunded or R/G. Nothing here re-tests
   them; the required broad move (§B, ~$2–3) is the same object caiso-140 §C
   measured needing the whole 2.3–2.6 GW wedge at once.

## §G — Conclusion, and what would actually move C3a

**The honest determination stands at NOT-YET.** On this keeper's committed
bytes: 2024's C3a miss is dominated by a settlement-basis representation gap
(model ≈ DA +1.6 %; rubric scores RT; RT-DA basis measured +$3.32 lw), and
2025's genuine level miss is the standing CC-side supply-state residual whose
admissible instruments the owner has adjudicated or declined to fund. The
mid-band clearing level itself is set by CAISO's own measured DAM bid stack —
there is no fitted offer object left to repair, and no admissible in-model
lever of the required size. Manufacturing the pass through any of §F's killed
levers would be a rule-13 act.

The two routes that exist, both owner acts, both already on the record:
funding the caiso-201 Q2 objects (PS water-state intake; new evidence for the
import spot capacities — noting §C now measures the latter's direct λ share at
<5 %, so its C3a reach is bounded small), or the C3a-basis question caiso-186
§(b) packaged and ruling 5 declined. This finding adds the new quantified fact
to that record: **the same model scored against the DA settlement it
structurally represents reads +1.6 / — in-band — in 2024, and its three-year
pattern is one compression behaviour, not a 2024/2025 regression.**

## §H — Record changes

* Keeper, markers, freeze: UNCHANGED. No solve, no bundle, no dashboard
  registration due (rule 15 applies to completed runs — caiso-134/140/150
  disposition).
* Matrix (rule 28b, CAISO shard only): evidence appended on
  `import_hub_pricing` (K — the §C acquittal), `cc_committed_offer_margin`
  (U — §E annotation), `diurnal_price_amplitude` (U — §B is its CAISO evidence
  base), `caiso_firm_selfsched_floor` (O — §F.3 direction note). §5.2 header:
  caiso-202 block added recording the owner re-opening and this outcome. NO
  cell verdict moves.
* `docs/calibration-log/caiso.md`: caiso-202 entry (the re-opening record the
  charter requires; the caiso-201 ruling record stands, annotated not
  rewritten).
* DOF-ledger text item filed (not fixed): the `offer_curve_by_group` row's
  "residual" identification is stale for CAISO's CC_REGULAR/CT_PEAKER bands
  (measured 2026-08-02); correct at the next promotion's attestation.

## §I — DO-NOT-REDO (new, binding; carried §G lists of caiso-140/150 unchanged)

* **Re-measuring the level-vs-basis table, the bucket decomposition, the
  marginal-rung attribution or the CC-interior witness** — the two committed
  probes reproduce all of it from committed bytes in minutes.
* **Attributing the overrun to biomass, coal, or the import price ladder on
  this keeper** — §C.1/§C: must-run month-flat, 13 MW, <5 % measured.
* **Re-running a fleet-rung attribution without dropping the biomass units**
  the solve drops (`inject_biomass_mustrun`) — the §C.1 artifact.
* **Arming the per-year margin anchor or per-year band mults as a C3a-2024/25
  lever** — §F.1/§F.2 kill arithmetic (2023-high / 2025-adverse).
* **Scoping a C3a fix to 2024/2025 as if they were a regression** — §B: the
  sub-$60 overprice is year-invariant; 2023 differs only in tail mass.

Next number: caiso-203.
