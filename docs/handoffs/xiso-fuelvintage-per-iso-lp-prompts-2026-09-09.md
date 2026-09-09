# Per-ISO LP handoff prompts — the 2019-2022 retiree window + the monthly gas LEVEL

**Issued by:** session xiso-fuelvintage-1, 2026-09-09 (zero LP).
**Read first:** `docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` — the phase-0
tables, the pre-registered per-ISO expectations, and why C3b should not break the way
ercot-254's did. **Nothing below may be solved without reading it.**

## What already landed on `main` (no LP, no keeper moved, every bundle byte-identical)

| commit | what |
|---|---|
| `7934e92c` | `RETIREMENT_WINDOW_START` 2023 → 2019; the retiree artifact rebuilt **additively** (477 → 1,094 units). **Zero effect on 2023-2025 by construction.** |
| `7648daa0` | `gas_electric_power_monthly_level` — the shared measured-monthly-gas-LEVEL seam, **default off**, CLI `--gas-electric-power-monthly-level`, registered in the cache key and the mechanism matrix. |

## The two facts that shape every prompt below

1. **Card A (fleet) touches 2019-2022 ONLY.** A 2023-2025 solve is therefore a **pure
   fuel-seam A/B**, and a 2020-2022 solve carries both changes at once (owner instruction:
   no attribution arms).
2. **Markers, read per ISO from `frontend/data/backcast/calibration-complete.json` on
   2026-09-09** (`scripts/lib/holdout_policy.registration_refusals`, authoritative):

| ISO | 2023-2025 | 2022 | 2021 | 2020 | 2019 | fuel seam admissible |
|---|---|---|---|---|---|---|
| CAISO | yes | yes | yes | yes | **NO** | 2022-2025 only |
| PJM | yes | yes | yes | yes | **NO** | all years |
| **MISO** | yes | **NO** | **NO** | **NO** | **NO** | 2022-2024 (so **2023/2024 in reach**) |
| NYISO | yes | yes | yes | yes | **NO** | all years |
| NEISO | yes | yes | yes | yes | **NO** | all years |

**2019 is refused for every ISO** — locked-test tier under an ACTIVE freeze, `final` empty.
Do not ask for it and do not work around it. **MISO holds no `complete` marker**, so MISO is
2023-2025 only; the retiree window is prepared for MISO's 2020-2022 and will apply the day a
marker exists, which is exactly rule 22's "hold out the SCORE, never the DATA".

## Order of work (rule 29 `[R-SCREEN]`)

**PJM 2023 is the screen, and it runs before any other ISO spends an LP.** It is named on the
mechanism's own measured footprint, not on any residual: PJM is the only in-scope ISO where
the seam actually replaces the operative level in every month of every year (no hub overlay
to supersede it), and 2023 is its largest measured footprint year (mae 0.775 $/MMBtu, annual
−0.770). If the screen's STOP gates fail, **PJM stops and the other ISOs' fuel arms are
re-examined before they are spent.** Card A is not gated by the screen — it is an input
correctness fix with no flag.

Then, per rule 12 `[R-PARALLEL]`: separate ISO invocations concurrently, **cap 2 at a time**
for per-plant multi-zone LPs; **years sequential within one invocation, always**.
Suggested pairing: (PJM, MISO) → (NYISO, NEISO) → (CAISO).

---

## PROMPT 1 — PJM (run this one FIRST; it carries the screen)

```
PJM: the measured monthly gas LEVEL + the 2019-2022 retiree window — session pjm-fuelvintage-1

DATA PROFILE: pjm
MODEL: Opus or Fable (rule 27 [R-PUSH])
BRANCH: your own claude/<name> branch off the latest origin/main.
SCOPE: PJM ONLY. Never write another ISO's keeper shard, matrix shard or calibration log.

READ FIRST, IN THIS ORDER:
  docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md   (phase 0, all tables)
  docs/RESULT-ercot254-monthly-ep-basis-2026-09-07.md  §3b, §5, §6  (the failure mode)
  docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md    (Card A's charter)
  docs/codebase-site/data/mechanism-matrix/PJM.js  cell gas_electric_power_monthly_level (O)

TWO CHANGES ARE ALREADY ON MAIN, BOTH ZERO-LP, BOTH DEFAULT-SAFE:
  - the retiree window now covers 2019-2022 (commit 7934e92c). PJM gains 205 units /
    13,294.9 MW of net summer capacity in 2019-2022, coal-dominated (10,649.9 MW).
    Per solve year: 2020 +8,094.5 MW, 2021 +5,687.1, 2022 +4,535.9. ZERO in 2023-2025.
  - gas_electric_power_monthly_level (commit 7648daa0), default OFF, CLI
    --gas-electric-power-monthly-level.
YOU ARE NOT REBUILDING EITHER. You are solving and scoring them.

YOU CARRY THE PROGRAM'S SCREEN (rule 29 [R-SCREEN]). Do the screen before anything else.

## CARD 0 — PRECOMMIT, before any LP
Write docs/PRECOMMIT-pjm-fuelvintage-2026-09-XX.md carrying:
  (a) G-DRIFT (rule 29(b)): git diff <pjm keeper git_sha> HEAD -- src/market_sim scripts/
      run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-
      source data/raw/reference, every changed hunk on the backcast path classified INERT
      (with its reason) or LIVE. All INERT => G-CTRL form 4 and the COMMITTED keeper bundle
      pjm_debugb_inputclock_A is the control. NO CONTROL SOLVES.
      Note that data/raw/reference/iso-gas-capacity-state-weights.csv is NEW and LIVE only
      when the flag is armed; the retiree parquet is LIVE for 2019-2022 and INERT for
      2023-2025 (prove the second, don't assert it).
  (b) The screen year, NAMED BEFORE THE SCREEN RUNS: 2023, on the mechanism's largest
      measured footprint (FINDING §3: mae 0.775 $/MMBtu, annual -0.770), never on a residual.
  (c) Your per-year predictions, copied from FINDING §5b/§5c and made specific:
      gas DOWN in every year (-0.19 to -0.77 $/MMBtu annual; every month of 2023 lower by
      -0.31 to -1.42), so COAL UP and PRICES DOWN. Predict C3a's sign and magnitude, and
      predict C3b explicitly per year. PJM IS THE HIGHEST-RISK ISO for C3b in the whole
      program — say why in your own words before you see the number.
  (d) The 2020-2022 capacity predictions: prices FALL, coal generation UP.

## CARD 1 — THE SCREEN (one year, structural STOP gates only)
  python scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A \
    --years 2023 --set gas_electric_power_monthly_level=true \
    --out-dir results/screen/pjm_ep_level_2023 --note "xiso fuel seam screen"
Gates, all STOP-only (a screen may KILL an arm; it may NEVER promote one), and NONE of them
may reference the target residual:
  G-1 the delivered gas array moves in the direction and order of magnitude the pre-solve
      arithmetic implies (compare monthly means against FINDING §3's PJM 2023 row);
  G-2 confinement: non-gas fuel prices move EXACTLY 0.0;
  G-3 rule 19: the armed monthly level equals iso_electric_power_monthly_level('PJM',2023)
      exactly, i.e. it REPLACED the F923 receipt level rather than blending with it;
  G-4 no NON-TARGET load-bearing criterion (C1/C2/C3a/C3b) flips PASS -> FAIL;
  G-5 slack and dump stay 0.0.
If G-4 fails, THE ARM DIES HERE. Report it as the session's result, do not spend the other
years, and say so plainly in the FINDING — that is a successful screen, not a failure.

## CARD 2 — the training span (only if the screen clears)
  python scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A \
    --years 2023 2024 2025 --set gas_electric_power_monthly_level=true \
    --out-dir results/pjm_fuelvintage_A --note "EP monthly gas level, full span"
ONE bundle, one invocation, years sequential (rules 16 [R-ALLYEARS] / 12 [R-PARALLEL]).
Control = the committed keeper (G-CTRL form 4). Card A is inert here — PROVE IT: the fleet
arrays must be identical to the keeper's, max |class-hour delta| = 0.000000 MW.

## CARD 3 — the validation touchpoints (2020, 2021, 2022)
PJM HOLDS THE `complete` MARKER, so the validation tier is open with --holdout-authorized.
2019 is REFUSED (locked tier, active freeze) — do not attempt it.
  python scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A \
    --years 2020 2021 2022 --set gas_electric_power_monthly_level=true \
    --holdout-authorized --out-dir results/pjm_fuelvintage_TP \
    --note "retiree window 2019-2022 + EP monthly gas level"
These carry BOTH fixes at once, per the owner instruction (no attribution arms).
This supersedes 2026-09-07-pjm-2022-2021-touchpoints, which was measured on the OLD fleet:
say so, and difference against it.
Rule 30 [R-TOUCHPOINT-FOLD]: stamp the touchpoint to the keeper
(scripts/stamp_touchpoint_holdout.py --run-id <id> --keeper-id <keeper>), rebuild
scripts/build_status.py --iso PJM, and remember rule 30(c) — a held-out year NEVER
downgrades PJM's determination.

## GOVERNANCE (all of it binds)
- Rule 31 [R-RETAIN]: DO NOT DELETE ANY SOLVE'S RESULTS until the owner rules on promotion.
  Gitignore the bundle families instead (that is what discharges rule 29(c)); keep them on
  local disk; say in your final report that they will not survive the session, and ASK THE
  PROMOTION QUESTION EXPLICITLY.
- Rule 15 [R-DASHBOARD]: register every completed run in THIS session, keeper or rejected.
- Rule 1 [R-STRUCT] / 14 [R-ACCURATE]: these land because they are CORRECT. If a fit gets
  worse, keep the accurate input and open the root cause — never revert to the estimate.
  Report every criterion at full magnitude; do not gate on the target.
- Rule 28: update ONLY docs/codebase-site/data/mechanism-matrix/PJM.js, cell
  gas_electric_power_monthly_level (currently O), with your verdict and evidence.
- Gates before push: check_registry_payload_parity, audit_keepers --iso PJM,
  build_status --check --iso PJM, check_mechanism_matrix --base origin/main,
  check_cache_key_registration --base origin/main (ALREADY RED on main for
  HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT — pre-existing, not yours), pytest tests/scoring
  (baseline the pre-existing failures yourself before editing).
- ruff pre-push hook: uv run ruff check --fix --force-exclude -- <files> then
  uv run ruff format --force-exclude -- <files>.
```

---

## PROMPT 2 — MISO (the ISO the fuel seam was built for; run alongside PJM)

```
MISO: the measured monthly gas LEVEL — session miso-fuelvintage-1

DATA PROFILE: miso
MODEL: Opus or Fable (rule 27 [R-PUSH])
BRANCH: your own claude/<name> branch off the latest origin/main.
SCOPE: MISO ONLY. Never write another ISO's shard or log.

READ FIRST: docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md (§1a, §3, §3b, §5)
            docs/RESULT-ercot254-monthly-ep-basis-2026-09-07.md §3b/§5/§6
            docs/codebase-site/data/mechanism-matrix/MISO.js cell
            gas_electric_power_monthly_level (O)

WHY MISO. MISO is one of only TWO ISOs whose keeper carries NO measured monthly gas level at
all: gas_monthly_actuals False, gas_hub_basis_overlay False. Its gas price is the annual
Henry Hub override plus the flat GAS_BASIS_DIFFERENTIAL 0.30 constant times the GENERIC
climatological shape — model monthly CV = 0.094 identically in 2019, 2020, 2021, 2022, 2023,
2024 and 2025. That is the GAS_MONTHLY_SEASONALITY constant, exactly. MISO's gas price shape
is the same in Winter Storm Uri as in a mild spring.

TWO HARD CONSTRAINTS, BOTH MEASURED, BOTH NON-NEGOTIABLE:
 1. MISO HOLDS NO `complete` MARKER. You may solve 2023, 2024 and 2025 and NOTHING ELSE.
    holdout_policy.registration_refusals refuses 2020/2021/2022 for MISO at both the launch
    gate and the registration gate. Do not pass --holdout-authorized; do not work around it.
    If you believe MISO should hold the marker, say so to the owner — do not act on it.
 2. THE RETIREE WINDOW (commit 7934e92c) IS INERT IN 2023-2025 BY CONSTRUCTION. MISO gains
    189 units / 9,127.8 MW in 2019-2022 (coal 6,673.5 MW, Palisades 601.4 MW nuclear), and
    ZERO MW in any year you are allowed to solve. So YOUR RUN IS A PURE FUEL A/B — say that
    plainly rather than crediting the fleet fix with anything.

AND THE THING YOU MOST WANT IS OUT OF REACH, STATED UP FRONT: MISO's Feb-2021 gas is
11.245 $/MMBtu BELOW measured (~84 $/MWh at a 7.5 MMBtu/MWh CC heat rate) — the largest
in-scope defect in the program. It is NOT FIXABLE from this source and NOT SOLVABLE by you:
Louisiana is 23.8% of MISO's gas capacity and the state Uri hit hardest, and EIA prints no
N3045 month for LA in 2019, 2020 or 2021, so the seam REFUSES those years rather than blend
a basket that omits the hot state (FINDING §3b). Do not add a national backfill to reach it.

## CARD 0 — PRECOMMIT before any LP
  (a) G-DRIFT per rule 29(b) against miso247_fullspan_K's git_sha; all-INERT => G-CTRL form 4,
      the committed keeper IS the control. NO CONTROL SOLVES.
  (b) Screen year NAMED FIRST: 2024, the larger measured footprint of the two admissible
      training years (FINDING §3: max month gap 1.551 $/MMBtu in January vs 1.000 in 2023).
      Named on the mechanism's footprint, never on a residual.
  (c) Predictions from FINDING §5b: gas UP slightly on the annual (+0.18 in 2023, +0.07 in
      2024), with the move CONCENTRATED IN JANUARY (1.0-1.6 $/MMBtu => 7.5-11.6 $/MWh).
      FLATNESS CHECK, pre-registered: MISO 2023's measured monthly CV is 0.148 against a
      model 0.094 — a small difference, so 2023 MUST BARELY MOVE. IF 2023 MOVES A LOT, THAT
      IS A BUG TO INVESTIGATE, NOT A WIN.
      C3b is the criterion most likely to move (the change is concentrated in the month C3b's
      monthly shape is measured on): predict improvement, magnitude < 0.05.
  (d) Rule 19 [R-ONE-MECH] check, IN WRITING: miso_zonal_gas_basis is a MEAN-ZERO SPREAD and
      is orthogonal to this LEVEL; miso_zonal_gas_basis_skip_923_priced and the per-plant
      F923 print path are NOT. Under the keeper's print path 100% of MISO gas capacity-hours
      are print-derived (FINDING §4 table; matrix MISO zonal_gas_basis note). WORK OUT AND
      STATE, BEFORE SOLVING, whether apply_plant_monthly_fuel_prices overwrites this seam's
      level per plant, and if it does, whether that makes the arm inert. THIS IS THE MOST
      LIKELY WAY THIS ARM COMES BACK INERT and you should find it at zero LP cost, not after.

## CARD 1 — screen (2024, structural STOP gates only, never the target residual)
  python scripts/replay_keeper.py results/calibration/miso247_fullspan_K \
    --years 2024 --set gas_electric_power_monthly_level=true \
    --out-dir results/screen/miso_ep_level_2024 --note "xiso fuel seam screen"
Gates: G-1 direction/magnitude vs the pre-solve delta; G-2 non-gas fuels move exactly 0.0;
G-3 the armed monthly level equals iso_electric_power_monthly_level('MISO',2024) exactly at
the ISO series (rule 19: replaced, not blended); G-4 no non-target load-bearing criterion
flips PASS -> FAIL; G-5 slack/dump 0.0. A screen may KILL the arm and may never promote it.

## CARD 2 — the full span (only if the screen clears)
  python scripts/replay_keeper.py results/calibration/miso247_fullspan_K \
    --years 2023 2024 2025 --set gas_electric_power_monthly_level=true \
    --out-dir results/miso_fuelvintage_A --note "EP monthly gas level, full span"
NOTE 2025 IS INERT BY COVERAGE (basket 0.40 — Minnesota and Mississippi drop out; FINDING §3).
Predict a byte-identical 2025 and then CHECK IT: a 2025 move means the admission test is not
doing what the module says, and that is a STOP.

## GOVERNANCE
Same as PJM's prompt: rule 31 (NEVER delete results before the owner rules — gitignore, keep
on disk, ask the promotion question explicitly in your final report), rule 15 (register in
this session, keeper or rejected), rule 1/14 (a worse fit is a root cause, never a revert),
rule 28 (update ONLY MISO's shard cell), and the same pre-push gate list with --iso MISO.
```

---

## PROMPT 3 — NYISO

```
NYISO: the 2019-2022 retiree window (+ a near-inert fuel check) — session nyiso-fuelvintage-1

DATA PROFILE: nyiso
MODEL: Opus or Fable (rule 27 [R-PUSH])
BRANCH: your own claude/<name> branch off the latest origin/main.
SCOPE: NYISO ONLY.

READ FIRST: docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md §3, §4, §5

THE HEADLINE FOR NYISO IS THE FLEET, NOT THE FUEL. The retiree window (commit 7934e92c) adds
31 units / 3,671.9 MW to NYISO's 2019-2022 fleets, and it is dominated by NUCLEAR: Indian
Point 2 (plant 2497, 1,299 MW, retired 2020-04) and Indian Point 3 (plant 8907, 1,012 MW,
retired 2021-04), plus 1,487.0 MW of coal. Per solve year: 2020 +3,261.5 MW, 2021 +1,570.2,
2022 +526.6, and ZERO in 2023-2025. This closes the standing constants.py caveat on
NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO'] ("a 2018-2021 solve is short that capacity regardless of
this overlay") — the CF overlays are INTENSIVE and could never restore missing capacity.
Retiring that caveat text is NYISO's lane's to do (charter task 4) and belongs in this session.

THE FUEL SEAM SHOULD BE NEAR-INERT FOR NYISO, AND THAT IS THE PREDICTION, NOT AN EXCUSE.
gas_electric_power_monthly_level is admissible in all seven years, but NYISO's keeper carries
gas_hub_basis_overlay (Transco Z6) covering 12/12 months of every year, and the seam is
applied BEFORE the hub overlay precisely so a measured constrained-hub index supersedes a
state-average delivered cost (FINDING §4's ordering table). Phase 0 shows why that ordering
is right: the keeper series runs ABOVE the state average in nearly every month (2025 annual
-1.189, Jan -5.107 $/MMBtu) — expected, because downstate NYC gas is dearer than the NY state
mean. PRE-REGISTER: C3b unchanged to three decimals with the flag armed. A LARGE NYISO MOVE
MEANS THE ORDERING IS WRONG — STOP AND REPORT, do not bank it.

## CARD 0 — PRECOMMIT
  (a) G-DRIFT vs nyiso213_summer_seam's git_sha; all-INERT => G-CTRL form 4, committed keeper
      is the control. NO CONTROL SOLVES.
  (b) The near-inertness prediction above, in numbers, before you solve.
  (c) 2020/2021 capacity predictions: prices FALL, nuclear generation UP; 2020 is the bigger
      year (Indian Point 2 present for Jan-Apr).

## CARD 1 — the fuel inertness check (2023 only, cheap)
  python scripts/replay_keeper.py results/calibration/nyiso213_summer_seam \
    --years 2023 --set gas_electric_power_monthly_level=true \
    --out-dir results/screen/nyiso_ep_level_2023 --note "ordering check, expect near-inert"
If it is near-inert as predicted, LEAVE THE FLAG OFF for the rest of the session and say so —
that is the correct outcome and it costs NYISO nothing. If it is NOT, stop and report.

## CARD 2 — the touchpoints, on the CORRECTED fleet (the real work)
NYISO HOLDS `complete`, so 2020/2021/2022 are open with --holdout-authorized.
2019 IS REFUSED (locked tier, active freeze). Do not attempt it.
  python scripts/replay_keeper.py results/calibration/nyiso213_summer_seam \
    --years 2020 2021 2022 --holdout-authorized \
    --out-dir results/nyiso_fuelvintage_TP --note "retiree window 2019-2022 fleet"
This SUPERSEDES 2026-09-06-nyiso-209-2022-touchpoint, which was scored on a fleet missing
Indian Point 3: difference against it and say what the nuclear restoration did to
C1 CC_REGULAR (+4.35 TWh / +3.3 pp there) and to C3a (-11.2%).
Rule 30 [R-TOUCHPOINT-FOLD]: stamp to the keeper, rebuild build_status.py --iso NYISO, and
remember 30(c) — a held-out year NEVER downgrades NYISO's determination.

## CARD 3 — prove the training window did not move
The retiree window is inert in 2023-2025 by construction. PROVE IT rather than asserting it
(charter task 3): re-solve 2023-2025 on the frozen recipe and require max |class-hour delta|
= 0.000000 MW against the committed keeper in all three years. A nonzero delta means
capacity-denominated code is reading retired units — root-cause it, do not wave it through.

## GOVERNANCE
Rules 31 / 15 / 1 / 14 / 28 exactly as in PJM's prompt, with --iso NYISO. Update ONLY
NYISO's matrix shard. Charter task 4 (retiring the NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']
caveat text in constants.py) is NYISO's own lane work and belongs here.
```

---

## PROMPT 4 — NEISO

```
NEISO: the 2019-2022 retiree window, and the gas index-vs-delivered gap — session neiso-fuelvintage-1

DATA PROFILE: neiso
MODEL: Opus or Fable (rule 27 [R-PUSH])
BRANCH: your own claude/<name> branch off the latest origin/main.
SCOPE: NEISO ONLY.

READ FIRST: docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md §3, §4, §6a

THE FLEET FIX. The retiree window (commit 7934e92c) adds 44 units / 1,696.5 MW to NEISO's
2019-2022 fleets, of which PILGRIM (plant 1590, 673.6 MW nuclear, retired 2019-05) is the
one that matters, plus 574.2 MW of oil peakers. Per solve year: 2020 +956.0 MW, 2021 +949.0,
2022 +201.3 (immaterial), ZERO in 2023-2025. THE 2019 CASE IS THE BIG ONE AND YOU CANNOT
SOLVE IT: the charter measured Pilgrim's absence at -2.123 TWh in 2019 against +/-0.15 TWh in
every year 2020-2025 — 91% of NEISO 2019's whole C1 error budget — but 2019 is LOCKED-TEST
tier under an ACTIVE freeze with `final` empty, and it is REFUSED. Do not attempt it, and do
not treat the repair as evidence about 2019. What you CAN do is retire the standing
constants.py caveat on NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO'] ("a 2019 solve is short ~2.18 TWh
of nuclear regardless of this overlay") — charter task 4, NEISO's own lane, belongs here.

THE FUEL SEAM SHOULD BE NEAR-INERT FOR NEISO, for the same ordering reason as NYISO:
gas_hub_basis_overlay (Algonquin Citygate, via the ISO-NE MA gas index) covers 12/12 months
of every year and supersedes the state-average level. Predict C3b unchanged to three decimals.

BUT NEISO CARRIES THE ONE DISCREPANCY THIS PROGRAM HAS NOT RESOLVED, AND IT IS YOURS:
for January 2023 the two measured sources disagree by 3.2x. The ISO-NE published AGT index
gives HH 3.273 + 1.46 = $4.73/MMBtu; EIA N3045 MA/CT/RI delivered-to-electric-power reads
$15.34. That is why NEISO's keeper gas series sits 2.303 $/MMBtu BELOW measured on the 2023
annual — the largest level gap in the whole cross-ISO table (FINDING §3, §6a). The reading
this session took, and did NOT act on: they measure different things (a day-ahead index vs
the average delivered cost actually paid, including the intraday and balancing purchases New
England generators without firm transport make in January), the marginal OFFER is set by the
index, so the hub index correctly keeps priority under rule 14's misalignment exception.
THAT READING IS STATED, NOT PROVEN. A 3.2x gap between two measured series for one quantity
is NEISO's real fuel lever and it is a ZERO-LP investigation. Do it before you spend an LP on
anything else, and write it up whatever it concludes.

## CARDS
 0. PRECOMMIT: G-DRIFT vs neiso106_offerlevel's git_sha (all-INERT => G-CTRL form 4, the
    committed keeper is the control, NO CONTROL SOLVES); the near-inertness prediction in
    numbers; the 2020/2021 capacity predictions (prices FALL modestly; 2022 immaterial at
    201 MW — a large 2022 move is a BUG, not a win).
 1. THE INDEX-VS-DELIVERED INVESTIGATION (zero LP). Is $15.34 the New England marginal
    generator's January gas cost, or is it a small-denominator artifact of a month when
    little gas was burned at extreme prices? Check the N3045 volume series, the AGT daily
    prints (data/raw/gas-prices/algonquin_citygate_daily.csv), and the EIA-923 NEISO
    receipts against each other. Conclude, cite, and STOP THERE if the answer is that the
    index is right — that is a real result.
 2. The fuel inertness check, 2023 only:
      python scripts/replay_keeper.py results/calibration/neiso106_offerlevel \
        --years 2023 --set gas_electric_power_monthly_level=true \
        --out-dir results/screen/neiso_ep_level_2023 --note "ordering check"
    Near-inert as predicted => leave the flag OFF and say so.
 3. The touchpoints on the corrected fleet. NEISO HOLDS `complete`; 2020/2021/2022 are open
    with --holdout-authorized; 2019 IS REFUSED.
      python scripts/replay_keeper.py results/calibration/neiso106_offerlevel \
        --years 2020 2021 2022 --holdout-authorized \
        --out-dir results/neiso_fuelvintage_TP --note "retiree window 2019-2022 fleet"
    Rule 30 [R-TOUCHPOINT-FOLD]: stamp to the keeper, rebuild build_status.py --iso NEISO,
    and 30(c) — a held-out year NEVER downgrades NEISO.
 4. Prove 2023-2025 did not move: max |class-hour delta| = 0.000000 MW vs the committed
    keeper, all three years (charter task 3). A nonzero delta is a STOP.

## GOVERNANCE
Rules 31 / 15 / 1 / 14 / 28 exactly as in PJM's prompt, with --iso NEISO. Update ONLY
NEISO's matrix shard.
```

---

## PROMPT 5 — CAISO (run last; smallest expected effect)

```
CAISO: the 2019-2022 retiree window (+ a near-inert fuel check) — session caiso-fuelvintage-1

DATA PROFILE: caiso
MODEL: Opus or Fable (rule 27 [R-PUSH])
BRANCH: your own claude/<name> branch off the latest origin/main.
SCOPE: CAISO ONLY.

READ FIRST: docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md §3, §4, §5

CAISO IS THE SMALL CASE AND THAT IS THE PRE-REGISTERED PREDICTION, NOT A HEDGE.
The retiree window (commit 7934e92c) adds 86 units / 1,700.6 MW to CAISO's 2019-2022 fleets
(gas-CC 703.0 MW, gas-ST 480.0, solar-thermal 180.0, wind 166.2). Per solve year: 2020
+1,120.5 MW, 2021 +278.6, 2022 +60.1, ZERO in 2023-2025. PREDICT NO MATERIAL PRICE MOVEMENT
IN 2021 OR 2022 on a fleet of tens of GW; 2020 is the only year with a plausible signal.
A LARGE 2021 OR 2022 MOVE IS A BUG TO INVESTIGATE, NOT A WIN.

THE FUEL SEAM IS INERT IN 2019-2021 BY COVERAGE and near-inert in 2022-2025 by ordering.
Coverage: California itself prints only 11 of 12 N3045 months in each of 2019, 2020 and 2021,
so the admission test (all twelve months, majority of gas capacity) refuses those years and
the ISO's existing construction stands byte-for-byte (FINDING §3, §3b). Ordering: CAISO's
keeper carries gas_hub_basis_overlay (SoCal / PG&E Citygate) covering 12/12 months of every
year, which supersedes the state-average level by construction. Phase 0's 2023-2025 annual
deltas are +0.09 to +0.24 $/MMBtu — small, and mostly not reachable. PRE-REGISTER: C3b
unchanged to three decimals; 2019-2021 byte-identical with the flag armed. VERIFY THE
BYTE-IDENTITY rather than assuming it — it is the admission test's own guarantee and it is
the cheapest possible check that the module does what its docstring says.

ONE NUMBER WORTH KNOWING even though you probably cannot reach it: CAISO December 2022 is
16.058 $/MMBtu below measured (~120 $/MWh at a CC heat rate) — the western gas crisis. 2022
IS admissible for the seam and IS open to you under the `complete` marker, so this is the one
CAISO ISO-month where the mechanism could actually bite. Predict its sign and magnitude
before you solve it.

## CARDS
 0. PRECOMMIT: G-DRIFT vs caiso260_demand_vintage's git_sha (all-INERT => G-CTRL form 4, the
    committed keeper is the control, NO CONTROL SOLVES); the inertness and Dec-2022
    predictions in numbers.
 1. Fuel check, 2023 only (ordering) plus a zero-LP assertion that
    iso_electric_power_monthly_level('CAISO', y) is None for y in 2019, 2020, 2021.
      python scripts/replay_keeper.py results/calibration/caiso260_demand_vintage \
        --years 2023 --set gas_electric_power_monthly_level=true \
        --out-dir results/screen/caiso_ep_level_2023 --note "ordering check"
 2. The touchpoints on the corrected fleet. CAISO HOLDS `complete` (declared 2026-09-06);
    2020/2021/2022 are open with --holdout-authorized; 2019 IS REFUSED (locked tier, freeze).
      python scripts/replay_keeper.py results/calibration/caiso260_demand_vintage \
        --years 2020 2021 2022 --holdout-authorized \
        --out-dir results/caiso_fuelvintage_TP --note "retiree window 2019-2022 fleet"
    These are CAISO's FIRST validation touchpoints since the marker was declared: the ladder
    on the Calibration Status page is currently empty for CAISO, so build_status.py --iso
    CAISO will populate it. Rule 30 [R-TOUCHPOINT-FOLD]: stamp to the keeper; 30(c) — a
    held-out year NEVER downgrades CAISO's determination, which stays the train-tier verdict.
 3. Prove 2023-2025 did not move: max |class-hour delta| = 0.000000 MW vs the committed
    keeper, all three years (charter task 3). A nonzero delta is a STOP.

## GOVERNANCE
Rules 31 / 15 / 1 / 14 / 28 exactly as in PJM's prompt, with --iso CAISO. Update ONLY
CAISO's matrix shard.
```

---

## Not issued, and why

- **SPP** — explicitly out of this session's scope. For the record it is the *other* ISO on
  the generic shape in every year (model CV 0.094 throughout), with a **Jan-2022 gap of
  13.368 $/MMBtu (~100 $/MWh)**, admissible 2022-2024 and inert 2019-2021/2025 because
  Oklahoma (37.5 % of its gas capacity) prints no N3045 month. Its matrix cell is `U`, minted
  by the rule-28(c) same-PR duty with **no adjudication made or implied**.
- **ERCOT** — session ercot-261's. ERCOT already carries the ISO-specific ancestor of this
  construction (`ercot_electric_power_gas_basis`, N3045TX3) and its monthly form
  `ercot_ep_gas_basis_monthly`, built and left default-off by ercot-254. **Rule 19
  `[R-ONE-MECH]`: ERCOT must never arm `gas_electric_power_monthly_level` alongside either
  of those — they price the same phenomenon.**
- **2019, every ISO** — locked-test tier, `final` empty, freeze ACTIVE. Refused at the launch
  gate, the registration gate and `audit_keepers`. Granting it is an explicit owner act.
- **The 107 units / 497.7 MW of 2023-2025 retirements** the newer EIA release carries and the
  keepers' fleets lack (FINDING §2b). Real, and deliberately excluded here because adding
  them changes the training window and re-keys every committed bundle. It needs its own
  session, scoped to the training window, per ISO, with its own control.

---

## ADDENDUM — issued with the shard launches, 2026-09-09

The five prompts above were launched as **five independent Claude Code Remote sessions**, each
branched off `claude/xiso-fuelvintage-retirements-96sbx9` (this branch, **not** `main` — the
seam and the artifact are not on `main`):

| session | ISO | id |
|---|---|---|
| `pjm-fuelvintage-1` (carries the program screen) | PJM | `session_01BvoDm9zatZFZeUoeXET8Vg` |
| `miso-fuelvintage-1` | MISO | `session_01VbwJT9rfJnos5AwCRJhRrE` |
| `nyiso-fuelvintage-1` | NYISO | `session_012sPYKANuAcHZQ6HwuAC8fY` |
| `neiso-fuelvintage-1` | NEISO | `session_01MxJVKFsVxeFMR8wMwzKTXi` |
| `caiso-fuelvintage-1` | CAISO | `session_01WUiDChsnCoj1Y3W6SF5DR9` |

### A1. Each lane shards its own solves, 2 years per shard (owner instruction)

Each lane launches its solve groups as **its own** child sessions, so every shard gets its own
container and rule 12 `[R-PARALLEL]`'s ~2-simultaneous RAM cap does not bind across them; years
**within** one invocation stay sequential, always.

| shard | years | ISOs |
|---|---|---|
| S / F | one year | screen (PJM 2023, MISO 2024) or ordering check (CAISO / NYISO / NEISO 2023) |
| T1 | 2023 2024 | all five |
| T2 | 2025 | all five |
| H1 | 2020 2021 | CAISO PJM NYISO NEISO (`--holdout-authorized`) |
| H2 | 2022 | CAISO PJM NYISO NEISO (`--holdout-authorized`) |

**Sharding the SOLVE must not become registering FRAGMENTS.** Rule 16 `[R-ALLYEARS]` is
untouched: each ISO registers **one** bundle covering 2023-2025, composing T1 and T2 the way
ERCOT's keeper composes several configs into one registered run. A 2-year or 1-year fragment is
never a keeper.

### A2. A LATE FINDING every lane carries in its prompt — the arm may be INERT

**All five keepers carry `gas_plant_monthly_fuel_pricing = True.**
`apply_plant_monthly_fuel_prices` runs **after** the new seam and overwrites each gas plant's
price with that plant's own F923 monthly print. The seam may therefore reach only the cells the
print path does not write, plus the ISO-level `_gas_series` that keys the coal passthrough
sigmoid. For MISO the mechanism matrix's own note already records that **100 % of MISO gas
capacity-hours are print-derived** under the keeper's path.

Every lane is directed to **census the written-cell mask at zero LP cost before any solve**
(rule 29 `[R-SCREEN]` clause (0): an arm with a computable pre-solve gate does not reach a solve
until that gate passes), and to report an inert result as the session's result rather than
spending the span. The parent session attempted this census and did not land it — `run_year`'s
`fleet_only` return shape defeated two attempts inside the remaining budget — so it is handed
over as named, scoped work rather than left implied.

### A3. Corrected gate baselines (measured on this branch, 2026-09-09)

- **`pytest tests/scoring`: 16 failures, not 15.** Measured identically on this branch and with
  every changed source reverted to `origin/main` (16 failed / 1,532 passed both ways), so **all
  16 are pre-existing and this branch adds none.**
- **`check_cache_key_registration --base origin/main`: RED on `main`** for
  `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`. Pre-existing. This branch's own new field passes
  (`ok: 1 new field(s), all registered: gas_electric_power_monthly_level`).
- **`build_status --check --iso CAISO` / `audit_keepers --iso CAISO`: RED on `main`**, "stale vs
  the current verdicts". Verified pre-existing by reverting every changed source to
  `origin/main` and reproducing it. **Not touched here** — rule 25 `[R-ISO-SCOPE]` makes CAISO's
  status file CAISO's lane's to write, so clearing it is assigned to `caiso-fuelvintage-1`.
- Green on this branch: `check_registry_payload_parity` (22 runs, 55 bundle dirs, 0 tolerated),
  `check_mechanism_matrix --base origin/main`, and `audit_keepers` for PJM / MISO / NYISO /
  NEISO.

### A4. LAUNCH FAILURE AND FIX — pin `source_revision` to a COMMIT SHA, never a branch name

**All five shards in A1 failed to initialize.** Every one returned the same
`last_init_error`:

```
error_kind   : source_processing
error_type   : ref_not_found
message      : The requested branch or commit was not found in the repository
               "jessicacohen554-cyber/market-simulator". Check the spelling of the branch
               name, verify it exists on the remote, and ...
recoverable  : false
```

**The branch was not missing.** `git ls-remote origin refs/heads/claude/xiso-fuelvintage-retirements-96sbx9`
resolves, and it resolved at launch time — it had been pushed (and blob-verified against the
server) before the first `create_session` call. The failures are at 03:48:07, 03:48:40,
03:49:24, 03:49:58 and 03:50:40, all after the push. What distinguishes them from the ERCOT
sibling sessions launched at 03:46-03:47, which initialized fine, is that ERCOT's branch had
existed on the remote for far longer: **the CCR source-processing worker resolves against a
repo view that lags a freshly-created ref.**

**The fix, verified:** pass `source_revision` as the **full 40-character commit SHA**
(`33f6c0614ecd63a5019742c5ee588e791c0f12ab`) instead of the branch name. All five relaunched
sessions initialized clean — `connection_status: connected`, `status_bucket: WORKING`, no
`last_init_error`:

| session | ISO |
|---|---|
| `session_01SkSpzepiCuuJxYVbMctUy4` | PJM (carries the program screen) |
| `session_01CvLmniL3N8QcAG8SpVCHtt` | MISO |
| `session_01QpQ55FJ3LUqahzyibsy7jF` | NYISO |
| `session_01D8ZQWudYxQkivKxkBZZxp7` | NEISO |
| `session_01RX3WrPVoVWhkRBgVDEgzzy` | CAISO |

**Standing guidance for every lane that shards further** (each carries it in its own prompt):
push, then `git rev-parse HEAD`, then pass **that SHA** to `create_session`. Give every child a
STEP-0 checkout verification (`git log --oneline -4`, plus an existence check on a file the
branch introduces) with an explicit `git fetch` + `git checkout -B <own> FETCH_HEAD` recovery,
so a child that lands on `main` by accident repairs itself instead of silently rebuilding work
that already exists.

### A5. THE BRANCH MERGED TO MAIN, MAIN MOVED 51 COMMITS, AND ALL FIVE SHARDS WERE RELAUNCHED AT THE TIP

**This program's branch is on `main`.** PRs **#5734** and **#5735** merged
`claude/xiso-fuelvintage-retirements-96sbx9`, so the retiree-window widening, the
`gas_electric_power_monthly_level` seam, the weight table, the tests, the FINDING and these
prompts are all on `main` — nothing here is branch-only any more.

**Main then moved 51 commits ahead**, and the A4 shards were pinned to `33f6c061`, i.e. 51
commits stale. `origin/main` was merged into the branch (clean, zero conflicts), verified, and
pushed: the tip is now **`b9fcb160d92dadbe86dcec5f6c8e2ba1793a5f1c`**, which is `origin/main`
**plus nothing** (`git rev-list --count origin/main ^HEAD` = 0).

**Verified on the merged tree before relaunching** — the merge changed none of this program's
work: `data/raw/eia-860/eia860_generator_retired_within_window.parquet` still 1,094 rows /
min year 2019 / 477 rows at ≥2023; `RETIREMENT_WINDOW_START = 2019`;
`src/market_sim/data/fuel/electric_power.py` present; `gas_electric_power_monthly_level` in
`scenarios.py` (4), `run_calibration_full.py` (2), `resolve.py` (1), `trajectories.py` (2);
`test_retiree_window_extension.py` + `test_gas_electric_power_level.py` +
`test_partial_plant_exit_carry.py` + `tests/regression/test_fuel_facade.py` **50 passed**;
`check_mechanism_matrix --base origin/main` green.

**Three things landed on main that every lane must now account for**, and each carries them in
its own prompt:

1. **ercot-261 built an ERCOT-scoped SIBLING of the seam** — a *corroborated* monthly gas LEVEL
   (`data/raw/ercot_gas_corroborator_monthly.csv`,
   `scripts/data/derive_ercot_gas_corroborator.py`, `src/market_sim/data/fuel/basis/ercot.py`,
   `tests/unit/data/fuel/test_ercot_gas_corroboration.py`). It touches neither
   `gas_electric_power_monthly_level` nor any non-ERCOT ISO, but it is the closest prior art to
   every lane's arm — and checking one measured series against a second is the one legitimate
   line of attack on **MISO's Louisiana coverage hole** and on **NEISO's 3.2× index-vs-delivered
   gap** (§6a). Lanes are told to **recommend**, not to build a copy unilaterally.
2. **ercot-261 added a PARTIAL-PLANT exit channel** —
   `src/market_sim/data/fleet/eia860.py::_partial_plant_exit_rows`, gated
   `ScenarioConfig.partial_plant_exit_carry`, `_PARTIAL_EXIT_WINDOW_START = 2019`. It is the
   exact complement of the whole-plant window this program widened: same 2019 floor, units whose
   *plant survives*. Its docstring asserts zero overlap with the whole-plant parquet by
   construction; **every lane is told to verify that for its own ISO rather than trust it**,
   because a double-count would be invisible and, in PJM (13,294.9 MW restored), material.
3. **Each ISO's own lane moved** — pjm-177, miso-248, caiso-267, NEISO capx-D90, spp-52a. Lanes
   must run **G-DRIFT against `origin/main`**, not the handoff base, and **re-read their keeper
   shard** in case the keeper moved. CAISO is told explicitly that caiso-267 may already have
   spent its 2022 touchpoint, and that its lane's `build_status` red may already be cleared.

**Relaunch.** SendMessage cannot reach a cloud sibling, so the five stale sessions were
interrupted, archived, and **relaunched pinned to `b9fcb160`** (~5 minutes of work lost, all of
it setup). All five came up `connected` / `WORKING` with no `last_init_error`:

| session | ISO |
|---|---|
| `session_01BudZjmibLgP6M6EtSxCkwp` | PJM (carries the program screen) |
| `session_011LP4g5bi8YHsaH5yeZVvh2` | MISO |
| `session_012VikC6mGbPmctE9gVS3QcF` | NYISO |
| `session_01RWLcg3XCMyDuGy45WAXoyM` | NEISO |
| `session_012aNt8CFETU5cCW3EiWzmXf` | CAISO |

**Two operational rules this cost us, now in every prompt:** pin `source_revision` to a commit
SHA (§A4), and **put everything a child needs in its launch prompt** — a cloud sibling cannot be
messaged after launch, so a stale one must be archived and relaunched rather than corrected.
Every lane is additionally told to **re-baseline `pytest tests/scoring` on its own tree**: the
16-failure figure in §A3 was measured on the pre-merge base and 51 commits have landed since.

### A6. THE PJM OOM — diagnosed, fixed, and the fix is standing tooling

**Symptom.** `pjm-fuelvintage-1` reported *"control solve at 13.75 GiB RSS past OOM wall"*.

**Diagnosis, from the repo's own measured registry — not a guess.**
`scripts/run_isos_concurrent.py` puts **PJM's single-solve peak RSS at 13.0 GB**, the highest
of any ISO (MISO 11.5, SPP/ERCOT 6.0, CAISO 4.5, NYISO/NEISO 4.0), and it is the only ISO that
is both `per_plant` **and** `co_opt`. A CCR container is **15.7 GiB with ZERO swap**. The
wallclock/RSS baseline those numbers were measured on had a **pre-existing `/swapfile`**
(`docs/handoffs/perf-recheck-2026-08.md` §1.2). That is precisely why PJM "has run in this
container before" and is dying now: the box is the same, the **swap backstop is gone**, so a
13 GB peak that used to page now gets SIGKILL'd (child return code −9).

**Three causes, in order of size:**

1. **No swap.** Fixed by new standing tooling, `scripts/prepare_solve_container.py` —
   provisions a swapfile up to a RAM+swap target (default 24 GiB), bounded by free disk with a
   6 GiB reserve for solve output. **Verified end to end in this container class**: `fallocate`
   + `mkswap` + `swapon` all succeed as root, `free` confirms the swap, and the script
   correctly reports a disk-bound partial provision rather than failing silently.
2. **Missing env pins.** The canonical single-thread / arena-pinned profile
   (`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1`) is already used by
   five scripts and by `run_isos_concurrent._CHILD_ENV_PINS`, and `model/lp/model.py`'s own
   comment records the OOM it exists to prevent. **They do not change the LP optimum** — thread
   count is a factorization-workspace choice. The lanes were never told to set them.
3. **PJM was running a CONTROL SOLVE, which rule 29(b) forbids.** "NO CONTROL SOLVES — the
   committed keeper bundle IS the control (G-CTRL form 4)." That is a governance deviation
   *and* it doubles the LP work on the heaviest ISO in the program. Removing it is the largest
   single saving available.

Every relaunched lane now runs `prepare_solve_container.py` before its first solve, exports the
pins, and is reminded that a control solve is refused.

### A7. OWNER RULING 2026-09-09 — PROMOTE ON BOTH COUNTS, REGARDLESS OF INERTNESS

Verbatim: *"these should be promoted as keepers on both 860 and gas shape counts regardless of
inertness."*

This **overrides the disposition guidance in PROMPT 1-5 and in §A2**, which told each lane to
report an inert arm as its result and not spend the span. It does **not** override any
measurement duty. Concretely, for every lane:

- **Both changes are promoted**: the EIA-860 retiree-window widening **and** the measured
  monthly gas LEVEL. Neither waits on the other, and neither waits on a favourable residual.
- **Inertness is not a disqualifier.** An arm measured inert in dispatch is still promoted; the
  lane reports the inertness at full magnitude as a property of the result, not as a reason to
  withhold. This is the owner's standing formula — *"If structural integrity improves but gates
  regress that may still be a keeper"* — applied a step further.
- **Everything else still binds, and none of it is relaxed**: the phase-0 census is still run
  and still reported (it now tells you *what the promotion is worth*, not *whether to promote*);
  every criterion is still reported at full magnitude; a screen may still kill an *arm variant*
  on structural grounds; rule 1 `[R-STRUCT]`'s ban on gating a mechanism on its target residual
  is untouched; and rule 16 `[R-ALLYEARS]` still requires ONE registered bundle per ISO covering
  2023-2025.
- **Rule 31 `[R-RETAIN]` is now doubly binding**: results are promoted, so nothing may be
  deleted before the owner rules — and the ruling here is *promote*, not *delete*.

### A8. REBASE BEFORE MERGE

Each lane rebases (or merges) its branch onto the latest `origin/main` before its work is
merged, and resolves conflicts in its own ISO's files. `main` moved 51 commits during the last
handoff alone, so a lane that solves for an hour will be behind by the time it pushes. Lanes
edit disjoint files by rule 25 `[R-ISO-SCOPE]` — each ISO's keeper shard, matrix shard, status
part and calibration log — so conflicts should be confined to shared surfaces (the mechanism
matrix base row, the handoff docs). Re-run the full gate list after the rebase, never before.

### A9. THE "plant-356 COD DEFECT" IS A FALSE ALARM — MEASURED, CLOSED, DO NOT RE-LITIGATE

Session `caiso-fuelvintage-1` (v3) stopped with *"plant-356 COD defect blocks 5 parallel
lanes"* and asked which of three repairs to apply. **The answer is none: there is no defect.**

**The concern was real in shape.** Widening the window to 2019 created injected plants whose
units retire up to **four years apart** — AES Redondo Beach (356): gen 7 retired **2019-10**,
gens 5/6/8 **2023-12**. `_load_cod_map` collapses a plant's heterogeneous unit retirements to
the **latest** one, so a plant-keyed mask would hold gen 7's 480 MW online for three extra
years. Across the whole artifact that exposure is **19 plants / 31 units / 4,779.2 MW**
(PJM 3,055.2 · NEISO 614.2 · MISO 495.8 · CAISO 481.8 · NYISO 88.5 · SPP 43.7).

**But the code already prefers the per-unit date, and always has.**
`cod_ramp.effective_cod` returns `(entry_oy, entry_om, retirement_year, retirement_month)` —
the plant map supplies the **online** date, the generator's **own** retirement overrides the
collapsed one whenever the row carries it, and every retiree row carries it by construction.
Its docstring names this exact case (the Homer City seam, plant 3122).

**Measured, not read** — masks built through the real `_load_cod_map` + `effective_cod` +
`monthly_online_mask` path:

| plant | unit | actual retirement | online months 2019 → 2024 |
|---|---|---|---|
| 356 AES Redondo Beach | gen 7, 480 MW | 2019-10 | **10 · 0 · 0 · 0 · 0 · 0** |
| 356 | gens 5/6/8 | 2023-12 | 12 · 12 · 12 · 12 · 12 · 0 |
| 3122 Homer City | gen 3 | 2023-07 | 12 · 12 · 12 · 12 · **7** · 0 |
| 3122 | gen 1 | 2024-04 | 12 · 12 · 12 · 12 · 12 · **4** |
| 2866 W H Sammis | gens 1-4, 720 MW | 2020-05 | 12 · **5** · 0 · 0 · 0 · 0 |
| 2840 Conesville | gens 5/6, 750 MW | 2019-05 | **5** · 0 · 0 · 0 · 0 · 0 |

Every unit ages out on its own month. **The 4,779.2 MW is the exposure the existing code
already prevents, not a loss anyone is taking.**

**Pinned by test** so a future change to the COD map cannot silently reintroduce it:
`test_multi_vintage_plants_age_out_PER_UNIT_not_plant_collapsed` (every multi-vintage row in
the committed artifact, through the real path) and
`test_a_units_own_retirement_wins_over_a_later_plant_date` (the synthetic form). 13 pass.

**No lane should spend time on this.** If a lane sees a fleet number it cannot explain, the
per-unit ageing is not the cause — look at `partial_plant_exit_carry` (§A5 item 2) instead.
