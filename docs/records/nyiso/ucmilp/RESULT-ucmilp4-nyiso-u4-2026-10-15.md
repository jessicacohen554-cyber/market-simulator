# RESULT — UC-4-NYISO: arm U4 at engine uc-1.7 — **KILL #1 (engine defect), no leg solved, no verdict on the arm**

**Lane:** UC-4-NYISO · **Session:** `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · **Date:** 2026-10-15 · **Branch:** `claude/ucmilp-4-nyiso`
· **PRECOMMIT:** `PRECOMMIT-ucmilp4-nyiso-u4-2026-10-15.md` (pushed `e7e12823` before any shard) · **Charter:** UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) r14 · **Pin solved:** `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (uc-1.7) · **LP in this
session:** zero · **LP in any shard:** zero · **Registered:** nothing (E13).

## 0. Headline

The first leg to reach the UC stage (2021) stopped before any LP, inside the UC stage's preparation:

```
File "src/market_sim/pipeline/uc.py", line 493, in __init__  self.commit: CommitmentDemand = commitment_demand(config, demand)
File "src/market_sim/data/commitment_demand.py", line 254, in commitment_demand  raise ValueError(
ValueError: commitment increment has 5 zones, demand 7
```

PRECOMMIT §5 kill #1 (an exception inside the UC stage is an engine defect): the lane stops, routes the defect to UC-DESK and patches
nothing. **No year was solved, so U4 gets no verdict.** The NYISO `unit_commitment_milp` cell stays R (uc-1.5). The
`uc_commitment_demand_source` cell stays U, with this record cited.

## 1. The defect (zero-LP reading, `7dbfe20f`)

- **The increment.** `commitment_demand()` builds the backcast increment with `backcast_commitment_increment(iso, year,
  get_iso_config(iso))`. That call goes through `eia930.load_zone_weights`, which weights by the ISO's **load zones**. For NYISO those are
  the 5 zones `Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island`.
- **The demand.** The P1 demand matrix the increment is added to has **7** rows, because it also carries the interchange
  pseudo-zones the NYISO recipe builds (`model/interchange/spec.py::IMPORT_ZONE["NYISO"] = "NYISO_external"`, plus a seam zone).
- **The shape check.** `commitment_demand.py:251–254` compares the two row counts and raises.
- **Scope.**
  - The failure is deterministic for every NYISO year: the zones come from the recipe, not from the data year.
  - UC-1-FIX-7's repro covered only SPP 2020, which has no import pseudo-zone.
  - The same raise is expected in any UC-4 lane whose recipe builds an `IMPORT_ZONE` or seam zone: CAISO `WECC_import`, NEISO
    `HQ_import`, MISO `MISO_external`, PJM, NWPP. This was not tested here. UC-DESK was alerted at 10:12Z.
- **Fix shape, for the engine lane, not done here.** Map the increment onto the demand rows by zone name, with zero rows for zones that
  carry no BA load (external and seam zones). Rule 4 is not affected: P1 still clears on actual load.

The data side is sound. The NYISO EIA-930 day-ahead forecast exists for every year: 0 / 0 / 0 / 49 / 48 hours are dropped by the QA cut.
The PRECOMMIT §1.1 table stands: commitment demand is 0.32–0.43 GW lower on mean, and 0.30–1.04 GW lower at the 100 highest-load hours.

## 2. Gate table (control → U4)

| year | outcome | C1 / C3a / C3b / C3c / C4 / C8 | unserved | uplift | starts ÷ CEMS (CC / ST_GAS) | wall |
|---|---|---|---|---|---|---|
| 2021 | **kill #1** at UC-stage prep, about 3 min, no LP | not scored | — | — | — | — |
| 2022 | memory gate blocked (attempt 1); not relaunched after kill #1 | not scored | — | — | — | — |
| 2023 | shard archived before it reached the stage (halted after kill #1) | not scored | — | — | — | — |
| 2024 | shard archived before it reached the stage (halted after kill #1) | not scored | — | — | — | — |
| 2025 | not launched (halted after kill #1) | not scored | — | — | — | — |

The bars T1–T3 and ctl, the starts ÷ CEMS readings and U6 are all **not evaluable**. The control (keeper `2026-10-02-w0-nyiso`) is
unchanged and CALIBRATED.

## 3. Attempt log (memory gate ≥ 22.4 GiB = ceiling + swap)

| year | attempt | session | launched (Z) | gate | outcome |
|---|---|---|---|---|---|
| 2021 | 1 | `session_01B11znSju38dhBYiNah9YAu` | 09:51 | 13.36 + 9.0 = 22.4 GiB (15.7 GiB free disk), passed | `uc-params` rebuilt (108 clusters, 95 with a no-load fit, 3 class-fallback rows); `replay_keeper` accepted the `"da_forecast"` JSON; **kill #1** about 3 min after launch; nothing pushed |
| 2022 | 1 | `session_014xa7hMEctDfZrymaKTE3ec` | 09:56 | 13.36 + 4.0 = **17.4 GiB** (10.3 GiB free disk), blocked | stopped before any data step; nothing pushed |
| 2023 | 1 | `session_01NfAaPLMLQRpLFmqhn9ZDKD` | 10:02 | — | archived at 10:08 after kill #1 (container still pending) |
| 2024 | 1 | `session_01GWTNNtiCJWBZRLh1oKAa6Y` | 10:07 | — | archived at 10:08 after kill #1 (container still pending) |
| 2025 | — | — | — | — | not launched |

- **Archived:** all four shard sessions. None is left alive.
- **Branches:** no shard pushed one, so none needs cutting.
- **2022 relaunch budget:** none of the four permitted relaunches was used. Relaunching into a deterministic stage failure would only waste
  containers.

## 4. Disclosed deviations

**Shell quoting of the new `--set` value.** `scripts/shard_prompt.py` passes `--set` values through verbatim. A bare
`uc_commitment_demand_source="da_forecast"` would reach `replay_keeper` as `da_forecast`, which is not valid JSON. The emitted command
therefore carries `--set uc_commitment_demand_source='"da_forecast"'`, and the 2021 shard confirmed that `replay_keeper` accepted it. No
script was edited.

This is a small tooling gap for UC-DESK to note: `shard_prompt.py` does not shell-quote string-valued `--set`s.

## 5. What a relaunch needs (for UC-DESK)

1. An engine fix to `data/commitment_demand.py` (zone-name mapping), with a repro on an ISO that has an import pseudo-zone. This would
   be uc-1.8 or a patch release.
2. The PRECOMMIT then carries forward unchanged, with only the pin replaced. Its G-DRIFT would be extended over the fix commit, which
   should be LIVE on the gate-on path only.
3. Containers that pass the 22.4 GiB gate. One of the two that reached preflight did not.

## Log entry

- 2026-10-15 · UC-4-NYISO `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · `claude/ucmilp-4-nyiso` · PRECOMMIT `e7e12823` before any shard
  (G-DRIFT `2dd69d5a → 7dbfe20f`: UC path only, solve surface 0 moved; DA-forecast lowers NYISO commitment demand 0.3–1.0 GW at peak) ·
  **kill #1**: `commitment_demand.py:254` "commitment increment has 5 zones, demand 7" (load zones vs P1 demand with interchange
  pseudo-zones) at UC-stage prep, 2021, before any LP · 2022 memory-gate blocked (17.4 GiB) · 2023/2024 archived, 2025 not launched ·
  0 legs solved, no verdict · nothing registered · matrix: `uc_commitment_demand_source` NYISO stays U (cited), `unit_commitment_milp`
  stays R (U4 noted as pending).
