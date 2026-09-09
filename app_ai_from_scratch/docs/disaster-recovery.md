# Disaster recovery

Target RPO is 1 hour and RTO is 4 hours. Enable Railway Postgres daily, weekly
and monthly volume snapshots and PITR where eligible. `scripts/backup.sh`
creates logical dumps for course, payments and messages; upload encrypted dumps
to the environment backup bucket with checksums and retention.

Run `sh scripts/restore.sh <dump>` only against a disposable Postgres instance,
then apply migrations and `pnpm verify`. Record duration and recoverable time.
For API failure, redeploy the last successful image. For a bad migration, stop
writers and restore into a new database service before switching variables.
Redis and RabbitMQ are disposable: restart, replay durable jobs and redrive DLQ.
AI and Resend outages degrade optional features and retry. Payment webhooks stay
persisted and are reconciled before granting access. Bucket loss uses the
external dump copy; rotate credentials afterward.
