# FINDING miso-113 — regulated-PRB committed-run NIGHT-LEVEL floor (C7 amplitude lane)

Session miso-113, 2026-08-01, branch `claude/miso-113-coal-prb-floor-wtd8kl`,
off `origin/main` at `b948805` (miso-112 merged as PR #3250, so this branch
carries its artifacts). Pre-registration committed BEFORE the ex-ante
measurement and before any mechanism code (`554e71d`):
`results/calibration/PREREG-miso113-prb-night-floor-2026-08-01.md`.

## 0. Verdict

**REJECTED on pre-registered guards G1 and G4. Keeper
`2026-07-31-miso-109b-hy-level` stays.** The floor does exactly what it was
built to do — it relocates the regulated PRB fleet onto its measured night
level, per plant, in all three years (**G6 PASS**, the gate miso-112 said
would decide the lane) — and that turns out **not** to be what C7 needs. The
shape gate moves the **wrong way** in the two years it had to clear.

**The lane the PREREG opened is CLOSED, and with it the whole
regulated-PRB self-commitment family**: offer-side both ways (miso-111
whole-band, miso-112 per-plant split) and now floor-side. §4 states why the
inference that named this successor was wrong, and §5 says what that leaves.

## 1. The mechanism as built

`coal_prb_night_floor` (ScenarioConfig, default off; registered in
`_CACHE_KEY_OPTIONAL_FIELDS`, so the default key is unmoved at
`0e9fce2fb55b889f`). The repo's existing P1-native P0-detected-run →
`min_gen` construction — the CAISO RA must-offer / ERCOT / NYISO gas-bridge
family, injected at the P0→P1 seam, **no P2 pass** — routed onto regulated
PRB coal:

- **Detector** `model.commitment.coal_selfcommit_night_min_gen`; seam hook
  `pipeline.commitment.build_coal_night_floor_p1_prep`.
- **Level** each plant's MEASURED `night_p50` from the frozen miso-112
  artifact, **not re-derived** (rule 23).
- **Placement** incremental floor `max(0, night_p50 − pct_mr/100) ×
  nameplate`, spread at assembly across the plant's tranches in FILL order
  with `_mustrun` counted at its full capacity, so `mustrun + floor ==
  night_p50 × nameplate` wherever the floor is positive.
- **Window** the plant's own P0-detected committed run and nothing else.
- Zero fitted parameters. Rule 19 mutual exclusivity with both offer-side
  forms enforced in `__post_init__` and again at the single-`p1_fleet_prep`
  seam. D-2 id `MECH_COAL_SELFCOMMIT_NIGHT` (22) with its cited `D4_WINDOWS`
  entry and ablation registration added in this session (rule 20).

## 2. Phase 1 — the ex-ante inertness check (kill rule did not fire)

miso-111 PREREG §8 retired the bridge form as "provably inert". That verdict
was reached on the **LSL** statistic (plant-basis loading-when-on p5 =
0.182), which sits below every plant's `_mustrun` band. The PREREG required
the argument be **re-run at the night level, not quoted**
(`scripts/probes/_miso113_floor_inertness.py`,
`results/calibration/miso113_floor_inertness.txt`):

- **18 of 26** regulated PRB plants carry a non-zero incremental floor,
  covering **69.2 %** of regulated-PRB nameplate (17,956 of 25,942 MW) —
  against a pre-registered kill at <5 plants or <5 % of capacity.
- Total incremental floor **4,274 MW**; cap-weighted `night_p50` **0.4446**
  against a `_mustrun` band of **0.3013**.
- **911 MW on 12 plants spills past `_committed` into `_econ`**, so the
  fill-order spread is load-bearing, not cosmetic.

The runtime fleet build reproduces the probe exactly (37 floored tranche
rows / 18 plants / 4,274 MW; 3,363 MW on `_committed`, 911 MW on
`econc00/01/02`), so the CSV-basis readout IS the runtime basis. **The
mechanism is not inert, and the miso-111 argument genuinely does not
transfer to this statistic.**

## 3. Phase 2 — the A/B

Arms, each 2023+2024+2025 in ONE bundle (rule 16), years chained sequentially
(rule 12) via `scripts/probes/_miso113_chain.sh`:

- **A (control)** `results/calibration/miso113_control_A` →
  `2026-08-01-miso-113a-control`
- **B (arm)** `results/calibration/miso113_nightfloor_B` →
  `2026-08-01-miso-113b-prb-night` (A + `coal_prb_night_floor=true`)

**Control integrity.** Arm A reproduces the committed 109b keeper at
**L1 0.00000 %** in 2023 and 2024 (max class-hour |diff| 0.0000 MW) and
carries **0.03007 %** in 2025 — *the identical figure miso-112 measured*,
with COAL_PRB's D-1 statistics reproduced exactly (cv_ratio 0.466 / 0.475 /
0.314, profile_r 0.988 / 0.978 / 0.971). Cross-session agreement on the
drift confirms it is a pre-existing HEAD effect, not this session's. Every
arm-B movement is attributable to the single flag.

**The mechanism fired** (it did not in the first attempt — §6): 223,130 /
216,702 / 243,402 unit-hours floored, **20.12 / 19.78 / 21.93 TWh of floor
volume**, 37 plant-tranches, in 237 / 199 / 229 committed blocks of which
**209 / 162 / 198 are longer than 72 h** — the baseload committed-run window
the rule-17 declaration claims, with no clock-hour banding.

### 3.1 Results

**D-1 COAL_PRB (the C7 gate), A → B:**

| year | profile_r | model off-peak CV | actual | cv_ratio | verdict |
|---|---|---|---|---|---|
| 2023 | 0.988 → 0.985 | 0.072 → 0.071 | 0.155 | **0.466 → 0.460** | FAIL → FAIL (**worse**) |
| 2024 | 0.978 → 0.968 | 0.058 → 0.051 | 0.121 | **0.475 → 0.420** | FAIL → FAIL (**worse**) |
| 2025 | 0.971 → 0.972 | 0.023 → 0.026 | 0.074 | **0.314 → 0.357** | FAIL → FAIL (better) |

**C-series, arm B:** C1 **16/16 (free 12/12)** every year — the gate that
killed both predecessors PASSES here. C2 PASS. C4 PASS. C8 PASS. C3a
**regresses** (2025 −14.2 % → −15.8 %) and **C3b flips PASS → FAIL** (2025
NRMSE 0.200). C3c unchanged. COAL_BIT untouched (cv_ratio 0.719/0.600/1.120
→ 0.709/0.544/1.197, profile_r within 0.003).

**COAL_PRB volume, A → B:** 123.69 → 122.45 (−1.24), 118.33 → 117.86
(−0.47), 147.14 → 145.62 (−1.51) TWh.

### 3.2 Guard readout

| guard | result |
|---|---|
| G1 C7 2023+2024 ≥ 0.5 | **FAIL** — 0.460 / 0.420, both *below* the control |
| G2 C1 16/16 every year | **PASS** (free 12/12) |
| G3 COAL_BIT ≤ 2.0, r within 0.05 | PASS |
| G4 C3a/C3b/C3c no regression | **FAIL** — C3a 2025 −14.2 → −15.8 %; C3b PASS → FAIL |
| G5 forced share ≤ 30 %, D-4 off-window ≤ 5 % | PASS — `coal_selfcommit_night` forced **2.0 / 3.9 / 0.8 %** (COAL total 2.3 / 4.3 / 1.0 %); D-4 **0.0 %** off-window all years |
| G6 night level toward the meter | **PASS** — see §4 |

**The pre-registered G2 direction prediction was WRONG and is recorded as
such.** §6 of the PREREG argued the floor would push volume UP (+2 to +5 TWh)
against the +8 ceiling, inverting the predecessors' risk. Volume moved
DOWN by 0.5–1.5 TWh: the floor forces PRB on in the plant's cheapest hours,
which depresses the clearing price (2025 mean $38.01 → $37.24), and the
price effect costs PRB slightly more economic dispatch elsewhere than the
floor forces. The guard passed for a reason the prediction did not contain.

## 4. Why it fails — G6 passes and the gate still moves backwards

The PREREG promoted miso-112 §4's structural test to a first-class gate
precisely so the arm could not "pass C7 by overshooting the level". It is
the reverse that happened. Reproducing that construction with the artifact's
**measured `hsl_mw`** as the shared denominator (recovering miso-112's own
numbers to ~0.005 — control 0.488 / 0.444 against their 0.483 / 0.437):

| year | MEASURED | control | arm | cap-wtd abs error |
|---|---|---|---|---|
| 2023 | 0.437 | 0.488 | 0.485 | 0.121 → **0.108** |
| 2024 | 0.438 | 0.444 | 0.461 | 0.108 → **0.089** |
| 2025 | 0.438 | 0.563 | 0.553 | 0.141 → **0.133** |

**The floor works.** Per-plant capacity-weighted error to each plant's own
meter falls in every year — 18 % better in 2024 — and unlike the miso-112
split, which drove the level *below* the meter, this arm never crosses it.
This is the structural claim the mechanism was built on, and it is
**confirmed**.

And the C7 gate still moves backwards, for a reason that is now arithmetic
rather than interpretation:

1. **The keeper already sits ABOVE the measured night level** (0.488 / 0.444
   / 0.563 vs 0.437 / 0.438 / 0.438). miso-112 §4 established this; what it
   did not draw out is the consequence for a floor. A floor placed at a
   level the model is already above is **slack in most hours by
   construction**: of 20.12 / 19.78 / 21.93 TWh of floor volume, only
   **3.46 / 6.53 / 1.72 TWh** is actually dispatched at a binding floor.
   82 / 67 / 92 % of the floor never binds.
2. **Where it does bind, it binds in exactly the wrong hours.** The only
   hours a slack floor reaches are the model's *cheapest* — the hours the
   fleet does back down. Those hours are the entire source of the model's
   (already too small) off-peak variability. Clipping them lowers model
   off-peak CV (0.072 → 0.071, 0.058 → 0.051) against an actual of 0.155 /
   0.121 that the model must move **toward**, not away from.

So a floor cannot fix C7 on this fleet **in principle, not by tuning**: C7's
failure is that the model's overnight distribution is too NARROW, and a
lower bound can only narrow a distribution further. miso-112 §5's inference —
"the missing object is a floor, not a second price" — was right that the
level needed holding and wrong that holding it addresses the amplitude. The
two structural statistics are **decoupled**: this arm improves the level and
degrades the amplitude, the mirror image of the split, which bought
amplitude by breaking the level.

Under rule 1 the owner's structural-fidelity grant was weighed against this
measurement, as in miso-112, and does not apply: the arm improves one
structural statistic while degrading another (C7 amplitude) *and* two price
criteria (C3a, C3b). It is not "structurally better with worse gates".
**Not promoted.**

## 5. What this closes, and what it leaves

**CLOSED — the entire regulated-PRB self-commitment mechanism family**, all
three admissible forms, each on its own pre-registered guards:

| form | session | cell | why |
|---|---|---|---|
| whole-band repricing | miso-111 | R | C1 −8.77 / −14.97 TWh |
| per-plant committed split | miso-112 | R | C1 2024 −10.23 TWh; night level driven below the meter |
| **committed-run night floor** | **miso-113** | **R** | **C7 moves backwards; a floor cannot widen a distribution** |

Do not re-test any of the three. Any successor must be a mechanism that
**widens the model's overnight dispatch distribution**, which none of them
is: two were prices that move the whole band together, and one was a lower
bound.

**What the three sessions have jointly established** is that COAL_PRB's C7
failure is not a coal-conduct defect at all. The class's night LEVEL is
right (§4), its volume is right (C1 16/16), its phase is right (profile_r
0.97–0.99), and neither pricing nor flooring the band moves the amplitude in
the right direction. What is missing is the **dispersion of the overnight
price signal the fleet responds to** — the model's off-peak p10 is $29.71
against an actual hub p10 of $17.95, so cheap nights in the model are not
cheap enough to make the fleet back down as far as reality does, in any
mechanism that leaves that price alone. That is the **data-blocked miso-78/79
lane** (intra-zonal congestion + sub-hourly RT price formation), and it now
carries the C7 COAL_PRB residual for all three years, not just 2025.

No successor is chartered in this lane. Rule 19 forbids stacking a fourth
coal mechanism on a price-formation residual.

## 6. The wiring defect this session found (operational, worth carrying)

The first arm-B chain solved 2023 and 2024 with `coal_prb_night_floor=true`
recorded in `run_config.json` and mechanism id 22 absent from **every**
floored unit-hour. `scripts/run_calibration.py` keeps its **own**
`p1_fleet_prep=` chain — it is the orchestrator every calibration arm and
keeper actually runs — and the hook had been wired only into
`pipeline/year.py` and `runner.py`. That is the nyiso-87 failure mode
verbatim: flag accepted, run completes, mechanism never fires, no error and
no log line.

`tests/unit/pipeline/test_p1_prep_wiring.py` exists to catch exactly this,
but its `_BRIDGE_BUILDERS` registry is hand-maintained, so a new builder
absent from it is unguarded. The row is now added and the guard verified to
fail on the real bug. **Any session adding a P1-native bridge must add its
row there in the same commit** — the test passing is otherwise no evidence.

Both void bundles were deleted and the A/B re-run from scratch.

**Memory (this box, 15 GB / 4 cores).** Rule 12's "~2 simultaneous per-plant
multi-zone runs" **does not hold here**: two concurrent single-year MISO
per-plant chains OOM-killed one arm at 9.99 GB anon-rss, and a single armed
2024 link later peaked at **15.85 GB** and was killed on its own. Both arms
completed only after (a) serializing to one chain at a time and (b) adding an
8 GB swapfile. A future MISO session on a 15 GB box should assume **one chain
at a time plus swap**, not two.

## 7. Rule duties discharged

- **Rule 15**: both arms registered on the backcast dashboard in this
  session (`2026-08-01-miso-113a-control`, `2026-08-01-miso-113b-prb-night`),
  rejection included; top-15 MISO retention honoured (pruned
  `2026-07-27-miso-96-sunkfixed-takeorpay`,
  `2026-07-27-miso-98a-sectorabsent-control`).
- **Rule 16**: one bundle per arm, `--year 2023 2024 2025`, years sequential.
- **Rule 20**: `MECH_COAL_SELFCOMMIT_NIGHT` carries a cited `D4_WINDOWS`
  entry and an ablation registration, added with the mechanism. COAL_PRB
  carried zero forced rows before this; C8 and D-4 went live on the class and
  **both pass** (2.0–3.9 % forced against a 30 % budget, 0.0 % off-window).
  No exemption was claimed in advance and none was needed.
- **Rule 22**: `--year` strictly {2023, 2024, 2025}; MISO holds no holdout
  marker and none was touched.
- **Rule 23**: the measured artifact was consumed, never re-derived; the
  deriver is untouched.
- **Rule 26b/c**: `coal_prb_night_floor` carries its OWN matrix row, added in
  the same PR as the field and stamped **R** with this finding. The
  `coal_prb_committed_dispatchable` and `coal_prb_committed_split` cells are
  NOT altered — neither form was re-tested and no new evidence bears on their
  R adjudications.
- **Rule 21**: no free parameter added — the floor consumes one measured
  conduct input formulaically; the arm is not a keeper, so no DOF ledger
  entry is created.
