/** Paths the browser must never reach through the public reverse proxy. */
export function isInternal(path: string): boolean {
  return /^(v3\/)?(interno|internal)(\/|$)/.test(path);
}
