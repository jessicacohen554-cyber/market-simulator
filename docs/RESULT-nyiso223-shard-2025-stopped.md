# RESULT — nyiso-223 shard `nyiso223-y2025` (NYISO, 2025)

_Provenance: rescued verbatim from branch `claude/nyiso223-y2025`, renamed from `RESULT-nyiso223-shard-2025.md` because `main` already carries the SOLVED `y2025-r2` report at that path. This is the first 2025 shard's STOPPED report. Content unmodified._

**STATUS: STOPPED — NO SOLVE, NO BUNDLE, NOTHING PUSHED BUT THIS DOC.**

The shard stopped on a blocked prerequisite, not on a gate mismatch and not on a
model result. Per rule 32 `[R-SHARD]` (b) — "a shard approaching 20 minutes with
no artifact STOPS and reports" — and the standing instruction that a shard which
repairs infrastructure is a FAILURE.

**None of the eight requested numbers (C3a / C3b / C3c / C1 / C8 / June-Nov-Dec
means / determination / per-class energy deltas) exist.** No LP was solved. Do
not read any number into this document that is not here.

---

## 1. Hard stops — ALL PASSED

| Check | Expected | Observed | Verdict |
|---|---|---|---|
| `git rev-parse HEAD` | `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` | identical | PASS |
| `results/calibration/nyiso_fuelvintage_A/meta.json` `iso` | `NYISO` | `NYISO` (years 2023/24/25) | PASS |
| `grep -c nyiso_hub_gap_month_level src/market_sim/config/scenarios.py` | ≥ 4 | 4 | PASS |

No `git pull`, no `git rebase`, no sync. HEAD is untouched.

## 2. Pre-solve gate (zero LP) — PASSED, EXACTLY ON THE PRECOMMIT

| Quantity | PRECOMMIT | Observed | Verdict |
|---|---|---|---|
| annual mean off → on | 5.5602 → 5.5602 | **5.5602 → 5.5602** | PASS (identical to 4 dp) |
| Dec 22–31 off → on | 7.256 → 7.256 | **7.256 → 7.256** | PASS (December unmoved, as registered) |
| hours moved | 6552 | **6552** | PASS |
| max abs delta | 7.587 $/MMBtu | **7.587** | PASS |

The mechanism's *pre-solve* arithmetic reproduces the PRECOMMIT to every declared
digit. That is the one substantive positive result this shard establishes: the
2025 gap-fill is annual-mean-preserving to 4 dp while moving 6552 hours, and its
December is genuinely unmoved. **Mean preservation in the FUEL ARRAY is confirmed;
mean preservation in DISPATCHED ENERGY (report item 8) is NOT — that needs the LP.**

## 3. What blocked the solve

`data/clean/` was **completely empty** in this container. The clean tree is
gitignored, derived and disposable (`scripts/regenerate_clean.py` docstring: it
"must be rebuilt from `data/raw` before the model — or CI — can read it"), and the
shard SETUP recipe I was given (`uv sync` + `hydrate_data.py --profile nyiso`) does
not build it. `hydrate_data.py` was additionally a **no-op** here: this is a FULL
clone, so it reported "hydrating changes nothing" and exited.

Failure sequence:

1. **Solve attempt 1** — reached the LP setup, then died:
   `nyiso_li_lcr_tsl=True but no published Long Island transfer_security_limit for
   delivery year 2025/2026 … available areas: []`
   → missing clean datatype `capacity-deliverability`.
2. **Repair (sanctioned, "regenerate only the named datatype, retry once")** —
   `curate_capacity_deliverability.py --isos NYISO` wrote 35 rows. Clean.
3. **Solve attempt 2** — got further, then died on a *different* missing datatype:
   `nyiso_seam_par_attribution 2025: could not read the 'nyiso-interface-flows'
   clean partition … (the mechanism never silently no-ops)`.
4. Since this was clearly not a one-datatype gap but an empty clean tree, I ran the
   single documented entrypoint `scripts/regenerate_clean.py` (no code edits).

## 4. THE BLOCKER — `lmp` curation fails on a CAISO file, and it takes NYISO down with it

`regenerate_clean.py` runs each datatype independently, and **`lmp` FAILED**:

```
[run ] lmp: curate_lmp.py
  File "scripts/data/curate_lmp.py", line 379, in curate
    frames.append(parse_caiso_file(f))
  File "scripts/data/curate_lmp.py", line 171, in parse_caiso_file
    ghg_usd_per_mwh=num("MGHG"),
KeyError: 'MGHG'
[FAIL] lmp: exit 1
```

Three things make this fatal for this shard, and they are the actionable findings:

- **It is a CAISO file, but it kills NYISO.** `curate_lmp.py::curate()` parses every
  ISO's raw LMP drops in ONE pass into one frame. A single CAISO file lacking the
  `MGHG` column aborts the whole datatype, so **no ISO gets an `lmp` partition** —
  `data/clean/lmp/` does not exist.
- **There is no per-ISO escape hatch.** Unlike
  `curate_capacity_deliverability.py --isos NYISO`, `curate_lmp.py` takes no `--isos`
  flag; it calls `curate(raw_dir)` unconditionally and crashes before argparse can
  even print `--help`. NYISO-only LMP cannot be curated without a code change.
- **Fixing it requires editing `scripts/`, which is forbidden to me by name.** So
  this is a hard stop by construction, not a judgement call.

Note on why this surfaced here: `hydrate --profile nyiso` no-opped because the
container holds a FULL clone, so the CAISO raw subtree is present and gets swept in.
On a genuine `--filter=blob:none` partial clone with only the `nyiso` profile
hydrated, the CAISO files would be absent and this parse might never run. **The
full-clone container may itself be what exposes the bug.**

**Consequence even if the solve had completed:** `lmp` is the actuals source for
C3a (mean LMP % error), C3b (monthly-shape NRMSE) and C3c (hours > $300). With no
`lmp` clean partition those three cannot be scored at all. Repairing only
`nyiso-interface-flows` would have bought a solve whose headline criteria were
still unscoreable.

## 5. Budget and final state

Elapsed ~17 min at stop (launched 02:09 UTC, stopped 02:27 UTC). The full
`regenerate_clean.py` sweep completed **7 of ~50 datatypes in 14 minutes** —
`ancillary-services, capacity-deliverability, demand-profile, emissions,
generation, load, renewables` — and was still grinding through `emissions`
(~29M rows/year × 8 years) across all seven ISOs. At that velocity the clean
rebuild alone is well over an hour, before the ~10–15 min replay. It could not
have landed inside the 20-minute shard budget, so I stopped it rather than push a
half-written bundle.

- `results/calibration/nyiso223_gapfill_2025/` — contains only an empty `dispatch/`
  dir. **No bundle, no `run_config.json`**, so the post-solve config signature was
  never checkable. Left on disk, not deleted (rule 31 `[R-RETAIN]`).
- `data/clean/lmp/` — ABSENT. `data/clean/nyiso-interface-flows/` — ABSENT.
- No edits under `src/` or `scripts/`. No `results/` path committed. No PR.

## 6. What the parent should do

1. **Fix `curate_lmp.py` first — it blocks every NYISO shard (2023 and 2024 will hit
   the identical wall), and every other ISO's lane too.** Either make
   `parse_caiso_file` tolerate a missing `MGHG` column (the other `num()` calls
   already coerce with `errors="coerce"`; this one just needs the column-absent
   case), or give `curate_lmp.py` the `--isos` flag its sibling curators have.
   Both are `scripts/` edits and belong in the parent, not a shard.
2. **Add the clean rebuild to the shard SETUP recipe**, scoped to what a solve
   actually needs — a bare `regenerate_clean.py` is an hour-plus and violates the
   20-minute unit. The NYISO 2025 replay demonstrably needs at least
   `capacity-deliverability` and `nyiso-interface-flows`; scoring additionally needs
   `lmp` and `validation`. Better: pre-bake `data/clean` into the shard image, since
   it is identical across all three year-shards and rebuilding it three times is
   pure waste.
3. **Re-launch this shard unchanged once (1) and (2) land.** The gate in §2 already
   passed on this exact SHA, so the arm is ready to solve; only the data layer was
   in the way.

---

*Shard `nyiso223-y2025` stopped with a clear report and repaired no infrastructure.*
