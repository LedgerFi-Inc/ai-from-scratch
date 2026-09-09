import { bucket, defineRailway, github, group, image, postgres, project, redis, service } from "railway/iac";

export default defineRailway((ctx) => {
  const prod = ctx.isEnvironment("PROD") || ctx.isEnvironment("production");
  const db = postgres("course-db");
  const paymentsDb = postgres("payments-db");
  const messagesDb = postgres("messages-db");
    // `redis` is reserved by an orphaned template service in the Railway
    // project; use a project-unique name while retaining the Redis role.
    const cache = redis("cache");
  const files = bucket(prod ? "prod-files" : "dev-files", { region: "iad" });
  const repo = github("Alxn44/ai-from-scratch", { branch: "main" });
  const common = { source: repo, replicas: 1 };
    const data = service("data", { ...common, root: "app_ai_from_scratch", build: { builder: "DOCKERFILE", dockerfilePath: "data/Dockerfile", watchPatterns: ["data/**", "api/src/ontologia.json"] }, healthcheck: "/health", env: { DATABASE_URL: db.env.DATABASE_URL, DATA_SECRETO: { preserveExisting: true } } });
    const api = service("api", { ...common, root: "app_ai_from_scratch", build: { builder: "DOCKERFILE", dockerfilePath: "api/Dockerfile", watchPatterns: ["api/**", "auth/**", "package.json", "pnpm-lock.yaml"] }, preDeploy: "pnpm db:deploy", healthcheck: "/api/health", env: { DATABASE_URL: db.env.DATABASE_URL, REDIS_URL: cache.env.REDIS_URL, DATA_URL: "http://data.railway.internal:8080", JWT_SECRET: { preserveExisting: true }, DATA_SECRETO: { preserveExisting: true }, WEB_ORIGIN: { preserveExisting: true }, NODE_ENV: "production", APP_ENV: prod ? "PROD" : "DEV" } });
    const web = service("web", { ...common, root: "app_ai_from_scratch/web", build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["**"] }, env: { API_URL: api.env.RAILWAY_PRIVATE_DOMAIN, APP_ENV: prod ? "PROD" : "DEV" }, domains: prod ? ["aifromscratch.shop"] : [], healthcheck: "/robots.txt" });
    const payments = service("payments", { ...common, root: "app_ai_from_scratch/payments", build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["**"] }, healthcheck: "/health", env: { DATABASE_URL: paymentsDb.env.DATABASE_URL, ENTITLEMENTS_URL: "http://api.railway.internal:8787", NODE_ENV: prod ? "production" : "development", APP_ENV: prod ? "PROD" : "DEV" } });
    const messages = service("messages", { ...common, root: "app_ai_from_scratch/messages", build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["**"] }, healthcheck: "/health", env: { DATABASE_URL: messagesDb.env.DATABASE_URL } });
    const ai = service("ai", { ...common, root: "app_ai_from_scratch/ai", build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["**"] }, start: "sh -c '.venv/bin/uvicorn course_ai.app:app --host 0.0.0.0 --port ${PORT:-8799}'", healthcheck: "/salud", env: { NODE_URL: api.env.RAILWAY_PRIVATE_DOMAIN, IA_SECRETO: { preserveExisting: true } } });
    const worker = service("api-worker", { ...common, root: "app_ai_from_scratch", build: { builder: "DOCKERFILE", dockerfilePath: "api/Dockerfile", watchPatterns: ["api/**", "auth/**", "package.json", "pnpm-lock.yaml"] }, start: "node dist/api/src/worker.js", env: { DATABASE_URL: db.env.DATABASE_URL, REDIS_URL: cache.env.REDIS_URL, JWT_SECRET: { preserveExisting: true } } });
  const broker = service("rabbitmq", { source: image("rabbitmq:4-management-alpine"), replicas: 1 });
  return project("ai-from-scratch", { resources: [group("core", [web, api, data, ai]), group("async", [worker, payments, messages, broker]), db, paymentsDb, messagesDb, cache, files] });
});
