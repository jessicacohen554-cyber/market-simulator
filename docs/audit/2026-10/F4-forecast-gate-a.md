# F4 — Forecast gate-(a) board vs the 2026-10-02 keepers (2026-10-03)

Follow-up to `B-capacity-policy-forecast.md:78` and `E-model-positioning-matrix.md:116,142`,
which read the forecast program's gate-(a) board (`frontend/data/forecast/program-status.json`)
as stale against the nine 2026-10-02 keepers. Zero-LP; nothing solved, scored or registered.

## 1. Per-ISO marker table (board vs keeper file)

The board carries the keeper id in two places: the gate row's `detail` head
(`isos.<ISO>.gate.a_keeper_marker.detail`, the string `promote_keeper.py::rekey_gate_a`
rewrites, matched by its own regex `keeper (20\d\d-\d\d-\d\d-[\w.-]+)`) and the top-level
scalar `isos.<ISO>.keeper` (a records field no script writes and `forecast-status.html` does
not render — it shows `flip`, `golden`, `candidate` and the gate track only).

| ISO | `keepers/<ISO>.json` | gate row `detail` head | top-level `isos.<ISO>.keeper` (before) | `marker_complete` on board / `complete` entry | leg (a) |
|---|---|---|---|---|---|
| ERCOT | 2026-10-02-closeout-l1-coal-fuel | same — OK | 2026-09-30-r-19-eia-923 — STALE | false / none | fail |
| CAISO | 2026-10-02-closeout-caiso-w1-arm2 | same — OK | 2026-09-25-caiso-r2-cc-gross — STALE | **true / none (withdrawn)** | fail |
| PJM | 2026-10-02-w0-pjm-fix2 | same — OK | 2026-09-24-pjm-h22-rggi-span — STALE | true / 2026-10-02-w0-pjm-fix2 | pass |
| MISO | 2026-10-02-w0-miso-fix2 | same — OK | 2026-09-28-miso-280-splitremap — STALE | false / none | fail |
| NYISO | 2026-10-02-w0-nyiso | same — OK | 2026-09-22-nyiso-hydro3-ror-split — STALE | false / none | fail |
| NEISO | 2026-10-02-w0-neiso | same — OK | 2026-09-26-neiso-119-anchor-fuelsec — STALE | true / 2026-10-02-w0-neiso | pass |
| SPP | 2026-10-02-w0-spp107r | same — OK | 2026-09-26-spp-85-netload-mask — STALE | **true / none (withdrawn)** | fail |
| NWPP | 2026-10-02-w0-nwpp-fix2 | no board row | no board row | — / none | — |
| SOCO | 2026-10-02-w0-soco-fix2 | no board row | no board row | — / none | — |

Reading: the gate rows themselves are **current** — every promotion on 2026-10-02 (and SPP on
2026-10-03) ran `rekey_gate_a`, and each row's `detail` opens with the matching
`RE-KEYED … by promote_keeper.py (identity only)` prefix. The audit's "stale" reading came
from the top-level `isos.<ISO>.keeper` scalar (7/7 stale, last re-keyed by the r#66 lane on
2026-09-25, see `gate_a_provenance.derived_by`) and from the file's `generated: 2026-09-06`
stamp, neither of which `rekey_gate_a` writes.

## 2. What `rekey_gate_a` does and what was changed

`scripts/promote_keeper.py:717` `rekey_gate_a(iso, run_id, dry)` is a pure JSON re-key (no
LP): it loads the board, finds `isos.<ISO>.gate.a_keeper_marker`, regex-extracts the first
`keeper <id>` in `detail`, returns silently if it already equals `run_id`, otherwise
substitutes the id and prepends the `RE-KEYED <date> …` prefix, then writes
`json.dumps(doc, indent=2, ensure_ascii=False) + "\n"`. It honours `dry` (the promoter's
`--dry-run`) but has **no standalone CLI path** — `main()` only reaches it as step 6b of the
full promotion chain after register/attest/designate/fold.

Dry-mode call of the function itself (imported with `pyarrow`/`pandas`/`numpy` stubbed, since
`uv sync` was out of scope) for all nine ISOs with each ISO's live keeper id:

```
rekey_gate_a(ERCOT|CAISO|PJM|MISO|NYISO|NEISO|SPP, <keeper>, dry=True)  -> returns, prints nothing (old == run_id)
rekey_gate_a(NWPP, 2026-10-02-w0-nwpp-fix2, dry=True) -> "NWPP: no gate.a_keeper_marker row on the forecast board — skipped"
rekey_gate_a(SOCO, 2026-10-02-w0-soco-fix2, dry=True) -> "SOCO: no gate.a_keeper_marker row on the forecast board — skipped"
rekey_complete(<ISO>, …, dry=True) -> PJM, NEISO: no-op (already current); every other ISO "holds no `complete` entry — nothing to re-key"
```

So the change `rekey_gate_a` would write is empty; nothing was applied through it.

**Applied by hand (the one mechanical edit):** the seven stale top-level `isos.<ISO>.keeper`
scalars were re-keyed to the live ids, by `json.load` → assign → `json.dumps(indent=2,
ensure_ascii=False)` (verified byte-stable round trip before writing, so the diff is exactly
7 insertions / 7 deletions in `frontend/data/forecast/program-status.json`; key order and
indent preserved). This repeats what the r#66 re-key lane did on 2026-09-25 ("the four
top-level isos.<ISO>.keeper fields re-keyed to the live ids"). No other field was touched:
not `generated`, not `marker_complete`, not `gate_a_provenance`, no NWPP/SOCO rows.

`program-status.js` is generated at Pages deploy from the committed `program-status.json`
(`scripts/register_forecast_run.py:20-40`, `deploy-pages.yml:81-85`; gitignored) — no
generated output is committed.

## 3. Parity check

`python3 scripts/check_forecast_parity.py` (reads `keepers/<ISO>.json` → registry sidecar →
bundle `run_config.json`; it does not read the board), run before and after the edit:

```
SUMMARY: 9 keeper posture(s); 0 unaccounted, 26 filed gap(s), 0 registry failure(s), 0 error(s)
exit=0
```

(CI runs it non-blocking, `ci.yml:226`. The 26 filed gaps are the pre-existing registered
`GAP` rows, e.g. `coal_fuel_inventory_*` on NWPP; unchanged by this lane.)

## 4. `calibration-complete.json` under rule 22

`complete` block: NEISO → `2026-10-02-w0-neiso`, PJM → `2026-10-02-w0-pjm-fix2` — both equal
the live keeper (re-keyed by `rekey_complete` at promotion). No stale keeper. `withdrawn`:
NYISO (null), ERCOT `2026-10-01-r-23-swcap-hourly`, CAISO `2026-09-30-caiso-r20-overnight`,
SPP `2026-09-28-spp-100-chp-scope` (historical ids of the withdrawal, not keeper claims).
`final` is deliberately empty. Not edited.

## 5. Remaining owner / lane decisions (not mechanical, not done here)

1. **`marker_complete: true` for CAISO and SPP** (top-level and `gate.marker_complete`)
   contradicts `calibration-complete.json`, which lists only NEISO and PJM. The leg verdict is
   already `fail` for both and SPP's detail says "FAIL ON THE WITHDRAWN MARKER", so the gate
   reading is right and only the scalar is stale; flipping it is a board-content edit a
   forecast-desk records lane should carry with its own provenance block.
2. **NWPP and SOCO have no board row** although both carry a 2026-10-02 keeper; `iso_order`
   lists seven ISOs. Adding rows requires a leg-(a) reading (both: full-span keeper present,
   no `complete` entry → fail on the literal §2.1b(2)(a) test) and is the forecast director's
   charter.
3. `generated: 2026-09-06` and `gate_a_provenance.derived_at_sha c64e69eb (2026-09-25)` are
   not refreshed; every later re-key lives only in the per-row `RE-KEYED` prefixes. Whether to
   stamp a new derivation block (the r#65/r#66 pattern) is a lane decision.
4. `rekey_gate_a` leaves `isos.<ISO>.keeper` untouched by design; if that scalar is meant to
   track the keeper, a one-line addition to the function (owner-approved, rule 27 file) would
   stop it drifting again.
5. `B-capacity-policy-forecast.md:78` / `E-model-positioning-matrix.md:116,142` should be
   read as "the board's records scalar and `generated` stamp were stale; the gate rows were
   not" — the audit prose was not edited by this lane.
