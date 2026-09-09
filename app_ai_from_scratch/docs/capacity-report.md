# Capacity report

No Railway capacity claim is made yet. Run `k6 run scripts/load-test.js` against
DEV at 10, 50, 100, 250, 500 and 1,000 VUs with synthetic users and external AI
and payments disabled. Capture RPS, p50/p95/p99, errors, CPU/RAM, database
connections/latency, Redis usage, queue depth and worker utilization. Stop over
1% errors, 1s deterministic p95, or 85% memory/connections. Report the first
bottleneck and largest passing stage; do not convert VUs into user counts.
