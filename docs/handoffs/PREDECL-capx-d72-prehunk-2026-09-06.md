# PRE-DECLARATION — capx D72: the pre-hunk re-solve campaign, scoped by a zero-LP inertness proof

**Lane:** capx D72 — the PRE-HUNK RE-SOLVE CAMPAIGN routed by capx D60-R3
(`FINDING-capx-d60-2026-09-05.md` §8-blast-radius / §9). **Branch:**
`claude/capx-d72-prehunk-resolves`, fresh off `origin/main`, rebased to **`8bc588a2`** before
any solve. **Pushed before any solve.**

**The object.** capx D55 (`da007e0f`, PR #4747) replaced key 1 of the reliability-floor
retention sort in `retirements.py::_floor_retention_merit` — the per-unit quotient
`(FOM × mult × pmax × 1000) / (pmax × fraction)` — with the class constant
`(FOM × mult × 1000) / fraction`. Equal in exact arithmetic, **not** in IEEE-754, so it
re-orders the retention sort. It is an intentional repair of D32 §3.2 and **this lane does not
touch it.** Its consequence is that a forecast bundle solved before it no longer necessarily
describes what HEAD produces from its own recipe. D60-R3 classified all 33 committed bundles
and re-solved three; **seven bare keys remain PRE-hunk** and are this lane's charter.

---

## 0. State at start — two environment defects found and repaired BEFORE any measurement

Both cost D60-R3 real time; both were present again and are recorded rather than assumed away.

1. **The stack was BELOW nothing and ABOVE nothing — it was ABSENT.** The container's
   `pip install -r requirements.txt` aborts on the Debian-owned PyYAML
   (`Cannot uninstall PyYAML 6.0.1, RECORD file not found`) and leaves the whole scientific
   stack uninstalled (`import numpy` → `ModuleNotFoundError`). Repaired with
   `pip3 install --ignore-installed PyYAML -r requirements.txt`. **Verified at the pins:**
   python 3.11.15, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0,
   pydantic 2.13.4 — byte-for-byte the stack the committed controls record, which is what
   D65 §3b's drift argument rests on.
2. **The clone was SHALLOW** (183→666 commits), so bundle `git.sha` values did not resolve.
   Deepened to **3,522** first-parent commits.

**Interpreter note.** `uv run` builds an empty `.venv` in this container (`--no-sync` →
`ModuleNotFoundError: numpy`), so every command below runs under the system `python3`, which
carries the verified pins. This is D60-R3's own precedent (pip-forced pins), not a deviation.
The stray `.venv` uv created was deleted.

---

## 1. STOP 1 — every one of the seven keys resolved through the harness path at HEAD

Resolved exactly as D60 Addendum §A.2 / §R2.2 / §R3.2 resolve them — config construction only,
no fleet build, no solve:
`run_full_horizon.reference_config(iso, 2026, 2030, False, golden_posture=True)` →
`apply_iso_scenario_defaults` → `cache_key()` for t1f;
`run_capacity_hindcast.build_config(iso, 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True)` → same → `cache_key()` for t1h.

| bare key | pin (D60 §R3.2) | resolved at `8bc588a2` | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | `0c3e9cd5b5993bdf` | **HIT** |
| `neiso-t1f` | `18515067bf4d2fbe` | `18515067bf4d2fbe` | **HIT** |
| `ercot-t1h` | `82b27751be747552` | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` | `7da58199acd362ee` | **HIT** |
| `miso-t1h`  | `687bd75f2828bea1` | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` | `6e70a637b3465542` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` | `f3988df3068020d1` | **HIT** |

**Seven of seven.** Resolved once at `c5786dfa` and again after the rebase to `8bc588a2`; the
rebase's four commits touch **neither `src/market_sim/` nor `scripts/`**
(`git diff --stat c5786dfa..8bc588a2 -- src/market_sim scripts/` → empty), so the keys hold by
construction as well as by measurement. **STOP 1 does not fire.**

---

## 2. THE SCOPE DECISION PUT TO THE DIRECTOR — four of the seven keys are PROVABLY INERT at zero LP

The charter asked whether the t1h keys "may be INERT and provable at zero LP by replaying the
D55 instrument rather than re-solving". **They are — and so is one of the two t1f keys.** The
answer is stronger than the charter anticipated in one direction and weaker in another, and
both halves are stated at full magnitude.

### 2.1 The instrument, and why it is a PROOF rather than an indication

D55's own probe (`scripts/probes/_capxd55_retention_replay.py`, deleted at `677b605a` under the
delete-not-archive discipline, recovered here from `27ab11b1`) established the decisive
signature in its D46 row: *"the floor exhausted the eligible set (every failing unit retained);
the retention ORDER is irrelevant"* — `n_eligible 1489 / n_capped 1489 / n_decided 0`.

That generalises to a two-sided proof, read directly off the committed evolution ledgers. Read
from the code at HEAD, `_apply_reliability_floor` (`retirements.py:2385`) is a greedy loop over
`sorted(eligible, key=_floor_retention_merit)` that `break`s the moment the requirement clears;
the admission-cap call site (`retirements.py:2656`, D65 §3d's un-logged one) then emits
`entry_capped` for every unit the floor un-retired and `decided` for every unit it did not
(`retirements.py:2670–2675`). Therefore, **per screen year**:

| observed in the committed ledger | what the floor did | is the ORDER observable? |
|---|---|---|
| `entry_capped == 0` | un-retired **nothing** (returned at the guard, or every unit `continue`d) | **NO** — the outcome set is empty under every order |
| `decided == 0` (and `capped > 0`) | un-retired **everything** — exhausted the eligible set | **NO** — the outcome set is the whole set under every order |
| both `> 0` | broke mid-loop | **YES** — the order selects the boundary |

and, for the two *logged* call sites (`:2704`, `:3666`), a `floor_retained == []` means those
sites un-retired nothing, which is order-invariant on the same argument.

**The proof composes across the horizon by induction.** If year *Y*'s floor outcome is
order-invariant, the fleet entering *Y+1* is identical under both key forms, so *Y+1*'s
eligible set is identical and its own row can be read the same way. A key is therefore
**provably inert** iff *every* year of its committed bundle is order-invariant — no LP.

**Two guards against a vacuous proof, both checked:**
- `floor_retained` is a **live** field, not one that is always empty: 3 of 416 committed
  evolution ledgers carry a non-empty one (`neiso-…-t1h-d37-armed` 2024/2025,
  `neiso-…-t1h-d46` 2025). An empty one is evidence, not an artifact.
- **Nothing else consumes the merit ORDER.** `_floor_retention_merit` is referenced at exactly
  three points in live code: the sort (`:2462`), the log's own *values* (`:2477`, not its
  order), and a re-export in `capacity_evolution/__init__.py` that no module imports.

### 2.2 The census — every committed bundle of all seven keys, every year

`capped` / `decided` are raw `pipeline_events` counts (D55's probe filtered to units whose
attributes it could rebuild — 1489 of 1497 in MISO 2022 — so the raw count is the conservative
one and yields the same verdict).

| key | committed bundle (cache key) | per-year `capped`/`decided`/`floor_retained` | verdict |
|---|---|---|---|
| **`ercot-t1f`** | `ff-t1f-d50/ercot` (`0c3e9cd5b5993bdf`) | 26: 0/0/0 · 27: **377/0**/0 · 28: **11/0**/0 · 29: **1/0**/0 · 30: **1/0**/0 | **INERT** — floor exhausts every year it is consulted |
| `neiso-t1f` | `ff-t1f-d50/neiso` (`18515067bf4d2fbe`) | 26: 0/0/0 · **27: 292/30**/0 · 28: 0/0/0 · 29: 0/0/0 · 30: 0/0/0 | **NOT INERT** — 2027 breaks mid-loop |
| **`ercot-t1h`** | `…-t1h-d46` (`67d5dcc1ada2e2df`) | 21–25: **0/0**/0 every year (zero pipeline events at all) | **INERT** |
| **`caiso-t1h`** | `…-t1h-d46` (`2c8cc7d19ccaed4c`) | 21–25: **0/0**/0 every year | **INERT** |
| `miso-t1h` | `…-t1h-d53-sectorgate-d51ratio` (`6ea92547eaa62559`) | 21: 0/0/0 · **22: 405/5**/0 · 23: 385/0/0 · 24: 415/0/0 · 25: 0/0/0 | **NOT INERT** — 2022 breaks mid-loop |
| **`nyiso-t1h`** | `…-t1h-d52-devintage` (`911371a8cf23d5c3`) | 21–25: **0/0**/0 every year | **INERT** |
| `neiso-t1h` | `…-t1h-d45r` (`d6c0137e37bf3200`) | 21: 0/0/0 · 22: 0/22/0 · 23: 0/0/0 · **24: 187/52**/0 · 25: 0/0/0 | **NOT INERT** — 2024 breaks mid-loop |

**The instrument is validated on both a positive and a negative control, neither of which this
lane chose after the fact:**
- **Negative (known-inert):** `miso-…-t1h-d46`, the bundle D55 itself measured byte-identical,
  reads 2022 `1497/0`, 2023 `948/0` — "retained all", exactly D55 §2.1's row.
- **Positive (known-moving):** `neiso-t1f` is the ONE bundle with an independently measured
  magnitude (D65 §3c: 7 rows, −124.92 MW gas_cc in 2027). The census flags **2027 and only
  2027** as observable, and its 2026 / 2028–2030 rows read inert — which is precisely where
  D65 measured byte-identity ("the 2026 result parquet is byte-identical across all 12
  columns"). The instrument fires where the drift is and nowhere else.

### 2.3 A CORRECTION to the §8-blast-radius residue table, recorded before it can be inherited

D60-R3's residue table annotates `miso-t1h` as **"(measured INERT by D55)"**. **That citation
is wrong**, and it is wrong in the unsafe direction.

D55 measured the **`miso-2021-2025-realized-t1h-d46`** bundle inert (`eff2c890746ec966`;
§2.1's third row, `1489/1489/0`). The bare `miso-t1h` key does **not** point there — it points
at **`miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio`** (`6ea92547eaa62559`), a different
bundle on a different recipe. And D55 §2.3 measured *that* lineage — the D51-ratio arm — as the
case where the floor **does** release a suffix (477.4 MW committed; certain fixed-key release
278.6 MW, i.e. the released set CHANGES). The census above reproduces exactly that shape
(2022: 405 capped / 5 decided). **`miso-t1h` is the residue table's one mislabelled row: it is
not inert, and it is solved in this lane rather than waved through on the inherited note.**

### 2.4 What this buys, and what the director is asked to confirm

> **Four keys — `ercot-t1f`, `ercot-t1h`, `caiso-t1h`, `nyiso-t1h` — are proved inert against
> the D55 hunk on committed evidence alone, at zero LP.** Each earns a **RENAME-grade note**
> (a `scored_at_sha` disposition recorded against the committed bundle), **not** a solve.
> **Three keys — `neiso-t1f`, `miso-t1h`, `neiso-t1h` — are NOT provably inert and are solved.**

Three solves rather than seven. **The scope of the claim, stated so it is not over-read:** this
proves the **D55 hunk** cannot move these four bundles — that and nothing more. It is not a
claim that they reproduce at HEAD in general (other drift is out of this lane's charter), and
for the three t1h keys it is worth recording that their committed bundles were solved at cache
keys *older* than the bare key HEAD now resolves (e.g. `ercot-t1h` committed at
`67d5dcc1ada2e2df` vs the bare `82b27751be747552`) — a pre-existing recipe drift of the class
D60 §7 discloses for the t1x keys, **not** created here and **not** repaired here.

---

## 3. The expected FC rows per key, from its committed control

Read from each bundle's committed `forecast_verdict.json`. For the four inert keys these are
also the **post-lane** rows, unchanged by construction; for the three solved keys they are the
control the leg is graded against.

| key | determination | FC-1 | FC-2 | FC-3 | FC-4 | FC-5 | FC-6 | FC-7 | FC-8 | caveats | rubric / `scored_at_sha` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ercot-t1f` **(inert)** | HOLD | FAIL | FAIL | n/a | n/a | SKIPPED | SKIPPED | CAVEAT | PASS | FC-7 provenance & DOF | 1.0 / `9e48ff6820b0` |
| `neiso-t1f` **(solve)** | **PROMOTE** | PASS | PASS | n/a | n/a | SKIPPED | SKIPPED | PASS | PASS | — | 1.0 / `9e48ff6820b0` |
| `ercot-t1h` **(inert)** | HOLD | SKIPPED | n/a | FAIL | n/a | n/a | n/a | CAVEAT | SKIPPED | FC-7 provenance & DOF | 1.0 / `71d3f1a6e3c2` |
| `caiso-t1h` **(inert)** | HOLD | SKIPPED | n/a | FAIL | n/a | n/a | n/a | CAVEAT | SKIPPED | FC-7 provenance & DOF | 1.0 / `71d3f1a6e3c2` |
| `miso-t1h` **(solve)** | HOLD | SKIPPED | n/a | FAIL | n/a | n/a | n/a | CAVEAT | SKIPPED | FC-7 provenance & DOF | 1.1 / `36009c652a67` |
| `nyiso-t1h` **(inert)** | HOLD | SKIPPED | n/a | FAIL | n/a | n/a | n/a | CAVEAT | SKIPPED | FC-7 provenance & DOF | 1.0 / `881c11de24bb` |
| `neiso-t1h` **(solve)** | HOLD | SKIPPED | n/a | FAIL | n/a | n/a | n/a | CAVEAT | SKIPPED | FC-7 provenance & DOF | 1.0 / `0f22b42140e3` |

`neiso-t1f` is the lane's only **PROMOTE** and therefore the only key whose determination has
anywhere to fall. It is pre-declared below rather than hoped for.

---

## 4. The legs, in order

Rule 12 `[R-PARALLEL]`: **sequential**, never concurrent. Rebase **between** legs, never during
one (D60 §5.0e); each leg records `HEAD` before the solve and refuses to score or register if
`HEAD` moved during it. One blob-verified commit per leg, pushed as it lands.

### Leg 1 — `neiso-t1f` (the measured case) · ~11 min

```
python3 scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ff-t1f-d72/neiso
```

**Pre-declared.** Realized cache key **`18515067bf4d2fbe`** (STOP 4 if not). The 2027 ledger
lands on the **POST-hunk side**, to the digit:

| 2027 | rows | total MW | `reserve_margin` | `fleet_by_fuel_after.gas_cc` |
|---|---|---|---|---|
| PRE-hunk (committed, `9e48ff6`) | 33 | 2,369.81 | 0.045867 | 10,713.80312 |
| **POST-hunk (pre-declared)** | **40** | **2,244.89** | **0.050821** | **10,838.72120** |

Both rows are reproduced here from the committed ledgers themselves
(`ff-t1f-d50/neiso` and `ff-t1f-d65-ctl/neiso`), not copied from the charter. 2026 is
pre-declared **byte-identical** to the committed bundle (D65 §4.2). **Determination:** the FC
map is pre-declared **unchanged at PROMOTE** — the 2027 economic-exit set moves but FC-1/FC-2
are band criteria over the horizon, and D65 measured the seam as re-ordering rather than
re-selecting. **A determination move to anything other than PROMOTE is a STOP**, reported and
not registered as bare.

*(Recorded so it is not later mistaken for an oversight: `results/ff-t1f-d65-ctl/neiso` is
already a committed POST-hunk bundle at this exact key, so a Class-A rename onto it was
available. It is **refused**: it carries D65's basis `e5ac39f1b2a6`, it was never scored — it
has no `forecast_verdict.json` — and a rename is precisely the "complete as a rename,
incomplete as a re-measure" gap D60 §9 routed to this lane. The whole point is to re-measure.)*

### Leg 2 — `miso-t1h` · ~12–25 min

```
python3 scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 \
    --vintage 2020 --fuel-variant realized --entry-screen-diagnostics \
    --out-dir results/hindcast/miso-2021-2025-realized-t1h-d72
```

**Pre-declared.** Realized key **`687bd75f2828bea1`**. 2022 is the biting year; the released
set may change (D55 §2.3's construction predicts the release shrinking toward the CO2 tail of
the coal candidate set). **Determination pre-declared unchanged at HOLD**, FC-3 FAIL,
FC-7 CAVEAT.

### Leg 3 — `neiso-t1h` · ~12–25 min

```
python3 scripts/run_capacity_hindcast.py --iso NEISO --start-year 2021 --end-year 2025 \
    --vintage 2020 --fuel-variant realized --entry-screen-diagnostics \
    --out-dir results/hindcast/neiso-2021-2025-realized-t1h-d72
```

**Pre-declared.** Realized key **`f3988df3068020d1`**. 2024 is the biting year.
**Determination pre-declared unchanged at HOLD**, FC-3 FAIL, FC-7 CAVEAT.

Each leg: solve → `score_capacity_hindcast.py` (t1h) / the t1f scoring path →
`forecast_verdict.py --tier` → `register_forecast_run.py`, **after that leg's final rebase**.
Every prior is preserved at `<key>-pre-d72` via `register_forecast_run.VERDICT_MAP`
(preserve-then-overwrite); **no existing preserved baseline** (`-pre-d60`, `-pre-d53`,
`-pre-d46`, `-pre-d45r`, `-pre-d37` …) is overwritten.

---

## 5. STOPs

| # | STOP | disposition |
|---|---|---|
| 1 | any of the seven keys ≠ its pre-declared value | **not fired** at `8bc588a2` (§1, 7/7); re-read before each leg |
| 2 | a realized bundle key ≠ the pre-declared key for that leg | pending — checked per leg |
| 3 | a NEISO 2027 ledger matching **neither** the PRE side (33 / 2,369.81 / 0.045867 / 10,713.803) **nor** the POST side (40 / 2,244.89 / 0.050821 / 10,838.721) — a **SECOND hunk** | pending; D60-R3 §5.0d found no second hunk at its HEAD, and this lane's HEAD adds no `src/`+`scripts/` change over it |
| 4 | any determination moving where §3/§4 did not admit it | pending |
| 5 | an inert-key census row that disagrees with a re-read at HEAD | the four inert verdicts rest on committed ledgers + HEAD source; both are re-checkable at zero cost |

---

## 6. What this lane will NOT do, stated so it is not assumed

No keeper, no shard, no `complete`/`final` marker, no freeze, no default, no new
`ScenarioConfig` field, **no parameter value** (rule 21 `[R-DOF]`), and **no mechanism-matrix
cell** (rule 28 — this lane tests no mechanism; it re-measures existing recipes across a hunk
it does not touch). Rule 22: every solved year is 2021–2025 hindcast or 2026–2030 forecast
under `mode="forecast"`, no measured H1-2026 actual is touched. Rule 25: no ISO's value
identifies another's. The D55 hunk is **named and not touched**. The D65 §3d floor-diagnostic
gap (the `:2656` call site discarding its return — now `retirements.py:2656`, D65's `:2517`)
is **re-routed, not repaired here**; §2.1 records that this lane had to reconstruct from
`pipeline_events` precisely because that return is discarded.
