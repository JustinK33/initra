const users = [];
let nextId = 1;

function listUsers() {
  return users;
}

function findUserById(id) {
  return users.find((user) => user.id === id);
}

function createUser(name, email) {
  const user = { id: nextId++, name, email: email.toLowerCase() };
  users.push(user);
  return user;
}

function updateUser(id, name, email) {
  const user = findUserById(id);
  if (!user) return null;
  user.name = name;
  user.email = email.toLowerCase();
  return user;
}

function deleteUser(id) {
  const index = users.findIndex((user) => user.id === id);
  if (index === -1) return false;
  users.splice(index, 1);
  return true;
}

module.exports = { listUsers, findUserById, createUser, updateUser, deleteUser };
