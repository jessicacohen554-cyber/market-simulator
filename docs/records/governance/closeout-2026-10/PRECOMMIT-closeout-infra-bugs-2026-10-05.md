# PRECOMMIT — closeout-infra-bugs: how the two fixes land

Lane: `claude/closeout-infra-bugs` (desk-chartered, 2026-10-05). **Zero LP.** Diagnosis and census:
`FINDING-closeout-infra-bugs-2026-10-05.md`. This PRECOMMIT asks the owner to rule on BUG 1's landing. BUG 2 needs
no ruling.

## 1. How the repo lands a solve-affecting code fix

- **Key.** `ScenarioConfig.cache_key()` does not see code. A code-level change that moves a solve declares a scoped
  `SolveEpoch` in `config/solve_surface.py` (append-only, rule 26) and a prose entry in the `results/cache.py` epoch
  ledger. Precedents: 2026-10-02c/d (desk ruling D-1), 2026-10-03b (owner ruling R-35), 2026-10-03d (R-43).
- **No global epoch.** The design forbids an unscoped or global epoch, because it would move the pinned default key
  (`test_the_default_config_carries_no_epoch`).
- **Keepers stay designated.** Their committed bundles remain the record. The epoch only stops a stale cache being
  served.
- **Re-solves.** Precedent keepers were re-solved at a later promotion, or by a W0-style re-solve program where the
  desk chartered one.
- **No knob.** Rule 26: the fix replaces the defect outright, with no `--legacy-clock` escape.

## 2. BUG 2 (PJM per-DIBA label): lands now, keeper-neutral

- **What lands.** The only live reader is the print-only cross-check in `scripts/data/derive_pjm_seam_ladders.py`.
  The fix (`pjm_eia930_label_to_est`, tests, README data-contract note) changes no solve input, no ladder value and
  no key.
- **Rule 23.** The derive's outputs come from the tie meter and are byte-identical.
- **Merge.** Merged with this PRECOMMIT on `main`.
- **Open item (not ruled here).** The PJM 2019 per-DIBA sign window, and a bulk re-pull to settle the root cause,
  before any future consumer reads this file.

## 3. BUG 1 (leap-year model clock): needs a ruling

- **Code.** On branch `claude/closeout-infra-bugs-leapclock` at `dfe60e6e7de13d04759a7d19af39590a5cbfcae0`: the
  fix, tests, and `SolveEpoch 2026-10-05a` (backcast, every ISO).
- **Why it is held.** It is not keeper-neutral. It changes the 2020 and 2024 inputs of every registered keeper,
  and NYISO's 2024 leg only (that keeper starts in 2021). The common years are byte-identical.
- **Why it is not urgent.** The defect has existed since these call sites were written. Every keeper's 2020 and
  2024 numbers were produced under it, consistently.

**Exposure by keeper** (FINDING §2; leap legs only):

| ISO (keeper) | Leap legs | What moves | Size |
|---|---|---|---|
| PJM `2026-10-03-closeout-pjm-nuc-keeper` | 2020, 2024 | Tie and seam envelopes (congestion, seam import/export, net-position cut); midcurve gas day; must-run; temperature floors | **Largest.** Envelopes move 1.2–5.8 % of envelope MWh, up to 4.3 GW in one hour. |
| NYISO `2026-10-02-w0-nyiso` (CALIBRATED) | 2024 | LI 30-min requirement On-Peak mask; must-run; temperature floors | 1,504 h flip 270↔540 MW (11.7 % of requirement MWh) |
| NEISO `2026-10-02-w0-neiso` (CALIBRATED) | 2020, 2024 | Coldsnap derate and winter-fuel temperature driver; must-run; floors | Every day Mar–Dec shifts one day: ≈ 3.2 °C mean \|ΔT\| on 7,344 h. Coldsnap acts only in cold windows, so Mar and Nov–Dec. |
| CAISO `2026-10-02-closeout-caiso-w1-arm2` | 2020, 2024 | Midday gas floor; gap-hour measured-gas hub reference; must-run; floors | 240 h; 0.6 % of floor MWh; up to 7.7 GW in one hour |
| ERCOT `2026-10-02-closeout-l1-coal-fuel` | 2020, 2024 | Offer-surface gas day; must-run; floors | Gas day: 4 % of $·h, ≤ $0.77/MMBtu |
| MISO `2026-10-03-closeout-miso-nuc-r` | 2020, 2024 | CHP temperature derate; must-run; floors | Temperature input as above; must-run 0.12–0.18 TWh relocated, annual energy unchanged |
| SPP, SOCO, NWPP | 2020, 2024 | Must-run only (plus the benchmark monthly split) | ≤ 0.07 TWh relocated per year, annual energy unchanged |

**Options for the owner:**

- **(A) Land now; fold into each ISO's next promotion (recommended).**
  - Merge the leap branch (renaming the epoch id if one with the same date lands first).
  - Every keeper stays designated on its committed bundle.
  - The next promotion of any ISO re-solves its full span under the fix (rules 16 and 35 already require that), so
    the fix costs no extra solves.
  - G-DRIFT for any lane after the merge classifies these hunks LIVE on 2020 and 2024 only. Under (A) the owner
    rules that hunk a **declared co-traveller**: no control solve, and the PRECOMMIT and attestation of the next
    promotion name it.
  - **Cost:** zero LP now. Lane PRECOMMITs must attribute leap-leg deltas between the fix and their own lever.
- **(B) Land now plus a dedicated re-solve program.**
  - Re-solve the 17 leap legs (8 ISOs × 2020 and 2024, plus NYISO 2024) as one shard per leg against each keeper's
    recipe, compose, and promote as a recipe-identical re-key.
  - **Cost:** 17 shard legs and 9 promotions. The determination is re-checked everywhere.
  - Clean attribution, but it competes with close-out lever work for shard capacity.
- **(C) Hybrid.**
  - (A) for every ISO, plus (B) only for the two CALIBRATED keepers, whose determinations would otherwise rest on
    pre-fix leap legs until they promote again: NYISO 2024 (1 leg) and NEISO 2020 and 2024 (2 legs).
  - **Cost:** 3 legs and 2 promotions.
- **(D) Hold the branch until close-out ends.** Nothing moves. The defect stays live in every new solve, so every
  close-out lever lands on top of it.

**Recommendation: (C).**
- The defect is a calendar error with no structural content. Rules 13 and 14 favour the measured-calendar input,
  and every promotion re-solves anyway, so (A) is nearly free for the ISOs still promoting.
- The two CALIBRATED determinations should not stand on a known-wrong clock longer than 3 legs cost.
- PJM is the ISO where the fix matters most. It is still promoting (closeout-PJM-w3 is live), so it gets the fix
  through (A) at its next keeper.

**Forecast.**
- Forecast keys are not moved (the epoch is backcast-scoped, to keep the default key pinned).
- A forecast whose pinned `weather_year` is 2020 or 2024 reads the corrected daily temperature and On-Peak mask. That
  is a same-key change for that forecast family.
- The forecast program should be told, so it can decide whether to re-solve. It is out of this desk's backcast
  scope.

## 4. What this lane did not touch

No solve, rubric, matrix shard or keeper designation. No `ScenarioConfig` field was added. No results were deleted.
