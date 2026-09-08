// Exercise the real, unchanged Azure function without an emulator or network.
const test = require('node:test');
const assert = require('node:assert/strict');
const webfinger = require('../api/webfinger/index.js');
const binding = require('../api/webfinger/function.json');

async function request(query) {
    const context = {};
    await webfinger(context, { query });
    return context.res;
}

test('valid account returns the exact subject and Clerk issuer', async () => {
    const resource = 'acct:hello@khoit.dev';
    const res = await request({ resource });
    assert.equal(res.status, 200);
    assert.deepEqual(JSON.parse(res.body), {
        subject: resource,
        links: [{ rel: 'http://openid.net/specs/connect/1.0/issuer', href: 'https://clerk.khoit.dev' }],
    });
    assert.deepEqual(res.headers, {
        'Content-Type': 'application/jrd+json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=3600',
    });
});

test('other local account names are echoed without hardcoding', async () => {
    const resource = 'acct:identity-regression@khoit.dev';
    assert.equal(JSON.parse((await request({ resource })).body).subject, resource);
});

test('missing, empty, foreign, and suffix-spoofed domains are rejected', async () => {
    for (const query of [{}, { resource: '' }, { resource: 'acct:hello@example.com' },
        { resource: 'acct:hello@khoit.dev.example.com' }, { resource: 'acct:hello@notkhoit.dev' }]) {
        const res = await request(query);
        assert.equal(res.status, 400);
        assert.deepEqual(JSON.parse(res.body), { error: 'Invalid resource domain.' });
        assert.equal(res.headers['Content-Type'], 'application/json');
        assert.equal(res.headers['Access-Control-Allow-Origin'], '*');
    }
});

test('Azure function binding remains anonymous GET with HTTP output', () => {
    assert.deepEqual(binding.bindings, [
        { authLevel: 'anonymous', type: 'httpTrigger', direction: 'in', name: 'req', methods: ['get'] },
        { type: 'http', direction: 'out', name: 'res' },
    ]);
});
