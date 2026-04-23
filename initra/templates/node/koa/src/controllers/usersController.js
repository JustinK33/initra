const userService = require('../services/userService');

async function listUsers(ctx) {
  ctx.body = { users: userService.listUsers() };
}

async function getUser(ctx) {
  const user = userService.getUser(Number(ctx.params.id));
  if (!user) {
    ctx.status = 404;
    ctx.body = { error: 'User not found' };
    return;
  }
  ctx.body = user;
}

async function createUser(ctx) {
  try {
    const user = userService.createUser(ctx.request.body);
    ctx.status = 201;
    ctx.body = user;
  } catch (error) {
    ctx.status = 400;
    ctx.body = { error: error.message };
  }
}

async function updateUser(ctx) {
  try {
    const user = userService.updateUser(Number(ctx.params.id), ctx.request.body);
    if (!user) {
      ctx.status = 404;
      ctx.body = { error: 'User not found' };
      return;
    }
    ctx.body = user;
  } catch (error) {
    ctx.status = 400;
    ctx.body = { error: error.message };
  }
}

async function deleteUser(ctx) {
  const deleted = userService.removeUser(Number(ctx.params.id));
  if (!deleted) {
    ctx.status = 404;
    ctx.body = { error: 'User not found' };
    return;
  }
  ctx.body = { status: 'deleted' };
}

module.exports = { listUsers, getUser, createUser, updateUser, deleteUser };
