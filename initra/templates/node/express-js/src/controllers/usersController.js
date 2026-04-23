const userService = require('../services/userService');

function listUsers(req, res) {
  res.json({ users: userService.listUsers() });
}

function getUser(req, res) {
  const user = userService.getUser(Number(req.params.id));
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
}

function createUser(req, res) {
  try {
    const user = userService.createUser(req.body);
    res.status(201).json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
}

function updateUser(req, res) {
  try {
    const user = userService.updateUser(Number(req.params.id), req.body);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
}

function deleteUser(req, res) {
  const deleted = userService.removeUser(Number(req.params.id));
  if (!deleted) return res.status(404).json({ error: 'User not found' });
  res.json({ status: 'deleted' });
}

module.exports = { listUsers, getUser, createUser, updateUser, deleteUser };
