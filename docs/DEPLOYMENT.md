# Romega Chatbot - Deployment Guide for EasyPanel

This guide will help you deploy the Romega Chatbot as an API on your Virtual Private Server using EasyPanel.

## 📋 Prerequisites

1. A VPS with Docker installed
2. EasyPanel installed on your VPS
3. Google API Key for Gemini (get from: https://aistudio.google.com/app/apikey)

## 🚀 Deployment Options

### Option 1: Deploy via EasyPanel (Recommended)

1. **Login to EasyPanel Dashboard**
   - Access your EasyPanel at: `http://your-vps-ip:3000`

2. **Create New Application**
   - Click "Create Application"
   - Choose "GitHub" or "Git Repository"
   - Connect your repository or upload your code

3. **Configure Environment Variables**
   - Add the following environment variable:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```

4. **Configure Build Settings**
   - Build Method: Dockerfile
   - Dockerfile Path: `./Dockerfile`
   - Port: `8000`

5. **Deploy**
   - Click "Deploy"
   - Wait for the build and deployment to complete

### Option 2: Manual Docker Deployment

1. **Copy files to your VPS**
   ```bash
   scp -r romega-chatbot/ user@your-vps-ip:/path/to/deployment/
   ```

2. **SSH into your VPS**
   ```bash
   ssh user@your-vps-ip
   cd /path/to/deployment/romega-chatbot
   ```

3. **Create .env file**
   ```bash
   cp .env.example .env
   nano .env  # Edit and add your GOOGLE_API_KEY
   ```

4. **Build and Run with Docker**
   ```bash
   # Build the image
   docker build -t romega-chatbot:latest .
   
   # Run the container
   docker run -d \
     --name romega-chatbot \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     romega-chatbot:latest
   ```

### Option 3: Docker Compose Deployment

1. **Prepare the environment**
   ```bash
   cd /path/to/romega-chatbot
   cp .env.example .env
   nano .env  # Add your GOOGLE_API_KEY
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Your Google Gemini API key | Yes | - |
| `PORT` | Port for the API server | No | 8000 |

### Port Configuration

The application runs on port `8000` by default. You can change this by:
- Setting the `PORT` environment variable
- Modifying the port mapping in docker-compose.yml or docker run command

## 📡 API Endpoints

Once deployed, your API will be available at: `http://your-vps-ip:8000`

### Available Endpoints:

- `GET /` - API information
- `GET /health` - Health check endpoint
- `POST /chat` - Send a message to the chatbot
- `GET /docs` - Swagger UI documentation (interactive)
- `GET /redoc` - ReDoc documentation

### Example API Usage:

```bash
# Health Check
curl http://your-vps-ip:8000/health

# Send a chat message
curl -X POST http://your-vps-ip:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega offer?"}'
```

### Example Response:

```json
{
  "response": "Romega Solutions offers several key services including...",
  "status": "success"
}
```

## 🔐 Security Recommendations

1. **Use HTTPS**: Set up a reverse proxy (nginx/traefik) with SSL certificate
2. **Environment Variables**: Never commit .env file to git
3. **API Rate Limiting**: Consider adding rate limiting middleware
4. **CORS Configuration**: Update allowed origins in production (src/api.py)
5. **Firewall**: Configure firewall to only allow necessary ports

## 🛠️ Troubleshooting

### Container won't start
```bash
# Check logs
docker logs romega-chatbot

# Check if port is already in use
netstat -tulpn | grep 8000
```

### API returns 503 error
- Check if GOOGLE_API_KEY is set correctly
- Verify the API key is valid at https://aistudio.google.com/app/apikey
- Check container logs for initialization errors

### High memory usage
- The sentence-transformers model loads into memory on startup
- Ensure your VPS has at least 2GB RAM available

## 📊 Monitoring

### Check Application Status
```bash
# Docker status
docker ps | grep romega-chatbot

# Health check
curl http://localhost:8000/health

# View logs
docker logs -f romega-chatbot
```

### Resource Usage
```bash
# Check container stats
docker stats romega-chatbot
```

## 🔄 Updates and Maintenance

### Update the Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or with docker
docker stop romega-chatbot
docker rm romega-chatbot
docker build -t romega-chatbot:latest .
docker run -d --name romega-chatbot -p 8000:8000 --env-file .env romega-chatbot:latest
```

### Backup
```bash
# Backup knowledge base
docker cp romega-chatbot:/app/knowledge_base ./backup/

# Backup vector database (if persistent)
docker cp romega-chatbot:/app/chroma_data ./backup/
```

## 🌐 Domain Setup (Optional)

1. Point your domain to your VPS IP
2. Set up reverse proxy (nginx or traefik)
3. Configure SSL with Let's Encrypt
4. Update CORS settings in src/api.py

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name chatbot.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Support

For issues or questions:
- Check logs: `docker logs romega-chatbot`
- Review API documentation: `http://your-vps-ip:8000/docs`
- Contact: info@romega-solutions.com

## 🎯 Quick Start Checklist

- [ ] VPS/Server with Docker installed
- [ ] EasyPanel installed (optional)
- [ ] Google API Key obtained
- [ ] Repository cloned/uploaded
- [ ] .env file created with GOOGLE_API_KEY
- [ ] Application built and deployed
- [ ] Health check endpoint responds successfully
- [ ] Test chat endpoint with sample message
- [ ] Configure firewall/security settings
- [ ] Set up monitoring/logging (optional)
- [ ] Configure domain and SSL (optional)
