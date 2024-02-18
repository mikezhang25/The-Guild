const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');

const client = new Client();

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
});

client.on('ready', async () => {
    console.log('Client is ready!');
});

client.initialize();

//---------------------------------------

const app = express();

app.use(express.json()) // for parsing application/json
app.use(express.urlencoded({ extended: true })) // for parsing application/x-www-form-urlencoded

app.get('/phone-numbers', async (req, res) => {
    try {
        const chats = await client.getChats();
        const phoneNumbers = chats.map(chat => chat.id.user);
        res.json(phoneNumbers);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch chats' });
    }
});

app.get('/fetch-messages/:phoneNumber', async (req, res) => {
    const phoneNumber = req.params.phoneNumber;
    try {
        const chat = await client.getChatById(`${phoneNumber}@c.us`);
        if (chat) {
            const messages = await chat.fetchMessages();
            const messageBodies = messages.map(message => message.body);
            res.json(messageBodies);
        } else {
            res.status(404).json({ error: 'Chat not found' });
        }
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch messages' });
    }
});

app.post('/send-message', async (req, res) => {
    const phoneNumber = req.body.phoneNumber;
    const message = req.body.message;
    try {
        const chat = await client.getChatById(`${phoneNumber}@c.us`);
        if (chat) {
            await chat.sendMessage(message);
            res.json({ message: 'Message sent successfully' });
        } else {
            res.status(404).json({ error: 'Chat not found' });
        }
    } catch (error) {
        res.status(500).json({ error: 'Failed to send message' });
    }
});

// For debugging purposes
app.get('/chats', async (req, res) => {
    try {
        const chats = await client.getChats();
        res.json(chats);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch chats' });
    }
});

const PORT = 3001;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

