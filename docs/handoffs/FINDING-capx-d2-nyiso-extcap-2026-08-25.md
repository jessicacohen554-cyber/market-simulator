# FINDING — NYISO external-capacity accreditation intake (capx D-2 successor)

**Session:** capx D-2 NYISO-EXTCAP-INTAKE (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-25 · **Branch:** `claude/capx-d2-nyiso-extcap-intake-sewmyx`
**Charter:** execute the pre-stated successor of
`FINDING-capx-d2-adequacy-nyiso-2026-08-24.md` §6 — source NYISO's *published*
external-capacity accreditation and add NYISO to `ADEQUACY_EXTERNAL_TIE_FIRM_MW`
on the FF-2B construction, never a number tuned to the invariant.

---

## 0. Headline

**Sourced and shipped: `ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"] = 3,168.5 × (1 − 0.1321)
= 2,749.9 MW UCAP**, from the 2026 Gold Book Table V-1 (Summer 2026 net capacity
purchases from external control areas) converted with the same published NYCA
ICAP→UCAP translation factor the requirement side already applies.

**I7 now PASSES for NYISO — all five T1-F years, and the whole FC-1 battery with
it: the re-scored leg reads 14/14 invariants PASS, FC-2 PASS (I12 in-band, no
backstop caveat), determination HOLD → PROMOTE-WITH-CAVEATS** (the remaining
caveat is FC-7's program-wide missing DOF-ledger instrument, not this lane's).
**Honesty test: the value overshoots the adjudicated 35.7 MW gap by ~77× —
inside the pre-declared O(10²–10³) band, not suspiciously close.** One
honesty-critical decomposition is reported in §4: the demand path at this HEAD
had already drifted the 2026 peak down 341.4 MW since the FFR-3A-2 epoch, which
alone would have flipped I7's 2026 leg by a thin +333 MW — the intake is what
moves the position from marginal-by-drift to structurally held (+3,083 MW).

---

## 1. The sourced value and its citation chain

| quantity | value | source |
|---|---:|---|
| Summer 2026 net capacity purchases, total | **3,168.5 MW** (ICAP) | 2026 Gold Book, Table V-1 (p. 140) |
| — ISO-NE | 67.3 | same table |
| — Hydro-Québec | 2,443.0 | same table (incl. CHPE availability per its note 4) |
| — IESO (Ontario) | 3.3 | same table |
| — PJM | 654.9 | same table |
| NYCA ICAP→UCAP translation factor | 1 − 0.1321 = 0.8679 | NYSRC 2025-2026 IRM Study Technical Appendices, App. D Table D.2 (already intaken: `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv`) |
| **registry entry (UCAP)** | **2,749.9 MW** | product of the two published operands |

**Primary source identity.** `data/raw/NYISO/2026-Gold-Book-Public.pdf` (April
2026, 166 pp) was re-fetched from the README-verified URL
(`https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf`) and
verified **byte-identical** to the committed provenance record: sha256
`43865c1cbe38ca2ef4c8319d11454881de2b9dde3e48867dbbd2e94855b908bf`, 2,666,002
bytes, exactly as `data/raw/NYISO/SHA256SUMS.txt` records. The payload itself
stays gitignored (BLOAT-B-2 corpus conversion); the README's Gold-Book bullet
now names Table V-1 as this constant's source alongside the existing
`DEMAND_GROWTH_RATES` (Table I-1a) note.

**What Table V-1 is.** The Gold Book's own external-capacity accounting: *net*
capacity purchases from external control areas (imports minus capacity exports),
backed by UDR / External-CRIS-Rights / ETCNL / FCFSR elections and grandfathered
rights (table note 2) — i.e. the ICAP-market products through which external
capacity counts in NYISO's ledger. It is the exact quantity NYISO's own NYCA
Capacity Schedule adds to internal resources: Table V-2a Summer 2026,
37,697.7 (NYCA resource capability) + 3,168.5 (net capacity purchases)
= 40,866.2 MW Total Resource Capability, restated in prose on p. 75 and p. 137.

## 2. Basis discipline — why × 0.8679, and why that is the conservative direction

The Gold Book capacity schedule states **seasonal capability (ICAP)** MW, while
the model's NYISO adequacy requirement is **UCAP**:
`peak × (1 + IRM 0.244) × (1 − 0.1321)` (the R5a pairing,
`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`). Crediting the ICAP number
against a UCAP requirement would overstate by ~13 % of the entry. So the entry
converts with the **same published factor the requirement side uses** — one
basis across both sides of the I7 comparison (rule 19), the identical
documented-reconciliation pattern as the PJM DR entry (DR UCAP / UCAP
requirement). Zero free parameters: both operands are published, both are
already independently intaken/tested in this repo, and the arithmetic is stated
in the constant's citation block and pinned by test
(`test_ucap_conversion_uses_the_requirement_side_factor` — the entry's implied
conversion **is** the registered requirement-side ratio, so the two can never
silently diverge).

Direction of the approximation: NYISO's actual ledger derates each external
resource by its *own* EFORd / UDR-line availability (ICAP Manual §4.5). The HQ
and CHPE ties derate far less than the NYCA-wide 13.21 % fleet average applied
here, so this construction can only **under-credit** — it cannot manufacture
firm MW NYISO would not count (the same conservative-direction argument as the
hydro registry's lower-class-factor choice).

**Corroboration (UCAP basis + magnitude).** NYISO 2025 SOM (Potomac Economics,
May 2026 — re-fetched, sha-verified against `SHA256SUMS.txt`:
`80c27d0b…`, 14,425,051 B): Figure A-97 "NYISO Capacity Imports and Exports by
Interface" shows **net capacity imports transacting in UCAP** at roughly
1,500–2,500 MW monthly over May 2023–Apr 2026, and the adjoining text confirms
the §4.5 EFORd-derate construction. The Gold Book's 2026 figure sits at the top
of that historical band because it adds CHPE (in service 2026, note 4). A
2,749.9 MW UCAP entry is squarely the magnitude NYISO's own ICAP market record
shows.

**The two rejected bases, re-affirmed** (and pinned by
`test_entry_is_not_a_deliverability_limit_or_the_dispatch_floor`):

* **NOT** the model's 900 MW HQ firm dispatch floor — an inherited ladder
  constant (`scripts/data/derive_nyiso_import_tranches.py`: *"kept at the
  ladder's established value"*), not a published RA accreditation. The prior
  session's refusal stands; no new evidence overturned it, and none was needed
  once the published number existed.
* **NOT** the 4,350 MW Simultaneous Import Limit — a deliverability *limit*,
  the exact error the CAISO entry rejects for the MIC.

## 3. The honesty test, carried as declared

The prior session pre-declared: *"any real value is O(10²–10³) MW against a
36 MW gap … that overshoot is the evidence the input is honest rather than
tuned."* Result: **2,749.9 MW against 35.7 MW = 77×** — one-to-two orders of
magnitude, inside the declared band. The number was fixed by the two published
operands before any solve was run; the pre-solve arithmetic predictions were
recorded in-session before launching the T1-F leg.

## 4. Re-scored NYISO T1-F leg (I7's post-intake state)

**Run:** `run_full_horizon.py --iso NYISO --start-year 2026 --end-year 2030`
(HEAD defaults — the NYISO T1-F posture, plain like FFR-3A-2's NYISO leg), on a
freshly regenerated `data/clean` (50/51 datatypes; the one failure is
`miso-m2m-flowgates`, a MISO-only mirror absent on disk, irrelevant here).
Solved 5/5 years, wall 13.1 min, peak RSS 2.82 GB, cache key
`fdd84d51e31ffc82`, scored at sha `ea4e4faf65de`.

**Verdict (rubric v1.0, tier t1f): `PROMOTE-WITH-CAVEATS`** —
FC-1 **PASS** (all 14 invariants; was FAIL `['I7']`), FC-2 **PASS** (I12
"requirement-implied floor [8.0%, 23.0%]; all in-band" — was CAVEAT with an I12
WARN and a 23.8 % backstop-share caveat), FC-7 CAVEAT (DOF ledger absent — the
program-wide instrument gap every T1-F leg carries, unchanged), FC-8 PASS.

The per-year ledger, with the intake's contribution decomposed:

| year | peak MW | accredited firm MW | requirement MW | surplus | surplus − credit¹ |
|---|---:|---:|---:|---:|---:|
| 2026 | 29,409.6 | 34,835.4 | 31,752.6 | **+3,082.8** | +332.9 |
| 2027 | 29,479.9 | 34,828.1 | 31,828.5 | **+2,999.6** | +249.7 |
| 2028 | 29,554.6 | 34,828.1 | 31,909.2 | **+2,918.9** | +169.0 |
| 2029 | 29,633.8 | 36,172.1 | 31,994.7 | **+4,177.4** | +1,427.5 |
| 2030 | 29,717.5 | 36,172.1 | 32,085.1 | **+4,087.0** | +1,337.1 |

¹ the position with the 2,749.9 MW credit subtracted. For 2026 this is **exact**
(the base year runs no evolution, so the subtraction reproduces the pre-intake
ledger); for 2027–2030 it is arithmetic only, not a solved counterfactual — a
pre-intake solve could have built differently.

**The honest attribution, both halves:**

* **The 2026 accredited firm is exactly the predicted number.** The pre-solve
  prediction (recorded in-session before launch) was 32,085.5 + 2,749.9 =
  34,835.4 MW — the solve reproduces it to the digit. The base-fleet ledger is
  unchanged; the credit lands verbatim and nothing else moved on the supply
  side.
* **The PASS is over-determined at this HEAD.** The FFR-3A-2 verdict was scored
  at the 2026-08-03 epoch with peak 29,750.97 MW (requirement 32,121.2); at
  today's HEAD the demand path has drifted the 2026 peak to 29,409.6 MW
  (−341.4 MW), so even *without* the intake the 2026 leg would have passed by
  a thin +332.9 MW (~1.0 %). That drift is epoch noise, not a mechanism —
  exactly the kind of margin the adjudicating finding warned is invisible to
  I7. The intake is what moves every year from marginal-by-drift to
  structurally held (+2.9 to +4.2 GW, 9–13 % of requirement).
* 2027/2029 entry is **economic** (gas-CC/wind/solar via the entry screen);
  no backstop build appears in any year's ledger, consistent with FC-2's
  backstop-share caveat clearing.

**Registration (rule 15, forecast namespace only):** run id
`nyiso-2026-2030-extcap-capxd2` via `scripts/register_forecast_run.py --summary
… --label extcap-capxd2 --kind t1f`, with `verdict_key: nyiso-t1f`. The
committed artifacts: the canonical sidecar
`frontend/data/hindcast/nyiso-2026-2030-extcap-capxd2.json`, the bundle's
`full_horizon_summary.json` + **`run_config.json`** (FC-7's requirement) +
per-year `evolution_*.json` + resolved `config.yaml` under
`results/ff-t1f-extcap/nyiso/`, and the verdict snapshot merge below. The
generated registry/runs/manifest files stay gitignored (the Pages deploy is
their writer).

**Verdict snapshot merge** (`frontend/data/forecast/ff-verdicts.json`),
following the FFR-3A-2 preserve-then-overwrite convention its own docstring
mandates (board readers consume the bare key): the FFR-3A-2 measurement is
preserved verbatim under **`nyiso-t1f-ffr3a2`**, and the bare **`nyiso-t1f`**
now carries this re-score, stamped `scored_at_sha ea4e4faf65de / cache_epoch
fdd84d51e31ffc82 / session capx-D2-extcap-intake`. The FF-2D baseline
(`nyiso-t1f-ff2d`) is untouched.

## 5. What was shipped

* `src/market_sim/config/capacity_market.py` — the NYISO registry entry
  (`3_168.5 * (1.0 - 0.1321)`) with its full citation block; the header's
  provenance-case (a) list gains NYISO.
* `src/market_sim/model/capacity_evolution/adequacy.py` — docstring updates
  only (`_firm_import_mw`, `accredited_firm_capacity_mw`).
* `tests/unit/model/test_capacity.py` — `TestNyisoExternalCapacityIntake`
  (4 tests): registry reconstruction from the published operands (including
  Table V-1's own component sum), the one-basis factor identity against
  `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`, ledger additivity via
  `_firm_import_mw`/`accredited_firm_capacity_mw`, and a pin that the entry is
  neither the 4,350 MW SIL nor the 900 MW dispatch floor.
* `tests/unit/model/test_capacity_demand_curve.py` — the hand-computed NYISO
  reserve-position ledger gains the new firm-import term.
* `data/raw/NYISO/README.md` — the 2026 Gold Book bullet now names Table V-1
  as this constant's source (payload stays gitignored; sha unchanged in
  `SHA256SUMS.txt` — both re-fetched files verified byte-identical).
* The T1-F registration set of §4.

Tests: the fast lane passes with the change (7,160 passed; the only 6 failures
reproduce identically on the un-edited tree — pre-existing local-environment
issues: 5 pandas-3 curation quirks + 1 keeper-resolution test, all unrelated).
`scripts/check_mechanism_matrix.py` green.

## 6. Governance

* **Rule 28 `[R-MECH-MATRIX]` — no shard edit, and none made.** A registry
  constant with a published citation is an **input, not a mechanism**: this
  change adds no `ScenarioConfig` field, arms no flag, and mints no cell
  verdict. (The verdict's run_config row reads 752 keys vs FFR-3A-2's 671 —
  that growth is other sessions' fields landed between the 2026-08-03 epoch
  and this HEAD, none of them this lane's; this session's diff touches only a
  constants registry and docstrings.) CI's matrix guard passes; its WARN-level
  duty-(b) heuristic on new registrations is expected and correct here.
* **Rule 22 `[R-HOLDOUT]` — freeze not implicated.** No backcast year was
  solved, scored or registered; the solve is forecast-mode 2026–2030, which the
  policy explicitly leaves unrestricted. Data intake (the two PDF re-fetches)
  is channel-1 unrestricted and no-LP.
* **Rule 13 `[R-MEASURED]`** — the entry is a forward-regenerating market
  input (annual Gold Book publication, responsive to conditions), never an
  outcome pin; the trap identified by the prior finding (re-deriving the
  translation factor because a residual moved) was not touched — the factor
  used is the one already registered and tested on the requirement side.
* **Backcast keeper untouched, by construction.** The calibration backcast
  solves every year as its own base year (`run_calibration_full.py` builds a
  pristine per-year config; `evolve_fleet` never runs), so
  `accredited_firm_capacity_mw` — the only consumer of this registry — is
  unreachable in any backcast keeper solve. No keeper shard, `status/*.js`,
  `calibration-complete.json`, offer curve or commitment bridge was touched.
  The backcast registry was not written to (rule 15's forecast/backcast split).
* **Model assignment honoured** (rule 27): `src/market_sim/config` edited under
  Fable; all pushes are exact on-disk bytes over `git push` with post-push blob
  verification (line count + sha256) on every ≥300-line file.

## 7. What remains between NYISO and a clean T1-F PROMOTE

Nothing in this lane. FC-1 gate (a) already held (marker + keeper
`2026-08-22-nyiso-152-duty-complete`, CALIBRATED); gate (b)'s FC-1/FC-2 now
PASS on the bare `nyiso-t1f` key. The single remaining caveat is **FC-7's
absent DOF ledger**, a program-wide instrument every T1-F leg carries equally
(`build_forecast_dof_ledger.py` lane) — not NYISO-specific and not addressable
by this session's charter.

## 8. Routed items (unchanged from the adjudicating finding)

D-1 (the checker's dropped `year` argument for PJM's published-FPR path) and
D-2 (backstop EFORd sizing vs `_make_new_generator`) remain routed to the
director; nothing here touched either. Note D-1 is inert for NYISO (no
published FPR), so this leg's I7/I12 readings are unaffected by it.
