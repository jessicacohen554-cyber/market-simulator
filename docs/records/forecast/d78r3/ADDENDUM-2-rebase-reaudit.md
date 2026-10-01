# ADDENDUM 2 — capx D78-R3: the rebase re-audit found a LIVE hunk, and the control leg's recipe changes because of it

**Pushed BEFORE the control-P leg runs.** ADDENDUM 1's G-DRIFT covered
`65e12b21 → 0f7a4842`. The owner asked me to refresh `main` mid-session; the rebase moved this
branch to **`992760ec`**, so ADDENDUM 1's range no longer reaches the leg's code state and the
audit is re-run over the delta. This is D78-R2's ADDENDUM A discipline, applied to my own rebase.

**I had already started the bare leg when the rebase landed. It was KILLED after ~1 minute and
its partial bundle deleted**, rather than argued past on the reasoning that a 21-minute solve
could not yet have shown me anything. PRECOMMIT §7 says the audit is recorded before the leg it
governs; a lane that reaches for a correct-sounding reason to walk past its own gate has made
that gate advisory (D78-R2 §1, which discarded 20.5 minutes on the same principle). **The killed
leg produced no number and none is cited.** It turns out to have been the right call for a second
reason I did not anticipate — §2.

## 1. The delta

`0f7a4842 → 992760ec`, **76 commits**.

```
git diff --stat 0f7a4842..992760ec -- src/market_sim scripts/run_capacity_hindcast.py \
    scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib \
    data/raw/_validation-source data/raw/reference
```

**13 files.** Classified below.

## 2. THE LIVE HUNK — capx D75-R-ARM / owner ruling Q55 lands PJM's VRE devintage

| file | Δ | verdict |
|---|---|:--:|
| `src/market_sim/config/iso_configs.py` | +67 | **LIVE** |
| `src/market_sim/config/constants.py` | +1 | **LIVE** (its dependency) |

`_pjm_config`'s `default_scenario_overrides` now carries
**`pjm_vre_accreditation_vintage: True`** — owner ruling **Q55**, executed by capx D75-R-ARM,
armed the D57/Q44/D67-ARM way (through the ISOConfig override, not a shared `ScenarioConfig`
default flip). PJM wind and solar are accredited at each delivery year's own published ELCC class
ratings. `constants.py` +1 is that lane's `PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE` import.

**This is LIVE for exactly the object I am deriving on.** VRE accreditation feeds the accredited
census, which feeds the adequacy position, the clearing and therefore the **offer stack**. It is
not a flag absent from the recipe: it is now **in** the bare recipe by ruling.

**Measured, zero LP**, through the same harness path `keys_probe.py` uses
(`build_config` → `apply_iso_scenario_defaults` → `cache_key()`):

| recipe at `992760ec` | key | is it D78-R2's graded control? |
|---|---|:--:|
| bare `pjm-t1h` (what `run_full.sh control-P` sends) | **`b518f5fe7d02f961`** | **NO** |
| `--no-pjm-vre-accreditation-vintage` | **`a9c66d8ea25acb9d`** | **YES** |

The bare leg I killed would have solved a **different control** from the one whose mover counts
the W5″ re-grade reads. PRECOMMIT §6's **S1 (G-CTL-ID)** would have caught it on the key alone —
the pre-registration doing its job — but only after 21 minutes of LP.

### 2.1 The consequence: the leg's recipe changes, and the change is disclosed here

PRECOMMIT §5.1 quoted `bash docs/handoffs/d78r2/run_full.sh control-P`. **That command no longer
reaches the graded control**, so the leg runs as

```
bash docs/handoffs/d78r3/run_ctl.sh          # adds --no-pjm-vre-accreditation-vintage
```

out-dir `results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P`, HEAD-guarded, deleted
before merge (rule 29(c)). **S1's requirement is unchanged and unrelaxed**: the leg must realize
`a9c66d8ea25acb9d` and reproduce `control_band.json`'s aggregates to `MW_TOL`. What changed is
only which command reaches that key — the *object* S1 demands is the same object it demanded
before the rebase.

**Note what is NOT being claimed.** This lane does not evaluate Q55, does not grade the VRE
devintage, and does not say the pre-arm posture is the better one. It says the derivation base
must be the control that produced the graded comparison, and at `992760ec` that control is named
by an explicit flag rather than by omission.

## 3. Everything else — INERT, with its reason

| file | Δ | verdict | reason |
|---|---|:--:|---|
| `scripts/run_capacity_hindcast.py` | +9 −6 | **INERT** | An argparse `help=` string only (the `--pjm-vre-accreditation-vintage` help now records the Q55 arm). No executable line changes. |
| `src/market_sim/config/scenarios.py` | +44 | **INERT** | One new field, `miso_seam_neighbour_hourly_ladder: bool = False` (miso-231) — **MISO's** mechanism (rule 25, another ISO's branch), default-off and absent from this recipe, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at declared default `"False"` so it is dropped from the hash. |
| `src/market_sim/model/interchange/import_nodes.py` | +19 −6 | **INERT by algebraic identity** | `_inject_seam_ladder` gains `hourly_anchor: … | None = None`; with `None`, `anchors = {}`, `anchors.get(name)` is `None`, and the assignment reduces to `mc[row, :] = prices[k]` — **the pre-change line exactly**. No caller passes an anchor unless the MISO gate is armed. |
| `src/market_sim/model/interchange/spec.py` | +134 −0 | **INERT** | Purely additive registry rows for the MISO seam ladder (from line 1370). Nothing existing is edited. |
| `src/market_sim/model/interchange/miso.py` | +55 −? | **INERT** | MISO's own branch (rule 25); a PJM run never enters it. |
| `data/raw/reference/caiso-supply-consistent-demand/*.csv` + `provenance.json` | ±17,520×3 | **INERT** | **CAISO's** artifact (rule 25). A PJM run reads none of it. |
| `scripts/run_calibration.py` | +77 | **INERT** | The **backcast** calibration CLI. `run_capacity_hindcast.py`'s import block never imports it; a hindcast executes no line of it. (Unchanged verdict from ADDENDUM 1.) |

**Carried forward from ADDENDUM 1** (`65e12b21 → 0f7a4842`, 89 commits, 5 files): all INERT —
two default-off cache-key-dropped `ScenarioConfig` fields, a `runner.py` line that reduces
algebraically to its predecessor in forecast mode, a pure `paths.py` addition, a fully
flag-guarded transfer-limits gate, and the backcast CLI.

**Net over `65e12b21 → 992760ec`: ONE live mechanism (Q55's VRE devintage), answered by naming
it explicitly on the leg's command line rather than by ignoring it.**

## 4. What is untouched by all of this

The **W5″ re-grade (step 2) is already complete and is not affected**: it reads
`window_compare2.json` and the merged FINDING §5.1 only, spends no LP, and re-solves neither leg.
Its verdict does not move with `main`.
