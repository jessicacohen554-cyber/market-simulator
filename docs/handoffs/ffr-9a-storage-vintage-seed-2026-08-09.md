# FFR-9A — hindcast storage base fleet seeds from the run's own EIA-860 vintage

**Session.** FFR Wave 9, fix + measurement lane (manager dispatch Addendum AG.2
rider 2, under the owner-re-opened D-21(a) completion mandate). Branch
`claude/ffr-9a-storage-vintage-seed-2su81u`, off `origin/main` `ae7bd5e`.
Model: Fable (rule 27 — capacity-evolution core).

**Charter.** Repair the T1-FF hindcast posture's storage-fleet trajectory: the
base fleet seeded from a present-day scalar instead of the run's own
vintage-measured fleet (the FFR-3V leak's storage sibling), inflating the arm's
storage power to ~30 GW by the 2024 solve against ~10 GW actual — the measured
DOMINANT remaining input error on the forward price object (FFR-8B §3–§4:
+7.3–8.8 GW at p1 on E1's reserve quantity; E2's AS withholding held inert by
the same over-build). NO tuning, NO arming beyond the measurement arm, NO
keeper contact, NO backcast-registry touch.

**Evidence cited, never re-derived:**
`docs/handoffs/ffr-8b-rebase-dispersion-2026-08-09.md` §2.3 (the additions
METRIC passes at −5.0 % — the BASE seeding is the error), §3 (the B̃→B
storage-term step), §4 (the de-prioritization evidence);
`docs/handoffs/ffr-3v-fix-2026-08-08.md` (the pattern mirrored);
`docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md` §5 (the
`storage_measured_base_fleet` machinery REUSED, not parallel-built), §7 D-3 and
D-5 (the ERCOT scalar and the five-ISO scalar exposure, routed there to this
judgment).

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE either arm was launched.
Nothing in §1 changes after. The fix itself (§1.2) was built and committed
before this prereg — it is an input-basis correction identified from the
committed evidence above, with zero parameters identified from any solve this
session runs.*

### 1.1 The leak, measured at this head

`runner.py`'s storage seam (the FFR-4D `measured_storage` predicate) tested
`config.mode == "backcast"`. A capacity hindcast is `mode="forecast"` +
`hindcast=True`, so it fell through to `build_default_storage` — the
**present-day forward scalar** `STORAGE_BASE_FLEET_MW` (ERCOT mid 17,000 MW) —
even though `set_eia860_vintage` had already pointed every EIA-860 loader at
the run's `vintage_<year>/` snapshot. Exactly the FFR-3V renewable-pool leak,
one seam over.

Measured at this head (`load_eia860_storage` — battery + pumped storage — at
`start_year = vintage + 1` against each committed `vintage_<year>/` sheet,
vs what the shipped path supplies, scalar + PS prepend):

| ISO, vintage 2020 | shipped (scalar + PS) | vintage-measured | ratio |
|---|---:|---:|---:|
| ERCOT | 17,000.0 | **223.1** | **76.2×** |
| CAISO | 16,993.6 | 2,022.4 | 8.40× |
| PJM | 5,603.3 | 5,357.6 | 1.05× |
| MISO | 2,887.0 | 2,142.4 | 1.35× |
| NYISO | 1,490.0 | 1,308.1 | 1.14× |
| NEISO | 2,569.0 | 1,924.2 | 1.34× |

ERCOT by vintage (battery + PS; PS = 0 in ERCOT), the T1-FF lane's own seed:

| vintage | measured MW | measured MWh | scalar |
|---|---:|---:|---:|
| 2018 | 94.3 | 54.0 | 17,000 |
| 2019 | 114.2 | 106.0 | 17,000 |
| **2020** | **223.1** | **231.6** | 17,000 |
| 2021 | 792.4 | 998.7 | 17,000 |
| 2022 | 2,086.9 | 2,682.8 | 17,000 |
| 2023 | 3,814.4 | 5,554.0 | 17,000 |
| 2024 | 8,052.5 | 11,498.0 | 17,000 |

Why it is the dominant error and not a cosmetic mis-seed: the base is what the
endogenous entry screen ADDS to. FFR-8B §2.3 measured the additions decision
basis itself INSIDE its score band (13.0 vs 13.691 GW actual, −5.0 %, PASS)
while the arm's total storage power still reached ~30 GW by the 2024 solve
against ~10 GW actual — the 17 GW phantom base is arithmetically the error.
Downstream, the storage-AS term it feeds (0.35 × fleet) inflates E1's reserve
quantity by +7,289 / +8,805 MW at p1 (2024 / 2025, FFR-8B §3's B̃ vs B step —
the single largest model-side inflator on that arm) and swallows the ~4.6 GW
responsive requirement that keeps E2's `as_hold` identically zero.

**The FFR-4D D-3 judgment, exercised for the hindcast posture.** D-3 routed
ERCOT's hand-entered scalar row (17,000 shipped vs 13,709.3 by the registry's
own EIA-860 construction) to "ERCOT's lane to judge". For the HINDCAST posture
the judgment is: the scalar — under either value — is the wrong OBJECT, not
the wrong number. It is a 2026 forecast base standing in for a 2020 vintage
fleet; no re-derivation of the row can fix a vintage/as-of misalignment. The
hindcast therefore bypasses the row entirely in favour of the vintage-measured
fleet, and the row's forecast-lane value is left exactly as D-3 routed it —
untouched, ERCOT's forecast lane's to judge.

### 1.2 The fix (committed `57cb3e7`, before this prereg)

The seam now resolves through one predicate,
`model.storage.measured_storage_base_fleet_active(config, iso)`:

* **Backcast leg — byte-identical to FFR-4D.** `storage_measured_base_fleet`
  × `STORAGE_MEASURED_BASE_FLEET_ISOS` (CAISO only), fleet as of the solve
  year. No keeper moves.
* **Hindcast leg — the fix.** `mode != "backcast"` × `hindcast=True` ×
  `eia860_vintage_year is not None`: the base fleet is
  `load_eia860_storage(iso, start_year, config)` against the already-armed
  vintage dir — the vintage year-end battery fleet plus pumped storage, real
  zone assignment, real durations. Called at `start_year`, every vintage-sheet
  unit has a pre-window COD, so the seed carries **no intra-year ramp profile**
  (the FFR-3V third-leg hazard, pinned by test). All later growth stays
  endogenous — the storage entry value stack (spec §5.5) is untouched.
* **Plain-forecast leg — untouched.** `hindcast=False` keeps the scenario
  ladder even when a vintage is set, mirroring the runner's vintage-arming
  predicate.

Rule alignment: **rule 13 [R-MEASURED]** — the vintage sheet is precisely what
a run at that cutoff may know, a physical fleet inventory, regenerating for
any vintage (measured 2018–2024 above) and responsive to changed conditions.
**Rule 14 [R-ACCURATE]** — measured beats the scalar. **Rule 19 [R-ONE-MECH]**
— the seed REPLACES the scalar on the path it governs. **Rule 24
[R-REGISTRY]** — no new channel; the governing field is the existing
registered `storage_measured_base_fleet`. **Rule 28** — no `ScenarioConfig`
field added, so no matrix row is owed under duty (c); duty (b) citations are
updated in this PR.

**Gating choice: UNGATED** (the FFR-3V precedent, stated as the charter
requires). The change cannot reach anything but a capacity hindcast: a
backcast takes the pre-existing FFR-4D branch unchanged, and a plain forecast
keeps the scalar — all three no-op halves pinned by
`tests/unit/model/test_storage.py::TestHindcastStorageVintageSeed` (truth
table over every ISO × mode, seed content at the vintage, no-ramp). The only
affected artifacts are hindcast runs — measurement evidence expected to be
superseded, with no keeper among them. A default-off gate here would be an
armed answer key (rules 26/14). The hindcast leg is deliberately NOT scoped by
the frozenset: the frozenset exists to keep the five non-CAISO **keepers**
byte-identical, and a hindcast is not a keeper; scoping a measured-data
correction per-ISO where no keeper is at stake would gate an accurate input
behind an enrollment (rule 14), and the FFR-3V renewable seed is likewise
all-ISO.

**Cache:** no `ScenarioConfig` field moves, so **no key moves anywhere** (the
pinned default key regression and `check_cache_key_registration.py` pass
unchanged) while hindcast output moves. Same-key invalidation, recorded as
**cache epoch 2026-08-09** in `results/cache.py`.

**EPOCH STATEMENT (for the manager; FH-4-ERCOT is HELD for this landing).**
This fix is ungated, so it **re-bases every capacity hindcast in every ISO at
this head** — T1-H plain hindcasts, T1-X crossovers, T1-FF full-forward legs.
Every committed `frontend/data/hindcast/` sidecar — the FFR-8B re-base
`ercot-2021-2025-t1ff-armr-ffr8b-base` included — is pre-epoch evidence: the
record of what the harness did, not re-runnable results. The FFR-8B §2 record
is superseded AS BASELINE by this session's control+treated pair for any run
at or after this epoch (the same clause FFR-8B applied to FFR-8A §4).

### 1.3 The measurement — paired arms, fixed before launching

Paired ERCOT T1-FF arms at THIS head, 4 LP solve-years each (2021, 2023,
2024, 2025; 2022 bridged), years SEQUENTIAL within each invocation (rule 12):

```
# control — the ffr8b-base recipe VERBATIM, pre-fix harness
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9a-control

# treated — the SAME recipe + the storage vintage seed fix
  ... --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9a-storageseed
```

**Arm construction (the FFR-3V §5 design note, adopted in advance).** The fix
is ungated, so the arms differ by CODE STATE, not by flag. The control runs
with `src/market_sim/runner.py` + `src/market_sim/model/storage.py` restored
in the working tree to `origin/main` (`ae7bd5e`, the pre-fix bytes — every
other changed file is comments/tests only); the treated arm runs at this
branch head. The arms run **SEQUENTIALLY in the same tree** — FFR-3V measured
that relocating the source root moves `REPO_ROOT` and the config hash, so the
checkout-swap-in-place is the only construction where the sole difference is
the fix; additionally this container has 15 GB RAM / 4 cores, below what two
concurrent per-plant ERCOT invocations need (rule 12's own cap note). Both
arms cold, each in its own `--out-dir` (the FFR-4D/3V same-key hazard: the
arms share a cache key, so a shared dir would silently re-use the first
bundle).

**Reproduction gate (control).** The control is expected to reproduce
**FFR-8B §2 BY CONTENT**: its read set (the §1.4 probes below) against the
committed `docs/handoffs/ffr-8b/rebase-reads-2026-08-09.json` +
`e1-dispersion-2026-08-09.json`. Reproduction failure is diagnosed before the
treated arm is compared to anything.

**Bookkeeping reads.** The runtime `cache_key=` line of each arm and the
ledger path `<out-dir>/ERCOT/<runtime-key>/`, verified before believing any
zero. No registered field moved since FFR-8B measured `816031a3308cccde`, so
BOTH arms are expected at that key; identical keys across materially different
output is the D-13 hazard doing its job (the epoch entry records it), while a
DIFFERENT key is explainable only by a registered-field change on main since
2026-08-09 and is diagnosed before proceeding.

**Holdout posture.** Solve years {2021, 2023, 2024, 2025}: the enumerated
hindcast seed year plus training-tier years; 2022 bridged, never solved, no
file for it opened. The holdout freeze state is read at launch; no marker is
spent, no out-of-training year is approached.

### 1.4 Pre-registered reads (R1–R5)

All read from the arms' own ledgers/dumps and the two FFR-8B probes re-run
VERBATIM per arm (`scripts/probes/ffr8b_rebase_reads.py`,
`scripts/probes/ffr8b_e1_dispersion.py`, each with `--bundle <arm-dir>`).
Every delta reported at FULL MAGNITUDE; expectations are to test, never
targets.

* **R1 — the storage fleet trajectory** by solve year vs ~10 GW actual (2024):
  base + additions, power AND energy. Control expectation: base 17,000 MW
  (the scalar), total ~30 GW power by the 2024 solve (FFR-8B §2.3).
  Treated expectation, **exact on the base**: 223.1 MW / 231.6 MWh — the
  vintage-2020 measured fleet. Additions stay endogenous; NO magnitude is
  pre-registered for the treated total (what the entry stack builds off the
  corrected base is the measurement). If the entry stack itself proves
  defective against the corrected base, that is a FINDING to record, not a
  repair to improvise.
* **R2 — the E1 storage-term step** (FFR-8B §3's B̃ vs B, from the dispersion
  probe's `storage_basis_Btilde_vs_B` and the dump's `storage_as_mw`): does
  the +7,289 / +8,805 MW p1 inflation collapse toward the measured
  storage-AS series? Expected DIRECTION: the arm's storage-AS scalar falls
  with the corrected fleet, shrinking the step. Magnitude not pre-registered.
* **R3 — E2's `as_hold`**: does the AS withholding come ALIVE once the
  storage AS share stops swallowing the ~4.6 GW responsive requirement?
  FFR-8B §2.1: `as_hold` identically 0 at every screen, storage AS share
  5.95–10.5 GW. Expected DIRECTION: at early screens (fleet near the 0.22 GW
  seed) the storage AS share collapses and `as_hold` can go nonzero for the
  first time; later screens depend on the endogenous build. Recorded either
  way — a still-inert E2 is a finding, not a failure of the fix.
* **R4 — the price side, FFR-8B §2.1 re-run verbatim**: per-screen
  (into-2022/2023/2024/2025) mean / max / h>$100 / h>$1000 / adder mean vs
  the control AND vs measured (2024: 161 h > $100, mean $26.82, max $3,060;
  2025: 217 h, $32.49, $1,570); per-fuel replica margins vs the FFR-6A bars
  and replica-at-measured-prices columns. **Into-2025's 8-vs-217 undershoot is
  the number to watch, at full magnitude, never a target.** Expected
  DIRECTION: removing phantom storage lowers E1's reserve quantity at every
  screen priced off a thin fleet → more scarcity content at the early
  screens; the late screens depend on the endogenous build response (FFR-8B
  §2.1 measured exactly this inversion pattern on the VRE seed — the
  expectation carries the same caveat).
* **R5 — the exit/entry census**: (1) in-window economic executions must stay
  ≈ 0 — ANY in-window economic execution is a FALSIFICATION signal per
  FFR-7C, never a success; (2) the gas_st false wave must stay GONE (FFR-8B
  §2.2: zero pipeline events); (3) the additions decision basis vs 55.4 GW
  actual, per tech — reported, not targeted (the entry economics are
  FFR-4/5 lanes' objects); (4) the coal cohort's event sequence and the
  per-year reserve margins (the §4.2.4 cap-interaction context); (5) the
  `entry_capped` census.

**What would falsify the fix** (as opposed to surprising us): treated R1 base
≠ 223.1 MW / 231.6 MWh; arm cache keys differing; any movement in a backcast
or plain-forecast output (pinned by test). R2–R5 landing against expectation
is a finding to report, not grounds to revert (rule 1 [R-STRUCT]: the vintage
seed is the structurally correct base whatever it does to any residual; rule
14 forbids restoring the scalar because it flattered something).

**Registration commitment.** BOTH arms register in the HINDCAST namespace
(`scripts/register_hindcast.py`, `meta.kind="full_forward"`, ids
`ercot-2021-2025-t1ff-armr-ffr9a-control` / `-storageseed`) REGARDLESS of what
the reads show. NEVER the backcast registry — the backcast CI gates stay blind
to this namespace.

### 1.5 What this lane will NOT do

No tuning toward any residual (the ~10 GW actual, the 217 h, the measured
RTOLCAP distribution included), no arming beyond the measurement arm, no
keeper contact, no promotion, no backcast-registry touch, no bar re-levels, no
signal scaling. The FFR-8B Phase-2 escalation (commitment dispersion) stays
escalated — not this lane's. The storage entry value stack is not modified —
defects there are FINDINGS. If any step had required inventing a parameter,
the instruction was STOP and escalate; none did.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*
