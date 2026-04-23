async function errorHandler(ctx, next) {
  try {
    await next();
  } catch (error) {
    ctx.status = error.status || 500;
    ctx.body = { error: error.message || 'Internal Server Error' };
  }
}

async function notFoundHandler(ctx, next) {
  await next();
  if (ctx.status === 404 && !ctx.body) {
    ctx.body = { error: 'Not Found' };
  }
}

module.exports = { errorHandler, notFoundHandler };
