const { Router } = require('express');
const health = require('./health');
const users = require('./users');

const router = Router();

router.use('/health', health);
router.use('/users', users);

module.exports = router;
