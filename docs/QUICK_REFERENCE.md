# 🚀 QUICK REFERENCE - Romega Chatbot API

## 📝 Essential Information

**Project**: Romega Chatbot - RAG-powered AI Assistant
**Technology**: Python + FastAPI + Google Gemini + ChromaDB
**Port**: 8000
**Deployment**: Docker + EasyPanel

---

## 🔑 Required Before Deployment

```env
GOOGLE_API_KEY=your_key_here
```

Get your key: https://aistudio.google.com/app/apikey

---

## ⚡ Quick Deploy Commands

### EasyPanel (Easiest)
1. Open: `http://your-vps-ip:3000`
2. Create Application → From Git/Path
3. Build Method: **Dockerfile**
4. Port: **8000**
5. Env: `GOOGLE_API_KEY=your_key`
6. Deploy!

### Docker Compose (Fast)
```bash
cp .env.example .env
nano .env  # Add GOOGLE_API_KEY
docker-compose up -d
```

### Docker Manual
```bash
docker build -t romega-chatbot .
docker run -d -p 8000:8000 --env-file .env --name romega-chatbot romega-chatbot
```

---

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/chat` | POST | Chat with bot |
| `/docs` | GET | Swagger UI |

---

## 🧪 Quick Tests

### Health Check
```bash
curl http://your-vps-ip:8000/health
```

### Chat Test
```bash
curl -X POST http://your-vps-ip:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega offer?"}'
```

### Interactive Docs
Open browser: `http://your-vps-ip:8000/docs`

---

## 🔍 Troubleshooting

### Check Container
```bash
docker ps | grep romega
```

### View Logs
```bash
docker logs romega-chatbot
# or with compose
docker-compose logs -f
```

### Restart
```bash
docker restart romega-chatbot
# or with compose
docker-compose restart
```

### Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

---

## 📊 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| 503 Error | Missing API key | Set `GOOGLE_API_KEY` in .env |
| Container crashes | Invalid API key | Check key at aistudio.google.com |
| Can't connect | Port blocked | `sudo ufw allow 8000/tcp` |
| Slow startup | Model loading | Wait 30-60 seconds |

---

## 🗂️ File Structure

```
romega-chatbot/
├── Dockerfile              ← Docker config
├── docker-compose.yml      ← Compose file
├── .env                    ← Your secrets (create this!)
├── requirements.txt        ← Python deps
├── src/
│   ├── api.py             ← FastAPI server
│   ├── agent.py           ← Chatbot agent
│   └── rag_pipeline.py    ← RAG logic
└── knowledge_base/
    └── romega_kb.json     ← Company data
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `../README.md` | Complete project guide |
| `DEPLOYMENT.md` | Detailed deployment steps |
| `EASYPANEL_GUIDE.md` | EasyPanel specific guide |
| `PROJECT_SUMMARY.md` | Overview & quick start |
| `ARCHITECTURE.md` | System diagrams |
| `QUICK_REFERENCE.md` | This file! |

---

## 🎯 Deployment Checklist

- [ ] Get Google API key
- [ ] Create `.env` file with API key
- [ ] Choose deployment method (EasyPanel/Docker)
- [ ] Deploy application
- [ ] Wait for initialization (30-60 sec)
- [ ] Test `/health` endpoint
- [ ] Test `/chat` endpoint
- [ ] Access `/docs` for interactive API

---

## 🌐 After Deployment

**Your API**: `http://your-vps-ip:8000`
**Docs**: `http://your-vps-ip:8000/docs`
**Health**: `http://your-vps-ip:8000/health`

---

## 🔒 Production Setup (Recommended)

1. Set up custom domain: `chatbot.yourdomain.com`
2. Configure reverse proxy (nginx/traefik)
3. Enable SSL with Let's Encrypt
4. Update CORS in `src/api.py`
5. Set up monitoring/logging
6. Configure backups

---

## 💡 Quick Tips

- **Memory**: Need at least 2GB RAM
- **Startup**: Takes 30-60 seconds to initialize
- **Logs**: Check logs if something goes wrong
- **Updates**: Rebuild container after code changes
- **Testing**: Use `/docs` for interactive testing

---

## 🆘 Need Help?

1. Check logs: `docker logs romega-chatbot`
2. Read: `DEPLOYMENT.md` for detailed steps
3. Test: Use `/docs` endpoint for debugging
4. Verify: API key is valid and set correctly

---

## 📞 Integration Example

```javascript
// JavaScript
fetch('http://your-vps-ip:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Hello!'})
})
.then(r => r.json())
.then(data => console.log(data.response));
```

```python
# Python
import requests
response = requests.post(
    'http://your-vps-ip:8000/chat',
    json={'message': 'Hello!'}
)
print(response.json()['response'])
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | - | Gemini API key |
| `PORT` | ❌ No | 8000 | API server port |

---

## 🚀 Success Indicators

✅ Container status: **Running**
✅ Health endpoint: **Returns 200 OK**
✅ Chat endpoint: **Returns AI response**
✅ Docs: **Accessible and interactive**

---

**You're all set! 🎉**

For more details, see [README.md](../README.md) or [DEPLOYMENT.md](DEPLOYMENT.md)
