# PRECOMMIT — spp-52: an authorized offer-curve price-tuning solve, **fossil bands × 0.93, SPP-scoped**

**Session spp-52, 2026-09-09.** Branch `claude/fossil-offer-curve-tune-6okt4h`.
**PUSHED BEFORE THE FIRST LP.** Every number below is measured from committed
artifacts and two zero-LP `fleet_only` rebuilds; **no solver has been called**
at the moment this document is committed.

---

## §A — What the owner asked, and what this session is

Verbatim:

> *"For the next spp solve, tune the fossil offer curve down by 7% across the
> board and run."*

Read as written: multiply **every** `offer_curve_by_group` band multiplier of
**every fossil class SPP's keeper carries an entry for** by **0.93**, and solve.
There is no ambiguity to resolve and no alternative reading, so nothing is
withheld pending clarification.

**The incumbent keeper is `2026-09-09-spp-51c-oversupply-curtailment`**
(bundle `results/calibration/spp51c_oversupply`, `git_sha 86e45462`,
determination **NOT-YET**). Its resolved offer curve is **entirely neutral** —
every band of every router-readable class is **1.000**, i.e. SPP has never had
a fitted curve — so "down by 7 % across the board" resolves to a single value,
**0.930**, in all 40 bands.

**The direction is consistent with the model's measured error.** Model
load-weighted price against the repaired-clock actual (both from committed
artifacts; the clock repair is spp-51c's, not this session's):

| year | model rt_lw | actual rt_lw | C3a |
|---|--:|--:|--:|
| 2023 | 27.0934 | 25.133 | **+7.80 %** |
| 2024 | 26.8848 | 25.450 | **+5.64 %** |
| 2025 | 31.5372 | 28.598 | **+10.28 %** (the lone C3a FAIL) |

The model overshoots in every year. This is **not** the reason the factor is
0.93 — the factor is the owner's, fixed ex ante — and it is **not** a rule 14
`[R-ACCURATE]` measured-input repair. It is the rules 1 `[R-STRUCT]` / 13
`[R-MEASURED]` **authorized price-tuning channel**, declared in §C.

## §B — The mechanism, and every rule 1 `[R-STRUCT]` carve-out condition answered

**Mechanism.** The override is applied through the operator channel
(`replay_keeper.py --offer-curve-json`, resolving at
`pipeline/backcast_config.py:2523` — *after* every per-ISO and measured-surface
merge, so the cut cannot be silently overwritten). The resolved absolute values
are committed verbatim at
`results/calibration/_spp52_fossil93_offer_curve.json` and reproduced in §D.

* **(a) the channel is the band multipliers ONLY.** Exactly four bands move per
  class — `committed`, `econ_low`, `econ_high`, `peak`. **UNTOUCHED:** every
  `phys_*` key, the structural shares `econ_low_share` and `pct_peaking` (both
  carried through byte-identical), and every non-band key. No adder, offset,
  haircut, load proxy or fuel discount exists anywhere in this run. The coal
  `mustrun` / `sync` tranches are **not** in the channel by construction — they
  price off the measured `hr_mr` column and are VOM-only, never `base_hr ×
  multiplier` (`data/offer_curves.py:1096,1167`).
* **(b) ONE config across EVERY scored year.** One factor, one override file,
  one `--years 2023 2024 2025` invocation. **No per-year value exists and none
  will be produced.**
* **(c) set EX ANTE, declared BEFORE the solve, NEVER swept.** The factor is the
  owner's, handed down in §A before any solve; this document is committed and
  pushed **before the first LP**. **The factor will not be swept.** If the gates
  do not land where the owner expects, the RESULT reports that at full
  magnitude — it does **not** try 5 % or 9 %. Trying a second factor to make a
  criterion pass is exactly the fitted-mechanism selection condition (c)
  forbids, and it stays forbidden in this session.
* **(d) merit-order adjustment across classes is INTENDED, not a defect.** A
  uniform 0.93 on the heat-rate multiplier is **not** a uniform 0.93 on marginal
  cost: `mc = hr × fuel + vom` (SPP prices no carbon), so the *fuel* leg falls
  7 % and the VOM leg does not. Gas, with the dearer fuel, therefore falls more
  in absolute $/MWh than coal, and **gas gains against coal at the margin**.
  That is the intended effect, stated here in advance so it cannot later be
  reported as a surprise.
* **(e) declared in the attestation + carried in the DOF ledger.** The bundle's
  `calibration_attestation.json` carries an `authorized_price_tuning` block
  naming this instruction (C6 FAILS without it), and the DOF ledger gains
  **one** free parameter — `fossil_offer_band_scale = 0.93` — whose
  identification source is, per rule 20 `[R-DOF]`'s cross-reference, **"price
  residual, authorized channel (rules 1/13 amendment 2026-09-05); owner
  instruction 2026-09-09"** — never a measured input. Under that same
  cross-reference its presence does not by itself make the residual it closes an
  open root-cause issue; **every other** tuned value still would, and no other
  one exists here.

**Rule 25 `[R-ISO-SCOPE]`:** applied as a CLI override on an **SPP** invocation.
It touches no shared default, no `constants.py` value and no other ISO's curve.
"Across the board" is read as *across every fossil class of this ISO*, which is
what rule 25 permits; it is **not** propagated to ERCOT, CAISO, PJM, MISO,
NYISO or NEISO.

**Rule 24 `[R-REGISTRY]`:** the resolved curve is recorded in the bundle's
`run_config.json` (`scenario_config.offer_curve_by_group`), so the channel is
on-registry and inspectable. No env var, no hardcoded dict.

**Rule 28 `[R-MECH-MATRIX]`:** `offer_curve_by_group` is an existing matrix row;
its **SPP** cell takes this session's evidence. No new `ScenarioConfig` field is
created, so duty (c) does not fire.

## §C — The 10 classes and 40 bands that move

Every class that is BOTH router-readable (`plant_taxonomy.fossil_classes()`)
AND present in the keeper's resolved curve. All keeper values are 1.000, so
every moved band lands on **0.930**.

| class | committed | econ_low | econ_high | peak | SPP P1 energy 2023/24/25 (TWh) |
|---|--:|--:|--:|--:|---|
| CC_REGULAR | 1.000 → **0.930** | → 0.930 | → 0.930 | → 0.930 | 42.24 / 41.92 / 35.66 |
| CC_CHP | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 1.850 / 1.891 / 1.936 |
| CT_PEAKER | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 17.70 / 19.57 / 15.10 |
| CT_CHP | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 1.225 / 1.239 / 1.157 |
| ST_GAS | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 8.257 / 11.875 / 8.328 |
| COAL_PRB | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 63.82 / 59.82 / 82.13 |
| COAL_LIGNITE | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 7.950 / 6.548 / 7.090 |
| COAL_BIT | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 0 (no SPP energy) |
| COAL_WC | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 0 (no SPP energy) |
| COAL (generic) | → 0.930 | → 0.930 | → 0.930 | → 0.930 | 0 (supply-routed above) |

`econ_low_share` and `pct_peaking` are carried through **unchanged** in every
class (condition (a)).

**Three declared exclusions, all disclosed pre-solve:**

1. **`ST_CHP` is router-readable but has NO entry in the keeper's curve**, so it
   is **not** cut. Adding one would inject a band set the keeper never had —
   that is a new parameter, not a cut of an existing one. It carries
   0.358 / 0.447 / 0.216 TWh (0.15–0.31 % of SPP fossil energy) and is reported
   as an untouched fossil class in the footprint.
2. **`CC_INTERMEDIATE` / `CT_INTERMEDIATE` / `ST_GAS_INTERMEDIATE`** are present
   in the keeper's resolved curve but the router **never reads them**
   (`parse_offer_curve_json` refuses them outright). The keeper carries
   `cc_intermediate_split = ct_intermediate_split = st_gas_intermediate =
   false`, so they are inert in every year regardless.
3. **The coal `mustrun` / `sync` tranches** are outside the channel by
   construction (§B(a)). Measured in the phase-0 rebuild: **733 of 765** (2023)
   and **731 of 763** (2024, 2025) fossil tranches move; the unmoved remainder
   is exactly the ST_CHP and vom-only coal min-load rows.

## §D — Phase 0 (ZERO LP): the footprint, and the screen year

**Instrument:** `scripts/probes/spp52_fossil93_phase0.py`. Two on-recipe
`fleet_only` rebuilds of the keeper per year, differing ONLY in
`offer_curve_overrides`, differenced on the model's own assembled offer array
`mc_base`. Nothing is re-implemented: the pricing arithmetic is whatever
`bins_to_fleet` does. Tranche energy is recovered from the committed
`hourly/class_band_hourly_<y>.parquet` by (class, band) and split within a cell
by tranche capacity — the keeper's per-plant parquets were pruned under rule 15
keeper-only retention, so the class-band sidecar is the finest committed
dispatch grain available, and the within-cell capacity split is an
approximation, declared as one. A **coverage guard** refuses to report F(y)
unless the reconstruction reconciles with the sidecar's own fossil total; it
reads **1.000000** in all three years (it caught, and killed, a first cut that
silently dropped the entire coal fleet).

    F(y) = Σ over fossil tranches of  energy[u] × mean_t |Δmc[u, t]|   ($)

| year | fossil TWh | **$ of offer re-pricing** | mean Δmc on fossil MWh |
|---|--:|--:|--:|
| 2023 | 143.403 | $213.34 M | $1.4877/MWh |
| 2024 | 143.315 | $209.59 M | $1.4624/MWh |
| **2025** | **151.621** | **$245.34 M** | **$1.6181/MWh** |

Per-class 2025 ($M): COAL_PRB 84.20 · CC_REGULAR 72.01 · CT_PEAKER 52.17 ·
ST_GAS 25.13 · COAL_LIGNITE 7.39 · CC_CHP 2.57 · CT_CHP 1.88 · ST_CHP 0.00.
`max_abs_dmc_nonfossil = 0.0` in all three years — **not one non-fossil row
moves**, which is the mechanism's claimed footprint holding exactly.

**SCREEN YEAR = 2025**, fixed here before the screen runs. It is
`argmax_y F(y)` — the largest footprint on the mechanism's own quantity — and
it is *also* the largest on raw fossil energy, so the choice does not turn on
which measure is preferred.

**DISCLOSED HONESTLY, because it differs from the caiso-267 precedent:** 2025
is *also* the year with the largest C3a residual (+10.28 %) and the lone C3a
FAIL. The two measures **coincide** here where in CAISO they pointed apart.
That coincidence is not the reason for the choice — F(y) contains no price
actual, no residual and no criterion, and the probe that computes it reads
none — and the protection that matters is unchanged: **the screen gate itself
reads no residual** (§E), so a screen year that happens to be the worst
residual year cannot select the mechanism on the residual. Stated rather than
smoothed.

## §E — The pre-registered SCREEN gates (rule 29 `[R-SCREEN]`)

**Pre-solve prediction, so the screen has something to falsify.** Mean Δmc on
2025 fossil energy is **$1.6181/MWh** against a model rt_lw of $31.5372. λ is
set by the marginal fossil unit in most hours, so |Δλ| should be of order
**$1–3/MWh and NEGATIVE**. A move an order of magnitude away from that, or
positive, means the LP and the pre-solve arithmetic disagree and the session
stops to find out why.

**The gate is STRUCTURAL and STOP-ONLY. It may kill the arm; it may never
promote one, it contributes to no determination, and it is NOT gated on the
target residual** (a screen reading "did C3a improve" is exactly the selection
rule 1(c) forbids, one year at a time). Fixed here, never widened after the
fact:

* **G-IDENT** — the arm differs from the control by the offer curve and
  **nothing else**: demand byte-identical, fleet capacity byte-identical. Any
  other moved input **STOPS** the session.
* **G-FOOT** — the response is confined to the rows the mechanism claims:
  fossil classes and the prices they set. Non-fossil *capacity* and
  *availability* unchanged (their dispatch may move — that is the merit order
  working).
* **G-DIR** — |Δλ| on 2025 lands in **[$0.4, $5.0]/MWh** and is **NEGATIVE**
  (a cut cannot raise the annual mean price).
* **G-NOFLIP** — no **non-target load-bearing** criterion flips PASS → FAIL
  (C1 `fuelmix`, C2 `sysvol`, C3b `price_shape`, C4 `dispatch_corr`, C6, C8).
  **C3a is the target and is exempt in both directions. C3c is exempt** — it is
  already failing in all three years and is the standing model-class limitation
  under rubric v3.6 (SPP has no scarcity mechanism at all; that is SPP-55's
  object, not this lane's).

**Only if all four hold** does the full span run, as ONE
`--years 2023 2024 2025` invocation and ONE bundle (rule 16 `[R-ALLYEARS]`).
The screen bundle is a **throwaway diagnostic probe** — never registered, never
a keeper, never quoted as a keeper number — and 2025 is re-solved inside the
full bundle.

## §F — G-CTRL: **form 4**, and the G-DRIFT audit that earns it

Rule 29(b): the keeper's committed bundle **IS** the control, and **no control
solve is spent**, provided a code-level `G-DRIFT` audit classifies every changed
hunk on the backcast solve path as INERT. Run and recorded here **before** the
arm is solved, so it cannot be written to fit the result.

    git diff 86e45462 HEAD -- src/market_sim scripts/run_calibration.py \
        scripts/run_calibration_full.py scripts/lib \
        data/raw/_validation-source data/raw/reference

**Four files, +281 / −4 lines, and it is ONE mechanism:**

| file | change | classification |
|---|---|---|
| `config/scenarios.py` (+89) | adds field `netload_drag_min_run_persistence: bool = False`, plus its `_CACHE_KEY_OPTIONAL_FIELDS` / drop-value registration | **INERT** — a `ScenarioConfig` flag that is default-off AND absent from the keeper's recipe; dropped from the cache key at its default, so the key is unmoved |
| `data/fleet/floors.py` (+139) | `_circular_centred_mean`, `_min_run_hours`, and a `persist_params` argument | **INERT** — every new path is guarded `if persist_params is not None`, and `persist_params` is `None` unless `config.netload_drag_min_run_persistence` is True |
| `scripts/run_calibration.py` (+10) | threads the same flag; `if … is not None` | **INERT** — same flag, never passed |
| `scripts/run_calibration_full.py` (+47) | threads the same flag + CLI; and calls `enforce_single_recipe_partition` in `run_replay_bundle` | **INERT** — same flag; and the partition consumer is a no-op for a bundle with no `config_partition_overrides` block, which SPP's `meta.json` does not have |

**ALL HUNKS INERT ⇒ G-DRIFT PASSES ⇒ form 4 is valid and the keeper's committed
bundle is the control.** No control LP is spent. Zero data files changed on the
solve path, so the arm's inputs are the keeper's inputs.

## §G — Exposures declared BEFORE the solve

So that no post-hoc reading can be presented as a prediction:

* **C3a may cross zero.** Residuals are +7.80 / +5.64 / +10.28 % on rt_lw of
  27.09 / 26.88 / 31.54, i.e. gaps of **$1.96 / $1.43 / $2.94**/MWh, against a
  mean Δmc of **$1.49 / $1.46 / $1.62**/MWh. **The cut is the same order as the
  whole residual in every year, and in 2024 it is LARGER than the gap.** C3a
  landing *negative* in 2024 is a live outcome, not a surprise. Reported at full
  magnitude either way.
* **C1 and C2 move by construction, and coal is the one to watch.** §B(d): gas
  falls more in absolute $/MWh than coal, so gas share rises and coal share
  falls. C1's live failing row is **2024 ST_GAS at −8.23 TWh** (model under),
  which this cut should push *toward* the band; but C2 (`sysvol`, gas/coal
  families) currently PASSES and a coal displacement is the most likely
  **G-NOFLIP** failure. It is named here, in advance.
* **C3b-2025 is on a knife edge** at NRMSE 0.204 against a ≤0.20 band, and a
  level cut moves the whole duration curve.
* **C3c will not improve.** SPP has no scarcity mechanism of any kind (0/4/2 h
  >$200 against 42/59/68 actual); a *downward* offer cut can only reduce tail
  hours. It is exempt from G-NOFLIP and stays the lane's ledgered
  model-class limitation. This is expected, not a defect of this run.
* **The determination may get worse.** If it does, that is the result, reported
  as such. **The keeper is not replaced by a worse run** — promotion is the
  owner's call (§H).

## §H — Governance

* **Rule 15 `[R-DASHBOARD]`** — the full-span bundle is registered whatever it
  says, keeper or rejection, in this session. The **screen** bundle is never
  registered (rule 29(2)/(c)) and is `.gitignore`d so it cannot reach `main` or
  turn the parity gate red.
* **Rule 31 `[R-RETAIN]`** — **nothing solved is deleted.** `.gitignore`
  discharges the delete-before-merge duty; `rm` does not. The promotion question
  is put to the owner **explicitly** before the session ends, together with the
  statement that the bundles live on local disk and do not survive container
  reclamation.
* **Rule 22 `[R-HOLDOUT]`** — only 2023–2025 are solved. No holdout year is
  touched, no marker is read, and `--holdout-authorized` is not passed.
* **Rule 27 `[R-PUSH]`** — no source file ≥300 lines is rewritten. The only new
  code is a probe under `scripts/probes/`.
* **Rule 12 `[R-PARALLEL]`** — years run sequentially inside the single
  full-span invocation.

**Next number: spp-53.**
