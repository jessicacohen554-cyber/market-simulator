# UC-4-NEISO 2019: container-reclaim evidence (uc-1.8, HEAD 282150d5)

Shard `session_011r5KgSp8LR45heJBXtPbdw`, reported verbatim on 2026-10-16 at 00:29Z. The logs have no timestamped lines, so the launch times are the ones the shard recorded when it launched. The death time is the log's last-write mtime. UC window counts are 0-indexed.

| attempt | PID | launched | last log write | lived | `grep -c "UC window"` | Traceback/Error/MemoryError/Killed | keep-alive |
|---|---|---|---|---|---|---|---|
| 1 | 1230 | 21:22:58Z | 22:31:07.9Z | 68.2 min | 326 (0..325) | 0 | background `timeout 5400` watcher + send_later |
| 2 | 488 | 22:33:28Z | 23:48:36.5Z | 75.1 min | 362 (0..361 of ~365) | 0 | background `timeout 5400` watcher + send_later |
| 3 | 1573 | 23:51:54Z | 23:56:41.0Z | 4.8 min | 15 (0..14) | 0 | send_later every 25 min only; died ~5 min after the shard's turn ended |

Every logged window was Optimal. After each death, `uptime` read "up 0 min", which is a fresh boot, and the swap was gone. The memory gate passed at 22.4 GiB each time, against a NEISO peak of about 5.2–5.5 GiB (the 2020 and 2021 legs).

An earlier uc-1.7 2019 run, under a different shard, was lost at about 14:28Z at window 254 while its session was idle (Addendum C).

Last 3 lines of each log:

```
ATTEMPT 1 — /tmp/aborted_2019/solve_2019_attempt1.log
INFO: UC window 323 [7752, 7788): Optimal, MILP 6.37 s, 1 nodes, gap 4.41e-04
INFO: UC window 324 [7776, 7812): Optimal, MILP 12.44 s, 3 nodes, gap 1.00e-03
INFO: UC window 325 [7800, 7836): Optimal, MILP 8.92 s, 3 nodes, gap 9.97e-04
ATTEMPT 2 — /tmp/aborted_2019_attempt2/solve_2019.log.raw
INFO: UC window 359 [8616, 8652): Optimal, MILP 4.42 s, 1 nodes, gap 8.32e-04
INFO: UC window 360 [8640, 8676): Optimal, MILP 5.78 s, 1 nodes, gap 5.10e-04
INFO: UC window 361 [8664, 8700): Optimal, MILP 39.37 s, 29 nodes, gap 9.99e-04
ATTEMPT 3 — /tmp/solve_2019.log
INFO: UC window 12 [288, 324): Optimal, MILP 5.63 s, 1 nodes, gap 3.62e-04
INFO: UC window 13 [312, 348): Optimal, MILP 4.64 s, 1 nodes, gap 9.29e-04
INFO: UC window 14 [336, 372): Optimal, MILP 7.31 s, 1 nodes, gap 6.21e-04
```

Reading, unadjudicated: a running background tool task holds the container for at most about 70–75 min, and `send_later` alone does not hold it. A NEISO UC year needs at least 60 min of UC plus P0 and P1, so it does not fit that window reliably.
