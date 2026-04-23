require('dotenv').config();

module.exports = {
  env: process.env.NODE_ENV || 'development',
  port: Number(process.env.PORT || 3000),
};
