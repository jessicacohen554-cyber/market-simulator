# RESULT — nyiso-227: C3b IS MEASURED. The NYC persistent-base re-basing CLEARS its pre-registered gate in all three years, and the span reproduces nyiso-226 to the fourth decimal

**Session:** nyiso-227 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-11
**Keeper / control:** `2026-09-09-nyiso-221-fuelvintage-span`
(`results/calibration/nyiso_fuelvintage_A`, `git_sha da2e7076`) — **UNCHANGED at this writing.**
**Chain:** `ADDENDUM-nyiso226-not-promoted-and-main-reverted-2026-09-10.md` §4 →
`PRECOMMIT-nyiso227-c3b-measurement-2026-09-11.md` → this document.
**LP spent: ONE shard, 13 m 35 s, three years, exit 0.** The parent ran no LP (rule 32(a)).

---

## 0. Headline

**The open question is answered. C3b passes in every year, with room to spare.**

| year | control | **arm** | Δ | headroom to the 0.20 ceiling |
|---|---|---|---|---|
| 2023 | 0.122103 | **0.122552** | +0.000450 | 0.077448 |
| 2024 | 0.179016 | **0.179205** | +0.000189 | **0.020795** |
| 2025 | 0.159598 | **0.159371** | **−0.000226** | 0.040629 |

Unrounded, because the band test is on the unrounded NRMSE. **The pre-registered decision rule —
*promote iff no year's arm C3b exceeds 0.20* — is CLEARED.** The tightest year, 2024, consumed
**0.9 % of its remaining headroom.** Max |ΔC3b| is **0.00045**, which is **11× inside** the
`|ΔC3b| ≤ 0.005` prediction registered in the PRECOMMIT before the solve — and 2025 moves the
*right* way, so the movement is two-sided here too.

**Recommendation: PROMOTE.** It is not actionable this session — §3.

## 1. The span independently reproduces nyiso-226, on every number that lane reported

This was solved from scratch on a fresh container at a different HEAD, against the same
committed control. Every figure below is measured here, not copied:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **C1 ST_GAS** \|miss\| ctrl → arm | 1.669 → **1.591 BETTER** | 1.369 → **1.410 WORSE** | *rubric-skipped* |
| C1 CT_PEAKER | 1.717 → 1.716 | 1.540 → 1.539 | *skipped* |
| C1 CC_REGULAR | 0.786 → 0.832 worse | 2.915 → 2.924 worse | *skipped* |
| C1 CC_CHP | 1.103 → 1.124 worse | 2.548 → 2.570 worse | *skipped* |
| C1 ST_CHP | 0.199 → 0.203 worse | 0.257 → 0.259 worse | *skipped* |
| **C3a** ctrl → arm (actual) | 33.6503 → 33.6760 (32.25) | 40.1499 → 40.1782 (38.12) | 61.5983 → 61.6235 (66.43) |
| **C8** ST_GAS forced share | 0.1611 → **0.1596** | 0.2090 → **0.2071** | 0.1813 → **0.1796** |
| D-2 `reliability_floor × ST_GAS` TWh | 1.9019 → **1.8716** | 2.2021 → **2.1733** | 2.1240 → **2.0983** |

**These match nyiso-226's RESULT §1 to the fourth decimal on every row.** D-1 `passed=True` and
D-2 `passed=True` on both sides; **D-4 `passed=False` on BOTH sides with byte-identical failure
text** (2023 plant 2480, 0.0015 TWh), i.e. pre-existing and not introduced — exactly as that lane
reported. *(2025's C1 is SKIPPED by the rubric — preliminary EIA-923 vintage — so the 2025 ST_GAS
row is not gated in either run; nyiso-226 §1.1 established this and it is restated so the large
2025 numbers are not misread as a failure.)*

**An independent confirmation the arm is exactly one coefficient:** the arm's `meta.json`
`shared_inputs` are **byte-identical content hashes** to the keeper's — `eia923-920c8b8bc1b1`,
`eia930-31afc8dc1922`, `campd-c51cde2ea05a`, and the whole unit-outage family. The store is
content-addressed, so identical hashes are proof the two solves read identical derived inputs.

## 2. How C3b was measured, and why it is not an approximation

`scripts/score_bundle_price_shape.py` (added by this session, additive, no existing file touched)
rebuilds the one payload block C3b reads — `lmp[zone] = {"pMon","dMon"}` — from a bundle's own
`hourly/system_<year>.parquet` using `render_calibration_html.py`'s arithmetic, **then calls
`calibration_verdict.score_price_shape` itself.** Band, load-weighted-actual ladder,
partial-month coverage mask and NRMSE are the scorer's, unmodified; the benchmark is the
committed `bench/NYISO/<year>.json.gz` — **the same part the registered control was scored
against.**

**It is exact.** Run against the designated keeper it returns **0.122 / 0.179 / 0.160**, identical
to that run's registered verdict. nyiso-226's hand reconstruction was ±0.002 — itself 10 % of
2024's headroom, and the reason that lane could not have concluded from it. Both sides above were
measured with this one tool, in this one container, in one command each.

**This closes the architectural gap nyiso-226 named in general terms:** a shard, or a parent
holding only a slim bundle, can now price-shape-score without registering anything.

## 3. WHAT IS BLOCKED, AND IT IS THE MECHANICS OF PROMOTION, NOT THE DECISION

**The run is NOT registered, so rule 15 `[R-DASHBOARD]` is NOT discharged and the promotion
cannot be executed this session.** Stated plainly rather than worked around.

`scripts/dashboard_add_run.py` → `render_calibration_html.build_payload` needs three bundle
artifacts. Two were recoverable here and one was not:

| artifact | status |
|---|---|
| `_shared/NYISO/{eia923,eia930,campd}` | **recovered** — `run_calibration_full.py --rebuild-benchmark` (its own log: *"no re-solve"*) rebuilt them to the **byte-identical content hashes** the solve recorded |
| `system.parquet` | **recovered** — it is the concatenation of the committed `hourly/system_<year>.parquet`; the reshape adds no information, and the proof is that `score_bundle_price_shape.py` reproduces the registered keeper's C3b from those same hourly files |
| **`dispatch/<year>_P1.parquet`** | **NOT recoverable.** Per-**plant** hourly MW (`plant_code`, `klass`, `zone`, `hour`, `mw`). Class aggregates cannot substitute, it is gitignored, it is most of the shard's **124 MB** bundle — over the pack size `git push` is licensed for — and the shard's container is gone |

**No block was routed around.** In particular: the shard was not asked to register
(rule 32 `[R-SHARD]` (c)(6) forbids it by name, and registration is the parent's under (d)), and
no scorer or payload path was patched to skip the dispatch read.

**THE FIX, now fully characterized — and it is cheap.** The shard should ALSO have committed
`hourly/unit_hourly_<year>.parquet`, which carries `plant_code / plant_group / zone / hour / mw`
— everything `build_payload` takes from `dispatch/` — and which `.gitignore`'s own comment
measures at **920 KB/yr for NYISO** while explicitly blessing the opt-in:
*"a lane that WILL interrogate a bundle commits its layer deliberately with `git add -f`… Opt-in
per bundle, not a policy flip."* **~2.8 MB for a three-year span.** Every future NYISO span-shard
prompt should carry that line. This is the third iteration of one architectural lesson
(nyiso-226: no `metrics.json`; then: the scorer resolves registered runs only; now: registration
itself needs a per-plant layer the shard must be told to keep) and it is now closed on all three
legs.

**Cost to finish (rule 31 `[R-RETAIN]`, stated before spending, and NOT spent): one ~14-minute
shard**, re-solving the same span and committing `hourly/unit_hourly_*` alongside the slim bundle
— **or** an owner waiver of rule 32(c)(6) for a single shard, which carries none of that clause's
collision risk when exactly one shard is running.

## 4. `main`, and the invariant nyiso-226 had to repair

At this writing `main` reads **0.175** and the shard branch `claude/nyiso227-span` has **not**
auto-merged. When it does, `main` will carry **0.16629202320362052** while the designated keeper
— which solved at `da2e7076`, where that cell reads `0.175` — is unchanged. **That is precisely
the silent drift the nyiso-226 addendum had to undo**, and it must not be left standing on a
recommendation alone.

**So: if the owner does not promote, `main` is reverted to `0.175`** (one line, binary-mode edit,
CRLF preserved), exactly as nyiso-226 did. **If the owner promotes, the armed value is correct on
`main` and stays** — it becomes the new keeper's recipe. Either way the invariant *"the designated
keeper reproduces from `main`"* holds. The re-apply, if promotion comes later, is the same one line.

## 5. Retention and the open question

**The shard's full 124 MB bundle is GONE** — its container is reclaimed and it was not reachable
for messaging (no cross-session channel to a cloud shard from this parent). **The 19-file slim
bundle it pushed survives on `claude/nyiso227-span`** and carries every number in this document:
`meta.json`, `run_config.json`, `legitimacy_diagnostics.json`, and the full `hourly/` set
(`class_hourly`, `class_band_hourly`, `system`, `storage`, `reserve_family`) for all three years.
**Nothing was deleted by this session.**

**THE PROMOTION QUESTION IS THE OWNER'S AND IT IS OPEN.** The arm cleared every criterion this
program can measure on it — C1 (both gated years, both sides, no flip), C3a (all three), C8
(falls every year), D-1, D-2, and now **C3b (all three, the tightest at 0.9 % of its headroom)**
— with two-sided evidence in two independent places (2024 C1 worse while 2023 better; 2025 C3b
better while 2023/2024 worse) that it is not residual-fitted. Against it, unchanged from
nyiso-226 and restated rather than dropped: it **moves a frozen coefficient with no source-data
trigger**, so rule 23 `[R-FROZEN-DERIVE]` / rule 21 `[R-DOF]` admissibility remains an **open
owner question** that nyiso-203 declined to answer alone; and **2024's C1 ST_GAS gets worse by
0.041 TWh**, a real cost.

## 6. Rules

- **Rule 1 `[R-STRUCT]`** — the value was fixed ex ante in the PRECOMMIT, never swept; the
  two-sidedness in §0 and §1 is the positive evidence. `authorized_price_tuning` = **NONE**.
- **Rule 13/14** — measured basis, forward-regenerable, no outcome pinned.
- **Rule 15 `[R-DASHBOARD]`** — **NOT discharged.** §3, stated not hidden.
- **Rule 16 `[R-ALLYEARS]`** — one invocation, one bundle, 2023–2025.
- **Rule 21 `[R-DOF]`** — the coefficient remains a ledgered free parameter; count unchanged.
- **Rule 23 `[R-FROZEN-DERIVE]`** — no source-data trigger, and none claimed. Open, §5.
- **Rule 29 `[R-SCREEN]` (b)** — G-CTRL form 4 with the G-DRIFT audit in the PRECOMMIT §3
  (all hunks INERT, `ec3374d2 → HEAD`; bench separately verified unchanged for NYISO).
  **No control solve spent.**
- **Rule 31 `[R-RETAIN]`** — nothing deleted; the completion cost is stated in §3 and not spent;
  the promotion question is asked explicitly in §5 before the session ends.
- **Rule 32 `[R-SHARD]`** — parent ran no LP; one shard, one commit, 13 m 35 s.
