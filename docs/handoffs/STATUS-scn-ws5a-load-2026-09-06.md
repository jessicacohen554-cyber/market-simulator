# STATUS — SCN-WS5A-LOAD (live campaign state)

Standing answer to the recurring check-in questions, so they do not have to be
re-derived from scrollback. Updated as ISOs land.

## Is this a keeper candidate? Should it be promoted?

**No — and this is a category fact, not a judgement on the results.**

"Keeper" is a **backcast calibration** concept: CLAUDE.md rule 1 `[R-STRUCT]`, rule 15
`[R-DASHBOARD]`, the C1–C8 determination rubric, `frontend/data/backcast/keepers/<ISO>.json`.

This lane is a **forecast scenario campaign**: `ScenarioConfig.mode="forecast"`, T1-F
2026–2030, registered with `--kind scenario` into the **forecast** namespace under campaign
`scn-campaign-load-2026-09-06` (forecast plan §7.5). It therefore has:

- no C1–C8 gates, so no "structural integrity improved but gates regressed" trade to weigh;
- no keeper shard, no determination, nothing that *can* be promoted;
- an explicit charter prohibition on touching `frontend/data/*` beyond its own registration
  sidecars, `program-status.json`, `ff-verdicts.json`, or any other ISO's files.

Promoting anything from here would be a governance breach, not a close call.

## Is there backcast calibration work blocked on a merge?

**No.** This session runs no backcast calibration, is not blocked, and has no unpushed or
untracked state.

**Checked at HEAD (`scripts/calibration_verdict.py`, committed artifacts only, no solve):
all six ISOs' designated keepers score `CALIBRATED`.**

| ISO | keeper | determination |
|---|---|---|
| ERCOT | `2026-09-05-ercot248-two-config-keeper` | CALIBRATED |
| CAISO | `2026-09-05-caiso-252-b1-notrim` | CALIBRATED |
| PJM | `2026-08-15-pjm-162-inputclock` | CALIBRATED |
| MISO | `2026-09-05-miso-220-nonsteam-lift` | CALIBRATED |
| NYISO | `2026-09-06-nyiso-196-extract-basis` | CALIBRATED |
| NEISO | `2026-08-17-neiso-99-joint-p1` | CALIBRATED |

So **there is no rubric-failure keeper to tune.** CAISO's only `FAIL` is **C5a CO2 vs eGRID**
(−11.5 %, 2023), which rubric v2.9 demoted to **REPORTED-ONLY** — it carries no status, no
caveat budget and no reason line. Every other ISO's sole blemish is the ledgered **C3c**,
non-downgrading since rubric v3.3.

**What IS open is governance, not tuning.** `calibration-complete.json` reads
`complete = {ERCOT, NEISO, PJM}`, `withdrawn = {CAISO, NYISO}`, MISO never granted, and
`final` is empty with the locked-test tier frozen. Three ISOs hold CALIBRATED keepers while
sitting outside `complete`, which blocks their 2020–2022 validation ladder — and only an
explicit owner declaration clears that. No session can tune its way in.

The handoff prompt for the highest-value remaining calibration work — the **rule-22 touchpoint
loop** on the three ISOs that *are* authorized — was delivered in-session; its shape is
`BC-TOUCHPOINT-2022-<ISO>`, one ISO per invocation, `<ISO> ∈ {ERCOT, NEISO, PJM}`.

## Campaign state

- **Frozen pin** `1cc45bb2`; every leg verified a descendant with **zero** solve-path diff
  and `git.dirty=False` (PRECOMMIT ADDENDUM §5).
- **16 legs** planned: ERCOT/CAISO/MISO/NYISO 3 each, PJM/NEISO 2 each (phase 0 measured the
  DC axis degenerate in PJM and NEISO).
- **Complete:** ERCOT, NEISO, NYISO — solved, registered, delta-reported, FINDING written.
- **Running / queued:** PJM, then MISO, then CAISO (each alone, rule 12).
- Backcast byte-identity untouched; DOF ledger carries **zero** free parameters.
