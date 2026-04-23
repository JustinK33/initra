import {
  createUser as createUserRecord,
  deleteUser,
  findUserById,
  listUsers,
  updateUser as updateUserRecord,
  type User,
} from '../models/userModel';

export type UserPayload = {
  name: string;
  email: string;
};

function assertValidPayload(payload: UserPayload): void {
  if (!payload.name || payload.name.trim().length < 2) {
    throw new Error('Name must be at least 2 characters long');
  }
  if (!payload.email || !payload.email.includes('@')) {
    throw new Error('Email must be valid');
  }
}

export function listAllUsers(): User[] {
  return listUsers();
}

export function getUser(id: number): User | undefined {
  return findUserById(id);
}

export function createUser(payload: UserPayload): User {
  assertValidPayload(payload);
  return createUserRecord(payload.name.trim(), payload.email.trim());
}

export function updateUser(id: number, payload: UserPayload): User | undefined {
  assertValidPayload(payload);
  return updateUserRecord(id, payload.name.trim(), payload.email.trim());
}

export function removeUser(id: number): boolean {
  return deleteUser(id);
}
