import http from 'http';
import dotenv from 'dotenv';
import { Server } from 'socket.io';
import app from './app';

dotenv.config();

const PORT = process.env.PORT || 3000;

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*', // Allow all origins for now (adjust for production)
        methods: ['GET', 'POST']
    }
});

io.on('connection', (socket: { id: any; on: (arg0: string, arg1: () => void) => void; }) => {
    console.log('User connected:', socket.id);

    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
    });
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
