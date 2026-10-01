# FINDING — SCN-FIX3: four small repairs, zero LP

**Lane** SCN-FIX3 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-08 ·
**Branch** `claude/scn-fix3-ercot-repairs-7bkfmg` · **Base** `a667073f` ·
**DATA PROFILE** `code` · **Solves: NONE.** No LP ran, nothing was registered, no
cache key moved, no default moved, no `src/` file was touched.

| # | repair | commit | files |
|---|---|---|---|
| 1 | ERCOT DC-block regime re-derived from HEAD constants | `8006571d` | `configs/scenario_campaign_matrix.yaml` |
| 2 | S9/S10/S11/S12-committed levels relabelled | `b422ad69` | `configs/scenario_campaign_matrix.yaml` |
| 3 | Policy-row duals recorded in the full-horizon summary | `1d683cd7` | `scripts/run_full_horizon.py`, `scripts/run_ces_leg.py`, +test |
| 4 | `--set` overrides carried into the forecast sidecar | `55102143` | `scripts/register_forecast_run.py`, +test |

**Rule 28 `[R-MECH-MATRIX]` duty (c) does not fire and no matrix shard was
edited.** No `ScenarioConfig` field is added, removed or defaulted differently
by any of the four repairs; no mechanism was proposed or tested. Items 3 and 4
add keys to two OUTPUT artifacts and items 1–2 are comments. There is nothing
for the matrix to record.

---

## 1. Item 1 — the ERCOT tail-regime block was derived from a retired constant

**The block's headline conclusion was wrong at HEAD, and so was the constant
under it.** `configs/scenario_campaign_matrix.yaml` carried "THE ERCOT
TAIL-REGIME ARITHMETIC" with a five-row table predicting that 2030 flips to the
tail regime — energy 800 → 1,800 TWh and peak 94 → 267 GW in ONE year, making
2030 "an unserved-energy year by construction". It said so "with the constants
at this commit (DC high 122 GW by 2030 … growth high 11.5 %/yr)". **Both of
those constants are retired**:

| input | block assumed | HEAD | citation |
|---|---|---|---|
| `DATACENTER_ADDITIONS_MW["ERCOT"]["high"]` @2030 | 122,000 MW | **88,603 MW** | `constants.py:3153` (the retirement note), `:3160` (the value) |
| `DEMAND_GROWTH_RATES["ERCOT"]["high"]["near"]` | 0.115 | **0.206157** | `constants.py:2727` |

The 122 GW figure was a raw interconnection-queue estimate (0.70 × 226 GW queue
× 0.77 in-service); constants.py replaced it with ERCOT's own published
TSP-Provided upper FORECAST. Both moves push `dc_E/E` down — a smaller block
over a larger denominator — so the tail regime is unreachable.

### 1.1 The re-derivation, and why it is trustworthy

Re-derived with stdlib arithmetic only (no numpy in this container, no solve):
the two dict literals are pulled out of `constants.py` with `ast.literal_eval`
so the table is provably the HEAD literal, `np.interp` semantics are reproduced
(piecewise-linear, flat-extrapolated), and growth is compounded from the 2024
weather base exactly as `runner._scale_demand` does (`range(weather_year,
year)`, near era throughout — `DEMAND_GROWTH_TRANSITION_YEAR` is 2030).

| year | block GW | dc_E TWh | E TWh | dc_E/E | regime | LOAD-HI peak GW | measured |
|---|---|---|---|---|---|---|---|
| 2026 | 21.4 | 187.2 | 675 | 0.277 | relocate | 110.6 | 110.63 |
| 2027 | 34.9 | 305.4 | 814 | 0.375 | relocate | 128.0 | 127.90 |
| 2028 | 48.3 | 423.5 | 982 | 0.431 | relocate | 150.5 | 150.43 |
| 2029 | 61.8 | 541.6 | 1185 | 0.457 | relocate | 179.5 | 179.30 |
| 2030 | 75.3 | 659.7 | 1429 | 0.462 | relocate | 216.0 | 215.81 |

`dc_E/E` **peaks at 0.462**; the tail needs 1.000.

**The derivation is validated against nine measured points, not asserted.** It
reproduces the solved peaks of ALL THREE arms to ≤ 0.09 %: LOAD-HI in all five
years (above), LOAD-HI-ORGANIC at 2026/2030 (118.2 vs 118.24; 241.8 vs 241.94)
and REF at 2026/2030 (104.0 vs 104.05; 161.8 vs 161.75). The base it uses —
`E0 ≈ 464 TWh`, `P0 ≈ 84.9 GW`, inverted from the committed REF trajectory — is
the one input NEITHER moved constant touches, and the cross-check confirms it is
still right.

### 1.2 The measured outcome

Prediction **P-1 is a HIT**: ERCOT stays in RELOCATE in all five years of both
arms; the 1,800 TWh / 267 GW discontinuity does not reproduce; the arms' energy
deltas are identical (2030: 22.978 vs 22.984 TWh, where a tail step would add
~660 TWh). 2030 is therefore **not** "an unserved-energy year by construction" —
ERCOT does shed 538.9 TWh, but because HEAD REF is already in deep shortage (REF
alone sheds 127.2 TWh), not because of a tail step. Right number, wrong cause,
scored SPLIT (`FINDING-scn-ws5a-load-ercot-2026-09-06.md` §0, §3, §5).

The TAIL row is **deleted, not annotated** (rule 26 `[R-DELETE]`).

### 1.3 DEVIATION FROM THE PROMPT, stated plainly — consequence (1)'s comparator

The prompt instructed: *"Keep consequence (1) — the flat block depresses ERCOT's
peak below REF while energy rises … it is still true and still load-bearing."*
**Half of that is measured FALSE at HEAD, and the FINDING the prompt cites as
authority is what falsifies it.** §3(b) of that document scores the "below REF"
claim a **clean MISS**: LOAD-HI's peak is measured ABOVE REF in every year
(110.6 vs 104.1 … 215.8 vs 161.8 GW) and I12 is uniformly WORSE. NYISO's
identical claim is also scored MISS (`FINDING-scn-ws5a-load-nyiso` §3(b) — its
block reaches 11 % of energy, not the 35 % assumed).

Leaving it in place would have reproduced exactly the defect item 1 exists to
repair, so I **kept the caveat and corrected its comparator** rather than either
deleting or preserving it:

* The flattening artefact is **real** against the comparison that holds growth
  fixed — LOAD-HI vs LOAD-HI-ORGANIC: **−7.5 / −12.1 / −16.7 / −21.3 / −25.8 GW**
  across 2026–2030. MISO carries the campaign's cleanest confirmation of this
  framing (LOAD-HI peak 3.91 GW below ORGANIC at 2030 on identical energy,
  scored **HIT**, `FINDING-scn-ws5a-load-miso` §3(c)).
* It is **not** real against REF, because REF rides the MID growth path and that
  gap (+6.6 → +54.3 GW) swamps the flattening.

The operative warning is unchanged and still binds, now stated correctly: *a
peak-based adequacy reading (I12, reserve margin) of a high-DC arm understates
that arm's stress relative to its ORGANIC twin, as an artefact of the relocate
rule, and is not to be quoted as adequacy.*

I also corrected the NYISO/MISO sentence inside the same block, which was stale
from the same cause and had a measured citation available.

### 1.4 Proof it is comment-only

Both revisions parsed with `yaml.safe_load` and compared: **identical**. All
non-comment lines diffed against the pre-lane base `a667073f`: **identical**.
16 cases, unchanged.

---

## 2. Item 2 — four owner rulings had not been swept into the file

Ruling **S9** (2026-09-06, card D-2(b)) took the WS-3a memo box-5 placeholders
as the **committed** levels: `f_commit` mid **0.5** and the WTP ceiling
**$4.5/MWh**. `constants.py` already carries the S9 stamp on both cells
(`VOLUNTARY_COMMITTED_DC_FRACTION`, `VOLUNTARY_WTP_CEILING_USD_PER_MWH`), so the
campaign YAML was the **last stale site** — it still read "owner-set and
LABELLED ILLUSTRATIVE", "0.5 placeholder", "4.5 placeholder", and "VOL-MID
carries two illustrative cells".

The sweep found three more of the same class, all ruled the same day:

| card | ruling | file said | now |
|---|---|---|---|
| D-2(b) | **S9** — placeholders ARE the committed levels | "LABELLED ILLUSTRATIVE" | committed, S9 cited |
| D-3c | **S10** — eligible set stands as built | "is STILL OPEN", a "RECOMMENDATION" | committed set, S10 cited |
| D-6 | **S11** — counts-toward, both nettings reported | "D-6 IS STILL UNRULED", "(D-6 OPEN)" | ruled, S11 cited |
| D-2(c) | **S12** — 80 % slope committed | banner counted it among "TWO OPEN" | "ALL THREE ARE NOW CLOSED" |

**Stale holds released too.** Ruling S5 held the four voluntary cases and
`CAP-STATE-TIGHT` until the capx CCS emission-rate seam was repaired. capx D77
landed that repair, the campaign itself falsified S5's premise (the retrofit
screen is armed by the STATE carbon program, not the CES — SCN-DESK r#10), and
S9 added the four to the Stage A-POLICY lanes by addendum. Three sites still
said "solved by nobody until the desk releases A-POLICY". `CAP-STATE-TIGHT`
alone stayed out of that addendum and now says exactly that.

**LABELS ONLY, NEVER NUMBERS** — the same identification SCN-LEVELS made for the
S3 levels ("the change is to the label, not the number"). Proven by the same two
checks as item 1: parsed YAML identical, all non-comment lines identical. **No
re-solve is owed by any of it.**

---

## 3. Item 3 — a policy leg's duals were unrecoverable from its committed artifacts

`clean_region_duals` and `co2_cap_price` were written only to the cached year
bundle (`results/<ISO>/<key>/`, gitignored) and the solver log. The slim summary
carried `rps_dual` alone and the sidecar carried neither, so under ruling **S16**
— each campaign shard's bundles die with its container — the dual limbs of gates
**G4** and **G7** were unscorable at the coordinator by construction. Reported by
SCN-WS5A-POLICY-NYISO §9 item 4.

### 3.1 DEVIATION FROM THE PROMPT — the writer is not `run_ces_leg.py`

The prompt (and the originating lane) named `scripts/run_ces_leg.py`, while
instructing me to *"find the writer yourself rather than trusting a line number
from this prompt"*. I did, and it is
**`scripts/run_full_horizon.py::extract_trajectory`**. `run_ces_leg.py` delegates
every summary key to `solve_and_summarize`, and its two per-leg hooks
(`extra_summary` / `extra_spec`) are **static per leg**, so neither can carry a
per-year value; a `run_ces_leg`-local version would have to re-open the very
cached bundles that S16 kills, would duplicate the recording seam
(rule 19 `[R-ONE-MECH]`), and would fix only the CES lane while REF / LOAD-* /
CARB-* / CAP-* / VOL-* kept the same gap.

`run_full_horizon.py` is **not** in the prompt's FILES-YOU-OWN list, so I flag it
here for SCN-DESK. It is not in the MUST-NOT-TOUCH list either, and the prompt's
own STOP trigger is scoped to `src/` — *"items 3 and 4 are recording seams in
`scripts/` — if a repair genuinely requires `src/`, STOP"* — with model
assignment as its stated reason. This is `scripts/`, not `src/`, and rule 27
`[R-PUSH]` assigns `scripts/run_*.py` to Opus or Fable, which this lane is. **No
`src/` file is touched.** If SCN-DESK disagrees, the repair is one revertible
commit (`1d683cd7`) with a +84/−0 diff.

### 3.2 What was added

A new `_policy_duals(yd)` helper reads both vectors off the year's
`DispatchResult` and passes them through **RAW**, in the LP's own row order,
exactly as the LP exposes them (the per-fuel/zone consumer mapping deliberately
happens at the runner, which owns the qualifying sets). Two keys join the
trajectory row beside `rps_dual`.

**The null contract, as required:** a missing dual is `None`, **never `0.0` and
never `[]`**. A zero dual (the row is slack) and an unrecorded dual (nothing was
measured) are different facts, and every consumer of `rps_dual` already separates
them with `is not None`. Read via `getattr` so a year restored from an older
cached bundle reports "not measured" rather than raising.

### 3.3 PROVEN UNCHANGED

* **Cache keys.** `tests/regression/test_persisted_identity.py` passes unchanged:
  `PINNED_DEFAULT_CACHE_KEY = 547053bdfccd4264` and
  `PINNED_BACKCAST_CACHE_KEY = f61891696e671969`.
* **The solve-surface fingerprint cannot see it either** (capx D79):
  `SURFACE_MODULES` names only `market_sim.config.*` plus one pipeline module.
  `scripts/` is outside the surface by construction.
* **Solve path untouched.** The diff is **+84/−0** across two `scripts/` files;
  the only functional addition sits in `extract_trajectory` and its helper, both
  called AFTER the solve returns (`run_full_horizon.py:884`,
  `run_equilibrium_battery.py:188`). `git diff --name-only | grep ^src/` → empty.
* **Backward compatibility.** Every consumer reads NAMED keys (`row["year"]`,
  `.get("co2_mt")`); the two key-by-key comparators the code warns about use
  explicit allowlists (`_CAPACITY_KEYS` / `_OUTCOME_KEYS`) and ignore new keys.
  The 63 Stage-A legs and every earlier forecast bundle simply lack the keys,
  which reads identically to `None`. **No committed summary is rewritten.**
* **Test.** `tests/scoring/test_policy_duals_recording.py`, 12 LP-free cases:
  emission, the null-vs-zero distinction both ways, the JSON round trip, the
  genuinely-missing-attribute path, and the additive promise over 11 legacy keys.

---

## 4. Item 4 — a `--set`-constructed leg was not self-describing from the dashboard

Traced: `run_full_horizon.py:943` writes `summary["set_overrides"]`, but
`register_forecast_baseline.build_sidecar` copies a **fixed list** of summary
keys into `meta` and that block is not among them — so the key never reached the
sidecar at all. Verified on the committed artifact: the NYISO `ces-p60` sidecar
has **no** `set_overrides` key (`'set_overrides' in meta` → `False`), which every
reader sees as `null`, while its bundle correctly holds
`federal_ces_premium_usd_per_mwh: 60.0`.

Nothing is mis-registered — the run is still identified by `meta.case` plus its
distinct `cache_key`. What was missing is dashboard self-description.

Carried in **`register_forecast_run.py`** — which CLAUDE.md names as the SINGLE
forecast registration path, and which IS in this lane's owned files —
immediately after the `build_sidecar` delegation and **before** the provenance
stamp, so the stamp covers it. `{}` (recorded, none applied) and `None` (the
summary predates the block) stay distinguishable, the same discipline
`build_sidecar` states for its own config-describing keys. An explicit
`--extra-meta` claim is never overwritten; a missing or unparseable summary
cannot break a registration.

**Additive only: +55/−0.** No committed sidecar is rewritten in this lane, the
backcast namespace is untouched, and `meta` is passed through wholesale to the
run payload so the field reaches the explorer with no renderer change. A later
registration carries it naturally. Test:
`tests/scoring/test_register_set_overrides.py`, 13 LP-free cases.

---

## 5. Found and NOT fixed — routed, not absorbed

1. **`test_solve_surface_fingerprint_is_pinned[PJM]` is RED on `main`.**
   `f5eeaed979e6ce82` (212 rows) vs the pinned `0f749d17202c32d9` (211 rows) — a
   config registry VALUE moved and gained a row, so every future PJM solve
   produces different numbers than the bundles on disk. **It fails identically at
   the pre-lane base `a667073f`**, so it is not this lane's, and the fix is a
   `src/market_sim/config/` pin advance with a dated cause block — outside these
   regions and owed by whichever lane moved the row. Routed to SCN-DESK.
2. **Nine more pre-existing failures** under the `register|forecast_run|sidecar|
   provenance` selection (`test_gate_a_provenance`, five `PartitionCaptureKeyTest`
   cases, two `GoldenManifestSchemaTest` cases, `test_registration_marker_gate`,
   `test_capacity::test_unregistered_iso_is_none`). Failure sets on this branch
   and at the base were captured and **diffed byte-for-byte: identical, 10 = 10**.
   This lane adds 13 passing tests and introduces no failure.
3. **`register_forecast_baseline.py`'s standalone CLI still drops
   `set_overrides`.** Item 4 is carried at the single registration path CLAUDE.md
   designates, which covers every forecast registration in practice; a direct
   `register_forecast_baseline.py --summary` invocation would still omit the key.
   That file is outside these regions — routed rather than touched.
4. **Item 3's duals are emitted UNLABELLED**, in the LP's clean-row order. The
   labels live in `clean_region_arrays.labels`, which needs per-year fleet/zone
   context the reporting path does not carry; resolving them would mean a `src/`
   change. The order is documented instead. If a gate needs labelled duals,
   that is a `src/` card for SCN-DESK.

## 6. Duties

* **Rule 28 `[R-MECH-MATRIX]` duty (c) does not fire** — no `ScenarioConfig`
  field added; no mechanism proposed or tested; no shard edited. Stated here so
  the omission is explained rather than silent.
* **Rule 15 `[R-DASHBOARD]` / rule 29 / rule 31** — not engaged. Zero LP, zero
  bundles produced, nothing registered, nothing deleted.
* **Rule 27 `[R-PUSH]`** — all four files ≥ 300 lines were fetch-back verified
  after the push (blob SHA + line count vs local): `run_full_horizon.py` 1544,
  `run_ces_leg.py` 299, `scenario_campaign_matrix.yaml` 470,
  `test_policy_duals_recording.py` 194 — all OK. Edits were made locally and the
  exact on-disk bytes pushed; no file was regenerated from response content.
* **Nothing in the MUST-NOT-TOUCH list was edited**: no `src/market_sim/**`, no
  `results/` bundle, no committed sidecar, no `frontend/data/backcast/**`, no
  `program-status.json`, no `ff-verdicts.json`, no desk ledger, no plan §5.1, no
  mechanism-matrix shard. The one file outside the named FILES-YOU-OWN list is
  `scripts/run_full_horizon.py` (§3.1), flagged rather than quietly taken.
