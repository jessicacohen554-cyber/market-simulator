# SPP Addition Desk — ledger (2026-09)

Canonical live state of the SPP addition program. Plan: `docs/multi-iso/spp-addition-plan-2026-09.md`.
Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`. **This ledger wins where the plan or the
handoff diverge on live state.** One `§0` entry per sitting, newest at top; amendments are appended to
the sitting's entry (`am.1`, `am.2`), never rewritten. Errors are recorded against interest in the entry
that finds them (§6).

---

## 0. Sittings (newest first)

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
| SPP-10 audit + doc 00 fix | W1 | Opus | shared | CHARTERED | — | — | — |
| SPP-11 EPA CAMPD + EIA fetch | W1 | Opus | shared | CHARTERED | — | — | — |
| SPP-12 portal.spp.org + spp.org fetch | W1 | Opus | shared | CHARTERED | — | — | — |
| SPP-20 register (pin flip) | W2 | Fable | shared→spp | CHARTERED · blocked on P1–P8 + G12 | — | — | — |
| SPP-21 matrix shard + §5.7 | W2 | Opus | code | CHARTERED · issuable when the base file is not mid-edit | — | — | — |
| SPP-30 outages + tranches | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-31 benchmarks | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-12 | — | — | — |
| SPP-32 zonal + wind shape + gas hub | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-33 seam derive | W3 | Opus | spp | CHARTERED · blocked on SPP-20, SPP-11 | — | — | — |
| SPP-34 site + docs | W3 | Opus | code | CHARTERED · blocked on SPP-20 | — | — | — |
| SPP-40 first solve → first keeper | W4 | Fable | spp | CHARTERED · blocked on SPP-30/31/32 | — | — | — |
| SPP-51…56 levers | W5 | per plan §8 | spp | RESERVED · blocked on SPP-40 | — | — | — |
| SPP-60 forecast entry | W6 | Fable | spp | ROUTED to capx director (P8) | — | — | — |

---

## 2. Owner rulings (verbatim, numbered)

| # | Date | Question | Ruling (verbatim) | Where it binds |
|---|---|---|---|---|
| O-1 | 2026-09-06 | SPP topology for the first backcast: how many zones? | "Let the Phase-0 data audit decide" | plan §3 card P1 (served at sitting #2 with W1 evidence); no default topology in any charter |
| O-2 | 2026-09-06 | Where should the SPP desk sit relative to the existing directors? | "Standalone SPP desk (Recommended)" | this desk; rulings namespace P; collision register §4 |
| O-3 | 2026-09-06 | Data you cannot fetch from a session — how should the plan handle it? | "The plan should include sessions that fetch the data" | plan §6 (every row is a fetch lane first: SPP-11, SPP-12); manual upload only on a documented block |
| P1–P8 | — | plan §3 | PENDING — due at sitting #2 | — |

---

## 3. Routed / open, not this desk's to fix

| # | Item | Owner | Why it is here |
|---|---|---|---|
| R-a | W6 forecast-program entry for SPP (T1-F, `program-status.json`, `GOLDEN_ISOS`) | capx director (after card P8) | this desk never writes `frontend/data/forecast/` |
| R-b | `complete` marker for SPP holdout years | owner (rule 22) | manifest row 15 deferred; no out-of-training solve chartered |
| R-c | MISO's own SPP seam constants | MISO calibration lane | rule 25; SPP-20 adds SPP's blocks only |
| R-d | rule-28(c) CI enforcement gap | audit track | inherited consequence: read checker output, not exit code |

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

Holds recorded: none.

---

## 5. Issuance record

| Sitting | Lane | Stem issued | Branch realised | Charter location | Note |
|---|---|---|---|---|---|
| — | — | — | — | — | nothing issued at r#0 |

---

## 6. Errors against interest

None yet.
