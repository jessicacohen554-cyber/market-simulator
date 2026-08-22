# PREREG nyiso-150 — the zonal-gradient/2025-level object: the winter-spread measured-input repair (ARM W) and the `cc_reserve_duty_split` re-arm (ARM C′)

**Session nyiso-150, 2026-08-22. Committed and pushed BEFORE any arm solves.**
Control: the designated keeper `2026-08-22-nyiso-149-duty-curve` recipe replayed
at HEAD (`results/calibration/nyiso150_control`). Years 2023/2024/2025, one
bundle per arm, years sequential within each invocation (rule 12); holdout
freeze ACTIVE and untouched — every year solved, scored or read is 2023–2025.

**Authorization.** The owner's in-session directive (2026-08-22, verbatim): *"Is
NYISO at frontier? If not, please continue working thru and finalizing to reach
frontier."* Read together with
`docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md` Q1 option A
(*charter the 2025 offer-level object, with the gradient and the tail as
co-criteria* — the card's own recommendation, and "the last thing standing
between NYISO and a frontier declaration"), this session takes the directive as
the Q1 charter and works the chartered object. Both A/B arms are run and
registered whatever their outcomes; **promotion happens only if the
pre-registered gates below clear and the re-verified determination is not worse
(rule 22 D-5(b) — a worse determination stops and escalates instead)**.

---

## 0. QUEUE PROVENANCE (rule 28(a))

* **ARM C′** is queue item 3 of `ASSESSMENT-nyiso148-frontier-2026-08-21.md` §5
  — *"`cc_reserve_duty_split` re-arm on its standing prereg (PREREG-nyiso146b
  §ARM C), conditioned on 1"* — and its condition (item 1, CHP operating
  conduct) landed at nyiso-149. The nyiso-146b rejection had two legs:
  **(a)** Allegany 7784 fell only −64/−50 % vs the ≥80 % bar; **(b)** C3a-2023
  +9.0 % → +11.3 % — the phantom cheap upstate energy was price-relevant and
  2023 held 1 pp of headroom. Leg (b)'s root cause moved: the CHP
  capacity+conduct repair (nyiso-147/149) landed C3a-2023 at **+3.3 %** (6.7 pp
  headroom). Leg (a) is re-measured on the new merit order — it is an empirical
  question, not a voided one, and C-K2 gates it identically.
* **ARM W** is the winter half of queue item 2 (the 2025 dear-gas level and the
  missing zonal gradient), whose identification is §1 below. The mechanism
  (`nyiso_iroquois_winter_spread`) was A/B'd once at nyiso-82 on the pre-CHP
  keeper — winter decisively fixed (Feb-23 −24.1→−7.6 %, Dec-24 −27.1→−6.3 %,
  Feb-25 −16.8→−5.1 % system-monthly), cost exported to the summer under-price
  — and the recorded re-exercise condition was *"re-exercise this flag as a
  candidate keeper arm when the summer scarcity lane moves."* The summer lane
  has since been adjudicated **exhausted and owner-ledgered** (the rule-22 C3c
  STANDING RULE; rubric v3.3 non-downgrading), which resolves the summer cost
  as an accepted model-class limitation rather than a swap-bar: under rule 14
  `[R-ACCURATE]`, the flat construction's silent compensation of that accepted
  miss is exactly the buried error the rule orders removed. nyiso-122 left the
  cell `O` deliberately (*"an owner question … arming it improves a measured
  input while degrading C3a-2025"*) — this session's owner directive plus the
  Q1 charter supplies that owner round, and W-K5 makes the C3a-2025 concern a
  kill gate rather than a hope.
* DO-NOT-REDO honoured: `nyiso_downstate_ct_gas_daily` stays CT_PEAKER-scoped
  (the LI CC/ST extension is refuted, nyiso-145); the Zone-K bound, the
  min-run/online-hours adjudications, and the nyiso-146 membership artifact are
  untouched.

## 1. ARM W IDENTIFICATION — what the flag actually changes (measured, no LP)

Evaluating the shipped construction at both flag settings
(`scripts/probes/_nyiso150_gradient_phase0.py`,
`results/calibration/_nyiso150_gradient_phase0.json`):

1. **NYC's gas is IDENTICAL flag-on and flag-off in every month of every year.**
   The committed `transco_z6_iroquois_monthly.csv` Iroquois column is
   constructed as *Transco-Z6-NY monthly + the SOM annual spread*, so the
   flag-off additive offset (NYC annual − Iroquois annual) cancels the spread
   exactly and lands NYC on its own measured Transco Z6 NY monthly already.
   The prior reading of this lever as "the NYC winter gas repair" is therefore
   WRONG — pre-registered here so the A/B cannot be sold as one.
2. **The flag-off construction gives Upstate_West PHANTOM gas at both ends.**
   The additive annual offset drags the Marcellus-supplied Tenn Z4 zone up
   with the Iroquois winter blowout and down with its summer: UW resolves to
   **$11.01/MMBtu in Jan-2025** (measured Tenn Z4 world ≈ $3.5) and
   **$0.16–0.64 in summer-2025** (below any measured print). Flag-on replaces
   this with the zone's measured SOM annual level riding the Henry-Hub shape
   ($3.54 Jan-2025; $2.32–2.61 summer) — the physically-sane series.
3. **The reference zones (Capital_Hudson / Lower_Hudson / Long_Island) get the
   Algonquin-shaped winter reallocation** of the measured SOM annual spread:
   Jan-25 14.09→16.92, Feb-25 7.40→10.98, Dec-24 4.01→7.50, with summer
   surrendering (Jun-25 3.71→2.49). Annual conservation is exact by
   construction (re-verified in phase 0).

**The object this addresses, measured on the keeper**
(`_nyiso150_gradient_phase0.json`): the model carries essentially no zonal
gradient — annual eqh max−min **$2.21 / $1.47 / $0.80** vs actual
**$15.73 / $9.17 / $14.83** — and in the winter event months it is FLAT
statewide while the actual downstate−upstate spread runs $11–44:

| month | model spread (CH/NYC/LI − UW) | actual spread |
|---|---|---|
| Feb-2023 | +1.6 / +1.6 / +1.6 | +33.2 / +21.8 / +43.6 |
| Dec-2024 | +0.0 / +0.2 / +1.2 | +11.0 / +13.6 / +18.1 |
| Feb-2025 | +0.0 / +0.1 / +0.4 | +27.1 / +24.7 / +24.4 |
| Jan-2025 | +2.1 / +2.2 / +2.6 | +36.8 / +44.2 / +40.6 |

The downstate annual under-pricing this cancels against upstate over-pricing:
2025 CH −9.3 % / LH −8.9 % / NYC −13.9 % / LI −17.4 % with UW +3.2 %; the
2025 miss decomposes ~60–70 % into the winter event months (Jan/Feb/Dec) and
~30 % into the summer heat-wave months (Jun/Jul), the latter being the
ledgered C3c scarcity-formation limitation seen in the monthly mean.

**What ARM W does NOT claim:** the summer half. The pre-registered adverse case
ADV-W1 is that summer downstate months worsen modestly (the construction
surrenders what winter gains); that residual is the accepted C3c model-class
limitation's face and is reported at full magnitude, never called progress.

## 2. THE ARMS

* **Control** — `nyiso150_control`: the keeper recipe replayed at HEAD, zero
  deltas. IDENT gate: byte-identity of prices to the registered keeper (max
  |Δprice| = 0 over every zone-hour of all three years) — proving HEAD drift
  is absent so each arm's delta is its mechanism.
* **ARM C′** — `nyiso150_armC`: control + `cc_reserve_duty_split=true` (one
  field). Membership artifact `reserve_duty_cc_NYISO.csv` FROZEN (rule 23,
  unchanged from nyiso-146b).
* **ARM W** — `nyiso150_armW`: control + `nyiso_iroquois_winter_spread=true`
  (one field). All inputs are committed measured series; no re-derivation.
* **COMBINED** (only if BOTH arms clear their gates) — control + both fields,
  scored on the same gates vs control; the promotion candidate per the
  nyiso-146b §GOVERNANCE convention. If exactly one clears, that arm is the
  candidate. If neither, both register as rejections and the frontier
  statement carries the outcome.

## 3. KILL GATES — ARM C′ (verbatim PREREG-nyiso146b §C.3, re-scored vs the new control)

* **C-K1 EXACTNESS** — exactly one differing field: `cc_reserve_duty_split`
  False→True.
* **C-K2 LIVENESS** — the armed cohort logs 7 plants; each of {50744, 54592,
  54593, 7784}'s model/EIA-923 ratio falls ≥80 % vs control in 2023 and 2024
  (2025 reported, preliminary vintage); an inert arm fails.
* **C-K3 NO-DEGRADE** — non-cohort CC plant-years: start-count error ≤ 1.5 ×
  control error + 5; C1 stays PASS every year.
* **C-K4 D-4/D-2 (K6′)** — zero new D-4 failures; no material class's forced
  share rises without clearing both K6′ legs; C8 PASS.
* **C-K5** — C1/C2/C3a/C3b/C4/C6/C8: no PASS→FAIL vs control; C3c reported.
* **C-K6 LOYO** — membership stability already proven derive-side (nyiso-146b);
  gate-side: C-K2 holds in 2023 and 2024 separately.

## 4. KILL GATES — ARM W

* **W-K1 EXACTNESS** — exactly one differing field:
  `nyiso_iroquois_winter_spread` False→True.
* **W-K2 CONSTRUCTION + LIVENESS** — (a) NYC monthly gas identical on/off
  (§1.1, asserted from the resolved construction); (b) annual conservation of
  each zone's measured level: |flag-on annual − measured SOM annual| on the
  reference ≤ $0.005/MMBtu (the nyiso-122 Δ=0.00000 re-verified); (c) LP
  liveness: the arm's winter-month (DJF) zone-hours move (mean |ΔLMP| in DJF
  > $1/MWh) — an inert arm fails.
* **W-K3 TARGET (the gradient/level object; gated months are the nyiso-82
  decisively-fixed three: Feb-2023, Dec-2024, Feb-2025):**
  * (a) In each gated month, the modeled downstate−UW spread for each of CH,
    NYC, LI recovers **≥30 %** of the control's spread gap to actual, and no
    gated zone-month's signed error (model−actual, eqh) lands past **+15 %**
    of its actual (overshoot kill). Jan-2025 reported, not gated (the
    Algonquin-ceiling stubbornness is known: nyiso-82 measured −18.7→−15.1 %).
  * (b) The annual eqh zonal gradient (max−min over the five zones) in 2024
    and in 2025 at least **doubles** from control toward actual and does not
    exceed actual × 1.10.
  * (c) UW-2023's annual over-pricing (+23.6 % control) strictly improves.
  * (d) ANTI-RELOCATION — in each year, the worst-zone |annual eqh error|
    does not exceed the control's worst-zone |annual eqh error| in that year.
    (The Q1 card's own warning: a candidate judged on the mean alone would
    simply relocate the error.)
* **W-K4 CONDUCT** — zero NEW failing D-1/D-2/D-4 rows; C8 PASS every year.
* **W-K5 CRITERIA** — C1/C2/C3a/C3b/C4/C8: no PASS→FAIL vs control in any
  year (C6 is attested at promotion; probe bundles report UNATTESTED as
  usual). C3c reported at full magnitude in all three years under the
  standing ledger — it is not this lever's criterion in either direction.
* **W-K6 LOYO** — derive-side vacuous (zero fitted parameters; fixed measured
  series; conservation exact). Gate-side: W-K3(a) holds in each gated month
  separately and W-K3(b) holds in 2024 and 2025 separately.
* **ADV-W1 (pre-registered adverse case, reported not gated)** — summer
  downstate months (Jun/Jul) worsen; attributed to the ledgered C3c
  scarcity-formation limitation whose silent compensation the flat
  construction was providing. Bounded by W-K5 (C3a stays in band) and
  W-K3(d).
* **ADV-W2 (pre-registered adverse case)** — UW winter months may fall too
  far once the phantom winter gas is removed (upstate separating on a binding
  CE cutset with cheap local gas). Bounded by W-K3(d) and W-K5; the UW
  monthly table is reported in full.

## 5. PREDICTIONS (falsifiable, from §1 and nyiso-82's measured A/B)

* Feb-2023 / Dec-2024 / Feb-2025 downstate spreads move decisively (nyiso-82
  system-monthly analogue recovered 68–77 %); Jan-2025 partially (ceiling).
* UW Jan-2024 (+11.7 over) and Feb-2023 (+9.3 over) shrink — the phantom
  upstate winter gas is the identified cause of both.
* 2025 system lw moves toward actual (control −8.8 %); the sign of the 2024
  move is not predicted (UW winter correction pulls down, downstate winter
  pulls up).
* Dec-2025 may over-raise (nyiso-82 measured −3.0→+7.5 % on the old keeper) —
  reported; the overshoot kill in W-K3(a) does not gate Dec-2025 but the
  anti-relocation gate W-K3(d) bounds it.

## 6. GOVERNANCE

* Rule 15: every completed solve is registered on the backcast dashboard
  whatever its outcome, in this session.
* Rule 28(b): `cc_reserve_duty_split`'s outcome is recorded on the
  `offer_curve_by_group` row's def (the nyiso-146b convention);
  `nyiso_iroquois_winter_spread`'s outcome requires the row split
  DECISION-CARD-nyiso143-iroquois-taxonomy-gap-2026-08-18.md D1 requested —
  executed in this session (own base row + a cell line in every ISO shard,
  NYISO carrying the verdict, `.` elsewhere) so the verdict has a cell to
  live in. D2 (the checker leg) stays with its governance round.
* Rule 21: zero new free parameters in either arm (frozen membership; fixed
  measured series). The DOF ledger of any promoted candidate inherits the
  149 lineage's 8 entries unchanged.
* Rule 22: training years only; the holdout spend freeze outranks everything
  and is untouched. Promotion (if any) executes the D-5(b) re-key with a
  determination re-verification; a worse determination stops and escalates.
* Rule 19: ARM W replaces the flat construction on the SAME hub-basis
  mechanism (`gas_hub_basis_overlay` + `nyiso_zonal_gas_basis`, both already
  armed) — one mechanism, its measured monthly form; nothing stacks.

## AMENDMENT 1 (disclosed before any arm solve) — the nyiso-122 refusal grounds, re-read and mapped to gates

The `gas_hub_basis_overlay` row def carries nyiso-122's ex-ante refusal of this
flag *as the C3a-2025 winter lever*, on four measured grounds. This prereg does
NOT re-litigate that refusal — the arm is run as the rule-14 measured-input
repair whose "standalone case survives untested by solve" per the same record,
under the owner round §0 describes — and each refusal ground maps to a kill
gate so the A/B cannot succeed by the refused route failing silently:

* **(a) "it cannot touch NYC"** — confirmed independently in §1.1 (NYC gas
  bit-identical). Any NYC winter improvement must come through the COUPLED
  clearing (the eastern marginal unit re-pricing the block) or not at all;
  W-K3(a) gates the NYC spread leg on the same ≥30 % bar, and if the static
  read is right and the LP agrees, that leg fails and the arm registers as a
  rejection — which is itself the decisive measurement the ex-ante read could
  not make (nyiso-82's solved A/B on the pre-CHP keeper moved winter months
  decisively; the two reads disagree BECAUSE prices move through the coupled
  marginal unit, and only a solve arbitrates).
* **(b) "it cuts Upstate-January gas by $7.48 on the one zone that is
  currently right"** — the UW-January accuracy still holds on the 149 keeper
  (−2.2 $/MWh err) and W-K3(d) (anti-relocation: no year's worst-zone error
  may worsen) plus ADV-W2 make breaking UW a kill, not a footnote.
* **(c) "it lifts December on a month already accurate"** — no longer true at
  the 149 keeper for 2025 (UW Dec-25 is +6.9 % OVER and the flag *cuts* UW
  Dec gas; LI Dec-25 is −13.9 % UNDER and the flag lifts its reference), but
  Dec-2025 stays ungated and reported, and the overshoot kill in W-K3(a)
  bounds the gated months.
* **(d) "the measured NYC−Upstate gas spread is worth only $12.75–17.00/MWh
  against a $44.28 actual premium"** — accepted: Jan-2025 is reported, not
  gated. The GATED months were chosen where the mechanism's measured reach
  covers the actual spread: Feb-25 reference−UW gas spread $7.38/MMBtu
  (≈$55/MWh at CC heat rates) vs $24–27 actual; Dec-24 $4.86 (≈$36) vs
  $11–18; Feb-23 $6.47 (≈$48) vs $22–44.

The C3a-2025 *system* consequence remains fully gated by W-K5 in both
directions, and the summer surrender by ADV-W1 + W-K3(d).

## 7. REPRODUCTION

```
python3 scripts/probes/_nyiso150_gradient_phase0.py
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso149_armF --out-dir results/calibration/nyiso150_control
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso150_armC_recipe --out-dir results/calibration/nyiso150_armC
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso150_armW_recipe --out-dir results/calibration/nyiso150_armW
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso150_arm{C,W} --iso NYISO --years 2023 2024 2025
python3 scripts/probes/_nyiso150_ab_gates.py
```
