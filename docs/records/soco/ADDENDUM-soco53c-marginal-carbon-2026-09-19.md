# ADDENDUM — SOCO-53c: the marginal-carbon control arm (owner instruction, 2026-09-19)

Recorded **before** either in-flight shard has landed, so the scope decision cannot be written to
fit a result. Parent: `PRECOMMIT-soco-53c-2026-09-19.md`.

## 1. THE SHA CHECK — PASSES, NO RE-PIN NEEDED

```
git merge-base --is-ancestor 2ec096633f5624585eb9db1728ebc7c8ca5ccbdf \
                             0f8ebad9d71d19a30bd020359d5b86ffb7576850   -> TRUE
```

`2ec09663` (merge of PR #6280, 2026-09-18) carries `fba0ecd7` *"Emit the marginal emission rate
from every solve"*, and it is an **ancestor of this lane's pinned shard SHA**. Both shards already
in flight therefore emit `marginal_emission_rate` on
`hourly/system_<year>.parquet` for all three years. **Nothing is re-pinned and no shard is wasted.**

This was not luck: the same commit is the LIVE hunk this lane's G-DRIFT audit identified
(PRECOMMIT §3.1), which is why the lane was already pinned past it.

## 2. THE ADDITIONAL CONTROL SHARD IS **SKIPPED**, on the instruction's own condition

> *"If you DO expect your arm to be promoted, skip this: your arm's own bundle will carry the
> column and the replay would be redundant."*

**This lane DOES expect its arm to be promoted**, on the standard the owner set twice — at the
SOCO-53 promotion (*"If structural integrity improves but gates regress that may still be a
keeper"*) and again in this sitting. The arm is a rule 14 `[R-ACCURATE]` repair of a **physically
impossible input**: Victor J Daniel Jr's 1970s subcritical PRB boilers are priced at **8.399
MMBtu/MWh** against their own measured **12.895**, and Barry's bituminous units at 8.995 against
11.699. Rule 1 `[R-STRUCT]` makes the most structurally faithful run the keeper, not the
lowest-residual one. The recommendation is made on that basis and is stated here **before** the
gates are read, exactly as the prediction was.

## 3. AND THE FORM-4 CHECK IS ALREADY IN FLIGHT — by a STRONGER route than a replay

This lane independently launched a control shard for precisely the rule 29 `[R-SCREEN]` (b) reason
the instruction names, before the instruction arrived (PRECOMMIT §3.1). The constructions differ,
and the difference is worth stating because it changes what the answer means:

| | the instruction's control | THIS LANE'S control |
|---|---|---|
| command | `replay_keeper.py <keeper bundle>` | `run_calibration_full.py --iso SOCO --year 2023 2024 2025 --measured-ct-heat-rates` |
| reconstructs from | the keeper's recorded `run_config.json` kwargs, incl. `DERIVED_RUN_YEAR_INPUTS` | the CLI's own defaults **at the pinned SHA** |
| catches code drift | yes | yes |
| catches **ScenarioConfig default drift** since the keeper's basis | **no** — the recorded kwargs pin it | **yes** |

So this lane's control answers the stronger question — *"would solving the keeper's recipe today
still give the keeper's numbers?"* — which is what form 4 actually asserts. Its cost is that a
difference is not self-attributing: it could be `fba0ecd7`'s dual **or** a default that moved.
**That is resolved without another solve**, by differencing the two bundles' `scenario_config`
blocks field-by-field (852 fields, the same construction `audit_keepers` E11 uses). Config-identical
+ numbers-identical ⇒ form 4 confirmed empirically. Config-identical + numbers-moved ⇒ the dual
moved the LP, which is a cross-ISO finding about `fba0ecd7` and is reported as one.

**SOCO gets its marginal-carbon data either way**, because BOTH in-flight bundles carry the column:
the arm's (which becomes the keeper if promoted) and the control's (the keeper's own recipe at
HEAD). No third span is spent.

## 4. WHAT THIS LANE STILL OWES ON THE MARGINAL-CARBON OBJECT

Verified and reported when the bundles land, per the instruction:

- `marginal_emission_rate` **present and not all-zero** on every
  `hourly/system_<year>.parquet`, both bundles, all three years. Absent ⇒ the SHA was wrong and the
  bundle is useless for this purpose; this lane would say so rather than quietly registering it.
  *(A cached or `--reuse-solved` year carries `None`; both shards solve into a fresh `--out-dir` in
  a fresh container with no committed `results/<ISO>/` cache, so neither can reuse.)*
- Per year: load-weighted mean, p10 / median / p90, and the **share of zone-hours at exactly 0.0**.
  SOCO's zero share is expected to be material and is a BOUNDARY artifact, not a measurement:
  zero-carbon columns carry rate 0 and **import pseudo-units carry rate 0 by design**, and SOCO is
  a net exporter of 10.2–13.0 TWh/yr served on measured EIA-930 interchange. An import-marginal
  hour reads 0 and understates true system consequence — stated here so the marginal-abatement page
  does not read those zeros as abatement headroom.
- `container preflight:` and `memory peak:` (RSS and RSS+swap) verbatim, per the instruction's
  note that **the dual's memory cost is unvalidated at scale**. SOCO is a 3-zone, ~393-generator,
  non-per-plant LP at a measured 2.65 GiB cgroup peak, so it is a WEAK test of that concern — an
  OOM here would be alarming, but a clean run here does **not** clear per-plant MISO/PJM. Said
  plainly rather than offered as reassurance.
- The bundle path and its **full immutable SHA** in the RESULT (rule 33 `[R-SHARD-ARCHIVE]` (d)),
  so the marginal-abatement page can find them.

## 5. UNCHANGED

No re-pin, no fourth shard, no new mechanism, no `ScenarioConfig` field, no matrix row owed. The
arm, the control, the ex-ante prediction with its three falsifiers, the G-DRIFT audit and the DOF
ledger all stand exactly as `PRECOMMIT-soco-53c-2026-09-19.md` fixed them. Rule 31 `[R-RETAIN]`:
nothing is deleted.
