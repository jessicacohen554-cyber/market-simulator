# FINDING — caiso-160 / NYISO: the CT meter screen re-based onto nyiso-113, and what the control caught

**Session:** caiso-160 · **Date:** 2026-08-03 · **ISO:** NYISO
**Pre-registration:** `PREREG-caiso160-nyiso-ct-heat-rate-rebase-2026-08-03.md`
**Outcome:** **PROMOTED** — NYISO keeper → `2026-08-03-nyiso160-ctmeter-screen-b`

---

## 1. What this closes

caiso-159 promoted the caiso-156 CT heat-rate meter screen (`f6238a5`) into the
CAISO and NEISO keepers and **could not** promote NYISO. Its §8 item 1 is now
closed: the screen is promoted in **all four ISOs that consume the artifact**.

The blocker was not the screen. It was that nyiso-113 promoted
`2026-08-02-nyiso-113-li-locational` **underneath the caiso-158 arms while they
solved**, so that arm carried `nyiso_li_locational_reserve=False` against a
keeper that arms it. Promoting it would have dropped a **published Zone-K
locational reserve requirement** to gain an input correction — a rule 14
`[R-ACCURATE]` regression committed in the name of rule 14.

This session re-solved the pair on the nyiso-113 recipe so the two compose.

---

## 2. The promotion

| | value |
|---|---|
| keeper | `2026-08-03-nyiso160-ctmeter-screen-b` (bundle `nyiso160_ctmeter_screen_B`) |
| control | `2026-08-03-nyiso160-ctmeter-control` (bundle `nyiso160_ctmeter_control_A`) |
| determination | CALIBRATED-WITH-CAVEATS — **unchanged** |
| grade | 9 scored / 8 target / 1 ledgered / 0 fails — **unchanged** |
| criteria | all 9 verdicts **identical** to the incumbent (C3c the sole ledgered caveat) |
| C1 | all 14/14 · free 10/10 — **unchanged** |
| DOF ledger | (30 entries, 6 residual) — **carried verbatim** |
| config delta | **zero recipe changes** |

**Promoted on rule 14, not on fit.** The scorecard did not move and was never
expected to. Both arms replay the keeper's own `meta.json` kwargs via
`replay_keeper.py` with **no `--set`**, so the zero delta is *structural* rather
than asserted.

### The input delta

`campd_ct_heat_rates_NYISO.csv`, `f6238a5^` (md5 `749f4ff…`) → HEAD (md5 `6fb8543…`):

* cap-weighted applied net HR **12.0769 → 12.4355 (+0.3586)** — the **largest of
  the six ISOs** (CAISO +0.176, NEISO +0.171, PJM +0.069, ERCOT +0.063, MISO +0.030)
* **one-sided dearer**: 17 plants dearer, 0 cheaper, 2 unchanged; 19/19 still
  applied; no flag changes; 80 → 79 unit rows
* only two plants move > 0.5 — **Gowanus 15.2804 → 16.9538** and **Narrows
  15.7537 → 16.7814**, both NYC in-city CTs whose sub-6.0 loaded hours were
  diluting the meter low

### K3 liveness — the prediction reproduced

caiso-158 measured this artifact against the **nyiso-112** base. caiso-160
measured it against **nyiso-113**. The agreement is close to exact:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CT_PEAKER ΔTWh — predicted | −0.012 | −0.005 | −0.036 |
| CT_PEAKER ΔTWh — **measured** | **−0.0121** | **−0.0047** | **−0.0359** |
| λ Δ% — predicted | +0.028 | +0.020 | +0.080 |
| λ Δ% — **measured** | **+0.030** | **+0.024** | **+0.079** |

Direction as pre-registered (P1): the artifact is one-sided dearer, so the class
re-prices up the stack and dispatches less. C3c untouched (P4): 12/8/68 h > \$200
with identical max λ in both arms.

**"No criterion flips" is not "inert."** K3 shows real energy moving in
thousands of hours; the screen re-prices the class without moving the scorecard.
Those are different claims (caiso-158 §7).

---

## 3. The control arm was solved against the handoff, and it earned its compute

The caiso-159 handoff said: *"NO CONTROL RE-SOLVE NEEDED — `nyiso113_lilocational_B`
IS the control."* That premise **did not hold**. The keeper solved at `3746eda`;
**seven `src/market_sim` commits landed after it**, two touching paths this ISO
uses (`a0fc302` deletes the CT_CHP override triple and re-scopes
`caiso_ra_min_load_frac`; `9a54412` moves the reserve balance-row activity inside
the co-opt branch).

Each is *documented* solve-inert — which is precisely what caiso-146 recorded of
the commits that nonetheless left the outgoing CAISO keeper's sidecars diverging
**up to 3.2 GW on a class-hour**, cause still unidentified. Comparing a fresh arm
against a bundle solved at a different HEAD would have confounded the CT
correction with that drift beyond recovery.

### K2 result: bit-identical

The control replays the nyiso-113 recipe at **this** HEAD against the keeper's
**own pre-fix artifact**:

| year | max abs Δ MW, any P1 class-hour | control total | keeper total |
|---|---|---|---|
| 2023 | **0.000000** | 147.1621 TWh | 147.1621 TWh |
| 2024 | **0.000000** | 150.6234 TWh | 150.6234 TWh |
| 2025 | **0.000000** | 151.7383 TWh | 151.7383 TWh |

Two consequences:

1. The A/B delta in §2 is attributable to the **artifact alone**.
2. **The standing caiso-146 HEAD-drift item is answered in the negative for
   NYISO.** Whatever produced CAISO's 3.2 GW divergence does not reach this ISO.
   The item stays open for CAISO.

---

## 4. A new general defect: `config_drift` cannot see a moved default

**This is the session's most transferable result, and it is not a NYISO quirk.**

The premise guard fired with **four** value diffs vs the keeper:
`retirement_rule`, `entry_rate_limits`, `entry_commissioning_lag`,
`caiso_ra_min_load_frac`.

**None is a recipe choice.** Every one is a **shipped default that moved on
main** after the keeper solved (`24b1602`, `3e33f15`, `a0fc302`), recorded
identically by *both* arms — so the A/B is unaffected; only arm-vs-incumbent
differs.

`config_drift` is absence-aware, which is what caiso-159 built it for. But
absence-awareness does not help here: **a moved default and a changed recipe are
byte-indistinguishable** — the field is present on both sides with different
values either way. Left unhandled, the guard either blocks every promotion that
follows a default change, or gets bypassed by hand, which is worse.

### The remedy, and why it is not self-certifying

`gen_caiso160_attestation.DEFAULT_MOVES` enumerates each field with **the commit
that moved it** and **why it cannot reach a NYISO backcast**:

* `retirement_rule`, `entry_rate_limits`, `entry_commissioning_lag` — capacity
  evolution steps 3 and 5, **forecast-mode only**; a backcast solves a fixed
  historical fleet per year and never runs the evolution loop.
* `caiso_ra_min_load_frac` — re-scoped to CAISO under rule 25 `[R-ISO-SCOPE]`;
  every reader sits behind `caiso_ra_mustoffer and iso == "CAISO"`, and NYISO
  carries `caiso_ra_mustoffer=False`. A **recording** change, not a solve change.

The allowlist is honoured **only when the K2 bit-identity holds**. One non-zero
MW voids the exemption and stops the promotion. The evidence is the measurement;
the entry is only the hypothesis.

**Any ISO promoted after a default move will hit this.** The pattern belongs in
every lane's promotion path, not just this one.

---

## 5. Also found (not in scope, not acted on)

1. **`regenerate_clean` reports `[FAIL] ancillary-services: exit -6` on a
   *successful* run.** The log order is `34 partition(s) written.` →
   `terminate called without an active exception` → `[FAIL]`. That is a C++
   abort at interpreter **teardown**, after every write completed. All six NYISO
   2023–25 AS partitions verified readable (~96k rows each). A future session
   reading the `[FAIL]` alone would re-run 45 minutes of curation or abandon a
   solve on a false premise.
2. **A misleading cache log line.** `_cache_binned_fleet`'s skip branch logs
   *"Binned fleet cache for NYISO is up to date — loaded from
   `nyiso_fleet_binned.parquet`"*. Nothing is loaded — it is a **write-skip** of
   a side artifact, and `load_binned_fleet` has zero callers in the solve path
   (`eia860.py:1387`: "it is not consumed by dispatch"). The wording reads
   exactly like the stale-cache failure mode this lane's cold-solve rule exists
   to prevent, and cost a real investigation to clear.
3. **The `git push` 413 is misdiagnosed in the handoff.** It is **not** pack
   size. A 25 KB markdown commit 413'd; a 7 MB bundle commit pushed fine minutes
   later. The cause is a **stale base**: when `origin/main` has advanced to a
   commit the client lacks, git cannot find a common ancestor and tries to send
   the entire history. `git fetch origin main` first is the fix — which is what
   CLAUDE.md's "start fresh on main" is actually doing, and it deserves to be
   stated as a *correctness* requirement rather than hygiene.

---

## 6. DO-NOT-REDO

* **Do not re-test `measured_ct_heat_rates` as a mechanism.** It is an INPUT
  CORRECTION with zero `ScenarioConfig` surface. All six cells keep their
  existing per-ISO verdicts; only the note/evidence moved (rule 28b).
* **Do not read the promotion as evidence the screen improves the fit.** It does
  not move the scorecard in any of the four ISOs, and was never expected to.
* **Do not treat the committed keeper bundle as a same-HEAD control** without
  first checking whether `src/market_sim` moved since it solved. When it has,
  solve the control — §3 is what that buys.
* **Do not "fix" a `config_drift` value-diff by editing the allowlist to make it
  pass.** The allowlist entry is a hypothesis; K2 is the evidence. If K2 is
  non-zero the diff is real, whatever the entry says.
* **Do not re-open the caiso-158 or caiso-159 DO-NOT-REDO lists.** All stand.

---

## 7. Follow-up lane items (not done here)

1. **PJM A/B for the same artifact** — still the one lane never run, and now the
   *only* consumer ISO not re-based. Unchanged rationale for the cut: ~15.5 GB
   peak RSS against a 15 GB box, and the smallest predicted effect (+0.069
   cap-weighted). Routes: a bigger box, or `replay_keeper`'s per-year
   `--reuse-solved` chain, which keeps all three years in ONE bundle (rule 16).
2. **`cache_key` blindness to input-artifact provenance** — caiso-158 §8.1,
   still open. §4 here is its *sibling* at the config layer: the cache key cannot
   see an input's bytes, and `config_drift` cannot see a default's provenance.
   Both want the same fix — hash what was actually consumed.
3. **`DEFAULT_MOVES` should not live in one session's generator.** It is
   lane-general; it belongs beside `config_drift` in a shared module so every
   ISO's promotion path gets it.
4. **The caiso-146 HEAD-drift item stays open for CAISO** — closed here for
   NYISO only, by measurement.
5. **Retention vs holdout artifacts** — caiso-158 §6, still unaddressed;
   consider making holdout-validation runs retention-exempt.
