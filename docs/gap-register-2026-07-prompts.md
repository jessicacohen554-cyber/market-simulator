# Gap Register 2026-07 — parallel prompt pack (code-verified 2026-07-08)

Ready-to-paste handoff prompts for the gaps in `docs/gap-register-2026-07.md` that are
**genuinely open, not in-flight, and in scope**, verified against `origin/main` HEAD on
2026-07-08. Each prompt is self-contained: drop it into a fresh Claude Code session.

> **Scope (owner directive 2026-07-08): focus on the four unfinished ISOs — MISO, CAISO,
> PJM, ERCOT.** NEISO is calibration-complete and NYISO's keeper stands — do not re-tune either.

## Disposition ledger

**LANDED this session (first no-solve wave — all merged 2026-07-08):**
- **L-7 Cross-ISO SRMC audit (#1302)** — `docs/miso-caiso-srmc-floor-audit-2026-07.md` (#1749).
  Result: MISO's headline defect is **`ST_GAS_INTERMEDIATE.committed = 0.85×`** (uncited generic
  default); CAISO findings scoped too. → unblocks **L-10**.
- **L-8 PJM I7 backstop-on re-run (G-41)** — hindcast bundle landed (#1753).
- **L-9 Seam-ladder provenance (#1350)** — PJM/CAISO ladders labelled static-fitted-pending-measured (#1748/#1752).

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
- **CAISO (G-15 belly + zonal-gas/path-ratings)** — belly-commitment probe + CAISO ST_GAS drag
  (#1733/#1735/#1746/#1750/#1751); the measured PG&E/SoCal zonal-gas basis + WECC Path-15/26
  ratings patch LANDED (#1754). CAISO's own SRMC re-grounding (L-7 scoped it) is gated behind this.
- **PJM (G-21 ST_GAS/SRMC)** — `pjm-90-cchp-srmc` keeper; **owner has midstream PJM fixes in
  progress** — do NOT dispatch PJM calibration lanes; coordinate. PJM still scores **NOT-YET**
  (C1 fuel-mix + C3c scarcity FAIL; C3c = G-20b, brief below).
- **ERCOT price-shape / clock (G-22)** — settled into the `ercot46` keeper (#1740).

**Data-blocked / accepted:** MISO G-20e, G-26 #1347/#1335/#1336/#1348 + #1344, G-19, G-40.

**Owner decisions — see `docs/handoffs/owner-decision-briefs-2026-07-08.md`:** G-61(b) `caiso-66`
adoption; G-20b PJM reserve magnitude.

## Open lanes (this pack)

| Lane | Gap(s) | ISOs | Solve? | Model |
|---|---|---|---|---|
| **L-10** MISO ST_GAS_INTERMEDIATE SRMC re-grounding | #1302 / G-21 (MISO) | MISO | SH | Fable |
| **L-1** ERCOT hindcast scarcity/retirement regime | G-30 (narrowed) | ERCOT | SH (non-keeper harness) | Opus/Fable |
| **L-6** Statmode D-7 same-SHA re-solves | G-10 | ERCOT/CAISO/PJM/MISO | SH | Opus |

## How to run

- **The no-solve first wave (L-7/L-8/L-9) is done.** The remaining lanes are solve-heavy — run
  each in its OWN session/environment; they can all go at once (rule 12's ≤2 cap is per-machine,
  not per-environment). **Years run sequentially WITHIN a single invocation.**
- **L-10 is MISO-only and MISO is not in-flight** (miso-47 promoted, no active MISO session) — a
  clean lane. Do NOT start a PJM lane (owner's midstream fixes) or a CAISO SRMC lane (gated on the
  in-flight CAISO input work).
- **Re-verify the current keeper** in `keepers.json` + rebase on `origin/main` before solving.

**Shared rules (CLAUDE.md):** right structure first (#1); measured data only as a reproducible
forward input, never pinned to the residual (#10/#11); a correct mechanism stays even if a metric
worsens — fix the root cause (#11); register every run on the dashboard + commit same-session
(#12); solve ALL scoreable years in one bundle (#16); no hour loops in LP construction; push via
`mcp__github__push_files`.

---

## L-10 — MISO ST_GAS_INTERMEDIATE committed-band SRMC re-grounding  ·  Fable  ·  SH (MISO namespace)

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
(re-verify in keepers.json; churn fast): ercot46-clock-steamgas / caiso65 /
pjm-90-cchp-srmc / miso-47-steamgas-ct (all churned 2026-07-08 — re-verify before
replaying; note L-10 may swap the MISO keeper). Every statmode registry sidecar
replays a SUPERSEDED bundle (caiso51/58, miso39, ercot34, pjm-77/83). Owns
docs/statistical-mode-results-2026-07.md + the statmode registry sidecars ONLY —
do NOT change any keeper config (FROZEN-recipe replay at one SHA, not a re-tune).

Task: for each in-scope keeper, replay the keeper recipe at one pinned HEAD SHA in
statistical mode so the D-7 r2/v2 twin is same-SHA-comparable. Solve all scoreable
years per bundle (rule 16). Years run sequentially WITHIN each invocation; separate
sessions may run different keepers' twins concurrently. MISO needs ~16 GB + swap.
Update the doc's stale-boxes + re-solve queue to CURRENT as each twin lands.

Deliverable: the same-SHA statmode twins registered + the doc's stale-boxes cleared
to current, committed and pushed. Honesty gate: a D-7 number may be quoted as skill
only once its twin is a same-SHA replay of the current keeper.
```

---

*Verified 2026-07-08 against `origin/main` HEAD. First no-solve wave (L-7/L-8/L-9) landed and
merged; L-7's audit unblocked L-10. Descoped: NEISO (complete), NYISO (keeper stands), G-37.
PJM is owner-midstream + still NOT-YET; CAISO SRMC re-grounding is gated on in-flight CAISO input
work. Owner decisions in `docs/handoffs/owner-decision-briefs-2026-07-08.md`. The board churns
hourly — each session re-verifies keepers.json + rebases before solving.*
