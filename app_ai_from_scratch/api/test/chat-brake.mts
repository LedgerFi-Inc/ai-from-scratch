// The test the ledger claimed existed for months.
//
// docs/MVP-READINESS.md cited `api/test/chat-brake.mts` as the evidence for
// "chat spend uncapped by tokens; client picks model". The file did not exist,
// and the token half of that ceiling did not work: the counters were compared
// after the billed call and the only consequence was a log line. Citing a test
// that is not there is worse than citing none — it stops anyone from looking.

import assert from 'node:assert/strict';
import { tokenCeiling } from '../src/chat-ceiling.ts';

const CAPS = { own: 200_000, global: 5_000_000 };
const WAIT = 3600;

// Under both ceilings: the message goes through.
assert.equal(tokenCeiling(0, 0, CAPS, WAIT), null);
assert.equal(tokenCeiling(199_999, 4_999_999, CAPS, WAIT), null);

// EXACTLY at the ceiling still passes. The question caps use `>` too: a counter
// sitting on its allowance has spent it, not exceeded it. If this ever flips to
// `>=`, a user is refused one turn earlier than the number on screen promises.
assert.equal(tokenCeiling(200_000, 0, CAPS, WAIT), null);
assert.equal(tokenCeiling(0, 5_000_000, CAPS, WAIT), null);

// One token past the personal ceiling.
const own = tokenCeiling(200_001, 0, CAPS, WAIT);
assert.ok(own, 'a personal token overrun must be refused');
assert.equal(own.limite, 'tokens_dia');
assert.equal(own.tope, CAPS.own);
assert.equal(own.esperaS, WAIT);
assert.ok(own.msg.length > 0, 'the payload carries a message the client can show');

// One token past the platform ceiling.
const global = tokenCeiling(0, 5_000_001, CAPS, WAIT);
assert.ok(global, 'a platform token overrun must be refused');
assert.equal(global.limite, 'tokens_dia_global');
assert.equal(global.tope, CAPS.global);

// Both blown: the person is told it was THEIR budget, not the platform's.
// Telling someone the platform is full when they are the one who drained their
// own allowance sends them to support instead of to tomorrow.
const both = tokenCeiling(200_001, 5_000_001, CAPS, WAIT);
assert.ok(both);
assert.equal(both.limite, 'tokens_dia');

// The regression this file exists for: a run far past the ceiling — 120 turns
// at ~30 000 tokens, which the question cap alone permits — must not pass.
assert.ok(tokenCeiling(3_600_000, 0, CAPS, WAIT), 'the count cap alone is not a spend cap');

console.log('chat-brake: token ceiling refuses past-limit counters, ok');
