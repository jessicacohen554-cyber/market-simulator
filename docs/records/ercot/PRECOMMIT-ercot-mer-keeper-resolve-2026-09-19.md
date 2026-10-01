# PRECOMMIT — ERCOT keeper re-solve for the marginal emission rate (MER control arm)

**Session:** ercot-mer (parent/orchestrator), 2026-09-19. Branch
`claude/ercot-keeper-configs-60kit8`.
**Owner instruction:** the 2026-09-19 MARGINAL-CARBON CONTROL ARM append — every solve
now emits `marginal_emission_rate` (the emissions dual, per-zone-hour tCO2/MWh, in
`hourly/system_<year>.parquet`), landed on `main` at
`2ec096633f5624585eb9db1728ebc7c8ca5ccbdf` (2026-09-18) and **not retroactive**.
**Purpose:** (1) produce the MER series for ERCOT; (2) empirically test the rule 29
`[R-SCREEN]` (b) G-DRIFT form-4 claim that the committed ERCOT keeper is a valid
control at HEAD.
**Not a keeper candidate.** No dashboard id is minted, the keeper bundle is not
overwritten, nothing is re-registered (append, "WHEN IT LANDS").

---

## 1. What is being re-solved

ERCOT's designated keeper is `2026-09-09-ercot265-receipts-fallback`
(`frontend/data/backcast/keepers/ERCOT.json`), bundle
`results/calibration/ercot265_receipts_five_year`, spanning **five years
2021-2025**. It is a **COMPOSITE**: `meta.json`'s
`config_partition_overrides` (`composite-per-year-recipe/v1`) records a per-year
recipe overlay. Computed from the committed block, the span splits into **three
recipe groups**:

| group | years | overlay over the base (forward) recipe |
|---|---|---|
| carve-out A | 2021, 2022 | `ercot_offer_swcap_clip=true`, the x33 `offer_curve_by_group` peak bands |
| carve-out B | **2023** | the same **plus** `ercot_zonal_spread_ep_referenced=false` |
| forward | 2024, 2025 | — (the base recipe as recorded in `meta.json` / `run_config.json`) |

The owner's note that "2023 has a different config than the other years" is
**confirmed and is stronger than stated**: 2023 differs from BOTH the other
carve-out years and the forward years.

Per-leg config signatures, read from the committed `run_config_*.json`:

| leg | `ercot_offer_swcap_clip` | `ercot_zonal_spread_ep_referenced` | `CC_REGULAR.peak` | `CT_PEAKER.peak` |
|---|---|---|---|---|
| carve-out 2021/2022 | `true` | `true` | 151.008 | 433.95 |
| carve-out 2023 | `true` | **`false`** | 151.008 | 433.95 |
| forward 2024/2025 | `false` | `true` | 4.576 | 13.15 |

`ercot_ep_gas_basis_receipts_fallback=true` and
`netload_drag_layup_window_mask=true` in all three.

## 2. Why this is three invocations, not one — and why that is NOT a rule-32(b) fan-out

Rule 32 `[R-SHARD]` (b) and the append both require **one shard, one
`--years` invocation, one bundle**. That is **impossible for this bundle as a
matter of code, not preference**: `replay_keeper.enforce_single_recipe_partition`
HARD FAILS (`SystemExit`) on a span that mixes recipe groups, because
`solve_and_persist` carries ONE config per call. Its own docstring prescribes the
remedy: *"Chain one invocation per group with `--years`."*

`--reuse-solved` cannot chain the groups either: `plan_reuse_solved` requires the
prior bundle's reconstructed kwargs to **equal** this invocation's
solve-affecting kwargs, and by construction the three groups' kwargs differ. So
the legs cannot be merged into one out-dir by the sanctioned channel.

**The execution is therefore: ONE SHARD, ONE CONTAINER, THREE SEQUENTIAL
INVOCATIONS, THREE OUT-DIRS.** This is not the banned fan-out: the ban's own
stated defect is legs *"that cannot be reassembled"* across ephemeral
containers. Here all three legs are solved in a single container and pushed on a
single branch, and reassembly is a solved problem — it is exactly how
`ercot265_receipts_five_year` itself was composed, re-derivable with
`scripts/stamp_config_partition.py --check`. Rules 16 `[R-ALLYEARS]` and 34
`[R-SHARD-PROMOTABLE]` (c) are met in full: **every year the keeper carries
(2021, 2022, 2023, 2024, 2025) is solved, in one batch.**

## 3. Pinned SHA and the MER precondition

Pinned `source_revision`: `5017c3602adf7bc9389cf10755fc22833f8f1b2d`
(`origin/main` at 2026-09-19).

Precondition checked **before** launch, as the append requires:

```
git merge-base --is-ancestor 2ec096633f5624585eb9db1728ebc7c8ca5ccbdf 5017c360... -> YES
```

So the pinned tree carries the emissions dual. No leg may use `--reuse-solved`
or a warm cache: a reused year carries `marginal_emission_rate = None`.

## 4. G-DRIFT — NOT asserted, MEASURED

Rule 29 `[R-SCREEN]` (b) form 4 differences an arm against the keeper's committed
numbers, and is voided by a LIVE hunk on the backcast solve path. **There is no
arm here**, so form 4 is not being claimed; this replay is the stronger test —
the empirical one — and the drift audit is recorded as the *prediction basis*,
not as a clearance.

`git diff <keeper git_sha 6bc43501> origin/main` over
`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` touches **115 files,
+18,810 / -1,921**. That is ten days of engine commits and it is NOT
hunk-classified here, deliberately: the replay measures the answer directly.
The last measurement of this question was ercot-264 (2026-09-09,
`docs/RESULT-ercot264-keeper-repro-2026-09-09.md`), which reproduced all five
years **to the cent** at `754a91d9` — i.e. zero drift as of the keeper's own era,
with ten days of commits landing since.

## 5. Baseline — the committed keeper's own numbers (read from the committed sidecars, this session)

P1, load-weighted over `demand`, 7 zones x 8760 h:

| year | P1 load-wtd mean price $/MWh | simple mean $/MWh | `marginal_emission_rate` present? |
|---|---:|---:|---|
| 2021 | 174.8514 | 157.9566 | **no** |
| 2022 | 68.3962 | 57.3161 | **no** |
| 2023 | 60.1182 | 45.5178 | **no** |
| 2024 | 30.8901 | 26.6091 | **no** |
| 2025 | 33.8052 | 29.5925 | **no** |

The all-five-absent column is the append's "not retroactive" claim, verified
rather than assumed.

## 6. Sealed predictions (scored in the RESULT)

* **P1** — every leg's per-year P1 load-weighted mean price reproduces the §5
  baseline to **within 0.01 $/MWh**. ercot-264 reproduced to the cent; ten days
  of commits have landed since, so this is a real test and not a formality.
* **P2** — `marginal_emission_rate` is present and **not all-zero** in all five
  `hourly/system_<year>.parquet`. Absent => the SHA was wrong; the shard STOPS
  and does not push.
* **P3** — each leg solves its own signature (§1 table). A leg that sees
  otherwise STOPS. This is the ercot-259 two-config replay defect, and the
  `config_partition_overrides` consumption is what closes it.
* **P4** — if any scored number moves, it is reported **at full magnitude as a
  finding** and the lane STOPS. No config is hunted that restores the old
  numbers (rule 1 `[R-STRUCT]`).
* **P5** — a byte-faithful reproduction is **not** a keeper candidate and is not
  registered (rule 30 `[R-TOUCHPOINT-FOLD]`; append "WHEN IT LANDS").
* **P6** — MEMORY IS UNVALIDATED at per-plant ERCOT scale with the dual. The
  dual adds one basis refactorization after the main solve. An OOM is a
  **FINDING about the dual**, not a model regression, and is reported as such
  rather than worked around.

## 7. Budget, stated rather than hidden

One ERCOT per-plant year measured at **974 s / ~9 GB**
(`docs/RESULT-ercot252-2022-repair-resolve-2026-09-06.md`). Five years is
therefore **~80-90 min of LP**, plus hydration and the per-leg verification.
Rule 32(b)'s 20-minute ceiling is a STOP rule, and the rule's own remedy for a
span that cannot fit is *"a longer single shard with the budget stated in its
prompt, not a fan-out whose legs cannot be reassembled."* **The stated budget is
~120 minutes.** The shard pushes **each leg the moment it completes** (three
commits) so a later-leg failure cannot strand an earlier leg's bytes
(rule 34 `[R-SHARD-PROMOTABLE]` (a)).

## 8. Retention and retrievability

* Rule 34(a): every leg bundle is **pushed to the shard's own branch**, via a
  `.gitignore` NEGATION plus a **plain `git add`** (never `git add -f`),
  including `dispatch/<year>_P1.parquet`.
* Rule 34(d): the parent runs `git ls-tree -r <shard sha> -- <bundle path>` and
  requires **> 0 files** before archiving anything.
* Rule 33 `[R-SHARD-ARCHIVE]`: fetch, check out, verify, **then** archive;
  recovery recorded by **full immutable SHA**, never branch name.
* Rule 31 `[R-RETAIN]`: nothing is deleted. The promotion question is put to the
  owner explicitly in the RESULT, with the statement that the bundles do not
  survive container reclamation.

---

# AMENDMENT 1 — OWNER OVERRIDE: ONE SHARD PER YEAR, THEN COMPILE (2026-09-19)

**Owner instruction, verbatim:** *"What the fuck launch one shard per year then compile"*.

This **supersedes §2 and §7 above**. The single three-leg shard
(`session_01P6ZYCiNKAPDKjc1NcUt2k2`) was interrupted ~6 min into LEG 1, had pushed
**nothing** (`git ls-remote` showed no `ercot-mer` branch), and was archived — so no
result was lost and rule 31 `[R-RETAIN]` is not engaged.

**FIVE SHARDS, ONE YEAR EACH**, all pinned to `5017c3602adf7bc9389cf10755fc22833f8f1b2d`,
launched concurrently, each pushing its own bundle to its own branch:

| year | recipe leg | out-dir | branch | session |
|---|---|---|---|---|
| 2021 | carve-out A | `results/calibration/ercot_mer20260919_2021/` | `claude/ercot-mer-2021` | `session_01XAPSJtKQgkgJFRmxvhKpRE` |
| 2022 | carve-out A | `results/calibration/ercot_mer20260919_2022/` | `claude/ercot-mer-2022` | `session_01RRhQsYd2hLrTrKcpsFxbKP` |
| **2023** | **carve-out B** (`ep_referenced=false`) | `results/calibration/ercot_mer20260919_2023/` | `claude/ercot-mer-2023` | `session_018sZN9sa47f5PBrKi2jhkLu` |
| 2024 | forward | `results/calibration/ercot_mer20260919_2024/` | `claude/ercot-mer-2024` | `session_01L44zSgtycE6LNJKk4vrU9k` |
| 2025 | forward | `results/calibration/ercot_mer20260919_2025/` | `claude/ercot-mer-2025` | `session_013uD117W2qrc3RgxKtcsUYi` |

**Wall-clock is now ~35 min, not ~120** — five per-plant years solve in parallel in five
containers instead of sequentially in one. Rule 12 `[R-PARALLEL]`'s ~2-invocation cap is a
**within-container memory** limit and does not bind across separate containers; the
precedent is exact — ercot-264 (`docs/RESULT-ercot264-keeper-repro-2026-09-09.md`) ran this
identical five-shard, one-year-each fan-out on this identical keeper.

**Rule 32 `[R-SHARD]` (b) is set aside on the owner's instruction, and the cost is stated
rather than hidden.** The ban exists because a slim per-year fan-out cannot be recomposed
(`render_calibration_html.build_payload` needs the bundle-root `system.parquet`, and the
per-plant D-1/D-2/D-4 diagnostics PASS VACUOUSLY off an unregistered composite). **That
failure mode is closed here by rule 34 `[R-SHARD-PROMOTABLE]` (a): every shard PUSHES its
full bundle, `dispatch/<year>_P1.parquet` included**, so the parent receives real bytes and
compiles from them. What made the miso-255 / SPP-36 fan-outs unrecoverable was shards that
gitignored their bundles — not the fan-out itself.

**Compilation is the parent's job (rule 32(d)):** fetch all five branches, check out each
bundle, verify each leg's config signature and its `marginal_emission_rate` column, compile
the five per-year legs into one bundle span, and re-derive the partition block with
`scripts/stamp_config_partition.py --check` — which must reproduce the three recipe groups
of §1. The compile is zero-LP.

Every other section stands: the pinned SHA and its MER-ancestry check (§3), the drift
posture (§4), the baseline table (§5), the six sealed predictions (§6), and the retention
and retrievability duties (§8).
