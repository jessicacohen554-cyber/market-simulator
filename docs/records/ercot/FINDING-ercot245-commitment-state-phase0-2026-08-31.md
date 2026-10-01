# FINDING — ercot-245 (2026-08-31): the PER-CLASS commitment-state (slow-start reachability) bound is KILLED AT CENSUS — K-A fires on ST (the SCED GS* restype universe cannot express the model's ST_GAS class), K-C fires in BOTH scored years on all three legs (the transferred grain binds 8760/8760 hours, NUC saturated at mass 1.0 and CC ordinary-bound 3,300–4,272 hours vs bar 150), and K-T fires on both gas classes (T-1 CC 0.1935 / ST 0.1849 vs 0.15; T-2 p95 overshoot 3.2/4.1 GW vs 2 GW) — the charter's named kill decomposition lands on BOTH residues: the class-share FORM over-fires a composition-correct keeper exactly as the K-C prior warned, and the 2023-identified transfer does not transport for the classes that matter, so per-class forward-regime identification is blocked on the 2024/2025 all-resource SCED corpus intake (§4, the owner's decision)

**Session ercot-245 (relaunch), branch
`claude/ercot-245-phase0-census-0f5d8h`. ZERO-SOLVE** — every number below
is read from the FORWARD keeper's committed sidecars
(`results/calibration/ercot234_eastex_identity`), the committed actuals,
the EIA-930 wide extract, the measured ORDC/reserves series, the
delivery-2023 all-resource NP3-965 SCED corpus (323 shards scanned), the
2025 tail-day extract (11/11 days parsed, 0 excluded), and a
fidelity-guarded no-LP fleet reconstruction. Precommit
`docs/PRECOMMIT-ercot245-commitment-state-phase0-2026-08-30.md` (with
Amendment 1, the V-0(d) storage-excluded level leg) pushed + blob-verified
BEFORE any measurement; probe
`scripts/probes/ercot245_commitment_state_phase0.py` →
`results/calibration/ercot245_commitment_state_phase0.json` (committed,
blob-verified). **The Phase-1 A/B license is NOT spent** — no lever, no
solve, no ScenarioConfig change, no matrix verdict move; the two-config
keeper untouched. Kills graded exactly as declared: ANY kill ⇒ record and
STOP.

## 0. Verdict in seven lines

1. **K-A fires — construction invalidity, ST only.** F_ST > CAP_ST^meas in
   **26.1 %** of covered 2023 hours (bar 25 %) at the direct measured
   grain, and **30.3 %** of covered 2025 extract-day hours. Per the
   precommit's own declaration this cannot be conduct (the model's class
   energy passes C1 in all three years): the SCED restype universe
   {GSREH, GSNONR, GSSUP} is mis-scoped against the model's ST_GAS class.
   The universe anchor agrees in direction: ST is the ONLY class whose
   measured available universe is SMALLER than the model's (ratio 0.874;
   CC 1.265, COAL 1.186, NUC 1.040, all inside band) — gas-steam
   capability the model carries as ST_GAS is not visible under the GS*
   restypes at the train grain.
2. **K-C fires in both scored years, on all three legs, at saturation.**
   The transferred grain binds the union in **8,760 of 8,760 hours** both
   years — 8,676 / 8,692 ordinary (bar 150), ordinary > missed by
   8,676:36 / 8,692:31, away-binds 6,798 / 6,260 (> ⅓). Two independent
   components: (a) **NUC binds every hour at mass 1.0** — a FORM artifact:
   the model dispatches nuclear at its availability bound (spare ≡ 0), so
   ANY share c < 1 (measured c_NUC 0.962–0.991) binds a baseload class
   permanently, at depth p50 102–184 MW; (b) **the kill survives NUC's
   exclusion** — CC alone binds 3,363 / 4,333 hours (mass 0.384 / 0.495),
   of which 3,300 / 4,272 ordinary, depth p50 1.2–1.8 GW. The standing
   ercot-244 §2.3 measurement (model slow+held above the measured online
   total in ~11 % of forward-span hours) concentrates per-class exactly as
   the precommit's K-C prior warned: **the kill firing IS the verdict —
   the instrument-form is wrong for the object, not a tuning invitation.**
3. **K-T fires — the 2023-identified transfer does not transport, and it
   fails on exactly the classes that matter.** T-1 (extract-day level):
   CC median rel err **0.1935**, ST **0.1849** vs the 0.15 band (COAL
   0.0574, NUC 0.0546 pass). T-2 (aggregate containment): frac_over
   passes (1.02 % / 0.65 % vs 5 %) but p95 overshoot **3,249 / 4,096 MW**
   vs 2,000. T-3 PASSES (bind agreement 0.9565 on 23/31 covered M_2025
   hours) — the direct and transferred grains agree about the missed set;
   they disagree about the level everywhere else.
4. **K-B does NOT fire — but its no-fire is VACUOUS and is not claimed as
   reach.** The union reach at M is 36/36 and 31/31 only because NUC binds
   all 8,760 hours; a union containing every hour contains every missed
   hour. The honest per-class reads: CC 29/36 and 29/31, ST 19/12, COAL
   18/19 — real reach at M, but attached to 3,300–4,272 ordinary CC binds,
   i.e. base-rate binding, not discrimination.
5. **Every V-0 anchor passed**, Amendment 1's re-declared (d) included:
   populations exact (22/1 model tails, 53/31 actual, 36/31/115 missed);
   EIA-930 lag-0 (corr 0.9996+); rtolhsl evening means to the hundredth;
   corpus reconciliation corr **0.9935** with storage-excluded median gap
   **+2,371 MW** (raw +4,948 MW; storage online HSL mean 2,676 MW —
   committed as the series-composition record); CC cap_ref **35.260 GW**
   vs the committed ercot-163 35.2601 (dev 0.003 %); extract 11/11 days,
   M_2025 coverage 23/31 ≥ 16 so T-3 was gradeable. All four universe
   anchors inside [0.80, 1.60].
6. **The census leaves behind two REALITY-SIDE measurements that outlive
   the kill** (§2): at the covered missed events the model's slow
   composition is skewed — ~3 GW MORE gas-steam and ~4 GW LESS CC online
   than ERCOT's measured mix — and (D-V5) reality's per-class online
   shares at events are statistically indistinguishable from same-net-load
   ordinary hours (CC 0.805 vs 0.807, ST 0.553 vs 0.589, COAL 0.715 vs
   0.737, NUC 0.966 vs 0.982), so **no net-load-conditioned class-share
   bound — however identified — carries an event-discriminating signal.**
7. **Disposition per the precommit's kill rule: record and STOP.** No
   Phase-1 precommit, no A/B, nothing armed, no solve. Matrix: evidence
   notes appended to the §5.1 item-9 card and the
   `energy_online_capability_cap` cell (verdict **R** unchanged — the
   note-append precedent); calibration-log entry ercot-245; the forward
   span's ledgered C3c (2024 22/53, 2025 1/31) is carried at full
   magnitude, un-repaired by this lane.

## 1. The census record (full detail in the committed JSON)

Transferred grain (ĈAP_k = c_k(nl-bin) × AvailModel_k, scored years):

| measure | 2024 | 2025 |
|---|---|---|
| missed set \|M\| | 36 | 31 |
| union binds \|B∪\| | **8,760** | **8,760** |
| B∪ ∩ M (reach) | 36 (1.00, vacuous) | 31 (1.00, vacuous) |
| B∪ ∩ hit | 17 | 0 |
| B∪ ∩ ordinary (actual < $150) | **8,676** | **8,692** |
| away-binds (model_dw ≥ actual) | 6,798 | 6,260 |
| CC binds / ordinary / mass | 3,363 / 3,300 / 0.384 | 4,333 / 4,272 / 0.495 |
| ST binds / ordinary / mass | 1,242 / 1,198 / 0.142 | 544 / 515 / 0.062 |
| COAL binds / ordinary / mass | 418 / 373 / 0.048 | 2,125 / 2,087 / 0.243 |
| NUC binds / mass | 8,760 / **1.000** | 8,760 / **1.000** |
| CC depth p50 at M / ordinary (MW) | 1,978 / 1,756 | 1,571 / 1,204 |

Direct grains (F_k vs CAP_k^meas): **2023** (D-V3, DIAGNOSTIC-ONLY — the
miscalibrated-year caveat: C3a-2023 −39.7 % on this bundle): union 2,979
binds — 115/115 missed, 66 hit, 2,757 ordinary, away 1,814; ST dominates
(2,286 binds, mass **0.261** = the K-A trip; CC 34 / COAL 202 / NUC 749,
all under bar). **2025 extract days** (264 covered hours): union 111 binds
— 22/23 covered missed (0.9565), 82 ordinary; the binding classes are ST
(80, mass 0.303) and COAL (51, mass 0.193); **CC and NUC bind ZERO
extract-day hours at the direct measured grain.** Identified shares c_k
(10 net-load deciles, 2023): CC 0.404→0.875, ST 0.078→0.914, COAL
0.766→0.948, NUC 0.989→0.962 (note NUC's share *declines* with net load).

Disclosed variants: D-V1 (held-attributed) and D-V2 (class-whole/CHP)
reproduce the primary union numbers identically in both years — a union
already at 8,760 hours cannot move in either direction, so neither
loosening nor tightening the F side changes the shape (the invariance leg
of the ercot-244 precedent, reproduced at this grain).

## 2. The structural evidence — what the per-class grain could see that the aggregate could not, and why the instrument still dies

1. **The compositional skew at events is REAL and now measured** (D-V4, 23
   covered M_2025 hours, e.g. h342 = 2025-01-15 18:00 CST, actual $306.04
   vs model $43.60): model ST_GAS F 4,283 MW vs measured ST online
   **1,236 MW** (reality's gas-steam fleet ~88 % cold); model CC F
   23,872 MW vs measured CC online **28,029 MW** (spare 1,198 MW). The
   model meets the same net load slow-heavy in ST/COAL and lean in CC
   relative to reality's committed mix. This is the per-class
   decomposition of ercot-244's aggregate finding — the aggregate summed
   these opposite-signed skews to "model under the total ceiling at 33/36
   and 28/31 missed hours" and could grab nothing; the class grain sees
   both sides.
2. **But reality carries NO event-conditional class-share signal for a
   bound to express** (D-V5): at the covered missed events, ERCOT's
   per-class online share of cap_ref is within 0.4–3.6 pp of the SAME
   net-load bins' ordinary hours — and slightly LOWER, not higher, in
   every class. The commitment share is set by net load, not by event-ness.
   A share bound conditioned on net load (this instrument, and any
   admissible refinement of it) therefore binds events and same-bin
   ordinary hours identically — which is exactly the measured K-C
   signature: reach at M rides on ~40 % base-rate binding, and the
   discrimination the C3c object needs (why THIS tight hour cleared $300
   and THAT one $40) lives in price formation over the online cushion,
   not in the class-grain online share.
3. **The baseload face of the form defect** (NUC mass 1.0): a share bound
   built as c × the model's own availability-derated capability
   permanently binds any class the model dispatches AT its availability
   bound whenever c < 1 — for nuclear a 1–4 % haircut (c 0.962–0.991,
   the measured online-HSL-below-p98-cap_ref gap) becomes an 8,760-hour
   102–184 MW clamp. On a composition-correct keeper this repriced-nothing
   artifact would still enter the LP's arithmetic in every hour of the
   year — indefensible under `[R-FLOOR-WINDOW]`, caught zero-solve.
4. **The transfer face** (K-T): the 2023-identified deciles miss the 2025
   extract-day level by 18–19 % at the median for CC and ST — the two
   classes that carry the object — while COAL/NUC transport within 6 %.
   The gas classes' commitment shares moved between 2023 and 2025 in ways
   a net-load bin index does not carry (fleet turnover, the 2024-08-01
   ECRS reform, RTC+B-era conduct). The precommit's §2d honesty clause
   fires as designed: "if commitment has memory/dynamics this form cannot
   express, the transfer validation fails HONESTLY and the lane records
   it."

## 3. The kill-decomposition adjudication (the charter's K-E question, answered for the K-A-clean classes)

K-E's formal premise (no K-A) fails — ST's construction is invalid at this
measured grain. For the three K-A-clean classes (CC, COAL, NUC) the
reach/window/transfer kills still fired, and the decomposition the charter
demands is adjudicated on the record above: **BOTH residues are
established.**

* **(form)** — a net-load-conditioned availability-shaped CLASS-share
  bound mis-expresses the object on a composition-correct keeper: it
  saturates baseload (§2.3), binds the mid-merit classes at 38–49 %
  base rate with ordinary hours outnumbering missed ~120:1 (§1), and the
  reality-side D-V5 null shows the event-discriminating signal it would
  need does not exist at this grain in ERCOT's own conduct. This extends
  the ercot-244 adjudication one grain down: neither the aggregate NOR the
  class grain of a pure-LP availability-shaped share bound expresses
  headroom-price reachability. What discriminates events in reality is
  which UNITS are where in their startup/notice cycle and what the online
  cushion prices at — per-unit state and price formation, not class
  occupancy shares.
* **(grain/identification)** — the direct extract-day census (the honest
  measured grain) DOES discriminate better than any transferred form:
  22/23 reach at M with 82/264 ordinary binds, and the D-V4 skew is real.
  A per-unit forward-regime representation might express what the class
  share cannot — but its identification basis does not exist on disk: the
  delivery-2023 corpus identifies the wrong regime (T-1/T-2 measured that
  directly), and the 11-day 2025 extract is validation-scale, not
  identification-scale. **That is the §4 owner flag, verbatim from the
  charter.**

## 4. Owner-visible flags (not executed, per charter §8)

1. **The 2024/2025 all-resource SCED conduct corpus intake**
   (PRECOMMIT-ercot242 §6) is named as THE identification unblock — K-T
   fired on the forward-span transfer, and the §3 grain adjudication
   lands on per-unit forward-regime state as the only residue a future
   instrument could express. The decision is the owner's; the three
   gitignored probe-day extracts are re-fetch-only and were NOT fetched.
   **Qualification this census adds:** the D-V5 null means the intake
   would buy per-UNIT state identification (startup/notice cycles,
   which-cold-unit-when), not a better class-share table — a class-grain
   re-identification on 2024/2025 data would inherit the same form
   defects measured here (§2.2–2.3).
2. The D-V4 per-class composition skew at events (model ST-heavy /
   CC-lean vs reality's committed mix, opposite signs summing to the
   ercot-244 aggregate under-ceiling) is a standing structural
   observation about the current keeper, recorded for any future owner
   charter; no lane owns it today.

## 5. Implementation notes (precommit §7 amendment convention — constructions unchanged)

1. The bundle fleet carries nuclear units with an EMPTY `plant_group`;
   their selector is `fuel_type == "nuclear"` (recorded in the probe
   source at the `avail_model` construction; the construction — the
   model's nuclear pmax × availability — is unchanged).
2. The probe env was recreated after the original session's container was
   lost: same pins (python 3.11.15, pandas 3.0.5, pyarrow 25.0.1, numpy
   2.4.6), venv outside the project dir (`/home/user/ercot245-venv` vs
   the docstring's `/root/ercot245-venv` path).
3. The two RTC+B-era extract days (12-01, 12-15) parsed cleanly under the
   declared per-day column-completeness gate — 0 days excluded, so the
   declared coverage seam never engaged.

## 6. Hygiene

Zero-solve; the Phase-1 A/B license NOT spent; reads ⊂ {2023, 2024,
2025}; no `--holdout-authorized`; the holdout freeze untouched; ERCOT
surfaces only (rule 25); no run produced (rule 15 not triggered — nothing
to register); zero fitted scalars anywhere in the construction (10
ratio-of-sums bin shares, declared ex ante); the ercot-244 DO-NOT-REDO
honoured (no aggregate-RHS variant touched — the aggregate series appears
only as T-2's declared containment reference); the ercot-163 refutation
distinguished per §0.2 of the precommit, not re-litigated; §0 standing
verdicts respected; every deliverable pushed on the designated branch with
blob verification on ≥300-line files; no workflows, no CI solves.
