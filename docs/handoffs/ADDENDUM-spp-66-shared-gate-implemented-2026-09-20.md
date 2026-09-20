# ADDENDUM — SPP-66. The **shared gate** is implemented. Owner ruling executed; no LP spent.

**Lane** SPP-66 · **Ruling** owner, 2026-09-20, verbatim: **"Shared gate"** — answering the scope
question put in `PRECOMMIT-spp-66-rbd-netload-window-2026-09-20.md` §6 (gate the coal-sync floor
alone, or gate the shared ranking for all four floors and arm it per-ISO). The lane had recommended
the shared form; the owner chose it. · **Base** `00aa4a32` · **ZERO LP RAN.** No shard, no bundle, no
registration, no keeper file touched, nothing deleted (rule 31 `[R-RETAIN]`).

---

## 1. What was built

One new **shared, default-`False`** field, `ScenarioConfig.commitment_floor_window_netload`, which
replaces the **single** series all four commitment floors shape themselves on.

The four floors do **not** consume it identically, which is exactly why a per-floor gate would have
been the wrong object: three rank hours by it (top-k carries the floor, plus
`_commitment_day_order`'s day grain) and the fourth builds per-month `max(load - median, 0)`
placement weights from it. The shared thing is **`sys_load` itself**, not the `argsort`. So the gate
resolves that series **once**, into `_window_shape`, before any floor is composed — and all four move
together by construction (rule 19 `[R-ONE-MECH]`).

| file | change |
|---|---|
| `config/scenarios.py` | the field, its citation block, `TIER_TAGS` = 1, and registration in **both** `_CACHE_KEY_OPTIONAL_FIELDS` and `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` (same commit — the nyiso-119 discipline) |
| `data/fleet/arrays.py` | `_window_shape` resolved once in `_compose_min_gen_floors`; the four inline `sys_load = (...)` blocks collapse to `sys_load = _window_shape`; `netload_shape` added to both signatures |
| `scripts/run_calibration.py` | builds the net-load series at the **calibration** fleet seam; `run_year` kwarg + `with_overrides` wiring |
| `src/market_sim/runner.py` | same at the **runner** fleet seam |
| `tests/unit/data/test_commitment_floor_window_netload.py` | 6 tests (new) |

## 2. THREE CORRECTIONS, stated rather than quietly fixed

**(a) §5 named `runner.py:2757` as "the seam", validated. That was INCOMPLETE and, for this lane,
the wrong one.** `scripts/run_calibration.py` has its **own** `generators_to_fleet_arrays` call, and
*that* is the path every calibration run and every `run_year(fleet_only=True)` reconstruction takes.
This was not caught by reading — it was caught by the liveness test: with only `runner.py` wired, the
**armed** arm reproduced the control's floors **cell for cell**, 9,706,080 of 9,706,080. A gate armed
on one seam only is inert in precisely the lane that would use it. **Both seams are now wired**, and
the row note says so, so no successor repeats it.

**(b) The new parameter was first inserted mid-signature on `_compose_min_gen_floors`, which silently
re-bound every argument after it** for the two fully-positional callers in
`tests/unit/data/test_mustrun_commitment_feasibility_clip.py` (5 failures, `TypeError`). It is now
**trailing and defaulted** (`netload_shape: np.ndarray | None = None`), with a comment saying why, so
no future insertion repeats it either.

**(c) The `runner.py` wiring broke four tests in `tests/unit/pipeline/test_runner.py`, and I had
talked myself out of checking.** `_trace_fleet_build`'s `fake_fleet_arrays` declares a fixed keyword
signature, so the unconditional `netload_shape=` at the call site hit it with
`TypeError: got an unexpected keyword argument 'netload_shape'` — taking down
`TestCampdBinningGate::test_ercot_takes_campd_path` and all three of
`TestHistoricOutageOverlayDefault`. I had reasoned that the gate being off would protect them; it
does not, because the kwarg is passed whether or not the flag is set and the fake never sees the
flag. **The fix is `**_kw` on the fake**, matching `fake_demand` and `fake_renewables` in the same
helper, which already take it — that helper exists to observe the outage overlay and the binning
path, not to pin the fleet-build call surface. The tempting alternative, passing `netload_shape`
only when non-`None`, was **rejected**: it would make the call site conditional to dodge a test and
hide the parameter from exactly the tracer meant to watch it.

**How it was caught, and the method that caught all three of these:** diffing the FAILURE SET against
clean `origin/main` sources rather than reading the count. The subset ran 11 failed / 21 passed on
this tree against 7 / 25 on `main`; after the fix it is 7 / 25 with an **empty set difference in both
directions**. A raw failure count would have looked like ordinary pre-existing noise in a repo whose
`main` is already red in several places.

A third fleet build exists at `data/fleet/assembly.py` (inside `bins_to_fleet`) and passes **no**
`load_shape` at all — its floors have no window either way, so the gate is correctly inert there and
no new asymmetry is introduced. `runner.py`'s pipeline-lookahead build (the pro-forma capacity stack)
likewise passes `netload_shape=None` deliberately.

## 3. Inertness — MEASURED, not asserted (rule 25 `[R-ISO-SCOPE]`)

- **Cache keys: every one byte-stable.** All **19** committed `results/calibration/*/run_config.json`
  re-keyed under both trees, plus a default and a backcast config — **21 configs, 0 errors, diff
  empty.** No bundle in any ISO is re-keyed. (SPP keeper 13 `be07f1f3e9836dc0`, its rung
  `5814cc5ebf0349ba`, unchanged.)
- **Floors, gate OFF: cell-for-cell identical to clean `main`.** A `fleet_only` rebuild of SPP keeper
  13's own 2023 recipe differs from the committed `floors/2023_P1.npz` in **272 of 9,706,080** cells
  (max 357.679535 MW, +44 MWh of 46,556,188 = +0.0001 %) — and the **identical** 272 cells and
  identical 357.679535 MW maximum appear on **clean `origin/main`**, so **none of it is this
  change**.
  **CORRECTION (§3a below): those 272 cells are NOT pin-to-pin code drift.** This bullet first
  attributed them to "pre-existing drift between the keeper's pin `f80de3e1` and HEAD", and the
  G-DRIFT measurement falsifies that: `min_gen` rebuilds **byte-identically at both pins**. They are
  a *rebuild-versus-solve-time* artifact — what `fleet_only` reconstructs differs very slightly from
  what the solve wrote — and they are present at `f80de3e1` too. The number is unchanged; the cause
  named for it was wrong.
- **Solve-surface fingerprint: nothing moved.** `solve_surface_register.py --diff origin/main` →
  *"307 -> 307 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED."*
- **Matrix CI gate passes**, including the `--base origin/main` diff gate that checks new-field
  registration.

### 3a. G-DRIFT, by measurement rather than by hunk audit (rule 29(b))

Before spending seven shards the lane owed proof that keeper 13's committed bundle is still a valid
control at the arm's pin — `origin/main` had moved **128 files** past the keeper's `f80de3e1`, and
rule 29(b) is explicit that *"a 'files changed, therefore void' heuristic with no audit behind it is
not a reason to spend an LP."*

Rather than classify hunks, the lane **measured the thing the hunks could affect**: it rebuilt keeper
13's own 2023 recipe (`run_year(fleet_only=True)`, zero LP) at **both** pins — `f80de3e1` and the arm
pin `17a8a14c` — and diffed every LP input array.

| array | shape | result |
|---|---|---|
| `mc_base` | 1108 × 8760 | **INERT** (0 cells) |
| `availability` | 1108 × 8760 | **INERT** |
| `min_gen` | 1108 × 8760 | **INERT** |
| `demand` | 2 × 8760 | **INERT** |
| `pmax` / `pmin` / `heat_rate` / `vom` / `emission_rate` | 1108 | **INERT** |
| `unit_ids` / `plant_group` | 1108 | identical |

**Every LP input is byte-identical across the two pins. Form 4 is valid, the keeper's committed
bundle IS the control, and NO control solve is earned** — so each shard solves the arm only, one leg,
and the seven shards cost seven year-solves rather than fourteen. This is the sense in which rule
29(b) calls G-DRIFT *stronger* than a control solve: a control solve would have shown two numbers
differing, whereas this shows that **nothing the LP reads moved at all**.

It also supplies the correction folded into §3 above: since `min_gen` is inert pin-to-pin, the 272
differing floor cells cannot be code drift.

**A pre-existing red on `main`, reported and NOT absorbed:**
`tests/regression/test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned` fails for
**all six** ISOs at `00aa4a32`, with byte-identical fingerprint pairs in both trees (e.g. PJM
`151fce41b8d76651` (216 rows) vs pinned `905116f13849914f` (214 rows)). This is `main`'s to fix, not
this lane's, and it is named here so nobody later mistakes it for fallout from this change.

## 4. Liveness — the gate is not a no-op

Armed on the same zero-LP SPP 2023 rebuild: **52,425 floor cells move** and floored energy goes
**46,556,188 → 46,999,040 MWh (+442,852, +0.95 %)**, against the unarmed 272 cells / +44 MWh. The
unit tests additionally pin the shape of the move: the armed window is **exactly** the top-k hours by
net load, with the **same k and the same level** as the system-load window (rule 19 — the window
moves; its size and level do not), and a `None`/short `netload_shape` **falls back** to `load_shape`
rather than dropping the floor, so a plumbing gap can never silently un-floor an armed run.

**Both arming routes were exercised and agree exactly.** The `run_year` kwarg (used by
`fleet_only` reconstructions) and the generic `prb_overrides` channel that `replay_keeper --set`
actually uses — the shard route — each produce the **same 52,425 cells and the same +442,852 MWh**.
The `--set` path was checked end-to-end rather than reasoned about, because its override is applied
at `run_calibration.py` ~line 2057 while the floor seam reads `config` at ~line 4023; the ordering
is fine, and is now measured to be fine.

## 5. Matrix (rule 28(c), same PR)

New base row `commitment_floor_window_netload` (`cat: "commit"`, `mode: "BF"`) plus a cell in **every
one of the nine** ISO shards: **SPP `O`** (open — the ISO the evidence came from, not yet solved),
every other ISO **`U`**, minted by the same-PR duty only with **no adjudication made or implied**
(rules 25 / 28(d)). Each non-SPP cell carries a REACH NOTE naming what the gate can actually touch
there — PJM is called out as the only other ISO whose committed bundles arm
`coal_sync_srmc_tranche` (3 configs), so an arming decision there is material. Line anchors that
drifted from the `scenarios.py` insertion were repaired with the tool's own
`--fix-anchors` (digits only).

## 6. The seven shards — LAUNCHED

**LAUNCHED 2026-09-20** — seven shards, one per year, all pinned to
`17a8a14c7e10fe6f9e0db7101a587c54d4fc11a8` (the arm tree, NOT `origin/main`'s tip, which had already
moved 128 files past it and would have handed the shards a tree nobody tested). Each solves the
**arm only** — §3a's G-DRIFT result is what makes that legitimate. The two config families are
solved from their **own** bundles, which is trap (n): `mid_vintage_exit_carry` is `False` on the
span and `True` on the rung, and each shard hard-stops on its own expected value.

| year | family | bundle replayed | out-dir | branch | session |
|---|---|---|---|---|---|
| 2019 | rung | spp51_syncfloor_rung | spp66_netwin_2019 | claude/spp66-netwin-2019 | session_019zQYcECx8e4DAGocKV77iQ |
| 2020 | rung | spp51_syncfloor_rung | spp66_netwin_2020 | claude/spp66-netwin-2020 | session_011X4U3prhUtJuEmm4bCSGFc |
| 2021 | rung | spp51_syncfloor_rung | spp66_netwin_2021 | claude/spp66-netwin-2021 | session_01BMiDnTEUcFdDWdBG6cr62S |
| 2022 | rung | spp51_syncfloor_rung | spp66_netwin_2022 | claude/spp66-netwin-2022 | session_017kpRFgqqEBFzFoSbUWECWd |
| 2023 | span | spp51_syncfloor_span | spp66_netwin_2023 | claude/spp66-netwin-2023 | session_01AYLq7hu4ciZVKthctkxKv8 |
| 2024 | span | spp51_syncfloor_span | spp66_netwin_2024 | claude/spp66-netwin-2024 | session_01BuruTx4CAJL7KzAAbZkPsd |
| 2025 | span | spp51_syncfloor_span | spp66_netwin_2025 | claude/spp66-netwin-2025 | session_01UJAgwAKPbcaiwUV8bv97dr |

They compose **separately** — span and rung — and the rung is stamped to the keeper only after the
keeper's payload renders (rule 30 `[R-TOUCHPOINT-FOLD]` (a), trap (i)).

**Previous arming instructions, retained for reference.** Arming for SPP is
`replay_keeper.py <keeper bundle> --years <y> --out-dir … --set commitment_floor_window_netload=true`
(the generic `prb_overrides` channel; a `run_year` kwarg also exists for `fleet_only` rebuilds).
Execution shape is unchanged from PRECOMMIT §5: **seven shards, one per year 2019-2025** (rules 32 /
34 / 36), each solving the arm only against keeper 13's committed bundle as control (form 4), each
pushing its **full** bundle including `dispatch/<y>_P1.parquet`; span and rung composed **separately**
(trap (n)); G-DRIFT re-audited at the new pin first — and note §3's 272-cell / +44 MWh pre-existing
floor drift is the noise floor any HEAD differencing now carries.

The **pre-registered predictions in PRECOMMIT §5 stand unamended** and were written before any of
this. They are what the arm gets scored against.
