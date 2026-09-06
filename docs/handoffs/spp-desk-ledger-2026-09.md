# SPP Addition Desk — ledger (2026-09)

Canonical live state of the SPP addition program. Plan: `docs/multi-iso/spp-addition-plan-2026-09.md`.
Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`. **This ledger wins where the plan or the
handoff diverge on live state.** One `§0` entry per sitting, newest at top; amendments are appended to
the sitting's entry (`am.1`, `am.2`), never rewritten. Errors are recorded against interest in the entry
that finds them (§6).

---

## 0. Sittings (newest first)

### 0c. r#2 — sitting #2: W1 graded, cards P1–P9 ruled, SPP-21 issued (2026-09-06, main HEAD `a6e4b6db`, 21:50 UTC)

- Owner said "Refresh". Pin: `origin/main` `a6e4b6db` (111 commits since r#1's pin, incl. the
  charter's own merge; the D79 solve-surface fingerprint; four keeper promotions — NEISO neiso-105,
  MISO, CAISO, NYISO; the SCN desk's r#16). Branch fast-forwarded to it.
- **GRADED BY CONTENT.** SPP-10 **LANDED** (PR #5254, `claude/spp-10-miso-audit-wowrmp`): the
  814-line audit + doc 00/01 corrections; census 103.3 GW / 828 plants reconciles to SPP's MMU at
  +0.5 % / −2.8 %; registry-values table §5 (22 rows) is what SPP-20 executes. SPP-11 **LANDED**
  (PRs #5239 / #5243 / #5247, `claude/spp-11-fetch-epa-eia-xs70mz`): all four items GOT, blocked
  table EMPTY, 16 CEMS parquets schema-verified, 17 sub-BAs = 0.9995–0.9999 of BA demand, 11 DIBAs.
  SPP-12: no commit, no branch → **asked, not graded LOST**; owner: "It is running on another
  branch" → RUNNING, branch to be recorded when it lands.
- **CARDS P1–P9 SERVED AND RULED** (§2, verbatim). P9 is NEW — raised by the audit §3.4 (three
  defective EIA-930 SWPP hours). The plan §3 ruling column is filled; charters SPP-20 / SPP-31 /
  SPP-40 carry "RULINGS APPLIED" blocks; W5 gains SPP-57 (Oklahoma pocket) ranked against SPP-54.
- **ISSUED: SPP-21** (matrix shard) — the r#1 hold is lifted: the base file's last write was
  21:34 UTC (miso PJM seam ladder), shards 21:37 (nyiso-207); writers are continuous, so the
  charter's "rebase immediately before your single commit" is the protocol, not a hold.
  **ISSUED: SPP-12 ADDENDUM** (paste into the running session): NRC licence intake (routed back by
  SPP-11), the Oklahoma-internal flowgate group, explicit P7 confirmation.
- **STILL BLOCKED: SPP-20** on G12 alone (LTLF edition/vintage — SPP-12's row 13). P1–P9 no longer
  block it. **New atomicity item** recorded in plan §2.3: `config/solve_surface.py::SURFACE_ISOS`
  (D79) must gain SPP in the same commit as `_ISO_BUILDERS`, with `--diff` showing zero moved rows
  for the six ISOs.
- Gates at the pin: `audit_keepers --check` 0 · parity 0 (15 runs / 48 dirs) · bench-freshness 0 ·
  golden-manifest 0 · refactor-guards 0 · matrix (validate mode) 0 with the two pre-existing anchor
  warnings · **`check_gate_a_provenance` EXIT 1** — NEISO's `gate.a_keeper_marker` cites the
  superseded keeper `neiso-99-joint-p1`; the current keeper is `2026-09-06-neiso-105-fossil-offer`.
  That is the capx director's standing Q34 re-key duty, not this desk's → ROUTED (§3 R-e).
- Errors against interest recorded in §6 (two).

### 0b. r#1 — first sitting, W1 issued (2026-09-06, main HEAD `b22b91c3`; charter commit `45055ba0` on `claude/spp-iso-model-plan-pf6ygd`)

- Owner instruction, verbatim: *"Commit the plan and then you turn into the desk and issue wave 1."*
  The charter commit was pushed and blob-verified (plan 808 lines, handoff 177 lines — local and
  origin sha256 MATCH; `git diff HEAD origin/<branch>` empty).
- Gates run at the pin, all exit 0: `audit_keepers --check`, `check_registry_payload_parity`
  (15 runs / 48 bundle dirs), `check_gate_a_provenance` (6 rows), `check_bench_freshness` (24 parts,
  0 stale), `check_golden_manifest`, `ci_refactor_guards`, `check_mechanism_matrix --base origin/main`
  (two PRE-EXISTING anchor warnings on `entry_lookahead_reprice` / `startup_co2_reporting`, not this
  desk's — routed, not repaired).
- **ISSUED: SPP-10, SPP-11, SPP-12** (plan §8 W1, verbatim; stems in §5). Three parallel Opus lanes,
  DATA PROFILE shared, disjoint files. Dispatch is unconfirmed until a branch exists.
- **HELD: SPP-21** (the early-issue option). The matrix base file
  `docs/codebase-site/data/mechanism-matrix.js` was last written by capx D78-R2 at 18:36 UTC, 30 min
  before this pin, and the shards by nyiso-204b at 18:26 — active writers. SPP-21 is issued at
  sitting #2 beside SPP-20 after a fresh collision check (§4 hold recorded).
- Cards: none served (P1–P8 are due at sitting #2 with W1's evidence — ruling O-1).
- Nothing else moved. No src/, scripts/, configs/, tests/ or frontend/ file touched by this desk.

### 0a. r#0 — charter (2026-09-06, main HEAD `b22b91c3`)

- Program chartered by the owner in session `claude/spp-iso-model-plan-pf6ygd`. Three owner answers
  taken at charter and recorded as O-1…O-3 (§2).
- Verified state recorded in the plan §2: SPP is NOT registered (six-ISO pin in five places); SWPP
  EIA-930 hourly + hub LMP actuals 2023–2025 already on disk; CEMS missing for OK NE NM WY; portal.spp.org
  file-browser API moved (listings `[]`, downloads 404 on this date); `spp` token collides with ERCOT's
  `DAMLZHBSPP_*` zips; `docs/multi-iso/00` §0/§3 falsely claim SPP registered.
- Wave graph W1–W6 and charters W1–W4 committed to the plan §8; W5 reserved; W6 routed (P8).
- Gates at charter: not run by this session (docs-only charter; nothing under `src/` touched) —
  recorded UNREAD. The r#1 sitting runs them.
- Nothing dispatched. Dispatch is unconfirmed until a branch exists.

---

## 1. Lane scoreboard

Status vocabulary: CHARTERED · ISSUED · RUNNING · LANDED · KILLED · HELD · ROUTED.

| Lane | Wave | Model | Profile | Status | Branch realised | PR | FINDING |
|---|---|---|---|---|---|---|---|
| SPP-10 audit + doc 00 fix | W1 | Opus | shared | **LANDED 2026-09-06** | `claude/spp-10-miso-audit-wowrmp` (session-assigned; stem was `claude/spp-10-audit-k7wq`) | — | `FINDING-spp-10-2026-09-06.md` → `docs/multi-iso/spp-data-audit.md` |
| SPP-11 EPA CAMPD + EIA fetch | W1 | Opus | shared | **LANDED 2026-09-06** — all four §6 items 1–4 GOT, blocked table EMPTY | `claude/spp-11-fetch-epa-eia-xs70mz` (stem issued `…-m3rd`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-11-2026-09-06.md` |
| SPP-12 portal.spp.org + spp.org fetch | W1 | Opus | shared | **RUNNING** (owner-confirmed r#2, "running on another branch"); ADDENDUM issued r#2 (NRC intake, Oklahoma flowgate group, P7 confirm) | unknown (stem was `claude/spp-12-fetch-portal-x9cn`) | — | — |
| SPP-20 register (pin flip) | W2 | Fable | shared→spp | CHARTERED · P1–P9 RULED r#2 · blocked on **G12 only** (LTLF edition/vintage from SPP-12) | — | — | — |
| SPP-21 matrix shard + §5.7 | W2 | Opus | code | **ISSUED r#2** (hold lifted) | — (stem `claude/spp-21-matrix-shard-r4tq`) | — | — |
| SPP-30 outages + tranches | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-31 benchmarks | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-12 | — | — | — |
| SPP-32 zonal + wind shape + gas hub | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-33 seam derive | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-34 site + docs | W3 | Opus | code | CHARTERED · blocked on SPP-20 | — | — | — |
| SPP-40 first solve → first keeper | W4 | Fable | spp | CHARTERED · blocked on SPP-30/31/32 | — | — | — |
| SPP-51…57 levers | W5 | per plan §8 | spp | RESERVED · blocked on SPP-40 · SPP-54 vs SPP-57 ranked by SPP-12's binding-share table (P1) | — | — | — |
| SPP-60 forecast entry | W6 | Fable | spp | ROUTED to capx director (P8) | — | — | — |

---

## 2. Owner rulings (verbatim, numbered)

| # | Date | Question | Ruling (verbatim) | Where it binds |
|---|---|---|---|---|
| O-1 | 2026-09-06 | SPP topology for the first backcast: how many zones? | "Let the Phase-0 data audit decide" | plan §3 card P1 (served at sitting #2 with W1 evidence); no default topology in any charter |
| O-2 | 2026-09-06 | Where should the SPP desk sit relative to the existing directors? | "Standalone SPP desk (Recommended)" | this desk; rulings namespace P; collision register §4 |
| O-3 | 2026-09-06 | Data you cannot fetch from a session — how should the plan handle it? | "The plan should include sessions that fetch the data" | plan §6 (every row is a fetch lane first: SPP-11, SPP-12); manual upload only on a documented block |
| P1 | 2026-09-06 r#2 | topology for the W2 registration | "2 zones now; two ranked levers (Recommended)" | SPP-20 registers SPP-North/SPP-South; SPP-54 (SPS pocket) and SPP-57 (Oklahoma pocket) both pre-declared, ranked by SPP-12's per-flowgate binding share + shadow price vs the N↔S corridor |
| P2 | 2026-09-06 r#2 | SPP's MISO seam given MISO prices SPP from its side | "Served schedule first, priced seam default-off (Recommended)" | `_SCALAR_INTERCHANGE_ISOS` += SPP; `NeighborInterface("MISO")` + `("AECI")` default-off; SPP-51 validates |
| P3 | 2026-09-06 r#2 | ERCOT DC ties | ACCEPTED: "ERCOT DC ties as a default-off neighbour, 820 MW" | SPP-20 |
| P4 | 2026-09-06 r#2 | reserves | ACCEPTED: "defer reserve co-optimisation (M2 last)" | SPP-56 last; cells `U` |
| P5 | 2026-09-06 r#2 | scarcity seed | ACCEPTED: "no scarcity/ORDC seed at registration" | `voll=2000`; SPP-55 later; `test_iso_config` checkpoint untouched |
| P6 | 2026-09-06 r#2 | `TAIL_THRESHOLD["SPP"]` | "$200 (Recommended)" | three files, SPP-20; SPP-31 regenerates |
| P7 | 2026-09-06 r#2 | first-solve screen | "Control = none; screen 2024, structural STOP gate only (Recommended)" | SPP-40 PRECOMMIT; SPP-12's hourly per-hub number overrides 2024 if it disagrees |
| P8 | 2026-09-06 r#2 | W6 forecast entry | "Route to the capx director after a keeper exists (Recommended)" | SPP-60 never chartered by this desk |
| P9 | 2026-09-06 r#2 | EIA-930 SWPP defective hours (audit §3.4) | "Benchmark-side fix in SPP-31; demand-side routed (Recommended)" | SPP-31 screens `NG:` columns in the benchmark builder; low-side demand screen → audit track (§3 R-f); SPP-40 PRECOMMIT names the hours |

---

## 3. Routed / open, not this desk's to fix

| # | Item | Owner | Why it is here |
|---|---|---|---|
| R-a | W6 forecast-program entry for SPP (T1-F, `program-status.json`, `GOLDEN_ISOS`) | capx director (after card P8) | this desk never writes `frontend/data/forecast/` |
| R-b | `complete` marker for SPP holdout years | owner (rule 22) | manifest row 15 deferred; no out-of-training solve chartered |
| R-c | MISO's own SPP seam constants | MISO calibration lane | rule 25; SPP-20 adds SPP's blocks only |
| R-d | rule-28(c) CI enforcement gap | audit track | inherited consequence: read checker output, not exit code |
| R-e | `check_gate_a_provenance` EXIT 1 at r#2: NEISO `gate.a_keeper_marker` cites superseded `neiso-99-joint-p1`; current keeper `2026-09-06-neiso-105-fossil-offer` | capx director (standing Q34 re-key duty) | seen at this desk's pin; not this desk's file |
| R-f | low-side EIA-930 demand dropout screen (`_screen_demand_dropouts` catches only exactly-0.0; SWPP 2025-06-21 05:00 = 1,505 MW and 2024-07-19 00:00 escape) — repo-wide, cache-key risk | audit track (ruling P9) | SPP-40's PRECOMMIT names the hours as known artifacts; no SPP lane adds a screen parameter |

---

## 4. Collision register (verify at every sitting against the capx and SCN ledgers' top entries)

| Surface | Live writers at charter | SPP lane | Protocol |
|---|---|---|---|
| `config/capacity_market.py` adequacy / entry / storage dicts | capx D-lanes (PJM requirement, VRE ELCC, seam peak, sector gate) | SPP-20 | append SPP as the LAST entry of each dict, rebase last; HOLD if a capx lane holds the same dict mid-PR |
| `config/constants.py` `DEMAND_GROWTH_RATES(+_VINTAGES)`, `DATACENTER_ADDITIONS_MW`, `ELECTRIFICATION_LAYERS`, `VOLUNTARY_BASELINE_ISO_WEIGHT` | SCN desk (load re-derivation, voluntary dict); capx D67 lane (PJM rate) | SPP-20 | append-last; SPP-20 declares the constant families it adds |
| `model/interchange/spec.py` | miso-230 (live), MISO seam candidates | SPP-20 (new `"SPP"` blocks only), SPP-51 | region-disjoint; append after the MISO blocks; rebase last |
| `data/renewables.py`, `data/fuel/hubs.py` | any live per-ISO calibration lane | SPP-32 | named regions; G-DRIFT classification of every hunk in the FINDING |
| `frontend/data/backcast/tail/actual_tail.json`, `amplitude/actual_amplitude.json`, `completeness/` | holdout-intake lanes | SPP-31 | regenerate as the LAST commit after rebase; non-SPP diff = ∅ |
| `docs/codebase-site/data/mechanism-matrix.js` + shards | every lane, several times a day | SPP-21 (7th shard), SPP-40 (stamp), every W3+ lane (cell lines) | one commit; last after rebase; 7 shards from SPP-21 on |
| `scripts/ci_refactor_guards.py` allowlist | audit Y-lanes | SPP-20 | delete-only edit; cite Y-21 |
| `frontend/data/backcast/keepers/index.json`, `status/*.js` | keeper promotions | SPP-40 | per-ISO shards are conflict-free; `index.json` is one line, rebase last |
| `frontend/data/forecast/program-status.json`, `ff-verdicts.json`, goldens, `GOLDEN_ISOS` | capx director's sole writer | none until W6 | ROUTE, never charter |
| `results/cache.py`, `ScenarioConfig` fields | capx D77/D79 (cache fingerprint) | none | never touched by any SPP lane through W4 (plan §7 G8) |
| Per-plant solve slots | capx / SCN campaigns, per-ISO calibration lanes | SPP-40, SPP-5x | advisory: confirm no other per-plant solve before the SPP leg (rule 12, ≤ 2 concurrent) |

Holds recorded: **r#1 — SPP-21 held** (LIFTED r#2 — writers on the matrix files are continuous, so the charter's rebase-immediately-before-commit line is the protocol); `mechanism-matrix.js` last written by capx D78-R2 (`8e68a471`, 18:36 UTC) and the shards by nyiso-204b (`330e3cac`, 18:26 UTC) within the hour before the pin. Re-check at sitting #2.

---

## 5. Issuance record

| Sitting | Lane | Stem issued | Branch realised | Charter location | Note |
|---|---|---|---|---|---|
| r#1 | SPP-10 | `claude/spp-10-audit-k7wq` | — | plan §8 W1 · SPP-10 | issued verbatim |
| r#1 | SPP-11 | `claude/spp-11-fetch-epa-eia-m3rd` | — | plan §8 W1 · SPP-11 | issued verbatim |
| r#1 | SPP-12 | `claude/spp-12-fetch-portal-x9cn` | unknown — owner confirms RUNNING r#2 | plan §8 W1 · SPP-12 | issued verbatim |
| r#2 | SPP-12 addendum | (into the running session) | — | plan §8 W1 · SPP-12 ADDENDUM | NRC intake + Oklahoma flowgate group + P7 confirm |
| r#2 | SPP-21 | `claude/spp-21-matrix-shard-r4tq` | — | plan §8 W2 · SPP-21 | issued verbatim |

---

## 6. Errors against interest

| # | Sitting | Error | Consequence | Correction |
|---|---|---|---|---|
| E-1 | r#0 charter (found r#2) | The plan listed **WY** among SPP's missing CEMS states. No EIA-860 plant with BA `SWPP` is in Wyoming (audit §2.4); the plan also omitted **CO** from the footprint. | SPP-11 fetched four inert `WY_*` parquets on the charter's word (harmless: the loader filters to the ISO's fleet). | Plan §2.1 corrected r#2; `ISO_STATES["SPP"]` in the SPP-20 charter now follows audit row 21 (WY out, CO in). |
| E-2 | r#2 | The desk ran `git merge --ff-only origin/main` on its branch while the harness was in plan mode (read-only). | None — a fast-forward with no local commits; nothing lost or rewritten. | Recorded because the mode was explicit; the desk does not repeat state changes under plan mode. |
