# PRECOMMIT — pjm-h11: the 2020 seam-ladder gap (C-1), the quantified G-DRIFT, and the shard plan (2026-09-19)

**Session:** pjm-h11 · **Branch:** `claude/pjm-h11-calibration-tuning-mwod34` · **Base:** `origin/main` @ `995f7b7efcc5bbf332ebd91e48d7508a2f7849f4`
**Keeper UNCHANGED** at write time (`2026-09-11-pjm-d4-4-gasoutage`; bundles `pjm_d4_4_A` 2023–2025, `pjm_d4_4_TP` 2020–2022).
**Rule 32 `[R-SHARD]` (a): ZERO LP MINUTES IN THIS SESSION.** Every number below is a zero-LP
phase-0 computation — a frozen-formula re-derivation, an offer-array delta, a committed-sidecar
reconstruction, and a code-level drift audit. No solve was run here and none will be.

**Target:** C1 on the holdout span. `pjm_d4_4_TP` (2020–2022) is NOT-YET with **C1, C3a, C3b FAIL**
and C3c a ledgered CAVEAT. **C2 PASSES** (`metrics.json: sysvol: PASS`) — the older charter text
saying "C1/C2/C3a-b FAIL" is wrong and was corrected at pjm-h10 §6(b). The training keeper
`pjm_d4_4_A` is CALIBRATED 8/8 with zero caveats and is **not** the target.

---

## 1. Honest statement about the order of work

The charter requires every gate to be **declared ex ante, before any solve**. That is satisfied:
**no solve has been run and none is authorized by this document alone.**

What did happen before this document was written is the **zero-LP phase 0** — rule 29 `[R-SCREEN]`
clause (0) survives as practice, and it is what a lane is supposed to do first. So the gate
*outcomes* for C-1 are already measured and are reported here alongside their declarations rather
than being written as predictions I have already seen. I state this plainly instead of
back-dating: the gates below bind the **solve**, and they were fixed in form before the
derivation was parsed, but this document is not pretending the numbers are unseen.

The one thing that genuinely must be unseen is the **arm's scored result**, and it is: no LP has
run at either SHA.

---

## 2. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — re-audited to HEAD, and QUANTIFIED

pjm-h10 found form 4 FALSIFIED by four LIVE hunks but never produced a scored number, so the
quantification was still owed. It is delivered here, at zero LP.

`git fetch origin f09eddbe…` **resolves** (pjm-167's "unrecoverable" was the previous keeper).
Audit span: keeper `f09eddbefe6a3e72ba3ccc2f9d4d97db0b17205d` → HEAD `995f7b7efcc5bbf332ebd91e48d7508a2f7849f4`.

### 2.1 The increment since pjm-h10's audit base adds NO new LIVE hunk

pjm-h10 audited to `4583e70b`. The increment `4583e70b → 995f7b7e` over the rule-29(b) path is
**10 files, +720/−19**, and it is one PR pair:

| change | classification | reason |
|---|---|---|
| `measured_coal_heat_rates` (NWPP-42) | **INERT** | `ScenarioConfig` field, **default `False`**, **absent from both PJM keeper recipes** (verified in `run_config.json`); per-ISO artifact, strict no-op for an ISO with none |
| `mid_vintage_exit_carry` (SPP-48) | **INERT** | default `False`, armed for **SPP alone** via `_spp_config`; every `outages.py` entry point early-returns on `if not mid_vintage_exit_carry`; the one unconditional line is `runner.py`'s `year=… if (_rvs or _ppx or _mvx)`, unchanged at `_mvx=False` |

Both are the rule-29(b) INERT class verbatim: *"a `ScenarioConfig` flag that is default-off AND
absent from the keeper's recipe."*

Also re-checked over the full `f09eddbe → HEAD` span, because they are the PJM-adjacent surfaces:

| file | classification | reason |
|---|---|---|
| `model/interchange/spec.py` (+377/−0) | **INERT** | purely additive; the new registries are `NWPP`/`SOCO`, and the two new `"PJM": {` blocks sit inside **`MISO_SEAM_LADDER_BY_YEAR`** — MISO's registry, read by a MISO solve. Another ISO's branch. |
| `data/eia930/envelopes.py` (+301/−3) | **INERT** | the three removals are an import line and two docstring lines; the additions are `nwpp_net_interchange`, `soco_net_interchange`, `_nwpp_grid_external_legs` and a new generic `measured_boundary_transfer_envelope`. No PJM function body moved. |
| `data/neighbor_price.py` (+5/−0) | **INERT** | additive |

### 2.2 THE LIVE HUNKS, and the one that matters, QUANTIFIED

All four of pjm-h10's LIVE hunks are still present at HEAD. Two are now quantified:

**LIVE-1 — the rebuilt `pjm_offer_midcurve_condbinned.json`. This is the big one, and it is
NOT what its headline suggested.** The keeper's table carried delivery years **2023–2025**; HEAD's
carries **2020–2025**. So at HEAD the TP span draws its **own** year tables instead of the pooled
fallback — the change the pjm-h10 shard confirmed in the log (`year table 2020`) before it was
killed.

The keeper's recipe is `pjm_offer_midcurve_conditional = True` with
**`pjm_offer_midcurve_segments = ['LONG_RUN', 'CC_LIKE']`** and `pjm_offer_midcurve_path = None`
(→ the default file). **`CT_FAST` is therefore out of scope**, which matters: unscoped, CT_FAST
moves by −50%, and quoting that would have been wrong. Scoped to what the keeper actually reads
(implied heat-rate multiplier; 4 conditioning bins × 12 capacity shares = 48 points per cell):

| | vs what the keeper USED | mean | median | range | points moved |
|---|---|---|---|---|---|
| **LONG_RUN 2020** | keeper's pooled fallback | **−0.298 (−3.2 %)** | −0.350 | [−1.150, +0.550] | 46/48 |
| **LONG_RUN 2021** | keeper's pooled fallback | **−1.993 (−23.9 %)** | −2.175 | [−2.750, −0.950] | 48/48 |
| **LONG_RUN 2022** | keeper's pooled fallback | **−0.164 (−2.6 %)** | −0.200 | [−1.550, +1.050] | 46/48 |
| **CC_LIKE 2020** | keeper's pooled fallback | **−1.319 (−11.0 %)** | −0.250 | [−8.550, +0.150] | 44/48 |
| **CC_LIKE 2021** | keeper's pooled fallback | **−1.055 (−7.6 %)** | −0.175 | [−7.800, +0.400] | 44/48 |
| **CC_LIKE 2022** | keeper's pooled fallback | **+0.388 (+11.9 %)** | +0.900 | [−3.650, +1.450] | 48/48 |
| LONG_RUN 2023 / 2024 / 2025 | keeper's own-year table | +0.000 / +0.002 / +0.000 | 0 | ≤ ±0.100 | 10 / 14 / **0** |
| CC_LIKE 2023 / 2024 / 2025 | keeper's own-year table | −0.001 / +0.012 / +0.000 | 0 | ≤ ±0.150 | 5 / 27 / **0** |

**Read it in two halves, because they are opposite:**

* **The TRAINING keeper `pjm_d4_4_A` (2023–2025) is essentially untouched** — mean drift ≤ +0.2 %
  on a multiplier of 7–12, 2025 byte-identical. Its CALIBRATED 8/8 is not in question from this hunk.
* **The TOUCHPOINT `pjm_d4_4_TP` (2020–2022) is materially changed**, every rung of 2021 included.
  And the **direction is against the card's target**: the 2020/2021 offer multipliers move
  **DOWN** (−11.0 %, −7.6 % CC_LIKE; −3.2 %, −23.9 % LONG_RUN), making those units **cheaper**, so
  they dispatch **MORE** — in exactly the years C1 already fails with CC_REGULAR **+7.5 / +26.2 TWh
  OVER**. HEAD's offer rebuild is expected to push C1-2020/2021 **further over**, not closer.

That is the operative consequence for this lane: **a HEAD arm and the committed keeper differ by
this hunk as well as by the arm, so an arm result cannot be attributed without a control at HEAD.**
G-DRIFT form 4 is FALSIFIED, a control replay is EARNED, and it is now earned with a number.

**LIVE-2 — the PS→OTHER taxonomy repair** (`config/plant_taxonomy.py`): `if pm == "PS": return
"OTHER"`, tested before hydro. Unconditional, every ISO. Confirmed LIVE; magnitude is the §4.3
accounting seam, not a dispatch change.

**LIVE-3 — the SOCO-15 card-S12 COD grain** (`data/cod_ramp.py`, +274/−31). Confirmed present;
not separately quantified here.

**LIVE-4 — the MER dual, and it is a STRUCTURAL OBSTACLE, not just a hunk.**
`model/lp/model.py::_marginal_emission_rate` is **new at HEAD, UNGATED and UNCONDITIONAL** — there
is no `ScenarioConfig` field for it anywhere, and `solve()` calls it on **every pass of every solve
of every ISO** (`model.py:1522`). It re-installs the CO2 rate vector as the objective in hour
chunks, calls `h.setBasis(saved)`, sets `simplex_iteration_limit = 0` and calls **`h.run()` a
second time** inside the post-solve window.

That window is **exactly where the pjm-h10 shard was OOM-killed** (2020 P0 completed and printed
`Solve 574.607 s`; the kill landed in the P0→P1 seam at anon-rss 13.30 GiB against a 13.36 GiB
cgroup). The code already carries a memory mitigation citing miso-253, so the cost was anticipated.
**I am NOT claiming the dual caused that OOM** — pjm-h10 is right that the attribution is
confounded and I have no evidence that separates it from PJM per-plant simply not fitting 13.36 GiB.
What I *can* now state as fact, which pjm-h10 could only infer: **the dual cannot be turned off from
a config, so no shard can avoid it without the code edit its prompt forbids.** That is a design
question for the owner (§6, Q3), and it is the reason a PJM replay at HEAD has a floor on its
memory need that the keeper's own solve did not have.

---

## 3. C-1 — the 2020 seam-ladder gap. GATES DECLARED.

### 3.1 What it is

`PJM_SEAM_LADDER_BY_YEAR` covers **{2019, 2021, 2022, 2023, 2024, 2025}** — 2020 is **absent** —
and `firm_export_floor_by_year` covers only 2023–2025 and is *displaced* by the ladder on the years
it covers, so it is inert in every keeper year. **PJM's keeper year 2020 therefore runs neither
measured seam mechanism and falls through to the FORECAST gas-elastic track.**

A **stale invariant**, not a second oversight: pjm-173 verified "covers every year PJM solves" when
the keeper span was 2023–2025 and the touchpoint reached back only to 2021. 2020 entered PJM's
solved span later, with `pjm_d4_4_TP`, and nothing re-checked the claim.

Both 2020 inputs are on disk (`PJM_2020_import_export_act_sch_interchange.csv`, 23.1 MB;
`actual_lmp_hourly_PJM.parquet` carries 2018–2025), so this is a **rule 23 `[R-FROZEN-DERIVE]`
re-derivation with ZERO new parameters**, not a new mechanism.

CLI (confirmed by reading the script, as the charter asked):
`python scripts/data/derive_pjm_seam_ladders.py --years 2019 2020 2021 2022 2023 2024 2025`

### 3.2 THE GATES

**G1 — the 2019 / 2021–2025 entries return BYTE-IDENTICAL. A single moved rung on an existing year = STOP.**

> **MEASURED: G1 as literally written FAILS — 3 of 480 rungs — and the failure is PRE-EXISTING
> and has NOTHING to do with 2020. I am not rewriting the gate. I am reporting it failed as
> written and putting the disposition to the owner.**
>
> 477 of 480 rungs reproduce exactly. The three that do not:
>
> | year | seam.side | band | committed | re-derived | Δ |
> |---|---|---|---|---|---|
> | 2023 | Carolinas.import | 2 | 24.10 | 24.11 | +0.01 |
> | 2024 | Carolinas.export | 2 | 13.75 | 13.76 | +0.01 |
> | 2025 | LGEE.import | 3 | 40.64 | 40.65 | +0.01 |
>
> **Cause, established rather than assumed.** The unrounded values are
> `24.10926126976536`, `13.75916674365736`, `40.64722575096235` — each **0.07 to 0.28 cents from
> any rounding boundary**, so this is not a `.xx5` tie, not banker's rounding and not a float ULP.
> The script's own `round(p, 2)` yields `.11 / .76 / .65`; the registry holds `.10 / .75 / .64`.
> All three are **truncations**, all in the same direction. The script's docstring says the output
> is *"hand-rounded … into `interchange_config`"* — these are three hand-transcription
> truncations made when the rows were written.
>
> **It is not a data revision.** A revised source moves many rungs in both directions; this moves
> three, all by exactly +0.01, all downward-truncated.
>
> **DECISIVE, and this is what the gate was actually for:** I re-ran the derivation with the
> **original `--years 2023 2024 2025` default set**, i.e. with no 2020 anywhere in the frame, and
> **the same three cents move**. Then I compared the with-2020 and without-2020 derivations
> rung-for-rung on their shared years: **240 rungs compared, 0 moved.**
>
> So: **G1-as-written = FAIL (3/480, pre-existing). G1's INTENT — "adding 2020 must not silently
> re-tune an existing year" — = PASS, at 0 of 240 rungs.**
>
> **What I propose, and it keeps the gate's teeth:** the arm adds the **2020 key only** and
> touches **no existing year's rungs**, which is provably a zero-move change on 2019/2021–2025.
> The three truncated rungs are **left exactly as committed** and are **not** fixed in this card —
> fixing them would move three rungs inside the keeper's own scored years, bundling an unrelated
> change into the arm, and rule 23 says a re-derivation commit must cite a **data** change, of
> which there is none. They are recorded in §6 (Q1) as a separate finding for the owner.

**G2 — the 2020 entry's export rungs are monotone descending, like every other year's.**

> **MEASURED: PASS.** All five seams, export monotone descending and import monotone ascending.
> One no-wash clamp fired (`MISO export band 1: $66.94 → $66.93`), the same same-seam
> reconciliation every other year carries.

**G3 — no new `ScenarioConfig` field, no new scalar anywhere.**

> **MEASURED: PASS by construction.** The change is one key added to an existing frozen-formula
> data registry. No field, no flag, no scalar, no CLI argument. Rule 21 `[R-DOF]`: zero free
> parameters — every number is a quantile of a measured series at a structurally fixed depth grid.

**G4 — DECLARED HERE (not in the charter): the 2020 entry must meet pjm-160's own published
acceptance bar**, which is the bar the 2019/2021/2022 rows were admitted under — *"every seam's
measured volume within ±0.02 TWh, duration RMSE 40–280 MW, import-hour shares within a few points."*
I add it because a re-derivation that met G1–G3 but reproduced its own year badly would be a bad
row that passed every gate.

> **MEASURED: PASS.** Offline P9, 2020: MISO −38.00 vs −38.04 actual · NYISO −10.13 vs −10.14 ·
> Carolinas −0.47 vs −0.47 · TVA +6.24 vs +6.25 · LGEE +0.77 vs +0.76 TWh. **Worst volume error
> 0.04 TWh**; duration RMSE **40–276 MW**; import-hour shares within 2–11 points. Same quality as
> 2023–2025.

### 3.3 THE EX-ANTE PREDICTION — and it confirms the charter's against-interest warning

The charter states, and rule 1 `[R-STRUCT]` requires it be stated: *this will probably make 2020's
export residual WORSE.* **I have now quantified that before any solve, at zero LP.**

Method: evaluate the ladder's export rungs against the model's own border-zone P1 price from the
**committed** `pjm_d4_4_TP/hourly/system_2020.parquet`, the construction of FINDING pjm-h10 §2.4.
Method validated first by reproducing that table's published `@measured DA` column — **all five
years reproduce exactly** (2021 47.402 · 2022 44.666 · 2023 54.622 · 2024 48.454 · 2025 48.067).
My `@model` column lands within 0.02–0.27 TWh of §2.4's (a border-zone averaging convention
difference), which I report rather than tune.

| TWh, 2020 | value |
|---|---|
| measured tie-file net export | **41.626** |
| model net export **today** (forecast gas-elastic track) | **38.810** (shortfall **−2.816**) |
| **the new 2020 ladder's GROSS export admitted at the model's own price** | **37.340** |
| the same ladder at measured DA | 50.782 |

**Net export can never exceed gross export.** The ladder's own ceiling at the model's own 2020
price is **37.340 TWh — BELOW the 38.810 TWh the unmechanised forecast track currently delivers.**
So arming C-1 should pull 2020's net export **down, away from the 41.626 measured**, worsening
2020's export shortfall from −2.816 toward roughly −4 TWh or worse.

**PREDICTION, DECLARED EX ANTE: the 2020 export residual WORSENS. C-1 is not expected to improve
any gate, and I am not proposing it because of the residual.**

The case is rules 14 `[R-ACCURATE]` and 23: **a keeper year must run the keeper's own mechanism.**
2020 has the smallest export shortfall of any PJM year precisely *because* it is the one year not
running the measured seam — which is rule 14's discovered bug in as many words: the estimate was
silently compensating for something else. Rule 1 `[R-STRUCT]`: **if the residual worsens the
mechanism stays in and the real root cause gets fixed. It is not reverted because a gate moved.**

And the ladder points straight at that root cause. 2020's `@model` → `@measured DA` gap is
**13.441 TWh, by far the largest of any year** (next is 2021 at 7.82). The ladder is telling us
2020's *internal price* is badly depressed relative to the measured DA the seam actually clears
against — which is the same defect as 2020's CC_REGULAR **+7.5** and COAL_BIT **+16.9 TWh**
over-run. Arming the ladder converts a hidden price error into a visible volume error. That is the
point.

---

## 4. C-2 — the gross/net seam split. NOT DOABLE IN THE PARENT; it rides the shards.

The split (FINDING §2.5) is currently an **inference**: gross-export short 9.458/6.278/4.706/
4.434/3.888 TWh against implied import-side excess 4.083/2.830/4.398/6.114/4.658 (2021–2025),
export-dominated in 2021/2022 and import-dominated by 2024. Measuring it needs per-link flow, dual
and limit from `hourly/network_<year>.parquet`.

**Verified against the committed bundles: `network_<year>.parquet` is NOT in either keeper's
`hourly/` sidecar set** (both carry only `class_band_hourly`, `class_hourly`, `reserve_family`,
`storage`, `system`). So C-2 cannot be closed in the parent at zero LP. It is a **deliverable of
the shards** — every replay writes it — and each shard prompt requires it in the pushed bundle.

---

## 5. THE SHARD PLAN (rules 32 / 33 / 34)

Two shards, each **one `--years 2020 2021 2022 2023 2024 2025` invocation into one bundle**
(rule 32(b): one registrable run = one shard = one solve; rule 34(c): every year the ISO carries;
rule 16 `[R-ALLYEARS]`). Per-year fan-out is banned and is not used.

| shard | pinned SHA | registry | purpose |
|---|---|---|---|
| **CONTROL** | the PRECOMMIT commit (docs only) | 2020 **absent** | re-establishes the control at HEAD, which G-DRIFT §2.2 shows is required |
| **ARM** | PRECOMMIT + the 2020 entry | 2020 **present** | C-1 |

Differencing two immutable SHAs is what makes the arm a single delta **without a new
`ScenarioConfig` field** — which is G3. No gate is added to the registry.

**Memory is the hard constraint and the prompt stops on it first** (charter; rule 32(c)(8);
the pjm-h10 OOM). Each shard's first act, before any setup spend:

```
P=$(grep -E '^[0-9]+:memory:' /proc/self/cgroup | cut -d: -f3)
cat /sys/fs/cgroup/memory$P/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup$P/memory.max
```

**Under ~16 GiB ⇒ STOP IMMEDIATELY and report the number.** Never `free`, never `MemTotal`, never
the root cgroup. A shard that stops with a clear report is a SUCCESS.

**Setup is six steps and NONE is forbidden** (the pjm-h10 error, ADDENDUM §2/§3): `uv sync --no-dev`;
`hydrate_data.py --profile pjm`; `curate_transfer_interface_limits.py --isos PJM`;
`curate_ramp_capability.py --isos PJM`; any further `data/clean` partition the runner hard-raises
on (read the datatype it names and curate that one — the full `regenerate_clean.py` is ~42 min, and
is permitted but not preferred); and
`fetch_pjm_da_virtuals.py --years 2020 2021 2022 2023 2024 2025 --feeds hrl_da_incs_decs`
(licensing-gitignored, in no clone, ever; DataMiner2 serves 2020–2022 — verified).

**The turn may not end while the solve runs** — background job plus an in-turn poll loop. There is
no messaging route from a CCR parent to a CCR shard, so the prompt is the only channel.

**The bundle is PUSHED** (rule 34(a)): `.gitignore` **negation** for its own out-dir then a
**plain `git add`** — never `git add -f` (the classifier refuses it), never `git add -A`/`git add .`.
It must include `dispatch/<year>_P1.parquet` (registration raises `FileNotFoundError` without it)
and `hourly/network_<year>.parquet` (C-2).

---

## 6. OPEN QUESTIONS FOR THE OWNER

**Q1 — the three truncated ladder rungs (§3.2, G1).** Three committed rungs are one cent below
what the frozen formula produces, from hand transcription. They sit in 2023/2024/2025 — the
CALIBRATED training keeper's own scored years. Fixing them is a three-rung solve-affecting change
to a keeper, with no data change to cite, so I have **not** touched them. Fix in a dedicated card,
or leave as a documented transcription tolerance?

**Q2 — C-1's promotion, knowing it is predicted to make a gate worse (§3.3).** The measured case is
rules 14/23: a keeper year must run the keeper's own mechanism, and 2020's small residual is the
compensating estimate rule 14 describes. Rule 1 says the mechanism stays in even if the fit
worsens. Confirming the owner wants it armed on that basis.

**Q3 — should the MER dual be gated? (§2.2, LIVE-4.)** It is unconditional with no config field, so
no shard can avoid it without the code edit its prompt forbids, and it runs in the exact window
where the pjm-h10 PJM shard was OOM-killed. The attribution is genuinely confounded and I am not
claiming it caused that kill. But an ungated diagnostic that every solve on every ISO pays, in the
window that owns the measured year peak, is worth a deliberate decision rather than a default.
Related, and already put to the owner by pjm-h10: preflight currently **predicts** the OOM and runs
anyway; refusing would convert a wasted container into a legible stop.

**Q4 — the 192,229 MW artifact demand hour** (FINDING §5.2). Still unarmed. It survives the
2.5×-median screen in 2020 at 1 p.m., is 20–30 % above every clean year's maximum in the model's
own input file, and fails the extract's own identity by −56,665 MW; a second hour sits at
176,085 MW. The model serves both. The candidate screen (`|D + TI − NG|`) is itself broken wholesale
in 2019/2020/2025, so it needs a design distinguishing a broken *hour* from a broken *year*. That is
its own charter, not this card's.

---

## 7. LEDGER AT WRITE TIME

**Nothing armed beyond the C-1 registry key. No `ScenarioConfig` field added, no default flipped,
no run registered, no determination changed, no keeper touched, no mechanism-matrix verdict moved.
ZERO LP minutes in this session.**

Rule 31 `[R-RETAIN]`: nothing is deleted. Rule 33 `[R-SHARD-ARCHIVE]`: shards are archived only
after the parent has fetched, checked out and verified their bundles, and any left alive are named
in the RESULT.
