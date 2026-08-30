# PREREG nyiso-159 — `nyiso_zonal_loss_surface`: the NYISO test of the shared marginal delivery-factor loss row, identified from NYISO's own posted components, zero fitted scalars

**Filed and blob-verified BEFORE any solve, before the mechanism is armed in
any run** (the nyiso-115/117/119 discipline). Phase-0 evidence:
`FINDING-nyiso159-loss-surface-phase0-2026-08-30.md` +
`_nyiso159_loss_phase0.json` (committed alongside this prereg, same
pre-solve commit).

**Charter.** nyiso-159 handoff step 1c on the phase-0 MATERIAL verdict. The
matrix row `zonal_loss_surface` exists (PJM **K** — pjm-136 keeper; CAISO
variant construction — caiso-164; MISO **R** by its own market's data);
NYISO's cell is `·`, never adjudicated. Rule 25/28(d): NOTHING transfers
across the boundary but the estimator's algebra — every parameter below is
derived from NYISO's own published component record. Off the nyiso-145 queue
with stated cause (handoff): every determination-moving queue item is
owner-court (Leg 2 AORR intake, CC cycling-cost id, hydro AS certification)
or ledgered (C3c); this lane addresses the C3a annual-gradient face with
measured physics under an existing cross-ISO construction.

**Keeper / baseline:** `2026-08-30-nyiso-157-par-attribution` (bundle
`results/calibration/nyiso157_pararm_B`), NOT-YET on {C3a −12.0 % (2025),
C3b 0.203 (2025), C3c ledgered}. C3a-2023 +1.0, C3a-2024 −2.0 (both in
band).

---

## §1 The mechanism (xiso pattern: per-ISO field on the shared row, NO new row)

`ScenarioConfig.nyiso_zonal_loss_surface: bool = False` — default off,
byte-identical off, registered at introduction in
`_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` /
`TIER_TAGS` (tier 3) so the pinned default cache key never moves.

When True for NYISO in either mode:

1. **Topology split** (`interchange.nyiso.apply_nyiso_zonal_loss_links`, step
   10 of the `interchange/spec.py` transform ladder, after every other
   transform): each of the four internal chain links
   (UW↔CH, CH↔LH, LH↔NYC, NYC↔LI) becomes a one-way pair
   (`is_bidirectional=False`, same TTC each way), each direction charged the
   `NYISO_LOSS_LINK_TIEBREAK_EPS = 1e-3` flow cost — the storage-ε numerical
   device (rule 9 class), identical in construction and value to the PJM and
   CAISO tiebreaks, declared in NYISO's own module (rule 25). Import
   generators, seam mechanisms (`nyiso_seam_par_attribution` armed,
   `nyiso_seam_deliverability_envelope` armed-but-shadowed) and every
   interface/TSL cap are untouched — losses apply to INTERNAL links only,
   the same exclusion PJM's star node and CAISO's WECC nodes carry.
2. **Loss fractions** (`interchange.nyiso.build_nyiso_link_loss`): per
   one-way internal link x→y and month m,
   `eps_(x→y),m = max(0, (dev_y,m − dev_x,m) / (1 + dev_y,m))`, expanded to
   hours on the model's fixed non-leap calendar and passed as
   `link_loss` into the energy balance (`rows.py` link_loss: receiving zone
   gains `(1 − eps) × flow`). The reverse direction clamps to 0 for the
   month; a sign-flipped month would swap the lossy direction automatically
   (phase-0: no NYISO month flips — the gradient is monotone UW<CH<LH<NYC<LI
   in 36/36 months).
3. **Prices stay LP duals** (rule 4): an interior uncongested flow x→y prices
   the receiving zone at `λ_y = λ_x × (1+dev_y,m)/(1+dev_x,m)` — the measured
   marginal delivery-factor ratio NYISO's own LBMPs carry
   (`LBMP = E + MCL − MCC`, NYISO MST / Manual 12; identity verified to
   $0.009 on all 36 months, phase-0 §1). No price adder anywhere.

## §2 Identification (the derive; frozen on filing, rule 23)

`scripts/data/derive_nyiso_loss_surface.py` →
`data/raw/iso-specific-transmission/NYISO_loss_surface.csv`
(columns `iso,zone,year,month,df_deviation,n_hours,interpolated` — the shared
loader `data.loss_surface.load_zone_month_deviation` resolves NYISO
generically; `_DERIVE_SCRIPT` gains the NYISO entry).

* **Estimator:** `dev_z,m = Σ_h MCL_z,h / Σ_h E_h` over the month's hours —
  the frozen MISO/PJM/CAISO estimator, on NYISO's own posted components ONLY.
  Never the price residual, never a model output.
* **Source:** `data/clean/lmp/NYISO/RTM/lmp_<yr>.parquet` (the curated MIS
  P-24A record intaken this session; regeneration =
  `fetch_nyiso_zonal_lmp.py --kind rt` → `curate_lmp.py` → derive).
* **Basis: REAL-TIME — a declared, deliberate divergence from CAISO's DA
  basis.** NYISO's scored C3a/C3b target is the RT LW price; the committed
  component contract series is RT; and NYISO's RTD/RTC is a full-network
  optimization whose posted MCL is the marginal-loss object itself. (PJM/
  CAISO derive from their DA records for their own stated reasons; per-ISO
  identification is per-ISO, rule 25.)
* **Zone aggregation:** model zone = SIMPLE MEAN of member A–K zones —
  `derive_actual_lmp.NYISO_ZONE_MAP` / `nyiso_zone_hourly`, the SAME
  convention the scoring actuals use, so the surface and the target measure
  one representation. Declared crosswalk: UW={WEST,GENESE,CENTRL,NORTH,
  MHK VL}, CH={CAPITL}, LH={HUD VL,MILLWD,DUNWOD}, NYC={N.Y.C.},
  LI={LONGIL}.
* **Rows:** per-year rows for 2023/2024/2025 (a backcast train year consumes
  its own year's measured surface — the CEMS-rate admissibility class,
  rule 13: regenerates for any year from the same public feed, responds to
  changed grid conditions) + pooled `year=0` rows over the train years (the
  forecast-mode forward analogue). Guards mirrored from the CAISO derive:
  `MIN_HOURS_PER_YEAR = 8000`; monthly `ΣE > 0` asserted; E-uniformity
  asserted at the CAISO `MCE_IDENTITY_TOL` class bound (measured p99
  $0.0075).
* **ZERO free parameters.** No threshold, weight, or scalar new to this
  mechanism; the DOF ledger's `n_residual` stays 6.

## §3 Acceptance gate (offline, BEFORE any solve is spent)

`derive_nyiso_loss_surface.py --acceptance`: for each of the four adjacent
chain pairs × three years (12 pair-years), the dual-ratio separation the
surface implies at the measured E — `Σ_m h_m·E_m·((1+dev_y,m)/(1+dev_x,m)−1)
/ Σ_m h_m` — must sit in the miso-76 B1 band **[0.5×, 1.5×] of the measured
mean ΔMCL** for that pair-year. **All 12 in band is the precondition to
solve; any miss is a stop-the-line** → file the finding, spend no solve.
(This validates the derive→eps→ratio→$ algebra offline; the LP A/B is the
real test.)

## §4 The A/B (single-delta channel, rule 12)

```
# control (zero-delta replay of the current keeper recipe at this HEAD)
python3 scripts/replay_keeper.py results/calibration/nyiso157_pararm_B \
  --out-dir results/calibration/nyiso159_lossctl_A \
  --note "nyiso-159 control: zero-delta replay of 2026-08-30-nyiso-157-par-attribution at HEAD"

# arm (single delta)
python3 scripts/replay_keeper.py results/calibration/nyiso157_pararm_B \
  --out-dir results/calibration/nyiso159_lossarm_B \
  --set nyiso_zonal_loss_surface=true \
  --note "nyiso-159 arm: + nyiso_zonal_loss_surface (PREREG-nyiso159; measured NYISO delivery-factor surface, zero fitted scalars)"
```

Concurrent invocations, years 2023 2024 2025 sequential within each
(rule 12). Freeze ACTIVE: no other year, no `--holdout-authorized`. **Both
runs register whatever the outcome** (rule 15), matrix cell updated
in-session (rule 28(b)), rejections included.

## §5 Gates (pass/fail written before results exist)

* **K2 — feasibility:** zero slack, zero dump, both arms, all years (losses
  consume real MWh; the fleet must cover them without scarcity artifacts).
* **K5 — off-state byte-identity:** flag-off build path unchanged (unit
  test + the control run IS the off state at HEAD).
* **K6 — control reproduction:** control C3a per year within ±0.2 pp of the
  keeper's **+1.0 / −2.0 / −12.0 %**. (G1 drift class reported, not gated.)
* **P1 — measured-loss reproduction (the mechanism does what the physics
  says, no more):** per adjacent pair-year, the ARM−CONTROL annual mean
  zonal-dual spread delta within **[0.5×, 1.5×] of the measured mean ΔMCL**
  for that pair-year. 12 pair-years; pass = ≥ 10/12 in band with NO miss
  below 0.25× or above 2.0× (the pjm-136 P1 edge-miss precedent, tightened
  with an outer floor/ceiling); else FAIL.
* **W-K3d — no upstate relocation:** |arm − control| Upstate_West annual
  mean dual ≤ $0.75/MWh every year.
* **Adverse band (named):** arm C3a-2023 stays ≤ +10 % (phase-0 worst-case
  push +3.3 pp from +1.0 leaves ≥ 5.7 pp margin — a breach means the
  mechanism moved MORE than the measured premium and is a stop);
  C3a-2024 stays in ±10 likewise.
* **C3c:** arm-vs-control deltas ONLY (nyiso-137 clock caveat); no absolute
  band claim; the ledgered queue stays CLOSED.
* **LOYO consistency:** the surface pools nothing across backcast years —
  each year consumes its own measured rows — so the LOYO form is P1 holding
  in each year separately; a year where it breaks indicts the identification
  (stop), never a re-tune.

## §6 Honest P3 (what this lever is predicted to do, and what it is not)

The loss surface restores a measured FLOOR component: predicted arm−control
LW annual +$0.6–1.1 (2023) / +$0.9–1.6 (2024) / +$1.5–2.5 (2025), i.e.
C3a-2025 −12.0 → ≈ −8.2 to −9.7 % (may re-enter the ±10 band), C3b-2025
0.203 → ≈ 0.16–0.19 by upper-bound arithmetic. **It is NOT predicted to
close the winter or summer faces**, where congestion dominates ($16–35 of
the $13–44 face spreads); the object months stay routed to Leg 2 (winter)
and the ledgered C3c (summer) exactly as nyiso-158 adjudicated. A promotion
case, if any, rests on rule 1/14 grounds — the mechanism is real measured
physics the lossless LP omits — never on the score alone.

## §7 Escalation and authority

Any determination change is **D-5(b)-escalated** (re-verify the `complete`
entry only if NYISO held one — it does not; the determination text change
itself goes to the owner): a worse re-verified determination stops and
escalates. `audit_keepers` E11 binds any promotion. **THE OWNER RULES on
promotion; this session promotes nothing on its own.** Leg 2 outranks this
lane if the MyNYISO AORR files land in-session (INTAKE-SPEC-nyiso156 §2
identifiability gate first, fail-closed).
