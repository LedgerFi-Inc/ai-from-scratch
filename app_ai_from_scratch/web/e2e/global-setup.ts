const API = process.env.API_URL ?? 'http://127.0.0.1:8787';

export default async function globalSetup(): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/health`);
  } catch (err) {
    throw new Error(`e2e-journey failed closed: ${API}/api/health is unreachable. Start the stack (pnpm dev) then re-run. ${String(err)}`);
  }
  if (!res.ok) {
    throw new Error(`e2e-journey failed closed: ${API}/api/health returned ${res.status}. Start the stack (pnpm dev) then re-run.`);
  }
}
