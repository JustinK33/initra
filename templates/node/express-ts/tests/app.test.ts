import test from 'node:test';
import assert from 'node:assert/strict';

import app from '../src/app';

test('app exports a callable handler', () => {
  assert.equal(typeof app, 'function');
});
