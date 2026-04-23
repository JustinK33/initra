const express = require('express');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/requestLogger');
const healthRoutes = require('./routes/health');
const usersRoutes = require('./routes/users');

const app = express();

app.use(express.json());
app.use(requestLogger);

app.use('/health', healthRoutes);
app.use('/users', usersRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
