# FINDING — the C8 unit-grain sweep is 2/6 measured; MISO and PJM are BLOCKED, and the blockers are environmental, not analytic

**Session:** gpk4xr. **Date:** 2026-09-06. Diagnostic only (rule 13 `[R-MEASURED]`):
nothing re-scored; C8's committed plant-grain verdict stands on every ISO. Replay bundles
live in the gitignored `scratch/` tree and are never registered (rule 29(c)).

Companion to `docs/PREREG-c8-unit-grain-sweep-2026-09-06.md`, whose predictions P1–P8 /
W1–W2 remain **UNGRADED** for the four ISOs below.

## 1. Where the sweep got to

| ISO | status | number |
|---|---|---|
| NEISO | **MEASURED** | CC_REGULAR 0.007 / 0.014 / 0.016 — not exposed |
| NYISO | **MEASURED** | ST_GAS 0.305 / 0.312 / 0.230; CC_CHP 0.277 / 0.223 / 0.209 |
| CAISO | in flight at hand-off | — |
| MISO | **BLOCKED — memory** | — |
| PJM | **BLOCKED — missing corpus** | — |
| ERCOT | not attempted | — |

## 2. MISO: the replay does not fit in a standard session container

`replay_keeper.py` on `miso220_nonsteamlift_B` was **OOM-killed twice**, the second time
as the **sole running job** with 15.1 GB free. Kernel record:

```
Memory cgroup out of memory: Killed process (python)
total-vm:9668128kB anon-rss:7307328kB   oom_memcg=.../claude-code-bash
```

It dies at a reproducible point — immediately after
`miso_reserve_pergen` pools 2,606 members into 60 (zone, fuel-class) reserve columns —
having reached ~13 GB RSS. This is MISO's per-asset reserve LP construction, and it
exceeds what this container can give it. **No scheduling fix reaches it**: rule 12's
~2-concurrent cap already assumes more headroom than exists here, and the correct cap on
this box is one.

*A caution for whoever picks this up*: my first two MISO failures were NOT this. Two
orphaned CAISO replays from killed sweeps had been reparented to init, survived
`pkill -f replay_keeper.py`, and were holding **12 GB between them**. Check for
orphans (`ps -eo pid,ppid,rss,cmd | grep replay_keeper`) and kill by PID before
concluding anything about a replay's footprint.

## 3. PJM: a gitignored corpus that only a re-fetch restores

```
FileNotFoundError: pjm_da_virtual_bids is on but data/raw/pjm-da-virtuals/ has no
hrl_da_incs_decs_2023_* parquets — run scripts/data/fetch_pjm_da_virtuals.py
```

`pjm-da-virtuals` is one of the corpus-conversion datasets whose bulk payload is
untracked at tip and was stripped from history by the 2026-08-16 rewrite; `data/raw/
pjm-da-virtuals/` holds only its `README.md`. Recovery is **re-fetch only** — there is no
pin to restore from. So the PJM leg needs a data-intake step before it needs an LP, and
`pjm_da_virtual_bids` is armed in the keeper recipe, so the mechanism refuses to
no-op (by design).

## 4. What this does NOT change

The nyiso-193 card's question is untouched, and the two measured ISOs already sharpen it
(NEISO not exposed; NYISO's breach marginal and two-of-three years, against the card's
"over cap in every year" — see the corrected-basis commit). What is missing is the
cross-ISO cost estimate the PREREG §3 predicts, and P1 (MISO `CC_CHP`) — the headline
call — is precisely the one the memory blocker prevents grading.

**Neither blocker is a reason to rule differently.** They are reasons the option-C
measurement needs a container with more memory for MISO/ERCOT and a PJM virtuals
re-fetch, both of which belong to the scorer lane, not a per-ISO calibration lane
(rule 25 `[R-ISO-SCOPE]`; the card says so itself).
