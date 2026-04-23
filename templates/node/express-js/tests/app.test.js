const test = require('node:test');
const assert = require('node:assert/strict');

const app = require('../src/app');

test('app exports a callable handler', () => {
  assert.equal(typeof app, 'function');
});
