# Forecast retirement/entry screen calibration plan — 2026-07 (the flip-gate lane)

**Purpose.** The forecast-driver capacity-revenue audit program
(`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`, Waves 0–3 +
follow-ups through N-5 complete; the N-6 full-horizon re-run was dropped by the owner
and is NOT re-proposed here) localized the model's entry/exit unfitness to one
dominant frontier: **the economic retirement/entry screens are miscalibrated in
opposite directions in the two market designs**, and that single miss now gates the
entire capacity-market side of the model — it is the remaining ~1/3 of the PJM
curve-position error (`capacity-price-validation-2026-07-14.md` §5), the MISO coal
0-vs-10.9 GW miss, the ERCOT +1386 % over-retirement, and the last open prerequisite
before `capacity_market_clearing` can flip (P-2A §7 prerequisite 2). This document is
the plan for that lane: root-cause decomposition (§1), the ordered fix path to the
flip (§2), a pre-registered acceptance battery (§3), the session prompt pack (§4),
and data needs (§5). **Planning only — no LP was solved and nothing was tuned in the
session that produced this document.**

**North star.** Every item below is framed as "what closes the flip gate": per ISO,
`capacity_market_clearing` flips ON **only once that ISO's Pass-2 accredited position
— computed from a calibrated hindcast fleet on its own published accreditation basis
— lands in the priced region of its own demand curve in the year(s) the real market
priced, and stays out of it in the years it didn't.** The full gate is stated
precisely in §2.1.

**Method.** Verified against `origin/main` at HEAD 2026-07-15 (merge-base `825ea75`):
the four committed 2021–2025 realized hindcasts
(`docs/hindcast-reports/{ercot,pjm}-2021-2025-realized-p2c*-2026-07-12.md`,
`{miso,nyiso}-2021-2025-realized-2026-07-14.md`), the P-2A/N-5 validations, the P-2B
memo and its R1–R6 landing, the BLK-9 ratio memo
(`capacity-revenue-fom-ratio-2026-07-13.md`), the G-30/G-31 probe reports, the
equilibrium battery (P-3B), the P-3C verdict
(`docs/forecasting-entry-exit-assessment.md`), the gap register
(`docs/gap-register-2026-07.md` §3.9/§3.10), and the live code
(`model/capacity.py::apply_economic_retirements` /
`apply_economic_new_entry` / `capacity_revenue_per_mw_yr`,
`scripts/run_capacity_hindcast.py::build_config`, `config/constants.py::MARKET_DESIGN`,
`data/raw/capacity-market/`).

**Governance (applies to every session in §4).** Rules 1/11/13/14 govern the whole
lane: the fix is root-cause, never a retirement-count or emissions-residual tune; a
residual closable only by a fitted value is an open issue, not a parameter. The fixed
capacity payment is resolved by the accreditation chain + position calibration,
**never a payment haircut** (rule 13; gap-register BLK-9 row says this verbatim).
Holdout years (2022, 2019, ≤2021 solves, H1-2026) are never solved or scored
(rule 22 — the hindcast's 2022 stays an evolved-never-solved bridge). Every new
tunable lands in `ScenarioConfig`/`constants.py` with a citation and appears in
`run_config.json` (rules 5/24). Forecast probes and hindcasts register on the
forecast-validation dashboard only — never the backcast dashboard. Push via
`mcp__github__push_files` only.

---

## 1. Root-cause decomposition of the retirement/entry miss (Task A)

The two market designs fail in opposite directions, through **different mechanisms**.
Each subsection names the mechanism, grades it *structural* (a mechanism the real
market has and the model lacks, or vice versa — rule 1 work) vs *calibration* (the
mechanism exists, its level/inputs are wrong), and routes it to an owner.

### 1.1 Direction 1 — capacity-market ISOs retire ~nothing (PJM −63 %, MISO −95 %, NYISO fossil −100 %, NEISO 0 MW / 25 yr)

**Mechanism (proven, arithmetic):** the fixed-mode capacity payment
`net_cone_per_kw_yr × accreditation` clears **1.26×–4.92× of FOM-only going-forward
cost for every fossil/CCS class in every capacity-market ISO**
(`capacity-revenue-fom-ratio-2026-07-13.md` §3; BLK-9). Since the screen tests
`net_revenue ≥ GFC` and `net_revenue ≥ capacity term` by construction, **fossil
economic exit is arithmetically impossible** — the energy-margin term is structurally
decorative. The measured record reproduces this exactly: zero `reason:"economic"`
fossil retirements in any year of the PJM, MISO, NYISO hindcasts or the NEISO 25-year
run (T2.4c), against 6.9/10.9/0.4 GW of real coal/CT/oil exits. MISO is the cleanest
reproduction (coal at the 1.26 cliff-edge still cannot post a loss year; its 10.9 GW
coal miss is the largest single capacity miss in the program).

- **Class: STRUCTURAL — a non-responsive price where the real market has a sloped
  curve.** The real markets pay a position-dependent price (PJM VRR, MISO RBDC,
  NYISO ICAP curve, ISO-NE MRI); a fleet that stays long drives its own price to $0
  and exits resume. The model's flat price cannot produce that restoring force
  (T2.2b: reserve margin monotone 25/25 years, zero sign changes).
- **Resolution (already designed, partially landed):** the CR chain — CR-1 curve
  (landed, default-off, instrument-validated by P-2A Pass 1), the P-2B Option A
  basis migration (landed for PJM as N-4/N-5: R1 UCAP anchor, R2 published-FPR
  requirement, R3 ELCC-class supply ledger, R4 basis-consistent payment seam), and
  the flip (BLK-4). **Not** a haircut to `net_cone_per_kw_yr` — that would force the
  ratio below 1 with no published basis and no forward analogue (rule 13).
- **What remains after N-5 (this lane's object):** the position is still long for
  fleet reasons. The 2026-07-14 re-validation restates PJM's hindcast position at
  **1.06–1.15** — still past the VRR zero-cross at 1.045, still paying $0 in every
  year including the 2025/26 shortage that cleared at 98.5 $/kW-yr. With the basis
  errors closed, **the residual length is cleanly the fleet error**: the model
  retires too little (≈1/3 of the original P-2A excess) *and* over-builds additions
  (§1.5). Closing it is "position calibration" — P-2A §7 prerequisite 2.

**The nuclear inversion — three distinct things, only one of them a model defect.**
The hindcasts' only retirements in these ISOs are nuclear, 100 % scored-false. Keep
the components separate:

1. *Mechanism risk (real, latent):* nuclear is the only class with a fixed-payment
   ratio < 1.0 everywhere (0.60–0.82), so it is the only class the economic screen
   *can* retire — the retirement signal is inverted onto the one technology that
   did not retire. In the committed hindcasts the **economic screen actually retired
   zero nuclear** (survivors clear margin + §45U/ZEC) — the inversion is a live risk
   under revenue shocks, not the realized failure. Structural; resolved by the same
   CR chain (once fossil ratios respond, nuclear stops being the unique exit valve).
2. *Announced-channel information artifact (PJM Byron/Dresden):* the model honored a
   2020-vintage EIA-860 planned date that IL CEJA later reversed. From an as-of-2020
   information set this was the *correct call at the time*; scoring it false is an
   information-set question for the scoring memo (RC-0B), not a screen defect.
3. *Actuals-coverage artifact (NYISO Indian Point 3, MISO Palisades):* the committed
   EIA-860 retired sheet omits plants 8907 and 1715 entirely, so a genuinely correct
   retirement (IP3) scores 100 % false and Palisades' restart-complicated case is
   unscoreable. **Scoring-target data fix (RD-5), not a model change.**

### 1.2 Direction 2 — ERCOT over-retires ~15× (22.8 vs 1.5 GW), with 96 % false-retire

Three stacked causes, one owned elsewhere:

1. **Screen scarcity/AS revenue level ≈ 25 % of the SOM benchmark (BLK-6) —
   CALIBRATION-of-a-structural-mechanism, owned by G-20/G-22, referenced as a
   dependency, NOT absorbed here.** The screens' CT revenue is 17.2 $/kW-yr against
   the Potomac SOM ≈ 68 anchor (`cross-model-corridor-2026-07-13.md` §2.1). With no
   capacity payment and scarcity rent at a quarter of benchmark, marginal coal/steam
   margins read negative and the screen cuts them. Every ERCOT number in this lane is
   conditioned on that level; this plan measures the residual the G-20/G-22 lane must
   close (§3 T-R3) rather than duplicating its work.
2. **In-year scarcity never forms in the hindcast — STRUCTURAL, this lane's charter
   to scope (not implement blind).** The perfect-foresight LP on the over-supplied
   2020-vintage fleet clears every hour with ample reserves (ORDC overlay $0.00 in
   every year of every arm, Winter Storm Uri included — G-30/G-31 reports). The
   G-31 verdict names the structural direction: forecast-mode availability is too
   high because the model carries no **measured-admissible correlated forced-outage
   / extreme-weather derating** (EFORd-based, cold-snap-correlated — rule-13
   admissible: regenerates forward, responds to conditions), so the scarcity that
   really happened is physically absent from the in-year LP. RC-2A scopes this as a
   design memo; implementation is chartered on its evidence.
3. **First-wave timing — STRUCTURAL, two corrective arms already built and
   probe-validated (G-30/G-31), both default-off.** The largest wave (coal, 14 GW)
   is decided in the quarantined 2022 bridge on the 2021 raw dual, before any
   admissible forward signal exists. `entry_lookahead_reprice` (zero-DOF developer
   pro-forma) unlocks waves 2+ (over-retire 22.8→15.8 GW; first non-zero solar
   entry); `staged_oversupply_thinning` (deactivation-lead-time rate cap, cited to
   notice periods) spreads the first wave into priceable years (coal false-retire
   13.96→6.47 GW, recall band FAIL→PASS) at a real LP-size/runtime cost. Neither is
   a fitted knob; composition and default posture are RC-2A's question.

Note the ERCOT screens are **highly sensitive to the still-uncalibrated scarcity
level** (the 2026-07-05→07-12 hindcast vintage moved 9.7→22.8 GW retired across the
AS-co-opt/FOM merge week). That sensitivity is itself evidence: absolute ERCOT exit
calls stay unfit until BLK-6 closes, whatever this lane does about timing.

### 1.3 The retirement-threshold / GFC interaction — DOF hygiene (calibration-adjacent)

The screen's free parameters are the per-fuel loss-year thresholds
(`retirement_years_coal=3` — see the RC-D1 status note below; `gas_ct/gas_st/oil=2`,
`gas_cc/nuclear=3` — `scenarios.py:283-289`) and the GFC construction (`fixed_om_*`
ATB/Lazard-cited; `retirement_fom_multiplier_coal=1.3`, Lazard-cited). Two problems,
neither of which is "tune them":

- **The loss-year thresholds carry no external identification source** — bare
  comments, no citation. Under an understated revenue signal, coal's 1-year trigger
  is a hair-trigger (ERCOT); under an overstated one it is unreachable (capacity-
  market ISOs). They are DOF-ledger items (rule 21) that must be **identified from
  measured behaviour** — announced-to-deactivation lag distributions derivable from
  on-disk EIA-860 vintage history, RTO deactivation-notice periods (RD-6) — and then
  frozen against residuals (rule 23). RC-0B owns the identification memo.

  **RC-D1 status (landed 2026-07-16):** the coal row is now **identified and
  adopted** — `retirement_years_coal` moved 1 → **3** (D1 Option B), the measured
  EIA-860 announced-to-deactivation lag (cap-weighted / ≥300 MW median = 3 yr,
  left-censored so a conservative floor; RC-0B §a.3/§a.4/§d,
  `retirement-dof-identification-2026-07-15.md`). Cited to the lag table only, never
  a residual (rules 1/14); re-derives only when the EIA-860 vintages update (rule
  23). Per rule 19 the threshold now carries the full decision+lead-time (D+L)
  deactivation total, so `staged_oversupply_thinning` stays default-off (the same
  physical queue is not double-counted; §a.6). The remaining loss-year thresholds
  (`gas_ct/gas_st/oil/gas_cc/nuclear`) stay **open DOF-ledger rows** — RC-0B §a.4
  graded them consistent-but-unidentified, so they hold pending their own data. The
  RC-0B §d LOYO-within-2023-2025 re-probe was **deferred by owner decision** (the
  owner skipped the RC-1A curve-ON re-probe and elected to land the change on
  identification alone); no hindcast LOYO was run, and RC-2B grades the gate
  analytically with this caveat. Backcast-invariant: the threshold is forecast-side
  capacity-evolution only, so every backcast keeper is byte-identical and no
  dashboard is touched.
- **GFC is FOM-only by construction** while the monitors' going-forward benchmark
  (PJM Avoidable Cost Rates, the SOM avoidable-cost tables) includes avoidable
  labor/maintenance/capex categories. Whether FOM-only is understating the bar (which
  would *worsen* under-retirement in capacity-market ISOs once the payment responds)
  is an identification question against published ACR data (RD-4), answered before
  any threshold moves. If the published bar and the ATB FOM differ, rule 14 applies:
  prefer the measured bar, then fix whatever it breaks.

**Explicitly:** if a probe shows the screens only reproduce reality with, say,
`retirement_years_coal=2` *and no data identifies 2*, that is an open root-cause
issue (the revenue signal is still wrong), not a parameter change.

### 1.4 BLK-8 — the solar-entry zero: this lane's diagnosis, possibly its own fix

Solar additions: ERCOT **0 vs 25.1 GW**, PJM **0 vs 13.1 GW**, MISO 6 vs 18.6 GW —
the program's largest additions miss — while NYISO *over*-builds solar +264 %. The
entry screen (`apply_economic_new_entry`) values a zonal-CF-shaped revenue + attribute
price against `lcoe × 8760 × base_cf`. Candidate terms, pre-registered for the RC-0C
decomposition:

| # | Term | Evidence for | Class | If dominant, owner |
|---|---|---|---|---|
| a | **Screen price signal too low** (same starved signal as §1.2: zero scarcity + prior-year perfect-foresight duals on an over-supplied fleet) | G-30: lookahead arm alone unlocked solar 0→4 GW in ERCOT — no cost-side change | structural | THIS lane (shared root with §1.2; the lookahead/scarcity work is the fix) |
| b | **Capex vintage too high** (Wright's-Law on hardcoded global deployment; hindcast years 2021–25 may not see the realized capex decline; ATB calendar files landed P-1D but the entry path's usage unverified) | solar LCOE fell ~20 % over the window while the model's decline is deployment-indexed | calibration (input) | this lane diagnoses; fix is a cited data re-derivation (rule 23) |
| c | **VRE earns zero capacity revenue everywhere** (BLK-7) — even in ISOs that pay ELCC-accredited VRE | PJM solar would earn ~0.08–0.11 × curve price post-N-5 basis; small but nonzero | structural | this lane (small work item, rides the R3/R4 accreditation resolver) |
| d | **Negative-price / cannibalization treatment** — shape-aware CF screen sees solar-hour prices depressed by the model's own (over-built) wind | PJM/MISO wind over-build +271 %/+67 % coexists with the solar zero; NYISO (no wind glut modeled per-zone) overshoots BOTH | structural interaction | route on evidence: entry-sizing (§1.5) vs price formation |
| e | **Queue caps / block granularity** (`QUEUE_CAP_PER_TECH_GW`, chunky blocks) | NYISO builds in 1–2 GW blocks; MISO solar stops flat at 6 GW | structural (sizing) | §1.5 work item |

Verdict on placement: **the diagnosis belongs in this lane** — terms (a), (c), (e)
are screen-calibration work sharing this lane's harness and signal, and (a) is
literally the same root cause as the ERCOT over-retire. **Split trigger:** if RC-0C
finds term (b) (cost/LCOE input) dominant, the fix forks to its own small chartered
item (a data re-derivation with rule-23 citations), because it is an input-fidelity
fix, not screen calibration. BLK-8 keeps its gap-register row either way until the
re-scored hindcasts show solar recall > 0 in ERCOT *and* PJM.

### 1.5 The additions side of position calibration — backstop over-fire + chunk sizing

Position = accredited supply ÷ requirement; a too-long fleet is over-building as much
as under-retiring. The measured record: NYISO gas_ct +5494 % (a 4 GW backstop block
fired at the near-zero seed-year reserve margin, then RM balloons 3.4 %→34 % — the
I12 de-firm→overshoot signature), MISO gas_cc +133 % / wind +67 % (chunky 3–4 GW
blocks pushing RM to 31 %), PJM wind +271 % / gas_cc +41 %. Mechanisms: the
`reserve_margin_build_enabled` backstop's need-sizing on a one-pass loop that
over-corrects, plus entry block granularity. **Structural (sizing/dynamics), this
lane** — and note the N-5 interaction the P-2B memo §6 predicted: PJM supply now
accredits ~15 % lower on the ELCC basis, so the floor retains more and the backstop
builds more; the RC-1A probe must *measure* that shift (it is a basis-consistency
consequence, never a reason to re-touch the basis).

### 1.6 Decomposition summary

| Miss | Mechanism | Class | Owner |
|---|---|---|---|
| PJM/MISO/NYISO/NEISO fossil exit ≈ 0 | BLK-9 flat payment ≥ GFC ∀ fossil | structural | THIS LANE (CR chain: flip gate §2) |
| PJM position long by ≈1/3 post-basis | retirement miss + additions overshoot | structural + dynamics | THIS LANE (prereq 2) |
| Nuclear-only retirement pattern | sub-1.0 ratio + announced-channel artifacts + actuals gaps | mixed | this lane (RC-0B memo + RD-5 data fix); mechanism risk closed by CR chain |
| ERCOT over-retire 22.8 GW | AS/scarcity level 25 % of SOM | calibration of structural mechanism | **G-20/G-22 (dependency)** |
| — same, timing component | first-wave on unpriceable bridge year | structural | this lane (G-30/G-31 arms — composition/default posture) |
| — same, availability component | no correlated forced-outage model in forecast mode | structural | this lane scopes (RC-2A memo), implement on evidence |
| Solar entry 0 GW (BLK-8) | §1.4 terms a–e | mixed | this lane diagnoses (RC-0C); split trigger on term b |
| Threshold/GFC DOFs unidentified | rule-21 ledger gap | identification | this lane (RC-0B); **coal threshold identified + adopted (coal=3, RC-D1 2026-07-16)** — GFC and the other loss-year thresholds stay open |

---

## 2. The ordered fix path to the `capacity_market_clearing` flip (Task B)

### 2.1 The flip gate, stated precisely

`capacity_market_clearing` flips ON **per ISO**, and only when ALL of the following
hold for that ISO:

1. **Basis (P-2A §7 prereq 1 — PJM CLOSED by N-5).** Requirement, supply ledger,
   curve position, curve $ anchor, and per-unit payment all sit on the ISO's own
   published accreditation basis (P-2B Option A). PJM: done (R1–R4). MISO: keep-and-
   verify (its EFORd pairing is ~consistent). NYISO: R5a pairing audit must land
   first (ICAP-stated IRM vs UCAP supply — position understated ~5–7 %, the
   *opposite*-sign error class). NEISO: R5b qualified-capacity audit must land first.
2. **Instrument.** The ISO's curve is validated at the P-2A Pass-1 bar on
   **per-delivery-year published parameters** (prereq 3): shape exact, anchor from
   the matching vintage — no frozen single-vintage anchor held across years. For
   MISO this requires the seasonal grain (prereq 4a); for NYISO the multi-vintage
   curve intake (prereq 4b).
3. **Position (prereq 2 — THE OBJECT OF THIS LANE).** On the calibrated hindcast
   fleet, restated through `scripts/validate_capacity_prices.py` Pass 2, the ISO's
   accredited position lands **in the priced region of its own curve in the year(s)
   the real auction priced, and outside it in the years it cleared ≈$0/floor** —
   quantified as |model position − published auction position| small relative to the
   curve's priced width (PJM's priced region is ≈5.6 points wide, 0.989–1.045; a
   ≥18-point error was 3× the curve — the calibrated target is an error ≲ half the
   priced width, pre-registered per ISO in §3 T-R4 *before* any probe runs).
4. **Skill.** The curve-ON probe hindcast strictly improves retirement recall and
   false-retire vs the committed fixed-mode leg without degrading the additions
   bands, and any mechanism-driven verdict flip is scored leave-one-year-out within
   2023–2025 (rule 22's LOYO clause) before the flip commit.
5. **Plumbing.** A per-ISO gate surface exists. P-2A §7 flagged that the current
   single global bool cannot be ON for NEISO while OFF for PJM; the flip cannot be
   executed per-ISO until the gate is per-ISO (RC-1B; structural plumbing, default
   byte-identical).

The flip itself is a dedicated, cited commit per ISO (W2-P3 convention), which also
executes **R4's deferred re-derivation**: the legacy fixed anchor
(`net_cone_per_kw_yr`, e.g. PJM's uncited 100.0) is re-derived to the published
UCAP-basis figure *in the flip commit* (accreditation-basis memo §4.3-R4) — until
then it stays, explicitly labeled legacy.

### 2.2 The circularity, and how the lane breaks it

Prerequisite 3 looks circular: the position only shortens if fossil retires, and
fossil cannot retire while the fixed payment is active (BLK-9) — but the curve stays
off until the position is trustworthy (P-2A's correct call: flipping on today
substitutes a fleet-error-driven $0 for the fixed price). **Resolution: probe-mode
curve-ON hindcasts** (`capacity_market_clearing=True` as an explicit harness A/B arm,
defaults untouched, forecast-validation dashboard only). The probe *is* the
position-calibration measurement: it answers whether the coupled system —
$0-at-long-position → fossil GFC uncovered → economic exits resume → position
shortens → price rises along the curve — converges toward the observed exit path and
the auction's own position, with every divergence routed to a named mechanism
(§1.3 thresholds, §1.5 additions dynamics, §1.4 entry terms). This is rule-1 work:
the probe tests a real market mechanism end-to-end; it never bends the curve, the
basis, or the thresholds to make the numbers land.

**Pre-registered risk (stated before any probe runs):** with the curve ON at a long
position, *every* fossil class loses its payment simultaneously — PJM could flip
into the ERCOT failure mode (a mass first-wave exit / I13 sawtooth). The structural
throttle already exists and is admissible (`staged_oversupply_thinning`, a
deactivation-lead-time rate cap cited to notice periods — not a fitted knob); I5/I13
are scored on every probe leg (§3 T-R5-inv). If the first curve-ON wave is
unphysically large, the answer is the lead-time mechanism and the §1.3
identification work — never re-softening the price.

### 2.3 Ordered steps

```
F-0  (done)  P-2B Option A basis migration for PJM (N-4/N-5): R1–R4 landed,
             Pass-1B anchor error 0 %, position 1.29–1.36 → 1.06–1.15.
F-1  RC-0A   Intake: per-delivery-year curve vintages (PJM pre-2025/26 params;
             NYISO 2021–25 ICAP curve vintages; MISO PRA/RBDC history + seasonal
             grain), PJM ACR/avoidable-cost tables, actuals-coverage fix (RD-5),
             deactivation-notice citations (RD-6), R5a/R5b filings.        [data]
F-2  RC-0B   Identification memo: loss-year thresholds + GFC vs published
             avoidable-cost benchmarks; hindcast channel-split & information-set
             scoring adjudication (Byron/Dresden class).                [no code]
F-3  RC-0C   BLK-8 entry-stack decomposition (terms a–e), ERCOT+PJM+MISO.
F-4  RC-1B   Plumbing: per-ISO clearing gate + per-delivery-year net-CONE
             resolver (prereq 3) + forward-year anchor policy (hold-last-vintage
             + documented escalator decision). Default byte-identity proven.
F-5  RC-1C   MISO seasonal curve grain (prereq 4a) + NYISO curve-vintage wiring
             (prereq 4b). RC-1D: R5a/R5b pairing-audit memos (gate item 1 for
             NYISO/NEISO).
F-6  RC-1A ⛔ Curve-ON probe hindcasts (PJM + MISO first; NYISO after F-5/R5a):
             the position-calibration measurement, scored against §3
             T-R1/T-R2/T-R4/T-R7 + invariants. Iterate root-cause fixes surfaced
             by the probe (each its own cited change, LOYO-scored) until the §2.1
             gate quantities are measured — or the honest blockers are named.
F-7  RC-2A   ERCOT composition probe (G-30/G-31 arms; + the G-20/G-22 increment
             if landed) + forced-outage availability design memo. Measures the
             residual ERCOT level gap for the G-20/G-22 lane (T-R3).
F-8  RC-2B ⛔ Flip-recommendation memo per ISO: grades the battery, quantifies
             gate items 1–5 per ISO, owner-decision box.
F-9  RC-3A   Flip commits per approved ISO (incl. R4 anchor re-derivation),
             then the gated re-runs: T1.7 net-CONE ladder + tornado capacity
             entries, P-3D hindcast re-scores, P-3C verdict-table update.
```

Parallelism: F-1/F-2/F-3 are independent (Wave 0). F-4/F-5 are independent of each
other and of F-3, but F-5 needs F-1's intake. F-6 needs F-4 (per-ISO gate + vintage
anchors) and is the ⛔ gate for F-8. F-7 can run parallel with F-6 (different ISO,
different files; obey rule 12's ≤2 concurrent per-plant invocations). F-8 needs
F-6+F-7 (+F-2's scoring adjudication). F-9 needs F-8 + owner sign-off.

### 2.4 Gap-register reconciliation (no new IDs where lanes exist)

| Plan item | Existing ID | Status change proposed |
|---|---|---|
| Fixed-payment degeneracy | **BLK-9** (§3.9) | resolution path = this plan §2; row unchanged |
| Position calibration / flip | **BLK-3 (closed for PJM by N-5) / BLK-4** | BLK-4 gains this plan as its execution charter |
| ERCOT over-retire (timing/level) | **G-30 / G-31** (+ BLK-5) | this plan §1.2/§3 T-R3 is the lane's continuation |
| ERCOT scarcity/AS level | **G-20 / G-22** (BLK-6) | dependency only — NOT absorbed |
| Solar entry zero | **BLK-8** (§3.9) | RC-0C is the "re-diagnosis" its row calls for; row gains an owner |
| NYISO/NEISO pairing audits | **R5a / R5b** (§3.10) | RC-0A intake + RC-1D memos execute them |
| Additions overshoot / backstop over-fire | none | propose ONE new §3.9 row (RC-1A files it with evidence) — the only new ID this plan creates |
| MISO forecast blocker | ~~BLK-1~~ | already closed (PR #2223); first MISO hindcast committed 2026-07-14 |

---

## 3. Pre-registered test & acceptance battery (Task C)

All expectations below are registered **now, before any run**. Bands are graded
against the four committed hindcast bundles (the BEFORE legs — ERCOT/PJM p2c
2026-07-12, MISO/NYISO 2026-07-14) and are **never widened**; a FAIL is a root-cause
investigation (rules 1/11/14). Harnesses are the existing ones — `run_capacity_hindcast.py`
(+ a `--capacity-market-clearing` probe flag it must grow, mirroring its existing
probe-arm pattern), `score_capacity_hindcast.py`, `validate_capacity_prices.py`
(Pass 2), `run_driver_battery.py` (T1.7), `run_equilibrium_battery.py`
(T2.2b/T2.4c/T2.5), `check_forecast_invariants.py` (I5/I12/I13). **No new harness is
built where one exists.** All runs are in-train (2021–2025 window, 2022 bridged;
2026–2030 for equilibrium probes); nothing touches a holdout; nothing registers on
the backcast dashboard.

| ID | Run (probe legs vs committed BEFORE) | Pre-registered expectation (PASS criteria) |
|---|---|---|
| **T-R1** | PJM 2021–25 realized hindcast, curve-ON probe vs fixed BEFORE | (a) fossil `reason:"economic"` exits appear for the first time: coal recall > 0 with cumulative coal exits in [2, 14] GW (actual 6.9 — order-of-magnitude band, half-to-2×); (b) cumulative thermal exits ≤ 2× actual 11.1 GW (over-shoot guard — the ERCOT-failure-mode tripwire); (c) **zero economic nuclear exits** (T-R7); (d) 2025-step restated position moves ≥ half the distance from 1.06 toward the auction's 1.007; (e) additions bands not degraded vs BEFORE (solar/wind/gas_cc/storage each no further from actual) |
| **T-R2** | MISO same design (annual curve until F-5 lands; seasonal re-run after) | (a) coal economic exits resume: recall > 0, cumulative in [3, 22] GW (actual 10.9); (b) gas_cc/wind additions **fall** vs BEFORE's +133 %/+67 % (a responsive price should relieve the backstop/entry over-fire); (c) 2025 CO2 error sign moves from +14 % toward 0 (report-only — decomposition caveat per plan §1.4 of the hindcast harness) |
| **T-R3** | ERCOT composition probe: committed G-30+G-31 arms; leg 2 adds the G-20/G-22 co-opt increment if landed by run time | (a) reproduce the committed arm results (lookahead+staged: thermal 12.7 GW, coal 6.5 GW) at HEAD; (b) pre-registered honesty: composition alone does NOT reach the actual 1.5 GW — the probe's deliverable is the **quantified residual level gap** (screen CT $/kW-yr vs SOM ≈68) handed to G-20/G-22; (c) solar entry strictly > 0 (BEFORE: 4 GW on lookahead); (d) no in-year ORDC formation is EXPECTED without the availability work (§1.2-2) — finding it would itself be a discovery to explain |
| **T-R4** | `validate_capacity_prices.py` Pass 2 restated on each probe fleet (no LP) | Per hindcast year, model position vs published auction position: PJM 2025 within ±0.028 (half the 5.6-pt priced width) of 1.007; long years (2021/23/24, auction positions 1.07–1.09) remain OUT of the priced region (the curve must NOT pay in years the real market cleared at floor/$0-ish levels) |
| **T-R5** | `run_equilibrium_battery.py` re-run, curve-ON probe: NEISO or PJM 2026–2030 base + overbuild | (a) T2.4a flips: capacity value **collapses** under +10 GW overbuild; (b) T2.4c flips: retirements resume post-shock (>0 MW); (c) T2.2b directional: RM no longer monotone over the probe window (≥1 sign change); (d) **T-R5-inv:** I5 (no retire-reenter) and I13 (no sawtooth) PASS on every leg — the §2.2 risk gate; (e) T2.5 ERCOT control unchanged (curve mode is a no-op there, byte-identical) |
| **T-R6** | `run_driver_battery.py` T1.7 net-CONE ladder + tornado capacity entries | Re-run ONLY after a flip commit (gated per the audit plan); expectation unchanged from its pre-registration: retirements monotone ↓ / entry monotone ↑ in the anchor, ERCOT byte-identical negative control |
| **T-R7** | Nuclear guard, every probe leg, every ISO | Economic-channel nuclear exits = 0 (the §45U/ZEC attribute path holds); announced-channel events adjudicated per the RC-0B scoring memo, reported in both raw and information-set-adjusted recall |
| **T-R8** | Scoring-hygiene re-score after RD-5 actuals fix (no re-solve — `score_capacity_hindcast.py` on the committed bundles) | NYISO false-retire → ≈0 (IP3 becomes a correct recall); MISO Palisades adjudicated per RC-0B's restart rule; ERCOT/PJM rows byte-identical (no 8907/1715 exposure) |
| **T-R9** | BLK-8 decomposition ledger (RC-0C; instrumented screen logs, probe re-solves as needed) | Each §1.4 term (a–e) carries a measured $/MW-yr (or GW) attribution per ISO-year; the dominant term is named with its routing (split trigger fires iff term b dominates); no model default changes in the session |

**Grading protocol.** Every T-R table lands in the session's findings doc with
model-vs-actual-vs-BEFORE columns; every FAIL gets a one-paragraph mechanism
hypothesis naming the responsible module (the P-1A convention). Verdict-relevant
flips are LOYO-scored within 2023–2025 before promotion. The battery's aggregate
result feeds RC-2B's per-ISO gate scorecard (§2.1 items 1–5, each PASS/OPEN with
evidence).

---

## 4. Prompt pack (Task D)

### 4.1 Dependency graph

```
WAVE 0 (parallel, independent):
  RC-0A [SONNET] curve-vintage/ACR/actuals/notice-period intake      ─┐
  RC-0B [FABLE]  threshold+GFC identification & scoring memo          ├─ no cross-deps
  RC-0C [OPUS]   BLK-8 entry-stack decomposition                     ─┘

WAVE 1 (each starts when its own deps land):
  RC-1B [SONNET] per-ISO gate + per-delivery-year net-CONE resolver  (no deps)
  RC-1C [OPUS]   MISO seasonal grain + NYISO vintage wiring          (needs RC-0A)
  RC-1D [SONNET] R5a/R5b pairing-audit memos                          (needs RC-0A)
  RC-1A [OPUS] ⛔ curve-ON probe hindcasts PJM+MISO (+NYISO if R5a    (needs RC-1B;
               clean & RC-1C landed)                                   RC-0B for scoring)

WAVE 2 (after Wave 1):
  RC-2A [OPUS]   ERCOT composition probe + availability design memo  (parallel w/ RC-1A,
                                                                       ≤2 concurrent solves)
  RC-2B [FABLE] ⛔ per-ISO flip-recommendation memo                    (needs RC-1A, RC-2A,
                                                                       RC-1D)
WAVE 3 (owner sign-off on RC-2B):
  RC-3A [OPUS]   flip commits + R4 anchor re-derivation + T1.7/tornado
                 re-runs + P-3D re-scores + verdict-table update trigger
```

Model assignment convention (same as the audit plan): SONNET for intake and scripted
compute, OPUS for design-heavy implementation and probe campaigns, FABLE for
adjudication/verdict memos. Compute sessions obey rule 12 internally (years
sequential; ≤2 concurrent invocations; per-plant multi-zone cap).

> **AMENDED 2026-07-15 (owner order — CLAUDE.md rule 27).** After a Sonnet session
> truncated `constants.py` (6,368 → 33 lines) and merged fragment "restores" onto
> main, **no further session in this lane is assigned to Sonnet**: every remaining
> session (RC-1E, RC-2A, RC-2B, RC-3A, and any repair/follow-up) runs on OPUS or
> FABLE regardless of scope. The [SONNET] labels on already-executed sessions
> (RC-0A, RC-1B, RC-1D) are historical record only. Rule 27's push-integrity
> protocol (verify every ≥300-line pushed blob; no placeholder/partial commits of
> existing source files) binds every session in this pack.

**Standing constraints for every prompt (copied into each):** fresh branch off latest
`origin/main`; findings-only sessions never tune; forecast probes and hindcasts
register on the forecast-validation dashboard only, never the backcast dashboard;
no solve/score of 2022, ≤2021, 2019 or H1-2026 (rule 22 — hindcast 2022 stays an
evolved-never-solved bridge); every new tunable in `ScenarioConfig`/`constants.py`
with citation + `run_config.json` visibility (rules 5/24); push via
`mcp__github__push_files` only; no per-task GitHub Actions workflows (CLAUDE.md CI
policy).

### 4.2 Prompts

#### RC-0A [SONNET] — Intake: curve vintages, avoidable-cost benchmarks, actuals coverage, notice periods

```
[SONNET] RC-0A — Data intake: per-delivery-year capacity-curve vintages, PJM ACR,
retired-sheet coverage, deactivation notice periods

Read CLAUDE.md, the data-intake skill, and docs/handoffs/
forecast-retirement-calibration-plan-2026-07.md §1/§2/§5 (RD-1..RD-6, RD-9, RD-10).
Fresh branch off latest origin/main.

Extend the existing capacity-market datatypes (schema-first, write_clean/read_clean,
per-ISO registry modules — same contract as P-0B; do NOT create parallel datatypes):
1. PJM demand-curve vintages for delivery years 2021/22–2024/25 (pre-CIFP era: VRR
   points, net-CONE both bases, IRM, and the era-correct requirement construction —
   record the basis vocabulary per row; the pre-reform years have no FPR, capture
   what PJM actually published). data/raw/capacity-market/demand-curve/pjm/.
2. NYISO ICAP demand-curve vintages 2021–2025 (per-year ARV, seasonal caps, curve
   points, per-locality) — today only 2025-2026 is on disk, which is why P-2A scored
   zero NYISO years.
3. MISO PRA history: pre-RBDC delivery years (PY21/22–24/25 — document the vertical-
   curve regime explicitly rather than inventing curve points) + the PY26/27 seasonal
   RBDC parameters if published.
4. PJM Avoidable Cost Rates: Manual 18 / MSOC default gross ACR by technology class +
   Monitoring Analytics SOM avoidable-cost tables (RD-4) — new small datatype under
   data/raw/capacity-market/, the identification source for RC-0B's GFC audit.
5. Actuals-coverage fix (RD-5): the committed EIA-860 retired sheet omits plants 8907
   (Indian Point) and 1715 (Palisades). Intake the authoritative retired/canceled
   rows (EIA-860/860M), regenerate capacity_actuals_{nyiso,miso}.csv via
   scripts/build_capacity_actuals.py, and document Palisades' restart ambiguity in
   the README (adjudication itself is RC-0B's, not yours).
6. Deactivation-notice/lead-time citations (RD-6): PJM Part V deactivation process,
   ERCOT NPRR/Protocol §3.14 NSO, MISO Attachment Y — as citation rows for
   docs/parameter-citations.md (feeds staged_oversupply_thinning's citation and
   RC-0B's threshold identification).
7. R5a/R5b filings (RD-9/RD-10): NYISO's published IRM→UCAP translation (NYSRC/ICAP
   manual), ISO-NE qualified-capacity definition (FCA qualification docs) — raw
   documents + extracted parameters, no model wiring.
Published market-design parameters and outcomes are rule-13-admissible inputs /
validation observables — mark auction outcomes NEVER-a-fit-target in the dictionary.
Anything login-walled: log exact URL + error under MANUAL DOWNLOADS NEEDED in
docs/handoffs/retirement-lane-intake-<date>.md and move on — never guess values.
No LP solves. Tests: loader-resolvability + schema round-trip, tmp CLEAN_DIR.
Push via mcp__github__push_files.
```

#### RC-0B [FABLE] — Identification memo: thresholds, GFC, and hindcast scoring adjudication

```
[FABLE] RC-0B — Identify the retirement-screen DOFs and adjudicate hindcast scoring
channels (memo, no code)

Read CLAUDE.md (rules 1/13/14/21/23 govern this memo), docs/handoffs/
forecast-retirement-calibration-plan-2026-07.md §1.1/§1.3 (your spec),
docs/handoffs/capacity-revenue-fom-ratio-2026-07-13.md, the four hindcast reports
(docs/hindcast-reports/{ercot,pjm}-2021-2025-realized-p2c*-2026-07-12.md,
{miso,nyiso}-2021-2025-realized-2026-07-14.md), scenarios.py:283-366, and the RC-0A
ACR + notice-period intakes. No code changes — memo session; findings only, never
tune.

Write docs/handoffs/retirement-dof-identification-<date>.md:
(a) Loss-year thresholds (retirement_years_*): derive the announced-to-deactivation
    lag distribution per fuel from the on-disk EIA-860 vintage history + the RD-6
    notice periods; state per fuel whether the current values {coal:1, ct/st/oil:2,
    cc/nuclear:3} are identified, mis-identified, or unidentifiable from this data.
    A value the data cannot identify stays where it is and is ledgered as an open
    DOF (rule 21) — you do not propose tuning it to any hindcast residual.
(b) Going-forward cost: reconcile the FOM-only GFC construction against the PJM ACR /
    SOM avoidable-cost benchmarks (RC-0A #4) per class. If the published avoidable-
    cost bar materially differs from ATB FOM, recommend the measured bar per rule 14
    (with the expected downstream effects named, esp. its interaction with BLK-9
    ratios), citing the data — never citing a retirement count.
(c) Hindcast channel-split adjudication: which real 2021-25 exits should the
    ECONOMIC screen own vs the announced channel, under the harness's as-of-2020
    information discipline (confirmed instruments dated post-2020 are unknowable at
    forecast start)? Rule on the Byron/Dresden class (information-set-correct,
    reality-reversed) and the Palisades restart: define raw vs information-set-
    adjusted recall so score_capacity_hindcast.py can report both. Scoring
    definitions only — the actuals data fix is RC-0A's.
(d) End with an owner-decision box (options, recommendation, what each re-opens).
Push via mcp__github__push_files.
```

#### RC-0C [OPUS] — BLK-8 solar-entry decomposition

```
[OPUS] RC-0C — Decompose the solar-entry zero (BLK-8): which term starves the screen?

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §1.4
(THE SPEC — terms a-e and the split trigger), docs/gap-register-2026-07.md §3.9
BLK-8, model/capacity.py::apply_economic_new_entry + compute_lcoe, and the ERCOT/PJM/
MISO hindcast reports. Fresh branch off latest origin/main. Findings only — no model
default changes, no tuning, no threshold widening (rules 1/11/14).

1. Instrument the entry screen with a diagnostic per-candidate ledger (revenue terms:
   energy, attribute, capacity; cost terms: capex-vintage/Wright state, CRF, FOM;
   binding caps) emitted per evolution year — diagnostic-only output, no decision
   effect, OFF by default.
2. Re-run the minimum probe set needed to fill the §1.4 attribution table: the
   committed ERCOT/PJM/MISO hindcast configs (BEFORE legs), plus single-term probe
   legs where isolation requires it (e.g. capex pinned to the realized ATB
   calendar-year value as a labeled diagnostic arm — rule 13's default-off probe
   clause; a lookahead-armed leg to price term (a)). Years sequential, ≤2 concurrent
   invocations, separate --out-dirs (rule 12). 2022 stays an evolved-never-solved
   bridge; no holdout year is touched.
3. Commit docs/handoffs/blk8-solar-entry-decomposition-<date>.md: the measured $/MW-yr
   (or GW) attribution per term per ISO-year (plan §3 T-R9), the dominant-term verdict,
   and the routing: term (a) → this lane's scarcity/lookahead work; term (b) → fork a
   cited data re-derivation charter; terms (c)/(e) → named work items with code
   anchors. Register probe runs on the forecast-validation dashboard; NEVER the
   backcast dashboard. Push via mcp__github__push_files.
```

#### RC-1B [SONNET] — Per-ISO gate + per-delivery-year net-CONE resolver

```
[SONNET] RC-1B — Plumbing: per-ISO capacity_market_clearing + vintage-resolved
net-CONE anchors (prereq 3 + gate item 5)

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1
items 2/5, docs/handoffs/capacity-price-validation-2026-07-12.md §7, and
docs/handoffs/accreditation-basis-memo-2026-07-12.md §4.3 (R4 stays deferred to the
flip commit — do NOT re-derive the legacy fixed anchor here). Fresh branch off latest
origin/main. Scope guard: annual capacity-evolution layer only (capacity.py /
constants.py / scenarios.py / pipeline seams) — never the dispatch-layer floors, the
AS co-opt, or any backcast keeper.

1. Grow the clearing gate to a per-ISO surface (e.g. capacity_market_clearing:
   bool | per-ISO mapping resolved through one seam) so a future flip can be ON for
   one ISO and OFF elsewhere (P-2A §7 NEISO note). Global-bool semantics preserved;
   default (all off) byte-identical — prove with the existing byte-identity test
   pattern.
2. Per-delivery-year net-CONE/curve anchoring: MarketDesign resolves curve parameters
   from the capacity-market datatype BY DELIVERY YEAR (RC-0A vintages) instead of one
   frozen vintage; forward years beyond the last published vintage hold-last-vintage
   with the policy documented in the field docstring (a real-dollar escalator is an
   owner decision — present the option, do not enable one). This closes P-2A's
   "frozen single-vintage anchor" residual (±8-15%).
3. run_capacity_hindcast.py grows a --capacity-market-clearing probe flag wired
   through build_config exactly like the existing G-30/G-31 probe arms (default off,
   probe-documented docstring).
4. Tests trivial-first: vintage resolution vs hand values; hold-last behavior;
   per-ISO gate isolation (PJM on / NEISO off); default byte-identity; the T2.1
   arithmetic identity re-asserted in both modes. No default flip anywhere. Update
   methodology-spec §5.9 + parameter citations. Push via mcp__github__push_files.
```

#### RC-1C [OPUS] — MISO seasonal grain + NYISO curve-vintage wiring

```
[OPUS] RC-1C — MISO seasonal RBDC + NYISO multi-vintage ICAP curves (prereq 4)

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1
item 2, docs/handoffs/capacity-price-validation-2026-07-12.md §3.3-3.4 (why MISO and
NYISO are not curve-eligible today), and the RC-0A intakes. Requires RC-0A + RC-1B
merged. Fresh branch off latest origin/main. Same scope guard as RC-1B.

1. MISO: extend the curve seam to the seasonal PRA grain — evaluate the RBDC per
   season on the published seasonal parameters and annualize revenue as the seasonal
   sum (the market's own construction), replacing the annual approximation. The
   model's reserve position stays annual until a seasonal accreditation basis exists
   — document the mapping honestly (one position, four seasonal curve evaluations)
   and its limits; do not invent seasonal fleet accreditation.
2. NYISO: wire the multi-vintage curves (RC-0A #2) through the RC-1B vintage
   resolver; NYISO stays curve-INELIGIBLE until R5a lands (RC-1D) — enforce that in
   the eligibility logic, not prose.
3. Re-run scripts/validate_capacity_prices.py (no LP): MISO Pass 1 becomes scoreable
   at seasonal grain (expect the 2025/26 summer-at-cap / other-seasons-near-zero
   pattern to reproduce directionally); NYISO Pass 1B becomes scoreable for delivery
   years ≤ 2025/26. Commit the refreshed validation report section. Comparison only —
   no parameter bending (rules 1/13/23); ≥2026 delivery rows stay greyed/excluded.
Tests: seasonal evaluation vs hand values; vintage fallback; eligibility gating.
Push via mcp__github__push_files.
```

#### RC-1D [SONNET] — R5a/R5b pairing-audit memos

```
[SONNET] RC-1D — NYISO ICAP/UCAP and NEISO qualified-capacity pairing audits
(R5a/R5b — gap register §3.10)

Read CLAUDE.md, docs/gap-register-2026-07.md §3.10, docs/handoffs/
accreditation-basis-memo-2026-07-12.md §2/§4.1 (the per-ISO published-basis
principle), and the RC-0A filing intakes (RD-9/RD-10). Requires RC-0A. Fresh branch
off latest origin/main. Memo-first: no basis change lands without the filing citation
(stage-5 bar).

1. R5a NYISO: from the published IRM→UCAP translation, adjudicate the requirement
   pairing (today: ICAP-stated IRM vs UCAP supply — position understated ~5-7%,
   over-pays). Specify the exact registry change (ratio or published-UCAP
   requirement row), its citation, and the expected position shift — implement it
   only if the citation is unambiguous; otherwise land the memo + a MANUAL row.
2. R5b NEISO: reconcile the model's (1-EFORd) thermal ledger against ISO-NE's
   qualified-capacity definition (no EFORd derate; availability priced via PFP).
   Same standard: cite-then-implement or memo-only.
3. Update the §3.10 rows with status + evidence; add the basis-consistency tests
   (mirror the PJM R2/R3 test pattern) for whichever half lands.
No LP. LOYO discipline n/a (no keeper touched; forecast-only machinery). Push via
mcp__github__push_files.
```

#### RC-1A [OPUS] ⛔ — Curve-ON probe hindcasts (the position-calibration measurement)

```
[OPUS] RC-1A — Position calibration: curve-ON probe hindcasts for PJM + MISO
(§2.2 — the measurement that breaks the circularity)

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md
§2.1/§2.2/§3 (T-R1/T-R2/T-R4/T-R5-inv/T-R7 are YOUR pre-registered scorecard — read
them before any run and do not restate them looser), docs/handoffs/
capacity-price-validation-2026-07-14.md, and the RC-0B scoring memo. Requires RC-1B
(gate + vintages; MISO seasonal via RC-1C if landed — else run MISO on the annual
curve and label it). Fresh branch off latest origin/main.

1. Run the A/B: committed fixed-mode configs (BEFORE — reproduce at HEAD) vs
   --capacity-market-clearing probe legs, PJM and MISO 2021-2025 realized. Years
   sequential within each invocation; ≤2 concurrent invocations, separate --out-dirs
   (rule 12). 2022 bridged, never solved/read (rule 22). Score with
   score_capacity_hindcast.py + validate_capacity_prices.py Pass 2 restatements +
   check_forecast_invariants.py (I5/I13 on every leg).
2. Grade every T-R row PASS/FAIL against the pre-registered bands. Every FAIL gets a
   mechanism hypothesis naming the module; misses route per plan §1 (thresholds/GFC →
   RC-0B's identified values ONLY if the data identified them; additions overshoot →
   file the §2.4 new gap row with evidence; entry terms → RC-0C's routing). You may
   land root-cause FIXES surfaced by the probe when they are cited, structural, and
   LOYO-scored within 2023-2025 — never a value chosen to move a residual (rules
   1/13/14). If a residual is only closable by an unidentified value, write it up as
   an open blocker instead.
3. Register all runs on the forecast-validation dashboard (register_hindcast.py);
   NEVER the backcast dashboard. Commit
   docs/hindcast-reports/{pjm,miso}-2021-2025-realized-cmc-probe-<date>.md +
   docs/handoffs/position-calibration-findings-<date>.md with the §2.1 gate-item
   scorecard per ISO (items 1-5, PASS/OPEN, evidence). This is the ⛔ gate input for
   RC-2B. Push via mcp__github__push_files.
```

#### RC-2A [OPUS] — ERCOT composition probe + availability design memo

```
[OPUS] RC-2A — ERCOT retirement-level composition probe + forced-outage availability
scoping (G-30/G-31 continuation; BLK-6 stays with G-20/G-22)

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md
§1.2/§3 T-R3, docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md +
ercot-g31-staged-thinning-limited-foresight-2026-07-08.md (the arms you are
composing), and docs/handoffs/cross-model-corridor-2026-07-13.md §2.1 (the SOM
anchors). Fresh branch off latest origin/main. HARD BOUNDARY: the AS co-opt
mechanism itself is G-20/G-22's lane — you consume whatever is on main, you do not
extend it.

1. Probe legs (ERCOT 2021-2025 realized, rule 12 concurrency): (i) HEAD reproduction
   of lookahead+staged (T-R3a); (ii) + the current G-20/G-22 screen increment if any
   landed since 2026-07-12 (label the vintage). Score retirements/additions per
   T-R3; quantify the RESIDUAL screen-revenue level gap per class ($/kW-yr vs the
   SOM CT ≈68 anchor) — that number is the handoff to G-20/G-22, not something you
   close here (rule 1: never a fitted rent).
2. Runtime honesty: the staged arm's LP-bloat (G-31: ~2.7h) is a real cost — report
   wall/RAM per leg and, if a looser cap materially helps, propose it ONLY with its
   lead-time citation (never fitted to the retirement count).
3. Design memo (no implementation): the measured-admissible correlated forced-outage
   / extreme-weather availability model the G-31 verdict named (EFORd-based,
   cold-snap-correlated, rule-13 test stated: regenerates forward from weather-year
   + fleet physics, responds to changed conditions). Enumerate what already derates
   availability (rule 19 — outage windows are backcast-only overlays; what does
   forecast mode carry?), the data needed, backcast/forecast parity implications,
   and an implementation charter. Explicitly scope AGAINST double-counting with the
   ORDC curve's own reserve-error convolution.
4. Findings + probes to the forecast-validation dashboard; findings doc
   docs/handoffs/ercot-retirement-composition-<date>.md. No defaults change. Push
   via mcp__github__push_files.
```

#### RC-2B [FABLE] ⛔ — Per-ISO flip-recommendation memo

```
[FABLE] RC-2B — The flip memo: grade the gate, per ISO, and put the decision to the
owner

Read CLAUDE.md, docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1
(the gate you are grading) + §3 (the battery), the RC-1A position-calibration
findings, the RC-2A ERCOT findings, the RC-1C validation refresh, and the RC-1D
audit memos. Memo only — no code, no solve, no tuning.

Write docs/handoffs/capacity-clearing-flip-memo-<date>.md:
(a) Per ISO (PJM/MISO/NYISO/NEISO/CAISO): the five §2.1 gate items each PASS/OPEN
    with the measured evidence (positions vs auction positions, T-R scores, basis
    status). CAISO is a documented no-op (no curve) — say so and stop.
(b) The honest failure modes of flipping each ISO now vs waiting (incl. the §2.2
    mass-first-wave risk and what the probe legs measured about it).
(c) Which residuals remain and where they live (BLK-6 level gap number from RC-2A;
    additions-overshoot row; any unidentified DOFs from RC-0B).
(d) Owner-decision box per ISO: flip / hold with named blocker / hold pending
    G-20/G-22. A recommended flip must cite exactly which battery rows justify it
    and which LOYO scores back any mechanism change involved.
Be adversarial, not celebratory — a $0-paying curve and an always-paying constant
are BOTH wrong; recommend ON only where the probe showed the coupled system tracks
reality. Push via mcp__github__push_files.
```

#### RC-3A [OPUS] — Flip execution + gated re-runs (reassigned from SONNET, rule 27)

```
[OPUS] RC-3A — Execute the approved flips + the gated re-runs

Read CLAUDE.md, the RC-2B memo + the owner's sign-off (do NOT start without it),
docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.3 F-9, and
docs/handoffs/accreditation-basis-memo-2026-07-12.md §4.3-R4. Fresh branch off
latest origin/main.

1. One dedicated commit per approved ISO: per-ISO gate ON, citing the RC-2B memo;
   the same commit executes R4 for that ISO (legacy fixed net_cone_per_kw_yr
   re-derived to the published basis figure, reconciliation test updated).
2. Re-run the gated batteries: T1.7 net-CONE ladder + tornado capacity entries
   (run_driver_battery.py — the audit plan gated these on a flip); the equilibrium
   probe rows T-R5 on the flipped default; P-3D hindcast re-scores for the flipped
   ISOs (register on the forecast-validation dashboard).
3. Trigger the P-3C verdict-table update: file the follow-up session request (or
   update rows 7-12/14 of docs/forecasting-entry-exit-assessment.md yourself if the
   evidence is mechanical), and refresh the §2.4 gap-register rows (BLK-4/BLK-9
   status). /sync-docs at session end (methodology spec §5.9, parameter citations).
Years sequential; ≤2 concurrent invocations; no holdout touched; nothing on the
backcast dashboard. Push via mcp__github__push_files.
```

---

## 5. Data needs (Task E)

Storage per the `data-intake` skill (schema-first, `data/raw/` immutable, citations
into `parameter-citations.md`). "Fetch" = Sonnet session over the proxy;
**anything ERCOT-MIS-hosted is presumed credential-blocked** (precedent: the NP6 HSL
attempt). On-disk inventory verified 2026-07-15: PJM demand-curve vintages 2025/26–
2027/28 only; NYISO 2025-2026 only; MISO seasonal RBDC 2025-2026 + seasonal IRM
2023-2025; NEISO 2020/21–2027/28 (adequate).

| # | Dataset | For | Source | Fetchability |
|---|---|---|---|---|
| RD-1 | PJM BRA planning parameters, delivery years 2021/22–2024/25 (VRR points, net-CONE both bases, IRM; pre-CIFP requirement vocabulary) | prereq 3; T-R4 hindcast-year positions | pjm.com RPM auction-info pages (public PDF/XLS) | **Fetch** |
| RD-2 | NYISO ICAP demand-curve vintages 2021–2025 (ARV, seasonal caps, curve points, localities) + spot history already on disk | prereq 4b; NYISO Pass-1 scoreability | nyiso.com ICAP / demand-curve-reset filings | **Fetch** |
| RD-3 | MISO PRA regime documentation PY21/22–24/25 (vertical-curve era) + PY26/27 seasonal RBDC parameters when posted | prereq 4a; honest MISO backfill (no invented curve points) | misoenergy.org PRA postings; FERC eLibrary for filings (slower, public) | **Fetch** |
| RD-4 | PJM default/gross Avoidable Cost Rates (Manual 18 / MSOC) + Monitoring Analytics SOM avoidable-cost tables | §1.3 GFC identification (RC-0B) | pjm.com manuals; monitoringanalytics.com (public PDFs — budget extraction time) | **Fetch** |
| RD-5 | EIA-860/860M retired-generator rows for plants 8907 (Indian Point) and 1715 (Palisades); regenerate capacity_actuals CSVs | T-R8 scoring hygiene | eia.gov (public) | **Fetch** |
| RD-6 | RTO deactivation notice/lead-time provisions (PJM Part V, ERCOT §3.14 NSO, MISO Attachment Y) | staged-thinning citation; §1.3 threshold identification | RTO tariffs/protocols (public) | **Fetch** (ERCOT protocol library is public; only MIS data products are credential-blocked) |
| RD-7 | EIA-860 announced→actual retirement lag history | §1.3 threshold identification | **on disk** (EIA-860 vintages) — derive, no fetch | **Derive** |
| RD-8 | Forward net-CONE basis beyond last published vintage (escalator policy) | RC-1B hold-last policy decision | no published source for future vintages — documented hold-last; escalator = owner decision | **MANUAL (owner decision, not data)** |
| RD-9 | NYISO IRM→UCAP translation (NYSRC/ICAP manual) | R5a (RC-1D) | nysrc.org / nyiso.com manuals | **Fetch** |
| RD-10 | ISO-NE FCA qualified-capacity definition | R5b (RC-1D) | iso-ne.com qualification docs | **Fetch** |
| RD-11 | ERCOT Peaker Net Margin live series (MIS dashboard) | RC-2A residual-gap context (SOM PDFs on disk already carry the anchors) | ERCOT MIS | **BLOCKED (presumed credential-walled)** — use the on-disk SOM vintages; log a MANUAL row only if a specific number is missing |

---

## 6. Hard boundaries (what this plan does NOT do)

- **No dispatch-layer changes**: keeper offer curves, floors, commitment bridges, and
  the backcast dashboard are untouched. The one dispatch-adjacent item (forecast-mode
  correlated availability, §1.2-2) enters as a *design memo only* in this lane.
- **No AS co-opt work**: BLK-6 / G-20/G-22 is referenced as a dependency and handed a
  quantified residual (T-R3b); its mechanism is built in its own lane.
- **No payment haircuts, no threshold tuning, no curve bending**: rules 1/13/14/23
  as restated in §0/§1.3. Published parameters move only by citation to their own
  publications.
- **No full-horizon 2026–2050 re-run**: dropped by the owner (N-6); it returns only
  after the flip gate closes (RC-3A triggers the P-3D/P-3C updates, not a horizon
  campaign).
- **No holdout contact**: 2022 remains an evolved-never-solved bridge in every
  hindcast; 2019/H1-2026 are untouched (rule 22).

## 7. What remains UNfit even after this lane closes (honest statement)

Closing this lane makes fossil exit *possible* and the capacity price *responsive*
in the capacity-market ISOs, and it bounds the ERCOT retirement miss to its
scarcity-level root — but it does not make the model fit for absolute entry/exit
calls everywhere. ERCOT exit/entry levels stay gated on the G-20/G-22 scarcity/AS
revenue lane (screens at ~25 % of the SOM anchor until that mechanism lands) and on
the still-unbuilt correlated-availability model this lane only scopes; solar entry
may remain partially unfit if RC-0C shows a cost-side root that needs its own
charter; the adequacy-timing verdict (row 11) additionally hinges on the one-pass
backstop/entry-sizing dynamics this lane measures but may not fully re-architect;
NYISO/NEISO stay curve-ineligible until their pairing audits land, and CAISO's
bilateral-RA proxy stays the documented low-fidelity member with no curve at all;
the long-horizon CO2/energy-mix corridor (row 14) inherits every one of these until
they close; locational (LDA/zonal) capacity curves, CP/PAI performance penalties,
and the Y-3 forward-clearing lag remain explicitly out of scope, so intra-ISO siting
and forward-auction timing are not forecastable claims; and every skill number this
lane produces is **in-train** (2021–2025 hindcasts) — under rule 22 the only honest
out-of-sample evidence remains the untouched 2022 validation year and the
locked-test 2019/H1-2026 one-shots, none of which this lane may touch. Until the
RC-2B gate scorecard says otherwise, every capacity-market entry/exit output should
keep its current label: a fixed-price screen, not a market equilibrium.

---

*Produced 2026-07-15 (planning session — no LP solved, no parameter changed).
Verified against `origin/main` merge-base `825ea75`; hindcast evidence as committed
2026-07-12/14; gate arithmetic from `capacity-revenue-fom-ratio-2026-07-13.md` and
`capacity-price-validation-2026-07-14.md`. Successor to the audit program's P-2A §7
prerequisite chain; supersedes nothing.*
