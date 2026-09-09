# Railway runbook

```sh
railway whoami --json
railway link --project <project-id> --environment DEV
railway config plan
railway config apply
railway deployment list --environment DEV --json
railway logs --service api --environment DEV --lines 200 --json
```

Use `railway up --ci` only after CI and DEV gates pass. Verify the submitted
deployment reaches `SUCCESS`; queued or exited CLI commands are not success.
For rollback, redeploy the last known-good release, then run
`scripts/health-check.sh` and the smoke suite. Before migrations create a
logical dump and a named Railway backup. Never delete or restore a PROD volume
automatically.
