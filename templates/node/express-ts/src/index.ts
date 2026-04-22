import express, { Request, Response } from 'express';

const app = express();
const port = Number(process.env.PORT || 3000);

app.get('/', (req: Request, res: Response) => {
  res.json({ status: 'ok', project: '{{project_name}}' });
});

if (require.main === module) {
  app.listen(port, () => {
    console.log(`{{project_name}} listening on port ${port}`);
  });
}

export default app;
