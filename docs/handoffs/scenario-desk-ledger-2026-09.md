# Scenario Readiness Desk — Ledger

Standing coordination ledger for the SCN track, implementing
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` ("the plan"). Maintained by the
desk session; one refresh = one commit = one small PR. The desk charters lanes and tracks
state — it never solves, never edits `src/market_sim/` or `scripts/`, and never charters
backcast-calibration work or anything on the capacity-expansion director's queue
(`docs/handoffs/capx-director-ledger-2026-08.md`), which it deconflicts with at every refresh.

**Charter date:** 2026-09-05 · **Last refresh:** 2026-09-05 (refresh #1) ·
**r#1 (HEAD `d01ab8b0`):** the desk opens. Ledger created; plan read whole; capx r#40 read for
deconfliction (**D60-R2 RUNNING**, D61/D64 issued-unlaunched, D58 released-pending-D60, D63
queued — none holds a wave-1 SCN file, but D60-R2 and the owner's backcast lanes append to the
six matrix shards continuously, so the last-commit one-line shard protocol is MANDATORY, not
advisory) · **WAVE 1 ISSUED IN FULL — SCN-WS0, WS-1a, WS-2a, WS-3a, WS-4a** (five disjoint-file
lanes, no owner ruling required to start any of them) · **cards D-1, D-2, D-3, D-6 PRESENTED**;
D-4 held for WS-4a's gap list, D-5 held for Stage A's measured cost table · **§2.1b gate read at
the pin: NEISO ONLY** — NYISO's `complete` was withdrawn again on 2026-09-05 (nyiso-193
executing the owner's nyiso-192 promotion ruling; Q5 uniform rule), so `complete` =
{ERCOT, NEISO, PJM} and Q45's premise has lapsed. No Stage-B lane is issuable at this refresh
and none is issued.

**Transport note (r#1):** this session's harness assigns the branch
`claude/scn-desk-charter-x9v4k4` and forbids pushing elsewhere, so this refresh lands there
rather than on the charter's nominal `claude/scn-desk-ledger`. Successor refreshes should use
`claude/scn-desk-ledger` unless their own harness says otherwise; the ledger file path is
unchanged and is what matters.

---

## 0. Refresh log (newest first)

### r#1 — 2026-09-05, main HEAD `d01ab8b0ea5e3c6e1a68c86f8daad1b4b6d605e9`

`d01ab8b0` = PR #4840 (`claude/miso-219-evening-scarcity-qrliuv`), Sat 2026-09-05 15:25:45
−0700. The plan was surveyed at `4d4dc6ce`; the delta to the pin is owner-track backcast work
(miso-219 and predecessors) plus capx records lanes — **no file in any wave-1 SCN region moved**,
so every plan §2 file:line citation is used as written and each lane re-verifies its own anchors
at its branch point (each prompt says so).

**Read this refresh:** CLAUDE.md; the plan entire (§1 definition of done, §2 per-mechanism
state, §3 workstreams, §3.5 case set, §4 constraints, §5/§5.1 sequencing + scorecard, §6 owner
boxes, §7 prompts, §8 findings); FF plan §2.1b (window cap + four-leg gate), §2.4 (budget
anchors + the `data/clean` prerequisite), §7; capx ledger top block + §1 scoreboard;
`docs/mechanism-testing-matrix.md` §5 and the six shards.

**Graded by content — SCN lanes:** none exist. `git ls-remote origin 'refs/heads/claude/scn-*'`
returns empty; no `FINDING-scn-*` doc on main; plan §5.1 unmoved from v1. This is the first
refresh, so nothing is LOST and no relaunch protocol applies.

**Graded by content — capx deconfliction (from capx r#40, HEAD `4d4dc6ce`):**

| capx lane | status | files it holds | collision with wave 1? |
|---|---|---|---|
| **D60-R2** | RUNNING (PR #4824) | `scripts/forecast_verdict.py` (the `_dof_ledger_row` builder + six new (ISO, field) rows), `frontend/data/forecast/` board + verdict re-scores, the finding | **NO** on `src/`; **SHARD-ADJACENT** — its re-scores can append to matrix shards. Mitigated by the last-commit protocol. |
| **D61** | ISSUED, unlaunched | docs only (PJM E&AS operand Phase 0) | no |
| **D64** | ISSUED r#40, unlaunched | docs only (CCS ΔFOM / capture VOM Phase 0) | no |
| **D58** | RELEASED, dispatch after D60 lands | `frontend/data/forecast/` PJM board t1f row; solves | **NO** on `src/`; WS-0 must not touch `program-status.json`. |
| **D63** | queued-named | MISO/CAISO DOF-row identification | no |
| **T3-NYISO-GOLDEN** | HELD (precondition lapsed) | — | no |

**Conclusion: no HOLD is required for any wave-1 lane.** The capx track's live writers are in
`scripts/forecast_verdict.py` and `frontend/data/forecast/`; wave 1's `src/` regions
(`policy/carbon.py`, `policy/cap_and_trade.py`, `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/lp/rows.py`, `model/interchange/spec.py`, `results/export.py|outputs.py|emissions.py`,
`src/market_sim/matrix.py`, `data/datacenter.py`, and the four named `runner.py` /
`scenarios.py` / `constants.py` regions) are unheld. The one live shared surface is the six
matrix shards, written by capx re-scores AND by the owner's backcast lanes several times a day
(`3eaf7918` caiso-252, `fe38a699` nyiso-194 both landed on 2026-09-05) — hence the protocol.

**Issued:** SCN-WS0, SCN-WS1a, SCN-WS2a, SCN-WS3a, SCN-WS4a (§5).
**Cards presented:** D-1, D-2, D-3, D-6.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **SCN-WS0** | Emissions grain (by fuel / by zone / import line / unserved) + multi-metric matrix frame + `report_scenario_deltas.py` + `collate_scenario_campaign.py` + the scenario YAML set + `--set` override + `scenario` registration kind; one paired NEISO T0 to exercise it | **ISSUED r#1** | `claude/scn-ws0-k7m2` | **Opus** | Plan §3 WS-0. Blocks WS-1b, WS-2b, WS-4b/c, WS-5. Sole writer of `configs/scenario_campaign_matrix.yaml` this wave. |
| **SCN-WS1a** | Federal carbon-price semantics (G-C1, gated on D-1) + the two seam defects (G-C2, G-C3) + the pre-declared `CAP-STATE-TIGHT` case | **ISSUED r#1** | `claude/scn-ws1a-p4qd` | **Fable** | Plan §3 WS-1 items 1–3. Item 1 gated: D-1 open at issuance → items 2–3 + the Phase-0 trajectory table + a D-1 evidence memo, then stop. |
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **ISSUED r#1** | `claude/scn-ws2a-t9xb` | **Fable** | Plan §3 WS-2 items 1–2. Its `rows.py:1346` coupling relaxation is WS-3b's precondition. Uses the illustrative target if D-2 is unsigned and says so. |
| **SCN-WS3a** | Voluntary clean-demand **design memo** (no code, no solve) | **ISSUED r#1** | `claude/scn-ws3a-r6vn` | **Fable** | Plan §3 WS-3 item 1. Its signed boxes + card D-3 gate WS-3b. |
| **SCN-WS4a** | DC zone shares for ERCOT + MISO; NEISO `{}` re-check; the D-4 constant-vs-published gap list | **ISSUED r#1** | `claude/scn-ws4a-h3zc` | **Opus** | Plan §3 WS-4 items 2 + 5 only. NOT the named cases (WS-0 owns the YAML this wave), NOT the probes, NOT the adequacy reading (WS-4b, wave 2). |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT T1-F ladder | **QUEUED (wave 2)** | — | Opus | Precondition: WS-0 **and** WS-1a on main. Reduced form (`--set carbon_price_delta=25`) if D-1 is still open. |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `ces_national_clearing.py` | **QUEUED (wave 2)** | — | Opus | Precondition: WS-0 on main. Independent of WS-2a. |
| **SCN-WS4b** | Pre-declared adequacy reading per ISO under LOAD-HI + the LOAD-HI / LOAD-HI-ORGANIC case comments + the "backstop-built" column | **QUEUED (wave 2)** | — | Fable | Precondition: WS-0 on main (it owns `report_scenario_deltas.py` and the campaign YAML). |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F | **QUEUED (wave 2)** | — | Opus | Precondition: WS-0, WS-4a, WS-4b on main. |
| **SCN-WS3b** | Voluntary-demand build | **QUEUED (wave 2)** | — | Fable | Precondition: D-3 ruled YES **and** WS-3a's boxes signed **and** WS-2a on main (no concurrent `rows.py` writer) **and** WS-4a on main. |
| **SCN-WS3c** | Voluntary-demand probe (ERCOT T0 → T1-F) | **QUEUED (wave 3)** | — | Opus | Precondition: WS-3b on main. |
| **SCN-WS5A-\<ISO\>** ×6 + **-SYNTH** | Stage A campaign, T1-F 2026–2030, all six ISOs | **QUEUED (wave 3)** | — | Opus | Precondition: WS-0, WS-1a/b, WS-2a/b, WS-4a/b/c on main; WS-3b/c on main **or** D-3 ruled NO (then VOL-\* and CES-P20+VOL-HI drop, with a ledger note). |
| **Stage B** | Full-horizon legs | **NOT ISSUABLE** | — | — | Needs card D-5 **and** an OPEN §2.1b gate for the named ISO at issuance. At the r#1 pin only NEISO is open. Re-check at issuance, never at planning. |

---

## 2. Owner cards

| card | question | status | recorded ruling |
|---|---|---|---|
| **D-1** | Federal carbon price on a program ISO: **replace** (today), **floor** (`max`), or **additive**? Recommendation: **floor**. | **PRESENTED r#1** | — |
| **D-2** | Campaign levels — carbon paths, CES premium ladder, **CES target schedule + ACP**, voluntary levels, load-high pairing. Recommendation: the plan's §3.5 table. | **PRESENTED r#1** | — |
| **D-3** | Is a voluntary clean-demand **scenario axis** admissible given ffr-5b's inadmissibility ruling on corporate PPA demand as a *driver*? Recommendation: **yes**, as a declared forecast-only publicly-anchored axis. | **PRESENTED r#1** | — |
| **D-4** | Fund the `load-forecast` curated intake? Recommendation: **defer**. | **HELD** — presented with WS-4a's gap list, not before (charter §2). | — |
| **D-5** | Per-campaign §2.1b grant for the NEISO scenario campaign (Stage B). | **HELD** — presented only with Stage A's measured cost table on the dashboard. | — |
| **D-6** | Attribute netting between a federal CES row and a voluntary-demand row. Recommendation: **counts toward**, report both. | **PRESENTED r#1** | — |

Rulings are recorded verbatim and numbered **S1, S2, …** here and appended to the plan's §6 row
as `RULED <date>: …` in the same refresh commit.

---

## 3. Readiness scorecard (the plan's §5.1, kept current here)

State at r#1 = plan v1, unmoved. Each landing lane updates BOTH this table and the plan's §5.1.

| Criterion (plan §1) | Carbon | CES premium | CES target | Voluntary | Load-HI | Emissions |
|---|---|---|---|---|---|---|
| 1 expressible in committed config | yes (semantics defect G-C1) | yes | **no** | **no** | partial — **siting sourced** for ERCOT/PJM/MISO (SCN-WS4a), still **no named case** | — |
| 2 reaches dispatch + deployment | yes | yes | **no** | **no** | yes | — |
| 3 paired probe right-signed, per ISO | NEISO only | ERCOT only (July posture) | **no** | **no** | **no** | — |
| 4 backcast byte-identity | yes | yes | — | — | yes | — |
| 5 matrix duty | stamped | stamped | — | — | stamped | — |
| 6 emissions grain | scalar only | scalar only | — | — | scalar only | **G-E1..E5 open** |
| 7 registered probes on dashboard | NEISO FC-6 pair | pruned (G-S5) | — | — | none | — |

**Open lane assignments against the scorecard:** WS-0 → the Emissions column entire (criterion
6) + criterion 1's harness half; WS-1a → Carbon row 1 (the G-C1 defect) and rows 4/5; WS-1b →
Carbon rows 3/7; WS-2a → the CES-target column rows 1/2/4/5 and its probe half of row 3; WS-2b →
CES-premium rows 3/7; WS-3a → nothing (memo); WS-4a → Load-HI row 1 (partial → the siting half)
— **LANDED 2026-09-05**: MISO populated from the 2026 LTLF regional DC decomposition, ERCOT
verified already-populated (the plan §2.4 "only for PJM" line was stale and is corrected), NEISO
`{}` re-confirmed with its arithmetic; the named case remains SCN-WS4b's and is NOT claimed.
The D-4 gap list is `docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §4, presentable unedited; that
FINDING §6 routes one cache-epoch ledger entry (MISO forecast bundles stale at the same key) that
SCN-WS4a may not write, `results/cache.py` being another lane's region.

---

## 4. Collision register (file → owning lane → wave)

**Wave-1 shared-file protocol** (written verbatim into every wave-1 prompt):

1. `config/scenarios.py` and `runner.py` are touched by WS-1a and WS-2a in the **named disjoint
   regions ONLY**. Any edit outside your region is a **STOP** — route it to SCN-DESK in your
   FINDING; do not widen.
2. The six matrix shards (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`) and
   `docs/codebase-site/data/mechanism-matrix.js`: make the edit your **LAST commit**, after
   `git fetch origin main` + rebase, as **one appended cell line per ISO**, so any conflict is
   one line. This is not advisory — capx D60-R2's re-scores and the owner's backcast lanes
   append to these files several times a day (`3eaf7918`, `fe38a699` both on 2026-09-05).
   Merge order if WS-1a and WS-2a are both ready: **WS-1a first, WS-2a rebases.** CI
   (`scripts/check_mechanism_matrix.py`) enforces that a new `ScenarioConfig` field carries its
   base row + a cell line in every shard **in the same PR** (rule 28 duty c).
3. **Nobody touches `configs/scenario_campaign_matrix.yaml` but WS-0 this wave.**
4. **Nobody touches `frontend/data/forecast/program-status.json`** — it is the capx board,
   written by D60-R2 and D58.

| file / region | owning lane | wave | note |
|---|---|---|---|
| `src/market_sim/results/export.py`, `results/outputs.py`, `results/emissions.py` | SCN-WS0 | 1 | |
| `src/market_sim/matrix.py`, `scripts/collate_full_horizon.py` | SCN-WS0 | 1 | |
| new `scripts/report_scenario_deltas.py`, new `scripts/collate_scenario_campaign.py` | SCN-WS0 | 1 | WS-4b adds the "backstop-built" column to the former **after** WS-0 lands. |
| `scripts/run_full_horizon.py`, `scripts/run_ces_leg.py` | SCN-WS0 | 1 | **the `--set` override ONLY** |
| `scripts/register_forecast_run.py`, the forecast dashboard pages | SCN-WS0 | 1 | NOT `frontend/data/forecast/program-status.json` |
| `configs/scenarios/*`, `configs/scenario_campaign_matrix.yaml` | SCN-WS0 | 1 | sole writer this wave |
| `src/market_sim/policy/carbon.py`, `policy/cap_and_trade.py`, `config/scenario_resolvers.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/interchange/spec.py` — **the one carbon-adder line (~:1931)** | SCN-WS1a | 1 | |
| `runner.py` — **REGION: the `assemble_mc` call site (~:2561-2575)** | SCN-WS1a | 1 | |
| `config/scenarios.py` — **REGION: the D34 guard in `__post_init__` (~:15572)** | SCN-WS1a | 1 | |
| `src/market_sim/results/cache.py` — **one epoch entry** | SCN-WS1a | 1 | |
| `tests/unit/policy/test_cap_and_trade.py`, `test_carbon_price_below_base_guard.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/lp/rows.py` | SCN-WS2a | 1 | WS-3b is the next writer (wave 2), **after** WS-2a merges. |
| `src/market_sim/policy/federal_ces.py`, `policy/clean_tiers.py` | SCN-WS2a | 1 | |
| `runner.py` — **REGION: RPS/clean-row arming + dual plumbing (~:1195-1229, :2851-2864, :4484-4521)** | SCN-WS2a | 1 | |
| `config/scenarios.py` — **REGION: the `federal_ces_*` block (~:3084-3157) + its `__post_init__` guard (~:15584)** | SCN-WS2a | 1 | |
| `docs/codebase/05-policy.md`, `policy/constraints.py` docstring (G-S6) | SCN-WS2a | 1 | |
| `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md` (new) | SCN-WS3a | 1 | memo only |
| `config/constants.py` — **REGION: `DATACENTER_ZONE_SHARE` / `DATACENTER_ADDITIONS_MW` only** | SCN-WS4a | 1 | `VOLUNTARY_*` anchors are WS-3b's separate region, wave 2. |
| `src/market_sim/data/datacenter.py`, `tests/unit/data/test_datacenter.py` | SCN-WS4a | 1 | WS-3b's DC-linked volume helper is the next writer, **after** WS-4a merges. |
| the six matrix shards + `mechanism-matrix.js` | ALL, last commit only | 1–3 | see protocol item 2 |
| `scripts/forecast_verdict.py`, `frontend/data/forecast/program-status.json` | **capx D60-R2 / D58** | — | **no SCN lane may touch these** |

---

## 5. Issuance record

Stems are recorded so a relaunch (`…-r2`) can never collide with the original.

| refresh | lane | model (id) | branch stem issued | data profile | plan §7 body used |
|---|---|---|---|---|---|
| r#1 | SCN-WS0 | **Opus** `claude-opus-5` | `claude/scn-ws0-k7m2` | `neiso` | §7 "WS-0", verbatim |
| r#1 | SCN-WS1a | **Fable** `claude-fable-5-1` | `claude/scn-ws1a-p4qd` | `caiso` | §7 "WS-1a", verbatim + the D-1 gate split (item 1 conditional) |
| r#1 | SCN-WS2a | **Fable** `claude-fable-5-1` | `claude/scn-ws2a-t9xb` | `neiso` | §7 "WS-2a", verbatim |
| r#1 | SCN-WS3a | **Fable** `claude-fable-5-1` | `claude/scn-ws3a-r6vn` | `code` | §7 "WS-3a", verbatim |
| r#1 | SCN-WS4a | **Opus** `claude-opus-5` | `claude/scn-ws4a-h3zc` | `all` | §7 "WS-4" **items 2 and 5 only** (items 1/3/4 split to WS-4b/WS-4c, wave 2) |

### 5.1 Model assignment — the standing rule and the r#1 assignments

**The rule, in force for every SCN lane at every refresh.** Rule 27 `[R-PUSH]` second half: any
session whose scope writes core infrastructure — anything under `src/market_sim/`,
`scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`, `model-methodology-spec.md`, or
`.github/workflows/` — is **Opus or Fable, never Sonnet**. The desk charter tightens this to
**no Sonnet on any SCN lane at all**, docs-only lanes included, so rule 27 is never the binding
constraint here — the plan's own label is. Within Opus/Fable the split follows the director's
r#20 doctrine, restated at plan §3: **`[FABLE]` for structural / adjudication work** (a design
whose shape is still being decided, a semantics change, an argument against a standing ruling)
and **`[OPUS]` for pre-declared execution** (a charter whose deliverables and gates are already
written down and whose job is to carry them out exactly).

| lane | label | model id | why this side of the split |
|---|---|---|---|
| SCN-WS0 | `[OPUS]` | `claude-opus-5` | Execution. Six enumerated deliverables, each with its own commit and its own trivial-first test; the paired T0's gate is arithmetic (by-fuel CO2 sums to `emissions_mt`). Nothing here is a judgment call. Writes `src/` + `scripts/` → rule 27 binds. |
| SCN-WS1a | `[FABLE]` | `claude-fable-5-1` | Adjudication. It changes what an existing registered field *resolves to* on three ISOs, argues the D-1 evidence memo the owner rules on, and must prove byte-identity across every keeper key. Writes `src/` → rule 27 binds. |
| SCN-WS2a | `[FABLE]` | `claude-fable-5-1` | Structural. A new LP row family, a coupling relaxation (`rows.py:1346`) that a later lane inherits, two new fields with a mutual-exclusion guard, and three postures to document. Writes `src/` → rule 27 binds. |
| SCN-WS3a | `[FABLE]` | `claude-fable-5-1` | Pure adjudication — the memo argues, line by line, that a declared scenario axis is a different admissibility class from the driver `ffr-5b` ruled out. Docs-only, so rule 27's letter would permit Sonnet; **the charter forbids it**, and this is the least Sonnet-shaped task in the wave. |
| SCN-WS4a | `[OPUS]` | `claude-opus-5` | Execution. Transcribe published siting geography with citations, hold shares to 1.0, re-check one immateriality arithmetic, enumerate a gap list. Rule 14 provenance work with a fixed shape. Writes `config/constants.py` → rule 27 binds. |

**Queued lanes carry their labels forward** (assigned now so a relaunch cannot drift): SCN-WS1b
Opus, SCN-WS2b Opus, SCN-WS4b **Fable** (it is the adequacy *adjudication* — it pre-declares how
each ISO's high case is read, and pre-declaring a reading is the Fable half of plan §3 WS-4),
SCN-WS4c Opus, SCN-WS3b **Fable** (build-from-a-signed-design, but it is the first writer of a
new mechanism), SCN-WS3c Opus, SCN-WS5A-\<ISO\> ×6 + -SYNTH Opus.

**The desk itself.** The charter assigns **Fable** to SCN-DESK; this session is configured
`claude-opus-5` and the serving model may differ again. Recorded against interest — it is a
divergence from the charter, it affects only adjudication tone and not any lane's assignment,
and a successor desk session should be opened on Fable.

**Splits and gates applied to the plan's §7 bodies (never widenings):**
- WS-1a: plan item 1 is conditional on card D-1 reading FLOOR; unsigned → items 2–3 + the
  Phase-0 trajectory table + the D-1 evidence memo, then stop.
- WS-4: the plan's single §7 "WS-4" prompt is split three ways by the charter's wave plan —
  items 2+5 to **WS-4a** (wave 1), items 1+3 to **WS-4b** (wave 2, Fable), item 4 to **WS-4c**
  (wave 2, Opus) — because items 1 and 4 depend on WS-0's campaign YAML and harness, which do
  not exist yet.
- No other lane's body was edited.
