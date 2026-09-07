import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const index = readFileSync(resolve(root, 'src/pages/index.astro'), 'utf8');
const meta = readFileSync(resolve(root, 'src/lib/meta.ts'), 'utf8');
assert.match(index, /MetaPixel/);
assert.match(meta, /no_ads=1/);
console.log('attribution: landing pixel present; no_ads guard in snippets');
