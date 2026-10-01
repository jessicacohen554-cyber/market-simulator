# FINDING — PJM's "structural summer-scarcity miss" is a silently-degraded measured overlay, not a modelling gap (pjm-119, 2026-07-24)

**Charter:** the PJM C3a/C3c handoff — "the 2025 summer-scarcity structural miss",
opened by pjm-118 with three proposed lanes (outage completeness at summer peaks,
import abundance, scarcity price formation). **Verdict: none of the three lanes is
the cause.** PJM was scored `CALIBRATED` — all ten criteria PASS — six days before
the handoff was written, and both of the currently-failing gates regressed for
traceable, non-structural reasons. The dominant one is a **reproducibility defect**:
three of the keeper's measured overlays read the gitignored `data/clean` tree and
**silently no-op'd** when it was absent, which it is by default on a fresh
container.

---

## 1. The regression timeline

| run | date | C3a mean LMP 2025 | C3c tail 2025 | determination |
|---|---|---|---|---|
| pjm-114 east-interface | 07-16 | PASS | PASS — **40 h** | CALIBRATED-WITH-CAVEATS |
| pjm-115 unit-only | 07-18 | PASS | PASS — **40 h** | **CALIBRATED** (10/10 PASS) |
| pjm gasshape-interpfix | 07-19 | — | **40 h** | — |
| pjm-116 netrev **base** (= pjm-115 recipe, flag OFF) | 07-23 | PASS −9.4 % | **FAIL** | — |
| pjm-117 netrev-margin (flag ON) | 07-23 | **FAIL −10.6 %** | FAIL | NOT-YET |
| pjm-118 netrev-level (**current keeper**) | 07-24 | **FAIL −10.5 %** | FAIL — **15 h** | NOT-YET |

Two independent regressions, not one:

* **C3c** broke between pjm-115 and pjm-116 **on the byte-identical recipe** —
  `replay_keeper` of the same bundle with the flag off. The pjm-117 log recorded
  this as "a pre-existing scorer/commit drift from the keeper's `688e168`" and
  moved on. It is not a scorer artifact: `git diff 6d6867b HEAD --
  scripts/calibration_verdict.py` shows the C3c tail scoring semantics unchanged
  in that window (only a lib-extraction refactor and a docstring path rename).
  It is a real dispatch/price change.
* **C3a 2025** went −9.4 % (PASS) → −10.6 % (FAIL) as the measured cost of the
  owner-promoted `gas_offer_net_revenue_margin`, which compresses offers exactly
  when gas exceeds the anchor (2025: $3.52 vs $3.4483). This was pre-registered as
  the refutation signature, promoted anyway on rule 1 structural grounds, and is
  the *same* "margin-compressed high-gas gas offers" the pjm-118 attestation names
  as root cause of the cheap summer supply. Known and attributed, not mysterious.

## 2. Root cause of the C3c half — the mechanism was never applied

`ScenarioConfig.pjm_east_interface_cut` is the measured joint EMAAC import cut
(PJM's published "Average Eastern" reactive-interface limit). Its pre-committed
gate was adjudicated in `docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md` §10.6–10.7
and it is what moved C3c from 18 h to **40 h** — the mechanism that made PJM
CALIBRATED.

Its input is `data/clean/transfer-interface-limits/PJM/*.parquet` — the **curated
clean tree, which is gitignored, derived and disposable** (CLAUDE.md: "`clean/` →
curated, schema-validated Parquet (DERIVED, disposable, gitignored)"). A fresh
session container therefore starts with `data/clean` **empty**, and the loader
returns `None`:

```
$ ls data/clean/                     # fresh container
$ python -c "from market_sim.data.transfer_interface_limits import \
    pjm_eastern_interface_hourly; print(pjm_eastern_interface_hourly(2025, 8760))"
None
```

The consumption site in `scripts/run_calibration.py` then **logged a warning and
carried on with the cut absent**, leaving `pjm_east_interface_cut: true` in the
run's recorded `meta.json` / `run_config.json` and in the keeper's
`calibration_attestation.json` DOF ledger — which names it as a live measured
input with full provenance. Nothing in the registered artifacts distinguishes
"applied" from "skipped".

### 2.1 It is not one overlay — three of the keeper's measured inputs degrade

Every one of these is `true` in `results/calibration/pjm_netrev_retune/meta.json`
and every one silently falls back when its partition is missing:

| keeper flag | clean datatype | silent fallback | consequence |
|---|---|---|---|
| `pjm_east_interface_cut` | `transfer-interface-limits` | group skipped | the EMAAC cut disappears; cheap west→east energy meets the summer peak |
| `pjm_measured_interface_limits` | `transfer-interface-limits` | static TTC kept | per-link measured hourly ratings replaced by statics |
| `measured_ramp_capability` | `ramp-capability` | class ramp fractions | feeds the reserve co-opt's deliverable ramp → moves reserve prices |

Observed directly in this session: a keeper-recipe build on the untouched
container logged `measured_ramp_capability: no clean ramp-capability partition for
PJM ... falling back to class ramp fractions`, and after
`scripts/regenerate_clean.py transfer-interface-limits ramp-capability` the same
build instead logged `PJM 2025: measured EAST interface cut on 2 link(s) — joint
EMAAC import cap follows Average Eastern (hourly 2210-10769 MW, mean 8149)` with
the ramp warning gone.

### 2.2 The session's own log corroborates it

The pjm-117 calibration-log entry records:

> "PJM DA-virtuals (`pjm_da_virtual_bids`, in the keeper recipe) were re-fetched
> from DataMiner2 (gitignored raw) to replay."

That session therefore *did* hit a gitignored-input problem and fix it — for the
one mechanism that **hard-fails** when its input is missing. It says nothing about
regenerating the clean tree, because the three overlays above only *warn*. The
session repaired exactly the dependency that raised and silently lost the three
that did not. This is the whole defect in one line: the guard, not the analyst, is
what decides whether a missing input gets noticed.

### 2.3 Why the keeper's own narrative is the signature of the cut being off

The pjm-118 attestation's root cause — "too much cheap supply meets summer peaks,
so scarcity never forms" — is, verbatim, the pre-east-cut diagnosis:

> §8.1(2): "cheap western/ComEd energy flows east essentially unconstrained and
> imports backfill, so the system still needs system-wide shortage to clear $200
> in any zone."
> §10.2: "a net ~+3.0 to +3.6 GW excess west→east wheel in scarcity hours … the
> model imports the east's scarcity away."

And the numbers land on the pre-cut side of the ledger: 2025 tail 15 h (pre-cut
pjm-113: 18 h; post-cut pjm-114: 40 h); 2024 tail 1 h (pre-cut 1 h; post-cut 9 h).

**Partially refuted by §3, recorded here as written.** The narrative match holds
for the *tail*, but the pjm-118 attestation's other headline number — the June
−19.9 $/MWh undershoot — is **not** the unconstrained wheel: §3 measures it at
−20.1 with the cut fully live. The narrative-match argument was therefore right
about C3c and wrong to sweep the mean-price miss in with it; the direct
measurement governs.

## 3. Measured adjudication (2025 diagnostic probe)

Decision rule, fixed before the result was read: replay the **pjm-118 keeper
recipe byte-faithfully** (`replay_keeper`, no `--set`, no offer-curve change) for
2025 with the clean partitions **present**, so the recipe's own
`pjm_east_interface_cut` actually applies. The only delta versus the registered
keeper solve is the availability of the derived input.

* If the tail returns toward the pjm-114/115 level (**≥ 26 h**, the scorer's PASS
  band floor for 2025), the keeper's registered 15 h is **inconsistent with its
  own recipe**: the cut cannot have been live, and the "structural
  summer-scarcity miss" is an artifact of the degraded overlay.
* If the tail stays near 15 h, the degradation is real but not the C3c cause, and
  the handoff's structural lanes stand.

**Result: the C3c half is CONFIRMED; the C3a half is REFUTED. A clean split.**

Probe `results/probes/pjm119_eastcut` (2025 only, diagnostic, never registerable
per rule 16), read out by `scripts/probes/pjm119_eastcut_readout.py` on the
dashboard's own definitions:

| metric | pjm-118 keeper (registered) | pjm-119 probe (same recipe, partitions present) | actual |
|---|---|---|---|
| C3c any-zone tail > $200 | 15 h (**FAIL**) | **39 h (PASS)** | 59 h |
| C3a load-weighted mean LMP 2025 | −10.5 % (FAIL) | **−10.7 % (still FAIL)** | $46.10 |
| system LMP max | $324 | $375.7 | — |

* **C3c is the artifact.** 15 h → **39 h** with *zero* recipe change — the delta
  is only that the derived partition existed. That is one hour off pjm-114/115's
  40 h, well inside the [26, 102] PASS band, and it settles the attribution: the
  registered keeper's 15 h is unreachable from its own recipe with the cut live,
  so the cut cannot have been applied. The east cut logged
  `measured EAST interface cut on 2 link(s) … mean 8149 MW` in this run and
  nothing at all in the keeper's environment.
* **C3a 2025 is NOT the artifact, and stays open.** −10.5 % → −10.7 % is noise;
  the monthly signature is unchanged (Jun −20.1 vs −19.9, Jul −9.0 vs −9.8). The
  east cut is C3a-neutral. Attribution therefore rests where the pjm-117 A/B
  already put it: base arm (margin flag OFF) −9.4 % **PASS** → margin arm ON
  −10.6 % **FAIL**. The ~1.2 pp that crosses the ±10 % band is the measured cost
  of the owner-promoted `gas_offer_net_revenue_margin`, not a missing overlay and
  not an unmodelled outage.
* **A sharper residual for the next session.** With the cut live the model now
  reaches the *extreme* tail (39 of 59 hours > $200; max $376) while still
  running **$20/MWh light on the June mean**. So what is left is not a
  scarcity-formation failure at the top — it is a **summer shoulder-hour price
  level** miss, exactly the "misses the event shoulders" signature of diagnosis
  §1. Any further structural work should be scoped to the shoulders, on a
  residual re-measured with the overlays live.

## 4. The fix — an enabled measured mechanism never silently no-ops

Follows the `pjm_da_virtual_bids` precedent already in the codebase, whose loader
raises `FileNotFoundError(... "the mechanism never silently no-ops")`.

**The guard goes in the LOADER, not the call site.** Every one of these loaders is
reached only from a site already gated on its `ScenarioConfig` flag, so a missing
input is unambiguously a misconfiguration — and guarding at the loader protects
every present *and future* caller. That is the whole point of the finding: the
guard must not depend on the analyst remembering to add it at each new call site.

1. **`data/transfer_interface_limits.py`** — `pjm_eastern_interface_hourly` and
   `pjm_interface_ttc_hourly` now **raise `FileNotFoundError`** instead of
   returning `None`, on a missing partition, a missing "Average Eastern" series,
   or (for the per-link overlay) a partition carrying none of the mapped series.
   Return types narrow accordingly.
2. **`data/ramp_capability.py`** — `load_measured_ramp_capability` raises instead
   of returning `{}` when the ISO has **no** partition.
3. **`tests/test_measured_overlay_no_silent_noop.py`** (new) — asserts each guard
   raises with the missing input simulated, that the gated fleet build propagates
   it (a solve stops rather than quietly reverting), plus a positive control that
   a present partition still resolves to ONE one-sided group over BOTH EMAAC
   links.
4. **`tests/test_curate_transfer_interface_limits.py`** — the three assertions
   that pinned the old `None` contract become `assertRaises`. The contract change
   is deliberate and now tested in its new form.

The fallbacks *inside* a present partition are deliberately kept, and pinned by
test, so the hard-fail is not over-read: an individual series absent from a
populated partition still falls back to that link's static rating, and an
individual plant absent from a populated ramp partition still falls back to its
class ramp fraction. What is refused is losing a **whole mechanism** in silence.

Deliberately *not* done: no scalar moved, no offer surface touched, no new tunable
introduced, and no change to `scripts/run_calibration.py` or
`data/fleet/arrays.py` — both exceed the API push path's safe emission size, and
guarding at the loader made editing them unnecessary (rule 27).

## 5. Consequences

* **The handoff's three lanes are scoped against a residual that no longer
  exists.** Lane 1 (CT/CC <5-day summer outage intake), Lane 2 (seam import
  abundance) and Lane 3 (reserve curve steepness) were each aimed at the missing
  scarcity tail — and the tail is back at 39 h without any of them. The
  proposed unit-level max-gen-event outage intake is a substantial data-intake
  charter aimed at a ~1.5 GW phantom whose removal was already measured (pjm-112)
  to move the tail by **+1 h**; it should not be opened. What survives is the
  narrower, re-measured residual of §3: the **June/July shoulder price level**,
  with the extreme tail now formed correctly.
* **C3a's remaining miss is an owner decision, not an open investigation.**
  `gas_offer_net_revenue_margin` carries the ~1.2 pp that fails C3a-2025, was
  adopted knowingly on rule-1 structural grounds against its pre-registered
  refutation signature, and pjm-118's level retune already spent the sanctioned
  offer DOF closing C1 instead. Reverting it is the owner's call; nothing in this
  finding touches it.
* **Governance.** The pjm-118 keeper's attestation asserts three measured inputs
  its solve did not apply — the C3c evidence in §3 is decisive on the east cut.
  The keeper record should be superseded by the re-solved 3-year bundle
  (`results/calibration/pjm119_overlay_restore`, pjm-118 recipe verbatim with the
  partitions present), and `governance.levers_trace_to_measured_input` is only
  true of a run whose inputs were verified present. A run record should carry
  that verification rather than relying on the config flag alone.
* **Systemic exposure beyond PJM.** The same warn-and-degrade pattern exists for
  `gtc-limits`, `emissions`, `nyiso-downstate-gas` and
  `nyiso-renewable-curtailment`, and every ISO keeper that names a clean-tree
  overlay is exposed to the identical defect on a fresh container. A cross-ISO
  sweep — either extending the hard-fail posture or recording a per-run
  manifest of which measured partitions resolved — is the follow-on charter. The
  cheap immediate mitigation is to run `scripts/regenerate_clean.py` before any
  calibration solve in a new container.

## 6. Guardrail review

* **Rules 1/11** — no lever tuned to any residual; the finding *removes* a
  mechanism-loss rather than adding a fitted one. The probe's decision rule was
  fixed before its result was read (§3).
* **Rule 13** — measured/published interface limits and measured ramp capability
  are the explicitly admissible class (physical/security limits, regenerating
  forward, responsive to conditions); nothing here pins an outcome.
* **Rule 12** — the 3-year re-solve runs years strictly sequentially, one fresh
  process each (a single 3-year PJM per-plant process peaks ~16 GB and OOMs).
* **Rule 16** — the 2025-only probe is a diagnostic, explicitly never registerable
  as a keeper; a keeper re-solve covers 2023+2024+2025 in one bundle.
* **Rule 22** — 2023–2025 only; no holdout year touched (PJM has no
  calibration-complete marker).
* **Rule 24** — every change is PJM-scoped or ISO-generic guarding; no other ISO's
  curve moved.
* **Rule 27** — no core file ≥300 lines was rewritten over the API: the guards
  land in two small loader modules (248 / 162 lines), each pushed as its exact
  on-disk bytes and blob-verified against the local `git hash-object` after the
  push (`501a3457…` / `da4b679f…`, both matched).

## Pointers

* Regression origin: `docs/calibration-log/pjm.md` 2026-07-24 (pjm-117 entry,
  "fails in BOTH arms — a pre-existing scorer/commit drift").
* The mechanism this restores: `docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md`
  §10.5–10.7.
* Superseded framing: the PJM C3a/C3c summer-scarcity handoff (2026-07-24).
