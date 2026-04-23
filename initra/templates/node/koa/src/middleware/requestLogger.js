async function requestLogger(ctx, next) {
  const start = Date.now();
  await next();
  const duration = Date.now() - start;
  console.log(`${ctx.method} ${ctx.path} ${ctx.status} ${duration}ms`);
}

module.exports = { requestLogger };
