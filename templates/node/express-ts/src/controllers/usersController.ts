import type { Request, Response } from 'express';

import {
  createUser,
  getUser,
  listAllUsers,
  removeUser,
  updateUser,
} from '../services/userService';

export function listUsersHandler(_req: Request, res: Response): void {
  res.json({ users: listAllUsers() });
}

export function getUserHandler(req: Request, res: Response): void {
  const user = getUser(Number(req.params.id));
  if (!user) {
    res.status(404).json({ error: 'User not found' });
    return;
  }
  res.json(user);
}

export function createUserHandler(req: Request, res: Response): void {
  try {
    const user = createUser(req.body);
    res.status(201).json(user);
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
}

export function updateUserHandler(req: Request, res: Response): void {
  try {
    const user = updateUser(Number(req.params.id), req.body);
    if (!user) {
      res.status(404).json({ error: 'User not found' });
      return;
    }
    res.json(user);
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
}

export function deleteUserHandler(req: Request, res: Response): void {
  const deleted = removeUser(Number(req.params.id));
  if (!deleted) {
    res.status(404).json({ error: 'User not found' });
    return;
  }
  res.json({ status: 'deleted' });
}
