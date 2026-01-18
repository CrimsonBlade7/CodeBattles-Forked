import express from 'express';
import cors from 'cors';
import helmet from 'helmet';

const app = express();

app.use(process.env.NODE_ENV === 'production' ? helmet() : helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

export default app;
