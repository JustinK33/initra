import express, { type Request, type Response } from 'express';

import { env } from './config/env';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import { requestLogger } from './middleware/requestLogger';
import healthRoutes from './routes/health';
import usersRoutes from './routes/users';

const app = express();

app.use(express.json());
app.use(requestLogger);

app.use('/health', healthRoutes);
app.use('/users', usersRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

app.get('/', (_req: Request, res: Response) => {
  res.json({ message: '{{project_name}} API', env });
});

export default app;
