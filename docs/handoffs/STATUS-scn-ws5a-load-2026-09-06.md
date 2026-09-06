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

---

## Routed defect — `collate_scenario_campaign.py` differences sums over DIFFERENT ISO sets

Found while pre-flighting the sanctioned collation tool against the three completed ISOs,
**before** it reached this lane's synthesis. Not fixed here: `scripts/collate_scenario_campaign.py`
is SCN-WS0's file and this lane's charter says consume, never modify.

**The defect.** The `six-ISO modeled system` scope in `campaign_delta_table.csv` computes
`emissions_mt_delta` as *(sum over the case's ISOs)* − *(sum over the reference case's ISOs)*,
without restricting both to a common set. When a case has incomplete ISO coverage the two sums
span different systems and the delta is meaningless.

**Measured, on the three ISOs complete at the time:**

| system-scope `LOAD-HI-ORGANIC`, 2030 | Mt |
|---|---|
| reported `emissions_mt_delta` | **+5.4620** |
| correct delta on the common {ERCOT, NYISO} set | **+18.8300** |
| error | **−13.368**, exactly NEISO's REF 2030 level |

`LOAD-HI-ORGANIC` summed 2 ISOs (ERCOT, NYISO — NEISO has no ORGANIC leg because phase 0
measured its DC axis degenerate) while `REF` summed 3. The understatement is **71 %**.

**This is structural, not a partial-results transient.** At full completion `REF` and `LOAD-HI`
will cover **6** ISOs while `LOAD-HI-ORGANIC` covers **4** — PJM and NEISO ship
`LOAD-HI == LOAD-HI-ORGANIC` byte-for-byte, so their ORGANIC arm is correctly never solved
(SCN-WS4b §3, reproduced by this lane's phase 0). So any campaign with a legitimately
degenerate arm hits this.

**Mitigations.** The tool *does* emit `isos` and `isos_missing` per case, so the coverage is
disclosed and the defect is detectable — it is a wrong number beside honest metadata, not a
silent one. This lane's synthesis will compute every cross-ISO delta on the **common ISO set**
and will not quote the system-scope ORGANIC row.

**Suggested repair (for whoever owns the file):** restrict both operands to
`isos(case) ∩ isos(reference_case)` before summing, and label the row with that intersection;
or emit the row as `null` with the coverage mismatch named, rather than a computable-looking
number. Either is preferable to a delta a reader cannot tell is malformed.
