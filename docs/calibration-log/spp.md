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

## 2026-09-07 — spp-1: SPP-40 first SPP solve — rule-29(a) screen (2024) KILLED at the P7 STOP gate

**Result: SCREEN KILLED on the direction leg; the full span was NOT spent; no bundle registered, no
keeper.** Records: `docs/handoffs/PRECOMMIT-spp-40-2026-09-07.md` (pushed at `45d02b0e` before the
solve) and `docs/handoffs/FINDING-spp-40-2026-09-07.md` (every screen number; the bundle
`_spp40_screen` was deleted before merge, rule 29(c)).

- **Recipe**: the all-defaults backcast (`run_calibration_full.py --iso SPP --year 2024`, no other
  flag; `passes ["P1"]`, `commitment false`, `outage_source historic`, served EIA-930 interchange per
  P2, N↔S link 3,400 MW per SPP-53), every offer band **1.0**. Zero-LP phase 0 found SPP coal
  inheriting the generic ERCOT-fitted `COAL` bands (0.90 committed / 1.45 peak) — corrected before the
  solve by the SPP-scoped `_SPP_OFFER_CURVE` identity merge (`pipeline/backcast_config.py`, rule 25;
  six keepers unmoved, 0 surface rows moved). `authorized_price_tuning = NONE`.
- **Screen 2024** (146 s wall, 4.82 GB peak RSS; P0 78.7 s / P1 23.3 s): the 3,400 MW link is LIVE —
  at bound 1,776 h (20.3 %): **877 h N→S, 899 h S→N**. Pre-registered STOP *"S→N > N→S"* fired by
  22 h against a market 1.7:1 N→S dominant. Season leg passed (Spearman +0.14). Fuel mix all within
  [0.1×, 10×]: coal 0.94, gas_cc 0.85, **gas_ct 1.78**, gas_st 0.78, nuclear 0.98, wind 1.12
  (un-recurtailed gross-up delivered in full), hydro 1.00. 0 MWh unserved; **7 negative hours vs
  1,172 measured**; load-weighted price $26.37 vs RT $23.31 / DA $25.92; mean |S−N| zonal spread
  **$0.99 vs $17.23 measured**.
- **Structural reading**: South (Oklahoma / Panhandle) wind and CC export north overnight until the
  link binds, where the market traps that energy inside Oklahoma (`oklahoma_internal` binds 60–68 %
  of hours), curtails it and prices it negative — SPP-57 corroborated as the first lever (P1
  ranking). Nothing tuned; the TTC not moved. Routed: FINDING-spp-53 §6 O-1 / O-2; SPP-57; the
  `NG: WND` 2023 slip on the wind-input path (new); the CT/CC/ST gas split (commitment physics).
- **Desk action**: re-issue SPP-40 with the direction leg re-cut ex ante as a dominance ratio (or
  accept the corridor's bidirectionality) — one ~8-minute full-span solve; the branch carries the
  rule-25 fix, the PRECOMMIT and the FINDING (`build_status.ISO_ORDER += SPP` is the re-issue's,
  landed with `status/SPP.js`).
- Matrix shard: `measured_interface_limits` U → O; `keeper` / `gates` empty. Rule 22: only 2024
  (training tier) solved; nothing registered.

**Next shorthand: spp-2.**
