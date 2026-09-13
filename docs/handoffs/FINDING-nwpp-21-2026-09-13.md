# FINDING — NWPP-21: the eighth mechanism-matrix shard (rule 28 `[R-MECH-MATRIX]`)

**Lane** NWPP-21 · **Model** Opus `claude-opus-5` · **Date** 2026-09-13 ·
**Base sha** `33a7c961` (= the r#3 issuance pin) · **Branch**
`claude/nwpp-21-matrix-shard-6qezh7` · **DATA PROFILE** `code` ·
**Zero LP spent** (rule 32 `[R-SHARD]` (a) — this lane runs no solve; rule 31
`[R-RETAIN]`'s promotion question does not fire).

**Charter** `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-21, W2
prompt §8. **Template** `docs/codebase-site/data/mechanism-matrix/SPP.js`
(the seventh shard, emitted by lane SPP-21, 2026-09-06).

---

## 0. Measured at this lane's own base sha — NOT taken from the charter

The charter required re-measurement because a sibling program (SOCO, chartered
2026-09-12) may register first (plan §0, gate **G2**). Measured at `33a7c961`:

| Quantity | Measured | Charter/notice said |
|---|---|---|
| `mechanism-matrix.js` base `isos` | **7** — `ERCOT CAISO PJM MISO NYISO NEISO SPP` | 7 |
| `scripts/lib/mech_matrix.ISO_ORDER` | **7**, same names, same order | 7 |
| Shard files on disk | **7** (`CAISO ERCOT MISO NEISO NYISO PJM SPP`) | 7 |
| `SOCO` occurrences in `scripts/lib/mech_matrix.py` | **0** | 0 |
| Base mechanism rows | **327** | — |
| ev letters taken | `E C P M N Q S` — **`W` free** | same |

**So NWPP is the EIGHTH shard and takes `W`.** No count in this document is
carried from the notice; every one was re-derived here. If this lane is rebased
onto a `main` that has since landed SOCO, §8.0 rule 3 applies: rebase, re-count
at the new sha, re-run the checker — the emission is mechanical and reproduces.

---

## 1. Cell census — the exit check

**327 ids · 174 `U` · 153 `.`** (of the 153, **47** are forecast-lane-only and
carry `fc: "U"`; the remaining **106** are foreclosed in both lanes).
Sum check: 174 + 153 = 327 = the base row count. Verified against the committed
file through the committed assembler (`mech_matrix.load_merged`), not against
the emitter's in-memory state.

| Class | Cells | Rule |
|---|---:|---|
| `U` — untested, plausibly applicable | **174** | fall-through |
| `.` — ISO-exclusive elsewhere | **100** | (a) |
| `.` — no centralized forward capacity auction (both lanes, no `fc`) | **6** | (b) |
| `.` + `fc: "U"` — forecast-only row | **47** | (c) |

`keeper` and `gates` are **deliberately EMPTY**: NWPP has no keeper, no bundle,
no solve of any kind, and is **not yet registered in `_ISO_BUILDERS`** (W2 /
NWPP-20 flips that pin). Both the CI guard (`keeper_drift`) and
`test_mechanism_matrix_shard_migration` fail open for an ISO with no
`frontend/data/backcast/keepers/<ISO>.json`, which is the same scoping SPP-21
relied on.

### 1.1 The classification rule, applied in order

Stated in the shard's own header so any cell can be audited without re-deriving
the column:

- **(a) ISO-EXCLUSIVE ELSEWHERE → `.`** — the id carries a foreign
  `ScenarioConfig` stem (`ercot_ caiso_ pjm_ miso_ nyiso_ nysdec_ neiso_ spp_`)
  or names a foreign region/programme (`wtx_ path15_ tsa_ rdt_tcdc
  wecc_endogenous_node`), **and every non-owner ISO's cell reads `.` at HEAD**.
  A foreign-stemmed row some other ISO *has* entered is a live cross-ISO
  question and reads `U` — 7 such rows (`ercot_wind_zone_shape`,
  `ercot_storage_adaptive_expectation`, `caiso_p1_export_sink_seam`,
  `caiso_node_export_constraint`, `miso_intermediate_gas_offer_margin`,
  `pjm_midcurve_belt`, `nyiso_ct_peaker_bands_measured`).
- **(b) NO CENTRALIZED FORWARD CAPACITY AUCTION → `.` in both lanes** — six
  rows: `capacity_market_clearing`, `capacity_market_supply_clearing`,
  `capacity_going_forward_bar_published`, `capacity_no_default_cap_convention`,
  `net_cone_forward_vintages`, `locality_capacity_curves`.
- **(c) FORECAST-ONLY ROW (`mode: "F"`) → `.` + `fc: "U"`** — 47 rows. NWPP has
  no forecast-lane entry at HEAD (W6 / card N9, routed to the capx director;
  gate G16), and this shard is not the forecast board.
- **otherwise → `U`.**

This rule reproduces SPP's committed column **exactly** where the two footprints
agree: run against SPP it predicts all 327 of SPP's cells, and the arithmetic
reconciles end to end — SPP's 152 `.` **+ 2** (`spp_gas_commitment_bridge`,
`spp_curtailment_ceiling` are SPP's own rows and therefore foreign to NWPP)
**− 1** (`state_carbon_pricing`, §1.3) **= NWPP's 153**. That is the check that
the emission is mechanical rather than editorial.

### 1.2 Two charter-offered reasons this seed did **NOT** use

Recorded here and in the shard header so their absence is never read as an
oversight. `.` is the STRONGER claim — it forecloses a lever — so a reason that
does not survive contact with the row set must not be spent:

- **"No reserve co-optimisation" foreclosed ZERO cells.** All eight reserves
  rows in the base set (`energy_reserve_coopt`, `reserve_pergen`,
  `dynamic_reserve_requirements`, `reserve_deliverability_scoping`,
  `online_capacity_envelope`, `measured_ramp_capability`,
  `reserve_family_sidecar`, `reserve_family_dual_sidecar`) are requirement,
  pool, scoping or write-only *instrument* rows — none is a market-cleared AS
  price or a published reserve demand curve, which is the thing NWPP lacks. And
  `model/reserves/spec.py` takes an NWPP entry at W2 (plan §2.3, per cards
  N5/N7), so each of those objects exists for NWPP. All eight read `U`.
- **"No offer-curve tuning channel" foreclosed ZERO cells.**
  `offer_curve_by_group` is the shared per-class band **container** every ISO
  carries (cells `KKKKKKK` at HEAD). NWPP's bands sit at **1.0**, which is a
  *value*, not an absence — and gate **G5** states it as the desk's posture
  *"unless the owner rules otherwise"*. A posture cannot carry `.`. It reads `U`.

### 1.3 The one cell where NWPP diverges from the SPP template

**`state_carbon_pricing` reads `U` here; SPP reads `.`.** SPP's stated reason is
that no state in its footprint carries a carbon programme. That reason does not
hold for NWPP: **Washington's Climate Commitment Act cap-and-invest programme
has been in effect since 2023-01-01** — inside the 2023–2025 scored window —
and covers in-state electricity generation and imported electricity, and WA is
the footprint's largest state by capacity (31,711.8 MW of 98,738.1 MW, plan
§2.1). So an NWPP allowance cost in dispatch is a real candidate object, not a
structural absence, and `.` would be the stronger claim made falsely.

**Nothing is asserted about magnitude, coverage or price**, and no lane may arm
this from memory: the registry values and the in-window applicability are
NWPP-12's to transcribe with URL + page (plan §6 discipline). Plan §2.3's
`test_iso_coverage` row expects carbon-`None` at registration — that is a W2
default, not an adjudication of this cell.

### 1.4 One bespoke `.` worth reading — `wecc_endogenous_node`

NWPP *is* WECC, so this row's name is the one place rule (a) could be
mis-applied. It is `.` for **two** independent reasons, both in its `ev`:
(1) the object is CAISO's own `WECC_import` zone (`iso_configs.py`
:533/:570/:573 and its two `TransferLink`s under the 7,500 MW simultaneous
cap), and every non-owner ISO reads `.`; (2) NWPP gets **no import node** of its
own — its seams are served schedules, so neither `IMPORT_TRANCHES` nor
`IMPORT_ZONE` takes an NWPP key and `build_import_generators("NWPP") == []`
(plan §3 recorded defaults, gate **G7**).

**Card N4's double-count is carried in that cell rather than resolved by it**:
CAISO's `WECC_import` counterparty *is* this footprint —
`model/interchange/caiso.py`:443 names its firm tranches `PNW_hydro_base` /
`DSW_solar_PV` — so registering NWPP puts the same physical energy on both sides
of a seam, represented two ways. Rule 25 `[R-ISO-SCOPE]` forbids this lane
touching how CAISO prices its side and it did not; the CAISO-side question stays
routed to the CAISO lane.

### 1.5 What fell through to `U` on purpose

Named in the shard header so the next lane does not read `U` as "nobody looked":
the **hydro family** that is this program's structural core
(`hydro_budget_period_by_instrument`, `hydro_dispatch_envelope`,
`hydro_min_flow_floor`, `hydro_ror_split`, `hydro_budget_nameplate_aware`,
`hydro_level_923_hy`, `hydro_vintage_input_repair` — cards N3 / NWPP-32 /
NWPP-36); the **seam and import-price rows** lever NWPP-56 will enter
(`priced_interchange`, `reference_price_interface`, `import_hub_pricing`,
`import_shape_lever`, `seam_neighbour_anchored_ladder`,
`seam_neighbour_hourly_ladder`, `measured_interface_limits`); and the genuinely
open ones (`capacity_deliverability`, `lcr_tsl_published`,
`m2m_seam_entitlement_cap`, `mass_cap_lp_row`, `legacy_p2`).

---

## 2. Gate G15 — `scripts/check_mechanism_matrix.py` OUTPUT (not its exit code)

```
mechanism-matrix: integrity OK (docs/codebase-site/data/mechanism-matrix.js + 8 ISO shards)
mechanism-matrix: anchors checked (206 field + 51 row + 206 path; skipped 39 non-field token(s) and 4 unresolvable path(s)) — 257 unresolvable beyond the ratchet
mechanism-matrix: keeper stamps match every keepers/<ISO>.json
mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json
mechanism-matrix: gap ratchet OK (no ISO-scoped field is invisible)
mechanism-matrix: shared ratchet OK (no keeper arms an unregistered shared field)
mechanism-matrix: absent-shared ratchet OK (every shared field is registered or baselined)
mechanism-matrix: diff gate NOT RUN — pass --base <sha> to check new-field registration, keeper-promotion stamps and anchor blame. A 0 from this mode is not a registration verdict for a NEW field.
```

Exit 0. **257 `::warning::` lines are emitted and are elided above**: every one
is a pre-existing stale line anchor (`<field> :<line>` digits drifted by an
unrelated `scenarios.py` merge), they are advisory by design, and the count is
**byte-identical before and after this lane** — 257 → 257.

**The only line that changed at all is the first: `7 ISO shards` → `8 ISO
shards`.** `diff` of the full non-warning output before/after this commit
reports exactly that one substitution and nothing else — which is the evidence
that the `ISO_FIELD_STEMS` addition in §3.2 is a measured no-op rather than an
asserted one.

### 2.1 Tests

```
tests/unit/config/test_mechanism_matrix_keeper_stamp.py
tests/unit/config/test_mechanism_matrix_shard_migration.py
tests/unit/config/test_mechanism_matrix_shared_ratchet.py     33 passed
tests/unit/config (full directory)         846 passed, 25 skipped, 23 subtests
```

### 2.2 Rule 25 `[R-ISO-SCOPE]` proof — no other ISO's column moved

The pre-change matrix was rebuilt from `origin/main` and compared to the
post-change matrix through `mech_matrix.canonical()`, per mechanism × ISO:

```
rows compared   : 327
non-NWPP drift  : NONE — every existing ISO's verdict, fc, ev and note byte-identical
keepers/gates   : unchanged
```

Also verified on the committed store: shard cell-id set **≡** base row-id set
(327/327), every cell char inside `K R I G O U .`, ev letter `W` present on all
327, `fc` set on exactly the 47 forecast-lane rows.

---

## 3. The ONE commit (gate G2)

### 3.1 As chartered

| File | Change |
|---|---|
| `docs/codebase-site/data/mechanism-matrix/NWPP.js` | **NEW**, 434 lines — 327 cell lines + the classification-rule header |
| `docs/codebase-site/data/mechanism-matrix.js` | base `isos` += `"NWPP"` (one line) |
| `scripts/lib/mech_matrix.py` | `ISO_ORDER` += `"NWPP"`; `ISO_EV_KEY["NWPP"] = "W"` |
| `docs/codebase-site/mechanism-matrix.html` | `<script src="data/mechanism-matrix/NWPP.js">` tag |
| `tests/unit/config/test_mechanism_matrix_shard_migration.py` | comments only — the frozen-fixture ISO list at line 113 is **deliberately untouched** (it pins the 2026-08-11 pre-shard monolith; comparing it to the live tuple is exactly what that test forbids) |
| `docs/codebase-site/css/shared.css` | `--iso-nwpp: #6366F1` (indigo — distinct from every existing token) |
| `docs/codebase-site/js/backcast-runs.js` | `ISO_COLORS.NWPP = '#6366F1'` |
| `docs/mechanism-testing-matrix.md` | **§5.8 NWPP lever queue** (new) + `### 5.8 Cross-cutting audits` renumbered `### 5.9` |

### 3.2 Three files beyond the charter's enumeration — routed to NWPP-DESK

Each is inside the matrix surface and each is **required for gate G2 to land
whole**; none is another ISO's cell value, none is `src/`, none is
`frontend/data/**`. Named here per the charter's "if you must touch a file
outside your regions, STOP and route" clause:

1. **`docs/codebase-site/data/mechanism-matrix-assemble.js`** — `EV_KEY` gains
   `NWPP: 'W'`. **Forced by an existing test**:
   `test_python_and_browser_assemblers_stay_in_sync` asserts `f"{iso}: '{letter}'"
   appears in the browser twin for **every** entry of `mm.ISO_EV_KEY`, so adding
   `W` to the Python map without this edit turns that test red. The module
   docstring already requires the two assemblers be kept in sync.
2. **`tests/unit/config/test_mechanism_matrix_keeper_stamp.py`** — its `ISOS`
   tuple (line 41) is the real "expected set" the charter refers to; the
   charter names `test_mechanism_matrix_shard_migration.py`, whose only ISO list
   is the **frozen fixture's** and must not move. Two tests
   (`test_matrix_isos_parses_every_iso`, `test_matrix_keepers_stamps_every_iso`)
   fail without this edit. Its `KEEPER_ISOS` scoping already fails open for an
   ISO with no keeper shard, so NWPP's empty stamp is admitted by construction.
   **Recommendation to the desk:** the plan's §2.3 matrix pin row should name
   this file, not (or as well as) the migration test.
3. **`scripts/lib/mech_matrix.ISO_FIELD_STEMS`** — gains `"NWPP": ("nwpp",)`.
   A **judgement call, measured as a no-op**: `scenarios.py` carries zero
   `nwpp_*` fields at this sha, so all three ratchet lines are byte-identical
   (§2). Registered anyway so the first `nwpp_*` field — NWPP-36's coupling
   gate, if it takes an ISO stem — is classed ISO-scoped rather than falling
   silently into the SHARED complement, which is the exact hole
   `absent_shared_fields` exists to close. **Back this out if the desk prefers
   the stems table to move only with NWPP-20's pin flip**; nothing else in this
   commit depends on it.

### 3.3 A scope collision to sequence — the dashboard colour

Plan §2.3's "Dashboard colour" pin row and §5's lane table both assign
`--iso-nwpp` to **NWPP-35**; the r#3 charter issued to **this** lane assigns it
here, in the enumerated one-commit list. This lane executed its own charter
(nothing else claims the file yet, so §8.0 rule 5's "second lane on the same
file" has not fired — NWPP-21 is first). **The desk should de-scope the colour
from NWPP-35's row** so the later lane does not re-mint it. NWPP-35's remaining
site work is untouched here: `js/viz-iso-topology.js` and
`js/iso-configs-table.js` carry their own `ISO_COLORS` maps and this lane did
**not** edit them, nor `scripts/build_status.py` / `render_data_dictionary.py`,
which hold unrelated `ISO_ORDER` tuples belonging to NWPP-20/NWPP-35.

### 3.4 §5.8 seeding — what was and was not seeded

Seeded from plan §4's W5 list, in issue order: **NWPP-55** WECC path TTC derive
· **NWPP-56** priced seams · **NWPP-57** WRAP adequacy · **NWPP-58** zone
refinement · **NWPP-59** retirement sector gate.

**NWPP-54 (Columbia hydraulic coupling) was NOT seeded** — owner ruling **N3**
(sitting #1, 2026-09-13) retired it from the queue and promoted its content into
W3b / **NWPP-36**, ahead of the first keeper. §5.8 records it under *"RETIRED
FROM THIS QUEUE BEFORE IT WAS EVER ISSUED"* with the gate-G8 cache-key condition
it must satisfy, so a later reader cannot mistake its absence for an omission.

§5.8 also carries the standing rules that bind the queue (25 / 29 / 16 / 28(b))
and the **N2 price-benchmark caveat** — no lever may assume a benchmark exists,
and gate **G17** (substituting SP15/NP15, Palo Verde, or Mid-C as a benchmark)
stays refused.

---

## 4. What this lane did NOT touch

Per §8.0 collision rules 1 and 2, and the charter's MUST-NOT list: no other
ISO's shard **cell values** (proved byte-identical in §2.2), no other ISO's
keeper shard or calibration log, no `src/`, no `frontend/data/**` (backcast or
forecast), no `ScenarioConfig` default, no CI workflow, no plan file, no ledger,
no `docs/calibration-log/nwpp.md`, no `CHANGELOG.md`. `docs/mechanism-testing-matrix.md`
§5 is the single shared record the charter explicitly grants, and this lane
edited **only** its own new §5.8 plus the one renumbered heading below it.

## 5. Log entry (for the desk to append verbatim)

> **NWPP-21 — 2026-09-13 — matrix shard (Opus, zero LP).** The eighth
> mechanism-matrix shard `docs/codebase-site/data/mechanism-matrix/NWPP.js` is
> live: **327 ids · 174 `U` · 153 `.`** (47 of the `.` are forecast-lane-only
> with `fc: "U"`). `ISO_EV_KEY["NWPP"] = "W"`, `ISO_ORDER` and the base `isos`
> re-measured at the lane's own sha `33a7c961` as **7 → 8**. `keeper`/`gates`
> empty by design — NWPP is not yet in `_ISO_BUILDERS`. `check_mechanism_matrix.py`
> exit 0, its output byte-identical to the pre-change run **except** `7 ISO
> shards → 8`; 33 matrix tests and the full `tests/unit/config` (846 passed)
> green; canonical per-mechanism × ISO comparison against `origin/main` shows
> **zero drift** in every existing ISO's verdict, fc, ev, note, keeper and gates.
> One cell diverges from the SPP template by design: `state_carbon_pricing` is
> `U`, not `.`, because Washington's Climate Commitment Act cap-and-invest is in
> effect across the 2023–2025 window. Two charter-offered `.` reasons foreclosed
> **zero** cells and are recorded as unused rather than stretched. §5.8 NWPP
> lever queue seeded (NWPP-55/56/57/58/59; **NWPP-54 not seeded**, retired by
> ruling N3 into NWPP-36); `--iso-nwpp: #6366F1` minted. **Three items for the
> desk:** (a) the colour is chartered to both NWPP-21 and NWPP-35 — de-scope
> NWPP-35; (b) the plan's §2.3 matrix pin row should name
> `tests/unit/config/test_mechanism_matrix_keeper_stamp.py`, which holds the real
> expected ISO set, not the migration test's frozen fixture; (c)
> `ISO_FIELD_STEMS["NWPP"]` was added as a measured no-op and is trivially
> reversible if the desk wants it to ride NWPP-20's pin flip instead.
