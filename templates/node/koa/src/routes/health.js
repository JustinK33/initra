const Router = require('@koa/router');
const { env } = require('../config/env');

const router = new Router();

router.get('/health', async (ctx) => {
  ctx.body = { status: 'ok', project: '{{project_name}}', env };
});

module.exports = router;
