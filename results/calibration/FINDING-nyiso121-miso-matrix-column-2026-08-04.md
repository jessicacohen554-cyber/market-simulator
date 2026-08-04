# FINDING — nyiso-121 (TASK 2): MISO's rule-28(c) matrix column is CLOSED

**Date:** 2026-08-04 · **Session:** nyiso-121 (NYISO lane, cross-ISO column work) ·
**Target column:** MISO · **MISO keeper:** `2026-08-04-miso-122b-scope-gate`, **unchanged**
**NYISO keeper:** `2026-08-03-nyiso-119-seny-increment`, **unchanged**
**Pre-registration:** `PREREG-nyiso121-miso-matrix-column-2026-08-04.md` — committed and
pushed **before** any row was written and before the probe was run.

**Zero solves. Zero years touched. No `ScenarioConfig` value, constant or derive script
changed.**

> **Session renumbered nyiso-120 → nyiso-121, recorded not silent.** This session opened as
> nyiso-120; a concurrent NYISO session (the East River hybrid-cogen scope gate) merged to
> main first and spent that label — itself having renumbered off nyiso-119 for the same
> reason. No pre-registered content changed; see PREREG's header note and commit `9b3fe469`,
> the timestamped record that the pre-registration preceded the work.
>
> **Rebased onto `origin/main` at `f3a1e817` after the work was done.** Two main-side changes
> are attributed here so they are not read as this session's: (a) `pjm-152` collapsed
> `pjm_seam_envelope_by_neighbor` under rule 26 `[R-DELETE]`, which is why **PJM's family
> count moves 36 → 35** in §7's criterion-4 table — main's deletion, not this census's doing;
> and (b) that same deletion **fixes two `tests/scoring/test_forecast_parity.py` failures that
> were red on this session's pre-rebase base** (`pjm_seam_envelope_by_neighbor` armed in the
> PJM keeper with no forecast consumer) — pre-existing, PJM's, and cleared by the rebase.
> The only conflict was `seam_flow_envelopes`' `def:` line, which `pjm-152` also edited;
> it was resolved by taking **main's** line and re-applying this session's isolated 3,693-char
> MISO insertion onto it, verified by exact length delta.

---

## §1 — headline

**MISO was the LAST ISO with an open own-family column, and it is now closed.** All **8
absent + 4 prose-only** `miso_*` fields — **7 of them ARMED on the published keeper with no
cell anywhere**, the 227-3 shape — are registered as **LITERAL sub-scalar entries on 7
EXISTING family rows**.

| metric | before | after |
|---|---|---|
| MISO family fields | 25 | 25 |
| absent from matrix | **8** | **0** |
| prose-only | **4** | **0** |
| ARMED-on-keeper, no cell | **7** | **0** |
| matrix rows | 169 | **169** (zero new rows) |
| ratchet baseline MISO | 8 | **0** |

With ERCOT (`ercot-156`), CAISO (`caiso-161`), NEISO (`neiso-78`), PJM (`pjm-151`) and
NYISO (`nyiso-113`) already closed, **every ISO's own-family column is now closed** and the
six-lane backlog `nyiso-113/114` measured — **161 absent, 95 armed-but-cell-less** — is
fully discharged.

## §2 — why this session, and why MISO (measured, not assumed)

NYISO's column and lever queue are **exhausted**: `--iso NYISO` re-confirms **41 family / 0
/ 0 / 0 / 0**, sole exclusion the declared `weather_year`. TASK 1's two lanes are both
owner-gated — (a) the compressed peak-half distribution is route-exhausted at nyiso-110 and
**pending an owner amplitude-criterion call**; (b) C3c's re-open condition is a
`Capital_Hudson` → Zone-F/Zone-G **topology split** needing its own owner charter. Neither
was re-opened. The SENY curve lane stays **CLOSED**.

**The handoff's counts were stale and the sweep was re-run rather than trusted.** PJM's
own-family column had since been closed by `pjm-151` (15 absent → 0), so "MISO and PJM are
the worst columns" resolved to **MISO alone**:

| ISO | family | absent | prose | armed-no-cell | shared-gap | invisible |
|---|---|---|---|---|---|---|
| ERCOT | 84 | 0 | 0 | 0 | 14 | 12 |
| CAISO | 61 | 0 | 0 | 0 | 5 | 1 |
| **MISO** | **25** | **8** | **4** | **7** | 17 | 18 |
| NEISO | 20 | 0 | 0 | 0 | 0 | 0 |
| NYISO | 41 | 0 | 0 | 0 | 0 | 0 |
| PJM | 36 | 0 | 0 | 0 | 18 | 0 |

## §3 — the registrations: 12 fields, 7 existing rows, zero new rows

Each home is chosen on a **code-level dependency**, not on theme.

| # | field | keeper | home row | why that row |
|---|---|---|---|---|
| 1 | `miso_zonal_reserves` :4660 | **True** | `energy_reserve_coopt` | states "Requires `energy_reserve_coopt`" |
| 2 | `miso_zonal_reserve_zones` :4677 | None | `energy_reserve_coopt` | zone-set override of #1 |
| 3 | `miso_midwest_subregional_reserves` :4681 | **True** | `energy_reserve_coopt` | states "Requires `energy_reserve_coopt`" |
| 4 | `miso_rpe_pricing` :4814 | **True** | `rdt_tcdc` | "Requires `miso_rdt_tcdc` (fails loud otherwise)" |
| 5 | `miso_seam_envelope_merit_cap` :3820 | **True** | `seam_flow_envelopes` | composes through `inject_miso_seam_flow_limit` |
| 6 | `miso_manitoba_seam` :3911 | **True** | `seam_flow_envelopes` | same injector; **was mis-homed** |
| 7 | `miso_south_seam_split` :4785 | **True** | `seam_flow_envelopes` | hosts the South seam's bands |
| 8 | `miso_pjm_border_anchor` :3789 | **True** | `import_hub_pricing` | re-anchors the PJM neighbour price |
| 9 | `miso_pjm_lmp_import_pricing` :3872 | False | `import_hub_pricing` | prices the PJM seam at measured hub LMP |
| 10 | `miso_firm_import_floor` :3841 | False | `reference_price_interface` | floor on the reference-price seam |
| 11 | `miso_cc_coal_rebalance` :3859 | False | `diurnal_price_amplitude` | the only row that ever named it |
| 12 | `miso_native_outage_source` :9576 | False | `campd_outage_windows` | the `ercot_noncampd_*` shape |

**ONE cell mint, an AUDIT STATUS and not a mechanism verdict:** `matrix_gap_census` MISO
**`O` → `K`** — the `ercot-156` / `caiso-161` / `pjm-151` precedent.

**ZERO mechanism verdicts.** Every verdict-bearing sentence added **transcribes** an
adjudication already on the record, with its citation, exactly as pre-registered in
PREREG §3 K-3 (so anything beyond them would have been visible as a breach):

* `miso_firm_import_floor` — **REJECTED as an outcome pin (rule 13 `[R-MEASURED]`)**;
  miso-114, and independently `miso_seam_measured_ladder`'s own code comment.
* `miso_pjm_lmp_import_pricing` — **REFUTED EX ANTE on MISO's own data** for the seam
  hour-of-day defect, and must not be armed for it; miso-114.
* `miso_cc_coal_rebalance` — **LICENSED BY NOTHING**: its target is defined against another
  *model* quantity with no measured identification (rules 5/21/24), and miso-115 §2
  **removes its stated premise** by measurement.
* the per-Reserve-Zone §5.2.1.2 **Zonal ORDC ladder is MEASURED-REFUTED** (never separated
  in 26,280 h), which is why `miso_midwest_subregional_reserves` deliberately does not use
  it; miso-71 design §1b/§2a.

**No never-adjudicated armable candidate was surfaced.** All three default-off MISO fields
carry standing refusals, so this census did **not** manufacture a successor for MISO's
queue — unlike `caiso-161`, which surfaced two.

## §4 — mechanical cause: the same defect a third time, plus a NEW variant

`import_hub_pricing`'s def carried the fragment **`miso_pjm_lmp :2914`**. That is
`caiso-161` §2's abbreviation defect **and** a stale anchor:

* `miso_pjm_lmp` **is not a `ScenarioConfig` field**, so a checker matching literals could
  never see it;
* `scenarios.py:2914` is an unrelated **over-generation-repricing** comment block. The real
  field is `miso_pjm_lmp_import_pricing` at **:3872**.

That one fragment accounts for **two of the twelve gaps** — exactly as `pjm_seam_* :7371+`
did for PJM and the `_intercept` short form did for CAISO.

**A NEW variant, worth recording because no checker looks for it.**
`miso_manitoba_seam` — **ARMED on the keeper** — was prose-only inside the
**`diagnostics_plant_set`** row, a row about *probe plant sets*. **A mention on the WRONG
family row is as invisible as no mention**, and unlike a glob or a stale anchor **it reads
as correct coverage to a human auditor**. Globs and stale anchors are mechanically
detectable; this is not.

## §5 — G-1: `miso_pjm_border_anchor` is PROVABLY UNOBSERVABLE on the keeper

Pre-registered in PREREG §4 as observation **O-1**, with PASS / FAIL / UNINFORMATIVE and a
**mandatory positive control** all specified before the probe ran.

**Written on CONSTRUCTION, not on a solved dual** — the binding lesson of nyiso-115 G2 and
nyiso-118 (a scope question gated on a solved dual can only pass when the mechanism does
nothing, and a provably-unchanged construction can still move its dual through general
equilibrium). **No LP, no solve, no dual.**

The keeper arms **both** `miso_pjm_border_anchor` and `miso_seam_measured_ladder`. The
ladder **runs LAST** among the seam price overwrites and displaces the anchor on any row it
covers, and `MISO_SEAM_LADDER_BY_YEAR` carries a full **8-band import + 8-band export PJM
entry in all three keeper years**.

Built twice at one HEAD, ladder **ON in both arms**:

| year | seam rows | PJM rows | all rows exactly equal | max abs Δ |
|---|---|---|---|---|
| 2023 | 48 | 16 | **yes** | **0.0** |
| 2024 | 48 | 16 | **yes** | **0.0** |
| 2025 | 48 | 16 | **yes** | **0.0** |

`np.array_equal` on float32 — **exact equality, not a tolerance** (a 1e-6 tolerance is
unsatisfiable in principle on these columns; nyiso-116 G3/P4).

**The positive control SEPARATES, so the silence is the mechanism's and not the
instrument's.** With the ladder **OFF**, the anchor moves the 16 PJM band rows by
**$0.92 / $2.23 / $4.78** and leaves **SPP/South exactly untouched** — confirming it is
live, correctly wired, and PJM-scoped.

**G-1 PASS.** This is the `caiso-161` §5 / `pjm-151` armed-looking-but-dead shape: a MISO
`run_config.json` **overstates** what the solve did.

**A SECOND, weaker instance, filed as an observation:** the keeper arms `miso_firm_imports`
alongside `miso_manitoba_seam`, and `interchange/spec.py:1757-1763` **drops the MHEB firm
block** when the Manitoba seam is set, so `inject_miso_firm_imports` no-ops.

**Neither is a rule 26 `[R-DELETE]` candidate** — both are built, reachable, default-off
mechanisms at their documented defaults, displaced by **documented alternatives** rather
than a retired mechanism's fitted residue. Whether arming both halves of an either/or pair
is cosmetic or a rule 19 `[R-ONE-MECH]` question **belongs to a lane that may adjudicate
MISO. A census may not** (rule 28(d)). **No cell moved on either.**

## §6 — two pre-registered checks that FIRED, recorded rather than redefined

Following nyiso-115 G2, nyiso-117 G2a and nyiso-119 G4: a pre-registered statement that
fails is **recorded**, never quietly rewritten.

### §6.1 — criterion 3's predicted cells string was WRONG

PREREG §7 criterion 3 predicted `matrix_gap_census` would go **`KKKOKO` → `KKKKKK`**. That
assumed **NEISO's** audit cell was already `K`, because NEISO's own-family sweep reads
20/0/0/0 and its column was closed by commit `12cca41d`. **It is not** — NEISO's
audit-status cell is still `O`, and minting it is **NEISO's lane's call, not this
session's** (rules 25 / 28(d)). Only index 3 moves: **`KKKOKO` → `KKKKKO`**.

### §6.2 — criterion 4 CAUGHT A REAL CROSS-COLUMN LEAK IN THIS SESSION'S OWN FIRST DRAFT

This is the substantive methodological result, and it is a **correction to the precedent
this row itself set**.

A first draft of the census note **enumerated MISO's 17 shared-stem literals**, following
`ercot-156` / `caiso-161` / `pjm-151`, which each list theirs. Criterion 4 — *the five other
ISOs' counts must not move* — then **failed**: **ERCOT went 12 → 11**. One field
(shared, armed on **both** the MISO and ERCOT keepers, and visible on ERCOT's list only
because `ercot-156` happened to write an abbreviated stem for it rather than the literal)
**silently vanished from ERCOT's live-but-invisible list with no ERCOT session having
registered anything.**

**Naming a shared field as a bare literal makes the sweep count it MENTIONED — which is
precisely the "a mention is not a registration" defect this whole census exists to close —
and it leaks ACROSS columns**: one lane's prose drops a field from *both* lanes' lists.

The enumeration was **withdrawn** for a **count plus a pointer to the committed,
machine-readable `_matrix_gap_sweep_<ISO>.json`**, so nothing is hidden. After that, all
five other ISOs' counts are **byte-unchanged**.

**It fired twice.** The first correction still named the field *while explaining the
defect*, which re-committed it and held ERCOT at 11. The literal had to be removed a second
time — from the explanation itself. That is recorded in the row.

**Consequence for the precedent, stated plainly:** the enumerated lists `ercot-156`,
`caiso-161` and `pjm-151` left in that note are **prose, not registrations**, and any lane
should trust `_matrix_gap_sweep_<ISO>.json` over the row's text.

## §7 — verification (all five pre-registered success criteria)

| # | criterion | result |
|---|---|---|
| 1 | MISO sweep 25 family / 0 / 0 / 0 | **PASS** |
| 2 | `check_mechanism_matrix.py` passes | **PASS** — integrity OK, keeper stamps match |
| 3 | every `cells:` byte-identical except `matrix_gap_census` | **PASS** — sole change `KKKOKO` → `KKKKKO`; 169 → 169 rows, **0 new**; predicted string corrected (§6.1) |
| 4 | five other ISOs' counts unchanged | **PASS after the §6.2 correction** — CAISO 61/0/0/0/5/1, ERCOT 84/0/0/0/14/12, NEISO 20/0/0/0/0/0, NYISO 41/0/0/0/0/0, PJM 36/0/0/0/18/0 |
| 5 | G-1 reported with its positive control | **PASS** — §5 |

Kills K-1 (zero mechanism-cell changes), K-2 (one audit mint), K-3 (transcription only) and
K-4 (no re-derivation, no solve, no-tuning clause) all hold.

**Rule 27 `[R-PUSH]`:** `mechanism-matrix.js` is **2,014 lines**; it was edited locally with
the Edit tool, pushed as exact on-disk bytes, and the pushed blob **verified byte-identical**
(2,014 lines, 746,282 bytes, sha256 `5888cb4a…4828c`) before any further commit.

## §8 — what this session did NOT do

* **No MISO lever was tested, chartered or queued**, and no MISO cell verdict was minted.
* **The 17 shared-stem fields MISO's keeper arms invisibly** — overlapping PJM's 18 and
  ERCOT's 14 — **stay open**, filed for a cross-ISO hygiene lane. One column's session does
  not close them.
* **NYISO's keeper, gates, determination and `calibration-complete.json` entry are
  UNTOUCHED.** No promotion was made in any ISO, so rule 22 D-5(b) does not fire and no
  determination re-verification is owed.
* **The holdout spend freeze is ACTIVE and untouched.** No year outside 2023–2025 was
  solved, scored or read; no year was solved at all.

## §9 — the named successor

**The cross-ISO shared-stem backlog is now the ONLY remaining rule-28(c) debt** — PJM 18,
MISO 17, ERCOT 14, CAISO 5, all overlapping, all armed on keepers with no cell anywhere.
With every ISO-family column closed it is the natural next target, and §6.2 is a
prerequisite finding for it: **that lane must register these fields on rows, not enumerate
them in prose**, or it will hide the very backlog it is closing.
