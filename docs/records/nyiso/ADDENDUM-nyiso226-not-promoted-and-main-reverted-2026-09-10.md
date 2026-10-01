# ADDENDUM nyiso-226 — **NOT PROMOTED. `main` IS REVERTED TO 0.175, because the auto-merge had armed the arm without a promotion decision and left the designated keeper unreproducible**

**Session:** nyiso-226 · **ISO:** NYISO · **Date:** 2026-09-10
**Keeper:** `2026-09-09-nyiso-221-fuelvintage-span`, **UNCHANGED.**
**Governs:** `RESULT-nyiso226-span-2026-09-10.md` §5–§6 and the "never merged to `main`" claims in
`RESULT-nyiso226-nyc-base-rebasis-2026-09-10.md`, `RESULT-nyiso226-span-2026-09-10.md` and
`docs/mechanism-testing-matrix.md` §5.5. **ZERO LP.**

---

## 1. TWO STATEMENTS IN MY OWN COMMITTED DOCS WERE FALSE. CORRECTED HERE

Those documents say the shard branches are **"never merged to `main`"**. **They were merged** —
`claude/nyiso226-screen-2023` as **PR #5953** and `claude/nyiso226-span` as **PR #5958**, by the
environment's automatic branch merge, which rule 32 `[R-SHARD]` (c)(1) itself describes
(*"branches here are auto-merged and DELETED within minutes"*). I wrote "never merged" as an
intention; it was not a fact, and it did not survive contact with the environment.

**The consequence was material, not cosmetic.** Each shard branch carried the one-cell arm edit,
so `data/raw/reference/reliability_floor_coeffs_NYISO.csv` on `main` came to read
**`0.16629202320362052`** — the arm — **with no promotion decision behind it.**

## 2. WHY THAT STATE HAD TO BE UNDONE RATHER THAN LEFT

The designated keeper `nyiso_fuelvintage_A` solved at `git_sha da2e7076`, where that cell reads
**`0.175`** (verified: `git show da2e7076:…` line 6). With `main` carrying `0.16629…`:

> **the ISO's designated keeper no longer reproduced from `main`.**

A replay of the keeper's own recipe at HEAD would have produced numbers its committed bundle does
not contain — silently, with no flag and no cache-key delta, because an artifact edit carries
neither. That is precisely the class of drift `G-DRIFT` exists to catch, and leaving it in place
would have made every future NYISO lane's form-4 control (rule 29(b)) quietly invalid.

**So `main` is reverted to `0.175`** — one line, CRLF preserved (47 before, 47 after), no other
byte touched. This restores the invariant that the designated keeper is reproducible from `main`.
**It is not a judgement against the arm.**

## 3. THE ARM IS NOT REJECTED. IT IS UNDECIDED, AND ONE CRITERION IS WHY

Everything measured still stands (RESULT-span §1–§2): C1 passes on both sides in both gated
years, C3a passes all three, C8 falls every year, the footprint landed within 7 % of its
pre-registered prediction, and the two-sidedness (2023 better, 2024 worse) is positive evidence
it is not residual-fitted. **My recommendation remains YES on the structural half.**

**But C3b was never measured, and it is the tightest-margin criterion** (2024 at 0.179 against a
0.20 ceiling). **Five separate routes were tried and every one was blocked:**

| # | route | blocker |
|---|---|---|
| 1 | shard runs the scorer on its bundle | the solve path writes no `metrics.json` |
| 2 | same, with the scorer invoked directly | `calibration_verdict.py` resolves **REGISTERED** runs only; registration is what rule 32(c) forbids a shard to do |
| 3 | shard pushes its three `system_*.parquet` | `git add -f` on a gitignored path **refused by the shard's permission classifier** |
| 4 | shard copies the bundle to a non-ignored path, plain `git add` | `git add` under `results/calibration/**` **refused** |
| 5 | shard computes C3b in place and writes the numbers to `docs/` | it **computed them** — then `git add` was **denied at all paths** |

**None of these blocks was routed around, and none should be.** Routes 3–5 are permission
decisions; a peer performing what a classifier refused is exactly the laundering that must not
happen. The numbers existed, briefly, in a transcript no other session can read.

**THE GENERAL LESSON, which outlives this arm:** a shard must be told to return **NUMBERS in its
final message**, never artifacts — and a full-span candidate must be **registered where it is
solved**, because an unregistered, gitignored bundle on an ephemeral container is unreachable by
every route this architecture offers. Rule 15 `[R-DASHBOARD]` already implies this; nyiso-226 is
the demonstration of what it costs to discover it late.

## 4. WHAT PROMOTION WOULD NOW REQUIRE

Rule 15 requires a keeper to carry its bundle plus `hourly/` sidecars. That bundle is gone —
unreachable, and its container ephemeral. **Promotion therefore costs a fresh ~18-minute
full-span re-solve**, in a shard instructed from the outset to (a) print the C3b reconstruction
for arm and control in its final message and (b) register the run itself, where the bundle lives.
Rule 31 `[R-RETAIN]` requires that estimate be stated **before** the LP is spent; it is stated
here, and **the LP is not spent.**

## 5. Rules

- **Rule 1 `[R-STRUCT]`** — nothing was decided on a residual. The revert is about reproducibility,
  not fit.
- **Rule 15 `[R-DASHBOARD]`** — no run registered: the screen bundle was never registrable
  (rule 29) and the span bundle became unreachable before registration. Stated, not hidden.
- **Rule 29 `[R-SCREEN]` (c)** — the intent held (no bundle reached `main`; `.gitignore` did its
  job and the parity gate is clean). What failed was my claim about the **branches**, §1.
- **Rule 31 `[R-RETAIN]`** — nothing deleted by this session. The re-solve cost is stated before
  spending, and it is not spent.
- **Rule 32 `[R-SHARD]`** — the parent ran no LP at any point in nyiso-226.
