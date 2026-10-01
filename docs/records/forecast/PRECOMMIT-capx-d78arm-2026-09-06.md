# PRECOMMIT — capx D78-ARM: arming the PJM retirement-screen sector gate (owner ruling Q56)

**Lane:** capx D78-ARM, executing **owner ruling Q56** — served by
`FINDING-capx-d78r3-2026-09-06.md` §5 (*"RECOMMENDATION: RECOMMEND ARM. Serve as owner card Q56"*),
ruled ARM by the owner in this lane's charter (*"owner ruling Q56 … ARMS retirement_sector_gate for
PJM. Execute it — this lane DOES arm"*). **Branch:** `claude/pjm-retirement-sector-gate-at0cao`,
fresh off `origin/main` **`8875af59`**. **Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.

**Pushed before any code change and before any solve.** Every key, count and classification below
was measured at `8875af59` with **zero LP**, through the shipped harness path, and is recorded here
so it cannot be written to fit a result.

**Template:** `PRECOMMIT-capx-d75r-arm-2026-09-06.md` (the Q55 arm — this lane copies its execution
pattern exactly) and the D57/Q44 → D67-ARM → Q55 arming precedent. **Charter evidence:**
`FINDING-capx-d78r3` (all; §5.2 twice), `FINDING-capx-d78r2` §§3–8, `FINDING-capx-d57` §4 / §8.1.

**Instruments** (declared here, before the edit):
- `scripts/probes/capxd78arm_iso_override_no_op_check.py` — the D75-R-ARM committed-config sweep,
  with ONE change this field forces: `retirement_sector_gate` is **already armed for MISO** (capx
  D53), so "the value the arm resolves" ≠ "the value the shipped path resolves" for every ISO. The
  probe therefore differences the field resolved **without** the PJM override against the field
  resolved **with** it, both off the shipped `apply_iso_scenario_defaults` path, so it isolates THIS
  arm. (The first cut, copied verbatim, reported nine MISO moves that were D53's arm showing through
  the instrument — disclosed rather than smoothed: the record is `docs/handoffs/d78arm/`.)
- `docs/handoffs/d78arm/keys_probe.py` — the recipe-leg key table (bare, every explicit control leg,
  the five other ISOs, the PJM plain backcast), `--simulate-arm` ex ante and flag-omitted ex post.

---

## 0. A record fact the charter names, and this lane's answer to it

**The serving document is not on `main`.** `FINDING-capx-d78r3-2026-09-06.md` exists only at
`origin/claude/capx-d78r3-perdy-set` **`4d668500`** (one commit past the merged PR #5295, which
landed that lane's PRECOMMIT and addenda); at `8875af59` no open PR carries it. This lane cites it by
branch and sha, does not carry that lane's commit into its own PR, and **does not depend on it for
any number**: every figure this PRECOMMIT quotes from D78-R2 is in the merged
`FINDING-capx-d78r2-2026-09-06.md` and `docs/handoffs/d78r2/window_compare2.json`. The D78-R3 cell
text in `mechanism-matrix/PJM.js` is likewise on that branch only; this lane edits the cell as it
stands on `main` and states the collision (§7).

**The D78-R2 arm bundle was never registered** (D78-R3 §2, §5.2 item 1: merge `80c88b76` landed docs
and JSON only, so limbs (b)/(c)/(d) rest on a bundle in no repo). **This lane closes that by
construction** — arming means solving and registering the bare `pjm-t1h` on the new default, and the
registration is NOT deferred behind any other lane's batch. That deferral is exactly what stranded
D78-R2 (its §11: *"after D65-B-R's batch registers"* — it never did).

---

## 1. The act

`config/iso_configs.py::_pjm_config` `default_scenario_overrides` gains one key:

```python
"retirement_sector_gate": True,
```

The D57/Q44 → D67-ARM → Q55 pattern exactly, and **nothing else**:

- the shared `ScenarioConfig` dataclass default stays **`False`** — an **ISO override, not a declared
  default flip**, so no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry, no other ISO's key moves, and
  every backcast key is byte-identical (the field is coerced to its dataclass default in
  `mode="backcast"`, kept in a hindcast);
- the explicit `--no-retirement-sector-gate` path reaches the pre-arm posture and keeps its key (the
  (b′-1) inverse) — the flag already exists, `argparse.BooleanOptionalAction` with `default=None`
  (`scripts/run_capacity_hindcast.py:1911`), so **no CLI surface is added**;
- **rule 19 `[R-ONE-MECH]`**: one partition on one published boolean at one seam
  (`exit_exempt_unit_ids`, the screen's sole exemption seam since D78-R2 deleted `exempt_unit_ids`);
  no unit's exit is decided twice — a dated sector-1 plant is a dated plant first, and neither
  declaration produces an exit;
- **rule 21 `[R-DOF]`: zero free parameters.** `Sector` is a published per-plant EIA-860 attribute read
  at the run's active vintage; no weight, threshold, share or fitted value. **The ruling is the
  identification.** The decision to arm rests on the structural limbs D78-R2 §8 / D78-R3 §5 graded —
  a pure candidate-set partition (W1/W2/W3 exact in five years, W4′ hit to the milli-MW, W5″ PASS on
  D57's per-delivery-year set) — never on a residual;
- **rule 25 `[R-ISO-SCOPE]`: a PJM posture on PJM's own evidence.** MISO's D53 arm transferred
  nothing; PJM's cell moved from `U` through `O` on D58 / D78 / D78-R / D78-R2 / D78-R3, all PJM
  legs. No other ISO's cell, key or shard is touched.

**Also in the PR** (test + docs, no solve-path behaviour): the D75-R-ARM-style override pin
`tests/unit/model/test_capacity.py::test_pjm_iso_override_arms_forecast_only` re-pinned to the new
key set with every inverse beside it; the `--retirement-sector-gate` help string, whose *"OMIT to
inherit the shipped default (off, owner-armed only)"* clause becomes false for PJM the moment the arm
lands; the CLAUDE.md Capacity Evolution bullet (on the D75-R-ARM template); the `results/cache.py`
cache-epoch entry; the PJM matrix shard cell `O → K`. **Docs follow code.**

**NOT in the PR:** any `retirements.py` decision logic (this is an arming lane, not a mechanism lane);
any `ScenarioConfig` field or default; any other ISO's shard; any backcast file; the
`ff-verdicts.json` / `program-status.json` snapshot (§6).

---

## 2. THE RE-KEY — declared before the edit, measured through the harness at `8875af59`

Harness path, the same one the override pin uses: `build_config(iso, 2021, 2025, "realized",
vintage=2020, entry_screen_diagnostics=True)` → `apply_iso_scenario_defaults` → `cache_key()`.
Records: `docs/handoffs/d78arm/keys_pre_arm.json` (flag omitted, override absent) and
`keys_expectation.json` (`--simulate-arm`). The post-edit run must reproduce the right-hand column.

| recipe | key at `8875af59` (pre-arm) | **after the arm** | |
|---|---|---|---|
| **bare `pjm-t1h`** | `b518f5fe7d02f961` | **`fb16fda2ddb0a94a`** | **moves** — the armed posture |
| explicit `--no-retirement-sector-gate` | `b518f5fe7d02f961` | `b518f5fe7d02f961` | **unmoved** — the Q55 posture, reachable and identified |
| explicit `--no-pjm-vre-accreditation-vintage` | `a9c66d8ea25acb9d` | **`bb6a60239d69508b`** | moves — **and lands on D78-R2's own arm key** (`d78r2/keys_probe.json` `pjm_t1h_arm_2021_2025`) |
| `--no-pjm-vre-accreditation-vintage --no-retirement-sector-gate` | `a9c66d8ea25acb9d` | `a9c66d8ea25acb9d` | unmoved — the D67-ARM / D78-R2 graded control |
| D57 off3 (`--no-` ×3), D67 + Q55 on | `1785cb6086cd2b15` | **`f1a9881ed29df6cb`** | moves |
| off3 + `--no-retirement-sector-gate` | `1785cb6086cd2b15` | `1785cb6086cd2b15` | unmoved |
| off3 + `--no-vre` + `--no-gate` | `61dfbc5c48af076b` | `61dfbc5c48af076b` | unmoved |
| off3 + `--no-req-pub` + `--no-vre` + `--no-gate` (D45-R bare) | `c5ec052057905966` | `c5ec052057905966` | unmoved |
| D57 arm B (`--no-` ×2), D67 + Q55 on | `ab0237198cff24ad` | **`944c89de0a74ca63`** | moves |
| off2 + `--no-retirement-sector-gate` | `ab0237198cff24ad` | `ab0237198cff24ad` | unmoved |
| off2 + `--no-req-pub` + `--no-vre` + `--no-gate` (arm B) | `6ba67a81ed4d2ed6` | `6ba67a81ed4d2ed6` | unmoved |
| MISO / NYISO / NEISO / CAISO / ERCOT bare | `1f92943f84f42fd0` · `ee6a3e764324f28f` · `5b292e24dd752ea4` · `8f1c3766703a90c4` · `46d013cbf1f35d27` | all **unmoved** | MISO resolves the gate **True** on both sides — D53's own arm, untouched |
| PJM plain backcast | `3a566deac3a85682` | `3a566deac3a85682` | **unmoved**, field coerced `False` |

### 2.1 The control legs MOVE, pre-declared with their measured literals

As D75-R-ARM §2.1 declared for its field and D67-ARM §2.1 discovered for its own: a leg that turns
off named fields and says nothing about this one carries it **armed** after the arm. The reason is
structural — `retirement_sector_gate` is a `_CACHE_KEY_OPTIONAL_FIELDS` member registered at
`"False"`, dropped from the hash while unarmed and entering it once armed, on every PJM forecast leg
whatever the other flags say. **The arm is fully invertible**: adding `retirement_sector_gate=False`
to each post-arm leg restores its pre-arm literal exactly (every "unmoved" row above IS that
inverse, measured). All three moved legs are re-pinned in `test_capacity.py` with their inverses
beside them.

### 2.2 The three keys that already carry a measurement — this is a re-declaration of a measured recipe, not a new number

- **`bb6a60239d69508b`** — the post-arm `--no-pjm-vre-accreditation-vintage` leg — is **D78-R2's
  measured arm** (its control `a9c66d8ea25acb9d`, its arm `bb6a60239d69508b`, solved at one HEAD).
  So the sector gate's own effect on the PJM recipe has a measured record; what this lane solves is
  that record **plus Q55**, which is the shipped posture.
- **`b518f5fe7d02f961`** — the post-arm `--no-retirement-sector-gate` leg — is **D75-R's measured
  arm** (its control `a9c66d8ea25acb9d`), i.e. the Q55-only posture, whose full-window numbers are
  documented in `FINDING-capx-d75r` §5.2. That bundle was never registered (D75-R-ARM's steps 3–4
  were HELD on the board STOP and never released), so its numbers survive as document only —
  rule 29(c)'s standard.
- **`a9c66d8ea25acb9d`** — the committed bare `pjm-t1h` (D67-ARM), the only PJM T1-H bundle on
  `main` with the full slim ledgers — is the common control of both.

**Cache-epoch ledger** (`src/market_sim/results/cache.py`): a **KEY ADVANCE, not a same-key
invalidation** — the bare recipe moves `b518f5fe7d02f961` → `fb16fda2ddb0a94a`, so no committed
bundle is silently re-interpreted and the D67-ARM bundle keeps its own key under its own id.
**Registration re-key (`register_forecast_run.py` `VERDICT_MAP`), landed in THIS lane**: the D67-ARM
record `pjm-2021-2025-realized-t1h-d67arm` → `pjm-t1h-pre-d78arm` (verbatim, its own verdict
standing — the D45-R / D57 / D67 convention); the armed re-solve
`pjm-2021-2025-realized-t1h-d78arm` → **`pjm-t1h`**. (No `pjm-t1h-pre-d75r` step exists to preserve,
because the Q55 posture was never registered.)

### 2.3 The committed-config sweep (P-1's expectation, ex ante)

`capxd78arm_iso_override_no_op_check.py --simulate-arm` at `8875af59`, over all **157** committed
`run_config.json` payloads (`docs/handoffs/d78arm/no-op-expectation.json`):

| bucket | configs | moved by THIS arm |
|---|---:|---:|
| every non-PJM ISO (CAISO/ERCOT/MISO/NEISO/NYISO), forecast **and** backcast | 134 | **0** |
| PJM **backcast** | 2 | **0** |
| **PJM forecast** | 21 | **21** |

Ten committed configs (nine MISO forecast bundles solved before D53, and D78-R's own PJM arm, whose
committed value is already `True`) carry a field value that differs from the shipped path's
**pre-arm** resolution; the probe lists them under `committed_differs_from_pre_arm_resolution` and
counts none as a move, because none is this arm's. Zero off-target moves. Re-running the same probe
**after** the edit with `--simulate-arm` omitted must reproduce this table exactly. **Any non-PJM or
backcast move is a STOP, not a number to record.**

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — from D78-R3's control HEAD to this lane's

**Window: `bb728e43` → `8875af59`**, 43 commits (21 merges, PRs #5287–#5307). `bb728e43` is the HEAD
D78-R3's control leg was solved under (its ADDENDUM 2 commit; the leg realized `a9c66d8ea25acb9d`
and reproduced D78-R2's `control_band.json` sha-identical, D78-R3 §4.1). D78-R3's own two addenda
carry the audit back to D78-R2's solve base (`65e12b21 → 0f7a4842 → 992760ec`): **one LIVE hunk in
that whole span, Q55**, everything else INERT with its reason.

### 3.1 Q55 / D75-R-ARM is LIVE on PJM's accreditation — and it is IN the armed recipe

Stated plainly, as the charter asks. `pjm_vre_accreditation_vintage: True` arms PJM's VRE devintage
by owner ruling; VRE accreditation feeds the accredited census, the adequacy position, the clearing
and therefore the offer stack the sector gate partitions. It is **LIVE relative to D78-R2's graded
comparison** (both of whose legs pre-date it), and it is **part of the shipped posture this lane
arms on top of**. This lane therefore solves the bare recipe **with** Q55 — `fb16fda2ddb0a94a` — and
does **not** pass `--no-pjm-vre-accreditation-vintage`. That flag existed in D78-R3 only to reproduce
D78-R2's graded control as a derivation base (its ADDENDUM 2 §2.1); an arming lane has no such object
to reproduce. Consequence for the read-out (§5): the armed run's move against the committed control
`a9c66d8ea25acb9d` is the **sum** of Q55 (documented, D75-R §5.2) and the gate (documented, D78-R2
§7), and the two documented single-mechanism legs are what the decomposition is read against.

### 3.2 `bb728e43 → 8875af59` on the solve path — **every hunk INERT**

```
git diff --stat bb728e43 8875af59 -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/run_capacity_hindcast.py scripts/lib \
    data/raw/_validation-source data/raw/reference
```
**3 files, +15 −5.** Plus `data/raw` / `configs` / `scripts/data`: 6 files, all ERCOT.

| file | Δ | commit | classification |
|---|---|---|---|
| `src/market_sim/config/scenarios.py` | +7 −5 | `b8e0c537` (ercot-252) | **INERT — comment only.** The hunk edits the citation comment above `ercot_load_resource_reserve_from_year`; no field, default, or executable line changes. `git diff -w` on code lines is empty; the field's declaration (`int = 2023`) is byte-identical. |
| `src/market_sim/results/scarcity.py` | +5 −1 | `b8e0c537` | **INERT — docstring only**, inside `ercot_load_resource_reserve_mw`, an ERCOT co-opt reader (rule 25: another ISO's branch; a PJM hindcast never calls it). |
| `scripts/lib/mech_matrix.py` | +5 −2 | `62681e22` (SPP-21) | **INERT — not on the solve path.** The matrix-guard library adds SPP to `ISO_ORDER` / `ISO_EV_KEY`; imported by `check_mechanism_matrix.py` only. |
| `data/raw/ercot-AS/*` (+3 parquet, README), `scripts/data/build_ercot_as_backyear.py` (+422), `build_ercot_as_by_restype_from_60day.py` | — | `b8e0c537` | **INERT — ERCOT artifact** (rule 25); consumed only under `ercot_load_resource_reserve_from_year`, an ERCOT co-opt gate. |

**Recipe posture, resolved at `8875af59` (measured through the harness, not asserted):**
`pjm_accreditation_design_vintage` **True** · `pjm_demand_response_supply` **True** ·
`capacity_market_supply_clearing_by_iso` **`{"PJM": True}`** ·
`capacity_adequacy_requirement_published_by_iso` **`{"PJM": True}`** · `pjm_vre_accreditation_vintage`
**True** (Q55) · `retirement_sector_gate` **False** (the field this lane arms) ·
`ccs_retrofit_available_year` 2028 · `fossil_announced_exits_enabled` True.

**ALL HUNKS INERT ⇒ D78-R3's control leg (which reproduced D78-R2's control byte-for-byte) is still
the graded control at this HEAD, and G-CTRL form 4 against the committed `a9c66d8ea25acb9d` bundle is
valid.** No control solve is earned and none will be spent (rule 29(b)); the one LIVE mechanism in
the wider span, Q55, is not drift on the recipe but the recipe (§3.1).

---

## 4. Rule 29(a) — why there is no screen solve

**29(a) does not apply**, exactly as in D75-R-ARM §4 and D67-ARM. The screen exists to *select* an arm
before spending a full span. There is nothing to select: the sector gate has been through D58's
screen, D78's screen (three legs), D78-R's full window, D78-R2's full window (both legs at one HEAD)
and D78-R3's control re-solve, and **the owner has ruled**. This lane executes a ruled arming and
spends **one** solve: the shipped posture, 2021–2025, PJM solo, sequential, HEAD-guarded.

---

## 5. Pre-declared expectations — graded at full magnitude, whatever they read

### 5.1 STOP list (structural, STOP-only; none promotes anything)

| # | STOP | reading that fires it |
|---|---|---|
| **S1** | the post-edit no-op sweep or key table departs from §2 / §2.3 | any non-PJM or backcast key move; the bare key ≠ `fb16fda2ddb0a94a`; `--no-retirement-sector-gate` ≠ `b518f5fe7d02f961` |
| **S2** | the solve's realized key ≠ `fb16fda2ddb0a94a`, or the HEAD guard trips | — |
| **S3** | any of the 14 forecast invariants non-PASS on the armed run | the bar is D67-ARM's / D75-R-ARM §5.1's: **14 PASS, 0 FAIL, 0 WARN** on the committed `pjm-t1h` sidecar; D75-R measured all 26 scored bands byte-identical and D78-R2's arm carried no invariant regression |
| **S4** | **the identity the mechanism asserts, on the armed run alone** (D78-R2's W2): any sector-1 row in `decided`, `entry_capped`, `floor_retained`, `throughput_deferred`, any `pipeline_events` row, or `retirements` with `reason == "economic"`, in any of the five years; or a year whose ledger lacks the `sector_gated` block | a sector-1 unit reaching any decision ledger means the partition is not what its own definition says |
| **S5** | a re-key of any file outside the PR's declared set (§1), or any edit to `retirements.py` | scope |

A STOP halts the lane and is reported; nothing is re-tuned in response.

### 5.2 Reported at full magnitude, gated on NONE (rule 14) — the numbers the charter names

| quantity | committed control `a9c66d8ea25acb9d` (D67-ARM) | Q55 only, `b518f5fe7d02f961` (D75-R §5.2, doc) | gate only, `bb6a60239d69508b` (D78-R2 §7, doc) | **armed run (Q55 + gate)** |
|---|---:|---:|---:|---|
| FC-3 `retire.total_gw` (actual 15.062) | 18.058 · FAIL | 17.294 · FAIL | 15.937 · **PASS** | expected **≤ 17.294** (sign: the gate can only reduce or leave unchanged economic exits, `scenarios.py` field comment); a FAIL→PASS crossing is **not an argument for arming** |
| `unit_recall_gt300` | 0.650 (13/20) | 0.650 (13/20) | **0.550 (11/20)** | expected 0.550 — a partition removing matched sector-1 exits must lose recall; Q55 does not touch the matched set |
| `false_retire` (GW · frac) | 8.065 · 0.447 | 7.596 | 7.166 · 0.450 | reported |
| window `economic` release precision | 0.122 | 0.129 | 0.146 | reported |
| 2025/26 clearing price ($/MW-day) | 358.267 | — | **236.945** | reported — the steep VRR limb (control position 0.998023 short of the requirement); Q55 moves the census, so the armed value is not predicted |
| **limb (d) LOYO on recall** | non-discriminating | — | non-discriminating | **cannot discriminate in either leg** (the control holds no recall-PASS fold); read as no evidence either way |

The one metric that improves under the gate (`retire.total_gw`, FAIL → PASS at D78-R2) is
**explicitly not a criterion in either direction**. A worse band would not have been an argument
against arming, and it is written here before the solve so it cannot become one after.

### 5.3 What the solve is expected to reproduce structurally

- **P-A** the `sector_gated` ledger block present in every year, with the gated set drawn from the
  2020-vintage plant table (D78-R2 §6: the block is absent in the control, present in the arm);
- **P-B** 2021 runs no screen (no `prior_results`), so its ledger is byte-identical in the two
  mechanisms' presence or absence — as in D67-ARM P-D;
- **P-C** economic exits executed in 2024 and 2025 read **0** under the gate at D78-R2 (its §7:
  8,693.255 / 700.901 / 0); with Q55 raising accredited VRE credit **down** (D75-R: −754.6 / −332.9 /
  −148.3 MW), the direction of any departure is toward *more* pressure on the merchant pool, not less
  — a non-zero 2024/2025 economic execution is reported, not a STOP.

---

## 6. The board, and the collision map — this lane is NOT the board writer

Checked at `8875af59`: `"D65-B-R"` occurs **0** times in `frontend/data/forecast/program-status.json`
and `ff-verdicts.json`; the `pjm-t1h` verdict's provenance still names
`run_id = pjm-2021-2025-realized-t1h-d57-clearing` (`session = capx-D57`), i.e. even D67-ARM's
registered posture has not reached the snapshot; the director's latest collision map (capx ledger
r#52 §0aw.4) names **D65-B-R the sole board writer**; **zero open PRs** at the time of writing. So:

- **THIS lane writes:** the armed solve's slim record under `results/capacity-hindcast/…-d78arm/`
  (the D67-ARM retention class — a REGISTERED shipped posture, not a rule 29(c) screen bundle), the
  canonical sidecar `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d78arm.json`, the
  `VERDICT_MAP` re-key (§2.2), the hindcast report, the FINDING, and the PJM shard cell.
- **THIS lane does NOT write:** `frontend/data/forecast/ff-verdicts.json` or `program-status.json`.
  The snapshot row is the board writer's; the FINDING records what that row must carry when it is
  written (the §5.2 magnitudes and the `pjm-t1h` provenance move to `…-d78arm`,
  `cache_epoch = fb16fda2ddb0a94a`).

The registration itself is **not** held: the sidecar + `VERDICT_MAP` + slim files land in this PR,
which is what the D67-ARM lane did under the same lock and what D78-R2 failed to do.

---

## 7. Collisions and execution order

- **`mechanism-matrix/PJM.js` `retirement_sector_gate` line**: D78-R3's unmerged `4d668500` rewrites
  the same line (its `O` evidence). This lane edits the `main` version to `fc: "K"` with its own
  evidence appended after the D78-R2 text. If `4d668500` merges first, the conflict is resolved by
  keeping D78-R3's evidence and appending this lane's — never by dropping either.
- `_pjm_config` is this lane's window (D75-R-ARM was its last writer, merged).
- No other lane names `results/cache.py`'s ledger head, the `--retirement-sector-gate` help string, or
  the `VERDICT_MAP` PJM rows in an open PR.

**Order:**
1. **This PRECOMMIT + the two probes + their ex-ante records**, pushed **before** the override.
2. The override + the re-pinned test + the CLI help string + the CLAUDE.md bullet + the cache-epoch
   entry + the PJM shard cell + the `VERDICT_MAP` re-key — one commit.
3. The **post-edit** probe runs (flags omitted): `no-op-measured.json`, `keys_measured.json`; must
   reproduce §2 / §2.3 exactly. Guards: `test_persisted_identity.py`,
   `check_cache_key_registration.py --base origin/main`, `check_mechanism_matrix.py --base
   origin/main`, `ruff`, the PJM override pin.
4. The solve: `--iso PJM --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized
   --entry-screen-diagnostics --out-dir results/capacity-hindcast/pjm-2021-2025-realized-t1h-d78arm`,
   HEAD-guarded (`H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`),
   years sequential (rule 12), PJM solo. Then `score_capacity_hindcast.py --bundle … ` and
   `--flip-gate-extras`, `register_forecast_run.py --bundle …`.
5. The FINDING, the slim record, the sidecar — one commit. Blob-verify every pushed file ≥300 lines
   (rule 27).

**Rebase discipline:** between steps, never during; no commit while the solve runs.

---

## 8. What this lane does NOT claim

It moves **no** `ScenarioConfig` default, no other ISO, no backcast keeper, no marker or freeze file,
no calibration determination, and no `retirements.py` logic. It re-opens no adjudicated cell. It adds
no CLI surface. It does not re-litigate D78-R3's open items (the derivation rule's false-positive
class, its one-sidedness, the unrecoverable `max |delta|`), which stay routed. And it does not claim
the arm closes what the record says it does not: `unit_recall_gt300` **falls**, `false_retire` stays
FAIL, and the CT / ST / oil E&AS operand (D57 §4, the D12 scarcity-basis object) remains the named
successor for the retirement bands.
