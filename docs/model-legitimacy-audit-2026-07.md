# Model Legitimacy Audit — Magic Numbers, Forcing Mechanisms, and Overfitting Risk

**Date:** 2026-07-02 · **Scope:** third-party-style audit of the full `src/market_sim` codebase, the
six-ISO calibration lineage (≥400 solves, 92 registered runs), and the current keepers — with a
specific investigation of the CAISO CT-peaker behaviour flagged by the model owner.
**Companion prompt pack:** `docs/legitimacy-scrub-prompts-2026-07.md`.

---

## 0. Executive summary

The model's *architecture* is legitimate: prices are LP duals, renewables are decision variables,
commitment is parameter-driven UC physics, and the project's governance (probe vs keeper, the
2026-06 measured-data audit, demoted answer-injection overlays, machine-enforced rubric) is real
and unusually self-aware. **No current keeper carries a direct pin of model output to actuals.**
Two past violations (HSL output-target rescale, BTM benchmark circularity) were found and fixed by
the project itself.

The audit nevertheless confirms the owner's complaint and locates the systemic risks:

1. **The CAISO CT-peaker forcing is real, is in the current keeper (caiso-42), and comes from three
   stacked engines** — a reliability floor whose day gate binds **all 24 hours**, an evening
   net-load drag, and an RA startup bridge that applies CC restart economics to 1-hour-min-down
   CTs. Model CT output for hours 0–14 has coefficient of variation **0.000** (perfectly flat
   ~134–157 MW every day) vs 0.35–0.45 in CAMPD actuals; ~half of modeled CAISO CT energy sits at
   that floor. The annual-volume scoring rubric *rewarded* this — nothing scores diurnal shape.
   *(RESOLVED 2026-07-05 — scrubbed and verified at HEAD; see §1.4.)*
2. **The dominant overfitting surface is the tuned-scalar population iterated in-sample:** ~290
   residual-identified scalars model-wide (~230 in the per-ISO offer-curve multiplier dicts and
   coal sigmoids), selected over ≥400 solves all scored on the same three years, with a
   purpose-built Jacobian joint-move solver optimizing knobs against the backcast error. Offer-curve
   tuning is sanctioned (rule #1) — but there is **no held-out data anywhere**: the designated
   holdouts (2022, H1-2026) have never been scored, and the one out-of-sample experiment ever run
   (ERCOT statistical mode, 2026-06-16) **doubled the failure count** and was never repeated.
3. **The scored surface is quietly saturated with outcome-derived inputs:** delivered EIA-930
   output as the renewable CF upper bound (pins wind/solar wherever no HSL exists), per-year
   measured nuclear monthly CF, EIA-930 hydro budgets, the measured CHP export floor, and the NYISO
   measured interchange band. Each has a defensibility argument; jointly they mean gas/coal/CT are
   the only genuinely free classes — precisely the ones the tuned offer curves then target.
4. **A handful of fitted scalars sit inside keepers against the rules' spirit:** the CAISO 7,500 MW
   WECC cap (hand-tightened from measured 8,300; the project's own caiso-46 probe calls it "an
   over-tight fitted scalar" generating the entire 2023 scarcity tail), per-plant/per-year coal CF
   ceilings, CHP BTM shares trimmed to close a run-61–65 residual, an env-var-tunable import-offer
   band anchored to observed negative-price prevalence, and ERCOT-fitted offer bands silently
   inherited by MISO/NEISO through the generic fallback.
5. **Forecast/backcast parity gaps:** the CAISO RA must-offer floor is built only in
   `scripts/run_calibration.py`, never in `runner.py` — the mechanism the backcast is calibrated
   *with* is absent from the forecast it is calibrated *for*.

Sections 2–6 give the evidence; §7 the diagnostic suite; §8 the protective rules. The prompt pack
sequences the scrub.

---

## 1. The CAISO CT-peaker finding (owner's complaint, confirmed)

### 1.1 Symptom — measured from the dashboard payloads

Fleet-average MW by hour-of-day, CAISO CT_PEAKER (43–44 plants), model vs CAMPD actuals.
Current keeper **caiso-42** (the caiso-48 probe is essentially identical):

| | h0 | h2 | h4 | h6 | h8 | h10 | h12 | h14 | h16 | h18 | h19 | h20 | h22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2023 model** | 134 | 134 | 134 | 134 | 134 | 134 | 134 | 134 | 335 | 699 | 733 | 715 | 135 |
| **2023 actual** | 93 | 63 | 138 | 249 | 108 | 91 | 125 | 236 | 741 | 1292 | 1114 | 809 | 250 |
| **2024 model** | 157 | 157 | 157 | 157 | 157 | 157 | 157 | 157 | 277 | 625 | 749 | 741 | 159 |
| **2024 actual** | 241 | 191 | 257 | 310 | 143 | 104 | 124 | 263 | 676 | 1077 | 974 | 759 | 367 |

- **Hours 0–14 model CV: 0.000 (2023, 2024)** — literally constant. Actual CV: 0.35–0.45, with a
  real morning-ramp bump (h4–7), a real midday dip, and an evening peak the model reaches only half of.
- Floor-level energy ≈ 134–157 MW × 8760 h ≈ **1.2–1.4 TWh ≈ 50–55 % of all modeled CT energy**.
- Real CAISO CTs *do* run overnight sometimes (actual h0–5 ≈ 60–330 MW) — but shaped by conditions,
  never flat. Flatness is the signature of a forced floor, not economics.

### 1.2 Root cause — three stacked engines, composed via `np.maximum` into `FleetArrays.min_gen`

**(a) Generic reliability floor, all-24h day gate** — `reliability_floor=True` in every CAISO bundle
including the keeper. The CAISO CT_PEAKER netload limbs
(`data/raw/reference/reliability_floor_coeffs_CAISO.csv`: NP15 0.1389, SP15 0.1626, ZP26 0.1231)
flag every day whose **peak** system net-load exceeds 27.57 GW (the p70 → ~110 days/yr) and then
bind **all 24 hours of the flagged day** (`model/transmission.py:2884-2892`,
`flagged = np.repeat(day_flagged, 24)`). The CSV carries no `start_hour`/`end_hour`, so the
sub-daily window (`transmission.py:2905-2909`) never engages. Result: 12–16 % of zonal CT capacity
forced on at 3 a.m. one day in three. *The mechanism's own derivation contradicts this*:
`docs/caiso-ct-netload-drag-2026-06.md` found overnight CT CF ≈ 0 even at high net load.

**(b) CT net-load drag** — `ct_netload_drag=True` in the keeper; hour-gated 15–22
(`data/fleet.py:1975-2050`), floor `clip(0.00901×netload_GW − 0.1124, 0, 0.36)`. This is the
*right shape* of mechanism (external driver, evening window, forward-derivable) — the template for
what (a) should look like.

**(c) RA must-offer startup bridge applied to CTs** — `caiso_ra_mustoffer` is default-ON for every
CAISO calibration run (`scripts/run_calibration.py:1111`); eligible classes are hard-coded
`("CC_REGULAR", "CT_PEAKER")` (`model/commitment.py:775`). The *physical* bridge (gap < min-down)
can never fire for CTs (min-down = 1 h), but with `caiso_ra_startup_bridge` on (caiso-44/45/48),
**any** overnight gap bridges when `startup > (MC − LMP)×0.26×gap_hours` — and in a cheap-gas year
CT MC sits within a few $/MWh of the overnight LMP, so `hold_cost ≈ 0` and CTs are floored at 26 %
of plant pmax through the night. The caiso-48 decommit control only prunes **midday-surplus**
bridges; overnight bridges survive by construction. Restart-economics bridging is real UC physics
**for CCs** (min-down 4–8 h, $24–64/MW starts); for fast-start CTs (~$12–25/MW, 1-h min-down) it
forces exactly the units that *do* cycle off overnight in the real market.

### 1.3 What is and isn't acceptable here (aligned to the owner's stated position)

- Net-load / temperature-tied reliability commitment for CTs and steam gas: **acceptable in
  principle** (precedent: PLEXOS/Aurora min-commit constraints, RMR schedules) — *provided the
  floor binds in the hours the driver justifies*.
- Mine-mouth / take-or-pay coal must-run floors, coal PRB sigmoids, offer-curve tranche
  customization: **acceptable** — economics-driven; stays.
- A flat around-the-clock CT floor, a startup bridge holding CTs overnight, or any floor sized from
  the class's *observed output* to close a volume residual: **not acceptable — scrub.**

**Fixes** (sequenced in the prompt pack): window the CAISO CT netload limbs to the evening ramp (or
retire them in favour of the drag, which already covers h15–22); gate bridge eligibility on
`min_down_hours ≥ 4` instead of a hard-coded class tuple; reconcile the three stacked CT floors
into one mechanism; add the shape diagnostics of §7 so this class of feature cannot silently return.

### 1.4 RESOLUTION — the three-engine forcing is scrubbed and verified at HEAD *(2026-07-05, W3-P2 `caiso-52-ct-scrub`)*

**Red flag CLOSED at the mechanism level.** All three fixes above are merged; the CT forcing is now a
single audit-sanctioned mechanism, defended at three independent code layers so it cannot silently
return:

1. **All-24h reliability CT limbs → windowed then disabled.** `reliability_floor_coeffs_CAISO.csv`
   CT_PEAKER/CT_CHP netload limbs carry `start_hour/end_hour = 15/21`; every CAISO row is now
   `enabled=False` (loader: `enabled AND NOT r1_disabled`, `iso_configs.py:1012`). The
   `np.repeat(day_flagged,24)` all-24h gate can no longer bind.
2. **Rule-19 code dedup.** `drop_drag_owned_reliability_specs` (`iso_configs.py:1059`) drops every
   CT_PEAKER reliability limb whenever `ct_netload_drag` is active — a re-enabled limb still cannot
   stack with the drag.
3. **Bridge eligibility by physics.** The economic RA startup bridge gates on
   `min_down ≥ RA_BRIDGE_ECON_MIN_DOWN_HOURS` (`constants.py:120 = 4.0`; `commitment.py:816`, rule 17);
   fast-start CTs (min-down 1 h) are never economically bridged.

**Verification** (`results/calibration/caiso55_ctscrub_head`, byte-faithful replay of the caiso-51
keeper config at 2026-07-05 HEAD, all 3 years; `legitimacy_diagnostics.json` committed). The §1.1
symptom is gone: CT_PEAKER off-peak CV ratio **0.000 → 3.05–3.52**, D-4 off-window binding **62–66% →
0%** all years, CT forcing now one windowed mechanism (net-load drag; RA-bridge CT share <0.4%). The
flagged "keeper-reproducibility drift" (CT ~3.4→~1.7 TWh) is the **scrub effect** vs the pre-scrub
keeper, reproducing committed caiso-52 (CT 2.12/1.73/1.30 vs 1.97/1.56/1.15 TWh) — not a bug.

**Still open, but NOT a floor-scrub item (rule #1 — do not re-floor):** D-2 CT forced share
59.7/66.7/69.4% > 10% persists because the P1 energy-only zonal merit order prices thermally-dominated
CTs out of the evening ramp — the **evening-merit structural gap** (`FINDING-caiso-evening-merit-2026-07-04.md`),
needing CC ramp/min-up-down commitment + sub-zonal LA-basin transmission (a large build). The scrubbed
config carries the disclosed C3a evening-scarcity regressions, so **no keeper swap**: keeper stays
caiso-51 until that structure lands. D-5 parity (the w2-caiso-ra-p2 wiring gap) and ST_GAS D-1 shape are
separate, pre-existing. Full disposition: `docs/calibration-log.md` 2026-07-05 CAISO caiso-55 entry.

---

## 2. Forcing-mechanism legitimacy matrix

Verdicts: **STRUCTURAL** = real market physics/design, keep. **DwC** (defensible-with-conditions) =
legitimate mechanism class, needs the stated repair/grounding. **FIT-FORCING** = exists to move an
asset-class residual; scrub from keepers (may survive only as an explicitly-labelled default-off
diagnostic probe).

### Commitment layer (`model/commitment.py`)

| Mechanism | Toggle / location | Verdict | Condition / action |
|---|---|---|---|
| P2 economic commitment screen (min-down `_merge_runs`) | `commitment_enabled`; L333–479 | **STRUCTURAL** | — |
| RA must-offer *physical* bridge (gap < min-down; floor 0.26 = CAMPD measured min-stable) | `caiso_ra_mustoffer`; L616–842 | **STRUCTURAL** | 0.26 is a physical, forward-reproducible input (the caiso-40 re-grounding from 0.40 was done right). Only ever fires for CCs. |
| RA *startup* bridge — CC eligibility | `caiso_ra_startup_bridge`; L813–827 | **DwC** | Bounded by DA horizon + decommit (caiso-48). Sensitive to P1 LMP bias — keep the decommit screen. |
| RA startup bridge — **CT_PEAKER eligibility** | hard-coded tuple, L775 | **FIT-FORCING** | Remove CTs: gate on `min_down_hours ≥ 4` (physics), not class names. |
| Bridge decommit control (DA horizon, RUC-order) | `caiso_ra_bridge_decommit`; L530–613 | **DwC** | Right direction; does not fix the CT limb (only prunes midday surplus). |
| NYISO reserve-adequacy commit (measured spinning req) | `nyiso_synchronised_reserve`; L845–914 | **DwC** | Requirement is a market-design quantity — admissible. |
| ERCOT AS-aware commit (measured ASPLANNP433) | `ercot_as_aware_commitment`; L917–1028 | **STRUCTURAL/DwC** | — |
| Coal P1 pin + adequacy backstop | L1031–1174 | **STRUCTURAL** | Internal consistency, not actuals. |

### Min-gen floors (`data/fleet.py`, `model/transmission.py`)

| Mechanism | Toggle / location | Verdict | Condition / action |
|---|---|---|---|
| Nuclear must-run | `fleet.py:1529` | **STRUCTURAL** | — |
| CHP steam-following floor (EIA-923 min-month CF × 40 %) | `chp_steam_following` | **STRUCTURAL** | Price-inelastic steam host. Never extend the construction to merchant classes. |
| CHP export floor at measured class CF (backcast-gated) | `chp_export_floor_measured` | **DwC** | Steam-host physics argument is genuine and it is mode-gated; but the floored level *is* the measured outcome, so CHP C1 accuracy is largely fed in — exclude CHP classes from skill claims (§7 D-11). |
| Coal take-or-pay / mine-mouth must-run + PRB sigmoid passthrough | `fleet.py:4036`, sigmoids | **STRUCTURAL** | Owner-accepted; economics-driven. Per-plant %s are CEMS-derived min-load *behaviour* — admissible as physics; freeze the derive script (§8 rule 22). |
| CT/ST net-load drag (evening-gated hinge, regressed vs net load a priori) | `ct_netload_drag`, `gas_st_netload_drag` | **DwC** | The template mechanism. Coefficients are fitted to the scored years — validate leave-one-year-out (§7 D-8) and freeze. |
| Generic reliability floor registry (temp/netload day gates) | `reliability_floor`; `transmission.py:2693` | **DwC** | **Repair: CAISO CT netload limbs must carry an hour window** (or be replaced by the drag). Any all-24h limb needs an explicit physical justification (steam boilers spanning multi-day events qualify; fast-start CTs do not). |
| **CT must-run per plant (observed EIA-923 monthly gen injected as floor)** | `ct_mustrun_per_plant` (default-off) | **FIT-FORCING** | Correctly demoted; never in a keeper; candidate for deletion. |
| **CT deployment overlay (floor to measured CEMS output)** | `ct_deployment_overlay` (default-off) | **FIT-FORCING** | Same. The per-ISO parquet artifacts (`ct_deployment_floor_CAISO.parquet` etc.) are re-armable answer keys — delete or quarantine (§7 D-9). |
| **Reliability deployment overlay (load-pocket CC/coal/ST CEMS floor)** | `reliability_deployment_overlay` (default-off) | **FIT-FORCING** | Same. |
| **CAISO gas commitment floor (0.8 × measured EIA-930 NG:NG profile, h9–16)** | `caiso_gas_commitment_floor` (default-off) | **FIT-FORCING** | The prior "midday forcing" the owner flagged. Already out of keepers (Step-1 removal); keep it that way — diagnostic probe only. |
| **Deprecated ORDC reliability-deployment MW offset** | `ordc_reliability_deployment_mw` (default 0) | **FIT-FORCING** | Fitted to the 2023 LMP residual, deprecated — and *re-swept after deprecation* (calibration-log:185). Delete, don't deprecate. |
| NYISO local self-supply (Zone-K LMIC rule; 0.45 set "a touch below" the realized share) | `nyiso_local_selfsupply` | **DwC** | Market-design rule, but the fraction is outcome-anchored — re-ground on the LMIC requirement itself. |
| NEISO cold-snap gas derate | ScenarioConfig params, NERC-cited | **STRUCTURAL** | Availability *reduction*, not forcing. |

### Offer-curve quasi-forcing

Committed tranches bidding below true SRMC (caiso-48: CC committed 0.90×, ST_GAS 0.81×) emulate
commitment through sub-cost offers. Inside the owner's accepted offer-curve scope, but it is the
soft sibling of a must-run floor and **feeds the bridge detector** (cheap committed band → P1 runs →
bridges). CC committed shares from CAMPD P5-of-online-CF are physical min-stable parameters —
admissible. Flag: any committed-tranche multiplier below ~0.85 should carry a written physical
rationale (fuel contract, heat-rate spread), not just a residual improvement.

---

## 3. Magic-number audit

Full sweep of `src/market_sim` (config, data, model, policy, results, runner). Classes:
**A** = cited physical/market constant (~200+, dominated by `constants.py`, `scarcity.py`,
`policy/` — genuinely good compliance). **B** = uncited-but-plausible structural literal (~75;
rule-#5 violations, low fit-risk). **C** = suspected fitted/tuned (~29 findings ≈ 95 literals).

### Class C — the complete list, ranked

| # | Location | Value(s) | What it is | Why C |
|---|---|---|---|---|
| C-1 | `scenarios.py:2722-2860` `COAL_SIGMOID_DEFAULTS` | ~40 literals (per-ISO PRB/lignite/bit/sub/waste floor/ceil/mid/slope) | Gas-keyed coal offer-passthrough sigmoids | Explicitly "the per-ISO **tuned** curves" with run-numbered residual narrative ("Ceiling 1.25→1.32 (PJM run 16)… pulls coal toward EIA-930 in every year"). **Sanctioned by rule #1 and by the owner** — but the largest fitted surface in the model, invisible to `parameter-citations.md`, and identified in-sample only. |
| C-2 | `fleet.py:505-521` `COAL_MAX_CF_BY_PLANT` | 0.90/0.80/0.99/… + `(6179, 2025): 0.78` | Per-plant coal availability ceilings, one per-plant-per-**year** | Outcome-shaped caps "so coal does not over-run"; the year-specific override has no forward analogue — closest thing to a pin in a keeper. |
| C-3 | `constants.py:1383-1411` | storage 169.0 / ct 22.0 / st 15.0 / cc 8.0 $/kW-yr; REF_GW 4.0; EXPONENT 2.5 | ERCOT AS revenue + saturation curve | "Calibrated so the observed crash is reproduced" — exogenous revenue stream fit to the observed 2023→25 AS collapse; drives retirement/entry/storage economics in *forecasts*. |
| C-4 | `fleet.py:4103-4113` `CHP_BTM_PCT_BY_SECTOR` | 40→35, 60→50 | CHP behind-the-meter pull-out shares | Comment admits it: trimmed "after the Run-61..65 backcasts showed" the CF cap was binding — direct residual fit, in a hardcoded dict outside config. |
| C-5 | `iso_configs.py:321` | **7,500 MW** | CAISO WECC simultaneous import cap | Hand-"tightened from 8,300 (raw p01) to 7,500" against the EIA-930 import tail; caiso-46 probe: "the calibrated cap, not physics, generated the 2023 scarcity tail". Replace with reconciled MIC/path data (open rule-#12 thread). |
| C-6 | `interchange_config.py:72-147` | per-ISO `IMPORT_TRANCHES`/`EXPORT_TRANCHES` (MW, $/MWh) ladders; `atc_base_fraction` 0.43/0.56; `ATC_SOLAR_K` 1.5 | Seam supply curves + corridor derates | The repo's own comments call them "the static **fitted** IMPORT_TRANCHES"; the CAISO ladder was historically re-fit against the model's *own* solved price (self-referential; now a fallback behind measured-price paths). NYISO's per-year ladders (scarcity rung 68.4→79.7→135.2) track realized year levels. *(NEISO portion RESOLVED 2026-07-06 — ladders rederived from measured data only: per-seam Q-Q duration coupling of measured ISO-NE DA LMP with EIA-930 per-seam flows, NYISO proxy-bus anchors; `scripts/derive_neiso_import_tranches.py`, identification now measured/rule-23-frozen. CAISO fallback ladder + NYISO year-keyed rungs remain open.)* |
| C-7 | `transmission.py:1857-1858` | `_CAISO_SOLAR_SHAPE_NL_HI/LO_PCT = 30.0/10.0` (env-var overridable) | Net-load band collapsing the import offer to the negative floor | Anchored to *observed negative-price prevalence*, "validated to ~100 % precision" against actual LMP — plus an **off-the-books env-var tuning channel**. |
| C-8 | `scenarios.py:286-307, 1502-1507` + `constants.py:154` | 1.23/1.28/1.32/1.22 committed-econ HR mults; 1.15/1.10/1.08 peak penalties; coal tranches 0.30/0.25/0.45, passthrough 0.35 | Core offer-curve step sizes | All "Tier 3 (calibration)" / needs-citation; set clearing prices every hour. Sanctioned mechanism, undisciplined values. |
| C-9 | `fuel.py:2929-2934` `_PRB_PRICE_CALIBRATION` | lignite 1.45; PRB 2.15/2.00/2.00; shares 0.42/0.12/0.46 | Delivered coal cost trajectories | Named "calibration"; "user calibration" source line; feeds coal MC directly, forward curve built on the calibrated average. |
| C-10 | `reserve_config.py:44-65` | 0.01/0.10/0.18 quadrature weights; 0.065, 1160, 0.24, 0.017, 0.00418, 0.025 | ERCOT AS-requirement regression coefficients | Fit target is the *published requirement MW* (defensible under rule #12), but the coefficients are uncited odd-precision fits. |
| C-11 | `offer_curves.py:136-143, 535-550` | CC (0.30/0.60/0.10), ST (0.40/0.50/0.10), CT (0/0.88/0.12); `getattr` fallbacks 1.2/1.8/1.5/1.1/1.3 | Generic (non-CAMPD) gas tranche shares + buried fallback HR mults | "Tier 3 — tune per ISO"; the fallbacks are inline logic literals in the offer path — and they leak **ERCOT-fitted bands into MISO (~26 scalars) and NEISO (~19)** via the generic fallback, contradicting the no-cross-ISO-leakage rule. |
| C-12 | `fleet.py:4208-4213` | 15.0 × 4 plants | CC peaking-tranche % override | Applied to exactly "the four F-class CCs the model over-runs" — tranche moved to fix a known over-run. |
| C-13 | keeper configs | NYISO/NEISO `CT_PEAKER peak = 13.15×` | Offer tail | Uncited ERCOT inheritance carried across ISOs (NEISO-42 capped to 4.0 but wasn't promoted). NYISO CC econ_high 1.21 retained *because* removing it cratered C3a −24 % — identified purely by the price residual. |
| C-14 | `transmission.py:312` | `CAISO_BIDIR_EXPORT_CAP_MW = 3500.0` | Signed-tie export cap | Measured 2024 export *peak* baked static; the code's own comment flags this as the approach the per-hub successor removed. |
| C-15 | ERCOT keeper | `wefor_residual = 0.06` (PJM 0.015); `wefor_multiplier = 0.7` | Wind EFOR adjustments | The names admit residual identification; the 0.7 haircut's stated purpose is coal shoulder-month generation. |
| C-16 | `eia_loader.py:72-77` / `iso_configs.py:264-266` | PGE-TAC {NP15 0.86, ZP26 0.14} | Zonal load split | Self-labelled "Tier 3 — calibration"; preserves a prior ratio of unknown provenance. |
| C-17 | `constants.py:1885-1887` | Long_Island 0.45 | NYISO LI self-supply floor | Anchored on the 2023 *realized* share (≈0.48) "set a touch below". |
| C-18 | `constants.py:335-341` | 0.85/0.89/0.87/0.86/0.85 | Per-ISO gas availability factors | "was 0.83"/"was 0.88" adjustment trail + three "TODO: verify" — calibration nudges under a NERC GADS label. |

Retired-but-instructive (the governance working): PJM PS $10 adder ("calibrated so PJM PS lands
near its observed ~3.5-4 TWh/yr" — retired as a mis-measured-residual fit), NEISO AGT convexity 7.0
("chosen so switching tracked the measured oil burn" — retired for measured daily prints), ERCOT
RTORDPA offset. `scenarios.py:2225-2237` still documents the retired PS adder — stale doc.

### Class B highlights (fix opportunistically)

Inline `EFORD.get(fuel, 0.05)` / `VOM.get(fuel, 2.5)` fallbacks in `capacity.py` (11×, should be
pure table lookups); the 5 %-of-pmax run detector in `commitment.py`; ~22 geographic lat/lon zone
boundaries in `zone_assignment.py` (4 PJM cuts self-flagged "Tier 3 — verify"); uncited interior
TTC mesh values in `iso_configs.py`; `_COAL_CHP_FLOOR_FACTOR 0.85`; `voll=5000` fallbacks;
percentile defaults. None move the backcast materially.

### Citation-system findings

`docs/parameter-citations.md` carries **439 "needs-citation" flags**, omits the
`COAL_SIGMOID_DEFAULTS` values entirely (the largest fitted table is invisible to the citation
system), and retains stale entries for retired knobs (AGT convexity, sigmoid_midpoint, PS adder).

---

## 4. Measured-data leakage inventory (rule #13 compliance)

The 2026-06 internal audit's claims all verified against current code (overlay defaults off,
HSL rescale gone, mode gates in place). Severity: **HIGH** = pins a large scored quantity via a
thin argument; **MED** = outcome-derived with a genuine forward analogue; **GOV** = off, governance
risk only; **FIXED** = historic.

| # | Mechanism | Where | Severity |
|---|---|---|---|
| L1 | **Delivered EIA-930 output as renewable CF upper bound** wherever no HSL/potential series exists (all non-fallback ISOs; ERCOT 2024/25). Wind/solar are decision variables, but with UB = the delivered outcome the LP rides the bound — the renewable C1 rows score plumbing. | `renewables.py:1736-1739` | **HIGH** |
| L2 | **NYISO monthly net-interchange reconciliation band targeted at measured EIA-930** (~19–23 TWh/yr held to the measured schedule). Aurora/PLEXOS boundary-flow precedent is a fair defense; still the largest single outcome-anchored volume in any keeper. | `transmission.py:3116-3219`; NYISO keeper | **HIGH** |
| L3 | **`NUCLEAR_MONTHLY_CF_BY_YEAR`** — per-(ISO, year) measured EIA-923 monthly nuclear CF (~234 literals; near-must-run ⇒ the nuclear C1 row is essentially copied in). Derived from net *generation*, not outage records. | `constants.py:383-459` | **MED-HIGH** |
| L4 | **`chp_export_floor_measured`** — CHP min-gen rides the plant's measured class CF for the solved year (~32 TWh ERCOT CC_CHP). Mode-gated, documented, steam-host physics real — but the floored level *is* the outcome. | `fleet.py:5431-5446`; ERCOT keeper lineage | **MED-HIGH** |
| L5 | **Regression-fitted floors/drags** (temp→CF coefficient CSVs, net-load hinges, CC cap at CAMPD p99.9) — pass the admissibility test formally, but coefficients are fitted on the same years being scored; no leave-year-out fit reported. | `scenarios.py:1887-1911`; coeff CSVs | **MED** |
| L6 | **EIA-930 monthly hydro budgets** (CAISO/NEISO keepers) + MISO Manitoba per-year firm MW — hydro C1 rows near-vacuous; industry-standard, forward analogue exists. | keeper defs; `interchange_config.py:473` | **MED** |
| L7 | **NYISO per-year import price ladders** (scarcity rung 68.4→79.7→135.2 across 2023/24/25) — year-keyed levels with no independent citation. | `interchange_config.py:101-125` | **MED** |
| L8 | **CAISO static import ladder historically re-fit against the model's own solved price** — self-referential; superseded in the keeper by measured-hub-price paths but still the default fallback. | `interchange_config.py:73-80` | **MED** |
| L9 | **CEMS deployment pins** (`ct_deployment_overlay`, `reliability_deployment_overlay`, `ct_mustrun_per_plant`) — the canonical forbidden pins; off in all keepers, keeper-enabled as recently as runs 115b/118/122/123, **no CI check prevents re-enablement**. | `scenarios.py:1783-1821` | **GOV** |
| L10 | **`ordc_reliability_deployment_mw`** — deprecated fitted offset, *re-swept after deprecation*. | `scenarios.py:399-410` | **GOV** |
| L11 | **BTM benchmark circularity** — the CHP "actual" was computed from the model's own dispatch; every pre-fix keeper's CHP C1 pass is untrustworthy. Fixed 2026-07-02. | `run_calibration_full._btm_frame` | **FIXED** |
| L12 | **HSL output-target rescale** — the exact forbidden anti-pattern; fixed 2026-06-17. | `renewables.py` (removed) | **FIXED** |
| L13 | Admissible measured **inputs** (historic outage windows, F923 delivered fuel, CEMS heat/emission rates, hub-basis overlays, measured GTC/TTC/ATC, published ORDC/BPM curves) — pass the forward-analogue test. Input-gap note *(reframed 2026-07-13, owner directive — NOT a caveat on backcast skill)*: the D-7 statistical-mode ablation showed the historic-outage overlay alone carries 5→9 of the ERCOT fit. A backcast is scored *with* the year's admissible measured inputs by construction — that is what the mode measures — so an overlay-carried delta deducts nothing from a backcast result and needs no asterisk. The delta's use is as the **backcast→forecast input gap** (accuracy a forecast gives up to statistical inputs): forecast-uncertainty information for error bars and the crossover window, reported beside D-7, never as a caveat on a commercial-grade backcast metric. | various | — |

**Net picture:** with wind, solar, nuclear, hydro, CHP, and (NYISO) net imports substantially fed
from measured realizations, **gas/coal/CT are the only genuinely free classes** — and those are the
ones the ~230 tuned offer scalars target. In-sample class-volume passes therefore overstate skill
even before overfitting is considered.

---

## 5. Overfitting risk assessment

### 5.1 Free parameters vs data

~**290 residual-identified scalars model-wide** (census below) against, per ISO, ~100–130 strongly
correlated observation cells (3 years × class volumes + monthly LMPs + shape/CO₂ metrics), scored
as coarse pass/fail bands. Selection ran over **≥400 solves in a 6-week window**, all scored on the
same three years; the registry's top-15 retention hides ~80 % of the search.

| ISO | Lineage (solves) | ≈ class-(c) scalars | Dominant surface |
|---|---|---|---|
| ERCOT | ≥165 (+ renumbered 20–26) | ~75 | offer bands (~54), coal sigmoids (12), take-or-pay tranches, wefor pair, AS saturation |
| PJM | ≥75 | ~83 | offer bands (~54), sigmoids (12), fitted seam ladders (16) |
| MISO | ≥38 | ~42 | sigmoid ceilings (12), ~26 **inherited ERCOT-fitted** bands |
| NYISO | ≥39 | ~35 | import ladders (27), retained "reach" markup, LI 0.45 |
| NEISO | ≥43 | ~33 | ~19 inherited ERCOT bands, ladders (14) |
| CAISO | ≥48 | ~20 | fitted ladder (fallback), 7,500 MW cap, battery adder, solar-deliverability k |

Two genuine mitigants: the three years span very different gas regimes ($2.54/$2.19/$3.52), which
really does constrain the sigmoids; and cross-ISO tuned-curve leakage is formally forbidden —
though MISO/NEISO silently violate it through the generic fallback (C-11).

### 5.2 Residual-chasing is institutionalized machinery, not incidental drift

`scripts/derive_offer_curve_jacobian.py` fits a ridge-regularized map from offer-band deltas to
Δ(class TWh), Δ(LMP MAE), Δ(NRMSE), with a **joint-move solver** proposing multi-knob moves that
minimize backcast error (used on ERCOT and NEISO; log records "predicted twh RMS 0.671→0.649").
Documented residual moves: PJM sigmoid ceiling/floor per-run adjustments; ERCOT lignite curve
back-solved to "land all three years"; the deprecated ORDC offset re-swept; NYISO run-28 markup
retained because removing it cratered C3a; ercot-22 deltas set "halfway between" two prior runs'
values after an LMP collapse; pjm-71 coal floor bisected on the residual.

**Countervailing discipline is real and improving:** the determination rubric is machine-enforced;
multiple keepers were promoted on structure while fit worsened (pjm-75, miso-38, ercot26 "NEUTRAL
on the backcast"); explicit refusals to tune are logged; probes rejected on mechanism grounds
(caiso-48); the project ran its own leakage audits and retired violations. The hygiene is far
better than typical. But the rubric is scored **entirely in-sample** — no train/test split, no
parameter-count penalty, no DOF accounting anywhere in the scoring path.

### 5.3 Out-of-sample discipline: designed, almost entirely unexecuted

- `--statistical-mode` (all answer-injection overlays off) was run **once**, ERCOT only,
  2026-06-16: **fails doubled 5→10, CT collapsed −75/−88 %, CO₂ +8/+9 %**. Never re-run after the
  subsequent rebuilds; never run for the other five ISOs.
- **2022 and H1-2026 are designated untrained holdouts — never scored.**
- `docs/forecast-validation-plan.md` prescribes the right protocol (tune on 2018-22, score 2023-25
  once); none of its phases has produced a number.
- The only executed holdout anywhere is inside the Jacobian fitting (parameter-estimation hygiene,
  not model validation).

### 5.4 Structural gaps that let the CT forcing survive

1. **Annual-volume scoring hides shape errors** — the flat CT floor *helped* C1 while destroying
   the diurnal shape nobody scores.
2. **No forced-energy attribution** — nothing reports how much class energy binding floors supply.
3. **No forecast/backcast parity check** — the CAISO RA floor exists only in the calibration
   script, not `runner.py` (docs/audit-wiring-iso-gaps/prompt-pack/w2-caiso-ra-p2.md).
4. **No DOF ledger** — nothing tracks what a keeper's free parameters are or how many solves chose them.

---

## 6. Verdict

**Legitimate-but-unproven, with one confirmed forcing defect.** The architecture and most inputs
are sound; the governance catches its own violations; coal/offer-curve tuning is within the
owner's sanctioned scope. But (a) the CAISO CT floors force dispatch the market doesn't produce and
must be scrubbed; (b) forecast skill is currently **asserted, not measured** — the only
out-of-sample datapoint that exists is adverse; and (c) without the §7 diagnostics the same class
of feature will be rebuilt under calibration pressure, because the scoring rubric rewards it.

---

## 7. Legitimacy diagnostic suite

Cheap to run against any bundle's `dispatch/<year>_P2.parquet` + bench payloads. Target
implementation: `scripts/legitimacy_diagnostics.py`, with D1–D5 + D-9 wired into keeper promotion.

| ID | Diagnostic | Pass condition | Catches |
|---|---|---|---|
| **D-1** | **Diurnal shape test, per class**: hour-of-day mean profile, model vs CAMPD; correlation + CV ratio for peaker/intermediate classes | CT/peaker: profile r ≥ 0.8 AND model off-peak CV ≥ 0.5 × actual (no flat lines) | The exact caiso-42 signature (model CV 0.000 vs 0.45) |
| **D-2** | **Forced-energy attribution**: TWh dispatched at a binding `min_gen` floor, by class × mechanism (each injector tags its rows) | Dashboard-reported; keeper gate: forced share < 10 % for peaker classes, < 30 % any merchant class | Stacked-floor creep; ~50 % CT forced share fails instantly |
| **D-3** | **Zero-forcing ablation twin**: reference solve with all merchant floors/bridges off (keep nuclear + CHP steam + coal ToP), registered beside every keeper. **Forcing only** — admissible measured overlays (outage windows, F923 fuel, CEMS rates) stay ON; the twin is never an overlay on/off comparison (that is D-7, an input-gap statistic, not a legitimacy diagnostic) | Keeper-vs-ablation delta per class explained by a market story, not a residual story | Quantifies what each floor buys |
| **D-4** | **Off-window binding test**: % of floored MWh outside each floor's driver-justified hours | < 5 % off-window | All-24h day gates on evening mechanisms |
| **D-5** | **Forecast/backcast parity**: diff mechanism sets active in the two modes (excluding declared backcast-only overlays) | Empty diff or on the declared list | The w2-caiso-ra-p2 wiring gap |
| **D-6** | **Score the designated holdouts — under strict quarantine** *(amended 2026-07-04, owner's directive)*: 2022 + H1-2026 are fully quarantined (no solves, no scoring, no data intake) until an ISO's calibration is declared complete (`frontend/data/backcast/calibration-complete.json` marker); then scored EXACTLY ONCE with frozen keeper configs — the holdout data intake happens at that moment as step 1 of the one-shot validation (`docs/out-of-sample-results-2026-07.md` §1) — results recorded whatever they are, no re-touch (a calibration response requires designating a new never-touched holdout); plus leave-2025-out refit (retune on 2023-24, score 2025 frozen) | Held-out degradation < 1.5× in-sample on C2/C3b/C4; CI: no registered bundle carries a solve year outside 2023–2025 pre-marker | Lineage-scale overfitting invisible to in-sample gates |
| **D-7** | **Statistical-mode A/B per ISO**: all overlay/answer-adjacent inputs off, all six current keepers; publish the fail-count gap on the dashboard next to each keeper. *Reframed 2026-07-13:* the gap has two components — the part carried by **admissible measured inputs** (historic outages, F923 fuel) is the irreducible backcast→forecast **input gap** (forecast-uncertainty information, never a backcast caveat); only the part carried by answer-injection floors bears on legitimacy | Gap documented; the answer-injection component shrinking release-over-release | Answer-injection-carried fit; quantifies the forecast input gap (the ERCOT D1 result, measured everywhere) |
| **D-8** | **Frozen-coefficient stability**: refit drag hinges / temp-CF coeffs / offer bands on 2023-24 only, predict 2025 | Coefficients stable within physical uncertainty; sign flips = unidentified | Regression floors absorbing residual |
| **D-9** | **Overlay quarantine CI**: assert every keeper `run_config.json` has `ct_deployment_overlay=False`, `reliability_deployment_overlay=False`, `ct_mustrun_per_plant=False`, `ordc_reliability_deployment_mw=0`, `caiso_gas_commitment_floor=False`; assert non-ERCOT ISOs resolve no ERCOT-fitted offer band via the generic fallback | CI red on violation | Re-arming answer keys; silent cross-ISO leakage |
| **D-10** | **Free-class-only rescore**: re-score C1 with pinned classes (wind/solar under L1, nuclear, hydro, CHP, NYISO imports) excluded | "Free-class" pass rate published per keeper | Pinned-class gate inflation |
| **D-11** | **Knob perturbation Jacobian, published**: ±10 % on each keeper free parameter (the derive script already computes this) | Ranked ∂fit/∂knob per keeper in the bundle; no single knob moves headline metrics beyond its physical uncertainty | Fragile fitted values (the 7,500 MW cap lights up) |
| **D-12** | **DOF ledger in the attestation**: every free parameter, identification source (published / measured-physical / residual), lineage solve count | No residual-sourced parameter in a keeper without an open root-cause issue | Silent parameter accretion |
| **D-13** | **Bench reproducibility CI**: rebuild every `bench/` artifact twice from committed code + `data/raw`, assert byte-identity; static check no bench builder imports dispatch results | CI green | Benchmark-side circularity (the BTM pattern) |
| **D-14** | **Negative-control probes**: corrupt one physical input (wrong gas price, shuffled outages) — the backcast must *worsen* | Insensitivity ⇒ a compensating knob exists | The nyiso-32 compensator pattern |

**Rubric change** (closes §5.4-1/2): add D-1 shape metrics and the D-2 forced-energy share as
first-class C-criteria so a flat floor can never again *improve* a keeper's score.

---

## 8. Protective rules (proposed CLAUDE.md additions)

16. **No floor without a window, a driver, and a forward story.** Every min-gen/commitment floor
    states (a) its external driver, (b) the hours it may bind and why, (c) how it regenerates in a
    forecast year. A floor binding in hours its own driver evidence says the class is offline
    (CT overnight CF ≈ 0) is a bug by definition, whatever it does to the residual.
17. **Commitment physics by parameters, not class names.** Bridge/commit eligibility gates on unit
    physics (`min_down_hours`, startup cost) — never a hard-coded class tuple. Fast-start units
    (min-down ≤ 2 h, startup < $30/MW) are never economically bridged beyond their min-down.
18. **One mechanism per phenomenon.** Before adding a floor/bridge, enumerate what already floors
    the same class (D-2 attribution) and replace or reconcile — never stack a new floor on the
    unexplained residual of an old one.
19. **Forced energy is budgeted.** A keeper fails if any merchant class dispatches > 30 %
    (peakers: > 10 %) of its energy at binding floors. Floors are commitment scaffolding, not the
    dispatch model. *(Peaker cap later raised 10 → 15 %, rubric v2.1 2026-07-06. Amended 2026-07-07
    by the rubric v2.2 grounded-above-budget escalation: a class above its cap is no longer an
    automatic fail — it passes clean if every binding merchant mechanism clears D-4 off-window
    binding AND its D-1 diurnal shape clears the gates, i.e. the forcing is a real windowed driver
    that reproduces the observed dispatch. This promotes D-4 from a reported diagnostic to a
    promotion-gating input for any over-budget class. See CLAUDE.md rule 20 / rubric §1 C8 §9 v2.2.)*
20. **Every keeper carries a DOF ledger and an ablation twin.** The attestation lists each free
    parameter with its identification source; a zero-forcing ablation run is registered alongside.
    A residual that can only be closed by a tuned value is an open root-cause issue, not a parameter.
21. **Hold out data, and score it exactly once.** *(Amended 2026-07-04 to the owner's strict
    quarantine — supersedes the original wording; see D-6.)* The designated holdouts — 2022 and
    H1-2026 — are under **full quarantine: no solves, no scoring, no data intake for those
    years** — until an ISO's calibration is declared complete (the per-ISO marker in
    `frontend/data/backcast/calibration-complete.json`). They are then scored **exactly once**
    with frozen keeper configs; the required holdout data intake (the coverage gap itemized in
    `docs/out-of-sample-results-2026-07.md` §1) happens at that moment, as step 1 of the one-shot
    validation. Results are recorded whatever they are; no calibration change may respond to them
    without designating a new never-touched holdout. Structural mechanism changes are scored
    leave-one-year-out within 2023–2025 before promotion. In-sample improvement with held-out
    degradation is overfitting, not skill. CI-enforced: `legitimacy_diagnostics --keepers` /
    `audit_keepers` fail any registered bundle with a solve year outside 2023–2025 before the
    ISO's calibration-complete marker exists.
22. **Derive scripts are frozen against residuals.** Measured-behaviour parameters (min-stable
    loads, drag hinges, sigmoid anchors, committed shares) re-derive only when their *source data*
    updates — never because a residual moved. Re-derivation commits must cite the data change.
23. **No off-registry tuning channels.** Every tunable that can change a solve appears in
    `ScenarioConfig`/`constants.py` and the run's `run_config.json` — no env-var knobs, no
    hardcoded per-plant dicts in `data/` modules, no `getattr` fallback literals in the offer path.
24. **Tuned curves never cross ISO boundaries.** A multiplier fitted on one ISO's residual is that
    ISO's; generic fallbacks carry neutral (1.0) bands. (Makes the existing informal rule
    CI-enforced; see D-9.)
25. **Deleted means deleted.** Deprecated fitted knobs are removed, not zeroed — a deprecated
    parameter that still parses is a re-armable answer key (the ORDC offset was re-swept *after*
    deprecation).

---

## 9. Prompt pack

`docs/legitimacy-scrub-prompts-2026-07.md` — sequenced scrub + guardrail sessions. S1
(diagnostics + CI) lands first so every subsequent scrub run is scored by the new tests; S2–S4 are
independent parallel branches; S5 (rules + rubric + holdout scoring) closes.

---

## Appendix: evidence provenance

- CT diurnal profiles: decoded from `frontend/data/backcast/runs/2026-07-01-caiso-42-atc-hydro.js`
  / `…caiso-48-solar-decommit.js` (`plants[pid].m`, 8760-byte arrays scaled to `m_ann`) against
  `frontend/data/backcast/bench/CAISO/<year>.json.gz` CAMPD series, CT_PEAKER membership per bench
  plant `group`.
- Forcing-mechanism traces, magic-number sweeps, leakage inventory, registry census: five parallel
  audit passes over `src/market_sim`, `scripts/run_calibration*.py`,
  `results/calibration/*/run_config.json`, all 92 registry JSONs,
  `docs/backcast-measured-data-audit-2026-06.md`, `docs/calibration-log.md` (3,825 lines),
  `docs/calibration-session-log.md`, and the determination rubric — 2026-07-02.
