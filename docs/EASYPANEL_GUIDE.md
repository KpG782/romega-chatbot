# 🚀 EasyPanel Deployment - Quick Start Guide

This is the FASTEST way to deploy your Romega Chatbot API to your VPS using EasyPanel.

## 📋 Prerequisites

1. ✅ VPS with EasyPanel installed
2. ✅ Google API Key (get from: https://aistudio.google.com/app/apikey)
3. ✅ Your project code

## 🎯 Step-by-Step Deployment

### Step 1: Access EasyPanel

Open your browser and go to:
```
http://your-vps-ip:3000
```

Login with your EasyPanel credentials.

### Step 2: Create New Application

1. Click **"+ New Project"** or **"Create Application"**
2. Give your project a name: `romega-chatbot`

### Step 3: Choose Deployment Method

#### Option A: From Git Repository (Recommended if code is on GitHub)

1. Click **"From Git Repository"**
2. Connect your GitHub account (if not already connected)
3. Select your repository
4. Select the branch (usually `main` or `master`)

#### Option B: Upload Files (If no Git repository)

1. Use SFTP/SCP to upload your project to VPS:
   ```bash
   scp -r romega-chatbot/ user@your-vps-ip:/home/user/
   ```

2. In EasyPanel, choose **"From Path"**
3. Enter the path: `/home/user/romega-chatbot`

### Step 4: Configure Build Settings

In the application settings:

**Build Configuration:**
- Build Method: **Dockerfile**
- Dockerfile Path: `./Dockerfile` (default)
- Build Context: `.` (default)

**Port Configuration:**
- Container Port: **8000**
- External Port: **8000** (or any port you prefer)

### Step 5: Set Environment Variables

Click on **"Environment Variables"** or **"Env"** tab and add:

```
GOOGLE_API_KEY=your_google_api_key_here
PORT=8000
```

⚠️ **IMPORTANT**: Replace `your_google_api_key_here` with your actual Google API key!

### Step 6: Deploy!

1. Click **"Deploy"** or **"Build & Deploy"** button
2. Wait for the build process (usually 3-5 minutes)
3. EasyPanel will:
   - Pull your code
   - Build the Docker image
   - Start the container
   - Map the ports

### Step 7: Verify Deployment

Once deployment is complete, EasyPanel will show you the URL.

**Test your deployment:**

1. **Health Check**
   ```
   http://your-vps-ip:8000/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "message": "Chatbot is ready to serve requests",
     "api_version": "1.0.0"
   }
   ```

2. **API Documentation**
   ```
   http://your-vps-ip:8000/docs
   ```
   Opens interactive Swagger UI

3. **Test Chat**
   ```
   http://your-vps-ip:8000/docs
   ```
   - Click on `/chat` endpoint
   - Click "Try it out"
   - Enter a message: `"What services does Romega offer?"`
   - Click "Execute"

## 🎨 EasyPanel Tips

### Viewing Logs

In EasyPanel:
1. Go to your application
2. Click **"Logs"** tab
3. View real-time logs

### Restarting Application

1. Go to your application
2. Click **"Restart"** button
3. Wait for container to restart

### Updating Application

When you push new code:
1. Go to your application
2. Click **"Rebuild"** or **"Redeploy"**
3. EasyPanel will pull latest code and rebuild

### Custom Domain Setup

1. In EasyPanel, go to your application
2. Click **"Domains"** tab
3. Add your domain: `chatbot.yourdomain.com`
4. EasyPanel automatically sets up SSL with Let's Encrypt
5. Wait for DNS propagation (5-30 minutes)

## 🔒 Security Settings in EasyPanel

### Enable HTTPS

1. Go to **"Domains"** tab
2. Add your domain
3. Toggle **"Enable SSL"**
4. EasyPanel handles Let's Encrypt automatically

### Resource Limits

Set appropriate resource limits:
- **Memory**: 1GB minimum (2GB recommended)
- **CPU**: 1 CPU core minimum

In EasyPanel:
1. Go to **"Resources"** tab
2. Set memory and CPU limits

## 📊 Monitoring in EasyPanel

### Check Container Status

In your application dashboard:
- **Status**: Should show "Running" with green indicator
- **Uptime**: How long container has been running
- **Memory Usage**: Current memory consumption
- **CPU Usage**: Current CPU usage

### Set Up Alerts (Optional)

1. Go to **"Alerts"** or **"Notifications"**
2. Configure alerts for:
   - Container crashes
   - High memory usage
   - High CPU usage

## 🔄 Common Operations

### Update Environment Variable

1. Go to your application
2. Click **"Environment"** tab
3. Edit `GOOGLE_API_KEY` value
4. Click **"Save"**
5. Click **"Restart"** for changes to take effect

### Scale Application

1. Go to **"Scale"** or **"Replicas"**
2. Increase number of instances
3. EasyPanel handles load balancing automatically

### View Application URL

In your application dashboard, EasyPanel shows:
- **Internal URL**: For container-to-container communication
- **External URL**: Public access URL

## 🆘 Troubleshooting

### Issue: Build Failed

**Check:**
1. Logs in EasyPanel build output
2. Dockerfile syntax
3. Missing files in repository

**Common causes:**
- Missing `requirements.txt`
- Missing `knowledge_base/romega_kb.json`
- Dockerfile errors

**Solution:**
- Review build logs
- Fix errors
- Redeploy

### Issue: Container Crashes

**Check:**
1. Application logs in EasyPanel
2. Environment variables set correctly
3. Google API key is valid

**Common causes:**
- Missing `GOOGLE_API_KEY`
- Invalid API key
- Insufficient memory

**Solution:**
- Set `GOOGLE_API_KEY` correctly
- Verify API key at https://aistudio.google.com/app/apikey
- Increase memory limit

### Issue: Cannot Access API

**Check:**
1. Container status (should be "Running")
2. Port mapping (8000:8000)
3. Firewall rules on VPS

**Solution:**
```bash
# On your VPS, check firewall
sudo ufw status
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Issue: 503 Error on /chat

**Check:**
1. Application logs
2. Initialization complete
3. API key valid

**Solution:**
- Wait 30-60 seconds after deployment (initialization time)
- Check logs for errors
- Verify `GOOGLE_API_KEY` is set

## 📱 Accessing Your API

After deployment, your API is available at:

### Direct IP Access
```
http://your-vps-ip:8000
```

### With Custom Domain (after DNS setup)
```
https://chatbot.yourdomain.com
```

### API Endpoints
```
GET  https://chatbot.yourdomain.com/
GET  https://chatbot.yourdomain.com/health
POST https://chatbot.yourdomain.com/chat
GET  https://chatbot.yourdomain.com/docs
```

## 🎯 Next Steps After Deployment

1. ✅ Test all endpoints
2. ✅ Set up custom domain (optional)
3. ✅ Enable SSL/HTTPS
4. ✅ Integrate with your frontend
5. ✅ Set up monitoring/alerts
6. ✅ Configure backups

## 📖 Additional Resources

- [Full Deployment Guide](DEPLOYMENT.md) - Detailed instructions for all deployment methods
- [API Documentation](http://your-vps-ip:8000/docs) - Interactive API docs
- [Project Overview](PROJECT_SUMMARY.md) - Complete project information
- [README](../README.md) - Development and usage guide

## ✅ Deployment Checklist

Before deploying, ensure:

- [ ] EasyPanel installed on VPS
- [ ] Google API key obtained
- [ ] Project code ready (in Git or on VPS)
- [ ] `.env` file configured (or env vars in EasyPanel)
- [ ] Dockerfile present in project root
- [ ] `knowledge_base/romega_kb.json` exists
- [ ] Port 8000 available or choose different port

During deployment:

- [ ] Created application in EasyPanel
- [ ] Set build method to Dockerfile
- [ ] Configured port 8000
- [ ] Set `GOOGLE_API_KEY` environment variable
- [ ] Clicked Deploy and waited for build

After deployment:

- [ ] Container shows "Running" status
- [ ] Health check endpoint responds
- [ ] Can access API documentation
- [ ] Chat endpoint works correctly
- [ ] Set up custom domain (optional)
- [ ] Enabled HTTPS (optional)

---

## 🎉 You're Done!

Your Romega Chatbot API is now live and accessible!

**Test it now:**
```bash
curl http://your-vps-ip:8000/health
```

**Use the interactive docs:**
```
http://your-vps-ip:8000/docs
```

For any issues, check the logs in EasyPanel or refer to [DEPLOYMENT.md](DEPLOYMENT.md).
