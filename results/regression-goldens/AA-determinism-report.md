# A/A determinism report — Stage-0 regression gate

**Date:** 2026-07-05  ·  **Branch:** `claude/regression-gate-stage-0-umopup`
**Git SHA:** `842d7f3` (origin/main HEAD)
**Purpose:** prove the golden-capture harness is deterministic before the six
keeper baselines are trusted as before/after references for Stages 1-7. A gate
that is not bit-reproducible A-vs-A is meaningless (a later stage's "diff" would
be indistinguishable from solver noise).

## Method

The cheapest keeper by fleet/zone size — **NEISO** (`2026-07-03-neiso-47-fast-start`,
4 zones + HQ import) — was captured **twice, independently**, from the same
frozen keeper `meta.json`, at the same commit, with determinism pinned:

```
MARKET_SIM_HIGHS_THREADS=1   MARKET_SIM_WARMSTART=1   MARKET_SIM_WARMSTART_XYEAR=0
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag aa-run1
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag aa-run2
```

Cold-vs-cold at `THREADS=1` is bit-identical; multi-threaded dual simplex breaks
marginal ties nondeterministically (`docs/cross-year-warmstart.md`), which is
exactly why the pin is mandatory.

## Result — BYTE-IDENTICAL

`python scripts/regression_gate.py --before …/aa-run1 --after …/aa-run2 --mode byte`
(`--atol 0 --rtol 0`):

```
[1] Golden bundle diff
    PASS  NEISO: 9 files, 43 numeric columns within tolerance (atol=0.0, rtol=0.0)
[2] Reshuffle localization
    NEISO 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
    NEISO 2024: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
    NEISO 2025: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
RESULT: PASS
```

Every numeric column of every result frame — `dispatch/{2023,2024,2025}_{P1,P2}`,
`system` (prices), `flows`, `storage`, `btm` — is identical to Δ = 0, and the
per-`plant_code` reshuffle is 0.000% across all three years (including the P2
commitment pass).

The manifests' **content hashes** (canonical column bytes, metadata-independent)
match to the full sha256 on all 10 files:

| file | sha256 (first 16) |
|------|-------------------|
| dispatch/2023_P1.parquet | `1c3ad609b40081f4` |
| dispatch/2023_P2.parquet | `98b41453b8472200` |
| dispatch/2024_P1.parquet | `3cefaa4c75edef99` |
| dispatch/2024_P2.parquet | `a85bc58909d30f0c` |
| dispatch/2025_P1.parquet | `8b8fea14a1f55e52` |
| dispatch/2025_P2.parquet | `0105e9d08c848864` |
| system.parquet | `531c92f52f7c0292` |
| flows.parquet | `661190486051cf2b` |
| storage.parquet | `faa4ecdda7f78ae8` |
| btm.parquet | `30e617f6492cc201` |

(Full hashes in `aa-run1/manifest.json` and `aa-run2/manifest.json`, both
committed alongside this report.)

## Conclusion

The harness is deterministic under the THREADS=1 pin. The six-ISO `stage1-before`
baseline captured with the same pins is therefore a trustworthy before-reference:
any non-zero `regression_gate --mode byte` diff a later stage produces is a real
dispatch change, not harness noise.
