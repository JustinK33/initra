const app = require('./app');
const { env, port } = require('./config/env');

app.listen(port, () => {
  console.log(`{{project_name}} listening on port ${port} (${env})`);
});
