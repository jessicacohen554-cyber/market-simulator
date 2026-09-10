# RESULT — nyiso-223 shard `nyiso223-y2023` (NYISO 2023 hub gap-fill arm)

_Provenance: rescued verbatim from branch `claude/nyiso223-y2023`, original path unchanged. That branch also carried a duplicate of the `nyiso_hub_gap_month_level` mechanism commit, which is already on `main`; only this report was unmerged. The SOLVED 2023 result is `RESULT-nyiso223-shard-2023-r2.md`._

**Status: STOPPED — no solve artifact. Blocked on an unbuilt `data/clean` tree.**
**Date:** 2026-09-10 · **Pinned SHA:** `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99`

Per rule 32 `[R-SHARD]` (b): *"A shard approaching 20 minutes with no artifact
stops and reports; it never pushes a half-written bundle."* This is that report.
No bundle was written, nothing under `results/` was committed, and nothing under
`src/` or `scripts/` was edited.

---

## 1. Hard stops — ALL PASS

| # | Check | Result |
|---|---|---|
| 1 | `git rev-parse HEAD` == `ce4779ec…3ed99` | **PASS** (exact) |
| 2 | `results/calibration/nyiso_fuelvintage_A/meta.json` exists, `iso == NYISO` | **PASS** (years `[2023, 2024, 2025]`) |
| 3 | `grep -c nyiso_hub_gap_month_level src/market_sim/config/scenarios.py` ≥ 4 | **PASS** (4) |

## 2. PRE-SOLVE GATE — ALL THREE NUMBERS MATCH THE PRECOMMIT EXACTLY

This is the one substantive deliverable the shard did produce, and it is
zero-LP, so it stands on its own regardless of the solve failure.

| Quantity | PRECOMMIT expectation | Measured | Verdict |
|---|---|---|---|
| Annual mean hub gas, off → on | 3.3566 → 3.3566 | **3.3566 → 3.3566** | exact to 4 dp |
| Dec 22–31 mean, off → on | 3.919 → 3.683 | **3.919 → 3.683** | exact to 3 dp |
| Hours moved | 4416 | **4416** | exact |

**The arm's own falsification test passes at the input layer.** Mean preservation
holds to 4 decimal places, and the December window moves **DOWN** (3.919 → 3.683)
— i.e. *against* the price residual the arm would otherwise be suspected of
chasing. Whatever the dispatch response turns out to be, the input construction
is mean-preserving and is not aimed at the residual.

## 3. Why the solve did not complete

`data/clean/` in this container is **completely empty (0 entries)**. It is
derived, disposable and gitignored, so it is never present in a fresh clone, and
`scripts/hydrate_data.py --profile nyiso` does not build it — on this box it
reported *"This is a FULL clone — every blob is already local, so hydrating
changes nothing"* and exited without writing a single clean partition.

The NYISO keeper recipe reads that tree, so the solve fails on the **first**
partition it needs, ~10 minutes into the year (after fleet build / CAMPD binning),
and each fix only surfaces the **next** missing partition:

**Attempt 1** (launched 02:09) — failed in `model/interchange/nyiso.py:279`:

> `ValueError: nyiso_li_lcr_tsl=True but no published Long Island
> transfer_security_limit for delivery year 2023/2024 … available areas: []`

Diagnosed as a *false* data-absence report: the raw row **does exist** —
`data/raw/capacity-deliverability/nyiso/nyiso.csv` carries
`NYISO,2023/2024,annual,Long Island,locality,transfer_security_limit,940`. The
loader was returning `{}` solely because the **clean** partition was absent
(`capacity-deliverability: clean partition for NYISO absent`). Regenerated the
one named datatype, as the shard prompt directs:

```
PYTHONPATH=.:src uv run python scripts/data/curate_capacity_deliverability.py --isos NYISO
→ wrote data/clean/capacity-deliverability/NYISO/capacity-deliverability.parquet (35 rows)
→ transfer_security_limit_by_area('NYISO','2023/2024') == {'Long Island': 940.0}   ✓ resolves
```

**Attempt 2** (the one authorized retry, launched 02:11:36, failed 02:21:42) —
got past the TTC cap and failed ~10 min in at
`data/nyiso_par_attribution.py:378`:

> `FileNotFoundError: nyiso_seam_par_attribution 2023: could not read the
> 'nyiso-interface-flows' clean partition … run scripts/regenerate_clean.py
> nyiso-interface-flows (the mechanism never silently no-ops)`

**Blocking datatypes named so far: `capacity-deliverability` (now built) and
`nyiso-interface-flows` (not built).** There is no reason to believe these are
the last two — an empty `data/clean` means *every* clean-backed reader in the
NYISO path is a candidate, and each one costs ~10 minutes of solve to discover.

The one authorized retry was spent, and at ~17 minutes elapsed the 20-minute
shard budget left no room for a third ~10-minute discovery pass, so the shard
stopped rather than run long.

## 4. What the parent needs to change before relaunching

**The SETUP block in the shard prompt is incomplete.** It has
`uv sync` + `hydrate_data.py --profile nyiso`, but a solve additionally needs the
clean tree built, and that is **not a 20-minute step**. Two repo findings put a
number on it:

- `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md:226` — *"`scripts/regenerate_clean.py` — 50 datatypes across all ISOs, **~2 h wall-clock on this box**"*
- `docs/FINDING-entry-signal-disarm-2026-08.md:487` — *"`PYTHONPATH=. uv run python scripts/regenerate_clean.py` before any solve (48/51 …)"*

So a full regeneration **cannot** live inside a 20-minute solve shard. Options
for the parent, in the order I'd recommend them:

1. **Split the bootstrap out of the solve shard.** Run a dedicated
   provisioning step (or a longer-budget shard whose only job is
   `PYTHONPATH=. uv run python scripts/regenerate_clean.py`) and only then launch
   the per-year solve shards. Note this does **not** transfer between containers:
   `data/clean` is local disk, so the provisioning and the solve must share one
   container, i.e. the solve shard's own budget must cover both — which argues
   for (2).
2. **Give the 2023 solve shard a budget that covers provisioning + solve**, and
   name the NYISO-relevant datatype subset explicitly (rather than all 50) so the
   bootstrap is minutes, not hours. Known-required so far:
   `capacity-deliverability`, `nyiso-interface-flows`; the NYISO keeper recipe
   will also plausibly want `lmp`, `load`, `demand-profile`, `fleet`,
   `fuel-prices`, `outages`, `renewables`, `ancillary-services`,
   `nyiso-reserve-requirements`, `nyiso-downstate-gas`,
   `nyiso-som-hub-fuel-annual`, `nyiso-renewable-curtailment`, `reference`.
   **This list is inferred from datatype names, not verified by a solve** — treat
   it as a starting set, not a guarantee.
3. **Confirm whether the sibling 2024/2025 shards hit the same wall.** If they
   did, this is a program-level prompt defect, not a 2023-specific one.

## 5. Reporting items 1–8 of the shard brief

**Not available — no LP artifact was produced.** C3a, C3b, C3c, C1 per-class TWh,
C8 forced shares, the Dec 22–31 vs Dec 1–21 split, the determination, and the
per-class ≥0.10 TWh mean-preservation falsification check all require the solved
bundle. None of them are reported here, and none should be inferred from §2 —
the gate is an *input*-layer measurement only.

Nothing is claimed about whether the arm is promotable.

## 6. Rule compliance

- **Rule 31 `[R-RETAIN]`** — nothing deleted. `results/calibration/nyiso223_gapfill_2023/`
  holds only a stub `dispatch` dir from the failed attempts and is left on disk,
  already gitignored.
- **Rule 32 `[R-SHARD]`** — stopped at the budget with a report rather than
  running long or pushing a partial bundle. No infrastructure was repaired: the
  only write outside the doc was regenerating one derived, gitignored `data/clean`
  partition, which the shard prompt explicitly authorizes.
- **Forbidden list** — no `git add -A` / `git add .`; nothing under `results/`,
  `frontend/data/backcast/**`, `src/` or `scripts/` committed or edited; no
  dashboard/registration script run; no PR opened.
