# PRECOMMIT — NEISO: the 2019-2022 retiree window + the measured monthly gas LEVEL

**Session:** `neiso-fuelvintage-1`, 2026-09-09. **Written before any LP was spent.**
**Keeper / control:** `results/calibration/neiso106_offerlevel` (NEISO, 2023-2025).
**Owner ruling (`xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md` §A7), verbatim:** *"these should
be promoted as keepers on both 860 and gas shape counts regardless of inertness."* Both changes are
therefore **promoted**; inertness is reported as a property of the result, never as a reason to
withhold.

---

## 1. THE PHASE-0 RESULT THAT REORDERS THE WHOLE SESSION

Rule 29 `[R-SCREEN]` clause (0): *"An arm that has a computable pre-solve gate does not reach a solve
until that gate passes."* Both of this lane's changes have one, and **both gates return an exact
identity**, not merely a pass. The two censuses below are the session's most load-bearing
measurements and they cost **zero LP**.

### 1a. The fuel seam writes ZERO cells on NEISO's keeper — 2023, 2024 and 2025

`scripts/probes/_neiso_fuelvintage_census.py 2023 2024 2025` builds the NEISO fleet twice per year
through `run_calibration.run_year(fleet_only=True)` on the keeper's own `meta.json`, differing only in
`gas_electric_power_monthly_level` (routed through `prb_overrides`, byte-identical to what
`replay_keeper --set` does):

| year | LP rows | gas rows | fuel cells | **cells written** | max abs Δ fuel | max abs Δ `mc_base` |
|---|---|---|---|---|---|---|
| 2023 | 875 | 463 | 7,665,000 | **0** | **0.0** | **0.0** |
| 2024 | 865 | 458 | 7,577,400 | **0** | **0.0** | **0.0** |
| 2025 | 867 | 460 | 7,594,920 | **0** | **0.0** | **0.0** |

**22,837,320 fuel cells, none written, and the P0 offer surface `mc_base` is identical to the last
bit.** Confinement (G-2) holds trivially: non-gas max abs Δ is 0.0 because *everything* is 0.0.

**Why**, from the solve's own log lines, and it is the FINDING §4 ordering working exactly as
designed: `hub-basis overlay (NEISO 2023, daily): 463 gas generators repriced at the measured hub
spot in 12/12 months` — the Algonquin index covers every gas row in every month and **supersedes**
the state-average seam; `gas_plant_monthly_fuel_pricing` then overwrites from F923 prints on top.
There is no cell left for the seam to reach.

**Consequence: shard F (the 2023 LP ordering check) is CANCELLED, not skipped.** The handoff
anticipated this — *"§2 comes before all of them and may make F unnecessary — say so if it does."*
It does, and more strongly than anticipated: an LP whose *inputs* are proven bit-identical cannot
produce a different *output*. Spending one to confirm a proved identity is the waste rule 29 exists
to prevent. **Pre-registered prediction §5c ("C3b unchanged to 3 decimals") is met by construction,
at exactly 0 decimals of movement.**

### 1b. The retiree window is EXACTLY inert in 2023-2025 — charter task 3, discharged at the input layer

This one was **at genuine risk**. `docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md`
proved the "zero effect on 2023-2025 by construction" claim FALSE for PJM (720 MW of coal retired in
May 2020 redistributed onto live siblings at W H Sammis) and tabulated **NEISO's exposure at 521.5 MW
— Mystic Generating Station**, warning that "each ISO must measure its own rather than assume the
bound is realised."

Measured, `scripts/probes/_neiso_retiree_window_delta.py <year>` — the NEISO fleet built twice off
the keeper recipe, swapping only which `eia860_generator_retired_within_window.parquet` vintage
`paths.active_eia860_dir` serves (committed 2019-window vs a temp copy filtered to
`planned_retirement_year >= 2023`, i.e. pre-`7934e92c`; nothing under `data/raw` touched):

| NEISO | rows (2019-window) | rows (2023-window) | injected | injected nameplate | **injected effective MW-h** | **max abs Δ `pmax`** | **max abs Δ availability** | **max abs Δ `mc_base`** | **Δ effective MW-h** |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 875 | 816 | 59 | 1,696.374 MW | **0.0000000000** | **0.0** | **0.0** | **0.0** | **+0.0000 (+0.000000 %)** |
| 2024 | 865 | 806 | 59 | 1,696.374 MW | **0.0000000000** | **0.0** | **0.0** | **0.0** | **+0.0000 (+0.000000 %)** |
| 2025 | 867 | 806 | 61 | 1,697.490 MW | **0.0000000000** | **0.0** | **0.0** | **0.0** | **+0.0000 (+0.000000 %)** |

**Zero shared rows move, in any of the three years.** Charter task 3's gate — *"max |class-hour delta|
= 0.000000 MW in all three years"* — is met, and met at the **input** layer, which is strictly
stronger than the dispatch A/B the charter specified: if `pmax`, `availability` and `mc_base` are all
bit-identical then the LP is the same LP, so no class-hour delta is possible.

**NEISO's 521.5 MW Mystic exposure is NOT realised.** That is a measurement, not an assumption, and
it confirms the PJM finding's own caution that its table is an upper bound. **This lane therefore
carries only ONE delta against the committed keeper — and, per §1a, that delta is also zero.** The
joint-attribution problem PJM's §5 item 2 has to live with does not arise here.

## 2. G-DRIFT (rule 29(b)) — and the honest limit on it

**The audit cannot be run as specified, for the same reason it could not be run in PJM's lane.**
`neiso106_offerlevel/meta.json` records `git_sha: 70ee7fca`, and that object **does not exist in this
repository** (`git cat-file -t 70ee7fca` → `fatal: Not a valid object name`). The 2026-08-16 history
rewrite (`docs/FINDING-history-rewrite-2026-08-16.md`) invalidated pre-rewrite short shas, and
`docs/governance/citation-commit-map.txt` carries no mapping for this one. The bundle also predates
capx D79 and so carries no `solve_surface.json`. **There is no auditable base, so G-CTRL form 4
cannot be certified in its literal form. Stated, not worked around.**

**What replaces it, and why it is stronger rather than weaker here.** Form 4's purpose is to establish
that the difference between the arm and the committed keeper is the *mechanism* and not HEAD drift.
This lane does not need that inference, because §1a and §1b prove the mechanisms' contribution
**directly and exactly**: at HEAD, arming both changes leaves every LP input bit-identical. So:

- **Any** difference between this lane's 2023-2025 bundle and `neiso106_offerlevel`'s committed
  metrics is **HEAD drift from other lanes' commits**, and **none of it** is attributable to the
  retiree window or the fuel seam. That attribution is established by measurement, not by an audit.
- **No control solve is spent** (rule 29(b): "NO CONTROL SOLVES"). A control at HEAD would build
  provably identical LP inputs to the arm and is therefore not merely disallowed but *uninformative*.
- HEAD drift is **reported at full magnitude** in the RESULT, per rule 1 `[R-STRUCT]`, and routed —
  never absorbed and never used to justify a revert.

## 3. PRE-REGISTERED PREDICTIONS (recorded before the solves; §1a/§1b were measured before them too)

**2023-2025 (train).** Fleet and fuel inputs proven identical, so the *mechanisms* move nothing.
Predicted: every criterion equal to the committed keeper's **up to HEAD drift**, which is the only
live term. Charter task 3: **0.000000 MW**, already proved at the input layer.

**2020 / 2021 (validation touchpoints, `--holdout-authorized`).** The retiree window is LIVE here:
+956.0 MW in 2020 and +949.0 MW in 2021, of which Pilgrim (plant 1590, 673.6 MW nuclear, retired
2019-05) is the bulk, plus 574.2 MW of oil peakers. Pilgrim is retired *before* both years, so what
the window restores in 2020/2021 is the **oil-peaker capacity**, not the nuclear. Predicted:
**prices FALL modestly**; nuclear generation essentially unchanged in both years (Pilgrim is dead by
then); the effect is smaller than PJM's or MISO's by an order of magnitude. The fuel seam is
predicted inert here too, for the same ordering reason, but that is **not** proved for 2020-2022 —
only 2023-2025 were censused — so it is a prediction, not an identity.

**2022 (validation touchpoint).** +201.3 MW, immaterial. **A large 2022 move is a BUG, not a win**
(handoff §4) and will be root-caused rather than reported as a result.

**2019 is REFUSED** — locked-test tier, `final` empty, freeze ACTIVE. Not attempted, not designed
around. The charter's −2.123 TWh Pilgrim measurement for 2019 is **not** evidence produced or
claimed by this session.

**Rule 30(c):** a held-out year NEVER downgrades NEISO's determination, which is the train-tier
(2023-2025) verdict and nothing else.

## 4. THE ZERO-LP INVESTIGATION — settled, and it is the session's headline

`docs/FINDING-neiso-index-vs-delivered-gas-2026-09-09.md`. The 3.24× January-2023 disagreement
between the ISO-NE Algonquin index ($4.73) and the EIA N3045 MA/CT/RI/ME/NH blend ($15.35) is
**settled in the index's favour by a physical falsification**: over 84 months the index never once
implies a marginal heat rate below 7.99 MMBtu/MWh, while the N3045 blend implies one below NEISO's
6.3 MMBtu/MWh CC floor in **13 of 84 months** and, in January 2023, **3.29 MMBtu/MWh — a
~104 %-efficient heat engine**. Corroborated four ways (Jan-23 vs Jan-25; the Algonquin daily prints;
a New England EIA-923 receipt panel that is **one 58 MW peaker**, 0.09 % of the month's burn; and
MA/CT dispersion up to 4.13× inside a single month). **Recommendation: do NOT build a NEISO copy of
ercot-261's corroborator** — the second series fails a physical test and would import panel noise.

## 5. MEMORY (§A6)

`scripts/prepare_solve_container.py` run before the first solve: swap 0 → **8 GiB**, RAM+swap
**23.7 GiB**; `MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` exported into
every solve shell. NEISO's measured single-solve peak is 4.0 GB, the lightest ISO in the program.

## 6. SHARD PLAN — and one declared deviation from the handoff

| shard | years | flags | out-dir | status |
|---|---|---|---|---|
| ~~F~~ | ~~2023~~ | — | — | **CANCELLED by §1a** (proved identity; an LP cannot add to it) |
| T1 | 2023 2024 | `--set gas_electric_power_monthly_level=true` | `results/neiso_fuelvintage_T1` | launched |
| T2 | 2025 | same | `results/neiso_fuelvintage_T2` | queued |
| H1 | 2020 2021 | same + `--holdout-authorized` | `results/neiso_fuelvintage_H1` | launched |
| H2 | 2022 | same + `--holdout-authorized` | `results/neiso_fuelvintage_H2` | queued |

**Deviation, declared:** the handoff (§A1) directs each shard into its own child CCR session. This
lane runs them **in this container, two at a time**. The stated rationale for child containers is
memory — *"so every shard gets its own container and rule 12's ~2-simultaneous RAM cap does not bind
across them"* — and at NEISO's measured 4.0 GB peak against 23.7 GiB, the cap **does not bind at
two**, which is the cap rule 12 `[R-PARALLEL]` actually sets. Years **within** each invocation stay
sequential, always. The deviation also serves rule 31 `[R-RETAIN]`: bundles stay on *this* session's
disk, under this session's control, where the owner's promotion decision can still reach them,
instead of dying with a child container that cannot be messaged.

## 7. GOVERNANCE

- **Rule 31 `[R-RETAIN]`:** every bundle family is `.gitignore`d (`results/neiso_fuelvintage_*/`,
  `results/screen/neiso_ep_level_*/`) — which is what discharges rule 29(c), per that clause as
  amended 2026-09-07. **Nothing is deleted.** The bundles will not survive this ephemeral container;
  the promotion question is asked explicitly in the final report.
- **Rule 16 `[R-ALLYEARS]`:** T1 and T2 are **composed into ONE bundle covering 2023-2025** before
  registration. No fragment is ever registered as a keeper.
- **Rule 30 `[R-TOUCHPOINT-FOLD]`:** H1/H2 are stamped to the keeper
  (`stamp_touchpoint_holdout.py`), then `build_status.py --iso NEISO`. Rule 30(c) binds.
- **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`:** both changes land because they are correct. No gate
  was consulted in choosing them, and no criterion is gated on the target residual.
- **Rule 25 `[R-ISO-SCOPE]` / 28 `[R-MECH-MATRIX]`:** only NEISO's shard
  (`docs/codebase-site/data/mechanism-matrix/NEISO.js`) is written.
- **Rule 22 `[R-HOLDOUT]`:** NEISO holds `complete`; 2020/2021/2022 are spent with
  `--holdout-authorized`. 2019 and H1-2026 are refused and untouched.
