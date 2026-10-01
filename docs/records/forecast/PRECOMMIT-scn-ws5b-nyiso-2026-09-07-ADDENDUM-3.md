# ADDENDUM 3 to PRECOMMIT-scn-ws5b-nyiso-2026-09-07 — **STOP: NYISO's solve surface moved mid-campaign. Three named rows, routed to SCN-DESK, and the remaining legs are pinned rather than re-keyed.**

**Trigger:** shard S-3b refused to solve `CES-P60` on a **cache-key mismatch** against the
PRECOMMIT §4 pre-declaration and stopped without changing anything — the STOP condition working
exactly as written. **No shard "fixed" the key, and nothing was re-pinned silently.** This
addendum is the audit that mismatch earned, written before any further leg is solved.

---

## 1. What happened, and what it is NOT

**It is not a shard error, not a config drift, and not the two NYISO adequacy gates.** Ruling
them out was the first thing done, because each would have meant something different:

| candidate cause | test | result |
|---|---|---|
| a shard edited a config | `git status` clean on its branch; it stopped before solving | **ruled out** |
| the new `netload_drag_min_run_persistence` field (pjm-177) | key at `ad197380` == key at `1d1336d4` | **ruled out** — that field moves zero keys; it is registered with its frozen drop value `"False"` and drops correctly |
| a registered field missing its drop declaration | all **284** `_CACHE_KEY_OPTIONAL_FIELDS` members have a declared drop default; the missing-set is **empty** | **ruled out** |
| the two NYISO adequacy gates (`nyiso_requirement_forecast_peak` / `_vintage_factors`, capx D60/Q41) | both resolve **`True` at BOTH commits** — identical posture | **ruled out** (they enter the key equally on both sides; a red herring) |
| **the capx D79 solve-surface fingerprint** | `surface_stamp("NYISO", cfg)` compared across the window | **THIS IS IT** |

```
4e4ad90d  fingerprint 48353917f7510af3   rows 206   moved {}
ad197380  fingerprint 1eefed492204fab7   rows 209   moved {}
```

**Three new rows entered NYISO's projection of the seven `SURFACE_MODULES`**, and the fingerprint
is part of `cache_key()` since capx D79 (owner ruling Q54) — so every NYISO key moved, including
the committed Stage-A control:

```
Stage-A REF 2026-2030   committed f10cc93084b4c0db
  at 4e4ad90d (PRECOMMIT HEAD)  f10cc93084b4c0db   MATCH
  at ad197380 / 1d1336d4        5f23b38313ca8150   MOVED
```

## 2. The three rows, named

| new NYISO surface row | landed by | why it is **LIVE for NYISO**, not INERT |
|---|---|---|
| **`F923_GAS_PRICE_PLAUSIBILITY_BAND`** | spp-49 — "the EIA-923 own-month gas-price plausibility screen (**registered gate, default ON**)" | A **default-ON** screen on EIA-923 delivered gas prices. NYISO's gas prices resolve through F923. A gas-price screen is a marginal-cost input on a gas-margin ISO. |
| **`EGRID_CT_HR_PHYSICAL_FLOOR`** | spp-49 — "the simple-cycle heat-rate floor (construction)" | A physical heat-rate floor on CT units. NYISO carries **3,033.8 MW of `gas_ct`** (committed Stage-A REF 2030). |
| **`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`** | "Add `hydro_budget_period_by_instrument`: use-it-or-lose-it hydro budgets" | A per-plant hydro budget period. NYISO is a hydro ISO — **26.2 TWh**, one of the two fuels carrying its clean share (Stage-A §1.2). |

**None of these is dischargeable by any of the INERT reasons rule 29(b) enumerates** — not a
forecast-only path, not another ISO's branch, not a default-off flag absent from the recipe, not
a per-ISO artifact NYISO lacks, not timing/diagnostics. Two are *named* for another ISO's lane but
land in **shared registry tables** that NYISO reads, which is the same class of seam this lane
already had to measure once (SPP-41, PRECOMMIT §2.4) — and unlike that one, these are not measured
to zero here, because measuring them is a solve, and the whole point of the STOP is not to spend
one on a question the desk owns.

**Per the charter: a genuinely LIVE hunk is a STOP and a route to SCN-DESK — never a silent
re-pin, never a control solve.** That is what this is.

## 3. Why this is campaign-critical, not bookkeeping

`REF` **already solved** on the old surface, and its own committed bundle proves it — capx D79's
instrument doing exactly the job it was built for:

```
REF full_horizon_summary.json -> solve_surface
  {"fingerprint": "48353917f7510af3", "rows": 206, "git_sha": "1cb976f", "iso": "NYISO",
   "epochs": [], "moved": {}, "schema": 1}
```

`CAP-STATE-TIGHT` is in flight from a checkout at `4e4ad90d`, whose fingerprint is the **same**
`48353917f7510af3`. So two of five legs are on the 206-row surface.

**Had I let `CES-P60` solve at HEAD, it would have run on the 209-row surface, and the
`CES-P60 − REF` delta — the entire object of the leg — would have confounded a $60 CES premium
with a gas-price screen, a CT heat-rate floor and a hydro budget rule.** That is precisely the
confound a pinned campaign exists to prevent, and it would have been invisible in the summary:
the leg would have completed, reported 25/25 years, and been wrong as a *delta* while being
perfectly valid as a *run*.

## 4. What this lane does, and the line it does not cross

**DECIDED, within this lane's authority:** the three remaining legs (`CES-P60`, `CES-T80`,
`ALL-CLEAN`) are solved from a checkout **pinned at `4e4ad90d`** — the PRECOMMIT's own audited
HEAD, carrying fingerprint `48353917f7510af3`, the same surface `REF` and `CAP-STATE-TIGHT` are
on. At that commit the PRECOMMIT §4 keys are restored exactly, which is the independent proof the
pin is the right one:

| leg | key at `4e4ad90d` = PRECOMMIT §4 | on the 206-row surface |
|---|---|---|
| REF | `f1a2ef17634b0467` | **solved** ✓ |
| CAP-STATE-TIGHT | `462d197ef1f9e023` | **in flight** ✓ |
| CES-P60 | `ddff74e2738eaf96` | pinned |
| CES-T80 | `fc3ad07981d95d84` | pinned |
| ALL-CLEAN | `774db75da9f4d95a` | pinned |

**THIS IS NOT A RE-PIN.** THE PIN — `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, Stage A's and
this lane's, against which the G-DRIFT audit was written and the 2026–2030 identity gate is
scored — is **unchanged**. What is pinned is the shard *checkout*, which every shard already fixed
implicitly by branching from one commit; making it explicit is what keeps the five legs
internally differenceable. The published PRECOMMIT audit covers `4e4ad90d` exactly, so pinning
there also keeps every leg inside the audit that was published before the first solve.

**NOT DECIDED HERE — routed to SCN-DESK.** Three questions this lane will not answer for itself:

1. **Should the Stage-B campaign be re-solved on the 209-row surface?** All five legs would have
   to move together (≈15–17 h of LP, `REF` and `CAP-STATE-TIGHT` included), and the 2026–2030
   identity gate would then be scored against a Stage A that is itself on the 206-row surface — so
   a gate miss would become expected rather than diagnostic. That is a campaign-scope call.
2. **Are the three rows INERT for NYISO in fact?** Answering it costs a paired solve. This lane
   has not spent one and is not asking to.
3. **Is a NEW registry row supposed to move a key at all?** D79's own design note says *"adding a
   table moves no key"*, because a name enters the key only when its live hash differs from its
   **frozen registration-time declaration**. These three rows have no declaration yet, and the
   fingerprint moved. Either they need a `solve_surface_declared` entry (in which case this is a
   registration gap that will re-key every ISO on every future registry addition), or the
   behaviour is intended and the design note is loose. **That is a capx-director question, not a
   scenario-desk one**, and it affects every lane holding a pin — which right now includes the
   NEISO Stage-B sibling. `config/solve_surface*.py` is outside this lane's regions and was not
   touched.

## 5. What this does NOT change

- **`REF` stays registered.** It solved on the 206-row surface at `1cb976f`, its identity gate
  passed exactly (232 scalars, worst `|rel|` = 0.000e+00, ADDENDUM 2 §2), and un-registering a
  sound bundle strands it and reddens the parity gate — the same reasoning ruling S17 gave.
- **`CAP-STATE-TIGHT` is NOT killed.** It is hours into a ≈5.4 h+ indivisible solve on the
  correct surface. Killing it would destroy the campaign's most expensive leg to fix a problem it
  does not have.
- **`CARB-MID` stays killed at phase 0** on the 25-year identity of PRECOMMIT §3, which is a
  resolver-level proof and is untouched by any of this.
- **No prediction in PRECOMMIT §7 is edited.** P-1's identity gate is still scored against Stage A
  at THE PIN, as pre-registered.

---

*Written after the S-3b mismatch and before any further leg was solved. Parent:
`docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md`, ADDENDUM 1, ADDENDUM 2.*
