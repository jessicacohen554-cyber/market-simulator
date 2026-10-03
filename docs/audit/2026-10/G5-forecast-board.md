# G5 — Forecast program board: NWPP + SOCO rows, CAISO/SPP marker reconciliation (2026-10-03)

Owner ruling 2026-10-03, executing `F4-forecast-gate-a.md` §5.1–5.2. Zero-LP; nothing solved,
scored or registered. One file edited: `frontend/data/forecast/program-status.json` (frontend/data/forecast/program-status.json | 128 +++++++++++++++++++++++++++--
 1 file changed, 123 insertions(+), 5 deletions(-)).
Branch `claude/audit-rulings-2026-10`; nothing committed by this lane.

## 1. Before / after

| ISO | field | before | after |
|---|---|---|---|
| NWPP | board row | none; absent from `iso_order` | row added (keeper `2026-10-02-w0-nwpp-fix2` read from `keepers/NWPP.json`); leg (a) **fail** on the absent marker (no `complete`, no `withdrawn` entry; determination NOT-YET per `status/NWPP.js`, read not scored); (b)/(c) fail by absence, `c_readiness`/`c_cost`/`d_owner_auth` none; `open` false, `closed_on` [a,b,c,d]; `tier_reached` "none -- NOT RUN"; `t1f`/`t1h` NOT RUN, `t1x` n/a; no `fc` map (no FC result fabricated); `marker_complete`/`marker_final` false; appended to `iso_order` |
| SOCO | board row | none; absent from `iso_order` | same shape, keeper `2026-10-02-w0-soco-fix2`; leg (a) detail additionally states the no-LMP posture (C3a/b/c unscorable by design) |
| CAISO | `isos.CAISO.marker_complete` | `true` (while `calibration-complete.json` holds `withdrawn.CAISO`, withdrawn 2026-09-30, and `gate.a_keeper_marker.status` = fail, `gate.marker_complete` = false) | `false` + `marker_complete_note` (withdrawal date, keeper at withdrawal `2026-09-30-caiso-r18-dswgas`, reconciliation 2026-10-03) |
| SPP | `isos.SPP.marker_complete` | `true` (withdrawn 2026-09-30; gate leg fail; `gate.marker_complete` false) | `false` + `marker_complete_note` (keeper at withdrawal `2026-09-28-spp-100-chp-scope`) |
| top level | `g5_forecast_board` | absent | records-only provenance block (y31/nyiso193 form; no forecast-provenance/v1 field names) |

Authoritative field: membership of `calibration-complete.json` `complete` block. `promote_keeper.py::rekey_complete`
(l.695) writes only there, `rekey_gate_a` (l.717) writes only the gate row's `detail`; the top-level
`marker_complete` scalar is hand-kept and had drifted (the soco-96 withdrawal flipped `gate.marker_complete`
and the leg status but not the scalar). Marker vocabulary used for NWPP/SOCO: "absent / never declared"
(neither ISO has a `withdrawn` entry, so "withdrawn" would be false).

Not changed: `generated` (still 2026-09-06 — the 2026-10-03 scalar re-key `8f0fc697` and every promotion
re-key left it alone; convention is per-block `derived_at_date` stamps), `gate_a_provenance`, every other
ISO row, all prose, all verdicts. `calibration-complete.json` not edited (nothing required it).
`docs/forecast-development-plan-2026-07.md` carries no per-ISO status table — not edited.

Byte discipline: `json.load` → edit → `json.dumps(indent=2, ensure_ascii=False) + "\n"`; round-trip
verified byte-stable before writing, so the diff is exactly the rows above.

## 2. Checks

```
python3 scripts/check_forecast_parity.py
SUMMARY: 9 keeper posture(s); 0 unaccounted, 26 filed gap(s), 0 registry failure(s), 0 error(s)   exit 0
```
(Parity reads keepers → registry → bundle `run_config.json`, not the board; unchanged before/after, as F4 §3.)

`python3 scripts/register_forecast_run.py --reindex` (stdlib, no network, no solve) regenerated
`frontend/data/forecast/program-status.js` (now carries NWPP and SOCO) + `manifest.js`, `registry/`, `runs/`.
All four are gitignored (`.gitignore:271`; the Pages deploy is their single writer) — not committed.
`forecast-status.html` renders `iso_order`, so both cards appear after SPP; `fcChips` renders nothing for a
row without `fc`.

## 3. Idempotent snippet (re-run on the merged file)

origin/main moved past this branch (the board changed there and NWPP's keeper bundle moved to
`nwppnext22b_span`). The edit is therefore carried as a snippet that reads every keeper id at run time
from `keepers/<ISO>.json`, adds a row only if absent (re-keys the keeper scalar and the gate `detail` head
otherwise, with the same regex `rekey_gate_a` uses), flips `marker_complete` only where the `complete`
entry is absent AND a `withdrawn` entry exists, and is a no-op once applied (`--check` reports).
Run from the repo root after the merge: `python3 g5_forecast_board.py --check` then without `--check`.

```python
#!/usr/bin/env python3
"""G5 (2026-10-03): add NWPP + SOCO rows to the forecast board and reconcile
marker_complete against calibration-complete.json. Idempotent; zero-LP; stdlib only.
Keeper ids are read at run time from frontend/data/backcast/keepers/<ISO>.json.
Run from the repo root: python3 g5_forecast_board.py [--check]"""
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[0]
while not (REPO / "frontend/data/forecast/program-status.json").exists():
    if REPO.parent == REPO:
        REPO = Path.cwd(); break
    REPO = REPO.parent
BOARD = REPO / "frontend/data/forecast/program-status.json"
COMPLETE = REPO / "frontend/data/backcast/calibration-complete.json"
KEEPERS = REPO / "frontend/data/backcast/keepers"
STATUS = REPO / "frontend/data/backcast/status"
DATE = "2026-10-03"
NEW_ISOS = ["NWPP", "SOCO"]
KEEPER_RX = re.compile(r"keeper (20\d\d-\d\d-\d\d-[\w.-]+)")  # promote_keeper.rekey_gate_a's own regex


def keeper_id(iso):
    return json.loads((KEEPERS / f"{iso}.json").read_text())["keeper"]


def status_read(iso):
    """Determination + registered years from the committed status sidecar (never re-scored)."""
    try:
        t = (STATUS / f"{iso}.js").read_text()
        det = re.search(r'"determination"\s*:\s*"([^"]+)"', t)
        yrs = re.search(r'"years"\s*:\s*(\[[^\]]*\])', t)
        return (det.group(1) if det else "unread"), (json.loads(yrs.group(1)) if yrs else [])
    except FileNotFoundError:
        return "unread", []


def gate_a_detail(iso, kid, det, years):
    extra = (" SOCO publishes no LMP (single BA, no LMP market); C3a/C3b/C3c are unscorable by "
             "design, so a price criterion can never close this leg." if iso == "SOCO" else "")
    return (
        f"keeper {kid} (registry years {years}, full span, rule 16 [R-ALLYEARS]; "
        f"frontend/data/backcast/keepers/{iso}.json); ISO determination {det} under rubric v3.13, "
        f"read from the committed status sidecar frontend/data/backcast/status/{iso}.js (not re-scored); "
        f"marker complete=False final=False. FAIL ON THE ABSENT MARKER: gate (a) needs the designated "
        f"full-span keeper AND a `complete` entry; calibration-complete.json carries no `complete` and no "
        f"`withdrawn` entry for {iso} (never declared; rule 22 [R-C3C]: `calibration-complete.json` survives "
        f"only as the keeper designation and the forecast program's gate-(a) input, and the standing Q5 rule - "
        f"a marker cannot stand on a NOT-YET keeper - applies). Row added {DATE} by audit lane G5 "
        f"(owner ruling {DATE}: add NWPP and SOCO to the board) on the 2026-10-02 keeper." + extra
    )


def new_row(iso):
    kid = keeper_id(iso)
    det, years = status_read(iso)
    absent = (f"NO T1-F, T1-X, T1-H OR T0 OF ANY KIND EXISTS FOR {iso}: ff-verdicts.json carries no "
              f"{iso.lower()}-* key and frontend/data/hindcast/ holds no {iso} sidecar. The leg is closed by "
              f"the absence of the instrument, not by a measured HOLD; nothing here says {iso} would fail a "
              f"battery it has never been given.")
    return {
        "tier_reached": f"none -- NOT RUN (no forecast tier, T0 included, has ever been solved for {iso})",
        "t1f_determination": "NOT RUN",
        "t1x_determination": "n/a",
        "t1h_determination": "NOT RUN",
        "flip": (f"no flip arm measured. {iso} has no forecast or hindcast bundle of any tier, so no A/B posture "
                 f"has ever been established for it; this board's `flip_config` line says nothing about {iso}."),
        "blocking_rows": [
            f"NO FORECAST TIER HAS BEEN RUN FOR {iso} (T0 / T1-F / T1-X / T1-H / T2 / T3 all absent as of {DATE}); "
            f"every FC-1..FC-8 cell is unmeasured. The row exists so the board stops being silent about an ISO "
            f"that carries a 2026-10-02 full-span keeper ({kid}); it asserts no forecast result."
        ],
        "gate": {
            "a_keeper_marker": {
                "status": "fail",
                "detail": gate_a_detail(iso, kid, det, years),
                "read_live_at": (f"audit lane G5 {DATE}, zero-LP: keepers/{iso}.json + calibration-complete.json "
                                 f"(both blocks) + status/{iso}.js read from the checkout; nothing solved or re-scored"),
                "corrected_by": f"audit lane G5 ({DATE}): row created; no prior row existed (F4-forecast-gate-a.md s5.2).",
            },
            "b_t1f_verdict": {"status": "fail", "detail": absent},
            "c_crossover_gap": {"status": "fail",
                                "detail": f"NO T1-X CROSSOVER MEASUREMENT EXISTS FOR {iso}; FC-4 has never been measured."},
            "c_readiness": {"status": "none",
                            "detail": f"FF-3E readiness battery never run for {iso}; project_full_horizon reads the "
                                      f"GOLDEN_ISOS anchors only and {iso} is not a member."},
            "c_cost": {"status": "none", "detail": f"no forecast-family invocation exists for {iso}; no wall/RSS anchor."},
            "d_owner_auth": {"status": "none",
                             "detail": (f"no authorization exists. The {DATE} owner ruling authorized THE BOARD ROW and "
                                        f"nothing else -- not a s2.1b(2)(d) full-solve authorization.")},
            "open": False,
            "closed_on": ["a", "b", "c", "d"],
            "note": (f"[G5, {DATE}] Row created on the owner ruling of {DATE}. ALL FOUR legs are closed: (a) on the "
                     f"never-declared `complete` marker ({det} keeper determination concurring), (b) and (c) on the total "
                     f"absence of any forecast or hindcast measurement, (d) on the absence of any authorization. "
                     f"Like SPP's row at its creation, (b)/(c) are closed by absence rather than by a measured shortfall."),
            "marker_complete": False,
        },
        "golden": "deferred (s2.1b); not a GOLDEN_ISOS member.",
        "candidate": None,
        "keeper": kid,
        "marker_complete": False,
        "marker_final": False,
        "note": (f"[G5, {DATE}] Board row added by owner ruling; no forecast tier has been run for {iso}. "
                 f"Keeper {kid} per keepers/{iso}.json; determination {det} per status/{iso}.js."),
    }


def rekey_existing(row, iso, kid):
    """Re-run on a merged file: keep the keeper scalar and the detail head on the live keeper (identity only)."""
    changed = False
    if row.get("keeper") != kid:
        row["keeper"] = kid; changed = True
    a = row.get("gate", {}).get("a_keeper_marker", {})
    m = KEEPER_RX.search(a.get("detail", ""))
    if m and m.group(1) != kid:
        a["detail"] = (f"RE-KEYED {DATE} by G5 snippet (identity only): {m.group(1)} -> {kid}; leg verdict unchanged. "
                       + KEEPER_RX.sub(f"keeper {kid}", a["detail"], count=1)); changed = True
    return changed


def main():
    check = "--check" in sys.argv
    raw = BOARD.read_text(); doc = json.loads(raw)
    assert json.dumps(doc, indent=2, ensure_ascii=False) + "\n" == raw, "board is not round-trip stable; stop"
    cc = json.loads(COMPLETE.read_text())
    complete, withdrawn = cc.get("complete") or {}, cc.get("withdrawn") or {}
    log = []
    isos = doc["isos"]
    for iso in NEW_ISOS:
        assert iso not in complete and iso not in withdrawn, f"{iso} now has a marker entry; re-read before adding"
        kid = keeper_id(iso)
        if iso not in isos:
            isos[iso] = new_row(iso); log.append(f"{iso}: row added (keeper {kid})")
        elif rekey_existing(isos[iso], iso, kid):
            log.append(f"{iso}: existing row re-keyed to {kid}")
        if iso not in doc.get("iso_order", []):
            doc.setdefault("iso_order", []).append(iso); log.append(f"{iso}: appended to iso_order")
    # marker_complete reconciliation: calibration-complete.json `complete` membership is authoritative
    # (rekey_complete/rekey_gate_a only ever write there and the gate detail; the scalar is hand-kept).
    for iso, row in isos.items():
        if iso in complete or iso not in withdrawn:
            continue
        w = withdrawn[iso]; wd = w.get("withdrawn", "?")
        note = (f"RECONCILED {DATE} by audit lane G5 (F4-forecast-gate-a.md s5.1): marker_complete true -> false; "
                f"calibration-complete.json holds no complete.{iso} entry (withdrawn {wd}, keeper at withdrawal "
                f"{w.get('keeper_at_withdrawal', '?')}); the gate-(a) leg already read fail on the withdrawn marker.")
        if row.get("marker_complete") is True:
            row["marker_complete"] = False; row["marker_complete_note"] = note
            log.append(f"{iso}: marker_complete true -> false (withdrawn {wd})")
        g = row.get("gate", {})
        if g.get("marker_complete") is True:
            g["marker_complete"] = False; log.append(f"{iso}: gate.marker_complete true -> false")
    if "g5_forecast_board" not in doc:
        doc["g5_forecast_board"] = {
            "note": ("RECORDS-ONLY BOARD EDIT EXECUTING ONE OWNER RULING -- NOT A SCORING STAMP. No LP, no forecast "
                     "or backcast run solved or re-scored, nothing registered. Like `y31_nyiso_q5_withdrawal`, this "
                     "block deliberately avoids the forecast-provenance/v1 field names so "
                     "scripts/check_forecast_staleness.py can never read it as evidence of a re-score."),
            "lane": "G5 forecast board (Model Audit program 2026-10), owner ruling of 2026-10-03",
            "derived_at_date": DATE,
            "derived_from": ("docs/audit/2026-10/F4-forecast-gate-a.md s1/s5; frontend/data/backcast/keepers/{NWPP,SOCO}.json "
                             "(keeper ids read at run time); frontend/data/backcast/calibration-complete.json (complete + "
                             "withdrawn blocks); frontend/data/backcast/status/{NWPP,SOCO}.js (determination, read not scored); "
                             "docs/audit/2026-10/G5-forecast-board.md (the idempotent snippet)."),
            "what_changed": ("NWPP + SOCO rows added to `isos` and `iso_order` (leg (a) fail on the absent marker, legs (b)-(d) "
                             "closed by absence, no FC result asserted); CAISO + SPP top-level `marker_complete` true -> false "
                             "with a `marker_complete_note` (and SPP/CAISO `gate.marker_complete` already false); this block."),
            "what_did_NOT_change": ("`generated` (left at 2026-09-06: the 2026-10-03 scalar re-key 8f0fc697 did not refresh it "
                                    "either), `gate_a_provenance`, every other ISO row, headline / gate_reading / readiness prose, "
                                    "tier_ladder, every verdict and its provenance."),
        }
        log.append("g5_forecast_board provenance block added")
    out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if check:
        print("CHECK:", "no change needed" if out == raw else "would change:\n  " + "\n  ".join(log)); return
    if out != raw:
        BOARD.write_text(out)
    print("\n".join(log) or "no change (already applied)")


if __name__ == "__main__":
    main()
```

## 4. What remains (owner / lane)

1. Re-run the snippet on the merged `program-status.json` (section 3); if NWPP's keeper id changed with
   `nwppnext22b_span`, the row re-keys itself from `keepers/NWPP.json`.
2. `isos.<ISO>.keeper` is still hand-kept: F4 §5.4's one-line addition to `rekey_gate_a` (rule 27 file,
   owner-approved) would stop the scalar drifting; same for the `marker_complete` scalar.
3. SPP `gate.closed_on` reads [b,c,d] although leg (a) is fail (soco-96 flipped status/detail but not
   `closed_on`); CAISO reads [a,b,c] correctly. Not touched here (outside the ruling's scope).
4. The forecast director's charter decides whether NWPP/SOCO ever get a T0/T1 tier; nothing here schedules one.
