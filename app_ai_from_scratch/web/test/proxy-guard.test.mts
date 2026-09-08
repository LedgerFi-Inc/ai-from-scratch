import assert from 'node:assert/strict';
import { isInternal } from '../src/lib/proxy-guard.ts';

assert.equal(isInternal('internal/entitlements'), true);
assert.equal(isInternal('interno/catalogo'), true);
assert.equal(isInternal('v3/internal/entitlements'), true);
assert.equal(isInternal('v3/interno/herramienta'), true);
assert.equal(isInternal('auth/login'), false);
assert.equal(isInternal('lessons/1'), false);
console.log('proxy-guard: internal paths blocked');
