export type User = {
  id: number;
  name: string;
  email: string;
};

const users: User[] = [];
let nextId = 1;

export function listUsers(): User[] {
  return users;
}

export function findUserById(id: number): User | undefined {
  return users.find((user) => user.id === id);
}

export function createUser(name: string, email: string): User {
  const user: User = { id: nextId++, name, email: email.toLowerCase() };
  users.push(user);
  return user;
}

export function updateUser(id: number, name: string, email: string): User | undefined {
  const user = findUserById(id);
  if (!user) return undefined;
  user.name = name;
  user.email = email.toLowerCase();
  return user;
}

export function deleteUser(id: number): boolean {
  const index = users.findIndex((user) => user.id === id);
  if (index < 0) return false;
  users.splice(index, 1);
  return true;
}
