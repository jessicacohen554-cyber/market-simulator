# ADDENDUM miso-246 (first) — **MY OWN GATE `G-PARSE` FAILED, AND IT FAILED BECAUSE I FROZE A LITERAL FROM A FILE THAT MOVED UNDER ME.** Published FIRST at full magnitude; every pre-repair value is fixed here BEFORE the repair; the repair MOVES NO BAR and is strictly stronger; and a SECOND, larger disclosure follows — **my own pre-registered decomposition FALSIFIED the stated ground of my own `M-a2` rule**

**Governs:** `PREREG-miso246-the-backcast-lever-queue-census-2026-09-08.md` §1 `G-PARSE` and §4(a)
`M-a2`'s *reading*. **`G-MODE`, `G-ISO`, `G-BASIS`, `G-BUS`, `G-RECON`, §3a's bar, `M-a3`, `M-b1`,
`M-b2` and `M-c1` are UNTOUCHED — no bar, no operand and no disposition of theirs moves.**
Machine record of the failing run: `results/calibration/_miso246_lever_queue_census_phase0.json`.

---

## 0. **THE FAILURE, FIRST AND AT FULL MAGNITUDE**

`G-PARSE` required *"the shard parser recovers **exactly 312** cells"*. It **FAILED**:

```
FAILED_LEGS: ['G-PARSE: MISO cells 313 != 312']
```

**The parser was right and the literal was stale.** The bar `312` came from this session's own
**PRE-PREREG reconnaissance** (PREREG §0), taken at the session's start HEAD **`de837c38`** with a
looser `grep`. Between that reading and the probe's run I rebased onto `origin/main`, which had
moved: commit **`5df6192f`** — *"Add hydro_budget_period_by_instrument: use-it-or-lose-it hydro
budgets"*, the NYISO hydro lane discharging rule 28(c) — landed a **313th** mechanism row and, as
rule 28(c) requires, **one cell line in every one of the seven shards**.

**This is the handoff's own standing warning, and I walked into it:** *"RE-READ `origin/main` WHEN YOU
NEED IT, NOT ONLY AT SESSION START — parallel MISO lanes have landed records mid-session more than
once, and main moved four times during miso-245."* It has now moved **twice more** during this
session (`de837c38` → `1393fdd2` → `15bbb371`).

### 0a. THE 313th CELL, NAMED

| | |
|---|---|
| mechanism id | **`hydro_budget_period_by_instrument`** |
| base row `mode` | **`BF`** (backcast-lane reachable) |
| cell code | **`U` in all seven shards** — ERCOT, CAISO, PJM, MISO, NYISO, NEISO, SPP |
| landed by | `5df6192f`, in `de837c38..1393fdd2` |

Because it is `U` at `BF` **in every shard**, it adds **exactly +1 to every ISO's `N_bc`** and to
every shard's cell count.

## 1. **THE MAGNITUDE: WHAT MOVED, WHAT DID NOT, AND THAT NO VERDICT MOVED AT ALL**

Measured at three commits with one parser, so the failure's whole effect is visible:

| commit | shard cells (all 7) | `N_bc` ERCOT / CAISO / PJM / **MISO** / NYISO / NEISO | median over the 5 `complete` holders | §3a PRIMARY BAR |
|---|---:|---|---:|---|
| `de837c38` (session start) | 312 | 54 / 48 / 59 / **43** / 30 / 65 | **54** | **CLEARS** |
| `2d0767a5` (the run) | 313 | 55 / 49 / 60 / **44** / 31 / 66 | **55** | **CLEARS** |
| `15bbb371` (`origin/main` now) | 313 | 55 / 49 / 60 / **44** / 31 / 66 | **55** | **CLEARS** |

**THE ARITHMETIC SHOWING THE FAILURE MOVED NOTHING:** the added cell is `U`/`BF` in every shard, so
it adds +1 to MISO **and** +1 to every comparator, leaving the difference `median − MISO` at
**exactly 11** at both commits. **The §3a verdict is identical at all three.**

**MY PREREG's §0 DISCLOSURE OF `43` IS SUPERSEDED BY `44`, and I say so rather than quietly using the
new number.** Neither is wrong: `43` was correct at `de837c38` and `44` is correct at the commit the
probe ran on. What was wrong was **freezing a count from a moving file as a gate literal.**

## 2. **THE PRE-REPAIR VALUES, PUBLISHED HERE SO THE REPAIR CANNOT LAUNDER THEM**

**NOTHING BELOW READS THE MATRIX**, so none of it is affected by the `G-PARSE` failure in any way.
All values are from the failing run's committed JSON and are fixed on the record now:

| leg | measured (2023 / 2024 / 2025) | |
|---|---|---|
| **G-BASIS** corr(DA, RT) | **0.4023 / 0.4237 / 0.5527** — all < 0.60 (the lane's published +0.402 / +0.424 / +0.553, reproduced) | **PASS** |
| **G-BUS** | 8,760 P1 rows at `MISO_external`; `MISO_external_South` present and **distinct** | **PASS** |
| **G-RECON** Manitoba incumbent ≡ repaired export leg | `np.array_equal` **True**, all three years | **PASS** |
| **M-a1** σ(`p_bus`) | **6.09 / 16.53 / 15.21** (miso-242: 6.09 / 16.51 / 15.22) | reported |
| **M-a1** σ(Indiana DA) | **12.81 / 19.89 / 26.12** (miso-242: identical) | reported |
| **M-a1** ratio / corr | 0.4756 / 0.8308 / 0.5823 ; corr 0.6926 / 0.5881 / 0.7827 | reported |
| **M-a2** `R_rung` | **1.0000 / 1.0000 / 1.0000**; unmatched hours **0**; max min-distance **$0.00** | **fires** |
| **M-a2** ladder-exclusive / zone-exclusive | **0.0007 / 0.0001 / 0.0000** vs **0.8478 / 0.8492 / 0.8758** | reported |
| **M-b1** Manitoba template, measured / model | 0.7380 / 0.7205 / 0.6594 **vs** 0.6029 / 0.5225 / 0.2868 | reported |
| **M-b1** ceiling-active share | 0.4281 / 0.4170 / 0.2490 (miso-241: 0.4279 / 0.4152 / 0.2492) | reported |
| **M-b2** `Γ_ceiling` / `Γ_merit` | −0.1290 / −0.1912 / +0.1254 **vs** +0.1791 / +0.1866 / +0.3559 | **MERIT 3–0** |
| **M-c1** CC_REGULAR shape d1→d10 | 2023 −96.6→+134.2 · 2024 −63.1→+344.3 · 2025 −800.8→+454.0 MW | reported |
| **M-c1** hod argmin / argmax | **0 / 3** · **0 / 19** · **0 / 19** | reported |

## 3. **THE REPAIR — `G-PARSE′`, DECLARED HERE BEFORE ITS NUMBERS EXIST. NO BAR IS MOVED; THE LITERAL IS DELETED, NOT WIDENED**

**The `312` literal is NOT changed to `313`.** Widening a stale literal to the number I have just
seen is precisely the laundering the process forbids. It is **DELETED** (rule 26 `[R-DELETE]` — a
literal that still parses is a re-armable answer key) and replaced by three limbs, **none of which
contains a hand-copied count**:

> **`G-PARSE′` PASSES iff ALL THREE limbs hold. Any failure VOIDS the census's E1 enumeration.**
>
> * **L1 — CROSS-SHARD IDENTITY (literal-free).** The parser recovers the **same** cell count in
>   **all seven** shards. *This is rule 28(c)'s own invariant — a new mechanism row lands with a cell
>   line in every shard — so a parser that silently missed lines in one shard would break it. The
>   original gate could not have caught that at all: it checked one shard against one number.*
> * **L2 — UPPER-BOUND IDENTITY.** For **each** shard, the strict parser's count equals an
>   independent looser count over the same bytes (the same cell-opener with the leading-indent
>   constraint dropped). **Zero cells may be missed.**
> * **L3 — PROVENANCE STAMP (the limb whose absence caused the failure).** The artifact records
>   `git rev-parse HEAD`, the **blob sha of every shard and of the base matrix as actually parsed**,
>   and whether the tree is dirty. *A future comparison against these counts can then see the commit
>   they were taken at, which is exactly what the failing gate could not.*
>
> **Applied to all seven shards, not one.**

**WHY THIS IS STRICTER AND NOT A LOOSENED BAR.** `G-PARSE` asked *"did the parser see every cell?"*
and answered it by comparing one shard against a number copied by hand from a different instrument at
a different commit — a construction that can fail while the parser is perfect (what happened) and can
**pass while the parser is broken** (if the count coincidentally matched). `G-PARSE′` answers the
same question with two internal identities that hold **only if** the parser is complete, on **seven**
shards instead of one, and adds the provenance the original entirely lacked.

## 4. **THE SECOND DISCLOSURE, AND IT IS THE LARGER ONE: MY OWN PRE-REGISTERED DECOMPOSITION FALSIFIED THE STATED GROUND OF MY OWN `M-a2` RULE**

PREREG §4(a) fixed: *"`R_rung ≥ 0.90` in all three years ⇒ `p_bus` is **RUNG-DETERMINED**: its
dispersion is a mechanical consequence of the frozen ladders, the measured anchors and the merit
position … Item (a) is then class `G`."*

**`R_rung` = 1.0000 in all three years — a perfect fire, zero unmatched hours, maximum min-distance
$0.00. And the decomposition the SAME PREREG required has falsified the reason:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `R_rung` (any candidate) | 1.0000 | 1.0000 | 1.0000 |
| ladder-rung candidates alone | 0.1522 | 0.1508 | 0.1242 |
| **ladder-EXCLUSIVE** (rung matches, no zone price does) | **0.0007** | **0.0001** | **0.0000** |
| **zone-EXCLUSIVE** (a Midwest zone price matches, no rung does) | **0.8478** | **0.8492** | **0.8758** |

**`p_bus` is not rung-determined. It is ZONE-determined:** in 85–88 % of hours the model's
`MISO_external` price equals a **Midwest internal zone price** to the cent while **no** seam-tranche
offer does, and the ladder explains essentially nothing exclusively (**0.00 %** of hours in 2025).

**I therefore will NOT classify item (a) `G` on the ladder-freeze ground.** That ground is now
**measured false**, and firing a rule on a reason its own required decomposition refutes would be
laundering. The classification is re-derived below on the ground the measurement actually supports,
with its own test, **declared here before its number exists and written so it can only REFUSE the
reclassification.**

> **`M-a4` — DECLARED BEFORE ITS NUMBER EXISTS; IT CAN ONLY INVALIDATE.**
> If `p_bus` is the model's **own internal Midwest price**, then in every year:
> **(i)** `p_bus` equals the Midwest zone P1 price within **$0.01** in **≥ 99 %** of hours, and
> **(ii)** `|σ(p_bus) − σ(p_Midwest)| ≤ $0.05`.
>
> **If EITHER limb fails at ANY year, item (a) is reported UNRESOLVED, no reclassification is made,
> and that failure is published before anything else.** Passing adds no evidence for any lever and
> changes no other number; it only establishes **which object** item (a) is.

**If `M-a4` holds, the classification and its ground are these, fixed here before the number:** item
(a)'s object is **not a seam object at all** — it is the **model's own MISO price distribution**,
which the rubric already scores twice: **C3b** price duration / shape (**PASS**) and **C3c** price
tail / scarcity (the **designated frontier since 2026-07-20**, the single ledgered caveat).
Item (a) is then class **`G`**, refused on **C3c's own standing charter** — a new admissible measured
identification **plus an owner ruling**, never an offer adder, an ORDC offset, a scarcity multiplier
or any level tuned to the tail. **This is a correction to how miso-242's Q-B was filed**, and it is a
correction that **removes** an item from MISO's queue by identifying it as an already-scored object,
so it is stated with that interest declared.

**A CONSEQUENCE FOR `M-b2`, NOTED HERE AND NOT USED TO MOVE ITS VERDICT.** `M-b2` returned
**MERIT 3–0** on its own pre-registered rule, i.e. Manitoba's determinism deficit is the merit test
on `p_bus`. If `M-a4` holds, that merit test is `internal price − anchor > δ_k` — **a hub-pair spread
by construction**. `M-b2`'s verdict is unchanged and is not re-opened; what changes is only what the
shared object is understood to be.

## 5. Non-claims

1. **No bar is moved, and `G-PARSE`'s failure is not withdrawn** — it is repaired, and every
   pre-repair value is published above before the repair runs.
2. **`G-MODE`, `G-ISO`, `G-BASIS`, `G-BUS`, `G-RECON`, §3a's bar, `M-a3`, `M-b1`, `M-b2` and `M-c1`
   are untouched**, and none of them reads the matrix cell count except §3a, whose verdict is
   measured identical at all three commits (§1).
3. **`M-a4` cannot promote anything.** It can only refuse the reclassification; it is not evidence
   for a lever and no route becomes LIVE on the strength of it.
4. **Zero LP.** Nothing is solved, screened, registered or promoted; DOF stays **41/2**; no
   `ScenarioConfig` field is created or changed.
5. **No out-of-training year is solved, scored or registered, and no marker is sought or implied.**
6. **MISO has no failing gate**, this session does not invent one, and **C3c is untouched.**
