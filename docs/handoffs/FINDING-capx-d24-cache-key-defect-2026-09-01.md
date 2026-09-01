# FINDING — capx D24: the `cache_key` optional-field defect, characterized and priced

**Lane:** capx D24 · **Model:** Opus · **Branch:** `claude/capx-d24-cache-key-defect-5vlmxd`
**Charter:** the D24 prompt (director pack section unpushed at r#23; the prompt is the charter)
**Graded object:** `src/market_sim/config/scenarios.py::ScenarioConfig.cache_key`,
`_CACHE_KEY_OPTIONAL_FIELDS`, and the cache-epoch ledger in `src/market_sim/results/cache.py`
**Upgraded from:** `docs/handoffs/FINDING-capx-d4m-ercot-t1h-2026-08-31.md` §6 (R-5, demonstrated)
· original observation `docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §5.1
**Date:** 2026-09-01 · **ZERO SOLVES.** Every number below is computed from committed artifacts
and from git history. **NO REPAIR WAS LANDED** — see §7.

---

## 0. Headline

1. **Every one of the 98 analyzable committed forecast run records is exposed.** All 98 have at
   least one field whose default has moved dropped out of their cache key, so their key does not
   encode that field's value. (§2, §3)
2. **Two collision pairs are DEMONSTRATED, not inferred** — two committed runs at one key with a
   provably different posture. One is the known-true positive (`f061b264…`, ERCOT
   `d12c-armed` / `d4m`), which the method finds independently; **the other is NEW and is in
   NEISO** (`07e416f3…`, `capxd14` / `rcrepair`). The defect is not an ERCOT phenomenon. (§4)
3. **No committed run can have been served another committed run's bundle.** All 99 keyed run
   records used a *distinct* cache root (`--out-dir`), 99/99. Both collisions are therefore
   "collides and was re-solved anyway", not "collides and a cached result may have been served" —
   on the evidence available. The residual hazard is real but is about *readers* and about
   *future* runs. (§5)
4. **A committed verdict IS among them.** The NEISO T1-X FF-2D verdict `neiso-t1x` in
   `frontend/data/forecast/ff-verdicts.json` is currently keyed to `rcrepair`, its two preserved
   predecessors (`neiso-t1x-pre-rcrepair` = `capxd14`, `neiso-t1x-pre-d5r`) to `capxd14`, and
   NEISO's §2.1b gate leg `gate/c_crossover_gap` in `program-status.json` cites `capxd14` by
   name. **Reported, not acted on** (charter). No verdict is shown to be *wrong* — see §5. (§6)
5. **D4-I3 §5.1's five-record divergence is NOT this defect.** All seven committed runs at
   `28cef3500ec1fd9e` are *identical in effective posture* on every flipped field, and all seven
   had separate cache roots. This rules the default-flip mechanism, and bundle reuse between
   them, out of that group entirely — narrowing R-5 to a non-`ScenarioConfig` behavioral change
   or a scorer change, zero-solve. (§4.3)
6. **The recorded key fails identity in BOTH directions.** Beyond two-postures→one-key, there is
   also one-posture→two-keys: `ff-t3-neiso-golden/bau` and its `fc6/arms/base` carry
   **byte-identical `scenario_config` dicts and different `cache_key`s**, and four fc6 records'
   keys are not reproducible from their own committed config under any main-line code state in
   the window. Provenance gap, routed. (§4.4)
7. **The cheapest correct repair costs nothing to land.** Option (c′) — refuse a cache hit whose
   stored `config.yaml` disagrees — moves **0 keys**, invalidates **0 committed artifacts**, and
   forces **0 re-solves** except exactly where a genuine collision would have been served.
   Option (a) moves **99/99 forecast and 63/63 backcast keys**, orphaning every on-disk cache in
   both lanes including all six backcast keepers. (§7)

---

## 1. The mechanism, restated exactly

`ScenarioConfig.cache_key()` (`scenarios.py:14271`):

```python
payload_dict = asdict(self)
defaults = ScenarioConfig()                       # <- the LIVE default, recomputed every call
for name in _CACHE_KEY_OPTIONAL_FIELDS:
    if payload_dict.get(name) == getattr(defaults, name):
        payload_dict.pop(name, None)              # <- dropped at whatever the default IS TODAY
```

A registered field is dropped from the hash when it equals the **live** default. Move that
default and the *new*-default run hashes exactly as the *old*-default run did. The key does not
move; the dispatch does.

This is not a discovery of this lane — `scenarios.py`'s own
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` block states it verbatim ("THE HAZARD IT MAKES VISIBLE
(FFR-3A blocker 4, structural)"), `check_cache_key_registration.py` check 3 guards the
*declaration* of a flip, and `results/cache.py`'s 2026-08-31 epoch entry predicted this exact
recurrence in terms. What this lane adds is the measurement: **which fields, which runs, and what
it costs to fix.**

### 1.1 Method, and why it is trustworthy

The analysis is a reproduction, not an inference. For each committed run, the run's own
`run_config.json` carries `scenario_config` (the full resolved config, 765 fields at HEAD),
`cache_key`, and `timestamp`. The key was recomputed from that dict by re-implementing
`cache_key` against the `_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_RETIRED_FIELDS` / field
defaults parsed by AST out of `scenarios.py` **at each of the 170 first-parent commits that
touched it since 2026-07-25** (the window strictly contains every committed forecast run, the
earliest of which is 2026-08-04T01:31Z).

Three independent checks that the reimplementation is faithful:

- `ScenarioConfig()` → **`603c2498bf71d21d`**, byte-identical to the live code and to
  `PINNED_DEFAULT_CACHE_KEY`.
- `d4m`'s committed config under HEAD defaults → **`f061b2646bfaac8b`**, byte-identical to its
  recorded key.
- Across the whole population the recorded key is reproduced exactly at some main-line snapshot
  for **94 of 98** runs. The 4 misses are the fc6 arms of §4.4, whose keys are not derivable from
  their own recorded config at all.

One correction worth recording for anyone repeating this: the drop test must compare
JSON-normalized values. Six `*_offer_surface_netload_pcts` / `*_position_bins` fields are
**tuples** in `asdict` and **lists** in the committed JSON; a naive `==` leaves them in the hash
and no key reproduces. (The real `cache_key` is unaffected — `json.dumps` renders both as lists.)

---

## 2. EXPOSURE — which registered fields have had a default move

Registry growth over the window, measured on main's first-parent line: `_CACHE_KEY_OPTIONAL_FIELDS`
**48 → 218** entries; `ScenarioConfig` **604 → 765** fields. `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
covers all 218 (guard check 3 enforces the parity).

**Every default change of an ever-registered field on main, 2026-07-26 → 2026-09-01 — the
complete list, four events, seven fields:**

| when (UTC) | field | default moved | merge commit | authority |
|---|---|---|---|---|
| 2026-07-26T22:05:55 | `forecast_xyear_warmstart` | `False` → `True` | `c049359cd332` (PR #2957) | D-9 guardrail |
| 2026-08-03T02:21:07 | `retirement_rule` | `'legacy'` → `'pipeline'` | `8f989de9ef1e` (PR #3338) | owner **D-1** |
| 2026-08-03T02:21:07 | `entry_rate_limits` | `False` → `True` | `8f989de9ef1e` | owner **D-2** |
| 2026-08-03T02:21:07 | `entry_commissioning_lag` | `False` → `True` | `8f989de9ef1e` | owner **D-2** |
| 2026-08-03T06:09:44 | `net_cone_forward_escalation` | `'hold_last'` → `'reindex_gross'` | `98cf3465580e` (PR #3356) | owner **D-3a** |
| 2026-08-31T02:37:43 | `storage_entry_availability_gate` | `False` → `True` | `57a700a9d999` (PR #4442) | owner **R-A** |
| 2026-08-31T02:37:43 | `storage_entry_cost_normalized_rank` | `False` → `True` | `57a700a9d999` | owner **R-A** |

All seven were registered **on both sides** of their flip, which is precisely the condition for a
same-key invalidation. **The other 211 registered fields have no default movement in the window
and therefore carry no flip exposure** — their registration behaves exactly as designed.

Two of the seven are behaviorally inert or near-inert by their own record and are listed for
completeness, not as live hazards: `net_cone_forward_escalation` (FFR-3D §4.3–4.5 — the field has
no live consumer and the two modes are byte-identical at the shipped 0.0 rate, classified
BYTE-IDENTICAL with no epoch entry owed), and `forecast_xyear_warmstart` (flipped 2026-07-26,
before every committed forecast run; and D-10 made every shipped forecast runner pass it
**explicitly**, so 92 of 98 runs hash it — see the `warmst` column in §3).

**Registry *additions* are a separate, benign direction.** 170 fields joined the registry in the
window. A run predating a field and a run carrying it at its default hash identically — which is
the design intent, and is sound exactly as far as the field's "byte-identical off" promise holds.
It stops being benign the moment that default is later *armed*, which is how the NEISO collision
in §4.2 arises: `capxd14` predates the field, `rcrepair` carries it at the post-R-A armed
default, and neither value is in the key.

---

## 3. EXPOSURE — the affected-run table

**Population.** 169 committed `run_config.json`; **99 carry a `cache_key`, and all 99 are
`mode="forecast"`**. The 63 `results/calibration/*` records are `mode="backcast"` and carry no
`cache_key` field at all. One of the 99 (`tests/golden/ercot_2026_2040.run_config.json`) has no
timestamp, leaving **98 analyzable**. Three further registered sidecars carry a key with no keyed
run_config committed (`{ercot,miso,pjm}-2023-2027-crossover-ffr2a`, all 2026-08-02, the
`run-config-debt` reconstructions) — **exposure not assessable for those three**.

Every run's key drops between **115 and 215** registered fields (median 155) out of a registry of
120–218 at its solve time. That is the scale of the surface: a key names its config by omission.

Legend for the seven flip columns: `dX` = **dropped** at value X (not in the key), `KX` =
explicitly hashed at X (**protected**), `—X` = field did not exist in the run's schema (effective
posture X, the pre-existence behavior). `T`/`F` = True/False.

| run | ISO | solved (UTC) | key | reg | dropped | SEAG | SECNR | retRule | entRL | entCL | netCONE | warmst |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ffrsc/txexp-off/caiso` | CAISO | 2026-08-04T01:31 | `fe814896` | 120 | 116 | —F | —F | dpipe | dT | dT | drein | dT |
| `ffrsc/txexp-on/caiso` | CAISO | 2026-08-04T01:32 | `f4a79a86` | 120 | 115 | —F | —F | dpipe | dT | dT | drein | dT |
| `ffr3p/caiso-nqc-armed` | CAISO | 2026-08-04T05:39 | `ee0e4480` | 125 | 121 | —F | —F | dpipe | dT | dT | drein | dT |
| `ffr3p/caiso-control` | CAISO | 2026-08-04T05:39 | `e5822277` | 125 | 122 | —F | —F | dpipe | dT | dT | drein | dT |
| `ffr4d/caiso-treated` | CAISO | 2026-08-04T16:08 | **`35b0a89b`** | 128 | 125 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4d/caiso-control` | CAISO | 2026-08-04T16:28 | **`35b0a89b`** | 128 | 125 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4e/caiso-treated` | CAISO | 2026-08-09T05:15 | `bf9b4d73` | 155 | 151 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4e/caiso-control` | CAISO | 2026-08-09T05:15 | **`3d3e836a`** | 155 | 152 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4f/caiso-treated` | CAISO | 2026-08-09T19:39 | `da19509d` | 156 | 152 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4f/caiso-control` | CAISO | 2026-08-09T19:39 | **`3d3e836a`** | 157 | 153 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2023-2025-t1ff-armr-fh4` | CAISO | 2026-08-10T06:15 | `c4071170` | 159 | 151 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2023-2025-t1ff-armk-fh4` | CAISO | 2026-08-10T06:27 | `9759385a` | 159 | 150 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2021-2025-t1ff-armr-fh5` | CAISO | 2026-08-11T09:23 | `ecb416fd` | 165 | 158 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2021-2025-t1ff-armk-fh5` | CAISO | 2026-08-13T07:17 | `05289c29` | 167 | 157 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2021-2025-realized` | CAISO | 2026-08-22T16:13 | **`408f9199`** | 202 | 197 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2021-2025-realized-dumps` | CAISO | 2026-08-24T15:48 | `af508406` | 205 | 200 | —F | —F | dpipe | dT | dT | drein | KF |
| `caiso-2021-2025-realized-control` | CAISO | 2026-08-24T16:08 | **`408f9199`** | 205 | 200 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr3q3-legacy` | ERCOT | 2026-08-04T16:04 | `d065923f` | 128 | 119 | —F | —F | **Klega** | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr3q3-pipeline` | ERCOT | 2026-08-04T16:05 | **`6a824992`** | 128 | 120 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr5a-pipeline` | ERCOT | 2026-08-05T02:37 | **`6a824992`** | 132 | 125 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr5d-unified` | ERCOT | 2026-08-05T20:29 | **`49eac64f`** | 139 | 131 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr5d-shipped` | ERCOT | 2026-08-05T20:34 | **`6a824992`** | 139 | 132 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr8a-unified` | ERCOT | 2026-08-08T23:39 | **`49eac64f`** | 151 | 143 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr8a-scarcity` | ERCOT | 2026-08-08T23:56 | **`816031a3`** | 152 | 142 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr8b-base` | ERCOT | 2026-08-09T04:32 | **`816031a3`** | 155 | 143 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9a-control` | ERCOT | 2026-08-09T06:01 | **`816031a3`** | 155 | 146 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9a-storageseed` | ERCOT | 2026-08-09T06:15 | **`816031a3`** | 155 | 146 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-2023-2025-t1ff-armr-fh4gate` | ERCOT | 2026-08-09T19:21 | `e1714e3d` | 156 | 146 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9b-regen` | ERCOT | 2026-08-09T19:26 | **`816031a3`** | 156 | 146 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-2023-2025-t1ff-armk-fh4` | ERCOT | 2026-08-09T19:32 | `74323d2e` | 156 | 145 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9c-control` | ERCOT | 2026-08-10T06:20 | **`816031a3`** | 159 | 150 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9c-pipeline` | ERCOT | 2026-08-10T06:32 | `3301180d` | 159 | 149 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1ff-armr-ffr9c-full` | ERCOT | 2026-08-10T06:44 | `d6bc5469` | 159 | 147 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-2021-2025-t1ff-armr-fh5` | ERCOT | 2026-08-11T08:08 | **`816031a3`** | 165 | 156 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-2021-2025-t1ff-armk-fh5` | ERCOT | 2026-08-11T08:22 | `5347a4e6` | 165 | 155 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-refresh` | ERCOT | 2026-08-22T16:08 | **`28cef350`** | 202 | 191 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-disarm` | ERCOT | 2026-08-24T15:47 | `2eab2146` | 205 | 195 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-control` | ERCOT | 2026-08-24T15:57 | **`28cef350`** | 205 | 195 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-fwdexp-control` | ERCOT | 2026-08-25T17:47 | **`28cef350`** | 208 | 197 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-fwdexp` | ERCOT | 2026-08-25T17:52 | `a2dc52ff` | 207 | 196 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-d11r-exhaustion` | ERCOT | 2026-08-30T17:39 | `cc7bbe11` | 210 | 199 | —F | —F | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-d11r-control` | ERCOT | 2026-08-30T17:39 | **`28cef350`** | 211 | 200 | —F | —F | dpipe | dT | dT | drein | KF |
| **`ercot-…-t1h-d12c-armed`** | ERCOT | 2026-08-30T22:48 | **`f061b264`** | 218 | 206 | **dF** | **dF** | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-d12c-control` | ERCOT | 2026-08-30T22:49 | **`28cef350`** | 218 | 208 | dF | dF | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-capentry-control` | ERCOT | 2026-08-30T23:35 | **`28cef350`** | 218 | 208 | dF | dF | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-capentry-repair` | ERCOT | 2026-08-30T23:43 | `dcbd3b95` | 218 | 206 | **KT** | **KT** | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-c1joint-control` | ERCOT | 2026-08-31T01:14 | **`28cef350`** | 218 | 208 | dF | dF | dpipe | dT | dT | drein | KF |
| `ercot-…-t1h-c1joint-arm` | ERCOT | 2026-08-31T01:30 | `0490af52` | 218 | 207 | dF | dF | dpipe | dT | dT | drein | KF |
| **`ercot-…-t1h-d4m`** | ERCOT | 2026-08-31T17:08 | **`f061b264`** | 218 | 206 | **dT** | **dT** | dpipe | dT | dT | drein | KF |
| `ffr3v/miso-entry-diag` | MISO | 2026-08-04T13:21 | **`ca36ba26`** | 127 | 123 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4b/ctl` | MISO | 2026-08-04T16:17 | **`ca36ba26`** | 128 | 123 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4c/miso-ptcwindow-control` | MISO | 2026-08-04T16:42 | `18688555` | 128 | 123 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4b/gate` | MISO | 2026-08-04T16:48 | **`27597e34`** | 128 | 122 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4c/miso-ptcwindow-treatment` | MISO | 2026-08-04T17:08 | **`ca36ba26`** | 131 | 124 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4b/wire` | MISO | 2026-08-04T17:19 | **`ca36ba26`** | 128 | 123 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr4b/both` | MISO | 2026-08-04T17:39 | **`27597e34`** | 128 | 122 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-…-ffr3vfix-before` | MISO | 2026-08-09T00:47 | **`d1459d48`** | 150 | 141 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-…-ffr3vfix-after` | MISO | 2026-08-09T01:06 | **`d1459d48`** | 150 | 141 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-…-ffr5eh-control` | MISO | 2026-08-09T04:00 | **`42985ca8`** | 154 | 143 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-…-ffr5eh-armed` | MISO | 2026-08-09T04:19 | `0dc92a27` | 155 | 142 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2023-2025-t1ff-armr-fh4` | MISO | 2026-08-10T06:19 | `e95ffde7` | 159 | 149 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2023-2025-t1ff-armk-fh4` | MISO | 2026-08-10T06:29 | `d955f6ca` | 159 | 148 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2021-2025-t1ff-armr-fh5` | MISO | 2026-08-11T09:41 | **`42985ca8`** | 165 | 156 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2021-2025-t1ff-armk-fh5` | MISO | 2026-08-11T10:00 | `935ba4b2` | 165 | 155 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2031-2035-armed-default` | MISO | 2026-08-11T19:28 | `9337e005` | 165 | 159 | —F | —F | dpipe | dT | dT | drein | KF |
| `miso-2026-2030-s123-verify` | MISO | 2026-08-31T01:14 | `587dc5b3` | 218 | 212 | dF | dF | dpipe | dT | dT | drein | KF |
| `neiso-2023-2025-t1ff-armr-fh4` | NEISO | 2026-08-10T06:06 | `326cbab4` | 159 | 151 | —F | —F | dpipe | dT | dT | drein | KF |
| `neiso-2023-2025-t1ff-armk-fh4` | NEISO | 2026-08-10T06:10 | `424eff25` | 159 | 150 | —F | —F | dpipe | dT | dT | drein | KF |
| `neiso-2021-2025-t1ff-armr-fh5` | NEISO | 2026-08-11T08:35 | `968729ac` | 165 | 158 | —F | —F | dpipe | dT | dT | drein | KF |
| `neiso-2021-2025-t1ff-armk-fh5` | NEISO | 2026-08-11T08:42 | `961bf0c6` | 165 | 157 | —F | —F | dpipe | dT | dT | drein | KF |
| `neiso-2021-2025-realized-k99` | NEISO | 2026-08-19T06:49 | `b50062a6` | 181 | 176 | —F | —F | dpipe | dT | dT | drein | KF |
| `neiso-…-mystic-rescore` | NEISO | 2026-08-22T05:52 | `e118e887` | 196 | 190 | —F | —F | dpipe | dT | dT | drein | KF |
| `ff-t1f-s4hydro/neiso` | NEISO | 2026-08-30T18:21 | **`9a7f68fc`** | 211 | 207 | —F | —F | dpipe | dT | dT | drein | KF |
| `ff-t1f-s4hydro/neiso-control` | NEISO | 2026-08-30T18:29 | **`9a7f68fc`** | 211 | 207 | —F | —F | dpipe | dT | dT | drein | KF |
| **`neiso-2023-2027-crossover-capxd14`** | NEISO | 2026-08-30T20:45 | **`07e416f3`** | 215 | 207 | **—F** | **—F** | dpipe | dT | dT | drein | KF |
| `ff-t1f-s4b-ara/neiso` | NEISO | 2026-08-30T22:15 | **`9a7f68fc`** | 218 | 213 | —F | —F | dpipe | dT | dT | drein | KF |
| `ff-t1f-s4b-ara/neiso-control` | NEISO | 2026-08-30T22:24 | **`9a7f68fc`** | 218 | 213 | —F | —F | dpipe | dT | dT | drein | KF |
| `ff-t3-neiso-golden/bau` | NEISO | 2026-08-31T03:18 | `a4b11ef4` | 218 | 215 | dF | dF | dpipe | dT | dT | drein | KF |
| **`neiso-2023-2027-crossover-rcrepair`** | NEISO | 2026-08-31T04:55 | **`07e416f3`** | 218 | 212 | **dT** | **dT** | dpipe | dT | dT | drein | KF |
| `fc6/arms/carbon25` ⚠ | NEISO | 2026-08-31T17:41 | `7924eccc` | 218 | 213 | KF | KF | dpipe | dT | dT | drein | KF |
| `fc6/arms/base` ⚠ | NEISO | 2026-08-31T18:03 | `0365174a` | 218 | 213 | KF | KF | dpipe | dT | dT | drein | KF |
| `fc6/arms/gasup150` ⚠ | NEISO | 2026-08-31T18:15 | `13f93577` | 218 | 213 | KF | KF | dpipe | dT | dT | drein | KF |
| `fc6/arms/gaspm5` ⚠ | NEISO | 2026-08-31T18:37 | `1de43201` | 218 | 213 | KF | KF | dpipe | dT | dT | drein | KF |
| `nyiso-2023-2025-t1ff-armr-fh4` | NYISO | 2026-08-10T06:16 | `90c7a76c` | 159 | 151 | —F | —F | dpipe | dT | dT | drein | KF |
| `nyiso-2023-2025-t1ff-armk-fh4` | NYISO | 2026-08-10T06:22 | `30eedfd2` | 159 | 150 | —F | —F | dpipe | dT | dT | drein | KF |
| `nyiso-2021-2025-t1ff-armr-fh5` | NYISO | 2026-08-11T08:54 | `02154078` | 165 | 158 | —F | —F | dpipe | dT | dT | drein | KF |
| `nyiso-2021-2025-t1ff-armk-fh5` | NYISO | 2026-08-11T09:06 | `cad3a795` | 165 | 157 | —F | —F | dpipe | dT | dT | drein | KF |
| `nyiso-2026-2030-extcap-capxd2` | NYISO | 2026-08-25T01:48 | `fdd84d51` | 205 | 202 | —F | —F | dpipe | dT | dT | drein | KF |
| `nyiso-2023-2027-crossover-capxd10` | NYISO | 2026-08-30T18:23 | `7323dc2d` | 211 | 204 | —F | —F | dpipe | dT | dT | drein | KF |
| `ffr-sa-smoke/pjm-off` | PJM | 2026-08-04T02:22 | `c5054dc0` | 121 | 119 | —F | —F | dpipe | dT | dT | drein | dT |
| `ffr-sa-smoke/pjm-mid` | PJM | 2026-08-04T02:32 | `ced93433` | 121 | 118 | —F | —F | dpipe | dT | dT | drein | dT |
| `pjm-2023-2025-t1ff-armr-fh4` | PJM | 2026-08-10T07:00 | `69fdb766` | 159 | 151 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-2023-2025-t1ff-armk-fh4` | PJM | 2026-08-10T07:16 | `baa01738` | 159 | 150 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-2021-2025-t1ff-armr-fh5` | PJM | 2026-08-11T10:19 | `d41445ea` | 165 | 158 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-2021-2025-t1ff-armk-fh5` | PJM | 2026-08-11T10:38 | `d67ed72d` | 165 | 157 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-…-realized-verified-exits` | PJM | 2026-08-22T05:59 | `4c2c7907` | 196 | 190 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-…-realized-exante-control` | PJM | 2026-08-22T06:14 | **`f9d5d795`** | 196 | 191 | —F | —F | dpipe | dT | dT | drein | KF |
| `pjm-2026-2030-s6-ledger` | PJM | 2026-08-31T00:40 | `31a19d81` | 218 | 215 | dF | dF | dpipe | dT | dT | drein | KF |

Bold key = shared with at least one other committed run. ⚠ = key not reproducible from the run's
own committed config (§4.4). `pjm-2021-2025-realized-k162` also carries `f9d5d795106d9c74` in its
sidecar but has no committed `run_config.json`, so it is not in this table.

### 3.1 What the table says in aggregate

- **98 / 98 runs are exposed** — every one drops at least one flipped field.
- Per field, runs whose key does **not** encode it: `entry_rate_limits` 98,
  `entry_commissioning_lag` 98, `net_cone_forward_escalation` 98, `retirement_rule` 97
  (only `ffr3q3-legacy` hashes it, at an explicit `'legacy'`), the R-A pair 93 each,
  `forecast_xyear_warmstart` 6.
- **On the R-A pair specifically:** 91 runs pre-date the 2026-08-31T02:37:43Z flip and 7 post-date
  it. Of the 91, **90 do not encode the pair**; the sole exception is
  `ercot-…-t1h-capentry-repair`, which passed both **explicitly** and therefore hashed distinctly
  — exactly as `cache.py`'s R-A epoch entry predicted ("the inverse still holds and stays useful").
  Of the 7 post-flip runs, **2 land on a key a pre-flip record already occupies** (§4).

---

## 4. THE COLLISIONS

### 4.1 `f061b2646bfaac8b` — ERCOT, the known-true positive (method check)

| | `d12c-armed` | `d4m` |
|---|---|---|
| solved | 2026-08-30T22:48Z | 2026-08-31T17:08Z |
| `storage_entry_availability_gate` | **False** (dropped: was the default) | **True** (dropped: is the default) |
| `storage_entry_cost_normalized_rank` | **False** (dropped) | **True** (dropped) |
| every other of 765 fields | identical | identical |
| recorded key | `f061b2646bfaac8b` | `f061b2646bfaac8b` |

The charter's method check: **found, independently, by the same procedure that found everything
else.** Nothing about this pair was seeded into the search.

Quantifying the time-dependence directly: `d12c-armed`'s own committed config, re-hashed under
**today's** defaults, gives **`4705f4cc56949fd0`** — not the `f061b2646bfaac8b` it recorded. The
same config has two keys depending on the day it is hashed, and the key it recorded now belongs
to the opposite posture.

### 4.2 `07e416f3f8072e7c` — NEISO, NEW in this lane

| | `neiso-2023-2027-crossover-capxd14` | `neiso-2023-2027-crossover-rcrepair` |
|---|---|---|
| solved | 2026-08-30T20:45Z | 2026-08-31T04:55Z |
| `storage_entry_availability_gate` | **absent from the schema** (field did not exist ⇒ unarmed) | **True** (dropped: is the default) |
| `storage_entry_cost_normalized_rank` | **absent** ⇒ unarmed | **True** (dropped) |
| every field present in both | identical | identical |
| recorded key | `07e416f3f8072e7c` | `07e416f3f8072e7c` |

This is the **absent-vs-armed-default** form, and it is nastier than §4.1 in one respect: there is
no differing value to notice. A reader diffing the two `run_config.json` files sees only "the
newer one has two extra fields", which looks like ordinary schema growth. It is a posture change.

**It also means the defect is not ERCOT-specific.** `results/cache.py`'s R-A epoch entry named
one bundle by construction (`ercot-…-t1h-capentry-control`); the actual reach is at least two
ISOs, and the second instance is a crossover run, not a T1-H.

### 4.3 `28cef3500ec1fd9e` — the D4-I3 §5.1 group: RULED OUT as this defect

Seven committed runs share this key (`refresh`, `t1h-control`, `fwdexp-control`, `d11r-control`,
`d12c-control`, `capentry-control`, `c1joint-control`; D4-I3 §5.1 saw five of them, because two
have no sidecar). Measured here:

- **No flip-field divergence.** Four predate the R-A fields; three carry them at `False`. All
  seven are effectively **unarmed on every one of the seven flipped fields**.
- **No differing common field** at all across the seven.
- **Seven distinct cache roots**, so no bundle reuse between them was possible.

So D4-I3 §5.1's disagreement (2023 slack 0.02 % vs 0.01 %, LW price $100.4 vs $86.1, three
distinct CO2 quantities) **cannot be explained by the mechanism D4-M demonstrated**, and it
cannot be explained by one of these runs reading another's bundle. Within R-5, that removes the
default-flip route and the inter-run-reuse route; what remains for candidate (i) is a
non-`ScenarioConfig` behavioral change between the 2026-08-22 `refresh` solve and the
2026-08-24+ solves (the *other* half of the epoch hazard, the one `cache.py`'s policy paragraph
opens with), or D4-I3's candidate (ii), a scorer change. **Adjudicating between those two is
still R-5's, and is not done here.**

### 4.4 The inverse failure: one posture, two keys

`results/ff-t3-neiso-golden/bau/run_config.json` and
`results/ff-t3-neiso-golden/bau/fc6/arms/base/run_config.json` carry **byte-identical
`scenario_config` dicts (all 765 fields)** and different keys — `a4b11ef4aaa1be35` vs
`0365174ab16cc318`. All four fc6 arms' keys are unreproducible from their own committed configs
at any of the 170 main-line snapshots in the window (the other 94 of 98 reproduce exactly). Their
`run_config.json` records `dirty: true` with 2,963 changed files, though none under `src/`.

Whatever the cause, the consequence for this lane's question is direct: **`cache_key` /
`cache_epoch` is non-identifying in both directions today** — it maps two postures to one key
(§4.1, §4.2) and one posture to two keys (here). Routed as a provenance gap, not adjudicated.

### 4.5 The eleven other shared-key groups

`816031a3` (7 ERCOT), `9a7f68fc` (4 NEISO), `ca36ba26` (4 MISO), `6a824992` (3 ERCOT),
`27597e34`, `35b0a89b`, `3d3e836a`, `408f9199`, `42985ca8`, `49eac64f`, `d1459d48` (2 each).
**None shows posture divergence**: within each group every field present in all members is equal,
and every flipped field is at one effective value. They are the designed case — a run predating a
field and a run carrying it default-off. 43 of the 98 runs sit on a shared key; 4 of those 43 are
in the two divergent pairs.

---

## 5. CONSEQUENCE, per pair, stated honestly

A shared key proves a wrong result **could** have been served. It does not prove one **was**. The
discriminator is the cache root: `cache.CACHE_ROOT` is redirected per run
(`run_capacity_hindcast.py:1841`, `cachemod.CACHE_ROOT = args.out_dir`), and a bundle is only
reachable at `<CACHE_ROOT>/<ISO>/<key>`.

**Measured: all 99 keyed run records used a distinct cache root — 99 distinct
(root, key) pairs for 99 runs.** So:

| pair | verdict |
|---|---|
| `f061b264…` — `d12c-armed` / `d4m` | **Collides; re-solved anyway.** Separate roots (`results/hindcast/…-d12c-armed` vs `…-d4m`). D4-M additionally attests `results/ERCOT/` was empty in its container. **No cached result was served.** |
| `07e416f3…` — `capxd14` / `rcrepair` | **Collides; re-solved anyway.** Separate roots (`results/hindcast/neiso-2023-2027-crossover-capxd14` vs `…-rcrepair`). **No cached result was served.** |

**Two limits on that conclusion, stated rather than buried.** (a) A distinct out-dir rules out one
committed run reading *another committed run's* bundle. It does not rule out a run reading a
**stale, uncommitted** bundle left in its *own* out-dir by an earlier attempt in the same
session; nothing in the committed record can see that. (b) It says nothing about any operator
cache outside this container.

**And the protection is incidental, not designed.** `--out-dir` is a required argument whose
value is the operator's choice, and `run_capacity_hindcast.py`'s own usage block suggests
posture-independent names (`--out-dir results/hindcast/ercot-2021-2025-realized`). The convention
that has held so far — one directory per *run id*, which encodes the arm — is what has kept the
program clean. A single re-used out-dir across an R-A-style flip converts every collision in §4
from "reader hazard" into "wrong dispatch served, silently". That is the actual risk this defect
carries forward.

---

## 6. Does a committed verdict rest on a collided entry? — YES, in NEISO

Searched `frontend/data/forecast/ff-verdicts.json`, `program-status.json` and
`frontend/data/hindcast/invariant-failures.json` for the four runs in the two divergent pairs.

| surface | finding |
|---|---|
| `ff-verdicts.json` → **`neiso-t1x`** | The committed FF-2D verdict. Per `program-status.json` `/neiso_rc_repair/verdict_movement` it is **re-keyed to `neiso-2023-2027-crossover-rcrepair`**, with `capxd14` preserved as `neiso-t1x-pre-rcrepair`. Both runs are the `07e416f3…` collision pair. `neiso-t1x-pre-d5r` is also `capxd14`. |
| `program-status.json` → NEISO `gate/c_crossover_gap/detail` | The §2.1b gate leg is declared satisfied by "NEISO's FIRST-EVER T1-X crossover run `neiso-2023-2027-crossover-capxd14`" — named. |
| `program-status.json` → NEISO `blocking_rows[3]` | The T1-X FC-4 measurement row, from the same two runs. |
| `program-status.json` → ERCOT `blocking_rows[1]`, `/d4m_ercot_t1h/*`, `/d4i3_ercot_slack/*` | Board rows citing `d4m` and `d12c-armed`. No FF-2D verdict. |
| `invariant-failures.json` | Declares `d12c-armed` and `d4m` I3 rows. Records, not verdicts. |
| `ff-verdicts.json` for the ERCOT pair | **No entry.** No FF-2D verdict rests on `d12c-armed` or `d4m`. |

**Reported, not acted on, per the charter.** Nothing in this finding says any of those verdicts is
wrong: §5 establishes that both NEISO runs solved fresh, so the verdict was scored on the
dispatch its own config produced. What is compromised is the *provenance claim* — the
`cache_epoch` / `cache_key` field can no longer establish that two NEISO forecast runs share a
config identity, and `capxd14` and `rcrepair` stamp the same one while differing in posture.
**Whether the NEISO gate leg or the `neiso-t1x` verdict needs any re-statement is the NEISO
crossover lane's question and the director's, not this lane's.**

---

## 7. REPAIR OPTIONS, priced — NOTHING LANDED

Costs are measured, not estimated: each option was implemented against the live `cache_key`
algorithm and applied to every committed config.

Baseline population for cost: **99 keyed forecast run records**, **63 committed backcast
`run_config.json`** (all six ISOs' calibration lane, keeper configs among them), **132 distinct
16-hex keys / 164 bundle directories committed under `results/`**.

A note the ledger already makes and this section keeps: **committed bundles and sidecars are
files, not cache lookups** — no option below deletes or invalidates a committed artifact. What a
key move costs is (i) every on-disk cache bundle becomes unreachable (a replay = a full re-solve),
and (ii) every committed `cache_key` stops being reproducible from its own config, which is the
last remaining identity handle on these runs.

### (a) Include the optional fields unconditionally — delete the drop loop

| | |
|---|---|
| Correctness | **Complete.** No field is ever omitted; two configs share a key iff they are equal. Fixes both directions of §4. |
| Keys moved, forecast | **99 / 99** |
| Keys moved, backcast | **63 / 63** — including every keeper's config. Default forecast `603c2498bf71d21d` → `58e023e59ee6c18d`; default backcast `e027bc248c93c835` → `1c28a2c70fe4754b`. |
| Committed cache entries orphaned | **all 164 bundle dirs / 132 keys** (files retained, addresses dead) |
| Recurring cost | **High and permanent.** Removes the mechanism that keeps a key stable when a default-off field is *added*. The schema grew 604 → 765 fields in five weeks; under (a) each of those 161 additions would have re-keyed every config in the program. This is precisely the failure `check_cache_key_registration.py` exists to prevent, re-armed. |
| Verdict | Correct but the most expensive option, and it trades one silent failure for a loud, recurring one. |

### (b) Fold a defaults-snapshot hash into the key

| | |
|---|---|
| Correctness | **Complete for the flip hazard**, and it additionally catches nothing else (a non-field behavior change still moves no key). |
| Keys moved now | **99 / 99 forecast + 63 / 63 backcast** (the snapshot is new to every key). |
| Recurring cost | **Worse than (a).** The key then moves whenever *any* registered field's default moves, relevant to that config or not. Measured: 4 flip events in the 5-week window ⇒ ~4 program-wide invalidations per 5 weeks, most of them irrelevant to most configs. |
| Verdict | **Not recommended.** Strictly dominated by (a) on churn and by (b′) on precision. |

### (b′) Freeze the drop comparison against the DECLARED default, ledger append-only

Stop reading the live default; drop a field only when it equals the value recorded for it in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, and make that ledger **append-only** (a flip adds a new
declaration; it does not overwrite the old). A post-flip config at the new default then carries a
non-default value, enters the hash, and gets its own key. **This is the "deeper fix" already
recorded as the open follow-up** in `scenarios.py`'s own ledger comment and
`docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md` §4.

Two variants, and they differ enormously in price:

| variant | correctness | keys moved now | note |
|---|---|---|---|
| **(b′-1) re-baseline at today's declared values** | Prevents every **future** flip collision. Does **not** disambiguate the two existing collisions. | **0 forecast, 0 backcast** — declared == live today, so the change is a no-op on every current key. | Costs nothing to land. Landing it *before* the next flip is what makes it worth anything. |
| (b′-2) retroactive to each field's registration-time default | Prevents future and retroactively separates the seven flipped fields. | **98 / 99 forecast, 63 / 63 backcast** — dominated by `forecast_xyear_warmstart`, registered at `False` and live `True`, which every config now carries. | Same order of cost as (a), without (a)'s recurring penalty. |

### (c) Keep the drop; refuse a cache hit whose stored config differs

`save_result` already writes the full resolved config as `config.yaml` beside every bundle, and
`get_cache_path` already carries a refusal precedent (`assert_cache_key_uncontaminated`, owner
decision D-11). The seam is one line: `runner.py:2263`'s `is_cached(iso, cache_key, year)` gains
a config-equality test against `get_config_path(...)`.

| | strict (refuse on any difference) | **(c′) refuse on any differing common field, OR on a field absent from the stored config that does not hold its registration-time default** |
|---|---|---|
| Correctness | Complete for reuse; a wrong bundle can never be served. | Complete for reuse: catches §4.1 (differing common field) **and** §4.2 (absent vs armed default). |
| Keys moved | **0** | **0** |
| Committed cache entries invalidated | **0** | **0** |
| Forced re-solves | Every would-be hit where the schema has grown at all — i.e. a bundle is reusable only within roughly one schema generation (days, at the observed 161 fields / 5 weeks). Of the 14 shared-key groups, strict refuses **14/14**, only 2 of which are true positives. | Refuses the **2** true-positive groups; permits the 12 designed-case groups. |
| Does not fix | Provenance: two runs still stamp one `cache_epoch` (§4.1/§4.2), and one posture can still carry two keys (§4.4). | Same. |

### Recommendation to the owner (a recommendation, not a decision)

**(c′) + (b′-1), together, cost zero keys and zero re-solves.** (c′) makes a wrong serve
mechanically impossible from the moment it lands, at the seam that already refuses contaminated
keys; (b′-1) makes the key identifying from the *next* flip onward. Neither touches a committed
artifact, a keeper, or any board surface. What they deliberately do **not** do is retroactively
separate the two existing collisions — that needs (a) or (b′-2), and paying for it is the owner's
call, since the measured price is every on-disk cache in both lanes, keepers included.

If the owner wants the retroactive separation, **(b′-2) is the better buy than (a)**: same
one-time cost, without permanently re-arming the add-a-field-re-keys-everything failure.

---

## 8. Governance and scope

- **Zero solves.** No LP was built or run. Every figure is computed from committed
  `run_config.json` / sidecars and from `scenarios.py` blobs read out of git history.
- **NO REPAIR LANDED** (charter, §7). No change to `cache_key`, `_CACHE_KEY_OPTIONAL_FIELDS`,
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, `results/cache.py`, `runner.py`, or any guard script.
- **No bundle purged, re-solved, re-scored or deleted.** No `results/` file touched.
- **Rule 28 `[R-MECH-MATRIX]` NOT TRIGGERED** — no mechanism proposed or tested, no
  `ScenarioConfig` field added or moved. **No matrix shard edited.**
- **No verdict, board, keeper, shard or marker edit.** §6 reports a verdict linkage and routes it;
  it changes nothing. Backcast namespace untouched; the 63 backcast configs were read only, and
  appear here solely as a cost denominator in §7.
- **Rule 22 `[R-HOLDOUT]`:** no holdout year solved, scored or registered. Nothing read here is
  year-scoped.
- **Rule 25 `[R-ISO-SCOPE]`:** the finding spans ISOs because the defect does; no ISO-scoped
  parameter, file or cell was written.
- **Rule 27 `[R-PUSH]`:** this session adds exactly one new file. No existing source file was
  edited, so no ≥300-line file was rewritten; nothing to blob-verify beyond this document.
- **No GitHub Actions workflow added.**
- **Container note:** the clone was deepened with `git fetch --filter=blob:none --unshallow` to
  reach the 170 historical `scenarios.py` blobs (13,929 commits, blobless). Read-side git calls
  ran under `GIT_NO_LAZY_FETCH=1` per CLAUDE.md; the only blobs downloaded are `scenarios.py`
  versions, deliberately.

---

## 9. Routed to the director — reported, not acted on

1. **The NEISO T1-X verdict linkage (§6).** `neiso-t1x`, `neiso-t1x-pre-rcrepair`,
   `neiso-t1x-pre-d5r` and NEISO's `gate/c_crossover_gap` all rest on runs in the `07e416f3…`
   collision pair. Nothing here shows the verdict is wrong; the *provenance* claim is what breaks.
   Belongs to the NEISO crossover lane.
2. **R-5 is narrowed, not closed (§4.3).** The `28cef3500ec1fd9e` divergence is **not** this
   defect and **not** inter-run bundle reuse. The remaining candidates are a non-`ScenarioConfig`
   behavioral change between 2026-08-22 and 2026-08-24, or a scorer change.
3. **`cache_epoch` should stop being quoted as a config-identity field** until a repair lands. It
   is non-identifying in both directions today (§4.1, §4.2, §4.4).
4. **Out-dir naming is the live control (§5).** The only thing standing between this defect and a
   silently-wrong dispatch is the convention of one `--out-dir` per run id. It is undocumented,
   and `run_capacity_hindcast.py`'s own usage examples show posture-independent directory names.
   Cheapest possible mitigation, independent of §7: fix the usage examples and say the rule out
   loud.
5. **Four fc6 run records carry unreproducible keys (§4.4)**, and one pair carries identical
   configs under two keys. Records defect in the NEISO T3 golden lane's registration path.
6. **Three registered sidecars have no keyed `run_config.json`** (`{ercot,miso,pjm}-2023-2027-crossover-ffr2a`,
   2026-08-02, the `run-config-debt` reconstructions). Their exposure is not assessable from
   committed artifacts.
