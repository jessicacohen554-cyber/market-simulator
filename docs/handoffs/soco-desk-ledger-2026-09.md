# SOCO Addition Desk — ledger (2026-09)

The live record of the SOCO addition program. **This ledger wins where it and
`docs/multi-iso/soco-addition-plan-2026-09.md` diverge on live state**; the plan owns the charters
(§8) and the decisions (§3), this owns who is running what.

Refresh discipline: one refresh = one §0 entry = one ledger commit = one small PR, off a branch
recreated fresh from `origin/main`.

---

## 0. Live state — newest entry FIRST

### r#1 — 2026-09-13 — W1 ISSUED (main `2c2fc065`)

**What happened.** The owner directed the desk to issue the first wave. Charters **SOCO-10**,
**SOCO-11** and **SOCO-12** were issued verbatim from plan §8 W1, each with §8.0's collision rules
pasted in and `origin/main` pinned at **`2c2fc065`**. The charter commit `6f2dbe23` is **on main**,
so every lane reads the plan, the handoff and this ledger from `origin/main` — no lane needs a
branch reference.

**SOCO-13 (the FERC-EQR price index) was NOT issued** and is held exactly where plan §5 puts it:
behind owner card **S2**. Issuing it unruled would have a `[FABLE]` lane construct the benchmark
every later price criterion is scored against, before the owner has said whether that benchmark is
wanted or what a SOCO run may be called without one. The desk declines to pre-empt the card.

**Cards S1 and S2 were served to the owner at this sitting** (plan §3; sitting #1 is where they are
due). Status: **PENDING** until ruled — recorded in §2, not assumed here.

**Collision check before issuance** (handoff §0.4). The surfaces the three W1 lanes own were checked
at the pin: `data/raw/campd-unit-level/`, `data/raw/zone-specific-demand/`,
`scripts/data/fetch_campd_unit_level.py`, `scripts/data/fetch_eia930_interchange.py`,
`docs/multi-iso/00-iso-addition-protocol.md` — the most recent commit touching any of them is
`db5f11ea` (PR #6000, PJM-H1), which is well behind the pin and is not a live lane. **No hold.**
The three lanes are file-disjoint from each other by construction (plan §5 FILES YOU OWN), so they
run in parallel.

**Gates:** not re-run — this refresh commits one ledger entry and touches no code, data or registry,
so every gate's input is unchanged since r#0. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #2 — grade SOCO-10/11/12 BY CONTENT (open each FINDING; never grade on
absence or on a green CI check), then serve cards S3–S9 with W1's evidence, then issue W2.

---

### r#0 — 2026-09-12 — CHARTER (main `ab1267e9`)

**What happened.** The owner asked for a plan and prompt pack to add "whatever ISO Hillabee gas
plant in Alabama is in", using the SPP addition workstream as the reference. The chartering session
measured the answer rather than assuming it: Hillabee Energy Center is EIA plant **55411**,
Tallapoosa County AL, 822.8 MW across three CC generators, balancing authority **`SOCO`** (Southern
Company Services, Inc. - Trans), NERC region SERC — **not an RTO/ISO**. The program is therefore the
addition of a **balancing authority** as the eighth registered region.

**Committed at charter:** `docs/multi-iso/soco-addition-plan-2026-09.md`,
`docs/handoffs/soco-desk-handoff-2026-09-12.md`, this ledger. Nothing else. No code, no data, no
registry touched.

**Measured in the charter session** (plan §2 carries all of it with its provenance; do not
re-derive):

| Fact | Value |
|---|---|
| Fleet, BA `SOCO`, EIA-860 operable | 335 plants · 786 generators · **70,665.7 MW** nameplate |
| By state | GA 41,284.4 · AL 24,494.0 · MS 4,577.7 · FL 309.6 · **MA 1.5 (a source defect — SOCO-10 adjudicates)** |
| By technology (top) | CC 20,702.8 · coal 12,234.7 · CT 11,676.8 · nuclear 8,282.4 · solar 5,825.9 · gas ST 3,839.2 · hydro 3,317.6 · PS 1,306.6 · **CAES 110.0** |
| EIA-930 `SOCO hourly.parquet` | 26,304 rows, 2023-01-01 → 2025-12-31 UTC; 8760 / 8784 / **8753** local-date hours |
| Demand | **229.47 / 239.33 / 239.36 TWh** (2023/24/25) |
| Net position | **net EXPORTER, 10.2 / 10.8 / 13.0 TWh/yr** |
| Nuclear energy | 52.4 → 63.0 → 64.2 TWh — the Vogtle 3 (2023-07) and Vogtle 4 (2024-04) commissionings, both mid-window |
| CAMPD CEMS | **AL and GA ABSENT**; MS present 2019–2026 |
| EIA-930 sub-BAs | **SOCO has none** (the product covers CISO/ERCO/ISNE/MISO/NYIS/PJM/PNM/SWPP only) |
| Probes | EPA CAMPD bulk **200** anonymous (187 MB/state-year) · PUDL FERC-714 parquet **206** · `ferc.gov` **403** · FERC EQR viewer **200** · SEEM site **200** · no `EIA_API_KEY` in the container |

**The program's defining problem, stated at charter so it is never discovered late:** Southern
Company publishes **no LMP, no day-ahead clearing price and no hourly index**, and SEEM publishes
matched volumes but **no price**. Three of the rubric's load-bearing criteria (C3a/C3b/C3c) score
against a committed hourly price series. Card **S2** is the only route to resolving that, and it is
due at **sitting #1**.

**Gates run at charter:** none — the charter commit touches no code, no data and no registry, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #1 — serve cards **S1** (the registry key) and **S2** (the price / rubric
card) to the owner via AskUserQuestion, then issue W1 (SOCO-10/11/12; SOCO-13 only if S2 rules for
option (a)).

---

## 1. Scoreboard

| Lane | Model | Wave | Status | Branch | FINDING |
|---|---|---|---|---|---|
| SOCO-10 audit | OPUS | W1 | **ISSUED r#1** | pending dispatch | — |
| SOCO-11 CEMS + FERC-714 + interchange | OPUS | W1 | **ISSUED r#1** | pending dispatch | — |
| SOCO-12 documents + gas | OPUS | W1 | **ISSUED r#1** | pending dispatch | — |
| SOCO-13 EQR price index | FABLE | W1 | **HELD r#1 — blocked on card S2, deliberately not issued** | — | — |
| SOCO-20 registration | FABLE | W2 | BLOCKED on S1/S3–S8 + LTLF | — | — |
| SOCO-21 matrix shard | OPUS | W2 | BLOCKED on collision check | — | — |
| SOCO-30/31/32/33/34 | OPUS | W3 | BLOCKED on SOCO-20 | — | — |
| SOCO-40 first solve | FABLE | W4 | BLOCKED on SOCO-30/31/32 | — | — |
| SOCO-54/55/56/57 levers | — | W5 | pre-declared, not issuable | — | — |
| W6 forecast entry | — | W6 | ROUTED to the capx director (card S10) | — | — |

## 2. Owner rulings — verbatim, numbered

| # | Card | Ruling | Date |
|---|---|---|---|
| O-1 | charter | *"Use the add spp workstream as a reference and develop a plan and prompt pack to do whatever iso Hillabee gas plant in Alabama is in."* | 2026-09-12 |
| S1 | the registry key | **SERVED r#1, PENDING** | 2026-09-13 |
| S2 | price benchmark / rubric class | **SERVED r#1, PENDING** — the program's load-bearing decision; SOCO-13 is held until it is ruled | 2026-09-13 |
| S3–S9 | topology, seams, VOLL, adequacy, CAES, Vogtle vintage, tail threshold | **PENDING** — due sitting #2 | — |
| S10 | W6 routing | **PENDING** — due when a keeper exists | — |

## 3. Routed — open, not this desk's to fix

| # | Item | Owner | Why it stays visible |
|---|---|---|---|
| R-a | The rubric cannot express a determination for a region with no price benchmark | the owner (card S2 option b) | A keeper solved before it is ruled cannot be scored |
| R-b | The NWPP program shares card S2's problem in a milder form (WEIM prices exist). The rubric question should be ruled ONCE for both | the owner | Two desks asking the same question twice invites two different answers |

## 4. Collision register

| # | Surface | Other writer | Action |
|---|---|---|---|
| C-1 | `config/capacity_market.py`, `config/constants.py`, `model/interchange/spec.py` | capx D-lanes, the SCN desk, the per-ISO calibration lanes | SOCO-20 rebases last and appends; the desk re-checks their ledgers' top entries at issuance |
| C-2 | `docs/codebase-site/data/mechanism-matrix.js` (base file) | every ISO's lanes, whenever a field is added | SOCO-21 is issued only after the desk verifies nobody is mid-edit |
| C-3 | W1 lane surfaces (`campd-unit-level/`, `zone-specific-demand/`, the two fetch scripts, doc 00) | — | **CHECKED CLEAR at r#1**, pin `2c2fc065`: last touch `db5f11ea` (PR #6000), not a live lane. No hold |

## 5. Issuance record

| Sitting | Date | Lanes issued | Cards served |
|---|---|---|---|
| r#0 | 2026-09-12 | none (charter commit) | none |
| r#1 | 2026-09-13 | **SOCO-10, SOCO-11, SOCO-12** (plan §8 W1, verbatim, pinned `2c2fc065`). SOCO-13 HELD on card S2 | **S1, S2** |

## 6. Errors against interest

*(The desk records its own mistakes here, in its own words, so the next refresh does not repeat
them. Empty at charter.)*
