# SOCO Addition Desk — ledger (2026-09)

The live record of the SOCO addition program. **This ledger wins where it and
`docs/multi-iso/soco-addition-plan-2026-09.md` diverge on live state**; the plan owns the charters
(§8) and the decisions (§3), this owns who is running what.

Refresh discipline: one refresh = one §0 entry = one ledger commit = one small PR, off a branch
recreated fresh from `origin/main`.

---

## 0. Live state — newest entry FIRST

### r#8 — 2026-09-16 — **THE DESK REOPENS AND W3 HAS RUN: FOUR OF FIVE LANES DISPATCHED, THREE LANDED AND GRADED PASS, ONE FINISHED WITH NO PR, ONE NEVER STARTED** (main `e9e1f4f0`)

**The handoff said W3 was "issued and undispatched". That was true at `1f586ed7` and is no longer true**
— which is exactly why §0.5 says re-verify with git rather than trust the document. Between the desk
closing and this sitting, four of the five W3 lanes ran:

| Lane | State at `e9e1f4f0` | Grade |
|---|---|---|
| **SOCO-30** outages + tranches | **ON MAIN**, PR #6179 + #6181 | **PASS** |
| **SOCO-31** benchmarks | **ON MAIN**, PR #6185 | **PASS** |
| **SOCO-33** seam derive | **ON MAIN**, PR #6180 | **PASS** |
| **SOCO-34** site + docs | **FINISHED ON ITS BRANCH, NO PR EXISTS** — `claude/soco-34-site-docs-pxkmb5` @ `1f71ec097b3f4b7e4ef17a5f88225abdd4c988c5`, 2 commits, 16 files, FINDING shipped, **zero conflicts against main** | **PASS**, graded off the branch |
| **SOCO-32** zonal shares + solar + gas hub | **NO BRANCH, NO COMMIT, NO FINDING** | **not graded** (gate G15) |

**GRADED BY CONTENT, AND THE DESK RE-MEASURED THE LOAD-BEARING CLAIMS RATHER THAN READING THEM OFF THE
FINDINGs.** Four checks the desk ran itself, each against `main`:

1. **`actual_lmp.json` has no SOCO block** — verified by loading the file: its top-level keys are the
   seven price-carrying ISOs and the string `SOCO` appears nowhere in it. The classifier key rubric
   v3.8 reads is intact, and G17 held through three lanes that each had a reason to reach for a proxy.
2. **Gate G9 is EXACTLY zero** — `git diff` over SOCO-31's commits gives `calibration_reference.json`
   **+295 / −1**, and the one deletion is the `generated` date stamp. Not "the lane says so": the diff.
3. **`CAMPD_BINNING_ISOS` is `{ERCOT, CAISO, NEISO, NYISO, PJM, MISO}`** — SOCO is absent, so SOCO-30's
   bound on its own §6.2 defect ("nothing in W4 reads this file") is true as written.
4. **SOCO-34 did not clobber `docs/calibration-log/soco.md`** — the charter called any removed entry a
   stop-the-line event, and its diff is 121 insertions / **7 deletions, all seven in the old header
   block**; all nine existing `## soco-` entries are present on the branch.

**THE SITTING'S BIGGEST TECHNICAL RESULT IS SOCO-33'S, AND IT IS A RULE-14 MISALIGNMENT WITH A NUMBER ON
IT.** Seven of SOCO's eight registered `interface_limit_mw` values are contradicted by SOCO's own meter:
arming the priced blocks at the registered values would **refuse 10.66 / 12.81 / 14.21 TWh — 35.6 / 39.0 /
41.7 %** of those seams' gross throughput. `SOCO_SCEG`, the largest export seam, is over its 126 MW limit
in **99.8 %** of 2025 hours. `SOCO_MISO` (2,374 MW) is the only seam never exceeded in any hour of any
year — and the only one with a price anchor, which the lane correctly called a coincidence rather than a
result. `spec.py` already declared the misalignment in prose (the values are the 2024 Reserve Margin
Study's **average import transfer capability**, an adequacy quantity, not a tie rating); this lane put the
consequence in TWh. **It blocks nothing in W4** — card S4 ruled the first keeper uses the served measured
schedule and all eight priced blocks are inert until `reference_price_interface` is armed, which no keeper
does — and it is now the **binding precondition on lever SOCO-56**, ahead of any heat-rate work. Routed
**R-t**.

**WHAT EACH LANE ESTABLISHED, beyond passing.**

- **SOCO-30** ran six invocations and changed no flag and no constant. **Gate G4 both legs PASS**: windows
  in every CEMS state-year (AL 196/206/240 · GA 115/118/155 · MS 21/31/37 = **1,119**), and the 8 full-year
  rows are **all** the `eia923_netzero` structural fallback, all 2025, all small non-CEMS CHP — **zero
  measured full-year CEMS outages, and no unit fell back for want of data**, which is the failure this
  gate's leg 2 exists to catch. It derived the standard extract **twice** and got byte-identical output,
  then caught that `--merit-order-guard` rewrites the default-read file (1,119 → 1,085) and re-derived
  guard-off to prove the committed blob. Vogtle emits **zero rows** — the phantom SOCO-15 removed was not
  re-introduced. Class bands reported against MISO's and **explicitly not tuned**, with three divergences
  named and attributed rather than smoothed.
- **SOCO-31** met the charter's reconciliation targets and **told the desk its labels were wrong** (see
  E-9). It held the price line under pressure: `actual_lmp.json` untouched, `TAIL_THRESHOLD` skipped in
  all three copies and **verified by execution** — both derives re-run, both emitted zero SOCO rows, both
  outputs reverted to committed bytes. On `eia923_2025.json`, where the audit has no `--isos` filter and
  genuinely moves two non-SOCO rows, it ran a **control on `main`'s own code with `data/clean` removed**
  and proved the committed file byte-identical to what `main` produces today — rather than suppressing the
  NWPP block, which would have committed a file the script does not emit. That is the SOCO-20 same-tree-control
  standard held by a second lane, unprompted.
- **SOCO-33** verified its sign convention instead of asserting it: a shift test over 26,294 joined hours,
  agreement in **91.7 %** of hours at zero shift collapsing to **0.2 %** at ∓1 h. Every interchange residual
  is explained (2024's 0.0248 TWh = 0.0242 leap day + 0.0007 UTC re-binning), not padded. Both committed
  producers **fail on `--iso SOCO`** and one fails **silently, exit 0 with an empty table** — it routed both
  rather than patching a shared producer it does not own.
- **SOCO-34** did the one thing its charter asked it to *check* rather than assume — `index.html`'s
  "47 zones (44 carry load), 58 links" — and found it **already correct**, measured two independent ways
  (`39+5+3`, `36+5+3`, `47+9+2`). NWPP-35's four cited debts are all discharged. It also caught itself
  writing "§5.10" from memory and corrected it against the file, and reports that.

**SOCO-32 IS NOT GRADED AND IS NOT LOST (gate G15).** It has no branch, no commit and no FINDING — and
absence is not evidence. It is the **one open item on SOCO-40's critical path**: gate G4's preconditions
are `SOCO-30/31/32` and two of three are now discharged. The desk asks dispatch status in this sitting's
report rather than inferring it, and re-issues nothing — the charter is already paste-ready in plan §8 and
carries card S3's exclusion of Southern Power (186) as a hard precondition.

**E-9, AND IT IS THE E-5 SHAPE FOR THE THIRD TIME: TWO NUMBERS IN THE DESK'S OWN W3 CHARTER DELTAS WERE
WRONG, AND TWO SEPARATE LANES HAD TO CORRECT THEM.** SOCO-30's delta asserted "CEMS coverage is 91.6 % of
fossil MW"; SOCO-10 had measured 91.6 % as the **missing** share, *before* SOCO-11 landed AL and GA — a
polarity flip in paraphrase that would have had the lane report a 4 % gap as an 8.4 % one and double-count
the lane that closed it. SOCO-31's delta gave "demand 239.6 / 249.5 / 252.6 TWh"; that is **demand + net
export**, and SOCO-31 measured demand at **229.47 / 238.70 / 239.56**. Both were checkable when written.
Full text in §6.

**PR #6178 (the desk's own handoff) MERGED** at `b5bf0238`. There is **no open desk PR** and, at this pin,
**no open PR in the repository at all** — which is why SOCO-34's finished branch is invisible to anyone
reading the PR list.

**Appended to `docs/calibration-log/soco.md` this sitting, VERBATIM**: soco-30, soco-31 and soco-33's
`## Log entry` blocks. **E-6's correlation now holds at 7/7** for pack-copied charters and 0/2 for
desk-drafted ones — all five W3 charters carried the EXIT boilerplate with its `## Log entry` line, and
every lane that has run so far shipped one. One formatting note, recorded rather than silently fixed:
SOCO-31's heading reads `## 2026-09-16 — SOCO-31: …` where the file's convention is
`## soco-31 — 2026-09-16 — …`. **The desk appends verbatim and does not rewrite a lane's words**, so the
deviation stands and is named here instead.

**SOCO-34's entry is NOT appended**, because the lane has not landed. It is appended at the sitting that
sees its merge.

**THE STANDING CI POSTURE NEEDS A CORRECTION, AND IT IS AGAINST THIS PROGRAM'S INTEREST.** The handoff
says `main`'s seven red checks are "not this desk's and not portable into its write scope". That is now
**half wrong on one of them.** `check_registry_payload_parity` is RED with **two** unmapped bundle dirs,
and the second is **`results/calibration/soco15_spp_arm` — SOCO-15's own A/B arm, 34 files / 126 MB,
TRACKED ON `main`** (commit `59c045e1`, *"SOCO-15 SPP arm: spp38_span recipe replayed at 4f33476c"*), not
gitignored, mapping to no retained sidecar. It is a rule 29 `[R-SCREEN]` (c) *delete-before-merge* bundle
that **reached `main`**, which is the one thing that clause exists to prevent.

Three things follow, and the desk states all three rather than the convenient one:

- **This is not the rule-31 local-tree trap** (CLAUDE.md rule 31's 2026-09-16 correction: a *gitignored*
  bundle in a session's own working tree reddens the gate locally while CI stays green). The desk checked
  `git ls-tree origin/main` before concluding anything: the bundle is **committed**, so CI sees it too.
- **The desk did NOT delete it, and will not without a ruling.** Rule 31 `[R-RETAIN]`'s bar is the
  OWNER's decision, not a session's, and "not needed in my judgement" is the exact reasoning that produced
  the ercot-255 incident. `results/` is also outside this desk's enumerated write scope. Routed **R-p**,
  with the question put to the owner in this sitting's report.
- **The numbers survive the bundle either way**, which is what makes it disposable *once ruled*:
  `FINDING-soco-15-2026-09-13.md` carries the eight-footprint A/B at full magnitude, exactly as rule
  29 (c) requires of a screen's record.

**GATES AT `e9e1f4f0`** — run directly on this tree, never read off a CI tick:

| Gate | Exit | Note |
|---|---|---|
| `check_registry_payload_parity.py` | **1 — RED** | **2 dirs: CAISO's `caiso279_ablate_dswcouple_span` (R-c, still open since r#2) and SOCO's OWN `soco15_spp_arm` (R-p, NEW)** |
| `check_gate_a_provenance.py` | **1 — RED** | **3 rows, and the NYISO one has MOVED AGAIN**: NYISO's marker now cites `2026-09-09-nyiso-221-…` against live `2026-09-14-nyiso-235-gas-repair`; SPP cites `2026-09-12-spp-36-…` against live `2026-09-13-spp-38-vintage-cache`; plus SPP's marker/`calibration-complete.json` `complete` inconsistency |
| `check_forecast_parity.py` (FR-22) | **1 — RED** | the same two undeclared NYISO mechanisms as r#5 — `gas_offer_margin_zonal_anchor_vintage`, `nyiso_st_gas_econ_bands_deleaked`. 7 keeper postures, 2 unaccounted, 14 filed gaps |
| `audit_keepers.py --check` | **1 — RED** | 1 failure / 4 warnings |
| `check_mechanism_matrix.py` | **0** | 2 warnings, both NYISO's keeper-stamp drift (shard + prose header) from the nyiso-235 promotion. Diff gate NOT RUN (no `--base`) — a 0 here is not a registration verdict |

**R-j's "churn, not monotone growth" reading holds and is sharpened.** MISO's four E13 rows stayed
cleared; what replaced them is a **third** NYISO promotion that did not re-key its own marker or re-stamp
its matrix shard, plus SPP's. The population of unswept promotions is stable while its membership rotates —
which is a protocol gap, not a lane's carelessness, and it is rule 35 `[R-PROMOTE]`'s own invariant
failing to be enforced by anything that blocks.

---

### DESK CLOSED — 2026-09-16 — monitoring stopped at owner instruction; successor handoff written (main `1f586ed7`)

> **SUPERSEDED BY r#8 (above), same day — THE DESK IS REOPEN AND THIS ENTRY'S CENTRAL CLAIM HAS EXPIRED.**
> "W3 is **issued and undispatched**" was true at `1f586ed7` and was false by `e9e1f4f0`: four of the
> five lanes ran. The entry is annotated rather than edited — it is the baseline r#8's grades are
> measured against, and rewriting it would destroy the record of what the desk believed when it
> closed. **The "no armed check-in" line still holds**: nothing woke this session and a successor
> still inherits no watch.

**Both desk PRs merged within 23 minutes of each other** — #6144 at 03:49 (r#5 + r#6) and #6172 at 04:12
(r#7). Verified on main: all five W3 charters present in plan §8, plan 1012 L, ledger 663 L. **No open desk
PR, no armed check-in, nothing in flight.**

**Monitoring STOPPED** at the owner's explicit instruction. Both scheduled triggers were deleted
(`trig_018sP2aGF8ygSLL2CbCt917u`, the #6172 watch; `trig_01Uf5jTosMAbVLDUeGHPBv7f`, the W3 dispatch watch).
Nothing will wake this session. **A successor does not inherit a watch — if one is wanted, it is armed fresh.**

**The successor handoff is `docs/handoffs/soco-desk-handoff-2026-09-16.md`**, and the r#0 charter
(`…-2026-09-12.md`) is annotated SUPERSEDED in place rather than deleted — it is the baseline every error in
§6 is measured against, including the two it caused itself (E-3's gate G13, E-4's uncensused FERC-714 "spine").

**Where the program stands.** W1 and W2 are closed: SOCO is the **ninth registered region**, SOCO-20 graded
PASS. W3 is **issued and undispatched** — five paste-ready charters in plan §8, all independent. W4 is blocked
on W3. One card is open: **S10**, the W6 forecast routing, due when a keeper exists. Fifteen items are routed
(R-a…R-o), none of them this desk's to write.

**What this desk got wrong, since that is the part worth inheriting.** Eight errors against interest, and the
last two are the same shape one sitting apart: **right about the data, wrong about the code.** E-7 read another
program's defect report as "not our problem" instead of "this construction is being removed from under us";
E-8 wrote a gate calling the EIA-860 parquet rebase mechanical and offered a **census** as its check — the
routine then corrupted four tables **with every count still matching**. The rule the desk leaves behind:
**a gate that prescribes running a script must state the assertion that proves the script did what it claims,
and for a derived table that is an identity check, never a count.**

---

### r#7 — 2026-09-16 — NOTHING OF SOCO'S MOVED, AND THAT IS THE ENTRY: NWPP FINISHED ITS WHOLE W3 IN THE SAME WINDOW (main `8b9b32e4`)

**No SOCO lane was dispatched, so nothing was graded.** W3 (SOCO-30/31/32/33/34) was issued 2026-09-14
19:55 UTC and at this pin has no branch, no commit, no FINDING and no PR. Gate G15 holds: **no lane is
graded LOST on absence**, and the dispatch gap itself was already reported once (09-15 08:09) and is not
re-reported here.

**What IS new is the magnitude, and it is a measurement rather than a repeat.** At the 08:09 report the
contrast was one work item: NWPP-30 had landed, SOCO-30 had not started. At this pin **NWPP has landed its
ENTIRE W3** — NWPP-31 benchmarks, NWPP-32 hydro, NWPP-33 zonal shares, NWPP-34 seam, NWPP-35 site+docs
(PRs #6167–#6171) — while SOCO's five lanes have not begun. Both programs registered on 2026-09-14, hours
apart. This is recorded, not re-escalated; the paste-ready W3 block is already with the owner and there is
nothing for the desk to re-issue.

**The sitting's actual deliverable is a charter repair that only became possible now.** NWPP-35 swept the
shared codebase-site prose to NINE regions and — correctly, under rule 25 `[R-ISO-SCOPE]` — did **not**
serialize SOCO. What it did instead is the part worth naming: it **cited the debt in the artifact**, in
`iso-topologies.json`'s own `_meta.description` (*"eight are serialized here. SOCO registered the same day
as NWPP and its block is owed by the SOCO desk's own site lane, not by this one"*) and again as a code
comment at `data-completeness.html:364`. That is a clean handover, not a collision, and it is the standard
this desk should hold its own lanes to. **SOCO-34's §8 charter delta now carries all four owed items
specifically** — the topology block, the completeness filter entry, the stale "eight serialized" line at
`config-reference.html:404`, and a CHECK (not an assumption) that `index.html:297`'s "47 zones" already
counts SOCO's three. Routed as **R-o**.

**A question closed with a measurement rather than an assumption.** NWPP's W3 has a lane SOCO's does not —
NWPP-32, hydro. The desk checked whether SOCO's W3 is short a lane: **it is not.** SPP's W3, the template
this program issues against, has no hydro lane either, and the reason is proportion — NWPP is hydro-dominated,
SOCO's hydro is ~2.5–3.5 % of energy. SOCO's awkward water asset is the 1,306.6 MW of pumped storage, already
routed as R-i. Recorded as a **DO-NOT-REDO** in §6, with the numbering-offset trap named (NWPP-33 ≈ SOCO-32,
NWPP-34 ≈ SOCO-33, NWPP-35 ≈ SOCO-34 — a charter copied from NWPP by lane number is the wrong charter).

**PR #6144 MERGED at 03:49:09 UTC**, mid-sitting — the r#5 and r#6 records (SOCO-20's grade, the G23
correction, R-l/R-m/R-n, the W3 issuance) are on main. The desk's opening state check for this sitting ran
minutes before the merge and read it open; the merge was caught when the push hint for a branch with no open
PR came back. Because a merged PR cannot track new work, r#7 moved to a **fresh branch cut from origin/main**,
`claude/soco-desk-r7`, carrying this entry — the merged `claude/soco-desk-r5` is not reused.

---

### r#6 — 2026-09-14 — **SOCO IS REGISTERED** · SOCO-20 GRADES PASS · W3 ISSUED · the desk's own G23 was wrong about the one step that mattered (main `d54cd9c5`)

**SOCO is the NINTH registered region.** `_ISO_BUILDERS` on main is nine keys ending `"SOCO"`; PR #6152
merged as *"Register SOCO as the **ninth** region (SOCO-20)"* after the lane rebased onto the
NWPP-inclusive main. W2 is CLOSED. W3 is unblocked and issued below.

**SOCO-20 — graded PASS, by content.** Verified on main rather than taken from the FINDING:
`_ISO_BUILDERS` / `DEMAND_LOADERS` / `SURFACE_ISOS` all carry SOCO; `BA_CODE_TO_ISO["SOCO"]="SOCO"` and
`_ISO_TO_BA_CODE["SOCO"]` both present (the §2.3 pin the desk added at r#3–r#4, and the one NWPP's
precedent did NOT discharge); three zones on the **five**-respondent shares card S3 re-ruled, Southern
Power 186 excluded. **G8 holds** — 0 moved rows for all eight incumbents, seven keepers' `cache_key()`
byte-identical. What earns the grade is not the pin flip but the conduct around it:

- **Every** remaining test failure carries a **same-tree control** — "FAILS on main's code, same tree" —
  rather than an assertion that it is pre-existing. That is the standard this desk should hold every
  lane to, and it is the first lane to volunteer it unprompted.
- The lane found `--rescope-from-parquet` **corrupting** the tables it was told to regenerate, repaired
  them by hand to an identity standard, and **ROUTED the script defect instead of patching outside its
  regions** — the STOP-and-route discipline working in the direction that costs the lane time.
- It shipped its `## Log entry` (appended verbatim to `docs/calibration-log/soco.md` this sitting).
  E-6's correlation holds at 4/4 for pack-copied charters and 0/2 for desk-drafted ones.

**The desk was wrong, and it was wrong about the step it had just written a gate for.** G23 told the
rebasing lane the parquet conflicts were mechanical — *"no judgment call"* — and offered a **census** as
the check. The rescope dropped the eGRID `heat_rate` join on four of eight tables, added a column,
reordered another and admitted a foreign PJM row; **every count still matched**, so the census this desk
prescribed would have passed all of it. Recorded as **E-8**, G23 corrected to the lane's proven recipe
(main's frame byte-for-byte + the new rows, `heat_rate` from the PLNT23 cache, and `.equals()` on the
untouched slice — an identity, never a count). Two sittings, two errors of the same shape: right about
the data, wrong about the code.

**Routed this sitting:** **R-l** the `process_eia860` non-additivity (the committed tables are repaired,
the script is not — and SPP-20 and NWPP-20 ran the same routine, so their tables deserve the same
`.equals()` audit); **R-m** 20 undeclared D79 SOCO rows, the same state SPP-20 left, now a
two-region-wide protocol gap rather than either lane's miss; **R-n** `solve_surface.py:75` still calls
SOCO "the eighth registered region".

**W3 ISSUED — SOCO-30/31/32/33/34**, per §8's standing instruction (against SPP's committed W3 charters
plus the SOCO deltas). **SOCO-32 carries card S3's exclusion of Southern Power (186) as a hard
precondition**, so the zonal share is never quietly rebuilt on six respondents — the specific failure
this desk flagged at r#5 before the lane existed.

**Open, and the owner's:** PR **#6144** (r#5 + r#6 records) is still unmerged, and it is now costing
something measurable — SOCO-20 had to route *"ledger r#5 five-respondent ruling not on main"* as an item
because the lane could not cite it. Its seven red checks are all base-branch, covered by one
standing-down comment, and its diff is markdown only.

---

### r#5 — 2026-09-14 — ALL FIVE LANES LAND AND ALL FIVE PASS · GATE G22 FAILS AND THE GATE IS THE POINT · **SOCO-20 IS CLEARED** (main `39a1c9a1`)

**Graded BY CONTENT — five FINDINGs opened, five PASS.** The r#4 re-emission worked: every lane
that had stood undispatched came back, and two of them came back with a NO, which is what a
well-built gate is supposed to produce.

| Lane | Verdict | What it actually established |
|---|---|---|
| **SOCO-13** EQR price index | **PASS — and the answer is NO** | Three of five pre-registered gates fail: **D2.2** every year (indexed short-term energy **3.66 / 2.69 / 2.64 %** of SOCO demand vs a ≥ 5 % bar), **D3.1** in 2024/25 (**+54.2 / +72.1 %** vs the SEEM auditor's annual clearing price, ±15 % bar), **D4.2** in 2025 (2.008 vs 0.8–2.0). D1, D2.1, D3.2, D3.3, D4.1, D5 pass. **No bar was moved after the series was seen** — the one post-PRECOMMIT change, addendum A, corrected the D3 anchor's *source* before `build` first ran and moved no number, and the FINDING **reports D3 on the original letter too, where it also fails**. Nothing landed to `_validation-source`; **G17 intact** |
| **SOCO-14** BA membership | **PASS — gate G22 FAILS** | **Oglethorpe (107) YES** and **MEAG (210) YES**, both from primary sources, both cross-checked against an independent EIA-861 peak that equals the 714 series' own 2024 maximum. **Southern Power (186) a documented NO.** The lane reported the three **separately** as chartered and **refused to stretch** a generation-side document into a load-side claim |
| **SOCO-15** COD seam | **PASS — the strongest lane of the program** | Repair on `main` (`9398000d`, PR #6127). **All three exit conditions MET** with evidence, not assertion. Eight footprints: four solved (MISO 2020–25, SPP 2023–25, ERCOT 2021–25, PJM 2023–25), four bounded by input census. **Both directions reported at full magnitude** |
| **SOCO-21** matrix shard | **PASS** | Eighth shard, one commit (G2). **327** ids = **168 `U`** + **159 `·`**, one cell line per base id. `keeper`/`gates` deliberately EMPTY and **no verdict minted** — correct, because SOCO has no keeper, no registered run and no solve at HEAD |
| **SOCO-22** rubric class | **PASS** | Rubric **v3.8**. Over **54 verdict files** (14 runs full-span + 40 per-year) the union of differing lines is exactly `rubric_version` 3.7 → 3.8, **54 times each, and nothing else**; all 14 `render_text` blocks byte-identical. The one permitted diff was **declared in the PRECOMMIT before the scorer was edited**. `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, never `CALIBRATED` |

**THE SITTING'S REAL RESULT: A GATE THIS DESK BUILT FIRED, AND IT CHANGED THE ANSWER.** Gate G22
existed because the desk's r#3 card-S3 ruling rested on an attribution nobody had cited. SOCO-14
went and looked, found two of three, and returned a **documented NO** on the third rather than
stretching the IIC contract or EIA-860's 11-of-53 plants into a load claim they do not support.
The card came back to the owner exactly as designed, and **the owner re-ruled to the FIVE
fully-cited respondents** — residual **3.03 / 2.92 / 1.26 %** — in preference to the six-respondent
**1.63 / 1.50 / −0.03 %**. Two things make that the right trade and both are on the record: a
cited basis beats a smaller residual (rule 13), and the six-set's 2025 residual going **negative**
is the overshoot SOCO-11's own falsifier was built to detect. 186's 1.3–1.4 % is **excluded and
named on the first keeper's determination basis**. G22 is now **DISCHARGED for the five-set and no
other**.

**Two cards closed themselves on the evidence, needing no owner time.** **S9** (`TAIL_THRESHOLD`)
resolves **n/a** — SOCO-13's NO means no series, so no tail, so gate **G6**'s pre-specified skip
branch fires and the three edits are deliberately skipped. **S12** closes: the repair is on `main`.

**SOCO-20 IS CLEARED TO PROCEED.** Every precondition is now discharged: cards S1–S8, S11, S12
ruled; **G12 MET** (SOCO-12's LTLF); **G22 discharged** on the five-set; **SOCO-15 landed** with the
seven keepers' cache keys byte-identical. Its charter is issued in this sitting's report.

**ERRORS AND OMISSIONS, recorded because the record is the deliverable.** **SOCO-15 and SOCO-21
shipped no `## Log entry` section**, which plan §8.0 rule 1 requires so the desk can append
verbatim. The desk **did not fabricate their words**: `docs/calibration-log/soco.md` carries the
three that exist verbatim and, for those two, a **clearly-labelled DESK-AUTHORED STUB** giving only
what another ISO's lane must know, pointing at the FINDING. For SOCO-15 that is load-bearing: its
repair **moves results for registered keepers while leaving cache keys untouched**, so a lane whose
numbers shift and whose key does not needs to find this entry rather than open a regression hunt.

**Gates at `39a1c9a1`** — the base-branch debt **grew again**, and every increment is another
program's promotion:

| Gate | Exit | Note |
|---|---|---|
| `audit_keepers.py --check` | **1 — RED** | 5 failures: MISO **E13 ×4**, plus **S1** status stale vs current verdicts (ERCOT) |
| `check_gate_a_provenance.py` | **1 — RED** | now **THREE** ISOs — MISO, NYISO **and SPP** — plus an SPP marker/`calibration-complete.json` inconsistency |
| `check_forecast_parity.py` (FR-22) | **1 — RED** | now **TWO** undeclared NYISO mechanisms: `gas_offer_margin_zonal_anchor_vintage` **and** `nyiso_st_gas_econ_bands_deleaked` — the second arrived with the nyiso-232 promotion |
| `check_mechanism_matrix` · `check_bench_freshness` · `check_golden_manifest` | 0 | |

**Next act:** sitting #6 — grade SOCO-20, then issue W3 (SOCO-30/31/32/33/34). **SOCO-32 must be
issued against the FIVE-respondent set**, and its charter must carry S3's exclusion of 186 so the
share is never quietly rebuilt on six.

**ADDENDUM — r#5 check-in, 2026-09-14 ~16:40 UTC (main `c6c70190`). SOCO-20 is DONE, and it is
BLOCKED — by NWPP, not by itself.** The scheduled check-in on PR #6144 fired against a moved main
and the picture inverted in both directions:

- **SOCO-20 never stalled.** Its tip sat at `e85bd85e` for ~8 h because it **finished** — 5 commits,
  77 files, `FINDING-soco-20-2026-09-14.md` shipped, PR **#6152 open**. The r#4/r#5 reading of an
  unmoved tip as an in-flight lane was wrong in the safe direction (gate G15: never grade on
  absence) but it was still wrong, and one `git ls-tree` on the branch would have shown it.
- **NWPP-20 (PR #6153) merged first and took the eighth slot.** `_ISO_BUILDERS` on main is nine
  keys with `"NWPP"` last; `mech_matrix.ISO_ORDER` already carries both (SOCO `O`, NWPP `W`). **SOCO
  is the NINTH region** and every "eighth" in this plan, in SOCO-20's commit subject and in its own
  `fleet/models.py` comment is stale.
- **PR #6152 now carries 55 conflict markers across 25+ files**, and one of them is not mechanical:
  NWPP-20 made `BA_CODE_TO_ISO` **many-to-one** and **deleted the scalar inverse** as a silent
  1/17-of-a-pool bug; SOCO-20's branch **writes that exact scalar inverse**. Taking SOCO's side at
  the merge breaks NWPP. Recorded as collision **C-7**, resolution as gate **G23**, and the desk's
  own misreading of the same evidence at r#3 as error **E-7**.
- **PR #6144 (this desk) is clean against the new main** — `merge-tree` reports zero conflicts, so
  no rebase was needed. This addendum and C-7/E-7/G23 ride it.

**The rebase is the LANE's, not this desk's** — the 8 `eia860_generators.parquet` conflicts and
every `src/`/`scripts/` hunk are outside this desk's write scope. One comment posted on #6152
naming the hazard and the resolution; **what the owner owes is a re-dispatch of SOCO-20 to rebase
per G23**, since a desk cannot rebase a lane's branch for it.

---

### r#4 — 2026-09-13 — NOTHING LANDED, AND THAT IS THE FINDING: FIVE LANES ISSUED, ZERO DISPATCHED (main `33a7c961`)

**Graded: nothing, because nothing exists to grade.** `git log cd09607a..origin/main --grep=SOCO -i`
returns only this desk's own r#3 merge and NWPP commits. No branch matches any SOCO stem
(`git ls-remote --heads origin | grep -i soco` → empty). No PR since **#6103** carries a SOCO lane.
Five lanes stand issued and undispatched: **SOCO-13** and **SOCO-21** since r#2 (~8 h), **SOCO-14**,
**SOCO-15** and **SOCO-22** since r#3 (~2 h).

**THE CONTRAST IS THE EVIDENCE, and it is why this is not a harness problem.** In the same window
the **NWPP** program dispatched and landed **three** lanes — NWPP-10 (#6104), NWPP-11 (#6105),
NWPP-13 (#6106), all merged 15:50–15:51 — and NYISO-231, MISO-256, PJM-H3b, CAISO-281 and SPP-38
all shipped besides. **Dispatch works everywhere except here.** Issuance is this desk's act;
dispatch is not, and the desk has now measured the gap rather than assuming a lane was slow.
Under gate **G15** none is graded LOST.

**Card served and RULED (owner, r#4): "Re-emit all five as one paste-ready block."** All five
re-pinned to `33a7c961` and emitted in dependency order in the sitting report. The desk's own
reading, recorded because it shaped the option set: the five are **file-disjoint** and NWPP just
demonstrated three-way concurrency without collision, so serialising them buys nothing.

**A REGISTRATION PIN THIS PLAN WAS MISSING, FOUND BY ANOTHER PROGRAM.** NWPP-10 flagged
`ISO_TO_BA_CODE` as "the W2 novel change" its plan had missed. **SOCO's §2.3 had missed it too**,
and the desk verified the consequence in the live code rather than taking the report on trust:
`data/zone_assignment.py:69` is a **7-key dict pinned to `SUPPORTED_ISOS`**, and `:1092` indexes it
bare — `df[ba == _ISO_TO_BA_CODE[iso]]` — so a registered SOCO without a key raises **`KeyError`**,
not a fallback. Added to §2.3 as a SOCO-20 checklist row. SOCO's case is trivial (`"SOCO": "SOCO"`,
the BA code and the registry key being the same string); NWPP's is not, and its 17→1 map fails
**silently** at 13 call sites. **The lesson is the transfer, not the fix**: two addition programs
chartered four days apart both missed the same pin, so a §2.3-style atomicity list is only as good
as the last program that stress-tested it.

**Also carried to SOCO-13 in its re-emission: NWPP-13 is its sister lane and it has already run.**
Its WEIM STOP gate read **NO** (on-peak 22.6–37.5 % below Mid-C against a ±10 % bar; daily corr
0.74/0.95/0.67 against ≥0.80), the gate was fixed **ex ante** in a pushed PRECOMMIT before any value
was read, **no bar was moved afterwards**, and the lane landed nothing to `_validation-source`. That
is exactly the discipline SOCO-13's charter demands, now with a worked precedent in the same repo.
SOCO-13's re-emission also carries the anchor candidate **SOCO-12** found after its charter was
written — the SEEM Independent Market Auditor's public monthly price series, 2022-11 → 2026-07.

**Gates at `33a7c961`** — unchanged from r#3; the base-branch debt persists:

| Gate | Exit |
|---|---|
| `audit_keepers.py --check` | **1 — RED** (MISO E13 ×4) |
| `check_registry_payload_parity.py` | **1 — RED** |
| `check_gate_a_provenance.py` | **1 — RED** (MISO + NYISO) |
| `check_mechanism_matrix.py` · `check_bench_freshness.py` · `check_golden_manifest.py` | 0 |
| `ci_refactor_guards.py` | **UNREAD** — `numpy` absent in a `DATA PROFILE: code` container |

**Next act:** sitting #5 — grade whichever of the five land, BY CONTENT. **SOCO-20 is issuable the
moment SOCO-15 lands and G22 is discharged**; nothing else blocks it.

---

### r#3 — 2026-09-13 — ALL THREE W1 LANES LAND AND GRADE PASS · SEVEN CARDS RULED · THE EVIDENCE INVERTED TWO OF THE DESK'S OWN RECOMMENDATIONS (main `c93b0d27`)

**Graded BY CONTENT, not by claim** — each FINDING opened and checked against what its dispatch
said. All three W1 lanes **PASS**, and two of them found things the charter did not anticipate.

| Lane | Verdict | What it actually delivered |
|---|---|---|
| **SOCO-10** audit (PR #6091) | **PASS** | Census **336 plants / 788 gens / 70,667.2 MW** — and it caught that the charter's 335/786/70,665.7 is that figure *minus* the MA row while the charter's own per-state list *includes* it: both right about different sets, one labelled. MA **rejected** (plant 67241, Berkshire MA, NERC **NPCC** — a BA-field mis-entry) under a stated two-key rule; FL **kept** (6 plants, SERC, panhandle). Reconciled to Southern's 10-K on an explicit whole-unit-vs-ownership bridge, the wedge proved exactly on nuclear (10-K 4,786.7 vs EIA-860 8,282.4 MW = Oglethorpe 30 / MEAG 22.7 / Dalton 2.2 %). **Gate G19 CLOSED**: `America/Chicago`, DST-aware, hour-ending, measured over all 26,304 rows. CEMS gap **91.6 %** of fossil MW (SPP's was 44.9 %) |
| **SOCO-11** CEMS + 714 + interchange (PR #6083) | **PASS — including the way it failed** | 8/8 CAMPD files landed, every one re-checked against the charter's named sibling `MS_2024` after the fetcher had used a different one. **The FERC-714 gate FAILED and the lane stopped, rescaling nothing** (rule 13) and deriving no share (rule 23). Interchange confirms the charter to **0.001 TWh** and is the cleanest book in the corpus (zero NaN hours, nine DIBAs, three years) |
| **SOCO-12** documents + gas (PR #6092) | **PASS** | **Gate G12 MET** with a real edition and vintage. **SEEM corrected on three counts** — live **Nov 2022** not Nov 2023; SEEM publishes no price *but its Independent Market Auditor does, monthly, publicly, back to 2022-11*; and a **FERC-accepted settlement (2026-01-05)** will oblige hourly posting. Then it **refused its own find as a benchmark** on four disqualifying grounds and re-cast it as a boundedness anchor — exactly what gate G17 demands |

**THE TWO INVERSIONS, because they are the sitting's real content.**

1. **Card S3's recommendation was conditional and the condition failed.** SOCO-10 predicted the
   three OpCos *structurally* cannot sum to the BA (Georgia Power's winter peak 16,284 MW against
   the BA's 47,368 MW); SOCO-11 measured it — **73.2 %**, short **61.4 / 66.2 / 64.2 TWh** in every
   hour of every year, shape right (r ≈ 0.99) and level short, which is the signature of whole
   planning areas absent rather than a scaling error. **The desk recommended 1 zone. The owner ruled
   3 zones on the six-respondent sum, and that is now the plan of record.** The desk's stated risk —
   an attribution nobody has cited — does not vanish with the ruling, so it is *controlled* rather
   than re-litigated: new gate **G22** makes a cited BA-membership basis a hard precondition on
   SOCO-32, and new lane **SOCO-14** exists to produce it. If SOCO-14 returns a documented NO the
   ruling's premise is gone and S3 goes back to the owner — it is not worked around.

2. **Card S8 was answered and the answer is worse than the card assumed — now card S12.** SOCO-10
   found by *calling the live code* that `cod_ramp.effective_cod` always prefers a plant's
   capacity-weighted mean COD for the ONLINE date; the per-unit preference exists only for
   retirement. `load_cod_map()[649] -> (2005, 5)`, so **Vogtle 3 and 4 are online all 12 months of
   2023**. Phantom **+12.979 TWh** (+24.8 %); a 2023 SOCO backcast would read ≈65.41 TWh of nuclear,
   **above measured 2025's 64.17**, inverting the commissioning step and displacing ~13 TWh of gas.
   Blast radius **SOCO 3,040.3 MW vs next-worst SPP 1,127.4** — 2.7×. Ruled: charter the cross-ISO
   repair **before** SOCO-20, as lane **SOCO-15**, never inside the registration PR.

**Seven cards ruled** (verbatim in §2, appended to plan §3): **S3** 3 zones / six-respondent sum ·
**S4** served interchange · **S5** DOE/LBNL ICE VOLL · **S6** winter 26.0 % scalar · **S7** CAES → gas
CT at the **25 MW rating** (SOCO-10 corrected the charter's 110 MW nameplate — a 77 % derate) ·
**S11** this desk charters SOCO-22 · **S12** (new) charter SOCO-15 before SOCO-20. **S9** stays
deferred behind SOCO-13 as the plan says; **S10** waits for a keeper.

**Issued this sitting: SOCO-14 `[OPUS]`, SOCO-15 `[FABLE]`, SOCO-22 `[FABLE]`** — all three created
by rulings at this sitting, all pinned `c93b0d27`, charters in the sitting report.

**SOCO-13 and SOCO-21 (issued r#2) have NOT landed** — no branch, no PR, no FINDING on origin.
**Not graded LOST** (gate G15): the desk asks dispatch status rather than inferring from absence,
and that question is in this sitting's report.

**Gates at `c93b0d27`** — the base-branch debt recorded at r#2 has **grown**, not cleared:

| Gate | Exit | Note |
|---|---|---|
| `audit_keepers.py --check` | **1 — RED** | was EXIT 0 at `7404ef12` twelve hours ago; the MISO E13 rows landed in between |
| `check_registry_payload_parity.py` | **1 — RED** | R-c, CAISO's |
| `check_gate_a_provenance.py` | **1 — RED** | R-d, MISO **and** NYISO |
| `check_mechanism_matrix.py` | 0 | warnings, other programs' |
| `check_bench_freshness.py` | 0 | |
| `check_golden_manifest.py` | 0 | |
| `ci_refactor_guards.py` | **UNREAD** | `numpy` absent in a `DATA PROFILE: code` container; not carried forward green |

**Next act:** sitting #4 — grade SOCO-13/14/15/21/22 by content, then issue **SOCO-20** (its G12
blocker is now MET; it still needs S3's G22 discharged and SOCO-15 landed first).

---

### r#2 — 2026-09-13 — CARDS S1 AND S2 RULED · SOCO-13 AND SOCO-21 ISSUED · rules 33/34/35 folded into the plan (main `7404ef12`)

**What happened.** Both pending cards were re-served as clickable decision cards and **both were
ruled**, which unblocked two lanes in one sitting. The desk also performed the refresh edit it owns
rather than a lane: CLAUDE.md gained rule **35 `[R-PROMOTE]`** and a **correction to rule 34(a)**
after this program was chartered, and neither was reflected anywhere in the plan.

**Graded — nothing, and deliberately not graded LOST.** SOCO-10/11/12 have no branch, PR or FINDING
on `origin` (`git ls-remote --heads origin | grep -i soco` → empty; `git log origin/main
--grep=SOCO` → only the desk's own two commits). Under handoff §0.3 / gate **G15** branch-name
matching is a weak detector and absence is not evidence, so the desk **asked dispatch status**
instead of grading. The owner confirms **all three are dispatched and running**. They are LIVE at
the r#1 pin `2c2fc065` and will be graded BY CONTENT — the cited FINDING opened, never a green CI
check — at sitting #3. No charter was re-issued.

**Rulings (verbatim in §2 and appended to the plan's §3 rows).**
- **S1 — the key is `SOCO`.** The recommendation as served. `ISO_EV_KEY["SOCO"] = "O"` and the shard
  filename `SOCO.js` follow from it, so SOCO-21's object is now fully determined.
- **S2 — BOTH limbs.** Charter SOCO-13's FERC-EQR index with its pre-registered STOP gate, **and**
  rule the fallback now: with no price benchmark a SOCO run reads a determination naming its own
  basis (e.g. `PHYSICALLY CALIBRATED — price unscored, no public price exists`), scored on
  C1/C2/C4/C6/C8, **never `CALIBRATED`**, price gap on the determination basis at full magnitude.
  Five binding consequences are written into plan §3 so no lane re-derives them. Gate **G17** is
  untouched — a neighbouring hub stays refused, ruling or no ruling.

**Issued this sitting — SOCO-13 `[FABLE]` and SOCO-21 `[OPUS]`**, both verbatim from plan §8 with
§8.0 pasted in and `origin/main` pinned at **`7404ef12`**.
- **SOCO-13** was unblocked by S2 directly; its charter's own first line ("ONLY START AFTER the
  owner has ruled card S2") is now satisfied and the ruling is quoted into the issued prompt.
- **SOCO-21** was unblocked by S1 **plus** a collision-protocol correction (§4 C-2, and §6). Before
  issuing, the desk **measured** that the lane can pass its own gate ahead of SOCO-20: nothing in
  `scripts/lib/mech_matrix.py` or `scripts/check_mechanism_matrix.py` validates `ISO_ORDER` /
  `isos` against `SUPPORTED_ISOS` (`grep` for either returns nothing in both files), and
  `tests/unit/config/test_mechanism_matrix_shard_migration.py:128` documents the precedent in its
  own comment — *"a column is seeded before its first keeper exists (SPP, seeded at SPP-21
  2026-09-06; first keeper at SPP-40)"*. An eight-ISO matrix over a seven-ISO registry is therefore
  a supported intermediate state, not a half-landed matrix.

**Refresh edit — rules 33/34/35 reconciled into the plan.** This is the desk's own work under
handoff §5, not a lane's:
- **G13 REWRITTEN.** As chartered it read *".gitignore the bundle family — never `rm`"*, which
  **collides head-on** with rule 34(a) as corrected 2026-09-12: the SHARD must push its bundle, and
  *"a shard prompt that tells its shard to gitignore or omit the bundle is a defect in the prompt."*
  G13 now states the seam — `.gitignore` is the **parent's** tree; the shard appends a `.gitignore`
  **negation** for its own out-dir and uses a **plain `git add`, never `git add -f`**; the bundle
  must carry `dispatch/<year>_P1.parquet`; the parent keeps per-year dirs out of `main`; never `rm`.
  Left unrepaired, this program's W4 charter would have stranded its first keeper's bytes on an
  ephemeral container — the miso-255 incident, pre-ordered.
- **G20 NEW** (rule 33 `[R-SHARD-ARCHIVE]`): archive on *"the parent has it"*, verify retrievability
  with `git ls-tree` first (34(d)), pin recovery to a **full 40-char SHA**, never delete a branch
  carrying an undecided bundle, and the measured **HTTP 403** on branch deletion with its misleading
  `Everything up-to-date` symptom.
- **G21 NEW** (rule 35 `[R-PROMOTE]`): the promoting session prunes the outgoing keeper's three
  stores; enumerate the year union **before** pruning; the incoming keeper covers it; promote →
  verify (E1) → delete; `audit_keepers.py` **E13** is the invariant.
- **§8.0 collision rules**: rule 7 corrected to the real shard mechanics, **rules 8 and 9 added**
  (archive, promotion). Every future SOCO charter inherits them.
- **SOCO-40's W4 bullet** now carries the mechanics, the S2 price posture, the in-session promotion
  question, and the year-set duty: 2023–2025 IS the union today, but manifest row 9 (holdout
  2019–2022) changes that the moment it lands — thereafter every batch covers the union, one shard
  per year (34(c)), and an unstamped year drops off the report silently (30(a) + 35(c)).
- **Definition of done** row 2 rewritten to S2's ruling; **row 7 added** for the rule-35 invariant.
  **Card S11 added** (§3) — see below.

**Card S11 raised, not assumed.** S2's ruling authorizes the determination class; it does not write
it. `scripts/calibration_verdict.py` carries no branch that can express it, so **W4 cannot score
until someone does**. Plan §1 says this desk does not charter rubric changes — but that prohibition
was written when the question was unruled. The desk **recommends** chartering it itself as
**SOCO-22 `[FABLE]`**, narrowly scoped (an added branch no existing ISO can reach, byte-identity
proof over all seven keepers' verdicts as the exit), because routing it to a desk with no reason to
prioritise it is exactly how R-a sat open. **The desk did not act on its own recommendation** — the
card is served at sitting #3.

**Gates at `7404ef12`** (7 run, exits recorded, none carried forward):

| Gate | Exit | Note |
|---|---|---|
| `audit_keepers.py --check` | **0** | 0 failures, 3 warnings |
| `check_registry_payload_parity.py` | **1 — RED** | 1 failure, **not this program's**: `results/calibration/caiso279_ablate_dswcouple_span` is a dead solve output mapping to no retained sidecar. ROUTED (§3 R-c) |
| `check_gate_a_provenance.py` | **1 — RED** | 1 failure, **not this program's**: NYISO's `gate.a_keeper_marker` cites superseded `2026-09-09-nyiso-221-fuelvintage-span` against live `2026-09-12-nyiso229-hourgrain-span`. ROUTED (§3 R-d) |
| `check_mechanism_matrix.py` | **0** | 3 warnings, all other programs': 2 anchor-line drifts, 1 SPP §5.x prose header not naming its keeper. Diff gate NOT RUN (no `--base`) — a 0 here is not a registration verdict |
| `check_bench_freshness.py` | **0** | 34 parts, 0 stale, 34 carrying engine drift |
| `check_golden_manifest.py` | **0** | 57 manifests / 100 entries; 28 stale vs the live keeper, reported not failed |
| `ci_refactor_guards.py` | **UNREAD** | `ModuleNotFoundError: No module named 'numpy'` — this is a `DATA PROFILE: code` container. Recorded UNREAD, **not** carried forward green (handoff §0.6) |

**The two REDs are the desk's own gates G13 and G21 observed live in other programs**, one day after
the rules that name them landed. That is why the refresh edit was not deferred.

**ADDENDUM (same sitting, after the push). CI on this desk's own three-markdown-file PR came back
with FIVE red checks, and every one is a base-branch condition in another program's files** — which
is the desk's seven-gate read at `7404ef12` reproduced by CI on `c4d4a108` and then some. Verified
by re-running the same checkers in-session against this tree, never by reading the red ticks:

| Failing CI check | What it says | Whose |
|---|---|---|
| Keeper-integrity gates | `audit_keepers` FAIL — **4× E13 on MISO**: `2026-09-09-miso-250-ep-gas` registered but neither keeper nor stamped, and `miso-251-{screen2022,tp2020,tp2021}` each stamped to that superseded id; + E11 (NYISO lineage baseline) and 3× E3 | MISO lane |
| FR-21 forecast-board staleness | gate-(a): MISO **and** NYISO markers both cite superseded keepers | capx gate (a) / promoting lanes |
| Ruff lint + format | 2 errors, e.g. unused `drift` at `scripts/gen_nyiso229_attestation.py:63` | NYISO lane |
| Pinned default cache key | default key `1eefed492204fab7` → `bd2b4657f9b5df7e` — a `ScenarioConfig` field landed without its pin re-mint | capx |
| Structural refactor guards | the same key mismatch, 1 failed / 99 passed | capx |

**Stood down with one PR comment and no ported fix, because every repair lives in `src/`, `scripts/`
or `frontend/data/backcast/`** — surfaces this desk is forbidden to write, and no fix PR exists that
the desk has read. **No re-run spent**: a hash-literal mismatch, a registry identity mismatch and a
static lint error are deterministic, and the confirmation a re-run would give was taken by running
the checkers directly instead.

**The finding that matters more than the standing-down.** The four MISO `E13` rows ARE rule 35
`[R-PROMOTE]` (f)'s invariant firing on a real unswept promotion — the same failure mode this desk
wrote into the plan as gate **G21** hours earlier, before this CI run existed, and while the desk's
own local read at `7404ef12` showed `audit_keepers` at **EXIT 0**. Between that read and CI, MISO
promoted and did not sweep; the count went 0 → 4. **A gate this desk added on principle went red on
`main` the same afternoon, four times over.** Recorded here because the desk's r#2 entry above says
the two REDs were "why the refresh edit was not deferred" — this strengthens that claim rather than
merely repeating it, and it is the second unswept promotion (NYISO) plus a third ISO's, inside one
week of the rule landing.

**Next act:** sitting #3 — grade SOCO-10/11/12 BY CONTENT, grade SOCO-13/21, serve **S3–S9** with
W1's evidence and **S11**, then issue W2 (SOCO-20 — still additionally blocked on manifest row 7,
the LTLF edition + vintage, gate G12).

---

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
| SOCO-10 audit | OPUS | W1 | **LANDED r#3 — GRADED PASS** | PR #6091 (`a23a4212`, `b4d0dd92`) | `FINDING-soco-10-2026-09-13.md` + `soco-data-audit.md` |
| SOCO-11 CEMS + FERC-714 + interchange | OPUS | W1 | **LANDED r#3 — GRADED PASS**, gate failure included | PR #6083 | `FINDING-soco-11-2026-09-13.md` |
| SOCO-12 documents + gas | OPUS | W1 | **LANDED r#3 — GRADED PASS**; gate G12 MET | PR #6092 (`738fc0ab`, `98c1fd92`) | `FINDING-soco-12-2026-09-13.md` |
| SOCO-13 EQR price index | FABLE | W1 | **LANDED r#5 — GRADED PASS, verdict NO** (3 of 5 gates fail; no bar moved) | PR #6129 | `FINDING-soco-13-2026-09-13.md` |
| SOCO-14 BA membership | OPUS | W1 | **LANDED r#5 — GRADED PASS; gate G22 FAIL, 2 of 3 cited** → card S3 re-ruled to the five-set | merged | `FINDING-soco-14-2026-09-13.md` |
| SOCO-15 COD seam (cross-ISO) | FABLE | W1.5 | **LANDED r#5 — GRADED PASS**, all three exit conditions MET; **SOCO-20 CLEARED**. Owes a `## Log entry` (desk stub in its place) | PR #6127/#6135 | `FINDING-soco-15-2026-09-13.md` |
| SOCO-22 rubric class | FABLE | W1.5 | **LANDED r#5 — GRADED PASS**, rubric v3.8, seven keepers byte-identical; NWPP adopted it | merged | `FINDING-soco-22-2026-09-13.md` |
| SOCO-20 registration | FABLE | W2 | **CLEARED AND ISSUED r#5** — every precondition discharged: cards ruled, G12 MET, G22 discharged on the five-set, SOCO-15 landed with seven cache keys byte-identical | — | — |
| SOCO-21 matrix shard | OPUS | W2 | **LANDED r#5 — GRADED PASS**, 327 ids / 168 `U` / 159 `·`, no verdict minted. Owes a `## Log entry` (desk stub in its place) | merged | `FINDING-soco-21-2026-09-13.md` |
| SOCO-30 outages + tranches | OPUS | W3 | **LANDED r#8 — GRADED PASS.** Gate G4 both legs; 1,119 windows; zero measured full-year CEMS outages; three defects routed | PR #6179 / #6181 | `FINDING-soco-30-2026-09-16.md` |
| SOCO-31 benchmarks | OPUS | W3 | **LANDED r#8 — GRADED PASS.** Gate G9 **exactly zero**, re-measured by the desk from the diff (+295/−1, the deletion a date stamp); price line held under pressure | PR #6185 | `FINDING-soco-31-2026-09-16.md` |
| SOCO-32 zonal shares + solar + gas hub | OPUS | W3 | **ISSUED, NOT DISPATCHED** — no branch, no commit, no FINDING. **NOT graded LOST** (gate G15). It is SOCO-40's last open precondition | — | — |
| SOCO-33 seam derive | OPUS | W3 | **LANDED r#8 — GRADED PASS.** Net-exporter sanity on both clocks; sign convention verified by shift test; **G17 never approached**; headline = the interface limits | PR #6180 | `FINDING-soco-33-2026-09-16.md` |
| SOCO-34 site + docs | OPUS | W3 | **FINISHED, NOT MERGED — NO PR EXISTS.** Branch `claude/soco-34-site-docs-pxkmb5` @ `1f71ec097b3f4b7e4ef17a5f88225abdd4c988c5`, zero conflicts vs `main`. **GRADED PASS r#8 off the branch.** The owner owes it a PR | branch only | `FINDING-soco-34-2026-09-16.md` (on the branch) |
| SOCO-40 first solve | FABLE | W4 | **BLOCKED ON SOCO-32 ALONE.** Card S11 is discharged (SOCO-22 landed r#5, rubric v3.8); SOCO-30 and SOCO-31 landed r#8. Gate G4 is 2 of 3. **The charter is not issuable until SOCO-32 lands** | — | — |
| ~~SOCO-22 rubric class (duplicate row)~~ | — | — | **STALE ROW, superseded by the SOCO-22 row above** — the lane was issued r#3 and graded PASS r#5. Kept struck rather than deleted so the r#2→r#3 sequence stays readable | — | — |
| SOCO-54/55/56/57 levers | — | W5 | pre-declared, not issuable | — | — |
| W6 forecast entry | — | W6 | ROUTED to the capx director (card S10) | — | — |

## 2. Owner rulings — verbatim, numbered

| # | Card | Ruling | Date |
|---|---|---|---|
| O-1 | charter | *"Use the add spp workstream as a reference and develop a plan and prompt pack to do whatever iso Hillabee gas plant in Alabama is in."* | 2026-09-12 |
| S1 | the registry key | **RULED r#2**, verbatim: *"SOCO (Recommended) — The EIA-930/EIA-860 balancing-authority code. Already the on-disk filename convention (`SOCO hourly.parquet`, `SOCO_fueltype.parquet`), so no crosswalk is invented. Lets every doc say 'balancing authority' rather than 'ISO'."* | 2026-09-13 |
| S2 | price benchmark / rubric class | **RULED r#2**, verbatim: *"Both: build the EQR index AND rule the fallback class now (Recommended) — Issue SOCO-13 to build a footprint-hourly volume-weighted price index from FERC EQR transaction data, with a STOP gate registered before any data is read; AND rule now that if it fails, a SOCO run reads a determination that names its own basis (e.g. PHYSICALLY CALIBRATED — price unscored, no public price exists) scored on C1/C2/C4/C6/C8, never CALIBRATED, with the price gap on the determination basis at full magnitude."* Five binding consequences: plan §3 card S2 | 2026-09-13 |
| S3 | topology | **RULED r#3**, verbatim: *"3 zones now on the six-respondent sum"* — **over the desk's own 1-zone recommendation**, with full knowledge of the desk's stated risk. Conditions the desk attached rather than re-litigating: gate **G22** + lane **SOCO-14**, geographic zone names, and the split is never sold as improving accuracy | 2026-09-13 |
| S4 | seams | **RULED r#3**, verbatim: *"Served measured EIA-930 interchange for the first keeper (Recommended)"* — priced neighbours register default-off as lever SOCO-56 | 2026-09-13 |
| S5 | VOLL | **RULED r#3**, verbatim: *"DOE/LBNL ICE calculator, SERC/Southeast mix (Recommended)"* — $2,000 only as a documented fallback; Brattle cited as method, never value | 2026-09-13 |
| S6 | adequacy | **RULED r#3**, verbatim: *"Register winter 26.0% as the scalar, misalignment documented (Recommended)"* — SOCO is winter-peaking in 2 of 3 backcast years; a seasonal registry for all ISOs was offered and declined as an ISO-addition act | 2026-09-13 |
| S7 | the CAES unit | **RULED r#3**, verbatim: *"Map to a gas CT at the 25 MW rating (Recommended)"* — SOCO-10 corrected the charter's 110 MW nameplate to the source's own 25 MW rating, a 77 % derate | 2026-09-13 |
| S8 | mid-window nuclear commissioning | **ANSWERED AND SUPERSEDED BY S12** — the machinery resolves neither the month nor the year for a brownfield addition | 2026-09-13 |
| S9 | `TAIL_THRESHOLD` | **RESOLVED r#5 — n/a, no card needed.** SOCO-13 returned NO, so no series, so no tail; gate G6's pre-specified skip branch fires and the three edits are deliberately skipped | 2026-09-14 |
| S3 | topology (RE-RULED) | **RE-RULED r#5**, verbatim: *"FIVE respondents — the fully-cited set (Recommended)"* — AP + GP + MP + Oglethorpe (107) + MEAG (210); Southern Power (186) EXCLUDED as a documented NO and named on the first keeper's determination basis. Residual 3.03 / 2.92 / 1.26 % | 2026-09-14 |
| S10 | W6 routing | **PENDING** — due when a keeper exists | — |
| S11 | who implements S2's determination class | **RULED r#3**, verbatim: *"This desk charters it as SOCO-22 [FABLE] (Recommended)"* — one added branch keyed on the ABSENCE of an `actual_lmp.json` block, byte-identity proof over all seven keepers as its exit, serving NWPP's card N2 with the same amendment. Issued r#3 | 2026-09-13 |
| S12 | the COD-seam defect (SOCO-10's R-4) | **RAISED AND RULED r#3**, verbatim: *"Charter a cross-ISO repair lane BEFORE SOCO-20 (Recommended)"* — issued as SOCO-15 `[FABLE]`. Floor stands regardless of outcome: the bias is stated on SOCO's first keeper's determination basis | 2026-09-13 |

## 3. Routed — open, not this desk's to fix

| # | Item | Owner | Why it stays visible |
|---|---|---|---|
| R-a | The rubric cannot express a determination for a region with no price benchmark | **CLOSED r#3** — S2 authorized the class, S11 assigned the scorer, and lane **SOCO-22** is issued | Closed as a routed item; it is now a lane to grade, not an open question. W4 still cannot score until SOCO-22 lands |
| R-b | The NWPP program shares card S2's problem in a milder form. **It is no longer hypothetical: NWPP was chartered 2026-09-13** (`docs/multi-iso/nwpp-addition-plan-2026-09.md`, landed on `main` between this desk's push and its rebase), it cites the SOCO charter as its non-market precedent, and its §2.6 raises card **N2** — the same question | the owner; the NWPP desk | **S2's ruling is the "once", on the CLASS.** The two programs are not identical: NWPP's §2.6 records that WEIM 15-minute LMPs for its BAs are anonymously fetchable (CAISO OASIS `PRC_RTPD_LMP` probed 200), so NWPP may need the no-price class only partially or not at all. What must not happen is **two scorer amendments**: card **S11** should be scoped to a determination class **keyed on the absence of an `actual_lmp.json` block**, which serves any region without a price benchmark, rather than a SOCO-specific branch. This desk surfaces that and does not charter across the boundary |
| R-c | `check_registry_payload_parity` **RED** at `7404ef12`: `results/calibration/caiso279_ablate_dswcouple_span` is a dead solve output mapping to no retained sidecar (Class-E point 4) | the CAISO calibration lane / caiso-279 | Not this desk's file and not this desk's to fix. It is **gate G13 observed live** — the exact failure mode this desk just wrote into its own W4 charter |
| R-d | `check_gate_a_provenance` **RED**, and it grew inside this sitting: NYISO's marker cites superseded `2026-09-09-nyiso-221-fuelvintage-span` (live `2026-09-12-nyiso229-hourgrain-span`) **and, as of `c4d4a108`, MISO's cites superseded `2026-09-09-miso-250-ep-gas`** (live `2026-09-12-miso-255-sil-measured`) | the NYISO and MISO lanes / the capx director's gate (a) | Not this desk's files. **Gate G21 / rule 35 `[R-PROMOTE]` observed live, twice, within days of the rule landing** |
| R-f | **`cod_ramp.effective_cod` prefers a plant's mean COD for the ONLINE date** — a general defect in shared `src/`, worst in SOCO (3,040.3 MW, 2.7× the next footprint) but live in all eight | **NO LONGER ROUTED — the owner ruled it (card S12) and the desk chartered SOCO-15** | Kept visible because the repair moves **results** for all seven registered keepers; each ISO's lane will see its own numbers move and must not read it as its own regression |
| R-g | **SHA256SUMS.txt scope** — SOCO-11 deliberately did not add rows for the tracked 2019-2026 CEMS files, since that file's own header scopes it to the 35 gitignored `<ST>_2018` extracts and git's blob hashes are the tracked files' integrity record | the desk | The desk **agrees with the lane** and records it as correct, not outstanding: adding rows would misrepresent the file's stated scope. No action; noted so a later lane does not "fix" it |
| R-h | **EIA-930 defect screens catch none of the three real SOCO defects** SOCO-10 found (four `NG: NG` hours at ~70 GW against a 36,336 MW gas fleet; the netgen identity breaking in 2025 only, 595 h; a 1-h partial demand dropout) — `_screen_demand_spikes` is high-side only, `_screen_demand_dropouts` is exact-0.0 only, and **no repo screen touches a fuel column at all** | the data/curation owner | SOCO-10 correctly proposed **no new constant** (rule 23 — setting a threshold after seeing the outliers is a fitted threshold). Cross-ISO, not SOCO's to fix |
| R-i | **SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in EIA-930 for 2023 and most of 2024** — `NG: PS`/`BAT`/`SNB`/`OES` are a taxonomy cut-over at 2024-07-15, and `NG: WAT` never goes negative before it (min +32 MW), so PS charging was not folded into hydro, it was not reported | SOCO-31 (benchmarks) | A hard constraint on the **C1 `fuelmix`** benchmark, not a bug to fix. Must be stated on SOCO's first keeper's determination basis |
| R-j | **The base-branch debt is now GROWING with each promotion, not static.** At r#5: gate-(a) red on **three** ISOs (MISO, NYISO, **SPP**) plus an SPP marker/`calibration-complete.json` inconsistency; FR-22 on **two** undeclared NYISO mechanisms (`gas_offer_margin_zonal_anchor_vintage`, `nyiso_st_gas_econ_bands_deleaked`); `audit_keepers` at 5 failures including a new **S1** status-stale on ERCOT | the promoting lanes; the capx director's gate (a) | Every increment arrived with a promotion that did not finish its duties — the exact failure mode rule 35 `[R-PROMOTE]` names. Not this desk's files. **Reported once here; the desk will not re-report it each sitting.** **PARTLY FALSIFIED at the r#5 check-in (main `c6c70190`) — corrected rather than left standing.** "Growing with each promotion" was true at r#5 and is not a law: measured just now, `audit_keepers --check` is **1 failure / 4 warnings**, down from 5 failures. **MISO's E13 ×4 CLEARED** — the MISO promotion swept and `2026-09-12-miso-255-sil-measured` is designated with no orphan runs, which is rule 35 `[R-PROMOTE]`'s invariant actually holding. What remains: the lone FAILURE is **S1 status-stale, and it grew from ERCOT alone to ERCOT + CAISO + NEISO** (fix: `python scripts/build_status.py`, three ISOs' `status/*.js`, so rule 35(a) puts it on those lanes); plus two new WARNs — **NYISO E11** (see G21) and **MISO E3** (`meta.json` years `[2020…2025]` vs `calibration_flags` years `[2023]`). The honest shape is **churn, not monotone growth**: promotions clear their own debt and open new debt elsewhere |
| R-e | `audit_keepers` **E13 RED ×4 on MISO** at `c4d4a108` — `2026-09-09-miso-250-ep-gas` registered but neither keeper nor stamped, and three `miso-251` runs stamped to it; plus E11 on NYISO's missing lineage baseline. Separately: **Ruff** 2 errors (`scripts/gen_nyiso229_attestation.py:63`) and the **default cache-key pin** off its literal (`1eefed49…` → `bd2b4657…`), which reds both the pin check and the structural guards | MISO lane · NYISO lane · capx (cache fingerprint) | All in `src/`/`scripts/`/`frontend/`, none this desk's to write. Stood down on PR #6090 with one comment and no ported fix; no re-run spent (deterministic, reproduced locally). **They will red every SOCO PR until repaired**, so a future sitting must not read them as its own regression |
| R-k | **The BLOCKING `Structural refactor guards` gate is red on a FALSE POSITIVE stacked on a real stale docstring — and both obvious repairs are wrong.** Root-caused at the r#5 check-in from the #6144 failure. (i) `scripts/ci_refactor_guards.py:52` is `_SCRIPT_REF_RE = re.compile(r"scripts/[\w/.\-]+\.py")` — **no left word boundary**, so any path *containing* `.../scripts/foo.py` is read as repo-root `scripts/foo.py`. Proved empirically: on `scripts/run_calibration_full.py:3780` it yields `scripts/test_recorded_config_gas_anchor_mirror.py`; adding `(?<![\w/])` yields **zero** matches. (ii) that same docstring is **independently wrong** — it cites `tests/unit/`**`scripts`**`/test_recorded_config_gas_anchor_mirror.py` but the file is tracked at `tests/unit/`**`data`**`/…` (created by nyiso-231, `0acedb7e`). So the gate is red for a genuine doc error, surfaced through a buggy lint | the CI owner (the regex) · the NYISO lane (the docstring) | **Both need fixing, and the two tempting one-liners are each a paper-over**: creating a stub at `scripts/` would satisfy a regex bug with a fake file, and adding the string to `KNOWN_DANGLING` would allowlist a real stale path AND leave the regex mis-reporting every future nested `scripts/` reference. A false positive in a blocking gate is worse than a true failure — it trains lanes to read a red as noise. Not this desk's files (`scripts/`). Diagnosis recorded here so the next lane does not repeat the four-call root-cause |
| R-l | **`process_eia860.rescope_generator_table_from_parquet` is NOT additive when columns differ** — its last line writes the RAW rebuild, so a rescope DROPS the eGRID `heat_rate` join (8,101 populated rows on the canonical table), ADDS `planned_retirement_month`, reorders `balancing_authority_code`, and admits foreign rows (one PJM plant, 60781). Found by SOCO-20 when its own rescope tripped `test_fleet` heat-rate pins, `test_egrid_boundary_heat_rate`, `test_cc_steam_part_reclass` and `test_derive_coal_sigmoid` | the data-curation owner (routed BY SOCO-20 through this desk) | **The committed tables are REPAIRED; the script is not.** The proven recipe is in gate G23 and in SOCO-20's FINDING §4: main's frame byte-for-byte + the new region's rows only, `heat_rate` joined from the PLNT23 cache, and **the non-new slice `.equals()` main's frame** asserted per file. **Every future region addition hits this** — SPP-20 (`3117f06a`) and NWPP-20 both ran the same routine, so their tables are worth the same `.equals()` audit |
| R-m | **D79 solve-surface: 20 undeclared SOCO rows** (`solve_surface_register.py --diff` shows SOCO 20 = its own new rows). There is no `--declare-iso` route, so a new region cannot declare its own rows without touching the shared declaration file | SOCO-DESK (the R-1 successor) | **Same state SPP-20 left**, so the gap is now two regions wide and is a registration-protocol defect rather than either lane's miss. Gate G8 is unaffected — 0 moved rows for all eight incumbents — so nothing is mis-keyed; what is missing is the declaration, not the correctness |
| R-n | **`config/solve_surface.py:75` calls SOCO "the eighth registered region"** — it is the NINTH; NWPP took eighth the same day. The PR title was corrected to "ninth" and the `_ISO_BUILDERS` comment is right, so this is the one place the same-day collision left stale | whoever next edits `solve_surface.py` | Cosmetic, and named only so a later reader does not trust it over `SUPPORTED_ISOS`. `src/`, outside this desk's write scope. (Swept the rest: `export_lce_lmp.py:109` and `test_mechanism_matrix_keeper_stamp.py:37` both read correctly in context) |
| R-o | **NWPP-35 swept the shared codebase-site prose to NINE regions and left SOCO's own blocks owed, citing the debt in place.** `iso-topologies.json` keys are the eight without SOCO and its `_meta.description` says so verbatim; `data-completeness.html:364` carries the same marker in a code comment; `config-reference.html:404` still says "the **eight** serialized … render below" | **SOCO-34** (folded into its §8 charter delta at r#7) | **Not a collision — a clean handover.** NWPP-35 stayed inside rule 25 `[R-ISO-SCOPE]` (it did not serialize another region's topology) and, instead of leaving the gap to be discovered, named the owing lane in the artifact. That is the behaviour this desk should hold its own lanes to, and it is worth saying so rather than only logging the debt |
| R-p | **`results/calibration/soco15_spp_arm` IS THIS PROGRAM'S OWN PARITY RED — a rule 29 `[R-SCREEN]` (c) delete-before-merge bundle that REACHED `main`.** 34 files / **126 MB**, tracked (commit `59c045e1`, *"SOCO-15 SPP arm: spp38_span recipe replayed at 4f33476c"*), **not** gitignored, mapping to no retained sidecar. Verified committed with `git ls-tree origin/main` — so this is **not** the local-working-tree false positive rule 31's 2026-09-16 correction describes; CI sees it | **the owner (a promotion/retention ruling), then whoever executes the `git rm -r`** | **The desk found it, routed it and did NOT delete it.** Rule 31 `[R-RETAIN]`'s bar is the OWNER's decision — "not needed in my judgement" is the ercot-255 reasoning verbatim — and `results/` is outside this desk's enumerated write scope besides. The record survives the bytes either way: `FINDING-soco-15-2026-09-13.md` carries the eight-footprint A/B at full magnitude, which is exactly what rule 29 (c) requires of a screen's record and what makes the bundle disposable **once ruled**. Until then it reddens `check_registry_payload_parity` on every PR, and a future sitting must not read it as another program's |
| R-q | **The `-layup` merit-order guard is COAL-ONLY in SOCO**, because `data/raw/gas_basis_by_iso_month.csv` has **zero SOCO rows**: all 238 gas units of the 279-unit panel drop out and the ~15 priced units are the 17 coal. NWPP-30 §7.1 reproduced the same shape | **SOCO-32** (it lands the gas hub), then a re-derive | Bounded and stated: until a SOCO gas basis exists, the `-layup` companion must **not** be read as "SOCO has no economic gas layup" — it is a panel that never contained gas. A one-line consequence of a missing input, not a defect in the derive |
| R-r | **The tranche file's primary-group filter drops 15 `(plant, group)` pairs / 4,872.9 MW — including 2,954.5 MW (25.7 %) of SOCO's COAL.** SOCO has 7 mixed plants; Barry, Daniel and Gaston each lose their COAL row to a CC or ST primary, which also inflates Barry's `median_cf` to the 150.0 cap. `--per-unit-attribution` is **not** a safe fix as-is: its classifier keys on CAMPD `unitType`, a prime-mover descriptor with no coal concept, and on the 2024 panel it re-seats all three onto CC/ST and finds **zero** coal | the data-curation owner; a later `[FABLE]` lane for the arming half | **Inert for W4 and the desk is not making it a card.** `CAMPD_BINNING_ISOS` is `{ERCOT, CAISO, NEISO, NYISO, PJM, MISO}` — **verified in `capacity_market.py`** — so SOCO's per-plant path is never entered and nothing in W4 reads this file. SOCO's absence is also the **norm for a new region**, not an omission: NWPP's own `ISOConfig` docstring records the identical posture (*"legacy heat-rate bins … NWPP is absent from `CAMPD_BINNING_ISOS`"*, owner ruling N8) and SPP is absent too. SOCO-20's comment that SOCO-30 would add SOCO "with the artifact" is therefore **not a duty SOCO-30 failed** — it is `src/`, a declared `solve_surface` value (`65b4e3e163ffd580`), a gate-G8 cache-key move and a `[FABLE]` call. The artifact now exists and §6.2 is the evidence a later lever weighs |
| R-s | **Four SOCO CC plants (6073, 7897, 55382, 57037) carry corrupt EIA-860 summer-capacity rows** and **1,412.3 MW is reconciled away at every fleet load** — existing committed behaviour, unchanged by SOCO-30, but every `unit_pct_of_plant` in the outage extract sits on that basis | the data-curation owner | Reported at full magnitude rather than silenced, as SOCO-32's charter also instructs for the same four plants. Three of the four are > 160 MW, so this is not a rounding-scale item |
| R-t | **THE INTERFACE LIMITS ARE THE BINDING OBSTACLE ON SOCO'S PRICED SEAMS, WITH A NUMBER ON IT.** Seven of eight registered `interface_limit_mw` values are contradicted by SOCO's own meter: arming them would refuse **10.66 / 12.81 / 14.21 TWh = 35.6 / 39.0 / 41.7 %** of those seams' gross throughput; `SOCO_SCEG` (126 MW) is over limit in **99.8 %** of 2025 hours and would lose 8.68 of its 9.78 TWh. `SOCO_MISO` (2,374 MW) is the only seam never exceeded in any hour of any year | **lever SOCO-56** (W5) — not W4 | **Blocks nothing in the first keeper**: card S4 ruled the served measured schedule, and `spec.py` records that all eight priced blocks are inert until `reference_price_interface` is armed, which no keeper does. It does **not** say the published values are wrong — they are a correctly cited 2024 Reserve Margin Study *average import transfer capability*, an adequacy quantity. It says they are the **wrong quantity for a transfer limit**, which is rule 14 `[R-ACCURATE]`'s misalignment exception, whose instruction is a **reconciled** real quantity (posted firm ATC/TTC, or the measured envelope with a stated basis) — never a guess and never the estimate. SPP-51's ERCOT-tie reconciliation is the precedent `spec.py` already names. **This is a precondition on SOCO-56 ahead of any heat-rate work** |
| R-u | **Both committed neighbour-heat-rate producers fail on `--iso SOCO`, and one fails SILENTLY.** `derive_neighbor_hr_by_year.py` exits **1** (`no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS`) — fail-closed, working as designed. `derive_neighbor_hr_elasticity.py` exits **0 with an empty table**: its `_NEIGHBOR_LMP_ISO` is still the pre-SPP-51 **global name map**, and SOCO's neighbours are named `SOCO_<DIBA>` *by design* (plan gate G10, rule 25), so **no** SOCO seam can ever resolve through it | the shared-producer owner (the same defect class SPP-51 fixed in the other producer) | SOCO-33 **routed both rather than patching a shared producer it does not own** — the STOP-and-route discipline again. Also routed by that lane and carried here so they are not lost: **`FLA hourly.parquet` ends 2025-01-31**, so `SOCO_FPL` / `SOCO_FPC` / `SOCO_TAL` have no 2025 load shape and cannot be priced that year (a fetch, a SOCO-56 precondition, **blocks nothing in the served keeper**); and the served scalar and the eight priced seams are **not the same quantity** — gross throughput roughly **doubles** — which is the step change rule 29 `[R-SCREEN]` makes SOCO-56 screen, its phase 0 computable with no LP from `soco_seam_diba_duration.csv` |
| R-v | **Three EIA-930 data items SOCO-31 found, all reported with NO new constant proposed (rule 23).** (i) **2025 `demand.min_mw` = 12,638 MW is a one-hour partial post** (2025-10-23 21:00 UTC — `D` and `NG` both halve and both recover), **0.486× median against a documented 0.2 floor, which no existing screen catches**; (ii) the **EIA-930 balance identity `NG − D − TI` is exactly zero in every hour of 2023 and 2024 and nonzero in 633 hours of 2025** (−0.6963 TWh, 0.28 % of net generation); (iii) 2025 carries **no** `eia923_incomplete` flag (ratio 0.9533, the most complete of all nine regions) **but its peaker census is not complete** — 6 of 23 `CT_PEAKER` plants and 1 of 6 `CC_CHP` have filed, so **no SOCO pair is gate-eligible and a 2025 gas-split comparison must defer to EIA-930** | the data/curation owner (screens); **SOCO-40** inherits (iii) | Extends **R-h**, which said the repo's screens catch none of SOCO's real defects — (i) is a **fourth** defect class and it is on the LOW side, where `_screen_demand_dropouts` only tests exact 0.0. **No downward bound was invented**, which is the correct refusal: a threshold set after seeing the outlier is a fitted threshold |

## 4. Collision register

| # | Surface | Other writer | Action |
|---|---|---|---|
| C-1 | `config/capacity_market.py`, `config/constants.py`, `model/interchange/spec.py` | capx D-lanes, the SCN desk, the per-ISO calibration lanes | SOCO-20 rebases last and appends; the desk re-checks their ledgers' top entries at issuance |
| C-2 | `docs/codebase-site/data/mechanism-matrix.js` (base file) | every ISO's lanes, whenever a field is added | **HOLD LIFTED r#2, and the test itself was wrong.** "Verify nobody is mid-edit" is unsatisfiable: writers on the matrix files are continuous (last base write `26737620` nyiso-230; last shard write `e24c0d90` caiso-279 — both within the pin window). The SPP desk retired the same precondition at its own r#2; the protocol is **rebase immediately before commit, one commit, re-run `check_mechanism_matrix`**, which is what SOCO-21's charter already says. See §6 |
| C-5 | `scripts/calibration_verdict.py` (SOCO-22) and the `cod_ramp` online-date seam (SOCO-15) — both are **shared `src/`/`scripts/` surfaces every ISO reads** | the capx D-lanes, the audit Y-lanes, every per-ISO calibration lane | **Both charters carry a byte-identity exit** (seven keepers' verdicts for SOCO-22; seven keepers' cache **keys** for SOCO-15, whose **results** deliberately move). Each rebases last and re-runs the gates. **SOCO-15 must land before SOCO-20**, so they are sequenced, not parallel |
| C-6 | `data/raw/zone-specific-demand/SOCO/SOURCES.md` | SOCO-11 (landed), SOCO-14 (issued) | **Append-only** for SOCO-14 — it adds BA-membership citations beneath SOCO-11's committed eight-respondent table and edits none of it |
| C-4 | `scripts/lib/mech_matrix.py` `ISO_ORDER`/`ISO_EV_KEY`, `tests/unit/config/test_mechanism_matrix_shard_migration.py` | SOCO-21 (this program), any ISO addition | **Measured gate-independent from SOCO-20 at r#2**: neither `mech_matrix.py` nor `check_mechanism_matrix.py` references `SUPPORTED_ISOS` or `_ISO_BUILDERS`, and the shard test's own comment records SPP's column being seeded before SPP's first keeper. An 8-ISO matrix over a 7-ISO registry is a supported intermediate state |
| C-3 | W1 lane surfaces (`campd-unit-level/`, `zone-specific-demand/`, the two fetch scripts, doc 00) | — | **CHECKED CLEAR at r#1**, pin `2c2fc065`: last touch `db5f11ea` (PR #6000), not a live lane. No hold |
| C-7 | `src/market_sim/data/fleet/models.py` `BA_CODE_TO_ISO` + the ISO→BA direction; the 8 `data/raw/eia-860/**/eia860_generators.parquet` tables; and ~23 further registration modules | **NWPP-20 (PR #6153), which MERGED FIRST** — 78 files, registered NWPP as the **eighth** builder at 2026-09-14 | **LIVE AND BLOCKING, measured at the r#5 check-in (main `c6c70190`).** SOCO-20's PR #6152 is complete (5 commits, 77 files, FINDING shipped) and now carries **55 conflict markers across 25+ files**. Two halves, and only one is mechanical: (i) the 8 parquets are **derived** — `process_eia860.py` filters on `BA_CODE_TO_ISO`, so re-running curation on merged main regenerates both regions' rows; (ii) `fleet/models.py` is **semantic** — SOCO-20's scalar inverse is the construction NWPP-20 deleted as a silent 1/17-of-a-pool bug, so taking SOCO's side breaks NWPP. Resolution recorded as gate **G23**; the rebase is the LANE's (parquet + `src/` are outside this desk's write scope). **SOCO is now the NINTH region, not the eighth** — every "eighth" in the plan, in SOCO-20's commit message and in its `fleet/models.py` comment is stale |

## 5. Issuance record

| Sitting | Date | Lanes issued | Cards served |
|---|---|---|---|
| r#8 | 2026-09-16 | **NONE — and deliberately none.** All five W3 charters were issued at r#6 and four have since run; **SOCO-32's charter is already paste-ready in plan §8** and carries card S3's five-respondent precondition, so re-transcribing it would risk E-6's failure mode for no gain. The desk **asks its dispatch status** (gate G15) rather than re-issuing it. SOCO-40 is **not** issued: gate G4 is 2 of 3 | **none served.** **S10** stays open (W6 routing, due when a keeper exists). Two questions are put to the owner in the report — SOCO-32's dispatch status, and the **R-p** retention ruling on `soco15_spp_arm` — but neither is a design card and neither is minted as one |
| r#0 | 2026-09-12 | none (charter commit) | none |
| r#1 | 2026-09-13 | **SOCO-10, SOCO-11, SOCO-12** (plan §8 W1, verbatim, pinned `2c2fc065`). SOCO-13 HELD on card S2 | **S1, S2** |
| r#2 | 2026-09-13 | **SOCO-13** (plan §8 W1, verbatim, pinned `7404ef12` — S2 ruled) · **SOCO-21** (plan §8 W2, verbatim, pinned `7404ef12` — S1 ruled, C-2 lifted) | **S1 RULED, S2 RULED**; **S11 raised**, due sitting #3 |
| r#6 | 2026-09-14 | **SOCO-30, SOCO-31, SOCO-32, SOCO-33, SOCO-34** (plan §8 W3), pinned `d54cd9c5`. Issued per §8's standing instruction — **against SPP's committed W3 charters** (`docs/multi-iso/spp-addition-plan-2026-09.md` §8, SPP-30 L972 / SPP-31 L1008 / SPP-32 L1056 / SPP-33 L1112 / SPP-34 L1144, read VERBATIM by each lane) **plus the SOCO deltas §8 names**, so the desk transcribes nothing and E-6's desk-drafted-charter failure mode is not re-entered. Each charter ends with the pack's EXIT boilerplate **including the `## Log entry` line** (E-6 remedy). **SOCO-32 carries card S3's exclusion of Southern Power (186) as a HARD PRECONDITION** | none — no card was due; **S10** (W6 forecast routing) stays open until a keeper exists |
| r#5 | 2026-09-14 | **SOCO-20** `[FABLE]` — the registration pin flip, cleared on every precondition | **S3 RE-RULED** (five-set); **S9 resolved n/a**; **S12 closed** |
| r#4 | 2026-09-13 | **RE-EMITTED all five undispatched lanes** — SOCO-13, SOCO-14, SOCO-15, SOCO-21, SOCO-22 — as one paste-ready block pinned `33a7c961`, in dependency order (owner ruling r#4). No new lane created | dispatch card SERVED and RULED |
| r#3 | 2026-09-13 | **SOCO-14** `[OPUS]` · **SOCO-15** `[FABLE]` · **SOCO-22** `[FABLE]` — all three created by this sitting's rulings, pinned `c93b0d27`. None existed in the charter's prompt pack, so all three are written charters rather than verbatim copies (plan §5 rows added) | **S3, S4, S5, S6, S7, S11 RULED; S12 raised AND ruled**; S8 answered/superseded; S9 still deferred |

## 6. Errors against interest

*(The desk records its own mistakes here, in its own words, so the next refresh does not repeat
them.)*

**E-9 (r#8, against the desk's own W3 charter deltas — and it is the E-5 shape for the THIRD time).
Two numbers the desk wrote into the W3 charters were wrong, and two different lanes had to correct
them before they could work.**

1. **SOCO-30's delta: *"CEMS COVERAGE IS 91.6 % OF FOSSIL MW, not 100 % … State the uncovered 8.4 %."*
   SOCO-10 measured 91.6 % as the ***MISSING*** share** — 45,797.3 MW of 50,005.0 MW with no CAMPD extract,
   **while AL and GA were still absent** — and SOCO-11 then landed AL and GA, which is precisely what closed
   that gap. Quoting it as post-SOCO-11 *coverage* double-counts the lane that fixed it. Re-measured on
   SOCO-10's own denominator, coverage is **95.95 %** and the gap is **4.05 %**, not 8.4 %. A lane that had
   trusted the delta would have gone looking for **twice** the uncovered MW that exist.
2. **SOCO-31's delta: *"demand 239.6 / 249.5 / 252.6 TWh"*. That is DEMAND + NET EXPORT, not demand.**
   SOCO-31 measured demand at **229.47 / 238.70 / 239.56** and showed the charter's figures are exactly
   `demand + export` (239.63 / 249.51 / 252.59, reproduced to 0.01 TWh). The desk's own plan §2.1 carries
   demand correctly at 229.47 / 239.33 / 239.36; the **handoff** §1 and the charter both carried the
   generation-side number under the demand label. On a net exporter this is not cosmetic — it is a 10–13 TWh
   label error on the single quantity the C1 benchmark is built from, and a lane trying to *reconcile* to it
   would have had a 4–5 % residual with nothing wrong.

**Both were checkable when written, and neither is a data finding — both are the desk paraphrasing a
number out of a FINDING and losing its polarity or its subject in the paraphrase.** That is E-5's lesson
(*"a charter's narrative sections carry the same cite-or-say-pending rule as its tables"*) failing on its
third outing, which means the lesson as stated was not operational enough. **Adopted forward, and this
one is mechanical: a charter delta that carries a number from a FINDING QUOTES THE FINDING'S OWN SENTENCE
around it — the subject and the direction included — rather than restating the number in the desk's words.
If the quote will not fit, cite the section and let the lane read it.**

*(Recorded in the lanes' favour, not the desk's: both lanes caught the error, said so in their FINDING's
first section, and proceeded on the measurement rather than on the charter. Neither stopped to ask, and
neither should have — the charter is not evidence.)*

**E-6 (r#5, against the desk's own charter-writing). Two of five lanes shipped no `## Log entry`,
and the charters the desk wrote are why.** Plan §8.0 rule 1 requires it, and the three W1 charters —
copied verbatim from the committed prompt pack — produced it three times out of three. The r#3/r#4
charters for SOCO-15 and SOCO-21 were **written by the desk rather than copied from the pack**, and
both omitted the explicit `## Log entry` line the pack's charters carry; both lanes then omitted the
section. That is a **100 % correlation between the desk's own drafting and the missing duty**, on a
population of five. Adopted forward: every desk-written charter ends with the pack's own EXIT
boilerplate, `## Log entry` line included, and the desk diffs a new charter against a pack charter
before issuing it.

**E-4 (r#3, against the charter — the biggest of the four so far). The desk built a plan around a
load spine it never checked, and a two-number test would have falsified it in the chartering
session.** Plan §2.5 declares FERC Form 714 "the zonal-load spine", names **three** respondents, and
card S3 recommends three zones on it. SOCO-10 found PUDL carries **eight** Southern-area respondents,
and disproved the three-respondent premise with arithmetic the charter had every input for:
**Georgia Power's own winter peak is 16,284 MW against a BA winter peak of 47,368 MW**. SOCO-11 then
spent a lane measuring what that implies — 73.2 %, short a quarter in every hour of every year. The
charter did measure a great deal (§2 is dense with real numbers) but it measured the *fleet* side
thoroughly and asserted the *load* side, and the load side was the half card S3 turned on. **A plan
that names a data source as a spine owes that source the same census it gives the fleet** — how many
respondents, covering what, summing to what. Adopted forward: before any future card recommends a
topology, the desk states the load decomposition's **coverage fraction** as a measured number or
says it is unmeasured.

**E-5 (r#3, against the charter). Four numbers the desk asserted that lanes had to correct — three
of them in §2.6, the section the desk called the program's defining problem.** The CAES unit was
carried at its **110 MW nameplate** when the source itself states a **25 MW** rating (a 77 % derate,
so card S7 was written about a unit 4.4× its real size); SEEM was dated **November 2023** when it
launched **November 2022**; SEEM was said to publish **no price** when its Independent Market Auditor
publishes a monthly price series publicly, back to 2022-11, no login; and the census headline
335/786/70,665.7 was the MA-excluded figure sitting beside a per-state list that includes it, with
neither labelled. None changed a ruling — S7 got smaller, S2 got *corroborated* by SEEM's own FAQ
routing price to FERC reporting — but all four were checkable at charter, and the SEEM ones sat in
the paragraph the whole program is organised around. **The desk's own §2 discipline ("no number here
is recalled or inferred") was applied unevenly**: it held for the fleet and the 930 extract and
lapsed for the documents. Adopted forward: a charter's narrative sections carry the same
cite-or-say-pending rule as its tables.

**E-1 (r#2, against r#1 and against the charter). The desk carried a blocking precondition that
cannot be satisfied, and the reference workstream had already retired it.** C-2 said SOCO-21 would
be "issued only after the desk verifies nobody else is mid-edit on the matrix base file." There is
no way to verify that: the matrix base and shards are written several times a day by every ISO's
lanes, and the SPP desk lifted the identical hold at its own r#2 with the finding *"writers on the
matrix files are continuous, so the charter's rebase-immediately-before-commit line is the
protocol."* That lift is in `docs/handoffs/spp-desk-ledger-2026-09.md` §4, which handoff §0.1
instructs this desk to read — so the error is not that the precedent was unavailable, it is that
the desk wrote a precondition without asking whether anything could ever discharge it. **A hold
whose release condition can never be observed is not caution, it is an indefinite block.** Adopted
forward: every hold this desk records names the **observation that releases it**, and if that
observation cannot be made, the hold is a protocol instead.

**E-2 (r#2, against r#1). The r#1 scoreboard understated SOCO-21's block, and the understatement
pointed the wrong way.** The row read "BLOCKED on collision check" alone, while handoff §1 correctly
listed SOCO-21 as blocked on card **S1** as well. The lane's entire object — the shard filename
`SOCO.js`, `ISO_EV_KEY["SOCO"] = "O"`, the `--iso-soco` colour token — is the registry key that S1
decides, so S1 was always the binding constraint and the collision check was the softer one. Had
the desk acted on its own scoreboard it would have issued a lane whose deliverable had no name.
The handoff was right and the ledger was wrong, which inverts the documented precedence (*"the
ledger wins on live state"*) — **the ledger wins on live state, not on dependency structure, and
this desk should re-derive a block from the plan rather than copy it forward from its own last
entry.**

**E-3 (r#2, against the charter). The plan's own G13 would have produced the miso-255 incident.**
As chartered, G13 told W4 to "`.gitignore` the bundle family" — written on 2026-09-12, the same day
rule 34(a) was corrected to say the opposite for a shard, and that a charter saying so is *"a defect
in the prompt."* The charter is this desk's document; the defect was this desk's. It is repaired at
r#2, before any SOCO solve exists, which is the only reason it cost nothing. **Adopted forward: a
CLAUDE.md rule that lands after a plan is chartered is a refresh edit due at the NEXT sitting, not
whenever a lane trips over it.**

**E-7 (r#5 check-in, against this desk's own §2.3). The row that found the `_ISO_TO_BA_CODE` pin drew the wrong conclusion from the same evidence.** §2.3's `_ISO_TO_BA_CODE` row closed with *"NWPP's harder case does not apply here — its 17→1 BA map collapses to one arbitrary BA and fails **silently** at 13 `==` call sites, while SOCO is one BA and one code."* That is correct about **SOCO's data** and wrong about **the codebase**: NWPP's case applied to SOCO not as a data problem but as a **merge hazard**, because NWPP-20's repair *deleted the scalar inverse SOCO-20 was concurrently writing*. The desk had the 13-call-site silent-failure sentence in front of it at r#3, quoted it, and still read it as "not our problem" rather than "this construction is being removed from under us." It cost nothing only because the check-in caught it before the merge. **Adopted forward: when another program's lane reports a defect in a surface this program also writes, record what it CHANGED, not only whether the defect reproduces here — a repair that deletes a construction is a collision even when the bug is not.**

**E-8 (r#6, against this desk's own gate G23). The desk called the parquet step mechanical, and it was the one step that needed judgment.** G23, written at the r#5 check-in, told the rebasing lane the 8 `eia860_generators.parquet` conflicts were *"derived artifacts, not data … re-running the curation step on top of merged main regenerates both regions' rows — no re-fetch, **no judgment call**"*, and offered a **census** (plants/generators counts) as the verification. SOCO-20 did exactly that and the routine silently dropped the eGRID `heat_rate` join on four of eight tables, added a column, reordered another and admitted a foreign PJM row. **A census would not have caught any of it** — every count still matched. The suite caught it, and the lane repaired it by hand and routed the script (R-l). The desk reasoned from the script's *inputs* ("it filters on `BA_CODE_TO_ISO`, therefore it regenerates correctly") without reading its *output path*, which is the same shape of error as E-7 one sitting earlier: correct about the data, wrong about the code. **Adopted forward: a gate that prescribes running a script states the assertion that proves the script did what it claims — for a derived table that is an IDENTITY check on the untouched slice (`.equals()`), never a count.** Corrected in G23 with the lane's proven recipe. *(Also corrected here: the desk's r#5 suggestion that the NEISO Mystic `oil != gas_cc` failure might be rescope residue. It is not — SOCO-20 §6.1 measures plant 1588 as genuinely carrying an oil steam unit AND GT1, so the test over-asserts that every unit under the plant is `gas_cc`. A test-expectation defect, not a data corruption; the desk's hypothesis was offered as a lead and the lane's evidence retired it.)*

**DO-NOT-REDO (r#7, not an error — a question closed with a measurement).** NWPP's W3 carries a lane SOCO's does not: **NWPP-32, a hydro energy budget + envelope** for 288 plants. The desk checked whether SOCO's W3 is therefore short a lane, rather than assuming either way. **It is not.** SPP-30/31/32/33/34 — the template this program's W3 is issued against — has **no hydro lane either**, and the reason is proportion, not oversight: NWPP is a hydro-dominated footprint (BPA), while SOCO's hydro is **8.45 / 6.92 / 5.93 TWh against ~240 TWh of demand, i.e. ~2.5–3.5 % of energy** (plan §2.1). SOCO's genuinely awkward water asset is the **1,306.6 MW of pumped storage**, and that is already routed as **R-i** — unobservable in EIA-930 for 2023 and most of 2024, a stated constraint on the C1 `fuelmix` benchmark for SOCO-31, not a missing derive lane. **The W3 issuance stands as five lanes against SPP's template. Do not re-open this by analogy to NWPP** — the lane counts differ because the footprints do, and the numbering is offset besides (NWPP-33 ≈ SOCO-32, NWPP-34 ≈ SOCO-33, NWPP-35 ≈ SOCO-34), so a charter copied from NWPP by lane number would be the wrong charter.
