# Calibration Log — SPP

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for SPP calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## Lane state at file creation (2026-09-07, lane SPP-34)

**No keeper exists.** SPP was registered as the seventh ISO on 2026-09-06 by
lane SPP-20 (`docs/handoffs/FINDING-spp-20-2026-09-06.md`); the first-ever solve
and the first keeper are lane **SPP-40**'s, whose four preconditions are
SPP-30 / SPP-31 / SPP-32 / SPP-53 (plan §4 critical path, owner ruling r#5). So
`frontend/data/backcast/keepers/SPP.json` does not exist yet, and this lane has
no run to score, no determination and no gates.

Program docs: `docs/multi-iso/spp-addition-plan-2026-09.md` (charters, cards,
wave graph, lane table), `docs/handoffs/spp-desk-ledger-2026-09.md` (live state
— **the ledger wins where the two diverge**), `docs/multi-iso/spp-data-audit.md`
(the Phase-0 census). Lever queue: `docs/mechanism-testing-matrix.md` §5.7;
cell verdicts `docs/codebase-site/data/mechanism-matrix/SPP.js`.

Two facts every SPP session inherits, so nobody rediscovers them in a residual:

- **The N↔S TTC is a Tier-3 placeholder that cannot bind** (48,700 MW = the
  North zone's own EIA-860 2025 ER summer capability). No public document states
  an SPP North↔South transfer capability — SPP-13 swept all four candidates and
  found the rated interface data is NDA / CEII
  (`docs/handoffs/FINDING-spp-13-2026-09-06.md` §0). Until lever **SPP-53**
  reconciles one, an SPP solve is a **two-zone copperplate on price**, and
  SPP-40's P7 STOP gate ("link binds in the measured direction/season") cannot
  be met. Never tune the placeholder to a price residual (rules 1 / 13 / 14).
- **The published hubs are a two-point spread, not a zonal price.**
  `SPPNORTH_HUB` ≈ Nebraska, `SPPSOUTH_HUB` ≈ central Oklahoma
  (`docs/multi-iso/spp-data-audit.md` §6.1), so the scoring benchmark is a
  narrower object than the zones it grades. State this at the gate rather than
  absorbing it.

Holdout tiers (rule 22 `[R-HOLDOUT]`): SPP holds **neither** marker — no
`complete`, no `final` — so 2019–2022 and H1-2026 are unsolvable, unscorable and
unregisterable for SPP at both the CLI year gate and the registration gate. The
training window is **2023–2025**, and rule 16 `[R-ALLYEARS]` binds from day one
(`audit_keepers._MULTI_YEAR_ISOS` already lists SPP): a single-year SPP keeper is
refused.

## Pre-push checklist (STANDING — every session in this lane, before every push)

`.claude/hooks/ruff-prepush-gate.sh` (`PreToolUse` on
`Bash|mcp__github__push_files`) refuses a push whose *own* changed `.py` files
fail either gate, and names them plus the fix. It is check-only — it never edits
your tree (rule 27 `[R-PUSH]`). Run the two commands yourself anyway: a hook can
be disabled, a session can run without it, and it deliberately does not gate the
whole tree. Run from the repo root and confirm **exit 0** before staging:

```
uv run ruff format --check .
uv run ruff check .
```

**Tree-wide, not just your own files.** `.github/workflows/ci.yml` runs exactly
these two commands over the whole tree, so a formatting miss anywhere turns the
lane's PR red — and the next lane's too.

**If it fails, format only the files it names**, then verify the change carries
no semantic delta before pushing — `git diff -w` is NOT sufficient (ruff reflows
split and join lines, and adds magic trailing commas plus grouping parens, all of
which survive `-w`). Compare the parsed tree instead:
`ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))` per file.

---

**Next shorthand: spp-1.**
