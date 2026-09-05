# PREREG miso-214 — THE MIDWEST CT_PEAKER FLEET AT ITS OWN DELIVERED COST: phase 0 (zero-solve) splits the missed peaker-hours three ways — the model's price, the market's own out-of-merit conduct, or a model-internal defect — and charters at most ONE single-delta A/B (2026-09-05)

**Pushed BLIND** before any adjudicating statistic and before any arm is designed. Keeper at
open `2026-09-05-miso-213-layering` (bundle `results/calibration/miso213_layering_B`),
NOT-YET on {C3a-2025 −11.747} alone, C3c ledgered 3/3, C6 attested 41/2. Branch
`claude/miso-214-ct-peaker-backcast-de2wpw` (the session's DESIGNATED branch; the charter
text names `claude/miso-214-ct-peaker-conduct` — same lane, the designated name governs)
from `origin/main` `c9f1d26e` (contains miso-213). Rule 22 `[R-HOLDOUT]`: 2023–2025 only —
MISO holds no marker. Rule 25 `[R-ISO-SCOPE]`: MISO's shard only, plus one cell line per
shard IF a new `ScenarioConfig` field is added (rule 28c).

---

## 1. The object, read from the code and from the miso-213 record (not measured here)

miso-213 removed a double-counted regional premium: on this keeper every MISO gas cell is
priced by the EIA-923 print path (own monthly receipt, or the class-aware state/zone pool of
other plants' receipts), and the mean-zero `miso_zonal_gas_basis` increment no longer stacks
on top of it. The per-zone increment that came off (FINDING-miso213 §1, L-1):

| year | West/Plains | Illinois/Indiana/East | South |
|---|---:|---:|---:|
| 2023 | **+0.307** | **−0.260** | +0.143 |
| 2024 | +0.087 | **−0.150** | +0.118 |
| 2025 | **−0.642** | −0.039 | +0.287 |

$/MMBtu, after the capacity-weighted mean. A NEGATIVE entry was a **discount** the zone had
been receiving; removing it RAISES that zone's delivered gas cost. So the repair raised
Illinois/Indiana/East in 2023 and 2024 and raised West/Plains in 2025 — and CT_PEAKER became
the largest C1 mover on the board: **−3.33 / −2.32 / −3.62 TWh** (2023 / 2024 / 2025), now
**11.92 vs 17.04 TWh actual in 2023** (C1 PASS, inside ±8) and **16.10 vs 19.29 in 2025**
(SKIPPED — preliminary EIA-923 vintage).

**Why the peaker class is a NEW question, and not the adjudicated one.** The MISO CT offer
is, on this keeper (`gas_offer_net_revenue_margin=True`, `apply_gas_offer_margin`):

```
mc[g,t] = phys_HR_mult × HR_base × F[g,t]  +  markup_hr[g] × anchor      (anchor = 3.0492 $/MMBtu)
```

— the physical burn tracks delivered fuel, the residual markup is a **fuel-invariant $/MWh
margin**. For the CT econ band `phys_econ_low/high` = 0.687 / 0.691 against an offered 1.0,
so at the published cap-weighted base heat rate 12.0351 the fixed margin is ≈ 3.8 MMBtu/MWh ×
3.0492 ≈ **$11.5/MWh** and the fuel-tracking leg is ≈ 8.3 MMBtu/MWh. A $0.26/MMBtu increment
removal therefore moves the CT econ offer by ≈ **$2.1/MWh** — and that $2.1/MWh moved
3.3 TWh, which says the class sits in a very flat, very dense part of the MISO stack. The
miso-134 / 179 / 180 family adjudicated the offer **LEVEL** (`R`) and **SPREAD** (`I`) on the
whole gas fleet **at the pre-repair cost**, when the Midwest CT fleet was carrying a
−0.26 / −0.15 $/MMBtu discount on the fuel-tracking leg. Rule 14 `[R-ACCURATE]` says the
plant's own receipt is the accurate input and it stays; what has not been asked at the
post-repair cost is whether the class's **own conduct** — when the market starts a peaker,
how long it keeps it on, and at what price — is represented at all. **That question, not the
offer level, is this lane's.**

**What is already in the model for this class** (the rule-19 `[R-ONE-MECH]` census L-4
verifies against the bundle's D-2/D-4 rows; stated here from the code and the keeper's
`run_config.json` BEFORE reading them):

1. `reliability_floor=True`, `reliability_floor_overrides={}` → the MISO CT_PEAKER limbs in
   `RELIABILITY_FLOOR_REGISTRY`: **`netload` driver only, enabled, window h15–21, all six
   carry zones** (`floor_pct` 0.0994–0.2459, threshold 78.52); the `tmax` / `tmin` CT limbs
   are `enabled=False`.
2. `ct_intermediate_split=True` with `ct_intermediate_cf_threshold=50.0` — high-CF CTs are
   reclassified to `CT_INTERMEDIATE` and leave the class.
3. The band construction: `committed` 1.025 (= `phys_committed`, measured), `econ_low` /
   `econ_high` 1.0 vs phys 0.687 / 0.691, `peak` **4.0** vs `phys_peak` 1.0 (the deliberate
   MISO-cap scarcity wall), `econ_low_share` 0.526, `pct_peaking` 7.0; plus
   `ct_committed_hr_mult` 1.28, `ct_econ_hr_mult` 0.97, `ct_peak_hr_penalty` 1.1.
4. `tranche_startup_amortization=True` (+ `tranche_startup_measured_runs`,
   `tranche_startup_conditional_runs`) — the P1 bid-cost startup markup.
5. `measured_ct_heat_rates=True`; `ct_mustrun_floor_frac` / `ct_deployment_floor_frac` 1.0;
   `ct_netload_drag=False`, `ct_deployment_overlay=False`, `miso_commitment_posture=False`.

**There is no commitment bridge of any kind armed for MISO.** The three P1-native bridges in
the repo are CAISO's RA must-offer, ERCOT's `ercot_gas_commitment_bridge` and NYISO's
`nyiso_gas_commitment_bridge`; each gates on its own ISO. MISO CT_PEAKER is therefore a pure
hour-by-hour economic dispatch decision outside h15–21, with no min-run, no min-down and no
start commitment of its own.

## 2. Instrument, and its limits — stated in advance

Probe `scripts/probes/_miso214_ct_peaker_conduct_phase0.py` →
`results/calibration/_miso214_ct_peaker_conduct.json`. **Zero solve.** Readers reused from
`_miso213_basis_layering_phase0.py` / `_miso211_rdt_binding_state.py` /
`_miso134_ct_night_order_screen.py` with `_miso134.BUNDLE`, `m207.KEEPER` and `m208.KEEPER`
re-pointed to `results/calibration/miso213_layering_B` before any helper runs;
`campd.load_campd_hourly` for measured conduct; `_miso211` hour sets and regional series.

* **CONTROL leg = `results/calibration/miso210_clock_B`** (the pre-repair keeper), whose
  `hourly/class_band_hourly_*` + `class_hourly_*` + `system_*` are committed. **ARM leg =
  the keeper `miso213_layering_B`**, same sidecars plus `network_*`. The class×band×hour
  delta between them IS the 3.3 / 2.3 / 3.6 TWh, measured from LP output, not reconstructed.
* **NEITHER bundle carries `unit_hourly/` or `dispatch/`** (gitignored, 79 MB/yr). So
  `class_band_hourly` has **no zone dimension** and there is **no plant-grain model dispatch**
  in the record. Plant-grain and zone-grain model merit is therefore a **PRICE-TAKING STATIC
  SCREEN** — the miso-134 S-2 / miso-213 L-3 instrument — on the HEAD fleet chain
  (`build_year` under the keeper's own recorded `ScenarioConfig`) against the keeper's own
  committed P1 zone prices, on `mc_base` (**no P1 startup adder**). It is a BOUND, not the
  LP: it ignores simultaneity, the energy balance and the reserve co-optimization. Every
  screen number is reported beside the corresponding committed class total so the reader can
  see how far the bound sits from the LP.
* **MISO's masked energy-offer corpus cannot carry this question.** `data/raw/miso-energy-
  offers` is identity-masked with **no fuel or technology attribute**, its offer-side class
  bridge was built and **REFUTED at miso-138**, and its payload is gitignored and ABSENT in
  this container (README only). No offer-side CT statistic is available for MISO at any
  price — this is a property of the data, not a choice made here.
* **CAMPD is the only measured class-grain conduct instrument.** The facility-level extracts
  are missing for 12 of the 14 MISO states in this container; the **unit-level** extracts are
  complete for 2023–2025, so every CAMPD read uses `prefer_unit_level=True`. CAMPD reports
  **GROSS** MW against the model's **NET** tranches; the wedge is small for simple-cycle CTs
  (~1 %) and is **reported, never adjusted**. CEMS exempts small units, so the model's
  CT_PEAKER fleet is only partly CEMS-visible — the covered capacity share is an N-1 footing
  statistic and a kill (§4 K-e).
* **The plant's own cost is a MONTHLY average applied to an HOURLY decision.** The
  average-vs-marginal delivered-cost convention (miso-212 §8) is **OWNER-COURT and is not
  touched**; it is a known upward bias on any "out-of-merit" reading in a month whose
  intra-month spot varied, and it is disclosed beside the §3 P-2 split rather than corrected.

## 3. Predictions — each with its mechanism, scored against interest in the finding

* **P-1 — where the 3.6 TWh went (L-1).**
  * **(a) Band.** ≥ 70 % of each year's class ΔTWh (arm − control) lands in the **econ**
    band family (`econ*`), not `committed` / `peak` / `mustrun` (0.70). *Mechanism:* the
    econ band is the only CT band whose offer sits within ~$2/MWh of the clearing price —
    `committed` is scaffolded, `peak` sits at 4.0× base HR and is out of merit outside
    scarcity, and a floored hour cannot lose energy at all.
  * **(b) Zone, year-specific and sign-derived from the table in §1** (via the static
    screen, since `class_band_hourly` carries no zone): 2023 ≥ 60 % of the CT loss in
    **Illinois + Indiana + East**; 2024 ≥ 50 % in **Illinois + Indiana + East**; 2025 ≥ 50 %
    in **West + Plains** (0.60). *Mechanism:* the loss must follow the zones whose increment
    was NEGATIVE (a discount removed ⇒ cost up), and that is IIE in 2023/2024 and W/P in
    2025. A uniform or South-led loss falsifies the mechanism outright.
  * **(c) Diurnal.** ≥ 60 % of the lost MWh falls **outside h15–21** (0.65). *Mechanism:*
    inside h15–21 the enabled `netload` reliability-floor limb holds the class up in the
    hours it binds, so energy cannot be lost there; outside it the econ band is free.
* **P-2 — THE DISCRIMINATOR (L-2), and the pre-registered decision statistic.** Take every
  **missed plant-hour**: a model CT_PEAKER plant that CAMPD shows running (gross > 0) in an
  hour the static screen has out of merit at the keeper's own P1 zone price. Split it, MWh-
  weighted, on the plant's **own** cost — its own EIA-923 monthly delivered print × its own
  CAMPD-measured burn heat rate in those hours + the model's VOM — against **two** prices,
  the keeper's P1 zone price and the **measured** MISO zonal LMP
  (`_validation-source/actual_lmp_hourly_zonal_MISO.parquet`):
  * **A — price-reachable:** own cost ≤ ACTUAL price **and** own cost > MODEL price. *The
    market's price is above the plant's cost and the model's is not — the C3a object.*
  * **B — out-of-merit in the market itself:** own cost > ACTUAL price. *The market ran the
    peaker at a loss on its own delivered energy cost — a conduct / commitment / reserve /
    local-reliability object.*
  * **C — model-internal:** own cost ≤ MODEL price and the model is still idle. *The LP had
    a cheaper option, or the unit was unavailable — an availability or mechanism defect.*
  **Prediction: A 45–65 %, B 20–40 %, C 5–20 %, ordered A > B > C, in ≥ 2 of 3 years
  (0.50).** *Mechanism:* MISO's real CT run-hours are concentrated in the top decile of net
  load where actual RT prices clear far above a $35–40/MWh peaker cost, and the keeper's P1
  price is 11.75 % low on the 2025 mean and further low in the tail — so most missed hours
  should be reachable-but-unreached. B is real but a minority: starts, min-run tails,
  reserve duty and local reliability do put peakers on below their own cost, and MISO's
  own market design (ELMP fast-start pricing, VLR commitments in the South) names those
  reasons.
* **P-3 — the 2023 question (L-3).** The 2023 CT under-dispatch is **all-hours, not a
  summer tail**: the Jun–Aug share of the 2023 CAMPD-minus-model CT_PEAKER MWh gap is
  **≤ 55 %** (0.60), against 25 % of hours; a tail phenomenon would be ≥ 70 %. *Mechanism:*
  2023's C3a is **+0.91 %** — the model's mean price is ABOVE actual on the year — so the
  "prices the model does not reach" story is least available in 2023 of the three years. If
  the 2023 gap is nonetheless summer-concentrated, the tail story survives even in the year
  whose mean price is too high, and that is a stronger claim for the C3a object than
  anything 2025 can supply.
* **P-4 — the rule-19 census (L-4).** The mechanisms touching MISO CT_PEAKER are exactly the
  five listed in §1, no more (0.75); the **only** D-2 attribution row for CT_PEAKER is the
  **reliability floor** (0.70); and the class's **C8 forced share is ≤ 0.15 in every year**,
  i.e. inside the peaker budget (0.70). *Mechanism:* the only floor armed for the class is
  the h15–21 netload limb, which spans 7/24 of hours at floor_pct ≤ 0.246.
* **P-5 — the meta prediction, stated so the finding can score it.** **P(an A/B is
  chartered) = 0.35.** I expect P-2 to return A > B, i.e. the object to be the C3a-2025 tail
  the owner already holds — in which case this lane writes the finding, mints nothing and
  stops (§4 K-a). If B does clear its bar, I expect the honest identified input to be a
  **commitment** object and not an offer one: a CAMPD-measured min-run / min-load conduct
  for the MISO CT fleet, built by the WP-3 loading-when-on construction that
  `scripts/data/derive_campd_gas_commitment_params.py` already runs for NYISO (the ISO that,
  like MISO, publishes no unmasked LSL/HSL). That would be a NEW `ScenarioConfig` field and
  would need a matrix base row + a cell line in all six shards (rule 28c).

## 4. Decision rules — the kills, written before the numbers

Charter an A/B **only if ALL** of the following hold; otherwise write
`FINDING-miso214-…md`, update the matrix, **mint nothing and stop**.

* **K-a (the discriminator).** B ≥ **40 %** of missed CT plant-hours, MWh-weighted, in ≥ 2
  of 3 years. If B < 40 % in ≥ 2 years the object is the model's **price** — the C3a-2025
  tail, whose live items are OWNER-COURT (the D-2 5(i) seam-response ruling; the
  average-vs-marginal convention, miso-212 §8) — and this lane stops.
* **K-b (the offer-level trap).** Re-run the model-side merit test with the CT econ band's
  residual margin removed (`markup_hr × anchor` → 0, i.e. the miso-134 full measured swap).
  If ≥ **60 %** of bucket **A** flips to in-merit-in-model, the missed energy is the offer
  **LEVEL**, adjudicated **R** at miso-134/179 — DO-NOT-REDO — and this lane stops
  regardless of B.
* **K-c (rule 19 `[R-ONE-MECH]`).** If L-4 shows an armed mechanism already represents the
  driver B identifies, reconcile or replace — never stack. Nothing is chartered unless the
  reconciliation itself is the single delta.
* **K-d (rule 13 `[R-MEASURED]`).** The identified input must be a reproducible physical /
  market quantity that regenerates for a forward year from forward drivers and responds to
  changed conditions. A fitted markup, a load proxy, a share tuned to the CT residual, or
  anything whose value is read off this session's gap is **forbidden** and is an automatic
  stop.
* **K-e (instrument footing).** If CEMS-covered capacity is < 60 % of the model's CT_PEAKER
  fleet in any year, the instrument cannot carry the class: report the coverage and stop.

If an A/B **is** chartered: ONE `ScenarioConfig` field (rule 24), matrix base row + six
cells (rule 28c) with `scripts/check_mechanism_matrix.py` green, unit tests pinning the
flag-off byte identity, replay via
`scripts/replay_keeper.py results/calibration/miso213_layering_B --set <field>=true
--out-dir results/calibration/miso214_<name>_B`, years 2023 2024 2025 **sequential in one
invocation** (rule 12); CONTROL is the keeper bundle itself (S-0 inherited, not re-solved).
Scorer on the `_miso213_ab_gates.py` pattern, committed **before** the solve: S-0 inherited,
S-1 restated over the RECORDED configs (fields new on `main` since the keeper solved must sit
at default), K-1..K-6, the pre-registered object gates (CT_PEAKER C1 face by year; the 2025
real S→N binding-hour South gas / corridor flow / Indiana−South spread; C8), attestation via
`gen_miso214_attestation.py` on the miso-213 template. Promote only if structurally faithful
AND no protective gate regresses. **C3a is reported at full magnitude and is never the
justification.**

## 5. Reported against interest, in advance

1. **The static screen is a price-taking bound.** It will over-state how much CT capacity
   "should" have run, because it prices every tranche against a fixed zone price with no
   energy balance. Bucket sizes are shares of a population the bound defines; the class
   totals from the screen are reported beside the LP's own committed totals precisely so a
   reader can discount them.
2. **Bucket B is a residual category.** "Out-of-merit on the actual price" is consistent
   with reserve duty, local-reliability / VLR commitment, a start's min-run tail, a
   self-schedule, a bilateral or hedge obligation — and also with plain measurement error
   from applying a MONTHLY 923 average to an HOURLY decision. A large B is **necessary but
   not sufficient** to charter; K-d still has to be satisfied by a specific measured input.
3. **The asymmetry between the two headline years is disclosed now.** 2023 carries the
   larger absolute gap (5.1 TWh) and is the year whose C1 face **PASSES** and whose mean
   price is too HIGH; 2025's face is **SKIPPED** on a preliminary 923 vintage. A story that
   only works in 2025 is a story about the year the actuals are weakest.
4. **P-5 says I expect to charter nothing.** That is the prediction most at risk of being
   overturned by motivated reasoning in the other direction — a lane that finds nothing can
   feel like a wasted session. K-a is a number, fixed here, and the finding reports it
   whichever side of 40 % it lands on.
5. **CT_PEAKER moved AWAY from actual under miso-213 and stays there.** Rule 14 keeps the
   accurate fuel input. Nothing in this lane may be justified by moving the C1 face back.

## 6. Governance

Rule 15 `[R-DASHBOARD]`: any solve this lane produces is registered the same session; a
zero-solve phase 0 registers nothing but publishes its JSON and the finding. Rule 22: 2023–
2025 only. Rule 25: `docs/codebase-site/data/mechanism-matrix/MISO.js` only (plus one cell
line per shard if and only if a field is added). Rule 27 `[R-PUSH]`: `src/` edited locally,
blob-verified after every push, no full-file rewrites. Rule 13: CAMPD hourly conduct, the
EIA-923 prints and the measured zonal LMP are read here as **diagnostics**; no measured
outcome may be fed back as an input. Rule 12: any solve runs its years sequentially in one
invocation. DO-NOT-REDO: `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
`miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
`miso_south_gas_delivered_cost_basis` (R), `zonal_gas_basis` (K, scoped by miso-213).
OWNER-COURT, not armed here: the average-vs-marginal delivered-cost convention (miso-212 §8)
and the D-2 5(i) seam-response object. STILL OPEN, not this lane's lever: the South PRICE
separation (miso-213 O-4, +$0.16 vs +$58 measured — the miso-211 D-3 object).

Next shorthand: **miso-215**.
