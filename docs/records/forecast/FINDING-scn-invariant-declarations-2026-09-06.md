# FINDING — SCN invariant declarations: the ledger landed elsewhere, and the 4fab3f0a forensic answer

**Lane** SCN-INVARIANT-DECLARATIONS (Scenario Desk) · **Model** Opus (`claude-opus-5`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-invariant-declarations-hacutm` ·
**Pin at open** `d1aa877f` · **Pin at write** `ea99a008` ·
**Scope** records + forensics only. **No solve, no score, no re-score, no registration.**
No invariant definition, threshold, exemption or `curated_subsets` entry was touched; no
verdict, board, keeper shard, marker, freeze, matrix shard, `program-status.json`,
`CLAUDE.md` or workflow was written.

---

## 0. Bottom line

1. **The 22 declarations were already landed, 25 minutes before this lane could push them.**
   Lane **SCN-FIX1** (Scenario Readiness Desk r#10 item 1) merged them at `06bdcc2e`
   (PR #5127, 07:28:23Z). This lane had derived the same edit independently and it is
   **byte-identical** — same 22 run ids, same 34 (run, ident) pairs, same 16 baseline prunes,
   same 8 survivors. That is reported as a **cross-check, not as duplicated work**: two
   readings of the same committed sidecars, taken from the checker rather than from the
   routing prose, agree exactly. This lane therefore **did not re-land the ledger edit** (§1).
2. **The forensic question is answered, and there is NO second writer of the forecast
   namespace** (§2). `register_forecast_run.py --summary` wrote both CAISO sidecars, on its
   canonical path. The gate did not refuse them because **it was not in the tree the command
   ran against**: `provenance.scored_at_sha` is `27dcb35a2d43`, a commit that is
   **unreachable at `main`** — the pre-rebase HEAD that the 05:57:20Z rebase rewrote into
   `aafbdb76`. The Y-24 ratchet is a **working-tree** gate, so a lane that registers on a
   pre-`8ca9ad2f` base and *then* rebases forward lands a sidecar in a gated tree that never
   met the gate. Command line, and the byte-level reproduction that pins the writer, in §2.
3. **Y-24 §4.1's magnitude question is settled on committed artifacts, and the answer is both
   limbs** (§3): the *mechanism* is unchanged FR-6 (backstop measured 0.0 in every year of
   every ERCOT arm) and the *membership* is unchanged ({I3, I12}); what moved is the
   **premise** — an owner-ruled load re-derivation, 7.9 %/yr → 13.48 %/yr — which is a levels
   question already routed to the owner and **not closed by declaring the FAIL**.
4. **One declared row's cause is named by no finding, and it is named here** (§4):
   `ercot-2026-2030-scn-ws4-probe-t1f-load-hi`'s I7 is the **energy-only retirement-bounded**
   limb, not the accredited-firm limb every other declared I7 is. Re-derived at zero LP cost:
   a **123.2 MW** net thermal decrease in the single year 2027, from a 244.4 MW retirement the
   REF arm does not make.
5. **The rebase directive is satisfied for every branch this lane can see** (§5): exactly one
   live `scn-` branch exists at `origin`, and it is already past `8ca9ad2f`.

---

## 1. The declarations — landed by SCN-FIX1, reproduced here as a cross-check

Y-24 routed 16 scenario-desk runs (`FINDING-y24-invariant-declaration-ratchet-2026-09-06.md`
§4.1). The charter prompt for this lane counted **22**, because six more had registered since
Y-24 snapshotted. Running the checker at this lane's pin rather than reading either list:

| campaign | runs | pairs | in Y-24's baseline |
|---|---|---|---|
| `scn-ws1-probe` | 8 | 12 | 4 (the ercot + pjm pairs) |
| `scn-campaign-load-2026-09-06` | 5 | 11 | 3 (the ercot legs) |
| `scn-ws4-probe` | 9 | 11 | 9 |
| **total** | **22** | **34** | **16** |

The six with no baseline line (`{caiso,miso}-2026-2027-scn-ws1-probe-{carb,ref}` and the two
`pjm-2026-2030-scn-campaign-load-*` legs) registered **after** the baseline was taken — i.e.
they are inflow the ratchet was built to stop, and §2 is why it did not.

**Landed at `06bdcc2e` by SCN-FIX1, not here.** This lane built its own edit from the checker
output before fetching, then compared:

```
declared_failures            mine 43  theirs 43  IDENTICAL
registration_ratchet_baseline mine  8  theirs  8  IDENTICAL
```

Two lanes, two independent derivations, the same 34 pairs and the same 8 survivors
(capx 4 + forecast-orchestrator 4). The edit is not re-landed: a second commit writing the
same bytes buys nothing and would collide with `scnfix1_note`. What this lane adds instead is
§§2–4, none of which is in that note.

**Audit state at `ea99a008`:** 30 undeclared runs → **8**, exactly the two other desks' rows.
No stale-baseline problem is reported, so the prune is complete.
`pytest tests/scoring/test_invariant_declaration_ratchet.py` → 22 passed.

---

## 2. THE FORENSIC ANSWER — how the two CAISO sidecars in `4fab3f0a` were produced

**The question.** `4fab3f0a` ("SCN-WS1b-r2: CAISO pair, and the FINDING complete at 12/12
arms") adds `frontend/data/hindcast/caiso-2026-2027-scn-ws1-probe-{carb,ref}.json`. That
commit's tree carries `register_forecast_run.enforce_invariant_declaration_gate`, and the gate
refuses both sidecars today. So how were they written?

### 2.1 The answer

**`scripts/register_forecast_run.py --summary` wrote them, on its canonical path, at a tree
that did not carry the gate.** There is no second writer. The reconstructed command line, one
invocation per arm:

```
python scripts/register_forecast_run.py \
  --summary results/scn-ws1-probe/caiso/REF/full_horizon_summary.json \
  --kind scenario --label scn-ws1-probe-ref \
  --extra-meta '{"campaign": "scn-ws1-probe", "case": "REF", "reference_case": "REF"}'

python scripts/register_forecast_run.py \
  --summary results/scn-ws1-probe/caiso/CARB/full_horizon_summary.json \
  --kind scenario --label scn-ws1-probe-carb \
  --extra-meta '{"campaign": "scn-ws1-probe", "case": "CARB-MID", "reference_case": "REF"}'
```

REF ran first (`registered_utc` 05:53:41Z), CARB one second later (05:53:42Z).

**This command line is RECONSTRUCTED from the artifacts, not recovered from a shell history**
— no session transcript is in the repo — and it is verified by reproduction, not asserted.
Replaying `register_forecast_baseline.build_sidecar` with exactly these arguments at
`ea99a008` reproduces each committed sidecar **byte-identically except for the one field that
cannot match**, `meta.started_utc` (a wall-clock stamp):

```
caiso-2026-2027-scn-ws1-probe-ref : rebuild == committed (minus stamp)?  True
caiso-2026-2027-scn-ws1-probe-carb: rebuild == committed (minus stamp)?  True
   (the sole meta difference, both arms: started_utc 2026-09-06T07:26:20Z vs 05:53:41Z)
```

That the full 14-row `invariants` block also reproduces exactly is the strongest part of the
identification: the invariant block is computed inside `build_sidecar` from the summary, so a
hand-written or copied sidecar would not carry a block that recomputes to itself.

### 2.2 Why `--summary`, and why `register_forecast_run` rather than the two legacy writers

Three artifact facts pin the entry point without needing the history at all:

1. **`meta.variant == "forecast-baseline"`.** Only the `--summary` branch delegates to
   `register_forecast_baseline.build_sidecar`; the `--bundle` branch delegates to
   `register_hindcast.build_sidecar`, which stamps a different variant.
2. **The sidecars carry a `provenance` block** (`forecast-provenance/v1`). `build_sidecar`
   does **not** produce one — verified directly: its output keys are
   `['invariants', 'meta', 'registered_utc', 'run_id', 'score']`. The block is added by
   `register_forecast_run._stamp_sidecar`, which is called **only** in that module's
   `main()` `--bundle` / `--summary` branches. So the write did **not** go through
   `register_forecast_baseline.py`'s own `main()`, which never stamps.
3. `register_hindcast.py` is excluded by (1) and by having no `--summary` path at all.

**Conclusion for the director: there is no second writer of the forecast namespace.** The
single registration path wrote these files. Nothing needs naming, and nothing needs fixing.

### 2.3 Why the gate did not refuse them — the real defect, which is a *timing* seam

`provenance.scored_at_sha` records `git rev-parse HEAD` at registration
(`scripts/lib/forecast_provenance.head_sha`). The two CAISO sidecars carry:

```
scored_at_sha = 27dcb35a2d43        # $ git cat-file -t 27dcb35a2d43
                                    # fatal: Not a valid object name
```

**That commit is unreachable at `main`.** It is the WS-1b-r2 branch's pre-rebase HEAD — the
05:33:36Z doc commit that the rebase at 05:57:20Z rewrote into `aafbdb76` (both `aafbdb76`
and `4fab3f0a` carry committer date 05:57:20Z against author dates 05:33:36Z and 05:54:32Z,
the rebase signature). The reconstructed timeline:

| time (UTC) | event | gate in the working tree? |
|---|---|---|
| 04:42:49 | `8ca9ad2f` merges the Y-24 ratchet to `main` | — |
| 05:24:45 | `9baeba1a` registers the MISO pair on the WS-1b branch | **no** (`8ca9ad2f` not an ancestor; 0 gate refs in tree) |
| 05:28:53 | PR #5096 merges `9baeba1a` to `main` | — |
| 05:33:36 | `27dcb35a2d43` authored — branch still on its pre-`8ca9ad2f` base | **no** |
| **05:53:41–42** | **both CAISO sidecars written, HEAD = `27dcb35a2d43`** | **no — so the gate was never reached** |
| 05:54:32 | the sidecar commit authored | — |
| 05:57:20 | `git fetch` + rebase onto `2eb65038` (contains `8ca9ad2f`) | **yes, from here on** |

The same holds for every other post-baseline registration measured: `9baeba1a` (the MISO
`scn-ws1-probe` pair) and `6f18377f` (the two PJM `scn-campaign-load` legs) both have
`8ca9ad2f` **not** an ancestor and zero gate references in their trees.

**So the ratchet did not fail; it was bypassed by ordinary branch hygiene.** It is enforced
against the **working tree at registration time**, and a lane that solves on a base predating
the gate and rebases forward afterwards lands a gated-tree sidecar that never met the gate.
Verified in the other direction too — the gate does refuse the same command today, and leaves
nothing behind (`git status --porcelain` empty after the refusal):

```
error: REGISTRATION REFUSED (forecast-invariant declaration ratchet, lane Y-24 ...)
  caiso-2026-2027-scn-ws1-probe-ref: invariant FAIL(s) ['I7'] are not declared ...
```

**This is a finding about the seam, not a repair, and this lane deliberately does not repair
it** — `register_forecast_run.py` is not this lane's file and a merge-time check is a CI
question, not a records one. **Routed to the director** with the mitigation the charter
already names as the operational answer: **rebase every live lane branch past `8ca9ad2f`
before its next registration** (§5). A durable fix, if the director wants one, is a
merge-time re-ask at the CI seam — the same shape as the R-AZ registration-time re-ask the
backcast marker gate got when Z-6 showed a launch-time check could outlive its authorization.

---

## 3. Y-24 §4.1's magnitude question, settled

Y-24 declined to adjudicate and said the desk must settle it first: *"Whether FR-6 **at this
magnitude** is the same finding, or a load-scenario premise that has outrun the fleet the run
is allowed to build, is the desk's call … It should be settled before these are declared."*
The three `ercot-2026-2030-scn-campaign-load-*` legs and `-ws4-probe-t1f-load-hi` were its
named rows (8,760 h of slack, 37–53 % of load, reserve margin −43 % to −49 %).

**Settled on committed artifacts, no solve. The answer is BOTH LIMBS, and they are not
alternatives.**

| what Y-24 asked | evidence | verdict |
|---|---|---|
| Is the **mechanism** still FR-6? | `backstop_built_mw` = **0.0 in every year of every arm** (WS5A-ERCOT §3(a), scored HIT) — the energy-only backstop is off by market design and the residual leaves through the VOLL slack column, exactly as `dominant_open_causes.I3` describes | **YES, unchanged** |
| Is the **FAIL set** still the same? | WS5A-ERCOT §6 gate **S5**: FAIL set `{I3, I12}` in all three arms, *"unchanged from the board's bare key"*; §7 corrects the lane's own earlier in-session `{I3, I12, I13, I14}` claim — *"I13 and I14 are WARN, not FAIL … what changed is severity, not membership"* | **YES, unchanged** |
| Has the **premise** outrun the fleet? | WS5A-ERCOT §8.1: SCN-LOAD re-derived ERCOT REF growth **7.9 %/yr → 13.48 %/yr** (owner-ruled intake S4/D-4). The **shipped REF** — `demand_growth_path=mid`, `datacenter_load_path=mid`, `set_overrides={}` — now fails I12 from **2026** and sheds **127.2 TWh** (14.7 % of 2030 load) at $4,438/MWh with `hours_ge_500` 7,962 of 8,760, *before any load case is applied* | **YES — and it is an input change, not an arm artefact** |

So the 8,760-hour numbers are **the same unowned mechanism biting a much larger premise**.
Two further facts make that reading falsifiable rather than convenient:

* **SCN-WS4b pre-registered this magnitude class before the solve** (§5.1 ERCOT row: *"I3 in
  the hundreds of TWh, `hours_ge_500` ≈ 8,760, I12 FAIL"*). WS5A scores it a **SPLIT**, not a
  HIT, because the number landed while the *tail-regime* mechanism they attributed it to is
  **absent** (WS5A-ERCOT §0.2/§3) — right number, wrong cause, reported as such.
* **The premise question is NOT closed by declaring the FAIL, and this desk cannot close it.**
  WS5A-ERCOT §8.2 routes *"whether a reference case in permanent shortage is the intended
  posture"* as a **levels** question (D-2) for the owner: flagged, not repaired. The
  declaration records the FAIL; it does not answer that.

**Reading limits that bind any quotation of these runs**, stated with the declaration rather
than left to be discovered: ERCOT levels are **not quotable at any year** and its deltas only
at **2026–2027**, because from 2028 both arms price at the VOLL ceiling (~$4,990–5,000), so
ΔCO2 there measures fleet saturation, not an emissions response (WS5A-ERCOT §7).

---

## 4. The one declared row no finding's prose covers — and its attribution

`ercot-2026-2030-scn-ws4-probe-t1f-load-hi` declares **I7**, and it is **not** the
accredited-firm shortfall every other declared I7 is. ERCOT is energy-only, so
`check_forecast_invariants` I7 takes its other branch — a **retirement-bounded** floor,
`thermal_after ≥ min(floor, thermal_before)` — which exists to catch *over-retirement*, and
deliberately tolerates a fleet that **started** below the floor. WS-4c §3.2 scores ERCOT's
(b) clause on I12 and I3 and does not itemise this row; SCN-FIX1's `scnfix1_note` §(c) covers
I7 generically. Neither names it. Re-derived here from the committed
`full_horizon_summary.json`, **zero LP**:

| ERCOT T1-F, 2027 | REF | LOAD-HI |
|---|---|---|
| thermal 2026 (= `thermal_before`) | 78,333.6 | 78,333.6 MW |
| thermal 2027 (= `thermal_after`) | 78,454.8 | **78,210.4 MW** |
| net change | **+121.2** | **−123.2 MW** |
| `retire_mw` | **0.0** | **244.4 MW** |
| floor `(peak − firm_clean) × 1.15` | 113,202.5 | 98,522.2 MW |
| bound `min(floor, thermal_before)` | — | **78,333.6 MW** ← binds on `thermal_before` |

**Three things this pins.** (a) The bound binds on `thermal_before`, **not** on the floor —
the fleet is 20.2 GW below the floor and has been since 2026, which this limb *tolerates*, so
the FAIL is **not** an adequacy statement. (b) It is purely a **net thermal decrease of
123.2 MW (0.157 %) in one year**, against a 1.0 MW checker slack. (c) The arithmetic closes
exactly: **+121.2 MW of lagged commissioning is common to both arms** (it is REF's whole
change, at `retire_mw` 0), and LOAD-HI additionally retires **244.4 MW**;
121.2 − 244.4 = −123.2, to the decimal.

**Why the high-load arm retires MORE is OPEN, and is stated as a reading, not a chain.** The
reading consistent with WS-4c §3.2's relocate-regime artefact and its §5 MISS 2 (*"adequacy in
ERCOT 2026 is a peak problem, not a floor problem"*) is that the flat DC block **cuts the 2026
peak the step-3 screen reads by 9.1 GW** (84,601.5 vs 93,673.3 MW), thinning the attainable
scarcity margin of the marginal peaking tranche even though LOAD-HI's 2026 load-weighted price
is *higher* ($36.23 vs $34.59) — a tail effect, not a mean effect, which is exactly what
`Σ_t max(0, price − cost, reserve price)` screens on. **The per-unit retirement ledger is not
in the committed bundle**, so the unit-level "which units, and why" cannot be closed without a
replay and is left open rather than asserted.

---

## 5. The rebase directive

*"Rebase every live scenario branch past `8ca9ad2f` before the next registration."* Measured
at `ea99a008` over every remote branch whose name carries `scn` or `scenario`:

| remote branch | past `8ca9ad2f`? | ahead of main |
|---|---|---|
| `origin/claude/scenario-readiness-refresh-9-d0pha6` | **PAST** | 3 |

**That is the whole list** — after `git fetch --prune`, exactly one live remote branch carries
`scn` or `scenario` in its name, and it is already past the gate. Every other `scn-` lane
branch has been merged and deleted, so **nothing needs rebasing**. This lane's own branch is
fast-forwarded onto `origin/main` (`ea99a008`), i.e. past `8ca9ad2f`, before this doc was
written. Two standing notes
for the desk, since §2.3 shows the failure mode is a *timing* seam rather than a per-branch
one: a branch that is past `8ca9ad2f` **today** can still register ungated tomorrow if it was
based before the gate and has not fetched since — so the operative rule is **fetch and rebase
immediately before each registration**, not once per branch; and a branch that registers and
*then* rebases forward reproduces `4fab3f0a` exactly.

---

## 6. Duties

- **Rule 15 `[R-DASHBOARD]` / forecast plan §7.5:** no run registered, no sidecar written, no
  namespace regenerated. The backcast registry was not touched.
- **Rule 22 `[R-HOLDOUT]`:** no marker, freeze or holdout surface read or written.
- **Rule 24 `[R-REGISTRY]` / 28 `[R-MECH-MATRIX]`:** no `ScenarioConfig` field, no solve-
  affecting mechanism, no CLI flag — no matrix row or shard is owed.
- **Rule 27 `[R-PUSH]`:** no existing ≥300-line source file rewritten; the ledger edit this
  lane built was **discarded unpushed** once SCN-FIX1's identical edit was found on `main`.
- **DOF ledger: zero** free parameters. No `authorized_price_tuning` (a backcast channel;
  untouched). Backcast byte-identity: untouched — nothing under `src/` was read for effect.

## 7. Open after this lane

1. **The registration-timing seam** (§2.3) — routed to the director, unrepaired by choice.
2. **The premise question** (§3) — WS5A-ERCOT §8.2's D-2 levels question, owner's to answer.
3. **`-t1f-load-hi`'s 244.4 MW retirement, unit-level** (§4) — needs a replay; not spent.
4. **The eight non-`scn-` rows** — capx 4 and forecast-orchestrator 4, per Y-24 §§4.2–4.3.
   CI stays red on exactly those until their desks adjudicate them.
