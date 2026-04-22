const Koa = require('koa');
const Router = require('@koa/router');

const app = new Koa();
const router = new Router();
const port = process.env.PORT || 3000;

router.get('/', (ctx) => {
  ctx.body = { status: 'ok', project: '{{project_name}}' };
});

app.use(router.routes());
app.use(router.allowedMethods());

if (require.main === module) {
  app.listen(port, () => {
    console.log(`{{project_name}} listening on port ${port}`);
  });
}

module.exports = app;
