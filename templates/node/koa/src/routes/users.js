const Router = require('@koa/router');

const controller = require('../controllers/usersController');

const router = new Router({ prefix: '/users' });

router.get('/', controller.listUsers);
router.get('/:id', controller.getUser);
router.post('/', controller.createUser);
router.put('/:id', controller.updateUser);
router.delete('/:id', controller.deleteUser);

module.exports = router;
