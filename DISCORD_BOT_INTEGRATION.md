# Discord Bot Integration Guide

## 🚀 **Your Discord Notes Web Interface is Ready!**

### **What's Built:**

1. **Web Interface**: Sign in/Sign up with Discord User ID + Password + Notes management dashboard
2. **API Backend**: FastAPI with JWT authentication, password protection, and full CRUD for notes
3. **Database**: MongoDB storing users (with hashed passwords) and notes
4. **Integration Ready**: API endpoints for your JavaScript Discord bot

---

## 📋 **API Endpoints for Your JavaScript Discord Bot**

### **Base URL:** `https://discord-notes.preview.emergentagent.com/api`

### **Authentication Endpoints:**

#### **1. Register User**
```javascript
POST /api/auth/register
{
  "discord_user_id": "123456789012345678",
  "username": "MyUsername",
  "password": "securepassword123"
}
```

#### **2. Login User**  
```javascript
POST /api/auth/login
{
  "discord_user_id": "123456789012345678",
  "password": "securepassword123"
}
```

### **Bot Endpoints (No Auth Required):**

#### **1. Create Note** 
```javascript
POST /api/notes
{
  "discord_user_id": "123456789012345678",
  "content": "Your note content here",
  "server_id": "server123", // optional
  "server_name": "My Server", // optional  
  "channel_id": "channel456", // optional
  "channel_name": "general" // optional
}
```

#### **2. Get User Notes**
```javascript
GET /api/bot/notes/{discord_user_id}?limit=10
```

#### **3. Search Notes**
```javascript  
GET /api/bot/notes/{discord_user_id}/search?q=search_term&limit=5
```

#### **4. Delete Note**
```javascript
DELETE /api/bot/notes/{note_id}
```

---

## 🤖 **JavaScript Discord Bot Example**

```javascript
const axios = require('axios');

const API_BASE = 'https://discord-notes.preview.emergentagent.com/api';

class NotesBot {
  async addNote(userId, content, serverInfo = {}) {
    try {
      const response = await axios.post(`${API_BASE}/notes`, {
        discord_user_id: userId,
        content: content,
        server_id: serverInfo.serverId,
        server_name: serverInfo.serverName,
        channel_id: serverInfo.channelId,
        channel_name: serverInfo.channelName
      });
      return response.data;
    } catch (error) {
      console.error('Failed to add note:', error);
      return null;
    }
  }

  async getUserNotes(userId, limit = 10) {
    try {
      const response = await axios.get(`${API_BASE}/bot/notes/${userId}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get notes:', error);
      return [];
    }
  }

  async searchNotes(userId, query, limit = 5) {
    try {
      const response = await axios.get(`${API_BASE}/bot/notes/${userId}/search?q=${encodeURIComponent(query)}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Failed to search notes:', error);
      return [];
    }
  }

  async deleteNote(noteId) {
    try {
      await axios.delete(`${API_BASE}/bot/notes/${noteId}`);
      return true;
    } catch (error) {
      console.error('Failed to delete note:', error);
      return false;
    }
  }
}

// Usage in your Discord bot
const notesBot = new NotesBot();

// Discord.js example commands
client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  
  const args = message.content.split(' ');
  const command = args[0].toLowerCase();

  switch (command) {
    case '!note':
      if (args[1] === 'add' && args.length > 2) {
        const content = args.slice(2).join(' ');
        const serverInfo = {
          serverId: message.guild?.id,
          serverName: message.guild?.name,
          channelId: message.channel.id,
          channelName: message.channel.name
        };
        
        const note = await notesBot.addNote(message.author.id, content, serverInfo);
        if (note) {
          message.reply(`✅ Note saved! ID: ${note.id}`);
        } else {
          message.reply('❌ Failed to save note.');
        }
      }
      break;

    case '!notes':
      const notes = await notesBot.getUserNotes(message.author.id, 5);
      if (notes.length === 0) {
        message.reply('📝 You have no notes yet.');
      } else {
        const notesList = notes.map((note, index) => 
          `${index + 1}. **${note.content.substring(0, 50)}${note.content.length > 50 ? '...' : ''}** (ID: ${note.id})`
        ).join('\n');
        message.reply(`📝 Your recent notes:\n${notesList}`);
      }
      break;

    case '!search':
      if (args.length > 1) {
        const query = args.slice(1).join(' ');
        const results = await notesBot.searchNotes(message.author.id, query);
        if (results.length === 0) {
          message.reply(`🔍 No notes found for "${query}".`);
        } else {
          const resultsList = results.map(note => 
            `• **${note.content.substring(0, 100)}${note.content.length > 100 ? '...' : ''}** (ID: ${note.id})`
          ).join('\n');
          message.reply(`🔍 Search results for "${query}":\n${resultsList}`);
        }
      }
      break;

    case '!delete':
      if (args.length > 1) {
        const noteId = args[1];
        const success = await notesBot.deleteNote(noteId);
        if (success) {
          message.reply('✅ Note deleted successfully!');
        } else {
          message.reply('❌ Failed to delete note. Check the note ID.');
        }
      }
      break;
  }
});
```

---

## 🌐 **Web Interface Features**

Users can visit the web interface to:

1. **Sign In/Sign Up** with their Discord User ID
2. **View All Notes** taken via Discord commands  
3. **Search & Filter** notes by content or server
4. **Edit Notes** directly in the web interface
5. **Delete Notes** with confirmation
6. **Organize Notes** by server/channel information

### **How Users Get Their Discord User ID:**
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click their username → Copy ID
3. Use this ID to sign up on the web interface

---

## 🔧 **Installation Commands for Your Bot**

Add to your `package.json`:
```json
{
  "dependencies": {
    "axios": "^1.8.4"
  }
}
```

Then: `npm install axios`

---

## 🎯 **Bot Commands Summary**

| Command | Description | Example |
|---------|-------------|---------|
| `!note add <content>` | Save a new note | `!note add Remember to buy milk` |
| `!notes` | List recent notes | `!notes` |
| `!search <query>` | Search notes | `!search milk` |
| `!delete <note_id>` | Delete a note | `!delete abc123` |

---

## ✅ **Testing the Integration**

1. **Test API directly:**
   ```bash
   curl -X POST "https://discord-notes.preview.emergentagent.com/api/notes" \
   -H "Content-Type: application/json" \
   -d '{"discord_user_id": "123456789", "content": "Test note from curl"}'
   ```

2. **Test web interface:**
   - Visit: https://discord-notes.preview.emergentagent.com
   - Sign up with a Discord User ID
   - View your notes dashboard

3. **Integration test:**
   - Add notes via your Discord bot
   - Check they appear in the web interface
   - Edit notes on web, verify they're updated

---

**🎉 Your Discord Notes system is fully functional and ready to use!**