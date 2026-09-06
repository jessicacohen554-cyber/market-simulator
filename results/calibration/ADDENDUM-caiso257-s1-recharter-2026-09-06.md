# ADDENDUM to PRECOMMIT-caiso255 — caiso-257: the owner **RE-CHARTERS S-1 on a plant-deduplicated estimator** and rules the CT-only partition arm **WANTED**. The new gate is fixed to a number HERE, before the artifact pair is re-applied and before any LP is spent. **The comfort this document has to buy off: the prior screen's answer is already PUBLISHED, so this re-screen cannot surprise anyone — what the re-charter buys is a correct estimator, not a fresh unknown, and this document says so at the top rather than in a footnote.**

**Session caiso-257, 2026-09-06.** Branch
`claude/caiso-257-backcast-calibration-5kj8t9` off `main` `2485e611`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED** (rubric v3.6). Rule 22
`[R-HOLDOUT]`: **2023–2025 only**; CAISO holds no `complete`/`final` marker
(re-raised this session and **again declined** — see §8.6); the holdout spend
freeze is ACTIVE.

`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` and its addenda,
including `ADDENDUM-caiso256-partition-screen-2026-09-06.md`, stand unchanged
except where this document **replaces S-1's number**. Nothing else is relaxed,
re-scoped or re-run to a pass.

---

## §1 — THE TWO RULINGS

`FINDING-caiso256-partition-screen-2026-09-06.md §5` put two questions to the
owner. Both are answered, 2026-09-06:

1. **"Is the arm wanted at all, given §3?"** — the +219.8 GWh landed on
   p57482 / p57515 / p57555 (462 / 375 / 281 GWh) and **not** on Panoche
   (172), deepening the `caiso-252 §3.3` mis-allocation. **Ruling: YES,
   PURSUE IT.** The basis stated in the ask and adopted here: the repair is
   right about the **offer** — it is a measured de-contamination under rule 14
   `[R-ACCURATE]` — while the **plant allocation** is a separate open object
   (Panoche, `caiso-252 §7 #4`, which forbids reaching it by re-pricing the
   class and is untouched by this arm). Adopting a correct offer and leaving a
   known allocation miss open is coherent; pretending the arm closes the CT
   volume miss would not be, and this session never claims it does.
2. **"Re-charter S-1 on a plant-deduplicated estimator?"** — **Ruling: YES.**

**What the second ruling does NOT do.** It does not re-score caiso-256, whose
verdict stands as recorded (S-1 FAIL on the registered count; the arm died
there and the artifact was reverted). It does not relax S-2, S-3 or S-4, or
the exclusion of C3a. It does not change the promotion basis. And it is not a
finding that the arm passes: the re-chartered gate is registered here and the
arm is screened against it, and it can still die.

## §2 — THE NEW ESTIMATOR, AND ITS BAND, FIXED BEFORE THE ARTIFACT IS RE-APPLIED

### §2.1 — The defect in the registered estimator, measured not argued

`ADDENDUM-caiso256 §4` registered

> ΔE_implied = Σ_i pmax_i × #{ t : mc_new_i ≤ λ_{z(i),t} < mc_old_i }

over every CT_PEAKER tranche whose P0 offer fell, λ the keeper's committed P1
zonal price. **784 of 828** tranches fell across **79 plants**, and sibling
tranches of one plant (`p57482_econc00 … econc04`, mc 73.5–76.3 $/MWh) carry
bands that all contain the same hours. The count therefore charges one plant's
capacity up to five times in one hour, while in the LP the first tranche to
clear lowers λ and the rest do not. Registered floor 311.8 GWh; measured rise
**+219.8 GWh**; over-count **4.26×**.

### §2.2 — The re-chartered estimator

> **ΔE_dedup = Σ_plants Σ_t max_{i ∈ plant, band_i ∋ λ_t} pmax_i**
>
> i.e. the same band-membership test, but at most **one tranche's worth of MW
> per (plant, hour)** — the largest qualifying tranche of that plant in that
> hour — so a plant's capacity is displaced at most once per hour.

It is already implemented and committed
(`scripts/probes/_caiso256_s1_implied_displacement.py:164-176`, the
`plant_hours` / `np.maximum` block), was labelled `POST_HOC_…` there, and is
promoted by this ruling from a reported number to **the** S-1 operand.

**Why it is defensible on its own construction, which is the only ground it
may be adopted on.** One plant cannot displace its capacity twice in one hour.
That is a statement about the LP's feasible set, true before any result was
seen, and it is the whole argument. **It is NOT adopted because it passes** —
that inversion is the selection rule 29 `[R-SCREEN]` and rule 1 `[R-STRUCT]`
exist to forbid, and §3 below refuses it explicitly.

**Its bias, disclosed in the same breath and in the direction against this
session's interest.** The `max`-per-(plant, hour) form is biased **LOW**
against a reading in which several tranches of one plant genuinely clear
together and the whole plant ramps: the true first-order displacement of such
a plant-hour is the *sum* of its in-band tranches, which this estimator
replaces with their maximum. So the registered count is biased high, this one
is biased low, and the truth is bracketed between them. The factor of 3 is
carried unchanged as the absorber of both directions; it is not widened.

### §2.3 — THE BAND, FIXED TO A NUMBER HERE

`ΔE_dedup` was measured at **261.5 GWh over 79 plants** and is **already
published** (`FINDING-caiso256 §2`), so there is nothing left to back-fit. The
gate is therefore written as a fixed numeric interval rather than as "whatever
the probe returns":

> **S-1 (re-chartered): CT_PEAKER 2023 energy RISES within
> `[87.2, 784.5]` GWh** — ΔE_dedup 261.5 GWh, factor 3 both ways, against the
> keeper's 2023 CT_PEAKER 1.6447 TWh. **FAIL ⇒ the arm dies here**, and this
> time there is no third estimator: a second re-charter is refused in advance
> by §8.3.

`scripts/probes/_caiso256_screen2023.py::S1_BAND_GWH` is edited from
`(311.8, 2806.4)` to `(87.2, 784.5)` and that edit is **committed together
with this document, before the artifact pair is re-applied and before the
solve**, so the scorer on disk carries the new gate at every moment the LP is
running.

## §3 — THE DISCLOSURE THAT GOVERNS THIS WHOLE SESSION

**This re-screen cannot surprise me, and I will not present it as though it
could.** `FINDING-caiso256 §1` publishes the arm's 2023 answer on every gate:
+219.8 GWh, S-2 ≤ 0.0027 %, no C1 flip, C4 0.879 / 0.287. **+219.8 sits inside
`[87.2, 784.5]`.** I knew that when I put the re-charter to the owner, the
owner knew it when they granted it — `FINDING-caiso256 §2` states it in the
words "on a plant-deduplicated estimator the arm would have sat inside a
factor-3 band with room to spare" — and it is restated here so no later reader
has to reconstruct it.

**What the re-charter therefore buys, honestly stated:**

* a **correct** S-1 operand, adopted on its construction (§2.2) by the owner,
  who is the only party entitled to make that call after the fact;
* a **fresh solve at this session's HEAD** (`2485e611`, 10 files past
  `c274f1a0`), which re-establishes form-4 comparability at the sha the arm is
  actually solved at — the audit `PRECOMMIT-caiso255 §6.2` says is the one
  that binds;
* a **reproduction check** on caiso-256's screen (§4), which is the one thing
  in this session that genuinely can fail.

**What it does not buy: any claim of out-of-sample surprise.** No sentence in
the FINDING this session writes will describe S-1's re-screened pass as
evidence *for* the mechanism. The evidence for the mechanism is, and stays,
what `PRECOMMIT-caiso255 §3.1` registered before any of this: **G-BIMODAL plus
the G1 capacity reconciliation** — a 30 % CT-bucket capacity excess collapsing
to 3 % against the class's own published fleet — two statistics that contain
no price and no residual.

## §4 — REPRODUCTION GATES: the part that can actually fail, and stops the session if it does

| # | gate | threshold | if it fails |
|---|---|---|---|
| **R-1** | re-applying `df277e89` restores the three artifact files to their `df277e89` blob shas **byte-exactly** | exact sha match on all three | stop; the pair is not what history says it is |
| **R-2** | the re-run S-1 probe reproduces **ΔE_dedup = 261.5 GWh over 79 plants** and **ΔE_implied = 935.5 GWh**, 784 of 828 tranches fallen, 0 risen | ±0.5 GWh / exact counts | **STOP BEFORE THE LP.** A deterministic estimator on the same artifact bytes at a HEAD whose LP inputs are bit-identical (§6) that does not reproduce means one of the two runs is not what it claims — the `PRECOMMIT-caiso255 P-2` standard, applied to this session |
| **R-3** | the 2023 screen reproduces caiso-256's CT_PEAKER **+219.8 GWh (1.6447 → 1.8645 TWh)** | ±5 GWh | the solve path drifted between `c274f1a0` and `2485e611` in a way §6's identity measurement did not see. **STOP and report**; do not proceed to the full span, and do not re-score the difference away |

R-3 is the honest test of §6's G-DRIFT claim, and it is registered as a
**stop**, not as a tolerance to be widened afterwards.

## §5 — EVERY OTHER GATE, CARRIED UNCHANGED

Verbatim from `PRECOMMIT-caiso255 §7.2` / `ADDENDUM-caiso256 §5`. Only S-1's
number moves.

* **S-2 — footprint confinement.** nuclear / hydro / wind / solar each move
  **< 0.5 %** of keeper annual energy. Storage, imports, CC classes reported.
* **S-3 — C1 stop gate.** Arm class TWh vs the keeper `_verdict.json` C1
  records' actual ± the same tolerance (±5.27 TWh, ±3 pp share, 2023). A class
  PASS → FAIL flip STOPS and ESCALATES.
* **S-4 — C4 stop gate.** Gas r / NRMSE by the caiso-252 construction against
  the HEAD-scored keeper **0.880 / 0.285**; a flip is r < 0.70 or NRMSE > 0.30
  — STOPS and ESCALATES.
* **C3a is EXCLUDED IN BOTH DIRECTIONS** — the target residual; it can neither
  kill the arm nor promote it, and its −0.16 pt move is barred from being
  quoted as evidence (`FINDING-caiso256 §7 #4`).
* **`co2` is never differenced** — `import_co2_tons` is the one LIVE hunk on
  the chain and `co2` is not in `CRITERIA`.
* **The screen may kill, never promote** (rule 29).

## §6 — G-DRIFT AT SOLVE-TIME HEAD (`fa23c1f7 → 2485e611`), BY MEASUREMENT

Rule 29(b), form 4, **no control solve**. The instrument is the committed
`scripts/probes/_caiso255_gdrift_identity.py`, re-run at this session's HEAD
with the artifact pair in its reverted (`fa23c1f7`) state — which is what
`main` carries at `2485e611` — so the measurement isolates the code:

> `--keeper-sha fa23c1f7` → artifact
> `results/calibration/_caiso257_gdrift_at_solve.json`
> **RESULT RECORDED IN §6.1 BEFORE THE SOLVE IS LAUNCHED.**

The incremental scope `c274f1a0 → 2485e611` is **10 files, +616 / −44**, and
every one is read as INERT for a CAISO backcast with its reason cited:

| file | Δ | verdict |
|---|--:|---|
| `config/scenarios.py` | +95 | **INERT** — two added fields, `miso_gas_variable_transport` and `miso_seam_neighbour_anchored_ladder`, both `bool = False`, both absent from the keeper's recipe (they post-date it); no pre-existing default moved |
| `model/interchange/spec.py` | +75 | **INERT** — a new `MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR` / `…_POOLED` constant pair, read only through the MISO seam-ladder path |
| `data/fuel/basis/miso.py` | +141 | **INERT** — gated on `miso_gas_variable_transport` (default off) |
| `model/interchange/miso.py` | +29 | **INERT** — the same MISO seam path |
| `scripts/run_calibration.py` | +30 | **INERT** — a `ValueError` guard plus a `neighbour_anchored` kwarg inside the `reference_price_interface and iso in INTERFACE_NEIGHBORS` block; CAISO is not a MISO seam ISO and the keeper does not carry the flag |
| `capacity_evolution/evolve.py`, `retirements.py` | +135 | **INERT — UNREACHED**: capacity evolution; a `mode="backcast"` run never calls `evolve_fleet` (`results/cache.py:337-339`) |
| `results/cache.py` | +20 | **INERT** — cache-epoch **docstring** only (capx D78); a replay never hits a cache |
| `data/raw/reference/miso_gas_variable_transport*.csv` | +135 | **INERT** — MISO input files, read only under the default-off flag |

Instrument 3 (the fleet-array rebuild at both shas) is what settles this,
because a reading can miss a hunk and a bit-comparison cannot.

### §6.1 — THE MEASUREMENT, RECORDED BEFORE THE ARTIFACT PAIR IS RE-APPLIED

> `PYTHONPATH=.:src uv run python scripts/probes/_caiso255_gdrift_identity.py --keeper-sha fa23c1f7 --out results/calibration/_caiso257_gdrift_at_solve.json`
>
> **VERDICT: ALL LP INPUTS BIT-IDENTICAL**, all three years.

Two `fleet_only` rebuilds per year on the keeper's own recipe — `market_sim`
imported from a sparse worktree at `fa23c1f7` in one arm and from HEAD
`2485e611` in the other, sharing ONE `data/` tree by symlink so both read
identical bytes off disk — differenced by sha256 over the raw array bytes:

| year | units | `unit_ids` | `mc_base` | `pmax` | `pmin` | `min_gen` | `availability` | `heat_rate` | `emission_rate` | `vom` | demand (7×8760) |
|---|--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 2023 | 1,662 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| 2024 | 1,656 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| 2025 | 1,661 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |

**Reported in full, because a bit-identity verdict is only worth what its
reporting is.** Instruments 1 and 2 do flag movement, and instrument 3 is what
settles each: `ScenarioConfig` **794 → 810** fields, **16 added** (every one
absent from the keeper's recipe) and **6 pre-existing defaults changed** —
`campd_bins_path`, `control_retrofit_path`, `plant_emission_rates_path`,
`plant_emission_rates_v2_path`, `plant_registry_path` (the path-registry
relocation) and `ccs_retrofit_vom_adder` (a capacity-evolution step-2 field a
`mode="backcast"` run never reaches). Constants **267 → 275**, 8 added and 7
changed (`CAMPD_BINNING_ISOS`, `DATACENTER_ADDITIONS_MW`,
`DATACENTER_ZONE_SHARE`, `DEMAND_GROWTH_RATES`, `EIA930_PS_FOLDED_INTO_WAT`
— `{MISO, PJM}`, CAISO absent — `ELECTRIFICATION_LAYERS`,
`RGGI_MEMBER_STATES_BY_YEAR`). **Every one of them is settled empirically
rather than argued**: the five path fields and `DEMAND_GROWTH_RATES` are on
live backcast paths and the arrays and the 7×8760 demand matrix come back
bit-identical anyway.

**⇒ G-CTRL FORM 4 STANDS at the solve sha. No control solve is spent, and the
artifact pair is the only thing that will differ between the arm and the
keeper.** What this measurement does not cover is LP *construction* and
*solve*, closed by the table above and by `PRECOMMIT-caiso255 §9.4`, plus
`--no-p1-basis-seed`/`MARKET_SIM_P1_BASIS_SEED=0` (§7.3), which makes the one
LIVE solve-path hunk **unreached** rather than asserted inert.

## §7 — PRECONDITIONS THE ARM MUST MEET OR BE DISCARDED

Unchanged from `ADDENDUM-caiso256 §3`, checked from the arm's own
`run_config.json` rather than asserted. `data/clean` is gitignored and was
EMPTY at session start; `scripts/data/curate_capacity_deliverability.py`
(5 partitions) and `curate_hydro_plant_modes.py` were run **before any solve**.

1. `resolved_inputs.seam_import_cap.source == "mic_partition"`, **16,055 MW**
   in 2023 (16,452 / 16,148 in 2024 / 2025). An arm that solved on the baked
   7,500 MW fallback is **not form-4 comparable and is thrown away**.
2. `resolved_inputs.hydro_plant_modes.partition_present == true` (flag off, as
   the keeper); `campd_unit_outages` and `thermal_tranches` sha256 identical to
   the keeper's.
3. `MARKET_SIM_P1_BASIS_SEED=0` and the driver log reads
   **"P1 route: COLD REBUILD"** (`PRECOMMIT-caiso255 §6.1`: the seed is
   turned OFF rather than argued inert).

## §8 — STOP RULE

1. **R-1, R-2 or R-3 fails ⇒ STOP**, before the LP for R-1/R-2, before the
   full span for R-3. Report and revert.
2. **S-1 fails on `[87.2, 784.5]` ⇒ the arm dies**, the artifact pair is
   reverted to `fa23c1f7`, and the object closes.
3. **NO THIRD ESTIMATOR.** A second re-charter of S-1 is refused here, in
   advance, whatever this screen returns. One estimator was replaced, by the
   owner, on a construction argument, with the prior result public; doing it
   twice would be estimator-shopping however it were dressed.
4. **No gate is relaxed, re-run to a pass, or redefined after its result.**
   S-2 keeps 0.5 %, S-3 and S-4 keep their tolerances, R-3 keeps ±5 GWh.
5. **No threshold in the derive is retuned**; the derive is not re-run at all
   — the artifact pair is restored from `df277e89` by `git checkout`, byte for
   byte, and is **never hand-edited**.
6. **No `complete` marker.** Re-raised this session under rule 22 and
   **declined by the owner ("not now — keep raising it")**. CAISO stays
   2023–2025; the freeze stays active.
7. `frontend/data/forecast/program-status.json`'s stale top-level
   `isos.CAISO.keeper` is **not touched**; the owner ask stays open.
8. **THE PROMOTION BASIS IS `PRECOMMIT-caiso255 §5(8)`, UNCHANGED:** promoted
   iff **(a)** S-1 / S-2 pass, **(b)** no **load-bearing** criterion
   (C1 / C2 / C3a / C3b) regresses to a **new failure** in any of the three
   years, and **(c)** governance holds (C6 attested, C8 passes). **C3a and C4
   enter (a)–(c) in neither direction.**

## §9 — SEQUENCE AND LAUNCH RECORD

Executed strictly in this order; each step's artifact is committed before the
next begins.

1. This document + the `S1_BAND_GWH` edit — **pushed first**.
2. `git checkout df277e89 -- data/raw/_validation-source/caiso_offer_curve_measured.json data/raw/_validation-source/caiso_offer_surface_condbinned.json data/raw/_validation-source/caiso_offer_surface_summary.csv` → **R-1**.
3. `scripts/probes/_caiso256_s1_implied_displacement.py` → **R-2**.
4. The 2023 screen, ONE LP-year:

```
MARKET_SIM_P1_BASIS_SEED=0 PYTHONPATH=.:src uv run python scripts/replay_keeper.py \
    results/calibration/caiso252_b1_notrim \
    --out-dir results/calibration/caiso257_screen2023 --years 2023 \
    --note "caiso-257 rule-29 SCREEN of the CT-only partition on the RE-CHARTERED S-1 (owner ruling 2026-09-06): keeper replay with the df277e89 artifact pair on disk; throwaway, deleted before merge"
```

5. `scripts/probes/_caiso256_screen2023.py` → **R-3, S-1, S-2, S-3, S-4**.
6. If and only if every gate clears: **ONE** invocation
   `--years 2023 2024 2025` into `results/calibration/caiso257_ctonly`
   (rule 16 `[R-ALLYEARS]`), registered the same session (rule 15
   `[R-DASHBOARD]`), promoted iff §8.8 holds.
7. Both screen bundles are **DELETED before this PR merges** (rule 29(c));
   every number they produce lives in the FINDING.

**Deliverables:** this ADDENDUM; the `S1_BAND_GWH` edit; the restored artifact
pair; `_caiso257_gdrift_at_solve.json`; the re-run S-1 artifact; the screen
gate table; the full-span bundle + its registration + `gen_caiso257_attestation.py`
(written from the caiso-252 pattern — the caiso-256 draft was deleted with its
bundle); the FINDING; the `docs/calibration-log/caiso.md` entry; the rule-28
CAISO matrix-shard stamp; and, on promotion, `keepers/CAISO.json` +
`build_status.py --iso CAISO` + the `calibration-keeper-auditor` run.
