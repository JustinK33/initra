const userModel = require('../models/userModel');

function assertValidPayload(payload) {
  if (!payload || typeof payload.name !== 'string' || payload.name.trim().length < 2) {
    throw new Error('Name must be at least 2 characters long');
  }
  if (typeof payload.email !== 'string' || !payload.email.includes('@')) {
    throw new Error('Email must be valid');
  }
}

function listUsers() {
  return userModel.listUsers();
}

function getUser(id) {
  return userModel.findUserById(id);
}

function createUser(payload) {
  assertValidPayload(payload);
  return userModel.createUser(payload.name.trim(), payload.email.trim());
}

function updateUser(id, payload) {
  assertValidPayload(payload);
  return userModel.updateUser(id, payload.name.trim(), payload.email.trim());
}

function removeUser(id) {
  return userModel.deleteUser(id);
}

module.exports = { listUsers, getUser, createUser, updateUser, removeUser };
