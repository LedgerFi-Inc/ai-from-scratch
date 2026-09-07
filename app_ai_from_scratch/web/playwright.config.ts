import { defineConfig, devices } from '@playwright/test';

const API = process.env.API_URL ?? 'http://127.0.0.1:8787';
const WEB = process.env.WEB_ORIGIN ?? 'http://127.0.0.1:4321';

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: { baseURL: WEB, trace: 'off' },
  globalSetup: './e2e/global-setup.ts',
  outputDir: '../docs/readiness/evidence/e2e',
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 12'], viewport: { width: 390, height: 844 } } },
  ],
  metadata: { api: API },
});
