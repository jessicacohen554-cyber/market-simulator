# Gap Register 2026-07 — parallel prompt pack (code-verified 2026-07-08)

Ready-to-paste handoff prompts for the gaps in `docs/gap-register-2026-07.md` that are
**genuinely open, not in-flight, and in scope**, verified against `origin/main` HEAD on
2026-07-08 (five read-only code/artifact audits, not the register prose). Each prompt is
self-contained: drop it into a fresh Claude Code session on this repo.

> **Scope (owner directive 2026-07-08): focus on the four unfinished ISOs — MISO, CAISO,
> PJM, ERCOT.** NEISO is calibration-complete (`calibration-complete.json`) and NYISO's
> keeper stands — do not re-tune either. NEISO (L-4) and NYISO (L-5) lanes are descoped.

## Disposition ledger

**DESCOPED per owner 2026-07-08 — do not pursue:**
- **L-4 NEISO ST_GAS C7 (G-16)** — NEISO is calibration-COMPLETE; C7 is an accepted ledgered
  caveat, not a blocker. Leave the keeper frozen.
- **L-5 NYISO downstate tail (G-20c)** — NYISO keeper stands; the deep 2024/25 tail residual is
  #1344 (data-blocked). Leave it.
- **L-2 ERCOT storage energy-vs-AS (G-37)** — the mechanism IS built and shipped:
  `ercot_storage_as_duration_gate` → `storage_reserve_dispatch` (dispatch.py:1255/3040-3044/3846)
  makes the energy-vs-AS split the LP's own choice. The sub-band validation (0.54–0.61×) is a
  documented default-off limitation the FINDING scopes out (two forward-uncertainty mechanisms),
  not an active build. Treated as addressed.

**Already CLOSED (verified at HEAD):** G-42 (Mode-A tiebreak, ADR 0019), G-51/G-52 (README
canonical-install + rule-16 caveat), G-26 #1349 (dead code deleted), G-41 code+decision
(market-design I7 split, `00bbd4b` — only a confirmation re-run remains → L-8), G-32 (FOM flip
+ foresight A/B), #1345 (NYISO LI 0.45 → `nyiso_li_lcr_tsl`).

**IN-FLIGHT — a session/PR is on it; do NOT prompt (would duplicate):**
- **CAISO belly commitment (G-15)** — belly-grounding diagnostic + CAISO ST_GAS overnight drag
  landed (PRs #1733/#1735). The core CAISO backcast-calibration gap is being worked now.
- **PJM ST_GAS volume driver (G-21/#1483)** — overnight pre-positioning drag (PR #1728);
  `pjm-89`/`pjm-90` (CC_CHP-SRMC) keeper-candidates in flight.
- **ERCOT price-shape / clock (G-22)** — clock-unification round settled into the `ercot46`
  keeper (PR #1740); the offer-surface leg lives here.

**Data-blocked / accepted — no prompt:** MISO G-20e (no published Midwest zonal reserve
requirement; G-25 posture lever rejected), G-26 #1347/#1335/#1336/#1348 + #1344, G-19, G-40.

**Owner decisions — surface, don't dispatch:** G-61(b) `caiso-66` adoption; G-20b PJM reserve
magnitude (`pjm-87`/`pjm-88`); G-21 `pjm-89`/`pjm-90` adjudication.

> **Reality check for the four target ISOs:** their live *backcast calibration* is mostly
> in-flight (CAISO/PJM/ERCOT above) or data-blocked (MISO). The lanes below are the free,
> non-colliding work — forecast-side, cross-ISO audit, and provenance hygiene.

## Open lanes (this pack)

| Lane | Gap(s) | ISOs | Solve? | Model |
|---|---|---|---|---|
| **L-1** ERCOT hindcast scarcity/retirement regime | G-30 (narrowed) | ERCOT | SH (non-keeper harness) | Opus/Fable |
| **L-6** Statmode D-7 same-SHA re-solves | G-10 | ERCOT/CAISO/PJM/MISO | SH | Opus |
| **L-7** Cross-ISO SRMC committed-band audit | #1302 | MISO/CAISO/PJM | no | Sonnet |
| **L-8** PJM I7 backstop-on confirmation re-run | G-41 remainder | PJM | light forecast | Sonnet/Opus |
| **L-9** Seam-ladder provenance comments | G-26 #1350 | PJM/CAISO | no | Sonnet |

## How to run these in parallel

- **No-solve / light lanes (L-7, L-8, L-9): run all concurrently, any tier** — disjoint files,
  no keeper bundle touched.
- **Solve lanes (L-1, L-6): run each in its OWN session/environment and both can go at once.**
  CLAUDE.md rule 12's "≤2 concurrent" is a *per-machine memory* limit (one box OOMs on 2+
  per-plant multi-zone LPs) — it does not cap separate environments, each with its own RAM. The
  invariant that always holds: **years run sequentially WITHIN a single invocation**
  (`--year 2023 2024 2025` is never parallelized).
- **Every solve lane re-verifies the current keeper** in `frontend/data/backcast/keepers.json`
  and rebases on `origin/main` first — the board churns hourly.

**Shared rules every prompt inherits (CLAUDE.md):** right structure first, level second (#1);
measured data only as a reproducible forward-regenerating input, never an outcome pinned to the
residual (#10/#11); a structurally-correct mechanism stays even if it worsens a metric — fix the
root cause (#11); register every completed backcast run on the dashboard (`calibration-report` +
`build_manifest.py`) and commit it same-session (#12); solve ALL scoreable years in one bundle
(#16); no Python loops over hours in LP construction; push via `mcp__github__push_files`.

---

## L-7 — Cross-ISO SRMC committed-band audit (#1302)  ·  Sonnet  ·  no solve

```
#1302 (docs/gap-register-2026-07.md G-21 row) generalizes the PJM Manual-15 SRMC
committed-band re-grounding (landed as the pjm-83 keeper) to the other target
ISOs' committed offer bands. Scope: MISO and CAISO (NYISO/NEISO are out of scope
per owner directive; PJM is the worked reference, actively re-grounding CC_CHP
SRMC via the pjm-90 candidate). DESIGN + AUDIT only — no solves, no keeper touch.

For MISO and CAISO: locate each ISO's committed/must-run offer bands in the offer
path (offer_curves.py, the per-ISO sigmoid/tranche overrides in config/scenarios.py
+ constants.py) and compare each sub-SRMC band multiplier to that ISO's OWN cited
SRMC floor (fuel heat-rate x delivered fuel + VOM). Report, per ISO: which
committed bands sit BELOW their SRMC floor (the pjm-83 defect pattern), the
citation backing the current multiplier, and whether it is an ISO-local fitted
value or an ERCOT byte-copy (rule 25 — a multiplier fitted on one ISO's residual
must not cross an ISO boundary; the MISO sigmoid family's floor/gas_mid/gas_slope
are flagged ERCOT byte-copies in the register).

Deliverable: a MISO+CAISO SRMC-floor audit table + a per-ISO re-grounding recipe
(which band -> 1.00x SRMC floor, with the citation), written to a short handoff
doc, committed and pushed. Do NOT change any numeric offer value (that changes a
solve). Honesty gate: this scopes the work; each ISO's re-grounding + re-solve is
its own lane and its own keeper decision.
```

---

## L-8 — PJM hindcast I7 backstop-on confirmation re-run (G-41 remainder)  ·  Sonnet/Opus  ·  light forecast

```
G-41's code + owner decision already landed: resolve_reserve_margin_build_enabled
(model/capacity.py:2143) implements the market-design split (backstop ON for
capacity-market ISOs incl. PJM, OFF for energy-only ERCOT); commit 00bbd4b. The
checker check_i7_reliability_floor was reconciled and already flips I7 FAIL->PASS
on the existing backstop-OFF bundle. FORECAST-SIDE ONLY — no keeper, no backcast
re-gate, no quarantine concern. Owns docs/hindcast-reports/pjm-i7-g41-2026-07-07.md
and the PJM hindcast harness only.

The ONE remaining item: docs/hindcast-reports/pjm-i7-g41-2026-07-07.md line ~40
carries an unfilled marker (<!-- G41_RESOLVE_MARKER ... filled after the
backstop-on PJM re-run -->) and claims a bundle results/hindcast/pjm-2021-2025-
realized-g41 that DOES NOT EXIST. Produce that backstop-default-on PJM hindcast
re-run, confirm I7 PASSES with the backstop actually building (not just the
checker reconciliation), fill the marker with the real numbers, and confirm the
ERCOT hindcast is unchanged (energy-only -> retirement-bounded, backstop stays off).

Deliverable: the backstop-on PJM hindcast bundle + the filled marker + a one-line
ERCOT-unchanged control, committed and pushed. Honesty gate: forecast-mode
capacity-adequacy structure (rule 1); report whatever the re-run shows.
```

---

## L-9 — Seam-ladder provenance comments (G-26 #1350)  ·  Sonnet  ·  no solve

```
G-26 #1350 in docs/gap-register-2026-07.md. MISO and NEISO seam import/export
tranches are now MEASURED, derived ladders (interchange_config.MISO_SEAM_LADDER_
BY_YEAR; IMPORT_TRANCHES_BY_YEAR["NEISO"] via scripts/derive_neiso_import_tranches.py).
The PJM and CAISO ladders are still bare/near-static literals with weaker
provenance: IMPORT_TRANCHES["PJM"] (interchange_config.py ~:122, no by-year entry
at all) and IMPORT_TRANCHES_BY_YEAR["CAISO"] (~:165, prices identical across all
three years per its own comment). Owns src/market_sim/config/interchange_config.py
(comments only).

Task: for the PJM and CAISO seam ladders, add a citation comment stating the
source/derivation status and an open-issue pointer (#1350 / #C-6) so each literal
is honestly labelled as static-fitted-pending-measured, matching the MISO/NEISO
derived-ladder provenance style. Do NOT change any tranche number or price (that
changes a solve). This is truth-in-labelling for rule-24/rule-11 transparency only.

Deliverable: the provenance comments + a note in the register's G-26 row marking
#1350 PJM/CAISO as labelled-open (MISO/NEISO closed), committed and pushed.
Honesty gate: byte-identical LP — comments only.
```

---

## L-1 — ERCOT hindcast scarcity/retirement regime (G-30, narrowed)  ·  Opus/Fable  ·  SH (non-keeper harness)

```
G-30 in docs/gap-register-2026-07.md, NARROWED by a 2026-07-08 code audit: the
co-scoped G-32 work the register listed as the task is DONE — the ATB FOM flip
landed (scenarios.py:264-282, fixed_om_gas_cc=30 / gas_ct=21 / coal=45, "G-32")
and the foresight A/B re-ran (docs/handoffs/foresight-ab-ercot-2026-07-0{6,7}.*;
fom-scarcity-defaults-flip-2026-07-07.md "Closes G-32"). Do NOT redo those.

What REMAINS open: the hindcast SYMPTOM persists at HEAD despite the FOM flip.
docs/hindcast-reports/ercot-2021-2025-realized-2026-07-07.md still shows solar
additions 0.0 GW (-100% FAIL), coal retire +13.96 GW / gas_st +8.83 GW (~22.8 GW
over-retirement), CO2 -49%. The corrective arm entry_lookahead_reprice is
default-OFF (scenarios.py:815) and the foresight work is forecast-scoped. Owns the
hindcast harness scripts + model/capacity.py. NON-KEEPER, forecast-side — no
quarantine.

Task: determine why the hindcast forms ZERO scarcity hours even after the FOM
flip (perfect-foresight LP on the over-supplied 2020-vintage fleet vs un-grown
realized demand -> ORDC overlay inert -> solar can't clear fixed cost -> whole
coal/gas_st fleet below FOM bar). Evaluate the built-but-off entry_lookahead_reprice
(and/or a limited-foresight screen) ON the hindcast: does tempering foresight let
scarcity form so solar entry clears and the false-retire (96% genuine per the
G-31 per-plant scoring) drops? Over-retirement and 0-GW-solar are DIAGNOSTICS to
close via root cause, never fit targets (rule 11).

Deliverable: the hindcast re-run with the foresight/entry mechanism exercised,
registered, + a note on whether scarcity now forms. Honesty gate: scarcity forms
from the LP regime, never an adder tuned to a retirement or entry number.
```

---

## L-6 — Statmode D-7 same-SHA twin re-solves (G-10)  ·  Opus  ·  SH

```
G-10 in docs/gap-register-2026-07.md, GENUINELY-OPEN (2026-07-08 audit: NO statmode
bundle exists for any current keeper). Scope: the four unfinished ISOs — ERCOT,
CAISO, PJM, MISO (NYISO/NEISO out of scope per owner directive). Current keepers
(re-verify in keepers.json; churn fast): ercot46-clock-steamgas / caiso65 / pjm-83
/ miso-47-steamgas-ct (ERCOT churned 42->46, MISO 46->47 on 2026-07-08; a pjm-90
CC_CHP-SRMC candidate is in flight — confirm the live PJM keeper before replaying).
Every statmode registry sidecar replays a SUPERSEDED bundle (caiso51/58, miso39,
ercot34). Owns docs/statistical-mode-results-2026-07.md + the statmode registry
sidecars ONLY — do NOT change any keeper config (FROZEN-recipe replay at one SHA,
not a re-tune).

Task: for each of the four in-scope keepers, replay the keeper recipe at one
pinned HEAD SHA in statistical mode so the D-7 r2/v2 twin is same-SHA-comparable to
the keeper. Solve all scoreable years per bundle (rule 16). Years run sequentially
WITHIN each invocation (rule 12 within-box OOM); separate sessions/environments may
run different keepers' twins concurrently. MISO needs ~16 GB + swap. Update the
doc's stale-boxes + re-solve queue to CURRENT as each twin lands.

Deliverable: the four same-SHA statmode twins registered + the doc's stale-boxes /
queue cleared to current (for the in-scope ISOs), committed and pushed. Honesty
gate: a D-7 number may be quoted as skill only once its twin is a same-SHA replay
of the current keeper.
```

---

*Verified 2026-07-08 against `origin/main` HEAD via five read-only code/artifact audits, then
refocused per owner directive (same day) onto the four unfinished ISOs — MISO/CAISO/PJM/ERCOT.
Descoped: NEISO (complete), NYISO (keeper stands), G-37 (mechanism shipped default-off). The
four ISOs' live backcast calibration is mostly in-flight (CAISO belly, PJM ST_GAS, ERCOT clock)
or data-blocked (MISO); the lanes above are the free forecast/audit/hygiene work. The board
churns hourly — each session re-verifies keepers.json + rebases before solving.*
