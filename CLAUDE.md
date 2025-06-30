# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based web application for audio transcription using OpenAI's Whisper v3 model. The application provides a modern UI for uploading audio files, transcribing them, and managing transcription history with persistent storage options.

**Available Versions:**
- **Modular Version** (`main.py`): Clean, maintainable architecture split into focused modules
- **Monolithic Version** (`transcription_app.py`): Original single-file implementation (legacy)
- **Offline Version** (`Offline version_no_db/`): Simplified version without database

## Architecture

### Modular Architecture (Recommended)
The application is organized into focused modules for better maintainability:

- **config/**: Application settings, environment variables, and UI styling
- **database/**: Data persistence layer with Supabase/session state abstraction  
- **audio/**: Audio processing, preprocessing, and Whisper API integration
- **ui/**: User interface components and page rendering logic
- **utils/**: General utilities, dependency checking, and file handling
- **tests/**: Unit tests for application components

### Legacy Components
- **transcription_app.py**: Original monolithic implementation (830 lines)
- **Offline version_no_db/**: Simplified version without database features

### Storage Strategy
The app uses a flexible storage approach:
- **Supabase (Cloud)**: When `SUPABASE_URL` and `SUPABASE_ANON_KEY` are configured
- **Session State (Fallback)**: When Supabase is unavailable or not configured
- Automatic fallback ensures the app works in any environment

### Key Features
- Multi-format audio support (mp3, wav, m4a, etc.)
- Multi-language transcription with auto-detection
- **Audio preprocessing**: Silence detection/removal and compression
- **FFmpeg integration**: Opus codec compression at 12kbps for optimal API usage
- Persistent transcription history
- Search functionality across transcriptions
- Export capabilities (JSON/TXT)
- Custom naming for transcriptions

## Development Commands

### Running the Application
```bash
# Modular version (recommended)
streamlit run main.py

# Original monolithic version (legacy)
streamlit run transcription_app.py

# Offline version (no database)
streamlit run "Offline version_no_db/transcription_app.py"
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Then edit .env with your OpenAI API key
```

### Database Setup (Supabase)
See `DATABASE_SETUP.md` for complete setup instructions. The required table schema:
```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    date TEXT NOT NULL,
    text TEXT NOT NULL,
    language TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Deployment
See `DEPLOYMENT_GUIDE.md` for various deployment options including:
- Streamlit Community Cloud (free)
- Heroku, Railway, Render
- Google Cloud Run

## Code Patterns

### Environment Variables
- `OPENAI_API_KEY`: Required for Whisper API
- `SUPABASE_URL`: Optional, for cloud storage
- `SUPABASE_ANON_KEY`: Optional, for cloud storage

### Database Operations
The `TranscriptionDB` class provides these methods:
- `add_transcription()`: Save new transcription
- `get_all_transcriptions()`: Retrieve all transcriptions
- `delete_transcription()`: Remove specific transcription
- `clear_all_transcriptions()`: Clear all data

### Error Handling
- Graceful fallback from Supabase to session state
- User-friendly error messages with styled boxes
- API key validation and environment setup guidance

### UI Styling
Custom CSS classes for consistent theming:
- `.transcription-card`: Main content cards
- `.history-item`: History list items
- `.success-box`, `.error-box`, `.warning-box`: Status messages
- Tailwind-inspired color scheme and spacing

## Testing

### Automated Testing
The modular version includes unit tests:

```bash
# Run all tests
python -m pytest transcription_app/tests/

# Run with coverage
python -m pytest transcription_app/tests/ --cov=transcription_app

# Run specific test file
python -m pytest transcription_app/tests/test_utils.py
```

### Manual Testing Workflow
1. Test with and without API key
2. Test with various audio formats
3. Test Supabase connection (if configured)
4. Test audio preprocessing features
5. Test export functionality
6. Test search and filtering

## Dependencies

Core dependencies from `requirements.txt`:
- `streamlit`: Web framework
- `openai`: Whisper API client
- `python-dotenv`: Environment variable management
- `supabase`: Optional cloud database client
- `pydub`: Audio manipulation and silence detection
- `ffmpeg-python`: Audio compression and format conversion
- `audioop-lts`: Python 3.13 compatibility for pydub

### System Requirements
- **FFmpeg**: Must be installed on the system for audio compression
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Download from https://ffmpeg.org/
- **Python Version**: Python 3.11, 3.12, or 3.13 supported (audioop-lts provides Python 3.13 compatibility)

## Audio Preprocessing

The application includes sophisticated audio preprocessing to optimize transcription:

### Silence Detection
- Uses pydub to detect and remove silent segments
- Configurable silence threshold (-50 dBFS default)
- Minimum silence length (1000ms default)
- Preserves 200ms of silence at chunk boundaries
- Shows time reduction statistics

### Audio Compression
- FFmpeg integration with Opus codec
- Optimized for speech: 12kbps bitrate, mono channel
- VoIP application profile for better speech quality
- Removes metadata and video tracks
- Shows file size reduction statistics

### Preprocessing Flow
1. **Upload**: User uploads audio file
2. **Silence Removal**: Detect and remove silent parts (optional)
3. **Compression**: Convert to OGG/Opus format (optional)
4. **Transcription**: Send optimized audio to Whisper API
5. **Results**: Display transcription with preprocessing statistics