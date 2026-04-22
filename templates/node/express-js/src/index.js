const express = require('express');

const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ status: 'ok', project: '{{project_name}}' });
});

if (require.main === module) {
  app.listen(port, () => {
    console.log(`{{project_name}} listening on port ${port}`);
  });
}

module.exports = app;
