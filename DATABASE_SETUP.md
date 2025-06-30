# 🗄️ Database Setup Guide

This app now includes database support to save transcriptions permanently!

## 📊 Database Options

### Option 1: SQLite (Local Development) - DEFAULT
- **Best for:** Local development and testing
- **Pros:** No setup required, works immediately
- **Cons:** Data doesn't persist on Streamlit Cloud
- **File:** `transcription_app.py` (main version)

### Option 2: Supabase (Cloud Deployment) - RECOMMENDED
- **Best for:** Streamlit Cloud and production deployments
- **Pros:** Free tier, persists data across sessions
- **Cons:** Requires setup (5 minutes)
- **File:** `transcription_app_cloud.py`

## 🚀 Quick Start (SQLite - Local)

Just run the app! SQLite database is created automatically:
```bash
streamlit run transcription_app.py
```

A file called `transcriptions.db` will be created in your project directory.

## ☁️ Cloud Setup (Supabase)

### Step 1: Create Supabase Account
1. Go to [supabase.com](https://supabase.com)
2. Sign up for free account
3. Create a new project (remember your database password)

### Step 2: Create Database Table
1. In Supabase dashboard, go to **SQL Editor**
2. Run this SQL command:

```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    date TEXT NOT NULL,
    text TEXT NOT NULL,
    language TEXT,
    improved_text TEXT,  -- Added for GPT-4o-mini transcript improvement
    output_format TEXT DEFAULT 'text',  -- Added for SRT subtitle support
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (adjust as needed)
CREATE POLICY "Allow all operations" ON transcriptions
    FOR ALL USING (true);
```

#### 🔄 **For Existing Users: Update Schema**
If you already have a `transcriptions` table, add the new columns:
```sql
-- Add improved_text column for GPT-4o-mini transcript improvement feature
ALTER TABLE transcriptions ADD COLUMN improved_text TEXT;

-- Add output_format column for SRT subtitle support
ALTER TABLE transcriptions ADD COLUMN output_format TEXT DEFAULT 'text';
```

### Step 3: Get Your Credentials
1. Go to **Settings** → **API**
2. Copy:
   - `Project URL` (looks like: https://xxxxxxxxxxxx.supabase.co)
   - `anon public` key (safe to use in frontend)

### Step 4: Configure Environment

#### For Local Development (.env file):
```bash
OPENAI_API_KEY=sk-your-openai-key
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### For Streamlit Cloud (secrets):
1. Go to your app dashboard on Streamlit Cloud
2. Click **Settings** → **Secrets**
3. Add:
```toml
OPENAI_API_KEY = "sk-your-openai-key"
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 5: Use Cloud Version
```bash
# For cloud deployment, use:
streamlit run transcription_app_cloud.py
```

## 🔄 Switching Between Databases

The cloud version (`transcription_app_cloud.py`) automatically:
- Uses Supabase if credentials are provided
- Falls back to session state if not configured
- Shows connection status in the UI

## 📱 Features by Database Type

| Feature | SQLite (Local) | Session State | Supabase (Cloud) |
|---------|---------------|---------------|------------------|
| Instant setup | ✅ | ✅ | ❌ (5 min setup) |
| Persists locally | ✅ | ❌ | ✅ |
| Works on cloud | ❌ | ✅ | ✅ |
| Data survives restart | ✅ | ❌ | ✅ |
| Multi-user support | ❌ | ❌ | ✅ |
| Free tier | ✅ | ✅ | ✅ (500MB) |

## 🛠️ Troubleshooting

### Supabase Connection Issues
1. Check credentials are correct
2. Ensure table exists with correct schema
3. Check Row Level Security policies
4. Try the connection URL in a browser

### SQLite Issues (Local)
1. Check write permissions in directory
2. Delete `transcriptions.db` to reset
3. Ensure SQLite3 is installed (comes with Python)

### Missing Transcriptions
- **Session State:** Normal - data is temporary
- **SQLite:** Check if `.db` file exists
- **Supabase:** Check table in Supabase dashboard

## 🔒 Security Considerations

1. **API Keys:** Always use environment variables
2. **Supabase:** The `anon` key is safe for frontend use
3. **RLS:** Enable Row Level Security for multi-user apps
4. **Backups:** Export your transcriptions regularly

## 📈 Scaling Considerations

- **SQLite:** Good for <100GB data, single user
- **Supabase Free:** 500MB storage, 2GB transfer
- **Supabase Pro:** $25/month for 8GB storage

## 🎯 Recommendation

- **Local Development:** Use SQLite version
- **Streamlit Cloud:** Use Supabase version
- **Production:** Use Supabase with proper authentication

Need help? Check the logs or open an issue!