# FINDING — caiso-255 (closing): the caiso-255 ARM IS SUPERSEDED by the promoted caiso-257 keeper and was ABANDONED mid-solve. One substantive result survives it, and it is a **factual error now propagating through the promoted keeper's durable record**: the ST_GAS bypass covers **76 %** of CAISO's ST_GAS fleet, not "the whole class".

**Session caiso-255, 2026-09-06.** Keeper at close:
**`2026-09-06-caiso-257-b1-ctonly`** (bundle `caiso257_ctonly`), DETERMINATION
**CALIBRATED** — **not this session's run**. Rule 22: 2023–2025 only; no
`complete`/`final` marker; freeze ACTIVE. **No run registered by this session.**

---

## §1 — WHAT HAPPENED, STATED PLAINLY

caiso-255 was granted FINDING-caiso254 §4 **option 1** (CT-only partition
adoption), pre-registered it, built the mechanism, re-fetched the corpus,
re-derived the artifact, ran phase 0, screened 2023, and launched the full
2023–2025 span. **While that solve was running, `main` advanced 232 commits and
session caiso-257 promoted the identical arm** — using *this session's*
`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` as its
pre-registration and citing this session's P-3 verification.

**The solve was therefore killed mid-flight and its bundle deleted.** It was
reproducing an already-promoted result against a **stale control**
(`caiso252_b1_notrim` is no longer the keeper), so G-CTRL form 4 no longer held
for it. **The process error is mine and is recorded as such: `main` was not
re-checked before an LP was launched.** A 45-minute solve was spent on a
superseded object. The rule that would have caught it is not a new one — it is
simply re-reading the keeper shard at launch.

The screen bundle was deleted per rule 29(c); the abandoned arm bundle was
deleted with it. Every number either produced is in this document.

### §1.1 — What this session's work DID contribute, and what it did not

**Contributed** (all merged and in use by caiso-257):
* the `--st-split-report-only` mechanism in `derive_caiso_offer_surface.py` —
  three-way CLASSIFICATION, two-way CONSUMPTION, with the refused class
  published under `_provenance.reported_not_consumed`;
* the derive's **corpus-coverage guard**, which caiso-254 had added to the
  probe but not to the writer;
* the PRECOMMIT that caiso-257 promoted under, including the ex-ante
  registration that the promotion basis contains **no price**;
* the consolidated **G-DRIFT input-identity** instrument (`fa23c1f7` → HEAD,
  every LP input bit-identical, measured by two `fleet_only` rebuilds from a
  sparse worktree).

**Did NOT contribute:** a run. **Zero registered runs, zero keeper change.**
The artifact this session independently re-derived is **byte-identical on the
consumed bands** to the one on `main` (CT_PEAKER 1.103 / 1.146 / 1.154), which
is corroboration — two independent OASIS fetches and two independent store
builds agreeing to the digit — and nothing more.

---

## §2 — THE SURVIVING RESULT: P-5 IS FALSIFIED, AND THE PROMOTED KEEPER'S NOTE REPEATS THE WITHDRAWN CLAIM

`PRECOMMIT-caiso255` **P-5** predicted *"zero ST_GAS tranches move"*, on the
strength of caiso-254 §3's execution proof. **It is FALSIFIED**, measured on
the screen year:

| class | tranches | **moved** | F share |
|---|--:|--:|--:|
| CT_PEAKER | 828 | 784 | 11,801.4 |
| CT_CHP | 195 | 147 | 935.2 |
| **ST_GAS** | **25** | **14** | **1,829.7** |
| CC_REGULAR / CC_CHP / non-gas | 614 | **0** | 0.0 |

**The bypass itself is exactly as caiso-254 proved** — all nine tranches of
plants 315 / 335 / 350 move by **exactly 0.0000**. What is wrong is the *set's
claimed extent*:

| plant | MW | in `ST_GAS_PEAKER_PLANTS` | max Δmc |
|---|--:|:--:|--:|
| 315 AES Alamitos | 1,142.0 | YES | 0.0000 |
| 335 AES Huntington Beach | 225.8 | YES | 0.0000 |
| 350 Ormond Beach | 1,491.0 | YES | 0.0000 |
| **356** (LA_BASIN) | **830.1** | **NO** | **$4.4475** |
| **10446** (ZP26) | **88.2** | **NO** | **$2.3564** |

> **CAISO ST_GAS in the LP = 3,777.1 MW, of which 2,858.8 MW (75.7 %) is
> bypassed and 918.3 MW (24.3 %) is NOT.**

The origin of the error is precise and checkable: `bin_assignments_CAISO.csv`
— the derive's fleet-geometry source — has **exactly three** ST_GAS rows
(315/335/350, read and confirmed this session). The **LP** builds ST_GAS from
the CAMPD per-plant binning and carries **five** plants. caiso-254 §3 read the
first and described the second.

### §2.1 — WHERE THE WITHDRAWN CLAIM IS STILL LIVE ON `main`

The correction was merged as
`ADDENDUM-caiso255-p5-falsified-stgas-reach-2026-09-06.md` **before** caiso-257
promoted. It was not picked up. Checked at `origin/main`: **no CAISO session
256, 257, 258 or 259 cites P-5, p356, p10446, or the 918.3 MW.** The claim is
still asserted in:

* **`frontend/data/backcast/keepers/CAISO.json`**, the promoted keeper's note —
  *"caiso-254 sec 3 proved by execution that no ST_GAS band reaches a CAISO
  plant either way (offer_curves.py:259/:318 bypass)"*;
* `FINDING-caiso257-ctonly-promotion-2026-09-06.md`, which carries it forward.

### §2.2 — WHAT IT DOES AND DOES NOT AFFECT

**IT DOES NOT CHANGE THE DETERMINATION, AND NO GATE MOVES.** The caiso-257
promotion basis is **G-BIMODAL + the G1 capacity reconciliation** (CT bucket
1.306 → 0.970), registered ex ante and containing no price and no ST_GAS reach
term. The keeper is CALIBRATED on 8/8 scored criteria and stays so. **Nothing
here is a reason to re-open it.**

**What it changes is what the record may CLAIM**, and the correction runs in
the keeper's favour — which is why it is stated carefully rather than quietly:

* the note uses the inertness claim to argue the ST_GAS omission is
  **harmless**. The measured truth is **stronger**: the separated ST_GAS bucket
  fails G4 with `peak` 1.196 inverted **0.350 below** `econ_high` 1.546, and
  those bands **would have reached 918.3 MW of real steamers**. Option 1 is
  therefore not a cosmetic omission — **it is the leg that keeps an inverted
  offer curve out of the LP**;
* a **third, independent defect** in the ST_GAS bucket, orthogonal to the G4
  inversion: the derive's G1 reconciles it against `fleet_mw` **2,858.8 MW**,
  the three-plant figure, when the LP class is **3,777.1 MW**. The ratio
  **0.895 that PASSED G1 is measured against a fleet definition omitting 24 %
  of what the bands would price.** Had the bucket been consumed, that would
  have gone unnoticed.

---

## §3 — QUEUE (for the next CAISO session)

1. **Correct the propagated claim** in `keepers/CAISO.json` and
   `FINDING-caiso257-ctonly-promotion` — the bypass covers 76 % of the class,
   not all of it. Not done here: the CAISO keeper shard is being actively
   edited by the 256–259 lane, and a cross-lane shard edit mid-flight is how
   conflicts get made. It is a note correction, **not** a re-determination.
2. **The ST_GAS G1 denominator** (2,858.8 vs 3,777.1 MW) is a real derive
   defect and needs its own pre-registration before anything is changed.
3. Carried unchanged: the `complete` marker (owner act, raised not granted);
   the **CAISO-side P1-basis-seed neutrality A/B** — the seed is default-ON for
   every ISO's next *CLI* calibration solve and is validated on ERCOT alone;
   the stale `program-status.json` CAISO keeper stamp (ask before touching);
   the C3a weight basis; the per-zone storage/class sidecar; the DMM 2025
   RA-import basis; Panoche.

---

## §4 — DO-NOT-REDO ADDS

1. **Re-read the ISO's keeper shard on `main` immediately before launching any
   LP.** This session spent a full-span solve on an object another session had
   already promoted. The check costs one command.
2. **Never write a wait loop as `pgrep -f <pattern>` where `<pattern>` appears
   in the loop's own command line.** It matches itself and never exits. It cost
   this session hours of idle time across three separate occurrences; watch a
   captured PID with `kill -0` instead.
3. **The ST_GAS bypass is NOT the ST_GAS class** — 76 %, not 100 %. Do not
   re-assert LP-inertness for CAISO ST_GAS bands without re-deriving the reach
   from the LP fleet rather than from `bin_assignments_CAISO.csv`.
4. caiso-254 §6 and its predecessors stand in full.
