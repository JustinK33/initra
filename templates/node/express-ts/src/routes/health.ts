import { Router } from 'express';

import { env } from '../config/env';

const router = Router();

router.get('/', (_req, res) => {
  res.json({ status: 'ok', project: '{{project_name}}', env });
});

export default router;
