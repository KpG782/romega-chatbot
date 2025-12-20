# Romega Chatbot - RAG-Powered API

🤖 An intelligent chatbot API for Romega Solutions, powered by Google's Gemini AI and Retrieval-Augmented Generation (RAG).

## 🌟 Features

- **RAG Pipeline**: Retrieves relevant information from knowledge base before generating responses
- **Google Gemini Integration**: Uses Gemini 2.0 Flash for intelligent, context-aware responses
- **REST API**: FastAPI-based API for easy integration
- **Docker Support**: Containerized for easy deployment
- **EasyPanel Compatible**: Ready to deploy on your VPS with EasyPanel
- **Vector Search**: ChromaDB for semantic search across company knowledge
- **Interactive Documentation**: Swagger UI and ReDoc included

## 🏗️ Project Structure

```
romega-chatbot/
├── src/
│   ├── agent.py           # Main chatbot agent with Gemini integration
│   ├── rag_pipeline.py    # RAG pipeline (Extract → Chunk → Embed → Vectorize → Retrieve)
│   ├── api.py             # FastAPI REST API application
│   └── vector_store.py    # Vector storage utilities
├── knowledge_base/
│   └── romega_kb.json     # Company knowledge base
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose for easy deployment
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── DEPLOYMENT.md         # Detailed deployment guide
└── README.md            # This file
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd romega-chatbot
   ```

2. **Set up environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

4. **Run the API**
   ```bash
   cd src
   python api.py
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   docker-compose up -d
   ```

2. **Or build manually**
   ```bash
   docker build -t romega-chatbot .
   docker run -d -p 8000:8000 --env-file .env romega-chatbot
   ```

3. **Check health**
   ```bash
   curl http://localhost:8000/health
   ```

## 📡 API Usage

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/chat` | Send a message to chatbot |
| GET | `/docs` | Swagger UI (interactive) |
| GET | `/redoc` | ReDoc documentation |

### Example Requests

**Chat with the bot:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega offer?"}'
```

**Response:**
```json
{
  "response": "Romega Solutions offers several key services including Recruitment Process Outsourcing (RPO), Business Process Outsourcing (BPO), Strategic HR Consulting, and Quality Hire solutions...",
  "status": "success"
}
```

**Health Check:**
```bash
curl http://localhost:8000/health
```

### Using Python

```python
import requests

# Send a chat message
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "How much does RPO cost?"}
)

print(response.json())
```

### Using JavaScript

```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'What is Romega\'s retention rate?'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
GOOGLE_API_KEY=your_google_api_key_here
PORT=8000
```

Get your Google API key from: https://aistudio.google.com/app/apikey

### Customization

- **Update knowledge base**: Edit `knowledge_base/romega_kb.json`
- **Change model**: Modify `model_name` in `src/agent.py`
- **Adjust CORS**: Update `allow_origins` in `src/api.py`
- **Port configuration**: Set `PORT` environment variable

## 🐳 Deployment to VPS with EasyPanel

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions on deploying to your VPS using EasyPanel or manual Docker deployment.

**Quick Steps:**
1. Install EasyPanel on your VPS
2. Create new application in EasyPanel
3. Connect your Git repository
4. Set `GOOGLE_API_KEY` environment variable
5. Deploy with Dockerfile
6. Access at `http://your-vps-ip:8000`

## 📚 How It Works

### RAG Pipeline

The chatbot uses a 5-step RAG pipeline:

1. **Extract**: Load knowledge base from JSON
2. **Chunk**: Break content into semantic chunks
3. **Embed**: Convert chunks to vector embeddings using SentenceTransformers
4. **Vectorize**: Store embeddings in ChromaDB vector database
5. **Retrieve**: Find most relevant chunks for user queries

### Query Flow

```
User Query → Embed Query → Vector Search → Retrieve Top-K Chunks
    ↓
Context + Query → Gemini AI → Generate Response → Return to User
```

## 🛠️ Development

### Running Tests

```bash
# Test the RAG pipeline
cd src
python rag_pipeline.py

# Test the agent
python agent.py

# Test the API (requires running server)
bash test_api.sh
```

### Project Components

- **agent.py**: Main chatbot agent with Gemini integration
- **rag_pipeline.py**: RAG pipeline implementation
- **api.py**: FastAPI REST API application
- **vector_store.py**: Vector database utilities

## 📦 Dependencies

- `google-adk>=0.3.0` - Google AI Development Kit
- `google-generativeai>=0.4.0` - Gemini AI API
- `chromadb>=0.4.22` - Vector database
- `sentence-transformers>=2.3.1` - Text embeddings
- `fastapi>=0.109.0` - Web framework
- `uvicorn>=0.27.0` - ASGI server
- `python-dotenv>=1.0.0` - Environment management

See [requirements.txt](requirements.txt) for complete list.

## 📚 Documentation

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Quick command cheat sheet
- **[EasyPanel Guide](docs/EASYPANEL_GUIDE.md)** - Step-by-step EasyPanel deployment
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Complete project overview
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture & diagrams

## 🔐 Security

- Never commit `.env` file or API keys
- Use environment variables for sensitive data
- Configure CORS appropriately for production
- Consider adding API authentication
- Use HTTPS with SSL certificate in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Your License Here]

## 📞 Support

- Email: info@romega-solutions.com
- Website: www.romega-solutions.com

## 🎯 Roadmap

- [ ] Add authentication/API keys
- [ ] Implement rate limiting
- [ ] Add conversation history
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] WebSocket support for real-time chat
- [ ] Integration examples (Slack, Discord, etc.)

---

Built with ❤️ for Romega Solutions
