import dotenv from 'dotenv';

dotenv.config();

export const env = process.env.NODE_ENV ?? 'development';
export const port = Number(process.env.PORT ?? 3000);
