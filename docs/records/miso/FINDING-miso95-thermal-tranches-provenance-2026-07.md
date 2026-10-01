# miso-95 — LANE 1 STAGE 1: `thermal_tranches_MISO.csv` does not reproduce, and **neither does any other ISO's**. STAGE 2 is NOT entered.

**Determination: `PROVENANCE-BLOCKED — NO ADOPTION, NO A/B, NO SOLVE.`**

The miso-94 handoff pre-registered the decision rule verbatim: *"If STAGE 1
cannot be closed, REPORT THAT AND STOP (rule 24) — a non-reproducing artifact is
a provenance finding, not a licence to adopt."* It could not be closed. No LP was
launched, no bundle was produced, so there is nothing to register (rule 15 has no
subject this session) and the MISO keeper `2026-07-25-miso-88-egrid-hr` is
untouched.

What the session *did* produce is larger than the MISO cell it was scoped to:
**all five committed `thermal_tranches_<ISO>.csv` artifacts are provenance-orphaned,
on a staleness axis miso-94 never named — the merchant-CC summer-capacity guard —
and that axis is exactly and completely reproducible.**

---

## §1 — the one axis that reproduces exactly: the merchant-CC summer-capacity guard

`derive_thermal_tranches.py::_fleet_nameplate_and_group` takes every non-ERCOT
ISO's per-plant nameplate from `load_fleet_from_csv(iso, get_iso_config(iso))` —
i.e. with `apply_cc_summer_guard` at its default **True**, the reconciliation
`fleet/eia860.py::_reconcile_cc_pmax_to_nameplate` that caps a merchant CC's
summed fleet pmax at its trusted nameplate bound ("corrupt summer-capacity rows").

**Measured: the committed artifacts were derived with that guard OFF.** Re-deriving
with `apply_cc_summer_guard=False` monkeypatched onto both `fleet.eia860` and
`fleet` (and `_iso_plant_capacity.cache_clear()`, so the outage-derate denominator
follows) makes `nameplate_mw` match **exactly, on every row, in every ISO**:

| ISO | rows | `nameplate_mw` matching the GUARDED (model) fleet | matching the UN-GUARDED fleet only | neither |
|---|---|---|---|---|
| MISO | 282 | 276 | **6** | 0 |
| PJM | 256 | 251 | **5** | 0 |
| CAISO | 156 | 154 | **2** | 0 |
| NYISO | 78 | 75 | **3** | 0 |
| NEISO | 76 | 74 | **2** | 0 |

The 18 exceptions are precisely the 18 CC plants the guard reconciles. Nothing
else in the fleet moved: 842 of 848 rows already agree, and the 6/5/2/3/2 that
disagree agree to the cent with the un-guarded fleet. This is a **code** change,
not a source-data change — outside rule 23 `[R-FROZEN-DERIVE]`'s re-derivation
trigger, which is why nothing re-derived when the guard landed.

### Why it is a live defect, not a curiosity

`committed_pct` / `mustrun_pct` / `p25_cf` are **ratios whose denominator is that
nameplate**. At runtime the model applies the derived percentage to the
**guarded** (smaller) fleet pmax. An over-stated derivation denominator therefore
understates the tranche share, and the understated share is then applied to the
already-reduced capacity — the min-stable / must-run floor MW is understated
twice over. Direction is unambiguous and one-sided: **too small, never too large.**

Order of magnitude, `(r − 1) × committed_pct × pmax_model` per plant
(r = file nameplate ÷ model nameplate):

| ISO | plants | over-stated CC nameplate in the file | understated committed floor |
|---|---|---|---|
| **MISO** | 6 | 2,479 MW | **~766 MW** |
| PJM | 5 | 887 MW | ~230 MW |
| NEISO | 2 | 378 MW | ~45 MW |
| NYISO | 3 | 152 MW | ~40 MW |
| CAISO | 2 | 31 MW | ~10 MW |
| | **18** | **3,927 MW** | **~1,090 MW** |

Worst single rows: MISO Union Power 55380 (3,456.6 file vs 2,428.0 model,
r = 1.42), Perryville 55620 (r = 1.53), Hot Spring 55418 (r = 1.34);
PJM 60302 (r = 1.49) and 55297 (r = 1.33); NEISO 60903 (r = 1.45).

This is a rule-11 `[R-ACCURATE]` / rule-1 `[R-STRUCT]` item: the accurate input
(the guarded fleet, which is what dispatch runs on) is already in the model, and
the tranche artifact is still quoting the pre-guard basis at it.

## §2 — the axes that do NOT reproduce

With the guard axis neutralized (`nameplate_mw` differs on **0** rows in every
ISO), material drift remains everywhere:

| ISO | max `online_hours` in file | `online_hours` drift | `committed_pct` drift | `p25_cf` drift | columns the committed file LACKS |
|---|---|---|---|---|---|
| MISO | 26,280 | 94 rows, max **17,378 h** | 69 rows, max 53.3 pp | 75 rows, max 133.3 | `steam_level_cf` |
| PJM | 26,280 | 103 rows, max 6,857 h | 79 rows, max 32.8 pp | 79 rows, max 27.0 | `steam_level_cf` |
| CAISO | 22,760 | 27 rows, max 323 h | 21 rows, max 20.7 pp | 23 rows, max 12.9 | — (has extra `chp_btm_pct`) |
| NYISO | 26,253 | 46 rows, max 26,271 h | 34 rows, max 27.2 pp | 29 rows, max 83.6 | `mustrun_online_pct`, `online_frac`, `steam_level_cf` |
| NEISO | 24,504 | 28 rows, max 8,087 h | 24 rows, max 46.8 pp | 24 rows, max 63.8 | `mustrun_online_pct`, `online_frac`, `steam_level_cf` |

Two independent generational tells fall straight out of the schema, before any
number is compared:

* **Only CAISO's file has `steam_level_cf`** — MISO, PJM, NYISO and NEISO all
  predate that column. (CAISO is also the only one carrying `chp_btm_pct`.)
* **NYISO and NEISO additionally lack `mustrun_online_pct` and `online_frac`** —
  they predate the coal online-Pmin work
  (`docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md`) that added
  them. Those two artifacts are at least one generation older than MISO's and
  PJM's; CAISO's is the *newest* on schema (it alone has `steam_level_cf`) but
  sits on a different year window entirely (max `online_hours` 22,760 ≪ 26,280
  ⇒ a shorter/partial span, consistent with the deriver docstring's CAISO P2
  note), which is why its drift is the smallest of the five.

The standing check for all of this is
`scripts/probes/miso95_tranche_provenance_sweep.py` — a pure artifact diff, no
CAMPD read, seconds to run, re-answerable after any change to the guard or to a
committed tranche artifact.

### What was ruled out, and what the residual looks like

Four arms, all at HEAD, all over `--years 2023 2024 2025`, MISO
(`nameplate_mw` diffs shown against the committed file):

| arm | fleet guard | std outage extract | derate routing | `nameplate` diffs | max `online_hours` diff |
|---|---|---|---|---|---|
| A | ON (HEAD) | HEAD `c298c68` | per-unit (HEAD) | 6 | 17,378 |
| B | **OFF** | HEAD `c298c68` | per-unit | **0** | 17,378 |
| D | OFF | **pre-guard `f2b3ec8`** | per-unit | 0 | 17,006 |
| E | OFF | HEAD | **plant-primary group** | 0 | **3,614** |
| F | OFF | HEAD | derate disabled entirely | 0 | 21,027 |

* **The `6a8f285` merit-order guard is not the driver** (arm D moves the tail by
  372 h and closes 3 of 94 rows). The lane's original premise — that the guard
  staled the tranches file — is *true but immaterial* next to what else moved.
* **The derate was applied** when the file was derived (arm F is strictly worse
  on every column), so it is not a "derate wasn't wired yet" artifact.
* **The derate was routed differently.** Arm E — every unit-outage row routed to
  its plant's *primary* fleet group instead of to the row's own `plant_group` —
  takes Brame Energy Center 6190/COAL from 21,099 online hours to **3,288**
  against a committed **3,721**, and cuts the ISO-wide tail 17,378 → 3,614. The
  committed vintage's routing was primary-group-like; HEAD's
  `outages.py::_generic_unit_outage_target` routes per-unit off the extract's own
  `plant_group` column. Close, but **not exact** — so the extract vintage differs
  too, and the two are not separable from what is on disk.
* **The residual is small, two-signed and ubiquitous**: ±10–400 h on ~84 of MISO's
  198 `ok` rows, in every arm, on plants with no outage-family story at all
  (e.g. Whitewater +331, South Oak Creek +172, Zeeland +44). `nameplate_mw`
  matches those rows exactly, so the fleet is not the source. That signature is an
  upstream **CAMPD hourly / `parasitic_load_factors.parquet` vintage** move —
  CEMS is revised and backfilled, and a re-fetch shifts `net > 0` crossings a
  little everywhere while leaving capacities alone. It is **not reconstructible**:
  the repo is a shallow clone (304 commits, everything earlier absorbed into the
  graft), the raw parquets now span 2018–2026, and `git log` on
  `data/raw/campd-unit-level/` returns exactly one merge commit.

**Conclusion: no constructible input vintage reproduces the committed artifact,
in any ISO.** Three of the four axes are identified (CC guard — exact; outage
routing — approximate; merit-order guard — measured and immaterial); the fourth
is upstream of anything git or disk can recover here.

## §3 — why STAGE 2 is not entered

Adopting a re-derived `thermal_tranches_MISO.csv` now would move, in one blob,
at minimum: the CC-guard nameplate basis (6 plants), the outage-derate routing
(≥2 plants, ±17 k online hours), the merit-order guard delta, an unknown CAMPD
vintage step, and three new columns. That is a **five-way confounded arm** — the
caiso-123 defect that miso-93 and miso-94 were both careful to avoid — offered
against a C3a-2024 miss of 0.05 pp. Whatever it did to the residual would be
uninterpretable, and per rule 24 `[R-DOF]` an uninterpretable move is an answer
key, not a parameter. **The lane stays closed until a control reproduces.**

## §4 — what would actually unblock it (for the owner)

Ranked, cheapest first. None is in this session's scope.

1. **Retire the provenance question instead of solving it.** Re-derive all five
   `thermal_tranches_<ISO>.csv` at HEAD *on purpose*, as a declared
   re-baselining, and A/B each ISO against its own keeper as a normal registered
   arm. This does not recover the old vintage — it makes the artifact
   reproducible **going forward**, which is what rule 23 actually wants. It is
   five separate ISO lanes and five registered bundles, not a MISO chore.
2. **Isolate the CC-guard axis alone**, by re-deriving with the guard OFF (arm B
   above — already produced and byte-stable) and adopting *only* the six/five/…
   guarded plants' rows. That is a genuinely single-delta arm with a known sign
   (floors go **up** by ~766 MW in MISO) and it is the only sub-axis here that is
   cleanly separable today.
3. **Pin the CAMPD vintage.** Nothing in the repo records which CEMS snapshot a
   derived artifact was built from. A `campd_vintage` provenance stamp
   (fetch date + per-file hash) written into every derived artifact's header
   would have answered this session in one `head -1`. This is the governance fix,
   and it generalizes past the tranche family.

## §5 — cross-ISO exposure, now measured (LANE 2, partially closed)

miso-94 flagged that `6a8f285` adopted the merit-order guard for all six ISOs and
re-derived no downstream artifact for any of them. Confirmed and itemized:

* `6a8f285` removed rows from **every** ISO's std extract — MISO −2,424, PJM
  −3,246, NYISO −3,037, NEISO −1,294, CAISO −810, ERCOT −3,484 (moved to the
  `-layup-` companions, which no loader reads).
* **Consumers of the std extract, by artifact:**
  * `thermal_tranches_<ISO>.csv` — **all five ISOs, all stale** (§2), and stale on
    the CC-guard axis too (§1). *This is the new finding.*
  * `campd-unit-outages-short-<ISO>.csv` — exists for MISO and PJM.
    `derive_campd_unit_outages.py:1042` reads the std extract via
    `_load_standard_windows(unit_outage_csv_for_iso(iso))`, so both are downstream.
    **MISO's was re-derived and adopted in miso-94; PJM's has not been touched** —
    it is stale, and it feeds `unit_outage_short_windows`.
  * `campd-unit-outages-maxgen-MISO.csv` — MISO only; re-derived in miso-94.
* **Solve-side exposure is separately covered** and should not be re-run: PJM
  re-audited its keeper on the guard-corrected envelope in **pjm-129**
  (`CALIBRATED` → `NOT-YET`, three gates, guard owns 100 % of the −$0.518 move),
  and MISO in miso-93/94. The residue here is the *artifact* re-derives, not the
  solve exposure.

**Highest-value un-actioned item in this family: `campd-unit-outages-short-PJM.csv`.**
It is a one-command re-derive with a live consumer and, unlike the tranche files,
its MISO twin's control **passed** in miso-94 — so a clean single-delta A/B is
available on it today.

## §6 — pre-registration honesty

No mechanism was proposed and no magnitude was pre-registered, because the
handoff's STAGE 1 is a measurement with a binary pre-registered outcome
(reproduces / does not) and STAGE 2 was never reached. Two things the session got
wrong on the way and is recording rather than narrating as foreseen:

* The lane was scoped, by miso-94 and by this session's first hour, as *"the
  `6a8f285` guard staled the tranches file."* That framing is **wrong by an order
  of magnitude** — the guard accounts for 3 of 94 drifting rows and 372 of 17,378
  drifting hours. The dominant axes (CC summer guard, outage routing, CAMPD
  vintage) were all invisible to it.
* The first hypothesis chased for the `online_hours` tail was an availability
  effect. It cannot be one: `online = net > 0.05 × nameplate × derate`, so no
  derate can push a plant *below* its no-derate online count, yet Brame's
  committed 3,721 sits far below its no-derate 24,748. Only a re-routing (which
  changes which rows land on the group, and zeroes it) can. Half an hour was
  spent before that arithmetic was checked.

## §7 — hygiene

Every input swap was hash-verified in both directions (rule: single-delta input
probe protocol). The pre-guard std blob was mounted once and restored:
`f2b3ec8e4f2920bccf9d64200b1635cc42d223a9` → `c298c6801d8f93c99a762749b01fabe829f92bc4`,
verified equal to `git rev-parse HEAD:data/raw/campd-unit-outages-MISO.csv`. All
arms wrote to `/tmp`; **no artifact under `data/` was modified by this session.**
Rule 22 honoured — every derive ran `--years 2023 2024 2025` only; MISO still has
no calibration-complete marker and `holdout-freeze.json` is active.
