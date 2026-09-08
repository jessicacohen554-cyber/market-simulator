# `_rollup/` provenance — how these four files were produced

**Produced by** SCN-WS5A-POLICY-SYNTH (Stage C), 2026-09-08, **zero LP**.
**Tool** `scripts/collate_scenario_campaign.py` (unmodified — this lane edits no `scripts/`).
**Reference case** `REF`. **Campaign** `scn-campaign-policy-2026-09-06`.
**THE PIN of every leg summarised here** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`.

Read the headline in `docs/handoffs/FINDING-scenario-campaign-2026-09-07.md`.

---

## 1. Why the tool was pointed at an assembled root, and exactly what was in it

`collate_scenario_campaign.py` takes **one** `--root` and discovers every
`<root>/**/full_horizon_summary.json` beneath it. The campaign's summaries are split
across **two committed roots**:

| root | what it holds | summaries |
|---|---|---|
| `results/scn-campaign-policy-2026-09-06/` | the 65 policy-axis legs | 65 |
| `results/scn-campaign-load-2026-09-06-r2/` | the campaign's `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` legs, re-solved by SCN-WS5A-RESOLVE after capx D77 repaired the CCS emission-rate seam | 16 |

A collate run over the policy root alone would have carried **no `REF` for five of six
ISOs**, so every per-ISO and system delta would have read `NO DELTA`. **No committed bundle
was moved, renamed, or deleted.** Instead a read-only union tree was assembled in the
session scratchpad by *copying* the summary JSONs:

```
scn-campaign-policy-2026-09-06-with-r2-refs/     (scratchpad, not committed)
  <ISO>/<CASE>/full_horizon_summary.json          79 files
```

- **63 of the 65** policy-root summaries were copied verbatim.
- **All 16** r2-root summaries were copied verbatim.
- **2 were deduplicated**: the policy root additionally carries its own copies of
  `NYISO/REF` and `NYISO/LOAD-HI` (the ragged-tree fact — CAISO's eight legs carry no such
  copies, NYISO's twelve do). Both copies were dropped in favour of the r2 root's, so
  NYISO's `REF` and `LOAD-HI` levels enter the sum **once**. This is a no-op on every
  number: the two pairs carry the **same `cache_key`** (`f10cc93084b4c0db`,
  `c2ceaefa4afafcda`) and **byte-identical `trajectory` arrays**; they differ only in
  `campaign`, `run_config_path` and the wall-clock/RSS perf block. Had they not been
  deduplicated, `build_system_frame`'s group sum would have double-counted NYISO in every
  `REF` and `LOAD-HI` system row.

Because the summaries are copies, every `run_dir` string inside them is unchanged, so the
side-line reconstruction behaved exactly as it would have in place (§3).

**Reproduce:** copy the 79 summaries as above, then

```
python3 scripts/collate_scenario_campaign.py \
    --root <union-tree> --reference-case REF \
    --out-dir results/scn-campaign-policy-2026-09-06/_rollup
```

The union tree's directory name is what appears in `campaign_report.md`'s title
(`scn-campaign-policy-2026-09-06-with-r2-refs`) — it names the assembly, deliberately, so the
title cannot be read as "the policy root alone".

## 2. Which `REF` each ISO's deltas are taken against

**All six ISOs difference against the post-D77 r2 `REF`**, i.e.
`results/scn-campaign-load-2026-09-06-r2/<ISO>/REF/`. No delta in these files is taken
against a pre-r2 bundle. That matters: SCN-WS5A-RESOLVE measured the campaign's CO2 levels
overstated by up to **57 %** before the D77 repair, and the error does **not** cancel out of
a delta, because the two arms re-screen the retrofit fleet differently
(`docs/handoffs/FINDING-scn-ws5a-resolve-2026-09-06.md`).

**Every reference leg is at THE PIN on the solve path, and this was verified rather than
assumed.** Four `git.basis_sha` values appear across the twelve r2 reference legs — the pin
`bdfb3095` (ERCOT, NEISO, NYISO, PJM/REF), `c538ecfb` (CAISO), `95ad76d4` (MISO) and
`9ef06cf8` (PJM/LOAD-HI). All three non-pin shas are **descendants of the pin**, and a
zero-cost G-DRIFT audit (`git diff <pin> <sha> -- src/market_sim scripts configs data/raw`)
returns an **empty diffstat for all three**: CAISO's and MISO's commits add one doc file each
(their own PRECOMMIT) and PJM/LOAD-HI's adds 41 doc / registry-sidecar / results files and no
solve-path file. **The campaign therefore sits at one effective pin, not four.**

The former ERCOT caveat is **RETIRED, not carried**: `ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md`
re-solved ERCOT's `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` at the pin, and the committed r2 ERCOT
`REF` (`de9c68e19316910e`, sha `bdfb3095`) carries `gas_cc_ccs` 0.0 / 2,763.8 / 5,763.8 MW in
2028/29/30 — it converts on its own, so ERCOT's 2028–2030 deltas are no longer differenced
against a non-converting control. These files **reproduce ADDENDUM B exactly** at 2030
(CARB-HI −10.7360, CARB-LO −10.6016, CES-P10 −10.0300, VOL-HI +0.0000, ALL-CLEAN +4.2334 Mt),
which is the cross-check that the re-difference landed. ERCOT's **price** levels remain
disclosure-only in every year for the separate adequacy reason (memo §10.1).

## 3. Why every side-line cell reads blank

`import_co2_mt_reported` and `unserved_mwh` are **not** in the `full_horizon_summary.json`
schema. The tool reconstructs them from each run's cached `year_*.parquet` through
`results/export.py::_summarize_year`. **No scenario cache is on disk** — the caches are
gitignored and this container was cloned fresh — so the tool reports a blank, which is its
documented behaviour and is **never** a zero. The lane-measured side lines DO exist, in the
six per-ISO FINDINGs, and are carried with their citations in §9 of the Stage C memo.

## 4. What the total is, and what it is not

The `six-ISO modeled system` label is the tool's and it is load-bearing: the sum spans
ERCOT + CAISO + MISO + PJM + NYISO + NEISO, roughly two thirds of US load. It is **never**
national. SPP is a seventh registered ISO and is outside the sum (memo §10.4). Rows whose
`delta_coverage` is not `full` were differenced on the **intersection** of the case's ISO
set with `REF`'s — read that column before quoting any system delta; five of the seventeen
cases are partial (`CARB-*` on two or three ISOs, `CES-P60` on five, `VOL-*` on four or
five, `CAP-STATE-TIGHT` on four).

`CAP-STATE-TIGHT` is present in these files because it is a committed, registered bundle on
disk and the tool reads disk. Under **owner ruling S17** it is **out of Stage A**: it is
excluded from the memo's headline, its delta tables and the plan §5.1 rows, and is carried
only as Stage-B seed evidence (memo Appendix A).
