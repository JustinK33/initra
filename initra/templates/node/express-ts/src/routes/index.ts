import { Router } from 'express';

import healthRoutes from './health';
import usersRoutes from './users';

const router = Router();

router.use('/health', healthRoutes);
router.use('/users', usersRoutes);

export default router;
