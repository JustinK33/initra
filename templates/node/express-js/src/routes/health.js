const { Router } = require('express');
const { env } = require('../config/env');

const router = Router();

router.get('/', (req, res) => {
  res.json({ status: 'ok', project: '{{project_name}}', env });
});

module.exports = router;
