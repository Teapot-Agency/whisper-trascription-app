# 🚀 Deployment Guide for Whisper Transcription App

## 📁 Project Setup

### 1. Local Setup with .env file

1. Create a `.env` file in your project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
streamlit run transcription_app.py
```

## 🌐 Online Deployment Options

### Option 1: Streamlit Community Cloud (FREE & EASIEST)

**Perfect for personal projects and demos**

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/whisper-transcription-app.git
   git push -u origin main
   ```

2. **Set up Supabase (Optional but Recommended for persistent storage):**
   - Follow the [DATABASE_SETUP.md](DATABASE_SETUP.md) guide
   - Get your Supabase URL and anon key

3. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `transcription_app_cloud.py` (for cloud with database)
   - Or use `transcription_app.py` (for local SQLite version)

4. **Add Secrets:**
   - In Streamlit Cloud dashboard, go to your app
   - Click "Settings" → "Secrets"
   - Add:
   ```toml
   OPENAI_API_KEY = "sk-your-api-key-here"
   
   # Optional: For persistent storage
   SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

5. **Your app will be live at:** `https://YOUR_USERNAME-whisper-transcription-app.streamlit.app`

### Option 2: Heroku (Paid - Starting $7/month)

1. **Create `Procfile`:**
   ```
   web: sh setup.sh && streamlit run transcription_app.py
   ```

2. **Create `setup.sh`:**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=sk-your-api-key-here
   git push heroku main
   ```

### Option 3: Railway (Simple & Modern)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Add environment variable in Railway dashboard:**
   - Go to your project
   - Variables → Add Variable
   - `OPENAI_API_KEY` = `sk-your-api-key-here`

### Option 4: Render (Free tier available)

1. **Create `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: whisper-transcription
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run transcription_app.py --server.port $PORT
       envVars:
         - key: OPENAI_API_KEY
           sync: false
   ```

2. **Deploy:**
   - Push to GitHub
   - Connect GitHub to Render
   - Add environment variable in dashboard

### Option 5: Google Cloud Run

1. **Create `Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   
   CMD streamlit run transcription_app.py \
       --server.port 8080 \
       --server.address 0.0.0.0
   ```

2. **Deploy:**
   ```bash
   gcloud run deploy whisper-transcription \
       --source . \
       --region us-central1 \
       --set-env-vars OPENAI_API_KEY=sk-your-api-key-here
   ```

## 🔒 Security Best Practices

1. **Never commit `.env` files to Git**
2. **Use environment variables for all sensitive data**
3. **Set up usage limits in OpenAI dashboard**
4. **Consider adding authentication for production apps**

## 💰 Cost Considerations

- **Streamlit Cloud:** FREE for public apps (3 apps limit)
- **Heroku:** ~$7/month for basic dyno
- **Railway:** ~$5/month (pay as you go)
- **Render:** Free tier with limitations, ~$7/month for starter
- **Google Cloud Run:** Pay per use, ~$0-10/month for light usage

## 📊 OpenAI API Costs

- Whisper API: $0.006 per minute of audio
- Example: 100 minutes = $0.60

## 🔧 Advanced Configuration

### Add Authentication (for production)

1. **Using Streamlit-Authenticator:**
   ```python
   import streamlit_authenticator as stauth
   
   # Add to requirements.txt:
   # streamlit-authenticator==0.3.1
   ```

2. **Configure in `.streamlit/secrets.toml`:**
   ```toml
   [passwords]
   usernames = ["admin", "user1"]
   passwords = ["hashed_password1", "hashed_password2"]
   ```

### Add Database for Persistent Storage

1. **Using Supabase (free tier):**
   ```python
   from supabase import create_client, Client
   
   # Add to requirements.txt:
   # supabase==2.4.0
   ```

2. **Set up in environment:**
   ```
   SUPABASE_URL=your-project-url
   SUPABASE_KEY=your-anon-key
   ```

## 🎉 You're Ready!

Choose the deployment option that best fits your needs and budget. Streamlit Community Cloud is recommended for getting started quickly and for free!