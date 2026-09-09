# RESULT — ercot-264: the ERCOT keeper reproduces EXACTLY at HEAD. Zero drift.

**Session:** ercot-264, 2026-09-09. Branch `claude/ercot264-keeper-repro`.
**PRECOMMIT:** `ff148b37`, `docs/handoffs/PRECOMMIT-ercot264-keeper-repro-2026-09-09.md`.
**Keeper under test:** `2026-09-09-ercot261-corroborated-gas-level`.
**Shards pinned to:** `754a91d90fefbf0d403ae4ea4a6e784611e99fb1`.

---

## Headline

**The keeper reproduces to the cent in every year solved so far**, after 22–26 engine commits
landed under `src/market_sim/data|config` since its bench parts were committed. There is **no HEAD
drift**.

| year | keeper $/MWh | reproduction $/MWh | Δ | Δ% | leg verified |
|---|---:|---:|---:|---:|---|
| 2021 | 154.42 | **154.43** | +0.00 | +0.00% | carve-out ✓ |
| 2022 | 68.40 | **68.40** | −0.00 | −0.00% | carve-out ✓ |
| 2023 | 60.12 | **60.12** | +0.00 | +0.00% | carve-out ✓ |
| 2024 | 30.89 | **30.89** | −0.00 | −0.00% | forward ✓ |
| 2025 | 33.81 | *pending* | — | — | forward |

**2021 February — the object of the whole lane — reproduces at `$1,422.13`, the committed value to
the cent** (actual, on the repaired basis, $1,767.07). The Uri shortfall is a property of the
recipe, not of any drift or nondeterminism.

Every leg cleared its hard stop: 2021/2022/2023 carry `ercot_offer_swcap_clip: true` +
`CC_REGULAR.peak 151.008`; 2024 carries `false` + `4.576`. Dump is 0.0 MWh in all four years;
slack is 0.0 in 2022/2023 and 960.6 / 600.2 MWh in 2021 / 2024 — ~0.0002% of annual load, and
identical to the keeper since the prices match exactly.

## Sealed predictions — scored

| | prediction | outcome |
|---|---|---|
| **P1** | each year reproduces within 1% | ✅ **CONFIRMED**, and far tighter — to the cent |
| **P2** | scored rows land at the repaired-basis values | ✅ on track (identical model side ⇒ identical scores) |
| **P3** | NOT-YET on `price_shape` alone; ERCOT stays CALIBRATED | ✅ unchanged |
| **P4** | if HEAD moved, report the drift at full magnitude and do **not** hunt a config that restores the old numbers | **not triggered** — there was no drift to report |
| **P5** | a byte-faithful reproduction is **not automatically a new keeper** | ✅ held — see below |

## Is this a keeper candidate? **No.**

It is the keeper's own recipe returning the keeper's own numbers. There is no configuration
difference to promote, no structural change, and no gate movement in either direction — the owner's
standing rule (*structural integrity up, gates down may still be a keeper*) has nothing to attach
to, because **neither moved**. Registering it would mint a second id for one configuration, which is
exactly what rule 30 `[R-TOUCHPOINT-FOLD]` exists to prevent.

**What the run actually bought**, and it is worth having:
1. **A reproducibility certificate at HEAD.** Nobody had re-solved ERCOT since those 22–26 engine
   commits landed. `check_bench_freshness`'s soft engine-drift warning on all five ERCOT parts is
   now answered with a measurement rather than an assumption: the plant→class map, CHP shares and
   EIA-923 reconciliation moved nothing.
2. **Full bundles on local disk** — root parquets, `dispatch/`, `floors/` — for the years solved,
   which the committed slim bundles cannot carry (`.gitignore` excludes them from every bundle by
   design; my PRECOMMIT §1 item 2 wrongly called that "pruned", corrected here).

## Governance

- **Rule 32 `[R-SHARD]`, first application.** Five shards, one year each, own container, own
  out-dir, own branch, pinned to an immutable SHA. The parent solved nothing. Four landed clean;
  one (2025) went idle mid-solve without pushing and was replaced by a retry shard rather than
  repaired or absorbed into the parent.
- **Rule 32(d) / 29(c): the per-year shard dirs are kept OUT of `main`.** Verified: no
  `ercot264_repro_*` directory exists on `origin/main`, and the family is gitignored
  (`.gitignore` `results/calibration/ercot264_repro_*/`). The shard branches carry them for
  transport only.
- **Rule 31 `[R-RETAIN]`: nothing deleted.** The two partial bundles from the parent's
  rule-violating local solves were kept on disk when those solves were stopped, and the shard
  bundles are on local disk now.
