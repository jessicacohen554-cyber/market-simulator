# PJM matrix-column triage — pjm-146 (2026-08-02)

**Session scope.** No-LP triage of every open PJM cell in the cross-ISO
mechanism matrix (rule 28 `[R-MECH-MATRIX]`), then ONE pre-registered A/B on
the strongest admissible live candidate. PJM is CALIBRATED (keeper
`2026-07-31-pjm-143b-hy-level`, 9/9, C1 16/16 free 12/12, zero FAILs) and the
pjm-142 frontier declaration closed the price-formation (diurnal-amplitude)
queue — every arm here is rule-1 structural work: no residual wants closing,
and a gate regression on a correct change goes to the owner with numbers,
never silently kept or reverted (the pjm-144 posture).

**Numbering.** The handoff that opened this session was drafted against
pjm-144's HEAD and titled itself pjm-145 with 22 open cells. Between drafting
and execution, shorthand **pjm-145 was spent**: the 2026-08-02 session that
refused `dam_availability_rebasis` ex ante (PJM `U → G`, no solve;
`results/calibration/FINDING-pjm145-dam-availability-2026-08-02.md`; log entry
ends "Next shorthand: pjm-146"). This session is therefore **pjm-146**, the
open-cell count at its HEAD is **21** (20 `U` + 1 `O`), and the previously
drafted 2022-validation session renumbers to **pjm-147**.

**Environment facts re-measured this session** (fresh container, HEAD
`cb1c416`): `uv sync`; `curate_capacity_deliverability.py` (155 PJM rows);
`regenerate_clean.py`; `fetch_pjm_da_virtuals.py` (36 monthly
`hrl_da_incs_decs` parquets — the keeper arms `pjm_da_virtual_bids`, loader
hard-fails without them); `build_pjm_as_withholding.py` re-run per the
pjm-145 fresh-clone note, with the byte-churned committed ≤2022 parquets
`git checkout`-ed back (rule 23). 12 GB swapfile enabled BEFORE any solve
(keeper note 14: peak RSS 15.55 GB with `ramp_limits=True`). Default cache
key verified `603c2498bf71d21d` (the pjm-145 repair at f58339b; the handoff's
`0e9fce2fb55b889f` was stale). Test baseline: see §4.

---

## 1. Classification of the 21 open cells

Classes: **(a)** forecast-lane (not a backcast lever) · **(b)** superseded by
rule-19 precedence · **(c)** data-/instrument-blocked (the blocking fact
recorded) · **(d)** live candidate.

| # | cell | class | one-line verdict |
|---|------|-------|------------------|
| 1 | `state_carbon_pricing` | **(d) — RANK 1** | RGGI cost measured-absent; machinery committed; only the price registration + adder wiring missing |
| 2 | `measured_chp_heat_rates` | **(d) — RANK 2** | keeper note 13 (CC_CHP +42 %); PJM is the other hand-factor ISO; deriver ISO-generic, artifact never derived |
| 3 | `hydro_ror_split` | (d)-minor | admissible source (ORNL EHA, not the 930 fold) but ~1.1 % of load and a classifier review is a prerequisite |
| 4 | `storage_vintage_ramp` | (d)-immaterial | PJM-state battery ≈ 436/626/1,260 MW cum., 71/190/634 MW in-year CODs — audit-grade vs CAISO's 3.0–3.6 GW/yr |
| 5 | `st_gas_mustrun_p25` | (c) | pair is a no-op on the committed artifact: `online_frac` 0/10 ST_GAS rows (verified); firing = fleet-wide tranche re-basing → own charter |
| 6 | `nuclear_unit_availability` | (c)-adjudicated | PJM-NUC-1b build-gate FAIL (−72 MW vs ≥ +75 MW), self-defeating by construction; not re-armable without a new identification |
| 7 | `hydro_dispatch_envelope` | (c) | deriver reads EIA-930 `NG:WAT` hourly — PJM's is the PS fold pjm-143 adjudicated (+72–78 %) |
| 8 | `hydro_min_flow_floor` | (c) | same source, same fold; Q95 of a PS-inflated series overstates the floor |
| 9 | `winter_citygate_daily` | (c) + scope bound | no TETCO-M3 daily series on disk; pjm-141 σ=$0.000000 bar leaves only the winter-LEVEL story, and no winter-level defect stands |
| 10 | `coal_offer_net_revenue_margin` | (c)-instrument | ERCOT form reads SCED TPO (per-unit, unmasked); PJM has no equivalent |
| 11 | `cc_committed_offer_margin` | (c)-instrument | same; class-level PJM variant = a chartered successor lane, not a narrow lever |
| 12 | `coal_peak_offer_margin` | (c)-instrument | same |
| 13 | `coal_perplant_offer_level` | (c)-instrument | per-plant identification blocked outright by masked unit identity |
| 14 | `import_hub_pricing` | (b) | armed `pjm_seam_measured_ladder` owns seam-band pricing (rule 19); pjm-141 refuted the one chartering premise |
| 15 | `mass_cap_lp_row` | (a)/(b) | adder path is the faithful banked-market representation (module-adjudicated); the row is a forecast/scenario instrument |
| 16 | `td_loss_factor` | (a)-no-charter | every keeper pins 0.0; PJM's passing C1 16/16 is the evidence no basis gross-up is missing |
| 17 | `lcr_tsl_published` | (a) | CETO/CETL live inside `capacity_deliverability_limits` (forecast); dispatch-side half undercut by pjm-137's sub-zonal congestion measurement |
| 18 | `entry_dampers` | (a) | mode-F row; FFR program owns it (MISO `O` at FFR-2B) |
| 19 | `transmission_expansion` | (a) | mode-F, built, untested in any lane |
| 20 | `hydro_accreditation` | (a) | mode-F adequacy-ledger term, armed-unprobed for PJM at FFR-1C (`O`); FFR probes it |
| 21 | `startup_co2_reporting` | (a)-reporting | never in LP; arm opportunistically with emissions-accounting work |

`dam_availability_rebasis` — the 22nd cell in the drafting-time count — is
already `G` (pjm-145, refused ex ante, no solve).

---

## 2. Per-cell detail and citations

### 2.1 (d) RANK 1 — `state_carbon_pricing` (the Phase-2 lever)

**The absence is verified, not assumed.** The keeper runs
`carbon_price_path="zero"`, `carbon_price=0.0`, `state_carbon_pricing=True`
(`results/calibration/pjm143_hy_level_B/run_config.json`). The flag is a
provable no-op for PJM: `policy.cap_and_trade.resolve_carbon_program` finds
the PJM program but `measured_price("PJM", ·)` returns `None` because
`STATE_CARBON_PRICE_BY_ISO` has no PJM entry — by design,
`CAP_AND_TRADE_PROGRAMS["PJM"].price_key = None` ("Still ships inert by
default", `config/capacity_market.py:137-140`). The adder is `float(None or
0.0) = 0`. So RGGI allowance cost is absent from every PJM offer while the
same mechanism family is `K` in CAISO (CARB), NYISO and NEISO (RGGI).

**What already exists, committed and measured (this is why the lever is
narrow):**

- `PJM_RGGI_ZONE_SHARE` — per-zone, per-year member fraction of operating
  fossil nameplate, derived by `scripts/data/derive_pjm_rggi_zone_share.py`
  from year-matched EIA-860 + the model's own zone assignment. Dominion
  0.9881 (2023) → 0.0 (2024, Virginia's exit); EMAAC 0.7327/0.7252/0.7221;
  SWMAAC 0.9976; western zones 0.
- `RGGI_MEMBER_STATES_BY_YEAR` — VA member 2023, exited 2024-01-01; PA never
  a member (enjoined).
- `per_generator_membership` — exact per-plant state test against the year's
  member set (EIA-860-backed), zone-share fallback only for synthetic rows.
  PJM's CAMPD per-plant fleet (`use_campd_bins=True`) carries real plant
  codes, so membership resolves per-unit for ~the whole fossil fleet.
- `assemble_mc` already accepts a per-generator membership-weighted carbon
  column (`legacy_bins.py:329-336`) — "a uniform m_zone == 1 reproduces the
  scalar path bit-for-bit".
- The forward story is already built: `projected_price` escalates the last
  measured clearing price at the program's containment-band rate (rule 13 —
  the quantity regenerates for a forward year and responds to conditions).

**What is missing (the whole delta):** the measured price series for PJM and
the adder-path wiring that turns the scalar `resolve_carbon_price` into the
membership-weighted per-generator column at the backcast mc seam
(`scripts/run_calibration.py::run_year`; today no caller builds the vector —
the scalar goes uniformly to all units, exact only for whole-ISO programs).

**The measured input.** RGGI quarterly-auction clearing prices, annual
means — the same primary series already cited in-repo for NYISO/NEISO
(`fuel_trajectories.py` block comment; rggi.org auction results A59–A70):
2023 $13.49, 2024 $20.71, 2025 $22.09 per **short** ton. PJM stores the
**metric-converted** values (the NEISO convention, unit-exact against the
model's tCO2/MWh `emission_rate`): **$14.87 / $22.83 / $24.35 per tonne**.
Zero fitted parameters.

**Materiality (first-order).** At ~0.37 t/MWh a member gas-CC carries
~$5.5–9.0/MWh; member coal (~0.95–1.0 t/MWh — Brandon Shores/Wagner in MD
through mid-2025) ~$14–24/MWh. Member fossil is roughly the EMAAC + SWMAAC
fleets (+ Dominion in 2023): the model's own zone shares above.

**Admissibility.** Rule 14 (measured statutory cost replaces a zero
estimate); rule 13 (auction price + built escalator = forward-reproducible,
condition-responsive); rule 1 (a real market mechanism — RGGI compliance cost
is genuinely in member units' offers; PJM's MMU cost-offer guidance includes
allowance cost). Frontier-declaration-compatible: "further PJM
price-formation work needs a NEW defect or a NEW measured identification with
its own charter" (`keepers/PJM.json` frontier block) — this is a new measured
identification, not an amplitude lever from the closed queue.

**Declared caution, pre-registered rather than discovered.** PJM's offer
level is partly carried by residual-identified surfaces
(`offer_curve_by_group`, 60 scalars; the pjm-117/118 margin level) that were
fitted on the carbon-UNCOMPENSATED stack. They are ISO-wide per class, so
they **cannot** have absorbed the member/non-member differential — the
differential is pure structural gain — but they may have absorbed part of the
average level. Expected consequences, declared before any solve: C3a-2023
(+2.99 % over, post-pjm-143) worsens; C3a-2025 (−9.04 % under) improves; the
C3c 1 h / 2.5 h margins are reported explicitly (queue item 6). Gate flips go
to the owner with numbers. The compensating-error follow-on (re-identifying
the fitted bands on the compensated stack) is a successor lane, not this
session. Note the armed midcurve belt prices to a measured **target** (`max(0,
target − mc_base)`), so where it binds, a carbon-inclusive mc is absorbed
into a target that itself was measured from carbon-inclusive conduct — the
composition is self-consistent in exactly the hours the belt owns.

**Cache/registry discipline** (`results/cache.py` epoch policy; rule 24;
duty 28c): the delta ships as a **new default-off ScenarioConfig gate**
(`pjm_rggi_allowance_pricing`) + a separate cited constants registry — NOT a
bare `STATE_CARBON_PRICE_BY_ISO["PJM"]` entry, which would silently re-arm
every PJM backcast under the default-True `state_carbon_pricing` (a same-key
cache invalidation and an uncontrolled keeper-semantics change).
`_CACHE_KEY_OPTIONAL_FIELDS` registration keeps the default key at
`603c2498bf71d21d`; the matrix row lands in the same PR. Promotion-to-default
(folding the series into `STATE_CARBON_PRICE_BY_ISO` + `price_key="PJM"`,
retiring the gate, unifying the RGGI unit convention per the harmonization
note) is an owner decision after the A/B.

### 2.2 (d) RANK 2 — `measured_chp_heat_rates`

Live and admissible; deliberately ranked behind the carbon cell.

- **Standing defect:** keeper note 13 — "PJM CC_CHP runs +42 %" (carried from
  pjm-135). Model CC_CHP 9.06/8.72/7.79 TWh.
- **PJM is the other hand-factor ISO**: `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS
  = {CAISO, PJM}` (`data/chp.py::_correct_chp_steam_credit_hr` — ×1.8 CT_CHP
  below 8.0; ×1.15/floor-6.3 CC_CHP below 6.0; "PJM 2026-07-07: CC_CHP ~4.95
  / CT_CHP ~6.14 are equally sub-physical"). Arming retires a hand number
  (rules 21/24) exactly as caiso-147 did, and caiso-147's ISO-generic
  basis-gate fix (compare at the replacement seam, before the hand factor)
  pre-cleared the defect it called "LATENT IN PJM TOO".
- **Readiness:** `derive_chp_power_only_heat_rates.py` is ISO-generic
  (eGRID CHPCHTI add-back on the net denominator; CEMS validation built in);
  eGRID + CAMPD raw are on disk; artifacts exist for MISO/CAISO/NYISO/NEISO
  and **none for PJM** (verified: `data/raw/_processed-legacy/
  chp_power_only_heat_rates_{NEISO,MISO,NYISO,CAISO}.csv`).
- **The NEISO-70 overshoot risk is mitigated but must be a pre-registered
  kill**: PJM CC_CHP *does* carry a `chp_steam` D-2 floor (11.0/7.9/10.4 % of
  class; CT_CHP 23.7/17.4/27.2 % — keeper `legitimacy_diagnostics.json`),
  unlike NEISO's 0 % — but far below CAISO's 43–47 %, so a dearer offer can
  still over-release the class.
- **Known-red cluster measured:** all 7
  `tests/unit/data/test_measured_chp_heat_rates.py::TestDerive` failures are
  ONE stale test-harness signature — `plant_table()` grew a required
  `cems_heat` argument and the tests' own call sites were never updated
  (same `TypeError` at line 66 in every one). Pre-existing on main; not a
  deriver defect. The session that arms PJM should fix the call sites in the
  same PR.
- **Why rank 2:** CC_CHP + CT_CHP ≈ 1.3 % of PJM load (both classes exempt
  from C7/C8 by explicit list), against a first-order ISO-wide cost input at
  rank 1; and the derive-plus-overshoot-guard design burden exceeds the
  carbon cell's registration-plus-wiring delta.

### 2.3 (d)-minor — `hydro_ror_split`, `storage_vintage_ramp`

- `hydro_ror_split`: the ONE hydro-trio member not blocked by the 930 PS fold
  (source = ORNL EHA classifier + monthly budgets). But PJM conventional
  hydro is 3,334 MW / ~9 TWh (~1.1 % of load, ungated), and the matrix
  carries the nyiso-92 caution that the completion rule is CAISO-reviewed
  only — a PJM classifier review (Conowingo's pondage, Safe Harbor's peaking)
  is a prerequisite. Stays `U`; queue behind the top two.
- `storage_vintage_ramp`: sized this session from
  `data/raw/eia-860/eia860_energy_storage_operable.parquet` (PJM-state
  approximation, upper bound incl. MISO slivers): cumulative battery ≈ 436 /
  626 / 1,260 MW with 71 / 190 / 634 MW commissioned in-year 2023/24/25. The
  mechanism's whole correction is bounded by the in-year COD MW — two orders
  under any gated statistic (CAISO's motivation was 3.0–3.6 GW/yr). Stays
  `U`, audit-grade; revisit when the fleet grows.

### 2.4 (c) — blocked cells, with the blocking facts

- **`st_gas_mustrun_p25`** — verified in-session on the committed artifact
  (`data/raw/_processed-legacy/thermal_tranches_PJM.csv`): `online_frac`
  populated on 168/256 rows overall but **0/10 ST_GAS rows**, while `p25_cf`
  is present 10/10. The runtime gate needs level>0 AND frac>0 (nyiso-105
  blocker 1/2, `arrays.py:1750-1753`), so the armed pair solves a
  bit-identical control today. Firing it requires re-deriving the tranche
  artifact at HEAD — a **fleet-wide re-basing** of the shares the whole PJM
  offer curve is built from, plus the >100 % p25 clamp prerequisite
  (nyiso-105 blockers 3-4) — i.e. its own rule-23 charter with its own
  control arm. Also pjm-139 W4: PJM's ST_GAS forcing owner is
  `st_netload_drag` (D-2 52.2/48.7/40.0 %), not the MISO six-limb form; the
  lever is a forced-share re-grounding candidate, never an overnight-price
  lever. Named successor for the C8 ST_GAS row; not a narrow lever.
- **`nuclear_unit_availability`** — adjudicated at PJM-NUC-1/1b (2026-07-16,
  owner-ordered build, gate pre-committed in §8.2.1 BEFORE deriving):
  build-time provenance gate **FAILED** (net tail-hour recovery −72 MW vs
  ≥ +75 MW) and the failure is structural — conserving the EIA-923 monthly
  anchor redistributes event-day energy onto near-full pool days, which ARE
  the scarcity days; dropping the anchor or pinning to EIA-930 hourly is
  rules-13/14-refused. "Not re-armable; another ISO needs its own derivation
  + gate." The later NYISO/CAISO/NEISO `K`s confirm the contrast (their G2
  retention 104 %/pass vs "PJM's was NEGATIVE" — nyiso-98). The artifact
  itself (`data/raw/nuclear-availability-PJM.csv`) reproduces byte-for-byte
  and stays the cross-ISO deriver's frozen reference. Re-open only with a NEW
  identification (a different level-anchor basis), not a re-run.
- **`hydro_dispatch_envelope` / `hydro_min_flow_floor`** — both derive from
  EIA-930 `NG:WAT` hourly (envelope: month×hod p95 ceiling; floor: Q95
  monthly exceedance — `scenarios.py` flag docs). PJM files **no `NG:PS`
  column** and its `NG:WAT` carries pumped-storage gross discharge — +6.5 to
  +7.0 TWh/yr (+72–78 %) above the 923 `HY` level, breaching the 3,334 MW
  conventional nameplate 1,437–1,572 h/yr (the pjm-143 keeper's own
  measurement, `EIA930_PS_FOLDED_INTO_WAT`). A p95 ceiling or Q95 floor of
  that series would encode Bath County's cycling onto conventional hydro —
  the same wrong-population defect pjm-143 refused at the level, at hourly
  grain (rule 14 misalignment clause). Blocked until a PS-separated hourly
  series exists for the PJM footprint; intake of one would re-open the trio
  under its own charter.
- **`winter_citygate_daily`** — three stacked facts: (i) the pjm-141 bar —
  measured within-day offer σ is $0.000000 on every thermal LP row, so no
  calendar-day series can move an intra-day differential; the cell survives
  on the winter-LEVEL story alone (queue item 10). (ii) No TETCO-M3 daily
  series exists on disk (`data/raw/gas-prices/` holds algonquin/caiso/miso
  citygate dailies and `transco_z6_iroquois_monthly.csv`; nothing M3-daily) —
  an intake precondition. (iii) No standing winter-level defect charters it:
  the keeper is CALIBRATED 9/9 and the post-pjm-137/138 winter reading is
  "the energy stack's LEVEL is right and the residual is SHAPE ONLY" (keeper
  note 3). Stays `U`; charter only on a demonstrated winter-level defect
  after intake.
- **The ERCOT offer-margin family** (`coal_offer_net_revenue_margin`,
  `cc_committed_offer_margin`, `coal_peak_offer_margin`,
  `coal_perplant_offer_level`) — every ERCOT identification reads the 60-Day
  SCED Submitted TPO disclosure: per-unit, identity-resolved,
  capacity-quantified. PJM publishes no equivalent: the DataMiner2
  energy-offers corpus is unit-masked (PJM-NUC-1b: `unit_code` is
  "identity-MASKED (base64-opaque)"; pjm-128: "no public unit-level DA award
  feed exists"). Consequences: `coal_perplant_offer_level` is blocked
  outright (per-plant identity is the identification). For the three
  class-level forms, the `measured_offer_surface` `R` (pjm-123/126/127,
  pjm-132 "Lane 2 ENDS") adjudicated the corpus for the net-load-binned
  SURFACE use — it does not by itself bar a curve-bottom class-LEVEL
  statistic (pjm-121's belt shows class attribution is derivable). But any
  PJM-instrument level identification must first solve capacity-weighting
  under masked identity, the pjm-126/127 conditioning-artifact lesson, and a
  rule-19 REPLACEMENT design against the armed owners of those prices
  (pjm-117/118 margin structure, the 60-scalar `offer_curve_by_group`
  surface, the midcurve belt, the coal passthrough sigmoids) — a
  DOF-retirement lane of the ercot144 shape, multi-session, with its own
  charter. Blocked as a single-lever candidate.

### 2.5 (b) — precedence

- **`import_hub_pricing`** — the keeper's `pjm_seam_measured_ladder` already
  owns seam-band pricing under rule 19: every seam band (MISO/NYISO/
  Carolinas/TVA/LGEE, import + export) is priced at the measured per-year
  Q-Q ladder (settlement-grade tie-line flow duration curves coupled
  quantile-by-quantile with measured PJM DA LMP;
  `derive_pjm_seam_ladders.py`), alongside `pjm_external_net_position_cut` +
  the measured per-border flow/export envelopes. A neighbor-hub-price
  mechanism is a second owner for the same phenomenon — admissible only as a
  replacement under its own charter with measured evidence the ladder
  mis-prices. The one chartering premise on record was refuted no-LP at
  pjm-141 §5.2 (overnight seam volume: the model tracks EIA-930 total
  interchange to ~1 GW with a sign that flips across years — wrong-signed
  for the 2023–24 overnight cell). Stays `U`; do not charter on the
  overnight cell.
- **`mass_cap_lp_row`** — the representation choice is module-adjudicated
  (`policy/cap_and_trade.py` header; emissions-mass-cap plan §2/§8): RGGI/
  CARB clear in a banked multi-sector market this power model does not
  contain, so the **adder path is the faithful backcast representation** and
  the row's endogenous dual is a power-sector no-bank **scenario** price.
  PJM's per-state budgets (VA counted 2023-only) are landed and the row is
  buildable — as forecast/counterfactual scenario work, not a backcast
  lever. Stays `U`.

### 2.6 (a) — forecast-lane and no-charter cells

- **`entry_dampers`**, **`transmission_expansion`** — mode-F rows; the FFR
  program owns them (entry_dampers MISO `O` at FFR-2B; the PJM half of the
  D-1 decision already measured the retirement-wave side). Stay `U` here.
- **`hydro_accreditation`** — mode-F adequacy-ledger term; PJM is `O`
  ("armed there too but unprobed", FFR-1C, with the published 0.38 BRA ELCC
  'Hydro Intermittent' factor already registered). The probe is a T0
  forecast A/B in the FFR lane, not a backcast solve. Stays `O`.
- **`lcr_tsl_published`** — the forecast half (PJM CETO/CETL) lives inside
  `capacity_deliverability_limits` (curated datatype present; 155 PJM rows
  this session). A backcast dispatch-side arming would need (i) a
  representable locality boundary and a posted in-window flow series (the
  NYISO admissibility test), and (ii) survival against pjm-137's measurement
  that zonal-scale interfaces carry only 3.06–6.34 % of PJM's DA congestion
  rent (the binding facilities are sub-zonal), with rule-19 reconciliation
  against the armed `pjm_east_interface_cut` + `pjm_measured_interface_limits`.
  Stays `U` with that bar recorded.
- **`td_loss_factor`** — NYISO `R` (Arm D); every keeper pins 0.0. For PJM
  the passing C1 16/16 free 12/12 is the operative measurement: a material
  demand-basis loss gross-up would break the passing energy balance. A
  nonzero proposal needs its own derivation (rule 24), and no defect calls
  for one. Stays `U`.
- **`startup_co2_reporting`** — reporting-only column, never in the LP; no
  dispatch, price, or gate effect. Arm opportunistically in an
  emissions-accounting session. Stays `U`.

---

## 3. Ranking verdict and the Phase-2 charter

The handoff's seed ranking is **partially confirmed, partially refuted by the
record**:

1. `state_carbon_pricing` — **confirmed rank 1** (§2.1). The Phase-2 lever.
2. `measured_chp_heat_rates` — **confirmed rank 2** (§2.2), behind carbon on
   materiality and design burden. Named successor for the next PJM session.
3. `nuclear_unit_availability` — **refuted as a candidate**: the seed said
   "data committed, narrow, clean A/B"; the record says the PJM build gate
   already failed (PJM-NUC-1b, pre-committed, structural). §2.4.
4. `st_gas_mustrun_p25` — **demoted**: admissible in principle but a no-op
   without a fleet-wide artifact re-basing under its own charter. §2.4.

Phase 2 (this session): pre-registered single-delta A/B of
`pjm_rggi_allowance_pricing` on the pjm-143b keeper, full pjm-144 protocol —
PREREG pushed before any arm solves; same-HEAD zero-delta control via
`replay_keeper`; years 2023 2024 2025 in one invocation per arm, sequential;
`legitimacy_diagnostics` on both arms; scorer from `metrics.json` only;
attestation from the committed A/B JSON. See
`results/calibration/PREREG-pjm146-rggi-allowance-2026-08-02.md`.

## 4. Test baseline (re-measured at HEAD `cb1c416`)

Recorded after the environment build completed — see the calibration-log
entry for the run result. pjm-145's baseline at f58339b was 11 failed /
5869 passed: `test_measured_chp_heat_rates` ×7 (stale `plant_table`
signature, §2.2), `test_outages` ×1, `test_ff_readiness_battery` ×1,
`test_consume_phase3d` zone parity ×1, `test_fleet_arrays_golden` ERCOT
golden ×1.

## 5. Matrix duties discharged this session (rule 28b)

Cell notes/citations updated in `docs/codebase-site/data/mechanism-matrix.js`
for: `st_gas_mustrun_p25` (verified 0/10 census), `winter_citygate_daily`
(no-M3-on-disk intake precondition), `hydro_dispatch_envelope` +
`hydro_min_flow_floor` (PS-fold blocker), `import_hub_pricing` (ladder
precedence), `storage_vintage_ramp` (sized), the offer-margin family (PJM
instrument bar), and `state_carbon_pricing` (the A/B verdict, whatever it
is). `U` cells stay `U` — notes still land. The `mechanism-testing-matrix.md`
§5.3 queue and `docs/calibration-log/pjm.md` take the session entry ending
"Next shorthand: pjm-147."
