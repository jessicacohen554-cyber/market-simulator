# SOCO Addition Desk — handoff (2026-09-16, after r#7)

**SUPERSEDES `soco-desk-handoff-2026-09-12.md`** (the r#0 charter). That file stays as the founding
record; this is the live one. A successor reads THIS, then the ledger, then the plan.

---

## 0. First act, in this order — re-verify, never trust this file's numbers

1. **`CLAUDE.md` in full and freshly.** It moves. Rules 31–35 all landed *after* this program was
   chartered, and reconciling the plan with a rule that lands mid-program is a **refresh edit the desk
   owns**, not a lane's. Two of this desk's six logged errors came from not doing that promptly.
2. **`docs/handoffs/soco-desk-ledger-2026-09.md`** — the desk's own record. **It wins over the plan on
   live state.** §0 is newest-first sittings; §1 scoreboard; §2 verbatim owner rulings; §3 routed items
   (R-a…R-o); §4 collisions (C-1…C-7); §5 issuance record; §6 **errors against interest** — read §6 in
   full before your first act, it is where the desk's own mistakes are written down so you don't repeat
   them.
3. **`docs/multi-iso/soco-addition-plan-2026-09.md`** — the plan. §3 cards (S1–S12 + rulings), §5 lane
   rows, §7 gates (G1–G23), **§8 the prompt pack — the five W3 charters are written out there in full**,
   §9 findings index.
4. **`docs/multi-iso/spp-addition-plan-2026-09.md` §2.3, §7, §8.0** — the reference workstream. SPP is
   the template this program is built against, **not NWPP** (see the DO-NOT-REDO in ledger §6).
5. **Re-verify live state with git, not with this document.** Pin `origin/main`, grep `_ISO_BUILDERS`,
   list branches and open PRs. Every number below was true at `1f586ed7` and will rot.

---

## 1. Live state — **REFRESHED AT r#8 (main `e9e1f4f0`)**; the `1f586ed7` column below is kept as the r#7 baseline

| | |
|---|---|
| **SOCO** | **REGISTERED — the NINTH region.** `_ISO_BUILDERS` is nine keys ending `"SOCO"` |
| W1 (data) | LANDED — SOCO-10/11/12/13/14/15 |
| W2 (registration) | **CLOSED** — SOCO-20 landed (PR #6152) and **graded PASS**; SOCO-21 (matrix shard), SOCO-22 (rubric v3.8) landed |
| W3 (derives) | ~~ISSUED, UNDISPATCHED~~ → **FOUR OF FIVE HAVE RUN (r#8).** SOCO-30 / SOCO-31 / SOCO-33 **LANDED and GRADED PASS**; **SOCO-34 FINISHED on `claude/soco-34-site-docs-pxkmb5` @ `1f71ec097b3f4b7e4ef17a5f88225abdd4c988c5` with NO PR — graded PASS off the branch, and it needs merging**; **SOCO-32 never started** (no branch, no commit, no FINDING — NOT graded LOST, gate G15) |
| W4–W6 | **SOCO-40 is blocked on SOCO-32 ALONE** — gate G4 is 2 of 3, and card S11 was discharged at r#5. W6 is still the capx director's (card S10) |
| Desk PRs | #6144, #6172 and **#6178 all MERGED**. No open desk PR — and at `e9e1f4f0` **no open PR in the repository at all**, which is why SOCO-34's finished branch is invisible in a PR listing |
| **NEW at r#8** | **`check_registry_payload_parity` is HALF THIS PROGRAM'S NOW**: `results/calibration/soco15_spp_arm` (34 files / 126 MB) is **tracked on `main`** and maps to no sidecar — a rule 29 `[R-SCREEN]` (c) delete-before-merge bundle that reached `main`. **Not deleted; routed as R-p and put to the owner** (rule 31 `[R-RETAIN]`) |
| Open cards | **S10 only** — W6 forecast-program routing, due when a keeper exists |
| Monitoring | **STOPPED** at the owner's instruction, 2026-09-16. No check-in is armed |

**What SOCO is:** the Southern Company balancing authority (BA code `SOCO`, NERC SERC) — Alabama Power,
Georgia Power, Mississippi Power, Southern Power. **Not an RTO.** No capacity market, no import node, no
AS design, every offer band 1.0. Three geographic zones SOCO_AL / SOCO_GA / SOCO_MS on shares
**0.3510 / 0.5842 / 0.0648**. Fleet 393 thermal units / 55.09 GW; 8 nuclear incl. Vogtle 3 (COD 2023-07)
and 4 (2024-04). **Demand 229.47 / 238.70 / 239.56 TWh** (SOCO-31's committed measurement); **net exporter
every year** (+10.16 / +10.81 / +13.03), so **net generation** is 239.6 / 249.5 / 252.6.
*(CORRECTED at r#8 — this line read "Demand 239.6 / 249.5 / 252.6", which is demand **plus** the export.
The same mislabel went into SOCO-31's charter delta and the lane corrected it; ledger §6 **E-9**.)*

---

## 2. The three things that will bite a successor

**(a) THE PRICE PROBLEM IS THE PROGRAM'S DEFINING CONSTRAINT, AND IT IS SETTLED — DO NOT RE-OPEN IT.**
Southern publishes no LMP and never will; SEEM publishes matched volumes, no price. SOCO-13 built a
FERC-EQR index behind a **pre-registered ex-ante STOP gate** and the gate read **NO** — three of five
gates failed and **no bar moved after the series was seen**. SOCO-22 then implemented the fallback as
rubric **v3.8**: `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, never `CALIBRATED`, **keyed on the ABSENCE of a
SOCO block in `actual_lmp.json`**. That absence is load-bearing — a placeholder block breaks the
classifier. **Gate G17 is absolute**: no lane may substitute a neighbouring market's hub (MISO-South, a
TVA or PJM proxy, an EIA state average dressed as a price). The desk has refused this twice and logged
both refusals in ledger §6. Refuse it again and log it.

**(b) CARD S3 IS RE-RULED AND THE SMALLER RESIDUAL IS THE WRONG ANSWER.** The zonal shares are the
**FIVE fully-cited FERC-714 respondents; Southern Power (186) is EXCLUDED**, residual 3.03 / 2.92 / 1.26 %.
The six-respondent set has a *smaller* residual (1.63 / 1.50 / **−0.03** %) and the owner chose the five-set
anyway, because SOCO-14 cited 107 and 210 from primary sources and returned a **documented NO on 186** — a
cited basis beats a smaller residual (rule 1 `[R-STRUCT]`), and that negative 2025 value is exactly the
overshoot SOCO-11's falsifier was built to detect. **Any lane rebuilding the shares on six is wrong.**
SOCO-32's charter carries this as a hard precondition; keep it there.

**(c) GATE G15 — NEVER GRADE A LANE LOST ON ABSENCE, AND NEVER READ A GREEN CHECK AS A DISCHARGED DUTY.**
Ask dispatch status; don't infer it. Two live corollaries: at r#4 a SOCO lane had landed under **another
program's branch stem** and the desk wrongly read it as undispatched — so check *four* signals (branches,
commit messages, new handoff docs, open PRs), never branch names alone. And at r#5 the desk read SOCO-20's
unmoved branch tip as a stall when the lane had simply **finished**.

---

## 3. What the desk writes, and what it never touches

**WRITES:** the plan (§3 rulings, §5 row statuses, §7 gates, §8 prompt pack, §9 findings index); the
ledger; `docs/calibration-log/soco.md` (each lane's `## Log entry` appended **VERBATIM** — the desk never
writes a lane's words, only a clearly-labelled DESK-AUTHORED STUB when a lane ships none); `CHANGELOG.md`.

**NEVER:** runs an LP (rule 32 `[R-SHARD]` — the parent never solves); edits `src/`, `scripts/`, `configs/`,
`tests/`, `frontend/` or `docs/codebase-site/`; writes `frontend/data/forecast/**` or charters
forecast-program work (the capx director's, card S10); touches another region's keeper shard, log or
matrix shard (rule 25 `[R-ISO-SCOPE]`).

**Cadence:** one refresh = one ledger §0 entry = one small PR off a branch **cut fresh from `origin/main`**.
Batch a sitting's edits into ONE commit — this is a private repo and every push re-fires the full CI matrix
on the owner's billed runner minutes.

---

## 4. Standing CI posture — do not re-litigate this every sitting

`main` carries **seven persistent red checks** that are **not this desk's and not portable into its write
scope**: FR-21 (`check_gate_a_provenance`), FR-22 (`check_forecast_parity`), Ruff, Structural refactor
guards, Pinned default cache key, Keeper-integrity gates, Fast test tier. Every desk PR inherits all seven.

The protocol, already established: **one standing-down comment per PR** (not per check, not per firing),
naming the set and re-measuring the base-branch claim by running the deterministic gates directly on the
tree — a docs-only branch *is* main's code, so running them locally runs them on the base branch. **No
re-runs** (all deterministic over committed files). **No porting** — each repair belongs to the promoting
ISO's own lane under rules 25 / 35(a). Duplicate firings need no second comment.

Two root-causes the desk found and routed, so a successor doesn't redo them:
- **R-k:** `Structural refactor guards` is red on a **false positive** — `ci_refactor_guards.py:52`
  `_SCRIPT_REF_RE` has no left word boundary, so any path *containing* `.../scripts/foo.py` reads as
  repo-root `scripts/foo.py`; `(?<![\w/])` fixes it. The cited docstring is *also* independently stale.
  **Both obvious one-liners are paper-overs** (a stub file; a `KNOWN_DANGLING` entry).
- **R-l:** `process_eia860.rescope_generator_table_from_parquet` is **not additive** when columns differ —
  it dropped the eGRID `heat_rate` join on four of eight tables **with every row count still matching**.
  SPP-20 and NWPP-20 ran the same routine; their tables deserve the same `.equals()` audit.

---

## 5. The next three moves

1. **Dispatch W3.** The five charters are paste-ready in plan §8 (SOCO-30 outages/tranches · SOCO-31
   benchmarks · SOCO-32 zonal shares + **solar** shape + gas hub · SOCO-33 seam derive · SOCO-34 site+docs).
   All five are independent — dispatch in any order. Each ends with the pack's EXIT boilerplate **including
   the `## Log entry` line**; ledger E-6 measured 4/4 compliance for pack-copied charters and 0/2 for
   desk-drafted ones that omitted it, so never issue a charter without it.
2. **Grade each lane BY CONTENT as it lands** — open the cited FINDING, verify its claims against `main`
   rather than reading them off the document. SOCO-20 set the standard worth holding others to: every
   remaining test failure carried a **same-tree control** proving it pre-existing.
3. **Then W4** (first solve, SOCO-40): ONE shard, ONE `--year 2023 2024 2025`, ONE bundle (rule 32(b)); the
   shard **pushes its bundle to its own branch** including `dispatch/<year>_P1.parquet` (rule 34(a) as
   corrected — a charter telling a shard to gitignore its bundle is a defect in the prompt); the PRECOMMIT
   states the **no-price posture before the solve**; the parent verifies retrievability before archiving
   (rules 33/34(d)) and **asks the promotion question in-session while the bundle is alive** (rule 31).

---

## 6. Where the bodies are buried

`docs/handoffs/soco-desk-ledger-2026-09.md` §6, in full. The short version, because each cost something:

- **E-1** an unsatisfiable hold ("verify nobody is mid-edit") — every hold must name the observation that
  releases it.
- **E-4** the charter called FERC-714 a "spine" without censusing it; it named three respondents, there are
  eight. State a decomposition's coverage fraction as a measured number *before* recommending a topology.
- **E-6** the two lanes that shipped no `## Log entry` were both **desk-drafted** charters. 100 % correlation.
- **E-7** and **E-8** are the same shape one sitting apart: **right about the data, wrong about the code.**
  E-8 is the sharpest — the desk wrote a gate telling a lane the EIA-860 parquet rebase was mechanical
  ("no judgment call") and offered a **census** as the check; the routine silently corrupted four tables
  **with every count matching**. A gate that prescribes running a script must state the assertion proving
  the script did what it claims — for a derived table that is an **identity** check (`.equals()`) on the
  untouched slice, never a count.
