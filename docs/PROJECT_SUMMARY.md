# 🚀 Romega Chatbot - Complete Project Overview

## 📋 What I Created

I've set up a complete Docker deployment flow for your Romega chatbot project to be available as an API on your VPS with EasyPanel.

### **Existing Flow Analysis**

Your project has a RAG (Retrieval-Augmented Generation) pipeline:

1. **Knowledge Base** (`romega_kb.json`) - Contains all information about Romega Solutions
2. **RAG Pipeline** (`rag_pipeline.py`) - 5-step process:
   - Extract → Chunk → Embed → Vectorize → Retrieve
3. **Agent** (`agent.py`) - Integrates RAG with Google Gemini AI
4. **Flow**: User Query → Vector Search → Retrieve Context → Gemini AI → Response

### **New Files Created**

#### 1. **src/api.py** - FastAPI REST API
- Exposes your chatbot as a REST API
- Endpoints: `/chat`, `/health`, `/docs`
- CORS enabled for cross-origin requests
- Automatic Swagger UI documentation

#### 2. **Dockerfile** - Container Configuration
- Based on Python 3.11-slim
- Installs all dependencies
- Sets up non-root user for security
- Health checks built-in
- Exposes port 8000

#### 3. **docker-compose.yml** - Easy Deployment
- One-command deployment
- Environment variable management
- Auto-restart on failure
- Health monitoring

#### 4. **.dockerignore** - Build Optimization
- Excludes unnecessary files from Docker image
- Reduces image size
- Faster builds

#### 5. **.env.example** - Environment Template
- Template for configuration
- Documents required variables

#### 6. **DEPLOYMENT.md** - Complete Deployment Guide
- Step-by-step instructions for EasyPanel
- Manual Docker deployment
- Docker Compose deployment
- Troubleshooting guide
- Security recommendations

#### 7. **README.md** - Project Documentation
- Complete project overview
- Quick start guide
- API usage examples
- Development instructions

#### 8. **test_api.sh** - API Testing Script
- Automated API endpoint testing
- Validates deployment

#### 9. **Makefile** - Convenience Commands
- Easy-to-use commands for common tasks

### **Path Fix Applied**

Updated `rag_pipeline.py` to handle different working directories:
- Works in local development
- Works in Docker container
- Automatically finds knowledge base file

## 🎯 How to Deploy to Your VPS with EasyPanel

### **Option 1: EasyPanel (Easiest)**

1. **Login to EasyPanel**
   ```
   http://your-vps-ip:3000
   ```

2. **Create New Application**
   - Click "Create Application"
   - Choose "Git Repository" or upload code

3. **Configure**
   - Build Method: Dockerfile
   - Port: 8000
   - Environment Variable: `GOOGLE_API_KEY=your_key_here`

4. **Deploy**
   - Click "Deploy" button
   - Wait for build to complete

5. **Access Your API**
   ```
   http://your-vps-ip:8000/docs
   ```

### **Option 2: Direct Docker Deployment**

```bash
# 1. SSH to your VPS
ssh user@your-vps-ip

# 2. Clone/upload your project
cd /path/to/romega-chatbot

# 3. Create .env file
cp .env.example .env
nano .env  # Add your GOOGLE_API_KEY

# 4. Deploy with Docker Compose (EASIEST)
docker-compose up -d

# OR build and run manually
docker build -t romega-chatbot .
docker run -d -p 8000:8000 --env-file .env --name romega-chatbot romega-chatbot
```

## 📡 Your API Endpoints

Once deployed, you'll have these endpoints:

### **GET /** - API Info
```bash
curl http://your-vps-ip:8000/
```

### **GET /health** - Health Check
```bash
curl http://your-vps-ip:8000/health
```

### **POST /chat** - Chat with Bot
```bash
curl -X POST http://your-vps-ip:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega offer?"}'
```

Response:
```json
{
  "response": "Romega Solutions offers...",
  "status": "success"
}
```

### **GET /docs** - Interactive API Documentation
```
http://your-vps-ip:8000/docs
```

## 🔑 Required: Get Your Google API Key

Before deploying, you MUST get a Google API key:

1. Go to: https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy it to your `.env` file:
   ```
   GOOGLE_API_KEY=your_actual_key_here
   ```

## 🧪 Testing Your Deployment

### **Quick Health Check**
```bash
curl http://your-vps-ip:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Chatbot is ready to serve requests",
  "api_version": "1.0.0"
}
```

### **Test Chat**
```bash
curl -X POST http://your-vps-ip:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Romega"}'
```

### **Use Test Script**
```bash
bash test_api.sh
```

## 🔐 Security Checklist

- [ ] Set `GOOGLE_API_KEY` in environment (NEVER commit to git)
- [ ] Update CORS settings in `src/api.py` for production
- [ ] Set up reverse proxy with SSL (nginx + Let's Encrypt)
- [ ] Configure firewall to allow only port 80/443
- [ ] Consider adding API authentication
- [ ] Set up monitoring and logging

## 📊 Monitoring Your Deployment

### **Check Container Status**
```bash
docker ps | grep romega-chatbot
```

### **View Logs**
```bash
# Docker Compose
docker-compose logs -f

# Direct Docker
docker logs -f romega-chatbot
```

### **Check Resource Usage**
```bash
docker stats romega-chatbot
```

## 🔄 Updating Your Application

```bash
# With Docker Compose
docker-compose down
docker-compose up -d --build

# With Docker
docker stop romega-chatbot
docker rm romega-chatbot
docker build -t romega-chatbot .
docker run -d -p 8000:8000 --env-file .env --name romega-chatbot romega-chatbot
```

## 💡 Integration Examples

### **HTML/JavaScript Frontend**
```html
<script>
async function askRomega(question) {
  const response = await fetch('http://your-vps-ip:8000/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: question})
  });
  const data = await response.json();
  console.log(data.response);
}

askRomega("What services does Romega offer?");
</script>
```

### **Python Client**
```python
import requests

def chat_with_romega(message):
    response = requests.post(
        'http://your-vps-ip:8000/chat',
        json={'message': message}
    )
    return response.json()['response']

# Use it
answer = chat_with_romega("How much does RPO cost?")
print(answer)
```

### **cURL**
```bash
curl -X POST http://your-vps-ip:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Contact information please"}'
```

## 🎨 Customization Options

### **Change Port**
Edit `.env`:
```env
PORT=3000
```

Update `docker-compose.yml`:
```yaml
ports:
  - "3000:3000"
```

### **Update Knowledge Base**
1. Edit `knowledge_base/romega_kb.json`
2. Rebuild container:
   ```bash
   docker-compose up -d --build
   ```

### **Change AI Model**
Edit `src/agent.py`:
```python
self.model = genai.GenerativeModel(
    model_name='gemini-pro',  # Change this
    system_instruction=self.system_instruction
)
```

### **Adjust CORS Settings**
Edit `src/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🆘 Troubleshooting

### **Issue: Container won't start**
```bash
# Check logs
docker logs romega-chatbot

# Common causes:
# - Missing GOOGLE_API_KEY
# - Port 8000 already in use
# - Invalid knowledge_base path
```

### **Issue: API returns 503**
```bash
# Check if API key is valid
# View initialization logs
docker logs romega-chatbot | grep "Initializing"

# Restart container
docker restart romega-chatbot
```

### **Issue: High memory usage**
- Normal! Sentence-transformers model loads into memory
- Ensure VPS has at least 2GB RAM
- Consider upgrading VPS if needed

### **Issue: Connection refused**
```bash
# Check if container is running
docker ps | grep romega

# Check port mapping
docker port romega-chatbot

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

## 📈 Next Steps

1. **Deploy to VPS** - Follow deployment guide
2. **Test endpoints** - Use test script or Swagger UI
3. **Set up domain** - Point domain to your VPS
4. **Configure SSL** - Use nginx + Let's Encrypt
5. **Add monitoring** - Set up logging and alerts
6. **Integrate with website** - Use API in your frontend

## 📞 Getting Help

- Check logs: `docker logs romega-chatbot`
- Review [DEPLOYMENT.md](DEPLOYMENT.md)
- Visit API docs: `http://your-vps-ip:8000/docs`
- Test with Swagger UI for interactive testing

## ✅ Pre-Deployment Checklist

- [ ] Google API Key obtained and added to `.env`
- [ ] VPS with Docker installed
- [ ] EasyPanel installed (optional)
- [ ] Firewall configured
- [ ] Code uploaded to VPS
- [ ] `.env` file created with API key
- [ ] Docker image built successfully
- [ ] Container running
- [ ] Health check passes
- [ ] Test chat request works
- [ ] API documentation accessible

---

**Your chatbot is now ready to deploy as an API! 🎉**

Choose your deployment method (EasyPanel or Docker) and follow the instructions above.
