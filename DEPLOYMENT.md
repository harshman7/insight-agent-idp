# DocSage Deployment Guide

This guide covers deploying DocSage to **Railway** (free tier available) with free LLM APIs.

## 🚀 Quick Start: Railway Deployment

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app) (free tier includes $5 credit/month)
2. **Groq API Key** (Recommended - Free): Get from [console.groq.com](https://console.groq.com)
   - Alternative: Hugging Face API key from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### Step 1: Prepare Your Repository

1. Push your code to GitHub
2. Make sure all files are committed

### Step 2: Deploy Backend (FastAPI) to Railway

1. Go to [railway.app](https://railway.app) and create a new project
2. Click "New" → "GitHub Repo" → Select your repository
3. Railway will detect the Dockerfile and start building
4. Add environment variables:
   - `LLM_PROVIDER=groq` (or `huggingface` or `ollama`)
   - `GROQ_API_KEY=your_groq_api_key` (if using Groq)
   - `HUGGINGFACE_API_KEY=your_hf_key` (if using Hugging Face)
   - `POSTGRES_HOST=${{Postgres.PGHOST}}` (Railway will provide this)
   - `POSTGRES_USER=${{Postgres.PGUSER}}`
   - `POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}`
   - `POSTGRES_DB=${{Postgres.PGDATABASE}}`
   - `POSTGRES_PORT=${{Postgres.PGPORT}}`
   - `USE_SQLITE=False`

### Step 3: Add PostgreSQL Database

1. In Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically create the database
3. The connection variables are automatically available to your services

### Step 4: Deploy Frontend (Streamlit) to Railway

1. Create a new service in the same Railway project
2. Set the Dockerfile path to `Dockerfile.frontend`
3. Add environment variables:
   - `API_HOST=your-backend-service.railway.app` (or use Railway's internal networking)
   - `API_PORT=8000`

### Step 5: Initialize Database

1. Connect to your Railway PostgreSQL database
2. Run the migration:
   ```bash
   # Using Railway CLI
   railway run python scripts/migrate_database.py
   ```

3. Seed the database (optional):
   ```bash
   railway run python scripts/seed_db.py
   ```

### Step 6: Configure Domains

1. In Railway, go to your service settings
2. Click "Generate Domain" to get a public URL
3. Your app will be available at `https://your-app.railway.app`

## 🔧 Alternative: Render Deployment

### Backend Deployment

1. Go to [render.com](https://render.com)
2. Create new "Web Service"
3. Connect your GitHub repository
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. Add environment variables (same as Railway)

### Frontend Deployment

1. Create new "Web Service" for Streamlit
2. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
3. Add environment variables

### PostgreSQL on Render

1. Create new "PostgreSQL" database
2. Use the connection string provided

## 🆓 Free LLM API Setup

### Option 1: Groq (Recommended - Fastest)

1. Sign up at [console.groq.com](https://console.groq.com)
2. Get your API key
3. Set environment variables:
   ```bash
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```

**Free Tier**: Very generous, fast responses

### Option 2: Hugging Face Inference API

1. Sign up at [huggingface.co](https://huggingface.co)
2. Create API token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Set environment variables:
   ```bash
   LLM_PROVIDER=huggingface
   HUGGINGFACE_API_KEY=your_token_here
   HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
   ```

**Free Tier**: Limited requests, may have rate limits

### Option 3: Keep Using Ollama (Not Recommended for Cloud)

If you want to use Ollama, you'll need to:
1. Deploy Ollama on a separate VM (Oracle Cloud Always Free)
2. Set `OLLAMA_BASE_URL` to your Ollama instance
3. Set `LLM_PROVIDER=ollama`

## 📝 Environment Variables Reference

### Required for All Deployments

```bash
# LLM Provider
LLM_PROVIDER=groq  # or "huggingface" or "ollama"

# Database (provided by Railway/Render for managed PostgreSQL)
POSTGRES_HOST=your_host
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=docsage
POSTGRES_PORT=5432
USE_SQLITE=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### For Groq

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

### For Hugging Face

```bash
HUGGINGFACE_API_KEY=your_hf_token
HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

### For Ollama (Local/VM)

```bash
OLLAMA_BASE_URL=http://your-ollama-instance:11434
OLLAMA_MODEL=llama3
```

## 🐳 Docker Compose (Local Production)

For local production-like deployment:

```bash
# Build and run
docker-compose -f docker-compose.prod.yml up -d

# Or use the provided docker-compose.yml and add services
```

## 🔍 Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL service is running
- Check environment variables are set correctly
- Verify database exists: `railway run psql -l`

### LLM API Errors

- **Groq**: Check API key is valid, check rate limits
- **Hugging Face**: May need to wait for model to load (first request)
- **Ollama**: Ensure Ollama service is accessible

### Build Failures

- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt
- Check build logs in Railway/Render dashboard

## 📊 Cost Estimation (Free Tier)

### Railway
- **Free Tier**: $5 credit/month
- **Backend**: ~$0-2/month (sleeps when inactive)
- **Frontend**: ~$0-2/month (sleeps when inactive)
- **PostgreSQL**: Included in free tier
- **Total**: **$0/month** for low usage

### Render
- **Free Tier**: PostgreSQL + Web Services
- **Backend**: Free (sleeps after 15 min)
- **Frontend**: Free (sleeps after 15 min)
- **PostgreSQL**: Free tier available
- **Total**: **$0/month** for low usage

### Groq API
- **Free Tier**: Very generous limits
- **Cost**: **$0/month** for typical usage

## 🎯 Next Steps

1. Set up monitoring (optional): Add health checks
2. Configure custom domain (optional): Use Railway/Render domain features
3. Set up CI/CD: Auto-deploy on git push
4. Add backups: Configure database backups

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Groq API Documentation](https://console.groq.com/docs)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference)

---

**Need Help?** Check the [README.md](README.md) for local setup or open an issue on GitHub.

