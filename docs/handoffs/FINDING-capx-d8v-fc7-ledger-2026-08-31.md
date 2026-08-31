# FINDING — capx-D8-V: FC-7 ledger completion — the two routed flips published, PJM and MISO ledgered

**Lane:** capx-D8-V (director r#22 dispatch; charter:
`docs/handoffs/capx-director-prompt-pack-2026-08.md` §D8-V — executes capx-D8-RE's
routed set) · **Branch:** `claude/capx-d8v-fc7-ledger-gf4h5g` · **Date:** 2026-08-31
· **Base:** `origin/main` @ `836e48e1` · **Zero solves.**

## §0 Headline

All four routed items are closed; every number below is
`scripts/forecast_verdict.py`'s own output on committed artifacts:

1. **The two STOPPED flips are RE-VERIFIED AND PUBLISHED** through each affected
   lane's own record (the 2026-08-30 cross-lane re-grade ruling, discharged):
   **`neiso-t1f` and `nyiso-t1f` each move PROMOTE-WITH-CAVEATS → PROMOTE with
   caveats `[]`** — the program's first two clean FC maps, exactly the D8 §6
   pre-registration and D8-RE's §8.2 stopped measurement. Nothing else moved in
   either key (asserted row-by-row).
2. **PJM's ledger is BUILT, COMMITTED and consumed**
   (`results/ff-t1f-s6-pjm/ledger/dof_ledger.json`, 1 entry, 0 UNIDENTIFIED):
   `pjm-t1f` FC-7 CAVEAT → PASS with **determination UNCHANGED** (HOLD, held by
   the FC-1/FC-2 FAILs) — matching D8-RE's §8.4 read-only measurement; not a stop.
   D8 §5.1's "FC-7 rows with no committed backing" records gap is closed for PJM.
3. **MISO's ledger is BUILT, COMMITTED and consumed**
   (`results/ff-t1f-s123/verify/dof_ledger.json`, 4 entries, **3 UNIDENTIFIED**):
   FC-7 **stays CAVEAT** and no verdict moves — the scorer treats an
   unattested-carrying ledger exactly as an absent one. The value is the **named
   attestation debt** (§5), which is the instrument working as designed.
4. **The controls came first, on all four keys, and all four are byte-exact**
   (§1) — so the ledger input is provably the only delta in every movement here.

Not touched, per charter and director ruling §0s.5: the seven legacy legs'
reconstructed run_configs and their FC-7 rows (lane D20's), `neiso-t3`, every
crossover/t1x key, the ERCOT board block (lane D4-M's), and every bundle with no
committed run_config (ercot/caiso-t1f, the S-4V pair, all `-ff2d`/`-ffr3a2`
vintages — D8-RE's correctly-skipped set stays skipped).

## §1 The controls (all four keys, before anything else)

Each key was re-scored on its committed artifacts **WITHOUT** `--dof-ledger`
(D8-RE's §8.1 protocol re-run in full, never inherited) and compared against its
committed record on **every scorer-derived field**: categories row-by-row
(status, detail, gating), determination, reasons, caveats, tier / iso / schema /
rubric_version, and `provenance.cache_epoch`.

| key | bundle | compared against | result |
|---|---|---|---|
| `neiso-t1f` | `results/ff-t1f-s4b-ara/neiso` | ff-verdicts key AND committed bundle sidecar | **byte-exact** |
| `nyiso-t1f` | `results/ff-t1f-extcap/nyiso` | ff-verdicts key (bundle carried no sidecar) | **byte-exact** |
| `pjm-t1f` | `results/ff-t1f-s6-pjm/ledger` | ff-verdicts key AND committed bundle sidecar | **byte-exact** |
| `miso-t1f` | `results/ff-t1f-s123/verify` | ff-verdicts key (bundle carried no sidecar) | **byte-exact** |

Sole non-scorer divergence, expected and preserved: `miso-t1f`'s board key
carries one **lane-authored** S-123-V note (the §6-measured I7-closure note)
that the scorer never emits — a board-side annotation, kept verbatim through the
publish. No scorer drift, no artifact drift; the movement below is the ledger
input alone. The stop-the-line clause was never triggered.

## §2 NEISO — the routed flip, re-verified and PUBLISHED (Task 1)

Affected lane **capx-S4b-neiso-ara**; its own record is the Addendum appended to
`docs/handoffs/FINDING-capx-s4b-neiso-ara-2026-08-30.md` (the cross-lane rule's
requirement). The documented command, on committed artifacts only:

```
python scripts/forecast_verdict.py --tier t1f \
  --summary results/ff-t1f-s4b-ara/neiso/full_horizon_summary.json \
  --run-config results/ff-t1f-s4b-ara/neiso/run_config.json \
  --dof-ledger results/ff-t1f-s4b-ara/neiso/dof_ledger.json \
  --json-out results/ff-t1f-s4b-ara/neiso/forecast_verdict.json
```

**Movement, asserted row-by-row against the committed record — exactly the
pre-registration and NOTHING else:**

- FC-7 `dof ledger` row CAVEAT → PASS ("7 entries well-formed (0 open residual
  DOF listed)"); FC-7 category CAVEAT → PASS;
- caveat `FC-7 provenance & DOF` retired;
- **DETERMINATION PROMOTE-WITH-CAVEATS → PROMOTE, caveats `[]`** — NEISO's
  first clean FC map (FC-1 / FC-2 / FC-7 / FC-8 all PASS);
- every other category, row status and row detail **byte-identical** (the
  publish-only-if condition, checked programmatically before writing).

Published: `ff-verdicts.json[neiso-t1f]` (prior stamp `88baa9d5c71b @
2026-08-30T22:25:51Z` preserved in the session string), the bundle sidecar, and
the NEISO board rows (§6). This also **closes the S-4b treatment/control FC-7
split** D8-RE flagged: both arms again read identical FC-7 rows.

## §3 NYISO — the routed flip, re-verified and PUBLISHED (Task 2)

Affected lane **capx-D2-extcap-intake**; its record is the Addendum appended to
`docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md`. Identical shape on
`results/ff-t1f-extcap/nyiso/` (ledger: 1 entry, 0 UNIDENTIFIED —
`forecast_xyear_warmstart=False`, owner decision D-10):

- FC-7 `dof ledger` row CAVEAT → PASS ("1 entries well-formed (0 open residual
  DOF listed)"); FC-7 category CAVEAT → PASS; caveat retired;
- **DETERMINATION PROMOTE-WITH-CAVEATS → PROMOTE, caveats `[]`** — NYISO's
  first clean FC map;
- nothing else moved (same programmatic row-by-row assertion).

Published: `ff-verdicts.json[nyiso-t1f]` (prior stamp `ea4e4faf65de @
2026-08-25T01:49:23Z` preserved), a bundle verdict sidecar written (the bundle
previously carried none), and the NYISO board rows (§6). The D2 finding §7's
"single remaining caveat" sentence is discharged in its Addendum.

## §4 PJM — ledger built, committed, consumed (Task 3)

`python scripts/build_forecast_dof_ledger.py results/ff-t1f-s6-pjm/ledger` over
the committed `run_config.json` (run `pjm-2026-2030-s6-ledger`, sha `54ca19a`,
cache `31a19d815fa319a7`). **Contents — 1 entry, 0 UNIDENTIFIED**, matching
D8-RE's §8.4 read-only measurement:

| entry | value | identification | source |
|---|---|---|---|
| `forecast_xyear_warmstart` | False | design-decision | Owner D-10 (2026-08-04, ffr-owner-sitting Addendum K.3); registry carrier `FORECAST_BUNDLE_XYEAR_WARMSTART` via `forecast_posture.py`; measurement ffr-3t |

Epoch drift (reported, never scored): `storage_entry_availability_gate` and
`storage_entry_cost_normalized_rank` equal the shipped default at the run's own
sha — the HEAD default moved after the solve (the D12-A/R-A arming), not free
parameters of this run. `registry_identification.backcast_keeper_at_build`:
`2026-08-15-pjm-162-inputclock`.

**Re-score:** FC-7 `dof ledger` CAVEAT → PASS, FC-7 category CAVEAT → PASS,
caveat `FC-7 provenance & DOF` retired (caveats now the FC-8 runtime caveat
alone); **DETERMINATION UNCHANGED — HOLD**, held by `FC-1 structural integrity
FAIL` + `FC-2 adequacy & equilibrium behavior FAIL`, byte-identical reasons.
Exactly D8-RE's measurement ⇒ **not a stop**; the flip clause never fired.
Published: `ff-verdicts.json[pjm-t1f]` (prior stamp `54ca19ae0782 @
2026-08-31T00:43:56Z` preserved), the bundle sidecar, `isos.PJM.fc.FC-7` (§6).

## §5 MISO — ledger built, committed, consumed; the attestation debt NAMED (Task 4)

`python scripts/build_forecast_dof_ledger.py results/ff-t1f-s123/verify` over
the committed `run_config.json` (run `miso-2026-2030-s123-verify`, sha
`54ca19a`, cache `587dc5b32ba71ceb`). **Contents — 4 entries, 3 UNIDENTIFIED**,
matching D8-RE's §8.4 read-only measurement:

| entry | group | value | status |
|---|---|---|---|
| `entry_vre_capacity_revenue` | entry | True | **UNIDENTIFIED** (`unattested`) |
| `miso_clean_tier_rows` | dispatch_mechanism | True | **UNIDENTIFIED** (`unattested`) |
| `miso_rps_compliance_regions` | dispatch_mechanism | True | **UNIDENTIFIED** (`unattested`) |
| `forecast_xyear_warmstart` | other | False | IDENTIFIED (design-decision, owner D-10) |

Same two epoch-drift rows as PJM; `backcast_keeper_at_build`:
`2026-08-30-miso-191-bexit`.

**Re-score:** the FC-7 `dof ledger` row moves in **DETAIL only** — from "DOF
ledger absent (identification unproven)" to the UNATTESTED-SKELETON text naming
the three entries awaiting attestation. Row status CAVEAT, FC-7 category
CAVEAT, the caveat list, and the **determination (HOLD, held by FC-1 I3) are
all UNCHANGED** — the scorer treats an unattested-carrying ledger exactly as an
absent one (D8 §1 step 4). Published: `ff-verdicts.json[miso-t1f]` (prior stamp
`54ca19ae0782 @ 2026-08-31T01:17:55Z` preserved; the S-123-V lane note
preserved verbatim), the ledger, a bundle sidecar (previously none).

**THE ROUTED DEBT, named and deliberately NOT attested** (rule 21 `[R-DOF]` —
an identification is *reported* from committed evidence, never invented to
clear a row; this lane's charter forbids attesting them):

- `entry_vre_capacity_revenue`
- `miso_clean_tier_rows`
- `miso_rps_compliance_regions`

All three are MISO's registered `default_scenario_overrides` inherited `True`;
the builder's `CURATED_IDENTIFICATIONS` table carries no session-reviewed row
citing committed evidence for them, so they stay UNIDENTIFIED. Closing the debt
= adding curated rows citing committed evidence (registry rule-5 citations /
intake findings), regenerating the ledger, and a chartered re-score — a
follow-up lane. This is also the first measured confirmation of D8-RE's §8.4
reading: **the "tiny, fully-identified T1-F free-parameter surface" of D8 §2 is
a NEISO/NYISO property, not a program-wide one.**

## §6 Board writes and assertions

`frontend/data/forecast/program-status.json`: `isos.NEISO.{t1f_determination →
PROMOTE, fc.FC-7 → PASS, blocking_rows[2] → the published record}`, the same
three for NYISO, `isos.PJM.fc.FC-7 → PASS`, one new
`d8_v_ledger_completion` lane block (the established `what_changed` /
`what_did_NOT_change` convention, plus the `miso_attestation_debt` list), and
this finding appended to `sources`. MISO's board block needed no edit: nothing
moved there, and its FC-7 story lives in the re-scored key + the lane block.

**Asserted programmatically against HEAD before commit** (the D8-RE §8.5
protocol): exactly the four intended keys differ in `ff-verdicts.json` and
every other key is byte-identical; on the board, every ISO determination not
moved here, every other fc cell, every keeper / marker / candidate / golden /
flip field, **every §2.1b gate cell (status AND detail)**, every other blocking
row, every prior lane block, and every other top-level field (headline,
gate_reading, readiness, tier_ladder, flip_config, honest_unfit, open_frontier,
readiness_limits, refresh, gate_a_provenance) are byte-identical; `sources` is
append-only.

**Flagged, not edited** (gate cells are outside this lane's write scope):
NEISO's and NYISO's `gate.b_t1f_verdict.detail` still open
"PROMOTE-WITH-CAVEATS" from their 2026-08-30 scoring and are now stale at HEAD
— routed to the **D19 board reconcile**, which the director queued for exactly
this class of cross-ISO prose.

Validators after the writes: `check_forecast_staleness.py` reads this lane's
stamp (`836e48e1efdc`) as the board's newest scored evidence and raises nothing
new (its one WARN — 31 of 51 verdicts carry no scored-at date — is
pre-existing and untouched); `register_forecast_run.py --reindex` assembles
cleanly (generated namespace stays gitignored, the Pages deploy is its writer).

## §7 Guardrail compliance

Zero solves — `forecast_verdict.py` re-scores and two
`build_forecast_dof_ledger.py` runs on committed inputs; no LP, no data read
beyond the bundles. No model surface touched: `src/market_sim/` and `scripts/`
unmodified. No re-grade, no hand-edited status, no widened band (rule 1
`[R-STRUCT]`): every published value is the scorer's own output; the controls
prove the scorer reproduces the committed records first. No measured-outcome
feedback (rule 13). The ledger reports identification and supplies none (rule
21): MISO's three UNIDENTIFIED rows are carried forward as UNIDENTIFIED and
named as debt, not papered over. Backcast namespace untouched (rule 15's
forecast/backcast split): no keeper shard, no `status/*.js`, no
`calibration-complete.json`, no backcast registry/runs sidecar. No holdout year
of any tier solved, scored or registered. No ScenarioConfig field, no
mechanism, no matrix cell (rule 28 not triggered — nothing tested). No GitHub
Actions workflow. Model assignment honoured (rule 27): the lane ran under the
charter's Fable assignment (two ISO determinations move — adjudication).
Branch created fresh off `origin/main`, rebased before every
push; every ≥300-line file blob-verified after push (rule 27), ff-verdicts.json
and program-status.json included.
