const test = require('node:test');
const assert = require('node:assert/strict');

const app = require('../src/app');

test('app exports a middleware stack', () => {
  assert.equal(typeof app.callback, 'function');
});
