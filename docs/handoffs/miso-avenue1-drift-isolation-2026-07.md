# MISO avenue #1 — faithful-box re-solve / drift isolation (miso-84), 2026-07-24

**Status:** DONE (diagnostic). Keeper unchanged. This doc is the pushable record
of the miso-84 finding + the still-open sync follow-up, authored on the
`claude/miso-calibration-net-revenue-esg5o7` lane. It exists as a standalone
handoff because the API-only session that produced it cannot push the large/
binary dashboard artifacts nor safely rewrite the 410-line
`docs/calibration-log/miso.md` (rule 27). **Fold the "miso-84 entry" below into
`docs/calibration-log/miso.md` verbatim (it is already drafted there in the lane
working tree; if that tree was reclaimed, re-add it from here) and bump
`Next number:` to miso-85.**

## What was asked (handoff avenue #1)

The miso-83 owner-override promotion of the gas-offer net-revenue-margin form
downgraded MISO to NOT-YET on two NEW single-threshold crossings:

- **C1 fuelmix CC_REGULAR 2023** −8.62 TWh (over the ±8.0 band), and
- **C3b price_shape 2025** monthly-NRMSE 0.204 (over the ≤0.20 veto).

The handoff flagged (avenue #1) that ~1 % of both is this box's alternate-optimal
drift vs the keeper's original solve host, and that "until this is done, neither
crossing should be treated as a real miss." Task: re-solve the margin keeper AND
a **same-box BASE replica** (miso-81 recipe, `gas_offer_margin` OFF), score both
with the determination scorer so box drift cancels (BASE→MARGIN) and the
margin's own effect separates from the host difference.

## What was done

All `replay_keeper` of `results/calibration/miso81_phantom_outage`, per-year
`--reuse-solved` chains (rule 12, 15 GB box), scored via `calibration_verdict`:

- **MARGIN arm** (`--set gas_offer_margin=true`, full 2023-25 span) →
  `results/calibration/miso_netrev_margin`. Reproduces the miso-83 keeper bundle
  in place (attestation regenerated via the new
  `scripts/gen_miso83_attestation.py`; `legitimacy_diagnostics.json` +
  `metrics.json` written). Determination scored **NOT-YET**, basis "undocumented
  FAIL: fuelmix, price_shape" — **byte-faithful to the registered miso-83**
  (C1 CC_REGULAR 2023 −8.62, C3b 2025 0.204, inherited C3a-2025 −16.2 %,
  C3c 0/6/0 vs RT 30/37/88).
- **BASE arm** (no flag): 2023 full-year + 2025 single-year diagnostic probes
  (rule 16 — 1-year solves are throwaway diagnostics, NOT registered as keepers).

## Result — same-box scored (drift cancels between BASE and MARGIN)

| crossing | BASE this-box | MARGIN this-box | keeper host (registered) | box drift (host→base) | margin effect (base→margin) |
|---|---|---|---|---|---|
| C1 CC_REGULAR 2023 grid-delivered miss | **−8.97 TWh (FAIL)** | −8.62 TWh (FAIL) | −7.76 TWh (PASS) | **−1.21 TWh** | **+0.35 TWh (IMPROVES)** |
| C3b price_shape 2025 monthly-NRMSE | **0.200 (FAIL)** | 0.204 (FAIL) | 0.194 (PASS) | **+0.006** | +0.004 |

Context (the ~1 % drift signature, same scorer): C3a price_mean 2025 base
−15.7 % / margin −16.2 % / keeper −14.8 %; C3a 2023 base −3.3 % / margin −2.8 %;
C3b 2023 base 0.083 / margin 0.081.

## Adjudication — BOTH crossings are BOX-DRIFT-DOMINATED, not real margin misses

1. **CC_REGULAR 2023.** On this box the BASE (miso-81 recipe, no margin) *already*
   fails at −8.97 TWh — **worse** than the margin's −8.62. The margin *improves*
   CC_REGULAR by +0.35 TWh (below-anchor firming adds CC dispatch). The miso-81
   keeper's registered PASS (−7.76) came from its original solve host; THIS box
   drifts the identical recipe to −8.97 (a −1.21 TWh alternate-optimal shift). The
   miso-83 record's attribution — "the below-anchor firming *sheds* ~0.86 TWh of CC
   dispatch" — conflated box drift (−1.21) with the margin effect (+0.35): the net
   −0.86 vs the keeper is drift PLUS an offsetting margin *gain*. On a faithful host
   (base −7.76) the margin lands ≈ **−7.4 TWh → PASS**. The margin does not cause a
   CC_REGULAR miss.
2. **price_shape 2025.** Box drift (host 0.194 → this-box base 0.200, +0.006) and
   the margin (+0.004) contribute about equally; base alone already sits at the 0.20
   veto edge on this box. On a faithful host the margin lands ≈ **0.198 → PASS**.

**Conclusion (rule 1: separate real misses from box drift BEFORE structural work).**
Neither NOT-YET-driving crossing is a real margin miss: on the keeper's faithful
host both fall back inside tolerance, and the margin mechanism itself either
*improves* the gate (CC_REGULAR) or moves it by less than the host drift
(price_shape). MISO's **structural** state under the net-revenue-margin form is
unchanged from miso-81 — **CALIBRATED-WITH-CAVEATS** on the ledgered
{C3a-2025, C3c} + storage frontier (miso-82) — and the miso-83 NOT-YET is a
solve-host alternate-optimal sensitivity on two marginal gates, **not** a
structural regression and **not** grounds for structural work. No parameter was
touched (rule 1/10); the keeper bundle keeps its honest scored NOT-YET (we do not
manufacture a passing host).

**Owner call:** whether to re-read MISO's determination as CALIBRATED-WITH-CAVEATS
given the crossings are box noise. The science says the two fails are not real; the
registered number stays NOT-YET because this box (≈ the miso-83 host) genuinely
scores it there. Avenues #2 (CC under-dispatch), #4 (offer-surface grounding in the
margin framework), and #5 (holdout path) from the source handoff are unaffected —
avenue #1 simply removes the "real structural miss" reading of the two crossings.

## Still-open sync follow-up (needs a git-capable environment)

The full miso-83 keeper bundle was REPRODUCED and re-verified locally this session
(`results/calibration/miso_netrev_margin/`: 6 JSON sidecars + 6 `hourly/*.parquet`,
determination NOT-YET) — the expensive recipe replay from the lost source container
is redone. But the push wall from the source session persists: `git push` is
forbidden (CLAUDE.md; the git relay 413s) and `push_files`/`create_or_update_file`
take a text `content` string, so a model cannot author the 6 **binary**
`hourly/*.parquet` sidecars, the ~968 KB gzip-base64 `runs/<id>.js` payload, or the
49 KB generated `status/MISO.js` as tool-call content. So
`2026-07-24-miso-83-netrev-margin` REMAINS in `scripts/lib/known_unsynced_keepers.py`
(CI stays green via its artifact-absent tolerance).

**To finish from a git-capable env** (recipe unchanged from the source handoff):

```
# 1. reproduce the keeper bundle (per-year chained, rule 12)
replay_keeper.py results/calibration/miso81_phantom_outage --set gas_offer_margin=true \
    --years 2023        --out-dir results/calibration/miso_netrev_margin_y23
replay_keeper.py ... --set gas_offer_margin=true --years 2023 2024 \
    --out-dir results/calibration/miso_netrev_margin_y2324 --reuse-solved <y23>
replay_keeper.py ... --set gas_offer_margin=true --years 2023 2024 2025 \
    --out-dir results/calibration/miso_netrev_margin      --reuse-solved <y2324>
# assemble class_hourly_2023 (from y23) + class_hourly_2024 (from y2324) into the final hourly/
python scripts/gen_miso83_attestation.py            # writes calibration_attestation.json
python scripts/legitimacy_diagnostics.py --bundle results/calibration/miso_netrev_margin --iso MISO \
    --json-out results/calibration/miso_netrev_margin/legitimacy_diagnostics.json
python scripts/dashboard_add_run.py --label "miso 83 netrev margin" \
    --bundle results/calibration/miso_netrev_margin   # registry + runs/<id>.js + metrics.json
python scripts/build_status.py --iso MISO             # status/MISO.js -> MISO:NOT-YET
# 2. git commit + push: results/calibration/miso_netrev_margin/ (6 JSON + 6 hourly parquet),
#    registry/<id>.json, runs/<id>.js, status/MISO.js (keepers/MISO.json already on main)
# 3. DELETE "2026-07-24-miso-83-netrev-margin" from scripts/lib/known_unsynced_keepers.py
#    (both UNSYNCED_RUN_PAYLOADS and UNSYNCED_KEEPERS); run calibration-keeper-auditor --iso MISO
```

Note `keeper_store.py` referenced in the source handoff does not exist — the keeper
is set by editing `frontend/data/backcast/keepers/MISO.json` directly (already points
to the id on main), then `build_status.py --iso MISO`.

---

### miso-84 entry (fold into docs/calibration-log/miso.md verbatim, then bump Next number → miso-85)

The full entry text is drafted in `docs/calibration-log/miso.md` on this lane's
working tree (a `## 2026-07-24 — miso-84: avenue #1 …` section). It mirrors the
Result table + Adjudication above. If the working tree was reclaimed, reconstruct
it from the "Result" and "Adjudication" sections of this document.
