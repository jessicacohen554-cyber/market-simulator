# FINDING — caiso-193 (lane 2): `wefor_residual` is REFUSED AT G-COV — both granted classes fail the 95 % observability bar on the frozen instrument; **killed before solve**. The CC_REGULAR miss decomposes into TWO named instrument defects, one repaired by the companion session caiso-196 the same day

**Zero LP. Nothing registered. No data byte written by this lane. DOF 11/8 untouched.
C3a never read.** Keeper UNCHANGED at `2026-08-09-caiso-188-d1-micseam`. 2023–2025
only; both holdout markers untouched (owner acts); the holdout spend freeze untouched.

Gate spec applied as written: `GATESPEC-caiso193-wefor-residual-2026-08-11.md`
(authored by caiso-191 BEFORE any lane-2 measurement, owner ruling 2). No band was
edited or reinterpreted. Measurement instrument:
`scripts/probes/_caiso193_wefor_coverage.py` → committed record
`results/calibration/_caiso193_wefor_coverage.json`.

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

No price series was read anywhere in this lane; no C3a number appears in this FINDING.

## 1. The G-COV measurement, and the §5 kill

G-COV (GATESPEC §4): a class enters `wefor_residual_groups` only if ≥ 95 % of its
EIA-860 capacity (through the shipped fleet path — the caiso-187 probe's own
construction, so the population is exactly the LP's bins) belongs to plants present
in the committed CAMPD CAISO extract population. Measured against BOTH defensible
readings of "extract population", gated on the STRICTER (GATESPEC §5 conservative
default — exclusion keeps MORE removal in place, the anti-C3a-favorable direction):

| class | capacity | extract population¹ | CEMS 2023–25 population² | strict | bar | verdict |
|---|---|---|---|---|---|---|
| CC_CHP | 1,689.3 MW (21 plants) | **0.678375** (9 plants) | **0.635703** (6 plants) | 0.6357 | ≥ 0.95 | **FAIL** |
| CC_REGULAR | 15,284.8 MW (28 plants) | **0.940625** (26 plants) | **0.841402** (22 plants) | 0.8414 | ≥ 0.95 | **FAIL** |

¹ facility_ids appearing in the committed `data/raw/campd-unit-outages-CAISO.csv`
(sha256 `25360e90…1166c6`, the extract the LP derates from).
² facility_ids in `data/raw/campd-unit-level/CA_{2023,2024,2025}.parquet`, the
detector's own source, restricted to the solve years.

**Both granted classes fail, so GATESPEC §5 fires as written: "If BOTH classes fail
G-COV the arm is dead; the null result is reported (that too is a finding: the grant
was conditioned on an observability that failed)." No solve, no PRECHECK, no arm.**
(The §1 cure PRECHECK is a pre-*solve* artifact; the lane died at the gate before the
solve stage, so the obligation never fired. Its content is prepared in §4 below for
any owner-granted re-run.)

## 2. The decomposition — what the miss actually is, verified in bytes

**CC_CHP (63.6–67.8 %): a REAL observability limit, not repairable by plumbing.**
12 of 21 plants (543.4 MW, 32.2 %) are absent from the extract; 15 of 21 are absent
from the 2023–25 CEMS files. These are small industrial cogens (2–161 MW: e.g.
50216 Watson Cogeneration 141.8 MW, 55084 Crockett 160.6 MW, 10342 73.8 MW), largely
outside 40 CFR Part 75's practical CEMS coverage. The gatespec's fail-closed clause
is doing exactly its job here: CC_CHP keeps its full statistical WEFOR because the
overlay cannot see it.

**CC_REGULAR (94.06 % on the extract population — a 0.94 pp miss): two named
instrument defects, 907.5 MW.**

1. **El Segundo Energy Center, EIA 57901, 537.4 MW (3.52 % of the class) — a
   CEMS→EIA split-plant remap gap.** The plant IS CEMS-observed: its two CTs report
   to CAMPD under the legacy site ORIS **330** as units **"5"** and **"7"** in every
   CA unit-level file 2018–2025 (verified; e.g. 581/560 GWh gross in 2018,
   30–103 GWh/yr 2023–2025). `campd.CAMPD_UNIT_PLANT_REMAP` carries the two sibling
   repowers — (315, CT1/CT2) → 62115 AES Alamitos, (335, CT1/CT2) → 62116 AES
   Huntington Beach — but **no (330, ·) → 57901 row**. Without it,
   `derive_campd_unit_outages.py` re-keys nothing, `group_by_code.get(330)` matches
   no fleet plant (EIA plant 330's own units retired 2015, so unlike 315/335 nothing
   remains to mis-attribute to), `fac_groups & QUALIFYING_PLANT_GROUPS` is empty and
   the whole facility is skipped BEFORE detection — silently, which is why the two
   loud siblings were caught and this one never was. EIA-860 generator IDs at 57901
   are "5"/"6"/"7"/"8" with the CTs at "5" and "7" — an exact ID match to the CAMPD
   units, so the capacity index resolves with no digit heuristics. Effect on the
   keeper: a 537 MW CC_REGULAR plant's measured outage history never derates the LP;
   it carries only the statistical WEFOR (×0.7 multiplier) while its real windows
   sit unread on disk. **Repaired the same day by the companion session caiso-196**
   (`PRECHECK-caiso196-elsegundo-remap-2026-08-15.md`), which pre-registers the
   remap fix + full-span extract re-derivation + an A/B re-solve of the caiso-188
   recipe on the repaired extract.
2. **Desert Star Energy Center, EIA 55077, 370.1 MW (2.42 %) — a state-scope gap.**
   A 2000-vintage CAISO CC in Clark County, **Nevada**. `campd.ISO_STATES["CAISO"]`
   is `("CA",)` and `data/raw/campd-unit-level/` holds no NV file, so the plant is
   unobservable by the current intake. The NYISO precedent (NY + NJ, with the loader
   filtering every state to the ISO's own fleet so nothing leaks) is the exact
   template for adding NV. **Filed as a follow-up intake, not executed here** —
   rule 22 data intake is unrestricted, but the fetch requires the CAMPD API queue
   path and its own byte-verified landing.

Also recorded: 50541 Harbor Cogen (107.4 MW) and 50748 Agnews (32.0 MW) are covered
in the extract population only through the plant-grain `eia923_netzero` channel
(full-year observed-inactive windows, 2025–2026 rows only) and appear in no CA CEMS
file 2018–2025 — their 2023–2024 availability is unobserved. They are counted
covered under reading ¹ and uncovered under reading ².

## 3. What survives on the repaired instrument (measured, no-LP)

With the El Segundo remap in place (caiso-196), CC_REGULAR's extract population
gains 57901 and the class measures **97.58 %** (uncovered: Desert Star only) on
reading ¹ and **96.67 %** on the strict 2023–25 CEMS reading (uncovered: Desert
Star + Harbor + Agnews) — **≥ 95 % under BOTH readings**. CC_CHP stays excluded
fail-closed. A `{CC_REGULAR}`-only arm is the subset the GATESPEC itself prescribes
("A class below 95 % is EXCLUDED from `wefor_residual_groups` (fail-closed);
uncovered units keep their full WEFOR by construction when their class is
excluded"), so it remains within owner ruling 2's grant. The owner-granted VALUE is
invariant to the repair by construction: `residual_c = max(0, W_c − X_c)` with
CC_REGULAR X already 4–6× W on the committed extract (0.2157/0.2621/0.3186 vs 0.05),
and the repair can only RAISE X. The frozen 0.0 cannot move.

## 4. Escalations owed to the owner (nothing here is executed by this session)

1. **Campaign re-anchor.** The integration protocol §3 fixes the campaign control to
   the caiso-188 recipe on its committed inputs, and "deviation requires a fresh
   adjudication session and explicit owner authorization". The caiso-196 repair, if
   its gates pass, changes a keeper INPUT — the same class of event as the
   2026-07-24 detector re-derive ("flagged for a CAISO re-audit/re-solve", executed
   as caiso-180). Whether the campaign's remaining lanes (3, 5) re-anchor onto the
   repaired-extract base, and whether the caiso-196 arm is promoted, are owner
   decisions the caiso-196 FINDING packages.
2. **Lane-2 re-run grant on the repaired instrument**, scoped `{CC_REGULAR}` per §3
   above. Fully prepped: value 0.0 / multiplier 1.0 / groups {CC_REGULAR}, the §1
   cure's clauses (scoped-groups form only; protective gate dominant; no
   recomputation — the frozen `_caiso187_residual_identification.json` record
   stands; ST_GAS untouched, lane 3's object). Needs only the owner's word plus the
   re-anchored control.
3. **NV CAMPD intake** (Desert Star; template: the NYISO NY+NJ state-list entry),
   after which CC_REGULAR's extract population reaches 100 % of its current roster.
4. **The `eia923_netzero` 2023–2024 blind spot** for Harbor/Agnews (139.4 MW):
   observed-inactive only from 2025. Diagnostic note, no action proposed.

## 5. Matrix duty (b)

`wefor_residual` CAISO cell: **O → R** — a coverage/provenance refusal on the frozen
instrument, NOT a dispatch-level refutation (the caiso-194 `hydro_ror_split`
precedent: a re-anchored instrument is a new charter, not a DO-NOT-REDO-frozen
cell). Evidence citation updated in
`docs/codebase-site/data/mechanism-matrix/CAISO.js` this session.

## 6. G-DOF baseline (recorded, unmoved)

`caiso188_d1_micseam/calibration_attestation.json` `free_parameters`: n_entries 11 /
n_residual 8; the `wefor_multiplier` row (value 0.7, identification "residual",
lineage ≥52 solves) quoted in the committed record. No solve ⇒ no ledger movement;
the 11/8 → 11/7 target remains the re-run's arithmetic obligation, not this
session's claim.

## 7. Environment

Full clone (all `data/raw` blobs local); `data/clean/capacity-deliverability/CAISO`
materialized this session via `scripts/data/curate_capacity_deliverability.py --isos
CAISO` (386 rows, matching the committed intake count) in preparation for the
caiso-196 solves; highspy 1.14.0 (the caiso-188 G-CTRL cross-build identity covers
1.14.0 ↔ 1.15.1). The dashboard-deploy stall found at session start (deploy run
#1400 stuck `waiting` since 2026-08-06, holding the `pages` concurrency group; every
later deploy auto-cancelled) was cleared by cancelling the stuck run; run #1510
deployed clean at 2026-08-15T20:33Z, so the live dashboard again shows the committed
keeper lineage through caiso-188.
