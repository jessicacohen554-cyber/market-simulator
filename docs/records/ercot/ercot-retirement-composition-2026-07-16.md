# RC-2A — ERCOT retirement-level composition probe + forced-outage availability scoping

_Generated 2026-07-16 · flip-gate lane F-7 (`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §3 T-R3) · forecast-side, NON-KEEPER probe · no quarantine touched (2022 bridged, never solved/read; no ≤2021/2019/H1-2026 contact — rule 22) · no defaults changed · no dispatch-layer / offer-curve / backcast-keeper change. **Hard boundary:** the AS co-opt is G-20/G-22's lane — consumed as-is, never extended._

**One line.** At HEAD the committed lookahead+staged arm reproduces **byte-identically** (thermal 12.727 GW, coal 6.466 GW vs committed 12.73 / 6.47; recall PASS); D1 is unchanged (coal threshold still 1) so the BEFORE re-baselines to the committed values with **no arm-attributable delta**; composition alone cannot approach the actual 1.53 GW because the retirement screen is starved of AS+scarcity rent — **the CT screen sees ≈1.9 $/kW-yr against the SOM ≈68 anchor, a ~66 $/kW-yr residual handed to G-20/G-22**; and the structural fix for the in-year scarcity that never forms (ORDC $0.00 in every year, Uri included) is a measured-admissible correlated forced-outage availability model (design memo, Part D).

---

## A. HEAD state (re-baseline, verified before any run)

- **D1 coal threshold = 1** (`scenarios.py:283`, `retirement_years_coal`). D1 Option B (coal=3, RC-0B §d) has **not** landed. ⇒ the T-R3a BEFORE reproduction targets the committed **12.73 GW thermal / 6.47 GW coal unchanged**; there is **no D1 delta to attribute to my arms** (recorded per the RC-2A prompt's explicit ask). If Option B lands later, the BEFORE re-baselines and `staged_oversupply_thinning` should go default-off (rule 19 — the threshold would then carry the deactivation queue; RC-0B §a.6/§d D1).
- **D4 hindcast information gate: ON main.** `confirmed_retirements.py::load_confirmed_exits` / `load_announced_reversal_plants` take `as_of`; `runner.py:623-625` sets `confirmed_registry_as_of = Dec-31 of the EIA-860 vintage year = 2020-12-31` in hindcast mode. The ERCOT confirmed registry is only **Braunig 1/2 (instrument_date 2024-03-13)**, gated OUT (2024-03-13 > 2020-12-31). So no confirmed exit / post-2020 instrument can leak into the ERCOT legs — the run reproduces the committed run's accidental as-of-2020 behavior **deterministically** (closes the RC-0B §c.1-2 reproducibility land-mine). Verified `load_reversal_set('ERCOT')` = NONE (Braunig `superseded=false`, not a reversal).
- **Config-path invariance since 2026-07-08.** Every `scenarios.py`/`capacity.py` default added since the committed run is default-OFF or ISO-specific: ERCOT-71 LEG A (`ercot_noncampd_plant_availability=False`), LEG B (`ercot_offer_surface_midcurve_conditional=False`), `unit_partial_outage_windows=False`, `nuclear_unit_availability=False`, `ercot_gas_commitment_bridge=False`; RC-0C entry-screen instrumentation (diagnostic, no decision effect); RC-1B vintage resolver (default byte-identical). The built config is byte-identical to the committed `run_config` on every screen-relevant flag (`as_revenue_enabled=False`, `ercot_thermal_as_endogenous=False`, `screen_reserve_value_enabled=True`, `coal_thr=1`, `staged=True cap=3.0`, `entry_lookahead_reprice=True`, `limited_foresight_dispatch=True`). New `cache_key b98b4918 ≠ committed d8d5676d` (new config *fields* were added), so the run genuinely **re-solved** rather than hitting the committed cache — and reproduced it exactly (§B.1).

## B. Probe legs

**Leg (i) — HEAD reproduction of lookahead+staged (T-R3a).** ERCOT 2021→2025 realized, `entry_lookahead_reprice` + `staged_oversupply_thinning` (3.0 GW/fuel/yr) + `limited_foresight_dispatch`, 2020 vintage, 2022 bridged. Bundle `ercot-2021-2025-realized-g31staged-rc2a`.

**Leg (ii) — G-20/G-22 screen increment: NONE landed since 2026-07-12.** The retirement screen's sole AS pricing is the ORDC `reserve_price_signal` (`screen_reserve_value_enabled`, on since before the committed hindcasts); `as_revenue_enabled` / `ercot_thermal_as_endogenous` remain default-OFF. ERCOT-67/68/69 (2026-07-15) are all keeper/dispatch-side (May-2024 under-pricing, DAM offer surfaces), default-off, "keeper UNCHANGED", and do not feed the forecast screen. ⇒ **leg (ii) == leg (i)**; no increment to compose. Vintage of the unchanged G-20/G-22 screen posture: **2026-07-05→07-12**.

### B.1 T-R3 scorecard — ERCOT arm chain (GW; 2021→2025, scored 2023-25)

| arm | thermal | coal | gas_ct | gas_st | false-retire (%model) | recall≥300 | solar add | CO2'25 Mt |
|---|--:|--:|--:|--:|--:|:--|--:|--:|
| baseline (p2c / g30base) | 22.80 | 13.96 | 0.00 | 8.83 | 21.87 (95.9%) | FAIL | 0.0 | 95.2 |
| lookahead (g30lookahead = g31lookonly) | 15.83 | 13.96 | 0.00 | 1.87 | 14.90 (94.1%) | FAIL | 4.0 | 79.4 |
| staged (g31staged), committed | 12.73 | 6.47 | 3.02 | 3.24 | 11.29 (88.7%) | PASS | 4.0 | 115.6 |
| **staged, HEAD reproduction (this run)** | **12.727** | **6.466** | **3.023** | **3.237** | **11.292 (88.7%)** | **PASS** | **4.0** | **115.7** |
| actual | 1.53 | 0.93 | 0.50 | 0.00 | — | — | 25.1 | 193.6 |

**Reproduction: byte-identical CLEAN PASS.** Every retirement, addition, and CO2 figure matches the committed g31staged to the reported precision — confirming (a) D1 unchanged, (b) the D4 gate correctly excludes Braunig, (c) config-path invariance since 2026-07-08.

**IS-2020 == RAW for ERCOT (RC-0B §c.5).** `--rescore` pass: raw false-retire 11.292 GW (FAIL) → IS-2020 11.292 GW (FAIL), **reversal_exposure 0.0 GW**. ERCOT has no information-set-correct reversals (Braunig `superseded=false`) and no 8907/1715-class coverage gap (all its retirements on-sheet), so the IS-2020 adjustment is exactly zero — its 21.9 GW-class false-retire is genuine economic over-retirement, not a scoring artifact.

**T-R3 pre-registered grading.**
- (a) reproduce committed arm results at HEAD → **PASS** (byte-identical).
- (b) composition alone does NOT reach actual 1.5 GW (12.73 vs 1.53): **PASS-as-registered** — the deliverable is the residual screen-revenue level gap (§C), not an approach to 1.5.
- (c) solar entry strictly > 0 → reproduction **4.0 GW > 0: PASS** (matches BEFORE; the coal drop did not unlock more entry — G-31).
- (d) no in-year ORDC formation EXPECTED without the availability work → **CONFIRMED**: ORDC scarcity adder **mean $0.00/MWh, >$10 in 0 h, max $0 in every solved year (2021/2023/2024/2025)**, Winter Storm Uri (2021) included.

### B.2 Runtime honesty (RC-2A item 2)

Machine: **4 CPU / 15 GiB RAM**. Total wall **~1h44m** (05:07:30 → 06:51:31 UTC); RSS peak **~2.9 GB** — no OOM, and materially cheaper than the G-31 report's ~2.7h estimate on this fleet.

| year | role | wall | RSS (setup) |
|---|---|--:|--:|
| 2021 | seed solve (base fleet) | 8.5 min (510 s) | ~2.5 GB |
| 2022 | bridge (evolved, not solved — rule 22) | — (folded into 2023 evolution) | — |
| 2023 | solve | 12.1 min (726 s) | ~2.35 GB |
| 2024 | solve | 26.1 min (1567 s) | ~2.62 GB |
| 2025 | solve (P0 cold 2766 s + P1 warm 626 s) | 56.6 min (3396 s) | ~2.92 GB |

The staged arm's LP-bloat is real (2025 P0 cold solve alone 46 min, the fleet held fuller by staging), but on this ISO/fleet it stayed within a 15 GiB session — the G-31 "impractical for routine use" caution is a per-fleet judgment; the ERCOT 2020-vintage per-plant staged run is tractable here. **A looser cap is NOT proposed as a default.** Per RC-2A item 2 and rule 1, the G-31-noted 5–6 GW/fuel/yr option may be proposed **only** with its lead-time citation (RD-6 deactivation-notice minimums: PJM Part V ~90 d, ERCOT §3.14 NSO ~150 d, MISO Att-Y ~26 wk — **pending RD-6 intake**), **never fitted to the retirement count**; it trades LP size for a larger first wave, so it is a runtime lever, not a retirement-science lever. Since the run is feasible as-is, no cap change is recommended.

## C. Residual screen-revenue level gap — the handoff to G-20/G-22

_(Never closed here, never a fitted rent — rule 1.)_ Per-fuel `screen revenue stack` net_rev $/kW-yr (capacity-weighted; `capacity.py:1510`, the diagnostic the code explicitly maintains for SOM comparison), this probe's HEAD config (co-opt OFF; ORDC in-year $0 per §B.1-d), against the going-forward bar and the Potomac SOM net-revenue anchors (`cross-model-corridor-2026-07-13.md` §2.1):

| class | 2022 screen | 2023 screen | 2024 screen | 2025 screen | GFC bar $/kW-yr | SOM net-rev anchor $/kW-yr |
|---|--:|--:|--:|--:|--:|--:|
| coal   | 21.3 | 24.4 | 827.7 | 239.6 | 58.5 | (rev << bar → exits) |
| gas_cc | 12.5 | 12.5 | 837.8 | 265.3 | 30.0 | CC 89(24)/83(25)/228-272(23) |
| **gas_ct** | **1.9** | **1.9** | 757.3 | 241.8 | 21.0 | **CT 68(24)/52.6(25)/224-257(23)** |
| gas_st | 0.2 | 0.2 | 687.4 | 191.5 | 35.0 | — |
| nuclear| 306.4 | 306.4 | 1025.4 | 457.1 | 130.0 | (clears; survives — §45U path) |

**The signal is BIMODAL — the core structural finding.** The un-thinned first-wave screen years (2022/2023) consume the RAW 2021 duals on the over-supplied fleet (ORDC ≈ 0): CT sees **1.9 $/kW-yr**, starved → coal/gas over-retire. The later years (2024/2025) consume the `entry_lookahead_reprice` forward pro-forma on the thinned fleet: CT jumps to **757 then 242 $/kW-yr** (vs SOM CT 68) → retains everything (2024/2025 retire nothing; 2024→2025 decays because 2024's entry re-fills the stack — G-30/G-31). **Neither is the real market revenue:** one is starved of AS+scarcity, the other overshoots SOM ~11× because the pro-forma re-prices the whole thinned stack against the published ORDC curve — a screen-internal re-pricing, not in-year dispatch scarcity (the in-year ORDC stays $0, §B.1-d). The composition arms deliver a discontinuous revenue signal, not a physical one.

**Residual gap (the number handed to G-20/G-22):**
- **CT: HEAD screen net_rev ≈ 1.9 $/kW-yr vs SOM CT ≈68 → captures ~2.8%; residual ≈ 66 $/kW-yr.**
- **Decomposition (why 1.9, not the corridor's 17.1).** The corridor's 17.1 CT figure came from the stage-2 grid's `coopt` axis (`energy_reserve_coopt` + `ercot_thermal_as_endogenous` ON — the G-20/G-22 mechanism; config caveats: legacy bins + backstop). This probe runs that path **off** (consumes main as-is — the hard boundary). So G-20/G-22 owns two increments: **(i)** turning on the co-opt lifts CT ~1.9 → ~17.1 (+~15 $/kW-yr); **(ii)** even co-opt-ON, 17.1 vs 68 leaves **~51 $/kW-yr** — the level sits at ~25% of SOM. **Total CT residual to SOM: ~66 $/kW-yr (co-opt off) / ~51 $/kW-yr (co-opt on).**
- gas_cc: 12.5 vs SOM CC 89 → ~14%. gas_st: 0.2 (≈ no rent). Every merchant thermal class reads first-wave revenue far below its GFC bar (CT 1.9<21, ST 0.2<35, coal 21-24<58.5) → the economic screen cuts them → the over-retire.
- This is exactly plan §1.2-1 / T-R3(b): **every ERCOT absolute exit call stays conditioned on the ~25%-of-SOM scarcity/AS level until BLK-6 (G-20/G-22) closes.** Composition (timing) has done its job — the recall band is PASS and the coal false-retire halved — but the *level* is the open lane, and it is G-20/G-22's, not this one's.

---

## Part D — Design memo: correlated forced-outage / extreme-weather availability (no implementation)

### D.1 Why the availability model is the structural root
G-31 verdict (verbatim): the perfect-foresight LP on the over-supplied 2020-vintage fleet clears every hour with ample reserves; the in-year ORDC overlay = $0.00 in EVERY year of EVERY arm, Winter Storm Uri (Feb 2021) included — reconfirmed here (§B.1-d). The scarcity that really happened is physically absent from the in-year LP. Both screen misses trace to it:
- No in-year scarcity → no scarcity rent in the screen's attainable margin → marginal coal/gas_st read loss-making → economic over-retire.
- No scarcity-priced hours → solar entry cannot clear fixed cost → BLK-8 entry zero.

The G-30/G-31 arms **work around** this (lookahead pro-forma manufactures the signal in the screen's forward pro-forma; staged thinning delays exits until the pro-forma prices them). Neither makes the in-year LP tight — witness the bimodal, physically-inconsistent screen signal in §C. The genuine forward fix the G-31 verdict named: a measured-admissible correlated forced-outage model so tight hours form **physically** in-LP.

### D.2 What already derates availability (rule-19 inventory) — precise
The `(n_gen,T)` `availability` array (`fleet.py:1022`) seeds at `1−eford` but for THERMAL groups is immediately **superseded** by the statistical age model, then scaled by overlays. It enters the LP only as the per-hour bound `pmin ≤ P ≤ pmax×availability` (`dispatch.py:2875`), and post-solve it is exactly what the ORDC point-reserve reads (`scarcity.py:424`).

**FORECAST-mode active mechanisms** (the ERCOT hindcast carries only these):
1. **Statistical seasonal WEFOR/POF/derate age model** (`constants.py:1656` `THERMAL_AVAILABILITY`; `fleet.py:596,1331`) — always on; THE forecast forced-outage representation. `avail = 1 − WEFOR − derate`, minus POF in shoulder; summer keeps only 30% of WEFOR (`fleet.py:559`). Forecast levels: CC ~0.93 winter, COAL ~0.85, ST_GAS ~0.75. **Per-unit INDEPENDENT; NO weather driver.**
2. `maintenance_monthly_shape` (default True, FORECAST-ONLY, `fleet.py:1259`): puts the POF budget at Apr/Oct-Nov, **~0 at summer peak** — planned maintenance is scheduled *away* from peak, the opposite of a correlated forced event at peak.
3. `_SUMMER_CLASS_DERATE` (flat GT summer derate CC .10/CT .125), COAL CF ceilings, `BIN_FORCED_DERATE_BY_YEAR` (confirmed losses), nuclear monthly CF — all seasonal/static, none weather-correlated.
4. Weather-correlated derates EXIST but are ALL DEFAULT-OFF: `gt_ambient_derate` (hot), `temp_dependent_derate` (**refuted for the ERCOT gas fleet, 2026-07-09**), `neiso_gas_coldsnap_derate` (NEISO-only, single-fuel).

Every CAMPD/measured overlay (`historic_outage_overlay`, `unit_*_outage_windows`, `ercot_thermal_dam_availability`, `retiree_cems_cap`, `ercot_noncampd_plant_availability`, …) is **BACKCAST-ONLY** — gated on `outage_source=="historic"` (default `"statistical"`) and several additionally hard-gate `mode=="backcast"`. The measured Uri trips live here; the forecast hindcast never sees them.

**THE GAP.** Forecast mode's forced-outage representation (item 1) is (a) uncorrelated across units and (b) weather-blind, with maintenance actively moved off-peak. So even though it derates 15–25% on average, it NEVER concentrates the derate into a correlated peak-hour event — enough units are always up to clear any single hour → in-year ORDC = $0.00 even in Uri. The one correlated, weather-driven, reserve-shortage-forming derate in the codebase (`neiso_gas_coldsnap_derate`, `transmission.py:3504`, `frac = clip(slope·(t0 − TMIN), 0, cap)` keyed to one system daily-min-temp series → the whole gas fleet derates together) is the **working template** — but it is NEISO-only and single-fuel. ERCOT needs its generalization.

### D.3 Proposed mechanism — EFORd-conditioned correlated cold-/heat-event derate
Extend the availability builder so forced outages become a time-varying, cross-unit-correlated process keyed on the weather-year temperature series already in the model:

    avail[g,t] = 1 − wefor_residual[g] − excess_FOR(fuel[g], T_zone[t]; winterization)

- **Baseline:** cap the statistical WEFOR to a small residual for the affected classes (reuse the exact `wefor_residual`/`coal_drop_pof` machinery the historic overlays already use — `fleet.py:1234,1363,1423`) so the correlated model REPLACES the independent WEFOR share it now represents rather than stacking on it (in-fleet double-count guard, D.6).
- **Excess:** a per-class cold-weather (and symmetric extreme-heat) excess-outage function, monotone in temperature deviation, CORRELATED across the fleet because every unit reads the same zonal temperature series (the `neiso_gas_coldsnap_derate` pattern: one system TMIN → whole gas fleet derates together).

**Rule-13 admissibility (the test, met).** Regenerates forward for any year from forward drivers (weather-year temperature sample + per-class EFORd + fleet winterization state) and RESPONDS to changed conditions — a colder sampled year deepens the derate; a post-Uri winterized/hardened fleet shrinks it; more gas-CT share shifts the mix. A formulaic PHYSICAL input, never a measured outcome pinned to actuals; it never reads the price/volume residual. Passes the CLAUDE.md rule-13 test verbatim.

### D.4 Data needed
- **Baseline EFORd: ON DISK** — `data/raw/reference/nerc-gads-eford-*` (4 vintages 2018–2024) + the derived `EFORD` constants (coal .08 / gas_st .07 / gas_ct .06 / gas_cc .05). No new intake.
- **Weather-year temperature 8760: ALREADY in the model** (the zonal TMAX/TMIN series consumed by `gt_ambient_derate` / `neiso_gas_coldsnap_derate`).
- **NEW derivation — the temperature→excess-FOR curve per class** (the only new derive):
  - *Primary derivation/validation target:* measured ERCOT cold-weather outage events on disk — `ercot-outages.csv`, `tx-jan-aug23-unit-outages.csv`, `campd-unit-outages*.csv` (Uri Feb-2021, Elliott Dec-2022, Jan-2024), regressed on the coincident temperature series → excess FOR vs T by fuel.
  - *Citation anchor (off-disk, public — NOT MIS-walled):* the FERC/NERC Feb-2021 Cold Weather Report (ERCOT lost ~half the fleet at Uri peak), NERC cold-weather GADS bins → `docs/parameter-citations.md`.
  - *Winterization state (the forward-responsiveness lever):* ERCOT weatherization-compliance vintage / EIA-860.

### D.5 Backcast/forecast parity (no double-count with the historic overlay)
- Backcast ALREADY carries the ACTUAL outages via the CAMPD overlays (`outage_source="historic"`). The correlated model is therefore a **FORECAST-mode mechanism**; in backcast it must be SUPPRESSED (measured windows take precedence) so the same event is never counted twice — the precedence the overlays already enforce over statistical WEFOR.
- **Self-consistency validation (the rule-13 proof):** run the FORECAST correlated model on the 2021 backcast weather year → confirm it REPRODUCES the Uri-scale derate depth the CAMPD windows record. If the forward statistical model regenerates the measured event from weather+physics alone, it is admissible; if it can only match by reading the realized outage, it is a pinned outcome and FAILS.
- **Crossover diagnostic (2024–H1 2026, plan rule 22):** backcast (measured windows) vs forecast (model) against the same weather — the honest backcast→forecast availability-gap measure.

### D.6 Scope against double-counting with the ORDC reserve-error convolution — precise
The ORDC adder is POST-solve (`runner.py:1699`; skipped under `energy_reserve_coopt`, which is OFF in the hindcast). `adder = 0.5(VOLL−λ)·LOLP(R)` with `LOLP = 1 − Φ((R − mcl − mu_eff)/sigma)` (`scarcity.py:236`), `sigma_mw=1400`, over the online + offline (quick-start gas_ct/oil only) reserve `R`.
- **Point-derate channel is SAFE.** `R` reads `pmax×availability` (`scarcity.py:424`), so a NEW *deterministic* correlated derate lowers `R` and raises LOLP/adder additively and correctly. Feed the model here.
- **`sigma_mw` is the double-count surface.** ERCOT's published LOLP distribution (NP6-576-ER, the source of sigma/mu) is the HISTORICAL reserve-error distribution, which already combines net-load forecast error AND generation forced-outage/unit-trip uncertainty. So `sigma` already represents the stochastic SPREAD of forced outages around the point reserve. **Rule:** inject the new model ONLY as a deterministic derate on the MEAN availability (feeding R); do NOT inject forced-outage VARIANCE/scenario spread. If the model explicitly represents the forced-outage COMPONENT of reserve error, correspondingly REDUCE `sigma_mw` (or supply a re-derived NP6-576-ER table via `ordc_lolp_params_path`) so the convolution is not counting the same uncertainty twice. **Gate the sigma re-decomposition TOGETHER with the forced-outage flag** so they can never fire inconsistently.
- **Two more surfaces (name them):** (i) within the fleet, statistical WEFOR IS the forced-outage representation — coordinate via the `wefor_residual`/`coal_drop_pof` cap (D.3) or it double-counts inside `availability` before ORDC. (ii) The backcast measured scarcity-rent overlays (`ercot_rtordpa_overlay_series`, `ercot_dam_as_overlay_series`, already year-scoped to avoid RTORDPA↔DAM-AS overlap) fire in the same hours; a backcast forced-outage model deepening scarcity there would overlap realized rent — keeping the model forecast-only (D.5) avoids it.

### D.7 Implementation charter (staged; no implementation here)
- **Stage 1 (derive, frozen — rule 23):** per-class temperature→excess-FOR curve from the on-disk measured cold-weather outage events + the FERC/NERC citation; re-derives only on data update.
- **Stage 2 (wire, default-off):** forecast-mode `correlated_forced_outage` availability overlay in `fleet.py`'s availability builder, keyed on the weather-year temperature series, WEFOR-residual coordinated; ISO-generic, ERCOT-first; modeled on the validated `neiso_gas_coldsnap_derate` pattern. In `ScenarioConfig` + `run_config` (rules 5/24).
- **Stage 3 (double-count guard):** ORDC `sigma_mw` re-decomposition, GATED WITH Stage 2 (D.6).
- **Stage 4 (validate, not tune — rule 1):** (i) forecast-mode on 2021 weather reproduces the measured Uri derate depth (D.5); (ii) in-year ORDC now FORMS scarcity in the tight hours (the G-31 residual); (iii) re-run the retirement/entry hindcast to measure whether in-year scarcity closes the first-wave problem WITHOUT staging. The curve is calibrated to outage/temperature DATA and validated against scarcity-formation/retirement as INDEPENDENT checks — NEVER tuned to the retirement count (rule 1: never a fitted availability).
- **Acceptance:** T-R3 (retire/entry) + T-R5 invariants; LOYO within 2023-2025 before any default flip; forecast-validation dashboard only.

**How this closes the G-31 residual.** Stage 4(ii)/(iii) is the test the composition arms could not pass: replace the bimodal, screen-internal signal (§C) — starved raw duals in the un-thinned first-wave years, overshooting lookahead pro-forma later — with ONE consistent, bounded, physical scarcity price formed in the in-year dispatch. If it works, `staged_oversupply_thinning`'s LP-bloat (§B.2) and the lookahead's first-wave blind spot both become unnecessary, and the retirement screen's first-wave revenue rises toward SOM without any fitted rent — which is where the G-20/G-22 lane and this availability model must ultimately meet.

---

## Runs registered (forecast-validation dashboard only — never the backcast dashboard)
- `ercot-2021-2025-realized-g31staged-rc2a` — the HEAD reproduction leg (byte-identical to the committed g31staged; recall PASS, false-retire 11.29 GW, ORDC $0 all years).

## What this session did / did not do
- **Did:** reproduced the committed lookahead+staged ERCOT arm at HEAD (byte-identical); recorded the D1/D4/config-invariance re-baseline; determined leg (ii) is a no-op (no G-20/G-22 screen increment); quantified the residual CT screen-revenue gap (~66 $/kW-yr to SOM) as the G-20/G-22 handoff; reported per-year runtime/RAM; scoped the correlated forced-outage availability model as a design memo (Part D) with an explicit ORDC double-count analysis; registered the run on the forecast-validation dashboard.
- **Did not:** change any default; touch the AS co-opt / any dispatch-layer floor / offer curve / backcast keeper; solve or read 2022 or any ≤2021/2019/H1-2026 holdout (2022 bridged); implement the availability model; fit any rent, threshold, or availability to a residual.

*Produced 2026-07-16 (RC-2A). No LP parameter changed; no default flipped; no dispatch-layer/offer-curve/backcast-keeper touched; no holdout year solved or read. Reproduces `docs/hindcast-reports/ercot-g31-staged-thinning-limited-foresight-2026-07-08.md` at HEAD. Successor input to RC-2B (flip-recommendation memo) and the forced-outage availability-model charter.*
