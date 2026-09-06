# FINDING — capx D73: D23's R1 guard already exists (capx-D26); the one gap is a zero-LP artifact route, and the archived `carbon25` P1 FAIL is a render-orphaned snapshot

**Session:** D73 (capacity-expansion track), branch `claude/capx-d73-fc6-p1-guard-iqepvu`.
**Date:** 2026-09-06. **HEAD at launch:** `a98a0310` (fresh off `origin/main`, 0 ahead / 0 behind).
**Charter:** pack §D73 + `FINDING-capx-d23-p1-carbon-sign-2026-09-01.md` §8 R1 +
`FINDING-capx-d72-2026-09-06.md` §5–§6.1. **ZERO LP held throughout:** no solve, no re-solve,
no registration, no board byte. Every number below is computed from committed
`run_config.json` files and read from committed source at HEAD.

**Headline, phase 0: the charter's build is already on `main`.** The string at
`scripts/check_forecast_invariants.py:880` is the body of `carbon_pair_premise` (L839), which
IS D23's R1 in substance — both halves, checker and scorer — landed by capx-D26 on
2026-09-01 (D26 finding §2 item 3), with the battery-side twin `carbon_ladder_premise`
(`scripts/run_driver_battery.py:1111`) and tests for both branches in all three consumers.
What D26 did NOT build is the route D23's R1 literally names — *"from each arm's COMMITTED
config"*: the premise can only be asked of the multi-GB cache directories (`--paired`), and
the artifact-mode entry point refuses P1 outright (L1166–1180). Phase 1 therefore builds
exactly that route and nothing else (§3). **The guard's live effect is nil**: the phase-0
table (§2.3) has **zero INVERTED live rows** — every committed `paired_invariants.json`
already carries a `P1.premise PASS` on a `carbon_plus25` pair at **+$25.00/t in all 25
years** — and the only INVERTED pair in the repository is the archived
`bau-prera-2026-08-31` `base ↔ carbon25` arm directory, which **no committed paired record
scores**. The whole question is therefore two **suffixed** board keys (`neiso-t3-pre-fc5`,
`neiso-t3-pre-fc6repair`) whose FC-6 category reads FAIL on the D21/D25 P1 row, and which
**no registered run sidecar resolves to** (§2.2): reclassifying them would change nothing
that renders anywhere. The three-way recommendation is §4.

---

## 0. Charter discipline

No solve, no score, no registration. `ff-verdicts.json` and `program-status.json` untouched
(D60-R4 is their sole writer this window — I REPORT what the guard would write, §2.4/§4). No
keeper, marker, shard, freeze, or board byte. No `ScenarioConfig` field, no default, no
matrix cell (rule 28: no mechanism is tested; the D26 row for `carbon_price_delta` stands as
is). Rules 13/21: nothing measured enters, no tunable is added — the build is
evidence-tightening only, reading configs the repository already commits. D23's file is
amended by dated cross-reference only (§5), the D23 §8-R3 / D72 precedent.

## 1. Phase 0(a) — what L872 guards today, quoted

`scripts/check_forecast_invariants.py:839–903` (HEAD `a98a0310`):

```python
def carbon_pair_premise(base: Run, high: Run) -> Result:
    """Premise assertion for the carbon pair (capx-D23 R1 / capx-D26). ..."""
    from market_sim.policy.carbon import resolve_carbon_price

    years = sorted(set(base.years) & set(high.years))
    ...
    b_sig = [float(resolve_carbon_price(base.config, y)) for y in years]
    h_sig = [float(resolve_carbon_price(high.config, y)) for y in years]
    delta = [round(h - b, 6) for b, h in zip(b_sig, h_sig)]
    bad = [y for y, d in zip(years, delta) if d <= 0.0]
    ...
    if bad:
        return Result("P1.premise", "carbon pair premise", FAIL,
            f"MIS-CONSTRUCTED: high-arm effective carbon ≤ base in "
            f"{len(bad)}/{len(years)} years (first {bad[0]}: Δ... $/t) — the pair does not "
            "construct a carbon-price increase, P1 not scored", data=table)
    return Result("P1.premise", "carbon pair premise", PASS, ..., data=table)
```

This is R1's assertion verbatim: `resolve_carbon_price(cfg, y)` over each arm's own config,
every common solved year, strictly-above-base or a MIS-CONSTRUCTED row. **What fires on it
today, and where:**

| consumer | line | behaviour on an inverted pair | behaviour on a monotone pair |
|---|---|---|---|
| `check_forecast_invariants.run_paired(..., kind="carbon")` | L1138–1157 | `P1` emitted **SKIP** ("premise mis-constructed — … see P1.premise") + `P1.premise` **FAIL**; `check_p1_co2_monotone` never called | `P1` scored PASS/FAIL + `P1.premise` PASS with the year table in `data` |
| `forecast_verdict.score_fc6` | L1425–1452 | `paired P1` row → **CAVEAT**, detail `"P1 MIS-CONSTRUCTED pair (vacuous evidence, FC-6.2): …"` — never PASS, never a scored FAIL, whatever the P1 row itself says | `paired P1` scored normally, `[premise: …]` annotation appended |
| `forecast_verdict.score_fc6`, **no premise row** | L1431–1434 | scores exactly as pre-D26 (every pre-D26 committed record) | — |
| `run_driver_battery.carbon_ladder_premise` | L1111, called L1320 | an inverted carbon-signal ladder's gate rows reclassified to vacuous SKIP (the D23 §7 T1.1-rung-0 case) | ladder scored |
| runtime, `policy/carbon.py::carbon_price_below_base_warning` (capx-D34) | — | fires at config construction on a `carbon_price` override below the program trajectory (D72 §6.1 saw it fire live on `carbon25`) | silent |

Existing tests (all green at HEAD, §3.4): `tests/regression/test_forecast_invariants.py`
L745–818 (additive-delta arm PASSes; replacement-override inversion FAILs with
`MIS-CONSTRUCTED` and a negative first-year delta; a no-program ISO's 0→25 absolute pair
PASSes), `tests/scoring/test_forecast_verdict.py` L765–800 (premise-FAIL P1 → CAVEAT for
P1 ∈ {SKIP, FAIL, PASS}; premise-PASS annotates and scores), `tests/scoring/test_driver_battery.py`
L403–430 (non-carbon and mass-cap ladders have no premise; NEISO absolute ladder inverted;
inverted ladder's gate rows vacuous).

**Verdict on (a): rule 19 forbids a second guard, and none is built.** The one thing R1
asks for that D26 did not deliver is the *committed-config* route. `run_paired_summaries`
(L1166–1180) refuses `--pair-kind carbon` with *"P1 needs each arm's resolved config for the
premise row … which live in the cache dirs"* — but the resolved config also lives in every
arm's committed `run_config.json` (`scenario_config` block, 765 keys on the golden arms), so
the premise IS computable at zero LP from committed artifacts. That is the phase-1 build:
one shared core the cache path delegates to (one mechanism), plus an artifact-mode entry
point and CLI flag that print the phase-0 table (§3).

## 2. Phase 0(b)/(c) — the board, the pairs, the table

### 2.1 Every FC-6 row on the board, and its arm pair

`frontend/data/forecast/ff-verdicts.json` carries **104** keys. **96** of them have FC-6
`SKIPPED` (T1-F, no battery/pair committed) or `n/a` (T1-H/T1-X, not applicable). The
**8** keys with FC-6 paired rows are all NEISO T3 and all descend from the golden families:

| key | bare? | scored_at (sha · date · stamping lane) | family · carbon pair | P1 row | premise row | FC-6 | det. |
|---|---|---|---|---|---|---|---|
| **`neiso-t3`** | **bare** | `7ed062ba9a68` · 2026-09-06 · D60-R3 | `bau-d46` · `base ↔ carbon_plus25` (rows carried into `bau-d60`, which has no `fc6/`) | PASS 284.42 → 273.92 Mt | PASS +25.00 ×25 | CAVEAT (T1.6 vacuous ×2) | HOLD |
| `neiso-t3-pre-d60` | suffixed | `71dd390ed56f` · 2026-09-04 · D47 | `bau-d46` · `carbon_plus25` | PASS 284.42 → 273.92 | PASS +25.00 ×25 | CAVEAT | HOLD |
| `neiso-t3-pre-d47` | suffixed | `e659a6eaecdc` · 2026-09-03 · D46 | `bau-d46` · `carbon_plus25` | PASS 284.42 → 273.92 | PASS +25.00 ×25 | CAVEAT | HOLD |
| `neiso-t3-pre-d46` | suffixed | `a67364c1aa2d` · 2026-09-02 (unstamped lane) | `bau` · `carbon_plus25` | PASS 229.82 → 196.00 | PASS +25.00 ×25 | CAVEAT | HOLD |
| `neiso-t3-pre-p2scope` | suffixed | `cba50e46aa70` · 2026-09-02 (unstamped lane) | `bau` · `carbon_plus25` | PASS 229.82 → 196.00 | PASS +25.00 ×25 | FAIL (P2, pre-D35 scope) | HOLD |
| `neiso-t3-prera-2026-08-31` | suffixed | `7dffe3341158` · 2026-09-01 · D26 | `bau-prera-2026-08-31` · `carbon_plus25` | PASS 210.52 → 174.96 | PASS +25.00 ×25 | CAVEAT | HOLD |
| **`neiso-t3-pre-fc6repair`** | suffixed | `7b085947b0ee` · 2026-09-01 01:10Z · D25 | `bau-prera-2026-08-31` · **`base ↔ carbon25`** | **FAIL 210.52 → 320.84** | **none** (pre-D26) | **FAIL** | HOLD |
| **`neiso-t3-pre-fc5`** | suffixed | `89dacc4c0343` · 2026-08-31 18:38Z (unstamped; D21's reading) | `bau-prera-2026-08-31` · **`base ↔ carbon25`** | **FAIL 210.52 → 320.84** | **none** (pre-D26) | **FAIL** | HOLD |

(`neiso-t3-pre-fc6`, `271ad606c3fd`, predates the battery entirely: FC-6 SKIPPED.) The
pair attribution is by the P1 row's own cumulative-CO2 values against the committed
`paired_invariants.json` of each family (§2.3 gives each family's arm set), so it is read
from the record, not inferred from the key name.

**The ONLY bare FC-6 paired row on the board is `neiso-t3`, and it is scored on a
`carbon_plus25` pair with a PASSing premise row.** The `carbon25`-scored P1 FAIL exists on
the board in exactly two places, both suffixed preserved baselines, both scored before the
premise row existed.

### 2.2 Who reads those two snapshots

- **The forecast dashboard: nobody.** `register_forecast_run.py::_verdict_key` resolves a
  run's verdict from the sidecar's `meta.verdict_key`, else `VERDICT_MAP`. All four committed
  T3 golden sidecars (`frontend/data/hindcast/neiso-2026-2050-t3-golden{,2,3}-bau.json`,
  `…-golden3-d60.json`) carry `verdict_key: "neiso-t3"` — the bare key — and `VERDICT_MAP`
  has no `neiso-t3-*` entry. `--reindex` therefore bakes the bare `neiso-t3` verdict into
  every golden run page; no page renders `neiso-t3-pre-fc5` or `neiso-t3-pre-fc6repair`.
- **`rescore_forecast_verdicts.py`: cannot touch them.** It re-scores only keys reachable
  through `VERDICT_MAP` with tracked artifacts, and in any case the input those two keys were
  scored on — a `paired_invariants.json` carrying `[P1 FAIL, P2, P3]` on `carbon25` — no
  longer exists: D26 replaced `bau-prera-2026-08-31/fc6/paired_invariants.json` in place
  with the `carbon_plus25` record (D26 §5, "the D21 precedent"). The snapshots are frozen by
  construction; a re-score cannot regenerate them.
- **`check_forecast_staleness.py`**: reads their `provenance` stamps as members of the
  gate-evidence class; a rewrite of their rows would need a fresh stamp and would move that
  class's "newest scored sha" — a side effect, not a reader.
- **Humans and findings**: D21 (`FINDING-capx-t3-golden2-2026-09-01.md`), D23, D25, D26,
  D72 and the director ledger cite the FAIL as the pre-repair reading. D26 §5 published the
  reclassification path already exercised — `neiso-t3-pre-fc6repair` is *itself* the
  preserved prior of a P1 FAIL → PASS re-score.

### 2.3 The effective-carbon table, every committed carbon pair

Method (D23's, D72 §9's): rebuild `ScenarioConfig` from each arm's committed
`run_config.json` `scenario_config` block (dropping keys no longer dataclass fields —
`caiso_bidir_intertie` on `bau`/`bau-prera`, `renewable_buildout_pace` on `bau-prera`;
neither is a carbon field, so the resolved signal is unaffected), then
`resolve_carbon_price(cfg, y)` for every solved year, arm minus base.

| family | carbon arm | `carbon_price` / `carbon_price_delta` (high) | Δ 2026 | Δ 2030 | Δ 2035 | Δ 2040 | Δ 2045 | Δ 2050 | inverted yrs | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `bau` (live) | `carbon_plus25` | 0.0 / 25.0 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | 0/25 | **MONOTONE** |
| `bau-d46` (live; rows carried into `bau-d60`) | `carbon_plus25` | 0.0 / 25.0 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | 0/25 | **MONOTONE** |
| `bau-prera-2026-08-31` (snapshot) | `carbon_plus25` | 0.0 / 25.0 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | +25.00 | 0/25 | **MONOTONE** |
| `bau-prera-2026-08-31` (snapshot) | **`carbon25`** | **25.0 / 0.0** | **−1.05** | **−9.15** | **−22.90** | **−42.18** | **−69.23** | **−107.16** | **25/25** | **INVERTED** |

Base trajectory in every family: 2026 $26.05 · 2030 $34.15 · 2035 $47.90 · 2040 $67.18 ·
2045 $94.23 · 2050 $132.16 (D23 §2.2 / D72 §6 to the cent). `bau-d60` has no `fc6/` of its
own. **Zero INVERTED live rows.** The single INVERTED pair is an arm directory with no
committed paired record scoring it — the `carbon25` arm is an orphan of the D26 in-place
replacement — and its only scored descendants are the two suffixed keys in §2.1.

### 2.4 What the guard WOULD write for the archived row (reported, not written)

Fed the archived pair's committed configs, the guard emits
`P1.premise FAIL — "MIS-CONSTRUCTED: high-arm effective carbon ≤ base in 25/25 years
(first 2026: Δ-1.05 $/t) — the pair does not construct a carbon-price increase, P1 not
scored"`. Fed that row beside the archived `P1 FAIL (210.52 → 320.84 Mt)`, `score_fc6`
writes `paired P1 = CAVEAT, "P1 MIS-CONSTRUCTED pair (vacuous evidence, FC-6.2): …"`. For
each of `neiso-t3-pre-fc5` / `neiso-t3-pre-fc6repair` the consequence is mechanical and
identical: FC-6 category **FAIL → CAVEAT** (the T1.6 vacuous battery row still holds it at
CAVEAT), `reasons` drops `"FC-6 driver response FAIL"`, `caveats` gains
`"FC-6 driver response"`, and the **determination stays HOLD** on FC-1/2/3/4/7 (plus FC-5
SKIPPED on `-pre-fc5`). Both are pinned as tests in §3.3 so the claim is executable rather
than narrated.
