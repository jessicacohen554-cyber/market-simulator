# FINDING — capx-D8: the forecast DOF-ledger instrument + the seven-leg run_config provenance debt

**Lane:** capx-D8 (director r#19, `docs/handoffs/capx-director-ledger-2026-08.md` §0p.2)
· **Branch:** `claude/capx-d8-dof-ledger-lrih7b` · **Date:** 2026-08-30 · **Zero solves.**

## §0 Headline

Both FC-7 halves are delivered, and **no verdict, board, or backcast surface was
touched** (the re-emission is the deferred follow-up, §6):

1. **The DOF-ledger instrument exists.** `scripts/build_forecast_dof_ledger.py`
   grew from the FFR-3B FR-27 all-`unattested` skeleton into an attribution
   engine that REPORTS each run-chosen parameter's committed identification
   source (rule 21 `[R-DOF]`: report, never supply). Ledgers are committed for
   the live t1f bundles that have committed run_configs — **NEISO s4b-ara
   treatment + control (7 entries, all IDENTIFIED) and NYISO extcap (1 entry,
   IDENTIFIED)**. MISO/PJM live t1f ledgers are blocked on a records fact
   discovered here (§5.1): their FFR-3A-2 bundles were never committed, so no
   committed run_config exists to build from.
2. **All seven legacy legs are RECOVERED — none is irrecoverable.**
   `results/run-config-debt/<leg>/run_config.json`, each labelled
   `RECONSTRUCTED — NOT ORIGINAL` with its evidence chain, plus a
   reconstruction-labelled `dof_ledger.json` per leg. Verification is exact on
   every leg (§4): the six documented resolved-posture flags reproduce on all
   seven, and the MISO FFR-3A-4 leg reproduces its committed cache key
   `46954f417b6e18e2` **byte-for-byte**.

## §1 The instrument's contract

`python scripts/build_forecast_dof_ledger.py <bundle>` reads the bundle's
committed `run_config.json` (or harness `run_config.yaml`), enumerates the
**non-default solve-affecting ScenarioConfig fields** — the parameters THIS run
chose relative to the shipped registry, with tuple/list representation
normalized — and writes `<bundle>/dof_ledger.json` (`schema: dof-ledger/v1`,
readable by `forecast_verdict.py --dof-ledger`).

**Attribution chain, per entry** (first match wins; every step is
mechanically cross-checked):

1. **iso-registry** — the value equals the ISO's registered
   `ISOConfig.default_scenario_overrides` cell (provenance recorded; the
   identification token + primary source come from the curated table, gated on
   that match);
2. **runner-posture / curated rows** — a session-reviewed
   `CURATED_IDENTIFICATIONS` row citing committed evidence, applied ONLY when
   its gate passes (the run value equals the row's expected value, or the
   registry match above succeeded). A refused row leaves the entry
   UNIDENTIFIED and records why (`curation_refused`);
3. **epoch drift** — a value equal to the shipped default *at the run's own
   recorded git sha* (checked via `git show` of `scenarios.py`, literal
   defaults only) is not a free parameter of the run: reported under
   `epoch_drift`, never scored;
4. **UNIDENTIFIED** — everything else. The entry keeps the literal
   `identification: "unattested"` token, so FC-7 scores the ledger **exactly
   as an absent one** (CAVEAT at t1/t2, FAIL at t3) with zero scorer changes.

**Identification taxonomy:** `published` · `measured-physical` · `residual`
(must carry an open `root_cause` or the ledger is malformed — unchanged) ·
`design-decision` (NEW: a structural/reproducibility posture identified to a
signed owner decision or committed decision record; refuses numeric
magnitudes) · `unattested` (not an identification — the UNIDENTIFIED marker).

**Rule-21 honesty pins, tested** (`tests/scoring/test_forecast_dof_ledger.py`,
20 tests, trivial fixtures first): an UNIDENTIFIED entry scores as an absent
ledger at every tier; a mixed ledger still CAVEATs; a curated row with a value
mismatch is refused; another ISO's run never borrows NEISO's curation (rule 25);
`design-decision` never identifies a magnitude; a fully-identified ledger CAN
pass FC-7 — but only a chartered re-score consumes it (§6). The full
`tests/scoring/` suite: 1104 passed; the 7 failures are pre-existing at the
branch base (verified by stash-rerun), none introduced here.

**Scope boundary, stated in every ledger:** registry defaults the run inherits
(offer surfaces, floors, sigmoids, …) carry their identification burden in the
registry's rule-5 citations and the ISO's designated backcast keeper's rule-21
DOF ledger — named in the ledger's `registry_identification` block (keeper read
from `frontend/data/backcast/keepers/<ISO>.json` at build time, read-only) —
and are not re-enumerated per bundle. Ledgers built from a RECONSTRUCTED
run_config inherit that label in a `basis` field.

## §2 Live-bundle ledgers (committed beside each run_config)

### NEISO — `results/ff-t1f-s4b-ara/neiso/dof_ledger.json` (+ identical `neiso-control/`)

The live NEISO t1f leg (`neiso-2026-2030-s4b-ara`, the bare `neiso-t1f` key's
backing pair). **7 entries, ALL IDENTIFIED, 0 UNIDENTIFIED:**

| entry | value | identification | source |
|---|---|---|---|
| `scarcity_price_overlay` | True | published | ISO-NE scarcity market design; registered NEISO footing (iso_configs `_neiso_config`) |
| `ordc_voll` | 2000.0 | published | ISO-NE Tariff §III.1.10.1A energy offer cap |
| `ordc_mcl_mw` | 1200.0 | published | Millstone 3 largest contingency — ISO-NE RSP Table 4.1 / NPCC Directory #1 |
| `ordc_lolp_sigma_mw` | 900.0 | published | ISO-NE PAF Study 2022 winter reserve-error σ |
| `ordc_lolp_shift_sigma` | 0.0 | published | no administrative shift applies to ISO-NE (ERCOT PUCT instrument) |
| `ordc_multistep_floor` | False | published | no OBDRR048 floor in ISO-NE (ERCOT-specific rule) |
| `forecast_xyear_warmstart` | False | design-decision | owner D-10 (2026-08-04); `FORECAST_BUNDLE_XYEAR_WARMSTART`; ffr-3t measurement |

Epoch note: 2 fields added to ScenarioConfig since the run's sha (`88baa9d5`),
reported, not scored.

### NYISO — `results/ff-t1f-extcap/nyiso/dof_ledger.json`

The live NYISO t1f leg (`nyiso-2026-2030-extcap-capxd2`). **1 entry,
IDENTIFIED:** `forecast_xyear_warmstart=False` (design-decision, D-10, as
above). Epoch report: 13 fields added since its sha (`ea4e4faf`), and
`capacity_market_clearing_by_iso: null` vs the HEAD factory default — resolved
here (§5.2) as the runner's non-golden posture at that sha, not default drift.

**No UNIDENTIFIED row exists in any committed ledger.** The instrument's
UNIDENTIFIED path is exercised and pinned by tests; the live bundles simply
run very close to the shipped registry — which is itself the finding: the
T1-F free-parameter surface is tiny, and its identification burden lives
almost entirely in the registry + backcast-keeper lane the ledgers now name.

### MISO / PJM live t1f — BLOCKED, records gap (§5.1)

`miso-t1f` / `pjm-t1f` remain at the FFR-3A-2 vintage; their bundles
(`results/ffr3a2/`, gitignored by design) died with the container and **no
committed run_config exists** — their FC-7 `run_config` PASS rows were scored
in-session before the bundle was discarded. No committed evidence ⇒ no ledger;
fabricating one from HEAD defaults would violate the instrument's own
contract. The S-6 (PJM) and S-123-V (MISO) lanes land new committed bundles;
each ledger is then one command. No s6/s123v bundle had landed at this lane's
start (checked against `origin/main` at write time).

## §3 The curated table (the committed, session-reviewed half)

`CURATED_IDENTIFICATIONS` in the script carries 8 rows, each verified
in-session against its cited surface: the six NEISO scarcity/ORDC rows (gated
`requires: "iso-registry"`), the D-10 warm-start posture (gated
`expected: False`), and the hindcast harness's production-scarcity footing
(`scarcity_pricing_enabled`, gated `expected: True`; evidence:
`run_capacity_hindcast.build_config` docstring + the s2 root-cause report).
Extending coverage = adding a row citing committed evidence + regenerating;
hand-editing an emitted ledger is forbidden by its own `how_to_fill`.

## §4 The seven legacy legs — RECOVERED (none irrecoverable)

The debt class: the FFR-3A-3/-3A-4 wave (the four T1-H realized legs + three
T1-X crossover legs; exactly the set the ffr-3a3 handoff §1.1 enumerates plus
its MISO completion). Their FC-7 rows read FAIL `run_config.json absent` — an
instrument-shape defect recorded at solve time (FFR-3A-2 blocker 5: the
harness wrote `run_config.yaml`; the fix was deliberately left to an
instrument lane). Bundles were gitignored; the YAML dumps died with the
containers. D10/D14-era legs already comply and were not touched.

**Method (zero solves):** import `run_capacity_hindcast.build_config` at the
recorded solve sha — mapped across the 2026-08-16 history rewrite via
`docs/governance/citation-commit-map.txt` — in a sparse worktree; call it with
the invocation the committed record documents (all solve-affecting flags
omitted; window/vintage = the harness mode defaults at that sha); emit
`asdict()` as `scenario_config` with a full `reconstruction` block.

| leg (tier) | recorded solve sha → mapped | invocation source | verification |
|---|---|---|---|
| `miso-2021-2025-realized-ffr3a3` (t1h) | `941f4983` → `7ac1ba88` | ffr-3a3 §1.1/§1.3 (flags omitted) | 6/6 posture flags exact |
| `neiso-2021-2025-realized-ffr3a3` (t1h) | `941f4983` → `7ac1ba88` | same | 6/6 posture flags exact |
| `nyiso-2021-2025-realized-ffr3a3` (t1h) | `941f4983` → `7ac1ba88` | same | 6/6 posture flags exact |
| `pjm-2021-2025-realized-ffr3a3` (t1h) | `941f4983` → `7ac1ba88` | same | 6/6 posture flags exact |
| `ercot-2023-2027-crossover-ffr3a3` (t1x) | `941f4983` → `7ac1ba88` | same + PREREG invocation shape | 6/6 posture flags exact |
| `pjm-2023-2027-crossover-ffr3a3` (t1x) | `941f4983` → `7ac1ba88` | same | 6/6 posture flags exact |
| `miso-2023-2027-crossover-ffr3a4` (t1x) | `292f577e` (unmapped) → surface pinned at `edb8d0c2` (= recorded scored_at `6fbd3f28`) | PREREG §1, invocation committed **verbatim** pre-solve | **cache key `46954f417b6e18e2` EXACT** + 6/6 flags |

The cache-key match is the strong result: `ScenarioConfig.cache_key()` hashes
the full registered config payload (path-sentinel-normalized), so reproducing
the committed key means the recovered config surface is exact — it also
**proves the MISO leg ran post-FFR-3T** (`forecast_xyear_warmstart=False`),
where the six 3a3 legs ran pre-3T (`True`; `941f4983` is an ancestor of the
FFR-3T merge, verified) — an epoch boundary inside the wave that a
defaults-at-HEAD reconstruction would have silently erased.

**Honestly irrecoverable remainder, per leg** (recorded in each
`known_unverified`): the original YAML dump bytes and solve outputs (gone with
the containers); per-leg committed cache keys for the six 3a3 legs (none were
recorded, so their reconstructed keys have no comparator); the exact commit
identity of MISO's launch base `292f577e` (the cache-key match pins the config
surface, not the sha). T1-H vintage 2020 / t1x vintage 2023 are the harness
mode defaults at the solve sha, labelled as such rather than independently
documented per leg.

**Adjacent debt, out of this lane's scope, flagged for the director:** (a) the
superseded bare FFR-3A-2 keys (`ercot-t1x`, `miso/neiso/nyiso/pjm-t1h`) — same
class, solved on a rebased lane branch (`f0b8c025`→`87659ae4`), reconstructible
by the same protocol if ever needed; (b) the three committed `-ffr2a` t1x
re-measures — their sidecars carry rich flag meta + cache keys
(`frontend/data/hindcast/*-crossover-ffr2a.json`), making them the easiest next
reconstruction if the director wants their FC-7 rows repaired too.

## §5 Discoveries worth carrying

1. **`miso-t1f` / `pjm-t1f` FC-7 `run_config` PASS rows have no committed
   backing.** The rows are true as scored (in-session, pre-discard) but no
   artifact exists at HEAD; the board's FC-7 story for those two ISOs rests on
   ff-verdicts.json alone until S-6 / S-123-V land committed bundles.
2. **NYISO extcap ran the by-ISO clearing map explicitly nulled.** At
   `ea4e4faf`, `run_full_horizon.reference_config` sets `cmc_by_iso=None` on
   every non-golden run while the dataclass factory already shipped
   {PJM,MISO,CAISO,NEISO: True}; with the scalar gate False, NYISO resolved
   curve-OFF (the board's recorded flip posture). The instrument reports the
   null under `epoch_drift` with the quoted epoch source line and an explicit
   "not mechanically established" note rather than guessing.
3. **The FFR-3B stub's default-comparison had a representation bug**: JSON
   lists never equal dataclass tuples, so all six `*_offer_surface_*` families
   mis-listed as non-default in every ledger it would have produced. Fixed by
   normalization; pinned by test.
4. **Reconstruction across the history rewrite works and is cheap**: shallow
   clone deepened with `--filter=blob:none --shallow-since=...`, old→new sha
   via the citation commit map, sparse worktrees (`src scripts configs`) for
   config-only imports. No data blobs pulled; zero solves.

## §6 The deferred re-emission (explicitly NOT done here)

Per the charter, this lane wrote **no** FC-7 re-score, **no**
`ff-verdicts.json` key, **no** board edit — golden, S-6, and S-123-V were
in-flight on those files. The follow-up lane the director charters after they
land should:

1. re-run `forecast_verdict.py` for the affected keys with `--dof-ledger`
   (and, where the director accepts reconstructions, `--run-config
   results/run-config-debt/<leg>/run_config.json`);
2. expected movement, for pre-registration: `neiso-t1f` / `nyiso-t1f` FC-7
   `dof ledger` CAVEAT → PASS (their ledgers are fully identified — NEISO's
   ONLY caveat retires, giving the program's first clean FC map);
   `ercot/caiso/miso/pjm-t1f` unchanged (no committed bundle to ledger); the
   seven legacy keys' `run_config` row is a **director decision** — a
   RECONSTRUCTED artifact can honestly flip FAIL → PASS-with-note or stay
   FAIL-annotated, but the scorer currently has no notion of the
   `reconstruction` label, so surfacing it (a one-line detail addition) should
   ride with that re-score, not precede it;
3. nothing else: the ledgers and reconstructions are already committed and
   labelled.

## §7 Guardrail compliance

Zero solves (config resolution only, no LP, no data read). Read-only against
every model surface (`src/market_sim/` untouched; keeper shards read-only).
No measured-outcome feedback (rule 13): every identification cites a source
document or decision record, never a residual fit — no `residual` token was
issued. The ledger reports identification and supplies none (rule 21): every
curated row is value-gated, refusals are recorded in the artifact, and
UNIDENTIFIED rows keep FC-7's CAVEAT byte-for-byte. No verdict/board/backcast
write. Tests: trivial fixtures first; 20 new, all passing; no new failures in
`tests/scoring/`. No new ScenarioConfig field, no new mechanism (matrix
duties not triggered). Model: Fable (rule 27); pushes blob-verified.
