# Last-Day Usage Plan — 2026-07-11

A prioritized plan for spending one final day of Claude usage on this repo, built from
the actual open state as of this morning: `keepers.json` (incl. the NEISO/NYISO frontier
declarations), `calibration-complete.json` (NEISO only), the 2026-07-11 calibration-log
entries (miso-56, caiso-76), `owner-decision-briefs-2026-07-08.md`,
`probability-bounds-plan-2026-07.md`, and `09-ercot-propagation-prompt-pack.md`.

**Organizing principle:** the box solves ~2 concurrent LPs and a 25-year forecast member
takes ~2 h — so the compute-heavy lane must start in the first minutes of the day and run
in the background while agent-parallel code/docs work fills the foreground. Everything
must be committed and pushed the same session (rule 15; the container is ephemeral).

---

## Lane A — PB-5: the production ERCOT probability band (START FIRST)

The single highest-leverage unfinished deliverable. The entire probability-bounds
program (PB-0 scenario matrix, PB-2 multivariate sampler, PB-3 structural prior,
weather-year ensemble) is **built and merged** — but PB-5, the production ERCOT
2026–2050 band run, has never been executed. This is the model's actual purpose
(it is a *forecasting* model; every recent session has been backcast calibration).

- Kick off the ensemble members as background invocations at day start, capped at
  2 concurrent (rule 12), years sequential within each invocation.
- Foreground work continues while it solves; check in on members periodically.
- Deliverable: the first emissions forecast with a defensible probability statement,
  registered + pushed, with sampler spec/seed echoed into `run_config.json` (rule 24).
- Forecast-mode 2026+ runs are unrestricted under rule 22 (no measured H1-2026 inputs).

## Lane B — Clear the pending owner decisions (minutes each; batch them up front)

Three build-exhausted decisions are gating finished work. Answering all of them in one
message at day start unblocks the corresponding pushes without round-trips:

1. **MISO — promote `2026-07-11-miso-56-measured-scarcity`?** Recommended in the
   2026-07-11 calibration-log entry: supersedes miso-55 on structural grounding
   (two measured series replace two wrong estimates), score flat-to-better, zero fitted
   scalars. Keeper currently held at miso-54 pending this call. Scorer/registry-only
   swap + `build_status.py` + keeper-auditor agent — cheap.
2. **CAISO — G-61(b): ship `caiso-66` (startup-aware RA bridge)?** Brief recommends
   adopt-bundled-with-G-15 belly grounding. Decide: is G-15 far enough along to bundle
   today, or adopt caiso-66 standalone with the λ miss attributed to the documented
   belly gap? (The brief explicitly forbids reverting to phantom anchoring either way.)
3. **PJM — G-20b:** brief says hold `pjm-87`/`pjm-88` (reserve dual fires in the right
   regime but at $0–10 vs the $75–200 residual). Confirm the hold stands so no one
   re-opens it.

## Lane C — MISO RDT S→N congestion (the largest quantified residual lead)

The IMM attributes the 2025 MISO tail to Midwest–South separation of **$9.31/MWh; the
model carries $0.19**. This is a measured transmission-lane build (RDT limit intake →
`interchange_config.py` / `transmission.py`), squarely rule-13-admissible, and the
calibration log names it first in measured-impact order. A full build-probe-register
cycle (3 solve-years, ~30–60 min MISO solves) fits alongside Lane A's 2-concurrent cap
if scheduled after Lane A's first members finish, or run at cap-2 with Lane A at cap-1.
Use `/deep-research` for the RDT limit sourcing if the raw data isn't already on disk.

## Lane D — Holdout one-shots (IRREVERSIBLE — owner-only, only if confident)

NYISO declared **frontier** on 2026-07-11 (no admissible mechanism remains for its last
gap). If the owner judges NYISO calibration-complete, today is a natural day to:
- add the NYISO marker to `calibration-complete.json` (frozen keeper `nyiso-61`),
- run the 2022 validation solve, then the **touch-once** 2019 + H1-2026 locked test.

NEISO already has its marker and its locked test is scored and stands. **Do not** do
this for any ISO with open decision lanes (MISO/CAISO/PJM). A locked-test score can
never be responded to — this is the one action on the list that cannot be redone, so
skip it entirely if there is any doubt.

## Lane E — ERCOT propagation pack (doc 09): W0 + W1a/W1b/W1c

Most of the pack is open (only W1c done). W0 (parity baseline + byte-identity guard) is
the hard gate; after it merges, W1a (per-ISO planning reserve margins), W1b (CAMPD
binning unlock for CAISO/NEISO/NYISO/PJM + per-ISO outage-overlay default) run in
parallel worktrees. This is high-value *structural* work (rule 1) that benefits every
ISO's next calibration cycle — a good multi-agent lane: say **"use a workflow"** to
authorize fan-out (one agent per wave, byte-identity verification stage).

## Lane F — Hygiene sweep (cheap, agent-parallel, do while Lane A solves)

- **Docs reorg** per `multi-iso-triage-2026-07.md`: 27 files → sessions-archive,
  8 flagged open — mechanical, fully specified, never executed.
- **Fleet-group backfill fix** (2026-07-11 log follow-up): bucket the CAMPD backfill by
  unit prime-mover class instead of plant (WA-Parish / Doswell mixed-fuel mis-bucketing;
  display + preliminary-vintage only, so low risk).
- **`/sync-docs`** at end of day, after the approach settles.
- Dashboard retention check (top-15 per ISO) + `calibration-keeper-auditor` agent pass
  if any keeper swapped.

---

## How to actually extract maximum value from the day (feature leverage)

- **Background everything long-running.** Solves launch as background jobs; Claude keeps
  working the foreground lanes and gets woken when they finish. Never let the box idle.
- **Multi-agent workflows need explicit opt-in.** Saying **"use a workflow"** (or
  "ultracode") in a message authorizes orchestrated fan-out — e.g. Lane E's parallel
  waves with an adversarial byte-identity verify stage, or a repo-wide audit
  (rule-24 off-registry-knob sweep, `/code-review` at high effort over recent merges).
- **Batch your decisions.** The plan blocks only on Lane B's three calls and Lane D's
  go/no-go. One message answering all four at day start means zero mid-day round-trips.
- **Push early, push often** via `mcp__github__push_files` (never `git push` — HTTP 413).
  Anything not pushed when the container is reclaimed is gone.
- **`/deep-research`** for external sourcing (RDT limits, any primary-document citation
  gaps in `parameter-citations.md`) runs as an agent while solves occupy the CPUs.

## Recommended single-day sequencing

| When | Foreground | Background |
|---|---|---|
| Start | Owner answers Lane B ×3 + Lane D go/no-go in one message | **Lane A members launch (2×)** |
| Morning | Lane B keeper swaps/registrations; Lane F agents (docs reorg, backfill fix) | Lane A |
| Midday | Lane C build (or Lane E W0 if C's data is missing) | Lane A ↔ Lane C solves share the 2-cap |
| Afternoon | Lane C probe scoring + registration; Lane E W1a/W1b if time | remaining Lane A members |
| End | PB-5 band assembly + dashboard registration; `/sync-docs`; final push audit | — |

If the day shrinks, the cut order is: drop E, then C, then D (D was optional anyway).
**Never cut the end-of-day push audit** — an unregistered, unpushed run doesn't exist
(rule 15).
