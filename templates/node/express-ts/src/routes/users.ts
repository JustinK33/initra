import { Router } from 'express';

import {
  createUserHandler,
  deleteUserHandler,
  getUserHandler,
  listUsersHandler,
  updateUserHandler,
} from '../controllers/usersController';

const router = Router();

router.get('/', listUsersHandler);
router.get('/:id', getUserHandler);
router.post('/', createUserHandler);
router.put('/:id', updateUserHandler);
router.delete('/:id', deleteUserHandler);

export default router;
