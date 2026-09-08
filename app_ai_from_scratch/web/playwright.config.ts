import { defineConfig, devices } from '@playwright/test';

const API = process.env.API_URL ?? 'http://127.0.0.1:8787';
const WEB = process.env.WEB_ORIGIN ?? 'http://localhost:4321';
const channel = process.env.PW_CHANNEL;

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: { baseURL: WEB, trace: 'off', ...(channel ? { channel } : {}) },
  globalSetup: './e2e/global-setup.ts',
  outputDir: '../docs/readiness/evidence/e2e',
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  metadata: { api: API },
});
