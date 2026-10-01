# ADDENDUM nyiso-226 — **OWNER RULING 2026-09-10: SPEND THE SPAN.** The `S3(a′)` repair is accepted, the full 2023–2025 arm is authorized, and the two zero-LP findings are RECORD-ONLY

**Governs:** `docs/RESULT-nyiso226-nyc-base-rebasis-2026-09-10.md` §6 (a) and (b), and §7.
**Written and pushed BEFORE the span solve.** Nothing here changes a gate, a bar or a
determination.

---

## 1. The two rulings, verbatim in effect

**(a) SPAN — "Spend the span."** The owner accepted the `S3(a′)` repair
(`ADDENDUM-…-my-own-gate-S3a-failed-…-2026-09-10.md`), including its stated weakness that the
repair was declared post-hoc, and authorized the full 2023–2025 arm. **The screen is treated as
cleared.** Restated so it cannot drift: **spending the span is NOT promotion.** Rule 31
`[R-RETAIN]` still reserves the promotion call, and RESULT §6(b) is still open.

**(b) THE TWO FINDINGS — "Record only."** RESULT §7's CT_CHP scoring-scope gap and the
`curate_lmp.py` `KeyError: 'MGHG'` avoidance are **recorded and not acted on**. **No file under
`src/` or `scripts/` is touched by this session on either count**, `FUELMIX_EXCLUDED` is not
edited, and no ISO's scores move. Both are already written into the RESULT and into
`docs/mechanism-testing-matrix.md` §5.5's `QUEUE STATUS UPDATE`, so a successor inherits them
without rediscovering them.

## 2. How the span is run, and why it is ONE invocation rather than three

**One shard, one invocation, `--years 2023 2024 2025`, ONE bundle.** Rule 16 `[R-ALLYEARS]`
asks for exactly that — *"in a single `--year` invocation and a single bundle"* — and it costs
nothing here, because rule 32 `[R-SHARD]`'s per-year split exists for spans that cannot fit a
20-minute unit and **this one fits**: the screen year measured **5 min 00 s**, so three
sequential years is ~15 minutes. Years run **sequentially inside the invocation**, which rule 12
`[R-PARALLEL]` requires anyway.

**The 20-minute ceiling is honoured by construction, not by hope.** The shard is instructed to
stop after the current year once total solve time passes 20 minutes, commit what completed, and
report which years are done. If that fires, the parent launches a continuation shard that
byte-copies the finished years with `--reuse-solved` — rule 32(b)'s *"shards launch shards"*,
applied to the tail rather than the head. **Choosing one invocation also removes the composition
seam entirely**: there are no three per-year bundles to merge, so no per-year bundle dir can be
left committed and turn the Class-E parity gate red (rule 29(c)).

**The `S4` gap is fixed where it belonged — in the shard's ORIGINAL prompt.** RESULT §5 recorded
that C3a/C3b went unmeasured because the solve path writes no `metrics.json` and the shard could
not be reached mid-flight. The span shard is told from the outset to run
`scripts/calibration_verdict.py <bundle>` (full span, and per year) read-only, without
`--write-metrics`, and to paste both the table and the `--json`, plus the load-weighted mean LMP
computed from its own `system_<year>.parquet`. **It still scores nothing itself** — it pastes
numbers, and every verdict is the parent's (rule 32(d)).

## 3. What does NOT change

- **The arm is unchanged**: the same single-cell artifact edit,
  `NYISO,NYC,ST_GAS,tmax,-50.0` `floor_pct` **0.175 → 0.16629202320362052**, value fixed ex ante
  in the PRECOMMIT and never swept. No `ScenarioConfig` delta.
- **The control is unchanged**: the committed keeper bundle, rule 29(b) form 4, G-DRIFT already
  audited. **No control solve is spent for the span either.**
- **`main` is unchanged**: `reliability_floor_coeffs_NYISO.csv` on `main` still reads `0.175`,
  and it stays that way unless and until the owner rules on promotion.
- **Retention**: `results/calibration/nyiso226_*/` stays gitignored (rule 31 `[R-RETAIN]` —
  gitignoring, never `rm`, is what discharges rule 29(c)), and nothing is deleted.
