# FINDING — capx D110: rung-0 gate-(a) re-key (PJM/SPP/NWPP/SOCO) + PJM CT-2021 frontier carry (2026-10-03)

**Lane:** capx D110 (zero LP, DATA PROFILE: code), desk refresh #70, standing duty Q34 (rung 0 of ledger §0bn.2a)
plus the first frontier carry under ledger §0bn.2b.1 as amended by owner ruling Q75 (§0bn.4a).
**Read at:** origin/main `6277de60a22efb44dc2b5ce7f18d274ca7cfddc7` (PR #7152, the closeout-PJM-nuc merge). The
charter pinned `51422d1b5f02bff56e85b26ebbb36090eed14599`; origin/main had moved past it, so the branch was cut
from the newer main and every keeper / status / marker file below was read at `6277de60`.
**Scope:** `frontend/data/forecast/program-status.json` only (plus this record and one CHANGELOG entry). This lane
changes NO verdict, NO FC cell, NO tier, NO leg status, NO `complete` entry, NO keeper shard, NO status sidecar,
NO `ff-verdicts.json` byte. Nothing solved, scored or registered. Edited by targeted string edits at uniquely
anchored positions, never a `json.dumps` round-trip; a flattened before/after diff shows only the paths named in §1–§3.

## 1. Rung 0 — the nine-row keeper table (old → new)

Board determination = `frontend/data/backcast/status/<ISO>.js` `keeper.determination` (rubric 3.17), read live.
`complete` = `calibration-complete.json` `complete` block: **NEISO** (`2026-10-02-w0-neiso`) and **NYISO**
(`2026-10-02-w0-nyiso`, Q74); ERCOT / CAISO / SPP / PJM (Q73) in `withdrawn`; MISO, NWPP, SOCO never held one.

| ISO | program-status keeper before (at `6277de60`) | designated keeper (`keepers/<ISO>.json` at `6277de60`) | re-keyed? | board | `complete`? | gate (a) |
|---|---|---|---|---|---|---|
| ERCOT | 2026-10-02-closeout-l1-coal-fuel | 2026-10-02-closeout-l1-coal-fuel | no | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| CAISO | 2026-10-02-closeout-caiso-w1-arm2 | 2026-10-02-closeout-caiso-w1-arm2 | no | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| PJM | 2026-10-02-w0-pjm-fix2 | **2026-10-03-closeout-pjm-nuc-keeper** | **yes** (R-52, PR #7152) | NOT-YET | no (withdrawn, Q73) | NOT MET (unchanged) |
| MISO | 2026-10-02-w0-miso-fix2 | 2026-10-02-w0-miso-fix2 | no (R-53 not landed, §1.1) | NOT-YET | no (never) | NOT MET (unchanged) |
| NYISO | 2026-10-02-w0-nyiso | 2026-10-02-w0-nyiso | no | CALIBRATED | **yes** (Q74) | **MET** (unchanged) |
| NEISO | 2026-10-02-w0-neiso | 2026-10-02-w0-neiso | no | CALIBRATED | **yes** | **MET** (unchanged) |
| SPP | 2026-10-02-w0-spp107r | **2026-10-03-closeout-spp-nuc-keeper** | **yes** (R-44) | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| NWPP | 2026-10-03-closeout-nwpp-anchor-roster | **2026-10-03-nwpp-next-24-head** | **yes** (desk ruling NWPP-NEXT-24, PR #7148) | NOT-YET | no (never) | NOT MET (in `gate_a_provenance`, Q68) |
| SOCO | 2026-10-02-w0-soco-fix2 | **2026-10-03-closeout-soco-2-nuclear** | **yes** (R-41, PR #7112) | NOT-YET | no (never) | NOT MET (in `gate_a_provenance`, Q68) |

Four of nine `isos.<ISO>.keeper` fields were stale (the charter named three; PJM had moved to the pjm-nuc keeper
under R-52 by the read, as the charter anticipated). Each re-keyed row carries the prior id in its
`keeper_corrected_by` Supersedes chain — PJM and SPP prepend to the D101 chain; NWPP and SOCO receive the field for
the first time (their rows were added by the G5 forecast-board snippet and had no chain). The
`gate.a_keeper_marker.detail` leaves had already been re-keyed by `promote_keeper.py` and are byte-unchanged; no
leg status moves. The NWPP chain records the intermediate id `2026-10-03-nwpp-next-23-coi` that the leaf shows
between the two ids in the table.

**Per-row `gate_a` re-derived live** for the seven board ISOs: `read_live_at` → `6277de60`, `derived_by` → this
lane (prior derivation kept inline), `reason` → the live reading with the prior reason carried beneath. **No gate (a)
reading moved.** Gate (a) is MET for NEISO and NYISO and NOT MET elsewhere, exactly as r#69b left it; only keeper
ids moved. NWPP and SOCO keep no `gate_a` object on their rows: owner ruling Q68 (2026-09-24) admits a board reading
only after a backcast `complete` declaration, so both readings (NOT MET, board NOT-YET, never in `complete`) are
recorded inside `gate_a_provenance.d110_rekey.derived_by`, as D101 did.

**`gate_a_provenance`:** top-level stamp re-keyed to `derived_at_sha 6277de60` / `2026-10-03` / this lane; a new
`d110_rekey` block carries the full derivation text and nests the prior r#69b stamp (`07f5b88e`) as `prior_stamp`;
the existing `r69b_rulings` block (which nests D101 and its predecessors) is untouched.

### 1.1 Rulings recorded but not landed at the read sha (for the next rung-0 firing)

The close-out plan §5 carries two further promotion rulings whose keeper shards had NOT moved at `6277de60`:
**R-53** MISO → `2026-10-03-closeout-miso-nuc-r` and **R-54** SOCO → `2026-10-03-closeout-soco-3-coalpile`. This
stamp follows the shards (rule 35: a promotion is `promote_keeper.py`, not a ruling), so MISO stays at
`2026-10-02-w0-miso-fix2` and SOCO at `2026-10-03-closeout-soco-2-nuclear` here. Both re-keys belong to the rung-0
firing of the session that reads those promotions (§0bn.2a: a duty of the promotion-reading session).

## 2. Frontier carry (§0bn.2b.1, Q75)

**Which list.** `docs/codebase-site/forecast-status.html` renders `honest_unfit` entries with an `isos` chip per
entry (`id` · `title` · `(isos)` · `detail` · `lane`), `open_frontier` as the ranked lane table (`rank` /
`title` / `lane` / `detail`, no ISO), and `readiness_limits` as title/detail method cards (no ISO). So
`honest_unfit` is the ISO-scoped frontier list and the entry goes there; `readiness_limits` keeps its program-wide
items (the ercot-190 scarcity-tail card is program-wide wording, not an ISO row). Rendering code untouched.

**Carried — one entry, `honest_unfit[5]`, id `C1 CT_PEAKER 2021 — R-36`, isos `[PJM]`.** The owner-SIGNED
model-class frontier (ruling R-36, 2026-10-03, *"Sign CT 2021 now; hold COAL_BIT 1b for NEXT-31"*): out-of-merit
CT commitment conduct (IMM 2021 SOM Table 4-3: CTs took 92.8 % of the $128 M of balancing credits), every CT lever
adjudicated, re-open trigger a measured commitment-state input. The `detail` carries the signed ledger text
VERBATIM from the current PJM keeper's attestation,
`results/calibration/closeout_pjm_nuc_full_span/calibration_attestation.json` `exceptions[0]` (kind `model-class`,
criterion fuelmix, class CT_PEAKER, year 2021, magnitude −8.07 TWh; `carried_forward` from
`2026-10-02-w0-pjm-fix2` into `2026-10-03-closeout-pjm-nuc-keeper`, not re-measured because C1 is not ledgerable
under rubric v3.1 — the entry documents the FAIL and reclassifies nothing; PJM stays NOT-YET). Record paths in the
entry's `record` list: the attestation above; `docs/records/pjm/DRAFT-closeout-pjm-2-frontier-text-2026-10-03.md`
Statement 2 (source text); `docs/records/pjm/RESULT-closeout-pjm-impl-2026-10-03.md`; `docs/calibration-log/pjm.md`
closeout-PJM-impl entry; `docs/backcast-closeout-plan-2026-10.md` §5 R-36. The entry states the Q75 posture in its
`lane` and `detail`: **PJM gets no forecast work at all** (no T0/T1 POC, no indicative tier) until its determination
changes; rungs 0–1 only. A `forward_implication` paragraph (§0bn.2b.2, zero LP) names what the forecast would
mis-state — CT shoulder-hour commitment and its balancing-credit uplift read cost-based, not conduct-based — and
that under Q75 no PJM forecast row exists to mis-state it.

**Watched, NOT carried** (the charter's exclusions, confirmed against the plan text at `6277de60`):

| row | why not carried |
|---|---|
| R-37 PJM 2025 C3a/C3b *"Documented FAIL; no re-open"* | a documented FAIL with the online-gated reserve pool as a frontier **CANDIDATE**; no signed frontier statement. |
| R-47 PJM COAL_BIT 2019–21 frontier card | **held** by the owner until after the PJM-nuc promotion (now landed, R-52), so the card is due but unsigned; closeout-PJM-2's DRAFT (Statement 1) owns the wording. |

**Search for other owner-SIGNED frontier statements** (plan §5 rows R-1…R-54 and every "frontier" / "owner-signed"
mention outside §5): R-36 is the only row in which the owner signs a **model-class frontier**. Rows that ledger a
miss as **data-limited** are a different class and were not carried: R-26 PJM Elliott 2022 *"Accept as data-limited"*
(C3a/C3b/C3c 2022), R-32 ERCOT *"Both rows data-limited"* (2019/20 coal conduct; 2024 West LZ basis). R-40 (CAISO
C3a 2019–21 reference-coverage caveat) is a rubric amendment, not a frontier. The ledger §0bn.2b.2 list (ERCOT 2023
ECRS tail, SPP 2019–20 body, MISO 2020 low-load margin, SOCO reference error, NWPP price reference) names
candidates the close-out program has not signed; none is carried.

**Not done here (desk item):** §0bn.2b.4 asks for a forecast-side `U` row in the mechanism matrix for each frontier
mechanism. That is a `docs/codebase-site/data/mechanism-matrix*.js` edit outside this lane's file scope and is left
for the desk to charter (rule 28: the session that tests a cell writes it; nothing was tested here).

## 3. Rung-1 note (D102 census method, re-run zero-LP for the re-keyed ISOs)

`ff-verdicts.json` at `6277de60`: **SPP carries one verdict** (`spp-t1h`, HOLD), **PJM carries 21**
(`pjm-t1f`, `pjm-t1h`, `pjm-t1x` and their `-pre-*` / `-ff2d` / arm / control keys, all HOLD); **NWPP and SOCO carry
none**, so the census has nothing to classify for them. Method re-run via `uv run --frozen python` over
`market_sim.config.solve_surface.moved_rows` / `SOLVE_EPOCHS`:

| ISO | keys | `SOLVE_EPOCHS` reaching a forecast key | live `moved_rows` | post-verdict movers | reading |
|---|---|---|---|---|---|
| SPP | 1 | none (`2026-10-02e`, `2026-10-03b` are `modes=('backcast',)`) | 8 | CC_STEAM_PART_REPAIR_ISOS (as D102) | STALE-SURFACE (all 1) |
| PJM | 21 | none (`2026-10-02c/d`, `2026-10-03b` are `modes=('backcast',)`) | **13** (D102 read 12) | CC_STEAM_PART_REPAIR_ISOS, STORAGE_BASE_FLEET_MW, **+ NUCLEAR_MONTHLY_CF_BY_YEAR** (the R-35 rows, PR #7109) | STALE-SURFACE (all 21) |
| NWPP | 0 | — | 8 | — | nothing to classify |
| SOCO | 0 | — | 13 | — | nothing to classify |

Seven `SOLVE_EPOCHS` exist at HEAD (`2026-10-02c/d/e`, `2026-10-03a/b/c/d`), every one `modes=("backcast",)`, so
no epoch moves a forecast key; staleness stays value-level (D102 §5). The readings for SPP and PJM are unchanged
from D102 (STALE-SURFACE), with one additional PJM mover. Under Q75 PJM's rung 3 is closed regardless; SPP has no
`complete` entry and no T1-F, so its rung 3 is not in question either.

## 4. Checks run (all exit 0 before AND after the edit)

Before the edit, at `6277de60`: `scripts/audit_keepers.py` PASS (0 failures, 4 warnings) · `scripts/check_forecast_parity.py`
(9 postures, 0 unaccounted, 26 filed gaps, 0 errors) · `scripts/check_registry_payload_parity.py` (9 runs OK). After
the edit: identical readings, all EXIT 0; `python3 -c 'import json; json.load(...)'` re-parses the file; fast lane
`pytest tests/scoring/test_promote_keeper.py -n auto -m "not slow and not integration and not fulldata"` → 13 passed
(the only test module that names `program-status`; it monkeypatches a tmp copy).

## 5. Deviations and leftovers

* Charter pin `51422d1b` was behind origin/main; branched from `6277de60` and recorded both SHAs (as instructed).
* The charter said "three stale"; four were (PJM had moved under R-52), as the charter's own check anticipated.
* NWPP and SOCO `isos` rows exist on the board (G5 snippet) although Q68 admits a board row only after `complete`;
  this lane re-keyed their keeper id (the charter says every row) and added no `gate_a` object, keeping their
  readings inside `gate_a_provenance`. Whether the rows should exist at all is a desk question, not this lane's.
* R-53 / R-54 re-keys deferred to the session that reads those promotions (§1.1).
* Mechanism-matrix `U` row for the PJM CT frontier (§0bn.2b.4) left for the desk (§2).
