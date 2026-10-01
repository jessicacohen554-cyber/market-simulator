# ADDENDUM — caiso-268 SPAN, **Card 0: the G-DRIFT code audit**

**Session caiso-268, shard SPAN, branch `claude/caiso268-span`, 2026-09-09.**
**PUSHED BEFORE THE FIRST LP OF THIS SHARD.** Every number below is read from git and from
committed artifacts at **zero LP cost**; no solver has been called at the moment this document is
committed. That ordering is the point — an audit written after a result can be written to fit it.

Charter: `docs/PRECOMMIT-caiso268-fossil-offer-8pct-2026-09-09.md` §5, which defers G-DRIFT to
this shard as its Card 0.

---

## §1 — The claim being earned

Rule 29 `[R-SCREEN]` (b) makes the incumbent keeper's **committed bundle** the control and forbids
spending a control solve to establish HEAD drift. The claim is **G-CTRL form 4**:

> the committed keeper bundle `results/calibration/caiso_fuelvintage_span`
> (run `2026-09-09-caiso-fuelvintage-860-gas`, `git_sha 873f7564`) is a valid control for an arm
> solved at HEAD `3ac68fff`.

Rule 29(b) states the price of that claim exactly: **every changed hunk on the backcast solve path
must be classified INERT, with its reason cited, or LIVE** — and *"files changed, therefore void"*
with no audit behind it is not a reason to spend an LP. A **LIVE** hunk is the only thing that
earns a control solve.

`873f7564` resolves: `873f7564b2bc879df68334df4796a7f4d440f9c6`. It is a real object in this
repository, so unlike the immediately preceding CAISO lane — whose keeper recorded an
**unresolvable** `git_sha e162147b` and which therefore had to fall back to a measured
G-DRIFT-M (`docs/RESULT-caiso-fuelvintage-2026-09-09.md` §4) — the code audit rule 29(b) actually
names **can be run here**, and is.

## §2 — The diff, in full

```
git diff --stat 873f7564 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

| file | + | − |
|---|--:|--:|
| `src/market_sim/config/constants.py` | 83 | 19 |
| `src/market_sim/config/solve_surface_declared.py` | 1 | 0 |
| **total** | **83** | **19** |

**Two files. Two hunks in one, one hunk in the other.** The PRECOMMIT predicted the keeper's youth
would make this small enough to audit honestly, and it is — the contrast with caiso-267, which
faced 94 files / +46,838 / −26,486 lines and refused to assert a classification it could not
support, is the whole reason that lane spent a control solve and this one does not.

`data/raw/_validation-source`, `data/raw/reference`, `scripts/lib`, `scripts/run_calibration.py`
and `scripts/run_calibration_full.py` are **unchanged** — zero hunks, so nothing to classify.

## §3 — Hunk-by-hunk classification

### Hunk 1 + 2 — `src/market_sim/config/constants.py`, `NUCLEAR_MONTHLY_CF_BY_YEAR` — **INERT**

Both hunks sit inside `NUCLEAR_MONTHLY_CF_BY_YEAR`, under the `"NYISO"` key (hunk 1, lines
~2545-2570) and the `"NEISO"` key (hunk 2, lines ~2604-2680). They retire two fleet-vintage
caveats — NYISO's Indian Point 2/3 and NEISO's Pilgrim — that the 2019+ retiree-window move
(`RETIREMENT_WINDOW_START`, commit `7934e92c`, already in the keeper) closed, and replace them with
successor caveats about the derive's fleet definition.

**Reason cited — every changed line is a COMMENT. Not one value moves.** Verified mechanically
rather than by eye: filtering the diff to added/removed lines whose content is non-empty and does
not begin with `#` returns **0 lines**.

```
non-comment changed lines in constants.py: 0
```

The three classification limbs that also apply, any one of which is sufficient:

1. **Another ISO's branch.** The dict is keyed by ISO; the edits are under `"NYISO"` and `"NEISO"`.
   A CAISO run reads `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]`, which is not in either hunk.
2. **A year no backcast reaches.** The substance concerns 2019-2022 fleet vintage. This arm solves
   2023, 2024, 2025 only (rule 22 — training tier, no marker, no `--holdout-authorized`).
3. **Both hunks are self-describing about their own inertness**: the NEISO hunk states in terms
   that the table was *"NOT re-derived here on purpose"* precisely because it sits on the solve
   surface and editing it would re-key every ISO's configs. The comment change was made *instead
   of* a value change, for that reason.

### Hunk 3 — `src/market_sim/config/solve_surface_declared.py`, +1 line — **INERT**

```diff
+    "HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT": {"NYISO": "0d6bce3ba875ed62"},
```

**Reason cited — a per-ISO declaration scoped to NYISO, and the name is not in CAISO's projected
surface at all.** `solve_surface_declared.DECLARED` records each surface name's *frozen declared
value hash* so that a re-derived table re-keys the ISOs whose rows moved (capx D79). This entry
adds a **new** name at a **NYISO-only** scope. Measured at HEAD:

```
HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT in CAISO surface: False
```

The ISO projection drops it, so it cannot enter CAISO's row set, its fingerprint, or its cache key.
This is the same mechanism the previous lane measured from the other side: CAISO's surface moved by
exactly two rows when four names were added, because the projection dropped the two that were not
CAISO's.

### Not in the audited path, but invoked by this shard — `scripts/replay_keeper.py`, +8 lines — **INERT**

The charter's audit list does not name `replay_keeper.py`, but it is the script this shard actually
runs, so it is classified here rather than left silently outside the frame.

```diff
+    "model_changes_note",
```

One key added to the replay guard's `_IGNORE` set. `model_changes_note` is a **recorded-only
free-text provenance field** in the same class as `timestamp` / `git_sha` / `basis_sha`: it selects
no mechanism and has no `solve_and_persist` kwarg. Adding it to `_IGNORE` changes which *unmapped
keys* the guard refuses to replay over; it changes no LP row and no resolved config value. **Pure
provenance accounting.** (The keeper's own `run_config.json` does carry a `model_changes_note` key,
so this hunk is what lets the replay proceed at all — it is enabling, not perturbing.)

## §4 — The independent instrument agrees, and it is stronger than the hunk count

The repo's own capx-D79 solve-surface fingerprint answers the same question end-to-end, without
relying on my reading of any hunk. It hashes CAISO's **whole projected row set**, so a value change
anywhere on the surface — including one I mis-classified — moves it.

| | fingerprint | rows | moved rows |
|---|---|--:|---|
| keeper's recorded `solve_surface` block | `cba92d202f32f9fd` | 204 | `NUCLEAR_MONTHLY_CF_BY_YEAR: 9f120808f18b3f19`, `STATE_CARBON_PRICE_BY_ISO: c970824c3c583991` |
| **recomputed at HEAD `3ac68fff`** | **`cba92d202f32f9fd`** | **204** | **identical** |

**MATCH.** CAISO's solve surface at HEAD is byte-identical to the surface the keeper solved on,
including the `NUCLEAR_MONTHLY_CF_BY_YEAR` row hash (`9f120808f18b3f19`) that hunks 1-2 touch — which
is the mechanical confirmation that those hunks moved comments and nothing else.

This is what rule 29(b) means by the audit being *stronger* than a control solve for this question:
a control solve would have shown two numbers agreeing to some tolerance; this says **which lines
changed and that the surface they live on did not move at all.** It cost seconds.

## §5 — Verdict

**ALL HUNKS INERT. ZERO LIVE HUNKS. G-CTRL form 4 HOLDS.**

The committed keeper bundle `results/calibration/caiso_fuelvintage_span` is this shard's control,
and **no control solve is spent**.

Recorded against interest, so a later reader weighs it: this audit's confidence rests on the
diff being two files of comments plus one NYISO-scoped declaration line. Had the diff been large,
the honest move would have been caiso-267's — refuse the classification and spend the control.
It was not, so it was not.

**Next: the arm. `results/calibration/caiso268_fossil92_span`, 2023 2024 2025, ONE invocation,
years sequential.**
