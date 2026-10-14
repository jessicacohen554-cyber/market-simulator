# FINDING — UC-1-FIX-6: an offline integer cluster carries no reserve (uc-1.6)

**Lane:** UC-1-FIX-6 (engine) · **Chartered by:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-fix6-reserve-headroom` off `main` `d99bf94d`.
**Defect:** UC-DIAG cause #1 (FINDING-ucmilp-diag-undercommit-2026-10-14, PR #7249).
**Nothing tuned, nothing registered.** No new ScenarioConfig field, no new constant.

## 0. Result

| item | status |
|---|---|
| Engine fix (window) | **Done.** `model/uc/window.py::reserve_headroom_u_terms`. Engine `uc-1.5 → uc-1.6`. |
| Rule 19 | **One reserve mechanism.** The window keeps the production reserve rows; only their integer-member capacity moves from the RHS onto `u`. `reserve_posture_pools` and `posture_gen_idx` stay refused. P1 reserve rows unchanged (`lp/reserve_rows.py` untouched). |
| G-OFF | **Every hunk is UC-only** (`model/uc/window.py`, `pipeline/uc.py`). With no reserve co-opt the window is byte-identical to uc-1.5 (test). Keeper defaults unchanged. |
| Arming reserves in a UC arm | **Already possible** through the existing fields: SPP `energy_reserve_coopt=true`; CAISO `energy_reserve_coopt=true` + `caiso_reserve_coopt=true`. No code needed. |
| Repro shard (SPP 2020, arm B + reserves) | see §4 |

## 1. The change

Before: every capacity-anchored reserve headroom row reads `Σ P + Σ R ≤ Σ_elig pmax·a` (zonal shared-headroom rows, `reserve_rows.py:193`; pergen joint pool rows, `:808`). An integer cluster at `u = 0` still counts `pmax·a` toward reserve.

After, inside the UC window only: member `g` of integer cluster `c` contributes `pmax_g·a_g,t · u_c,t / n_c` instead of `pmax_g·a_g,t`:

    Σ P + Σ R ≤ Σ_{non-integer elig} pmax·a  +  Σ_{integer elig} pmax·a·u/n   (+ storage, extra, unchanged)

So for an integer member `r ≤ pmax·a·u/n − P`, the same ceiling the schedule later puts on P1 (`pipeline/uc.py`: availability · u/n). At `u = n` the row is the production row.

- Built as `u`-column coefficients passed to `addCols` plus one vectorized `changeRowsBounds` on the touched rows (rule 2: no hour loop).
- Rows already P-gated (legacy `reserve_online_gated` class rows, pergen online-gated coupling rows) are left alone.
- A guard raises if a row's RHS would go negative (the reserve block not where the layout says).
- `uc_solve_log` windows record `reserve_gated_rows`.

**Which products may count offline capacity.** None, for integer members. An integer cluster is by construction not fast-start: `params.integer_gate` is the posture fast-start exemption inverted (`spec.POSTURE_FAST_START_MIN_DOWN_H = 2 h`, `POSTURE_FAST_START_STARTUP_PER_MW = $30/MW`). The spec defines that exemption as exactly the set whose offline capacity provides offline supplemental / non-spin (`spec.py` comment at the constants: "its OFFLINE capacity still provides MISO offline supplemental reserve"). Non-integer (fast-start) members keep `pmax·a`, i.e. today's offline non-spin / supplemental credit. Market rules relied on:
- SPP Integrated Marketplace Protocols §4.1.5 / RSG Operating Process 0820EXT00002 v4.0 definitions (p. 5): Contingency Reserve = Spinning (synchronized) + Supplemental (on-line or off-line, deployable within 10 min).
- CAISO tariff §8.4 / Appendix K: Spinning is synchronized; Non-Spinning may be off-line if it can reach output within 10 min.
- NYISO/ISO-NE 10-min non-sync products: off-line quick-start only.

A slow-start unit cannot be synchronized and loaded within 10 (or 30) minutes, so its offline capacity qualifies for none of these.

**Limitation (declared).** The integer gate is by min-down / start cost, not measured start time. A 30-minute product (NYISO 30-min, PJM secondary) could in principle take an offline integer unit that starts inside 30 min; no such start-time data is on disk. ERCOT's additive `reserve_headroom_extra_cap` (offline quick-start Non-Spin) is a precomputed RHS term and is not re-gated; it is built from the quick-start set, which the integer gate excludes in practice.

## 2. Tests (`tests/unit/model/uc/test_window_reserve_headroom.py`, fast lane)

1 cluster (CC, 2 × 100 MW, mlf 0.5) / 1 zone / 24 h, night load 40 MW covered by baseload.

| test | asserts | uc-1.5 behaviour (gate stubbed out) |
|---|---|---|
| no co-opt adds nothing | 0 gated rows; `u/v/w` columns hold no LP-row entry; night decommit as before | pass (G-OFF) |
| R = 80 MW on the CC alone | `u = 2` every hour (one unit: 100 online − 50 min-load = 50 < 80); R = 80; `200 − P ≥ R` | **fails** (u = 0 at night) |
| `u` fixed 0 | reserve provided = 0 | **fails** (80 MW from offline) |
| R = 30 MW, hard | `u = 1` at night; `r ≤ 100·u − P` every hour | — |
| fast-start CT eligible | CT's offline 150 MW still covers R; CC stays off | pass |
| pergen pool | entries `−pmax·a/n = −100`, RHS cut 200, `u = 2` | — |

UC suite: 113 passed. Fast lane: see PR.

## 3. Requirement source each ISO would use (UC arm with reserves armed)

| ISO | keeper `energy_reserve_coopt` | requirement (existing spec, `model/reserves/spec.py`) | to arm in a UC arm |
|---|---|---|---|
| SPP | false | One Contingency Reserve family: `0.964 × 1.2 × MSSC_t` (RSG Operating Process §4.1–4.3; MSSC = largest available unit ≥ 600 MW nameplate; 0.964 measured from SPP RTBM-OR, FINDING-spp-55). Published CR demand curve $275/$550/$1,100. **Pools spin + supplemental**; the ≥ ½-spin sub-constraint is not modelled (SPP-56). | `--set energy_reserve_coopt=true` |
| CAISO | false | Spin + Non-Spin, pergen pools: `max(MSSC, 6 % load)` split half/half (BAL-002-WECC-3 R1), tariff §27.1.2.3.5 demand curves, storage duration-gated. | `--set energy_reserve_coopt=true --set caiso_reserve_coopt=true` |
| NYISO, NEISO, ERCOT, MISO, PJM | true | their keeper specs (RCPF / ORDC / RBDC) | already armed; they gain only the u-gate |

**Ex-ante expectation for SPP.** The SPP family pools spin and supplemental, and fast-start CTs are non-integer, so their offline `pmax·a` (several GW) can carry the whole ~1.4 GW requirement. The u-gate binds only if the CT pool cannot. The repro measures whether it does. If it does not, the remaining SPP lever is the spin sub-constraint (a spec change with its own PRECOMMIT), not this engine fix.

## 4. Repro shard — SPP 2020, arm B + UC + reserves (uc-1.6)

_Filled at shard return._
