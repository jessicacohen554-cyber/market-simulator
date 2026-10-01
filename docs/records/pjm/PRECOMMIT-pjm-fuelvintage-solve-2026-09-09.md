> **TWO SESSIONS RAN THIS LANE CONCURRENTLY, AND BOTH RECORDS ARE KEPT.** A sibling
> `pjm-fuelvintage-1` session (PRs #5741 / #5748 / #5759) landed its own PRECOMMIT at
> `docs/PRECOMMIT-pjm-fuelvintage-2026-09-09.md` before this branch merged; it reached the SAME
> G-DRIFT conclusion independently (the keeper's `git_sha` is dead, so rule 29(b) cannot be run)
> and left the matrix cell at `O` — it did not complete an A/B, register a run, or promote.
> **This document is the PRECOMMIT of the session that solved the span, registered
> `2026-09-09-pjm-fuelvintage-ep-level` and promoted it**; the sibling's is kept verbatim at the
> original path. Neither supersedes the other as a record — they corroborate each other on the
> control posture, which is worth more than either alone.

# PRECOMMIT — PJM: the measured monthly gas LEVEL + the 2019-2022 retiree window

**Session:** `pjm-fuelvintage-1` · **Date:** 2026-09-09 · **Branch:** `claude/pjm-fuelvintage-1`
**HEAD at writing:** `f51c287d8e1655ba4bf4e9ff9ebe2857fa4a733e`
**Keeper / control:** `results/calibration/pjm_debugb_inputclock_A` = run `2026-08-15-pjm-162-inputclock`
**Scope:** PJM ONLY. No other ISO's keeper shard, matrix shard, status part or calibration log is touched.

> **The owner has already ruled (§A7, 2026-09-09, verbatim: *"these should be promoted as keepers on
> both 860 and gas shape counts regardless of inertness"*).** This session is PROMOTING, not deciding.
> Everything below is measurement duty, which §A7 explicitly does not relax: the phase-0 census, every
> criterion at full magnitude, rule 1 `[R-STRUCT]`'s ban on gating a mechanism on its target residual,
> rule 16 `[R-ALLYEARS]`'s ONE registered bundle over 2023-2025, and rule 31 `[R-RETAIN]`.

---

## (a) G-DRIFT (rule 29(b)) — **NOT RUNNABLE FOR PJM, and the control posture is IMPAIRED**

**This is a negative result, stated before any solve, not an assertion of cleanliness.**

**Reason 1 — the keeper's recorded sha is dead.** `meta.json` / `run_config.json` record
`git_sha = 457ae04`. It does not resolve at HEAD (`git cat-file -t 457ae04` → *"Not a valid object
name"*), and it has **no entry in `docs/governance/citation-commit-map.txt`**. The keeper was solved
2026-08-15T08:42:21, one day before the 2026-08-16 `cleanup-large-blobs` history rewrite, which
CLAUDE.md records as making every pre-rewrite sha citation outside that map dead. Deepening the
shallow clone from 506 to 5,553 commits (back to 2026-08-09) does not recover it — the rewrite
replaced the object, it did not hide it.

**Session `pjm-177` reached the identical conclusion earlier TODAY**
(`results/calibration/FINDING-pjm177-st-gas-commitment-persistence-2026-09-09.md` §4, verbatim):

> *"The keeper's recorded `git_sha` `457ae04` **does not resolve at HEAD** and has no entry in
> `docs/governance/citation-commit-map.txt`, so G-DRIFT could not be run against it and G-CTRL form 4
> is void."*

**Reason 2 — the surrogate window is too large to audit honestly.** The nearest defensible base is
`acf784ec5cb6a0b1f3328f2249d9eb2bbc872009` (2026-08-15 08:09:40 UTC, the last `origin/main` commit
before the keeper's solve timestamp — 33 minutes ahead of it). Measured on the rule-29(b) paths:

```
git diff --stat acf784ec HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
  -> 221 files changed, 187,385 insertions(+), 28,868 deletions(-)
```

Rule 29(b)'s premise is that the audit "costs seconds" and is *stronger* than a control solve because
"it says which line did it". At 221 files / 187k insertions over a 25-day window that premise does not
hold. Declaring all of it INERT without reading it would be exactly the unbacked heuristic rule 29(b)
refuses — in the permissive direction, which is worse. **So this PRECOMMIT does not claim it.**

**Reason 3 — there is DIRECT MEASURED EVIDENCE of LIVE drift, at today's HEAD, on this exact keeper.**
`pjm-177` spent the same-HEAD control that reason 1 earned it, and published the result:

| class (2023) | committed keeper | same-HEAD control | drift |
|---|---|---|---|
| every class except the one below | — | — | **≤ 0.25 %** |
| **C1 CT_PEAKER annual TWh** | **19.363** | **18.911** | **−2.34 %** |

pjm-177's own words: *"HEAD drift in a class this mechanism never touches, which form-4 differencing
would have charged to the arm."*

### The posture this session adopts, and why

**G-CTRL form 4 is used — the committed keeper IS the control — but it is declared IMPAIRED, and no
control solve is spent.** Under rule 29(b)'s own terms a LIVE hunk earns a control solve, and a
*measured* live drift is stronger evidence of liveness than a hunk. I am nonetheless not spending one,
for three reasons stated ex ante:

1. **The handoff forbids it explicitly and repeatedly** (§2c, §A6 item 3), on the owner-relayed
   grounds that PJM's control solve was the largest single cost in the failed predecessor session.
2. **Under §A7 the differencing decides nothing.** The owner has ruled promote-regardless, so the
   arm-vs-control comparison sizes the promotion; it does not select it. A control solve would buy
   reporting precision, not a decision.
3. **The drift is already published for the screen year at today's HEAD** (the table above), so it can
   be carried as a stated correction rather than re-measured at LP cost.

**The binding consequence, pre-registered so it cannot be written to fit the result:** any
keeper-differenced class move within **±0.25 %** (and within **±2.4 %** for **CT_PEAKER**) is **NOT
SEPARABLE** from HEAD drift and will be reported as such — never claimed for or against the arm. Moves
outside those bands are attributable. This band is set from pjm-177's measurement, before my solve.

### What IS audited at zero cost, and is clean

| object | verdict | evidence |
|---|---|---|
| `data/raw/reference/iso-gas-capacity-state-weights.csv` | **NEW; LIVE only when the flag is armed** | absent from the keeper's recipe; read only by `iso_electric_power_monthly_level` |
| retiree parquet, 2019-2022 | **LIVE** | see (a2) |
| retiree parquet, 2023-2025 | **INERT — PROVEN, not asserted** | see (a2) |
| `partial_plant_exit_carry` (§A5 item 2 double-count) | **STRUCTURALLY IMPOSSIBLE for PJM** | see (a3) |

### (a2) The retiree window is INERT in 2023-2025 — proven

Measured directly off `data/raw/eia-860/eia860_generator_retired_within_window.parquet` (1,094 rows),
PJM rows only (393 rows / 19,703.0 MW net summer). A row can contribute months to solve year *Y* only
if `planned_retirement_year >= Y`. Partitioning on the pre-widening window boundary:

| | rows | MW (net summer) |
|---|---|---|
| shipped set (`retirement_year >= 2023`) | 188 | 6,408.1 |
| **added by the widening (`retirement_year <= 2022`)** | **205** | **13,294.9** |

**Capacity the widening ADDS, per solve year:**

| solve year | 2019 | 2020 | 2021 | 2022 | **2023** | **2024** | **2025** |
|---|---|---|---|---|---|---|---|
| rows | 205 | 151 | 108 | 78 | **0** | **0** | **0** |
| MW | 13,294.9 | 8,094.5 | 5,687.1 | 4,535.9 | **0.0** | **0.0** | **0.0** |

Every one of the 205 added rows carries `planned_retirement_year <= 2022`, so **zero** of them
contribute a single month to 2023, 2024 or 2025. The artifact's own max retirement year is 2024 and
its min is 2019. This reproduces the handoff's PJM figures **exactly** (205 units / 13,294.9 MW;
2020 +8,094.5; 2021 +5,687.1; 2022 +4,535.9), which is an independent check on the whole chain.

Class mix of the 205 added rows: **Conventional Steam Coal 10,649.9 MW** (80.1 %), gas-CC 968.6,
petroleum liquids 547.4, gas-ST 431.1, gas-CT 364.5, landfill gas 168.0, wood biomass 83.0,
batteries 47.6.

### (a3) §A5 item 2 — the partial-plant double-count cannot occur in PJM

`market_sim.data.fleet.eia860._partial_plant_exit_rows(data/raw, ba)` returns **`None` for every BA
tested** (PJM, MISO, CISO, ERCO, NYIS, ISNE, and `None`) in this container, so it contributes no rows
at all. Independently and decisively, `partial_plant_exit_carry` is **absent from the keeper's
`run_config.json`**, i.e. at its `False` default, so the channel is disarmed in every run this session
solves. **No overlap is possible.** (Reported honestly: the all-`None` reading may reflect a source
file outside the `pjm` hydration profile rather than an empty channel. The flag being off is the
load-bearing half and does not depend on that.)

---

## (b) THE SCREEN YEAR — **2023**, named here, BEFORE the screen runs

**2023**, on the mechanism's own **largest measured footprint**: FINDING §3's PJM rows give 2023 the
largest mae (**0.775 $/MMBtu**) and the largest annual gap (**−0.770**) of all seven admitted years,
and its largest single month (Feb, 1.415). It is a **training** year. It is **not** named on any
residual, and the footprint ranking is a property of the input table, computed before any solve.

Ranking, from FINDING §3 (`mae`, all seven admitted): **2023 0.775** > 2019 0.704 > 2022 0.646 >
2020 0.552 > 2021 0.527 > 2025 0.479 > 2024 0.473.

---

## (b2) PHASE 0 — the written-cell census (handoff §4)

**The question.** PJM's keeper carries `gas_plant_monthly_fuel_pricing = True`, so
`apply_plant_monthly_fuel_prices` runs **after** the new seam and overwrites gas plants with their own
F923 monthly prints. What fraction of PJM's **gas capacity-hours** does that print path own? Whatever
it owns, the seam cannot reach.

**Keeper fuel recipe, read from `run_config.json` (not `meta.json` — FINDING §1):**

| field | value | consequence |
|---|---|---|
| `gas_plant_monthly_fuel_pricing` | **True** | the print path prices gas — the seam is overwritten wherever it writes |
| `nearby_fuel_price_fallback` | **True** | a plant-month with no print is filled from the state/zone pool — this **widens** print ownership well beyond own-reported months |
| `gas_monthly_actuals` | True | the ISO-month receipt level the seam REPLACES |
| `gas_hub_basis_overlay` | **False** | **no hub index supersedes the seam** — PJM is the only in-scope ISO where the seam is the operative level |
| `gas_daily_shape` | True | mean-preserving within month; rides on top, untouched (rule 19) |
| `pjm_zonal_gas_basis` | True | mean-zero spread; orthogonal (rule 19) |
| `coal_prb_passthrough_sigmoid` | True | **keyed to the ISO `_gas_series`** — see the two-channel note below |
| `partial_plant_exit_carry` | absent (False) | §A5 item 2 disarmed |
| `gas_electric_power_monthly_level` | absent (False) | the control posture |

### THE CENSUS NUMBER — measured 2026-09-09, before the screen solve

Measured through the real path: `run_calibration.run_year(..., fleet_only=True)` off the keeper's own
`meta.json`, then `apply_plant_monthly_fuel_prices(base, fleet_arrays, config, 2023)` reading its
returned `(n_gen, T)` written-cell mask, restricted to gas rows (`_GAS_FUEL_IDX = (0, 1, 10, 14)`) and
weighted by `pmax`.

| quantity | PJM 2023 |
|---|---|
| generators in the LP | 3,789 |
| **gas rows** | **1,744** |
| **gas capacity** | **100,451.1 MW** |
| **print-path-owned share of gas CAPACITY-HOURS** | **51.794 %** |
| print-path-owned share of gas cells, unweighted | 49.871 % |
| gas rows the print path owns in **all 8,760 hours** | 780 (**47,285.5 MW**) |
| gas rows the print path **never touches** | 844 (**46,825.4 MW**, 46.6 % of gas capacity) |
| gas rows partially owned | 120 |

**WHAT THIS MEANS, and it is not what §A2 expected.** §A2 flagged the per-plant print path as "THE MOST
LIKELY WAY THIS ARM COMES BACK INERT", and for MISO the matrix already records **100 %** print
ownership. **PJM is not that case.** The print path owns barely half, so **48.2 % of PJM's gas
capacity-hours are reachable by the seam directly** and **46,825.4 MW of gas capacity is untouched by
the print path in every hour of the year**. Both channels enumerated below are therefore LIVE, and the
arm is **not** inert by construction.

**The consequence for the coal prediction, registered before the solve.** With channel 1 roughly half
open rather than closed, the sign of the coal move is **genuinely contested** between the two channels
rather than settled by channel 2. The handoff and FINDING §5b predict **coal UP**; that reading assumed
channel 1 was throttled. I am recording, before seeing any dispatch, that **the census does not support
that assumption**, and that a coal move in **either** direction is consistent with the mechanism. I
will report which channel won, at full magnitude, and will not treat either sign as a success.

**Per §A7 this number SIZES the promotion; it does not gate it.** The owner has ruled promote-regardless
of inertness, and this measurement says the promotion is worth substantially more in PJM than the inert
case §A2 feared: about half of PJM's gas fleet prices off the seam.

**G-3 anchor, fixed here before the solve.** `iso_electric_power_monthly_level('PJM', 2023)` =
[3.8617, 3.4389, 2.6920, 2.2664, 2.0334, 1.9419, 2.2058, 1.9799, 2.0993, 2.1397, 2.6888, 2.5357]
$/MMBtu, mean **2.4903**. The armed run's ISO monthly level must equal this array **exactly** (rule 19:
replaced, never blended).

### The two channels, enumerated before the number is known (rule 19 `[R-ONE-MECH]`)

The seam can reach PJM's dispatch by exactly two routes, and they push **opposite ways on coal**:

1. **DIRECT (per-generator gas price).** Only through gas cells the print path does *not* write.
   Cheaper gas ⇒ gas CC moves **down** the stack ⇒ **coal DOWN**, prices down. This channel is
   throttled by the census fraction: at 100 % print ownership it is **dead**.
2. **INDIRECT (the ISO-level `_gas_series`).** The seam sets the ISO gas series that keys the **coal
   PRB passthrough sigmoid**, which the keeper arms. A lower gas series ⇒ lower coal passthrough ⇒
   coal offers **fall** ⇒ **coal UP**. This channel survives the per-plant overwrite entirely.

The handoff and FINDING §5b predict **"coal UP, prices DOWN"**. That is channel 2 dominating, which is
only coherent if channel 1 is largely closed — i.e. if the census is high. **I am pre-registering the
census as the discriminator between the two channels**, and I am recording here, before seeing it,
that a naive reading of channel 1 alone would predict the opposite sign on coal. If the census comes
back low and coal still goes UP, that is a result to investigate, not to bank.

---

## (c) PER-YEAR PREDICTIONS — registered before any solve

Copied from FINDING §3/§5b and made specific. **Rule 1 `[R-STRUCT]`: none of these is a gate.** They
exist so the measurement can surprise me on the record.

### Fuel input (the mechanism's own arithmetic, not a dispatch claim)

| year | model annual | measured annual | **Δ annual** | max month gap | mae |
|---|---|---|---|---|---|
| 2020 | 2.484 | 1.936 | **−0.548** | 1.178 (Feb) | 0.552 |
| 2021 | 4.109 | 3.581 | **−0.528** | 1.075 (Dec) | 0.527 |
| 2022 | 7.121 | 6.479 | **−0.641** | 1.374 (Feb) | 0.646 |
| **2023** | 3.255 | 2.485 | **−0.770** | 1.415 (Feb) | **0.775** |
| 2024 | 2.856 | 2.387 | **−0.469** | 0.736 (Feb) | 0.473 |
| 2025 | 3.934 | 3.745 | **−0.189** | 1.720 (Jan) | 0.479 |

**Gas DOWN in every year**, by −0.19 to −0.77 $/MMBtu on the annual. **Every month of 2023 lower**, by
−0.31 to −1.42 $/MMBtu. At 7.5 MMBtu/MWh that is roughly −1.4 to −5.8 $/MWh on a CC-marginal hour.

### Dispatch and price

- **C3a (mean LMP): predicted DOWN in every year**, and predicted to **improve** — PJM's keeper runs
  **above** actual (pjm-177 measures control 31.418 vs actual 29.58 in 2023, **+6.22 %**), and a
  uniform gas-level cut moves the marginal offer down. Predicted 2023 magnitude **−0.5 to −2.0 $/MWh**
  (i.e. toward actual). *This is a prediction, never a gate — rule 1.*
- **Coal: predicted UP** (channel 2 dominating, per (b2)). Predicted small — **under +2 % of coal
  annual TWh** in 2023, because the passthrough sigmoid is a bounded transform, not a price swap.
- **Gas CC: predicted DOWN slightly**, as coal takes share.
- **2020/2021/2022 (Card A + Card B together, no attribution arms):** **prices FALL** and **coal
  generation UP** — and here the two changes push the *same* way, since the widening restores
  8,094.5 / 5,687.1 / 4,535.9 MW that is **80 % coal**. **2020 is the largest effect year.** Rule 30(c)
  is noted in advance: a held-out year never downgrades PJM.

### C3b — **PJM IS THE HIGHEST-RISK ISO IN THE PROGRAM, and here is why in my own words**

C3b scores the **shape** of the price distribution/duration curve, not its level. A mechanism that
moves the level *uniformly* is nearly free for C3b; a mechanism that moves it *unevenly across the
year* re-ranks hours and can break it. PJM is the worst case on both counts that matter:

1. **It is the only in-scope ISO with no hub overlay.** For NYISO, NEISO and CAISO the measured
   constrained-hub index supersedes the seam, so their level barely moves and their shape cannot. PJM
   has nothing above the seam — the full move lands.
2. **The move is not uniform.** It is −0.31 to −1.42 $/MMBtu across the twelve months of 2023 — a
   **4.6× spread**, concentrated in **February** (the largest gap, 1.415). So the winter months fall
   ~3× harder than the mild ones. C3b is measured on exactly that monthly shape.
3. **PJM's marginal unit is overwhelmingly gas CC**, so essentially every hour's price moves — there
   is no insulated block of hours to absorb the change.
4. **This is the ercot-254 failure mode's own family.** ercot-254 broke because a monthly level was
   smeared flat across a month whose real event lasted five days. PJM's saving graces are that its
   largest admitted gap is **1.42 $/MMBtu**, not ERCOT's 49.53 — **35× smaller** — and that
   `gas_daily_shape` is already armed in the keeper, so the monthly level is redistributed across days
   by the measured Henry Hub daily swing rather than laid down flat. That is why I predict a miss is
   unlikely, not impossible.

**Pre-registered C3b prediction: within ±0.03 of the keeper, in every year, and more likely to improve
than degrade** (the seam removes a level that is biased high in 12/12 months, and a bias that varies
by month is itself a shape error). **Pre-registered STOP (rule 29):** if the 2023 screen flips any
load-bearing criterion (C1 / C2 / C3a / C3b) **PASS → FAIL**, the fuel arm dies at the screen, the
remaining years are not spent on it, and that is reported as the session's result. Card A is **not**
gated by the screen — it is an input-correctness fix with no flag (rule 14 `[R-ACCURATE]`).

---

## (d) THE SCREEN'S STOP GATES — structural only, none references the target residual

A screen **may kill an arm; it may never promote one** (rule 29).

| gate | claim | bar |
|---|---|---|
| **G-1** | the delivered gas array moves in the direction and order of magnitude the pre-solve arithmetic implies | monthly means vs FINDING §3's PJM 2023 row; sign correct in 12/12 months |
| **G-2** | confinement | **non-gas fuel prices move EXACTLY 0.0** |
| **G-3** | rule 19 — REPLACED, not blended | the armed ISO monthly level equals `iso_electric_power_monthly_level('PJM', 2023)` exactly |
| **G-4** | no collateral damage | **no NON-TARGET load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL** |
| **G-5** | LP integrity | slack and dump stay **0.0** |

---

## (e) EXECUTION PLAN — and one declared deviation from §A1's shard table

**Container prep (§A6), done and verified in this container before any solve:**
`python3 scripts/prepare_solve_container.py` → swap provisioned, **RAM 15.7 + swap 8.0 = 23.7 GiB**
(the container ships with **zero** swap; PJM's measured single-solve peak is 13.0 GB, the highest of
any ISO, which is what SIGKILL'd the predecessor). Env pins exported for every solve —
`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` — which do **not** change the
LP optimum (thread count is a factorization-workspace choice).

**A setup cost this program has not recorded, found here and reported rather than absorbed.** A fresh
container needs, before its first PJM LP: `hydrate_data.py --profile pjm` (2.3 GB), **`regenerate_clean.py`
over ~55 datatypes** (`data/clean` is gitignored and ships empty), **and a re-fetch of
`data/raw/pjm-da-virtuals/`** — a gitignored DataMiner corpus (`pjm_da_virtual_bids` is armed in the
keeper and `virtual_bids.py` hard-fails rather than silently no-op) requiring
`scripts/data/fetch_pjm_da_virtuals.py` for **six** years. That is on the order of **1.5-2 hours of
non-LP setup per container**, and §A1's five-shard plan pays it **five times**.

**Declared deviation.** §A1 shards the training span as T1 (2023 2024) + T2 (2025) and requires them
composed into one bundle. Given the setup cost above, and that **rule 16 `[R-ALLYEARS]` asks for one
bundle from one `--year 2023 2024 2025` invocation** while **rule 12 `[R-PARALLEL]` requires years
sequential within an invocation anyway**, the training span is solved here as a **single three-year
invocation**. This is *more* rule-16-faithful than composing two fragments, removes the
cross-session composition step that has failed repeatedly in this program, and costs nothing: §A1's
split was a RAM workaround, and the RAM is now backed by 8 GiB of swap. The holdout groups remain
sharded. **No fragment is registered as a keeper under any plan.**

| shard | years | `--out-dir` | where |
|---|---|---|---|
| **S** screen | 2023 | `results/screen/pjm_ep_level_2023` | this container, **first** |
| **T** training | 2023 2024 2025 | `results/pjm_fuelvintage_A` | this container, one invocation |
| **H1** validation | 2020 2021 | `results/pjm_fuelvintage_H1` | `--holdout-authorized` |
| **H2** validation | 2022 | `results/pjm_fuelvintage_H2` | `--holdout-authorized` |

All arms: `scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A --set
gas_electric_power_monthly_level=true`.

**Markers (§6).** PJM holds `complete`, so **2020 / 2021 / 2022 are OPEN** with `--holdout-authorized`.
**2019 is REFUSED for every ISO** (locked tier, `final` empty, freeze ACTIVE) and is neither attempted
nor designed around.

**Rule 31 `[R-RETAIN]`.** Nothing is deleted. Bundle families are added to `.gitignore` — which is what
discharges rule 29(c)'s delete-before-merge duty, per rule 31's own correction of the ercot-255
incident — and kept on local disk. This container is ephemeral, so the promotion question is asked
explicitly in the final report.
