import app from './app';
import { env, port } from './config/env';

app.listen(port, () => {
  console.log(`{{project_name}} listening on port ${port} (${env})`);
});
