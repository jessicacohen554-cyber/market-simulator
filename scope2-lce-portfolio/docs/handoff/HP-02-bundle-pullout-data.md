# HP-02 — Bundle pull-out data + standalone extraction smoke test

**Model:** Sonnet · **Depends on:** nothing (parallel-safe with HP-01) ·
**Unblocks:** HP-04, HP-05
**Targets:** `data/profiles/`, `data/emissions/`, `data/bundled/` (new),
`.gitignore`, `scripts/verify_standalone.sh` (new), `PLAN.md`

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are finalizing the standalone Scope 2 LCE portfolio tool in
scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator). Develop
on a fresh branch off latest origin/main named scope2/hp-02-bundle-data (or
your session's designated branch); push there; open NO pull request.

GOAL
Today the tool needs the parent market-simulator data tree at build time:
data/profiles/ (per-ISO CF Parquets), data/emissions/ (hourly fossil-avg CO2
rates), and a real BAU LMP export are all gitignored and rebuilt from the
parent repo. After this task, the scope2-lce-portfolio/ folder can be copied
OUT of the repo and run real-ISO analyses with zero parent-repo access.

CONTEXT (read first)
- scope2-lce-portfolio/PLAN.md §6 (data), .gitignore (what's ignored and why)
- scripts/build_profiles.py, scripts/build_fossil_avg_co2_rate.py (both take
  --market-sim-root, default ..)
- docs/validation-2026-07-05-ercot-2024-backcast.md and
  docs/validation-2026-07-05-5iso-backcast-extension.md — how the six real
  2024 backcast LMP exports and dispatch caches were produced (per-ISO
  bridge re-solves from calibration keepers)
- data/inputs/bau_lmp_2026_dummy.csv.provenance.json — the provenance-sidecar
  pattern to follow for every bundled file.

REQUIREMENTS
1. CF profiles: run scripts/build_profiles.py --year 2024 for all six ISOs
   against the parent tree (it exists in this checkout); commit the resulting
   per-ISO Parquets under data/profiles/ and flip the .gitignore rule so
   committed profiles are versioned (keep a comment: regenerate with the
   script when the source data updates — rule: derived-but-bundled).
2. Real BAU LMPs: locate or regenerate the six 2024 backcast LMP exports the
   results/*_backcast2024_premiumcap runs consumed (their run_metadata.json
   records the input paths; the validation memos document the bridge
   procedure if regeneration is needed — a bridge re-solve is minutes-long
   per ISO and years must run sequentially within one invocation). Commit
   them under data/bundled/lmp/ with one provenance sidecar each (source
   keeper run id, solve date, schema). If an ISO's export genuinely cannot
   be reproduced in this session, commit the ones that can, and record the
   gap explicitly in PLAN.md §6 and docs/handoff/README.md — never silently
   skip.
3. Fossil-avg CO2 rates: same treatment via
   scripts/build_fossil_avg_co2_rate.py for whichever ISO-2024 dispatch
   caches are available; commit under data/emissions/ (flip its gitignore
   rule); document any ISO gaps the same way. The tool must degrade
   gracefully where a rate file is absent (it already treats the emission
   file as optional — verify, don't assume).
4. Reference load stays generated-on-demand (scripts/make_reference_load.py
   is inside the tool) — no change.
5. New scripts/verify_standalone.sh: copies scope2-lce-portfolio/ to a temp
   dir OUTSIDE the repo, creates a fresh venv, pip installs
   requirements.txt, then runs: pytest -q; examples/run_sample_sweep.py; a
   real-ISO CLI run using ONLY bundled data (e.g. ERCOT 2024 bundled LMP +
   committed profiles + the reference-load generator) asserting a
   report.html is produced; and `python -m lce_portfolio.launcher --no-open
   --port 0` smoke (start, hit /, shut down — mirror
   tests/test_launcher.py's approach). The script must fail loudly on any
   step and must not touch the parent repo from inside the copy.
6. Run the script; paste its passing output into the session summary; record
   the bundle inventory (files, sizes, provenance) in PLAN.md §6.

SIZE / PUSH DISCIPLINE
Bundled files are small (profiles ~100 KB/ISO, LMP CSVs ~150 KB/ISO) but the
remote 413s on large git packs: commit bundled data via
mcp__github__push_files (one call per logical group), source/docs via normal
small git pushes rebased on origin/main. Never retry a 413'd git push more
than once.

INVARIANTS
- No `import market_sim` anywhere (grep guard). The build scripts may READ
  the parent tree in this session (that is their documented job) but nothing
  under src/ or the bundled data may require it afterward.
- Immutable-source discipline: never modify anything under the parent repo's
  data/raw/. All verify commands green before each commit. No raw model IDs
  in commits/code. Imperative present-tense commit messages.
```
