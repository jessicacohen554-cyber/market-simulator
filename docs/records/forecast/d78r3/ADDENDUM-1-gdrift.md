# ADDENDUM 1 — capx D78-R3: the G-DRIFT audit for the earned control leg

**Pushed BEFORE the control-P solve**, per PRECOMMIT §5.1 and §7. Rule 29(b): the audit is
recorded before the arm — here, before the leg — so it cannot be written to fit a result.

## 1. The question this audit answers

The control I re-solve is at **`0f7a4842`**. The committed mover counts the W5″ re-grade reads
came from a control D78-R2 solved at **`65e12b21`** (`ADDENDUM-1-w4prime-band.md` §1). If any
solve-path hunk between those two states is LIVE for a bare PJM T1-H hindcast, then the
derivation base and the graded comparison sit at different code states and the derivation does
not transfer.

`main` moved `65e12b21 → 0f7a4842`, **89 commits**.

```
git diff --stat 65e12b21..0f7a4842 -- src/market_sim scripts/run_capacity_hindcast.py \
    scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib \
    data/raw/_validation-source data/raw/reference
```

**5 files, +381 −16.** Every hunk classified below. **No file this lane's entry path executes is
changed behaviourally.**

## 2. The classification — every hunk, with its reason

| file | Δ | verdict | reason |
|---|---|:--:|---|
| `src/market_sim/config/scenarios.py` | +103 −0 | **INERT** | Two new `ScenarioConfig` fields, both `bool = False`: `eia860_vintage_tracks_solve_year` (pjm-167, *"Engaged in backcast mode only"*, `mode == "backcast"`-guarded at its only caller) and `pjm_interface_feed_admissibility_gate` (pjm-167, default-off, **absent from the control recipe**). Both are registered in `_CACHE_KEY_OPTIONAL_FIELDS` with `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` = `"False"`, i.e. **dropped from the hash at their declared default**, so every pre-existing key is byte-stable. This is rule 29(b)'s named INERT class verbatim: *"a `ScenarioConfig` flag that is default-off AND absent from the keeper's recipe."* |
| `src/market_sim/runner.py` | +18 −4 | **INERT by algebraic identity** | The one behavioural line: `set_eia860_vintage(config.eia860_vintage_year …)` becomes `set_eia860_vintage(resolve_backcast_eia860_vintage(config.eia860_vintage_year, int(config.weather_year) if config.mode == "backcast" else None, config.mode == "backcast" and getattr(…, False)) …)`. **A T1-H hindcast is forecast-mode** (`mode == "forecast"`, `hindcast=True`), so arg 2 evaluates to `None` and arg 3 short-circuits to `False`. Reading the function body (not its comment): clause 1 `if explicit_vintage is not None: return int(explicit_vintage)`; clause 2 needs `tracks_solve_year and solve_year is not None`, both false; clause 3 `return None`. So the expression reduces to **exactly** `config.eia860_vintage_year` — `2020` under `--vintage 2020`. Identical input to `set_eia860_vintage`. |
| `src/market_sim/config/paths.py` | +40 −0 | **INERT** | Pure addition of `resolve_backcast_eia860_vintage`. Its only caller is the `runner.py` line above (and `run_calibration.py`, off this path). No existing function's body changes. |
| `src/market_sim/data/transfer_interface_limits.py` | +168 −11 | **INERT** | The pjm-167 interface-feed admissibility gate. Threaded as `admissibility_gate: bool = False` parameters and guarded by `if admissibility_gate:` at **every** new site, so with the flag off every added branch is unreachable. Independently: it bounds **energy-LP transmission limits**, not the capacity screen, the offer stack or the retirement decision — the objects this lane grades. |
| `scripts/run_calibration.py` | +68 −16 | **INERT — not on this entry path at all** | The **backcast calibration** CLI. `scripts/run_capacity_hindcast.py`'s import block reads `market_sim.config.*`, `market_sim.results.*`, `market_sim.pipeline.api`, `market_sim.runner`, `scripts.lib.*` — it **never** imports `scripts/run_calibration.py`. A hindcast never executes a line of it. |

**ALL HUNKS INERT. ZERO LIVE.** No control solve is owed to *drift* (rule 29(b)); the one this
lane spends is owed to a **deleted derivation base** — no committed artifact anywhere carries the
control's per-DY per-class offer stack (PRECOMMIT §5, enumerated).

## 3. The empirical confirmation this audit will receive

The audit is a code argument; **S1 (G-CTL-ID) is its measurement**, and it is pre-registered in
PRECOMMIT §6. The re-solved control must realize key **`a9c66d8ea25acb9d`** and reproduce
`control_band.json`'s aggregates — window decided **11,514.910 MW**, sector-1 decided
**2,120.754**, `Σg_y` **1,003.400** — to `MW_TOL = 0.001`. If it does, the leg is empirically the
same object across 89 commits, from a different direction than this audit, exactly as D78-R2's
own ADDENDUM 1 §5 obtained across 45.

**If S1 trips**, the pre-registered consequence stands unchanged: the derivation is reported
**NOT TRANSFERABLE**, the lane still grades, and **W5″ is unaffected** — its verdict is already
taken (§ below) and rests on the DECLARED set and committed artifacts, never on this leg.

## 4. Scope note

The W5″ re-grade (step 2) is **already complete and does not depend on this leg**: it reads
`window_compare2.json` and the merged FINDING §5.1 only, spends no LP, and re-solves neither the
arm nor the control. This addendum governs the **derivation** (step 1) alone.
