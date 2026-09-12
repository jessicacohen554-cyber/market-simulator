# PRECOMMIT — SPP-36: `unit_outage_short_windows` to the FULL 2023–2025 span, on the owner's promotion ruling.

**Lane** SPP-36 · **Keeper / control** `2026-09-10-spp-27-commitment-grain`, bundle
`results/calibration/spp27_span` (COMMITTED; differenced, **never re-solved** — rule 29(b) form 4) ·
**Parent LP: ZERO** (rule 32 `[R-SHARD]` (a)) · **Predecessors**
`docs/RESULT-spp-32-shortwindow-screen-2026-09-12.md`, `docs/handoffs/PRECOMMIT-spp-32-shortwindow-availability-2026-09-12.md`.

## 0. THE RULING THIS LANE EXECUTES

Owner, in session, 2026-09-12, **verbatim**:

> *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but
> gates regress that may still be a keeper."*

Put to the owner as `RESULT-spp-32` §7. **Promotion is the owner's act and it has now been made;
this lane executes it.** Arm A's screen bundle did not survive its ephemeral shard container and a
single-year keeper is refused by rule 16 `[R-ALLYEARS]`, so executing the ruling means **solving the
full 2023–2025 span** and registering the composite — not re-litigating the screen.

**The ruling's second clause is the operative one.** SPP-32 stopped arm A on G4 (`slack` must be
0.0000; arm A produced 240.5966 MWh) — a gate SPP-32 itself showed to be mis-set, because keeper 9's
own committed span carries **0.0000 / 370.1017 / 0.0000 MWh** and the 2024 event is *larger*, in the
same 2 hours, same zone (SPP-South), same VOLL. Structural integrity improves (a measured
availability input, rule 14 `[R-ACCURATE]`); some gates regress. That is precisely the case the
owner's standing rule admits.

## 1. THE ARM — one field, zero code, zero free parameters

`unit_outage_short_windows = True`, via
`replay_keeper.py results/calibration/spp27_span --set unit_outage_short_windows=true`.

- **`unit_outage_short_windows_gas` STAYS `False`.** Cell **`R`** for SPP (SPP-32: slack
  10,911.0219 MWh and *both* load-bearing price criteria flipped). Re-arming it is refused under
  rule 28(a) without new evidence, and this lane does not seek any.
- **Extract NOT re-derived** (rule 23 `[R-FROZEN-DERIVE]`): `data/raw/campd-unit-outages-short-SPP.csv`,
  committed, 620 windows / 24 plants / 39 units, **620 of 620 rows `plant_group == COAL`**.
- **Rule 21 `[R-DOF]`: ledger stays n_entries 3 / n_residual 2.** No threshold, share, multiplier or
  level. **Rule 1 `[R-STRUCT]`: `offer_curve_by_group` byte-identical at a uniform 0.93** — not
  re-cut, not swept, not examined against any gate.
- **Rule 19 `[R-ONE-MECH]`:** disjoint from the ≥ 5-day CAMPD overlay (`outage_source="historic"`,
  already on) by DURATION, and from every gas scope by plant group. It **widens a discard**.
- **Rule 25 `[R-ISO-SCOPE]`:** SPP only; the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` at
  its `False` default, so every other ISO's keys are byte-stable.

## 2. G-DRIFT — re-run at THIS base, all hunks INERT, so form 4 holds and no control solve is spent

`git diff 09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ 12 files. Beyond the five classified at `PRECOMMIT-spp-32` §3 (all INERT there, unchanged here):

| file | change | verdict | reason |
|---|---|---|---|
| `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` | 383,037 → 841,783 B | **INERT for the train tier — VERIFIED, not assumed** | lane SPP-30 landed SPP's out-of-training coverage: years go `{2023,2024,2025}` → `{2019…2025}`. The old blob was read back from the keeper's own `basis_sha` and compared row-for-row: **2023, 2024 and 2025 are IDENTICAL** (8,760 rows each; `rt` means 23.4732 / 23.3135 / 27.1112 unchanged to 4 dp). Additive years only. |
| `actual_lmp_hourly_zonal_SPP.parquet`, `actual_lmp.json`, `_validation-source/README.md` | same intake | **INERT** | same additive SPP-30 landing; `frontend/data/backcast/tail/actual_tail.json` gains 2019–2022 and SPP's **2023/2024/2025 rows are unchanged** (`rt_gt` 42 / 59 / 68, `da_gt` 6 / 35 / 0), and `bench/SPP/` still holds exactly 2023/2024/2025 |
| `config/scenarios.py`, `data/outages.py`, `data/fleet/arrays.py`, `data/resolved_inputs.py` | +`unit_outage_window_hour_grain` (nyiso-229) | **INERT** | `bool = False`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` **and** `_..._DEFAULTS` at `"False"` in the same commit; predicated on `campd_per_unit_attribution` **and** `campd_outage_merit_order_guard`, both **`False`** in the keeper's recorded config; it selects a `-perunitmerithour-<ISO>.csv` companion that **exists only for NYISO**; and it acts on the ≥ 5-day `unit_outage_derate_factors` path, not this arm's `unit_outage_short_derate_factors` |
| `scripts/lib/solve_container.py` (new), + its call sites in both runners | swap preflight (miso-254) | **INERT** | provisions a swapfile before the first loader runs; changes no input, no matrix and no dual. Beneficial here, not load-bearing |
| `model/lp/model.py` | release `_all_cols` across `h.run()`, rebuild lazily | **INERT** | `np.arange(total_columns, dtype=int32)` is rebuilt identically; HiGHS has consumed the indices before `run()`. Same class as the SPP-32-audited `cost`/`mc` release; **named as a code-reading call, not a gate** |
| `run_calibration.py`, `run_calibration_full.py` | CLI/plumbing for the above | **INERT** | every new path is behind a default-off flag or the preflight |

**ALL HUNKS INERT ⇒ keeper 9's committed bundle is the control; NO CONTROL SOLVE IS SPENT.**

## 3. HOW IT IS SOLVED — three shards, one fresh year each, chained (rules 12 / 16 / 32)

Rule 12 forbids parallel years inside one invocation; rule 32(b) makes one year one shard. The
supported composition path is `replay_keeper.py`'s **`--reuse-solved`** chain, so the three shards run
**serially**, each pinned to this PRECOMMIT's SHA, each force-adding **only its own slim year files**
onto **its own branch** (never `main` — rule 32(d); `.gitignore` carries `results/calibration/spp36_*/`
as of this commit, which is what discharges the duty, never `rm`):

1. `--years 2023 --out-dir results/calibration/spp36_span` → branch `claude/spp36-2023`
2. `--years 2023 2024 … --reuse-solved <shard-1 dir>` → 2023 byte-copied, **2024 solved** → `claude/spp36-2024`
3. `--years 2023 2024 2025 … --reuse-solved <shard-2 dir>` → **2025 solved** → `claude/spp36-2025`

~166 s of LP per fresh year (keeper 9's measured 499 s / 3 y); a cold container's whole cycle measured
15–25 min at SPP-32. Each shard also pushes `docs/handoffs/SHARDREPORT-spp36-<year>.md` — **the parent
cannot read a cloud sibling's transcript**, the lesson SPP-32 paid for.

## 4. WHAT THE PARENT OWES AFTER THE CHAIN LANDS — once, in the parent, zero LP (rule 32(d))

Compose from shard 3's cumulative bundle → `scripts/calibration_verdict.py --run-id <new id>` (the
FULL three-year verdict) → `scripts/legitimacy_diagnostics.py` → register on the dashboard with
`hourly/` sidecars (rule 15 `[R-DASHBOARD]`; a run is not done until its bundle and dashboard files
are committed and pushed **in this session**) → `keepers/SPP.json` + `build_status.py --iso SPP` +
`audit_keepers.py --iso SPP --check` → rule 28(b) cell move.

## 5. WHAT IS PREDICTED, AND WHAT WOULD MAKE THIS LANE REPORT AGAINST ITSELF

Sealed before the solve. On 2025 alone, arm A measured: coal −2.5714 TWh onto gas +2.3710 TWh;
**C3a +0.66 % → +5.15 %** and **C3b 0.1638 → 0.1878**, both still PASS; slack 240.5966 MWh; 2 hours
> \$200, both at VOLL. **2023 and 2024 are unmeasured and may go either way.**

- The arm is expected to **degrade C3a and C3b** in every year and to introduce slack. Under the
  owner's ruling that is admissible; **it is not a reason to stop, and equally it is not to be
  described as an improvement.**
- **If any load-bearing criterion (C1, C2, C3a, C3b) FLIPS PASS → FAIL on the full span, the
  determination changes and this lane says so in its headline** — SPP would read `NOT-YET`, C3c
  would no longer be a lone failure, and rule 22 `[R-C3C]`'s standing rule could not fire. That is a
  material consequence of promotion and the owner must see it stated, not buried.
- **If slack appears in 2023 or 2025 (where the control has none) at an order of magnitude above
  2024's 370.1017 MWh**, this lane will report the arm as removing capacity the system needed rather
  than as a measured-availability repair, and will recommend against registration despite the ruling.
- C3c will not move meaningfully: the extract removes a mean 172.0 MW per hour across 2024's DA-tail
  hours against ~8,233 MW of headroom. **No gate here reads C3c** (`FINDING-spp-29`).

## 6. GOVERNANCE

Rule 32(a) parent solves nothing · rule 31 `[R-RETAIN]` nothing deleted, no `rm`, and the promotion
question is already answered so trigger (i) is met for SPP-32's superseded artifacts · rule 29(c)
discharged by `.gitignore` · rule 15 keeper-only retention executed at registration ·
`[R-HOLDOUT]` removed 2026-09-09, so **no number here is a certified out-of-sample skill claim** ·
**no `complete` or `frontier` declaration is added, requested or implied.**
