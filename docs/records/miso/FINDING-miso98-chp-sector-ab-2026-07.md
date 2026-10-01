# FINDING miso-98 — the miso-97 CHP sector correction is SOLVED: it is a **net improvement** (C3b FAIL→PASS, C3a better in all three years, C1 PASS in both arms), the pre-registered CC_CHP degradation happened exactly as written, and the pre-registered **CT_CHP prediction is REFUTED** — §2.1's `ρ ≥ f` bound is not structural, because the BTM share is nameplate-weighted on the capacity side and generation-weighted on the benchmark side

**Determination: A/B SOLVED AND REGISTERED. Keeper `2026-07-25-miso-88-egrid-hr`
UNCHANGED.** Both arms are `NOT-YET` probe arms (governance UNATTESTED by
construction — neither is a keeper candidate). The miso-97 TASK 1 data
correction **STAYS IN** and is vindicated on the rubric, not merely tolerated
under rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`.

Registered runs (rule 15 `[R-DASHBOARD]`):

| arm | run id | bundle | `chp_sector` |
|---|---|---|---|
| A | `2026-07-27-miso-98a-sectorabsent-control` | `miso98_chp_sector_A` | all-NaN (pre-`f883346`) |
| B | `2026-07-27-miso-98b-sectormeasured` | `miso98_chp_sector_B` | measured EIA-860, 104 rows |

Both arms are same-HEAD replays of the miso-88 keeper recipe rebuilt from its
`meta.json` (**208 kwargs**, zero unmapped) — not from `run_config.json`'s
curated ~35-key `calibration_flags`. Single delta, verified: A and B differ on
the `chp_sector` column of `thermal_tranches_MISO.csv` **and nothing else**
(all 14 other columns byte-identical, 282 rows each).

---

## 1. The headline — the accurate input IMPROVES the run

Each arm scored against **its own** benchmark (see §4 — this is not a detail):

| criterion | arm A (sector absent) | arm B (sector measured) | |
|---|---|---|---|
| C1 fuel-mix | **PASS** | **PASS** | unchanged |
| C2 system volume | PASS | PASS | unchanged |
| **C3a mean LMP** | FAIL — −4.7 / **−10.1** / **−17.5** % | FAIL — −2.5 / **−7.8** / −15.4 % | **better every year; 2024 flips PASS** |
| **C3b price shape** | **FAIL** — 0.087 / 0.137 / **0.214** | **PASS** — 0.077 / 0.121 / **0.198** | **FAIL → PASS** |
| C3c price tail | FAIL | FAIL | unchanged |
| C4 dispatch corr | PASS | PASS | unchanged |
| C5a CO2 | PASS | PASS | unchanged (no longer scored — see below) |
| C7 diurnal shape | FAIL | FAIL | unchanged |
| C8 forced share | PASS | PASS | unchanged |
| **determination** | NOT-YET | NOT-YET | C3a-2025 / C3c / C7 decide both |

**Rubric version.** Both arms' committed `metrics.json` were scored at **v2.8**,
each against its own benchmark (which is what makes them correct — §5.2).
Rubric **v2.9** landed on main mid-session (`1bd70b3`, owner amendment) and
removes **C5a CO2** from the scored set; re-scoring arm B at v2.9 reproduces
every other status exactly, so the comparison above is unaffected and the C5a
row simply drops out.

**One load-bearing criterion flips FAIL → PASS and no criterion regresses.**
The mechanism is the obvious one: removing 1,405 MW of host self-supply that was
being offered into the LP as cheap grid-facing merchant capacity raises the
clearing price toward the actual. Mean LMP 2023 $31.33 → $32.06 against an
actual $32.87.

This was **not** the pre-registered expectation, and it is worth stating
plainly: miso-97 §5.1 framed the arm as "a way-station, not a keeper
candidate" whose CC_CHP fit would degrade. The class fit did degrade exactly as
predicted (§2) — and the run still got better, because the correction's price
effect dominates its class-volume effect.

---

## 2. CC_CHP — the pre-registered degradation, confirmed

| year | A model | A bench | A err | B model | B bench | B err | abs. miss A → B |
|---|---|---|---|---|---|---|---|
| 2023 | 29.423 | 28.042 | **+4.9 %** | 23.827 | 21.311 | **+11.8 %** | +1.38 → +2.52 TWh |
| 2024 | 29.556 | 27.865 | **+6.1 %** | 23.701 | 21.339 | **+11.1 %** | +1.69 → +2.36 TWh |
| 2025 | 27.791 | 24.146 | +15.1 % | 22.317 | 16.947 | +31.7 % | +3.65 → +5.37 TWh |

**PREDICTED, and not grounds to revert** (rules 1 / 14). Note what the C1 gate
says though: the absolute miss stays **well inside** the ±min(2 % ISO-load,
8 TWh) band in both arms, so CC_CHP **PASSes C1 in arm B too** (+2.52 TWh,
share +0.5 pp). The degradation is real in percentage terms and immaterial to
the gate. §2.1's `ρ ≥ f` reasoning holds here: model fell to 0.810 of arm A
against an in-LP capacity cut to 0.756, so CC_CHP is partly economic and the
ratio rises.

2025 is quoted for completeness only — its EIA-923 vintage is the monthly early
release (11 of 23 prior CC_CHP plants missing, 52 % reporting) and the scorer
**SKIPS** it for exactly the miso-97 §2.2 coverage-trap reason.

---

## 3. CT_CHP — the pre-registered prediction is REFUTED, and §2.1's bound is not structural

miso-97 §5.1: *"CT_CHP should improve or be flat, from −20.6 % toward zero."*
§2.1 backed it with a claimed structural bound (`ρ ≥ f`, so "raising the BTM
share can only move a class UP relative to its meter"), and §6 DO-NOT-REDO
forbade *"re-arguing that raising the BTM share could deepen a CHP under-run."*

| year | A err | B err | verdict |
|---|---|---|---|
| 2023 | −21.8 % | **−33.3 %** | **deepens — refutes the bound** |
| 2024 | −20.9 % | **−32.9 %** | **deepens — refutes the bound** |
| 2025 | +29.4 % | +15.7 % | moves toward zero (as predicted) |

**Why the bound fails, measured.** §2.1 assumed capacity and the benchmark
subtrahend are rescaled by *the same* linear factor `(1 − s)`. They are not,
because **`s` is applied to nameplate on the capacity side and to net
generation on the benchmark side**, and MISO's high-BTM CT_CHP plants run at a
*lower* capacity factor than its low-BTM ones:

* capacity-weighted share (miso-97 §1.2): 35.0 → 65.5 %, in-LP 1,707 → 906 MW,
  ratio **0.531**
* generation-weighted share (measured from the arms' own `btm.parquet`, total
  20.795 TWh both arms): 33.0 → 58.8 %, bench 13.925 → 8.562 TWh, ratio
  **0.615**
* model 10.888 → 5.707 TWh, ratio **0.524** ≈ the capacity ratio — CT_CHP is
  capacity/floor-bound, so `ρ = f_capacity`, and `f_capacity (0.531) <
  f_bench (0.615)`.

The model loses 47.6 % of the class while its meter loses only 38.5 %, so the
under-run deepens. `ρ ≥ f` is true only when the two `f`s are the same number,
which requires the BTM share to be uncorrelated with capacity factor within the
class. In MISO CT_CHP it is not. **This is a correction to miso-97 §2.1 and
§6, not a new mechanism** — and it is the reason the A/B was worth six solves
rather than a proof.

CT_CHP is not gated by C1 (excluded from the class gate) and its absolute miss
actually *improves* slightly (−3.04 → −2.86 TWh in 2023), because both sides
shrank.

---

## 4. ST_CHP, the non-CHP control, and peers

**ST_CHP — reported, never gated** (rule 20 materiality: 0.4–2.7 TWh against a
12.8 TWh line). It moves the most in relative terms and in the *right*
direction: populating the sector moves it off the no-sector `CHP_ST_BTM_PCT`
90.0 fallback onto its measured 63.6, so model energy rises 0.521 → 2.285 TWh
(2023) and the C1 miss shrinks **−4.72 → −3.05 TWh**. Both arms PASS.

**Non-CHP control.** The delta enters only through `chp_btm_pct`, so every
non-CHP move is an indirect merit/price response. All of them improve or are
flat:

| class | A err (23/24/25) | B err (23/24/25) |
|---|---|---|
| CC_REGULAR | −7.0 / −3.2 / −8.3 | −5.4 / −1.5 / −5.9 |
| CT_PEAKER | −22.4 / −11.6 / −10.8 | **−14.4 / −2.5 / −1.8** |
| COAL_PRB | −0.7 / −0.4 / +3.8 | +0.7 / +0.8 / +4.7 |
| COAL_LIGNITE | −14.0 / −19.9 / −7.3 | −12.5 / −19.3 / −6.7 |
| ST_GAS | +9.7 / −13.3 / +0.9 | +16.2 / −8.3 / +6.8 |

CT_PEAKER is the big one — the 1.4 GW of withdrawn cheap CHP is replaced by the
peaking fleet that actually served that energy, closing a −22 % under-run to
−1.8 % in 2025. That is a coherent market story, not a residual absorption.

**Peers: exactly zero, by construction.** The delta is one column of
`thermal_tranches_MISO.csv`, a file no other ISO's solve reads; miso-97 §1.4
measured the peer in-LP delta at **0.0 MW** on PJM/CAISO/NYISO/NEISO. No peer
solve was spent proving a file that is not read cannot have an effect.

---

## 5. TWO CONTAMINATION TRAPS this session hit and corrected — DO NOT REDO

Both were caught by the arms disagreeing with their own solve-time artifacts,
and both would have inverted the conclusion. They are the miso-94 §5 trap
displaced *downstream of the solve*.

1. **Every post-solve step recomputes the benchmark from the artifact on disk
   at the time it runs** — `pjm119_merge_year_chain.py` (which rebuilds
   `btm.parquet`), `--rebuild-benchmark`, `legitimacy_diagnostics.py` and
   `dashboard_add_run.py` all do. Running arm A's post-processing while arm B's
   artifact was staged gave arm A **arm B's BTM hold-out** (CC_CHP bench 21.311
   instead of 28.042), which reported CC_CHP as *improving* +38.1 % → +11.8 %
   — the exact opposite of the truth. **Post-processing must be staged per arm**
   (`_miso98_postproc` recipe: stage artifact → merge → rebuild-benchmark →
   diagnostics → register).
2. **`frontend/data/backcast/bench/<ISO>/<year>.json.gz` is shared per
   (ISO, year), not per run.** When an A/B delta *moves the benchmark* — as any
   BTM-share change does — the two arms cannot both be represented: the
   last-registered arm owns the bench and the other is scored against the wrong
   actual. Arm A first scored C1 **FAIL** (+8.11 TWh) purely because arm B had
   registered after it. Each arm's honest scorecard requires registering it
   last and reading the verdict immediately. **The committed dashboard state is
   arm B's**, which is correct — arm B is the landed on-disk artifact.

Consequence for readers: **arm A's numbers on the live dashboard are scored
against arm B's benchmark.** Arm A's true, own-bench scorecard is §1 of this
document; its sidecar definition says so.

---

### 5.1 CONSEQUENCE FOR THE KEEPER — surfaced, not silently absorbed

The shared bench is not only an A/B nuisance: **registering arm B re-based the
committed MISO benchmark for every registered MISO run, the keeper included.**
`bench/MISO/<year>.json.gz` had carried the pre-correction (35.0 % merchant
default) BTM hold-out since 2026-07-25; it now carries the measured one, because
that is what is on disk. This session is the first MISO registration since
`f883346` landed, so it is the first to move it.

The keeper `2026-07-25-miso-88-egrid-hr` **solved with the old 35.0 % share and
is now scored against the measured hold-out.** Its C1 CC_CHP miss therefore
inflates from ≈ +1.4 TWh to **+7.77 TWh — 97 % of the ±8 TWh gate** — with no
change to the keeper's dispatch at all. It still PASSes, and its
**determination is unchanged (NOT-YET, decided by C7 COAL_PRB shape, unrelated
to CHP)**, so nothing about the keeper's standing moves today.

This is the right basis to keep (rule 14 `[R-ACCURATE]`: the benchmark should
hold out the measured host share, not an unsourced default) and the wrong pair
to leave standing indefinitely: model and meter are on different BTM bases for
the keeper alone. **Arm B is precisely the keeper recipe re-solved on the
corrected data**, so the natural resolution is to promote it once it can carry a
governance attestation. That is an owner decision and this session does not take
it — no keeper shard was edited beyond the mandatory `build_status.py --iso
MISO` refresh that S1 requires.

## 6. TASK 3 (heat rate) — judged against the POST-A residual, BUILT AS A MEASUREMENT, and **NOT ARMED**: the design's own non-optional step is unobtainable for CHP

The post-correction residual is what caiso-128 §6 must now answer to:
**CC_CHP over-delivers +11.8 / +11.1 %, CT_CHP under-runs −33.3 / −32.9 %.**
The 2026-07-08 tension is therefore *not* resolved by TASK 1 — it is sharper.
Raising CHP heat rates 30 % makes CHP dearer, which helps CC_CHP and hurts
CT_CHP.

**On the residual alone the design still looks well-targeted**, because
coverage is asymmetric in exactly the helpful direction. Built and measured
(`scripts/data/derive_campd_chp_heat_rates.py`, committed, ISO-generic):

| class | plants covered | MW covered | model (eGRID) | **measured power-only** | model error |
|---|---|---|---|---|---|
| CC_CHP | 14 / 24 | 5,852 / 7,036 (**83.2 %**) | 6.72 | **9.69** | **−30.7 %** |
| CT_CHP | 4 / 52 | 274 / 2,625 (**10.4 %**) | 7.28 | 10.02 | −27.3 % |
| ST_CHP | 1 / 55 | 425 / 1,935 (21.9 %) | 11.50 | 11.74 | −2.0 % |

The mechanism reaches **83 % of the over-delivering class and only 10 % of the
under-running one**, so it cannot do much damage to CT_CHP even in principle.
It also confirms caiso-128 §4's central claim directly: the error is in **both
directions per plant** — 16 of 19 rows understate (Midland Cogeneration
Venture, 1,479 MW: model 6.89 vs measured 11.23), but 3 overstate (plant 64854:
model 12.16 vs measured 7.24, **+68 %**). No single topping factor can be right
for both, which is why the 1.8× is not armed for MISO.

**Two corrections to the charter's feasibility numbers**, both measured with
the design's own definitional gates rather than the looser feasibility
instrument:

* **CT_CHP MW coverage is 10.4 %, not 38 %.** Under `opTime ≥ 0.99`,
  `grossLoad > 0.5 × p95` and ≥ 50 qualifying unit-year hours, 48 of MISO's 52
  CT_CHP plants never clear the window — they are small industrial cogens.
* **ST_CHP coverage is 21.9 %, not 0 %** — one 425 MW plant (1393) reports, and
  it measures **accurate to −2.0 %**, which independently supports keeping
  ST_CHP on the existing fallback.

### 6.1 The blocking defect — and why the gate is deliberately not wired

caiso-128 §6(a) requires the plant's **own same-year measured gross→net ratio**
and states the reconciliation "is not optional — it is what this session got
wrong first". Measured: **it fires on 0 of 19 rows.**

```
factor_source:  class_default 16 rows / 5,946 MW   pooled 3 rows / 604 MW
                same_year      0 rows /     0 MW
```

The reason is structural, not a bug in the derive: `compute_parasitic_factors`
resolves a plant to `class_default` whenever `net923/gross_CEMS` falls outside
its plausibility band — and for a cogen it always does, because EIA-923 net
includes the **host-served** generation that CEMS never meters. The one class
the design targets is the one class the committed parasitic artifact cannot
reconcile.

So 94 % of the covered MW currently divides by a **2.5 % class constant**
against MISO's own measured CHP station-service of **8.0 % (CC_CHP), 23.7 %
(CT_CHP), 30.8 % (ST_CHP)** (miso-97 §3). The artifact as derived is therefore
on a near-**gross** basis, understating the net rate by ~5.5 pp (CC) to ~28 pp
(ST) — precisely the error caiso-128 warns about, and an unsourced hand
constant on the critical path (rule 24 `[R-REGISTRY]`).

**Judgment: the measurement is committed; the `ScenarioConfig` gate is NOT
wired and nothing reads the artifact.** Arming a known-wrong-basis heat rate to
chase a residual would violate rule 14's "reconciled real data, never a guess"
exactly as the design itself anticipates. The correct next step is a CHP-specific
gross→net derivation that separates station service from host supply — note
that host supply is *already* held out separately by `chp_btm_pct`, so reusing
`net923/gross` here would double-count it. That is its own delta and its own
session (rule 19 `[R-ONE-MECH]`).

---

## 7. DO-NOT-REDO

* Re-running the A/B — six solves, both arms registered, numbers above.
* **Using the registered dashboard scorecard for arm A** (§5.2 — it carries arm
  B's benchmark). Arm A's own-bench scorecard is §1.
* **Post-processing an arm without staging its own tranche artifact** (§5.1) —
  four separate steps recompute the benchmark from disk.
* Re-asserting miso-97 §2.1's `ρ ≥ f` bound or its §6 DO-NOT-REDO line that
  raising the BTM share cannot deepen an under-run (§3 — refuted by LP, with
  the nameplate-vs-generation weighting attributed).
* Re-measuring MISO CHP CEMS coverage with the looser feasibility instrument
  (§6 — 10.4 % CT_CHP / 21.9 % ST_CHP under the design's own gates).
* **Arming `measured_chp_heat_rates` on the current artifact** (§6.1 — near-gross
  basis, `same_year` factor fires on 0/19 rows).
* Adding MISO to `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` / the 1.8× topping factor
  (§6 — measured over-correcting 3 of 19 MISO plants, one by +68 %).
* The `--reuse-solved` form of a three-year MISO bundle (§8) — OOMs at 15.9 GB
  on the assembly stage. Use per-year processes into one dir +
  `pjm119_merge_year_chain.py`.

## 8. Solve hygiene

* Four clean partitions regenerated first; every solve log carries the healthy
  tell `seasonal CIL/CEL interface caps on 5 zone group(s) … static summer
  fallbacks replaced` (miso-93 correction 1).
* **`--reuse-solved` OOM'd at 15.9 GB** (anon-rss, `oom-kill` confirmed) on the
  three-year assembly stage — the 2025 LP itself finished (`Solve: 644.063s`);
  the kill was `_load_prior_bundle_tables` holding the reused years alongside
  the fresh one. Re-run as one process per year into a single bundle dir, then
  `pjm119_merge_year_chain.py`; peak then stays at the single-year peak.
* Chain integrity verified: `system_2023` / `class_hourly_2023` /
  `storage_2023` byte-identical across the staged legs.
* A-arm control check vs the registered keeper: CC_CHP +1.16 / +4.34 / +0.41 %,
  CT_CHP −0.56 / −0.49 / −0.26 %, CC_REGULAR ±0.4 % — the classes under test
  reproduce. ST_GAS (+8.5 to +12.3 %) and CT_PEAKER (−4.5 to −8.0 %) are the
  documented post-CAMPD-envelope drift (miso-93 §3 attributes 73.5 % of the
  11,614 removed GW-days to ST_GAS), which is why arm A cannot be the
  registered keeper bundle (miso-92 §7).
* Rule 22 `[R-HOLDOUT]` honoured: 2023–2025 only, no marker, freeze active.
* `audit_keepers.py --check` is **GREEN** at this HEAD (0 failures, 0 warnings)
  — the miso-97 §5 blocker #4 (`status/PJM.js` stale) was cleared upstream by
  `38d00fc`. Registration was not blocked.

Next number: **miso-99.**
