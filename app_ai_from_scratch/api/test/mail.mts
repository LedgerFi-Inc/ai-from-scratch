import assert from 'node:assert/strict';
import test from 'node:test';
import { loadMailer } from '../src/mail.ts';

const KEYS = ['RESEND_API_KEY', 'MAIL_FROM'];

const withEnv = <T,>(env: Record<string, string | undefined>, run: () => T): T => {
  const saved = { ...process.env };
  for (const key of KEYS) delete process.env[key];
  Object.assign(process.env, env);
  try { return run(); } finally { process.env = saved; }
};

test('both unset: no mailer, no throw', () => {
  assert.equal(withEnv({}, loadMailer), undefined);
});

test('RESEND_API_KEY without MAIL_FROM throws', () => {
  assert.throws(() => withEnv({ RESEND_API_KEY: 're_' + 'k'.repeat(20) }, loadMailer), /together/);
});

test('MAIL_FROM without RESEND_API_KEY throws', () => {
  assert.throws(() => withEnv({ MAIL_FROM: 'no-reply@aifromscratch.shop' }, loadMailer), /together/);
});

test('a key with no re_ prefix throws', () => {
  assert.throws(() => withEnv({ RESEND_API_KEY: 'sk_' + 'k'.repeat(20), MAIL_FROM: 'a@b.co' }, loadMailer),
    /re_ prefix/);
});

test('a non-email MAIL_FROM throws', () => {
  assert.throws(() => withEnv({ RESEND_API_KEY: 're_' + 'k'.repeat(20), MAIL_FROM: 'not-an-email' }, loadMailer),
    /email address/);
});

test('both set builds a mailer that posts to the Resend API', async () => {
  const mailer = withEnv({ RESEND_API_KEY: 're_' + 'k'.repeat(20), MAIL_FROM: 'no-reply@aifromscratch.shop' },
    loadMailer);
  assert.ok(mailer);
  const original = globalThis.fetch;
  let seenUrl = '', seenInit: RequestInit | undefined;
  globalThis.fetch = (async (url: string, init?: RequestInit) => {
    seenUrl = String(url); seenInit = init;
    return new Response(null, { status: 200 });
  }) as typeof fetch;
  try {
    await mailer!.send({ to: 'student@example.com', subject: 'Recuperar acceso', text: 'enlace' });
  } finally { globalThis.fetch = original; }
  assert.equal(seenUrl, 'https://api.resend.com/emails');
  assert.equal(seenInit?.method, 'POST');
  const headers = seenInit?.headers as Record<string, string>;
  assert.equal(headers.authorization, `Bearer re_${'k'.repeat(20)}`);
  const body = JSON.parse(String(seenInit?.body));
  assert.deepEqual(body, {
    from: 'no-reply@aifromscratch.shop', to: 'student@example.com',
    subject: 'Recuperar acceso', text: 'enlace',
  });
});

test('a non-2xx Resend response throws with the status and body', async () => {
  const mailer = withEnv({ RESEND_API_KEY: 're_' + 'k'.repeat(20), MAIL_FROM: 'no-reply@aifromscratch.shop' },
    loadMailer);
  const original = globalThis.fetch;
  globalThis.fetch = (async () => new Response('rate limited', { status: 429 })) as typeof fetch;
  try {
    await assert.rejects(
      mailer!.send({ to: 'a@b.co', subject: 's', text: 't' }),
      /resend_429/,
    );
  } finally { globalThis.fetch = original; }
});
