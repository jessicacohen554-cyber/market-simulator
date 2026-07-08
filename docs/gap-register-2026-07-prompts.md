# Gap Register 2026-07 — parallel prompt pack (code-verified 2026-07-08)

Ready-to-paste handoff prompts for the gaps in `docs/gap-register-2026-07.md` that are
**genuinely open, not in-flight, and in scope**, verified against `origin/main` HEAD on
2026-07-08. Each prompt is self-contained: drop it into a fresh Claude Code session.

> **Scope (owner directive 2026-07-08): focus on the four unfinished ISOs — MISO, CAISO,
> PJM, ERCOT.** NEISO is calibration-complete and NYISO's keeper stands — do not re-tune either.

## Disposition ledger

**LANDED (merged 2026-07-08):**
- **L-7 Cross-ISO SRMC audit (#1302)** — `docs/miso-caiso-srmc-floor-audit-2026-07.md` (#1749).
  Result: MISO's headline defect is **`ST_GAS_INTERMEDIATE.committed = 0.85×`** (uncited generic
  default); CAISO findings scoped too. → unblocks **L-10**.
- **L-8 PJM I7 backstop-on re-run (G-41)** — hindcast bundle landed (#1753).
- **L-9 Seam-ladder provenance (#1350)** — PJM/CAISO ladders labelled static-fitted-pending-measured (#1748/#1752).
- **L-1 ERCOT hindcast G-30** — `entry_lookahead_reprice` arm exercised (#1760). Scarcity now
  forms from the LP regime; over-retire **22.8 → 15.8 GW**, solar 0 → 4 GW. But coal 13.96 GW
  false-retire is UNCHANGED (coal exits in the quarantined 2022 bridge before any forward signal
  reaches the screen). Progressed, not closed → residual is **L-11** (limited-foresight *dispatch*
  screen). Default-off, forecast-side, no keeper touched.
- **L-6 statmode (G-10) — 3/4 done** — ERCOT/CAISO/PJM same-SHA twins landed
  (`ercot46-statmode`, `caiso65-statmode`, `pjm-91-statmode`, #1759/#1762). **MISO twin still
  pending** (~16 GB + swap) — sequence it AFTER L-10 (which may swap the MISO keeper).

**CLOSED — G-16 NEISO ST_GAS C7:** NEISO complete; `neiso-54-steamgas-ct` (#1743) landed the
CT/ST_GAS reliability drag. Not reopening.

**DESCOPED per owner 2026-07-08:**
- **NYISO downstate tail (G-20c)** — keeper stands; residual is #1344 (data-blocked).
- **ERCOT storage energy-vs-AS (G-37)** — mechanism shipped default-off
  (`ercot_storage_as_duration_gate` → `storage_reserve_dispatch`); sub-band is a documented
  limitation, not an active build.

**Already CLOSED (verified at HEAD):** G-42, G-51/G-52, G-26 #1349, G-41 code+decision, G-32,
#1345.

**IN-FLIGHT — do NOT prompt (a session/PR is on it; would duplicate):**
- **L-10 MISO ST_GAS_INTERMEDIATE SRMC re-grounding** — OWNER RUNNING (2026-07-08); MISO keeper
  still miso-47, re-solve in progress. Prompt retained below for reference. L-6b (MISO statmode)
  waits on its outcome.
- **CAISO (G-15 belly + zonal-gas/path-ratings)** — belly-commitment probe + CAISO ST_GAS drag
  (#1733/#1735/#1746/#1750/#1751); measured zonal-gas basis + WECC Path-15/26 ratings LANDED
  (#1754); caiso-67 zonalgas+asympaths A/B in flight (#1761). CAISO's own SRMC re-grounding
  (L-7 scoped it) is gated behind this.
- **PJM (G-21 ST_GAS/SRMC)** — `pjm-90-cchp-srmc` keeper; **owner has midstream PJM fixes in
  progress** — do NOT dispatch PJM calibration lanes; coordinate. PJM still scores **NOT-YET**
  (C1 fuel-mix + C3c scarcity FAIL; C3c = G-20b, brief below).
- **ERCOT** — price-shape/clock settled into the `ercot46` keeper (#1740); a midstream ERCOT
  keeper run is in progress (owner). L-11 (below) is non-keeper but shares `capacity.py`/
  `dispatch.py` — coordinate.

**Data-blocked / accepted:** MISO G-20e, G-26 #1347/#1335/#1336/#1348 + #1344, G-19, G-40.

**Owner decisions — see `docs/handoffs/owner-decision-briefs-2026-07-08.md`:** G-61(b) `caiso-66`
adoption; G-20b PJM reserve magnitude.

## Open lanes (this pack)

| Lane | Gap(s) | ISOs | Solve? | Model |
|---|---|---|---|---|
| **L-11** ERCOT limited-foresight dispatch screen | G-30 residual | ERCOT | SH (non-keeper harness) | Opus/Fable |
| **L-6b** MISO statmode twin (after L-10) | G-10 (MISO) | MISO | SH | Opus |

*(L-10 MISO SRMC re-grounding is OWNER-RUNNING — see IN-FLIGHT above.)*

## How to run

- **DONE:** L-7/L-8/L-9 (no-solve wave), L-1, L-6 (ERCOT/CAISO/PJM statmode). **OWNER-RUNNING:**
  L-10 (MISO SRMC) + a midstream ERCOT keeper run. **Open to dispatch: L-11** (ERCOT G-30 dispatch
  screen); **L-6b** (MISO statmode) waits on L-10's outcome.
- **L-11 (ERCOT hindcast) is non-keeper/forecast-side** — won't touch the ERCOT keeper, but it
  edits `capacity.py` / `dispatch.py` foresight path. The owner's midstream ERCOT run may touch
  those files — coordinate ownership or run L-11 in an isolated worktree.
- Do NOT start a PJM lane (owner midstream fixes) or a CAISO SRMC lane (gated on in-flight CAISO
  input work). Run each solve lane in its own session/environment; **years sequential WITHIN an
  invocation**.
- **Re-verify the current keeper** in `keepers.json` + rebase on `origin/main` before solving.

**Shared rules (CLAUDE.md):** right structure first (#1); measured data only as a reproducible
forward input, never pinned to the residual (#10/#11); a correct mechanism stays even if a metric
worsens — fix the root cause (#11); register every run on the dashboard + commit same-session
(#12); solve ALL scoreable years in one bundle (#16); no hour loops in LP construction; push via
`mcp__github__push_files`.

---

## L-10 — MISO ST_GAS_INTERMEDIATE committed-band SRMC re-grounding  ·  Fable  ·  SH (MISO namespace)  · OWNER-RUNNING

```
Follow-on to the L-7 audit (docs/miso-caiso-srmc-floor-audit-2026-07.md, #1302 /
G-21): MISO's headline SRMC defect is ST_GAS_INTERMEDIATE.committed = 0.85x — a
GENERIC-DEFAULT sub-1.0 multiplier (backcast_config.py:1539-1546), NOT ISO-scoped,
NOT in _GENERIC_NEUTRAL_GAS_CLASSES, with NO physical citation for pricing below
the floor (the class's doc comment justifies only its near-baseload SHAPE, not a
sub-SRMC price). It is live in the current MISO keeper 2026-07-08-miso-47-steamgas-ct
and under-prices the class ~$3.3-5.2/MWh ((1.00-0.85) x 9.917 base_HR). This is
the exact pjm-83 defect pattern. Owns the MISO registry/bundle namespace +
MISO-only offer sections. MISO is NOT in-flight — clean lane. Re-verify the MISO
keeper in keepers.json first.

Task: re-ground ST_GAS_INTERMEDIATE.committed from 0.85 -> 1.00x its own base_HR
SRMC floor (MISO cost-based-offer floor, Tariff Module C / Attachment L, sanity
against the MISO IMM/Potomac SOM — backcast_config.py:630-633). LEAVE the
CC_REGULAR econ_low 0.95 band alone (the audit rules it SURVIVES on MISO's own
CAMPD flat-body marginal-HR physics, ~0.93-0.95x avg — a recognized CC exception,
not a defect). Do not touch any other class. Re-solve MISO all years (2023 2024
2025, one bundle, rule 16).

Per rule 1/11 this is a STRUCTURE fix promoted on correctness even if it worsens a
metric: expect the dear-gas ST_GAS volume to shift (C1 fuel-mix / C2 sysvol may
move) — if it relocates a residual, that is a discovered root cause to attribute,
NOT a reason to revert to 0.85. Register the run on the dashboard; present the
keeper-swap as an owner decision with the before/after C1/C2/C3 deltas.

Deliverable: the re-grounded MISO bundle registered + a swap memo. Honesty gate:
1.00x is the tariff SRMC floor (measured base_HR x delivered gas + VOM), not a
value tuned to a residual.
```

---

## L-11 — ERCOT limited-foresight dispatch screen (G-30 residual)  ·  Opus/Fable  ·  SH (non-keeper harness)

```
Follow-on to L-1 (docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md):
the entry_lookahead_reprice arm cut ERCOT hindcast over-retire 22.8 -> 15.8 GW and
made solar entry non-zero, BUT the headline coal 13.96 GW false-retire is
UNCHANGED. Root cause (from the finding, NOT a fit target): the FIRST
economic-retirement wave exits coal in the quarantined 2022 bridge on the 2021
raw-dual signal (ORDC ~ 0 on the un-thinned over-supplied fleet), BEFORE any
admissible forward signal reaches the screen — the entry-side lookahead only bites
waves 2+ (2024/25). Owns the hindcast harness scripts + model/capacity.py +
model/dispatch.py foresight path. NON-KEEPER, forecast-side — no quarantine, no
keeper/backcast touched. COORDINATION: an ERCOT run may be live in another session
— confirm no one else is editing capacity.py / dispatch.py's foresight path, or
work in an isolated worktree.

Task: build a LIMITED-FORESIGHT *dispatch* screen so the in-year LP itself forms
scarcity on the over-supplied vintage fleet (which also fixes the inert ORDC
overlay), instead of the perfect-foresight LP clearing every hour with ample
reserves. And/or a staged vintage-over-supply thinning so the first coal
retirement wave spreads into lookahead-priced years rather than firing all at once
on the 2021 raw dual. Gate: does the coal false-retire drop from the LP regime
(not a floor/adder)? The 13.96 GW over-retire and 0-scarcity are DIAGNOSTICS to
close via root cause (rule 11), never fit targets.

Deliverable: the limited-foresight dispatch screen (and/or staged thinning)
exercised on the hindcast, both registered on forecast-validation, + a finding on
whether the coal wave now spreads and scarcity forms in-year. Honesty gate:
scarcity forms from the LP regime, never an adder tuned to a retirement number.
```

---

## L-6b — MISO statmode D-7 twin (after L-10)  ·  Opus  ·  SH

```
G-10 remainder: ERCOT/CAISO/PJM same-SHA D-7 statmode twins already landed
(2026-07-08-{ercot46,caiso65,pjm-91}-statmode, #1759/#1762). The MISO twin is the
only one left. SEQUENCE THIS AFTER L-10 — L-10 may swap the MISO keeper, and a
statmode twin must replay the CURRENT keeper at one pinned SHA. Owns
docs/statistical-mode-results-2026-07.md + the MISO statmode registry sidecar ONLY
— do NOT change any keeper config (FROZEN-recipe replay, not a re-tune).

Task: once the MISO keeper is settled (post-L-10 or confirmed unchanged at
miso-47), replay the MISO keeper recipe at one pinned HEAD SHA in statistical mode
so its D-7 r2/v2 twin is same-SHA-comparable. Solve all scoreable years in one
bundle (rule 16); years sequential within the invocation; MISO needs ~16 GB + swap.
Update the doc's stale-boxes + re-solve queue to CURRENT.

Deliverable: the MISO same-SHA statmode twin registered + stale-box cleared,
committed and pushed. Honesty gate: a D-7 number may be quoted as skill only once
its twin is a same-SHA replay of the current keeper.
```

---

*Verified 2026-07-08 against `origin/main` HEAD. Landed since the audit: L-7/L-8/L-9 (no-solve
wave), L-1 (G-30 lookahead — progressed 22.8→15.8 GW, residual → L-11), L-6 ERCOT/CAISO/PJM
statmode twins. Owner-running: L-10 (MISO SRMC) + a midstream ERCOT run. Open: L-11 (ERCOT G-30
dispatch screen), L-6b (MISO statmode, after L-10). Descoped: NEISO (complete), NYISO (keeper
stands), G-37. PJM is owner-midstream + still NOT-YET; CAISO SRMC re-grounding gated on in-flight
CAISO input work. Owner decisions in `docs/handoffs/owner-decision-briefs-2026-07-08.md`. Board
churns hourly — re-verify keepers.json + rebase before solving.*
