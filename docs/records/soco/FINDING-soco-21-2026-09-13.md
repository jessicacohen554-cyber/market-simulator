# FINDING — SOCO-21: the eighth mechanism-matrix shard

**Lane** SOCO-21 · **Date** 2026-09-13 · **Model** Opus `claude-opus-5` ·
**Pin** `origin/main` 33a7c961 · **Branch** `claude/soco-21-matrix-a49att` ·
**Data profile** `code` · **Solves** none (zero LP; rule 32 `[R-SHARD]` (a) is
not engaged — this lane never had a solve to shard).

A mechanical emission against a validated schema, per rule 28
`[R-MECH-MATRIX]` and `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row
SOCO-21. **ONE commit (gate G2).** **NO VERDICT MINTED** — SOCO has no keeper,
no registered run and no solve of any kind at HEAD.

---

## 1. Cell census (the EXIT deliverable)

| | count |
|---|---|
| mechanism ids in the base file | **327** |
| `U` — untested, plausibly applicable | **168** |
| `·` — structurally n/a | **159** |
| of which `mode: "F"` forecast-only rows carrying `fc: "U"` | 47 |

`159 + 168 = 327`; every base row id has exactly one cell line, which is what
gate G2 requires (a shard missing an id hard-errors). `keeper` and `gates` are
deliberately **empty strings** — the same fail-open state SPP's column carried
between SPP-21 and SPP-40, and the state
`check_mechanism_matrix.shard_keeper` / `doc_header_drift` both skip when
`frontend/data/backcast/keepers/<ISO>.json` is absent.

### 1.1 Why each `·` is a `·` — the classification rule, and its per-class count

The rule is stated in full in the shard's own header so a later lane can audit
any single cell without re-deriving the column. Applied in order:

| class | rule | `·` cells |
|---|---|---|
| **(a)** | **ISO-EXCLUSIVE ELSEWHERE** — the row names another ISO's own market object (a foreign `ScenarioConfig` field stem, or a foreign region/programme name: `wtx_` `path15_` `wecc_` `tsa_` `rdt_tcdc`) **AND** no non-owner ISO has entered the cell at HEAD. `spp_*` is foreign here too. A foreign-stemmed row some OTHER ISO HAS entered is a live cross-ISO question and reads `U` (e.g. `ercot_wind_zone_shape`, `miso_intermediate_gas_offer_margin`, `pjm_midcurve_belt`) | **100** |
| **(b)** | **NO CENTRALIZED CAPACITY MARKET** — card **S6** (ruled 2026-09-13) registers SOCO **absent** from `MARKET_DESIGN` / `_CURVE_ISOS` / `_CAPACITY_ISOS` (→ `DEFAULT_MARKET_DESIGN`, `capacity_market=False`, the ERCOT/SPP branch), adequacy carried by the IRP-cited `PLANNING_RESERVE_MARGIN_BY_ISO` scalar instead | **6** |
| **(c)** | **NO CLEARED ANCILLARY-SERVICE MARKET** — card **S5** (ruled): SOCO takes no offers; it clears no AS market, publishes no reserve demand curve, has no reserve clearing price, and registers `co_opt=False` | **4** |
| **(d)** | **NO SCARCITY PRICING / NO OFFER CAP** — card **S5**, verbatim: *"No ORDC, no scarcity seed"*; there is no market to cap | **1** |
| **(e)** | **NO CARBON PROGRAMME** — no state in AL/GA/MS carries RGGI or a cap-and-trade, and the registration is carbon-`None` by gate **G7**'s own `test_iso_coverage` sweep | **1** |
| **(F)** | **FORECAST-ONLY ROW** (`mode: "F"`) — a forecast mechanism has no backcast posture, so `cell: "."` + `fc: "U"`. SOCO has no forecast-lane entry at HEAD: that is W6, routed to the capx director (card **S10**) | **47** |

Class (b): `capacity_market_clearing`, `capacity_market_supply_clearing`,
`capacity_going_forward_bar_published`, `capacity_no_default_cap_convention`,
`net_cone_forward_vintages`, `locality_capacity_curves` — the identical six SPP
placed under its own energy-only reason.
Class (c): `energy_reserve_coopt`, `reserve_pergen`,
`dynamic_reserve_requirements`, `reserve_deliverability_scoping`.
Class (d): `ordc_scarcity_overlay`. Class (e): `state_carbon_pricing`.

Rule (a) was not asserted — it was **validated against SPP's committed column
before it was used**: applied to SPP (with SPP's own six foreign stems) it
reproduces SPP's `·`/`U` split on every foreign-stemmed row at HEAD, **0
mismatches**. That is what licenses it as a mechanical rule rather than this
lane's reading.

**`·` is the STRONGER claim** — it forecloses a lever — so every row this
session could not place with a stated structural reason fell through to `U`, the
weaker one. Rows whose applicability is genuinely open and therefore deliberately
`U`: `capacity_deliverability`, `reserve_margin_backstop`,
`adequacy_internal_supply_accounting`, `lcr_tsl_published`, `legacy_p2`,
`mass_cap_lp_row`, `m2m_seam_entitlement_cap`, `online_capacity_envelope`,
`measured_ramp_capability`, and the two reserve **sidecar** rows
(`reserve_family_sidecar`, `reserve_family_dual_sidecar` — CROSS-ISO INSTRUMENT
rows for write-only bundle artifacts every run emits, so the object exists for
SOCO even when empty; what it holds is SOCO-40's to measure, not this lane's to
foreclose).

---

## 2. TWO OF THE CHARTER'S FOUR `·` REASONS PRODUCE NO `·` CELL — stated, not buried

The charter names four n/a reasons: *no capacity market, no import node, no
reserve co-optimisation, no offer-curve tuning channel*. Two of them
(capacity market → class (b), reserve co-optimisation → class (c)) produce `·`
cells as written. **The other two do not**, because the charter's own test is
"structurally n/a for SOCO" and neither meets it. Both are recorded at full
strength on the affected rows' `ev` instead, with the cell at `U`:

- **NO IMPORT NODE** (gate **G7** — neither `IMPORT_TRANCHES["SOCO"]` nor
  `IMPORT_ZONE["SOCO"]`, so `build_import_generators("SOCO") == []`) is a
  **registration fact for the first keeper**, whose seams are served measured
  EIA-930 `Total interchange` (card **S4**). The *same* ruling registers priced
  `NeighborInterface`s (TVA, MISO-South, Duke/CPLE, the Florida BAs, Santee
  Cooper) **default-off as lever SOCO-56**. Marking these `·` would foreclose a
  chartered lever. **Six rows read `U` carrying the G7 fact**:
  `priced_interchange`, `reference_price_interface`, `import_hub_pricing`,
  `import_shape_lever`, `seam_neighbour_anchored_ladder`,
  `seam_neighbour_hourly_ladder`.
- **NO OFFER-CURVE TUNING CHANNEL** (gate **G5** — the rule 1 `[R-STRUCT]` /
  rule 13 `[R-MEASURED]` carve-out authorizes tuning MARKET OFFERS and SOCO
  takes none, so the bands stay 1.0 *unless the owner rules otherwise*) closes
  the **authorized price-tuning channel**, not the row's object. SOCO's first
  keeper will carry per-class band curves at neutral 1.0, and the duty-role
  cohort splits and econ-ramp shape anchor registered on that row under rule
  28(c) are live SOCO questions. `·` would claim there is no SOCO object, which
  is false. **One row reads `U` carrying the G5 fact**: `offer_curve_by_group`.

If the desk wants either of these as a hard `·`, it is a one-line change to the
shard and this section is the record of why it was not taken unilaterally.

---

## 3. Checker output (gate G15 — the OUTPUT, not the exit code)

`python3 scripts/check_mechanism_matrix.py`, run at the rebased tip immediately
before the commit:

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

`0 ::error` lines. **257 `::warning` lines, every one a pre-existing stale line
anchor** in the base file, of the form *"row `X` anchors scenarios.py:N but its
field is defined at …:M"*. They are not this commit's: measured directly, the
same three anchor legs run over **HEAD's** base + seven shards also return
**257 unresolvable beyond the ratchet**, and `SOCO.js` contains **zero** anchor
tokens (`grep -cE "\.py:[0-9]+|[a-z][a-z0-9_]{3,} :[0-9]+"` → `0`). The anchor
ratchet baseline is untouched. Per the checker's own blame rule they belong to
whoever last moved `scenarios.py`, and digit drift does not decide this job's
exit code.

Tests (`uv run python -m pytest`), all green:

```
tests/unit/config/test_mechanism_matrix_keeper_stamp.py
tests/unit/config/test_mechanism_matrix_shard_migration.py     13 passed
tests/unit/config/test_mechanism_matrix_shared_ratchet.py      20 passed
```

`scripts/mechanism_matrix_gap_sweep.py` (read-only, no `--write-baseline`) runs
clean against the 8-ISO store.

---

## 4. What landed — ONE commit

| file | change |
|---|---|
| `docs/codebase-site/data/mechanism-matrix/SOCO.js` | **NEW** (452 lines): the eighth shard — 327 cell lines, `iso: "SOCO"`, `updated: "2026-09-13"`, empty `keeper`/`gates`, and a header carrying the classification rule, the S1/S4/S5/S6 rulings it rests on, and §2's two exceptions |
| `docs/codebase-site/data/mechanism-matrix.js` | base `isos:` gains `"SOCO"` (eighth position) |
| `scripts/lib/mech_matrix.py` | `ISO_ORDER` gains `"SOCO"`; `ISO_EV_KEY["SOCO"] = "O"` (card **S1**; `"S"` is SPP's) |
| `docs/codebase-site/data/mechanism-matrix-assemble.js` | browser twin's `EV_KEY` gains `SOCO: 'O'` — **required**, `test_python_and_browser_assemblers_stay_in_sync` asserts the two maps agree |
| `docs/codebase-site/mechanism-matrix.html` | `<script src="data/mechanism-matrix/SOCO.js">` tag (the page renders columns from `M.isos`, so nothing else there is ISO-literal) |
| `tests/unit/config/test_mechanism_matrix_keeper_stamp.py` | `ISOS` tuple gains `"SOCO"` + the seeded-before-keeper comment |
| `tests/unit/config/test_mechanism_matrix_shard_migration.py` | comments only (the frozen six-ISO fixture pin is untouched) |
| `docs/codebase-site/css/shared.css` | `--iso-soco: #6366F1` + `.badge--iso-soco` + `.iso-btn.active--soco`, on the `--iso-spp` precedent |
| `docs/codebase-site/js/backcast-runs.js` | `ISO_COLORS.SOCO` |
| `docs/codebase-site/js/chart-utils.js` | `soco`/`SOCO` → `cssColor('--iso-soco')`, the same precedent (without it SOCO renders in the generic fallback colour in every d3 chart) |
| `docs/mechanism-testing-matrix.md` | **§5.8 SOCO lever queue** (the charter's ONE granted exception to §8.0 rule 1) + the §5.8→§5.9 renumber in §4 |
| `docs/handoffs/FINDING-soco-21-2026-09-13.md` | this file |

The §5.8 queue is seeded verbatim from the plan's W5 list — **SOCO-54**
inter-OpCo TTC derive (card S3), **SOCO-55** VOLL/adequacy (cards S5/S6),
**SOCO-56** priced seams (card S4), **SOCO-57** CAES/PS representation (card S7)
— each naming the object it must derive from SOCO's own data, and none naming a
gate it has moved, because none has been tested. It states in place that it is
issued against a keeper that does not exist yet (SOCO-40) and is a prior, not a
mandate.

---

## 5. Five things to report to the desk

1. **§5.8 WAS ALREADY TAKEN.** `docs/mechanism-testing-matrix.md` §5.8 was
   *"Cross-cutting audits (not ISO levers)"*. Since §5.1–§5.7 are the seven ISOs
   and the charter directs SOCO to §5.8, the cross-cutting section is
   **renumbered to §5.9** and the one internal cross-reference to it (§4 item 4,
   *"no ISO's keeper consumes a stale outage-derived artifact"*) is updated in
   place with a note saying why. No cross-reference anywhere else in the repo
   cites that section by number (swept: `*.md`, `*.py`, `*.js`). This is the
   only text in that file outside §5.8 that this lane touched, and it is a
   mechanical consequence of the instruction, not a substantive edit. **No other
   ISO's §5.x prose header was touched.**
2. **SPP's §5.x prose header is NOT drifted at this pin** — contrary to the
   charter's note. `check_mechanism_matrix.doc_header_drift` reports
   *"§5.x prose headers match every keepers/<ISO>.json"* for all seven, and §5.7
   names `2026-09-13-spp-38-vintage-cache`, which is what
   `frontend/data/backcast/keepers/SPP.json` designates. The SPP-38 promotion
   (2026-09-13) evidently re-stamped it after the charter was written. Nothing
   for the SPP desk to do; reported because the charter asked.
3. **The charter cited the wrong test for the "expected set".** It names
   `tests/unit/config/test_mechanism_matrix_shard_migration.py`, whose only ISO
   literal is the **frozen pre-shard fixture's six** (deliberately pinned
   literally, and correctly left alone) — it would have stayed green untouched.
   The set that would actually have failed is
   `tests/unit/config/test_mechanism_matrix_keeper_stamp.py`'s `ISOS` tuple,
   which is asserted against both `matrix_isos(...)` and the shard-stamp key
   set. Both files are updated; the first for its comments only.
4. **`check_mechanism_matrix.N_ISOS = 6` is dead and now wrong by two.** It is
   defined at line 109 and referenced nowhere (`grep -rn N_ISOS scripts/ tests/`
   → the definition only). SPP-21 left it at 6 and so did this lane: it decides
   nothing, and deleting it is a `check_mechanism_matrix.py` edit outside this
   charter's named scope. Flagged for whoever owns that file — rule 26
   `[R-DELETE]` argues for removing it rather than re-valuing it.
5. **`mech_matrix.ISO_FIELD_STEMS` has no `SOCO` entry, on purpose.** The
   charter names `ISO_ORDER` and `ISO_EV_KEY` only, and there is **no `soco_*`
   `ScenarioConfig` field at HEAD** (`grep -c '^    soco_' scenarios.py` → `0`),
   so the three gap ratchets are byte-identical either way today. The moment
   **SOCO-20** (or any later lane) adds one, that field will be read as *shared*
   rather than SOCO-scoped and the `absent_shared` ratchet will go red until its
   row lands — so the stem belongs in the same PR as the first `soco_*` field.
   Named here so it is a handoff, not a trap.

---

## 6. Scope discipline

- **No other ISO's shard was opened for writing**; no cell verdict outside
  SOCO's new column exists in this diff (the other seven shards are untouched —
  `git diff --stat` shows them absent).
- **`src/` untouched. `frontend/data/**` untouched.** No registry, no keeper
  shard, no run payload.
- **No verdict was transferred** (rule 25 `[R-ISO-SCOPE]` / rule 28(d)). SPP's
  `R` on `priced_interchange` / `reference_price_interface`, and every other
  ISO's `K`, enter SOCO's column as `U` or as a reasoned `·`, never as an
  inherited verdict.
- **Rule 28(c) is not engaged**: this commit adds no `ScenarioConfig` field and
  no calibration CLI flag.
- Collision protocol followed: rebased onto `origin/main` immediately before the
  commit, checker re-run at the rebased tip, then pushed.
