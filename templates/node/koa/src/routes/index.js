const Router = require('@koa/router');

const healthRoutes = require('./health');
const usersRoutes = require('./users');

const router = new Router();

router.use(healthRoutes.routes(), healthRoutes.allowedMethods());
router.use(usersRoutes.routes(), usersRoutes.allowedMethods());

module.exports = router;
