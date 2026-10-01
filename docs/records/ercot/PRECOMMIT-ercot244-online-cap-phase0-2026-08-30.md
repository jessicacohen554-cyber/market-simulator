# PRECOMMIT — ercot-244 Phase-0 (2026-08-30): the rtolhsl-based energy-side online-capability ceiling — zero-solve identification on the FORWARD keeper's committed sidecars, chartered, constructed and kill-gated BEFORE any measurement

**Owner authorization: the ercot-244 session handoff (2026-08-30) IS the owner
charter the §5.1 item-9 queue card requires.** It charters a Phase-0 zero-solve
identification of an energy-side measured online-capability ceiling
(`energy_online_capability_cap`, the ERCOT-155 named successor) identified from
`rtolhsl`, and licenses ONE forward-span A/B (Phase-1, its own separate
precommit) ONLY if this Phase-0 passes its own declared kills. This document is
pushed and blob-verified before any measurement runs. Branch
`claude/ercot-244-online-cap-xi7kvo`.

## 0. Cell status, the ercot-159 rejection, and the re-open basis (stated first because it is the governance load-bearing point)

**The matrix cell is `R`, not `U`.** The charter quotes the card's original
text ("UNCHARTERED — needs owner authorization and its own precommit", matrix
§5.1 item 9), but the card carries the appended adjudication: **CHARTERED,
EXECUTED AND REJECTED AT ERCOT-159 (2026-08-04, owner-authorized; cell
`U → R`)**, and `docs/codebase-site/data/mechanism-matrix/ERCOT.js` reads
`cell: "R"` today. This precommit does not pretend otherwise. The lane
proceeds under `[R-MECH-MATRIX]` duty (a)'s own escape clause — "never re-test
a cell already adjudicated R/I/G **without new evidence**" — on four pieces of
new evidence, each post-dating the R:

1. **The forward span has never been tested by any energy-side ceiling.** The
   ercot-159 artifact carried a 2023 block only (full-year SCED corpus
   coverage); its 2024/2025 years were **byte-inert by construction** and
   measured bit-identical A→B. Every kill that fired — C3a −24.5 % → +44.7 %,
   +39 spurious mid-band, NRMSE 2.866 → 6.584, 33 fabricated tail hours —
   fired **in 2023, on the ercot158-era keeper** (C3a-2023 basis −24.5 %).
   The R adjudicates that arm on that year on that model.
2. **The object moved.** Under the two-config keeper (owner ruling 2026-08-26,
   `docs/FINDING-ercot-two-config-keeper-2026-08-26.md`) the 2023 year — the
   ercot-159 arm's entire live surface — is covered by the CALIBRATED
   zero-caveat carve-out (`2026-08-25-236-swcap-clip-k33`) and is NOT this
   lane's object. The object is the FORWARD keeper's lone blemish: the
   ledgered C3c ×2 (2024 22/53 = 0.42×, 2025 1/31 = 0.03×).
3. **New adjudicated evidence points at commitment state.** ercot-241
   (2026-08-30, zero-solve) measured the λ-band tight-room dependence as
   **position/participation-carried, not within-resource repricing** (paired
   Δ at 0.9×HSL = +$0.20 CC / +$0.52 CT); ercot-242 (2026-08-30) then refuted
   the room-conditioned OFFER surface as-armed and recorded the residue:
   "any further repair direction for these hours points at the POPULATIONS
   that carry their λ-band (… participation/commitment state), not at CC/CT
   offer re-pricing." The commitment-state axis is the adjudicated repair
   direction; the offer-arm alternative is refused on the card.
4. **A different instrument.** The rejected construction was the 2023-only
   SCED-derived conditional envelope (season × hour-block × 14 net-load bins,
   per-cell MAX). This lane identifies from the **hourly measured `rtolhsl`
   series** (NP6-905-CD settled telemetry, committed for all three years in
   `data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`), against the
   CURRENT forward keeper's committed sidecars.

**The ercot-159 DO-NOT-REDO is honoured, not waived:** the SCED conditional
envelope construction is not re-run, and no envelope re-grain against the 2023
residuals occurs (nothing here reads the 2023 residual at all except as
report-only side context). Its postmortem finding — "the next object is the
commitment level in ordinary hours, not the cap"; ordinary-hour binds are NOT
benignly absorbed (the CT-buffer hypothesis is REFUTED, 523 ordinary binds
cascaded to reserve shortage/VOLL) — is built into this lane's kills: K-C
below kills the lane on exactly that signature, measured zero-solve on the
current keeper before any LP exists.

**DO-NOT-REDO fence (this lane touches none of these):** release-guard exit
condition (KILLED-AT-CENSUS, ercot-243); room-axis offer surface (R,
ercot-242); graded static peak_ladder (R, ercot-239 r2 FINAL); ercot-219
option-b (R); storage RT offer surface (R, Door A); topology splits (G);
cross-year seed (R); adaptive fixed point (measured inert, ercot-230);
seasonal end-of-season term (ercot-232); ORDC/adder channel closures;
ercot-178/-180 grains (R); lowcurve/negative-offer variants; the demand-gap
object (CLOSED, ercot-240: DC-tie identity). The ercot-239/240/241/242/243
measurements are read from their committed JSONs, never re-run. The 2024/2025
all-resource SCED conduct corpus intake stays UNCHARTERED (owner-visible flag
only, §8; SCED-CT is re-fetch-only and CT-only and is not fetched here).

## 1. Object and basis

* **Object:** the forward span's missed-event tail. Official C3c basis
  (`ercot226_official_score.py` / `render_calibration_html._tail_hours`,
  reproduced verbatim, never re-derived): model tail = hours whose MAX ZONAL
  system-sidecar `price` > $200; actual tail = hours with actual RT > $200
  (`actual_lmp_hourly_ERCOT.parquet` `rt`; registered counts 53 (2024) and
  31 (2025), cross-checked at V-0). **Missed set
  `M_y = {h : actual_rt > 200 ∧ model_maxzonal ≤ 200}`.**
* **Basis bundle:** the committed FORWARD keeper
  `results/calibration/ercot234_eastex_identity`
  (`2026-08-25-234-eastex-identity`, span verdict CALIBRATED on {2024, 2025}:
  C3a −0.2 % / −7.9 %, C3b 0.131 / 0.101, C3c the lone ledgered caveat).
  Its committed hourly sidecars (`hourly/{system,class_hourly,reserve_family,
  storage}_<year>.parquet`) are the model side; no solve, no replay.
* **Scored years {2024, 2025}.** 2023 is REPORT-ONLY (census run on the same
  bundle's 2023 sidecars for completeness; the year is the carve-out's, its
  designated config is not this bundle, and no gate reads it).
* **Prep is unrestricted, spend is gated** (rule 22, SPEND-ONLY): hydration
  (`scripts/hydrate_data.py --profile ercot`) and the pinned-env venv are
  prep; every read is years ⊂ {2023, 2024, 2025}; no `--holdout-authorized`
  anywhere; the freeze stays untouched.

## 2. The construction (fixed a priori; grading never re-selects it)

**The ceiling, per hour t of the year's fixed-CST 8760 clock:**

    CAP(t) = rtolhsl(t) − Σ_nonthermal EIA930_netgen(t)

* `rtolhsl(t)`: Real-Time On-Line HSL, hourly mean, from the committed
  `ercot_<year>_ordc_reserves_hourly.parquet` (NP6-905-CD settled telemetry,
  CPT→CST curated, the same file/clock the armed reserve supply cap reads).
* `Σ_nonthermal`: the sum over every `NG: *` fuel column present in the
  committed EIA-930 wide extract (`data/raw/eia-930-hourly/ERCO
  hourly.parquet`, mapped to the local 8760 by the ercot-243 convention,
  reused verbatim) **EXCEPT** `NG: NG` (gas), `NG: COL` (coal) and `NG: NUC`
  (nuclear). I.e. wind, solar, hydro, other, battery (as present) are
  subtracted at their measured net generation; gas, coal and nuclear are not.
  NaN → 0. Negative values (battery charge) enter as-is.
* NaN `rtolhsl` hours (the 2025 RTC+B tail after 2025-12-05) are UNCAPPED and
  excluded from every census count — the same seam as the armed reserve cap.

**The model-side fast-tier point, per hour (the ercot-159 census formula,
reused verbatim on this bundle):**

    F(t) = Σ P_slow(t) + Σ held_fast(t)

* `P_slow`: `class_hourly` `mw` summed over klass ∈ {CC_REGULAR, CC_CHP,
  ST_GAS, ST_CHP, COAL_PRB, COAL_LIGNITE, NUCLEAR} (the nuclear klass string
  resolved case-insensitively at probe start; the probe asserts exactly 7
  classes resolve, else stops).
* `held_fast`: `reserve_family` `held_mw` summed over families
  {RegUp_withheld, RRS_withheld, ECRS_withheld} (asserted present).

**"Binds" (zero-solve counterfactual):** `F(t) > CAP(t)`; depth
`d(t) = F(t) − CAP(t)`.

**Why this construction, stated before any number exists:**

1. **It is deliberately LOOSE-side everywhere it approximates.** `rtolhsl` is
   total-fleet online HSL; subtracting measured non-thermal net GENERATION
   (not HSL) leaves inside CAP: renewable curtailment headroom, idle online
   storage discharge capability, hydro headroom, and the ENTIRE online
   quick-start HSL (base points + headroom — a superset of the quick online
   headroom the ercot-159 construction deliberately credited). Every
   approximation error loosens the ceiling. A loose ceiling errs toward
   inertness (K-B), never toward the ercot-159 over-fire — the failure mode
   that killed the predecessor is the one this construction is biased away
   from by design.
2. **No credit terms, because the keeper already owns that arithmetic.** The
   armed `ercot_load_resource_reserve` / `ercot_storage_as_product_credit` /
   `ercot_reserve_supply_cap_net_credits` machinery already removes the
   LR-RRS-UFR and battery-AS-award MW from what the model's thermal fleet
   must hold, so the sidecar's `held_mw` is the thermal-side holding on both
   sides of the comparison. Adding the measured credit series to CAP on top
   would double-loosen and double-own (rule 19). A credit-augmented variant
   is computed as DISCLOSED DIAGNOSTIC D-V1 only.
3. **Zero fitted scalars** (rule 23 `[R-DOF]` / rule 24): every term is a
   committed measured series used whole; there is no coefficient, margin,
   trim, grain or bin anywhere in the construction. The subtraction set is
   declared by complement (everything non-thermal-non-nuclear present in the
   extract), so no column choice is available to fit.

## 3. `[R-FLOOR-WINDOW]` triple and `[R-MEASURED]` admissibility

* **(a) Driver:** ERCOT's real commitment/online state. Only online resources
  convert capability to energy within the operating hour; slow-start offline
  capability (min-down ≥ 4 h, startup ≥ $35/MW — unit physics, rule 18) is
  physically unreachable within SCED's horizon. The measured driver series is
  settled operator telemetry (RTOLHSL), not a price and not a dispatch
  outcome.
* **(b) Binding window and why:** tight hours — high net load, the evening
  ramp (hod 17–21) and event afternoons — where the real online cushion was
  0.92–2.80 GW against the model's 15.3–17.5 GW (the card's measurement). In
  ordinary hours the committed level should sit well below this loose
  ceiling, so the cap should be slack. **The census IS the window
  verification:** material binding in ordinary hours (actual < $150) is the
  off-window signature (the D-4 analogue for an upper bound) and is kill K-C
  — a mechanism binding where its own driver evidence says the constraint
  was slack is a bug by definition, whatever it does to any residual.
* **(c) Forward story (rule 13's regeneration test):** in a forecast year the
  online state regenerates from forward drivers, on the exact staged pattern
  of the armed reserve-side incumbent: `ercot_rtolcap_supply_cap_mw` armed
  the measured series backcast-only first (G1), then grew the forward
  formula (`ercot_rtolcap_forward_supply_cap_mw`: deliverability share ×
  availability-derated tier MW, keyed on season × net-load bin — every input
  regenerates and responds to fleet/load change). The identical derivation
  applies to an online-HSL share, and the model's own commitment layer
  (P0-detected run patterns + the physics-gated bridges) is the structural
  generator of online state forward. At Phase-1 the mechanism is
  backcast-mode-only (forecast → `None`, uncapped — the G4 seam; matrix row
  stays mode `B`), exactly like CAMPD outage windows: a measured physical
  availability state, admissible as a backcast input because the same
  quantity is producible for a forward year from forward drivers and would
  respond to changed conditions.
* **The ERCOT-89 §6 "never the raw hour series" bright line is consciously
  superseded FOR THIS INSTRUMENT by the owner charter,** recorded here, not
  silently: the charter names `rtolhsl` — an hourly measured series — as the
  identification basis and demands this regeneration story. Two things
  distinguish this from the "raw per-hour telemetered ceiling" the ercot-159
  Phase-0 measured broken (3,838 binding hours): (i) that form was the
  attained slow-fleet capability pin in the SCED taxonomy — a tight hour-pin
  of the day's realized commitment answer; CAP(t) here is a loose aggregate
  envelope (§2.1) that leaves the within-hour commitment choice free below a
  physically-online total; (ii) the program's live jurisprudence already
  arms raw hourly measured operational-state series on this exact file (the
  reserve supply cap, keeper-armed) — the bright line has not governed the
  reserve side since G1, and the charter extends that admissibility posture
  to the energy side with the forward story stated. Whether the loose hourly
  form is also MECHANICALLY sound on the current keeper is precisely what
  the census measures; if it reproduces the raw-form bind census, K-C kills
  the lane and the record reaffirms ercot-159 rather than litigating it.

## 4. Rule-19 `[R-ONE-MECH]` reconciliation (enumerated before any seam is written; precedence explicit, nothing stacked)

* **The DAM availability lane** (`ercot_thermal_dam_availability*`, armed)
  owns OUTAGES: per-unit derates on generator bounds. This ceiling owns
  ONLINE STATE. Both installed, the physically tighter binds; the ceiling
  never tightens because of an outage (it is measured attained-online
  telemetry) and the availability lane never loosens because of the ceiling.
* **The commitment bridges** (`ercot_gas_commitment_bridge`, armed) own the
  LOWER bound (min-gen floors detected from P0). The ceiling is the
  upper-bound counterpart at the same P0→P1 seam; at Phase-1, P0 solves WITH
  the cap so the bridge detects capability-consistent run patterns —
  composition through the existing seam, never a stacked floor. Floors sit
  far below the ceiling by construction (floor ≈ 0.574 × committed-CC ≤
  attained dispatch ≤ online capability); VOLL slack remains the LP's escape
  and is guarded at Phase-1.
* **The reserve supply cap** (`ercot_reserve_supply_cap` +
  `_net_credits`, armed) owns the RESERVE side: Σ R ≤ measured
  RTOLCAP-based tier rows, credit-netted. This ceiling bounds the fast
  tier's TOTAL capability use (P + R). Physically nested, not stacked
  (procured AS ≤ online responsive capability; output + headroom ≤ online
  HSL): on the reserve-only margin the RTOLCAP cap binds; on the
  energy+reserve margin this ceiling does. Neither is derived from the
  other. The credit series stay owned by the reserve machinery (§2.2).
  **D-V3 reports the nesting arithmetic at the binding hours so an
  "already-owned upper bound" verdict (kill K-B's second face) is measured,
  not asserted.**
* **The fast-start pool** (`ercot_faststart_pool_offer`, armed) owns the
  offline-QUICK price route; this ceiling closes the phantom slow-online
  QUANTITY route. Quick-start energy is never capped (row-0 eligibility
  excludes quick classes; the real market reaches its offline quicks within
  the hour and so must the model).
* **The RT offer wall** (`ercot_offer_surface_cleared_share_rt`, armed,
  mode=replace) owns the PRICE of the online spare ladder; this ceiling owns
  the QUANTITY of slow capability reachable. Not stacked — and this is the
  ercot-241/242 adjudication made structural: position/participation is the
  carrier, so the repair moves the model's reachable POSITION honestly
  (a quantity bound) instead of re-pricing curves (the refused arm).
* **ECRS conservative deployment, the adaptive expectation, the ORDC total
  family:** untouched; interactions flow through the LP's own arithmetic
  (the ERCOT-155 prediction that a capped cushion lets the armed 1–3 GW
  withdrawals finally move duals is an expected consequence, not a new
  coupling). The all tier keeps its uncapped sentinel (NonSpin escape valve
  — the ercot41/43 arithmetic cannot recur; unchanged from ercot-159 §0.2).
* **Mutual exclusivity carried over at Phase-1:** one writer of
  `ReserveDesign.online_capacity_cap` — hard error with every
  `online_capacity_envelope` variant, with `ercot_ordc_only_scarcity`, and
  with `ercot_energy_online_capability_cap` (the retired condbinned gate,
  which stays merged default-off as the ercot-159 record; the rule-26
  disposal question remains the owner's).

## 5. The census (every quantity below is committed to the probe JSON; nothing else is measured)

Probe `scripts/probes/ercot244_online_cap_phase0.py` →
`results/calibration/ercot244_online_cap_phase0.json`. Per year (2024, 2025
scored; 2023 report-only):

* **V-0 anchors (measured first; any failure = STOP-AND-INVESTIGATE, no
  census is graded):** (a) model max-zonal > $200 counts reproduce the
  registered 22 (2024) / 1 (2025) exactly; (b) actual rt > $200 counts
  reproduce 53 / 31 exactly; (c) the EIA-930 lag-0 demand alignment assert
  (finite rows, the ercot-243 convention); (d) SOFT check: `rtolhsl`
  hod-17–21 means within ±3 GW of the card's 58.87 / 62.64 / 67.81 GW
  (2023/24/25) — a larger gap is a series-identity question and stops the
  lane, since the card's evening convention is not published.
* **Population prior:** |M_2024| expected ≈ 31–41, |M_2025| ≈ 30 (from
  22/53 and 1/31 with unknown overlap); either outside [15, 80] is an
  anchor breach (stop-and-investigate, not a kill).
* **Census rows:** |B|, |B∩M|, |B∩H| (hit tail), |B∩ordinary|
  (actual < $150), |B∩buffer| ($150–200), away-binds
  |{t ∈ B : model_dw(t) ≥ actual(t)}| (model_dw = demand-weighted system
  price — direction is graded system-to-system, never max-zonal-to-system),
  NaN-cap hour count; depth p50/p90 over B∩M and over B∩ordinary; the
  per-hour records for every t ∈ B∩(M∪H).
* **Disclosed diagnostics (report-only; none is armable without a new owner
  precommit; no grading reads them):** D-V1 credit-augmented CAP
  (+ measured LR RRS-UFR + storage DAM AS awards); D-V2 CAP without the
  OTH/WAT subtraction; D-V3 the reserve-cap nesting arithmetic at B hours
  (credit-netted rtolcap vs held_fast — how far the armed reserve cap is
  from owning the same margin); D-V4 the 2023 census on this bundle's own
  2023 sidecars.
* **Size priors (report-graded, not kills):** at B∩M, expect depth p50 of
  order 1–4 GW (the phantom cushion in use); expect |B∩M|/|M| well above
  the K-B floor in 2024 (the 22/53 year, where the tail exists but is
  under-populated) and unknown in 2025 (the 1/31 year may sit beyond any
  quantity bound — that is what K-B's either-year form allows).

## 6. Kills (declared ex ante; graded on the scored years only; ANY kill ⇒ record and STOP — no Phase-1, no solve, the A/B license is never spent)

* **K-A — construction invalidity.** In either scored year: (i) CAP ≤ 0 in
  more than 24 non-NaN hours; or (ii) `P_slow` ALONE (no reserves) exceeds
  CAP in more than 8 % of non-NaN hours. Rationale: the model's slow
  dispatch tracks reality's slow generation at C1/C2-passing years, and
  reality's slow generation respects its own online HSL with room to spare
  under a loose-side ceiling — mass violation by dispatch alone means the
  subtraction stack is mis-scoped (a series-identity/coverage defect), not
  that the model over-commits.
* **K-B — no reach / already owned.** |B∩M_y| / |M_y| < 0.20 in BOTH scored
  years. The ceiling cannot address even a fifth of the object anywhere —
  inert-shaped, whether because the loose construction never engages or
  because the armed reserve-side caps already own the margin (D-V3 says
  which; both are the same verdict for this lane).
* **K-C — off-window binding / away-from-actual (the ercot-159 over-fire
  signature, killed zero-solve).** In EITHER scored year: (i)
  |B∩ordinary| > 150; or (ii) |B∩ordinary| > |B∩M| (worse than 1:1
  discrimination against the object); or (iii) away-binds > |B| / 3. The
  predecessor bound 523 ordinary hours and every one of its kill gates
  fired in-solve; a construction that re-creates that shape on the current
  keeper is dead before the LP, which is this Phase-0's entire purpose.
* Kills are direction-blind and the thresholds above are frozen: no
  post-hoc re-selection, re-scoping, re-binning or year-scoping to dodge a
  fired kill (rule 20; the year-agnostic arm is the only arm Phase-1 may
  build). A fired kill is recorded at full magnitude in the FINDING, the
  matrix cell keeps `R` with an appended evidence note (the ercot-243
  note-append precedent — no verdict move without a tested mechanism), and
  the calibration-log entry lands either way.

## 7. Decision rule and deliverables

* **All kills clear ⇒ Phase-1 opens** under the charter's own terms and ONLY
  those: a SEPARATE pushed + blob-verified precommit BEFORE any solve or
  derive; the mechanism as a registered default-off ScenarioConfig field
  (working name `ercot_energy_online_cap_rtolhsl`; final name and matrix row
  def amendment per `[R-MECH-MATRIX]` duty (c) in the Phase-1 precommit)
  filling the EXISTING fast-tier `online_capacity_cap` row with §2's CAP —
  identification from measured online state only, zero fitted-to-residual
  content; ONE forward-span A/B — control = replay of the committed forward
  keeper (`replay_keeper.py results/calibration/ercot234_eastex_identity`),
  arm = the single delta; solve 2023 2024 2025 SEQUENTIALLY on the keeper's
  recorded env (highspy 1.15.1 / pandas 3.0.5 / pyarrow 25.0.1 + openpyxl +
  tzdata, venv outside the project dir — the ercot-213 `.venv` trap); score
  `--years 2024 2025` (span-restricted, the two-config discipline), 2023
  side-effect-reported. Phase-1 kills, declared now and frozen: C3a/C3b
  2024 AND 2025 retained PASS; C3c no-worsen per year and the target-year
  counts must IMPROVE toward 53/31 (else inert-recorded); ZERO new shed
  hours; lidless spur no-increase (either year); off-season intact; coal
  ≤ +0.5 TWh; CT/ST within ±1.0 TWh; G-BAT (the 2025 EIA-930 `NG: BAT`
  volume guard); G-REPRO (control sidecars sha256-identical to the
  committed keeper bundle BEFORE the arm is read; on a mismatch the arm is
  not read until the drift is adjudicated). Both runs registered whatever
  the outcome (rule 15), matrix cell updated with the tested verdict +
  citation in-session, calibration-log entry ercot-244. **BORDERLINE
  VERDICTS AND ANY KEEPER CONSEQUENCE ESCALATE TO THE OWNER, NEVER
  SELF-ADOPTED.**
* **Any kill fires ⇒** FINDING-ercot244 records it at full magnitude, cell
  `R` + evidence note, log entry, STOP.
* **Amendment convention (the ercot-243 precedent):** implementation repairs
  that leave every declared construction unchanged (a column-name spelling,
  a dtype, an alignment assert running on finite rows) are recorded in the
  FINDING as notes; any construction-affecting surprise is an AMENDMENT
  pushed before measurement proceeds.
* **Deliverable order (each pushed before the next starts; blob verification
  after every push touching a ≥300-line file):** (1) this precommit;
  (2) probe + JSON; (3) FINDING + matrix evidence note + calibration-log
  entry; (4) Phase-1 (if licensed): precommit, then mechanism + tests, then
  A/B bundles + registration + payloads, then FINDING/log/matrix.

## 8. Owner-visible flag (not executed here, per the charter)

The 2024/2025 all-resource SCED conduct corpus intake
(PRECOMMIT-ercot242 §6) remains the blocker on any forward-regime SCED
CONDUCT identification (offer surfaces, per-type online composition).
`data/raw/ercot/SCED-CT/` is re-fetch-only and CT-only (corpus README read;
the data is unfetched, not missing). This lane's aggregate `rtolhsl`
identification does not need it and does not touch it; a future per-type
forward-span identification would. Unchartered — flagged only.
