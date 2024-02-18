const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');

const client = new Client();

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
});

client.on('ready', async () => {
    console.log('Client is ready!');
    // const chats = await client.getChats();
    // console.log(chats);
    // client.getc

});

client.initialize();

//---------------------------------------

const app = express();

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
        const chats = await client.getChats();
        const chat = chats.find(chat => chat.id.user === phoneNumber);
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

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

