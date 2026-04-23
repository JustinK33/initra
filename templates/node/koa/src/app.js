const Koa = require('koa');

const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/requestLogger');
const healthRoutes = require('./routes/health');
const usersRoutes = require('./routes/users');

const app = new Koa();

app.use(errorHandler);
app.use(requestLogger);
app.use(healthRoutes.routes()).use(healthRoutes.allowedMethods());
app.use(usersRoutes.routes()).use(usersRoutes.allowedMethods());
app.use(notFoundHandler);

module.exports = app;
