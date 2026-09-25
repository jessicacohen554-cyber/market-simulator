# PRECOMMIT — R-PJM2-CS: the PJM keeper recipe (h22 RGGI + corrected inputs) re-solved on COAL-SUB HEAD, 2019–2025 (2026-09-25)

Written and pushed **before any solve**. The seven shards pin to this commit's full SHA.

**Owner instruction (2026-09-25), verbatim:** *"The r PJM resolve should be run again on rggi keeper config"* —
with all coal now in its subclass (COAL-SUB, #6611/#6616, eliminated the bare `COAL` class).

## 0. The premise, reconciled against the repository at the pin

The handoff named `2026-09-24-pjm-h22-rggi-span` as the incumbent and `2026-09-24-pjm-r-pjm-corrected` as the
run to prune. **Both were already superseded and pruned before this session started**: lane R-PJM-2 solved the
h22 RGGI recipe on the corrected (F1/F2) inputs for 2019–2025, the owner ruled *"Yes promote"*, and it was
promoted as **`2026-09-25-pjm-r-pjm-2`** (bundle `results/calibration/rpjm2_span`) with h22 span, h22
touchpoint and r-pjm-corrected pruned under rule 35 (`docs/RESULT-r-pjm-2-rggi-keeper-corrected-inputs-2026-09-25.md`).

What R-PJM-2 did **not** have is COAL-SUB: its shards pinned `651fac08…`, and `git merge-base --is-ancestor`
confirms neither #6611 (`5f8d153c`) nor #6616 (`ab0d0059`) is in that pin. So the instruction resolves to:
**re-solve the current keeper's recipe — which IS the h22 RGGI config on corrected inputs — at a HEAD that
carries COAL-SUB.** The incumbent / control is `2026-09-25-pjm-r-pjm-2`. No recipe key is changed; the only
intended treatment is the code (COAL-SUB) plus whatever else G-DRIFT (§4) finds LIVE, each named.

Nothing remains to prune from the handoff's list (r-pjm-corrected is gone; `prune_iso_runs.py` would be a
no-op). If this run is promoted, the outgoing keeper is `2026-09-25-pjm-r-pjm-2`.

Concurrency note: a separate session ("PJM follow-ons after R-PJM-2 promotion", branch
`claude/pjm-follow-ons-rpjm2-uft6xl`) is live on PJM. This lane touches no shared file until registration and
edits only PJM's own shards; any promotion collision is surfaced to the owner, never resolved silently.

## 1. Year set (rules 34(c) / 35(b))

PJM registered runs at this pin: `2026-09-25-pjm-r-pjm-2` only, years **2019–2025**. Union = 2019–2025.
This lane solves all seven, one shard per year (rule 36).

## 2. Recipe

`scripts/replay_keeper.py results/calibration/rpjm2_span --years <y>` — the keeper's `meta.json` replayed
unchanged, **no `--set` flags** (the six F1 flags and `pjm_rggi_allowance_pricing` are already in the recipe).
Offer curves unchanged (rule 1(c)); `authorized_price_tuning` carried unchanged. The recipe's
`offer_curve_overrides` carries a legacy bare `"COAL"` entry beside all four subclasses; `replay_keeper.
translate_legacy_coal_keys` → `plant_taxonomy.fold_legacy_coal_key(covered=COAL_CLASSES)` drops it (every
subclass has its own curve), **verified zero-LP**: the rebuilt `offer_curve_by_group` carries no `COAL` key in
any year, and the four subclass bands are byte-equal to the recipe's.

## 3. Phase 0 census (zero LP, this session, at the pin's code)

### 3a. Coal by subclass — keeper recipe, `run_year(fleet_only=True)` (`scripts/probes/coal_subclass_snapshot.py
--set pjm_da_virtual_bids=false`; the virtual-bid rungs are appended pseudo-units, never coal rows)

| MW | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COAL_BIT | 43,981.8 | 41,034.3 | 43,661.7 | 38,097.5 | 33,266.8 | 32,536.8 | 44,942.0 |
| COAL_PRB | 3,845.0 | 3,845.0 | 3,845.0 | 2,646.0 | 2,650.0 | 2,650.0 | 3,160.0 |
| COAL_WC | 1,264.0 | 1,206.5 | 1,202.0 | 1,201.6 | 1,201.3 | 1,201.3 | 1,376.2 |
| **bare `COAL` rows** | **0** | **0** | **0** | **0** | **0** | **0** | **0** |
| former generic bucket (pre-COAL-SUB `UNRESOLVED`, `docs/handoffs/coal-sub/census-2019-2025.json`) | 5,372.8 | 3,887.7 | 4,616.0 | 1,311.0 | 0 | 0 | 0 |
| … now → BIT / PRB / WC | 4,651.3 / 689.0 / 32.5 | 3,198.7 / 689.0 / 0 | 3,927.0 / 689.0 / 0 | 1,311.0 / 0 / 0 | — | — | — |

Plants in the former bucket (2019): Morgantown Energy Facility, Herbert A Wagner, Chalk Point, Dickerson,
Morgantown Generating Plant, Brunner Island, Chesterfield, Notre Dame, Spruance, Ingredion, Waukegan (the
689 MW PRB); 2022: Wagner + Chesterfield only. **2023–2025 had no generic-bucket coal**, so COAL-SUB's
fleet/offer effect on PJM is confined to 2019–2022.

The former bucket read the `COAL` band (committed 0.648 / econ_low 0.684 / econ_high 0.792 / peak 1.044); it
now reads its subclass's (BIT 0.548 / 0.6556 / 1.2664 / 1.044; PRB 0.684 / 0.5544 / 0.80 / 1.0656;
WC 0.512 / 0.548 / 0.6344 / 0.764) — the multipliers themselves are the keeper's, unchanged.

### 3b. EIA-860 vintage and class-table heat rates (`docs/handoffs/f1/census.py --iso PJM --posture
backcast-default`, re-run here — byte-equal to R-PJM PRECOMMIT §3a)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EIA-860 source | vintage_2019 | vintage_2020 | vintage_2021 | vintage_2022 | vintage_2023 | vintage_2024 | canonical 2025ER |
| thermal nameplate (MW) | 140,065 | 138,067 | 141,761 | 138,274 | 135,864 | 135,400 | 134,572 |
| thermal MW at a class-table heat rate | 279.6 (0.20 %) | 255.6 (0.19 %) | 281.3 (0.20 %) | 280.3 (0.20 %) | 280.3 (0.21 %) | 63.4 (0.05 %) | 869.6 (0.65 %) |
| retiree class-table MW / online | 905 / 18,993 | 871 / 13,920 | 327 / 11,599 | 327 / 10,467 | 320 / 6,316 | 6 / 1,268 | — |

### 3c. Outage windows

Every PJM outage file is byte-identical between the keeper's pin and this one (`git diff --stat` empty on
`data/raw/campd-unit-outages*`); `campd-unit-outages-PJM.csv` sha256 `312a11b84778…`. Windows per family are
therefore exactly R-PJM PRECOMMIT §3d: std 1255 / 1118 / 1379 / 1321 / 1372 / 1364 / 1271 (2019→2025),
short-coal 113 / 87 / 125 / 134 / 94 / 85 / 106, short-gas 246 / 283 / 291 / 409 / 317 / 323 / 236, partial 0
(not armed).

## 4. G-DRIFT `651fac08` → this pin (rule 29(b)) — zero LP

{GDRIFT}

## 5. Gates and predictions — declared before any solve

Decided on structure (rules 1 / 14): COAL-SUB is a representation correction (no unit sits in a class that
does not exist); the re-solve is promoted or not on the owner's ruling, and the gates are reported at full
magnitude either way.

- **G1 liveness (shard hard stop):** `run_config` shows the six F1 flags and `pjm_rggi_allowance_pricing`
  true, no `COAL` key in `offer_curve_overrides`, outage sha `312a11b8…`; RGGI log line P = 5.97 / 7.07 /
  10.44 / 14.84 / 14.87 / 22.83 / 24.35 $/t for 2019–2025 with N > 0.
- **G2 predictions.** 2023–2025: no generic-bucket coal, so class TWh within ±0.1 TWh of the keeper and
  C1–C8 unchanged, unless a §4 LIVE hunk other than COAL-SUB reaches them. 2019–2022: the former bucket
  (5.4 / 3.9 / 4.6 / 1.3 GW) mostly moves to COAL_BIT, whose committed and econ_low bands are ~15 % / ~4 %
  cheaper than the old COAL band and whose econ_high is ~60 % dearer; its net sign on coal energy is **not
  predicted**. The known 2020/21 COAL_BIT over-run (R-PJM-2: +21.45 / +25.70 TWh) is at risk of worsening,
  and a worsening is an offers finding (pjm-168), reported, never re-tuned. The C1 bench is by subclass, so
  the old bare-COAL model energy now lands in its subclass row — a scoring move, not a physics move.
- **G3:** full rubric C1–C8 every year, vs the keeper re-scored on the same benchmark.

## 6. DOF (rule 21)

Zero new free parameters. The offer-curve block is the keeper's, with its existing ledger entry; the bare
`COAL` entry is dropped by the legacy translator, which reduces the effective band set (no unit read it).

## 7. Shards (rules 32 / 34 / 36)

Seven, one per year 2019…2025, each its own container, pinned to this commit's full SHA. Out-dir
`results/calibration/rpjm2cs_<y>`, branch `claude/rpjm2cs-<y>`. Prompt: `SHARD-PROMPT.md` beside this file.
Each shard pushes its full bundle including `dispatch/<y>_P1.parquet`; the parent fetches, verifies, composes
one 2019–2025 bundle (`rpjm2cs_span`) and lands it on `main` before this lane's PR merges. Shard SHAs are
provenance only; per-year leg dirs are gitignored on `main`.
